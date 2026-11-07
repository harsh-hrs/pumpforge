"""
Plunger Pump — horizontal triplex reciprocating pump.  A crankshaft (120° throws)
drives three crossheads and solid plungers; each plunger displaces liquid in a
pumping chamber of the fluid end with spring-loaded suction and discharge
valves.  The plunger seals in stationary packing, so it suits high pressure.
Crankshaft along +Y; plungers along X; cut plane y = middle cylinder.
"""
import math
from pumpforge.core import (Model, lathe, lathe_split, ring_profile, cyl, box, csg, split, join, merge_halves, split_faces, split_many, TAU)
from pumpforge.parts import add_drive_y, nozzle_bolts, pipe
from pumpforge.recip import power_end, motion_keys, RECIP_META, crosshead_x
from pumpforge.common_meta import C

ID = 'plunger_pump'
CZ = 0.36
BP = 0.0
YS = (0.0, 0.16, 0.32)
YC = 0.16
XC, R, L = 0.62, 0.04, 0.26


def build(out_dir, pump_id=ID, title='Triplex Plunger Pump', meta=None):
    m = Model(pump_id, title, 'C · Reciprocating Positive-Displacement Pumps', meta or META)
    phases = [0.0, TAU / 3, 2 * TAU / 3]
    cyls, pe = power_end(m, YS, CZ, XC, R, L, phases, YC, mat='paint_blue', revs=1.0, rod_to=0.15, bp=BP)
    xmin = XC - R - L
    mat = 'paint_grey'
    # ---------------- fluid end
    ya, yb = YS[0] - 0.09, YS[-1] + 0.09
    outs = [box('fe', (0.2, yb - ya, 0.24), (-0.02, (ya + yb) / 2, CZ), mat, bevel=0.012),
            cyl('sm', 0.05, ya - 0.04, yb + 0.04, mat, 48, axis='Y', center=(-0.04, 0, CZ - 0.16)),
            cyl('dm', 0.045, ya - 0.04, yb + 0.04, mat, 48, axis='Y', center=(-0.04, 0, CZ + 0.16)),
            cyl('smf', 0.085, ya - 0.06, ya - 0.04, mat, 48, axis='Y', center=(-0.04, 0, CZ - 0.16), ch=0.003),
            cyl('dmf', 0.08, yb + 0.04, yb + 0.06, mat, 48, axis='Y', center=(-0.04, 0, CZ + 0.16), ch=0.003)]
    ins = [cyl('smi', 0.038, ya - 0.07, yb + 0.03, mat, 48, axis='Y', center=(-0.04, 0, CZ - 0.16)),
           cyl('dmi', 0.033, ya - 0.03, yb + 0.07, mat, 48, axis='Y', center=(-0.04, 0, CZ + 0.16))]
    for i, y in enumerate(YS):
        ins += [cyl(f'pb{i}', 0.024, -0.07, 0.1, mat, 48, axis='X', center=(0, y, CZ)),
                cyl(f'vb{i}', 0.034, CZ - 0.16, CZ + 0.16, mat, 48, center=(-0.04, y, 0))]
    fe = csg('fluid_end', outs, ins, mat)
    fb, ff = split(fe, 'y', YC)
    p = m.part('fluid_end', 'Fluid End (Cylinder Block) with Manifolds', 'fluid_end', section='split', explode=(-0.35, 0, 0), info={'ref': 'fluid_end'})
    p.add_split(fb, ff, smooth_angle=40)
    # valves (suction lower, discharge upper) per cylinder
    for i, c in enumerate(cyls):
        y = c['y']
        for kind, zs in (('suction', CZ - 0.075), ('discharge', CZ + 0.055)):
            seat = lathe(f'seat{kind}{i}', [(0.018, zs - 0.01), (0.034, zs - 0.01), (0.034, zs), (0.022, zs), (0.018, zs - 0.004)], 'stainless', 48, center=(-0.04, y, 0))
            p = m.part(f'{kind}_seat_{i + 1}', f'{kind.title()} Valve Seat {i + 1}', 'valves', section='split', explode=(-0.35, 0, -0.25 if kind == 'suction' else 0.25),
                       info={'ref': 'valve_seat_r'})
            p.add_split(*split_many(f'vs{kind}{i}', [seat], 'y', YC))
            disc = join(f'vd{kind}{i}', [cyl(f'vdd{kind}{i}', 0.026, zs + 0.0, zs + 0.008, 'steel', 40, center=(-0.04, y, 0), ch=0.001),
                                          cyl(f'vds{kind}{i}', 0.006, zs + 0.008, zs + 0.03, 'steel', 16, center=(-0.04, y, 0))])
            from pumpforge.shapes import sweep_tube
            spr = sweep_tube(f'vsp{kind}{i}', [(-0.04 + 0.014 * math.cos(TAU * 5 * k / 60), y + 0.014 * math.sin(TAU * 5 * k / 60), zs + 0.009 + 0.022 * k / 60)
                                               for k in range(61)], 0.0018, 'steel', 8)
            p = m.part(f'{kind}_valve_{i + 1}', f'{kind.title()} Valve Disc & Spring {i + 1}', 'valves', explode=(-0.35, -0.12, -0.3 if kind == 'suction' else 0.3),
                       info={'ref': 'valve_disc_r'})
            vm = p.add(join(f'valve{kind}{i}', [disc, spr]), smooth_angle=50)
            mk = motion_keys(c['lk'], kind)
            m.keyframes(vm, 'Operate', 'location', [(f, (0, 0, 0.007 * v)) for f, v in mk])
        # plunger (moves with crosshead)
        x_t0 = c['x0'] - xmin - 0.055
        pl = join(f'plunger{i}', [cyl(f'pl{i}', 0.0195, x_t0, x_t0 + 0.2, 'chrome', 40, axis='X', center=(0, y, CZ), ch=0.002),
                                  cyl(f'plc{i}', 0.026, x_t0 + 0.2, x_t0 + 0.225, 'steel_dark', 6, axis='X', center=(0, y, CZ))])
        p = m.part(f'plunger_{i + 1}', f'Plunger {i + 1} (Hard-Coated)', 'reciprocating', pivot=(x_t0, y, CZ), explode=(-0.1, 0, 0.32 + 0.04 * i),
                   info={'ref': 'plunger'})
        pm = p.add(pl, smooth_angle=40)
        m.keyframes(pm, 'Operate', 'location', c['lk'])
        # stuffing box packing
        pk = [lathe(f'pk{i}{k}', ring_profile(0.0198, 0.03, 0.085 + k * 0.012, 0.095 + k * 0.012), 'ptfe', 40, axis='X', center=(0, y, CZ)) for k in range(3)]
        pk.append(lathe(f'gl{i}', [(0.0198, 0.121), (0.03, 0.121), (0.03, 0.08), (0.045, 0.08), (0.045, 0.135), (0.0198, 0.135)], 'steel', 48, axis='X', center=(0, y, CZ)))
        p = m.part(f'packing_{i + 1}', f'Plunger Packing & Gland {i + 1}', 'shaft_seal', section='split', explode=(-0.05, 0, -0.3 - 0.04 * i), info={'ref': 'plunger_packing'})
        p.add_split(*split_many(f'pk{i}', pk, 'y', YC))
    # distance piece (spacer frame with open windows)
    dp = csg('distance_piece', [box('dp', (pe['xg0'] - 0.08, yb - ya, 0.22), ((pe['xg0'] + 0.08) / 2, (ya + yb) / 2, CZ), 'paint_blue', bevel=0.01)],
             [box('dpw', (pe['xg0'] - 0.14, yb - ya + 0.1, 0.16), ((pe['xg0'] + 0.08) / 2, (ya + yb) / 2, CZ), 'paint_blue', bevel=0.01),
              box('dpz', (pe['xg0'] - 0.14, yb - ya - 0.04, 0.3), ((pe['xg0'] + 0.08) / 2, (ya + yb) / 2, CZ), 'paint_blue', bevel=0.01)], 'paint_blue')
    p = m.part('distance_piece', 'Distance Piece (Spacer Frame)', 'power_end', section='split', explode=(0.0, 0, 0.45), info={'ref': 'distance_piece'})
    p.add_split(*split(dp, 'y', YC), smooth_angle=40)
    # gear reducer + motor along +Y from crankshaft end
    y_e = pe['y1'] + 0.42
    gb = csg('reducer', [box('gb', (0.26, 0.2, 0.3), (XC, pe['y1'] + 0.24, CZ - 0.02), 'paint_grey', bevel=0.02)],
             [box('gbi', (0.22, 0.16, 0.26), (XC, pe['y1'] + 0.24, CZ - 0.02), 'paint_grey', bevel=0.015)], 'paint_grey')
    p = m.part('gear_reducer', 'Gear Reducer', 'power_transmission', section='split', explode=(0.4, 0.3, 0), info={'ref': 'gear_reducer_r'})
    p.add_split(*split(gb, 'y', pe['y1'] + 0.24), smooth_angle=40)
    add_drive_y(m, y_e, CZ, BP, 0.03, motor_R=0.15, motor_L=0.46, revs=1, x_off=XC, base=False)
    m.flow('flow_in', [(-0.04, ya - 0.3, CZ - 0.16), (-0.04, YC, CZ - 0.16), (-0.04, YC, CZ - 0.06), (-0.02, YC, CZ - 0.01), (0.04, YC, CZ)],
           'flow_suction', 0.006, 0.08)
    m.flow('flow_out', [(0.04, YC, CZ + 0.005), (-0.03, YC, CZ + 0.02), (-0.04, YC, CZ + 0.16), (-0.04, yb + 0.3, CZ + 0.16)], 'flow_discharge', 0.006, 0.08)
    return m.export(out_dir)


