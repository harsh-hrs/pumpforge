"""Horizontally split-case, double-suction, between-bearings pump (API 610 BB1 style).
Shaft along +X, centred at x = 0; casing split on the horizontal plane through the
shaft: the UPPER casing half is the part hidden in cutaway (role 'hide').
Suction nozzle -Y, discharge nozzle +Y, both in the lower half."""
import math
from mathutils import Matrix, Vector
from .core import (lathe, lathe_split, ring_profile, cyl, box, csg, split, join, merge_halves, split_many, rotate, TAU)
from .parts import radial_impeller, place, frame_matrix, ball_bearing, seal_cartridge, add_impeller, nozzle_bolts
from .shapes import sweep_tube
from .common_meta import C


def split_case_pump(m, cz, scale=1.0, mat='paint_red', foot_z=0.0, revs=2):
    s = scale
    d2, b2, r_eye, rs = 0.34 * s, 0.05 * s, 0.075 * s, 0.032 * s
    Mx = frame_matrix((-(0.55 * r_eye + b2 / 2), 0, cz), (1, 0, 0), (0, 0, 1))   # impeller mid-plane at x = 0
    core, shroud, imp = radial_impeller('impeller', d2, b2, r_eye, rs, n_blades=6, mat='bronze', wrap=1.6, double_suction=True)
    r2 = imp['r2']
    r3 = 1.06 * r2
    t = 0.018 * s
    # spiral volute in the YZ plane around the X axis, ending at the bottom heading +Y
    a_min, a_max = 0.012 * s, 0.075 * s
    path, rad = [], []
    th0 = -math.pi / 2 + 0.5
    for i in range(41):
        th = th0 + (2 * math.pi - 0.5) * i / 40
        a = a_min + (a_max - a_min) * i / 40
        R = r3 + 0.8 * a
        path.append((0.0, R * math.cos(th), cz + R * math.sin(th)))
        rad.append(a)
    yend, zend = path[-1][1], path[-1][2]
    L_d = 0.42 * s
    for k in range(1, 7):
        path.append((0.0, yend + L_d * k / 6, zend))
        rad.append(a_max + (0.1 * s - a_max) * min(1, k / 3))
    vo = sweep_tube('vol_o', path, [r + t for r in rad], mat, 32)
    vi = sweep_tube('vol_i', path + [(0.0, yend + L_d + 0.03, zend)], rad + [0.1 * s], mat, 32)
    # suction: nozzle from -Y at zend level -> chamber under shaft -> annular chambers both sides of impeller
    xs_ = 0.11 * s
    body = lathe('body', [(0, -0.3 * s), (0.17 * s, -0.3 * s), (r3 + a_min + t, -0.08 * s), (r3 + a_min + t, 0.08 * s), (0.17 * s, 0.3 * s), (0, 0.3 * s)],
                 mat, 96, axis='X', center=(0, 0, cz))
    sbox = box('sbox', (0.5 * s, 0.34 * s, 0.32 * s), (0, -0.05 * s, cz - 0.12 * s), mat, bevel=0.02 * s)
    snoz = cyl('snoz', 0.11 * s + t, -0.62 * s, -0.1 * s, mat, 64, axis='Y', center=(0, 0, zend))
    sfl = cyl('sfl', 0.19 * s, -0.62 * s, -0.59 * s, mat, 64, axis='Y', center=(0, 0, zend), ch=0.004)
    dfl = cyl('dfl', 0.18 * s, yend + L_d - 0.03 * s, yend + L_d, mat, 64, axis='Y', center=(0, 0, zend), ch=0.004)
    feet = [box(f'ft{i}', (0.12 * s, 0.6 * s, 0.04 * s), (sx * 0.28 * s, 0, cz - 0.02 * s), mat, bevel=0.004) for i, sx in enumerate((1, -1))]
    pads = [box(f'pd{i}', (0.12 * s, 0.14 * s, cz - foot_z - 0.04 * s), (sx * 0.28 * s, sy * 0.24 * s, foot_z + (cz - foot_z - 0.04 * s) / 2), mat)
            for i, (sx, sy) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1)))]
    outs = [body, vo, sbox, snoz, sfl, dfl] + feet + pads
    ins = [vi, lathe('imp_ch', [(0, -0.05 * s), (r3, -0.05 * s), (r3, 0.05 * s), (0, 0.05 * s)], mat, 96, axis='X', center=(0, 0, cz)),
           cyl('sni', 0.1 * s, -0.66 * s, -0.12 * s, mat, 64, axis='Y', center=(0, 0, zend)),
           box('sch', (0.4 * s, 0.26 * s, 0.2 * s), (0, -0.06 * s, cz - 0.15 * s), mat, bevel=0.03 * s)]
    for sx in (1, -1):
        ins.append(lathe(f'sann{sx}', [(rs * 1.5, sx * 0.045 * s), (0.15 * s, sx * 0.07 * s), (0.15 * s, sx * 0.2 * s), (rs * 1.5, sx * 0.2 * s)], mat, 64, axis='X',
                         center=(0, 0, cz)))
        ins.append(box(f'slink{sx}', (0.12 * s, 0.12 * s, 0.2 * s), (sx * 0.13 * s, -0.04 * s, cz - 0.12 * s), mat))
    ins.append(cyl('shb', rs + 0.004, -0.5 * s, 0.5 * s, mat, 32, axis='X', center=(0, 0, cz)))
    cas = csg('casing', outs, ins, mat)
    upper, lower = split(cas, 'z', cz)
    return dict(upper=upper, lower=lower, core=core, shroud=shroud, Mx=Mx, imp=imp, rs=rs, zend=zend, yend=yend + L_d, path=path)


