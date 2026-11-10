"""Convert PumpForge glTF binaries (.glb) into the compact native model format (.pfm).

Why: the native Android app draws straight from GPU-ready buffers. Quantising positions to 16-bit and
normals to 8-bit (per-primitive bounding box) cuts vertex data from 24 to 12 bytes per vertex with no
visible change (2 m part -> 0.03 mm grid; normals ~0.5 deg).

Layout (little-endian):
  'PFM1' | u32 json_len | json (UTF-8, padded with spaces to 4 bytes) | binary blob
JSON:
  materials : [{name, c:[r,g,b,a] (linear), m, r, e:[r,g,b], ds}]
  nodes     : [{n:name, p:parent(-1), t,r,s, mesh:-1|idx, x:{extras}}]   (parents always precede children)
  meshes    : [{w:[default morph weights], prims:[{mat, vc, ic, vo, io, c:[3], h:[3], tg:[{po, ps:[3], no, ns}]}]}]
  anims     : [{name, dur, ch:[{node, path(t|r|s|w), n, k(comps), to, vo}]}]
  extras    : root scene extras (pump_id, title, ...)
Binary (all offsets in bytes from blob start, 4-byte aligned):
  vertices  : 9 bytes/vertex, byte planes of zigzag deltas: x lo,x hi,y lo,y hi,z lo,z hi (int16), nx,ny,nz (int8)
              decoded on load to GPU layout int16 x,y,z,0 + int8 nx,ny,nz,0 (12 bytes; pos = c + q/32767*h)
  indices   : uint16, high-watermark coded (code = maxSoFar+1 - index), lo plane then hi plane
              vertices are stored in first-use order, so the codes are tiny and deflate (APK zip) packs them well
  morph pos : int16 dx,dy,dz,0 per vertex (scale ps per axis)  morph nrm: int8 x,y,z,0 (scale ns)
  anim      : float32 times, float32 values
Usage: python3 glb2pfm.py <in_dir> <out_dir>   (verifies every file by decoding it back)
"""
import json, struct, sys, os, glob
import numpy as np

CT = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8, 5122: np.int16, 5120: np.int8}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def read_glb(path):
    b = open(path, 'rb').read()
    assert b[:4] == b'glTF', path
    jl = struct.unpack('<I', b[12:16])[0]
    j = json.loads(b[20:20 + jl])
    off = 20 + jl
    bl = struct.unpack('<I', b[off:off + 4])[0]
    blob = b[off + 8: off + 8 + bl]
    return j, blob


def accessor(j, blob, i):
    a = j['accessors'][i]
    n, k, dt = a['count'], NC[a['type']], CT[a['componentType']]
    if 'bufferView' in a:
        bv = j['bufferViews'][a['bufferView']]
        start = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
        stride = bv.get('byteStride', 0)
        isz = np.dtype(dt).itemsize
        if stride and stride != k * isz:
            raw = np.frombuffer(blob, np.uint8, count=stride * (n - 1) + k * isz, offset=start)
            out = np.empty((n, k), dt)
            for r in range(n):
                out[r] = np.frombuffer(raw[r * stride: r * stride + k * isz].tobytes(), dt)
        else:
            out = np.frombuffer(blob, dt, count=n * k, offset=start).reshape(n, k).copy()
    else:
        out = np.zeros((n, k), dt)
    if 'sparse' in a:
        sp = a['sparse']
        ib, vb = sp['indices'], sp['values']
        ibv, vbv = j['bufferViews'][ib['bufferView']], j['bufferViews'][vb['bufferView']]
        idx = np.frombuffer(blob, CT[ib['componentType']], count=sp['count'], offset=ibv.get('byteOffset', 0) + ib.get('byteOffset', 0))
        val = np.frombuffer(blob, dt, count=sp['count'] * k, offset=vbv.get('byteOffset', 0) + vb.get('byteOffset', 0)).reshape(-1, k)
        out[idx.astype(np.int64)] = val
    if a.get('normalized'):
        raise ValueError('normalized accessors not expected')
    return out


