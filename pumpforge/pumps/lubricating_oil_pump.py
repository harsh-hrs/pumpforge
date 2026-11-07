"""
Lubricating Oil Pump (Lube-Oil Console) — API 614-style package: oil reservoir
with heater, main and standby screw pumps driven by motors, duplex filters with
transfer valve, twin coolers, pressure-control valve and supply header.
Pumps are three-screw type (shown sectioned).  System-level model.
"""
import math
from mathutils import Matrix
from pumpforge.core import Model, lathe, cyl, box, csg, split, join, split_many, TAU
from pumpforge.parts import add_coupling, add_motor_h, transform_parts, hollow_pipe, pipe, gate_valve, pressure_gauge
from pumpforge.shapes import twisted_extrude, lobed_profile
from pumpforge.common_meta import C

ID = 'lubricating_oil_pump'
SK = 0.12          # skid top


def screw_pump_set(m, tag, ypos, cz, label):
    n0 = len(m.parts)
    D = 0.022
    body = csg(f'pb{tag}', [cyl(f'pbo{tag}', 0.075, -0.2, 0.08, 'paint_grey', 64, axis='X', center=(0, 0, cz), ch=0.005),
                            box(f'pbf{tag}', (0.24, 0.16, cz - SK - 0.07), (-0.06, 0, SK + (cz - SK - 0.07) / 2 + 0.004), 'paint_grey', bevel=0.004),
                            cyl(f'pbs{tag}', 0.035, cz - 0.15, cz, 'paint_grey', 32, center=(-0.15, 0, 0)), cyl(f'pbd{tag}', 0.03, cz, cz + 0.13, 'paint_grey', 32, center=(0.03, 0, 0))],
               [cyl(f'pbi{tag}', 0.052, -0.18, 0.06, 'paint_grey', 64, axis='X', center=(0, 0, cz)), cyl(f'pbsi{tag}', 0.025, cz - 0.16, cz - 0.02, 'paint_grey', 32, center=(-0.15, 0, 0)),
                cyl(f'pbdi{tag}', 0.02, cz + 0.02, cz + 0.14, 'paint_grey', 32, center=(0.03, 0, 0)), cyl(f'pbsh{tag}', 0.012, 0.05, 0.1, 'paint_grey', 24, axis='X', center=(0, 0, cz))],
               'paint_grey')
    b, f = split(body)
    p = m.part(f'pump_{tag}', f'{label} Lube-Oil Pump (Three-Screw)', 'pumps', section='split', explode=(0, 0, 0.3), info={'ref': 'lo_pump'})
    p.add_split(b, f, smooth_angle=40)
    pr = twisted_extrude(f'pr{tag}', lobed_profile(D / 2, 5 * D / 6, 2, n=64, land=0.5, sharp=3), -0.17, 0.04, 10 * D / 3, 'steel', axis='X', center=(0, 0, cz), hand=1)
    sh = cyl(f'psh{tag}', 0.011, -0.17, 0.15, 'steel', 24, axis='X', center=(0, 0, cz))
    p = m.part(f'rotor_{tag}', f'{label} Pump – Power Rotor', 'pumps', pivot=(0, 0, cz), explode=(0, -0.25, 0.3), info={'ref': 'power_rotor_lo'})
    p.add(join(f'rot{tag}', [pr, sh]), smooth_angle=50); p.spin('X', 2)
    for s in (1, -1):
        ir = twisted_extrude(f'ir{tag}{s}', lobed_profile(D / 6, D / 2, 2, n=48, phase=math.pi / 2, land=0.5, sharp=3), -0.17, 0.04, 10 * D / 3, 'steel_dark',
                             axis='X', center=(0, s * D, cz), hand=-1)
        p = m.part(f'idler_{tag}_{"a" if s > 0 else "b"}', f'{label} Pump – Idler Rotor', 'pumps', pivot=(0, s * D, cz), explode=(0, -0.25 + 0.05 * s, 0.35),
                   info={'ref': 'power_rotor_lo'})
        p.add(ir, smooth_angle=50); p.spin('X', -2)
    add_coupling(m, f'coupling_{tag}', 0.1, 0.17, cz, 0.04, 0.012, explode=(0.2, 0, 0.3), foot_z=SK)
    add_motor_h(m, f'm{tag}_', 0.19, cz, 0.11, 0.34, SK, 0.016, 0.06, explode_dx=0.5)
    transform_parts(m, m.parts[n0:], Matrix.Translation((0.0, ypos, 0.0)))


