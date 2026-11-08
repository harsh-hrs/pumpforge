"""Alumina Refinery (Bayer process) — EQ-271 … EQ-283: bauxite handling, grinding, digestion, flash, desilication,
precipitation, classification and residue washing / settling."""
import math
from mathutils import Matrix, Vector
from pumpforge.core import Model, lathe, cyl, box, csg, join, rotate, extrude_poly, TAU, OPERATE_FRAMES
from pumpforge.valvekit import P, keys_loop, smooth_pulse
from pumpforge.parts import hollow_pipe, pressure_gauge, add_tracers
from pumpforge.vesselkit import vessel, nozzle, legs, droplets, liquid_v, half, animate_level, helix_coil
from pumpforge.handlingkit import rocks_along, rock, belt_loop
from pumpforge.plantkit import thickener, agitated_tank, hydrocyclone, drum, particles_path, ball
from pumpforge.shapes import sweep_tube
from pumpforge.common_meta import C
from pumps._eq_thermal_a import _bands_z, _bands_x, _pump

CAT = '12 · Alumina Refinery (Bayer Process)'


def _model(pid, title):
    return Model(pid, title, CAT, META[pid])


def _press(m, objs, title, desc, kind='pressure'):
    m.overlay(kind, join(kind, objs), title, desc, split=True)


def _drum_machine(m, R, X0, X1, CZ, label, ref, liner_mat='rubber', girth=True, tyres=True, revs=1.0):
    """Horizontal rotating drum: split static shell with liners/lifters, rotating girth gear + tyres (keep), rollers/bearings, drive."""
    sh = [cyl('ds', R + 0.03, X0, X1, 'paint_grey', 96, axis='X', center=(0, 0, CZ), r_in=R), cyl('dl', R, X0, X1, liner_mat, 96, axis='X', center=(0, 0, CZ), r_in=R - 0.04)]
    sh += [rotate(box(f'lf{k}', (X1 - X0 - 0.1, 0.05, 0.07), ((X0 + X1) / 2, 0, CZ - R + 0.06), liner_mat), TAU * k / 12, 'X', (0, 0, CZ)) for k in range(12)]
    P(m, 'shell', f'{label}: Shell with Liners / Lifters (rotates)', 'casing', sh, explode=(0, 0.8, 0), ref=ref + '_shell')
    rot = []
    if tyres:
        rot += [cyl(f'ty{k}', R + 0.1, x - 0.06, x + 0.06, 'steel', 96, axis='X', center=(0, 0, CZ), r_in=R + 0.03) for k, x in enumerate((X0 + 0.25, X1 - 0.25))]
    if girth:
        rot += [cyl('gg', R + 0.16, (X0 + X1) / 2 - 0.05, (X0 + X1) / 2 + 0.05, 'steel_dark', 96, axis='X', center=(0, 0, CZ), r_in=R + 0.03)]
        rot += [rotate(box(f'gt{k}', (0.1, 0.03, 0.04), ((X0 + X1) / 2, 0, CZ + R + 0.17), 'steel_dark'), TAU * k / 48, 'X', (0, 0, CZ)) for k in range(48)]
    pr = P(m, 'girth_tyres', f'{label}: Riding Tyres & Girth Gear (turn with the shell)', 'rotating_element', rot, explode=(0, -0.9, 0), ref=ref + '_drive', section='keep', pivot=(0, 0, CZ))
    pr.spin('X', revs)
    return pr


# =============================================================== EQ-271 Bauxite stockpile reclaimer (bridge scraper)
def bauxite_stockpile_reclaimer(out):
    m = _model('bauxite_stockpile_reclaimer', 'Bridge-Type Scraper Reclaimer for a Bauxite Blending Stockpile')
    pile = extrude_poly('pl', [(-1.5, 0.0), (1.5, 0.0), (0.0, 1.3)], -2.4, 1.45, 'bauxite', plane='YZ')
    face = extrude_poly('pf', [(-1.5, 0.0), (1.5, 0.0), (0.0, 1.3)], 1.45, 1.55, 'red_mud', plane='YZ')
    P(m, 'stockpile', 'Chevron-Stacked Bauxite Blending Pile (reclaimed across the full face)', 'material', [pile, face], explode=(0, 0, 0), ref='br_pile', section='keep')
    rl = [box(f'rl{s}', (5.0, 0.08, 0.08), (0, s * 1.9, 0.04), 'steel_dark') for s in (-1, 1)]
    P(m, 'rails', 'Travel Rails', 'structure', rl, explode=(0, 0, -0.2), ref='br_rails', section='keep')
    trav = lambda t: 0.08 * math.sin(TAU * t)
    br = [box('gd', (0.4, 4.2, 0.35), (1.75, 0, 1.75), 'paint_yellow')] + [box(f'lg{s}', (0.3, 0.3, 1.6), (1.75, s * 1.9, 0.9), 'paint_yellow') for s in (-1, 1)] + \
         [box(f'tr{s}', (0.8, 0.35, 0.2), (1.75, s * 1.9, 0.18), 'paint_yellow') for s in (-1, 1)] + [box('cab', (0.4, 0.4, 0.4), (2.0, 1.6, 1.4), 'paint_grey')]
    pb = P(m, 'bridge', 'Portal Bridge with Travel Bogies & Operator Cab', 'structure', br, explode=(0.5, 0, 0.6), ref='br_bridge', section='keep')
    keys_loop(m, pb, lambda t: (trav(t), 0, 0))
    hr = [box('hrf', (0.06, 3.0, 0.06), (1.62, 0, 0.12), 'steel')]
    for s in (-1, 1):
        a, b = Vector((1.62, s * 1.5, 0.12)), Vector((1.62, 0.0, 1.3))
        d = b - a
        bm = box(f'hs{s}', (0.06, d.length, 0.06), (0, 0, 0), 'steel')
        bm.data.transform(Matrix.Translation((a + b) / 2) @ Matrix.Rotation(math.atan2(d.z, -d.y) if s > 0 else -math.atan2(d.z, d.y), 4, 'X'))
        hr.append(bm)
    for k in range(9):
        y = -1.2 + 0.3 * k
        zt = 1.3 * (1 - abs(y) / 1.5)
        hr += [cyl(f'tn{k}_{j}', 0.012, 1.45, 1.62, 'steel', 6, axis='X', center=(0, y, z)) for j, z in enumerate([0.2 + (zt - 0.2) * q / 3 for q in range(4)]) if z < zt - 0.05]
    ph = P(m, 'harrow', 'Harrow (raking frame with tines — loosens the whole pile face)', 'reclaiming', hr, explode=(0.4, -0.5, 0.4), ref='br_harrow', section='keep')
    keys_loop(m, ph, lambda t: (trav(t), 0.25 * math.sin(TAU * 2 * t), 0))
    pf = m.part('scraper', 'Chain Scraper Flights (drag material to the side conveyor)', 'reclaiming', explode=(0.3, 0, -0.2), info={'ref': 'br_scraper'})
    n = 10
    for i in range(n):
        ms = pf.add(box(f'sf{i}', (0.18, 0.04, 0.12), (0, 0, 0), 'steel_dark'), smooth_angle=30)
        lk = []
        for f in range(OPERATE_FRAMES + 1):
            s_ = ((f / OPERATE_FRAMES) * 2 + i / n) % 1.0
            if s_ < 0.5:
                pos = (1.5, -1.6 + 3.4 * s_ / 0.5, 0.1)
            else:
                pos = (1.5, 1.8 - 3.4 * (s_ - 0.5) / 0.5, 0.3)
            lk.append((1 + f, (pos[0] + trav(f / OPERATE_FRAMES), pos[1], pos[2])))
        ms.location = lk[0][1]
        m.keyframes(ms, 'Operate', 'location', lk)
    sc = [box('sb', (0.3, 3.6, 0.04), (1.5, 0.1, 0.03), 'steel_dark'), cyl('sp1', 0.12, 1.4, 1.6, 'steel', 24, axis='X', center=(0, 1.8, 0.2)),
          cyl('sp2', 0.12, 1.4, 1.6, 'steel', 24, axis='X', center=(0, -1.6, 0.2)), box('sdm', (0.3, 0.3, 0.3), (1.5, 2.1, 0.35), 'paint_blue')]
    psc = P(m, 'scraper_frame', 'Scraper Chain Sprockets & Drive', 'reclaiming', sc, explode=(0.3, 0, -0.3), ref='br_scraper', section='keep')
    keys_loop(m, psc, lambda t: (trav(t), 0, 0))
    belt_loop(m, 'yc', -2.4, 2.4, 0.35, 0.1, 0.5, revs=2, markers=8, label='Yard Belt Conveyor (to grinding)', y=-2.2, foot_z=0.0, idlers=False)
    rocks_along(m, 'bauxite', 'Reclaimed Bauxite on the Yard Conveyor', [(1.5, 0.52), (-2.4, 0.52)], 8, r=0.05, mat='bauxite', y=-2.2)
    m.flow('reclaim', [(1.5, 1.2, 0.5), (1.5, 0.0, 0.15), (1.5, -1.9, 0.15), (1.5, -2.2, 0.5), (-2.6, -2.2, 0.5)], 'sand', 0.03, 0.4)
    _press(m, [box('bz', (0.04, 3.0, 0.04), (1.47, 0, 0.7), 'pressure_6')], 'Why full-face reclaiming blends the bauxite',
           'The pile is stacked in many thin layers (chevron) along its length, each layer slightly different in quality. Raking the whole cross-section at once takes a slice of every layer, '
           'so the reclaimed bauxite has a much more uniform alumina, silica and moisture content — critical for stable digestion (blending ratio often 5:1 or better).')
    return m.export(out)


