"""
Hydraulic Power Pack — oil reservoir with a vertical electric motor on the lid
driving a submerged external gear pump through a bell housing and coupling;
suction strainer, relief valve, directional valve manifold, bladder accumulator,
return-line filter, air-oil cooler, level gauge and breather.  Axis Z.
"""
import math
from pumpforge.core import Model, lathe, lathe_split, ring_profile, cyl, box, csg, split, join, merge_halves, split_many, extrude_poly, TAU
from pumpforge.parts import add_motor_v, pipe, pressure_gauge
from pumpforge.shapes import involute_gear_profile, sweep_tube
from pumpforge.common_meta import C

ID = 'hydraulic_power_pack_pump'
LX, LY, LZ = 0.9, 0.6, 0.5     # tank
ZT = 0.12 + LZ                  # lid top (tank on 0.12 m feet)


def build(out_dir):
    m = Model(ID, 'Hydraulic Power Pack (Motor–Pump Unit on Reservoir)', 'E · Industrial Pump Applications', META)
    t = 0.006
    tank = csg('tank', [box('to', (LX, LY, LZ), (0, 0, 0.12 + LZ / 2), 'paint_grey', bevel=0.01)] +
               [box(f'tf{i}', (0.06, 0.06, 0.12), (sx * (LX / 2 - 0.05), sy * (LY / 2 - 0.05), 0.06), 'paint_grey') for i, (sx, sy) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1)))],
               [box('ti', (LX - 2 * t, LY - 2 * t, LZ), (0, 0, 0.12 + LZ / 2 + t), 'paint_grey')], 'paint_grey')
    oil = box('oil', (LX - 2 * t - 0.002, LY - 2 * t - 0.002, LZ * 0.7), (0, 0, 0.12 + t + LZ * 0.35), 'flow_suction')
    p = m.part('reservoir', 'Oil Reservoir (Tank) with Baffle', 'reservoir', section='split', explode=(0, 0, -0.3), info={'ref': 'hpu_tank'})
    baffle = box('baffle', (0.006, LY - 0.03, LZ * 0.6), (0.05, 0, 0.12 + LZ * 0.32), 'paint_grey')
    b, f = split(tank)
    bb2, bf2 = split(baffle)
    p.add_split(join('tb', [b, bb2]), join('tf', [f, bf2]), smooth_angle=40)
    lid = csg('lid', [box('lid', (LX + 0.03, LY + 0.03, 0.02), (0, 0, ZT + 0.01), 'paint_grey', bevel=0.004)],
              [cyl('lh', 0.09, ZT - 0.01, ZT + 0.03, 'paint_grey', 48, center=(-0.15, 0, 0))], 'paint_grey')
    p = m.part('tank_lid', 'Tank Lid (Pump Mounting Plate)', 'reservoir', section='split', explode=(0, 0, 0.25), info={'ref': 'hpu_lid'})
    p.add_split(*split(lid), smooth_angle=40)
    # bell housing + coupling + submerged gear pump
    xm = -0.15
    bell = csg('bell', [lathe('bh', [(0.0, ZT + 0.02), (0.13, ZT + 0.02), (0.13, ZT + 0.04), (0.09, ZT + 0.06), (0.09, ZT + 0.2), (0.13, ZT + 0.22), (0.13, ZT + 0.24), (0, ZT + 0.24)],
                               'aluminium', 64, center=(xm, 0, 0))],
               [cyl('bhi', 0.08, ZT + 0.0, ZT + 0.25, 'aluminium', 48, center=(xm, 0, 0)), box('bhw', (0.1, 0.3, 0.09), (xm, 0, ZT + 0.13), 'aluminium', bevel=0.01)], 'aluminium')
    p = m.part('bell_housing', 'Bell Housing (Motor–Pump Adapter)', 'drive', section='split', explode=(0, 0, 0.35), info={'ref': 'hpu_bell'})
    p.add_split(*split(bell), smooth_angle=40)
    cp = join('coupling', [cyl('c1', 0.035, ZT + 0.1, ZT + 0.13, 'steel', 32, center=(xm, 0, 0)), cyl('c2', 0.035, ZT + 0.135, ZT + 0.165, 'steel', 32, center=(xm, 0, 0)),
                           cyl('cs', 0.03, ZT + 0.128, ZT + 0.137, 'rubber', 8, center=(xm, 0, 0)), cyl('ps', 0.012, ZT - 0.3, ZT + 0.12, 'steel', 24, center=(xm, 0, 0))])
    p = m.part('coupling_shaft', 'Jaw Coupling & Pump Drive Shaft', 'drive', pivot=(xm, 0, ZT), explode=(0.3, 0, 0.35), info={'ref': 'coupling_flex'})
    p.add(cp, smooth_angle=40); p.spin('Z', 3)
    zp = ZT - 0.3
    gp_body = csg('gp', [box('gpb', (0.13, 0.09, 0.07), (xm, 0.0, zp), 'aluminium', bevel=0.008),
                         cyl('gpo', 0.014, zp, ZT - 0.0, 'steel', 24, center=(xm + 0.04, 0, 0))],
                  [cyl('g1', 0.0255, zp - 0.03, zp + 0.03, 'aluminium', 48, center=(xm, 0.0, 0)), cyl('g2', 0.0255, zp - 0.03, zp + 0.03, 'aluminium', 48, center=(xm + 0.0, 0.048, 0)),
                   cyl('gsi', 0.012, zp - 0.05, zp, 'aluminium', 24, center=(xm - 0.04, 0.024, 0))], 'aluminium')
    p = m.part('gear_pump', 'Gear Pump Body (Submerged)', 'pump', section='split', explode=(0, -0.4, 0.0), info={'ref': 'hpu_pump'})
    p.add_split(*split(gp_body), smooth_angle=40)
    gpf, _ = involute_gear_profile(0.004, 12, 25.0, steps=5)
    for i, (cy, sg, ph) in enumerate(((0.0, 1, 0.0), (0.048, -1, math.pi / 12))):
        pts = [(x * math.cos(ph) - y * math.sin(ph) + xm, y * math.cos(ph) + x * math.sin(ph) + cy) for x, y in gpf]
        g = extrude_poly(f'gear{i}', pts, zp - 0.025, zp + 0.025, 'steel', plane='XY')
        p = m.part(f'pump_gear_{i + 1}', f'Pump Gear {i + 1}', 'pump', pivot=(xm, cy, zp), explode=(0, -0.55, -0.1 * i), info={'ref': 'hpu_gear'})
        p.add(g, smooth_angle=30); p.spin('Z', 3 * sg)
    strainer = join('strainer', [cyl('st', 0.035, 0.18, 0.3, 'stainless', 32, center=(xm - 0.04, 0.024, 0)),
                                 pipe('stp', [(xm - 0.04, 0.024, 0.3), (xm - 0.04, 0.024, zp - 0.04)], 0.012, 'steel', 16)])
    p = m.part('suction_strainer', 'Suction Strainer', 'pump', explode=(0, -0.3, -0.25), info={'ref': 'hpu_strainer'})
    p.add(strainer, smooth_angle=50)
    add_motor_v(m, 'm_', ZT + 0.265, 0.11, 0.32, 0.016, 0.1, explode_dz=0.6, flange_r=0.135, revs=3)
    for prt in m.parts:
        if prt.id.startswith('m_'):
            prt.pivot.x += xm
            prt.node.location.x += xm
    # manifold block with relief valve and solenoid valves
    mx = 0.22
    mb = join('manifold', [box('mb', (0.2, 0.14, 0.08), (mx, 0.0, ZT + 0.06), 'steel', bevel=0.004),
                           cyl('rv', 0.018, mx - 0.1, mx - 0.05, 'steel', 6, axis='X', center=(0, -0.04, ZT + 0.06)),
                           cyl('rvk', 0.015, mx - 0.13, mx - 0.1, 'thermoplastic', 24, axis='X', center=(0, -0.04, ZT + 0.06))] +
              [box(f'sv{i}', (0.06, 0.12, 0.05), (mx - 0.05 + i * 0.08, 0.0, ZT + 0.125), 'paint_blue', bevel=0.004) for i in range(2)] +
              [cyl(f'sol{i}{s}', 0.02, 0.0, 0.05, 'thermoplastic', 24, axis='Y', center=(mx - 0.05 + i * 0.08, s * 0.085, ZT + 0.125)) for i in range(2) for s in (1, -1)])
    p = m.part('valve_manifold', 'Valve Manifold: Relief Valve + Solenoid Directional Valves', 'valves', explode=(0.3, 0, 0.3), info={'ref': 'hpu_valves'})
    p.add(mb, smooth_angle=40)
    acc = join('accumulator', [lathe('acc', [(0, -0.2), (0.06, -0.17), (0.07, -0.1), (0.07, 0.1), (0.06, 0.17), (0, 0.2)], 'paint_red', 48, center=(0.36, 0.18, ZT + 0.25)),
                               cyl('accv', 0.012, ZT + 0.45, ZT + 0.48, 'brass', 12, center=(0.36, 0.18, 0))])
    p = m.part('accumulator', 'Bladder Accumulator', 'accumulator', explode=(0.3, 0.3, 0.3), info={'ref': 'hpu_accumulator'})
    p.add(acc, smooth_angle=50)
    rf = join('return_filter', [cyl('rf', 0.05, ZT + 0.0, ZT + 0.14, 'aluminium', 48, center=(0.3, -0.18, 0), ch=0.006),
                                cyl('rfe', 0.035, ZT - 0.2, ZT, 'paint_yellow', 32, center=(0.3, -0.18, 0))])
    p = m.part('return_filter', 'Return-Line Filter', 'filtration', explode=(0.3, -0.3, 0.3), info={'ref': 'hpu_filter'})
    p.add(rf, smooth_angle=40)
    brt = join('breather', [cyl('br', 0.04, ZT + 0.02, ZT + 0.09, 'thermoplastic', 32, center=(-0.38, -0.2, 0), ch=0.008)])
    lg = join('level', [box('lg', (0.03, 0.012, 0.3), (0.2, -LY / 2 - 0.006, 0.12 + LZ * 0.5), 'thermoplastic'),
                        box('lgw', (0.016, 0.004, 0.26), (0.2, -LY / 2 - 0.013, 0.12 + LZ * 0.5), 'flow_suction')])
    p = m.part('breather_level', 'Filler-Breather & Level/Temperature Gauge', 'reservoir', explode=(0, -0.3, 0), info={'ref': 'hpu_breather'})
    p.add(join('bl', [brt, lg]), smooth_angle=40)
    cool = join('cooler', [box('co', (0.06, 0.4, 0.3), (LX / 2 + 0.06, 0, ZT - 0.18), 'aluminium', bevel=0.005),
                           cyl('cf', 0.14, LX / 2 + 0.09, LX / 2 + 0.12, 'thermoplastic', 48, axis='X', center=(0, 0, ZT - 0.18))])
    p = m.part('oil_cooler', 'Air–Oil Cooler', 'cooling', explode=(0.4, 0, 0), info={'ref': 'hpu_cooler'})
    p.add(cool, smooth_angle=40)
    pp = [pipe('pl1', [(xm + 0.04, 0, ZT + 0.0), (xm + 0.04, 0, ZT + 0.05), (mx - 0.1, 0, ZT + 0.05)], 0.01, 'steel', 12, bend=0.03),
          pipe('pl2', [(mx + 0.1, 0.0, ZT + 0.06), (0.3, 0.0, ZT + 0.06), (0.3, -0.18, ZT + 0.14)], 0.01, 'steel', 12, bend=0.03),
          pipe('pl3', [(mx + 0.1, 0.03, ZT + 0.06), (0.36, 0.18, ZT + 0.06)], 0.01, 'steel', 12)]
    p = m.part('tubing', 'Pressure & Return Tubing', 'system_piping', explode=(0, 0, 0.4), info={'ref': 'pipework'})
    p.add(join('tubing', pp), smooth_angle=50)
    g = pressure_gauge('pg', (mx + 0.05, -0.07, ZT + 0.1))
    p = m.part('pressure_gauge', 'System Pressure Gauge', 'instrumentation', explode=(0, -0.2, 0.4), info={'ref': 'pressure_gauge'})
    p.add(g, smooth_angle=50)
    m.flow('flow_suction', [(xm - 0.04, 0.024, 0.2), (xm - 0.04, 0.024, zp - 0.04), (xm, 0.024, zp)], 'flow_suction', 0.005, 0.08)
    m.flow('flow_pressure', [(xm + 0.04, 0.0, zp), (xm + 0.04, 0.0, ZT + 0.05), (mx, 0.0, ZT + 0.05), (mx + 0.12, 0.0, ZT + 0.06), (0.36, 0.18, ZT + 0.06)], 'flow_discharge', 0.005, 0.08)
    m.flow('flow_return', [(0.5, -0.3, ZT + 0.14), (0.3, -0.18, ZT + 0.14), (0.3, -0.18, ZT - 0.2)], 'flow_suction', 0.005, 0.08)
    return m.export(out_dir)


