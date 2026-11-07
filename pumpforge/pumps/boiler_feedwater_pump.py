"""
Boiler Feedwater Pump — horizontal multistage ring-section (segmental) pump:
suction casing, five stage casings with diffusers and return channels, discharge
casing with balance drum, clamped by tie bolts; bearings at both ends; motor via
flexible spacer coupling.  Feeds the boiler/steam generator from the deaerator.
Shaft along +X, cut plane y = 0.
"""
import math
from pumpforge.core import Model, lathe, lathe_split, ring_profile, cyl, box, csg, split, join, merge_halves, split_many, rotate, TAU
from pumpforge.parts import (H_FRAME, hollow_pipe, radial_impeller, add_impeller, ball_bearing, seal_cartridge, add_coupling, add_motor_h, add_baseplate,
                             nozzle_bolts, pressure_gauge)
from pumpforge.shapes import vane
from pumpforge.common_meta import C

ID = 'boiler_feedwater_pump'
CZ = 0.5
BP = 0.12
N = 5
LS = 0.11
X0 = 0.0


def build(out_dir, pump_id=ID, title='Boiler Feedwater Pump (Multistage Ring-Section, BB4)', meta=None, n=N, mat='paint_blue_dark', extra=None):
    N = n
    m = Model(pump_id, title, '5 · Industrial Pump Applications', meta or META)
    imp_info = None
    for k in range(N):
        zk = X0 + k * LS
        core, shroud, imp = radial_impeller(f'imp{k}', 0.26, 0.014, 0.042, 0.03, n_blades=7, mat='stainless', wrap=1.9)
        imp_info = imp
        add_impeller(m, f'impeller_{k + 1}', f'Impeller – Stage {k + 1}', core, shroud, H_FRAME(zk, CZ), (zk, 0, CZ), explode=(0, -0.5, 0.0), ref='impeller_closed')
        zf, b2 = imp['zf'], imp['b2']
        cas = [lathe(f'sc{k}', [(0.19, -0.012), (0.215, -0.012), (0.215, LS - 0.012), (0.19, LS - 0.012)], mat, 96, axis='X', center=(zk, 0, CZ)),
               lathe(f'dia{k}', [(0.05, 0.062), (0.19, 0.062), (0.19, 0.074), (0.05, 0.074)], mat, 96, axis='X', center=(zk, 0, CZ)),
               lathe(f'lip{k}', [(0.045, LS - 0.03), (0.06, LS - 0.03), (0.06, LS - 0.012), (0.045, LS - 0.012)], mat, 64, axis='X', center=(zk, 0, CZ)),
               lathe(f'dw{k}', [(0.136, zf - 0.009), (0.19, zf - 0.009), (0.19, zf - 0.003), (0.136, zf - 0.003)], mat, 96, axis='X', center=(zk, 0, CZ))]
        from pumpforge.parts import H_FRAME as HF
        Mx = HF(zk, CZ)
        dv = [vane(f'dv{k}{i}', [(0.136, zf - 0.004), (0.188, zf - 0.004)], [(0.136, zf + b2 + 0.004), (0.188, zf + b2 + 0.004)],
                   lambda s, t, th=TAU * i / 9: th + 0.45 * s, 0.006, mat, ns=10, nt=3) for i in range(9)]
        rv = [vane(f'rv{k}{i}', [(0.186, 0.076), (0.12, 0.076), (0.065, 0.076)], [(0.186, 0.098), (0.12, 0.098), (0.065, 0.098)],
                   lambda s, t, th=TAU * i / 8 + 0.2: th + 1.0 * s - 0.4 * s * s, 0.006, mat, ns=12, nt=3) for i in range(8)]
        for v in dv + rv:
            v.data.transform(Mx)
        pieces = cas + dv + rv
        b, f = split_many(f'stage_{k + 1}', pieces)
        p = m.part(f'stage_casing_{k + 1}', f'Stage Casing with Diffuser & Return Vanes – Stage {k + 1}', 'stages', section='split',
                   explode=(0.08 * (k - N / 2), 0, 0.45), info={'ref': 'bfp_stage'})
        p.add_split(b, f, smooth_angle=40)
    # suction casing
    xs0, xs1 = X0 - 0.17, X0 - 0.012
    sc = csg('suction_casing', [lathe('sco', [(0.0, xs0), (0.235, xs0), (0.235, xs1), (0.0, xs1)], mat, 96, axis='X', center=(0, 0, CZ)),
                                cyl('sn', 0.075, CZ, CZ + 0.33, mat, 48, center=(xs0 + 0.08, 0, 0)), cyl('snf', 0.13, CZ + 0.31, CZ + 0.335, mat, 48, center=(xs0 + 0.08, 0, 0), ch=0.004),
                                box('sft', (0.12, 0.62, CZ - BP - 0.1), (xs0 + 0.08, 0, BP + (CZ - BP - 0.1) / 2 + 0.006), mat, bevel=0.006)],
             [cyl('sni', 0.06, CZ + 0.05, CZ + 0.34, mat, 48, center=(xs0 + 0.08, 0, 0)),
              lathe('sci', [(0.045, xs0 + 0.03), (0.17, xs0 + 0.03), (0.17, xs1 - 0.02), (0.06, xs1 - 0.005), (0.045, xs1 + 0.01)], mat, 96, axis='X', center=(0, 0, CZ)),
              cyl('ssh', 0.034, xs0 - 0.01, xs0 + 0.04, mat, 32, axis='X', center=(0, 0, CZ))], mat)
    p = m.part('suction_casing', 'Suction Casing', 'casing', section='split', explode=(-0.4, 0, 0), info={'ref': 'bfp_suction'})
    p.add_split(*split(sc), smooth_angle=40)
    # discharge casing with balance drum chamber
    xd0 = X0 + N * LS - 0.012
    xd1 = xd0 + 0.2
    dc = csg('discharge_casing', [lathe('dco', [(0.0, xd0), (0.235, xd0), (0.235, xd1), (0.0, xd1)], mat, 96, axis='X', center=(0, 0, CZ)),
                                   cyl('dn', 0.07, CZ, CZ + 0.33, mat, 48, center=(xd0 + 0.07, 0, 0)), cyl('dnf', 0.13, CZ + 0.31, CZ + 0.335, mat, 48, center=(xd0 + 0.07, 0, 0), ch=0.004),
                                   box('dft', (0.12, 0.62, CZ - BP - 0.1), (xd0 + 0.1, 0, BP + (CZ - BP - 0.1) / 2 + 0.006), mat, bevel=0.006)],
             [cyl('dni', 0.055, CZ + 0.05, CZ + 0.34, mat, 48, center=(xd0 + 0.07, 0, 0)),
              lathe('dci', [(0.05, xd0 - 0.01), (0.19, xd0 - 0.01), (0.19, xd0 + 0.11), (0.05, xd0 + 0.12)], mat, 96, axis='X', center=(0, 0, CZ)),
              cyl('bdc', 0.075, xd0 + 0.1, xd1 + 0.01, mat, 64, axis='X', center=(0, 0, CZ))], mat)
    p = m.part('discharge_casing', 'Discharge Casing (with Balance Drum Chamber)', 'casing', section='split', explode=(0.45, 0, 0), info={'ref': 'bfp_discharge'})
    p.add_split(*split(dc), smooth_angle=40)
    bush = lathe('bdb', ring_profile(0.0615, 0.075, xd0 + 0.115, xd1 - 0.01), 'bronze', 64, axis='X', center=(0, 0, CZ))
    p = m.part('balance_drum_bush', 'Balance Drum Bushing', 'balancing', section='split', explode=(0.45, -0.35, 0), info={'ref': 'bfp_balance'})
    p.add_split(*split(bush))
    tb = [cyl(f'tb{i}', 0.012, xs0 + 0.01, xd1 - 0.01, 'steel', 16, axis='X', center=(0, 0.25 * math.sin(TAU * (i + 0.5) / 8), CZ + 0.25 * math.cos(TAU * (i + 0.5) / 8)))
          for i in range(8)]
    tb += [box(f'tn{i}{e}', (0.025, 0.035, 0.035), (x, 0.25 * math.sin(TAU * (i + 0.5) / 8), CZ + 0.25 * math.cos(TAU * (i + 0.5) / 8)), 'steel_dark', bevel=0.003)
           for i in range(8) for e, x in enumerate((xs0 - 0.004, xd1 + 0.004))]
    bb, bf = split_many('tie_bolts', tb)
    p = m.part('tie_bolts', 'Tie Bolts (Clamp the Stage Stack)', 'casing', explode=(0, 0, 0.75), info={'ref': 'bfp_tiebolts'})
    p.add(bb, 'back'); p.add(bf, 'front')
    # shaft + balance drum (rotating)
    xb0, xb1 = xs0 - 0.2, xd1 + 0.22
    sh = join('rotor', [cyl('shaft', 0.03, xb0 - 0.05, xb1 + 0.12, 'steel', 32, axis='X', center=(0, 0, CZ), ch=0.002),
                        cyl('drum', 0.061, xd0 + 0.115, xd1 - 0.01, 'stainless', 64, axis='X', center=(0, 0, CZ))])
    p = m.part('shaft', 'Shaft & Balance Drum', 'rotating_element', pivot=(0, 0, CZ), explode=(0, -0.8, 0), info={'ref': 'pump_shaft'})
    p.add(sh, smooth_angle=40); p.spin('X', 2)
    for side, xb, sx in (('suction', xb0, -1), ('discharge', xb1, 1)):
        bh = csg(f'bh{side}', [lathe(f'bho{side}', [(0, xb - 0.08), (0.1, xb - 0.08), (0.1, xb + 0.08), (0, xb + 0.08)], mat, 64, axis='X', center=(0, 0, CZ)),
                              box(f'bhs{side}', (0.12, 0.12, CZ - BP - 0.06), (xb, 0, BP + (CZ - BP - 0.06) / 2 + 0.006), mat, bevel=0.005)],
                 [cyl(f'bhi{side}', 0.068, xb - 0.06, xb + 0.06, mat, 48, axis='X', center=(0, 0, CZ)), cyl(f'bhsh{side}', 0.033, xb - 0.1, xb + 0.1, mat, 32, axis='X', center=(0, 0, CZ))], mat)
        p = m.part(f'bearing_housing_{side}', f'Bearing Housing – {side.title()} End', 'bearing_housing', section='split', explode=(sx * 0.6, 0, 0), info={'ref': 'bearing_frame'})
        p.add_split(*split(bh), smooth_angle=40)
        p = m.part(f'bearing_{side}', f'{"Thrust" if sx > 0 else "Radial"} Bearing – {side.title()} End', 'bearings', section='split', explode=(sx * 0.6, -0.4, 0),
                   info={'ref': 'thrust_bearing' if sx > 0 else 'radial_bearing'})
        p.add_split(*ball_bearing(f'b{side}', 0.03, 0.068, xb - 0.03, xb + 0.03, 10, center=(0, 0, CZ)))
        xs_ = (xs0 - 0.12, xs0 - 0.02) if sx < 0 else (xd1 + 0.02, xd1 + 0.12)
        sb, sf = seal_cartridge(f'seal_{side}', xs_[0], xs_[1], 0.03, 0.06, center=(0, 0, CZ))
        p = m.part(f'seal_{side}', f'Mechanical Seal – {side.title()} End', 'mechanical_seal', section='split', explode=(sx * 0.45, -0.3, 0.2), info={'ref': 'mechanical_seal'})
        p.add_split(sb, sf)
    xc = xb1 + 0.12
    add_coupling(m, 'coupling', xc, xc + 0.12, CZ, 0.08, 0.03, explode=(0.8, 0, 0), foot_z=BP)
    mo = add_motor_h(m, 'm_', xc + 0.14, CZ, 0.28, 0.9, BP, 0.04, 0.12, explode_dx=1.2)
    add_baseplate(m, xb0 - 0.2, mo['x1'] + 0.05, 0.9, BP)
    g = [pressure_gauge('pgs', (xs0 + 0.08, 0.0, CZ + 0.335)), pressure_gauge('pgd', (xd0 + 0.07, 0.0, CZ + 0.335))]
    p = m.part('gauges', 'Suction & Discharge Pressure Gauges', 'instrumentation', explode=(0, 0, 0.4), info={'ref': 'pressure_gauge'})
    p.add(join('gauges', g), smooth_angle=50)
    Y = 0.0
    path = [(xs0 + 0.08, Y, CZ + 0.6), (xs0 + 0.08, Y, CZ + 0.1), (xs0 + 0.1, Y, CZ + 0.08), (X0 - 0.02, Y, CZ + 0.05)]
    for k in range(N):
        zk = X0 + k * LS
        path += [(zk + 0.005, Y, CZ + 0.05), (zk + 0.035, Y, CZ + 0.12), (zk + 0.04, Y, CZ + 0.17), (zk + 0.068, Y, CZ + 0.2), (zk + 0.087, Y, CZ + 0.17),
                 (zk + 0.087, Y, CZ + 0.07), (zk + LS - 0.005, Y, CZ + 0.05)]
    path += [(xd0 + 0.05, Y, CZ + 0.1), (xd0 + 0.07, Y, CZ + 0.2), (xd0 + 0.07, Y, CZ + 0.6)]
    m.flow('flow_suction', path[:6], 'flow_suction', 0.006, 0.08)
    m.flow('flow_discharge', path[5:], 'flow_discharge', 0.006, 0.08)
    # balance leak-off line: balance chamber (behind the drum) back to suction
    lk = [(xd1 - 0.05, -0.15, CZ + 0.10), (xd1 - 0.05, -0.27, CZ + 0.17), (xs0 + 0.05, -0.27, CZ + 0.17), (xs0 + 0.05, -0.15, CZ + 0.10)]
    lb, lf = split_many('leakoff', [hollow_pipe('leakoff', lk, 0.014, 'stainless', 20, bend=0.04, t=0.003)])
    p = m.part('balance_leakoff_line', 'Balance Leak-off Line (to Suction)', 'balancing', section='split', explode=(0, -0.35, 0.3), info={'ref': 'bfp_leakoff'})
    p.add_split(lb, lf, smooth_angle=50)
    m.flow('flow_balance_leakoff', [(xd1 - 0.03, 0.0, CZ + 0.07), (xd1 - 0.05, -0.12, CZ + 0.09)] + lk[1:] + [(xs0 + 0.05, -0.05, CZ + 0.06)], 'flow_discharge', 0.004, 0.1)
    teaching_overlays(m, N, xs0, xs1, xd0, xd1)
    if extra:
        extra(m)
    return m.export(out_dir)


