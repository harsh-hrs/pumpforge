"""Filtration & Separation — filters, membranes, centrifuges, magnetic separation (EQ-253 … EQ-261)."""
import math
from mathutils import Matrix, Vector
from pumpforge.core import Model, lathe, cyl, box, csg, join, rotate, TAU, OPERATE_FRAMES
from pumpforge.valvekit import P, keys_loop, smooth_pulse
from pumpforge.parts import hollow_pipe, pressure_gauge, add_tracers
from pumpforge.vesselkit import vessel, nozzle, legs, droplets, liquid_v, half, animate_level
from pumpforge.handlingkit import rocks_along
from pumpforge.shapes import sweep_tube
from pumpforge.common_meta import C
from pumps._eq_thermal_a import _hduct, _hliq, _bands_z, _bands_x, _pump, _fan_rotor

CAT = '11 · Filtration & Separation Equipment'


def _model(pid, title):
    return Model(pid, title, CAT, META[pid])


def _press(m, objs, title, desc):
    m.overlay('pressure', join('press', objs), title, desc, split=True)


def _stick_particles(m, pid, name, starts, ends, mat='coal', r=0.012, ref='flow_tracers'):
    """Particles that travel from start to end in the first half of their cycle and then stay (captured); hidden at loop restart."""
    p = m.part(pid, name, 'flow_tracers', explode=(0, 0, 0), info={'ref': ref})
    for i, (a, b) in enumerate(zip(starts, ends)):
        ms = p.add(lathe(f'{pid}{i}', [(r * math.sin(k * math.pi / 6), -r * math.cos(k * math.pi / 6)) for k in range(7)], mat, 10), smooth_angle=80)
        ph = (i * 0.21) % 0.5
        lk, sk = [], []
        for f in range(OPERATE_FRAMES + 1):
            t = f / OPERATE_FRAMES
            u = min(1.0, max(0.0, (t - ph) / 0.35))
            pos = tuple(Vector(a).lerp(Vector(b), u))
            lk.append((1 + f, pos))
            v = 0.0 if t < ph else 1.0
            sk.append((1 + f, (v, v, v)))
        ms.location = lk[0][1]
        m.keyframes(ms, 'Operate', 'location', lk)
        m.keyframes(ms, 'Operate', 'scale', sk)
    return p


def _pressure_vessel_h(name, x0, L, y, z, R=0.1, mat='polypropylene'):
    """Horizontal membrane pressure vessel (FRP) with end caps and ports."""
    return join(name, [cyl(name + 's', R, x0, x0 + L, mat, 48, axis='X', center=(0, y, z), r_in=R - 0.008),
                       cyl(name + 'c0', R + 0.015, x0 - 0.05, x0, 'paint_grey', 48, axis='X', center=(0, y, z)),
                       cyl(name + 'c1', R + 0.015, x0 + L, x0 + L + 0.05, 'paint_grey', 48, axis='X', center=(0, y, z))])


# =============================================================== EQ-253 Cartridge filter
def cartridge_filter(out):
    m = _model('cartridge_filter', 'Multi-Cartridge Filter Housing (Outside-In Pleated Cartridges)')
    R, Z0, L = 0.32, 0.55, 0.85
    hs = vessel('hs', R, L, 0.008, 'stainless', heads=('2:1', 'flat'), z0=Z0)
    fl = cyl('fl', R + 0.05, Z0 + L - 0.03, Z0 + L, 'stainless', 64)
    P(m, 'housing', 'Housing (pressure vessel) & Body Flange', 'casing', [hs, fl], explode=(0, 0.5, 0), ref='cf_housing')
    cv = join('cv', [vessel('cvh', R, 0.02, 0.008, 'stainless', heads=('flat', '2:1'), z0=Z0 + L), cyl('cvf', R + 0.05, Z0 + L, Z0 + L + 0.03, 'stainless', 64),
                     cyl('vt', 0.015, Z0 + L + R * 0.5, Z0 + L + R * 0.5 + 0.1, 'brass', 12)] + [cyl(f'eb{k}', 0.018, Z0 + L - 0.05, Z0 + L + 0.08, 'steel', 8, center=((R + 0.03) * math.cos(TAU * k / 8), (R + 0.03) * math.sin(TAU * k / 8), 0)) for k in range(8)])
    P(m, 'cover', 'Bolted (or swing-bolt) Cover with Vent', 'casing', cv, explode=(0, 0, 0.6), ref='cf_cover')
    TS = Z0 + 0.12
    P(m, 'tube_sheet', 'Tube Sheet / Cartridge Seat Plate (separates dirty and clean sides)', 'internals', cyl('ts', R - 0.008, TS - 0.015, TS, 'stainless', 64), explode=(0, -0.3, -0.2), ref='cf_tubesheet', section='split')
    pos = [(0.0, 0.0)] + [(0.18 * math.cos(TAU * k / 6), 0.18 * math.sin(TAU * k / 6)) for k in range(6)]
    cart = []
    for i, (x, y) in enumerate(pos):
        cart.append(cyl(f'cc{i}', 0.03, TS, TS + 0.62, 'steel', 16, center=(x, y, 0), r_in=0.024))
        cart.append(cyl(f'ce{i}', 0.058, TS + 0.62, TS + 0.64, 'paint_blue', 24, center=(x, y, 0)))
        cart += [rotate(box(f'pl{i}_{k}', (0.022, 0.006, 0.6), (x + 0.045, y, TS + 0.31), 'polypropylene'), TAU * k / 18, 'Z', (x, y, 0)) for k in range(18)]
    P(m, 'cartridges', 'Pleated Filter Cartridges (media wrapped round perforated cores)', 'filter_media', cart, explode=(0, -0.6, 0.5), ref='cf_cartridges', section='keep')
    nz = [nozzle('in', (-R, 0, Z0 + 0.55), (-1, 0, 0), 0.06, 0.25), nozzle('out', (0, 0, Z0 - R * 0.5), (0, 0, -1), 0.06, 0.25), nozzle('dr', (R * 0.6, 0, Z0 - R * 0.3), (0, 0, -1), 0.02, 0.15),
          box('dpg', (0.1, 0.06, 0.1), (R + 0.12, 0, Z0 + 0.4), 'paint_grey'), cyl('dpi', 0.012, R, R + 0.07, 'steel', 8, axis='X', center=(0, 0, Z0 + 0.55)), cyl('dpo', 0.012, R, R + 0.07, 'steel', 8, axis='X', center=(0, 0, Z0 + 0.0))]
    P(m, 'nozzles_gauge', 'Inlet, Outlet, Drain & Differential-Pressure Gauge', 'nozzles', nz, explode=(0, 0, -0.3), ref='cf_dp', section='keep')
    P(m, 'legs', 'Support Legs', 'structure', legs('lg', R, 0.0, Z0 - 0.05, n=3), explode=(0, 0, -0.3), ref='cf_housing', section='keep')
    starts = [(-R + 0.03, 0.06 + 0.02 * (i % 3), Z0 + 0.45 + 0.03 * (i % 4)) for i in range(10)]
    ends = [(pos[k][0] + 0.06 * math.cos(1.2 + 0.3 * i), max(0.02, pos[k][1] + 0.06 * math.sin(1.2 + 0.3 * i)), TS + 0.15 + 0.045 * i) for i, k in enumerate((1, 2, 0, 3, 1, 2, 0, 3, 2, 1))]
    _stick_particles(m, 'dirt', 'Dirt Particles Captured on the Media', starts, ends, mat='coal', r=0.01)
    add_tracers(m, 'clean_fluid', 'Filtered Fluid flowing down the Cartridge Cores', [(0, 0.03, TS + 0.6), (0, 0.03, TS), (0, 0.03, Z0 - R * 0.5 - 0.25)], n=6, radius=0.012, mat='water')
    m.flow('dirty', [(-R - 0.3, 0, Z0 + 0.55), (-0.1, 0.1, Z0 + 0.55), (0.08, 0.1, Z0 + 0.4)], 'flow_suction', 0.015, 0.2)
    m.flow('filtrate', [(0.0, 0.05, TS + 0.55), (0.0, 0.05, TS - 0.02), (0, 0, Z0 - R * 0.5 - 0.3)], 'water', 0.015, 0.2)
    _press(m, [cyl('pu', R + 0.04, TS, Z0 + L, 'pressure_7', 64, r_in=R + 0.02), cyl('pd', R + 0.04, Z0 - 0.1, TS, 'pressure_4', 64, r_in=R + 0.02)],
           'Differential pressure across the cartridges', 'Upstream (dirty side, red) pressure is higher than downstream (clean side, green). As dirt builds on the media the differential '
           'pressure (ΔP) rises; cartridges are changed at the maker\'s terminal ΔP (often ~ 1–2.5 bar) or a set interval. Too high a ΔP can collapse or bypass a cartridge.')
    return m.export(out)