# =============================================================== EQ-272 Bauxite washing drum
def bauxite_washing_drum(out):
    m = _model('bauxite_washing_drum', 'Bauxite Washing (Scrubbing) Drum with Trommel Discharge Screen')
    R, X0, X1, CZ = 0.6, -1.3, 1.1, 1.0
    _drum_machine(m, R, X0, X1, CZ, 'Scrubbing Drum', 'bw', revs=1.0)
    tr = [cyl('ts', R * 0.85, X1, X1 + 0.7, 'steel', 64, axis='X', center=(0, 0, CZ), r_in=R * 0.83)] + [rotate(cyl(f'th{k}', 0.02, X1 + 0.05, X1 + 0.65, 'steel_dark', 6, axis='X', center=(0, 0, CZ - R * 0.84)), TAU * k / 16, 'X', (0, 0, CZ)) for k in range(16)]
    ptr = P(m, 'trommel', 'Trommel Discharge Screen (separates washed lumps from fines/clay)', 'screen', tr, explode=(0.6, -0.5, 0), ref='bw_trommel', section='split')
    sp = [cyl('sh', 0.035, X0 - 0.4, X1 - 0.2, 'stainless', 16, axis='X', center=(0, 0, CZ + 0.25))] + [cyl(f'sn{k}', 0.012, CZ + 0.18, CZ + 0.25, 'brass', 8, center=(X0 + 0.2 + 0.3 * k, 0, 0)) for k in range(7)]
    P(m, 'spray_header', 'Water Spray Header & Nozzles', 'water', sp, explode=(0, -0.4, 0.5), ref='bw_spray', section='keep')
    fc = join('fc', [box('fch', (0.5, 0.6, 0.4), (X0 - 0.45, 0, CZ + 0.6), 'paint_grey'), box('fcs', (0.6, 0.35, 0.08), (X0 - 0.1, 0, CZ + 0.15), 'paint_grey')])
    P(m, 'feed_chute', 'Feed Chute (crushed bauxite + water)', 'chutes', fc, explode=(-0.5, 0, 0.3), ref='bw_chutes', section='keep')
    ch = [box('uc', (0.8, 1.0, 0.5), (X1 + 0.35, 0, 0.25), 'paint_grey'), box('oc', (0.4, 0.8, 0.6), (X1 + 0.95, 0, 0.5), 'paint_grey')]
    P(m, 'discharge_chutes', 'Undersize (slimes) Sump & Oversize (washed bauxite) Chute', 'chutes', ch, explode=(0.5, 0, -0.3), ref='bw_chutes', section='keep')
    sup = [cyl(f'rr{k}{s}', 0.12, x - 0.07, x + 0.07, 'steel', 24, axis='X', center=(0, s * 0.45, CZ - R - 0.08)) for k, x in enumerate((X0 + 0.25, X1 - 0.25)) for s in (-1, 1)]
    sup += [box(f'bs{k}', (0.4, 1.3, CZ - R - 0.15), (x, 0, (CZ - R - 0.15) / 2), 'paint_grey') for k, x in enumerate((X0 + 0.25, X1 - 0.25))]
    sup += [cyl('pn', 0.1, -0.05, 0.05, 'steel', 24, axis='X', center=(0, R + 0.27, CZ - 0.1)), box('gbx', (0.35, 0.3, 0.3), (0.0, R + 0.55, CZ - 0.35), 'paint_blue'), cyl('mot', 0.13, R + 0.7, R + 1.15, 'paint_motor', 24, axis='Y', center=(0.0, 0, CZ - 0.35))]
    P(m, 'supports_drive', 'Support Rollers, Bases & Drive (motor, reducer, pinion)', 'structure', sup, explode=(0, 0, -0.4), ref='bw_drive', section='keep')
    def tumble(i, s):
        x = X0 + 0.1 + (X1 + 0.6 - X0 - 0.1) * s
        ph = (s * 7 + i * 0.29) % 1.0
        r = R - 0.12
        if ph < 0.7:                                    # carried up the rising wall
            a = math.radians(-150 + 90 * ph / 0.7)
            return (x, 0.05 + 0.08 * (i % 3), CZ + r * math.sin(a))
        u = (ph - 0.7) / 0.3                            # falls back to the toe
        z0, z1 = CZ + r * math.sin(math.radians(-60)), CZ + r * math.sin(math.radians(-150))
        return (x, 0.05 + 0.08 * (i % 3), z0 + (z1 - z0) * u + 0.15 * math.sin(math.pi * u))
    particles_path(m, 'lumps', 'Bauxite Lumps Tumbling and Scrubbing (clay is washed off)', tumble, 14, mat='bauxite', r=0.04)
    droplets(m, 'spray', 'Wash Water Sprays', X0 + 0.2, X1 - 0.3, CZ + 0.17, CZ - 0.3, n=8, mat='water', y=0.05, r=0.012)
    m.flow('ore', [(X0 - 0.45, 0, CZ + 0.9), (X0 - 0.1, 0, CZ + 0.15), (X1, 0.05, CZ - R + 0.15), (X1 + 0.7, 0.05, CZ - R * 0.7), (X1 + 0.95, 0, 0.5)], 'sand', 0.025, 0.4)
    m.flow('slimes', [(X1 + 0.35, 0.1, CZ - R * 0.85), (X1 + 0.35, 0.1, 0.3)], 'water', 0.02, 0.2)
    _press(m, [cyl('rz', R + 0.2, X0, X1, 'pressure_5', 64, axis='X', center=(0, 0, CZ), r_in=R + 0.18)], 'Attrition scrubbing removes clay and reactive silica',
           'Lifters raise the bauxite and drop it, so lumps rub and impact each other in water. Fine clay (often rich in reactive silica, which costs caustic soda in digestion) is washed off and '
           'leaves with the trommel undersize. Drum speed is typically ~ 50–75 % of critical speed.')
    return m.export(out)


# =============================================================== EQ-273 Bauxite grinding mill
def bauxite_grinding_mill(out):
    m = _model('bauxite_grinding_mill', 'Bauxite Ball Mill (Wet Grinding in Spent Liquor, Overflow Discharge)')
    R, X0, X1, CZ = 0.7, -1.0, 1.0, 1.2
    _drum_machine(m, R, X0, X1, CZ, 'Mill', 'bg', liner_mat='steel_dark', tyres=False, revs=0.7)
    hd = [lathe('hf', [(0.2, X0 - 0.35), (0.24, X0 - 0.35), (R + 0.03, X0), (R - 0.02, X0), (0.2, X0 - 0.3)], 'paint_grey', 64, axis='X', center=(0, 0, CZ)),
          lathe('hd', [(0.2, X1 + 0.35), (0.24, X1 + 0.35), (R + 0.03, X1), (R - 0.02, X1), (0.2, X1 + 0.3)], 'paint_grey', 64, axis='X', center=(0, 0, CZ)),
          cyl('tf', 0.24, X0 - 0.7, X0 - 0.35, 'steel', 48, axis='X', center=(0, 0, CZ), r_in=0.2), cyl('tdd', 0.24, X1 + 0.35, X1 + 0.75, 'steel', 48, axis='X', center=(0, 0, CZ), r_in=0.2)]
    P(m, 'heads_trunnions', 'Feed & Discharge Heads with Hollow Trunnions', 'casing', hd, explode=(0, 0.6, 0), ref='bg_heads')
    br = [box(f'pb{k}', (0.4, 0.9, CZ - 0.25), (x, 0, (CZ - 0.25) / 2), 'paint_grey') for k, x in enumerate((X0 - 0.55, X1 + 0.55))] + [cyl(f'bb{k}', 0.32, x - 0.12, x + 0.12, 'paint_blue', 48, axis='X', center=(0, 0, CZ), r_in=0.25) for k, x in enumerate((X0 - 0.55, X1 + 0.55))]
    br += [cyl('pn', 0.12, -0.08, 0.08, 'steel', 24, axis='X', center=(0, R + 0.3, CZ - 0.25)), box('gbx', (0.5, 0.45, 0.45), (0, R + 0.75, CZ - 0.5), 'paint_blue'), cyl('mot', 0.2, R + 1.0, R + 1.7, 'paint_motor', 32, axis='Y', center=(0, 0, CZ - 0.5))]
    P(m, 'bearings_drive', 'Trunnion Bearings, Pedestals & Drive (motor, gearbox, pinion)', 'drive', br, explode=(0, 0, -0.4), ref='bg_drive', section='keep')
    fs = [box('fsp', (0.4, 0.5, 0.5), (X0 - 0.95, 0, CZ + 0.2), 'paint_grey'), cyl('trs', 0.3, X1 + 0.75, X1 + 1.2, 'steel', 32, axis='X', center=(0, 0, CZ), r_in=0.28), box('dsu', (0.6, 0.8, 0.5), (X1 + 1.0, 0, 0.35), 'paint_grey')]
    P(m, 'feed_discharge', 'Feed Spout, Trommel Screen & Discharge Sump', 'chutes', fs, explode=(0.4, 0, 0), ref='bg_heads', section='keep')
    pball = m.part('balls', 'Grinding Balls & Charge (cascading / cataracting)', 'flow_tracers', explode=(0, 0, 0), info={'ref': 'flow_tracers'})
    for i in range(18):
        ph = i / 18
        ms = pball.add(ball(f'gb{i}', 0.05, 'steel'), smooth_angle=80)
        lk = []
        for f in range(OPERATE_FRAMES + 1):
            s_ = ((f / OPERATE_FRAMES) * 2 + ph) % 1.0
            x = X0 + 0.15 + (X1 - X0 - 0.3) * ((i * 0.37) % 1)
            r = R - 0.1
            if s_ < 0.65:
                a = math.radians(-115 + 95 * s_ / 0.65)
                lk.append((1 + f, (x, 0.1, CZ + r * math.sin(a))))
            else:
                u = (s_ - 0.65) / 0.35
                z0, z1 = CZ + r * math.sin(math.radians(-20)), CZ + r * math.sin(math.radians(-115))
                lk.append((1 + f, (x, 0.1, z0 + (z1 - z0) * u + 0.2 * math.sin(math.pi * u))))
        ms.location = lk[0][1]
        m.keyframes(ms, 'Operate', 'location', lk)
    chg = lathe('chg', [(0.0, X0 + 0.02), (R - 0.05, X0 + 0.02), (R - 0.05, X1 - 0.02), (0.0, X1 - 0.02)], 'steel_dark', 48, a0=math.radians(200), a1=math.radians(340), axis='X', center=(0, 0, CZ), cap_mat='steel_dark')
    P(m, 'charge', 'Ball Charge Bed (≈ 30–40 % of mill volume)', 'fluid', half(chg, 'steel_dark'), explode=(0, -0.5, -0.2), ref='bg_charge', section='keep')
    m.flow('feed', [(X0 - 0.95, 0, CZ + 0.5), (X0 - 0.6, 0, CZ), (X0 + 0.1, 0.1, CZ - 0.2)], 'sand', 0.025, 0.3)
    m.flow('slurry', [(X1 - 0.1, 0.1, CZ - 0.15), (X1 + 0.9, 0, CZ), (X1 + 1.0, 0, 0.5)], 'flow_discharge', 0.025, 0.3)
    _press(m, [cyl('cz', R + 0.2, X0, X1, 'pressure_7', 64, axis='X', center=(0, 0, CZ), r_in=R + 0.18)], 'Critical speed and grinding action',
           'The mill turns at about 65–78 % of critical speed (n_c = 42.3/√D rpm). Balls are lifted up the rising side and cascade/cataract back onto the toe of the charge, breaking bauxite by impact '
           'and attrition. Grinding in spent liquor starts the dissolution of gibbsite and produces slurry for digestion; product size is controlled by classification (screens/cyclones).')
    return m.export(out)


