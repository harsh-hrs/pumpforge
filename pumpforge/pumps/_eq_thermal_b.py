"""Thermal & Process — evaporators, dryers and combustion equipment (EQ-235 … EQ-246)."""
import math
from mathutils import Matrix, Vector
from pumpforge.core import Model, lathe, cyl, box, csg, join, rotate, TAU, OPERATE_FRAMES
from pumpforge.valvekit import P, keys_loop, smooth_pulse
from pumpforge.parts import hollow_pipe, pressure_gauge, add_tracers
from pumpforge.vesselkit import vessel, nozzle, legs, skirt, droplets, liquid_v, half, mesh_pad, animate_level
from pumpforge.rotkit import axis_rot_keys
from pumpforge.handlingkit import rocks_along, rock
from pumpforge.shapes import sweep_tube
from pumpforge.common_meta import C
from pumps._eq_thermal_a import _hduct, _vduct, _hliq, _bands_z, _bands_x, _flame, _pump, _fan_rotor

CAT = '10 · Thermal & Process Equipment'


def _model(pid, title):
    return Model(pid, title, CAT, META[pid])


def _bed_particles(m, pid, name, x0, x1, y0, y1, z0, z1, n, mat='sand', drift=0.0, r=0.018, ref='flow_tracers'):
    """Fluidised particles: each bobs up and down (bubbling) and optionally drifts along x (continuous flow)."""
    p = m.part(pid, name, 'flow_tracers', explode=(0, 0, 0), info={'ref': ref})
    for i in range(n):
        fx, fy, ph = ((i * 0.618) % 1), ((i * 0.377) % 1), (i * 0.29) % 1
        ms = p.add(lathe(f'{pid}{i}', [(r * math.sin(k * math.pi / 6), -r * math.cos(k * math.pi / 6)) for k in range(7)], mat, 10), smooth_angle=80)
        keys = []
        for f in range(OPERATE_FRAMES + 1):
            t = f / OPERATE_FRAMES
            x = x0 + ((fx + drift * t) % 1.0) * (x1 - x0)
            z = z0 + (z1 - z0) * (0.5 + 0.5 * math.sin(TAU * (3 * t + ph)))
            keys.append((1 + f, (x, y0 + fy * (y1 - y0), z)))
        ms.location = keys[0][1]
        m.keyframes(ms, 'Operate', 'location', keys)
    return p


def _cyclone(name, x, y, z_top, R=0.25, mat='paint_grey'):
    """Cyclone body (cylinder + cone) with vortex finder, axis Z at (x, y); top at z_top."""
    body = vessel(name, R, 0.5, 0.006, mat, center=(x, y, 0), heads=('cone', 'flat'), z0=z_top - 0.5)
    vf = cyl(name + 'vf', R * 0.45, z_top - 0.3, z_top + 0.25, mat, 32, center=(x, y, 0), r_in=R * 0.42)
    inl = box(name + 'in', (0.3, 0.12, 0.18), (x - R - 0.1, y, z_top - 0.12), mat)
    return [body, vf, inl]


def _rotary_valve(name, x, y, z, mat='cast_iron'):
    return join(name, [box(name + 'b', (0.18, 0.18, 0.16), (x, y, z), mat), cyl(name + 'm', 0.05, y + 0.09, y + 0.25, 'paint_motor', 16, axis='Y', center=(x, 0, z))])


def _calandria(m, pid, name, x, z0, L, R, ntube=12, ref='ev_calandria', mat='stainless', label_tubes='Heating Tubes'):
    """Vertical shell (steam chest) with tubesheets and a ring of vertical tubes; returns tube x/y list."""
    sh = csg(pid + 's', [cyl(pid + 'so', R + 0.012, z0, z0 + L, mat, 64, center=(x, 0, 0))], [cyl(pid + 'si', R, z0 - 0.1, z0 + L + 0.1, mat, 64, center=(x, 0, 0))], mat)
    ts = [cyl(pid + f'ts{k}', R + 0.03, z, z + 0.03, 'steel', 64, center=(x, 0, 0)) for k, z in enumerate((z0 - 0.03, z0 + L))]
    P(m, pid, name, 'casing', [sh] + ts, explode=(0, 0.6, 0), ref=ref)
    pos = [(x + rr * math.cos(TAU * k / n + 0.2 * j), rr * math.sin(TAU * k / n + 0.2 * j)) for j, (rr, n) in enumerate(((R * 0.35, 4), (R * 0.72, 8))) for k in range(n)][:ntube]
    tubes = [cyl(f'{pid}t{i}', 0.022, z0 - 0.03, z0 + L + 0.03, 'steel', 12, center=(px, py, 0), r_in=0.018) for i, (px, py) in enumerate(pos)]
    P(m, pid + '_tubes', label_tubes, 'tubes', tubes, explode=(0, -0.6, 0), ref=ref, section='keep')
    return pos


# =============================================================== EQ-235 Flash evaporator
def flash_evaporator(out):
    m = _model('flash_evaporator', 'Flash Evaporator (Heater → Pressure Reduction → Flash Vessel)')
    R, Z0, L = 0.45, 0.8, 1.4
    fv = vessel('fv', R, L, 0.01, 'stainless', heads=('2:1', '2:1'), z0=Z0)
    P(m, 'flash_vessel', 'Flash Vessel (lower pressure)', 'vessel', fv, explode=(0, 0.6, 0), ref='fe_vessel')
    P(m, 'demister', 'Mesh-Pad Demister (stops droplet carry-over)', 'internals', half(mesh_pad('dm', R - 0.012, Z0 + L - 0.25, Z0 + L - 0.12), 'steel'), explode=(0, -0.3, 0.4), ref='fe_demister', section='keep')
    pl = P(m, 'concentrate', 'Liquid Collecting in the Vessel (concentrate / brine)', 'fluid', liquid_v('lq', R - 0.012, Z0, Z0 + 0.35, mat='brine'), explode=(0, -0.3, -0.2), ref='fe_liquid', section='keep')
    animate_level(m, pl, Z0 + 0.34, 0.04, lambda t: 0.5 + 0.5 * math.sin(TAU * t))
    nz = [nozzle('vo', (0, 0, Z0 + L + R * 0.5), (0, 0, 1), 0.1, 0.25), nozzle('li', (-R, 0, Z0 + 0.6), (-1, 0, 0), 0.05, 0.25), nozzle('lo', (0, 0, Z0 - R * 0.5), (0, 0, -1), 0.05, 0.25),
          box('lgc', (0.06, 0.05, 0.6), (R + 0.06, 0, Z0 + 0.35), 'paint_grey')]
    P(m, 'nozzles', 'Nozzles: Hot Feed Inlet (tangential), Vapour Outlet, Concentrate Outlet, Level Gauge', 'nozzles', nz, explode=(0, 0, 0.4), ref='fe_vessel', section='keep')
    hx = join('hx', [vessel('hxv', 0.18, 1.0, 0.008, 'paint_blue', axis='X', center=(0, 0, 0.55), heads=('2:1', '2:1'), z0=-2.4), nozzle('hxs', (-1.9, 0, 0.73), (0, 0, 1), 0.04, 0.15)])
    P(m, 'feed_heater', 'Feed Heater (raises liquid temperature under pressure)', 'exchanger', hx, explode=(-0.4, 0, 0), ref='fe_heater', section='keep')
    pp = [hollow_pipe('fp', [(-1.3, 0, 0.55), (-0.9, 0, 0.55), (-0.9, 0, Z0 + 0.6), (-R - 0.25, 0, Z0 + 0.6)], 0.04, 'stainless', 24, bend=0.08)]
    vl = join('vl', [box('vb', (0.14, 0.12, 0.14), (-0.9, 0, 1.05), 'paint_blue_dark'), cyl('vs', 0.012, 1.12, 1.35, 'steel', 12, center=(-0.9, 0, 0)), cyl('va', 0.09, 1.35, 1.45, 'paint_grey', 32, center=(-0.9, 0, 0))])
    P(m, 'feed_line', 'Feed Line', 'piping', pp, explode=(0, 0.3, 0), ref='fe_valve', section='keep')
    pv = P(m, 'flash_valve', 'Pressure-Reducing (Flash) Valve — pressure drops, liquid partly flashes to vapour', 'valves', vl, explode=(0, -0.3, 0.3), ref='fe_valve', section='keep')
    P(m, 'supports', 'Legs', 'structure', legs('lg', R, 0.0, Z0, n=4), explode=(0, 0, -0.3), ref='fe_vessel', section='keep')
    droplets(m, 'flash_vapour', 'Vapour Flashing off the Liquid', -0.3, 0.3, Z0 + 0.4, Z0 + L - 0.3, n=12, mat='steam', y=0.15, r=0.02)
    m.flow('feed', [(-2.6, 0, 0.55), (-1.3, 0, 0.55), (-0.9, 0, 0.55), (-0.9, 0, Z0 + 0.6), (-0.2, 0.1, Z0 + 0.6)], 'flow_discharge', 0.02, 0.3)
    m.flow('vapour', [(0, 0.1, Z0 + 0.6), (0, 0.1, Z0 + L + R + 0.3)], 'steam', 0.03, 0.3)
    m.flow('concentrate', [(0, 0.1, Z0 + 0.1), (0, 0, Z0 - R - 0.3)], 'flow_discharge', 0.02, 0.2)
    _bands_z(m, [(Z0 - R * 0.5, Z0 + L + R * 0.5, 2)], R, 'Pressure drop causes flashing', 'The feed is heated under pressure so it does not boil. Passing the pressure-reducing valve into the lower-pressure '
             'vessel, it is suddenly above its boiling point at the new pressure: part of it flashes to vapour, and the latent heat taken by that vapour cools the remaining liquid to the '
             'saturation temperature of the vessel. Flash fraction ≈ cp·(T_in − T_sat) / h_fg.', kind='pressure')
    return m.export(out)


