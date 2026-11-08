"""Static Equipment — EQ-180 … EQ-195: steam-system & storage vessels, separators, gas treatment, stack, silencer, gas holder, storage tanks."""
import math
from mathutils import Matrix, Vector
from pumpforge.core import Model, lathe, cyl, box, csg, split, join, rotate, extrude_poly, hex_prism, TAU, OPERATE_FRAMES
from pumpforge.valvekit import P, keys_loop, smooth_pulse, spring, sphere
from pumpforge.parts import add_tracers, hollow_pipe, pressure_gauge
from pumpforge.vesselkit import (half, vessel, liquid, liquid_v, animate_level, nozzle, saddles, legs, skirt, mesh_pad, packing, tray, helix_coil, ladder, platform, droplets)
from pumpforge.rotkit import ring_of, flow_ring
from pumpforge.shapes import sweep_tube, cone_arrow
from pumpforge.common_meta import C

CAT = '8 · Static Equipment – Additional Equipment'


def _model(pid, title):
    return Model(pid, title, CAT, META[pid])


def _hvessel(m, pid, name, R, L, X0, CZ, mat, ref, heads=('2:1', '2:1'), t=0.01, saddle=True, foot_z=0.0):
    v = vessel(pid, R, L, t, mat, axis='X', center=(0, 0, CZ), heads=heads, z0=X0)
    P(m, pid, name, 'vessel', v, explode=(0, 0, 0), ref=ref)
    if saddle:
        sd = saddles(pid + 'sd', (X0 + L * 0.2, X0 + L * 0.8), R, CZ, foot_z)
        P(m, 'saddles', 'Saddle Supports (one fixed, one sliding)', 'structure', sd, explode=(0, 0, -0.3), ref='sv_saddles', section='keep')


def _hliquid(m, pid, name, R, L, X0, CZ, z_level, ref, mat='water', dz=None, fn=None):
    lq = liquid(pid, R, X0 - R * 0.45, z_level, mat=mat, axis='X', L=L + R * 0.9, zt=CZ)
    lq = csg(pid + 'c', [lq], [vessel(pid + 'm', R + 0.3, L, 0.3, mat, axis='X', center=(0, 0, CZ), z0=X0)], mat)
    p = P(m, pid, name, 'fluid', lq, explode=(0, -0.3, 0), ref=ref, section='keep')
    if dz:
        animate_level(m, p, z_level - 0.01, dz, fn)
    return p


# =============================================================== EQ-180 Deaerator
def deaerator(out):
    m = _model('deaerator', 'Deaerator (Spray-Tray Type) on Feedwater Storage Tank')
    R, L, X0, CZ = 0.55, 2.4, -1.2, 0.85
    _hvessel(m, 'storage_tank', 'Feedwater Storage Tank', R, L, X0, CZ, 'paint_grey', 'da_tank')
    _hliquid(m, 'water', 'Deaerated Feedwater', R - 0.01, L, X0, CZ, CZ + 0.15, 'da_water', dz=0.1, fn=lambda t: 0.5 + 0.5 * math.sin(TAU * t))
    HR, HZ0, HL = 0.32, CZ + R - 0.05, 1.0
    hd = vessel('hd', HR, HL, 0.008, 'paint_grey', z0=HZ0 + 0.2, center=(-0.5, 0, 0))
    neck = cyl('nk', 0.2, CZ + R * 0.6, HZ0 + 0.25, 'paint_grey', 48, center=(-0.5, 0, 0), r_in=0.19)
    P(m, 'deaerator_head', 'Deaerator Head (vertical) & Downcomer Neck', 'vessel', [hd, neck], explode=(0, 0, 0.5), ref='da_head')
    trays = [tray(f'tr{k}', HR - 0.02, HZ0 + 0.45 + 0.13 * k, holes=True, weir=False, dc_side=1 if k % 2 else -1) for k in range(4)]
    for t_ in trays:
        t_.data.transform(Matrix.Translation((-0.5, 0, 0)))
    sp = [join(f'sv{i}', [cyl(f'svb{i}', 0.025, HZ0 + 1.05, HZ0 + 1.12, 'stainless', 16, center=(-0.5 + 0.12 * (i - 1), 0.0, 0)), spring(f'svs{i}', (-0.5 + 0.12 * (i - 1), 0, 0), 0.015, HZ0 + 1.12, HZ0 + 1.18, 0.003, 4)]) for i in range(3)]
    P(m, 'trays', 'Deaerating Trays', 'internals', trays, explode=(0, 0.6, 0.5), ref='da_trays', section='keep')
    P(m, 'spray_valves', 'Spray Valves (atomise incoming water)', 'internals', sp, explode=(0, -0.5, 0.8), ref='da_spray', section='keep')
    noz = [nozzle('wi', (-0.5 + HR, 0, HZ0 + 1.1), (1, 0, 0), 0.04, 0.3), nozzle('vent', (-0.5, 0, HZ0 + 1.2 + HR / 2 - 0.02), (0, 0, 1), 0.02, 0.25),
           nozzle('st', (-0.5 - HR, 0, HZ0 + 0.35), (-1, 0, 0), 0.06, 0.3), nozzle('fo', (0.6, 0, CZ - R), (0, 0, -1), 0.06, 0.25),
           nozzle('ov', (0.9, 0, CZ + 0.2), (0, 0, 1) if False else (1, 0, 0), 0.03, 0.1)]
    gl = join('lg', [cyl('lgg', 0.02, CZ - R * 0.6, CZ + R * 0.6, 'glass', 16, center=(X0 + L - 0.15, -R - 0.08, 0)),
                     cyl('lgu', 0.01, X0 + L - 0.2, X0 + L - 0.15, 'steel', 8, axis='X', center=(0, -R - 0.08, CZ + R * 0.6))])
    P(m, 'nozzles', 'Water Inlet, Steam Inlet, Vent, Feedwater Outlet & Level Gauge', 'nozzles', noz + [gl], explode=(0, 0, 0.4), ref='da_nozzles', section='keep')
    droplets(m, 'spray', 'Water Spray & Cascade (tracers)', -0.5 - 0.2, -0.5 + 0.2, HZ0 + 1.0, HZ0 + 0.3, n=10, mat='water', y=0.04, r=0.014)
    m.flow('steam', [(-0.5 - HR - 0.3, 0, HZ0 + 0.35), (-0.5 - 0.1, 0.05, HZ0 + 0.35), (-0.5, 0.05, HZ0 + 0.6), (-0.5, 0.05, HZ0 + 1.0), (-0.5, 0, HZ0 + 1.45)], 'steam', 0.01, 0.2)
    m.flow('feedwater', [(-0.5 + HR + 0.3, 0, HZ0 + 1.1), (-0.5, 0.02, HZ0 + 1.08), (-0.45, 0.02, HZ0 + 0.3), (-0.5, 0.02, CZ + 0.1), (0.6, 0.02, CZ - 0.2), (0.6, 0, CZ - R - 0.25)], 'water', 0.009, 0.2)
    return m.export(out)


# =============================================================== EQ-181 Boiler feedwater tank
def boiler_feedwater_tank(out):
    m = _model('boiler_feedwater_tank', 'Boiler Feedwater Tank (Horizontal, Atmospheric/Low Pressure)')
    R, L, X0, CZ = 0.6, 2.4, -1.2, 0.8
    _hvessel(m, 'tank', 'Tank Shell & Dished Heads', R, L, X0, CZ, 'paint_blue', 'fw_tank')
    _hliquid(m, 'water', 'Feedwater (level rises and falls with make-up/demand)', R - 0.01, L, X0, CZ, CZ + 0.1, 'fw_water', dz=0.25, fn=lambda t: 0.5 + 0.5 * math.sin(TAU * t))
    noz = [nozzle('mu', (X0 + 0.4, 0, CZ + R), (0, 0, 1), 0.04, 0.2), nozzle('cr', (X0 + 1.0, 0, CZ + R), (0, 0, 1), 0.05, 0.2), nozzle('vt', (X0 + 1.6, 0, CZ + R), (0, 0, 1), 0.03, 0.25),
           nozzle('mh', (X0 + 2.0, 0, CZ + R - 0.02), (0, 0, 1), 0.2, 0.12), nozzle('so', (X0 + 1.9, 0, CZ - R), (0, 0, -1), 0.06, 0.25),
           nozzle('ov', (X0 + L + R * 0.45, 0, CZ + 0.35), (1, 0, 0), 0.04, 0.15), nozzle('dr', (X0 + 0.3, 0, CZ - R), (0, 0, -1), 0.025, 0.15)]
    lg = join('lg', [cyl('lgg', 0.02, CZ - R * 0.7, CZ + R * 0.7, 'glass', 16, center=(X0 + 0.6, -R - 0.1, 0))] +
              [cyl(f'lgc{s}', 0.012, -R - 0.1, -R * 0.9, 'steel', 8, axis='Y', center=(X0 + 0.6, 0, CZ + s * R * 0.7)) for s in (-1, 1)])
    P(m, 'nozzles', 'Make-up, Condensate Return, Vent, Manway, Pump Suction, Overflow, Drain & Level Gauge', 'nozzles', noz + [lg], explode=(0, 0, 0.4), ref='fw_nozzles', section='keep')
    coil, cp = helix_coil('sc', 0.1, 0, 0, 1, 0.012) if False else (sweep_tube('spg', [(X0 + 0.2, 0, CZ - R * 0.6), (X0 + L - 0.2, 0, CZ - R * 0.6)], 0.018, 'stainless', 10), None)
    P(m, 'steam_sparger', 'Steam Sparger (pre-heating / deaeration assist)', 'internals', coil, explode=(0, 0.4, 0), ref='fw_sparger', section='keep')
    m.flow('makeup', [(X0 + 0.4, 0, CZ + R + 0.3), (X0 + 0.4, 0.02, CZ + 0.05), (X0 + 1.9, 0.02, CZ - 0.2), (X0 + 1.9, 0, CZ - R - 0.3)], 'water', 0.01, 0.25)
    m.flow('condensate_return', [(X0 + 1.0, 0, CZ + R + 0.3), (X0 + 1.0, 0.02, CZ + 0.05)], 'flow_discharge', 0.009, 0.15)
    return m.export(out)