class Blob:
    def __init__(self):
        self.parts, self.size = [], 0

    def add(self, arr):
        b = np.ascontiguousarray(arr).tobytes()
        off = self.size
        pad = (-len(b)) % 4
        self.parts.append(b + b'\0' * pad)
        self.size += len(b) + pad
        return off

    def bytes(self):
        return b''.join(self.parts)


def q16(v):
    return np.clip(np.round(v * 32767.0), -32767, 32767).astype(np.int16)


def q8(v):
    return np.clip(np.round(v * 127.0), -127, 127).astype(np.int8)


def first_use_order(idx, n):
    seen = np.full(n, -1, np.int64)
    first = np.unique(idx, return_index=True)
    # vertices sorted by the position of their first appearance; unused vertices go last
    used = first[0][np.argsort(first[1])]
    seen[used] = np.arange(len(used))
    rest = np.setdiff1d(np.arange(n), used)
    seen[rest] = len(used) + np.arange(len(rest))
    order = np.empty(n, np.int64)
    order[seen] = np.arange(n)
    return order, seen[idx]


def zz16(a):
    """16-bit wrapping delta + zigzag along the vertex order."""
    a = a.astype(np.int16)
    d = np.diff(a.astype(np.int32), prepend=0).astype(np.int64)
    d = ((d + 32768) % 65536 - 32768).astype(np.int16).astype(np.int32)
    return (((d << 1) ^ (d >> 15)) & 0xFFFF).astype(np.uint16)


def zz8(a):
    d = np.diff(a.astype(np.int32), prepend=0)
    d = ((d + 128) % 256 - 128).astype(np.int32)
    return (((d << 1) ^ (d >> 7)) & 0xFF).astype(np.uint8)


def planes16(u):
    return np.concatenate([(u & 0xFF).astype(np.uint8), (u >> 8).astype(np.uint8)])


def encode_vertices(qp, qn):
    """Byte layout: x lo-plane, x hi-plane, y lo, y hi, z lo, z hi, nx, ny, nz  (9 bytes per vertex)."""
    return np.concatenate([planes16(zz16(qp[:, 0])), planes16(zz16(qp[:, 1])), planes16(zz16(qp[:, 2])),
                           zz8(qn[:, 0]), zz8(qn[:, 1]), zz8(qn[:, 2])])


def encode_indices(ni):
    """High-watermark coding: code = (max index so far + 1) - index; a brand-new vertex is always 0."""
    mx = np.maximum.accumulate(ni)
    hw = np.concatenate([[0], mx[:-1] + 1])
    code = hw - ni
    assert code.min() >= 0 and code.max() < 65536
    return planes16(code.astype(np.uint16))


def decode_vertices(b, off, n):
    raw = np.frombuffer(b, np.uint8, count=9 * n, offset=off)
    def un16(k):
        z = raw[2 * k * n: 2 * k * n + n].astype(np.int64) | (raw[2 * k * n + n: 2 * k * n + 2 * n].astype(np.int64) << 8)
        d = (z >> 1) ^ -(z & 1)
        return ((np.cumsum(d) + 32768) % 65536 - 32768).astype(np.int16)
    def un8(k):
        z = raw[6 * n + k * n: 6 * n + (k + 1) * n].astype(np.int64)
        d = (z >> 1) ^ -(z & 1)
        return ((np.cumsum(d) + 128) % 256 - 128).astype(np.int8)
    return np.stack([un16(0), un16(1), un16(2)], 1), np.stack([un8(0), un8(1), un8(2)], 1)


def decode_indices(b, off, n):
    raw = np.frombuffer(b, np.uint8, count=2 * n, offset=off)
    code = raw[:n].astype(np.int64) | (raw[n:].astype(np.int64) << 8)
    out = np.empty(n, np.int64)
    hw = 0
    for i in range(n):          # sequential by nature (mirrors the C++ decoder)
        v = hw - code[i]
        out[i] = v
        if v + 1 > hw:
            hw = v + 1
    return out


