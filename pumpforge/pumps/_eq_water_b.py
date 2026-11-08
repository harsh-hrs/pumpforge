"""Water Treatment & Utilities — part B (EQ-309 … EQ-320): compressed air, nitrogen, steam & condensate,
cooling-tower basin / fan / gearbox, diesel firewater, sewage lift station, effluent treatment plant."""
import math
from mathutils import Matrix, Vector
from pumpforge.core import Model, lathe, cyl, box, csg, join, rotate, TAU, OPERATE_FRAMES
from pumpforge.valvekit import P, keys_loop, smooth_pulse
from pumpforge.parts import hollow_pipe, pressure_gauge, add_tracers
from pumpforge.vesselkit import vessel, nozzle, legs, droplets, liquid_v, liquid, half, animate_level, saddles
from pumpforge.plantkit import thickener, agitated_tank, particles_path, ball
from pumpforge.rotkit import helical_gear
from pumpforge.common_meta import C
from pumps._eq_thermal_a import _bands_z, _bands_x, _pump, _fan_rotor
from pumps._eq_water_a import _rect_tank, _water_box, _press, _std, _c, _thk, _agt

CAT = '13 · Water Treatment & Utilities'


def _model(pid, title):
    return Model(pid, title, CAT, META[pid])


def _valve(name, c, axis='X', r=0.05, mat='cast_iron', kind='gate', wheel_mat='paint_red'):
    """Simple in-line valve: body on a pipe running along `axis`, bonnet & handwheel (gate/globe) or cover (check)."""
    x, y, z = c
    if axis == 'X':
        b = cyl(name + 'b', r * 1.45, x - r * 1.5, x + r * 1.5, mat, 24, axis='X', center=(0, y, z))
    elif axis == 'Y':
        b = cyl(name + 'b', r * 1.45, y - r * 1.5, y + r * 1.5, mat, 24, axis='Y', center=(x, 0, z))
    else:
        b = cyl(name + 'b', r * 1.45, z - r * 1.5, z + r * 1.5, mat, 24, center=(x, y, 0))
    objs = [b]
    if kind == 'check':
        if axis == 'Z':
            objs.append(cyl(name + 'c', r * 1.0, y + r * 1.3, y + r * 1.8, mat, 24, axis='Y', center=(x, 0, z)))
        else:
            objs.append(cyl(name + 'c', r * 1.0, z + r * 1.3, z + r * 1.8, mat, 24, center=(x, y, 0)))
    else:
        if axis == 'Z':
            objs += [cyl(name + 's', r * 0.5, y + r * 1.3, y + r * 3.4, mat, 16, axis='Y', center=(x, 0, z)),
                     cyl(name + 'w', r * 1.7, y + r * 3.4, y + r * 3.65, wheel_mat, 24, axis='Y', center=(x, 0, z), r_in=r * 1.4)]
        else:
            objs += [cyl(name + 's', r * 0.5, z + r * 1.3, z + r * 3.4, mat, 16, center=(x, y, 0)),
                     cyl(name + 'w', r * 1.7, z + r * 3.4, z + r * 3.65, wheel_mat, 24, center=(x, y, 0), r_in=r * 1.4)]
    return join(name, objs)


def _filter_housing(name, x, y, z0, h=0.45, r=0.08, mat='aluminium'):
    """Compressed-air filter: head, bowl and auto-drain."""
    return join(name, [box(name + 'h', (r * 2.6, r * 2.6, 0.08), (x, y, z0 + h), mat), cyl(name + 'bw', r, z0 + 0.06, z0 + h - 0.04, mat, 32, center=(x, y, 0)),
                       cyl(name + 'dr', r * 0.35, z0, z0 + 0.06, 'brass', 12, center=(x, y, 0))])


# =============================================================== EQ-309 Instrument air dryer (heated blower purge)
def instrument_air_dryer(out):
    m = _model('instrument_air_dryer', 'Instrument Air Dryer — Twin-Tower Heated Blower-Purge Desiccant Type')
    R, Z0, L = 0.25, 0.6, 1.4
    zt = Z0 + L + R * 0.5
    zb = Z0 - R * 0.5
    for k, x in enumerate((-0.5, 0.5)):
        v = vessel(f'tw{k}', R, L, 0.008, 'paint_blue', heads=('2:1', '2:1'), z0=Z0, center=(x, 0, 0))
        P(m, f'tower_{"ab"[k]}', f'Desiccant Tower {"AB"[k]} (' + ('drying — in service' if k == 0 else 'regenerating — heated purge') + ')', 'vessel', v, explode=(0, 0.6, 0), ref='iad_tower')
        bed = lathe(f'ds{k}', [(0.0, Z0 + 0.1), (R - 0.01, Z0 + 0.1), (R - 0.01, Z0 + 1.25), (0.0, Z0 + 1.25)], 'powder', 48, a0=0.0, a1=math.pi, center=(x, 0, 0), cap_mat='powder')
        P(m, f'desiccant_{"ab"[k]}', f'Activated Alumina / Molecular-Sieve Desiccant Bed {"AB"[k]}', 'media', bed, explode=(0, -0.5, 0), ref='iad_desiccant', section='keep')
        P(m, f'supports_{"ab"[k]}', f'Tower {"AB"[k]} Legs', 'structure', legs(f'lg{k}', R, 0.0, Z0, n=4, cx=x), explode=(0, 0, -0.3), ref='iad_tower', section='keep')
    # moisture (mass-transfer) front climbing tower A while it dries air
    mtz = lathe('mtz', [(0.0, Z0 + 0.12), (R - 0.008, Z0 + 0.12), (R - 0.008, Z0 + 0.26), (0.0, Z0 + 0.26)], 'water', 48, a0=0.0, a1=math.pi, center=(-0.5, 0, 0), cap_mat='water')
    pm = P(m, 'moisture_front', 'Moisture Front (mass-transfer zone) rising through the drying bed', 'fluid', mtz, explode=(0, -0.7, 0), ref='iad_desiccant', section='keep')
    keys_loop(m, pm, lambda t: (0, -0.004, 0.85 * t))
    mf = [hollow_pipe('bm', [(-0.9, 0, 0.25), (0.9, 0, 0.25)], 0.04, 'steel', 16), hollow_pipe('tm', [(-0.9, 0, zt + 0.15), (0.9, 0, zt + 0.15)], 0.04, 'steel', 16)]
    mf += [cyl(f'bt{k}', 0.04, 0.25, zb + 0.01, 'steel', 16, center=(x, 0, 0)) for k, x in enumerate((-0.5, 0.5))] + [cyl(f'tt{k}', 0.04, zt - 0.01, zt + 0.15, 'steel', 16, center=(x, 0, 0)) for k, x in enumerate((-0.5, 0.5))]
    mf += [_valve(f'sv{k}', (x, 0, 0.25), 'X', 0.04, 'paint_grey', wheel_mat='paint_blue_dark') for k, x in enumerate((-0.2, 0.2))]
    mf += [_valve(f'cv{k}', (x, 0, zt + 0.15), 'X', 0.04, 'paint_grey', kind='check') for k, x in enumerate((-0.2, 0.2))]
    P(m, 'switching_valves', 'Inlet/Exhaust Switching Valves (bottom) & Outlet Check Valves (top) with Manifolds', 'valves', mf, explode=(0, -0.4, 0), ref='iad_valves', section='keep')
    fl = [_filter_housing('pf', -1.15, 0, 0.35), _filter_housing('af', 1.15, 0, zt - 0.6), hollow_pipe('fi', [(-1.6, 0, 0.82), (-1.15, 0, 0.82), (-1.15, 0, 0.8)], 0.04, 'steel', 12),
          hollow_pipe('fo', [(-1.15, 0, 0.35), (-1.15, 0, 0.25), (-0.9, 0, 0.25)], 0.04, 'steel', 12, bend=0.04),
          hollow_pipe('ao', [(0.9, 0, zt + 0.15), (1.15, 0, zt + 0.15), (1.15, 0, zt - 0.11)], 0.04, 'steel', 12, bend=0.04), hollow_pipe('ap', [(1.15, 0, zt - 0.6), (1.15, 0, zt - 0.75), (1.65, 0, zt - 0.75)], 0.04, 'steel', 12, bend=0.04)]
    fl += [cyl('fls', 0.025, 0.0, 0.35, 'paint_grey', 12, center=(-1.15, 0, 0)), cyl('als', 0.025, 0.0, zt - 0.6, 'paint_grey', 12, center=(1.15, 0, 0))]
    P(m, 'filters', 'Coalescing Pre-Filter (oil/water) & Particulate After-Filter (desiccant dust)', 'filters', fl, explode=(0, -0.3, 0.3), ref='iad_filters', section='keep')
    bl = csg('bh', [cyl('bho', 0.18, 0.62, 0.86, 'paint_blue_dark', 48, axis='Y', center=(-0.3, 0, 0.4))], [cyl('bhi', 0.16, 0.64, 0.84, 'paint_blue_dark', 48, axis='Y', center=(-0.3, 0, 0.4))], 'paint_blue_dark')
    ht = join('ht', [cyl('hts', 0.09, -0.12, 0.7, 'stainless', 32, axis='X', center=(0, 0.74, 0.4), r_in=0.08), box('htt', (0.18, 0.12, 0.12), (0.3, 0.74, 0.52), 'paint_grey'),
                     cyl('htm', 0.08, 0.86, 1.1, 'paint_motor', 24, axis='Y', center=(-0.3, 0, 0.4))])
    rg = hollow_pipe('rg', [(0.7, 0.74, 0.4), (0.8, 0.74, 0.4), (0.8, 0.74, zt + 0.35), (0.5, 0.15, zt + 0.35), (0.5, 0.15, zt - 0.06)], 0.04, 'stainless', 12, bend=0.05)
    ex = [hollow_pipe('ex', [(0.5, 0.12, zb + 0.03), (0.5, 0.12, 0.1), (0.95, 0.12, 0.1)], 0.035, 'steel', 12, bend=0.04), cyl('sil', 0.08, 0.1, 0.55, 'paint_grey', 24, center=(0.95, 0.12, 0))]
    P(m, 'regeneration_system', 'Regeneration Blower, Electric Heater, Hot-Purge Line & Exhaust Silencer', 'regeneration', [bl, ht, rg] + ex, explode=(0, 0.5, 0.2), ref='iad_regen', section='keep')
    hel = [cyl(f'he{k}', 0.012, -0.08, 0.66, 'hot_glow', 8, axis='X', center=(0, 0.74 + 0.035 * math.cos(TAU * k / 3), 0.4 + 0.035 * math.sin(TAU * k / 3))) for k in range(3)]
    P(m, 'heater_elements', 'Heater Elements (purge air ≈ 150–200 °C)', 'regeneration', hel, explode=(0, 0.7, 0.3), ref='iad_regen', section='keep')
    _fan_rotor(m, 'blower_impeller', 'Regeneration Blower Impeller', (-0.3, 0.74, 0.4), 'Y', 0.14, 'iad_regen', revs=6)
    P(m, 'controls', 'Controller (dew-point dependent switching) & Dew-Point Analyser', 'controls', [box('cp', (0.35, 0.15, 0.5), (-1.6, 0.5, 1.2), 'paint_grey'), cyl('cps', 0.025, 0.0, 0.95, 'paint_grey', 12, center=(-1.6, 0.5, 0)),
                                                                                                  box('dpa', (0.1, 0.08, 0.14), (1.45, 0, zt - 0.62), 'paint_blue_dark')], explode=(-0.3, 0.3, 0), ref='iad_controls', section='keep')
    m.flow('wet_air', [(-1.7, 0, 0.82), (-1.15, 0, 0.82), (-1.15, 0, 0.25), (-0.5, 0, 0.25), (-0.5, 0.05, Z0), (-0.5, 0.05, Z0 + L), (-0.5, 0, zt + 0.15), (1.15, 0, zt + 0.15), (1.15, 0, zt - 0.75), (1.75, 0, zt - 0.75)],
           'air', 0.018, 0.4)
    m.flow('hot_purge', [(-0.3, 1.15, 0.4), (-0.3, 0.74, 0.4), (0.8, 0.74, 0.4), (0.8, 0.74, zt + 0.35), (0.5, 0.15, zt + 0.35), (0.5, 0.1, Z0 + L), (0.5, 0.1, Z0), (0.5, 0.12, 0.1), (0.95, 0.12, 0.6)],
           'flue_gas', 0.016, 0.4)
    _bands_z(m, [(Z0 + 0.95, Z0 + 1.3, 8), (Z0 + 0.55, Z0 + 0.95, 6), (Z0 + 0.1, Z0 + 0.55, 3)], R, 'Heat drives the water off the desiccant',
             'In the regenerating tower, ambient air from the blower is heated (≈ 150–200 °C) and passed down through the bed, opposite to the drying flow, so the wettest desiccant at the inlet end is heated last '
             'and the outlet end stays driest. The heat front moves through the bed, then the tower is cooled and repressurised before switching. Compared with heatless dryers (≈ 15 % purge of dried air), '
             'blower-purge dryers use little or no compressed air. Instrument air is typically dried to a pressure dew point of about −40 °C (ISO 8573-1 class 2).', kind='temperature', cx=0.5)
    return m.export(out)


# =============================================================== EQ-310 Air receiver & refrigerated dryer package
def air_receiver_dryer_package(out):
    m = _model('air_receiver_dryer_package', 'Air Receiver with Refrigerated Dryer & Filtration Package')
    R, Z0, L = 0.45, 0.55, 1.8
    zt = Z0 + L + R * 0.5
    P(m, 'receiver', 'Vertical Air Receiver (pressure vessel)', 'vessel', vessel('rv', R, L, 0.01, 'paint_grey', heads=('2:1', '2:1'), z0=Z0), explode=(0, 0.7, 0), ref='ard_receiver')
    P(m, 'receiver_legs', 'Receiver Legs', 'structure', legs('lg', R, 0.0, Z0 + 0.05, n=3), explode=(0, 0, -0.3), ref='ard_receiver', section='keep')
    cd = lathe('cd', [(0.0, Z0 - R * 0.5 + 0.01), (0.12, Z0 - R * 0.47), (0.25, Z0 - R * 0.38), (0.0, Z0 - R * 0.38)], 'water', 32, a0=0.0, a1=math.pi, cap_mat='water')
    pc = P(m, 'condensate', 'Condensate collecting in the receiver bottom', 'fluid', cd, explode=(0, -0.4, -0.2), ref='ard_drain', section='keep', pivot=(0, 0, Z0 - R * 0.5))
    keys_loop(m, pc, lambda t: (1, 1, 0.3 + 0.7 * (t / 0.8 if t < 0.8 else (1 - t) / 0.2)), 'scale')
    acc = [nozzle('in', (-R, 0, Z0 + 0.3), (-1, 0, 0), 0.05, 0.4), hollow_pipe('ot', [(0, 0, zt - 0.01), (0, 0, zt + 0.2), (1.25, 0, zt + 0.2), (1.25, 0, 1.36)], 0.05, 'steel', 16, bend=0.08),
           join('sv', [cyl('svb', 0.04, zt - 0.02, zt + 0.12, 'brass', 16, center=(0.2, 0, 0)), cyl('svc', 0.03, zt + 0.12, zt + 0.25, 'paint_red', 16, center=(0.2, 0, 0))]),
           pressure_gauge('pg', (-0.2, -0.05, zt + 0.02), r=0.05, facing=(0, -1, 0)), box('mw', (0.3, 0.06, 0.4), (0, R + 0.02, Z0 + 0.6), 'paint_grey'),
           join('ad', [hollow_pipe('adp', [(0, 0, Z0 - R * 0.5), (0, 0, 0.12), (0.3, 0, 0.12)], 0.015, 'steel', 8, bend=0.02), box('adb', (0.12, 0.1, 0.12), (0.36, 0, 0.12), 'paint_blue_dark')])]
    P(m, 'receiver_fittings', 'Inlet (low) & Outlet (high), Safety Valve, Pressure Gauge, Inspection Opening & Zero-Loss Auto Drain', 'fittings', acc, explode=(0, 0, 0.4), ref='ard_fittings', section='keep')
    cab = csg('cab', [box('cbo', (1.0, 0.7, 1.3), (1.6, 0, 0.7), 'paint_blue')], [box('cbi', (0.96, 0.66, 1.26), (1.6, 0, 0.7), 'paint_blue'), box('cbg', (0.04, 0.5, 0.5), (2.1, 0, 0.5), 'paint_blue')], 'paint_blue')
    P(m, 'dryer_cabinet', 'Refrigerated Dryer Cabinet (front panel removed in cutaway)', 'casing', cab, explode=(0, 0.6, 0), ref='ard_dryer')
    hx = [box('aah', (0.3, 0.3, 0.45), (1.33, 0.1, 0.98), 'aluminium'), box('evp', (0.3, 0.3, 0.45), (1.75, 0.1, 0.98), 'copper'),
          cyl('sep', 0.08, 0.35, 0.72, 'stainless', 24, center=(1.75, 0.1, 0)), hollow_pipe('sx', [(1.75, 0.1, 0.76), (1.75, 0.1, 0.72)], 0.04, 'aluminium', 12)]
    P(m, 'heat_exchangers', 'Air-to-Air Pre-Cooler/Re-Heater, Evaporator (air-to-refrigerant) & Moisture Separator', 'heat_exchange', hx, explode=(0, -0.5, 0.3), ref='ard_hx', section='keep')
    rf = [cyl('cmp', 0.13, 0.08, 0.42, 'steel_dark', 32, center=(1.35, 0.1, 0)), box('cnd', (0.05, 0.55, 0.5), (2.03, 0, 0.5), 'copper'),
          hollow_pipe('rl', [(1.35, 0.25, 0.3), (2.0, 0.25, 0.3), (2.0, 0.25, 0.78), (1.9, 0.25, 0.98), (1.75, 0.25, 0.98)], 0.012, 'copper', 8, bend=0.03),
          hollow_pipe('rs', [(1.75, 0.25, 0.98), (1.55, 0.25, 0.98), (1.55, 0.25, 0.4), (1.45, 0.1, 0.4)], 0.014, 'copper', 8, bend=0.03), box('xv', (0.06, 0.06, 0.08), (1.95, 0.25, 0.86), 'brass')]
    P(m, 'refrigeration_circuit', 'Refrigeration Circuit: Hermetic Compressor, Air-Cooled Condenser, Expansion Valve & Lines', 'refrigeration', rf, explode=(0, -0.3, -0.2), ref='ard_refrig', section='keep')
    _fan_rotor(m, 'condenser_fan', 'Condenser Fan', (1.93, 0, 0.5), 'X', 0.2, 'ard_refrig', revs=6)
    droplets(m, 'drain_drops', 'Condensed water drained from the separator', 1.74, 1.76, 0.33, 0.06, n=4, mat='water', y=0.1, r=0.012)
    fl = [_filter_housing(f'f{k}', 0.75, 0.55, 0.45, h=0.4) for k in range(1)] + [_filter_housing('f2', 0.95, 0.55, 0.45, h=0.4),
          hollow_pipe('dto', [(1.1, 0.2, 1.1), (0.95, 0.2, 1.1), (0.95, 0.55, 0.85)], 0.035, 'steel', 12, bend=0.05),
          hollow_pipe('ff', [(0.95, 0.55, 0.45), (0.95, 0.55, 0.38), (0.75, 0.55, 0.38), (0.75, 0.55, 0.45)], 0.03, 'steel', 12, bend=0.03),
          hollow_pipe('po', [(0.75, 0.55, 0.85), (0.75, 0.55, 1.05), (0.75, 1.1, 1.05)], 0.035, 'steel', 12, bend=0.04)]
    P(m, 'filters', 'Coalescing Filter (oil aerosols ≈ 0.01 mg/m³) & Dust Filter with Auto Drains', 'filters', fl, explode=(-0.2, 0.4, 0.2), ref='ard_filters', section='keep')
    m.flow('compressed_air', [(-R - 0.5, 0, Z0 + 0.3), (-0.1, 0.05, Z0 + 0.4), (0, 0.05, zt - 0.1), (0, 0, zt + 0.2), (1.25, 0, zt + 0.2), (1.25, 0.1, 1.2), (1.75, 0.1, 1.0), (1.75, 0.1, 0.55),
                               (1.33, 0.1, 0.85), (1.1, 0.2, 1.1), (0.95, 0.55, 0.85), (0.95, 0.55, 0.38), (0.75, 0.55, 0.38), (0.75, 0.55, 1.05), (0.75, 1.2, 1.05)], 'air', 0.016, 0.4)
    m.flow('refrigerant', [(1.35, 0.25, 0.3), (2.0, 0.25, 0.3), (2.0, 0.25, 0.78), (1.75, 0.25, 0.98), (1.55, 0.25, 0.98), (1.55, 0.25, 0.4), (1.4, 0.15, 0.4)], 'flow_suction', 0.01, 0.3)
    _bands_x(m, [(1.18, 1.48, 5), (1.6, 1.9, 1)], 0.32, 0.47, 0.98, 'Chill to condense, re-heat to protect', 'Warm saturated air is pre-cooled by the outgoing cold air, then chilled in the evaporator to ≈ 3 °C so the water '
             'condenses and is drained. The cold dry air is re-heated in the air-to-air exchanger before leaving, which saves refrigeration energy and prevents pipe sweating. Pressure dew point ≈ +3 °C '
             '(ISO 8573-1 class 4) — fine for general plant air; instrument air needing −40 °C uses a desiccant dryer. The receiver buffers demand, settles condensate and smooths compressor cycling.',
             kind='temperature', cy=0.1)
    return m.export(out)


