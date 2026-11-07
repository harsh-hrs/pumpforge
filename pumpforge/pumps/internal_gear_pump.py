"""
Internal Gear Pump — rotor (internal gear, integral with the drive shaft) drives an
idler (external gear) that turns on a stationary pin in the head; a crescent cast
on the head seals between them.  Flow: liquid enters as teeth come out of mesh,
is carried in rotor and idler tooth spaces on both sides of the crescent, and is
forced out where the teeth re-mesh.  Shaft along +Y (head at -Y), cut plane x = 0.
"""
import math
from pumpforge.core import (Model, lathe, lathe_split, ring_profile, cyl, box, csg, split_keep, join, merge_halves, split_faces,
                            extrude_poly, split_many, TAU)
from pumpforge.parts import add_drive_y, ball_bearing, seal_cartridge, nozzle_bolts
from pumpforge.shapes import involute_gear_profile
from pumpforge.common_meta import C

ID = 'internal_gear_pump'
CZ = 0.28
BP = 0.09
MOD = 0.008
ZR, ZI = 12, 8
W = 0.07          # gear width (y from 0 to W)


def ksplit(o):
    return split_keep(o, 'x', 0.0, keep_positive=False)


def build(out_dir):
    m = Model(ID, 'Internal Gear Pump (Rotor–Idler–Crescent)', 'B · Rotary Positive-Displacement Pumps', META)
    rpr = MOD * ZR / 2
    rpi = MOD * ZI / 2
    e = rpr - rpi
    R_out = rpr + 1.25 * MOD + 0.012     # rotor rim outer radius
    rs = 0.022
    # ---------------- casing (body) -----------------------------------------
    mat = 'paint_red'
    Rc = R_out + 0.02
    outs = [cyl('cb', Rc + 0.015, -0.005, W + 0.11, mat, 96, axis='Y', center=(0, 0, CZ), ch=0.004),
            cyl('pin_', 0.045, -0.24, 0.0, mat, 64, axis='X', center=(0, W / 2, CZ)),
            cyl('pout', 0.045, 0.0, 0.24, mat, 64, axis='X', center=(0, W / 2, CZ)),
            cyl('fin', 0.085, -0.24, -0.22, mat, 64, axis='X', center=(0, W / 2, CZ), ch=0.003),
            cyl('fout', 0.085, 0.22, 0.24, mat, 64, axis='X', center=(0, W / 2, CZ), ch=0.003),
            box('foot', (0.3, 0.12, CZ - Rc - BP), (0, W / 2, BP + (CZ - Rc - BP) / 2 + 0.006), mat, bevel=0.005)]
    ins = [cyl('rb', R_out + 0.0015, -0.01, W + 0.003, mat, 96, axis='Y', center=(0, 0, CZ)),
           cyl('pinb', 0.035, -0.25, -R_out + 0.01, mat, 48, axis='X', center=(0, W / 2, CZ)),
           cyl('poutb', 0.035, R_out - 0.01, 0.25, mat, 48, axis='X', center=(0, W / 2, CZ)),
           cyl('shb', rs + 0.002, W, W + 0.13, mat, 48, axis='Y', center=(0, 0, CZ)),
           cyl('sealc', 0.04, W + 0.02, W + 0.12, mat, 48, axis='Y', center=(0, 0, CZ))]
    cas = csg('casing', outs, ins, mat)
    cb, cf = ksplit(cas)
    bolts = [nozzle_bolts(f'pf{s}', 4, 0.12, 0.022, s * 0.22, s * 0.205, 'X', (0, W / 2, CZ), math.pi / 4) for s in (1, -1)]
    bb, bf = split_faces(join('pfb', bolts), 'x', 0.0, keep_positive=False)
    p = m.part('casing', 'Casing (Pump Body)', 'casing', section='split', explode=(0, 0.15, 0), info={'ref': 'pd_casing'})
    p.add_split(join('cb_', [cb, bb]), join('cf_', [cf, bf]), smooth_angle=40)
    # ---------------- rotor (internal gear + shaft) -------------------------
    cut_pts, _ = involute_gear_profile(MOD, ZR, 20.0, steps=7)
    rim = lathe('rim', [(0, -0.0), (R_out, 0.0), (R_out, W), (0, W)], 'ductile_iron', 96, axis='Y', center=(0, 0, CZ))
    # rotor disc is closed at the back (y = W - 0.012) — cut the tooth spaces from the front only
    cutter = extrude_poly('rcut', [(x, z + CZ) for x, z in cut_pts], -0.01, W - 0.014, 'steel', plane='XZ')
    rotor = csg('rotor', [rim, cyl('rshaft', rs, W - 0.02, W + 0.42, 'steel', 40, axis='Y', center=(0, 0, CZ), ch=0.002)], [cutter], 'ductile_iron')
    p = m.part('rotor', 'Rotor (Internal Gear) & Shaft', 'rotating_element', pivot=(0, 0, CZ), explode=(0, -0.22, 0), info={'ref': 'ig_rotor'})
    p.add(rotor, smooth_angle=30); p.spin('Y', 1)
    # ---------------- idler -------------------------------------------------
    ipts, _ = involute_gear_profile(MOD, ZI, 20.0, steps=7, backlash=0.0006)
    ph = math.radians(270 - 270 // (360 / ZI) * (360 / ZI))
    ipts = [(x * math.cos(ph) - z * math.sin(ph), z * math.cos(ph) + x * math.sin(ph)) for x, z in ipts]
    idl = extrude_poly('idler', [(x, z + CZ - e) for x, z in ipts], 0.001, W - 0.0145, 'stainless', plane='XZ')
    idl = csg('idler', [idl], [cyl('ib', 0.016, -0.01, W, 'steel', 32, axis='Y', center=(0, 0, CZ - e))], 'stainless')
    bush = lathe('ibush', ring_profile(0.012, 0.016, 0.001, W - 0.0145), 'carbon', 32, axis='Y', center=(0, 0, CZ - e))
    p = m.part('idler', 'Idler Gear & Bushing', 'rotating_element', pivot=(0, 0, CZ - e), explode=(0, -0.32, -0.12), info={'ref': 'ig_idler'})
    p.add(join('idler', [idl, bush])); p.spin('Y', ZR / ZI)
    # ---------------- head with crescent + idler pin -----------------------
    head = csg('head', [cyl('hd', Rc + 0.015, -0.045, -0.005, mat, 96, axis='Y', center=(0, 0, CZ), ch=0.004)], [], mat)
    hb_ = [cyl(f'hb{i}', 0.008, -0.055, -0.045, 'steel_dark', 20, axis='Y',
               center=(0.9 * (Rc + 0.0) * math.cos(TAU * (i + 0.5) / 8), 0, CZ + 0.9 * Rc * math.sin(TAU * (i + 0.5) / 8))) for i in range(8)]
    p = m.part('head', 'Head (Front Cover)', 'casing', section='hide', explode=(0, -0.55, 0), info={'ref': 'ig_head'})
    p.add(join('head', [head] + hb_), smooth_angle=40)
    R1 = rpr - 1.25 * MOD - 0.0008
    Ri = rpi + MOD + 0.0008
    outer, inner = [], []
    for i in range(41):
        ph_ = math.radians(28 + 124 * i / 40)
        outer.append((R1 * math.cos(ph_), R1 * math.sin(ph_)))
        sn = math.sin(ph_)
        t = -e * sn + math.sqrt(max(0.0, e * e * sn * sn - e * e + Ri * Ri))
        inner.append((t * math.cos(ph_), t * math.sin(ph_)))
    cres_pts = [(x, z + CZ) for x, z in outer + list(reversed(inner))]
    cres = extrude_poly('crescent', cres_pts, -0.005, W - 0.0145, 'paint_red', plane='XZ')
    pin = cyl('pin', 0.012, -0.005, W - 0.012, 'stainless', 32, axis='Y', center=(0, 0, CZ - e))
    p = m.part('crescent_pin', 'Crescent & Idler Pin (on Head)', 'casing', explode=(0, -0.44, 0), info={'ref': 'ig_crescent'})
    p.add(join('crescent_pin', [cres, pin]), smooth_angle=30)
    # ---------------- seal, bracket, bearings -------------------------------
    sb, sf = seal_cartridge('seal', W + 0.03, W + 0.11, rs, 0.038, axis='Y', center=(0, 0, CZ))
    p = m.part('mechanical_seal', 'Mechanical Seal', 'mechanical_seal', section='split', explode=(-0.3, 0.2, 0.1), info={'ref': 'mechanical_seal'})
    p.add_split(sb, sf)
    y0, y1 = W + 0.11, W + 0.36
    br = csg('bracket', [lathe('br', [(0.0, y0), (Rc + 0.015, y0), (Rc + 0.015, y0 + 0.015), (0.06, y0 + 0.04), (0.06, y1), (0.0, y1)], mat, 96,
                               axis='Y', center=(0, 0, CZ)),
                         box('brf', (0.16, 0.12, CZ - BP - 0.05), (0, y1 - 0.08, BP + (CZ - BP - 0.05) / 2 + 0.006), mat, bevel=0.004)],
             [cyl('bri', 0.048, y0 + 0.04, y1 - 0.02, mat, 48, axis='Y', center=(0, 0, CZ)), cyl('brs', rs + 0.002, y0 - 0.01, y1 + 0.01, mat, 32, axis='Y', center=(0, 0, CZ)),
              box('brw', (0.2, 0.08, 0.07), (0, y0 + 0.06, CZ), mat, bevel=0.01)], mat)
    p = m.part('bearing_bracket', 'Bearing Bracket', 'bearing_housing', section='split', explode=(0, 0.35, 0), info={'ref': 'bearing_frame'})
    p.add_split(*ksplit(br), smooth_angle=40)
    bbr = merge_halves('brg', [ball_bearing('b1', rs, 0.048, y1 - 0.12, y1 - 0.095, 10, axis='Y', center=(0, 0, CZ)) if False else
                               lathe_split('b1', ring_profile(rs, 0.048, y1 - 0.12, y1 - 0.095), 'steel', 48, axis='Y', center=(0, 0, CZ), phase=math.pi / 2),
                               lathe_split('b2', ring_profile(rs, 0.048, y1 - 0.045, y1 - 0.02), 'steel', 48, axis='Y', center=(0, 0, CZ), phase=math.pi / 2)])
    p = m.part('bearings', 'Shaft Bearings', 'bearings', section='split', explode=(-0.3, 0.35, 0), info={'ref': 'radial_bearing'})
    p.add_split(*bbr)
    add_drive_y(m, W + 0.42, CZ, BP, rs, motor_R=0.13, motor_L=0.42, y_base0=-0.2, base_w=0.6, revs=1)

    yf = -0.009
    rm = rpr + 0.3 * MOD
    for nm, rr, cz_, kind in (('rotor', rm, CZ, 'flow_suction'), ('idler', rpi - 0.2 * MOD, CZ - e, 'flow_suction')):
        arc = [(rr * math.cos(math.radians(a)), yf, cz_ + rr * math.sin(math.radians(a))) for a in range(200, -21, -10)]
        m.flow(f'flow_{nm}_in', [(-0.45, yf, CZ), (-0.1, yf, CZ)] + arc[:12], 'flow_suction', 0.004, 0.06)
        m.flow(f'flow_{nm}_out', arc[11:] + [(0.1, yf, CZ), (0.45, yf, CZ)], 'flow_discharge', 0.004, 0.06)
    return m.export(out_dir)


META = {
    'summary': ('An internal gear pump has two gears of different sizes: an outer rotor with internal teeth, driven by the shaft, '
                'and a smaller idler with external teeth that runs on a fixed pin set off-centre. A crescent-shaped partition '
                'fills the space between them on the side away from the mesh. As the gears turn, teeth separate at the inlet '
                'and draw liquid in; it is carried around in pockets above and below the crescent and squeezed out as the '
                'teeth re-mesh at the outlet. Low shear, low speed and good suction make it ideal for viscous liquids.'),
    'classification': {'family': 'Positive displacement – rotary', 'configuration': 'Internal gear, crescent type ("gear-within-a-gear")'},
    'model_configuration': {'rotor_teeth': ZR, 'idler_teeth': ZI, 'module_mm': MOD * 1000, 'idler_speed_ratio': round(ZR / ZI, 3),
                            'note': 'Many commercial designs use pin-type rotor teeth; involute form shown for clarity.'},
    'standards': [
        {'id': 'API 676', 'title': 'Positive Displacement Pumps – Rotary', 'relevance': 'Process-service rotary PD pumps.', 'edition': 'to be verified'},
        {'id': 'ANSI/HI 3.1-3.5', 'title': 'Rotary Pumps', 'relevance': 'Nomenclature, application, operation.', 'edition': 'to be verified'},
    ],
    'references': ['Karassik et al., Pump Handbook — rotary pumps.', 'Hydraulic Institute rotary pump standards (scope summary).'],
    'components': {
        'pd_casing': C('Contains the gears and forms suction and discharge ports.', 'Cast body with ports at opposite sides of the mesh; jacketed versions for heating.',
                       'Cast iron, ductile iron, steel, stainless.', 'Pressure set by system; needs relief protection.', ['Bore wear', 'Over-pressure cracking'], ['Clearances at overhaul']),
        'ig_rotor': C('Driven internal gear that drives the idler and carries liquid in its tooth spaces.', 'Internal gear cast/machined integral with (or keyed to) the shaft.',
                      'Cast iron, steel, stainless.', 'End clearance to the head controls slip (adjustable on many pumps).', ['Tooth and end-face wear'], ['End clearance setting']),
        'ig_idler': C('External gear driven by the rotor; forms the inner pumping pockets.', 'Gear with bushing turning on the idler pin; turns faster than the rotor (tooth ratio).',
                      'Cast iron, steel, stainless; carbon-graphite or bronze bushing.', 'Bushing lubricated by pumped liquid.', ['Bushing wear (most common wear item)'], ['Pin/bushing clearance']),
        'ig_head': C('Front cover carrying the idler pin and crescent; removable for service.', 'Machined head, often with integral relief valve.',
                     'Cast iron, steel, stainless.', 'Shims between head and casing set rotor end clearance.', ['Pin wear', 'Crescent wear'], ['End clearance']),
        'ig_crescent': C('Seals between rotor tooth tips and idler tooth tips to separate suction from discharge.', 'Crescent-shaped partition cast on the head with the idler pin.',
                         'As head.', 'Wear increases slip.', ['Tip wear'], ['Visual']),
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
