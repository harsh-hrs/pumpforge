"""Filtration & Separation — flotation, oil/water, coalescing, adsorption, drying, dehydration, sand removal (EQ-262 … EQ-270)."""
import math
from mathutils import Matrix, Vector
from pumpforge.core import Model, lathe, cyl, box, csg, join, rotate, TAU, OPERATE_FRAMES
from pumpforge.valvekit import P, keys_loop, smooth_pulse
from pumpforge.parts import hollow_pipe, pressure_gauge, add_tracers
from pumpforge.vesselkit import vessel, nozzle, legs, droplets, liquid_v, half, animate_level, packing, tray, mesh_pad
from pumpforge.handlingkit import rocks_along, movers, polyline_path
from pumpforge.shapes import sweep_tube
from pumpforge.common_meta import C
from pumps._eq_thermal_a import _hliq, _bands_z, _pump, _fan_rotor, _flame
from pumps._eq_thermal_b import _bed_particles

CAT = '11 · Filtration & Separation Equipment'


def _model(pid, title):
    return Model(pid, title, CAT, META[pid])


def _bed(name, R, z0, z1, mat='powder', cx=0.0, cy=0.0, n=0):
    """Half (y >= 0) adsorbent bed with bead texture rings (keep section)."""
    b = lathe(name, [(0.0, z0), (R, z0), (R, z1), (0.0, z1)], mat, 48, a0=0.0, a1=math.pi, center=(cx, cy, 0), cap_mat=mat)
    return b


def _twin(m, pid, cx, R, Z0, L, label, bed_mat, ref, bed_ref, bed_name):
    v = vessel(pid, R, L, 0.01, 'paint_grey', heads=('2:1', '2:1'), z0=Z0, center=(cx, 0, 0))
    P(m, pid, label, 'vessel', v, explode=(0, 0.5, 0), ref=ref)
    bd = [_bed(pid + 'b', R - 0.012, Z0 + 0.15, Z0 + L - 0.15, bed_mat, cx), _bed(pid + 'cs', R - 0.012, Z0 + 0.02, Z0 + 0.15, 'cast_iron', cx), _bed(pid + 'ct', R - 0.012, Z0 + L - 0.15, Z0 + L - 0.08, 'cast_iron', cx)]
    P(m, pid + '_bed', bed_name, 'media', bd, explode=(0, -0.4, 0), ref=bed_ref, section='keep')


# =============================================================== EQ-262 Flotation cell
def flotation_cell(out):
    m = _model('flotation_cell', 'Mechanical Flotation Cell (Forced-Air, Rotor–Stator)')
    R, H = 0.75, 1.5
    tk = csg('tk', [cyl('to', R + 0.03, 0.0, H, 'paint_grey', 64)], [cyl('ti', R, 0.05, H + 0.1, 'paint_grey', 64)], 'paint_grey')
    ld = csg('ld', [cyl('lo', R + 0.25, H - 0.25, H, 'paint_grey', 64)], [cyl('li', R + 0.03, H - 0.3, H + 0.1, 'paint_grey', 64), cyl('lc', R + 0.22, H - 0.22, H + 0.1, 'paint_grey', 64)], 'paint_grey')
    P(m, 'tank', 'Cell Tank & Peripheral Froth Launder', 'tank', [tk, ld, nozzle('ldo', (R + 0.2, 0, H - 0.25), (0, 0, -1), 0.07, 0.3)], explode=(0, 0.6, 0), ref='fc_tank')
    pl = P(m, 'pulp', 'Pulp (ore slurry with reagents)', 'fluid', half(cyl('pu', R - 0.005, 0.05, H - 0.2, 'water', 64), 'water'), explode=(0, -0.3, 0), ref='fc_pulp', section='keep')
    fr = P(m, 'froth', 'Mineralised Froth Layer', 'froth', half(cyl('fz', R - 0.005, H - 0.2, H + 0.03, 'powder', 64), 'powder'), explode=(0, -0.3, 0.3), ref='fc_froth', section='keep')
    keys_loop(m, fr, lambda t: (1, 1, 1 + 0.04 * math.sin(TAU * 2 * t)), 'scale')
    rt = [cyl('sh', 0.05, 0.3, H + 0.45, 'steel', 24, r_in=0.03)] + [rotate(box(f'rb{k}', (0.18, 0.03, 0.2), (0.11, 0, 0.35), 'rubber'), TAU * k / 8, 'Z') for k in range(8)]
    prt = P(m, 'rotor', 'Rotor on Hollow Shaft (air enters through the shaft)', 'rotating_element', rt, explode=(0, -0.7, 0.3), ref='fc_mechanism', section='keep')
    prt.spin('Z', 4)
    stt = [rotate(box(f'sb{k}', (0.12, 0.02, 0.3), (0.3, 0, 0.35), 'rubber'), TAU * k / 12 + 0.13, 'Z') for k in range(12)] + [cyl('hd', 0.35, 0.55, 0.58, 'steel', 48, r_in=0.08)]
    P(m, 'stator', 'Stator (dispersion hood) — shears air into fine bubbles', 'internals', stt, explode=(0, -0.5, 0.1), ref='fc_mechanism', section='keep')
    dr = join('dr', [box('br', (1.8, 0.2, 0.12), (0.0, 0, H + 0.3), 'paint_grey'), cyl('mt', 0.13, H + 0.35, H + 0.75, 'paint_motor', 32, center=(0.55, 0, 0), ch=0.01), box('bg', (0.7, 0.06, 0.2), (0.27, 0, H + 0.5), 'paint_yellow')])
    P(m, 'drive_bridge', 'Bridge, Motor & V-Belt Drive', 'drive', dr, explode=(0, 0, 0.5), ref='fc_drive', section='keep')
    ai = [hollow_pipe('ap', [(-1.2, 0, H + 0.5), (-0.1, 0, H + 0.5), (0, 0, H + 0.45)], 0.03, 'paint_blue', 16, bend=0.05), nozzle('fi', (-R, 0, 0.6), (-1, 0, 0), 0.07, 0.3), nozzle('tl', (R, 0, 0.25), (1, 0, 0), 0.07, 0.3)]
    P(m, 'air_feed_tailings', 'Low-Pressure Air Line, Feed Inlet & Tailings Outlet (level-controlled)', 'nozzles', ai, explode=(0, 0, -0.3), ref='fc_tank', section='keep')
    pb = m.part('bubbles', 'Bubbles carrying Hydrophobic Particles to the Froth', 'flow_tracers', explode=(0, 0, 0), info={'ref': 'flow_tracers'})
    for i in range(16):
        a, ph = TAU * i / 16, (i * 0.37) % 1
        ms = pb.add(lathe(f'bb{i}', [(0.02 * math.sin(k * math.pi / 6), -0.02 * math.cos(k * math.pi / 6)) for k in range(7)], 'air', 10), smooth_angle=80)
        keys = []
        for f in range(OPERATE_FRAMES + 1):
            s_ = ((f / OPERATE_FRAMES) + ph) % 1.0
            rr = 0.3 + 0.3 * min(1, s_ * 3)
            keys.append((1 + f, (rr * math.cos(a), abs(rr * math.sin(a)) + 0.02, 0.4 + (H - 0.45) * s_)))
        ms.location = keys[0][1]
        m.keyframes(ms, 'Operate', 'location', keys)
    m.flow('air', [(-1.2, 0, H + 0.5), (0, 0, H + 0.45), (0, 0, 0.35), (0.35, 0.05, 0.35)], 'air', 0.015, 0.3)
    m.flow('feed', [(-R - 0.3, 0, 0.6), (-0.2, 0.05, 0.5)], 'flow_suction', 0.02, 0.2)
    m.flow('concentrate_froth', [(0.3, 0.05, H - 0.1), (R + 0.1, 0.05, H), (R + 0.2, 0, H - 0.6)], 'sand', 0.02, 0.2)
    m.flow('tailings', [(0.4, 0.05, 0.3), (R + 0.3, 0, 0.25)], 'flow_discharge', 0.02, 0.2)
    m.overlay('pressure', join('hz', [cyl('hzp', R + 0.06, H - 0.2, H + 0.03, 'pressure_8', 64, r_in=R + 0.04), cyl('hzw', R + 0.06, 0.05, H - 0.2, 'pressure_2', 64, r_in=R + 0.04)]),
              'Hydrophobic vs hydrophilic particles', 'Collectors make the wanted mineral surfaces water-repellent (hydrophobic). Those particles attach to air bubbles and rise into the froth (red zone), '
              'which overflows into the launder as concentrate. Hydrophilic gangue stays in the pulp (blue) and leaves as tailings. Frothers stabilise the froth.', split=True)
    return m.export(out)


