"""
Condensate Extraction Pump (CEP) — power-plant application of the vertical can
(VS6) pump: draws saturated condensate from the condenser hotwell under vacuum
and delivers it through the LP heaters/deaerator.  Model adds the can vent
(balance) line back to the condenser and a minimum-flow recirculation branch.
"""
import math
from pumpforge.core import join
from pumpforge.parts import pipe, gate_valve
from pumpforge.vertical import VERTICAL_META
from pumps import vertical_can_pump as vc

ID = 'condensate_extraction_pump'


def extra(m):
    vent = pipe('vent', [(0.0, 0.3, -0.02), (0.0, 0.3, 0.12), (0.0, 0.3, 0.32), (0.0, 0.75, 0.32), (0.0, 1.1, 0.32)], 0.025, 'stainless',
                20, bend=0.06)
    vent_base = pipe('vent_nz', [(0.0, 0.23, -0.02), (0.0, 0.31, -0.02)], 0.03, 'paint_grey', 20)
    v1 = gate_valve('vent_valve', (0.0, 0.75, 0.32), 0.025, axis='Y')
    p = m.part('can_vent_line', 'Can Vent (Balance) Line to Condenser', 'system_piping', explode=(0, 0.4, 0.2),
               info={'ref': 'can_vent'})
    p.add(join('can_vent_line', [vent, vent_base, v1]), smooth_angle=50)
    rec = pipe('recirc', [(0.62, 0.0, 0.43), (0.62, 0.0, 0.7), (0.62, 0.6, 0.7), (0.62, 1.1, 0.7)], 0.03, 'paint_grey', 20, bend=0.07)
    tee = pipe('disch', [(0.48, 0.0, 0.43), (0.9, 0.0, 0.43)], 0.1, 'paint_grey', 32)
    v2 = gate_valve('mf_valve', (0.62, 0.6, 0.7), 0.03, axis='Y', mat='paint_red')
    p = m.part('min_flow_line', 'Discharge Pipe with Minimum-Flow Recirculation Branch', 'system_piping', explode=(0.5, 0, 0.3),
               info={'ref': 'min_flow'})
    p.add(join('min_flow_line', [rec, tee, v2]), smooth_angle=50)


META = {
    'summary': ('Condensate extraction pumps take condensed steam from the turbine condenser hotwell and push it through '
                'the low-pressure feedwater heaters to the deaerator. The liquid is saturated and under vacuum, so the '
                'NPSH available is very small; the pump is therefore a vertical can (barrel) pump whose first stage sits '
                'deep below the hotwell, gaining submergence. The can is vented back to the condenser so vapour cannot '
                'collect, and a minimum-flow line returns condensate to the condenser at low load.'),
    'classification': {'family': 'Rotodynamic (centrifugal), diffuser type', 'configuration': 'Vertical can (VS6), multistage',
                       'application': 'Power plant condensate system (typically 2 x 100 % or 3 x 50 % pumps)'},
    'model_configuration': {'stages': 5, 'first_stage': 'Low-NPSH design (often a larger-eye or double-suction first-stage impeller in real units)',
                            'shaft_seal': 'Mechanical seal or packing sealed with condensate to stop air ingress under vacuum',
                            'piping_shown': 'Can vent to condenser, minimum-flow recirculation branch'},
    'standards': [
        {'id': 'API 610', 'title': 'Centrifugal Pumps …', 'relevance': 'VS6 type definition (power projects may instead use utility specifications).', 'edition': 'to be verified'},
        {'id': 'HEI Standards for Steam Surface Condensers', 'title': 'Heat Exchange Institute', 'relevance': 'Condenser/hotwell design interfaces (NPSH, hotwell storage).', 'edition': 'to be verified'},
        {'id': 'ANSI/HI 9.6.1', 'title': 'Rotodynamic Pumps Guideline for NPSH Margin', 'relevance': 'NPSH margin guidance for low-NPSHa services such as condensate.', 'edition': 'to be verified'},
    ],
    'references': ['Karassik et al., Pump Handbook — power plant pumps.', 'Power plant engineering texts on condensate systems (e.g. Black & Veatch, Power Plant Engineering).'],
    'components': {**vc.META['components'],
        'can_vent': {'function': 'Equalises the can with the condenser and removes vapour/non-condensables so the first stage stays flooded.',
                     'construction': 'Small pipe from the can top (or head suction chamber) back to the condenser steam space, with isolation valve.',
                     'material': 'Stainless or carbon steel.', 'operating_conditions': 'Must be open during operation.',
                     'failure_modes': ['Closed vent causing vapour binding and loss of flow'], 'inspection': ['Valve position checks']},
        'min_flow': {'function': 'Keeps flow above the pump minimum continuous stable flow at low plant load by recirculating to the condenser.',
                     'construction': 'Branch from discharge with control valve (or automatic recirculation valve).',
                     'material': 'Carbon steel.', 'operating_conditions': 'Opens at low flow.', 'failure_modes': ['Valve stuck closed → low-flow vibration/overheating'],
                     'inspection': ['Function test of recirculation control']},
    },
}


def build(out_dir):
    return vc.build(out_dir, pump_id=ID, title='Condensate Extraction Pump (Vertical Can, Multistage)', meta=META, stages=5,
                    head_color='paint_green', extra=extra)


if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
