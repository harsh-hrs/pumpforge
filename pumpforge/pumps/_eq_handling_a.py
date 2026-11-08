"""Material Handling — EQ-196 … EQ-209: feeders, screens and crushers."""
import math
from mathutils import Matrix, Vector
from pumpforge.core import Model, lathe, cyl, box, csg, split, join, rotate, extrude_poly, hex_prism, TAU, OPERATE_FRAMES
from pumpforge.valvekit import P, keys_loop, smooth_pulse, spring
from pumpforge.parts import add_motor_h, add_coupling, hollow_pipe, transform_parts
from pumpforge.rotkit import open_path, sprocket, local_pivot, axis_rot_keys, ring_of, radial_blades
from pumpforge.handlingkit import hopper, beam, movers, polyline_path, rock, rocks_along, belt_loop, wheel
from pumpforge.vesselkit import half
from pumpforge.shapes import sweep_tube, twisted_extrude
from pumpforge.common_meta import C

CAT = '9 · Material Handling & Heavy Machinery'


def _model(pid, title):
    return Model(pid, title, CAT, META[pid])


def _gearmotor(m, pid, x, y, z, axis='Y', label='Gearmotor', revs=1.0, ref='hm_drive'):
    g = join(pid, [box(pid + 'gb', (0.2, 0.18, 0.2), (x, y, z), 'paint_blue', bevel=0.015),
                   cyl(pid + 'mt', 0.08, y + 0.09, y + 0.35, 'paint_motor', 32, axis='Y', center=(x, 0, z + 0.03), ch=0.01) if axis == 'Y' else
                   cyl(pid + 'mt', 0.08, x + 0.1, x + 0.36, 'paint_motor', 32, axis='X', center=(0, y, z + 0.03), ch=0.01)])
    return P(m, pid, label, 'drive', g, explode=(0, 0.3, 0.2), ref=ref, section='keep')


def _vib_keys(m, part, amp=0.012, ang=math.radians(30), freq=6):
    keys_loop(m, part, lambda t: (amp * math.cos(ang) * math.sin(TAU * freq * t), 0, amp * math.sin(ang) * math.sin(TAU * freq * t)))


def _springs(name, pts, z0, z1, r=0.03):
    return join(name, [spring(f'{name}{i}', (x, y, 0), r, z0, z1, 0.006, 5) for i, (x, y) in enumerate(pts)])


# =============================================================== EQ-196 Apron feeder
def apron_feeder(out):
    m = _model('apron_feeder', 'Apron Feeder (Heavy-Duty, Chain-Driven Pans)')
    Z, X0, X1, R = 0.55, -1.2, 1.2, 0.22
    pos, L = open_path(R, R, X1 - X0, X0, Z)
    W = 0.7
    n = int(L / 0.16)
    pitch = L / n
    dist = pitch * 4

    def pan(i):
        return join(f'pan{i}', [box(f'pp{i}', (pitch * 1.05, W, 0.015), (0, 0, 0.0), 'steel_dark'), box(f'pl{i}', (pitch * 1.0, 0.02, 0.06), (0, -W / 2, 0.03), 'steel_dark'),
                                box(f'pr{i}', (pitch * 1.0, 0.02, 0.06), (0, W / 2, 0.03), 'steel_dark')])
    movers(m, 'pans', 'Overlapping Apron Pans on Crawler-Type Chains', pos, L, n, dist, pan, group='conveyor', ref='af_pans')
    for i, (x, nm) in enumerate(((X0, 'Tail'), (X1, 'Head (drive)'))):
        sp, _ = sprocket(f'sp{i}', 8, 2 * R * math.sin(math.pi / 8), 0.03, -W / 2 - 0.05, -W / 2 + 0.02, 'steel', cx=x, cz=Z)
        sp2, _ = sprocket(f'sq{i}', 8, 2 * R * math.sin(math.pi / 8), 0.03, W / 2 - 0.02, W / 2 + 0.05, 'steel', cx=x, cz=Z)
        sh = cyl(f'sh{i}', 0.05, -W / 2 - 0.25, W / 2 + 0.25, 'steel', 24, axis='Y', center=(x, 0, Z))
        ps = P(m, f'{"head" if i else "tail"}_shaft', f'{nm} Shaft & Sprockets', 'conveyor', [sp, sp2, sh], explode=(0.3 * (1 if i else -1), 0, 0.2), ref='af_sprockets', section='keep', pivot=(x, 0, Z))
        ps.spin('Y', dist / (TAU * R))
    rl = [box(f'rl{s}', (X1 - X0, 0.06, 0.08), (0, s * (W / 2 + 0.03), Z + R - 0.06), 'paint_yellow') for s in (-1, 1)]
    rl += [cyl(f'cr{k}{s}', 0.05, s * (W / 2 + 0.06) - 0.03, s * (W / 2 + 0.06) + 0.03, 'steel', 16, axis='Y', center=(X0 + 0.3 + 0.35 * k, 0, Z + R - 0.12)) for k in range(6) for s in (-1, 1)]
    fr = [box(f'fl{k}{s}', (0.12, 0.08, Z + R - 0.12), (X0 + 0.2 + 1.0 * k, s * (W / 2 + 0.12), (Z + R - 0.12) / 2), 'paint_yellow') for k in range(3) for s in (-1, 1)]
    P(m, 'frame', 'Main Frame, Carrying Rollers & Track Rails', 'structure', rl + fr, explode=(0, 0, -0.3), ref='af_frame', section='keep')
    sk = [box(f'sk{s}', (1.4, 0.02, 0.35), (-0.3, s * (W / 2 - 0.02), Z + R + 0.2), 'paint_grey') for s in (-1, 1)]
    hp = hopper('hp', 1.2, 0.7, Z + R + 0.35, Z + R + 0.9)
    hp.data.transform(Matrix.Translation((-0.35, 0, 0)))
    P(m, 'hopper', 'Feed Hopper & Skirt Boards', 'structure', sk + [hp], explode=(0, 0, 0.5), ref='af_hopper')
    _gearmotor(m, 'drive', X1, -W / 2 - 0.45, Z, label='Drive: Motor, Gearbox (planetary/shaft-mounted)', ref='af_drive')
    rocks_along(m, 'ore', 'Ore Lumps (bed carried by the pans)', [(-0.9, Z + R + 0.08), (X1 - 0.05, Z + R + 0.08), (X1 + R + 0.1, Z + 0.1), (X1 + R + 0.2, Z - 0.5)], 14, r=0.05)
    m.flow('material', [(-0.35, 0, Z + R + 0.95), (-0.35, 0, Z + R + 0.1), (X1, 0, Z + R + 0.1), (X1 + R + 0.15, 0, Z - 0.5)], 'flow_discharge', 0.02, 0.3, speed=[2, 0.6, 0.6, 2])
    return m.export(out)


# =============================================================== EQ-197 Vibrating feeder / EQ-203 Grizzly feeder
def _vib_feeder(pid, title, grizzly=False):
    m = _model(pid, title)
    Z, L, W = 0.55, 1.6, 0.6
    tray = [box('tb', (L, W, 0.015), (0, 0, Z), 'steel'), box('tl', (L, 0.015, 0.25), (0, -W / 2, Z + 0.12), 'steel'), box('tr', (L, 0.015, 0.25), (0, W / 2, Z + 0.12), 'steel'),
            box('te', (0.015, W, 0.25), (-L / 2, 0, Z + 0.12), 'steel')]
    if grizzly:
        tray = [t for t in tray[:1]]
        tray[0] = box('tb', (L * 0.5, W, 0.015), (-L / 4, 0, Z), 'steel')
        tray += [box('tl', (L, 0.015, 0.25), (0, -W / 2, Z + 0.12), 'steel'), box('tr', (L, 0.015, 0.25), (0, W / 2, Z + 0.12), 'steel'), box('te', (0.015, W, 0.25), (-L / 2, 0, Z + 0.12), 'steel')]
        tray += [box(f'gb{i}', (L * 0.5, 0.035, 0.06), (L / 4, -W / 2 + 0.06 + (W - 0.12) * i / 7, Z + 0.02), 'steel_dark') for i in range(8)]
    pt = P(m, 'tray', 'Feeder Tray (pan) with Liners' + (' & Grizzly Bars (fines fall through gaps)' if grizzly else ''), 'vibrating', tray, explode=(0, 0, 0.4), ref='vf_tray', section='split')
    _vib_keys(m, pt)
    ex = join('ex', [box('eb', (0.3, 0.2, 0.12), (-0.3, 0, Z - 0.1), 'paint_blue', bevel=0.01)] + [cyl(f'em{s}', 0.07, s * (W / 2 + 0.01), s * (W / 2 + 0.22), 'paint_motor', 32, axis='Y', center=(-0.3, 0, Z - 0.1)) for s in (-1, 1)])
    pe = P(m, 'exciters', 'Twin Unbalanced-Motor Exciters (counter-rotating → straight-line vibration)', 'drive', ex, explode=(0, 0, -0.4), ref='vf_exciter', section='keep')
    _vib_keys(m, pe)
    sp = _springs('sp', [(-L / 2 + 0.1, -W / 2 - 0.05), (-L / 2 + 0.1, W / 2 + 0.05), (L / 2 - 0.1, -W / 2 - 0.05), (L / 2 - 0.1, W / 2 + 0.05)], Z - 0.25, Z - 0.02)
    P(m, 'springs', 'Coil-Spring Isolators', 'support', sp, explode=(0, 0, -0.2), ref='vf_springs', section='keep')
    base = [box(f'bs{i}', (0.15, 0.15, Z - 0.25), (x, s * (W / 2 + 0.05), (Z - 0.25) / 2), 'paint_grey') for i, (x, s) in enumerate(((-L / 2 + 0.1, -1), (-L / 2 + 0.1, 1), (L / 2 - 0.1, -1), (L / 2 - 0.1, 1)))]
    P(m, 'support', 'Support Brackets', 'structure', base, explode=(0, 0, -0.3), ref='vf_support', section='keep')
    hp = hopper('hp', 1.0, 0.5, Z + 0.3, Z + 0.9)
    hp.data.transform(Matrix.Translation((-0.45, 0, 0)))
    P(m, 'hopper', 'Feed Hopper (bin outlet)', 'structure', hp, explode=(0, 0, 0.6), ref='vf_hopper')
    rocks_along(m, 'ore', 'Material Moving by Micro-Throws', [(-0.6, Z + 0.06), (L / 2, Z + 0.06), (L / 2 + 0.15, Z - 0.4)], 12, r=0.035 if not grizzly else 0.05)
    if grizzly:
        rocks_along(m, 'fines', 'Fines Falling Through the Grizzly', [(0.2, Z + 0.04), (0.35, Z - 0.1), (0.35, Z - 0.6)], 6, r=0.015, mat='sand', y=0.08)
        chute = join('ch', [box('cb', (L * 0.5, W, 0.01), (L / 4, 0, Z - 0.35), 'paint_grey')])
        P(m, 'bypass_chute', 'Fines Bypass Chute (under the grizzly)', 'structure', chute, explode=(0, 0, -0.5), ref='vf_chute', section='keep')
        m.flow('fines', [(0.3, 0, Z + 0.02), (0.3, 0, Z - 0.6)], 'sand', 0.012, 0.15)
    m.flow('material', [(-0.45, 0, Z + 0.95), (-0.45, 0, Z + 0.08), (L / 2, 0, Z + 0.08), (L / 2 + 0.15, 0, Z - 0.4)], 'flow_discharge', 0.02, 0.3)
    return m


