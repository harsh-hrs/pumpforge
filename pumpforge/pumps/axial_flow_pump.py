"""
Axial Flow (Propeller) Pump — vertical wet-pit propeller pump: 4-blade axial
propeller in a cylindrical housing, straightening diffuser vanes above it,
bell-mouth inlet, column and above-floor discharge elbow.  For very large flow
at low head (flood control, irrigation, cooling water circulation).  Axis Z.
"""
import math
from pumpforge.core import Model, lathe, lathe_split, ring_profile, cyl, join, split, merge_halves, group_by, TAU
from pumpforge.shapes import vane
from pumpforge.vertical import column, lineshaft_bearing, VERTICAL_META, elbow_head, nut_ring, radial_rib
from pumpforge.common_meta import C

ID = 'axial_flow_pump'
RS = 0.045        # shaft radius
ZP = -1.75        # propeller centre plane
RT = 0.30         # tip radius
RH = 0.13         # hub radius


def ex(z, dx=0.0):
    return (dx * 1.6, 0.0, 0.3 * z)


def build(out_dir):
    m = Model(ID, 'Axial Flow (Propeller) Pump, Vertical Wet-Pit', 'A · Centrifugal & Special Hydraulic Pumps', META)
    hd = elbow_head(m, 0.2, ex, x_noz=1.2, z_bend=0.7, motor_R=0.3, motor_L=0.75, shaft_r=RS, revs=1.5)
    z_col = ZP + 0.66
    zr = z_col * 0.5
    column(m, 'column_pipe_1', 'Column Pipe – Upper', 0.0, zr + 0.01, s=2.0, ex=ex)
    column(m, 'column_pipe_2', 'Column Pipe – Lower', zr - 0.01, z_col, s=2.0, ex=ex)
    lineshaft_bearing(m, 1, zr, s=2.0, ex=ex)
    mat = 'paint_blue'
    # diffuser bowl: propeller housing outlet -> column
    z0, z1 = ZP + 0.12, z_col
    dif = [lathe_split('dif_wall', [(RT + 0.004, z0), (0.37, z0), (0.37, z0 + 0.03), (RT + 0.03, z0 + 0.05), (0.25, z1 - 0.05),
                                    (0.34, z1 - 0.03), (0.34, z1), (0.202, z1), (0.202, z1 - 0.04), (RT + 0.004, z0 + 0.06)], mat, 96),
           lathe_split('dif_hub', [(RS + 0.006, z0 + 0.01), (RH, z0 + 0.01), (RH, z0 + 0.08), (0.075, z1 - 0.1), (0.06, z1 - 0.02),
                                   (RS + 0.006, z1 - 0.02)], mat, 64)]
    vanes = [vane(f'dv{i}', [(RH, z0 + 0.04), (0.11, z0 + 0.2), (0.08, z1 - 0.12)], [(RT, z0 + 0.04), (0.28, z0 + 0.2), (0.24, z1 - 0.12)],
                  lambda s, t, th=TAU * i / 7: th + 0.7 * (1 - (1 - s) ** 2), 0.01, mat, ns=16, nt=5) for i in range(7)]
    dif.append(split(join('dvanes', vanes)))
    dif.append(nut_ring('dif_n', 12, 0.66, 0.03, z1 - 0.03, z1 - 0.05))
    p = m.part('diffuser_bowl', 'Diffuser Bowl (Straightening Vanes)', 'bowl_assembly', section='split', explode=ex(z0 + 0.3),
               info={'ref': 'diffuser_bowl'})
    p.add_split(*merge_halves('diffuser_bowl', dif))
    p = m.part('diffuser_bearing', 'Diffuser Hub Bearing', 'bearings', section='split', explode=ex(z0 + 0.3, -0.7), info={'ref': 'bowl_bearing'})
    p.add_split(*lathe_split('dbr', ring_profile(RS + 0.0005, RS + 0.006, z1 - 0.3, z1 - 0.03), 'bronze', 48))
    # propeller housing
    ph = [lathe_split('ph', [(RT + 0.004, ZP - 0.14), (0.37, ZP - 0.14), (0.37, ZP - 0.11), (RT + 0.03, ZP - 0.1), (RT + 0.03, ZP + 0.1),
                             (0.37, ZP + 0.11), (0.37, ZP + 0.14), (RT + 0.004, ZP + 0.14)], 'paint_blue_dark', 96),
          nut_ring('ph_n', 12, 0.66, 0.03, ZP + 0.14, ZP + 0.16), nut_ring('ph_n2', 12, 0.66, 0.03, ZP - 0.14, ZP - 0.16)]
    p = m.part('propeller_housing', 'Propeller Housing (Liner)', 'bowl_assembly', section='split', explode=ex(ZP), info={'ref': 'propeller_housing'})
    p.add_split(*merge_halves('propeller_housing', ph))
    # propeller
    hub = lathe('prop_hub', [(RS, ZP + 0.1), (RH, ZP + 0.1), (RH, ZP - 0.08), (0.11, ZP - 0.16), (0.06, ZP - 0.22), (0.0, ZP - 0.24),
                             (0.0, ZP + 0.1)], 'stainless', 96)
    blades = [vane(f'pb{i}', [(RH - 0.005, ZP - 0.075), (RH - 0.005, ZP + 0.075)], [(RT - 0.002, ZP - 0.05), (RT - 0.002, ZP + 0.05)],
                   lambda s, t, th=TAU * i / 4: th - s * (1.15 * (1 - t) + 0.5 * t), 0.014, 'stainless', ns=18, nt=8, t_ext=0.03, taper=0.25)
              for i in range(4)]
    p = m.part('propeller', 'Propeller (4-Blade)', 'rotating_element', explode=ex(ZP, 0.8), info={'ref': 'propeller'})
    hb, hf = split(hub)
    p.add(join('prop_blades', blades), 'keep')
    p.add(hb, 'back'); p.add(hf, 'front')
    p.spin('Z', 1.5)
    # suction bell
    zb = ZP - 0.14
    bell = [lathe_split('bell', [(RT + 0.004, zb), (0.37, zb), (0.37, zb - 0.03), (RT + 0.04, zb - 0.05), (0.38, zb - 0.25),
                                 (0.47, zb - 0.36), (0.49, zb - 0.385), (0.47, zb - 0.395), (0.44, zb - 0.38), (0.35, zb - 0.27),
                                 (RT + 0.006, zb - 0.06)], mat, 96),
            lathe_split('bhub', [(RS + 0.006, zb - 0.06), (0.075, zb - 0.06), (0.075, zb - 0.3), (0.0, zb - 0.33), (0.0, zb - 0.31),
                                 (RS + 0.006, zb - 0.3)], mat, 48),
            group_by([radial_rib(f'br{i}', 0.07, 0.33, zb - 0.28, zb - 0.16, math.radians(a), 0.016, mat) for i, a in enumerate((30, 150, 270))],
                     'bribs')]
    p = m.part('suction_bell', 'Suction Bell', 'bowl_assembly', section='split', explode=ex(zb - 0.3), info={'ref': 'suction_bell'})
    p.add_split(*merge_halves('suction_bell', bell))
    p = m.part('bell_bearing', 'Suction Bell Bearing', 'bearings', section='split', explode=ex(zb - 0.2, -0.7), info={'ref': 'bowl_bearing'})
    p.add_split(*lathe_split('bbr', ring_profile(RS + 0.0005, RS + 0.006, zb - 0.29, zb - 0.07), 'bronze', 48))
    sh = cyl('shaft', RS, zb - 0.29, hd['z_shaft_top'], 'stainless', 40, ch=0.003)
    p = m.part('pump_shaft', 'Pump & Line Shaft', 'rotating_element', explode=ex(-0.8, 0.8), info={'ref': 'line_shaft'})
    p.add(sh); p.spin('Z', 1.5)

    Y = 0.02
    for sx in (1, -1):
        m.flow(f'flow_suction{sx}', [(sx * 0.42, Y, zb - 0.8), (sx * 0.44, Y, zb - 0.45), (sx * 0.24, Y, zb - 0.1), (sx * 0.22, Y, ZP - 0.06)],
               'flow_suction', 0.014, 0.25)
    m.flow('flow_discharge', [(0.22, Y, ZP - 0.06), (0.22, Y, ZP + 0.08), (0.2, Y, z0 + 0.2), (0.16, Y, z1), (0.15, Y, 0.0), (0.16, Y, 0.55),
                              (0.4, Y, 0.7), (1.5, Y, 0.7)], 'flow_discharge', 0.014, 0.3)
    m.flow('flow_discharge2', [(-0.22, Y, ZP - 0.06), (-0.22, Y, ZP + 0.08), (-0.2, Y, z0 + 0.2), (-0.16, Y, z1), (-0.15, Y, 0.0),
                               (-0.15, Y, 0.45), (0.05, Y, 0.85), (0.4, Y, 0.8), (1.5, Y, 0.75)], 'flow_discharge', 0.014, 0.3)
    return m.export(out_dir)