# =============================================================== EQ-236 Falling film evaporator
def falling_film_evaporator(out):
    m = _model('falling_film_evaporator', 'Falling Film Evaporator (Calandria + Vapour–Liquid Separator)')
    R, Z0, L = 0.35, 0.9, 2.0
    pos = _calandria(m, 'calandria', 'Calandria Shell (steam chest) & Tubesheets', 0.0, Z0, L, R, ntube=12, ref='ff_calandria', label_tubes='Long Vertical Tubes (liquid film inside, steam outside)')
    th = vessel('th', R, 0.15, 0.01, 'stainless', heads=('flat', '2:1'), z0=Z0 + L + 0.03)
    bh = vessel('bh', R, 0.15, 0.01, 'stainless', heads=('cone', 'flat'), z0=Z0 - 0.18)
    P(m, 'heads', 'Top Head (feed chamber) & Bottom Head', 'casing', [th, bh], explode=(0, 0.5, 0.3), ref='ff_calandria')
    ds = csg('ds', [cyl('dsp', R - 0.012, Z0 + L + 0.1, Z0 + L + 0.115, 'stainless', 64)], [cyl(f'dh{i}', 0.012, Z0 + L, Z0 + L + 0.2, 'stainless', 8, center=(px, py, 0)) for i, (px, py) in enumerate(pos)], 'stainless')
    P(m, 'distributor', 'Liquid Distributor Plate (wets every tube evenly)', 'internals', ds, explode=(0, -0.3, 0.5), ref='ff_distributor', section='keep')
    sp = vessel('sp', 0.3, 1.2, 0.008, 'stainless', heads=('2:1', '2:1'), z0=0.6, center=(1.0, 0, 0))
    P(m, 'separator', 'Vapour–Liquid Separator', 'vessel', sp, explode=(0.5, 0.4, 0), ref='ff_separator')
    psl = P(m, 'separator_liquid', 'Concentrate in the Separator', 'fluid', liquid_v('sl', 0.29, 0.6, 0.85, mat='brine', cx=1.0), explode=(0.5, -0.3, 0), ref='ff_separator', section='keep')
    animate_level(m, psl, 0.84, 0.03, lambda t: 0.5 + 0.5 * math.sin(TAU * t))
    pi = [hollow_pipe('lk', [(0, 0, Z0 - 0.25), (0, 0, 0.45), (1.0, 0, 0.45), (1.0, 0, 0.6 - 0.3 * 0.5)], 0.06, 'stainless', 24, bend=0.1),
          hollow_pipe('rc', [(1.0, 0, 0.45), (1.0, 0, 0.3), (1.6, 0, 0.3), (1.6, 0, Z0 + L + 0.5), (0.0, 0, Z0 + L + 0.5), (0.0, 0, Z0 + L + 0.33)], 0.035, 'stainless', 24, bend=0.1),
          nozzle('sv', (0, -R, Z0 + L - 0.2), (0, -1, 0), 0.07, 0.25), nozzle('cd', (0, -R, Z0 + 0.15), (0, -1, 0), 0.03, 0.2), nozzle('vo', (1.0, 0, 1.8 + 0.15), (0, 0, 1), 0.09, 0.2)]
    P(m, 'piping', 'Bottom Link to Separator, Recirculation Line, Steam In, Condensate Out, Vapour Out', 'piping', pi, explode=(0, 0, 0.3), ref='ff_piping', section='keep')
    _pump(m, 'recirc_pump', 'Recirculation Pump', 1.35, 0.0, 0.3, 'ff_pump', explode=(0.3, -0.4, 0))
    P(m, 'structure', 'Support Steel', 'structure', [box(f'sl{k}', (0.08, 0.08, Z0 + 0.4), (sx * 0.45, sy * 0.45, (Z0 + 0.4) / 2), 'paint_grey') for k, (sx, sy) in enumerate(((-1, -1), (-1, 1), (1, -1), (1, 1)))],
      explode=(0, 0, -0.3), ref='ff_calandria', section='keep')
    pf = m.part('films', 'Liquid Film Falling down Inside the Tubes', 'flow_tracers', explode=(0, 0, 0), info={'ref': 'flow_tracers'})
    for i, (px, py) in enumerate(pos):
        if py < -0.01:
            continue
        for k in range(3):
            ms = pf.add(cyl(f'fd{i}{k}', 0.012, -0.02, 0.02, 'brine', 8), smooth_angle=60)
            keys = [(1 + f, (px, py, Z0 + L - (L + 0.1) * (((f / OPERATE_FRAMES) * 2 + k / 3 + i * 0.07) % 1.0))) for f in range(OPERATE_FRAMES + 1)]
            ms.location = keys[0][1]
            m.keyframes(ms, 'Operate', 'location', keys)
    m.flow('feed', [(1.6, 0, Z0 + L + 0.6), (0.0, 0, Z0 + L + 0.6), (0.0, 0, Z0 + L + 0.2)], 'flow_discharge', 0.02, 0.3)
    m.flow('film_and_vapour', [(0.0, 0.05, Z0 + L), (0.0, 0.05, Z0 - 0.2), (0.5, 0.05, 0.45), (1.0, 0.05, 0.6)], 'water', 0.02, 0.3)
    m.flow('vapour', [(1.0, 0.05, 1.0), (1.0, 0, 2.2)], 'steam', 0.03, 0.3)
    m.flow('heating_steam', [(0, -R - 0.3, Z0 + L - 0.2), (0, -0.2, Z0 + L - 0.25), (0, -0.2, Z0 + 0.2), (0, -R - 0.25, Z0 + 0.15)], 'steam', 0.02, 0.3)
    _bands_z(m, [(Z0, Z0 + L, 6)], R, 'Small temperature difference, short residence time',
             'Steam condenses outside the tubes while a thin film of liquid flows down the inside walls by gravity and evaporates from its surface. Because the film is thin and there is no '
             'hydrostatic head, it works with small temperature differences and very short residence time — ideal for heat-sensitive products such as milk, juices and pharmaceuticals.')
    return m.export(out)


# =============================================================== EQ-237 Forced circulation evaporator
def forced_circulation_evaporator(out):
    m = _model('forced_circulation_evaporator', 'Forced Circulation Evaporator (Heater + Flash Separator + Circulation Pump)')
    R, Z0, L = 0.28, 0.7, 1.4
    pos = _calandria(m, 'heater', 'Heat Exchanger Shell (steam side)', 0.0, Z0, L, R, ntube=12, ref='fc_heater', label_tubes='Heater Tubes (liquid pumped through at high velocity — no boiling in the tubes)')
    hh = [vessel('hb', R, 0.12, 0.008, 'stainless', heads=('cone', 'flat'), z0=Z0 - 0.15), vessel('ht', R, 0.12, 0.008, 'stainless', heads=('flat', 'cone'), z0=Z0 + L + 0.03)]
    P(m, 'heads', 'Inlet & Outlet Heads', 'casing', hh, explode=(0, 0.4, 0.2), ref='fc_heater')
    SX, SZ, SR = 1.2, 1.9, 0.5
    sp = vessel('sp', SR, 0.9, 0.01, 'stainless', heads=('cone', '2:1'), z0=SZ, center=(SX, 0, 0))
    P(m, 'separator', 'Flash Separator (liquid boils here as pressure falls)', 'vessel', sp, explode=(0.4, 0.5, 0.3), ref='fc_separator')
    psl = P(m, 'separator_liquid', 'Circulating Liquid in the Separator', 'fluid', liquid_v('sl', SR - 0.012, SZ, SZ + 0.35, head='cone', mat='brine', cx=SX), explode=(0.4, -0.3, 0), ref='fc_separator', section='keep')
    animate_level(m, psl, SZ + 0.34, 0.03, lambda t: 0.5 + 0.5 * math.sin(TAU * t))
    loop = [(0.0, 0, Z0 + L + 0.2), (0.0, 0, Z0 + L + 0.45), (SX - SR - 0.2, 0, Z0 + L + 0.45), (SX - SR, 0, SZ + 0.25)]
    down = [(SX, 0, SZ - SR * 0.9), (SX, 0, 0.35), (0.45, 0, 0.35)]
    pi = [hollow_pipe('up', loop, 0.07, 'stainless', 24, bend=0.12), hollow_pipe('dn', down, 0.08, 'stainless', 24, bend=0.12),
          hollow_pipe('pin', [(0.0, 0, 0.35), (0.0, 0, Z0 - 0.3)], 0.08, 'stainless', 24),
          nozzle('vo', (SX, 0, SZ + 0.9 + SR * 0.5), (0, 0, 1), 0.12, 0.25), nozzle('si', (0, -R, Z0 + L - 0.2), (0, -1, 0), 0.06, 0.25), nozzle('co', (SX + 0.15, 0, 0.35), (1, 0, 0), 0.03, 0.2)]
    P(m, 'circulation_loop', 'Circulation Loop: Heater Outlet → Separator → Downcomer → Pump', 'piping', pi, explode=(0, 0.3, 0.3), ref='fc_loop', section='keep')
    pump = join('cp', [cyl('cpv', 0.2, -0.08, 0.08, 'paint_blue', 48, axis='Y', center=(0.3, 0, 0.35)), cyl('cpm', 0.15, 0.4, 1.0, 'paint_motor', 32, axis='Y', center=(0.3, 0, 0.35), ch=0.01)])
    P(m, 'circulation_pump', 'Axial/Mixed-Flow Circulation Pump & Motor (high flow, low head)', 'pumps', pump, explode=(0, 0.5, -0.2), ref='fc_pump', section='keep')
    imp = join('cpi', [rotate(box(f'ib{k}', (0.16, 0.012, 0.05), (0.38, 0, 0.35), 'stainless'), TAU * k / 4, 'Y', (0.3, 0, 0.35)) for k in range(4)])
    pi_ = P(m, 'pump_impeller', 'Pump Impeller', 'pumps', imp, explode=(0, -0.4, -0.2), ref='fc_pump', section='keep', pivot=(0.3, 0, 0.35))
    pi_.spin('Y', 5)
    P(m, 'structure', 'Support Steel', 'structure', [box(f'sl{k}', (0.08, 0.08, SZ), (SX + sx * 0.4, sy * 0.4, SZ / 2), 'paint_grey') for k, (sx, sy) in enumerate(((-1, -1), (-1, 1), (1, -1), (1, 1)))],
      explode=(0, 0, -0.3), ref='fc_separator', section='keep')
    add_tracers(m, 'circulating', 'Liquid Circulating round the Loop', [(0.3, 0.05, 0.35), (0.0, 0.05, 0.35), (0.0, 0.05, Z0 + L + 0.45), (SX - SR - 0.2, 0.05, Z0 + L + 0.45), (SX, 0.05, SZ + 0.2), (SX, 0.05, 0.35), (0.3, 0.05, 0.35)], n=14, radius=0.025, mat='brine', loops=2)
    droplets(m, 'flash_vapour', 'Vapour Flashing in the Separator', SX - 0.3, SX + 0.3, SZ + 0.4, SZ + 1.1, n=10, mat='steam', y=0.15, r=0.02)
    m.flow('circulation', [(0.3, 0, 0.35), (0.0, 0, 0.35)] + loop + [(SX, 0, SZ + 0.2)] + down, 'flow_discharge', 0.02, 0.4)
    m.flow('vapour', [(SX, 0.1, SZ + 0.5), (SX, 0, SZ + 1.6)], 'steam', 0.03, 0.3)
    m.flow('heating_steam', [(0, -R - 0.3, Z0 + L - 0.2), (0, -0.15, Z0 + L - 0.25), (0, -0.15, Z0 + 0.1)], 'steam', 0.02, 0.3)
    _bands_z(m, [(Z0, Z0 + L, 7)], R, 'Hydrostatic head suppresses boiling in the tubes',
             'The circulation pump drives liquid through the tubes at high velocity (typically ~ 1.5–3 m/s). The static head above the tubes keeps the liquid under enough pressure that it is '
             'only heated (a few °C) without boiling; it flashes when it reaches the separator. Suppressing boiling at the wall prevents scaling and crystal deposition — ideal for '
             'crystallising, scaling or viscous liquids.')
    return m.export(out)