# =============================================================== EQ-182 Hotwell
def hotwell(out):
    m = _model('hotwell', 'Condenser Hotwell (Surface Condenser Lower Section)')
    W, Lh, Z0 = 1.2, 2.0, 0.0
    shell = csg('cs', [box('co', (Lh, W, 1.0), (0, 0, 1.25), 'paint_grey', bevel=0.02)], [box('ci', (Lh - 0.04, W - 0.04, 0.96), (0, 0, 1.25), 'paint_grey'), box('cio', (Lh - 0.3, W - 0.3, 0.2), (0, 0, 0.75), 'paint_grey')], 'paint_grey')
    P(m, 'condenser_shell', 'Condenser Shell (lower part) — exhaust steam from turbine above', 'vessel', shell, explode=(0, 0, 0.5), ref='hw_shell')
    tubes = [cyl(f't{i}{j}', 0.012, -Lh / 2 + 0.02, Lh / 2 - 0.02, 'copper', 10, axis='X', center=(0, -W / 2 + 0.12 + j * 0.08, 1.05 + i * 0.08)) for i in range(6) for j in range(13)]
    tsh = [box(f'ts{s}', (0.03, W - 0.04, 1.0), (s * (Lh / 2 - 0.03), 0, 1.25), 'paint_grey') for s in (-1, 1)]
    P(m, 'tube_bundle', 'Cooling-Water Tube Bundle & Tube Sheets', 'tubes', tubes + tsh, explode=(0, 0.6, 0.6), ref='hw_tubes', section='keep')
    hw = csg('hw', [box('ho', (Lh - 0.2, W - 0.2, 0.6), (0, 0, 0.45), 'paint_grey', bevel=0.02)], [box('hi', (Lh - 0.24, W - 0.24, 0.62), (0, 0, 0.47), 'paint_grey')], 'paint_grey')
    P(m, 'hotwell_box', 'Hotwell (condensate collection box)', 'vessel', hw, explode=(0, 0, -0.3), ref='hw_box')
    lq = csg('lq', [box('lqb', (Lh - 0.25, (W - 0.25) / 2, 0.35), (0, (W - 0.25) / 4, 0.33), 'water')], [], 'water') if False else box('lqb', (Lh - 0.25, (W - 0.25) / 2, 0.35), (0, (W - 0.25) / 4, 0.33), 'water')
    pl = P(m, 'condensate', 'Condensate (level held by the level controller)', 'fluid', lq, explode=(0, -0.4, 0), ref='hw_condensate', section='keep')
    animate_level(m, pl, 0.3, 0.08, lambda t: 0.5 + 0.5 * math.sin(TAU * t))
    noz = [nozzle('co', (0.5, 0, 0.15), (0, 0, -1), 0.07, 0.15), hollow_pipe('cep', [(0.5, 0, 0.0), (0.5, 0, -0.05), (1.4, 0, -0.05)], 0.07, 'steel', 24, bend=0.08, t=0.006),
           join('lt', [cyl('ltb', 0.03, 0.2, 0.8, 'steel', 16, center=(-Lh / 2 + 0.05, -W / 2 - 0.05, 0)), box('ltx', (0.08, 0.06, 0.1), (-Lh / 2 + 0.05, -W / 2 - 0.1, 0.85), 'paint_blue')]),
           nozzle('cwi', (-Lh / 2, -0.25, 1.15), (-1, 0, 0), 0.12, 0.2), nozzle('cwo', (-Lh / 2, 0.25, 1.4), (-1, 0, 0), 0.12, 0.2),
           nozzle('ar', (Lh / 2 - 0.2, W / 2, 1.6), (0, 1, 0), 0.04, 0.15), nozzle('mk', (-0.6, 0, 1.75), (0, 0, 1), 0.04, 0.12)]
    P(m, 'connections', 'Condensate Outlet to CEP, Level Transmitter, CW Inlet/Outlet, Air Extraction & Make-up', 'nozzles', noz, explode=(0, 0, -0.3), ref='hw_connections', section='keep')
    droplets(m, 'drops', 'Condensate Droplets (from tubes)', -0.7, 0.7, 1.0, 0.5, n=10, mat='water', y=0.1, r=0.014)
    m.flow('exhaust_steam', [(0.0, 0.1, 1.9), (0.0, 0.1, 1.45), (-0.3, 0.1, 1.2)], 'steam', 0.014, 0.2)
    m.flow('condensate_out', [(0.0, 0.1, 0.4), (0.5, 0.05, 0.3), (0.5, 0, -0.05), (1.45, 0, -0.05)], 'water', 0.012, 0.2)
    m.flow('cooling_water', [(-Lh / 2 - 0.3, -0.25, 1.15), (Lh / 2 - 0.1, -0.25, 1.15), (Lh / 2 - 0.1, 0.25, 1.4), (-Lh / 2 - 0.3, 0.25, 1.4)], 'flow_suction', 0.012, 0.3)
    return m.export(out)


# =============================================================== EQ-183 Surge vessel
def surge_vessel(out):
    m = _model('surge_vessel', 'Surge Vessel (Air-Cushion Type) for Water-Hammer Protection')
    R, L, Z0 = 0.5, 1.6, 0.6
    v = vessel('v', R, L, 0.012, 'paint_blue', z0=Z0)
    P(m, 'vessel', 'Surge Vessel (pressure vessel)', 'vessel', v, explode=(0, 0, 0), ref='sg_vessel')
    sk = legs('lg', R * 0.85, 0.0, Z0, 4)
    P(m, 'supports', 'Support Legs', 'structure', sk, explode=(0, 0, -0.3), ref='sg_supports', section='keep')
    lq = liquid_v('lq', R - 0.012, Z0, Z0 + L * 0.55)
    pl = P(m, 'water', 'Water (level oscillates during a surge)', 'fluid', lq, explode=(0, -0.4, 0), ref='sg_water', section='keep')
    animate_level(m, pl, Z0 + 0.3, 0.35, lambda t: 0.5 + 0.5 * math.sin(TAU * 2 * t) * math.exp(-1.5 * t) if t < 0.95 else 0.5)
    air = liquid('air', R - 0.02, Z0 + L * 0.62, Z0 + L + 0.1, mat='glass')
    P(m, 'air_cushion', 'Compressed Air Cushion (expands/compresses to absorb surges)', 'fluid', air, explode=(0, 0, 0.6), ref='sg_air', section='keep')
    noz = [hollow_pipe('mn', [(0, 0, Z0 - R / 2 - 0.0), (0, 0, 0.2), (1.2, 0, 0.2)], 0.1, 'paint_grey', 32, bend=0.12, t=0.008),
           hollow_pipe('mm', [(-1.2, 0, 0.2), (1.6, 0, 0.2)], 0.12, 'paint_grey', 32, t=0.008),
           join('lg', [cyl('lgg', 0.02, Z0 + 0.1, Z0 + L - 0.1, 'glass', 16, center=(0, -R - 0.08, 0))] + [cyl(f'lgc{s}', 0.012, -R - 0.08, -R + 0.01, 'steel', 8, axis='Y', center=(0, 0, z)) for s, z in ((0, Z0 + 0.1), (1, Z0 + L - 0.1))]),
           nozzle('ac', (0.2, 0, Z0 + L + R / 2 - 0.05), (0, 0, 1), 0.02, 0.3), join('psv', [cyl('pv', 0.03, Z0 + L + R / 2, Z0 + L + R / 2 + 0.25, 'brass', 16, center=(-0.2, 0, 0))]),
           pressure_gauge('pg', (0.0, -R * 0.4, Z0 + L + R / 2 + 0.1), r=0.05, facing=(0, -1, 0))]
    P(m, 'connections', 'Connection to Pipeline, Level Gauge, Air Make-up, Safety Valve & Gauge', 'nozzles', noz, explode=(0, 0, 0.3), ref='sg_connections', section='keep')
    comp = box('cp', (0.4, 0.3, 0.3), (1.0, -0.6, 0.15), 'paint_motor', bevel=0.02)
    P(m, 'air_compressor', 'Air Compressor (maintains air volume)', 'auxiliary', comp, explode=(0.3, -0.3, 0), ref='sg_compressor', section='keep')
    m.flow('pipeline', [(-1.3, 0, 0.2), (1.7, 0, 0.2)], 'water', 0.02, 0.3)
    m.flow('surge_in_out', [(0.3, 0, 0.2), (0, 0, 0.3), (0, 0, Z0 + 0.3)], 'flow_discharge', 0.014, 0.15, active=[(0.0, 0.25), (0.5, 0.75)])
    return m.export(out)


# =============================================================== separators (KO drum, 2-phase, 3-phase)
def knockout_drum(out):
    m = _model('knockout_drum', 'Flare Knockout Drum (Horizontal, Liquid Removal)')
    R, L, X0, CZ = 0.7, 3.0, -1.5, 0.95
    _hvessel(m, 'drum', 'Knockout Drum Shell', R, L, X0, CZ, 'paint_grey', 'ko_drum')
    _hliquid(m, 'liquid', 'Collected Liquid (hydrocarbon condensate)', R - 0.01, L, X0, CZ, CZ - 0.25, 'ko_liquid', mat='hydraulic_oil', dz=0.15, fn=lambda t: t)
    inl = [nozzle('in', (X0 + 0.4, 0, CZ + R), (0, 0, 1), 0.12, 0.3), box('dv', (0.4, 0.5, 0.02), (X0 + 0.4, 0, CZ + 0.3), 'stainless')]
    noz = [nozzle('out', (X0 + L - 0.4, 0, CZ + R), (0, 0, 1), 0.14, 0.3), nozzle('po', (X0 + L / 2, 0, CZ - R), (0, 0, -1), 0.05, 0.2),
           join('lt', [cyl('ltb', 0.03, CZ - R * 0.8, CZ + 0.1, 'steel', 16, center=(X0 + L / 2, -R - 0.12, 0)), box('ltx', (0.08, 0.06, 0.1), (X0 + L / 2, -R - 0.17, CZ + 0.15), 'paint_blue')]),
           cyl('vb', 0.12, CZ - R + 0.01, CZ - R + 0.05, 'stainless', 32, center=(X0 + L / 2, 0, 0))]
    P(m, 'inlet', 'Inlet Nozzle with Impingement / Diverter Plate', 'internals', inl, explode=(0, 0, 0.4), ref='ko_inlet', section='keep')
    P(m, 'nozzles', 'Vapour Outlet to Flare, Liquid Pump-Out, Level Transmitter & Vortex Breaker', 'nozzles', noz, explode=(0, 0, 0.4), ref='ko_nozzles', section='keep')
    droplets(m, 'drops', 'Liquid Droplets Settling (tracers)', X0 + 0.5, X0 + L - 0.6, CZ + 0.45, CZ - 0.2, n=12, mat='hydraulic_oil', y=0.05, r=0.016)
    m.flow('vapour', [(X0 + 0.4, 0, CZ + R + 0.3), (X0 + 0.4, 0, CZ + 0.35), (X0 + 0.8, 0.05, CZ + 0.2), (X0 + L - 0.6, 0.05, CZ + 0.3), (X0 + L - 0.4, 0, CZ + R + 0.3)], 'air', 0.014, 0.3,
           speed=[1.5, 1.5, 0.5, 0.4, 1.2])
    m.flow('liquid_out', [(X0 + L / 2, 0.05, CZ - 0.3), (X0 + L / 2, 0, CZ - R - 0.2)], 'hydraulic_oil', 0.012, 0.15)
    return m.export(out)


