"""
Diaphragm Metering Pump — hydraulically actuated (plunger + hydraulic fluid) PTFE
diaphragm dosing pump.  Motor -> worm gear -> eccentric -> plunger; the plunger
displaces hydraulic oil that flexes the diaphragm; double ball check valves on
the liquid end.  Stroke length is adjustable (knob) for accurate dosing.
Plunger axis X (liquid end at -X), cut plane y = 0.
"""
import math
from pumpforge.core import (Model, lathe, lathe_split, ring_profile, cyl, box, csg, split, join, merge_halves, split_faces, split_many,
                            TAU, OPERATE_FRAMES)
from pumpforge.parts import add_motor_v, nozzle_bolts
from pumpforge.shapes import twisted_extrude, lobed_profile, involute_gear_profile, sweep_tube
from pumpforge.core import extrude_poly
from pumpforge.common_meta import C

ID = 'diaphragm_metering_pump'
CZ = 0.24
EC = 0.008          # eccentricity (stroke = 2*EC)
XD = -0.06          # diaphragm plane
RD = 0.07           # diaphragm clamp radius


def build(out_dir):
    m = Model(ID, 'Diaphragm Metering (Dosing) Pump, Hydraulically Actuated', 'C · Reciprocating Positive-Displacement Pumps', META)
    xs = []
    for f in range(OPERATE_FRAMES + 1):
        th = TAU * f / OPERATE_FRAMES
        xs.append((1 + f, EC * math.cos(th) - EC))     # plunger displacement (0 at rest, -2EC at max forward)
    # ---------- gearbox / drive housing
    xw = 0.16
    hz = csg('drive_housing', [box('dh', (0.3, 0.22, 0.26), (0.17, 0, CZ + 0.0), 'paint_red', bevel=0.02),
                               box('dhf', (0.34, 0.26, 0.03), (0.17, 0, 0.015), 'paint_red', bevel=0.005),
                               box('dhw', (0.24, 0.16, CZ - 0.13), (0.17, 0, (CZ - 0.13) / 2 + 0.02), 'paint_red'),
                               cyl('dhb', 0.06, CZ + 0.13, CZ + 0.16, 'paint_red', 48, center=(xw, 0, 0))],
             [box('dhi', (0.26, 0.18, 0.22), (0.17, 0, CZ), 'paint_red', bevel=0.015), cyl('pb', 0.016, -0.02, 0.1, 'paint_red', 32, axis='X', center=(0, 0, CZ)),
              cyl('wb', 0.012, CZ + 0.05, CZ + 0.2, 'paint_red', 24, center=(xw, 0, 0))], 'paint_red')
    p = m.part('drive_housing', 'Drive Housing (Worm Gear & Eccentric)', 'drive', section='split', explode=(0.3, 0, 0), info={'ref': 'mp_drive'})
    p.add_split(*split(hz), smooth_angle=40)
    # worm (vertical, driven by motor) and worm wheel (axis Y)
    worm = twisted_extrude('worm', lobed_profile(0.012, 0.02, 1, n=48, land=0.4), CZ + 0.02, CZ + 0.11, 0.03, 'steel', axis='Z', center=(xw, 0, 0), hand=1)
    p = m.part('worm', 'Worm (on Motor Shaft)', 'drive', pivot=(xw, 0, CZ), explode=(0.3, -0.3, 0.3), info={'ref': 'mp_worm'})
    p.add(join('worm', [worm, cyl('ws', 0.01, CZ + 0.0, CZ + 0.2, 'steel', 24, center=(xw, 0, 0))]), smooth_angle=50); p.spin('Z', 8)
    wp, _ = involute_gear_profile(0.004, 30, 20.0, steps=4)
    wc = (xw + 0.02 + 0.06, CZ + 0.065)
    wheel = extrude_poly('wheel', [(x + wc[0], z + wc[1]) for x, z in wp], -0.015, 0.015, 'bronze', plane='XZ')
    p = m.part('worm_wheel', 'Worm Wheel', 'drive', pivot=(wc[0], 0, wc[1]), explode=(0.35, -0.35, 0.1), info={'ref': 'mp_wheel'})
    p.add(join('worm_wheel', [wheel, cyl('wsh', 0.012, -0.08, 0.08, 'steel', 24, axis='Y', center=(wc[0], 0, wc[1]))]), smooth_angle=30); p.spin('Y', -1)
    # eccentric + plunger (simplified: eccentric on the plunger axis, driven by a second shaft)
    ecc = join('eccentric', [cyl('ecd', 0.03, -0.012, 0.012, 'steel', 48, axis='Y', center=(0.17 + EC, 0, CZ)),
                             cyl('ecs', 0.012, -0.08, 0.08, 'steel', 24, axis='Y', center=(0.17, 0, CZ))])
    p = m.part('eccentric', 'Eccentric (Stroke-Adjustable Cam)', 'drive', pivot=(0.17, 0, CZ), explode=(0.3, 0.3, 0), info={'ref': 'mp_eccentric'})
    p.add(ecc, smooth_angle=40); p.spin('Y', -1)
    pl = join('plunger', [cyl('pl', 0.014, -0.02, 0.135, 'chrome', 32, axis='X', center=(0, 0, CZ), ch=0.002),
                          box('yoke', (0.012, 0.03, 0.08), (0.135, 0, CZ), 'steel', bevel=0.003)])
    p = m.part('plunger', 'Plunger', 'reciprocating', pivot=(0.0, 0, CZ), explode=(0.15, -0.25, 0), info={'ref': 'mp_plunger'})
    pm = p.add(pl, smooth_angle=40)
    m.keyframes(pm, 'Operate', 'location', [(f, (x, 0, 0)) for f, x in xs])
    # stroke-adjust knob with dial
    kb = join('knob', [cyl('kd', 0.045, CZ + 0.16, CZ + 0.17, 'ptfe', 64, center=(0.25, 0, 0)), cyl('kk', 0.035, CZ + 0.17, CZ + 0.21, 'thermoplastic', 24, center=(0.25, 0, 0), ch=0.004),
                       cyl('ks', 0.008, CZ + 0.05, CZ + 0.16, 'steel', 16, center=(0.25, 0, 0))])
    p = m.part('stroke_knob', 'Stroke-Length Adjustment Knob (0–100 %)', 'controls', explode=(0.0, 0, 0.35), info={'ref': 'mp_knob'})
    p.add(kb, smooth_angle=40)
    # hydraulic housing (oil side) with relief/refill valve
    hh = csg('hyd', [lathe('hh', [(0.0, XD + 0.006), (RD + 0.02, XD + 0.006), (RD + 0.02, XD + 0.02), (0.05, XD + 0.04), (0.05, 0.02), (0.0, 0.02)], 'paint_grey', 96, axis='X',
                           center=(0, 0, CZ)),
                     cyl('rv', 0.012, CZ + 0.04, CZ + 0.09, 'brass', 6, center=(-0.01, 0, 0))],
             [lathe('hhi', [(0.0, XD + 0.0), (RD - 0.005, XD + 0.0), (RD - 0.02, XD + 0.012), (0.016, XD + 0.03), (0.016, 0.03), (0, 0.03)], 'paint_grey', 96, axis='X',
                    center=(0, 0, CZ)), cyl('rvb', 0.004, CZ, CZ + 0.1, 'paint_grey', 12, center=(-0.01, 0, 0))], 'paint_grey')
    p = m.part('hydraulic_housing', 'Hydraulic Chamber Housing (with Relief/Refill Valve)', 'hydraulic', section='split', explode=(0.12, 0, 0), info={'ref': 'mp_hydraulic'})
    p.add_split(*split(hh), smooth_angle=40)
    # PTFE diaphragm with morph targets (flexes with plunger stroke)
    prof = [(0.0, XD - 0.002), (RD + 0.012, XD - 0.002), (RD + 0.012, XD + 0.003), (0.0, XD + 0.003)]
    db, df = lathe_split('diaphragm', prof, 'ptfe', 96, axis='X', center=(0, 0, CZ))
    p = m.part('diaphragm', 'PTFE Diaphragm (Sandwich)', 'pumping_element', section='split', explode=(-0.08, 0, 0.18), info={'ref': 'mp_diaphragm'})
    p.add_split(db, df, smooth_angle=60)
    amp = 0.004
    for mesh in p.meshes:
        if not mesh.data.shape_keys:
            mesh.shape_key_add(name='Basis', from_mix=False)
        k = mesh.shape_key_add(name='forward', from_mix=False)
        for i, v in enumerate(mesh.data.vertices):
            r = math.hypot(v.co.y, v.co.z)
            f = max(0.0, 1 - (r / RD) ** 2)
            k.data[i].co = (v.co.x - amp * f, v.co.y, v.co.z)
        m.morph(mesh, 'forward', 'Operate', [(f, -x / (2 * EC)) for f, x in xs])
    # liquid end (pump head) with double ball check valves
    xh = XD - 0.06
    le = csg('liquid_end', [lathe('le', [(0.0, xh), (RD + 0.02, xh), (RD + 0.02, XD - 0.002), (0.0, XD - 0.002)], 'polypropylene', 96, axis='X', center=(0, 0, CZ)),
                            cyl('sv', 0.024, CZ - 0.16, CZ - 0.04, 'polypropylene', 48, center=(xh + 0.025, 0, 0)),
                            cyl('dv', 0.024, CZ + 0.04, CZ + 0.16, 'polypropylene', 48, center=(xh + 0.025, 0, 0))],
             [lathe('lei', [(0.0, XD - 0.012), (RD - 0.004, XD - 0.012), (RD, XD - 0.002), (0.0, XD - 0.0)], 'polypropylene', 96, axis='X', center=(0, 0, CZ)),
              cyl('svb', 0.009, CZ - 0.17, CZ - 0.0, 'polypropylene', 24, center=(xh + 0.025, 0, 0)),
              cyl('dvb', 0.009, CZ + 0.0, CZ + 0.17, 'polypropylene', 24, center=(xh + 0.025, 0, 0)),
              box('lch', (0.03, 0.018, 0.08), (xh + 0.025 + 0.012, 0, CZ), 'polypropylene')], 'polypropylene')
    bolts = [cyl(f'lb{i}', 0.006, xh - 0.008, xh, 'steel_dark', 16, axis='X', center=(0, (RD + 0.008) * math.sin(TAU * (i + 0.5) / 6), CZ + (RD + 0.008) * math.cos(TAU * (i + 0.5) / 6)))
             for i in range(6)]
    lb, lf = split(le)
    bb, bf = split_many('lebolts', bolts)
    p = m.part('liquid_end', 'Liquid End (Pump Head)', 'liquid_end', section='split', explode=(-0.25, 0, 0), info={'ref': 'mp_liquid_end'})
    p.add_split(join('leb', [lb] + ([bb] if bb else [])), join('lef', [lf] + ([bf] if bf else [])), smooth_angle=40)
    for kind, z0, sel in (('suction', CZ - 0.12, 1), ('discharge', CZ + 0.06, -1)):
        balls = []
        for j in range(2):
            zb = z0 + j * 0.035 + 0.012
            prof = [(0.008 * math.sin(t * math.pi / 12), zb - 0.008 * math.cos(t * math.pi / 12)) for t in range(13)]
            balls.append(lathe(f'{kind}b{j}', prof, 'ceramic' if False else 'ptfe', 24, center=(xh + 0.025, 0, 0)))
        p = m.part(f'{kind}_valve', f'{kind.title()} Valve (Double Ball)', 'check_valves', explode=(-0.25, -0.2, sel * -0.25), info={'ref': 'mp_ball_valve'})
        vm = p.add(join(f'{kind}_balls', balls), smooth_angle=70)
        keys = []
        for f, x in xs:
            prev = xs[max(0, f - 2)][1]
            nxt = xs[min(len(xs) - 1, f)][1]
            vel = nxt - prev
            up = (vel > 1e-6) if kind == 'suction' else (vel < -1e-6)
            keys.append((f, (0, 0, 0.004 if up else 0.0)))
        m.keyframes(vm, 'Operate', 'location', keys)
    pipes = [sweep_tube('sp', [(xh + 0.025, 0, CZ - 0.16), (xh + 0.025, 0, 0.03), (xh - 0.2, 0, 0.03)], 0.007, 'polypropylene', 12),
             sweep_tube('dp', [(xh + 0.025, 0, CZ + 0.16), (xh + 0.025, 0, CZ + 0.24), (xh - 0.2, 0, CZ + 0.24)], 0.007, 'polypropylene', 12)]
    p = m.part('tubing', 'Suction & Discharge Tubing', 'system_piping', explode=(-0.35, 0, 0), info={'ref': 'pipework'})
    pb, pf = split_many('tubing', pipes)
    p.add(pb, 'back'); p.add(pf, 'front')
    add_motor_v(m, 'm_', CZ + 0.165, 0.07, 0.2, 0.01, 0.0, explode_dz=0.4, flange_r=0.075, revs=8)
    for prt in m.parts:
        if prt.id.startswith('m_'):
            prt.pivot.x += xw
            prt.node.location.x += xw
    m.flow('flow_in', [(xh - 0.25, 0.0, 0.03), (xh + 0.025, 0.0, 0.03), (xh + 0.025, 0.0, CZ - 0.02), (XD - 0.01, 0.0, CZ)], 'flow_suction', 0.004, 0.06)
    m.flow('flow_out', [(XD - 0.01, 0.0, CZ + 0.005), (xh + 0.025, 0.0, CZ + 0.02), (xh + 0.025, 0.0, CZ + 0.24), (xh - 0.25, 0.0, CZ + 0.24)], 'flow_discharge', 0.004, 0.06)
    return m.export(out_dir)


