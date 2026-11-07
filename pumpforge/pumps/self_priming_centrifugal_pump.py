"""
Self-Priming Centrifugal Pump — end-suction pump with an integral priming
(separation) chamber, elevated suction inlet with flap check valve, frame-mounted.
Once the casing is filled, the pump can evacuate air from the suction line: the
impeller mixes air with the retained liquid, the mixture separates in the chamber
above the volute, air leaves through the discharge and liquid recirculates.
Shaft along +X (suction at -X), cut plane y = 0.
"""
import math
from mathutils import Matrix
from pumpforge.core import (Model, lathe, cyl, box, csg, split, join, split_faces, split_many, hex_prism, TAU)
from pumpforge.parts import (H_FRAME, place, radial_impeller, volute_casing, add_impeller, nozzle_bolts, add_oh_drive,
                             add_baseplate)
from pumpforge.shapes import sweep_tube

ID = 'self_priming_centrifugal_pump'
CZ = 0.36
BP = 0.10


def build(out_dir):
    m = Model(ID, 'Self-Priming Centrifugal Pump (Priming Chamber, Flap Valve)', 'A · Centrifugal & Special Hydraulic Pumps', META)
    Mx = H_FRAME(0.0, CZ)
    core, shroud, imp = radial_impeller('impeller', 0.24, 0.03, 0.05, 0.02, n_blades=3, mat='ductile_iron', closed=False, wrap=1.3)
    cas, geo = volute_casing('volute', imp, 'paint_blue_dark', r_suc=0.05, L_suc=0.05, r_dis=0.045, H_dis=0.30, flange=False)
    place(cas, Mx)
    zb = geo['z_back']
    xm = -0.05
    top = CZ + 0.50
    # priming / separation chamber around and above the volute, elevated suction housing
    yr = geo['Rend']
    outs = [cas,
            box('ch_o', (zb - xm + 0.03, 0.40, top - (CZ - 0.02)), ((xm + zb) / 2 + 0.005, 0.03, (top + CZ - 0.02) / 2), 'paint_blue_dark', bevel=0.02),
            box('sh_o', (0.22, 0.17, 0.24), (xm - 0.1, 0, CZ + 0.17), 'paint_blue_dark', bevel=0.02),
            cyl('suc_fl', 0.105, -0.02, 0.0, 'paint_blue_dark', 64, axis='X', center=(xm - 0.21, 0, CZ + 0.24), ch=0.003),
            cyl('dis_fl', 0.10, top - 0.001, top + 0.02, 'paint_blue_dark', 64, center=((xm + zb) / 2, yr * 0.5, 0), ch=0.003),
            box('foot', (0.16, 0.34, CZ - geo['r3'] - BP), (zb - 0.08, 0, BP + (CZ - geo['r3'] - BP) / 2 + 0.006), 'paint_blue_dark', bevel=0.005)]
    ins = [box('ch_i', (zb - xm - 0.01, 0.36, top - CZ - 0.24), ((xm + zb) / 2 + 0.005, 0.03, (top - 0.02 + CZ + 0.22) / 2), 'paint_blue_dark', bevel=0.012),
           box('sh_i', (0.19, 0.13, 0.17), (xm - 0.11, 0, CZ + 0.195), 'paint_blue_dark', bevel=0.012),
           cyl('suc_in', 0.06, -0.06, 0.02, 'paint_blue_dark', 64, axis='X', center=(xm - 0.21, 0, CZ + 0.24)),
           cyl('suc_down', 0.05, CZ - 0.01, CZ + 0.14, 'paint_blue_dark', 64, center=(xm - 0.1, 0, 0)),
           sweep_tube('suc_eye', [(xm - 0.1, 0, CZ + 0.03), (xm - 0.1, 0, CZ), (-0.07, 0, CZ), (0.01, 0, CZ)], 0.05, 'paint_blue_dark', 32),
           cyl('dis_in', 0.06, top - 0.06, top + 0.05, 'paint_blue_dark', 64, center=((xm + zb) / 2, yr * 0.5, 0)),
           cyl('recirc', 0.012, CZ + geo['r3'], CZ + 0.24, 'paint_blue_dark', 24, center=(imp['zc'], 0.0, 0)),
           cyl('fill', 0.02, top - 0.06, top + 0.05, 'paint_blue_dark', 24, center=(xm + 0.03, -0.1, 0)),
           cyl('back_open', geo['r_back'], zb - 0.002, zb + 0.06, 'paint_blue_dark', 96, axis='X', center=(0, 0, CZ))]
    body = csg('casing', outs, ins, 'paint_blue_dark')
    cb, cf = split(body)
    bolts = [nozzle_bolts('sfb', 8, 0.17, 0.022, xm - 0.23, xm - 0.245, 'X', (0, 0, CZ + 0.24), phase=math.pi / 8),
             nozzle_bolts('dfb', 8, 0.16, 0.022, top + 0.02, top + 0.035, 'Z', ((xm + zb) / 2, yr * 0.5, 0), phase=math.pi / 8)]
    plug = hex_prism('fill_plug', 0.05, top, top + 0.04, 'steel_dark', center=(xm + 0.03, -0.1, 0))
    bb, bf = split_faces(join('bolts', bolts + [plug]), 'y', 0.0)
    p = m.part('casing', 'Casing with Priming Chamber', 'casing', section='split', explode=(-0.45, 0, 0))
    p.add_split(join('cb', [cb, bb]), join('cf', [cf, bf]), smooth_angle=40)
    add_impeller(m, 'impeller', 'Semi-Open Impeller (3-vane, solids-handling)', core, shroud, Mx, (0, 0, CZ),
                 explode=(-0.2, 0, 0), ref='impeller_open')
    # wear plate
    wp = lathe('wear_plate', [(0.052, -0.012), (0.15, -0.012), (0.15, -0.002), (0.052, -0.002)], 'steel', 96, axis='X', center=(0, 0, CZ))
    p = m.part('wear_plate', 'Replaceable Wear Plate', 'casing', section='split', explode=(-0.3, 0, 0))
    p.add_split(*split(wp))
    # flap (suction check) valve: rubber flap with steel weights, hinged at top
    hx, hz = xm - 0.19, CZ + 0.24 + 0.068
    flap = [cyl('flap', 0.068, -0.006, 0.006, 'rubber', 48, axis='X', center=(xm - 0.19, 0, CZ + 0.24)),
            cyl('fw1', 0.04, -0.012, -0.006, 'steel', 32, axis='X', center=(xm - 0.19, 0, CZ + 0.24)),
            cyl('fw2', 0.04, 0.006, 0.012, 'steel', 32, axis='X', center=(xm - 0.19, 0, CZ + 0.24))]
    fb_, ff_ = split_many('flap_valve', flap)
    p = m.part('flap_valve', 'Suction Flap Check Valve', 'check_valves', pivot=(hx, 0, hz), explode=(-0.35, 0, 0.3))
    p.add(fb_, 'back'); p.add(ff_, 'front')
    for mesh in p.meshes:
        m.keyframes(mesh, 'Operate', 'rotation_euler', [(1, (0, -0.85, 0)), (61, (0, -0.85, 0))])

    add_oh_drive(m, zb, CZ, BP, 0.022, imp['z_back'] - 0.03, frame_R=0.08, frame_L=0.34, motor_R=0.14, motor_L=0.46,
                 frame_mat='paint_blue', cover_r=geo['r_back'] + 0.015)
    add_baseplate(m, xm - 0.32, 1.55, 0.50, BP)

    zc = imp['zc']
    m.flow('flow_suction', [(xm - 0.42, 0.0, CZ + 0.24), (xm - 0.16, 0.0, CZ + 0.24), (xm - 0.1, 0.0, CZ + 0.18),
                            (xm - 0.1, 0.0, CZ + 0.03), (-0.07, 0.0, CZ), (0.0, 0.0, CZ)], 'flow_suction', 0.008, 0.12)
    m.flow('flow_discharge', [(zc, 0.0, CZ + 0.03), (zc, 0.06, CZ + 0.11), (zc, geo['r3'] * 0.8, CZ + 0.12),
                              (zc, yr, CZ + 0.1), (zc, yr, CZ + 0.26), ((xm + zb) / 2, yr * 0.6, top - 0.1),
                              ((xm + zb) / 2, yr * 0.5, top + 0.15)], 'flow_discharge', 0.008, 0.12)
    m.flow('flow_recirculation', [((xm + zb) / 2 - 0.03, 0.02, CZ + 0.26), (imp['zc'], 0.0, CZ + 0.23),
                                  (imp['zc'], 0.0, CZ + geo['r3'] + 0.005)], 'flow_suction', 0.005, 0.06)
    return m.export(out_dir)


