"""Thermal & Process — heat transfer, boilers, heat recovery, fired equipment and cooling (EQ-228 … EQ-234, EQ-247 … EQ-252)."""
import math
from mathutils import Matrix, Vector
from pumpforge.core import Model, lathe, cyl, box, csg, join, rotate, extrude_poly, TAU, OPERATE_FRAMES
from pumpforge.valvekit import P, keys_loop, smooth_pulse
from pumpforge.parts import hollow_pipe, pressure_gauge, add_tracers
from pumpforge.vesselkit import vessel, nozzle, saddles, legs, skirt, droplets, liquid_v, half, mesh_pad, animate_level
from pumpforge.shapes import sweep_tube
from pumpforge.common_meta import C

CAT = '10 · Thermal & Process Equipment'


def _model(pid, title):
    return Model(pid, title, CAT, META[pid])


# ------------------------------------------------------------------ helpers
def _hduct(name, x0, x1, W, H, CZ, t=0.025, mat='paint_grey', cy=0.0):
    """Rectangular duct along X, open at both ends."""
    return csg(name, [box(name + 'o', (x1 - x0, W + 2 * t, H + 2 * t), ((x0 + x1) / 2, cy, CZ), mat)],
               [box(name + 'i', (x1 - x0 + 0.05, W, H), ((x0 + x1) / 2, cy, CZ), mat)], mat)


def _vduct(name, z0, z1, Wx, Wy, cx=0.0, t=0.025, mat='paint_grey', cy=0.0):
    """Rectangular duct along Z, open at both ends."""
    return csg(name, [box(name + 'o', (Wx + 2 * t, Wy + 2 * t, z1 - z0), (cx, cy, (z0 + z1) / 2), mat)],
               [box(name + 'i', (Wx, Wy, z1 - z0 + 0.05), (cx, cy, (z0 + z1) / 2), mat)], mat)


def _hliq(name, R, x0, x1, CZ, zl, mat='water'):
    """Half (y >= 0) liquid body in a horizontal cylinder of radius R between x0 and x1 up to level zl."""
    b = box(name + 'b', (x1 - x0, R, zl - (CZ - R)), ((x0 + x1) / 2, R / 2, (zl + CZ - R) / 2), mat)
    out = csg(name + 'x', [box(name + 'big', (x1 - x0 + 1, 2 * R + 1, 2 * R + 1), ((x0 + x1) / 2, 0, CZ), mat)], [cyl(name + 'c', R, x0 - 0.6, x1 + 0.6, mat, 64, axis='X', center=(0, 0, CZ))], mat)
    return csg(name, [b], [out], mat)


def _u_bundle(name, xa, xb, CZ, pairs, ys, r=0.011, mat='stainless'):
    """U-tubes: straight legs from the tubesheet (xa) to xb, bend in the XZ plane; pairs = [(z_low, z_high)], repeated at each y."""
    tubes = []
    for i, y in enumerate(ys):
        for j, (za, zb) in enumerate(pairs):
            rb = (zb - za) / 2
            pts = [(xa, y, za), (xb, y, za)] + [(xb + rb * math.sin(math.pi * k / 8), y, za + rb - rb * math.cos(math.pi * k / 8)) for k in range(1, 8)] + [(xb, y, zb), (xa, y, zb)]
            tubes.append(sweep_tube(f'{name}{i}_{j}', pts, r, mat, 8))
    return tubes


def _bands_x(m, segs, W, H, CZ, title, desc, kind='temperature', cy=0.0):
    """Temperature bands wrapped round a duct along X: segs = [(x0, x1, level 0..9)]."""
    objs = [csg(f'tb{i}', [box(f'to{i}', (b - a, W + 0.12, H + 0.12), ((a + b) / 2, cy, CZ), f'pressure_{lev}')], [box(f'ti{i}', (b - a + 0.1, W + 0.07, H + 0.07), ((a + b) / 2, cy, CZ), f'pressure_{lev}')], f'pressure_{lev}')
            for i, (a, b, lev) in enumerate(segs)]
    m.overlay(kind, join(kind, objs), title, desc, split=True)


def _bands_z(m, segs, R, title, desc, kind='temperature', cx=0.0, cy=0.0):
    """Temperature rings round a vertical cylinder: segs = [(z0, z1, level)]."""
    objs = [cyl(f'tz{i}', R + 0.05, a, b, f'pressure_{lev}', 64, center=(cx, cy, 0), r_in=R + 0.025) for i, (a, b, lev) in enumerate(segs)]
    m.overlay(kind, join(kind, objs), title, desc, split=True)


def _flame(m, pid, name, base, direction, L, r, ref, group='combustion', explode=(0, -0.3, 0)):
    """Flickering flame (cone of revolution) from base along direction."""
    f = lathe(pid + 'f', [(0.0, 0.0), (r, 0.12 * L), (r * 0.85, 0.5 * L), (r * 0.4, 0.85 * L), (0.0, L)], 'flame', 32)
    d = Vector(direction).normalized()
    q = Vector((0, 0, 1)).rotation_difference(d)
    f.data.transform(Matrix.Translation(Vector(base)) @ q.to_matrix().to_4x4())
    p = P(m, pid, name, group, f, explode=explode, ref=ref, section='keep', pivot=tuple(base))
    keys_loop(m, p, lambda t: (1 + 0.07 * math.sin(TAU * 7 * t), 1 + 0.07 * math.sin(TAU * 7 * t + 1.3), 1 + 0.1 * math.sin(TAU * 5 * t + 0.4)), 'scale')
    return p


def _vtube_bank(name, xs, ys, z0, z1, r=0.014, mat='steel_dark', hdr_r=0.04, hdr_mat='steel'):
    """Rows of vertical tubes between a bottom and a top header (headers run along Y at each x)."""
    objs = []
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            objs.append(cyl(f'{name}t{i}_{j}', r, z0, z1, mat, 10, center=(x, y, 0)))
        objs.append(cyl(f'{name}hb{i}', hdr_r, min(ys) - 0.06, max(ys) + 0.06, hdr_mat, 16, axis='Y', center=(x, 0, z0)))
        objs.append(cyl(f'{name}ht{i}', hdr_r, min(ys) - 0.06, max(ys) + 0.06, hdr_mat, 16, axis='Y', center=(x, 0, z1)))
    return objs


def _serp(name, x0, x1, z0, z1, n, y, r=0.012, mat='steel_dark'):
    """Serpentine tube in the XZ plane (horizontal runs from x0 to x1, stacked between z0 and z1)."""
    pts = []
    for k in range(n):
        z = z0 + (z1 - z0) * k / (n - 1)
        a, b = (x0, x1) if k % 2 == 0 else (x1, x0)
        pts += [(a, y, z), (b, y, z)]
    return sweep_tube(name, pts, r, mat, 8), pts


def _pump(m, pid, name, x, y, z, ref, explode=(0, -0.3, 0), facing=1):
    """Simple end-suction pump + motor along X (casing at x, motor towards +x*facing) with spinning shaft/coupling."""
    s = facing
    body = join(pid + 'b', [cyl(pid + 'v', 0.12, y - 0.06, y + 0.06, 'paint_blue', 32, axis='Y', center=(x, 0, z)),
                            cyl(pid + 'bf', 0.06, min(x, x + s * 0.18), max(x, x + s * 0.18), 'paint_blue', 24, axis='X', center=(0, y, z)),
                            cyl(pid + 'mt', 0.1, min(x + s * 0.3, x + s * 0.65), max(x + s * 0.3, x + s * 0.65), 'paint_motor', 32, axis='X', center=(0, y, z), ch=0.01),
                            box(pid + 'bp', (0.9, 0.3, 0.05), (x + s * 0.3, y, z - 0.15), 'paint_grey')])
    P(m, pid, name, 'pumps', body, explode=explode, ref=ref, section='keep')
    cp = join(pid + 'c', [cyl(pid + 'sh', 0.02, min(x + s * 0.18, x + s * 0.3), max(x + s * 0.18, x + s * 0.3), 'steel', 12, axis='X', center=(0, y, z)),
                          box(pid + 'cj', (0.04, 0.1, 0.02), (x + s * 0.24, y, z), 'steel')])
    pc = P(m, pid + '_shaft', name + ' — Shaft & Coupling (turning)', 'pumps', cp, explode=explode, ref=ref, section='keep', pivot=(x + s * 0.24, y, z))
    pc.spin('X', 4)


def _fan_rotor(m, pid, name, center, axis, R, ref, revs=4, n=6, mat='aluminium', explode=(0, -0.3, 0.3)):
    hub = cyl(pid + 'h', R * 0.25, -0.03, 0.03, 'steel', 24, axis=axis, center=center if axis == 'Z' else ((0, center[1], center[2]) if axis == 'X' else (center[0], 0, center[2])))
    if axis == 'Z':
        hub = cyl(pid + 'h', R * 0.25, center[2] - 0.03, center[2] + 0.03, 'steel', 24, center=(center[0], center[1], 0))
    elif axis == 'X':
        hub = cyl(pid + 'h', R * 0.25, center[0] - 0.03, center[0] + 0.03, 'steel', 24, axis='X', center=(0, center[1], center[2]))
    else:
        hub = cyl(pid + 'h', R * 0.25, center[1] - 0.03, center[1] + 0.03, 'steel', 24, axis='Y', center=(center[0], 0, center[2]))
    bl = []
    for k in range(n):
        b = box(f'{pid}b{k}', (R * 0.7, R * 0.28, 0.01), (R * 0.6, 0, 0), mat)
        b = rotate(b, 0.35, 'X')
        b = rotate(b, TAU * k / n, 'Z')
        if axis == 'X':
            b = rotate(b, math.pi / 2, 'Y')
        elif axis == 'Y':
            b = rotate(b, -math.pi / 2, 'X')
        b.data.transform(Matrix.Translation(center))
        bl.append(b)
    p = P(m, pid, name, 'rotating_element', [hub] + bl, explode=explode, ref=ref, section='keep', pivot=center)
    p.spin(axis, revs)
    return p


# =============================================================== EQ-228 Reboiler (kettle)
def reboiler(out):
    m = _model('reboiler', 'Kettle Reboiler (U-Tube Bundle, Overflow Weir)')
    R, CZ, XS0, XS1 = 0.55, 0.95, -0.75, 1.15
    zb = CZ - 0.2                                     # bundle centre (low in the kettle)
    shell = csg('ks', [vessel('ksv', R, XS1 - XS0, 0.012, 'paint_grey', axis='X', center=(0, 0, CZ), heads=('flat', '2:1'), z0=XS0),
                       cyl('ksn', 0.33, XS0 - 0.6, XS0 + 0.05, 'paint_grey', 64, axis='X', center=(0, 0, zb), r_in=0.32)],
                [cyl('ksh', 0.32, XS0 - 0.7, XS0 + 0.2, 'paint_grey', 64, axis='X', center=(0, 0, zb))], 'paint_grey')
    P(m, 'shell', 'Kettle Shell (enlarged vapour space) & Bundle Neck', 'casing', shell, explode=(0, 0.6, 0), ref='rb_shell')
    ch = join('ch', [cyl('chs', 0.34, XS0 - 1.05, XS0 - 0.62, 'paint_blue', 64, axis='X', center=(0, 0, zb), r_in=0.32),
                     cyl('chc', 0.36, XS0 - 1.1, XS0 - 1.05, 'paint_blue', 64, axis='X', center=(0, 0, zb)),
                     cyl('ts', 0.36, XS0 - 0.62, XS0 - 0.58, 'steel', 64, axis='X', center=(0, 0, zb)),
                     box('pp', (0.4, 0.62, 0.012), (XS0 - 0.83, 0, zb), 'steel')])
    P(m, 'channel_head', 'Channel Head with Pass Partition & Tubesheet', 'casing', ch, explode=(-0.5, 0, 0), ref='rb_channel')
    tb = _u_bundle('ub', XS0 - 0.58, 0.55, CZ, [(zb - 0.06, zb + 0.06), (zb - 0.14, zb + 0.14), (zb - 0.22, zb + 0.22)], (-0.2, -0.07, 0.07, 0.2), r=0.012)
    tb += [box(f'sp{k}', (0.01, 0.6, 0.6), (x, 0, zb), 'steel') for k, x in enumerate((-0.6, -0.1, 0.35))]
    P(m, 'tube_bundle', 'U-Tube Bundle with Support Plates (heating medium inside)', 'tubes', tb, explode=(0, -0.7, 0.3), ref='rb_bundle', section='keep')
    wr = box('wr', (0.02, 2 * R * 0.92, 0.75), (0.82, 0, CZ - R + 0.375 + 0.05), 'steel')
    P(m, 'weir', 'Overflow Weir (keeps the bundle submerged)', 'internals', csg('wrc', [wr], [csg('wo', [box('wb', (0.3, 3, 3), (0.82, 0, CZ), 'steel')], [cyl('wcy', R - 0.012, 0.5, 1.1, 'steel', 64, axis='X', center=(0, 0, CZ))], 'steel')], 'steel'),
      explode=(0, -0.4, -0.2), ref='rb_weir', section='keep')
    lq = _hliq('lq', R - 0.012, XS0 + 0.01, 0.81, CZ, CZ + 0.27, 'water')
    pl = P(m, 'boiling_liquid', 'Boiling Liquid Pool (bundle submerged)', 'fluid', lq, explode=(0, -0.3, 0), ref='rb_liquid', section='keep')
    animate_level(m, pl, CZ + 0.26, 0.015, lambda t: 0.5 + 0.5 * math.sin(TAU * 3 * t))
    P(m, 'product_liquid', 'Liquid Product beyond the Weir', 'fluid', _hliq('lp', R - 0.012, 0.83, XS1, CZ, CZ - 0.25, 'water'), explode=(0.3, -0.3, 0), ref='rb_liquid', section='keep')
    nz = [nozzle('vo1', (-0.2, 0, CZ + R), (0, 0, 1), 0.09, 0.25), nozzle('vo2', (0.5, 0, CZ + R), (0, 0, 1), 0.09, 0.25),
          nozzle('fi', (-0.2, 0, CZ - R), (0, 0, -1), 0.05, 0.2), nozzle('po', (1.0, 0, CZ - R + 0.05), (0, 0, -1), 0.05, 0.2),
          nozzle('si', (XS0 - 0.85, 0, zb + 0.34), (0, 0, 1), 0.05, 0.18), nozzle('co', (XS0 - 0.85, 0, zb - 0.34), (0, 0, -1), 0.04, 0.15)]
    P(m, 'nozzles', 'Nozzles: Vapour Outlets, Liquid Feed, Product, Steam In, Condensate Out', 'nozzles', nz, explode=(0, 0, 0.4), ref='rb_nozzles', section='keep')
    P(m, 'saddles', 'Saddle Supports', 'structure', saddles('sd', (-0.3, 0.8), R, CZ, 0.0), explode=(0, 0, -0.3), ref='rb_saddles', section='keep')
    droplets(m, 'bubbles', 'Vapour Bubbles rising from the Bundle', -0.6, 0.6, zb + 0.15, CZ + 0.5, n=12, mat='steam', y=0.1, r=0.02)
    m.flow('heating_steam', [(XS0 - 0.85, 0, zb + 0.55), (XS0 - 0.85, 0, zb + 0.12), (0.5, 0.05, zb + 0.14), (0.62, 0.05, zb), (0.5, 0.05, zb - 0.14), (XS0 - 0.85, 0, zb - 0.12), (XS0 - 0.85, 0, zb - 0.5)], 'steam', 0.02, 0.3)
    m.flow('process_feed', [(-0.2, 0, CZ - R - 0.25), (-0.2, 0, CZ - 0.2)], 'flow_suction', 0.02, 0.2)
    m.flow('vapour', [(-0.2, 0.1, CZ + 0.35), (-0.2, 0, CZ + R + 0.3)], 'steam', 0.025, 0.2)
    m.flow('overflow', [(0.6, 0.1, CZ + 0.27), (0.85, 0.1, CZ + 0.3), (1.0, 0.1, CZ - 0.3), (1.0, 0, CZ - R - 0.25)], 'flow_discharge', 0.02, 0.2)
    return m.export(out)


