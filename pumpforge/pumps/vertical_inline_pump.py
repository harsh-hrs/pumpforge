"""
Vertical Inline Pump — single-stage centrifugal pump whose suction and discharge
flanges are on one common centreline (installed directly in a pipeline), with a
vertical flange-mounted motor on a lantern (motor stand), rigid spacer coupling
and cartridge mechanical seal (OH4-style; OH3 adds a bearing bracket, OH5 is
close-coupled).  Axis vertical, flanges along X, cut plane y = 0.
"""
import math
from mathutils import Matrix
from pumpforge.core import (Model, lathe, lathe_split, ring_profile, cyl, box, csg, split, join, split_faces, split_many,
                            merge_halves, TAU)
from pumpforge.parts import (V_FRAME, place, radial_impeller, volute_casing, add_impeller, nozzle_bolts, seal_cartridge,
                             add_motor_v, pressure_gauge)
from pumpforge.shapes import sweep_tube

ID = 'vertical_inline_pump'
Z_S = 0.20       # flange centreline height
Z_EYE = 0.32     # impeller eye plane
XF = 0.31        # flange face distance from axis


def build(out_dir):
    m = Model(ID, 'Vertical Inline Centrifugal Pump', 'A · Centrifugal & Special Hydraulic Pumps', META)
    Mx = V_FRAME(Z_EYE)
    core, shroud, imp = radial_impeller('impeller', 0.21, 0.018, 0.046, 0.017, n_blades=6, mat='bronze', wrap=1.7)
    cas, geo = volute_casing('vol', imp, 'paint_blue', r_suc=0.05, L_suc=0.05, r_dis=0.04, H_dis=0.10, flange=False)
    place(cas, Mx)
    t = 0.012
    rd = 0.05
    zv = Z_EYE + imp['zc']
    y_n = -geo['Rend']
    dis_path = [(geo['H_dis'] - 0.02, y_n, zv), (0.16, y_n * 0.7, zv - 0.01), (0.22, y_n * 0.15, Z_S + 0.03), (0.25, 0, Z_S),
                (XF, 0, Z_S)]
    suc_path = [(-XF, 0, Z_S), (-0.12, 0, Z_S), (-0.03, 0, Z_S + 0.01), (0, 0, Z_S + 0.07), (0, 0, Z_EYE - 0.03)]
    outs = [cas,
            sweep_tube('suc_o', suc_path, rd + t, 'paint_blue', 40), sweep_tube('dis_o', dis_path, rd + t, 'paint_blue', 40),
            cyl('sfl', 0.115, -XF, -XF + 0.024, 'paint_blue', 64, axis='X', center=(0, 0, Z_S), ch=0.003),
            cyl('dfl', 0.115, XF - 0.024, XF, 'paint_blue', 64, axis='X', center=(0, 0, Z_S), ch=0.003),
            lathe('ped', [(0.06, 0.0), (0.15, 0.0), (0.15, 0.02), (0.08, 0.04), (0.07, Z_S - 0.05), (0.06, Z_S - 0.05)],
                  'paint_blue', 64)]
    ins = [sweep_tube('suc_i', [(-XF - 0.02, 0, Z_S)] + suc_path[1:] + [(0, 0, Z_EYE + 0.0)], rd, 'paint_blue', 40),
           sweep_tube('dis_i', [(geo['H_dis'] - 0.06, y_n, zv)] + dis_path[1:] + [(XF + 0.02, 0, Z_S)], rd, 'paint_blue', 40),
           sweep_tube('dnoz', [(geo['H_dis'] - 0.1, y_n, zv), (geo['H_dis'] + 0.0, y_n, zv)], 0.04, 'paint_blue', 40)]
    cas = csg('casing', outs, ins, 'paint_blue')
    cb, cf = split(cas)
    bolts = [nozzle_bolts('sfb', 8, 0.18, 0.022, -XF + 0.024, -XF + 0.04, 'X', (0, 0, Z_S), phase=math.pi / 8),
             nozzle_bolts('dfb', 8, 0.18, 0.022, XF - 0.024, XF - 0.04, 'X', (0, 0, Z_S), phase=math.pi / 8)]
    gauges = [pressure_gauge('pg_s', (-XF + 0.07, 0.0, Z_S + rd + t - 0.004)), pressure_gauge('pg_d', (XF - 0.07, 0.0, Z_S + rd + t - 0.004))]
    bb, bf = split_faces(join('bolts', bolts), 'y', 0.0)
    p = m.part('casing', 'Inline Volute Casing', 'casing', section='split', explode=(0, 0, -0.35), info={'ref': 'inline_casing'})
    p.add_split(join('cb', [cb, bb]), join('cf', [cf, bf]), smooth_angle=40)
    p = m.part('pressure_gauges', 'Suction & Discharge Pressure Gauges', 'instrumentation', explode=(0, -0.25, 0.1),
               info={'ref': 'pressure_gauge'})
    p.add(join('gauges', gauges), smooth_angle=50)
    add_impeller(m, 'impeller', 'Closed Impeller', core, shroud, Mx, (0, 0, Z_EYE), axis='Z', explode=(0, 0, -0.12))

    zb = Z_EYE + geo['z_back']
    cov = lathe('cover', [(0.022, zb), (geo['r_bf'], zb), (geo['r_bf'], zb + 0.02), (0.055, zb + 0.03), (0.055, zb + 0.09),
                          (0.045, zb + 0.09), (0.045, zb + 0.02), (0.022, zb + 0.016)], 'paint_blue', 96)
    p = m.part('casing_cover', 'Casing Cover & Seal Chamber', 'casing', section='split', explode=(0, 0, 0.05), info={'ref': 'casing_cover'})
    p.add_split(*split(cov), smooth_angle=40)
    sb, sf = seal_cartridge('seal', zb + 0.025, zb + 0.105, 0.017, 0.04, axis='Z')
    p = m.part('mechanical_seal', 'Cartridge Mechanical Seal', 'mechanical_seal', section='split', explode=(-0.35, 0, 0.12),
               info={'ref': 'mechanical_seal'})
    p.add_split(sb, sf)
    # lantern / motor stand with two windows
    z1 = zb + 0.32
    ln = csg('lantern', [lathe('ln', [(0.0, zb + 0.02), (geo['r_bf'], zb + 0.02), (geo['r_bf'], zb + 0.04), (0.13, zb + 0.06),
                                       (0.13, z1 - 0.03), (0.19, z1 - 0.02), (0.19, z1), (0.0, z1)], 'paint_blue', 96)],
             [cyl('lni', 0.118, zb + 0.05, z1 + 0.01, 'paint_blue', 96), cyl('lnb', 0.056, zb, zb + 0.07, 'paint_blue', 64),
              box('win', (0.13, 0.4, 0.17), (0, 0, zb + 0.18), 'paint_blue', bevel=0.02, segs=3)], 'paint_blue')
    p = m.part('motor_stand', 'Motor Stand (Lantern)', 'casing', section='split', explode=(0, 0, 0.32))
    p.add_split(*split(ln), smooth_angle=40)
    sh = cyl('shaft', 0.017, Z_EYE + imp['z_back'] - 0.02, zb + 0.2, 'stainless', 32, ch=0.002)
    p = m.part('pump_shaft', 'Pump Shaft', 'rotating_element', pivot=(0, 0, zb), explode=(0.42, 0, 0.1), info={'ref': 'pump_shaft'})
    p.add(sh); p.spin('Z', 2)
    cp = [lathe('cp', [(0.017, zb + 0.15), (0.045, zb + 0.15), (0.045, zb + 0.26), (0.017, zb + 0.26)], 'steel', 64),
          lathe('cpg', [(0.044, zb + 0.204), (0.05, zb + 0.204), (0.05, zb + 0.206), (0.044, zb + 0.206)], 'steel_dark', 64)]
    from pumpforge.core import bolt_circle
    cp.append(bolt_circle('cpb', 4, 0.07, 0.012, zb + 0.15, zb + 0.142, phase=math.pi / 4))
    cp.append(bolt_circle('cpb2', 4, 0.07, 0.012, zb + 0.26, zb + 0.268, phase=math.pi / 4))
    p = m.part('coupling', 'Rigid Spacer Coupling (Split)', 'power_transmission', pivot=(0, 0, zb + 0.2), explode=(0.42, 0, 0.35),
               info={'ref': 'coupling_rigid'})
    p.add(join('coupling', cp)); p.spin('Z', 2)
    add_motor_v(m, 'm_', z1 + 0.025, 0.16, 0.46, 0.022, z1 + 0.025 - (zb + 0.205), explode_dz=0.55, flange_r=0.19)

    m.flow('flow_suction', [(-XF - 0.25, 0.0, Z_S)] + suc_path[1:] + [(0, 0.0, Z_EYE + 0.01)], 'flow_suction', 0.007, 0.1)
    r2 = imp['r2']
    spiral = []
    for i in range(25):
        th = math.pi / 2 + (2 * math.pi - math.pi / 2) * i / 24
        R = geo['r3'] + 0.8 * geo['a_max'] * (0.4 + 0.6 * i / 24)
        lx, ly = R * math.cos(th), R * math.sin(th)
        spiral.append((ly, -lx, zv))
    m.flow('flow_discharge', [(0, 0.0, Z_EYE + 0.02), (0.0, -0.05, zv)] + spiral + dis_path[1:] + [(XF + 0.25, 0, Z_S)],
           'flow_discharge', 0.007, 0.1)
    return m.export(out_dir)