# =============================================================== EQ-263 Dissolved air flotation
def dissolved_air_flotation_unit(out):
    m = _model('dissolved_air_flotation_unit', 'Dissolved Air Flotation (DAF) Unit with Recycle Saturation')
    X0, X1, W, H = -1.6, 1.6, 0.9, 1.1
    tk = csg('tk', [box('to', (X1 - X0 + 0.06, W + 0.06, H), (0, 0, H / 2), 'stainless')], [box('ti', (X1 - X0, W, H), (0, 0, H / 2 + 0.03), 'stainless')], 'stainless')
    bf = box('bf', (0.02, W, 0.75), (X0 + 0.6, 0, 0.55), 'stainless')
    P(m, 'tank', 'DAF Tank with Contact-Zone Baffle', 'tank', [tk, bf], explode=(0, 0.6, 0), ref='daf_tank')
    pw = P(m, 'water', 'Water in the Tank', 'fluid', box('wt', (X1 - X0 - 0.01, W / 2 - 0.01, H - 0.2), (0, W / 4, (H - 0.2) / 2 + 0.03), 'water'), explode=(0, -0.3, 0), ref='daf_tank', section='keep')
    fl = P(m, 'float_layer', 'Float (sludge) Blanket on the Surface', 'froth', box('fl', (X1 - X0 - 0.5, W / 2 - 0.01, 0.08), ((X0 + X1) / 2 + 0.2, W / 4, H - 0.13), 'powder'), explode=(0, -0.3, 0.3), ref='daf_float', section='keep')
    keys_loop(m, fl, lambda t: (1, 1, 1 + 0.15 * math.sin(TAU * t)), 'scale')
    pos, L = polyline_path([(X0 + 0.8, H + 0.05), (X1 - 0.3, H + 0.05), (X1 - 0.3, H + 0.35), (X0 + 0.8, H + 0.35)] + [(X0 + 0.8, H + 0.05)])
    movers(m, 'skimmer', 'Chain-and-Flight Surface Skimmer', pos, L, 8, L / 4, lambda i: box(f'sf{i}', (0.03, W - 0.04, 0.12), (0, 0, 0), 'polypropylene'), group='skimmer', ref='daf_skimmer', y=0.0, keep_angle=False)
    sk = [box(f'sr{s}', (X1 - X0 - 1.0, 0.04, 0.04), ((X0 + X1) / 2 + 0.25, s * (W / 2 + 0.03), H + 0.2), 'steel') for s in (-1, 1)] + [cyl(f'sp{k}', 0.08, -W / 2, W / 2, 'steel', 24, axis='Y', center=(x, 0, H + 0.2)) for k, x in enumerate((X0 + 0.8, X1 - 0.3))]
    P(m, 'skimmer_frame', 'Skimmer Sprockets & Rails', 'skimmer', sk, explode=(0, 0, 0.5), ref='daf_skimmer', section='keep')
    hp = csg('hp', [box('hpo', (0.4, W, 0.45), (X1 - 0.15, 0, H - 0.1), 'stainless')], [box('hpi', (0.34, W - 0.06, 0.45), (X1 - 0.15, 0, H - 0.05), 'stainless')], 'stainless')
    P(m, 'sludge_hopper', 'Float Sludge Beach & Hopper', 'tank', [hp, box('bch', (0.4, W, 0.02), (X1 - 0.5, 0, H - 0.05), 'stainless')], explode=(0.4, 0, 0.3), ref='daf_float', section='keep')
    sat = vessel('sat', 0.2, 0.9, 0.008, 'paint_blue', heads=('2:1', '2:1'), z0=0.3, center=(X1 + 0.7, 0, 0))
    P(m, 'saturator', 'Air Saturator (recycle water dissolved with air at ~ 4–6 bar)', 'vessel', sat, explode=(0.5, 0, 0), ref='daf_saturator')
    _pump(m, 'recycle_pump', 'Recycle Pump (pressurises clarified water)', X1 + 0.3, -0.6, 0.25, 'daf_saturator', explode=(0.3, -0.3, 0), facing=1)
    rp = [hollow_pipe('rc', [(X1 + 0.7, 0, 1.45), (X1 + 0.7, 0, 1.6), (X0 + 0.3, 0, 1.6), (X0 + 0.3, 0, 0.25), (X0 + 0.45, 0, 0.25)], 0.03, 'stainless', 16, bend=0.06),
          box('rv', (0.1, 0.1, 0.1), (X0 + 0.3, 0, 0.55), 'paint_blue_dark'), nozzle('in', (X0, 0, 0.35), (-1, 0, 0), 0.06, 0.3), nozzle('ef', (X1, 0, 0.2), (1, 0, 0), 0.06, 0.25),
          hollow_pipe('cw', [(X1 - 0.6, 0, 0.12), (X1 + 0.3, -0.6, 0.12)], 0.03, 'stainless', 16)]
    P(m, 'recycle_piping', 'Recycle Line, Pressure-Release Valve / Nozzles, Inlet & Clarified Outlet', 'piping', rp, explode=(0, 0, 0.3), ref='daf_release', section='keep')
    droplets(m, 'microbubbles', 'Micro-bubbles (≈ 30–100 µm) attaching to Flocs', X0 + 0.1, X0 + 1.2, 0.25, H - 0.15, n=16, mat='air', y=0.15, r=0.012)
    m.flow('feed', [(X0 - 0.35, 0, 0.35), (X0 + 0.5, 0.1, 0.35), (X0 + 0.5, 0.1, 0.9), (X0 + 0.8, 0.1, 0.9)], 'flow_suction', 0.02, 0.3)
    m.flow('clarified', [(X0 + 1.0, 0.1, 0.5), (X1 - 0.6, 0.1, 0.15), (X1 + 0.3, 0, 0.2)], 'water', 0.02, 0.3)
    m.flow('recycle', [(X1 + 0.3, -0.6, 0.25), (X1 + 0.7, 0, 0.6), (X1 + 0.7, 0, 1.6), (X0 + 0.3, 0, 1.6), (X0 + 0.3, 0, 0.25), (X0 + 0.45, 0, 0.25)], 'air', 0.015, 0.3)
    m.overlay('pressure', join('pz', [cyl('ps', 0.24, 0.3, 1.2, 'pressure_8', 48, center=(X1 + 0.7, 0, 0), r_in=0.22), cyl('pr', 0.05, 0.2, 0.3, 'pressure_1', 24, axis='X', center=(0, 0, 0.25), r_in=0.04)]),
              'Pressure release creates micro-bubbles', 'Part of the clarified water is pumped to the saturator at about 4–6 bar, where air dissolves into it (Henry\'s law: more gas dissolves at higher pressure). '
              'At the release valve the pressure drops to atmospheric and the excess air comes out of solution as micro-bubbles, which attach to flocs and float them to the surface.', split=True)
    return m.export(out)