def convert(path):
    j, blob = read_glb(path)
    out = Blob()
    mats = []
    for m in j.get('materials', []):
        pbr = m.get('pbrMetallicRoughness', {})
        mats.append({'name': m.get('name', ''), 'c': [round(x, 5) for x in pbr.get('baseColorFactor', [1, 1, 1, 1])],
                     'm': round(pbr.get('metallicFactor', 1.0), 4), 'r': round(pbr.get('roughnessFactor', 1.0), 4),
                     'e': [round(x, 5) for x in m.get('emissiveFactor', [0, 0, 0])], 'ds': bool(m.get('doubleSided', False))})
    meshes, stats = [], {'verts': 0, 'tris': 0}
    for me in j.get('meshes', []):
        prims = []
        for pr in me['primitives']:
            assert pr.get('mode', 4) == 4
            pos = accessor(j, blob, pr['attributes']['POSITION']).astype(np.float64)
            nrm = accessor(j, blob, pr['attributes']['NORMAL']).astype(np.float64) if 'NORMAL' in pr['attributes'] else None
            if nrm is None:
                raise ValueError('normals required')
            idx = accessor(j, blob, pr['indices']).reshape(-1) if 'indices' in pr else np.arange(len(pos))
            # bounding box must include morphed extremes so the quantised grid stays valid only for base pos (deltas separate)
            lo, hi = pos.min(0), pos.max(0)
            c = (lo + hi) / 2
            h = np.maximum((hi - lo) / 2, 1e-6)
            qp = q16((pos - c) / h)
            ln = np.linalg.norm(nrm, axis=1, keepdims=True)
            ln[ln == 0] = 1
            qn = q8(nrm / ln)
            assert idx.max() < 65536
            # vertex fetch order = first use in the index buffer (better GPU locality and much better compression)
            order, ni = first_use_order(idx.astype(np.int64), len(pos))
            qp, qn = qp[order], qn[order]
            vo = out.add(encode_vertices(qp, qn))
            io = out.add(encode_indices(ni))
            tg = []
            for t in pr.get('targets', []):
                dp = (accessor(j, blob, t['POSITION']).astype(np.float64) if 'POSITION' in t else np.zeros_like(pos))[order]
                ps = np.maximum(np.abs(dp).max(0), 1e-7)
                qd = np.zeros((len(pos), 4), np.int16)
                qd[:, :3] = q16(dp / ps)
                po = out.add(qd)
                dn = (accessor(j, blob, t['NORMAL']).astype(np.float64) if 'NORMAL' in t else np.zeros_like(pos))[order]
                ns = float(max(np.abs(dn).max(), 1e-7))
                qn2 = np.zeros((len(pos), 4), np.int8)
                qn2[:, :3] = q8(dn / ns)
                no = out.add(qn2)
                tg.append({'po': po, 'ps': [float(x) for x in ps], 'no': no, 'ns': ns})
            prims.append({'mat': pr.get('material', -1), 'vc': int(len(pos)), 'ic': int(len(idx)), 'vo': vo, 'io': io,
                          'c': [float(x) for x in c], 'h': [float(x) for x in h], 'tg': tg})
            stats['verts'] += len(pos)
            stats['tris'] += len(idx) // 3
        meshes.append({'w': me.get('weights', []), 'prims': prims})
    # nodes in parent-before-child order
    scene = j['scenes'][j.get('scene', 0)]
    parent = {}
    for i, n in enumerate(j['nodes']):
        for ch in n.get('children', []):
            parent[ch] = i
    order = []

    def walk(i):
        order.append(i)
        for ch in j['nodes'][i].get('children', []):
            walk(ch)
    for r in scene['nodes']:
        walk(r)
    remap = {old: new for new, old in enumerate(order)}
    nodes = []
    for old in order:
        n = j['nodes'][old]
        assert 'matrix' not in n
        nodes.append({'n': n.get('name', ''), 'p': remap[parent[old]] if old in parent else -1,
                      't': n.get('translation', [0, 0, 0]), 'r': n.get('rotation', [0, 0, 0, 1]), 's': n.get('scale', [1, 1, 1]),
                      'mesh': n.get('mesh', -1), 'x': n.get('extras', {})})
    anims = []
    for an in j.get('animations', []):
        chs, dur = [], 0.0
        for ch in an['channels']:
            s = an['samplers'][ch['sampler']]
            assert s.get('interpolation', 'LINEAR') == 'LINEAR'
            tm = accessor(j, blob, s['input']).reshape(-1).astype(np.float32)
            vals = accessor(j, blob, s['output']).astype(np.float32)
            path = {'translation': 't', 'rotation': 'r', 'scale': 's', 'weights': 'w'}[ch['target']['path']]
            k = vals.size // len(tm)
            dur = max(dur, float(tm[-1]))
            chs.append({'node': remap[ch['target']['node']], 'path': path, 'n': int(len(tm)), 'k': int(k),
                        'to': out.add(tm), 'vo': out.add(vals.reshape(-1))})
        anims.append({'name': an.get('name', ''), 'dur': dur, 'ch': chs})
    hdr = {'materials': mats, 'nodes': nodes, 'meshes': meshes, 'anims': anims, 'extras': scene.get('extras', {}),
           'stats': stats}
    js = json.dumps(hdr, separators=(',', ':'), ensure_ascii=False).encode()
    js += b' ' * ((-len(js)) % 4)
    data = b'PFM1' + struct.pack('<I', len(js)) + js + out.bytes()
    return data, j, blob, hdr