# =============================================================== EQ-229 Preheater (feedwater heater)
def preheater(out):
    m = _model('preheater', 'Shell & U-Tube Preheater (Steam-Heated Feedwater Heater)')
    R, CZ, X0, L = 0.4, 0.85, -0.6, 2.0
    sh = vessel('sh', R, L, 0.01, 'paint_grey', axis='X', center=(0, 0, CZ), heads=('flat', '2:1'), z0=X0)
    P(m, 'shell', 'Shell (steam side)', 'casing', sh, explode=(0, 0.6, 0), ref='ph_shell')
    ch = join('ch', [vessel('chv', R, 0.35, 0.01, 'paint_blue', axis='X', center=(0, 0, CZ), heads=('2:1', 'flat'), z0=X0 - 0.39),
                     cyl('ts', R + 0.03, X0 - 0.04, X0 + 0.0, 'steel', 64, axis='X', center=(0, 0, CZ)), box('pp', (0.35, 2 * R * 0.95, 0.012), (X0 - 0.21, 0, CZ), 'steel')])
    P(m, 'channel', 'Channel (water box) with Pass Partition & Tubesheet', 'casing', ch, explode=(-0.5, 0, 0), ref='ph_channel')
    tb = _u_bundle('ub', X0, X0 + L - 0.15, CZ, [(CZ - 0.07, CZ + 0.07), (CZ - 0.16, CZ + 0.16), (CZ - 0.25, CZ + 0.25)], (-0.18, -0.06, 0.06, 0.18), r=0.01)
    P(m, 'tube_bundle', 'U-Tube Bundle (feedwater inside)', 'tubes', tb, explode=(0, -0.6, 0.3), ref='ph_bundle', section='keep')
    bf = []
    for k, x in enumerate((X0 + 0.35, X0 + 0.75, X0 + 1.15, X0 + 1.55)):
        s = 1 if k % 2 == 0 else -1
        d = csg(f'bf{k}', [cyl(f'bfd{k}', R - 0.012, x - 0.005, x + 0.005, 'steel', 64, axis='X', center=(0, 0, CZ))], [box(f'bfc{k}', (0.1, 1.0, R * 0.55), (x, 0, CZ + s * (R - R * 0.27)), 'steel')], 'steel')
        bf.append(d)
    bf.append(box('imp', (0.3, 0.35, 0.01), (X0 + 0.95, 0, CZ + R - 0.06), 'steel'))
    P(m, 'baffles', 'Segmental Baffles & Steam Impingement Plate', 'internals', bf, explode=(0, -0.4, -0.3), ref='ph_baffles', section='keep')
    pc = P(m, 'condensate', 'Condensate Level (drain-cooling zone)', 'fluid', _hliq('cd', R - 0.011, X0 + 0.01, X0 + L, CZ, CZ - R + 0.12, 'water'), explode=(0, -0.3, -0.1), ref='ph_condensate', section='keep')
    animate_level(m, pc, CZ - R + 0.11, 0.02, lambda t: 0.5 + 0.5 * math.sin(TAU * t))
    nz = [nozzle('si', (X0 + 0.95, 0, CZ + R), (0, 0, 1), 0.08, 0.22), nozzle('cdo', (X0 + 1.6, 0, CZ - R), (0, 0, -1), 0.04, 0.2),
          nozzle('fwi', (X0 - 0.2, 0, CZ - R), (0, 0, -1), 0.06, 0.2), nozzle('fwo', (X0 - 0.2, 0, CZ + R), (0, 0, 1), 0.06, 0.2),
          nozzle('vt', (X0 + 1.8, 0, CZ + R), (0, 0, 1), 0.02, 0.12)]
    P(m, 'nozzles', 'Nozzles: Steam In, Condensate Drain, Feedwater In/Out, Vent', 'nozzles', nz, explode=(0, 0, 0.4), ref='ph_nozzles', section='keep')
    P(m, 'saddles', 'Saddle Supports', 'structure', saddles('sd', (X0 + 0.4, X0 + 1.6), R, CZ, 0.0), explode=(0, 0, -0.3), ref='ph_saddles', section='keep')
    droplets(m, 'drips', 'Condensate Dripping off the Tubes', X0 + 0.2, X0 + 1.7, CZ + 0.2, CZ - R + 0.12, n=10, mat='water', y=0.1, r=0.012)
    m.flow('feedwater', [(X0 - 0.2, 0, CZ - R - 0.2), (X0 - 0.2, 0, CZ - 0.15), (X0 + L - 0.2, 0.06, CZ - 0.16), (X0 + L - 0.05, 0.06, CZ), (X0 + L - 0.2, 0.06, CZ + 0.16), (X0 - 0.2, 0, CZ + 0.15), (X0 - 0.2, 0, CZ + R + 0.2)], 'water', 0.02, 0.3)
    m.flow('steam', [(X0 + 0.95, 0, CZ + R + 0.22), (X0 + 0.95, 0, CZ + R - 0.08), (X0 + 1.2, 0.1, CZ + 0.3)], 'steam', 0.025, 0.2)
    m.flow('condensate_drain', [(X0 + 1.3, 0.1, CZ - R + 0.08), (X0 + 1.6, 0, CZ - R + 0.05), (X0 + 1.6, 0, CZ - R - 0.2)], 'flow_discharge', 0.015, 0.2)
    _bands_x(m, [(X0 - 0.3, X0 + 0.3, 2), (X0 + 0.3, X0 + 0.9, 4), (X0 + 0.9, X0 + 1.5, 6), (X0 + 1.5, X0 + L, 7)], 2 * R, 2 * R, CZ,
             'Temperature: water heats along the bundle', 'Feedwater (cool, blue) gains heat as it passes the tubes; condensing steam on the shell side stays near its saturation '
             'temperature, which is why the temperature difference is largest at the cold end. Condensate is sub-cooled in the drain-cooling zone at the bottom.')
    return m.export(out)


# =============================================================== EQ-230 Economizer
def economizer(out):
    m = _model('economizer', 'Boiler Economizer (Serpentine Tube Bank in the Flue-Gas Duct)')
    Z0, Z1, Wx, Wy = 0.5, 2.3, 1.3, 0.9
    dc = _vduct('dc', Z0, Z1, Wx, Wy)
    P(m, 'casing', 'Gas Duct Casing (gas flows downward)', 'casing', dc, explode=(0, 0.7, 0), ref='ec_casing')
    tubes, pth = [], None
    for j, y in enumerate((-0.3, -0.1, 0.1, 0.3)):
        t_, pts = _serp(f'sp{j}', -0.55, 0.55, Z0 + 0.25, Z1 - 0.25, 10, y, r=0.022)
        tubes.append(t_)
        if j == 2:
            pth = pts
        for k in range(0, 10, 2):                               # stub fins on each tube run (visual)
            z = Z0 + 0.25 + (Z1 - Z0 - 0.5) * k / 9
            tubes += [cyl(f'fn{j}{k}{q}', 0.04, x - 0.003, x + 0.003, 'steel', 16, axis='X', center=(0, y, z)) for q, x in enumerate((-0.4, -0.2, 0.0, 0.2, 0.4))]
    P(m, 'tube_bank', 'Finned Serpentine Tube Bank (water inside)', 'tubes', tubes, explode=(0, -0.8, 0), ref='ec_tubes', section='keep')
    hd = [cyl('hi', 0.06, -0.55, 0.55, 'steel', 24, axis='Y', center=(-0.75, 0, Z0 + 0.25)), cyl('ho', 0.06, -0.55, 0.55, 'steel', 24, axis='Y', center=(-0.75, 0, Z1 - 0.25))]
    hd += [cyl(f'hs{k}{y}', 0.02, -0.75, -0.55, 'steel', 12, axis='X', center=(0, y, z)) for k, z in enumerate((Z0 + 0.25, Z1 - 0.25)) for y in (-0.3, -0.1, 0.1, 0.3)]
    hd += [nozzle('fwi', (-0.75, -0.55, Z0 + 0.25), (0, -1, 0), 0.05, 0.25), nozzle('fwo', (-0.75, -0.55, Z1 - 0.25), (0, -1, 0), 0.05, 0.25)]
    P(m, 'headers', 'Inlet (bottom) & Outlet (top) Headers', 'headers', hd, explode=(-0.5, 0, 0), ref='ec_headers', section='keep')
    sb = join('sb', [cyl('sbl', 0.015, -0.7, 0.7, 'steel', 12, axis='Y', center=(0.0, 0, (Z0 + Z1) / 2)), cyl('sbm', 0.05, 0.75, 0.95, 'paint_motor', 16, axis='Y', center=(0.0, 0, (Z0 + Z1) / 2))] +
             [cyl(f'sbn{k}', 0.008, -0.04, 0.04, 'steel', 8, axis='X', center=(0, y, (Z0 + Z1) / 2)) for k, y in enumerate((-0.4, -0.2, 0.0, 0.2, 0.4))])
    psb = P(m, 'soot_blower', 'Rotary Soot Blower (steam/air jets clean the fins)', 'cleaning', sb, explode=(0, 0.5, 0.2), ref='ec_sootblower', section='keep', pivot=(0, 0, (Z0 + Z1) / 2))
    keys_loop(m, psb, lambda t: (0, TAU * t, 0), 'rotation_euler')
    hp = join('hp', [lathe('hpp', [(0.0, Z0 - 0.45), (0.35, Z0 - 0.45), (0.75, Z0 - 0.02), (0.0, Z0 - 0.02)], 'paint_grey', 4, a0=math.pi / 4, a1=math.pi / 4 + TAU)] +
             [box(f'lg{k}', (0.06, 0.06, Z0), (sx * 0.62, sy * 0.42, Z0 / 2), 'paint_grey') for k, (sx, sy) in enumerate(((-1, -1), (-1, 1), (1, -1), (1, 1)))])
    P(m, 'ash_hopper', 'Ash Hopper & Support Steel', 'structure', hp, explode=(0, 0, -0.4), ref='ec_casing', section='keep')
    add_tracers(m, 'water_tracers', 'Feedwater rising through the Serpentine', [(-0.75, 0.1, Z0 + 0.25)] + pth, n=14, radius=0.018, mat='water')
    droplets(m, 'gas_particles', 'Flue Gas Flowing Down through the Bank', -0.5, 0.5, Z1 + 0.2, Z0 - 0.1, n=10, mat='flue_gas', y=0.4, r=0.02)
    m.flow('flue_gas', [(0.0, 0.42, Z1 + 0.4), (0.0, 0.42, Z0 - 0.3)], 'flue_gas', 0.04, 0.4)
    m.flow('water', [(-0.75, -0.8, Z0 + 0.25), (-0.75, 0.1, Z0 + 0.25)] + pth + [(-0.75, 0.1, Z1 - 0.25), (-0.75, -0.8, Z1 - 0.25)], 'water', 0.015, 0.4)
    _bands_z(m, [(Z1 - 0.6, Z1, 6), (Z0 + 0.6, Z1 - 0.6, 5), (Z0, Z0 + 0.6, 3)], 0.85, 'Gas cools as it gives heat to the water',
             'Flue gas enters at the top hot (orange) and leaves the bottom cooler (blue-green), while feedwater flows upward — counter-flow. Gas outlet temperature must stay above '
             'the acid dew point when the fuel contains sulphur, to avoid cold-end corrosion; water must stay below saturation to avoid steaming in the economizer.')
    return m.export(out)