def vibrating_feeder(out):
    return _vib_feeder('vibrating_feeder', 'Electromechanical Vibrating Feeder (Twin Unbalanced Motors)').export(out)


def grizzly_feeder(out):
    return _vib_feeder('grizzly_feeder', 'Vibrating Grizzly Feeder (Feeder Pan + Grizzly Bar Section)', grizzly=True).export(out)


# =============================================================== EQ-198 Rotary airlock feeder
def rotary_airlock_feeder(out):
    m = _model('rotary_airlock_feeder', 'Rotary Airlock (Rotary Valve) Feeder — 8 Pockets')
    CZ, R, W = 0.6, 0.14, 0.3
    hs = csg('hs', [box('ho', (2 * R + 0.08, W, 2 * R + 0.08), (0, 0, CZ), 'cast_iron', bevel=0.01), box('hi', (0.22, W - 0.02, 0.14), (0, 0, CZ + R + 0.08), 'cast_iron'),
                    box('hb', (0.22, W - 0.02, 0.14), (0, 0, CZ - R - 0.08), 'cast_iron')],
             [cyl('bo', R + 0.002, -W / 2 - 0.01, W / 2 + 0.01, 'cast_iron', 96, axis='Y', center=(0, 0, CZ)), box('pi', (0.18, W - 0.06, 0.2), (0, 0, CZ + R + 0.06), 'cast_iron'),
              box('po', (0.18, W - 0.06, 0.2), (0, 0, CZ - R - 0.06), 'cast_iron')], 'cast_iron')
    P(m, 'housing', 'Housing (inlet top, outlet bottom; close rotor clearance)', 'casing', half(hs, 'cast_iron'), explode=(0, 0.4, 0), ref='ra_housing', section='keep')
    rot = [cyl('hub', 0.04, -W / 2 + 0.01, W / 2 - 0.01, 'stainless', 32, axis='Y', center=(0, 0, CZ)), cyl('sh', 0.02, -W / 2 - 0.25, W / 2 + 0.15, 'steel', 16, axis='Y', center=(0, 0, CZ))]
    rot += [rotate(box(f'v{i}', (R - 0.045, W - 0.03, 0.008), (0.04 + (R - 0.045) / 2, 0, CZ), 'stainless'), TAU * i / 8, 'Y', (0, 0, CZ)) for i in range(8)]
    rot += [cyl(f'sd{s}', R - 0.002, s * (W / 2 - 0.01) - 0.005, s * (W / 2 - 0.01) + 0.005, 'stainless', 64, axis='Y', center=(0, 0, CZ)) for s in (1,)]
    pr = P(m, 'rotor', 'Rotor (8 vanes, closed end discs) & Shaft', 'rotating_element', rot, explode=(0, -0.4, 0), ref='ra_rotor', section='keep', pivot=(0, 0, CZ))
    pr.spin('Y', 1)
    ep = cyl('ep', R + 0.04, -W / 2 - 0.03, -W / 2, 'cast_iron', 64, axis='Y', center=(0, 0, CZ))
    P(m, 'end_plate', 'End Cover with Bearing & Shaft Seal (hidden in cutaway)', 'casing', ep, explode=(0, -0.6, 0), ref='ra_housing', section='hide')
    _gearmotor(m, 'drive', 0.0, W / 2 + 0.25, CZ, label='Gearmotor (fixed speed or VFD = feed rate)', ref='ra_drive')
    hp = hopper('hp', 0.5, 0.18, CZ + R + 0.13, CZ + R + 0.55)
    pl = hollow_pipe('pl', [(-0.9, 0, CZ - R - 0.25), (0.9, 0, CZ - R - 0.25)], 0.06, 'paint_grey', 24, t=0.004)
    P(m, 'connections', 'Silo/Hopper Above & Pneumatic Conveying Line Below', 'system_piping', [hp, pl, box('ad', (0.16, 0.16, 0.12), (0, 0, CZ - R - 0.18), 'paint_grey')], explode=(0, 0, 0.4), ref='ra_connections', section='keep')
    rk = m.part('powder', 'Powder in Rotor Pockets', 'flow_tracers', explode=(0, 0, 0), info={'ref': 'flow_tracers'})
    for i in range(8):
        a0 = TAU * (i + 0.5) / 8
        o = box(f'pw{i}', (0.05, W - 0.06, 0.04), (0, 0, 0), 'sand')
        ms = rk.add(o, smooth_angle=30)
        lk, rk_ = [], []
        for f in range(OPERATE_FRAMES + 1):
            a = a0 - TAU * f / OPERATE_FRAMES
            full = 1.0 if math.sin(a) < 0.95 and not (math.cos(a) < 0 and math.sin(a) < -0.3) else 0.0
            rr = R * 0.65
            lk.append((1 + f, (rr * math.cos(a), 0.03, CZ + rr * math.sin(a))))
            rk_.append((1 + f, (0.0, -(a - a0), 0.0)))
        ms.location = lk[0][1]
        m.keyframes(ms, 'Operate', 'location', lk)
        m.keyframes(ms, 'Operate', 'rotation_euler', rk_)
    m.flow('powder', [(0, 0, CZ + R + 0.6), (0, 0, CZ + R), (R * 0.6, 0, CZ), (0, 0, CZ - R), (0, 0, CZ - R - 0.25), (0.9, 0, CZ - R - 0.25)], 'sand', 0.012, 0.15)
    m.flow('conveying_air', [(-0.95, 0, CZ - R - 0.25), (0.95, 0, CZ - R - 0.25)], 'air', 0.01, 0.2)
    return m.export(out)


# =============================================================== EQ-199 Screw feeder
def _screw(name, x0, x1, r_sh, r_fl, lead, cz, mat='steel', t=0.006):
    pts = [(0.0, r_sh * 0.9), (0.0, r_fl), (t, r_fl), (t, r_sh * 0.9)]
    pts = [(u - t / 2, v) for u, v in pts]
    flight = twisted_extrude(name + 'f', [(v, u) for u, v in pts], x0, x1, lead, mat, steps=int((x1 - x0) / lead * 36), axis='X', center=(0, 0, cz))
    shaft = cyl(name + 's', r_sh, x0 - 0.1, x1 + 0.3, 'steel', 24, axis='X', center=(0, 0, cz))
    return join(name, [flight, shaft])