META = {
    'summary': ('A reciprocating pump in which a smooth solid plunger moves in and out of a pumping chamber through stationary '
                'packing. As the plunger withdraws, the chamber pressure falls, the suction valve opens and liquid enters; as it '
                'advances, the suction valve closes, pressure rises and the discharge valve opens. Three plungers driven 120° '
                'apart (triplex) smooth the flow. Flow depends only on speed and displacement; pressure is limited by rod load '
                'and fluid-end strength, so plunger pumps reach very high pressures (water jetting, hydrostatic test, injection).'),
    'classification': {'family': 'Positive displacement – reciprocating', 'configuration': 'Horizontal, triplex, single-acting plunger, crank-driven'},
    'model_configuration': {'cylinders': 3, 'stroke_mm': 2 * R * 1000, 'crank_phasing': '120°', 'valves': 'Spring-loaded disc (plate) valves',
                            'flow_formula': 'Q = n_cyl × (π/4·d²) × stroke × N × ηv (single-acting)'},
    'standards': [
        {'id': 'API 674', 'title': 'Positive Displacement Pumps – Reciprocating', 'relevance': 'Process service reciprocating pumps (rod load, pulsation, valves).', 'edition': 'to be verified'},
        {'id': 'ANSI/HI 6.1-6.5', 'title': 'Reciprocating Power Pumps', 'relevance': 'Nomenclature, application and operation.', 'edition': 'to be verified'},
        {'id': 'API 674 / API 618 pulsation guidance', 'title': 'Pulsation and vibration control', 'relevance': 'Dampener and piping design.', 'edition': 'to be verified'},
    ],
    'references': ['Karassik et al., Pump Handbook — reciprocating pumps.', 'Hydraulic Institute ANSI/HI 6.1-6.5 (scope summary).'],
    'components': {**RECIP_META,
        'fluid_end': C('Pressure-containing block with pumping chambers, valve bores and suction/discharge manifolds.', 'Forged or cast block; valve covers for access.',
                       'Forged steel, stainless, duplex; cast iron/bronze for low pressure.', 'Cyclic pressure → fatigue design at bore intersections.',
                       ['Fatigue cracking at cross-bores', 'Valve seat washout'], ['NDT at bore intersections', 'Valve seat condition']),
        'valve_seat_r': C('Sealing seat for the valve disc.', 'Replaceable tapered seat.', 'Hardened stainless/steel.', 'High-velocity flow when opening.', ['Washout/erosion'], ['Seat condition']),
        'valve_disc_r': C('Automatic check valve: opens by pressure difference, closed by spring.', 'Disc/plate with spring and guide.', 'Stainless steel, polymer (PEEK) discs.',
                          'Suction valves open on the suction stroke, discharge valves on the delivery stroke.', ['Spring breakage', 'Disc wear → slip'], ['Volumetric efficiency trend']),
        'plunger': C('Displaces liquid as it enters the chamber.', 'Solid ground plunger, often ceramic or hard-coated, clamped to the extension rod.',
                     'Stainless with ceramic/tungsten carbide coating, solid ceramic.', 'Surface finish critical for packing life.', ['Scoring', 'Coating chipping'], ['Surface condition']),
        'plunger_packing': C('Seals around the moving plunger.', 'Rings of packing in a stuffing box with gland (spring-loaded or adjustable); lubricated or flushed.',
                             'PTFE, aramid, fabric-reinforced elastomer, metal anti-extrusion rings.', 'Some leakage normal; lubrication often required.', ['Leakage', 'Extrusion'], ['Leakage rate, adjust/replace']),
        'distance_piece': C('Separates the power end from the fluid end so that leakage cannot reach the crankcase oil.', 'Open frame with access windows, wipers on extension rods.',
                            'Cast iron/steel.', 'Ventilated, drained.', ['Contamination of crankcase oil'], ['Wiper seals']),
        'gear_reducer_r': C('Reduces motor speed to the crankshaft speed.', 'Parallel-shaft helical gearbox.', 'Cast iron, alloy steel gears.', 'Oil lubricated.', ['Gear wear', 'Oil leak'], ['Oil level']),
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
