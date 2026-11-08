"""Material Handling — EQ-210 … EQ-227: stackers/reclaimers, conveyors, pneumatic conveying, lifting, hydraulics, BWE."""
import math
from mathutils import Matrix, Vector
from pumpforge.core import Model, lathe, cyl, box, csg, split, join, rotate, extrude_poly, hex_prism, TAU, OPERATE_FRAMES
from pumpforge.valvekit import P, keys_loop, smooth_pulse, spring, sphere, shape_key, morph_loop
from pumpforge.parts import add_motor_h, add_coupling, hollow_pipe, pressure_gauge, transform_parts
from pumpforge.rotkit import open_path, sprocket, local_pivot, axis_rot_keys, ring_of, helical_gear
from pumpforge.handlingkit import hopper, beam, movers, polyline_path, rock, rocks_along, belt_loop, wheel, rope, hook_block
from pumpforge.vesselkit import half, vessel, liquid, nozzle
from pumpforge.shapes import sweep_tube, twisted_extrude
from pumpforge.common_meta import C

CAT = '9 · Material Handling & Heavy Machinery'


def _model(pid, title):
    return Model(pid, title, CAT, META[pid])


def _keys_part(m, part, path, fn):
    keys_loop(m, part, fn, path)


def _rails(m, x0, x1, ys, z=0.0):
    rl = [box(f'rl{i}', (x1 - x0, 0.06, 0.08), ((x0 + x1) / 2, y, z + 0.04), 'steel_dark') for i, y in enumerate(ys)]
    rl += [box(f'sl{k}', (0.1, abs(ys[-1] - ys[0]) + 0.3, 0.04), (x0 + 0.2 + 0.4 * k, (ys[0] + ys[-1]) / 2, z - 0.02), 'cast_iron') for k in range(int((x1 - x0) / 0.4))]
    P(m, 'rails', 'Rails & Sleepers (travel track)', 'structure', rl, explode=(0, 0, -0.3), ref='hm_rails', section='keep')


def _pile(m, x, y, R, H, mat='coal', name='Stockpile'):
    p = lathe('pile', [(0.0, 0.0), (R, 0.0), (0.0, H)], mat, 48, center=(x, y, 0))
    P(m, 'stockpile', name, 'material', p, explode=(0, 0, 0), ref='hm_pile', section='keep')


def _slewed_lumps(m, pid, name, pts, n, slew, trav, r=0.06, mat='coal'):
    """Lumps riding the boom conveyor: path in the boom's XZ plane, then slewed/travelled with the superstructure."""
    pos, L = polyline_path(pts)
    p = m.part(pid, name, 'flow_tracers', explode=(0, -0.3, 0.2), info={'ref': 'flow_tracers'})
    for i in range(n):
        ms = p.add(rock(f'{pid}{i}', r * (0.7 + 0.6 * ((i * 0.37) % 1)), mat, i), smooth_angle=30)
        lk = []
        for f in range(OPERATE_FRAMES + 1):
            t = f / OPERATE_FRAMES
            x, z, _ = pos(L * i / n + L * t)
            a = slew(t)
            lk.append((1 + f, (x * math.cos(a) + trav(t), x * math.sin(a), z)))
        ms.location = lk[0][1]
        m.keyframes(ms, 'Operate', 'location', lk)
    return p


# =============================================================== boom machines: stacker, reclaimer, stacker-reclaimer, BWE
def _boom_machine(pid, title, kind):
    m = _model(pid, title)
    Hp = 1.2                                       # slew bearing height
    slew = lambda t: math.radians(18) * math.sin(TAU * t)
    trav = lambda t: 0.25 * math.sin(TAU * t)
    if kind == 'bwe':
        crawl = []
        for s in (-1, 1):
            pos, L = open_path(0.22, 0.22, 2.0, -1.0, 0.25)
            crawl.append(join(f'tf{s}', [box(f'tb{s}', (2.0, 0.45, 0.3), (0.0, s * 0.75, 0.25), 'paint_yellow')] +
                              [cyl(f'tw{s}{k}', 0.22, s * 0.75 - 0.22, s * 0.75 + 0.22, 'steel_dark', 24, axis='Y', center=(x, 0, 0.25)) for k, x in enumerate((-1.0, 1.0))]))
            movers(m, f'track_{"left" if s < 0 else "right"}', f'Crawler Track Shoes ({"left" if s < 0 else "right"})', pos, L, 24, L / 6,
                   lambda i, s=s: box(f'ts{s}{i}', (0.2, 0.5, 0.05), (0, 0, 0), 'steel_dark'), group='undercarriage', ref='bw_crawler', y=s * 0.75)
        P(m, 'crawlers', 'Crawler Undercarriage (track frames)', 'undercarriage', crawl, explode=(0, 0, -0.4), ref='bw_crawler', section='keep')
        base = cyl('bs', 0.7, 0.4, Hp - 0.1, 'paint_yellow', 48)
        P(m, 'base', 'Lower Structure & Slew Ring', 'structure', base, explode=(0, 0, -0.2), ref='bw_base', section='keep')
    else:
        _rails(m, -2.5, 2.5, (-0.7, 0.7))
        car = [box('cb', (1.6, 1.6, 0.3), (0, 0, 0.5), 'paint_yellow', bevel=0.02)] + [cyl(f'w{i}{s}', 0.14, s * 0.7 - 0.05, s * 0.7 + 0.05, 'steel', 24, axis='Y', center=(x, 0, 0.18))
                                                                                     for i, x in enumerate((-0.6, -0.3, 0.3, 0.6)) for s in (-1, 1)]
        car += [cyl('pt', 0.45, 0.65, Hp - 0.1, 'paint_yellow', 48)]
        pc = P(m, 'portal', 'Portal / Travel Carriage with Bogies', 'undercarriage', car, explode=(0, 0, -0.3), ref='sr_portal', section='keep')
        keys_loop(m, pc, lambda t: (trav(t), 0, 0))
    sup = [cyl('sr', 0.6, Hp - 0.1, Hp, 'steel_dark', 64), box('mh', (1.2, 1.0, 0.6), (-0.3, 0, Hp + 0.35), 'paint_yellow', bevel=0.03),
           box('cab', (0.4, 0.35, 0.35), (0.35, -0.55, Hp + 0.55), 'glass' if False else 'paint_grey', bevel=0.02), box('mast', (0.2, 0.2, 1.4), (-0.2, 0, Hp + 1.3), 'paint_yellow')]
    cw = box('cw', (0.8, 0.9, 0.6), (-2.2, 0, Hp + 0.6), 'cast_iron', bevel=0.02)
    cwb = beam('cwb', (-0.3, 0, Hp + 0.6), (-2.0, 0, Hp + 0.6), w=0.3, h=0.3)
    stays = [rope(f'sty{s}', [(-0.2, s * 0.08, Hp + 2.0), (3.2, s * 0.25, Hp + 0.9)], r=0.015), rope(f'stc{s}', [(-0.2, s * 0.08, Hp + 2.0), (-2.0, s * 0.3, Hp + 0.9)], r=0.015)] if False else []
    stays = [rope('sty1', [(-0.2, 0.0, Hp + 2.0), (3.0, 0.0, Hp + 0.85)], r=0.02), rope('stc1', [(-0.2, 0.0, Hp + 2.0), (-2.0, 0.0, Hp + 0.9)], r=0.02)]
    boom = [beam('bm1', (0.0, 0.25, Hp + 0.6), (3.6, 0.25, Hp + 0.6 + 3.6 * math.tan(math.radians(-6))), w=0.08, h=0.25),
            beam('bm2', (0.0, -0.25, Hp + 0.6), (3.6, -0.25, Hp + 0.6 + 3.6 * math.tan(math.radians(-6))), w=0.08, h=0.25)]
    for k in range(6):
        x = 0.3 + 0.55 * k
        z = Hp + 0.6 + x * math.tan(math.radians(-6))
        boom.append(box(f'bx{k}', (0.06, 0.5, 0.06), (x, 0, z), 'paint_yellow'))
    tip = Vector((3.6, 0, Hp + 0.6 + 3.6 * math.tan(math.radians(-6))))
    belt = [beam('bb', (0.0, 0, Hp + 0.72), (3.5, 0, tip.z + 0.12), w=0.4, h=0.015)]
    belt[0].data.materials.clear()
    from pumpforge.core import M as _Mat
    belt[0].data.materials.append(_Mat('belt'))
    parts = sup + [cw, cwb] + stays + boom + belt
    if kind in ('reclaimer', 'both', 'bwe'):
        wh = [cyl('wr', 0.6, -0.12, 0.12, 'paint_orange', 48, axis='Y', center=(tip.x + 0.3, 0, tip.z), r_in=0.5)]
        for k in range(10):
            b = box(f'bk{k}', (0.28, 0.3, 0.22), (tip.x + 0.3, 0, tip.z + 0.62), 'steel_dark', bevel=0.02)
            wh.append(rotate(b, TAU * k / 10, 'Y', (tip.x + 0.3, 0, tip.z)))
        wh.append(cyl('wh', 0.12, -0.25, 0.25, 'steel', 24, axis='Y', center=(tip.x + 0.3, 0, tip.z)))
    pivot = (0, 0, Hp)
    sp = P(m, 'superstructure', 'Slewing Superstructure: Machinery House, Cab, Mast, Counterweight & Boom Conveyor', 'superstructure', parts, explode=(0, 0, 0.6), ref='sr_boom', section='keep')
    for mesh in sp.meshes:
        axis_rot_keys(m, mesh, (0, 0, 1), slew)
        if kind != 'bwe':
            pass
    if kind != 'bwe':
        for mesh in sp.meshes:
            m.keyframes(mesh, 'Operate', 'location', [(1 + f, (trav(f / OPERATE_FRAMES), 0, 0)) for f in range(OPERATE_FRAMES + 1)])
    if kind in ('reclaimer', 'both', 'bwe'):
        pw = P(m, 'bucket_wheel', 'Bucket Wheel (digs material and drops it on the boom conveyor)', 'rotating_element', wh, explode=(0.6, 0, 0.3), ref='sr_wheel', section='keep', pivot=(tip.x + 0.3, 0, tip.z))
        # wheel: spin + slew about the machine centre — combine into one rotation key per frame
        wc = Vector((tip.x + 0.3, 0, tip.z))
        for mesh in pw.meshes:                     # part node sits at the wheel centre; keys are relative to it
            lk, rk = [], []
            for f in range(OPERATE_FRAMES + 1):
                t = f / OPERATE_FRAMES
                Rz = Matrix.Rotation(slew(t), 3, 'Z')
                c = Rz @ Vector((tip.x + 0.3, 0, tip.z))
                if kind != 'bwe':
                    c = c + Vector((trav(t), 0, 0))
                R = Rz @ Matrix.Rotation(-TAU * 2 * t, 3, 'Y')
                e = R.to_euler('XYZ')
                lk.append((1 + f, tuple(c - wc)))
                rk.append((1 + f, (e.x, e.y, e.z)))
            m.keyframes(mesh, 'Operate', 'location', lk)
            m.keyframes(mesh, 'Operate', 'rotation_euler', rk)
    if kind == 'bwe':
        db = [beam('db1', (-0.3, 0, Hp + 0.4), (-2.6, 0.0, Hp - 0.1), w=0.35, h=0.15)]
        pdb = P(m, 'discharge_boom', 'Discharge Boom (loads trucks/conveyors)', 'superstructure', db, explode=(-0.5, 0, 0.3), ref='bw_discharge', section='keep')
        for mesh in pdb.meshes:
            axis_rot_keys(m, mesh, (0, 0, 1), lambda t: -0.5 * slew(t))
        # benched face: two benches with a sloping face the wheel cuts into (profile in XZ, extruded across Y)
        face = extrude_poly('face', [(4.15, 0.0), (6.2, 0.0), (6.2, 2.6), (5.3, 2.6), (5.05, 1.7), (4.75, 1.7), (4.35, 0.6)], -1.6, 1.6, 'ore', plane='XZ')
        P(m, 'mine_face', 'Mine Bench / Face (overburden, coal, lignite)', 'material', face, explode=(0, 0, 0), ref='hm_pile', section='keep')
        _slewed_lumps(m, 'spoil', 'Excavated Material on the Boom Conveyor', [(tip.x + 0.1, tip.z + 0.25), (0.05, Hp + 0.8)], 8, slew, lambda t: 0.0, mat='ore')
        m.flow('excavated', [(tip.x + 0.6, 0, tip.z + 0.3), (tip.x, 0, tip.z + 0.15), (0.0, 0, Hp + 0.75), (-2.6, 0, Hp - 0.0), (-2.7, 0, 0.3)], 'flow_discharge', 0.03, 0.4)
    elif kind == 'stacker':
        _pile(m, 4.3, 0, 1.6, 1.5)
        _slewed_lumps(m, 'coal', 'Coal on the Boom Belt & Leaving the Tip', [(0.2, Hp + 0.8), (tip.x, tip.z + 0.15), (tip.x + 0.3, tip.z - 0.6), (tip.x + 0.5, 1.4)], 10, slew, trav)
        m.flow('stacking', [(-2.6, 0, 0.6), (-0.5, 0, 0.6), (0.0, 0, Hp + 0.75), (tip.x, 0, tip.z + 0.15), (tip.x + 0.4, 0, 1.5)], 'flow_discharge', 0.03, 0.4)
    else:
        _pile(m, 4.3, 0, 1.6, 1.5)
        _slewed_lumps(m, 'coal', 'Reclaimed Coal Riding the Boom Conveyor to the Centre Chute', [(tip.x + 0.1, tip.z + 0.25), (0.05, Hp + 0.8), (-0.05, 0.75), (-0.4, 0.66)], 10, slew, trav)
        m.flow('reclaiming', [(tip.x + 0.6, 0, tip.z + 0.3), (tip.x, 0, tip.z + 0.15), (0.0, 0, Hp + 0.75), (-0.5, 0, 0.6), (-2.6, 0, 0.6)], 'flow_discharge', 0.03, 0.4)
        if kind == 'both':
            m.flow('stacking_mode', [(-2.6, 0, 0.7), (0.0, 0, Hp + 0.8), (tip.x, 0, tip.z + 0.25)], 'flow_suction', 0.02, 0.4)
    if kind != 'bwe':
        yc = [box('yc', (5.2, 0.4, 0.04), (0.0, 1.2, 0.6), 'belt'), box('ycf', (5.2, 0.5, 0.08), (0.0, 1.2, 0.55), 'paint_grey')]
        P(m, 'yard_conveyor', 'Yard (Stockpile) Conveyor alongside the Rails', 'conveyor', yc, explode=(0, 0.6, 0), ref='hk_belt', section='keep')
    return m