# =============================================================== EQ-311 Nitrogen generation (PSA)
def nitrogen_generation_system(out):
    m = _model('nitrogen_generation_system', 'Nitrogen Generation System — Pressure Swing Adsorption (Carbon Molecular Sieve)')
    R, Z0, L = 0.22, 0.6, 1.3
    zt = Z0 + L + R * 0.5
    zb = Z0 - R * 0.5
    for k, x in enumerate((-0.45, 0.15)):
        P(m, f'adsorber_{"ab"[k]}', f'Adsorber {"AB"[k]} (' + ('adsorbing at pressure' if k == 0 else 'depressurised — regenerating') + ')', 'vessel',
          vessel(f'ad{k}', R, L, 0.008, 'paint_green', heads=('2:1', '2:1'), z0=Z0, center=(x, 0, 0)), explode=(0, 0.6, 0), ref='n2_adsorber')
        cms = lathe(f'cm{k}', [(0.0, Z0 + 0.05), (R - 0.01, Z0 + 0.05), (R - 0.01, Z0 + 1.2), (0.0, Z0 + 1.2)], 'carbon', 48, a0=0.0, a1=math.pi, center=(x, 0, 0), cap_mat='carbon')
        P(m, f'cms_{"ab"[k]}', f'Carbon Molecular Sieve Bed {"AB"[k]}', 'media', cms, explode=(0, -0.5, 0), ref='n2_cms', section='keep')
        P(m, f'legs_{"ab"[k]}', f'Adsorber {"AB"[k]} Legs', 'structure', legs(f'lg{k}', R, 0.0, Z0, n=3, cx=x), explode=(0, 0, -0.3), ref='n2_adsorber', section='keep')
    fr = lathe('o2f', [(0.0, Z0 + 0.1), (R - 0.008, Z0 + 0.1), (R - 0.008, Z0 + 0.2), (0.0, Z0 + 0.2)], 'paint_red', 48, a0=0.0, a1=math.pi, center=(-0.45, 0, 0), cap_mat='paint_red')
    pf = P(m, 'oxygen_front', 'Oxygen Adsorption Front (O₂ held by the CMS; N₂ passes)', 'fluid', fr, explode=(0, -0.7, 0), ref='n2_cms', section='keep')
    keys_loop(m, pf, lambda t: (0, -0.004, 0.8 * t))
    vs = [hollow_pipe('bm', [(-0.85, 0, 0.25), (0.55, 0, 0.25)], 0.035, 'stainless', 12), hollow_pipe('tm', [(-0.85, 0, zt + 0.15), (0.75, 0, zt + 0.15)], 0.03, 'stainless', 12)]
    vs += [cyl(f'b{k}', 0.035, 0.25, zb + 0.01, 'stainless', 12, center=(x, 0, 0)) for k, x in enumerate((-0.45, 0.15))] + [cyl(f't{k}', 0.03, zt - 0.01, zt + 0.15, 'stainless', 12, center=(x, 0, 0)) for k, x in enumerate((-0.45, 0.15))]
    vs += [_valve(f'pv{k}', (x, 0, 0.25), 'X', 0.035, 'paint_grey', wheel_mat='paint_blue_dark') for k, x in enumerate((-0.7, -0.15, 0.4))]
    vs += [_valve(f'tv{k}', (x, 0, zt + 0.15), 'X', 0.03, 'paint_grey', wheel_mat='paint_blue_dark') for k, x in enumerate((-0.15, 0.45))]
    vs += [hollow_pipe('ex', [(0.55, 0, 0.25), (0.75, 0, 0.25), (0.75, 0, 0.12)], 0.035, 'stainless', 12, bend=0.03), cyl('sl', 0.09, 0.0, 0.12, 'paint_grey', 24, center=(0.75, 0, 0))]
    P(m, 'valve_manifold', 'Pneumatic Valve Manifolds (feed / exhaust / equalise / product) & Exhaust Silencer', 'valves', vs, explode=(0, -0.4, 0), ref='n2_valves', section='keep')
    pre = [_filter_housing('fa', -1.3, 0, 0.35), _filter_housing('fb', -1.05, 0, 0.35), cyl('fs1', 0.02, 0.0, 0.35, 'paint_grey', 8, center=(-1.3, 0, 0)), cyl('fs2', 0.02, 0.0, 0.35, 'paint_grey', 8, center=(-1.05, 0, 0)),
           hollow_pipe('fi', [(-1.8, 0, 0.82), (-1.3, 0, 0.82), (-1.3, 0, 0.8)], 0.035, 'steel', 12), hollow_pipe('fj', [(-1.3, 0, 0.35), (-1.3, 0, 0.28), (-1.05, 0, 0.28), (-1.05, 0, 0.35)], 0.03, 'steel', 12, bend=0.03),
           hollow_pipe('fk', [(-1.05, 0, 0.8), (-1.05, 0, 0.9), (-0.92, 0, 0.9), (-0.92, 0, 0.25), (-0.85, 0, 0.25)], 0.03, 'steel', 12, bend=0.03)]
    P(m, 'air_treatment', 'Feed-Air Treatment: Coalescing Filter & Activated-Carbon Filter (protect the CMS from oil)', 'filters', pre, explode=(-0.3, -0.3, 0), ref='n2_filters', section='keep')
    bv = vessel('bv', 0.32, 1.1, 0.008, 'paint_grey', heads=('2:1', '2:1'), z0=0.55, center=(1.25, 0, 0))
    P(m, 'nitrogen_buffer', 'Nitrogen Buffer Vessel (smooths the cyclic product flow)', 'vessel', [bv, legs('bl', 0.32, 0.0, 0.6, n=3, cx=1.25),
                                                                                        hollow_pipe('bi', [(0.75, 0, zt + 0.15), (1.25, 0, zt + 0.15), (1.25, 0, 0.55 + 1.1 + 0.15)], 0.03, 'stainless', 12, bend=0.04)],
      explode=(0.4, 0, 0), ref='n2_buffer')
    pa = [hollow_pipe('po', [(1.25 + 0.32, 0, 0.9), (2.0, 0, 0.9)], 0.03, 'stainless', 12), _valve('fcv', (1.8, 0, 0.9), 'X', 0.03, 'paint_grey', wheel_mat='paint_blue_dark'),
          box('o2a', (0.25, 0.12, 0.35), (1.85, 0.4, 1.3), 'paint_blue_dark'), cyl('o2s', 0.02, 0.0, 1.12, 'paint_grey', 8, center=(1.85, 0.4, 0)),
          hollow_pipe('smp', [(1.7, 0, 0.92), (1.7, 0.4, 0.92), (1.7, 0.4, 1.3), (1.72, 0.4, 1.3)], 0.006, 'stainless', 6, bend=0.02), box('ofs', (0.06, 0.06, 0.08), (1.65, 0, 1.0), 'paint_red')]
    P(m, 'product_controls', 'Product Flow Control, Oxygen Analyser (ppm / %) & Off-Spec Vent Valve', 'controls', pa, explode=(0.3, 0.3, 0.2), ref='n2_controls', section='keep')
    particles_path(m, 'oxygen_molecules', 'O₂ molecules (small, fast) trapped in the CMS pores', lambda i, s: (-0.45 + 0.15 * math.cos(i * 1.7), 0.08 + 0.05 * (i % 3), Z0 + 0.1 + (0.2 + 0.7 * ((i * 0.37) % 1)) * min(1.0, 1.4 * s)), 10,
                   mat='paint_red', r=0.014)
    particles_path(m, 'nitrogen_molecules', 'N₂ molecules passing through to the product', lambda i, s: (-0.45 + 0.12 * math.cos(i * 2.3), 0.1, Z0 + 0.05 + (L + 0.2) * ((s + i / 8) % 1)), 8, mat='paint_blue', r=0.014)
    m.flow('feed_air', [(-1.9, 0, 0.82), (-1.3, 0, 0.82), (-1.3, 0, 0.28), (-1.05, 0, 0.9), (-0.92, 0, 0.25), (-0.45, 0, 0.25), (-0.45, 0.05, Z0 + 0.1), (-0.45, 0.05, Z0 + L)], 'air', 0.016, 0.4)
    m.flow('nitrogen', [(-0.45, 0, zt + 0.15), (1.25, 0, zt + 0.15), (1.25, 0.05, 1.2), (1.25 + 0.32, 0, 0.9), (2.1, 0, 0.9)], 'flow_discharge', 0.016, 0.4)
    m.flow('o2_rich_exhaust', [(0.15, 0.05, Z0 + 1.0), (0.15, 0.05, Z0), (0.15, 0, 0.25), (0.75, 0, 0.25), (0.75, 0, 0.0)], 'exhaust', 0.014, 0.3)
    _press(m, [cyl('pa', R + 0.04, Z0, Z0 + L, 'pressure_8', 48, center=(-0.45, 0, 0), r_in=R + 0.02), cyl('pb', R + 0.04, Z0, Z0 + L, 'pressure_1', 48, center=(0.15, 0, 0), r_in=R + 0.02)],
           'Kinetic separation by pressure swing', 'Carbon molecular sieve separates by speed, not equilibrium: O₂ molecules (≈ 0.346 nm) diffuse into the pores much faster than N₂ (≈ 0.364 nm). With feed air at ≈ 7–10 bar(g) '
           'the CMS takes up O₂ in the short cycle (≈ 60 s) and N₂ passes through as product (purity typically 95 – 99.999 %). The tower is then depressurised to atmosphere, releasing the O₂-rich gas, while the '
           'other tower takes over; a pressure-equalisation step between towers saves air.')
    return m.export(out)


# =============================================================== EQ-312 Nitrogen storage vessel (cryogenic)
def nitrogen_storage_vessel(out):
    m = _model('nitrogen_storage_vessel', 'Liquid Nitrogen Storage Vessel (Vacuum-Insulated) with Ambient Vaporiser')
    Ro, Ri, Z0, L = 0.6, 0.5, 0.75, 2.6
    P(m, 'outer_vessel', 'Outer Vessel / Vacuum Jacket (carbon steel)', 'vessel', vessel('ov', Ro, L, 0.008, 'paint_grey', heads=('2:1', '2:1'), z0=Z0), explode=(0, 0.8, 0), ref='ln_outer')
    P(m, 'inner_vessel', 'Inner Vessel (austenitic stainless steel, rated for −196 °C)', 'vessel', vessel('iv', Ri, L - 0.2, 0.006, 'stainless', heads=('2:1', '2:1'), z0=Z0 + 0.1), explode=(0, 0.45, 0.2), ref='ln_inner')
    ins = csg('ins', [lathe('inso', [(0.0, Z0 - Ro * 0.5 + 0.01), (Ro - 0.01, Z0), (Ro - 0.01, Z0 + L), (0.0, Z0 + L + Ro * 0.5 - 0.01)], 'insulation', 48, a0=0.0, a1=math.pi)],
              [lathe('insi', [(0.0, Z0 + 0.1 - Ri * 0.5 - 0.005), (Ri + 0.005, Z0 + 0.1), (Ri + 0.005, Z0 + L - 0.1), (0.0, Z0 + L - 0.1 + Ri * 0.5 + 0.005)], 'insulation', 48, a0=-0.1, a1=math.pi + 0.1)], 'insulation')
    P(m, 'annulus_insulation', 'Annular Space: Perlite (or multilayer insulation) under High Vacuum', 'insulation', ins, explode=(0, 0.6, 0.1), ref='ln_annulus', section='keep')
    lq = liquid_v('lin', Ri - 0.008, Z0 + 0.1, Z0 + 1.9, head='2:1', mat='water', cx=0.0)
    pl = P(m, 'liquid_nitrogen', 'Liquid Nitrogen (−196 °C at 1 atm; stored at ≈ 2–17 bar)', 'fluid', lq, explode=(0, -0.5, 0), ref='ln_inner', section='keep')
    animate_level(m, pl, Z0 + 0.4, -0.6, lambda t: t)
    P(m, 'legs', 'Support Legs', 'structure', legs('lg', Ro, 0.0, Z0 + 0.05, n=4), explode=(0, 0, -0.3), ref='ln_outer', section='keep')
    pb = [hollow_pipe('pbo', [(0.0, 0.0, Z0 - Ro * 0.5), (0.0, -0.0, 0.3), (0.8, 0.0, 0.3)], 0.025, 'stainless', 12, bend=0.04)]
    for k in range(3):
        pb.append(cyl(f'pbc{k}', 0.025, 0.3, 1.4, 'aluminium', 12, center=(0.8 + 0.12 * k, 0.6, 0)))
        pb += [box(f'pbf{k}{j}', (0.09, 0.006, 1.1), (0.8 + 0.12 * k, 0.6, 0.85), 'aluminium') if j == 0 else box(f'pbf{k}{j}', (0.006, 0.09, 1.1), (0.8 + 0.12 * k, 0.6, 0.85), 'aluminium') for j in range(2)]
    pb += [hollow_pipe('pbr', [(0.8, 0.0, 0.3), (0.8, 0.6, 0.3)], 0.02, 'stainless', 12), hollow_pipe('pbt', [(1.04, 0.6, 1.4), (1.04, 0.6, Z0 + L + Ro * 0.5 + 0.12), (0.12, 0.6, Z0 + L + Ro * 0.5 + 0.12), (0.12, 0.0, Z0 + L + Ro * 0.5 + 0.12), (0.12, 0.0, Z0 + L + Ro * 0.5 - 0.02)], 0.02, 'stainless', 10, bend=0.05),
           box('pbv', (0.08, 0.08, 0.1), (0.85, 0.6, 1.5), 'brass')]
    P(m, 'pressure_builder', 'Pressure-Building Coil & Regulator (vaporises a little liquid to hold tank pressure)', 'pressure_control', pb, explode=(0.3, 0.3, 0), ref='ln_pbc', section='keep')
    vp = []
    for i in range(2):
        for j in range(2):
            x, y = 1.7 + 0.32 * i, -0.2 + 0.32 * j
            vp.append(cyl(f'vt{i}{j}', 0.025, 0.3, 2.2, 'aluminium', 12, center=(x, y, 0)))
            for a in range(4):
                vp.append(rotate(box(f'vf{i}{j}{a}', (0.13, 0.008, 1.85), (x + 0.065, y, 1.25), 'aluminium'), TAU * a / 4 + math.pi / 4, 'Z', (x, y, 0)))
    vp += [hollow_pipe('vh0', [(1.7, -0.2, 0.3), (2.02, -0.2, 0.3), (2.02, 0.12, 0.3), (1.7, 0.12, 0.3)], 0.025, 'aluminium', 12, bend=0.04), hollow_pipe('vh1', [(1.7, -0.2, 2.2), (2.02, -0.2, 2.2), (2.02, 0.12, 2.2), (1.7, 0.12, 2.2)], 0.025, 'aluminium', 12, bend=0.04),
           box('vfr', (0.8, 0.8, 0.06), (1.86, -0.04, 0.03), 'paint_grey')] + [cyl(f'vl{k}', 0.03, 0.06, 0.3, 'paint_grey', 12, center=(x, y, 0)) for k, (x, y) in enumerate(((1.6, -0.3), (2.12, -0.3), (1.6, 0.22), (2.12, 0.22)))]
    P(m, 'ambient_vaporiser', 'Ambient-Air Vaporiser (star-finned aluminium tubes)', 'vaporiser', vp, explode=(0.6, 0, 0), ref='ln_vaporiser', section='keep')
    fr = [cyl(f'fr{i}{j}', 0.05, 0.32, 0.95, 'foam', 16, center=(1.7 + 0.32 * i, -0.2 + 0.32 * j, 0)) for i in range(2) for j in range(2)]
    pfr = P(m, 'frost', 'Frost building on the cold lower tubes', 'fluid', fr, explode=(0.6, -0.3, 0), ref='ln_vaporiser', section='keep', pivot=(1.86, -0.04, 0.32))
    keys_loop(m, pfr, lambda t: (1, 1, 0.6 + 0.4 * math.sin(math.pi * t)), 'scale')
    pp = [hollow_pipe('lo', [(0.0, 0.0, Z0 - Ro * 0.5), (0.0, -0.25, Z0 - Ro * 0.5), (0.0, -0.25, 0.18), (1.7, -0.2, 0.18), (1.7, -0.2, 0.3)], 0.025, 'stainless', 12, bend=0.04),
          hollow_pipe('go', [(1.7, 0.12, 2.2), (1.7, 0.12, 2.45), (2.6, 0.12, 2.45), (2.6, 0.12, 1.2), (3.0, 0.12, 1.2)], 0.03, 'stainless', 12, bend=0.05), _valve('rg', (2.6, 0.12, 1.6), 'Z', 0.04, 'brass', wheel_mat='paint_blue_dark'),
          _valve('ev', (0.0, -0.25, 0.45), 'Z', 0.03, 'brass', wheel_mat='paint_blue_dark'), hollow_pipe('fl', [(-0.3, -0.3, Z0 - 0.2), (-0.3, -0.3, 0.9), (-0.8, -0.3, 0.9)], 0.025, 'stainless', 12, bend=0.04)]
    P(m, 'piping_valves', 'Liquid Withdrawal Valve, Fill Connection, Gas Line & Final Line Regulator', 'piping', pp, explode=(0.2, -0.4, 0), ref='ln_piping', section='keep')
    sf = [join('sv', [cyl(f'svb{k}', 0.03, Z0 + L + 0.3, Z0 + L + 0.45, 'brass', 12, center=(-0.15 + 0.3 * k, 0.0, 0)) for k in range(2)] + [cyl('svh', 0.025, Z0 + L + 0.15, Z0 + L + 0.3, 'stainless', 12, center=(0.0, 0.0, 0)),
                                                                                                                                        cyl('svx', 0.025, -0.15, 0.15, 'stainless', 12, axis='X', center=(0, 0.0, Z0 + L + 0.3))]),
          box('gp', (0.3, 0.04, 0.35), (-0.9, -0.3, 1.5), 'paint_grey'), cyl('gps', 0.025, 0.0, 1.33, 'paint_grey', 12, center=(-0.9, -0.3, 0)), box('dpg', (0.12, 0.06, 0.12), (-0.97, -0.35, 1.55), 'paint_blue_dark'),
          pressure_gauge('pgg', (-0.82, -0.33, 1.55), r=0.05, facing=(0, -1, 0)), hollow_pipe('gl', [(-0.5, -0.3, 0.6), (-0.9, -0.3, 0.6), (-0.9, -0.3, 1.33)], 0.008, 'copper', 6, bend=0.02),
          join('bd', [cyl('bds', 0.02, Z0 + L + 0.1, Z0 + L + 0.32, 'stainless', 8, center=(0.3, 0.3, 0)), cyl('bdd', 0.04, Z0 + L + 0.32, Z0 + L + 0.36, 'paint_red', 16, center=(0.3, 0.3, 0))])]
    P(m, 'safety_instruments', 'Dual Safety Relief Valves (change-over), Annulus Burst Disc, Level (ΔP) Gauge & Pressure Gauge', 'safety', sf, explode=(0, 0, 0.5), ref='ln_safety', section='keep')
    m.flow('liquid_out', [(0.0, 0.05, Z0 + 0.3), (0.0, -0.25, Z0 - Ro * 0.5), (0.0, -0.25, 0.18), (1.7, -0.2, 0.18), (1.7, -0.2, 2.1)], 'flow_suction', 0.016, 0.4)
    m.flow('gas_to_plant', [(1.7, 0.12, 2.2), (1.7, 0.12, 2.45), (2.6, 0.12, 2.45), (2.6, 0.12, 1.2), (3.1, 0.12, 1.2)], 'air', 0.016, 0.4)
    m.flow('pressure_build', [(0.0, 0.0, Z0 - Ro * 0.5), (0.0, 0.0, 0.3), (0.8, 0.6, 0.3), (0.92, 0.6, 1.4), (1.04, 0.6, Z0 + L + Ro * 0.5 + 0.12), (0.12, 0.6, Z0 + L + Ro * 0.5 + 0.12), (0.12, 0.0, Z0 + L + Ro * 0.5)], 'steam', 0.012, 0.3)
    m.overlay('temperature', join('temperature', [cyl('ti', Ri + 0.03, Z0 + 0.1, Z0 + L - 0.1, 'pressure_0', 48, r_in=Ri + 0.015)] +
                                  [cyl(f'tv{k}', 0.06, 0.3 + 0.48 * k, 0.78 + 0.48 * k, f'pressure_{lev}', 16, center=(1.7, -0.2, 0), r_in=0.04) for k, lev in enumerate((0, 3, 5, 7))]),
              'From −196 °C liquid to ambient gas', 'Liquid nitrogen boils at −196 °C (77 K). The vacuum-perlite annulus keeps heat leak so low that daily boil-off is only a fraction of a percent of capacity. '
              'Withdrawn liquid warms in the finned ambient vaporiser (heat from the air; frost forms on the cold lower tubes) and leaves close to ambient temperature. 1 litre of liquid gives ≈ 0.69 Nm³ of gas, '
              'so a closed-in liquid line must always have a relief device (trapped liquid → very high pressure).', split=True)
    return m.export(out)


