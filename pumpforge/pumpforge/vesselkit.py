"""Building blocks for static equipment: vessels, heads, nozzles, supports, internals, liquid levels.
Convention: cut plane y = 0 keeps +y (valvekit.P splits automatically)."""
import math
from mathutils import Vector, Matrix
from .core import lathe, cyl, box, csg, join, rotate, extrude_poly, hex_prism, TAU, OPERATE_FRAMES
from .shapes import sweep_tube, cone_arrow
from .valvekit import shape_key, morph_loop


def _head(R, kind, n=10):
    """(r, dz) points of a head from the tangent line (dz >= 0 outward)."""
    if kind == 'hemi':
        return [(R * math.cos(math.pi / 2 * i / n), R * math.sin(math.pi / 2 * i / n)) for i in range(n + 1)]
    if kind == 'flat':
        return [(R, 0.0), (0.0, 0.0)]
    if kind == 'cone':
        return [(R, 0.0), (R * 0.12, R * 1.0), (0.0, R * 1.0)]
    h = R / 2                                         # 2:1 semi-ellipsoidal
    return [(R * math.cos(math.pi / 2 * i / n), h * math.sin(math.pi / 2 * i / n)) for i in range(n + 1)]


def vessel(name, R, L, t, mat, axis='Z', center=(0, 0, 0), heads=('2:1', '2:1'), segs=96, z0=0.0):
    """Hollow vessel: straight shell of length L between tangent lines (from z0), heads at both ends, wall t.
    axis 'Z' (vertical, tangent lines at z0 and z0 + L) or 'X' (horizontal, from z0 to z0 + L along x)."""
    lo = [(r, z0 - dz) for r, dz in _head(R, heads[0])][::-1]
    hi = [(r, z0 + L + dz) for r, dz in _head(R, heads[1])]
    outer = lo[::-1][::-1]
    prof_o = [(0.0, lo[0][1])] + lo[1:] + hi[:-1] + [(0.0, hi[-1][1])]
    Ri = R - t
    lo_i = [(r, z0 - dz) for r, dz in _head(Ri, heads[0])][::-1]
    hi_i = [(r, z0 + L + dz) for r, dz in _head(Ri, heads[1])]
    prof_i = [(0.0, lo_i[0][1])] + lo_i[1:] + hi_i[:-1] + [(0.0, hi_i[-1][1])]
    o = lathe(name + 'o', prof_o, mat, segs, axis=axis, center=center)
    i = lathe(name + 'i', prof_i, mat, segs, axis=axis, center=center)
    return csg(name, [o], [i], mat)


def liquid(name, R, z0, z1, mat='water', axis='Z', center=(0, 0, 0), segs=96, heads=None, L=None, zt=None):
    """Half body (y >= 0) so the cutaway shows the liquid itself — register with section='keep'.
    Liquid body inside a vertical vessel (cylinder z0..z1 of radius R) or a horizontal vessel (axis 'X':
    slab of the cylinder below level z1 between x = z0 .. z0 + L, centre height zt)."""
    if axis == 'Z':
        full = cyl(name + 'f', R, z0, z1, mat, segs, center=center)
        return csg(name, [full], [box(name + 'h', (4 * R, 2 * R, z1 - z0 + 0.2), (center[0], center[1] - R, (z0 + z1) / 2), mat)], mat)
    c = cyl(name + 'c', R, z0, z0 + L, mat, segs, axis='X', center=(0, center[1], zt))
    cut = box(name + 'k', (L + 0.1, 2 * R + 0.1, 2 * R), (z0 + L / 2, center[1], z1 + R), mat)
    half = box(name + 'h', (L + 0.1, 2 * R, 2 * R + 0.1), (z0 + L / 2, center[1] - R, zt), mat)
    return csg(name, [c], [cut, half], mat)


def animate_level(m, part, z_ref, dz, fn, key='level'):
    """Morph: vertices above z_ref move up by dz at weight 1; fn(t) -> weight."""
    for mesh in part.meshes:
        shape_key(mesh, key, lambda co: Vector((co.x, co.y, co.z + dz if co.z > z_ref else co.z)))
    morph_loop(m, part, key, fn)


def nozzle(name, base, direction, r, L, mat='steel', flange=True, t=None):
    """Pipe stub from base along direction with a weld-neck flange at the end (hollow)."""
    d = Vector(direction).normalized()
    b = Vector(base)
    e = b + d * L
    t = t or max(0.003, r * 0.12)
    objs = [sweep_tube(name + 'p', [tuple(b), tuple(e)], r, mat, 24)]
    if flange:
        objs.append(sweep_tube(name + 'f', [tuple(e - d * 0.012), tuple(e)], r * 1.9, mat, 32))
    return join(name, objs)


