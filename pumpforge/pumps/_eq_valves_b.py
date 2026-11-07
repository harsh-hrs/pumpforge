"""Valves & Piping — EQ-126 … EQ-131 (pressure sustaining valve, steam trap, flame arrestor, rupture disc, sight glass, flow indicator)."""
import math
from mathutils import Vector, Matrix
from pumpforge.core import Model, lathe, cyl, box, csg, split, join, split_many, rotate, transform, hex_prism, TAU, OPERATE_FRAMES
from pumpforge.valvekit import (P, bore_pipe, flange, bolts_x, gasket, handwheel, spring, sphere, keys_loop, smooth_pulse, shape_key,
                                morph_loop, tap)
from pumpforge.parts import pressure_gauge, add_tracers, hollow_pipe
from pumpforge.shapes import sweep_tube
from pumpforge.common_meta import C
from pumps._eq_valves_a import _std

CAT = '6 · Valves & Piping'


def _flanged_line(m, CZ, R, x0, x1, xl=0.8, mat='paint_grey', pid='pipework', name='Adjoining Pipework (flanged)'):
    rf = R * 2.0 + 0.04
    objs = [hollow_pipe('pl', [(-xl, 0, CZ), (x0 - 0.02, 0, CZ)], R, mat, 48, t=0.006), hollow_pipe('pr', [(x1 + 0.02, 0, CZ), (xl, 0, CZ)], R, mat, 48, t=0.006),
            cyl('fl1', rf, x0 - 0.022, x0 - 0.002, mat, 64, axis='X', center=(0, 0, CZ), r_in=R), cyl('fl2', rf, x1 + 0.002, x1 + 0.022, mat, 64, axis='X', center=(0, 0, CZ), r_in=R),
            bolts_x('b1', x0 - 0.002, rf, CZ, 8, 0.05), bolts_x('b2', x1 + 0.002, rf, CZ, 8, 0.05)]
    return P(m, pid, name, 'system_piping', objs, explode=(0, 0.35, 0), ref='pipework')