# =============================================================== EQ-313 Steam distribution header
def steam_distribution_header(out):
    m = _model('steam_distribution_header', 'Steam Distribution Header with Branch Take-offs, Drip Leg Trap Station & PRV Station')
    ZH, X0, X1, r = 1.6, -2.2, 2.0, 0.1
    hd = csg('hd', [cyl('hdo', r, X0, X1 + 0.02, 'steel', 48, axis='X', center=(0, 0, ZH))], [cyl('hdi', r - 0.008, X0 - 0.01, X1, 'steel', 48, axis='X', center=(0, 0, ZH))], 'steel')
    dl = csg('dl', [cyl('dlo', r, 0.7, ZH, 'steel', 48, center=(1.8, 0, 0))], [cyl('dli', r - 0.008, 0.72, ZH, 'steel', 48, center=(1.8, 0, 0))], 'steel')
    P(m, 'header', 'Steam Header (sloped ≈ 1:100 toward the drip leg) & Full-Bore Drip Leg / Dirt Pocket', 'piping', [hd, dl, cyl('ec', r + 0.012, X1, X1 + 0.03, 'steel', 48, axis='X', center=(0, 0, ZH))],
      explode=(0, 0.5, 0), ref='sh_header')
    ins = csg('ins', [cyl('iso', r + 0.07, X0 + 0.3, X1 - 0.3, 'cladding', 48, axis='X', center=(0, 0, ZH))], [cyl('isi', r + 0.002, X0, X1, 'cladding', 48, axis='X', center=(0, 0, ZH))], 'cladding')
    P(m, 'insulation', 'Insulation & Aluminium Cladding', 'insulation', ins, explode=(0, 0.8, 0.2), ref='sh_insulation')
    sp = []
    for k, x in enumerate((-1.6, -0.2, 1.2)):
        sp += [cyl(f'sc{k}', 0.05, 0.0, ZH - r - 0.12, 'paint_grey', 16, center=(x, 0, 0)), box(f'sb{k}', (0.12, 0.5, 0.06), (x, 0, ZH - r - 0.12), 'paint_grey'),
               box(f'ss{k}', (0.2, 0.08, 0.05), (x, 0, ZH - r - 0.07), 'steel_dark')]
    P(m, 'supports', 'Pipe Supports with Shoes & Guides (allow thermal expansion)', 'structure', sp, explode=(0, 0, -0.3), ref='sh_supports', section='keep')
    br = []
    for k, x in enumerate((-1.2, 1.0)):
        br += [hollow_pipe(f'br{k}', [(x, 0, ZH + r - 0.01), (x, 0, 2.25), (x, 0.3, 2.25), (x, 1.4, 2.25)], 0.05, 'steel', 16, bend=0.08), _valve(f'bv{k}', (x, 0.75, 2.25), 'Y', 0.05, 'cast_iron')]
    P(m, 'branch_takeoffs', 'Branch Take-offs from the TOP of the Header (dry steam) with Isolation Valves', 'piping', br, explode=(0, 0.4, 0.3), ref='sh_branches', section='keep')
    pr = [hollow_pipe('pr', [(0.0, 0, ZH + r - 0.01), (0.0, 0, 2.25), (0.0, 0.3, 2.25), (0.0, 0.55, 2.25)], 0.05, 'steel', 16, bend=0.08), _valve('pi', (0.0, 0.4, 2.25), 'Y', 0.05, 'cast_iron'),
          join('prv', [cyl('prb', 0.08, 0.5, 0.74, 'cast_iron', 24, axis='Y', center=(0, 0, 2.25)), cyl('prs', 0.03, 2.25, 2.45, 'steel', 12, center=(0, 0.62, 0)), lathe('prd', [(0.0, 2.45), (0.14, 2.45), (0.14, 2.5), (0.0, 2.56)], 'paint_red', 32, center=(0, 0.62, 0)),
                       hollow_pipe('ppl', [(0.0, 0.85, 2.25), (0.0, 0.85, 2.48), (0.0, 0.76, 2.48)], 0.008, 'copper', 6, bend=0.02)]),
          hollow_pipe('pd', [(0.0, 0.74, 2.25), (0.0, 1.5, 2.25)], 0.075, 'steel', 16), join('psv', [cyl('psb', 0.06, 2.3, 2.42, 'paint_red', 16, center=(0, 1.0, 0)), cyl('psc', 0.035, 2.42, 2.6, 'paint_red', 16, center=(0, 1.0, 0))]),
          pressure_gauge('pg1', (0.0, 0.3, 2.37), r=0.04, facing=(-1, 0, 0)), pressure_gauge('pg2', (0.0, 1.2, 2.37), r=0.04, facing=(-1, 0, 0))]
    P(m, 'prv_station', 'Pressure-Reducing Station: Isolation, Pilot-Operated PRV, Downstream Safety Valve & Gauges', 'pressure_control', pr, explode=(0, 0.5, 0.5), ref='sh_prv', section='keep')
    ts = [hollow_pipe('tl', [(1.8 + r, 0, 0.95), (2.75, 0, 0.95), (2.75, 0, 0.45), (3.2, 0, 0.45)], 0.025, 'steel', 12, bend=0.04), _valve('ti', (2.05, 0, 0.95), 'X', 0.025, 'cast_iron'),
          join('st', [cyl('stb', 0.04, 2.2, 2.32, 'cast_iron', 16, axis='X', center=(0, 0, 0.95)), rotate(cyl('sts', 0.03, 0.8, 0.95, 'cast_iron', 16, center=(2.27, 0, 0)), math.radians(35), 'Y', (2.27, 0, 0.95))]),
          join('tp', [lathe('tpb', [(0.0, 0.8), (0.08, 0.8), (0.08, 1.02), (0.0, 1.02)], 'steel_dark', 32, center=(2.47, 0, 0))]), _valve('tc', (2.65, 0, 0.95), 'X', 0.025, 'cast_iron', kind='check'),
          box('tv', (0.04, 0.04, 0.08), (2.57, 0, 0.88), 'brass'), hollow_pipe('dp', [(1.8, 0, 0.7), (1.8, 0, 0.55)], 0.03, 'steel', 12), _valve('bd', (1.8, 0, 0.5), 'Z', 0.03, 'cast_iron')]
    P(m, 'trap_station', 'Drip-Leg Trap Station: Isolation Valve, Strainer, Steam Trap, Test Valve, Check Valve & Blowdown', 'trap_station', ts, explode=(0.3, -0.3, 0), ref='sh_trap', section='keep')
    P(m, 'main_valve', 'Main Steam Stop Valve (from boiler) & End Air Vent', 'valves', [_valve('mv', (X0 + 0.25, 0, ZH), 'X', 0.1, 'cast_iron'), box('av', (0.06, 0.06, 0.1), (X1 - 0.05, 0, ZH + r + 0.05), 'brass')],
      explode=(-0.3, 0, 0.3), ref='sh_header', section='keep')
    particles_path(m, 'condensate_film', 'Condensate running along the header bottom to the drip leg', lambda i, s: (X0 + 0.4 + (1.8 - X0 - 0.4) * ((s + i / 10) % 1), 0.03, ZH - r + 0.015), 10, mat='water', r=0.012)
    droplets(m, 'drip', 'Condensate falling into the drip leg', 1.79, 1.81, ZH - r, 1.0, n=3, mat='water', y=0.0, r=0.014)
    add_tracers(m, 'trap_discharge', 'Condensate discharged by the trap (steam held back)', [(1.8, 0.0, 0.95), (2.47, 0, 0.95), (2.75, 0, 0.95), (2.75, 0, 0.45), (3.2, 0, 0.45)], n=5, radius=0.016, mat='water')
    m.flow('steam', [(X0 - 0.2, 0, ZH), (X1 - 0.1, 0, ZH)], 'steam', 0.03, 0.4)
    m.flow('branch_steam', [(-1.2, 0, ZH + 0.1), (-1.2, 0, 2.25), (-1.2, 1.5, 2.25)], 'steam', 0.015, 0.3)
    m.flow('reduced_steam', [(0.0, 0, ZH + 0.1), (0.0, 0, 2.25), (0.0, 1.6, 2.25)], 'steam', 0.015, 0.3)
    _press(m, [cyl('hp', r + 0.1, X0 + 0.3, X1 - 0.3, 'pressure_8', 48, axis='X', center=(0, 0, ZH), r_in=r + 0.08), cyl('lp', 0.11, 0.78, 1.5, 'pressure_3', 32, axis='Y', center=(0, 0, 2.25), r_in=0.09)],
           'Dry steam at the right pressure', 'The header carries boiler-pressure steam. Branches leave from the top so they take dry steam, not the condensate that runs along the bottom. Drip legs of full header '
           'bore every ≈ 30–50 m (and at low points / before risers) collect condensate, which a trap removes; without them slugs of water cause water hammer and erosion. A PRV station drops the pressure for '
           'users that need lower pressure; latent heat per kg rises as pressure falls, and a downstream safety valve protects the low-pressure side.')
    return m.export(out)


# =============================================================== EQ-314 Condensate recovery system
def condensate_recovery_system(out):
    m = _model('condensate_recovery_system', 'Condensate Recovery System: Flash Vessel, Vented Receiver & Condensate Pump Set')
    CZ, R, XA, XB = 1.15, 0.35, -0.7, 0.7
    P(m, 'receiver', 'Vented Condensate Receiver (horizontal)', 'vessel', vessel('rc', R, XB - XA, 0.006, 'stainless', axis='X', center=(0, 0, CZ), heads=('2:1', '2:1'), z0=XA), explode=(0, 0.7, 0), ref='cr_receiver')
    P(m, 'receiver_supports', 'Receiver Stand (raised to give the pumps NPSH)', 'structure', [box(f'rs{k}', (0.08, 0.6, CZ - R + 0.05), (x, 0, (CZ - R + 0.05) / 2), 'paint_grey') for k, x in enumerate((-0.45, 0.45))] +
      [box('rsb', (1.6, 1.3, 0.06), (0.1, 0, 0.03), 'paint_grey')], explode=(0, 0, -0.3), ref='cr_receiver', section='keep')
    lq = liquid('cw', R - 0.008, XA, CZ - 0.05, axis='X', center=(0, 0, 0), L=XB - XA, zt=CZ)
    pl = P(m, 'condensate', 'Hot Condensate (≈ 95–100 °C)', 'fluid', lq, explode=(0, -0.5, 0), ref='cr_receiver', section='keep')
    lvl = lambda t: 0.5 - 0.5 * math.cos(TAU * t)
    animate_level(m, pl, CZ - 0.2, 0.2, lvl)
    fs = [cyl('fsr', 0.008, CZ - 0.25, CZ + R + 0.1, 'stainless', 8, center=(0.35, 0.15, 0))]
    P(m, 'level_switch_rod', 'Float-Switch Guide Rod (pump start/stop)', 'controls', fs, explode=(0, 0.3, 0.4), ref='cr_controls', section='keep')
    fb = P(m, 'level_float', 'Level Float (rises → pump starts; falls → pump stops)', 'controls', ball('flt', 0.045, 'stainless', (0.35, 0.15, CZ - 0.1)), explode=(0, 0.3, 0.4), ref='cr_controls', section='keep')
    keys_loop(m, fb, lambda t: (0, 0, 0.2 * lvl(t)))
    fv = vessel('fv', 0.2, 0.7, 0.006, 'stainless', heads=('2:1', '2:1'), z0=1.4, center=(-1.3, 0, 0))
    P(m, 'flash_vessel', 'Flash Vessel (releases flash steam from high-pressure condensate)', 'vessel', [fv, legs('fl', 0.2, 0.0, 1.45, n=3, cx=-1.3)], explode=(-0.4, 0.4, 0), ref='cr_flash')
    pp = [hollow_pipe('hp', [(-2.1, 0.1, 1.9), (-1.48, 0.1, 1.9)], 0.035, 'steel', 12), hollow_pipe('fs', [(-1.3, 0, 2.2), (-1.3, 0, 2.6), (-2.1, 0, 2.6)], 0.06, 'steel', 16, bend=0.08),
          hollow_pipe('fd', [(-1.3, 0, 1.3), (-1.3, 0, 1.05), (-0.95, 0, 1.05), (-0.8, 0, CZ + 0.15)], 0.035, 'steel', 12, bend=0.05),
          hollow_pipe('lr', [(-2.1, -0.25, CZ + 0.25), (-0.6, -0.25, CZ + 0.25), (-0.3, -0.1, CZ + R - 0.02)], 0.04, 'steel', 12, bend=0.05),
          hollow_pipe('vt', [(0.2, 0, CZ + R - 0.01), (0.2, 0, 2.5)], 0.06, 'steel', 16), lathe('vh', [(0.0, 2.5), (0.12, 2.5), (0.12, 2.56), (0.0, 2.6)], 'steel', 24, center=(0.2, 0, 0)),
          hollow_pipe('of', [(XB + 0.15, 0, CZ + 0.2), (XB + 0.4, 0, CZ + 0.2), (XB + 0.4, 0, 0.3)], 0.04, 'steel', 12, bend=0.05), box('lg', (0.03, 0.03, 0.4), (-0.3, -R - 0.03, CZ), 'glass'),
          _valve('sp', (-1.3, 0, 2.45), 'Z', 0.05, 'cast_iron', kind='check')]
    P(m, 'piping', 'HP Condensate Inlet, Flash-Steam Outlet (to LP header), LP Condensate Returns, Atmospheric Vent, Overflow & Gauge Glass', 'piping', pp, explode=(0, 0, 0.4), ref='cr_piping', section='keep')
    for k, y in enumerate((-0.3, 0.3)):
        _pump(m, f'pump_{k + 1}', f'Condensate Pump {k + 1} (' + ('duty' if k == 0 else 'standby') + ')', -0.3, y, 0.3, 'cr_pumps', explode=(0, -0.4 if k == 0 else 0.4, 0))
    sd = [hollow_pipe(f'sl{k}', [(-0.3, 0, CZ - R + 0.01), (-0.3, 0, 0.62), (-0.3, y, 0.62), (-0.3, y, 0.42)], 0.03, 'stainless', 12, bend=0.04) for k, y in enumerate((-0.3, 0.3))]
    sd += [hollow_pipe(f'dl{k}', [(-0.3, y, 0.18), (-0.3, y, 0.1), (0.75, y, 0.1), (0.75, y, 0.55), (1.2, y, 0.55)], 0.025, 'steel', 12, bend=0.04) for k, y in enumerate((-0.3, 0.3))]
    sd += [hollow_pipe('rt', [(1.2, -0.3, 0.55), (1.2, 0.3, 0.55)], 0.03, 'steel', 12), hollow_pipe('rm', [(1.2, 0.3, 0.55), (1.2, 0.3, 1.0), (1.8, 0.3, 1.0)], 0.03, 'steel', 12, bend=0.05)]
    sd += [_valve(f'dc{k}', (0.95, y, 0.55), 'X', 0.025, 'cast_iron', kind='check') for k, y in enumerate((-0.3, 0.3))]
    P(m, 'pump_piping', 'Pump Suction Lines, Discharge Check Valves & Return Main to the Boiler Feed Tank', 'piping', sd, explode=(0, 0, -0.2), ref='cr_piping', section='keep')
    P(m, 'control_panel', 'Pump Control Panel (alternating duty, high-level alarm)', 'controls', [box('cpb', (0.35, 0.15, 0.5), (1.0, -0.6, 1.2), 'paint_grey'), cyl('cps', 0.025, 0.06, 0.95, 'paint_grey', 12, center=(1.0, -0.6, 0))],
      explode=(0.3, -0.3, 0), ref='cr_controls', section='keep')
    droplets(m, 'flash_steam', 'Flash steam released as pressure drops', -1.35, -1.25, 1.6, 2.2, n=5, mat='steam', y=0.06, r=0.02)
    m.flow('hp_condensate', [(-2.2, 0.1, 1.9), (-1.48, 0.1, 1.9), (-1.3, 0.05, 1.6), (-1.3, 0, 1.3), (-1.3, 0, 1.05), (-0.8, 0, CZ + 0.15)], 'water', 0.016, 0.3)
    m.flow('flash_steam_out', [(-1.3, 0, 2.0), (-1.3, 0, 2.6), (-2.2, 0, 2.6)], 'steam', 0.02, 0.3)
    m.flow('returns', [(-2.2, -0.25, CZ + 0.25), (-0.6, -0.25, CZ + 0.25), (-0.3, -0.1, CZ + 0.1)], 'water', 0.014, 0.3)
    m.flow('pumped_return', [(-0.3, 0.3, CZ - R), (-0.3, 0.3, 0.62), (-0.3, 0.3, 0.42), (-0.3, 0.3, 0.1), (0.75, 0.3, 0.1), (0.75, 0.3, 0.55), (1.2, 0.3, 0.55), (1.2, 0.3, 1.0), (1.9, 0.3, 1.0)], 'water', 0.016, 0.4)
    m.flow('vent', [(0.2, 0, CZ + R), (0.2, 0, 2.65)], 'steam', 0.012, 0.2)
    _press(m, [cyl('fz', 0.24, 1.4, 2.1, 'pressure_6', 32, center=(-1.3, 0, 0), r_in=0.22), cyl('rz', R + 0.04, XA, XB, 'pressure_1', 48, axis='X', center=(0, 0, CZ), r_in=R + 0.02)],
           'Recover heat, water and chemicals', 'High-pressure condensate entering a lower pressure partly flashes to steam: flash fraction = (h_f,high − h_f,low) / h_fg,low (≈ 10–15 % from ~10 bar to atmosphere). '
           'The flash vessel sends this steam to the LP header; the remaining hot condensate (already treated water, ≈ 90–100 °C) returns to the boiler, saving fuel, make-up water and treatment chemicals. '
           'Pumps handling near-boiling water need generous NPSH, which is why the receiver is raised above them.')
    return m.export(out)


