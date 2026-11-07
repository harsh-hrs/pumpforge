"""
Regenerative Turbine (Peripheral) Pump — close-coupled.  A disc impeller with
many small radial vanes on its rim runs in an annular side channel.  Liquid
circulates repeatedly between vanes and channel (a helical path) gaining energy
each pass, so a small pump produces high head at low flow.  Suction and
discharge ports sit next to each other, separated by a close-clearance stripper.
Shaft along +X, cut plane y = 0.
"""
import math
from pumpforge.core import Model, lathe, lathe_split, ring_profile, cyl, box, csg, split, join, merge_halves, split_faces, split_many, rotate, TAU
from pumpforge.parts import add_motor_h, seal_cartridge, add_baseplate, nozzle_bolts
from pumpforge.shapes import sweep_tube
from pumpforge.common_meta import C

ID = 'regenerative_turbine_pump'
CZ = 0.22
BP = 0.06
RI = 0.1           # impeller radius
W = 0.016          # impeller width
X0 = 0.0           # impeller mid-plane
AP = math.radians(22)   # port angle from top


def build(out_dir):
    m = Model(ID, 'Regenerative Turbine (Peripheral) Pump, Close-Coupled', 'A · Centrifugal & Special Hydraulic Pumps', META)
    mat = 'paint_green'
    zt = CZ + 0.2
    outs = [lathe('cbody', [(0.0, X0 - 0.04), (0.135, X0 - 0.04), (0.145, X0 - 0.03), (0.145, X0 + 0.03), (0.135, X0 + 0.04),
                            (0.0, X0 + 0.04)], mat, 96, axis='X', center=(0, 0, CZ)),
            box('cfoot', (0.07, 0.2, CZ - BP - 0.1), (X0, 0, BP + (CZ - BP - 0.1) / 2 + 0.005), mat, bevel=0.004)]
    ins = [cyl('icav', RI + 0.0008, X0 - W / 2 - 0.0008, X0 + W / 2 + 0.0008, mat, 96, axis='X', center=(0, 0, CZ)),
           lathe('chan', [(RI - 0.024, X0 - 0.02), (RI + 0.012, X0 - 0.02), (RI + 0.018, X0 - 0.012), (RI + 0.018, X0 + 0.012),
                          (RI + 0.012, X0 + 0.02), (RI - 0.024, X0 + 0.02), (RI - 0.024, X0 + W / 2), (RI - 0.024, X0 - W / 2)],
                 mat, 96, a0=AP + 0.08, a1=TAU - AP - 0.08, axis='X', center=(0, 0, CZ), cap_mat=mat),
           cyl('shb', 0.02, X0, X0 + 0.06, mat, 32, axis='X', center=(0, 0, CZ))]
    for sgn in (1, -1):
        y = sgn * (RI + 0.004) * math.sin(AP)
        z0 = CZ + (RI + 0.004) * math.cos(AP)
        outs.append(cyl(f'boss{sgn}', 0.03, z0 - 0.03, zt - 0.01, mat, 48, center=(X0, y, 0)))
        outs.append(cyl(f'pfl{sgn}', 0.05, zt - 0.02, zt, mat, 48, center=(X0, y, 0), ch=0.002))
        ins.append(cyl(f'pb{sgn}', 0.017, z0 - 0.02, zt + 0.01, mat, 32, center=(X0, y, 0)))
    cas = csg('casing', outs, ins, mat)
    cb, cf = split(cas)
    nb = [nozzle_bolts(f'pn{s}', 4, 0.075, 0.014, zt, zt + 0.01, 'Z', (X0, s * (RI + 0.004) * math.sin(AP), 0), math.pi / 4) for s in (1, -1)]
    nbb, nbf = split_faces(join('pn', nb), 'y', 0.0)
    p = m.part('casing', 'Casing with Side Channel & Stripper', 'casing', section='split', explode=(-0.3, 0, 0), info={'ref': 'regen_casing'})
    p.add_split(join('cb', [cb, nbb]), join('cf', [cf, nbf]), smooth_angle=40)
    # impeller with peripheral vanes
    imp = [lathe('disc', [(0.016, X0 - 0.004), (RI - 0.022, X0 - 0.004), (RI - 0.022, X0 + 0.004), (0.016, X0 + 0.004)], 'bronze', 96, axis='X',
                 center=(0, 0, CZ)),
           lathe('hub', [(0.016, X0 - W / 2), (0.03, X0 - W / 2), (0.03, X0 + W / 2), (0.016, X0 + W / 2)], 'bronze', 48, axis='X', center=(0, 0, CZ)),
           lathe('web', [(RI - 0.024, X0 - 0.0015), (RI, X0 - 0.0015), (RI, X0 + 0.0015), (RI - 0.024, X0 + 0.0015)], 'bronze', 96, axis='X',
                 center=(0, 0, CZ))]
    nv = 36
    for i in range(nv):
        v = box(f'v{i}', (W, 0.0025, 0.024), (X0, 0, CZ + RI - 0.012), 'bronze')
        imp.append(rotate(v, TAU * i / nv, 'X', (0, 0, CZ)))
    p = m.part('impeller', 'Peripheral (Regenerative) Impeller — 36 vanes', 'rotating_element', pivot=(X0, 0, CZ), explode=(-0.12, 0, 0.3),
               info={'ref': 'regen_impeller'})
    p.add(join('impeller', imp), smooth_angle=30); p.spin('X', 1)
    # cover/adapter between casing and motor
    xa0, xa1 = X0 + 0.04, X0 + 0.16
    ad = csg('adapter', [lathe('ad', [(0.02, xa0), (0.135, xa0), (0.135, xa0 + 0.015), (0.08, xa0 + 0.03), (0.08, xa1 - 0.02), (0.13, xa1 - 0.01),
                                      (0.13, xa1), (0.02, xa1)], mat, 96, axis='X', center=(0, 0, CZ))],
             [cyl('adi', 0.068, xa0 + 0.03, xa1 + 0.01, mat, 64, axis='X', center=(0, 0, CZ)),
              box('adw', (0.06, 0.3, 0.07), ((xa0 + xa1) / 2 + 0.01, 0, CZ), mat, bevel=0.01)], mat)
    p = m.part('adapter', 'Seal Housing / Motor Adapter', 'casing', section='split', explode=(0.15, 0, 0), info={'ref': 'casing_cover'})
    p.add_split(*split(ad), smooth_angle=40)
    sb, sf = seal_cartridge('seal', xa0 - 0.01, xa0 + 0.05, 0.016, 0.035, center=(0, 0, CZ))
    p = m.part('mechanical_seal', 'Mechanical Seal', 'mechanical_seal', section='split', explode=(0.1, -0.25, 0), info={'ref': 'mechanical_seal'})
    p.add_split(sb, sf)
    add_motor_h(m, 'm_', xa1 + 0.005, CZ, 0.12, 0.34, BP, 0.016, xa1 + 0.005 - X0 + 0.004, explode_dx=0.5, flange_r=0.13, revs=1)
    add_baseplate(m, X0 - 0.12, xa1 + 0.48, 0.32, BP)

    th_s, th_e = AP, TAU - AP
    path = [(X0, 0.006 + (RI + 0.004) * math.sin(AP), zt + 0.12), (X0, (RI + 0.004) * math.sin(AP), CZ + RI)]
    for i in range(60):
        th = th_s + (th_e - th_s) * i / 59
        r = RI + 0.004 + 0.009 * math.cos(i * 1.2)
        x = X0 + 0.012 * math.sin(i * 1.2)
        path.append((x, r * math.sin(th), CZ + r * math.cos(th)))
    path += [(X0, -(RI + 0.004) * math.sin(AP), CZ + RI + 0.02), (X0, -(RI + 0.004) * math.sin(AP), zt + 0.12)]
    m.flow('flow_suction', path[:20], 'flow_suction', 0.003, 0.05)
    m.flow('flow_discharge', path[19:], 'flow_discharge', 0.003, 0.05)
    return m.export(out_dir)