# =============================================================== EQ-126 Pressure sustaining valve
def pressure_sustaining_valve(out):
    m = Model('pressure_sustaining_valve', 'Pressure Sustaining Valve (Pilot-Operated Diaphragm, Globe Pattern)', CAT, META['pressure_sustaining_valve'])
    CZ, R = 0.3, 0.05
    body = csg('ps_body', [sphere('bs', (0, 0, CZ), 0.11, 'paint_blue', 64), cyl('bx', 0.075, -0.18, 0.18, 'paint_blue', 64, axis='X', center=(0, 0, CZ)),
                           cyl('f1', 0.12, -0.2, -0.18, 'paint_blue', 64, axis='X', center=(0, 0, CZ), ch=0.003), cyl('f2', 0.12, 0.18, 0.2, 'paint_blue', 64, axis='X', center=(0, 0, CZ), ch=0.003),
                           cyl('bf', 0.14, CZ + 0.09, CZ + 0.11, 'paint_blue', 64)],
               [cyl('ii', R, -0.21, -0.03, 'paint_blue', 48, axis='X', center=(0, 0, CZ - 0.01)), cyl('oi', R, 0.03, 0.21, 'paint_blue', 48, axis='X', center=(0, 0, CZ + 0.01)),
                box('wl', (0.012, 0.25, 0.09), (0, 0, CZ - 0.03), 'paint_blue') if False else cyl('in_ch', 0.085, CZ - 0.09, CZ - 0.0, 'paint_blue', 64),
                cyl('up_ch', 0.085, CZ + 0.02, CZ + 0.12, 'paint_blue', 64)], 'paint_blue')
    part_wall = cyl('deck', 0.086, CZ - 0.0, CZ + 0.02, 'paint_blue', 64, r_in=0.045)
    seat = cyl('seat', 0.05, CZ + 0.018, CZ + 0.026, 'bronze', 64, r_in=0.042)
    P(m, 'body', 'Globe Body with Seat Deck', 'body', [body, part_wall, seat], explode=(0, 0, -0.35), ref='psv_body')
    lift = lambda t: 0.012 + 0.018 * (0.5 + 0.5 * math.sin(TAU * t))         # modulating opening
    disc = join('disc', [cyl('d', 0.052, CZ + 0.026, CZ + 0.04, 'bronze', 64, ch=0.003), cyl('ds', 0.009, CZ + 0.04, CZ + 0.2, 'stainless', 24),
                         cyl('dd', 0.12, CZ + 0.118, CZ + 0.124, 'rubber', 64), cyl('dw', 0.07, CZ + 0.124, CZ + 0.134, 'steel', 64)])
    pd = P(m, 'disc_diaphragm', 'Disc, Stem & Main Diaphragm (moves as one)', 'disc', disc, explode=(0, -0.4, 0.15), ref='psv_disc')
    keys_loop(m, pd, lambda t: (0, 0, lift(t)))
    cov = csg('cov', [cyl('c', 0.14, CZ + 0.124, CZ + 0.2, 'paint_blue', 64, ch=0.004), cyl('ind', 0.02, CZ + 0.2, CZ + 0.26, 'glass', 24)],
              [cyl('ci', 0.12, CZ + 0.118, CZ + 0.185, 'paint_blue', 64), cyl('cs', 0.0095, CZ + 0.18, CZ + 0.25, 'paint_blue', 24)], 'paint_blue')
    sp = spring('sp', (0, 0, 0), 0.03, CZ + 0.134, CZ + 0.185, 0.004, 4)
    P(m, 'cover_spring', 'Cover (Control Chamber) & Spring; Position Indicator', 'bonnet', [cov, sp], explode=(0, 0, 0.35), ref='psv_cover')
    pil = [box('pb', (0.06, 0.04, 0.05), (0.0, -0.2, CZ + 0.26), 'brass', bevel=0.004), cyl('psp', 0.016, CZ + 0.285, CZ + 0.37, 'brass', 24, center=(0.0, -0.2, 0)),
           hex_prism('pad', 0.024, CZ + 0.37, CZ + 0.39, 'steel', center=(0.0, -0.2, 0)),
           sweep_tube('t1', [(-0.14, -0.06, CZ + 0.05), (-0.14, -0.2, CZ + 0.05), (-0.14, -0.2, CZ + 0.26), (-0.03, -0.2, CZ + 0.26)], 0.005, 'copper', 8),
           sweep_tube('t2', [(0.03, -0.2, CZ + 0.26), (0.06, -0.2, CZ + 0.26), (0.06, -0.12, CZ + 0.17), (0.04, -0.06, CZ + 0.17)], 0.005, 'copper', 8),
           sweep_tube('t3', [(0.0, -0.22, CZ + 0.235), (0.0, -0.22, CZ + 0.12), (0.14, -0.06, CZ + 0.05)], 0.005, 'copper', 8)]
    pg = [pressure_gauge('g1', (-0.12, 0.0, CZ + 0.075)), pressure_gauge('g2', (0.12, 0.0, CZ + 0.075))]
    P(m, 'pilot_system', 'Pilot Valve (adjustable set point), Control Tubing & Gauges', 'controls', pil + pg, explode=(0, -0.35, 0.3), ref='psv_pilot', section='keep')
    _flanged_line(m, CZ, R, -0.2, 0.2)
    m.flow('flow', [(-0.8, 0, CZ - 0.01), (-0.05, 0, CZ - 0.01), (-0.02, 0, CZ - 0.05), (0.0, 0, CZ + 0.0), (0.0, 0.0, CZ + 0.06), (0.05, 0, CZ + 0.06), (0.06, 0, CZ + 0.01),
                    (0.8, 0, CZ + 0.01)], 'flow_suction', 0.008, 0.15, speed=[1, 1, 1.4, 2, 2, 1.5, 1, 1])
    return m.export(out)


