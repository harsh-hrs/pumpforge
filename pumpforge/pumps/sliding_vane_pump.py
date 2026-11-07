"""
Sliding Vane Pump — slotted rotor turning eccentrically in a cam (liner) bore;
vanes slide out under centrifugal force (and push rods) to follow the liner,
forming chambers that grow on the inlet side and shrink on the outlet side.
Self-compensating for vane wear; good for thin liquids (LPG, solvents, fuels).
Shaft along +Y (front head at -Y), cut plane x = 0.
"""
import math
from pumpforge.core import (Model, lathe, lathe_split, ring_profile, cyl, box, csg, split_keep, join, merge_halves, split_faces,
                            rotate, TAU, OPERATE_FRAMES)
from pumpforge.parts import add_drive_y, nozzle_bolts, seal_cartridge
from pumpforge.common_meta import C

ID = 'sliding_vane_pump'
CZ = 0.28
BP = 0.09
RB = 0.075        # liner bore radius
E = 0.011         # eccentricity
RR = RB - E       # rotor radius
W = 0.08
NV = 6
RS = 0.022
TV = 0.007        # vane thickness
LV = 0.042        # vane radial length


def ks(o):
    return split_keep(o, 'x', 0.0, keep_positive=False)


def t_reach(phi):
    s = math.sin(phi)
    return E * s + math.sqrt(RB * RB - E * E * math.cos(phi) ** 2)