# =============================================================== EQ-254 Membrane filter (plate-and-frame)
def membrane_filter(out):
    m = _model('membrane_filter', 'Plate-and-Frame Membrane Filter (Flat-Sheet Membranes, Cross-Flow)')
    CZ, N, T, X0 = 1.0, 9, 0.045, -0.4
    hd = join('hd', [box('fh', (0.12, 0.7, 0.7), (X0 - 0.06, 0, CZ), 'paint_blue'), box('fhb', (0.25, 0.8, CZ - 0.35), (X0 - 0.1, 0, (CZ - 0.35) / 2), 'paint_blue')])
    P(m, 'fixed_head', 'Fixed Head (feed & retentate ports) & Stand', 'frame', hd, explode=(-0.4, 0, 0), ref='mf_frame')
    plates, perm = [], []
    for k in range(N):
        x = X0 + T / 2 + k * T
        plates.append(box(f'pt{k}', (T * 0.7, 0.6, 0.6), (x, 0, CZ), 'polypropylene' if k % 2 else 'thermoplastic', bevel=0.004))
        plates.append(box(f'mb{k}', (0.004, 0.58, 0.58), (x + T * 0.4, 0, CZ), 'ptfe'))
        perm.append(cyl(f'po{k}', 0.008, CZ - 0.38, CZ - 0.3, 'polypropylene', 8, center=(x, 0.25, 0)))
    P(m, 'plate_stack', 'Plate Stack: Support Plates with Flat-Sheet Membranes & Spacers', 'filter_media', plates, explode=(0, -0.6, 0), ref='mf_plates', section='split')
    XE = X0 + N * T
    fol = join('fl', [box('fb', (0.1, 0.7, 0.7), (XE + 0.05, 0, CZ), 'paint_blue'), cyl('rod', 0.04, XE + 0.1, XE + 0.6, 'chrome', 24, axis='X', center=(0, 0, CZ)),
                      cyl('cy', 0.08, XE + 0.6, XE + 1.1, 'paint_red', 32, axis='X', center=(0, 0, CZ)), box('eh', (0.12, 0.7, 0.7), (XE + 1.16, 0, CZ), 'paint_blue'),
                      box('ehb', (0.25, 0.8, CZ - 0.35), (XE + 1.16, 0, (CZ - 0.35) / 2), 'paint_blue')])
    P(m, 'closure', 'Follower Plate, Hydraulic Closing Cylinder & End Stand', 'frame', fol, explode=(0.5, 0, 0), ref='mf_closure', section='keep')
    sb = [box(f'sb{s}', (XE + 1.4 - X0, 0.06, 0.08), ((X0 + XE + 1.2) / 2, s * 0.38, CZ + 0.38), 'steel') for s in (-1, 1)]
    P(m, 'side_bars', 'Side Bars (carry the plates)', 'frame', sb, explode=(0, 0, 0.4), ref='mf_frame', section='keep')
    pm = [cyl('ph', 0.03, X0, XE, 'polypropylene', 16, axis='X', center=(0, 0.25, CZ - 0.42)), box('tr', (XE - X0 + 0.1, 0.15, 0.06), ((X0 + XE) / 2, 0.25, CZ - 0.47), 'stainless')] + perm
    P(m, 'permeate_collection', 'Permeate Outlets & Collection Trough', 'outlets', pm, explode=(0, 0.4, -0.3), ref='mf_permeate', section='keep')
    nz = [nozzle('fi', (X0 - 0.12, 0, CZ - 0.2), (-1, 0, 0), 0.04, 0.25), nozzle('ro', (X0 - 0.12, 0, CZ + 0.2), (-1, 0, 0), 0.04, 0.25)]
    P(m, 'ports', 'Feed Inlet & Retentate (concentrate) Outlet', 'nozzles', nz, explode=(-0.3, 0, 0), ref='mf_frame', section='keep')
    pth = [(X0 - 0.35, 0.05, CZ - 0.2)]
    for k in range(N):
        x = X0 + T / 2 + k * T
        pth += [(x, 0.05, CZ - 0.25 if k % 2 == 0 else CZ + 0.25), (x, 0.05, CZ + 0.25 if k % 2 == 0 else CZ - 0.25)]
    add_tracers(m, 'feed_tracers', 'Feed Sweeping Across the Membranes (cross-flow)', pth, n=14, radius=0.012, mat='flow_discharge')
    droplets(m, 'permeate', 'Permeate Dripping into the Trough', X0, XE, CZ - 0.38, CZ - 0.47, n=N, mat='water', y=0.25, r=0.008)
    m.flow('feed', [(X0 - 0.4, 0, CZ - 0.2), (X0 + 0.02, 0, CZ - 0.2), (XE - 0.02, 0, CZ - 0.2)], 'flow_suction', 0.015, 0.2)
    m.flow('retentate', [(XE - 0.02, 0, CZ + 0.2), (X0 + 0.02, 0, CZ + 0.2), (X0 - 0.4, 0, CZ + 0.2)], 'flow_discharge', 0.015, 0.2)
    m.flow('permeate', [(X0, 0.25, CZ - 0.42), (XE + 0.2, 0.25, CZ - 0.42), (XE + 0.2, 0.25, 0.2)], 'water', 0.012, 0.2)
    _press(m, [box('pf', (XE - X0, 0.02, 0.62), ((X0 + XE) / 2, -0.33, CZ), 'pressure_7'), box('pp', (XE - X0, 0.02, 0.1), ((X0 + XE) / 2, 0.33, CZ - 0.42), 'pressure_1')],
           'Trans-membrane pressure drives permeation', 'Feed is held at pressure on one side of each membrane (red); permeate leaves at near-atmospheric pressure (blue). The trans-membrane '
           'pressure (TMP) pushes liquid through the pores, while the feed sweeps across the surface (cross-flow) to limit the fouling layer.')
    return m.export(out)


# =============================================================== EQ-255 Microfiltration (submerged hollow fibre)
def microfiltration_system(out):
    m = _model('microfiltration_system', 'Submerged Hollow-Fibre Microfiltration System (Membrane Tank, Permeate Pump, Air Scour)')
    X0, X1, W, H = -0.9, 0.9, 0.9, 1.5
    tk = csg('tk', [box('tko', (X1 - X0 + 0.06, W + 0.06, H), (0, 0, H / 2), 'paint_grey')], [box('tki', (X1 - X0, W, H), (0, 0, H / 2 + 0.03), 'paint_grey')], 'paint_grey')
    P(m, 'membrane_tank', 'Membrane Tank (open, concrete or steel)', 'tank', tk, explode=(0, 0.6, 0), ref='mfs_tank')
    pw = P(m, 'mixed_liquor', 'Feed / Mixed Liquor in the Tank', 'fluid', box('wt', (X1 - X0 - 0.01, W / 2 - 0.01, H - 0.25), (0, W / 4, (H - 0.25) / 2 + 0.03), 'water'), explode=(0, -0.3, 0), ref='mfs_tank', section='keep')
    animate_level(m, pw, H - 0.22, 0.03, lambda t: 0.5 + 0.5 * math.sin(TAU * t))
    cs = [box('ht', (1.2, 0.5, 0.06), (0, 0, 1.15), 'polypropylene'), box('hb', (1.2, 0.5, 0.06), (0, 0, 0.3), 'polypropylene')] + \
         [box(f'fr{k}{s}', (0.04, 0.5, 0.92), (s * 0.62, 0, 0.72), 'stainless') for k, s in enumerate((-1, 1))]
    fib = [cyl(f'fb{i}_{j}', 0.006, 0.33, 1.12, 'ptfe', 6, center=(-0.55 + 0.1 * i, -0.2 + 0.1 * j, 0)) for i in range(12) for j in range(5)]
    P(m, 'membrane_cassette', 'Membrane Cassette: Hollow Fibres (≈ 0.1–0.4 µm pores) between Potted Headers', 'filter_media', cs + fib, explode=(0, -0.7, 0.6), ref='mfs_fibres', section='keep')
    df = [cyl('df', 0.025, -0.6, 0.6, 'stainless', 12, axis='X', center=(0, 0, 0.15))] + [cyl(f'dh{k}', 0.01, 0.15, 0.2, 'stainless', 8, center=(-0.5 + 0.2 * k, 0, 0)) for k in range(6)]
    df.append(hollow_pipe('ap', [(-0.6, 0, 0.15), (-0.8, 0, 0.15), (-0.8, 0, H + 0.2), (X0 - 0.5, 0, H + 0.2), (X0 - 0.5, 0, 0.6)], 0.03, 'stainless', 16, bend=0.06))
    P(m, 'air_diffuser', 'Air-Scour Diffuser & Air Line', 'aeration', df, explode=(0, 0, -0.4), ref='mfs_air', section='keep')
    bl = csg('blh', [cyl('blo', 0.22, -0.12, 0.12, 'paint_blue', 48, axis='Y', center=(X0 - 0.5, 0, 0.4))], [cyl('bli', 0.19, -0.1, 0.1, 'paint_blue', 48, axis='Y', center=(X0 - 0.5, 0, 0.4))], 'paint_blue')
    P(m, 'blower', 'Air-Scour Blower Housing', 'aeration', bl, explode=(-0.3, 0, 0), ref='mfs_air', section='keep')
    _fan_rotor(m, 'blower_rotor', 'Blower Impeller', (X0 - 0.5, 0, 0.4), 'Y', 0.16, 'mfs_air', revs=6)
    pp = [hollow_pipe('pm', [(0.0, 0, 1.18), (0.0, 0, H + 0.3), (X1 + 0.6, 0, H + 0.3), (X1 + 0.6, 0, 0.45)], 0.035, 'stainless', 16, bend=0.06)]
    P(m, 'permeate_line', 'Permeate Header & Line (under suction)', 'piping', pp, explode=(0, 0, 0.4), ref='mfs_permeate', section='keep')
    _pump(m, 'permeate_pump', 'Permeate Pump (reversible for backpulse)', X1 + 0.6, 0.0, 0.3, 'mfs_permeate', explode=(0.3, 0, 0))
    droplets(m, 'air_bubbles', 'Coarse Air Bubbles scouring the Fibres', -0.55, 0.55, 0.2, H - 0.25, n=16, mat='air', y=0.12, r=0.02)
    m.flow('permeate', [(0.0, 0.0, 0.9), (0.0, 0, H + 0.3), (X1 + 0.6, 0, H + 0.3), (X1 + 0.6, 0, 0.5)], 'water', 0.015, 0.3)
    m.flow('air', [(X0 - 0.5, 0, 0.62), (X0 - 0.5, 0, H + 0.2), (-0.8, 0, H + 0.2), (-0.8, 0, 0.15), (0.5, 0, 0.15)], 'air', 0.015, 0.3)
    m.flow('feed', [(X0 - 0.2, 0.3, H - 0.1), (X0 + 0.2, 0.3, H - 0.3)], 'flow_suction', 0.02, 0.2)
    _press(m, [box('pt', (1.2, 0.02, 0.8), (0, -0.28, 0.72), 'pressure_3'), cyl('pq', 0.05, 1.2, H + 0.25, 'pressure_1', 16, r_in=0.04)],
           'Suction-driven filtration (low TMP)', 'The permeate pump applies a gentle suction inside the fibres (trans-membrane pressure typically only ~ 0.1–0.5 bar), drawing clean water '
           'in through the pores while solids stay outside. Air scouring and periodic back-pulsing keep the fibre surfaces clean.')
    return m.export(out)


