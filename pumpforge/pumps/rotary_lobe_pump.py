"""
Rotary Lobe Pump — two tri-lobe rotors (cycloidal profile) turn in opposite
directions without touching, synchronised by timing gears in a gearbox behind
the pump chamber.  Liquid is carried from the bottom (inlet) port around the
outside of each rotor to the top (outlet) port.  Hygienic-style front cover.
Shafts along +Y (front cover at -Y), cut plane x = 0.
"""
import math
from pumpforge.core import (Model, lathe, lathe_split, ring_profile, cyl, box, csg, split_keep, join, merge_halves, split_faces,
                            extrude_poly, TAU)
from pumpforge.parts import add_drive_y, nozzle_bolts
from pumpforge.shapes import involute_gear_profile
from pumpforge.common_meta import C

ID = 'rotary_lobe_pump'
CZ = 0.30
BP = 0.09
N = 3
RP = 0.055           # pitch radius -> centre distance 2*RP
RC = RP / (2 * N)
W = 0.07
RS = 0.02


def lobe_profile(phase, steps=14):
    pts = []
    for k in range(2 * N):
        a0 = k * math.pi / N
        for i in range(steps):
            t = math.pi / N * i / steps
            if k % 2 == 0:   # epicycloid (tip)
                x = (RP + RC) * math.cos(t) - RC * math.cos((RP + RC) / RC * t)
                y = (RP + RC) * math.sin(t) - RC * math.sin((RP + RC) / RC * t)
            else:            # hypocycloid (root)
                x = (RP - RC) * math.cos(t) + RC * math.cos((RP - RC) / RC * t)
                y = (RP - RC) * math.sin(t) - RC * math.sin((RP - RC) / RC * t)
            r, a = math.hypot(x, y), math.atan2(y, x) + a0 + phase
            pts.append((r * math.cos(a), r * math.sin(a)))
    return pts


def ks(o):
    return split_keep(o, 'x', 0.0, keep_positive=False)