META = {
    'summary': ('A centrifugal pump designed to be installed directly in a straight pipe run: suction and discharge '
                'flanges face each other on one centreline. Liquid enters horizontally, turns upward into the eye of '
                'the vertical-shaft impeller, is discharged into the volute and turned back to the outlet flange. The '
                'vertical motor sits on a lantern above; a spacer coupling lets the seal be changed without disturbing '
                'the motor. Small footprint, common in HVAC, water and process plants.'),
    'classification': {'family': 'Rotodynamic (centrifugal), radial flow', 'configuration': 'Vertical inline, overhung',
                       'api_610_type': 'OH3 (bearing bracket), OH4 (rigidly coupled), OH5 (close-coupled); model shows OH4-style rigid coupling'},
    'model_configuration': {'impeller': 'Closed radial, 6 blades', 'seal': 'Cartridge mechanical seal', 'motor': 'Vertical flange-mounted (thrust carried by motor bearings)'},
    'standards': [
        {'id': 'API 610', 'title': 'Centrifugal Pumps for Petroleum, Petrochemical and Natural Gas Industries', 'relevance': 'Defines OH3/OH4/OH5 vertical inline types.', 'edition': 'to be verified'},
        {'id': 'ASME B73.2', 'title': 'Specification for Vertical In-Line Centrifugal Pumps for Chemical Process', 'relevance': 'Chemical-process inline pumps.', 'edition': 'to be verified'},
        {'id': 'ISO 9906', 'title': 'Hydraulic performance acceptance tests', 'relevance': 'Testing.', 'edition': 'to be verified'},
    ],
    'references': ['Karassik et al., Pump Handbook.', 'API 610 pump type classification (scope summary).'],
    'components': {
        'inline_casing': {'function': 'Volute casing with suction and discharge passages turned onto a common horizontal centreline.',
                          'construction': 'One-piece casting with integral suction elbow, volute and discharge passage; pedestal foot; gauge tappings.',
                          'material': 'Cast iron, ductile iron, carbon steel, stainless steel.',
                          'operating_conditions': 'Pipe loads act directly on the pump; piping must be supported either side.',
                          'failure_modes': ['Nozzle overload from pipe strain', 'Erosion at cutwater'], 'inspection': ['Pipe supports', 'Wall thickness']},
        'motor_stand': {'function': 'Supports the vertical motor and aligns it to the pump; windows give access to coupling and seal.',
                        'construction': 'Cast lantern with machined registers.', 'material': 'Cast iron.', 'operating_conditions': 'Carries motor weight and torque reaction.',
                        'failure_modes': ['Register damage causing misalignment', 'Structural resonance'], 'inspection': ['Vibration at motor top']},
        'coupling_rigid': {'function': 'Rigidly connects pump shaft to motor shaft; the spacer can be removed to change the seal.',
                           'construction': 'Split clamp halves with spacer; no flexibility — alignment comes from machined registers.',
                           'material': 'Steel.', 'operating_conditions': 'Motor bearings carry pump thrust.', 'failure_modes': ['Loose bolts', 'Run-out after poor assembly'],
                           'inspection': ['Shaft run-out at seal after assembly']},
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
