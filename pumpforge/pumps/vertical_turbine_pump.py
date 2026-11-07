"""
Vertical Turbine Pump (line-shaft, wet-pit, open line-shaft, product-lubricated)
3-stage mixed-flow bowl assembly, flanged column, cast discharge head with
above-ground discharge, mechanical seal, adjustable spacer coupling and a
vertical solid-shaft (VSS) induction motor.

Representative arrangement: API 610 type VS1 / ANSI/HI 2.1-2.2 "deep-well
turbine" nomenclature.  Column length is shortened for display (2 x 0.8 m).
Blender Z-up metres; ground (head sole) at z = 0.
"""
import math
from mathutils import Vector
from pumpforge.core import (Model, lathe, lathe_split, ring_profile, cyl, box, csg, split,
                            join, move, rotate, bolt_circle, hex_prism, TAU, M)
from pumpforge.shapes import vane, sweep_tube

ID = 'vertical_turbine_pump'
H = 0.26            # bowl (stage) height
N_STAGES = 3
Z_DC_TOP = -1.60    # top of discharge case (bottom of column)
Z_DC_BOT = Z_DC_TOP - 0.26
Z_BELL = Z_DC_BOT - N_STAGES * H   # bottom face of lowest bowl
R_SH = 0.0215       # line/bowl shaft radius (≈ 43 mm shaft)
SPREAD = 0.35       # vertical explode factor
X_ROT = 0.80        # lateral explode offset for the rotating element
X_INT = -0.70       # lateral explode offset for stationary internals


def ex(z, dx=0.0):
    return (dx, 0.0, SPREAD * z)


def sides(objs, name):
    """Group separate closed objects into (back, front) by centroid y."""
    b, f = [], []
    for o in objs:
        cy = sum(v.co.y for v in o.data.vertices) / max(1, len(o.data.vertices))
        (b if cy > 0 else f).append(o)
    return (join(name + '__b', b) if b else None, join(name + '__f', f) if f else None)


def merge_halves(name, pairs):
    backs = [p[0] for p in pairs if p[0] is not None]
    fronts = [p[1] for p in pairs if p[1] is not None]
    return join(name + '__back', backs), join(name + '__front', fronts)


def radial_rib(name, r0, r1, z0, z1, ang, t, mat):
    o = box(name, (r1 - r0, t, z1 - z0), ((r0 + r1) / 2, 0, (z0 + z1) / 2), mat)
    return rotate(o, ang)


def nut_ring_split(name, n, pcd, af, h0, h1, axis='Z', center=(0, 0, 0)):
    o = bolt_circle(name, n, pcd, af, h0, h1, axis=axis, center=center,
                    stud=(af * 0.62, h0 - 0.004 if h1 > h0 else h0 + 0.004, h1 + 0.012 if h1 > h0 else h1 - 0.012))
    # separate into individual islands by side
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(o.data)
    back = [f for f in bm.faces if f.calc_center_median().y > 0]
    front_faces = [f for f in bm.faces if f.calc_center_median().y <= 0]
    bm2 = bm.copy()
    bmesh.ops.delete(bm, geom=front_faces, context='FACES')
    bm2.faces.ensure_lookup_table()
    bmesh.ops.delete(bm2, geom=[f for f in bm2.faces if f.calc_center_median().y > 0], context='FACES')
    from pumpforge.core import _link
    import bpy
    out = []
    for tag, b in (('b', bm), ('f', bm2)):
        me = bpy.data.meshes.new(name + tag)
        b.to_mesh(me)
        b.free()
        me.materials.append(M('steel_dark'))
        out.append(_link(bpy.data.objects.new(name + tag, me)))
    from pumpforge.core import delete
    delete(o)
    return out[0], out[1]