def stacker(out):
    return _boom_machine('stacker', 'Rail-Mounted Slewing & Luffing Boom Stacker', 'stacker').export(out)


def reclaimer(out):
    return _boom_machine('reclaimer', 'Bucket Wheel Reclaimer (Boom Type)', 'reclaimer').export(out)


def stacker_reclaimer(out):
    return _boom_machine('stacker_reclaimer', 'Bucket Wheel Stacker-Reclaimer (Reversible Boom Conveyor)', 'both').export(out)


def bucket_wheel_excavator(out):
    return _boom_machine('bucket_wheel_excavator', 'Bucket Wheel Excavator (Crawler-Mounted, Surface Mining)', 'bwe').export(out)


# =============================================================== EQ-213 Tripper, EQ-214 Shuttle
def tripper_conveyor(out):
    m = _model('tripper_conveyor', 'Travelling Tripper on a Bunker-Feed Belt Conveyor')
    Z = 1.2
    belt_loop(m, 'cv', -2.4, 2.4, Z, 0.12, 0.6, revs=2, markers=0, label='Bunker Feed Conveyor', foot_z=None, frame=True)
    bins = [csg(f'bn{i}', [box(f'bo{i}', (0.9, 1.2, 1.0), (x, 0, 0.5), 'cast_iron')], [box(f'bi{i}', (0.8, 1.1, 1.0), (x, 0, 0.55), 'cast_iron')], 'cast_iron') for i, x in enumerate((-1.5, -0.5, 0.5, 1.5))]
    P(m, 'bunkers', 'Bunkers / Silos below the Conveyor', 'structure', bins, explode=(0, 0, -0.3), ref='tc_bunkers')
    tr = lambda t: 1.0 * math.sin(TAU * t)
    car = [beam('rmp', (-0.6, 0, Z + 0.14), (0.2, 0, Z + 0.6), w=0.62, h=0.02), cyl('hp', 0.12, -0.35, 0.35, 'steel', 32, axis='Y', center=(0.25, 0, Z + 0.55)),
           cyl('bp', 0.1, -0.35, 0.35, 'steel', 32, axis='Y', center=(0.4, 0, Z + 0.25)), box('cf', (1.2, 0.9, 0.04), (0.0, 0, Z + 0.75), 'paint_yellow'),
           hopper('ch', 0.5, 0.25, Z - 0.3, Z + 0.3, cx=0.35, cy=0.0)] + [cyl(f'tw{i}{s}', 0.08, s * 0.5 - 0.03, s * 0.5 + 0.03, 'steel', 16, axis='Y', center=(x, 0, Z - 0.05)) for i, x in enumerate((-0.6, 0.5)) for s in (-1, 1)] + \
          [box(f'lg{i}{s}', (0.05, 0.05, 0.8), (x, s * 0.45, Z + 0.35), 'paint_yellow') for i, x in enumerate((-0.6, 0.5)) for s in (-1, 1)]
    pc = P(m, 'tripper_car', 'Tripper Car: Ramp, Head & Snub Pulleys, Discharge Chute, Travel Wheels', 'tripper', car, explode=(0, 0, 0.6), ref='tc_tripper', section='keep')
    keys_loop(m, pc, lambda t: (tr(t), 0, 0))
    rl = [box(f'rl{s}', (5.0, 0.04, 0.04), (0, s * 0.5, Z - 0.15), 'steel_dark') for s in (-1, 1)]
    P(m, 'rails', 'Tripper Rails along the Conveyor Gallery', 'structure', rl, explode=(0, 0, -0.2), ref='hm_rails', section='keep')
    rk = m.part('coal', 'Coal Discharged into the Bunker below the Tripper', 'flow_tracers', explode=(0, 0, 0), info={'ref': 'flow_tracers'})
    for i in range(10):
        o = rock(f'rk{i}', 0.04, 'coal', i)
        ms = rk.add(o, smooth_angle=30)
        ph = i / 10
        lk = []
        for f in range(OPERATE_FRAMES + 1):
            t = f / OPERATE_FRAMES
            s = (t * 3 + ph) % 1.0
            x0 = tr(t)
            if s < 0.6:
                p = (-2.2 + (x0 + 0.25 + 2.2) * s / 0.6, 0.05, Z + 0.15 + (0.45 if s > 0.45 else 0))
            else:
                p = (x0 + 0.35, 0.05, Z + 0.4 - (s - 0.6) / 0.4 * 1.0)
            lk.append((1 + f, p))
        ms.location = lk[0][1]
        m.keyframes(ms, 'Operate', 'location', lk)
    m.flow('coal', [(-2.4, 0, Z + 0.15), (-0.6, 0, Z + 0.15), (0.25, 0, Z + 0.68), (0.35, 0, Z + 0.2), (0.35, 0, 0.6)], 'flow_discharge', 0.02, 0.3)
    return m.export(out)


def shuttle_conveyor(out):
    m = _model('shuttle_conveyor', 'Reversible Shuttle Conveyor on a Travelling Carriage')
    Z, R, HL = 1.2, 0.1, 1.0                     # pulley centre height, pulley radius, half belt length
    sh = lambda t: 0.8 * math.sin(TAU * t)        # carriage travel: right half-cycle, then left half-cycle
    VB = 8.0                                      # belt speed, m per Operate cycle (reverses at mid-cycle)
    bdir = lambda t: 1.0 if (t % 1.0) < 0.5 else -1.0
    bdisp = lambda t: VB * (t if t < 0.5 else 1.0 - t)       # belt surface travel (+x first, then back)
    n0 = len(m.parts)
    belt_loop(m, 'sc', -HL, HL, Z, R, 0.6, revs=0, markers=0, label='Reversible Shuttle Belt', foot_z=None)
    # reversing head/tail pulleys: replace the constant spin with forward-then-reverse rotation
    for p in m.parts[n0:]:
        if p.id.startswith('scpulley'):
            for mesh in p.meshes:
                m._anims[(mesh, 'Operate')] = [c for c in m._anims.get((mesh, 'Operate'), []) if c[0] != 'rotation_euler']
                m.keyframes(mesh, 'Operate', 'rotation_euler', [(1 + f, (0.0, bdisp(f / OPERATE_FRAMES) / R, 0.0)) for f in range(OPERATE_FRAMES + 1)])
    car = [box('cf', (2.2, 0.9, 0.06), (0, 0, Z - 0.25), 'paint_yellow')] + [cyl(f'w{i}{s}', 0.08, s * 0.45 - 0.03, s * 0.45 + 0.03, 'steel', 16, axis='Y', center=(x, 0, Z - 0.33)) for i, x in enumerate((-0.9, 0.9)) for s in (-1, 1)] + \
          [box('dr', (0.25, 0.25, 0.25), (0.0, 0.55, Z - 0.1), 'paint_blue')]
    P(m, 'carriage', 'Travelling Carriage with Wheels & Travel Drive', 'carriage', car, explode=(0, 0, -0.3), ref='shc_carriage', section='keep')
    for p in m.parts[n0:]:
        for mesh in p.meshes:
            m.keyframes(mesh, 'Operate', 'location', [(1 + f, (sh(f / OPERATE_FRAMES), 0, 0)) for f in range(OPERATE_FRAMES + 1)])
    rl = [box(f'rl{s}', (4.4, 0.04, 0.04), (0, s * 0.45, Z - 0.4), 'steel_dark') for s in (-1, 1)]
    bins = [csg(f'bn{i}', [box(f'bo{i}', (0.8, 1.1, 0.8), (x, 0, 0.4), 'cast_iron')], [box(f'bi{i}', (0.7, 1.0, 0.8), (x, 0, 0.45), 'cast_iron')], 'cast_iron') for i, x in enumerate((-1.6, -0.6, 0.4, 1.4))]
    P(m, 'rails_bins', 'Rails & Bins being Filled', 'structure', rl + bins, explode=(0, 0, -0.3), ref='shc_bins')
    feed = box('fd', (0.4, 0.4, 0.3), (0, 0, Z + 0.5), 'paint_grey')
    P(m, 'feed_chute', 'Fixed Feed Chute (centre)', 'structure', feed, explode=(0, 0, 0.4), ref='shc_feed', section='keep')
    # lumps: drop from the fixed chute, ride the moving belt to whichever end is discharging, fall into a bin
    rk = m.part('coal', 'Material Lumps: Chute → Belt → End Discharge into Bins', 'flow_tracers', explode=(0, 0, 0), info={'ref': 'flow_tracers'})
    BT = Z + R + 0.03
    for i in range(10):
        h, j = divmod(i, 5)
        ph = 0.5 * h + 0.02 + 0.21 * j / 5
        d = 1.0 if h == 0 else -1.0
        land = ph + 0.02
        r0 = -sh(land)                             # lands at world x = 0 → position relative to the carriage
        t_end = land + (HL - d * r0) / VB
        ms = rk.add(rock(f'lump{i}', 0.04, 'coal', i), smooth_angle=30)
        lk, sk = [], []
        for f in range(OPERATE_FRAMES + 1):
            t = f / OPERATE_FRAMES
            age = (t - ph) % 1.0
            tt = ph + age
            vis = 1.0
            if tt < land:
                pos = (0.0, 0.05, Z + 0.35 - (Z + 0.35 - BT) * (tt - ph) / 0.02)
            elif tt < t_end:
                pos = (sh(tt) + r0 + d * VB * (tt - land), 0.05, BT)
            elif tt < t_end + 0.06:
                u = (tt - t_end) / 0.06
                xe = sh(t_end) + d * HL
                pos = (xe + d * 0.2 * u, 0.05, BT - (BT - 0.55) * u * u)
            else:
                xe = sh(t_end) + d * HL
                pos, vis = (xe + d * 0.2, 0.05, 0.55), 0.0
            lk.append((1 + f, pos))
            sk.append((1 + f, (vis, vis, vis)))
        ms.location = lk[0][1]
        m.keyframes(ms, 'Operate', 'location', lk)
        m.keyframes(ms, 'Operate', 'scale', sk)
    m.flow('to_right_bins', [(0, 0, Z + 0.5), (0, 0, BT), (1.8, 0, BT), (1.8, 0, 0.6)], 'flow_discharge', 0.02, 0.3, active=[(0.0, 0.5)])
    m.flow('to_left_bins', [(0, 0, Z + 0.5), (0, 0, BT + 0.04), (-1.8, 0, BT + 0.04), (-1.8, 0, 0.6)], 'flow_suction', 0.02, 0.3, active=[(0.5, 1.0)])
    return m.export(out)


