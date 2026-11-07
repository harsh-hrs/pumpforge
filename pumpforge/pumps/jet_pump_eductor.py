"""
Jet Pump / Eductor — a high-velocity motive jet from a converging nozzle entrains
the suction fluid by momentum exchange in the suction chamber; the mixture is
homogenised in the throat and slowed in the diffuser, recovering pressure.
No moving parts.  Axis X (motive inlet at -X), cut plane y = 0.
"""
import math
from pumpforge.core import Model, lathe, lathe_split, ring_profile, cyl, box, csg, split, join, merge_halves, split_faces, TAU
from pumpforge.parts import nozzle_bolts, add_tracers, hollow_pipe as pipe, pressure_gauge, gate_valve
from pumpforge.common_meta import C

ID = 'jet_pump_eductor'
CZ = 0.3


def build(out_dir):
    m = Model(ID, 'Jet Pump / Eductor', 'D · Special-Purpose Pumping Systems', META)
    mat = 'stainless'
    # body: suction chamber + throat + diffuser (one casting)
    outs = [lathe('body', [(0.0, -0.18), (0.075, -0.18), (0.075, 0.0), (0.035, 0.05), (0.03, 0.17), (0.06, 0.48), (0.0, 0.48)], mat, 96, axis='X', center=(0, 0, CZ)),
            cyl('sbr', 0.045, CZ - 0.2, CZ, mat, 48, center=(-0.09, 0, 0)), cyl('sfl', 0.08, CZ - 0.2, CZ - 0.185, mat, 48, center=(-0.09, 0, 0), ch=0.003),
            cyl('mfl', 0.1, -0.2, -0.18, mat, 64, axis='X', center=(0, 0, CZ), ch=0.003),
            cyl('dfl', 0.1, 0.48, 0.5, mat, 64, axis='X', center=(0, 0, CZ), ch=0.003)]
    ins = [lathe('cav', [(0.0, -0.16), (0.06, -0.16), (0.06, -0.01), (0.02, 0.04), (0.019, 0.17), (0.048, 0.48), (0.048, 0.52), (0.0, 0.52)], mat, 96, axis='X', center=(0, 0, CZ)),
           cyl('sbb', 0.035, CZ - 0.21, CZ - 0.05, mat, 48, center=(-0.09, 0, 0)), cyl('mb', 0.03, -0.21, -0.15, mat, 48, axis='X', center=(0, 0, CZ))]
    body = csg('eductor_body', outs, ins, mat)
    bolts = [nozzle_bolts('mb_', 8, 0.16, 0.018, -0.18, -0.165, 'X', (0, 0, CZ), math.pi / 8),
             nozzle_bolts('db_', 8, 0.16, 0.018, 0.48, 0.465, 'X', (0, 0, CZ), math.pi / 8),
             nozzle_bolts('sb_', 6, 0.13, 0.016, CZ - 0.185, CZ - 0.17, 'Z', (-0.09, 0, 0), math.pi / 6)]
    bb, bf = split_faces(join('bolts', bolts), 'y', 0.0)
    b, f = split(body)
    p = m.part('body', 'Eductor Body (Suction Chamber, Throat, Diffuser)', 'body', section='split', explode=(0.2, 0, 0), info={'ref': 'eductor_body'})
    p.add_split(join('bb_', [b, bb]), join('bf_', [f, bf]), smooth_angle=40)
    # motive nozzle (threaded insert)
    nz = lathe('nozzle', [(0.022, -0.17), (0.03, -0.17), (0.03, -0.12), (0.022, -0.1), (0.012, -0.03), (0.0095, -0.02), (0.0065, -0.02), (0.0065, -0.03),
                          (0.018, -0.1), (0.022, -0.12)], 'chrome', 64, axis='X', center=(0, 0, CZ))
    p = m.part('motive_nozzle', 'Motive Nozzle (Converging)', 'nozzle', section='split', explode=(-0.25, 0, 0.2), info={'ref': 'motive_nozzle'})
    p.add_split(*split(nz), smooth_angle=40)
    # pipework stubs + gauges
    pipes = [pipe('mp', [(-0.55, 0, CZ), (-0.2, 0, CZ)], 0.03, 'paint_blue', 24), pipe('sp', [(-0.09, 0, CZ - 0.5), (-0.09, 0, CZ - 0.2)], 0.035, 'paint_green', 24),
             pipe('dp', [(0.5, 0, CZ), (0.85, 0, CZ)], 0.048, 'paint_blue', 24)]
    g = [pressure_gauge('g1', (-0.4, 0.0, CZ + 0.028)), pressure_gauge('g2', (0.7, 0.0, CZ + 0.046)), pressure_gauge('g3', (-0.09 + 0.0, 0.035, CZ - 0.42))]
    pv = gate_valve('mv', (-0.36, 0, CZ), 0.03)
    from pumpforge.core import split_many
    pb, pf = split_many('pipes', pipes)
    p = m.part('pipework', 'Motive, Suction & Discharge Piping', 'system_piping', section='split', explode=(0, 0.3, -0.2), info={'ref': 'pipework'})
    p.add_split(pb, pf, smooth_angle=50)
    p = m.part('instruments', 'Pressure Gauges & Motive Isolation Valve', 'instrumentation', explode=(0, -0.3, 0.2), info={'ref': 'pressure_gauge'})
    p.add(join('instruments', g + [pv]), smooth_angle=50)
    # flow tracers
    add_tracers(m, 'motive_tracers', 'Motive Flow (Tracers)', [(-0.5, 0.0, CZ), (-0.02, 0.0, CZ), (0.17, 0.0, CZ), (0.8, 0.0, CZ)], n=10, radius=0.006, mat='flow_discharge')
    add_tracers(m, 'suction_tracers', 'Entrained Suction Flow (Tracers)', [(-0.09, 0.0, CZ - 0.45), (-0.09, 0.0, CZ - 0.05), (-0.03, 0.0, CZ - 0.012), (0.02, 0.0, CZ - 0.008),
                                                                          (0.17, 0.0, CZ - 0.008), (0.8, 0.0, CZ - 0.02)], n=10, radius=0.006, mat='flow_suction')
    m.flow('flow_motive', [(-0.6, 0.0, CZ), (-0.02, 0.0, CZ), (0.9, 0.0, CZ)], 'flow_discharge', 0.005, 0.1)
    m.flow('flow_suction', [(-0.09, 0.0, CZ - 0.55), (-0.09, 0.0, CZ - 0.05), (0.0, 0.0, CZ - 0.012), (0.17, 0.0, CZ - 0.01), (0.9, 0.0, CZ - 0.02)], 'flow_suction', 0.004, 0.1)
    return m.export(out_dir)


