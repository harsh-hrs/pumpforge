"""Building blocks for material-handling and heavy machinery: hoppers, belts, idlers, moving markers/rocks,
structural members, rails/wheels, rope and hook blocks.  Cut plane y = 0 keeps +y."""
import math
from mathutils import Matrix, Vector
from .core import lathe, cyl, box, csg, join, rotate, extrude_poly, hex_prism, TAU, OPERATE_FRAMES
from .shapes import sweep_tube
from .rotkit import open_path


def hopper(name, w_top, w_bot, z_bot, z_top, mat='paint_grey', t=0.008, cx=0.0, cy=0.0):
    """Square hopper (frustum) open at both ends."""
    def frus(nm, a, b, z0, z1):
        return lathe(nm, [(b * math.sqrt(2) / 2, z0), (a * math.sqrt(2) / 2, z1), (0.0, z1), (0.0, z0)], mat, 4, a0=math.pi / 4, a1=math.pi / 4 + TAU, center=(cx, cy, 0))
    return csg(name, [frus(name + 'o', w_top + 2 * t, w_bot + 2 * t, z_bot, z_top)], [frus(name + 'i', w_top, w_bot, z_bot - 0.01, z_top + 0.01)], mat)


def beam(name, p0, p1, w=0.06, h=0.08, mat='paint_yellow'):
    """Rectangular structural member between two points (sweep with square-ish section)."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    L = d.length
    b = box(name, (L, w, h), (0, 0, 0), mat)
    q = d.normalized().to_track_quat('X', 'Z')
    b.data.transform(Matrix.Translation((p0 + p1) / 2) @ q.to_matrix().to_4x4())
    return b


def movers(m, pid, name, path_fn, L, n, dist, maker, group='flow_tracers', ref='flow_tracers', y=0.0, explode=(0, -0.3, 0.2), keep_angle=True):
    """n objects moving along a closed path pos(s)->(x, z, ang) of length L by dist per loop."""
    p = m.part(pid, name, group, explode=explode, info={'ref': ref})
    for i in range(n):
        s0 = L * i / n
        o = maker(i)
        ms = p.add(o, smooth_angle=30)
        lk, rk = [], []
        for f in range(OPERATE_FRAMES + 1):
            xx, zz, aa = path_fn(s0 + dist * f / OPERATE_FRAMES)
            lk.append((1 + f, (xx, y, zz)))
            rk.append((1 + f, (0.0, -aa if keep_angle else 0.0, 0.0)))
        ms.location = lk[0][1]
        m.keyframes(ms, 'Operate', 'location', lk)
        m.keyframes(ms, 'Operate', 'rotation_euler', rk)
    return p


def polyline_path(pts):
    """pos(s) along an open polyline [(x, z)...] (wraps at the end) -> (x, z, ang)."""
    segs, L = [], 0.0
    for a, b in zip(pts[:-1], pts[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        segs.append((a, b, L, d))
        L += d

    def pos(s):
        s %= L
        for a, b, s0, d in segs:
            if s <= s0 + d:
                f = (s - s0) / d if d else 0.0
                return a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, math.atan2(b[1] - a[1], b[0] - a[0])
        a, b, s0, d = segs[-1]
        return b[0], b[1], 0.0
    return pos, L


def rock(name, r, mat='ore', seed=0):
    """Irregular lump: a bevelled box rotated by a pseudo-random angle."""
    o = box(name, (r * 1.6, r * 1.3, r * 1.1), (0, 0, 0), mat, bevel=r * 0.25)
    o = rotate(o, 0.7 + seed * 1.3, 'Z')
    return rotate(o, 0.4 + seed * 0.9, 'X')


def rocks_along(m, pid, name, pts, n, r=0.03, mat='ore', y=0.05, loops=1.0, ref='flow_tracers', shrink=None):
    """Lumps travelling along an open polyline in the XZ plane at depth y (loops per Operate cycle)."""
    pos, L = polyline_path(pts)
    return movers(m, pid, name, pos, L, n, L * loops, lambda i: rock(f'{pid}{i}', r * (0.7 + 0.6 * ((i * 0.37) % 1)), mat, i), y=y, keep_angle=False, ref=ref)


def belt_loop(m, prefix, x0, x1, z, r_pulley, width, revs=1.0, markers=12, mat_belt='belt', y=0.0, label='Belt', ref_belt='hk_belt', ref_pulley='hk_pulley',
              idlers=True, frame=True, frame_mat='paint_grey', foot_z=0.0):
    """Flat belt conveyor between pulleys at x0 (tail) and x1 (head) at height z (pulley centre). Belt moves +x on top."""
    pos, L = open_path(r_pulley, r_pulley, x1 - x0, x0, z)
    # open_path travels clockwise: top run goes +x
    belt = []
    pts = []
    for k in range(121):
        xx, zz, _ = pos(L * k / 120)
        pts.append((xx, zz))
    for side in (-1, 1):
        pass
    top = box(prefix + 'bt', (x1 - x0, width, 0.01), ((x0 + x1) / 2, y, z + r_pulley + 0.005), mat_belt)
    bot = box(prefix + 'bb', (x1 - x0, width, 0.01), ((x0 + x1) / 2, y, z - r_pulley - 0.005), mat_belt)
    wraps = [cyl(prefix + f'bw{i}', r_pulley + 0.01, y - width / 2, y + width / 2, mat_belt, 32, axis='Y', center=(xx, 0, z), r_in=r_pulley) for i, xx in enumerate((x0, x1))]
    from .valvekit import P
    P(m, prefix + 'belt', f'{label}', 'conveyor', [top, bot] + wraps, explode=(0, 0, 0.3), ref=ref_belt, section='keep')
    for i, (xx, nm) in enumerate(((x0, 'Tail'), (x1, 'Head (Drive)'))):
        pul = join(prefix + f'p{i}', [cyl(prefix + f'pd{i}', r_pulley - 0.002, y - width / 2 - 0.01, y + width / 2 + 0.01, 'steel', 32, axis='Y', center=(xx, 0, z)),
                                     cyl(prefix + f'ps{i}', 0.02, y - width / 2 - 0.08, y + width / 2 + 0.08, 'steel', 16, axis='Y', center=(xx, 0, z)),
                                     box(prefix + f'pm{i}', (0.01, width + 0.02, 0.02), (xx, y, z + r_pulley - 0.012), 'paint_yellow')])
        pp = P(m, prefix + f'pulley_{i + 1}', f'{nm} Pulley', 'conveyor', pul, explode=(0.2 * (1 if i else -1), 0, 0.2), ref=ref_pulley, section='keep', pivot=(xx, 0, z))
        pp.spin('Y', revs)
    if markers:
        dist = TAU * r_pulley * revs
        movers(m, prefix + 'marks', f'{label} Motion Markers', pos, L, markers, dist,
               lambda i: box(f'{prefix}mk{i}', (0.02, width * 0.9, 0.004), (0, 0, 0), 'paint_yellow'), group='conveyor', ref=ref_belt, y=y)
    objs = []
    if idlers:
        n = max(2, int((x1 - x0) / 0.3))
        for k in range(1, n):
            xx = x0 + (x1 - x0) * k / n
            for s, a in ((-1, 0.35), (0, 0.0), (1, -0.35)):
                c = cyl(prefix + f'id{k}{s}', 0.025, -width / 6, width / 6, 'steel', 16, axis='Y', center=(xx, 0, 0))
                c = rotate(c, a, 'X')
                c.data.transform(Matrix.Translation((0, y + s * width / 3, z + r_pulley - 0.03 + abs(s) * 0.02)))
                objs.append(c)
            objs.append(cyl(prefix + f'ri{k}', 0.02, y - width / 2, y + width / 2, 'steel', 12, axis='Y', center=(xx, 0, z - r_pulley - 0.03)))
    if frame:
        for s in (-1, 1):
            objs.append(box(prefix + f'st{s}', (x1 - x0, 0.03, 0.08), ((x0 + x1) / 2, y + s * (width / 2 + 0.06), z), frame_mat))
        if foot_z is not None:
            for k, xx in enumerate((x0 + 0.1, (x0 + x1) / 2, x1 - 0.1)):
                for s in (-1, 1):
                    objs.append(box(prefix + f'lg{k}{s}', (0.04, 0.04, z - foot_z), (xx, y + s * (width / 2 + 0.06), (z + foot_z) / 2), frame_mat))
    if objs:
        P(m, prefix + 'frame', f'{label} Frame & Idlers (troughing and return)', 'conveyor', objs, explode=(0, 0, -0.25), ref='hk_idlers', section='keep')
    return pos, L


def wheel(name, x, y, z, r, w=0.05, mat='steel', axis='Y'):
    return cyl(name, r, y - w / 2, y + w / 2, mat, 32, axis='Y', center=(x, 0, z)) if axis == 'Y' else cyl(name, r, x - w / 2, x + w / 2, mat, 32, axis='X', center=(0, y, z))


def rope(name, pts, r=0.006, mat='steel_dark'):
    return sweep_tube(name, pts, r, mat, 8)


def hook_block(name, x, y, z, mat='paint_yellow'):
    blk = box(name + 'b', (0.12, 0.08, 0.16), (x, y, z + 0.08), mat, bevel=0.01)
    sh = [cyl(name + f's{i}', 0.05, y - 0.03 + 0.06 * i - 0.01, y - 0.03 + 0.06 * i + 0.01, 'steel', 24, axis='Y', center=(x, 0, z + 0.12)) for i in range(2)] if False else []
    hk = sweep_tube(name + 'h', [(x, y, z), (x, y, z - 0.06), (x + 0.03, y, z - 0.1), (x + 0.06, y, z - 0.07)], 0.012, 'steel', 10)
    return join(name, [blk, hk] + sh)