def build(out_dir):
    m = Model(ID, 'Rotary Lobe Pump (Tri-Lobe, Timing Gears)', 'B · Rotary Positive-Displacement Pumps', META)
    mat = 'stainless'
    rt = RP + 2 * RC
    cx = (-RP, RP)
    # pump chamber (rotor case)
    outs = [extrude_poly('case', [(x, z + CZ) for x, z in _stadium(RP + rt + 0.025, rt + 0.025)], -0.0, W + 0.012, mat, plane='XZ'),
            cyl('pin', 0.04, CZ - 0.2, CZ - rt, mat, 48, center=(0, W / 2, 0)), cyl('pout', 0.04, CZ + rt, CZ + 0.2, mat, 48, center=(0, W / 2, 0)),
            lathe('cl1', [(0.025, CZ - 0.2), (0.06, CZ - 0.2), (0.06, CZ - 0.185), (0.025, CZ - 0.18)], mat, 48, center=(0, W / 2, 0)),
            lathe('cl2', [(0.025, CZ + 0.18), (0.06, CZ + 0.185), (0.06, CZ + 0.2), (0.025, CZ + 0.2)], mat, 48, center=(0, W / 2, 0))]
    ins = [cyl(f'b{i}', rt + 0.0008, -0.01, W, mat, 96, axis='Y', center=(c, 0, CZ)) for i, c in enumerate(cx)]
    ins += [box('mid', (0.06, W + 0.01, 2 * rt), (0, W / 2 - 0.005, CZ), mat),
            cyl('pinb', 0.03, CZ - 0.21, CZ - rt + 0.01, mat, 48, center=(0, W / 2, 0)), cyl('poutb', 0.03, CZ + rt - 0.01, CZ + 0.21, mat, 48, center=(0, W / 2, 0))]
    ins += [cyl(f'sh{i}', RS + 0.002, W - 0.01, W + 0.03, mat, 32, axis='Y', center=(c, 0, CZ)) for i, c in enumerate(cx)]
    case = csg('rotor_case', outs, ins, mat)
    p = m.part('rotor_case', 'Rotor Case (Pump Chamber)', 'casing', section='split', explode=(0, -0.12, 0), info={'ref': 'lobe_case'})
    p.add_split(*ks(case), smooth_angle=40)
    # front cover with wing nuts
    fc = extrude_poly('fcov', [(x, z + CZ) for x, z in _stadium(RP + rt + 0.025, rt + 0.025)], -0.025, 0.0, mat, plane='XZ')
    wn = [cyl(f'wn{i}', 0.012, -0.045, -0.025, 'stainless', 6, axis='Y', center=(x, 0, CZ + z)) for i, (x, z) in
          enumerate(((-RP - rt, 0.06), (-RP - rt, -0.06), (RP + rt, 0.06), (RP + rt, -0.06)))]
    p = m.part('front_cover', 'Front Cover (Quick-Release)', 'casing', section='hide', explode=(0, -0.4, 0), info={'ref': 'lobe_cover'})
    p.add(join('front_cover', [fc] + wn), smooth_angle=40)
    # rotors
    for i, (c, sg, nm) in enumerate(((cx[0], 1, 'Drive'), (cx[1], -1, 'Driven'))):
        prof = lobe_profile(-math.pi / (2 * N))
        lob = extrude_poly(f'lobe{i}', [(x + c, z + CZ) for x, z in prof], 0.001, W - 0.001, 'paint_blue_dark', plane='XZ')
        nut = cyl(f'rn{i}', 0.022, -0.012, 0.001, 'stainless', 6, axis='Y', center=(c, 0, CZ))
        sh = cyl(f'rs{i}', RS, -0.0, W + 0.32 + (0.2 if i == 0 else 0.0), 'steel', 32, axis='Y', center=(c, 0, CZ), ch=0.002)
        p = m.part(f'rotor_{i + 1}', f'{nm} Rotor & Shaft', 'rotating_element', pivot=(c, 0, CZ), explode=(c * 2.5, -0.26, 0),
                   info={'ref': 'lobe_rotor'})
        p.add(join(f'rotor{i}', [lob, nut, sh]), smooth_angle=35); p.spin('Y', sg)
    # gearbox with timing gears
    g0, g1 = W + 0.06, W + 0.30
    gb = csg('gearbox', [extrude_poly('gb', [(x, z + CZ) for x, z in _stadium(RP + 0.07, 0.09)], g0, g1, 'paint_grey', plane='XZ'),
                         box('gbf', (0.36, 0.1, CZ - 0.09 - BP), (0, g1 - 0.08, BP + (CZ - 0.09 - BP) / 2 + 0.006), 'paint_grey', bevel=0.005)],
             [extrude_poly('gbi', [(x, z + CZ) for x, z in _stadium(RP + 0.055, 0.075)], g0 + 0.015, g1 - 0.015, 'paint_grey', plane='XZ')] +
             [cyl(f'gs{i}', RS + 0.002, g0 - 0.01, g1 + 0.01, 'paint_grey', 32, axis='Y', center=(c, 0, CZ)) for i, c in enumerate(cx)], 'paint_grey')
    adapt = [cyl(f'ad{i}', 0.034, W + 0.012, g0, 'paint_grey', 48, axis='Y', center=(c, 0, CZ)) for i, c in enumerate(cx)]
    adapt = [csg(f'ad{i}', [a], [cyl(f'adi{i}', RS + 0.002, W, g0 + 0.01, 'paint_grey', 32, axis='Y', center=(cx[i], 0, CZ))], 'paint_grey')
             for i, a in enumerate(adapt)]
    p = m.part('gearbox', 'Gearbox (Timing Gear Case) & Seal Housings', 'gearbox', section='split', explode=(0, 0.25, 0), info={'ref': 'gearbox'})
    gb_b, gb_f = ks(gb)
    a_b, a_f = ks(adapt[0])
    a2b, a2f = ks(adapt[1])
    p.add_split(join('gbb', [gb_b] + [o for o in (a_b, a2b) if o]), join('gbf_', [o for o in (gb_f, a_f, a2f) if o]), smooth_angle=40)
    gpts, _ = involute_gear_profile(2 * RP / 22, 22, 20.0, steps=6, backlash=0.0005)
    for i, (c, sg) in enumerate(((cx[0], 1), (cx[1], -1))):
        ph = 0.0 if i == 0 else math.pi / 22
        pp = [(x * math.cos(ph) - z * math.sin(ph) + c, z * math.cos(ph) + x * math.sin(ph) + CZ) for x, z in gpts]
        g = extrude_poly(f'tg{i}', pp, g0 + 0.09, g0 + 0.13, 'steel', plane='XZ')
        p = m.part(f'timing_gear_{i + 1}', f'Timing Gear {i + 1}', 'gearbox', pivot=(c, 0, CZ), explode=(c * 3, 0.25, 0.35), info={'ref': 'timing_gear'})
        p.add(g, smooth_angle=30); p.spin('Y', sg)
    brg = merge_halves('brgs', [lathe_split(f'brg{i}{j}', ring_profile(RS, RS + 0.016, y, y + 0.022), 'steel', 32, axis='Y', center=(c, 0, CZ),
                                            phase=math.pi / 2) for i, c in enumerate(cx) for j, y in enumerate((g0 + 0.03, g1 - 0.05))])
    p = m.part('bearings', 'Shaft Bearings (in Gearbox)', 'bearings', section='split', explode=(0, 0.25, -0.25), info={'ref': 'radial_bearing'})
    p.add_split(*brg)
    sl = merge_halves('seals', [lathe_split(f'sl{i}', ring_profile(RS, RS + 0.012, W + 0.014, W + 0.05), 'carbon', 32, axis='Y', center=(c, 0, CZ),
                                            phase=math.pi / 2) for i, c in enumerate(cx)])
    p = m.part('shaft_seals', 'Front-Loading Mechanical Seals', 'mechanical_seal', section='split', explode=(0, 0.1, -0.2), info={'ref': 'mechanical_seal'})
    p.add_split(*sl)
    add_drive_y(m, W + 0.52, CZ, BP, RS, motor_R=0.12, motor_L=0.4, y_base0=-0.15, base_w=0.5, revs=1, x_off=-RP)
    # (drive shaft is the left rotor shaft; coupling is on its axis offset by -RP)
    for prt in m.parts:
        if prt.id in ('coupling', 'coupling_guard') or prt.id.startswith('m_'):
            pass
    yf = -0.004
    for c, sg in ((cx[0], 1), (cx[1], -1)):
        arc = []
        for k in range(19):
            a = math.radians(-90 - sg * 0) + 0
        arc = [(c + (RP + RC) * math.cos(math.radians(a)), yf, CZ + (RP + RC) * math.sin(math.radians(a)))
               for a in (range(-100, -261, -10) if sg > 0 else range(-80, 81, 10))]
        m.flow(f'flow_in{sg}', [(0, yf, CZ - 0.4), (0, yf, CZ - rt - 0.02), (c * 0.6, yf, CZ - rt)] + arc[:9], 'flow_suction', 0.004, 0.06)
        m.flow(f'flow_out{sg}', arc[8:] + [(c * 0.6, yf, CZ + rt), (0, yf, CZ + rt + 0.02), (0, yf, CZ + 0.4)], 'flow_discharge', 0.004, 0.06)
    return m.export(out_dir)


