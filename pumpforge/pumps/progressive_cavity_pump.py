"""
Progressive Cavity Pump (Moineau, 1:2 geometry) — a single-helix metal rotor
turns inside a double-helix elastomer stator; sealed cavities progress from the
suction end to the discharge end.  The rotor rotates about its own axis while
that axis orbits the stator axis in the opposite direction (eccentricity e); a
connecting rod with two universal joints transmits the drive.
Axis Y: discharge end at -Y, drive at +Y, cut plane x = 0.
"""
import math
from mathutils import Matrix, Vector
from pumpforge.core import (Model, lathe, lathe_split, ring_profile, cyl, box, csg, split_keep, join, merge_halves, split_faces, split_many,
                            TAU, OPERATE_FRAMES)
from pumpforge.parts import add_drive_y, nozzle_bolts, seal_cartridge
from pumpforge.shapes import twisted_extrude
from pumpforge.common_meta import C

ID = 'progressive_cavity_pump'
CZ = 0.30
BP = 0.09
E = 0.011
RR = 0.028
P = 0.16
YS0, YS1 = -0.75, -0.11       # stator
RS = 0.024


def ks(o):
    return split_keep(o, 'x', 0.0, keep_positive=False)


def stadium(r, half, n=24):
    pts = []
    for cx, a0 in ((half, -90), (-half, 90)):
        for i in range(n + 1):
            a = math.radians(a0 + 180 * i / n)
            pts.append((cx + r * math.cos(a), r * math.sin(a)))
    return pts