def screw_feeder(out):
    m = _model('screw_feeder', 'Screw Feeder (Variable-Pitch Flight, U-Trough)')
    CZ, X0, X1, R = 0.55, -0.7, 0.7, 0.12
    tr = csg('tr', [cyl('to', R + 0.02, X0 - 0.02, X1 + 0.02, 'paint_grey', 64, axis='X', center=(0, 0, CZ)), box('tt', (X1 - X0 + 0.04, 2 * R + 0.04, R + 0.04), (0, 0, CZ + (R + 0.04) / 2), 'paint_grey')],
             [cyl('ti', R + 0.005, X0, X1, 'paint_grey', 64, axis='X', center=(0, 0, CZ)), box('tii', (X1 - X0, 2 * R + 0.01, R + 0.04), (0, 0, CZ + (R + 0.04) / 2 + 0.005), 'paint_grey'),
              box('dis', (0.16, 2 * R, 0.2), (X1 - 0.12, 0, CZ - R), 'paint_grey')], 'paint_grey')
    P(m, 'trough', 'U-Trough with Discharge Spout', 'casing', tr, explode=(0, 0.4, -0.2), ref='sf_trough')
    sc = _screw('scr', X0 + 0.02, X1 - 0.02, 0.03, R - 0.005, 0.18, CZ)
    ps = P(m, 'screw', 'Screw: Flight on Pipe Shaft (pitch sets volume per turn)', 'rotating_element', sc, explode=(0, -0.4, 0.2), ref='sf_screw', section='keep', pivot=(0, 0, CZ))
    ps.spin('X', -2)
    hp = hopper('hp', 0.6, 0.35, CZ + R + 0.04, CZ + R + 0.5)
    hp.data.transform(Matrix.Translation((-0.4, 0, 0)))
    P(m, 'inlet_hopper', 'Inlet Hopper', 'structure', hp, explode=(0, 0, 0.4), ref='sf_hopper')
    add_coupling(m, 'coupling', X1 + 0.18, X1 + 0.26, CZ, 0.05, 0.03, explode=(0.3, 0, 0), revs=-2, foot_z=0.0)
    add_motor_h(m, 'm_', X1 + 0.28, CZ, 0.12, 0.34, 0.15, 0.03, 0.0, explode_dx=0.5, revs=-2, label='Gearmotor')
    st = [box(f'lg{i}', (0.06, 2 * R, CZ - R - 0.02), (x, 0, (CZ - R - 0.02) / 2), 'paint_grey') for i, x in enumerate((X0 + 0.1, X1 - 0.3))] + [box('mb', (0.5, 0.35, 0.15), (X1 + 0.45, 0, 0.075), 'paint_grey')]
    P(m, 'supports', 'Supports & Drive Base', 'structure', st, explode=(0, 0, -0.3), ref='sf_supports', section='keep')
    path = [(-0.4, 0.05, CZ + R + 0.45), (-0.4, 0.05, CZ)] + [(X0 + 0.3 + (X1 - X0 - 0.45) * k / 40, (R * 0.6) * math.sin(TAU * k / 40 * 6), CZ - (R * 0.6) * math.cos(TAU * k / 40 * 6) * 0.5) for k in range(41)] + [(X1 - 0.12, 0, CZ - R - 0.2)]
    m.flow('material', path, 'sand', 0.01, 0.2)
    rocks_along(m, 'bulk', 'Bulk Solids Conveyed by the Flight', [(-0.4, CZ + 0.15), (X1 - 0.12, CZ - 0.05), (X1 - 0.12, CZ - R - 0.3)], 10, r=0.02, mat='sand', y=0.04)
    return m.export(out)


# =============================================================== EQ-200 Weigh feeder
def weigh_feeder(out):
    m = _model('weigh_feeder', 'Belt Weigh Feeder (Gravimetric, Load Cell + Speed Sensor)')
    Z = 0.6
    belt_loop(m, 'bf', -0.8, 0.8, Z, 0.08, 0.5, revs=2, markers=14, label='Feeder Belt', foot_z=0.0)
    lc = join('lc', [cyl('wi', 0.028, -0.18, 0.18, 'chrome', 16, axis='Y', center=(0.1, 0, Z + 0.05)), box('lcb', (0.08, 0.06, 0.08), (0.1, 0.33, Z - 0.0), 'paint_blue', bevel=0.006),
                     box('lca', (0.03, 0.4, 0.03), (0.1, 0.16, Z + 0.01), 'steel')])
    plc = P(m, 'weigh_idler', 'Weigh Idler on Load Cell (measures belt load, kg/m)', 'instrument', lc, explode=(0, 0.4, 0.2), ref='wf_loadcell', section='keep')
    keys_loop(m, plc, lambda t: (0, 0, -0.002 * (0.5 + 0.5 * math.sin(TAU * 3 * t))))
    sp = join('sp', [cyl('spw', 0.04, 0.27, 0.29, 'paint_red', 24, axis='Y', center=(-0.8, 0, Z)), box('spb', (0.08, 0.04, 0.06), (-0.8, 0.31, Z + 0.06), 'paint_blue')])
    P(m, 'speed_sensor', 'Speed Sensor on Tail Pulley (belt speed, m/s)', 'instrument', sp, explode=(-0.3, 0.3, 0), ref='wf_speed', section='keep')
    ctl = box('ctl', (0.3, 0.12, 0.4), (0.0, 0.6, 0.9), 'paint_grey', bevel=0.01)
    P(m, 'controller', 'Weigh Controller (rate = load × speed; adjusts belt speed via VFD)', 'controls', ctl, explode=(0, -0.3, 0.2), ref='wf_controller', section='keep')
    hp = hopper('hp', 0.5, 0.3, Z + 0.15, Z + 0.6)
    hp.data.transform(Matrix.Translation((-0.55, 0, 0)))
    gate = box('gt', (0.02, 0.32, 0.15), (-0.38, 0, Z + 0.17), 'steel')
    P(m, 'inlet', 'Inlet Hopper & Shear Gate (sets bed depth)', 'structure', [hp, gate], explode=(0, 0, 0.4), ref='wf_inlet')
    _gearmotor(m, 'drive', 0.8, 0.45, Z, label='Variable-Speed Gearmotor (VFD)', ref='wf_drive')
    rocks_along(m, 'material', 'Material on Belt', [(-0.6, Z + 0.1), (0.85, Z + 0.1), (0.95, Z - 0.3)], 16, r=0.018, mat='sand', y=0.05, loops=1.0)
    m.flow('material', [(-0.55, 0, Z + 0.65), (-0.55, 0, Z + 0.12), (0.8, 0, Z + 0.12), (0.92, 0, Z - 0.35)], 'sand', 0.012, 0.25)
    m.flow('signal', [(0.1, 0.33, Z), (0.0, 0.55, 0.9), (0.8, 0.45, Z + 0.1)], 'electric', 0.006, 0.15)
    return m.export(out)


# =============================================================== EQ-201 Vibrating screen
def vibrating_screen(out):
    m = _model('vibrating_screen', 'Inclined Vibrating Screen (Double Deck, Circular Motion)')
    Z, L, W = 0.9, 1.8, 0.8
    ang = math.radians(18)

    def deck(name, dz, mat, hole):
        d = box(name, (L, W - 0.04, 0.01), (0, 0, dz), mat)
        grid = [box(f'{name}g{i}', (L, 0.006, 0.012), (0, -W / 2 + 0.03 + (W - 0.06) * i / 12, dz + 0.004), 'steel_dark') for i in range(13)]
        return join(name + 'j', [d] + grid)
    body = [box('sl', (L, 0.02, 0.5), (0, -W / 2, 0.15), 'paint_green'), box('sr', (L, 0.02, 0.5), (0, W / 2, 0.15), 'paint_green'),
            deck('d1', 0.25, 'rubber', 0.04), deck('d2', 0.02, 'steel', 0.02), cyl('cb', 0.04, -W / 2 - 0.02, W / 2 + 0.02, 'steel', 16, axis='Y', center=(0, 0, 0.45))]
    body = join('body', body)
    body.data.transform(Matrix.Translation((0, 0, Z)) @ Matrix.Rotation(ang, 4, 'Y'))
    pb = P(m, 'screen_body', 'Screen Body: Side Plates, Top Deck (coarse) & Bottom Deck (fine mesh)', 'vibrating', body, explode=(0, 0, 0.4), ref='vs_body', section='split')
    keys_loop(m, pb, lambda t: (0.008 * math.cos(TAU * 8 * t), 0, 0.008 * math.sin(TAU * 8 * t)))
    ex = join('ex', [cyl('exs', 0.03, -W / 2 - 0.1, W / 2 + 0.1, 'steel', 16, axis='Y', center=(0, 0, 0)), cyl('ew1', 0.09, -W / 2 - 0.1, -W / 2 - 0.04, 'steel', 24, axis='Y', center=(0, 0, 0)),
                     cyl('ew2', 0.09, W / 2 + 0.04, W / 2 + 0.1, 'steel', 24, axis='Y', center=(0, 0, 0)),
                     box('cw1', (0.08, 0.06, 0.06), (0.06, -W / 2 - 0.07, 0), 'paint_red'), box('cw2', (0.08, 0.06, 0.06), (0.06, W / 2 + 0.07, 0), 'paint_red')])
    ex.data.transform(Matrix.Translation((0, 0, Z + 0.47)))
    pe = P(m, 'exciter', 'Exciter Shaft with Unbalanced Weights (circular throw)', 'drive', ex, explode=(0, 0, 0.6), ref='vs_exciter', section='keep', pivot=(0, 0, Z + 0.47))
    pe.spin('Y', 8)
    sp = _springs('sp', [(-L / 2 + 0.1, -W / 2 - 0.08), (-L / 2 + 0.1, W / 2 + 0.08), (L / 2 - 0.1, -W / 2 - 0.08), (L / 2 - 0.1, W / 2 + 0.08)], Z - 0.25, Z + 0.0, r=0.035)
    sp.data.transform(Matrix.Translation((0, 0, 0)))
    P(m, 'springs', 'Spring Supports', 'support', sp, explode=(0, 0, -0.3), ref='vs_springs', section='keep')
    st = [box(f'st{i}', (0.12, 0.12, Z - 0.25 + (0.3 if i < 2 else -0.3) * 0), (x, s * (W / 2 + 0.08), (Z - 0.25) / 2), 'paint_grey') for i, (x, s) in enumerate(((-L / 2 + 0.1, -1), (-L / 2 + 0.1, 1), (L / 2 - 0.1, -1), (L / 2 - 0.1, 1)))]
    P(m, 'support_frame', 'Support Frame', 'structure', st, explode=(0, 0, -0.4), ref='vs_frame', section='keep')
    ch = [box('ch1', (0.5, W, 0.01), (L / 2 + 0.3, 0, Z - 0.35), 'paint_grey'), box('ch2', (L, W, 0.01), (0.0, 0, Z - 0.6), 'paint_grey')]
    P(m, 'chutes', 'Discharge Chutes (oversize, middlings, fines)', 'structure', ch, explode=(0, 0, -0.5), ref='vs_chutes', section='keep')
    def dk(x, dz):
        return (x * math.cos(ang), Z + dz + 0.03 + x * (-math.sin(ang)) * -1 * -1)
    top = [(-L / 2 * math.cos(ang), Z + 0.25 + L / 2 * math.sin(ang) + 0.06), (L / 2 * math.cos(ang), Z + 0.25 - L / 2 * math.sin(ang) + 0.06), (L / 2 + 0.3, Z - 0.3)]
    bot = [(-0.4, Z + 0.25 + 0.4 * math.sin(ang) + 0.04), (-0.3, Z + 0.02 + 0.3 * math.sin(ang) + 0.03), (L / 2 * math.cos(ang), Z + 0.02 - L / 2 * math.sin(ang) + 0.03), (L / 2 + 0.1, Z - 0.5)]
    fines = [(0.0, Z + 0.02 + 0.02), (0.05, Z - 0.58)]
    rocks_along(m, 'oversize', 'Oversize (stays on top deck)', top, 8, r=0.045)
    rocks_along(m, 'middlings', 'Middlings (pass top deck, retained on bottom deck)', bot, 8, r=0.025, mat='ore', y=0.12)
    rocks_along(m, 'fines', 'Fines (pass both decks)', fines, 6, r=0.012, mat='sand', y=0.2)
    m.flow('feed', [(-L / 2 - 0.3, 0, Z + 0.7)] + [(x, 0, z) for x, z in top], 'flow_discharge', 0.015, 0.25)
    m.flow('undersize', [(0.0, 0.05, Z + 0.25), (0.0, 0.05, Z - 0.6)], 'sand', 0.01, 0.15)
    return m.export(out)