def teaching_overlays(m, N, xs0, xs1, xd0, xd1):
    """Stage-by-stage pressure build-up and axial-thrust balance overlays."""
    from pumpforge.shapes import cone_arrow, sweep_tube
    ramp = lambda k: f'pressure_{min(9, round(9 * k / N))}'
    rings = [lathe('p_suc', [(0.237, xs0 + 0.01), (0.25, xs0 + 0.01), (0.25, xs1 - 0.005), (0.237, xs1 - 0.005)], ramp(0), 96, axis='X', center=(0, 0, CZ))]
    for k in range(N):
        zk = X0 + k * LS
        rings.append(lathe(f'p_st{k}', [(0.217, zk - 0.007), (0.232, zk - 0.007), (0.232, zk + LS - 0.017), (0.217, zk + LS - 0.017)], ramp(k + 1), 96, axis='X', center=(0, 0, CZ)))
        m.annotate('pressure', f'+{k + 1}Δp', (zk + LS / 2, 0.0, CZ + (0.29 if k % 2 == 0 else 0.37)), value=k + 1)
    rings.append(lathe('p_dis', [(0.237, xd0 + 0.01), (0.25, xd0 + 0.01), (0.25, xd1 - 0.01), (0.237, xd1 - 0.01)], ramp(N), 96, axis='X', center=(0, 0, CZ)))
    m.annotate('pressure', 'Suction p_s (lowest, NPSH-critical)', (xs0 + 0.02, 0.0, CZ - 0.36), value=0)
    m.annotate('pressure', f'Discharge p_s + {N}Δp', (xd0 + 0.14, 0.0, CZ - 0.30), value=N)
    m.overlay('pressure', join('pressure_rings', rings), 'Stage-by-stage pressure', split=True, description=(
              'Colour rings show static pressure rising from suction (blue) to discharge (red). Each stage adds roughly the same head, so '
              'total head ≈ number of stages × head per stage at the same flow.'))
    arrows = []
    for k in range(N):
        zk = X0 + k * LS
        for sz in (1, -1):
            base = (zk + 0.075, 0.0, CZ + sz * 0.1)
            arrows += [sweep_tube(f'ta{k}{sz}', [base, (base[0] - 0.035, 0.0, base[2])], 0.0045, 'thrust', 10),
                       cone_arrow(f'tc{k}{sz}', (base[0] - 0.035, 0.0, base[2]), (-1, 0, 0), 0.022, 0.011, 'thrust')]
    xm = X0 + N * LS / 2
    arrows += [sweep_tube('tnet', [(xm + 0.25, 0.0, CZ - 0.27), (xm - 0.2, 0.0, CZ - 0.27)], 0.011, 'thrust', 16),
               cone_arrow('tnetc', (xm - 0.2, 0.0, CZ - 0.27), (-1, 0, 0), 0.06, 0.028, 'thrust')]
    m.overlay('thrust', join('thrust_arrows', arrows), 'Axial thrust & balancing',
              'Each impeller is pushed towards suction (magenta) because its back shroud sees higher pressure than the eye side. '
              'The balance drum (green) has full discharge pressure on its inner face and near-suction pressure in the balance chamber '
              'behind it (leak-off line), creating an opposing force. A thrust bearing carries the small residual.')
    counter = [sweep_tube('cdr', [(xd0 + 0.12, 0.0, CZ - 0.13), (xd0 + 0.36, 0.0, CZ - 0.13)], 0.011, 'counter_force', 16),
               cone_arrow('cdrc', (xd0 + 0.36, 0.0, CZ - 0.13), (1, 0, 0), 0.06, 0.028, 'counter_force')]
    m.overlay('thrust', join('counter_arrows', counter))
    m.annotate('thrust', 'Net impeller thrust → towards suction', (xm, 0.0, CZ - 0.32))
    m.annotate('thrust', 'Balance drum force → towards discharge', (xd0 + 0.24, 0.0, CZ - 0.18))
    m.annotate('thrust', 'Leak-off returns balance-chamber water to suction', (xd1 - 0.05, -0.27, CZ + 0.22))



