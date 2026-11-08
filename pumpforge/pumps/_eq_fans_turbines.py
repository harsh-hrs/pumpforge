"""Rotating Equipment — EQ-146 … EQ-154: fans (axial, centrifugal, ID, FD, PA) and turbines (steam, gas, hydraulic, expander)."""
import math
from mathutils import Matrix
from pumpforge.core import Model, lathe, cyl, box, csg, split, join, split_many, rotate, extrude_poly, TAU, OPERATE_FRAMES
from pumpforge.valvekit import P, keys_loop, smooth_pulse
from pumpforge.parts import add_motor_h, add_coupling, add_drive_y, add_tracers, hollow_pipe, transform_parts
from pumpforge.rotkit import (blade_row, radial_blades, scroll_polys, pedestal, local_pivot, axis_rot_keys, ring_of, flow_ring)
from pumpforge.shapes import sweep_tube
from pumpforge.common_meta import C

CAT = '7 · Rotating Equipment – Additional Machinery'


def _model(pid, title):
    return Model(pid, title, CAT, META[pid])


def _bands_x(m, segs, cz, r_in, r_out, title, desc, kind='pressure'):
    rings = [cyl(f'pb{i}', r_out, a, b, f'pressure_{lev}', 64, axis='X', center=(0, 0, cz), r_in=r_in) for i, (a, b, lev) in enumerate(segs)]
    m.overlay(kind, join('bands', rings), title, desc, split=True)


# =============================================================== EQ-146 Axial flow fan
def axial_flow_fan(out):
    m = _model('axial_flow_fan', 'Axial Flow Fan (Tube-Axial with Guide Vanes, In-Line Motor)')
    CZ, R = 0.55, 0.36
    cas = lathe('cas', [(R + 0.004, -0.42), (R + 0.012, -0.42), (R + 0.012, 0.42), (R + 0.004, 0.42)], 'paint_grey', 96, axis='X', center=(0, 0, CZ))
    fl = [cyl(f'fl{i}', R + 0.06, x - 0.012, x + 0.012, 'paint_grey', 96, axis='X', center=(0, 0, CZ), r_in=R + 0.004) for i, x in enumerate((-0.43, 0.43))]
    legs = [box(f'lg{i}', (0.05, 0.05, CZ - R), (x, sy * 0.25, (CZ - R) / 2), 'paint_grey') for i, (x, sy) in enumerate(((-0.25, -1), (-0.25, 1), (0.25, -1), (0.25, 1)))]
    P(m, 'casing', 'Fan Casing (Tube) with Flanges & Supports', 'casing', [cas] + fl + legs, explode=(0, 0, -0.3), ref='af_casing')
    bell = lathe('bell', [(R + 0.004, -0.43), (R + 0.012, -0.43), (R + 0.16, -0.62), (R + 0.15, -0.63)], 'paint_grey', 96, axis='X', center=(0, 0, CZ))
    scr = cyl('scr', R + 0.17, -0.64, -0.635, 'steel_dark', 64, axis='X', center=(0, 0, CZ), r_in=R + 0.16)
    P(m, 'inlet_bell', 'Inlet Bell (Bellmouth) & Guard Ring', 'casing', [bell, scr], explode=(-0.4, 0, 0), ref='af_bell')
    hub = join('hub', [lathe('hb', [(0.0, -0.32), (0.07, -0.3), (0.13, -0.22), (0.14, -0.12), (0.14, -0.04), (0.0, -0.04)], 'aluminium', 64, axis='X', center=(0, 0, CZ)),
                       blade_row('bl', -0.13, 0.135, R - 0.008, 8, 'aluminium', chord=0.13, thick=0.012, stagger=0.75, twist=0.55, cz=CZ, steps=6)])
    ph = P(m, 'impeller', 'Impeller: Hub & 8 Aerofoil Blades (adjustable pitch)', 'rotating_element', hub, explode=(-0.2, -0.6, 0), ref='af_impeller', section='keep', pivot=(0, 0, CZ))
    ph.spin('X', 4)
    gv = blade_row('gv', 0.12, 0.15, R + 0.004, 11, 'paint_grey', chord=0.12, thick=0.008, stagger=-0.2, twist=-0.15, cz=CZ, steps=3)
    P(m, 'guide_vanes', 'Outlet Guide Vanes (Straighteners)', 'stator', gv, explode=(0.3, 0.6, 0), ref='af_guide_vanes', section='keep')
    mo = join('mo', [cyl('mb', 0.15, -0.03, 0.36, 'paint_motor', 64, axis='X', center=(0, 0, CZ), ch=0.01),
                     lathe('mt', [(0.15, 0.36), (0.1, 0.46), (0.0, 0.5), (0.0, 0.36)], 'paint_motor', 48, axis='X', center=(0, 0, CZ)),
                     box('tb', (0.08, 0.06, 0.2), (0.25, 0, CZ + 0.24), 'paint_motor')])
    P(m, 'motor', 'In-Line Motor (in the air stream) & Terminal Box', 'motor', mo, explode=(0.5, 0, 0.3), ref='af_motor')
    add_tracers(m, 'swirl', 'Air Tracers', [(-0.8, 0, CZ + 0.24), (-0.2, 0, CZ + 0.24), (0.05, 0.12, CZ + 0.2), (0.2, 0, CZ + 0.24), (0.9, 0, CZ + 0.24)], n=8, radius=0.012, mat='air')
    for j, a in enumerate((0.3, 2.4, 4.5)):
        r = 0.25
        path = [(-0.85, r * math.cos(a), CZ + r * math.sin(a)), (-0.2, r * math.cos(a), CZ + r * math.sin(a))]
        for k in range(1, 9):
            aa = a - 0.35 * k / 8
            path.append((-0.2 + 0.32 * k / 8, r * math.cos(aa), CZ + r * math.sin(aa)))
        path.append((0.95, r * math.cos(a - 0.35), CZ + r * math.sin(a - 0.35)))
        m.flow(f'air_{j}', path, 'air', 0.008, 0.2, speed=[1, 1.1] + [1.4] * 8 + [1.2])
    return m.export(out)