# ---------------------------------------------------------------------------
def build(out_dir):
    m = Model(ID, 'Vertical Turbine Pump (Line-Shaft, 3-Stage)',
              'A · Centrifugal & Special Hydraulic Pumps', META)

    # ================= DISCHARGE HEAD =====================================
    outers = [
        cyl('h_base', 0.36, 0.0, 0.035, 'paint_blue', 96, ch=0.004),
        lathe('h_body', [(0, 0.03), (0.205, 0.03), (0.2, 0.06), (0.2, 0.50), (0.16, 0.55),
                         (0.11, 0.585), (0, 0.585)], 'paint_blue', 96),
        lathe('h_stand', [(0, 0.50), (0.25, 0.50), (0.262, 0.56), (0.262, 0.905), (0, 0.905)],
              'paint_blue', 96),
        cyl('h_mflange', 0.335, 0.895, 0.94, 'paint_blue', 96, ch=0.004),
        cyl('h_nozzle', 0.118, 0.0, 0.40, 'paint_blue', 64, axis='X', center=(0, 0, 0.30)),
        cyl('h_nflange', 0.17, 0.395, 0.43, 'paint_blue', 64, axis='X', center=(0, 0, 0.30), ch=0.003),
        lathe('h_nboss', [(0, 0.0), (0.16, 0.0), (0.125, 0.14), (0, 0.14)], 'paint_blue', 64, axis='X',
              center=(0.08, 0, 0.30)),
    ]
    inners = [
        lathe('h_cav', [(0, -0.01), (0.16, -0.01), (0.16, 0.42), (0.10, 0.47), (0, 0.47)], 'paint_blue', 96),
        cyl('h_noz_bore', 0.101, 0.0, 0.45, 'paint_blue', 64, axis='X', center=(0, 0, 0.30)),
        cyl('h_shaft_bore', 0.03, 0.40, 0.70, 'paint_blue', 48),
        cyl('h_stand_cav', 0.238, 0.585, 0.95, 'paint_blue', 96),
        box('h_win', (0.30, 0.70, 0.235), (0, 0, 0.745), 'paint_blue', bevel=0.03, segs=4),
    ]
    for o in outers[4:7]:
        pass
    head = csg('discharge_head', outers, inners, 'paint_blue')
    hb, hf = split(head)
    # anchor bolts + nozzle flange bolts
    nb, nf = nut_ring_split('h_anchor', 4, 0.62, 0.036, 0.035, 0.06)
    fb, ff = nut_ring_split('h_nfb', 8, 0.29, 0.03, 0.43, 0.452, axis='X', center=(0, 0, 0.30))
    mb, mf = nut_ring_split('h_mfb', 8, 0.60, 0.03, 0.94, 0.965)
    p = m.part('discharge_head', 'Discharge Head', 'discharge_head', section='split', explode=ex(0.45))
    p.add_split(join('dh_b', [hb, nb, fb, mb]), join('dh_f', [hf, nf, ff, mf]))

    # ================= MECHANICAL SEAL ====================================
    shb, shf = lathe_split('seal_housing', [(0.03, 0.585), (0.09, 0.585), (0.09, 0.605), (0.07, 0.61),
                                            (0.07, 0.675), (0.05, 0.675), (0.05, 0.605), (0.03, 0.605)],
                           'paint_blue_dark', 64)
    p = m.part('seal_housing', 'Seal Chamber / Stuffing Box', 'mechanical_seal', section='split',
               explode=ex(0.63, X_INT * 0.5))
    p.add_split(shb, shf)

    pairs = [
        lathe_split('gland', [(0.026, 0.675), (0.085, 0.675), (0.085, 0.695), (0.026, 0.695)], 'stainless', 64),
        lathe_split('sleeve', [(R_SH, 0.6), (0.026, 0.6), (0.026, 0.745), (R_SH, 0.745)], 'stainless', 48),
        lathe_split('seat', [(0.027, 0.655), (0.046, 0.655), (0.046, 0.675), (0.027, 0.675)], 'silicon_carbide', 48),
        lathe_split('face', [(0.028, 0.64), (0.042, 0.64), (0.042, 0.655), (0.028, 0.655)], 'carbon', 48),
        lathe_split('spring', [(0.03, 0.618), (0.045, 0.618), (0.045, 0.64), (0.03, 0.64)], 'stainless', 48),
        lathe_split('collar', [(0.026, 0.735), (0.04, 0.735), (0.04, 0.75), (0.026, 0.75)], 'stainless', 48),
    ]
    gb, gf = nut_ring_split('gland_n', 4, 0.15, 0.019, 0.695, 0.71)
    sb, sf = merge_halves('mech_seal', pairs)
    p = m.part('mechanical_seal', 'Mechanical Seal (Cartridge)', 'mechanical_seal', section='split',
               explode=ex(0.80, X_INT * 0.5))
    p.add_split(join('ms_b', [sb, gb]), join('ms_f', [sf, gf]))

    # ================= HEAD SHAFT & COUPLING ==============================
    hs = cyl('head_shaft', R_SH, -0.05, 0.79, 'steel', 32, ch=0.002)
    key = box('hs_key', (0.008, 0.008, 0.035), (R_SH, 0, 0.765), 'steel_dark')
    p = m.part('head_shaft', 'Head Shaft', 'rotating_element', explode=ex(0.35, X_ROT))
    p.add(join('head_shaft', [hs, key])); p.spin('Z', 2)

    cp = [
        lathe('c_hub1', [(R_SH, 0.75), (0.04, 0.75), (0.04, 0.775), (0.07, 0.775), (0.07, 0.795),
                         (R_SH, 0.795)], 'steel', 64),
        lathe('c_nut', [(R_SH, 0.735), (0.042, 0.735), (0.042, 0.75), (R_SH, 0.75)], 'steel_dark', 6),
        lathe('c_spacer', [(0.03, 0.795), (0.07, 0.795), (0.07, 0.81), (0.05, 0.815), (0.05, 0.835),
                           (0.07, 0.84), (0.07, 0.855), (0.03, 0.855)], 'steel', 64),
        lathe('c_hub2', [(0.03, 0.855), (0.07, 0.855), (0.07, 0.875), (0.045, 0.875), (0.045, 0.905),
                         (0.03, 0.905)], 'steel', 64),
        bolt_circle('c_bolts', 6, 0.115, 0.016, 0.775, 0.765, phase=0.3),
        bolt_circle('c_bolts2', 6, 0.115, 0.016, 0.875, 0.885, phase=0.3),
    ]
    p = m.part('coupling', 'Adjustable Spacer Coupling', 'power_transmission', explode=ex(0.82, X_ROT))
    p.add(join('coupling', cp)); p.spin('Z', 2)

    # ================= MOTOR ==============================================
    Z0 = 0.94
    shells = [
        lathe_split('m_lower', [(0.07, Z0), (0.335, Z0), (0.335, Z0 + 0.035), (0.29, Z0 + 0.05),
                                (0.282, Z0 + 0.09), (0.262, Z0 + 0.09), (0.262, Z0 + 0.06), (0.10, Z0 + 0.06),
                                (0.10, Z0 + 0.075), (0.07, Z0 + 0.075)], 'paint_motor', 96),
        lathe_split('m_frame', [(0.262, Z0 + 0.09), (0.282, Z0 + 0.09), (0.282, Z0 + 0.56),
                                (0.262, Z0 + 0.56)], 'paint_motor', 96),
        lathe_split('m_upper', [(0.262, Z0 + 0.56), (0.282, Z0 + 0.56), (0.27, Z0 + 0.60),
                                (0.12, Z0 + 0.625), (0.12, Z0 + 0.70), (0.08, Z0 + 0.70),
                                (0.08, Z0 + 0.60), (0.255, Z0 + 0.585), (0.262, Z0 + 0.575)], 'paint_motor', 96),
    ]
    fins = []
    for i in range(24):
        a = (i + 0.5) * TAU / 24
        fins.append(radial_rib(f'fin{i}', 0.278, 0.308, Z0 + 0.10, Z0 + 0.54, a, 0.007, 'paint_motor'))
    finb, finf = sides(fins, 'fins')
    tb = box('tbox', (0.11, 0.17, 0.15), (-0.335, 0, Z0 + 0.36), 'paint_motor', bevel=0.008)
    tlid = box('tlid', (0.02, 0.185, 0.165), (-0.395, 0, Z0 + 0.36), 'paint_motor', bevel=0.005)
    gl = cyl('tgland', 0.022, Z0 + 0.25, Z0 + 0.29, 'brass', 24, center=(-0.335, 0, 0))
    tbo = join('tbox_all', [tb, tlid, gl])
    tbb, tbf = split(tbo)
    lugs = [box(f'lug{i}', (0.06, 0.03, 0.07), (sx * 0.2, 0, Z0 + 0.635), 'paint_motor', bevel=0.006)
            for i, sx in enumerate((1, -1))]
    lgb, lgf = split(join('lugs', lugs))
    plate = box('nameplate', (0.14, 0.004, 0.09), (0.0, -0.284, Z0 + 0.33), 'nameplate', bevel=0.002)
    mfb, mff = merge_halves('motor_frame', shells + [(finb, finf), (tbb, tbf), (lgb, lgf), (None, plate)])
    p = m.part('motor_frame', 'Motor Frame & End Shields', 'motor', section='split', explode=ex(1.25))
    p.add_split(mfb, mff)

    cb, cf = lathe_split('canopy', [(0.0, Z0 + 0.82), (0.0, Z0 + 0.835), (0.26, Z0 + 0.81),
                                     (0.30, Z0 + 0.76), (0.30, Z0 + 0.66), (0.29, Z0 + 0.66),
                                     (0.29, Z0 + 0.755), (0.255, Z0 + 0.80)], 'paint_motor', 96)
    cpb, cpf = nut_ring_split('canopy_b', 4, 0.5, 0.016, Z0 + 0.66, Z0 + 0.645)
    p = m.part('drip_cover', 'Drip Cover (Canopy)', 'motor', section='split', explode=ex(2.4))
    p.add_split(join('dc_b', [cb, cpb]), join('dc_f', [cf, cpf]))

    st = [lathe_split('stator', [(0.172, Z0 + 0.16), (0.262, Z0 + 0.16), (0.262, Z0 + 0.46),
                                 (0.172, Z0 + 0.46)], 'lamination', 96)]
    for z0, z1 in ((Z0 + 0.10, Z0 + 0.16), (Z0 + 0.46, Z0 + 0.52)):
        prof = [(0.185, z0 if z0 > Z0 + 0.3 else z1), (0.24, z0 if z0 > Z0 + 0.3 else z1)]
        lo, hi = (z0, z1)
        prof = [(0.182, lo + 0.01), (0.19, lo), (0.235, lo), (0.245, lo + 0.015), (0.245, hi - 0.015),
                (0.235, hi), (0.19, hi), (0.182, hi - 0.01)]
        st.append(lathe_split('winding', prof, 'copper', 64))
    sb, sf = merge_halves('stator', st)
    p = m.part('stator', 'Stator Core & Windings', 'motor', section='split', explode=ex(1.3, X_INT))
    p.add_split(sb, sf)

    rot = [cyl('rotor_core', 0.168, Z0 + 0.165, Z0 + 0.455, 'lamination', 96),
           cyl('end_ring1', 0.168, Z0 + 0.145, Z0 + 0.165, 'aluminium', 96, r_in=0.13),
           cyl('end_ring2', 0.168, Z0 + 0.455, Z0 + 0.475, 'aluminium', 96, r_in=0.13)]
    p = m.part('rotor', 'Rotor (Squirrel Cage)', 'motor', explode=ex(1.3, X_ROT))
    p.add(join('rotor', rot)); p.spin('Z', 2)

    ms = cyl('motor_shaft', 0.03, 0.855, Z0 + 0.74, 'steel', 32, ch=0.002)
    p = m.part('motor_shaft', 'Motor Shaft', 'motor', explode=ex(1.6, X_ROT))
    p.add(ms); p.spin('Z', 2)

    fan = [cyl('fan_hub', 0.05, Z0 + 0.715, Z0 + 0.745, 'aluminium', 48, r_in=0.03)]
    for i in range(10):
        b = box(f'fan_bl{i}', (0.2, 0.004, 0.04), (0.15, 0, Z0 + 0.73), 'aluminium')
        rotate(b, math.radians(25), 'X', (0.15, 0, Z0 + 0.73))
        fan.append(rotate(b, TAU * i / 10))
    p = m.part('motor_fan', 'Cooling Fan', 'motor', explode=ex(2.1, X_ROT))
    p.add(join('motor_fan', fan)); p.spin('Z', 2)

    def ball_bearing(name, ri, ro, z0, z1, nballs):
        w = z1 - z0
        rm = (ri + ro) / 2
        rb = min(w, ro - ri) * 0.3
        pairs = [lathe_split(name + '_ir', [(ri, z0), (rm - rb * 0.6, z0), (rm - rb * 0.6, z1),
                                            (ri, z1)], 'steel', 48),
                 lathe_split(name + '_or', [(rm + rb * 0.6, z0), (ro, z0), (ro, z1),
                                            (rm + rb * 0.6, z1)], 'steel', 48)]
        balls = []
        for i in range(nballs):
            a = (i + 0.5) * TAU / nballs
            prof = [(rb * math.sin(t * math.pi / 8), (z0 + z1) / 2 - rb * math.cos(t * math.pi / 8)) for t in range(9)]
            bo = lathe(name + f'_b{i}', prof, 'chrome', 16)
            balls.append(move(bo, (rm * math.cos(a), rm * math.sin(a), 0)))
        bb, bf = sides(balls, name + '_balls')
        return merge_halves(name, pairs + [(bb, bf)])

    tb_ = ball_bearing('thrust_brg', 0.03, 0.075, Z0 + 0.64, Z0 + 0.665, 14)
    tb2 = ball_bearing('thrust_brg2', 0.03, 0.075, Z0 + 0.665, Z0 + 0.69, 14)
    b1, f1 = merge_halves('thrust_bearing', [tb_, tb2])
    p = m.part('thrust_bearing', 'Motor Thrust Bearing (Angular-Contact Pair)', 'bearings', section='split',
               explode=ex(1.95, X_INT))
    p.add_split(b1, f1)
    gb_ = ball_bearing('guide_brg', 0.03, 0.07, Z0 + 0.03, Z0 + 0.058, 12)
    p = m.part('motor_guide_bearing', 'Motor Lower Guide Bearing', 'bearings', section='split',
               explode=ex(0.95, X_INT))
    p.add_split(*gb_)

    # ================= COLUMN =============================================
    def column(name, ztop, zbot):
        prof = [(0.101, zbot), (0.17, zbot), (0.17, zbot + 0.025), (0.125, zbot + 0.03), (0.11, zbot + 0.045),
                (0.11, ztop - 0.045), (0.125, ztop - 0.03), (0.17, ztop - 0.025), (0.17, ztop), (0.101, ztop)]
        b, f = lathe_split(name, prof, 'paint_blue', 96)
        nb1, nf1 = nut_ring_split(name + '_n1', 8, 0.29, 0.03, ztop - 0.025, ztop - 0.045)
        return join(name + 'b', [b, nb1]), join(name + 'f', [f, nf1])

    c1 = column('column_1', -0.01, -0.80)
    p = m.part('column_pipe_1', 'Column Pipe – Upper Section', 'column', section='split', explode=ex(-0.4),
               info={'ref': 'column_pipe', 'note': 'Column length shortened for display.'})
    p.add_split(*c1)
    c2 = column('column_2', -0.82, -1.60)
    p = m.part('column_pipe_2', 'Column Pipe – Lower Section', 'column', section='split', explode=ex(-1.2),
               info={'ref': 'column_pipe', 'note': 'Column length shortened for display.'})
    p.add_split(*c2)
    top_ring = lathe_split('head_gasket', ring_profile(0.101, 0.17, -0.01, 0.0), 'rubber', 96)
    p = m.part('column_gasket', 'Column Flange Gasket', 'column', section='split', explode=ex(-0.02),
               info={'ref': 'gasket'})
    p.add_split(*top_ring)

    # bearing retainer (spider) at the column joint
    zr = -0.81
    ret = [lathe_split('ret_rim', ring_profile(0.101, 0.17, zr - 0.01, zr + 0.01), 'bronze', 96),
           lathe_split('ret_hub', ring_profile(0.028, 0.045, zr - 0.05, zr + 0.05, 0.003), 'bronze', 48)]
    ribs = [radial_rib(f'rr{i}', 0.04, 0.106, zr - 0.035, zr + 0.008, TAU * (i + 0.5) / 4, 0.012, 'bronze')
            for i in range(4)]
    ret.append(sides(ribs, 'ret_ribs'))
    p = m.part('bearing_retainer', 'Bearing Retainer (Spider)', 'column', section='split',
               explode=ex(zr, X_INT * 0.5))
    p.add_split(*merge_halves('bearing_retainer', ret))
    p = m.part('lineshaft_bearing', 'Line-Shaft Bearing (Rubber-Lined)', 'bearings', section='split',
               explode=ex(zr, X_INT))
    p.add_split(*lathe_split('lsb', ring_profile(R_SH + 0.0005, 0.028, zr - 0.048, zr + 0.048), 'rubber', 48))

    # ================= SHAFTING ===========================================
    ls = cyl('line_shaft', R_SH, -1.50, -0.05, 'stainless', 32)
    p = m.part('line_shaft', 'Line Shaft', 'rotating_element', explode=ex(-0.75, X_ROT))
    p.add(ls); p.spin('Z', 2)
    zb_bottom = Z_BELL - 0.235
    bs = cyl('bowl_shaft', R_SH, zb_bottom, -1.50, 'stainless', 32, ch=0.002)
    p = m.part('bowl_shaft', 'Pump (Bowl) Shaft', 'rotating_element', explode=ex(-2.1, X_ROT))
    p.add(bs); p.spin('Z', 2)
    cpls = [cyl('sc1', 0.034, -1.545, -1.455, 'steel', 6, ch=0.003),
            cyl('sc2', 0.034, -0.095, -0.005, 'steel', 6, ch=0.003)]
    p = m.part('shaft_couplings', 'Threaded Line-Shaft Couplings', 'power_transmission',
               explode=ex(-0.8, X_ROT + 0.15))
    p.add(join('shaft_couplings', cpls)); p.spin('Z', 2)

    # ================= DISCHARGE CASE =====================================
    zb = Z_DC_BOT
    dc_prof = [(0.093, zb), (0.195, zb), (0.195, zb + 0.022), (0.132, zb + 0.045), (0.13, zb + 0.15),
               (0.122, zb + 0.225), (0.17, zb + 0.235), (0.17, zb + 0.26), (0.101, zb + 0.26),
               (0.101, zb + 0.2), (0.113, zb + 0.11), (0.111, zb + 0.05), (0.098, zb + 0.02)]
    dcs = [lathe_split('dcase', dc_prof, 'paint_blue', 96),
           lathe_split('dcase_hub', [(0.028, zb), (0.047, zb), (0.047, zb + 0.15), (0.035, zb + 0.19),
                                     (0.028, zb + 0.19)], 'paint_blue', 48)]
    ribs = [radial_rib(f'dr{i}', 0.04, 0.112, zb + 0.03, zb + 0.15, TAU * (i + 0.5) / 4, 0.012, 'paint_blue')
            for i in range(4)]
    dcs.append(sides(ribs, 'dc_ribs'))
    dcs.append(nut_ring_split('dc_n', 8, 0.35, 0.024, zb + 0.022, zb + 0.04))
    dcs.append(nut_ring_split('dc_n2', 8, 0.29, 0.03, zb + 0.235, zb + 0.215))
    p = m.part('discharge_case', 'Discharge Case (Top Bowl)', 'bowl_assembly', section='split',
               explode=ex(zb + 0.13))
    p.add_split(*merge_halves('discharge_case', dcs))
    p = m.part('discharge_case_bearing', 'Discharge Case Bearing', 'bearings', section='split',
               explode=ex(zb + 0.1, X_INT), info={'ref': 'bowl_bearing'})
    p.add_split(*lathe_split('dcb', ring_profile(R_SH + 0.0005, 0.028, zb + 0.01, zb + 0.18), 'bronze', 48))

    # ================= BOWLS + IMPELLERS ==================================
    bowl_prof = [(0.093, 0.0), (0.195, 0.0), (0.195, 0.022), (0.152, 0.034), (0.152, 0.226),
                 (0.195, 0.238), (0.195, 0.26), (0.093, 0.26), (0.098, 0.235), (0.115, 0.205),
                 (0.135, 0.17), (0.142, 0.135), (0.138, 0.115), (0.123, 0.094), (0.104, 0.062),
                 (0.093, 0.032)]
    hub_prof = [(0.028, 0.134), (0.074, 0.134), (0.076, 0.15), (0.071, 0.18), (0.061, 0.215),
                (0.05, 0.245), (0.046, 0.258), (0.028, 0.258)]
    d_hub = [(0.075, 0.14), (0.071, 0.18), (0.061, 0.215), (0.05, 0.245)]
    d_wall = [(0.142, 0.14), (0.135, 0.17), (0.115, 0.205), (0.098, 0.235)]
    imp_hub = [(0.0215, 0.005), (0.036, 0.005), (0.045, 0.04), (0.06, 0.085), (0.075, 0.12),
               (0.072, 0.128), (0.0215, 0.128)]
    imp_shroud = [(0.079, 0.002), (0.085, 0.002), (0.085, 0.028), (0.100, 0.060), (0.119, 0.092),
                  (0.134, 0.112), (0.132, 0.118), (0.127, 0.116), (0.113, 0.097), (0.094, 0.066),
                  (0.079, 0.034)]
    b_hub = [(0.04, 0.03), (0.05, 0.06), (0.063, 0.09), (0.075, 0.118)]
    b_shr = [(0.079, 0.034), (0.094, 0.066), (0.113, 0.097), (0.128, 0.116)]

    for k in range(N_STAGES):
        z0 = Z_DC_BOT - (k + 1) * H     # bowl bottom
        stage = k + 1
        # --- bowl casting: wall + hub + 7 diffuser vanes
        wall = lathe_split(f'bowl{stage}_wall', [(r, z + z0) for r, z in bowl_prof], 'paint_blue', 96)
        hubp = lathe_split(f'bowl{stage}_hub', [(r, z + z0) for r, z in hub_prof], 'paint_blue', 64)
        vanes = []
        for i in range(7):
            th0 = TAU * i / 7 + 0.2
            vanes.append(vane(f'dv{stage}_{i}', [(r, z + z0) for r, z in d_hub],
                              [(r, z + z0) for r, z in d_wall],
                              lambda s, t, th0=th0: th0 + 0.55 * (1 - (1 - s) ** 2), 0.006, 'paint_blue',
                              ns=14, nt=4))
        vb, vf = split(join(f'dvanes{stage}', vanes))
        nb_, nf_ = nut_ring_split(f'bowl{stage}_n', 8, 0.35, 0.024, z0 + 0.022, z0 + 0.04)
        bb, bf = merge_halves(f'bowl_{stage}', [wall, hubp, (vb, vf), (nb_, nf_)])
        zc = z0 + H / 2
        p = m.part(f'bowl_{stage}', f'Bowl – Stage {stage}', 'bowl_assembly', section='split',
                   explode=ex(zc), info={'ref': 'bowl'})
        p.add_split(bb, bf)
        # wear ring (in bowl, around impeller skirt)
        p = m.part(f'wear_ring_{stage}', f'Bowl Wear Ring – Stage {stage}', 'bowl_assembly',
                   section='split', explode=ex(zc, X_INT * 0.5), info={'ref': 'wear_ring'})
        p.add_split(*lathe_split(f'wr{stage}', ring_profile(0.0865, 0.093, z0 + 0.001, z0 + 0.03),
                                 'bronze', 64))
        p = m.part(f'bowl_bearing_{stage}', f'Bowl Bearing – Stage {stage}', 'bearings', section='split',
                   explode=ex(zc, X_INT), info={'ref': 'bowl_bearing'})
        p.add_split(*lathe_split(f'bbr{stage}', ring_profile(R_SH + 0.0005, 0.028, z0 + 0.138, z0 + 0.255),
                                 'bronze', 48))
        # --- enclosed mixed-flow impeller
        hubo = lathe(f'imp{stage}_hub', [(r, z + z0) for r, z in imp_hub], 'bronze', 64)
        shr_b, shr_f = lathe_split(f'imp{stage}_shroud', [(r, z + z0) for r, z in imp_shroud], 'bronze', 96)
        blades = [vane(f'ib{stage}_{i}', [(r, z + z0) for r, z in b_hub], [(r, z + z0) for r, z in b_shr],
                       lambda s, t, th=TAU * i / 5: th - 1.25 * s - 0.12 * t * s, 0.005, 'bronze',
                       ns=18, nt=5)
                  for i in range(5)]
        imp = join(f'impeller_{stage}', [hubo] + blades)
        p = m.part(f'impeller_{stage}', f'Impeller – Stage {stage}', 'rotating_element',
                   explode=ex(zc, X_ROT), info={'ref': 'impeller'})
        p.add(imp, 'keep')
        # front shroud is sectioned so the blades are visible in cutaway
        p.add(shr_b, 'back').name = f'impeller_{stage}_shroud__back'
        p.add(shr_f, 'front').name = f'impeller_{stage}_shroud__front'
        p.spin('Z', 2)
        col = lathe(f'collet{stage}', [(R_SH, z0 - 0.004), (0.024, z0 - 0.004), (0.029, z0 + 0.04),
                                       (R_SH, z0 + 0.04)], 'steel', 32)
        p = m.part(f'collet_{stage}', f'Taper Lock Collet – Stage {stage}', 'rotating_element',
                   explode=ex(zc - 0.12, X_ROT), info={'ref': 'collet'})
        p.add(col); p.spin('Z', 2)

    # ================= SUCTION BELL + STRAINER ============================
    zb = Z_BELL
    bell_prof = [(0.093, zb), (0.195, zb), (0.195, zb - 0.022), (0.122, zb - 0.04), (0.128, zb - 0.12),
                 (0.165, zb - 0.215), (0.212, zb - 0.268), (0.222, zb - 0.282), (0.214, zb - 0.292),
                 (0.2, zb - 0.285), (0.155, zb - 0.235), (0.118, zb - 0.135), (0.105, zb - 0.05)]
    bs_ = [lathe_split('bell', bell_prof, 'paint_blue', 96),
           lathe_split('bell_hub', [(0.028, zb - 0.02), (0.047, zb - 0.02), (0.047, zb - 0.22),
                                    (0.035, zb - 0.25), (0.0, zb - 0.255), (0.0, zb - 0.24),
                                    (0.028, zb - 0.24)], 'paint_blue', 48)]
    ribs = [radial_rib(f'br{i}', 0.04, 0.125, zb - 0.19, zb - 0.06, math.radians(a), 0.012, 'paint_blue')
            for i, a in enumerate((30, 150, 270))]
    bs_.append(sides(ribs, 'bell_ribs'))
    p = m.part('suction_bell', 'Suction Bell', 'bowl_assembly', section='split', explode=ex(zb - 0.15))
    p.add_split(*merge_halves('suction_bell', bs_))
    p = m.part('bell_bearing', 'Suction Bell Bearing', 'bearings', section='split',
               explode=ex(zb - 0.13, X_INT), info={'ref': 'bowl_bearing'})
    p.add_split(*lathe_split('bellb', ring_profile(R_SH + 0.0005, 0.028, zb - 0.235, zb - 0.025),
                             'bronze', 48))

    zs = zb - 0.29
    rods = []
    for i in range(16):
        a = (i + 0.5) * TAU / 16
        path = [(0.212 * math.cos(a), 0.212 * math.sin(a), zs),
                (0.04 * math.cos(a), 0.04 * math.sin(a), zs - 0.24)]
        rods.append(sweep_tube(f'rod{i}', path, 0.004, 'stainless', 8))
    rb, rf = sides(rods, 'rods')
    rings = [lathe_split('srt', [(0.205, zs - 0.004), (0.226, zs - 0.004), (0.226, zs + 0.01),
                                 (0.205, zs + 0.01)], 'stainless', 96)]
    for f_ in (0.33, 0.66):
        r = 0.212 - (0.212 - 0.04) * f_
        rings.append(lathe_split(f'sr{f_}', [(r - 0.004, zs - 0.24 * f_ - 0.003), (r + 0.004, zs - 0.24 * f_ - 0.003),
                                             (r + 0.004, zs - 0.24 * f_ + 0.003), (r - 0.004, zs - 0.24 * f_ + 0.003)],
                                 'stainless', 64))
    rings.append(lathe_split('scap', [(0, zs - 0.25), (0.05, zs - 0.25), (0.05, zs - 0.235), (0, zs - 0.235)],
                             'stainless', 48))
    rings.append((rb, rf))
    p = m.part('strainer', 'Cone Strainer', 'bowl_assembly', section='split', explode=ex(zs - 0.35))
    p.add_split(*merge_halves('strainer', rings))

    # ================= FLOW PATH OVERLAY ==================================
    Y = 0.012   # just behind the section plane so paths read clearly in cutaway

    def path_stage(z0, sx):
        rz = [(0.06, 0.0), (0.062, 0.03), (0.075, 0.06), (0.095, 0.095), (0.11, 0.12), (0.112, 0.15),
              (0.1, 0.18), (0.083, 0.215), (0.07, 0.25)]
        return [(sx * r, Y, z0 + z) for r, z in rz]
    for sx in (1, -1):
        suction = [(sx * 0.12, Y, zs - 0.30), (sx * 0.12, Y, zs - 0.12), (sx * 0.13, Y, zb - 0.24),
                   (sx * 0.09, Y, zb - 0.1), (sx * 0.07, Y, zb - 0.02), (sx * 0.06, Y, zb)]
        m.flow(f'flow_suction_{sx:+d}', suction, 'flow_suction', 0.008, 0.2)
        disc = []
        for k in reversed(range(N_STAGES)):
            disc += path_stage(Z_DC_BOT - (k + 1) * H, sx)
        disc += [(sx * 0.075, Y, Z_DC_BOT + 0.05), (sx * 0.08, Y, Z_DC_BOT + 0.2), (sx * 0.075, Y, -1.5),
                 (sx * 0.075, Y, -0.2), (sx * 0.075, Y, 0.10)]
        if sx > 0:
            disc += [(0.09, Y, 0.2), (0.14, Y, 0.27), (0.22, Y, 0.30), (0.55, Y, 0.30)]
        else:
            disc += [(-0.08, Y, 0.25), (-0.03, Y, 0.34), (0.06, Y, 0.34), (0.16, Y, 0.32), (0.55, Y, 0.31)]
        m.flow(f'flow_discharge_{sx:+d}', disc, 'flow_discharge', 0.008, 0.3)

    teaching_overlays(m, zb, zs)
    return m.export(out_dir)


