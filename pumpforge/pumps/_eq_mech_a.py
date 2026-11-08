"""Mechanical Components & Maintenance — part A (EQ-321 … EQ-333): seals, bearings, couplings and pump components."""
import math
from mathutils import Matrix, Vector
from pumpforge.core import Model, lathe, cyl, box, csg, join, rotate, TAU, OPERATE_FRAMES
from pumpforge.valvekit import P, keys_loop, spring
from pumpforge.parts import hollow_pipe, pressure_gauge, add_tracers, radial_impeller, add_impeller
from pumpforge.vesselkit import nozzle, droplets, half
from pumpforge.plantkit import ball
from pumpforge.shapes import sweep_tube, cone_arrow
from pumpforge.rotkit import axis_rot_keys
from pumpforge.common_meta import C

CAT = '14 · Mechanical Components & Maintenance'


def _model(pid, title):
    return Model(pid, title, CAT, META[pid])


def _ov(m, kind, objs, title, desc):
    m.overlay(kind, join(kind, objs), title, desc, split=True)


def _torus(name, R, r, x, mat, axis='X', cy=0.0, cz=0.0, n=48):
    """Ring (torus) of tube radius r around `axis`, centre radius R at axial position x."""
    if axis == 'X':
        pts = [(x, cy + R * math.cos(TAU * k / n), cz + R * math.sin(TAU * k / n)) for k in range(n + 1)]
    else:
        pts = [(cy + R * math.cos(TAU * k / n), cz + R * math.sin(TAU * k / n), x) for k in range(n + 1)]
    return sweep_tube(name, pts, r, mat, 10, cap=False)


def _shaft(m, pid, name, x0, x1, r, ref, revs=2.0, mat='steel', key=True, explode=(0, -0.3, 0), extra=()):
    o = [cyl(pid + 's', r, x0, x1, mat, 48, axis='X', ch=0.002)] + list(extra)
    if key:
        o.append(box(pid + 'k', (min(0.08, (x1 - x0) * 0.2), r * 0.4, r * 0.3), (x1 - min(0.08, (x1 - x0) * 0.2) / 2 - 0.01, 0, r + r * 0.1), 'steel_dark'))
    p = P(m, pid, name, 'rotating_element', o, explode=explode, ref=ref, section='keep')
    p.spin('X', revs)
    return p


def _sector(name, r0, r1, x0, x1, a0, a1, mat, segs=12):
    """Annular sector (pad) about the X axis between angles a0..a1 (0 = +y, towards +z)."""
    return lathe(name, [(r0, x0), (r1, x0), (r1, x1), (r0, x1)], mat, segs, a0=a0, a1=a1, axis='X', cap_mat=mat)


# =============================================================== EQ-321 Labyrinth seal
def labyrinth_seal(out):
    m = _model('labyrinth_seal', 'Labyrinth Seal (Compressor / Turbine Shaft Seal)')
    teeth = [-0.105, -0.075, -0.045, -0.015, 0.015, 0.045, 0.075, 0.105]
    rb, rt = 0.075, 0.0635
    prof = [(0.16, -0.13), (rb, -0.13)]
    for xk in teeth:
        prof += [(rb, xk - 0.006), (rt, xk - 0.0015), (rt, xk + 0.0015), (rb, xk + 0.006)]
    prof += [(rb, 0.13), (0.16, 0.13)]
    st = csg('st', [lathe('sto', prof, 'aluminium', 96, axis='X')], [cyl('sth', 0.01, 0.06, 0.2, 'aluminium', 16)], 'aluminium')
    P(m, 'labyrinth_stator', 'Labyrinth Stator: Knife-Edge Teeth & Cavities (aluminium / abradable)', 'seal', st, explode=(0, 0.35, 0.15), ref='lab_stator')
    cs = csg('cs', [cyl('cso', 0.3, -0.2, 0.2, 'cast_iron', 96, axis='X'), cyl('csf', 0.34, -0.2, -0.17, 'cast_iron', 96, axis='X')],
             [cyl('csi', 0.16, -0.13, 0.13, 'cast_iron', 96, axis='X'), cyl('csb', 0.068, -0.25, 0.25, 'cast_iron', 64, axis='X'), cyl('csh', 0.012, 0.15, 0.4, 'cast_iron', 16)], 'cast_iron')
    P(m, 'casing', 'Casing / Diaphragm holding the Seal', 'casing', [cs, nozzle('bp', (0, 0, 0.3), (0, 0, 1), 0.02, 0.12)], explode=(0, 0.6, 0), ref='lab_casing')
    _shaft(m, 'shaft', 'Rotor Shaft (turning; tooth tips run with small radial clearance)', -0.3, 0.3, 0.062, 'lab_shaft', revs=2)
    pts = [(-0.2, 0.004, 0.066)]
    for k, xk in enumerate(teeth):
        pts += [(xk - 0.012, 0.004, 0.071), (xk, 0.004, 0.0632), (xk + 0.012, 0.004, 0.071)]
    pts += [(0.2, 0.004, 0.066)]
    add_tracers(m, 'leakage', 'Leakage gas throttled at each tooth, swirling in each cavity', pts, n=6, radius=0.0025, mat='flow_discharge')
    m.flow('leakage', pts, 'flow_discharge', 0.0015, 0.05)
    m.flow('buffer_gas', [(0, 0.004, 0.42), (0, 0.004, 0.08)], 'air', 0.004, 0.08)
    cav = [-0.125, -0.09, -0.06, -0.03, 0.0, 0.03, 0.06, 0.09, 0.125]
    _ov(m, 'pressure', [cyl(f'pc{k}', 0.074, x - 0.006, x + 0.006, f'pressure_{9 - k}', 64, axis='X', r_in=0.0655) for k, x in enumerate(cav)], 'Pressure drops step by step',
        'A labyrinth seal is a non-contacting seal: gas leaking along the shaft is forced through a series of tiny clearances at the knife-edge teeth. At each tooth it accelerates and loses pressure; in the '
        'cavity after it the jet\'s kinetic energy is dissipated as turbulence instead of being recovered. Pressure therefore falls in steps from the high-pressure side to the low-pressure side. Leakage '
        'falls with more teeth and smaller clearance, but never reaches zero; a buffer-gas or eductor port at a middle cavity can stop process gas escaping.')
    return m.export(out)


# =============================================================== EQ-322 Oil seal (radial lip seal)
def oil_seal(out):
    m = _model('oil_seal', 'Radial Shaft Oil Seal (Lip Seal with Garter Spring & Dust Lip)')
    hs = csg('hs', [cyl('hso', 0.1, -0.06, 0.02, 'cast_iron', 96, axis='X')], [cyl('hsb', 0.0715, -0.0062, 0.03, 'cast_iron', 96, axis='X'), cyl('hss', 0.06, -0.07, -0.006, 'cast_iron', 96, axis='X')], 'cast_iron')
    P(m, 'housing', 'Housing Bore & Shoulder (oil side left, air side right)', 'casing', hs, explode=(0, 0.3, 0), ref='os_housing')
    case = join('case', [cyl('cs1', 0.0715, -0.006, 0.006, 'steel', 96, axis='X', r_in=0.0665), cyl('cs2', 0.0665, 0.0042, 0.006, 'steel', 96, axis='X', r_in=0.057)])
    P(m, 'metal_case', 'Metal Case (press-fit in the bore)', 'seal', case, explode=(0.05, 0.12, 0.05), ref='os_case')
    lip = lathe('lip', [(0.0665, 0.0042), (0.057, 0.0042), (0.0545, 0.0), (0.0498, -0.0035), (0.0512, -0.0058), (0.055, -0.004), (0.0585, -0.0005), (0.0665, -0.0045)], 'rubber', 96, axis='X')
    dl = lathe('dl', [(0.057, 0.0042), (0.0506, 0.0068), (0.0512, 0.0078), (0.0575, 0.0055)], 'rubber', 96, axis='X')
    P(m, 'sealing_lip', 'Elastomer Sealing Lip (NBR / FKM) & Dust Lip', 'seal', [lip, dl], explode=(0.08, 0.08, 0.08), ref='os_lip')
    P(m, 'garter_spring', 'Garter Spring (keeps lip load constant as the lip wears)', 'seal', _torus('gs', 0.0555, 0.0014, -0.0028, 'stainless'), explode=(0.12, 0.05, 0.12), ref='os_spring')
    _shaft(m, 'shaft', 'Shaft (turning; ground surface Ra ≈ 0.2–0.8 µm, hardened)', -0.09, 0.07, 0.05, 'os_shaft', revs=2)
    oil = lathe('oil', [(0.0502, -0.06), (0.0598, -0.06), (0.0598, -0.0065), (0.0502, -0.0065)], 'hydraulic_oil', 64, a0=0.0, a1=math.pi, axis='X', cap_mat='hydraulic_oil')
    P(m, 'oil', 'Lubricating Oil on the Pressure Side', 'fluid', oil, explode=(-0.1, 0, 0), ref='os_housing', section='keep')
    add_tracers(m, 'pumping', 'Hydrodynamic pumping at the lip returns oil to the oil side', [(-0.001, 0.003, 0.0503), (-0.004, 0.003, 0.0506), (-0.012, 0.003, 0.052), (-0.03, 0.003, 0.054)], n=4, radius=0.0012, mat='hydraulic_oil')
    m.flow('oil_splash', [(-0.06, 0.003, 0.056), (-0.02, 0.003, 0.054), (-0.005, 0.003, 0.051)], 'hydraulic_oil', 0.0012, 0.02)
    _ov(m, 'pressure', [cyl('lp0', 0.0512, -0.0045, -0.0025, 'pressure_9', 96, axis='X', r_in=0.0502), cyl('lp1', 0.0512, -0.0062, -0.0045, 'pressure_4', 96, axis='X', r_in=0.0502),
                        cyl('lp2', 0.0512, -0.0025, -0.0008, 'pressure_4', 96, axis='X', r_in=0.0502)], 'Narrow, controlled lip contact',
        'The lip is moulded slightly smaller than the shaft (interference) and the garter spring adds radial load, so it contacts the shaft over a band only ≈ 0.1–0.3 mm wide. A thin oil film under the '
        'lip lubricates it; the asymmetric lip angles (steeper on the oil side) create a pumping action that returns oil. Lip seals suit low pressure (≈ ≤ 0.5 bar) and surface speeds up to about '
        '10–30 m/s depending on the elastomer; the dust lip keeps dirt out.')
    return m.export(out)