# =============================================================== EQ-215 Drag chain conveyor
def drag_chain_conveyor(out):
    m = _model('drag_chain_conveyor', 'En-Masse Drag Chain Conveyor (Enclosed, Flighted Chain)')
    Z, X0, X1, R, W = 0.6, -1.4, 1.4, 0.13, 0.35
    cs = csg('cs', [box('co', (X1 - X0 + 0.5, W + 0.06, 2 * R + 0.25), (0, 0, Z), 'paint_grey', bevel=0.01)], [box('ci', (X1 - X0 + 0.44, W, 2 * R + 0.19), (0, 0, Z), 'paint_grey')], 'paint_grey')
    P(m, 'casing', 'Enclosed Casing (dust-tight) with Inlet & Outlet', 'casing', cs, explode=(0, 0.5, 0), ref='dc_casing')
    pos, L = open_path(R, R, X1 - X0, X0, Z)
    n = int(L / 0.12)
    dist = L / n * 4
    movers(m, 'chain', 'Chain with Flights (drags the material bed)', pos, L, n, dist,
           lambda i: join(f'fl{i}', [box(f'fb{i}', (0.012, W - 0.04, 0.08), (0, 0, -0.04), 'steel_dark'), box(f'cl{i}', (0.11, 0.03, 0.02), (0, 0, 0), 'steel')]), group='conveyor', ref='dc_chain')
    for i, (x, nm) in enumerate(((X0, 'Tail (take-up)'), (X1, 'Head (drive)'))):
        sp_, _ = sprocket(f'sp{i}', 10, 2 * R * math.sin(math.pi / 10), 0.02, -0.03, 0.03, 'steel', cx=x, cz=Z)
        shf = cyl(f'sh{i}', 0.03, -W / 2 - 0.25, W / 2 + 0.1, 'steel', 16, axis='Y', center=(x, 0, Z))
        ps = P(m, f'sprocket_{i + 1}', f'{nm} Sprocket & Shaft', 'conveyor', [sp_, shf], explode=(0.3 * (1 if i else -1), 0, 0.2), ref='dc_sprocket', section='keep', pivot=(x, 0, Z))
        ps.spin('Y', dist / (TAU * R))
    noz = [box('in', (0.3, W, 0.3), (-0.9, 0, Z + R + 0.25), 'paint_grey'), box('out', (0.3, W, 0.3), (0.9, 0, Z - R - 0.25), 'paint_grey')]
    P(m, 'inlet_outlet', 'Inlet Spout & Bottom Outlet Gate', 'casing', noz, explode=(0, 0, 0.3), ref='dc_casing', section='keep')
    from pumps._eq_handling_a import _gearmotor
    _gearmotor(m, 'drive', X1, -W / 2 - 0.4, Z, label='Drive Gearmotor', ref='dc_drive')
    st = [box(f'st{i}', (0.08, W, Z - R - 0.12), (x, 0, (Z - R - 0.12) / 2), 'paint_grey') for i, x in enumerate((X0, 0.0, X1))]
    P(m, 'supports', 'Supports', 'structure', st, explode=(0, 0, -0.3), ref='dc_casing', section='keep')
    rocks_along(m, 'grain', 'Bulk Material Moving as a Mass', [(-0.9, Z + R + 0.3), (-0.9, Z - R + 0.06), (0.9, Z - R + 0.06), (0.9, Z - R - 0.4)], 14, r=0.025, mat='sand', y=0.05)
    m.flow('material', [(-0.9, 0, Z + R + 0.45), (-0.9, 0, Z - R + 0.07), (0.9, 0, Z - R + 0.07), (0.9, 0, Z - R - 0.45)], 'sand', 0.014, 0.25)
    return m.export(out)


# =============================================================== EQ-216 Pneumatic conveying system
def pneumatic_conveying_system(out):
    m = _model('pneumatic_conveying_system', 'Dilute-Phase Pneumatic Conveying System (Pressure Type)')
    bl = join('bl', [box('blb', (0.4, 0.35, 0.35), (-2.0, 0, 0.35), 'cast_iron', bevel=0.02), cyl('blm', 0.13, 0.17, 0.5, 'paint_motor', 32, axis='Y', center=(-2.0, 0, 0.35)),
                     cyl('bls', 0.12, 0.55, 0.9, 'paint_grey', 32, center=(-2.0, 0, 0))])
    P(m, 'blower', 'Positive-Displacement Blower & Inlet Silencer (air mover)', 'air_mover', bl, explode=(-0.4, 0, 0), ref='pc_blower', section='keep')
    hp = join('hp', [lathe('hpc', [(0.35, 1.6), (0.35, 1.0), (0.08, 0.75), (0.0, 0.75), (0.0, 1.6)], 'paint_grey', 48, center=(-1.2, 0, 0)), box('rv', (0.2, 0.2, 0.2), (-1.2, 0, 0.62), 'cast_iron')])
    P(m, 'feed_hopper_valve', 'Feed Hopper & Rotary Airlock (feeds solids into the line)', 'feeder', hp, explode=(0, 0, 0.4), ref='pc_feeder', section='keep')
    line = [(-1.8, 0, 0.35), (-1.2, 0, 0.35), (0.4, 0, 0.35), (0.6, 0, 0.55), (0.6, 0, 2.2), (0.8, 0, 2.4), (1.6, 0, 2.4), (1.75, 0, 2.25)]
    pl = hollow_pipe('pl', line, 0.045, 'stainless', 24, bend=0.18, t=0.004)
    P(m, 'pipeline', 'Conveying Pipeline with Long-Radius Bends', 'system_piping', pl, explode=(0, 0.4, 0), ref='pc_pipeline')
    rc = vessel('rc', 0.35, 0.6, 0.006, 'stainless', heads=('cone', 'flat'), z0=1.7, center=(2.0, 0, 0))
    bf = join('bf', [cyl('bfs', 0.36, 2.3, 2.85, 'paint_grey', 48, center=(2.0, 0, 0), r_in=0.35), cyl('bft', 0.36, 2.79, 2.81, 'steel', 48, center=(2.0, 0, 0)),
                     cyl('bfc', 0.37, 2.85, 2.9, 'paint_grey', 48, center=(2.0, 0, 0)), cyl('bfo', 0.06, 2.9, 3.05, 'paint_grey', 24, center=(2.0, 0.2, 0))])
    bags = [cyl(f'bg{i}', 0.05, 2.32, 2.8, 'polypropylene', 16, center=(2.0 + 0.15 * math.cos(TAU * i / 6), 0.15 * math.sin(TAU * i / 6), 0)) for i in range(6)]
    P(m, 'receiver_filter', 'Receiver with Bag Filter (separates solids from conveying air)', 'separator', [rc, bf] + bags, explode=(0.4, 0, 0.3), ref='pc_receiver')
    silo = vessel('silo', 0.5, 1.2, 0.006, 'paint_grey', heads=('cone', 'flat'), z0=0.45, center=(2.0, 0, 0))
    P(m, 'silo', 'Receiving Silo', 'vessel', silo, explode=(0, 0, -0.3), ref='pc_silo')
    legs_ = [box(f'sl{i}', (0.06, 0.06, 0.9), (2.0 + 0.45 * math.cos(TAU * i / 4 + 0.78), 0.45 * math.sin(TAU * i / 4 + 0.78), 0.45), 'paint_grey') for i in range(4)]
    P(m, 'supports', 'Silo Legs & Pipe Supports', 'structure', legs_, explode=(0, 0, -0.3), ref='pc_silo', section='keep')
    add_tracers = __import__('pumpforge.parts', fromlist=['add_tracers']).add_tracers
    add_tracers(m, 'particles', 'Solids Particles Carried by the Air', [(-1.2, 0, 0.6), (-1.2, 0, 0.35), (0.4, 0, 0.35), (0.6, 0, 0.55), (0.6, 0, 2.2), (0.8, 0, 2.4), (1.6, 0, 2.4), (2.0, 0, 2.0), (2.0, 0, 1.2)],
                n=16, radius=0.022, mat='sand', loops=2)
    m.flow('air', [(-2.0, 0, 0.9), (-2.0, 0, 0.35)] + line[1:] + [(2.0, 0, 2.0), (2.0, 0, 2.75), (2.0, 0.2, 2.86), (2.0, 0.2, 3.1)], 'air', 0.014, 0.3)
    m.flow('solids', [(-1.2, 0, 1.5), (-1.2, 0, 0.35)] + line[2:] + [(2.0, 0, 1.9), (2.0, 0, 1.0)], 'sand', 0.01, 0.3)
    return m.export(out)


# =============================================================== EQ-217 Screw jack
def screw_jack(out):
    m = _model('screw_jack', 'Worm-Gear Screw Jack (Translating Screw)')
    CZ = 0.35
    lift = lambda t: 0.15 * smooth_pulse(t, 0.35, 0.15, 0.35)
    hs = csg('hs', [box('ho', (0.3, 0.24, 0.22), (0, 0, CZ), 'paint_blue', bevel=0.02), cyl('hb', 0.06, CZ - 0.2, CZ + 0.18, 'paint_blue', 32)],
             [cyl('hw', 0.095, -0.06, 0.06, 'paint_blue', 48, axis='Y', center=(0, 0, CZ)), cyl('hs_', 0.031, CZ - 0.3, CZ + 0.3, 'paint_blue', 24), cyl('wb', 0.03, -0.3, 0.3, 'paint_blue', 24, axis='X', center=(0, 0.0, CZ - 0.11))], 'paint_blue')
    P(m, 'housing', 'Gear Housing', 'casing', hs, explode=(0, 0.4, 0), ref='sj_housing')
    worm = join('worm', [twisted_extrude('wt', [(0.022 * math.cos(a), 0.022 * math.sin(a) + (0.008 if (a % (TAU / 2)) < 0.4 else 0)) for a in [TAU * k / 24 for k in range(24)]], -0.08, 0.08, 0.025, 'steel', axis='X', center=(0, 0, CZ - 0.11)),
                         cyl('ws', 0.015, -0.35, 0.35, 'steel', 16, axis='X', center=(0, 0, CZ - 0.11))])
    pw = P(m, 'worm', 'Worm (input shaft)', 'rotating_element', worm, explode=(0, -0.3, -0.2), ref='sj_worm', section='keep', pivot=(0, 0, CZ - 0.11))
    g, _ = helical_gear('wg', 0.006, 30, -0.05, 0.05, 'bronze', cx=0, cz=0, helix_deg=8, bore=0.031)
    g.data.transform(Matrix.Translation((0, 0, CZ)) @ Matrix.Rotation(math.pi / 2, 4, 'X'))
    pg = P(m, 'worm_wheel', 'Worm Wheel (bronze) with Internal Thread (nut)', 'rotating_element', g, explode=(0, -0.5, 0.2), ref='sj_wheel', section='keep', pivot=(0, 0, CZ))
    th_w = lambda t: TAU * 6 * (lift(t) / 0.15)
    for mesh in pg.meshes:
        m.keyframes(mesh, 'Operate', 'rotation_euler', [(1 + f, (0, 0, th_w(f / OPERATE_FRAMES) / 30)) for f in range(OPERATE_FRAMES + 1)])
    for mesh in pw.meshes:
        m.keyframes(mesh, 'Operate', 'rotation_euler', [(1 + f, (th_w(f / OPERATE_FRAMES), 0, 0)) for f in range(OPERATE_FRAMES + 1)])
    scr = join('scr', [sweep_tube('thr', [(0.028 * math.cos(TAU * 20 * k / 400), 0.028 * math.sin(TAU * 20 * k / 400), CZ - 0.25 + 0.6 * k / 400) for k in range(401)], 0.004, 'steel', 6),
                       cyl('sc', 0.026, CZ - 0.25, CZ + 0.35, 'steel', 24), cyl('lp', 0.09, CZ + 0.35, CZ + 0.37, 'steel', 32)])
    ps = P(m, 'lifting_screw', 'Lifting Screw (Acme/trapezoidal) & Load Plate — translates', 'rotating_element', scr, explode=(0, 0, 0.5), ref='sj_screw', section='keep')
    keys_loop(m, ps, lambda t: (0, 0, lift(t)))
    load = box('ld', (0.5, 0.4, 0.06), (0, 0, CZ + 0.4), 'cast_iron')
    pl = P(m, 'load', 'Load (platform being raised)', 'load', load, explode=(0, 0, 0.7), ref='sj_load', section='keep')
    keys_loop(m, pl, lambda t: (0, 0, lift(t)))
    add_motor_h(m, 'm_', 0.37, CZ - 0.11, 0.07, 0.2, CZ - 0.11 - 0.09, 0.015, 0.02, explode_dx=0.3, revs=3)
    bs = box('bs', (0.6, 0.4, 0.04), (0.2, 0, CZ - 0.22), 'paint_grey')
    P(m, 'base', 'Mounting Base', 'structure', bs, explode=(0, 0, -0.3), ref='sj_housing', section='keep')
    m.flow('power', [(0.6, 0, CZ - 0.11), (0.0, 0, CZ - 0.11), (0.0, 0, CZ), (0.0, 0, CZ + 0.4)], 'power', 0.008, 0.15)
    return m.export(out)


# =============================================================== cranes and hoists
def _hoist(m, pid, x, y, z_top, z_hook, label='Hoist', moving=None, lift=None, ref='cr_hoist'):
    """Hoist body + rope + hook block + load. moving(t)->(dx, dy) for trolley travel; lift(t)->hook height."""
    body = join(pid + 'b', [box(pid + 'hb', (0.35, 0.25, 0.18), (x, y, z_top - 0.12), 'paint_yellow', bevel=0.02), cyl(pid + 'dr', 0.07, x - 0.12, x + 0.12, 'steel_dark', 32, axis='X', center=(0, y, z_top - 0.12)),
                            cyl(pid + 'mt', 0.06, x + 0.17, x + 0.33, 'paint_motor', 24, axis='X', center=(0, y, z_top - 0.12))])
    pb = P(m, pid + '_trolley', f'{label}: Trolley, Rope Drum & Hoist Motor', 'hoist', body, explode=(0, -0.3, 0.3), ref=ref, section='keep')
    hook = join(pid + 'hk', [box(pid + 'blk', (0.12, 0.08, 0.14), (x, y, 0.0 + 0.07), 'paint_yellow', bevel=0.01),
                             sweep_tube(pid + 'hh', [(x, y, 0.0), (x, y, -0.06), (x + 0.03, y, -0.1), (x + 0.06, y, -0.07)], 0.012, 'steel', 10),
                             box(pid + 'ld', (0.4, 0.3, 0.25), (x, y, -0.3), 'cast_iron', bevel=0.01), rope(pid + 'sl', [(x - 0.15, y, -0.18), (x + 0.0, y, -0.08), (x + 0.15, y, -0.18)], r=0.006)])
    ph = P(m, pid + '_hook', 'Hook Block & Load', 'hoist', hook, explode=(0, -0.3, -0.3), ref=ref, section='keep')
    rp = rope(pid + 'rp', [(x, y, z_top - 0.2), (x, y, 0.15)], r=0.007)
    prp = P(m, pid + '_rope', 'Wire Rope (scales with hook height)', 'hoist', rp, explode=(0, -0.3, 0), ref=ref, section='keep')
    for f_ in (pb, ph, prp):
        for mesh in f_.meshes:
            lk, sk = [], []
            for f in range(OPERATE_FRAMES + 1):
                t = f / OPERATE_FRAMES
                dx, dy = moving(t) if moving else (0, 0)
                zh = lift(t) if lift else z_hook
                if f_ is pb:
                    lk.append((1 + f, (dx, dy, 0)))
                elif f_ is ph:
                    lk.append((1 + f, (dx, dy, zh)))
                else:
                    s = (z_top - 0.2 - zh - 0.15) / (z_top - 0.2 - 0.15)
                    lk.append((1 + f, (dx, dy, (z_top - 0.2) * (1 - s))))
                    sk.append((1 + f, (1.0, 1.0, max(0.05, s))))
            m.keyframes(mesh, 'Operate', 'location', lk)
            if sk:
                m.keyframes(mesh, 'Operate', 'scale', sk)