# =============================================================== EQ-127 Steam trap (inverted bucket)
def steam_trap(out):
    m = Model('steam_trap', 'Steam Trap (Inverted Bucket)', CAT, META['steam_trap'])
    Z0 = 0.1
    body = csg('st_body', [cyl('b', 0.085, Z0, Z0 + 0.26, 'cast_iron', 64, ch=0.005), cyl('cap', 0.095, Z0 + 0.26, Z0 + 0.29, 'cast_iron', 64, ch=0.004),
                           cyl('ib', 0.03, -0.15, -0.06, 'cast_iron', 32, axis='X', center=(0, 0, Z0 + 0.035)), cyl('ob', 0.03, 0.06, 0.15, 'cast_iron', 32, axis='X', center=(0, 0, Z0 + 0.26))],
               [cyl('bi', 0.075, Z0 + 0.012, Z0 + 0.28, 'cast_iron', 64), cyl('ii', 0.015, -0.16, 0.0, 'cast_iron', 24, axis='X', center=(0, 0, Z0 + 0.035)),
                cyl('oi', 0.012, 0.0, 0.16, 'cast_iron', 24, axis='X', center=(0, 0, Z0 + 0.265))], 'cast_iron')
    riser = cyl('riser', 0.012, Z0 + 0.03, Z0 + 0.19, 'stainless', 24, r_in=0.009)
    elb = sweep_tube('rel', [(-0.07, 0, Z0 + 0.035), (0.0, 0, Z0 + 0.035), (0.0, 0, Z0 + 0.05)], 0.011, 'stainless', 16)
    seat = join('seat', [cyl('vs', 0.012, Z0 + 0.25, Z0 + 0.268, 'stainless', 24, r_in=0.0035), box('lp', (0.03, 0.02, 0.01), (0.0, 0, Z0 + 0.245), 'stainless')])
    P(m, 'body', 'Trap Body, Cap, Inlet Riser & Valve Seat', 'body', [body, riser, elb, seat], explode=(0, 0, -0.3), ref='stt_body')
    up = lambda t: smooth_pulse(t, 0.12, 0.33, 0.12)          # 1 = bucket floating (steam) → valve closed
    bk = csg('bucket', [cyl('bo', 0.06, Z0 + 0.04, Z0 + 0.2, 'stainless', 64)], [cyl('bi', 0.057, Z0 + 0.035, Z0 + 0.197, 'stainless', 64),
                                                                                   cyl('vent', 0.003, Z0 + 0.195, Z0 + 0.205, 'stainless', 12, center=(0.03, 0, 0))], 'stainless')
    pb = P(m, 'bucket', 'Inverted Bucket (with vent hole)', 'float', bk, explode=(0, -0.3, 0), ref='stt_bucket')
    keys_loop(m, pb, lambda t: (0, 0, 0.03 * up(t)))
    lev = join('lev', [sweep_tube('lv', [(0.0, 0, Z0 + 0.2), (0.0, 0, Z0 + 0.235)], 0.003, 'stainless', 8), lathe('ball', [(0, Z0 + 0.235), (0.0045, Z0 + 0.238), (0.006, Z0 + 0.244), (0.0, Z0 + 0.249)], 'chrome', 16)])
    pl = P(m, 'valve_lever', 'Lever & Valve Head', 'disc', lev, explode=(0, -0.3, 0.25), ref='stt_lever', section='keep')
    keys_loop(m, pl, lambda t: (0, 0, 0.012 * up(t)))
    cond = lambda t: 0.06 + 0.12 * (1 - up(t))
    wat = cyl('cw', 0.074, Z0 + 0.013, Z0 + 0.03, 'water', 64)
    pw = P(m, 'condensate', 'Condensate (water seal) — animated', 'flow_tracers', wat, ref='stt_condensate', section='split')
    for mesh in pw.meshes:
        shape_key(mesh, 'fill', lambda co: Vector((co.x, co.y, co.z if co.z < Z0 + 0.02 else co.z + 0.18)))
    morph_loop(m, pw, 'fill', lambda t: 0.4 + 0.5 * (1 - up(t)))
    pipes = [hollow_pipe('pi', [(-0.45, 0, Z0 + 0.035), (-0.15, 0, Z0 + 0.035)], 0.015, 'steel', 24, t=0.004), hollow_pipe('po', [(0.15, 0, Z0 + 0.265), (0.45, 0, Z0 + 0.265)], 0.012, 'steel', 24, t=0.004)]
    P(m, 'pipework', 'Inlet from Steam Main Drip Leg / Outlet to Condensate Return', 'system_piping', pipes, explode=(0, 0.3, 0), ref='pipework')
    m.flow('condensate', [(-0.45, 0, Z0 + 0.035), (0.0, 0, Z0 + 0.035), (0.0, 0, Z0 + 0.18), (0.04, 0, Z0 + 0.12), (0.065, 0, Z0 + 0.2), (0.0, 0, Z0 + 0.255), (0.45, 0, Z0 + 0.265)],
           'water', 0.004, 0.08, active=[(0.62, 1.0)])
    m.flow('steam', [(-0.45, 0.01, Z0 + 0.035), (0.0, 0.01, Z0 + 0.035), (0.0, 0.01, Z0 + 0.19)], 'steam', 0.004, 0.08, active=[(0.05, 0.55)])
    return m.export(out)