# =============================================================== EQ-323 Gland packing assembly
def gland_packing_assembly(out):
    m = _model('gland_packing_assembly', 'Gland Packing (Stuffing Box) Assembly with Lantern Ring & Flush')
    bx = csg('bx', [cyl('bxo', 0.085, -0.1, 0.04, 'cast_iron', 96, axis='X'), cyl('bxb', 0.22, -0.16, -0.1, 'cast_iron', 96, axis='X'), cyl('bxf', 0.12, 0.022, 0.04, 'cast_iron', 96, axis='X')],
             [cyl('bxi', 0.058, -0.09, 0.05, 'cast_iron', 96, axis='X'), cyl('bxt', 0.043, -0.17, -0.08, 'cast_iron', 64, axis='X'), cyl('fh', 0.008, 0.05, 0.2, 'cast_iron', 16, center=(-0.042, 0, 0))] +
             [cyl(f'sh{k}', 0.009, 0.0, 0.05, 'cast_iron', 16, axis='X', center=(0, 0.095 * math.cos(a), 0.095 * math.sin(a))) for k, a in enumerate((math.pi / 4, math.pi * 5 / 4))], 'cast_iron')
    P(m, 'stuffing_box', 'Stuffing Box (casing back plate) with Throat Bushing & Flush Connection', 'casing', [bx, nozzle('fl', (-0.042, 0, 0.085), (0, 0, 1), 0.012, 0.1)], explode=(0, 0.5, 0), ref='gp_box')
    rings = []
    for k, (a, b) in enumerate(((-0.09, -0.0725), (-0.0725, -0.055), (-0.031, -0.0135), (-0.0135, 0.004))):
        rings.append(cyl(f'pr{k}', 0.0578, a + 0.0005, b - 0.0005, 'carbon', 96, axis='X', r_in=0.0405))
    P(m, 'packing_rings', 'Packing Rings (braided PTFE / graphite; joints staggered)', 'seal', rings, explode=(0.12, -0.2, 0.15), ref='gp_packing')
    lr = csg('lr', [cyl('lro', 0.0578, -0.0545, -0.0315, 'bronze', 96, axis='X', r_in=0.0405)], [cyl(f'lh{k}', 0.004, 0.035, 0.07, 'bronze', 12, center=(-0.043, 0, 0)) for k in range(1)] +
             [rotate(cyl(f'lh{k}', 0.004, 0.035, 0.07, 'bronze', 12, center=(-0.043, 0, 0)), TAU * k / 6, 'X') for k in range(1, 6)], 'bronze')
    P(m, 'lantern_ring', 'Lantern Ring (distributes flush / cooling liquid into the packing)', 'seal', lr, explode=(0.08, -0.3, 0.2), ref='gp_lantern')
    gl = csg('gl', [cyl('glp', 0.0578, 0.0045, 0.05, 'stainless', 96, axis='X'), cyl('glf', 0.12, 0.05, 0.065, 'stainless', 96, axis='X')],
             [cyl('gli', 0.042, -0.01, 0.08, 'stainless', 64, axis='X')] + [cyl(f'gh{k}', 0.0095, 0.04, 0.08, 'stainless', 16, axis='X', center=(0, 0.095 * math.cos(a), 0.095 * math.sin(a))) for k, a in enumerate((math.pi / 4, math.pi * 5 / 4))], 'stainless')
    pg = P(m, 'gland_follower', 'Gland Follower (compresses the packing)', 'seal', gl, explode=(0.25, 0, 0), ref='gp_gland')
    keys_loop(m, pg, lambda t: (-0.0015 * smooth(t), 0, 0))
    st = [join(f'st{k}', [cyl(f'sts{k}', 0.008, 0.0, 0.1, 'steel', 16, axis='X', center=(0, 0.095 * math.cos(a), 0.095 * math.sin(a))),
                          cyl(f'stn{k}', 0.014, 0.065, 0.078, 'steel_dark', 6, axis='X', center=(0, 0.095 * math.cos(a), 0.095 * math.sin(a)))]) for k, a in enumerate((math.pi / 4, math.pi * 5 / 4))]
    P(m, 'gland_studs', 'Gland Studs & Nuts (tighten evenly, a little at a time)', 'fasteners', st, explode=(0.35, 0, 0), ref='gp_gland', section='keep')
    _shaft(m, 'shaft_sleeve', 'Shaft with Replaceable Sleeve (turning)', -0.22, 0.16, 0.0405, 'gp_sleeve', revs=2, mat='chrome')
    lk = droplets(m, 'leakage_drips', 'Controlled leakage (≈ 40–60 drops/min) lubricates and cools the packing', 0.066, 0.07, -0.042, -0.25, n=4, mat='water', y=0.02, r=0.004)
    m.flow('flush', [(-0.042, 0.003, 0.2), (-0.042, 0.003, 0.06), (-0.06, 0.003, 0.045), (-0.09, 0.003, 0.045)], 'water', 0.003, 0.05)
    m.flow('leakage', [(-0.12, 0.003, 0.045), (-0.09, 0.003, 0.042), (0.004, 0.003, 0.042), (0.06, 0.003, 0.043), (0.068, 0.003, -0.04)], 'flow_discharge', 0.0025, 0.05)
    _ov(m, 'pressure', [cyl(f'pp{k}', 0.06, a, b, f'pressure_{lev}', 96, axis='X', r_in=0.0585) for k, (a, b, lev) in enumerate(((-0.09, -0.0725, 8), (-0.0725, -0.055, 6), (-0.0545, -0.0315, 5), (-0.031, -0.0135, 3), (-0.0135, 0.004, 1)))],
        'Pressure is broken down along the packing', 'Packing seals by throttling: the gland compresses the rings so they press radially on the sleeve, and leakage flows along a long, narrow path, losing '
        'pressure ring by ring. Most of the pressure drop happens in the rings nearest the gland, so those wear first. A packed gland must leak a little (≈ 40–60 drops per minute) — the liquid '
        'lubricates and removes friction heat; over-tightening burns the packing and grooves the sleeve. The lantern ring feeds clean flush liquid into the middle of the set.')
    return m.export(out)


def smooth(t):
    return 0.5 - 0.5 * math.cos(TAU * t)


# =============================================================== EQ-324 Thrust bearing (tilting pad)
def thrust_bearing_assembly(out):
    m = _model('thrust_bearing_assembly', 'Tilting-Pad Thrust Bearing Assembly (Double-Acting)')
    _shaft(m, 'shaft', 'Rotor Shaft (turning)', -0.45, 0.45, 0.06, 'tb_shaft', revs=2)
    cl = [cyl('cl', 0.2, -0.02, 0.02, 'steel', 96, axis='X'), cyl('clh', 0.085, -0.06, 0.06, 'steel', 64, axis='X')] + [box(f'cm{k}', (0.04, 0.01, 0.012), (0.0, 0.0, 0.19), 'steel_dark') for k in range(1)]
    pc = P(m, 'thrust_collar', 'Thrust Collar (shrunk / integral on the shaft)', 'rotating_element', cl, explode=(0, -0.4, 0.3), ref='tb_collar', section='keep')
    pc.spin('X', 2)
    span = math.radians(48)
    for side, (x0, x1) in (('active', (0.024, 0.054)), ('inactive', (-0.054, -0.024))):
        pads = []
        for k in range(6):
            a = TAU * k / 6
            pads.append(_sector(f'{side}p{k}', 0.09, 0.19, x0 + (0.004 if side == 'active' else 0), x1, a - span / 2, a + span / 2, 'steel'))
            fx = (x0, x0 + 0.004) if side == 'active' else (x1 - 0.004, x1)
            pads.append(_sector(f'{side}b{k}', 0.09, 0.19, fx[0], fx[1], a - span / 2, a + span / 2, 'aluminium'))
            px = (x1, x1 + 0.012) if side == 'active' else (x0 - 0.012, x0)
            pads.append(cyl(f'{side}v{k}', 0.016, px[0], px[1], 'chrome', 24, axis='X', center=(0, 0.14 * math.cos(a), 0.14 * math.sin(a))))
        P(m, f'{side}_pads', ('Active (Loaded) Pads' if side == 'active' else 'Inactive (Counter-Thrust) Pads') + ': steel shoes, babbitt faces & spherical pivots', 'bearing', pads,
          explode=((0.25 if side == 'active' else -0.25), -0.3, 0.2), ref='tb_pads', section='keep')
    cr = [cyl('cra', 0.205, 0.066, 0.09, 'steel', 96, axis='X', r_in=0.085), cyl('cri', 0.205, -0.09, -0.066, 'steel', 96, axis='X', r_in=0.085)]
    P(m, 'carrier_rings', 'Carrier / Base Rings (with levelling links in self-equalising designs)', 'bearing', cr, explode=(0, 0.3, 0.3), ref='tb_carrier')
    hs = csg('hs', [cyl('hso', 0.28, -0.12, 0.12, 'paint_blue', 96, axis='X')], [cyl('hsi', 0.215, -0.1, 0.1, 'paint_blue', 96, axis='X'), cyl('hsb', 0.066, -0.2, 0.2, 'paint_blue', 64, axis='X')], 'paint_blue')
    P(m, 'housing', 'Bearing Housing with End Seals', 'casing', [hs, nozzle('oi', (0, 0, 0.28), (0, 0, 1), 0.025, 0.1), nozzle('od', (0, 0, -0.28), (0, 0, -1), 0.03, 0.08),
                                                                 hollow_pipe('rtd', [(0.04, 0.12, 0.15), (0.04, 0.12, 0.33), (0.2, 0.12, 0.33)], 0.004, 'copper', 6, bend=0.01)], explode=(0, 0.6, 0), ref='tb_housing')
    add_tracers(m, 'oil', 'Oil dragged into the converging wedge between collar and pads', [(0.022, 0.15 * math.cos(a), 0.15 * math.sin(a)) for a in [TAU * k / 24 for k in range(25)]],
                n=12, radius=0.004, mat='hydraulic_oil')
    m.flow('oil_supply', [(0, 0.004, 0.38), (0, 0.004, 0.215), (0.022, 0.004, 0.2), (0.022, 0.004, 0.09)], 'hydraulic_oil', 0.005, 0.08)
    ov = []
    for k in range(6):
        a = TAU * k / 6
        for j, lev in enumerate((2, 5, 8)):
            ov.append(_sector(f'pz{k}{j}', 0.095, 0.185, 0.0205, 0.0235, a - span / 2 + span * j / 3, a - span / 2 + span * (j + 1) / 3, f'pressure_{lev}', 6))
    _ov(m, 'pressure', ov, 'Oil-film pressure builds toward the trailing edge',
        'Each pad tilts freely on its pivot so a converging oil wedge forms between the rotating collar and the pad face. Oil dragged into the narrowing gap builds hydrodynamic pressure, highest '
        'toward the trailing edge, which carries the axial thrust without metal contact (film typically ≈ 10–50 µm). Pad temperature (RTD in the babbitt) is the main health indicator; the '
        'inactive pads take reverse thrust during start-up or surge.')
    m.overlay('thrust', join('thrustarrow', [cone_arrow('ta', (-0.42, 0, 0.0), (1, 0, 0), 0.12, 0.03, 'thrust'), cyl('tas', 0.012, -0.55, -0.42, 'thrust', 16, axis='X')]), 'Axial thrust', 'Rotor thrust pushes the collar against the active pads.', split=False)
    return m.export(out)