META = {
    'summary': ('In a regenerative turbine pump the liquid enters the side channel and is caught by the small vanes on the '
                'impeller rim, flung outward into the channel and returned to the vane roots further round — many times '
                'during one trip from suction to discharge. Each pass adds energy, so the pump develops far higher head '
                'than a centrifugal pump of the same size at small flows. It can handle some entrained vapour/gas, has a '
                'steep, almost linear H-Q curve and power rises toward shut-off, so it needs relief protection.'),
    'classification': {'family': 'Rotodynamic (peripheral/side-channel)', 'configuration': 'Close-coupled, single stage, end-top ports'},
    'model_configuration': {'impeller': '36 radial vanes machined on a disc rim, floating axially between casing faces (typical)',
                            'clearances': 'Very small side clearances (hundredths of a mm range) — performance is sensitive to wear and solids'},
    'standards': [
        {'id': 'ANSI/HI 1.1-1.2 & 1.3', 'title': 'Rotodynamic centrifugal pumps', 'relevance': 'Regenerative turbine pumps are covered as a rotodynamic subtype in HI documents.', 'edition': 'to be verified'},
        {'id': 'ISO 9906', 'title': 'Hydraulic performance acceptance tests', 'relevance': 'Testing.', 'edition': 'to be verified'},
    ],
    'references': ['Karassik et al., Pump Handbook — regenerative turbine pumps.', 'Manufacturer regenerative turbine pump literature (generic practice).'],
    'components': {
        'regen_casing': C('Forms the annular side channel around the impeller rim and the stripper that separates discharge from suction.',
                          'Two casing halves (shown as one body) with machined channels; ports at the top close together.', 'Cast iron, bronze, stainless steel.',
                          'Pressure rises nearly linearly around the channel; the stripper must stay tight to limit leakage back to suction.',
                          ['Channel and stripper wear from solids', 'Corrosion'], ['Side clearance measurement']),
        'regen_impeller': C('Imparts energy repeatedly to the liquid circulating between vanes and channel.', 'Disc with 20–60 short radial vanes on each face of the rim.',
                            'Bronze, stainless steel, engineered polymers.', 'Requires clean liquids; tight axial clearance.', ['Vane wear', 'Seizure from solids or thermal growth'], ['Clearance, vane condition']),
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
