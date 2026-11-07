"""
Vertical Sump / Cantilever Pump — vertical pump hung from a sump cover plate
with NO submerged bearings: a stiff cantilevered shaft carries an overhung
open impeller in a volute at the bottom; both bearings sit above the plate.
Discharge rises through a separate pipe.  Can run dry without bearing damage.
Axis Z, mounting plate top at z = 0.
"""
import math
from pumpforge.core import Model, lathe, lathe_split, ring_profile, cyl, box, csg, split, join, merge_halves, split_faces, split_many, TAU
from pumpforge.parts import V_FRAME, place, radial_impeller, volute_casing, add_impeller, ball_bearing, add_motor_v, pipe, nozzle_bolts
from pumpforge.common_meta import C

ID = 'vertical_sump_cantilever_pump'
ZE = -1.15


def build(out_dir):
    m = Model(ID, 'Vertical Sump / Cantilever Pump (No Submerged Bearings)', 'A · Centrifugal & Special Hydraulic Pumps', META)
    Mx = V_FRAME(ZE)
    core, shroud, imp = radial_impeller('impeller', 0.22, 0.03, 0.05, 0.024, n_blades=4, mat='stainless', closed=False, wrap=1.5)
    cas, geo = volute_casing('volute', imp, 'paint_blue', r_suc=0.06, L_suc=0.09, r_dis=0.045, H_dis=0.13, flange=False)
    place(cas, Mx)
    zb = ZE + geo['z_back']
    xn, yn, zd = geo['H_dis'], -geo['Rend'], ZE + imp['zc']
    cas = csg('casing', [cas, cyl('dfl', 0.1, xn - 0.02, xn, 'paint_blue', 48, axis='X', center=(0, yn, zd))], [], 'paint_blue')
    cb, cf = split(cas)
    p = m.part('volute_casing', 'Volute Casing (Submerged)', 'casing', section='split', explode=(0, 0, -0.35), info={'ref': 'volute_casing'})
    p.add_split(cb, cf, smooth_angle=40)
    add_impeller(m, 'impeller', 'Semi-Open Impeller', core, shroud, Mx, (0, 0, ZE), axis='Z', explode=(0, 0, -0.18), ref='impeller_open')
    # casing cover + support column (stiff tube) to the plate
    cov = lathe('cover', [(0.03, zb), (geo['r_bf'], zb), (geo['r_bf'], zb + 0.02), (0.1, zb + 0.04), (0.1, zb + 0.07), (0.03, zb + 0.07)],
                'paint_blue', 96)
    col = lathe('col', [(0.07, zb + 0.06), (0.085, zb + 0.06), (0.085, -0.03), (0.07, -0.03)], 'paint_blue', 64)
    fl = lathe('colfl', [(0.07, zb + 0.06), (0.14, zb + 0.06), (0.14, zb + 0.085), (0.085, zb + 0.09), (0.07, zb + 0.09)], 'paint_blue', 64)
    p = m.part('support_column', 'Casing Cover & Support Column', 'column', section='split', explode=(-0.45, 0, -0.1), info={'ref': 'support_column'})
    p.add_split(*split_many('support_column', [cov, col, fl]))
    # discharge pipe
    dp_o = pipe('dpo', [(xn, yn, zd), (xn + 0.16, yn, zd), (xn + 0.16, yn, 0.35), (xn + 0.4, yn, 0.35)], 0.06, 'paint_blue', 40, bend=0.12)
    dp_i = pipe('dpi', [(xn - 0.01, yn, zd), (xn + 0.16, yn, zd), (xn + 0.16, yn, 0.35), (xn + 0.41, yn, 0.35)], 0.05, 'paint_blue', 40, bend=0.12)
    dpf = [cyl('dpf1', 0.1, xn, xn + 0.02, 'paint_blue', 48, axis='X', center=(0, yn, zd)),
           cyl('dpf2', 0.11, xn + 0.38, xn + 0.4, 'paint_blue', 48, axis='X', center=(0, yn, 0.35))]
    dp = csg('discharge_pipe', [dp_o] + dpf, [dp_i], 'paint_blue')
    p = m.part('discharge_pipe', 'Discharge Pipe', 'system_piping', section='split', explode=(0.4, 0, 0), info={'ref': 'pipework'})
    p.add_split(*split_many('discharge_pipe', [dp], 'y', yn))
    # sump cover (mounting) plate
    plate = box('plate', (1.0, 0.8, 0.03), (0.1, 0, -0.015), 'paint_grey', bevel=0.004)
    plate = csg('plate', [plate], [cyl('ph1', 0.09, -0.05, 0.02, 'paint_grey', 48), cyl('ph2', 0.065, -0.05, 0.02, 'paint_grey', 48, center=(xn + 0.16, yn, 0))],
                'paint_grey')
    p = m.part('mounting_plate', 'Sump Cover / Mounting Plate', 'baseplate', section='split', explode=(0, 0, 0.0), info={'ref': 'mounting_plate'})
    p.add_split(*split(plate), smooth_angle=40)
    # bearing housing above plate
    bh = lathe('bh', [(0.03, 0.0), (0.16, 0.0), (0.16, 0.025), (0.09, 0.04), (0.09, 0.32), (0.12, 0.34), (0.12, 0.36), (0.03, 0.36),
                      (0.03, 0.34), (0.075, 0.32), (0.075, 0.04), (0.03, 0.03)], 'paint_blue', 96)
    p = m.part('bearing_housing', 'Bearing Housing (Above Plate)', 'bearing_housing', section='split', explode=(0, 0, 0.35), info={'ref': 'bearing_frame'})
    p.add_split(*split(bh), smooth_angle=40)
    br = merge_halves('brg', [ball_bearing('b1', 0.024, 0.075, 0.04, 0.075, 12, axis='Z'),
                              ball_bearing('b2', 0.024, 0.075, 0.27, 0.3, 12, axis='Z'), ball_bearing('b3', 0.024, 0.075, 0.24, 0.27, 12, axis='Z')])
    p = m.part('bearings', 'Bearings (Radial Lower, Duplex Thrust Upper)', 'bearings', section='split', explode=(-0.45, 0, 0.35), info={'ref': 'thrust_bearing'})
    p.add_split(*br)
    sh = cyl('shaft', 0.024, ZE + imp['z_back'] - 0.03, 0.46, 'stainless', 32, ch=0.002)
    p = m.part('pump_shaft', 'Cantilever Shaft (Large Diameter)', 'rotating_element', explode=(0.5, 0, 0), info={'ref': 'cantilever_shaft'})
    p.add(sh); p.spin('Z', 2)
    cp = lathe('cp', [(0.024, 0.38), (0.06, 0.38), (0.06, 0.41), (0.035, 0.415), (0.035, 0.435), (0.06, 0.44), (0.06, 0.47), (0.024, 0.47)], 'steel', 48)
    st = csg('stand', [lathe('st', [(0, 0.36), (0.12, 0.36), (0.12, 0.38), (0.12, 0.52), (0.18, 0.53), (0.18, 0.55), (0, 0.55)], 'paint_blue', 96)],
             [cyl('sti', 0.105, 0.37, 0.56, 'paint_blue', 96), box('stw', (0.1, 0.4, 0.12), (0, 0, 0.445), 'paint_blue', bevel=0.015)], 'paint_blue')
    p = m.part('motor_stand', 'Motor Stand', 'bearing_housing', section='split', explode=(0, 0, 0.5), info={'ref': 'motor_stand_c'})
    p.add_split(*split(st), smooth_angle=40)
    p = m.part('coupling', 'Flexible Coupling', 'power_transmission', pivot=(0, 0, 0.42), explode=(0.5, 0, 0.5), info={'ref': 'coupling_flex'})
    p.add(cp); p.spin('Z', 2)
    add_motor_v(m, 'm_', 0.575, 0.15, 0.42, 0.024, 0.575 - 0.44, explode_dz=0.75, flange_r=0.18)

    m.flow('flow_suction', [(0, 0, ZE - 0.45), (0, 0, ZE - 0.1), (0, 0, ZE + 0.01)], 'flow_suction', 0.007, 0.12)
    spiral = []
    for i in range(25):
        th = math.pi / 2 + 1.5 * math.pi * i / 24
        Rr = geo['r3'] + 0.8 * geo['a_max'] * (0.4 + 0.6 * i / 24)
        spiral.append((Rr * math.sin(th), -Rr * math.cos(th), zd))
    m.flow('flow_discharge', [(0, 0, ZE + 0.02), (0, -0.06, zd)] + spiral + [(xn + 0.16, yn, zd + 0.1), (xn + 0.16, yn, 0.3), (xn + 0.6, yn, 0.35)],
           'flow_discharge', 0.007, 0.12)
    return m.export(out_dir)