def add_split_case(m, cz, scale=1.0, mat='paint_red', foot_z=0.0, revs=2, bearing_span=0.62):
    s = scale
    g = split_case_pump(m, cz, scale, mat, foot_z, revs)
    lb, lf = split(g['lower'], 'y', 0.0)
    p = m.part('lower_casing', 'Lower Casing Half (with Nozzles & Feet)', 'casing', section='split', explode=(0, 0, -0.2 * s), info={'ref': 'sc_lower'})
    p.add_split(lb, lf, smooth_angle=40)
    up = g['upper']
    bolts = []
    for sx in (-0.22, -0.11, 0.11, 0.22):
        for sy in (-1, 1):
            bolts.append(cyl('ub', 0.012 * s, cz, cz + 0.03 * s, 'steel_dark', 6, center=(sx * s, sy * 0.21 * s, 0)))
    eye = lathe('eye', [(0, 0.0), (0.02 * s, 0.0), (0.02 * s, 0.04 * s), (0, 0.04 * s)], 'steel', 24, center=(0, 0, cz + 0.3 * s))
    p = m.part('upper_casing', 'Upper Casing Half (Removable)', 'casing', section='hide', explode=(0, 0, 0.55 * s), info={'ref': 'sc_upper'})
    p.add(join('upper_casing', [up, eye] + bolts), smooth_angle=40)
    add_impeller(m, 'impeller', 'Double-Suction Impeller', g['core'], g['shroud'], g['Mx'], (0, 0, cz), axis='X', explode=(0, 0, 0.32 * s),
                 ref='impeller_ds', revs=revs, split_axis='y')
    rs = g['rs']
    sh = cyl('shaft', rs, -bearing_span - 0.1 * s, bearing_span + 0.25 * s, 'steel', 32, axis='X', center=(0, 0, cz), ch=0.002)
    slv = [cyl(f'sl{k}', rs + 0.006 * s, k * 0.09 * s, k * 0.3 * s, 'stainless', 32, axis='X', center=(0, 0, cz)) for k in (-1, 1)]
    p = m.part('shaft', 'Shaft & Sleeves', 'rotating_element', pivot=(0, 0, cz), explode=(0, -0.55 * s, 0.2 * s), info={'ref': 'pump_shaft'})
    p.add(join('shaft', [sh] + slv), smooth_angle=40); p.spin('X', revs)
    for side, sx in (('inboard', 1), ('outboard', -1)):
        x0 = sx * 0.3 * s
        sb, sf = seal_cartridge(f'seal_{side}', min(x0, x0 + sx * 0.07 * s), max(x0, x0 + sx * 0.07 * s), rs, rs * 2.0, axis='X', center=(0, 0, cz))
        p = m.part(f'seal_{side}', f'Mechanical Seal – {side.title()}', 'mechanical_seal', section='split', explode=(sx * 0.2 * s, -0.3 * s, 0), info={'ref': 'mechanical_seal'})
        p.add_split(sb, sf)
        xb = sx * bearing_span
        bh = csg(f'bh_{side}', [lathe(f'bho{side}', [(0, -0.09 * s), (0.11 * s, -0.09 * s), (0.11 * s, 0.09 * s), (0, 0.09 * s)], mat, 64, axis='X', center=(xb, 0, cz)),
                                box(f'bhb{side}', (0.14 * s, 0.2 * s, 0.08 * s), (xb + sx * 0.0, 0, cz - 0.1 * s), mat, bevel=0.006),
                                box(f'bhs{side}', (0.08 * s, 0.1 * s, abs(xb) - 0.32 * s), (xb - sx * (abs(xb) - 0.32 * s) / 2 - sx * 0.04 * s, 0, cz - 0.09 * s), mat)],
                 [cyl(f'bhi{side}', rs * 2.3, -0.08 * s + xb, 0.08 * s + xb, mat, 48, axis='X', center=(0, 0, cz)),
                  cyl(f'bhs2{side}', rs + 0.003, xb - 0.12 * s, xb + 0.12 * s, mat, 32, axis='X', center=(0, 0, cz))], mat)
        p = m.part(f'bearing_housing_{side}', f'Bearing Housing – {side.title()}', 'bearing_housing', section='split', explode=(sx * 0.35 * s, 0, 0), info={'ref': 'bearing_frame'})
        p.add_split(*split(bh, 'y', 0.0), smooth_angle=40)
        br = ball_bearing(f'brg{side}', rs, rs * 2.25, xb - 0.03 * s, xb + 0.03 * s, 10, center=(0, 0, cz))
        p = m.part(f'bearing_{side}', f'{"Thrust" if sx < 0 else "Radial"} Bearing – {side.title()}', 'bearings', section='split', explode=(sx * 0.35 * s, -0.4 * s, 0),
                   info={'ref': 'thrust_bearing' if sx < 0 else 'radial_bearing'})
        p.add_split(*br)
    return g