# =============================================================== centrifugal fan family (EQ-147 … EQ-150)
def _centrifugal(pid, title, R2=0.3, wimp=0.16, nbl=12, curve=0.55, kind='air', variant='general'):
    m = _model(pid, title)
    CZ = R2 * 1.9 + 0.15
    r0, r1 = R2 * 1.08, R2 * 1.72
    W = wimp + 0.06
    xout = r1 * 0.95
    t = 0.008
    so, si, do, di = scroll_polys(0.0, CZ, r0, r1, xout, t)
    R1 = R2 * 0.62
    outer = [extrude_poly('so', so, -W / 2 - t, W / 2 + t, 'paint_blue' if kind == 'air' else 'paint_grey', plane='XZ'),
             box('do', (xout - do[0], W + 2 * t, do[3] - do[2]), ((do[0] + xout) / 2, 0, (do[2] + do[3]) / 2), 'paint_grey')]
    inner = [extrude_poly('si', si, -W / 2, W / 2, 'paint_grey', plane='XZ'),
             box('di', (di[1] - di[0], W, di[3] - di[2]), ((di[0] + di[1]) / 2, 0, (di[2] + di[3]) / 2), 'paint_grey'),
             cyl('eye', R1 * 1.04, -W / 2 - 0.05, -W / 2 + 0.001, 'paint_grey', 64, axis='Y', center=(0, 0, CZ)),
             cyl('shh', 0.04, W / 2 - 0.01, W / 2 + 0.05, 'paint_grey', 32, axis='Y', center=(0, 0, CZ))]
    mat = 'paint_grey' if kind != 'air' else 'paint_blue'
    hous = csg('housing', outer, inner, mat)
    of = box('ofl', (0.02, W + 0.12, do[3] - do[2] + 0.12), (xout - 0.01, 0, (do[2] + do[3]) / 2), mat)
    ofl = csg('ofl', [of], [box('ofi', (0.04, W, di[3] - di[2]), (xout - 0.01, 0, (di[2] + di[3]) / 2), mat)], mat)
    P(m, 'housing', 'Scroll (Volute) Housing with Outlet', 'casing', [hous, ofl], explode=(0, 0, 0), ref='cf_housing', section='split')
    bp = cyl('bp', R2, W / 2 - 0.03 - 0.01, W / 2 - 0.03, 'steel', 96, axis='Y', center=(0, 0, CZ))
    shr = lathe('shr', [(R1, -W / 2 + 0.03 - 0.03), (R1 + 0.004, -W / 2 + 0.03 - 0.03), (R2 * 0.9, -W / 2 + 0.03), (R2, -W / 2 + 0.03), (R2, -W / 2 + 0.04),
                        (R2 * 0.88, -W / 2 + 0.04), (R1 - 0.004, -W / 2 + 0.005 - 0.02)], 'steel', 96, axis='Y', center=(0, 0, CZ))
    bl = radial_blades('bl', -W / 2 + 0.035, W / 2 - 0.04, R1 * 0.95, R2 - 0.004, nbl, 'steel', curve=curve, t=0.006, cx=0, cz=CZ, k=10)
    hub = cyl('hub', 0.07, 0.0, W / 2 - 0.03, 'steel', 48, axis='Y', center=(0, 0, CZ))
    sh = cyl('sh', 0.035, -0.02, W / 2 + 0.75, 'steel', 32, axis='Y', center=(0, 0, CZ), ch=0.003)
    imp = P(m, 'impeller', f'Impeller ({nbl} {"backward-curved aerofoil" if curve > 0 else "radial"} blades), Hub & Shaft', 'rotating_element',
            [bp, shr, bl, hub, sh], explode=(0, -0.0, R2 * 2.2), ref='cf_impeller', section='split', pivot=(0, 0, CZ))
    imp.spin('Y', 2)
    cone = lathe('cone', [(R1 * 0.98, -W / 2 + 0.03), (R1 * 1.01, -W / 2 + 0.03), (R1 * 1.35, -W / 2 - 0.16), (R1 * 1.32, -W / 2 - 0.165)], 'paint_grey', 96, axis='Y', center=(0, 0, CZ))
    P(m, 'inlet_cone', 'Inlet Cone (Venturi)', 'casing', cone, explode=(0, -0.45, 0), ref='cf_inlet_cone', section='hide')
    yb = W / 2 + 0.2
    peds = [pedestal('pb1', W / 2 + 0.2, CZ, 0.035, 0.0, axis='Y'), pedestal('pb2', W / 2 + 0.6, CZ, 0.035, 0.0, axis='Y')]
    P(m, 'bearings', 'Bearing Pedestals (Plummer Blocks, Fixed & Free)', 'bearings', peds, explode=(0, 0.3, -0.2), ref='cf_bearings', section='keep')
    add_drive_y(m, W / 2 + 0.75, CZ, 0.0, 0.035, motor_R=R2 * 0.6, motor_L=R2 * 1.5, revs=2, base=False, explode0=0.5)
    stand = [box('st1', (r1 * 2.1, W + 0.3, 0.06), (r1 * 0.2, 0, 0.03), 'paint_grey'),
             box('st2', (0.2, W + 0.1, CZ - r1 - 0.06), (-r1 * 0.2, 0, 0.06 + (CZ - r1 - 0.06) / 2), 'paint_grey')]
    P(m, 'stand', 'Fan Housing Support & Sole Plate', 'baseplate', stand, explode=(0, 0, -0.3), ref='cf_stand', section='keep')
    # variant extras
    yin = -W / 2 - 0.165
    if variant in ('id',):
        ib = csg('ib', [box('ibo', (R1 * 3.2, 0.5, R1 * 3.2), (0, yin - 0.25, CZ), 'paint_grey')],
                 [box('ibi', (R1 * 3.0, 0.46, R1 * 3.0), (0, yin - 0.25, CZ), 'paint_grey'), cyl('ibh', R1 * 1.32, yin - 0.05, yin + 0.05, 'paint_grey', 64, axis='Y', center=(0, 0, CZ)),
                  box('ibt', (R1 * 3.0, 0.46, 0.4), (0, yin - 0.25, CZ + R1 * 1.6), 'paint_grey')], 'paint_grey')
        duct = csg('dct', [box('dco', (R1 * 3.2, 0.5, 0.6), (0, yin - 0.25, CZ + R1 * 1.6 + 0.3), 'paint_grey')], [box('dci', (R1 * 3.0, 0.46, 0.7), (0, yin - 0.25, CZ + R1 * 1.6 + 0.3), 'paint_grey')], 'paint_grey')
        P(m, 'inlet_box', 'Inlet Box & Flue-Gas Duct', 'casing', [ib, duct], explode=(0, -0.5, 0), ref='cf_inlet_box', section='split')
        zl = CZ + R1 * 1.6 + 0.3
        lp = m.part('inlet_damper', 'Inlet Louvre Damper (blades modulate)', 'damper', section='hide', explode=(0, -0.5, 0.5), info={'ref': 'cf_damper'})
        for i in range(4):
            x = -R1 * 1.5 + R1 * 3.0 * (i + 0.5) / 4
            b = box(f'lv{i}', (R1 * 3.0 / 4 - 0.01, 0.44, 0.006), (x, yin - 0.25, zl), 'steel')
            ms = lp.add(join(f'lvj{i}', [b, cyl(f'lvs{i}', 0.008, yin - 0.5, yin, 'steel', 12, axis='Y', center=(x, 0, zl))]), smooth_angle=30)
            local_pivot(ms, (x, yin - 0.25, zl))
            axis_rot_keys(m, ms, (0, 1, 0), lambda tt: 0.35 + 0.35 * math.sin(TAU * tt))
        m.flow('flue_gas', [(0, yin - 0.25, zl + 0.6), (0, yin - 0.25, CZ), (0, yin + 0.1, CZ), (0, -W / 2 + 0.05, CZ - 0.02)] +
               flow_ring(0, CZ, R2 * 1.25, math.radians(-90), math.radians(-270), 24, y=0.0) + [(xout + 0.5, 0, CZ + (r0 + r1) / 2)], 'flue_gas', 0.012, 0.3)
    else:
        if variant in ('fd', 'pa'):
            igv = m.part('inlet_guide_vanes', 'Inlet Guide Vanes (variable, pre-swirl capacity control)', 'damper', explode=(0, -0.6, 0.3), info={'ref': 'cf_igv'})
            for i in range(8):
                a = TAU * i / 8
                v = box(f'ig{i}', (R1 * 1.1, R1 * 0.45, 0.004), (R1 * 0.6 * math.cos(a), yin + 0.03, CZ + R1 * 0.6 * math.sin(a)), 'steel')
                v = rotate(v, -a, 'Y', (R1 * 0.6 * math.cos(a), 0, CZ + R1 * 0.6 * math.sin(a)))
                ms = igv.add(v, smooth_angle=30)
                local_pivot(ms, (R1 * 0.6 * math.cos(a), yin + 0.03, CZ + R1 * 0.6 * math.sin(a)))
                axis_rot_keys(m, ms, (math.cos(a), 0, math.sin(a)), lambda tt: 0.6 + 0.4 * math.sin(TAU * tt))
            ring = cyl('igr', R1 * 1.36, yin, yin + 0.06, 'paint_grey', 64, axis='Y', center=(0, 0, CZ), r_in=R1 * 1.28)
            P(m, 'igv_ring', 'IGV Housing Ring & Actuator Linkage', 'damper', ring, explode=(0, -0.7, 0), ref='cf_igv', section='hide')
        if variant == 'fd':
            sil = csg('sil', [cyl('so', R1 * 1.7, yin - 0.6, yin - 0.05, 'paint_grey', 64, axis='Y', center=(0, 0, CZ))],
                      [cyl('si', R1 * 1.3, yin - 0.7, yin, 'paint_grey', 64, axis='Y', center=(0, 0, CZ))], 'paint_grey')
            pod = cyl('pod', R1 * 0.55, yin - 0.55, yin - 0.1, 'foam', 48, axis='Y', center=(0, 0, CZ))
            P(m, 'inlet_silencer', 'Inlet Silencer (absorptive, with acoustic pod)', 'casing', [sil, pod], explode=(0, -0.9, 0), ref='cf_silencer', section='split')
        if variant == 'pa':
            zc = (di[2] + di[3]) / 2
            od = m.part('outlet_damper', 'Outlet Isolating / Control Damper', 'damper', explode=(0.5, 0, 0.3), info={'ref': 'cf_damper'})
            n = 3
            for i in range(n):
                z = di[2] + (di[3] - di[2]) * (i + 0.5) / n
                b = box(f'od{i}', (0.005, W - 0.01, (di[3] - di[2]) / n - 0.01), (xout + 0.15, 0, z), 'steel')
                ms = od.add(join(f'odj{i}', [b, cyl(f'ods{i}', 0.008, -W / 2 - 0.03, W / 2 + 0.03, 'steel', 12, axis='Y', center=(xout + 0.15, 0, z))]), smooth_angle=30)
                local_pivot(ms, (xout + 0.15, 0, z))
                axis_rot_keys(m, ms, (0, 1, 0), lambda tt: 0.5 + 0.3 * math.sin(TAU * tt))
            dfr = csg('dfr', [box('dfo', (0.3, W + 2 * t, di[3] - di[2] + 2 * t), (xout + 0.15, 0, zc), 'paint_grey')], [box('dfi', (0.4, W, di[3] - di[2]), (xout + 0.15, 0, zc), 'paint_grey')], 'paint_grey')
            P(m, 'damper_frame', 'Outlet Damper Frame', 'damper', dfr, explode=(0.6, 0, 0), ref='cf_damper', section='keep')
        y0 = yin - (0.6 if variant == 'fd' else 0.3)
        for j, a_in in enumerate((0.0, 2.1, 4.2)):
            r = R1 * 0.5
            st = a_in - 0.3
            k = math.floor((st - math.pi / 2) / TAU)
            en = math.pi / 2 + TAU * k
            if en > st - 1.0:
                en -= TAU
            m.flow(f'{kind}_{j}', [(r * math.cos(a_in), y0, CZ + r * math.sin(a_in)), (r * math.cos(a_in), -W / 2 + 0.05, CZ + r * math.sin(a_in))] +
                   flow_ring(0, CZ, R2 * 1.25, st, en, 26, y=0.0) + [(xout + 0.4, 0, CZ + (r0 + r1) / 2)], kind, 0.01, 0.25)
    return m


def centrifugal_fan(out):
    m = _centrifugal('centrifugal_fan', 'Centrifugal Fan (Backward-Curved, Single Inlet, Direct Drive)', R2=0.28, wimp=0.16, nbl=12, curve=0.55, kind='air', variant='general')
    return m.export(out)