# =============================================================== EQ-274 Bauxite slurry mixing tank
def bauxite_slurry_mixing_tank(out):
    m = _model('bauxite_slurry_mixing_tank', 'Bauxite Slurry Mixing / Storage Tank (Agitated)')
    R, Z0, H = 0.85, 0.3, 1.7
    zt = agitated_tank(m, 'mx_', R, Z0, H, 'Slurry Tank', 'sm', liquid='bauxite', imp='hydrofoil', revs=1.2)
    nz = [hollow_pipe('fi', [(-1.6, 0, Z0 + H + 0.3), (-0.5, 0, Z0 + H + 0.3), (-0.5, 0, Z0 + H - 0.2)], 0.05, 'paint_grey', 16, bend=0.08),
          hollow_pipe('li', [(-1.6, 0.4, Z0 + H + 0.45), (-0.3, 0.4, Z0 + H + 0.45), (-0.3, 0.4, Z0 + H - 0.2)], 0.04, 'stainless', 16, bend=0.06),
          nozzle('out', (R, 0, Z0 + 0.15), (1, 0, 0), 0.06, 0.3), box('lt', (0.12, 0.12, 0.12), (0.4, 0.5, Z0 + H + 0.1), 'paint_blue_dark')]
    P(m, 'nozzles', 'Ground Bauxite Slurry Inlet, Spent-Liquor Inlet, Outlet & Level Transmitter', 'nozzles', nz, explode=(0, 0, 0.4), ref='sm_nozzles', section='keep')
    _pump(m, 'slurry_pump', 'Slurry Transfer Pump (to digestion)', R + 0.6, 0.0, 0.25, 'sm_pump', explode=(0.3, -0.3, 0))
    P(m, 'foundation', 'Ring-Wall Foundation', 'structure', cyl('fd', R + 0.1, 0.0, Z0, 'cast_iron', 96), explode=(0, 0, -0.3), ref='sm_nozzles', section='split')
    particles_path(m, 'swirl', 'Solids kept in suspension by the agitator flow', lambda i, s: ((0.2 + 0.5 * ((i * 0.31) % 1)) * math.cos(TAU * (s + i / 10)), abs((0.2 + 0.5 * ((i * 0.31) % 1)) * math.sin(TAU * (s + i / 10))) + 0.02,
                                                                                                  Z0 + 0.2 + (H - 0.5) * (0.5 + 0.5 * math.sin(TAU * (s + i * 0.2)))), 14, mat='bauxite', r=0.025)
    m.flow('slurry_in', [(-1.7, 0, Z0 + H + 0.3), (-0.5, 0, Z0 + H + 0.3), (-0.5, 0, Z0 + H - 0.3)], 'sand', 0.02, 0.3)
    m.flow('spent_liquor', [(-1.7, 0.4, Z0 + H + 0.45), (-0.3, 0.4, Z0 + H + 0.45), (-0.3, 0.4, Z0 + H - 0.3)], 'flow_suction', 0.02, 0.3)
    m.flow('to_digestion', [(R - 0.1, 0, Z0 + 0.15), (R + 0.6, 0, 0.25), (R + 1.4, 0, 0.25)], 'flow_discharge', 0.02, 0.3)
    _press(m, [cyl('sz', R + 0.05, Z0, Z0 + H, 'pressure_5', 64, r_in=R + 0.03)], 'Keeping solids in suspension',
           'The agitator must give enough upward flow to keep coarse bauxite particles off the floor (the "just-suspended" speed, Zwietering correlation). Tanks are sized for hours of residence '
           'to buffer the mills from digestion and to start pre-desilication. Solids content is typically ~ 40–55 wt % (slurry density control).')
    return m.export(out)


# =============================================================== EQ-275 Digestion autoclave
def digestion_autoclave(out):
    m = _model('digestion_autoclave', 'Digestion Autoclave Train (Agitated Pressure Vessels in Series, Live-Steam Injection)')
    R, Z0, H = 0.45, 0.6, 1.8
    xs = (-1.4, 0.0, 1.4)
    for k, x in enumerate(xs):
        agitated_tank(m, f'ac{k + 1}_', R, Z0, H, f'Autoclave {k + 1}', 'da', cx=x, liquid='red_mud', open_top=False, imp='pbt', revs=1.5, baffles=False)
    tp = []
    for k in range(2):
        a, b = xs[k], xs[k + 1]
        tp.append(hollow_pipe(f'tf{k}', [(a + R, 0, Z0 + H - 0.2), (a + R + 0.2, 0, Z0 + H - 0.2), (a + R + 0.2, 0, Z0 + 0.3), (b - R, 0, Z0 + 0.3)], 0.05, 'steel', 16, bend=0.08))
    tp += [hollow_pipe(f'st{k}', [(x - 0.25, -0.6, Z0 + H + 0.9), (x - 0.25, -0.6, Z0 + 0.4), (x - 0.25, -R + 0.05, Z0 + 0.4)], 0.03, 'steel', 12, bend=0.06) for k, x in enumerate(xs)]
    tp += [hollow_pipe('sh', [(-2.0, -0.6, Z0 + H + 0.9), (1.2, -0.6, Z0 + H + 0.9)], 0.05, 'steel', 16), nozzle('in', (xs[0] - R, 0, Z0 + 0.3), (-1, 0, 0), 0.05, 0.3), nozzle('out', (xs[2] + R, 0, Z0 + H - 0.2), (1, 0, 0), 0.05, 0.3)]
    tp += [pressure_gauge(f'pg{k}', (x, 0.3, Z0 + H + R * 0.5 + 0.05), r=0.05, facing=(0, -1, 0)) for k, x in enumerate(xs)]
    P(m, 'transfer_steam', 'Slurry Transfer Lines (overflow → bottom of next), Live-Steam Header & Injectors, Gauges', 'piping', tp, explode=(0, 0, 0.4), ref='da_piping', section='keep')
    P(m, 'supports', 'Support Legs', 'structure', [legs(f'lg{k}', R, 0.0, Z0, n=4, cx=x) for k, x in enumerate(xs)], explode=(0, 0, -0.3), ref='da_piping', section='keep')
    droplets(m, 'steam_bubbles', 'Live Steam Condensing in the Slurry', xs[0] - 0.2, xs[2] + 0.2, Z0 + 0.4, Z0 + 1.2, n=12, mat='steam', y=0.15, r=0.02)
    m.flow('slurry', [(xs[0] - R - 0.4, 0, Z0 + 0.3)] + [p_ for k in range(2) for p_ in ((xs[k], 0.05, Z0 + 0.4), (xs[k], 0.05, Z0 + H - 0.2), (xs[k] + R + 0.2, 0, Z0 + H - 0.2), (xs[k] + R + 0.2, 0, Z0 + 0.3))] + [(xs[2], 0.05, Z0 + H - 0.2), (xs[2] + R + 0.4, 0, Z0 + H - 0.2)], 'flow_discharge', 0.02, 0.4)
    m.flow('live_steam', [(-2.1, -0.6, Z0 + H + 0.9), (xs[0] - 0.25, -0.6, Z0 + H + 0.9), (xs[0] - 0.25, -0.6, Z0 + 0.4), (xs[0] - 0.25, -R + 0.05, Z0 + 0.4)], 'steam', 0.02, 0.3)
    _press(m, [cyl(f'pz{k}', R + 0.05, Z0, Z0 + H, 'pressure_8', 48, center=(x, 0, 0), r_in=R + 0.03) for k, x in enumerate(xs)], 'High temperature and pressure dissolve the alumina',
           'In digestion hot caustic liquor dissolves the alumina minerals: Al(OH)₃ + NaOH → NaAl(OH)₄. Gibbsitic bauxite digests at about 140–150 °C; boehmitic/diaspore bauxites need ~ 230–270 °C, '
           'which means pressures up to roughly 30–35 bar. Vessels in series give the residence time needed while keeping the slurry hot and well mixed.')
    return m.export(out)


