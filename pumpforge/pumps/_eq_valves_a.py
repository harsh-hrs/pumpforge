"""Valves & Piping — EQ-118 … EQ-125 (needle, pinch, float, foot, solenoid, three-way, four-way, vacuum relief).
Each builder: geometry + named parts + cutaway halves + Explode + Operate animation + flow paths."""
import math
from mathutils import Vector
from pumpforge.core import Model, lathe, cyl, box, csg, split, join, split_many, rotate, transform, hex_prism, TAU, OPERATE_FRAMES
from pumpforge.valvekit import (P, bore_pipe, flange, bolts_x, gasket, handwheel, spring, sphere, keys_loop, smooth_pulse, shape_key,
                                morph_loop, tap)
from pumpforge.parts import pressure_gauge, add_tracers, hollow_pipe
from pumpforge.shapes import sweep_tube
from pumpforge.common_meta import C

CAT = '6 · Valves & Piping'


def _model(pid, title, meta):
    return Model(pid, title, CAT, meta)


# =============================================================== EQ-118 Needle valve
def needle_valve(out):
    m = _model('needle_valve', 'Needle Valve (Bar-Stock, Rising Stem)', META['needle_valve'])
    CZ = 0.12
    body = csg('nv_body', [box('b', (0.1, 0.05, 0.06), (0, 0, CZ), 'stainless', bevel=0.004),
                           hex_prism('bh', 0.05, CZ + 0.03, CZ + 0.05, 'stainless', center=(0, 0, 0))],
               [cyl('in', 0.006, -0.06, 0.0, 'stainless', 24, axis='X', center=(0, 0, CZ - 0.012)),
                cyl('or', 0.0028, CZ - 0.018, CZ + 0.004, 'stainless', 24, center=(0, 0, 0)),
                cyl('ch', 0.008, CZ + 0.004, CZ + 0.06, 'stainless', 32, center=(0, 0, 0)),
                cyl('out', 0.006, 0.0, 0.06, 'stainless', 24, axis='X', center=(0, 0, CZ + 0.014))], 'stainless')
    P(m, 'body', 'Valve Body (Bar Stock) with Seat Orifice', 'body', body, explode=(0, 0, -0.08), ref='nv_body')
    bon = csg('nv_bonnet', [hex_prism('bn', 0.036, CZ + 0.05, CZ + 0.075, 'stainless'),
                            hex_prism('pn', 0.028, CZ + 0.075, CZ + 0.092, 'brass')],
              [cyl('sb', 0.0045, CZ + 0.04, CZ + 0.1, 'stainless', 24)], 'stainless')
    pk = cyl('pack', 0.0085, CZ + 0.062, CZ + 0.074, 'ptfe', 32, r_in=0.0046)
    P(m, 'bonnet', 'Bonnet, Packing & Gland Nut', 'bonnet', [bon, pk], explode=(0, 0, 0.09), ref='nv_bonnet')
    lift = 0.012
    stem = join('nv_stem', [lathe('needle', [(0.0, CZ - 0.016), (0.0034, CZ + 0.004), (0.0045, CZ + 0.008), (0.0045, CZ + 0.15), (0.0, CZ + 0.15)], 'stainless', 32),
                            cyl('thr', 0.0062, CZ + 0.035, CZ + 0.05, 'stainless', 24),
                            cyl('knob', 0.022, CZ + 0.15, CZ + 0.175, 'paint_red', 32, ch=0.003),
                            box('tb', (0.07, 0.008, 0.008), (0, 0, CZ + 0.168), 'paint_red', bevel=0.002)])
    pst = P(m, 'stem', 'Needle Stem & Handle (rising, fine thread)', 'stem', stem, explode=(0, 0, 0.2), ref='nv_stem', section='keep')
    keys_loop(m, pst, lambda t: (0, 0, lift * smooth_pulse(t, 0.25, 0.25, 0.25)))
    keys_loop(m, pst, lambda t: (0, 0, TAU * 3 * smooth_pulse(t, 0.25, 0.25, 0.25)), 'rotation_euler')
    tub = [hollow_pipe('ti', [(-0.2, 0, CZ - 0.012), (-0.05, 0, CZ - 0.012)], 0.006, 'stainless', 24, t=0.0015),
           hollow_pipe('to', [(0.05, 0, CZ + 0.014), (0.2, 0, CZ + 0.014)], 0.006, 'stainless', 24, t=0.0015),
           hex_prism('fi', 0.024, -0.075, -0.05, 'brass', center=(0, 0, CZ - 0.012), axis='X') if False else cyl('fi', 0.013, -0.075, -0.05, 'brass', 6, axis='X', center=(0, 0, CZ - 0.012), r_in=0.0075),
           cyl('fo', 0.013, 0.05, 0.075, 'brass', 6, axis='X', center=(0, 0, CZ + 0.014), r_in=0.0075)]
    P(m, 'tubing', 'Instrument Tubing & Compression Fittings', 'system_piping', tub, explode=(0, -0.08, 0), ref='nv_tubing')
    m.flow('flow', [(-0.22, 0, CZ - 0.012), (-0.002, 0, CZ - 0.012), (0, 0, CZ - 0.004), (0, 0, CZ + 0.008), (0.004, 0, CZ + 0.014), (0.22, 0, CZ + 0.014)],
           'flow_suction', 0.0025, 0.05, speed=[1, 1, 3, 2.5, 1, 1], active=[(0.12, 0.62)])
    return m.export(out)