def build(out_dir):
    m = Model(ID, 'Sliding Vane Pump (Eccentric Rotor, Cam Liner)', 'B · Rotary Positive-Displacement Pumps', META)
    mat = 'paint_blue'
    Rc = RB + 0.035
    outs = [cyl('cb', Rc, -0.0, W + 0.06, mat, 96, axis='Y', center=(0, 0, CZ), ch=0.004),
            cyl('pin', 0.045, -0.26, 0.0, mat, 48, axis='X', center=(0, W / 2, CZ - 0.01)),
            cyl('pout', 0.045, 0.0, 0.26, mat, 48, axis='X', center=(0, W / 2, CZ - 0.01)),
            cyl('fi', 0.085, -0.26, -0.24, mat, 48, axis='X', center=(0, W / 2, CZ - 0.01), ch=0.003),
            cyl('fo', 0.085, 0.24, 0.26, mat, 48, axis='X', center=(0, W / 2, CZ - 0.01), ch=0.003),
            box('foot', (0.32, 0.12, CZ - Rc - BP), (0, W / 2, BP + (CZ - Rc - BP) / 2 + 0.006), mat, bevel=0.005)]
    ins = [cyl('lb', RB + 0.012, -0.01, W, mat, 96, axis='Y', center=(0, 0, CZ)),
           cyl('pib', 0.035, -0.27, -RB, mat, 48, axis='X', center=(0, W / 2, CZ - 0.01)),
           cyl('pob', 0.035, RB, 0.27, mat, 48, axis='X', center=(0, W / 2, CZ - 0.01)),
           cyl('sb', 0.04, W, W + 0.07, mat, 48, axis='Y', center=(0, 0, CZ - E))]
    cas = csg('casing', outs, ins, mat)
    bolts = [nozzle_bolts(f'pf{s}', 4, 0.12, 0.022, s * 0.24, s * 0.225, 'X', (0, W / 2, CZ - 0.01), math.pi / 4) for s in (1, -1)]
    cb, cf = ks(cas)
    bb, bf = split_faces(join('pfb', bolts), 'x', 0.0, keep_positive=False)
    p = m.part('casing', 'Casing', 'casing', section='split', explode=(0, 0.12, 0), info={'ref': 'pd_casing'})
    p.add_split(join('cb_', [cb, bb]), join('cf_', [cf, bf]), smooth_angle=40)
    # cam liner with inlet/outlet port slots
    ln = csg('liner', [cyl('lo', RB + 0.012, 0.0, W, 'cast_iron', 96, axis='Y', center=(0, 0, CZ))],
             [cyl('li', RB, -0.01, W + 0.01, 'cast_iron', 96, axis='Y', center=(0, 0, CZ)),
              box('ps1', (0.04, W * 0.7, 0.07), (-RB, W / 2, CZ - 0.01), 'cast_iron'), box('ps2', (0.04, W * 0.7, 0.07), (RB, W / 2, CZ - 0.01), 'cast_iron')],
             'cast_iron')
    p = m.part('liner', 'Cam Liner (with Port Openings)', 'casing', section='split', explode=(0, -0.18, 0.0), info={'ref': 'vane_liner'})
    p.add_split(*ks(ln), smooth_angle=40)
    # front head (hidden in cutaway)
    hd = cyl('head', Rc, -0.04, 0.0, mat, 96, axis='Y', center=(0, 0, CZ), ch=0.004)
    hb = [cyl(f'hb{i}', 0.008, -0.05, -0.04, 'steel_dark', 20, axis='Y',
              center=((Rc - 0.016) * math.cos(TAU * (i + 0.5) / 8), 0, CZ + (Rc - 0.016) * math.sin(TAU * (i + 0.5) / 8))) for i in range(8)]
    p = m.part('front_head', 'Front Head', 'casing', section='hide', explode=(0, -0.5, 0), info={'ref': 'vane_head'})
    p.add(join('front_head', [hd] + hb), smooth_angle=40)
    # rotor with slots + shaft
    cz_r = CZ - E
    slots = []
    for i in range(NV):
        a = TAU * i / NV
        s = box(f'sl{i}', (LV + 0.004, W + 0.02, TV + 0.0008), (RR - LV / 2 + 0.002, W / 2, 0), 'steel')
        s = rotate(s, -a, 'Y')
        s.data.transform(__import__('mathutils').Matrix.Translation((0, 0, cz_r)))
        slots.append(s)
    rot = csg('rotor', [cyl('r', RR - 0.0004, 0.0005, W - 0.0005, 'steel', 96, axis='Y', center=(0, 0, cz_r)),
                        cyl('rsh', RS, -0.02, W + 0.4, 'steel', 32, axis='Y', center=(0, 0, cz_r), ch=0.002)], slots, 'steel')
    p = m.part('rotor', 'Slotted Rotor & Shaft', 'rotating_element', pivot=(0, 0, cz_r), explode=(0, -0.3, 0), info={'ref': 'vane_rotor'})
    p.add(rot, smooth_angle=30); p.spin('Y', 1)
    # vanes: rotate with rotor + slide radially to follow the liner
    for i in range(NV):
        a = TAU * i / NV
        v = box(f'vane{i}', (LV, W - 0.002, TV), (RR - LV / 2 - 0.0005, W / 2, 0), 'carbon')
        v = rotate(v, -a, 'Y')
        v.data.transform(__import__('mathutils').Matrix.Translation((0, 0, cz_r)))
        p = m.part(f'vane_{i + 1}', f'Vane {i + 1}', 'rotating_element', pivot=(0, 0, cz_r), explode=(0, -0.3, 0.25 + 0.04 * i),
                   info={'ref': 'vane'})
        mesh = p.add(v, smooth_angle=30)
        rk, lk = [], []
        for f in range(OPERATE_FRAMES + 1):
            th = TAU * f / OPERATE_FRAMES
            phi = a - th
            d = max(0.0, t_reach(phi) - (RR - 0.0005))
            rk.append((1 + f, (0.0, th, 0.0)))
            lk.append((1 + f, (d * math.cos(phi), 0.0, d * math.sin(phi))))
        m.keyframes(mesh, 'Operate', 'rotation_euler', rk)
        m.keyframes(mesh, 'Operate', 'location', lk)
        # rest pose: extended for its angle
        d0 = max(0.0, t_reach(a) - (RR - 0.0005))
        mesh.data.transform(__import__('mathutils').Matrix.Translation((d0 * math.cos(a), 0, d0 * math.sin(a))))
        rel = []
        for f in range(OPERATE_FRAMES + 1):
            phi = a - TAU * f / OPERATE_FRAMES
            dd = max(0.0, t_reach(phi) - (RR - 0.0005)) - d0
            rel.append((1 + f, (dd * math.cos(phi), 0.0, dd * math.sin(phi))))
        m.keyframes(mesh, 'Operate', 'location', rel)
        m._anims[(mesh, 'Operate')] = [c for c in m._anims[(mesh, 'Operate')] if not (c[0] == 'location' and c[1] is lk)]
    # rear head, seal, bearing housing
    y0, y1 = W + 0.06, W + 0.3
    bh = csg('bearing_housing', [lathe('bh', [(0.0, y0), (Rc, y0), (Rc, y0 + 0.015), (0.06, y0 + 0.04), (0.06, y1), (0, y1)], mat, 96, axis='Y',
                                           center=(0, 0, cz_r)),
                                 box('bhf', (0.16, 0.12, cz_r - BP - 0.05), (0, y1 - 0.08, BP + (cz_r - BP - 0.05) / 2 + 0.006), mat, bevel=0.004)],
             [cyl('bhi', 0.048, y0 + 0.04, y1 - 0.02, mat, 48, axis='Y', center=(0, 0, cz_r)), cyl('bhs', RS + 0.002, y0 - 0.01, y1 + 0.01, mat, 32, axis='Y', center=(0, 0, cz_r)),
              box('bhw', (0.2, 0.08, 0.07), (0, y0 + 0.06, cz_r), mat, bevel=0.01)], mat)
    p = m.part('bearing_housing', 'Rear Head & Bearing Housing', 'bearing_housing', section='split', explode=(0, 0.35, 0), info={'ref': 'bearing_frame'})
    p.add_split(*ks(bh), smooth_angle=40)
    sb, sf = seal_cartridge('seal', W + 0.005, W + 0.06, RS, 0.038, axis='Y', center=(0, 0, cz_r))
    p = m.part('mechanical_seal', 'Mechanical Seal', 'mechanical_seal', section='split', explode=(-0.3, 0.2, 0.1), info={'ref': 'mechanical_seal'})
    p.add_split(sb, sf)
    add_drive_y(m, W + 0.4, cz_r, BP, RS, motor_R=0.12, motor_L=0.4, y_base0=-0.2, base_w=0.6, revs=1)

    yf = -0.004
    arc = []
    for k in range(25):
        phi = math.radians(-100 - 340 * k / 24)
        r = (RB + RR) / 2 + 0.004
        arc.append((r * math.cos(phi), yf, CZ + r * math.sin(phi) * 1.0))
    m.flow('flow_in', [(-0.5, yf, CZ - 0.01), (-0.1, yf, CZ - 0.01)] + arc[3:13], 'flow_suction', 0.004, 0.06)
    m.flow('flow_out', arc[12:22] + [(0.1, yf, CZ - 0.01), (0.5, yf, CZ - 0.01)], 'flow_discharge', 0.004, 0.06)
    return m.export(out_dir)