# =============================================================== EQ-231 Superheater
def superheater(out):
    m = _model('superheater', 'Pendant Superheater (Primary + Secondary with Spray Attemperator)')
    CZ, H, W = 1.4, 1.5, 1.0
    dc = _hduct('dc', -1.6, 1.6, W, H, CZ)
    P(m, 'gas_pass', 'Horizontal Gas Pass (boiler back-pass casing)', 'casing', dc, explode=(0, 0.7, 0), ref='sh_casing')
    loops, paths = [], {}
    ys = (-0.35, -0.12, 0.12, 0.35)
    for st, (xa, xb) in (('pri', (-0.95, -0.55)), ('sec', (0.35, 0.75))):
        objs = []
        for j, y in enumerate(ys):
            pts = [(xa, y, CZ + H / 2 + 0.25), (xa, y, CZ - H / 2 + 0.25)] + [((xa + xb) / 2 - (xb - xa) / 2 * math.cos(math.pi * k / 8), y, CZ - H / 2 + 0.25 - (xb - xa) / 2 * math.sin(math.pi * k / 8)) for k in range(1, 8)] + [(xb, y, CZ - H / 2 + 0.25), (xb, y, CZ + H / 2 + 0.25)]
            objs.append(sweep_tube(f'{st}l{j}', pts, 0.022, 'steel_dark' if st == 'pri' else 'steel', 8))
            if j == 2:
                paths[st] = pts
        objs += [cyl(st + 'hi', 0.06, -0.55, 0.55, 'steel', 24, axis='Y', center=(xa, 0, CZ + H / 2 + 0.25)), cyl(st + 'ho', 0.06, -0.55, 0.55, 'steel', 24, axis='Y', center=(xb, 0, CZ + H / 2 + 0.25))]
        P(m, f'{st}mary_stage' if st == 'pri' else 'secondary_stage', ('Primary (low-temperature) Superheater Platens & Headers' if st == 'pri' else 'Secondary (final) Superheater Platens & Headers'),
          'tubes', objs, explode=(0, -0.7, 0.4 if st == 'pri' else 0.6), ref='sh_tubes', section='keep')
    lk = hollow_pipe('lk', [(-0.55, -0.55, CZ + H / 2 + 0.25), (-0.55, -0.7, CZ + H / 2 + 0.25), (-0.55, -0.7, CZ + H / 2 + 0.55), (0.35, -0.7, CZ + H / 2 + 0.55), (0.35, -0.7, CZ + H / 2 + 0.25), (0.35, -0.55, CZ + H / 2 + 0.25)], 0.05, 'steel', 24, bend=0.08)
    att = join('att', [cyl('atb', 0.08, -0.2, 0.05, 'steel', 32, axis='X', center=(0, -0.7, CZ + H / 2 + 0.55)), cyl('atn', 0.02, CZ + H / 2 + 0.6, CZ + H / 2 + 0.85, 'stainless', 12, center=(-0.1, -0.7, 0)),
                       box('atv', (0.1, 0.08, 0.1), (-0.1, -0.7, CZ + H / 2 + 0.92), 'paint_blue')])
    P(m, 'link_attemperator', 'Link Pipe with Spray Attemperator (controls final steam temperature)', 'control', [lk, att], explode=(0, -0.4, 0.5), ref='sh_attemperator', section='keep')
    nz = [nozzle('si', (-0.95, -0.55, CZ + H / 2 + 0.25), (0, -1, 0), 0.05, 0.25), nozzle('so', (0.75, -0.55, CZ + H / 2 + 0.25), (0, -1, 0), 0.05, 0.25)]
    P(m, 'nozzles', 'Saturated Steam Inlet (from drum) & Main Steam Outlet', 'nozzles', nz, explode=(0, -0.3, 0.3), ref='sh_tubes', section='keep')
    sup = [box(f'hg{k}', (0.06, W + 0.3, 0.06), (x, 0, CZ + H / 2 + 0.45), 'paint_grey') for k, x in enumerate((-0.75, 0.55))] + [box(f'cl{k}{s}', (0.08, 0.08, CZ + H / 2 + 0.45), (sx, s * (W / 2 + 0.2), (CZ + H / 2 + 0.45) / 2), 'paint_grey') for k, sx in enumerate((-1.4, 1.4)) for s in (-1, 1)]
    P(m, 'support_steel', 'Hanger Supports (pendants hang and expand downward)', 'structure', sup, explode=(0, 0, 0.6), ref='sh_casing', section='keep')
    add_tracers(m, 'steam_tracers', 'Steam Flowing through the Platens', paths['pri'] + [(-0.55, -0.7, CZ + H / 2 + 0.55), (0.35, -0.7, CZ + H / 2 + 0.55)] + paths['sec'], n=16, radius=0.02, mat='steam')
    add_tracers(m, 'gas_particles', 'Hot Flue Gas Crossing the Platens', [(-1.6, 0.45, CZ + 0.2), (1.6, 0.45, CZ + 0.2)], n=8, radius=0.03, mat='flue_gas')
    m.flow('flue_gas', [(-1.8, 0.0, CZ), (1.8, 0.0, CZ)], 'flue_gas', 0.05, 0.5)
    m.flow('steam', [(-0.95, -0.8, CZ + H / 2 + 0.25)] + [(p[0], 0.12, p[2]) for p in paths['pri']] + [(-0.55, -0.7, CZ + H / 2 + 0.55), (0.35, -0.7, CZ + H / 2 + 0.55)] + [(p[0], 0.12, p[2]) for p in paths['sec']] + [(0.75, -0.8, CZ + H / 2 + 0.25)], 'steam', 0.015, 0.4)
    m.flow('spray_water', [(-0.1, -0.7, CZ + H / 2 + 1.0), (-0.1, -0.7, CZ + H / 2 + 0.6)], 'water', 0.012, 0.15)
    _bands_x(m, [(-1.6, -0.3, 9), (-0.3, 0.2, 8), (0.2, 1.6, 7)], W, H, CZ, 'Gas temperature falls across the pass',
             'Flue gas enters at very high temperature and gives heat first to the secondary and then the primary stage. The final steam temperature is held at its set-point by '
             'spraying feedwater in the attemperator between the stages; tube metal temperature (not gas temperature) limits the materials used (alloy steels such as T22/T91).')
    return m.export(out)


# =============================================================== EQ-232 Air preheater (rotary regenerative)
def air_preheater(out):
    m = _model('air_preheater', 'Rotary Regenerative Air Preheater (Ljungström Type)')
    R, Z0, Z1 = 0.85, 0.9, 1.7
    hs = csg('hs', [cyl('ho', R + 0.08, Z0 - 0.15, Z1 + 0.15, 'paint_grey', 64)], [cyl('hi', R + 0.04, Z0 - 0.2, Z1 + 0.2, 'paint_grey', 64)], 'paint_grey')
    P(m, 'housing', 'Housing (rotor shell)', 'casing', hs, explode=(0, 0.8, 0), ref='ap_housing')
    rot = [cyl('rs', 0.12, Z0 - 0.25, Z1 + 0.25, 'steel', 32), cyl('rsh', R, Z0, Z1, 'steel', 96, r_in=R - 0.02)]
    rot += [rotate(box(f'dp{k}', (R - 0.12, 0.012, Z1 - Z0), ((R + 0.12) / 2, 0, (Z0 + Z1) / 2), 'steel'), TAU * k / 12, 'Z') for k in range(12)]
    rot += [cyl(f'bk{k}', r, Z0 + 0.02, Z1 - 0.02, 'steel_dark', 96, r_in=r - 0.008) for k, r in enumerate((0.3, 0.45, 0.6, 0.75))]
    rot += [cyl('pr', R + 0.03, Z0 + 0.1, Z0 + 0.14, 'steel_dark', 96, r_in=R)]
    pr = P(m, 'rotor', 'Rotor with Heating-Element Baskets (matrix) — turns slowly through gas and air', 'rotating_element', rot, explode=(0, -0.9, 0), ref='ap_rotor', section='split')
    pr.spin('Z', -0.25)
    sp = [box(f'sp{s}', (0.12, 2 * R, 0.03), (0, 0, z), 'steel') for s, z in enumerate((Z1 + 0.04, Z0 - 0.04))]
    sp += [cyl('rsl', R + 0.035, Z1 + 0.02, Z1 + 0.05, 'rubber', 96, r_in=R + 0.005)]
    P(m, 'sector_plates_seals', 'Sector Plates & Radial/Circumferential Seals (limit air-to-gas leakage)', 'seals', sp, explode=(0, -0.3, 0.5), ref='ap_seals', section='keep')
    ducts = [_vduct('gin', Z1 + 0.15, Z1 + 0.9, 0.7, 1.4, cx=0.5, mat='paint_grey'), _vduct('gout', Z0 - 0.8, Z0 - 0.15, 0.7, 1.4, cx=0.5, mat='paint_grey'),
             _vduct('ain', Z0 - 0.8, Z0 - 0.15, 0.7, 1.4, cx=-0.5, mat='paint_blue'), _vduct('aout', Z1 + 0.15, Z1 + 0.9, 0.7, 1.4, cx=-0.5, mat='paint_blue')]
    P(m, 'ducts', 'Ducts: Flue Gas In (top) / Out (bottom), Air In (bottom) / Out (top)', 'ducts', ducts, explode=(0, 0, 0.6), ref='ap_ducts')
    drv = join('drv', [cyl('dm', 0.1, R + 0.15, R + 0.45, 'paint_motor', 24, axis='X', center=(0, 0, (Z0 + Z1) / 2)), box('dg', (0.2, 0.25, 0.25), (R + 0.2, 0, (Z0 + Z1) / 2), 'paint_blue'),
                       cyl('dp', 0.06, (Z0 + Z1) / 2 - 0.08, (Z0 + Z1) / 2 + 0.08, 'steel', 16, center=(R + 0.1, 0, 0))])
    P(m, 'drive', 'Rotor Drive (motor, reducer, pinion on pin rack)', 'drive', drv, explode=(0.5, 0, 0), ref='ap_drive', section='keep')
    P(m, 'structure', 'Support Structure', 'structure', legs('lg', R + 0.08, 0.0, Z0 - 0.8, n=4), explode=(0, 0, -0.3), ref='ap_housing', section='keep')
    droplets(m, 'gas_particles', 'Hot Flue Gas passing Down through the Matrix', 0.2, 0.8, Z1 + 0.85, Z0 - 0.75, n=8, mat='flue_gas', y=0.3, r=0.025)
    droplets(m, 'air_particles', 'Combustion Air passing Up through the Matrix', -0.8, -0.2, Z0 - 0.75, Z1 + 0.85, n=8, mat='air', y=0.3, r=0.025)
    m.flow('flue_gas', [(0.5, 0.3, Z1 + 1.0), (0.5, 0.3, Z0 - 0.9)], 'flue_gas', 0.04, 0.35)
    m.flow('air', [(-0.5, 0.3, Z0 - 0.9), (-0.5, 0.3, Z1 + 1.0)], 'air', 0.04, 0.35)
    hot = lathe('hz', [(0.15, Z1 + 0.06), (R, Z1 + 0.06), (R, Z1 + 0.08), (0.15, Z1 + 0.08)], 'pressure_8', 48, a0=-math.pi / 2, a1=math.pi / 2, cap_mat='pressure_8')
    cold = lathe('cz', [(0.15, Z1 + 0.06), (R, Z1 + 0.06), (R, Z1 + 0.08), (0.15, Z1 + 0.08)], 'pressure_2', 48, a0=math.pi / 2, a1=1.5 * math.pi, cap_mat='pressure_2')
    m.overlay('temperature', join('tz', [hot, cold]), 'Hot side vs cold side of the rotor',
              'The matrix plates in the gas half (right) are heated by the flue gas; as the rotor turns (about 1–3 rpm) they move into the air half (left) and give that heat to the '
              'combustion air. Hotter combustion air improves boiler efficiency (roughly 1 % fuel saving per ~20 °C of extra air temperature, rule of thumb). Leakage of air into gas '
              'past the seals is the main performance loss.')
    return m.export(out)