# =============================================================== EQ-119 Pinch valve
def pinch_valve(out):
    m = _model('pinch_valve', 'Pinch Valve (Enclosed Body, Double-Pinch Mechanism)', META['pinch_valve'])
    CZ, R = 0.35, 0.05
    sl = lathe('sleeve', [(R - 0.006, -0.16), (0.1, -0.16), (0.1, -0.148), (R + 0.006, -0.14), (R + 0.006, 0.14), (0.1, 0.148), (0.1, 0.16),
                          (R - 0.006, 0.16)], 'rubber', 96, axis='X', center=(0, 0, CZ))
    sb, sf = split_many('sleeve', [sl])
    p = m.part('sleeve', 'Elastomer Sleeve (only wetted part)', 'sleeve', section='split', explode=(0, -0.3, 0), info={'ref': 'pv_sleeve'})
    p.add_split(sb, sf, smooth_angle=40)

    def pinch(co, k=0.94):
        f = math.exp(-(co.x / 0.07) ** 2)
        if abs(co.x) > 0.14:
            f = 0.0
        dz = co.z - CZ
        return Vector((co.x, co.y * (1 + 0.35 * f), CZ + dz * (1 - k * f)))
    for mesh in p.meshes:
        shape_key(mesh, 'pinch', pinch)
    cyc = lambda t: smooth_pulse((t + 0.6) % 1.0, 0.2, 0.3, 0.2)       # 1 = closed
    morph_loop(m, p, 'pinch', cyc)
    hous = csg('housing', [cyl('h', 0.1, -0.13, 0.13, 'paint_blue', 96, axis='X', center=(0, 0, CZ)),
                           cyl('f1', 0.12, -0.16, -0.13, 'paint_blue', 96, axis='X', center=(0, 0, CZ), ch=0.003),
                           cyl('f2', 0.12, 0.13, 0.16, 'paint_blue', 96, axis='X', center=(0, 0, CZ), ch=0.003),
                           box('yk', (0.08, 0.06, 0.14), (0, 0, CZ + 0.15), 'paint_blue', bevel=0.006)],
               [cyl('hi', 0.088, -0.14, 0.14, 'paint_blue', 96, axis='X', center=(0, 0, CZ)),
                cyl('fi', R + 0.007, -0.17, 0.17, 'paint_blue', 96, axis='X', center=(0, 0, CZ)),
                box('yki', (0.04, 0.03, 0.2), (0, 0, CZ + 0.15), 'paint_blue')], 'paint_blue')
    bl = [bolts_x(f'hb{s_}', s_ * 0.165, 0.12, CZ, 8, 0.05) for s_ in (-1, 1)]
    P(m, 'housing', 'Valve Housing with Flanges & Yoke', 'body', [hous] + bl, explode=(0, 0, -0.35), ref='pv_housing')
    stroke = 0.047
    top = join('topbar', [box('tbar', (0.05, 0.16, 0.02), (0, 0, CZ + R + 0.016), 'steel', bevel=0.003),
                          cyl('stm', 0.008, CZ + R + 0.02, CZ + 0.42, 'stainless', 24), cyl('thr', 0.011, CZ + 0.24, CZ + 0.33, 'steel_dark', 24)])
    pt = P(m, 'upper_pinch_bar', 'Upper Pinch Bar & Stem', 'mechanism', top, explode=(0, 0, 0.3), ref='pv_bars', section='keep')
    keys_loop(m, pt, lambda t: (0, 0, -stroke * cyc(t)))
    bot = join('botbar', [box('bbar', (0.05, 0.16, 0.02), (0, 0, CZ - R - 0.016), 'steel', bevel=0.003),
                          box('lk1', (0.012, 0.012, 0.13), (0, 0.075, CZ - 0.015), 'steel'), box('lk2', (0.012, 0.012, 0.13), (0, -0.075, CZ - 0.015), 'steel')])
    pb = P(m, 'lower_pinch_bar', 'Lower Pinch Bar & Links (double-pinch)', 'mechanism', bot, explode=(0, 0, -0.55), ref='pv_bars', section='keep')
    keys_loop(m, pb, lambda t: (0, 0, stroke * cyc(t)))
    hw = handwheel('hw', (0, 0, CZ + 0.42), 0.09, 'Z', 'paint_red')
    ph = P(m, 'handwheel', 'Handwheel', 'actuator', hw, explode=(0, 0, 0.45), ref='pv_handwheel', section='keep', pivot=(0, 0, CZ + 0.42))
    keys_loop(m, ph, lambda t: (0, 0, -stroke * cyc(t)))
    keys_loop(m, ph, lambda t: (0, 0, TAU * 4 * cyc(t)), 'rotation_euler')
    pipes = [hollow_pipe('pi', [(-0.6, 0, CZ), (-0.19, 0, CZ)], R, 'paint_grey', 48, t=0.006), hollow_pipe('po', [(0.19, 0, CZ), (0.6, 0, CZ)], R, 'paint_grey', 48, t=0.006),
             cyl('pf1', 0.12, -0.19, -0.165, 'paint_grey', 64, axis='X', center=(0, 0, CZ), r_in=R), cyl('pf2', 0.12, 0.165, 0.19, 'paint_grey', 64, axis='X', center=(0, 0, CZ), r_in=R)]
    P(m, 'pipework', 'Adjoining Pipework', 'system_piping', pipes, explode=(0, 0.3, 0), ref='pipework')
    m.flow('flow', [(-0.6, 0, CZ), (0.6, 0, CZ)], 'flow_suction', 0.012, 0.25, active=[(0.0, 0.38), (0.88, 1.0)])
    return m.export(out)


# =============================================================== EQ-120 Float valve
def float_valve(out):
    m = _model('float_valve', 'Float Valve (Ball-Float Tank Filling Valve)', META['float_valve'])
    CZ = 0.9
    wall = lathe('tank', [(0.75, -0.05), (0.79, -0.05), (0.79, 1.15), (0.75, 1.15)], 'paint_grey', 96, a0=0.0, a1=math.pi,
                 center=(0.55, 0, 0), cap_mat='paint_grey')
    floor = lathe('fl', [(0.0, -0.05), (0.79, -0.05), (0.79, 0.0), (0.0, 0.0)], 'paint_grey', 96, a0=0.0, a1=math.pi, center=(0.55, 0, 0), cap_mat='paint_grey')
    P(m, 'tank', 'Storage Tank (shown cut away)', 'structure', [wall, floor], explode=(0, 0.6, 0), ref='fv_tank', section='keep')
    wl = lambda t: 0.72 + 0.1 * smooth_pulse(t, 0.4, 0.15, 0.35)            # water level: rises → valve closes → falls
    water = lathe('water', [(0.0, -0.006), (0.745, -0.006), (0.745, 0.006), (0.0, 0.006)], 'water', 96, a0=0.0, a1=math.pi, center=(0.55, 0, 0), cap_mat='water')
    pw = P(m, 'water_level', 'Water Level (animated)', 'flow_tracers', water, ref='fv_water', section='keep')
    keys_loop(m, pw, lambda t: (0, 0, wl(t)))
    inl = [hollow_pipe('in', [(-0.45, 0, CZ), (0.0, 0, CZ)], 0.025, 'paint_blue', 32, t=0.004),
           cyl('wf', 0.06, 0.0, 0.02, 'steel', 6, axis='X', center=(0, 0, CZ), r_in=0.029)]
    P(m, 'inlet_pipe', 'Inlet Pipe through Tank Wall', 'system_piping', inl, explode=(-0.3, 0, 0), ref='pipework')
    body = csg('fv_body', [cyl('b', 0.04, 0.02, 0.14, 'brass', 48, axis='X', center=(0, 0, CZ)),
                           cyl('noz', 0.024, CZ - 0.12, CZ, 'brass', 48, center=(0.04, 0, 0))],
               [cyl('bi', 0.025, 0.0, 0.135, 'brass', 48, axis='X', center=(0, 0, CZ)), cyl('ni', 0.016, CZ - 0.13, CZ - 0.01, 'brass', 48, center=(0.04, 0, 0))], 'brass')
    P(m, 'valve_body', 'Valve Body, Seat & Outlet Nozzle', 'body', body, explode=(0, 0, 0.25), ref='fv_body')
    L, xp, zp = 0.5, 0.16, CZ + 0.05
    ang = lambda t: math.asin(max(-0.95, min(0.95, (wl(t) + 0.11 - zp) / L)))
    a_open, a_closed = ang(0.0), ang(0.5)
    plunger = join('plg', [cyl('pl', 0.022, 0.068, 0.135, 'stainless', 32, axis='X', center=(0, 0, CZ)), cyl('ws', 0.02, 0.06, 0.068, 'rubber', 32, axis='X', center=(0, 0, CZ))])
    ppl = P(m, 'plunger', 'Piston / Plunger with Rubber Washer', 'disc', plunger, explode=(0, -0.3, 0.2), ref='fv_plunger', section='keep')
    keys_loop(m, ppl, lambda t: (-0.038 * (ang(t) - a_open) / (a_closed - a_open), 0, 0))
    lever = join('lev', [box('arm', (L, 0.012, 0.012), (xp + L / 2, 0, zp), 'stainless'), cyl('pv', 0.01, -0.03, 0.03, 'steel', 16, axis='Y', center=(xp, 0, zp)),
                         sweep_tube('rod', [(xp + L, 0, zp), (xp + L, 0, zp - 0.04)], 0.006, 'stainless', 8),
                         sphere('fb', (xp + L, 0, zp - 0.11), 0.075, 'paint_red')])
    plv = P(m, 'float_lever', 'Float Ball & Lever Arm', 'float', lever, explode=(0, 0, 0.4), ref='fv_float', section='keep', pivot=(xp, 0, zp))
    keys_loop(m, plv, lambda t: (0, -ang(t), 0), 'rotation_euler')
    m.flow('flow_in', [(-0.45, 0, CZ), (0.035, 0, CZ), (0.04, 0, CZ - 0.02), (0.04, 0, 0.62)], 'water', 0.008, 0.2, active=[(0.0, 0.3), (0.9, 1.0)])
    return m.export(out)


