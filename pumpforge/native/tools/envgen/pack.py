"""Pack the baked RoomEnvironment radiance maps into assets/env.bin (RGB9_E5, 6 roughness layers)."""
import json, sys, struct, numpy as np
e = json.load(open(sys.argv[1]))
W, H, L = e['W'], e['H'], e['LEVELS']

def rgb9e5(c):
    c = np.clip(c, 0, 65408.0)
    m = c.max(-1)
    e_ = np.maximum(-16, np.floor(np.log2(np.maximum(m, 1e-30)))) + 1 + 15
    e_ = np.clip(e_, 0, 31)
    denom = 2.0 ** (e_ - 15 - 9)
    mm = np.floor(m / denom + 0.5)
    e_ = np.where(mm == 512, e_ + 1, e_); denom = 2.0 ** (e_ - 15 - 9)
    q = np.clip(np.floor(c / denom[..., None] + 0.5), 0, 511).astype(np.uint32)
    return (q[..., 0] | (q[..., 1] << 9) | (q[..., 2] << 18) | (e_.astype(np.uint32) << 27)).astype(np.uint32)

out = bytearray(b'PFEV' + struct.pack('<IIII', W, H, len(L), 0))
for lv, d in zip(L, e['data']):
    a = np.array(d, np.float64).reshape(H, W, 4)[..., :3]
    out += struct.pack('<f', lv)
for d in e['data']:
    a = np.array(d, np.float64).reshape(H, W, 4)[..., :3]
    out += rgb9e5(a).tobytes()
open(sys.argv[2], 'wb').write(out)
print('env.bin', len(out), 'bytes')