# =============================================================== EQ-276 Digestion heater
def digestion_heater(out):
    m = _model('digestion_heater', 'Digestion Slurry Heater (Vertical Shell & Tube, Flash-Vapour Heated)')
    R, Z0, L = 0.4, 0.8, 2.0
    sh = csg('sh', [cyl('so', R + 0.015, Z0, Z0 + L, 'paint_grey', 64)], [cyl('si', R, Z0 - 0.1, Z0 + L + 0.1, 'paint_grey', 64)], 'paint_grey')
    ts = [cyl(f'ts{k}', R + 0.05, z, z + 0.04, 'steel', 64) for k, z in enumerate((Z0 - 0.04, Z0 + L))]
    P(m, 'shell', 'Shell (vapour side) & Tubesheets', 'casing', [sh] + ts, explode=(0, 0.6, 0), ref='dh_shell')
    hd = [vessel('th', R, 0.25, 0.012, 'paint_blue', heads=('flat', '2:1'), z0=Z0 + L + 0.04), vessel('bh', R, 0.25, 0.012, 'paint_blue', heads=('2:1', 'flat'), z0=Z0 - 0.29),
          box('pp1', (0.012, 2 * R * 0.95, 0.24), (0, 0, Z0 + L + 0.16), 'steel'), box('pp2', (0.012, 2 * R * 0.95, 0.24), (0.15, 0, Z0 - 0.16), 'steel'), box('pp3', (0.012, 2 * R * 0.95, 0.24), (-0.15, 0, Z0 - 0.16), 'steel')]
    P(m, 'channel_heads', 'Top & Bottom Channel Heads with Pass Partitions (slurry makes several passes)', 'casing', hd, explode=(0, 0, 0.5), ref='dh_heads')
    pos = [(x, y) for x in (-0.27, -0.15, -0.05, 0.05, 0.15, 0.27) for y in (-0.25, -0.12, 0.0, 0.12, 0.25) if x * x + y * y < (R - 0.06) ** 2]
    tb = [cyl(f't{i}', 0.022, Z0 - 0.04, Z0 + L + 0.04, 'steel', 10, center=(x, y, 0), r_in=0.017) for i, (x, y) in enumerate(pos)]
    tb += [cyl(f'sc{i}', 0.0175, Z0, Z0 + L, 'cast_iron', 8, center=(x, y, 0), r_in=0.014) for i, (x, y) in enumerate(pos) if y >= 0 and abs(x) < 0.1]
    P(m, 'tubes', 'Tube Bundle (slurry inside) with Scale Layer shown in Some Tubes', 'tubes', tb, explode=(0, -0.6, 0), ref='dh_tubes', section='keep')
    nz = [nozzle('vi', (0, -R, Z0 + L - 0.3), (0, -1, 0), 0.1, 0.25), nozzle('co', (0, -R, Z0 + 0.15), (0, -1, 0), 0.04, 0.2), nozzle('nc', (0.25, R * 0.9, Z0 + L - 0.1), (0, 1, 0), 0.02, 0.15),
          nozzle('si', (-0.25, 0, Z0 - 0.29 - R * 0.5), (0, 0, -1), 0.05, 0.25), nozzle('so', (0.25, 0, Z0 - 0.29 - R * 0.5), (0, 0, -1), 0.05, 0.25)]
    P(m, 'nozzles', 'Flash-Vapour Inlet, Condensate Outlet, Non-Condensable Vent, Slurry In/Out', 'nozzles', nz, explode=(0, 0, -0.3), ref='dh_nozzles', section='keep')
    P(m, 'supports', 'Support Lugs & Structure', 'structure', [box(f'sl{k}', (0.1, 0.1, Z0 + 1.0), (sx * (R + 0.15), sy * (R + 0.15), (Z0 + 1.0) / 2), 'paint_grey') for k, (sx, sy) in enumerate(((-1, -1), (-1, 1), (1, -1), (1, 1)))] +
      [rotate(box(f'lu{k}', (0.32, 0.08, 0.08), (R + 0.06, 0, Z0 + 0.96), 'paint_grey'), math.pi / 4 + k * math.pi / 2, 'Z') for k in range(4)],
      explode=(0, 0, -0.3), ref='dh_shell', section='keep')
    droplets(m, 'condensate', 'Vapour Condensing on the Tubes', -0.3, 0.3, Z0 + L - 0.2, Z0 + 0.1, n=10, mat='water', y=0.3, r=0.012)
    add_tracers(m, 'slurry', 'Slurry making Passes through the Tubes', [(-0.25, 0.06, Z0 - 0.4), (-0.25, 0.06, Z0 + L + 0.2), (0.0, 0.06, Z0 + L + 0.2), (0.1, 0.06, Z0 - 0.1), (0.25, 0.06, Z0 + L + 0.1)], n=10, radius=0.018, mat='flow_discharge')
    m.flow('vapour', [(0, -R - 0.3, Z0 + L - 0.3), (0, -0.2, Z0 + L - 0.35), (0, -0.2, Z0 + 0.3), (0, -R - 0.25, Z0 + 0.15)], 'steam', 0.02, 0.3)
    m.flow('slurry_path', [(-0.25, 0, Z0 - 0.75), (-0.25, 0, Z0 + L + 0.2), (0.25, 0, Z0 + L + 0.2), (0.25, 0, Z0 - 0.75)], 'flow_discharge', 0.015, 0.3)
    _bands_z(m, [(Z0, Z0 + L * 0.5, 5), (Z0 + L * 0.5, Z0 + L, 7)], R, 'Regenerative heating with flash vapour',
             'Vapour flashed from the hot digested slurry (multi-stage flash) is condensed in these heaters to preheat the incoming slurry — recovering most of the heat. Desilication product scale '
             '(sodalite) and titanate deposits build up inside the tubes and cut heat transfer, so heaters are taken off-line for descaling (hydro-blasting or acid) in rotation.')
    return m.export(out)


# =============================================================== EQ-277 Multi-stage flash vessel
def multi_stage_flash_vessel(out):
    m = _model('multi_stage_flash_vessel', 'Multi-Stage Flash Train (Blow-Off / Flash Tanks after Digestion)')
    xs, Rs = (-1.4, 0.0, 1.4), (0.45, 0.5, 0.55)
    Z0, L = 0.7, 1.4
    for k, (x, R) in enumerate(zip(xs, Rs)):
        v = vessel(f'fv{k}', R, L, 0.014, 'paint_grey', heads=('cone', '2:1'), z0=Z0, center=(x, 0, 0))
        P(m, f'flash_tank_{k + 1}', f'Flash Tank {k + 1} (pressure stage {k + 1})', 'vessel', v, explode=(0, 0.6, 0.2 * k), ref='mf_tanks')
        pl = P(m, f'slurry_{k + 1}', f'Slurry Level in Tank {k + 1}', 'fluid', liquid_v(f'sl{k}', R - 0.014, Z0, Z0 + 0.4, head='cone', mat='red_mud', cx=x), explode=(0, -0.3, 0), ref='mf_slurry', section='keep')
        animate_level(m, pl, Z0 + 0.39, 0.06, lambda t, k=k: 0.5 + 0.5 * math.sin(TAU * t + k))
        droplets(m, f'flash_{k + 1}', f'Vapour Flashing in Tank {k + 1}', x - 0.25, x + 0.25, Z0 + 0.45, Z0 + L, n=6, mat='steam', y=0.15, r=0.02)
    pp = []
    for k in range(2):
        a, b, Ra, Rb = xs[k], xs[k + 1], Rs[k], Rs[k + 1]
        pp.append(hollow_pipe(f'sp{k}', [(a, 0, Z0 - Ra - 0.05), (a, 0, 0.25), ((a + b) / 2, 0, 0.25), ((a + b) / 2, 0, Z0 + 0.8), (b - Rb, 0, Z0 + 0.8)], 0.05, 'steel', 16, bend=0.08))
        pp.append(box(f'cv{k}', (0.14, 0.14, 0.14), ((a + b) / 2, 0, 0.55), 'paint_blue_dark'))
    pp += [hollow_pipe(f'vp{k}', [(x, 0, Z0 + L + R * 0.5), (x, 0, Z0 + L + R * 0.5 + 0.3), (x + 0.3, 0, Z0 + L + R * 0.5 + 0.3)], 0.07, 'steel', 16, bend=0.08) for k, (x, R) in enumerate(zip(xs, Rs))]
    pp += [nozzle('in', (xs[0] - Rs[0], 0, Z0 + 0.8), (-1, 0, 0), 0.05, 0.3), nozzle('out', (xs[2], 0, Z0 - Rs[2] - 0.05), (0, 0, -1), 0.05, 0.25)]
    P(m, 'piping', 'Slurry Transfer Lines with Level-Control (choke) Valves & Vapour Lines to Heaters', 'piping', pp, explode=(0, 0, 0.4), ref='mf_piping', section='keep')
    P(m, 'supports', 'Support Legs', 'structure', [legs(f'lg{k}', R, 0.0, Z0, n=4, cx=x) for k, (x, R) in enumerate(zip(xs, Rs))], explode=(0, 0, -0.3), ref='mf_tanks', section='keep')
    m.flow('slurry', [(xs[0] - Rs[0] - 0.4, 0, Z0 + 0.8)] + [p_ for k in range(2) for p_ in ((xs[k], 0.05, Z0 + 0.3), (xs[k], 0, 0.25), ((xs[k] + xs[k + 1]) / 2, 0, 0.25), ((xs[k] + xs[k + 1]) / 2, 0, Z0 + 0.8), (xs[k + 1], 0.05, Z0 + 0.8))] + [(xs[2], 0, Z0 - 0.9)], 'flow_discharge', 0.02, 0.4)
    for k, (x, R) in enumerate(zip(xs, Rs)):
        m.flow(f'vapour_{k + 1}', [(x, 0.05, Z0 + 0.6), (x, 0, Z0 + L + R * 0.5 + 0.3), (x + 0.5, 0, Z0 + L + R * 0.5 + 0.3)], 'steam', 0.02, 0.3)
    _press(m, [cyl(f'pz{k}', R + 0.05, Z0, Z0 + L, f'pressure_{lev}', 48, center=(x, 0, 0), r_in=R + 0.03) for k, (x, R, lev) in enumerate(zip(xs, Rs, (8, 5, 2)))],
           'Stepwise pressure reduction recovers heat', 'Hot digested slurry is let down in steps to lower pressures; in each tank part of the water flashes to steam and the slurry cools to the saturation '
           'temperature of that stage. The flash vapour from each stage heats incoming slurry in the matching heater stage (regenerative heating). Erosion at let-down valves and inlets is a key concern.')
    return m.export(out)


