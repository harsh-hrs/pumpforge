"""Real-scale detailing kit for the Mine-to-Port catalog (all dimensions in metres, Blender Z up).

Everything here is built to common engineering practice so that a measured distance in the app is a real distance:
- access ways: handrail 1.0 m (top rail) with knee rail 0.5 m and 100 mm toe board, posts <= 1.8 m apart; fixed
  ladders 450 mm between stiles, rungs at 300 mm, safety cage from 2.2 m with hoops at <= 0.9 m; stairs at ~40 deg
  with 250 mm treads (AS 1657 / OSHA 1910.23-29 / ISO 14122);
- flanges to ASME B16.5 / B16.47 class 150 outside diameters and bolt counts;
- motors to IEC frame sizes (shaft height from rated power), TEFC with cooling fins, fan cowl and terminal box.
Helpers return ordinary Blender objects; register them with pumpforge.valvekit.P like any other geometry.
"""
import math
from mathutils import Matrix, Vector
from .core import lathe, cyl, box, join, transform, extrude_poly, TAU
from .shapes import sweep_tube

V = Vector

# ------------------------------------------------------------------ helpers
def frame(origin, z_dir, y_hint=(0, 0, 1)):
    """Matrix taking local (x, y, z) to world with local z along z_dir."""
    z = V(z_dir).normalized()
    y = V(y_hint)
    if abs(z.dot(y.normalized())) > 0.95:
        y = V((1, 0, 0)) if abs(z.x) < 0.9 else V((0, 1, 0))
    x = y.cross(z).normalized()
    y = z.cross(x).normalized()
    o = V(origin)
    return Matrix(((x.x, y.x, z.x, o.x), (x.y, y.y, z.y, o.y), (x.z, y.z, z.z, o.z), (0, 0, 0, 1)))


def placed(obj, Mx):
    transform(obj, Mx)
    return obj


def bar(name, p0, p1, w, h, mat, up=(0, 0, 1)):
    """Rectangular bar (w across, h along `up`) from p0 to p1."""
    a, b = V(p0), V(p1)
    d = b - a
    L = d.length
    if L < 1e-6:
        return None
    o = box(name, (w, h, L), (0, 0, L / 2), mat)
    up = V(up)
    if abs(d.normalized().dot(up.normalized())) > 0.95:
        up = V((1, 0, 0))
    return placed(o, frame(a, d, up))


def rod(name, p0, p1, r, mat, segs=12):
    a, b = V(p0), V(p1)
    return sweep_tube(name, [tuple(a), tuple(b)], r, mat, segs)


def i_section(name, p0, p1, depth, width, mat='struct_grey', tf=None, tw=None, web_up=(0, 0, 1)):
    """I / H section member between two points; web along web_up."""
    a, b = V(p0), V(p1)
    d = b - a
    L = d.length
    tf = tf or max(0.008, depth * 0.06)
    tw = tw or max(0.006, depth * 0.035)
    parts = [box(name + 'w', (tw, depth - 2 * tf, L), (0, 0, L / 2), mat),
             box(name + 'f1', (width, tf, L), (0, depth / 2 - tf / 2, L / 2), mat),
             box(name + 'f2', (width, tf, L), (0, -depth / 2 + tf / 2, L / 2), mat)]
    up = V(web_up)
    if abs(d.normalized().dot(up.normalized())) > 0.95:
        up = V((1, 0, 0))
    return placed(join(name, parts), frame(a, d, up))


def angle_section(name, p0, p1, leg, mat='galvanised', t=None, up=(0, 0, 1)):
    t = t or max(0.005, leg * 0.1)
    a, b = V(p0), V(p1)
    d = b - a
    L = d.length
    parts = [box(name + 'a', (leg, t, L), (leg / 2, t / 2, L / 2), mat), box(name + 'b', (t, leg, L), (t / 2, leg / 2, L / 2), mat)]
    return placed(join(name, parts), frame(a, d, up))


# ------------------------------------------------------------------ foundations & structure
def concrete_pad(name, x0, y0, x1, y1, z_top, h=0.3, chamfer=0.03):
    return box(name, (x1 - x0, y1 - y0, h), ((x0 + x1) / 2, (y0 + y1) / 2, z_top - h / 2), 'concrete', bevel=chamfer, segs=1)


def ring_foundation(name, R, z_top=0.3, w=0.6, h=0.6):
    """Ringwall foundation for a flat-bottom tank (API 650 style)."""
    return cyl(name, R + w / 2, z_top - h, z_top, 'concrete', 96, r_in=R - w / 2, ch=0.02)


def anchor_bolts(name, n, pcd, z, d=0.036, proj=0.12, phase=0.0, center=(0, 0)):
    objs = []
    for k in range(n):
        a = phase + TAU * k / n
        x, y = center[0] + pcd / 2 * math.cos(a), center[1] + pcd / 2 * math.sin(a)
        objs.append(cyl(f'{name}{k}', d / 2, z, z + proj, 'steel_dark', 10, center=(x, y, 0)))
        objs.append(cyl(f'{name}n{k}', d * 0.9, z + 0.02, z + 0.02 + d * 0.8, 'steel_dark', 6, center=(x, y, 0)))
    return join(name, objs)


def column(name, x, y, z0, z1, size=0.25, mat='struct_grey', base_plate=True):
    objs = [i_section(name + 'c', (x, y, z0), (x, y, z1), size, size, mat, web_up=(1, 0, 0))]
    if base_plate:
        objs.append(box(name + 'bp', (size * 1.8, size * 1.8, 0.03), (x, y, z0 + 0.015), mat))
    return join(name, objs)


def pipe_rack(name, x0, x1, y_c, width, levels, bent_spacing=6.0, col_size=0.3, beam_depth=0.36):
    """Pipe rack along X: bents (two columns + level beams) and longitudinal struts at each level."""
    n = max(1, int(round((x1 - x0) / bent_spacing)))
    objs = []
    top = max(levels)
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        for s in (-1, 1):
            objs.append(column(f'{name}c{i}{s}', x, y_c + s * width / 2, 0.0, top + 0.3, col_size))
        for k, z in enumerate(levels):
            objs.append(i_section(f'{name}b{i}{k}', (x, y_c - width / 2 - col_size / 2, z), (x, y_c + width / 2 + col_size / 2, z), beam_depth, beam_depth * 0.55))
    for k, z in enumerate(levels):
        for s in (-1, 1):
            objs.append(i_section(f'{name}l{k}{s}', (x0, y_c + s * width / 2, z + beam_depth / 2 + 0.1), (x1, y_c + s * width / 2, z + beam_depth / 2 + 0.1), 0.2, 0.1))
    return join(name, objs)