# =============================================================== EQ-264 Oil-water separator (CPI)
def oil_water_separator(out):
    m = _model('oil_water_separator', 'Oil–Water Separator (Corrugated Plate Interceptor, CPI)')
    X0, X1, W, H = -1.5, 1.5, 0.9, 1.1
    tk = csg('tk', [box('to', (X1 - X0 + 0.06, W + 0.06, H), (0, 0, H / 2), 'paint_grey')], [box('ti', (X1 - X0, W, H), (0, 0, H / 2 + 0.03), 'paint_grey')], 'paint_grey')
    bw = [box('ib', (0.02, W, 0.7), (X0 + 0.5, 0, 0.6), 'paint_grey'), box('ow', (0.02, W, 0.75), (X1 - 0.35, 0, 0.375 + 0.03), 'paint_grey'), box('ub', (0.02, W, 0.5), (X1 - 0.5, 0, H - 0.25), 'paint_grey')]
    hp = lathe('sh', [(0.0, 0.05), (0.01, 0.05), (0.3, 0.3), (0.0, 0.3)], 'paint_grey', 4, a0=math.pi / 4, a1=math.pi / 4 + TAU, center=(-0.1, 0, 0))
    P(m, 'tank', 'Separator Tank: Inlet Baffle, Oil-Retention Baffle, Outlet Weir & Sludge Hopper', 'tank', [tk, hp] + bw, explode=(0, 0.6, 0), ref='ows_tank')
    pk = []
    for k in range(10):
        pl = box(f'cp{k}', (0.9, W - 0.04, 0.008), (-0.1, 0, 0.32 + 0.055 * k), 'polypropylene')
        pk.append(rotate(pl, math.radians(45), 'Y', (-0.1, 0, 0.32 + 0.055 * k)))
    pk += [box(f'pf{s}', (0.8, 0.02, 0.8), (-0.1, s * (W / 2 - 0.02), 0.6), 'stainless') for s in (-1, 1)]
    P(m, 'plate_pack', 'Corrugated Plate Pack (45°) — short rise distance for oil droplets', 'internals', pk, explode=(0, -0.7, 0.4), ref='ows_plates', section='split')
    pwt = P(m, 'water', 'Water Phase', 'fluid', box('wt', (X1 - X0 - 0.4, W / 2 - 0.01, 0.85), (-0.15, W / 4, 0.46), 'water'), explode=(0, -0.3, 0), ref='ows_tank', section='keep')
    poi = P(m, 'oil_layer', 'Separated Oil Layer', 'fluid', box('ol', (X1 - X0 - 0.95, W / 2 - 0.01, 0.07), (-0.35, W / 4, 0.92), 'hydraulic_oil'), explode=(0, -0.3, 0.3), ref='ows_oil', section='keep')
    keys_loop(m, poi, lambda t: (1, 1, 1 + 0.3 * smooth_pulse(t, 0.4, 0.2, 0.3)), 'scale')
    sk = [cyl('sk', 0.05, -0.6, 0.6, 'stainless', 24, axis='Y', center=(0.9, 0, 0.93)), box('sks', (0.02, 1.0, 0.03), (0.9, 0, 0.97), 'stainless'), nozzle('so', (0.9, -W / 2, 0.93), (0, -1, 0), 0.04, 0.25)]
    psk = P(m, 'oil_skimmer', 'Rotatable Slotted-Pipe Oil Skimmer', 'skimmer', sk, explode=(0, -0.4, 0.4), ref='ows_skimmer', section='keep', pivot=(0.9, 0, 0.93))
    keys_loop(m, psk, lambda t: (0, -0.4 * smooth_pulse(t, 0.4, 0.2, 0.3), 0), 'rotation_euler')
    nz = [nozzle('in', (X0, 0, 0.75), (-1, 0, 0), 0.07, 0.3), nozzle('out', (X1, 0, 0.6), (1, 0, 0), 0.07, 0.3), nozzle('sd', (-0.1, 0, 0.05), (0, 0, -1), 0.04, 0.2)]
    P(m, 'nozzles', 'Inlet, Clean-Water Outlet & Sludge Drain', 'nozzles', nz, explode=(0, 0, -0.3), ref='ows_tank', section='keep')
    droplets(m, 'oil_droplets', 'Oil Droplets rising to the Plates and Surface', -0.5, 0.3, 0.35, 0.88, n=14, mat='hydraulic_oil', y=0.15, r=0.012)
    droplets(m, 'sludge', 'Solids settling into the Hopper', -0.4, 0.2, 0.75, 0.1, n=8, mat='coal', y=0.25, r=0.012)
    m.flow('oily_water', [(X0 - 0.35, 0, 0.75), (X0 + 0.4, 0.1, 0.75), (X0 + 0.4, 0.1, 0.3), (-0.5, 0.1, 0.35), (0.3, 0.1, 0.8), (X1 - 0.5, 0.1, 0.3), (X1 - 0.38, 0.1, 0.78), (X1 + 0.35, 0, 0.6)], 'water', 0.02, 0.4)
    m.flow('oil', [(-0.3, 0.1, 0.92), (0.9, 0.1, 0.95), (0.9, -W / 2 - 0.3, 0.93)], 'hydraulic_oil', 0.015, 0.2)
    m.overlay('pressure', join('sz', [box('sv', (0.02, 0.02, 0.5), (-0.35, -W / 2 - 0.08, 0.6), 'pressure_6')]), 'Stokes\' law sets the rise velocity',
              'An oil droplet rises at v = g·d²·(ρw − ρo)/(18·μ) (Stokes). Small droplets rise very slowly, so the inclined plates give each droplet only a short distance to rise before it meets a '
              'plate surface, coalesces and slides up to the oil layer. CPI separators typically remove free oil droplets down to roughly 50–60 µm; API separators ~ 150 µm.')
    return m.export(out)


# =============================================================== EQ-265 Coalescer
def coalescer(out):
    m = _model('coalescer', 'Liquid–Liquid Coalescer (Cartridge Coalescer + Vane Pack, Water Boot)')
    R, CZ, X0, L = 0.45, 1.05, -1.2, 2.4
    sh = vessel('sh', R, L, 0.01, 'paint_grey', axis='X', center=(0, 0, CZ), heads=('2:1', '2:1'), z0=X0)
    bt = vessel('bt', 0.15, 0.35, 0.008, 'paint_grey', heads=('2:1', 'flat'), z0=CZ - R - 0.35, center=(0.8, 0, 0))
    P(m, 'vessel', 'Horizontal Vessel & Water Boot', 'vessel', [sh, bt], explode=(0, 0.6, 0), ref='co_vessel')
    ts = cyl('ts', R - 0.01, X0 + 0.5, X0 + 0.53, 'steel', 48, axis='X', center=(0, 0, CZ))
    cr = [cyl(f'cc{k}', 0.07, X0 + 0.53, X0 + 1.3, 'polypropylene', 24, axis='X', center=(0, y, CZ + z), r_in=0.04) for k, (y, z) in enumerate(((-0.15, 0.12), (0.15, 0.12), (0, -0.05), (-0.18, -0.2), (0.18, -0.2)))]
    vp = [box(f'vn{k}', (0.25, 0.006, 2 * R * 0.8), (X0 + 1.6, -0.3 + 0.06 * k, CZ), 'steel') for k in range(11)]
    P(m, 'coalescing_elements', 'Tube Sheet, Coalescing Cartridges (inside-out) & Vane Separator Pack', 'internals', [ts] + cr + vp, explode=(0, -0.7, 0.3), ref='co_elements', section='keep')
    pl = P(m, 'liquid', 'Continuous Hydrocarbon Phase', 'fluid', _hliq('lq', R - 0.01, X0 + 0.05, X0 + L - 0.05, CZ, CZ + R - 0.1, 'hydraulic_oil'), explode=(0, -0.3, 0), ref='co_vessel', section='keep')
    pwb = P(m, 'boot_water', 'Separated Water in the Boot (interface controlled)', 'fluid', liquid_v('bw', 0.14, CZ - R - 0.35, CZ - R - 0.12, head='2:1', mat='water', cx=0.8), explode=(0, -0.3, -0.3), ref='co_boot', section='keep')
    animate_level(m, pwb, CZ - R - 0.13, 0.08, lambda t: smooth_pulse(t, 0.4, 0.2, 0.3))
    nz = [nozzle('in', (X0 - R * 0.5, 0, CZ), (-1, 0, 0), 0.06, 0.25), nozzle('out', (X0 + L + R * 0.5, 0, CZ + 0.1), (1, 0, 0), 0.06, 0.25), nozzle('wd', (0.8, 0, CZ - R - 0.35 - 0.075), (0, 0, -1), 0.03, 0.2),
          box('lt', (0.06, 0.05, 0.35), (1.0, 0, CZ - R - 0.2), 'paint_blue_dark')]
    P(m, 'nozzles_instruments', 'Inlet, Outlet, Water Drain & Interface Level Transmitter', 'nozzles', nz, explode=(0, 0, -0.3), ref='co_boot', section='keep')
    P(m, 'saddles', 'Saddles', 'structure', [box(f'sd{k}', (0.2, 0.7, CZ - R + 0.1), (x, 0, (CZ - R + 0.1) / 2), 'paint_grey') for k, x in enumerate((X0 + 0.4, X0 + L - 0.4))], explode=(0, 0, -0.3), ref='co_vessel', section='keep')
    pd = m.part('drops', 'Fine Water Droplets growing into Large Drops', 'flow_tracers', explode=(0, 0, 0), info={'ref': 'flow_tracers'})
    for i in range(10):
        ph = i / 10
        ms = pd.add(lathe(f'wd{i}', [(0.012 * math.sin(k * math.pi / 6), -0.012 * math.cos(k * math.pi / 6)) for k in range(7)], 'water', 10), smooth_angle=80)
        lk, sk = [], []
        for f in range(OPERATE_FRAMES + 1):
            s_ = ((f / OPERATE_FRAMES) + ph) % 1.0
            x = X0 + 0.2 + (0.8 - X0 - 0.2) * s_
            g = 1.0 + 3.0 * min(1.0, max(0.0, (x - (X0 + 0.55)) / 0.8))
            z = CZ + 0.05 - (0.0 if x < X0 + 1.3 else (x - X0 - 1.3) / (0.8 - X0 - 1.3) * (R + 0.15))
            lk.append((1 + f, (x, 0.08 + 0.02 * (i % 3), z)))
            sk.append((1 + f, (g, g, g)))
        ms.location = lk[0][1]
        m.keyframes(ms, 'Operate', 'location', lk)
        m.keyframes(ms, 'Operate', 'scale', sk)
    m.flow('feed', [(X0 - 0.5, 0, CZ), (X0 + 0.5, 0.0, CZ), (X0 + 1.3, 0.0, CZ - 0.05), (X0 + L + 0.5, 0, CZ + 0.1)], 'hydraulic_oil', 0.015, 0.3)
    m.flow('water', [(0.6, 0.1, CZ - 0.2), (0.8, 0.0, CZ - R - 0.2), (0.8, 0, CZ - R - 0.65)], 'water', 0.015, 0.2)
    m.overlay('pressure', join('cz', [cyl('cz1', R + 0.03, X0 + 0.53, X0 + 1.3, 'pressure_7', 48, axis='X', center=(0, 0, CZ), r_in=R + 0.015)]), 'Coalescence: small drops become large drops',
              'Fine dispersed droplets (a few µm to tens of µm) are captured by the fibres of the coalescing media, merge with other captured droplets and leave the outer surface as large drops. '
              'Large drops settle quickly (Stokes: velocity ∝ d²) into the water boot. Surfactants can disarm coalescing media, so they are selected for the interfacial tension of the system.', split=True)
    return m.export(out)


