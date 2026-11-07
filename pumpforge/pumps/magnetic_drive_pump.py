"""
Magnetic Drive Pump — sealless end-suction centrifugal pump (frame-mounted).
Torque passes through a stationary containment shell by a synchronous permanent-
magnet coupling: outer magnet ring on the drive shaft, inner magnet carrier fixed
to the impeller, which runs on SiC sleeve bearings on a stationary shaft.
Representative of ISO 15783 / ASME B73.3 / API 685 style designs.
Shaft along +X (suction at -X), cut plane y = 0.
"""
import math
from pumpforge.core import Model, lathe, lathe_split, ring_profile, cyl, box, csg, split, join, merge_halves, TAU
from pumpforge.parts import (H_FRAME, place, radial_impeller, volute_casing, ball_bearing, add_motor_h, add_coupling,
                             add_baseplate, nozzle_bolts, volute_flow, add_impeller)
from pumpforge.core import split_faces, split_many

ID = 'magnetic_drive_pump'
CZ = 0.34
BP_TOP = 0.10


def build(out_dir):
    m = Model(ID, 'Magnetic Drive Pump (Sealless, Frame-Mounted)', 'A · Centrifugal & Special Hydraulic Pumps', META)
    Mx = H_FRAME(0.0, CZ)
    core, shroud, imp = radial_impeller('impeller', 0.20, 0.016, 0.042, 0.012, n_blades=6, mat='stainless', wrap=1.7)
    cas, geo = volute_casing('casing', imp, 'stainless', r_suc=0.042, L_suc=0.13, r_dis=0.033, H_dis=0.21)
    place(cas, Mx)
    zb = geo['z_back']
    # casing foot (cast) down to baseplate
    foot = box('cfoot', (0.07, 0.26, CZ - geo['r3'] - BP_TOP), (zb - 0.04, 0, BP_TOP + (CZ - geo['r3'] - BP_TOP) / 2 + 0.004),
               'stainless', bevel=0.004)
    cas = csg('casing', [cas, foot], [], 'stainless')
    cb, cf = split(cas)
    Rend = geo['Rend']
    nb = [nozzle_bolts('dfb', 8, 2 * (geo['r_dis'] + 0.03), 0.02, geo['H_dis'] + CZ, geo['H_dis'] + CZ + 0.014, 'Z',
                       (zb * 0 + imp['zc'], Rend, 0), phase=math.pi / 8),
          nozzle_bolts('sfb', 8, 2 * (geo['r_suc'] + 0.03), 0.02, -geo['L_suc'], -geo['L_suc'] - 0.014, 'X', (0, 0, CZ),
                       phase=math.pi / 8)]
    nbb, nbf = split_faces(join('nozb', nb), 'y', 0.0)
    p = m.part('casing', 'Volute Casing', 'casing', section='split', explode=(-0.42, 0, 0), info={'ref': 'volute_casing'})
    p.add_split(join('cas_b', [cb, nbb]), join('cas_f', [cf, nbf]), smooth_angle=40)

    add_impeller(m, 'impeller', 'Closed Impeller', core, shroud, Mx, (0, 0, CZ), explode=(-0.2, 0, 0))

    x_ib = imp['z_back']           # impeller hub back face
    # rear casing (casing cover) with containment shell flange
    rc = lathe('rear_casing', [(0.074, zb), (geo['r_bf'], zb), (geo['r_bf'], zb + 0.016), (0.11, zb + 0.022),
                               (0.11, zb + 0.03), (0.074, zb + 0.03)], 'stainless', 96, axis='X', center=(0, 0, CZ))
    p = m.part('rear_casing', 'Rear Casing (Casing Cover)', 'casing', section='split', explode=(-0.05, 0, 0),
               info={'ref': 'casing_cover'})
    p.add_split(*split(rc))
    # containment shell (can)
    x_s0, x_s1 = zb + 0.006, zb + 0.13
    shell = lathe('shell', [(0.066, x_s0), (0.07, x_s0), (0.07, x_s1 - 0.012), (0.062, x_s1), (0.02, x_s1 + 0.004),
                            (0.02, x_s1 - 0.01), (0.056, x_s1 - 0.012), (0.066, x_s1 - 0.018)], 'chrome', 96, axis='X',
                  center=(0, 0, CZ))
    p = m.part('containment_shell', 'Containment Shell', 'magnetic_coupling', section='split', explode=(0.22, 0, 0))
    p.add_split(*split(shell))
    # stationary shaft + SiC bearings
    ss = cyl('stat_shaft', 0.012, 0.005, x_s1 - 0.002, 'silicon_carbide', 32, axis='X', center=(0, 0, CZ), ch=0.002)
    p = m.part('stationary_shaft', 'Stationary Shaft', 'magnetic_coupling', explode=(0.05, -0.32, 0))
    p.add(ss)
    bush = merge_halves('sic', [lathe_split(f'sic{i}', ring_profile(0.0122, 0.018, x0, x0 + 0.018), 'silicon_carbide', 48,
                                            axis='X', center=(0, 0, CZ)) for i, x0 in enumerate((x_ib + 0.02, x_s1 - 0.045))])
    p = m.part('product_bearings', 'Product-Lubricated SiC Sleeve Bearings', 'bearings', section='split',
               explode=(0.05, -0.24, 0))
    p.add_split(*bush)
    # inner magnet carrier (rotates with impeller)
    ic = [lathe('ic_hub', [(0.018, x_ib - 0.002), (0.026, x_ib - 0.002), (0.026, x_ib + 0.02), (0.018, x_ib + 0.02)],
                'stainless', 48, axis='X', center=(0, 0, CZ)),
          lathe('ic_body', [(0.018, x_ib + 0.02), (0.06, x_ib + 0.02), (0.06, x_s1 - 0.022), (0.018, x_s1 - 0.022)],
                'stainless', 96, axis='X', center=(0, 0, CZ))]
    for i in range(12):
        a = TAU * (i + 0.5) / 12
        mag = box(f'im{i}', (x_s1 - 0.03 - x_ib - 0.03, 0.022, 0.006), (x_ib + 0.02 + (x_s1 - x_ib - 0.042) / 2, 0, 0.0625),
                  'paint_red' if i % 2 else 'paint_blue_dark')
        from pumpforge.core import rotate
        rotate(mag, a, 'X')
        mag.data.transform(__import__('mathutils').Matrix.Translation((0, 0, CZ)))
        ic.append(mag)
    p = m.part('inner_magnet', 'Inner Magnet Carrier', 'magnetic_coupling', pivot=(x_ib, 0, CZ), explode=(0.05, 0, 0.34))
    b_, f_ = split_many('inner_magnet', ic)
    p.add(b_, 'back'); p.add(f_, 'front'); p.spin('X', 2)
    # outer magnet ring + drive shaft
    x_om0, x_om1 = x_ib + 0.012, x_s1 + 0.004
    x_b0 = x_s1 + 0.07            # drive bearing housing start
    om = [lathe('om_ring', [(0.078, x_om0), (0.098, x_om0), (0.098, x_om1 + 0.016), (0.03, x_om1 + 0.016),
                            (0.03, x_om1 + 0.002), (0.078, x_om1 + 0.002)], 'steel', 96, axis='X', center=(0, 0, CZ)),
          cyl('drive_shaft', 0.022, x_om1, x_b0 + 0.24, 'steel', 32, axis='X', center=(0, 0, CZ), ch=0.002)]
    from pumpforge.core import rotate
    for i in range(14):
        a = TAU * (i + 0.5) / 14
        mag = box(f'om{i}', (x_om1 - x_om0 - 0.01, 0.026, 0.006), ((x_om0 + x_om1) / 2, 0, 0.0745),
                  'paint_red' if i % 2 else 'paint_blue_dark')
        rotate(mag, a, 'X')
        mag.data.transform(__import__('mathutils').Matrix.Translation((0, 0, CZ)))
        om.append(mag)
    p = m.part('outer_magnet', 'Outer Magnet Ring & Drive Shaft', 'magnetic_coupling', pivot=(x_om1, 0, CZ),
               explode=(0.42, 0, 0.0))
    b_, f_ = split_many('outer_magnet', om)
    p.add(b_, 'back'); p.add(f_, 'front'); p.spin('X', 2)
    # bearing bracket
    br_out = lathe('bracket', [(0.0, zb + 0.03), (0.13, zb + 0.03), (0.13, zb + 0.042), (0.118, zb + 0.05),
                               (0.118, x_om1 + 0.03), (0.07, x_b0), (0.07, x_b0 + 0.2), (0.08, x_b0 + 0.21), (0, x_b0 + 0.21)],
                   'paint_blue', 96, axis='X', center=(0, 0, CZ))
    br_in = lathe('bracket_i', [(0, zb + 0.02), (0.108, zb + 0.02), (0.108, x_om1 + 0.025), (0.05, x_b0 + 0.005),
                                (0.05, x_b0 + 0.195), (0.03, x_b0 + 0.2), (0.03, x_b0 + 0.22), (0, x_b0 + 0.22)],
                  'paint_blue', 96, axis='X', center=(0, 0, CZ))
    bfoot = box('bfoot', (0.12, 0.24, CZ - 0.07 - BP_TOP), (x_b0 + 0.1, 0, BP_TOP + (CZ - 0.07 - BP_TOP) / 2 + 0.005),
                'paint_blue', bevel=0.004)
    br = csg('bearing_bracket', [br_out, bfoot], [br_in], 'paint_blue')
    p = m.part('bearing_bracket', 'Bearing Bracket (Drive End)', 'bearing_housing', section='split', explode=(0.58, 0, 0))
    p.add_split(*split(br), smooth_angle=40)
    bb = merge_halves('drv_brg', [ball_bearing('db1', 0.022, 0.05, x_b0 + 0.01, x_b0 + 0.032, 10, center=(0, 0, CZ)),
                                  ball_bearing('db2', 0.022, 0.05, x_b0 + 0.165, x_b0 + 0.19, 10, center=(0, 0, CZ))])
    p = m.part('drive_bearings', 'Drive Shaft Bearings', 'bearings', section='split', explode=(0.58, -0.3, 0),
               info={'ref': 'radial_bearing'})
    p.add_split(*bb)
    xc0 = x_b0 + 0.24
    add_coupling(m, 'coupling', xc0, xc0 + 0.09, CZ, 0.05, 0.022, explode=(0.75, 0, 0), foot_z=BP_TOP)
    mo = add_motor_h(m, 'm_', xc0 + 0.11, CZ, 0.13, 0.42, BP_TOP, 0.022, 0.11, explode_dx=0.95)
    add_baseplate(m, -0.22, mo['x1'] + 0.04, 0.46, BP_TOP)

    suc, dis = volute_flow(imp, geo, Mx, 0.25)
    m.flow('flow_suction', suc, 'flow_suction', 0.006, 0.12)
    m.flow('flow_discharge', dis, 'flow_discharge', 0.006, 0.12)
    return m.export(out_dir)