# ------------------------------------------------------------------ access: grating, handrails, ladders, stairs
def handrail(name, pts, h=1.0, post_max=1.8, closed=False, mat='safety_yellow', toe=True):
    """Handrail along a polyline at floor level pts (x, y, z): top rail, knee rail, posts, toe board."""
    P = [V(p) for p in pts] + ([V(pts[0])] if closed else [])
    objs = []
    for i in range(len(P) - 1):
        a, b = P[i], P[i + 1]
        seg = b - a
        L = seg.length
        if L < 0.05:
            continue
        objs.append(rod(f'{name}t{i}', a + V((0, 0, h)), b + V((0, 0, h)), 0.024, mat))
        objs.append(rod(f'{name}k{i}', a + V((0, 0, h * 0.5)), b + V((0, 0, h * 0.5)), 0.016, mat))
        if toe:
            objs.append(bar(f'{name}e{i}', a + V((0, 0, 0.0)), b + V((0, 0, 0.0)), 0.006, 0.2, mat))   # 100 mm toe board above deck (half below)
        n = max(1, math.ceil(L / post_max))
        for k in range(n + (1 if (i == len(P) - 2 and not closed) else 0)):
            p = a + seg * (k / n)
            objs.append(rod(f'{name}p{i}_{k}', p, p + V((0, 0, h)), 0.022, mat, 10))
    return join(name, objs)


def grating_rect(name, x0, y0, x1, y1, z, t=0.04, edge=True, rail_sides=('n', 'e', 's', 'w'), h=1.0):
    """Rectangular platform: grating deck on edge angles, handrail on the listed sides (n = +y, e = +x)."""
    objs = [box(name + 'd', (x1 - x0, y1 - y0, t), ((x0 + x1) / 2, (y0 + y1) / 2, z - t / 2), 'grating')]
    if edge:
        for k, (a, b) in enumerate((((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0)))):
            objs.append(bar(f'{name}ea{k}', (a[0], a[1], z - 0.05), (b[0], b[1], z - 0.05), 0.012, 0.1, 'galvanised'))
    sides = {'s': [(x0, y0, z), (x1, y0, z)], 'e': [(x1, y0, z), (x1, y1, z)], 'n': [(x1, y1, z), (x0, y1, z)], 'w': [(x0, y1, z), (x0, y0, z)]}
    for s in rail_sides:
        objs.append(handrail(f'{name}h{s}', sides[s], h))
    return join(name, objs)


def grating_ring(name, cx, cy, r_in, r_out, z, a0=0.0, a1=TAU, t=0.04, rail=True, inner_rail=False, brackets=True, h=1.0, segs=48):
    """Circular (or segment) platform round a vertical vessel, with knee brackets back to the shell."""
    n = max(6, int(segs * (a1 - a0) / TAU))
    prof = [(r_in, z - t), (r_out, z - t), (r_out, z), (r_in, z)]
    deck = lathe(name + 'd', prof + [prof[0]], 'grating', n, a0=a0, a1=a1, center=(cx, cy, 0))
    objs = [deck, lathe(name + 'ke', [(r_out - 0.006, z - 0.1), (r_out + 0.006, z - 0.1), (r_out + 0.006, z), (r_out - 0.006, z), (r_out - 0.006, z - 0.1)], 'galvanised', n, a0=a0, a1=a1, center=(cx, cy, 0))]
    if rail:
        pts = [(cx + (r_out - 0.03) * math.cos(a0 + (a1 - a0) * k / n), cy + (r_out - 0.03) * math.sin(a0 + (a1 - a0) * k / n), z) for k in range(n + 1)]
        objs.append(handrail(name + 'ho', pts, h, post_max=1.8))
    if inner_rail:
        pts = [(cx + (r_in + 0.03) * math.cos(a0 + (a1 - a0) * k / n), cy + (r_in + 0.03) * math.sin(a0 + (a1 - a0) * k / n), z) for k in range(n + 1)]
        objs.append(handrail(name + 'hi', pts, h, post_max=1.8))
    if brackets:
        nb = max(2, int((a1 - a0) * (r_in + r_out) / 2 / 2.0))
        for k in range(nb + 1):
            a = a0 + (a1 - a0) * k / nb
            c, s = math.cos(a), math.sin(a)
            p_shell_lo = V((cx + r_in * c, cy + r_in * s, z - (r_out - r_in) * 0.8))
            p_out = V((cx + (r_out - 0.05) * c, cy + (r_out - 0.05) * s, z - t))
            p_in = V((cx + r_in * c, cy + r_in * s, z - t))
            objs.append(bar(f'{name}bt{k}', p_in, p_out, 0.08, 0.12, 'galvanised'))
            objs.append(bar(f'{name}bk{k}', p_shell_lo, p_out, 0.06, 0.08, 'galvanised'))
    return join(name, objs)


def ladder(name, base, z1, facing=(0, -1, 0), cage=True, width=0.45, mat='safety_yellow', extend=1.0):
    """Fixed vertical ladder. base = (x, y, z0) at the climbing face centre; the climber faces -facing
    (stands on the `facing` side). Stiles extend `extend` above the landing at z1."""
    x, y, z0 = base
    f = V(facing).normalized()
    side = V((-f.y, f.x, 0))
    top = z1 + extend
    objs = []
    for s in (-1, 1):
        a = V((x, y, z0)) + side * (s * width / 2)
        objs.append(bar(f'{name}s{s}', a, a + V((0, 0, top - z0)), 0.065, 0.012, mat, up=tuple(side)))
    n = int((z1 - z0) / 0.3)
    for k in range(1, n + 1):
        z = z0 + k * 0.3
        a = V((x, y, z)) - side * (width / 2)
        objs.append(rod(f'{name}r{k}', a, a + side * width, 0.012, 'galvanised', 8))
    if cage and z1 - z0 > 3.0:
        R = 0.36                                           # 720 mm hoop diameter
        c0 = V((x, y, 0)) + f * (R - 0.0)
        hz = [z0 + 2.2 + 0.9 * k for k in range(int((top - z0 - 2.2) / 0.9) + 1)]
        for k, z in enumerate(hz):
            pts = []
            for j in range(13):
                a = math.atan2(-side.y, -side.x) + math.pi * j / 12
                p = c0 + V((math.cos(a) * R, math.sin(a) * R, 0))
                pts.append((p.x, p.y, z))
            # hoop: half circle + straight returns to the stiles
            sa = V((x, y, z)) - side * (width / 2 + 0.03)
            sb = V((x, y, z)) + side * (width / 2 + 0.03)
            pts = [tuple(sa)] + pts + [tuple(sb)]
            objs.append(sweep_tube(f'{name}h{k}', pts, 0.012, mat, 8, cap=True))
        if hz:
            for j in range(5):                              # vertical cage bars
                a = math.atan2(-side.y, -side.x) + math.pi * (j + 0.5) / 5
                p = c0 + V((math.cos(a) * R, math.sin(a) * R, 0))
                objs.append(bar(f'{name}v{j}', (p.x, p.y, hz[0]), (p.x, p.y, hz[-1]), 0.05, 0.008, mat))
    return join(name, objs)


