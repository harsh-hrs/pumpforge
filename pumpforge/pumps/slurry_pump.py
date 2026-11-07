"""
Slurry Pump — heavy-duty horizontal end-suction centrifugal pump with
replaceable hard-metal liners (volute liner, throatbush), closed impeller with
pump-out (expelling) vanes, expeller + gland packing shaft seal, cartridge
bearing assembly on a pedestal base, and overhead motor with V-belt drive.
Shaft along +X (suction at -X), cut plane y = 0.
"""
import math
from pumpforge.core import (Model, lathe, lathe_split, ring_profile, cyl, box, csg, split, join, split_faces, split_many,
                            merge_halves, rotate, hex_prism, TAU)
from pumpforge.parts import (H_FRAME, place, radial_impeller, volute_casing, add_impeller, nozzle_bolts, ball_bearing,
                             add_motor_h)
from pumpforge.shapes import sweep_tube

ID = 'slurry_pump'
CZ = 0.42
BASE = 0.0


def build(out_dir):
    m = Model(ID, 'Slurry Pump (Hard-Metal Lined, V-Belt Driven)', 'A · Centrifugal & Special Hydraulic Pumps', META)
    Mx = H_FRAME(0.0, CZ)
    core, shroud, imp = radial_impeller('impeller', 0.36, 0.05, 0.065, 0.03, n_blades=5, mat='ductile_iron', wrap=1.3,
                                        t=0.016, expeller=True)
    # liner (hard metal) and outer casing (ductile iron) share the hydraulic cavity
    liner, geo = volute_casing('liner', imp, 'ductile_iron', r_suc=0.065, L_suc=0.16, r_dis=0.055, H_dis=0.30, t=0.018,
                               flange=False)
    outer, geo2 = volute_casing('outer', imp, 'paint_red', r_suc=0.065, L_suc=0.16, r_dis=0.055, H_dis=0.30, t=0.042)
    for o in (liner, outer):
        place(o, Mx)
    liner_cut = liner.copy(); liner_cut.data = liner.data.copy(); m_link(liner_cut)
    # fill the liner's own cavity in the cutter so subtracting it leaves only the space it occupies
    zb = geo2['z_back']
    foot = box('pfoot', (0.24, 0.5, CZ - geo2['r3'] - 0.08 - BASE), (zb - 0.1, 0, BASE + (CZ - geo2['r3'] - 0.08) / 2 + 0.004),
               'paint_red', bevel=0.006)
    outer = csg('casing', [outer, foot], [liner_cut], 'paint_red')
    ob, of = split(outer)
    bolts = [nozzle_bolts('sfb', 8, 2 * (geo2['r_suc'] + 0.045), 0.026, -geo2['L_suc'], -geo2['L_suc'] - 0.018, 'X',
                          (0, 0, CZ), phase=math.pi / 8),
             nozzle_bolts('dfb', 8, 2 * (geo2['r_dis'] + 0.045), 0.026, CZ + geo2['H_dis'], CZ + geo2['H_dis'] + 0.018, 'Z',
                          (imp['zc'], geo2['Rend'], 0), phase=math.pi / 8),
             nozzle_bolts('cfb', 12, 2 * (geo2['r3'] + 0.07), 0.03, zb + 0.004, zb + 0.026, 'X', (0, 0, CZ), phase=math.pi / 12)]
    bb, bf = split_faces(join('bolts', bolts), 'y', 0.0)
    p = m.part('casing', 'Outer Casing (Cover & Frame Plates)', 'casing', section='split', explode=(-0.6, 0, 0))
    p.add_split(join('cb', [ob, bb]), join('cf', [of, bf]), smooth_angle=40)
    p = m.part('volute_liner', 'Volute Liner & Throatbush (Hard Metal)', 'casing', section='split', explode=(-0.4, 0, 0))
    p.add_split(*split(liner), smooth_angle=40)
    add_impeller(m, 'impeller', 'Closed Impeller with Pump-Out Vanes', core, shroud, Mx, (0, 0, CZ),
                 explode=(-0.22, 0, 0), ref='impeller_slurry')

    wear_overlay(m, Mx, imp, geo)
    # frame-plate liner insert / stuffing box
    xs = imp['z_back'] + 0.004
    fpl = lathe('fpl', [(0.06, zb - 0.03), (geo2['r_back'], zb - 0.03), (geo2['r_back'], zb + 0.01), (0.12, zb + 0.03),
                        (0.12, xs + 0.13), (0.06, xs + 0.13), (0.06, xs + 0.03), (0.05, xs + 0.02)], 'ductile_iron', 96,
                axis='X', center=(0, 0, CZ))
    p = m.part('frame_plate_liner', 'Frame-Plate Liner Insert & Stuffing Box', 'casing', section='split', explode=(-0.05, 0, 0.0))
    p.add_split(*split(fpl), smooth_angle=40)
    # expeller (dynamic seal while running) — spins
    ex = [lathe('exd', [(0.034, xs + 0.012), (0.105, xs + 0.012), (0.105, xs + 0.024), (0.034, xs + 0.024)], 'ductile_iron', 96,
                axis='X', center=(0, 0, CZ))]
    for i in range(8):
        b = box(f'exv{i}', (0.012, 0.006, 0.06), (xs + 0.006, 0, CZ + 0.07), 'ductile_iron')
        ex.append(rotate(b, TAU * (i + 0.5) / 8, 'X', (0, 0, CZ)))
    exb, exf = split_many('expeller', ex)
    p = m.part('expeller', 'Expeller (Dynamic Seal)', 'rotating_element', pivot=(xs, 0, CZ), explode=(-0.05, -0.45, 0))
    p.add(exb, 'back'); p.add(exf, 'front'); p.spin('X', 2)
    # gland packing
    pk = [lathe_split(f'pk{i}', ring_profile(0.036, 0.059, xs + 0.06 + i * 0.012, xs + 0.07 + i * 0.012), 'ptfe' if i != 1 else 'brass',
                      48, axis='X', center=(0, 0, CZ)) for i in range(4)]
    pk.append(lathe_split('gland', [(0.036, xs + 0.112), (0.059, xs + 0.112), (0.059, xs + 0.13), (0.1, xs + 0.13),
                                    (0.1, xs + 0.145), (0.036, xs + 0.145)], 'steel', 64, axis='X', center=(0, 0, CZ)))
    p = m.part('gland_packing', 'Gland Packing, Lantern Ring & Gland Follower', 'shaft_seal', section='split',
               explode=(0.15, -0.3, 0))
    p.add_split(*merge_halves('packing', pk))
    # bearing assembly (cartridge) and pedestal base
    xb0, xb1 = xs + 0.2, xs + 0.72
    bh = lathe('bh', [(0.06, xb0), (0.13, xb0), (0.13, xb0 + 0.04), (0.11, xb0 + 0.06), (0.11, xb1 - 0.06), (0.13, xb1 - 0.04),
                      (0.13, xb1), (0.06, xb1)], 'paint_red', 96, axis='X', center=(0, 0, CZ))
    p = m.part('bearing_housing', 'Bearing Cartridge Housing', 'bearing_housing', section='split', explode=(0.25, 0, 0.0),
               info={'ref': 'bearing_frame'})
    p.add_split(*split(bh), smooth_angle=40)
    brg = merge_halves('brgs', [ball_bearing('b1', 0.036, 0.085, xb0 + 0.01, xb0 + 0.06, 12, center=(0, 0, CZ)),
                                ball_bearing('b2', 0.036, 0.085, xb1 - 0.06, xb1 - 0.01, 12, center=(0, 0, CZ))])
    p = m.part('bearings', 'Roller Bearings (Wet End & Drive End)', 'bearings', section='split', explode=(0.25, -0.35, 0),
               info={'ref': 'radial_bearing'})
    p.add_split(*brg)
    ped = csg('pedestal', [box('pb', (xb1 - zb + 0.25, 0.62, 0.05), ((zb + xb1) / 2 + 0.08, 0, BASE + 0.025), 'paint_red', bevel=0.006),
                           box('pw', (xb1 - xb0 + 0.06, 0.3, CZ - 0.12 - BASE), ((xb0 + xb1) / 2, 0, BASE + (CZ - 0.12) / 2 + 0.02), 'paint_red', bevel=0.006),
                           box('pc', (xb1 - xb0 + 0.06, 0.32, 0.06), ((xb0 + xb1) / 2, 0, CZ - 0.1), 'paint_red', bevel=0.006)],
              [cyl('pci', 0.128, xb0 - 0.05, xb1 + 0.05, 'paint_red', 96, axis='X', center=(0, 0, CZ))], 'paint_red')
    pb_, pf_ = split(ped)
    p = m.part('pedestal_base', 'Pedestal Base (with Bearing Adjustment)', 'baseplate', section='split', explode=(0.25, 0, -0.35),
               info={'ref': 'baseplate'})
    p.add_split(pb_, pf_, smooth_angle=40)
    # shaft + sheave
    xsh = xb1 + 0.12
    sh = [cyl('shaft', 0.036, imp['z_back'] - 0.02, xsh + 0.06, 'steel', 40, axis='X', center=(0, 0, CZ), ch=0.003),
          cyl('sleeve', 0.0395, xs + 0.03, xs + 0.15, 'stainless', 40, axis='X', center=(0, 0, CZ))]
    p = m.part('shaft', 'Shaft & Shaft Sleeve', 'rotating_element', pivot=(xs, 0, CZ), explode=(0.25, -0.6, 0), info={'ref': 'pump_shaft'})
    p.add(join('shaft', sh)); p.spin('X', 2)

    def sheave(name, r, x0, cz, grooves=3):
        prof = [(0.03, x0), (r, x0)]
        w = 0.022
        for g in range(grooves):
            a = x0 + 0.008 + g * w
            prof += [(r, a), (r - 0.012, a + w * 0.35), (r - 0.012, a + w * 0.65), (r, a + w)]
        prof += [(r, x0 + 0.016 + grooves * w), (0.03, x0 + 0.016 + grooves * w)]
        return lathe(name, prof, 'cast_iron', 96, axis='X', center=(0, 0, cz)), x0 + 0.008 + grooves * w / 2 + 0.004
    r_ps, r_ms = 0.15, 0.085
    ps, xmid = sheave('pump_sheave', r_ps, xsh - 0.04, CZ)
    p = m.part('pump_sheave', 'Pump Sheave (V-Belt Pulley)', 'power_transmission', pivot=(xsh, 0, CZ), explode=(0.6, 0, 0))
    p.add(ps, smooth_angle=50); p.spin('X', 2)
    CZm = CZ + 0.62
    ms, _ = sheave('motor_sheave', r_ms, xsh - 0.04, CZm)
    p = m.part('motor_sheave', 'Motor Sheave', 'power_transmission', pivot=(xsh, 0, CZm), explode=(0.6, 0, 0.1))
    p.add(ms, smooth_angle=50); p.spin('X', 2 * r_ps / r_ms)
    belts = []
    for g in range(3):
        xg = xsh - 0.04 + 0.008 + g * 0.022 + 0.011
        pts = []
        d = CZm - CZ
        ang = math.asin((r_ps - r_ms) / d)
        for i in range(25):
            a = -math.pi / 2 - ang + (math.pi + 2 * ang) * i / 24
            pts.append((xg, (r_ps - 0.006) * math.cos(a + math.pi), CZ + (r_ps - 0.006) * math.sin(a)))
        for i in range(25):
            a = math.pi / 2 + ang - (math.pi - 2 * ang) * i / 24
            a2 = math.pi / 2 - ang + (math.pi - 2 * ang) * i / 24
            pts.append((xg, -(r_ms - 0.006) * math.cos(a2), CZm + (r_ms - 0.006) * math.sin(a2)))
        pts.append(pts[0])
        belts.append(sweep_tube(f'belt{g}', pts, 0.0065, 'rubber', 10, cap=False))
    p = m.part('v_belts', 'V-Belts', 'power_transmission', explode=(0.75, 0, 0.05))
    p.add(join('v_belts', belts), smooth_angle=70)
    gd = box('belt_guard', (0.1, 0.42, CZm - CZ + 0.36), (xsh - 0.04 + 0.04, 0, (CZ + CZm) / 2), 'paint_yellow', bevel=0.03)
    gdi = box('belt_guard_i', (0.08, 0.4, CZm - CZ + 0.34), (xsh - 0.04 + 0.04, 0, (CZ + CZm) / 2), 'paint_yellow', bevel=0.02)
    g_ = csg('belt_guard', [gd], [gdi], 'paint_yellow')
    p = m.part('belt_guard', 'Belt Guard', 'power_transmission', section='hide', explode=(0.95, 0, 0), info={'ref': 'coupling_guard'})
    p.add(g_, smooth_angle=40)
    # overhead motor mount + motor (drive end toward -X? sheave at the +X... motor faces -X: put motor body toward -X)
    mount = box('mmount', (0.62, 0.42, 0.03), (xb0 + 0.05, 0, CZ + 0.27), 'paint_red', bevel=0.004)
    posts = [box(f'mp{i}', (0.05, 0.05, 0.16), (xb0 + 0.05 + sx * 0.25, sy * 0.17, CZ + 0.18), 'paint_red')
             for i, (sx, sy) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1)))]
    mb_, mf_ = split_many('motor_mount', [mount] + posts)
    p = m.part('motor_mount', 'Overhead Motor Mount', 'baseplate', section='split', explode=(0.25, 0, 0.3))
    p.add(mb_, 'back'); p.add(mf_, 'front')
    # motor drive end faces +X toward sheave: build at x and mirror by placing body on -X side
    import mathutils
    before = set(o.name for o in __import__('bpy').data.objects)
    mo = add_motor_h(m, 'm_', xsh - 0.04 - 0.5 - 0.0, CZm, 0.15, 0.48, CZ + 0.285, 0.03, 0.1, explode_dx=0.0, revs=2 * r_ps / r_ms)
    # mirror motor about its own centre so the shaft points +X toward the sheave
    xm_c = xsh - 0.04 - 0.5 + 0.24
    Mm = mathutils.Matrix.Translation((2 * xm_c, 0, 0)) @ mathutils.Matrix.Scale(-1, 4, (1, 0, 0))
    from pumpforge.core import recalc_normals
    for pp in m.parts:
        if pp.id.startswith('m_'):
            pp.node.location.x = 2 * xm_c - pp.node.location.x
            pp.pivot.x = pp.node.location.x
            pp.explode.z += 0.5
            pp.node['explode_offset'] = [pp.explode.x, pp.explode.z, -pp.explode.y]
            for mesh in pp.meshes:
                mesh.data.transform(mathutils.Matrix.Scale(-1, 4, (1, 0, 0)))
                recalc_normals(mesh)
                from pumpforge.core import smooth
                smooth(mesh, 40)
    zc = imp['zc']
    from pumpforge.parts import volute_flow
    suc, dis = volute_flow(imp, geo, Mx, 0.35)
    m.flow('flow_suction', suc, 'flow_suction', 0.01, 0.15)
    m.flow('flow_discharge', dis, 'flow_discharge', 0.01, 0.15)
    return m.export(out_dir)