# =============================================================== EQ-325 Journal bearing
def journal_bearing(out):
    m = _model('journal_bearing', 'Hydrodynamic Plain Journal Bearing (Split Babbitt-Lined Shell)')
    e = 0.0045
    ec = (0, e * math.cos(math.radians(45)), -e * math.sin(math.radians(45)))
    js = [cyl('jn', 0.08, -0.3, 0.3, 'steel', 96, axis='X', center=ec), box('jm', (0.06, 0.012, 0.01), (-0.2, ec[1], ec[2] + 0.08), 'steel_dark')]
    pj = P(m, 'journal', 'Journal (shaft) — runs eccentric, clearance exaggerated for teaching', 'rotating_element', js, explode=(0, -0.4, 0.2), ref='jb_journal', section='keep', pivot=ec)
    pj.spin('X', 2)
    ln = csg('ln', [cyl('lno', 0.091, -0.08, 0.08, 'aluminium', 96, axis='X')], [cyl('lni', 0.086, -0.1, 0.1, 'aluminium', 96, axis='X'), box('g1', (0.12, 0.012, 0.01), (0, 0.088, 0), 'aluminium'), box('g2', (0.12, 0.012, 0.01), (0, -0.088, 0), 'aluminium'),
                                                                                cyl('oh', 0.006, 0.08, 0.13, 'aluminium', 12)], 'aluminium')
    sh = csg('sh', [cyl('sho', 0.11, -0.08, 0.08, 'steel', 96, axis='X')], [cyl('shi', 0.0905, -0.1, 0.1, 'steel', 96, axis='X'), cyl('oh2', 0.006, 0.08, 0.13, 'steel', 12)], 'steel')
    P(m, 'babbitt_lining', 'Babbitt (white-metal) Lining with Axial Oil Grooves at the Split', 'bearing', ln, explode=(0, 0.25, 0.25), ref='jb_lining')
    P(m, 'bearing_shell', 'Steel Backing Shell (upper & lower halves)', 'bearing', sh, explode=(0, 0.4, 0.4), ref='jb_shell')
    hs = csg('hs', [box('hso', (0.22, 0.4, 0.34), (0, 0, -0.03), 'cast_iron'), box('hsf', (0.3, 0.55, 0.05), (0, 0, -0.205), 'cast_iron')],
             [cyl('hsb', 0.11, -0.2, 0.2, 'cast_iron', 96, axis='X'), cyl('hsh', 0.008, 0.08, 0.2, 'cast_iron', 12)], 'cast_iron')
    P(m, 'pedestal', 'Bearing Pedestal & Cap (bolted at the horizontal split)', 'casing', [hs, nozzle('oin', (0, 0, 0.14), (0, 0, 1), 0.015, 0.1)] +
      [cyl(f'cb{k}', 0.012, -0.1, 0.17, 'steel_dark', 12, center=(0, s * 0.16, 0)) for k, s in enumerate((-1, 1))], explode=(0, 0.6, 0), ref='jb_pedestal')
    of = half(csg('of', [cyl('ofo', 0.0859, -0.079, 0.079, 'hydraulic_oil', 96, axis='X')], [cyl('ofi', 0.0802, -0.1, 0.1, 'hydraulic_oil', 96, axis='X', center=ec)], 'hydraulic_oil'), 'hydraulic_oil')
    P(m, 'oil_film', 'Oil Film (thickest opposite the load, thinnest at h_min)', 'fluid', of, explode=(0, -0.2, 0), ref='jb_film', section='keep')
    path = [(0.04, 0.083 * math.sin(a), 0.083 * math.cos(a)) for a in [TAU * k / 32 for k in range(33)]]
    add_tracers(m, 'oil', 'Oil carried round by the journal into the converging gap', path, n=10, radius=0.0025, mat='hydraulic_oil')
    m.flow('oil_in', [(0, 0.004, 0.25), (0, 0.004, 0.09), (0.06, 0.004, 0.087)], 'hydraulic_oil', 0.004, 0.06)
    m.flow('side_leakage', [(0.06, 0.06, -0.06), (0.1, 0.07, -0.07), (0.1, 0.07, -0.2)], 'hydraulic_oil', 0.003, 0.05)
    bars = []
    eps, phi_max = 0.7, math.radians(315)
    vals = []
    for k in range(1, 36):
        psi = math.pi * k / 36
        vals.append((phi_max - psi, math.sin(psi) / (1 + eps * math.cos(psi)) ** 2))
    pmax = max(v for _, v in vals)
    for k, (phi, v) in enumerate(vals):
        pn = v / pmax
        if pn < 0.06:
            continue
        L = 0.015 + 0.13 * pn
        b = box(f'pb{k}', (0.01, 0.012, L), (0.1, 0, 0.115 + L / 2), f'pressure_{min(9, int(1 + 8 * pn))}')
        bars.append(rotate(b, -phi, 'X'))
    _ov(m, 'pressure', bars, 'Hydrodynamic pressure lifts the journal',
        'When the shaft turns it drags oil into the narrowing gap on one side of the eccentric journal. The wedge builds pressure (bars) that floats the shaft on an oil film; the shaft settles at an '
        'eccentricity and attitude angle that balance the load. Minimum film thickness is typically ≈ 10–50 µm; the bearing clearance is ≈ 1–2 µm per mm of diameter. At start-up and shut-down there is '
        'little film, so most babbitt wear happens then (jacking oil is used on large machines).')
    return m.export(out)


# =============================================================== EQ-326 Bearing housing (oil-ring lubricated)
def bearing_housing(out):
    m = _model('bearing_housing', 'Pump Bearing Housing (Oil-Ring Lubricated, Radial + Duplex Thrust Bearings)')
    hs = csg('hs', [cyl('hso', 0.13, -0.3, 0.3, 'paint_blue', 96, axis='X'), box('hsp', (0.5, 0.22, 0.14), (0, 0, -0.16), 'paint_blue'), box('hsf', (0.36, 0.34, 0.04), (0, 0, -0.25), 'paint_blue')] +
             [cyl(f'fn{k}', 0.15, x - 0.005, x + 0.005, 'paint_blue', 96, axis='X') for k, x in enumerate((-0.15, -0.075, 0.0, 0.075, 0.15))],
             [cyl('hsi', 0.11, -0.26, 0.2, 'paint_blue', 96, axis='X'), box('hspi', (0.46, 0.18, 0.13), (0, 0, -0.155), 'paint_blue'), cyl('bi', 0.065, -0.31, -0.25, 'paint_blue', 64, axis='X'),
              cyl('bo', 0.075, 0.19, 0.31, 'paint_blue', 64, axis='X')], 'paint_blue')
    P(m, 'housing', 'Bearing Housing / Frame with Cooling Fins, Oil Sump & Mounting Foot', 'casing', hs, explode=(0, 0.6, 0), ref='bh_housing')
    sh = [cyl('s0', 0.035, -0.5, 0.45, 'steel', 48, axis='X', ch=0.002), cyl('s1', 0.045, -0.24, 0.19, 'steel', 48, axis='X'), box('ky', (0.06, 0.012, 0.01), (0.41, 0, 0.037), 'steel_dark')]
    ps = P(m, 'shaft', 'Pump Shaft (impeller end left, coupling end right)', 'rotating_element', sh, explode=(0, -0.4, 0.2), ref='bh_shaft', section='keep')
    ps.spin('X', 2)
    for nm, x0, x1, ri, ro, label in (('inboard', -0.3, -0.26, 0.035, 0.065, 'Inboard Radial Bearing (deep-groove ball)'), ('outboard', 0.2, 0.3, 0.035, 0.075, 'Outboard Thrust Bearings (duplex angular-contact, back-to-back)')):
        rm = (ri + ro) / 2
        rings = [cyl(nm + 'ir', rm - 0.006, x0, x1, 'steel', 64, axis='X', r_in=ri), cyl(nm + 'or', ro, x0, x1, 'steel', 64, axis='X', r_in=rm + 0.006)]
        P(m, nm + '_bearing_rings', label + ' — rings', 'bearing', rings, explode=(0, 0.3, 0.3), ref='bh_bearings')
        balls = []
        rows = [(x0 + x1) / 2] if nm == 'inboard' else [x0 + 0.025, x0 + 0.075]
        for j, xc in enumerate(rows):
            for k in range(10):
                a = TAU * (k + 0.5 * j) / 10
                balls.append(ball(f'{nm}b{j}{k}', 0.0085, 'chrome', (xc, rm * math.cos(a), rm * math.sin(a))))
        pb = P(m, nm + '_bearing_balls', label + ' — balls & cage (cage turns ≈ 0.4 × shaft speed)', 'bearing', balls, explode=(0, -0.3, 0.3), ref='bh_bearings', section='keep')
        pb.spin('X', 0.8)
    orr = _torus('or', 0.075, 0.005, -0.1, 'brass', cz=-0.03)
    po = P(m, 'oil_ring', 'Oil Ring (rides on the shaft, dips in oil and lifts it to the bearings)', 'lubrication', orr, explode=(0, -0.2, 0.3), ref='bh_oilring', section='keep', pivot=(-0.1, 0, -0.03))
    po.spin('X', 0.6)
    oil = box('oil', (0.455, 0.09, 0.115), (0, 0.045, -0.155), 'hydraulic_oil')
    P(m, 'oil_sump', 'Oil Bath (level at about the centre of the lowest ball)', 'fluid', oil, explode=(0, -0.3, -0.2), ref='bh_oil', section='keep')
    ac = [cyl(f'is{k}', 0.06, x0, x1, 'bronze', 64, axis='X', r_in=0.036) for k, (x0, x1) in enumerate(((-0.33, -0.3), (0.3, 0.33)))]
    ac += [join('clo', [hollow_pipe('clp', [(0.05, 0.11, -0.1), (0.05, 0.2, -0.1), (0.05, 0.2, -0.05)], 0.008, 'brass', 8, bend=0.01), cyl('clb', 0.035, -0.05, 0.1, 'glass', 24, center=(0.05, 0.2, 0))]),
           cyl('br', 0.012, 0.13, 0.17, 'brass', 12, center=(0.1, 0, 0)), cyl('sg', 0.02, 0.11, 0.135, 'glass', 24, axis='Y', center=(-0.12, 0, -0.13)), cyl('dp', 0.012, -0.29, -0.26, 'brass', 8, center=(0.15, 0, 0))]
    P(m, 'accessories', 'Bearing Isolators (labyrinth), Constant-Level Oiler, Breather, Sight Glass & Drain Plug', 'lubrication', ac, explode=(0, 0.3, 0.3), ref='bh_accessories', section='keep')
    droplets(m, 'oil_splash', 'Oil lifted by the ring and splashed onto the bearings', -0.12, 0.2, 0.06, -0.09, n=8, mat='hydraulic_oil', y=0.06, r=0.005)
    m.flow('oil_level', [(0.05, 0.2, 0.08), (0.05, 0.2, -0.1), (0.05, 0.11, -0.1)], 'hydraulic_oil', 0.004, 0.05)
    _ov(m, 'temperature', [cyl('t0', 0.068, -0.3, -0.26, 'pressure_5', 64, axis='X', r_in=0.066), cyl('t1', 0.078, 0.2, 0.3, 'pressure_7', 64, axis='X', r_in=0.076), box('t2', (0.44, 0.005, 0.1), (0, 0.095, -0.155), 'pressure_3')],
        'Heat comes from the bearings; oil carries it to the housing', 'Friction in the bearings (thrust bearings more) heats the oil; the oil ring spreads oil and the finned housing rejects heat to air. '
        'Typical limits: bearing housing ≈ 80–85 °C or ≈ 40 °C above ambient (check the maker/API 610 guidance). Correct oil level matters: too low starves the bearings, too high churns and overheats. '
        'Bearing isolators keep water and dust out — contamination is the leading cause of bearing failure.')
    return m.export(out)


