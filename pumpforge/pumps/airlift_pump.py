"""
Airlift Pump — compressed air injected near the bottom of a submerged riser pipe
forms a light air-water mixture; the heavier surrounding water pushes it up the
riser to discharge above the liquid level.  No moving parts in the liquid.
Tank shown cut away; axis Z, tank floor at z = 0.
"""
import math
from pumpforge.core import Model, lathe, lathe_split, ring_profile, cyl, box, csg, split, join, merge_halves, split_many, TAU
from pumpforge.parts import hollow_pipe, add_tracers, add_motor_h, pressure_gauge, gate_valve
from pumpforge.common_meta import C

ID = 'airlift_pump'
H = 2.4          # tank height
RT = 0.7         # tank radius
ZW = 2.0         # water level
RR = 0.05        # riser radius


def build(out_dir):
    m = Model(ID, 'Airlift Pump (Compressed-Air Riser)', 'D · Special-Purpose Pumping Systems', META)
    tank = lathe('tank', [(RT, 0.0), (RT + 0.012, 0.0), (RT + 0.012, H), (RT, H)], 'paint_grey', 96, a0=0.0, a1=math.pi, cap_mat='paint_grey')
    floor = lathe('floor', [(0, -0.02), (RT + 0.012, -0.02), (RT + 0.012, 0.0), (0, 0.0)], 'paint_grey', 96, a0=0.0, a1=math.pi, cap_mat='paint_grey')
    lvl = lathe('level', [(RT - 0.02, ZW - 0.004), (RT, ZW - 0.004), (RT, ZW + 0.004), (RT - 0.02, ZW + 0.004)], 'flow_suction', 96, a0=0.0, a1=math.pi, cap_mat='flow_suction')
    p = m.part('tank', 'Sump / Tank (shown cut away) with Water-Level Mark', 'structure', explode=(0, 0.5, 0), info={'ref': 'al_tank'})
    p.add(join('tank', [tank, floor, lvl]), smooth_angle=40)
    # riser: from foot (z 0.15) up through the tank top, bending to the separator
    xr = 0.0
    riser = hollow_pipe('riser', [(xr, 0, 0.12), (xr, 0, H + 0.35), (0.9, 0, H + 0.35)], RR, 'stainless', 32, bend=0.18)
    p = m.part('riser_pipe', 'Riser (Eductor) Pipe', 'riser', section='split', explode=(0.0, 0, 0.0), info={'ref': 'al_riser'})
    p.add_split(*split_many('riser', [riser]), smooth_angle=50)
    # foot piece: annular air chamber with injection holes
    zf = 0.25
    foot = csg('foot', [lathe('fp', [(RR, zf - 0.08), (RR + 0.03, zf - 0.06), (RR + 0.03, zf + 0.06), (RR, zf + 0.08)], 'brass', 64)],
               [lathe('fpi', [(RR - 0.004, zf - 0.05), (RR + 0.022, zf - 0.04), (RR + 0.022, zf + 0.04), (RR - 0.004, zf + 0.05)], 'brass', 64)] +
               [cyl(f'h{i}', 0.004, -0.02, 0.02, 'brass', 8, axis='X', center=(RR * math.cos(TAU * i / 12), RR * math.sin(TAU * i / 12), zf)) for i in range(12)],
               'brass')
    bell = lathe('bell', [(RR - 0.004, 0.12), (RR + 0.004, 0.12), (0.12, 0.04), (0.11, 0.04)], 'stainless', 64)
    p = m.part('foot_piece', 'Air Injector (Foot Piece) & Inlet Bell', 'air_injection', section='split', explode=(0.5, 0, -0.2), info={'ref': 'al_foot'})
    p.add_split(*split_many('foot_piece', [foot, bell]), smooth_angle=50)
    # air line from the blower down to the foot piece
    air = hollow_pipe('air_line', [(-0.9, 0, H + 0.6), (-0.15, 0, H + 0.6), (-0.15, 0, zf), (-RR - 0.03, 0, zf)], 0.016, 'paint_yellow', 20, bend=0.08)
    p = m.part('air_line', 'Compressed-Air Supply Line', 'air_injection', section='split', explode=(-0.3, 0, 0), info={'ref': 'al_airline'})
    p.add_split(*split_many('air_line', [air]), smooth_angle=50)
    v = gate_valve('air_valve', (-0.6, 0, H + 0.6), 0.016)
    g = pressure_gauge('air_gauge', (-0.4, 0.0, H + 0.616))
    p = m.part('air_controls', 'Air Control Valve & Pressure Gauge', 'instrumentation', explode=(-0.3, 0, 0.3), info={'ref': 'pressure_gauge'})
    p.add(join('air_controls', [v, g]), smooth_angle=50)
    # blower on a platform
    plat = box('plat', (0.9, 0.7, 0.04), (-1.25, 0, H + 0.2), 'paint_grey', bevel=0.004)
    legs = [box(f'pl{i}', (0.05, 0.05, H + 0.18), (-1.25 + sx * 0.4, sy * 0.3, (H + 0.18) / 2), 'paint_grey') for i, (sx, sy) in
            enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1)))]
    bl = csg('blower', [lathe('bl', [(0, -0.12), (0.2, -0.12), (0.2, 0.12), (0, 0.12)], 'paint_blue', 64, axis='Y', center=(-1.05, 0, H + 0.42)),
                        cyl('bo', 0.035, -1.05, -0.9, 'paint_blue', 24, axis='X', center=(0, 0, H + 0.6))], [], 'paint_blue')
    p = m.part('blower', 'Air Blower / Compressor & Platform', 'air_supply', explode=(-0.6, 0, 0.3), info={'ref': 'al_blower'})
    p.add(join('blower', [plat, bl] + legs), smooth_angle=40)
    n0 = len(m.parts)
    add_motor_h(m, 'm_', -1.3, H + 0.42, 0.12, 0.34, H + 0.22, 0.02, 0.05, explode_dx=-0.5, revs=4)
    from mathutils import Matrix
    from pumpforge.parts import transform_parts
    transform_parts(m, m.parts[n0:], Matrix.Translation((-2.6, 0, 0)) @ Matrix.Rotation(math.pi, 4, 'Z'))
    for prt in m.parts[n0:]:
        prt.pivot.y = -prt.pivot.y
    # separator / discharge box
    sep = csg('separator', [box('sb', (0.4, 0.4, 0.5), (1.0, 0, H + 0.15), 'paint_grey', bevel=0.01)],
              [box('sbi', (0.37, 0.37, 0.5), (1.0, 0, H + 0.2), 'paint_grey', bevel=0.005), cyl('so', 0.04, 0.95, 1.4, 'paint_grey', 24, axis='X', center=(0, 0, H - 0.05))],
              'paint_grey')
    p = m.part('separator', 'Air Separator / Discharge Box', 'riser', section='split', explode=(0.4, 0, 0.2), info={'ref': 'al_separator'})
    p.add_split(*split(sep), smooth_angle=40)
    # tracers: air bubbles (green) rising in the riser, water entering the bell
    add_tracers(m, 'air_bubbles', 'Air Bubbles (Tracers)', [(-0.9, 0.0, H + 0.6), (-0.15, 0.0, H + 0.6), (-0.15, 0.0, zf), (0.0, 0.0, zf), (0.0, 0.0, H + 0.3),
                                                           (0.3, 0.0, H + 0.35), (0.95, 0.0, H + 0.6)], n=18, radius=0.018, mat='air', loops=1)
    add_tracers(m, 'water_flow', 'Water Flow (Tracers)', [(0.5, 0.0, 0.3), (0.12, 0.0, 0.06), (0.0, 0.0, 0.14), (0.0, 0.0, H + 0.3), (0.4, 0.0, H + 0.35),
                                                          (1.0, 0.0, H), (1.4, 0.0, H - 0.05)], n=18, radius=0.014, mat='flow_suction')
    m.flow('flow_water', [(0.6, 0.0, 0.4), (0.12, 0.0, 0.06), (0.0, 0.0, 0.14), (0.0, 0.0, H + 0.3), (0.4, 0.0, H + 0.35), (1.0, 0.0, H), (1.5, 0.0, H - 0.05)],
           'flow_discharge', 0.012, 0.3)
    m.flow('flow_air', [(-0.9, 0.0, H + 0.6), (-0.15, 0.0, H + 0.6), (-0.15, 0.0, zf), (-0.05, 0.0, zf)], 'air', 0.01, 0.3)
    return m.export(out_dir)


