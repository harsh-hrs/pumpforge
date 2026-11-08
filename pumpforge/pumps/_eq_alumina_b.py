"""Alumina Refinery (Bayer process) — EQ-284 … EQ-295: sand separation, hydrate filtration & washing, product cooling,
storage & conveying, causticization, oxalate removal, liquor clarification and dust collection."""
import math
from mathutils import Matrix, Vector
from pumpforge.core import Model, lathe, cyl, box, csg, join, rotate, extrude_poly, TAU, OPERATE_FRAMES
from pumpforge.valvekit import P, keys_loop, smooth_pulse
from pumpforge.parts import hollow_pipe, pressure_gauge, add_tracers
from pumpforge.vesselkit import vessel, nozzle, legs, droplets, liquid_v, half, animate_level
from pumpforge.handlingkit import rocks_along, belt_loop
from pumpforge.rotkit import axis_rot_keys
from pumpforge.plantkit import agitated_tank, hydrocyclone, particles_path, ball, silo
from pumpforge.shapes import sweep_tube
from pumpforge.common_meta import C
from pumps._eq_thermal_a import _bands_z, _bands_x, _pump, _fan_rotor
from pumps._eq_thermal_b import _bed_particles
from pumps._eq_alumina_a import _drum_machine, _thk_comp, _agt_comp

CAT = '12 · Alumina Refinery (Bayer Process)'


def _model(pid, title):
    return Model(pid, title, CAT, META[pid])


def _press(m, objs, title, desc, kind='pressure'):
    m.overlay(kind, join(kind, objs), title, desc, split=True)


# =============================================================== EQ-284 Sand separator (screw classifier)
def sand_separator(out):
    m = _model('sand_separator', 'Sand Separator — Inclined Screw Classifier (Coarse Sand from Red Mud Slurry)')
    ang = math.radians(18)
    L, W = 3.0, 0.5
    x0, z0 = -1.4, 0.35
    ax = Vector((math.cos(ang), 0, math.sin(ang)))
    c0 = Vector((x0, 0, z0 + 0.25))
    Mx = Matrix.Translation(c0) @ Matrix.Rotation(-ang, 4, 'Y')
    tr = csg('tr', [box('tro', (L, W + 0.06, 0.55), (L / 2, 0, 0.05), 'paint_grey')], [cyl('trc', W / 2, -0.1, L + 0.1, 'paint_grey', 48, axis='X', center=(0, 0, 0)), box('trt', (L + 0.2, W, 0.5), (L / 2, 0, 0.3), 'paint_grey')], 'paint_grey')
    tr.data.transform(Mx)
    pool = csg('pl', [box('plo', (1.1, W + 0.3, 0.9), (x0 + 0.3, 0, z0 + 0.35), 'paint_grey')], [box('pli', (1.04, W + 0.24, 0.9), (x0 + 0.3, 0, z0 + 0.4), 'paint_grey')], 'paint_grey')
    P(m, 'trough_tank', 'Inclined Trough & Settling Pool (with overflow weir)', 'casing', [tr, pool, box('wr', (0.04, W + 0.3, 0.12), (x0 - 0.22, 0, z0 + 0.72), 'steel')], explode=(0, 0.7, 0), ref='ss_trough')
    P(m, 'pool_slurry', 'Pool of Mud Slurry (fines overflow, sand settles)', 'fluid', box('ps', (1.0, (W + 0.22) / 2, 0.55), (x0 + 0.3, (W + 0.22) / 4, z0 + 0.42), 'red_mud'), explode=(0, -0.4, 0), ref='ss_trough', section='keep')
    pts = []
    for k in range(121):
        u = k / 120
        a = TAU * 7 * u
        pts.append(((L - 0.2) * u + 0.1, (W / 2 - 0.04) * math.cos(a), (W / 2 - 0.04) * math.sin(a)))
    fl = sweep_tube('fl', pts, 0.025, 'steel_dark', 6)
    sh = cyl('sh', 0.06, -0.15, L + 0.25, 'steel', 24, axis='X', center=(0, 0, 0))
    for o in (fl, sh):
        o.data.transform(Mx)
    mid = c0 + ax * (L / 2)
    for o in (fl, sh):
        o.data.transform(Matrix.Translation(Vector((0, 0, 0))))
    ps = P(m, 'screw', 'Spiral Screw (rakes settled sand up the incline)', 'rotating_element', [fl, sh], explode=(0, -0.8, 0.3), ref='ss_screw', section='keep', pivot=tuple(mid))
    for mesh in ps.meshes:
        axis_rot_keys(m, mesh, tuple(ax), lambda t: -TAU * 1.0 * t)
    top = c0 + ax * (L + 0.2)
    dr = join('dr', [box('gb', (0.35, 0.35, 0.35), (top.x + 0.1, 0, top.z + 0.1), 'paint_blue'), cyl('mt', 0.12, top.z + 0.28, top.z + 0.65, 'paint_motor', 24, center=(top.x + 0.1, 0, 0)),
                     box('ch', (0.35, 0.45, 0.5), (top.x - 0.1, 0, top.z - 0.4), 'paint_grey')])
    P(m, 'drive_discharge', 'Head Drive (gearmotor) & Sand Discharge Chute', 'drive', dr, explode=(0.4, 0, 0.3), ref='ss_drive', section='keep')
    P(m, 'supports', 'Supports', 'structure', [box(f'sp{k}', (0.12, W + 0.2, (c0 + ax * s).z - 0.1), ((c0 + ax * s).x, 0, ((c0 + ax * s).z - 0.1) / 2), 'paint_grey') for k, s in enumerate((1.2, 2.6))],
      explode=(0, 0, -0.3), ref='ss_trough', section='keep')
    particles_path(m, 'sand', 'Sand Grains raked up the Incline (drained of liquor)', lambda i, s: tuple(c0 + ax * (0.3 + (L - 0.2) * s) + Vector((0, 0.05 + 0.05 * (i % 3), -0.12))), 12, mat='sand', r=0.025)
    m.flow('feed', [(x0 + 0.3, 0, z0 + 1.2), (x0 + 0.3, 0, z0 + 0.6)], 'flow_discharge', 0.02, 0.2)
    m.flow('overflow', [(x0 + 0.1, 0.05, z0 + 0.7), (x0 - 0.22, 0, z0 + 0.8), (x0 - 0.5, 0, z0 + 0.4)], 'water', 0.02, 0.2)
    m.flow('sand', [tuple(c0 + ax * 0.5 + Vector((0, 0.05, -0.1))), tuple(c0 + ax * (L + 0.1) + Vector((0, 0.05, -0.1))), (top.x - 0.1, 0, top.z - 0.7)], 'sand', 0.02, 0.3)
    _press(m, [box('vz', (1.0, 0.02, 0.5), (x0 + 0.3, -(W + 0.3) / 2 - 0.03, z0 + 0.45), 'pressure_6')], 'Sand settles, mud overflows',
           'Coarse sand (typically > ~ 100 µm) settles quickly in the pool and is raked up the incline, draining and being washed on the way, while fine red mud stays in suspension and overflows the weir to the '
           'washers. Removing sand early reduces erosion in thickeners, pumps and pipelines; the washed sand is often used for residue-area construction.')
    return m.export(out)