# =============================================================== EQ-327 Mechanical cartridge seal
def mechanical_cartridge_seal(out):
    m = _model('mechanical_cartridge_seal', 'Mechanical Cartridge Seal (Single, Pusher Type) with Flush (API Plan 11)')
    ch = csg('ch', [cyl('cho', 0.11, -0.13, 0.0, 'cast_iron', 96, axis='X'), cyl('chb', 0.22, -0.16, -0.13, 'cast_iron', 96, axis='X')],
             [cyl('chi', 0.068, -0.12, 0.01, 'cast_iron', 96, axis='X'), cyl('cht', 0.042, -0.2, -0.11, 'cast_iron', 64, axis='X')], 'cast_iron')
    P(m, 'seal_chamber', 'Seal Chamber (pump casing back plate)', 'casing', ch, explode=(0, 0.5, 0), ref='mcs_chamber')
    gl = csg('gl', [cyl('glo', 0.12, 0.0, 0.03, 'stainless', 96, axis='X'), cyl('glp', 0.0675, -0.015, 0.0, 'stainless', 96, axis='X')],
             [cyl('gli', 0.04, -0.02, 0.04, 'stainless', 64, axis='X'), cyl('gls', 0.059, -0.016, -0.001, 'stainless', 64, axis='X'), cyl('glh', 0.004, 0.035, 0.13, 'stainless', 12, center=(0.012, 0, 0))] +
             [cyl(f'bh{k}', 0.008, -0.01, 0.04, 'stainless', 12, axis='X', center=(0, 0.095 * math.cos(a), 0.095 * math.sin(a))) for k, a in enumerate((math.pi / 4, math.pi * 3 / 4, math.pi * 5 / 4, math.pi * 7 / 4))], 'stainless')
    P(m, 'gland_plate', 'Gland Plate with Flush (F), Quench (Q) & Drain (D) Ports', 'seal', [gl, nozzle('fp', (0.012, 0, 0.12), (0, 0, 1), 0.008, 0.05)], explode=(0.2, 0.2, 0), ref='mcs_gland')
    seat = cyl('seat', 0.0585, -0.0145, -0.002, 'silicon_carbide', 96, axis='X', r_in=0.042)
    P(m, 'stationary_seat', 'Stationary Seat (silicon carbide), O-ring mounted in the gland', 'seal', [seat, _torus('so', 0.06, 0.0015, -0.008, 'rubber')], explode=(0.06, 0.15, 0.15), ref='mcs_faces')
    rf = lathe('rf', [(0.043, -0.0245), (0.056, -0.0245), (0.056, -0.0165), (0.052, -0.0145), (0.045, -0.0145), (0.043, -0.0165)], 'carbon', 96, axis='X')
    P(m, 'rotating_face', 'Rotating Face (carbon-graphite) — lapped flat to ≈ 1 µm (2–3 helium light bands)', 'seal', rf, explode=(-0.03, 0.2, 0.2), ref='mcs_faces')
    sl = csg('sl', [cyl('slo', 0.0395, -0.11, 0.075, 'stainless', 96, axis='X')], [cyl('sli', 0.035, -0.12, 0.08, 'stainless', 64, axis='X')], 'stainless')
    P(m, 'sleeve', 'Cartridge Sleeve (O-ring sealed to the shaft)', 'seal', [sl, _torus('sso', 0.0365, 0.0015, -0.1, 'rubber')], explode=(-0.15, -0.2, 0), ref='mcs_sleeve')
    ru = [cyl('ret', 0.058, -0.075, -0.064, 'stainless', 96, axis='X', r_in=0.0395), cyl('hold', 0.058, -0.032, -0.0245, 'stainless', 96, axis='X', r_in=0.044)]
    for k in range(8):
        a = TAU * k / 8
        ru.append(spring(f'sp{k}', (0, 0.051 * math.cos(a), 0.051 * math.sin(a)), 0.0035, -0.064, -0.032, 0.0008, turns=6, mat='stainless', axis='X'))
    ru += [join('dc', [cyl('dco', 0.055, 0.035, 0.055, 'stainless', 96, axis='X', r_in=0.0395)] + [cyl(f'ss{k}', 0.004, 0.039, 0.058, 'steel_dark', 8, center=(0.045, 0, 0)) if k == 0 else
                                                                                                   rotate(cyl(f'ss{k}', 0.004, 0.039, 0.058, 'steel_dark', 8, center=(0.045, 0, 0)), TAU * k / 3, 'X') for k in range(3)])]
    pr = P(m, 'rotating_unit', 'Rotating Unit: Spring Retainer, 8 Small Springs, Face Holder & Drive Collar with Set Screws (turning)', 'rotating_element', ru, explode=(-0.12, -0.25, 0.15), ref='mcs_springs', section='keep')
    pr.spin('X', 2)
    _shaft(m, 'shaft', 'Pump Shaft (turning)', -0.3, 0.2, 0.035, 'mcs_shaft', revs=2)
    clips = [rotate(box(f'cl{k}', (0.03, 0.012, 0.008), (0.04, 0, 0.062), 'paint_yellow'), TAU * k / 3 + 0.3, 'X') for k in range(3)]
    P(m, 'setting_clips', 'Setting Clips (centre & set the cartridge — REMOVE after installation)', 'seal', clips, explode=(0.1, 0, 0.15), ref='mcs_gland', section='keep')
    fl = lathe('pl', [(0.0405, -0.12), (0.0675, -0.12), (0.0675, -0.016), (0.059, -0.016), (0.059, -0.002), (0.0585, -0.0145), (0.0405, -0.0145)], 'water', 64, a0=0.0, a1=math.pi, axis='X', cap_mat='water')
    P(m, 'process_liquid', 'Process Liquid in the Seal Chamber', 'fluid', fl, explode=(-0.1, -0.1, 0), ref='mcs_chamber', section='keep')
    m.flow('flush', [(0.012, 0.004, 0.2), (0.012, 0.004, 0.064), (-0.01, 0.004, 0.062), (-0.06, 0.004, 0.062), (-0.11, 0.004, 0.05)], 'water', 0.003, 0.05)
    _ov(m, 'pressure', [cyl(f'fz{k}', b, -0.0148, -0.0142, f'pressure_{lev}', 96, axis='X', r_in=a) for k, (a, b, lev) in enumerate(((0.045, 0.0485, 2), (0.0485, 0.052, 5), (0.052, 0.056, 8)))],
        'A micro-thin film seals across the faces', 'Springs and the hydraulic closing force press the rotating face against the stationary seat. Liquid from the chamber (outside diameter) forms a film of '
        'only ≈ 0.5–1 µm between the lapped faces, and its pressure falls across the face width to atmosphere at the inside diameter. Balance ratio (≈ 0.7–0.85 for balanced seals) sets the face load. '
        'The flush (Plan 11: from discharge to the seal chamber) removes heat and keeps the faces cool; running dry destroys the faces in seconds. A cartridge is pre-assembled and pre-set, so '
        'installation errors are fewer — but the setting clips must be removed before start-up.')
    return m.export(out)


