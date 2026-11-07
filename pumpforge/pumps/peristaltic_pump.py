"""
Peristaltic (Hose) Pump — a reinforced hose lies in a U-loop around the inside of
a lubricant-filled housing; two rotor shoes squeeze it shut and roll the
occlusion along, pushing the liquid ahead and drawing more in behind as the hose
recovers.  Only the hose is wetted.  Axis Y (window cover at -Y), cut x = 0.
"""
import math
from pumpforge.core import (Model, lathe, lathe_split, ring_profile, cyl, box, csg, split_keep, join, merge_halves, split_many, rotate, TAU)
from pumpforge.parts import add_drive_y, nozzle_bolts, pipe
from pumpforge.shapes import sweep_tube
from pumpforge.common_meta import C

ID = 'peristaltic_pump'
CZ = 0.42
BP = 0.09
RH = 0.19        # hose centreline radius
RHO = 0.03       # hose outer radius
W = 0.11         # housing depth
YH = W / 2


def ks(o):
    return split_keep(o, 'x', 0.0, keep_positive=False)


def build(out_dir):
    m = Model(ID, 'Peristaltic Hose Pump', 'B · Rotary Positive-Displacement Pumps', META)
    mat = 'paint_yellow'
    Rc = RH + RHO + 0.03
    hs = csg('housing', [cyl('ho', Rc + 0.012, 0.0, W + 0.02, mat, 128, axis='Y', center=(0, 0, CZ), ch=0.006),
                         box('ft', (0.42, W + 0.04, CZ - Rc - BP + 0.05), (0, W / 2, BP + (CZ - Rc - BP + 0.05) / 2 + 0.006), mat, bevel=0.006)],
             [cyl('hi', Rc, -0.01, W + 0.005, mat, 128, axis='Y', center=(0, 0, CZ)),
              cyl('pl', RHO + 0.004, CZ - Rc - 0.06, CZ - 0.05, mat, 32, center=(-RH * math.cos(math.radians(70)), YH, 0)),
              cyl('pr', RHO + 0.004, CZ - Rc - 0.06, CZ - 0.05, mat, 32, center=(RH * math.cos(math.radians(70)), YH, 0)),
              cyl('sh', 0.03, W, W + 0.03, mat, 32, axis='Y', center=(0, 0, CZ))], mat)
    p = m.part('pump_housing', 'Pump Housing (Lubricant-Filled)', 'casing', section='split', explode=(0, 0.15, 0), info={'ref': 'peri_housing'})
    p.add_split(*ks(hs), smooth_angle=40)
    win = csg('window', [cyl('w', Rc + 0.012, -0.02, 0.0, 'aluminium', 128, axis='Y', center=(0, 0, CZ), ch=0.004)],
              [cyl('wg', Rc - 0.04, -0.03, -0.012, 'aluminium', 96, axis='Y', center=(0, 0, CZ))], 'aluminium')
    glass = cyl('glass', Rc - 0.04, -0.016, -0.012, 'ptfe', 96, axis='Y', center=(0, 0, CZ))
    bolts = [cyl(f'wb{i}', 0.008, -0.03, -0.02, 'steel_dark', 16, axis='Y', center=((Rc - 0.012) * math.cos(TAU * (i + 0.5) / 10), 0,
                                                                                    CZ + (Rc - 0.012) * math.sin(TAU * (i + 0.5) / 10))) for i in range(10)]
    p = m.part('front_cover', 'Front Cover with Inspection Window', 'casing', section='hide', explode=(0, -0.45, 0), info={'ref': 'peri_cover'})
    p.add(join('front_cover', [win, glass] + bolts), smooth_angle=40)
    # hose: U-loop + legs to ports
    a0, a1 = math.radians(-70), math.radians(250)
    arc = [(RH * math.cos(a0 + (a1 - a0) * i / 80), YH, CZ + RH * math.sin(a0 + (a1 - a0) * i / 80)) for i in range(81)]
    xr, xl = arc[0][0], arc[-1][0]
    path = [(xr, YH, CZ - Rc - 0.12), (xr, YH, arc[0][2] - 0.02)] + arc + [(xl, YH, arc[-1][2] - 0.02), (xl, YH, CZ - Rc - 0.12)]
    hose = sweep_tube('hose', path, RHO, 'rubber', 24)
    p = m.part('hose', 'Reinforced Pump Hose', 'pumping_element', explode=(0, -0.3, 0.25), info={'ref': 'peri_hose'})
    p.add(hose, smooth_angle=70)
    ports = []
    for x in (xr, xl):
        ports += [cyl('pt', RHO + 0.012, CZ - Rc - 0.2, CZ - Rc - 0.06, 'stainless', 32, center=(x, YH, 0)),
                  cyl('ptf', 0.07, CZ - Rc - 0.2, CZ - Rc - 0.185, 'stainless', 32, center=(x, YH, 0), ch=0.003)]
    pb, pf = split_many('ports', ports, 'x', 0.0)
    p = m.part('port_flanges', 'Inlet & Outlet Port Flanges (Hose Clamps)', 'casing', section='split', explode=(0, 0, -0.3), info={'ref': 'peri_ports'})
    p.add_split(pf, pb, smooth_angle=40)
    # rotor with two shoes
    rt = RH - RHO * 0.3     # shoe tip radius -> squeezes hose
    rot = [cyl('hub', 0.06, 0.012, W - 0.012, 'cast_iron', 64, axis='Y', center=(0, 0, CZ)),
           cyl('rsh', 0.03, 0.01, W + 0.42, 'steel', 32, axis='Y', center=(0, 0, CZ), ch=0.002)]
    for s in (1, -1):
        rot.append(box(f'arm{s}', (0.05, W - 0.03, rt - 0.09), (0, YH, CZ + s * (rt - 0.09) / 2 + s * 0.04), 'cast_iron', bevel=0.006))
        shoe = lathe(f'shoe{s}', [(rt - 0.03, 0.015), (rt - 0.004, 0.015), (rt, 0.03), (rt, W - 0.03), (rt - 0.004, W - 0.015), (rt - 0.03, W - 0.015)],
                     'steel', 32, a0=s * math.pi / 2 - 0.42, a1=s * math.pi / 2 + 0.42, axis='Y', center=(0, 0, CZ), cap_mat='steel')
        rot.append(shoe)
    p = m.part('rotor', 'Rotor with Pressing Shoes', 'rotating_element', pivot=(0, 0, CZ), explode=(0, -0.6, 0), info={'ref': 'peri_rotor'})
    p.add(join('rotor', rot), smooth_angle=40); p.spin('Y', 0.5)
    # bearing bracket + gear motor
    y0, y1 = W + 0.02, W + 0.3
    bh = csg('bh', [lathe('bh', [(0.0, y0), (0.12, y0), (0.12, y0 + 0.02), (0.065, y0 + 0.05), (0.065, y1), (0, y1)], mat, 96, axis='Y', center=(0, 0, CZ)),
                    box('bhf', (0.18, 0.14, CZ - BP - 0.06), (0, y1 - 0.09, BP + (CZ - BP - 0.06) / 2 + 0.006), mat, bevel=0.005)],
             [cyl('bhi', 0.05, y0 + 0.05, y1 - 0.02, mat, 48, axis='Y', center=(0, 0, CZ)), cyl('bhs', 0.032, y0 - 0.01, y1 + 0.01, mat, 32, axis='Y', center=(0, 0, CZ))], mat)
    p = m.part('bearing_bracket', 'Bearing Bracket', 'bearing_housing', section='split', explode=(0, 0.3, 0), info={'ref': 'bearing_frame'})
    p.add_split(*ks(bh), smooth_angle=40)
    gb = csg('gearbox', [box('gb', (0.26, 0.24, 0.3), (0, y1 + 0.32, CZ - 0.02), 'paint_grey', bevel=0.02),
                         box('gbf', (0.3, 0.2, CZ - 0.17 - BP), (0, y1 + 0.32, BP + (CZ - 0.17 - BP) / 2 + 0.006), 'paint_grey', bevel=0.005)],
             [box('gbi', (0.22, 0.2, 0.26), (0, y1 + 0.32, CZ - 0.02), 'paint_grey', bevel=0.015)], 'paint_grey')
    p = m.part('gear_reducer', 'Gear Reducer', 'power_transmission', section='split', explode=(0, 0.45, 0), info={'ref': 'gear_reducer'})
    p.add_split(*ks(gb), smooth_angle=40)
    add_drive_y(m, y1 + 0.46, CZ, BP, 0.024, motor_R=0.11, motor_L=0.34, y_base0=-0.12, base_w=0.5, revs=4, coupling_len=0.07)
    for prt in m.parts:
        if prt.id == 'coupling':
            prt.node.location.z = CZ
    m.flow('flow_in', [(xl, YH - 0.0, CZ - Rc - 0.5), (xl, YH, CZ - 0.05)] + list(reversed(arc))[0:30], 'flow_suction', 0.006, 0.08)
    m.flow('flow_out', list(reversed(arc))[29:] + [(xr, YH, CZ - 0.05), (xr, YH, CZ - Rc - 0.5)], 'flow_discharge', 0.006, 0.08)
    return m.export(out_dir)