# =============================================================== EQ-285 Alumina hydrate filter (rotary vacuum drum)
def alumina_hydrate_filter(out):
    m = _model('alumina_hydrate_filter', 'Rotary Vacuum Drum Filter for Alumina Hydrate')
    R, X0, X1, CZ = 0.6, -0.9, 0.9, 1.0
    tr = csg('tr', [cyl('tro', R + 0.2, X0 - 0.05, X1 + 0.05, 'paint_grey', 64, axis='X', center=(0, 0, CZ))], [cyl('tri', R + 0.17, X0, X1, 'paint_grey', 64, axis='X', center=(0, 0, CZ)), box('trt', (3, 3, 2), (0, 0, CZ + 0.85), 'paint_grey')], 'paint_grey')
    P(m, 'trough', 'Slurry Trough (drum submerged ~ 30–40 %)', 'casing', tr, explode=(0, 0.7, -0.2), ref='hf_trough')
    sl = csg('sl', [box('slb', (X1 - X0 - 0.02, R + 0.15, 0.5), (0, (R + 0.15) / 2, CZ - R + 0.05), 'liquor')], [cyl('sld', R + 0.01, X0 - 0.1, X1 + 0.1, 'liquor', 64, axis='X', center=(0, 0, CZ)),
                                                                                                                csg('slo', [box('slx', (3, 3, 3), (0, 0, CZ), 'liquor')], [cyl('slc', R + 0.165, X0 - 0.5, X1 + 0.5, 'liquor', 64, axis='X', center=(0, 0, CZ))], 'liquor')], 'liquor')
    P(m, 'slurry', 'Hydrate Slurry in the Trough', 'fluid', sl, explode=(0, -0.4, -0.2), ref='hf_trough', section='keep')
    dr = [cyl('dd', R, X0 + 0.02, X1 - 0.02, 'steel', 96, axis='X', center=(0, 0, CZ), r_in=R - 0.03)] + [cyl(f'de{k}', R, x, x + 0.03, 'steel', 96, axis='X', center=(0, 0, CZ), r_in=0.08) for k, x in enumerate((X0 + 0.02, X1 - 0.05))]
    dr += [cyl('ds', 0.07, X0 - 0.4, X1 + 0.3, 'steel', 24, axis='X', center=(0, 0, CZ))]
    P(m, 'drum', 'Drum with Internal Filtrate Pipes (rotates ~ 0.5–3 rpm)', 'rotating_element', dr, explode=(0, -0.8, 0.3), ref='hf_drum', section='split')
    sec = [rotate(box(f'sc{k}', (X1 - X0 - 0.06, 0.012, 0.025), (0, 0, CZ + R + 0.005), 'polypropylene'), TAU * k / 20, 'X', (0, 0, CZ)) for k in range(20)]
    psc = P(m, 'filter_sectors', 'Filter Cloth Sector Strips (show drum rotation)', 'rotating_element', sec, explode=(0, -1.0, 0.3), ref='hf_drum', section='keep', pivot=(0, 0, CZ))
    psc.spin('X', -0.5)
    ck = lathe('ck', [(R + 0.003, X0 + 0.04), (R + 0.03, X0 + 0.04), (R + 0.03, X1 - 0.04), (R + 0.003, X1 - 0.04)], 'powder', 64, a0=math.radians(-60), a1=math.radians(160), axis='X', center=(0, 0, CZ), cap_mat='powder')
    P(m, 'cake', 'Hydrate Cake: forms in the slurry, is dewatered/washed, then scraped off', 'fluid', half(ck, 'powder'), explode=(0, -0.5, 0.4), ref='hf_cake', section='keep')
    sc = [box('sb', (X1 - X0, 0.02, 0.2), (0, 0, CZ + 0.05), 'steel'), box('dc', (X1 - X0, 0.5, 0.4), (0, 0, 0.4), 'paint_grey')]
    sc = [rotate(sc[0], 0.3, 'X', (0, 0, CZ)), sc[1]]
    sc[0].data.transform(Matrix.Translation((0, R + 0.05, -0.05)))
    sc[1].data.transform(Matrix.Translation((0, R + 0.25, 0)))
    P(m, 'scraper_chute', 'Discharge Scraper (with air blow-back) & Cake Chute', 'discharge', sc, explode=(0, 0.5, 0), ref='hf_scraper', section='keep')
    sp = [cyl('wsh', 0.025, X0, X1, 'stainless', 12, axis='X', center=(0, -0.2, CZ + R + 0.2))] + [cyl(f'ws{k}', 0.01, CZ + R + 0.1, CZ + R + 0.2, 'brass', 8, center=(X0 + 0.15 + 0.25 * k, -0.2, 0)) for k in range(7)]
    P(m, 'wash_sprays', 'Cake Wash Sprays', 'water', sp, explode=(0, -0.3, 0.5), ref='hf_wash', section='keep')
    vv = join('vv', [cyl('vvb', 0.18, X1 + 0.05, X1 + 0.25, 'paint_blue', 32, axis='X', center=(0, 0, CZ)), hollow_pipe('vl', [(X1 + 0.25, 0, CZ), (X1 + 0.6, 0, CZ), (X1 + 0.6, 0, 0.3)], 0.05, 'paint_blue', 16, bend=0.08),
                     vessel('fr', 0.22, 0.5, 0.006, 'paint_blue', center=(X1 + 1.0, 0, 0), heads=('2:1', '2:1'), z0=0.3)])
    P(m, 'vacuum_system', 'Automatic Vacuum (control) Valve, Vacuum Line & Filtrate Receiver', 'vacuum', vv, explode=(0.5, 0, 0), ref='hf_valve', section='keep')
    dv = join('dv', [box('gb', (0.3, 0.3, 0.3), (X0 - 0.55, 0, CZ), 'paint_blue'), cyl('mt', 0.1, X0 - 1.0, X0 - 0.7, 'paint_motor', 24, axis='X', center=(0, 0, CZ)),
                     box('ag', (X1 - X0 - 0.1, 0.03, 0.15), (0, 0, CZ - R - 0.08), 'steel')])
    P(m, 'drive_agitator', 'Drum Drive & Trough Agitator (keeps solids suspended)', 'drive', dv, explode=(-0.4, 0, 0), ref='hf_drive', section='keep')
    P(m, 'supports', 'Supports', 'structure', [box(f'sp{k}', (0.2, 1.3, CZ - R - 0.2), (x, 0, (CZ - R - 0.2) / 2), 'paint_grey') for k, x in enumerate((X0 + 0.1, X1 - 0.1))], explode=(0, 0, -0.3), ref='hf_trough', section='keep')
    particles_path(m, 'filtrate', 'Liquor drawn through the Cloth into the Drum', lambda i, s: (-0.7 + 0.15 * (i % 10), (R + 0.12 - 0.25 * s) * math.cos(math.radians(-60 + 12 * (i % 6))) * 0 + 0.05 + (R + 0.1) * (1 - s) * 0.5, CZ - (R + 0.1) * (1 - s * 0.8)),
                   10, mat='liquor', r=0.012)
    m.flow('vacuum_filtrate', [(0, 0.1, CZ - R + 0.05), (0, 0.05, CZ - 0.2), (X1 + 0.15, 0, CZ), (X1 + 0.6, 0, CZ), (X1 + 1.0, 0, 0.8)], 'flow_suction', 0.015, 0.3)
    m.flow('cake', [(0, R + 0.08, CZ + 0.1), (0, R + 0.25, 0.6)], 'sand', 0.02, 0.2)
    _press(m, [lathe('vz', [(R + 0.04, X0), (R + 0.06, X0), (R + 0.06, X1), (R + 0.04, X1)], 'pressure_1', 48, a0=math.radians(-120), a1=math.radians(160), axis='X', center=(0, 0, CZ), cap_mat='pressure_1')],
           'Vacuum zones round the drum', 'Each drum sector passes through the slurry (cake formation under vacuum), then dewatering and washing zones, then a blow-back zone where the vacuum valve switches to '
           'air pressure to release the cake at the scraper. Vacuum is typically ~ 0.4–0.8 bar below atmospheric; cake moisture and wash efficiency set the soda carried to calcination.')
    return m.export(out)


# =============================================================== EQ-286 Hydrate washing system (belt filter)
def hydrate_washing_system(out):
    m = _model('hydrate_washing_system', 'Horizontal Vacuum Belt Filter with Counter-Current Hydrate Washing')
    Z, X0, X1 = 1.0, -1.8, 1.8
    belt_loop(m, 'bf', X0, X1, Z, 0.15, 0.7, revs=1.0, markers=14, label='Filter Belt (drainage belt + cloth)', foot_z=0.0, idlers=False)
    vb = [box(f'vb{k}', (0.6, 0.35, 0.18), (X0 + 0.7 + 0.7 * k, 0, Z + 0.03), 'paint_blue_dark') for k in range(4)]
    vb += [cyl(f'vp{k}', 0.035, 0.3, Z - 0.06, 'paint_blue_dark', 16, center=(X0 + 0.7 + 0.7 * k, 0, 0)) for k in range(4)]
    P(m, 'vacuum_boxes', 'Vacuum Boxes under the Belt & Filtrate Down-Pipes', 'vacuum', vb, explode=(0, 0, -0.4), ref='hw_vacuum', section='split')
    rc = [vessel(f'rc{k}', 0.12, 0.35, 0.006, 'paint_blue', center=(X0 + 0.7 + 0.7 * k, 0.55, 0), heads=('2:1', '2:1'), z0=0.15) for k in range(4)]
    P(m, 'filtrate_receivers', 'Filtrate Receivers (separate per zone: mother liquor, wash 1, wash 2, wash 3)', 'vacuum', rc, explode=(0, 0.5, 0), ref='hw_vacuum', section='keep')
    fb = box('fb', (0.4, 0.8, 0.3), (X0 + 0.4, 0, Z + 0.35), 'stainless')
    sp = []
    for k in range(3):
        x = X0 + 1.4 + 0.7 * k
        sp += [cyl(f'sh{k}', 0.025, -0.45, 0.45, 'stainless', 12, axis='Y', center=(x, 0, Z + 0.5))] + [cyl(f'sn{k}{j}', 0.01, Z + 0.4, Z + 0.5, 'brass', 8, center=(x, -0.3 + 0.2 * j, 0)) for j in range(4)]
    P(m, 'feed_wash', 'Feed Box & Wash Spray Headers (hot condensate, counter-current)', 'water', [fb] + sp, explode=(0, -0.4, 0.5), ref='hw_wash', section='keep')
    ck = box('ck', (X1 - X0 - 0.6, 0.33, 0.04), (0.2, 0.17, Z + 0.18), 'powder')
    P(m, 'cake', 'Hydrate Cake on the Belt', 'fluid', ck, explode=(0, -0.4, 0.3), ref='hw_cake', section='keep')
    P(m, 'discharge_chute', 'Cake Discharge Chute (to calcination)', 'discharge', box('dc', (0.4, 0.8, 0.5), (X1 + 0.35, 0, Z - 0.4), 'paint_grey'), explode=(0.4, 0, 0), ref='hw_cake', section='keep')
    for k in range(3):
        droplets(m, f'wash_{k + 1}', f'Wash Stage {k + 1} Sprays', X0 + 1.3 + 0.7 * k, X0 + 1.5 + 0.7 * k, Z + 0.4, Z + 0.2, n=3, mat='water', y=0.15, r=0.012)
    m.flow('slurry', [(X0 + 0.4, 0, Z + 0.7), (X0 + 0.4, 0, Z + 0.22)], 'flow_discharge', 0.02, 0.2)
    m.flow('wash_cascade', [(X0 + 2.8, 0.55, 0.4), (X0 + 2.8, 0.7, Z + 0.7), (X0 + 2.1, 0.7, Z + 0.7), (X0 + 2.1, 0.55, 0.4), (X0 + 2.1, 0.8, Z + 0.8), (X0 + 1.4, 0.8, Z + 0.8)], 'water', 0.015, 0.3)
    m.flow('cake', [(X0 + 0.5, 0, Z + 0.2), (X1, 0, Z + 0.2), (X1 + 0.35, 0, Z - 0.6)], 'sand', 0.02, 0.4)
    _press(m, [box(f'wz{k}', (0.6, 0.02, 0.15), (X0 + 0.7 + 0.7 * k, -0.4, Z + 0.03), f'pressure_{lev}') for k, lev in enumerate((8, 6, 4, 2))], 'Counter-current washing lowers soda in the hydrate',
           'Fresh hot condensate washes the cake in the last zone; its filtrate is used to wash the previous zone, and so on (counter-current). Soda in the cake falls zone by zone (red → blue) using little water. '
           'Low soda in the hydrate is essential because sodium ends up in the smelter-grade alumina product (typical spec ≲ 0.3–0.4 % Na₂O).')
    return m.export(out)