def gas_liquid_separator(out):
    m = _model('gas_liquid_separator', 'Vertical Gas–Liquid (Two-Phase) Separator')
    R, L, Z0 = 0.45, 2.2, 0.7
    v = vessel('v', R, L, 0.012, 'paint_grey', z0=Z0)
    P(m, 'vessel', 'Separator Vessel', 'vessel', v, explode=(0, 0, 0), ref='gl_vessel')
    P(m, 'skirt', 'Support Legs', 'structure', legs('lg', R * 0.9, 0.0, Z0, 4), explode=(0, 0, -0.3), ref='gl_supports', section='keep')
    lq = liquid_v('lq', R - 0.012, Z0, Z0 + 0.55)
    pl = P(m, 'liquid', 'Liquid Section (level controlled)', 'fluid', lq, explode=(0, -0.4, 0), ref='gl_liquid', section='keep')
    animate_level(m, pl, Z0 + 0.3, 0.12, lambda t: 0.5 + 0.5 * math.sin(TAU * t))
    inl = [nozzle('in', (R, 0, Z0 + 1.2), (1, 0, 0), 0.08, 0.3), join('dv', [lathe('dvp', [(0.12, Z0 + 1.1), (0.13, Z0 + 1.1), (0.13, Z0 + 1.32), (0.12, Z0 + 1.32)], 'stainless', 32, a0=-1.2, a1=1.2, center=(R - 0.15, 0, 0))])]
    P(m, 'inlet_diverter', 'Inlet Nozzle & Half-Pipe Diverter (momentum breaker)', 'internals', inl, explode=(0.4, 0, 0), ref='gl_inlet', section='keep')
    P(m, 'mist_eliminator', 'Wire-Mesh Mist Eliminator (demister pad)', 'internals', half(mesh_pad('mp', R - 0.015, Z0 + L - 0.25, Z0 + L - 0.1), 'foam'), explode=(0, 0, 0.5), ref='gl_mesh', section='keep')
    noz = [nozzle('go', (0, 0, Z0 + L + R / 2 - 0.02), (0, 0, 1), 0.07, 0.3), nozzle('lo', (0, 0, Z0 - R / 2 - 0.01), (0, 0, -1), 0.05, 0.2),
           join('vb', [box('vb1', (0.24, 0.01, 0.1), (0, 0, Z0 - R / 2 + 0.08), 'stainless'), box('vb2', (0.01, 0.24, 0.1), (0, 0, Z0 - R / 2 + 0.08), 'stainless')]),
           join('lc', [cyl('lcb', 0.04, Z0 + 0.1, Z0 + 0.9, 'steel', 16, center=(-R - 0.12, 0, 0)), box('lcx', (0.1, 0.08, 0.12), (-R - 0.12, -0.05, Z0 + 0.95), 'paint_blue')]),
           join('cv', [cyl('cvb', 0.05, -0.05, 0.05, 'paint_blue', 24, axis='Y', center=(0.4, 0, 0.15)), cyl('cva', 0.07, 0.2, 0.32, 'paint_grey', 24, center=(0.4, 0, 0))]),
           hollow_pipe('lp', [(0, 0, Z0 - R / 2 - 0.2), (0, 0, 0.15), (0.9, 0, 0.15)], 0.04, 'steel', 16, bend=0.05, t=0.004)]
    P(m, 'nozzles', 'Gas Outlet, Liquid Outlet, Vortex Breaker, Level Controller & Control Valve', 'nozzles', noz, explode=(0, 0, 0.4), ref='gl_nozzles', section='keep')
    droplets(m, 'drops', 'Droplets Settling by Gravity (tracers)', -0.25, 0.25, Z0 + 1.15, Z0 + 0.6, n=8, mat='water', y=0.06, r=0.014)
    m.flow('gas', [(R + 0.3, 0, Z0 + 1.2), (R - 0.1, 0, Z0 + 1.2), (0.0, 0.05, Z0 + 1.5), (0.0, 0.05, Z0 + L - 0.1), (0, 0, Z0 + L + R / 2 + 0.3)], 'air', 0.012, 0.25, speed=[1.5, 1, 0.5, 0.5, 1.3])
    m.flow('liquid', [(0.0, 0.05, Z0 + 0.5), (0, 0, Z0 - R / 2 - 0.2), (0, 0, 0.15), (0.95, 0, 0.15)], 'water', 0.01, 0.2)
    return m.export(out)


def three_phase_separator(out):
    m = _model('three_phase_separator', 'Horizontal Three-Phase Separator (Gas / Oil / Water) with Weir')
    R, L, X0, CZ = 0.65, 3.4, -1.7, 0.95
    _hvessel(m, 'vessel', 'Separator Vessel', R, L, X0, CZ, 'paint_grey', 'tp_vessel')
    xw = X0 + L * 0.72
    water = csg('wtr', [liquid('w0', R - 0.012, X0 - R * 0.45, CZ - 0.25, axis='X', L=xw - X0 + R * 0.45, zt=CZ)], [vessel('wm', R + 0.3, L, 0.3, 'water', axis='X', center=(0, 0, CZ), z0=X0)], 'water')
    oil = csg('oil', [liquid('o0', R - 0.012, X0 - R * 0.45, CZ + 0.15, axis='X', L=xw - X0 + R * 0.45, zt=CZ)],
              [vessel('om', R + 0.3, L, 0.3, 'hydraulic_oil', axis='X', center=(0, 0, CZ), z0=X0), box('ow', (L * 2, 2 * R, 0.4 + 0.0), (X0, 0, CZ - 0.25 - 0.2 + 0.0), 'hydraulic_oil')], 'hydraulic_oil')
    oil2 = csg('oil2', [liquid('o1', R - 0.012, xw + 0.02, CZ - 0.05, axis='X', L=0.5, zt=CZ)], [box('ob', (1, 2 * R, 1), (xw + 0.27, 0, CZ - 0.6 - 0.25), 'hydraulic_oil')], 'hydraulic_oil')
    pw = P(m, 'water_layer', 'Free Water Layer (heaviest, at the bottom)', 'fluid', water, explode=(0, -0.4, -0.2), ref='tp_water', section='keep')
    po = P(m, 'oil_layer', 'Oil Layer (floats on water, spills over the weir)', 'fluid', [oil, oil2], explode=(0, -0.4, 0), ref='tp_oil', section='keep')
    weir = box('weir', (0.02, 2 * R * 0.95, 0.75), (xw, 0, CZ - R + 0.375 + 0.03), 'stainless')
    inl = [nozzle('in', (X0 + 0.3, 0, CZ + R), (0, 0, 1), 0.1, 0.3), box('dv', (0.02, 0.6, 0.5), (X0 + 0.45, 0, CZ + 0.15), 'stainless')]
    P(m, 'internals', 'Inlet Diverter & Oil Weir', 'internals', inl + [weir], explode=(0, 0.6, 0.2), ref='tp_internals', section='keep')
    P(m, 'mist_eliminator', 'Vane-Pack / Mesh Mist Eliminator', 'internals', box('me', (0.12, 2 * R * 0.7, 0.3), (X0 + L - 0.45, 0, CZ + R * 0.5), 'foam'), explode=(0, 0, 0.5), ref='tp_mesh', section='keep')
    noz = [nozzle('go', (X0 + L - 0.25, 0, CZ + R), (0, 0, 1), 0.08, 0.3), nozzle('oo', (xw + 0.3, 0, CZ - R), (0, 0, -1), 0.05, 0.25),
           nozzle('wo', (xw - 0.4, 0, CZ - R), (0, 0, -1), 0.05, 0.25), nozzle('sd', (X0 + 1.0, 0, CZ - R), (0, 0, -1), 0.04, 0.2)]
    P(m, 'nozzles', 'Gas, Oil and Water Outlets & Sand Drain', 'nozzles', noz, explode=(0, 0, 0.4), ref='tp_nozzles', section='keep')
    droplets(m, 'wdrops', 'Water Droplets Falling Out of the Oil', X0 + 0.7, xw - 0.3, CZ + 0.1, CZ - 0.3, n=8, mat='water', y=0.07, r=0.013)
    m.flow('well_fluid', [(X0 + 0.3, 0, CZ + R + 0.3), (X0 + 0.3, 0, CZ + 0.15), (X0 + 0.6, 0.05, CZ + 0.0)], 'flow_discharge', 0.014, 0.2)
    m.flow('gas', [(X0 + 0.5, 0.05, CZ + 0.45), (X0 + L - 0.4, 0.05, CZ + 0.45), (X0 + L - 0.25, 0, CZ + R + 0.3)], 'air', 0.012, 0.3)
    m.flow('oil', [(X0 + 0.8, 0.05, CZ + 0.05), (xw - 0.05, 0.05, CZ + 0.12), (xw + 0.1, 0.05, CZ - 0.1), (xw + 0.3, 0, CZ - R - 0.25)], 'hydraulic_oil', 0.011, 0.25)
    m.flow('water', [(X0 + 0.8, 0.05, CZ - 0.4), (xw - 0.4, 0.05, CZ - 0.45), (xw - 0.4, 0, CZ - R - 0.25)], 'water', 0.011, 0.25)
    return m.export(out)


# =============================================================== EQ-187 Scrubber, EQ-188 Demister
def scrubber_vessel(out):
    m = _model('scrubber_vessel', 'Packed Wet Scrubber (Counter-Current, Recirculated Liquor)')
    R, L, Z0 = 0.5, 2.6, 0.9
    v = vessel('v', R, L, 0.01, 'polypropylene', heads=('flat', '2:1'), z0=Z0)
    P(m, 'vessel', 'Scrubber Tower (FRP/PP)', 'vessel', v, explode=(0, 0, 0), ref='sc_vessel')
    sump = liquid('sp', R - 0.012, Z0 + 0.01, Z0 + 0.35)
    P(m, 'sump', 'Liquor Sump', 'fluid', sump, explode=(0, -0.4, 0), ref='sc_sump', section='keep')
    pk = packing('pk', R - 0.012, Z0 + 0.8, Z0 + 1.8)
    sg = cyl('sg', R - 0.012, Z0 + 0.76, Z0 + 0.8, 'steel_dark', 64)
    P(m, 'packing', 'Random Packing Bed on Support Grid (gas–liquid contact area)', 'internals', [half(pk, 'polypropylene'), half(sg, 'steel_dark')], explode=(0, -0.6, 0), ref='sc_packing', section='keep')
    sph = [sweep_tube('hdr', [(-R * 0.8, 0, Z0 + 2.0), (R * 0.8, 0, Z0 + 2.0)], 0.02, 'polypropylene', 10)] + \
          [cyl(f'nz{i}', 0.015, Z0 + 1.96, Z0 + 2.0, 'brass', 12, center=(x, 0, 0)) for i, x in enumerate((-0.3, -0.1, 0.1, 0.3))]
    P(m, 'spray_header', 'Liquid Distributor / Spray Header', 'internals', sph, explode=(0, 0.6, 0.3), ref='sc_spray', section='keep')
    P(m, 'mist_eliminator', 'Mist Eliminator (chevron/mesh)', 'internals', half(mesh_pad('me', R - 0.012, Z0 + 2.25, Z0 + 2.38), 'foam'), explode=(0, 0, 0.5), ref='sc_mist', section='keep')
    noz = [nozzle('gi', (R, 0, Z0 + 0.55), (1, 0, 0), 0.15, 0.3), nozzle('go', (0, 0, Z0 + L + R / 2 - 0.02), (0, 0, 1), 0.14, 0.3),
           hollow_pipe('rc', [(-R, 0, Z0 + 0.1), (-R - 0.4, 0, Z0 + 0.1), (-R - 0.4, 0, Z0 + 2.0), (-R * 0.8, 0, Z0 + 2.0)], 0.03, 'polypropylene', 16, bend=0.05, t=0.004)]
    P(m, 'nozzles', 'Gas Inlet, Gas Outlet & Recirculation Line', 'nozzles', noz, explode=(0, 0, 0.3), ref='sc_nozzles', section='keep')
    pump = join('pm', [cyl('pc', 0.12, -R - 0.52, -R - 0.28, 'paint_blue', 32, axis='X', center=(0, 0, Z0 + 0.1)) if False else box('pc', (0.25, 0.2, 0.2), (-R - 0.4, 0, Z0 - 0.1), 'paint_blue', bevel=0.02),
                       cyl('mt', 0.09, -R - 0.4 + 0.0, -R - 0.4 + 0.0, 'paint_motor', 24) if False else box('mt', (0.2, 0.2, 0.2), (-R - 0.4, 0.3, Z0 - 0.1), 'paint_motor', bevel=0.02)])
    P(m, 'recirculation_pump', 'Recirculation Pump', 'auxiliary', pump, explode=(-0.3, 0, 0), ref='sc_pump', section='keep')
    P(m, 'supports', 'Base', 'structure', box('bs', (1.6, 1.4, Z0), (-0.2, 0, Z0 / 2), 'cast_iron'), explode=(0, 0, -0.3), ref='sc_supports', section='keep')
    droplets(m, 'liquor', 'Scrubbing Liquor Trickling Down (tracers)', -0.35, 0.35, Z0 + 1.95, Z0 + 0.4, n=10, mat='water', y=0.06, r=0.014)
    m.flow('gas', [(R + 0.3, 0, Z0 + 0.55), (0.0, 0.05, Z0 + 0.6), (0.0, 0.05, Z0 + 2.2), (0, 0, Z0 + L + R / 2 + 0.3)], 'flue_gas', 0.016, 0.3)
    m.flow('liquor', [(-R, 0, Z0 + 0.1), (-R - 0.4, 0, Z0 + 0.1), (-R - 0.4, 0, Z0 + 2.0), (0, 0, Z0 + 2.0), (0, 0.06, Z0 + 0.4)], 'water', 0.01, 0.25)
    return m.export(out)