# =============================================================== EQ-128 Flame arrestor
def flame_arrestor(out):
    m = Model('flame_arrestor', 'Flame Arrestor (In-Line Deflagration, Crimped-Ribbon Element)', CAT, META['flame_arrestor'])
    CZ, R = 0.3, 0.05
    hs = csg('fa_body', [lathe('h', [(R + 0.008, -0.3), (R + 0.008, -0.22), (0.15, -0.1), (0.15, 0.1), (R + 0.008, 0.22), (R + 0.008, 0.3), (0.0, 0.3), (0.0, -0.3)], 'paint_red', 96,
                               axis='X', center=(0, 0, CZ)),
                         cyl('cf1', 0.19, -0.1, -0.075, 'paint_red', 96, axis='X', center=(0, 0, CZ), ch=0.003), cyl('cf2', 0.19, 0.075, 0.1, 'paint_red', 96, axis='X', center=(0, 0, CZ), ch=0.003)],
             [lathe('hi', [(0.0, -0.31), (R, -0.31), (R, -0.22), (0.142, -0.1), (0.142, 0.1), (R, 0.22), (R, 0.31), (0.0, 0.31)], 'paint_red', 96, axis='X', center=(0, 0, CZ))], 'paint_red')
    P(m, 'housing', 'Housing (two halves bolted around the element)', 'body', [hs, bolts_x('hb', 0.0, 0.19, CZ, 12, 0.2)], explode=(0, 0, -0.35), ref='fa_housing')
    el = [cyl('ring', 0.142, -0.06, 0.06, 'stainless', 96, axis='X', center=(0, 0, CZ), r_in=0.134)]
    for i, r in enumerate([0.02 + 0.0095 * k for k in range(12)]):
        el.append(cyl(f'w{i}', r + 0.0015, -0.06, 0.06, 'stainless', 64, axis='X', center=(0, 0, CZ), r_in=r))
    for k in range(16):
        b = box(f'cr{k}', (0.12, 0.002, 0.115), (0, 0, CZ + 0.075), 'stainless')
        el.append(rotate(b, TAU * k / 16, 'X', (0, 0, CZ)))
    el.append(cyl('hub', 0.02, -0.065, 0.065, 'stainless', 24, axis='X', center=(0, 0, CZ)))
    P(m, 'element', 'Flame Arrestor Element (crimped metal ribbon, narrow gaps quench the flame)', 'element', el, explode=(0, -0.45, 0), ref='fa_element')
    _flanged_line(m, CZ, R, -0.3, 0.3, 1.0)
    m.flow('gas', [(-1.0, 0, CZ), (-0.12, 0, CZ), (-0.07, 0, CZ + 0.06), (0.07, 0, CZ + 0.06), (0.12, 0, CZ), (1.0, 0, CZ)], 'air', 0.01, 0.2, speed=[1, 1, 0.4, 0.4, 1, 1])
    add_tracers(m, 'flame_front', 'Flame Front (stopped at the element)', [(0.9, 0.0, CZ), (0.07, 0.0, CZ + 0.02)], n=6, radius=0.02, mat='flame')
    m.overlay('quench', join('q', [cyl('qz', 0.14, 0.06, 0.07, 'heat', 64, axis='X', center=(0, 0, CZ))]), 'Quenching zone',
              'The element splits the flow into many narrow channels. A flame entering them loses heat to the metal walls faster than it can '
              'release it; it cools below its ignition temperature and is extinguished. The gap size is chosen for the gas group (MESG).', split=True)
    m.annotate('quench', 'Flame quenched in narrow channels (gap < MESG)', (0.1, 0.0, CZ + 0.2))
    return m.export(out)


# =============================================================== EQ-129 Rupture disc
def rupture_disc(out):
    m = Model('rupture_disc', 'Rupture Disc (Forward-Acting, Scored) in Holder', CAT, META['rupture_disc'])
    CZ, R = 0.3, 0.06
    hold = [cyl('hi', 0.12, -0.04, 0.0, 'stainless', 96, axis='X', center=(0, 0, CZ), r_in=R, ch=0.003),
            cyl('ho', 0.12, 0.004, 0.044, 'stainless', 96, axis='X', center=(0, 0, CZ), r_in=R, ch=0.003),
            box('tag', (0.03, 0.004, 0.06), (0.002, 0, CZ + 0.15), 'nameplate')]
    P(m, 'holder', 'Disc Holder (inlet & outlet rings) with Tag', 'body', hold, explode=(0, 0, -0.3), ref='rd_holder')
    pet = []
    for k in range(4):
        pet.append(lathe(f'pt{k}', [(0.0, 0.0), (R + 0.012, 0.0), (R + 0.012, 0.0015), (0.0, 0.0015)], 'chrome', 24, a0=TAU * k / 4 + 0.02, a1=TAU * (k + 1) / 4 - 0.02,
                         axis='X', center=(0, 0, CZ), cap_mat='chrome'))
    p = m.part('disc', 'Rupture Disc (domed, cross-scored → 4 petals)', 'disc', section='keep', explode=(0, -0.35, 0), info={'ref': 'rd_disc'})
    meshes = [p.add(o, 'keep', smooth_angle=50) for o in pet]

    def dome(co):
        r = math.hypot(co.y, co.z - CZ)
        f = max(0.0, 1 - (r / R) ** 2) if r < R else 0.0
        return Vector((co.x + 0.025 * f, co.y, co.z))

    def burst(mesh):
        vs = [v.co for v in mesh.data.vertices if math.hypot(v.co.y, v.co.z - CZ) > 0.9 * R]
        mid = math.atan2(sum(v.z - CZ for v in vs), sum(v.y for v in vs))
        hinge = Vector((0.0, R * math.cos(mid), CZ + R * math.sin(mid)))
        axis = Vector((0, -math.sin(mid), math.cos(mid)))
        rot = Matrix.Rotation(math.radians(80), 3, axis)

        def f(co):
            d = dome(co) - hinge
            r = math.hypot(co.y, co.z - CZ)
            if r > R:
                return co
            return hinge + rot @ d
        return f
    for k, mesh in enumerate(meshes):
        shape_key(mesh, 'bulge', dome)
        shape_key(mesh, 'burst', burst(mesh))
    bul = lambda t: min(1.0, t / 0.4) if t < 0.45 else 0.0
    bst = lambda t: 0.0 if t < 0.45 else (min(1.0, (t - 0.45) / 0.05) if t < 0.95 else 0.0)
    for mesh in meshes:
        m.morph(mesh, 'bulge', 'Operate', [(1 + OPERATE_FRAMES * k / 60, bul(k / 60)) for k in range(61)])
        m.morph(mesh, 'burst', 'Operate', [(1 + OPERATE_FRAMES * k / 60, bst(k / 60)) for k in range(61)])
    _flanged_line(m, CZ, R, -0.04, 0.044, 0.7)
    gauge = [pressure_gauge('g', (-0.25, 0.0, CZ + R + 0.006))]
    P(m, 'gauge', 'Upstream Pressure Gauge', 'instrumentation', gauge, explode=(0, 0, 0.3), ref='pressure_gauge', section='keep')
    m.flow('relief', [(-0.7, 0, CZ), (0.7, 0, CZ)], 'flow_discharge', 0.012, 0.2, active=[(0.47, 0.95)])
    m.overlay('pressure', join('pr', [cyl('p1', R + 0.002, -0.7, -0.01, 'pressure_8', 48, axis='X', center=(0, 0, CZ), r_in=R - 0.002),
                                      cyl('p2', R + 0.002, 0.05, 0.7, 'pressure_1', 48, axis='X', center=(0, 0, CZ), r_in=R - 0.002)]), 'Pressure across the disc',
              'Upstream (red) the system pressure rises; downstream (blue) is the relief line at near-atmospheric pressure. At the burst pressure '
              '(within the stated tolerance at the coincident temperature) the scored dome tears along the score lines and the petals open fully.', split=True)
    m.annotate('pressure', 'Burst at set pressure → full-bore opening, non-reclosing', (0.0, 0.0, CZ + 0.2))
    return m.export(out)


