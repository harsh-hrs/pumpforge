"""
Chemical Dosing System — skid-mounted package: chemical storage tank with
agitator and level gauge, duty/standby diaphragm metering pumps, suction
strainer and calibration column, discharge pulsation dampener, safety relief
(PSV) and back-pressure valves, pressure gauge and injection quill, all on a
bunded (spill-containment) skid.  System-level model; cut plane y = 0.
"""
import math
from pumpforge.core import Model, lathe, cyl, box, csg, split, join, split_many, TAU, OPERATE_FRAMES
from pumpforge.parts import pipe, hollow_pipe, gate_valve, pressure_gauge, add_motor_v, add_tracers
from pumpforge.common_meta import C

ID = 'chemical_dosing_system'
SK = 0.15


def metering_pump(m, tag, x, y, label):
    """Compact motor-driven diaphragm metering pump (drive box + liquid end + motor)."""
    z = SK + 0.2
    drv = box(f'drv{tag}', (0.2, 0.16, 0.2), (x, y, SK + 0.1 + 0.02), 'paint_red', bevel=0.015)
    le = csg(f'le{tag}', [cyl(f'leo{tag}', 0.06, x - 0.17, x - 0.1, 'polypropylene', 48, axis='X', center=(0, y, z - 0.07), ch=0.006),
                          cyl(f'sv{tag}', 0.018, z - 0.17, z - 0.07, 'polypropylene', 24, center=(x - 0.14, y, 0)),
                          cyl(f'dv{tag}', 0.018, z - 0.07, z + 0.03, 'polypropylene', 24, center=(x - 0.14, y, 0))],
             [cyl(f'lei{tag}', 0.045, x - 0.13, x - 0.105, 'polypropylene', 48, axis='X', center=(0, y, z - 0.07))], 'polypropylene')
    knob = cyl(f'kn{tag}', 0.03, SK + 0.22, SK + 0.26, 'thermoplastic', 24, center=(x + 0.05, y, 0), ch=0.004)
    b, f = split_many(f'mp{tag}', [drv, le, knob], 'y', y)
    p = m.part(f'metering_pump_{tag}', f'{label} Metering Pump (Diaphragm)', 'pumps', section='split', explode=(0, 0, 0.35), info={'ref': 'cd_pump'})
    p.add_split(b, f, smooth_angle=40)
    dia = cyl(f'dia{tag}', 0.044, x - 0.104, x - 0.1, 'ptfe', 48, axis='X', center=(0, y, z - 0.07))
    p = m.part(f'diaphragm_{tag}', f'{label} Pump Diaphragm', 'pumps', explode=(-0.2, 0, 0.35), info={'ref': 'mp_diaphragm'})
    dm = p.add(dia, smooth_angle=50)
    m.keyframes(dm, 'Operate', 'location', [(1 + f, (-0.004 * (1 - math.cos(TAU * 2 * f / OPERATE_FRAMES)) / 2, 0, 0)) for f in range(OPERATE_FRAMES + 1)])
    n0 = len(m.parts)
    add_motor_v(m, f'm{tag}_', SK + 0.24, 0.05, 0.16, 0.008, 0.0, explode_dz=0.3, flange_r=0.06, revs=4)
    for prt in m.parts[n0:]:
        prt.pivot.x += x - 0.03
        prt.pivot.y += y
        prt.node.location = prt.pivot
    return z