def demister_vessel(out):
    m = _model('demister_vessel', 'Demister Vessel (Mesh Pad + Vane Pack Mist Eliminator)')
    R, L, Z0 = 0.4, 1.8, 0.6
    v = vessel('v', R, L, 0.01, 'paint_grey', z0=Z0)
    P(m, 'vessel', 'Vessel', 'vessel', v, explode=(0, 0, 0), ref='dm_vessel')
    P(m, 'supports', 'Legs', 'structure', legs('lg', R * 0.9, 0.0, Z0, 4), explode=(0, 0, -0.3), ref='dm_supports', section='keep')
    P(m, 'mesh_pad', 'Knitted Wire-Mesh Pad (coalesces fine droplets)', 'internals', half(mesh_pad('mp', R - 0.012, Z0 + 1.2, Z0 + 1.35), 'foam'), explode=(0, 0.5, 0.3), ref='dm_mesh', section='keep')
    vanes = [rotate(box(f'vn{i}', (0.006, 1.8 * math.sqrt(max(0.0, (R - 0.03) ** 2 - (-R * 0.8 + R * 1.6 * i / 9) ** 2)), 0.18), (-R * 0.8 + R * 1.6 * i / 9, 0, Z0 + 1.55), 'stainless'), 0.5 * (1 if i % 2 else -1), 'Y', (-R * 0.8 + R * 1.6 * i / 9, 0, Z0 + 1.55)) for i in range(10)]
    P(m, 'vane_pack', 'Chevron Vane Pack (inertial separation)', 'internals', vanes, explode=(0, 0.5, 0.6), ref='dm_vanes', section='keep')
    lq = liquid_v('lq', R - 0.012, Z0, Z0 + 0.25)
    P(m, 'drained_liquid', 'Drained Liquid', 'fluid', lq, explode=(0, -0.4, 0), ref='dm_liquid', section='keep')
    noz = [nozzle('in', (R, 0, Z0 + 0.6), (1, 0, 0), 0.08, 0.25), nozzle('out', (0, 0, Z0 + L + R / 2 - 0.02), (0, 0, 1), 0.08, 0.25), nozzle('dr', (0, 0, Z0 - R / 2 - 0.01), (0, 0, -1), 0.03, 0.2),
           join('dp', [cyl('dpt', 0.008, Z0 + 1.0, Z0 + 1.7, 'steel', 8, center=(-R - 0.1, 0, 0)), box('dpx', (0.08, 0.06, 0.1), (-R - 0.1, -0.05, Z0 + 1.75), 'paint_blue')])]
    P(m, 'nozzles', 'Inlet, Clean-Gas Outlet, Drain & ΔP Transmitter', 'nozzles', noz, explode=(0, 0, 0.3), ref='dm_nozzles', section='keep')
    droplets(m, 'mist', 'Mist Droplets (captured and drained)', -0.25, 0.25, Z0 + 1.15, Z0 + 0.3, n=10, mat='water', y=0.06, r=0.01)
    m.flow('gas', [(R + 0.25, 0, Z0 + 0.6), (0.0, 0.05, Z0 + 0.7), (0.0, 0.05, Z0 + 1.8), (0, 0, Z0 + L + R / 2 + 0.25)], 'air', 0.012, 0.25)
    return m.export(out)


# =============================================================== EQ-189 Chimney / stack
def chimney_stack(out):
    m = _model('chimney_stack', 'Self-Supported Steel Chimney / Stack (lined, with helical strakes)')
    H, R = 6.0, 0.35
    sh = csg('sh', [lathe('so', [(R * 1.6, 0.0), (R * 1.6, 0.6), (R + 0.015, 1.4), (R + 0.015, H), (R, H), (R, 1.4), (R * 1.6 - 0.015, 0.6), (R * 1.6 - 0.015, 0.0)], 'paint_grey', 96)],
             [box('br', (0.6, 0.6, 0.6), (R * 1.5, 0, 0.75), 'paint_grey')], 'paint_grey')
    P(m, 'shell', 'Steel Shell (flared base for stability)', 'structure', sh, explode=(0, 0, 0), ref='ch_shell')
    lin = cyl('ln', R - 0.002, 1.4, H, 'insulation', 96, r_in=R - 0.04)
    P(m, 'lining', 'Internal Lining / Insulation (corrosion & heat protection)', 'insulation', lin, explode=(0, -0.6, 0), ref='ch_lining')
    st = []
    for k in range(3):
        pts = [((R + 0.06) * math.cos(TAU * k / 3 + TAU * 1.0 * i / 60), (R + 0.06) * math.sin(TAU * k / 3 + TAU * 1.0 * i / 60), H * 0.6 + H * 0.38 * i / 60) for i in range(61)]
        st.append(sweep_tube(f'sk{k}', pts, 0.02, 'paint_grey', 6))
    P(m, 'strakes', 'Helical Strakes (suppress wind-induced vortex shedding)', 'structure', st, explode=(0, 0.6, 0.0), ref='ch_strakes', section='keep')
    brc = join('brc', [csg('bro', [box('bo', (0.9, 0.62, 0.62), (R * 1.5 + 0.35, 0, 0.75), 'paint_grey')], [box('bi', (1.0, 0.56, 0.56), (R * 1.5 + 0.4, 0, 0.75), 'paint_grey')], 'paint_grey')])
    P(m, 'breeching', 'Breeching (flue-gas inlet duct)', 'structure', brc, explode=(0.5, 0, 0), ref='ch_breeching')
    plf = [platform('pf1', R + 0.02, R + 0.6, H * 0.55, a0=-1.2, a1=1.2), platform('pf2', R + 0.02, R + 0.6, H - 0.4, a0=-1.2, a1=1.2)]
    ld = ladder('ld', -(R + 0.25), 0, 0.0, H, facing='y')
    P(m, 'access', 'Platforms (sampling/inspection) & Caged Ladder', 'access', plf + [ld], explode=(0, 0.5, 0), ref='ch_access', section='keep')
    misc = [cyl('al', 0.05, H + 0.02, H + 0.1, 'paint_red', 16, center=(R * 0.7, 0, 0)), cyl('lr', 0.008, H, H + 0.6, 'copper', 8, center=(-R * 0.7, 0, 0)),
            nozzle('sp1', (R, 0, H * 0.55 + 0.2), (1, 0, 0), 0.04, 0.15), nozzle('sp2', (0, R, H * 0.55 + 0.2), (0, 1, 0), 0.04, 0.15),
            box('db', (0.4, 0.3, 0.3), (0, -R - 0.25, 0.4), 'paint_grey')]
    P(m, 'fittings', 'Aviation Light, Lightning Rod, Sampling Ports (CEMS) & Drain/Clean-out', 'fittings', misc, explode=(0, 0, 0.3), ref='ch_fittings', section='keep')
    fnd = cyl('fd', R * 2.6, -0.3, 0.0, 'cast_iron', 64)
    P(m, 'foundation', 'Foundation & Anchor Bolts', 'structure', fnd, explode=(0, 0, -0.3), ref='ch_foundation', section='keep')
    add_tracers(m, 'plume', 'Flue Gas / Plume (tracers)', [(R * 1.5 + 0.8, 0, 0.75), (0.0, 0.0, 0.8), (0, 0, H), (0.3, 0, H + 1.2), (0.9, 0, H + 1.8)], n=14, radius=0.05, mat='flue_gas', loops=2)
    m.flow('flue_gas', [(R * 1.5 + 0.8, 0, 0.75), (0.0, 0.0, 0.8), (0, 0, H), (0.3, 0, H + 1.0)], 'flue_gas', 0.04, 0.6)
    return m.export(out)


# =============================================================== EQ-190 Silencer
def silencer(out):
    m = _model('silencer', 'Combination (Reactive + Absorptive) Silencer for Gas/Steam Vent or Engine Exhaust')
    CZ, X0, X1, R = 0.55, -0.9, 0.9, 0.3
    sh = vessel('sh', R, X1 - X0, 0.006, 'paint_grey', axis='X', center=(0, 0, CZ), heads=('cone', 'cone'), z0=X0)
    sh = csg('shc', [sh], [cyl('hi', 0.08, X0 - 0.5, X0 + 0.01, 'paint_grey', 32, axis='X', center=(0, 0, CZ)), cyl('ho', 0.08, X1 - 0.01, X1 + 0.5, 'paint_grey', 32, axis='X', center=(0, 0, CZ))], 'paint_grey')
    P(m, 'shell', 'Silencer Shell with Inlet & Outlet Cones', 'casing', sh, explode=(0, 0, 0), ref='si_shell')
    bf = [cyl(f'bf{i}', R - 0.006, x - 0.004, x + 0.004, 'steel', 64, axis='X', center=(0, 0, CZ), r_in=0.0 if False else 0.0) for i, x in enumerate((-0.35, 0.35))]
    bf = [csg(f'bfh{i}', [b], [cyl(f'bh{i}', 0.08, -2, 2, 'steel', 24, axis='X', center=(0, 0.13 * (1 if i else -1), CZ))], 'steel') for i, b in enumerate(bf)]
    P(m, 'baffles', 'Reactive Baffles (expansion chambers reflect low-frequency sound)', 'internals', bf, explode=(0, 0.5, 0), ref='si_baffles', section='keep')
    pt = csg('pt', [cyl('pto', 0.085, -0.35, 0.35, 'steel', 48, axis='X', center=(0, 0, CZ))],
             [cyl('pti', 0.08, -0.4, 0.4, 'steel', 48, axis='X', center=(0, 0, CZ))] + [cyl(f'ph{i}{j}', 0.008, -0.1, 0.1, 'steel', 8, axis='Z', center=(-0.3 + 0.06 * i, 0, 0)) if False else
                                                                                       cyl(f'ph{i}{j}', 0.008, CZ - 0.1, CZ + 0.1, 'steel', 8, center=(-0.3 + 0.06 * i, 0.0, 0)) for i in range(11) for j in range(1)], 'steel')
    ab = cyl('ab', R - 0.01, -0.33, 0.33, 'foam', 64, axis='X', center=(0, 0, CZ), r_in=0.09)
    P(m, 'absorptive_section', 'Perforated Tube & Absorptive Packing (mineral wool) — high-frequency absorption', 'internals', [half(pt, 'steel'), half(ab, 'foam')], explode=(0, -0.5, 0), ref='si_absorptive', section='keep')
    fl = [nozzle('fi', (X0 - R * 1.0, 0, CZ), (-1, 0, 0), 0.08, 0.3), nozzle('fo', (X1 + R * 1.0, 0, CZ), (1, 0, 0), 0.08, 0.3)]
    P(m, 'connections', 'Inlet & Outlet Flanges', 'nozzles', fl, explode=(0, 0, 0.3), ref='si_connections', section='keep')
    P(m, 'supports', 'Supports', 'structure', saddles('sd', (X0 + 0.3, X1 - 0.3), R, CZ, 0.0), explode=(0, 0, -0.3), ref='si_supports', section='keep')
    waves = []
    for i, x in enumerate((-1.5, -1.1, -0.6, 0.0, 0.6, 1.1, 1.5)):
        amp = [1.0, 1.0, 0.7, 0.45, 0.25, 0.12, 0.1][i]
        waves.append(cyl(f'wv{i}', 0.09 + 0.25 * amp, x - 0.01, x + 0.01, 'pressure_%d' % int(2 + 7 * amp), 48, axis='X', center=(0, 0, CZ), r_in=0.08 + 0.25 * amp))
    m.overlay('noise', join('nz', waves), 'Sound level through the silencer', 'Large rings = loud. Chambers and baffles reflect low-frequency sound back (reactive); the '
              'packing around the perforated tube absorbs high frequencies (absorptive). Insertion loss is typically 20–40 dB(A).')
    m.annotate('noise', 'Inlet: loud pulsating gas', (-1.4, 0, CZ + 0.45))
    m.annotate('noise', 'Outlet: much quieter', (1.4, 0, CZ + 0.3))
    m.flow('gas', [(X0 - 0.6, 0, CZ), (-0.4, 0.13 * -1, CZ), (-0.35, -0.13, CZ), (-0.3, 0, CZ), (0.3, 0, CZ), (0.35, 0.13, CZ), (0.4, 0.13, CZ), (X1 + 0.6, 0, CZ)], 'exhaust', 0.012, 0.2)
    return m.export(out)


