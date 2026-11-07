"""
Submersible Borewell Pump — multistage stainless pump end close-coupled to a
water-filled submersible motor, hung on the riser pipe inside a well casing.
Water enters through the intake screen between motor and pump, rises through
the stages and leaves through the built-in non-return valve into the riser.
Axis Z, top of pump (riser connection) at z = 0.
"""
import math
from pumpforge.core import Model, lathe, lathe_split, ring_profile, cyl, box, join, split, merge_halves, group_by, rotate, TAU
from pumpforge.vertical import bowl_stage, stage_flow, VERTICAL_META, H
from pumpforge.shapes import sweep_tube
from pumpforge.common_meta import C

ID = 'submersible_borewell_pump'
S = 0.45
N = 6


def ex(z, dx=0.0):
    return (dx * 0.5, 0.0, 0.45 * z)


def build(out_dir):
    m = Model(ID, 'Submersible Borewell Pump (6-inch, Multistage)', 'A · Centrifugal & Special Hydraulic Pumps', META)
    rs = 0.0215 * S
    # discharge head with non-return valve
    zt = 0.0
    dh = [lathe_split('dh', [(0.03, zt - 0.16), (0.0875, zt - 0.16), (0.0875, zt - 0.1), (0.06, zt - 0.05), (0.05, zt - 0.05),
                             (0.05, zt + 0.04), (0.04, zt + 0.04), (0.04, zt - 0.04), (0.045, zt - 0.08), (0.06, zt - 0.11),
                             (0.03, zt - 0.11)], 'stainless', 96)]
    p = m.part('discharge_head', 'Discharge Head (Threaded Outlet)', 'pump_end', section='split', explode=ex(0.15), info={'ref': 'sub_head'})
    p.add_split(*merge_halves('discharge_head', dh))
    nrv = [lathe('nrv', [(0, zt - 0.1), (0.035, zt - 0.1), (0.035, zt - 0.09), (0.012, zt - 0.075), (0.0, zt - 0.07)], 'stainless', 48),
           cyl('nrv_stem', 0.005, zt - 0.075, zt - 0.03, 'stainless', 16)]
    p = m.part('non_return_valve', 'Non-Return (Check) Valve', 'check_valves', explode=ex(0.25, 0.3), info={'ref': 'nrv'})
    p.add(join('nrv', nrv))
    for mesh in p.meshes:
        m.keyframes(mesh, 'Operate', 'location', [(1, (0, 0, 0.018)), (61, (0, 0, 0.018))])
    # stages
    z = zt - 0.16
    for k in range(N):
        z -= H * S
        bowl_stage(m, k + 1, z, s=S, mat='stainless', imp_mat='stainless', ex=ex, label='Stage', x_rot=0.45, x_int=-0.35, revs=3)
    z_in = z
    # intake / suction interconnector with screen
    it = [lathe_split('intake', [(0.03, z_in - 0.13), (0.0875, z_in - 0.13), (0.0875, z_in - 0.11), (0.05, z_in - 0.1),
                                 (0.05, z_in - 0.02), (0.0875, z_in - 0.01), (0.0875, z_in), (0.042, z_in), (0.042, z_in - 0.02),
                                 (0.045, z_in - 0.1), (0.03, z_in - 0.105)], 'stainless', 96)]
    bars = [sweep_tube(f'scr{i}', [(0.08 * math.cos(a), 0.08 * math.sin(a), z_in - 0.105), (0.08 * math.cos(a), 0.08 * math.sin(a), z_in - 0.015)],
                       0.003, 'stainless', 6) for i, a in enumerate([(j + 0.5) * TAU / 24 for j in range(24)])]
    it.append(group_by(bars, 'screen'))
    p = m.part('intake', 'Suction Intake & Screen', 'pump_end', section='split', explode=ex(z_in - 0.06), info={'ref': 'intake_screen'})
    p.add_split(*merge_halves('intake', it))
    sh = cyl('pshaft', rs, z_in - 0.08, zt - 0.11, 'stainless', 24, ch=0.001)
    p = m.part('pump_shaft', 'Pump Shaft', 'rotating_element', explode=ex(-0.6, 0.45), info={'ref': 'pump_shaft'})
    p.add(sh); p.spin('Z', 3)
    cpl = cyl('cpl', 0.02, z_in - 0.12, z_in - 0.07, 'stainless', 6, ch=0.002)
    p = m.part('shaft_coupling', 'Splined Shaft Coupling', 'power_transmission', explode=ex(z_in - 0.1, 0.45), info={'ref': 'sub_coupling'})
    p.add(cpl); p.spin('Z', 3)
    # motor
    zm1 = z_in - 0.13
    zm0 = zm1 - 0.95
    R = 0.071
    mot = [lathe_split('m_shell', [(R - 0.003, zm0 + 0.06), (R, zm0 + 0.06), (R, zm1 - 0.04), (R - 0.003, zm1 - 0.04)], 'stainless', 96),
           lathe_split('m_top', [(0.012, zm1 - 0.045), (R, zm1 - 0.045), (R, zm1 - 0.03), (0.06, zm1), (0.025, zm1), (0.025, zm1 - 0.02),
                                 (0.012, zm1 - 0.02)], 'stainless', 96),
           lathe_split('m_bot', [(0.0, zm0), (0.05, zm0), (R, zm0 + 0.03), (R, zm0 + 0.065), (R - 0.003, zm0 + 0.065), (R - 0.003, zm0 + 0.035),
                                 (0.0, zm0 + 0.03)], 'stainless', 96)]
    p = m.part('motor_shell', 'Submersible Motor Shell & End Covers', 'motor', section='split', explode=ex(zm0 + 0.4, -0.45), info={'ref': 'sub_motor'})
    p.add_split(*merge_halves('motor_shell', mot))
    st = [lathe_split('st', [(0.037, zm0 + 0.2), (R - 0.004, zm0 + 0.2), (R - 0.004, zm1 - 0.15), (0.037, zm1 - 0.15)], 'lamination', 96),
          lathe_split('w1', [(0.038, zm0 + 0.16), (0.06, zm0 + 0.16), (0.06, zm0 + 0.2), (0.038, zm0 + 0.2)], 'copper', 64),
          lathe_split('w2', [(0.038, zm1 - 0.15), (0.06, zm1 - 0.15), (0.06, zm1 - 0.11), (0.038, zm1 - 0.11)], 'copper', 64)]
    p = m.part('stator', 'Stator (Water-Filled, PE-Insulated Winding)', 'motor', section='split', explode=ex(zm0 + 0.4, -0.9), info={'ref': 'stator_sub'})
    p.add_split(*merge_halves('stator', st))
    rot = [cyl('rotor', 0.035, zm0 + 0.205, zm1 - 0.155, 'lamination', 64), cyl('mshaft', 0.0125, zm0 + 0.08, zm1 + 0.005, 'stainless', 24),
           lathe('slinger', [(0.0125, zm1 - 0.03), (0.03, zm1 - 0.03), (0.03, zm1 - 0.022), (0.0125, zm1 - 0.022)], 'rubber', 32)]
    p = m.part('rotor', 'Rotor & Motor Shaft', 'motor', pivot=(0, 0, zm0), explode=ex(zm0 + 0.4, 0.9), info={'ref': 'rotor'})
    p.add(join('rotor', rot)); p.spin('Z', 3)
    tb = [lathe_split('tb_runner', ring_profile(0.0125, 0.045, zm0 + 0.1, zm0 + 0.112), 'steel', 64),
          lathe_split('tb_pads', ring_profile(0.016, 0.047, zm0 + 0.086, zm0 + 0.1), 'carbon', 64),
          lathe_split('rb', ring_profile(0.0127, 0.02, zm1 - 0.1, zm1 - 0.06), 'carbon', 48)]
    p = m.part('thrust_bearing', 'Thrust Bearing (Tilting Pad) & Radial Bearings', 'bearings', section='split', explode=ex(zm0 + 0.1, -0.9),
               info={'ref': 'sub_thrust'})
    p.add_split(*merge_halves('thrust', tb))
    dia = lathe_split('diaph', [(0.0, zm0 + 0.02), (0.055, zm0 + 0.02), (0.065, zm0 + 0.03), (0.065, zm0 + 0.034), (0.055, zm0 + 0.026),
                                (0.0, zm0 + 0.026)], 'rubber', 64)
    p = m.part('pressure_diaphragm', 'Pressure-Equalising Diaphragm', 'motor', section='split', explode=ex(zm0 - 0.1, -0.45), info={'ref': 'sub_diaphragm'})
    p.add_split(*dia)
    # cable + cable guard
    cab = sweep_tube('cable', [(-0.05, 0.088, zm1 - 0.05), (-0.05, 0.092, zm1), (-0.03, 0.095, z_in), (-0.03, 0.097, zt - 0.17),
                               (-0.03, 0.097, zt + 0.25)], 0.006, 'rubber', 10)
    guard = box('cg', (0.03, 0.006, zt - 0.17 - z_in), (-0.03, 0.104, (zt - 0.17 + z_in) / 2), 'stainless')
    p = m.part('cable', 'Drop Cable & Cable Guard', 'electrical', explode=ex(-0.4, 0.0), info={'ref': 'drop_cable'})
    p.add(join('cable', [cab, guard]), smooth_angle=60)
    # riser and well casing
    rp = lathe('riser', [(0.034, zt - 0.02), (0.044, zt - 0.02), (0.044, zt + 0.35), (0.034, zt + 0.35)], 'steel', 48)
    p = m.part('riser_pipe', 'Riser (Drop) Pipe', 'system_piping', section='split', explode=ex(0.5), info={'ref': 'riser'})
    p.add_split(*split(rp))
    wc = lathe('casing', [(0.105, zm0 - 0.3), (0.112, zm0 - 0.3), (0.112, zt + 0.35), (0.105, zt + 0.35)], 'paint_grey', 48,
               a0=0.0, a1=math.pi, cap_mat='paint_grey')
    p = m.part('well_casing', 'Well Casing (150 mm, shown cut away)', 'well', section='keep', explode=(-0.5, 0.3, 0), info={'ref': 'well_casing'})
    p.add(wc, smooth_angle=40)

    Y = 0.01
    m.flow('flow_in', [(0.1, Y, zm1 - 0.4), (0.098, Y, zm1 - 0.05), (0.09, Y, z_in - 0.06), (0.03, Y, z_in - 0.04), (0.027, Y, z_in)],
           'flow_suction', 0.004, 0.08)
    d = []
    for k in reversed(range(N)):
        d += stage_flow(zt - 0.16 - (k + 1) * H * S, s=S, Y=Y)
    d += [(0.025, Y, zt - 0.14), (0.02, Y, zt - 0.06), (0.02, Y, zt + 0.3)]
    m.flow('flow_discharge', d, 'flow_discharge', 0.004, 0.1)
    return m.export(out_dir)