SPLITCASE_META = {
    'sc_lower': C('Lower half of the axially split casing: carries the suction and discharge nozzles, feet and bearing brackets, so the rotor can be removed without disturbing the piping.',
                  'Cast volute (often double volute) with suction passages feeding both impeller eyes; machined horizontal split flange.',
                  'Cast iron, ductile iron, cast steel, bronze, duplex.', 'Pipe loads act on this half; alignment depends on its rigidity.',
                  ['Erosion of volute/cutwater', 'Split-joint leakage'], ['Wear-ring clearances', 'Split gasket']),
    'sc_upper': C('Removable top half of the casing; lifting it exposes the complete rotor for inspection.', 'Cast cover bolted on the horizontal split joint with a gasket; lifting eye.',
                  'As lower half.', 'Contains full pump pressure.', ['Gasket blow-out from uneven bolting'], ['Bolt torque sequence']),
    'impeller_ds': C('Double-suction impeller: liquid enters from both sides, halving eye velocity (lower NPSHr) and balancing axial thrust.', 'Back-to-back enclosed impeller with two eyes and wear rings on both sides.',
                     'Bronze, cast iron, stainless, duplex.', 'Asymmetric suction piping can unbalance flow to the two eyes.', ['Cavitation at eyes', 'Wear-ring wear'], ['Clearances, inlet edges']),
}