# =============================================================== EQ-278 Desilication tank
def desilication_tank(out):
    m = _model('desilication_tank', 'Pre-Desilication Tank (Agitated, Long Residence, Steam-Heated)')
    R, Z0, H = 0.95, 0.3, 1.8
    agitated_tank(m, 'ds_', R, Z0, H, 'Desilication Tank', 'dsl', liquid='bauxite', imp='hydrofoil', revs=1.0, open_top=False)
    coil, _ = helix_coil('cl', R - 0.15, Z0 + 0.3, Z0 + 1.3, 4, 0.025, 'stainless')
    P(m, 'heating_coil', 'Steam Heating Coil (holds ~ 95–100 °C)', 'heater', half(coil, 'stainless'), explode=(0, -0.6, 0), ref='dsl_coil', section='keep')
    nz = [nozzle('in', (-R, 0, Z0 + H - 0.2), (-1, 0, 0), 0.06, 0.3), nozzle('out', (R, 0, Z0 + 0.2), (1, 0, 0), 0.06, 0.3), nozzle('si', (-R, 0.3, Z0 + 1.3), (-1, 0, 0), 0.03, 0.25)]
    P(m, 'nozzles', 'Slurry Inlet (top), Outlet (bottom), Steam Inlet', 'nozzles', nz, explode=(0, 0, 0.3), ref='dsl_coil', section='keep')
    P(m, 'foundation', 'Ring-Wall Foundation', 'structure', cyl('fd', R + 0.1, 0.0, Z0, 'cast_iron', 96), explode=(0, 0, -0.3), ref='dsl_tank', section='split')
    particles_path(m, 'dsp', 'Desilication Product (sodalite) Crystals forming and growing', lambda i, s: ((0.15 + 0.6 * ((i * 0.31) % 1)) * math.cos(TAU * (s + i / 12)), abs((0.15 + 0.6 * ((i * 0.31) % 1)) * math.sin(TAU * (s + i / 12))) + 0.02,
                                                                                                  Z0 + 0.3 + (H - 0.7) * (0.5 + 0.5 * math.sin(TAU * (s + i * 0.21)))), 14, mat='powder', r=0.02, scale_fn=lambda i, s: 0.4 + 1.2 * s)
    m.flow('slurry', [(-R - 0.4, 0, Z0 + H - 0.2), (-0.4, 0.05, Z0 + H - 0.3), (0.4, 0.05, Z0 + 0.3), (R + 0.4, 0, Z0 + 0.2)], 'flow_discharge', 0.02, 0.4)
    m.flow('steam', [(-R - 0.3, 0.3, Z0 + 1.3), (-R + 0.15, 0.3, Z0 + 1.3)], 'steam', 0.015, 0.2)
    _press(m, [cyl('tz', R + 0.05, Z0, Z0 + H, 'pressure_7', 64, r_in=R + 0.03)], 'Removing reactive silica before digestion',
           'Kaolinite and other reactive silica dissolve in caustic liquor and would later precipitate as scale or contaminate the product. Holding the slurry at about 95–100 °C for several hours '
           '(often ~ 6–10 h) lets the silica re-precipitate as sodalite (desilication product, DSP), which leaves with the red mud. Each kg of reactive silica locks up caustic soda and alumina in DSP.', kind='temperature')
    return m.export(out)


# =============================================================== EQ-279 Precipitation tank agitator
def precipitation_tank_agitator(out):
    m = _model('precipitation_tank_agitator', 'Gibbsite Precipitator with Draft-Tube Agitator')
    R, Z0, H = 0.85, 0.3, 2.6
    agitated_tank(m, 'pr_', R, Z0, H, 'Precipitator', 'pt', liquid='liquor', imp='hydrofoil', revs=0.8, open_top=True, baffles=False, draft_tube=True)
    cl = [hollow_pipe('ic', [(R + 0.5, 0, Z0 + H - 0.4), (R + 0.5, 0, Z0 + 0.4), (R - 0.05, 0, Z0 + 0.4)], 0.06, 'stainless', 16, bend=0.1), vessel('hx', 0.15, 1.0, 0.006, 'paint_blue', center=(R + 0.5, 0.5, 0), heads=('2:1', '2:1'), z0=Z0 + 0.8)]
    cl += [nozzle('in', (-R, 0, Z0 + H - 0.15), (-1, 0, 0), 0.06, 0.3), nozzle('sd', (-0.3, 0, Z0 + H - 0.1), (0, 0, 1), 0.05, 0.3)]
    P(m, 'interstage_cooling', 'Interstage Cooler, Overflow / Transfer & Seed Addition', 'piping', cl, explode=(0.4, 0, 0), ref='pt_cooler', section='keep')
    P(m, 'foundation', 'Ring-Wall Foundation', 'structure', cyl('fd', R + 0.1, 0.0, Z0, 'cast_iron', 96), explode=(0, 0, -0.3), ref='pt_tank', section='split')
    def loop(i, s):
        r_in, r_out = 0.15 + 0.12 * ((i * 0.37) % 1), R * 0.6 + 0.15 * ((i * 0.53) % 1)
        zl, zh = Z0 + 0.25 * H, Z0 + 0.85 * H
        if s < 0.5:
            return (r_in, 0.08, zh - (zh - zl) * s / 0.5)
        return (r_out, 0.08, zl + (zh - zl) * (s - 0.5) / 0.5)
    particles_path(m, 'hydrate', 'Gibbsite (Al(OH)₃) Crystals growing as the liquor circulates (down the draft tube, up the annulus)', loop, 16, mat='powder', r=0.022, scale_fn=lambda i, s: 0.6 + 0.8 * ((i * 0.41) % 1))
    m.flow('circulation', [(0, 0.05, Z0 + 0.85 * H), (0, 0.05, Z0 + 0.25 * H - 0.1), (R * 0.65, 0.05, Z0 + 0.2 * H), (R * 0.65, 0.05, Z0 + 0.85 * H), (0.1, 0.05, Z0 + 0.9 * H)], 'flow_discharge', 0.02, 0.4)
    m.flow('pregnant_liquor', [(-R - 0.4, 0, Z0 + H - 0.15), (-R + 0.2, 0.1, Z0 + H - 0.25)], 'flow_suction', 0.02, 0.2)
    _bands_z(m, [(Z0 + H * 0.6, Z0 + H, 6), (Z0, Z0 + H * 0.6, 5)], R, 'Supersaturation drives precipitation',
             'Cooled, seeded pregnant liquor is supersaturated: NaAl(OH)₄ → Al(OH)₃ + NaOH. Fine seed hydrate gives surface for growth and agglomeration. Precipitation runs for roughly 30–60 h through a '
             'train of tanks, cooling from about 75–80 °C to 60–65 °C (interstage cooling raises yield). The draft-tube agitator keeps the hydrate suspended with low shear.', kind='temperature')
    return m.export(out)