META = {
    'summary': ('A jet pump has no moving parts. A motive fluid (water, steam or air) under pressure accelerates through a '
                'converging nozzle into a high-velocity jet. The jet\'s low static pressure and its momentum drag the '
                'surrounding suction fluid into the mixing throat, where the two streams exchange momentum and mix; the '
                'diffuser then slows the mixture and converts velocity back into pressure. Efficiency is modest, but the '
                'device is simple, robust, self-priming and handles slurries, corrosives and gases.'),
    'classification': {'family': 'Kinetic – jet (ejector/eductor)', 'configuration': 'Liquid-motive eductor, single nozzle'},
    'model_configuration': {'key_ratios': 'Area ratio (nozzle/throat) and flow ratio (suction/motive) set the operating curve',
                            'uses': 'Tank mixing, priming centrifugal pumps, deep-well jet pumps, dewatering, chemical induction, steam ejectors for vacuum'},
    'standards': [
        {'id': 'HEI Standards for Steam Jet Vacuum Systems', 'title': 'Heat Exchange Institute', 'relevance': 'Steam ejectors (vacuum service).', 'edition': 'to be verified'},
        {'id': 'ASME PTC 24', 'title': 'Ejectors — Performance Test Code', 'relevance': 'Testing of ejectors.', 'edition': 'to be verified'},
    ],
    'references': ['Karassik et al., Pump Handbook — jet pumps.', 'ESDU / manufacturer eductor sizing guides (generic).'],
    'components': {
        'eductor_body': C('Forms the suction chamber, mixing throat and diffuser.', 'One-piece cast or machined body with flanged motive, suction and discharge connections.',
                          'Cast iron, stainless steel, PVDF, PTFE-lined, carbon steel.', 'Throat length and diffuser angle control efficiency.', ['Erosion in throat', 'Cavitation at high suction lift'],
                          ['Throat bore wear']),
        'motive_nozzle': C('Converts motive pressure to a high-velocity jet.', 'Replaceable converging (or converging–diverging for steam) nozzle insert.', 'Hardened stainless, ceramic, tungsten carbide.',
                           'Nozzle wear changes the flow and performance.', ['Erosion/enlargement', 'Blockage'], ['Nozzle bore measurement']),
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