def build(out_dir):
    m = Model(ID, 'Chemical Dosing System (Skid-Mounted)', 'E · Industrial Pump Applications', META)
    # bunded skid
    sk = csg('skid', [box('sk', (1.8, 1.2, SK), (0.1, 0, SK / 2), 'paint_grey', bevel=0.006)],
             [box('ski', (1.74, 1.14, SK), (0.1, 0, SK / 2 + 0.03), 'paint_grey')], 'paint_grey')
    p = m.part('bund_skid', 'Bunded Skid (Spill Containment)', 'baseplate', section='split', explode=(0, 0, -0.3), info={'ref': 'cd_skid'})
    p.add_split(*split(sk), smooth_angle=40)
    # storage tank with agitator
    tx, ty = -0.4, 0.15
    tk = csg('tank', [lathe('to', [(0, SK + 0.0), (0.38, SK), (0.4, SK + 0.02), (0.4, SK + 1.1), (0.38, SK + 1.13), (0.0, SK + 1.15)], 'polypropylene', 96,
                            center=(tx, ty, 0))],
             [lathe('ti', [(0, SK + 0.01), (0.39, SK + 0.02), (0.39, SK + 1.1), (0.0, SK + 1.13)], 'polypropylene', 96, center=(tx, ty, 0))], 'polypropylene')
    liquid = lathe('liq', [(0, SK + 0.02), (0.385, SK + 0.02), (0.385, SK + 0.8), (0, SK + 0.8)], 'flow_suction', 64, a0=0.0, a1=math.pi, center=(tx, ty, 0),
                   cap_mat='flow_suction')
    tb, tf = split(tk, 'y', ty)
    lb, lf = liquid, None
    p = m.part('storage_tank', 'Chemical Storage Tank (PE) with Contents', 'tank', section='split', explode=(-0.4, 0.4, 0), info={'ref': 'cd_tank'})
    p.add_split(join('tkb', [tb, lb]), tf, smooth_angle=40)
    ag = join('agitator', [cyl('ags', 0.012, SK + 0.25, SK + 1.3, 'stainless', 16, center=(tx, ty, 0))] +
              [box(f'agb{i}', (0.18, 0.02, 0.05), (tx + 0.09 * math.cos(TAU * i / 3), ty + 0.09 * math.sin(TAU * i / 3), SK + 0.3), 'stainless') for i in range(3)])
    for i, o in enumerate(ag.data.polygons):
        pass
    p = m.part('agitator', 'Agitator (Mixer) Shaft & Impeller', 'tank', pivot=(tx, ty, SK), explode=(-0.4, 0.4, 0.6), info={'ref': 'cd_agitator'})
    p.add(ag, smooth_angle=40); p.spin('Z', 1)
    n0 = len(m.parts)
    add_motor_v(m, 'mx_', SK + 1.16, 0.07, 0.22, 0.012, 0.0, explode_dz=0.6, flange_r=0.08, revs=1, label='Agitator Motor')
    for prt in m.parts[n0:]:
        prt.pivot.x += tx
        prt.pivot.y += ty
        prt.node.location = prt.pivot
    lg = join('level', [box('lgt', (0.03, 0.03, 1.0), (tx - 0.42, ty, SK + 0.55), 'ptfe'), box('lgf', (0.02, 0.032, 0.78), (tx - 0.42, ty, SK + 0.42), 'flow_suction')])
    p = m.part('level_gauge', 'Tank Level Gauge', 'instrumentation', explode=(-0.3, 0, 0), info={'ref': 'level_sensor'})
    p.add(lg, smooth_angle=40)
    # pumps
    zp = metering_pump(m, 'duty', 0.45, -0.2, 'Duty')
    metering_pump(m, 'standby', 0.45, 0.3, 'Standby')
    # suction manifold from tank with strainer and calibration column
    suc = [pipe('s1', [(tx + 0.3, ty - 0.25, SK + 0.08), (0.31, ty - 0.25, SK + 0.08), (0.31, -0.2, SK + 0.08), (0.31, -0.2, zp - 0.17)], 0.012, 'polypropylene', 12, bend=0.03),
           pipe('s2', [(0.31, ty - 0.25, SK + 0.08), (0.31, 0.3, SK + 0.08), (0.31, 0.3, zp - 0.17)], 0.012, 'polypropylene', 12, bend=0.03),
           cyl('strn', 0.03, -0.1, 0.0, 'polypropylene', 24, axis='X', center=(0, ty - 0.25, SK + 0.08)),
           cyl('calib', 0.03, SK + 0.08, SK + 0.75, 'ptfe', 24, center=(0.0, -0.45, 0)),
           pipe('cl', [(0.0, -0.45, SK + 0.08), (0.0, ty - 0.25, SK + 0.08)], 0.01, 'polypropylene', 12),
           gate_valve('cv', (0.0, -0.45, SK + 0.2), 0.012, axis='Y', mat='polypropylene')]
    p = m.part('suction_line', 'Suction Line with Strainer & Calibration Column', 'system_piping', explode=(0, -0.3, 0), info={'ref': 'cd_suction'})
    p.add(join('suction_line', suc), smooth_angle=50)
    zd = zp + 0.03
    dis = [pipe('d1', [(0.31, -0.2, zd), (0.31, -0.2, SK + 0.75), (0.31, 0.05, SK + 0.75)], 0.01, 'polypropylene', 12, bend=0.03),
           pipe('d2', [(0.31, 0.3, zd), (0.31, 0.3, SK + 0.75), (0.31, 0.05, SK + 0.75)], 0.01, 'polypropylene', 12, bend=0.03),
           pipe('d3', [(0.31, 0.05, SK + 0.75), (0.9, 0.05, SK + 0.75), (0.9, 0.05, SK + 0.3), (1.2, 0.05, SK + 0.3)], 0.012, 'polypropylene', 12, bend=0.04)]
    pd = lathe('pdamp', [(0, SK + 0.78), (0.06, SK + 0.8), (0.07, SK + 0.86), (0.07, SK + 0.95), (0.05, SK + 1.0), (0, SK + 1.01)], 'paint_blue', 48, center=(0.55, 0.05, 0))
    psv = join('psv', [cyl('psvb', 0.025, SK + 0.78, SK + 0.86, 'paint_red', 24, center=(0.7, 0.05, 0)), lathe('psvc', [(0, SK + 0.86), (0.02, SK + 0.86), (0.01, SK + 0.96), (0, SK + 0.97)],
                                                                                                              'paint_red', 24, center=(0.7, 0.05, 0))])
    bpv = join('bpv', [cyl('bpvb', 0.025, -0.03, 0.03, 'paint_blue_dark', 24, axis='X', center=(0, 0.05, SK + 0.3)), cyl('bpvk', 0.02, SK + 0.3, SK + 0.38, 'paint_blue_dark', 24, center=(0.0, 0.05, 0))])
    bpv.data.transform(__import__('mathutils').Matrix.Translation((1.05, 0, 0)))
    quill = join('quill', [cyl('qb', 0.03, 1.2, 1.26, 'stainless', 24, axis='X', center=(0, 0.05, SK + 0.3)), cyl('qt', 0.008, 1.26, 1.4, 'stainless', 12, axis='X', center=(0, 0.05, SK + 0.3))])
    g = pressure_gauge('pg', (0.8, 0.05, SK + 0.762))
    p = m.part('discharge_line', 'Discharge Line: Pulsation Dampener, PSV, Back-Pressure Valve, Gauge & Injection Quill', 'system_piping', explode=(0.3, 0, 0.3), info={'ref': 'cd_discharge'})
    p.add(join('discharge_line', dis + [pd, psv, bpv, quill, g]), smooth_angle=50)
    cp = join('panel', [box('cp', (0.3, 0.15, 0.4), (-0.4, -0.5, SK + 0.75), 'paint_grey', bevel=0.01), box('cps', (0.04, 0.04, 0.55), (-0.4, -0.5, SK + 0.28), 'paint_grey')])
    p = m.part('control_panel', 'Local Control Panel', 'controls', explode=(0, -0.3, 0.2), info={'ref': 'control_panel'})
    p.add(cp, smooth_angle=40)
    path = [(tx + 0.2, ty, SK + 0.08), (0.31, ty - 0.25, SK + 0.08), (0.31, -0.2, SK + 0.08), (0.31, -0.2, zd), (0.31, -0.2, SK + 0.75), (0.9, 0.05, SK + 0.75),
            (0.9, 0.05, SK + 0.3), (1.4, 0.05, SK + 0.3)]
    add_tracers(m, 'chemical_tracers', 'Chemical Flow (Tracers)', path, n=16, radius=0.012, mat='flow_discharge')
    m.flow('flow_chem', path, 'flow_discharge', 0.008, 0.2)
    return m.export(out_dir)


