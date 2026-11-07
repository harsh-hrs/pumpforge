"""Building blocks for valves, piping components and flow elements.
Convention: flow along +X through the origin at height CZ; cut plane y = 0 (keep +y)."""
import math
from mathutils import Vector
from .core import (lathe, cyl, box, join, split_many, rotate, transform, hex_prism, TAU, OPERATE_FRAMES)
from .parts import nozzle_bolts
from .shapes import sweep_tube


def P(m, pid, name, group, objs, explode=(0, 0, 0), ref=None, section='split', pivot=(0, 0, 0), smooth=40):
    """Register a part; split objects into cutaway halves when section == 'split'."""
    objs = [o for o in (objs if isinstance(objs, (list, tuple)) else [objs]) if o is not None]
    p = m.part(pid, name, group, pivot=pivot, section=section, explode=explode, info={'ref': ref or pid})
    if section == 'split':
        b, f = split_many(pid, objs)
        p.add_split(b, f, smooth_angle=smooth)
    else:
        p.add(join(pid, objs) if len(objs) > 1 else objs[0], smooth_angle=smooth)
    return p


def bore_pipe(name, x0, x1, r, t, cz, mat='paint_grey', segs=48):
    """Straight pipe along X with a real bore."""
    return cyl(name, r + t, x0, x1, mat, segs, axis='X', center=(0, 0, cz), r_in=r)


def flange(name, x, r_bore, cz, rf=None, th=0.02, mat='paint_grey', face=+1):
    """Weld-neck style flange: ring from x (sealing face) extending away from the joint by th."""
    rf = rf or (r_bore * 2.0 + 0.035)
    x0, x1 = (x, x + face * th) if face > 0 else (x + face * th, x)
    hub = cyl(name + 'h', r_bore * 1.35 + 0.006, min(x0, x1) - (0.0 if face > 0 else 0.03), max(x0, x1) + (0.03 if face > 0 else 0.0),
              mat, 48, axis='X', center=(0, 0, cz), r_in=r_bore)
    ring = cyl(name, rf, x0, x1, mat, 64, axis='X', center=(0, 0, cz), r_in=r_bore, ch=0.002)
    return join(name + 'j', [ring, hub])


def bolts_x(name, x, rf, cz, n=8, th=0.044, af=None):
    af = af or max(0.012, rf * 0.14)
    return nozzle_bolts(name, n, 2 * (rf - af * 0.9), af, x - th / 2, x + th / 2, 'X', (0, 0, cz), math.pi / n)


def gasket(name, x, r_in, r_out, cz, th=0.003):
    return cyl(name, r_out, x - th / 2, x + th / 2, 'rubber', 64, axis='X', center=(0, 0, cz), r_in=r_in)


def handwheel(name, center, r, axis='Z', mat='paint_red', spokes=3):
    cx, cy, cz = center
    prof = [(r - 0.012 * r / 0.06 * 0.6 - 0.004 + 0.0, -0.006), (r, -0.006), (r, 0.006), (r * 0.8, 0.006)]
    rim = lathe(name + 'rim', [(r * 0.86, -0.007 - r * 0.05), (r, -0.007 - r * 0.05), (r, 0.007 + r * 0.05), (r * 0.86, 0.007 + r * 0.05)],
                mat, 48, axis=axis, center=center)
    hub = cyl(name + 'hub', r * 0.18, -0.012 - r * 0.1, 0.012 + r * 0.1, mat, 24, axis=axis, center=center)
    objs = [rim, hub]
    for i in range(spokes):
        a = TAU * i / spokes
        if axis == 'Z':
            pts = [(cx + r * 0.15 * math.cos(a), cy + r * 0.15 * math.sin(a), cz), (cx + r * 0.9 * math.cos(a), cy + r * 0.9 * math.sin(a), cz)]
        elif axis == 'X':
            pts = [(cx, cy + r * 0.15 * math.cos(a), cz + r * 0.15 * math.sin(a)), (cx, cy + r * 0.9 * math.cos(a), cz + r * 0.9 * math.sin(a))]
        else:
            pts = [(cx + r * 0.15 * math.cos(a), cy, cz + r * 0.15 * math.sin(a)), (cx + r * 0.9 * math.cos(a), cy, cz + r * 0.9 * math.sin(a))]
        objs.append(sweep_tube(name + f's{i}', pts, r * 0.07, mat, 8))
    return join(name, objs)


