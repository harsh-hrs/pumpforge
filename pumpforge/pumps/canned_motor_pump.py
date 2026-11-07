"""
Canned Motor Pump — sealless close-coupled centrifugal pump: impeller and motor
rotor share one shaft running in product-lubricated bearings; thin corrosion-
resistant "cans" seal the stator and rotor from the pumped liquid. A
circulation line takes a small flow from the discharge through the motor to
cool it and lubricate the bearings (basic front-to-back circulation shown).
Shaft along +X (suction at -X), cut plane y = 0.
"""
import math
from mathutils import Matrix
from pumpforge.core import (Model, lathe, lathe_split, ring_profile, cyl, box, csg, split, join, merge_halves, split_faces,
                            split_many, rotate, TAU)
from pumpforge.parts import (H_FRAME, place, radial_impeller, volute_casing, add_impeller, nozzle_bolts, volute_flow,
                             pipe, add_baseplate)

ID = 'canned_motor_pump'
CZ = 0.30
BP = 0.08


def build(out_dir):
    m = Model(ID, 'Canned Motor Pump (Sealless, Close-Coupled)', 'A · Centrifugal & Special Hydraulic Pumps', META)
    Mx = H_FRAME(0.0, CZ)
    core, shroud, imp = radial_impeller('impeller', 0.19, 0.015, 0.04, 0.014, n_blades=6, mat='stainless', wrap=1.7)
    cas, geo = volute_casing('casing', imp, 'stainless', r_suc=0.04, L_suc=0.12, r_dis=0.032, H_dis=0.2)
    place(cas, Mx)
    zb = geo['z_back']
    cfoot = box('cfoot', (0.06, 0.24, CZ - geo['r3'] - BP), (zb - 0.035, 0, BP + (CZ - geo['r3'] - BP) / 2 + 0.004), 'stainless', bevel=0.004)
    cas = csg('casing', [cas, cfoot], [], 'stainless')
    cb, cf = split(cas)
    nb = [nozzle_bolts('dfb', 8, 2 * (geo['r_dis'] + 0.03), 0.02, geo['H_dis'] + CZ, geo['H_dis'] + CZ + 0.014, 'Z',
                       (imp['zc'], geo['Rend'], 0), phase=math.pi / 8),
          nozzle_bolts('sfb', 8, 2 * (geo['r_suc'] + 0.03), 0.02, -geo['L_suc'], -geo['L_suc'] - 0.014, 'X', (0, 0, CZ),
                       phase=math.pi / 8)]
    nbb, nbf = split_faces(join('nozb', nb), 'y', 0.0)
    p = m.part('casing', 'Volute Casing', 'casing', section='split', explode=(-0.4, 0, 0), info={'ref': 'volute_casing'})
    p.add_split(join('cb', [cb, nbb]), join('cf', [cf, nbf]), smooth_angle=40)
    add_impeller(m, 'impeller', 'Closed Impeller', core, shroud, Mx, (0, 0, CZ), explode=(-0.22, 0, 0))

    R = 0.135
    x_a = zb                     # adapter (front bearing housing) start
    x_m0, x_m1 = x_a + 0.06, x_a + 0.40   # motor housing
    # adapter / front bearing housing
    ad = lathe('adapter', [(0.03, x_a), (geo['r_bf'], x_a), (geo['r_bf'], x_a + 0.018), (R * 0.95, x_a + 0.03),
                           (R * 0.95, x_m0), (0.055, x_m0), (0.055, x_a + 0.035), (0.03, x_a + 0.03)],
               'stainless', 96, axis='X', center=(0, 0, CZ))
    p = m.part('adapter', 'Adapter & Front Bearing Housing', 'casing', section='split', explode=(-0.1, 0, 0))
    p.add_split(*split(ad), smooth_angle=40)
    # motor housing (stator frame) with feet and terminal box
    mh_o = [lathe('mh', [(R * 0.86, x_m0), (R, x_m0), (R, x_m1), (R * 0.86, x_m1)], 'paint_green', 96, axis='X', center=(0, 0, CZ)),
            box('tbx', (0.13, 0.12, 0.08), ((x_m0 + x_m1) / 2, 0, CZ + R + 0.03), 'paint_green', bevel=0.006),
            box('tbl', (0.14, 0.13, 0.012), ((x_m0 + x_m1) / 2, 0, CZ + R + 0.075), 'paint_green', bevel=0.003)]
    for xx in (x_m0 + 0.06, x_m1 - 0.06):
        mh_o.append(box('mf', (0.05, 0.22, CZ - BP - R * 0.7), (xx, 0, BP + (CZ - BP - R * 0.7) / 2 + 0.01), 'paint_green', bevel=0.004))
    for i in range(10):
        mh_o.append(lathe(f'rib{i}', [(R - 0.002, x_m0 + 0.03 + i * 0.031), (R + 0.008, x_m0 + 0.03 + i * 0.031),
                                      (R + 0.008, x_m0 + 0.036 + i * 0.031), (R - 0.002, x_m0 + 0.036 + i * 0.031)],
                          'paint_green', 96, axis='X', center=(0, 0, CZ)))
    mh = csg('motor_housing', mh_o, [cyl('mhi', R * 0.86, x_m0 - 0.01, x_m1 + 0.01, 'paint_green', 96, axis='X', center=(0, 0, CZ))],
             'paint_green')
    plate = box('np', (0.1, 0.003, 0.06), ((x_m0 + x_m1) / 2 + 0.06, -R - 0.0105, CZ), 'nameplate', bevel=0.0015)
    hb, hf = split(mh)
    p = m.part('motor_housing', 'Motor Housing (Secondary Containment)', 'motor', section='split', explode=(0.12, 0, 0))
    p.add_split(hb, join('mhf', [hf, plate]), smooth_angle=40)
    # stator core + windings
    x_s0, x_s1 = x_m0 + 0.05, x_m1 - 0.05
    st = [lathe_split('st', [(0.078, x_s0), (R * 0.86, x_s0), (R * 0.86, x_s1), (0.078, x_s1)], 'lamination', 96, axis='X', center=(0, 0, CZ)),
          lathe_split('w1', [(0.079, x_s0 - 0.035), (0.115, x_s0 - 0.035), (0.115, x_s0), (0.079, x_s0)], 'copper', 64, axis='X', center=(0, 0, CZ)),
          lathe_split('w2', [(0.079, x_s1), (0.115, x_s1), (0.115, x_s1 + 0.035), (0.079, x_s1 + 0.035)], 'copper', 64, axis='X', center=(0, 0, CZ))]
    p = m.part('stator', 'Stator Core & Windings', 'motor', section='split', explode=(0.12, 0, 0.42), info={'ref': 'stator'})
    p.add_split(*merge_halves('stator', st))
    p = m.part('stator_liner', 'Stator Liner (Stator Can)', 'motor', section='split', explode=(0.12, 0, 0.3))
    p.add_split(*lathe_split('can_s', ring_profile(0.0755, 0.0775, x_m0 - 0.004, x_m1 + 0.004), 'chrome', 96, axis='X', center=(0, 0, CZ)))
    # rotor + shaft (+ rotor can) — spins with impeller
    rot = [cyl('rcore', 0.072, x_s0 + 0.002, x_s1 - 0.002, 'lamination', 96, axis='X', center=(0, 0, CZ)),
           lathe('rcan', ring_profile(0.072, 0.0735, x_s0 - 0.006, x_s1 + 0.006), 'chrome', 96, axis='X', center=(0, 0, CZ)),
           cyl('shaft', 0.014, imp['z_back'] - 0.01, x_m1 + 0.06, 'stainless', 32, axis='X', center=(0, 0, CZ), ch=0.002),
           cyl('sleeve1', 0.0185, x_a + 0.035, x_a + 0.075, 'silicon_carbide', 32, axis='X', center=(0, 0, CZ)),
           cyl('sleeve2', 0.0185, x_m1 + 0.01, x_m1 + 0.05, 'silicon_carbide', 32, axis='X', center=(0, 0, CZ))]
    p = m.part('rotor', 'Canned Rotor & Shaft', 'rotating_element', pivot=(x_m0, 0, CZ), explode=(0.1, -0.42, 0), info={'ref': 'rotor_canned'})
    rb, rf = split_many('rotor', rot[:2])
    p.add(join('rotor_shaft', rot[2:]), 'keep')
    p.add(rb, 'back'); p.add(rf, 'front')
    p.spin('X', 2)
    # product-lubricated bearings
    br = merge_halves('brg', [lathe_split('b1', ring_profile(0.0187, 0.03, x_a + 0.038, x_a + 0.072), 'carbon', 48, axis='X', center=(0, 0, CZ)),
                               lathe_split('b2', ring_profile(0.0187, 0.03, x_m1 + 0.013, x_m1 + 0.047), 'carbon', 48, axis='X', center=(0, 0, CZ))])
    p = m.part('bearings', 'Product-Lubricated Journal Bearings', 'bearings', section='split', explode=(0.1, -0.28, 0),
               info={'ref': 'product_bearings'})
    p.add_split(*br)
    # rear bearing housing / end cover with bearing monitor
    rc = lathe('rear_cover', [(0, x_m1), (R, x_m1), (R, x_m1 + 0.02), (0.06, x_m1 + 0.03), (0.06, x_m1 + 0.075),
                              (0.03, x_m1 + 0.085), (0, x_m1 + 0.085)], 'stainless', 96, axis='X', center=(0, 0, CZ))
    rc = csg('rear_cover', [rc], [lathe('rci', [(0, x_m1 - 0.01), (0.03, x_m1 - 0.01), (0.03, x_m1 + 0.05), (0.016, x_m1 + 0.06),
                                                (0, x_m1 + 0.06)], 'stainless', 48, axis='X', center=(0, 0, CZ))], 'stainless')
    p = m.part('rear_cover', 'Rear Bearing Housing & End Cover', 'casing', section='split', explode=(0.45, 0, 0))
    p.add_split(*split(rc), smooth_angle=40)
    mon = join('monitor', [cyl('mon', 0.028, x_m1 + 0.085, x_m1 + 0.13, 'paint_yellow', 48, axis='X', center=(0, 0, CZ), ch=0.004),
                           cyl('mong', 0.022, x_m1 + 0.13, x_m1 + 0.136, 'ptfe', 48, axis='X', center=(0, 0, CZ))])
    p = m.part('bearing_monitor', 'Bearing Wear Monitor', 'instrumentation', explode=(0.6, 0, 0))
    p.add(mon)
    # circulation line: discharge -> rear cover
    xd = imp['zc']
    path = [(xd + 0.035, geo['Rend'], CZ + 0.12), (0.10, geo['Rend'], CZ + 0.12), (0.10, 0.07, CZ + R + 0.13),
            (x_m1 + 0.07, 0.07, CZ + R + 0.13), (x_m1 + 0.07, 0.04, CZ + 0.06)]
    cl = pipe('circ', path, 0.007, 'stainless', 16, bend=0.03)
    p = m.part('circulation_line', 'Circulation Line (Discharge to Motor)', 'circulation', explode=(0.05, 0, 0.25))
    p.add(cl, smooth_angle=60)
    add_baseplate(m, -0.2, x_m1 + 0.2, 0.36, BP)

    suc, dis = volute_flow(imp, geo, Mx, 0.25)
    m.flow('flow_suction', suc, 'flow_suction', 0.006, 0.12)
    m.flow('flow_discharge', dis, 'flow_discharge', 0.006, 0.12)
    m.flow('flow_circulation', path + [(x_m1 + 0.05, 0.0, CZ + 0.05), (x_m1 + 0.02, 0.0, CZ + 0.076), (x_m0, 0.0, CZ + 0.0745),
                                       (x_a + 0.04, 0.0, CZ + 0.025), (imp['z_back'] - 0.005, 0.0, CZ + 0.03)],
           'flow_discharge', 0.004, 0.08)
    return m.export(out_dir)