# =============================================================== EQ-287 Calcination fluidized bed cooler
def calcination_fluidized_bed_cooler(out):
    m = _model('calcination_fluidized_bed_cooler', 'Calcination Fluidised Bed Cooler (Water-Cooled Tube Bundles, Cascade Chambers)')
    X0, X1, W, ZD, H = -1.6, 1.6, 0.9, 0.7, 1.1
    bd = csg('bd', [box('bo', (X1 - X0 + 0.08, W + 0.08, H + 0.4), (0, 0, ZD - 0.2 + (H + 0.4) / 2), 'paint_grey')], [box('bi', (X1 - X0, W, H + 0.45), (0, 0, ZD - 0.2 + (H + 0.4) / 2 + 0.03), 'paint_grey')], 'paint_grey')
    wr = [box(f'wr{k}', (0.03, W, 0.45), (x, 0, ZD + 0.22), 'steel') for k, x in enumerate((-0.55, 0.55))] + [box('dp', (X1 - X0, W, 0.015), (0, 0, ZD), 'steel')]
    P(m, 'cooler_body', 'Cooler Body, Air Distributor & Chamber Weirs', 'casing', [bd] + wr, explode=(0, 0.7, 0), ref='fbc_body')
    tb = []
    for k, xc in enumerate((-1.05, 0.0, 1.05)):
        for j in range(4):
            for q in range(2):
                tb.append(cyl(f'tb{k}{j}{q}', 0.02, -W / 2 + 0.05, W / 2 - 0.05, 'steel', 10, axis='Y', center=(xc - 0.3 + 0.2 * j, 0, ZD + 0.12 + 0.15 * q)))
        tb += [cyl(f'hd{k}{s}', 0.045, ZD + 0.05, ZD + 0.35, 'steel', 16, center=(xc + s * 0.38, W / 2 + 0.06, 0)) for s in (-1, 1)]
    P(m, 'cooling_bundles', 'Cooling-Water Tube Bundles immersed in the Bed (counter-flow to the alumina)', 'tubes', tb, explode=(0, -0.8, 0), ref='fbc_tubes', section='keep')
    _bed_particles(m, 'bed', 'Fluidised Alumina flowing from Chamber to Chamber', X0 + 0.1, X1 - 0.1, 0.02, W / 2 - 0.05, ZD + 0.05, ZD + 0.42, 45, mat='powder', drift=1.0)
    ai = [box('pl', (X1 - X0, W, 0.3), (0, 0, ZD - 0.2), 'paint_blue'), hollow_pipe('ad', [(-2.4, 0, ZD - 0.2), (X0, 0, ZD - 0.2)], 0.1, 'paint_blue', 16)]
    P(m, 'air_plenum', 'Fluidising-Air Plenum & Inlet Duct', 'air', ai, explode=(0, 0, -0.4), ref='fbc_air', section='split')
    nz = [box('in', (0.3, 0.4, 0.4), (X0 + 0.2, 0, ZD + H + 0.35), 'paint_grey'), box('out', (0.3, 0.4, 0.4), (X1 + 0.2, 0, ZD + 0.1), 'paint_grey'), nozzle('ex', (0.0, 0, ZD + H + 0.2), (0, 0, 1), 0.12, 0.3)]
    nz += [hollow_pipe('cw', [(X1 + 0.6, W / 2 + 0.06, ZD + 0.05), (X1 + 0.6, W / 2 + 0.25, ZD + 0.05), (X0 - 0.3, W / 2 + 0.25, ZD + 0.35)], 0.03, 'paint_blue', 12, bend=0.04)]
    P(m, 'nozzles', 'Hot Alumina Inlet (from calciner), Cooled Alumina Outlet, Air Exhaust, Cooling-Water Lines', 'nozzles', nz, explode=(0, 0, 0.4), ref='fbc_nozzles', section='keep')
    m.flow('alumina', [(X0 + 0.2, 0, ZD + H + 0.5), (X0 + 0.2, 0, ZD + 0.3), (X1, 0, ZD + 0.3), (X1 + 0.2, 0, ZD - 0.1)], 'sand', 0.025, 0.4)
    m.flow('air', [(-2.5, 0, ZD - 0.2), (0, -0.2, ZD - 0.1), (0, -0.2, ZD + H), (0, 0, ZD + H + 0.5)], 'air', 0.025, 0.4)
    m.flow('cooling_water', [(X1 + 0.6, W / 2 + 0.25, ZD + 0.05), (X0 - 0.3, W / 2 + 0.25, ZD + 0.35)], 'water', 0.015, 0.3)
    _bands_x(m, [(X0, -0.55, 8), (-0.55, 0.55, 5), (0.55, X1, 2)], W, 0.5, ZD + 0.22, 'Alumina cools chamber by chamber',
             'Hot alumina from the calciner/cyclone coolers (several hundred °C) flows through the cascade of fluidised chambers. Fluidising air and the immersed water-cooled bundles remove heat; the water flows '
             'counter-current to the alumina. Product leaves at roughly 80 °C or less for safe conveying and storage; the warm air is often used as combustion air.')
    return m.export(out)


# =============================================================== EQ-288 Alumina cooler (rotary)
def alumina_cooler(out):
    m = _model('alumina_cooler', 'Rotary Alumina Cooler (Indirect, External Water-Spray Cooling)')
    R, X0, X1, CZ = 0.55, -1.5, 1.5, 1.0
    _drum_machine(m, R, X0, X1, CZ, 'Cooler Drum', 'ac', liner_mat='steel', revs=0.6)
    sp = [cyl('sph', 0.03, X0 + 0.3, X1 - 0.6, 'stainless', 12, axis='X', center=(0, 0.2, CZ + R + 0.25))] + [cyl(f'sn{k}', 0.01, CZ + R + 0.12, CZ + R + 0.25, 'brass', 8, center=(X0 + 0.4 + 0.3 * k, 0.2, 0)) for k in range(8)]
    sp += [csg('pn', [box('pno', (X1 - X0 - 0.6, 1.5, 0.3), (-0.15, 0, 0.3), 'paint_grey')], [box('pni', (X1 - X0 - 0.66, 1.44, 0.3), (-0.15, 0, 0.35), 'paint_grey')], 'paint_grey')]
    P(m, 'spray_system', 'External Water-Spray Header & Collecting Pan', 'water', sp, explode=(0, 0.4, 0.5), ref='ac_spray', section='keep')
    hd = [box('ih', (0.5, 0.9, 0.9), (X0 - 0.25, 0, CZ + 0.1), 'paint_grey'), box('oh', (0.5, 0.9, 1.2), (X1 + 0.25, 0, CZ - 0.2), 'paint_grey')]
    P(m, 'hoods', 'Inlet Hood (hot alumina feed) & Discharge Hood', 'casing', hd, explode=(0, 0, 0.4), ref='ac_hoods', section='split')
    sup = [cyl(f'rr{k}{s}', 0.12, x - 0.07, x + 0.07, 'steel', 24, axis='X', center=(0, s * 0.45, CZ - R - 0.08)) for k, x in enumerate((X0 + 0.25, X1 - 0.25)) for s in (-1, 1)]
    sup += [box(f'bs{k}', (0.4, 1.3, CZ - R - 0.15), (x, 0, (CZ - R - 0.15) / 2), 'paint_grey') for k, x in enumerate((X0 + 0.25, X1 - 0.25))]
    sup += [box('gbx', (0.35, 0.3, 0.3), (0.0, R + 0.55, CZ - 0.35), 'paint_blue'), cyl('mot', 0.13, R + 0.7, R + 1.15, 'paint_motor', 24, axis='Y', center=(0.0, 0, CZ - 0.35))]
    P(m, 'supports_drive', 'Support Rollers & Drive', 'structure', sup, explode=(0, 0, -0.4), ref='ac_drive', section='keep')
    def tumble(i, s):
        x = X0 + 0.1 + (X1 - X0 - 0.2) * s
        ph = (s * 6 + i * 0.29) % 1.0
        r = R - 0.1
        if ph < 0.7:
            a = math.radians(-150 + 80 * ph / 0.7)
            return (x, 0.06 + 0.06 * (i % 3), CZ + r * math.sin(a))
        u = (ph - 0.7) / 0.3
        z0, z1 = CZ + r * math.sin(math.radians(-70)), CZ + r * math.sin(math.radians(-150))
        return (x, 0.06 + 0.06 * (i % 3), z0 + (z1 - z0) * u)
    particles_path(m, 'alumina', 'Alumina tumbling against the Cooled Shell', tumble, 14, mat='powder', r=0.03)
    droplets(m, 'spray', 'Cooling Water running over the Shell', X0 + 0.4, X1 - 0.6, CZ + R + 0.12, 0.45, n=10, mat='water', y=0.4, r=0.012)
    m.flow('alumina_flow', [(X0 - 0.25, 0, CZ + 0.55), (X0 + 0.1, 0.05, CZ - R + 0.1), (X1, 0.05, CZ - R + 0.1), (X1 + 0.25, 0, 0.3)], 'sand', 0.025, 0.4)
    _bands_x(m, [(X0, -0.3, 8), (-0.3, 0.8, 5), (0.8, X1, 2)], 2 * R + 0.1, 2 * R + 0.1, CZ, 'Indirect cooling through the shell',
             'Hot alumina tumbles inside while water sprays and runs over the outside of the shell, removing heat through the steel wall (no contact between water and product). Lifters improve contact '
             'with the cooled wall. Shell temperature differences and scaling of the external surface reduce performance.')
    return m.export(out)