# =============================================================== EQ-233 Steam generator (3-pass fire-tube)
def steam_generator(out):
    m = _model('steam_generator', 'Packaged Steam Generator (3-Pass Dry-Back Fire-Tube Boiler)')
    R, CZ, X0, L = 0.75, 1.05, -1.2, 2.6
    sh = vessel('sh', R, L, 0.014, 'paint_red', axis='X', center=(0, 0, CZ), heads=('flat', 'flat'), z0=X0)
    P(m, 'shell', 'Pressure Shell & End Plates (water/steam side)', 'casing', sh, explode=(0, 0.8, 0), ref='sg_shell')
    fz = CZ - 0.25
    fur = cyl('fu', 0.3, X0, X0 + L + 0.1, 'steel', 64, axis='X', center=(0, 0, fz), r_in=0.285)
    fur = join('fuj', [fur] + [cyl(f'cg{k}', 0.315, x - 0.02, x + 0.02, 'steel', 64, axis='X', center=(0, 0, fz), r_in=0.29) for k, x in enumerate((X0 + 0.5, X0 + 1.0, X0 + 1.5, X0 + 2.0))])
    P(m, 'furnace', 'Furnace Tube (1st pass, corrugated)', 'tubes', fur, explode=(0, -0.9, 0), ref='sg_furnace', section='split')
    rc = csg('rc', [box('rco', (0.45, 1.3, 0.72), (X0 + L + 0.225, 0, CZ - 0.26), 'refractory')], [box('rci', (0.37, 1.2, 0.62), (X0 + L + 0.17, 0, CZ - 0.26), 'refractory')], 'refractory')
    P(m, 'reversal_chamber', 'Rear Reversal Chamber (refractory-lined door: turns gas from furnace into 2nd pass)', 'casing', rc, explode=(0.5, 0, 0), ref='sg_reversal')
    tubes = []
    for k, (y, z) in enumerate([(y, CZ + 0.02) for y in (-0.55, -0.42, 0.42, 0.55)] + [(y, CZ - 0.12) for y in (-0.55, -0.42, 0.42, 0.55)]):
        tubes.append(cyl(f'p2{k}', 0.035, X0, X0 + L + 0.05, 'steel_dark', 16, axis='X', center=(0, y, z), r_in=0.03))
    for k, y in enumerate((-0.36, -0.22, -0.08, 0.08, 0.22, 0.36)):
        tubes.append(cyl(f'p3{k}', 0.035, X0, X0 + L + 0.05, 'steel', 16, axis='X', center=(0, y, CZ + 0.22), r_in=0.03))
    P(m, 'smoke_tubes', 'Smoke Tubes: 2nd Pass (lower) & 3rd Pass (upper)', 'tubes', tubes, explode=(0, -0.6, 0.4), ref='sg_tubes', section='keep')
    fb = csg('fb', [box('fbo', (0.3, 1.3, 0.85), (X0 - 0.2, 0, CZ + 0.05), 'paint_grey')], [box('fbi', (0.24, 1.24, 0.79), (X0 - 0.2, 0, CZ + 0.05), 'paint_grey'), cyl('fbh', 0.3, X0 - 0.5, X0, 'paint_grey', 48, axis='X', center=(0, 0, fz))], 'paint_grey')
    stk = cyl('stk', 0.16, CZ + 0.72, CZ + R + 1.1, 'paint_grey', 48, center=(X0 + L + 0.3, 0, 0), r_in=0.15)
    stb = csg('stb', [box('sbo', (0.45, 1.2, 0.6), (X0 + L + 0.225, 0, CZ + 0.42), 'paint_grey')], [box('sbi', (0.37, 1.12, 0.52), (X0 + L + 0.17, 0, CZ + 0.42), 'paint_grey'), cyl('sbh', 0.15, CZ + 0.5, CZ + 0.8, 'paint_grey', 32, center=(X0 + L + 0.3, 0, 0))], 'paint_grey')
    P(m, 'smoke_boxes_stack', 'Front Smoke Box (2nd→3rd pass turn), Rear Smoke Box & Stack', 'casing', [fb, stb, stk], explode=(0, 0, 0.6), ref='sg_smokebox')
    bn = join('bn', [cyl('bnb', 0.22, X0 - 0.75, X0 - 0.35, 'paint_blue', 48, axis='X', center=(0, 0, fz)), cyl('bnf', 0.18, X0 - 1.1, X0 - 0.75, 'paint_motor', 48, axis='X', center=(0, 0, fz)),
                     cyl('bnt', 0.08, X0 - 0.35, X0 + 0.05, 'steel', 32, axis='X', center=(0, 0, fz))])
    P(m, 'burner', 'Forced-Draught Burner (fan, air register, gas train)', 'combustion', bn, explode=(-0.6, 0, 0), ref='sg_burner', section='keep')
    _flame(m, 'flame', 'Flame in the Furnace', (X0 + 0.08, 0, fz), (1, 0, 0), 1.4, 0.2, 'sg_burner')
    lq = _hliq('wt', R - 0.014, X0 + 0.02, X0 + L - 0.02, CZ, CZ + 0.42, 'water')
    pw = P(m, 'water', 'Boiler Water (level above the top tubes)', 'fluid', lq, explode=(0, -0.3, 0), ref='sg_water', section='keep')
    animate_level(m, pw, CZ + 0.41, 0.03, lambda t: 0.5 + 0.5 * math.sin(TAU * t))
    fit = [nozzle('ms', (0.4, 0, CZ + R), (0, 0, 1), 0.07, 0.25), cyl('sv1', 0.04, CZ + R, CZ + R + 0.3, 'brass', 16, center=(0.9, 0, 0)), cyl('sv2', 0.04, CZ + R, CZ + R + 0.3, 'brass', 16, center=(1.05, 0, 0)),
           box('lgc', (0.08, 0.06, 0.45), (X0 - 0.05, -0.68, CZ + 0.4), 'paint_grey'), box('lgg', (0.02, 0.01, 0.35), (X0 - 0.05, -0.715, CZ + 0.4), 'glass'),
           nozzle('fw', (-0.2, -R, CZ + 0.2), (0, -1, 0), 0.04, 0.2), nozzle('bd', (0.6, 0, CZ - R), (0, 0, -1), 0.03, 0.2), pressure_gauge('pg', (0.2, 0, CZ + R + 0.35), r=0.05, facing=(0, -1, 0))]
    P(m, 'fittings', 'Main Steam Valve, Safety Valves, Level Gauge, Feed Check, Blowdown, Pressure Gauge', 'fittings', fit, explode=(0, -0.5, 0.4), ref='sg_fittings', section='keep')
    sk = [box(f'sk{s}', (L + 0.6, 0.12, 0.12), (X0 + L / 2, s * 0.5, 0.06), 'paint_grey') for s in (-1, 1)] + [box(f'cr{k}', (0.12, 1.1, CZ - R - 0.1), (x, 0, (CZ - R - 0.1) / 2 + 0.1), 'paint_grey') for k, x in enumerate((X0 + 0.3, X0 + L - 0.3))]
    P(m, 'skid', 'Base Skid & Cradles', 'structure', sk, explode=(0, 0, -0.3), ref='sg_shell', section='keep')
    droplets(m, 'bubbles', 'Steam Bubbles from the Heating Surfaces', X0 + 0.3, X0 + L - 0.3, CZ - 0.1, CZ + 0.45, n=12, mat='steam', y=0.25, r=0.02)
    g = [(X0 + 0.1, 0.05, fz), (X0 + L + 0.2, 0.05, fz), (X0 + L + 0.3, 0.45, CZ - 0.05), (X0, 0.48, CZ - 0.05), (X0 - 0.2, 0.3, CZ + 0.1), (X0, 0.22, CZ + 0.22), (X0 + L + 0.3, 0.2, CZ + 0.3), (X0 + L + 0.3, 0, CZ + R + 1.2)]
    m.flow('flue_gas', g, 'flue_gas', 0.03, 0.4)
    m.flow('steam', [(0.4, 0, CZ + 0.5), (0.4, 0, CZ + R + 0.3)], 'steam', 0.03, 0.2)
    m.flow('feedwater', [(-0.2, -R - 0.25, CZ + 0.2), (-0.2, -R + 0.05, CZ + 0.2)], 'water', 0.015, 0.15)
    return m.export(out)


# =============================================================== EQ-234 Waste heat recovery boiler (HRSG)
def waste_heat_recovery_boiler(out):
    m = _model('waste_heat_recovery_boiler', 'Waste Heat Recovery Boiler (Horizontal HRSG, Single Pressure)')
    CZ, H, W = 1.3, 1.6, 1.1
    dc = join('dc', [_hduct('dcm', -1.5, 1.6, W, H, CZ), csg('tr', [box('tro', (0.8, 0.65, 0.65), (-1.9, 0, CZ), 'paint_grey')], [box('tri', (0.9, 0.6, 0.6), (-1.9, 0, CZ), 'paint_grey')], 'paint_grey')])
    P(m, 'casing', 'Insulated Gas Casing & Inlet Transition (from turbine/kiln exhaust)', 'casing', dc, explode=(0, 0.8, 0), ref='hr_casing')
    ys = (-0.4, -0.2, 0.0, 0.2, 0.4)
    z0, z1 = CZ - H / 2 + 0.1, CZ + H / 2 - 0.1
    banks = {'superheater': ((-1.1, -0.95), 'steel', 'Superheater (hottest gas)'), 'evaporator': ((-0.35, -0.2, -0.05, 0.1), 'steel_dark', 'Evaporator (boiling tubes)'), 'economizer': ((0.8, 0.95, 1.1), 'steel_dark', 'Economizer (coolest gas)')}
    for k, (xs, mt, nm) in banks.items():
        P(m, k, nm + ' Tube Bank & Headers', 'tubes', _vtube_bank(k[:3], xs, ys, z0, z1, mat=mt), explode=(0, -0.8, 0.3 + 0.2 * list(banks).index(k)), ref='hr_coils', section='keep')
    DZ = CZ + H / 2 + 0.6
    dr = vessel('drum', 0.3, 1.4, 0.012, 'paint_red', axis='X', center=(0, 0, DZ), heads=('hemi', 'hemi'), z0=-0.7)
    P(m, 'steam_drum', 'Steam Drum (separates steam from water)', 'vessel', dr, explode=(0, 0, 0.7), ref='hr_drum')
    pdw = P(m, 'drum_water', 'Drum Water Level', 'fluid', _hliq('dw', 0.288, -0.7, 0.7, DZ, DZ - 0.02, 'water'), explode=(0, -0.3, 0.7), ref='hr_drum', section='keep')
    animate_level(m, pdw, DZ - 0.03, 0.02, lambda t: 0.5 + 0.5 * math.sin(TAU * t))
    pip = [hollow_pipe('dcm', [(-0.6, 0.62, DZ - 0.1), (-0.6, 0.62, z0), (-0.35, 0.62, z0), (-0.35, 0.47, z0)], 0.05, 'steel', 24, bend=0.08),
           hollow_pipe('rsr', [(0.1, 0.47, z1), (0.1, 0.62, z1), (0.1, 0.62, DZ - 0.2), (0.1, 0.25, DZ - 0.2)], 0.05, 'steel', 24, bend=0.08),
           hollow_pipe('ssh', [(0.0, 0.0, DZ + 0.3), (0.0, 0.0, DZ + 0.5), (-1.1, 0.0, DZ + 0.5), (-1.1, 0.0, z1 + 0.04)], 0.04, 'steel', 24, bend=0.08),
           hollow_pipe('eco', [(0.8, -0.47, z1), (0.8, -0.62, z1), (0.8, -0.62, DZ), (0.7, -0.62, DZ), (0.7, -0.2, DZ)], 0.04, 'steel', 24, bend=0.06)]
    P(m, 'circulation_piping', 'Downcomer, Risers, Saturated-Steam & Economizer Links', 'piping', pip, explode=(0, 0.5, 0.4), ref='hr_piping', section='keep')
    stk = join('stk', [cyl('st', 0.35, CZ - 0.2, CZ + H + 1.6, 'paint_grey', 48, center=(2.0, 0, 0), r_in=0.33), csg('stt', [box('sto', (0.5, W + 0.05, H + 0.05), (1.8, 0, CZ), 'paint_grey')], [box('sti', (0.6, W - 0.05, H - 0.05), (1.75, 0, CZ), 'paint_grey'), cyl('sth', 0.33, CZ, CZ + H, 'paint_grey', 48, center=(2.0, 0, 0))], 'paint_grey')])
    P(m, 'stack', 'Outlet Transition & Stack', 'casing', stk, explode=(0.6, 0, 0), ref='hr_casing')
    add_tracers(m, 'gas_particles', 'Exhaust Gas crossing the Banks', [(-2.3, 0.48, CZ + 0.3), (1.8, 0.48, CZ + 0.3), (2.0, 0.2, CZ + 0.6), (2.0, 0.2, CZ + H + 1.6)], n=12, radius=0.03, mat='exhaust')
    add_tracers(m, 'circulation', 'Natural Circulation: Drum → Downcomer → Evaporator → Risers → Drum', [(-0.6, 0.62, DZ - 0.1), (-0.6, 0.62, z0), (-0.2, 0.0, z0), (-0.2, 0.0, z1), (0.1, 0.62, z1), (0.1, 0.62, DZ - 0.2), (-0.6, 0.62, DZ - 0.1)], n=12, radius=0.022, mat='water')
    m.flow('exhaust_gas', [(-2.4, 0, CZ), (1.8, 0, CZ), (2.0, 0, CZ + 0.4), (2.0, 0, CZ + H + 1.8)], 'exhaust', 0.05, 0.5)
    m.flow('water_steam', [(0.8, -0.8, z0), (0.8, -0.47, z0), (0.8, -0.47, z1), (0.8, -0.62, DZ), (0.7, -0.2, DZ), (0.0, 0.0, DZ + 0.5), (-1.1, 0.0, DZ + 0.5), (-1.1, 0.3, z1), (-1.1, 0.3, z0), (-1.1, -0.8, z0)], 'steam', 0.015, 0.4)
    _bands_x(m, [(-1.5, -0.6, 9), (-0.6, 0.45, 7), (0.45, 1.6, 4)], W, H, CZ, 'Gas temperature profile through the HRSG',
             'Exhaust gas gives up heat to the superheater, then the evaporator, then the economizer. The smallest gas-to-water temperature difference — the pinch point at the evaporator '
             'outlet — and the approach temperature at the economizer outlet set how much heat can be recovered (typical design pinch ~ 8–15 °C).')
    return m.export(out)