# =============================================================== EQ-121 Foot valve
def foot_valve(out):
    m = _model('foot_valve', 'Foot Valve with Strainer (Spring-Assisted Poppet)', META['foot_valve'])
    Z0, R = 0.25, 0.05
    sump = [box('fl', (0.9, 0.9, 0.05), (0, 0, -0.025), 'paint_grey'),
            lathe('w', [(0.45, 0.0), (0.48, 0.0), (0.48, 1.0), (0.45, 1.0)], 'paint_grey', 64, a0=0.0, a1=math.pi, cap_mat='paint_grey')]
    P(m, 'sump', 'Suction Sump (shown cut away)', 'structure', sump, explode=(0, 0.5, 0), ref='ftv_sump', section='keep')
    P(m, 'water', 'Liquid Level', 'flow_tracers', [lathe('wl', [(0.0, 0.774), (0.448, 0.774), (0.448, 0.782), (0.0, 0.782)], 'water', 64, a0=0.0, a1=math.pi, cap_mat='water')],
      ref='ftv_water', section='keep')
    body = csg('ftv_body', [cyl('b', R + 0.03, Z0 + 0.02, Z0 + 0.2, 'cast_iron', 64, ch=0.004), cyl('fl', 0.115, Z0 + 0.2, Z0 + 0.225, 'cast_iron', 64, ch=0.003)],
               [cyl('bi', R + 0.012, Z0 + 0.05, Z0 + 0.16, 'cast_iron', 64), cyl('st', R - 0.008, Z0 + 0.0, Z0 + 0.06, 'cast_iron', 64),
                cyl('ot', R, Z0 + 0.15, Z0 + 0.23, 'cast_iron', 64)], 'cast_iron')
    seat = cyl('seat', R + 0.004, Z0 + 0.045, Z0 + 0.055, 'bronze', 64, r_in=R - 0.008)
    P(m, 'body', 'Valve Body & Seat Ring', 'body', [body, seat], explode=(0.3, 0, 0), ref='ftv_body')
    cage = [cyl('sb', 0.11, Z0 - 0.17, Z0 - 0.16, 'stainless', 64), cyl('st', 0.11, Z0 + 0.0, Z0 + 0.02, 'stainless', 64, r_in=R - 0.008)]
    for i in range(24):
        a = TAU * i / 24
        cage.append(sweep_tube(f'cb{i}', [(0.105 * math.cos(a), 0.105 * math.sin(a), Z0 - 0.16), (0.105 * math.cos(a), 0.105 * math.sin(a), Z0)], 0.004, 'stainless', 6))
    for zz in (Z0 - 0.11, Z0 - 0.055):
        cage.append(cyl(f'cr{zz}', 0.109, zz - 0.003, zz + 0.003, 'stainless', 64, r_in=0.101))
    P(m, 'strainer', 'Strainer Basket', 'strainer', cage, explode=(0, 0, -0.35), ref='ftv_strainer')
    lift = 0.03
    disc = join('disc', [cyl('d', R + 0.006, Z0 + 0.055, Z0 + 0.07, 'bronze', 64, ch=0.003), cyl('ds', 0.008, Z0 + 0.03, Z0 + 0.15, 'stainless', 24),
                         cyl('rs', R - 0.004, Z0 + 0.052, Z0 + 0.056, 'rubber', 64)])
    cyc = lambda t: smooth_pulse(t, 0.1, 0.45, 0.08)          # pump runs (open) → stops (closes and holds the column)
    pd = P(m, 'poppet', 'Poppet Disc with Soft Seal & Guide Stem', 'disc', disc, explode=(0, 0, 0.3), ref='ftv_poppet', section='keep')
    keys_loop(m, pd, lambda t: (0, 0, lift * cyc(t)))
    guide = [cyl('gb', 0.012, Z0 + 0.135, Z0 + 0.15, 'cast_iron', 24, r_in=0.0085)] + [box(f'gr{i}', (0.006, R * 2 - 0.004, 0.01), (0, 0, Z0 + 0.142), 'cast_iron') for i in range(1)]
    sp = spring('spr', (0, 0, 0), 0.016, Z0 + 0.07, Z0 + 0.135, 0.0025, 5)
    P(m, 'guide_spring', 'Guide Bridge & Closing Spring', 'spring', guide + [sp], explode=(0, -0.3, 0.3), ref='ftv_spring')
    pipe = [hollow_pipe('sp', [(0, 0, Z0 + 0.225), (0, 0, 1.15)], R, 'paint_grey', 48, t=0.006), cyl('pfl', 0.115, Z0 + 0.225, Z0 + 0.25, 'paint_grey', 64, r_in=R)]
    P(m, 'suction_pipe', 'Suction Pipe (to pump)', 'system_piping', pipe, explode=(0, 0, 0.6), ref='pipework')
    m.flow('flow', [(0.2, 0, Z0 - 0.08), (0.11, 0, Z0 - 0.08), (0.03, 0, Z0 + 0.03), (0.03, 0, Z0 + 0.1), (0.0, 0, Z0 + 0.25), (0, 0, 1.2)], 'flow_suction', 0.008, 0.15,
           active=[(0.05, 0.55)])
    return m.export(out)


