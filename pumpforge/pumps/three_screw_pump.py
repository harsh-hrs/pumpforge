"""
Three-Screw Pump — one double-start power (drive) rotor meshes with two idler
rotors in a close-fitting housing insert.  The intermeshing threads form sealed
chambers that travel axially from the inlet end to the outlet end without
pulsation.  Idlers are driven hydraulically (no timing gears); common for
lubricating oil, fuel oil and hydraulic service.  Axis Y (inlet end at -Y),
cut plane x = 0.
"""
import math
from pumpforge.core import (Model, lathe, lathe_split, ring_profile, cyl, box, csg, split_keep, join, merge_halves, split_faces, TAU)
from pumpforge.parts import add_drive_y, nozzle_bolts, seal_cartridge
from pumpforge.shapes import twisted_extrude, lobed_profile
from pumpforge.common_meta import C

ID = 'three_screw_pump'
CZ = 0.26
BP = 0.09
D = 0.04                      # nominal idler OD / root diameter of power rotor
RP_O, RP_I = 5 * D / 6, D / 2  # power rotor outer / root radius
RI_O, RI_I = D / 2, D / 6     # idler outer / root radius
LEAD = 10 * D / 3
Y0, Y1 = 0.05, 0.33           # rotor (thread) length


def ks(o):
    return split_keep(o, 'x', 0.0, keep_positive=False)