# =============================================================== EQ-202 Trommel screen
def trommel_screen(out):
    m = _model('trommel_screen', 'Trommel (Rotary Drum) Screen')
    R, L, Z = 0.45, 2.2, 0.9
    ang = math.radians(4)
    drum = csg('dr', [cyl('do', R, -L / 2, L / 2, 'steel', 96, axis='X', center=(0, 0, 0))],
               [cyl('di', R - 0.008, -L / 2 - 0.01, L / 2 + 0.01, 'steel', 96, axis='X', center=(0, 0, 0))] +
               [rotate(cyl(f'h{i}{j}', 0.025, -0.02, R + 0.05, 'steel', 8, center=(-L / 2 + 0.6 + 0.12 * i, 0, 0)), TAU * j / 18, 'X') for i in range(12) for j in range(18)], 'steel')
    tyres = [cyl(f'ty{i}', R + 0.05, x - 0.05, x + 0.05, 'steel_dark', 64, axis='X', center=(0, 0, 0), r_in=R - 0.002) for i, x in enumerate((-L / 2 + 0.2, L / 2 - 0.2))]
    gr = ring_of('gr', 60, lambda i: box(f'gt{i}', (0.05, 0.025, 0.04), (-0.1, 0, R + 0.06), 'steel_dark'))
    allp = join('trm', [drum] + tyres + [gr, cyl('gbd', R + 0.04, -0.13, -0.07, 'steel_dark', 64, axis='X', center=(0, 0, 0), r_in=R)])
    allp.data.transform(Matrix.Translation((0, 0, Z)) @ Matrix.Rotation(ang, 4, 'Y'))
    pd = P(m, 'drum', 'Rotating Perforated Drum with Riding Tyres & Girth Gear', 'rotating_element', allp, explode=(0, 0, 0.5), ref='tr_drum', section='keep', pivot=(0, 0, Z))
    for mesh in pd.meshes:
        ax = Matrix.Rotation(ang, 3, 'Y') @ Vector((1, 0, 0))
        axis_rot_keys(m, mesh, ax, lambda t: TAU * 1.0 * t)
    rl = []
    for x in (-L / 2 + 0.2, L / 2 - 0.2):
        zc = Z - x * math.sin(ang)
        for s in (-1, 1):
            yy, zz = s * (R + 0.12) * math.sin(math.radians(35)), zc - (R + 0.12) * math.cos(math.radians(35))
            rl.append(cyl(f'tr{x}{s}', 0.07, x - 0.06, x + 0.06, 'steel', 32, axis='X', center=(0, yy, zz)))
            rl.append(box(f'tb{x}{s}', (0.16, 0.12, zz - 0.07), (x, yy, (zz - 0.07) / 2), 'paint_grey'))
    P(m, 'trunnions', 'Trunnion Rollers & Supports', 'support', rl, explode=(0, 0, -0.3), ref='tr_trunnions', section='keep')
    pn = cyl('pn', 0.06, -0.15, -0.05, 'steel', 24, axis='X', center=(0, R + 0.15, Z + 0.02))
    _gearmotor(m, 'drive', -0.1, R + 0.4, Z - 0.1, label='Drive Gearmotor & Pinion', ref='tr_drive')
    hood = half(csg('hd', [cyl('ho', R + 0.18, -L / 2 + 0.4, L / 2 - 0.4, 'paint_grey', 64, axis='X', center=(0, 0, Z))], [cyl('hi', R + 0.16, -L / 2, L / 2, 'paint_grey', 64, axis='X', center=(0, 0, Z))], 'paint_grey'), 'paint_grey')
    P(m, 'hood_hopper', 'Dust Hood & Undersize Hopper', 'structure', [hood, pn], explode=(0, 0.6, 0.3), ref='tr_hood', section='keep')
    fc = box('fc', (0.5, 0.3, 0.02), (-L / 2 - 0.15, 0, Z + 0.1), 'paint_grey')
    P(m, 'feed_chute', 'Feed Chute', 'structure', fc, explode=(-0.3, 0, 0.2), ref='tr_feed', section='keep')
    rocks_along(m, 'oversize', 'Oversize Tumbling to the Discharge End', [(-L / 2 - 0.3, Z + 0.2), (-L / 2, Z - R + 0.12), (L / 2, Z - R + 0.06), (L / 2 + 0.3, Z - R - 0.3)], 10, r=0.05)
    rocks_along(m, 'fines', 'Fines Falling Through the Perforations', [(-0.3, Z - R + 0.05), (-0.3, 0.2)], 5, r=0.015, mat='sand', y=0.1)
    m.flow('feed', [(-L / 2 - 0.4, 0, Z + 0.2), (-L / 2, 0, Z - R + 0.12), (L / 2, 0, Z - R + 0.06), (L / 2 + 0.3, 0, Z - R - 0.3)], 'flow_discharge', 0.015, 0.25)
    m.flow('undersize', [(0.0, 0.05, Z - R + 0.05), (0.0, 0.05, 0.2)], 'sand', 0.01, 0.15)
    return m.export(out)


# =============================================================== crushers
def jaw_crusher(out):
    m = _model('jaw_crusher', 'Single-Toggle Jaw Crusher')
    E = 0.012                                          # eccentric throw
    C = Vector((0.25, 0, 1.25))                          # eccentric shaft centre
    K = Vector((0.45, 0, 0.45))                          # toggle seat (fixed)
    Lt, Lj = 0.22, 0.75

    def jaw_pose(t):
        th = TAU * 2 * t
        T = C + Vector((E * math.cos(th), 0, E * math.sin(th)))
        # bottom point B: |B-K| = Lt, |B-T| = Lj  (choose the solution with B.x < K.x)
        d = (T - K).length
        a = (Lt * Lt - Lj * Lj + d * d) / (2 * d)
        h = math.sqrt(max(0.0, Lt * Lt - a * a))
        mid = K + (T - K) * (a / d)
        nrm = Vector(((T - K).z, 0, -(T - K).x)).normalized()
        B = mid + nrm * h
        if B.x > K.x:
            B = mid - nrm * h
        return T, B
    T0, B0 = jaw_pose(0)
    fr = csg('fr', [box('fo', (1.2, 0.9, 1.4), (0.0, 0, 0.8), 'paint_orange', bevel=0.02)],
             [box('fi', (0.85, 0.7, 1.5), (-0.02, 0, 0.85), 'paint_orange'), cyl('bb', 0.08, -0.6, 0.6, 'paint_orange', 32, axis='Y', center=(C.x, 0, C.z))], 'paint_orange')
    P(m, 'frame', 'Main Frame (fabricated)', 'casing', fr, explode=(0, 0.6, 0), ref='jc_frame')
    fj = join('fj', [box('fjb', (0.08, 0.68, 1.1), (-0.32, 0, 0.85), 'steel_dark')] + [box(f'ft{i}', (0.03, 0.66, 0.04), (-0.27, 0, 0.4 + 0.1 * i), 'steel_dark') for i in range(10)])
    P(m, 'fixed_jaw', 'Fixed Jaw Die (corrugated manganese liner)', 'wear_parts', fj, explode=(-0.4, 0, 0), ref='jc_fixed_jaw', section='keep')
    jaw = join('sj', [box('sjb', (0.08, 0.66, Lj), (0, 0, -Lj / 2), 'steel_dark'), box('sjl', (0.03, 0.64, Lj * 0.9), (-0.05, 0, -Lj / 2), 'steel_dark'),
                      cyl('sjh', 0.09, -0.3, 0.3, 'paint_orange', 32, axis='Y', center=(0, 0, 0))])
    ang0 = math.atan2((T0 - B0).x, (T0 - B0).z)
    jaw = rotate(jaw, ang0, 'Y')
    jaw.data.transform(Matrix.Translation(T0))
    pj = m.part('swing_jaw', 'Swing (Moving) Jaw on Eccentric Shaft', 'crushing', explode=(0.3, -0.5, 0), info={'ref': 'jc_swing_jaw'})
    ms = pj.add(jaw, smooth_angle=30)
    local_pivot(ms, tuple(T0))
    lk, rk = [], []
    for f in range(OPERATE_FRAMES + 1):
        T, B = jaw_pose(f / OPERATE_FRAMES)
        a = math.atan2((T - B).x, (T - B).z)
        lk.append((1 + f, tuple(T)))
        rk.append((1 + f, (0.0, a - ang0, 0.0)))
    m.keyframes(ms, 'Operate', 'location', lk)
    m.keyframes(ms, 'Operate', 'rotation_euler', rk)
    tg = box('tg', (Lt, 0.5, 0.04), (0, 0, 0), 'steel')
    a0 = math.atan2((B0 - K).z, (B0 - K).x)
    tg.data.transform(Matrix.Translation((K + B0) / 2) @ Matrix.Rotation(-a0, 4, 'Y'))
    pt = m.part('toggle_plate', 'Toggle Plate (safety element) & Tension Rod', 'crushing', explode=(0.5, 0, -0.3), info={'ref': 'jc_toggle'})
    mt = pt.add(tg, smooth_angle=30)
    local_pivot(mt, tuple(K))
    tk = []
    for f in range(OPERATE_FRAMES + 1):
        T, B = jaw_pose(f / OPERATE_FRAMES)
        tk.append((1 + f, (0.0, -(math.atan2((B - K).z, (B - K).x) - a0), 0.0)))
    m.keyframes(mt, 'Operate', 'rotation_euler', tk)
    ecc = [cyl('es', 0.06, -0.75, 0.75, 'steel', 32, axis='Y', center=(C.x, 0, C.z)), cyl('fw1', 0.4, -0.72, -0.62, 'cast_iron', 64, axis='Y', center=(C.x, 0, C.z)),
           cyl('fw2', 0.4, 0.62, 0.72, 'cast_iron', 64, axis='Y', center=(C.x, 0, C.z))] + [box(f'sp{k}', (0.05, 0.08, 0.32), (C.x, -0.67, C.z + 0.2), 'cast_iron') for k in range(0)]
    pe = P(m, 'eccentric_flywheels', 'Eccentric Shaft, Flywheel & Grooved Drive Pulley', 'rotating_element', ecc, explode=(0, -0.8, 0.3), ref='jc_eccentric', section='split', pivot=(C.x, 0, C.z))
    pe.spin('Y', 2)
    rocks_along(m, 'rocks', 'Rock Crushed Progressively in the Chamber', [(-0.15, 1.6), (-0.15, 1.2), (-0.2, 0.8), (-0.25, 0.4), (-0.25, 0.0)], 8, r=0.05)
    rocks_along(m, 'product', 'Crushed Product', [(-0.23, 0.35), (-0.23, -0.05)], 6, r=0.02, y=0.12)
    m.flow('material', [(-0.15, 0, 1.7), (-0.18, 0, 1.0), (-0.24, 0, 0.35), (-0.24, 0, -0.1)], 'flow_discharge', 0.015, 0.25)
    wz = [box(f'wz{i}', (0.014, 0.6, z1 - z0), (-0.246, 0, (z0 + z1) / 2), mat) for i, (z0, z1, mat) in
          enumerate(((0.33, 0.62, 'wear_severe'), (0.62, 0.98, 'wear_moderate'), (0.98, 1.38, 'wear_light')))]
    m.overlay('wear', join('wz', wz), 'Jaw die wear zones',
              'The dies wear fastest in the lower third, near the closed-side setting, where the gap is tightest and most of the crushing work is done (purple). '
              'Wear there opens the setting and makes the product coarser, so the setting is re-adjusted with shims or wedges. Many dies are symmetrical and can be turned '
              'top-to-bottom once to use the less-worn upper part.', split=True)
    return m.export(out)


