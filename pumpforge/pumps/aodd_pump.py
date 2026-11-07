"""
Air-Operated Double-Diaphragm (AODD) Pump — metallic, bolted construction.
Two liquid chambers either side of a centre section; diaphragms joined by a
common shaft; air valve (spool) on top of the centre section alternately
pressurises the air side of each diaphragm.  Four ball check valves:
inlet balls at the bottom of each chamber, outlet balls at the top.
Inlet manifold at the bottom (centre front port), discharge manifold on top.

Diaphragm axis = Blender X.  Shaft moving +X => right chamber discharging,
left chamber filling.
"""
import math
from pumpforge.core import (recalc_normals, Model, lathe, lathe_split, ring_profile, cyl, box, csg, split, join, move,
                            rotate, bolt_circle, hex_prism, merge_halves, split_faces, group_by, TAU,
                            OPERATE_FRAMES)
from pumpforge.shapes import sweep_tube

ID = 'aodd_pump'
ZC = 0.34            # diaphragm axis height
XF = 0.075           # centre-section clamp face
XP = 0.125           # check-valve port axis (x)
ST = 0.012           # half stroke (display)
Z_IN = 0.09          # inlet manifold axis
Z_OUT = ZC + 0.25    # discharge manifold axis
Z_SEAT_IN = ZC - 0.19
Z_SEAT_OUT = ZC + 0.19
RB = 0.021           # ball radius

SHAFT = [(0.0, 0.0), (0.25, ST), (0.5, 0.0), (0.75, -ST), (1.0, 0.0)]      # triangle-wave stroke


def ball_keys(up_when_plus, lift):
    a, b = (lift, 0.0) if up_when_plus else (0.0, lift)
    return [(0.0, (0, 0, a)), (0.23, (0, 0, a)), (0.27, (0, 0, b)), (0.73, (0, 0, b)), (0.77, (0, 0, a)),
            (1.0, (0, 0, a))]


