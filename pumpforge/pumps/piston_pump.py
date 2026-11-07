"""
Piston Pump — horizontal duplex double-acting piston pump.  Each piston (with
elastomer cups) slides in a replaceable cylinder liner and pumps on both
strokes: while one end of the liner fills through its suction valve, the other
end discharges through its discharge valve.  Crank-driven power end (90° throws).
Crankshaft along +Y, pistons along X, cut plane through the rear cylinder.
"""
import math
from pumpforge.core import (Model, lathe, lathe_split, ring_profile, cyl, box, csg, split, join, merge_halves, split_many, TAU)
from pumpforge.parts import add_drive_y
from pumpforge.recip import power_end, motion_keys, RECIP_META
from pumpforge.shapes import sweep_tube
from pumpforge.common_meta import C

ID = 'piston_pump'
CZ = 0.42
YS = (0.0, 0.24)
YC = 0.24
XC, R, L = 0.72, 0.05, 0.3
RL = 0.05          # liner bore radius


def build(out_dir):
    m = Model(ID, 'Duplex Double-Acting Piston Pump', 'C · Reciprocating Positive-Displacement Pumps', META)
    cyls, pe = power_end(m, YS, CZ, XC, R, L, [0.0, math.pi / 2], YC, mat='paint_red', revs=1.0, rod_to=0.12, bp=0.0)
    xmin = XC - R - L
    mat = 'paint_grey'
    ya, yb = YS[0] - 0.11, YS[-1] + 0.11
    xl0, xl1 = -0.3, 0.02          # liner
    outs = [box('fe', (0.46, yb - ya, 0.24), (-0.14, (ya + yb) / 2, CZ), mat, bevel=0.015),
            cyl('sm', 0.055, ya - 0.05, yb + 0.05, mat, 48, axis='Y', center=(-0.14, 0, CZ - 0.2)),
            cyl('dm', 0.05, ya - 0.05, yb + 0.05, mat, 48, axis='Y', center=(-0.14, 0, CZ + 0.2)),
            box('sbr', (0.42, 0.1, 0.1), (-0.14, YS[0], CZ - 0.14), mat), box('sbr2', (0.42, 0.1, 0.1), (-0.14, YS[1], CZ - 0.14), mat),
            box('dbr', (0.42, 0.1, 0.1), (-0.14, YS[0], CZ + 0.14), mat), box('dbr2', (0.42, 0.1, 0.1), (-0.14, YS[1], CZ + 0.14), mat)]
    ins = [cyl('smi', 0.045, ya - 0.06, yb + 0.03, mat, 48, axis='Y', center=(-0.14, 0, CZ - 0.2)),
           cyl('dmi', 0.04, ya - 0.03, yb + 0.06, mat, 48, axis='Y', center=(-0.14, 0, CZ + 0.2))]
    for i, y in enumerate(YS):
        ins += [cyl(f'lb{i}', RL + 0.008, xl0 - 0.04, xl1 + 0.03, mat, 48, axis='X', center=(0, y, CZ)),
                cyl(f'rb{i}', 0.022, xl1, 0.12, mat, 32, axis='X', center=(0, y, CZ))]
        for xv in (xl0 - 0.02, xl1 + 0.0):
            ins.append(cyl(f'vb{i}{xv}', 0.03, CZ - 0.2, CZ + 0.2, mat, 40, center=(xv, y, 0)))
    fe = csg('fluid_end', outs, ins, mat)
    p = m.part('fluid_end', 'Fluid End (Cylinder Body, Valve Pots, Manifolds)', 'fluid_end', section='split', explode=(-0.45, 0, 0), info={'ref': 'fluid_end_dp'})
    p.add_split(*split(fe, 'y', YC), smooth_angle=40)
    for i, c in enumerate(cyls):
        y = c['y']
        ln = lathe(f'liner{i}', ring_profile(RL, RL + 0.008, xl0 + 0.01, xl1 - 0.005), 'chrome', 64, axis='X', center=(0, y, CZ))
        p = m.part(f'liner_{i + 1}', f'Cylinder Liner {i + 1}', 'fluid_end', section='split', explode=(-0.6, 0, 0.2 + 0.05 * i), info={'ref': 'liner'})
        p.add_split(*split_many(f'ln{i}', [ln], 'y', YC))
        # valves: front pot (x = xl0-0.02) and rear pot (x = xl1)
        for pot, xv in (('front', xl0 - 0.02), ('rear', xl1)):
            for kind, zs in (('suction', CZ - 0.13), ('discharge', CZ + 0.1)):
                vid = f'{kind}_valve_{pot}_{i + 1}'
                disc = join(vid, [cyl(vid + 'd', 0.024, zs, zs + 0.008, 'steel', 32, center=(xv, y, 0), ch=0.001),
                                  cyl(vid + 's', 0.005, zs + 0.008, zs + 0.03, 'steel', 12, center=(xv, y, 0)),
                                  sweep_tube(vid + 'sp', [(xv + 0.012 * math.cos(TAU * 5 * k / 50), y + 0.012 * math.sin(TAU * 5 * k / 50), zs + 0.009 + 0.02 * k / 50)
                                                          for k in range(51)], 0.0016, 'steel', 8)])
                p = m.part(vid, f'{kind.title()} Valve – {pot} end, cyl. {i + 1}', 'valves', explode=(-0.45, -0.15, -0.3 if kind == 'suction' else 0.3),
                           info={'ref': 'valve_disc_r'})
                vm = p.add(disc, smooth_angle=50)
                # front chamber grows when piston moves +X; rear chamber grows when piston moves -X
                sel = kind if pot == 'front' else ('discharge' if kind == 'suction' else 'suction')
                m.keyframes(vm, 'Operate', 'location', [(f, (0, 0, 0.008 * v)) for f, v in motion_keys(c['lk'], sel)])
        # piston + rod
        xp0 = (c['x0'] - xmin) + xl0 + 0.07
        pist = join(f'piston{i}', [cyl(f'pr{i}', 0.02, xp0, 0.14 + (c['x0'] - xmin), 'chrome', 32, axis='X', center=(0, y, CZ)),
                                    lathe(f'ph{i}', [(0.02, xp0 - 0.03), (RL - 0.004, xp0 - 0.03), (RL - 0.004, xp0 + 0.03), (0.02, xp0 + 0.03)], 'steel', 48, axis='X', center=(0, y, CZ)),
                                    lathe(f'pc1{i}', [(0.03, xp0 - 0.03), (RL - 0.0005, xp0 - 0.026), (RL - 0.0005, xp0 - 0.012), (0.03, xp0 - 0.012)], 'rubber', 48, axis='X', center=(0, y, CZ)),
                                    lathe(f'pc2{i}', [(0.03, xp0 + 0.012), (RL - 0.0005, xp0 + 0.012), (RL - 0.0005, xp0 + 0.026), (0.03, xp0 + 0.03)], 'rubber', 48, axis='X', center=(0, y, CZ))])
        p = m.part(f'piston_{i + 1}', f'Piston (Double Cups) & Piston Rod {i + 1}', 'reciprocating', pivot=(xp0, y, CZ), explode=(-0.2, 0, 0.42 + 0.05 * i),
                   info={'ref': 'piston'})
        pm = p.add(pist, smooth_angle=40)
        m.keyframes(pm, 'Operate', 'location', c['lk'])
        pk = [lathe(f'rpk{i}{k}', ring_profile(0.0205, 0.03, 0.03 + k * 0.012, 0.04 + k * 0.012), 'ptfe', 32, axis='X', center=(0, y, CZ)) for k in range(3)]
        pk.append(lathe(f'rgl{i}', [(0.0205, 0.066), (0.03, 0.066), (0.03, 0.03), (0.045, 0.03), (0.045, 0.08), (0.0205, 0.08)], 'steel', 40, axis='X', center=(0, y, CZ)))
        p = m.part(f'rod_packing_{i + 1}', f'Piston Rod Packing {i + 1}', 'shaft_seal', section='split', explode=(-0.1, 0, -0.32 - 0.05 * i), info={'ref': 'plunger_packing'})
        p.add_split(*split_many(f'rpk{i}', pk, 'y', YC))
    add_drive_y(m, pe['y1'] + 0.42, CZ, 0.0, 0.03, motor_R=0.16, motor_L=0.5, revs=1, x_off=XC, base=False)
    gb = csg('reducer', [box('gb', (0.28, 0.2, 0.32), (XC, pe['y1'] + 0.24, CZ - 0.02), 'paint_grey', bevel=0.02)],
             [box('gbi', (0.24, 0.16, 0.28), (XC, pe['y1'] + 0.24, CZ - 0.02), 'paint_grey', bevel=0.015)], 'paint_grey')
    p = m.part('gear_reducer', 'Gear Reducer', 'power_transmission', section='split', explode=(0.4, 0.3, 0), info={'ref': 'gear_reducer_r'})
    p.add_split(*split(gb, 'y', pe['y1'] + 0.24), smooth_angle=40)
    y = YC
    m.flow('flow_in', [(-0.14, ya - 0.3, CZ - 0.2), (-0.14, y, CZ - 0.2), (xl0 - 0.02, y, CZ - 0.16), (xl0 - 0.02, y, CZ - 0.02), (xl0 + 0.03, y, CZ)],
           'flow_suction', 0.006, 0.08)
    m.flow('flow_out', [(xl1 - 0.02, y, CZ), (xl1, y, CZ + 0.03), (xl1, y, CZ + 0.16), (-0.14, y, CZ + 0.2), (-0.14, yb + 0.3, CZ + 0.2)], 'flow_discharge', 0.006, 0.08)
    return m.export(out_dir)