def stair(name, p0, p1, width=0.9, mat='galvanised', rail=True):
    """Straight stair flight from bottom landing point p0 to top landing point p1 (centre line)."""
    a, b = V(p0), V(p1)
    d = b - a
    rise = d.z
    run = V((d.x, d.y, 0))
    n = max(2, int(round(rise / 0.19)))
    fwd = run.normalized()
    side = V((-fwd.y, fwd.x, 0))
    objs = []
    for s in (-1, 1):
        o = side * (s * width / 2)
        objs.append(bar(f'{name}st{s}', a + o + V((0, 0, -0.1)), b + o + V((0, 0, -0.1)), 0.012, 0.25, 'struct_grey', up=tuple(V((0, 0, 1)))))
    for k in range(1, n + 1):
        p = a + run * ((k - 0.5) / n) + V((0, 0, rise * k / n))
        objs.append(box(f'{name}t{k}', (0.27, width - 0.04, 0.035), (0, 0, 0), 'grating'))
        M = frame(p - V((0, 0, 0.0175)), (0, 0, 1), tuple(side))
        transform(objs[-1], Matrix.Translation(p - V((0, 0, 0.0175))) @ Matrix.Rotation(math.atan2(fwd.y, fwd.x), 4, 'Z'))
    if rail:
        for s in (-1, 1):
            o = side * (s * (width / 2 + 0.02))
            objs.append(handrail(f'{name}h{s}', [tuple(a + o), tuple(b + o)], 0.9, post_max=1.6, toe=False))
    return join(name, objs)


# ------------------------------------------------------------------ flanges, nozzles, piping
NPS = {  # NPS: (pipe OD m, class-150 flange OD m, bolts, bolt circle m)
    1: (0.0334, 0.108, 4, 0.0794), 1.5: (0.0483, 0.127, 4, 0.0984), 2: (0.0603, 0.152, 4, 0.1206), 3: (0.0889, 0.190, 4, 0.1524),
    4: (0.1143, 0.229, 8, 0.1905), 6: (0.1683, 0.279, 8, 0.2413), 8: (0.2191, 0.343, 8, 0.2984), 10: (0.2731, 0.406, 12, 0.3620),
    12: (0.3239, 0.483, 12, 0.4318), 14: (0.3556, 0.533, 12, 0.4763), 16: (0.4064, 0.597, 16, 0.5397), 18: (0.4572, 0.635, 16, 0.5779),
    20: (0.5080, 0.699, 20, 0.6350), 24: (0.6096, 0.813, 20, 0.7493), 30: (0.7620, 0.984, 28, 0.9144), 36: (0.9144, 1.168, 32, 1.0858),
    42: (1.0668, 1.346, 36, 1.2573), 48: (1.2192, 1.511, 44, 1.4224)}


def nps_of(od):
    return min(NPS, key=lambda k: abs(NPS[k][0] - od))


def flange_set(name, center, axis, nps, mat='steel', cls=150, pair=True):
    """Flanged joint (or single flange) centred on `center` normal to `axis`: weld-neck flange(s), gasket, bolts."""
    od, fod, nb, pcd = NPS[nps]
    k = 1.0 if cls <= 150 else 1.18
    fod, pcd = fod * k, pcd * k
    th = max(0.018, fod * 0.085)
    objs = []
    for s in ((-1, 1) if pair else (1,)):
        z0, z1 = (0.0, th) if s > 0 else (-th, 0.0)
        objs.append(cyl(f'{name}f{s}', fod / 2, z0, z1, mat, 48, r_in=od / 2 - 0.006, ch=0.002))
        hl = max(0.03, od * 0.35)
        if s > 0:   # tapered weld-neck hub, wide at the flange, narrowing to the pipe
            prof = [(od / 2 - 0.006, th), (od / 2 * 1.16 + 0.004, th), (od / 2 + 0.003, th + hl), (od / 2 - 0.006, th + hl)]
        else:
            prof = [(od / 2 - 0.006, -th - hl), (od / 2 + 0.003, -th - hl), (od / 2 * 1.16 + 0.004, -th), (od / 2 - 0.006, -th)]
        objs.append(lathe(f'{name}h{s}', prof, mat, 32))
    if pair:
        objs.append(cyl(name + 'g', (pcd - 0.02) / 2, -0.0015, 0.0015, 'rubber', 40, r_in=od / 2))
    bl = th * (2.0 if pair else 1.0) + 0.05
    bd = max(0.016, fod * 0.045)
    for j in range(nb):
        a = TAU * (j + 0.5) / nb
        x, y = pcd / 2 * math.cos(a), pcd / 2 * math.sin(a)
        z_lo = -th - 0.025 if pair else -0.02
        objs.append(cyl(f'{name}b{j}', bd / 2, z_lo, z_lo + bl, 'steel_dark', 8, center=(x, y, 0)))
        for zz in ((th, th + bd * 0.8),) + (((-th - bd * 0.8, -th),) if pair else ()):
            objs.append(cyl(f'{name}n{j}{zz[0]:.3f}', bd * 0.85, zz[0], zz[1], 'steel_dark', 6, center=(x, y, 0)))
    return placed(join(name, objs), frame(center, axis))


