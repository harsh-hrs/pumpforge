"""
Twin Screw Pump — timed, double-flow (double-suction) design: two rotors each
carry a left-hand and a right-hand screw section; liquid enters at both ends and
is conveyed toward the centre discharge, so axial thrust balances.  External
timing gears keep the screws from touching; bearings outside the liquid.
Handles viscous, non-lubricating and multiphase liquids.  Axis Y, cut x = 0.
"""
import math
from pumpforge.core import (Model, lathe, lathe_split, ring_profile, cyl, box, csg, split_keep, join, merge_halves, split_faces, TAU)
from pumpforge.parts import add_drive_y, nozzle_bolts
from pumpforge.shapes import twisted_extrude, lobed_profile, involute_gear_profile
from pumpforge.core import extrude_poly
from pumpforge.common_meta import C

ID = 'twin_screw_pump'
CZ = 0.34
BP = 0.09
RO, RI = 0.06, 0.034
A = RO + RI + 0.0015
LEAD = 0.11
Y0, YM, Y1 = 0.06, 0.32, 0.58
RS = 0.024


def ks(o):
    return split_keep(o, 'x', 0.0, keep_positive=False)


def build(out_dir):
    m = Model(ID, 'Twin Screw Pump (Timed, Double-Flow)', 'B · Rotary Positive-Displacement Pumps', META)
    mat = 'paint_blue_dark'
    xs = (-A / 2, A / 2)
    hw, hh = A / 2 + RO + 0.03, RO + 0.03
    outs = [box('hb', (2 * hw, Y1 + 0.06, 2 * hh + 0.07), (0, Y1 / 2 + 0.0, CZ - 0.035), mat, bevel=0.02),
            cyl('din', 0.06, CZ, CZ + hh + 0.12, mat, 48, center=(0, YM, 0)), cyl('dfl', 0.1, CZ + hh + 0.1, CZ + hh + 0.12, mat, 48, center=(0, YM, 0), ch=0.003),
            cyl('sin', 0.06, CZ - hh - 0.2, CZ - hh, mat, 48, center=(0, YM, 0)), cyl('sfl', 0.1, CZ - hh - 0.2, CZ - hh - 0.18, mat, 48, center=(0, YM, 0), ch=0.003),
            box('ft1', (2 * hw, 0.12, CZ - hh - 0.07 - BP), (0, 0.08, BP + (CZ - hh - 0.07 - BP) / 2 + 0.006), mat, bevel=0.004),
            box('ft2', (2 * hw, 0.12, CZ - hh - 0.07 - BP), (0, Y1 - 0.08, BP + (CZ - hh - 0.07 - BP) / 2 + 0.006), mat, bevel=0.004)]
    ins = [cyl(f'b{i}', RO + 0.0007, Y0 - 0.03, Y1 + 0.03, mat, 96, axis='Y', center=(x, 0, CZ)) for i, x in enumerate(xs)]
    ins += [box('ec1', (2 * hw - 0.04, 0.05, 2 * RO + 0.02), (0, 0.025 - 0.005, CZ), mat), box('ec2', (2 * hw - 0.04, 0.05, 2 * RO + 0.02), (0, Y1 + 0.005, CZ), mat),
            box('chan', (2 * hw - 0.06, Y1 + 0.02, 0.045), (0, Y1 / 2, CZ - RO - 0.04), mat, bevel=0.01),
            box('ecl1', (2 * hw - 0.06, 0.05, 0.08), (0, 0.02, CZ - RO - 0.01), mat), box('ecl2', (2 * hw - 0.06, 0.05, 0.08), (0, Y1, CZ - RO - 0.01), mat),
            box('mid', (2 * hw - 0.04, 2 * (YM - 0.3) + 0.05, RO * 2 - 0.004), (0, YM, CZ + 0.0), mat),
            cyl('dib', 0.045, CZ + 0.02, CZ + hh + 0.13, mat, 48, center=(0, YM, 0)), cyl('sib', 0.045, CZ - hh - 0.21, CZ - RO - 0.03, mat, 48, center=(0, YM, 0))]
    ins += [cyl(f'sh{i}{j}', RS + 0.002, yy - 0.05, yy + 0.05, mat, 32, axis='Y', center=(x, 0, CZ)) for i, x in enumerate(xs) for j, yy in enumerate((-0.0, Y1 + 0.06))]
    body = csg('casing', outs, ins, mat)
    p = m.part('casing', 'Pump Casing (Double-Flow)', 'casing', section='split', explode=(0, 0.1, -0.35), info={'ref': 'pd_casing'})
    p.add_split(*ks(body), smooth_angle=40)
    # rotors
    prof = lobed_profile(RI, RO, 1, n=96, land=0.5, sharp=3.5)
    for i, (x, sg) in enumerate(((xs[0], 1), (xs[1], -1))):
        s1 = twisted_extrude(f'r{i}a', prof, Y0, YM - 0.025, LEAD, 'stainless', axis='Y', center=(x, 0, CZ), hand=sg)
        s2 = twisted_extrude(f'r{i}b', prof, YM + 0.025, Y1, LEAD, 'stainless', axis='Y', center=(x, 0, CZ), hand=-sg)
        hub = cyl(f'rh{i}', RI, YM - 0.03, YM + 0.03, 'stainless', 48, axis='Y', center=(x, 0, CZ))
        sh = cyl(f'rs{i}', RS, -0.14, Y1 + 0.3 + (0.2 if i == 0 else 0), 'steel', 32, axis='Y', center=(x, 0, CZ), ch=0.002)
        p = m.part(f'rotor_{i + 1}', f'{"Drive" if i == 0 else "Driven"} Screw Rotor', 'rotating_element', pivot=(x, 0, CZ),
                   explode=(x * 4, -0.5, 0), info={'ref': 'twin_rotor'})
        p.add(join(f'rotor{i}', [s1, s2, hub, sh]), smooth_angle=50); p.spin('Y', sg)
    # front bearing housings (cover) — hidden in cutaway
    fb = [box('fcov', (2 * hw, 0.03, 2 * hh), (0, -0.015 - 0.0, CZ - 0.0), mat, bevel=0.01)] + \
         [cyl(f'fbh{i}', 0.05, -0.13, -0.03, mat, 48, axis='Y', center=(x, 0, CZ), ch=0.004) for i, x in enumerate(xs)]
    p = m.part('front_bearing_housing', 'Front Cover & Bearing Housings', 'bearing_housing', section='hide', explode=(0, -0.6, 0), info={'ref': 'twin_bearings'})
    p.add(join('front_bh', fb), smooth_angle=40)
    # rear gearbox with timing gears
    g0, g1 = Y1 + 0.06, Y1 + 0.24
    gb = csg('gearbox', [box('gb', (2 * hw, g1 - g0, 2 * hh), (0, (g0 + g1) / 2, CZ), 'paint_grey', bevel=0.015)],
             [box('gbi', (2 * hw - 0.03, g1 - g0 - 0.03, 2 * hh - 0.03), (0, (g0 + g1) / 2, CZ), 'paint_grey', bevel=0.01)] +
             [cyl(f'gs{i}', RS + 0.002, g0 - 0.01, g1 + 0.01, 'paint_grey', 32, axis='Y', center=(x, 0, CZ)) for i, x in enumerate(xs)], 'paint_grey')
    p = m.part('gearbox', 'Timing Gearbox & Rear Bearings', 'gearbox', section='split', explode=(0, 0.35, 0), info={'ref': 'gearbox'})
    p.add_split(*ks(gb), smooth_angle=40)
    gp, _ = involute_gear_profile(A / 24, 24, 20.0, steps=6, backlash=0.0006)
    for i, (x, sg) in enumerate(((xs[0], 1), (xs[1], -1))):
        ph = 0.0 if i == 0 else math.pi / 24
        pp = [(u * math.cos(ph) - v * math.sin(ph) + x, v * math.cos(ph) + u * math.sin(ph) + CZ) for u, v in gp]
        p = m.part(f'timing_gear_{i + 1}', f'Timing Gear {i + 1}', 'gearbox', pivot=(x, 0, CZ), explode=(x * 4, 0.35, 0.4), info={'ref': 'timing_gear'})
        p.add(extrude_poly(f'tg{i}', pp, g0 + 0.07, g0 + 0.11, 'steel', plane='XZ'), smooth_angle=30); p.spin('Y', sg)
    add_drive_y(m, Y1 + 0.5, CZ, BP, RS, motor_R=0.14, motor_L=0.45, y_base0=-0.25, base_w=0.6, revs=1, x_off=xs[0])

    for sgy, y_end in ((1, Y0), (-1, Y1)):
        helix = [(xs[0] + RO * 0.8 * math.cos(TAU * k / 10), y_end + sgy * (YM - Y0 - 0.03) * k / 30, CZ + RO * 0.8 * math.sin(TAU * k / 10)) for k in range(31)]
        m.flow(f'flow_in{sgy}', [(0, YM, CZ - 0.55), (0, YM, CZ - RO - 0.04), (0, y_end - sgy * 0.03, CZ - RO - 0.04), (xs[0], y_end - sgy * 0.03, CZ)],
               'flow_suction', 0.006, 0.1)
        m.flow(f'flow_conv{sgy}', helix[::2] + [(0, YM, CZ + 0.03), (0, YM, CZ + 0.5)], 'flow_discharge', 0.005, 0.1)
    return m.export(out_dir)