def m_link(o):
    import bpy
    bpy.context.scene.collection.objects.link(o)


def wear_overlay(m, Mx, imp, geo):
    """Typical slurry-pump wear zones (colour = relative severity), shown on the wetted surfaces."""
    from mathutils import Vector
    W = lambda p: tuple(Mx @ Vector(p))
    r2, zf, b2, re, nk, t = imp['r2'], imp['zf'], imp['b2'], imp['r_eye'], imp['neck'], imp['t']
    r3, zc = geo['r3'], geo['zc']
    sev = [lathe('w_throat', [(re + t + 0.003, -nk - 0.008), (r2 * 0.85, -t - 0.016), (r2 * 0.85, -t - 0.004), (re + t + 0.003, -nk + 0.003)], 'wear_severe', 96),
           lathe('w_eye', [(re - 0.012, -0.03), (re - 0.002, -0.03), (re - 0.002, zf + 0.006), (re - 0.012, zf + 0.006)], 'wear_severe', 96)]
    th = 0.45
    cw = sweep_tube('w_cutwater', [((r3 + 0.004) * math.cos(th - 0.25), (r3 + 0.004) * math.sin(th - 0.25), zc),
                                   ((r3 + 0.004) * math.cos(th + 0.12), (r3 + 0.004) * math.sin(th + 0.12), zc)], b2 * 0.55, 'wear_severe', 16)
    sev.append(cw)
    mod = [lathe('w_tip', [(r3 - 0.002, zf - 0.008), (r3 + 0.004, zf - 0.008), (r3 + 0.004, zf + b2 + 0.008), (r3 - 0.002, zf + b2 + 0.008)], 'wear_moderate', 96),
           lathe('w_vane', [(r2 - 0.012, zf + 0.004), (r2 + 0.001, zf + 0.004), (r2 + 0.001, zf + b2 - 0.004), (r2 - 0.012, zf + b2 - 0.004)], 'wear_moderate', 96)]
    lig = [lathe('w_back', [(0.07, zf + b2 + t + 0.012), (r2 * 0.95, zf + b2 + t + 0.012), (r2 * 0.95, zf + b2 + t + 0.018), (0.07, zf + b2 + t + 0.018)], 'wear_light', 96)]
    objs = sev + mod + lig
    for o in objs:
        place(o, Mx)
    m.overlay('wear', join('wear_zones', objs), 'Wear zones',
              'Typical wear pattern of a centrifugal slurry pump. Purple = most severe: throatbush face and impeller front shroud gap '
              '(recirculation gouging), impeller eye / vane inlet edges, and the volute cutwater (tongue). Pink = moderate: volute '
              'liner around the impeller tip and vane trailing edges. Yellow = light: frame-plate liner / back shroud. Wear grows '
              'steeply with particle size, solids concentration and velocity, so slurry pumps run slow and keep the front clearance closed.',
              split=True, xray=True)
    m.annotate('wear', 'Throatbush & front-shroud gap: recirculation gouging (severe)', W((0.0, r2 * 0.75, -0.08)))
    m.annotate('wear', 'Impeller eye / vane inlet edges (severe)', W((0.0, -re * 0.3, -0.2)))
    m.annotate('wear', 'Volute cutwater / tongue (severe)', W(((r3 + 0.03) * math.cos(th), (r3 + 0.03) * math.sin(th) + 0.12, zc)))
    m.annotate('wear', 'Volute liner at impeller tip (moderate)', W((0.0, -(r3 + 0.07), zc)))
    m.annotate('wear', 'Frame-plate liner / back shroud (light)', W((0.0, r2 * 0.45, zf + b2 + 0.12)))