META = {
    'summary': ('A slotted rotor turns off-centre inside a cylindrical liner (cam). Flat vanes slide in and out of the rotor '
                'slots, pressed against the liner by centrifugal force (and often push rods or springs), so they form sealed '
                'chambers between rotor and liner. On the inlet side the chambers grow and fill; on the outlet side they '
                'shrink and push the liquid out. Vanes wear-compensate by sliding further out, keeping performance up on '
                'thin liquids such as LPG, fuels, solvents and refrigerants.'),
    'classification': {'family': 'Positive displacement – rotary', 'configuration': 'Sliding vane, eccentric rotor, single chamber (unbalanced)'},
    'model_configuration': {'vanes': NV, 'eccentricity_mm': E * 1000, 'vane_material': 'Carbon-graphite/composite (typical); metal for high viscosity',
                            'note': 'Balanced (double-cam) designs exist for hydraulic service.'},
    'standards': [
        {'id': 'API 676', 'title': 'Positive Displacement Pumps – Rotary', 'relevance': 'Process service.', 'edition': 'to be verified'},
        {'id': 'ANSI/HI 3.1-3.5', 'title': 'Rotary Pumps', 'relevance': 'Nomenclature and application.', 'edition': 'to be verified'},
        {'id': 'UL 51 / NFPA 58', 'title': 'LPG equipment / LP-Gas Code', 'relevance': 'Apply to LPG transfer installations using vane pumps; confirm listing per pump.', 'edition': 'to be verified'},
    ],
    'references': ['Karassik et al., Pump Handbook — sliding vane pumps.', 'Manufacturer vane pump technical literature (generic practice).'],
    'components': {
        'vane_liner': C('Cam-shaped (here circular, offset) bore that the vanes follow; replaceable wear part with port openings.', 'Hardened cast liner pressed or pinned into the casing.',
                        'Cast iron, Ni-Resist, hardened steel.', 'Wear raises slip.', ['Scoring from dirt', 'Wear'], ['Bore measurement']),
        'vane_head': C('Closes the pump chamber; disc faces set rotor end clearance.', 'Machined head with replaceable disc (side plate).', 'Cast iron, ductile iron.',
                       'End clearance is a main slip path.', ['Disc wear'], ['End clearance']),
        'vane_rotor': C('Carries and drives the vanes.', 'Slotted rotor integral with or keyed to the shaft.', 'Ductile iron, steel.', 'Turns eccentrically in the liner.', ['Slot wear'], ['Slot width']),
        'vane': C('Seal against the liner to form the pumping chambers.', 'Flat blades free to slide in the slots.', 'Carbon-graphite, composite polymers, bronze, steel.',
                  'Self-adjust for wear by sliding further out.', ['Breakage from dry running or debris', 'Wear'], ['Vane height measurement']),
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