# =============================================================== EQ-238 Multiple effect evaporator
def multiple_effect_evaporator(out):
    m = _model('multiple_effect_evaporator', 'Triple-Effect Evaporator (Forward Feed, Short-Tube Calandrias)')
    R, Z0, L = 0.38, 0.8, 0.8
    xs = (-1.6, 0.0, 1.6)
    for k, x in enumerate(xs):
        n = k + 1
        _calandria(m, f'effect_{n}', f'Effect {n}: Calandria (steam chest)', x, Z0, L, R, ntube=12, ref='me_effect', label_tubes=f'Effect {n}: Tubes')
        bd = vessel(f'bd{n}', R, 0.9, 0.01, 'stainless', heads=('flat', '2:1'), z0=Z0 + L + 0.03, center=(x, 0, 0))
        bb = vessel(f'bb{n}', R, 0.12, 0.01, 'stainless', heads=('cone', 'flat'), z0=Z0 - 0.15, center=(x, 0, 0))
        P(m, f'body_{n}', f'Effect {n}: Vapour Body & Bottom Cone', 'vessel', [bd, bb], explode=(0, 0.5, 0.4), ref='me_body')
        pl = P(m, f'liquor_{n}', f'Effect {n}: Boiling Liquor', 'fluid', half(cyl(f'lq{n}', R - 0.012, Z0 - 0.02, Z0 + L + 0.15, 'brine', 48, center=(x, 0, 0)), 'brine'), explode=(0, -0.3, 0), ref='me_liquor', section='keep')
        animate_level(m, pl, Z0 + L + 0.14, 0.02, lambda t, k=k: 0.5 + 0.5 * math.sin(TAU * t + k))
        droplets(m, f'vapour_{n}', f'Effect {n}: Vapour Bubbles', x - 0.25, x + 0.25, Z0 + L + 0.15, Z0 + L + 0.9, n=6, mat='steam', y=0.15, r=0.018)
    vl = []
    for k in range(2):
        a, b = xs[k], xs[k + 1]
        vl.append(hollow_pipe(f'vl{k}', [(a, 0, Z0 + L + 0.9 + R * 0.5), (a, 0, Z0 + L + 1.25), (a + 0.7, 0, Z0 + L + 1.25), (a + 0.7, 0, Z0 + L - 0.15), (b - R, 0, Z0 + L - 0.15)], 0.07, 'stainless', 24, bend=0.12))
    vl.append(hollow_pipe('vl2', [(xs[2], 0, Z0 + L + 0.9 + R * 0.5), (xs[2], 0, Z0 + L + 1.25), (2.5, 0, Z0 + L + 1.25), (2.5, 0, 1.5)], 0.07, 'stainless', 24, bend=0.12))
    vl.append(nozzle('ls', (xs[0] - R, 0, Z0 + L - 0.15), (-1, 0, 0), 0.07, 0.3))
    P(m, 'vapour_lines', 'Vapour Lines: vapour of each effect heats the next', 'piping', vl, explode=(0, 0, 0.5), ref='me_vapour')
    ll = [hollow_pipe(f'll{k}', [(xs[k], 0, Z0 - 0.15 - R * 0.6), (xs[k], 0, 0.3), (xs[k + 1] - 0.4, 0, 0.3), (xs[k + 1] - 0.4, 0, Z0 + 0.1), (xs[k + 1] - R, 0, Z0 + 0.1)], 0.03, 'stainless', 16, bend=0.06) for k in range(2)]
    ll.append(nozzle('cn', (xs[2], 0, Z0 - 0.15 - R * 0.6), (0, 0, -1), 0.03, 0.3))
    P(m, 'liquor_lines', 'Liquor Transfer Lines (forward feed: pressure difference moves liquor to the next effect)', 'piping', ll, explode=(0, 0, -0.3), ref='me_liquor', section='keep')
    cd = join('cd', [vessel('cdv', 0.25, 0.8, 0.008, 'paint_blue', center=(2.5, 0, 0), heads=('2:1', '2:1'), z0=0.6), nozzle('cdv2', (2.75, 0, 1.2), (1, 0, 0), 0.04, 0.2)])
    P(m, 'condenser', 'Final Condenser & Vacuum Connection (lowest pressure)', 'condenser', cd, explode=(0.5, 0, 0), ref='me_condenser', section='keep')
    P(m, 'structure', 'Support Legs', 'structure', [legs(f'lg{k}', R, 0.0, Z0 - 0.15, n=4, cx=x) for k, x in enumerate(xs)], explode=(0, 0, -0.3), ref='me_body', section='keep')
    m.flow('live_steam', [(xs[0] - R - 0.5, 0, Z0 + L - 0.15), (xs[0] - 0.2, -0.15, Z0 + L - 0.2), (xs[0] - 0.2, -0.15, Z0 + 0.1)], 'steam', 0.025, 0.3)
    for k in range(2):
        a, b = xs[k], xs[k + 1]
        m.flow(f'vapour_{k + 1}_to_{k + 2}', [(a, 0, Z0 + L + 0.8), (a, 0, Z0 + L + 1.25), (a + 0.7, 0, Z0 + L + 1.25), (a + 0.7, 0, Z0 + L - 0.15), (b - 0.2, -0.15, Z0 + L - 0.2)], 'steam', 0.02, 0.4)
    m.flow('last_vapour', [(xs[2], 0, Z0 + L + 0.8), (xs[2], 0, Z0 + L + 1.25), (2.5, 0, Z0 + L + 1.25), (2.5, 0, 1.4)], 'steam', 0.02, 0.4)
    m.flow('liquor', [(xs[0] - 0.9, 0, Z0 + 0.1), (xs[0] - R, 0, Z0 + 0.1)] + [p_ for k in range(2) for p_ in ((xs[k], 0, Z0 - 0.4), (xs[k], 0, 0.3), (xs[k + 1] - 0.4, 0, 0.3), (xs[k + 1] - R, 0, Z0 + 0.1))] + [(xs[2], 0, Z0 - 0.5)], 'flow_discharge', 0.015, 0.4)
    objs = [cyl(f'pz{k}', R + 0.06, Z0 - 0.15, Z0 + L + 0.95, f'pressure_{lev}', 48, center=(x, 0, 0), r_in=R + 0.035) for k, (x, lev) in enumerate(zip(xs, (7, 4, 1)))]
    m.overlay('pressure', join('pz', objs), 'Pressure and boiling point fall from effect to effect',
              'Effect 1 operates at the highest pressure and temperature, heated by live steam. Its vapour is hot enough to boil the liquor in effect 2, which runs at a lower pressure '
              '(lower boiling point), and so on to the last effect under vacuum. Each kilogram of steam evaporates roughly N × 0.8–1 kg of water in N effects (steam economy), '
              'at the cost of more heating surface.', split=True)
    return m.export(out)


# =============================================================== EQ-239 Spray dryer
def spray_dryer(out):
    m = _model('spray_dryer', 'Spray Dryer (Rotary Atomiser, Co-Current, Cyclone Collection)')
    R, Z0, L = 0.9, 1.4, 1.4
    ch = vessel('ch', R, L, 0.01, 'stainless', heads=('cone', 'flat'), z0=Z0)
    P(m, 'drying_chamber', 'Drying Chamber & Cone', 'vessel', ch, explode=(0, 0.8, 0), ref='sd_chamber')
    rf = join('rf', [csg('ad', [cyl('ado', 0.5, Z0 + L, Z0 + L + 0.3, 'stainless', 64)], [cyl('adi', 0.46, Z0 + L - 0.05, Z0 + L + 0.27, 'stainless', 64)], 'stainless'),
                     box('ain', (0.9, 0.35, 0.25), (-0.7, 0, Z0 + L + 0.15), 'stainless')] + [rotate(box(f'gv{k}', (0.14, 0.01, 0.2), (0.35, 0, Z0 + L + 0.12), 'steel'), TAU * k / 10, 'Z') for k in range(10)])
    P(m, 'air_disperser', 'Hot-Air Disperser (roof) with Guide Vanes', 'air', rf, explode=(0, 0, 0.6), ref='sd_disperser', section='keep')
    at = join('at', [cyl('atb', 0.12, Z0 + L + 0.3, Z0 + L + 0.75, 'paint_motor', 32, ch=0.01), cyl('ats', 0.03, Z0 + L - 0.25, Z0 + L + 0.3, 'steel', 16)])
    P(m, 'atomiser_drive', 'Rotary Atomiser Drive (high-speed motor / gearbox)', 'atomiser', at, explode=(0, 0, 0.9), ref='sd_atomiser', section='keep')
    wh = join('wh', [cyl('whd', 0.12, Z0 + L - 0.3, Z0 + L - 0.24, 'stainless', 32)] + [box(f'wv{k}', (0.1, 0.012, 0.05), (0.07, 0, Z0 + L - 0.27), 'stainless') for k in range(1)] +
              [rotate(box(f'wv{k}', (0.1, 0.012, 0.05), (0.07, 0, Z0 + L - 0.27), 'stainless'), TAU * k / 8, 'Z') for k in range(1, 8)])
    pw = P(m, 'atomiser_wheel', 'Atomiser Wheel (flings feed into a fine spray)', 'atomiser', wh, explode=(0, -0.5, 0.7), ref='sd_atomiser', section='keep', pivot=(0, 0, Z0 + L - 0.27))
    pw.spin('Z', 12)
    cy = _cyclone('cy', 1.8, 0.0, 1.9, R=0.28)
    duct = hollow_pipe('ex', [(R * 0.3, 0, Z0 + 0.3), (1.2, 0, Z0 + 0.3), (1.2, 0, 1.78), (1.45, 0, 1.78)], 0.08, 'stainless', 24, bend=0.12)
    P(m, 'cyclone', 'Cyclone (separates fines from the exhaust air) & Duct', 'separator', cy + [duct], explode=(0.6, 0, 0), ref='sd_cyclone', section='keep')
    rv = [_rotary_valve('rv1', 0, 0, Z0 - R - 0.05), _rotary_valve('rv2', 1.8, 0, 1.06)]
    P(m, 'rotary_valves', 'Rotary Valves (powder discharge, chamber & cyclone)', 'valves', rv, explode=(0, -0.3, -0.3), ref='sd_valves', section='keep')
    P(m, 'structure', 'Support Structure', 'structure', legs('lg', R, 0.0, Z0, n=4), explode=(0, 0, -0.3), ref='sd_chamber', section='keep')
    pdr = m.part('spray', 'Spray Droplets drying into Powder', 'flow_tracers', explode=(0, 0, 0), info={'ref': 'flow_tracers'})
    for i in range(18):
        a0, ph = TAU * i / 18, (i * 0.37) % 1
        ms = pdr.add(lathe(f'sp{i}', [(0.018 * math.sin(k * math.pi / 6), -0.018 * math.cos(k * math.pi / 6)) for k in range(7)], 'water' if i % 2 else 'powder', 10), smooth_angle=80)
        keys = []
        for f in range(OPERATE_FRAMES + 1):
            s = ((f / OPERATE_FRAMES) + ph) % 1.0
            rr = min(R * 0.85, 0.15 + 2.5 * s) * (1 - 0.8 * max(0.0, s - 0.5))
            z = Z0 + L - 0.27 - (L + R * 0.6) * s ** 1.4
            a = a0 + 2.5 * s
            keys.append((1 + f, (rr * math.cos(a), abs(rr * math.sin(a)) + 0.02, z)))
        ms.location = keys[0][1]
        m.keyframes(ms, 'Operate', 'location', keys)
    m.flow('hot_air', [(-1.2, 0, Z0 + L + 0.15), (-0.4, 0, Z0 + L + 0.15), (0, 0.1, Z0 + L - 0.1), (0, 0.1, Z0 + 0.5), (R * 0.3, 0, Z0 + 0.3), (1.2, 0, Z0 + 0.3), (1.2, 0, 1.78), (1.55, 0, 1.78), (1.8, 0.1, 1.5), (1.8, 0, 2.3)], 'air', 0.03, 0.4)
    m.flow('feed', [(0.3, 0, Z0 + L + 0.6), (0.06, 0, Z0 + L + 0.2), (0.06, 0, Z0 + L - 0.25)], 'flow_discharge', 0.015, 0.2)
    m.flow('powder', [(0, 0.05, Z0 - R * 0.5), (0, 0, Z0 - R - 0.3)], 'sand', 0.02, 0.2)
    _bands_z(m, [(Z0 + L - 0.4, Z0 + L, 8), (Z0 + 0.4, Z0 + L - 0.4, 6), (Z0 - 0.2, Z0 + 0.4, 4)], R, 'Air cools as it evaporates the droplets',
             'Hot inlet air (often ~ 150–250 °C, higher for robust products) meets the spray at the top. Evaporation is very fast because the droplets are tiny (large surface area); '
             'the evaporating droplets stay near the wet-bulb temperature, so even heat-sensitive products (milk, enzymes) survive. Outlet air (~ 70–100 °C) sets the final moisture.')
    return m.export(out)


