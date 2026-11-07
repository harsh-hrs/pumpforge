"""
Horizontal Split Case Pump (API 610 BB1 style) — axially (horizontally) split casing,
double-suction impeller between two bearings, side suction / side discharge nozzles in the
lower half, flexible coupling and foot-mounted motor on a common baseplate.
The upper casing half lifts off in the cutaway to expose the complete rotor.
Shaft along +X, cut plane y = 0 (upper half role 'hide').
"""
import math
from pumpforge.core import Model, lathe, join, split_many, cyl
from pumpforge.parts import add_coupling, add_motor_h, add_baseplate, hollow_pipe, pressure_gauge, nozzle_bolts
from pumpforge.splitcase import add_split_case, SPLITCASE_META
from pumpforge.common_meta import C

ID = 'horizontal_split_case_pump'
CZ = 0.62
BP = 0.12
S = 1.0


def build(out_dir):
    m = Model(ID, 'Horizontal Split Case Pump (BB1, Double Suction)', '1 · Centrifugal & Rotodynamic Pumps', META)
    g = add_split_case(m, CZ, S, mat='paint_blue', foot_z=BP, revs=2)
    imp = g['imp']
    # casing wear rings at both impeller eyes (impeller mid-plane at x = 0)
    zc, nk, rw = imp['zc'], imp['neck'], imp['r_wear']
    rings = []
    for sx in (-1, 1):
        x0, x1 = sx * zc, sx * (zc + nk)
        rings.append(lathe(f'cwr{sx}', [(rw + 0.0015, min(x0, x1)), (rw + 0.011, min(x0, x1)), (rw + 0.011, max(x0, x1)), (rw + 0.0015, max(x0, x1))],
                           'bronze', 96, axis='X', center=(0, 0, CZ)))
    rb, rf = split_many('wear_rings', rings)
    p = m.part('wear_rings', 'Casing Wear Rings (both eyes)', 'casing', section='split', explode=(0, -0.35, 0.45), info={'ref': 'wear_ring'})
    p.add_split(rb, rf)
    xc = 0.62 + 0.27
    add_coupling(m, 'coupling', xc, xc + 0.11, CZ, 0.075, 0.032, explode=(0.4, 0, 0), foot_z=BP)
    mo = add_motor_h(m, 'm_', xc + 0.13, CZ, 0.26, 0.85, BP, 0.04, 0.12, explode_dx=0.9)
    add_baseplate(m, -0.85, mo['x1'] + 0.05, 1.0, BP)
    zd, yd = g['zend'], g['yend']
    pipes = [hollow_pipe('suc', [(0, -1.05, zd), (0, -0.62, zd)], 0.11, 'paint_green', 40), hollow_pipe('dis', [(0, yd, zd), (0, yd + 0.45, zd)], 0.1, 'paint_blue', 40)]
    pb, pf = split_many('pipes', pipes)
    p = m.part('nozzle_spools', 'Suction & Discharge Spool Pieces', 'system_piping', section='split', explode=(0, 0, -0.3), info={'ref': 'pipework'})
    p.add_split(pb, pf, smooth_angle=50)
    gg = [pressure_gauge('pg_s', (0.0, -0.8, zd + 0.11)), pressure_gauge('pg_d', (0.0, yd + 0.2, zd + 0.1))]
    p = m.part('pressure_gauges', 'Suction & Discharge Pressure Gauges', 'instrumentation', explode=(0, 0, 0.5), info={'ref': 'pressure_gauge'})
    p.add(join('gauges', gg), smooth_angle=50)
    m.flow('flow_suction', [(0, -1.25, zd), (0, -0.3, zd), (0, -0.15, CZ - 0.15), (0.12, -0.05, CZ - 0.1), (0.12, 0.0, CZ - 0.02), (0.06, 0.0, CZ)], 'flow_suction', 0.012, 0.25)
    m.flow('flow_suction2', [(0, -0.15, CZ - 0.15), (-0.12, -0.05, CZ - 0.1), (-0.12, 0.0, CZ - 0.02), (-0.06, 0.0, CZ)], 'flow_suction', 0.012, 0.2)
    m.flow('flow_discharge', [(0.0, 0.0, CZ + 0.05)] + g['path'][10::3] + [(0, yd + 0.65, zd)], 'flow_discharge', 0.012, 0.25)
    return m.export(out_dir)


META = {
    'summary': ('A horizontal split case pump has its casing divided on the horizontal plane through the shaft centreline. '
                'The suction and discharge nozzles are cast into the lower half, so after removing the upper half the whole '
                'rotor (shaft, double-suction impeller, wear rings, sleeves, seals and bearings) can be lifted out without '
                'disturbing the pipework or the motor. Liquid from the side suction nozzle divides into two channels and '
                'enters the impeller from both sides; this halves the eye velocity (lower NPSH required) and balances the '
                'axial thrust. The impeller sits between two bearings, giving a stiff rotor suitable for large flows in '
                'water supply, cooling water, fire protection and pipeline service.'),
    'classification': {'family': 'Rotodynamic (centrifugal), radial flow, single stage', 'configuration': 'Between bearings, axially split, double suction',
                       'api_610_type': 'BB1 (one- and two-stage axially split)'},
    'model_configuration': {'impeller': 'Closed double-suction impeller with casing wear rings on both eyes',
                            'casing': 'Single volute, side suction and side discharge in the lower half; upper half with lifting eye and split-flange bolting',
                            'shaft_seal': 'Mechanical seals at both shaft exits (gland packing is a common alternative in water service)',
                            'bearings': 'Radial bearing inboard (coupling end), thrust bearing outboard',
                            'drive': 'Flexible coupling to a foot-mounted motor on a common baseplate'},
    'standards': [
        {'id': 'API 610 / ISO 13709', 'title': 'Centrifugal pumps for petroleum, petrochemical and natural gas industries', 'relevance': 'BB1 type definition.', 'edition': 'to be verified'},
        {'id': 'ANSI/HI 1.1-1.2, 1.3', 'title': 'Rotodynamic centrifugal pumps — nomenclature; design and application', 'relevance': 'Axially split pump nomenclature.', 'edition': 'to be verified'},
        {'id': 'ANSI/HI 9.6.3', 'title': 'Rotodynamic Pumps — Guideline for Operating Regions', 'relevance': 'Preferred/allowable operating region.', 'edition': 'to be verified'},
        {'id': 'ISO 9906', 'title': 'Rotodynamic pumps — Hydraulic performance acceptance tests', 'relevance': 'Performance testing.', 'edition': 'to be verified'},
        {'id': 'NFPA 20', 'title': 'Installation of Stationary Pumps for Fire Protection', 'relevance': 'When used as a fire pump.', 'edition': 'to be verified'},
    ],
    'references': ['Hydraulic Institute — Pump Types (between-bearings, axially split).', 'KSB Pump Lexicon — "Axially split pump", "Double-suction impeller".',
                   'US DOE — Improving Pumping System Performance: A Sourcebook for Industry.', 'Karassik et al., Pump Handbook.'],
    'components': {**SPLITCASE_META},
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