# =============================================================== EQ-315 Cooling tower basin
def cooling_tower_basin(out):
    m = _model('cooling_tower_basin', 'Cooling Tower Cold-Water Basin with Sump, Screens, Make-up, Blowdown & Overflow')
    bs = csg('bs', [box('bso', (4.24, 2.64, 0.6), (0, 0, 0.3), 'cast_iron'), box('pto', (1.04, 1.24, 0.82), (1.5, 0, -0.29), 'cast_iron')],
             [box('bsi', (4.0, 2.4, 0.6), (0, 0, 0.42), 'cast_iron'), box('pti', (0.8, 1.0, 1.0), (1.5, 0, -0.08), 'cast_iron'),
              cyl('oh', 0.16, 1.85, 2.2, 'cast_iron', 32, axis='X', center=(0, 0, -0.35))], 'cast_iron')
    P(m, 'basin', 'Concrete Cold-Water Basin with Sloped Floor to the Pump Sump', 'basin', bs, explode=(0, 0.8, 0), ref='ctb_basin')
    wt = [_water_box('bw', -2.0, 2.0, 2.4, 0.12, 0.5), box('pw', (0.79, 0.495, 0.7), (1.5, 0.25, -0.23), 'water')]
    pw = P(m, 'water', 'Cooled Water (level held by the make-up valve)', 'fluid', wt, explode=(0, -0.5, 0), ref='ctb_basin', section='keep')
    animate_level(m, pw, 0.45, 0.04, lambda t: 0.5 + 0.5 * math.sin(TAU * t))
    sc = [box('sr0', (0.04, 1.0, 0.04), (1.1, 0, 0.5), 'steel'), box('sr1', (0.04, 1.0, 0.04), (1.1, 0, -0.56), 'steel')] + [cyl(f'sb{k}', 0.008, -0.56, 0.5, 'steel', 6, center=(1.1, -0.47 + 0.0475 * k, 0)) for k in range(21)]
    sc += [cyl(f'sh{k}', 0.006, -0.47, 0.47, 'steel', 6, axis='Y', center=(1.1, 0, -0.5 + 0.1 * k)) for k in range(11)]
    P(m, 'sump_screens', 'Removable Sump Screens (protect the circulating-water pumps)', 'screens', sc, explode=(-0.3, -0.4, 0.6), ref='ctb_screens', section='split')
    st = []
    for i, x in enumerate((-1.5, -0.5, 0.5, 1.5)):
        for j, y in enumerate((-0.9, 0.9)):
            st.append(box(f'cl{i}{j}', (0.14, 0.14, 2.5), (x, y, 0.12 + 1.25), 'cast_iron'))
    st += [box(f'bm{j}', (4.0, 0.14, 0.14), (0, y, 2.55), 'cast_iron') for j, y in enumerate((-0.9, 0.9))]
    P(m, 'structure', 'Tower Columns & Beams (fan deck above — see Cooling Tower Fan)', 'structure', st, explode=(0, 0.3, 0.6), ref='ctb_structure', section='keep')
    fl = [box(f'fs{k}', (3.9, 2.3, 0.012), (0, 0, 1.55 + 0.08 * k), 'polypropylene') for k in range(9)] + [box('de', (3.9, 2.3, 0.08), (0, 0, 2.42), 'paint_grey')]
    P(m, 'fill_eliminators', 'Film Fill Pack & Drift Eliminators', 'fill', fl, explode=(0, -0.6, 0.6), ref='ctb_fill', section='split')
    hw = [cyl('hh', 0.08, -2.4, 1.9, 'paint_grey', 24, axis='X', center=(0, 0, 2.3))] + [cyl(f'hl{k}', 0.035, -1.1, 1.1, 'paint_grey', 12, axis='Y', center=(x, 0, 2.3)) for k, x in enumerate((-1.5, -0.5, 0.5, 1.5))]
    hw += [cyl(f'nz{k}{j}', 0.03, 2.2, 2.27, 'polypropylene', 12, center=(x, y, 0)) for k, x in enumerate((-1.5, -0.5, 0.5, 1.5)) for j, y in enumerate((-0.7, 0.0, 0.7))]
    P(m, 'hot_water_distribution', 'Hot-Water Header, Laterals & Spray Nozzles', 'distribution', hw, explode=(0, 0, 0.6), ref='ctb_distribution', section='keep')
    lv = [rotate(box(f'lv{s}{k}', (0.02, 2.4, 0.18), (s * 2.13, 0, 0.75 + 0.18 * k), 'paint_grey'), s * 0.6, 'Y', (s * 2.13, 0, 0.75 + 0.18 * k)) for s in (-1, 1) for k in range(4)]
    P(m, 'air_inlet_louvres', 'Air-Inlet Louvres (keep water in, let air in)', 'structure', lv, explode=(0, 0, 0.3), ref='ctb_structure', section='keep')
    mu = [hollow_pipe('mu', [(-1.5, 1.7, 0.75), (-1.5, 0.95, 0.75), (-1.5, 0.95, 0.62)], 0.03, 'paint_blue', 12, bend=0.04), box('mv', (0.12, 0.1, 0.1), (-1.5, 0.95, 0.57), 'brass')]
    P(m, 'makeup_valve', 'Make-up Water Line & Float Valve', 'water_balance', mu, explode=(0, 0.4, 0.3), ref='ctb_makeup', section='keep')
    fa = join('fa', [cyl('fr', 0.008, -1.5, -1.15, 'brass', 8, axis='X', center=(0, 0.95, 0.55)), ball('fb', 0.07, 'paint_red', (-1.1, 0.95, 0.5))])
    pfa = P(m, 'float_arm', 'Float & Arm (opens the valve as the level falls)', 'water_balance', fa, explode=(0, 0.4, 0.4), ref='ctb_makeup', section='keep', pivot=(-1.5, 0.95, 0.55))
    keys_loop(m, pfa, lambda t: (0, -0.06 * math.sin(TAU * t), 0), 'rotation_euler')
    bd = [hollow_pipe('bdp', [(1.82, 0.35, -0.4), (2.6, 0.35, -0.4)], 0.04, 'steel', 12), _valve('bdv', (2.35, 0.35, -0.4), 'X', 0.04, 'cast_iron'),
          hollow_pipe('of', [(-1.8, 0.6, 0.55), (-1.8, 0.6, 0.0), (-1.8, 0.6, -0.2), (-2.6, 0.6, -0.2)], 0.05, 'paint_grey', 16, bend=0.05),
          hollow_pipe('co', [(1.88, 0, -0.35), (2.9, 0, -0.35)], 0.16, 'steel', 32), _valve('cov', (2.6, 0, -0.35), 'X', 0.16, 'cast_iron', wheel_mat='paint_blue_dark'),
          box('cd0', (0.18, 0.12, 0.25), (1.7, 1.45, 0.75), 'paint_yellow'), box('cd1', (0.18, 0.12, 0.25), (1.95, 1.45, 0.75), 'paint_green')]
    P(m, 'outlets_blowdown', 'Cold-Water Outlet to CW Pumps, Blowdown Valve, Overflow Standpipe & Chemical Dosing Points', 'piping', bd, explode=(0.4, 0, -0.3), ref='ctb_outlets', section='keep')
    droplets(m, 'rain_zone', 'Water raining from the fill into the basin', -1.8, 1.8, 1.5, 0.5, n=14, mat='water', y=0.4, r=0.018)
    m.flow('hot_water', [(-2.6, 0, 2.3), (-0.5, 0, 2.3), (-0.5, 0.4, 2.2), (-0.5, 0.4, 1.5)], 'water', 0.02, 0.4)
    m.flow('cold_water', [(0.0, 0.3, 0.3), (1.2, 0.2, 0.2), (1.5, 0.2, -0.3), (2.0, 0, -0.35), (3.0, 0, -0.35)], 'water', 0.025, 0.4)
    m.flow('air', [(-2.6, 0.2, 1.0), (-1.2, 0.3, 1.1), (-0.8, 0.3, 2.6)], 'air', 0.02, 0.3)
    m.flow('makeup', [(-1.5, 1.8, 0.75), (-1.5, 0.95, 0.75), (-1.5, 0.95, 0.5)], 'water', 0.012, 0.2)
    m.flow('blowdown', [(1.8, 0.35, -0.4), (2.7, 0.35, -0.4)], 'flow_discharge', 0.012, 0.2)
    m.overlay('temperature', join('temperature', [box('t0', (4.1, 0.02, 0.4), (0, 1.25, 2.3), 'pressure_8'), box('t1', (4.1, 0.02, 0.9), (0, 1.25, 1.05), 'pressure_5'),
                                                  box('t2', (4.1, 0.02, 0.4), (0, 1.25, 0.32), 'pressure_2')]),
              'The basin holds the coldest water in the loop', 'Hot return water (e.g. 40 °C) is cooled mainly by evaporation in the fill and rain zone and collects in the basin at the cold-water '
              'temperature (e.g. 30 °C; range 10 °C, approach to wet-bulb ≈ 3–5 °C). Evaporation (≈ 0.15 % of flow per °C of range) concentrates the dissolved solids, so blowdown keeps cycles of '
              'concentration ≈ 3–6, and make-up = evaporation + drift + blowdown. The sump depth gives the pumps submergence against vortices.', split=True)
    return m.export(out)


# =============================================================== EQ-316 Cooling tower fan
def cooling_tower_fan(out):
    m = _model('cooling_tower_fan', 'Induced-Draught Cooling Tower Fan with Velocity-Recovery Stack, Gearbox & Drive Shaft')
    cs = csg('cs', [box('cso', (3.3, 3.3, 2.0), (0, 0, 1.0), 'paint_grey')], [box('csi', (3.2, 3.2, 2.2), (0, 0, 1.0), 'paint_grey'),
                                                                              box('lo0', (3.6, 2.6, 0.7), (0, 0, 0.55), 'paint_grey')], 'paint_grey')
    P(m, 'casing', 'Tower Casing (air-inlet openings on two faces)', 'structure', cs, explode=(0, 0.8, -0.3), ref='ctf_structure')
    P(m, 'fill', 'Fill Pack (air passes up through it)', 'fill', [box(f'fs{k}', (3.1, 3.1, 0.012), (0, 0, 0.95 + 0.07 * k), 'polypropylene') for k in range(8)], explode=(0, -0.6, -0.2), ref='ctf_structure', section='split')
    dk = csg('dk', [box('dko', (3.4, 3.4, 0.08), (0, 0, 2.04), 'paint_grey')], [cyl('dkh', 1.24, 1.9, 2.2, 'paint_grey', 96)], 'paint_grey')
    stk = lathe('stk', [(1.22, 2.08), (1.27, 2.08), (1.27, 2.62), (1.52, 3.4), (1.47, 3.4), (1.22, 2.64)], 'paint_green', 96)
    P(m, 'fan_deck_stack', 'Fan Deck & Fan Stack (cylinder with flared velocity-recovery section)', 'stack', [dk, stk], explode=(0, 0.6, 0.5), ref='ctf_stack')
    hr = [cyl(f'hp{k}', 0.02, 2.08, 3.0, 'paint_yellow', 8, center=(x, y, 0)) for k, (x, y) in enumerate(((-1.65, -1.65), (1.65, -1.65), (1.65, 1.65), (-1.65, 1.65)))]
    hr += [cyl(f'hrx{k}', 0.02, -1.65, 1.65, 'paint_yellow', 8, axis='X', center=(0, y, 3.0)) for k, y in enumerate((-1.65, 1.65))] + [cyl(f'hry{k}', 0.02, -1.65, 1.65, 'paint_yellow', 8, axis='Y', center=(x, 0, 3.0)) for k, x in enumerate((-1.65, 1.65))]
    P(m, 'handrail', 'Fan-Deck Handrail', 'structure', hr, explode=(0, 0, 0.3), ref='ctf_structure', section='keep')
    CZ, Rf = 2.45, 1.15
    fan = [cyl('hub', 0.28, CZ - 0.07, CZ + 0.07, 'aluminium', 48), cyl('hc', 0.12, CZ + 0.07, CZ + 0.14, 'aluminium', 32), cyl('osh', 0.05, 2.32, CZ - 0.07, 'steel', 16)]
    for k in range(6):
        b = box(f'bl{k}', (Rf - 0.32, 0.3, 0.025), (0.3 + (Rf - 0.32) / 2, 0, CZ), 'carbon')
        b = rotate(b, 0.22, 'X', (0, 0, CZ))
        fan += [rotate(b, TAU * k / 6, 'Z'), rotate(box(f'bc{k}', (0.12, 0.12, 0.1), (0.3, 0, CZ), 'steel'), TAU * k / 6, 'Z')]
    pf = P(m, 'fan_rotor', 'Axial Fan: Hub & 6 Adjustable-Pitch FRP Blades', 'rotating_element', fan, explode=(0, -0.5, 1.0), ref='ctf_fan', section='keep', pivot=(0, 0, CZ))
    pf.spin('Z', 1)
    gb = [box('gb', (0.42, 0.36, 0.28), (0, 0, 2.18), 'paint_blue'), box('tt', (2.6, 0.2, 0.1), (0, 0, 1.99), 'steel_dark'), box('vs', (0.08, 0.06, 0.08), (0.25, 0.1, 2.2), 'paint_red'),
          hollow_pipe('ol', [(0.0, 0.18, 2.1), (0.0, 0.5, 2.1), (1.65, 0.5, 2.1)], 0.01, 'copper', 6, bend=0.03), box('sg', (0.04, 0.04, 0.15), (1.7, 0.5, 2.15), 'glass')]
    P(m, 'gearbox', 'Right-Angle Gearbox on Torque Tube, Vibration Switch & Remote Oil Gauge / Fill Line', 'drive', gb, explode=(0, -0.3, 0.4), ref='ctf_gearbox', section='keep')
    mt = [cyl('mt', 0.16, 1.85, 2.3, 'paint_motor', 32, axis='X', center=(0, 0, 2.2), ch=0.01), box('mf', (0.4, 0.3, 0.06), (2.07, 0, 2.08 + 0.03), 'paint_grey')]
    P(m, 'motor', 'Fan Motor (outside the humid air stream)', 'drive', mt, explode=(0.5, 0, 0.2), ref='ctf_motor', section='keep')
    ds = [cyl('ds', 0.035, 0.22, 1.85, 'carbon', 16, axis='X', center=(0, 0, 2.2))] + [cyl(f'dc{k}', 0.08, x - 0.03, x + 0.03, 'steel', 24, axis='X', center=(0, 0, 2.2)) for k, x in enumerate((0.26, 1.8))]
    pd = P(m, 'drive_shaft', 'Drive Shaft (composite tube) with Flexible Couplings', 'rotating_element', ds, explode=(0, -0.3, 0.3), ref='ctf_shaft', section='keep', pivot=(1.0, 0, 2.2))
    pd.spin('X', 6)
    m.flow('air', [(-2.0, 0, 0.5), (-1.0, 0.3, 0.6), (-0.6, 0.3, 1.5), (-0.6, 0.3, 2.3), (-0.8, 0.3, 3.6)], 'air', 0.03, 0.4)
    m.flow('air2', [(2.0, 0.6, 0.5), (1.0, 0.6, 0.6), (0.7, 0.6, 1.5), (0.7, 0.4, 2.3), (0.9, 0.4, 3.6)], 'air', 0.03, 0.4)
    m.flow('power', [(2.3, 0, 2.2), (0.22, 0, 2.2), (0.0, 0, 2.3), (0.0, 0, CZ)], 'power', 0.012, 0.2)
    _press(m, [cyl('pz0', 1.23, 1.6, 2.35, 'pressure_2', 64, r_in=1.21), cyl('pz1', 1.31, 2.55, 2.75, 'pressure_7', 64, r_in=1.29), cyl('pz2', 1.55, 3.1, 3.4, 'pressure_5', 64, r_in=1.53)],
           'Fan lifts the air; the stack recovers velocity pressure', 'The induced-draught fan draws air through the louvres and fill, so the plenum below the fan is slightly below atmospheric pressure (typically '
           '≈ 100–250 Pa of static pressure duty). Large fans turn slowly (tip speed usually ≤ ≈ 60 m/s for noise) and move very large volumes. The flared stack slows the leaving air, turning part of its '
           'velocity pressure back into static pressure, so the fan needs less power. Blade pitch is set to load the motor correctly; tip clearance to the stack should be small and even.')
    return m.export(out)