# =============================================================== EQ-289 Alumina storage silo
def alumina_storage_silo(out):
    m = _model('alumina_storage_silo', 'Alumina Storage Silo (Aerated Floor, Bin-Vent Filter, Truck/Rail Loading)')
    R, Z0, H = 1.1, 1.3, 2.4
    sh = csg('sh', [cyl('so', R + 0.02, Z0, Z0 + H, 'paint_grey', 96), cyl('rf', R + 0.05, Z0 + H, Z0 + H + 0.05, 'paint_grey', 96)], [cyl('si', R, Z0 + 0.05, Z0 + H, 'paint_grey', 96)], 'paint_grey')
    fl = cyl('fl', R + 0.02, Z0, Z0 + 0.05, 'cast_iron', 96)
    sk = csg('sk', [cyl('sko', R + 0.02, 0.0, Z0, 'cast_iron', 96)], [cyl('ski', R - 0.15, -0.1, Z0 - 0.1, 'cast_iron', 96), box('skd', (1.0, 3, 0.9), (0, 0, 0.45), 'cast_iron')], 'cast_iron')
    P(m, 'silo_shell', 'Silo Shell, Roof & Concrete Skirt (with truck drive-through)', 'casing', [sh, fl, sk], explode=(0, 0.8, 0), ref='as_shell')
    ae = [rotate(box(f'as{k}', (R - 0.2, 0.15, 0.04), ((R - 0.2) / 2 + 0.12, 0, Z0 + 0.07), 'polypropylene'), TAU * k / 8, 'Z') for k in range(8)]
    ae += [cyl('dc', 0.15, Z0 - 0.4, Z0 + 0.1, 'steel', 32, r_in=0.13), box('ls', (0.3, 0.3, 0.2), (0, 0, Z0 - 0.5), 'paint_blue_dark'), cyl('sp', 0.12, 0.6, Z0 - 0.6, 'polypropylene', 24)]
    P(m, 'aeration_discharge', 'Aerated Floor (air-slide pads), Discharge Gate & Telescopic Loading Spout', 'discharge', ae, explode=(0, -0.6, -0.3), ref='as_aeration', section='keep')
    pl = P(m, 'alumina', 'Stored Alumina (level animated)', 'fluid', lathe('al', [(0.0, Z0 + 0.09), (R - 0.01, Z0 + 0.09), (R - 0.01, Z0 + 1.6), (0.0, Z0 + 1.9)], 'powder', 64, a0=0.0, a1=math.pi, cap_mat='powder'),
           explode=(0, -0.4, 0), ref='as_product', section='keep', pivot=(0, 0, Z0 + 0.09))
    keys_loop(m, pl, lambda t: (1, 1, 1 + 0.15 * math.sin(TAU * t)), 'scale')
    rf = [vessel('bv', 0.25, 0.4, 0.006, 'paint_grey', heads=('flat', '2:1'), z0=Z0 + H + 0.05, center=(0.5, 0.2, 0)), cyl('rd', 0.06, Z0 + H + 0.05, Z0 + H + 0.25, 'paint_blue_dark', 16, center=(-0.5, 0.3, 0)),
          hollow_pipe('fp', [(-2.0, 0, Z0 + H + 0.4), (-0.2, 0, Z0 + H + 0.4), (-0.2, 0, Z0 + H - 0.1)], 0.07, 'steel', 16, bend=0.1), box('pv', (0.15, 0.15, 0.15), (-0.8, 0.5, Z0 + H + 0.12), 'brass')]
    P(m, 'roof_equipment', 'Bin-Vent Filter, Radar Level Transmitter, Fill Pipe & Pressure/Vacuum Relief', 'roof', rf, explode=(0, 0, 0.6), ref='as_roof', section='keep')
    tr = join('tr', [box('tc', (1.6, 0.7, 0.5), (0, 0, 0.45), 'paint_yellow'), cyl(f'tw', 0.15, -0.38, 0.38, 'rubber', 24, axis='Y', center=(0.5, 0, 0.15)), cyl('tw2', 0.15, -0.38, 0.38, 'rubber', 24, axis='Y', center=(-0.5, 0, 0.15))])
    P(m, 'tanker', 'Bulk Road Tanker being Loaded', 'vehicle', tr, explode=(0, -0.8, 0), ref='as_aeration', section='keep')
    droplets(m, 'loading', 'Alumina flowing through the Loading Spout', 0.0, 0.0, Z0 - 0.5, 0.7, n=6, mat='powder', y=0.0, r=0.03)
    m.flow('fill', [(-2.1, 0, Z0 + H + 0.4), (-0.2, 0, Z0 + H + 0.4), (-0.2, 0, Z0 + 1.5)], 'sand', 0.02, 0.3)
    m.flow('aeration_air', [(0.9, 0.1, Z0 + 0.1), (0.1, 0.1, Z0 + 0.1)], 'air', 0.012, 0.2)
    m.flow('discharge', [(0, 0, Z0 + 0.1), (0, 0, 0.7)], 'sand', 0.02, 0.2)
    _press(m, [cyl('az', R + 0.06, Z0, Z0 + 0.15, 'pressure_5', 96, r_in=R + 0.04)], 'Aeration makes alumina flow',
           'Low-pressure air (typically a few hundred mbar) blown through porous air-slide pads fluidises the alumina above the floor so it flows to the discharge without bridging or rat-holing. '
           'The bin-vent filter releases displaced air during filling while retaining dust.')
    return m.export(out)


# =============================================================== EQ-290 Alumina pneumatic conveying (dense phase)
def alumina_pneumatic_conveying_system(out):
    m = _model('alumina_pneumatic_conveying_system', 'Dense-Phase Pneumatic Conveying of Alumina (Blow Tank / Pressure Vessel)')
    R, Z0, L = 0.4, 1.2, 0.8
    bt = vessel('bt', R, L, 0.012, 'paint_grey', heads=('cone', '2:1'), z0=Z0, center=(-1.6, 0, 0))
    P(m, 'blow_tank', 'Blow Tank (pressure vessel conveying batches)', 'vessel', bt, explode=(0, 0.6, 0), ref='pc_blowtank')
    fill = lambda t: smooth_pulse(t, 0.2, 0.25, 0.25)
    pa = P(m, 'batch', 'Alumina Batch in the Blow Tank (fills, then is blown out)', 'fluid', lathe('ab', [(0.0, Z0 - R + 0.05), (0.1, Z0 - R + 0.05), (R - 0.012, Z0), (R - 0.012, Z0 + 0.6), (0.0, Z0 + 0.7)], 'powder', 48, a0=0.0, a1=math.pi, center=(-1.6, 0, 0), cap_mat='powder'),
           explode=(0, -0.4, 0), ref='pc_blowtank', section='keep', pivot=(-1.6, 0, Z0 - R))
    keys_loop(m, pa, lambda t: (1, 1, max(0.02, fill(t))), 'scale')
    hp = join('hp', [silo('hs', 0.45, Z0 + L + 0.5, 0.6, cx=-1.6), cyl('hn', 0.1, Z0 + L + R * 0.5, Z0 + L + 0.5 - 0.45, 'steel', 24, center=(-1.6, 0, 0))])
    P(m, 'feed_hopper', 'Feed Hopper above the Blow Tank', 'vessel', hp, explode=(0, 0.4, 0.4), ref='pc_hopper', section='split')
    dv = join('dv', [cyl('dvb', 0.13, Z0 + L + R * 0.5 + 0.02, Z0 + L + R * 0.5 + 0.12, 'paint_blue_dark', 32, center=(-1.6, 0, 0)), cyl('dva', 0.05, Z0 + L + R * 0.5 + 0.12, Z0 + L + R * 0.5 + 0.3, 'paint_grey', 16, center=(-1.75, 0, 0))])
    pdv = P(m, 'dome_valve', 'Inlet Dome Valve (opens to fill, seals to pressurise)', 'valves', dv, explode=(0, -0.3, 0.4), ref='pc_valves', section='keep')
    keys_loop(m, pdv, lambda t: (0, 0, 0.06 * (1 - smooth_pulse(t, 0.05, 0.25, 0.05))) if t < 0.5 else (0, 0, 0))
    ln = [hollow_pipe('cl', [(-1.6, 0, Z0 - R - 0.05), (-1.6, 0, 0.5), (-1.2, 0, 0.5), (1.2, 0, 0.5), (1.4, 0, 0.7), (1.4, 0, 3.5), (1.6, 0, 3.7), (2.0, 0, 3.7)], 0.06, 'steel', 24, bend=0.25)]
    ln += [cyl(f'bs{k}', 0.015, 0.56, 0.75, 'paint_blue', 8, center=(x, 0.08, 0)) for k, x in enumerate((-0.6, 0.2, 1.0))] + [hollow_pipe('ba', [(-1.6, 0.3, 0.75), (1.0, 0.3, 0.75)], 0.02, 'paint_blue', 8)]
    ln += [hollow_pipe('ai', [(-2.6, 0, Z0 + 0.4), (-2.0, 0, Z0 + 0.4), (-1.6 - R, 0, Z0 + 0.4)], 0.03, 'paint_blue', 12, bend=0.05), box('ov', (0.12, 0.12, 0.12), (-1.6, 0, 0.75), 'paint_blue_dark')]
    P(m, 'conveying_line', 'Conveying Pipeline, Outlet Valve, Pressurising Air & Booster Air Injectors', 'piping', ln, explode=(0, 0, 0.3), ref='pc_line', section='keep')
    P(m, 'receiving_silo', 'Receiving Silo (top entry) on Legs', 'vessel', [silo('rs', 0.6, 2.4, 1.6, cx=2.4), legs('rl', 0.6, 0.0, 2.4, n=4, cx=2.4)], explode=(0.5, 0, 0), ref='pc_silo')
    P(m, 'supports', 'Blow-Tank Support Structure', 'structure', legs('lg', R, 0.0, Z0, n=4, cx=-1.6), explode=(0, 0, -0.3), ref='pc_blowtank', section='keep')
    path = [(-1.6, 0.0, Z0 - R - 0.05), (-1.6, 0, 0.5), (1.2, 0, 0.5), (1.4, 0, 0.7), (1.4, 0, 3.5), (2.0, 0, 3.7), (2.4, 0, 3.6)]
    segs = [(Vector(a), Vector(b)) for a, b in zip(path[:-1], path[1:])]
    Ltot = sum((b - a).length for a, b in segs)
    def plug(i, s):
        if s < 0.5:
            return (-1.6, 0.0, Z0)                                   # waiting (hidden) while tank fills
        d = (s - 0.5) / 0.5 * Ltot - i * 0.25
        d = max(0.0, d)
        for a, b in segs:
            l = (b - a).length
            if d <= l:
                return tuple(a + (b - a) * (d / l))
            d -= l
        return path[-1]
    particles_path(m, 'plugs', 'Dense-Phase Plugs moving slowly along the Line', plug, 6, mat='powder', r=0.05, scale_fn=lambda i, s: 0.0 if s < 0.5 else 1.0)
    m.flow('conveying', [(-1.6, 0, Z0 - 0.2), (-1.6, 0, 0.5), (1.2, 0, 0.5), (1.4, 0, 3.5), (2.0, 0, 3.7), (2.4, 0, 3.4)], 'sand', 0.03, 0.5, active=[(0.5, 1.0)])
    m.flow('filling', [(-1.6, 0, Z0 + L + 1.3), (-1.6, 0, Z0 + 0.4)], 'sand', 0.025, 0.2, active=[(0.0, 0.5)])
    m.flow('air', [(-2.7, 0, Z0 + 0.4), (-1.6 - R, 0, Z0 + 0.4)], 'air', 0.015, 0.2, active=[(0.5, 1.0)])
    _press(m, [cyl('bz', R + 0.05, Z0, Z0 + L, 'pressure_7', 48, center=(-1.6, 0, 0), r_in=R + 0.03)], 'Low velocity, high pressure: gentle on alumina',
           'In dense phase the blow tank is pressurised (often ~ 2–6 bar) and the alumina moves as slow plugs or dunes (typically ~ 2–10 m/s) rather than suspended at high speed. This greatly reduces '
           'particle breakage (attrition creates fines/dust that smelters dislike) and pipe wear, and needs less air than dilute-phase conveying.')
    return m.export(out)