META = {
    'summary': ('A vertical pump for sumps and pits where the hydraulic end hangs in the liquid but every bearing is above the '
                'mounting plate. A short, very stiff shaft carries the impeller as a cantilever, so there are no submerged '
                'bushings to wear out on abrasive or corrosive liquids, and the pump tolerates running dry when the sump '
                'empties. Liquid enters the bottom of the volute and leaves up a separate discharge pipe.'),
    'classification': {'family': 'Rotodynamic (centrifugal), radial flow', 'configuration': 'Vertical cantilever (no line-shaft bearings)', 'api_610_type': 'VS5 (cantilever sump pump); VS4 has line-shaft bearings'},
    'model_configuration': {'impeller': 'Semi-open, 4 vanes', 'immersion_note': 'Maximum setting depth is limited by shaft stiffness/critical speed (typically up to ~1.5–2 m; verify).',
                            'bearings': 'Grease/oil lubricated, above plate'},
    'standards': [
        {'id': 'API 610', 'title': 'Centrifugal Pumps …', 'relevance': 'Defines VS5 cantilever sump pumps.', 'edition': 'to be verified'},
        {'id': 'ANSI/HI 2.1-2.2 / 2.3', 'title': 'Rotodynamic vertical pumps', 'relevance': 'Nomenclature and application.', 'edition': 'to be verified'},
    ],
    'references': ['Karassik et al., Pump Handbook — vertical sump pumps.', 'API 610 type classification (scope summary).'],
    'components': {
        'support_column': C('Supports the casing from the mounting plate and encloses the shaft.', 'Stiff tube flanged to the casing cover and plate.', 'Carbon or stainless steel.',
                            'Immersed; no bearings inside.', ['Corrosion'], ['Visual at pull']),
        'mounting_plate': C('Covers the sump and carries the whole pump.', 'Fabricated plate with openings for column and discharge pipe.', 'Steel, stainless.',
                            'May need to be vapour-tight for hazardous sumps.', ['Corrosion', 'Gasket leakage'], ['Bolts and gasket']),
        'cantilever_shaft': C('Carries the overhung impeller with small deflection so no lower bearing is needed.', 'Large-diameter ground shaft; stiffness sets maximum length.',
                              'Stainless steel.', 'Must stay below critical speed with margin.', ['Excess deflection → rub', 'Fatigue'], ['Run-out']),
        'motor_stand_c': C('Supports the motor above the bearing housing.', 'Fabricated stand with access windows.', 'Steel.', 'Rigid support.', ['Resonance'], ['Vibration']),
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