def saddles(name, xs, R, zc, foot_z=0.0, w=None, mat='paint_grey'):
    w = w or R * 0.25
    out = []
    for i, x in enumerate(xs):
        prof = []
        n = 12
        for k in range(n + 1):
            a = math.radians(-150 + 120 * k / n)
            prof.append((R * 1.02 * math.cos(a), zc + R * 1.02 * math.sin(a)))
        prof = [(-R * 0.95, foot_z)] + [p for p in prof if p[1] <= zc - R * 0.45] + [(R * 0.95, foot_z)]
        out.append(extrude_poly(f'{name}{i}', [(y, z) for y, z in prof], x - w / 2, x + w / 2, mat, plane='YZ'))
        out.append(box(f'{name}b{i}', (w * 1.6, R * 2.0, 0.025), (x, 0, foot_z + 0.0125), mat))
    return join(name, out)


def legs(name, R, z_bot, z_top, n=4, r_leg=None, mat='paint_grey', phase=math.pi / 4, cx=0.0, cy=0.0):
    r_leg = r_leg or max(0.025, R * 0.07)
    out = []
    for i in range(n):
        a = phase + TAU * i / n
        x, y = cx + R * math.cos(a), cy + R * math.sin(a)
        out.append(cyl(f'{name}{i}', r_leg, z_bot, z_top, mat, 24, center=(x, y, 0)))
        out.append(box(f'{name}p{i}', (r_leg * 4, r_leg * 4, 0.02), (x, y, z_bot + 0.01), mat))
    return join(name, out)


def skirt(name, R, z0, z1, t=0.01, mat='paint_grey'):
    return join(name, [cyl(name + 's', R, z0, z1, mat, 96, r_in=R - t), cyl(name + 'b', R * 1.25, z0, z0 + 0.03, mat, 96, r_in=R * 0.8)])


def mesh_pad(name, R, z0, z1, mat='steel', center=(0, 0, 0), axis='Z'):
    """Wire-mesh demister pad (solid with grid lines)."""
    cx, cy, cz = center
    pad = cyl(name + 'p', R, z0, z1, 'foam', 64, axis=axis, center=center)
    grid = []
    if axis == 'Z':
        for k in range(-4, 5):
            grid.append(box(f'{name}g{k}', (2 * R * math.sqrt(max(0.0, 1 - (k / 5) ** 2)), 0.004, z1 - z0 + 0.004), (cx, cy + R * k / 5, (z0 + z1) / 2), mat))
    return join(name, [pad] + grid)


def packing(name, R, z0, z1, center=(0, 0, 0), mat='ptfe', rings=True):
    """Random-packing bed shown as a speckled block (solid cylinder + ring dots on the outside)."""
    cx, cy, _ = center
    bed = cyl(name + 'b', R, z0, z1, 'polypropylene', 64, center=(cx, cy, 0))
    dots = []
    if rings:
        nz = max(2, int((z1 - z0) / 0.05))
        for j in range(nz):
            for i in range(14):
                a = TAU * (i + 0.5 * (j % 2)) / 14
                dots.append(box(f'{name}d{j}_{i}', (0.018, 0.018, 0.018), (cx + R * math.cos(a), cy + R * math.sin(a), z0 + (z1 - z0) * (j + 0.5) / nz), mat))
    return join(name, [bed] + dots)


def tray(name, R, z, holes=True, mat='stainless', weir=True, dc_side=1):
    """Sieve tray with downcomer segment on side dc_side (+1: +x)."""
    deck = cyl(name + 'd', R, z - 0.004, z + 0.004, mat, 64)
    ins = []
    if holes:
        for i in range(-4, 5):
            for j in range(-4, 5):
                x, y = R * 0.15 * i, R * 0.15 * j
                if x * x + y * y < (R * 0.7) ** 2 and x * dc_side < R * 0.45:
                    ins.append(cyl(f'{name}h{i}_{j}', R * 0.03, z - 0.01, z + 0.01, mat, 8, center=(x, y, 0)))
    ins.append(box(name + 'dc', (R * 0.4, 2 * R, 0.03), (dc_side * (R * 0.82), 0, z), mat))
    deck = csg(name, [deck], ins, mat)
    parts = [deck]
    if weir:
        parts.append(box(name + 'w', (0.005, 2 * R * 0.8, 0.05), (dc_side * R * 0.62, 0, z + 0.025), mat))
        parts.append(box(name + 'ap', (0.005, 2 * R * 0.8, 0.25), (dc_side * R * 0.62, 0, z - 0.13), mat))
    return join(name + 'j', parts)


