"""
Firewater Pump Package — packaged fire pump set (NFPA 20 style): horizontal
split-case fire pump driven by a diesel engine through a drive shaft, jockey
(pressure-maintenance) pump, fire pump and jockey pump controllers, main relief
valve, test header and station valves on a common skid.  System-level model.
"""
import math
from pumpforge.core import Model, lathe, cyl, box, csg, split, join, split_many, rotate, TAU
from pumpforge.parts import (add_coupling, add_baseplate, hollow_pipe, gate_valve, check_valve, pressure_gauge, add_motor_v, pipe)
from pumpforge.common_meta import C
from pumps import cooling_water_pump as cw

ID = 'firewater_pump_package'
CZ, BP = cw.CZ, cw.BP


def extra(m, g):
    xc = 0.89
    # drive shaft (cardan) + engine flywheel coupling
    ds = join('driveshaft', [cyl('ds', 0.03, xc, xc + 0.42, 'steel', 24, axis='X', center=(0, 0, CZ)),
                             cyl('dy1', 0.07, xc, xc + 0.05, 'steel_dark', 32, axis='X', center=(0, 0, CZ)),
                             cyl('dy2', 0.07, xc + 0.37, xc + 0.42, 'steel_dark', 32, axis='X', center=(0, 0, CZ))])
    p = m.part('drive_shaft', 'Drive Shaft (Cardan) between Pump and Engine', 'power_transmission', pivot=(xc, 0, CZ), explode=(0.3, 0, 0.3), info={'ref': 'fw_driveshaft'})
    p.add(ds, smooth_angle=40); p.spin('X', 2)
    gd = lathe('dsg', [(0.12, xc - 0.02), (0.123, xc - 0.02), (0.123, xc + 0.44), (0.12, xc + 0.44)], 'paint_yellow', 48, a0=-1.9, a1=1.9, axis='X',
               center=(0, 0, CZ), cap_mat='paint_yellow')
    p = m.part('shaft_guard', 'Drive Shaft Guard', 'power_transmission', section='hide', explode=(0.3, 0, 0.6), info={'ref': 'coupling_guard'})
    p.add(gd, smooth_angle=50)
    # diesel engine
    xe = xc + 0.44
    eng_o = [lathe('bell', [(0.0, xe), (0.32, xe), (0.32, xe + 0.12), (0.0, xe + 0.12)], 'paint_red', 64, axis='X', center=(0, 0, CZ)),
             box('blk', (1.1, 0.5, 0.55), (xe + 0.67, 0, CZ + 0.02), 'paint_red', bevel=0.03),
             box('pan', (1.0, 0.42, 0.22), (xe + 0.65, 0, CZ - 0.33), 'paint_red', bevel=0.02),
             box('head', (1.05, 0.42, 0.18), (xe + 0.68, 0, CZ + 0.38), 'paint_red', bevel=0.02),
             box('rocker', (0.98, 0.32, 0.1), (xe + 0.68, 0, CZ + 0.52), 'paint_grey', bevel=0.03)]
    for i in range(6):
        eng_o.append(cyl(f'inj{i}', 0.015, CZ + 0.57, CZ + 0.62, 'steel', 12, center=(xe + 0.25 + i * 0.16, 0.08, 0)))
    eng = csg('engine', eng_o, [box('blki', (1.0, 0.4, 0.45), (xe + 0.67, 0, CZ + 0.02), 'paint_red', bevel=0.02)], 'paint_red')
    eb, ef = split(eng, 'y', 0.0)
    p = m.part('diesel_engine', 'Diesel Engine (Listed Fire-Pump Driver)', 'driver', section='split', explode=(0.8, 0, 0.3), info={'ref': 'fw_engine'})
    p.add_split(eb, ef, smooth_angle=40)
    # inline-6 running gear: crank throws (firing pairs 1-6, 2-5, 3-4), connecting rods and pistons
    r, Lr, REV = 0.05, 0.15, 2
    xs_cyl = [xe + 0.25 + i * 0.16 for i in range(6)]
    phase = [0.0, 2 * math.pi / 3, 4 * math.pi / 3, 4 * math.pi / 3, 2 * math.pi / 3, 0.0]
    crank_parts = [cyl('crk', 0.035, xe, xe + 1.15, 'steel', 32, axis='X', center=(0, 0, CZ), ch=0.004),
                   cyl('fw', 0.28, xe + 0.02, xe + 0.08, 'steel_dark', 64, axis='X', center=(0, 0, CZ), ch=0.006)]
    for x, a in zip(xs_cyl, phase):
        py, pz = -r * math.sin(a), r * math.cos(a)
        for dx in (-0.045, 0.045):
            web = box('web', (0.018, 0.06, r + 0.06), (x + dx, 0, CZ + (r) / 2), 'steel', bevel=0.004)
            crank_parts.append(rotate(web, a, 'X', (0, 0, CZ)))
        crank_parts.append(cyl('pin', 0.022, x - 0.045, x + 0.045, 'chrome', 24, axis='X', center=(0, py, CZ + pz)))
    crank = join('crank', crank_parts)
    p = m.part('crankshaft_flywheel', 'Crankshaft, Crank Throws & Flywheel', 'driver', pivot=(xe, 0, CZ), explode=(0.8, -0.8, 0.0), info={'ref': 'fw_flywheel'})
    p.add(crank, smooth_angle=40); p.spin('X', REV)
    from pumpforge.core import OPERATE_FRAMES
    pist = m.part('pistons', 'Pistons (6 Cylinders)', 'driver', pivot=(xe, 0, CZ), explode=(0.8, 0, 1.0), info={'ref': 'fw_pistons'})
    rods = m.part('connecting_rods', 'Connecting Rods', 'driver', pivot=(xe, 0, CZ), explode=(0.8, -0.5, 0.9), info={'ref': 'fw_conrods'})
    zp = lambda f: r * math.cos(f) + math.sqrt(Lr * Lr - (r * math.sin(f)) ** 2)
    for i, (x, a) in enumerate(zip(xs_cyl, phase)):
        pc = join(f'pis{i}', [cyl(f'pc{i}', 0.055, -0.01, 0.05, 'aluminium', 32, center=(xe, 0, CZ)),
                              cyl(f'pr{i}', 0.056, 0.035, 0.042, 'steel_dark', 32, center=(xe, 0, CZ))])
        mp = pist.add(pc, smooth_angle=40)
        rd = join(f'rod{i}', [box(f'rb{i}', (0.025, 0.03, Lr), (xe, 0, CZ - Lr / 2), 'steel', bevel=0.004),
                              cyl(f're{i}', 0.03, -0.018, 0.018, 'steel', 24, axis='X', center=(xe, 0, CZ - Lr)),
                              cyl(f'rs{i}', 0.018, -0.016, 0.016, 'steel', 24, axis='X', center=(xe, 0, CZ))])
        mr = rods.add(rd, smooth_angle=40)
        kp, kl, kr = [], [], []
        for k in range(61):
            f = a + TAU * REV * k / 60
            z = zp(f)
            fr = 1 + OPERATE_FRAMES * k / 60
            kp.append((fr, (x - xe, 0.0, z)))
            kl.append((fr, (x - xe, 0.0, z)))
            kr.append((fr, (math.asin(-r * math.sin(f) / Lr), 0.0, 0.0)))
        m.keyframes(mp, 'Operate', 'location', kp)
        m.keyframes(mr, 'Operate', 'location', kl)
        m.keyframes(mr, 'Operate', 'rotation_euler', kr)
    # heat exchanger (cooling loop from pump discharge), exhaust, air filter, batteries, fuel tank
    hx = join('hx', [cyl('hx', 0.09, xe + 0.2, xe + 0.9, 'paint_grey', 48, axis='X', center=(0, -0.38, CZ + 0.25), ch=0.01),
                     pipe('hxl', [(xe + 0.2, -0.38, CZ + 0.25), (xe + 0.1, -0.38, CZ + 0.25), (xe + 0.1, -0.38, CZ - 0.2)], 0.02, 'paint_grey', 12, bend=0.05)])
    exh = join('exhaust', [pipe('ex', [(xe + 0.68, 0.24, CZ + 0.38), (xe + 0.68, 0.38, CZ + 0.38), (xe + 0.68, 0.38, CZ + 1.6)], 0.06, 'steel_dark', 24, bend=0.1),
                           cyl('sil', 0.15, CZ + 1.0, CZ + 1.5, 'steel_dark', 48, center=(xe + 0.68, 0.38, 0), ch=0.02),
                           cyl('af', 0.13, xe + 1.2, xe + 1.45, 'paint_grey', 48, axis='X', center=(0, 0.0, CZ + 0.45), ch=0.02)])
    p = m.part('engine_auxiliaries', 'Heat Exchanger, Exhaust Silencer & Air Cleaner', 'driver', explode=(0.8, 0, 0.8), info={'ref': 'fw_aux'})
    p.add(join('aux', [hx, exh]), smooth_angle=40)
    bats = [box(f'bat{i}', (0.28, 0.18, 0.22), (xe + 0.4 + i * 0.35, -0.75, BP + 0.11), 'thermoplastic', bevel=0.01) for i in range(2)]
    p = m.part('batteries', 'Starting Batteries (2 Sets)', 'driver', explode=(0, -0.4, 0), info={'ref': 'fw_batteries'})
    p.add(join('batteries', bats), smooth_angle=40)
    ft = join('fuel_tank', [box('ft', (0.9, 0.5, 0.6), (xe + 0.6, 1.0, 1.3), 'paint_red', bevel=0.03)] +
              [box(f'ftl{i}', (0.05, 0.05, 1.0), (xe + 0.2 + sx * 0.0 + (0.8 if sx else 0), 1.0 + sy * 0.2, 0.5), 'paint_grey') for i, (sx, sy) in
               enumerate(((0, 1), (0, -1), (1, 1), (1, -1)))])
    p = m.part('fuel_tank', 'Diesel Day Tank on Stand', 'driver', explode=(0, 0.5, 0.3), info={'ref': 'fw_fuel'})
    p.add(ft, smooth_angle=40)
    # controllers
    ctl = [box('fpc', (0.6, 0.3, 1.1), (-1.2, 0.9, 0.75), 'paint_red', bevel=0.02), box('fpd', (0.02, 0.26, 0.9), (-0.89, 0.9, 0.78), 'paint_red'),
           box('jpc', (0.4, 0.25, 0.7), (-1.2, 1.45, 0.65), 'paint_red', bevel=0.02),
           box('stand', (0.7, 0.9, 0.2), (-1.2, 1.15, 0.1), 'paint_grey', bevel=0.01)]
    p = m.part('controllers', 'Fire Pump Controller & Jockey Pump Controller', 'controls', explode=(-0.5, 0.3, 0), info={'ref': 'control_panel'})
    p.add(join('controllers', ctl), smooth_angle=40)
    # jockey pump (vertical multistage) with its piping
    jx, jy = -0.7, 1.15
    jp = join('jockey', [cyl('jb', 0.08, BP, BP + 0.06, 'stainless', 48, center=(jx, jy, 0)), cyl('js', 0.065, BP + 0.06, BP + 0.55, 'stainless', 48, center=(jx, jy, 0)),
                         cyl('jt', 0.09, BP + 0.55, BP + 0.62, 'stainless', 48, center=(jx, jy, 0)),
                         pipe('jsuc', [(jx, jy, BP + 0.04), (jx, 0.5, BP + 0.04), (0.0, 0.5, BP + 0.04)], 0.025, 'stainless', 16, bend=0.05),
                         pipe('jdis', [(jx, jy, BP + 0.6), (jx, jy - 0.5, BP + 0.6), (jx, jy - 0.5, CZ + 0.5), (0.0, jy - 0.5, CZ + 0.5)], 0.02, 'stainless', 16, bend=0.05)])
    p = m.part('jockey_pump', 'Jockey (Pressure Maintenance) Pump', 'jockey', explode=(-0.3, 0.4, 0), info={'ref': 'fw_jockey'})
    p.add(jp, smooth_angle=40)
    n0 = len(m.parts)
    add_motor_v(m, 'jm_', BP + 0.64, 0.07, 0.24, 0.012, 0.0, explode_dz=0.4, flange_r=0.09, revs=3)
    from mathutils import Vector
    for prt in m.parts[n0:]:
        prt.pivot += Vector((jx, jy, 0))
        prt.node.location = prt.pivot
    # main relief valve + test header on discharge
    zd, yd = g['zend'], g['yend']
    rv = join('relief', [cyl('rvb', 0.09, zd + 0.1, zd + 0.3, 'paint_red', 48, center=(0, yd + 0.6, 0), ch=0.01),
                         lathe('rvc', [(0.0, zd + 0.3), (0.06, zd + 0.3), (0.03, zd + 0.55), (0.0, zd + 0.56)], 'paint_red', 48, center=(0, yd + 0.6, 0)),
                         pipe('rvp', [(0, yd + 0.6, zd), (0, yd + 0.6, zd + 0.1)], 0.06, 'paint_red', 24),
                         pipe('rvd', [(0, yd + 0.6, zd + 0.2), (0.4, yd + 0.6, zd + 0.2), (0.4, yd + 0.6, BP)], 0.05, 'paint_red', 24, bend=0.08)])
    p = m.part('main_relief_valve', 'Main Pressure Relief Valve', 'valves', explode=(0, 0.3, 0.4), info={'ref': 'fw_relief'})
    p.add(rv, smooth_angle=40)
    th = [pipe('thp', [(0, yd + 1.2, zd), (0, yd + 1.5, zd), (0, yd + 1.5, zd + 0.4), (-0.6, yd + 1.5, zd + 0.4), (0.6, yd + 1.5, zd + 0.4)], 0.07, 'paint_red', 24, bend=0.1)]
    for i, x in enumerate((-0.45, -0.15, 0.15, 0.45)):
        th.append(gate_valve(f'hv{i}', (x, yd + 1.62, zd + 0.4), 0.032, axis='Y', mat='brass'))
    p = m.part('test_header', 'Test Header with Hose Valves', 'valves', explode=(0, 0.6, 0.2), info={'ref': 'fw_test_header'})
    p.add(join('test_header', th), smooth_angle=40)
    add_baseplate(m, -1.6, xe + 1.6, 1.4, BP, pid='skid')