# =============================================================== EQ-256 Ultrafiltration (pressurised modules)
def ultrafiltration_system(out):
    m = _model('ultrafiltration_system', 'Pressurised Hollow-Fibre Ultrafiltration Skid')
    xs = (-0.45, -0.15, 0.15, 0.45)
    Z0, L, R = 0.45, 1.3, 0.1
    mods = []
    for k, x in enumerate(xs):
        mods.append(cyl(f'md{k}', R, Z0, Z0 + L, 'polypropylene', 48, center=(x, 0, 0), r_in=R - 0.008))
        mods += [cyl(f'mc{k}{s}', R + 0.012, z, z + 0.06, 'paint_grey', 48, center=(x, 0, 0)) for s, z in enumerate((Z0 - 0.06, Z0 + L))]
    P(m, 'modules', 'UF Modules (pressure housings)', 'casing', mods, explode=(0, 0.5, 0), ref='uf_modules')
    fib = [cyl(f'f{k}_{i}', 0.005, Z0 + 0.03, Z0 + L - 0.03, 'ptfe', 6, center=(x + 0.06 * math.cos(TAU * i / 8 + 0.4), abs(0.06 * math.sin(TAU * i / 8 + 0.4)), 0)) for k, x in enumerate(xs) for i in range(8)]
    fib += [cyl(f'fc{k}', 0.005, Z0 + 0.03, Z0 + L - 0.03, 'ptfe', 6, center=(x, 0.0, 0)) for k, x in enumerate(xs)]
    P(m, 'fibres', 'Hollow Fibres (≈ 0.01–0.1 µm; inside-out or outside-in)', 'filter_media', fib, explode=(0, -0.6, 0.3), ref='uf_fibres', section='keep')
    hd = [hollow_pipe('hf', [(-0.8, -0.2, Z0 - 0.2), (0.6, -0.2, Z0 - 0.2)], 0.04, 'paint_blue', 16), hollow_pipe('hp', [(-0.8, -0.2, Z0 + L + 0.2), (0.6, -0.2, Z0 + L + 0.2)], 0.04, 'paint_green', 16),
          hollow_pipe('hc', [(-0.8, 0.2, Z0 + L - 0.1), (0.6, 0.2, Z0 + L - 0.1)], 0.03, 'paint_red', 16)]
    for k, x in enumerate(xs):
        hd += [cyl(f'cf{k}', 0.018, Z0 - 0.2, Z0 - 0.06, 'paint_blue', 12, center=(x, -0.1, 0)), cyl(f'cp{k}', 0.018, Z0 + L + 0.06, Z0 + L + 0.2, 'paint_green', 12, center=(x, -0.1, 0)),
               cyl(f'cc{k}', 0.015, x + R, x + R + 0.05, 'paint_red', 12, axis='X', center=(0, 0.1, Z0 + L - 0.1))]
    P(m, 'headers', 'Feed (blue), Filtrate (green) & Concentrate/Backwash (red) Headers', 'piping', hd, explode=(0, 0, 0.3), ref='uf_headers', section='keep')
    fr = [box(f'fr{k}', (1.7, 0.05, 0.05), (-0.1, s * 0.3, z), 'paint_grey') for k, (s, z) in enumerate(((-1, 0.2), (1, 0.2), (-1, Z0 + L + 0.3), (1, Z0 + L + 0.3)))]
    fr += [box(f'fp{k}', (0.05, 0.05, Z0 + L + 0.3), (x, s * 0.3, (Z0 + L + 0.3) / 2), 'paint_grey') for k, (x, s) in enumerate(((-0.9, -1), (-0.9, 1), (0.7, -1), (0.7, 1)))]
    P(m, 'skid_frame', 'Skid Frame', 'structure', fr, explode=(0, 0, -0.3), ref='uf_modules', section='keep')
    _pump(m, 'feed_pump', 'Feed Pump', -1.3, -0.2, 0.25, 'uf_pumps', explode=(-0.3, 0, 0), facing=-1)
    st = join('st', [cyl('stb', 0.07, -0.95, -0.85, 'paint_grey', 24, axis='X', center=(0, -0.2, 0.25)), cyl('stv', 0.07, 0.25, 0.45, 'paint_grey', 24, center=(-0.9, -0.2, 0))])
    P(m, 'strainer', 'Self-Cleaning Pre-Strainer (protects fibres)', 'filter_media', st, explode=(0, -0.3, -0.2), ref='uf_headers', section='keep')
    ck = vessel('ck', 0.25, 0.7, 0.006, 'polypropylene', heads=('flat', 'flat'), z0=0.0, center=(1.3, 0, 0))
    P(m, 'backwash_tank', 'Filtrate / Backwash & CIP Tank', 'tank', ck, explode=(0.4, 0, 0), ref='uf_tank')
    pfl = P(m, 'tank_water', 'Filtrate in Tank', 'fluid', liquid_v('tw', 0.24, 0.0, 0.5, head='flat', mat='water', cx=1.3), explode=(0.4, -0.3, 0), ref='uf_tank', section='keep')
    animate_level(m, pfl, 0.49, 0.05, lambda t: smooth_pulse(t, 0.3, 0.2, 0.3))
    _pump(m, 'backwash_pump', 'Backwash Pump', 1.0, 0.45, 0.25, 'uf_pumps', explode=(0.3, 0.3, 0), facing=-1)
    m.flow('feed', [(-1.6, -0.2, 0.25), (-0.9, -0.2, 0.25), (-0.9, -0.2, Z0 - 0.2), (0.45, -0.2, Z0 - 0.2), (0.45, 0.02, Z0 + 0.3)], 'flow_suction', 0.015, 0.3, active=[(0.0, 0.8)])
    m.flow('filtrate', [(-0.15, 0.03, Z0 + 0.2), (-0.15, -0.1, Z0 + L + 0.2), (0.6, -0.2, Z0 + L + 0.2), (1.3, 0, Z0 + L + 0.2), (1.3, 0, 0.75)], 'water', 0.015, 0.3, active=[(0.0, 0.8)])
    m.flow('backwash', [(1.0, 0.45, 0.25), (1.0, 0.2, Z0 + L - 0.1), (-0.8, 0.2, Z0 + L - 0.1)], 'flow_discharge', 0.015, 0.3, active=[(0.8, 1.0)])
    _press(m, [cyl(f'pz{k}', R + 0.03, Z0, Z0 + L, 'pressure_5', 48, center=(x, 0, 0), r_in=R + 0.015) for k, x in enumerate(xs)],
           'Moderate trans-membrane pressure', 'UF modules typically run at a trans-membrane pressure of roughly 0.2–2 bar. Water and dissolved salts pass; suspended solids, colloids, '
           'bacteria and most viruses are retained. Every 20–60 min a short backwash (and sometimes chemically enhanced backwash) restores the flux.')
    return m.export(out)