def gantry_crane(out):
    m = _model('gantry_crane', 'Double-Girder Gantry Crane (Rail-Mounted)')
    H, S, Wd = 2.4, 3.0, 1.6
    trav = lambda t: 0.3 * math.sin(TAU * t)
    gir = [box(f'g{s}', (S + 0.4, 0.12, 0.25), (0, s * 0.3, H), 'paint_yellow') for s in (-1, 1)] + [box(f'tr{s}', (S + 0.3, 0.05, 0.04), (0, s * 0.3, H + 0.145), 'steel_dark') for s in (-1, 1)]
    legs_ = [beam(f'l{i}{s}', (sx * S / 2, s * 0.3, H), (sx * S / 2, s * Wd / 2, 0.25), w=0.12, h=0.12) for i, sx in enumerate((-1, 1)) for s in (-1, 1)]
    ec = [box(f'ec{i}', (0.25, Wd + 0.2, 0.15), (sx * S / 2, 0, 0.18), 'paint_yellow') for i, sx in enumerate((-1, 1))] + \
         [cyl(f'ew{i}{s}', 0.09, s * Wd / 2 - 0.03 + 0.0, s * Wd / 2 + 0.03, 'steel', 24, axis='Y', center=(sx * S / 2, 0, 0.09)) for i, sx in enumerate((-1, 1)) for s in (-1, 1)] if False else \
         [box(f'ec{i}', (0.25, Wd + 0.2, 0.15), (sx * S / 2, 0, 0.18), 'paint_yellow') for i, sx in enumerate((-1, 1))] + \
         [cyl(f'ew{i}{k}', 0.08, sx * S / 2 - 0.03 + 0.0, sx * S / 2 + 0.03, 'steel', 24, axis='X', center=(0, s * (Wd / 2), 0.09)) for i, sx in enumerate((-1, 1)) for k, s in enumerate((-1, 1))]
    pg = P(m, 'gantry', 'Gantry Structure: Twin Girders, Legs & End Carriages (long travel)', 'structure', gir + legs_ + ec, explode=(0, 0, 0), ref='cr_gantry', section='keep')
    keys_loop(m, pg, lambda t: (0, trav(t), 0))
    rl = [box(f'rl{i}', (0.08, 4.0, 0.06), (sx * S / 2, 0, 0.0), 'steel_dark') for i, sx in enumerate((-1, 1))]
    P(m, 'rails', 'Runway Rails', 'structure', rl, explode=(0, 0, -0.2), ref='hm_rails', section='keep')
    _hoist(m, 'hst', 0.0, 0.0, H + 0.4, 0.4, label='Crab / Trolley', moving=lambda t: (1.0 * math.sin(TAU * t + 0.6), trav(t)), lift=lambda t: 0.5 + 0.9 * smooth_pulse((t + 0.2) % 1, 0.25, 0.2, 0.25))
    cab = join('cab', [box('cbb', (0.35, 0.3, 0.35), (S / 2 - 0.3, -0.3, H - 0.33), 'paint_grey', bevel=0.02), box('cbw', (0.01, 0.22, 0.14), (S / 2 - 0.475, -0.3, H - 0.3), 'glass'),
                       box('cbh', (0.2, 0.08, 0.06), (S / 2 - 0.3, -0.3, H - 0.14), 'paint_yellow')])
    pcb = P(m, 'cab', 'Operator Cab / Radio Control', 'controls', cab, explode=(0.3, -0.3, 0), ref='cr_controls', section='keep')
    keys_loop(m, pcb, lambda t: (0, trav(t), 0))
    m.flow('supply', [(S / 2 - 0.3, -0.3, H - 0.16), (S / 2 - 0.3, -0.3, H + 0.2), (0.2, -0.3, H + 0.2), (0.2, -0.05, H + 0.35)], 'electric', 0.01, 0.3)
    return m.export(out)


def jib_crane(out):
    m = _model('jib_crane', 'Pillar-Mounted Slewing Jib Crane')
    H, Lj = 2.2, 2.0
    slew = lambda t: math.radians(60) * math.sin(TAU * t)
    pil = join('pil', [cyl('pc', 0.1, 0.0, H + 0.2, 'paint_yellow', 32), cyl('pb', 0.3, 0.0, 0.04, 'paint_yellow', 32), cyl('fd', 0.5, -0.3, 0.0, 'cast_iron', 32)])
    P(m, 'pillar', 'Pillar & Foundation (anchor bolts)', 'structure', pil, explode=(0, 0, -0.3), ref='jc_pillar', section='keep')
    arm = join('arm', [box('ab', (Lj, 0.1, 0.18), (Lj / 2, 0, H), 'paint_yellow'), beam('br', (0.1, 0, H - 0.6), (Lj * 0.6, 0, H - 0.09), w=0.06, h=0.06),
                       cyl('sb', 0.14, H - 0.12, H + 0.1, 'steel_dark', 32), box('es', (0.05, 0.15, 0.1), (Lj - 0.03, 0, H + 0.12), 'paint_red')])
    pa = P(m, 'jib_arm', 'Jib Arm with Slewing Bearing & Bracing', 'structure', arm, explode=(0, 0, 0.4), ref='jc_arm', section='keep')
    for mesh in pa.meshes:
        axis_rot_keys(m, mesh, (0, 0, 1), slew)
    tx = lambda t: 1.2 + 0.4 * math.sin(TAU * 2 * t)
    lift = lambda t: 0.6 + 0.6 * smooth_pulse(t, 0.25, 0.25, 0.25)
    body = join('hb', [box('hbb', (0.25, 0.2, 0.18), (0, 0, H - 0.2), 'paint_yellow', bevel=0.02), cyl('hbm', 0.05, 0.12, 0.25, 'paint_motor', 24, axis='X', center=(0, 0, H - 0.2))])
    hook = join('hk', [box('blk', (0.1, 0.08, 0.12), (0, 0, 0.06), 'paint_yellow'), sweep_tube('hh', [(0, 0, 0.0), (0, 0, -0.06), (0.03, 0, -0.1), (0.06, 0, -0.07)], 0.012, 'steel', 10),
                       box('ld', (0.3, 0.3, 0.2), (0, 0, -0.28), 'cast_iron')])
    rp = rope('rp', [(0, 0, H - 0.3), (0, 0, 0.12)], r=0.006)
    for nm, obj, kind in (('hoist_trolley', body, 'b'), ('hook_load', hook, 'h'), ('rope', rp, 'r')):
        p = P(m, nm, {'b': 'Trolley & Electric Hoist', 'h': 'Hook Block & Load', 'r': 'Hoist Rope / Chain'}[kind], 'hoist', obj, explode=(0, -0.3, 0.2), ref='cr_hoist', section='keep')
        for mesh in p.meshes:
            lk, rk, sk = [], [], []
            for f in range(OPERATE_FRAMES + 1):
                t = f / OPERATE_FRAMES
                a = slew(t)
                x, y = tx(t) * math.cos(a), tx(t) * math.sin(a)
                zh = lift(t)
                if kind == 'b':
                    lk.append((1 + f, (x, y, 0)))
                elif kind == 'h':
                    lk.append((1 + f, (x, y, zh)))
                else:
                    s = (H - 0.3 - zh - 0.12) / (H - 0.3 - 0.12)
                    lk.append((1 + f, (x, y, (H - 0.3) * (1 - s))))
                    sk.append((1 + f, (1, 1, max(0.05, s))))
                rk.append((1 + f, (0, 0, a)))
            m.keyframes(mesh, 'Operate', 'location', lk)
            m.keyframes(mesh, 'Operate', 'rotation_euler', rk)
            if sk:
                m.keyframes(mesh, 'Operate', 'scale', sk)
    m.flow('supply', [(0.12, 0, 0.1), (0.12, 0, H - 0.15)], 'electric', 0.01, 0.3)
    return m.export(out)


def monorail_hoist(out):
    m = _model('monorail_hoist', 'Monorail Electric Chain Hoist (Curved I-Beam Track)')
    H = 2.2
    pts = [(-1.6, 0.0), (0.4, 0.0)] + [(0.4 + 0.8 * math.sin(math.pi / 2 * k / 8), 0.8 - 0.8 * math.cos(math.pi / 2 * k / 8)) for k in range(1, 9)] + [(1.2, 2.0)]
    beamobj = []
    for a, b in zip(pts[:-1], pts[1:]):
        beamobj.append(beam(f'ib{len(beamobj)}', (a[0], a[1], H), (b[0], b[1], H), w=0.1, h=0.2))
        beamobj.append(beam(f'if{len(beamobj)}', (a[0], a[1], H - 0.1), (b[0], b[1], H - 0.1), w=0.16, h=0.02))
    hang = [rope(f'hg{k}', [(x, y, H + 0.1), (x, y, H + 0.6)], r=0.015) for k, (x, y) in enumerate(((-1.4, 0), (-0.4, 0), (0.6, 0.1), (1.2, 1.5)))]
    P(m, 'track', 'I-Beam Monorail Track & Hangers', 'structure', beamobj + hang, explode=(0, 0, 0.4), ref='mh_track', section='keep')
    tx = lambda t: -1.2 + 1.3 * smooth_pulse(t, 0.3, 0.2, 0.3)
    _hoist(m, 'hst', 0.0, 0.0, H, 0.4, label='Trolley & Electric Chain Hoist', moving=lambda t: (tx(t), 0.0), lift=lambda t: 0.5 + 0.8 * smooth_pulse((t + 0.15) % 1, 0.2, 0.3, 0.2), ref='mh_hoist')
    pend = join('pd', [box('pdb', (0.06, 0.04, 0.15), (0.0, -0.2, 1.1), 'paint_yellow', bevel=0.01), rope('pdc', [(0.0, -0.13, H - 0.2), (0.0, -0.2, 1.18)], r=0.004)])
    ppd = P(m, 'pendant', 'Pendant Control Station (hangs from the trolley)', 'controls', pend, explode=(0, -0.3, 0), ref='mh_pendant', section='keep')
    keys_loop(m, ppd, lambda t: (tx(t), 0, 0))
    m.flow('travel', [(-1.2, 0, H - 0.25), (0.1, 0, H - 0.25)], 'power', 0.012, 0.3)
    return m.export(out)


def electric_winch(out):
    m = _model('electric_winch', 'Electric Winch (Drum, Gearbox, Brake)')
    CZ = 0.4
    pull = lambda t: 0.9 * smooth_pulse(t, 0.4, 0.1, 0.4)
    drum = join('drum', [cyl('dc', 0.14, -0.25, 0.25, 'steel', 48, axis='Y', center=(0, 0, CZ)), cyl('df1', 0.22, -0.28, -0.25, 'steel', 48, axis='Y', center=(0, 0, CZ)),
                         cyl('df2', 0.22, 0.25, 0.28, 'steel', 48, axis='Y', center=(0, 0, CZ)), cyl('dsh', 0.03, -0.45, 0.45, 'steel', 16, axis='Y', center=(0, 0, CZ))])
    rope_on = sweep_tube('rw', [(0.15 * math.cos(TAU * 12 * k / 480), -0.24 + 0.48 * k / 480, CZ + 0.15 * math.sin(TAU * 12 * k / 480)) for k in range(481)], 0.008, 'steel_dark', 6)
    pd = P(m, 'drum', 'Rope Drum (grooved) with Wound Wire Rope', 'rotating_element', [drum, rope_on], explode=(0, -0.4, 0.3), ref='ew_drum', section='keep', pivot=(0, 0, CZ))
    for mesh in pd.meshes:
        m.keyframes(mesh, 'Operate', 'rotation_euler', [(1 + f, (0, -pull(f / OPERATE_FRAMES) / 0.15, 0)) for f in range(OPERATE_FRAMES + 1)])
    gb = box('gb', (0.28, 0.2, 0.32), (0, 0.42, CZ), 'paint_blue', bevel=0.02)
    P(m, 'gearbox', 'Reduction Gearbox (planetary/helical)', 'drive', gb, explode=(0, 0.4, 0), ref='ew_gearbox', section='keep')
    mt = cyl('mt', 0.11, 0.52, 0.85, 'paint_motor', 32, axis='Y', center=(0, 0, CZ), ch=0.01)
    br = cyl('br', 0.12, 0.85, 0.95, 'paint_red', 32, axis='Y', center=(0, 0, CZ))
    P(m, 'motor_brake', 'Motor & Spring-Applied Electromagnetic Brake', 'drive', [mt, br], explode=(0, 0.7, 0), ref='ew_motor', section='keep')
    fr = [box('fb', (0.7, 1.5, 0.05), (0, 0.25, 0.025), 'paint_grey')] + [box(f'fs{s}', (0.4, 0.04, CZ + 0.15), (0, s * 0.31, (CZ + 0.15) / 2), 'paint_grey') for s in (-1, 1)]
    P(m, 'frame', 'Base Frame & Drum Supports', 'structure', fr, explode=(0, 0, -0.3), ref='ew_frame', section='keep')
    rp = rope('rp', [(0.15, 0, CZ), (2.4, 0, CZ)], r=0.008)
    P(m, 'rope', 'Wire Rope to Load', 'hoist', rp, explode=(0, 0, 0.2), ref='ew_rope', section='keep')
    ld = join('ld', [box('lb', (0.4, 0.4, 0.3), (2.6, 0, 0.15), 'cast_iron', bevel=0.01), cyl('lw1', 0.05, -0.22, -0.18, 'steel', 16, axis='Y', center=(2.5, 0, 0.05))])
    pl = P(m, 'load', 'Load being Hauled', 'load', ld, explode=(0.3, 0, 0), ref='ew_load', section='keep')
    keys_loop(m, pl, lambda t: (-pull(t), 0, 0))
    m.flow('pull', [(2.4, 0, CZ), (0.2, 0, CZ)], 'power', 0.01, 0.3)
    return m.export(out)


