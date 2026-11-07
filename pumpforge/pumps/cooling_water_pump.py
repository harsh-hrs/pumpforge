"""
Cooling Water Pump — plant cooling-water service with a horizontally split-case,
double-suction pump (BB1), flexible coupling and motor on a common baseplate,
plus the typical station valves: suction isolation, discharge check and
isolation valves and pressure gauges.  Shaft along +X, cut plane y = 0
(upper casing half lifts off in cutaway).
"""
import math
from pumpforge.core import Model, join, split_many
from pumpforge.parts import add_coupling, add_motor_h, add_baseplate, hollow_pipe, gate_valve, check_valve, pressure_gauge
from pumpforge.splitcase import add_split_case, SPLITCASE_META
from pumpforge.common_meta import C

ID = 'cooling_water_pump'
CZ = 0.62
BP = 0.12
S = 1.0


def build(out_dir, pump_id=ID, title='Cooling Water Pump (Split-Case, Double-Suction)', meta=None, mat='paint_blue', extra=None, driver=True):
    m = Model(pump_id, title, 'E · Industrial Pump Applications', meta or META)
    g = add_split_case(m, CZ, S, mat=mat, foot_z=BP, revs=2)
    xc = 0.62 + 0.27
    if driver:
        add_coupling(m, 'coupling', xc, xc + 0.11, CZ, 0.075, 0.032, explode=(0.4, 0, 0), foot_z=BP)
        mo = add_motor_h(m, 'm_', xc + 0.13, CZ, 0.26, 0.85, BP, 0.04, 0.12, explode_dx=0.9)
        add_baseplate(m, -0.85, mo['x1'] + 0.05, 1.0, BP)
    zd, yd = g['zend'], g['yend']
    pipes = [hollow_pipe('suc', [(0, -1.6, zd), (0, -0.62, zd)], 0.11, 'paint_green', 40), hollow_pipe('dis', [(0, yd, zd), (0, yd + 1.2, zd)], 0.1, mat, 40)]
    pb, pf = split_many('pipes', pipes)
    p = m.part('station_piping', 'Suction & Discharge Piping', 'system_piping', section='split', explode=(0, 0, -0.3), info={'ref': 'pipework'})
    p.add_split(pb, pf, smooth_angle=50)
    v = [gate_valve('suc_valve', (0, -1.15, zd), 0.11, axis='Y', mat='paint_green'), check_valve('chk', (0, yd + 0.35, zd), 0.1, axis='Y'),
         gate_valve('dis_valve', (0, yd + 0.85, zd), 0.1, axis='Y')]
    p = m.part('station_valves', 'Suction Isolation, Discharge Check & Isolation Valves', 'valves', explode=(0, 0, 0.35), info={'ref': 'gate_valve'})
    p.add(join('valves', v), smooth_angle=40)
    gg = [pressure_gauge('pg_s', (0.0, -0.8, zd + 0.11)), pressure_gauge('pg_d', (0.0, yd + 0.15, zd + 0.1))]
    p = m.part('pressure_gauges', 'Suction & Discharge Pressure Gauges', 'instrumentation', explode=(0, 0, 0.5), info={'ref': 'pressure_gauge'})
    p.add(join('gauges', gg), smooth_angle=50)
    if extra:
        extra(m, g)
    m.flow('flow_suction', [(0, -1.8, zd), (0, -0.3, zd), (0, -0.15, CZ - 0.15), (0.12, -0.05, CZ - 0.1), (0.12, 0.0, CZ - 0.02), (0.06, 0.0, CZ)], 'flow_suction', 0.012, 0.25)
    m.flow('flow_suction2', [(0, -0.15, CZ - 0.15), (-0.12, -0.05, CZ - 0.1), (-0.12, 0.0, CZ - 0.02), (-0.06, 0.0, CZ)], 'flow_suction', 0.012, 0.2)
    m.flow('flow_discharge', [(0.0, 0.0, CZ + 0.05)] + g['path'][10::3] + [(0, yd + 1.4, zd)], 'flow_discharge', 0.012, 0.25)
    return m.export(out_dir)


META = {
    'summary': ('Cooling-water pumps circulate large volumes of water through heat exchangers, condensers and process coolers at '
                'moderate head. A horizontally split-case, double-suction pump is a common choice: high flow with low NPSH '
                'required, balanced axial thrust, long bearing life with bearings at both ends of the shaft, and the whole '
                'rotor can be lifted out after removing the upper casing half without disturbing the piping or motor. '
                'Typical installations run duty/standby pumps with check and isolation valves on each.'),
    'classification': {'family': 'Rotodynamic (centrifugal), radial flow', 'configuration': 'Horizontal, axially split, double suction, between bearings',
                       'api_610_type': 'BB1', 'application': 'Open/closed cooling water circuits, condenser cooling, HVAC chilled/condenser water'},
    'model_configuration': {'driver': 'Foot-mounted TEFC motor with flexible spacer coupling', 'valves': 'Suction isolation, discharge non-return and isolation',
                            'water_quality_note': 'Seawater/raw water needs material selection (bronze, duplex) and strainers upstream.'},
    'standards': [
        {'id': 'API 610', 'title': 'Centrifugal Pumps …', 'relevance': 'BB1 definition (industrial/utility specs often adapt it).', 'edition': 'to be verified'},
        {'id': 'ISO 13709 / ISO 9905/5199', 'title': 'Centrifugal pump technical requirements', 'relevance': 'Technical classes for industrial pumps.', 'edition': 'to be verified'},
        {'id': 'ANSI/HI 9.6.3', 'title': 'Allowable Operating Region', 'relevance': 'Keep operation near BEP for long life.', 'edition': 'to be verified'},
    ],
    'references': ['Karassik et al., Pump Handbook — split-case pumps; cooling water systems.', 'ASHRAE Handbook — HVAC Systems and Equipment (pumps).'],
    'components': {**SPLITCASE_META},
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