# =============================================================== EQ-291 Causticization tank
def causticization_tank(out):
    m = _model('causticization_tank', 'Causticization Reactor with Lime Slaker (Caustic Recovery)')
    R, Z0, H = 0.75, 0.3, 1.6
    agitated_tank(m, 'cz_', R, Z0, H, 'Causticization Reactor', 'ct', liquid='liquor', imp='pbt', revs=1.5, open_top=False)
    sl = join('sl', [cyl('sd', 0.3, -2.6, -1.4, 'paint_grey', 48, axis='X', center=(0, 0, 1.3), r_in=0.28), cyl('sm', 0.12, -2.95, -2.65, 'paint_motor', 24, axis='X', center=(0, 0, 1.3))])
    P(m, 'lime_slaker', 'Lime Slaker (CaO + H₂O → Ca(OH)₂ milk of lime)', 'slaker', sl, explode=(-0.4, 0, 0), ref='ct_slaker', section='split')
    pd = [rotate(box(f'pd{k}', (0.12, 0.02, 0.18), (-2.4 + 0.15 * k, 0, 1.3 - 0.12), 'steel'), TAU * k / 7, 'X', (0, 0, 1.3)) for k in range(8)] + [cyl('psh', 0.03, -2.65, -1.4, 'steel', 12, axis='X', center=(0, 0, 1.3))]
    ppd = P(m, 'slaker_paddles', 'Slaker Paddle Shaft', 'rotating_element', pd, explode=(-0.4, -0.4, 0), ref='ct_slaker', section='keep', pivot=(0, 0, 1.3))
    ppd.spin('X', 2)
    ls = join('ls', [silo('lsv', 0.3, 2.0, 0.6, cx=-2.0), cyl('lsf', 0.06, 1.45, 2.0 - 0.3, 'steel', 16, center=(-2.0, 0, 0))])
    P(m, 'lime_silo', 'Quicklime Silo & Feeder', 'vessel', ls, explode=(-0.3, 0, 0.5), ref='ct_slaker', section='split')
    pp = [hollow_pipe('ml', [(-1.4, 0, 1.25), (-R - 0.2, 0, 1.25), (-0.3, 0, Z0 + H + 0.4), (-0.3, 0, Z0 + H)], 0.04, 'paint_grey', 12, bend=0.06),
          hollow_pipe('li', [(-1.6, 0.5, Z0 + H + 0.6), (0.3, 0.5, Z0 + H + 0.6), (0.3, 0.3, Z0 + H)], 0.05, 'stainless', 12, bend=0.06), nozzle('out', (R, 0, Z0 + 0.2), (1, 0, 0), 0.06, 0.3)]
    P(m, 'piping', 'Lime Milk Line, Liquor Inlet & Slurry Outlet (to separation)', 'piping', pp, explode=(0, 0, 0.4), ref='ct_piping', section='keep')
    P(m, 'supports', 'Support Legs', 'structure', legs('lg', R, 0.0, Z0, n=4), explode=(0, 0, -0.3), ref='ct_piping', section='keep')
    particles_path(m, 'caco3', 'Calcium Carbonate (CaCO₃) particles forming', lambda i, s: ((0.15 + 0.5 * ((i * 0.31) % 1)) * math.cos(TAU * (s + i / 12)), abs((0.15 + 0.5 * ((i * 0.31) % 1)) * math.sin(TAU * (s + i / 12))) + 0.02,
                                                                                         Z0 + 0.25 + (H - 0.5) * (0.5 + 0.5 * math.sin(TAU * (s + i * 0.21)))), 12, mat='powder', r=0.018, scale_fn=lambda i, s: 0.4 + 1.0 * s)
    m.flow('lime_milk', [(-2.6, 0, 1.3), (-1.4, 0, 1.25), (-R - 0.2, 0, 1.25), (-0.3, 0, Z0 + H + 0.4), (-0.3, 0, Z0 + H - 0.3)], 'flow_discharge', 0.015, 0.3)
    m.flow('liquor', [(-1.7, 0.5, Z0 + H + 0.6), (0.3, 0.5, Z0 + H + 0.6), (0.3, 0.3, Z0 + H - 0.3)], 'flow_suction', 0.015, 0.3)
    m.flow('product', [(R - 0.1, 0, Z0 + 0.2), (R + 0.5, 0, Z0 + 0.2)], 'flow_discharge', 0.015, 0.2)
    _press(m, [cyl('rz', R + 0.05, Z0, Z0 + H, 'pressure_6', 64, r_in=R + 0.03)], 'Recovering caustic from carbonate',
           'Carbon dioxide picked up by the liquor turns caustic into sodium carbonate, which does nothing useful. Adding slaked lime converts it back: Na₂CO₃ + Ca(OH)₂ → 2 NaOH + CaCO₃↓. '
           'The calcium carbonate solids are separated and the regenerated caustic returns to the circuit; conditions (temperature, liquor strength) are chosen to limit alumina losses as calcium aluminates.', kind='pressure')
    return m.export(out)


# =============================================================== EQ-292 Oxalate removal system
def oxalate_removal_system(out):
    m = _model('oxalate_removal_system', 'Sodium Oxalate Removal (Seeded Crystallizer + Hydrocyclone)')
    R, Z0, H = 0.7, 0.4, 1.8
    agitated_tank(m, 'ox_', R, Z0, H, 'Oxalate Crystallizer', 'ox', liquid='liquor', imp='hydrofoil', revs=1.0, open_top=True, baffles=False, draft_tube=True)
    jk = cyl('jk', R + 0.07, Z0 + 0.2, Z0 + H - 0.2, 'paint_blue', 96, r_in=R + 0.02)
    P(m, 'cooling_jacket', 'Cooling Jacket (lowers temperature to drive crystallisation)', 'heater', jk, explode=(0, 0.6, 0), ref='ox_cooling')
    objs, info = hydrocyclone('cy', 1.6, 0.0, 2.6, D=0.2, L_cyl=0.25, L_cone=0.7)
    P(m, 'hydrocyclone', 'Hydrocyclone (separates oxalate crystals; overflow = de-oxalated liquor)', 'separator', objs, explode=(0.5, 0, 0), ref='ox_cyclone', section='keep')
    pp = [hollow_pipe('tc', [(R, 0, Z0 + 0.2), (1.2, 0, Z0 + 0.2), (1.2, 0, 2.5), (1.6 - 0.12, 0.07, 2.5)], 0.04, 'stainless', 12, bend=0.06),
          hollow_pipe('ur', [(1.6, 0, info['za'] - 0.05), (1.6, 0, 1.0), (0.4, 0, 1.0), (0.4, 0, Z0 + H)], 0.03, 'stainless', 12, bend=0.06),
          hollow_pipe('ol', [(1.6, 0, 2.85), (1.6, 0, 3.0), (2.4, 0, 3.0)], 0.03, 'stainless', 12, bend=0.05), nozzle('in', (-R, 0, Z0 + H - 0.2), (-1, 0, 0), 0.05, 0.3)]
    P(m, 'piping', 'Crystallizer → Cyclone Feed, Seed Return (underflow) & Clean Liquor Overflow', 'piping', pp, explode=(0, 0, 0.4), ref='ox_cyclone', section='keep')
    _pump(m, 'feed_pump', 'Cyclone Feed Pump', 1.2, 0.5, 0.25, 'ox_cyclone', explode=(0.3, 0.3, 0))
    P(m, 'foundation', 'Ring-Wall Foundation', 'structure', cyl('fd', R + 0.1, 0.0, Z0, 'cast_iron', 96), explode=(0, 0, -0.3), ref='ox_tank', section='split')
    particles_path(m, 'oxalate', 'Needle-like Sodium Oxalate Crystals growing on Seed', lambda i, s: ((0.15 + 0.4 * ((i * 0.37) % 1)) * math.cos(TAU * (s + i / 10)), abs((0.15 + 0.4 * ((i * 0.37) % 1)) * math.sin(TAU * (s + i / 10))) + 0.02,
                                                                                               Z0 + 0.3 + (H - 0.6) * (0.5 + 0.5 * math.sin(TAU * (s + i * 0.17)))), 12, mat='powder', r=0.016, scale_fn=lambda i, s: 0.5 + 1.0 * s)
    m.flow('liquor_in', [(-R - 0.4, 0, Z0 + H - 0.2), (-0.2, 0.1, Z0 + H - 0.3)], 'flow_suction', 0.015, 0.2)
    m.flow('to_cyclone', [(R - 0.1, 0, Z0 + 0.2), (1.2, 0, Z0 + 0.2), (1.2, 0, 2.5), (1.6, 0.05, 2.45)], 'flow_discharge', 0.015, 0.3)
    m.flow('clean_liquor', [(1.6, 0, 2.6), (1.6, 0, 3.0), (2.5, 0, 3.0)], 'water', 0.015, 0.2)
    m.flow('seed_return', [(1.6, 0, info['za']), (1.6, 0, 1.0), (0.4, 0, 1.0), (0.4, 0, Z0 + H - 0.3)], 'sand', 0.015, 0.3)
    _bands_z(m, [(Z0 + 0.2, Z0 + H - 0.2, 3)], R + 0.07, 'Why oxalate must be removed',
             'Organic matter in bauxite degrades in the hot caustic liquor to sodium oxalate. If it builds up, oxalate co-precipitates with gibbsite, giving fine, weak hydrate and lower yield. A side-stream is '
             'cooled and seeded with oxalate crystals so oxalate crystallises in a controlled way; crystals are separated (cyclones/filters) and destroyed (e.g. by lime or burning), and the clean liquor returns.', kind='temperature')
    return m.export(out)