# =============================================================== EQ-257 Nanofiltration
def nanofiltration_system(out):
    m = _model('nanofiltration_system', 'Nanofiltration Unit (Spiral-Wound Elements, 2:1 Array)')
    X0, L, R = -0.8, 1.6, 0.1
    pv = [(-0.15, 0.6), (0.15, 0.6), (0.0, 1.0)]
    vs = [_pressure_vessel_h(f'pv{k}', X0, L, y, z, R) for k, (y, z) in enumerate(pv)]
    P(m, 'pressure_vessels', 'FRP Pressure Vessels (stage 1: two, stage 2: one)', 'casing', vs, explode=(0, 0.6, 0), ref='nf_vessels')
    el = []
    for k, (y, z) in enumerate(pv):
        el.append(cyl(f'pt{k}', 0.015, X0, X0 + L, 'polypropylene', 12, axis='X', center=(0, y, z)))
        for j in range(5):
            r = 0.025 + 0.013 * j
            el.append(cyl(f'sw{k}{j}', r + 0.003, X0 + 0.05, X0 + L - 0.05, 'ptfe' if j % 2 else 'paint_grey', 32, axis='X', center=(0, y, z), r_in=r))
        el += [cyl(f'ic{k}{q}', R - 0.01, x, x + 0.015, 'polypropylene', 24, axis='X', center=(0, y, z), r_in=0.02) for q, x in enumerate((X0 + 0.04, X0 + L / 2, X0 + L - 0.06))]
    P(m, 'spiral_elements', 'Spiral-Wound Membrane Elements (membrane leaves, feed spacers, permeate tube)', 'filter_media', el, explode=(0, -0.6, 0.3), ref='nf_elements', section='keep')
    pip = [hollow_pipe('fd', [(-1.6, 0, 0.3), (X0 - 0.15, 0, 0.3), (X0 - 0.15, -0.15, 0.6), (X0 - 0.05, -0.15, 0.6)], 0.03, 'stainless', 16, bend=0.06),
           hollow_pipe('fd2', [(X0 - 0.15, 0, 0.3), (X0 - 0.15, 0.15, 0.6), (X0 - 0.05, 0.15, 0.6)], 0.03, 'stainless', 16, bend=0.06),
           hollow_pipe('s12', [(X0 + L + 0.05, -0.15, 0.6), (X0 + L + 0.15, -0.15, 0.6), (X0 + L + 0.15, 0, 0.8), (X0 - 0.2, 0, 0.8), (X0 - 0.2, 0, 1.0), (X0 - 0.05, 0, 1.0)], 0.025, 'stainless', 16, bend=0.05),
           hollow_pipe('cn', [(X0 + L + 0.05, 0, 1.0), (X0 + L + 0.35, 0, 1.0), (X0 + L + 0.35, 0, 0.2)], 0.025, 'stainless', 16, bend=0.05),
           hollow_pipe('pm', [(X0 + L + 0.05, 0.4, 1.25), (X0 - 0.3, 0.4, 1.25)], 0.03, 'polypropylene', 16)]
    pip += [hollow_pipe(f'ps{k}', [(X0 - 0.05, y, z), (X0 - 0.25, y, z), (X0 - 0.25, 0.4, 1.25)], 0.015, 'polypropylene', 12, bend=0.03) for k, (y, z) in enumerate(pv)]
    pip += [box('cv', (0.1, 0.1, 0.1), (X0 + L + 0.35, 0, 0.6), 'paint_blue_dark'), pressure_gauge('pg1', (X0 - 0.15, -0.05, 0.42), r=0.04, facing=(0, -1, 0))]
    P(m, 'piping', 'Feed Manifold, Interstage, Concentrate Line (with control valve) & Permeate Header', 'piping', pip, explode=(0, 0, 0.3), ref='nf_piping', section='keep')
    cf = join('cf', [vessel('cfv', 0.12, 0.5, 0.006, 'stainless', heads=('2:1', 'flat'), z0=0.25, center=(-2.0, 0, 0))])
    P(m, 'cartridge_prefilter', 'Cartridge Pre-Filter (≈ 5 µm, protects the elements)', 'filter_media', cf, explode=(-0.3, 0, 0), ref='nf_prefilter', section='keep')
    _pump(m, 'hp_pump', 'High-Pressure Feed Pump (multistage)', -1.4, 0.0, 0.3, 'nf_pump', explode=(0, -0.4, -0.2))
    fr = [box(f'r{k}', (L + 0.6, 0.05, 0.05), (X0 + L / 2, s * 0.3, z), 'paint_grey') for k, (s, z) in enumerate(((-1, 0.45), (1, 0.45), (-1, 1.15), (1, 1.15)))]
    fr += [box(f'p{k}', (0.05, 0.05, 1.2), (x, s * 0.3, 0.6), 'paint_grey') for k, (x, s) in enumerate(((X0 - 0.25, -1), (X0 - 0.25, 1), (X0 + L + 0.25, -1), (X0 + L + 0.25, 1)))]
    P(m, 'rack', 'Pressure-Vessel Rack', 'structure', fr, explode=(0, 0, -0.3), ref='nf_vessels', section='keep')
    add_tracers(m, 'feed_tracers', 'Feed flowing along the Element Spacers', [(X0, 0.06, 0.6), (X0 + L, 0.06, 0.6), (X0 + L + 0.15, 0.06, 0.8), (X0 - 0.2, 0.06, 0.8), (X0 - 0.2, 0.06, 1.0), (X0 + L, 0.06, 1.0)], n=12, radius=0.012, mat='flow_discharge')
    m.flow('feed', [(-2.0, 0, 0.8), (-1.6, 0, 0.3), (X0 - 0.15, 0, 0.3), (X0 - 0.15, -0.15, 0.6), (X0 + L, -0.15, 0.6)], 'flow_suction', 0.015, 0.3)
    m.flow('concentrate', [(X0 + L, 0, 1.0), (X0 + L + 0.35, 0, 1.0), (X0 + L + 0.35, 0, 0.2)], 'flow_discharge', 0.015, 0.3)
    m.flow('permeate', [(X0 + L, 0.4, 1.25), (X0 - 0.4, 0.4, 1.25)], 'water', 0.015, 0.3)
    _press(m, [cyl(f'pp{k}', R + 0.035, X0, X0 + L, f'pressure_{lev}', 48, axis='X', center=(0, y, z), r_in=R + 0.02) for k, ((y, z), lev) in enumerate(zip(pv, (8, 8, 7)))],
           'Feed pressure overcomes osmotic pressure', 'Nanofiltration needs a feed pressure of roughly 5–20 bar (between UF and reverse osmosis). Water and most monovalent ions pass; divalent '
           'ions (hardness, sulphate) and organics above ~ 200–1000 Da are largely rejected. Pressure falls slightly along each vessel; stage 2 treats the stage 1 concentrate to raise recovery.')
    return m.export(out)