def build(out_dir):
    m = Model(ID, 'Lubricating Oil Pump Console (Main + Standby, API 614 Style)', 'E · Industrial Pump Applications', META)
    # skid + reservoir
    sk = join('skid', [box('sk', (2.2, 2.0, 0.12), (0.2, -0.45, 0.06), 'paint_grey', bevel=0.006)])
    p = m.part('skid', 'Console Skid (Baseframe with Drip Pan)', 'baseplate', explode=(0, 0, -0.3), info={'ref': 'baseplate'})
    p.add(sk, smooth_angle=30)
    tank = csg('reservoir', [box('ro', (1.6, 0.8, 0.7), (0.2, 0.3, SK + 0.35), 'paint_green', bevel=0.012)],
               [box('ri', (1.58, 0.78, 0.68), (0.2, 0.3, SK + 0.35), 'paint_green')], 'paint_green')
    heater = cyl('heater', 0.025, -0.55, 0.0, 'chrome', 24, axis='X', center=(0, 0.3, SK + 0.15))
    p = m.part('reservoir', 'Oil Reservoir (Stainless/Carbon Steel)', 'reservoir', section='split', explode=(0, 0.5, 0), info={'ref': 'lo_reservoir'})
    rb, rf = split(tank)
    p.add_split(join('rb_', [rb, heater]), rf, smooth_angle=40)
    lg = join('lvl', [box('lg', (0.04, 0.012, 0.4), (0.7, -0.106, SK + 0.35), 'thermoplastic'), box('lgw', (0.02, 0.004, 0.36), (0.7, -0.114, SK + 0.35), 'flow_suction'),
                      cyl('brt', 0.05, SK + 0.7, SK + 0.8, 'thermoplastic', 32, center=(-0.4, 0.4, 0), ch=0.008)])
    p = m.part('level_breather', 'Level Gauge, Breather & Immersion Heater', 'reservoir', explode=(0, -0.3, 0.2), info={'ref': 'lo_level'})
    p.add(lg, smooth_angle=40)
    cz = SK + 0.16
    screw_pump_set(m, 'main', -0.45, cz, 'Main')
    screw_pump_set(m, 'standby', -0.95, cz, 'Standby')
    # suction lines from tank, discharge to filters
    pp = []
    for y in (-0.45, -0.95):
        pp.append(pipe(f'sl{y}', [(-0.15, y, cz - 0.15), (-0.15, y, SK + 0.06), (-0.15, -0.1, SK + 0.06), (-0.15, -0.1, SK + 0.12)], 0.022, 'steel', 16, bend=0.04))
        pp.append(pipe(f'dl{y}', [(0.03, y, cz + 0.13), (0.03, y, SK + 1.0), (-0.3, y, SK + 1.0)], 0.018, 'steel', 16, bend=0.04))
    pp.append(pipe('hdr', [(-0.3, -0.95, SK + 1.0), (-0.3, -0.45, SK + 1.0), (-0.3, -0.2, SK + 1.0)], 0.022, 'steel', 16))
    p = m.part('piping', 'Suction, Discharge & Header Piping', 'system_piping', explode=(0, -0.2, 0.3), info={'ref': 'pipework'})
    p.add(join('piping', pp), smooth_angle=50)
    # duplex filter with transfer valve
    flt = [cyl(f'fl{i}', 0.09, SK + 0.75, SK + 1.2, 'paint_grey', 48, center=(-0.75 + i * 0.25, -0.2, 0), ch=0.01) for i in range(2)]
    flt += [box('tv', (0.12, 0.12, 0.1), (-0.625, -0.2, SK + 1.0), 'brass', bevel=0.01), cyl('tvh', 0.012, SK + 1.05, SK + 1.18, 'steel', 12, center=(-0.625, -0.2, 0)),
            box('tvl', (0.2, 0.02, 0.015), (-0.625, -0.2, SK + 1.18), 'paint_red')]
    p = m.part('duplex_filter', 'Duplex Oil Filter with Transfer Valve', 'filtration', explode=(-0.4, -0.2, 0.3), info={'ref': 'lo_filter'})
    p.add(join('duplex_filter', flt), smooth_angle=40)
    # twin coolers
    cool = []
    for i in range(2):
        cool += [cyl(f'co{i}', 0.11, -0.4, 0.6, 'paint_blue', 48, axis='X', center=(0, 0.1 + i * 0.32, SK + 1.0), ch=0.012),
                 cyl(f'cn1{i}', 0.03, SK + 1.1, SK + 1.2, 'paint_blue', 24, center=(-0.3, 0.1 + i * 0.32, 0)),
                 cyl(f'cn2{i}', 0.03, SK + 1.1, SK + 1.2, 'paint_blue', 24, center=(0.5, 0.1 + i * 0.32, 0))]
    cool += [box(f'cs{i}', (0.06, 0.7, SK + 0.65), (x, 0.26, SK + 0.62), 'paint_grey') for i, x in enumerate((-0.35, 0.55))]
    p = m.part('coolers', 'Twin Shell-and-Tube Oil Coolers', 'cooling', explode=(0, 0.4, 0.5), info={'ref': 'lo_cooler'})
    p.add(join('coolers', cool), smooth_angle=40)
    pcv = join('pcv', [cyl('pcvb', 0.06, SK + 0.9, SK + 1.05, 'paint_blue_dark', 32, center=(0.85, -0.2, 0)),
                       lathe('pcva', [(0, SK + 1.05), (0.1, SK + 1.12), (0.1, SK + 1.16), (0, SK + 1.18)], 'paint_blue_dark', 48, center=(0.85, -0.2, 0)),
                       pipe('pcvp', [(0.6, -0.2, SK + 0.95), (1.1, -0.2, SK + 0.95)], 0.025, 'steel', 16)])
    g = [pressure_gauge('pg1', (0.95, -0.2, SK + 0.975)), pressure_gauge('pg2', (-0.3, -0.33, SK + 1.02))]
    p = m.part('pressure_control', 'Pressure-Control Valve & Gauges (Supply Header)', 'instrumentation', explode=(0.4, -0.2, 0.3), info={'ref': 'lo_pcv'})
    p.add(join('pressure_control', [pcv] + g), smooth_angle=40)
    m.flow('flow_oil', [(-0.15, 0.2, SK + 0.12), (-0.15, -0.1, SK + 0.08), (-0.15, -0.45, SK + 0.06), (-0.15, -0.45, cz), (0.03, -0.45, cz), (0.03, -0.45, SK + 1.0),
                        (-0.3, -0.45, SK + 1.0), (-0.3, -0.2, SK + 1.0), (-0.62, -0.2, SK + 1.0), (-0.3, 0.1, SK + 1.0), (0.6, 0.1, SK + 1.0), (0.6, -0.2, SK + 0.95), (1.2, -0.2, SK + 0.95)],
           'flow_discharge', 0.012, 0.25)
    return m.export(out_dir)