META = {
    'summary': ('A boiler feedwater pump raises water from the deaerator (low pressure, near saturation temperature) to above '
                'boiler drum or steam-generator pressure — often well over 100 bar in power plants. To reach that head at '
                'reasonable speed it uses several impellers in series: after each impeller a diffuser recovers pressure and '
                'return vanes lead the water inward to the next impeller eye. The stage casings are clamped between suction and '
                'discharge casings by tie bolts (ring-section design). A balance drum at the high-pressure end cancels most of '
                'the axial thrust. A minimum-flow recirculation valve protects the pump at low boiler demand.'),
    'classification': {'family': 'Rotodynamic (centrifugal), radial flow, multistage', 'configuration': 'Horizontal, between bearings, ring-section (segmental), radially split',
                       'api_610_type': 'BB4 (single casing, radially split, multistage); barrel BB5 for highest pressures'},
    'model_configuration': {'stages': N, 'axial_thrust': 'Balance drum (balance disc or opposed impellers are alternatives)', 'driver': 'Motor via flexible spacer coupling (turbine or VFD/hydraulic coupling on large units)',
                            'npsh_note': 'Deaerator elevation or a booster pump provides NPSH margin for hot feedwater.'},
    'standards': [
        {'id': 'API 610', 'title': 'Centrifugal Pumps …', 'relevance': 'BB4/BB5 multistage types.', 'edition': 'to be verified'},
        {'id': 'ASME PTC 8.2', 'title': 'Centrifugal Pumps — Performance Test Code', 'relevance': 'Power-plant pump testing.', 'edition': 'to be verified'},
        {'id': 'ANSI/HI 9.6.1', 'title': 'NPSH Margin', 'relevance': 'Feedwater pumps require adequate NPSH margin.', 'edition': 'to be verified'},
        {'id': 'IBR / ASME BPVC Sec. I', 'title': 'Boiler codes', 'relevance': 'Feedwater system requirements (country-specific).', 'edition': 'to be verified'},
    ],
    'references': ['Karassik et al., Pump Handbook — boiler feed pumps.', 'Power plant engineering texts (feedwater systems).'],
    'components': {
        'bfp_stage': C('One pumping stage: diffuser recovers pressure from the impeller discharge; return vanes guide water to the next impeller eye.', 'Cast or forged ring with diffuser vanes, diaphragm and return channel; metal-to-metal fits with O-rings.',
                       'Chrome steel (13 % Cr), carbon steel, stainless.', 'Pressure rises stage by stage; thermal transients must be limited (warm-up).', ['Erosion at diffuser tips', 'Interstage leakage'], ['Clearances at overhaul']),
        'bfp_suction': C('Receives feedwater from the deaerator/booster and feeds the first-stage impeller.', 'Casting with suction nozzle, foot and first-stage eye passage.', 'Carbon steel/chrome steel.',
                         'Hot, near-saturated water — low NPSHa.', ['Cavitation erosion at first stage'], ['First-stage impeller inspection']),
        'bfp_discharge': C('Collects flow from the last stage, carries the discharge nozzle and the balance drum chamber.', 'Heavy casting/forging.', 'Carbon/chrome steel.', 'Full discharge pressure.',
                           ['Erosion', 'Joint leakage'], ['Joint inspection']),
        'bfp_balance': C('Throttling bush around the balance drum; leak-off returns to suction to balance thrust.', 'Close-clearance bushing.', 'Bronze/hardened stainless.', 'Wear increases leak-off flow.',
                         ['Wear → higher leak-off and thrust'], ['Monitor balance leak-off flow']),
        'bfp_leakoff': C('Returns the controlled leakage past the balance drum from the balance chamber to the suction, keeping that chamber near suction pressure so the drum produces its balancing force.',
                         'Small-bore pipe from the discharge-end balance chamber to the suction casing (often with a flow indicator or orifice).', 'Stainless or carbon steel tube.',
                         'Leak-off flow rises as drum/bush clearance wears; rising flow or temperature is an early warning.', ['Blockage (thrust bearing overload)', 'Excess flow from worn bush'], ['Monitor leak-off flow and temperature']),
        'bfp_tiebolts': C('Clamp the stage stack between suction and discharge casings.', 'High-strength studs and nuts, hydraulically tensioned.', 'Alloy steel.', 'Preload must exceed hydraulic separating force.',
                          ['Loss of preload', 'Thermal relaxation'], ['Tension check per manufacturer']),
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