# =============================================================== EQ-328 Expansion (axial-float) coupling — gear type
def expansion_coupling(out):
    m = _model('expansion_coupling', 'Expansion (Axial-Float) Coupling — Double-Engagement Gear Type')
    fl = lambda t: 0.008 * math.sin(math.pi * t) ** 2       # thermal growth of the driven shaft, then back
    P(m, 'driver_hub', 'Driver Hub (keyed to the motor shaft)', 'hub', cyl('dh', 0.07, -0.13, -0.012, 'steel', 96, axis='X', r_in=0.04), explode=(-0.25, 0.2, 0), ref='ec_hubs')
    pdh = P(m, 'driven_hub', 'Driven Hub (keyed to the pump / compressor shaft) — slides axially', 'hub', cyl('nh', 0.07, 0.012, 0.13, 'steel', 96, axis='X', r_in=0.04), explode=(0.25, 0.2, 0), ref='ec_hubs')
    keys_loop(m, pdh, lambda t: (fl(t), 0, 0))
    for nm, x0, x1, sgn in (('driver', -0.06, -0.016, -1), ('driven', 0.016, 0.06, 1)):
        th = [cyl(nm + 'tr', 0.074, x0, x1, 'steel', 96, axis='X', r_in=0.068)]
        for k in range(36):
            t = lathe(f'{nm}t{k}', [(0.074, x0), (0.083, x0 + 0.006), (0.0845, (x0 + x1) / 2), (0.083, x1 - 0.006), (0.074, x1)], 'steel', 4, a0=-0.035, a1=0.035, axis='X', cap_mat='steel')
            th.append(rotate(t, TAU * k / 36, 'X'))
        sh = [cyl(nm + 'sh', 0.04, (-0.3 if sgn < 0 else 0.013), (-0.013 if sgn < 0 else 0.3), 'steel', 48, axis='X'), box(nm + 'ky', (0.06, 0.01, 0.01), (sgn * 0.22, 0, 0.042), 'steel_dark')]
        pt = P(m, f'{nm}_teeth_shaft', ('Driver' if sgn < 0 else 'Driven') + ' Shaft & Crowned External Teeth (turning)', 'rotating_element', th + sh, explode=(sgn * 0.3, -0.3, 0.1), ref='ec_teeth', section='keep')
        pt.spin('X', 1)
        if sgn > 0:
            for ms in pt.meshes:
                m.keyframes(ms, 'Operate', 'location', [(1 + f, (fl(f / OPERATE_FRAMES), 0, 0)) for f in range(OPERATE_FRAMES + 1)])
    sv = csg('sv', [cyl('svo', 0.11, -0.075, 0.075, 'steel', 96, axis='X'), cyl('svf', 0.15, -0.012, 0.012, 'steel', 96, axis='X')], [cyl('svi', 0.0855, -0.08, 0.08, 'steel', 96, axis='X')], 'steel')
    P(m, 'sleeve', 'Flanged Sleeve with Internal Teeth (two halves bolted at the centre)', 'sleeve', [sv] + [cyl(f'es{k}', 0.086, x0, x1, 'rubber', 96, axis='X', r_in=0.071) for k, (x0, x1) in enumerate(((-0.075, -0.068), (0.068, 0.075)))],
      explode=(0, 0.5, 0.2), ref='ec_sleeve')
    bl = [cyl(f'bo{k}', 0.008, -0.03, 0.03, 'steel_dark', 12, axis='X', center=(0, 0.13 * math.cos(TAU * k / 8), 0.13 * math.sin(TAU * k / 8))) for k in range(8)]
    pb = P(m, 'flange_bolts', 'Flange Bolts (turning with the sleeve)', 'fasteners', bl, explode=(0, 0.6, 0.3), ref='ec_sleeve', section='keep')
    pb.spin('X', 1)
    gr = half(csg('gr', [cyl('gro', 0.0855, -0.068, 0.068, 'hydraulic_oil', 96, axis='X')], [cyl('gri', 0.075, -0.07, 0.07, 'hydraulic_oil', 96, axis='X')], 'hydraulic_oil'), 'hydraulic_oil')
    P(m, 'lubricant', 'Coupling Grease / Oil (gear couplings must be lubricated)', 'fluid', gr, explode=(0, -0.2, 0.3), ref='ec_sleeve', section='keep')
    m.flow('torque', [(-0.3, 0, 0.0), (-0.04, 0, 0.0), (-0.04, 0.004, 0.08), (0.04, 0.004, 0.08), (0.04, 0, 0.0), (0.3, 0, 0.0)], 'power', 0.006, 0.08)
    _ov(m, 'pressure', [cyl(f'tz{k}', 0.086, x0, x1, 'pressure_7', 96, axis='X', r_in=0.082) for k, (x0, x1) in enumerate(((-0.05, -0.026), (0.026, 0.05)))],
        'Teeth transmit torque and let the shaft slide', 'Torque passes from the driver hub teeth to the sleeve and on to the driven hub teeth. Because the teeth can slide axially in the sleeve, the driven '
        'shaft is free to grow with temperature (animation shows axial float) without loading the bearings, and the crowned teeth accept small angular and offset misalignment. Sliding under '
        'torque needs lubrication — gear couplings are greased or oil-fed; dry teeth wear quickly and can lock, transmitting large thrust. (Pipework "expansion couplings" are a different item.)')
    m.overlay('thrust', join('th', [cone_arrow('ta', (0.2, 0, 0.1), (1, 0, 0), 0.08, 0.02, 'thrust')]), 'Thermal growth', 'The driven shaft grows axially; the coupling slides instead of pushing on the bearings.', split=False)
    return m.export(out)


# =============================================================== EQ-329 Universal joint (Cardan)
def universal_joint(out):
    m = _model('universal_joint', 'Universal (Cardan / Hooke\'s) Joint — Input & Output at 25°')
    beta = math.radians(25)
    u2 = Vector((math.cos(beta), 0, math.sin(beta)))
    Y = Vector((0, 1, 0))
    b0 = u2.cross(Y).normalized()
    b0 = -b0 if b0.z < 0 else b0
    n0 = Y.cross(b0)
    # input yoke (pins along Y)
    iy = [cyl('is', 0.03, -0.42, -0.07, 'steel', 48, axis='X'), cyl('ib', 0.065, -0.075, -0.06, 'steel', 64, axis='X'), box('ik', (0.06, 0.01, 0.008), (-0.3, 0, 0.032), 'steel_dark')]
    for s in (-1, 1):
        iy += [box(f'ie{s}', (0.08, 0.014, 0.04), (-0.025, s * 0.058, 0), 'steel'), cyl(f'ic{s}', 0.016, s * 0.047 - 0.008 if s > 0 else -0.062, s * 0.047 + 0.016 if s > 0 else -0.039, 'chrome', 24, axis='Y')]
    piy = P(m, 'input_yoke', 'Input Shaft & Yoke with Needle-Bearing Caps', 'rotating_element', iy, explode=(-0.25, 0, 0), ref='uj_yokes', section='keep')
    # output yoke built along +X with pins along local Z, then tilted by beta
    oy = [cyl('os', 0.03, 0.07, 0.42, 'steel', 48, axis='X'), cyl('ob', 0.065, 0.06, 0.075, 'steel', 64, axis='X'), box('ok', (0.06, 0.01, 0.008), (0.3, 0.032, 0), 'steel_dark')]
    for s in (-1, 1):
        oy += [box(f'oe{s}', (0.08, 0.04, 0.014), (0.025, 0, s * 0.058), 'steel'), cyl(f'oc{s}', 0.016, s * 0.047 - 0.008 if s > 0 else -0.062, s * 0.047 + 0.016 if s > 0 else -0.039, 'chrome', 24)]
    oy = [rotate(o, -beta, 'Y') for o in oy]
    poy = P(m, 'output_yoke', 'Output Shaft & Yoke (at joint angle β = 25°)', 'rotating_element', oy, explode=(0.25, 0, 0.1), ref='uj_yokes', section='keep')
    cr = [cyl('cy', 0.011, -0.05, 0.05, 'chrome', 24, axis='Y'), cyl('cz', 0.011, -0.05, 0.05, 'chrome', 24), ball('cc', 0.02, 'steel')]
    cr = [rotate(o, -beta, 'Y') if o.name.startswith('cz') else o for o in cr]
    pcr = P(m, 'cross_spider', 'Cross (Spider / Trunnion) with Four Journals', 'rotating_element', cr, explode=(0, -0.3, 0.25), ref='uj_cross', section='keep')
    th2s, prev = [], 0.0
    for f in range(OPERATE_FRAMES + 1):
        t1 = TAU * f / OPERATE_FRAMES
        a1 = Matrix.Rotation(t1, 3, 'X') @ Y
        A, B = a1.dot(b0), a1.dot(u2.cross(b0))
        c = math.atan2(-A, B)
        while c - prev > math.pi / 2:
            c -= math.pi
        while c - prev < -math.pi / 2:
            c += math.pi
        th2s.append(c)
        prev = c
    off = th2s[0]
    th2s = [c - off for c in th2s]
    ki, ko, kc = [], [], []
    ec_prev = None
    for f in range(OPERATE_FRAMES + 1):
        t1 = TAU * f / OPERATE_FRAMES
        ri = Matrix.Rotation(t1, 3, 'X')
        ro = Matrix.Rotation(th2s[f], 3, u2)
        a1, a2 = ri @ Y, ro @ b0
        a2 = (a2 - a1 * a1.dot(a2)).normalized()
        Mt = Matrix((a1, a2, a1.cross(a2))).transposed() @ Matrix((Y, b0, n0))
        e1 = ri.to_euler('XYZ')
        e2 = ro.to_euler('XYZ', ko[-1][1] if ko else None) if ko else ro.to_euler('XYZ')
        ec = Mt.to_euler('XYZ', ec_prev) if ec_prev else Mt.to_euler('XYZ')
        ec_prev = ec
        fr = 1 + f
        ki.append((fr, (t1, 0.0, 0.0)))
        ko.append((fr, e2))
        kc.append((fr, (ec.x, ec.y, ec.z)))
    ko = [(fr, (e.x, e.y, e.z)) for fr, e in ko]
    for p, keys in ((piy, ki), (poy, ko), (pcr, kc)):
        for ms in p.meshes:
            m.keyframes(ms, 'Operate', 'rotation_euler', keys)
    P(m, 'supports', 'Shaft Support Bearings (pillow blocks)', 'structure', [join(f'pb{k}', [box(f'pbb{k}', (0.06, 0.08, 0.1), c, 'paint_grey'), cyl(f'pbr{k}', 0.035, c[0] - 0.03, c[0] + 0.03, 'steel', 32, axis='X', center=(0, c[1], c[2]), r_in=0.031)])
                                                                                        for k, c in enumerate(((-0.35, 0, 0.0),))] +
      [rotate(join('pb2', [box('pbb2', (0.06, 0.08, 0.1), (0.35, 0, 0), 'paint_grey'), cyl('pbr2', 0.035, 0.32, 0.38, 'steel', 32, axis='X', r_in=0.031)]), -beta, 'Y')], explode=(0, 0, -0.2), ref='uj_supports', section='keep')
    m.flow('torque', [(-0.42, 0, 0.0), (-0.03, 0, 0.0)] + [(0.42 * u2.x * s, 0, 0.42 * u2.z * s) for s in (0.07, 1.0)], 'power', 0.006, 0.08)
    arc = lathe('arc', [(0.18, -0.003), (0.24, -0.003), (0.24, 0.003), (0.18, 0.003)], 'pressure_6', 24, a0=math.pi / 2 - beta, a1=math.pi / 2, axis='Y', cap_mat='pressure_6')
    _ov(m, 'pressure', [arc], 'Joint angle β makes the output speed fluctuate', 'A single Cardan joint transmits rotation through an angle, but not at constant speed: the output angular velocity '
        'swings between ω·cos β and ω/cos β twice every revolution (for β = 25° about −9 % to +10 %). Two joints with the yokes of the intermediate shaft in phase and equal angles (Z or W '
        'arrangement) cancel the fluctuation. The needle bearings in the cross only oscillate, so they need a minimum working angle (≈ 1–2°) to spread grease and avoid brinelling.')
    return m.export(out)