# =============================================================== EQ-240 Fluidized bed dryer
def fluidized_bed_dryer(out):
    m = _model('fluidized_bed_dryer', 'Continuous Fluidised Bed Dryer (Plenum, Distributor, Bed, Freeboard)')
    X0, X1, W, ZP, ZD = -1.2, 1.2, 0.8, 0.5, 0.75
    body = csg('bd', [box('bo', (X1 - X0 + 0.06, W + 0.06, 1.6), (0, 0, ZP + 0.75), 'stainless')], [box('bi', (X1 - X0, W, 1.55), (0, 0, ZP + 0.73), 'stainless')], 'stainless')
    P(m, 'body', 'Dryer Body: Plenum (below) & Freeboard (above the bed)', 'casing', body, explode=(0, 0.6, 0), ref='fb_body')
    dp = csg('dp', [box('dpp', (X1 - X0, W, 0.012), (0, 0, ZD), 'steel')], [cyl(f'dh{i}_{j}', 0.012, ZD - 0.02, ZD + 0.02, 'steel', 8, center=(X0 + 0.1 + 0.2 * i, -W / 2 + 0.1 + 0.2 * j, 0)) for i in range(12) for j in range(4)], 'steel')
    P(m, 'distributor', 'Perforated Distributor Plate (spreads air evenly)', 'internals', dp, explode=(0, -0.4, 0), ref='fb_distributor', section='keep')
    wr = [box('wr', (0.02, W, 0.2), (X1 - 0.12, 0, ZD + 0.1), 'steel'), box('fc', (0.25, 0.3, 0.4), (X0 + 0.2, 0, ZP + 1.75), 'stainless')]
    P(m, 'weir_feed', 'Discharge Weir (sets bed depth) & Feed Chute', 'internals', wr, explode=(0, -0.4, 0.3), ref='fb_weir', section='keep')
    _bed_particles(m, 'bed', 'Fluidised Particles (bubbling bed, moving towards the weir)', X0 + 0.1, X1 - 0.15, 0.02, W / 2 - 0.05, ZD + 0.04, ZD + 0.3, 40, mat='powder', drift=1.0)
    ai = [hollow_pipe('ai', [(-2.2, 0, ZP), (X0 - 0.05, 0, ZP)], 0.12, 'paint_grey', 32), box('ht', (0.4, 0.5, 0.5), (-1.9, 0, ZP), 'paint_red'),
          hollow_pipe('ex', [(0.6, 0, ZP + 1.55), (0.6, 0, ZP + 1.9), (1.7, 0, ZP + 1.9), (1.7, 0, 1.95)], 0.1, 'stainless', 24, bend=0.15)]
    P(m, 'air_system', 'Hot-Air Heater, Inlet Duct & Exhaust Duct', 'air', ai, explode=(0, 0.3, 0.3), ref='fb_air', section='keep')
    cy = _cyclone('cy', 2.1, 0.0, 2.0, R=0.25)
    P(m, 'cyclone', 'Cyclone (captures fines from exhaust air)', 'separator', cy, explode=(0.5, 0, 0), ref='fb_cyclone', section='keep')
    _fan_rotor(m, 'fan', 'Supply Air Fan Impeller', (-2.4, 0, ZP), 'X', 0.2, 'fb_air', revs=4)
    P(m, 'discharge', 'Product Discharge (rotary valve)', 'valves', _rotary_valve('rv', X1 + 0.15, 0, ZD - 0.1), explode=(0.3, -0.3, 0), ref='fb_weir', section='keep')
    P(m, 'legs', 'Support Legs', 'structure', [box(f'lg{k}', (0.06, 0.06, ZP - 0.25), (sx * (X1 - 0.1), sy * (W / 2), (ZP - 0.25) / 2), 'paint_grey') for k, (sx, sy) in enumerate(((-1, -1), (-1, 1), (1, -1), (1, 1)))],
      explode=(0, 0, -0.3), ref='fb_body', section='keep')
    m.flow('hot_air', [(-2.6, 0, ZP), (X0, 0, ZP), (0, -0.2, ZP + 0.05), (0, -0.2, ZD + 0.8), (0.6, 0, ZP + 1.5), (0.6, 0, ZP + 1.9), (1.7, 0, ZP + 1.9), (2.1, 0, 2.4)], 'air', 0.03, 0.4)
    m.flow('solids', [(X0 + 0.2, 0, ZP + 1.9), (X0 + 0.2, 0, ZD + 0.2), (X1 - 0.12, 0, ZD + 0.25), (X1 + 0.15, 0, ZD - 0.3)], 'sand', 0.02, 0.4)
    _bands_x(m, [(X0, 0, 7), (0, X1, 5)], W, 0.4, ZD + 0.2, 'Intense heat and mass transfer in the bed',
             'Air blown up through the distributor at just above the minimum fluidisation velocity makes the particles behave like a boiling liquid. Every particle is surrounded by hot air, '
             'so drying is fast and the bed temperature is uniform. Bed depth (weir height) and air temperature set residence time and final moisture.')
    return m.export(out)


# =============================================================== EQ-241 Flash dryer
def flash_dryer(out):
    m = _model('flash_dryer', 'Flash (Pneumatic) Dryer — Heater, Drying Riser, Cyclone, Exhaust Fan')
    ZB = 0.6
    ht = join('ht', [box('hb', (0.6, 0.6, 0.6), (-1.6, 0, ZB), 'paint_red'), cyl('bn', 0.12, -2.2, -1.9, 'paint_blue', 24, axis='X', center=(0, 0, ZB))])
    P(m, 'air_heater', 'Air Heater (direct gas burner)', 'heater', ht, explode=(-0.4, 0, 0), ref='fd_heater', section='keep')
    _flame(m, 'flame', 'Burner Flame', (-1.85, 0, ZB), (1, 0, 0), 0.4, 0.1, 'fd_heater')
    rs = [hollow_pipe('rs', [(-1.3, 0, ZB), (-0.6, 0, ZB), (-0.6, 0, 3.0), (0.3, 0, 3.0), (0.3, 0, 2.6)], 0.15, 'stainless', 32, bend=0.25)]
    rs.append(lathe('vt', [(0.15, ZB + 0.15), (0.17, ZB + 0.15), (0.11, ZB + 0.45), (0.17, ZB + 0.75), (0.15, ZB + 0.75), (0.09, ZB + 0.45)], 'stainless', 48, center=(-0.6, 0, 0)))
    P(m, 'drying_duct', 'Venturi & Vertical Drying Duct (riser) — particles dry in seconds', 'duct', rs, explode=(0, 0.5, 0), ref='fd_duct')
    fd = join('fd', [box('fh', (0.4, 0.4, 0.3), (-1.2, 0, ZB + 0.75), 'stainless'), cyl('fs', 0.06, -1.2, -0.65, 'steel', 16, axis='X', center=(0, 0, ZB + 0.5))])
    P(m, 'feeder', 'Wet-Feed Hopper & Screw Feeder / Disperser', 'feeder', fd, explode=(-0.3, -0.3, 0.3), ref='fd_feeder', section='keep')
    cy = _cyclone('cy', 0.6, 0.0, 2.45, R=0.32)
    P(m, 'cyclone', 'Product Cyclone', 'separator', cy, explode=(0.5, 0, 0), ref='fd_cyclone', section='keep')
    P(m, 'rotary_valve', 'Rotary Valve (product out, air lock)', 'valves', _rotary_valve('rv', 0.6, 0, 1.56), explode=(0, -0.3, -0.3), ref='fd_cyclone', section='keep')
    ex = [hollow_pipe('ex', [(0.6, 0, 2.7), (0.6, 0, 3.2), (1.6, 0, 3.2), (1.6, 0, 1.2)], 0.1, 'paint_grey', 24, bend=0.15), cyl('stk', 0.12, 1.2, 3.8, 'paint_grey', 32, center=(2.0, 0, 0), r_in=0.11)]
    ex.append(csg('fh', [cyl('fho', 0.3, -0.12, 0.12, 'paint_grey', 48, axis='Y', center=(1.75, 0, 0.95))], [cyl('fhi', 0.27, -0.1, 0.1, 'paint_grey', 48, axis='Y', center=(1.75, 0, 0.95))], 'paint_grey'))
    P(m, 'exhaust', 'Exhaust Duct, Fan Housing & Stack (to bag filter / stack)', 'air', ex, explode=(0.5, 0.3, 0), ref='fd_fan', section='keep')
    _fan_rotor(m, 'exhaust_fan', 'Exhaust Fan Impeller (draws the system under suction)', (1.75, 0, 0.95), 'Y', 0.24, 'fd_fan', revs=5)
    add_tracers(m, 'particles', 'Particles Conveyed and Dried in the Hot Gas', [(-0.75, 0.05, ZB + 0.5), (-0.6, 0.05, ZB + 0.5), (-0.6, 0.05, 3.0), (0.3, 0.05, 3.0), (0.3, 0.05, 2.6), (0.55, 0.05, 2.2), (0.6, 0.05, 1.3)], n=16, radius=0.022, mat='powder', loops=2)
    m.flow('hot_gas', [(-2.0, 0, ZB), (-0.6, 0, ZB), (-0.6, 0, 3.0), (0.3, 0, 3.0), (0.3, 0, 2.6), (0.6, 0, 2.3), (0.6, 0, 3.2), (1.6, 0, 3.2), (1.6, 0, 1.2), (2.0, 0, 1.2), (2.0, 0, 3.9)], 'air', 0.03, 0.5)
    m.flow('product', [(0.6, 0, 1.8), (0.6, 0, 1.2)], 'sand', 0.02, 0.2)
    _bands_z(m, [(ZB + 0.5, 1.6, 8), (1.6, 3.0, 5)], 0.15, 'Gas temperature falls quickly up the riser', 'Hot gas (~ 150–600 °C depending on product) picks up the wet particles at the venturi and carries them '
             'up the duct at high velocity (~ 10–30 m/s). Surface moisture flashes off within seconds, so the gas temperature falls rapidly; the short contact time makes flash dryers '
             'suitable for heat-sensitive, free-flowing materials with mainly surface moisture.', cx=-0.6)
    return m.export(out)