def induced_draft_fan(out):
    m = _centrifugal('induced_draft_fan', 'Induced Draft (ID) Fan with Inlet Box & Louvre Damper', R2=0.36, wimp=0.24, nbl=10, curve=0.45, kind='flue_gas', variant='id')
    return m.export(out)


def forced_draft_fan(out):
    m = _centrifugal('forced_draft_fan', 'Forced Draft (FD) Fan with Inlet Silencer & Inlet Guide Vanes', R2=0.34, wimp=0.22, nbl=12, curve=0.55, kind='air', variant='fd')
    return m.export(out)


def primary_air_fan(out):
    m = _centrifugal('primary_air_fan', 'Primary Air (PA) Fan — High Pressure, IGV & Outlet Damper', R2=0.4, wimp=0.12, nbl=16, curve=0.4, kind='air', variant='pa')
    return m.export(out)


# =============================================================== EQ-151 Steam turbine
def steam_turbine(out):
    m = _model('steam_turbine', 'Multistage Steam Turbine (Condensing, Single Casing)')
    CZ = 0.75
    stages = [(-0.36, 0.2, 0.235), (-0.24, 0.2, 0.25), (-0.12, 0.2, 0.27), (0.0, 0.2, 0.3), (0.13, 0.2, 0.335), (0.27, 0.2, 0.38)]
    ins = [(0.275, -0.6), (0.275, -0.4), (0.29, -0.26), (0.31, -0.14), (0.34, -0.02), (0.375, 0.1), (0.425, 0.24), (0.44, 0.4)]

    def r_in(x):
        for (r0, x0), (r1, x1) in zip(ins[:-1], ins[1:]):
            if x0 <= x <= x1:
                return r0 + (r1 - r0) * (x - x0) / (x1 - x0)
        return ins[-1][0]
    cas_o = [lathe('co', [(0.0, -0.62), (0.34, -0.62)] + [(r + 0.04, x) for r, x in ins[1:]] + [(0.48, 0.42), (0.0, 0.42)], 'paint_green', 96, axis='X', center=(0, 0, CZ)),
             box('exh', (0.5, 0.7, 0.45), (0.25, 0, CZ - 0.42), 'paint_green', bevel=0.01),
             box('chest', (0.3, 0.32, 0.2), (-0.5, 0, CZ + 0.38), 'paint_green', bevel=0.012),
             cyl('inl', 0.06, CZ + 0.47, CZ + 0.7, 'paint_green', 48, center=(-0.5, 0, 0))]
    cas_i = [lathe('ci', [(0.0, -0.6)] + ins + [(0.0, 0.4)], 'paint_green', 96, axis='X', center=(0, 0, CZ)),
             box('exi', (0.44, 0.64, 0.5), (0.25, 0, CZ - 0.45), 'paint_green'),
             box('chi', (0.26, 0.28, 0.12), (-0.5, 0, CZ + 0.4), 'paint_green'),
             cyl('inli', 0.045, CZ + 0.3, CZ + 0.72, 'paint_green', 48, center=(-0.5, 0, 0)),
             cyl('pt', 0.05, CZ + 0.2, CZ + 0.35, 'paint_green', 32, center=(-0.5, 0, 0)),
             cyl('gl1', 0.07, -0.66, -0.58, 'paint_green', 32, axis='X', center=(0, 0, CZ)), cyl('gl2', 0.07, 0.38, 0.46, 'paint_green', 32, axis='X', center=(0, 0, CZ))]
    P(m, 'casing', 'Turbine Casing (Inlet End, Exhaust Hood) & Steam Chest', 'casing', csg('st_case', cas_o, cas_i, 'paint_green'), explode=(0, 0, 0.0), ref='st_casing')
    rot = [cyl('sh', 0.06, -1.05, 0.95, 'steel', 48, axis='X', center=(0, 0, CZ), ch=0.004),
           cyl('drum', 0.12, -0.42, 0.33, 'steel', 64, axis='X', center=(0, 0, CZ)),
           cyl('tc', 0.12, -0.85, -0.82, 'steel', 48, axis='X', center=(0, 0, CZ))]
    dia = []
    for i, (x, rh, rt) in enumerate(stages):
        rot.append(cyl(f'dk{i}', rh, x + 0.012, x + 0.045, 'steel', 64, axis='X', center=(0, 0, CZ)))
        rot.append(blade_row(f'bk{i}', x + 0.03, rh - 0.003, rt, 40 + 4 * i, 'chrome', chord=0.028, thick=0.008, stagger=0.85, twist=0.3 * i / 5, cz=CZ, steps=2))
        dia.append(cyl(f'dr{i}', r_in(x - 0.04) - 0.001, x - 0.045, x - 0.03, 'paint_grey', 64, axis='X', center=(0, 0, CZ), r_in=rt + 0.004))
        dia.append(cyl(f'di{i}', rh - 0.01, x - 0.045, x - 0.03, 'paint_grey', 64, axis='X', center=(0, 0, CZ), r_in=0.125))
        dia.append(blade_row(f'nz{i}', x - 0.022, rh - 0.01, rt + 0.004, 36 + 4 * i, 'stainless', chord=0.026, thick=0.007, stagger=-0.95, twist=0.0, cz=CZ, steps=2))
    pr = P(m, 'rotor', 'Rotor: Shaft, Wheels (Discs) & Moving Blades (6 stages)', 'rotating_element', rot, explode=(0, -0.0, 0.9), ref='st_rotor', section='keep', pivot=(0, 0, CZ))
    pr.spin('X', 2)
    P(m, 'diaphragms', 'Diaphragms & Nozzle (Stationary Blade) Rings', 'stator', dia, explode=(0, 0, 0.55), ref='st_diaphragms', section='split')
    gv = join('gv', [cyl('vh', 0.04, CZ + 0.47, CZ + 0.8, 'chrome', 32, center=(-0.38, 0, 0)), box('act', (0.12, 0.14, 0.16), (-0.38, 0, CZ + 0.88), 'paint_red', bevel=0.01)])
    vp = join('vp', [cyl('vpl', 0.04, CZ + 0.31, CZ + 0.35, 'stainless', 32, center=(-0.5, 0, 0)), cyl('vst', 0.01, CZ + 0.35, CZ + 0.62, 'chrome', 16, center=(-0.5, 0, 0))])
    P(m, 'governor_actuator', 'Governor (Speed Control) Actuator', 'control', gv, explode=(0, 0, 0.5), ref='st_governor', section='keep')
    pv = P(m, 'control_valve', 'Steam Control (Governor) Valve Plug & Stem', 'control', vp, explode=(0, -0.4, 0.4), ref='st_control_valve', section='keep')
    keys_loop(m, pv, lambda tt: (0, 0, 0.02 + 0.006 * math.sin(TAU * tt)))
    brg = [pedestal('jb1', -0.75, CZ, 0.06, 0.0), pedestal('jb2', 0.7, CZ, 0.06, 0.0),
           cyl('tb', 0.13, -0.88, -0.79, 'cast_iron', 48, axis='X', center=(0, 0, CZ), r_in=0.062)]
    P(m, 'bearings', 'Journal Bearings (pedestals) & Thrust Bearing', 'bearings', brg, explode=(0, 0.6, 0), ref='st_bearings')
    gl = [cyl(f'g{i}', 0.068, x0, x1, 'bronze', 48, axis='X', center=(0, 0, CZ), r_in=0.061) for i, (x0, x1) in enumerate(((-0.66, -0.58), (0.38, 0.46)))]
    P(m, 'gland_seals', 'Labyrinth Gland Seals', 'seals', gl, explode=(0, 0.4, 0.3), ref='st_glands')
    add_coupling(m, 'coupling', 0.9, 1.0, CZ, 0.1, 0.06, explode=(0.4, 0, 0), revs=2, foot_z=0.0)
    gen = join('gen', [cyl('gb', 0.36, 1.05, 1.6, 'paint_blue', 64, axis='X', center=(0, 0, CZ)), box('gf', (0.5, 0.6, CZ - 0.25), (1.32, 0, (CZ - 0.25) / 2), 'paint_blue')])
    P(m, 'generator', 'Driven Generator (shown in part)', 'driven', gen, explode=(0.6, 0, 0), ref='st_generator', section='keep')
    fnd = box('fnd', (2.9, 1.0, 0.1), (0.2, 0, -0.05), 'cast_iron')
    P(m, 'foundation', 'Turbine Foundation / Baseplate', 'baseplate', fnd, explode=(0, 0, -0.3), ref='st_foundation', section='keep')
    path = [(-0.5, 0, CZ + 0.72), (-0.5, 0, CZ + 0.4), (-0.42, 0, CZ + 0.27)]
    for i, (x, rh, rt) in enumerate(stages):
        r = (rh + rt) / 2
        path += [(x - 0.04, 0, CZ + r), (x + 0.03, 0.03, CZ + r - 0.01), (x + 0.07, 0, CZ + r)]
    path += [(0.35, 0, CZ + 0.3), (0.28, 0, CZ - 0.1), (0.25, 0, CZ - 0.66)]
    m.flow('steam', path, 'steam', 0.009, 0.15)
    m.flow('steam_lower', [(p[0], -p[1], 2 * CZ - p[2]) for p in path[3:-2]] + [(0.35, 0, CZ - 0.3), (0.25, 0, CZ - 0.66)], 'steam', 0.009, 0.15)
    _bands_x(m, [(-0.6, -0.4, 9), (-0.4, -0.28, 8), (-0.28, -0.16, 7), (-0.16, -0.04, 5), (-0.04, 0.09, 4), (0.09, 0.22, 2), (0.22, 0.4, 0)], CZ, 0.44, 0.46,
             'Steam pressure through the stages', 'Steam expands stage by stage: in each nozzle row pressure falls and velocity rises; the moving blades turn that '
             'velocity into torque. Volume grows as pressure falls, so blades get longer toward the exhaust (condenser vacuum).')
    m.annotate('pressure', 'Inlet: high-pressure steam', (-0.55, 0, CZ + 0.55))
    m.annotate('pressure', 'Exhaust: condenser vacuum', (0.3, 0, CZ - 0.7))
    return m.export(out)