def _press_tubes(m, lines, title, desc, r=0.012):
    """Pressure overlay: tubes coloured on the low→high pressure scale (pressure_0 … pressure_9) along circuit lines."""
    objs = [sweep_tube(f'pt{i}', pts, r, f'pressure_{lev}', 10) for i, (pts, lev) in enumerate(lines)]
    m.overlay('pressure', join('press', objs), title, desc)


# =============================================================== hydraulics
def hydraulic_power_unit(out):
    m = _model('hydraulic_power_unit', 'Hydraulic Power Unit (HPU)')
    tk = csg('tk', [box('to', (1.0, 0.6, 0.5), (0, 0, 0.35), 'paint_blue', bevel=0.01)], [box('ti', (0.96, 0.56, 0.46), (0, 0, 0.35), 'paint_blue')], 'paint_blue')
    P(m, 'reservoir', 'Reservoir (tank) with Baffle', 'reservoir', [tk, box('bf', (0.01, 0.56, 0.3), (0.0, 0, 0.3), 'paint_blue')] + [box(f'ft{i}{s}', (0.08, 0.6, 0.1), (x, 0, 0.05), 'paint_grey') for i, x in enumerate((-0.42, 0.42)) for s in (1,)], explode=(0, 0, -0.3), ref='hp_reservoir')
    oil = box('oil', (0.95, 0.27, 0.32), (0, 0.135, 0.3), 'hydraulic_oil')
    P(m, 'oil', 'Hydraulic Oil', 'fluid', oil, explode=(0, -0.3, 0), ref='hp_oil', section='keep')
    pm = join('pm', [cyl('mt', 0.12, 0.76, 1.1, 'paint_motor', 32, center=(-0.2, 0, 0), ch=0.01), cyl('mfl', 0.13, 0.74, 0.76, 'paint_motor', 32, center=(-0.2, 0, 0)),
                     cyl('bh1', 0.11, 0.6, 0.63, 'paint_blue', 32, center=(-0.2, 0, 0)), cyl('bh2', 0.11, 0.71, 0.74, 'paint_blue', 32, center=(-0.2, 0, 0))] +
                    [box(f'bhr{k}', (0.03, 0.03, 0.08), (-0.2 + 0.095 * math.cos(TAU * k / 4 + 0.78), 0.095 * math.sin(TAU * k / 4 + 0.78), 0.67), 'paint_blue') for k in range(4)] +
                    [cyl('pp', 0.06, 0.4, 0.6, 'cast_iron', 32, center=(-0.2, 0, 0)), cyl('sct', 0.03, 0.2, 0.4, 'steel', 16, center=(-0.2, 0, 0)),
                     cyl('ssn', 0.045, 0.14, 0.2, 'steel_dark', 16, center=(-0.2, 0, 0))])
    P(m, 'motor_pump', 'Electric Motor, Lantern Bell Housing & Pump (gear/vane/piston) with Suction Strainer', 'pump', pm, explode=(0, 0, 0.5), ref='hp_pump', section='keep')
    cp = join('cp', [cyl('cph1', 0.045, 0.635, 0.665, 'steel', 24, center=(-0.2, 0, 0)), cyl('cph2', 0.045, 0.675, 0.705, 'steel', 24, center=(-0.2, 0, 0)),
                     cyl('cpe', 0.035, 0.665, 0.675, 'rubber', 24, center=(-0.2, 0, 0))] +
                    [box(f'cpj{k}', (0.02, 0.025, 0.02), (-0.2 + 0.04 * math.cos(TAU * k / 3), 0.04 * math.sin(TAU * k / 3), 0.67), 'steel') for k in range(3)])
    pcp = P(m, 'coupling', 'Jaw Coupling inside the Bell Housing (motor → pump)', 'pump', cp, explode=(0, -0.3, 0.5), ref='hp_pump', section='keep', pivot=(-0.2, 0, 0.67))
    pcp.spin('Z', 6)
    blk = join('blk', [box('mb', (0.22, 0.15, 0.12), (0.25, 0, 0.66), 'steel'), cyl('rv', 0.025, 0.72, 0.85, 'brass', 16, center=(0.2, 0, 0)), cyl('cv', 0.025, 0.72, 0.8, 'chrome', 16, center=(0.3, 0, 0)),
                       pressure_gauge('pg', (0.25, -0.075, 0.75), r=0.04, facing=(0, -1, 0))])
    P(m, 'valve_block', 'Pressure Relief Valve, Check Valve & Gauge on Manifold Block', 'valves', blk, explode=(0, -0.3, 0.3), ref='hp_relief', section='keep')
    flt = join('flt', [cyl('rf', 0.05, 0.6, 0.78, 'paint_red', 24, center=(0.38, 0.18, 0)), cyl('br', 0.035, 0.6, 0.7, 'chrome', 16, center=(-0.38, 0.18, 0)),
                       box('lg', (0.03, 0.02, 0.2), (0.45, -0.31, 0.38), 'glass')])
    P(m, 'filter_breather', 'Return Filter, Filler-Breather & Level/Temperature Gauge', 'conditioning', flt, explode=(0, 0, 0.4), ref='hp_filter', section='keep')
    cl = join('cl', [box('cc', (0.08, 0.3, 0.3), (0.62, 0, 0.4), 'aluminium'), cyl('cfs', 0.13, 0.66, 0.7, 'paint_grey', 32, axis='X', center=(0, 0, 0.4), r_in=0.12),
                     cyl('cfm', 0.05, 0.7, 0.8, 'paint_motor', 24, axis='X', center=(0, 0, 0.4))])
    P(m, 'cooler', 'Air-Blast Oil Cooler (core, fan shroud, fan motor)', 'conditioning', cl, explode=(0.4, 0, 0), ref='hp_cooler', section='keep')
    fan = join('fan', [cyl('fh', 0.025, 0.67, 0.69, 'steel', 16, axis='X', center=(0, 0, 0.4))] +
               [rotate(box(f'fb{k}', (0.012, 0.035, 0.1), (0.68, 0, 0.4 + 0.065), 'aluminium'), TAU * k / 5, 'X', (0.68, 0, 0.4)) for k in range(5)])
    pfn = P(m, 'cooler_fan', 'Cooler Fan', 'conditioning', fan, explode=(0.6, 0, 0), ref='hp_cooler', section='keep', pivot=(0.68, 0, 0.4))
    pfn.spin('X', 5)
    acc = cyl('ac', 0.07, 0.6, 1.1, 'paint_red', 24, center=(0.35, -0.2, 0), ch=0.03)
    P(m, 'accumulator', 'Accumulator', 'storage', acc, explode=(0.2, -0.3, 0.3), ref='hp_accumulator', section='keep')
    m.flow('suction', [(-0.2, 0.05, 0.16), (-0.2, 0.05, 0.5)], 'hydraulic_oil', 0.01, 0.15)
    m.flow('pressure_line', [(-0.2, 0.05, 0.5), (-0.1, 0.05, 0.66), (0.25, 0.05, 0.66), (0.3, 0.05, 0.8), (0.8, 0.05, 0.8)], 'flow_discharge', 0.01, 0.15)
    m.flow('return_line', [(0.8, 0.15, 0.7), (0.38, 0.18, 0.78), (0.38, 0.18, 0.55), (0.38, 0.15, 0.2)], 'flow_suction', 0.01, 0.15)
    _press_tubes(m, [([(-0.2, -0.12, 0.16), (-0.2, -0.12, 0.5)], 0), ([(-0.12, -0.12, 0.62), (0.25, -0.12, 0.62), (0.25, -0.12, 0.85), (0.8, -0.12, 0.85)], 8),
                     ([(0.8, 0.26, 0.72), (0.38, 0.26, 0.78), (0.38, 0.26, 0.2)], 2)],
                 'Pressure levels in the HPU circuit', 'Blue = suction (slightly below atmospheric at the pump inlet — keep it short and generous). Red = pressure line, '
                 'limited by the relief valve setting (system pressure is set by the load; the relief valve caps it). Green-blue = return line, a few bar back-pressure through the return filter.', r=0.01)
    m.annotate('pressure', 'Pump inlet: ≈ atmospheric or slightly below', (-0.2, -0.12, 0.3))
    m.annotate('pressure', 'Pressure line: up to the relief-valve setting', (0.5, -0.12, 0.9))
    m.annotate('pressure', 'Return line: low pressure (filter Δp)', (0.6, 0.26, 0.75))
    return m.export(out)


def hydraulic_cylinder(out):
    m = _model('hydraulic_cylinder', 'Double-Acting Hydraulic Cylinder (Tie-Rod / Welded)')
    CZ, X0, X1, R = 0.3, -0.5, 0.4, 0.06
    stroke = lambda t: 0.38 * smooth_pulse(t, 0.35, 0.15, 0.35)
    bar = csg('bar', [cyl('bo', R + 0.012, X0, X1, 'paint_red', 48, axis='X', center=(0, 0, CZ))], [cyl('bi', R, X0 - 0.01, X1 + 0.01, 'paint_red', 48, axis='X', center=(0, 0, CZ))], 'paint_red')
    P(m, 'barrel', 'Barrel (honed tube)', 'casing', bar, explode=(0, 0.3, 0), ref='hc_barrel')
    caps = [csg('cap', [cyl('cp', R + 0.03, X0 - 0.06, X0, 'steel', 48, axis='X', center=(0, 0, CZ)), cyl('cle', 0.03, -0.04, 0.04, 'steel', 24, axis='Y', center=(X0 - 0.09, 0, CZ))], [], 'steel') if False else
            join('cap', [cyl('cp', R + 0.03, X0 - 0.06, X0, 'steel', 48, axis='X', center=(0, 0, CZ)), cyl('cle', 0.035, -0.04, 0.04, 'steel', 24, axis='Y', center=(X0 - 0.1, 0, CZ)),
                         box('cl2', (0.07, 0.08, 0.07), (X0 - 0.08, 0, CZ), 'steel')]),
            csg('gl', [cyl('go', R + 0.03, X1, X1 + 0.07, 'steel', 48, axis='X', center=(0, 0, CZ))], [cyl('gi', 0.031, X1 - 0.01, X1 + 0.08, 'steel', 32, axis='X', center=(0, 0, CZ))], 'steel')]
    seals = [cyl('rs', 0.042, X1 + 0.02, X1 + 0.05, 'rubber', 32, axis='X', center=(0, 0, CZ), r_in=0.0305)]
    P(m, 'end_caps', 'Cap End (clevis mount) & Rod-End Gland with Rod Seals / Wiper', 'casing', caps + seals, explode=(0, 0, 0.3), ref='hc_caps')
    pr = join('pr', [cyl('pi', R - 0.001, X0 + 0.02, X0 + 0.08, 'steel_dark', 48, axis='X', center=(0, 0, CZ)), cyl('ps', R, X0 + 0.04, X0 + 0.06, 'rubber', 48, axis='X', center=(0, 0, CZ)),
                     cyl('rd', 0.03, X0 + 0.08, X1 + 0.35, 'chrome', 32, axis='X', center=(0, 0, CZ)), cyl('re', 0.04, X1 + 0.3, X1 + 0.4, 'steel', 24, axis='X', center=(0, 0, CZ))])
    pp = P(m, 'piston_rod', 'Piston (with seals) & Chrome-Plated Rod', 'rotating_element', pr, explode=(0.3, -0.3, 0), ref='hc_piston', section='split')
    keys_loop(m, pp, lambda t: (stroke(t), 0, 0))
    ports = [nozzle('pa', (X0 + 0.03, 0, CZ + R + 0.012), (0, 0, 1), 0.012, 0.06), nozzle('pb', (X1 - 0.03, 0, CZ + R + 0.012), (0, 0, 1), 0.012, 0.06)]
    P(m, 'ports', 'Ports A (cap end) & B (rod end)', 'nozzles', ports, explode=(0, 0, 0.3), ref='hc_ports', section='keep')
    # cap-end chamber: from the cap face (X0) to the piston face (X0 + 0.02 + stroke); node at X0 so x-scale stretches it
    oilA = cyl('oa', R - 0.001, X0, X0 + 0.02, 'hydraulic_oil', 48, axis='X', center=(0, 0, CZ))
    pa = P(m, 'oil_cap_side', 'Oil in Cap-End Chamber (fills on extend)', 'fluid', half(oilA, 'hydraulic_oil'), explode=(0, -0.3, 0), ref='hc_oil', section='keep', pivot=(X0, 0, CZ))
    keys_loop(m, pa, lambda t: (1 + stroke(t) / 0.02, 1, 1), 'scale')
    # rod-end annulus: from the piston back face (X0 + 0.08 + stroke) to the gland (X1); node at X1
    oilB = cyl('ob', R - 0.001, X0 + 0.08, X1, 'hydraulic_oil', 48, axis='X', center=(0, 0, CZ), r_in=0.0305)
    pb_ = P(m, 'oil_rod_side', 'Oil in Rod-End (annulus) Chamber (fills on retract)', 'fluid', half(oilB, 'hydraulic_oil'), explode=(0, -0.3, -0.1), ref='hc_oil', section='keep', pivot=(X1, 0, CZ))
    keys_loop(m, pb_, lambda t: (max(0.02, (X1 - X0 - 0.08 - stroke(t)) / (X1 - X0 - 0.08)), 1, 1), 'scale')
    m.flow('extend', [(X0 + 0.03, 0, CZ + R + 0.1), (X0 + 0.03, 0, CZ + 0.02), (X0 + 0.02, 0, CZ)], 'hydraulic_oil', 0.008, 0.08, active=[(0.0, 0.35)])
    m.flow('retract', [(X1 - 0.03, 0, CZ + R + 0.1), (X1 - 0.03, 0, CZ + 0.04), (X1 - 0.05, 0, CZ + 0.04)], 'hydraulic_oil', 0.008, 0.08, active=[(0.5, 0.85)])
    bands = [cyl('pbA', R + 0.022, X0 + 0.005, X0 + 0.2, 'pressure_8', 48, axis='X', center=(0, 0, CZ), r_in=R + 0.014),
             cyl('pbB', R + 0.022, X0 + 0.25, X1 - 0.005, 'pressure_1', 48, axis='X', center=(0, 0, CZ), r_in=R + 0.014)]
    m.overlay('pressure', join('bands', bands), 'Pressure while extending',
              'Extending: port A feeds the cap end (red, system pressure) and port B returns oil from the rod end (blue, low). Push force F = p × A_bore. '
              'Retracting reverses the ports: the pull force is p × (A_bore − A_rod), smaller, but the rod moves faster for the same pump flow because the annulus volume is smaller.', split=True)
    m.annotate('pressure', 'Cap end: F_extend = p · π D²/4', (X0 + 0.05, 0, CZ - R - 0.12))
    m.annotate('pressure', 'Rod end (annulus): F_retract = p · π (D² − d²)/4', (X1 - 0.05, 0, CZ + R + 0.14))
    return m.export(out)