# =============================================================== EQ-242 Paddle dryer
def paddle_dryer(out):
    m = _model('paddle_dryer', 'Twin-Shaft Hollow Paddle Dryer (Indirect, Steam-Heated)')
    X0, X1, CZ, Rs = -1.3, 1.3, 0.75, 0.28
    ys = (-0.27, 0.27)
    tr = csg('tr', [box('tro', (X1 - X0, 1.2, 0.75), (0, 0, CZ + 0.05), 'paint_grey')],
             [cyl(f'tri{k}', Rs + 0.02, X0 - 0.1, X1 + 0.1, 'paint_grey', 64, axis='X', center=(0, y, CZ)) for k, y in enumerate(ys)] + [box('trt', (X1 - X0 + 0.2, 1.0, 0.5), (0, 0, CZ + 0.35), 'paint_grey')], 'paint_grey')
    P(m, 'jacketed_trough', 'Jacketed W-Trough (steam jacket)', 'casing', tr, explode=(0, 0.7, 0), ref='pd_trough')
    for k, y in enumerate(ys):
        sh = [cyl(f'sh{k}', 0.08, X0 - 0.4, X1 + 0.3, 'steel', 32, axis='X', center=(0, y, CZ), r_in=0.06)]
        for i in range(10):
            x = X0 + 0.15 + (X1 - X0 - 0.3) * i / 9
            for q in range(2):
                pd = lathe(f'pd{k}{i}{q}', [(0.0, -0.09), (0.12, 0.0), (0.0, 0.09)], 'steel', 3, center=(0, 0, 0))
                pd = rotate(pd, math.pi / 2, 'Y')
                pd.data.transform(Matrix.Translation((x, 0, Rs - 0.1)))
                pd = rotate(pd, math.pi * q + (math.pi / 2 if k else 0) + i * 0.5, 'X')
                pd.data.transform(Matrix.Translation((0, y, CZ)))
                sh.append(pd)
        ps = P(m, f'paddle_shaft_{k + 1}', f'Hollow Shaft {k + 1} with Wedge Paddles (steam inside)', 'rotating_element', sh, explode=(0, -0.7 if k == 0 else -1.2, 0.2), ref='pd_shafts', section='keep', pivot=(0, y, CZ))
        ps.spin('X', 1.0 if k == 0 else -1.0)
    vd = join('vd', [csg('vdc', [box('vdo', (X1 - X0, 1.1, 0.3), (0, 0, CZ + 0.55), 'paint_grey')], [box('vdi', (X1 - X0 - 0.04, 1.06, 0.3), (0, 0, CZ + 0.52), 'paint_grey')], 'paint_grey'),
                     nozzle('vo', (0.6, 0, CZ + 0.7), (0, 0, 1), 0.1, 0.25), box('fi', (0.3, 0.4, 0.25), (X0 + 0.25, 0, CZ + 0.82), 'stainless')])
    P(m, 'vapour_dome', 'Cover / Vapour Dome, Vapour Outlet & Feed Inlet', 'casing', vd, explode=(0, 0, 0.6), ref='pd_dome')
    rj = [join(f'rj{k}', [cyl(f'rjb{k}', 0.07, X0 - 0.55, X0 - 0.4, 'brass', 24, axis='X', center=(0, y, CZ)), cyl(f'rjp{k}', 0.025, X0 - 0.75, X0 - 0.55, 'steel', 12, axis='X', center=(0, y, CZ))]) for k, y in enumerate(ys)]
    P(m, 'rotary_joints', 'Rotary Joints (steam in, condensate out of the hollow shafts)', 'seals', rj, explode=(-0.4, 0, 0), ref='pd_joints', section='keep')
    dr = join('dr', [box('gb', (0.35, 0.9, 0.35), (X1 + 0.5, 0, CZ), 'paint_blue'), cyl('mt', 0.13, X1 + 0.68, X1 + 1.1, 'paint_motor', 32, axis='X', center=(0, 0, CZ))])
    P(m, 'drive', 'Drive: Motor, Gearbox & Timing Gears (shafts counter-rotate)', 'drive', dr, explode=(0.5, 0, 0), ref='pd_drive', section='keep')
    P(m, 'outlet', 'Discharge Weir & Outlet', 'casing', [box('ow', (0.03, 1.0, 0.3), (X1 - 0.12, 0, CZ - 0.05), 'steel'), nozzle('od', (X1 - 0.05, 0, CZ - Rs - 0.03), (0, 0, -1), 0.08, 0.2)],
      explode=(0.3, -0.3, -0.3), ref='pd_trough', section='keep')
    P(m, 'supports', 'Supports', 'structure', [box(f'sp{k}', (0.12, 1.1, CZ - 0.3), (x, 0, (CZ - 0.3) / 2), 'paint_grey') for k, x in enumerate((X0 + 0.2, X1 - 0.2))], explode=(0, 0, -0.3), ref='pd_trough', section='keep')
    rocks_along(m, 'sludge', 'Wet Material Conveyed & Mixed by the Paddles', [(X0 + 0.25, CZ + 0.6), (X0 + 0.25, CZ - 0.05), (X1 - 0.15, CZ - 0.05), (X1 - 0.05, CZ - Rs - 0.3)], 14, r=0.035, mat='coal', y=0.3, ref='flow_tracers')
    droplets(m, 'vapour', 'Moisture Evaporating to the Vapour Dome', X0 + 0.3, X1 - 0.3, CZ + 0.1, CZ + 0.65, n=10, mat='steam', y=0.35, r=0.018)
    m.flow('steam', [(X0 - 0.85, ys[1], CZ), (X1, ys[1], CZ)], 'steam', 0.02, 0.3)
    m.flow('vapour_out', [(0.6, 0.1, CZ + 0.5), (0.6, 0, CZ + 1.0)], 'steam', 0.03, 0.2)
    m.flow('material', [(X0 + 0.25, 0, CZ + 0.95), (X0 + 0.25, 0, CZ), (X1 - 0.15, 0, CZ), (X1 - 0.05, 0, CZ - Rs - 0.25)], 'sand', 0.02, 0.4)
    _bands_x(m, [(X0, X1, 7)], 1.2, 0.75, CZ + 0.05, 'Indirect heating through jacket and paddles',
             'Steam (or thermal oil) heats the trough jacket and the inside of the hollow shafts and paddles, so the heating surface per unit volume is very large. The material never touches '
             'the heating medium, and only a small vapour stream leaves — easy to condense or treat. Used for sludges, pastes and filter cakes.')
    return m.export(out)


# =============================================================== EQ-243 Vacuum dryer (rotary double cone)
def vacuum_dryer(out):
    m = _model('vacuum_dryer', 'Rotary Double-Cone Vacuum Dryer')
    CZ, R, Lc = 1.3, 0.6, 0.35
    prof = [(0.12, -Lc - 0.55), (R, -Lc), (R, Lc), (0.12, Lc + 0.55)]
    outer = lathe('dco', [(0.0, -Lc - 0.58)] + [(r + 0.04, z) for r, z in prof] + [(0.0, Lc + 0.58)], 'stainless', 64)
    inner = lathe('dci', [(0.0, -Lc - 0.55)] + prof + [(0.0, Lc + 0.55)], 'stainless', 64)
    dc = csg('dc', [outer], [inner], 'stainless')
    dc.data.transform(Matrix.Translation((0, 0, CZ)))
    jk = lathe('jk', [(0.12, -Lc - 0.5), (R + 0.06, -Lc - 0.02), (R + 0.06, Lc + 0.02), (0.12, Lc + 0.5), (0.13, Lc + 0.5), (R + 0.075, Lc + 0.02), (R + 0.075, -Lc - 0.02), (0.13, -Lc - 0.5)], 'paint_grey', 64)
    jk.data.transform(Matrix.Translation((0, 0, CZ)))
    ports = [cyl('mh', 0.14, CZ + Lc + 0.55, CZ + Lc + 0.62, 'steel', 32), cyl('do', 0.1, CZ - Lc - 0.62, CZ - Lc - 0.55, 'steel', 32)]
    pv = P(m, 'double_cone', 'Double-Cone Vessel with Heating Jacket, Charging Manway & Discharge Valve', 'vessel', [dc, jk] + ports, explode=(0, 0.6, 0), ref='vd_vessel', section='split', pivot=(0, 0, CZ))
    pv.spin('Y', 0.5)
    pwd = lathe('pwl', [(0.0, CZ - Lc - 0.53), (0.12, CZ - Lc - 0.53), (R - 0.02, CZ - Lc + 0.02), (R - 0.02, CZ - 0.1), (0.0, CZ - 0.1)], 'powder', 48, a0=0.0, a1=math.pi, cap_mat='powder')
    pw = P(m, 'powder', 'Product Tumbling inside (stays low while the vessel turns)', 'fluid', pwd, explode=(0, -0.4, 0), ref='vd_product', section='keep', pivot=(0, 0, CZ))
    keys_loop(m, pw, lambda t: (0, 0.3 * math.sin(TAU * t), 0), 'rotation_euler')
    st = [box(f'st{s}', (0.25, 0.25, CZ + 0.1), (0, s * (R + 0.45), (CZ + 0.1) / 2), 'paint_blue') for s in (-1, 1)]
    st += [cyl(f'tn{s}', 0.07, s * (R + 0.08) if s > 0 else -(R + 0.35), (R + 0.35) if s > 0 else -(R + 0.08), 'steel', 24, axis='Y', center=(0, 0, CZ)) for s in (-1, 1)]
    P(m, 'stands_trunnions', 'Stands, Trunnions & Bearings (vessel rotates about the trunnion axis)', 'structure', st, explode=(0, 0, -0.3), ref='vd_stands', section='split')
    vac = [hollow_pipe('vl', [(0, R + 0.6, CZ), (0, R + 0.9, CZ), (0, R + 0.9, 2.3), (1.2, R + 0.9, 2.3)], 0.04, 'stainless', 24, bend=0.1), vessel('vf', 0.12, 0.3, 0.006, 'stainless', center=(1.4, R + 0.9, 0), heads=('2:1', '2:1'), z0=2.0)]
    vac += [cyl('vt', 0.035, -R - 0.08, R + 0.08, 'stainless', 16, axis='Y', center=(0, 0, CZ)), vessel('cnd', 0.15, 0.6, 0.006, 'paint_blue', center=(1.4, R + 0.9, 0), heads=('2:1', '2:1'), z0=0.6)]
    P(m, 'vacuum_system', 'Vacuum Line (through trunnion), Dust Filter & Condenser to Vacuum Pump', 'vacuum', vac, explode=(0.4, 0.4, 0), ref='vd_vacuum', section='keep')
    dr = join('dr', [box('gb', (0.35, 0.25, 0.35), (0, -(R + 0.7), CZ), 'paint_blue'), cyl('mt', 0.12, -(R + 1.2), -(R + 0.82), 'paint_motor', 32, axis='Y', center=(0, 0, CZ))])
    P(m, 'drive', 'Drive (motor, gearbox; slow rotation ≈ a few rpm)', 'drive', dr, explode=(0, -0.4, 0), ref='vd_drive', section='split')
    m.flow('vapour', [(0, 0.2, CZ), (0, R + 0.9, CZ), (0, R + 0.9, 2.3), (1.4, R + 0.9, 2.3), (1.4, R + 0.9, 1.4)], 'steam', 0.02, 0.3)
    m.flow('heating_medium', [(0.3, -R - 0.3, CZ - 0.3), (0.35, -R + 0.1, CZ - 0.2), (0.35, -R + 0.1, CZ + 0.2), (0.3, -R - 0.3, CZ + 0.3)], 'hydraulic_oil', 0.015, 0.2)
    _bands_z(m, [(CZ - Lc, CZ + Lc, 3)], R + 0.08, 'Low pressure lowers the boiling point',
             'Under vacuum (e.g. ~ 20–100 mbar abs) water and solvents boil at low temperature (≈ 20–45 °C), so heat-sensitive or solvent-wet products can be dried gently. The slow rotation '
             'tumbles the product against the heated wall; vapour is drawn through a filter to a condenser where solvents can be recovered.', kind='pressure')
    return m.export(out)