# =============================================================== EQ-249 Heat recovery system (run-around coil)
def heat_recovery_system(out):
    m = _model('heat_recovery_system', 'Run-Around Coil Heat Recovery System (Exhaust → Supply Air)')
    ZE, ZS, W, H = 2.0, 0.8, 0.8, 0.6
    ducts = [_hduct('de', -1.8, 1.8, W, H, ZE), _hduct('ds', -1.8, 1.8, W, H, ZS, mat='paint_blue')]
    P(m, 'ducts', 'Exhaust Air Duct (top) & Supply Air Duct (bottom)', 'ducts', ducts, explode=(0, 0.6, 0), ref='hx_ducts')
    for k, (z, nm) in enumerate(((ZE, 'exhaust_coil'), (ZS, 'supply_coil'))):
        cl = [box(f'{nm}f{i}', (0.006, W - 0.02, H - 0.02), (-0.15 + 0.03 * i, 0, z), 'aluminium') for i in range(11)]
        for j, y in enumerate((-0.25, -0.08, 0.08, 0.25)):
            cl.append(cyl(f'{nm}t{j}', 0.012, -0.2, 0.17, 'copper', 10, axis='X', center=(0, y, z + 0.12)))
            cl.append(cyl(f'{nm}u{j}', 0.012, -0.2, 0.17, 'copper', 10, axis='X', center=(0, y, z - 0.12)))
        cl += [cyl(f'{nm}h{s}', 0.03, -W / 2, W / 2 + 0.25, 'copper', 16, axis='Y', center=(0.22, 0, z + s * 0.12)) for s in (-1, 1)]
        P(m, nm, ('Exhaust-Air Coil (picks up heat)' if k == 0 else 'Supply-Air Coil (releases heat)') + ' — finned tubes', 'coils', cl, explode=(0, -0.6, 0.2 if k == 0 else -0.2), ref='hx_coils', section='keep')
    lp = [hollow_pipe('lpa', [(0.22, W / 2 + 0.25, ZE + 0.12), (0.22, W / 2 + 0.45, ZE + 0.12), (0.22, W / 2 + 0.45, ZS + 0.12), (0.22, W / 2 + 0.25, ZS + 0.12)], 0.03, 'paint_green', 24, bend=0.06),
          hollow_pipe('lpb', [(0.22, W / 2 + 0.25, ZS - 0.12), (0.6, W / 2 + 0.25, ZS - 0.12), (0.6, W / 2 + 0.25, ZE - 0.12), (0.22, W / 2 + 0.25, ZE - 0.12)], 0.03, 'paint_green', 24, bend=0.06),
          vessel('et', 0.1, 0.25, 0.006, 'paint_red', center=(0.6, W / 2 + 0.25, 0), heads=('2:1', '2:1'), z0=ZE + 0.1)]
    P(m, 'glycol_loop', 'Glycol Loop Piping & Expansion Tank', 'piping', lp, explode=(0, 0.5, 0), ref='hx_loop', section='keep')
    pmp = join('pm', [cyl('pv', 0.08, (ZE + ZS) / 2 - 0.07, (ZE + ZS) / 2 + 0.07, 'paint_blue', 24, center=(0.6, W / 2 + 0.25, 0)), cyl('pmt', 0.07, (ZE + ZS) / 2 + 0.07, (ZE + ZS) / 2 + 0.3, 'paint_motor', 24, center=(0.6, W / 2 + 0.25, 0))])
    P(m, 'loop_pump', 'Circulating Pump (in-line)', 'pumps', pmp, explode=(0.3, 0.3, 0), ref='hx_pump', section='keep')
    for k, (z, nm) in enumerate(((ZE, 'exhaust_fan'), (ZS, 'supply_fan'))):
        _fan_rotor(m, nm, ('Exhaust' if k == 0 else 'Supply') + ' Fan Impeller', (1.2 if k == 0 else -1.2, 0, z), 'X', 0.26, 'hx_fans', revs=4 if k == 0 else -4)
    droplets(m, 'glycol', 'Glycol circulating (dots)', 0.6, 0.6, ZS - 0.12, ZE - 0.12, n=6, mat='hydraulic_oil', y=W / 2 + 0.25, r=0.02)
    m.flow('exhaust_air', [(-2.0, 0, ZE), (2.0, 0, ZE)], 'exhaust', 0.03, 0.4)
    m.flow('supply_air', [(2.0, 0, ZS), (-2.0, 0, ZS)], 'air', 0.03, 0.4)
    m.flow('glycol', [(0.22, W / 2 + 0.45, ZE + 0.12), (0.22, W / 2 + 0.45, ZS + 0.12), (0.6, W / 2 + 0.25, ZS - 0.12), (0.6, W / 2 + 0.25, ZE - 0.12)], 'hydraulic_oil', 0.012, 0.3)
    _bands_x(m, [(-1.8, 0.0, 6), (0.0, 1.8, 3)], W, H, ZE, 'Air temperatures across the coils',
             'Warm exhaust air (orange) is cooled by the exhaust coil (blue after the coil), the glycol loop carries that heat to the supply coil, where cold fresh air is warmed. '
             'The two airstreams never mix — useful where cross-contamination is not allowed (labs, hospitals). Typical sensible effectiveness is about 45–65 %.')
    return m.export(out)


# =============================================================== EQ-250 Quench tower
def quench_tower(out):
    m = _model('quench_tower', 'Quench Tower (Down-Flow Spray Quench of Hot Gas)')
    R, Z0, Z1 = 0.5, 0.9, 3.0
    sh = vessel('sh', R, Z1 - Z0, 0.012, 'stainless', heads=('cone', '2:1'), z0=Z0)
    P(m, 'shell', 'Tower Shell (corrosion-resistant)', 'casing', sh, explode=(0, 0.6, 0), ref='qt_shell')
    sp = [cyl('sph', 0.03, -R + 0.05, R - 0.05, 'stainless', 16, axis='Y', center=(0, 0, Z1 - 0.3))] + [join(f'nz{k}', [cyl(f'nzb{k}', 0.025, Z1 - 0.38, Z1 - 0.3, 'brass', 12, center=(0, y, 0)), lathe(f'nzc{k}', [(0.0, Z1 - 0.38), (0.03, Z1 - 0.38), (0.0, Z1 - 0.43)], 'brass', 12, center=(0, y, 0))]) for k, y in enumerate((-0.3, 0.0, 0.3))]
    P(m, 'spray_nozzles', 'Spray Header & Atomising Nozzles', 'internals', sp, explode=(0, -0.5, 0.4), ref='qt_nozzles', section='keep')
    pl = P(m, 'sump', 'Quench Liquid Sump', 'fluid', liquid_v('lq', R - 0.012, Z0, Z0 + 0.25, head='cone', mat='water'), explode=(0, -0.3, -0.2), ref='qt_sump', section='keep')
    animate_level(m, pl, Z0 + 0.24, 0.03, lambda t: 0.5 + 0.5 * math.sin(TAU * t))
    nz = [nozzle('gin', (0, 0, Z1 + R * 0.5 + 0.02), (0, 0, 1), 0.2, 0.35), nozzle('gout', (-R, 0, Z0 + 0.6), (-1, 0, 0), 0.2, 0.35), nozzle('lo', (0, 0, Z0 - R * 0.9), (0, 0, -1), 0.05, 0.2)]
    P(m, 'nozzles', 'Hot Gas Inlet (top), Cooled Gas Outlet (side), Liquid Outlet', 'nozzles', nz, explode=(0, 0, 0.4), ref='qt_shell', section='keep')
    rc = [hollow_pipe('rc', [(0, 0, Z0 - R * 0.9 - 0.2), (0, 0, 0.25), (0.8, 0, 0.25), (0.8, 0, Z1 - 0.3), (R, 0, Z1 - 0.3)], 0.04, 'paint_grey', 24, bend=0.1)]
    P(m, 'recirculation', 'Recirculation Line', 'piping', rc, explode=(0.4, 0, 0), ref='qt_pump', section='keep')
    _pump(m, 'recirc_pump', 'Recirculation Pump', 0.45, 0.0, 0.25, 'qt_pump', explode=(0.3, -0.4, 0))
    P(m, 'skirt', 'Support Legs', 'structure', legs('lg', R, 0.0, Z0, n=4), explode=(0, 0, -0.3), ref='qt_shell', section='keep')
    droplets(m, 'spray', 'Spray Droplets Evaporating in the Hot Gas', -0.35, 0.35, Z1 - 0.45, Z0 + 0.3, n=14, mat='water', y=0.12, r=0.015)
    m.flow('hot_gas', [(0, 0.1, Z1 + 0.9), (0, 0.1, Z0 + 0.7), (-R - 0.4, 0.0, Z0 + 0.6)], 'flue_gas', 0.04, 0.4)
    m.flow('quench_liquid', [(0, 0, Z0 - 0.6), (0.8, 0, 0.25), (0.8, 0, Z1 - 0.3), (0, 0, Z1 - 0.32)], 'water', 0.018, 0.3)
    _bands_z(m, [(Z1 - 0.6, Z1 + 0.3, 9), (Z1 - 1.2, Z1 - 0.6, 6), (Z0 + 0.3, Z1 - 1.2, 3)], R, 'Gas temperature falls rapidly under the sprays',
             'Hot gas (e.g. several hundred °C from an incinerator or reactor) is cooled within a short distance to near its adiabatic saturation temperature as the spray water evaporates. '
             'Rapid quenching protects downstream equipment and limits the time spent in the temperature window where dioxins/furans can re-form (roughly 200–400 °C) in waste incineration.')
    return m.export(out)


# =============================================================== EQ-251 Cooling coil
def cooling_coil(out):
    m = _model('cooling_coil', 'Chilled-Water Cooling Coil in an Air-Handling Unit Section')
    CZ, W, H = 0.85, 0.9, 1.0
    cs = _hduct('cs', -1.2, 1.4, W, H, CZ, mat='paint_grey')
    P(m, 'casing', 'AHU Casing (insulated panels)', 'casing', cs, explode=(0, 0.6, 0), ref='cc_casing')
    cl = [box(f'fn{i}', (0.004, W - 0.03, H - 0.08), (-0.18 + 0.025 * i, 0, CZ + 0.02), 'aluminium') for i in range(15)]
    tpaths = []
    for j, y in enumerate((-0.3, -0.1, 0.1, 0.3)):
        t_, pts = _serp(f'ct{j}', -0.22, 0.22, CZ - H / 2 + 0.12, CZ + H / 2 - 0.1, 8, y, r=0.011, mat='copper')
        t_ = rotate(t_, 0, 'Z')
        cl.append(t_)
        tpaths.append(pts)
    P(m, 'coil', 'Finned-Tube Coil (aluminium fins on copper tubes)', 'coils', cl, explode=(0, -0.7, 0), ref='cc_coil', section='keep')
    hd = [cyl('hs', 0.035, CZ - H / 2 + 0.05, CZ + H / 2, 'copper', 16, center=(-0.3, W / 2 + 0.12, 0)), cyl('hr', 0.035, CZ - H / 2 + 0.05, CZ + H / 2, 'copper', 16, center=(0.3, W / 2 + 0.12, 0))]
    hd += [box('va', (0.12, 0.1, 0.12), (0.3, W / 2 + 0.12, CZ + H / 2 + 0.12), 'brass'), box('vac', (0.1, 0.1, 0.12), (0.3, W / 2 + 0.12, CZ + H / 2 + 0.26), 'paint_grey')]
    P(m, 'headers_valve', 'Supply/Return Headers & Chilled-Water Control Valve (actuated)', 'control', hd, explode=(0, 0.5, 0.3), ref='cc_valve', section='keep')
    pan = csg('pan', [box('pno', (0.7, W - 0.02, 0.08), (0.05, 0, CZ - H / 2 + 0.04), 'stainless')], [box('pni', (0.66, W - 0.06, 0.08), (0.05, 0, CZ - H / 2 + 0.08), 'stainless')], 'stainless')
    P(m, 'drain_pan', 'Sloped Condensate Drain Pan & Trap', 'drain', [pan, nozzle('dr', (0.35, -W / 2, CZ - H / 2 + 0.03), (0, -1, 0), 0.02, 0.2)], explode=(0, 0, -0.4), ref='cc_pan', section='keep')
    hs = csg('fh', [cyl('fho', 0.4, 0.9, 1.3, 'paint_grey', 48, axis='X', center=(0, 0, CZ))], [cyl('fhi', 0.37, 0.85, 1.35, 'paint_grey', 48, axis='X', center=(0, 0, CZ))], 'paint_grey')
    P(m, 'fan_housing', 'Fan Inlet Ring / Plenum', 'fan', hs, explode=(0.4, 0.4, 0), ref='cc_fan')
    _fan_rotor(m, 'fan', 'Supply Fan Impeller', (1.1, 0, CZ), 'X', 0.33, 'cc_fan', revs=4)
    droplets(m, 'condensate', 'Condensate Dripping off the Fins', -0.18, 0.18, CZ - 0.2, CZ - H / 2 + 0.06, n=8, mat='water', y=0.1, r=0.012)
    m.flow('air', [(-1.4, -0.2, CZ), (1.6, -0.2, CZ)], 'air', 0.03, 0.4)
    m.flow('chilled_water', [(-0.3, W / 2 + 0.12, CZ - H / 2 - 0.1)] + [(p[0], 0.1, p[2]) for p in tpaths[2]] + [(0.3, W / 2 + 0.12, CZ + H / 2 + 0.1)], 'water', 0.012, 0.3)
    _bands_x(m, [(-1.2, -0.25, 6), (0.25, 1.4, 2)], W, H, CZ, 'Air is cooled and dehumidified',
             'Warm, humid air (orange) passes the coil; it is cooled (blue) and, because the fin surface is below the air\'s dew point, moisture condenses and drains to the pan. '
             'Coil leaving-air temperature is controlled by modulating the chilled-water valve. Face velocity is kept low (≈ 2–2.5 m/s) to avoid carrying droplets off the coil.')
    return m.export(out)