# =============================================================== EQ-191 Gas holder
def gas_holder(out):
    m = _model('gas_holder', 'Wet (Water-Sealed) Telescopic Gas Holder')
    R, H = 1.4, 1.2
    tank = csg('tk', [cyl('to', R + 0.06, 0.0, H, 'paint_green', 96)], [cyl('ti', R, 0.05, H + 0.1, 'paint_green', 96)], 'paint_green')
    P(m, 'water_tank', 'Water Tank (forms the gas seal)', 'vessel', tank, explode=(0, 0, -0.3), ref='gh_tank')
    wtr = liquid('wtr', R - 0.002, 0.05, H - 0.1)
    wtr = csg('wtrc', [wtr], [cyl('wk', R - 0.12, 0.3, H, 'water', 96)], 'water')
    P(m, 'seal_water', 'Seal Water', 'fluid', wtr, explode=(0, -0.4, 0), ref='gh_water', section='keep')
    rise = lambda t: 0.9 * smooth_pulse(t, 0.4, 0.1, 0.4)
    bell = csg('bell', [cyl('bo', R - 0.06, 0.3, H + 0.6, 'paint_grey', 96), lathe('bd', [(0.0, H + 0.6), (R - 0.06, H + 0.6), (0.0, H + 0.9)], 'paint_grey', 96)],
               [cyl('bi', R - 0.07, 0.25, H + 0.6, 'paint_grey', 96), lathe('bdi', [(0.0, H + 0.59), (R - 0.07, H + 0.59), (0.0, H + 0.88)], 'paint_grey', 96)], 'paint_grey')
    rollers = [box(f'rl{i}', (0.08, 0.08, 0.08), ((R - 0.0) * math.cos(TAU * i / 8), (R - 0.0) * math.sin(TAU * i / 8), H + 0.55), 'steel_dark') for i in range(8)]
    pb = P(m, 'bell', 'Bell (Lift) — rises and falls with the stored gas volume', 'vessel', [bell] + rollers, explode=(0, 0, 1.2), ref='gh_bell')
    keys_loop(m, pb, lambda t: (0, 0, rise(t)))
    cols = [box(f'gc{i}', (0.1, 0.1, H + 2.0), ((R + 0.15) * math.cos(TAU * i / 8), (R + 0.15) * math.sin(TAU * i / 8), (H + 2.0) / 2), 'paint_grey') for i in range(8)]
    ring = cyl('gr', R + 0.22, H + 1.95, H + 2.0, 'paint_grey', 96, r_in=R + 0.08)
    P(m, 'guide_frame', 'Guide Columns & Top Ring (keep the bell vertical)', 'structure', cols + [ring], explode=(0, 0, 0), ref='gh_guides', section='keep')
    pip = [hollow_pipe('gi', [(-2.2, 0.3, 0.3), (-0.6, 0.3, 0.3), (-0.6, 0.3, H + 0.3)], 0.1, 'paint_grey', 24, bend=0.15, t=0.008),
           hollow_pipe('go', [(2.2, -0.3, 0.3), (0.6, -0.3, 0.3), (0.6, -0.3, H + 0.3)], 0.1, 'paint_grey', 24, bend=0.15, t=0.008)]
    P(m, 'gas_pipes', 'Gas Inlet & Outlet Pipes (rise through the water)', 'system_piping', pip, explode=(0, 0, -0.2), ref='gh_pipes', section='keep')
    m.flow('gas_in', [(-2.2, 0.3, 0.3), (-0.6, 0.3, 0.3), (-0.6, 0.3, H + 0.45), (-0.3, 0.3, H + 0.55)], 'flue_gas', 0.03, 0.4, active=[(0.0, 0.45)])
    m.flow('gas_out', [(0.3, -0.3, H + 0.55), (0.6, -0.3, H + 0.45), (0.6, -0.3, 0.3), (2.2, -0.3, 0.3)], 'flue_gas', 0.03, 0.4, active=[(0.5, 0.95)])
    return m.export(out)


# =============================================================== EQ-192 LPG bullet
def lpg_storage_bullet(out):
    m = _model('lpg_storage_bullet', 'LPG Storage Bullet (Horizontal Pressure Vessel)')
    R, L, X0, CZ = 0.7, 4.0, -2.0, 1.2
    _hvessel(m, 'bullet', 'Bullet Shell & Hemispherical Heads', R, L, X0, CZ, 'paint_white' if False else 'nameplate', 'lpg_shell', heads=('hemi', 'hemi'), t=0.02)
    _hliquid(m, 'lpg_liquid', 'Liquid LPG (≤ ~85 % fill; vapour above)', R - 0.021, L, X0, CZ, CZ + 0.25, 'lpg_liquid', mat='hydraulic_oil', dz=-0.2, fn=lambda t: 0.5 - 0.5 * math.cos(TAU * t))
    noz = [join('psv', [cyl(f'pv{i}', 0.04, CZ + R, CZ + R + 0.35, 'paint_red', 16, center=(X0 + 0.8 + 0.3 * i, 0, 0)) for i in range(2)] + [cyl('psvt', 0.04, CZ + R + 0.35, CZ + R + 1.2, 'steel', 16, center=(X0 + 0.95, 0, 0))]),
           nozzle('vl', (X0 + 2.0, 0, CZ + R), (0, 0, 1), 0.05, 0.25), nozzle('ll', (X0 + 1.2, 0, CZ - R), (0, 0, -1), 0.07, 0.3), nozzle('fl', (X0 + 3.0, 0, CZ + R), (0, 0, 1), 0.05, 0.25),
           nozzle('dr', (X0 + 3.3, 0, CZ - R), (0, 0, -1), 0.025, 0.2), nozzle('mh', (X0 + L + 0.0, 0, CZ + R * 0.3), (0, 0, 1), 0.2, 0.15) if False else nozzle('mh', (X0 + 2.6, 0, CZ + R - 0.02), (0, 0, 1), 0.22, 0.12),
           join('lg', [cyl('lgb', 0.04, CZ - R * 0.8, CZ + R * 0.8, 'steel', 16, center=(X0 + L - 0.5, -R - 0.15, 0)), box('lgx', (0.1, 0.08, 0.14), (X0 + L - 0.5, -R - 0.2, CZ + R * 0.8), 'paint_blue')]),
           join('ti', [cyl('ti', 0.012, CZ - 0.2, CZ + 0.2, 'chrome', 8, center=(X0 + 1.6, -R - 0.05, 0))])]
    P(m, 'fittings', 'Safety Relief Valves & Vent Stack, Vapour/Liquid/Fill Nozzles, Drain, Manway, Level & Temperature Gauges', 'nozzles', noz, explode=(0, 0, 0.5), ref='lpg_fittings', section='keep')
    dl = [sweep_tube('dlr', [(X0 + 0.2 + (L - 0.4) * i / 40, 0, CZ + R + 0.15) for i in range(41)], 0.025, 'paint_red', 10)] + \
         [cyl(f'dn{i}', 0.012, CZ + R + 0.1, CZ + R + 0.15, 'brass', 8, center=(X0 + 0.4 + 0.5 * i, 0, 0)) for i in range(8)]
    P(m, 'deluge', 'Water Deluge / Spray Ring (fire protection, cooling)', 'fire_protection', dl, explode=(0, 0.4, 0.4), ref='lpg_deluge', section='keep')
    P(m, 'earthing', 'Earthing Boss & Bonding', 'electrical', cyl('eb', 0.02, 0.0, 0.3, 'copper', 8, center=(X0 + 0.5, -R, 0)), explode=(0, -0.3, 0), ref='lpg_earthing', section='keep')
    m.flow('liquid_out', [(X0 + 1.2, 0.05, CZ - 0.2), (X0 + 1.2, 0, CZ - R - 0.3)], 'hydraulic_oil', 0.012, 0.2)
    m.flow('vapour_balance', [(X0 + 2.0, 0.05, CZ + 0.5), (X0 + 2.0, 0, CZ + R + 0.25)], 'air', 0.012, 0.15)
    m.flow('fill', [(X0 + 3.0, 0, CZ + R + 0.25), (X0 + 3.0, 0.05, CZ + 0.3)], 'hydraulic_oil', 0.012, 0.15)
    return m.export(out)


# =============================================================== EQ-193 Cryogenic storage tank
def cryogenic_storage_tank(out):
    m = _model('cryogenic_storage_tank', 'Full-Containment Cryogenic (LNG) Storage Tank')
    Ri, Ro, H = 1.6, 2.0, 2.2
    outer = csg('ow', [cyl('oo', Ro + 0.15, 0.0, H + 0.2, 'cast_iron', 96), lathe('rd', [(0.0, H + 0.2), (Ro + 0.15, H + 0.2), (0.0, H + 0.75)], 'cast_iron', 96)],
                [cyl('oi', Ro, 0.15, H + 0.21, 'cast_iron', 96), lathe('rdi', [(0.0, H + 0.19), (Ro, H + 0.19), (0.0, H + 0.6)], 'cast_iron', 96)], 'cast_iron')
    P(m, 'outer_tank', 'Outer Pre-stressed Concrete Wall & Dome Roof (secondary containment)', 'structure', half(outer, 'cast_iron'), explode=(0, 0.0, 0), ref='cr_outer', section='keep')
    liner = cyl('lin', Ro - 0.005, 0.15, H + 0.18, 'steel', 96, r_in=Ro - 0.015)
    P(m, 'liner', 'Carbon-Steel Vapour Liner', 'structure', half(liner, 'steel'), explode=(0, 0.4, 0), ref='cr_liner', section='keep')
    ins = csg('ins', [cyl('io', Ro - 0.015, 0.15, H, 'foam', 96)], [cyl('ii', Ri + 0.01, 0.3, H + 0.1, 'foam', 96)], 'foam')
    P(m, 'insulation', 'Annular Perlite Insulation & Base Insulation (cellular glass)', 'insulation', half(ins, 'foam'), explode=(0, 0.7, 0), ref='cr_insulation', section='keep')
    inner = csg('in', [cyl('ino', Ri + 0.01, 0.3, H - 0.1, 'stainless', 96)], [cyl('ini', Ri, 0.32, H, 'stainless', 96)], 'stainless')
    P(m, 'inner_tank', 'Inner Tank — 9 % Nickel Steel (primary containment)', 'vessel', half(inner, 'stainless'), explode=(0, 1.0, 0), ref='cr_inner', section='keep')
    deck = cyl('dk', Ri + 0.15, H - 0.05, H, 'aluminium', 96)
    hang = [cyl(f'hg{i}', 0.008, H, H + 0.45, 'steel', 8, center=(Ri * 0.7 * math.cos(TAU * i / 8), Ri * 0.7 * math.sin(TAU * i / 8), 0)) for i in range(8)]
    P(m, 'suspended_deck', 'Insulated Suspended Deck (hung from the roof)', 'structure', [deck] + hang, explode=(0, 0, 0.7), ref='cr_deck')
    lng = liquid('lng', Ri - 0.002, 0.32, H * 0.75, mat='water')
    pl = P(m, 'lng', 'LNG at about −162 °C', 'fluid', lng, explode=(0, -0.4, 0), ref='cr_lng', section='keep')
    animate_level(m, pl, 0.6, -0.4, lambda t: 0.5 - 0.5 * math.cos(TAU * t))
    pumps = [join(f'pc{i}', [cyl(f'pcc{i}', 0.08, 0.35, H + 1.0, 'stainless', 32, center=(x, 0.3, 0), r_in=0.07), cyl(f'pp{i}', 0.065, 0.36, 0.7, 'paint_blue', 32, center=(x, 0.3, 0))]) for i, x in enumerate((-0.5, 0.5))]
    P(m, 'in_tank_pumps', 'In-Tank Submerged Pumps in Pump Columns (no bottom penetrations)', 'pumps', pumps, explode=(0, 0, 1.0), ref='cr_pumps', section='keep')
    tp = [nozzle('bog', (0.9, 0, H + 0.45), (0, 0, 1), 0.08, 0.6), nozzle('fill', (-1.0, 0, H + 0.4), (0, 0, 1), 0.08, 0.6),
          join('pf', [platform('pf', 0.0, 1.0, H + 0.95, a0=0.0, a1=TAU)])]
    P(m, 'roof_platform', 'Roof Platform, Boil-off Gas Outlet & Top Fill Line', 'nozzles', tp, explode=(0, 0, 0.8), ref='cr_roof', section='keep')
    m.flow('boil_off_gas', [(0.2, 0.5, H * 0.75 + 0.05), (0.9, 0.1, H + 0.2), (0.9, 0, H + 1.05)], 'air', 0.025, 0.3)
    m.flow('send_out', [(-0.5, 0.3, 0.4), (-0.5, 0.3, H + 1.05)], 'water', 0.025, 0.3)
    m.flow('fill', [(-1.0, 0, H + 1.0), (-1.0, 0.1, H * 0.7)], 'water', 0.02, 0.25, active=[(0.0, 0.5)])
    return m.export(out)