# =============================================================== EQ-258 Disc stack centrifuge
def disc_stack_centrifuge(out):
    m = _model('disc_stack_centrifuge', 'Disc Stack Centrifuge (Self-Cleaning Separator)')
    ZB = 1.0
    fr = join('fr', [csg('fh', [cyl('fho', 0.55, 0.0, ZB - 0.05, 'paint_grey', 64)], [cyl('fhi', 0.5, 0.1, ZB, 'paint_grey', 64)], 'paint_grey'),
                     csg('ch', [cyl('cho', 0.6, ZB - 0.05, ZB + 0.75, 'stainless', 64)], [cyl('chi', 0.56, ZB - 0.1, ZB + 0.7, 'stainless', 64)], 'stainless'),
                     cyl('chc', 0.6, ZB + 0.7, ZB + 0.75, 'stainless', 64)])
    P(m, 'frame_hood', 'Frame (with solids collector) & Hood', 'casing', fr, explode=(0, 0.6, 0), ref='ds_frame')
    bowl = lathe('bw', [(0.06, ZB), (0.3, ZB), (0.45, ZB + 0.2), (0.45, ZB + 0.3), (0.22, ZB + 0.6), (0.08, ZB + 0.62), (0.08, ZB + 0.6), (0.2, ZB + 0.58), (0.42, ZB + 0.29),
                             (0.42, ZB + 0.21), (0.28, ZB + 0.03), (0.06, ZB + 0.03)], 'stainless', 64)
    discs = [lathe(f'dk{k}', [(0.09, ZB + 0.12 + 0.025 * k), (0.32, ZB + 0.27 + 0.025 * k), (0.32, ZB + 0.275 + 0.025 * k), (0.09, ZB + 0.125 + 0.025 * k)], 'steel', 48) for k in range(10)]
    dist = lathe('dt', [(0.04, ZB + 0.05), (0.09, ZB + 0.08), (0.09, ZB + 0.5), (0.04, ZB + 0.5)], 'stainless', 32)
    P(m, 'bowl', 'Bowl with Disc Stack & Distributor (rotates ≈ 4 000–10 000 rpm)', 'rotating_element', [bowl, dist] + discs, explode=(0, -0.8, 0.2), ref='ds_bowl', section='split', pivot=(0, 0, ZB))
    lr = [cyl('lr', 0.24, ZB + 0.6, ZB + 0.64, 'steel_dark', 48, r_in=0.08)] + [rotate(box(f'lg{k}', (0.06, 0.03, 0.05), (0.24, 0, ZB + 0.62), 'steel_dark'), TAU * k / 6, 'Z') for k in range(6)]
    lr += [rotate(box(f'nz{k}', (0.03, 0.03, 0.03), (0.46, 0, ZB + 0.25), 'steel_dark'), TAU * k / 10, 'Z') for k in range(10)]
    plr = P(m, 'lock_ring_nozzles', 'Bowl Lock Ring & Discharge Ports (turn with the bowl)', 'rotating_element', lr, explode=(0, -0.8, 0.5), ref='ds_bowl', section='keep', pivot=(0, 0, ZB))
    plr.spin('Z', 10)
    sp = join('sp', [cyl('spd', 0.05, 0.2, ZB, 'steel', 24), cyl('bh', 0.12, 0.4, 0.55, 'steel_dark', 32)])
    psp = P(m, 'spindle', 'Vertical Spindle & Bearings (with damping springs)', 'rotating_element', sp, explode=(0, -0.5, -0.3), ref='ds_spindle', section='keep', pivot=(0, 0, ZB))
    psp.spin('Z', 10)
    mt = join('mt', [cyl('mtb', 0.18, 0.6, 1.1, 'paint_motor', 32, center=(0.9, 0, 0), ch=0.01), box('mtf', (0.4, 0.4, 0.05), (0.9, 0, 0.58), 'paint_grey')])
    P(m, 'motor', 'Drive Motor (flat-belt or direct drive)', 'drive', mt, explode=(0.5, 0, 0), ref='ds_drive', section='keep')
    fp = [cyl('fp', 0.03, ZB + 0.3, ZB + 1.1, 'stainless', 16), cyl('lo', 0.04, 0.6, 0.9, 'stainless', 16, axis='X', center=(0, 0, ZB + 0.6)), cyl('ho', 0.03, 0.6, 0.9, 'stainless', 16, axis='X', center=(0, 0.15, ZB + 0.5))]
    P(m, 'inlet_outlets', 'Feed Pipe, Light-Phase & Heavy-Phase Outlets (paring discs)', 'nozzles', fp, explode=(0, 0, 0.5), ref='ds_outlets', section='keep')
    pej = m.part('solids_ejection', 'Solids Ejected Intermittently from the Bowl Periphery', 'flow_tracers', explode=(0, 0, 0), info={'ref': 'flow_tracers'})
    for i in range(10):
        a = TAU * i / 10
        ms = pej.add(lathe(f'ej{i}', [(0.02 * math.sin(k * math.pi / 6), -0.02 * math.cos(k * math.pi / 6)) for k in range(7)], 'ore', 10), smooth_angle=80)
        lk, sk = [], []
        for f in range(OPERATE_FRAMES + 1):
            t = f / OPERATE_FRAMES
            u = min(1.0, max(0.0, (t - 0.6) / 0.15))
            rr = 0.45 + 0.08 * u
            lk.append((1 + f, (rr * math.cos(a), rr * math.sin(a), ZB + 0.25 - 0.2 * u)))
            v = 1.0 if 0.6 <= t <= 0.8 else 0.0
            sk.append((1 + f, (v, v, v)))
        ms.location = lk[0][1]
        m.keyframes(ms, 'Operate', 'location', lk)
        m.keyframes(ms, 'Operate', 'scale', sk)
    add_tracers(m, 'liquid', 'Light Phase rising inward through the Discs', [(0.0, 0.03, ZB + 1.1), (0.0, 0.03, ZB + 0.08), (0.2, 0.05, ZB + 0.15), (0.12, 0.05, ZB + 0.4), (0.08, 0.05, ZB + 0.6), (0.7, 0.05, ZB + 0.6)], n=10, radius=0.012, mat='water')
    m.flow('feed', [(0, 0.0, ZB + 1.2), (0, 0.0, ZB + 0.08)], 'flow_suction', 0.015, 0.2)
    m.flow('light_phase', [(0.15, 0.05, ZB + 0.3), (0.1, 0.05, ZB + 0.6), (0.9, 0.0, ZB + 0.6)], 'water', 0.015, 0.2)
    m.flow('solids', [(0.45, 0.05, ZB + 0.25), (0.53, 0.05, ZB + 0.1), (0.4, 0.05, 0.2)], 'sand', 0.015, 0.2, active=[(0.6, 0.85)])
    _press(m, [lathe('gz', [(0.32, ZB + 0.21), (0.44, ZB + 0.21), (0.44, ZB + 0.3), (0.32, ZB + 0.3)], 'pressure_9', 64)],
           'Centrifugal force: thousands of g', 'At a few thousand rpm the bowl generates several thousand times gravity (g-force = ω²r/g). Heavier solids and liquid move outwards to the bowl '
           'wall (red, the sludge space); the discs split the flow into thin layers so particles only have a short distance to settle. Accumulated solids are ejected periodically by opening the bowl.')
    return m.export(out)


# =============================================================== EQ-259 Decanter centrifuge
def decanter_centrifuge(out):
    m = _model('decanter_centrifuge', 'Decanter Centrifuge (Solid-Bowl, Scroll Discharge)')
    CZ, X0, XC, X1, R, r1 = 0.9, -0.8, 0.3, 0.9, 0.25, 0.11
    cs = csg('cs', [box('cso', (2.2, 0.8, 0.8), (0.05, 0, CZ), 'stainless')], [box('csi', (2.1, 0.7, 0.7), (0.05, 0, CZ), 'stainless')], 'stainless')
    cs = join('csj', [cs, box('chs', (0.3, 0.6, 0.4), (X1 + 0.05, 0, CZ - 0.55), 'stainless'), box('chl', (0.3, 0.6, 0.4), (X0 + 0.05, 0, CZ - 0.55), 'stainless')])
    P(m, 'casing', 'Casing with Solids Chute (cone end) & Centrate Chute (cylinder end)', 'casing', cs, explode=(0, 0.6, 0), ref='dc_casing')
    bowl = lathe('bw', [(R, X0), (R, XC), (r1, X1), (r1 + 0.02, X1), (R + 0.02, XC), (R + 0.02, X0)], 'stainless', 64, axis='X', center=(0, 0, CZ))
    ends = [cyl('be', R + 0.02, X0 - 0.03, X0, 'stainless', 64, axis='X', center=(0, 0, CZ), r_in=0.15)] + [cyl(f'wp{k}', 0.03, X0 - 0.05, X0, 'paint_orange', 12, axis='X', center=(0, 0.18 * math.cos(TAU * k / 4), CZ + 0.18 * math.sin(TAU * k / 4))) for k in range(4)]
    P(m, 'bowl', 'Cylindro-Conical Bowl (rotates ≈ 2 000–4 000 rpm)', 'rotating_element', bowl, explode=(0, -0.7, 0.3), ref='dc_bowl', section='split', pivot=(0, 0, CZ))
    pe_ = P(m, 'bowl_head_weirs', 'Bowl Head with Adjustable Weir Plates (turns with the bowl)', 'rotating_element', ends, explode=(-0.3, -0.7, 0.3), ref='dc_bowl', section='keep', pivot=(0, 0, CZ))
    pe_.spin('X', 6)
    hub = cyl('hub', 0.08, X0 + 0.02, X1 - 0.05, 'steel', 32, axis='X', center=(0, 0, CZ))
    pts = []
    for k in range(161):
        x = X0 + 0.05 + (X1 - X0 - 0.1) * k / 160
        rr = R - 0.03 if x < XC else (R - 0.03) - (R - r1) * (x - XC) / (X1 - XC)
        a = TAU * 6 * k / 160
        pts.append((x, rr * math.cos(a), CZ + rr * math.sin(a)))
    fl = sweep_tube('fl', pts, 0.018, 'steel_dark', 6)
    ps = P(m, 'scroll', 'Scroll Conveyor (turns slightly slower than the bowl — differential speed)', 'rotating_element', [hub, fl], explode=(0, -1.2, 0.3), ref='dc_scroll', section='keep', pivot=(0, 0, CZ))
    ps.spin('X', 5.6)
    gb = join('gb', [cyl('gbx', 0.18, X0 - 0.45, X0 - 0.15, 'paint_blue', 48, axis='X', center=(0, 0, CZ)), cyl('bd', 0.08, X0 - 0.75, X0 - 0.45, 'paint_motor', 24, axis='X', center=(0, 0, CZ))])
    P(m, 'gearbox_backdrive', 'Planetary Gearbox & Back-Drive (sets differential speed)', 'drive', gb, explode=(-0.5, 0, 0), ref='dc_gearbox', section='keep')
    fr = join('fr', [box('bs', (2.6, 0.9, 0.12), (0.05, 0, 0.06), 'paint_grey'), box(f'pb0', (0.2, 0.3, CZ - 0.12), (X0 - 0.1, 0, (CZ + 0.12) / 2), 'paint_grey'), box('pb1', (0.2, 0.3, CZ - 0.12), (X1 + 0.3, 0, (CZ + 0.12) / 2), 'paint_grey'),
                     cyl('mm', 0.16, 0.3, 0.9, 'paint_motor', 32, axis='X', center=(0, -0.55, 0.3)), box('bg', (0.15, 0.08, 0.9), (X1 + 0.35, -0.45, 0.6), 'paint_yellow')])
    P(m, 'frame_motor', 'Base Frame, Main Bearings, Main Motor & Belt Guard', 'structure', fr, explode=(0, 0, -0.3), ref='dc_frame', section='keep')
    pl = P(m, 'liquid_pool', 'Liquid Pool against the Bowl Wall', 'fluid', half(lathe('lp', [(R - 0.09, X0 + 0.02), (R - 0.005, X0 + 0.02), (R - 0.005, XC), (R - 0.09, XC + 0.25)], 'water', 48, axis='X', center=(0, 0, CZ)), 'water'),
           explode=(0, -0.4, 0), ref='dc_bowl', section='keep')
    rocks_along(m, 'solids', 'Solids Conveyed by the Scroll up the Beach to the Cone Outlet', [(X0 + 0.2, CZ - R + 0.03), (XC, CZ - R + 0.03), (X1 - 0.05, CZ - r1 - 0.01), (X1 + 0.05, CZ - 0.5)], 10, r=0.025, mat='coal', y=0.06)
    m.flow('feed', [(X1 + 0.5, 0, CZ), (X0 + 0.3, 0, CZ)], 'flow_suction', 0.015, 0.3)
    m.flow('centrate', [(X0 + 0.2, 0.06, CZ - 0.2), (X0 - 0.03, 0.06, CZ - 0.18), (X0 + 0.05, 0, CZ - 0.75)], 'water', 0.015, 0.2)
    m.flow('cake', [(X1 - 0.05, 0.06, CZ - 0.13), (X1 + 0.05, 0, CZ - 0.75)], 'sand', 0.015, 0.2)
    _press(m, [half(lathe('gz', [(R + 0.03, X0), (R + 0.05, X0), (R + 0.05, XC), (R + 0.03, XC)], 'pressure_8', 64, axis='X', center=(0, 0, CZ)), 'pressure_8')],
           'High g-force settles solids against the bowl', 'Rotating at a few thousand rpm, the bowl creates ~ 2 000–4 000 g. Solids settle on the bowl wall; the scroll, turning a few rpm slower or faster '
           '(differential speed), pushes them up the conical beach out of the liquid and out of the bowl. Clarified liquid overflows the adjustable weir plates at the other end.')
    return m.export(out)


