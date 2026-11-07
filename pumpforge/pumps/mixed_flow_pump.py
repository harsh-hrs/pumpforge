"""
Mixed Flow Pump — large single-stage vertical wet-pit mixed-flow pump (VS1 type),
as used for cooling water intakes, drainage and irrigation.  Mixed-flow impeller
in a diffuser bowl, short column, fabricated above-floor discharge elbow, gland
packing and vertical motor.  Axis Z, floor at z = 0.
"""
from pumpforge.core import Model, cyl
from pumpforge.vertical import (bowl_stage, discharge_case, suction_bell, column, lineshaft_bearing, stage_flow, VERTICAL_META,
                                elbow_head, H, R_SH)

ID = 'mixed_flow_pump'
S = 2.0


def ex(z, dx=0.0):
    return (dx * 1.6, 0.0, 0.3 * z)


def build(out_dir):
    m = Model(ID, 'Mixed Flow Pump (Vertical Wet-Pit, Single Stage)', 'A · Centrifugal & Special Hydraulic Pumps', META)
    hd = elbow_head(m, 0.101 * S, ex, x_noz=1.15, z_bend=0.7, motor_R=0.3, motor_L=0.78, shaft_r=R_SH * S)
    z_col = -1.1
    zr = z_col * 0.5
    column(m, 'column_pipe_1', 'Column Pipe – Upper', 0.0, zr + 0.01, s=S, ex=ex)
    column(m, 'column_pipe_2', 'Column Pipe – Lower', zr - 0.01, z_col, s=S, ex=ex)
    lineshaft_bearing(m, 1, zr, s=S, ex=ex)
    z_dc = z_col - 0.26 * S
    discharge_case(m, z_dc, s=S, ex=ex, top_r=0.101 * S)
    z0 = z_dc - H * S
    bowl_stage(m, 1, z0, s=S, ex=ex, label='Pump', imp_blades=4, wrap=1.0)
    suction_bell(m, z0, s=S, ex=ex, strainer=False, lip_r=0.26)
    sh = cyl('shaft', R_SH * S, z0 - 0.235 * S, hd['z_shaft_top'], 'stainless', 40, ch=0.003)
    p = m.part('pump_shaft', 'Pump & Line Shaft', 'rotating_element', explode=ex(-0.8, 0.8), info={'ref': 'line_shaft'})
    p.add(sh); p.spin('Z', 1)
    Y = 0.02
    m.flow('flow_suction', [(-0.3, Y, z0 - 0.75), (-0.32, Y, z0 - 0.5), (-0.12, Y, z0 - 0.2), (-0.12, Y, z0)], 'flow_suction', 0.014, 0.3)
    m.flow('flow_suction2', [(0.3, Y, z0 - 0.75), (0.32, Y, z0 - 0.5), (0.12, Y, z0 - 0.2), (0.12, Y, z0)], 'flow_suction', 0.014, 0.3)
    d = stage_flow(z0, s=S, sx=1, Y=Y) + [(0.15, Y, z_dc + 0.3), (0.15, Y, 0.0), (0.16, Y, 0.55), (0.4, Y, 0.7), (1.5, Y, 0.7)]
    m.flow('flow_discharge', d, 'flow_discharge', 0.014, 0.35)
    return m.export(out_dir)


META = {
    'summary': ('A mixed-flow pump adds energy partly by centrifugal action and partly by the lift of its blades: liquid '
                'leaves the impeller diagonally, between the radial direction of a centrifugal pump and the axial direction '
                'of a propeller pump. This suits large flows at moderate heads (specific speed roughly between radial and '
                'axial machines). In the vertical wet-pit form shown, the bowl hangs in the intake sump and a discharge '
                'elbow above the floor turns the flow into the outlet pipe.'),
    'classification': {'family': 'Rotodynamic, mixed flow', 'configuration': 'Vertical wet pit, single stage, line-shaft', 'api_610_type': 'VS1 / VS3-style arrangement'},
    'model_configuration': {'impeller': 'Enclosed mixed-flow, 4 blades', 'shaft_seal': 'Gland packing in elbow stuffing box',
                            'specific_speed_note': 'Mixed-flow pumps typically sit around Ns ≈ 4,000–9,000 (US units) / nq ≈ 80–160; verify against design data.'},
    'standards': [
        {'id': 'ANSI/HI 9.8', 'title': 'Rotodynamic Pumps for Pump Intake Design', 'relevance': 'Sump geometry and submergence are critical for large wet-pit pumps.', 'edition': 'to be verified'},
        {'id': 'ANSI/HI 2.1-2.2 / 2.3', 'title': 'Rotodynamic vertical pumps', 'relevance': 'Nomenclature, design and application.', 'edition': 'to be verified'},
        {'id': 'ISO 9906', 'title': 'Hydraulic performance acceptance tests', 'relevance': 'Testing (often by model test for very large pumps).', 'edition': 'to be verified'},
    ],
    'references': ['Stepanoff — Centrifugal and Axial Flow Pumps.', 'Karassik et al., Pump Handbook — mixed and axial flow pumps.'],
    'components': dict(VERTICAL_META),
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