# =============================================================== EQ-330 Torsional (highly flexible) coupling
def torsional_coupling(out):
    m = _model('torsional_coupling', 'Highly Flexible Torsional Coupling (Rubber Element) — Engine Flywheel to Driven Shaft')
    th_o = lambda t: TAU * t + 0.08 * math.sin(TAU * 6 * t)
    th_h = lambda t: TAU * t + 0.02 * math.sin(TAU * 6 * t - 0.8)
    fw = [cyl('fw', 0.32, -0.24, -0.16, 'cast_iron', 96, axis='X'), cyl('fwg', 0.335, -0.2, -0.17, 'steel_dark', 96, axis='X', r_in=0.32), box('fwm', (0.05, 0.02, 0.02), (-0.2, 0, 0.3), 'paint_yellow'),
          cyl('crk', 0.06, -0.45, -0.24, 'steel', 48, axis='X')]
    fw += [cyl(f'fb{k}', 0.01, -0.165, -0.085, 'steel_dark', 12, axis='X', center=(0, 0.25 * math.cos(TAU * k / 8), 0.25 * math.sin(TAU * k / 8))) for k in range(8)]
    fw += [cyl('or', 0.27, -0.16, -0.14, 'steel', 96, axis='X', r_in=0.225)]
    pf = P(m, 'flywheel_outer', 'Engine Flywheel, Ring Gear & Outer Flange (driving side)', 'rotating_element', fw, explode=(-0.3, 0, 0), ref='tc_flywheel', section='keep')
    for ms in pf.meshes:
        axis_rot_keys(m, ms, (1, 0, 0), th_o)
    rb = []
    for k in range(8):
        a = TAU * k / 8
        rb.append(lathe(f'rb{k}', [(0.09, -0.135), (0.225, -0.135), (0.225, -0.03), (0.09, -0.03)], 'rubber', 10, a0=a - 0.3, a1=a + 0.3, axis='X', cap_mat='rubber'))
    pr = P(m, 'rubber_element', 'Rubber Element Segments (vulcanised; soft in torsion)', 'element', rb, explode=(0, -0.35, 0.2), ref='tc_element', section='keep')
    for ms in pr.meshes:
        axis_rot_keys(m, ms, (1, 0, 0), lambda t: 0.5 * (th_o(t) + th_h(t)))
    hb = [cyl('hb', 0.09, -0.14, 0.06, 'steel', 64, axis='X', r_in=0.05), cyl('hf', 0.12, -0.03, -0.015, 'steel', 64, axis='X', r_in=0.05), cyl('os', 0.05, -0.14, 0.55, 'steel', 48, axis='X'),
          box('hk', (0.06, 0.012, 0.01), (0.4, 0, 0.052), 'steel_dark'), box('hm', (0.04, 0.02, 0.02), (0.03, 0, 0.1), 'paint_yellow')]
    ph = P(m, 'hub_shaft', 'Inner Hub & Driven Shaft (generator / pump / gearbox)', 'rotating_element', hb, explode=(0.3, 0, 0), ref='tc_hub', section='keep')
    for ms in ph.meshes:
        axis_rot_keys(m, ms, (1, 0, 0), th_h)
    P(m, 'bearing_support', 'Driven-Machine Bearing (pillow block)', 'structure', join('pbk', [box('pbb', (0.1, 0.14, 0.18), (0.42, 0, -0.07), 'paint_grey'), cyl('pbr', 0.06, 0.37, 0.47, 'steel', 32, axis='X', r_in=0.051)]),
      explode=(0.3, 0, -0.2), ref='tc_hub', section='keep')
    m.flow('torque', [(-0.45, 0, 0.0), (-0.2, 0.004, 0.25), (-0.08, 0.004, 0.16), (0.0, 0.004, 0.07), (0.55, 0, 0.0)], 'power', 0.006, 0.08)
    _ov(m, 'pressure', [lathe(f'sz{k}', [(0.09, -0.134), (0.225, -0.134), (0.225, -0.031), (0.09, -0.031)], 'pressure_6', 6, a0=TAU * k / 8 - 0.3, a1=TAU * k / 8 + 0.3, axis='X', cap_mat='pressure_6') for k in range(8)],
        'Soft in torsion: detunes and damps vibration', 'A reciprocating engine delivers torque in pulses (here 6 per revolution). The soft rubber element lets the flywheel and the driven hub twist relative '
        'to each other, so the large flywheel oscillation (yellow mark) is strongly reduced at the hub. Choosing the torsional stiffness moves the system\'s torsional natural frequencies away from the '
        'engine firing orders (a torsional vibration analysis, TVA), and rubber hysteresis damps what remains; the damping heat must stay within the element\'s allowable power loss.')
    return m.export(out)


# =============================================================== EQ-331 Shaft sleeve
def shaft_sleeve(out):
    m = _model('shaft_sleeve', 'Pump Shaft Sleeve (Hook-Type) under the Packing, with Impeller Hub & Nut')
    sh = [cyl('sh', 0.03, -0.42, 0.12, 'steel', 48, axis='X', ch=0.002), cyl('sht', 0.024, -0.47, -0.42, 'steel_dark', 24, axis='X'), box('sk', (0.05, 0.01, 0.008), (0.08, 0, 0.032), 'steel_dark'),
          cyl('ihb', 0.055, -0.42, -0.33, 'bronze', 64, axis='X', r_in=0.03), cyl('ihn', 0.04, -0.47, -0.42, 'steel', 6, axis='X', r_in=0.024), box('ihk', (0.06, 0.01, 0.008), (-0.38, 0, 0.032), 'steel_dark')]
    psh = P(m, 'shaft_impeller', 'Shaft, Impeller Hub, Key & Impeller Nut (turning)', 'rotating_element', sh, explode=(0, -0.35, 0), ref='ss_shaft', section='keep')
    psh.spin('X', 2)
    sv = csg('sv', [cyl('svo', 0.042, -0.33, -0.05, 'chrome', 96, axis='X'), cyl('svh', 0.05, -0.33, -0.32, 'chrome', 96, axis='X')],
             [cyl('svi', 0.0302, -0.34, -0.04, 'chrome', 64, axis='X'), cyl('svg', 0.0435, -0.215, -0.16, 'chrome', 96, axis='X', r_in=0.0405)], 'chrome')
    P(m, 'sleeve', 'Replaceable Sleeve (hard-coated: e.g. ceramic / tungsten carbide / hardened stainless) — shows wear groove', 'sleeve', sv, explode=(0.35, 0.2, 0), ref='ss_sleeve')
    P(m, 'sleeve_seals', 'Sleeve O-ring & Gasket (stop leakage along the shaft under the sleeve)', 'seal', [_torus('so1', 0.031, 0.0015, -0.06, 'rubber'), cyl('sg', 0.05, -0.335, -0.33, 'rubber', 64, axis='X', r_in=0.031)],
      explode=(0.25, 0.15, 0.1), ref='ss_seals', section='keep')
    bx = csg('bx', [cyl('bxo', 0.085, -0.27, -0.09, 'cast_iron', 96, axis='X')], [cyl('bxi', 0.062, -0.26, -0.08, 'cast_iron', 96, axis='X'), cyl('bxt', 0.045, -0.3, -0.06, 'cast_iron', 64, axis='X')], 'cast_iron')
    P(m, 'stuffing_box', 'Stuffing Box (context)', 'casing', [bx] + [cyl(f'pk{k}', 0.0615, -0.255 + 0.032 * k, -0.255 + 0.032 * (k + 1) - 0.002, 'carbon', 96, axis='X', r_in=0.0425) for k in range(5)],
      explode=(0, 0.5, 0), ref='ss_box')
    m.flow('torque', [(0.12, 0, 0.0), (-0.33, 0, 0.0), (-0.38, 0.004, 0.05)], 'power', 0.006, 0.08)
    m.flow('leakage', [(-0.3, 0.004, 0.044), (-0.1, 0.004, 0.0435), (-0.08, 0.004, 0.06), (-0.08, 0.004, -0.1)], 'flow_discharge', 0.0025, 0.05)
    _ov(m, 'wear', [cyl('w0', 0.0445, -0.215, -0.16, 'wear_severe', 96, axis='X', r_in=0.0425), cyl('w1', 0.0445, -0.16, -0.12, 'wear_moderate', 96, axis='X', r_in=0.0425),
                    cyl('w2', 0.0445, -0.255, -0.215, 'wear_light', 96, axis='X', r_in=0.0425)], 'The sleeve wears, not the shaft',
        'Packing (and some seal elastomers) rub on the shaft surface and slowly cut a groove, worst under the rings nearest the gland. A replaceable, hard-coated sleeve takes this wear and protects the '
        'expensive shaft from wear and corrosion; it is renewed at overhaul. The sleeve is keyed or clamped to turn with the shaft, located against the impeller hub, and sealed with an O-ring so '
        'liquid cannot creep along the shaft underneath. Check sleeve runout (≈ ≤ 0.05 mm TIR typical) after fitting.')
    return m.export(out)


# =============================================================== EQ-332 Wear ring
def wear_ring(out):
    m = _model('wear_ring', 'Pump Wear Rings — Impeller (Rotating) & Casing (Stationary) with Running Clearance')
    core, shroud, info = radial_impeller('imp', 0.32, 0.03, 0.06, 0.02, n_blades=6, mat='bronze', closed=True, wrap=1.6)
    add_impeller(m, 'impeller', 'Closed Impeller (turning)', core, shroud, Matrix(), (0, 0, 0), axis='Z', explode=(0, -0.3, 0.3), ref='wr_impeller')
    rw, nk = info['r_wear'], info['neck']
    iw = cyl('iw', rw + 0.006, -nk + 0.002, -0.004, 'chrome', 96, r_in=rw - 0.0005)
    piw = P(m, 'impeller_wear_ring', 'Impeller Wear Ring (shrunk on the eye neck, turning)', 'wear_rings', [iw, box('iwm', (0.008, 0.004, nk * 0.6), (0, rw + 0.007, -nk / 2), 'steel_dark')], explode=(0, -0.2, -0.2), ref='wr_rings', section='keep')
    piw.spin('Z', 3)
    cg = rw + 0.006 + 0.0025
    cw = cyl('cw', cg + 0.012, -nk - 0.006, -0.002, 'bronze', 96, r_in=cg)
    P(m, 'casing_wear_ring', 'Casing Wear Ring (stationary; clearance exaggerated)', 'wear_rings', cw, explode=(0, 0.2, -0.25), ref='wr_rings')
    sc = lathe('sco', [(cg + 0.012, -0.25), (cg + 0.03, -0.25), (cg + 0.03, -nk - 0.01), (0.2, -nk - 0.01), (0.2, -nk + 0.005), (cg + 0.012, -nk + 0.005)], 'cast_iron', 96)
    vc = lathe('vc', [(0.17, -nk + 0.005), (0.2, -nk + 0.005), (0.2, 0.09), (0.03, 0.09), (0.03, 0.075), (0.17, 0.075)], 'cast_iron', 96)
    P(m, 'casing', 'Suction Cover & Casing (section)', 'casing', [sc, vc], explode=(0, 0.6, 0), ref='wr_casing')
    path = [(0.165, 0.004, 0.02), (0.165, 0.004, -nk + 0.0), (0.09, 0.004, -nk + 0.0), (cg - 0.0012, 0.004, -nk + 0.004), (cg - 0.0012, 0.004, -0.004), (rw - 0.01, 0.004, 0.006)]
    add_tracers(m, 'recirculation', 'Leakage from the high-pressure side back to the eye through the wear-ring clearance', path, n=6, radius=0.003, mat='flow_discharge')
    m.flow('leakage', path, 'flow_discharge', 0.0025, 0.05)
    m.flow('main_flow', [(0.03, 0.004, -0.24), (0.03, 0.004, -0.02), (0.08, 0.004, 0.03), (0.17, 0.004, 0.035)], 'water', 0.006, 0.08)
    _ov(m, 'pressure', [cyl('ph', 0.168, -nk - 0.004, -0.012, 'pressure_8', 96, r_in=cg + 0.014), cyl('pl', rw - 0.002, -0.05, -0.01, 'pressure_2', 64, r_in=rw - 0.006)], 'Clearance separates high and low pressure',
        'The impeller discharge pressure acts in the gap between the front shroud and the casing; only the narrow wear-ring clearance separates it from the low-pressure eye. Leakage through the '
        'clearance is recirculated inside the pump, wasting energy: as rings wear and clearance doubles, efficiency can fall several points. Typical diametral clearance ≈ 0.25–0.5 mm for '
        '50–150 mm rings (API 610 sets minimums by diameter and material). Replace rings when clearance reaches about twice the new value.')
    _ov(m, 'wear', [cyl('wz', cg + 0.002, -nk - 0.004, -0.004, 'wear_moderate', 96, r_in=cg - 0.001)], 'Rubbing surfaces', 'Wear rings are the sacrificial surfaces: dissimilar, galling-resistant materials and hardness differences are used.')
    return m.export(out)