# =============================================================== EQ-260 Basket centrifuge
def basket_centrifuge(out):
    m = _model('basket_centrifuge', 'Vertical Perforated-Basket Centrifuge (Filtering, Plough Discharge)')
    ZB, R = 0.6, 0.45
    cs = join('cs', [csg('cso', [cyl('co', R + 0.18, 0.2, ZB + 0.75, 'stainless', 64)], [cyl('ci', R + 0.14, 0.25, ZB + 0.8, 'stainless', 64)], 'stainless'),
                     csg('lid', [cyl('lo', R + 0.18, ZB + 0.75, ZB + 0.8, 'stainless', 64)], [cyl('lh', 0.2, ZB + 0.7, ZB + 0.85, 'stainless', 32)], 'stainless'), nozzle('fo', (0, -R - 0.18, 0.3), (0, -1, 0), 0.05, 0.2)])
    P(m, 'casing', 'Casing, Lid & Filtrate Outlet', 'casing', cs, explode=(0, 0.6, 0), ref='bc_casing')
    bk = [cyl('bs', R, ZB, ZB + 0.6, 'stainless', 64, r_in=R - 0.01), cyl('bb', R, ZB - 0.02, ZB, 'stainless', 64, r_in=0.12), cyl('lp', R, ZB + 0.58, ZB + 0.62, 'stainless', 64, r_in=R - 0.08)]
    bk += [cyl(f'hl{i}_{j}', 0.012, R - 0.012, R + 0.003, 'steel_dark', 6, axis='X', center=(0, 0, ZB + 0.08 + 0.09 * j)) for i in range(1) for j in range(6)]
    bk += [rotate(cyl(f'hr{i}_{j}', 0.01, R - 0.012, R + 0.003, 'steel_dark', 6, axis='X', center=(0, 0, ZB + 0.08 + 0.09 * j)), TAU * i / 16, 'Z') for i in range(1, 16) for j in range(6)]
    bk += [cyl('cl', R - 0.01, ZB + 0.01, ZB + 0.58, 'polypropylene', 64, r_in=R - 0.016)]
    P(m, 'basket', 'Perforated Basket with Filter Cloth (rotates)', 'rotating_element', bk, explode=(0, -0.7, 0.3), ref='bc_basket', section='split', pivot=(0, 0, ZB))
    hub = [cyl('hb', 0.13, ZB - 0.06, ZB + 0.02, 'steel_dark', 32)] + [rotate(box(f'sk{k}', (0.3, 0.03, 0.03), (0.25, 0, ZB - 0.04), 'steel_dark'), TAU * k / 6, 'Z') for k in range(6)]
    phb = P(m, 'basket_hub', 'Basket Hub & Spokes (turn with the basket)', 'rotating_element', hub, explode=(0, -0.5, -0.2), ref='bc_basket', section='keep', pivot=(0, 0, ZB))
    phb.spin('Z', 6)
    ck = lathe('ck', [(R - 0.11, ZB + 0.02), (R - 0.016, ZB + 0.02), (R - 0.016, ZB + 0.56), (R - 0.11, ZB + 0.56)], 'powder', 64, a0=0.0, a1=math.pi, cap_mat='powder')
    P(m, 'cake', 'Filter Cake building on the Cloth', 'fluid', ck, explode=(0, -0.4, 0.2), ref='bc_cake', section='keep')
    dr = join('dr', [cyl('sh', 0.05, 0.1, ZB, 'steel', 24), cyl('mt', 0.18, -0.4, 0.1, 'paint_motor', 48, ch=0.01), box('bp', (1.2, 1.2, 0.08), (0, 0, 0.16), 'paint_grey')])
    P(m, 'drive', 'Bottom Drive (motor, shaft, bearings) & Base', 'drive', dr, explode=(0, 0, -0.4), ref='bc_drive', section='keep')
    pl = join('pl', [cyl('pla', 0.03, ZB + 0.3, ZB + 1.0, 'steel', 16, center=(0.25, 0.1, 0)), box('plb', (0.04, 0.1, 0.5), (0.3, 0.1, ZB + 0.3), 'steel')])
    ppl = P(m, 'plough', 'Discharge Plough (scrapes the cake at low speed)', 'discharge', pl, explode=(0, 0, 0.6), ref='bc_plough', section='keep', pivot=(0.25, 0.1, ZB + 0.7))
    keys_loop(m, ppl, lambda t: (0.08 * smooth_pulse(t, 0.2, 0.3, 0.2), 0, 0))
    P(m, 'feed_pipe', 'Feed Pipe', 'nozzles', cyl('fp', 0.03, ZB + 0.3, ZB + 1.2, 'stainless', 16, center=(-0.1, 0, 0)), explode=(0, 0, 0.5), ref='bc_casing', section='keep')
    pdr = m.part('filtrate_spray', 'Filtrate flung out through the Cloth and Perforations', 'flow_tracers', explode=(0, 0, 0), info={'ref': 'flow_tracers'})
    for i in range(12):
        a, z = TAU * i / 12, ZB + 0.1 + 0.04 * (i % 10)
        ms = pdr.add(cyl(f'fd{i}', 0.01, -0.01, 0.01, 'water', 8), smooth_angle=60)
        keys = [(1 + f, ((R - 0.05 + 0.2 * (((f / OPERATE_FRAMES) * 3 + i * 0.13) % 1)) * math.cos(a), (R - 0.05 + 0.2 * (((f / OPERATE_FRAMES) * 3 + i * 0.13) % 1)) * math.sin(a), z)) for f in range(OPERATE_FRAMES + 1)]
        ms.location = keys[0][1]
        m.keyframes(ms, 'Operate', 'location', keys)
    m.flow('feed', [(-0.1, 0, ZB + 1.3), (-0.1, 0, ZB + 0.3), (R - 0.12, 0.05, ZB + 0.3)], 'flow_suction', 0.015, 0.2)
    m.flow('filtrate', [(R + 0.02, 0.05, ZB + 0.3), (R + 0.1, 0.05, 0.4), (0, -R - 0.38, 0.3)], 'water', 0.015, 0.2)
    _press(m, [cyl('gz', R + 0.06, ZB, ZB + 0.6, 'pressure_7', 64, r_in=R + 0.04)], 'Centrifugal pressure drives filtration',
           'Spinning at several hundred to ~ 1 500 rpm, the basket throws the slurry against the cloth (hundreds of g). The liquid is forced through the cake and cloth while solids '
           'build up as a cake; the cake can be washed and spun dry, then ploughed out at low speed.')
    return m.export(out)