def nozzle(name, base, direction, nps, L=None, mat='steel', pad=True, shell_r=None, blind=False):
    """Vessel nozzle: neck from base (on the shell surface) outwards, reinforcing pad, weld-neck flange + bolts
    (+ blind flange if `blind`). Returns the joined object; the flange face is at base + direction * L."""
    od = NPS[nps][0]
    L = L or max(0.15, od * 1.2 + 0.1)
    d = V(direction).normalized()
    b = V(base)
    objs = [sweep_tube(name + 'n', [tuple(b - d * 0.05), tuple(b + d * (L - 0.03))], od / 2, mat, 32)]
    if pad and od > 0.08:
        objs.append(placed(cyl(name + 'pd', od * 0.95, -0.01, 0.012, mat, 40), frame(b, d)))
    fod, th = NPS[nps][1], max(0.018, NPS[nps][1] * 0.085)
    objs.append(placed(cyl(name + 'f', fod / 2, -th, 0.0, mat, 48, ch=0.002), frame(b + d * L, d)))
    objs.append(placed(lathe(name + 'hb', [(od / 2, -th - max(0.03, od * 0.35)), (od / 2 * 1.16 + 0.004, -th), (od / 2, -th)], mat, 32), frame(b + d * L, d)))
    nb, pcd = NPS[nps][2], NPS[nps][3]
    bd = max(0.016, fod * 0.045)
    for j in range(nb):
        a = TAU * (j + 0.5) / nb
        x, y = pcd / 2 * math.cos(a), pcd / 2 * math.sin(a)
        objs.append(placed(cyl(f'{name}b{j}', bd / 2, -th - 0.02, (0.06 if blind else 0.03), 'steel_dark', 8, center=(x, y, 0)), frame(b + d * L, d)))
    if blind:
        objs.append(placed(cyl(name + 'bl', fod / 2, 0.003, 0.003 + th, mat, 48, ch=0.002), frame(b + d * L, d)))
    return join(name, objs)


def manway(name, base, direction, d_in=0.6, L=0.35, davit=True, mat='steel'):
    """Bolted manway (blind cover on a 24 in nozzle) with hinge davit."""
    nps = 24 if d_in <= 0.62 else 30
    objs = [nozzle(name + 'n', base, direction, nps, L, mat, blind=True)]
    d = V(direction).normalized()
    if davit:
        tip = V(base) + d * (L + 0.05)
        side = d.cross(V((0, 0, 1)))
        if side.length < 0.1:
            side = V((1, 0, 0))
        side.normalize()
        fod = NPS[nps][1]
        pivot = V(base) + d * (L * 0.4) + side * (fod / 2 + 0.12)
        objs.append(rod(name + 'dv', pivot - V((0, 0, 0.35)), pivot + V((0, 0, 0.25)), 0.025, 'steel_dark'))
        arm_end = tip + V((0, 0, 0.25))
        objs.append(sweep_tube(name + 'da', [tuple(pivot + V((0, 0, 0.25))), tuple(pivot + V((0, 0, 0.32)) + (arm_end - pivot) * 0.5), tuple(arm_end)], 0.02, 'steel_dark', 10))
        objs.append(rod(name + 'dh', arm_end, tip + V((0, 0, 0.02)), 0.012, 'steel_dark'))
    return join(name, objs)


def pipe_run(name, pts, nps, mat='pipe_liquor', bend=None, flanges=(), segs=24, insulated=False):
    """Pipe along a polyline with long-radius elbows (1.5 D) and optional flanged joints at given segment
    fractions: flanges = [(segment index, fraction), ...]."""
    od = NPS[nps][0]
    r = od / 2 + (0.05 if insulated else 0.0)
    bend = bend if bend is not None else 1.5 * NPS[nps][0] * 1.0 + 0.02
    P = [V(p) for p in pts]
    path = [P[0]]
    for i in range(1, len(P) - 1):
        a, b, c = P[i - 1], P[i], P[i + 1]
        d1, d2 = (b - a).normalized(), (c - b).normalized()
        if d1.dot(d2) > 0.999:
            path.append(b)
            continue
        rr = min(bend * math.tan(math.acos(max(-1, min(1, d1.dot(d2)))) / 2), (b - a).length / 2, (c - b).length / 2)
        p0, p1 = b - d1 * rr, b + d2 * rr
        for k in range(9):
            t = k / 8
            path.append((1 - t) ** 2 * p0 + 2 * (1 - t) * t * b + t * t * p1)
    path.append(P[-1])
    objs = [sweep_tube(name + 'p', [tuple(p) for p in path], r, 'pipe_steam' if insulated else mat, segs)]
    for k, (i, f) in enumerate(flanges):
        a, b = P[i], P[i + 1]
        if not insulated:
            objs.append(flange_set(f'{name}fl{k}', a + (b - a) * f, b - a, nps, 'steel'))
    return join(name, objs)


def pipe_shoe(name, p, nps, z_support):
    od = NPS[nps][0]
    x, y, z = p
    return join(name, [box(name + 's', (0.3, od * 0.8, max(0.02, z - od / 2 - z_support)), (x, y, (z - od / 2 + z_support) / 2), 'steel_dark')])


# ------------------------------------------------------------------ valves
def gate_valve(name, center, axis, nps, mat='paint_grey', up=(0, 0, 1), actuator=None):
    """Flanged gate (or knife-gate) valve with rising stem, yoke and handwheel (or pneumatic cylinder)."""
    od, fod = NPS[nps][0], NPS[nps][1]
    L = max(0.2, od * 1.4 + 0.1)
    loc = []
    loc.append(cyl(name + 'b', od * 0.78, -L * 0.35, L * 0.35, mat, 40))
    for s in (-1, 1):
        loc.append(cyl(f'{name}f{s}', fod / 2, s * L / 2 - (0.025 if s > 0 else 0), s * L / 2 + (0 if s > 0 else 0.025), mat, 40, ch=0.002))
    body = join(name + 'bd', loc)
    M = frame(center, axis, up)
    transform(body, M)
    u = V(up).normalized()
    c = V(center)
    h = od * 0.9 + 0.08
    bon = placed(box(name + 'bo', (od * 1.3, fod * 0.55, h), (0, 0, h / 2), mat, bevel=0.01), frame(c + u * (od * 0.55), u, tuple(V(axis))))
    stem_top = c + u * (od * 0.55 + h + od * 1.1 + 0.15)
    objs = [body, bon, rod(name + 'st', c + u * (od * 0.55 + h), stem_top, max(0.012, od * 0.06), 'stainless')]
    if actuator == 'pneumatic':
        objs.append(placed(cyl(name + 'ac', max(0.06, od * 0.45), 0, max(0.25, od * 1.6), 'paint_blue', 32), frame(c + u * (od * 0.55 + h), u)))
    else:
        objs.append(placed(lathe(name + 'hw', [(max(0.08, od * 0.7), -0.012), (max(0.08, od * 0.7) + 0.02, -0.012), (max(0.08, od * 0.7) + 0.02, 0.012), (max(0.08, od * 0.7), 0.012), (max(0.08, od * 0.7), -0.012)], 'paint_red', 32), frame(stem_top - u * 0.08, u)))
        for k in range(4):
            a = TAU * k / 4
            hw_r = max(0.08, od * 0.7)
            e = frame(stem_top - u * 0.08, u)
            objs.append(placed(rod(f'{name}sp{k}', (0, 0, 0), (hw_r * math.cos(a), hw_r * math.sin(a), 0), 0.008, 'paint_red'), e))
    return join(name, objs)