# =============================================================== EQ-122 Solenoid valve
def solenoid_valve(out):
    m = _model('solenoid_valve', 'Solenoid Valve (2/2 NC, Pilot-Operated Diaphragm)', META['solenoid_valve'])
    CZ = 0.15
    body = csg('sv_body', [box('b', (0.16, 0.08, 0.07), (0, 0, CZ), 'brass', bevel=0.006), cyl('bn', 0.05, CZ + 0.03, CZ + 0.05, 'brass', 64)],
               [cyl('in', 0.014, -0.09, -0.02, 'brass', 32, axis='X', center=(0, 0, CZ - 0.005)), cyl('chi', 0.035, CZ + 0.012, CZ + 0.04, 'brass', 64),
                cyl('ori', 0.012, CZ - 0.01, CZ + 0.02, 'brass', 32), cyl('out', 0.014, 0.0, 0.09, 'brass', 32, axis='X', center=(0, 0, CZ - 0.01)),
                box('inr', (0.06, 0.03, 0.03), (-0.025, 0, CZ + 0.008), 'brass')], 'brass')
    P(m, 'body', 'Valve Body (Brass) with Main Orifice', 'body', body, explode=(0, 0, -0.15), ref='sv_body')
    sv_open = lambda t: smooth_pulse(t, 0.08, 0.4, 0.08)
    dia = join('dia', [cyl('dm', 0.036, CZ + 0.02, CZ + 0.026, 'rubber', 64), cyl('dp', 0.016, CZ + 0.026, CZ + 0.032, 'brass', 32, r_in=0.002)])
    pdia = P(m, 'diaphragm', 'Main Diaphragm with Pilot & Bleed Orifices', 'disc', dia, explode=(0, -0.2, 0.05), ref='sv_diaphragm', section='split')
    keys_loop(m, pdia, lambda t: (0, 0, 0.009 * sv_open(max(0.0, t - 0.03))))
    cover = csg('cov', [cyl('c', 0.05, CZ + 0.05, CZ + 0.065, 'brass', 64), cyl('tube', 0.013, CZ + 0.065, CZ + 0.16, 'stainless', 32)],
                [cyl('ci', 0.035, CZ + 0.04, CZ + 0.055, 'brass', 64), cyl('ti', 0.0095, CZ + 0.05, CZ + 0.155, 'stainless', 32)], 'brass')
    P(m, 'armature_tube', 'Bonnet & Armature (Plunger) Tube', 'bonnet', cover, explode=(0, 0, 0.12), ref='sv_tube')
    plg = join('plg', [cyl('p', 0.009, CZ + 0.058, CZ + 0.13, 'steel_dark', 32), cyl('ps', 0.0035, CZ + 0.054, CZ + 0.058, 'rubber', 16),
                       spring('ps2', (0, 0, 0), 0.006, CZ + 0.13, CZ + 0.152, 0.0012, 5)])
    pp = P(m, 'plunger', 'Plunger (Armature), Pilot Seal & Spring', 'actuator', plg, explode=(0, 0, 0.3), ref='sv_plunger', section='split')
    keys_loop(m, pp, lambda t: (0, 0, 0.006 * sv_open(t)))
    coil = csg('coil', [box('ch', (0.07, 0.07, 0.085), (0, 0, CZ + 0.115), 'thermoplastic', bevel=0.006),
                        box('con', (0.03, 0.04, 0.03), (0.0, -0.05, CZ + 0.13), 'thermoplastic', bevel=0.004)],
                [cyl('cb', 0.0135, CZ + 0.06, CZ + 0.17, 'thermoplastic', 32)], 'thermoplastic')
    wind = cyl('wnd', 0.03, CZ + 0.08, CZ + 0.15, 'copper', 48, r_in=0.016)
    nut = hex_prism('nut', 0.03, CZ + 0.16, CZ + 0.17, 'steel')
    P(m, 'coil', 'Solenoid Coil (Encapsulated) & Connector', 'actuator', [coil, wind, nut], explode=(0, 0, 0.45), ref='sv_coil')
    pipes = [hollow_pipe('pi', [(-0.35, 0, CZ - 0.005), (-0.08, 0, CZ - 0.005)], 0.014, 'steel', 24, t=0.004), hollow_pipe('po', [(0.08, 0, CZ - 0.01), (0.35, 0, CZ - 0.01)], 0.014, 'steel', 24, t=0.004)]
    P(m, 'pipework', 'Threaded Pipework', 'system_piping', pipes, explode=(0, 0.25, 0), ref='pipework')
    m.flow('flow', [(-0.35, 0, CZ - 0.005), (-0.03, 0, CZ - 0.005), (-0.03, 0, CZ + 0.03), (0, 0, CZ + 0.03), (0, 0, CZ - 0.008), (0.35, 0, CZ - 0.01)],
           'flow_suction', 0.004, 0.08, active=[(0.1, 0.5)])
    loops = []
    for i, rr in enumerate((0.02, 0.03, 0.04)):
        for sx in (1, -1):
            pts = [(sx * rr * 0.55, 0, CZ + 0.075), (sx * (rr + 0.012), 0, CZ + 0.062), (sx * (rr + 0.03), 0, CZ + 0.07), (sx * (rr + 0.042), 0, CZ + 0.115),
                   (sx * (rr + 0.03), 0, CZ + 0.165), (sx * (rr + 0.012), 0, CZ + 0.172), (sx * rr * 0.55, 0, CZ + 0.16), (sx * rr * 0.35, 0, CZ + 0.115), (sx * rr * 0.55, 0, CZ + 0.075)]
            loops.append(sweep_tube(f'fl{i}{sx}', pts, 0.0016, 'heat', 8))
    m.overlay('magnetic_field', join('field', loops), 'Magnetic field',
              'When the coil is energised its magnetic field (loops) is concentrated by the plunger and pulls it up, opening the pilot orifice. '
              'Cover pressure then bleeds to the outlet, so line pressure lifts the diaphragm and the main orifice opens.', split=True)
    m.annotate('magnetic_field', 'Coil energised → field pulls plunger up', (0.12, 0, CZ + 0.16))
    return m.export(out)


# =============================================================== EQ-123 Three-way valve
def three_way_valve(out):
    m = _model('three_way_valve', 'Three-Way Ball Valve (L-Port, Diverting)', META['three_way_valve'])
    CZ, R = 0.35, 0.03
    body = csg('tw_body', [cyl('bx', 0.07, -0.12, 0.12, 'stainless', 64, axis='X', center=(0, 0, CZ)), cyl('bz', 0.07, CZ - 0.12, CZ + 0.06, 'stainless', 64),
                           sphere('bs', (0, 0, CZ), 0.085, 'stainless', 48), cyl('bn', 0.028, CZ + 0.06, CZ + 0.1, 'stainless', 32)],
               [cyl('ix', R, -0.13, 0.13, 'stainless', 48, axis='X', center=(0, 0, CZ)), cyl('iz', R, CZ - 0.13, CZ, 'stainless', 48),
                sphere('cav', (0, 0, CZ), 0.058, 'stainless', 48), cyl('sb', 0.011, CZ, CZ + 0.11, 'stainless', 24)], 'stainless')
    fl = [flange('f1', -0.12, R, CZ, 0.1, 0.02, 'stainless', -1), flange('f2', 0.12, R, CZ, 0.1, 0.02, 'stainless', +1)]
    fz = cyl('f3', 0.1, CZ - 0.14, CZ - 0.12, 'stainless', 64, r_in=R)
    seats = [cyl('s1', 0.052, -0.06, -0.05, 'ptfe', 48, axis='X', center=(0, 0, CZ), r_in=R + 0.002), cyl('s2', 0.052, 0.05, 0.06, 'ptfe', 48, axis='X', center=(0, 0, CZ), r_in=R + 0.002),
             cyl('s3', 0.052, CZ - 0.06, CZ - 0.05, 'ptfe', 48, r_in=R + 0.002)]
    P(m, 'body', 'Valve Body (Three Ports) with Flanges', 'body', [body, fz] + fl, explode=(0, 0, -0.3), ref='tw_body')
    P(m, 'seats', 'PTFE Seats', 'seat', seats, explode=(0, -0.3, -0.15), ref='tw_seats')
    rot = lambda t: math.pi * smooth_pulse(t, 0.12, 0.38, 0.12)
    ball = csg('ball', [sphere('bl', (0, 0, 0), 0.055, 'chrome', 48)],
               [cyl('lz', R, -0.07, 0.0, 'chrome', 32), cyl('lx', R, 0.0, 0.07, 'chrome', 32, axis='X'), sphere('lc', (0, 0, 0), R, 'chrome', 32),
                box('slot', (0.04, 0.012, 0.03), (0, 0, 0.055), 'chrome')], 'chrome')
    transform(ball, __import__('mathutils').Matrix.Translation((0, 0, CZ)))
    stem = join('stem', [cyl('st', 0.01, CZ + 0.035, CZ + 0.14, 'stainless', 24), box('lev', (0.24, 0.025, 0.012), (0.1, 0, CZ + 0.14), 'paint_red', bevel=0.003),
                         box('ind', (0.05, 0.008, 0.004), (0.03, 0, CZ + 0.148), 'paint_yellow')])
    pb = P(m, 'ball', 'L-Port Ball', 'disc', ball, explode=(0, -0.35, 0), ref='tw_ball', section='split', pivot=(0, 0, CZ))
    keys_loop(m, pb, lambda t: (0, 0, rot(t)), 'rotation_euler')
    ps = P(m, 'stem_lever', 'Stem & Lever (L-shaped pointer shows flow path)', 'actuator', stem, explode=(0, 0, 0.35), ref='tw_stem', section='keep', pivot=(0, 0, CZ))
    keys_loop(m, ps, lambda t: (0, 0, rot(t)), 'rotation_euler')
    pipes = [hollow_pipe('pa', [(-0.5, 0, CZ), (-0.14, 0, CZ)], R, 'paint_grey', 32, t=0.005), hollow_pipe('pb', [(0.14, 0, CZ), (0.5, 0, CZ)], R, 'paint_grey', 32, t=0.005),
             hollow_pipe('pc', [(0, 0, -0.1), (0, 0, CZ - 0.14)], R, 'paint_grey', 32, t=0.005)]
    P(m, 'pipework', 'Inlet (bottom) and Outlets A / B', 'system_piping', pipes, explode=(0, 0.3, 0), ref='pipework')
    m.flow('to_A', [(0, 0, -0.1), (0, 0, CZ), (0.5, 0, CZ)], 'flow_suction', 0.007, 0.15, active=[(0.0, 0.08), (0.66, 1.0)])
    m.flow('to_B', [(0, 0, -0.1), (0, 0, CZ), (-0.5, 0, CZ)], 'flow_discharge', 0.007, 0.15, active=[(0.15, 0.48)])
    return m.export(out)