# =============================================================== EQ-244 Fluidized bed combustor
def fluidized_bed_combustor(out):
    m = _model('fluidized_bed_combustor', 'Bubbling Fluidised Bed Combustor (with In-Bed Tubes & Cyclone)')
    R, ZW, ZD = 0.75, 0.6, 0.9
    sh = csg('sh', [cyl('so', R + 0.12, 0.3, 3.3, 'paint_grey', 64)], [cyl('si', R, 0.35, 3.4, 'paint_grey', 64)], 'paint_grey')
    rf = csg('rl', [cyl('ro', R, ZD, 3.3, 'refractory', 64)], [cyl('ri', R - 0.1, ZD - 0.1, 3.4, 'refractory', 64)], 'refractory')
    top = cyl('tp', R + 0.12, 3.3, 3.4, 'paint_grey', 64)
    P(m, 'combustor_shell', 'Combustor Shell, Refractory Lining & Wind Box (below distributor)', 'casing', [sh, rf, top], explode=(0, 0.8, 0), ref='bc_shell')
    dist = [cyl('dp', R, ZD - 0.02, ZD, 'steel', 64)] + [join(f'bc{i}', [cyl(f'bcs{i}', 0.015, ZD, ZD + 0.08, 'steel', 8, center=(x, y, 0)), cyl(f'bcc{i}', 0.03, ZD + 0.08, ZD + 0.11, 'steel', 12, center=(x, y, 0))])
                                                     for i, (x, y) in enumerate([(0.2 * i - 0.5, 0.2 * j - 0.5) for i in range(6) for j in range(6) if (0.2 * i - 0.5) ** 2 + (0.2 * j - 0.5) ** 2 < (R - 0.15) ** 2])]
    P(m, 'air_distributor', 'Air Distributor Plate with Bubble-Cap Nozzles', 'internals', dist, explode=(0, -0.5, -0.3), ref='bc_distributor', section='keep')
    ibt, ipth = [], []
    for k, z in enumerate((ZD + 0.3, ZD + 0.45)):
        for j, y in enumerate((-0.3, -0.1, 0.1, 0.3)):
            ibt.append(cyl(f'ib{k}{j}', 0.025, -R + 0.12, R - 0.12, 'steel_dark', 12, axis='X', center=(0, y, z)))
    P(m, 'in_bed_tubes', 'In-Bed Heat Transfer Tubes (raise steam, control bed temperature)', 'tubes', ibt, explode=(0, -0.9, 0), ref='bc_tubes', section='keep')
    _bed_particles(m, 'sand_bed', 'Bubbling Sand Bed (inert bed material + fuel + ash)', -R + 0.15, R - 0.15, 0.02, R - 0.2, ZD + 0.12, ZD + 0.65, 45, mat='sand', drift=0.0, r=0.02)
    for k, x in enumerate((-0.3, 0.25)):
        _flame(m, f'bed_flame_{k + 1}', f'Combustion in the Bed {k + 1}', (x, 0.2, ZD + 0.4), (0, 0, 1), 0.5, 0.12, 'bc_bed', explode=(0, -0.3, 0))
    fd = join('fd', [hollow_pipe('fc', [(-1.4, 0, 1.9), (-1.0, 0, 1.9), (-R + 0.05, 0, ZD + 0.9)], 0.1, 'paint_grey', 24, bend=0.1), box('fh', (0.4, 0.4, 0.4), (-1.5, 0, 2.2), 'paint_grey')])
    P(m, 'fuel_feed', 'Fuel Feed Hopper & Chute (coal, biomass, waste)', 'feeder', fd, explode=(-0.5, 0, 0), ref='bc_feed', section='keep')
    ai = [hollow_pipe('ai', [(-1.6, 0, ZW), (-R - 0.1, 0, ZW)], 0.12, 'paint_blue', 24)]
    P(m, 'air_inlet', 'Primary (Fluidising) Air Inlet to Wind Box', 'air', ai, explode=(-0.4, 0, -0.2), ref='bc_air', section='keep')
    cy = _cyclone('cy', 1.6, 0.0, 3.2, R=0.35)
    cy.append(hollow_pipe('xo', [(R + 0.1, 0, 3.05), (1.6 - 0.35 - 0.2, 0, 3.05)], 0.12, 'paint_grey', 24))
    cy.append(hollow_pipe('rl', [(1.6, 0, 2.38), (1.6, 0, 1.4), (R + 0.12, 0, ZD + 0.6)], 0.06, 'paint_grey', 24, bend=0.1))
    P(m, 'cyclone_return', 'Cyclone & Return Leg (fines back to the bed)', 'separator', cy, explode=(0.6, 0, 0), ref='bc_cyclone', section='keep')
    ad = [nozzle('ad', (0, 0, 0.3), (0, 0, -1), 0.08, 0.25)]
    P(m, 'ash_drain', 'Bed Ash Drain', 'nozzles', ad, explode=(0, 0, -0.3), ref='bc_shell', section='keep')
    rocks_along(m, 'fuel', 'Fuel Particles Dropping into the Bed', [(-1.4, 1.9), (-1.0, 1.9), (-R + 0.05, ZD + 0.9), (-0.2, ZD + 0.4)], 6, r=0.03, mat='coal', y=0.05)
    m.flow('fluidising_air', [(-1.8, 0, ZW), (0, 0.1, ZW), (0, 0.1, ZD + 0.7)], 'air', 0.03, 0.3)
    m.flow('flue_gas', [(0, 0.1, ZD + 0.8), (0, 0.1, 3.05), (1.25, 0, 3.05), (1.6, 0, 2.5), (1.6, 0, 3.7)], 'flue_gas', 0.04, 0.4)
    _bands_z(m, [(ZD, ZD + 0.7, 7), (ZD + 0.7, 3.3, 8)], R + 0.1, 'Low, uniform combustion temperature',
             'The bed is kept at roughly 800–900 °C — hot enough to burn the fuel completely but low enough to limit thermal NOx and to let limestone added to the bed capture sulphur. '
             'The large mass of hot sand gives stable combustion even of wet, low-grade or variable fuels.')
    return m.export(out)


# =============================================================== EQ-245 Thermal oxidizer (recuperative)
def thermal_oxidizer(out):
    m = _model('thermal_oxidizer', 'Recuperative Thermal Oxidizer (Burner, Combustion Chamber, Recuperator)')
    CZ, R, X0, X1 = 1.1, 0.55, -1.4, 1.0
    ch = csg('ch', [cyl('cho', R + 0.08, X0, X1, 'paint_grey', 64, axis='X', center=(0, 0, CZ))], [cyl('chi', R, X0 - 0.1, X1 + 0.1, 'paint_grey', 64, axis='X', center=(0, 0, CZ))], 'paint_grey')
    rf = csg('rf', [cyl('rfo', R, X0, X1, 'refractory', 64, axis='X', center=(0, 0, CZ))], [cyl('rfi', R - 0.12, X0 - 0.1, X1 + 0.1, 'refractory', 64, axis='X', center=(0, 0, CZ))], 'refractory')
    ec = cyl('ec', R + 0.08, X0 - 0.05, X0, 'paint_grey', 64, axis='X', center=(0, 0, CZ))
    P(m, 'combustion_chamber', 'Refractory-Lined Combustion Chamber (residence time)', 'casing', [ch, rf, ec], explode=(0, 0.8, 0), ref='to_chamber')
    bn = join('bn', [cyl('bnb', 0.18, X0 - 0.45, X0 - 0.05, 'paint_blue', 32, axis='X', center=(0, 0, CZ)), cyl('bnt', 0.07, X0 - 0.05, X0 + 0.15, 'steel', 24, axis='X', center=(0, 0, CZ))])
    P(m, 'burner', 'Burner (natural gas, with flame safeguard)', 'combustion', bn, explode=(-0.5, 0, 0), ref='to_burner', section='keep')
    _flame(m, 'flame', 'Burner Flame', (X0 + 0.15, 0, CZ), (1, 0, 0), 1.0, 0.2, 'to_burner')
    RX0, RX1 = X1, X1 + 1.2
    rc = csg('rc', [cyl('rco', R + 0.05, RX0, RX1, 'stainless', 64, axis='X', center=(0, 0, CZ))], [cyl('rci', R, RX0 - 0.1, RX1 + 0.1, 'stainless', 64, axis='X', center=(0, 0, CZ))], 'stainless')
    tubes = [cyl(f'rt{k}', 0.03, RX0 + 0.02, RX1 - 0.02, 'steel', 12, axis='X', center=(0, y, z), r_in=0.025) for k, (y, z) in enumerate([(0.12 * i - 0.36, CZ + 0.12 * j - 0.3) for i in range(7) for j in range(6) if (0.12 * i - 0.36) ** 2 + (0.12 * j - 0.3) ** 2 < (R - 0.08) ** 2])]
    bfl = [csg(f'rb{k}', [cyl(f'rbd{k}', R - 0.005, x - 0.005, x + 0.005, 'stainless', 48, axis='X', center=(0, 0, CZ))], [box(f'rbc{k}', (0.1, 2, R * 0.6), (x, 0, CZ + s * (R - R * 0.3)), 'stainless')], 'stainless') for k, (x, s) in enumerate(((RX0 + 0.35, 1), (RX0 + 0.7, -1)))]
    P(m, 'recuperator', 'Shell & Tube Recuperator (preheats the process air with the hot exhaust)', 'exchanger', [rc] + tubes + bfl, explode=(0.5, 0.6, 0), ref='to_recuperator')
    nz = [nozzle('pi', (RX1 - 0.15, 0, CZ - R), (0, 0, -1), 0.12, 0.3), nozzle('po', (RX0 + 0.15, 0, CZ + R), (0, 0, 1), 0.12, 0.25), cyl('pt', 0.12, RX1, RX1 + 0.3, 'paint_grey', 32, axis='X', center=(0, 0, CZ))]
    nz.append(hollow_pipe('xo', [(RX0 + 0.15, 0, CZ + R + 0.25), (RX0 + 0.15, 0, CZ + R + 0.45), (X0 + 0.3, 0, CZ + R + 0.45), (X0 + 0.3, 0, CZ + R + 0.05)], 0.1, 'stainless', 24, bend=0.12))
    P(m, 'ducts_nozzles', 'Process-Air Inlet/Outlet Nozzles, Hot-Air Crossover Duct & Exhaust Outlet', 'ducts', nz, explode=(0, 0, 0.4), ref='to_recuperator', section='keep')
    stk = cyl('stk', 0.15, 0.5, 4.0, 'paint_grey', 32, center=(RX1 + 0.6, 0, 0), r_in=0.14)
    stk = join('stkj', [stk, hollow_pipe('sx', [(RX1 + 0.3, 0, CZ), (RX1 + 0.6, 0, CZ)], 0.12, 'paint_grey', 24)])
    P(m, 'stack', 'Stack (clean exhaust)', 'casing', stk, explode=(0.5, 0, 0), ref='to_stack', section='keep')
    fn = csg('fh', [cyl('fho', 0.35, -0.15, 0.15, 'paint_blue', 48, axis='Y', center=(RX1 - 0.15, 0, 0.35))], [cyl('fhi', 0.32, -0.12, 0.12, 'paint_blue', 48, axis='Y', center=(RX1 - 0.15, 0, 0.35))], 'paint_blue')
    P(m, 'fan_housing', 'Process Fan Housing (VOC-laden air)', 'fan', fn, explode=(0, 0.4, -0.3), ref='to_fan', section='keep')
    _fan_rotor(m, 'fan', 'Process Fan Impeller', (RX1 - 0.15, 0, 0.35), 'Y', 0.28, 'to_fan', revs=5)
    P(m, 'supports', 'Saddle Supports', 'structure', [box(f'sd{k}', (0.2, 0.9, CZ - R), (x, 0, (CZ - R) / 2), 'paint_grey') for k, x in enumerate((X0 + 0.4, X1 - 0.3, RX1 - 0.3))], explode=(0, 0, -0.3), ref='to_chamber', section='keep')
    m.flow('process_air', [(RX1 + 0.2, 0, 0.35), (RX1 - 0.15, 0, 0.35), (RX1 - 0.15, 0, CZ - R - 0.3), (RX1 - 0.15, 0, CZ - 0.3), (RX0 + 0.35, 0.3, CZ - 0.3), (RX0 + 0.15, 0, CZ + R + 0.45), (X0 + 0.3, 0, CZ + R + 0.45), (X0 + 0.3, 0, CZ + 0.2)], 'exhaust', 0.025, 0.4)
    m.flow('hot_clean_gas', [(X0 + 0.5, 0.1, CZ), (RX1, 0.1, CZ), (RX1 + 0.6, 0, CZ), (RX1 + 0.6, 0, 4.1)], 'flue_gas', 0.03, 0.4)
    _bands_x(m, [(X0, X1, 9), (RX0, RX1, 5)], 2 * R + 0.2, 2 * R + 0.2, CZ, 'The 3 T\'s: temperature, time, turbulence',
             'VOCs are destroyed by holding the gas at high temperature (typically ~ 760–870 °C, higher for halogenated compounds) for enough residence time (~ 0.5–1 s) with good mixing. '
             'The recuperator recovers heat from the hot clean gas to preheat the incoming air, cutting burner fuel (typically ~ 50–70 % heat recovery for recuperative units).')
    return m.export(out)