# =============================================================== EQ-333 Impeller
def impeller(out):
    m = _model('impeller', 'Closed Centrifugal Pump Impeller (6 Backward-Curved Vanes)')
    core, shroud, info = radial_impeller('imp', 0.42, 0.04, 0.08, 0.03, n_blades=6, mat='bronze', closed=True, wrap=1.8)
    add_impeller(m, 'impeller', 'Impeller: Hub, Back Shroud, Vanes & Front Shroud (turning)', core, shroud, Matrix(), (0, 0, 0), axis='Z', explode=(0, -0.3, 0.2), ref='imp_impeller', revs=2)
    zb = info['z_back']
    sh = [cyl('sh', 0.03, -0.05, zb + 0.25, 'steel', 48), box('shk', (0.01, 0.008, 0.08), (0.031, 0, zb - 0.02), 'steel_dark')]
    ps = P(m, 'shaft_key', 'Shaft & Key (drive the impeller)', 'rotating_element', sh, explode=(0, 0, 0.3), ref='imp_shaft', section='keep')
    ps.spin('Z', 2)
    bv = [rotate(box(f'bv{k}', (0.09, 0.006, 0.01), (0.15, 0, info['zf'] + info['b2'] + info['t'] + 0.005), 'bronze'), TAU * (k + 0.5) / 6, 'Z') for k in range(6)]
    pbv = P(m, 'back_vanes', 'Pump-Out (Back) Vanes — reduce pressure behind the impeller and axial thrust', 'rotating_element', bv, explode=(0, 0, 0.15), ref='imp_impeller', section='keep')
    pbv.spin('Z', 2)
    flows = []
    for k in range(3):
        a0 = TAU * k / 3
        pts = [(0.0, 0.0, -0.15), (0.05 * math.cos(a0), 0.05 * math.sin(a0), -0.03)]
        for j in range(1, 9):
            r = info['r_eye'] + (info['r2'] - info['r_eye']) * j / 8
            a = a0 + 1.0 * (j / 8) ** 1.2
            pts.append((r * math.cos(a), r * math.sin(a), info['zc']))
        pts.append((0.26 * math.cos(a0 + 1.3), 0.26 * math.sin(a0 + 1.3), info['zc']))
        m.flow(f'stream_{k + 1}', pts, 'water', 0.005, 0.08)
    _ov(m, 'pressure', [cyl(f'pr{k}', r1, info['zc'] - 0.003, info['zc'] + 0.003, f'pressure_{lev}', 96, r_in=r0) for k, (r0, r1, lev) in enumerate(((0.06, 0.1, 1), (0.1, 0.14, 3), (0.14, 0.18, 5), (0.18, 0.21, 8)))],
        'Pressure and velocity rise outward', 'Liquid enters the eye axially, turns into the vane passages and is flung outward. The vanes add angular momentum (Euler: H ≈ u₂·c_u2 / g), so both pressure '
        'and velocity rise from eye to tip; the volute or diffuser then converts much of the velocity into pressure. Backward-curved vanes give a stable, falling head curve. Head scales with tip speed '
        'squared (u₂ = π·D·n), so trimming the diameter lowers head (affinity laws). Shrouds, balance holes and back vanes manage leakage and axial thrust; the impeller is dynamically balanced (e.g. ISO 21940 G6.3).')
    return m.export(out)


# ===================================================================== metadata
def _std(*items):
    return [{'id': i, 'title': t, 'relevance': r, 'edition': 'to be verified'} for i, t, r in items]


def _c(fn, cons, mat, op='—', fm=('—',), insp=('Visual',)):
    return C(fn, cons, mat, op, list(fm), list(insp))


def _comp(*items):
    out = {}
    for ref, *w in items:
        out[ref] = _c(w[0], w[1], w[2], w[3] if len(w) > 3 else '—', w[4] if len(w) > 4 else ('—',), w[5] if len(w) > 5 else ('Visual',))
    return out


_SEAL = _std(('API 682', 'Pumps — shaft sealing systems for centrifugal and rotary pumps', 'Seal types, arrangements, flush plans.'), ('ISO 21049', 'Pumps — shaft sealing systems', 'Equivalent of API 682.'))
_BRG = _std(('ISO 281', 'Rolling bearings — dynamic load ratings and rating life', 'Bearing life.'), ('API 610', 'Centrifugal pumps for petroleum, petrochemical and natural gas industries', 'Bearing & housing requirements.'))
_CPL = _std(('API 671', 'Special-purpose couplings for petroleum, chemical and gas industry services', 'Couplings.'), ('AGMA 9000 / 9002', 'Flexible couplings — balance, bores and keyways', 'Coupling practice.'))
_PMP = _std(('API 610', 'Centrifugal pumps for petroleum, petrochemical and natural gas industries', 'Clearances, materials.'), ('ISO 21940-11', 'Mechanical vibration — rotor balancing', 'Balance grades.'))