# =============================================================== EQ-124 Four-way valve
def four_way_valve(out):
    m = _model('four_way_valve', 'Four-Way Directional Control Valve (4/2 Spool) with Cylinder', META['four_way_valve'])
    CZ, rb = 0.2, 0.015
    gx = {'T1': -0.075, 'A': -0.04, 'P': 0.0, 'B': 0.04, 'T2': 0.075}
    ins = [cyl('bore', rb, -0.125, 0.125, 'paint_grey', 48, axis='X', center=(0, 0, CZ))]
    for k, x in gx.items():
        ins.append(cyl(f'g{k}', rb + 0.008, x - 0.009, x + 0.009, 'paint_grey', 48, axis='X', center=(0, 0, CZ)))
        up = k in ('A', 'B')
        ins.append(cyl(f'd{k}', 0.007, CZ if up else CZ - 0.07, CZ + 0.07 if up else CZ, 'paint_grey', 24, center=(x, 0, 0)))
    ins.append(box('tgal', (0.16, 0.012, 0.012), (0, 0.0, CZ - 0.045), 'paint_grey'))
    body = csg('fw_body', [box('b', (0.25, 0.09, 0.11), (0, 0, CZ), 'paint_grey', bevel=0.006)], ins, 'paint_grey')
    P(m, 'body', 'Valve Body with Ports P, T, A, B', 'body', body, explode=(0, 0, -0.25), ref='fwv_body')
    s_ = lambda t: -0.04 * smooth_pulse((t - 0.45) % 1.0, 0.06, 0.45, 0.06)
    spool = [cyl('sp', 0.007, -0.17, 0.17, 'chrome', 24, axis='X', center=(0, 0, CZ))]
    for x in (-0.0575, 0.02, 0.095):
        spool.append(cyl(f'l{x}', rb - 0.0005, x - 0.012, x + 0.012, 'chrome', 48, axis='X', center=(0, 0, CZ)))
    psp = P(m, 'spool', 'Spool with Lands', 'disc', spool, explode=(0, -0.3, 0), ref='fwv_spool')
    keys_loop(m, psp, lambda t: (s_(t), 0, 0))
    sol = []
    for sx in (-1, 1):
        sol += [box(f'sc{sx}', (0.07, 0.07, 0.07), (sx * 0.165, 0, CZ), 'thermoplastic', bevel=0.005), cyl(f'sn{sx}', 0.012, sx * 0.2, sx * 0.21, 'steel', 6, axis='X', center=(0, 0, CZ)),
                cyl(f'sw{sx}', 0.028, sx * 0.14 - 0.022, sx * 0.14 + 0.022 if sx > 0 else sx * 0.14 + 0.022, 'copper', 32, axis='X', center=(0, 0, CZ), r_in=0.012),
                box(f'cn{sx}', (0.03, 0.03, 0.025), (sx * 0.165, 0, CZ + 0.045), 'thermoplastic', bevel=0.003)]
    P(m, 'solenoids', 'Solenoid Operators a / b', 'actuator', sol, explode=(0, 0, 0.25), ref='fwv_solenoids')
    ZC, XC0, XC1 = CZ + 0.26, -0.22, 0.22
    cylb = csg('cyl', [cyl('c', 0.04, XC0, XC1, 'paint_blue', 48, axis='X', center=(0, 0, ZC)), cyl('e1', 0.048, XC0 - 0.02, XC0, 'paint_blue', 48, axis='X', center=(0, 0, ZC)),
                       cyl('e2', 0.048, XC1, XC1 + 0.02, 'paint_blue', 48, axis='X', center=(0, 0, ZC))],
               [cyl('ci', 0.033, XC0, XC1, 'paint_blue', 48, axis='X', center=(0, 0, ZC)), cyl('rb2', 0.012, XC1 - 0.01, XC1 + 0.03, 'paint_blue', 24, axis='X', center=(0, 0, ZC))], 'paint_blue')
    P(m, 'cylinder', 'Double-Acting Cylinder (actuator driven by A / B)', 'actuator', cylb, explode=(0, 0, 0.35), ref='fwv_cylinder')
    pos = lambda t: -0.13 + 0.26 * (smooth_pulse(t, 0.4, 0.06, 0.4))
    pis = join('pis', [cyl('pp', 0.0325, -0.015, 0.015, 'steel_dark', 48, axis='X', center=(0, 0, ZC)), cyl('rod', 0.011, 0.0, 0.33, 'chrome', 24, axis='X', center=(0, 0, ZC))])
    ppi = P(m, 'piston_rod', 'Piston & Rod', 'actuator', pis, explode=(0, -0.35, 0.35), ref='fwv_piston', section='split')
    keys_loop(m, ppi, lambda t: (pos(t), 0, 0))
    lines = [hollow_pipe('la', [(gx['A'], 0, CZ + 0.055), (gx['A'], 0, CZ + 0.14), (XC0 + 0.01, 0, CZ + 0.14), (XC0 + 0.01, 0, ZC - 0.035)], 0.007, 'steel', 16, bend=0.02, t=0.002),
             hollow_pipe('lb', [(gx['B'], 0, CZ + 0.055), (gx['B'], 0, CZ + 0.14), (XC1 - 0.01, 0, CZ + 0.14), (XC1 - 0.01, 0, ZC - 0.035)], 0.007, 'steel', 16, bend=0.02, t=0.002),
             hollow_pipe('lp', [(0.0, 0, CZ - 0.055), (0.0, 0, -0.0), (0.3, 0, 0.0)], 0.008, 'paint_red', 16, bend=0.02, t=0.002),
             hollow_pipe('lt', [(0.04, 0.0, CZ - 0.055), (0.04, 0.0, 0.04), (-0.3, 0.0, 0.04)], 0.008, 'paint_green', 16, bend=0.02, t=0.002)]
    P(m, 'hydraulic_lines', 'Hydraulic Lines: P (pump), T (tank), A, B', 'system_piping', lines, explode=(0, 0.3, 0), ref='fwv_lines')
    m.flow('P_to_A', [(0.3, 0, 0.0), (0, 0, 0.0), (0, 0, CZ), (gx['A'], 0, CZ), (gx['A'], 0, CZ + 0.14), (XC0 + 0.01, 0, CZ + 0.14), (XC0 + 0.01, 0, ZC)],
           'hydraulic_oil', 0.004, 0.08, active=[(0.0, 0.42)])
    m.flow('B_to_T', [(XC1 - 0.01, 0, ZC), (XC1 - 0.01, 0, CZ + 0.14), (gx['B'], 0, CZ + 0.14), (gx['B'], 0, CZ), (gx['T2'], 0, CZ), (gx['T2'], 0, CZ - 0.045), (0.04, 0, 0.04), (-0.3, 0, 0.04)],
           'flow_suction', 0.004, 0.08, active=[(0.0, 0.42)])
    m.flow('P_to_B', [(0.3, 0, 0.0), (0, 0, 0.0), (0, 0, CZ), (gx['B'], 0, CZ), (gx['B'], 0, CZ + 0.14), (XC1 - 0.01, 0, CZ + 0.14), (XC1 - 0.01, 0, ZC)],
           'hydraulic_oil', 0.004, 0.08, active=[(0.5, 0.92)])
    m.flow('A_to_T', [(XC0 + 0.01, 0, ZC), (XC0 + 0.01, 0, CZ + 0.14), (gx['A'], 0, CZ + 0.14), (gx['A'], 0, CZ), (gx['T1'], 0, CZ), (gx['T1'], 0, CZ - 0.045), (0.04, 0, CZ - 0.045),
                      (0.04, 0, 0.04), (-0.3, 0, 0.04)], 'flow_suction', 0.004, 0.08, active=[(0.5, 0.92)])
    return m.export(out)