META = {
    'summary': ('A piston pump moves liquid with a piston that slides in a cylinder liner, sealed against the bore by elastomer '
                'cups on the piston itself. In the double-acting design shown, both faces of the piston work: as it travels one '
                'way, the chamber ahead of it discharges while the chamber behind it fills, and the roles reverse on the return '
                'stroke. Two cylinders cranked 90° apart (duplex) give four deliveries per revolution. Used for drilling mud, '
                'slurries and general high-pressure transfer at moderate pressures.'),
    'classification': {'family': 'Positive displacement – reciprocating', 'configuration': 'Horizontal, duplex, double-acting piston, crank-driven'},
    'model_configuration': {'cylinders': 2, 'stroke_mm': 2 * R * 1000, 'liner_bore_mm': 2 * RL * 1000, 'crank_phasing': '90°',
                            'flow_formula': 'Q ≈ n_cyl × [2·(π/4)D² − (π/4)d_rod²] × stroke × N × ηv (double-acting)'},
    'standards': [
        {'id': 'API 674', 'title': 'Positive Displacement Pumps – Reciprocating', 'relevance': 'Reciprocating pumps in process service.', 'edition': 'to be verified'},
        {'id': 'ANSI/HI 6.1-6.5', 'title': 'Reciprocating Power Pumps', 'relevance': 'Nomenclature, application and operation.', 'edition': 'to be verified'},
        {'id': 'API 7K', 'title': 'Drilling and Well Servicing Equipment', 'relevance': 'Applies to drilling mud pumps; confirm applicability.', 'edition': 'to be verified'},
    ],
    'references': ['Karassik et al., Pump Handbook — reciprocating pumps.', 'Hydraulic Institute ANSI/HI 6.1-6.5 (scope summary).'],
    'components': {**RECIP_META,
        'fluid_end_dp': C('Houses the cylinder liners and four valve pots per cylinder (suction and discharge at each end).', 'Cast or forged body with valve covers and manifolds.',
                          'Cast steel, ductile iron, forged steel.', 'Cyclic pressure on both chambers.', ['Valve pot washout', 'Fatigue cracks'], ['Valve seats, NDT']),
        'liner': C('Replaceable wear surface in which the piston slides.', 'Hardened/chrome or ceramic-lined sleeve clamped in the fluid end.', 'Hardened steel, chrome-plated, ceramic.',
                   'Wear from abrasive fluids determines life.', ['Bore wear, scoring'], ['Bore measurement']),
        'piston': C('Displaces liquid on both strokes; cups seal against the liner.', 'Steel hub with replaceable elastomer/fabric cups, on a piston rod.', 'Steel hub, NBR/HNBR/urethane cups.',
                    'Liner spray/flush often used to cool and lubricate the back of the piston (single-acting mud pumps).', ['Cup wear', 'Rod scoring'], ['Leakage past piston, rod condition']),
        'valve_disc_r': C('Automatic check valves for each chamber.', 'Spring-loaded disc or poppet with seat.', 'Hardened steel, urethane inserts.', 'Open by pressure difference.', ['Seat washout', 'Spring failure'], ['Volumetric efficiency']),
        'plunger_packing': C('Seals the piston rod where it leaves the fluid end.', 'Packing rings in stuffing box with gland.', 'PTFE/fabric-reinforced elastomer.', 'Small controlled leakage.', ['Wear'], ['Adjust/replace']),
        'gear_reducer_r': C('Reduces motor speed to crankshaft speed.', 'Helical gearbox.', 'Cast iron, alloy gears.', 'Oil lubricated.', ['Gear wear'], ['Oil level']),
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