META = {
    'summary': ('A centrifugal pump without a dynamic shaft seal. The motor turns an outer ring of permanent '
                'magnets; their field passes through a thin, stationary containment shell and drags an inner '
                'magnet ring that is fixed to the impeller. The pumped liquid is fully enclosed by the casing and '
                'shell, and it also lubricates the internal sleeve bearings — so the pump suits toxic, '
                'flammable or costly liquids where leakage is unacceptable.'),
    'classification': {'family': 'Rotodynamic (centrifugal), radial flow',
                       'configuration': 'Overhung, end suction, sealless magnetic drive, frame-mounted',
                       'api_610_type': 'OH-type sealless; API 685 covers sealless centrifugal pumps'},
    'model_configuration': {'impeller': 'Closed radial, 6 blades', 'coupling': 'Synchronous permanent-magnet (12/14 pole sets shown)',
                            'internal_bearings': 'Silicon carbide sleeve bearings on stationary SiC shaft',
                            'containment_shell': 'Metallic (Hastelloy/stainless typical); non-metallic shells avoid eddy-current losses',
                            'note': 'Magnet count and geometry are representative.'},
    'standards': [
        {'id': 'API 685', 'title': 'Sealless Centrifugal Pumps for Petroleum, Petrochemical, and Gas Industry Process Service',
         'relevance': 'Design and testing of magnetic-drive and canned-motor pumps in process service.', 'edition': 'to be verified'},
        {'id': 'ISO 15783', 'title': 'Seal-less rotodynamic pumps — Class II — Specification',
         'relevance': 'General sealless pump requirements.', 'edition': 'to be verified'},
        {'id': 'ASME B73.3', 'title': 'Specification for Sealless Horizontal End Suction Metallic Centrifugal Pumps for Chemical Process',
         'relevance': 'Dimensional interchangeability for chemical-process mag-drive pumps.', 'edition': 'to be verified'},
        {'id': 'ISO 2858 / ISO 5199', 'title': 'End-suction centrifugal pumps — designation and technical requirements (Class II)',
         'relevance': 'Hydraulic end dimensions and design requirements for chemical pumps.', 'edition': 'to be verified'},
    ],
    'references': ['Karassik et al., Pump Handbook — sealless pumps chapter.', 'API 685 and ASME B73.3 (scope summaries).',
                   'Hydraulic Institute — magnetic drive pump application guidance (ANSI/HI 5.1-5.6, sealless rotodynamic pumps).'],
    'components': {
        'containment_shell': {
            'function': 'Pressure-retaining barrier between the pumped liquid and the atmosphere; the magnetic field passes through it.',
            'construction': 'Thin deep-drawn or machined cup bolted to the rear casing.',
            'material': 'Hastelloy C, titanium or stainless (metallic, with eddy-current heating) or PEEK/ceramic/composite (non-metallic, no eddy losses).',
            'operating_conditions': 'Metallic shells heat the liquid in the gap; internal circulation must remove this heat. Liquid near its boiling point can flash in the shell.',
            'failure_modes': ['Rupture from inner magnet rub after bearing failure', 'Overheating at low flow or dry running', 'Corrosion'],
            'inspection': ['Shell surface for rub marks at overhaul', 'Monitor shell temperature/power where instrumented']},
        'inner_magnet': {
            'function': 'Driven half of the magnetic coupling; turns the impeller.',
            'construction': 'Rare-earth (NdFeB or SmCo) magnets encapsulated in a sealed stainless or polymer-lined carrier fixed to the impeller.',
            'material': 'NdFeB/SmCo magnets, stainless or ETFE/PFA encapsulation.',
            'operating_conditions': 'Magnet temperature limits (SmCo higher) must not be exceeded or the coupling permanently weakens.',
            'failure_modes': ['Decoupling (slip) at start-up overload — magnets heat quickly', 'Demagnetisation from overheating', 'Encapsulation breach'],
            'inspection': ['Encapsulation condition', 'Coupling torque test per manufacturer']},
        'outer_magnet': {
            'function': 'Driving half of the magnetic coupling, mounted on the motor-driven shaft.',
            'construction': 'Magnet ring in a steel carrier surrounding the containment shell with a radial air gap.',
            'material': 'NdFeB/SmCo magnets, carbon steel carrier.',
            'operating_conditions': 'Runs in air; contact with the shell indicates drive bearing failure.',
            'failure_modes': ['Rubbing the shell after drive-bearing wear', 'Loose magnets'],
            'inspection': ['Drive bearing condition', 'Air-gap check']},
        'stationary_shaft': {
            'function': 'Fixed journal on which the impeller/inner magnet assembly rotates.',
            'construction': 'Ceramic or hard-coated shaft held in the shell and casing.',
            'material': 'Silicon carbide, alumina or hard-coated alloy.',
            'operating_conditions': 'Brittle — avoid thermal and mechanical shock.',
            'failure_modes': ['Fracture from dry running or shock', 'Wear'],
            'inspection': ['Visual and dimensional at overhaul']},
        'product_bearings': {
            'function': 'Radial (and with thrust faces, axial) support of the rotating inner assembly, lubricated by the pumped liquid.',
            'construction': 'SiC or carbon sleeve bushings with thrust washers.',
            'material': 'Silicon carbide (often diamond-coated), carbon-graphite.',
            'operating_conditions': 'Cannot run dry; solids in the liquid accelerate wear; minimum flow must be maintained.',
            'failure_modes': ['Dry running seizure/cracking', 'Abrasive wear', 'Thermal shock'],
            'inspection': ['Power and temperature monitoring for dry-run protection', 'Clearance at overhaul']},
        'bearing_bracket': {
            'function': 'Supports the drive shaft bearings and encloses the outer magnet ring.',
            'construction': 'Cast bracket bolted to the rear casing, with foot and bearing bores.',
            'material': 'Cast iron or ductile iron.',
            'operating_conditions': 'Air side; may include secondary containment on API 685 pumps.',
            'failure_modes': ['Bearing wear allowing outer magnet contact'],
            'inspection': ['Bearing temperature/vibration']},
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