# =============================================================== EQ-317 Cooling tower gearbox
def cooling_tower_gearbox(out):
    m = _model('cooling_tower_gearbox', 'Cooling Tower Gearbox — Right-Angle Spiral-Bevel + Helical Reducer (≈ 10:1)')
    za, mb, mh = 0.62, 0.012, 0.012
    rp1, rp2 = mb * 12 / 2, mb * 40 / 2
    tg = rp1 / rp2
    d = math.atan(tg)
    xo = mh * (15 + 45) / 2
    hs = csg('hs', [box('hso', (1.2, 0.72, 0.8), (0.18, 0, 0.5), 'paint_blue'), box('hsf', (1.3, 0.85, 0.05), (0.18, 0, 0.125), 'paint_blue'),
                    cyl('bbi', 0.1, -0.5, -0.4, 'paint_blue', 32, axis='X', center=(0, 0, za)), cyl('bbo', 0.12, 0.88, 0.98, 'paint_blue', 32, center=(xo, 0, 0))],
             [box('hsi', (1.14, 0.66, 0.74), (0.18, 0, 0.5), 'paint_blue'), cyl('shi', 0.05, -0.6, -0.3, 'paint_blue', 32, axis='X', center=(0, 0, za)), cyl('sho', 0.06, 0.8, 1.1, 'paint_blue', 32, center=(xo, 0, 0))], 'paint_blue')
    P(m, 'housing', 'Gear Housing (cast iron, split in cutaway) with Mounting Flange', 'casing', hs, explode=(0, 0.7, 0), ref='ctg_housing')
    oil = box('oil', (1.13, 0.325, 0.22), (0.18, 0.165, 0.24), 'hydraulic_oil')
    P(m, 'oil_bath', 'Oil Bath (gears dip and splash-lubricate the bearings)', 'fluid', oil, explode=(0, -0.5, -0.3), ref='ctg_oil', section='keep')
    # ---- spiral-bevel pinion on the horizontal input shaft
    pin = [lathe('pb', [(0.0, -0.3), (rp1 * 1.25 - 0.006, -0.3), (rp1 * 0.83 - 0.006, -0.2), (0.0, -0.2)], 'steel', 48, axis='X', center=(0, 0, za)),
           cyl('ish', 0.035, -0.98, -0.2, 'steel', 24, axis='X', center=(0, 0, za)), cyl('ich', 0.08, -0.98, -0.88, 'steel_dark', 32, axis='X', center=(0, 0, za))]
    xm, rm = -0.25, tg * 0.25
    for k in range(12):
        t = box(f'pt{k}', (0.105, 0.013, 0.016), (xm, 0, za + rm), 'steel')
        t = rotate(t, d, 'Y', (xm, 0, za + rm))
        t = rotate(t, 0.25, 'Z', (xm, 0, za + rm))
        pin.append(rotate(t, TAU * k / 12, 'X', (0, 0, za)))
    pp = P(m, 'input_pinion', 'Input Shaft & Spiral-Bevel Pinion (z = 12) with Coupling Hub', 'rotating_element', pin, explode=(-0.5, -0.4, 0.2), ref='ctg_input', section='keep', pivot=(0, 0, za))
    pp.spin('X', 2.0)
    # ---- bevel gear + helical pinion on the vertical intermediate shaft
    ig = [lathe('gbd', [(0.03, za - 0.16), (rp2 + 0.035, za - 0.16), (rp2 + 0.035, za - rp1 - 0.04), (0.2, za - 0.2 * tg - 0.006), (0.03, za - 0.2 * tg - 0.006)], 'steel', 64),
          cyl('ish2', 0.04, 0.16, za - 0.05, 'steel', 24)]
    for k in range(40):
        t = box(f'gt{k}', (0.09, 0.013, 0.016), (rp2, 0, za - rp1), 'steel')
        t = rotate(t, d, 'Y', (rp2, 0, za - rp1))
        t = rotate(t, -0.25, 'Z', (rp2, 0, za - rp1))
        ig.append(rotate(t, TAU * k / 40, 'Z', (0, 0, 0)))
    g3, rp3 = helical_gear('g3', mh, 15, 0.25, 0.33, 'steel', cx=0.0, cz=0.0, helix_deg=15, hand=1)
    ig.append(rotate(g3, math.pi / 2, 'X'))
    pi_ = P(m, 'intermediate_shaft', 'Intermediate Shaft: Spiral-Bevel Gear (z = 40) & Helical Pinion (z = 15)', 'rotating_element', ig, explode=(0, -0.6, 0.5), ref='ctg_intermediate', section='keep', pivot=(0, 0, za))
    pi_.spin('Z', -0.6)
    g4, _ = helical_gear('g4', mh, 45, 0.25, 0.33, 'steel', cx=xo, cz=0.0, helix_deg=15, hand=-1, phase=math.pi + math.pi / 45)
    og = [rotate(g4, math.pi / 2, 'X'), cyl('osh', 0.05, 0.15, 1.24, 'steel', 32, center=(xo, 0, 0)), cyl('ofl', 0.16, 1.18, 1.24, 'steel_dark', 48, center=(xo, 0, 0))]
    og += [cyl(f'ob{k}', 0.014, 1.24, 1.27, 'steel', 8, center=(xo + 0.12 * math.cos(TAU * k / 10), 0.12 * math.sin(TAU * k / 10), 0)) for k in range(10)]
    po = P(m, 'output_shaft', 'Vertical Output Shaft & Helical Gear (z = 45) with Fan-Hub Flange', 'rotating_element', og, explode=(0.4, -0.6, 0.6), ref='ctg_output', section='keep', pivot=(xo, 0, 0))
    po.spin('Z', 0.2)
    br = [cyl('bi1', 0.07, -0.4, -0.36, 'chrome', 32, axis='X', center=(0, 0, za), r_in=0.036), cyl('bi2', 0.07, -0.18, -0.14, 'chrome', 32, axis='X', center=(0, 0, za), r_in=0.036),
          cyl('bm1', 0.075, 0.13, 0.18, 'chrome', 32, r_in=0.041), cyl('bo1', 0.09, 0.13, 0.19, 'chrome', 32, center=(xo, 0, 0), r_in=0.051), cyl('bo2', 0.1, 0.8, 0.87, 'chrome', 32, center=(xo, 0, 0), r_in=0.051)]
    P(m, 'bearings', 'Taper-Roller Bearings (carry gear thrust and fan thrust / weight)', 'bearings', br, explode=(0, 0.5, 0.3), ref='ctg_bearings', section='keep')
    ac = [box('sg', (0.04, 0.04, 0.12), (-0.43, 0.2, 0.3), 'glass'), cyl('brt', 0.02, 0.87, 0.97, 'brass', 12, center=(-0.1, 0.2, 0)), hollow_pipe('fl', [(-0.43, -0.2, 0.25), (-0.7, -0.2, 0.25), (-0.7, -0.2, 0.9)], 0.012, 'copper', 8, bend=0.03),
          box('vsw', (0.08, 0.06, 0.08), (0.75, 0.3, 0.75), 'paint_red'), cyl('ofs', 0.06, 0.88, 0.92, 'rubber', 32, center=(xo, 0, 0), r_in=0.05)]
    P(m, 'accessories', 'Oil Sight Glass, Breather, Remote Fill / Drain Line, Vibration Switch & Output Shaft Seal (above oil level)', 'lubrication', ac, explode=(0, 0, 0.4), ref='ctg_accessories', section='keep')
    m.flow('power', [(-1.0, 0, za), (-0.25, 0, za), (-0.25, 0, za - rp1), (0.0, 0, za - 0.1), (0.0, 0, 0.29), (xo, 0, 0.29), (xo, 0, 1.3)], 'power', 0.01, 0.15, speed=[3, 3, 3, 1, 1, 0.35, 0.35])
    _press(m, [cyl('t1', 0.05, -0.9, -0.5, 'pressure_1', 24, axis='X', center=(0, 0, za), r_in=0.04), cyl('t2', 0.06, 0.4, 0.45, 'pressure_4', 24, r_in=0.045),
               cyl('t3', 0.07, 0.95, 1.15, 'pressure_9', 24, center=(xo, 0, 0), r_in=0.055)], 'Speed down, torque up',
           'Motor speed (≈ 1500 rpm) is reduced about 10:1 to fan speed (≈ 150 rpm): the spiral-bevel set (40/12 ≈ 3.3) turns the drive through 90° and the helical set (45/15 = 3) completes the reduction. '
           'Output torque ≈ input torque × ratio × efficiency, so the output shaft and its bearings are much heavier. Gearboxes are selected with a service factor (typically ≥ 2.0 for cooling-tower duty), '
           'run in a humid, often icing environment, and depend on correct oil level — hence the remote oil gauge outside the stack.')
    return m.export(out)


# =============================================================== EQ-318 Emergency diesel firewater pump system
def emergency_diesel_firewater_system(out):
    m = _model('emergency_diesel_firewater_system', 'Emergency Diesel-Driven Firewater Pump System (Horizontal Split-Case Pump)')
    P(m, 'skid', 'Common Base Frame', 'structure', box('sk', (4.6, 1.4, 0.12), (-0.3, 0, 0.06), 'paint_grey'), explode=(0, 0, -0.3), ref='dfw_skid', section='keep')
    CZ = 0.6
    en = [box('eb', (1.2, 0.6, 0.5), (-1.0, 0, 0.55), 'paint_yellow', bevel=0.02), box('es', (1.1, 0.45, 0.18), (-1.0, 0, 0.21), 'paint_yellow'),
          box('eh', (1.15, 0.4, 0.14), (-1.0, 0, 0.87), 'paint_yellow'), box('vc', (1.05, 0.3, 0.08), (-1.0, 0, 0.98), 'steel_dark'),
          cyl('tc', 0.1, -0.1, 0.12, 'steel', 24, axis='Y', center=(-0.6, 0.42, 1.0)), cyl('fh', 0.3, -0.4, -0.28, 'paint_yellow', 48, axis='X', center=(0, 0, CZ)),
          cyl('af', 0.12, 0.35, 0.65, 'paint_grey', 24, axis='Y', center=(-1.3, 0, 1.0))]
    en += [box(f'ic{k}', (0.07, 0.07, 0.08), (-1.45 + 0.18 * k, -0.12, 1.06), 'steel') for k in range(6)]
    P(m, 'diesel_engine', 'Listed Fire-Pump Diesel Engine: Block, Sump, Heads, Turbocharger, Air Filter & Flywheel Housing', 'engine', en, explode=(0, -0.6, 0.3), ref='dfw_engine', section='keep')
    rd = [box('rc', (0.1, 0.95, 0.85), (-2.2, 0, 0.72), 'copper'), csg('rs', [cyl('rso', 0.42, -2.12, -1.95, 'paint_grey', 48, axis='X', center=(0, 0, 0.72))], [cyl('rsi', 0.39, -2.2, -1.9, 'paint_grey', 48, axis='X', center=(0, 0, 0.72))], 'paint_grey'),
          hollow_pipe('rh1', [(-2.15, 0.35, 1.05), (-1.6, 0.35, 1.05), (-1.6, 0.2, 0.9)], 0.03, 'rubber', 12, bend=0.04), hollow_pipe('rh2', [(-2.15, 0.35, 0.4), (-1.6, 0.25, 0.4)], 0.03, 'rubber', 12)]
    P(m, 'radiator', 'Radiator (or heat exchanger cooled by pump water) & Hoses', 'cooling', rd, explode=(-0.5, 0, 0), ref='dfw_cooling', section='keep')
    _fan_rotor(m, 'radiator_fan', 'Radiator Fan (engine driven)', (-2.0, 0, 0.72), 'X', 0.36, 'dfw_cooling', revs=5)
    fw = [cyl('fwd', 0.26, -0.34, -0.3, 'steel', 48, axis='X', center=(0, 0, CZ)), cyl('dsh', 0.04, -0.3, 0.6, 'steel', 24, axis='X', center=(0, 0, CZ))] + \
         [cyl(f'cp{k}', 0.11, x - 0.03, x + 0.03, 'steel_dark', 32, axis='X', center=(0, 0, CZ)) for k, x in enumerate((0.0, 0.5))] + [box('cpk', (0.04, 0.18, 0.03), (0.0, 0, CZ + 0.05), 'steel')]
    pfw = P(m, 'drive_train', 'Crankshaft Output, Flywheel, Drive Shaft & Flexible Coupling (turning)', 'rotating_element', fw, explode=(0, -0.4, 0.3), ref='dfw_drive', section='keep', pivot=(0, 0, CZ))
    pfw.spin('X', 4)
    ex = [hollow_pipe('ep', [(-0.6, 0.42, 1.1), (-0.6, 0.42, 1.5), (-0.9, 0.3, 1.7)], 0.05, 'steel_dark', 16, bend=0.06), cyl('sl', 0.15, -1.7, -0.75, 'steel_dark', 32, axis='X', center=(0, 0.3, 1.7)),
          hollow_pipe('tp', [(-1.7, 0.3, 1.7), (-1.85, 0.3, 1.7), (-1.85, 0.3, 2.3)], 0.05, 'steel_dark', 16, bend=0.06)] + [cyl(f'sp{k}', 0.025, 0.12, 1.55, 'paint_grey', 12, center=(x, 0.6, 0)) for k, x in enumerate((-1.6, -0.85))] + \
         [box(f'sa{k}', (0.06, 0.35, 0.04), (x, 0.45, 1.55), 'paint_grey') for k, x in enumerate((-1.6, -0.85))]
    P(m, 'exhaust', 'Exhaust Pipe, Flexible Bellows & Silencer (piped outside)', 'exhaust', ex, explode=(0, 0.3, 0.6), ref='dfw_exhaust', section='keep')
    pc = csg('pc', [cyl('pco', 0.33, 0.62, 1.08, 'paint_red', 64, axis='X', center=(0, 0, CZ)), cyl('pbe', 0.09, 0.56, 1.2, 'paint_red', 32, axis='X', center=(0, 0, CZ)),
                    cyl('psn', 0.15, 0.2, 0.62, 'paint_red', 32, axis='Y', center=(0.85, 0, CZ - 0.05)), cyl('pdn', 0.12, -0.62, -0.2, 'paint_red', 32, axis='Y', center=(0.85, 0, CZ - 0.05)),
                    box('pft', (0.7, 0.5, 0.36), (0.85, 0, 0.3), 'paint_red')],
             [cyl('pci', 0.3, 0.65, 1.05, 'paint_red', 64, axis='X', center=(0, 0, CZ)), cyl('psi', 0.13, 0.15, 0.6, 'paint_red', 32, axis='Y', center=(0.85, 0, CZ - 0.05)),
              cyl('pdi', 0.1, -0.6, -0.15, 'paint_red', 32, axis='Y', center=(0.85, 0, CZ - 0.05)), cyl('psh', 0.045, 0.5, 1.3, 'paint_red', 24, axis='X', center=(0, 0, CZ))], 'paint_red')
    P(m, 'fire_pump_casing', 'Horizontal Split-Case Fire Pump Casing (axially split; side suction & discharge)', 'casing', pc, explode=(0, 0.6, 0.3), ref='dfw_pump')
    im = [lathe('imp', [(0.04, 0.72), (0.22, 0.74), (0.24, 0.85), (0.22, 0.96), (0.04, 0.98), (0.04, 0.72)], 'bronze', 48, axis='X', center=(0, 0, CZ)), cyl('psf', 0.04, 0.6, 1.25, 'steel', 24, axis='X', center=(0, 0, CZ))]
    im += [rotate(box(f'iv{k}', (0.2, 0.02, 0.16), (0.85, 0, CZ + 0.14), 'bronze'), TAU * k / 6, 'X', (0, 0, CZ)) for k in range(6)]
    pim = P(m, 'impeller', 'Double-Suction Impeller & Pump Shaft (turning)', 'rotating_element', im, explode=(0, -0.5, 0.5), ref='dfw_impeller', section='keep', pivot=(0, 0, CZ))
    pim.spin('X', 4)
    sp = [hollow_pipe('sp', [(0.85, 0.6, CZ - 0.05), (0.85, 1.7, CZ - 0.05)], 0.13, 'paint_red', 32), _valve('sgv', (0.85, 1.25, CZ - 0.05), 'Y', 0.13, 'paint_red', wheel_mat='steel'),
          pressure_gauge('cg', (0.7, 0.75, CZ + 0.12), r=0.04, facing=(-1, 0, 0))]
    P(m, 'suction_piping', 'Suction Pipe from the Firewater Tank, OS&Y Gate Valve & Compound Gauge', 'piping', sp, explode=(0, 0.4, 0), ref='dfw_suction', section='keep')
    dp = [hollow_pipe('dp', [(0.85, -0.6, CZ - 0.05), (0.85, -0.9, CZ - 0.05), (0.85, -0.9, 1.4), (2.4, -0.9, 1.4)], 0.1, 'paint_red', 32, bend=0.12),
          _valve('dcv', (0.85, -0.9, 0.95), 'Z', 0.1, 'paint_red', kind='check'), _valve('dgv', (0.85, -0.9, 1.2), 'Z', 0.1, 'paint_red', wheel_mat='steel'),
          join('rv', [cyl('rvb', 0.07, 1.42, 1.62, 'paint_red', 24, center=(1.4, -0.9, 0)), cyl('rvc', 0.05, 1.62, 1.85, 'paint_red', 24, center=(1.4, -0.9, 0)),
                      hollow_pipe('rvo', [(1.4, -0.9, 1.52), (1.4, -1.3, 1.52), (1.4, -1.3, 0.4)], 0.05, 'paint_red', 16, bend=0.05), lathe('wc', [(0.05, 0.4), (0.15, 0.4), (0.06, 0.28), (0.05, 0.28)], 'steel', 24, center=(1.4, -1.3, 0))]),
          pressure_gauge('dg', (0.95, -0.9, 1.5), r=0.04, facing=(0, -1, 0)), box('th', (0.2, 0.6, 0.2), (2.4, -0.9, 1.4), 'paint_red')]
    dp += [join(f'hv{k}', [cyl(f'hvb{k}', 0.05, -0.6 - 0.08, -0.6 + 0.05, 'brass', 16, axis='Y', center=(2.4, 0, 1.4 + 0.0)), cyl(f'hvc{k}', 0.035, -0.75, -0.68, 'brass', 16, axis='Y', center=(2.4, 0, 1.4))]) for k in range(1)]
    dp += [join(f'hx{k}', [cyl(f'hxb{k}', 0.05, 1.5, 1.6, 'brass', 16, center=(2.4, y, 0)), cyl(f'hxc{k}', 0.035, 1.6, 1.68, 'brass', 16, center=(2.4, y, 0))]) for k, y in enumerate((-1.1, -0.9, -0.7))]
    P(m, 'discharge_piping', 'Discharge: Check & Gate Valves, Main Relief Valve to Waste Cone, Gauge & Test Header with Hose Valves', 'piping', dp, explode=(0.3, -0.4, 0.2), ref='dfw_discharge', section='keep')
    _pump(m, 'jockey_pump', 'Jockey (Pressure-Maintenance) Pump', 1.6, 0.95, 0.25, 'dfw_jockey', explode=(0.3, 0.4, 0))
    P(m, 'jockey_piping', 'Jockey Pump Line (keeps the fire main pressurised so the main pump only starts on a real demand)', 'piping',
      [hollow_pipe('jp', [(1.6, 0.95, 0.37), (1.6, 0.95, 1.6), (1.6, -0.9, 1.6), (1.6, -0.9, 1.5)], 0.02, 'paint_red', 12, bend=0.04)], explode=(0.3, 0.4, 0.2), ref='dfw_jockey', section='keep')
    ft = [box('ftk', (0.9, 0.45, 0.45), (-1.2, 1.35, 1.35), 'paint_grey'), csg('ftb', [box('fbo', (1.1, 0.65, 0.15), (-1.2, 1.35, 0.95), 'paint_grey')], [box('fbi', (1.04, 0.59, 0.15), (-1.2, 1.35, 1.0), 'paint_grey')], 'paint_grey'),
          box('flg', (0.03, 0.03, 0.35), (-0.73, 1.35, 1.35), 'glass')] + [cyl(f'fl{k}', 0.025, 0.0, 0.88, 'paint_grey', 12, center=(x, y, 0)) for k, (x, y) in enumerate(((-1.7, 1.1), (-0.7, 1.1), (-1.7, 1.6), (-0.7, 1.6)))]
    ft += [hollow_pipe('fs', [(-1.4, 1.15, 1.13), (-1.4, 1.15, 0.9), (-1.4, 0.31, 0.5)], 0.012, 'copper', 8, bend=0.04), hollow_pipe('fr', [(-1.0, 0.31, 0.55), (-1.0, 1.15, 0.9), (-1.0, 1.15, 1.58)], 0.01, 'copper', 8, bend=0.04)]
    P(m, 'fuel_system', 'Fuel Day Tank (bunded, gauge) with Supply & Return Lines', 'fuel', ft, explode=(0, 0.5, 0.3), ref='dfw_fuel', section='keep')
    ct = [box('ctl', (0.5, 0.25, 0.8), (0.15, 1.15, 0.9), 'paint_red'), cyl('cts', 0.03, 0.0, 0.5, 'paint_grey', 12, center=(0.15, 1.15, 0))] + \
         [box(f'bt{k}', (0.25, 0.18, 0.2), (-1.4 + 0.3 * k, 0.52, 0.22), 'steel_dark') for k in range(2)] + [box(f'bs{k}', (0.25, 0.18, 0.2), (-1.4 + 0.3 * k, -0.52, 0.22), 'steel_dark') for k in range(2)]
    P(m, 'controller_batteries', 'Fire-Pump Controller (automatic start on pressure drop) & Two Battery Sets', 'controls', ct, explode=(0, 0.5, 0.2), ref='dfw_controls', section='keep')
    m.flow('suction', [(0.85, 1.8, CZ - 0.05), (0.85, 0.3, CZ - 0.05), (0.85, 0.1, CZ)], 'flow_suction', 0.025, 0.4)
    m.flow('discharge', [(0.85, -0.1, CZ), (0.85, -0.9, CZ - 0.05), (0.85, -0.9, 1.4), (2.4, -0.9, 1.4), (2.4, -0.9, 1.7)], 'flow_discharge', 0.025, 0.4)
    m.flow('relief', [(1.4, -0.9, 1.45), (1.4, -1.3, 1.52), (1.4, -1.3, 0.3)], 'water', 0.012, 0.2)
    m.flow('exhaust', [(-0.6, 0.42, 1.1), (-0.9, 0.3, 1.7), (-1.7, 0.3, 1.7), (-1.85, 0.3, 2.4)], 'exhaust', 0.02, 0.3)
    m.flow('fuel', [(-1.4, 1.15, 1.13), (-1.4, 1.15, 0.9), (-1.4, 0.31, 0.5)], 'hydraulic_oil', 0.01, 0.2)
    _press(m, [cyl('ps', 0.16, 0.25, 0.6, 'pressure_2', 32, axis='Y', center=(0.85, 0, CZ - 0.05), r_in=0.15), cyl('pd', 0.13, -0.6, -0.2, 'pressure_8', 32, axis='Y', center=(0.85, 0, CZ - 0.05), r_in=0.12)],
           'Rated flow at rated pressure — guaranteed', 'Fire pumps are certified to deliver rated flow at rated pressure, at least 150 % of rated flow at not less than 65 % of rated pressure, with churn (shut-off) '
           'pressure not above 140 % of rated (NFPA 20 style rules — verify against the governing edition). The diesel driver gives independence from the electrical supply; it starts automatically on a pressure '
           'drop, has two battery sets, and is tested weekly. The jockey pump makes up small leaks so the main pump starts only for a real demand.')
    return m.export(out)