META = {
    'summary': ('A borehole (well) pump in which both the multistage pump and its electric motor are lowered into the well '
                'below the water level and hang from the riser pipe. The sealed, water-filled motor sits at the bottom so '
                'water flowing past to the intake cools it; the pump stages above lift water up the riser. A built-in '
                'check valve keeps the riser full when the pump stops. No long line shaft is needed, so very deep wells '
                'can be served.'),
    'classification': {'family': 'Rotodynamic, mixed/radial flow diffuser stages', 'configuration': 'Submersible, multistage, close-coupled motor below pump'},
    'model_configuration': {'well_size': '150 mm (6 in) borehole', 'stages': N, 'motor': 'Water-filled rewindable 6 in motor with tilting-pad thrust bearing and pressure-equalising diaphragm (NEMA/ISO interface flange)',
                            'cooling_note': 'Minimum flow velocity past the motor (often ~0.08–0.15 m/s per manufacturer) is required; fit a flow sleeve if water enters from above.'},
    'standards': [
        {'id': 'NEMA MG 1 (Part 18) / ISO interface', 'title': 'Submersible motor mounting dimensions (4 in, 6 in, 8 in)', 'relevance': 'Motor–pump interchangeability.', 'edition': 'to be verified'},
        {'id': 'ANSI/HI 11.6', 'title': 'Rotodynamic Submersible Pumps for Hydraulic Performance, Hydrostatic Pressure, Mechanical, and Electrical Acceptance Tests', 'relevance': 'Testing of submersible pumps.', 'edition': 'to be verified'},
        {'id': 'ISO 9906', 'title': 'Hydraulic performance acceptance tests', 'relevance': 'Testing.', 'edition': 'to be verified'},
        {'id': 'IEC 60034 series', 'title': 'Rotating electrical machines', 'relevance': 'Motor ratings.', 'edition': 'to be verified'},
    ],
    'references': ['Manufacturer submersible pump and motor installation manuals (generic practice).', 'Karassik et al., Pump Handbook — submersible pumps.'],
    'components': {**VERTICAL_META,
        'sub_head': C('Top housing connecting the pump to the riser pipe; holds the non-return valve.', 'Cast or pressed stainless housing with threaded outlet.',
                      'Stainless steel (304/316), bronze, cast iron.', 'Carries full pump weight + water column load.', ['Thread corrosion', 'Valve seat wear'], ['Threads and valve at pull']),
        'nrv': C('Prevents back-flow and water hammer, keeps the riser full and stops reverse rotation.', 'Spring-assisted poppet in the discharge head.',
                 'Stainless steel/polymer with elastomer seat.', 'Opens when pump pressure exceeds column pressure.', ['Leakage (riser drains)', 'Sticking'], ['Check at each pull']),
        'intake_screen': C('Admits water to the first stage while keeping out large particles and protecting the motor-pump coupling.', 'Slotted screen around the suction interconnector.',
                           'Stainless steel.', 'Must stay submerged; sand ingress wears stages.', ['Clogging (encrustation)', 'Sand wear'], ['Clean/descale']),
        'sub_coupling': C('Transmits torque from motor to pump shaft.', 'Splined sleeve coupling.', 'Stainless steel.', 'Inside intake.', ['Spline wear'], ['Spline condition']),
        'sub_motor': C('Hermetically sealed water-filled (or oil-filled) motor that drives the pump under water.', 'Stainless shell, end covers, sand slinger and shaft seal at top, diaphragm at bottom.',
                       'Stainless steel (316 for aggressive water).', 'Cooled by water flowing past; maximum water temperature and minimum velocity per manufacturer.',
                       ['Overheating from low cooling flow', 'Insulation failure', 'Sand ingress'], ['Insulation resistance from surface', 'Current and voltage monitoring']),
        'stator_sub': C('Produces the rotating field; in rewindable motors the winding wire is PE/PVC insulated to run in water.', 'Laminated core in stainless can or wet-wound.',
                        'Electrical steel, insulated copper.', 'Rated for submersion.', ['Insulation breakdown'], ['Megger test']),
        'sub_thrust': C('Carries the full hydraulic down-thrust of all pump stages.', 'Water-lubricated tilting-pad (Kingsbury/Mitchell type) thrust bearing; carbon radial bushings.',
                        'Carbon pads, steel runner.', 'Thrust capacity limits the number of stages/head.', ['Overload/wear', 'Dry start damage'], ['Motor current trend']),
        'sub_diaphragm': C('Equalises internal fill-water pressure with the well and accommodates thermal expansion.', 'Rubber diaphragm in the motor base.',
                           'Nitrile/EPDM.', 'Prevents well water ingress.', ['Rupture'], ['Check fill water at service']),
        'drop_cable': C('Supplies power from the surface to the motor.', 'Flat or round submersible cable with motor lead and splice; protected by a cable guard over the pump.',
                        'Copper conductors, PVC/PE/EPDM insulation.', 'Sized for voltage drop over the full depth.', ['Abrasion against casing', 'Splice failure'], ['Insulation resistance']),
        'riser': C('Carries water to the surface and suspends the pump.', 'Threaded or flanged steel/stainless or HDPE pipe.', 'Galvanised steel, stainless, uPVC/HDPE.',
                   'Tensile load of pump + water column + cable.', ['Corrosion', 'Thread failure'], ['Inspect at pull']),
        'well_casing': C('Lines the borehole.', 'Steel or uPVC casing with screen at the aquifer.', 'Steel, uPVC.', 'Pump OD must clear casing ID.', ['Collapse/encrustation'], ['Camera survey']),
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