def control_valve(name, center, axis, nps, mat='paint_grey', up=(0, 0, 1)):
    """Globe control valve with spring-diaphragm actuator, yoke and positioner."""
    od, fod = NPS[nps][0], NPS[nps][1]
    L = max(0.25, od * 2.4 + 0.1)
    loc = [lathe(name + 'gb', [(0, -od * 0.9), (od * 0.85, -od * 0.6), (od * 0.95, 0), (od * 0.85, od * 0.6), (0, od * 0.9)], mat, 32, axis='X')]
    loc += [cyl(f'{name}n{s}', od * 0.55, 0, s * L / 2, mat, 32, axis='X') if s > 0 else cyl(f'{name}n{s}', od * 0.55, s * L / 2, 0, mat, 32, axis='X') for s in (-1, 1)]
    loc += [cyl(f'{name}f{s}', fod / 2, s * L / 2 - (0.025 if s > 0 else 0), s * L / 2 + (0 if s > 0 else 0.025), mat, 40, axis='X') for s in (-1, 1)]
    body = join(name + 'bd', loc)
    a = V(axis).normalized()
    u = V(up).normalized()
    side = u.cross(a)
    M = Matrix(((a.x, side.x, u.x, center[0]), (a.y, side.y, u.y, center[1]), (a.z, side.z, u.z, center[2]), (0, 0, 0, 1)))
    transform(body, M)
    c = V(center)
    dr = max(0.14, od * 1.2)
    y0 = c + u * (od * 0.9)
    objs = [body, placed(cyl(name + 'bn', od * 0.4, 0, od * 0.6, mat, 24), frame(y0, u))]
    for s in (-1, 1):
        objs.append(bar(f'{name}y{s}', y0 + u * (od * 0.6) + side * (s * od * 0.35), y0 + u * (od * 0.6 + 0.25 + od) + side * (s * od * 0.35), 0.03, 0.02, 'paint_grey'))
    top = y0 + u * (od * 0.6 + 0.25 + od)
    objs.append(placed(lathe(name + 'dia', [(0, 0), (dr, 0), (dr, 0.03), (dr * 0.85, dr * 0.45), (0, dr * 0.5)], 'paint_blue', 40), frame(top, u)))
    objs.append(placed(lathe(name + 'dib', [(0, 0), (dr * 0.85, -dr * 0.4), (dr, -0.03), (dr, 0), (0, 0)][::-1], 'paint_blue', 40), frame(top, u)))
    objs.append(placed(box(name + 'pos', (0.14, 0.12, 0.18), (0, 0, 0.09), 'paint_grey'), frame(y0 + u * (od * 0.6 + 0.08) + side * (od * 0.35 + 0.12), u, tuple(a))))
    return join(name, objs)


# ------------------------------------------------------------------ instruments
def pressure_transmitter(name, base, direction, up=(0, 0, 1)):
    """Root valve on a short tapping, 2-valve manifold and transmitter housing with display (dual compartment)."""
    d = V(direction).normalized()
    b = V(base)
    objs = [rod(name + 't', b, b + d * 0.12, 0.016, 'stainless'), placed(cyl(name + 'rv', 0.03, 0, 0.07, 'stainless', 6), frame(b + d * 0.12, d)),
            rod(name + 't2', b + d * 0.19, b + d * 0.3, 0.012, 'stainless'), placed(box(name + 'mf', (0.06, 0.06, 0.1), (0, 0, 0.05), 'stainless'), frame(b + d * 0.3, d)),
            placed(cyl(name + 'hs', 0.055, 0, 0.12, 'paint_blue', 24, axis='Z'), frame(b + d * 0.4 + V(up) * 0.0, V(up))),
            placed(cyl(name + 'ds', 0.045, 0, 0.03, 'glass', 24), frame(b + d * 0.4 + V(up) * 0.06 + d * 0.055, d))]
    return join(name, objs)


def pressure_gauge(name, base, direction, dial=0.1):
    d = V(direction).normalized()
    b = V(base)
    return join(name, [rod(name + 't', b, b + d * 0.12, 0.012, 'stainless'), placed(cyl(name + 'v', 0.025, 0, 0.05, 'brass', 6), frame(b + d * 0.12, d)),
                       rod(name + 's', b + d * 0.17, b + d * 0.24, 0.008, 'brass'),
                       placed(cyl(name + 'c', dial / 2, -0.035, 0.0, 'stainless', 32), frame(b + d * 0.24 + V((0, 0, dial / 2)), V((0, 0, 1)).cross(d).cross(V((0, 0, 1))) if abs(d.z) < 0.9 else V((1, 0, 0)))),
                       placed(cyl(name + 'f', dial / 2 - 0.004, 0.0, 0.004, 'glass', 32), frame(b + d * 0.24 + V((0, 0, dial / 2)), V((0, 0, 1)).cross(d).cross(V((0, 0, 1))) if abs(d.z) < 0.9 else V((1, 0, 0))))])