def teaching_overlays(m, zb, zs):
    """Flagship teaching layers: stage pressure build-up, axial (down) thrust path, sump/submergence."""
    from pumpforge.shapes import cone_arrow
    N = N_STAGES
    ramp = lambda k: f'pressure_{min(9, round(9 * k / (N + 1)))}'
    rings = [lathe('p_bell', [(0.226, zb - 0.07), (0.236, zb - 0.07), (0.236, zb - 0.02), (0.226, zb - 0.02)], ramp(0), 96)]
    for k in range(N):
        z0 = Z_DC_BOT - (N - k) * H     # bottom stage first
        rings.append(lathe(f'p_b{k}', [(0.198, z0 + 0.05), (0.21, z0 + 0.05), (0.21, z0 + H - 0.03), (0.198, z0 + H - 0.03)], ramp(k + 1), 96))
        m.annotate('pressure', f'Stage {k + 1}: +{k + 1}Δp', (0.33, 0.0, z0 + H / 2), value=k + 1)
    for j, zc_ in enumerate((Z_DC_BOT + 0.5, -0.9, -0.3)):
        rings.append(lathe(f'p_col{j}', [(0.0, zc_ - 0.02), (0.0, zc_ - 0.02)][:0] + [(0.2, zc_ - 0.02), (0.212, zc_ - 0.02), (0.212, zc_ + 0.02), (0.2, zc_ + 0.02)], ramp(N + 1), 64))
    m.annotate('pressure', 'Bell inlet: lowest pressure (submergence sets NPSHa)', (0.4, 0.0, zb - 0.1), value=0)
    m.annotate('pressure', f'Column & head: {N} stage heads − column/head losses', (0.35, 0.0, -0.8), value=N)
    m.overlay('pressure', join('pressure_rings', rings), 'Stage-by-stage pressure', split=True, description=(
              'Each bowl stage (impeller + diffuser bowl) adds about the same head; the stages are stacked so pressure rises from the bell '
              '(blue) to the top bowl (red). The column and discharge head then lose a little head to friction before the discharge flange.'))
    arr = []
    for k in range(N):
        z0 = Z_DC_BOT - (N - k) * H
        for sx in (1, -1):
            x = sx * 0.06
            arr += [sweep_tube(f'td{k}{sx}', [(x, 0.0, z0 + 0.2), (x, 0.0, z0 + 0.13)], 0.005, 'thrust', 10),
                    cone_arrow(f'tdc{k}{sx}', (x, 0.0, z0 + 0.13), (0, 0, -1), 0.025, 0.012, 'thrust')]
    arr += [sweep_tube('tline', [(0.0, -0.06, 0.4), (0.0, -0.06, 1.25)], 0.006, 'thrust', 10)]
    up = [sweep_tube('tup', [(0.12, 0.0, 1.45), (0.12, 0.0, 1.75)], 0.011, 'counter_force', 14),
          cone_arrow('tupc', (0.12, 0.0, 1.75), (0, 0, 1), 0.06, 0.028, 'counter_force')]
    m.overlay('thrust', join('thrust_arrows', arr + up), 'Axial thrust path',
              'In a vertical turbine pump the hydraulic thrust of every impeller acts downward and adds to the weight of the rotating '
              'element. The line shaft hangs from the motor: the total down-thrust is carried by the motor thrust bearing (green reaction). '
              'Impeller axial position (lift) is set at the adjusting nut / spacer coupling.')
    m.annotate('thrust', 'Impeller down-thrust (each stage)', (-0.32, 0.0, Z_DC_BOT - 0.4))
    m.annotate('thrust', 'Total down-thrust + rotor weight → motor thrust bearing', (0.45, 0.0, 1.6))
    D = 0.444                                   # bell inlet diameter of this model
    z_in = zb - 0.292
    z_min = z_in + 1.5 * D                      # illustrative minimum submergence
    sump = [lathe('wl_min', [(0.27, z_min - 0.004), (0.85, z_min - 0.004), (0.85, z_min), (0.27, z_min)], 'flow_suction', 96),
            lathe('wl_norm', [(0.2, -0.9 - 0.004), (0.85, -0.9 - 0.004), (0.85, -0.9), (0.2, -0.9)], 'flow_suction', 96),
            sweep_tube('dim_s', [(-0.5, 0.0, z_in), (-0.5, 0.0, z_min)], 0.004, 'steel_dark', 8),
            cone_arrow('dim_s1', (-0.5, 0.0, z_min - 0.03), (0, 0, 1), 0.03, 0.012, 'steel_dark'),
            cone_arrow('dim_s0', (-0.5, 0.0, z_in + 0.03), (0, 0, -1), 0.03, 0.012, 'steel_dark'),
            sweep_tube('dim_d', [(-0.222, 0.0, z_in - 0.06), (0.222, 0.0, z_in - 0.06)], 0.004, 'steel_dark', 8)]
    m.overlay('installation', join('sump_levels', sump), 'Sump levels & submergence',
              'Water levels and the submergence S above the bell inlet. ANSI/HI 9.8 gives the minimum submergence as a function of the '
              'bell diameter D and inlet velocity (S = D(1 + 2.3·F_D), F_D = V/√(gD); verify in the current edition). Low submergence causes '
              'air-entraining vortices, vibration and loss of performance. Levels shown are illustrative.', smooth_angle=None, split=True)
    m.annotate('installation', 'Normal operating water level', (0.95, 0.0, -0.9))
    m.annotate('installation', 'Minimum water level (illustrative)', (0.95, 0.0, z_min))
    m.annotate('installation', 'S = submergence above bell inlet', (-0.75, 0.0, (z_in + z_min) / 2))
    m.annotate('installation', 'D = bell inlet diameter', (0.0, 0.0, z_in - 0.12))
    m.annotate('installation', 'Floor clearance ≈ 0.3–0.5 D below the bell (ANSI/HI 9.8, verify)', (0.6, 0.0, z_in - 0.25))