# =============================================================== EQ-293 Sodium oxalate filter (horizontal pressure leaf)
def sodium_oxalate_filter(out):
    m = _model('sodium_oxalate_filter', 'Horizontal Pressure-Leaf Filter for Sodium Oxalate')
    R, X0, L, CZ = 0.55, -1.0, 2.0, 1.1
    sh = vessel('sh', R, L, 0.012, 'paint_grey', axis='X', center=(0, 0, CZ), heads=('flat', '2:1'), z0=X0)
    psh = P(m, 'shell', 'Pressure Shell (retracts on rails to discharge the cake)', 'vessel', sh, explode=(0.6, 0.6, 0), ref='of_shell')
    keys_loop(m, psh, lambda t: (0.8 * smooth_pulse(t, 0.12, 0.15, 0.12) if t > 0.6 else 0.0, 0, 0))
    hd = join('hd', [cyl('hf', R + 0.08, X0 - 0.08, X0, 'paint_blue', 64, axis='X', center=(0, 0, CZ)), box('hs', (0.3, 1.2, CZ - 0.1), (X0 - 0.2, 0, (CZ - 0.1) / 2), 'paint_blue'),
                     cyl('mf', 0.05, X0 - 0.4, X0 + L - 0.1, 'stainless', 16, axis='X', center=(0, 0, CZ - R + 0.12))])
    P(m, 'fixed_head', 'Fixed Head, Stand & Filtrate Manifold', 'frame', hd, explode=(-0.4, 0, 0), ref='of_head')
    lv = []
    for k in range(9):
        x = X0 + 0.2 + 0.2 * k
        h = 2 * math.sqrt(max(0.0, (R - 0.06) ** 2 - 0.0)) - 0.15
        lv.append(cyl(f'lf{k}', R - 0.08, x - 0.01, x + 0.01, 'steel', 48, axis='X', center=(0, 0, CZ + 0.03)))
        lv.append(cyl(f'ck{k}', R - 0.1, x - 0.025, x + 0.025, 'powder', 48, axis='X', center=(0, 0, CZ + 0.03)))
        lv.append(cyl(f'ln{k}', 0.015, CZ - R + 0.12, CZ - 0.3, 'stainless', 8, center=(x, 0, 0)))
    P(m, 'leaves', 'Filter Leaves (mesh-covered frames) with Oxalate Cake, on the Filtrate Manifold', 'filter_media', lv, explode=(0, -0.6, 0.3), ref='of_leaves', section='split')
    sl = [cyl('sl', 0.025, X0, X0 + L - 0.1, 'stainless', 12, axis='X', center=(0, 0, CZ + R - 0.1))] + [cyl(f'sn{k}', 0.008, CZ + R - 0.18, CZ + R - 0.1, 'brass', 6, center=(X0 + 0.3 + 0.2 * k, 0, 0)) for k in range(8)]
    P(m, 'sluice_header', 'Sluicing / Wash Header', 'water', sl, explode=(0, -0.3, 0.4), ref='of_sluice', section='keep')
    rl = [box(f'rl{s}', (L + 1.4, 0.06, 0.06), (X0 + L / 2 + 0.5, s * 0.45, 0.03), 'steel_dark') for s in (-1, 1)] + [box(f'sp{k}', (0.15, 1.0, CZ - R - 0.05), (x, 0, (CZ - R - 0.05) / 2 + 0.06), 'paint_grey') for k, x in enumerate((X0 + 0.4, X0 + L - 0.3))]
    P(m, 'rails_supports', 'Shell Rails & Carriages', 'structure', rl, explode=(0, 0, -0.3), ref='of_shell', section='keep')
    P(m, 'cake_hopper', 'Cake Discharge Hopper', 'discharge', csg('hp', [box('hpo', (L, 1.0, 0.4), (X0 + L / 2, 0, 0.25), 'paint_grey')], [box('hpi', (L - 0.06, 0.94, 0.4), (X0 + L / 2, 0, 0.3), 'paint_grey')], 'paint_grey'),
      explode=(0, 0, -0.4), ref='of_shell', section='keep')
    particles_path(m, 'feed_particles', 'Oxalate Crystals carried onto the Leaves', lambda i, s: (X0 + 0.25 + 0.2 * (i % 8), 0.05 + 0.4 * (1 - s), CZ + 0.3 - 0.4 * ((i * 0.37) % 1)), 10, mat='powder', r=0.012)
    m.flow('feed', [(X0 - 0.5, 0, CZ + 0.3), (X0 + 0.1, 0.1, CZ + 0.3)], 'flow_discharge', 0.015, 0.2, active=[(0.0, 0.6)])
    m.flow('filtrate', [(X0 + 0.6, 0.0, CZ - 0.3), (X0 + 0.6, 0, CZ - R + 0.12), (X0 - 0.4, 0, CZ - R + 0.12)], 'water', 0.015, 0.2, active=[(0.0, 0.6)])
    _press(m, [cyl('pz', R + 0.04, X0, X0 + L, 'pressure_7', 48, axis='X', center=(0, 0, CZ), r_in=R + 0.025)], 'Pressure filtration, then cake discharge',
           'Slurry is pumped into the closed shell under pressure (typically a few bar); liquid passes through the leaf screens into the manifold while oxalate builds up as cake on both faces of each leaf. '
           'At the end of the cycle the shell is drained, opened (rolled back) and the cake is sluiced or vibrated off into the hopper.')
    return m.export(out)


# =============================================================== EQ-294 Process liquor clarifier (multi-tray)
def process_liquor_clarifier(out):
    m = _model('process_liquor_clarifier', 'Multi-Tray Process Liquor Clarifier (Stacked Settling Trays, Common Rake Shaft)')
    R, Z0, H = 1.0, 0.5, 2.4
    tk = csg('tk', [cyl('to', R + 0.02, Z0, Z0 + H, 'paint_grey', 96), lathe('tb', [(0.0, Z0 - 0.4), (0.15, Z0 - 0.4), (R + 0.02, Z0), (0.0, Z0)], 'paint_grey', 96)],
             [cyl('ti', R, Z0, Z0 + H + 0.1, 'paint_grey', 96), lathe('tbi', [(0.0, Z0 - 0.37), (0.13, Z0 - 0.37), (R, Z0 + 0.01), (0.0, Z0 + 0.01)], 'paint_grey', 96)], 'paint_grey')
    ld = csg('ld', [cyl('ldo', R + 0.18, Z0 + H - 0.15, Z0 + H, 'paint_grey', 96)], [cyl('ldi', R + 0.02, Z0 + H - 0.2, Z0 + H + 0.05, 'paint_grey', 96), cyl('ldc', R + 0.15, Z0 + H - 0.12, Z0 + H + 0.05, 'paint_grey', 96)], 'paint_grey')
    P(m, 'tank', 'Clarifier Tank & Top Overflow Launder', 'tank', [tk, ld], explode=(0, 0.7, 0), ref='pl_tank')
    trays = []
    zs = (Z0 + 0.6, Z0 + 1.2, Z0 + 1.8)
    for k, z in enumerate(zs):
        trays.append(lathe(f'tr{k}', [(0.18, z + 0.15), (0.2, z + 0.15), (R - 0.005, z), (R - 0.005, z - 0.015), (0.18, z + 0.135)], 'steel', 96))
        trays.append(cyl(f'dc{k}', 0.17, z - 0.45, z + 0.15, 'steel', 32, r_in=0.155))
    P(m, 'trays', 'Stacked Conical Trays with Central Mud Downcomers (multiply settling area)', 'internals', trays, explode=(0, -0.7, 0), ref='pl_trays', section='split')
    lq = lathe('lq', [(0.0, Z0 - 0.36), (0.13, Z0 - 0.36), (R - 0.005, Z0 + 0.01), (R - 0.005, Z0 + H - 0.16), (0.0, Z0 + H - 0.16)], 'liquor', 64, a0=0.0, a1=math.pi, cap_mat='liquor')
    P(m, 'liquor', 'Process Liquor', 'fluid', lq, explode=(0, -0.4, 0), ref='pl_tank', section='keep')
    md = [lathe(f'md{k}', [(0.2, z + 0.15), (R - 0.01, z + 0.002), (R - 0.01, z + 0.06), (0.2, z + 0.2)], 'red_mud', 48, a0=0.0, a1=math.pi, cap_mat='red_mud') for k, z in enumerate(zs)]
    md.append(lathe('mdb', [(0.0, Z0 - 0.36), (0.13, Z0 - 0.36), (R - 0.01, Z0 + 0.01), (R - 0.01, Z0 + 0.08), (0.0, Z0 + 0.08)], 'red_mud', 48, a0=0.0, a1=math.pi, cap_mat='red_mud'))
    P(m, 'mud_layers', 'Settled Solids on each Tray & in the Bottom Cone', 'fluid', md, explode=(0, -0.5, -0.2), ref='pl_trays', section='keep')
    rk = [cyl('sh', 0.05, Z0 - 0.3, Z0 + H + 0.4, 'steel', 24)]
    for k, z in enumerate((Z0 - 0.05,) + zs):
        for s in (-1, 1):
            a0, a1 = Vector((s * 0.22, 0, (z + 0.17) if k else Z0 - 0.3)), Vector((s * (R - 0.05), 0, (z + 0.02) if k else Z0 - 0.02))
            d = a1 - a0
            arm = box(f'ar{k}{s}', (d.length, 0.04, 0.04), (0, 0, 0), 'steel')
            arm.data.transform(Matrix.Translation((a0 + a1) / 2 + Vector((0, 0, 0.04))) @ Matrix.Rotation(-math.atan2(d.z, d.x), 4, 'Y'))
            rk.append(arm)
    prk = P(m, 'rakes', 'Rake Arms on the Common Shaft (one set per tray)', 'rotating_element', rk, explode=(0, -0.9, 0.3), ref='pl_rakes', section='keep')
    prk.spin('Z', 0.25)
    br = [box('br', (2 * R + 0.5, 0.35, 0.12), (0, 0, Z0 + H + 0.25), 'paint_yellow'), box('dh', (0.5, 0.5, 0.35), (0, 0, Z0 + H + 0.48), 'paint_blue'), cyl('mt', 0.1, Z0 + H + 0.65, Z0 + H + 0.95, 'paint_motor', 24, center=(0.15, 0, 0))]
    P(m, 'drive', 'Bridge & Rake Drive', 'drive', br, explode=(0, 0, 0.7), ref='pl_drive', section='keep')
    fp = [hollow_pipe(f'fd{k}', [(-R - 0.6, 0.3, z + 0.35), (-0.25, 0.3, z + 0.35)], 0.03, 'paint_grey', 12) for k, z in enumerate(zs)] + [nozzle('uf', (0, 0, Z0 - 0.4), (0, 0, -1), 0.05, 0.25)]
    fp += [hollow_pipe(f'of{k}', [(0.6, -0.3, z + 0.45), (R + 0.3, -0.3, z + 0.45), (R + 0.3, -0.3, Z0 + H - 0.1)], 0.025, 'stainless', 12, bend=0.04) for k, z in enumerate(zs[:2])]
    P(m, 'feed_overflow', 'Feed Pipes to each Tray, Intermediate Overflows & Underflow', 'piping', fp, explode=(0, 0, 0.3), ref='pl_piping', section='keep')
    P(m, 'supports', 'Support Legs', 'structure', legs('lg', R, 0.0, Z0, n=4), explode=(0, 0, -0.3), ref='pl_tank', section='keep')
    particles_path(m, 'settling', 'Fine Solids settling onto the Trays', lambda i, s: (-0.8 + 1.6 * ((i * 0.37) % 1), 0.1 + 0.5 * ((i * 0.53) % 1), zs[i % 3] + 0.5 - 0.42 * s), 15, mat='red_mud', r=0.015)
    for k, z in enumerate(zs):
        m.flow(f'feed_tray_{k + 1}', [(-R - 0.7, 0.3, z + 0.35), (-0.3, 0.3, z + 0.35), (-0.5, 0.1, z + 0.3)], 'flow_discharge', 0.012, 0.2)
    m.flow('clear_liquor', [(0.6, 0.1, Z0 + H - 0.4), (R - 0.05, 0.1, Z0 + H - 0.15), (R + 0.3, 0, Z0 + H - 0.3)], 'water', 0.015, 0.2)
    m.flow('mud', [(0, 0.05, zs[2]), (0, 0.05, Z0 - 0.3), (0, 0, Z0 - 0.7)], 'sand', 0.015, 0.3)
    _press(m, [cyl(f'az{k}', R + 0.05, z - 0.05, z + 0.35, 'pressure_6', 96, r_in=R + 0.03) for k, z in enumerate(zs)], 'More settling area in the same footprint',
           'Settling capacity depends on area, not depth. Stacking several trays, each with its own feed, overflow and rake, multiplies the effective settling area in one tank. Fine suspended solids in the '
           'process liquor settle on the trays and are raked to the central downcomers; the clarified liquor overflows.')
    return m.export(out)