# =============================================================== EQ-194 Floating roof tank
def floating_roof_tank(out):
    m = _model('floating_roof_tank', 'External Floating Roof Storage Tank')
    R, H = 2.0, 2.4
    shell = csg('sh', [cyl('so', R + 0.02, 0.0, H, 'paint_grey', 128)], [cyl('si', R, 0.02, H + 0.1, 'paint_grey', 128)], 'paint_grey')
    wg = cyl('wg', R + 0.25, H - 0.15, H - 0.12, 'paint_grey', 128, r_in=R + 0.02)
    P(m, 'shell', 'Tank Shell, Bottom & Wind Girder', 'vessel', [shell, wg], explode=(0, 0, 0), ref='fr_shell')
    lvl = lambda t: 0.5 - 0.5 * math.cos(TAU * t)
    zr0 = 1.0
    prod = liquid('pr', R - 0.002, 0.02, zr0)
    pp = P(m, 'product', 'Stored Product (crude oil) — level changes', 'fluid', prod, explode=(0, -0.5, 0), ref='fr_product', section='keep')
    animate_level(m, pp, 0.5, 1.0, lvl)
    roof = csg('rf', [cyl('ro', R - 0.06, zr0, zr0 + 0.08, 'paint_grey', 128)], [cyl('rk', R - 0.5, zr0 + 0.01, zr0 + 0.09, 'paint_grey', 128)], 'paint_grey')
    deck = cyl('dk', R - 0.5, zr0 + 0.01, zr0 + 0.02, 'paint_grey', 96)
    seal = cyl('sl', R - 0.002, zr0 + 0.02, zr0 + 0.1, 'rubber', 128, r_in=R - 0.06)
    lgs = [cyl(f'lg{i}', 0.02, zr0 - 0.4, zr0 + 0.25, 'steel', 8, center=((R - 0.8) * math.cos(TAU * i / 8), (R - 0.8) * math.sin(TAU * i / 8), 0)) for i in range(8)]
    drain = sweep_tube('rd', [(0.0, 0.3, zr0), (0.6, 0.6, zr0 * 0.6), (R - 0.1, 0.4, 0.15)], 0.03, 'steel', 10)
    pr = P(m, 'floating_roof', 'Floating Roof: Pontoons, Deck, Rim Seal, Support Legs & Roof Drain', 'roof', [roof, deck, seal] + lgs, explode=(0, 0, 1.2), ref='fr_roof')
    keys_loop(m, pr, lambda t: (0, 0, 1.0 * lvl(t)))
    P(m, 'roof_drain', 'Articulated Roof Drain', 'roof', drain, explode=(0, 0.5, 0.5), ref='fr_drain', section='keep')
    gw = join('gw', [box('gwb', (0.5, 0.35, 0.03), (0.0, -R - 0.15, H), 'steel_dark') if False else box('gwb', (0.4, 0.4, 0.03), (R + 0.1, 0.0, H), 'steel_dark'),
                     ladder('st', R + 0.35, 0.0, 0.0, H, facing='x')])
    P(m, 'access', 'Gauger\'s Platform & Spiral Stair (shown straight)', 'access', gw, explode=(0.4, 0, 0), ref='fr_access', section='keep')
    xa = R + 0.1
    rl = join('rl', [cyl('rl1', 0.015, xa - 1.1, xa, 'paint_yellow', 8, axis='X', center=(0, -0.2, H)), cyl('rl2', 0.015, xa - 1.1, xa, 'paint_yellow', 8, axis='X', center=(0, 0.2, H))] +
              [cyl(f'rr{k}', 0.01, -0.2, 0.2, 'paint_yellow', 8, axis='Y', center=(xa - 0.1 - 0.15 * k, 0, H)) for k in range(7)])
    prl = P(m, 'rolling_ladder', 'Rolling Ladder (from gauger platform to the roof)', 'access', rl, explode=(0.3, 0, 0.6), ref='fr_access', section='keep', pivot=(xa, 0, H))
    from pumpforge.rotkit import axis_rot_keys
    for mesh in prl.meshes:
        axis_rot_keys(m, mesh, (0, 1, 0), lambda t: -math.asin(min(1.0, max(-1.0, (H - (zr0 + 0.08 + 1.0 * lvl(t))) / 1.1))))
    noz = [nozzle('in', (R, 0.6, 0.3), (1, 0.3, 0), 0.08, 0.3), nozzle('out', (R * 0.9, -0.9, 0.3), (1, -0.45, 0), 0.08, 0.3), nozzle('mx', (-R, 0, 0.4), (-1, 0, 0), 0.15, 0.2)]
    P(m, 'nozzles', 'Inlet, Outlet & Side-Entry Mixer Nozzle', 'nozzles', noz, explode=(0, 0, 0.3), ref='fr_nozzles', section='keep')
    m.flow('inlet', [(R + 0.4, 0.75, 0.3), (R - 0.2, 0.6, 0.3), (0.5, 0.3, 0.3)], 'hydraulic_oil', 0.03, 0.3, active=[(0.0, 0.5)])
    m.flow('outlet', [(0.5, -0.4, 0.3), (R * 0.9, -0.9, 0.3), (R + 0.4, -1.1, 0.3)], 'hydraulic_oil', 0.03, 0.3, active=[(0.5, 1.0)])
    return m.export(out)


# =============================================================== EQ-195 Pressure storage tank (sphere)
def pressure_storage_tank(out):
    m = _model('pressure_storage_tank', 'Spherical Pressure Storage Tank (Horton Sphere) for LPG/Butane')
    R, CZ = 1.6, 2.4
    sp = csg('sp', [sphere('so', (0, 0, CZ), R + 0.02, 'nameplate', 64)], [sphere('si', (0, 0, CZ), R, 'nameplate', 64)], 'nameplate')
    P(m, 'sphere', 'Spherical Shell (welded petals)', 'vessel', sp, explode=(0, 0, 0), ref='ps_sphere')
    lq = csg('lq', [sphere('lqs', (0, 0, CZ), R - 0.003, 'hydraulic_oil', 64)], [box('lqk', (4 * R, 4 * R, 2 * R), (0, 0, CZ + 0.2 + R), 'hydraulic_oil'), box('lqh', (4 * R, 2 * R, 4 * R), (0, -R, CZ), 'hydraulic_oil')], 'hydraulic_oil')
    pl = P(m, 'liquid', 'Liquefied Gas (level animated)', 'fluid', lq, explode=(0, -0.5, 0), ref='ps_liquid', section='keep')
    animate_level(m, pl, CZ - 0.3, -0.5, lambda t: 0.5 - 0.5 * math.cos(TAU * t))
    n = 8
    cols = []
    for i in range(n):
        a = TAU * i / n
        x, y = R * math.cos(a), R * math.sin(a)
        cols.append(cyl(f'c{i}', 0.08, 0.0, CZ, 'paint_grey', 24, center=(x, y, 0)))
        x2, y2 = R * math.cos(a + TAU / n), R * math.sin(a + TAU / n)
        cols.append(sweep_tube(f'br{i}', [(x, y, 0.3), (x2, y2, CZ - 0.5)], 0.02, 'steel', 6))
    P(m, 'legs', 'Support Columns (equatorial) & Cross Bracing', 'structure', cols, explode=(0, 0, -0.3), ref='ps_legs', section='keep')
    tp = [join('psv', [cyl(f'pv{i}', 0.05, CZ + R, CZ + R + 0.35, 'paint_red', 16, center=(0.3 * (i - 0.5), 0.2, 0)) for i in range(2)]),
          platform('tpf', 0.0, 0.7, CZ + R + 0.02, a0=0.0, a1=TAU), nozzle('bl', (0, 0, CZ - R), (0, 0, -1), 0.08, 0.5),
          join('lg', [box('lgr', (0.1, 0.08, 0.14), (-0.5, -0.3, CZ + R - 0.1), 'paint_blue')])]
    st = join('stair', [ladder('stl', R + 0.55, 0.0, 0.0, CZ + R + 0.05, facing='x'), box('wk', (R + 0.55 - 0.6, 0.5, 0.03), ((R + 0.55 + 0.6) / 2, 0, CZ + R + 0.04), 'steel_dark'),
                        box('wr', (R + 0.55 - 0.6, 0.02, 0.03), ((R + 0.55 + 0.6) / 2, 0.25, CZ + R + 0.55), 'paint_yellow')])
    P(m, 'fittings', 'Safety Valves, Top Platform, Bottom Liquid Nozzle & Level Transmitter', 'nozzles', tp, explode=(0, 0, 0.6), ref='ps_fittings', section='keep')
    P(m, 'stairway', 'Access Ladder & Walkway to Top Platform', 'access', st, explode=(0.5, 0.5, 0), ref='ps_stair', section='keep')
    dl = sweep_tube('dl', [((R + 0.15) * math.cos(TAU * i / 48), (R + 0.15) * math.sin(TAU * i / 48), CZ + R * 0.7) for i in range(49)], 0.025, 'paint_red', 8)
    P(m, 'deluge', 'Water Spray (Deluge) Ring', 'fire_protection', dl, explode=(0, 0, 0.4), ref='ps_deluge', section='keep')
    m.flow('liquid', [(0, 0.05, CZ - R + 0.2), (0, 0, CZ - R - 0.5)], 'hydraulic_oil', 0.02, 0.2)
    m.flow('vapour_to_relief', [(0.15, 0.2, CZ + R - 0.1), (0.15, 0.2, CZ + R + 0.4)], 'air', 0.02, 0.2)
    return m.export(out)


# ===================================================================== metadata
def _std(*items):
    return [{'id': i, 'title': t, 'relevance': r, 'edition': 'to be verified'} for i, t, r in items]