# =============================================================== EQ-266 Molecular sieve adsorber (twin tower)
def molecular_sieve_adsorber(out):
    m = _model('molecular_sieve_adsorber', 'Twin-Tower Molecular Sieve Adsorber (Gas Drying, TSA Regeneration)')
    R, Z0, L = 0.4, 0.8, 1.8
    _twin(m, 'tower_a', -0.7, R, Z0, L, 'Adsorber A (adsorbing — gas flows down)', 'powder', 'msa_towers', 'msa_sieve', 'Tower A: Molecular Sieve Bed (zeolite 3A/4A/13X beads) with Ceramic Support Balls')
    _twin(m, 'tower_b', 0.7, R, Z0, L, 'Adsorber B (regenerating — hot gas flows up)', 'powder', 'msa_towers', 'msa_sieve', 'Tower B: Molecular Sieve Bed being Regenerated')
    vl = []
    for k, (x, z) in enumerate(((-0.7, Z0 + L + R * 0.5 + 0.2), (0.7, Z0 + L + R * 0.5 + 0.2), (-0.7, Z0 - R * 0.5 - 0.2), (0.7, Z0 - R * 0.5 - 0.2))):
        vl += [join(f'sv{k}', [box(f'svb{k}', (0.14, 0.14, 0.14), (x, 0, z), 'paint_blue_dark'), cyl(f'sva{k}', 0.07, z + 0.07, z + 0.2, 'paint_grey', 24, center=(x, 0, 0))])]
    vl += [hollow_pipe('tp', [(-1.3, 0, Z0 + L + R * 0.5 + 0.2), (1.3, 0, Z0 + L + R * 0.5 + 0.2)], 0.04, 'steel', 16), hollow_pipe('bp', [(-1.3, 0, Z0 - R * 0.5 - 0.2), (1.3, 0, Z0 - R * 0.5 - 0.2)], 0.04, 'steel', 16)]
    vl += [cyl(f'vs{k}', 0.04, min(z0, z1), max(z0, z1), 'steel', 16, center=(x, 0, 0)) for k, (x, z0, z1) in enumerate(((-0.7, Z0 + L + R * 0.5, Z0 + L + R * 0.5 + 0.2), (0.7, Z0 + L + R * 0.5, Z0 + L + R * 0.5 + 0.2), (-0.7, Z0 - R * 0.5, Z0 - R * 0.5 - 0.2), (0.7, Z0 - R * 0.5, Z0 - R * 0.5 - 0.2)))]
    P(m, 'switching_valves', 'Switching Valves & Inlet/Outlet Manifolds (automatic sequencing)', 'valves', vl, explode=(0, -0.4, 0.3), ref='msa_valves', section='keep')
    ht = join('ht', [vessel('hv', 0.2, 0.8, 0.008, 'paint_red', axis='X', center=(0, 0.9, 0.5), heads=('2:1', '2:1'), z0=1.2), box('hc', (0.3, 0.3, 0.4), (2.3, 0.9, 0.5), 'paint_grey')])
    P(m, 'regen_heater', 'Regeneration Gas Heater (≈ 200–300 °C)', 'heater', ht, explode=(0.4, 0.4, 0), ref='msa_heater', section='keep')
    P(m, 'supports', 'Skirts / Legs', 'structure', [legs(f'lg{k}', R, 0.0, Z0 - R * 0.4, n=4, cx=x) for k, x in enumerate((-0.7, 0.7))], explode=(0, 0, -0.3), ref='msa_towers', section='keep')
    mtz = P(m, 'mass_transfer_zone', 'Mass-Transfer Zone moving down Tower A (saturated above, fresh below)', 'media', _bed('mz', R - 0.005, Z0 + L - 0.45, Z0 + L - 0.15, 'pressure_6', -0.7), explode=(0, -0.5, 0), ref='msa_sieve', section='keep')
    keys_loop(m, mtz, lambda t: (0, -0.005, -1.2 * t), 'location')
    add_tracers(m, 'wet_gas', 'Wet Gas flowing Down through Tower A', [(-1.3, 0.1, Z0 + L + R * 0.5 + 0.2), (-0.7, 0.1, Z0 + L + R * 0.5 + 0.2), (-0.7, 0.1, Z0 - R * 0.5 - 0.2), (-1.3, 0.1, Z0 - R * 0.5 - 0.2)], n=10, radius=0.018, mat='air')
    add_tracers(m, 'regen_gas', 'Hot Regeneration Gas flowing Up through Tower B', [(1.3, 0.1, Z0 - R * 0.5 - 0.2), (0.7, 0.1, Z0 - R * 0.5 - 0.2), (0.7, 0.1, Z0 + L + R * 0.5 + 0.2), (1.3, 0.1, Z0 + L + R * 0.5 + 0.2)], n=10, radius=0.018, mat='steam')
    m.flow('wet_gas_in', [(-1.5, 0, Z0 + L + R * 0.5 + 0.2), (-0.7, 0, Z0 + L + R * 0.5 + 0.2), (-0.7, 0, Z0 - R * 0.5 - 0.2), (-1.5, 0, Z0 - R * 0.5 - 0.2)], 'air', 0.02, 0.4)
    m.flow('regeneration', [(2.0, 0.9, 0.5), (1.3, 0, Z0 - R * 0.5 - 0.2), (0.7, 0, Z0 - R * 0.5 - 0.2), (0.7, 0, Z0 + L + R * 0.5 + 0.2), (1.5, 0, Z0 + L + R * 0.5 + 0.2)], 'steam', 0.02, 0.4)
    _bands_z(m, [(Z0 + L - 0.6, Z0 + L, 7), (Z0, Z0 + L - 0.6, 2)], R, 'Adsorption front and regeneration temperature',
             'In the adsorbing tower water is held in the zeolite pores; the saturated zone grows from the inlet and the mass-transfer zone moves down until breakthrough, when the towers switch. '
             'Regeneration heats the bed (typically ~ 200–300 °C, TSA) to drive the water off, then cools it. Molecular sieves reach very low dew points (≈ −70 to −100 °C, < 1 ppmv water) — needed before cryogenic units.', cx=-0.7)
    return m.export(out)