def _stadium(hw, r, n=16):
    pts = []
    for cxx, a0 in ((hw - r, -90), (-hw + r, 90)):
        for i in range(n + 1):
            a = math.radians(a0 + 180 * i / n)
            pts.append((cxx + r * math.cos(a), r * math.sin(a)))
    return pts


META = {
    'summary': ('Two lobed rotors turn in opposite directions inside a close-fitting case. They never touch each other or the '
                'case — timing gears in the gearbox keep them in phase — so the pump is gentle on shear-sensitive and '
                'particle-laden products and can run dry briefly. As the lobes separate at the inlet a void forms and fills; '
                'the liquid is carried around the outside of each rotor and expelled where the lobes re-mesh at the outlet. '
                'Widely used in food, beverage, pharmaceutical and wastewater sludge service; easy to clean in place.'),
    'classification': {'family': 'Positive displacement – rotary', 'configuration': 'Rotary lobe, external timing gears, overhung rotors'},
    'model_configuration': {'lobes': N, 'profile': 'Cycloidal (epicycloid tips / hypocycloid roots), non-contacting',
                            'ports': 'Bottom inlet, top outlet (reversible by changing rotation)', 'seals': 'Front-loading mechanical seals per shaft'},
    'standards': [
        {'id': 'API 676', 'title': 'Positive Displacement Pumps – Rotary', 'relevance': 'Process service.', 'edition': 'to be verified'},
        {'id': 'EHEDG / 3-A Sanitary Standards', 'title': 'Hygienic design', 'relevance': 'Hygienic lobe pumps for food/pharma are certified to these schemes; confirm per model.', 'edition': 'to be verified'},
        {'id': 'ANSI/HI 3.1-3.5', 'title': 'Rotary Pumps', 'relevance': 'Nomenclature and application.', 'edition': 'to be verified'},
    ],
    'references': ['Karassik et al., Pump Handbook — rotary pumps.', 'Manufacturer rotary lobe pump manuals (generic practice).'],
    'components': {
        'lobe_case': C('Pump chamber in which the rotors turn; forms the ports.', 'Machined block with two intersecting bores; front-pull design.', 'Stainless steel (316L), ductile iron.',
                       'Clearances (rotor-to-case, rotor-to-rotor) set slip and allow non-contact running.', ['Clearance growth from abrasion', 'Rotor-case contact if bearings/gears wear'],
                       ['Clearances, rubbing marks']),
        'lobe_cover': C('Front cover giving direct access to rotors and seals for cleaning.', 'Flat cover with quick-release nuts and O-ring.', 'Stainless steel.',
                        'Hygienic cleaning (CIP) requires drainable, crevice-free design.', ['O-ring damage'], ['O-ring condition']),
        'lobe_rotor': C('Displaces liquid; lobes carry pockets of liquid from inlet to outlet.', 'Bi-lobe, tri-lobe or multi-lobe rotors (sometimes elastomer-coated) secured by rotor nut.',
                        'Stainless steel, non-galling alloys, elastomer-covered.', 'Must not touch; timing set by gears.', ['Lobe tip wear', 'Galling if contact occurs'], ['Clearance checks']),
        'gearbox': C('Houses the timing gears and bearings that position the overhung rotors.', 'Oil-filled gear case with seal housings on the pump side.', 'Cast iron, stainless for washdown.',
                     'Oil level/quality per manufacturer.', ['Oil leakage', 'Bearing wear'], ['Oil level and analysis']),
        'timing_gear': C('Synchronise the rotors so they never touch.', 'Pair of helical or spur gears locked to the shafts (taper locking for timing).', 'Hardened alloy steel.',
                         'Run in oil bath.', ['Tooth wear → loss of timing'], ['Backlash and timing check']),
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