# =============================================================== EQ-319 Sewage lift station
def sewage_lift_station(out):
    m = _model('sewage_lift_station', 'Sewage Lift (Pumping) Station — Wet Well with Twin Submersible Pumps & Valve Chamber')
    Rw, Zb = 1.0, -3.0
    ww = csg('ww', [cyl('wwo', Rw + 0.12, Zb - 0.15, 0.3, 'cast_iron', 96)], [cyl('wwi', Rw, Zb, 0.4, 'cast_iron', 96), cyl('wi', 0.16, -1.2, -0.5, 'cast_iron', 32, axis='X', center=(0, 0, -0.8)),
                                                                             cyl('wo1', 0.08, 0.9, 1.25, 'cast_iron', 24, axis='X', center=(0, 0.55, -0.6)), cyl('wo2', 0.08, 0.9, 1.25, 'cast_iron', 24, axis='X', center=(0, 0.55, -0.95))], 'cast_iron')
    bn = lathe('bn', [(0.0, Zb), (Rw - 0.001, Zb), (Rw - 0.001, Zb + 0.25), (0.75, Zb + 0.04), (0.0, Zb + 0.04)], 'cast_iron', 96)
    P(m, 'wet_well', 'Concrete Wet Well with Benched (sloped) Floor', 'well', [ww, bn], explode=(0, 0.9, 0), ref='sls_well')
    sl = csg('sl', [cyl('slo', Rw + 0.12, 0.3, 0.45, 'cast_iron', 96)], [box('h1', (0.9, 0.6, 0.3), (-0.05, 0.4, 0.38), 'cast_iron'), cyl('vh', 0.08, 0.2, 0.6, 'cast_iron', 16, center=(-0.6, -0.4, 0))], 'cast_iron')
    P(m, 'cover_slab', 'Cover Slab with Pump-Access Hatch', 'well', sl, explode=(0, 0, 0.8), ref='sls_well')
    P(m, 'hatch', 'Hinged Access Hatch (open) & Safety Grid', 'well', [rotate(box('hl', (0.9, 0.03, 0.6), (-0.05, 0.7, 0.75), 'aluminium'), 0.0, 'Z'), box('sg', (0.88, 0.58, 0.02), (-0.05, 0.4, 0.42), 'paint_yellow')],
      explode=(0, 0.3, 1.0), ref='sls_well', section='keep')
    lq = lathe('lq', [(0.0, Zb + 0.04), (Rw - 0.005, Zb + 0.04), (Rw - 0.005, -1.6), (0.0, -1.6)], 'liquor', 96, a0=0.0, a1=math.pi, cap_mat='liquor')
    pl = P(m, 'sewage', 'Sewage in the Wet Well (fills, then is pumped down)', 'fluid', lq, explode=(0, -0.6, 0), ref='sls_well', section='keep')
    lvl = lambda t: (t / 0.7) if t < 0.7 else (1 - (t - 0.7) / 0.3)
    animate_level(m, pl, -2.3, 0.7, lvl)
    sc = [cyl('ip', 0.15, -2.6, -0.95, 'cast_iron', 32, axis='X', center=(0, 0, -0.8), r_in=0.13), csg('bk', [box('bko', (0.4, 0.4, 0.5), (-0.75, 0, -1.25), 'steel')], [box('bki', (0.36, 0.36, 0.5), (-0.75, 0, -1.2), 'steel')], 'steel')]
    sc += [cyl(f'br{k}', 0.015, -1.0, 0.3, 'steel', 8, center=(-0.75, y, 0)) for k, y in enumerate((-0.22, 0.22))]
    P(m, 'inlet_screen', 'Incoming Sewer & Inlet Basket Screen on Guide Rails (traps rags / large solids)', 'screening', sc, explode=(-0.5, 0, 0.3), ref='sls_inlet', section='keep')
    for k, x in enumerate((-0.35, 0.3)):
        y0 = 0.3
        body = [box(f'df{k}', (0.3, 0.3, 0.2), (x, 0.58, Zb + 0.12), 'cast_iron'), cyl(f'vl{k}', 0.2, Zb + 0.12, Zb + 0.42, 'paint_blue', 48, center=(x, y0, 0)),
                cyl(f'mt{k}', 0.15, Zb + 0.42, Zb + 1.05, 'paint_blue', 48, center=(x, y0, 0), ch=0.01), box(f'hd{k}', (0.2, 0.04, 0.12), (x, y0, Zb + 1.12), 'steel'),
                box(f'cl{k}', (0.08, 0.1, 0.18), (x, y0 + 0.22, Zb + 0.3), 'paint_blue')]
        body += [cyl(f'rl{k}{s}', 0.02, Zb + 0.22, 0.3, 'stainless', 8, center=(x + s * 0.12, 0.66, 0)) for s in (-1, 1)]
        body += [hollow_pipe(f'rs{k}', [(x, 0.58, Zb + 0.22), (x, 0.58, -0.6 - 0.35 * k), (0.92, 0.55, -0.6 - 0.35 * k)], 0.075, 'stainless', 24, bend=0.08)]
        P(m, f'pump_{k + 1}', f'Submersible Sewage Pump {k + 1} (' + ('duty' if k == 0 else 'standby') + ') on Duckfoot Bend, Guide Rails & Discharge Riser', 'pumps', body,
          explode=(0, -0.5, 0.6 + 0.3 * k), ref='sls_pumps', section='keep')
        im = [cyl(f'ih{k}', 0.05, Zb + 0.18, Zb + 0.36, 'steel', 16, center=(x, y0, 0))] + [rotate(box(f'iv{k}{j}', (0.14, 0.02, 0.14), (x + 0.09, y0, Zb + 0.26), 'cast_iron'), TAU * j / 2, 'Z', (x, y0, 0)) for j in range(2)]
        pim = P(m, f'impeller_{k + 1}', f'Non-Clog (2-channel) Impeller {k + 1}', 'rotating_element', im, explode=(0, -0.8, 0.3 + 0.3 * k), ref='sls_pumps', section='keep', pivot=(x, y0, 0))
        pim.spin('Z', 4 if k == 0 else 0)
    lc = [box('fb', (0.06, 0.06, 0.3), (0.62, -0.1, 0.15), 'steel')] + [cyl(f'fc{k}', 0.006, z, 0.3, 'rubber', 6, center=(0.62, -0.1 + 0.06 * k, 0)) for k, z in enumerate((-2.4, -1.6, -0.95))]
    lc += [ball(f'fl{k}', 0.06, 'paint_orange', (0.62, -0.1 + 0.06 * k, z - 0.06)) for k, z in enumerate((-2.4, -1.6, -0.95))] + [box('us', (0.12, 0.12, 0.12), (0.2, -0.6, 0.24), 'paint_blue_dark')]
    P(m, 'level_controls', 'Float Switches (stop / duty start / high-level alarm) & Ultrasonic Level Transmitter', 'controls', lc, explode=(0.3, -0.3, 0.3), ref='sls_controls', section='keep')
    vc = csg('vc', [box('vco', (1.5, 1.6, 1.75), (1.85, 0, -0.575), 'cast_iron')], [box('vci', (1.26, 1.36, 1.75), (1.85, 0, -0.45), 'cast_iron')], 'cast_iron')
    P(m, 'valve_chamber', 'Valve Chamber (dry, separate from the wet well)', 'chamber', vc, explode=(0.6, 0.6, 0), ref='sls_valves')
    vv = []
    for k, z in enumerate((-0.6, -0.95)):
        vv += [hollow_pipe(f'vp{k}', [(0.92, 0.55, z), (2.3, 0.55, z)], 0.075, 'cast_iron', 24), _valve(f'ck{k}', (1.5, 0.55, z), 'X', 0.075, 'cast_iron', kind='check'), _valve(f'gv{k}', (1.95, 0.55, z), 'X', 0.075, 'cast_iron')]
    vv += [hollow_pipe('hdr', [(2.3, 0.55, -0.95), (2.3, 0.55, -0.6), (2.3, 0.55, -0.3), (3.2, 0.55, -0.3)], 0.1, 'cast_iron', 24, bend=0.1)]
    P(m, 'valves_rising_main', 'Check & Gate Valves on each Pump Line, Common Header & Rising Main', 'valves', vv, explode=(0.6, 0, 0.3), ref='sls_valves', section='keep')
    ac = [hollow_pipe('vt', [(-0.6, -0.4, 0.3), (-0.6, -0.4, 1.9), (-0.45, -0.4, 2.05), (-0.3, -0.4, 1.9)], 0.05, 'paint_grey', 12, bend=0.06), cyl('cf', 0.12, 1.2, 1.6, 'paint_grey', 24, center=(-0.6, -0.4, 0)),
          box('kp', (0.6, 0.3, 1.0), (-2.0, 1.0, 0.5), 'paint_grey')]
    P(m, 'vent_kiosk', 'Odour-Control Vent (carbon filter) & Control Kiosk', 'controls', ac, explode=(-0.3, 0, 0.5), ref='sls_controls', section='keep')
    m.flow('inflow', [(-2.6, 0, -0.8), (-0.95, 0, -0.8), (-0.75, 0.05, -1.25), (-0.4, 0.2, -2.2)], 'flow_suction', 0.025, 0.4)
    m.flow('discharge', [(-0.35, 0.4, Zb + 0.25), (-0.35, 0.58, Zb + 0.22), (-0.35, 0.58, -0.6), (0.92, 0.55, -0.6), (2.3, 0.55, -0.6), (2.3, 0.55, -0.3), (3.3, 0.55, -0.3)], 'flow_discharge', 0.025, 0.4)
    _press(m, [cyl('rz', 0.1, Zb + 0.25, -0.65, 'pressure_6', 24, center=(-0.35, 0.58, 0), r_in=0.085), box('mz', (0.8, 0.02, 0.2), (2.75, 0.68, -0.3), 'pressure_7')], 'Lifting sewage to a higher sewer',
           'Gravity sewers get deeper downstream; a lift station raises the flow into a rising (force) main or a higher sewer. Pumps start and stop on level so they do not cycle too often (typically ≤ 6–10 starts/h '
           'per motor — wet-well volume is sized for it) and the duty alternates. Non-clog impellers pass solids (often ≥ 75–100 mm); rising-main velocity is kept ≈ 0.7–2.5 m/s to avoid settling. '
           'Pumps lift out on the guide rails without anyone entering the well — a confined space with H₂S risk.')
    return m.export(out)