META = {
    'summary': ('The liquid is enclosed in a flexible hose laid around the inside of the pump housing. Rotating shoes (or rollers) '
                'squeeze the hose completely shut and roll the closed point along, pushing the liquid ahead of them; behind the '
                'shoe the hose springs back open and draws in more liquid. Only the hose touches the product, there are no '
                'seals or valves, and the pump can run dry, self-prime and handle abrasive, viscous and shear-sensitive fluids.'),
    'classification': {'family': 'Positive displacement – rotary (peristaltic)', 'configuration': 'Hose pump with two pressing shoes, lubricant-filled housing'},
    'model_configuration': {'hose': 'Reinforced elastomer hose (NR, NBR, EPDM, CSM)', 'rotor': '2 shoes; roller versions are used on tube pumps',
                            'note': 'Hose compression is shown schematically; the real hose is fully occluded under each shoe.'},
    'standards': [
        {'id': 'ANSI/HI 3.1-3.5', 'title': 'Rotary Pumps', 'relevance': 'Includes peristaltic pump nomenclature and application.', 'edition': 'to be verified'},
    ],
    'references': ['Manufacturer hose pump manuals (generic practice).', 'Karassik et al., Pump Handbook — peristaltic pumps.'],
    'components': {
        'peri_housing': C('Holds the hose loop against the rotor and contains lubricant that cools and lubricates the hose/shoe contact.', 'Cast housing with port openings and drain.',
                          'Cast iron/aluminium.', 'Lubricant level must be maintained; hose failure detection often fitted.', ['Lubricant contamination after hose burst'], ['Lubricant level']),
        'peri_cover': C('Closes the housing; window allows inspection of hose and lubricant.', 'Bolted cover with window.', 'Aluminium, polycarbonate window.', 'Static.', ['Seal leak'], ['Visual']),
        'peri_hose': C('The only wetted part; its elastic recovery creates the suction.', 'Multi-layer hose with textile reinforcement, precision-machined OD for correct compression.',
                       'Natural rubber, NBR, EPDM, CSM.', 'Life depends on speed and pressure; replace on schedule.', ['Fatigue rupture', 'Chemical attack'], ['Count cycles/hours, leak detector']),
        'peri_ports': C('Connect and clamp the hose ends to the piping.', 'Flanged port inserts with hose clamps.', 'Stainless steel, PP.', 'Seal the hose ends.', ['Leakage'], ['Clamp tightness']),
        'peri_rotor': C('Carries the shoes that occlude the hose.', 'Cast rotor with replaceable/shimmable shoes to adjust compression.', 'Cast iron, steel.', 'Low speed (typically below ~100 rpm on large hose pumps).',
                        ['Shoe wear'], ['Shim setting for correct compression']),
        'gear_reducer': C('Reduces motor speed to the low rotor speed and increases torque.', 'Helical/bevel gear unit.', 'Cast iron, alloy steel gears.', 'Oil-lubricated.', ['Oil leakage', 'Gear wear'], ['Oil level']),
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