# =============================================================== EQ-130 Sight glass
def sight_glass(out):
    m = Model('sight_glass', 'Sight Glass (Double-Window, Flow-Through)', CAT, META['sight_glass'])
    CZ, R = 0.3, 0.04
    body = csg('sg_body', [cyl('bx', 0.07, -0.12, 0.12, 'stainless', 64, axis='X', center=(0, 0, CZ)), cyl('by', 0.075, -0.075, 0.075, 'stainless', 64, axis='Y', center=(0, 0, CZ)),
                           cyl('f1', 0.105, -0.14, -0.12, 'stainless', 64, axis='X', center=(0, 0, CZ), ch=0.003), cyl('f2', 0.105, 0.12, 0.14, 'stainless', 64, axis='X', center=(0, 0, CZ), ch=0.003)],
               [cyl('ix', R, -0.15, 0.15, 'stainless', 48, axis='X', center=(0, 0, CZ)), cyl('ch', 0.055, -0.07, 0.07, 'stainless', 64, axis='Y', center=(0, 0, CZ)),
                cyl('w1', 0.062, -0.08, -0.06, 'stainless', 64, axis='Y', center=(0, 0, CZ)), cyl('w2', 0.062, 0.06, 0.08, 'stainless', 64, axis='Y', center=(0, 0, CZ))], 'stainless')
    P(m, 'body', 'Body (flow-through chamber)', 'body', body, explode=(0, 0, -0.3), ref='sg_body')
    gl = [cyl('g1', 0.062, -0.075, -0.06, 'glass', 64, axis='Y', center=(0, 0, CZ)), cyl('g2', 0.062, 0.06, 0.075, 'glass', 64, axis='Y', center=(0, 0, CZ)),
          cyl('gk1', 0.064, -0.077, -0.075, 'ptfe', 64, axis='Y', center=(0, 0, CZ), r_in=0.05), cyl('gk2', 0.064, 0.075, 0.077, 'ptfe', 64, axis='Y', center=(0, 0, CZ), r_in=0.05)]
    p = m.part('windows', 'Glass Windows & Gaskets', 'window', section='keep', explode=(0, 0, 0.3), info={'ref': 'sg_glass'})
    from pumpforge.core import split_many as sm
    gb, gf = sm('gl', gl, 'y', 0.0)
    p.add_split(gb, gf, smooth_angle=50)
    rings = [cyl('r1', 0.085, -0.095, -0.077, 'stainless', 64, axis='Y', center=(0, 0, CZ), r_in=0.05), cyl('r2', 0.085, 0.077, 0.095, 'stainless', 64, axis='Y', center=(0, 0, CZ), r_in=0.05)]
    for sy in (-1, 1):
        for k in range(8):
            a = TAU * (k + 0.5) / 8
            rings.append(cyl(f'bt{sy}{k}', 0.007, sy * 0.06 if sy > 0 else -0.1, 0.1 if sy > 0 else -0.06, 'steel_dark', 6, axis='Y', center=(0.072 * math.cos(a), 0, CZ + 0.072 * math.sin(a))))
    rb, rf = sm('rings', rings, 'y', 0.0)
    p = m.part('cover_rings', 'Window Cover Rings & Studs', 'window', section='split', explode=(0, 0, 0.45), info={'ref': 'sg_rings'})
    p.add_split(rb, rf, smooth_angle=40)
    _flanged_line(m, CZ, R, -0.14, 0.14, 0.6)
    add_tracers(m, 'bubbles', 'Liquid with Entrained Bubbles (Tracers)', [(-0.6, 0.0, CZ + 0.01), (0.6, 0.0, CZ - 0.01)], n=14, radius=0.007, mat='water')
    m.flow('flow', [(-0.6, 0, CZ), (0.6, 0, CZ)], 'water', 0.01, 0.2)
    return m.export(out)