def temperature_element(name, base, direction):
    """Flanged thermowell with connection head and transmitter."""
    d = V(direction).normalized()
    b = V(base)
    return join(name, [rod(name + 'w', b - d * 0.2, b + d * 0.12, 0.012, 'stainless'), placed(cyl(name + 'fl', 0.06, 0, 0.02, 'stainless', 24), frame(b + d * 0.12, d)),
                       rod(name + 'x', b + d * 0.14, b + d * 0.3, 0.014, 'stainless'), placed(lathe(name + 'hd', [(0, 0), (0.045, 0), (0.05, 0.03), (0.05, 0.07), (0.035, 0.09), (0, 0.09)], 'aluminium', 24), frame(b + d * 0.3, d))])


def radar_level(name, top, cover=True):
    """Non-contact radar level transmitter on a roof nozzle (horn antenna inside, housing on top)."""
    x, y, z = top
    return join(name, [nozzle(name + 'nz', (x, y, z), (0, 0, 1), 6, 0.25, 'steel'),
                       cyl(name + 'hs', 0.06, z + 0.27, z + 0.42, 'aluminium', 24, center=(x, y, 0)),
                       lathe(name + 'cp', [(0, z + 0.42), (0.06, z + 0.42), (0.055, z + 0.46), (0, z + 0.47)], 'aluminium', 24, center=(x, y, 0)),
                       cyl(name + 'gl', 0.035, z + 0.33, z + 0.37, 'glass', 24, axis='Y', center=(x, y - 0.055, 0) if False else (x, y - 0.055, z + 0.35))])


def junction_box(name, pos, facing=(0, -1, 0)):
    d = V(facing).normalized()
    return placed(join(name, [box(name + 'b', (0.3, 0.4, 0.15), (0, 0, 0.075), 'paint_grey', bevel=0.01), box(name + 'l', (0.28, 0.38, 0.01), (0, 0, 0.155), 'paint_grey')]), frame(pos, d, (0, 0, 1)))


# ------------------------------------------------------------------ electric motors & gearboxes
def iec_frame(kw):
    """IEC shaft height H (m) for a 4-pole TEFC motor of rated power kW (typical catalogue values)."""
    table = [(4, 0.112), (7.5, 0.132), (15, 0.160), (22, 0.180), (37, 0.200), (45, 0.225), (55, 0.250), (90, 0.280), (132, 0.315), (250, 0.355),
             (400, 0.400), (560, 0.450), (800, 0.500), (1250, 0.560), (2000, 0.630), (3150, 0.710), (5000, 0.800)]
    for p, h in table:
        if kw <= p:
            return h
    return 0.9


def motor(name, shaft_end, axis, kw, up=(0, 0, 1), mat='paint_motor', foot=True):
    """TEFC induction motor: finned frame, end shields, fan cowl, terminal box, feet, lifting eyes, shaft.
    shaft_end = drive-end shaft tip, axis points from the motor towards the driven machine."""
    H = iec_frame(kw)
    R = H * 0.98                                 # frame radius incl. fins
    L = H * 3.6                                  # frame length (DE shield face to fan cowl end)
    sh_r = max(0.02, H * 0.12)
    sh_L = max(0.08, H * 0.55)
    loc = [cyl(name + 'sh', sh_r, -sh_L, 0.0, 'steel', 24, axis='Z')]
    z_de = -sh_L
    loc.append(lathe(name + 'de', [(sh_r * 1.3, z_de), (R * 0.8, z_de - 0.02), (R * 0.92, z_de - 0.08), (R * 0.92, z_de - 0.1)], mat, 48))
    body0, body1 = z_de - 0.1, z_de - 0.1 - L * 0.72
    loc.append(cyl(name + 'bd', R * 0.86, body1, body0, mat, 48))
    nf = 28
    for k in range(nf):
        a = TAU * k / nf
        if abs(math.sin(a)) > 0.93 and math.sin(a) < 0:
            continue
        loc.append(box(f'{name}fn{k}', (0.008, R * 0.16, L * 0.7), (math.cos(a) * R * 0.92, math.sin(a) * R * 0.92, (body0 + body1) / 2), mat))
        loc[-1].data.transform(Matrix.Translation((math.cos(a) * R * 0.92, math.sin(a) * R * 0.92, 0)) @ Matrix.Rotation(a, 4, 'Z') @ Matrix.Translation((-math.cos(a) * R * 0.92, -math.sin(a) * R * 0.92, 0)))
    loc.append(lathe(name + 'ns', [(R * 0.92, body1), (R * 0.92, body1 - 0.04), (R * 0.75, body1 - 0.08)], mat, 48))
    loc.append(lathe(name + 'cw', [(R * 0.95, body1 - 0.06), (R * 0.97, body1 - L * 0.26), (R * 0.6, body1 - L * 0.28), (0.0, body1 - L * 0.285)], mat, 48))
    for k in range(10):
        a = TAU * k / 10
        loc.append(box(f'{name}cg{k}', (0.01, R * 0.5, 0.012), (math.cos(a) * R * 0.33, math.sin(a) * R * 0.33, body1 - L * 0.286), 'steel_dark'))
    # terminal box on top (local +y is "up" after framing), feet at -y
    loc.append(box(name + 'tb', (R * 0.75, R * 0.45, R * 0.75), (0, R * 0.98 + R * 0.2, (body0 + body1) / 2 + L * 0.12), mat, bevel=0.01))
    loc.append(cyl(name + 'gl', R * 0.08, R * 1.2, R * 1.32, 'steel_dark', 16, axis='Y', center=(R * 0.25, 0, (body0 + body1) / 2 + L * 0.12)))
    for s in (-1, 1):
        loc.append(lathe(f'{name}le{s}', [(0.02, 0), (0.04, 0), (0.04, 0.01), (0.02, 0.01)], 'steel_dark', 16, axis='Y', center=(0, R * 0.95 + 0.04, (body0 + body1) / 2 + s * L * 0.25)))
    if foot:
        for s in (-1, 1):
            loc.append(box(f'{name}ft{s}', (R * 1.9, H - R * 0.55, L * 0.16), (0, -(H + R * 0.55) / 2 + 0.0, z_de - 0.1 - (0.12 if s > 0 else 0.6) * L), mat))
            loc[-1].data.transform(Matrix.Translation((0, 0, 0)))
    loc.append(box(name + 'np', (R * 0.4, 0.004, R * 0.25), (R * 0.45, R * 0.7, (body0 + body1) / 2), 'nameplate'))
    obj = join(name, loc)
    a = V(axis).normalized()
    u = V(up).normalized()
    x = u.cross(a).normalized()
    # local z = -axis direction is the motor body; local y = up
    z_loc = a
    Mx = Matrix(((x.x, u.x, z_loc.x, shaft_end[0]), (x.y, u.y, z_loc.y, shaft_end[1]), (x.z, u.z, z_loc.z, shaft_end[2]), (0, 0, 0, 1)))
    transform(obj, Mx)
    return obj, H