# =============================================================== EQ-320 Effluent treatment plant
def effluent_treatment_plant(out):
    m = _model('effluent_treatment_plant', 'Effluent Treatment Plant — Screening, Equalisation, Neutralisation, Activated Sludge & Secondary Clarifier')
    # screening channel
    P(m, 'screen_channel', 'Inlet Channel', 'tank', _rect_tank('sc', -4.7, -3.9, 0.5, 0.7, t=0.08), explode=(-0.3, 0.5, 0), ref='etp_screen')
    br = [rotate(cyl(f'bb{k}', 0.008, 0.08, 1.0, 'stainless', 6, center=(-4.3, -0.22 + 0.04 * k, 0)), math.radians(-25), 'Y', (-4.3, 0, 0.08)) for k in range(12)]
    br += [box('stry', (0.3, 0.5, 0.06), (-4.05, 0, 0.98), 'stainless')]
    P(m, 'bar_screen', 'Inclined Bar Screen & Screenings Tray', 'screening', br, explode=(-0.3, -0.4, 0.3), ref='etp_screen', section='keep')
    P(m, 'screen_water', 'Raw Effluent', 'fluid', _water_box('sw', -4.7, -3.9, 0.5, 0.08, 0.5, mat='liquor'), explode=(-0.3, -0.3, 0), ref='etp_screen', section='keep')
    # equalisation tank
    P(m, 'equalisation_tank', 'Equalisation Tank (evens out flow and strength)', 'tank', _rect_tank('eq', -3.6, -2.4, 1.4, 1.4, t=0.1), explode=(0, 0.7, 0), ref='etp_eq')
    peq = P(m, 'eq_liquid', 'Equalised Effluent (level varies with inflow)', 'fluid', _water_box('ew', -3.6, -2.4, 1.4, 0.1, 1.1, mat='liquor'), explode=(0, -0.4, 0), ref='etp_eq', section='keep')
    animate_level(m, peq, 1.0, 0.15, lambda t: 0.5 - 0.5 * math.cos(TAU * t))
    P(m, 'eq_mixer_body', 'Submersible Mixer (motor & mast)', 'mixer', [cyl('mm', 0.07, -3.35, -3.1, 'paint_blue', 24, axis='X', center=(0, 0.35, 0.4)), cyl('ms', 0.02, 0.4, 1.5, 'stainless', 8, center=(-3.4, 0.35, 0))],
      explode=(0, -0.3, 0.3), ref='etp_eq', section='keep')
    pr = [cyl('ph', 0.04, -3.1, -3.0, 'stainless', 16, axis='X', center=(0, 0.35, 0.4))] + [rotate(rotate(box(f'pb{k}', (0.02, 0.06, 0.16), (-3.05, 0.35, 0.4 + 0.1), 'stainless'), 0.4, 'Z', (-3.05, 0.35, 0.5)), TAU * k / 3, 'X', (0, 0.35, 0.4)) for k in range(3)]
    ppr = P(m, 'eq_propeller', 'Mixer Propeller (keeps solids suspended)', 'rotating_element', pr, explode=(0, -0.4, 0.3), ref='etp_eq', section='keep', pivot=(-3.05, 0.35, 0.4))
    ppr.spin('X', 6)
    _pump(m, 'eq_transfer_pump', 'Equalisation Transfer Pump (steady feed)', -2.2, -0.9, 0.2, 'etp_eq', explode=(0, -0.4, 0))
    # neutralisation
    agitated_tank(m, 'nt_', 0.45, 0.0, 1.2, 'Neutralisation Tank', 'etp_neut', cx=-1.6, liquid='water', imp='pbt', revs=3, open_top=True, legs_=False)
    nd = [cyl(f'dt{k}', 0.16, 0.0, 0.6, mat, 24, center=(-1.35 + 0.4 * k, 0.75, 0)) for k, mat in enumerate(('paint_red', 'paint_yellow'))]
    nd += [hollow_pipe(f'dl{k}', [(-1.35 + 0.4 * k, 0.75, 0.6), (-1.35 + 0.4 * k, 0.75, 1.35), (-1.6 + 0.1 * k, 0.25, 1.35), (-1.6 + 0.1 * k, 0.25, 1.1)], 0.012, 'polypropylene', 8, bend=0.04) for k in range(2)]
    nd += [cyl('php', 0.015, 0.6, 1.4, 'stainless', 8, center=(-1.85, 0.2, 0)), box('phx', (0.1, 0.06, 0.12), (-1.85, 0.2, 1.45), 'paint_blue_dark')]
    P(m, 'ph_control', 'pH Probe & Controller with Acid / Caustic Dosing Tanks and Lines', 'chemicals', nd, explode=(0, 0.5, 0.3), ref='etp_neut', section='keep')
    # aeration tank
    X0, X1, W, H = -0.9, 1.4, 1.6, 1.5
    P(m, 'aeration_tank', 'Aeration Tank (activated sludge reactor)', 'tank', _rect_tank('at', X0, X1, W, H, t=0.1), explode=(0, 0.8, 0), ref='etp_aeration')
    P(m, 'mixed_liquor', 'Mixed Liquor (wastewater + activated sludge biomass)', 'fluid', _water_box('ml', X0, X1, W, 0.1, H - 0.15, mat='liquor'), explode=(0, -0.5, 0), ref='etp_aeration', section='keep')
    df = [cyl(f'dg{k}', 0.025, X0 + 0.15, X1 - 0.15, 'polypropylene', 12, axis='X', center=(0, y, 0.18)) for k, y in enumerate((-0.4, 0.0, 0.4))]
    df += [cyl(f'dd{k}{j}', 0.07, 0.2, 0.23, 'rubber', 24, center=(X0 + 0.3 + 0.35 * j, y, 0)) for k, y in enumerate((-0.4, 0.0, 0.4)) for j in range(6)]
    df += [hollow_pipe('ah', [(0.2, 1.3, 0.4), (0.2, 1.3, H + 0.25), (0.2, 0.4, H + 0.25), (0.2, 0.4, 0.18)], 0.05, 'stainless', 16, bend=0.08), cyl('ahm', 0.04, -0.45, 0.45, 'stainless', 12, axis='Y', center=(0.2, 0, 0.18))]
    P(m, 'diffusers', 'Fine-Bubble Membrane Disc Diffusers, Drop Pipe & Air Grid', 'aeration', df, explode=(0, -0.3, -0.3), ref='etp_diffusers', section='keep')
    bw = csg('bw', [cyl('bwo', 0.22, 1.2, 1.45, 'paint_blue', 48, axis='Y', center=(0.2, 0, 0.4))], [cyl('bwi', 0.2, 1.22, 1.43, 'paint_blue', 48, axis='Y', center=(0.2, 0, 0.4))], 'paint_blue')
    P(m, 'blower', 'Aeration Blower (positive-displacement or turbo)', 'air', [bw, cyl('bm', 0.12, 1.45, 1.8, 'paint_motor', 32, axis='Y', center=(0.2, 0, 0.4)), box('bbp', (0.6, 0.7, 0.06), (0.2, 1.45, 0.15), 'paint_grey')],
      explode=(0, 0.5, 0), ref='etp_blower', section='keep')
    _fan_rotor(m, 'blower_impeller', 'Blower Impeller', (0.2, 1.33, 0.4), 'Y', 0.17, 'etp_blower', revs=6)
    droplets(m, 'air_bubbles', 'Fine air bubbles: oxygen for the bacteria and mixing', X0 + 0.25, X1 - 0.25, 0.25, H - 0.2, n=16, mat='air', y=0.2, r=0.02)
    particles_path(m, 'floc_biomass', 'Activated-sludge flocs (bacteria) consuming organic matter', lambda i, s: (X0 + 0.2 + (X1 - X0 - 0.4) * ((s + i / 10) % 1), 0.45 + 0.1 * math.sin(i), 0.4 + 0.8 * ((i * 0.37) % 1) + 0.1 * math.sin(TAU * 2 * s)), 10,
                   mat='sludge', r=0.02)
    # secondary clarifier
    z0 = thickener(m, 'sc_', 0.85, 1.0, 0.3, cx=2.6, label='Secondary Clarifier', ref='etp_clar', mat='cast_iron', liquid='water', mud='sludge', rake_revs=0.2)
    _pump(m, 'ras_pump', 'Return / Waste Activated Sludge (RAS / WAS) Pump', 1.9, 1.25, 0.2, 'etp_ras', explode=(0, 0.4, 0))
    pp = [hollow_pipe('ff', [(-4.7, 0, 0.4), (-5.2, 0, 0.4)], 0.06, 'cast_iron', 16), hollow_pipe('s2e', [(-3.9, 0, 0.35), (-3.6, 0, 0.35)], 0.06, 'cast_iron', 16),
          hollow_pipe('e2n', [(-2.85, -0.7, 0.2), (-2.85, -0.9, 0.2), (-2.2, -0.9, 0.2)], 0.04, 'paint_grey', 12, bend=0.04),
          hollow_pipe('e2n2', [(-2.2, -0.9, 0.32), (-2.2, -0.9, 1.35), (-1.6, -0.3, 1.35), (-1.6, -0.2, 1.1)], 0.04, 'paint_grey', 12, bend=0.05),
          hollow_pipe('n2a', [(-1.15, 0, 0.9), (X0 - 0.1, 0, 0.9)], 0.06, 'paint_grey', 16), hollow_pipe('a2c', [(X1 + 0.1, 0, 1.2), (2.0, 0, 1.2), (2.4, 0, z0 + 1.1), (2.6, 0, z0 + 1.1)], 0.06, 'paint_grey', 16, bend=0.06),
          hollow_pipe('uf', [(2.6, 0, 0.1), (2.6, 0, -0.05), (1.9, 1.25, -0.05), (1.9, 1.25, 0.08)], 0.04, 'paint_grey', 12, bend=0.05),
          hollow_pipe('ras', [(1.9, 1.25, 0.32), (1.9, 1.25, 1.75), (X0 + 0.3, 1.25, 1.75), (X0 + 0.3, 0.6, 1.75), (X0 + 0.3, 0.6, 1.3)], 0.035, 'paint_grey', 12, bend=0.05),
          hollow_pipe('was', [(1.9, 1.25, 1.75), (3.2, 1.25, 1.75), (3.2, 1.25, 0.6)], 0.025, 'paint_grey', 12, bend=0.04), _valve('wv', (2.7, 1.25, 1.75), 'X', 0.025, 'cast_iron'),
          hollow_pipe('te', [(2.6 + 0.85 + 0.15, 0, z0 + 0.92), (4.2, 0, z0 + 0.92)], 0.06, 'paint_grey', 16), box('fm', (0.14, 0.14, 0.14), (4.0, 0, z0 + 0.92), 'paint_blue_dark')]
    P(m, 'process_piping', 'Process Piping: Feed, Transfers, Clarifier Feed, Sludge Underflow, RAS & WAS Lines, Treated-Effluent Outlet & Flowmeter', 'piping', pp, explode=(0, 0, 0.4), ref='etp_piping', section='keep')
    m.flow('effluent', [(-5.2, 0, 0.4), (-3.6, 0.1, 0.35), (-2.85, 0.1, 0.25), (-2.85, -0.9, 0.2), (-2.2, -0.9, 1.35), (-1.6, -0.2, 1.1), (-1.15, 0.05, 0.9), (X0, 0.05, 0.9), (X1, 0.05, 1.2),
                         (2.6, 0, z0 + 1.1), (2.6, 0.1, z0 + 0.5), (3.4, 0.1, z0 + 0.85), (4.3, 0, z0 + 0.92)], 'water', 0.025, 0.5)
    m.flow('ras', [(2.6, 0, 0.12), (2.6, 0, -0.05), (1.9, 1.25, 0.1), (1.9, 1.25, 1.75), (X0 + 0.3, 1.25, 1.75), (X0 + 0.3, 0.6, 1.3)], 'sand', 0.018, 0.3)
    m.flow('air', [(0.2, 1.33, 0.4), (0.2, 1.3, H + 0.25), (0.2, 0.4, H + 0.25), (0.2, 0.4, 0.18)], 'air', 0.015, 0.3)
    _press(m, [box(f'bz{k}', (b - a, 0.04, 0.12), ((a + b) / 2, 0.0, 2.1), f'pressure_{lev}') for k, (a, b, lev) in enumerate(((-4.7, -3.9, 9), (-3.6, -2.4, 8), (-2.05, -1.15, 7), (X0, X1, 4), (1.75, 3.45, 1)))],
           'Pollution load falls along the train', 'Screening removes rags and grit; equalisation evens out flow and strength; neutralisation brings pH into the ≈ 6–9 range the bacteria tolerate. In the aeration tank '
           'bacteria oxidise dissolved organic matter (BOD/COD) using oxygen from the diffusers (DO ≈ 1.5–2 mg/L), growing into flocs. The clarifier settles the flocs: most are returned (RAS) to keep the biomass '
           '(MLSS ≈ 2,000–4,000 mg/L), the growth is wasted (WAS), and clear treated effluent leaves over the weir — typically > 90 % BOD removal. Discharge limits are set by the local regulator.', kind='pressure')
    return m.export(out)


# ===================================================================== metadata
_AIR = _std(('ISO 8573-1', 'Compressed air — contaminants and purity classes', 'Dew-point, particle and oil classes.'),
            ('ISA-7.0.01', 'Quality standard for instrument air', 'Instrument-air dew point and quality.'))
_PV = _std(('ASME BPVC VIII-1', 'Pressure vessels', 'Receiver / vessel design.'), ('Local pressure-equipment rules (e.g. PED / IBR)', 'Registration and inspection', 'Jurisdictional — to be verified.'))
_STM = _std(('ASME B31.1', 'Power piping', 'Steam & condensate piping.'), ('Spirax Sarco — The Steam & Condensate Loop', 'Steam system practice', 'Design guidance.'))
_CT = _std(('CTI ATC-105', 'Acceptance test code for water-cooling towers', 'Thermal performance.'), ('CTI STD-111 / AGMA 6010-class', 'Cooling-tower gear speed reducers', 'Gearbox selection & service factor.'))
_FIRE = _std(('NFPA 20', 'Installation of stationary pumps for fire protection', 'Pump, driver, controller, testing.'), ('NFPA 25', 'Inspection, testing and maintenance of water-based fire protection systems', 'Weekly / annual tests.'))
_WW = _std(('Metcalf & Eddy — Wastewater Engineering', 'Treatment and resource recovery', 'Process design.'), ('Local discharge consent / pollution-control board limits', 'Effluent standards', 'Site-specific — to be verified.'))


def _p(ref, what):
    return {ref: _c(what[0], what[1], what[2], what[3] if len(what) > 3 else '—', what[4] if len(what) > 4 else ('—',), what[5] if len(what) > 5 else ('Visual',))}


def _comp(*items):
    out = {}
    for ref, *what in items:
        out.update(_p(ref, what))
    return out