# =============================================================== EQ-131 Flow indicator (rotor)
def flow_indicator(out):
    m = Model('flow_indicator', 'Flow Indicator (Rotor / Paddle-Wheel Type)', CAT, META['flow_indicator'])
    CZ, R = 0.3, 0.035
    body = csg('fi_body', [cyl('bx', 0.06, -0.12, 0.12, 'brass', 64, axis='X', center=(0, 0, CZ)), cyl('by', 0.07, -0.07, 0.07, 'brass', 64, axis='Y', center=(0, 0, CZ)),
                           cyl('f1', 0.095, -0.14, -0.12, 'brass', 64, axis='X', center=(0, 0, CZ), ch=0.003), cyl('f2', 0.095, 0.12, 0.14, 'brass', 64, axis='X', center=(0, 0, CZ), ch=0.003)],
               [cyl('ix', R, -0.15, 0.15, 'brass', 48, axis='X', center=(0, 0, CZ)), cyl('ch', 0.052, -0.065, 0.065, 'brass', 64, axis='Y', center=(0, 0, CZ)),
                cyl('w1', 0.055, -0.08, -0.055, 'brass', 64, axis='Y', center=(0, 0, CZ)), cyl('w2', 0.055, 0.055, 0.08, 'brass', 64, axis='Y', center=(0, 0, CZ))], 'brass')
    P(m, 'body', 'Body with Rotor Chamber', 'body', body, explode=(0, 0, -0.3), ref='fi_body')
    from pumpforge.core import split_many as sm
    gl = [cyl('g1', 0.055, -0.07, -0.056, 'glass', 64, axis='Y', center=(0, 0, CZ)), cyl('g2', 0.055, 0.056, 0.07, 'glass', 64, axis='Y', center=(0, 0, CZ))]
    p = m.part('windows', 'Sight Windows', 'window', section='split', explode=(0, 0, 0.3), info={'ref': 'sg_glass'})
    p.add_split(*sm('gl', gl, 'y', 0.0), smooth_angle=50)
    rot = [cyl('hub', 0.01, -0.03, 0.03, 'paint_red', 24, axis='Y', center=(0, 0, CZ)), cyl('sh', 0.003, -0.055, 0.055, 'stainless', 12, axis='Y', center=(0, 0, CZ))]
    for k in range(6):
        b = box(f'pd{k}', (0.008, 0.05, 0.04), (0, 0, CZ + 0.028), 'paint_red', bevel=0.002)
        rot.append(rotate(b, TAU * k / 6, 'Y', (0, 0, CZ)))
    pr = P(m, 'rotor', 'Rotor (paddle wheel) — spins with flow', 'rotating_element', rot, explode=(0, -0.35, 0.2), ref='fi_rotor', section='keep', pivot=(0, 0, CZ))
    pr.spin('Y', 3)
    _flanged_line(m, CZ, R, -0.14, 0.14, 0.6)
    m.flow('flow', [(-0.6, 0, CZ - 0.025), (-0.05, 0, CZ - 0.025), (0.0, 0, CZ - 0.04), (0.05, 0, CZ - 0.025), (0.6, 0, CZ - 0.025)], 'water', 0.008, 0.2)
    return m.export(out)


