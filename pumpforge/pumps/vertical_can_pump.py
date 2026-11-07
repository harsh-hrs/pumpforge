"""
Vertical Can Pump (barrel-type, API 610 VS6 style) — multistage vertical turbine
bowl assembly enclosed in a suction can (barrel) installed below grade.  Suction
and discharge nozzles are both on the above-ground discharge head; liquid enters
the can, flows down around the column and bowls, and is drawn up through the
bell.  The extra can length gives NPSH available for low-NPSH liquids
(condensate, LPG, hydrocarbons).  Axis Z, ground (can flange) at z = 0.
"""
import math
from pumpforge.core import (Model, lathe, lathe_split, ring_profile, cyl, box, csg, split, join, merge_halves, split_faces,
                            TAU)
from pumpforge.parts import add_motor_v, nozzle_bolts, seal_cartridge
from pumpforge.vertical import (bowl_stage, discharge_case, suction_bell, column, lineshaft_bearing, stage_flow, VERTICAL_META,
                                nut_ring, R_SH, H)

ID = 'vertical_can_pump'
N = 4
Z_COL_BOT = -0.90
SP = 0.30


def ex(z, dx=0.0):
    return (dx, 0.0, SP * z)


def build(out_dir, pump_id=ID, title='Vertical Can Pump (Barrel Type, Multistage)', meta=None, stages=N, head_color='paint_blue', extra=None):
    m = Model(pump_id, title, 'A · Centrifugal & Special Hydraulic Pumps' if pump_id == ID else 'E · Industrial Pump Applications',
              meta or META)
    hc = head_color
    # ---------- discharge/suction head
    zt = 0.62
    outs = [cyl('hb', 0.36, 0.0, 0.04, hc, 96, ch=0.004),
            lathe('hbody', [(0, 0.03), (0.265, 0.03), (0.265, 0.5), (0.2, 0.58), (0.1, zt), (0, zt)], hc, 96),
            cyl('sn', 0.115, -0.46, -0.1, hc, 64, axis='X', center=(0, 0, 0.17)),
            cyl('snf', 0.17, -0.48, -0.445, hc, 64, axis='X', center=(0, 0, 0.17), ch=0.003),
            cyl('dn', 0.115, 0.1, 0.46, hc, 64, axis='X', center=(0, 0, 0.43)),
            cyl('dnf', 0.17, 0.445, 0.48, hc, 64, axis='X', center=(0, 0, 0.43), ch=0.003)]
    ins = [lathe('scav', [(0.123, -0.02), (0.232, -0.02), (0.232, 0.28), (0.123, 0.28)], hc, 96),
           cyl('snb', 0.1, -0.5, -0.15, hc, 64, axis='X', center=(0, 0, 0.17)),
           lathe('dcav', [(0, -0.02), (0.101, -0.02), (0.101, 0.40), (0.07, 0.5), (0, 0.52)], hc, 96),
           cyl('dnb', 0.1, 0.0, 0.5, hc, 64, axis='X', center=(0, 0, 0.43)),
           cyl('shb', 0.03, 0.4, zt + 0.01, hc, 48)]
    head = csg('head', outs, ins, hc)
    hb, hf = split(head)
    bolts = [nozzle_bolts('snb_', 8, 0.29, 0.026, -0.445, -0.43, 'X', (0, 0, 0.17), phase=math.pi / 8),
             nozzle_bolts('dnb_', 8, 0.29, 0.026, 0.445, 0.43, 'X', (0, 0, 0.43), phase=math.pi / 8),
             nozzle_bolts('hbn', 12, 0.64, 0.03, 0.04, 0.062, 'Z', (0, 0, 0), phase=math.pi / 12)]
    bb, bf = split_faces(join('hbolts', bolts), 'y', 0.0)
    p = m.part('discharge_head', 'Discharge Head (with Suction Nozzle)', 'discharge_head', section='split', explode=ex(0.5),
               info={'ref': 'can_head'})
    p.add_split(join('hb_', [hb, bb]), join('hf_', [hf, bf]), smooth_angle=40)
    # motor stand + seal + coupling + motor
    z1 = zt + 0.36
    st = csg('stand', [lathe('st', [(0.0, zt - 0.01), (0.2, zt - 0.01), (0.2, zt + 0.02), (0.17, zt + 0.04), (0.17, z1 - 0.03),
                                    (0.26, z1 - 0.02), (0.26, z1), (0.0, z1)], hc, 96)],
             [cyl('sti', 0.155, zt + 0.045, z1 + 0.01, hc, 96), cyl('stb', 0.07, zt - 0.02, zt + 0.06, hc, 64),
              box('stw', (0.16, 0.5, 0.2), (0, 0, zt + 0.2), hc, bevel=0.02)], hc)
    p = m.part('motor_stand', 'Motor Stand', 'discharge_head', section='split', explode=ex(1.0), info={'ref': 'motor_stand'})
    p.add_split(*split(st), smooth_angle=40)
    sb, sf = seal_cartridge('seal', zt + 0.03, zt + 0.12, R_SH * 1.2, 0.05, axis='Z')
    p = m.part('mechanical_seal', 'Cartridge Mechanical Seal', 'mechanical_seal', section='split', explode=ex(0.9, -0.5),
               info={'ref': 'mechanical_seal'})
    p.add_split(sb, sf)
    cp = join('coupling', [lathe('cp1', [(R_SH, zt + 0.17), (0.07, zt + 0.17), (0.07, zt + 0.2), (0.04, zt + 0.21), (0.04, zt + 0.235),
                                         (0.07, zt + 0.245), (0.07, zt + 0.275), (R_SH, zt + 0.275)], 'steel', 64)])
    p = m.part('coupling', 'Adjustable Spacer Coupling', 'power_transmission', pivot=(0, 0, zt + 0.22), explode=ex(1.1, 0.7),
               info={'ref': 'coupling_vertical'})
    p.add(cp); p.spin('Z', 2)
    add_motor_v(m, 'm_', z1 + 0.025, 0.21, 0.6, 0.03, z1 + 0.025 - (zt + 0.25), explode_dz=0.75, flange_r=0.26)

    # ---------- can (barrel)
    z_dc = Z_COL_BOT - 0.26
    z_bell = z_dc - stages * H
    z_can = z_bell - 0.29 - 0.22
    can = lathe('can', [(0.232, 0.0), (0.36, 0.0), (0.36, -0.04), (0.25, -0.045), (0.25, z_can + 0.08), (0.2, z_can + 0.01),
                        (0.0, z_can), (0.0, z_can + 0.012), (0.19, z_can + 0.022), (0.24, z_can + 0.08), (0.24, -0.04),
                        (0.232, -0.04)], 'paint_grey', 96)
    p = m.part('suction_can', 'Suction Can (Barrel)', 'can', section='split', explode=(-0.9, 0, 0.0), info={'ref': 'suction_can'})
    p.add_split(*split(can), smooth_angle=40)

    # ---------- column, bowls, bell
    zr = Z_COL_BOT * 0.5
    column(m, 'column_pipe_1', 'Column Pipe – Upper', 0.0, zr + 0.01, ex=ex)
    column(m, 'column_pipe_2', 'Column Pipe – Lower', zr - 0.01, Z_COL_BOT, ex=ex)
    lineshaft_bearing(m, 1, zr, ex=ex)
    discharge_case(m, z_dc, ex=ex)
    for k in range(stages):
        bowl_stage(m, k + 1, z_dc - (k + 1) * H, ex=ex, label='Stage')
    suction_bell(m, z_bell, ex=ex, strainer=False)

    ls = cyl('lineshaft', R_SH, z_bell - 0.235, zt + 0.17, 'stainless', 32, ch=0.002)
    p = m.part('pump_shaft', 'Pump & Line Shaft', 'rotating_element', explode=ex(-0.6, 0.8), info={'ref': 'line_shaft'})
    p.add(ls); p.spin('Z', 2)

    Y = 0.012
    m.flow('flow_suction', [(-0.75, Y, 0.17), (-0.2, Y, 0.17), (-0.2, Y, 0.0), (-0.21, Y, z_dc), (-0.215, Y, z_bell - 0.2),
                            (-0.12, Y, z_bell - 0.33), (-0.06, Y, z_bell - 0.12), (-0.06, Y, z_bell)], 'flow_suction', 0.009, 0.3)
    m.flow('flow_suction2', [(0.21, Y, 0.0), (0.21, Y, z_dc), (0.215, Y, z_bell - 0.2), (0.12, Y, z_bell - 0.33),
                             (0.06, Y, z_bell - 0.12), (0.06, Y, z_bell)], 'flow_suction', 0.009, 0.3)
    disc = []
    for k in reversed(range(stages)):
        disc += stage_flow(z_dc - (k + 1) * H, sx=-1)
    disc += [(-0.075, Y, z_dc + 0.1), (-0.075, Y, 0.3), (-0.05, Y, 0.42), (0.12, Y, 0.43), (0.75, Y, 0.43)]
    m.flow('flow_discharge', disc, 'flow_discharge', 0.009, 0.3)
    if extra:
        extra(m)
    return m.export(out_dir)