_VSTD = _std(('ASME BPVC Section VIII Div. 1', 'Rules for Construction of Pressure Vessels', 'Design, fabrication, inspection.'), ('EN 13445', 'Unfired pressure vessels', 'European design code.'))
_SEP_STD = _std(('API 12J', 'Specification for Oil and Gas Separators', 'Oilfield separators.'), ('ASME BPVC VIII', 'Pressure vessels', 'Pressure parts.'))
_SV = {'sv_saddles': C('Support a horizontal vessel; one saddle slides to allow thermal expansion.', 'Welded saddles with wear plates.', 'Carbon steel.', 'Zick analysis for saddle stresses.', ['Corrosion under wear plate'], ['Inspect'])}


def _c(fn, cons, mat, op='—', fm=('—',), insp=('Visual',)):
    return C(fn, cons, mat, op, list(fm), list(insp))


META = {
    'deaerator': {'summary': ('A deaerator removes dissolved oxygen and carbon dioxide from boiler feedwater, which would otherwise corrode the boiler. Incoming water is sprayed into '
                              'steam and trickles over trays, heating it to saturation; the gases are released and vented, and the hot deaerated water collects in the storage tank.'),
                  'classification': {'family': 'Steam-system vessel', 'type': 'Spray-tray deaerator with horizontal storage'},
                  'model_configuration': {'trays': 4, 'spray_valves': 3, 'oxygen_target': '≈ 0.005 cm³/L (7 ppb) — typical guarantee'},
                  'standards': _VSTD + _std(('HEI 2954', 'Standards and Typical Specifications for Deaerators', 'Design and performance.'),), 'references': ['Spirax Sarco — The Steam and Condensate Loop'],
                  'components': {**_SV, 'da_tank': _c('Stores deaerated feedwater for the boiler feed pumps.', 'Horizontal pressure vessel.', 'Carbon steel.', 'Provides NPSH for feed pumps (elevated).', ['Corrosion'], ['Thickness check']),
                                 'da_water': _c('Deaerated water (level animated).', '—', '—'), 'da_head': _c('Contains the deaeration section.', 'Vertical vessel with neck.', 'Carbon/stainless steel.'),
                                 'da_trays': _c('Spread the water into thin films for final gas stripping.', 'Perforated trays.', 'Stainless steel.', '—', ['Fouling'], ['Inspect']),
                                 'da_spray': _c('Atomise incoming water into the steam space.', 'Spring-loaded spray valves.', 'Stainless steel.', '—', ['Spring failure'], ['Inspect']),
                                 'da_nozzles': _c('Water, steam, vent, outlet and level connections.', 'Nozzles, level gauge.', 'Steel.', 'Vent must be kept open (small steam plume).', ['Blocked vent'], ['Check plume'])}},
    'boiler_feedwater_tank': {'summary': ('A boiler feedwater tank collects condensate returns and treated make-up water and holds a reserve for the boiler feed pumps. Keeping it hot '
                                          '(steam sparger) drives off oxygen and reduces corrosion and chemical dosing.'),
                              'classification': {'family': 'Storage vessel', 'type': 'Horizontal atmospheric/low-pressure feed tank'},
                              'model_configuration': {'animation': 'Level rises and falls with make-up and demand'},
                              'standards': _VSTD, 'references': ['Spirax Sarco — Boiler feedtanks'],
                              'components': {**_SV, 'fw_tank': _c('Holds feedwater.', 'Horizontal tank with dished heads.', 'Carbon/stainless steel.'), 'fw_water': _c('Feedwater (animated level).', '—', '—'),
                                             'fw_nozzles': _c('Connections and level gauge.', 'Nozzles.', 'Steel.', 'Pump suction low, returns high.', ['Leaks'], ['Visual']),
                                             'fw_sparger': _c('Injects steam to heat the water (~85–90 °C) to reduce dissolved oxygen.', 'Perforated pipe.', 'Stainless.', '—', ['Noise/hammer'], ['Inspect'])}},
    'hotwell': {'summary': ('The hotwell is the collection box at the bottom of a steam surface condenser. Steam from the turbine condenses on the cold tubes; the condensate drips into '
                            'the hotwell, which provides a small storage volume and suction head for the condensate extraction pumps. A level controller keeps the level steady.'),
                'classification': {'family': 'Condenser component / storage', 'type': 'Surface-condenser hotwell'},
                'model_configuration': {'animation': 'Condensate drops fall into the hotwell; level fluctuates'},
                'standards': _std(('HEI 2629', 'Standards for Steam Surface Condensers', 'Design and hotwell storage.'),), 'references': ['HEI condenser standards'],
                'components': {'hw_shell': _c('Encloses the condensing steam.', 'Fabricated shell.', 'Carbon steel.', 'Under vacuum.', ['Air in-leakage'], ['Helium leak test']),
                               'hw_tubes': _c('Condense the steam with cooling water inside.', 'Tube bundle and tube sheets.', 'Stainless/titanium/Cu-Ni.', '—', ['Tube leaks'], ['Eddy current']),
                               'hw_box': _c('Collects condensate.', 'Box below the bundle.', 'Carbon steel.'), 'hw_condensate': _c('Condensate (level animated).', '—', '—'),
                               'hw_connections': _c('Outlet to CEP, level, CW, air extraction, make-up.', 'Nozzles.', 'Steel.')}},
    'surge_vessel': {'summary': ('A surge vessel protects a pipeline from water hammer. When a pump trips or a valve closes quickly, pressure waves travel along the pipe; the vessel\'s '
                                 'compressed-air cushion lets water flow in or out, damping the pressure rise and preventing column separation (vacuum).'),
                     'classification': {'family': 'Pressure vessel (transient protection)', 'type': 'Air-cushion surge vessel'},
                     'model_configuration': {'animation': 'Level oscillates and damps out after a surge'},
                     'standards': _VSTD, 'references': ['Thorley, Fluid Transients in Pipeline Systems'],
                     'components': {'sg_vessel': _c('Holds water and the air cushion.', 'Vertical vessel.', 'Carbon steel.'), 'sg_supports': _c('Supports.', 'Legs.', 'Steel.'),
                                    'sg_water': _c('Water (oscillating level).', '—', '—'), 'sg_air': _c('Compressible cushion that absorbs surges.', 'Air above water (or bladder).', 'Air.', 'Air dissolves — top up.', ['Loss of air'], ['Level check']),
                                    'sg_connections': _c('Connection to main, gauges, air and safety valve.', 'Nozzles.', 'Steel.'), 'sg_compressor': _c('Tops up the air volume.', 'Small compressor.', '—')}},
    'knockout_drum': {'summary': ('A flare knockout (KO) drum removes liquid droplets from gas going to a flare. The gas slows down in the large drum so droplets fall out by gravity and '
                                  'collect at the bottom; dry gas goes on to the flare and the liquid is pumped out. It prevents burning liquid "rain" from the flare.'),
                      'classification': {'family': 'Separator', 'type': 'Horizontal flare KO drum'},
                      'model_configuration': {'animation': 'Droplets settle; liquid level rises'},
                      'standards': _std(('API 521 / ISO 23251', 'Pressure-relieving and depressuring systems', 'KO drum sizing.'),), 'references': ['API 521'],
                      'components': {**_SV, 'ko_drum': _c('Low-velocity space for droplets to settle.', 'Horizontal vessel.', 'Carbon steel.'), 'ko_liquid': _c('Collected liquid.', '—', '—'),
                                     'ko_inlet': _c('Inlet with diverter to spread the flow.', 'Nozzle and plate.', 'Steel.'), 'ko_nozzles': _c('Outlets, level transmitter, vortex breaker.', 'Nozzles.', 'Steel.')}},
    'gas_liquid_separator': {'summary': ('A gas–liquid separator splits a mixed stream into gas and liquid. The inlet device breaks the momentum, liquid drops to the bottom by gravity, and '
                                         'a mesh pad near the top catches fine mist before the gas leaves. A level controller and control valve keep the liquid level constant.'),
                             'classification': {'family': 'Separator', 'type': 'Vertical two-phase separator with mesh pad'},
                             'model_configuration': {'sections': 'Inlet, gravity settling, mist extraction, liquid collection'},
                             'standards': _SEP_STD, 'references': ['GPSA Engineering Data Book Section 7'],
                             'components': {'gl_vessel': _c('Pressure vessel.', 'Vertical vessel.', 'Carbon steel.'), 'gl_supports': _c('Supports.', 'Legs.', 'Steel.'), 'gl_liquid': _c('Liquid section.', '—', '—'),
                                            'gl_inlet': _c('Reduces inlet momentum and distributes flow.', 'Half-pipe diverter.', 'Stainless.'),
                                            'gl_mesh': _c('Captures fine droplets.', 'Knitted wire mesh pad.', 'Stainless wire.', 'Gas velocity limited by K-factor (Souders–Brown).', ['Plugging'], ['ΔP check']),
                                            'gl_nozzles': _c('Outlets, vortex breaker, level control loop.', 'Nozzles, LC, CV.', 'Steel.')}},
    'three_phase_separator': {'summary': ('A three-phase separator splits well fluid into gas, oil and water. Gas rises to the top; the liquid settles into a water layer below an oil layer. '
                                          'The oil spills over a weir into a separate compartment; water is drawn from under the oil. Interface and level controllers set each outlet.'),
                              'classification': {'family': 'Separator', 'type': 'Horizontal three-phase separator with weir'},
                              'model_configuration': {'phases': 'Gas / oil / water', 'internals': 'Inlet diverter, weir, mist eliminator'},
                              'standards': _SEP_STD, 'references': ['Arnold & Stewart, Surface Production Operations Vol. 1'],
                              'components': {**_SV, 'tp_vessel': _c('Holds the separation volumes.', 'Horizontal vessel.', 'Carbon steel.'), 'tp_water': _c('Free water layer.', '—', '—'), 'tp_oil': _c('Oil layer.', '—', '—'),
                                             'tp_internals': _c('Inlet diverter and oil weir.', 'Plates.', 'Stainless.', 'Weir height sets the oil–water interface.', ['Emulsion build-up'], ['Interface monitoring']),
                                             'tp_mesh': _c('Removes mist from gas.', 'Vane pack / mesh.', 'Stainless.'), 'tp_nozzles': _c('Gas, oil, water outlets and sand drain.', 'Nozzles.', 'Steel.')}},
    'scrubber_vessel': {'summary': ('A wet scrubber removes acid gases, dust or odours from a gas stream by contact with a scrubbing liquid. Gas flows up through a packed bed while liquor '
                                    'from spray nozzles trickles down over the packing; pollutants dissolve or react in the liquid. A mist eliminator stops droplets leaving with the gas.'),
                        'classification': {'family': 'Gas treatment', 'type': 'Packed-bed counter-current wet scrubber'},
                        'model_configuration': {'packing': 'Random packing (e.g. Pall rings)', 'liquor': 'Recirculated with pH control'},
                        'standards': _std(('EN 13121 / ASME RTP-1', 'FRP tanks and vessels', 'Plastic vessel design.'),), 'references': ['Perry\'s — gas absorption'],
                        'components': {'sc_vessel': _c('Contains the packing and contact zone.', 'Tower.', 'FRP / PP / lined steel.'), 'sc_sump': _c('Holds liquor.', '—', '—'),
                                       'sc_packing': _c('Large wetted surface for gas–liquid contact.', 'Random packing on support grid.', 'PP/ceramic/metal.', 'Flooding limit.', ['Fouling, scaling'], ['ΔP']),
                                       'sc_spray': _c('Distributes liquor evenly.', 'Spray header.', 'PP.'), 'sc_mist': _c('Removes entrained droplets.', 'Mist eliminator.', 'PP/stainless.'),
                                       'sc_nozzles': _c('Gas and liquor connections.', 'Nozzles.', '—'), 'sc_pump': _c('Recirculates liquor.', 'Centrifugal pump.', '—'), 'sc_supports': _c('Base.', '—', '—')}},
    'demister_vessel': {'summary': ('A demister vessel removes fine liquid mist from gas. Droplets hit the wires of a knitted mesh pad, merge into larger drops and drain away; a chevron vane '
                                    'pack after it uses changes of direction to catch remaining droplets. Clean, dry gas leaves at the top.'),
                        'classification': {'family': 'Gas treatment / separator', 'type': 'Vertical mist eliminator vessel (mesh + vane)'},
                        'model_configuration': {'internals': 'Mesh pad + chevron vane pack'},
                        'standards': _VSTD, 'references': ['Koch-Otto York / Sulzer demister literature (generic)'],
                        'components': {'dm_vessel': _c('Vessel.', '—', 'Steel.'), 'dm_supports': _c('Legs.', '—', 'Steel.'),
                                       'dm_mesh': _c('Coalesces fine droplets.', 'Knitted wire mesh.', 'Stainless.', 'Re-entrainment above design velocity.', ['Plugging'], ['ΔP']),
                                       'dm_vanes': _c('Inertial capture of droplets.', 'Chevron vanes.', 'Stainless.'), 'dm_liquid': _c('Drained liquid.', '—', '—'), 'dm_nozzles': _c('Connections and ΔP.', '—', '—')}},
    'chimney_stack': {'summary': ('A chimney (stack) discharges flue gases high enough to disperse them safely. Hot gas rises by natural draft; height and exit velocity set the dispersion. '
                                  'Steel stacks are lined against acid condensation, fitted with helical strakes against wind-induced vibration, and carry sampling ports, platforms and an aviation light.'),
                      'classification': {'family': 'Process structure', 'type': 'Self-supported lined steel stack with strakes'},
                      'model_configuration': {'height': 'Model scaled — real stacks 30–250 m', 'strakes': '3-start helical, upper third'},
                      'standards': _std(('EN 13084', 'Free-standing chimneys', 'Design.'), ('ASME STS-1', 'Steel Stacks', 'Design.'), ('CICIND', 'Model code for steel chimneys', 'Design.')),
                      'references': ['ASME STS-1 commentary'],
                      'components': {'ch_shell': _c('Carries loads and contains the gas.', 'Welded steel shell with flared base.', 'Carbon/weathering steel.', 'Wind and seismic design.', ['Corrosion'], ['Thickness survey']),
                                     'ch_lining': _c('Protects against heat and acid condensation.', 'Lining/insulation.', 'Mineral wool, refractory, alloy liner.'),
                                     'ch_strakes': _c('Break up vortex shedding that causes vibration.', 'Helical strakes.', 'Steel.'), 'ch_breeching': _c('Brings flue gas in.', 'Duct.', 'Steel.'),
                                     'ch_access': _c('Access for sampling and inspection.', 'Platforms, ladder.', 'Steel.'), 'ch_fittings': _c('Safety and monitoring fittings.', 'Light, rod, ports.', '—'),
                                     'ch_foundation': _c('Anchors the stack.', 'Concrete foundation with anchor bolts.', 'Concrete.')}},
    'silencer': {'summary': ('A silencer reduces noise from gas flow (engine exhausts, blow-offs, vents). Reactive chambers and baffles reflect low-frequency sound back toward the source; '
                             'absorptive packing behind a perforated tube converts high-frequency sound into heat. Combined designs cover a wide frequency range with low pressure drop.'),
                 'classification': {'family': 'Noise control', 'type': 'Combination reactive/absorptive silencer'},
                 'model_configuration': {'chambers': 3, 'packing': 'Mineral wool'},
                 'standards': _std(('ISO 7235', 'Acoustics — Laboratory measurement of ducted silencers', 'Insertion loss.'), ('ISO 11820', 'Acoustics — Measurements on silencers in situ', 'Field tests.')),
                 'references': ['Beranek & Vér, Noise and Vibration Control Engineering'],
                 'components': {'si_shell': _c('Pressure shell.', 'Welded shell with cones.', 'Steel.'), 'si_baffles': _c('Create chambers that reflect sound.', 'Baffle plates.', 'Steel.'),
                                'si_absorptive': _c('Absorb high-frequency noise.', 'Perforated tube with packing.', 'Steel, mineral wool.', 'Packing must be retained (cloth).', ['Packing loss'], ['Inspect']),
                                'si_connections': _c('Flanges.', '—', 'Steel.'), 'si_supports': _c('Supports.', '—', 'Steel.')}},
    'gas_holder': {'summary': ('A wet gas holder stores low-pressure gas (biogas, town gas, process gas) in a steel bell that floats in a water-filled tank. As gas comes in, the bell rises; '
                               'as gas is drawn off, it sinks. The water forms the seal and the bell\'s weight sets a nearly constant gas pressure.'),
                   'classification': {'family': 'Gas storage', 'type': 'Single-lift wet gas holder (guide-framed)'},
                   'model_configuration': {'animation': 'Bell rises as gas enters, falls as gas is drawn off'},
                   'standards': _std(('Historic / national codes', 'Gasholder design', 'Mostly legacy installations; modern sites use dry (membrane) holders.'),), 'references': ['Gas industry historical design notes'],
                   'components': {'gh_tank': _c('Holds the seal water.', 'Steel/concrete tank.', 'Steel.'), 'gh_water': _c('Water seal.', '—', '—'),
                                  'gh_bell': _c('Stores the gas; its weight sets the pressure.', 'Steel bell with crown.', 'Steel.', '—', ['Corrosion at water line'], ['Inspect']),
                                  'gh_guides': _c('Guide the bell vertically.', 'Columns and rollers.', 'Steel.'), 'gh_pipes': _c('Gas in and out.', 'Pipes through the water.', 'Steel.')}},
    'lpg_storage_bullet': {'summary': ('An LPG bullet is a horizontal pressure vessel that stores liquefied petroleum gas under its own vapour pressure. It is filled to no more than about '
                                       '85 % so the liquid can expand. Safety relief valves, a water deluge system and remote-operated valves protect it; it is mounded or spaced per fire codes.'),
                           'classification': {'family': 'Pressure storage', 'type': 'Horizontal LPG bullet with hemispherical heads'},
                           'model_configuration': {'fill': '≤ ~85 % liquid (typical maximum)', 'animation': 'Liquid level changes'},
                           'standards': _VSTD + _std(('NFPA 58', 'Liquefied Petroleum Gas Code', 'Installation and safety.'), ('API 2510', 'Design and Construction of LPG Installations', 'Design.')),
                           'references': ['NFPA 58'],
                           'components': {**_SV, 'lpg_shell': _c('Contains LPG under pressure.', 'Shell and hemispherical heads.', 'Carbon steel (impact tested).'), 'lpg_liquid': _c('Liquid LPG.', '—', '—'),
                                          'lpg_fittings': _c('Relief, process connections and gauges.', 'PSVs, nozzles, gauges.', '—', 'Relief valves sized for fire case.', ['Valve leakage'], ['PSV test']),
                                          'lpg_deluge': _c('Cools the vessel in a fire.', 'Spray ring.', 'Steel.'), 'lpg_earthing': _c('Prevents static build-up.', 'Earth boss.', 'Copper.')}},
    'cryogenic_storage_tank': {'summary': ('A full-containment LNG tank stores liquefied natural gas at about −162 °C. An inner tank of 9 % nickel steel holds the liquid; thick insulation '
                                           'limits heat leak; an outer pre-stressed concrete wall and roof can contain the liquid and vapour if the inner tank leaks. Pumps in columns '
                                           'send LNG out from the top, and boil-off gas is removed and recovered.'),
                               'classification': {'family': 'Cryogenic storage', 'type': 'Full-containment LNG tank with suspended deck'},
                               'model_configuration': {'animation': 'LNG level changes; boil-off gas leaves at the top'},
                               'standards': _std(('API 625', 'Tank Systems for Refrigerated Liquefied Gas Storage', 'Containment concepts.'), ('EN 14620', 'Design of site-built vertical cylindrical flat-bottomed steel tanks for refrigerated liquefied gases', 'Design.'),
                                                 ('NFPA 59A', 'Production, Storage and Handling of LNG', 'Safety.')), 'references': ['API 625'],
                               'components': {'cr_outer': _c('Secondary containment and weather enclosure.', 'Pre-stressed concrete wall and dome.', 'Concrete.'), 'cr_liner': _c('Vapour barrier.', 'Steel liner.', 'Carbon steel.'),
                                              'cr_insulation': _c('Limits heat leak and boil-off.', 'Perlite, cellular glass.', 'Insulation.'),
                                              'cr_inner': _c('Holds the cryogenic liquid.', 'Inner tank.', '9 % Ni steel.', 'Must remain ductile at −162 °C.', ['Leakage'], ['Monitoring']),
                                              'cr_deck': _c('Insulated deck hung from the roof.', 'Aluminium deck.', 'Aluminium.'), 'cr_lng': _c('LNG.', '—', '—'),
                                              'cr_pumps': _c('Send LNG out without bottom penetrations.', 'Submerged pumps in columns.', '—'), 'cr_roof': _c('Roof connections.', '—', '—')}},
    'floating_roof_tank': {'summary': ('An external floating roof tank stores volatile liquids such as crude oil. The roof floats on the liquid surface and rises and falls with the level, so there '
                                       'is almost no vapour space — greatly reducing evaporation losses and fire risk. A rim seal closes the gap to the shell; a rolling ladder follows the roof.'),
                           'classification': {'family': 'Atmospheric storage tank', 'type': 'External floating roof (pontoon)'},
                           'model_configuration': {'animation': 'Level rises and falls; roof and rolling ladder follow'},
                           'standards': _std(('API 650', 'Welded Tanks for Oil Storage', 'Tank and floating roof design (Annex C).'), ('API 2350', 'Overfill protection', 'Overfill.'),
                                             ('API 653', 'Tank inspection, repair, alteration', 'Inspection.')), 'references': ['API 650'],
                           'components': {'fr_shell': _c('Holds the liquid.', 'Welded shell, bottom and wind girder.', 'Carbon steel.'), 'fr_product': _c('Stored product.', '—', '—'),
                                          'fr_roof': _c('Floats on the product to eliminate vapour space.', 'Pontoon roof with rim seal and legs.', 'Steel.', 'Legs support the roof when the tank is low.', ['Sinking (drain failure)'], ['Inspect pontoons']),
                                          'fr_drain': _c('Drains rainwater from the roof.', 'Articulated pipe.', 'Steel.', 'Blocked drains can sink the roof.', ['Leak'], ['Test']),
                                          'fr_access': _c('Access to the roof.', 'Platform, stair, rolling ladder.', 'Steel.'), 'fr_nozzles': _c('Inlet, outlet, mixer.', 'Nozzles.', 'Steel.')}},
    'pressure_storage_tank': {'summary': ('A spherical pressure tank (Horton sphere) stores liquefied gases such as butane or propane under pressure. A sphere carries pressure with the '
                                          'least wall thickness for its volume. It stands on columns around the equator with bracing, and has relief valves, deluge cooling and level instruments.'),
                              'classification': {'family': 'Pressure storage', 'type': 'Sphere on equatorial columns'},
                              'model_configuration': {'animation': 'Liquid level changes'},
                              'standards': _VSTD + _std(('API 2510', 'LPG installations', 'Design.'),), 'references': ['API 2510'],
                              'components': {'ps_sphere': _c('Contains the liquefied gas.', 'Welded petal plates.', 'Carbon steel (impact tested).', 'Post-weld heat treatment.', ['Cracking'], ['Internal inspection']),
                                             'ps_liquid': _c('Liquid.', '—', '—'), 'ps_legs': _c('Support the sphere.', 'Columns and bracing.', 'Steel; fireproofed.'),
                                             'ps_fittings': _c('Relief, platform, nozzles, level.', '—', '—'), 'ps_stair': _c('Access.', 'Stairway.', 'Steel.'), 'ps_deluge': _c('Fire cooling.', 'Spray ring.', 'Steel.')}},
}

BUILDERS = {k: globals()[k] for k in META}