# =============================================================== EQ-125 Vacuum relief valve
def vacuum_relief_valve(out):
    m = _model('vacuum_relief_valve', 'Vacuum Relief Valve (Spring-Loaded, Tank Roof)', META['vacuum_relief_valve'])
    Z0, R = 0.3, 0.06
    roof = lathe('roof', [(0.0, Z0 - 0.21), (0.6, Z0 - 0.25), (0.6, Z0 - 0.22), (0.0, Z0 - 0.18)], 'paint_grey', 96, a0=0.0, a1=math.pi, cap_mat='paint_grey')
    noz = cyl('nz', R + 0.02, Z0 - 0.2, Z0, 'paint_grey', 64, r_in=R + 0.012)
    nfl = cyl('nf', 0.13, Z0 - 0.02, Z0, 'paint_grey', 64, r_in=R + 0.012)
    P(m, 'tank_roof', 'Tank Roof (shown cut away)', 'structure', [roof], explode=(0, 0, -0.3), ref='vr_roof', section='keep')
    P(m, 'nozzle', 'Roof Nozzle & Flange', 'structure', [noz, nfl], explode=(0, 0, -0.2), ref='vr_roof')
    body = csg('vr_body', [cyl('b', R + 0.03, Z0, Z0 + 0.16, 'stainless', 64), cyl('bf', 0.13, Z0, Z0 + 0.02, 'stainless', 64, ch=0.003)],
               [cyl('bi', R + 0.016, Z0 + 0.025, Z0 + 0.17, 'stainless', 64), cyl('bt', R + 0.016, Z0 - 0.01, Z0 + 0.03, 'stainless', 64)], 'stainless')
    seat = cyl('seat', R + 0.017, Z0 + 0.025, Z0 + 0.035, 'stainless', 64, r_in=R - 0.012)
    P(m, 'body', 'Valve Body & Seat Ring', 'body', [body, seat], explode=(0.3, 0, 0), ref='vr_body')
    hood = csg('hood', [cyl('h', 0.12, Z0 + 0.2, Z0 + 0.24, 'stainless', 64), cyl('hl', 0.12, Z0 + 0.13, Z0 + 0.2, 'stainless', 64)],
               [cyl('hi', 0.112, Z0 + 0.12, Z0 + 0.232, 'stainless', 64)], 'stainless')
    legs = [box(f'lg{i}', (0.012, 0.012, 0.07), (0.085 * math.cos(TAU * i / 4 + 0.5), 0.085 * math.sin(TAU * i / 4 + 0.5), Z0 + 0.17), 'stainless') for i in range(4)]
    screen = cyl('scr', 0.118, Z0 + 0.135, Z0 + 0.195, 'steel_dark', 64, r_in=0.114)
    P(m, 'hood_screen', 'Weather Hood & Bird Screen', 'body', [hood, screen] + legs, explode=(0, 0, 0.35), ref='vr_hood')
    op = lambda t: smooth_pulse(t, 0.15, 0.3, 0.15)
    pal = join('pal', [cyl('pd', R + 0.004, Z0 - 0.002, Z0 + 0.02, 'stainless', 64, ch=0.003), cyl('ps', R - 0.004, Z0 + 0.018, Z0 + 0.024, 'ptfe', 64),
                       cyl('stem', 0.007, Z0 - 0.06, Z0 + 0.2, 'stainless', 24), cyl('nut', 0.014, Z0 + 0.19, Z0 + 0.2, 'steel', 6)])
    pp = P(m, 'pallet', 'Pallet (Disc) & Stem — opens inward on vacuum', 'disc', pal, explode=(0, -0.3, -0.2), ref='vr_pallet', section='keep')
    keys_loop(m, pp, lambda t: (0, 0, -0.04 * op(t)))
    br = join('bridge', [box('br', (2 * R + 0.02, 0.016, 0.01), (0, 0, Z0 + 0.12), 'stainless'), cyl('bg', 0.012, Z0 + 0.11, Z0 + 0.13, 'stainless', 24, r_in=0.0075)])
    sp = spring('sp', (0, 0, 0), 0.018, Z0 + 0.13, Z0 + 0.19, 0.0025, 6)
    P(m, 'spring', 'Bridge & Set-Pressure Spring', 'spring', [br, sp], explode=(0, 0, 0.55), ref='vr_spring')
    add_tracers(m, 'air_in', 'Atmospheric Air Entering (Tracers)', [(0.2, 0.05, Z0 + 0.16), (0.0, 0.03, Z0 + 0.1), (0.0, 0.03, Z0 - 0.03), (0.0, 0.03, Z0 - 0.25)], n=8,
                radius=0.008, mat='air')
    m.flow('air', [(0.25, 0, Z0 + 0.165), (0.08, 0, Z0 + 0.165), (0.04, 0, Z0 + 0.08), (0.03, 0, Z0 - 0.05), (0.03, 0, Z0 - 0.25)], 'air', 0.006, 0.08, active=[(0.1, 0.55)])
    return m.export(out)


# ===================================================================== metadata
def _std(*items):
    return [{'id': i, 'title': t, 'relevance': r, 'edition': 'to be verified'} for i, t, r in items]


