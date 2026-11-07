"""Regenerate the README model catalogue from output/learning/index.json: python3 tools/update_docs.py"""
import json, os, re
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
idx = json.load(open(os.path.join(R, 'output', 'learning', 'index.json'), encoding='utf-8'))['modules']
cat = json.load(open(os.path.join(R, 'catalog.json'), encoding='utf-8'))
n = len(idx)
rows, last = ['| Module | Iso | Cutaway | Exploded |', '|---|---|---|---|'], None
for m in idx:
    if m['category'] != last:
        last = m['category']
        cid = next(c['id'] for c in cat['categories'] if c['name'] == last)
        rows.append(f'| **{cid} · {last}** | | | |')
    meta = json.load(open(os.path.join(R, 'output', 'meta', m['id'] + '.json'), encoding='utf-8'))
    tag = f"{m['eq_id']} · " if m.get('eq_id') else ''
    ov = [o for o in m['overlays'] if o != 'flow']
    sub = f"`{m['id']}` · {tag}phase {m['phase']} · {len(meta.get('parts', []))} parts" + (f" · overlays: {', '.join(ov)}" if ov else '')
    cells = ' | '.join(f"![](output/previews/{m['id']}_{v}.jpg)" for v in ('iso', 'cutaway', 'exploded'))
    rows.append(f"| {m['no']}. {m['title']}{' ★' if m['flagship'] else ''}<br><sub>{sub}</sub> | {cells} |")
p = os.path.join(R, 'README.md')
s = open(p, encoding='utf-8').read()
s = re.sub(r'\| Module \| Iso \| Cutaway \| Exploded \|\n(\|.*\n)+', '\n'.join(rows) + '\n', s, count=1)
s = re.sub(r'## Model catalogue — \d+ of \d+ built', f'## Model catalogue — {n} of {n} built', s)
open(p, 'w', encoding='utf-8').write(s)
print(f'README catalogue: {n} modules')


def glb_tris(path):
    import struct
    b = open(path, 'rb').read()
    ln = struct.unpack_from('<I', b, 12)[0]
    j = json.loads(b[20:20 + ln])
    t = 0
    for node in j.get('nodes', []):
        if 'mesh' in node:
            for pr in j['meshes'][node['mesh']]['primitives']:
                acc = j['accessors'][pr['indices']] if 'indices' in pr else j['accessors'][pr['attributes']['POSITION']]
                t += acc['count'] // 3
    return t


rows = ['| Module | Triangles | GLB size | Parts | Overlays |', '|---|---|---|---|---|']
tot, big = 0, (0, 0)
gdir = os.path.join(R, 'output', 'glb')
for f in os.listdir(gdir):
    tot += os.path.getsize(os.path.join(gdir, f))
for m in idx:
    g = os.path.join(gdir, m['id'] + '.glb')
    tr, sz = glb_tris(g), os.path.getsize(g)
    big = max(big, (tr, sz))
    meta = json.load(open(os.path.join(R, 'output', 'meta', m['id'] + '.json'), encoding='utf-8'))
    rows.append(f"| {m['no']}. {m['title']} | {round(tr / 1000)} k | {sz / 1e6:.1f} MB | {len(meta.get('parts', []))} | {', '.join(m['overlays'])} |")
p = os.path.join(R, 'docs', 'ANDROID_INTEGRATION.md')
s = open(p, encoding='utf-8').read()
s = re.sub(r'\| Module \| Triangles \| GLB size \| Parts \| Overlays \|\n(\|.*\n)+', '\n'.join(rows) + '\n', s, count=1)
s = re.sub(r'The largest model is about [^.]+\.[^.]+\. and the whole set is about [\d.]+ MB', '', s)
s = re.sub(r'The largest model is about .*? uncompressed, including (flow )?overlays\.',
           f'The largest model is about {round(big[0] / 1000)} k triangles, and the whole set of {len(os.listdir(gdir))} GLBs is about {tot / 1e6:.0f} MB uncompressed, including flow and teaching overlays.', s)
open(p, 'w', encoding='utf-8').write(s)
print('performance table:', len(idx), 'rows')