META = {
    'pressure_sustaining_valve': {
        'summary': ('A pressure sustaining (back-pressure) valve keeps the pressure UPSTREAM of it from falling below a set value. A small adjustable pilot '
                    'senses inlet pressure: when inlet pressure rises above the set point the pilot vents the control chamber and the main valve opens '
                    'further; when it falls, the pilot lets inlet pressure into the chamber and the main valve throttles. It protects high zones of water '
                    'networks, prevents pump run-out and maintains back-pressure on processes.'),
        'classification': {'family': 'Pilot-operated automatic control valve', 'type': 'Hydraulically operated diaphragm globe valve with sustaining pilot'},
        'model_configuration': {'animation': 'Main disc modulates continuously to hold inlet pressure', 'related': 'Pressure reducing valve (controls downstream), relief valve (fast opening)'},
        'standards': _std(('EN 1074-5', 'Valves for water supply — control valves', 'Water network control valves.'), ('AWWA C530', 'Pilot-operated control valves', 'US water service.')),
        'references': ['Cla-Val / Bermad / Singer control valve manuals (generic principle)'],
        'components': {
            'psv_body': C('Globe-pattern body with seat deck separating inlet and outlet.', 'Cast body, bolted cover.', 'Ductile iron, cast steel, bronze, stainless.', 'Flow under the seat.',
                          ['Cavitation damage at high ΔP'], ['Inspect seat, check for noise']),
            'psv_disc': C('Throttles flow; positioned by the pressure in the control chamber.', 'Disc and diaphragm assembly on a guided stem.', 'Bronze/stainless disc, reinforced elastomer diaphragm.',
                          'Modulates continuously.', ['Diaphragm tear', 'Seat wear'], ['Diaphragm leak test']),
            'psv_cover': C('Forms the control chamber above the diaphragm.', 'Cover with spring and position indicator.', 'As body.', '—', ['Indicator glass damage'], ['Visual']),
            'psv_pilot': C('Senses inlet pressure and sets the control-chamber pressure.', 'Adjustable spring-loaded pilot, needle/fixed restrictions, strainer and tubing.', 'Bronze/stainless.',
                           'Set point adjusted with the screw; dirty pilots cause hunting.', ['Blocked restriction/strainer', 'Hunting'], ['Clean pilot system', 'Verify set point with gauges']),
        },
    },
    'steam_trap': {
        'summary': ('A steam trap automatically drains condensate (and air) from steam lines and equipment while holding back live steam. In the inverted '
                    'bucket trap, steam entering under the bucket makes it float and close the valve; when condensate fills the bucket and the steam '
                    'escapes through the small vent hole, the bucket sinks, opens the valve and condensate is pushed out — an intermittent cycle.'),
        'classification': {'family': 'Steam system automatic valve', 'type': 'Mechanical trap — inverted bucket'},
        'model_configuration': {'animation': 'Steam in → bucket floats → valve shut; condensate in → bucket sinks → discharge', 'other_types': 'Float & thermostatic, thermodynamic disc, thermostatic (bimetal/balanced pressure)'},
        'standards': _std(('ISO 6552 / EN 26552', 'Automatic steam traps — definitions', 'Classification.'), ('ISO 7841', 'Steam loss determination', 'Testing.')),
        'references': ['Spirax Sarco — Steam and Condensate Loop (generic)', 'US DOE — Steam System Sourcebook'],
        'components': {
            'stt_body': C('Pressure housing with inlet riser and discharge valve seat at the top.', 'Cast body and cap.', 'Cast iron, cast steel, stainless.', 'Install below the drain point, upright.',
                          ['Body erosion', 'Freezing damage'], ['Ultrasonic / temperature test']),
            'stt_bucket': C('Floats on trapped steam and sinks when filled with condensate.', 'Inverted cup with small vent hole at the top.', 'Stainless steel.', 'Needs a water seal (prime) to work.',
                            ['Loss of prime → blows steam'], ['Ensure water seal']),
            'stt_lever': C('Links bucket motion to the valve head on the orifice.', 'Lever and hardened valve ball.', 'Stainless/chrome steel.', 'Orifice size set by ΔP.', ['Valve wear → steam leak'], ['Test with ultrasound']),
            'stt_condensate': C('Condensate collected in the trap (water seal).', '—', '—', 'Level rises until the bucket sinks.', ['—'], ['—']),
        },
    },
    'flame_arrestor': {
        'summary': ('A flame arrestor lets gas or vapour flow through but stops a flame from passing. Its element divides the flow into many very narrow '
                    'channels; a flame entering them loses heat to the metal so fast that it is cooled below ignition and extinguished. In-line '
                    'deflagration arrestors protect tanks, vent headers and burners against flashback.'),
        'classification': {'family': 'Explosion protection device', 'type': 'In-line deflagration flame arrestor, crimped-ribbon element'},
        'model_configuration': {'element': 'Crimped stainless ribbon wound into a disc; gap chosen for the gas group (MESG)', 'animation': 'Gas flows through; flame front stops at the element'},
        'standards': _std(('ISO 16852', 'Flame arresters — Performance requirements, test methods and limits for use', 'Testing and gas groups.'),
                          ('API 2000', 'Venting of storage tanks', 'Application with vents.')),
        'references': ['Protego / Elmac technical handbooks (generic)'],
        'components': {
            'fa_housing': C('Expands the pipe to the element diameter so flow velocity in the element stays low.', 'Two flanged halves clamping the element.', 'Carbon steel, stainless.', 'Pressure drop rises as element fouls.',
                            ['Corrosion'], ['ΔP monitoring']),
            'fa_element': C('Quenches the flame in narrow channels.', 'Crimped and flat metal ribbons wound together forming triangular channels.', 'Stainless steel.',
                            'Must match gas group, temperature and installation distance from ignition source.', ['Fouling/blocking', 'Damage after flame events'], ['Inspect & clean; replace after a stabilised burn']),
        },
    },
    'rupture_disc': {
        'summary': ('A rupture (bursting) disc is a non-reclosing pressure-relief device: a thin metal membrane designed to burst at a specified pressure and '
                    'temperature, opening a full relief path in milliseconds. It is used alone where fast, leak-tight relief is needed, or upstream of a '
                    'safety valve to isolate it from corrosive process fluid.'),
        'classification': {'family': 'Pressure protection device (non-reclosing)', 'type': 'Forward-acting, scored domed disc in holder'},
        'model_configuration': {'animation': 'Pressure rises → dome strains → bursts along score lines → petals open', 'reverse_acting': 'Reverse-acting discs buckle and open by knife or score lines; allow higher operating ratios'},
        'standards': _std(('ISO 4126-2 / -6', 'Safety devices for protection against excessive pressure — bursting disc safety devices', 'Design, application, installation.'),
                          ('ASME BPVC VIII Div.1 UG-127', 'Rupture disk devices', 'Certification and marking.'), ('API 520 Pt I', 'Sizing of pressure-relieving devices', 'Sizing.')),
        'references': ['Fike / BS&B / Oseco rupture disc technical guides (generic)'],
        'components': {
            'rd_holder': C('Clamps and centres the disc between the pipe flanges.', 'Inlet and outlet holder rings; tag shows burst pressure, temperature, lot.', 'Stainless, carbon steel.',
                           'Install in the correct flow direction.', ['Mis-installation (upside down)'], ['Check tag and orientation']),
            'rd_disc': C('Bursts at the rated pressure to open a full relief path.', 'Domed metal membrane with score lines forming petals.', 'Stainless, nickel alloys, tantalum, graphite (special).',
                         'Operating ratio (operating/burst pressure) limits life; cycling and temperature matter.', ['Premature burst (fatigue, corrosion)', 'Fragmentation (wrong type)'],
                         ['Replace on schedule; never reuse']),
        },
    },
    'sight_glass': {
        'summary': ('A sight glass lets operators see the liquid inside a pipe: its colour, clarity, flow, bubbles or the presence of liquid at all. '
                    'The double-window, flow-through type is lit from one side and viewed from the other.'),
        'classification': {'family': 'Piping accessory', 'type': 'Flow-through double-window sight glass'},
        'model_configuration': {'glass': 'Borosilicate, tempered (or fused glass-to-metal)'},
        'standards': _std(('DIN 7080 / DIN 8902', 'Sight glass discs', 'Glass dimensions and ratings.'), ('ASME B16.34', 'Valves and fittings ratings', 'Body pressure rating.')),
        'references': ['Sight glass manufacturer catalogues (generic)'],
        'components': {
            'sg_body': C('Pressure-retaining body that carries the windows.', 'Cast/fabricated cross body with flanges.', 'Stainless, carbon steel, ductile iron.', '—', ['Corrosion at gasket faces'], ['Visual']),
            'sg_glass': C('Allow the process to be seen while containing pressure.', 'Toughened borosilicate discs with gaskets.', 'Borosilicate glass, PTFE gaskets.',
                          'Thermal shock and over-pressure can break glass; fit shields where needed.', ['Cracking', 'Etching (caustic, HF)'], ['Inspect for chips/etching']),
            'sg_rings': C('Clamp the glass evenly.', 'Cover rings with studs.', 'Stainless.', 'Tighten evenly in a cross pattern.', ['Uneven bolting → glass breakage'], ['Torque check']),
        },
    },
    'flow_indicator': {
        'summary': ('A flow indicator shows at a glance whether liquid is flowing. In the rotor type a paddle wheel behind a window spins when liquid moves, '
                    'its speed roughly following the flow rate. It is used on cooling-water, seal-flush and lubrication lines.'),
        'classification': {'family': 'Instrumentation accessory', 'type': 'Rotor (paddle-wheel) flow indicator'},
        'model_configuration': {'alternatives': 'Flapper, ball (drip), and variable-area indicators'},
        'standards': _std(('ASME B16.34', 'Body ratings', 'Pressure rating of the body.'),),
        'references': ['Instrument accessory catalogues (generic)'],
        'components': {
            'fi_body': C('Housing with rotor chamber and windows.', 'Cast body with flanged ends.', 'Bronze, stainless, carbon steel.', '—', ['Fouling'], ['Clean chamber']),
            'sg_glass': C('Window to observe the rotor.', 'Toughened glass discs.', 'Borosilicate.', '—', ['Fouling, cracking'], ['Visual']),
            'fi_rotor': C('Spins with the flow to show movement.', 'Paddle wheel on a shaft in the chamber.', 'PTFE, stainless, coloured plastic.', 'Not a measuring device.', ['Jammed rotor'], ['Clean and check freedom']),
        },
    },
}

BUILDERS = {'pressure_sustaining_valve': pressure_sustaining_valve, 'steam_trap': steam_trap, 'flame_arrestor': flame_arrestor,
            'rupture_disc': rupture_disc, 'sight_glass': sight_glass, 'flow_indicator': flow_indicator}