def _gyr(m, R_top, R_bot, z_bot, z_top, R_m_top, R_m_bot, ecc_ang=0.03, spider=False, revs=2, label='Cone'):
    bowl = csg('bowl', [lathe('bo', [(R_bot + 0.12, z_bot), (R_top + 0.15, z_top), (0.0, z_top), (0.0, z_bot)], 'paint_orange', 96)],
               [lathe('bi', [(R_bot, z_bot - 0.01), (R_top, z_top + 0.01), (0.0, z_top + 0.01), (0.0, z_bot - 0.01)], 'paint_orange', 96)], 'paint_orange')
    conc = csg('conc', [lathe('co', [(R_bot + 0.002, z_bot), (R_top + 0.002, z_top), (0, z_top), (0, z_bot)], 'steel_dark', 96)],
               [lathe('ci', [(R_bot - 0.03, z_bot - 0.01), (R_top - 0.03, z_top + 0.01), (0, z_top + 0.01), (0, z_bot - 0.01)], 'steel_dark', 96)], 'steel_dark')
    P(m, 'shell', f'{label} Shell / Bowl (top & bottom)', 'casing', bowl, explode=(0, 0.6, 0.3), ref='cc_shell')
    P(m, 'concaves', 'Concave Liners (manganese steel)', 'wear_parts', conc, explode=(0, 0.4, 0.5), ref='cc_concave')
    mant = join('mant', [lathe('mn', [(0.0, z_bot - 0.05), (R_m_bot, z_bot - 0.05), (R_m_top, z_top - 0.1), (0.0, z_top)], 'steel_dark', 96),
                         cyl('msh', 0.06, z_bot - 0.6, z_top + 0.15, 'steel', 24)])
    pm = m.part('mantle', 'Mantle & Main Shaft (gyrating head)', 'crushing', pivot=(0, 0, z_bot - 0.6), explode=(0, -0.6, 0.6), info={'ref': 'cc_mantle'})
    ms = pm.add(mant, smooth_angle=35)
    keys = []
    for f in range(OPERATE_FRAMES + 1):
        ph = TAU * revs * f / OPERATE_FRAMES
        Rm = Matrix.Rotation(ph, 3, 'Z') @ Matrix.Rotation(ecc_ang, 3, 'X') @ Matrix.Rotation(-ph, 3, 'Z')
        e = Rm.to_euler('XYZ')
        keys.append((1 + f, (e.x, e.y, e.z)))
    m.keyframes(ms, 'Operate', 'rotation_euler', keys)
    ecc = join('ecc', [cyl('eb', 0.12, z_bot - 0.62, z_bot - 0.38, 'bronze', 48, r_in=0.065), cyl('bg', 0.25, z_bot - 0.45, z_bot - 0.4, 'steel', 64, r_in=0.12)])
    pe = P(m, 'eccentric', 'Eccentric Bushing & Bevel Gear (rotates → head gyrates)', 'rotating_element', ecc, explode=(0, -0.4, -0.3), ref='cc_eccentric', section='keep')
    pe.spin('Z', revs)
    pn = join('pn', [cyl('ps', 0.035, 0.0, 0.7, 'steel', 16, axis='X', center=(0, 0, z_bot - 0.48)), cyl('pg', 0.07, 0.18, 0.24, 'steel', 32, axis='X', center=(0, 0, z_bot - 0.48)),
                     cyl('pp', 0.18, 0.6, 0.68, 'cast_iron', 48, axis='X', center=(0, 0, z_bot - 0.48))])
    pp = P(m, 'pinion_shaft', 'Countershaft, Bevel Pinion & V-Belt Sheave', 'rotating_element', pn, explode=(0.5, 0, 0), ref='cc_pinion', section='keep', pivot=(0, 0, z_bot - 0.48))
    pp.spin('X', revs * 3)
    base = csg('base', [cyl('bs', R_bot + 0.2, 0.0, z_bot, 'paint_orange', 64)], [cyl('bsi', R_bot - 0.02, 0.05, z_bot + 0.01, 'paint_orange', 64), box('bw', (0.6, 0.3, 0.3), (0.35, 0, z_bot - 0.48), 'paint_orange')], 'paint_orange')
    P(m, 'main_frame', 'Main Frame / Bottom Shell (discharge opening)', 'casing', base, explode=(0, 0.5, -0.4), ref='cc_shell')
    if spider:
        sp = join('sp', [cyl('sph', 0.12, z_top, z_top + 0.15, 'paint_orange', 32)] + [box(f'sa{s}', (2 * R_top + 0.3, 0.12, 0.1), (0, 0, z_top + 0.07), 'paint_orange') for s in (0,)])
        P(m, 'spider', 'Spider (top bearing support arms)', 'casing', sp, explode=(0, 0, 0.6), ref='cc_spider', section='keep')
    rocks_along(m, 'rocks', 'Rock Squeezed Between Mantle and Concave', [(R_top * 0.6, z_top + 0.3), (R_top * 0.7, z_top - 0.05), ((R_bot + R_m_bot) / 2, z_bot + 0.05), (R_bot * 0.9, 0.05)], 8, r=0.04, y=0.05)
    m.flow('material', [(R_top * 0.6, 0, z_top + 0.4), (R_top * 0.75, 0, z_top - 0.05), ((R_bot + R_m_bot) / 2, 0, z_bot + 0.02), (R_bot * 0.9, 0, 0.0)], 'flow_discharge', 0.015, 0.25)
    rz = lambda z: (R_bot - 0.03) + (R_top - R_bot) * (z - z_bot) / (z_top - z_bot) - 0.004
    zs = [z_bot, z_bot + 0.3 * (z_top - z_bot), z_bot + 0.65 * (z_top - z_bot), z_top]
    rings = [lathe(f'wr{i}', [(rz(za), za), (rz(zb), zb), (rz(zb) - 0.005, zb), (rz(za) - 0.005, za)], mt, 96)
             for i, (za, zb, mt) in enumerate(((zs[0], zs[1], 'wear_severe'), (zs[1], zs[2], 'wear_moderate'), (zs[2], zs[3], 'wear_light')))]
    m.overlay('wear', join('wr', rings), 'Concave and mantle wear profile',
              'Wear is heaviest in the lower (parallel) zone, where the particles are smallest, the gap is closest and the crushing force is concentrated (purple). '
              'As the liners wear the closed-side setting opens, so it is re-adjusted (hydraulic or screw adjustment) to hold product size; liners are changed when '
              'the profile can no longer hold the setting or capacity drops.', split=True)


def cone_crusher(out):
    m = _model('cone_crusher', 'Cone Crusher (Secondary/Tertiary)')
    _gyr(m, 0.42, 0.62, 0.85, 1.25, 0.18, 0.58, ecc_ang=0.03, label='Cone Crusher')
    return m.export(out)