def build(out_dir):
    m = Model(ID, 'Three-Screw Pump (Power Rotor + 2 Idlers)', 'B · Rotary Positive-Displacement Pumps', META)
    mat = 'paint_grey'
    R = 0.09
    outs = [cyl('body', R, -0.02, Y1 + 0.08, mat, 96, axis='Y', center=(0, 0, CZ), ch=0.004),
            cyl('pin', 0.045, CZ - 0.2, CZ, mat, 48, center=(0, 0.0, 0)), cyl('pfi', 0.08, CZ - 0.2, CZ - 0.185, mat, 48, center=(0, 0.0, 0), ch=0.003),
            cyl('pout', 0.04, CZ, CZ + 0.18, mat, 48, center=(0, Y1 + 0.03, 0)), cyl('pfo', 0.075, CZ + 0.165, CZ + 0.18, mat, 48, center=(0, Y1 + 0.03, 0), ch=0.003),
            box('foot', (0.24, Y1 + 0.06, CZ - R - BP), (0, Y1 / 2, BP + (CZ - R - BP) / 2 + 0.006), mat, bevel=0.005)]
    ins = [cyl('ich', 0.075, -0.01, Y0 + 0.005, mat, 96, axis='Y', center=(0, 0, CZ)),
           cyl('och', 0.075, Y1 - 0.005, Y1 + 0.06, mat, 96, axis='Y', center=(0, 0, CZ)),
           cyl('ins', 0.072, Y0, Y1, mat, 96, axis='Y', center=(0, 0, CZ)),
           cyl('pinb', 0.035, CZ - 0.21, CZ - 0.05, mat, 48, center=(0, 0.0, 0)),
           cyl('poutb', 0.03, CZ + 0.05, CZ + 0.19, mat, 48, center=(0, Y1 + 0.03, 0)),
           cyl('shb', 0.016, Y1, Y1 + 0.1, mat, 32, axis='Y', center=(0, 0, CZ))]
    body = csg('casing', outs, ins, mat)
    p = m.part('casing', 'Pump Casing (Inlet & Outlet Chambers)', 'casing', section='split', explode=(0, 0.1, -0.2), info={'ref': 'pd_casing'})
    p.add_split(*ks(body), smooth_angle=40)
    # housing insert (liner) with three intersecting bores
    ins_o = cyl('io', 0.072, Y0, Y1, 'cast_iron', 96, axis='Y', center=(0, 0, CZ))
    bores = [cyl('bp', RP_O + 0.0006, Y0 - 0.01, Y1 + 0.01, 'cast_iron', 96, axis='Y', center=(0, 0, CZ))] + \
            [cyl(f'bi{s}', RI_O + 0.0006, Y0 - 0.01, Y1 + 0.01, 'cast_iron', 64, axis='Y', center=(s * D, 0, CZ)) for s in (1, -1)]
    hi = csg('insert', [ins_o], bores, 'cast_iron')
    p = m.part('housing_insert', 'Housing Insert (Rotor Liner)', 'casing', section='split', explode=(0, -0.05, 0.3), info={'ref': 'screw_insert'})
    p.add_split(*ks(hi), smooth_angle=40)
    # rotors
    prof_p = lobed_profile(RP_I, RP_O, 2, n=96, land=0.5, sharp=3.0)
    pr = join('power_rotor', [twisted_extrude('pr', prof_p, Y0, Y1, LEAD, 'steel', axis='Y', center=(0, 0, CZ), hand=1),
                              cyl('prs', 0.016, Y0 - 0.06, Y1 + 0.32, 'steel', 32, axis='Y', center=(0, 0, CZ), ch=0.002)])
    p = m.part('power_rotor', 'Power (Drive) Rotor', 'rotating_element', pivot=(0, 0, CZ), explode=(0, -0.45, 0), info={'ref': 'power_rotor'})
    p.add(pr, smooth_angle=50); p.spin('Y', 1)
    for s in (1, -1):
        prof_i = lobed_profile(RI_I, RI_O, 2, n=72, phase=math.pi / 2, land=0.5, sharp=3.0)
        ir = twisted_extrude(f'idl{s}', prof_i, Y0, Y1, LEAD, 'steel_dark', axis='Y', center=(s * D, 0, CZ), hand=-1)
        p = m.part(f'idler_{"right" if s > 0 else "left"}', f'Idler Rotor – {"Right" if s > 0 else "Left"}', 'rotating_element',
                   pivot=(s * D, 0, CZ), explode=(s * 0.25, -0.45, 0.1), info={'ref': 'idler_rotor'})
        p.add(ir, smooth_angle=50); p.spin('Y', -1)
    # front cover, balance piston/bearing & rear seal + bearing housing
    fc = cyl('front_cover', R, -0.05, -0.02, mat, 96, axis='Y', center=(0, 0, CZ), ch=0.004)
    p = m.part('front_cover', 'Inlet End Cover', 'casing', section='hide', explode=(0, -0.7, 0), info={'ref': 'screw_cover'})
    p.add(fc, smooth_angle=40)
    sb, sf = seal_cartridge('seal', Y1 + 0.03, Y1 + 0.09, 0.016, 0.03, axis='Y', center=(0, 0, CZ))
    p = m.part('mechanical_seal', 'Mechanical Seal', 'mechanical_seal', section='split', explode=(-0.3, 0.2, 0.1), info={'ref': 'mechanical_seal'})
    p.add_split(sb, sf)
    y0, y1 = Y1 + 0.08, Y1 + 0.28
    bh = csg('bh', [lathe('bh', [(0.0, y0), (R, y0), (R, y0 + 0.015), (0.05, y0 + 0.04), (0.05, y1), (0, y1)], mat, 96, axis='Y', center=(0, 0, CZ))],
             [cyl('bhi', 0.036, y0 + 0.04, y1 - 0.02, mat, 48, axis='Y', center=(0, 0, CZ)), cyl('bhs', 0.017, y0 - 0.01, y1 + 0.01, mat, 32, axis='Y', center=(0, 0, CZ)),
              box('bhw', (0.2, 0.06, 0.05), (0, y0 + 0.055, CZ), mat, bevel=0.01)], mat)
    p = m.part('bearing_housing', 'Bearing Housing', 'bearing_housing', section='split', explode=(0, 0.3, 0), info={'ref': 'bearing_frame'})
    p.add_split(*ks(bh), smooth_angle=40)
    brg = merge_halves('brg', [lathe_split('b', ring_profile(0.016, 0.036, y1 - 0.06, y1 - 0.035), 'steel', 48, axis='Y', center=(0, 0, CZ), phase=math.pi / 2)])
    p = m.part('bearing', 'Ball Bearing', 'bearings', section='split', explode=(-0.3, 0.3, 0), info={'ref': 'radial_bearing'})
    p.add_split(*brg)
    add_drive_y(m, Y1 + 0.32, CZ, BP, 0.016, motor_R=0.11, motor_L=0.36, y_base0=-0.12, base_w=0.46, revs=1)

    yf = 0.0
    m.flow('flow_in', [(0, 0.0, CZ - 0.5), (0, 0.0, CZ - 0.06), (0.0, Y0 - 0.02, CZ - 0.03)], 'flow_suction', 0.005, 0.08)
    for s in (1, -1):
        helix = [(s * D * 0.55 * math.cos(TAU * k / 12), Y0 + (Y1 - Y0) * k / 60, CZ + D * 0.55 * math.sin(TAU * k / 12)) for k in range(61)]
        m.flow(f'flow_axial{s}', [(s * 0.02, Y0 - 0.02, CZ - 0.02)] + helix[::3], 'flow_discharge', 0.0035, 0.06)
    m.flow('flow_out', [(0, Y1 + 0.02, CZ + 0.02), (0, Y1 + 0.03, CZ + 0.06), (0, Y1 + 0.03, CZ + 0.45)], 'flow_discharge', 0.005, 0.08)
    return m.export(out_dir)