# =============================================================== EQ-280 Seed classification unit
def seed_classification_unit(out):
    m = _model('seed_classification_unit', 'Hydrate Seed Classification Unit (Gravity Classifier Tank)')
    R, Z0, H = 0.9, 1.2, 0.9
    v = csg('cl', [lathe('clo', [(0.0, Z0 - R * 1.0 - 0.05), (0.12, Z0 - R * 1.0 - 0.05), (R + 0.02, Z0), (R + 0.02, Z0 + H), (0.0, Z0 + H)], 'paint_grey', 96)],
            [lathe('cli', [(0.0, Z0 - R * 1.0), (0.1, Z0 - R * 1.0), (R, Z0 + 0.02), (R, Z0 + H + 0.1), (0.0, Z0 + H + 0.1)], 'paint_grey', 96)], 'paint_grey')
    ld = csg('ld', [cyl('ldo', R + 0.18, Z0 + H - 0.15, Z0 + H, 'paint_grey', 96)], [cyl('ldi', R + 0.02, Z0 + H - 0.2, Z0 + H + 0.05, 'paint_grey', 96), cyl('ldc', R + 0.15, Z0 + H - 0.12, Z0 + H + 0.05, 'paint_grey', 96)], 'paint_grey')
    P(m, 'classifier_tank', 'Classifier Tank (cylinder on steep cone) & Overflow Launder', 'tank', [v, ld], explode=(0, 0.7, 0), ref='sc_tank')
    fw = csg('fw', [cyl('fwo', 0.25, Z0 + 0.2, Z0 + H + 0.1, 'steel', 48)], [cyl('fwi', 0.235, Z0 + 0.1, Z0 + H + 0.2, 'steel', 48)], 'steel')
    P(m, 'feedwell', 'Central Feedwell', 'internals', fw, explode=(0, -0.3, 0.5), ref='sc_feedwell', section='split')
    lq = lathe('lq', [(0.0, Z0 - R + 0.02), (0.1, Z0 - R + 0.02), (R - 0.005, Z0 + 0.02), (R - 0.005, Z0 + H - 0.16), (0.0, Z0 + H - 0.16)], 'liquor', 64, a0=0.0, a1=math.pi, cap_mat='liquor')
    P(m, 'liquor', 'Hydrate Slurry / Liquor', 'fluid', lq, explode=(0, -0.4, 0), ref='sc_tank', section='keep')
    nz = [hollow_pipe('fp', [(-1.6, 0, Z0 + H + 0.3), (0, 0, Z0 + H + 0.3), (0, 0, Z0 + H - 0.1)], 0.05, 'stainless', 16, bend=0.08), nozzle('uf', (0, 0, Z0 - R - 0.05), (0, 0, -1), 0.05, 0.3), nozzle('of', (R + 0.12, 0, Z0 + H - 0.15), (0, 0, -1), 0.06, 0.3)]
    P(m, 'nozzles', 'Feed Pipe, Coarse Underflow Outlet, Fine-Seed Overflow Outlet', 'nozzles', nz, explode=(0, 0, 0.3), ref='sc_nozzles', section='keep')
    _pump(m, 'underflow_pump', 'Underflow Pump (coarse hydrate → product)', 0.6, 0.0, 0.25, 'sc_pump', explode=(0.3, -0.3, 0))
    P(m, 'structure', 'Support Structure', 'structure', [box(f'sl{k}', (0.1, 0.1, Z0 + 0.1), (sx * (R - 0.1), sy * (R - 0.1), (Z0 + 0.1) / 2), 'paint_grey') for k, (sx, sy) in enumerate(((-1, -1), (-1, 1), (1, -1), (1, 1)))],
      explode=(0, 0, -0.3), ref='sc_tank', section='keep')
    particles_path(m, 'coarse', 'Coarse Hydrate settling to the Underflow (product)', lambda i, s: ((0.2 + 0.4 * ((i * 0.37) % 1)) * (1 - s), 0.08, Z0 + 0.2 - (R + 0.15) * s * 1.0), 10, mat='powder', r=0.03)
    particles_path(m, 'fines', 'Fine Seed rising with the Liquor to the Overflow (returned as seed)', lambda i, s: (0.3 + (R - 0.35) * s, 0.08, Z0 + 0.2 + (H - 0.35) * s), 10, mat='powder', r=0.012)
    m.flow('feed', [(-1.7, 0, Z0 + H + 0.3), (0, 0, Z0 + H + 0.3), (0, 0.05, Z0 + 0.2)], 'flow_discharge', 0.02, 0.3)
    m.flow('overflow', [(0.3, 0.05, Z0 + 0.4), (R - 0.05, 0.05, Z0 + H - 0.15), (R + 0.12, 0, Z0 + H - 0.5)], 'flow_suction', 0.02, 0.3)
    m.flow('underflow', [(0, 0.05, Z0 - 0.2), (0, 0, Z0 - R - 0.4)], 'sand', 0.02, 0.2)
    _press(m, [cyl('vz', R + 0.05, Z0, Z0 + H, 'pressure_4', 64, r_in=R + 0.03)], 'Upflow velocity sets the cut size',
           'Coarse hydrate crystals settle faster than the rising liquor and report to the underflow as product (to filtration and calcination). Fine crystals are carried up with the overflow and '
           'returned to precipitation as seed. The cut size is set by the overflow rate per unit area (upflow velocity) and slurry density — the key to controlling product particle size.')
    return m.export(out)


# =============================================================== EQ-281 Classification hydrocyclone
def classification_hydrocyclone(out):
    m = _model('classification_hydrocyclone', 'Classification Hydrocyclone Cluster (Radial Manifold)')
    ZT = 2.0
    cy_all = []
    pts = None
    for k in range(4):
        a = TAU * k / 4 + math.pi / 4
        x, y = 0.55 * math.cos(a), 0.55 * math.sin(a)
        objs, info = hydrocyclone(f'cy{k}', x, y, ZT, D=0.25, L_cyl=0.3, L_cone=0.9)
        cy_all += objs
        if k == 0:
            pts = info
    P(m, 'cyclones', 'Hydrocyclones: Inlet Head, Cylinder, Cone & Apex (rubber/ceramic lined)', 'separator', cy_all, explode=(0, 0.6, 0), ref='hc_cyclone')
    mf = [cyl('dm', 0.18, ZT - 0.4, ZT - 0.05, 'paint_grey', 48, r_in=0.16)] + [cyl(f'df{k}', 0.05, 0.12, 0.45, 'paint_grey', 16, axis='X', center=(0, 0, ZT - 0.15)) for k in range(1)]
    mf += [rotate(cyl(f'dr{k}', 0.05, 0.15, 0.42, 'paint_grey', 16, axis='X', center=(0, 0, ZT - 0.14)), TAU * k / 4 + math.pi / 4, 'Z') for k in range(4)]
    mf += [hollow_pipe('fd', [(-1.5, 0, 0.3), (-1.5, 0, ZT - 1.0), (0, 0, ZT - 1.0), (0, 0, ZT - 0.4)], 0.07, 'paint_grey', 16, bend=0.12)]
    P(m, 'distributor', 'Feed Distributor (radial manifold) & Feed Line', 'piping', mf, explode=(0, 0, -0.4), ref='hc_manifold', section='keep')
    ol = [csg('ofl', [cyl('ofo', 0.85, ZT + 0.25, ZT + 0.45, 'paint_grey', 64)], [cyl('ofi', 0.4, ZT + 0.2, ZT + 0.5, 'paint_grey', 64), cyl('ofc', 0.82, ZT + 0.28, ZT + 0.5, 'paint_grey', 64)], 'paint_grey')]
    ul = [csg('ufl', [cyl('ufo', 0.85, ZT - 1.55, ZT - 1.35, 'paint_grey', 64)], [cyl('ufi', 0.4, ZT - 1.6, ZT - 1.3, 'paint_grey', 64), cyl('ufc', 0.82, ZT - 1.52, ZT - 1.3, 'paint_grey', 64)], 'paint_grey')]
    P(m, 'launders', 'Overflow Launder (fines) & Underflow Launder (coarse)', 'launders', ol + ul, explode=(0, 0, 0.5), ref='hc_launders', section='split')
    P(m, 'structure', 'Support Structure', 'structure', [box(f'sl{k}', (0.08, 0.08, ZT + 0.45), (sx * 0.6, sy * 0.6, (ZT + 0.45) / 2), 'paint_grey') for k, (sx, sy) in enumerate(((-1, -1), (-1, 1), (1, -1), (1, 1)))],
      explode=(0, 0, -0.3), ref='hc_launders', section='keep')
    c0 = (0.55 * math.cos(math.pi / 4), 0.55 * math.sin(math.pi / 4))
    R = pts['R']
    def outer(i, s):
        z = ZT - 0.1 - (ZT - 0.1 - pts['za']) * s
        r = R - 0.02 if z > pts['zc'] else max(0.02, (R - 0.02) * (z - pts['za']) / (pts['zc'] - pts['za']))
        a = TAU * 4 * s + i
        return (c0[0] + r * math.cos(a), c0[1] + r * math.sin(a), z)
    def inner(i, s):
        z = pts['za'] + 0.2 + (ZT + 0.2 - pts['za'] - 0.2) * s
        a = -TAU * 4 * s + i
        return (c0[0] + 0.03 * math.cos(a), c0[1] + 0.03 * math.sin(a), z)
    particles_path(m, 'coarse', 'Coarse Particles spiralling down the Wall to the Apex (underflow)', outer, 10, mat='powder', r=0.014)
    particles_path(m, 'fines', 'Fine Particles carried up the Central Vortex to the Overflow', inner, 8, mat='water', r=0.01)
    m.flow('feed', [(-1.6, 0, 0.3), (-1.5, 0, ZT - 1.0), (0, 0, ZT - 1.0), (0, 0, ZT - 0.2), (c0[0], c0[1] + 0.05, ZT - 0.1)], 'flow_discharge', 0.025, 0.4)
    m.flow('overflow', [(c0[0], c0[1], ZT - 0.3), (c0[0], c0[1], ZT + 0.35)], 'water', 0.015, 0.2)
    m.flow('underflow', [(c0[0], c0[1], pts['za']), (c0[0], c0[1], ZT - 1.45)], 'sand', 0.015, 0.2)
    _press(m, [cyl('pz', R + 0.04, pts['zc'], ZT, 'pressure_7', 32, center=(c0[0], c0[1], 0), r_in=R + 0.025)], 'Centrifugal classification',
           'Feed enters tangentially under pressure (typically ~ 0.5–2 bar), forming an outer downward vortex and an inner upward vortex. Coarse/dense particles are thrown to the wall and leave at the apex; '
           'fines and most of the liquid leave through the vortex finder. The d50 cut size falls with smaller diameter and higher pressure; apex size controls the underflow density (avoid "roping").')
    return m.export(out)