META = {
    'summary': ('Two parallel screws with intermeshing threads turn in opposite directions inside a figure-8 housing. External '
                'timing gears drive the second screw, so the threads never touch and can handle non-lubricating, viscous, '
                'abrasive or gas-laden liquids. In the double-flow arrangement shown, each screw has a left- and a '
                'right-handed section: liquid enters at both ends and is conveyed toward the centre outlet, balancing axial '
                'thrust. Used for crude oil, bitumen, multiphase production fluids, polymers and food products.'),
    'classification': {'family': 'Positive displacement – rotary', 'configuration': 'Twin screw, timed, double-suction (double-flow), bearings external'},
    'model_configuration': {'thread': 'Single-start, square-like land (representative)', 'lead_mm': LEAD * 1000, 'timing': 'Spur timing gears in rear gearbox'},
    'standards': [
        {'id': 'API 676', 'title': 'Positive Displacement Pumps – Rotary', 'relevance': 'Twin screw pumps in process service.', 'edition': 'to be verified'},
        {'id': 'ANSI/HI 3.1-3.5', 'title': 'Rotary Pumps', 'relevance': 'Nomenclature and application.', 'edition': 'to be verified'},
    ],
    'references': ['Karassik et al., Pump Handbook — screw pumps.', 'Manufacturer twin screw pump literature (generic practice).'],
    'components': {
        'twin_rotor': C('Conveys liquid axially in the chambers formed between intermeshing threads and the housing.', 'Shaft with integral or shrunk-on screw sections (LH + RH for double-flow).',
                        'Carbon/alloy steel, stainless, duplex; hard-coated for abrasives.', 'Clearances set slip; thermal growth must be considered for hot liquids.',
                        ['Thread wear', 'Contact if timing or bearings fail'], ['Clearances', 'Timing']),
        'twin_bearings': C('Locate the rotors radially and axially, outside the pumped liquid.', 'Rolling bearings in external housings with their own lubrication.', 'Bearing steel.',
                           'Isolated from liquid by shaft seals (4 seals on double-flow pumps).', ['Lubrication failure'], ['Temperature, vibration']),
        'gearbox': C('Holds the timing gears and bearings.', 'Oil-filled gear case.', 'Cast iron/steel.', 'Oil level per manufacturer.', ['Oil leakage'], ['Oil level, analysis']),
        'timing_gear': C('Keep the screws in phase so they never touch.', 'Hardened spur or helical gears locked to the shafts.', 'Alloy steel.', 'Oil bath.', ['Wear → loss of timing'], ['Backlash check']),
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