META = {
    'summary': ('A propeller pump adds energy almost entirely by the lift of its blades, like a ship propeller working in a '
                'tube: liquid passes straight through axially. Straightening vanes above the propeller remove the swirl and '
                'recover pressure. It delivers very large flows at low heads with high specific speed; the head–flow curve is '
                'steep and power rises toward shut-off, so these pumps must not be started or run against a closed valve.'),
    'classification': {'family': 'Rotodynamic, axial flow', 'configuration': 'Vertical wet pit, single stage, line-shaft'},
    'model_configuration': {'propeller': '4 blades, fixed pitch (adjustable/variable-pitch hubs are used on large units)',
                            'diffuser': '7 straightening vanes', 'specific_speed_note': 'Axial pumps typically Ns > ~9,000 (US) / nq > ~160; verify.'},
    'standards': [
        {'id': 'ANSI/HI 9.8', 'title': 'Rotodynamic Pumps for Pump Intake Design', 'relevance': 'Intake design is critical; axial pumps are sensitive to inflow distortion and vortices.', 'edition': 'to be verified'},
        {'id': 'ANSI/HI 2.1-2.2 / 2.3', 'title': 'Rotodynamic vertical pumps', 'relevance': 'Nomenclature, design and application.', 'edition': 'to be verified'},
        {'id': 'ISO 9906', 'title': 'Hydraulic performance acceptance tests', 'relevance': 'Testing.', 'edition': 'to be verified'},
    ],
    'references': ['Stepanoff — Centrifugal and Axial Flow Pumps.', 'Karassik et al., Pump Handbook — axial flow pumps.'],
    'components': {**VERTICAL_META,
        'propeller': C('Adds energy to the liquid by blade lift, accelerating flow axially.', 'Hub with 3–6 twisted aerofoil-section blades; blade angle fixed, adjustable at standstill, or variable in service.',
                       'Stainless steel, bronze, duplex.', 'Steep head-capacity curve; power is highest near shut-off; unstable (stall) region at part load.',
                       ['Cavitation erosion on blade suction side', 'Tip clearance wear', 'Fatigue from inflow distortion'], ['Blade surfaces', 'Tip clearance']),
        'propeller_housing': C('Close-fitting liner around the propeller blade tips.', 'Machined cylindrical (sometimes spherical) housing; renewable liner.',
                               'Cast iron, steel, stainless.', 'Tip clearance strongly affects efficiency.', ['Wear increasing tip clearance', 'Cavitation pitting'], ['Clearance gauge']),
        'diffuser_bowl': C('Removes swirl from the propeller discharge and converts velocity into pressure before the column.', 'Casting with straightening vanes between hub and conical wall; bearing hub.',
                           'Cast iron, steel, stainless.', 'Efficiency depends on vane inlet angle match.', ['Erosion', 'Bearing hub wear'], ['Vane condition', 'Bearing clearance']),
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