META = {
    'summary': ('A metering (dosing) pump delivers a precise, adjustable volume per stroke. Here a motor turns a worm gear and '
                'eccentric that reciprocate a plunger; the plunger does not touch the chemical but pushes on hydraulic oil, '
                'which flexes a PTFE diaphragm evenly. As the diaphragm retracts, the suction ball valves open and the head '
                'fills; as it advances, they close and the discharge balls lift. Output is set by stroke length (knob) and '
                'stroke rate, typically with repeatability of the order of ±1 % — used for chemical injection, water treatment '
                'and process dosing where leakage of hazardous chemicals must be avoided.'),
    'classification': {'family': 'Positive displacement – reciprocating', 'configuration': 'Hydraulically actuated diaphragm metering pump (API 675 type), simplex'},
    'model_configuration': {'stroke_mm_display': 2 * EC * 1000, 'valves': 'Double ball check valves (suction and discharge)', 'diaphragm': 'PTFE (sandwich design with leak detection is common)',
                            'capacity_formula': 'Q = (stroke volume × stroke % setting) × strokes per minute'},
    'standards': [
        {'id': 'API 675', 'title': 'Positive Displacement Pumps – Controlled Volume for Petroleum, Chemical, and Gas Industry Services', 'relevance': 'The core standard for metering pumps (accuracy, linearity, repeatability).', 'edition': 'to be verified'},
        {'id': 'ANSI/HI 7.1-7.5', 'title': 'Controlled-Volume Metering Pumps', 'relevance': 'Nomenclature, application, operation.', 'edition': 'to be verified'},
    ],
    'references': ['API 675 (scope summary).', 'Manufacturer metering pump literature (generic practice).'],
    'components': {
        'mp_drive': C('Encloses the speed-reducing worm gear and the stroke mechanism in an oil bath.', 'Cast housing with worm, worm wheel, eccentric and stroke adjustment.',
                      'Cast iron/aluminium.', 'Oil lubricated.', ['Oil leakage', 'Gear wear'], ['Oil level']),
        'mp_worm': C('First reduction stage from motor speed.', 'Single-start hardened steel worm on the motor shaft.', 'Hardened steel.', 'High reduction ratio.', ['Wear'], ['Backlash']),
        'mp_wheel': C('Drives the eccentric at stroke frequency.', 'Bronze worm wheel.', 'Phosphor bronze.', 'Oil bath.', ['Tooth wear'], ['Backlash']),
        'mp_eccentric': C('Converts rotation into reciprocation; its effective throw sets the stroke length.', 'Adjustable eccentric or lost-motion cam.', 'Steel.', 'Adjust while stopped or running per design.', ['Wear'], ['Calibration check']),
        'mp_plunger': C('Displaces hydraulic oil to move the diaphragm.', 'Ground plunger in a close-fitting bore.', 'Hardened stainless steel.', 'Does not contact the process liquid.', ['Bore wear'], ['Hydraulic performance']),
        'mp_knob': C('Sets stroke length (capacity) as a percentage.', 'Micrometer dial/knob on top of the drive; automatic actuators available.', 'Polymer/steel.', 'Calibrate capacity at site with a calibration column.', ['Drift'], ['Calibration column test']),
        'mp_hydraulic': C('Holds hydraulic oil between plunger and diaphragm; includes relief and refill valves that protect the pump and keep the oil volume correct.', 'Housing with contour plate supporting the diaphragm.',
                          'Cast iron/steel.', 'Internal relief protects against closed discharge.', ['Air in oil (loss of accuracy)', 'Relief valve setting drift'], ['Oil condition, bleed air']),
        'mp_diaphragm': C('Separates process liquid from hydraulic oil and transmits displacement.', 'PTFE (often double/sandwich with leak detection); hydraulically balanced so it is not stretched.',
                          'PTFE, PTFE-faced elastomer.', 'Long life because pressure is balanced.', ['Rupture (detected by leak sensor in sandwich designs)'], ['Leak detector, scheduled replacement']),
        'mp_liquid_end': C('Process-wetted head that holds the check valves.', 'Moulded or machined head bolted to the hydraulic housing.', 'PP, PVDF, 316 SS, Alloy 20, Hastelloy.',
                           'Material selected for chemical compatibility.', ['Chemical attack', 'Valve leakage'], ['Inspect valves and seats']),
        'mp_ball_valve': C('Double ball check valves give tight shut-off for accurate metering.', 'Two balls in series in cartridges with seats.', 'Ceramic, PTFE, glass, stainless balls; PTFE/PVDF seats.',
                           'Suction balls lift on the suction stroke, discharge balls on the delivery stroke.', ['Crystals or debris on seats → loss of accuracy'], ['Clean/replace cartridges']),
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
