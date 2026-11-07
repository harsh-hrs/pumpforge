"""
Horizontal Multistage Pump (ring-section / segmental, API 610 BB4 style) — flagship
teaching model for stage-by-stage pressure generation: impellers in series, each followed
by a diffuser and return vanes; stage casings clamped by tie bolts; balance drum with
leak-off line for axial thrust; bearings at both ends.
Overlays: flow, stage-by-stage pressure, axial thrust & balancing.
Shaft along +X, cut plane y = 0.
"""
from pumps.boiler_feedwater_pump import build as _build, META as _BFP
from pumpforge.common_meta import C

ID = 'horizontal_multistage_pump'


def build(out_dir):
    return _build(out_dir, pump_id=ID, title='Horizontal Multistage Pump (Ring-Section, 6 Stages)', meta=META, n=6, mat='paint_blue')


META = {
    'summary': ('A horizontal multistage pump places several impellers in series on one shaft. Each stage — impeller, diffuser and '
                'return channel — adds roughly the same head, so the pressure builds up stage by stage from suction to discharge. '
                'The impeller flings liquid outward and raises its velocity and pressure; the diffuser vanes slow it down and convert '
                'velocity into more pressure; the return vanes guide it back inward, without swirl, to the eye of the next impeller. '
                'Because every impeller faces the same way, their axial thrusts add up; a balance drum at the discharge end, with a '
                'leak-off line back to suction, cancels most of it, and a thrust bearing takes the rest. Multistage pumps serve high-head '
                'duties such as boiler feed, reverse-osmosis feed, high-rise water supply, mine dewatering and pressure boosting.'),
    'classification': {'family': 'Rotodynamic (centrifugal), radial flow, multistage', 'configuration': 'Horizontal, between bearings, radially split ring-section (segmental)',
                       'api_610_type': 'BB4 (single casing, radially split, multistage); barrel BB5 and axially split BB3 are alternatives'},
    'model_configuration': {'stages': 6, 'impellers': 'Closed, same hand, in series (inline arrangement)',
                            'stage_hardware': 'Stage casing + diffuser vanes + return (cross-over) vanes per stage, clamped by 8 tie bolts',
                            'axial_thrust': 'Balance drum + balance bush + leak-off line to suction; thrust bearing for the residual',
                            'alternatives': 'Balance disc, opposed (back-to-back) impellers, or thrust bearing only (small pumps)',
                            'teaching_overlays': 'pressure (stage-by-stage), thrust (impeller thrust vs balance-drum force), flow'},
    'standards': [
        {'id': 'API 610 / ISO 13709', 'title': 'Centrifugal pumps for petroleum, petrochemical and natural gas industries', 'relevance': 'BB3/BB4/BB5 multistage types.', 'edition': 'to be verified'},
        {'id': 'ANSI/HI 1.1-1.2, 1.3', 'title': 'Rotodynamic centrifugal pumps — nomenclature; design and application', 'relevance': 'Multistage nomenclature.', 'edition': 'to be verified'},
        {'id': 'ANSI/HI 9.6.1', 'title': 'Rotodynamic Pumps Guideline for NPSH Margin', 'relevance': 'First-stage suction conditions.', 'edition': 'to be verified'},
        {'id': 'ISO 9906', 'title': 'Rotodynamic pumps — Hydraulic performance acceptance tests', 'relevance': 'Performance testing.', 'edition': 'to be verified'},
    ],
    'references': ['Hydraulic Institute — Pump Types (between-bearings, multistage).', 'KSB Pump Lexicon — "Multistage pump", "Axial thrust", "Balancing device".',
                   'US DOE — Improving Pumping System Performance: A Sourcebook for Industry.', 'Gülich J.F., Centrifugal Pumps (Springer) — axial thrust balancing.'],
    'components': dict(_BFP['components']),
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