def helix_coil(name, R, z0, z1, turns, r_tube, mat='copper', center=(0, 0, 0), n=None):
    cx, cy, _ = center
    n = n or int(turns * 24)
    pts = [(cx + R * math.cos(TAU * turns * i / n), cy + R * math.sin(TAU * turns * i / n), z0 + (z1 - z0) * i / n) for i in range(n + 1)]
    return sweep_tube(name, pts, r_tube, mat, 10), pts


def ladder(name, x, y, z0, z1, w=0.4, mat='paint_yellow', facing='x'):
    rails, rungs = [], []
    for s in (-1, 1):
        if facing == 'x':
            rails.append(cyl(f'{name}r{s}', 0.012, z0, z1, mat, 8, center=(x, y + s * w / 2, 0)))
        else:
            rails.append(cyl(f'{name}r{s}', 0.012, z0, z1, mat, 8, center=(x + s * w / 2, y, 0)))
    n = int((z1 - z0) / 0.3)
    for k in range(n):
        z = z0 + 0.15 + 0.3 * k
        if facing == 'x':
            rungs.append(cyl(f'{name}g{k}', 0.008, y - w / 2, y + w / 2, mat, 8, axis='Y', center=(x, 0, z)))
        else:
            rungs.append(cyl(f'{name}g{k}', 0.008, x - w / 2, x + w / 2, mat, 8, axis='X', center=(0, y, z)))
    return join(name, rails + rungs)


def platform(name, R_in, R_out, z, a0=-0.6, a1=0.6, mat='paint_yellow', cx=0.0, cy=0.0):
    deck = lathe(name + 'd', [(R_in, z - 0.01), (R_out, z - 0.01), (R_out, z + 0.01), (R_in, z + 0.01)], 'steel_dark', 48, a0=a0, a1=a1, center=(cx, cy, 0))
    rail = lathe(name + 'r', [(R_out - 0.01, z + 0.5), (R_out, z + 0.5), (R_out, z + 0.53), (R_out - 0.01, z + 0.53)], mat, 48, a0=a0, a1=a1, center=(cx, cy, 0))
    posts = [cyl(f'{name}p{i}', 0.01, z, z + 0.53, mat, 8, center=(cx + R_out * math.cos(a0 + (a1 - a0) * i / 4), cy + R_out * math.sin(a0 + (a1 - a0) * i / 4), 0)) for i in range(5)]
    return join(name, [deck, rail] + posts)


def droplets(m, pid, name, x0, x1, z_top, z_bot, n=8, mat='water', y=0.05, r=0.012, ref='flow_tracers'):
    """Falling droplets (tracers) between z_top and z_bot at evenly spread x."""
    p = m.part(pid, name, 'flow_tracers', explode=(0, 0, 0), info={'ref': ref})
    for i in range(n):
        x = x0 + (x1 - x0) * (i + 0.5) / n
        ph = (i * 0.37) % 1.0
        o = cyl(f'{pid}{i}', r, -r, r, mat, 12, center=(0, 0, 0))
        ms = p.add(o, smooth_angle=60)
        keys = []
        for f in range(OPERATE_FRAMES + 1):
            s = ((f / OPERATE_FRAMES) + ph) % 1.0
            keys.append((1 + f, (x, y, z_top + (z_bot - z_top) * s)))
        ms.location = keys[0][1]
        m.keyframes(ms, 'Operate', 'location', keys)
    return p


def liquid_v(name, R, z_tan, z_level, head='2:1', mat='water', cx=0.0, cy=0.0, segs=64):
    """Half (y >= 0) liquid body filling a vertical vessel's bottom head up to z_level; caps use the liquid material."""
    pts = [(r, z_tan - dz) for r, dz in _head(R, head)][::-1]          # apex -> tangent
    prof = [(0.0, pts[0][1])] + pts[1:] + [(R, z_level), (0.0, z_level)]
    return lathe(name, prof, mat, segs, a0=0.0, a1=math.pi, center=(cx, cy, 0), cap_mat=mat)


def half(obj, mat, size=50.0):
    """Keep only the y >= 0 half of a solid; the new cut faces take material `mat` (use with section='keep')."""
    return csg(obj.name, [obj], [box(obj.name + '_hcut', (size, size, size), (0, -size / 2, 0), mat)], mat)