META = {
    'summary': ('A heavy centrifugal pump built to move abrasive mixtures of liquid and solids (mine tailings, '
                'dredge spoil, mineral concentrates). Large, slow-running impellers with thick shrouds and wide '
                'passages limit wear; the wetted surfaces are replaceable liners of hard white iron or rubber held in '
                'a split outer casing. Pump-out vanes on the impeller and an expeller behind it keep slurry away '
                'from the gland. Speed is set by the V-belt ratio, so the duty can be matched without trimming the '
                'impeller.'),
    'classification': {'family': 'Rotodynamic (centrifugal), radial flow', 'configuration': 'Horizontal, end suction, lined, overhung, belt-driven'},
    'model_configuration': {'teaching_overlays': 'wear (x-ray map of typical wear zones by severity), flow', 'liners': 'Hard-metal (high-chrome white iron) volute liner with throatbush; rubber-lined versions exist for fine slurries',
                            'shaft_seal': 'Expeller + gland packing (centrifugal seal while running; packing for standstill)',
                            'drive': 'Overhead-mounted motor, 3 V-belts (ratio ~1.8:1 shown)',
                            'note': 'Slurry pump selection uses head/efficiency derating for solids (ANSI/HI 12.1-12.6).'},
    'standards': [
        {'id': 'ANSI/HI 12.1-12.6', 'title': 'Rotodynamic (Centrifugal) Slurry Pumps', 'relevance': 'Nomenclature, design, application, wear and performance derating for slurry service.', 'edition': 'to be verified'},
        {'id': 'ISO 9906', 'title': 'Hydraulic performance acceptance tests', 'relevance': 'Water performance testing.', 'edition': 'to be verified'},
    ],
    'references': ['Wilson, Addie, Sellgren, Clift — Slurry Transport Using Centrifugal Pumps.', 'ANSI/HI 12.1-12.6 (scope summary).'],
    'components': {
        'casing': {'function': 'Pressure-containing outer casing that supports the liners.', 'construction': 'Split cover plate and frame plate bolted around the liners; ribs carry pressure loads.',
                   'material': 'Ductile or cast iron (not wetted).', 'operating_conditions': 'Liners take the wear; outer casing must stay dry of slurry.',
                   'failure_modes': ['Wear-through of liner exposing casing', 'Bolt corrosion'], 'inspection': ['Liner thickness checks', 'Bolt condition']},
        'volute_liner': {'function': 'Replaceable wear-resistant hydraulic passage (volute) and suction throatbush.',
                         'construction': 'Cast hard-metal or moulded rubber liners; throatbush sets the front clearance to the impeller.',
                         'material': 'High-chrome white iron (~27% Cr), natural rubber, polyurethane, ceramics.',
                         'operating_conditions': 'Wear rate rises steeply with velocity and particle size/hardness.',
                         'failure_modes': ['Erosive wear (gouging, sliding)', 'Cracking of brittle white iron from impact'],
                         'inspection': ['Thickness gauging at scheduled intervals', 'Adjust throatbush clearance']},
        'impeller_slurry': {'function': 'Adds energy to the slurry; pump-out vanes reduce recirculation and pressure at the shaft seal.',
                            'construction': 'Thick closed shrouds, few (3-5) wide vanes, pump-out vanes on both shrouds; threaded to the shaft.',
                            'material': 'High-chrome white iron, rubber-covered steel, polyurethane.',
                            'operating_conditions': 'Low tip speeds limit wear.', 'failure_modes': ['Vane tip wear', 'Shroud wear', 'Threads seizing on shaft'],
                            'inspection': ['Vane length and shroud thickness', 'Impeller release collar use at removal']},
        'frame_plate_liner': {'function': 'Back liner of the pump chamber and housing for the expeller and gland.', 'construction': 'Insert in the frame plate.',
                              'material': 'High-chrome iron or rubber.', 'operating_conditions': 'Wetted.', 'failure_modes': ['Wear'], 'inspection': ['Thickness']},
        'expeller': {'function': 'Centrifugal (dynamic) seal: its vanes generate pressure that stops slurry reaching the gland while running.',
                     'construction': 'Vaned disc behind the impeller running in the expeller ring.', 'material': 'High-chrome iron.',
                     'operating_conditions': 'Works only above a minimum speed and limited suction pressure; packing seals at standstill.',
                     'failure_modes': ['Wear reducing sealing pressure'], 'inspection': ['Gland leakage trend']},
        'gland_packing': {'function': 'Seals the shaft at standstill (with expeller) or continuously (with gland water flush).',
                          'construction': 'Rings of braided packing with a lantern ring for gland-seal water, compressed by a gland follower.',
                          'material': 'PTFE/aramid/graphite braided packing; bronze lantern ring.',
                          'operating_conditions': 'Packing needs a small controlled leak for cooling; flush water must be clean and at higher pressure than the pump.',
                          'failure_modes': ['Over-tightening burns packing and scores the sleeve', 'Loss of flush water'],
                          'inspection': ['Adjust gland to maintain drip', 'Check flush flow/pressure']},
        'bearing_housing': {'function': 'Cartridge holding the shaft bearings; slides axially in the base to set impeller clearance.',
                            'construction': 'Cylindrical housing clamped in the pedestal with an adjusting screw.', 'material': 'Cast iron/ductile iron.',
                            'operating_conditions': 'Grease or oil lubricated; seals keep slurry out.', 'failure_modes': ['Contamination', 'Overheating'],
                            'inspection': ['Temperature/vibration', 'Regrease']},
        'pump_sheave': {'function': 'Driven pulley; sheave ratio sets pump speed.', 'construction': 'Taper-lock grooved pulley.', 'material': 'Cast iron.',
                        'operating_conditions': 'Belt tension per manufacturer.', 'failure_modes': ['Groove wear'], 'inspection': ['Groove gauge']},
        'motor_sheave': {'function': 'Driving pulley on the motor.', 'construction': 'Taper-lock grooved pulley.', 'material': 'Cast iron.',
                         'operating_conditions': 'Alignment with pump sheave.', 'failure_modes': ['Misalignment'], 'inspection': ['Straight-edge or laser alignment']},
        'v_belts': {'function': 'Transmit power from motor to pump sheave.', 'construction': 'Matched set of V-belts (or banded).', 'material': 'Rubber with tensile cords.',
                    'operating_conditions': 'Correct tension and alignment prevent slip and premature wear.', 'failure_modes': ['Slip, glazing', 'Cracking', 'Unequal stretch'],
                    'inspection': ['Tension check, replace as a set']},
        'motor_mount': {'function': 'Supports the motor above the pump and allows belt tensioning.', 'construction': 'Fabricated frame with adjusting screws.',
                        'material': 'Steel.', 'operating_conditions': 'Must be rigid to avoid belt-induced vibration.', 'failure_modes': ['Loose bolts'], 'inspection': ['Bolt torque']},
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