# =============================================================== EQ-252 Cooling water distribution system
def cooling_water_distribution_system(out):
    m = _model('cooling_water_distribution_system', 'Cooling Water Distribution System (Tower, Pumps, Headers, Users)')
    TX, TZ = -1.6, 0.4
    tw = join('tw', [csg('twc', [box('two', (1.2, 1.2, 1.8), (TX, 0, TZ + 1.0), 'paint_green')], [box('twi', (1.12, 1.12, 1.9), (TX, 0, TZ + 1.0), 'paint_green'), box('twl', (1.3, 1.0, 0.5), (TX, 0, TZ + 0.55), 'paint_green')], 'paint_green'),
                     csg('fst', [cyl('fso', 0.5, TZ + 1.9, TZ + 2.3, 'paint_green', 48, center=(TX, 0, 0))], [cyl('fsi', 0.47, TZ + 1.85, TZ + 2.35, 'paint_green', 48, center=(TX, 0, 0))], 'paint_green')])
    P(m, 'cooling_tower', 'Induced-Draught Cooling Tower (casing, air inlets, fan stack)', 'tower', tw, explode=(0, 0.6, 0), ref='cw_tower')
    fill = [box(f'fl{k}', (1.1, 0.005, 0.5), (TX, -0.5 + 0.1 * k, TZ + 1.0), 'polypropylene') for k in range(11)]
    fill += [cyl('dh', 0.03, TX - 0.5, TX + 0.5, 'paint_grey', 16, axis='X', center=(0, 0, TZ + 1.5))] + [box('de', (1.1, 1.1, 0.02), (TX, 0, TZ + 1.7), 'polypropylene')]
    P(m, 'fill_distribution', 'Film Fill, Hot-Water Distribution & Drift Eliminators', 'internals', fill, explode=(0, -0.7, 0), ref='cw_fill', section='keep')
    _fan_rotor(m, 'tower_fan', 'Tower Fan', (TX, 0, TZ + 2.0), 'Z', 0.45, 'cw_tower', revs=3)
    bs = csg('bs', [box('bso', (1.4, 1.4, 0.45), (TX, 0, 0.225), 'cast_iron')], [box('bsi', (1.3, 1.3, 0.45), (TX, 0, 0.3), 'cast_iron')], 'cast_iron')
    P(m, 'basin', 'Cold-Water Basin', 'tower', bs, explode=(0, 0, -0.3), ref='cw_tower')
    pw = P(m, 'basin_water', 'Cold Water in the Basin', 'fluid', box('bw', (1.28, 0.64, 0.3), (TX, 0.32, 0.22), 'water'), explode=(0, -0.3, -0.2), ref='cw_tower', section='keep')
    animate_level(m, pw, 0.36, 0.02, lambda t: 0.5 + 0.5 * math.sin(TAU * t))
    for k, y in enumerate((-0.35, 0.35)):
        _pump(m, f'cw_pump_{k + 1}', f'CW Pump {k + 1} ' + ('(duty)' if k == 0 else '(standby)'), -0.45, y, 0.25, 'cw_pumps', explode=(0, (k * 2 - 1) * 0.3, 0))
    hp = [hollow_pipe('suc', [(TX + 0.7, 0, 0.25), (-0.57, 0, 0.25), (-0.57, -0.35, 0.25)], 0.06, 'paint_blue', 24, bend=0.08),
          hollow_pipe('sup', [(-0.45, -0.35, 0.4), (-0.45, -0.35, 0.8), (2.0, -0.35, 0.8)], 0.06, 'paint_blue', 24, bend=0.08),
          hollow_pipe('ret', [(2.0, 0.35, 1.3), (TX, 0.35, 1.3), (TX, 0.35, TZ + 1.5), (TX, 0.0, TZ + 1.5)], 0.06, 'paint_red', 24, bend=0.1)]
    hp += [box('st', (0.2, 0.18, 0.18), (0.2, -0.35, 0.8), 'paint_blue_dark')]
    P(m, 'headers', 'Suction Line, Supply Header (with strainer) & Return Header', 'piping', hp, explode=(0, 0, 0.3), ref='cw_headers', section='keep')
    us = []
    for k, x in enumerate((0.8, 1.6)):
        us.append(vessel(f'ux{k}', 0.16, 0.6, 0.008, 'paint_grey', axis='Y', center=(x, 0, 1.05), heads=('2:1', '2:1'), z0=-0.3))
        us.append(hollow_pipe(f'ui{k}', [(x, -0.35, 0.8), (x, -0.35, 0.9), (x, -0.2, 0.95)], 0.03, 'paint_blue', 16, bend=0.04))
        us.append(hollow_pipe(f'uo{k}', [(x, 0.2, 1.15), (x, 0.35, 1.2), (x, 0.35, 1.3)], 0.03, 'paint_red', 16, bend=0.04))
    P(m, 'users', 'Heat Users (process coolers / condensers)', 'users', us, explode=(0, 0, 0.5), ref='cw_users', section='keep')
    droplets(m, 'tower_rain', 'Water Falling through the Fill (cooled by air)', TX - 0.4, TX + 0.4, TZ + 1.45, 0.4, n=12, mat='water', y=0.3, r=0.015)
    m.flow('supply', [(TX + 0.7, 0, 0.25), (-0.57, -0.35, 0.25), (-0.45, -0.35, 0.8), (2.0, -0.35, 0.8)], 'water', 0.025, 0.4)
    m.flow('return', [(2.0, 0.35, 1.3), (TX, 0.35, 1.3), (TX, 0.0, TZ + 1.5)], 'flow_discharge', 0.025, 0.4)
    m.flow('tower_air', [(TX, -0.9, TZ + 0.55), (TX, -0.2, TZ + 0.8), (TX, 0, TZ + 2.6)], 'air', 0.03, 0.4)
    _bands_x(m, [(-0.7, 0.6, 2), (0.6, 2.1, 6)], 0.5, 0.2, 0.8, 'Supply (cool) and return (warm) water',
             'Water leaves the basin cool, picks up heat in the users and returns warmer to the tower. The temperature difference supply–return is the range (often ≈ 5–10 °C); '
             'how close the cold water gets to the air\'s wet-bulb temperature is the approach (often ≈ 3–6 °C). Evaporation, drift and blowdown losses are replaced by make-up water.', cy=-0.35)
    return m.export(out)


# =============================================================== EQ-247 Gas-fired furnace (process heater)
def gas_fired_furnace(out):
    m = _model('gas_fired_furnace', 'Gas-Fired Process Heater (Box Type: Radiant + Convection Sections)')
    Wx, Wy, H, Z0 = 1.8, 1.2, 1.8, 0.4
    rb = csg('rb', [box('rbo', (Wx + 0.2, Wy + 0.2, H + 0.1), (0, 0, Z0 + H / 2), 'paint_grey')],
             [box('rbi', (Wx, Wy, H), (0, 0, Z0 + H / 2 + 0.05), 'paint_grey'), box('rbt', (0.9, Wy - 0.2, 0.3), (0, 0, Z0 + H), 'paint_grey')] + [cyl(f'bh{k}', 0.12, Z0 - 0.2, Z0 + 0.1, 'paint_grey', 24, center=(x, 0, 0)) for k, x in enumerate((-0.45, 0.45))], 'paint_grey')
    lin = csg('ln', [box('lno', (Wx, Wy, H), (0, 0, Z0 + H / 2 + 0.05), 'refractory')], [box('lni', (Wx - 0.12, Wy - 0.12, H - 0.06), (0, 0, Z0 + H / 2 + 0.08), 'refractory'), box('lnt', (0.9, Wy - 0.3, 0.3), (0, 0, Z0 + H), 'refractory')] +
              [cyl(f'lh{k}', 0.12, Z0 - 0.2, Z0 + 0.2, 'refractory', 24, center=(x, 0, 0)) for k, x in enumerate((-0.45, 0.45))], 'refractory')
    P(m, 'radiant_box', 'Radiant Section Casing & Refractory Lining', 'casing', [rb, lin], explode=(0, 0.8, 0), ref='ff_radiant')
    rt = []
    for side, x in (('l', -Wx / 2 + 0.15), ('r', Wx / 2 - 0.15)):
        pts = []
        for k, y in enumerate([-0.4, -0.2, 0.0, 0.2, 0.4]):
            za, zb = (Z0 + 0.25, Z0 + H - 0.2) if k % 2 == 0 else (Z0 + H - 0.2, Z0 + 0.25)
            pts += [(x, y, za), (x, y, zb)]
        rt.append(sweep_tube('rt' + side, pts, 0.035, 'steel_dark', 10))
    P(m, 'radiant_tubes', 'Radiant Coil (vertical tubes along the walls)', 'tubes', rt, explode=(0, -0.8, 0), ref='ff_tubes', section='keep')
    CZc = Z0 + H + 0.45
    cv = _hduct('cv', -0.45, 0.45, Wy - 0.2, 0.6, CZc)
    cv = rotate(cv, math.pi / 2, 'Z', (0, 0, CZc))
    ct, cpts = _serp('ctu', -0.4, 0.4, CZc - 0.22, CZc + 0.22, 6, 0.0, r=0.03, mat='steel')
    ct = rotate(ct, math.pi / 2, 'Z', (0, 0, CZc))
    P(m, 'convection_section', 'Convection Section (process feed preheat, shield tubes)', 'tubes', [cv, ct], explode=(0, 0.6, 0.4), ref='ff_convection')
    stk = join('stk', [cyl('sk', 0.22, CZc + 0.3, CZc + 2.0, 'paint_grey', 48, r_in=0.2), lathe('sb', [(0.2, CZc + 0.3), (0.45, CZc + 0.3), (0.22, CZc + 0.6), (0.2, CZc + 0.6)], 'paint_grey', 48)])
    P(m, 'stack', 'Stack (natural draught)', 'casing', stk, explode=(0, 0, 0.6), ref='ff_stack')
    dmp = box('dmp', (0.38, 0.01, 0.3), (0, 0, CZc + 1.0), 'steel')
    pdm = P(m, 'stack_damper', 'Stack Damper (controls draught)', 'control', dmp, explode=(0, -0.4, 0.6), ref='ff_damper', section='keep', pivot=(0, 0, CZc + 1.0))
    keys_loop(m, pdm, lambda t: (0, 0.0, 0.4 + 0.2 * math.sin(TAU * t)), 'rotation_euler')
    bn = [join(f'bn{k}', [cyl(f'bnb{k}', 0.1, Z0 - 0.5, Z0 - 0.2, 'paint_blue', 24, center=(x, 0, 0)), cyl(f'bnt{k}', 0.05, Z0 - 0.2, Z0 + 0.12, 'steel', 16, center=(x, 0, 0))]) for k, x in enumerate((-0.45, 0.45))]
    P(m, 'burners', 'Floor-Fired Gas Burners (low-NOx, with air registers)', 'combustion', bn, explode=(0, 0, -0.4), ref='ff_burners', section='keep')
    for k, x in enumerate((-0.45, 0.45)):
        _flame(m, f'flame_{k + 1}', f'Burner Flame {k + 1}', (x, 0, Z0 + 0.12), (0, 0, 1), 1.2, 0.17, 'ff_burners')
    stl = [box(f'cl{k}', (0.1, 0.1, Z0), (sx * (Wx / 2), sy * (Wy / 2), Z0 / 2), 'paint_grey') for k, (sx, sy) in enumerate(((-1, -1), (-1, 1), (1, -1), (1, 1)))]
    P(m, 'structure', 'Support Columns (burner access below)', 'structure', stl, explode=(0, 0, -0.3), ref='ff_radiant', section='keep')
    droplets(m, 'flue_particles', 'Hot Flue Gas Rising to the Convection Section', -0.3, 0.3, Z0 + 1.2, CZc + 1.8, n=8, mat='flue_gas', y=0.2, r=0.025)
    m.flow('flue_gas', [(0, 0.2, Z0 + 1.3), (0, 0.2, CZc), (0, 0.0, CZc + 2.1)], 'flue_gas', 0.04, 0.4)
    m.flow('process_fluid', [(0.0, -0.8, CZc + 0.22), (0.0, -0.4, CZc + 0.22), (0.0, 0.4, CZc - 0.22), (0.0, 0.7, CZc - 0.22), (-Wx / 2 + 0.15, 0.4, Z0 + H - 0.2), (-Wx / 2 + 0.15, 0.4, Z0 + 0.25), (-Wx / 2 + 0.15, -0.4, Z0 + 0.25), (-Wx / 2 + 0.15, -0.8, Z0 + 0.25)], 'flow_discharge', 0.02, 0.4)
    _bands_z(m, [(Z0, Z0 + H, 9), (Z0 + H, CZc + 0.3, 6), (CZc + 0.3, CZc + 2.0, 4)], 1.25, 'Flue-gas temperature: radiant → convection → stack',
             'Most heat (often ~ 60–70 %) is absorbed in the radiant section, where the flue gas is hottest (bridge-wall temperature often ~ 700–900 °C). The convection section recovers '
             'more heat from the cooler gas; the stack temperature sets the main efficiency loss. Tube metal temperature and heat flux limit the firing rate (API 560 / API 530).', cx=0.0)
    return m.export(out)