def verify(data, j, blob):
    """Decode the .pfm again and compare against the source glTF (positions, normals, indices, animation)."""
    assert data[:4] == b'PFM1'
    jl = struct.unpack('<I', data[4:8])[0]
    h = json.loads(data[8:8 + jl])
    b = data[8 + jl:]
    worst_p, worst_n = 0.0, 0.0
    for mi, me in enumerate(j.get('meshes', [])):
        for pi, pr in enumerate(me['primitives']):
            p = h['meshes'][mi]['prims'][pi]
            qp, qn = decode_vertices(b, p['vo'], p['vc'])
            idx = decode_indices(b, p['io'], p['ic'])
            src = accessor(j, blob, pr['attributes']['POSITION'])
            sidx = accessor(j, blob, pr['indices']).reshape(-1).astype(np.int64)
            # compare per triangle corner (vertex order changed, triangles identical)
            pos = (np.array(p['c']) + qp / 32767.0 * np.array(p['h']))[idx]
            worst_p = max(worst_p, float(np.abs(pos - src[sidx]).max()))
            n = (qn / 127.0)[idx]
            sn = accessor(j, blob, pr['attributes']['NORMAL'])[sidx]
            sn = sn / np.maximum(np.linalg.norm(sn, axis=1, keepdims=True), 1e-9)
            n = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
            worst_n = max(worst_n, float(np.degrees(np.arccos(np.clip((n * sn).sum(1), -1, 1))).max()))
            order = np.empty(p['vc'], np.int64)
            order[idx] = sidx          # new vertex -> source vertex
            for ti, t in enumerate(pr.get('targets', [])):
                tq = h['meshes'][mi]['prims'][pi]['tg'][ti]
                d = np.frombuffer(b, np.int16, count=p['vc'] * 4, offset=tq['po']).reshape(-1, 4)[:, :3] / 32767.0 * np.array(tq['ps'])
                sd = accessor(j, blob, t['POSITION'])[order]
                assert np.abs(d - sd).max() <= np.abs(sd).max() / 32767 + 1e-6
    assert len(h['nodes']) == len(j['nodes'])
    return worst_p, worst_n


def main():
    src, dst = sys.argv[1], sys.argv[2]
    os.makedirs(dst, exist_ok=True)
    tot_in = tot_out = 0
    wp = wn = 0
    files = sorted(glob.glob(os.path.join(src, '*.glb')))
    for f in files:
        data, j, blob, hdr = convert(f)
        p, n = verify(data, j, blob)
        wp, wn = max(wp, p), max(wn, n)
        name = os.path.splitext(os.path.basename(f))[0] + '.pfm'
        open(os.path.join(dst, name), 'wb').write(data)
        tot_in += os.path.getsize(f)
        tot_out += len(data)
    print(f'{len(files)} files: {tot_in / 1e6:.1f} MB glb -> {tot_out / 1e6:.1f} MB pfm; '
          f'max position error {wp * 1000:.4f} mm, max normal error {wn:.2f} deg')


if __name__ == '__main__':
    main()