# =============================================================== EQ-282 Red mud washer (CCD)
def red_mud_washer(out):
    m = _model('red_mud_washer', 'Red Mud Washer Train (Counter-Current Decantation, 3 Thickeners)')
    xs = (-2.0, 0.0, 2.0)
    for k, x in enumerate(xs):
        thickener(m, f'w{k + 1}_', 0.75, 0.6, 0.35, cx=x, label=f'Washer {k + 1}', ref='rw', mud='red_mud', liquid='liquor', rake_revs=0.25)
    pp = []
    for k in range(2):
        a, b = xs[k], xs[k + 1]
        pp.append(hollow_pipe(f'mu{k}', [(a, 0, 0.1), (a + 0.6, 0, 0.1), (b - 0.6, 0, 0.1), (b - 0.2, -0.3, 1.2), (b, -0.3, 1.2)], 0.035, 'paint_grey', 12, bend=0.06))
        pp.append(hollow_pipe(f'ov{k}', [(b + 0.9, 0.5, 1.1), (b + 0.9, 0.5, 1.4), (a, 0.5, 1.4), (a, 0.3, 1.2)], 0.035, 'stainless', 12, bend=0.06))
    pp += [hollow_pipe('ww', [(xs[2] + 1.1, 0.3, 1.6), (xs[2], 0.3, 1.6), (xs[2], 0.3, 1.2)], 0.035, 'paint_blue', 12, bend=0.06)]
    P(m, 'interstage_piping', 'Underflow (mud) Lines Forward & Overflow (wash liquor) Lines Backward', 'piping', pp, explode=(0, 0, 0.6), ref='rw_piping', section='keep')
    m.flow('mud', [(xs[0], 0, 0.15), (xs[1], -0.3, 1.2), (xs[1], 0, 0.15), (xs[2], -0.3, 1.2), (xs[2], 0, 0.15), (xs[2] + 1.2, 0, 0.15)], 'sand', 0.025, 0.5)
    m.flow('wash_liquor', [(xs[2] + 1.2, 0.3, 1.6), (xs[2], 0.3, 1.2), (xs[2] + 0.9, 0.5, 1.4), (xs[1], 0.3, 1.2), (xs[1] + 0.9, 0.5, 1.4), (xs[0], 0.3, 1.2), (xs[0] - 1.2, 0.5, 1.2)], 'water', 0.02, 0.5)
    _press(m, [cyl(f'cz{k}', 0.85, 0.5, 1.15, f'pressure_{lev}', 64, center=(x, 0, 0), r_in=0.82) for k, (x, lev) in enumerate(zip(xs, (8, 5, 2)))], 'Counter-current washing recovers caustic',
           'Mud moves forward (left → right) while wash water moves backward (right → left). Each stage dilutes the soluble soda and alumina left in the mud, so the liquor strength falls from red (first washer) to blue '
           '(last). Recovered liquor returns to the circuit; washed mud goes to residue storage. Typically 4–7 washers are used, with flocculant to speed settling.')
    return m.export(out)


# =============================================================== EQ-283 Mud settling tank
def mud_settling_tank(out):
    m = _model('mud_settling_tank', 'Red Mud Settler / High-Rate Thickener (Primary Residue Separation)')
    z0 = thickener(m, 'st_', 1.3, 1.0, 0.5, label='Settler', ref='ms', mud='red_mud', liquid='liquor', rake_revs=0.2)
    pp = [hollow_pipe('fd', [(-2.2, 0, z0 + 1.35), (0, 0, z0 + 1.35), (0, 0, z0 + 1.05)], 0.06, 'paint_grey', 16, bend=0.1),
          hollow_pipe('fl', [(-2.2, 0.35, z0 + 1.55), (-0.2, 0.35, z0 + 1.55), (-0.2, 0.2, z0 + 1.05)], 0.02, 'paint_green', 12, bend=0.04),
          hollow_pipe('uf', [(0, 0, 0.1), (0, 0, -0.05), (1.8, 0, -0.05), (1.8, 0, 0.25)], 0.06, 'paint_grey', 16, bend=0.08), nozzle('of', (1.45, 0, z0 + 0.85), (1, 0, 0), 0.07, 0.4)]
    P(m, 'piping', 'Feed Line (digested slurry), Flocculant Dosing Line, Underflow Line & Overflow Outlet', 'piping', pp, explode=(0, 0, 0.5), ref='ms_piping', section='keep')
    _pump(m, 'underflow_pump', 'Underflow (mud) Pump', 1.8, 0.0, 0.25, 'ms_piping', explode=(0.3, -0.3, 0))
    particles_path(m, 'settling', 'Flocculated Mud Particles settling', lambda i, s: (-1.0 + 2.0 * ((i * 0.37) % 1), 0.15 + 0.6 * ((i * 0.53) % 1), z0 + 0.9 - 0.75 * s), 14, mat='red_mud', r=0.02)
    m.flow('feed', [(-2.3, 0, z0 + 1.35), (0, 0, z0 + 1.35), (0, 0.05, z0 + 0.5)], 'flow_discharge', 0.025, 0.3)
    m.flow('overflow', [(0.5, 0.1, z0 + 0.6), (1.25, 0.1, z0 + 0.9), (1.9, 0, z0 + 0.85)], 'water', 0.02, 0.3)
    m.flow('underflow', [(0, 0.05, 0.2), (0, 0, -0.05), (1.8, 0, -0.05), (2.3, 0, 0.25)], 'sand', 0.02, 0.3)
    m.flow('flocculant', [(-2.3, 0.35, z0 + 1.55), (-0.2, 0.35, z0 + 1.55), (-0.2, 0.2, z0 + 1.0)], 'air', 0.012, 0.2)
    _press(m, [cyl('ss', 1.35, z0, z0 + 0.45, 'pressure_8', 96, r_in=1.33), cyl('sc', 1.35, z0 + 0.45, z0 + 1.0, 'pressure_2', 96, r_in=1.33)], 'Clear liquor above, compacted mud below',
           'Digested slurry is diluted and dosed with flocculant in the feedwell; flocs settle quickly, leaving clear pregnant liquor that overflows to security (polishing) filtration. The mud compacts in '
           'the lower zone and the rakes move it to the underflow cone. Overflow clarity (often ≲ 100 mg/L solids) and underflow density are the key performance targets.')
    return m.export(out)


# ===================================================================== metadata
def _std(*items):
    return [{'id': i, 'title': t, 'relevance': r, 'edition': 'to be verified'} for i, t, r in items]


def _c(fn, cons, mat, op='—', fm=('—',), insp=('Visual',)):
    return C(fn, cons, mat, op, list(fm), list(insp))


_REF = ['Hind, Bhargava & Grocott — The surface chemistry of Bayer process solids', 'Authier-Martin et al. / TMS Light Metals proceedings (Bayer process practice)']
_PVS = _std(('ASME BPVC VIII-1', 'Pressure vessels', 'Autoclaves, flash tanks, heaters.'), ('API 650', 'Welded tanks for oil storage', 'Atmospheric tank construction (adopted practice; to be verified for caustic service).'))
_MIN = _std(('Maker standards', 'Mineral processing equipment', 'Mill/drum design and liners.'),)


def _thk_comp(ref):
    return {ref + '_tank': _c('Holds slurry; launder collects overflow.', 'Steel/concrete tank with conical floor.', 'Carbon steel.'), ref + '_zones': _c('Clear and mud zones.', '—', '—'),
            ref + '_feedwell': _c('Calms feed; mixes flocculant.', 'Feedwell.', 'Steel.'), ref + '_rake': _c('Moves settled mud to the cone; keeps it from setting.', 'Rake arms and blades.', 'Steel.', 'Very slow (minutes per rev).', ['Bogging (high torque)'], ['Torque trend']),
            ref + '_drive': _c('Turns the rakes.', 'Bridge, planetary drive, torque protection, lift.', '—')}


def _agt_comp(ref):
    return {ref + '_tank': _c('Holds the slurry.', 'Tank with baffles/draft tube.', 'Carbon steel.'), ref + '_slurry': _c('Process slurry/liquor.', '—', '—'),
            ref + '_agitator': _c('Mixes and suspends solids.', 'Shaft and impellers.', 'Carbon steel (often rubber-lined).', '—', ['Blade wear, scale'], ['Inspect']), ref + '_drive': _c('Drives the agitator.', 'Motor and gearbox.', '—')}