META = {
    'instrument_air_dryer': {'summary': ('An instrument air dryer removes water vapour from compressed air so control valves and instruments never see condensation or ice. This heated blower-purge type has two desiccant towers: one dries the air while the other is regenerated by heated ambient air from a blower, so very little dried compressed air is used for purging.'),
                             'classification': {'family': 'Compressed air', 'type': 'Twin-tower heated blower-purge desiccant dryer'}, 'model_configuration': {'animation': 'Moisture front rises in the drying tower; blower and heater regenerate the other'},
                             'standards': _AIR, 'references': ['ISO 8573-1', 'Compressed Air & Gas Institute (CAGI) handbook'],
                             'components': _comp(('iad_tower', 'Pressure vessels holding desiccant.', 'Twin vertical towers with diffusers and support screens.', 'Carbon steel, coded vessel.', 'Cycling pressure.', ['Fatigue at nozzles', 'Corrosion'], ['Statutory inspection']),
                                                 ('iad_desiccant', 'Adsorbs water vapour.', 'Activated alumina (optionally with molecular-sieve top layer).', 'Activated alumina / zeolite beads.', 'Dew point ≈ −40 °C.', ['Oil fouling', 'Bead attrition (dusting)', 'Liquid water slugs'], ['Dew-point trend', 'Desiccant sample / change ≈ 3–5 years']),
                                                 ('iad_valves', 'Direct flow to the drying tower and vent the regenerating tower.', 'Butterfly / poppet switching valves and check valves.', 'Steel/stainless, soft seats.', '—', ['Valve leakage → dew-point rise'], ['Cycle check, seat leak test']),
                                                 ('iad_filters', 'Protect the desiccant from oil and catch desiccant dust.', 'Coalescing pre-filter, particulate after-filter, auto drains.', 'Aluminium housings, glass-fibre elements.', '—', ['Element blocked (high ΔP)', 'Drain stuck'], ['ΔP gauge, element change']),
                                                 ('iad_regen', 'Heats ambient air and forces it through the wet bed.', 'Blower, electric heater, hot-purge line, exhaust silencer.', 'Steel/stainless.', '≈ 150–200 °C purge.', ['Heater element failure', 'Blower bearing wear'], ['Heater current, regeneration temperature']),
                                                 ('iad_controls', 'Sequences the cycle and checks dryness.', 'PLC with dew-point dependent switching and analyser.', '—', '—', ['Analyser drift'], ['Calibrate dew-point sensor']))},
    'air_receiver_dryer_package': {'summary': ('An air receiver and refrigerated dryer package stores compressed air to buffer demand and then cools it to about +3 °C so most of the water condenses and drains. Filters remove oil aerosols and dust, giving clean dry plant air.'),
                                   'classification': {'family': 'Compressed air', 'type': 'Vertical receiver + refrigerated dryer + filters'}, 'model_configuration': {'animation': 'Condensate collects and drains; refrigerant circulates; condenser fan turns'},
                                   'standards': _AIR + _PV, 'references': ['ISO 8573-1', 'CAGI handbook'],
                                   'components': _comp(('ard_receiver', 'Stores air, damps pulsation, lets condensate settle.', 'Vertical vessel on legs.', 'Carbon steel.', 'Max working pressure per nameplate.', ['Internal corrosion from standing water'], ['Thickness survey, hydrotest per rules']),
                                                       ('ard_drain', 'Collects condensate.', 'Bottom of the receiver.', '—', '—', ['Overflow if drain fails'], ['Daily check']),
                                                       ('ard_fittings', 'Connections and protection.', 'Inlet low, outlet high, safety valve, gauge, inspection opening, auto drain.', 'Steel/brass.', '—', ['Safety valve stuck', 'Drain blocked'], ['Lift-test safety valve, test drain']),
                                                       ('ard_dryer', 'Houses the dryer.', 'Sheet-metal cabinet.', 'Painted steel.'),
                                                       ('ard_hx', 'Cool, separate and re-heat the air.', 'Air-to-air and air-to-refrigerant exchangers, separator.', 'Aluminium/copper/stainless.', '≈ +3 °C dew point.', ['Fouling', 'Freezing if bypass control fails'], ['ΔP, dew point']),
                                                       ('ard_refrig', 'Provides cooling.', 'Hermetic compressor, condenser, fan, expansion valve.', 'Copper/steel.', '—', ['Refrigerant leak', 'Dirty condenser'], ['Suction pressure, condenser cleaning']),
                                                       ('ard_filters', 'Remove oil aerosol and particles.', 'Coalescing and dust filters with drains.', 'Aluminium/glass fibre.', '—', ['Blocked element'], ['ΔP, change interval']))},
    'nitrogen_generation_system': {'summary': ('A PSA nitrogen generator separates nitrogen from compressed air. Two towers filled with carbon molecular sieve take turns: under pressure the sieve takes up oxygen faster than nitrogen, so nitrogen passes to a buffer vessel; the tower is then depressurised to release the oxygen and regenerate.'),
                                   'classification': {'family': 'Gas utilities', 'type': 'Twin-bed PSA with carbon molecular sieve'}, 'model_configuration': {'animation': 'O₂ front advances; O₂ trapped, N₂ passes; exhaust from regenerating bed'},
                                   'standards': _PV + _std(('EIGA / CGA guidance', 'Nitrogen asphyxiation hazards', 'Oxygen-deficiency safety.'),), 'references': ['Gas separation by adsorption (Ruthven)'],
                                   'components': _comp(('n2_adsorber', 'Pressure vessels for the CMS.', 'Two towers with diffusers and compaction springs.', 'Carbon steel.', '≈ 7–10 bar(g), cycling.', ['Fatigue'], ['Statutory inspection']),
                                                       ('n2_cms', 'Separates O₂ from N₂ by diffusion rate.', 'Carbon molecular sieve pellets, tightly packed.', 'Carbon.', '—', ['Dusting if loose', 'Oil poisoning'], ['Purity trend']),
                                                       ('n2_valves', 'Sequence pressurise / equalise / vent.', 'Pneumatic angle-seat valves, silencer.', 'Stainless/brass.', '—', ['Leaking valve → purity drop'], ['Cycle check']),
                                                       ('n2_filters', 'Remove oil and vapour from feed air.', 'Coalescing + activated-carbon filters.', 'Aluminium.', '—', ['Breakthrough of oil'], ['Element change']),
                                                       ('n2_buffer', 'Smooths product flow.', 'Vertical vessel.', 'Carbon steel.'),
                                                       ('n2_controls', 'Checks purity, controls flow.', 'Flow valve, zirconia/electrochemical O₂ analyser, off-spec vent.', '—', '—', ['Analyser drift'], ['Calibrate with span gas']))},
    'nitrogen_storage_vessel': {'summary': ('A liquid nitrogen storage vessel keeps nitrogen as a liquid at about −196 °C inside a vacuum-insulated double-wall tank. A pressure-building coil holds tank pressure, and an ambient-air vaporiser turns the withdrawn liquid into gas for the plant.'),
                                'classification': {'family': 'Gas utilities', 'type': 'Vertical vacuum-insulated cryogenic tank with ambient vaporiser'}, 'model_configuration': {'animation': 'Level falls as liquid is used; frost grows on the vaporiser'},
                                'standards': _std(('EN 13458 / ASME VIII', 'Static vacuum-insulated cryogenic vessels', 'Design.'), ('EIGA Doc 115 / CGA P-12', 'Storage of cryogenic air gases at users\' premises', 'Siting & safety.')), 'references': ['EIGA documents'],
                                'components': _comp(('ln_outer', 'Vacuum jacket.', 'Outer shell.', 'Carbon steel.', '—', ['Vacuum loss (sweating/frost on shell)'], ['Check shell for cold spots']),
                                                    ('ln_inner', 'Holds the liquid.', 'Inner pressure vessel.', 'Austenitic stainless (cryogenic).', '−196 °C.', ['—'], ['Statutory inspection']),
                                                    ('ln_annulus', 'Limits heat leak.', 'Perlite powder / MLI under high vacuum.', 'Perlite.', '—', ['Vacuum degradation → high boil-off'], ['Boil-off / vacuum check']),
                                                    ('ln_pbc', 'Maintains tank pressure.', 'Finned coil and regulator.', 'Aluminium/stainless.'),
                                                    ('ln_vaporiser', 'Vaporises liquid with ambient heat.', 'Star-finned tubes.', 'Aluminium.', '—', ['Excess icing → cold gas downstream'], ['Defrost, outlet temperature']),
                                                    ('ln_piping', 'Fill, withdrawal and gas supply.', 'Valves, regulator, lines.', 'Stainless/brass.', '—', ['Trapped liquid overpressure'], ['Relief devices on every liquid section']),
                                                    ('ln_safety', 'Protects against overpressure and indicates contents.', 'Dual relief valves, burst disc, ΔP level gauge.', 'Brass/stainless.', '—', ['Valve icing'], ['Periodic test']))},
    'steam_distribution_header': {'summary': ('A steam distribution header receives steam from the boilers and distributes it to plant users. Branches take steam from the top of the header so it is dry; drip legs and steam traps remove condensate, and a pressure-reducing station supplies lower-pressure users.'),
                                  'classification': {'family': 'Steam utilities', 'type': 'Header with branch take-offs, drip leg trap station and PRV station'}, 'model_configuration': {'animation': 'Condensate runs to the drip leg; the trap discharges it'},
                                  'standards': _STM, 'references': ['Spirax Sarco — The Steam & Condensate Loop'],
                                  'components': _comp(('sh_header', 'Collects and distributes steam.', 'Large-bore header sloped toward drip legs, main stop valve, air vent.', 'Carbon steel (e.g. ASTM A106 B).', 'Boiler pressure / temperature.', ['Water hammer', 'Erosion', 'Corrosion under insulation'], ['Thickness survey, insulation condition']),
                                                      ('sh_insulation', 'Reduces heat loss and protects personnel.', 'Mineral wool with metal cladding.', 'Mineral wool/aluminium.', '—', ['Wet insulation → CUI'], ['Visual, thermography']),
                                                      ('sh_supports', 'Carry the pipe and allow expansion.', 'Shoes, guides and anchors.', 'Steel.', '—', ['Seized guides → overstress'], ['Check movement']),
                                                      ('sh_branches', 'Supply users with dry steam.', 'Top take-offs with isolation valves.', 'Steel.'),
                                                      ('sh_prv', 'Reduces pressure for LP users.', 'Isolation, pilot-operated PRV, safety valve, gauges.', 'Cast steel/ductile iron.', '—', ['PRV hunting', 'Seat wear → creep'], ['Set-point check, safety valve test']),
                                                      ('sh_trap', 'Removes condensate, holds steam.', 'Isolation, strainer, trap, test valve, check valve.', 'Steel/cast iron.', '—', ['Trap failed open (steam loss) or closed (water hammer)'], ['Trap survey (ultrasonic / temperature)']))},
    'condensate_recovery_system': {'summary': ('A condensate recovery system collects hot condensate from steam users and returns it to the boiler. A flash vessel releases low-pressure flash steam for reuse; the remaining condensate drains to a vented receiver and condensate pumps send it back to the boiler feed tank.'),
                                   'classification': {'family': 'Steam utilities', 'type': 'Flash vessel + vented receiver + duplex pump set'}, 'model_configuration': {'animation': 'Receiver level rises and falls with the float; pumps run; flash steam rises'},
                                   'standards': _STM, 'references': ['Spirax Sarco — The Steam & Condensate Loop'],
                                   'components': _comp(('cr_receiver', 'Collects condensate at atmospheric pressure.', 'Horizontal vented vessel on a raised stand.', 'Stainless/carbon steel.', '≈ 90–100 °C.', ['Corrosion', 'Overflow'], ['Level checks']),
                                                       ('cr_controls', 'Start/stop pumps.', 'Float switches / level probes, control panel.', '—', '—', ['Float sticking'], ['Function test']),
                                                       ('cr_flash', 'Separates flash steam.', 'Vertical vessel with tangential inlet.', 'Steel.'),
                                                       ('cr_piping', 'Inlets, vent, overflow, returns.', 'Pipes, check valves, gauge glass.', 'Steel.', '—', ['Vent blocked → pressurised receiver'], ['Inspect vent']),
                                                       ('cr_pumps', 'Return condensate.', 'Duty/standby centrifugal pumps.', 'Cast iron/stainless.', 'Low NPSH available.', ['Cavitation', 'Seal wear'], ['Noise, seal leakage']))},
    'cooling_tower_basin': {'summary': ('The cold-water basin collects the cooled water falling from a cooling tower\'s fill and feeds the circulating-water pumps through a sump and screens. Make-up water replaces evaporation, drift and blowdown; blowdown controls the dissolved-solids concentration; an overflow protects against flooding.'),
                            'classification': {'family': 'Cooling utilities', 'type': 'Concrete basin with pump sump'}, 'model_configuration': {'animation': 'Rain zone falls; make-up float valve modulates; water level steady'},
                            'standards': _CT, 'references': ['CTI guidelines'],
                            'components': _comp(('ctb_basin', 'Holds cold water; feeds the pumps.', 'Concrete basin sloped to a sump.', 'Reinforced concrete.', '—', ['Cracks/leaks', 'Silt build-up'], ['Annual clean, crack survey']),
                                                ('ctb_screens', 'Keep debris from the pumps.', 'Removable mesh screens.', 'Stainless.', '—', ['Blinding'], ['Clean regularly']),
                                                ('ctb_structure', 'Support the tower.', 'Columns, beams, louvres.', 'Concrete/FRP/timber.'),
                                                ('ctb_fill', 'Spread water for heat transfer; stop drift.', 'Film fill and drift eliminators.', 'PVC/PP.', '—', ['Fouling, collapse'], ['Inspect fill']),
                                                ('ctb_distribution', 'Spread hot water over the fill.', 'Header, laterals, nozzles.', 'PVC/FRP.', '—', ['Blocked nozzles'], ['Inspect spray pattern']),
                                                ('ctb_makeup', 'Replace water losses.', 'Float valve or level-controlled valve.', 'Brass/PVC.'),
                                                ('ctb_outlets', 'Outlet, blowdown, overflow, dosing.', 'Pipes and valves.', 'Steel/PVC.', '—', ['Blowdown valve failure → scaling'], ['Conductivity control']))},
    'cooling_tower_fan': {'summary': ('A cooling tower fan is a large, slow axial fan that draws air up through the tower. It sits in a flared fan stack that recovers velocity pressure, and is driven by a motor outside the air stream through a drive shaft and a right-angle gearbox.'),
                          'classification': {'family': 'Cooling utilities', 'type': 'Induced-draught axial fan with gearbox drive'}, 'model_configuration': {'animation': 'Fan and drive shaft turn; air rises through the stack'},
                          'standards': _CT, 'references': ['CTI guidelines'],
                          'components': _comp(('ctf_structure', 'Casing, fill and deck.', 'Tower structure.', 'Concrete/FRP.'),
                                              ('ctf_stack', 'Shroud and velocity recovery.', 'Fan deck and flared stack.', 'FRP.', '—', ['Uneven tip clearance'], ['Measure tip clearance']),
                                              ('ctf_fan', 'Moves air.', 'Hub and adjustable-pitch FRP blades.', 'FRP/aluminium.', 'Tip speed ≲ 60 m/s.', ['Blade imbalance/cracks', 'Pitch mismatch'], ['Vibration, blade pitch check']),
                                              ('ctf_gearbox', 'Reduces speed, turns 90°.', 'Right-angle gearbox on torque tube, vibration switch.', 'Cast iron.', '—', ['Low oil', 'Bearing wear'], ['Oil level, vibration']),
                                              ('ctf_motor', 'Drives the fan.', 'TEFC motor, often two-speed or VFD.', '—'),
                                              ('ctf_shaft', 'Transmits power to the gearbox.', 'Composite/steel tube with flexible couplings.', 'Carbon fibre/steel.', '—', ['Misalignment', 'Coupling element wear'], ['Alignment']))},
    'cooling_tower_gearbox': {'summary': ('A cooling tower gearbox is a right-angle speed reducer. A spiral-bevel gear set turns the horizontal drive through 90° and a helical stage completes about a 10:1 reduction to the vertical fan shaft. It is splash-lubricated from an oil bath and designed for a wet, cycling environment.'),
                              'classification': {'family': 'Cooling utilities', 'type': 'Two-stage right-angle spiral-bevel / helical reducer'}, 'model_configuration': {'animation': 'Pinion, intermediate and output shafts turn at decreasing speed'},
                              'standards': _CT + _std(('AGMA 2005 / ISO 23509', 'Bevel gear design', 'Bevel gear geometry.'),), 'references': ['CTI STD-111', 'AGMA standards'],
                              'components': _comp(('ctg_housing', 'Holds gears, bearings and oil.', 'Cast housing with mounting flange.', 'Cast iron.'),
                                                  ('ctg_oil', 'Lubricates and cools.', 'Splash oil bath.', 'Mineral/synthetic gear oil (ISO VG per maker).', '—', ['Water contamination', 'Low level'], ['Oil analysis, level check']),
                                                  ('ctg_input', 'Receives motor power.', 'Input shaft with spiral-bevel pinion.', 'Case-hardened alloy steel.', '≈ 1500 rpm.', ['Pitting', 'Seal leak'], ['Vibration, contact pattern']),
                                                  ('ctg_intermediate', 'First reduction, 90° turn.', 'Spiral-bevel gear + helical pinion.', 'Alloy steel.'),
                                                  ('ctg_output', 'Drives the fan.', 'Output shaft, helical gear, hub flange.', 'Alloy steel.', '≈ 150 rpm, high torque, fan thrust.', ['Bearing wear'], ['Shaft runout']),
                                                  ('ctg_bearings', 'Carry radial and thrust loads.', 'Taper-roller bearings.', 'Bearing steel.', '—', ['Fatigue spalling'], ['Vibration spectrum']),
                                                  ('ctg_accessories', 'Monitor and maintain oil.', 'Sight glass, breather, remote fill/drain, vibration switch, seal.', '—', '—', ['Breather blocked'], ['Inspect']))},
    'emergency_diesel_firewater_system': {'summary': ('An emergency diesel firewater system is a fire pump driven by a dedicated diesel engine, so firefighting water is available even if electrical power fails. It starts automatically when the fire main pressure falls and delivers rated flow at rated pressure to hydrants, monitors and sprinkler systems.'),
                                          'classification': {'family': 'Fire protection', 'type': 'Diesel-driven horizontal split-case fire pump package'}, 'model_configuration': {'animation': 'Engine, radiator fan, drive and impeller turn'},
                                          'standards': _FIRE, 'references': ['NFPA 20', 'NFPA 25'],
                                          'components': _comp(('dfw_skid', 'Common base.', 'Fabricated base frame.', 'Steel.'),
                                                              ('dfw_engine', 'Drives the pump independently of mains power.', 'Listed fire-pump diesel engine.', '—', '—', ['Failure to start (batteries, fuel)', 'Overheating'], ['Weekly run test']),
                                                              ('dfw_cooling', 'Cools the engine.', 'Radiator and fan (or raw-water heat exchanger).', 'Copper/aluminium.'),
                                                              ('dfw_drive', 'Connects engine and pump.', 'Flywheel, drive shaft, flexible coupling.', 'Steel.', '—', ['Misalignment'], ['Alignment check']),
                                                              ('dfw_exhaust', 'Removes exhaust safely.', 'Bellows, silencer, tailpipe.', 'Steel.', '—', ['Back-pressure too high'], ['Inspect']),
                                                              ('dfw_pump', 'Pressure casing.', 'Axially split double-volute casing.', 'Cast iron/ductile iron.'),
                                                              ('dfw_impeller', 'Adds energy to the water.', 'Double-suction impeller on shaft.', 'Bronze.', '—', ['Wear ring wear'], ['Annual flow test']),
                                                              ('dfw_suction', 'Supplies water.', 'Suction pipe, OS&Y valve, gauge.', 'Steel.'),
                                                              ('dfw_discharge', 'Delivers and tests flow.', 'Check/gate valves, relief valve, test header.', 'Steel/brass.', '—', ['Relief valve stuck'], ['Annual flow test via test header']),
                                                              ('dfw_jockey', 'Maintains system pressure.', 'Small electric pump.', '—'),
                                                              ('dfw_fuel', 'Fuel supply.', 'Bunded day tank and lines.', 'Steel.', '—', ['Water in fuel, low level'], ['Level check, water drain']),
                                                              ('dfw_controls', 'Automatic start and monitoring.', 'Listed controller, two battery sets.', '—', '—', ['Battery failure'], ['Weekly test']))},
    'sewage_lift_station': {'summary': ('A sewage lift station collects sewage in a wet well and pumps it up to a higher sewer or treatment plant. Submersible pumps on guide rails start and stop on level, and a separate valve chamber holds the check and isolation valves.'),
                            'classification': {'family': 'Wastewater', 'type': 'Wet-well submersible pumping station'}, 'model_configuration': {'animation': 'Level rises then is pumped down; duty impeller turns'},
                            'standards': _WW + _std(('EN 752 / Hydraulic Institute 9.8', 'Drain & sewer systems / pump intake design', 'Wet-well design.'),), 'references': ['Metcalf & Eddy'],
                            'components': _comp(('sls_well', 'Stores incoming sewage.', 'Concrete wet well with benching, slab and hatch.', 'Concrete.', 'Corrosive (H₂S).', ['Concrete corrosion'], ['Confined-space entry only with permit']),
                                                ('sls_inlet', 'Stops large solids reaching pumps.', 'Inlet pipe and basket screen.', 'Stainless.', '—', ['Basket full'], ['Empty regularly']),
                                                ('sls_pumps', 'Lift the sewage.', 'Submersible non-clog pumps on duckfoot bends and guide rails.', 'Cast iron.', '—', ['Rag clogging', 'Seal failure (moisture alarm)'], ['Current, run hours, seal monitor']),
                                                ('sls_controls', 'Control pumps and alarms.', 'Floats, ultrasonic level, kiosk, vent.', '—', '—', ['Float tangling'], ['Function test']),
                                                ('sls_valves', 'Prevent backflow and isolate.', 'Valve chamber with check & gate valves and header.', 'Ductile iron.', '—', ['Check valve slamming'], ['Inspect']))},
    'effluent_treatment_plant': {'summary': ('An effluent treatment plant cleans industrial wastewater before discharge or reuse. Screening removes coarse solids, equalisation evens out flow and strength, neutralisation corrects pH, an activated-sludge aeration tank lets bacteria consume dissolved organics, and a secondary clarifier settles the biomass.'),
                                 'classification': {'family': 'Wastewater', 'type': 'Conventional activated-sludge ETP'}, 'model_configuration': {'animation': 'Bubbles rise, mixers and rakes turn, sludge returns'},
                                 'standards': _WW, 'references': ['Metcalf & Eddy — Wastewater Engineering'],
                                 'components': {**_agt('etp_neut'), **_thk('etp_clar'),
                                                **_comp(('etp_neut', 'Corrects pH for the biology.', 'pH probe/controller, acid and caustic dosing.', 'PP/PVDF, stainless.', 'pH ≈ 6 – 9 target.', ['Probe fouling → wrong dose'], ['Calibrate probe weekly']),
                                                        ('etp_screen', 'Removes coarse solids.', 'Channel with bar screen.', 'Concrete/stainless.', '—', ['Blinding'], ['Rake regularly']),
                                                        ('etp_eq', 'Evens out flow and load.', 'Mixed tank with transfer pump.', 'Concrete.', '—', ['Settled solids'], ['Mixer check']),
                                                        ('etp_aeration', 'Biological treatment.', 'Rectangular aeration tank.', 'Concrete.', 'DO ≈ 1.5–2 mg/L.', ['Bulking sludge', 'Foaming'], ['DO, MLSS, SVI']),
                                                        ('etp_diffusers', 'Transfer oxygen.', 'Fine-bubble membrane diffusers on an air grid.', 'EPDM/PP.', '—', ['Membrane fouling'], ['Air pressure trend']),
                                                        ('etp_blower', 'Supplies air.', 'Positive-displacement or turbo blower.', '—'),
                                                        ('etp_ras', 'Returns and wastes sludge.', 'Centrifugal sludge pump.', 'Cast iron.'),
                                                        ('etp_piping', 'Connects units.', 'Gravity and pumped lines, flowmeter.', 'Steel/HDPE.'))}},
}
BUILDERS = {k: globals()[k] for k in META}