# =============================================================== EQ-248 Electric furnace (electric arc furnace)
def electric_furnace(out):
    m = _model('electric_furnace', 'Electric Arc Furnace (AC, Three Graphite Electrodes)')
    R, Z0, Z1 = 1.0, 0.6, 1.6
    shell = csg('sh', [lathe('sho', [(0.0, Z0 - 0.25), (R * 0.8, Z0 - 0.25), (R + 0.06, Z0 + 0.2), (R + 0.06, Z1), (0.0, Z1)], 'paint_grey', 96)],
                [lathe('shi', [(0.0, Z0 - 0.2), (R * 0.78, Z0 - 0.2), (R, Z0 + 0.2), (R, Z1 + 0.1), (0.0, Z1 + 0.1)], 'paint_grey', 96)], 'paint_grey')
    hearth = csg('hr', [lathe('hro', [(0.0, Z0 - 0.2), (R * 0.78, Z0 - 0.2), (R, Z0 + 0.2), (R, Z0 + 0.6), (0.0, Z0 + 0.6)], 'refractory', 96)],
                 [lathe('hri', [(0.0, Z0 - 0.05), (R * 0.6, Z0 - 0.05), (R - 0.14, Z0 + 0.25), (R - 0.14, Z0 + 0.7), (0.0, Z0 + 0.7)], 'refractory', 96)], 'refractory')
    panels = [cyl('wp', R + 0.0, Z0 + 0.6, Z1, 'steel', 96, r_in=R - 0.06)]
    P(m, 'shell', 'Shell, Refractory Hearth & Water-Cooled Wall Panels', 'casing', [shell, hearth] + panels, explode=(0, 0.9, 0), ref='ef_shell')
    bath = lathe('bt', [(0.0, Z0 - 0.04), (R * 0.6, Z0 - 0.04), (R - 0.14, Z0 + 0.25), (R - 0.14, Z0 + 0.35), (0.0, Z0 + 0.35)], 'hot_glow', 64, a0=0.0, a1=math.pi, cap_mat='hot_glow')
    P(m, 'molten_bath', 'Molten Steel Bath & Slag', 'fluid', bath, explode=(0, -0.4, -0.2), ref='ef_bath', section='keep')
    rf = csg('rf', [lathe('rfo', [(0.0, Z1 + 0.02), (R + 0.1, Z1 + 0.02), (R + 0.1, Z1 + 0.1), (0.35, Z1 + 0.35), (0.0, Z1 + 0.35)], 'steel', 96)],
             [cyl(f'rh{k}', 0.1, Z1 - 0.1, Z1 + 0.5, 'steel', 24, center=(0.3 * math.cos(TAU * k / 3 + math.pi / 2), 0.3 * math.sin(TAU * k / 3 + math.pi / 2), 0)) for k in range(3)] +
             [cyl('rfd', 0.15, Z1 - 0.1, Z1 + 0.5, 'steel', 24, center=(0.6, 0.3, 0))], 'steel')
    P(m, 'roof', 'Water-Cooled Roof with Refractory Delta & Electrode Ports (swings aside for charging)', 'casing', rf, explode=(0, 0, 0.8), ref='ef_roof')
    pos = [(0.3 * math.cos(TAU * k / 3 + math.pi / 2), 0.3 * math.sin(TAU * k / 3 + math.pi / 2)) for k in range(3)]
    for k, (x, y) in enumerate(pos):
        el = join(f'el{k}', [cyl(f'eg{k}', 0.085, Z0 + 0.5, Z1 + 1.4, 'carbon', 32, center=(x, y, 0)), cyl(f'ec{k}', 0.12, Z1 + 1.0, Z1 + 1.15, 'copper', 24, center=(x, y, 0)),
                             box(f'ea{k}', (1.6, 0.12, 0.1), (x - 0.8 - 0.1, y, Z1 + 1.08), 'copper')])
        pe = P(m, f'electrode_{k + 1}', f'Graphite Electrode {k + 1} with Clamp & Current-Conducting Arm', 'electrodes', el, explode=(0, 0, 0.6 + 0.2 * k), ref='ef_electrodes', section='keep')
        keys_loop(m, pe, lambda t, k=k: (0, 0, 0.03 * math.sin(TAU * (2 * t + k / 3))))
        arc = lathe(f'arc{k}', [(0.0, Z0 + 0.36), (0.07, Z0 + 0.38), (0.05, Z0 + 0.5), (0.0, Z0 + 0.52)], 'hot_glow', 16, center=(x, y, 0))
        pa = P(m, f'arc_{k + 1}', f'Electric Arc {k + 1}', 'electrodes', arc, explode=(0, 0, 0), ref='ef_arc', section='keep', pivot=(x, y, Z0 + 0.36))
        keys_loop(m, pa, lambda t, k=k: (1 + 0.25 * math.sin(TAU * (9 * t + k / 3)), 1 + 0.25 * math.sin(TAU * (9 * t + k / 3)), 1 + 0.1 * math.sin(TAU * (2 * t + k / 3))), 'scale')
    mast = [box('ms', (0.25, 0.5, Z1 + 1.3), (-1.75, 0, (Z1 + 1.3) / 2), 'paint_grey'), box('msb', (0.6, 0.9, 0.12), (-1.75, 0, 0.06), 'paint_grey')] + \
           [cyl(f'hc{k}', 0.05, Z1 + 0.2, Z1 + 1.0, 'chrome', 16, center=(-1.55, (k - 1) * 0.15, 0)) for k in range(3)]
    P(m, 'mast_structure', 'Electrode Mast Structure & Hydraulic Regulation', 'structure', mast, explode=(-0.6, 0, 0), ref='ef_mast', section='keep')
    rk = [box('rk', (2.4, 1.6, 0.2), (0, 0, Z0 - 0.35), 'paint_grey')] + [box(f'rc{s}', (0.4, 0.3, Z0 - 0.45), (s * 0.9, 0, (Z0 - 0.45) / 2), 'paint_grey') for s in (-1, 1)]
    rk += [lathe('tsp', [(0.0, Z0 + 0.1), (0.1, Z0 + 0.1), (0.1, Z0 - 0.6), (0.0, Z0 - 0.6)], 'refractory', 24, center=(0.6, 0, 0))]
    P(m, 'tilting_platform', 'Tilting Rockers & Eccentric Bottom Tap (EBT)', 'structure', rk, explode=(0, 0, -0.4), ref='ef_tilt', section='keep')
    tr = join('trf', [box('tf', (0.7, 0.6, 0.8), (-2.6, 0, 0.4), 'paint_grey'), cyl('bus', 0.05, -2.3, -1.8, 'copper', 16, axis='X', center=(0, 0, Z1 + 1.08))])
    P(m, 'transformer', 'Furnace Transformer & Secondary Bus (high current to the electrodes)', 'electrical', tr, explode=(-0.5, 0, 0), ref='ef_transformer', section='keep')
    m.flow('power', [(-2.6, 0, 0.85), (-2.6, 0, Z1 + 1.08), (-1.8, 0, Z1 + 1.08), (pos[0][0], 0, Z1 + 1.08), (pos[0][0], 0, Z0 + 0.55)], 'electric', 0.025, 0.3)
    m.flow('fume_extraction', [(0.6, 0.3, Z1 + 0.2), (0.6, 0.3, Z1 + 0.9), (1.4, 0.3, Z1 + 0.9)], 'flue_gas', 0.04, 0.3)
    m.flow('tapping', [(0.6, 0, Z0), (0.6, 0, Z0 - 0.8)], 'flame', 0.03, 0.2, active=[(0.7, 1.0)])
    m.overlay('temperature', join('tzs', [lathe('tz1', [(0.12, Z0 + 0.36), (R - 0.16, Z0 + 0.36), (R - 0.16, Z0 + 0.38), (0.12, Z0 + 0.38)], 'pressure_9', 64)]),
              'Arc and bath temperatures', 'The arcs between the electrode tips and the scrap/bath are extremely hot (thousands of °C) and melt the charge; liquid steel is typically tapped at '
              'around 1600–1650 °C. Water-cooled panels and roof protect the shell; foamy slag shields the panels from arc radiation.', split=True)
    return m.export(out)


# ===================================================================== metadata
def _std(*items):
    return [{'id': i, 'title': t, 'relevance': r, 'edition': 'to be verified'} for i, t, r in items]


def _c(fn, cons, mat, op='—', fm=('—',), insp=('Visual',)):
    return C(fn, cons, mat, op, list(fm), list(insp))


_TEMA = _std(('TEMA', 'Standards of the Tubular Exchanger Manufacturers Association', 'Mechanical design of shell & tube exchangers.'), ('ASME BPVC VIII-1', 'Pressure vessels', 'Pressure parts.'), ('API 660', 'Shell-and-tube heat exchangers', 'Refinery/petrochemical service.'))
_BOIL = _std(('ASME BPVC Section I', 'Rules for construction of power boilers', 'Boiler design and safety valves.'), ('EN 12952 / EN 12953', 'Water-tube / shell boilers', 'European boiler codes.'))
_FIRED = _std(('API 560', 'Fired heaters for general refinery service', 'Design.'), ('API 530', 'Calculation of heater-tube thickness', 'Tube design.'), ('NFPA 86', 'Ovens and furnaces', 'Combustion safety.'))
_HVAC = _std(('AHRI 410', 'Forced-circulation air-cooling and air-heating coils', 'Coil rating.'), ('ASHRAE Handbook — HVAC Systems and Equipment', 'Coils and heat recovery', 'Design guidance.'))