# =============================================================== EQ-267 Activated alumina adsorber
def activated_alumina_adsorber(out):
    m = _model('activated_alumina_adsorber', 'Activated Alumina Adsorber (Fixed Bed, Down-Flow)')
    R, Z0, L = 0.5, 0.7, 1.8
    v = vessel('vs', R, L, 0.012, 'paint_blue', heads=('2:1', '2:1'), z0=Z0)
    mh = nozzle('mh', (R, 0, Z0 + L - 0.3), (1, 0, 0), 0.15, 0.15)
    P(m, 'vessel', 'Adsorber Vessel with Manway', 'vessel', [v, mh], explode=(0, 0.6, 0), ref='aa_vessel')
    layers = [('cs1', Z0 - 0.1, Z0 + 0.08, 'cast_iron', 'Ceramic Balls (large, bottom support)'), ('cs2', Z0 + 0.08, Z0 + 0.18, 'refractory', 'Ceramic Balls (small)'),
              ('al', Z0 + 0.18, Z0 + L - 0.25, 'powder', 'Activated Alumina Beads'), ('ht', Z0 + L - 0.25, Z0 + L - 0.15, 'cast_iron', 'Hold-Down Ceramic Balls')]
    bd = [_bed(n, R - 0.012 if z0 >= Z0 else R * 0.8, z0, z1, mt) for n, z0, z1, mt, _ in layers]
    P(m, 'bed', 'Graded Bed: Support Balls, Activated Alumina, Hold-Down Balls', 'media', bd, explode=(0, -0.5, 0), ref='aa_bed', section='keep')
    ds = [cyl('ds', 0.06, Z0 + L - 0.05, Z0 + L + R * 0.5, 'stainless', 24), lathe('dsc', [(0.06, Z0 + L - 0.1), (0.2, Z0 + L - 0.1), (0.2, Z0 + L - 0.08), (0.06, Z0 + L - 0.08)], 'stainless', 32)]
    cl = [cyl('cl', 0.05, Z0 - R * 0.5, Z0 + 0.0, 'stainless', 24)] + [cyl(f'lt{k}', 0.02, -0.35, 0.35, 'stainless', 12, axis='X' if k == 0 else 'Y', center=(0, 0, Z0 - 0.03) if k == 0 else (0, 0, Z0 - 0.03)) for k in range(2)]
    P(m, 'internals', 'Inlet Distributor & Outlet Collector (laterals with screens)', 'internals', ds + cl, explode=(0, -0.4, 0.3), ref='aa_internals', section='keep')
    nz = [nozzle('in', (0, 0, Z0 + L + R * 0.5), (0, 0, 1), 0.06, 0.2), nozzle('out', (0, 0, Z0 - R * 0.5), (0, 0, -1), 0.06, 0.2)] + [nozzle(f'sp{k}', (-R, 0, z), (-1, 0, 0), 0.015, 0.12) for k, z in enumerate((Z0 + 0.5, Z0 + 1.0, Z0 + 1.4))]
    P(m, 'nozzles', 'Inlet, Outlet & Bed Sample Points', 'nozzles', nz, explode=(0, 0, 0.3), ref='aa_vessel', section='keep')
    P(m, 'legs', 'Support Legs', 'structure', legs('lg', R, 0.0, Z0 - R * 0.4, n=4), explode=(0, 0, -0.3), ref='aa_vessel', section='keep')
    mtz = P(m, 'mass_transfer_zone', 'Mass-Transfer Zone travelling down the Bed', 'media', _bed('mz', R - 0.008, Z0 + L - 0.65, Z0 + L - 0.3, 'pressure_6'), explode=(0, -0.6, 0), ref='aa_bed', section='keep')
    keys_loop(m, mtz, lambda t: (0, -0.005, -1.0 * t), 'location')
    sat = P(m, 'saturated_zone', 'Saturated (spent) Zone above the MTZ', 'media', _bed('sz', R - 0.006, Z0 + L - 0.3, Z0 + L - 0.25, 'pressure_8'), explode=(0, -0.6, 0.2), ref='aa_bed', section='keep', pivot=(0, 0, Z0 + L - 0.25))
    keys_loop(m, sat, lambda t: (1, 1, 1 + 20 * t), 'scale')
    keys_loop(m, sat, lambda t: (0, -0.008, 0), 'location')
    add_tracers(m, 'fluid', 'Fluid flowing Down through the Bed', [(0, 0.1, Z0 + L + R * 0.5 + 0.2), (0, 0.1, Z0 + L - 0.1), (0.25, 0.1, Z0 + 1.0), (0, 0.1, Z0 + 0.1), (0, 0.1, Z0 - R * 0.5 - 0.2)], n=10, radius=0.018, mat='water')
    m.flow('feed', [(0, 0, Z0 + L + R * 0.5 + 0.3), (0, 0, Z0 + L - 0.1)], 'flow_suction', 0.02, 0.2)
    m.flow('treated', [(0, 0, Z0 + 0.1), (0, 0, Z0 - R * 0.5 - 0.3)], 'water', 0.02, 0.2)
    m.overlay('pressure', join('bz', [cyl('bk', R + 0.04, Z0 + 0.18, Z0 + L - 0.25, 'pressure_4', 48, r_in=R + 0.02)]), 'Breakthrough curve',
              'The bed works from the inlet down: the top becomes saturated (red), the mass-transfer zone (orange) moves down, and the outlet stays clean until the zone reaches the bottom — breakthrough. '
              'Activated alumina is used for drying gases and liquids (to dew points around −40 °C), fluoride and arsenic removal from water, and HCl/acid removal; it is regenerated by heating (drying duty) '
              'or chemically (e.g. caustic and acid for fluoride).', split=True)
    return m.export(out)


# =============================================================== EQ-268 Desiccant dryer (heatless PSA)
def desiccant_dryer(out):
    m = _model('desiccant_dryer', 'Heatless (Pressure-Swing) Twin-Tower Desiccant Air Dryer')
    R, Z0, L = 0.18, 0.55, 1.3
    _twin(m, 'tower_left', -0.35, R, Z0, L, 'Left Tower (drying — under line pressure)', 'powder', 'dd_towers', 'dd_desiccant', 'Left Tower Desiccant (activated alumina / molecular sieve)')
    _twin(m, 'tower_right', 0.35, R, Z0, L, 'Right Tower (regenerating — depressurised, purged)', 'powder', 'dd_towers', 'dd_desiccant', 'Right Tower Desiccant')
    zt, zb = Z0 + L + R * 0.5 + 0.12, Z0 - R * 0.5 - 0.12
    mv = [cyl('tm', 0.04, -0.5, 0.5, 'aluminium', 24, axis='X', center=(0, 0, zt)), cyl('bm', 0.05, -0.5, 0.5, 'aluminium', 24, axis='X', center=(0, 0, zb)),
          box('svb', (0.25, 0.15, 0.15), (0, 0, zb), 'aluminium'), box('cv', (0.2, 0.12, 0.12), (0, 0, zt), 'aluminium'), cyl('po', 0.012, -0.1, 0.1, 'brass', 12, axis='X', center=(0, 0.08, zt))]
    mv += [cyl(f'ms{s}', 0.07, 0.0, 0.3, 'paint_grey', 24, center=(s * 0.35, -0.25, 0)) for s in (-1, 1)]
    mv += [cyl(f'vs{k}', 0.035, min(a, b), max(a, b), 'aluminium', 16, center=(x, 0, 0)) for k, (x, a, b) in enumerate(((-0.35, zt, Z0 + L + R * 0.5), (0.35, zt, Z0 + L + R * 0.5), (-0.35, zb, Z0 - R * 0.5), (0.35, zb, Z0 - R * 0.5)))]
    P(m, 'valve_manifolds', 'Inlet Shuttle/Switching Valves, Outlet Check Valves, Purge Orifice & Exhaust Silencers', 'valves', mv, explode=(0, -0.4, 0.2), ref='dd_valves', section='keep')
    shut = P(m, 'shuttle', 'Inlet Shuttle Spool (switches towers)', 'valves', cyl('sp', 0.035, -0.08, 0.08, 'chrome', 16, axis='X', center=(0, -0.08, zb)), explode=(0, -0.5, 0), ref='dd_valves', section='keep')
    keys_loop(m, shut, lambda t: (0.06 if t < 0.5 else -0.06, 0, 0))
    flt = [vessel(f'fl{k}', 0.07, 0.35, 0.004, 'aluminium', heads=('flat', '2:1'), z0=zb - 0.1, center=(x, 0, 0)) for k, x in enumerate((-0.85, 0.85))]
    flt += [cyl('fa', 0.03, -0.85, -0.5, 'aluminium', 16, axis='X', center=(0, 0, zb + 0.15)), cyl('fb', 0.03, 0.5, 0.85, 'aluminium', 16, axis='X', center=(0, 0, zt))]
    P(m, 'filters', 'Coalescing Pre-Filter & Particulate After-Filter', 'filters', flt, explode=(0, 0, -0.3), ref='dd_filters', section='keep')
    P(m, 'controller', 'Controller (timer or dew-point dependent switching)', 'controls', box('ct', (0.3, 0.12, 0.35), (0, 0.35, 1.2), 'paint_grey'), explode=(0, 0.4, 0), ref='dd_controller', section='keep')
    P(m, 'frame', 'Frame', 'structure', [box('fr', (1.2, 0.5, 0.06), (0, 0, 0.03), 'paint_grey')] + [box(f'fp{k}', (0.05, 0.05, 1.9), (s * 0.6, 0.2, 0.95), 'paint_grey') for k, s in enumerate((-1, 1))], explode=(0, 0, -0.3), ref='dd_towers', section='keep')
    m.flow('drying_left', [(-0.85, 0, zb + 0.15), (-0.35, 0, zb), (-0.35, 0, zt), (0.85, 0, zt)], 'air', 0.015, 0.3, active=[(0.0, 0.5)])
    m.flow('purge_right', [(0.0, 0.08, zt), (0.35, 0.05, zt - 0.1), (0.35, 0.05, zb + 0.05), (0.35, -0.25, 0.3)], 'steam', 0.012, 0.3, active=[(0.0, 0.5)])
    m.flow('drying_right', [(-0.85, 0, zb + 0.15), (0.35, 0, zb), (0.35, 0, zt), (0.85, 0, zt)], 'air', 0.015, 0.3, active=[(0.5, 1.0)])
    m.flow('purge_left', [(0.0, 0.08, zt), (-0.35, 0.05, zt - 0.1), (-0.35, 0.05, zb + 0.05), (-0.35, -0.25, 0.3)], 'steam', 0.012, 0.3, active=[(0.5, 1.0)])
    m.overlay('pressure', join('pz', [cyl('pl', R + 0.04, Z0, Z0 + L, 'pressure_7', 48, center=(-0.35, 0, 0), r_in=R + 0.02), cyl('pr', R + 0.04, Z0, Z0 + L, 'pressure_1', 48, center=(0.35, 0, 0), r_in=R + 0.02)]),
              'Pressure swing: adsorb at high pressure, desorb at low', 'The drying tower works at line pressure (red); the desiccant adsorbs water vapour. The other tower is vented to atmosphere (blue) and swept by '
              'a small part of the dry air (purge, typically ~ 15–20 % for heatless dryers) which carries the water out through the silencer. Towers switch every few minutes. Typical pressure dew point −40 °C '
              '(−70 °C with molecular sieve).', split=True)
    return m.export(out)