META = {
    'needle_valve': {
        'summary': ('A needle valve controls small flows precisely. A long, tapered needle on a fine-threaded stem moves into a small seat orifice, '
                    'so many turns of the handle give a small, gradual change in the open area. It is used for instrument isolation, gauge snubbing, '
                    'sampling and fine metering.'),
        'classification': {'family': 'Linear-motion valve (globe family)', 'type': 'Needle valve, rising stem, bar-stock body'},
        'model_configuration': {'connection': 'Compression fittings on instrument tubing', 'seat': 'Integral metal seat, conical needle', 'packing': 'PTFE below gland nut'},
        'standards': _std(('ASME B16.34', 'Valves — Flanged, Threaded and Welding End', 'Pressure–temperature ratings.'),
                          ('MSS SP-99', 'Instrument Valves', 'Instrument valve design and testing.')),
        'references': ['Swagelok / Parker instrument valve catalogues (generic arrangement)', 'Skousen, Valve Handbook'],
        'components': {
            'nv_body': C('Contains the inlet, seat orifice and outlet passages.', 'Machined from bar stock; inlet below the seat so pressure acts under the needle.', 'Stainless steel 316, carbon steel, brass, Monel.',
                         'Rated to high pressures in small sizes.', ['Seat erosion (wire-drawing)', 'Thread galling'], ['Seat leak test']),
            'nv_bonnet': C('Guides the stem and seals it with packing.', 'Threaded bonnet with packing and gland nut.', 'Stainless steel; PTFE or graphite packing.', 'Adjust gland to stop stem leaks.',
                           ['Packing leakage'], ['Tighten gland, repack']),
            'nv_stem': C('Positions the needle in the seat orifice to set the flow area.', 'Fine-thread rising stem with integral cone needle and handle.', 'Hardened stainless.',
                         'Do not overtighten — the needle can deform the seat.', ['Bent / scored needle'], ['Visual, seat leak test']),
            'nv_tubing': C('Connects the valve to instruments or sample points.', 'Seamless tubing with two-ferrule compression fittings.', 'Stainless 316.', 'Correct make-up turns per fitting maker.',
                           ['Fitting leaks'], ['Gap gauge on fittings']),
        },
    },
    'pinch_valve': {
        'summary': ('A pinch valve closes by squeezing a flexible elastomer sleeve. The liquid touches only the sleeve, and the open valve is a straight, '
                    'full-bore tube, so pinch valves handle abrasive slurries, powders and corrosive liquids with no pockets to clog.'),
        'classification': {'family': 'Linear-motion valve', 'type': 'Enclosed-body pinch valve, double-pinch, manual'},
        'model_configuration': {'actuation': 'Handwheel; pneumatic/hydraulic versions pressurise the housing instead', 'sleeve': 'Natural rubber / EPDM / NBR'},
        'standards': _std(('ISO 5208', 'Industrial valves — Pressure testing of metallic valves', 'Shell and seat tests (adapted).'),
                          ('EN 593 / manufacturer', 'Valve design', 'Pinch valves are largely manufacturer-standardised.')),
        'references': ['Skousen, Valve Handbook — pinch valves', 'Slurry-handling guidance (mining, alumina)'],
        'components': {
            'pv_sleeve': C('The only wetted part: it carries the flow when open and is squeezed shut to close.', 'Reinforced elastomer tube with integral flanged ends.',
                           'Natural rubber (abrasion), EPDM, NBR, Hypalon, FKM.', 'Sleeve flex life and chemical compatibility govern service life.',
                           ['Fatigue cracking', 'Abrasion wear', 'Chemical swelling'], ['Inspect for cracks/bulges; scheduled replacement']),
            'pv_housing': C('Encloses and supports the sleeve and carries the mechanism.', 'Cast or fabricated body with end flanges and yoke.', 'Cast iron, aluminium, steel.',
                            'Contains leakage if the sleeve ruptures.', ['Corrosion'], ['Visual']),
            'pv_bars': C('Squeeze the sleeve from both sides so it closes on the pipe centreline.', 'Upper bar on the stem, lower bar via links (double pinch).', 'Steel.',
                         'Over-closing shortens sleeve life.', ['Bent bars'], ['Check closing stops']),
            'pv_handwheel': C('Moves the pinch bars via the stem thread.', 'Rising handwheel/stem.', 'Cast iron/steel.', 'Manual torque limited.', ['Thread wear'], ['Lubricate stem']),
        },
    },
    'float_valve': {
        'summary': ('A float valve keeps a tank at a set level automatically. A float on a lever arm rises with the liquid; the lever pushes a plunger '
                    'onto the seat and gradually closes the inlet as the tank fills. When the level falls, the float drops and the valve opens again.'),
        'classification': {'family': 'Self-acting level control valve', 'type': 'Ball-float valve (side-entry, piston type)'},
        'model_configuration': {'mechanism': 'Lever multiplies float buoyancy into seating force', 'animation': 'Level rises → valve closes; level falls → valve opens'},
        'standards': _std(('BS 1212 / EN 14124', 'Float-operated valves', 'Domestic/commercial float valves.'),),
        'references': ['Water-supply design guides (tank inlets)'],
        'components': {
            'fv_tank': C('Stores the liquid; the valve maintains its level.', 'Tank shell (cut away).', 'Steel, concrete, GRP.', '—', ['Overflow if valve fails'], ['Overflow pipe check']),
            'fv_water': C('Liquid surface that the float follows.', 'Animated level.', '—', 'Level band set by lever geometry.', ['—'], ['—']),
            'fv_body': C('Contains the seat and outlet nozzle.', 'Cast body screwed to the inlet pipe.', 'Brass, bronze, plastic.', 'Pressure rating must exceed supply pressure.', ['Seat erosion'], ['Check for passing']),
            'fv_plunger': C('Closes against the seat when pushed by the lever.', 'Piston with rubber washer.', 'Brass + EPDM washer.', 'Washer wear causes passing.', ['Worn washer'], ['Replace washer']),
            'fv_float': C('Senses the level and supplies the closing force.', 'Hollow ball float on an adjustable lever arm.', 'Copper, plastic, stainless.', 'Arm length sets force and level.',
                          ['Punctured float', 'Sticking pivot'], ['Check float buoyancy and pivot']),
        },
    },
    'foot_valve': {
        'summary': ('A foot valve is a check valve with a strainer fitted at the bottom of a pump suction pipe. It lets liquid flow up to the pump but '
                    'closes when the pump stops, so the suction line stays full (primed). The strainer keeps debris out of the pump.'),
        'classification': {'family': 'Check valve', 'type': 'Spring-assisted poppet foot valve with strainer'},
        'model_configuration': {'installation': 'Submerged at the end of a vertical suction pipe', 'animation': 'Pump running → poppet open; pump stopped → poppet closes'},
        'standards': _std(('EN 12334 / MSS SP-71', 'Check valves', 'Check valve design (generic).'), ('ANSI/HI 9.8', 'Pump intake design', 'Submergence and clearance at the suction.')),
        'references': ['Pump installation manuals — foot valves'],
        'components': {
            'ftv_sump': C('Holds the liquid the pump draws from.', 'Wet sump/tank.', 'Concrete/steel.', 'Keep foot valve submerged and clear of the bottom.', ['Sediment'], ['Clean sump']),
            'ftv_water': C('Liquid level above the valve.', '—', '—', 'Submergence prevents vortices.', ['—'], ['—']),
            'ftv_body': C('Holds the seat and connects to the suction pipe.', 'Cast body with seat ring.', 'Cast iron, bronze, PVC.', 'Large flow area keeps suction losses low.', ['Seat wear'], ['Check for back-leakage']),
            'ftv_strainer': C('Keeps debris out of the pump.', 'Perforated or bar basket around the inlet.', 'Stainless/galvanised steel, plastic.', 'Open area should be ≥3–4× pipe area (rule of thumb).',
                              ['Clogging'], ['Clean regularly']),
            'ftv_poppet': C('Opens with flow and closes on stop to hold the suction column.', 'Disc with soft seal on a guided stem.', 'Bronze/stainless + NBR.', 'Must close quickly to avoid back-flow.',
                            ['Sticking open', 'Seal wear'], ['Check pump re-priming']),
            'ftv_spring': C('Helps the poppet close fast when flow stops.', 'Guide bridge and compression spring.', 'Stainless.', '—', ['Spring corrosion'], ['Visual']),
        },
    },
    'solenoid_valve': {
        'summary': ('A solenoid valve opens and closes electrically. In this normally-closed, pilot-operated design the coil lifts a small plunger, '
                    'which opens a pilot orifice; pressure above the diaphragm bleeds away and line pressure lifts the diaphragm off the main seat. '
                    'De-energising the coil lets the spring push the plunger back and the valve closes. A minimum pressure difference is needed to operate.'),
        'classification': {'family': 'Automated on/off valve', 'type': '2/2-way normally closed, servo (pilot) operated diaphragm'},
        'model_configuration': {'coil': 'Encapsulated, connector per EN 175301-803', 'note': 'Direct-acting versions open without pressure difference but only for small orifices'},
        'standards': _std(('IEC 60730 / UL 429', 'Electrically operated valves', 'Safety of solenoid valves.'), ('EN 175301-803', 'Rectangular connectors', 'Coil connector.')),
        'references': ['ASCO / Bürkert technical guides (generic principle)'],
        'components': {
            'sv_body': C('Contains inlet, main orifice and outlet.', 'Forged/cast body with central seat.', 'Brass, stainless, plastic.', 'Flow direction arrow must be respected.', ['Seat damage from debris'], ['Fit strainer upstream']),
            'sv_diaphragm': C('Main closing element moved by pressure difference.', 'Elastomer diaphragm with bleed and pilot holes.', 'NBR, EPDM, FKM.', 'Needs minimum ΔP to open.', ['Torn diaphragm', 'Blocked bleed hole'], ['Inspect/clean']),
            'sv_tube': C('Pressure-tight guide for the plunger through the coil.', 'Non-magnetic tube welded to bonnet.', 'Stainless steel.', '—', ['Leak'], ['—']),
            'sv_plunger': C('Moved by the magnetic field to open the pilot orifice.', 'Ferromagnetic plunger with seal and return spring.', 'Magnetic stainless.', 'Shading ring prevents AC hum.',
                            ['Sticking (dirt, varnish)'], ['Clean plunger and tube']),
            'sv_coil': C('Produces the magnetic field when energised.', 'Copper winding encapsulated in epoxy with connector.', 'Copper, epoxy.', 'Check voltage and duty cycle.', ['Burn-out (wrong voltage, stuck plunger)'],
                         ['Resistance and insulation check']),
        },
    },
    'three_way_valve': {
        'summary': ('A three-way valve has three ports and either diverts one inlet to one of two outlets or mixes two inlets into one outlet. '
                    'In this L-port ball valve the bottom inlet is connected to outlet A or outlet B by rotating the ball; the lever pointer shows the flow path.'),
        'classification': {'family': 'Rotary (quarter-turn) valve', 'type': 'Three-way ball valve, L-port, diverting (180° switching)'},
        'model_configuration': {'ports': 'Bottom inlet, side outlets A and B', 'alternatives': 'T-port balls; three-way globe control valves (mixing/diverting)'},
        'standards': _std(('ISO 17292 / API 608', 'Metal ball valves', 'Ball valve design.'), ('ASME B16.34', 'Valves — ratings', 'Pressure–temperature ratings.')),
        'references': ['Valve manufacturer port-configuration charts'],
        'components': {
            'tw_body': C('Holds the ball and seats and provides three ports.', 'Cast/forged body with three flanged ends.', 'Stainless/carbon steel.', '—', ['Body leakage'], ['Hydrotest']),
            'tw_seats': C('Seal against the ball.', 'PTFE seat rings.', 'PTFE, RPTFE, PEEK, metal.', 'Temperature-limited for soft seats.', ['Seat wear', 'Cold flow'], ['Seat leak test']),
            'tw_ball': C('Directs flow from the inlet to the selected outlet.', 'Ball with L-shaped bore.', 'Stainless, chrome-plated.', 'Port pattern sets possible flow paths.', ['Scoring'], ['Inspect at overhaul']),
            'tw_stem': C('Turns the ball; the lever shows the position.', 'Blow-out-proof stem and lever.', 'Stainless steel.', '—', ['Stem leak'], ['Adjust packing']),
        },
    },
    'four_way_valve': {
        'summary': ('A four-way directional control valve connects a pressure supply (P) and a return to tank (T) to two actuator ports (A and B). '
                    'Shifting the spool reverses the connections — P→A with B→T, or P→B with A→T — so a double-acting cylinder extends and retracts. '
                    'The same principle is used in pneumatic valves and in refrigeration reversing valves.'),
        'classification': {'family': 'Directional control valve (hydraulic/pneumatic)', 'type': '4/2 spool valve, double solenoid'},
        'model_configuration': {'ports': 'P (pump), T (tank), A, B', 'actuator': 'Double-acting cylinder', 'symbol': 'ISO 1219-1 4/2 valve'},
        'standards': _std(('ISO 4401', 'Hydraulic fluid power — four-port directional control valves — mounting surfaces', 'Subplate interface (CETOP).'),
                          ('ISO 1219-1', 'Fluid power graphic symbols', 'Circuit symbols.')),
        'references': ['Bosch Rexroth / Parker hydraulic training manuals (generic principle)'],
        'components': {
            'fwv_body': C('Contains the spool bore and the P, T, A, B galleries.', 'Machined cast-iron body with annular grooves.', 'Cast iron, steel.', 'Pressure ratings to ~350 bar typical.',
                          ['Internal leakage'], ['Leak-off test']),
            'fwv_spool': C('Its lands open and close the passages between ports.', 'Precision-ground spool with lands.', 'Hardened steel, chrome.', 'Clearance ~ few µm; cleanliness critical.',
                           ['Sticking (silting)', 'Wear → leakage'], ['Oil cleanliness, function test']),
            'fwv_solenoids': C('Push the spool to either end position.', 'Wet-pin solenoids a and b.', 'Copper/steel.', 'Only one coil energised at a time.', ['Coil burn-out'], ['Coil resistance check']),
            'fwv_cylinder': C('Converts oil pressure into linear force.', 'Double-acting cylinder.', 'Steel.', '—', ['Seal leakage'], ['Drift test']),
            'fwv_piston': C('Moves out or in depending on which side is pressurised.', 'Piston with seals and chrome rod.', 'Steel/chrome.', '—', ['Rod scoring'], ['Visual']),
            'fwv_lines': C('Carry oil between pump, tank, valve and cylinder.', 'Steel tube or hose.', 'Steel.', '—', ['Leaks'], ['Visual']),
        },
    },
    'vacuum_relief_valve': {
        'summary': ('A vacuum relief valve protects a tank or vessel from collapsing under vacuum — for example when it is emptied quickly or when hot vapour '
                    'condenses. When the internal pressure falls below the set vacuum, atmospheric pressure pushes the pallet open against its spring '
                    'and air flows in; when the pressures equalise the spring closes it.'),
        'classification': {'family': 'Pressure/vacuum safety device', 'type': 'Spring-loaded vacuum relief (vacuum breaker), roof-mounted'},
        'model_configuration': {'set_point': 'Few mbar below atmospheric for storage tanks (design-specific)', 'related': 'Combined pressure/vacuum relief valves (PVRV) per API 2000'},
        'standards': _std(('API 2000 / ISO 28300', 'Venting of atmospheric and low-pressure storage tanks', 'Sizing of normal and emergency venting.'),
                          ('ASME BPVC VIII', 'Pressure vessels', 'Vacuum design of vessels.')),
        'references': ['Tank venting manufacturer guides (Protego, Groth — generic)'],
        'components': {
            'vr_roof': C('Tank roof nozzle on which the valve is mounted.', 'Flanged nozzle.', 'Steel.', '—', ['Corrosion'], ['Visual']),
            'vr_body': C('Holds the seat and guides the pallet.', 'Cylindrical body with seat ring.', 'Stainless, aluminium, carbon steel.', '—', ['Seat fouling'], ['Clean seat']),
            'vr_hood': C('Keeps out rain, birds and debris while letting air in.', 'Hood with mesh screen.', 'Stainless.', 'Blocked screen stops the valve working.', ['Screen blockage, icing'], ['Inspect screen']),
            'vr_pallet': C('Opens inward when the tank is under vacuum.', 'Disc with soft seal on a guided stem.', 'Stainless + PTFE/FEP.', 'Sticking pallets can cause tank collapse.', ['Sticking (polymer, ice)'], ['Function test']),
            'vr_spring': C('Sets the vacuum at which the pallet opens.', 'Bridge and compression spring.', 'Stainless.', 'Set pressure must not exceed the tank vacuum rating.', ['Corrosion'], ['Set check']),
        },
    },
}

BUILDERS = {'needle_valve': needle_valve, 'pinch_valve': pinch_valve, 'float_valve': float_valve, 'foot_valve': foot_valve,
            'solenoid_valve': solenoid_valve, 'three_way_valve': three_way_valve, 'four_way_valve': four_way_valve,
            'vacuum_relief_valve': vacuum_relief_valve}