META = {
    'summary': ('An airlift pump has no moving parts in the liquid. Compressed air is released through small holes near the '
                'bottom of a vertical riser pipe that stands in the liquid. The air–water mixture inside the riser is lighter '
                'than the water outside, so the outside water pressure (submergence) pushes the mixture up and out of the top. '
                'The deeper the injection point relative to the lift, the better the efficiency; typical submergence ratios '
                'are 50–70 %. Used for well development, aquaculture, wastewater sludge and grit transfer, and pumping corrosive '
                'or abrasive liquids.'),
    'classification': {'family': 'Kinetic / buoyancy (gas-lift)', 'configuration': 'Airlift riser with foot-piece air injector'},
    'model_configuration': {'submergence_ratio_note': 'Submergence ratio = submergence / (submergence + lift); ~0.5–0.7 typical (verify for design)',
                            'water_level_m': ZW, 'riser_diameter_mm': 2 * RR * 1000},
    'standards': [{'id': '—', 'title': 'No single product standard', 'relevance': 'Design is by empirical correlations and manufacturer data; pressure vessels/blowers follow their own standards.', 'edition': '—'}],
    'references': ['Karassik et al., Pump Handbook — airlift pumps.', 'Stenning A.H., Martin C.B., "An analytical and experimental study of air-lift pump performance", ASME J. Eng. Power 1968.'],
    'components': {
        'al_tank': C('Holds the liquid; its level sets the submergence.', 'Tank, well or sump.', 'Steel, concrete.', 'Level must stay above minimum for airlift to work.', ['Level too low → no flow'], ['Level monitoring']),
        'al_riser': C('Vertical pipe in which the air–water mixture rises.', 'Smooth pipe sized for mixture velocity.', 'Stainless, PVC, HDPE, steel.', 'Two-phase flow (slug/churn).', ['Scaling', 'Clogging'], ['Clean riser']),
        'al_foot': C('Injects air uniformly into the riser and admits water through the bell.', 'Annular air chamber with small holes (or diffuser) around the riser.', 'Brass, stainless, plastic.',
                     'Hole size affects bubble size and efficiency.', ['Blocked holes'], ['Air pressure trend']),
        'al_airline': C('Carries compressed air from blower to foot piece.', 'Small-bore pipe.', 'Steel, PVC.', 'Air pressure must exceed submergence head.', ['Leaks'], ['Pressure check']),
        'al_blower': C('Supplies low-pressure air.', 'Rotary lobe/side-channel blower or compressor.', 'Cast iron/aluminium.', 'Delivery pressure > static head at the injection point.', ['Filter clogging'], ['Filter, pressure']),
        'al_separator': C('Lets air escape and directs water to the outlet.', 'Open box with outlet nozzle.', 'Steel/plastic.', 'Vent to atmosphere.', ['Splashing'], ['Visual']),
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