META = {
    'summary': ('A hydraulic power unit (power pack) converts electrical power into hydraulic power for cylinders and motors. '
                'A motor drives a positive-displacement pump (here a submerged gear pump) that draws oil from the reservoir '
                'through a strainer and delivers it to a valve manifold. A relief valve limits maximum pressure; directional '
                'valves route oil to the actuators; an accumulator stores energy and absorbs shocks; returning oil passes '
                'through a filter and cooler back to the tank, where it settles, releases air and cools.'),
    'classification': {'family': 'Package / system (positive displacement pump)', 'configuration': 'Vertical motor-pump unit on reservoir lid, submerged gear pump'},
    'model_configuration': {'pump': 'External gear pump (vane or axial piston pumps are also common)', 'tank_rule_note': 'Reservoir volume often sized at ~3–5 × pump flow per minute (rule of thumb — verify).',
                            'valves': 'Relief valve + 2 solenoid directional valves (CETOP/ISO 4401 pattern)'},
    'standards': [
        {'id': 'ISO 4413', 'title': 'Hydraulic fluid power — General rules and safety requirements for systems and their components', 'relevance': 'Core safety/design standard for hydraulic systems.', 'edition': 'to be verified'},
        {'id': 'ISO 4401', 'title': 'Hydraulic fluid power — Four-port directional control valves — Mounting surfaces', 'relevance': 'Valve interface pattern.', 'edition': 'to be verified'},
        {'id': 'ISO 4406', 'title': 'Hydraulic fluid power — Fluids — Method for coding the level of contamination by solid particles', 'relevance': 'Cleanliness targets.', 'edition': 'to be verified'},
        {'id': 'ISO 1219', 'title': 'Fluid power systems — Graphical symbols and circuit diagrams', 'relevance': 'Schematics.', 'edition': 'to be verified'},
    ],
    'references': ['Parker / Bosch Rexroth hydraulic trainer manuals (generic practice).', 'ISO 4413 (scope summary).'],
    'components': {
        'hpu_tank': C('Stores oil, allows air release and settling, dissipates heat.', 'Welded steel tank with baffle separating return and suction zones, drain and clean-out covers.', 'Steel (painted inside), stainless, aluminium.',
                      'Oil level and temperature must stay within limits.', ['Contamination', 'Water condensation', 'Overheating'], ['Oil analysis (ISO 4406)', 'Level/temperature']),
        'hpu_lid': C('Mounting plate for motor-pump group, valves and filters.', 'Thick steel plate bolted to the tank with gasket.', 'Steel.', 'Seals tank from dirt.', ['Gasket leaks'], ['Visual']),
        'hpu_bell': C('Aligns motor and pump and encloses the coupling.', 'Machined aluminium bell housing with registers.', 'Aluminium/cast iron.', 'Guarantees concentricity.', ['Damage to registers'], ['Visual']),
        'hpu_pump': C('Converts mechanical power into hydraulic flow.', 'Fixed-displacement external gear pump (shown submerged).', 'Aluminium body, steel gears.', 'Pressure set by load and relief valve.',
                      ['Wear from contaminated oil', 'Cavitation if strainer blocked'], ['Case temperature, noise', 'Flow test']),
        'hpu_gear': C('Meshing gears that carry oil from the inlet to the outlet around the housing.', 'Involute spur gears (one driven, one idler) in a figure-8 housing.',
                      'Hardened steel.', 'Lubricated by the hydraulic oil.', ['Tooth and side-plate wear'], ['Volumetric efficiency test']),
        'hpu_strainer': C('Protects the pump from large particles.', 'Wire-mesh suction strainer.', 'Stainless mesh.', 'Must not restrict suction.', ['Clogging → cavitation'], ['Clean periodically']),
        'hpu_valves': C('Control pressure (relief valve) and direction of flow to actuators.', 'Manifold block with relief cartridge and solenoid-operated directional valves.', 'Steel/cast iron.',
                        'Solenoid voltage per design.', ['Spool sticking from dirt', 'Coil burn-out'], ['Function test']),
        'hpu_accumulator': C('Stores pressurised oil, absorbs shocks and pulsation, provides emergency flow.', 'Steel shell with nitrogen-filled bladder and gas valve.', 'Steel, NBR bladder.',
                             'Pre-charge pressure must be checked; pressure vessel rules apply.', ['Loss of pre-charge', 'Bladder rupture'], ['Pre-charge check']),
        'hpu_filter': C('Removes particles from returning oil.', 'Tank-top return filter with bypass valve and clogging indicator.', 'Aluminium housing, glass-fibre element.', 'β-ratio rating per ISO 16889.', ['Element clogging → bypass'], ['Indicator, change element']),
        'hpu_breather': C('Lets air in/out as level changes while filtering it; shows level and temperature.', 'Filler-breather cap; sight level gauge with thermometer.', 'Polymer/steel.', 'Desiccant breathers in humid areas.',
                          ['Clogged breather', 'Broken sight glass'], ['Visual']),
        'hpu_cooler': C('Removes heat generated by losses.', 'Fan-cooled aluminium core.', 'Aluminium.', 'Sized for heat load.', ['Fin fouling'], ['Clean fins']),
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