# =============================================================== EQ-246 Incinerator (rotary kiln)
def incinerator(out):
    m = _model('incinerator', 'Rotary Kiln Incinerator with Secondary Combustion Chamber')
    R, X0, X1 = 0.5, -1.6, 1.0
    ang = math.radians(2.5)
    zc = lambda x: 1.2 - (x - X0) * math.tan(ang)
    axis = Vector((math.cos(ang), 0, -math.sin(ang)))
    c0 = Vector((X0, 0, zc(X0)))
    L = (X1 - X0) / math.cos(ang)
    kiln = csg('kn', [cyl('kno', R + 0.06, 0, L, 'paint_grey', 64, axis='X', center=(0, 0, 0))], [cyl('kni', R, -0.1, L + 0.1, 'paint_grey', 64, axis='X', center=(0, 0, 0))], 'paint_grey')
    lin = csg('kl', [cyl('klo', R, 0, L, 'refractory', 64, axis='X', center=(0, 0, 0))], [cyl('kli', R - 0.1, -0.1, L + 0.1, 'refractory', 64, axis='X', center=(0, 0, 0))], 'refractory')
    tyres = [cyl(f'ty{k}', R + 0.12, x - 0.06, x + 0.06, 'steel', 64, axis='X', center=(0, 0, 0), r_in=R + 0.06) for k, x in enumerate((0.5, L - 0.5))]
    gear = [cyl('gr', R + 0.16, L / 2 - 0.04, L / 2 + 0.04, 'steel_dark', 64, axis='X', center=(0, 0, 0), r_in=R + 0.06)]
    lifters = [rotate(box(f'lf{k}', (L - 0.2, 0.04, 0.08), (L / 2, 0, -(R - 0.13)), 'refractory'), TAU * k / 6, 'X') for k in range(6)]
    objs = [kiln, lin] + tyres + gear + lifters
    Mx = Matrix.Translation(c0) @ Matrix.Rotation(-ang, 4, 'Y')
    for o in objs:
        o.data.transform(Mx)
    mid = c0 + axis * (L / 2)
    pk = P(m, 'rotary_kiln', 'Rotary Kiln: Shell, Refractory, Riding Tyres & Girth Gear (inclined, rotating)', 'rotating_element', objs, explode=(0, -0.9, 0), ref='ik_kiln', section='split', pivot=tuple(mid))
    for mesh in pk.meshes:
        axis_rot_keys(m, mesh, tuple(axis), lambda t: -TAU * 0.5 * t)
    sup2 = []
    for k, s in enumerate((0.5, L - 0.5)):
        p = c0 + axis * s
        for sy in (-1, 1):
            sup2.append(cyl(f'rr{k}{sy}', 0.12, p.x - 0.08, p.x + 0.08, 'steel', 32, axis='X', center=(0, sy * 0.42, p.z - 0.55)))
            sup2.append(box(f'rp{k}{sy}', (0.3, 0.2, p.z - 0.65), (p.x, sy * 0.42, (p.z - 0.65) / 2), 'paint_grey'))
    pdv = c0 + axis * (L / 2)
    sup2.append(join('kd', [cyl('pn', 0.1, pdv.x - 0.06, pdv.x + 0.06, 'steel', 24, axis='X', center=(0, -0.7, pdv.z - 0.3)), box('kdg', (0.3, 0.3, 0.3), (pdv.x, -1.0, pdv.z - 0.3), 'paint_blue'), cyl('kdm', 0.12, -1.6, -1.15, 'paint_motor', 24, axis='Y', center=(pdv.x, 0, pdv.z - 0.3))]))
    P(m, 'supports_drive', 'Support Rollers, Piers & Kiln Drive (motor, reducer, pinion)', 'structure', sup2, explode=(0, 0, -0.4), ref='ik_supports', section='keep')
    fh = join('fh', [csg('fhc', [box('fho', (0.5, 1.4, 1.4), (X0 - 0.3, 0, zc(X0)), 'paint_grey')], [box('fhi', (0.42, 1.3, 1.3), (X0 - 0.3, 0, zc(X0)), 'paint_grey'), cyl('fhh', R + 0.02, X0 - 0.2, X0 + 0.1, 'paint_grey', 48, axis='X', center=(0, 0, zc(X0)))], 'paint_grey'),
                     box('ch', (0.35, 0.4, 0.6), (X0 - 0.3, 0, zc(X0) + 0.95), 'paint_grey'), cyl('bn', 0.12, X0 - 0.9, X0 - 0.55, 'paint_blue', 24, axis='X', center=(0, 0, zc(X0) - 0.2))])
    P(m, 'feed_hood', 'Feed-End Hood, Waste Feed Chute (ram) & Primary Burner', 'casing', fh, explode=(-0.5, 0, 0), ref='ik_feed', section='keep')
    _flame(m, 'kiln_flame', 'Kiln Burner Flame', (X0 - 0.15, 0, zc(X0) - 0.2), (1, 0, -0.02), 1.0, 0.17, 'ik_feed')
    SX = X1 + 0.6
    scc = csg('scc', [box('sco', (1.0, 1.2, 3.2), (SX, 0, 1.6), 'paint_grey')], [box('sci', (0.82, 1.02, 3.0), (SX, 0, 1.7), 'paint_grey'), cyl('sch', R + 0.02, X1 - 0.2, SX, 'paint_grey', 48, axis='X', center=(0, 0, zc(X1)))], 'paint_grey')
    scr = csg('scr', [box('sro', (0.82, 1.02, 3.0), (SX, 0, 1.7), 'refractory')], [box('sri', (0.66, 0.86, 3.1), (SX, 0, 1.75), 'refractory'), cyl('srh', R + 0.02, X1 - 0.2, SX, 'refractory', 48, axis='X', center=(0, 0, zc(X1)))], 'refractory')
    P(m, 'secondary_chamber', 'Secondary Combustion Chamber (≥ 850 °C, ≥ 2 s) & Ash Quench below', 'casing', [scc, scr], explode=(0.6, 0.6, 0), ref='ik_scc')
    _flame(m, 'scc_flame', 'Secondary (Afterburner) Flame', (SX - 0.4, 0, 2.3), (1, 0, 0.3), 0.5, 0.12, 'ik_scc')
    P(m, 'scc_burner', 'Afterburner', 'combustion', cyl('ab', 0.1, SX - 0.85, SX - 0.45, 'paint_blue', 24, axis='X', center=(0, 0, 2.3)), explode=(-0.3, 0, 0.3), ref='ik_scc', section='keep')
    P(m, 'gas_outlet', 'Hot Gas Outlet to Boiler / Quench & Air Pollution Control', 'casing', hollow_pipe('go', [(SX, 0, 3.2), (SX, 0, 3.6), (SX + 1.0, 0, 3.6)], 0.25, 'paint_grey', 32, bend=0.3), explode=(0.3, 0, 0.5), ref='ik_scc', section='keep')
    pts = [(X0 + 0.1, zc(X0) - R * 0.6), (X1 - 0.1, zc(X1) - R * 0.6), (X1 + 0.35, 0.35)]
    rocks_along(m, 'waste', 'Waste Tumbling down the Kiln, Burning to Ash', [(X0 - 0.3, zc(X0) + 1.2), (X0 - 0.3, zc(X0) - 0.1)] + pts, 12, r=0.05, mat='coal', y=0.15)
    m.flow('flue_gas', [(X0 + 0.2, 0.1, zc(X0)), (X1, 0.1, zc(X1)), (SX, 0.1, zc(X1) + 0.2), (SX, 0.1, 3.4), (SX + 1.1, 0, 3.6)], 'flue_gas', 0.04, 0.4)
    m.flow('waste_feed', [(X0 - 0.3, 0, zc(X0) + 1.4), (X0 - 0.3, 0, zc(X0) + 0.6), (X0 + 0.1, 0, zc(X0) - 0.2)], 'sand', 0.03, 0.3)
    m.flow('ash', [(X1 - 0.1, 0, zc(X1) - 0.3), (X1 + 0.35, 0, 0.3)], 'sand', 0.025, 0.2)
    _bands_z(m, [(0.3, 1.2, 7), (1.2, 3.2, 9)], 0.75, 'Secondary chamber: temperature and residence time',
             'Solids burn and ash out in the kiln (often ~ 850–1200 °C). Gases are then held in the secondary chamber; EU rules (Industrial Emissions Directive) require at least 850 °C for 2 s '
             '(1100 °C if the waste contains more than 1 % halogenated organics as chlorine) to complete combustion of organic compounds. Rapid quenching afterwards limits dioxin re-formation.', cx=SX)
    return m.export(out)


# ===================================================================== metadata
def _std(*items):
    return [{'id': i, 'title': t, 'relevance': r, 'edition': 'to be verified'} for i, t, r in items]


def _c(fn, cons, mat, op='—', fm=('—',), insp=('Visual',)):
    return C(fn, cons, mat, op, list(fm), list(insp))


_EVAP = _std(('ASME BPVC VIII-1', 'Pressure vessels', 'Shells under pressure/vacuum.'), ('TEMA', 'Tubular exchanger standards', 'Calandria/heater design.'))
_DRY = _std(('NFPA 61 / 652', 'Combustible dust (agricultural/food) and fundamentals', 'Dust explosion protection.'), ('ATEX 2014/34/EU', 'Equipment for explosive atmospheres', 'Hazardous areas.'))
_COMB = _std(('NFPA 85 / NFPA 86', 'Boiler and combustion systems / ovens and furnaces', 'Combustion safeguards.'), ('EN 746-2', 'Industrial thermoprocessing equipment — combustion and fuel handling', 'Safety.'))