META = {
    'summary': ('A chemical dosing system injects a measured quantity of chemical (coagulant, chlorine, inhibitor, pH '
                'control, odorant) into a process or water line. Chemical is stored in a tank (often with a mixer), drawn '
                'through a strainer by a duty metering pump (with a standby), and delivered through a pulsation dampener and '
                'back-pressure valve to an injection quill. A calibration column on the suction lets operators measure the '
                'actual pump output; a safety relief valve protects the pump and piping; everything sits on a bunded skid to '
                'contain spills.'),
    'classification': {'family': 'Package / system (controlled-volume pumps)', 'configuration': 'Duty/standby diaphragm metering pumps on bunded skid', 'application': 'Water treatment, process chemical injection'},
    'model_configuration': {'pumps': '2 × diaphragm metering pumps (duty/standby)', 'accessories': 'Strainer, calibration column, pulsation dampener, PSV, back-pressure valve, gauge, injection quill',
                            'materials_note': 'Wetted materials (PP, PVDF, PTFE, 316 SS, Alloy 20) must suit the chemical; check compatibility tables.'},
    'standards': [
        {'id': 'API 675', 'title': 'Controlled-volume positive displacement pumps', 'relevance': 'Metering pump performance (accuracy, repeatability).', 'edition': 'to be verified'},
        {'id': 'ANSI/HI 7.1-7.5', 'title': 'Controlled-volume metering pumps', 'relevance': 'Application and installation guidance.', 'edition': 'to be verified'},
        {'id': 'Local chemical storage / bunding regulations', 'title': 'e.g. secondary containment ≥110 % of largest tank (common rule)', 'relevance': 'Spill containment design.', 'edition': 'verify locally'},
    ],
    'references': ['Manufacturer dosing skid design guides (generic practice).', 'Hydraulic Institute ANSI/HI 7.1-7.5 (scope summary).'],
    'components': {
        'mp_diaphragm': C('Flexing membrane that displaces the chemical.', 'PTFE-faced diaphragm.', 'PTFE.', 'Separates chemical from drive.', ['Rupture'], ['Leak detection']),
        'cd_skid': C('Supports the equipment and contains spills/leaks.', 'Fabricated tray with upstand (bund) and drain.', 'Steel (coated), PP, SS.', 'Bund volume per regulations.', ['Corrosion'], ['Inspect coating, keep drain closed']),
        'cd_tank': C('Stores and (with mixer) keeps the chemical solution uniform.', 'Moulded PE/PP or GRP vertical tank with lid, vent and outlets.', 'HDPE, PP, GRP, SS.', 'Level monitored; low-level pump cut-out.', ['Stress cracking', 'Overfill'], ['Visual, level alarms']),
        'cd_agitator': C('Mixes or keeps solids in suspension.', 'Top-entry mixer with shaft and impeller.', 'Stainless/coated steel.', 'Runs continuously or timed.', ['Shaft corrosion'], ['Visual']),
        'cd_pump': C('Delivers an accurate, adjustable flow of chemical.', 'Motor-driven diaphragm metering pump with stroke-length knob and ball check valves.', 'PP/PVDF/SS liquid end.',
                     'Output set by stroke length × stroke rate; verify with calibration column.', ['Valve fouling (crystallisation)', 'Air locking'], ['Calibration test', 'Valve cleaning']),
        'cd_suction': C('Feeds pumps with flooded suction; strainer protects valves; calibration column measures actual flow.', 'Short, large-bore suction lines with isolation valves.', 'PP/PVC/PVDF.',
                        'Avoid air ingress and long suction lines.', ['Strainer blockage'], ['Clean strainer']),
        'cd_discharge': C('Delivers chemical to the injection point with smooth flow and protection.', 'Pulsation dampener, PSV back to tank, back-pressure valve (ensures accurate dosing and prevents siphoning), gauge with diaphragm seal, injection quill with non-return.',
                          'PP/PVDF/SS; PTFE diaphragms.', 'Dampener pre-charge ≈ fraction of line pressure (per manufacturer).', ['PSV leakage', 'Quill blockage'], ['PSV test', 'Quill cleaning']),
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