META = {
    'summary': ('The motor rotor and the pump impeller are on one shaft inside a fully enclosed pressure boundary. '
                'The stator windings are sealed from the pumped liquid by a thin stator liner (can); the rotor is '
                'sealed by its own can. A small flow of pumped liquid circulates through the motor gap to remove '
                'heat and lubricate the sleeve bearings. There is no shaft seal and no coupling, so leakage paths '
                'are eliminated; the motor housing gives secondary containment.'),
    'classification': {'family': 'Rotodynamic (centrifugal), radial flow', 'configuration': 'Sealless, close-coupled canned motor',
                       'api_610_type': 'Sealless; covered by API 685'},
    'model_configuration': {'circulation': 'Basic front-to-back circulation from discharge (other arrangements: reverse circulation, high-temperature with external cooler, self-venting for volatile liquids)',
                            'bearings': 'Carbon/graphite journals on SiC sleeves; bearing wear monitor on rear cover',
                            'cans': 'Hastelloy C / stainless thin-wall liners (typical)'},
    'standards': [
        {'id': 'API 685', 'title': 'Sealless Centrifugal Pumps for Petroleum, Petrochemical, and Gas Industry Process Service',
         'relevance': 'Covers canned motor and magnetic drive pumps.', 'edition': 'to be verified'},
        {'id': 'ISO 15783', 'title': 'Seal-less rotodynamic pumps — Class II — Specification', 'relevance': 'General sealless pump requirements.', 'edition': 'to be verified'},
        {'id': 'IEC 60079 series', 'title': 'Explosive atmospheres', 'relevance': 'Canned motors in hazardous areas are certified to the applicable protection concept; confirm per unit.', 'edition': 'to be verified'},
    ],
    'references': ['Karassik et al., Pump Handbook — sealless pumps.', 'Manufacturer canned motor pump application guides (generic practice).'],
    'components': {
        'adapter': {'function': 'Connects casing to motor and houses the front bearing.', 'construction': 'Machined adapter with bearing bore and circulation passages.',
                    'material': 'Stainless steel or carbon steel.', 'operating_conditions': 'Part of the primary pressure boundary.',
                    'failure_modes': ['Bearing bore wear', 'Gasket leakage'], 'inspection': ['Bore and gasket faces at overhaul']},
        'motor_housing': {'function': 'Holds the stator and provides secondary containment if the stator liner fails.',
                          'construction': 'Welded/fabricated cylindrical housing with terminal box and feet.',
                          'material': 'Carbon or stainless steel.', 'operating_conditions': 'Rated for full system pressure on many designs.',
                          'failure_modes': ['Liner breach floods stator space', 'Terminal box seal failure'], 'inspection': ['Insulation resistance trend', 'Terminal seals']},
        'stator_liner': {'function': 'Thin can that separates the stator windings from the pumped liquid.',
                         'construction': 'Welded thin-wall sleeve supported by the stator bore.', 'material': 'Hastelloy C, stainless steel.',
                         'operating_conditions': 'Eddy-current losses in the can add heat removed by circulation.',
                         'failure_modes': ['Wear-through from rotor rub after bearing wear', 'Corrosion'], 'inspection': ['Bearing monitor readings to prevent rub']},
        'rotor_canned': {'function': 'Squirrel-cage rotor sealed in its own can; carries the impeller on the common shaft.',
                         'construction': 'Laminated rotor with welded can and end covers.', 'material': 'Electrical steel, stainless/Hastelloy can.',
                         'operating_conditions': 'Runs submerged in the circulating liquid.', 'failure_modes': ['Can breach', 'Imbalance'],
                         'inspection': ['Can condition at overhaul']},
        'product_bearings': {'function': 'Support the rotor/impeller shaft, lubricated by the pumped liquid.',
                             'construction': 'Carbon-graphite or SiC journal bearings with thrust faces.', 'material': 'Carbon-graphite, silicon carbide.',
                             'operating_conditions': 'Cannot run dry; vapour in the motor gap must be avoided (venting, sufficient margin to boiling).',
                             'failure_modes': ['Dry running', 'Abrasive wear', 'Vapour formation in circulation path'],
                             'inspection': ['Bearing wear monitor (axial/radial)', 'Clearance at overhaul']},
        'rear_cover': {'function': 'Closes the motor end, houses the rear bearing and returns circulation flow.', 'construction': 'Bolted end cover.',
                       'material': 'Stainless/carbon steel.', 'operating_conditions': 'Primary pressure boundary.', 'failure_modes': ['Gasket leakage'],
                       'inspection': ['Gasket faces']},
        'bearing_monitor': {'function': 'Indicates bearing wear (rotor position) so the pump can be stopped before the cans are damaged.',
                            'construction': 'Electrical or mechanical rotor-position monitor on the rear cover (e.g. "TRG"-type indicators).',
                            'material': 'Stainless steel housing.', 'operating_conditions': 'Continuous monitoring; often linked to alarm/trip.',
                            'failure_modes': ['Sensor fault'], 'inspection': ['Record readings; test alarm']},
        'circulation_line': {'function': 'Takes a small flow from discharge through the motor for cooling and bearing lubrication.',
                             'construction': 'Small-bore tube, sometimes with filter or heat exchanger.', 'material': 'Stainless steel.',
                             'operating_conditions': 'Blockage quickly overheats the motor and bearings.', 'failure_modes': ['Clogging', 'Vapour lock'],
                             'inspection': ['Check flow/temperature rise across motor']},
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