def gyratory_crusher(out):
    m = _model('gyratory_crusher', 'Primary Gyratory Crusher')
    _gyr(m, 0.7, 0.45, 0.8, 2.1, 0.15, 0.4, ecc_ang=0.015, spider=True, label='Gyratory Crusher')
    return m.export(out)


def _hsi(m, hammers=False):
    CZ, W, R = 0.75, 0.6, 0.3
    hs = csg('hs', [box('ho', (1.3, W + 0.08, 1.2), (0.05, 0, CZ + 0.15), 'paint_green', bevel=0.02)],
             [box('hi', (1.22, W, 1.12), (0.05, 0, CZ + 0.15), 'paint_green'), box('fi', (0.35, W, 0.3), (-0.4, 0, CZ + 0.75), 'paint_green'), box('bo', (0.8, W, 0.2), (0.05, 0, CZ - 0.45), 'paint_green')], 'paint_green')
    P(m, 'housing', 'Housing with Wear Liners', 'casing', hs, explode=(0, 0.6, 0), ref='ic_housing')
    rot = [cyl('rc', R * 0.75, -W / 2 + 0.03, W / 2 - 0.03, 'steel', 48, axis='Y', center=(0, 0, CZ)), cyl('rsh', 0.06, -W / 2 - 0.4, W / 2 + 0.25, 'steel', 24, axis='Y', center=(0, 0, CZ))]
    if hammers:
        rot += [cyl(f'pd{i}', R * 0.8, s - 0.01, s + 0.01, 'steel', 48, axis='Y', center=(0, 0, CZ)) for i, s in enumerate((-0.2, 0.0, 0.2))]
        for k in range(4):
            a = TAU * k / 4
            for j, yy in enumerate((-0.1, 0.1)):
                hb = box(f'hm{k}{j}', (0.06, 0.12, R * 0.55), (0, yy, CZ + R * 0.75 + R * 0.25), 'steel_dark', bevel=0.008)
                rot.append(rotate(hb, a, 'Y', (0, 0, CZ)))
    else:
        rot += [rotate(box(f'bb{k}', (0.05, W - 0.06, R * 0.35), (0, 0, CZ + R * 0.85), 'steel_dark'), TAU * k / 4, 'Y', (0, 0, CZ)) for k in range(4)]
    pr = P(m, 'rotor', 'Rotor with ' + ('Swing Hammers' if hammers else 'Blow Bars') + ' & Shaft', 'rotating_element', rot, explode=(0, -0.6, 0), ref='ic_rotor', section='keep', pivot=(0, 0, CZ))
    pr.spin('Y', -3)
    if hammers:
        grate = [box(f'gr{i}', (0.03, W - 0.02, 0.05), (R * 1.05 * math.cos(math.radians(-60 - 12 * i)), 0, CZ + R * 1.05 * math.sin(math.radians(-60 - 12 * i))), 'steel_dark') for i in range(6)]
        bp = box('bp', (0.05, W - 0.02, 0.35), (R + 0.12, 0, CZ + 0.2), 'steel_dark')
        P(m, 'grate_breaker', 'Grate Bars (sizing screen) & Breaker Plate', 'wear_parts', grate + [bp], explode=(0, 0.4, -0.4), ref='ic_aprons', section='keep')
        wz = [box('wbp', (0.006, W - 0.04, 0.33), (R + 0.09, 0, CZ + 0.2), 'wear_severe')] + \
             [box(f'wgr{i}', (0.035, W - 0.04, 0.006), (R * 1.0 * math.cos(math.radians(-60 - 12 * i)), 0, CZ + R * 1.0 * math.sin(math.radians(-60 - 12 * i)) + 0.0), 'wear_moderate') for i in range(6)]
        m.overlay('wear', join('wz', wz), 'Wear on the breaker plate, grate and hammer tips',
                  'The breaker plate takes the direct impact of material thrown by the hammers (purple); the grate bars wear from abrasion as the product is forced through '
                  '(pink), which widens the openings and coarsens the product. Hammer tips wear too — hammers are turned or reversed to use all four edges before replacement, '
                  'and replaced in matched-weight sets to keep the rotor balanced.', split=True)
    else:
        ap = []
        for i, (zz, ang) in enumerate(((CZ + 0.45, -0.6), (CZ + 0.15, -1.0))):
            a = box(f'ap{i}', (0.04, W - 0.02, 0.35), (R + 0.18, 0, zz), 'steel_dark')
            ap.append(rotate(a, ang * 0.3, 'Y', (R + 0.18, 0, zz + 0.17)))
            ap.append(cyl(f'as{i}', 0.03, -W / 2 - 0.05, W / 2 + 0.05, 'steel', 16, axis='Y', center=(R + 0.18, 0, zz + 0.17)))
        P(m, 'impact_aprons', 'Impact Aprons (curtains) — adjustable gap sets product size', 'wear_parts', ap, explode=(0.4, 0.4, 0), ref='ic_aprons', section='keep')
        wz = []
        for i, (zz, ang) in enumerate(((CZ + 0.45, -0.6), (CZ + 0.15, -1.0))):
            w = box(f'wa{i}', (0.006, W - 0.06, 0.33), (R + 0.155, 0, zz), 'wear_moderate' if i == 0 else 'wear_severe')
            wz.append(rotate(w, ang * 0.3, 'Y', (R + 0.18, 0, zz + 0.17)))
        m.overlay('wear', join('wz', wz), 'Apron and blow-bar wear',
                  'The lower (secondary) apron sees finer, faster material and a closer gap, so it wears most (purple). Blow bars wear on their leading edge; they are turned '
                  'end-for-end or reversed, and replaced in opposite pairs to keep the rotor balanced. Worn bars and aprons open the effective gap and coarsen the product.', split=True)
    _gearmotor(m, 'drive', 0.0, W / 2 + 0.45, CZ - 0.6, label='Drive (motor & V-belts)', ref='ic_drive')
    rocks_along(m, 'rocks', 'Feed Thrown Against the ' + ('Breaker Plate & Forced Through Grate' if hammers else 'Aprons'),
                [(-0.4, CZ + 0.95), (-0.3, CZ + 0.4), (-0.05, CZ + R + 0.05), (R + 0.12, CZ + 0.35), (R * 0.6, CZ - R - 0.1), (0.05, CZ - 0.7)], 9, r=0.035)
    m.flow('material', [(-0.4, 0, CZ + 1.0), (-0.3, 0, CZ + 0.4), (-0.05, 0, CZ + R + 0.05), (R + 0.12, 0, CZ + 0.35), (R * 0.6, 0, CZ - R - 0.1), (0.05, 0, CZ - 0.7)], 'flow_discharge', 0.015, 0.25)


def impact_crusher(out):
    m = _model('impact_crusher', 'Horizontal Shaft Impact (HSI) Crusher')
    _hsi(m, hammers=False)
    return m.export(out)


def hammer_crusher(out):
    m = _model('hammer_crusher', 'Hammer Mill / Hammer Crusher (Swing Hammers + Grate)')
    _hsi(m, hammers=True)
    return m.export(out)


def roller_crusher(out):
    m = _model('roller_crusher', 'Double Roll Crusher (Toothed Rolls, Spring Relief)')
    CZ, R, W, G = 0.7, 0.25, 0.6, 0.02
    for i, (x, sg, nm) in enumerate(((-R - G / 2, -1, 'Fixed Roll'), (R + G / 2, 1, 'Floating Roll (spring-loaded)'))):
        rl = [cyl(f'r{i}', R - 0.02, -W / 2, W / 2, 'steel', 64, axis='Y', center=(x, 0, CZ)), cyl(f's{i}', 0.05, -W / 2 - 0.35, W / 2 + 0.3, 'steel', 24, axis='Y', center=(x, 0, CZ))]
        rl += [rotate(box(f't{i}{k}', (0.05, W - 0.02, 0.045), (x, 0, CZ + R - 0.01), 'steel_dark'), TAU * k / 16 + (math.pi / 16 if i else 0), 'Y', (x, 0, CZ)) for k in range(16)]
        pr = P(m, f'roll_{i + 1}', nm, 'rotating_element', rl, explode=(sg * 0.4, -0.4, 0), ref='rc_roll', section='keep', pivot=(x, 0, CZ))
        pr.spin('Y', -sg * 1.0 * -1)
    fr = csg('fr', [box('fo', (2 * (2 * R + G) + 0.4, W + 0.2, 2 * R + 0.3), (0, 0, CZ), 'paint_blue', bevel=0.02)],
             [box('fi', (2 * (2 * R + G) + 0.2, W + 0.02, 2 * R + 0.4), (0, 0, CZ), 'paint_blue')] + [cyl(f'bb{i}', 0.06, -W, W, 'paint_blue', 24, axis='Y', center=(x, 0, CZ)) for i, x in enumerate((-R - G / 2, R + G / 2))], 'paint_blue')
    P(m, 'frame', 'Frame with Bearing Housings', 'casing', fr, explode=(0, 0.6, 0), ref='rc_frame')
    sp = join('sp', [spring(f'sp{s}', (0, s * (W / 2 + 0.05), 0), 0.04, 0, 0, 0.008, 6, axis='X') for s in (-1, 1)])
    sp = join('spj', [rotate(spring(f'sp{s}', (0, s * (W / 2 + 0.05), CZ), 0.04, 2 * R + 0.1, 2 * R + 0.35, 0.008, 6, axis='X'), 0, 'Z') for s in (-1, 1)])
    P(m, 'relief_springs', 'Relief Springs (let tramp metal pass)', 'support', sp, explode=(0.4, 0, 0.3), ref='rc_springs', section='keep')
    hp = hopper('hp', 1.1, 0.6, CZ + R + 0.1, CZ + R + 0.6)
    P(m, 'feed_hopper', 'Feed Hopper', 'structure', hp, explode=(0, 0, 0.5), ref='rc_hopper')
    _gearmotor(m, 'drive', -R - G / 2, W / 2 + 0.45, CZ, label='Drive (motor, gears/belts)', ref='rc_drive')
    lg = [box(f'lg{i}', (0.1, W + 0.2, CZ - R - 0.15), (x, 0, (CZ - R - 0.15) / 2), 'paint_blue') for i, x in enumerate((-2 * R - 0.1, 2 * R + 0.1))]
    P(m, 'stand', 'Support Stand', 'structure', lg, explode=(0, 0, -0.3), ref='rc_frame', section='keep')
    rocks_along(m, 'rocks', 'Material Nipped Between the Rolls', [(0.0, CZ + R + 0.5), (0.0, CZ + 0.05), (0.0, CZ - R - 0.4)], 8, r=0.04)
    m.flow('material', [(0, 0, CZ + R + 0.6), (0, 0, CZ), (0, 0, CZ - R - 0.45)], 'flow_discharge', 0.015, 0.25)
    wz = []
    for i, x in enumerate((-R - G / 2, R + G / 2)):
        for j, (y0, y1, mt) in enumerate(((-W / 2, -0.15, 'wear_light'), (-0.15, 0.15, 'wear_severe'), (0.15, W / 2, 'wear_light'))):
            wz.append(cyl(f'wz{i}{j}', R + 0.04, y0, y1, mt, 64, axis='Y', center=(x, 0, CZ), r_in=R + 0.034))
    m.overlay('wear', join('wz', wz), 'Roll wear pattern',
              'Feed tends to concentrate at the centre of the rolls, so the teeth wear fastest there (purple) and the rolls become "hollow" — the gap opens in the middle '
              'and the product coarsens. Spreading the feed across the full width (feeder width, chute design) and rebuilding or re-profiling the teeth keeps the gap even.', split=True)
    return m.export(out)