def hydraulic_accumulator(out):
    m = _model('hydraulic_accumulator', 'Bladder-Type Hydraulic Accumulator')
    R, L, Z0 = 0.12, 0.5, 0.25
    sh = vessel('sh', R, L, 0.012, 'paint_red', heads=('hemi', 'hemi'), z0=Z0)
    P(m, 'shell', 'Forged Steel Shell (pressure vessel)', 'vessel', sh, explode=(0, 0.3, 0), ref='ha_shell')
    bl = lathe('bl', [(0.0, Z0 + 0.05), (R * 0.75, Z0 + 0.12), (R * 0.85, Z0 + L * 0.6), (R * 0.75, Z0 + L + 0.05), (0.0, Z0 + L + R * 0.8)], 'rubber', 48, a0=0.0, a1=math.pi, cap_mat='rubber')
    pb = P(m, 'bladder', 'Elastomer Bladder pre-charged with Nitrogen', 'bladder', bl, explode=(0, -0.3, 0.3), ref='ha_bladder', section='keep')
    for mesh in pb.meshes:
        local_pivot(mesh, (0, 0, Z0 + L + R * 0.8))
        m.keyframes(mesh, 'Operate', 'scale', [(1 + f, (1 - 0.35 * smooth_pulse(f / OPERATE_FRAMES, 0.3, 0.2, 0.3), 1 - 0.35 * smooth_pulse(f / OPERATE_FRAMES, 0.3, 0.2, 0.3),
                                                         1 - 0.45 * smooth_pulse(f / OPERATE_FRAMES, 0.3, 0.2, 0.3))) for f in range(OPERATE_FRAMES + 1)])
    gv = join('gv', [cyl('gvb', 0.02, Z0 + L + R - 0.01, Z0 + L + R + 0.06, 'brass', 16), cyl('gvc', 0.025, Z0 + L + R + 0.06, Z0 + L + R + 0.09, 'steel_dark', 16)])
    P(m, 'gas_valve', 'Gas (Nitrogen) Charging Valve', 'valves', gv, explode=(0, 0, 0.3), ref='ha_gas_valve', section='keep')
    pv = join('pv', [cyl('pvb', 0.04, Z0 - R - 0.02, Z0 - R + 0.04, 'steel', 24), cyl('pvp', 0.03, Z0 - R + 0.04, Z0 - R + 0.06, 'steel_dark', 24)])
    P(m, 'oil_port', 'Oil Port with Anti-Extrusion Poppet Valve', 'valves', pv, explode=(0, 0, -0.3), ref='ha_poppet', section='keep')
    oil = csg('oil', [vessel('ov', R - 0.013, L, R - 0.014, 'hydraulic_oil', heads=('hemi', 'hemi'), z0=Z0)], [], 'hydraulic_oil') if False else \
        lathe('oil', [(0.0, Z0 - R + 0.015), (R - 0.013, Z0), (R - 0.013, Z0 + 0.12), (0.0, Z0 + 0.12)], 'hydraulic_oil', 48, a0=0.0, a1=math.pi, cap_mat='hydraulic_oil')
    po = P(m, 'oil', 'Hydraulic Oil (enters as the system pressure rises)', 'fluid', oil, explode=(0, -0.3, -0.2), ref='ha_oil', section='keep')
    from pumpforge.vesselkit import animate_level
    animate_level(m, po, Z0 + 0.06, 0.25, lambda t: smooth_pulse(t, 0.3, 0.2, 0.3))
    bk = [cyl('bk', R + 0.03, Z0 + 0.08, Z0 + 0.12, 'steel', 48, r_in=R + 0.012), box('bp', (0.4, 0.4, 0.03), (0, 0, 0.015), 'paint_grey'),
          cyl('pl', 0.015, 0.0, Z0 - R - 0.02, 'steel', 12, center=(0.0, 0.0, 0))] + \
         [box(f'bkl{s}', (0.03, 0.04, Z0 + 0.1), (s * (R + 0.04), 0, (Z0 + 0.1) / 2 + 0.015), 'steel') for s in (-1, 1)]
    P(m, 'mounting', 'Mounting Clamp & Base', 'structure', bk, explode=(0, 0, -0.3), ref='ha_mount', section='keep')
    m.flow('oil_in_out', [(0.3, 0, 0.05), (0.0, 0, 0.05), (0, 0, Z0 - R + 0.04), (0, 0, Z0 + 0.05)], 'hydraulic_oil', 0.008, 0.1)
    bands = [cyl('pg', R + 0.03, Z0 + 0.14, Z0 + L, 'pressure_6', 48, r_in=R + 0.022), cyl('po', R + 0.03, Z0 - 0.02, Z0 + 0.06, 'pressure_6', 48, r_in=R + 0.022)]
    m.overlay('pressure', join('bands', bands), 'Gas and oil at the same pressure',
              'The bladder separates nitrogen from oil but transmits pressure, so gas and oil are always at the same pressure. Before any oil enters, the gas is at the pre-charge '
              'pressure p₀ (bladder type: typically about 90 % of the minimum system pressure). Oil enters as the system pressure rises, compressing the gas (p·V = constant for slow, '
              'isothermal changes; p·V^1.4 for fast, adiabatic ones). The usable oil volume is the gas volume change between maximum and minimum system pressure.', split=True)
    m.annotate('pressure', 'N₂ pre-charge p₀ ≈ 0.9 × p_min (bladder, rule of thumb)', (0, 0, Z0 + L + R + 0.12))
    m.annotate('pressure', 'ΔV = V₁ − V₂ between p_min and p_max', (R + 0.05, 0, Z0 + 0.02))
    return m.export(out)


def hydraulic_control_valve_assembly(out):
    m = _model('hydraulic_control_valve_assembly', 'Hydraulic Control Valve Assembly (Manifold with Directional, Pressure & Flow Valves)')
    CZ = 0.4
    mf = csg('mf', [box('mb', (0.6, 0.3, 0.12), (0, 0, CZ), 'aluminium', bevel=0.004)],
             [cyl('gP', 0.012, -0.32, 0.32, 'aluminium', 16, axis='X', center=(0, -0.05, CZ)), cyl('gT', 0.012, -0.32, 0.32, 'aluminium', 16, axis='X', center=(0, 0.05, CZ))], 'aluminium')
    P(m, 'manifold', 'Manifold Block (P and T galleries drilled through)', 'manifold', mf, explode=(0, 0, -0.3), ref='hv_manifold')
    for i, x in enumerate((-0.15, 0.12)):
        body = box(f'db{i}', (0.2, 0.12, 0.1), (x, 0, CZ + 0.11), 'paint_grey', bevel=0.004)
        sol = [box(f'so{i}{s}', (0.06, 0.07, 0.07), (x + s * 0.13, 0, CZ + 0.11), 'thermoplastic', bevel=0.004) for s in (-1, 1)]
        P(m, f'directional_valve_{i + 1}', f'4/3 Solenoid Directional Valve {i + 1} (CETOP)', 'valves', [body] + sol, explode=(0, 0, 0.4 + 0.1 * i), ref='hv_directional', section='keep')
        spool = cyl(f'sp{i}', 0.012, x - 0.12, x + 0.12, 'chrome', 16, axis='X', center=(0, 0, CZ + 0.11))
        ps = P(m, f'spool_{i + 1}', f'Spool {i + 1}', 'valves', spool, explode=(0, -0.3, 0.4), ref='hv_directional', section='keep')
        keys_loop(m, ps, lambda t, i=i: (0.025 * math.sin(TAU * t + i * math.pi), 0, 0))
    rv = join('rv', [cyl('rvb', 0.03, CZ + 0.06, CZ + 0.18, 'brass', 24, center=(0.24, 0.08, 0)), hex_prism('rvn', 0.05, CZ + 0.18, CZ + 0.21, 'steel', center=(0.24, 0.08, 0)),
                     cyl('rva', 0.008, CZ + 0.21, CZ + 0.27, 'steel', 8, center=(0.24, 0.08, 0))])
    P(m, 'relief_valve', 'Pressure Relief Valve (cartridge, adjustable)', 'valves', rv, explode=(0.3, 0, 0.3), ref='hv_relief', section='keep')
    fc = join('fc', [cyl('fcb', 0.02, CZ + 0.06, CZ + 0.15, 'chrome', 16, center=(-0.26, -0.08, 0)), cyl('fck', 0.03, CZ + 0.15, CZ + 0.18, 'paint_blue', 16, center=(-0.26, -0.08, 0))])
    P(m, 'flow_control', 'Flow Control (throttle-check) Valve', 'valves', fc, explode=(-0.3, 0, 0.3), ref='hv_flow', section='keep')
    gp = [pressure_gauge('g1', (0.0, 0.15, CZ + 0.02), r=0.04, facing=(0, 1, 0))]
    P(m, 'gauge', 'Pressure Gauge (test point)', 'instrument', gp, explode=(0, 0.3, 0.2), ref='hv_gauge', section='keep')
    ports = [nozzle(f'pt{i}', (x, -0.15, CZ), (0, -1, 0), 0.012, 0.06) for i, x in enumerate((-0.22, -0.08, 0.06, 0.2))]
    P(m, 'work_ports', 'Work Ports A1 B1 A2 B2 to Actuators', 'nozzles', ports, explode=(0, -0.3, 0), ref='hv_ports', section='keep')
    m.flow('P_to_A', [(-0.35, -0.05, CZ), (-0.15, -0.05, CZ), (-0.15, 0, CZ + 0.1), (-0.22, -0.05, CZ + 0.02), (-0.22, -0.2, CZ)], 'flow_discharge', 0.007, 0.08, active=[(0.0, 0.5)])
    m.flow('B_to_T', [(-0.08, -0.2, CZ), (-0.08, 0.0, CZ + 0.05), (-0.08, 0.05, CZ), (0.35, 0.05, CZ)], 'flow_suction', 0.007, 0.08, active=[(0.0, 0.5)])
    m.flow('relief', [(0.24, -0.05, CZ), (0.24, 0.08, CZ + 0.12), (0.24, 0.05, CZ), (0.35, 0.05, CZ)], 'hydraulic_oil', 0.006, 0.06, active=[(0.5, 1.0)])
    _press_tubes(m, [([(-0.36, -0.05, CZ), (0.3, -0.05, CZ)], 8), ([(-0.36, 0.05, CZ), (0.36, 0.05, CZ)], 1)],
                 'P gallery vs T gallery', 'The pressure gallery P (red) carries pump flow at system pressure to every valve station; the tank gallery T (blue) collects return oil at low '
                 'pressure. Each directional valve connects P and T to its work ports A and B; the relief valve limits the pressure in P.', r=0.009)
    m.annotate('pressure', 'P: system pressure', (-0.3, -0.05, CZ + 0.1))
    m.annotate('pressure', 'T: tank (low) pressure', (0.3, 0.1, CZ + 0.1))
    return m.export(out)