def build(out_dir):
    m = Model(ID, 'Air-Operated Double-Diaphragm (AODD) Pump',
              'C · Reciprocating Positive-Displacement Pumps', META)

    # ================= CENTRE SECTION =====================================
    cs_prof = [(0.017, -0.055), (0.095, -0.055), (0.1, -0.07), (0.1, -XF), (0.135, -XF), (0.135, -0.06),
               (0.115, -0.05), (0.115, 0.05), (0.135, 0.06), (0.135, XF), (0.1, XF), (0.1, 0.07),
               (0.095, 0.055), (0.017, 0.055)]
    cs = csg('centre_section', [
        lathe('cs', cs_prof, 'thermoplastic', 96, axis='X', center=(0, 0, ZC)),
        box('cs_pad', (0.13, 0.1, 0.05), (0, 0, ZC + 0.11), 'thermoplastic', bevel=0.004),
    ], [
        cyl('air_d1', 0.006, ZC + 0.05, ZC + 0.14, 'thermoplastic', 20, center=(0.064, 0, 0)),
        cyl('air_d2', 0.006, ZC + 0.05, ZC + 0.14, 'thermoplastic', 20, center=(-0.064, 0, 0)),
        cyl('pilot_bore', 0.0065, -0.08, 0.08, 'thermoplastic', 20, axis='X', center=(0, 0, ZC + 0.075)),
    ], 'thermoplastic')
    p = m.part('centre_section', 'Centre Section (Air Chamber Block)', 'air_side', section='split')
    p.add_split(*split(cs), smooth_angle=40)
    p = m.part('shaft_bushing', 'Shaft Bushing', 'air_side', section='split', explode=(0, -0.12, 0.0))
    p.add_split(*lathe_split('shaft_bushing', ring_profile(0.0125, 0.017, -0.055, 0.055), 'bronze', 40,
                             axis='X', center=(0, 0, ZC)))

    # ================= AIR VALVE ==========================================
    zv = ZC + 0.16
    av = csg('air_valve', [
        box('av_body', (0.13, 0.09, 0.055), (0, 0, zv), 'aluminium', bevel=0.005),
        cyl('av_cap1', 0.024, 0.062, 0.075, 'aluminium', 48, axis='X', center=(0, 0, zv), ch=0.002),
        cyl('av_cap2', 0.024, -0.075, -0.062, 'aluminium', 48, axis='X', center=(0, 0, zv), ch=0.002),
        cyl('av_inlet', 0.014, -0.075, -0.044, 'brass', 6, axis='Y', center=(0, 0, zv)),
    ], [
        cyl('av_bore', 0.0155, -0.068, 0.068, 'aluminium', 40, axis='X', center=(0, 0, zv)),
        cyl('av_in_bore', 0.007, -0.09, 0.0, 'aluminium', 20, axis='Y', center=(0, 0, zv)),
        cyl('av_p1', 0.006, ZC + 0.12, zv, 'aluminium', 20, center=(0.035, 0, 0)),
        cyl('av_p2', 0.006, ZC + 0.12, zv, 'aluminium', 20, center=(-0.035, 0, 0)),
    ], 'aluminium')
    avb, avf = split(av)
    bolts = split_faces(join('av_bolts', [cyl(f'avb{i}', 0.0065, zv + 0.0275, zv + 0.034, 'steel_dark', 20,
                                              center=(sx * 0.05, sy * 0.032, 0), ch=0.001)
                                          for i, (sx, sy) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1)))]),
                        'y', 0.0)
    p = m.part('air_valve', 'Air Valve Body', 'air_side', section='split', explode=(0, 0, 0.17))
    p.add_split(*merge_halves('air_valve', [(avb, avf), bolts]), smooth_angle=40)

    spool = lathe('spool', [(0, -0.05), (0.015, -0.05), (0.015, -0.035), (0.009, -0.033), (0.009, -0.012),
                            (0.015, -0.01), (0.015, 0.01), (0.009, 0.012), (0.009, 0.033), (0.015, 0.035),
                            (0.015, 0.05), (0, 0.05)], 'stainless', 40, axis='X', center=(0, 0, zv))
    p = m.part('air_valve_spool', 'Air Valve Spool', 'air_side', explode=(0, -0.13, 0.17))
    p.add(spool)
    d = 0.008
    p.cycle_translate([(0, (d, 0, 0)), (0.23, (d, 0, 0)), (0.27, (-d, 0, 0)), (0.73, (-d, 0, 0)),
                       (0.77, (d, 0, 0)), (1.0, (d, 0, 0))])

    pil = cyl('pilot', 0.0055, -0.083, 0.083, 'stainless', 20, axis='X', center=(0, 0, ZC + 0.075), ch=0.001)
    p = m.part('pilot_valve', 'Pilot Shaft (Pilot Valve)', 'air_side', explode=(0, -0.22, 0.05))
    p.add(pil)

    muf = [cyl('muf_body', 0.026, 0.045, 0.15, 'thermoplastic', 40, axis='Y', center=(0, 0, zv), ch=0.004)]
    for i in range(6):
        y0 = 0.065 + i * 0.013
        muf.append(cyl(f'muf_r{i}', 0.0285, y0, y0 + 0.004, 'thermoplastic', 40, axis='Y', center=(0, 0, zv)))
    p = m.part('muffler', 'Exhaust Muffler', 'air_side', explode=(0, 0.2, 0.17))
    p.add(join('muffler', muf))

    # ================= SHAFT & DIAPHRAGM PLATES ===========================
    sh = cyl('shaft', 0.0125, -0.1, 0.1, 'stainless', 32, axis='X', center=(0, 0, ZC), ch=0.002)
    p = m.part('diaphragm_shaft', 'Diaphragm Shaft (Connecting Rod)', 'reciprocating', explode=(0, -0.28, 0))
    p.add(sh)
    p.cycle_translate([(t, (x, 0, 0)) for t, x in SHAFT])

    for side, sx in (('left', -1), ('right', 1)):
        xi = sx * (XF + 0.0003)
        inner = lathe(f'ip_{side}', [(0.0125, 0.0), (0.05, 0.0), (0.052, 0.003), (0.052, 0.006), (0.0125, 0.008)],
                      'aluminium', 64, axis='X', center=(xi, 0, ZC))
        if sx > 0:
            inner.data.transform(__import__('mathutils').Matrix.Scale(-1, 4, (1, 0, 0)))
            inner.data.transform(__import__('mathutils').Matrix.Translation((2 * xi, 0, 0)))
            recalc_normals(inner)
        p = m.part(f'inner_plate_{side}', f'Inner Diaphragm Plate – {side.title()}', 'reciprocating',
                   explode=(sx * 0.11, 0, 0), info={'ref': 'inner_plate'})
        p.add(inner)
        p.cycle_translate([(t, (x, 0, 0)) for t, x in SHAFT])

        xo = sx * (XF + 0.0065)
        outer = [lathe(f'op_{side}', [(0.0, 0.0), (0.05, 0.0), (0.05, 0.004), (0.035, 0.012), (0.0, 0.012)],
                       'stainless', 64, axis='X', center=(xo, 0, ZC)),
                 hex_prism(f'opn_{side}', 0.022, 0.012, 0.024, 'steel_dark', axis='X', center=(xo, 0, ZC))]
        o = join(f'outer_plate_{side}', outer)
        if sx < 0:
            import mathutils
            o.data.transform(mathutils.Matrix.Translation((xo, 0, 0)) @ mathutils.Matrix.Scale(-1, 4, (1, 0, 0))
                             @ mathutils.Matrix.Translation((-xo, 0, 0)))
            recalc_normals(o)
        p = m.part(f'outer_plate_{side}', f'Outer Diaphragm Plate & Nut – {side.title()}', 'reciprocating',
                   explode=(sx * 0.33, 0, 0), info={'ref': 'outer_plate'})
        p.add(o)
        p.cycle_translate([(t, (x, 0, 0)) for t, x in SHAFT])

        # ---- diaphragm with convolution, morph targets for flexing
        h = [(0.0125, 0.0), (0.06, 0.0), (0.075, 0.004), (0.087, 0.008), (0.097, 0.004), (0.1, 0.001),
             (0.135, 0.001), (0.135, 0.007), (0.1, 0.007), (0.097, 0.01), (0.087, 0.014), (0.075, 0.01),
             (0.06, 0.006), (0.0125, 0.006)]
        prof = [(r, sx * (XF + 0.0005 + x)) for r, x in h]
        db, df = lathe_split(f'diaphragm_{side}', prof, 'rubber', 96, axis='X', center=(0, 0, ZC))
        p = m.part(f'diaphragm_{side}', f'Diaphragm – {side.title()}', 'reciprocating', section='split',
                   explode=(sx * 0.2, 0, 0), info={'ref': 'diaphragm'})
        p.add_split(db, df, smooth_angle=60)
        for mesh in p.meshes:
            add_flex_keys(mesh)
            m.morph(mesh, 'shaft_plus', 'Operate', [(1 + OPERATE_FRAMES * t, max(0, x / ST)) for t, x in SHAFT])
            m.morph(mesh, 'shaft_minus', 'Operate', [(1 + OPERATE_FRAMES * t, max(0, -x / ST)) for t, x in SHAFT])

        # ---- liquid chamber (dome) with check-valve ports
        xc = sx * XP
        dome_out = [(0.0, 0.17), (0.06, 0.165), (0.1, 0.148), (0.125, 0.125), (0.138, 0.1), (0.142, 0.097),
                    (0.142, XF + 0.007), (0.0, XF + 0.007)]
        dome_in = [(0.0, 0.158), (0.06, 0.154), (0.095, 0.139), (0.115, 0.118), (0.122, 0.1), (0.1, XF + 0.003),
                   (0.0, XF + 0.003)]
        flip = lambda pr: [(r, sx * x) for r, x in pr]
        ch = csg(f'chamber_{side}', [
            lathe('d_out', flip(dome_out), 'aluminium', 96, axis='X', center=(0, 0, ZC)),
            lathe('d_fl', flip([(0.0, XF + 0.007), (0.142, XF + 0.007), (0.142, XF + 0.019), (0.0, XF + 0.019)]),
                  'aluminium', 96, axis='X', center=(0, 0, ZC)),
            cyl('boss_lo', 0.036, Z_SEAT_IN, ZC - 0.07, 'aluminium', 48, center=(xc, 0, 0)),
            cyl('fl_lo', 0.058, Z_SEAT_IN, Z_SEAT_IN + 0.012, 'aluminium', 48, center=(xc, 0, 0), ch=0.002),
            cyl('boss_hi', 0.036, ZC + 0.07, Z_SEAT_OUT, 'aluminium', 48, center=(xc, 0, 0)),
            cyl('fl_hi', 0.058, Z_SEAT_OUT - 0.012, Z_SEAT_OUT, 'aluminium', 48, center=(xc, 0, 0), ch=0.002),
        ], [
            lathe('d_in', flip(dome_in), 'aluminium', 96, axis='X', center=(0, 0, ZC)),
            cyl('cage_lo', 0.025, Z_SEAT_IN - 0.01, ZC - 0.09, 'aluminium', 48, center=(xc, 0, 0)),
            cyl('port_lo', 0.019, ZC - 0.1, ZC - 0.04, 'aluminium', 48, center=(xc, 0, 0)),
            cyl('port_hi', 0.019, ZC + 0.04, Z_SEAT_OUT + 0.01, 'aluminium', 48, center=(xc, 0, 0)),
        ], 'aluminium')
        cb, cf = split(ch)
        fb = bolt_circle(f'ch_bolts_{side}', 8, 0.25, 0.019, sx * (XF + 0.019), sx * (XF + 0.03), axis='X',
                         center=(0, 0, ZC), phase=math.pi / 8, stud=(0.012, sx * (XF + 0.015), sx * (XF + 0.036)))
        fbb, fbf = split_faces(fb, 'y', 0.0)
        p = m.part(f'chamber_{side}', f'Liquid Chamber – {side.title()}', 'wetted_casing', section='split',
                   explode=(sx * 0.28, 0, 0), info={'ref': 'liquid_chamber'})
        p.add_split(join(f'ch_b_{side}', [cb, fbb]), join(f'ch_f_{side}', [cf, fbf]), smooth_angle=40)

        # ---- check-valve seats & balls
        for kind, zs, up_plus in (('inlet', Z_SEAT_IN, sx < 0), ('outlet', Z_SEAT_OUT, sx > 0)):
            if kind == 'outlet':
                seat = [(0.0165, zs), (0.033, zs), (0.033, zs + 0.008), (0.021, zs + 0.008), (0.0165, zs + 0.005)]
            else:
                seat = [(0.0165, zs - 0.008), (0.033, zs - 0.008), (0.033, zs), (0.021, zs), (0.0165, zs - 0.003)]
            sb_, sf_ = lathe_split(f'seat_{kind}_{side}', seat, 'stainless', 48, center=(xc, 0, 0))
            ez = -0.17 if kind == 'inlet' else 0.2
            p = m.part(f'seat_{kind}_{side}', f'Valve Seat – {kind.title()}, {side.title()}', 'check_valves',
                       section='split', explode=(sx * 0.28, 0, ez), info={'ref': 'valve_seat'})
            p.add_split(sb_, sf_)
            top = zs if kind == 'inlet' else zs + 0.008
            zb = top + math.sqrt(RB ** 2 - 0.0185 ** 2) - 0.0
            prof = [(RB * math.sin(t * math.pi / 16), zb - RB * math.cos(t * math.pi / 16)) for t in range(17)]
            ball = lathe(f'ball_{kind}_{side}', prof, 'ptfe', 40, center=(xc, 0, 0))
            p = m.part(f'ball_{kind}_{side}', f'Check Ball – {kind.title()}, {side.title()}', 'check_valves',
                       explode=(sx * 0.28, 0, ez * 0.55), info={'ref': 'check_ball'})
            p.add(ball, smooth_angle=80)
            p.cycle_translate(ball_keys(up_plus, 0.014))

    # ================= MANIFOLDS ==========================================
    def manifold(name, z, z_seat, port_dir, mat='aluminium'):
        up = z_seat > z
        rz0, rz1 = (z, z_seat - 0.008) if up else (z_seat + 0.008, z)
        outs = [lathe(name + '_pipe', [(0, -0.19), (0.032, -0.19), (0.04, -0.182), (0.04, 0.182), (0.032, 0.19),
                                       (0, 0.19)], mat, 64, axis='X', center=(0, 0, z))]
        ins = [lathe(name + '_bore', [(0, -0.17), (0.028, -0.168), (0.028, 0.168), (0, 0.17)], mat, 64, axis='X',
                     center=(0, 0, z))]
        for s_ in (-1, 1):
            outs.append(cyl(f'{name}_r{s_}', 0.036, min(rz0, rz1), max(rz0, rz1), mat, 48, center=(s_ * XP, 0, 0)))
            f0 = rz1 - 0.012 if up else rz0
            outs.append(cyl(f'{name}_f{s_}', 0.058, f0, f0 + 0.012, mat, 48, center=(s_ * XP, 0, 0), ch=0.002))
            if up:   # inlet riser: plain bore up to the seat
                ins.append(cyl(f'{name}_rb{s_}', 0.019, z, rz1 + 0.01, mat, 48, center=(s_ * XP, 0, 0)))
            else:    # discharge riser: ball cage above the seat
                ins.append(cyl(f'{name}_rb{s_}', 0.026, rz0 - 0.01, z, mat, 48, center=(s_ * XP, 0, 0)))
        if port_dir == 'front':
            outs += [cyl(name + '_port', 0.036, -0.11, 0.0, mat, 48, axis='Y', center=(0, 0, z)),
                     cyl(name + '_pfl', 0.058, -0.122, -0.106, mat, 64, axis='Y', center=(0, 0, z), ch=0.002)]
            ins.append(cyl(name + '_pb', 0.026, -0.14, 0.0, mat, 48, axis='Y', center=(0, 0, z)))
        else:
            outs += [cyl(name + '_port', 0.036, z, z + 0.1, mat, 48),
                     cyl(name + '_pfl', 0.058, z + 0.088, z + 0.104, mat, 64, ch=0.002)]
            ins.append(cyl(name + '_pb', 0.026, z, z + 0.12, mat, 48))
        if not up:
            pass
        else:
            for s_ in (-1, 1):  # feet
                outs.append(box(f'{name}_leg{s_}', (0.05, 0.05, z - 0.012), (s_ * 0.16, 0, (z - 0.012) / 2 + 0.012),
                                mat, bevel=0.004))
                outs.append(box(f'{name}_foot{s_}', (0.075, 0.2, 0.014), (s_ * 0.16, 0, 0.007), mat, bevel=0.003))
        return csg(name, outs, ins, mat)

    imf = manifold('inlet_manifold', Z_IN, Z_SEAT_IN, 'front')
    ib, if_ = split(imf)
    pb = [bolt_circle(f'imb{s}', 4, 0.1, 0.014, Z_SEAT_IN - 0.02, Z_SEAT_IN - 0.028, center=(s * XP, 0, 0),
                      phase=math.pi / 4, stud=(0.01, Z_SEAT_IN - 0.016, Z_SEAT_IN - 0.034)) for s in (-1, 1)]
    pb.append(bolt_circle('imp', 4, 0.09, 0.016, -0.106, -0.098, axis='Y', center=(0, 0, Z_IN), phase=math.pi / 4))
    pbb, pbf = split_faces(join('im_bolts', pb), 'y', 0.0)
    p = m.part('inlet_manifold', 'Inlet (Suction) Manifold', 'wetted_casing', section='split',
               explode=(0, 0, -0.3))
    p.add_split(join('im_b', [ib, pbb]), join('im_f', [if_, pbf]), smooth_angle=40)

    dmf = manifold('discharge_manifold', Z_OUT, Z_SEAT_OUT, 'top')
    db_, df_ = split(dmf)
    pb = [bolt_circle(f'dmb{s}', 4, 0.1, 0.014, Z_SEAT_OUT + 0.02, Z_SEAT_OUT + 0.028, center=(s * XP, 0, 0),
                      phase=math.pi / 4, stud=(0.01, Z_SEAT_OUT + 0.016, Z_SEAT_OUT + 0.034)) for s in (-1, 1)]
    pbb, pbf = split_faces(join('dm_bolts', pb), 'y', 0.0)
    p = m.part('discharge_manifold', 'Discharge Manifold', 'wetted_casing', section='split',
               explode=(0, 0, 0.42))
    p.add_split(join('dm_b', [db_, pbb]), join('dm_f', [df_, pbf]), smooth_angle=40)

    # ================= FLOW PATHS =========================================
    Y = 0.01
    for sx in (-1, 1):
        xc = sx * XP
        m.flow(f'suction_{sx:+d}', [(0, -0.22, Z_IN), (0, -0.03, Z_IN), (sx * 0.04, Y, Z_IN), (xc * 0.85, Y, Z_IN),
                                     (xc, Y, Z_IN + 0.03), (xc, Y, Z_SEAT_IN + 0.04), (xc, Y, ZC - 0.1),
                                     (sx * 0.12, Y, ZC - 0.06), (sx * 0.112, Y, ZC - 0.02)],
               'flow_suction', 0.0045, 0.08)
        m.flow(f'discharge_{sx:+d}', [(sx * 0.112, Y, ZC + 0.02), (sx * 0.12, Y, ZC + 0.06), (xc, Y, ZC + 0.1),
                                       (xc, Y, Z_SEAT_OUT + 0.03), (xc, Y, Z_OUT - 0.01), (xc * 0.7, Y, Z_OUT),
                                       (sx * 0.03, Y, Z_OUT), (0, Y, Z_OUT + 0.03), (0, Y, Z_OUT + 0.17)],
               'flow_discharge', 0.0045, 0.08)
    m.flow('air_supply', [(0, -0.16, zv), (0, -0.05, zv), (0.02, Y, zv), (0.035, Y, zv - 0.02),
                          (0.035, Y, ZC + 0.125), (0.064, Y, ZC + 0.12), (0.064, Y, ZC + 0.06), (0.068, Y, ZC + 0.03)],
           'air', 0.0035, 0.05)
    m.flow('air_exhaust', [(-0.068, Y, ZC + 0.03), (-0.064, Y, ZC + 0.06), (-0.064, Y, ZC + 0.12),
                           (-0.035, Y, ZC + 0.125), (-0.035, Y, zv - 0.02), (-0.01, 0.03, zv), (0, 0.1, zv),
                           (0, 0.19, zv)], 'air', 0.0035, 0.05)
    return m.export(out_dir)