# =============================================================== EQ-295 Alumina dust collection system (ESP)
def alumina_dust_collection_system(out):
    m = _model('alumina_dust_collection_system', 'Alumina Dust Collection — Electrostatic Precipitator (Calciner Off-Gas)')
    X0, X1, W, Z0, H = -1.2, 1.2, 1.2, 1.4, 1.6
    cs = csg('cs', [box('cso', (X1 - X0 + 0.08, W + 0.08, H + 0.08), (0, 0, Z0 + H / 2), 'paint_grey')], [box('csi', (X1 - X0 + 0.2, W, H), (0, 0, Z0 + H / 2), 'paint_grey')], 'paint_grey')
    tri = lathe('tin', [(0.25, X0 - 0.9), (0.27, X0 - 0.9), (W * 0.75, X0), (W * 0.73, X0), (0.25, X0 - 0.88)], 'paint_grey', 4, a0=math.pi / 4, a1=math.pi / 4 + TAU, axis='X', center=(0, 0, Z0 + H / 2))
    tro = lathe('tout', [(0.25, X1 + 0.9), (0.27, X1 + 0.9), (W * 0.75, X1), (W * 0.73, X1), (0.25, X1 + 0.88)], 'paint_grey', 4, a0=math.pi / 4, a1=math.pi / 4 + TAU, axis='X', center=(0, 0, Z0 + H / 2))
    hp = [lathe(f'hp{k}', [(0.1, Z0 - 0.9), (0.12, Z0 - 0.9), (W * 0.7, Z0), (W * 0.68, Z0), (0.1, Z0 - 0.88)], 'paint_grey', 4, a0=math.pi / 4, a1=math.pi / 4 + TAU, center=(x, 0, 0)) for k, x in enumerate((-0.6, 0.6))]
    P(m, 'casing', 'Casing, Inlet/Outlet Transitions (with gas distribution) & Dust Hoppers', 'casing', [cs, tri, tro] + hp, explode=(0, 0.8, 0), ref='ep_casing')
    pl = [box(f'pl{k}', (X1 - X0 - 0.3, 0.01, H - 0.2), (0, -W / 2 + 0.1 + 0.15 * k, Z0 + H / 2), 'steel') for k in range(7)]
    P(m, 'collecting_plates', 'Collecting Electrodes (earthed plates)', 'electrodes', pl, explode=(0, -0.8, 0), ref='ep_plates', section='split')
    el = []
    for k in range(6):
        y = -W / 2 + 0.175 + 0.15 * k
        el += [cyl(f'de{k}_{j}', 0.006, Z0 + 0.15, Z0 + H - 0.1, 'steel_dark', 6, center=(x, y, 0)) for j, x in enumerate((-0.8, -0.4, 0.0, 0.4, 0.8))]
    el += [box('hf', (X1 - X0 - 0.3, W - 0.2, 0.04), (0, 0, Z0 + H - 0.08), 'steel_dark')]
    P(m, 'discharge_electrodes', 'Discharge Electrodes (high-voltage, negative corona) on Support Frame', 'electrodes', el, explode=(0, -0.5, 0.5), ref='ep_electrodes', section='keep')
    rp = [cyl('rs', 0.03, -W / 2 - 0.1, W / 2 + 0.1, 'steel', 12, axis='Y', center=(X1 - 0.1, 0, Z0 + 0.1))] + [rotate(box(f'rh{k}', (0.12, 0.04, 0.04), (X1 - 0.1 + 0.06, -W / 2 + 0.15 + 0.15 * k, Z0 + 0.1), 'steel'), 0, 'Y') for k in range(7)]
    prp = P(m, 'rappers', 'Tumbling-Hammer Rappers (knock dust off the plates)', 'cleaning', rp, explode=(0.4, -0.4, 0), ref='ep_rappers', section='keep', pivot=(X1 - 0.1, 0, Z0 + 0.1))
    prp.spin('Y', 1)
    tr = join('tr', [box('trb', (0.6, 0.5, 0.45), (0, 0, Z0 + H + 0.3), 'paint_grey'), box('trc', (0.2, 0.3, 0.3), (0.45, 0, Z0 + H + 0.2), 'paint_blue_dark'), cyl('bs', 0.04, Z0 + H, Z0 + H + 0.1, 'ptfe', 12)])
    P(m, 'tr_set', 'Transformer-Rectifier Set & HV Bushing (~ 40–100 kV DC)', 'electrical', tr, explode=(0, 0, 0.6), ref='ep_tr', section='keep')
    P(m, 'dust_valves', 'Hopper Rotary Valves (dust returned to product)', 'valves', [box(f'rv{k}', (0.15, 0.15, 0.15), (x, 0, Z0 - 0.98), 'cast_iron') for k, x in enumerate((-0.6, 0.6))], explode=(0, 0, -0.3), ref='ep_casing', section='keep')
    P(m, 'supports', 'Support Structure', 'structure', [box(f'sl{k}', (0.12, 0.12, Z0), (sx * 1.0, sy * 0.55, Z0 / 2), 'paint_grey') for k, (sx, sy) in enumerate(((-1, -1), (-1, 1), (1, -1), (1, 1)))], explode=(0, 0, -0.3), ref='ep_casing', section='keep')
    def drift(i, s):
        y0 = -W / 2 + 0.175 + 0.15 * (i % 6)
        x = X0 - 0.6 + (X1 - X0 + 0.6) * s
        side = 0.075 if (i % 2) else -0.075
        y = y0 + side * min(1.0, max(0.0, (x - X0) / 1.0))
        return (x, y, Z0 + 0.4 + 0.12 * (i % 8))
    particles_path(m, 'dust', 'Charged Dust Particles drifting to the Plates', drift, 14, mat='powder', r=0.012)
    droplets(m, 'falling_dust', 'Dust released by Rapping, falling into the Hoppers', -0.9, 0.9, Z0 + 0.1, Z0 - 0.7, n=8, mat='powder', y=0.2, r=0.015)
    m.flow('gas', [(X0 - 1.2, 0, Z0 + H / 2), (X1 + 1.2, 0, Z0 + H / 2)], 'flue_gas', 0.04, 0.4)
    m.flow('hv_power', [(0.3, 0, Z0 + H + 0.3), (0, 0, Z0 + H + 0.05), (0, 0, Z0 + H - 0.1)], 'electric', 0.015, 0.2)
    _press(m, [box('fz', (X1 - X0 - 0.3, 0.02, H - 0.2), (0, W / 2 - 0.1, Z0 + H / 2), 'pressure_8')], 'Corona charging and collection',
           'A high negative DC voltage on the discharge wires ionises the gas (corona). Dust particles pick up charge and drift to the earthed plates, where they collect. Periodic rapping drops the dust layer into '
           'the hoppers. ESPs reach very high efficiencies (typically > 99.5 %); dust resistivity, gas temperature and flow distribution govern performance. Recovered alumina is returned to product.')
    return m.export(out)


# ===================================================================== metadata
def _std(*items):
    return [{'id': i, 'title': t, 'relevance': r, 'edition': 'to be verified'} for i, t, r in items]


def _c(fn, cons, mat, op='—', fm=('—',), insp=('Visual',)):
    return C(fn, cons, mat, op, list(fm), list(insp))


_REF = ['TMS Light Metals proceedings — Bayer process practice', 'Hind, Bhargava & Grocott — The surface chemistry of Bayer process solids']
_PVS = _std(('ASME BPVC VIII-1', 'Pressure vessels', 'Pressure parts.'), ('API 650', 'Welded storage tanks', 'Atmospheric tanks (practice; to be verified for caustic service).'))