# ---------------------------------------------------------------------------
# Engineering metadata (general guidance; not manufacturer-specific data)
# ---------------------------------------------------------------------------
META = {
    'summary': ('A vertical turbine pump is a vertically suspended, multistage centrifugal pump. The bowl '
                'assembly (impellers and diffuser bowls) is submerged at the bottom of a well or sump; a '
                'line shaft running inside the column pipe transmits torque from a vertical motor mounted '
                'on the discharge head at ground level. Each stage adds head; liquid rises through the '
                'column and leaves through the discharge head nozzle.'),
    'classification': {
        'family': 'Rotodynamic (centrifugal), diffuser type',
        'configuration': 'Vertically suspended, wet pit, line-shaft driven, multistage',
        'hydraulic_type': 'Mixed-flow impellers with vaned diffuser bowls',
        'api_610_type': 'VS1 (wet-pit, vertically suspended, single casing, diffuser, discharge through column)',
    },
    'model_configuration': {
        'stages': N_STAGES,
        'lubrication': 'Open line shaft, product (water) lubricated rubber/bronze bearings',
        'driver': 'Vertical solid-shaft (VSS) induction motor with thrust bearing',
        'shaft_seal': 'Cartridge mechanical seal in head seal chamber',
        'coupling': 'Adjustable flanged spacer coupling (impeller lift set with adjusting nut)',
        'rotation': 'Counter-clockwise viewed from the motor end (most common convention; confirm per manufacturer)',
        'displayed_column_length_m': 1.6,
        'teaching_overlays': 'pressure (stage-by-stage), thrust (down-thrust carried by motor thrust bearing), installation (sump levels, submergence), flow',
        'learning_case': ('Flagship arrangement study prepared as a learning case for the WPIL WVT series (user reference: WVT-30-18). '
                          'The geometry is a representative line-shaft wet-pit VS1 arrangement; WPIL dimensions, stage count, bowl size and '
                          'ratings are NOT reproduced here and must be taken from the WPIL datasheet / GA drawing (see engineering_parameters.reference_model).'),
    },
    'standards': [
        {'id': 'API 610', 'title': 'Centrifugal Pumps for Petroleum, Petrochemical and Natural Gas Industries',
         'relevance': 'Defines pump type VS1 and requirements for vertically suspended pumps in process service.',
         'edition': 'to be verified (12th edition current at time of writing; confirm)'},
        {'id': 'ANSI/HI 2.1-2.2', 'title': 'Rotodynamic Vertical Pumps of Radial, Mixed and Axial Flow Types – Nomenclature and Definitions',
         'relevance': 'Component names and definitions used in this model.', 'edition': 'to be verified'},
        {'id': 'ANSI/HI 9.8', 'title': 'Rotodynamic Pumps for Pump Intake Design',
         'relevance': 'Sump and intake geometry, submergence and vortex avoidance for wet-pit pumps.',
         'edition': 'to be verified'},
        {'id': 'AWWA E103', 'title': 'Horizontal and Vertical Line-Shaft Pumps',
         'relevance': 'Water-utility line-shaft turbine pump requirements.', 'edition': 'to be verified'},
        {'id': 'ISO 9906', 'title': 'Rotodynamic pumps – Hydraulic performance acceptance tests',
         'relevance': 'Performance test grades and tolerances.', 'edition': 'to be verified'},
    ],
    'references': [
        'Karassik, Messina, Cooper, Heald – Pump Handbook (McGraw-Hill), chapters on vertical pumps.',
        'Hydraulic Institute – ANSI/HI 2.1-2.2 and 2.3 (vertical pump design and application).',
        'Manufacturer installation, operation & maintenance manuals for line-shaft vertical turbine pumps (generic practice).',
    ],
    'components': {
        'discharge_head': {
            'function': 'Supports the motor and the full suspended pump weight, turns the flow 90° from the column into the discharge nozzle and houses the shaft seal.',
            'construction': 'Cast or fabricated body with base (sole) plate, discharge elbow and flanged nozzle, motor stand with access windows for the coupling and seal, and a register fit for the motor.',
            'material': 'Cast iron or ductile iron for water service; fabricated carbon steel or stainless steel for higher pressure or corrosive service.',
            'operating_conditions': 'Carries discharge pressure, nozzle loads from piping and the axial/radial reaction of the pump; must be rigid enough to keep the structural natural frequency away from running speed.',
            'failure_modes': ['Cracking from excessive nozzle loads or piping misalignment', 'Structural resonance causing high vibration', 'Corrosion/erosion at the elbow', 'Soft-foot or grout failure at base'],
            'inspection': ['Check base-plate levelness and anchor-bolt torque', 'Verify piping is supported independently (no strain on nozzle)', 'Vibration measurement at motor top in two directions', 'Visual check for cracks and coating damage'],
        },
        'seal_housing': {
            'function': 'Provides the seal chamber where the shaft leaves the pressurised head; locates the mechanical seal.',
            'construction': 'Machined housing bolted to the head with a register fit concentric with the shaft; may include flush, vent and drain connections.',
            'material': 'Cast iron, ductile iron or stainless steel.',
            'operating_conditions': 'Exposed to pump discharge pressure at the head (minus column losses).',
            'failure_modes': ['Run-out/eccentricity causing seal face wear', 'Air trapped in chamber leading to dry-running', 'Corrosion of register faces'],
            'inspection': ['Check face and bore run-out relative to the shaft', 'Verify chamber vent before start-up', 'Inspect gasket faces'],
        },
        'mechanical_seal': {
            'function': 'Prevents pumped liquid escaping along the rotating shaft at the discharge head.',
            'construction': 'Cartridge seal: rotating face driven by the sleeve and spring assembly runs against a stationary seat held in the gland; secondary O-rings seal the sleeve and gland. Set collar locks the cartridge to the shaft.',
            'material': 'Faces commonly carbon-graphite vs silicon carbide (or SiC vs SiC for abrasive water); stainless steel metal parts; elastomers selected for fluid and temperature.',
            'operating_conditions': 'Faces need a liquid film; chamber must be vented and flooded. Seal selection and piping plans per manufacturer and, for process service, API 682.',
            'failure_modes': ['Dry running at start-up (chamber not vented)', 'Face wear from abrasives', 'Thermal cracking of faces', 'Elastomer chemical attack or compression set', 'Leakage from incorrect setting of the cartridge after impeller lift adjustment'],
            'inspection': ['Monitor leakage rate and seal temperature', 'Confirm setting clips removed after installation', 'Check flush flow if a flush is fitted'],
        },
        'head_shaft': {
            'function': 'Connects the top of the line shaft to the motor through the coupling; passes through the seal.',
            'construction': 'Precision-ground shaft with threaded lower end for the line-shaft coupling and keyed upper end for the coupling hub.',
            'material': 'Carbon steel or stainless steel (e.g. 416, 410, 316 depending on fluid).',
            'operating_conditions': 'Transmits full motor torque and the hydraulic down-thrust to the motor thrust bearing.',
            'failure_modes': ['Fatigue at keyway or thread', 'Wear under the seal', 'Bent shaft causing seal leakage and vibration'],
            'inspection': ['Total indicated run-out at seal area', 'Thread and keyway condition', 'Surface finish under seal'],
        },
        'coupling': {
            'function': 'Transmits torque from motor to pump and allows the impeller axial position (lift) to be set with the adjusting nut.',
            'construction': 'Pump hub, adjusting nut and spacer bolted to the motor hub; spacer allows seal removal without lifting the motor.',
            'material': 'Carbon steel or alloy steel; bolts per manufacturer grade.',
            'operating_conditions': 'Carries torque and the full down-thrust into the motor thrust bearing.',
            'failure_modes': ['Incorrect impeller lift leading to rubbing or loss of performance', 'Loose bolts', 'Misalignment between motor and pump shafts'],
            'inspection': ['Verify impeller lift setting per manufacturer data', 'Check bolt torque and locking', 'Measure run-out across the coupling'],
        },
        'motor_frame': {
            'function': 'Encloses and supports the stator, bearings and terminal box; the base flange locates the motor on the discharge head.',
            'construction': 'Cast iron or fabricated frame with cooling fins, lower and upper end shields (bearing brackets), lifting lugs, terminal box and nameplate.',
            'material': 'Cast iron or fabricated steel.',
            'operating_conditions': 'Enclosure type (e.g. WP-I, TEFC) and insulation class per motor data sheet.',
            'failure_modes': ['Overheating from blocked air paths', 'Moisture ingress', 'Loose foot/flange bolting', 'Reed-frequency resonance of motor on head'],
            'inspection': ['Insulation resistance test before start', 'Clean air paths', 'Vibration at top bearing', 'Terminal box seal and cable gland condition'],
        },
        'drip_cover': {
            'function': 'Protects the top bearing housing and the motor opening from rain and falling objects; covers the coupling access on hollow-shaft designs.',
            'construction': 'Formed steel or cast canopy bolted to the top end shield.',
            'material': 'Steel or cast iron, painted.',
            'operating_conditions': 'Outdoor exposure.',
            'failure_modes': ['Corrosion', 'Loose bolting causing rattle'],
            'inspection': ['Visual inspection, bolt tightness'],
        },
        'stator': {
            'function': 'Produces the rotating magnetic field that drives the rotor.',
            'construction': 'Stack of insulated electrical-steel laminations with copper windings in slots; end turns project above and below the core.',
            'material': 'Silicon electrical steel; copper magnet wire with Class F/H insulation (typical).',
            'operating_conditions': 'Rated voltage/frequency; temperature rise within the insulation class.',
            'failure_modes': ['Insulation breakdown from overheating or moisture', 'Single-phasing', 'Voltage unbalance overheating'],
            'inspection': ['Insulation resistance / polarisation index', 'Winding temperature (RTDs where fitted)', 'Phase current balance'],
        },
        'rotor': {
            'function': 'Squirrel-cage rotor that converts the stator field into shaft torque.',
            'construction': 'Laminated core on the motor shaft with aluminium or copper bars short-circuited by end rings.',
            'material': 'Electrical steel; die-cast aluminium or fabricated copper cage.',
            'operating_conditions': 'Runs at slightly below synchronous speed (slip).',
            'failure_modes': ['Broken rotor bars (current sidebands)', 'Imbalance', 'Rotor-to-stator rub from bearing failure'],
            'inspection': ['Motor current signature analysis', 'Vibration spectrum at 1× and pole-pass frequency'],
        },
        'motor_shaft': {
            'function': 'Carries the rotor and transmits torque to the pump; on solid-shaft motors it extends below the motor into the coupling.',
            'construction': 'Forged/ground steel shaft with keyway at the coupling end.',
            'material': 'Carbon or alloy steel.',
            'operating_conditions': 'Carries rotor weight plus pump thrust to the thrust bearing.',
            'failure_modes': ['Fatigue at keyway', 'Bearing-seat wear'],
            'inspection': ['Run-out at coupling', 'Keyway condition'],
        },
        'motor_fan': {
            'function': 'Moves cooling air through the motor.',
            'construction': 'Cast or fabricated fan keyed to the motor shaft.',
            'material': 'Aluminium, steel or reinforced polymer.',
            'operating_conditions': 'Rotates with the shaft; airflow depends on direction for unidirectional fans.',
            'failure_modes': ['Blade damage', 'Imbalance', 'Blocked intake'],
            'inspection': ['Visual check for damage and dirt build-up'],
        },
        'thrust_bearing': {
            'function': 'Carries the total down-thrust: hydraulic thrust from all impellers plus the weight of the rotating element (shafts, impellers, rotor).',
            'construction': 'Angular-contact ball bearings (often a matched pair) or spherical roller thrust bearing in the motor upper bracket, oil or grease lubricated.',
            'material': 'Bearing steel rolling elements and races.',
            'operating_conditions': 'Thrust rating must cover maximum down-thrust (including at shut-off) and any momentary up-thrust at start-up.',
            'failure_modes': ['Overload from under-estimated thrust', 'Lubricant degradation', 'Overheating', 'Brinelling from reverse rotation or transport'],
            'inspection': ['Bearing temperature', 'Oil level/quality or regreasing per schedule', 'Vibration (high-frequency envelope)'],
        },
        'motor_guide_bearing': {
            'function': 'Locates the lower end of the motor shaft radially.',
            'construction': 'Deep-groove ball bearing in the lower bracket.',
            'material': 'Bearing steel.',
            'operating_conditions': 'Radial load only.',
            'failure_modes': ['Lubrication failure', 'Contamination', 'Electrical fluting with VFD drives'],
            'inspection': ['Temperature, vibration, regreasing'],
        },
        'column_pipe': {
            'function': 'Carries the pumped liquid from the bowl assembly to the discharge head and suspends the bowl assembly.',
            'construction': 'Flanged or threaded pipe sections, typically 1.5–3 m (5–10 ft) long, with bearing retainers at the joints.',
            'material': 'Carbon steel, galvanised steel or stainless steel.',
            'operating_conditions': 'Internal pressure equal to discharge pressure at that elevation; tensile load from suspended weight.',
            'failure_modes': ['Corrosion/erosion and wall loss', 'Leaking joints reducing delivered flow', 'Misalignment of sections causing bearing wear'],
            'inspection': ['Wall thickness measurement at overhaul', 'Flange face and gasket condition', 'Straightness of assembled column'],
        },
        'gasket': {
            'function': 'Seals flanged joints.',
            'construction': 'Flat ring gasket or O-ring in a groove.',
            'material': 'Elastomer or compressed fibre suited to the fluid.',
            'operating_conditions': 'Bolted compression.',
            'failure_modes': ['Extrusion', 'Chemical attack', 'Loss of bolt load'],
            'inspection': ['Replace at reassembly'],
        },
        'bearing_retainer': {
            'function': 'Holds the line-shaft bearing concentric with the column at each joint.',
            'construction': 'Rim clamped between column flanges with radial ribs (spider) supporting a central hub.',
            'material': 'Bronze, cast iron or stainless steel.',
            'operating_conditions': 'Flow passes between the ribs; adds a small pressure loss.',
            'failure_modes': ['Rib erosion', 'Hub bore wear'],
            'inspection': ['Hub bore diameter and concentricity at overhaul'],
        },
        'lineshaft_bearing': {
            'function': 'Supports the line shaft radially and limits whip between the head and the bowls.',
            'construction': 'Fluted rubber-lined or bronze sleeve bearing, lubricated by the pumped water (open line shaft). Enclosed-shaft designs use oil-lubricated bronze bearings inside an enclosing tube.',
            'material': 'Nitrile/neoprene rubber, bronze, or engineered polymers.',
            'operating_conditions': 'Rubber bearings must be pre-lubricated before start if the column is dry (deep static levels).',
            'failure_modes': ['Dry-run burn-out at start', 'Abrasive wear from sand', 'Swelling from incompatible fluids'],
            'inspection': ['Bore diameter / clearance check at overhaul', 'Pre-lubrication system function'],
        },
        'line_shaft': {
            'function': 'Transmits torque from the head shaft to the bowl shaft along the column.',
            'construction': 'Sections matching the column length, joined by threaded couplings; ground at bearing journals.',
            'material': 'Carbon steel, 416 or 316 stainless steel; sometimes with stainless sleeves at journals.',
            'operating_conditions': 'Combined torsion and tension; elongates under hydraulic thrust, which must be allowed for when setting impeller lift.',
            'failure_modes': ['Thread unscrewing from reverse rotation', 'Fatigue', 'Journal wear', 'Straightness loss'],
            'inspection': ['Straightness (TIR) per section', 'Journal wear', 'Thread condition'],
        },
        'bowl_shaft': {
            'function': 'Carries the impellers and transmits torque from the line shaft to them.',
            'construction': 'Ground shaft through all bowls; impellers fixed by taper collets or keys and split rings.',
            'material': 'Stainless steel (410/416/316) or duplex for corrosive service.',
            'operating_conditions': 'Full torque at top stage; supported by bowl and bell bearings.',
            'failure_modes': ['Wear at bearing journals', 'Fatigue at collet seats'],
            'inspection': ['Straightness and journal diameter at overhaul'],
        },
        'shaft_couplings': {
            'function': 'Join shaft sections end-to-end.',
            'construction': 'Threaded sleeve coupling; threads are cut so that normal rotation tightens them.',
            'material': 'Stainless or carbon steel.',
            'operating_conditions': 'Reverse rotation (backspin after shutdown) can unscrew them; non-reverse ratchets or check valves are used where backspin is expected.',
            'failure_modes': ['Unscrewing', 'Thread galling'],
            'inspection': ['Butt the shaft ends correctly at assembly', 'Check thread condition'],
        },
        'discharge_case': {
            'function': 'Top bowl: collects flow from the last stage diffuser and transitions it into the column; houses the top bowl bearing.',
            'construction': 'Casting with straightening ribs, bearing hub and flanges for the column and the top bowl.',
            'material': 'Cast iron, ductile iron, bronze or stainless steel.',
            'operating_conditions': 'Full discharge pressure at the bowl level.',
            'failure_modes': ['Erosion', 'Bearing hub wear'],
            'inspection': ['Bore and bearing wear at overhaul'],
        },
        'bowl': {
            'function': 'Diffuser casing for one stage: converts the swirl (velocity) leaving the impeller into pressure and guides flow to the next impeller eye.',
            'construction': 'Casting with integral diffuser vanes, central bearing hub and bolted flanges; bowls are often enamel- or glass-lined to improve efficiency in water service.',
            'material': 'Cast iron (often enamel-lined), ductile iron, bronze, stainless or duplex stainless steel.',
            'operating_conditions': 'Pressure rises stage by stage; lowest bowl must have adequate submergence and NPSH margin.',
            'failure_modes': ['Erosion of vanes by sand', 'Corrosion', 'Wear-ring seat wear increasing recirculation'],
            'inspection': ['Vane and passage erosion', 'Wear-ring clearance', 'Bearing bore'],
        },
        'wear_ring': {
            'function': 'Renewable close-clearance ring that limits leakage from the impeller discharge back to its eye.',
            'construction': 'Press-fit ring in the bowl around the impeller skirt (impeller rings may also be fitted).',
            'material': 'Bronze, stainless steel or hardened materials for abrasive service.',
            'operating_conditions': 'Running clearance per manufacturer; leakage rises as clearance increases, reducing efficiency.',
            'failure_modes': ['Abrasive wear', 'Galling (dissimilar hardness required)', 'Loose fit'],
            'inspection': ['Measure diametral clearance at overhaul and compare with manufacturer limit'],
        },
        'bowl_bearing': {
            'function': 'Radial support of the bowl shaft at each bowl, discharge case and suction bell.',
            'construction': 'Sleeve bushing press-fitted in the bowl hub; product lubricated.',
            'material': 'Bronze, rubber, carbon or engineered polymers; harder materials for sandy water.',
            'operating_conditions': 'Lubricated by pumped liquid; the bell bearing may be grease-packed with a sand collar.',
            'failure_modes': ['Abrasive wear', 'Seizure on dry running', 'Loss of interference fit'],
            'inspection': ['Clearance measurement at overhaul'],
        },
        'impeller': {
            'function': 'Adds energy to the liquid: rotating blades increase angular momentum (velocity and pressure).',
            'construction': 'Enclosed mixed-flow impeller (hub, blades and front shroud) cast as one piece; fixed to the shaft by a taper collet. Semi-open impellers are also used and are set with a smaller axial clearance.',
            'material': 'Bronze, cast iron, stainless steel or duplex.',
            'operating_conditions': 'Rotates at motor speed; produces both head and axial down-thrust.',
            'failure_modes': ['Cavitation erosion at blade inlet (low submergence/NPSH)', 'Abrasive wear', 'Loose collet', 'Imbalance'],
            'inspection': ['Inlet edges for cavitation pitting', 'Skirt/wear surface clearance', 'Collet seating'],
        },
        'collet': {
            'function': 'Locks the impeller on the shaft by friction.',
            'construction': 'Split tapered sleeve driven into the impeller hub bore.',
            'material': 'Steel or stainless steel.',
            'operating_conditions': 'Must resist torque and thrust; removed with a collet driver at overhaul.',
            'failure_modes': ['Slipping on shaft', 'Corrosion seizure'],
            'inspection': ['Seating and contact pattern'],
        },
        'suction_bell': {
            'function': 'Guides liquid smoothly into the first-stage impeller and holds the bottom shaft bearing.',
            'construction': 'Bell-mouth casting with ribs and bearing hub; often fitted with a strainer.',
            'material': 'Cast iron, ductile iron, bronze or stainless steel.',
            'operating_conditions': 'Submergence above the bell lip must meet intake design guidance to avoid vortices and air entrainment.',
            'failure_modes': ['Vortex/air entrainment from low submergence', 'Abrasive erosion', 'Debris blockage'],
            'inspection': ['Check bell and ribs for erosion', 'Verify water level versus minimum submergence'],
        },
        'strainer': {
            'function': 'Keeps large debris out of the pump.',
            'construction': 'Clip-on cone or basket strainer of bars or perforated plate; open area normally several times the bell area.',
            'material': 'Galvanised or stainless steel.',
            'operating_conditions': 'Clogging raises inlet losses and reduces NPSH available.',
            'failure_modes': ['Clogging', 'Corrosion and loss of bars'],
            'inspection': ['Clean at each pump pull', 'Check differential/level if monitored'],
        },
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
