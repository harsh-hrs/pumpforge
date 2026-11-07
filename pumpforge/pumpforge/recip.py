"""Reciprocating power end (crankshaft, connecting rods, crossheads) shared by
piston and plunger pumps.  Crankshaft along +Y, plungers along -X from the
crossheads toward the fluid end; crank turns in the XZ plane."""
import math
from mathutils import Matrix
from .core import (lathe, lathe_split, ring_profile, cyl, box, csg, split, join, merge_halves, split_many, rotate, TAU, OPERATE_FRAMES)
from .common_meta import C


def crosshead_x(xc, r, L, phi):
    return xc + r * math.cos(phi) - math.sqrt(L * L - (r * math.sin(phi)) ** 2)


def power_end(m, ys, cz, xc, r, L, phases, y_cut, mat='paint_blue', revs=1.0, rod_to=None, bp=0.0):
    """Builds crankcase, crankshaft, connecting rods and crossheads (+extension rods to x = rod_to).
    Returns list of per-cylinder (y, phase, x_rest) and helper for crosshead x(t)."""
    y0, y1 = min(ys) - 0.11, max(ys) + 0.11
    xg0 = crosshead_x(xc, r, L, math.pi) - 0.07        # crosshead guide start
    cc_o = [box('cc', (xc + 0.12 - xg0 + 0.02, y1 - y0, 2 * r + 0.24), ((xc + 0.12 + xg0) / 2 + 0.01, (y0 + y1) / 2, cz), mat, bevel=0.02),
            box('ccf', (xc + 0.12 - xg0 + 0.02, y1 - y0 + 0.08, 0.03), ((xc + 0.12 + xg0) / 2 + 0.01, (y0 + y1) / 2, bp + 0.015), mat, bevel=0.004),
            box('ccw', (xc + 0.1 - xg0, y1 - y0 - 0.04, cz - r - 0.12 - bp), ((xc + 0.12 + xg0) / 2 + 0.01, (y0 + y1) / 2, bp + (cz - r - 0.12 - bp) / 2 + 0.02), mat)]
    cc_o += [cyl(f'bb{i}', 0.07, yy - 0.035, yy + 0.035, mat, 48, axis='Y', center=(xc, 0, cz)) for i, yy in enumerate((y0, y1))]
    cc_i = [box('cci', (xc + 0.1 - (xg0 + 0.09), y1 - y0 - 0.04, 2 * r + 0.2), ((xc + 0.1 + xg0 + 0.09) / 2, (y0 + y1) / 2, cz), mat, bevel=0.01)]
    cc_i += [cyl(f'g{i}', 0.042, xg0 - 0.05, xg0 + 0.11, mat, 48, axis='X', center=(0, yy, cz)) for i, yy in enumerate(ys)]
    cc_i += [cyl('cbore', 0.03, y0 - 0.05, y1 + 0.05, mat, 32, axis='Y', center=(xc, 0, cz))]
    cc = csg('crankcase', cc_o, cc_i, mat)
    cb, cf = split(cc, 'y', y_cut)
    p = m.part('crankcase', 'Crankcase (Power Frame) & Crosshead Guides', 'power_end', section='split', explode=(0.35, 0, 0), info={'ref': 'crankcase'})
    p.add_split(cb, cf, smooth_angle=40)
    # crankshaft
    parts = [cyl('cs_main', 0.028, y0 - 0.05, y1 + 0.42, 'steel', 32, axis='Y', center=(xc, 0, cz), ch=0.002)]
    for i, (yy, ph) in enumerate(zip(ys, phases)):
        px, pz = xc + r * math.cos(ph), cz + r * math.sin(ph)
        parts.append(cyl(f'pin{i}', 0.026, yy - 0.03, yy + 0.03, 'steel', 32, axis='Y', center=(px, 0, pz)))
        for s in (-1, 1):
            web = box(f'web{i}{s}', (r + 0.07, 0.018, 0.07), (xc + r / 2, yy + s * 0.04, cz), 'steel', bevel=0.008)
            web = rotate(web, -ph, 'Y', (xc, 0, cz))
            parts.append(web)
    p = m.part('crankshaft', 'Crankshaft', 'power_end', pivot=(xc, 0, cz), explode=(0.35, 0, 0.45), info={'ref': 'crankshaft'})
    p.add(join('crankshaft', parts), smooth_angle=40); p.spin('Y', -revs)
    out = []
    for i, (yy, ph) in enumerate(zip(ys, phases)):
        x0 = crosshead_x(xc, r, L, ph)
        beta0 = math.atan2(r * math.sin(ph), xc + r * math.cos(ph) - x0)
        rod = join(f'conrod{i}', [box(f'cr{i}', (L - 0.06, 0.022, 0.03), (x0 + L / 2, yy, cz), 'steel', bevel=0.006),
                                  cyl(f'ce{i}', 0.042, yy - 0.025, yy + 0.025, 'steel', 32, axis='Y', center=(x0 + L, 0, cz)),
                                  cyl(f'cs{i}', 0.025, yy - 0.02, yy + 0.02, 'steel', 24, axis='Y', center=(x0, 0, cz))])
        rod = rotate(rod, -beta0, 'Y', (x0, 0, cz))
        p = m.part(f'conrod_{i + 1}', f'Connecting Rod {i + 1}', 'power_end', pivot=(x0, yy, cz), explode=(0.35, 0, 0.3 + 0.05 * i), info={'ref': 'conrod'})
        rm = p.add(rod, smooth_angle=40)
        ch = join(f'xh{i}', [cyl(f'xhc{i}', 0.04, x0 - 0.06, x0 + 0.03, 'steel_dark', 48, axis='X', center=(0, yy, cz)),
                             cyl(f'xhr{i}', 0.016, (rod_to or x0 - 0.2), x0 - 0.05, 'steel', 24, axis='X', center=(0, yy, cz))])
        p2 = m.part(f'crosshead_{i + 1}', f'Crosshead & Extension Rod {i + 1}', 'power_end', pivot=(x0, yy, cz), explode=(0.2, 0, -0.25 - 0.05 * i),
                    info={'ref': 'crosshead'})
        xm = p2.add(ch, smooth_angle=40)
        rk, lk, xk = [], [], []
        for f in range(OPERATE_FRAMES + 1):
            th = TAU * revs * f / OPERATE_FRAMES
            phi = ph + th
            xx = crosshead_x(xc, r, L, phi)
            beta = math.atan2(r * math.sin(phi), xc + r * math.cos(phi) - xx)
            rk.append((1 + f, (0.0, -(beta - beta0), 0.0)))
            lk.append((1 + f, (xx - x0, 0.0, 0.0)))
        m.keyframes(rm, 'Operate', 'rotation_euler', rk)
        m.keyframes(rm, 'Operate', 'location', lk)
        m.keyframes(xm, 'Operate', 'location', lk)
        out.append(dict(y=yy, phase=ph, x0=x0, lk=lk))
    # bearings
    br = merge_halves('main_brg', [split(lathe(f'mb{i}', ring_profile(0.028, 0.06, yy - 0.025, yy + 0.025), 'steel', 48, axis='Y', center=(xc, 0, cz)), 'y', y_cut)
                                   for i, yy in enumerate((y0, y1))])
    p = m.part('main_bearings', 'Crankshaft Main Bearings', 'bearings', section='split', explode=(0.35, 0, 0.6), info={'ref': 'radial_bearing'})
    p.add_split(*br)
    return out, dict(y0=y0, y1=y1, xg0=xg0)