# =============================================================== EQ-226 Vibrating conveyor
def vibrating_conveyor(out):
    m = _model('vibrating_conveyor', 'Vibrating (Oscillating) Conveyor — Leaf-Spring Rocker Type with Crank Drive')
    Z, L, W = 0.7, 3.0, 0.4
    tr = [box('tb', (L, W, 0.01), (0, 0, Z), 'stainless'), box('tl', (L, 0.01, 0.15), (0, -W / 2, Z + 0.07), 'stainless'), box('tr', (L, 0.01, 0.15), (0, W / 2, Z + 0.07), 'stainless')]
    amp, ang = 0.015, math.radians(25)
    tr += [box(f'tbk{k}{s}', (0.06, 0.08, 0.05), (x - 0.4 * math.sin(ang), s * (W / 2 + 0.04), Z - 0.02), 'stainless') for k, x in enumerate((-1.2, -0.4, 0.4, 1.2)) for s in (-1, 1)]
    ptr = P(m, 'trough', 'Conveying Trough with Spring Brackets', 'vibrating', tr, explode=(0, 0, 0.4), ref='vc_trough', section='split')
    osc = lambda t: math.sin(TAU * 5 * t)
    keys_loop(m, ptr, lambda t: (amp * math.cos(ang) * osc(t), 0, amp * math.sin(ang) * osc(t)))
    pr = m.part('rockers', 'Inclined Leaf-Spring Rockers (guide the trough at 25°)', 'support', explode=(0, 0, -0.2), info={'ref': 'vc_springs'})
    for k, x in enumerate((-1.2, -0.4, 0.4, 1.2)):
        for s in (-1, 1):
            leaf = box(f'lf{k}{s}', (0.02, 0.05, 0.4), (x, s * (W / 2 + 0.04), Z - 0.2), 'steel')
            leaf = rotate(leaf, -ang, 'Y', (x, 0, Z - 0.4))
            ms = pr.add(leaf, smooth_angle=30)
            local_pivot(ms, (x, s * (W / 2 + 0.04), Z - 0.4))
            m.keyframes(ms, 'Operate', 'rotation_euler', [(1 + f, (0, amp / 0.4 * osc(f / OPERATE_FRAMES), 0)) for f in range(OPERATE_FRAMES + 1)])
    base = [box('bb', (L, 0.2, 0.08), (0, 0, Z - 0.44), 'paint_grey')] + [box(f'bx{k}', (0.08, W + 0.2, 0.06), (x, 0, Z - 0.43), 'paint_grey') for k, x in enumerate((-1.2, -0.4, 0.4, 1.2))] + [box(f'bl{i}', (0.08, 0.2, Z - 0.48), (x, 0, (Z - 0.48) / 2), 'paint_grey') for i, x in enumerate((-1.3, 1.3))]
    P(m, 'base_frame', 'Base Frame', 'structure', base, explode=(0, 0, -0.3), ref='vc_base', section='keep')
    crank = join('ck', [cyl('ckd', 0.08, -0.25, -0.2, 'steel', 32, axis='Y', center=(-1.6, 0, Z - 0.3)), cyl('ckp', 0.015, -0.27, -0.2, 'steel', 12, axis='Y', center=(-1.6 + 0.015, 0, Z - 0.3))])
    pc = P(m, 'eccentric_drive', 'Eccentric (crank) Drive & Connecting Arm', 'drive', crank, explode=(-0.3, -0.3, 0), ref='vc_drive', section='keep', pivot=(-1.6, 0, Z - 0.3))
    pc.spin('Y', 5)
    arm = beam('arm', (-1.6, -0.22, Z - 0.3), (-L / 2, -0.22, Z - 0.02), w=0.03, h=0.03)
    pa = P(m, 'connecting_arm', 'Connecting Arm (with rubber bush)', 'drive', arm, explode=(-0.3, -0.3, 0.2), ref='vc_drive', section='keep')
    keys_loop(m, pa, lambda t: (amp * math.cos(ang) * osc(t), 0, amp * math.sin(ang) * osc(t)))
    mt = join('mt', [box('mb', (0.3, 0.3, 0.2), (-1.9, 0, Z - 0.35), 'paint_blue', bevel=0.02)])
    P(m, 'motor', 'Motor & V-Belt to Eccentric Shaft', 'drive', mt, explode=(-0.4, 0, 0), ref='vc_drive', section='keep')
    rocks_along(m, 'parts', 'Material Hopping Forward with Each Stroke', [(-L / 2 + 0.1, Z + 0.04), (L / 2, Z + 0.04), (L / 2 + 0.2, Z - 0.4)], 16, r=0.04, y=0.05)
    m.flow('material', [(-L / 2 + 0.1, 0, Z + 0.05), (L / 2, 0, Z + 0.05), (L / 2 + 0.2, 0, Z - 0.4)], 'flow_discharge', 0.014, 0.3)
    return m.export(out)


# ===================================================================== metadata
def _std(*items):
    return [{'id': i, 'title': t, 'relevance': r, 'edition': 'to be verified'} for i, t, r in items]


def _c(fn, cons, mat, op='—', fm=('—',), insp=('Visual',)):
    return C(fn, cons, mat, op, list(fm), list(insp))


_BULK = _std(('ISO 5049-1', 'Mobile equipment for continuous handling of bulk materials — Rules for the design of steel structures', 'Stackers/reclaimers.'),
             ('FEM 2.131/2.132', 'Rules for the design of mobile equipment for continuous handling of bulk materials', 'Design rules.'))
_CRANE = _std(('ISO 4301 / FEM 1.001', 'Cranes — Classification / Rules for the design of hoisting appliances', 'Duty classification.'),
              ('ISO 9927', 'Cranes — Inspections', 'Inspection.'), ('ASME B30 series', 'Cranes, hoists and rigging safety', 'US practice.'))
_HYD = _std(('ISO 4413', 'Hydraulic fluid power — General rules and safety requirements', 'System safety.'), ('ISO 4406', 'Hydraulic fluid power — Fluids — Contamination code', 'Cleanliness.'))
_BOOM = {'sr_portal': _c('Carries the machine along the rails.', 'Portal frame with powered bogies.', 'Steel.', 'Rail clamps against storm wind.', ['Wheel/rail wear'], ['Inspect']),
         'sr_boom': _c('Slews/luffs the boom conveyor over the stockpile; houses machinery and counterweight.', 'Superstructure, boom, belt, counterweight.', 'Steel.', 'Balance by counterweight.', ['Structural cracks'], ['NDT of welds']),
         'sr_wheel': _c('Digs material from the pile/face and drops it on the boom conveyor.', 'Bucket wheel with buckets and drive.', 'Steel; wear teeth/lips.', '—', ['Bucket/teeth wear'], ['Replace teeth']),
         'hm_rails': _c('Track for travel.', 'Rails on sleepers.', 'Steel.'), 'hm_pile': _c('Stockpile / face.', '—', '—'), 'hk_belt': _c('Belt.', '—', 'Rubber.'),
         'bw_crawler': _c('Moves the machine on soft ground.', 'Crawler tracks with track shoes.', 'Steel.', 'Low ground pressure.', ['Shoe wear'], ['Inspect']),
         'bw_base': _c('Lower structure and slew ring.', '—', 'Steel.'), 'bw_discharge': _c('Discharges to conveyors.', 'Discharge boom conveyor.', 'Steel.')}