# =============================================================== EQ-269 Gas dehydration unit (TEG)
def gas_dehydration_unit(out):
    m = _model('gas_dehydration_unit', 'TEG Gas Dehydration Unit (Contactor + Glycol Regeneration)')
    R, Z0, L = 0.35, 0.8, 2.6
    ct = vessel('ct', R, L, 0.012, 'paint_grey', heads=('2:1', '2:1'), z0=Z0, center=(-1.2, 0, 0))
    P(m, 'contactor', 'Glycol Contactor (absorber tower)', 'vessel', ct, explode=(0, 0.6, 0), ref='gd_contactor')
    trs = []
    for k in range(6):
        t = tray(f'tr{k}', R - 0.012, Z0 + 0.6 + 0.3 * k, holes=True, weir=True, dc_side=1 if k % 2 else -1)
        t.data.transform(Matrix.Translation((-1.2, 0, 0)))
        trs.append(t)
    trs.append(half(mesh_pad('mp', R - 0.012, Z0 + L - 0.25, Z0 + L - 0.12, center=(-1.2, 0, 0)), 'steel'))
    P(m, 'trays_demister', 'Bubble-Cap/Valve Trays & Mist Eliminator', 'internals', trs, explode=(0, -0.5, 0), ref='gd_trays', section='keep')
    rb = vessel('rb', 0.25, 1.2, 0.01, 'paint_grey', axis='X', center=(0, 0, 0.6), heads=('2:1', '2:1'), z0=0.3)
    st = vessel('st', 0.1, 0.9, 0.006, 'paint_grey', heads=('2:1', '2:1'), z0=0.85, center=(0.9, 0, 0))
    P(m, 'regenerator', 'Reboiler (fire-tube) & Still Column (water vapour vented)', 'vessel', [rb, st], explode=(0.5, 0.5, 0), ref='gd_regenerator')
    ft = cyl('ftb', 0.08, 0.35, 1.25, 'steel', 24, axis='X', center=(0, 0, 0.55), r_in=0.07)
    P(m, 'fire_tube', 'Reboiler Fire Tube', 'heater', ft, explode=(0.4, -0.4, 0), ref='gd_regenerator', section='keep')
    _flame(m, 'reboiler_flame', 'Fire-Tube Burner Flame', (0.38, 0, 0.55), (1, 0, 0), 0.6, 0.05, 'gd_regenerator')
    fts = vessel('fts', 0.15, 0.5, 0.006, 'paint_grey', axis='X', center=(0, 0.6, 1.4), heads=('2:1', '2:1'), z0=-0.4)
    hx = vessel('hx', 0.08, 0.6, 0.006, 'paint_blue', axis='X', center=(0, -0.6, 1.2), heads=('flat', 'flat'), z0=-0.4)
    P(m, 'flash_tank_exchanger', 'Glycol Flash Tank & Lean/Rich Heat Exchanger', 'vessel', [fts, hx], explode=(0, 0.5, 0.4), ref='gd_flash', section='keep')
    _pump(m, 'glycol_pump', 'Lean Glycol Pump', -0.5, -0.6, 0.25, 'gd_pump', explode=(0, -0.4, 0))
    pp = [hollow_pipe('lg', [(-0.5, -0.6, 0.4), (-0.5, -0.6, Z0 + L - 0.2), (-1.2 + R, -0.0, Z0 + L - 0.35)], 0.025, 'stainless', 12, bend=0.06),
          hollow_pipe('rg', [(-1.2 + R, 0, Z0 + 0.25), (-0.6, 0.6, 1.4), (-0.4, 0.6, 1.4)], 0.025, 'stainless', 12, bend=0.06),
          hollow_pipe('r2', [(0.1, 0.6, 1.4), (0.9, 0.6, 1.4), (0.9, 0.0, 1.5)], 0.025, 'stainless', 12, bend=0.06),
          nozzle('gin', (-1.2 - R, 0, Z0 + 0.3), (-1, 0, 0), 0.07, 0.3), nozzle('gout', (-1.2, 0, Z0 + L + R * 0.5), (0, 0, 1), 0.07, 0.25)]
    P(m, 'piping', 'Lean & Rich Glycol Lines, Wet-Gas Inlet, Dry-Gas Outlet', 'piping', pp, explode=(0, 0, 0.3), ref='gd_piping', section='keep')
    P(m, 'skid', 'Skid & Contactor Skirt', 'structure', [box('sk', (3.2, 1.6, 0.06), (-0.3, 0, 0.03), 'paint_grey'), cyl('skt', R, 0.06, Z0 - R * 0.4, 'paint_grey', 48, center=(-1.2, 0, 0), r_in=R - 0.01)],
      explode=(0, 0, -0.3), ref='gd_contactor', section='keep')
    droplets(m, 'glycol_drops', 'Lean Glycol flowing Down across the Trays', -1.4, -1.0, Z0 + 2.2, Z0 + 0.5, n=10, mat='hydraulic_oil', y=0.12, r=0.014)
    add_tracers(m, 'gas_bubbles', 'Gas bubbling Up through the Glycol on each Tray', [(-1.2, 0.1, Z0 + 0.35), (-1.25, 0.1, Z0 + 1.3), (-1.15, 0.1, Z0 + 2.2), (-1.2, 0.1, Z0 + L + 0.3)], n=10, radius=0.02, mat='air')
    m.flow('gas', [(-1.2 - R - 0.4, 0, Z0 + 0.3), (-1.2, 0.05, Z0 + 0.4), (-1.2, 0.05, Z0 + L + R)], 'air', 0.025, 0.4)
    m.flow('lean_glycol', [(0.3, 0, 0.6), (-0.5, -0.6, 0.25), (-0.5, -0.6, Z0 + L - 0.2), (-1.2, 0.05, Z0 + L - 0.35)], 'hydraulic_oil', 0.015, 0.4)
    m.flow('rich_glycol', [(-1.2, 0.05, Z0 + 0.25), (-0.4, 0.6, 1.4), (0.9, 0.6, 1.4), (0.9, 0, 1.6), (0.9, 0, 1.0), (0.6, 0, 0.75)], 'flow_discharge', 0.015, 0.4)
    m.flow('water_vapour', [(0.9, 0, 1.75), (0.9, 0, 2.2)], 'steam', 0.015, 0.2)
    _bands_z(m, [(Z0, Z0 + L, 3)], R, 'Absorption at high pressure, regeneration at high temperature', 'In the contactor wet gas (often 30–100 bar) rises through trays while lean triethylene glycol (TEG, typically ~ 98.5–99.9 wt %) '
             'absorbs its water. Rich glycol is flashed, heated and boiled in the reboiler at about 200 °C (below TEG decomposition ~ 206 °C) to drive the water off through the still. Typical outlet water '
             'content ≈ 7 lb/MMscf (~ 110 mg/Sm³) pipeline specification.', cx=-1.2)
    return m.export(out)