def gearbox(name, in_c, out_c, size, mat='paint_grey', up=(0, 0, 1)):
    """Parallel-shaft gearbox housing spanning input centre in_c to output centre out_c (same axis direction
    across the housing), size = (width along shafts, height, extra length)."""
    a, b = V(in_c), V(out_c)
    d = b - a
    w, h, ext = size
    L = d.length + ext
    c = (a + b) / 2
    objs = [box(name + 'h', (L, w, h), (0, 0, 0), mat, bevel=0.02), box(name + 'sp', (L + 0.06, w + 0.06, 0.05), (0, 0, 0.02), mat)]
    for k in range(5):
        x = -L / 2 + L * (k + 0.5) / 5
        objs.append(box(f'{name}r{k}', (0.03, w + 0.03, h * 0.9), (x, 0, -h * 0.02), mat))
    objs.append(cyl(name + 'br', 0.03, h / 2, h / 2 + 0.08, 'steel_dark', 12, center=(L * 0.3, 0, 0)))
    objs.append(cyl(name + 'sg', 0.03, -0.01, 0.02, 'glass', 16, axis='Y', center=(-L * 0.35, -w / 2 - 0.01, -h * 0.2)))
    dd = d.normalized() if d.length > 1e-6 else V((1, 0, 0))
    u = V(up).normalized()
    y = u.cross(dd).normalized()
    Mx = Matrix(((dd.x, y.x, u.x, c.x), (dd.y, y.y, u.y, c.y), (dd.z, y.z, u.z, c.z), (0, 0, 0, 1)))
    o = join(name, objs)
    transform(o, Mx)
    return o


def coupling_guard(name, p0, p1, r, mat='safety_yellow'):
    a, b = V(p0), V(p1)
    d = b - a
    return placed(join(name, [cyl(name + 'g', r, 0, d.length, mat, 24, r_in=r - 0.006), box(name + 'f', (r * 2.6, 0.01, d.length), (0, -r * 1.05, d.length / 2), mat)]), frame(a, d))


# ------------------------------------------------------------------ vessel trim
def insulation_bands(name, R, z0, z1, pitch=0.6, cx=0.0, cy=0.0, w=0.02):
    objs = []
    n = max(1, int((z1 - z0) / pitch))
    for k in range(1, n + 1):
        z = z0 + (z1 - z0) * k / (n + 1)
        objs.append(cyl(f'{name}{k}', R + 0.004, z - w / 2, z + w / 2, 'stainless', 64, center=(cx, cy, 0)))
    return join(name, objs)


def lifting_lug(name, pos, normal, size=0.25):
    n = V(normal).normalized()
    return placed(join(name, [box(name + 'p', (size, 0.04, size * 1.2), (0, 0, size * 0.6), 'steel'), cyl(name + 'h', size * 0.2, -0.03, 0.03, 'steel_dark', 16, axis='Y', center=(0, 0, size * 0.85))]), frame(pos, n, (0, 0, 1)))


def nameplate(name, pos, normal, w=0.3, h=0.2):
    n = V(normal).normalized()
    return placed(join(name, [box(name + 'b', (w + 0.04, h + 0.04, 0.03), (0, 0, 0.015), 'steel'), box(name + 'p', (w, h, 0.004), (0, 0, 0.032), 'nameplate')]), frame(pos, n, (0, 0, 1)))


def earthing_boss(name, pos, normal):
    n = V(normal).normalized()
    return placed(join(name, [box(name + 'b', (0.08, 0.05, 0.02), (0, 0, 0.01), 'copper')]), frame(pos, n, (0, 0, 1)))