META = {
    'flash_evaporator': {'summary': ('A flash evaporator separates vapour from a liquid by sudden pressure reduction. The liquid is heated under pressure, then throttled into a vessel at lower pressure; '
                                     'part of it instantly boils ("flashes"), cooling the rest. Vapour leaves through a demister at the top, the concentrated liquid from the bottom.'),
                         'classification': {'family': 'Evaporator', 'type': 'Single-stage flash evaporator'}, 'model_configuration': {'animation': 'Vapour flashing; level control'},
                         'standards': _EVAP, 'references': ['Perry\'s Chemical Engineers\' Handbook — Evaporation'],
                         'components': {'fe_vessel': _c('Flash vessel: vapour/liquid separation at low pressure.', 'Vertical vessel.', 'Stainless steel.', '—', ['Erosion at inlet, corrosion'], ['Thickness']),
                                        'fe_demister': _c('Removes entrained droplets from the vapour.', 'Wire-mesh pad.', 'Stainless steel.', '—', ['Fouling, ΔP rise'], ['ΔP']),
                                        'fe_liquid': _c('Concentrate.', '—', '—'), 'fe_heater': _c('Heats feed under pressure.', 'Shell & tube heater.', 'Steel.'),
                                        'fe_valve': _c('Drops the pressure to cause flashing.', 'Control valve and feed line.', 'Steel.', '—', ['Erosion, cavitation (trim)'], ['Inspect trim'])}},
    'falling_film_evaporator': {'summary': ('In a falling film evaporator the liquid is distributed at the top of long vertical tubes and flows down the inside walls as a thin film, heated by steam condensing '
                                            'outside. Vapour and concentrate leave at the bottom and are split in a separator. Short residence time and small temperature differences suit heat-sensitive products.'),
                                'classification': {'family': 'Evaporator', 'type': 'Falling film with recirculation'}, 'model_configuration': {'animation': 'Film drops fall in the tubes'},
                                'standards': _EVAP, 'references': ['Perry\'s Handbook — Evaporators'],
                                'components': {'ff_calandria': _c('Steam chest and tubes.', 'Vertical shell & tube calandria.', 'Stainless steel.', '—', ['Fouling, dry patches'], ['CIP, ΔT trend']),
                                               'ff_distributor': _c('Spreads liquid evenly into every tube.', 'Perforated distributor plate.', 'Stainless steel.', 'Even wetting is critical.', ['Plugging'], ['Inspect']),
                                               'ff_separator': _c('Separates vapour from concentrate.', 'Vessel.', 'Stainless steel.'), 'ff_piping': _c('Links, steam and condensate.', 'Pipes.', 'Stainless steel.'),
                                               'ff_pump': _c('Recirculates liquid to keep tubes wetted.', 'Centrifugal pump.', '—')}},
    'forced_circulation_evaporator': {'summary': ('A forced circulation evaporator pumps liquid at high velocity through a heat exchanger and then into a separator. Static head keeps the liquid from boiling in the '
                                                  'tubes; it flashes in the separator. This prevents scaling and suits crystallising or viscous liquids.'),
                                      'classification': {'family': 'Evaporator', 'type': 'Forced circulation (suppressed boiling)'}, 'model_configuration': {'animation': 'Liquid circulates round the loop'},
                                      'standards': _EVAP, 'references': ['Perry\'s Handbook — Evaporators'],
                                      'components': {'fc_heater': _c('Heats the circulating liquid.', 'Vertical shell & tube heater.', 'Stainless/titanium.', 'High tube velocity.', ['Scaling, erosion'], ['ΔP, U trend']),
                                                     'fc_separator': _c('Liquid flashes and vapour separates.', 'Vessel.', 'Stainless steel.'), 'fc_loop': _c('Circulation piping.', 'Large-bore pipes.', 'Stainless steel.'),
                                                     'fc_pump': _c('Circulates large flow at low head.', 'Axial/mixed-flow pump.', 'Duplex/stainless.', '—', ['Wear from crystals, cavitation'], ['Vibration'])}},
    'multiple_effect_evaporator': {'summary': ('A multiple effect evaporator uses the vapour from one evaporator body (effect) as the heating steam of the next, which runs at lower pressure and boiling point. '
                                               'Only the first effect uses live steam, so steam consumption per kilogram of water evaporated falls roughly in proportion to the number of effects.'),
                                   'classification': {'family': 'Evaporator', 'type': 'Triple-effect, forward feed'}, 'model_configuration': {'effects': 3, 'animation': 'Boiling in each effect'},
                                   'standards': _EVAP, 'references': ['McCabe, Smith & Harriott — Unit Operations of Chemical Engineering'],
                                   'components': {'me_effect': _c('Calandria of each effect.', 'Short-tube vertical calandria.', 'Stainless steel.', '—', ['Fouling'], ['Clean']),
                                                  'me_body': _c('Vapour body of each effect.', 'Vessel.', 'Stainless steel.'), 'me_liquor': _c('Boiling liquor and transfer lines.', '—', '—'),
                                                  'me_vapour': _c('Vapour lines between effects.', 'Pipes.', 'Stainless steel.'), 'me_condenser': _c('Condenses last-effect vapour; vacuum.', 'Condenser.', 'Steel.')}},
    'spray_dryer': {'summary': ('A spray dryer turns a liquid feed into a dry powder in one step. The liquid is atomised into fine droplets by a fast-spinning wheel or nozzles inside a chamber of hot air; '
                                'the water evaporates in seconds and the dry particles fall to the cone or are collected from the exhaust air by a cyclone.'),
                    'classification': {'family': 'Dryer', 'type': 'Co-current rotary-atomiser spray dryer'}, 'model_configuration': {'animation': 'Atomiser spins; droplets spiral down'},
                    'standards': _DRY, 'references': ['Masters — Spray Drying Handbook'],
                    'components': {'sd_chamber': _c('Drying space.', 'Cylinder-on-cone chamber.', 'Stainless steel.', 'Explosion venting for combustible powders.', ['Wall deposits'], ['Inspect, CIP']),
                                   'sd_disperser': _c('Directs hot air around the atomiser.', 'Roof disperser with vanes.', 'Stainless steel.'),
                                   'sd_atomiser': _c('Creates the spray.', 'High-speed wheel (≈ 10 000 + rpm) and drive.', 'Stainless steel.', '—', ['Wear, imbalance, vibration'], ['Vibration']),
                                   'sd_cyclone': _c('Collects fines from exhaust air.', 'Cyclone and duct.', 'Stainless steel.'), 'sd_valves': _c('Discharge powder.', 'Rotary valves.', '—')}},
    'fluidized_bed_dryer': {'summary': ('A fluidised bed dryer blows hot air up through a perforated plate so a bed of particles lifts and behaves like a boiling liquid. Intense contact between air and every particle gives '
                                        'fast, uniform drying; in continuous units the bed flows from the feed point over a weir to the outlet.'),
                            'classification': {'family': 'Dryer', 'type': 'Continuous rectangular fluid-bed dryer'}, 'model_configuration': {'animation': 'Particles bubble and drift to the weir'},
                            'standards': _DRY, 'references': ['Mujumdar — Handbook of Industrial Drying'],
                            'components': {'fb_body': _c('Plenum and freeboard.', 'Fabricated housing.', 'Stainless steel.'), 'fb_distributor': _c('Distributes air uniformly.', 'Perforated plate.', 'Stainless steel.', 'ΔP across plate gives stable fluidisation.', ['Plugging'], ['Inspect']),
                                           'fb_weir': _c('Sets bed depth; feed chute.', 'Weir plate.', 'Steel.'), 'fb_air': _c('Supplies hot air.', 'Heater, fan, ducts.', '—'), 'fb_cyclone': _c('Captures fines.', 'Cyclone.', 'Steel.')}},
    'flash_dryer': {'summary': ('A flash (pneumatic) dryer disperses a wet, granular feed into a stream of hot gas, which carries it up a drying duct at high velocity. Surface moisture evaporates within '
                                'seconds; a cyclone separates the dry product and an exhaust fan pulls the gas through the system.'),
                    'classification': {'family': 'Dryer', 'type': 'Single-pass flash dryer'}, 'model_configuration': {'animation': 'Particles carried up the riser'},
                    'standards': _DRY, 'references': ['Mujumdar — Handbook of Industrial Drying'],
                    'components': {'fd_heater': _c('Heats the drying gas.', 'Direct burner / heater.', '—'), 'fd_duct': _c('Drying zone.', 'Venturi and riser duct.', 'Steel.', '—', ['Erosion at bends'], ['Thickness']),
                                   'fd_feeder': _c('Feeds and disperses wet material.', 'Screw feeder/disperser.', 'Steel.'), 'fd_cyclone': _c('Separates product.', 'Cyclone, rotary valve.', 'Steel.'), 'fd_fan': _c('Moves the gas.', 'Exhaust fan, stack.', 'Steel.')}},
    'paddle_dryer': {'summary': ('A paddle dryer is an indirect (contact) dryer. Two hollow shafts with wedge-shaped paddles turn in a jacketed trough; steam inside the jacket, shafts and paddles heats the '
                                 'material, while the paddles mix it and move it towards the outlet. Only a small vapour stream leaves, making it suitable for sludges and pastes.'),
                     'classification': {'family': 'Dryer', 'type': 'Twin-shaft hollow paddle (indirect)'}, 'model_configuration': {'animation': 'Shafts counter-rotate; material moves'},
                     'standards': _DRY + _std(('ASME BPVC VIII-1', 'Pressure vessels', 'Jacket and hollow shafts are pressure parts.'),), 'references': ['Mujumdar — Handbook of Industrial Drying'],
                     'components': {'pd_trough': _c('Contains the material; heated jacket.', 'Jacketed W-trough.', 'Steel/stainless.'), 'pd_shafts': _c('Heat, mix and convey.', 'Hollow shafts with wedge paddles.', 'Steel/stainless.', '—', ['Wear, fatigue'], ['Inspect']),
                                    'pd_dome': _c('Collects vapour.', 'Cover with vapour outlet.', 'Steel.'), 'pd_joints': _c('Steam into rotating shafts.', 'Rotary joints with siphons.', '—', '—', ['Leakage'], ['Inspect']),
                                    'pd_drive': _c('Turns the shafts.', 'Motor, gearbox, timing gears.', '—')}},
    'vacuum_dryer': {'summary': ('A rotary double-cone vacuum dryer dries batches of heat-sensitive or solvent-wet powders. The double-cone vessel turns slowly on trunnions so the product tumbles against the heated '
                                 'jacket, while a vacuum pump lowers the pressure so the liquid boils at a low temperature. Vapour passes a filter and condenser.'),
                     'classification': {'family': 'Dryer', 'type': 'Rotary double-cone vacuum dryer (batch)'}, 'model_configuration': {'animation': 'Vessel rotates; product tumbles'},
                     'standards': _DRY + _std(('ASME BPVC VIII-1', 'Pressure vessels', 'Vessel and jacket (full vacuum rating).'),), 'references': ['Pharmaceutical drying guides'],
                     'components': {'vd_vessel': _c('Holds and tumbles the product.', 'Double cone with jacket, manway, discharge valve.', 'Stainless steel (polished).', 'Full vacuum + jacket pressure.', ['Seal leaks'], ['Leak test']),
                                    'vd_product': _c('Product.', '—', '—'), 'vd_stands': _c('Support and rotation axis.', 'Stands and trunnions.', 'Steel.'), 'vd_vacuum': _c('Removes vapour.', 'Line, filter, condenser.', 'Stainless steel.'),
                                    'vd_drive': _c('Rotates the vessel.', 'Motor and gearbox.', '—')}},
    'fluidized_bed_combustor': {'summary': ('A bubbling fluidised bed combustor burns fuel inside a hot bed of sand kept fluidised by air blown through a distributor. The hot, well-mixed bed burns low-grade and variable '
                                            'fuels at a moderate, uniform temperature; tubes in the bed and walls raise steam, and a cyclone returns fines to the bed.'),
                                'classification': {'family': 'Combustion', 'type': 'Bubbling fluidised bed (BFB)'}, 'model_configuration': {'animation': 'Bed bubbles; fuel drops in'},
                                'standards': _COMB, 'references': ['Basu — Combustion and Gasification in Fluidized Beds'],
                                'components': {'bc_shell': _c('Contains the bed and freeboard.', 'Steel shell with refractory, wind box.', 'Steel/refractory.', '—', ['Refractory erosion'], ['Inspect']),
                                               'bc_distributor': _c('Distributes fluidising air.', 'Plate with bubble-cap nozzles.', 'Alloy steel.', '—', ['Nozzle erosion, plugging'], ['Inspect']),
                                               'bc_tubes': _c('Remove heat from the bed.', 'In-bed tubes.', 'Alloy steel.', '—', ['Erosion'], ['Thickness']), 'bc_bed': _c('Combustion zone.', '—', '—'),
                                               'bc_feed': _c('Feeds fuel.', 'Hopper and chute.', 'Steel.'), 'bc_air': _c('Primary air.', 'Duct.', 'Steel.'), 'bc_cyclone': _c('Returns fines.', 'Cyclone and return leg.', 'Steel/refractory.')}},
    'thermal_oxidizer': {'summary': ('A thermal oxidizer destroys volatile organic compounds (VOCs) and odours in process exhaust by burning them at high temperature. The contaminated air is preheated in a recuperator by the hot '
                                     'clean gas, then passes the burner and is held in the combustion chamber long enough for complete oxidation to CO₂ and water.'),
                         'classification': {'family': 'Air pollution control / combustion', 'type': 'Recuperative thermal oxidizer'}, 'model_configuration': {'animation': 'Flame; fan; flows'},
                         'standards': _COMB + _std(('EPA Air Pollution Control Cost Manual', 'Incinerators and oxidizers', 'Design and cost.'),), 'references': ['EPA APC Cost Manual'],
                         'components': {'to_chamber': _c('Gives temperature, time, turbulence.', 'Refractory-lined chamber.', 'Steel/refractory.', '≈ 760–870 °C, 0.5–1 s.', ['Refractory damage'], ['Inspect']),
                                        'to_burner': _c('Supplies heat.', 'Gas burner with safeguard.', '—'), 'to_recuperator': _c('Recovers heat.', 'Shell & tube recuperator, ducts.', 'Stainless/alloy steel.', '—', ['Thermal fatigue, leaks'], ['Inspect']),
                                        'to_stack': _c('Discharges clean gas.', 'Stack.', 'Steel.'), 'to_fan': _c('Moves process air.', 'Centrifugal fan.', 'Steel.')}},
    'incinerator': {'summary': ('A rotary kiln incinerator burns solid, sludge and liquid wastes. Waste fed at the upper end tumbles down the slowly rotating, slightly inclined kiln while it dries, burns and becomes ash. '
                                'The gases pass to a secondary combustion chamber where an afterburner ensures complete combustion before heat recovery and gas cleaning.'),
                    'classification': {'family': 'Combustion / waste treatment', 'type': 'Rotary kiln incinerator with SCC'}, 'model_configuration': {'animation': 'Kiln rotates; waste tumbles; flames'},
                    'standards': _COMB + _std(('Directive 2010/75/EU (IED)', 'Industrial Emissions Directive — waste incineration chapter', '850 °C / 2 s rule.'),), 'references': ['Niessen — Combustion and Incineration Processes'],
                    'components': {'ik_kiln': _c('Burns waste while turning it.', 'Inclined steel shell with refractory, tyres, girth gear.', 'Steel/refractory.', '≈ 0.5–3 rpm, 1–3° slope.', ['Refractory loss, shell hot spots'], ['Shell scanner']),
                                   'ik_supports': _c('Support and drive.', 'Rollers, piers, drive.', 'Steel.'), 'ik_feed': _c('Feeds waste; primary firing.', 'Feed hood, ram, burner.', 'Steel.'),
                                   'ik_scc': _c('Completes gas combustion.', 'Refractory-lined chamber with afterburner.', 'Steel/refractory.', '≥ 850 °C for ≥ 2 s.', ['Slagging'], ['Temperature monitoring'])}},
}
BUILDERS = {k: globals()[k] for k in META}