META = {
    'bauxite_stockpile_reclaimer': {'summary': ('A bridge-type scraper reclaimer recovers bauxite from a blending stockpile across its whole cross-section. A harrow rakes the pile face so material slides down to a chain scraper at the pile foot, '
                                                'which drags it onto the yard conveyor. Reclaiming the full face blends the many stacked layers into a uniform feed.'),
                                    'classification': {'family': 'Bulk handling', 'type': 'Bridge scraper (harrow) reclaimer'}, 'model_configuration': {'animation': 'Harrow oscillates, scraper flights run, bridge advances'},
                                    'standards': _std(('ISO 5049-1', 'Mobile equipment for continuous handling of bulk materials', 'Design rules.'),), 'references': ['Bulk blending bed design notes'],
                                    'components': {'br_pile': _c('Blending pile.', 'Chevron-stacked layers.', 'Bauxite.'), 'br_rails': _c('Travel track.', 'Rails.', 'Steel.'), 'br_bridge': _c('Carries harrow and scraper.', 'Portal bridge with bogies.', 'Steel.'),
                                                   'br_harrow': _c('Loosens the face.', 'Raking frame with tines.', 'Steel.', '—', ['Tine wear'], ['Inspect']), 'br_scraper': _c('Moves material to the conveyor.', 'Chain with flights, sprockets, drive.', 'Steel.', '—', ['Chain wear'], ['Measure']),
                                                   'hk_belt': _c('Carries reclaimed bauxite.', 'Belt.', 'Rubber.'), 'hk_pulley': _c('Pulleys.', '—', 'Steel.'), 'hk_idlers': _c('Frame.', '—', 'Steel.')}},
    'bauxite_washing_drum': {'summary': ('A bauxite washing (scrubbing) drum tumbles crushed bauxite with water so the lumps rub against each other and clay is washed off. A trommel screen at the discharge separates washed bauxite from the '
                                         'clay-rich fines, lowering reactive silica in the digestion feed.'),
                             'classification': {'family': 'Ore preparation', 'type': 'Rotary scrubber with trommel'}, 'model_configuration': {'animation': 'Tyres/gear turn; lumps tumble; sprays'},
                             'standards': _MIN, 'references': ['Wills\' Mineral Processing Technology — scrubbing'],
                             'components': {'bw_shell': _c('Rotating scrubbing chamber.', 'Shell with rubber liners and lifters.', 'Steel/rubber.', '—', ['Liner wear'], ['Inspect']), 'bw_drive': _c('Rotation and support.', 'Tyres, girth gear, rollers, motor.', 'Steel.'),
                                            'bw_trommel': _c('Screens discharge.', 'Perforated trommel.', 'Steel/PU.'), 'bw_spray': _c('Adds wash water.', 'Spray header.', 'Stainless.'), 'bw_chutes': _c('Feed and discharge.', 'Chutes and sump.', 'Steel.')}},
    'bauxite_grinding_mill': {'summary': ('A ball mill grinds bauxite in spent caustic liquor. The rotating shell lifts steel balls that cascade onto the charge, crushing and abrading the bauxite into a fine slurry ready for desilication and digestion.'),
                              'classification': {'family': 'Grinding', 'type': 'Overflow-discharge ball mill (wet)'}, 'model_configuration': {'animation': 'Balls cascade; girth gear turns'},
                              'standards': _MIN, 'references': ['Wills\' Mineral Processing Technology — grinding mills'],
                              'components': {'bg_shell': _c('Grinding chamber.', 'Shell with liners.', 'Steel/Ni-hard or rubber.', '—', ['Liner wear'], ['Liner profile']), 'bg_drive': _c('Rotation and support.', 'Girth gear, pinion, gearbox, motor, bearings.', 'Steel.', '—', ['Gear wear'], ['Vibration']),
                                             'bg_heads': _c('Feed/discharge and trunnions.', 'Heads, trunnions, trommel.', 'Cast steel.'), 'bg_charge': _c('Grinding media.', 'Steel balls (≈ 30–40 % fill).', 'Forged steel.')}},
    'bauxite_slurry_mixing_tank': {'summary': ('An agitated tank receives ground bauxite slurry and spent liquor, keeps the solids in suspension and buffers the flow between grinding and digestion. Density and level are controlled before the slurry is pumped on.'),
                                   'classification': {'family': 'Slurry preparation', 'type': 'Agitated slurry storage tank'}, 'model_configuration': {'animation': 'Agitator turns; solids circulate'},
                                   'standards': _PVS, 'references': _REF,
                                   'components': {**_agt_comp('sm'), 'sm_nozzles': _c('Inlets/outlet/level.', 'Nozzles, LT.', 'Steel.'), 'sm_pump': _c('Transfers slurry.', 'Slurry pump.', 'High-chrome/rubber.')}},
    'digestion_autoclave': {'summary': ('Digestion autoclaves are agitated pressure vessels in series where hot caustic liquor dissolves the alumina from bauxite. Live steam heats the slurry to digestion temperature, and the vessels give the residence time needed.'),
                            'classification': {'family': 'Digestion', 'type': 'Agitated autoclaves in series (high-temperature digestion)'}, 'model_configuration': {'vessels': 3, 'animation': 'Agitators turn; steam injected'},
                            'standards': _PVS, 'references': _REF,
                            'components': {**_agt_comp('da'), 'da_piping': _c('Transfer and steam lines.', 'Pipes, steam injectors, gauges.', 'Steel.', '—', ['Erosion, scaling'], ['Thickness'])}},
    'digestion_heater': {'summary': ('Digestion heaters preheat the slurry before digestion using flash vapour from the multi-stage flash tanks. The slurry passes several times through the tubes while vapour condenses on the outside.'),
                         'classification': {'family': 'Heat transfer', 'type': 'Vertical multi-pass shell & tube slurry heater'}, 'model_configuration': {'animation': 'Slurry tracers; condensate'},
                         'standards': _PVS + _std(('TEMA', 'Tubular exchanger standards', 'Design.'),), 'references': _REF,
                         'components': {'dh_shell': _c('Vapour side.', 'Shell and tubesheets.', 'Carbon steel.'), 'dh_heads': _c('Direct slurry passes.', 'Heads with partitions.', 'Steel.'),
                                        'dh_tubes': _c('Heat transfer.', 'Tubes (scale shown).', 'Carbon steel.', '—', ['DSP/titanate scale'], ['ΔT, U trend']), 'dh_nozzles': _c('Connections.', 'Nozzles.', 'Steel.')}},
    'multi_stage_flash_vessel': {'summary': ('After digestion the hot slurry passes through a train of flash tanks at falling pressure. In each tank part of the water flashes to steam, cooling the slurry; the vapour heats incoming slurry in the matching heaters.'),
                                 'classification': {'family': 'Digestion', 'type': 'Multi-stage flash (blow-off) tanks'}, 'model_configuration': {'stages': 3, 'animation': 'Flashing; levels'},
                                 'standards': _PVS, 'references': _REF,
                                 'components': {'mf_tanks': _c('Flash vessels.', 'Vertical vessels with cone.', 'Carbon steel (wear-lined).', '—', ['Erosion at inlet'], ['Thickness']), 'mf_slurry': _c('Slurry.', '—', '—'),
                                                'mf_piping': _c('Transfer/vapour lines and level control.', 'Pipes and choke valves.', 'Hardened steel trim.', '—', ['Valve erosion'], ['Inspect trim'])}},
    'desilication_tank': {'summary': ('Pre-desilication tanks hold the bauxite slurry hot for several hours so dissolved reactive silica re-precipitates as sodalite (desilication product) before digestion. This protects heaters from scale and the product from silica.'),
                          'classification': {'family': 'Desilication', 'type': 'Agitated heated holding tank'}, 'model_configuration': {'animation': 'DSP crystals grow'},
                          'standards': _PVS, 'references': _REF,
                          'components': {**_agt_comp('dsl'), 'dsl_coil': _c('Heating and connections.', 'Steam coil, nozzles.', 'Stainless.')}},
    'precipitation_tank_agitator': {'summary': ('Precipitators are large tanks where cooled, seeded pregnant liquor deposits gibbsite (aluminium hydroxide). A slow draft-tube agitator circulates the slurry to keep hydrate suspended and help crystals grow and agglomerate.'),
                                    'classification': {'family': 'Precipitation', 'type': 'Draft-tube agitated precipitator'}, 'model_configuration': {'animation': 'Circulation down the draft tube; crystals grow'},
                                    'standards': _PVS, 'references': _REF,
                                    'components': {**_agt_comp('pt'), 'pt_cooler': _c('Cooling, transfer, seed.', 'Interstage cooler and lines.', 'Stainless/steel.')}},
    'seed_classification_unit': {'summary': ('A seed classification unit splits the precipitated hydrate by size. Coarse crystals settle to the underflow as product; fine crystals rise with the overflow and return to precipitation as seed.'),
                                 'classification': {'family': 'Precipitation', 'type': 'Gravity hydrate classifier'}, 'model_configuration': {'animation': 'Coarse settle, fines rise'},
                                 'standards': _PVS, 'references': _REF,
                                 'components': {'sc_tank': _c('Classification zone.', 'Cylinder-on-cone tank with launder.', 'Steel.'), 'sc_feedwell': _c('Distributes feed.', 'Feedwell.', 'Steel.'),
                                                'sc_nozzles': _c('Feed/outlets.', 'Pipes, nozzles.', 'Steel.'), 'sc_pump': _c('Pumps coarse product.', 'Slurry pump.', '—')}},
    'classification_hydrocyclone': {'summary': ('Hydrocyclones classify hydrate (or other slurries) by particle size using centrifugal force. Fed tangentially under pressure, coarse particles move to the wall and exit at the apex, fines leave through the vortex finder.'),
                                    'classification': {'family': 'Classification', 'type': 'Hydrocyclone cluster'}, 'model_configuration': {'cyclones': 4, 'animation': 'Outer and inner vortex particles'},
                                    'standards': _MIN, 'references': ['Svarovsky — Hydrocyclones'],
                                    'components': {'hc_cyclone': _c('Classify by size.', 'Lined cyclones.', 'PU/rubber/ceramic.', '—', ['Apex and cone wear'], ['Inspect']), 'hc_manifold': _c('Distribute feed.', 'Radial manifold.', 'Steel.'),
                                                   'hc_launders': _c('Collect products.', 'Overflow and underflow launders.', 'Steel.')}},
    'red_mud_washer': {'summary': ('Red mud washers are thickeners in a counter-current decantation (CCD) train. Mud moves forward from washer to washer while wash water flows backward, recovering dissolved caustic soda and alumina from the mud.'),
                       'classification': {'family': 'Residue washing', 'type': 'CCD thickener train'}, 'model_configuration': {'washers': 3, 'animation': 'Rakes turn; mud and wash flows'},
                       'standards': _PVS, 'references': _REF,
                       'components': {**_thk_comp('rw'), 'rw_piping': _c('Interstage lines.', 'Underflow and overflow pipes.', 'Steel.')}},
    'mud_settling_tank': {'summary': ('The mud settler (primary thickener) separates red mud from the pregnant liquor after digestion. Flocculant helps the mud settle; clear liquor overflows to polishing filtration and the thickened mud is pumped to the washers.'),
                          'classification': {'family': 'Residue separation', 'type': 'High-rate thickener / settler'}, 'model_configuration': {'animation': 'Rakes turn; particles settle'},
                          'standards': _PVS, 'references': _REF,
                          'components': {**_thk_comp('ms'), 'ms_piping': _c('Feed, flocculant, underflow, overflow.', 'Pipes and pump.', 'Steel.')}},
}
BUILDERS = {k: globals()[k] for k in META}