META = {
    'summary': ('A centrifugal pump that can re-prime itself from a dry suction line once its casing holds liquid. '
                'During priming the impeller whips the retained liquid and the air drawn from the suction line into a '
                'froth; in the chamber above the volute the air separates and escapes through the discharge, while '
                'the liquid falls back (recirculation port) to be reused. When the suction line is evacuated, the pump '
                'runs as a normal centrifugal pump. The flap valve keeps liquid in the casing when the pump stops.'),
    'classification': {'family': 'Rotodynamic (centrifugal), radial flow', 'configuration': 'End suction, self-priming, frame-mounted',
                       'priming_principle': 'Recirculation-type self-priming with separation chamber'},
    'model_configuration': {'impeller': 'Semi-open, 3 vanes (solids handling) with replaceable wear plate',
                            'suction': 'Elevated suction inlet with weighted rubber flap check valve',
                            'note': 'Priming lift and time depend on design, speed, and the volume of the suction line; use manufacturer data.'},
    'standards': [
        {'id': 'ANSI/HI 1.1-1.2', 'title': 'Rotodynamic Centrifugal Pumps for Nomenclature and Definitions', 'relevance': 'Terminology.', 'edition': 'to be verified'},
        {'id': 'ANSI/HI 1.3', 'title': 'Rotodynamic Centrifugal Pumps for Design and Application', 'relevance': 'Application guidance incl. self-priming pumps.', 'edition': 'to be verified'},
        {'id': 'ISO 9906', 'title': 'Rotodynamic pumps — Hydraulic performance acceptance tests', 'relevance': 'Performance testing.', 'edition': 'to be verified'},
    ],
    'references': ['Karassik et al., Pump Handbook — self-priming centrifugal pumps.', 'Manufacturer self-priming pump manuals (generic practice).'],
    'components': {
        'casing': {'function': 'Volute plus integral priming/separation chamber and elevated suction passage that retain liquid for re-priming.',
                   'construction': 'Large one-piece casting: suction chamber above the impeller eye, volute discharging into a separation chamber with recirculation port near the cutwater, fill and drain plugs.',
                   'material': 'Cast iron, ductile iron, stainless steel.',
                   'operating_conditions': 'Casing must be filled with liquid before the first start; air in the suction line must be able to escape through discharge (open discharge or air-release line).',
                   'failure_modes': ['Loss of prime from flap leakage or suction leaks', 'Overheating if run long without priming', 'Erosion of volute'],
                   'inspection': ['Check priming liquid level', 'Inspect recirculation port and volute']},
        'flap_valve': {'function': 'Suction check valve: holds liquid in the casing when the pump stops so it can re-prime.',
                       'construction': 'Rubber flap with steel weights/reinforcement, hinged at the top of the suction inlet.',
                       'material': 'Neoprene/nitrile with steel weights.',
                       'operating_conditions': 'Lifts open during pumping; closes on stop.', 'failure_modes': ['Tearing or debris holding flap open'],
                       'inspection': ['Inspect flap and seat at regular intervals']},
        'wear_plate': {'function': 'Renewable surface opposite the open impeller face; sets the front clearance.',
                       'construction': 'Plate fixed to the casing/cover with shims or adjusting screws.', 'material': 'Steel, stainless, hardened alloys.',
                       'operating_conditions': 'Clearance growth reduces priming ability and performance.', 'failure_modes': ['Wear'],
                       'inspection': ['Measure and reset clearance']},
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