META = {
    'summary': ('A multistage vertical turbine (diffuser) pump installed inside a pressurised suction can (barrel). '
                'Suction and discharge both connect to the head at grade; the liquid fills the can, flows down outside '
                'the column and bowls and enters the first-stage impeller at the bottom. Because the first stage sits '
                'well below grade, the static liquid height in the can adds to NPSH available — the main reason to '
                'choose a can pump for liquids near their boiling point.'),
    'classification': {'family': 'Rotodynamic (centrifugal), diffuser type', 'configuration': 'Vertically suspended, double casing (can), multistage',
                       'api_610_type': 'VS6 (double-casing diffuser, vertically suspended)'},
    'model_configuration': {'stages': N, 'can': 'Fabricated barrel with dished bottom, flanged to head', 'shaft_seal': 'Cartridge mechanical seal',
                            'driver': 'Vertical motor with thrust bearing; adjustable spacer coupling', 'note': 'Lengths shortened for display.'},
    'standards': [
        {'id': 'API 610', 'title': 'Centrifugal Pumps for Petroleum, Petrochemical and Natural Gas Industries', 'relevance': 'Pump type VS6 and associated requirements.', 'edition': 'to be verified'},
        {'id': 'ANSI/HI 2.1-2.2 / 2.3', 'title': 'Rotodynamic Vertical Pumps — nomenclature, design and application', 'relevance': 'Vertical pump terminology and application.', 'edition': 'to be verified'},
        {'id': 'ASME BPVC Sec. VIII', 'title': 'Pressure vessels', 'relevance': 'Often referenced for can (barrel) design; confirm project requirements.', 'edition': 'to be verified'},
    ],
    'references': ['Karassik et al., Pump Handbook — vertical pumps.', 'API 610 pump type classification (scope summary).'],
    'components': {**VERTICAL_META,
        'can_head': {'function': 'Supports pump and motor, carries both suction and discharge nozzles and separates the suction chamber (can) from the discharge passage.',
                     'construction': 'Cast or fabricated head: suction nozzle feeds the annulus around the column; discharge nozzle connects to the column bore above it.',
                     'material': 'Carbon steel (fabricated), cast steel, stainless.', 'operating_conditions': 'Suction side at can pressure; discharge side at full pressure.',
                     'failure_modes': ['Nozzle overload', 'Gasket leak between can and head'], 'inspection': ['Pipe supports', 'Flange joints']},
        'suction_can': {'function': 'Pressure vessel that contains the bowl assembly in suction liquid and provides extra submergence (NPSHa).',
                        'construction': 'Rolled plate barrel with dished bottom, top flange bolted to the head; vent connection.',
                        'material': 'Carbon steel, stainless steel.', 'operating_conditions': 'Must be vented and filled before start; rated for suction pressure (often more).',
                        'failure_modes': ['Trapped vapour causing loss of prime', 'Corrosion'], 'inspection': ['Venting before start', 'Thickness surveys']},
        'motor_stand': {'function': 'Supports the motor and gives access to the coupling and seal.', 'construction': 'Cast/fabricated stand with windows.',
                        'material': 'Cast iron/steel.', 'operating_conditions': 'Structural natural frequency must be clear of running speed.',
                        'failure_modes': ['Reed-frequency resonance'], 'inspection': ['Vibration at motor top']},
        'coupling_vertical': {'function': 'Transmits torque and down-thrust to the motor thrust bearing; adjusting nut sets impeller lift.',
                              'construction': 'Adjustable flanged spacer coupling.', 'material': 'Steel.', 'operating_conditions': 'Carries full thrust.',
                              'failure_modes': ['Wrong lift setting', 'Loose bolts'], 'inspection': ['Lift setting per manufacturer']},
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