META = {
    'reboiler': {'summary': ('A kettle reboiler supplies the vapour that drives a distillation column. Liquid from the column bottom floods a horizontal tube bundle inside an enlarged shell; steam or hot oil '
                             'inside the tubes boils part of the liquid. Vapour rises to the column through the top nozzles; the remaining liquid spills over a weir and leaves as bottom product.'),
                 'classification': {'family': 'Heat exchanger', 'type': 'Kettle reboiler (TEMA K-shell, U-tube bundle)'}, 'model_configuration': {'animation': 'Boiling pool with rising vapour bubbles; overflow past the weir'},
                 'standards': _TEMA, 'references': ['Kister — Distillation Operation', 'TEMA Standards'],
                 'components': {'rb_shell': _c('Holds the boiling pool and gives vapour space for disengagement.', 'Enlarged kettle shell with bundle neck.', 'Carbon steel.', 'Shell side boils.', ['Fouling, corrosion'], ['Thickness, internal inspection']),
                                'rb_channel': _c('Distributes heating medium into the tubes and collects condensate.', 'Channel with pass partition and tubesheet.', 'Carbon steel.'),
                                'rb_bundle': _c('Transfers heat from steam to the boiling liquid.', 'Removable U-tube bundle with support plates.', 'Carbon/stainless steel.', '—', ['Fouling, tube leaks, vibration'], ['Eddy current, hydro-test']),
                                'rb_weir': _c('Keeps the bundle submerged.', 'Plate weir.', 'Steel.'), 'rb_liquid': _c('Process liquid (boiling pool / product).', '—', '—'),
                                'rb_nozzles': _c('Vapour, feed, product, steam and condensate connections.', 'Nozzles.', 'Steel.'), 'rb_saddles': _c('Supports.', 'Saddles.', 'Steel.')}},
    'preheater': {'summary': ('A preheater raises the temperature of a fluid before it enters the main process — for example a feedwater heater, where turbine extraction steam condenses on the outside '
                              'of a U-tube bundle and heats the boiler feedwater flowing inside. This recovers heat and improves cycle efficiency.'),
                  'classification': {'family': 'Heat exchanger', 'type': 'Shell & U-tube condensing preheater'}, 'model_configuration': {'animation': 'Condensate drips; level held in drain-cooling zone'},
                  'standards': _TEMA + _std(('HEI 2622', 'Standards for closed feedwater heaters', 'Power-plant feedwater heaters.'),), 'references': ['HEI feedwater heater standards'],
                  'components': {'ph_shell': _c('Contains the condensing steam.', 'Cylindrical shell.', 'Carbon steel.'), 'ph_channel': _c('Water box: water in/out.', 'Channel, pass partition, tubesheet.', 'Carbon steel.'),
                                 'ph_bundle': _c('Heat transfer surface.', 'U-tubes.', 'Stainless/carbon steel.', '—', ['Tube leaks, erosion at inlet'], ['Eddy current']),
                                 'ph_baffles': _c('Support tubes, direct steam; impingement plate protects tubes.', 'Segmental baffles.', 'Steel.'), 'ph_condensate': _c('Condensate level (drain cooling).', '—', '—'),
                                 'ph_nozzles': _c('Steam, drain, water and vent connections.', 'Nozzles.', 'Steel.', 'Vent non-condensables continuously.'), 'ph_saddles': _c('Supports.', 'Saddles.', 'Steel.')}},
    'economizer': {'summary': ('An economizer recovers heat from boiler flue gas to preheat the feedwater before it enters the drum. Banks of (often finned) serpentine tubes sit in the gas duct after the '
                               'main heating surfaces. Gas flows down while water flows up — counter-flow — so the gas leaves cooler and boiler efficiency rises.'),
                   'classification': {'family': 'Boiler heat recovery', 'type': 'Finned serpentine economizer'}, 'model_configuration': {'animation': 'Water tracers rise through the serpentine; soot blower rotates'},
                   'standards': _BOIL, 'references': ['Babcock & Wilcox — Steam: its generation and use'],
                   'components': {'ec_casing': _c('Encloses the gas path.', 'Insulated casing, ash hopper.', 'Steel.'), 'ec_tubes': _c('Transfer heat from gas to water.', 'Serpentine finned tubes.', 'Carbon steel.', 'Keep gas above acid dew point.', ['Cold-end corrosion, erosion, fouling'], ['Thickness survey']),
                                  'ec_headers': _c('Distribute and collect water.', 'Headers.', 'Carbon steel.'), 'ec_sootblower': _c('Removes ash deposits from fins.', 'Rotary lance with nozzles.', 'Alloy steel.', '—', ['Erosion of tubes if misaligned'], ['Check alignment'])}},
    'superheater': {'summary': ('A superheater heats saturated steam from the boiler drum above its saturation temperature. Dry superheated steam improves turbine efficiency and avoids blade erosion. '
                                'Pendant tube platens hang in the hot gas path; a spray attemperator between the primary and secondary stages controls the final steam temperature.'),
                    'classification': {'family': 'Boiler heat transfer', 'type': 'Two-stage pendant superheater with interstage attemperator'}, 'model_configuration': {'animation': 'Steam tracers through the platens'},
                    'standards': _BOIL, 'references': ['Babcock & Wilcox — Steam'],
                    'components': {'sh_casing': _c('Gas pass and supports.', 'Casing, hangers.', 'Steel.'), 'sh_tubes': _c('Superheat the steam.', 'Pendant platens and headers.', 'Alloy steel (T11/T22/T91, austenitic).', 'Highest metal temperatures in the boiler.', ['Creep, overheating, fireside corrosion'], ['Oxide scale thickness, metallurgy']),
                                   'sh_attemperator': _c('Controls final steam temperature by spraying feedwater.', 'Spray nozzle in link pipe with thermal liner.', 'Alloy steel.', '—', ['Thermal fatigue cracking'], ['NDT of liner'])}},
    'air_preheater': {'summary': ('A rotary regenerative air preheater transfers heat from boiler flue gas to the incoming combustion air. A large rotor packed with corrugated steel plates turns slowly; '
                                  'the plates are heated while passing through the gas side and release that heat while passing through the air side.'),
                      'classification': {'family': 'Boiler heat recovery', 'type': 'Ljungström rotary regenerative (vertical shaft)'}, 'model_configuration': {'animation': 'Rotor turns; gas down, air up'},
                      'standards': _std(('ASME PTC 4.3', 'Air heaters — performance test code', 'Performance testing.'),), 'references': ['Babcock & Wilcox — Steam'],
                      'components': {'ap_housing': _c('Encloses the rotor.', 'Housing.', 'Steel.'), 'ap_rotor': _c('Stores and transfers heat.', 'Rotor with heating-element baskets.', 'Steel/enamelled cold end.', '≈ 1–3 rpm.', ['Fouling, cold-end corrosion'], ['ΔP trend, wash']),
                                     'ap_seals': _c('Limit air leakage into the gas side.', 'Radial, axial and circumferential seals; sector plates.', 'Steel.', '—', ['Wear → leakage'], ['Leakage test (O₂ rise)']),
                                     'ap_ducts': _c('Connect gas and air paths.', 'Ducts.', 'Steel.'), 'ap_drive': _c('Turns the rotor.', 'Motor, reducer, pin rack.', '—')}},
    'steam_generator': {'summary': ('A packaged steam generator (shell or fire-tube boiler) produces steam for heating and process use. Hot combustion gases from the burner pass through the furnace tube and '
                                    'then through two banks of smoke tubes (three passes), all surrounded by water inside the pressure shell. Steam collects above the water level and leaves via the main steam valve.'),
                        'classification': {'family': 'Boiler', 'type': '3-pass dry-back fire-tube (shell) boiler'}, 'model_configuration': {'animation': 'Flame, boiling bubbles, level'},
                        'standards': _BOIL, 'references': ['Spirax Sarco — The Steam and Condensate Loop'],
                        'components': {'sg_shell': _c('Pressure shell containing water and steam.', 'Rolled shell with stayed end plates.', 'Boiler-quality steel.', '—', ['Corrosion, scale'], ['Statutory inspection']),
                                       'sg_furnace': _c('First pass: combustion chamber.', 'Corrugated furnace tube.', 'Boiler steel.', 'Highest heat flux.', ['Overheating from scale'], ['Internal inspection']),
                                       'sg_reversal': _c('Turns gases from the furnace into the 2nd pass.', 'Refractory-lined rear reversal chamber (dry-back); wet-back designs use a water-cooled chamber instead.', 'Steel/refractory.', '—', ['Refractory cracking, gas leakage'], ['Inspect refractory']), 'sg_tubes': _c('2nd and 3rd pass heat transfer.', 'Smoke tubes.', 'Steel.', '—', ['Soot fouling, leaks'], ['Brush, inspect']),
                                       'sg_smokebox': _c('Gas turning boxes and stack.', 'Smoke boxes, stack.', 'Steel.'), 'sg_burner': _c('Mixes and burns fuel with air.', 'Forced-draught burner with fan and gas train.', '—', 'Flame safeguard & purge sequence.', ['Flame failure'], ['Combustion analysis']),
                                       'sg_water': _c('Boiler water (level animated).', '—', '—'), 'sg_fittings': _c('Safety and control fittings.', 'Valves, gauges, level controls.', '—', 'Low-water cut-out tested regularly.', ['Stuck safety valve'], ['Test'])}},
    'waste_heat_recovery_boiler': {'summary': ('A waste heat recovery boiler (heat recovery steam generator, HRSG) makes steam from the hot exhaust of a gas turbine, engine, furnace or kiln. The gas passes '
                                               'superheater, evaporator and economizer banks in turn; water/steam circulates naturally between the drum and evaporator.'),
                                   'classification': {'family': 'Boiler', 'type': 'Horizontal natural-circulation HRSG (single pressure)'}, 'model_configuration': {'animation': 'Circulation tracers; drum level'},
                                   'standards': _BOIL, 'references': ['Ganapathy — Waste Heat Boiler Deskbook'],
                                   'components': {'hr_casing': _c('Gas path, transitions and stack.', 'Insulated casing.', 'Steel.'), 'hr_coils': _c('Heat transfer banks (SH, EVAP, ECO).', 'Finned vertical tubes with headers.', 'Carbon/alloy steel.', '—', ['Flow-accelerated corrosion, fatigue'], ['Thickness, NDT']),
                                                  'hr_drum': _c('Separates steam from water; holds inventory.', 'Steam drum with internals.', 'Carbon steel.', 'Level control critical.', ['Carry-over'], ['Level gauges']), 'hr_piping': _c('Circulation links.', 'Downcomer, risers.', 'Steel.')}},
    'heat_recovery_system': {'summary': ('A run-around coil heat recovery system recovers heat from building or process exhaust air. A finned coil in the exhaust duct heats a water–glycol loop; a pump carries it '
                                         'to a second coil in the supply duct, which preheats the incoming fresh air. The airstreams never mix.'),
                             'classification': {'family': 'Heat recovery', 'type': 'Run-around coil loop'}, 'model_configuration': {'animation': 'Fans turn; glycol circulates'},
                             'standards': _HVAC, 'references': ['ASHRAE Handbook — Air-to-air energy recovery'],
                             'components': {'hx_ducts': _c('Air paths.', 'Ducts.', 'Galvanised steel.'), 'hx_coils': _c('Exchange heat between air and glycol.', 'Finned copper/aluminium coils.', 'Cu/Al.', '—', ['Fouling, freezing'], ['Clean']),
                                            'hx_loop': _c('Carries glycol.', 'Pipes and expansion tank.', 'Steel.'), 'hx_pump': _c('Circulates glycol.', 'In-line pump.', '—'), 'hx_fans': _c('Move the air.', 'Fans.', 'Aluminium/steel.')}},
    'quench_tower': {'summary': ('A quench tower rapidly cools a hot gas stream by spraying water (or a recirculated liquid) into it. Evaporation of the droplets absorbs heat so the gas cools to near its '
                                 'saturation temperature within a short distance, protecting downstream scrubbers and filters.'),
                     'classification': {'family': 'Gas cooling', 'type': 'Down-flow spray quench'}, 'model_configuration': {'animation': 'Spray droplets; sump level'},
                     'standards': _std(('ASME BPVC VIII-1', 'Pressure vessels', 'Where pressure-rated.'),), 'references': ['EPA Air Pollution Control Cost Manual'],
                     'components': {'qt_shell': _c('Contains the quench zone.', 'Vertical shell.', 'Alloy / FRP-lined steel.', 'Wet/dry interface is corrosive.', ['Corrosion at wet-dry line'], ['Inspect']),
                                    'qt_nozzles': _c('Atomise the quench liquid.', 'Spray header & nozzles.', 'Alloy.', '—', ['Plugging, erosion'], ['Spray pattern check']),
                                    'qt_sump': _c('Collects liquid.', '—', '—'), 'qt_pump': _c('Recirculates liquid.', 'Pump and line.', '—')}},
    'cooling_coil': {'summary': ('A cooling coil cools and dehumidifies air in an air-handling unit. Chilled water flows through copper tubes bonded to thin aluminium fins; air passing over the fins is cooled, '
                                 'and moisture condenses on the cold surface and drains to a pan.'),
                     'classification': {'family': 'HVAC heat exchanger', 'type': 'Chilled-water finned-tube coil'}, 'model_configuration': {'animation': 'Fan turns; condensate drips'},
                     'standards': _HVAC, 'references': ['ASHRAE Handbook — HVAC Systems and Equipment'],
                     'components': {'cc_casing': _c('Encloses the coil section.', 'Insulated panels.', 'Galvanised steel.'), 'cc_coil': _c('Cools and dehumidifies air.', 'Finned tube coil.', 'Cu tubes/Al fins.', '—', ['Fouling, leaks, freezing'], ['Clean, pressure test']),
                                    'cc_valve': _c('Controls chilled-water flow.', 'Headers and control valve.', 'Cu/brass.'), 'cc_pan': _c('Collects condensate.', 'Sloped stainless pan and trap.', 'Stainless steel.', '—', ['Standing water → microbial growth'], ['Clean']),
                                    'cc_fan': _c('Moves the air.', 'Fan and housing.', 'Steel.')}},
    'cooling_water_distribution_system': {'summary': ('A cooling water distribution system circulates water from a cooling tower to the plant\'s heat users and back. Pumps draw cold water from the tower basin and push it '
                                                      'through a supply header to coolers and condensers; the warmed water returns to the tower, where evaporation cools it again.'),
                                          'classification': {'family': 'Utility system', 'type': 'Open recirculating cooling water system'}, 'model_configuration': {'animation': 'Tower fan, pumps, falling water'},
                                          'standards': _std(('CTI ATC-105', 'Acceptance test code for water cooling towers', 'Performance.'),), 'references': ['CTI publications'],
                                          'components': {'cw_tower': _c('Cools the water by evaporation.', 'Tower, fan, basin.', 'FRP/concrete/steel.', '—', ['Fill fouling, scaling'], ['Inspect']),
                                                         'cw_fill': _c('Spreads water into films for contact with air.', 'Film fill, distribution, drift eliminators.', 'PVC/PP.'),
                                                         'cw_pumps': _c('Circulate the water.', 'Centrifugal pumps (duty/standby).', '—'), 'cw_headers': _c('Distribute water.', 'Headers with strainer.', 'Steel/HDPE.'),
                                                         'cw_users': _c('Heat users.', 'Coolers/condensers.', '—')}},
    'gas_fired_furnace': {'summary': ('A gas-fired process heater (furnace) heats a process fluid flowing in tubes. Burners on the floor fire into a refractory-lined radiant box; the tubes along the walls '
                                      'absorb radiant heat. The flue gas then passes a convection section that preheats the feed before leaving through the stack.'),
                          'classification': {'family': 'Fired equipment', 'type': 'Box-type fired heater with convection section'}, 'model_configuration': {'animation': 'Burner flames; damper modulates'},
                          'standards': _FIRED, 'references': ['API 560'],
                          'components': {'ff_radiant': _c('Radiant enclosure.', 'Steel casing with refractory lining.', 'Steel/refractory.', '—', ['Refractory damage, hot spots'], ['IR thermography']),
                                         'ff_tubes': _c('Carry and heat the process fluid.', 'Radiant coil.', 'Alloy steel.', 'Limit tube-metal temperature.', ['Coking, creep'], ['TMT monitoring']),
                                         'ff_convection': _c('Recover heat from the cooler flue gas.', 'Tube bank.', 'Carbon/alloy steel.'), 'ff_stack': _c('Provides draught.', 'Stack.', 'Steel.'),
                                         'ff_damper': _c('Controls draught.', 'Damper blade.', 'Steel.'), 'ff_burners': _c('Burn fuel with air.', 'Low-NOx burners.', '—', 'Burner management system.', ['Flame impingement'], ['Visual'])}},
    'electric_furnace': {'summary': ('An electric arc furnace melts steel scrap or direct-reduced iron using electric arcs between three graphite electrodes and the charge. A transformer supplies very high '
                                     'currents; the electrode height is regulated hydraulically to hold the arc. The melt is refined and then tapped.'),
                         'classification': {'family': 'Fired/electric equipment', 'type': 'AC electric arc furnace (EAF)'}, 'model_configuration': {'animation': 'Electrodes regulate, arcs flicker, tapping shown'},
                         'standards': _std(('IEC 60519', 'Safety in electroheating installations', 'Electrical safety.'),), 'references': ['AIST — Making, Shaping and Treating of Steel'],
                         'components': {'ef_shell': _c('Holds the bath.', 'Shell, refractory hearth, water-cooled panels.', 'Steel/refractory.', '—', ['Refractory wear, water leaks'], ['Inspect after each heat']),
                                        'ef_bath': _c('Molten steel and slag.', '—', '—'), 'ef_roof': _c('Closes the furnace; swings for charging.', 'Water-cooled roof with delta.', 'Steel/refractory.'),
                                        'ef_electrodes': _c('Conduct current and form the arcs.', 'Graphite electrodes, clamps, arms.', 'Graphite/copper.', 'Consumed in operation.', ['Breakage, tip oxidation'], ['Monitor consumption']),
                                        'ef_arc': _c('Electric arc (heat source).', '—', '—'), 'ef_mast': _c('Carries and moves the arms.', 'Masts with hydraulic cylinders.', 'Steel.'),
                                        'ef_tilt': _c('Tilt for tapping/deslagging.', 'Rockers and EBT.', 'Steel.'), 'ef_transformer': _c('Supplies arc power.', 'Furnace transformer and bus.', '—')}},
}
BUILDERS = {k: globals()[k] for k in META}