META = {
    'summary': ('A lubricating-oil console supplies clean, cool oil at controlled pressure to the bearings (and often seals) of '
                'large machines such as turbines, compressors and big pumps. Oil is drawn from a reservoir by a main pump; an '
                'identical standby pump starts automatically if header pressure falls. Duplex filters and twin coolers can be '
                'switched over while running for maintenance, and a pressure-control valve spills excess oil back to the tank. '
                'Positive-displacement screw or gear pumps are used because they give steady flow regardless of oil viscosity.'),
    'classification': {'family': 'Package / system', 'configuration': 'Lube-oil console with main + standby rotary screw pumps', 'application': 'Turbomachinery bearing lubrication'},
    'model_configuration': {'pumps': '2 × 100 % three-screw pumps with motors (auto-start of standby on low pressure)', 'filters': 'Duplex with continuous-flow transfer valve',
                            'coolers': 'Twin shell-and-tube (water cooled)', 'reservoir_note': 'API 614 typically sizes reservoir retention time in minutes of normal flow — verify edition.'},
    'standards': [
        {'id': 'API 614', 'title': 'Lubrication, Shaft-Sealing and Oil-Control Systems and Auxiliaries', 'relevance': 'Governs design of lube-oil consoles in petroleum/petrochemical service.', 'edition': 'to be verified'},
        {'id': 'API 676', 'title': 'Positive Displacement Pumps – Rotary', 'relevance': 'Lube-oil pumps (screw/gear) in API 614 systems.', 'edition': 'to be verified'},
        {'id': 'ISO 10438', 'title': 'Lubrication, shaft-sealing and oil-control systems', 'relevance': 'ISO equivalent of API 614.', 'edition': 'to be verified'},
    ],
    'references': ['API 614 (scope summary).', 'Turbomachinery lube system design guides (generic practice).'],
    'components': {
        'lo_pump': C('Delivers oil flow to the header; one runs, one stands by.', 'Three-screw pump with motor on the console skid.', 'Cast iron/steel, hardened rotors.',
                     'Standby auto-start on low header pressure; check valves isolate the idle pump.', ['Rotor wear', 'Loss of suction (low level)'], ['Auto-start test', 'Vibration']),
        'power_rotor_lo': C('Screw rotors that move oil axially without pulsation.', 'Power rotor drives two idlers hydraulically.', 'Hardened steel.', 'Lubricated by the oil itself.', ['Wear'], ['Performance trend']),
        'lo_reservoir': C('Stores oil, separates air/water, provides retention time; heater for cold start.', 'Stainless tank with sloped bottom, drain, heater, level and temperature instruments.', 'Stainless steel (often required by API 614).',
                          'Maintain minimum level and temperature before start.', ['Water contamination', 'Foaming'], ['Oil analysis']),
        'lo_level': C('Shows level, breathes air, heats oil for cold start.', 'Sight gauge, breather, immersion heater.', '—', 'Heater interlocked with level.', ['Heater burn-out if exposed'], ['Function test']),
        'lo_filter': C('Removes particles; one side in service while the other is serviced.', 'Duplex filter housings with transfer valve, differential-pressure indicator.', 'Carbon/stainless housings.',
                       'Changeover without flow interruption.', ['Element clogging', 'Transfer valve leakage'], ['ΔP monitoring']),
        'lo_cooler': C('Removes heat from oil to keep supply temperature constant.', 'Twin shell-and-tube coolers with transfer valve; temperature-control valve.', 'Steel shell, copper-nickel/stainless tubes.',
                       'Oil pressure should exceed water pressure to avoid water ingress on tube leak.', ['Fouling', 'Tube leaks'], ['Outlet temperature trend']),
        'lo_pcv': C('Holds header pressure constant by spilling excess flow back to the tank.', 'Self-acting or pneumatic back-pressure control valve; gauges and transmitters.', 'Steel.',
                    'Stable header pressure is critical for bearing protection.', ['Sticking'], ['Calibration']),
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