def add_flex_keys(obj):
    """Morph targets: centre of diaphragm follows the plates, rim stays clamped."""
    me = obj.data
    if not me.shape_keys:
        obj.shape_key_add(name='Basis', from_mix=False)
    for name, sgn in (('shaft_plus', 1), ('shaft_minus', -1)):
        k = obj.shape_key_add(name=name, from_mix=False)
        for i, v in enumerate(me.vertices):
            r = math.hypot(v.co.y, v.co.z - ZC)
            if r <= 0.055:
                f = 1.0
            elif r >= 0.1:
                f = 0.0
            else:
                t = (r - 0.055) / 0.045
                f = 1 - t * t * (3 - 2 * t)
            k.data[i].co = (v.co.x + sgn * ST * f, v.co.y, v.co.z)


META = {
    'summary': ('Compressed air, switched by an air valve, alternately pressurises the air side of two '
                'flexible diaphragms joined by a shaft. The pressurised diaphragm pushes liquid out of its '
                'chamber through the upper (outlet) ball check, while the other diaphragm is pulled inward, '
                'drawing liquid in through its lower (inlet) ball check. At the end of each stroke a pilot '
                'shifts the air valve and the cycle reverses. Discharge pressure cannot exceed air supply '
                'pressure (1:1 ratio pumps), so the pump simply stalls against a closed valve.'),
    'classification': {
        'family': 'Positive displacement – reciprocating',
        'configuration': 'Double diaphragm, pneumatically driven, mechanically connected diaphragms',
        'valves': 'Ball check valves (flap valves are an alternative for large solids)',
    },
    'model_configuration': {
        'diaphragm': 'Moulded elastomer with convolution (PTFE overlay versions exist)',
        'materials_shown': 'Aluminium wetted castings, stainless plates/seats, PTFE balls, polymer centre section',
        'stroke_display': f'±{ST*1000:.0f} mm (animated); real stroke is size- and design-dependent',
        'cycle_note': 'Air valve and pilot arrangements vary by manufacturer; the spool shown is a generic representation.',
    },
    'standards': [
        {'id': 'ANSI/HI 10.1-10.5', 'title': 'Air-Operated Pumps for Nomenclature, Definitions, Application, and Operation',
         'relevance': 'Terminology, application and operation of AODD pumps.', 'edition': 'to be verified'},
        {'id': 'ANSI/HI 10.6', 'title': 'Air-Operated Pump Tests', 'relevance': 'Performance test methods.',
         'edition': 'to be verified'},
        {'id': 'ATEX 2014/34/EU', 'title': 'EU directive – equipment for potentially explosive atmospheres',
         'relevance': 'Conductive/groundable AODD versions are offered for hazardous areas; confirm certification per pump.',
         'edition': 'Directive 2014/34/EU'},
        {'id': 'EN ISO 80079-36/-37', 'title': 'Non-electrical equipment for explosive atmospheres',
         'relevance': 'Basis for ATEX certification of non-electrical pumps.', 'edition': 'to be verified'},
    ],
    'references': [
        'Hydraulic Institute ANSI/HI 10.1-10.5 (air-operated pumps).',
        'Manufacturer AODD engineering/operation manuals (generic practice).',
    ],
    'components': {
        'centre_section': {
            'function': 'Separates the two air chambers, guides the shaft and pilot, and carries the air valve and muffler.',
            'construction': 'Cast or moulded block; each face is dished to form the air chamber behind its diaphragm; drilled passages connect the air valve to each chamber.',
            'material': 'Aluminium, polypropylene, acetal or conductive polymers; not wetted by the pumped liquid unless a diaphragm fails.',
            'operating_conditions': 'Air supply pressure (commonly up to ~7–8.6 bar / 100–125 psi depending on model; check rating).',
            'failure_modes': ['Pumped liquid in the air side after diaphragm rupture', 'Shaft bore wear causing air leakage', 'Icing from air expansion'],
            'inspection': ['Check exhaust for liquid (diaphragm leak)', 'Shaft bushing wear', 'Air leak test'],
        },
        'shaft_bushing': {
            'function': 'Guides the diaphragm shaft and limits air leakage between the two air chambers.',
            'construction': 'Plain bushing with or without seals.',
            'material': 'Bronze, acetal, PTFE-based.',
            'operating_conditions': 'Lubricated by air-line lubricant where used; many designs are lube-free.',
            'failure_modes': ['Wear causing air bypass and stalling'],
            'inspection': ['Clearance at overhaul'],
        },
        'air_valve': {
            'function': 'Directs supply air to one air chamber while venting the other to exhaust; reverses at each stroke end.',
            'construction': 'Valve body with a shifting spool (or shuttle), end caps and air inlet connection; shifted by pilot air.',
            'material': 'Aluminium, polymer, brass; elastomer seals.',
            'operating_conditions': 'Requires clean, dry, regulated air; icing can occur at low air temperature/high humidity.',
            'failure_modes': ['Stalling (spool stuck at centre)', 'Icing of exhaust/valve', 'Worn seals causing air bypass'],
            'inspection': ['Air filter/regulator condition', 'Spool and seal wear', 'Exhaust for ice or liquid'],
        },
        'air_valve_spool': {
            'function': 'Moves between two positions to switch the air path.',
            'construction': 'Lands and grooves forming air ports; shown here as a generic two-position spool.',
            'material': 'Stainless steel, aluminium or polymer.',
            'operating_conditions': 'Shifts once per stroke.',
            'failure_modes': ['Sticking from contaminated air', 'Seal wear'],
            'inspection': ['Free movement; seal condition'],
        },
        'pilot_valve': {
            'function': 'Senses end of stroke (contacted by the inner diaphragm plates) and sends pilot air to shift the main air valve.',
            'construction': 'Small shaft/sleeve with seals through the centre section.',
            'material': 'Stainless steel, polymer sleeves.',
            'operating_conditions': 'Actuated mechanically each stroke.',
            'failure_modes': ['Seal wear causing erratic stroking', 'Sticking'],
            'inspection': ['Seal condition and free movement'],
        },
        'muffler': {
            'function': 'Reduces exhaust noise.',
            'construction': 'Porous polymer or sintered element; can be piped away to route exhaust if a diaphragm fails.',
            'material': 'Polypropylene, sintered bronze or polymer.',
            'operating_conditions': 'Exhaust air is cold (expansion) and may contain oil mist.',
            'failure_modes': ['Clogging causing loss of speed', 'Icing'],
            'inspection': ['Clean or replace when restricted'],
        },
        'diaphragm_shaft': {
            'function': 'Connects the two diaphragms so one discharges while the other fills.',
            'construction': 'Straight shaft with threaded ends for the diaphragm plates.',
            'material': 'Stainless steel or carbon steel.',
            'operating_conditions': 'Reciprocates once per cycle; carries pressure difference across the diaphragm.',
            'failure_modes': ['Thread wear', 'Fatigue', 'Bushing wear'],
            'inspection': ['Thread condition; straightness'],
        },
        'inner_plate': {
            'function': 'Supports the diaphragm on the air side and contacts the pilot at stroke end.',
            'construction': 'Formed or cast plate clamped on the shaft.',
            'material': 'Aluminium, polymer or steel.',
            'operating_conditions': 'Air side.',
            'failure_modes': ['Sharp edges cutting the diaphragm'],
            'inspection': ['Edges and fit'],
        },
        'outer_plate': {
            'function': 'Clamps the diaphragm centre on the liquid side.',
            'construction': 'Plate and nut/bolt on the shaft end; integral-plate diaphragms eliminate this wetted part.',
            'material': 'Matches wetted materials (stainless, aluminium, polymers).',
            'operating_conditions': 'Wetted.',
            'failure_modes': ['Corrosion', 'Loosening'],
            'inspection': ['Torque per manufacturer at reassembly'],
        },
        'diaphragm': {
            'function': 'Flexible membrane that separates air from liquid and displaces liquid as it moves.',
            'construction': 'Moulded convoluted elastomer clamped at its rim between chamber and centre section; PTFE versions often use a rubber backup diaphragm.',
            'material': 'Neoprene, Buna-N (NBR), EPDM, Viton (FKM), thermoplastic elastomers (e.g. Santoprene), PTFE; choose by chemical compatibility, temperature and abrasion.',
            'operating_conditions': 'Flex life depends on stroke rate, pressure, temperature and fluid.',
            'failure_modes': ['Fatigue rupture (liquid appears at exhaust)', 'Chemical swelling/softening', 'Abrasion', 'Over-pressurisation'],
            'inspection': ['Replace on a time/cycle basis', 'Monitor exhaust for liquid; leak detectors available'],
        },
        'liquid_chamber': {
            'function': 'Contains the liquid on the outside of each diaphragm and carries the check-valve ports.',
            'construction': 'Domed casting bolted (or clamped with a band) to the centre section, with inlet port at the bottom and outlet port at the top.',
            'material': 'Aluminium, cast iron, stainless steel, polypropylene, PVDF, conductive acetal.',
            'operating_conditions': 'Wetted; pressure up to the air supply pressure.',
            'failure_modes': ['Corrosion/erosion', 'Leakage at clamp from loose bolts'],
            'inspection': ['Bolt torque', 'Surface condition'],
        },
        'valve_seat': {
            'function': 'Sealing surface for the check ball.',
            'construction': 'Replaceable ring clamped between chamber and manifold with O-rings.',
            'material': 'Stainless steel, aluminium, polymers, elastomers.',
            'operating_conditions': 'Repeated ball impact each stroke.',
            'failure_modes': ['Wear/erosion leading to back-flow and reduced flow', 'Trapped solids holding the ball open'],
            'inspection': ['Seat edge condition'],
        },
        'check_ball': {
            'function': 'One-way valve: lifts to admit or discharge liquid, seats to block back-flow.',
            'construction': 'Solid sphere inside a cage formed by the chamber/manifold.',
            'material': 'PTFE, Neoprene, Buna-N, EPDM, Viton, stainless steel; weighted balls for viscous duties.',
            'operating_conditions': 'Inlet balls lift on the suction stroke; outlet balls lift on the discharge stroke.',
            'failure_modes': ['Wear (ball diameter reduction)', 'Chemical swelling causing sticking', 'Solids preventing seating'],
            'inspection': ['Measure ball diameter against manufacturer limit'],
        },
        'inlet_manifold': {
            'function': 'Distributes suction flow to both chambers and carries the pump feet.',
            'construction': 'Cast manifold with central suction port, risers to the inlet seats, and mounting feet.',
            'material': 'As liquid chambers.',
            'operating_conditions': 'Suction pressure; AODD pumps can self-prime and run dry without damage (per manufacturer limits).',
            'failure_modes': ['Air leaks at gaskets reducing suction lift', 'Sediment build-up'],
            'inspection': ['Gasket/O-ring condition'],
        },
        'discharge_manifold': {
            'function': 'Combines discharge from both chambers into one outlet; holds the outlet ball cages.',
            'construction': 'Cast manifold with risers to the outlet seats and a central discharge port.',
            'material': 'As liquid chambers.',
            'operating_conditions': 'Pulsating flow; a pulsation dampener is often fitted downstream.',
            'failure_modes': ['Leakage at seat gaskets', 'Fatigue from pulsation if piping unsupported'],
            'inspection': ['Gasket/O-ring condition', 'Piping supports'],
        },
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