META = {
    'stacker': {'summary': ('A stacker builds stockpiles of bulk material (coal, ore, limestone). It travels on rails alongside the yard conveyor; a tripper lifts material off that conveyor onto the '
                            'boom conveyor, which slews and luffs to place it on the pile in layers (chevron or windrow stacking).'),
                'classification': {'family': 'Bulk handling machine', 'type': 'Rail-mounted slewing/luffing boom stacker'}, 'model_configuration': {'animation': 'Travels and slews; coal discharged at boom tip'},
                'standards': _BULK, 'references': ['Bulk material handling by conveyor belt (SME)'], 'components': _BOOM},
    'reclaimer': {'summary': ('A bucket wheel reclaimer recovers material from stockpiles. The rotating bucket wheel at the end of the slewing boom digs into the pile face and drops material onto the '
                              'boom conveyor, which carries it back to the yard conveyor as the machine slews from side to side and advances.'),
                  'classification': {'family': 'Bulk handling machine', 'type': 'Boom-type bucket wheel reclaimer'}, 'model_configuration': {'animation': 'Wheel turns, boom slews across the pile'},
                  'standards': _BULK, 'references': ['Bulk material handling notes'], 'components': _BOOM},
    'stacker_reclaimer': {'summary': ('A stacker-reclaimer combines both jobs in one machine. Its boom conveyor is reversible: in stacking mode it carries material out to the boom tip; in reclaiming mode '
                                      'the bucket wheel digs material and the belt brings it back to the yard conveyor.'),
                          'classification': {'family': 'Bulk handling machine', 'type': 'Bucket wheel stacker-reclaimer'}, 'model_configuration': {'animation': 'Reclaiming with wheel; stacking flow also shown'},
                          'standards': _BULK, 'references': ['Bulk material handling notes'], 'components': _BOOM},
    'bucket_wheel_excavator': {'summary': ('A bucket wheel excavator (BWE) is a giant continuous mining machine. Buckets on the rotating wheel cut material from the bench as the boom slews; the material '
                                           'drops onto belt conveyors in the boom and leaves via the discharge boom to the mine conveyor system. Crawlers move the machine.'),
                               'classification': {'family': 'Heavy mining machinery', 'type': 'Compact crawler bucket wheel excavator'}, 'model_configuration': {'animation': 'Wheel digs, boom slews, crawler tracks move'},
                               'standards': _BULK, 'references': ['Surface mining equipment handbooks'], 'components': _BOOM},
    'tripper_conveyor': {'summary': ('A tripper is a travelling car on a belt conveyor that lifts the belt over a pulley and discharges material through a chute to either side. Moving the tripper along '
                                     'the rails lets one conveyor fill a row of bunkers or silos.'),
                         'classification': {'family': 'Conveyor accessory', 'type': 'Motorised travelling tripper'}, 'model_configuration': {'animation': 'Tripper travels; coal drops into bunkers'},
                         'standards': _std(('CEMA', 'Belt Conveyors for Bulk Materials', 'Design.'), ('ISO 5048', 'Belt conveyors — calculation of power and tensile forces', 'Calculation.')),
                         'references': ['CEMA Belt Conveyors for Bulk Materials'],
                         'components': {'tc_tripper': _c('Lifts the belt and discharges material.', 'Car with ramp, pulleys, chute and wheels.', 'Steel.', '—', ['Belt mistracking'], ['Alignment']),
                                        'tc_bunkers': _c('Receive material.', 'Bunkers/silos.', 'Steel/concrete.'), 'hm_rails': _c('Rails.', '—', 'Steel.'),
                                        'hk_belt': _c('Carries material.', 'Belt.', 'Rubber.'), 'hk_pulley': _c('Pulleys.', '—', 'Steel.'), 'hk_idlers': _c('Idlers/frame.', '—', 'Steel.')}},
    'shuttle_conveyor': {'summary': ('A shuttle conveyor is a short reversible belt conveyor on a travelling carriage. By running the belt in either direction and moving the carriage, it distributes '
                                     'material from a fixed feed point into many bins on both sides.'),
                         'classification': {'family': 'Conveyor', 'type': 'Reversible shuttle conveyor'}, 'model_configuration': {'animation': 'Carriage shuttles; belt runs one way then reverses; lumps discharge at the active end'},
                         'standards': _std(('CEMA', 'Belt Conveyors for Bulk Materials', 'Design.'),), 'references': ['CEMA'],
                         'components': {'shc_carriage': _c('Carries the conveyor along the rails.', 'Carriage with wheels and travel drive.', 'Steel.'), 'shc_bins': _c('Rails and bins.', '—', 'Steel.'),
                                        'shc_feed': _c('Fixed feed point.', 'Chute.', 'Steel.'), 'hk_belt': _c('Belt.', '—', 'Rubber.'), 'hk_pulley': _c('Pulleys.', '—', 'Steel.'), 'hk_idlers': _c('Idlers.', '—', 'Steel.')}},
    'drag_chain_conveyor': {'summary': ('A drag chain (en-masse) conveyor moves bulk solids inside an enclosed casing. A chain with flights drags the material bed along the bottom; because the material moves '
                                        'as a mass with the chain, it is gentle, dust-tight and can convey horizontally, inclined or around bends.'),
                            'classification': {'family': 'Conveyor', 'type': 'En-masse drag chain conveyor'}, 'model_configuration': {'animation': 'Flighted chain drags material'},
                            'standards': _std(('CEMA', 'Bulk handling conveyors', 'Practice.'),), 'references': ['Manufacturer en-masse conveyor guides'],
                            'components': {'dc_casing': _c('Encloses the chain and material.', 'Casing with liners.', 'Steel.'), 'dc_chain': _c('Drags the material.', 'Forged chain with flights.', 'Alloy steel.', '—', ['Wear, elongation'], ['Measure']),
                                           'dc_sprocket': _c('Drive and take-up.', 'Sprockets.', 'Steel.'), 'dc_drive': _c('Drive.', 'Gearmotor.', '—')}},
    'pneumatic_conveying_system': {'summary': ('A pneumatic conveying system moves powders and granules through a pipeline using air. In this dilute-phase pressure system a blower supplies air, a rotary '
                                               'airlock feeds solids into the line, the particles are carried in suspension, and a receiver with bag filter separates them into the silo.'),
                                   'classification': {'family': 'Bulk handling system', 'type': 'Dilute-phase positive-pressure conveying'}, 'model_configuration': {'animation': 'Particles carried along the pipeline'},
                                   'standards': _std(('NFPA 652/654', 'Combustible dust', 'Explosion protection.'),), 'references': ['Mills, Pneumatic Conveying Design Guide'],
                                   'components': {'pc_blower': _c('Supplies conveying air.', 'Roots blower with silencer.', '—'), 'pc_feeder': _c('Feeds solids into the line against pressure.', 'Hopper and rotary airlock.', '—'),
                                                  'pc_pipeline': _c('Carries the air–solids mixture.', 'Pipe with long-radius bends.', 'Stainless/steel.', 'Velocity ~ 15–25 m/s (dilute).', ['Bend erosion'], ['Thickness check']),
                                                  'pc_receiver': _c('Separates solids from air.', 'Receiver with bag filter.', '—'), 'pc_silo': _c('Stores the conveyed material.', 'Silo.', 'Steel.')}},
    'screw_jack': {'summary': ('A screw jack lifts loads precisely. A motor turns the worm, which turns a bronze worm wheel; the wheel acts as a nut on the lifting screw, so the screw moves up or down. '
                               'The high reduction makes it self-locking in many designs, holding the load without a brake.'),
                   'classification': {'family': 'Lifting equipment', 'type': 'Worm-gear screw jack, translating screw'}, 'model_configuration': {'animation': 'Worm turns, screw and load rise then lower'},
                   'standards': _std(('Manufacturer ratings', 'Screw jack load/duty charts', 'Duty cycle and column buckling.'),), 'references': ['Screw jack selection guides'],
                   'components': {'sj_housing': _c('Holds the gearing.', 'Cast housing.', 'Cast iron/aluminium.'), 'sj_worm': _c('Input; drives the wheel.', 'Hardened worm shaft.', 'Steel.'),
                                  'sj_wheel': _c('Turns and drives the screw (as a nut).', 'Bronze worm wheel.', 'Bronze.', '—', ['Wear'], ['Backlash']), 'sj_screw': _c('Lifts the load.', 'Acme/trapezoidal screw.', 'Steel.'),
                                  'sj_load': _c('Load.', '—', '—')}},
    'gantry_crane': {'summary': ('A gantry crane is an overhead crane supported on legs that run on ground rails. The trolley (crab) runs along the girders and its hoist raises and lowers the hook; the '
                                 'whole gantry travels along the runway. Used in yards, ports and workshops.'),
                     'classification': {'family': 'Crane', 'type': 'Double-girder rail-mounted gantry crane'}, 'model_configuration': {'animation': 'Gantry travels, trolley traverses, hook lifts'},
                     'standards': _CRANE, 'references': ['FEM 1.001'],
                     'components': {'cr_gantry': _c('Main structure carrying the trolley.', 'Girders, legs, end carriages with wheels.', 'Steel.', 'Duty class per ISO 4301.', ['Fatigue cracks'], ['NDT']),
                                    'cr_hoist': _c('Lifts the load.', 'Trolley, drum, motor, brake, rope, hook.', 'Steel.', 'Rope discard criteria ISO 4309.', ['Rope wear'], ['Rope inspection']),
                                    'cr_controls': _c('Operator control.', 'Cab or radio.', '—'), 'hm_rails': _c('Runway rails.', '—', 'Steel.')}},
    'jib_crane': {'summary': ('A jib crane has a horizontal arm (jib) that slews around a pillar or wall bracket, with a trolley and hoist running along it. It serves a circular work area — ideal for a '
                              'single workstation or machine tool.'),
                  'classification': {'family': 'Crane', 'type': 'Pillar-mounted slewing jib crane'}, 'model_configuration': {'animation': 'Jib slews, trolley moves, hook lifts'},
                  'standards': _CRANE, 'references': ['Crane manufacturer guides'],
                  'components': {'jc_pillar': _c('Supports the jib.', 'Pillar on foundation.', 'Steel.'), 'jc_arm': _c('Carries trolley and load; slews.', 'Jib arm with bearing.', 'Steel.'),
                                 'cr_hoist': _c('Lifts the load.', 'Trolley and electric hoist.', '—')}},
    'monorail_hoist': {'summary': ('A monorail hoist runs on a single I-beam track, which can curve to follow a process route. The trolley carries an electric chain or wire-rope hoist that lifts the '
                                   'load; it moves goods between fixed points such as machines or loading bays.'),
                       'classification': {'family': 'Lifting equipment', 'type': 'Monorail with electric chain hoist'}, 'model_configuration': {'animation': 'Trolley travels; hook lifts'},
                       'standards': _CRANE, 'references': ['Hoist manufacturer guides'],
                       'components': {'mh_track': _c('Guides the trolley.', 'I-beam track and hangers.', 'Steel.'), 'mh_hoist': _c('Lifts and moves the load.', 'Trolley with chain hoist.', '—'),
                                      'mh_pendant': _c('Control.', 'Pendant.', '—')}},
    'electric_winch': {'summary': ('An electric winch pulls or lifts loads by winding wire rope onto a drum. The motor drives the drum through a reduction gearbox; a spring-applied electromagnetic brake '
                                   'holds the load when power is off.'),
                       'classification': {'family': 'Lifting/hauling equipment', 'type': 'Electric drum winch'}, 'model_configuration': {'animation': 'Drum winds rope; load hauled in and paid out'},
                       'standards': _std(('EN 14492-1', 'Cranes — Power driven winches and hoists', 'Safety requirements.'),), 'references': ['EN 14492'],
                       'components': {'ew_drum': _c('Winds the rope.', 'Grooved drum.', 'Steel.'), 'ew_gearbox': _c('Reduces speed, increases torque.', 'Gearbox.', '—'),
                                      'ew_motor': _c('Drive and fail-safe brake.', 'Motor and brake.', '—', 'Brake applied by springs when power fails.', ['Brake wear'], ['Brake test']),
                                      'ew_frame': _c('Frame.', '—', 'Steel.'), 'ew_rope': _c('Transmits the pull.', 'Wire rope.', 'Steel.', '—', ['Broken wires'], ['ISO 4309 inspection']), 'ew_load': _c('Load.', '—', '—')}},
    'hydraulic_power_unit': {'summary': ('A hydraulic power unit (HPU) supplies pressurised oil to hydraulic actuators. A motor drives a pump that draws oil from the reservoir; a relief valve limits '
                                         'pressure, filters keep the oil clean, a cooler removes heat, and the oil returns to the tank after doing work.'),
                             'classification': {'family': 'Hydraulic equipment', 'type': 'Hydraulic power pack'}, 'model_configuration': {'animation': 'Oil flows suction → pressure → return'},
                             'standards': _HYD, 'references': ['Bosch Rexroth hydraulics trainer'],
                             'components': {'hp_reservoir': _c('Stores oil, lets air and dirt settle, dissipates heat.', 'Tank with baffle.', 'Steel.'), 'hp_oil': _c('Hydraulic oil.', '—', 'ISO VG 32/46/68.'),
                                            'hp_pump': _c('Creates flow.', 'Motor, bell housing, pump.', '—'), 'hp_relief': _c('Limits system pressure.', 'Relief, check valve, gauge.', '—', 'Set above working pressure.', ['Set point drift'], ['Test']),
                                            'hp_filter': _c('Keeps oil clean.', 'Return filter, breather, gauges.', '—'), 'hp_cooler': _c('Removes heat.', 'Air-blast cooler.', 'Aluminium.'),
                                            'hp_accumulator': _c('Stores energy, damps pulsation.', 'Accumulator.', '—')}},
    'hydraulic_cylinder': {'summary': ('A double-acting hydraulic cylinder turns oil pressure into straight-line force. Oil into port A pushes the piston and extends the rod; oil into port B retracts '
                                       'it. Force = pressure × area (the rod side has less area, so retract force is lower).'),
                           'classification': {'family': 'Hydraulic actuator', 'type': 'Double-acting cylinder'}, 'model_configuration': {'animation': 'Extends then retracts'},
                           'standards': _HYD + _std(('ISO 6020/6022', 'Hydraulic cylinders — mounting dimensions', 'Dimensions.'),), 'references': ['Cylinder manufacturer guides'],
                           'components': {'hc_barrel': _c('Contains the oil and piston.', 'Honed tube.', 'Steel.'), 'hc_caps': _c('Close the ends; mount; seal the rod.', 'Caps, gland, seals, wiper.', 'Steel, PU/NBR.'),
                                          'hc_piston': _c('Separates chambers and transmits force.', 'Piston with seals and chrome rod.', 'Steel, chrome.', '—', ['Seal leakage', 'Rod scoring'], ['Drift test']),
                                          'hc_ports': _c('Oil connections.', 'Ports.', 'Steel.'), 'hc_oil': _c('Oil.', '—', '—')}},
    'hydraulic_accumulator': {'summary': ('A hydraulic accumulator stores energy in compressed gas. In this bladder type a nitrogen-filled bladder sits inside a steel shell; when system pressure rises, oil '
                                          'enters and squeezes the bladder; when pressure falls, the gas pushes the oil back out. Used for energy storage, pulsation damping and emergency power.'),
                              'classification': {'family': 'Hydraulic equipment', 'type': 'Bladder accumulator'}, 'model_configuration': {'animation': 'Oil enters, bladder compresses, then oil returns'},
                              'standards': _HYD + _std(('PED / ASME VIII', 'Pressure vessel rules', 'Shell certification.'),), 'references': ['HYDAC accumulator guides'],
                              'components': {'ha_shell': _c('Pressure vessel.', 'Forged shell.', 'Steel.'), 'ha_bladder': _c('Separates gas from oil.', 'Elastomer bladder with nitrogen.', 'NBR/ECO.', 'Pre-charge ~ 0.9 × min pressure (typical).', ['Bladder rupture'], ['Pre-charge check']),
                                             'ha_gas_valve': _c('Charges nitrogen.', 'Gas valve.', '—'), 'ha_poppet': _c('Stops the bladder extruding into the port.', 'Poppet valve.', '—'),
                                             'ha_oil': _c('Oil.', '—', '—'), 'ha_mount': _c('Mounting.', '—', 'Steel.')}},
    'hydraulic_control_valve_assembly': {'summary': ('A hydraulic control valve assembly mounts several valves on one manifold block. Directional valves route oil to the actuators (P→A, B→T or P→B, A→T), '
                                                     'a relief valve limits pressure and a flow control sets actuator speed — compact, with fewer leak points than piped valves.'),
                                         'classification': {'family': 'Hydraulic equipment', 'type': 'Manifold with CETOP directional valves'}, 'model_configuration': {'animation': 'Spools shift; flow paths switch'},
                                         'standards': _HYD + _std(('ISO 4401', 'Four-port directional control valves — mounting surfaces', 'CETOP interfaces.'),), 'references': ['Hydraulics trainer manuals'],
                                         'components': {'hv_manifold': _c('Routes oil between valves.', 'Drilled block.', 'Aluminium/steel.'), 'hv_directional': _c('Select flow direction.', 'Solenoid spool valves.', '—', '—', ['Spool sticking'], ['Function test']),
                                                        'hv_relief': _c('Limits pressure.', 'Cartridge relief.', '—'), 'hv_flow': _c('Controls speed.', 'Throttle-check.', '—'), 'hv_gauge': _c('Pressure indication.', 'Gauge.', '—'),
                                                        'hv_ports': _c('Work ports.', '—', '—')}},
    'vibrating_conveyor': {'summary': ('A vibrating conveyor moves material along a trough by oscillating it on inclined springs or rockers. Each forward-upward stroke throws particles slightly ahead; '
                                       'they land further along before the trough returns. Used for hot, abrasive or delicate materials and for feeding, screening and cooling.'),
                           'classification': {'family': 'Conveyor', 'type': 'Leaf-spring rocker conveyor with eccentric drive'}, 'model_configuration': {'animation': 'Trough oscillates; material hops'},
                           'standards': _std(('ISO 12100', 'Safety of machinery', 'Guarding.'),), 'references': ['Vibratory conveyor guides'],
                           'components': {'vc_trough': _c('Carries material.', 'Trough.', 'Stainless/steel.'), 'vc_springs': _c('Guide and store energy.', 'Leaf springs/rockers.', 'Spring steel/FRP.'),
                                          'vc_base': _c('Base frame.', '—', 'Steel.'), 'vc_drive': _c('Creates oscillation.', 'Eccentric drive and arm.', '—')}},
}

BUILDERS = {k: globals()[k] for k in META}