META = {
    'labyrinth_seal': {'summary': 'A labyrinth seal is a non-contacting shaft seal: a series of knife-edge teeth with tiny clearances throttles the gas leaking along the shaft step by step, keeping leakage low without any rubbing contact.',
                       'classification': {'family': 'Sealing systems', 'type': 'Straight-through stator labyrinth'}, 'model_configuration': {'animation': 'Shaft turns; leakage zig-zags through tooth clearances'},
                       'standards': _std(('API 617', 'Axial and centrifugal compressors and expander-compressors', 'Shaft and interstage seals.'),), 'references': ['Bloch — A Practical Guide to Compressor Technology'],
                       'components': _comp(('lab_stator', 'Throttles leakage.', 'Ring with knife-edge teeth and cavities.', 'Aluminium / abradable / steel.', 'Radial clearance ≈ 0.1–0.5 mm (size dependent).', ['Tooth rub / mushrooming → larger clearance'], ['Measure clearance at overhaul']),
                                           ('lab_casing', 'Holds the seal, buffer port.', 'Casing / diaphragm.', 'Cast iron / steel.'),
                                           ('lab_shaft', 'Rotor surface for the seal.', 'Shaft.', 'Alloy steel.', '—', ['Rub marks'], ['Runout']))},
    'oil_seal': {'summary': 'A radial oil seal (lip seal) keeps lubricant in a bearing housing and dirt out. An elastomer lip, loaded by a garter spring, runs on a smooth shaft with a thin oil film.',
                 'classification': {'family': 'Sealing systems', 'type': 'Radial shaft seal with garter spring and dust lip'}, 'model_configuration': {'animation': 'Shaft turns; oil pumped back at the lip'},
                 'standards': _std(('ISO 6194', 'Rotary shaft lip-type seals', 'Dimensions & testing.'), ('DIN 3760', 'Radial shaft seals', 'Designs.')), 'references': ['SKF / Freudenberg seal handbooks'],
                 'components': _comp(('os_housing', 'Holds the seal.', 'Bore with chamfer and shoulder.', 'Cast iron/steel.'), ('os_case', 'Press-fit and stiffness.', 'Metal case.', 'Steel.'),
                                     ('os_lip', 'Seals oil, excludes dirt.', 'Main lip and dust lip.', 'NBR / FKM / PTFE.', 'Low pressure, ≤ ≈ 10–30 m/s.', ['Hardening by heat', 'Lip wear', 'Shaft groove'], ['Leak check']),
                                     ('os_spring', 'Maintains lip load.', 'Garter spring.', 'Stainless/steel.'), ('os_shaft', 'Counter-face.', 'Ground, hardened shaft.', 'Steel.', '—', ['Grooving'], ['Surface finish']))},
    'gland_packing_assembly': {'summary': 'A gland packing assembly seals a pump shaft with compressed rings of braided packing in a stuffing box. A small controlled leakage lubricates and cools the packing; a lantern ring can feed flush water.',
                               'classification': {'family': 'Sealing systems', 'type': 'Compression packing with lantern ring'}, 'model_configuration': {'animation': 'Shaft turns; gland takes up; leakage drips'},
                               'standards': _std(('Fluid Sealing Association — Compression packing technical manual', 'Packing practice', 'Installation guidance.'),), 'references': ['FSA/ESA packing manual'],
                               'components': _comp(('gp_box', 'Houses the packing.', 'Stuffing box with throat bushing.', 'Cast iron/steel.'), ('gp_packing', 'Throttle leakage.', 'Braided rings, staggered joints.', 'PTFE/graphite/aramid.', '—', ['Burning (over-tight)', 'Extrusion'], ['Leak rate']),
                                                   ('gp_lantern', 'Distribute flush.', 'Split ring with holes.', 'Bronze/PTFE.'), ('gp_gland', 'Compress packing.', 'Gland follower, studs, nuts.', 'Stainless/steel.', '—', ['Cocked gland'], ['Even gap check']),
                                                   ('gp_sleeve', 'Wear surface.', 'Hard-coated sleeve on shaft.', 'Stainless/ceramic.', '—', ['Grooving'], ['Inspect at repack']))},
    'thrust_bearing_assembly': {'summary': 'A tilting-pad thrust bearing carries a rotor\'s axial load on hydrodynamic oil films. Each pad pivots so an oil wedge forms against the thrust collar; double-acting units carry thrust in both directions.',
                                'classification': {'family': 'Bearings', 'type': 'Double-acting tilting-pad (Kingsbury/Michell) thrust bearing'}, 'model_configuration': {'animation': 'Collar turns; oil carried into pad wedges'},
                                'standards': _std(('API 617 / API 612', 'Compressors / steam turbines', 'Thrust bearing requirements.'),), 'references': ['Kingsbury / Waukesha bearing handbooks'],
                                'components': _comp(('tb_shaft', 'Rotor.', 'Shaft.', 'Alloy steel.'), ('tb_collar', 'Transfers thrust.', 'Collar shrunk or integral.', 'Steel.', '—', ['Face scoring'], ['Runout']),
                                                    ('tb_pads', 'Carry thrust on oil film.', 'Steel shoes, babbitt faces, pivots.', 'Steel + tin babbitt.', 'Film ≈ 10–50 µm.', ['Wiping (overload/oil loss)', 'Fatigue'], ['Pad RTD temperature']),
                                                    ('tb_carrier', 'Locates pads.', 'Base rings / levelling links.', 'Steel.'), ('tb_housing', 'Contains oil.', 'Housing, oil inlet/drain.', 'Steel/cast iron.'))},
    'journal_bearing': {'summary': 'A hydrodynamic journal bearing supports a rotating shaft on a pressurised oil film generated by the shaft\'s own rotation in a slightly larger, babbitt-lined bore.',
                        'classification': {'family': 'Bearings', 'type': 'Plain split sleeve bearing'}, 'model_configuration': {'animation': 'Journal turns; oil swirls into the converging gap'},
                        'standards': _std(('ISO 7902', 'Hydrodynamic plain journal bearings under steady-state conditions', 'Calculation.'),), 'references': ['Khonsari & Booser — Applied Tribology'],
                        'components': _comp(('jb_journal', 'Rotating shaft.', 'Ground journal.', 'Steel.', '—', ['Scoring'], ['Proximity probes']), ('jb_lining', 'Running surface.', 'Babbitt lining with grooves.', 'Tin babbitt.', '—', ['Wiping', 'Fatigue cracking'], ['Temperature']),
                                            ('jb_shell', 'Support lining.', 'Steel shell halves.', 'Steel.'), ('jb_pedestal', 'Support and oil supply.', 'Pedestal & cap.', 'Cast iron.'),
                                            ('jb_film', 'Carries load.', 'Hydrodynamic oil film.', 'Turbine oil.', '—', ['Oil whirl'], ['Vibration']))},
    'bearing_housing': {'summary': 'A pump bearing housing holds the radial and thrust bearings that support the pump shaft, with an oil bath, oil ring, constant-level oiler and bearing isolators.',
                        'classification': {'family': 'Mechanical components', 'type': 'Oil-ring lubricated bearing frame'}, 'model_configuration': {'animation': 'Shaft, balls and oil ring turn; oil splashes'},
                        'standards': _BRG, 'references': ['API 610', 'SKF bearing handbook'],
                        'components': _comp(('bh_housing', 'Supports bearings, holds oil.', 'Finned housing with sump.', 'Cast iron.'), ('bh_shaft', 'Transmits torque.', 'Stepped shaft.', 'Alloy steel.'),
                                            ('bh_bearings', 'Carry radial and thrust loads.', 'Deep-groove + duplex angular-contact ball bearings.', 'Bearing steel.', 'L10 ≥ 25,000 h (API 610 typical).', ['Contamination', 'Over-lubrication', 'Misalignment'], ['Vibration, temperature']),
                                            ('bh_oilring', 'Lifts oil.', 'Brass ring riding on shaft.', 'Brass.', '—', ['Ring stalls / wears'], ['Sight glass check']),
                                            ('bh_oil', 'Lubricates and cools.', 'Oil bath.', 'ISO VG 46/68 typical.'), ('bh_accessories', 'Level, breathing, sealing.', 'Oiler, breather, isolators, sight glass, drain.', '—'))},
    'mechanical_cartridge_seal': {'summary': 'A mechanical cartridge seal seals a rotating pump shaft with two lapped faces — one rotating, one stationary — pressed together by springs. It comes pre-assembled on a sleeve with its gland for easy, correct installation.',
                                  'classification': {'family': 'Sealing systems', 'type': 'Single pusher cartridge seal, Plan 11'}, 'model_configuration': {'animation': 'Springs and collar turn with the shaft; flush enters the chamber'},
                                  'standards': _SEAL, 'references': ['API 682'],
                                  'components': _comp(('mcs_chamber', 'Houses the seal.', 'Seal chamber.', 'Cast iron/steel.'), ('mcs_gland', 'Holds seat, ports.', 'Gland plate with F/Q/D ports, setting clips.', 'Stainless.'),
                                                      ('mcs_faces', 'Seal.', 'Rotating carbon face + stationary SiC seat.', 'Carbon / SiC.', 'Film ≈ 0.5–1 µm.', ['Dry running', 'Thermal cracking', 'Chipping'], ['Leakage, temperature']),
                                                      ('mcs_sleeve', 'Carries rotating parts.', 'Sleeve with O-ring.', 'Stainless.'), ('mcs_springs', 'Close the faces; drive.', 'Multiple springs, retainer, drive collar.', 'Hastelloy/stainless.', '—', ['Clogging (hang-up)'], ['Inspect']),
                                                      ('mcs_shaft', 'Pump shaft.', 'Shaft.', 'Steel.'))},
    'expansion_coupling': {'summary': 'An expansion (axial-float) gear coupling joins two shafts while letting one slide axially as it grows with temperature. Crowned hub teeth mesh with a sleeve\'s internal teeth and also accept small misalignment.',
                           'classification': {'family': 'Couplings', 'type': 'Double-engagement gear coupling'}, 'model_configuration': {'animation': 'Both shafts turn; driven shaft floats axially'},
                           'standards': _CPL, 'references': ['API 671', 'AGMA coupling standards'],
                           'components': _comp(('ec_hubs', 'Mount on shafts.', 'Keyed hubs.', 'Steel.'), ('ec_teeth', 'Transmit torque, allow float.', 'Crowned external teeth.', 'Hardened steel.', '—', ['Tooth wear (no lubricant)', 'Lock-up'], ['Inspect teeth']),
                                               ('ec_sleeve', 'Engage teeth, contain lubricant.', 'Flanged sleeve halves, seals, bolts.', 'Steel.', '—', ['Grease loss'], ['Re-grease interval']))},
    'universal_joint': {'summary': 'A universal (Cardan) joint connects two shafts at an angle using two yokes and a cross with needle bearings. It transmits torque through the angle, but a single joint makes the output speed fluctuate.',
                        'classification': {'family': 'Couplings', 'type': 'Single Cardan joint'}, 'model_configuration': {'animation': 'Input turns uniformly; output and cross move non-uniformly'},
                        'standards': _std(('ISO 12667 / maker standards', 'Cardan shafts', 'Ratings (to be verified).'),), 'references': ['Machinery\'s Handbook'],
                        'components': _comp(('uj_yokes', 'Connect shafts to the cross.', 'Forged yokes with bearing caps.', 'Alloy steel.'), ('uj_cross', 'Pivot between yokes.', 'Cross with four journals, needle bearings.', 'Case-hardened steel.', '—', ['Brinelling', 'Needle wear'], ['Free play']),
                                            ('uj_supports', 'Support shafts.', 'Pillow blocks.', '—'))},
    'torsional_coupling': {'summary': 'A highly flexible torsional coupling links an engine flywheel to a driven shaft through a soft rubber element. It tunes the system\'s torsional natural frequencies and damps the engine\'s torque pulses.',
                           'classification': {'family': 'Couplings', 'type': 'Rubber-element flywheel coupling'}, 'model_configuration': {'animation': 'Flywheel oscillates strongly; hub much less'},
                           'standards': _std(('DNV / class rules', 'Torsional vibration calculations', 'Marine/genset (to be verified).'),), 'references': ['Vulkan / Geislinger catalogues'],
                           'components': _comp(('tc_flywheel', 'Driving side.', 'Flywheel and outer flange.', 'Cast iron/steel.'), ('tc_element', 'Torsional flexibility and damping.', 'Rubber segments.', 'NR/SBR/silicone.', 'Allowable heat (damping power).', ['Overheating, cracking', 'Ageing'], ['Visual, twist marks']),
                                               ('tc_hub', 'Driven side.', 'Hub and shaft.', 'Steel.'))},
    'shaft_sleeve': {'summary': 'A shaft sleeve is a replaceable, hard-wearing tube fitted over the pump shaft where packing or seals run, so the sleeve wears instead of the shaft.',
                     'classification': {'family': 'Pump components', 'type': 'Hook-type sleeve'}, 'model_configuration': {'animation': 'Shaft turns; sleeve slides off in exploded view'},
                     'standards': _PMP, 'references': ['API 610'],
                     'components': _comp(('ss_shaft', 'Transmit torque.', 'Shaft, impeller hub, nut.', 'Steel.'), ('ss_sleeve', 'Wear surface.', 'Hard-coated sleeve.', 'Stainless + ceramic/WC.', '—', ['Grooving', 'Corrosion'], ['Runout, diameter']),
                                         ('ss_seals', 'Stop leakage under the sleeve.', 'O-ring and gasket.', 'Elastomer.'), ('ss_box', 'Context.', 'Stuffing box and packing.', 'Cast iron.'))},
    'wear_ring': {'summary': 'Wear rings are renewable rings on the impeller eye and in the casing that form a small running clearance between high- and low-pressure zones, limiting internal leakage.',
                  'classification': {'family': 'Pump components', 'type': 'Impeller & casing wear rings'}, 'model_configuration': {'animation': 'Impeller turns; leakage recirculates through the clearance'},
                  'standards': _PMP, 'references': ['API 610'],
                  'components': _comp(('wr_impeller', 'Adds energy.', 'Closed impeller.', 'Bronze/stainless.'), ('wr_rings', 'Limit leakage.', 'Impeller and casing wear rings.', 'Dissimilar hard materials.', 'Clearance per API 610 table.', ['Wear → efficiency loss', 'Galling'], ['Measure clearance']),
                                      ('wr_casing', 'Pressure boundary.', 'Suction cover, casing.', 'Cast iron/steel.'))},
    'impeller': {'summary': 'A centrifugal pump impeller is a rotating wheel with curved vanes between two shrouds. It takes liquid in at the eye and throws it outward, adding pressure and velocity.',
                 'classification': {'family': 'Pump components', 'type': 'Closed radial impeller, 6 backward-curved vanes'}, 'model_configuration': {'animation': 'Impeller turns; streamlines spiral outward'},
                 'standards': _PMP, 'references': ['Gülich — Centrifugal Pumps'],
                 'components': _comp(('imp_impeller', 'Adds energy to the liquid.', 'Hub, shrouds, vanes, back vanes.', 'Bronze/cast iron/stainless/duplex.', '—', ['Cavitation erosion', 'Imbalance', 'Corrosion'], ['Visual, balance check']),
                                     ('imp_shaft', 'Drives impeller.', 'Shaft and key.', 'Steel.'))},
}
BUILDERS = {k: globals()[k] for k in META}