# =============================================================== EQ-261 Magnetic separator (wet drum)
def magnetic_separator(out):
    m = _model('magnetic_separator', 'Wet Drum Magnetic Separator (Concurrent Tank)')
    CZ, R, W = 0.95, 0.42, 0.9
    tk = csg('tk', [box('to', (1.4, W + 0.1, 0.9), (0, 0, 0.7), 'paint_blue')], [box('ti', (1.3, W, 0.9), (0, 0, 0.8), 'paint_blue'), cyl('tc', R + 0.08, -W, W, 'paint_blue', 64, axis='Y', center=(0, 0, CZ))], 'paint_blue')
    tk = join('tkj', [tk, box('fb', (0.35, W, 0.35), (-0.75, 0, CZ + 0.2), 'paint_blue'), box('cl', (0.4, W, 0.08), (0.75, 0, CZ + 0.15), 'stainless')])
    P(m, 'tank', 'Tank, Feed Box & Concentrate Launder', 'casing', tk, explode=(0, 0.6, 0), ref='ms_tank')
    sl = csg('sw', [box('swb', (1.28, W / 2 - 0.01, CZ + 0.1 - 0.3), (0, W / 4, (CZ + 0.1 + 0.3) / 2), 'water')], [cyl('swd', R + 0.005, -W, W, 'water', 64, axis='Y', center=(0, 0, CZ)),
             csg('swo', [box('swx', (2, 2, 2), (0, 0, CZ), 'water')], [cyl('swc', R + 0.075, -W, W, 'water', 64, axis='Y', center=(0, 0, CZ)), box('swf', (0.35, 2, 1.0), (-0.75, 0, CZ - 0.2), 'water')], 'water')], 'water')
    pw = P(m, 'slurry', 'Slurry in the Tank', 'fluid', sl, explode=(0, -0.3, 0), ref='ms_tank', section='keep')
    dr = [cyl('ds', R, -W / 2, W / 2, 'stainless', 64, axis='Y', center=(0, 0, CZ), r_in=R - 0.01), cyl('dsh', 0.04, -W / 2 - 0.3, W / 2 + 0.2, 'steel', 16, axis='Y', center=(0, 0, CZ))]
    dr += [cyl(f'de{s}', R, y, y + 0.01, 'stainless', 64, axis='Y', center=(0, 0, CZ), r_in=0.04) for s, y in enumerate((-W / 2, W / 2 - 0.01))]
    P(m, 'drum', 'Rotating Non-Magnetic Stainless Drum', 'rotating_element', dr, explode=(0, -0.7, 0.4), ref='ms_drum', section='split', pivot=(0, 0, CZ))
    st = [rotate(box(f'ws{k}', (0.02, W - 0.02, 0.012), (0, 0, CZ + R + 0.006), 'rubber'), TAU * k / 12, 'Y', (0, 0, CZ)) for k in range(12)]
    pst = P(m, 'drum_strips', 'Drum Wear Strips (show the drum rotation)', 'rotating_element', st, explode=(0, -0.9, 0.4), ref='ms_drum', section='keep', pivot=(0, 0, CZ))
    pst.spin('Y', -1)
    mg = []
    for k in range(6):
        a0 = math.radians(150 - 30 * k - 28)            # rotate(-90° about X) maps lathe angle a to −a in the XZ plane
        seg = lathe(f'mg{k}', [(R - 0.11, -W / 2 + 0.03), (R - 0.02, -W / 2 + 0.03), (R - 0.02, W / 2 - 0.03), (R - 0.11, W / 2 - 0.03)], 'magnet_n' if k % 2 else 'magnet_s', 16, a0=a0, a1=a0 + math.radians(28), cap_mat='magnet_n' if k % 2 else 'magnet_s')
        seg = rotate(seg, -math.pi / 2, 'X')
        seg.data.transform(Matrix.Translation((0, 0, CZ)))
        mg.append(seg)
    P(m, 'magnet_assembly', 'Stationary Permanent-Magnet Arc (alternating poles, ~ 120° wrap)', 'magnets', mg, explode=(0, -0.4, 0.2), ref='ms_magnet', section='keep')
    drv = join('drv', [box('gb', (0.25, 0.2, 0.25), (0, W / 2 + 0.35, CZ), 'paint_blue_dark'), cyl('mt', 0.1, W / 2 + 0.45, W / 2 + 0.8, 'paint_motor', 24, axis='Y', center=(0, 0, CZ))])
    P(m, 'drive', 'Drum Drive (gearmotor)', 'drive', drv, explode=(0, 0.5, 0), ref='ms_drive', section='keep')
    nz = [nozzle('tl', (0.2, 0, 0.25), (0, 0, -1), 0.06, 0.2), nozzle('co', (0.9, 0, CZ + 0.1), (1, 0, 0), 0.05, 0.2)]
    P(m, 'outlets', 'Tailings (non-magnetic) Outlet & Concentrate Outlet', 'nozzles', nz, explode=(0, 0, -0.3), ref='ms_tank', section='keep')
    pm = m.part('magnetics', 'Magnetic Particles held on the Drum and carried to the Launder', 'flow_tracers', explode=(0, 0, 0), info={'ref': 'flow_tracers'})
    for i in range(10):
        ph = i / 10
        ms = pm.add(lathe(f'mp{i}', [(0.015 * math.sin(k * math.pi / 6), -0.015 * math.cos(k * math.pi / 6)) for k in range(7)], 'steel_dark', 10), smooth_angle=80)
        keys = []
        for f in range(OPERATE_FRAMES + 1):
            s = ((f / OPERATE_FRAMES) + ph) % 1.0
            if s < 0.75:
                a = math.radians(-160 + 220 * s / 0.75)
                pos = ((R + 0.015) * math.cos(a), 0.1, CZ + (R + 0.015) * math.sin(a))
            else:
                u = (s - 0.75) / 0.25
                a = math.radians(60)
                pos = ((R + 0.015) * math.cos(a) + 0.3 * u, 0.1, CZ + (R + 0.015) * math.sin(a) - 0.1 * u)
            keys.append((1 + f, pos))
        ms.location = keys[0][1]
        m.keyframes(ms, 'Operate', 'location', keys)
    rocks_along(m, 'non_magnetics', 'Non-Magnetic Particles passing to Tailings', [(-0.75, CZ + 0.1), (-0.4, CZ - R - 0.03), (0.2, CZ - R - 0.05), (0.2, 0.2)], 8, r=0.015, mat='sand', y=0.2)
    m.flow('feed', [(-0.75, 0, CZ + 0.45), (-0.75, 0, CZ), (-0.3, 0, CZ - R - 0.04), (0.2, 0, CZ - R - 0.05), (0.2, 0, 0.0)], 'flow_suction', 0.015, 0.3)
    m.flow('concentrate', [(0.2, 0.15, CZ + R), (0.75, 0.15, CZ + 0.2), (1.1, 0, CZ + 0.1)], 'flow_discharge', 0.015, 0.2)
    m.overlay('magnetic_field', join('mf', [rotate(lathe(f'fl{k}', [(R + 0.01, -0.03), (R + 0.05 + 0.02 * k, -0.03), (R + 0.05 + 0.02 * k, 0.03), (R + 0.01, 0.03)], 'magnet_n', 24, a0=math.radians(-30), a1=math.radians(150), cap_mat='magnet_n'), -math.pi / 2, 'X') for k in range(2)]),
              'Magnetic field round the lower drum', 'The stationary magnet arc creates a strong field (typically ~ 0.1–0.3 T at the drum surface for magnetite recovery) only over the lower part of the drum. '
              'Magnetic particles are pulled onto the rotating shell, carried out of the slurry and released where the field ends; non-magnetic particles stay in the slurry and leave as tailings.')
    return m.export(out)


# ===================================================================== metadata
def _std(*items):
    return [{'id': i, 'title': t, 'relevance': r, 'edition': 'to be verified'} for i, t, r in items]


def _c(fn, cons, mat, op='—', fm=('—',), insp=('Visual',)):
    return C(fn, cons, mat, op, list(fm), list(insp))


_FV = _std(('ASME BPVC VIII-1', 'Pressure vessels', 'Housings and vessels.'),)
_MEM = _std(('ASTM D4516', 'Standardizing RO performance data', 'Normalisation of membrane performance (also applied to NF).'), ('ASME BPVC X', 'FRP pressure vessels', 'Membrane pressure vessels.'))
_CEN = _std(('EN 12547', 'Centrifuges — common safety requirements', 'Machine safety.'), ('API 610 / maker standards', 'Rotating equipment practice', 'Bearings, vibration (to be verified for centrifuges).'))