# =============================================================== EQ-270 Sand trap
def sand_trap(out):
    m = _model('sand_trap', 'Vertical Cyclonic Sand Trap (Desander Vessel)')
    R, Z0, L = 0.4, 1.1, 1.3
    v = vessel('vs', R, L, 0.014, 'paint_grey', heads=('cone', '2:1'), z0=Z0)
    P(m, 'vessel', 'Vertical Pressure Vessel with Conical Bottom', 'vessel', v, explode=(0, 0.6, 0), ref='st_vessel')
    vf = [cyl('vf', 0.12, Z0 + L - 0.6, Z0 + L + R * 0.5, 'steel', 32, r_in=0.11), box('wp', (0.03, 0.3, 0.3), (-R + 0.1, 0.18, Z0 + L - 0.25), 'steel')]
    P(m, 'internals', 'Vortex Finder (outlet tube) & Inlet Wear Plate', 'internals', vf, explode=(0, -0.4, 0.4), ref='st_internals', section='keep')
    sd = P(m, 'sand_bed', 'Accumulated Sand in the Cone', 'media', lathe('sb', [(0.0, Z0 - R + 0.01), (0.12 * R, Z0 - R + 0.01), ((R - 0.014) * 0.6, Z0 - R * 0.55), (0.0, Z0 - R * 0.55)], 'sand', 48, a0=0.0, a1=math.pi, cap_mat='sand'), explode=(0, -0.3, -0.2), ref='st_sand', section='keep', pivot=(0, 0, Z0 - R))
    keys_loop(m, sd, lambda t: (1, 1, 1.0 + 0.6 * smooth_pulse(t, 0.6, 0.1, 0.2)), 'scale')
    nz = [nozzle('in', (-R, 0.18, Z0 + L - 0.25), (-1, 0, 0), 0.07, 0.35), nozzle('out', (0, 0, Z0 + L + R * 0.5), (0, 0, 1), 0.08, 0.2)]
    dv = join('dv', [nozzle('dn', (0, 0, Z0 - R), (0, 0, -1), 0.04, 0.25), box('dvb', (0.12, 0.12, 0.12), (0, 0, Z0 - R - 0.32), 'paint_blue_dark'), cyl('dva', 0.06, Z0 - R - 0.32, Z0 - R - 0.32, 'paint_grey', 16)])
    ins = [box('dpt', (0.1, 0.06, 0.12), (R + 0.15, 0, Z0 + 0.7), 'paint_grey'), cyl('dp1', 0.01, R, R + 0.12, 'steel', 8, axis='X', center=(0, 0, Z0 + L - 0.2)), cyl('dp2', 0.01, R, R + 0.12, 'steel', 8, axis='X', center=(0, 0, Z0 + 0.1))]
    P(m, 'nozzles_valves', 'Tangential Inlet, Gas/Liquid Outlet, Sand Dump Valve & ΔP / Sand Level Instruments', 'nozzles', nz + [dv] + ins, explode=(0, 0, -0.3), ref='st_valves', section='keep')
    P(m, 'legs', 'Support Legs', 'structure', legs('lg', R, 0.0, Z0 - R * 0.2, n=4), explode=(0, 0, -0.3), ref='st_vessel', section='keep')
    ps = m.part('sand_grains', 'Sand Grains spiralling down the Wall into the Cone', 'flow_tracers', explode=(0, 0, 0), info={'ref': 'flow_tracers'})
    for i in range(14):
        ph = i / 14
        ms = ps.add(lathe(f'sg{i}', [(0.014 * math.sin(k * math.pi / 6), -0.014 * math.cos(k * math.pi / 6)) for k in range(7)], 'sand', 10), smooth_angle=80)
        keys = []
        for f in range(OPERATE_FRAMES + 1):
            s_ = ((f / OPERATE_FRAMES) + ph) % 1.0
            z = Z0 + L - 0.25 - (L - 0.25 + R * 0.6) * s_
            rr = (R - 0.04) if z > Z0 else max(0.05, (R - 0.04) * (1 - (Z0 - z) / R))
            a = math.pi + TAU * 2.5 * s_
            keys.append((1 + f, (rr * math.cos(a), abs(rr * math.sin(a)) + 0.02, z)))
        ms.location = keys[0][1]
        m.keyframes(ms, 'Operate', 'location', keys)
    m.flow('inlet', [(-R - 0.45, 0.18, Z0 + L - 0.25), (-R + 0.05, 0.18, Z0 + L - 0.25), (0, 0.35, Z0 + L - 0.3), (0.3, 0.1, Z0 + L - 0.4)], 'flow_suction', 0.02, 0.3)
    m.flow('clean_outlet', [(0, 0.0, Z0 + L - 0.6), (0, 0, Z0 + L + R * 0.5 + 0.25)], 'water', 0.02, 0.2)
    m.flow('sand_dump', [(0, 0, Z0 - R + 0.05), (0, 0, Z0 - R - 0.5)], 'sand', 0.02, 0.2, active=[(0.8, 1.0)])
    _bands_z(m, [(Z0 + L - 0.45, Z0 + L, 6), (Z0, Z0 + L - 0.45, 3)], R, 'Swirl throws sand to the wall',
             'The tangential inlet sets up a swirl. Dense sand grains are thrown outward to the wall and slide down into the cone, while the cleaned fluid turns and leaves through the central vortex '
             'finder. Sand removal protects chokes, valves and separators from erosion. The rising ΔP / sand level triggers a dump (flush) of the cone — always under controlled conditions because '
             'of the erosive, pressurised discharge.', kind='pressure')
    return m.export(out)


# ===================================================================== metadata
def _std(*items):
    return [{'id': i, 'title': t, 'relevance': r, 'edition': 'to be verified'} for i, t, r in items]


def _c(fn, cons, mat, op='—', fm=('—',), insp=('Visual',)):
    return C(fn, cons, mat, op, list(fm), list(insp))


_PV = _std(('ASME BPVC VIII-1', 'Pressure vessels', 'Pressure parts.'),)
_WW = _std(('WEF/ASCE MOP 8', 'Design of Water Resource Recovery Facilities', 'Flotation and separation in wastewater.'),)
_OG = _std(('API 12J', 'Oil and gas separators', 'Separator design.'), ('GPSA Engineering Data Book', 'Dehydration and separation', 'Design data.'))