def build(out_dir):
    m = Model(ID, 'Progressive Cavity Pump (Rotor–Stator, Moineau)', 'B · Rotary Positive-Displacement Pumps', META)
    # ---- stator: steel tube + bonded elastomer with double-helix cavity
    cav = twisted_extrude('cav', stadium(RR, 2 * E), YS0 - 0.01, YS1 + 0.01, 2 * P, 'rubber', axis='Y', center=(0, 0, CZ), hand=1, steps=220)
    el = csg('elastomer', [cyl('el', 0.066, YS0, YS1, 'rubber', 96, axis='Y', center=(0, 0, CZ))], [cav], 'rubber')
    tube = lathe('tube', [(0.066, YS0), (0.072, YS0), (0.072, YS1), (0.066, YS1)], 'paint_red', 96, axis='Y', center=(0, 0, CZ))
    stb, stf = split_many('stator', [el, tube], 'x', 0.0)
    stb, stf = stf, stb   # keep -X half
    p = m.part('stator', 'Stator (Elastomer in Steel Tube)', 'pumping_element', section='split', explode=(0, -0.2, -0.32), info={'ref': 'pc_stator'})
    p.add_split(stb, stf, smooth_angle=60)
    # ---- rotor (single helix), animated: spin about own axis + opposite orbit
    rot_sec = [(E + RR * math.cos(TAU * i / 48), RR * math.sin(TAU * i / 48)) for i in range(48)]
    rotor = twisted_extrude('rotor', rot_sec, YS0 - 0.005, YS1 + 0.005, P, 'chrome', axis='Y', center=(0, 0, CZ), hand=1, steps=220)
    pinj = cyl('rjoint', 0.02, YS1 + 0.005, YS1 + 0.045, 'steel', 32, axis='Y', center=(E, 0, CZ))
    p = m.part('rotor', 'Rotor (Single Helix, Hard-Chrome)', 'pumping_element', pivot=(0, 0, CZ), explode=(0, -0.2, 0.3), info={'ref': 'pc_rotor'})
    mesh = p.add(join('rotor', [rotor, pinj]), smooth_angle=60)
    rk, lk = [], []
    for f in range(OPERATE_FRAMES + 1):
        g = TAU * f / OPERATE_FRAMES
        rk.append((1 + f, (0.0, -g, 0.0)))
        lk.append((1 + f, (0.0, 0.0, -2 * E * math.sin(g))))
    m.keyframes(mesh, 'Operate', 'rotation_euler', rk)
    m.keyframes(mesh, 'Operate', 'location', lk)
    # ---- connecting rod with universal joints
    yj0, yj1 = 0.10, YS1 + 0.045
    rod_len = yj0 - yj1
    rod = join('rod', [cyl('rod', 0.016, -rod_len, 0.0, 'steel', 24, axis='Y', center=(0, yj0, CZ)),
                       lathe('uj1', [(0, -0.03), (0.026, -0.03), (0.026, 0.0), (0, 0.0)], 'steel_dark', 24, axis='Y', center=(0, yj0, CZ)),
                       lathe('uj2', [(0, -rod_len), (0.026, -rod_len), (0.026, -rod_len + 0.03), (0, -rod_len + 0.03)], 'steel_dark', 24, axis='Y',
                             center=(0, yj0, CZ)),
                       box('ujx', (0.06, 0.012, 0.012), (0, yj0 - 0.015, CZ), 'steel'), box('ujz', (0.012, 0.012, 0.06), (0, yj0 - rod_len + 0.015, CZ), 'steel')])
    p = m.part('connecting_rod', 'Connecting Rod & Universal Joints', 'power_transmission', pivot=(0, yj0, CZ), explode=(0, 0.0, 0.4),
               info={'ref': 'pc_rod'})
    rmesh = p.add(rod, smooth_angle=40)
    rk = []
    for f in range(OPERATE_FRAMES + 1):
        g = TAU * f / OPERATE_FRAMES
        end = Vector((E * math.cos(-g) + 0.0, -rod_len, E * math.sin(-g)))
        d = end.normalized()
        tilt = Vector((0, -1, 0)).rotation_difference(d).to_matrix().to_4x4()
        spin = Matrix.Rotation(-g, 4, 'Y')
        rk.append((1 + f, tuple((tilt @ spin).to_euler('XYZ'))))
    m.keyframes(rmesh, 'Operate', 'rotation_euler', rk)
    # ---- suction housing, discharge end, tie rods
    mat = 'paint_red'
    sh = csg('suction_housing', [cyl('sh', 0.095, YS1, 0.17, mat, 96, axis='Y', center=(0, 0, CZ), ch=0.004),
                                  cyl('sn', 0.05, CZ, CZ + 0.2, mat, 48, center=(0, 0.02, 0)), cyl('snf', 0.09, CZ + 0.185, CZ + 0.2, mat, 48, center=(0, 0.02, 0), ch=0.003),
                                  cyl('shf', 0.11, YS1, YS1 + 0.02, mat, 96, axis='Y', center=(0, 0, CZ)),
                                  box('shft', (0.2, 0.14, CZ - 0.095 - BP), (0, 0.05, BP + (CZ - 0.095 - BP) / 2 + 0.006), mat, bevel=0.005)],
             [cyl('shi', 0.08, YS1 - 0.01, 0.13, mat, 96, axis='Y', center=(0, 0, CZ)), cyl('snb', 0.04, CZ + 0.05, CZ + 0.21, mat, 48, center=(0, 0.02, 0)),
              cyl('shs', RS + 0.002, 0.12, 0.18, mat, 32, axis='Y', center=(0, 0, CZ))], mat)
    p = m.part('suction_housing', 'Suction Housing', 'casing', section='split', explode=(0, 0.1, 0), info={'ref': 'pc_suction_housing'})
    p.add_split(*ks(sh), smooth_angle=40)
    de = csg('discharge_end', [cyl('de', 0.11, YS0 - 0.03, YS0, mat, 96, axis='Y', center=(0, 0, CZ)),
                                lathe('dn', [(0.0, YS0 - 0.15), (0.05, YS0 - 0.15), (0.05, YS0 - 0.03), (0.0, YS0 - 0.03)], mat, 48, axis='Y', center=(0, 0, CZ)),
                                cyl('dnf', 0.09, YS0 - 0.16, YS0 - 0.145, mat, 48, axis='Y', center=(0, 0, CZ), ch=0.003),
                                box('deft', (0.2, 0.08, CZ - 0.1 - BP), (0, YS0 - 0.05, BP + (CZ - 0.1 - BP) / 2 + 0.006), mat, bevel=0.005)],
             [cyl('dei', 0.04, YS0 - 0.17, YS0 + 0.01, mat, 48, axis='Y', center=(0, 0, CZ))], mat)
    p = m.part('discharge_end', 'Discharge Flange (End Housing)', 'casing', section='split', explode=(0, -0.3, 0), info={'ref': 'pc_discharge'})
    p.add_split(*ks(de), smooth_angle=40)
    tr = [cyl(f'tr{i}', 0.008, YS0 - 0.035, YS1 + 0.025, 'steel', 16, axis='Y', center=(0.09 * math.cos(a), 0, CZ + 0.09 * math.sin(a)))
          for i, a in enumerate((math.pi / 4, 3 * math.pi / 4, 5 * math.pi / 4, 7 * math.pi / 4))]
    p = m.part('tie_rods', 'Stator Tie Rods', 'casing', explode=(0, -0.2, -0.5), info={'ref': 'pc_tierods'})
    trb, trf = split_many('tie_rods', tr, 'x', 0.0)
    p.add(trf, 'back'); p.add(trb, 'front')
    # ---- seal, bearing housing, drive
    sb, sf = seal_cartridge('seal', 0.12, 0.18, RS, 0.04, axis='Y', center=(0, 0, CZ))
    p = m.part('mechanical_seal', 'Mechanical Seal', 'mechanical_seal', section='split', explode=(-0.3, 0.2, 0.1), info={'ref': 'mechanical_seal'})
    p.add_split(sb, sf)
    dsh = cyl('dshaft', RS, yj0 - 0.01, 0.62, 'steel', 32, axis='Y', center=(0, 0, CZ), ch=0.002)
    p = m.part('drive_shaft', 'Drive Shaft', 'rotating_element', pivot=(0, 0, CZ), explode=(0, 0.2, 0.4), info={'ref': 'pump_shaft'})
    p.add(dsh); p.spin('Y', -1)
    y0, y1 = 0.17, 0.42
    bh = csg('bh', [lathe('bh', [(0.0, y0), (0.11, y0), (0.11, y0 + 0.015), (0.06, y0 + 0.04), (0.06, y1), (0, y1)], mat, 96, axis='Y', center=(0, 0, CZ)),
                    box('bhf', (0.16, 0.12, CZ - BP - 0.05), (0, y1 - 0.08, BP + (CZ - BP - 0.05) / 2 + 0.006), mat, bevel=0.004)],
             [cyl('bhi', 0.048, y0 + 0.04, y1 - 0.02, mat, 48, axis='Y', center=(0, 0, CZ)), cyl('bhs', RS + 0.002, y0 - 0.01, y1 + 0.01, mat, 32, axis='Y', center=(0, 0, CZ)),
              box('bhw', (0.2, 0.08, 0.07), (0, y0 + 0.07, CZ), mat, bevel=0.01)], mat)
    p = m.part('bearing_housing', 'Bearing Housing', 'bearing_housing', section='split', explode=(0, 0.35, 0), info={'ref': 'bearing_frame'})
    p.add_split(*ks(bh), smooth_angle=40)
    add_drive_y(m, 0.62, CZ, BP, RS, motor_R=0.13, motor_L=0.42, y_base0=YS0 - 0.25, base_w=0.5, revs=-1)

    m.flow('flow_in', [(0, 0.02, CZ + 0.5), (0, 0.02, CZ + 0.05), (0, -0.05, CZ + 0.05), (0, YS1 + 0.01, CZ + 0.04)], 'flow_suction', 0.005, 0.08)
    hel = [(2 * E * math.cos(math.pi * (YS1 - y) / P) * math.cos(math.pi * y / P) * 0 + 0.0 + (RR + E) * math.cos(math.pi * y / P + math.pi / 2),
            y, CZ + (RR + E) * math.sin(math.pi * y / P + math.pi / 2)) for y in [YS1 - (YS1 - YS0) * k / 80 for k in range(81)]]
    m.flow('flow_cavity', hel[::2], 'flow_discharge', 0.004, 0.08)
    m.flow('flow_out', [(0, YS0 - 0.02, CZ), (0, YS0 - 0.4, CZ)], 'flow_discharge', 0.005, 0.08)
    return m.export(out_dir)