META = {
    'summary': ('Three intermeshing screws turn in a closely fitted housing: a centre power rotor driven by the motor and two '
                'idler rotors driven by the liquid pressure acting on their threads. The meshing threads create a series of '
                'sealed chambers that move steadily from the inlet end to the outlet end as the rotors turn, giving smooth, '
                'nearly pulse-free flow and quiet running at high pressures. Suited to clean lubricating liquids — '
                'lube and seal oil, fuel oil, hydraulic oil.'),
    'classification': {'family': 'Positive displacement – rotary', 'configuration': 'Three-screw, untimed (idlers hydraulically driven), single suction'},
    'model_configuration': {'rotor_proportions': 'Power rotor OD 5/3·d, root d; idler OD d, root d/3 (classic ratios)', 'lead': '≈10/3·d (representative)',
                            'thread_profile_note': 'True rotors use conjugate cycloidal profiles; the model approximates them for visual study.'},
    'standards': [
        {'id': 'API 676', 'title': 'Positive Displacement Pumps – Rotary', 'relevance': 'Process/lube service screw pumps.', 'edition': 'to be verified'},
        {'id': 'API 614', 'title': 'Lubrication, Shaft-Sealing and Oil-Control Systems and Auxiliaries', 'relevance': 'Lube-oil systems commonly use screw pumps.', 'edition': 'to be verified'},
        {'id': 'ANSI/HI 3.1-3.5', 'title': 'Rotary Pumps', 'relevance': 'Nomenclature and application.', 'edition': 'to be verified'},
    ],
    'references': ['Karassik et al., Pump Handbook — screw pumps.', 'Manufacturer three-screw pump literature (generic practice).'],
    'components': {
        'screw_insert': C('Close-fitting liner with three intersecting bores that, with the rotors, forms the sealed chambers.', 'Cast or machined insert pressed into the casing.',
                          'Cast iron, aluminium alloys, steel.', 'Clearance controls slip; needs clean lubricating liquid.', ['Bore wear from contaminated oil'], ['Bore measurement']),
        'power_rotor': C('Driven centre rotor; transmits most of the torque and drives the idlers hydraulically.', 'Double-start convex thread integral with the shaft; balance piston on high-pressure pumps.',
                         'Nitrided/hardened steel.', 'Axial thrust balanced hydraulically.', ['Thread wear', 'Shaft seal area wear'], ['Thread profile and clearance']),
        'idler_rotor': C('Seal the chambers; driven by liquid pressure, not by contact torque.', 'Double-start concave thread rotors, floating in their bores.',
                         'Hardened steel, cast iron.', 'Need lubricating liquid.', ['End wear', 'Thread wear'], ['End-play and clearance']),
        'screw_cover': C('Closes the inlet end; carries idler end plates/thrust surfaces.', 'Bolted end cover.', 'Cast iron/steel.', 'Inlet pressure.', ['Wear at idler thrust faces'], ['Thrust faces']),
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