META = {
    'cartridge_filter': {'summary': ('A cartridge filter removes fine particles from liquids or gases. The fluid flows from outside to inside through pleated filter cartridges mounted on a tube sheet; '
                                     'particles are trapped on the media and clean fluid flows down the cores to the outlet. Cartridges are replaced when the differential pressure reaches its limit.'),
                         'classification': {'family': 'Filter', 'type': 'Multi-cartridge housing (outside-in)'}, 'model_configuration': {'cartridges': 7, 'animation': 'Dirt captured; filtrate flows'},
                         'standards': _FV, 'references': ['Sutherland — Filters and Filtration Handbook'],
                         'components': {'cf_housing': _c('Pressure envelope.', 'Vessel with body flange.', 'Stainless steel.'), 'cf_cover': _c('Access for cartridge change.', 'Bolted cover with vent.', 'Stainless steel.', 'Depressurise before opening.'),
                                        'cf_tubesheet': _c('Holds cartridges; separates dirty and clean sides.', 'Seat plate.', 'Stainless steel.', '—', ['Seal bypass'], ['Inspect O-rings']),
                                        'cf_cartridges': _c('Capture particles.', 'Pleated media on perforated cores.', 'PP/PES/glass fibre.', 'Rated 0.1–100 µm.', ['Blinding, collapse'], ['ΔP']),
                                        'cf_dp': _c('Connections and ΔP indication.', 'Nozzles, ΔP gauge.', 'Steel.')}},
    'membrane_filter': {'summary': ('A plate-and-frame membrane filter stacks flat-sheet membranes between support plates. Feed under pressure sweeps across the membrane surfaces (cross-flow); '
                                    'permeate passes through and drains from each plate, while the concentrated retentate leaves at the end. A hydraulic cylinder clamps the stack.'),
                        'classification': {'family': 'Membrane filter', 'type': 'Plate-and-frame flat-sheet module'}, 'model_configuration': {'plates': 9, 'animation': 'Cross-flow tracers; permeate drips'},
                        'standards': _MEM, 'references': ['Baker — Membrane Technology and Applications'],
                        'components': {'mf_frame': _c('Holds plates; feed/retentate ports.', 'Fixed head, stand, side bars.', 'Steel.'), 'mf_plates': _c('Support membranes; form flow channels.', 'Plates, flat-sheet membranes, spacers.', 'PP / polymer membranes.', '—', ['Fouling, leaks'], ['Integrity test']),
                                       'mf_closure': _c('Clamps the stack.', 'Follower plate and hydraulic cylinder.', 'Steel.'), 'mf_permeate': _c('Collect permeate.', 'Outlets and trough.', 'PP/stainless.')}},
    'microfiltration_system': {'summary': ('A submerged hollow-fibre microfiltration system immerses bundles of porous fibres in the feed tank. A permeate pump applies a gentle suction so clean water passes into the fibres '
                                           'while particles and bacteria stay outside. Air bubbles from diffusers scour the fibres to limit fouling.'),
                               'classification': {'family': 'Membrane system', 'type': 'Submerged hollow-fibre MF (e.g. MBR)'}, 'model_configuration': {'animation': 'Air scour bubbles; permeate pump'},
                               'standards': _MEM, 'references': ['Judd — The MBR Book'],
                               'components': {'mfs_tank': _c('Holds the feed and the cassettes.', 'Tank.', 'Concrete/steel.'), 'mfs_fibres': _c('Separate solids from water.', 'Hollow fibres potted in headers.', 'PVDF/PES.', 'TMP ~ 0.1–0.5 bar.', ['Fouling, fibre breakage'], ['Integrity (pressure decay) test']),
                                              'mfs_air': _c('Scour fibres.', 'Blower, diffusers.', '—'), 'mfs_permeate': _c('Draw permeate.', 'Header, line, pump.', 'Stainless.')}},
    'ultrafiltration_system': {'summary': ('An ultrafiltration system pumps water through pressurised modules of hollow fibres with very fine pores. Water and dissolved salts pass; suspended solids, colloids, bacteria and viruses '
                                           'are retained. Frequent short backwashes with filtrate restore performance.'),
                               'classification': {'family': 'Membrane system', 'type': 'Pressurised hollow-fibre UF skid'}, 'model_configuration': {'modules': 4, 'animation': 'Filtration then backwash'},
                               'standards': _MEM, 'references': ['AWWA M53 — Microfiltration and Ultrafiltration Membranes for Drinking Water'],
                               'components': {'uf_modules': _c('House the fibres.', 'Pressure housings.', 'PVC/FRP.'), 'uf_fibres': _c('Filtration barrier.', 'Hollow fibres.', 'PVDF/PES.', '—', ['Fouling, breakage'], ['Pressure decay test']),
                                              'uf_headers': _c('Distribute flows.', 'Headers and strainer.', 'PVC/stainless.'), 'uf_pumps': _c('Feed and backwash.', 'Pumps.', '—'), 'uf_tank': _c('Filtrate/backwash/CIP storage.', 'Tank.', 'PE.')}},
    'nanofiltration_system': {'summary': ('A nanofiltration unit forces feed water at moderate pressure through spiral-wound membrane elements. NF removes hardness, sulphate, colour and many organics while letting most monovalent salts pass. '
                                          'Elements sit in pressure vessels arranged in stages to raise recovery.'),
                              'classification': {'family': 'Membrane system', 'type': 'Spiral-wound NF, 2:1 array'}, 'model_configuration': {'vessels': 3, 'animation': 'Feed tracers through stages'},
                              'standards': _MEM, 'references': ['Membrane manufacturer design guides (e.g. DuPont FilmTec)'],
                              'components': {'nf_vessels': _c('Contain elements under pressure.', 'FRP pressure vessels.', 'FRP.'), 'nf_elements': _c('Separate solutes.', 'Spiral-wound polyamide elements.', 'Polyamide TFC.', '≈ 5–20 bar.', ['Scaling, fouling'], ['Normalised flux/ΔP']),
                                             'nf_piping': _c('Manifolds and control.', 'Pipes, concentrate valve, gauges.', 'Stainless.'), 'nf_prefilter': _c('Protects elements.', 'Cartridge filter.', 'Stainless.'), 'nf_pump': _c('Provides feed pressure.', 'High-pressure pump.', 'Stainless.')}},
    'disc_stack_centrifuge': {'summary': ('A disc stack centrifuge separates liquids of different density and fine solids from liquids at very high g-force. A stack of conical discs inside the fast-spinning bowl splits the flow into thin '
                                          'layers, so particles settle a very short distance. Solids collect at the bowl wall and are ejected periodically.'),
                              'classification': {'family': 'Centrifuge', 'type': 'Self-cleaning disc stack separator'}, 'model_configuration': {'discs': 10, 'animation': 'Bowl spins; solids ejected'},
                              'standards': _CEN, 'references': ['Records & Sutherland — Decanter Centrifuge Handbook (centrifugation principles)'],
                              'components': {'ds_frame': _c('Supports and encloses.', 'Frame and hood.', 'Cast iron/stainless.'), 'ds_bowl': _c('Separates by centrifugal force.', 'Bowl, disc stack, distributor.', 'Duplex stainless.', 'High speed.', ['Corrosion, imbalance'], ['Vibration, NDT']),
                                             'ds_spindle': _c('Carries the bowl.', 'Spindle with bearings and springs.', 'Steel.'), 'ds_drive': _c('Drives the spindle.', 'Motor.', '—'), 'ds_outlets': _c('Feed and outlets.', 'Pipes, paring discs.', 'Stainless.')}},
    'decanter_centrifuge': {'summary': ('A decanter centrifuge continuously separates solids from liquid. The solid bowl spins at high speed so solids settle against its wall; a scroll conveyor turning at a slightly different speed pushes the '
                                        'settled solids up the conical beach to the solids outlet, while clarified liquid overflows weirs at the other end.'),
                            'classification': {'family': 'Centrifuge', 'type': 'Horizontal solid-bowl scroll decanter'}, 'model_configuration': {'animation': 'Bowl and scroll spin; solids conveyed'},
                            'standards': _CEN, 'references': ['Records & Sutherland — Decanter Centrifuge Handbook'],
                            'components': {'dc_casing': _c('Encloses the rotor; chutes.', 'Casing.', 'Stainless.'), 'dc_bowl': _c('Settles solids.', 'Cylindro-conical bowl with weirs.', 'Duplex stainless.', '—', ['Wear, imbalance'], ['Vibration']),
                                           'dc_scroll': _c('Conveys solids.', 'Scroll with hard-faced flights.', 'Stainless + tungsten carbide.', '—', ['Flight wear'], ['Inspect']),
                                           'dc_gearbox': _c('Creates differential speed.', 'Planetary gearbox, back-drive.', '—'), 'dc_frame': _c('Supports; drives.', 'Frame, bearings, motor.', 'Steel.')}},
    'basket_centrifuge': {'summary': ('A basket centrifuge filters slurries by spinning them in a perforated basket lined with filter cloth. Centrifugal force drives the liquid through the cake and cloth; solids build up as a cake, '
                                      'which can be washed, spun dry and ploughed out.'),
                          'classification': {'family': 'Centrifuge', 'type': 'Vertical perforated basket (batch)'}, 'model_configuration': {'animation': 'Basket spins; filtrate flung out'},
                          'standards': _CEN, 'references': ['Svarovsky — Solid-Liquid Separation'],
                          'components': {'bc_casing': _c('Encloses basket; collects filtrate.', 'Casing and lid.', 'Stainless.'), 'bc_basket': _c('Holds cake; filters.', 'Perforated basket with cloth.', 'Stainless.', '—', ['Cloth blinding, imbalance'], ['Vibration']),
                                         'bc_cake': _c('Filter cake.', '—', '—'), 'bc_drive': _c('Spins basket.', 'Bottom drive.', '—'), 'bc_plough': _c('Discharges cake.', 'Plough.', 'Steel.')}},
    'magnetic_separator': {'summary': ('A wet drum magnetic separator recovers magnetic particles (for example magnetite) from a slurry. A non-magnetic drum rotates around a stationary magnet arc; magnetic particles are attracted to the drum, '
                                       'carried out of the slurry and dropped into the concentrate launder, while non-magnetic material flows to tailings.'),
                           'classification': {'family': 'Magnetic separator', 'type': 'Wet drum, permanent magnet, concurrent tank'}, 'model_configuration': {'animation': 'Drum turns; magnetics carried over'},
                           'standards': _std(('Maker standards', 'Magnetic separator design', 'Field strength and wear liners.'),), 'references': ['Svoboda — Magnetic Techniques for the Treatment of Materials'],
                           'components': {'ms_tank': _c('Holds slurry; launder.', 'Tank and feed box.', 'Steel (lined).'), 'ms_drum': _c('Carries magnetic particles.', 'Stainless drum.', 'Stainless steel.', '—', ['Wear of shell'], ['Thickness']),
                                          'ms_magnet': _c('Creates the field.', 'Permanent magnet arc.', 'Ferrite/NdFeB.', '—', ['Demagnetisation (heat)'], ['Gauss check']), 'ms_drive': _c('Rotates drum.', 'Gearmotor.', '—')}},
}
BUILDERS = {k: globals()[k] for k in META}