META = {
    'flotation_cell': {'summary': ('A mechanical flotation cell separates valuable minerals from waste rock. Air is blown down a hollow shaft and dispersed into fine bubbles by a spinning rotor and stator. Particles made '
                                   'water-repellent by reagents attach to the bubbles and rise to form a froth that overflows into a launder; the rest leaves as tailings.'),
                       'classification': {'family': 'Flotation', 'type': 'Forced-air mechanical cell'}, 'model_configuration': {'animation': 'Rotor turns; bubbles rise; froth'},
                       'standards': _std(('Maker standards', 'Flotation cell design', 'Cell volume and mechanism sizing.'),), 'references': ['Wills\' Mineral Processing Technology'],
                       'components': {'fc_tank': _c('Holds the pulp; collects froth.', 'Tank and launder.', 'Steel (lined).'), 'fc_pulp': _c('Ore slurry.', '—', '—'), 'fc_froth': _c('Mineral-laden froth.', '—', '—'),
                                      'fc_mechanism': _c('Disperses air; suspends solids.', 'Rotor & stator.', 'Rubber-lined steel.', '—', ['Wear'], ['Measure clearances']), 'fc_drive': _c('Turns rotor.', 'Motor, belts, bridge.', '—')}},
    'dissolved_air_flotation_unit': {'summary': ('A dissolved air flotation (DAF) unit removes suspended solids, oil and grease from water. Part of the clarified water is pressurised and saturated with air; when the pressure is released '
                                                 'in the tank, micro-bubbles form and float the flocs to the surface, where a skimmer removes them as sludge.'),
                                     'classification': {'family': 'Flotation', 'type': 'Rectangular DAF with recycle pressurisation'}, 'model_configuration': {'animation': 'Micro-bubbles; skimmer flights move'},
                                     'standards': _WW, 'references': ['Metcalf & Eddy — Wastewater Engineering'],
                                     'components': {'daf_tank': _c('Contact and separation zones.', 'Tank with baffle.', 'Stainless/coated steel.'), 'daf_float': _c('Float sludge and hopper.', '—', '—'),
                                                    'daf_skimmer': _c('Removes float.', 'Chain-and-flight skimmer.', 'PP flights, steel chain.', '—', ['Chain wear'], ['Inspect']),
                                                    'daf_saturator': _c('Dissolves air into recycle water.', 'Pressure vessel, recycle pump.', 'Steel.'), 'daf_release': _c('Releases pressure → micro-bubbles.', 'Valves/nozzles, piping.', 'Stainless.')}},
    'oil_water_separator': {'summary': ('An oil–water separator removes free oil and settleable solids from wastewater by gravity. In a corrugated plate interceptor (CPI), inclined plates give oil droplets a short distance to rise; '
                                        'they coalesce on the plates, rise to the surface layer and are skimmed off, while solids slide into a hopper.'),
                            'classification': {'family': 'Gravity separator', 'type': 'Corrugated plate interceptor'}, 'model_configuration': {'animation': 'Oil droplets rise; skimmer tilts'},
                            'standards': _std(('API Publication 421', 'Design and operation of oil–water separators', 'Design basis.'),), 'references': ['API 421'],
                            'components': {'ows_tank': _c('Holds the flow; baffles and weir.', 'Concrete/steel tank with hopper.', 'Steel/concrete.'), 'ows_plates': _c('Short rise distance; coalescence.', 'Corrugated plate pack.', 'PP/FRP.', '—', ['Fouling'], ['Clean']),
                                           'ows_oil': _c('Separated oil.', '—', '—'), 'ows_skimmer': _c('Removes oil.', 'Slotted pipe skimmer.', 'Stainless.')}},
    'coalescer': {'summary': ('A liquid–liquid coalescer removes fine water droplets from hydrocarbons (or oil from water). The fluid passes through coalescing cartridges whose fibres capture small droplets and merge them into '
                              'large drops; a vane pack catches remaining drops, and the separated water settles into the boot where an interface controller drains it.'),
                  'classification': {'family': 'Liquid–liquid separator', 'type': 'Horizontal cartridge coalescer with water boot'}, 'model_configuration': {'animation': 'Droplets grow and settle'},
                  'standards': _PV, 'references': ['Maker coalescer design guides'],
                  'components': {'co_vessel': _c('Pressure envelope.', 'Horizontal vessel.', 'Carbon steel.'), 'co_elements': _c('Coalesce droplets.', 'Cartridges, tube sheet, vane pack.', 'Glass fibre/PTFE/steel.', '—', ['Disarming by surfactants, plugging'], ['ΔP, outlet water content']),
                                 'co_boot': _c('Collects water; interface control.', 'Boot, LT, drain.', 'Steel.')}},
    'molecular_sieve_adsorber': {'summary': ('A molecular sieve adsorber dries gas (or removes CO₂/H₂S/mercaptans) using zeolite beads with precisely sized pores. Two towers alternate: one adsorbs while the other is regenerated '
                                             'with hot gas (temperature swing adsorption). Very low dew points are reached.'),
                                 'classification': {'family': 'Adsorber', 'type': 'Twin-tower TSA molecular sieve dehydrator'}, 'model_configuration': {'animation': 'MTZ moves; regeneration flow'},
                                 'standards': _OG + _PV, 'references': ['GPSA Engineering Data Book — Dehydration'],
                                 'components': {'msa_towers': _c('Contain the beds.', 'Vertical vessels.', 'Carbon steel.'), 'msa_sieve': _c('Adsorbs water.', 'Zeolite 3A/4A/13X beads, ceramic balls.', 'Zeolite.', '—', ['Ageing, crushing, coking'], ['Dew point, ΔP']),
                                                'msa_valves': _c('Switch towers.', 'Automated valves.', 'Steel.', '—', ['Leak-by'], ['Leak test']), 'msa_heater': _c('Heats regeneration gas.', 'Heater.', '—')}},
    'activated_alumina_adsorber': {'summary': ('An activated alumina adsorber passes a gas or liquid down through a fixed bed of porous aluminium-oxide beads. The beads adsorb water (drying) or contaminants such as fluoride, arsenic or acids. '
                                               'The working zone moves down the bed until breakthrough, then the bed is regenerated or replaced.'),
                                   'classification': {'family': 'Adsorber', 'type': 'Fixed-bed down-flow adsorber'}, 'model_configuration': {'animation': 'Mass-transfer zone travels down'},
                                   'standards': _PV, 'references': ['Maker activated alumina data'],
                                   'components': {'aa_vessel': _c('Contains the bed.', 'Vessel with manway.', 'Carbon steel (lined if needed).'), 'aa_bed': _c('Adsorbs.', 'Graded ceramic balls + alumina.', 'Al₂O₃.', '—', ['Fines, channelling'], ['ΔP, samples']),
                                                  'aa_internals': _c('Distribute/collect flow.', 'Distributor, laterals with screens.', 'Stainless.')}},
    'desiccant_dryer': {'summary': ('A heatless desiccant dryer dries compressed air by pressure-swing adsorption. One tower dries the air at line pressure while the other is depressurised and purged with part of the dried air; '
                                    'the towers switch every few minutes.'),
                        'classification': {'family': 'Compressed air dryer', 'type': 'Heatless twin-tower PSA'}, 'model_configuration': {'animation': 'Towers alternate; shuttle valve moves'},
                        'standards': _std(('ISO 8573-1', 'Compressed air — contaminants and purity classes', 'Dew point classes.'), ('ISO 7183', 'Compressed air dryers — specifications and testing', 'Performance.')),
                        'references': ['ISO 8573-1'],
                        'components': {'dd_towers': _c('Contain desiccant.', 'Aluminium/steel towers.', '—'), 'dd_desiccant': _c('Adsorbs water vapour.', 'Activated alumina / molecular sieve.', '—', '—', ['Oil contamination, dusting'], ['Dew point']),
                                       'dd_valves': _c('Switch towers; purge.', 'Shuttle/switching valves, orifice, silencers.', '—'), 'dd_filters': _c('Protect desiccant and downstream.', 'Pre/after filters.', '—'),
                                       'dd_controller': _c('Controls cycle.', 'Timer / dew-point control.', '—')}},
    'gas_dehydration_unit': {'summary': ('A TEG gas dehydration unit removes water vapour from natural gas so it does not form hydrates or corrode pipelines. In the contactor, wet gas rises through trays against a downflow of lean '
                                         'triethylene glycol, which absorbs the water. The rich glycol is regenerated by boiling off the water in a reboiler and returned.'),
                             'classification': {'family': 'Gas treatment', 'type': 'TEG absorption with thermal regeneration'}, 'model_configuration': {'animation': 'Glycol falls, gas bubbles up; reboiler flame'},
                             'standards': _OG + _PV, 'references': ['GPSA Engineering Data Book — Dehydration', 'Campbell — Gas Conditioning and Processing'],
                             'components': {'gd_contactor': _c('Contacts gas and glycol.', 'Tower with skirt.', 'Carbon steel.'), 'gd_trays': _c('Mass transfer; mist removal.', 'Trays/structured packing, mist eliminator.', 'Stainless.'),
                                            'gd_regenerator': _c('Boils water out of glycol.', 'Reboiler with fire tube, still column.', 'Steel.', '≈ 200 °C max (TEG degrades ~ 206 °C).', ['Glycol degradation, fouling'], ['Glycol analysis']),
                                            'gd_flash': _c('Releases dissolved gas; recovers heat.', 'Flash tank, exchanger.', 'Steel.'), 'gd_pump': _c('Pumps lean glycol.', 'Glycol pump.', '—'), 'gd_piping': _c('Glycol and gas lines.', 'Pipes.', 'Steel.')}},
    'sand_trap': {'summary': ('A sand trap removes sand and solids from well fluids or other process streams. A tangential inlet creates a swirl that throws sand to the wall; it slides into the conical bottom while the cleaned fluid '
                              'leaves through a central vortex finder. Sand is dumped periodically through a dump valve.'),
                  'classification': {'family': 'Solids separator', 'type': 'Vertical cyclonic sand trap (desander vessel)'}, 'model_configuration': {'animation': 'Sand spirals down; cone fills; dump'},
                  'standards': _OG + _PV, 'references': ['Maker desander data'],
                  'components': {'st_vessel': _c('Pressure envelope.', 'Vertical vessel with cone.', 'Carbon steel.', 'Erosion allowance.', ['Erosion at inlet'], ['UT thickness']),
                                 'st_internals': _c('Outlet tube; wear protection.', 'Vortex finder, wear plate.', 'Hardened steel.'), 'st_sand': _c('Collected sand.', '—', '—'),
                                 'st_valves': _c('Connections; dump; instruments.', 'Nozzles, dump valve, ΔP/level.', 'Steel / hard-faced valve.', '—', ['Valve erosion'], ['Inspect'])}},
}
BUILDERS = {k: globals()[k] for k in META}