# =============================================================== EQ-152 Gas turbine
def gas_turbine(out):
    m = _model('gas_turbine', 'Industrial Gas Turbine (Single Shaft, Can-Annular Combustors)')
    CZ = 0.65
    comp = [(-0.55 + 0.055 * i, 0.1 + 0.012 * i, 0.27 - 0.008 * i) for i in range(8)]
    turb = [(0.28, 0.17, 0.27), (0.36, 0.17, 0.29), (0.44, 0.17, 0.31)]
    cas_o = [lathe('co', [(0.33, -0.62), (0.33, -0.12), (0.42, -0.08), (0.42, 0.2), (0.34, 0.25), (0.36, 0.5), (0.0, 0.5), (0.0, -0.62)], 'paint_grey', 96, axis='X', center=(0, 0, CZ))]
    cas_i = [lathe('ci', [(0.3, -0.64), (0.29, -0.12), (0.39, -0.08), (0.39, 0.2), (0.32, 0.25), (0.33, 0.52), (0.0, 0.52), (0.0, -0.64)], 'paint_grey', 96, axis='X', center=(0, 0, CZ))]
    P(m, 'casing', 'Compressor, Combustor & Turbine Casings', 'casing', csg('gt_case', cas_o, cas_i, 'paint_grey'), explode=(0, 0, 0), ref='gt_casing')
    inl = lathe('io', [(0.31, -0.64), (0.34, -0.64), (0.5, -0.85), (0.5, -0.87), (0.47, -0.87)], 'paint_grey', 96, axis='X', center=(0, 0, CZ))
    P(m, 'inlet', 'Air Inlet Bellmouth', 'casing', inl, explode=(-0.4, 0, 0), ref='gt_inlet')
    rot = [cyl('sh', 0.05, -0.95, 0.85, 'steel', 48, axis='X', center=(0, 0, CZ), ch=0.004),
           lathe('hub', [(0.0, -0.6), (0.09, -0.6), (0.19, -0.12), (0.19, -0.1), (0.12, 0.0), (0.12, 0.2), (0.16, 0.24), (0.16, 0.5), (0.0, 0.5)], 'steel', 64, axis='X', center=(0, 0, CZ))]
    stat = []
    for i, (x, rh, rt) in enumerate(comp):
        rot.append(blade_row(f'cb{i}', x, rh + 0.0, rt, 30 + 2 * i, 'stainless', chord=0.03, thick=0.004, stagger=0.7, twist=0.25, cz=CZ, steps=2))
        stat.append(blade_row(f'cs{i}', x + 0.028, rh + 0.005, 0.3, 34 + 2 * i, 'paint_grey', chord=0.025, thick=0.004, stagger=-0.6, twist=0.1, cz=CZ, steps=2))
    for i, (x, rh, rt) in enumerate(turb):
        stat.append(blade_row(f'tn{i}', x - 0.03, rh, rt + 0.03, 28, 'chrome', chord=0.035, thick=0.009, stagger=-0.95, cz=CZ, steps=2))
        rot.append(blade_row(f'tb{i}', x, rh - 0.01, rt, 36, 'chrome', chord=0.032, thick=0.009, stagger=0.9, twist=0.2, cz=CZ, steps=2))
    pr = P(m, 'rotor', 'Rotor: Compressor & Turbine Blading on a Single Shaft', 'rotating_element', rot, explode=(0, 0, 0.9), ref='gt_rotor', section='keep', pivot=(0, 0, CZ))
    pr.spin('X', 3)
    P(m, 'stator_vanes', 'Compressor Stator Vanes & Turbine Nozzle Guide Vanes', 'stator', stat, explode=(0, 0, 0.55), ref='gt_stators', section='split')
    cans, flames = [], []
    for i in range(6):
        a = TAU * i / 6 + math.pi / 6
        def at(x, r):
            return (x, r * math.cos(a), CZ + r * math.sin(a))
        cans.append(sweep_tube(f'can{i}', [at(-0.08, 0.26), at(0.08, 0.28), at(0.2, 0.24)], 0.055, 'stainless', 20))
        cans.append(sweep_tube(f'fn{i}', [at(-0.1, 0.26), at(-0.06, 0.262)], 0.02, 'chrome', 12))
        flames.append(sweep_tube(f'fl{i}', [at(-0.05, 0.262), at(0.05, 0.276), at(0.16, 0.25)], 0.03, 'flame', 12))
    P(m, 'combustors', 'Combustion Cans (6) with Fuel Nozzles', 'combustion', cans, explode=(0, 0.7, 0), ref='gt_combustors', section='keep')
    pf = P(m, 'flame', 'Flame Zone', 'combustion', flames, explode=(0, 0.9, 0.2), ref='gt_flame', section='keep')
    keys_loop(m, pf, lambda tt: (1 + 0.06 * math.sin(TAU * 6 * tt), 1 + 0.06 * math.cos(TAU * 5 * tt), 1 + 0.06 * math.sin(TAU * 7 * tt)), 'scale')
    exh = join('exh', [lathe('eo', [(0.36, 0.5), (0.4, 0.5), (0.5, 0.85), (0.5, 0.88), (0.46, 0.88)], 'paint_grey', 96, axis='X', center=(0, 0, CZ)),
                       lathe('ec', [(0.0, 0.5), (0.16, 0.5), (0.1, 0.85), (0.0, 0.85)], 'paint_grey', 64, axis='X', center=(0, 0, CZ))])
    P(m, 'exhaust', 'Exhaust Diffuser & Collector', 'casing', exh, explode=(0.5, 0, 0), ref='gt_exhaust')
    brg = [pedestal('b1', -0.75, CZ, 0.05, 0.0), pedestal('b2', 0.72, CZ, 0.05, 0.0, w=0.08)]
    P(m, 'bearings', 'Journal & Thrust Bearings', 'bearings', brg, explode=(0, 0.6, 0), ref='gt_bearings')
    acc = box('acc', (0.3, 0.4, 0.4), (-1.15, 0, CZ - 0.1), 'paint_blue', bevel=0.02)
    P(m, 'accessory_gearbox', 'Accessory Gearbox & Starter', 'auxiliary', acc, explode=(-0.4, 0, 0), ref='gt_accessories')
    fnd = box('fnd', (2.4, 1.0, 0.1), (-0.1, 0, -0.05), 'cast_iron')
    P(m, 'skid', 'Base Skid', 'baseplate', fnd, explode=(0, 0, -0.3), ref='gt_skid', section='keep')
    for j, a in enumerate((math.pi / 6, math.pi / 6 + TAU / 3, math.pi / 6 + 2 * TAU / 3)):
        def q(x, r):
            return (x, r * math.cos(a), CZ + r * math.sin(a))
        m.flow(f'air_{j}', [q(-0.9, 0.42), q(-0.62, 0.24), q(-0.15, 0.24), q(-0.08, 0.26)], 'air', 0.008, 0.15, speed=[1, 1.4, 1.0, 0.8])
        m.flow(f'combustion_{j}', [q(-0.08, 0.26), q(0.08, 0.28), q(0.2, 0.24)], 'flame', 0.009, 0.1, speed=[1.0, 1.5, 2.0])
        m.flow(f'exhaust_{j}', [q(0.2, 0.24), q(0.3, 0.22), q(0.5, 0.25), q(0.9, 0.35)], 'exhaust', 0.009, 0.15, speed=[2.2, 2.4, 1.6, 1.0])
    _bands_x(m, [(-0.62, -0.5, 1), (-0.5, -0.38, 3), (-0.38, -0.26, 5), (-0.26, -0.12, 7), (-0.12, 0.22, 9), (0.22, 0.32, 6), (0.32, 0.4, 4), (0.4, 0.5, 2), (0.5, 0.88, 0)],
             CZ, 0.51, 0.53, 'Pressure through the gas turbine (Brayton cycle)',
             'The axial compressor raises air pressure stage by stage; fuel burns at nearly constant pressure in the combustors; the hot gas expands through the '
             'turbine stages, which drive the compressor and the load; it leaves through the exhaust near atmospheric pressure.')
    m.annotate('pressure', 'Compression', (-0.35, 0, CZ + 0.6))
    m.annotate('pressure', 'Combustion (≈ constant pressure)', (0.05, 0, CZ + 0.6))
    m.annotate('pressure', 'Expansion', (0.4, 0, CZ + 0.6))
    return m.export(out)