META = {
    'summary': ('A single-helix steel rotor turns inside a double-helix rubber stator. Because the stator pitch is twice the rotor '
                'pitch, a chain of sealed cavities forms along the pump; as the rotor turns (rolling eccentrically, its axis '
                'orbiting the stator axis), the cavities progress from suction to discharge without changing shape or volume. '
                'The result is smooth, low-shear, nearly pulse-free flow proportional to speed — ideal for sludges, pastes, '
                'viscous and shear-sensitive products, and liquids with solids or gas.'),
    'classification': {'family': 'Positive displacement – rotary', 'configuration': 'Progressive cavity (Moineau), 1:2 rotor/stator lobe geometry, 2 stages'},
    'model_configuration': {'eccentricity_mm': E * 1000, 'rotor_pitch_mm': P * 1000, 'stator_pitch_mm': 2 * P * 1000, 'stages': 2,
                            'pressure_note': 'Pressure capability per stage depends on the design (often of the order of 6 bar per stage — verify with manufacturer).'},
    'standards': [
        {'id': 'API 676', 'title': 'Positive Displacement Pumps – Rotary', 'relevance': 'PC pumps in process service.', 'edition': 'to be verified'},
        {'id': 'ANSI/HI 3.1-3.5', 'title': 'Rotary Pumps', 'relevance': 'Nomenclature and application.', 'edition': 'to be verified'},
    ],
    'references': ['Karassik et al., Pump Handbook — progressing cavity pumps.', 'R. Moineau patents / manufacturer PC pump literature (generic practice).'],
    'components': {
        'pc_stator': C('Forms the double-helix cavity that seals against the rotor; with it, defines the progressing cavities.', 'Elastomer moulded and bonded into a steel tube.',
                       'NBR, EPDM, FKM, natural rubber; even-wall stators for higher pressure.', 'Interference fit with rotor; must never run dry (heat build-up destroys the elastomer).',
                       ['Dry-run burn-out', 'Swelling/chemical attack', 'Abrasive wear', 'Hysteresis heating at high pressure'], ['Pressure/flow test', 'Visual of elastomer']),
        'pc_rotor': C('Single-helix rotor that rolls inside the stator, displacing the liquid.', 'Machined steel helix, often hard-chrome plated.',
                      'Tool steel, stainless steel, hard-chrome or ceramic coated.', 'Orbits eccentrically (gyrates) while rotating.', ['Coating wear', 'Abrasion'], ['Diameter measurement']),
        'pc_rod': C('Transmits torque from the concentric drive shaft to the eccentrically moving rotor.', 'Connecting rod with two universal (pin or gear) joints, sealed and greased; or flexible shaft.',
                    'Steel with sealed joints.', 'Joints must be protected from the pumped liquid.', ['Joint pin wear', 'Boot/seal failure'], ['Joint play']),
        'pc_suction_housing': C('Receives the liquid and houses the connecting rod.', 'Cast housing with inlet nozzle (often rotatable) and drain.', 'Cast iron, stainless steel.',
                                'Suction pressure.', ['Abrasion'], ['Visual']),
        'pc_discharge': C('Outlet end holding the stator; discharge nozzle.', 'End housing clamped by tie rods.', 'Cast iron, stainless.', 'Discharge pressure.', ['Gasket leak'], ['Tie rod tension']),
        'pc_tierods': C('Clamp the stator between suction housing and discharge end.', 'Threaded rods.', 'Steel.', 'Preload must hold pressure.', ['Corrosion'], ['Tension']),
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