def spring(name, center, r, h0, h1, wire, turns=6, mat='steel', axis='Z'):
    cx, cy, cz = center
    pts = []
    n = int(turns * 16)
    for i in range(n + 1):
        t = i / n
        a = TAU * turns * t
        h = h0 + (h1 - h0) * t
        if axis == 'Z':
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a), h))
        else:
            pts.append((h, cy + r * math.cos(a), cz + r * math.sin(a)))
    return sweep_tube(name, pts, wire, mat, 8)


def sphere(name, center, r, mat, segs=24):
    prof = [(r * math.sin(t * math.pi / 12), -r * math.cos(t * math.pi / 12)) for t in range(13)]
    return lathe(name, prof, mat, segs, center=center)


def keys_loop(m, part, fn, path='location', n=60):
    """Keyframe every mesh of `part` with fn(phase 0..1) -> 3-tuple over the Operate loop."""
    for mesh in part.meshes:
        m.keyframes(mesh, 'Operate', path, [(1 + OPERATE_FRAMES * k / n, tuple(fn(k / n))) for k in range(n + 1)])


def smooth_pulse(t, rise=0.15, hold=0.35, fall=0.15):
    """0 → 1 → 0 over one loop with eased ramps (open / hold / close / hold)."""
    def ease(x):
        x = max(0.0, min(1.0, x))
        return x * x * (3 - 2 * x)
    if t < rise:
        return ease(t / rise)
    if t < rise + hold:
        return 1.0
    if t < rise + hold + fall:
        return 1.0 - ease((t - rise - hold) / fall)
    return 0.0


def shape_key(obj, name, fn):
    """Add a morph target: fn(co) -> new co (Vector)."""
    if not obj.data.shape_keys:
        obj.shape_key_add(name='Basis', from_mix=False)
    k = obj.shape_key_add(name=name, from_mix=False)
    for i, v in enumerate(obj.data.vertices):
        k.data[i].co = fn(v.co.copy())
    return k


def morph_loop(m, part, key, fn, n=60):
    from .core import OPERATE_FRAMES as OF
    for mesh in part.meshes:
        if mesh.data.shape_keys and key in mesh.data.shape_keys.key_blocks:
            m.morph(mesh, key, 'Operate', [(1 + OF * k / n, fn(k / n)) for k in range(n + 1)])


def tap(name, x, cz, r_out, up=0.08, r=0.008, mat='stainless'):
    """Pressure tap with root valve stub on top of a pipe at x."""
    return join(name, [cyl(name + 'n', r, cz + r_out - 0.004, cz + r_out + up, mat, 16, center=(x, 0, 0)),
                       hex_prism(name + 'h', r * 2.4, cz + r_out + up * 0.55, cz + r_out + up * 0.75, mat, center=(x, 0, 0))])


def dp_transmitter(name, center, mat='paint_blue'):
    cx, cy, cz = center
    return join(name, [box(name + 'b', (0.11, 0.06, 0.05), (cx, cy, cz), 'stainless', bevel=0.006),
                       cyl(name + 'h', 0.045, cz + 0.025, cz + 0.07, mat, 32, center=(cx, cy, 0)),
                       cyl(name + 'd', 0.035, cy - 0.032, cy - 0.022, 'chrome', 32, axis='Y', center=(cx, 0, cz + 0.05)),
                       cyl(name + 'c', 0.012, cz + 0.07, cz + 0.1, 'thermoplastic', 12, center=(cx + 0.03, cy, 0))])