# =============================================================== EQ-153 Hydraulic (Francis) turbine
def hydraulic_turbine(out):
    m = _model('hydraulic_turbine', 'Francis Hydraulic Turbine (Vertical Shaft) with Generator')
    ZR = 0.7
    Rst = 0.42
    segs = []
    inner = []
    n = 10
    for k in range(n):
        a0, a1 = math.pi / 2 - TAU * k / n * 0.95, math.pi / 2 - TAU * (k + 1.15) / n * 0.95
        rho = 0.2 * (1 - 0.8 * k / n)
        rc = Rst + rho * 0.85
        pts = [(rc * math.cos(a0 + (a1 - a0) * j / 6), rc * math.sin(a0 + (a1 - a0) * j / 6), ZR) for j in range(7)]
        segs.append(sweep_tube(f'sp{k}', pts, rho + 0.012, 'paint_blue', 24))
        inner.append(sweep_tube(f'spi{k}', pts, rho, 'paint_blue', 24))
    inl = [(-1.1, Rst + 0.17, ZR), (0.02, Rst + 0.17, ZR)]
    segs.append(sweep_tube('inl', inl, 0.212, 'paint_blue', 24))
    inner.append(sweep_tube('inli', [(-1.2, Rst + 0.17, ZR), (0.03, Rst + 0.17, ZR)], 0.2, 'paint_blue', 24))
    inner.append(cyl('core', Rst + 0.03, ZR - 0.09, ZR + 0.09, 'paint_blue', 96))
    sc = csg('spiral', segs, inner, 'paint_blue')
    P(m, 'spiral_casing', 'Spiral Casing (Scroll) & Inlet Pipe', 'casing', sc, explode=(0, 0, -0.0), ref='ht_spiral')
    srings = [cyl('sr1', Rst + 0.04, ZR + 0.07, ZR + 0.09, 'paint_grey', 96, r_in=0.18), cyl('sr2', Rst + 0.04, ZR - 0.09, ZR - 0.07, 'paint_grey', 96, r_in=0.2)]
    from pumpforge.rotkit import ring_of as _ro
    stay = _ro('stay', 12, lambda i: box(f'sv{i}', (0.09, 0.012, 0.14), (Rst - 0.01, 0, ZR), 'paint_grey'), cz=0, axis='Z')
    P(m, 'stay_ring', 'Stay Ring & Stay Vanes (fixed)', 'stator', srings + [stay], explode=(0, 0, 0.0), ref='ht_stay_vanes')
    gp = m.part('wicket_gates', 'Wicket Gates (Guide Vanes) — open/close to control flow', 'stator', explode=(0, 0, 0.45), info={'ref': 'ht_wicket_gates'})
    rg = 0.3
    for i in range(16):
        a = TAU * i / 16
        gx, gy = rg * math.cos(a), rg * math.sin(a)
        v = box(f'wg{i}', (0.075, 0.009, 0.135), (gx, gy, ZR), 'bronze', bevel=0.003)
        v = rotate(v, a + math.pi / 2 + 0.6, 'Z', (gx, gy, ZR))
        st = cyl(f'ws{i}', 0.007, ZR - 0.08, ZR + 0.16, 'steel', 12, center=(gx, gy, 0))
        ms = gp.add(join(f'wgj{i}', [v, st]), smooth_angle=30)
        local_pivot(ms, (gx, gy, ZR))
        axis_rot_keys(m, ms, (0, 0, 1), lambda tt: -0.35 * smooth_pulse(tt, 0.25, 0.25, 0.25))
    crown = lathe('crown', [(0.0, ZR + 0.07), (0.25, ZR + 0.07), (0.25, ZR + 0.05), (0.08, ZR - 0.02), (0.0, ZR - 0.05)], 'stainless', 64)
    band = lathe('band', [(0.25, ZR - 0.07), (0.262, ZR - 0.07), (0.2, ZR - 0.2), (0.188, ZR - 0.2)], 'stainless', 64)
    bl = radial_blades('rb', -0.06, 0.06, 0.12, 0.245, 13, 'stainless', curve=-0.9, t=0.01, k=10)
    bl = rotate(bl, math.pi / 2, 'X')
    bl.data.transform(Matrix.Translation((0, 0, ZR - 0.005)))
    sh = cyl('sh', 0.05, ZR, 2.15, 'steel', 32, ch=0.004)
    gen_rot = cyl('gr', 0.42, 1.65, 1.95, 'paint_red', 64)
    poles = _ro('poles', 12, lambda i: box(f'pl{i}', (0.06, 0.08, 0.28), (0.44, 0, 1.8), 'copper'), axis='Z')
    pr = P(m, 'runner', 'Francis Runner (crown, band, 13 blades), Shaft & Generator Rotor', 'rotating_element', [crown, band, bl, sh, gen_rot, poles],
           explode=(0, -0.0, 0.0), ref='ht_runner', section='split')
    pr.spin('Z', -1)
    dt = [lathe('dto', [(0.2, ZR - 0.2), (0.215, ZR - 0.2), (0.3, ZR - 0.55), (0.285, ZR - 0.55)], 'paint_grey', 64),
          hollow_pipe('dte', [(0, 0, ZR - 0.55), (0, 0, 0.0), (1.2, 0, 0.0)], 0.3, 'paint_grey', 48, bend=0.35, t=0.015)]
    P(m, 'draft_tube', 'Draft Tube (cone, elbow & diffuser)', 'casing', dt, explode=(0, 0, -0.3), ref='ht_draft_tube')
    hc = csg('hc', [cyl('hco', Rst + 0.04, ZR + 0.09, ZR + 0.16, 'paint_grey', 96)], [cyl('hci', 0.06, ZR, ZR + 0.2, 'paint_grey', 32)], 'paint_grey')
    gb = cyl('gbg', 0.12, ZR + 0.25, ZR + 0.4, 'cast_iron', 48, r_in=0.052)
    P(m, 'head_cover', 'Head Cover, Gate Operating Ring & Turbine Guide Bearing', 'stator', [hc, gb], explode=(0, 0, 0.7), ref='ht_head_cover')
    gs = csg('gs', [cyl('gso', 0.6, 1.55, 2.05, 'paint_blue_dark', 96)], [cyl('gsi', 0.47, 1.5, 2.1, 'paint_blue_dark', 96)], 'paint_blue_dark')
    gtop = [cyl('gt', 0.62, 2.05, 2.1, 'paint_blue_dark', 96, r_in=0.06), box('br', (1.3, 0.1, 0.06), (0, 0, 1.52), 'paint_blue_dark')]
    P(m, 'generator_stator', 'Generator Stator, Brackets & Thrust Bearing', 'generator', [gs] + gtop, explode=(0, 0, 0.8), ref='ht_generator')
    for j, a in enumerate((math.pi / 2, -math.pi / 6, -5 * math.pi / 6)):
        pts = [(-1.0, Rst + 0.17, ZR)]
        n2 = 12
        span = (a - (math.pi / 2)) if j else 0.0
        for k in range(n2 + 1):
            aa = math.pi / 2 + span * k / n2
            rr = Rst + 0.17 - 0.12 * k / n2 * (abs(span) / TAU)
            pts.append((rr * math.cos(aa), rr * math.sin(aa), ZR))
        aa = a
        pts += [(0.3 * math.cos(aa - 0.6), 0.3 * math.sin(aa - 0.6), ZR), (0.2 * math.cos(aa - 1.1), 0.2 * math.sin(aa - 1.1), ZR - 0.1),
                (0.1 * math.cos(aa - 1.5), 0.1 * math.sin(aa - 1.5), ZR - 0.3), (0.0, 0.05, ZR - 0.55), (0.0, 0.05, 0.25), (0.35, 0.05, 0.02), (1.25, 0.05, 0.0)]
        m.flow(f'water_{j}', pts, 'water', 0.012, 0.25)
    return m.export(out)


# =============================================================== EQ-154 Expander turbine (turboexpander-compressor)
def _radial_wheel(name, x_tip, x_eye, r_tip, r_eye_hub, r_eye_tip, nb, mat, cz, sign):
    """Radial-flow wheel: hub + meridional blades; sign=+1 eye toward +x."""
    s = sign
    hub = lathe(name + 'h', [(0.0, x_tip - s * 0.012), (r_tip, x_tip - s * 0.012), (r_tip, x_tip), (r_eye_hub * 1.6, x_tip + s * 0.03),
                             (r_eye_hub, x_eye), (0.0, x_eye)], mat, 64, axis='X', center=(0, 0, cz))
    pts = [(x_tip, r_tip), (x_tip + s * 0.004, r_tip), (x_tip + s * 0.03, r_eye_tip * 1.05), (x_eye, r_eye_tip), (x_eye, r_eye_hub), (x_tip + s * 0.02, r_eye_hub * 1.5), (x_tip, r_tip * 0.8)]
    bl = []
    for i in range(nb):
        b = extrude_poly(f'{name}b{i}', [(x, cz + r) for x, r in pts], -0.0018, 0.0018, mat, plane='XZ')
        bl.append(rotate(b, TAU * i / nb, 'X', (0, 0, cz)))
    return join(name, [hub] + bl)