def motion_keys(lk, sel):
    """Valve lift keys from plunger motion: sel='suction' lifts while moving +X, 'discharge' while moving -X."""
    keys = []
    n = len(lk)
    for k in range(n):
        a = lk[max(0, k - 1)][1][0]
        b = lk[min(n - 1, k + 1)][1][0]
        v = b - a
        up = (v > 1e-5) if sel == 'suction' else (v < -1e-5)
        keys.append((lk[k][0], 1.0 if up else 0.0))
    return keys


RECIP_META = {
    'crankcase': C('Rigid frame that carries the crankshaft bearings and crosshead guides and contains the lubricating oil.', 'Cast or fabricated frame with oil sump, crosshead guide bores and covers.',
                   'Cast iron, ductile iron, fabricated steel.', 'Rod load rating limits pressure × plunger area.', ['Oil contamination', 'Guide wear'], ['Oil level/quality', 'Crosshead clearance']),
    'crankshaft': C('Converts rotary motion into reciprocating motion of the plungers/pistons.', 'Forged or cast shaft with throws at equal angles (120° for triplex, 90°/180° for duplex).',
                    'Forged alloy steel, ductile iron.', 'Torque fluctuates with pumping cycle.', ['Bearing journal wear', 'Fatigue'], ['Bearing clearances']),
    'conrod': C('Links crankpin to crosshead.', 'Rod with split big-end bearing and wrist-pin bushing.', 'Steel, ductile iron; babbitt/bronze bearings.', 'Alternating tension/compression.',
                ['Big-end bearing wear', 'Wrist pin wear'], ['Knock/noise, oil analysis']),
    'crosshead': C('Guides the reciprocating motion in a straight line so the plunger/piston rod carries no side load; extension (pony) rod passes into the distance piece.',
                   'Cylindrical crosshead sliding in a guide; extension rod with oil wiper.', 'Cast iron/steel crosshead, steel rod.', 'Lubricated by crankcase oil.',
                   ['Guide scuffing', 'Wiper leakage'], ['Clearance, wiper condition']),
}