META = {
    'sand_separator': {'summary': ('A sand separator removes coarse sand from the red mud slurry. In an inclined screw classifier the sand settles in a pool and is raked up the incline by a slowly turning screw, draining as it goes, while fine mud overflows to the washers.'),
                       'classification': {'family': 'Residue separation', 'type': 'Inclined screw (spiral) classifier'}, 'model_configuration': {'animation': 'Screw turns; sand raked up'},
                       'standards': _std(('Maker standards', 'Classifier design', 'Sizing by sand load and overflow area.'),), 'references': _REF,
                       'components': {'ss_trough': _c('Settling pool and incline.', 'Trough, tank, weir.', 'Steel (wear-lined).'), 'ss_screw': _c('Rakes sand up.', 'Spiral screw on shaft.', 'Steel with wear shoes.', '—', ['Flight wear'], ['Inspect']),
                                      'ss_drive': _c('Turns screw; discharges sand.', 'Gearmotor, chute.', '—')}},
    'alumina_hydrate_filter': {'summary': ('A rotary vacuum drum filter separates alumina hydrate from liquor. The drum turns partly submerged in slurry; vacuum draws liquor through the cloth so a cake forms, is washed and dewatered, and is scraped off with air blow-back.'),
                               'classification': {'family': 'Filtration', 'type': 'Rotary vacuum drum filter'}, 'model_configuration': {'animation': 'Drum sectors turn; cake on drum'},
                               'standards': _std(('Maker standards', 'Vacuum filter design', 'Filter area by filtration rate.'),), 'references': _REF,
                               'components': {'hf_trough': _c('Holds slurry.', 'Trough.', 'Steel.'), 'hf_drum': _c('Carries cloth; filtrate pipes.', 'Drum and sectors.', 'Steel/PP cloth.', '—', ['Cloth blinding'], ['Inspect']),
                                              'hf_cake': _c('Hydrate cake.', '—', '—'), 'hf_scraper': _c('Discharges cake.', 'Scraper and chute.', 'Steel.'), 'hf_wash': _c('Wash cake.', 'Spray header.', 'Stainless.'),
                                              'hf_valve': _c('Switches vacuum/blow per sector.', 'Automatic valve, receiver.', 'Steel.', '—', ['Wear plate leakage'], ['Inspect']), 'hf_drive': _c('Drive and agitator.', 'Gearmotor, agitator.', '—')}},
    'hydrate_washing_system': {'summary': ('A horizontal vacuum belt filter dewaters and washes hydrate with hot condensate in counter-current stages. The belt moves over vacuum boxes; wash liquor from each later zone is used in the zone before, lowering soda in the cake with little water.'),
                               'classification': {'family': 'Filtration / washing', 'type': 'Horizontal vacuum belt filter'}, 'model_configuration': {'animation': 'Belt moves; sprays'},
                               'standards': _std(('Maker standards', 'Belt filter design', 'Area by cake formation and wash time.'),), 'references': _REF,
                               'components': {'hk_belt': _c('Filter belt.', 'Drainage belt with cloth.', 'Rubber/PP.'), 'hk_pulley': _c('Drive/tail rolls.', '—', 'Steel.'), 'hk_idlers': _c('Frame.', '—', 'Steel.'),
                                              'hw_vacuum': _c('Vacuum boxes and receivers.', 'Boxes, receivers.', 'Steel.'), 'hw_wash': _c('Feed and washes.', 'Feed box, spray headers.', 'Stainless.'), 'hw_cake': _c('Cake and discharge.', '—', '—')}},
    'calcination_fluidized_bed_cooler': {'summary': ('A fluidised bed cooler cools hot calcined alumina. The alumina flows through a cascade of fluidised chambers containing water-cooled tube bundles; fluidising air keeps the bed moving and is warmed for reuse as combustion air.'),
                                         'classification': {'family': 'Calcination', 'type': 'Fluidised bed cooler with immersed bundles'}, 'model_configuration': {'chambers': 3, 'animation': 'Bed flows chamber to chamber'},
                                         'standards': _std(('Maker standards', 'Fluid bed cooler design', 'Heat transfer surface.'),), 'references': ['Outotec/FLSmidth calciner literature'],
                                         'components': {'fbc_body': _c('Contains the bed.', 'Body, distributor, weirs.', 'Steel.'), 'fbc_tubes': _c('Remove heat.', 'Water-cooled bundles.', 'Steel.', '—', ['Erosion, leaks'], ['Thickness']),
                                                        'fbc_air': _c('Fluidising air.', 'Plenum, duct.', 'Steel.'), 'fbc_nozzles': _c('Connections.', 'Inlet, outlet, water lines.', 'Steel.')}},
    'alumina_cooler': {'summary': ('A rotary alumina cooler is a slowly rotating drum whose outside is sprayed with water. Hot alumina tumbles inside and is cooled through the shell without ever touching the water.'),
                       'classification': {'family': 'Cooling', 'type': 'Indirect rotary drum cooler'}, 'model_configuration': {'animation': 'Tyres turn; alumina tumbles; sprays'},
                       'standards': _std(('Maker standards', 'Rotary cooler design', 'Shell and drive.'),), 'references': ['Process cooler literature'],
                       'components': {'ac_shell': _c('Cooling drum.', 'Shell with lifters.', 'Steel.'), 'ac_drive': _c('Rotation.', 'Tyres, gear, rollers, motor.', 'Steel.'), 'ac_spray': _c('External cooling.', 'Spray header and pan.', 'Stainless.'),
                                      'ac_hoods': _c('Feed and discharge.', 'Hoods.', 'Steel.')}},
    'alumina_storage_silo': {'summary': ('An alumina storage silo holds finished smelter-grade alumina. An aerated floor fluidises the alumina so it flows to the discharge; a bin-vent filter on the roof vents air during filling, and trucks or rail cars are loaded beneath.'),
                             'classification': {'family': 'Storage', 'type': 'Aerated-floor concrete/steel silo'}, 'model_configuration': {'animation': 'Level changes; loading'},
                             'standards': _std(('EN 1991-4', 'Actions on silos and tanks', 'Structural loads.'),), 'references': ['Bulk solids storage design (Jenike)'],
                             'components': {'as_shell': _c('Holds product.', 'Shell, roof, skirt.', 'Steel/concrete.'), 'as_aeration': _c('Fluidise and discharge.', 'Air-slide pads, gate, spout.', 'Fabric/steel.', '—', ['Pad blinding'], ['ΔP check']),
                                            'as_product': _c('Stored alumina.', '—', '—'), 'as_roof': _c('Venting, level, fill.', 'Bin-vent filter, radar, relief.', '—')}},
    'alumina_pneumatic_conveying_system': {'summary': ('A dense-phase system conveys alumina in batches. A blow tank is filled through a dome valve, sealed and pressurised; the alumina is pushed through the pipeline as slow-moving plugs to the receiving silo. Low velocity limits attrition and wear.'),
                                           'classification': {'family': 'Material handling', 'type': 'Dense-phase blow-tank conveying'}, 'model_configuration': {'animation': 'Fill → pressurise → convey cycle'},
                                           'standards': _std(('ASME BPVC VIII-1', 'Pressure vessels', 'Blow tank.'),), 'references': ['Mills — Pneumatic Conveying Design Guide'],
                                           'components': {'pc_blowtank': _c('Pressurised batch vessel.', 'Blow tank.', 'Steel.'), 'pc_hopper': _c('Feeds blow tank.', 'Hopper.', 'Steel.'), 'pc_valves': _c('Seals inlet.', 'Dome valve.', '—', '—', ['Seal wear'], ['Leak test']),
                                                          'pc_line': _c('Conveys plugs.', 'Pipeline, boosters, outlet valve.', 'Steel.'), 'pc_silo': _c('Receives alumina.', 'Silo.', 'Steel.')}},
    'causticization_tank': {'summary': ('A causticization reactor regenerates caustic soda from sodium carbonate in the liquor by reaction with slaked lime. Calcium carbonate precipitates and is separated; the recovered caustic returns to the process.'),
                            'classification': {'family': 'Caustic recovery', 'type': 'Agitated reactor with lime slaker'}, 'model_configuration': {'animation': 'Agitator and slaker turn; CaCO₃ forms'},
                            'standards': _PVS, 'references': _REF,
                            'components': {**_agt_comp('ct'), 'ct_slaker': _c('Prepares lime milk.', 'Slaker, paddles, lime silo.', 'Steel.'), 'ct_piping': _c('Feeds and outlet.', 'Pipes.', 'Steel.')}},
    'oxalate_removal_system': {'summary': ('An oxalate removal system takes a side-stream of liquor, cools and seeds it so sodium oxalate crystallises in a controlled way, and separates the crystals in hydrocyclones. Clean liquor returns; part of the crystals is recycled as seed.'),
                               'classification': {'family': 'Liquor treatment', 'type': 'Seeded oxalate crystallization'}, 'model_configuration': {'animation': 'Crystals grow; cyclone separates'},
                               'standards': _PVS, 'references': _REF,
                               'components': {**_agt_comp('ox'), 'ox_cooling': _c('Cools liquor.', 'Jacket.', 'Steel.'), 'ox_cyclone': _c('Separates crystals; piping; pump.', 'Hydrocyclone, lines, pump.', 'Lined steel.')}},
    'sodium_oxalate_filter': {'summary': ('A horizontal pressure-leaf filter separates sodium oxalate crystals from liquor. Slurry is pumped into the closed shell; cake forms on vertical mesh leaves while filtrate leaves through the manifold. The shell then rolls back and the cake is sluiced off.'),
                              'classification': {'family': 'Filtration', 'type': 'Horizontal pressure-leaf filter'}, 'model_configuration': {'animation': 'Filtering, then shell opens'},
                              'standards': _PVS, 'references': ['Pressure leaf filter maker data'],
                              'components': {'of_shell': _c('Pressure envelope; retracts.', 'Shell on rails.', 'Steel.'), 'of_head': _c('Fixed head, manifold.', 'Head and stand.', 'Steel.'), 'of_leaves': _c('Filter surfaces.', 'Mesh leaves.', 'Stainless.', '—', ['Mesh damage'], ['Inspect']),
                                             'of_sluice': _c('Cake removal.', 'Sluice header.', 'Stainless.')}},
    'process_liquor_clarifier': {'summary': ('A multi-tray clarifier stacks several conical settling trays in one tank, each with its own feed, overflow and rake. This multiplies settling area to remove fine solids from process liquor in a small footprint.'),
                                 'classification': {'family': 'Liquor treatment', 'type': 'Multi-tray (stacked) clarifier'}, 'model_configuration': {'trays': 3, 'animation': 'Rakes turn; solids settle'},
                                 'standards': _PVS, 'references': _REF,
                                 'components': {'pl_tank': _c('Holds liquor.', 'Tank with launder.', 'Steel.'), 'pl_trays': _c('Settling surfaces.', 'Conical trays, downcomers.', 'Steel.'), 'pl_rakes': _c('Move solids to downcomers.', 'Rakes on common shaft.', 'Steel.'),
                                                'pl_drive': _c('Turns rakes.', 'Bridge drive.', '—'), 'pl_piping': _c('Feeds/overflows/underflow.', 'Pipes.', 'Steel.')}},
    'alumina_dust_collection_system': {'summary': ('An electrostatic precipitator removes alumina dust from calciner off-gas. High-voltage discharge electrodes charge the dust, which collects on earthed plates; rappers knock it into hoppers and it is returned to product.'),
                                       'classification': {'family': 'Environmental', 'type': 'Dry electrostatic precipitator'}, 'model_configuration': {'animation': 'Dust drifts to plates; rappers turn'},
                                       'standards': _std(('Industrial Emissions Directive / local permits', 'Dust emission limits', 'Compliance.'),), 'references': ['White — Industrial Electrostatic Precipitation'],
                                       'components': {'ep_casing': _c('Gas path and hoppers.', 'Casing, transitions, hoppers, valves.', 'Steel.'), 'ep_plates': _c('Collect dust.', 'Earthed plates.', 'Steel.'),
                                                      'ep_electrodes': _c('Produce corona.', 'Discharge electrodes.', 'Steel.', '—', ['Breakage, shorting'], ['Spark rate']), 'ep_rappers': _c('Clean plates.', 'Tumbling hammers.', 'Steel.'),
                                                      'ep_tr': _c('High-voltage supply.', 'T/R set.', '—', 'HV hazard.', ['Insulator tracking'], ['Inspect'])}},
}
BUILDERS = {k: globals()[k] for k in META}