META = {
    'summary': ('A fire pump package is a complete, listed pumping system that must start automatically and deliver its rated '
                'flow and pressure to sprinklers and hydrants whenever system pressure falls. It combines a fire pump (here a '
                'horizontal split-case pump), a reliable driver (diesel engine with its own batteries, fuel and cooling from the '
                'pump discharge, or an electric motor), a fire pump controller, a small jockey pump that keeps the system '
                'pressurised against minor leaks, a main relief valve, a test header for flow testing, and isolation/check valves. '
                'Installation and acceptance are governed by fire codes such as NFPA 20.'),
    'classification': {'family': 'Package / system', 'configuration': 'Horizontal split-case fire pump + diesel engine driver + jockey pump + controllers',
                       'application': 'Fire protection (sprinkler, hydrant, deluge systems)'},
    'model_configuration': {'performance_rule_note': 'Listed fire pumps must deliver ≥150 % of rated flow at ≥65 % of rated pressure, and shut-off ≤140 % of rated pressure (NFPA 20 — verify current edition).',
                            'driver': 'Diesel engine via drive shaft (electric-motor drives also common)', 'jockey_pump': 'Vertical multistage, small flow, sets pressure-maintenance band'},
    'standards': [
        {'id': 'NFPA 20', 'title': 'Standard for the Installation of Stationary Pumps for Fire Protection', 'relevance': 'Governs fire pump selection, drivers, controllers, piping, testing.', 'edition': 'to be verified (2022 edition current at time of writing; confirm)'},
        {'id': 'NFPA 25', 'title': 'Inspection, Testing and Maintenance of Water-Based Fire Protection Systems', 'relevance': 'Weekly/annual fire pump testing.', 'edition': 'to be verified'},
        {'id': 'UL 448 / FM Class 1311', 'title': 'Listing/approval of fire pumps', 'relevance': 'Pumps, drivers and controllers must be listed/approved.', 'edition': 'to be verified'},
        {'id': 'EN 12845', 'title': 'Fixed firefighting systems — Automatic sprinkler systems', 'relevance': 'European equivalent requirements for pump sets.', 'edition': 'to be verified'},
    ],
    'references': ['NFPA 20 (scope summary).', 'FM Global Property Loss Prevention Data Sheet 3-7 (Fire Protection Pumps) — summary.'],
    'components': {**cw.META['components'],
        'fw_driveshaft': C('Connects pump and engine while accommodating small misalignment.', 'Universal-joint drive shaft (cardan) or flexible coupling, guarded.', 'Steel.', 'Listed combination with engine.', ['Joint wear'], ['Grease, check play']),
        'fw_engine': C('Independent prime mover that runs even if electrical power fails.', 'Listed fire-pump diesel engine with dual starting batteries, overspeed shutdown, heat-exchanger cooling from pump discharge.',
                       'Cast iron engine.', 'Weekly no-flow run test typical; automatic start on pressure drop.', ['Battery failure', 'Fuel starvation', 'Cooling loop blocked'], ['Weekly run', 'Battery and fuel checks']),
        'fw_pistons': C('Convert the pressure of the burning fuel–air charge into force on the crankshaft (four-stroke: intake, compression, power, exhaust).',
                        'Aluminium or steel pistons with compression and oil-control rings, gudgeon pin to the connecting rod.', 'Aluminium alloy, steel crowns on heavy-duty engines.',
                        'Firing order spreads the power strokes evenly over two crank revolutions.', ['Ring wear (blow-by, oil consumption)', 'Scuffing from overheating'], ['Compression test', 'Blow-by and oil consumption trend']),
        'fw_conrods': C('Link each piston to its crank throw, turning straight-line motion into rotation.', 'Forged I-section rod with small-end bush and split big-end bearing shells.', 'Forged steel.',
                        'Alternating tension and compression every revolution.', ['Big-end bearing wear', 'Fatigue'], ['Oil pressure trend', 'Bearing inspection at overhaul']),
        'fw_flywheel': C('Smooths engine torque and drives the pump.', 'Crankshaft with flywheel in bell housing.', 'Steel/cast iron.', 'Rotates at engine speed.', ['Torsional issues'], ['Vibration']),
        'fw_aux': C('Engine cooling (heat exchanger fed from pump discharge), exhaust silencer and air cleaner.', 'Shell-and-tube heat exchanger, residential silencer, dry air filter.', 'Steel/copper.',
                    'Cooling loop must stay open.', ['Fouled strainer in cooling loop', 'Exhaust leaks'], ['Clean strainer, check exhaust']),
        'fw_batteries': C('Two independent battery sets to start the engine.', 'Lead-acid or NiCd batteries with chargers in the controller.', '—', 'Alternate cranking cycles.', ['Low charge'], ['Specific gravity/voltage']),
        'fw_fuel': C('Stores diesel for the required run time.', 'Tank with level gauge, vent, drain; sized for required hours.', 'Steel.', 'Keep full.', ['Water/microbial contamination'], ['Level, water drain']),
        'fw_jockey': C('Keeps the fire main pressurised against small leaks so the main fire pump starts only on real demand.', 'Small vertical multistage pump with its own controller and pressure switches.',
                       'Stainless steel.', 'Set to start/stop at pressures above the fire pump start point.', ['Short cycling'], ['Check start/stop pressures']),
        'fw_relief': C('Limits system pressure (required on engine-driven pumps where shut-off pressure could exceed system rating).', 'Pilot-operated or spring relief valve with discharge cone to drain.',
                       'Bronze/ductile iron.', 'Set per system design.', ['Leakage', 'Sticking'], ['Annual test']),
        'fw_test_header': C('Allows flow testing of the pump through hose streams or a flow meter.', 'Header with multiple 2½ in hose valves (or flow meter loop).', 'Steel/brass valves.',
                            'Used for annual performance test.', ['Valve leakage'], ['Annual flow test']),
    },
}


def build(out_dir):
    return cw.build(out_dir, pump_id=ID, title='Firewater Pump Package (Diesel-Driven, NFPA 20 Style)', meta=META, mat='paint_red', extra=extra, driver=False)


if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