def expander_turbine(out):
    m = _model('expander_turbine', 'Turboexpander–Compressor (Radial-Inflow Expander, Variable Nozzles)')
    CZ = 0.6
    xe, xc = -0.25, 0.25
    exw = _radial_wheel('exw', xe, xe - 0.1, 0.13, 0.04, 0.09, 14, 'aluminium', CZ, -1)
    cw = _radial_wheel('cw', xc, xc + 0.09, 0.12, 0.035, 0.085, 16, 'aluminium', CZ, 1)
    sh = cyl('sh', 0.03, xe - 0.02, xc + 0.02, 'steel', 32, axis='X', center=(0, 0, CZ), ch=0.002)
    pr = P(m, 'rotor', 'Rotor: Expander Wheel, Shaft & Compressor Wheel', 'rotating_element', [exw, cw, sh], explode=(0, 0, 0.5), ref='ex_rotor', section='keep', pivot=(0, 0, CZ))
    pr.spin('X', 4)
    bh = csg('bh', [cyl('bho', 0.12, xe + 0.03, xc - 0.03, 'paint_grey', 64, axis='X', center=(0, 0, CZ)), box('bhf', (0.3, 0.28, CZ - 0.12), (0, 0, (CZ - 0.12) / 2), 'paint_grey')],
             [cyl('bhi', 0.031, xe, xc, 'paint_grey', 32, axis='X', center=(0, 0, CZ)), box('oc', (0.3, 0.12, 0.12), (0, 0, CZ - 0.07), 'paint_grey')], 'paint_grey')
    brg = [cyl(f'jb{i}', 0.05, x - 0.025, x + 0.025, 'bronze', 32, axis='X', center=(0, 0, CZ), r_in=0.0305) for i, x in enumerate((-0.12, 0.12))]
    P(m, 'bearing_housing', 'Centre Bearing Housing (oil-lubricated tilting-pad bearings, seals)', 'bearings', [bh] + brg, explode=(0, 0, -0.3), ref='ex_bearings')
    es = csg('es', [lathe('eso', [(0.16, xe + 0.03), (0.3, xe + 0.03), (0.3, xe - 0.06), (0.12, xe - 0.08), (0.11, xe - 0.4), (0.13, xe - 0.4), (0.13, xe - 0.42), (0.0, xe - 0.42), (0.0, xe + 0.03)],
                          'stainless', 96, axis='X', center=(0, 0, CZ)), cyl('ein', 0.07, CZ + 0.2, CZ + 0.45, 'stainless', 48, center=(xe - 0.02, 0, 0))],
             [lathe('esi', [(0.135, xe + 0.0), (0.27, xe + 0.0), (0.27, xe - 0.045), (0.1, xe - 0.1), (0.09, xe - 0.43), (0.0, xe - 0.43), (0.0, xe + 0.0)], 'stainless', 96, axis='X', center=(0, 0, CZ)),
              cyl('einn', 0.055, CZ + 0.15, CZ + 0.46, 'stainless', 48, center=(xe - 0.02, 0, 0))], 'stainless')
    P(m, 'expander_casing', 'Expander Inlet Scroll & Axial Exhaust (cold gas out)', 'casing', es, explode=(-0.4, 0, 0), ref='ex_expander_casing')
    ng = m.part('nozzles', 'Variable Inlet Guide Vanes (Nozzles) — adjust gas flow', 'stator', explode=(-0.25, 0, 0.35), info={'ref': 'ex_nozzles'})
    for i in range(13):
        a = TAU * i / 13
        r = 0.175
        gx, gz = r * math.cos(a), CZ + r * math.sin(a)
        v = box(f'nv{i}', (0.035, 0.05, 0.006), (xe - 0.02, gx, gz), 'chrome')
        v = rotate(v, a + 0.9, 'X', (xe - 0.02, gx, gz))
        ms = ng.add(v, smooth_angle=30)
        local_pivot(ms, (xe - 0.02, gx, gz))
        axis_rot_keys(m, ms, (1, 0, 0), lambda tt: 0.25 * math.sin(TAU * tt))
    cs = csg('cs', [lathe('cso', [(0.16, xc - 0.03), (0.3, xc - 0.03), (0.3, xc + 0.06), (0.1, xc + 0.09), (0.1, xc + 0.38), (0.12, xc + 0.38), (0.12, xc + 0.4), (0.0, xc + 0.4), (0.0, xc - 0.03)],
                          'paint_blue', 96, axis='X', center=(0, 0, CZ)), cyl('cout', 0.065, CZ + 0.2, CZ + 0.45, 'paint_blue', 48, center=(xc + 0.02, 0, 0))],
             [lathe('csi', [(0.13, xc - 0.0), (0.27, xc - 0.0), (0.27, xc + 0.045), (0.088, xc + 0.09), (0.085, xc + 0.41), (0.0, xc + 0.41), (0.0, xc + 0.0)], 'paint_blue', 96, axis='X', center=(0, 0, CZ)),
              cyl('couti', 0.05, CZ + 0.15, CZ + 0.46, 'paint_blue', 48, center=(xc + 0.02, 0, 0))], 'paint_blue')
    P(m, 'compressor_casing', 'Compressor (Brake) Casing: Axial Inlet, Diffuser & Volute', 'casing', cs, explode=(0.4, 0, 0), ref='ex_compressor_casing')
    fnd = box('fnd', (1.6, 0.7, 0.08), (0, 0, -0.04), 'cast_iron')
    P(m, 'skid', 'Skid / Baseplate', 'baseplate', fnd, explode=(0, 0, -0.3), ref='ex_skid', section='keep')
    m.flow('expander_gas', [(xe - 0.02, 0, CZ + 0.45), (xe - 0.02, 0, CZ + 0.24)] + [(xe - 0.03, 0.2 * math.sin(a), CZ + 0.2 * math.cos(a)) for a in (0.0, -0.6, -1.2)] +
           [(xe - 0.03, 0.13 * math.sin(-1.6), CZ + 0.13 * math.cos(-1.6)), (xe - 0.12, 0.06, CZ), (xe - 0.45, 0.0, CZ)], 'air', 0.008, 0.12, speed=[1, 1.3, 1.8, 2, 2, 1.6, 1.2, 1])
    m.flow('compressor_gas', [(xc + 0.42, 0, CZ + 0.02), (xc + 0.1, 0, CZ + 0.05), (xc + 0.02, 0, CZ + 0.14), (xc + 0.02, 0.2 * math.sin(0.8), CZ + 0.2 * math.cos(0.8)),
                              (xc + 0.02, 0.0, CZ + 0.22), (xc + 0.02, 0, CZ + 0.45)], 'flow_discharge', 0.008, 0.12)
    _bands_x(m, [(xe - 0.42, xe - 0.1, 1), (xe - 0.1, xe + 0.03, 6)], CZ, 0.31, 0.33, 'Expander: pressure and temperature drop',
             'High-pressure gas enters the scroll, accelerates through the nozzles and expands through the wheel, doing work on it. Pressure and temperature fall '
             'sharply (refrigeration effect); the power drives the compressor (or a generator) on the same shaft.')
    m.annotate('pressure', 'Expander inlet: high P, ambient T', (xe - 0.02, 0, CZ + 0.5))
    m.annotate('pressure', 'Exhaust: low P, very cold', (xe - 0.4, 0, CZ - 0.18))
    return m.export(out)


# ===================================================================== metadata
def _std(*items):
    return [{'id': i, 'title': t, 'relevance': r, 'edition': 'to be verified'} for i, t, r in items]


_FAN_STD = _std(('ISO 5801', 'Fans — Performance testing using standardized airways', 'Performance tests.'), ('AMCA 210 / ASHRAE 51', 'Laboratory methods of testing fans', 'Rating tests.'),
                ('ISO 14694', 'Industrial fans — Specifications for balance quality and vibration levels', 'Balance and vibration.'), ('ISO 12759', 'Fans — Efficiency classification (FMEG)', 'Efficiency grades.'))
_CF_COMMON = {
    'cf_housing': C('Collects air from the impeller, slows it down and converts velocity into pressure; guides it to the outlet.', 'Welded steel scroll (volute) with side plates and outlet flange.',
                    'Carbon steel; stainless or lined for corrosive gas.', 'Cut-off (tongue) clearance affects noise and efficiency.', ['Erosion, corrosion, leaks'], ['Thickness survey, inspect cut-off']),
    'cf_impeller': C('Adds energy to the air by spinning it outward.', 'Back plate, shroud and curved blades welded or riveted; keyed to the shaft.', 'Steel; wear-resistant liners for dusty gas.',
                     'Tip speed limits pressure; balanced to ISO 14694 grade.', ['Imbalance from build-up or erosion', 'Fatigue cracking'], ['Vibration trending, blade inspection']),
    'cf_inlet_cone': C('Guides air smoothly into the impeller eye.', 'Spun or pressed cone overlapping the impeller shroud.', 'Steel.', 'Overlap/gap to impeller is set at installation.', ['Wrong gap → lost efficiency'], ['Check gap']),
    'cf_bearings': C('Support the shaft and impeller.', 'Plummer-block (pedestal) bearings, one fixed and one free.', 'Cast iron housing; rolling or sleeve bearings.', 'Free bearing allows thermal growth.',
                     ['Overheating, wear'], ['Temperature and vibration']),
    'cf_stand': C('Supports the housing and bearings.', 'Fabricated pedestal and sole plates.', 'Steel.', 'Rigid foundation avoids resonance.', ['Soft foot'], ['Check bolts']),
    'cf_inlet_box': C('Turns the gas from the duct into the fan inlet.', 'Rectangular box with turning section.', 'Steel.', '—', ['Erosion'], ['Inspect']),
    'cf_damper': C('Controls (or isolates) the flow by changing the blade angle.', 'Louvre blades on shafts linked to an actuator.', 'Steel.', 'Damper control wastes energy versus VFD.', ['Sticking', 'Linkage wear'], ['Stroke test']),
    'cf_igv': C('Pre-swirl the air in the direction of rotation to reduce flow and power efficiently.', 'Radial vanes in the inlet, turned together by a ring and actuator.', 'Steel.',
                'More efficient than outlet dampers at part load.', ['Linkage seizure'], ['Stroke test, lubricate']),
    'cf_silencer': C('Absorbs fan noise radiated from the inlet.', 'Cylindrical absorptive silencer with central pod.', 'Steel, mineral wool, perforated sheet.', '—', ['Clogging'], ['Inspect']),
}