def skirt(name, R, z0, z1, cx=0.0, cy=0.0, access=True, t=0.016):
    """Cylindrical support skirt with base ring, anchor chairs and an access opening (at -y)."""
    objs = [cyl(name + 's', R, z0 + 0.04, z1, 'paint_grey', 96, r_in=R - t, center=(cx, cy, 0)),
            cyl(name + 'br', R + 0.15, z0, z0 + 0.04, 'paint_grey', 96, r_in=R - 0.15, center=(cx, cy, 0))]
    n = max(8, int(TAU * R / 0.9) // 4 * 4)
    for k in range(n):
        a = TAU * (k + 0.5) / n
        x, y = cx + (R + 0.08) * math.cos(a), cy + (R + 0.08) * math.sin(a)
        for s in (-1, 1):
            ga = a + s * 0.05 / R * 2
            objs.append(box(f'{name}c{k}{s}', (0.16, 0.016, 0.3), (cx + (R + 0.08) * math.cos(ga), cy + (R + 0.08) * math.sin(ga), z0 + 0.19), 'paint_grey'))
            objs[-1].data.transform(Matrix.Translation((cx + (R + 0.08) * math.cos(ga), cy + (R + 0.08) * math.sin(ga), 0)) @ Matrix.Rotation(ga, 4, 'Z') @ Matrix.Translation((-(cx + (R + 0.08) * math.cos(ga)), -(cy + (R + 0.08) * math.sin(ga)), 0)))
        objs.append(cyl(f'{name}ab{k}', 0.02, z0 + 0.3, z0 + 0.42, 'steel_dark', 8, center=(x, y, 0)))
    return join(name, objs)


# ------------------------------------------------------------------ belt conveyors (CEMA / AS 1755 practice)
def conveyor(name, p0, p1, belt_w, idler_pitch=1.2, return_pitch=3.0, trough_deg=35, walkway='+', head_pulley_d=None, tail_pulley_d=None,
             frame_mat='struct_grey', cover=False, impact_len=0.0, legs=True, ground_z=0.0, ends=(True, True)):
    """Troughed belt conveyor in a vertical plane from tail pulley centre p0 to head pulley centre p1 (x/y horizontal direction,
    any slope). Returns (static_obj, belt_obj, path) where path = (origin, unit direction, length, belt-top offset) for moving loads.
    Includes stringers, troughed carry idlers (3-roll), impact beds, return idlers, pulleys, belt (carry + return), walkway + handrail,
    support legs to ground_z and optional hood cover."""
    a, b = V(p0), V(p1)
    d = b - a
    L = d.length
    u = d.normalized()
    hz = V((u.x, u.y, 0)).normalized()
    side = V((-hz.y, hz.x, 0))
    up = u.cross(side).normalized()                     # perpendicular to the belt, upwards
    if up.z < 0:
        up = -up
    Dh = head_pulley_d or max(0.63, belt_w * 0.6)
    Dt = tail_pulley_d or max(0.5, belt_w * 0.45)
    w2 = belt_w / 2
    th = math.radians(trough_deg)
    roll_l = belt_w * 0.38
    zc = Dh / 2                                         # belt top surface above the pulley-centre line
    st = []
    # stringers (channels) both sides
    for s in (-1, 1):
        o = side * (s * (w2 + 0.25))
        st.append(bar(f'{name}sg{s}', a + o + up * (zc - 0.35), b + o + up * (zc - 0.35), 0.1, 0.3, frame_mat, up=tuple(up)))
    n = int(L / idler_pitch)
    for k in range(1, n):
        c = a + u * (k * idler_pitch) + up * (zc - 0.18)
        imp = k * idler_pitch < impact_len
        # 3-roll trough set: centre roll + two wing rolls
        objs = [rod(f'{name}ic{k}', c - side * roll_l / 2, c + side * roll_l / 2, 0.065, 'paint_grey', 12)]
        for s in (-1, 1):
            e0 = c + side * (s * roll_l / 2)
            e1 = e0 + side * (s * roll_l * math.cos(th)) + up * (roll_l * math.sin(th))
            objs.append(rod(f'{name}iw{k}{s}', e0, e1, 0.065, 'paint_grey', 12))
        objs.append(bar(f'{name}if{k}', c - side * (w2 + 0.25) - up * 0.12, c + side * (w2 + 0.25) - up * 0.12, 0.08, 0.08, frame_mat, up=tuple(up)))
        if imp:
            objs.append(bar(f'{name}ib{k}', c - side * roll_l / 2 + up * 0.07, c + side * roll_l / 2 + up * 0.07, 0.25, 0.04, 'polypropylene', up=tuple(up)))
        st += objs
    nr = int(L / return_pitch)
    for k in range(1, nr):
        c = a + u * (k * return_pitch) - up * (Dt / 2 + 0.05)
        st.append(rod(f'{name}rr{k}', c - side * (w2 + 0.05), c + side * (w2 + 0.05), 0.065, 'paint_grey', 12))
    for nm, c, D_, on in (('hp', b, Dh, ends[1]), ('tp', a, Dt, ends[0])):
        if not on:
            continue
        st.append(rod(f'{name}{nm}', c - side * (w2 + 0.08), c + side * (w2 + 0.08), D_ / 2, 'steel_dark' if nm == 'hp' else 'steel', 28))
        st.append(rod(f'{name}{nm}s', c - side * (w2 + 0.5), c + side * (w2 + 0.5), 0.08, 'steel', 12))
        for s in (-1, 1):
            st.append(placed(box(f'{name}{nm}b{s}', (0.35, 0.25, 0.25), (0, 0, 0), 'paint_grey'), frame(c + side * (s * (w2 + 0.4)), up, tuple(u))))
    # belt: carry (troughed: flat centre + two inclined wings) and return strand
    cen0 = a + up * (zc - 0.18 + 0.075)
    cen1 = b + up * (zc - 0.18 + 0.075)
    bel = [bar(f'{name}bc', cen0, cen1, roll_l + 0.02, 0.018, 'belt', up=tuple(up))]
    for s in (-1, 1):
        mid = side * (s * (roll_l / 2 + roll_l * math.cos(th) / 2)) + up * (roll_l * math.sin(th) / 2)
        wing = bar(f'{name}bw{s}', cen0 + mid, cen1 + mid, roll_l * 1.02, 0.018, 'belt', up=tuple(up))
        # tilt the wing about the belt axis
        R = Matrix.Rotation(-s * th, 4, u)
        cm = (cen0 + cen1) / 2 + mid
        wing.data.transform(Matrix.Translation(cm) @ R @ Matrix.Translation(-cm))
        bel.append(wing)
    bel.append(bar(f'{name}br', a - up * (Dt / 2 - 0.0), b - up * (Dh / 2), belt_w, 0.018, 'belt', up=tuple(up)))
    # walkway + handrail on one side, legs
    if walkway:
        s = 1 if walkway == '+' else -1
        o = side * (s * (w2 + 0.25 + 0.55))
        st.append(bar(f'{name}ww', a + o + up * (zc - 0.45), b + o + up * (zc - 0.45), 0.9, 0.04, 'grating', up=tuple(up)))
        rail = [tuple(a + o + side * (s * 0.45) + up * (zc - 0.45)), tuple(b + o + side * (s * 0.45) + up * (zc - 0.45))]
        st.append(handrail(f'{name}hr', rail, 1.0, post_max=1.8))
    if legs:
        nl = max(1, int(L / 6.0))
        for k in range(nl + 1):
            c = a + u * (L * k / nl)
            z_top = c.z + zc - 0.5
            if z_top - ground_z > 0.6:
                for s in (-1, 1):
                    x = c + side * (s * (w2 + 0.25))
                    st.append(bar(f'{name}lg{k}{s}', (x.x, x.y, ground_z), (x.x, x.y, z_top), 0.15, 0.15, frame_mat))
    if cover:
        n2 = int(L / 1.2)
        for k in range(n2):
            c0 = a + u * (k * 1.2) + up * (zc + 0.1)
            st.append(placed(lathe(f'{name}cv{k}', [(w2 + 0.15, 0.0), (w2 + 0.17, 0.0), (w2 + 0.17, 1.12), (w2 + 0.15, 1.12)], 'galvanised', 16, a0=0, a1=math.pi), frame(c0, u, tuple(up))))
    return join(name + 'S', st), join(name + 'B', bel), (a, u, L, up * (zc - 0.1))


def chute(name, pts_top, pts_bot, mat='paint_grey'):
    """Simple 4-sided transfer chute between two rectangles (lists of 4 corner points, same order)."""
    from .core import mesh_from
    verts = [tuple(p) for p in pts_top] + [tuple(p) for p in pts_bot]
    faces = [[0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
    return mesh_from(name, verts, faces, [mat])