# ===================================================================== metadata
def _std(*items):
    return [{'id': i, 'title': t, 'relevance': r, 'edition': 'to be verified'} for i, t, r in items]


def _c(fn, cons, mat, op='—', fm=('—',), insp=('Visual',)):
    return C(fn, cons, mat, op, list(fm), list(insp))


_CR = _std(('ISO 21873-1', 'Building construction machinery — Mobile crushers — Terminology and commercial specifications', 'Terminology.'),
           ('ISO 12100', 'Safety of machinery — Risk assessment', 'Guarding and safety.'))
_FD = _std(('CEMA', 'Conveyor Equipment Manufacturers Association standards', 'Feeder/conveyor practice (US).'), ('ISO 12100', 'Safety of machinery', 'Guarding.'))

META = {
    'apron_feeder': {'summary': ('An apron feeder pulls heavy, lumpy ore out from under a hopper at a controlled rate. Overlapping steel pans bolted to crawler-type chains form a moving floor; '
                                 'the drive sprockets at the head pull the chain, and the pans dump the ore over the head. It withstands impact from large lumps and high loads.'),
                     'classification': {'family': 'Feeder', 'type': 'Heavy-duty apron (pan) feeder'}, 'model_configuration': {'animation': 'Pans travel round the sprockets carrying ore'},
                     'standards': _FD, 'references': ['Weir/FLSmidth apron feeder literature (generic)'],
                     'components': {'af_pans': _c('Moving floor that carries the ore.', 'Overlapping manganese/steel pans on chains.', 'Manganese steel.', 'Low speed ~ 0.05–0.3 m/s.', ['Pan wear, cracking'], ['Inspect']),
                                    'af_sprockets': _c('Drive and return the chains.', 'Head (drive) and tail shafts with sprockets.', 'Steel.', '—', ['Tooth wear'], ['Measure']),
                                    'af_frame': _c('Supports the chain on carrying rollers.', 'Fabricated frame, rails, rollers.', 'Steel.'), 'af_hopper': _c('Holds ore; skirts contain the bed.', 'Hopper and skirt boards.', 'Steel, liners.'),
                                    'af_drive': _c('Drives the head shaft slowly with high torque.', 'Motor and planetary/shaft-mounted gearbox, often VFD.', '—')}},
    'vibrating_feeder': {'summary': ('A vibrating feeder moves bulk material by vibrating a tray. Two counter-rotating unbalanced motors create a straight-line vibration at an angle; each stroke throws '
                                     'the particles slightly forward and up, so they hop along the tray at a rate set by amplitude and frequency.'),
                         'classification': {'family': 'Feeder', 'type': 'Electromechanical (twin unbalanced motor) vibrating feeder'}, 'model_configuration': {'animation': 'Tray vibrates; material hops forward'},
                         'standards': _FD, 'references': ['Vibratory feeder manufacturer guides (generic)'],
                         'components': {'vf_tray': _c('Carries and conveys material.', 'Tray with liners.', 'Steel, wear liners.'), 'vf_exciter': _c('Generate the vibration.', 'Two unbalanced motors rotating in opposite directions.', '—', 'Amplitude set by weights.', ['Bearing failure'], ['Temperature']),
                                        'vf_springs': _c('Isolate vibration from the structure.', 'Coil springs.', 'Spring steel.'), 'vf_support': _c('Support.', 'Brackets.', 'Steel.'), 'vf_hopper': _c('Feed hopper.', '—', 'Steel.')}},
    'grizzly_feeder': {'summary': ('A vibrating grizzly feeder combines a feeder pan with a section of tapered grizzly bars. As material vibrates forward, fines fall through the gaps between bars '
                                   'and bypass the crusher; oversize continues to the crusher. This reduces crusher load and wear.'),
                       'classification': {'family': 'Feeder / scalper', 'type': 'Vibrating grizzly feeder'}, 'model_configuration': {'animation': 'Fines fall through the bars; oversize continues'},
                       'standards': _FD, 'references': ['Primary crushing plant design notes'],
                       'components': {'vf_tray': _c('Pan and grizzly bars.', 'Tray and tapered bars.', 'Steel, manganese.'), 'vf_exciter': _c('Vibration drive.', 'Unbalanced motors.', '—'),
                                      'vf_springs': _c('Isolation.', 'Springs.', 'Steel.'), 'vf_support': _c('Support.', 'Brackets.', 'Steel.'), 'vf_hopper': _c('Hopper.', '—', 'Steel.'), 'vf_chute': _c('Carries fines past the crusher.', 'Chute.', 'Steel.')}},
    'rotary_airlock_feeder': {'summary': ('A rotary airlock feeder (rotary valve) meters powder or granules from a hopper into a pneumatic conveying line or out of a cyclone/filter while sealing the '
                                          'pressure difference. A vaned rotor turns in a close-fitting housing; each pocket fills at the top and empties at the bottom.'),
                              'classification': {'family': 'Feeder / airlock', 'type': 'Drop-through rotary valve, 8 pockets'}, 'model_configuration': {'animation': 'Rotor turns; pockets carry powder down'},
                              'standards': _std(('ATEX / NFPA 69', 'Explosion protection (flame-proof rotary valves)', 'Isolation of dust explosions.'),), 'references': ['Mills, Pneumatic Conveying Design Guide'],
                              'components': {'ra_housing': _c('Encloses the rotor with tight clearance (seal).', 'Cast housing.', 'Cast iron/stainless.', 'Air leakage through clearances.', ['Wear → leakage'], ['Clearance check']),
                                             'ra_rotor': _c('Meters and transfers material.', 'Vaned rotor on shaft.', 'Steel/stainless.', '—', ['Vane tip wear'], ['Clearance']), 'ra_drive': _c('Drives the rotor.', 'Gearmotor.', '—'),
                                             'ra_connections': _c('Hopper and conveying line.', '—', '—')}},
    'screw_feeder': {'summary': ('A screw feeder meters bulk solids with a rotating helical flight in a trough. Each turn moves a fixed volume, so feed rate is set by speed. A variable-pitch flight '
                                 'draws material evenly from the whole length of the inlet.'),
                     'classification': {'family': 'Feeder', 'type': 'Screw feeder, U-trough'}, 'model_configuration': {'animation': 'Screw turns; material conveyed to the spout'},
                     'standards': _std(('CEMA 350', 'Screw Conveyors', 'Design.'),), 'references': ['CEMA 350'],
                     'components': {'sf_trough': _c('Contains the material.', 'U-trough.', 'Steel/stainless.'), 'sf_screw': _c('Conveys material.', 'Helical flight on pipe.', 'Steel.', '—', ['Flight wear'], ['Inspect']),
                                    'sf_hopper': _c('Inlet.', 'Hopper.', 'Steel.'), 'sf_supports': _c('Supports.', '—', 'Steel.')}},
    'weigh_feeder': {'summary': ('A belt weigh feeder delivers a set mass flow (kg/h). A load cell under a weigh idler measures belt loading (kg/m) and a speed sensor measures belt speed; the controller '
                                 'multiplies them and adjusts belt speed to hold the set rate.'),
                     'classification': {'family': 'Feeder (gravimetric)', 'type': 'Belt weigh feeder'}, 'model_configuration': {'animation': 'Belt runs; weigh idler deflects slightly'},
                     'standards': _std(('OIML R 50', 'Continuous totalizing automatic weighing instruments (belt weighers)', 'Accuracy classes.'),), 'references': ['OIML R 50'],
                     'components': {'wf_loadcell': _c('Measures belt load.', 'Weigh idler on load cell.', '—', 'Calibrate with test weights/chains.', ['Drift'], ['Zero/span check']),
                                    'wf_speed': _c('Measures belt speed.', 'Pulse sensor.', '—'), 'wf_controller': _c('Computes and controls feed rate.', 'Controller with VFD output.', '—'),
                                    'wf_inlet': _c('Feeds and shapes the bed.', 'Hopper and shear gate.', 'Steel.'), 'wf_drive': _c('Variable-speed drive.', 'Gearmotor with VFD.', '—'),
                                    'hk_belt': _c('Carries the material.', 'Endless belt.', 'Rubber.'), 'hk_pulley': _c('Drive/return pulleys.', 'Pulleys.', 'Steel.'), 'hk_idlers': _c('Frame and idlers.', '—', 'Steel.')}},
    'vibrating_screen': {'summary': ('An inclined vibrating screen sorts material by size. An exciter with unbalanced weights makes the screen box move in a circle; particles jump along the decks, and '
                                     'those smaller than the openings pass through. The top deck retains oversize, the bottom deck middlings, and fines fall through both.'),
                         'classification': {'family': 'Screen', 'type': 'Inclined double-deck circular-motion screen'}, 'model_configuration': {'animation': 'Box vibrates; three size fractions separate'},
                         'standards': _std(('ISO 3310-1/-2', 'Test sieves — wire cloth / perforated plate', 'Aperture definitions.'),), 'references': ['Aggregates handbook — screening'],
                         'components': {'vs_body': _c('Carries the screen decks.', 'Side plates, cross members, decks.', 'Steel, rubber/PU or wire mesh.', '—', ['Cracks', 'Blinding'], ['Inspect welds/decks']),
                                        'vs_exciter': _c('Creates the vibration.', 'Shaft with unbalanced weights.', 'Steel.', 'Bearings highly loaded.', ['Bearing failure'], ['Temperature, oil']),
                                        'vs_springs': _c('Isolate vibration.', 'Coil springs.', 'Steel.'), 'vs_frame': _c('Support.', '—', 'Steel.'), 'vs_chutes': _c('Collect fractions.', 'Chutes.', 'Steel.')}},
    'trommel_screen': {'summary': ('A trommel is a slowly rotating, slightly inclined perforated drum. Material tumbles along inside; small particles fall through the holes and oversize leaves at the '
                                   'far end. It handles sticky or wet material well and is common in compost, MSW, gold washing and mineral sizing.'),
                       'classification': {'family': 'Screen', 'type': 'Rotary drum (trommel) screen on trunnions'}, 'model_configuration': {'animation': 'Drum rotates; fines fall through'},
                       'standards': _std(('ISO 12100', 'Safety of machinery', 'Guarding.'),), 'references': ['Trommel design notes'],
                       'components': {'tr_drum': _c('Screens the material as it tumbles.', 'Perforated drum with tyres and girth gear.', 'Steel.', 'Critical speed limits rpm.', ['Hole blinding'], ['Brush/clean']),
                                      'tr_trunnions': _c('Support and guide the drum.', 'Trunnion rollers.', 'Steel.'), 'tr_drive': _c('Rotates the drum.', 'Gearmotor and pinion.', '—'),
                                      'tr_hood': _c('Contains dust, collects undersize.', 'Hood and hopper.', 'Steel.'), 'tr_feed': _c('Feed chute.', '—', 'Steel.')}},
    'jaw_crusher': {'summary': ('A jaw crusher breaks rock between a fixed jaw and a swinging jaw. The eccentric shaft moves the top of the swing jaw in a small orbit while the toggle plate holds the '
                                'bottom; the jaw squeezes and releases the rock, which breaks and falls lower into the narrowing chamber until it passes the closed-side setting.'),
                    'classification': {'family': 'Crusher (compression)', 'type': 'Single-toggle jaw crusher'}, 'model_configuration': {'animation': 'Eccentric drives the swing jaw; toggle rocks'},
                    'standards': _CR, 'references': ['Wills\' Mineral Processing Technology — crushers'],
                    'components': {'jc_frame': _c('Carries all loads.', 'Fabricated frame.', 'Steel.'), 'jc_fixed_jaw': _c('Stationary crushing surface.', 'Jaw die.', 'Manganese steel.', '—', ['Wear'], ['Reverse/replace dies']),
                                   'jc_swing_jaw': _c('Moving crushing surface.', 'Pitman with jaw die.', 'Steel/manganese.'), 'jc_toggle': _c('Transmits force; breaks to protect the crusher from tramp metal.', 'Toggle plate.', 'Cast iron/steel.'),
                                   'jc_eccentric': _c('Creates the jaw motion and stores energy.', 'Eccentric shaft with flywheels.', 'Forged steel.')}},
    'cone_crusher': {'summary': ('A cone crusher crushes rock between a gyrating mantle and a fixed concave. The eccentric bushing, turned by a bevel gear, makes the head gyrate (wobble) so the gap '
                                 'opens and closes around the circle; rock is squeezed repeatedly as it moves down to the closed-side setting.'),
                     'classification': {'family': 'Crusher (compression)', 'type': 'Cone crusher (secondary/tertiary)'}, 'model_configuration': {'animation': 'Head gyrates; eccentric and pinion turn'},
                     'standards': _CR, 'references': ['Wills\' Mineral Processing Technology'],
                     'components': {'cc_shell': _c('Holds the concave and forms the chamber.', 'Top shell/bowl and main frame.', 'Cast steel.'), 'cc_concave': _c('Fixed crushing surface.', 'Liner.', 'Manganese steel.', '—', ['Wear'], ['Liner profile']),
                                    'cc_mantle': _c('Gyrating crushing surface.', 'Mantle on head and main shaft.', 'Manganese steel.'), 'cc_eccentric': _c('Makes the head gyrate.', 'Eccentric bushing with bevel gear.', 'Bronze/steel.'),
                                    'cc_pinion': _c('Drives the eccentric.', 'Countershaft and pinion.', 'Steel.')}},
    'gyratory_crusher': {'summary': ('A gyratory crusher is a large primary crusher. A long main shaft with a mantle hangs from a spider at the top and gyrates inside a tall concave; trucks dump ore '
                                     'straight in, and it crushes continuously around the circle — higher capacity than a jaw crusher.'),
                         'classification': {'family': 'Crusher (compression)', 'type': 'Primary gyratory crusher'}, 'model_configuration': {'animation': 'Main shaft gyrates'},
                         'standards': _CR, 'references': ['Wills\' Mineral Processing Technology'],
                         'components': {'cc_shell': _c('Shell.', 'Cast shell.', 'Steel.'), 'cc_concave': _c('Concaves.', 'Liners.', 'Manganese.'), 'cc_mantle': _c('Mantle & main shaft.', '—', 'Manganese/steel.'),
                                        'cc_eccentric': _c('Eccentric.', '—', 'Bronze.'), 'cc_pinion': _c('Pinion.', '—', 'Steel.'), 'cc_spider': _c('Top support of the main shaft.', 'Spider arms.', 'Cast steel.')}},
    'impact_crusher': {'summary': ('A horizontal shaft impact crusher breaks rock by impact. Blow bars on a fast rotor hit the falling rock and hurl it against impact aprons; it shatters along natural '
                                   'weaknesses, giving cubical product. The apron gap sets product size.'),
                       'classification': {'family': 'Crusher (impact)', 'type': 'HSI with two aprons'}, 'model_configuration': {'animation': 'Rotor spins; rock thrown to aprons'},
                       'standards': _CR, 'references': ['Aggregate processing handbooks'],
                       'components': {'ic_housing': _c('Encloses the crushing chamber.', 'Lined housing.', 'Steel.'), 'ic_rotor': _c('Strikes the rock.', 'Rotor with blow bars.', 'Steel; blow bars martensitic/ceramic.', 'Tip speed ~ 25–50 m/s.', ['Blow bar wear'], ['Turn/replace bars']),
                                      'ic_aprons': _c('Rock impacts and rebounds.', 'Hinged aprons.', 'Steel with liners.'), 'ic_drive': _c('Drive.', 'Motor and belts.', '—')}},
    'hammer_crusher': {'summary': ('A hammer crusher (hammer mill) uses swinging hammers on a fast rotor to smash material against a breaker plate; it keeps hitting it until it is small enough to pass '
                                   'through the grate bars below. Used for coal, limestone, clinker and softer materials.'),
                       'classification': {'family': 'Crusher (impact)', 'type': 'Swing-hammer mill with grate'}, 'model_configuration': {'animation': 'Rotor spins with hammers'},
                       'standards': _CR, 'references': ['Coal handling plant design notes'],
                       'components': {'ic_housing': _c('Housing.', '—', 'Steel.'), 'ic_rotor': _c('Rotor with pinned hammers.', '—', 'Steel; manganese hammers.', '—', ['Hammer wear'], ['Rotate/replace']),
                                      'ic_aprons': _c('Grate (size control) and breaker plate.', '—', 'Manganese.'), 'ic_drive': _c('Drive.', '—', '—')}},
    'roller_crusher': {'summary': ('A roll crusher nips material between two counter-rotating rolls. Teeth grip and break it as it is drawn down through the gap, which sets the product size. One roll is '
                                   'spring-loaded so uncrushable tramp material can pass without damage.'),
                       'classification': {'family': 'Crusher (compression)', 'type': 'Double toothed roll crusher'}, 'model_configuration': {'animation': 'Rolls counter-rotate'},
                       'standards': _CR, 'references': ['Coal and mineral crushing notes'],
                       'components': {'rc_roll': _c('Crush material in the nip.', 'Toothed rolls on shafts.', 'Manganese/alloy steel.', '—', ['Tooth wear'], ['Hard-face']),
                                      'rc_frame': _c('Frame & bearings.', '—', 'Steel.'), 'rc_springs': _c('Allow the roll to retreat for tramp metal.', 'Springs.', 'Steel.'),
                                      'rc_hopper': _c('Feed hopper.', '—', 'Steel.'), 'rc_drive': _c('Drive.', '—', '—')}},
}

BUILDERS = {k: globals()[k] for k in META}