META = {
    'axial_flow_fan': {
        'summary': ('An axial flow fan moves air parallel to its shaft. Aerofoil blades on a hub act like small wings: as they turn they push air along the casing. '
                    'Outlet guide vanes remove the swirl the blades add, turning it into pressure. Axial fans give large flow at low-to-medium pressure and are '
                    'used for ventilation, cooling towers, tunnels and (with variable-pitch blades) large boiler draft fans.'),
        'classification': {'family': 'Fan (dynamic)', 'type': 'Vane-axial fan, direct drive, in-line motor'},
        'model_configuration': {'blades': 8, 'guide_vanes': 11, 'pitch': 'Adjustable at standstill (variable-pitch in operation on large fans)'},
        'standards': _FAN_STD, 'references': ['Bleier, Fan Handbook', 'Eck, Fans'],
        'components': {
            'af_casing': C('Forms the air passage around the blades with a small tip clearance.', 'Rolled cylindrical casing with flanges.', 'Steel.', 'Tip clearance ~0.2–0.5 % of diameter.', ['Rub'], ['Check clearance']),
            'af_bell': C('Smooth inlet for low losses.', 'Bellmouth.', 'Steel/aluminium.', '—', ['—'], ['—']),
            'af_impeller': C('Pushes the air axially.', 'Hub with aerofoil blades clamped at a set pitch angle.', 'Cast aluminium, GRP, steel.', 'Pitch angle sets the duty.',
                             ['Imbalance', 'Blade fatigue', 'Stall in parallel operation'], ['Vibration, blade root checks']),
            'af_guide_vanes': C('Straighten the swirling air and recover pressure.', 'Fixed vanes welded in the casing.', 'Steel.', '—', ['Cracking'], ['Inspect welds']),
            'af_motor': C('Drives the impeller directly.', 'Motor in the air stream supported on vanes/struts.', 'TEAO motor.', 'Cooled by the air stream.', ['Overheating if airflow is blocked'], ['Winding temperature']),
        },
    },
    'centrifugal_fan': {
        'summary': ('A centrifugal fan draws air into the centre (eye) of a spinning impeller and throws it outward. The scroll-shaped housing collects the air, slows '
                    'it down and turns the velocity into pressure. Backward-curved blades give high efficiency and a non-overloading power curve.'),
        'classification': {'family': 'Fan (dynamic)', 'type': 'Centrifugal, single width single inlet (SWSI), backward-curved, direct drive'},
        'model_configuration': {'blades': 12, 'rotation': 'Clockwise viewed from drive side (by convention in this model)', 'discharge': 'Top horizontal'},
        'standards': _FAN_STD, 'references': ['Bleier, Fan Handbook', 'AMCA 99 — Standards Handbook (arrangements, rotation, discharge)'],
        'components': {k: _CF_COMMON[k] for k in ('cf_housing', 'cf_impeller', 'cf_inlet_cone', 'cf_bearings', 'cf_stand')},
    },
    'induced_draft_fan': {
        'summary': ('An induced draft (ID) fan sits after the boiler, dust collector or scrubber and sucks the hot flue gas out of the furnace, keeping it slightly below '
                    'atmospheric pressure (balanced draft). It handles hot, dusty and sometimes corrosive gas, so it is robust, heavily built and often controlled '
                    'by inlet dampers, inlet vanes or a variable-speed drive.'),
        'classification': {'family': 'Fan (dynamic) — boiler draft fan', 'type': 'Centrifugal, inlet box, louvre damper control, coupled motor'},
        'model_configuration': {'gas': 'Flue gas ~120–200 °C after air heater (plant specific)', 'control': 'Inlet louvre damper (VFD common on new plants)'},
        'standards': _FAN_STD, 'references': ['Steam: Its Generation and Use (B&W) — draft systems', 'Bleier, Fan Handbook'],
        'components': {k: _CF_COMMON[k] for k in ('cf_housing', 'cf_impeller', 'cf_inlet_cone', 'cf_bearings', 'cf_stand', 'cf_inlet_box', 'cf_damper')},
    },
    'forced_draft_fan': {
        'summary': ('A forced draft (FD) fan pushes ambient combustion air into a boiler through the air heater and windbox to the burners. It handles clean, cold air, '
                    'so it can run at high efficiency; inlet guide vanes or blade pitch/speed control set the airflow to match the fuel.'),
        'classification': {'family': 'Fan (dynamic) — boiler draft fan', 'type': 'Centrifugal, inlet silencer, inlet guide vanes, coupled motor'},
        'model_configuration': {'control': 'Inlet guide vanes (IGV)', 'air': 'Ambient, clean'},
        'standards': _FAN_STD, 'references': ['Steam: Its Generation and Use (B&W) — draft systems'],
        'components': {k: _CF_COMMON[k] for k in ('cf_housing', 'cf_impeller', 'cf_inlet_cone', 'cf_bearings', 'cf_stand', 'cf_igv', 'cf_silencer')},
    },
    'primary_air_fan': {
        'summary': ('A primary air (PA) fan supplies high-pressure air to the coal pulverisers (mills): it dries the coal and carries the fine powder to the burners. '
                    'It needs much higher pressure than an FD fan at lower flow, so it has a narrow, high-speed impeller; inlet vanes and an outlet damper control '
                    'and isolate it.'),
        'classification': {'family': 'Fan (dynamic) — boiler mill air fan', 'type': 'Centrifugal, narrow high-pressure impeller, IGV + outlet damper'},
        'model_configuration': {'blades': 16, 'pressure': 'Typically several times FD fan pressure (plant specific)'},
        'standards': _FAN_STD, 'references': ['Pulverised-coal firing system design notes (generic)'],
        'components': {k: _CF_COMMON[k] for k in ('cf_housing', 'cf_impeller', 'cf_inlet_cone', 'cf_bearings', 'cf_stand', 'cf_igv', 'cf_damper')},
    },
    'steam_turbine': {
        'summary': ('A steam turbine converts the energy of high-pressure steam into shaft power. In each stage, stationary nozzles accelerate the steam and the moving '
                    'blades on the rotor turn that velocity into torque. The steam expands through many stages to the condenser vacuum, so the blades get longer '
                    'toward the exhaust. A governor valve controls the steam flow to hold speed or load.'),
        'classification': {'family': 'Turbine (steam)', 'type': 'Multistage, condensing, single casing, impulse/reaction stages'},
        'model_configuration': {'stages': 6, 'exhaust': 'Downward to condenser', 'driven': 'Generator via coupling'},
        'standards': _std(('API 612', 'Special-Purpose Steam Turbines', 'Process drives.'), ('API 611', 'General-Purpose Steam Turbines', 'Smaller drives.'),
                          ('IEC 60045-1', 'Steam turbines — Specifications', 'Power-generation turbines.'), ('ASME PTC 6', 'Steam Turbines performance test code', 'Acceptance tests.')),
        'references': ['Bloch & Singh, Steam Turbines — Design, Applications and Rerating', 'Cotton, Evaluating and Improving Steam Turbine Performance'],
        'components': {
            'st_casing': C('Contains the steam, holds the diaphragms and forms the inlet and exhaust.', 'Horizontally split cast/fabricated casing with steam chest and exhaust hood.', 'Cr-Mo cast steel (HP); fabricated steel (LP).',
                           'Thermal stresses on start-up limit loading rate.', ['Distortion, cracking', 'Joint leaks'], ['Clearance checks at overhaul']),
            'st_rotor': C('Converts steam velocity into torque.', 'Forged shaft with wheels (discs) carrying moving blades; balance and thrust collar.', 'Cr-Mo-V forged steel; 12 % Cr blades.',
                          'Critical speeds must be away from running speed.', ['Blade erosion (wet LP steam)', 'Fouling', 'Imbalance'], ['Vibration, borescope']),
            'st_diaphragms': C('Hold the stationary nozzles that accelerate the steam into each stage.', 'Split diaphragms with nozzle partitions and shaft labyrinths.', 'Stainless/Cr steel.', '—', ['Erosion', 'Deposits'], ['Inspect at overhaul']),
            'st_governor': C('Controls speed/load by positioning the control valve.', 'Electro-hydraulic actuator.', 'Steel/hydraulic.', 'Overspeed trip is separate and independent.', ['Hunting', 'Sticking'], ['Overspeed trip test']),
            'st_control_valve': C('Throttles steam admission.', 'Plug valve(s) in steam chest.', 'Alloy steel.', '—', ['Stem sticking from deposits'], ['Valve exercise']),
            'st_bearings': C('Support the rotor and carry axial thrust.', 'Tilting-pad journal bearings and a thrust bearing.', 'Babbitt-lined steel.', 'Forced oil lubrication.', ['Wiped babbitt'], ['Bearing temperature, vibration']),
            'st_glands': C('Limit steam leakage (and air in-leakage) where the shaft leaves the casing.', 'Labyrinth seals with gland steam system.', 'Bronze/steel.', '—', ['Rub, wear'], ['Gland steam pressure']),
            'st_generator': C('Driven machine (load).', 'Generator or compressor.', '—', '—', ['—'], ['—']),
            'st_foundation': C('Supports the turbine-generator train.', 'Concrete table-top or steel base.', 'Concrete/steel.', '—', ['Settlement'], ['Alignment checks']),
        },
    },
    'gas_turbine': {
        'summary': ('A gas turbine works on the Brayton cycle: an axial compressor squeezes air, fuel is burned in the combustors at nearly constant pressure, and the hot '
                    'gas expands through the turbine. The turbine drives the compressor and has power left over for a generator or compressor. The hot exhaust is often '
                    'used in a heat-recovery boiler (combined cycle).'),
        'classification': {'family': 'Turbine (gas)', 'type': 'Industrial heavy-duty, single shaft, can-annular combustion'},
        'model_configuration': {'compressor_stages': 8, 'turbine_stages': 3, 'combustors': 6},
        'standards': _std(('API 616', 'Gas Turbines for the Petroleum, Chemical, and Gas Industry Services', 'Process service.'), ('ISO 3977', 'Gas turbines — Procurement', 'General.'),
                          ('ISO 2314 / ASME PTC 22', 'Gas turbines — Acceptance tests', 'Performance tests.')),
        'references': ['Saravanamuttoo et al., Gas Turbine Theory', 'Boyce, Gas Turbine Engineering Handbook'],
        'components': {
            'gt_casing': C('Encloses the compressor, combustion section and turbine.', 'Horizontally split casings.', 'Cast/fabricated steel; nickel alloys in hot section.', '—', ['Distortion', 'Cracks'], ['Borescope']),
            'gt_inlet': C('Brings filtered air smoothly into the compressor.', 'Bellmouth and plenum (after inlet filters).', 'Steel.', 'Inlet filtration protects the compressor.', ['Fouling'], ['ΔP, offline/online wash']),
            'gt_rotor': C('Compresses air and extracts power from the hot gas.', 'Bolted disc rotor with compressor and turbine blades.', 'Steel; nickel superalloy turbine blades (coated, cooled).',
                          'Firing temperature limits blade life.', ['Compressor fouling', 'Hot-gas-path damage', 'Creep'], ['Borescope, hot-gas-path inspection']),
            'gt_stators': C('Turn the flow between rotor stages; first-stage nozzles accelerate the hot gas.', 'Stator vanes / nozzle guide vanes.', 'Steel; nickel/cobalt alloys.', '—', ['Erosion, burn-through'], ['Borescope']),
            'gt_combustors': C('Mix fuel and air and burn it.', 'Combustion liners with fuel nozzles, transition pieces.', 'Nickel alloys with thermal barrier coatings.', 'Low-NOx (DLN) designs common.',
                               ['Liner cracking', 'Flashback'], ['Combustion inspection']),
            'gt_flame': C('Flame region (visual).', '—', '—', '—', ['—'], ['—']),
            'gt_exhaust': C('Slows the exhaust to recover pressure and leads it to the stack or HRSG.', 'Diffuser and collector.', 'Steel, insulated.', '—', ['Cracking'], ['Inspect']),
            'gt_bearings': C('Support and locate the rotor.', 'Tilting-pad journal and thrust bearings.', 'Babbitt/steel.', '—', ['Wear'], ['Temperature, vibration']),
            'gt_accessories': C('Drives lube oil and fuel pumps and starts the turbine.', 'Accessory gearbox and starter.', 'Steel.', '—', ['—'], ['—']),
            'gt_skid': C('Supports the turbine.', 'Steel base.', 'Steel.', '—', ['—'], ['—']),
        },
    },
    'hydraulic_turbine': {
        'summary': ('A Francis hydraulic turbine converts the pressure and velocity of water into shaft power. Water from the penstock fills the spiral casing, passes the '
                    'stay vanes and the adjustable wicket gates — which set the flow and give it swirl — and flows inward through the runner, turning it. The water '
                    'leaves downward through the draft tube, which recovers energy. The vertical shaft drives a generator above.'),
        'classification': {'family': 'Hydraulic turbine (reaction)', 'type': 'Francis, vertical shaft, spiral casing'},
        'model_configuration': {'runner_blades': 13, 'wicket_gates': 16, 'stay_vanes': 12, 'animation': 'Gates open/close while the runner turns'},
        'standards': _std(('IEC 60041', 'Field acceptance tests to determine the hydraulic performance of hydraulic turbines', 'Performance tests.'),
                          ('IEC 60193', 'Hydraulic turbines — Model acceptance tests', 'Model tests.'), ('IEC 60609', 'Cavitation pitting evaluation', 'Cavitation.')),
        'references': ['Krivchenko, Hydraulic Machines', 'US Bureau of Reclamation — Selecting Hydraulic Reaction Turbines'],
        'components': {
            'ht_spiral': C('Distributes water evenly around the runner.', 'Spiral (scroll) casing of decreasing cross-section.', 'Welded steel plate, embedded in concrete.', '—', ['Corrosion'], ['Inspect during outages']),
            'ht_stay_vanes': C('Fixed vanes that carry structural loads and guide the water.', 'Stay ring with welded vanes.', 'Steel.', '—', ['Cracking (vortex shedding)'], ['NDT']),
            'ht_wicket_gates': C('Control the flow and set the inflow angle.', 'Pivoted guide vanes moved together by the operating ring and servomotors.', 'Stainless/bronze.',
                                 'Gate opening follows the governor.', ['Leakage when closed', 'Bush wear'], ['Gate clearance, shear-pin check']),
            'ht_runner': C('Turns the water energy into torque.', 'Crown, band and curved blades; vertical shaft and generator rotor.', 'Cast/fabricated 13Cr-4Ni stainless.',
                           'Cavitation if submergence is too low.', ['Cavitation pitting', 'Cracking'], ['Cavitation repair, NDT']),
            'ht_draft_tube': C('Slows the outflow and recovers kinetic energy (suction head).', 'Cone, elbow and diffuser.', 'Steel liner / concrete.', 'Draft-tube vortex at part load.', ['Rope vortex vibration'], ['Pressure pulsation monitoring']),
            'ht_head_cover': C('Closes the top of the runner chamber and holds the guide bearing and gate mechanism.', 'Fabricated cover with guide bearing.', 'Steel.', '—', ['Leaks'], ['Inspect']),
            'ht_generator': C('Converts shaft power into electricity.', 'Synchronous generator stator, brackets and thrust bearing.', 'Steel, copper.', 'Thrust bearing carries rotor weight + hydraulic thrust.', ['Insulation ageing'], ['Electrical tests']),
        },
    },
    'expander_turbine': {
        'summary': ('A turboexpander lets high-pressure gas expand through a radial-inflow turbine wheel. Because the gas does work on the wheel, its temperature drops far '
                    'more than in a valve — the basis of gas processing, air separation and LNG refrigeration. The recovered power drives a compressor wheel on the '
                    'same shaft (or a generator). Variable inlet guide vanes control the flow.'),
        'classification': {'family': 'Turbine (expander)', 'type': 'Radial-inflow turboexpander–compressor, overhung wheels'},
        'model_configuration': {'expander_blades': 14, 'compressor_blades': 16, 'nozzles': 13, 'bearings': 'Oil-lubricated (active magnetic bearings also common)'},
        'standards': _std(('API 617 (Ch. 4)', 'Axial and Centrifugal Compressors and Expander-compressors', 'Expander-compressors.'),),
        'references': ['Bloch & Soares, Turboexpanders and Process Applications'],
        'components': {
            'ex_rotor': C('Extracts energy from the expanding gas and drives the compressor.', 'Two overhung wheels on a short shaft.', 'Aluminium alloy or titanium wheels; steel shaft.',
                          'Very high speed (tens of thousands rpm on small units).', ['Erosion by liquids/solids', 'Imbalance'], ['Vibration, speed']),
            'ex_bearings': C('Support the high-speed shaft and carry thrust.', 'Tilting-pad bearings in a centre housing with seals.', 'Steel/babbitt.', 'Seal gas keeps oil out of the process.', ['Oil contamination'], ['Temperature, vibration']),
            'ex_expander_casing': C('Leads gas through the inlet scroll to the nozzles and out the axial exhaust.', 'Scroll casing.', 'Stainless (cryogenic).', '—', ['—'], ['—']),
            'ex_nozzles': C('Accelerate the gas onto the wheel and control flow.', 'Adjustable nozzle vanes moved by an actuator ring.', 'Stainless.', '—', ['Sticking'], ['Stroke test']),
            'ex_compressor_casing': C('Collects compressed gas from the compressor wheel.', 'Axial inlet, diffuser and volute.', 'Steel.', '—', ['—'], ['—']),
            'ex_skid': C('Supports the machine.', 'Steel skid.', 'Steel.', '—', ['—'], ['—']),
        },
    },
}

BUILDERS = {'axial_flow_fan': axial_flow_fan, 'centrifugal_fan': centrifugal_fan, 'induced_draft_fan': induced_draft_fan, 'forced_draft_fan': forced_draft_fan,
            'primary_air_fan': primary_air_fan, 'steam_turbine': steam_turbine, 'gas_turbine': gas_turbine, 'hydraulic_turbine': hydraulic_turbine,
            'expander_turbine': expander_turbine}
