"""Valves & Piping — EQ-132 … EQ-140 (pipe spool, manifold, orifice plate, flow nozzle, venturi tube, pig launcher, pig receiver,
pipe insulation system, pipe tracing system)."""
import math
from mathutils import Vector, Matrix
from pumpforge.core import Model, lathe, cyl, box, csg, split, join, split_many, rotate, transform, hex_prism, TAU, OPERATE_FRAMES
from pumpforge.valvekit import (P, flange, bolts_x, gasket, handwheel, spring, sphere, keys_loop, smooth_pulse, shape_key, morph_loop, tap, dp_transmitter)
from pumpforge.parts import pressure_gauge, add_tracers, hollow_pipe, gate_valve
from pumpforge.shapes import sweep_tube
from pumpforge.common_meta import C
from pumps._eq_valves_a import _std

CAT = '6 · Valves & Piping'


def weld_bead(name, x, r, cz, axis='X', center=None):
    c = center or (0, 0, cz)
    return lathe(name, [(r, -0.004), (r + 0.004, -0.002), (r + 0.005, 0.0), (r + 0.004, 0.002), (r, 0.004)], 'steel_dark', 48, axis=axis,
                 center=(c[0] + (x if axis == 'X' else 0), c[1], c[2] + (x if axis == 'Z' else 0)))


def ball_valve(name, center, r, axis='X', handle_angle=0.0):
    cx, cy, cz = center
    objs = [cyl(name + 'b', r * 1.6, -r * 1.6, r * 1.6, 'stainless', 48, axis=axis, center=center, ch=0.003),
            sphere(name + 's', center, r * 1.9, 'stainless', 32), cyl(name + 'st', r * 0.3, cz + r * 1.8, cz + r * 2.6, 'stainless', 16, center=(cx, cy, 0))]
    return join(name, objs)


# =============================================================== EQ-132 Pipe spool
def pipe_spool(out):
    m = Model('pipe_spool', 'Pipe Spool (Prefabricated, Flanged, with Elbow, Tee & Reducer)', CAT, META['pipe_spool'])
    CZ, R, T = 0.4, 0.05, 0.006
    rf = 0.13
    pipe1 = hollow_pipe('s1', [(-0.6, 0, CZ), (0.25, 0, CZ), (0.25, 0, CZ + 0.55)], R, 'paint_grey', 48, bend=0.15, t=T)
    tee = hollow_pipe('tb', [(-0.15, 0, CZ), (-0.15, -0.35, CZ)], R * 0.7, 'paint_grey', 40, t=T)
    red = lathe('red', [(R * 0.7, 0.0), (R * 0.7 + T, 0.0), (R + T, 0.09), (R, 0.09)], 'paint_grey', 48, axis='Y', center=(-0.15, -0.44, CZ))
    welds = [weld_bead('w1', -0.42, R + T, CZ), weld_bead('w2', 0.0, R + T, CZ), lathe('w3', [(R + T, -0.004), (R + T + 0.005, 0), (R + T, 0.004)], 'steel_dark', 48, center=(0.25, 0, CZ + 0.42)),
             lathe('w4', [(R * 0.7 + T, -0.004), (R * 0.7 + T + 0.005, 0), (R * 0.7 + T, 0.004)], 'steel_dark', 48, axis='Y', center=(-0.15, -0.35, CZ))]
    P(m, 'spool_pipe', 'Spool Pipe, Long-Radius Elbow & Butt Welds', 'piping', [pipe1] + welds, explode=(0, 0.3, 0), ref='ps_pipe')
    P(m, 'tee_reducer', 'Branch Tee & Concentric Reducer', 'piping', [tee, red], explode=(0, -0.35, 0), ref='ps_tee')
    fls = [flange('fa', -0.6, R, CZ, rf, 0.025, 'paint_grey', +1),
           cyl('fb', rf, CZ + 0.55, CZ + 0.575, 'paint_grey', 64, r_in=R, center=(0.25, 0, 0)),
           cyl('fbh', R * 1.35 + 0.006, CZ + 0.5, CZ + 0.55, 'paint_grey', 48, r_in=R, center=(0.25, 0, 0)),
           cyl('fc', 0.11, -0.555, -0.53, 'paint_grey', 64, axis='Y', center=(-0.15, 0, CZ), r_in=R)]
    P(m, 'flanges', 'Weld-Neck Flanges (3 off)', 'piping', fls, explode=(-0.3, 0, 0.3), ref='ps_flanges')
    mate = [hollow_pipe('mp', [(-1.0, 0, CZ), (-0.65, 0, CZ)], R, 'paint_blue', 48, t=T), cyl('mf', rf, -0.65, -0.627, 'paint_blue', 64, axis='X', center=(0, 0, CZ), r_in=R),
            gasket('g1', -0.6135, R + 0.004, R + 0.045, CZ, 0.004), bolts_x('bt', -0.613, rf, CZ, 8, 0.07)]
    P(m, 'mating_joint', 'Mating Flange, Gasket & Bolting (field joint)', 'piping', mate, explode=(-0.4, 0, 0), ref='ps_joint')
    tag = box('tag', (0.12, 0.004, 0.05), (-0.25, -R - T - 0.003, CZ + 0.02), 'nameplate', bevel=0.002)
    P(m, 'spool_tag', 'Spool Identification Tag (line no., spool no., weld IDs)', 'piping', [tag], explode=(0, -0.2, 0.2), ref='ps_tag', section='keep')
    m.flow('main', [(-1.0, 0, CZ), (0.1, 0, CZ), (0.25, 0, CZ + 0.15), (0.25, 0, CZ + 0.6)], 'flow_suction', 0.01, 0.2)
    m.flow('branch', [(-1.0, 0.01, CZ), (-0.15, 0.0, CZ), (-0.15, -0.6, CZ)], 'flow_suction', 0.008, 0.2, speed=[1, 1, 1.6])
    return m.export(out)


# =============================================================== EQ-133 Pipe manifold
def pipe_manifold(out):
    m = Model('pipe_manifold', 'Pipe Manifold (Distribution Header with Valved Branches)', CAT, META['pipe_manifold'])
    CZ, R, T = 0.5, 0.06, 0.007
    hdr = [hollow_pipe('h', [(-0.7, 0, CZ), (0.62, 0, CZ)], R, 'paint_blue', 48, t=T), cyl('cap', R + T, 0.62, 0.66, 'paint_blue', 48, axis='X', center=(0, 0, CZ)),
           flange('fin', -0.7, R, CZ, 0.15, 0.025, 'paint_blue', -1)]
    xs = [-0.4, -0.12, 0.16, 0.44]
    br = []
    for i, x in enumerate(xs):
        br += [hollow_pipe(f'b{i}', [(x, 0, CZ), (x, 0, CZ + 0.42)], 0.025, 'paint_blue', 32, t=0.004), weld_bead(f'bw{i}', CZ + R + 0.006, 0.029, 0.0, 'Z', (x, 0, 0))]
    sup = [box(f'sp{i}', (0.06, 0.2, CZ - R - 0.006), (x, 0, (CZ - R - 0.006) / 2), 'steel_dark') for i, x in enumerate((-0.5, 0.5))]
    sup += [lathe(f'sd{i}', [(R + T, -0.03), (R + T + 0.01, -0.03), (R + T + 0.01, 0.03), (R + T, 0.03)], 'steel_dark', 32, a0=math.pi, a1=TAU, axis='X', center=(x, 0, CZ), cap_mat='steel_dark')
            for i, x in enumerate((-0.5, 0.5))]
    P(m, 'header', 'Header Pipe, Branch Outlets & Supports', 'piping', hdr + br + sup, explode=(0, 0, -0.3), ref='pm_header')
    vb = [ball_valve(f'v{i}', (x, 0, CZ + 0.25), 0.025, 'Z') for i, x in enumerate(xs)]
    P(m, 'branch_valves', 'Branch Isolation Valves (ball, quarter-turn)', 'valves', vb, explode=(0, -0.35, 0.1), ref='pm_valves')
    opens = [(0.0, 0.9), (0.15, 0.9), (0.3, 0.9), (0.45, 0.9)]
    for i, (x, (t0, t1)) in enumerate(zip(xs, opens)):
        lev = join(f'lv{i}', [box(f'lb{i}', (0.012, 0.16, 0.01), (x, -0.07, CZ + 0.31), 'paint_red', bevel=0.002)])
        pl = P(m, f'lever_{i + 1}', f'Valve Lever – Branch {i + 1}', 'actuator', lev, explode=(0, -0.45, 0.3), ref='pm_lever', section='keep', pivot=(x, 0, CZ + 0.31))
        keys_loop(m, pl, lambda t, t0=t0, t1=t1: (0, 0, -math.pi / 2 * (1 - (min(1, max(0, (t - t0) / 0.08)) if t < t1 else max(0, 1 - (t - t1) / 0.05)))), 'rotation_euler')
        m.flow(f'branch_{i + 1}', [(-0.7, 0, CZ - 0.02 + 0.01 * i), (x, 0, CZ), (x, 0, CZ + 0.55)], 'flow_suction', 0.006, 0.12, active=[(t0 + 0.06, t1)])
    g = [pressure_gauge('pg', (0.62, 0.0, CZ + R + T))]
    dv = [cyl('dr', 0.012, CZ - R - 0.1, CZ - R, 'stainless', 16, center=(0.58, 0, 0)), ball_valve('drv', (0.58, 0, CZ - R - 0.06), 0.012, 'Z')]
    P(m, 'gauge_drain', 'Header Pressure Gauge & Drain Valve', 'instrumentation', g + dv, explode=(0.3, 0, 0), ref='pm_instruments', section='keep')
    m.flow('header', [(-1.0, 0, CZ), (-0.7, 0, CZ), (0.55, 0, CZ)], 'flow_suction', 0.01, 0.2)
    return m.export(out)


def _meter_line(m, CZ, R, T, x0, x1, xl=0.7, mat='paint_grey', label='Meter Run (upstream & downstream straight pipe)'):
    objs = [hollow_pipe('ul', [(-xl, 0, CZ), (x0, 0, CZ)], R, mat, 48, t=T), hollow_pipe('dl', [(x1, 0, CZ), (xl, 0, CZ)], R, mat, 48, t=T)]
    return P(m, 'meter_run', label, 'system_piping', objs, explode=(0, 0.35, 0), ref='fm_run')


def _pressure_profile(m, CZ, R, T, profile, title, desc):
    """Pressure overlay: rings along the pipe coloured by static pressure (0..9 index)."""
    rings = []
    for i, (x0, x1, lev) in enumerate(profile):
        rings.append(cyl(f'pp{i}', R + T + 0.008, x0, x1, f'pressure_{lev}', 48, axis='X', center=(0, 0, CZ), r_in=R + T + 0.002))
    m.overlay('pressure', join('prof', rings), title, desc, split=True)


def _dp_set(m, CZ, R, T, xa, xb, pid='dp_transmitter', name='DP Transmitter, Impulse Lines & 3-Valve Manifold'):
    hi = sweep_tube('ih', [(xa, 0, CZ + R + T + 0.06), (xa, 0, CZ + 0.3), (-0.03, -0.0, CZ + 0.3), (-0.03, 0, CZ + 0.33)], 0.005, 'stainless', 8)
    lo = sweep_tube('il', [(xb, 0, CZ + R + T + 0.06), (xb, 0, CZ + 0.3), (0.03, 0, CZ + 0.3), (0.03, 0, CZ + 0.33)], 0.005, 'stainless', 8)
    man = box('man', (0.1, 0.035, 0.03), (0, 0, CZ + 0.345), 'stainless', bevel=0.003)
    tx = dp_transmitter('dpt', (0, 0, CZ + 0.39))
    return P(m, pid, name, 'instrumentation', [tap('ta', xa, CZ, R + T), tap('tb', xb, CZ, R + T), hi, lo, man, tx], explode=(0, -0.3, 0.3), ref='fm_dp', section='keep')


# =============================================================== EQ-134 Orifice plate
def orifice_plate(out):
    m = Model('orifice_plate', 'Orifice Plate Flowmeter (Concentric, Flange Taps)', CAT, META['orifice_plate'])
    CZ, R, T, beta = 0.35, 0.05, 0.006, 0.6
    d = beta * R
    fl = [cyl('of1', 0.13, -0.045, -0.006, 'paint_grey', 64, axis='X', center=(0, 0, CZ), r_in=R, ch=0.003), cyl('of2', 0.13, 0.006, 0.045, 'paint_grey', 64, axis='X', center=(0, 0, CZ), r_in=R, ch=0.003),
          bolts_x('ob', 0.0, 0.13, CZ, 8, 0.11), gasket('og1', -0.004, R + 0.002, R + 0.04, CZ), gasket('og2', 0.004, R + 0.002, R + 0.04, CZ)]
    P(m, 'orifice_flanges', 'Orifice Flanges with Tap Holes, Gaskets & Bolting', 'body', fl, explode=(0, 0, -0.3), ref='op_flanges')
    plate = csg('plate', [cyl('pl', R + 0.04, -0.0015, 0.0015, 'stainless', 64, axis='X', center=(0, 0, CZ)), box('tab', (0.003, 0.03, 0.08), (0, 0, CZ + R + 0.07), 'stainless')],
                [lathe('bore', [(0, -0.003), (d, -0.003), (d, 0.0005), (d + 0.0015, 0.003), (0, 0.003)], 'stainless', 64, axis='X', center=(0, 0, CZ))], 'stainless')
    P(m, 'plate', 'Orifice Plate (sharp square edge, β = d/D ≈ 0.6) with Handle Tab', 'element', plate, explode=(0, 0, 0.35), ref='op_plate')
    _meter_line(m, CZ, R, T, -0.045, 0.045)
    _dp_set(m, CZ, R, T, -0.025, 0.025)
    m.flow('flow', [(-0.7, 0, CZ), (-0.05, 0, CZ), (-0.004, 0, CZ), (0.03, 0, CZ), (0.12, 0, CZ), (0.4, 0, CZ), (0.7, 0, CZ)], 'flow_suction', 0.012, 0.25,
           speed=[1, 1, 2.8, 3.0, 2.0, 1.1, 1])
    m.flow('jet_edge', [(-0.2, 0, CZ + 0.04), (-0.01, 0, CZ + 0.031), (0.03, 0, CZ + 0.023), (0.15, 0, CZ + 0.035), (0.5, 0, CZ + 0.045)], 'flow_suction', 0.004, 0.2,
           speed=[1, 2.8, 3.1, 2.0, 1.1])
    _pressure_profile(m, CZ, R, T, [(-0.7, -0.05, 8), (-0.05, -0.005, 9), (0.005, 0.08, 1), (0.08, 0.2, 3), (0.2, 0.4, 5), (0.4, 0.7, 6)], 'Pressure profile',
                      'Static pressure is highest just upstream of the plate, lowest at the vena contracta just downstream (where the jet is narrowest and fastest), '
                      'then partly recovers. The unrecovered part is the permanent pressure loss (relatively high for orifice plates). Flow ∝ √ΔP (ISO 5167-2).')
    m.annotate('pressure', 'p1 (upstream tap)', (-0.1, 0, CZ + 0.15))
    m.annotate('pressure', 'p2 at vena contracta — lowest', (0.05, 0, CZ - 0.15))
    m.annotate('pressure', 'Permanent pressure loss', (0.6, 0, CZ + 0.15))
    return m.export(out)


# =============================================================== EQ-135 Flow nozzle
def flow_nozzle(out):
    m = Model('flow_nozzle', 'Flow Nozzle (ISA 1932 type) between Flanges', CAT, META['flow_nozzle'])
    CZ, R, T, beta = 0.35, 0.05, 0.006, 0.6
    d = beta * R
    fl = [cyl('nf1', 0.13, -0.06, -0.006, 'paint_grey', 64, axis='X', center=(0, 0, CZ), r_in=R, ch=0.003), cyl('nf2', 0.13, 0.006, 0.07, 'paint_grey', 64, axis='X', center=(0, 0, CZ), r_in=R, ch=0.003),
          bolts_x('nb', 0.0, 0.13, CZ, 8, 0.13)]
    P(m, 'carrier_flanges', 'Carrier Flanges & Bolting', 'body', fl, explode=(0, 0, -0.3), ref='fn_flanges')
    prof = [(R + 0.03, -0.004), (R + 0.03, 0.004), (R, 0.004)]
    for k in range(9):
        a = math.pi / 2 * k / 8
        prof.append((d + (R - d) * (1 - math.sin(a)) * 0.98 + 0.002, 0.004 + 0.035 * (1 - math.cos(a))))
    prof += [(d + 0.002, 0.06), (d, 0.06), (d, 0.04)]
    for k in range(8, -1, -1):
        a = math.pi / 2 * k / 8
        prof.append((d + (R - d) * (1 - math.sin(a)) * 0.98 - 0.002 if k < 8 else R - 0.004, 0.002 + 0.035 * (1 - math.cos(a))))
    noz = lathe('noz', [(R + 0.03, -0.004), (R + 0.03, 0.004), (R - 0.002, 0.004), (R - 0.005, 0.012), (d + 0.012, 0.03), (d + 0.004, 0.04), (d + 0.004, 0.065), (d, 0.065),
                        (d, 0.04), (d + 0.008, 0.03), (R - 0.012, 0.012), (R - 0.008, -0.004)], 'stainless', 64, axis='X', center=(0, 0, CZ))
    P(m, 'nozzle', 'Flow Nozzle (curved inlet, cylindrical throat)', 'element', noz, explode=(0, 0, 0.35), ref='fn_nozzle')
    _meter_line(m, CZ, R, T, -0.06, 0.07)
    _dp_set(m, CZ, R, T, -0.12, 0.035)
    m.flow('flow', [(-0.7, 0, CZ), (-0.02, 0, CZ), (0.03, 0, CZ), (0.07, 0, CZ), (0.25, 0, CZ), (0.7, 0, CZ)], 'flow_suction', 0.012, 0.25, speed=[1, 1.3, 2.6, 2.8, 1.4, 1])
    _pressure_profile(m, CZ, R, T, [(-0.7, -0.06, 8), (-0.06, 0.02, 7), (0.02, 0.1, 1), (0.1, 0.3, 4), (0.3, 0.7, 5)], 'Pressure profile',
                      'The smooth curved inlet accelerates the flow with little loss; pressure is lowest in the throat. Recovery downstream is limited (no diffuser), '
                      'so permanent loss lies between an orifice and a venturi. Flow nozzles suit high-velocity steam and erosive flows (ISO 5167-3).')
    m.annotate('pressure', 'Throat: highest velocity, lowest pressure', (0.05, 0, CZ - 0.15))
    return m.export(out)


# =============================================================== EQ-136 Venturi tube
def venturi_tube(out):
    m = Model('venturi_tube', 'Venturi Tube (Classical, Machined Convergent)', CAT, META['venturi_tube'])
    CZ, R, T, beta = 0.35, 0.06, 0.008, 0.55
    d = beta * R
    xi0, xc0, xt0, xt1, xd1 = -0.32, -0.2, -0.08, 0.0, 0.42
    outer = [(R + T + 0.004, xi0), (R + T + 0.004, xc0), (d + T + 0.006, xt0), (d + T + 0.006, xt1), (R + T + 0.004, xd1)]
    inner = [(R, xd1), (d, xt1), (d, xt0), (R, xc0), (R, xi0)]
    v = lathe('vt', outer + inner, 'paint_blue', 96, axis='X', center=(0, 0, CZ))
    fl = [cyl('vf1', 0.15, xi0 - 0.025, xi0, 'paint_blue', 64, axis='X', center=(0, 0, CZ), r_in=R, ch=0.003), cyl('vf2', 0.15, xd1, xd1 + 0.025, 'paint_blue', 64, axis='X', center=(0, 0, CZ), r_in=R, ch=0.003)]
    pr = [lathe(f'pr{i}', [(r - 0.001, x - 0.012), (r + T + 0.02, x - 0.012), (r + T + 0.02, x + 0.012), (r - 0.001, x + 0.012)], 'paint_blue', 48, axis='X', center=(0, 0, CZ))
          for i, (x, r) in enumerate(((xi0 + 0.05, R), ((xt0 + xt1) / 2, d)))]
    P(m, 'venturi', 'Venturi Body: Inlet Cylinder, Convergent Cone, Throat & Divergent Diffuser (with piezometer rings)', 'element', [v] + fl + pr, explode=(0, 0, -0.35), ref='vt_body')
    _meter_line(m, CZ, R, T, xi0 - 0.025, xd1 + 0.025, 0.8)
    hi = sweep_tube('ih', [(xi0 + 0.05, 0, CZ + R + T + 0.02), (xi0 + 0.05, 0, CZ + 0.3), (-0.03, 0, CZ + 0.3), (-0.03, 0, CZ + 0.33)], 0.005, 'stainless', 8)
    lo = sweep_tube('il', [(-0.04, 0, CZ + d + T + 0.02), (-0.04, 0, CZ + 0.29), (0.03, 0, CZ + 0.29), (0.03, 0, CZ + 0.33)], 0.005, 'stainless', 8)
    P(m, 'dp_transmitter', 'DP Transmitter & Impulse Lines (inlet and throat taps)', 'instrumentation',
      [hi, lo, box('man', (0.1, 0.035, 0.03), (0, 0, CZ + 0.345), 'stainless', bevel=0.003), dp_transmitter('dpt', (0, 0, CZ + 0.39))], explode=(0, -0.3, 0.3), ref='fm_dp', section='keep')
    m.flow('flow', [(-0.8, 0, CZ), (xc0, 0, CZ), (xt0, 0, CZ), (xt1, 0, CZ), (xd1, 0, CZ), (0.8, 0, CZ)], 'flow_suction', 0.012, 0.25, speed=[1, 1, 3.3, 3.3, 1, 1])
    m.flow('edge', [(-0.8, 0, CZ + 0.04), (xc0, 0, CZ + 0.04), (xt0, 0, CZ + 0.022), (xt1, 0, CZ + 0.022), (xd1, 0, CZ + 0.04), (0.8, 0, CZ + 0.04)], 'flow_suction', 0.004, 0.25,
           speed=[1, 1, 3.3, 3.3, 1, 1])
    _pressure_profile(m, CZ, R, T, [(-0.8, xc0, 8), (xc0, xt0, 6), (xt0, xt1, 1), (xt1, 0.12, 3), (0.12, 0.28, 5), (0.28, 0.8, 7)], 'Pressure profile (Bernoulli)',
                      'In the convergent cone velocity rises and static pressure falls (Bernoulli), reaching a minimum in the throat. The gentle divergent cone '
                      'recovers most of the pressure, so the permanent loss is only about 5–20 % of the measured ΔP — the lowest of the differential-pressure meters (ISO 5167-4).')
    m.annotate('pressure', 'Inlet tap p1', (xi0 + 0.05, 0, CZ + 0.2))
    m.annotate('pressure', 'Throat tap p2 — lowest pressure', (-0.04, 0, CZ - 0.15))
    m.annotate('pressure', 'Diffuser recovers most pressure', (0.3, 0, CZ + 0.17))
    return m.export(out)


# =============================================================== EQ-137 / 138 Pig launcher & receiver
def _pig_trap(out, pid, title, meta, launcher=True):
    m = Model(pid, title, CAT, meta)
    CZ, R, RB, T = 0.6, 0.075, 0.12, 0.01
    s = 1 if launcher else -1               # launcher: barrel at -X, pipeline leaves to +X; receiver mirrored (pipeline arrives from -X)
    xd, xr0 = -1.1 * s, -0.15 * s
    xr1 = 0.05 * s
    red = (lathe('red', [(RB, 0.0), (RB + T, 0.0), (R + T, 0.2), (R, 0.2)], 'paint_yellow', 64, axis='X', center=(xr0, 0, CZ)) if launcher else
           lathe('red', [(R, 0.0), (R + T, 0.0), (RB + T, 0.2), (RB, 0.2)], 'paint_yellow', 64, axis='X', center=(xr1, 0, CZ)))
    hub = cyl('hub', RB + T + 0.025, min(xd, xd - 0.05 * s), max(xd, xd - 0.05 * s), 'paint_yellow', 64, axis='X', center=(0, 0, CZ), r_in=RB)
    bar = [hollow_pipe('brl', [(xd, 0, CZ), (xr0, 0, CZ)], RB, 'paint_yellow', 64, t=T), red, hub]
    sad = [box(f'sd{i}', (0.08, 0.3, CZ - RB - T), (x, 0, (CZ - RB - T) / 2), 'steel_dark') for i, x in enumerate((xd + 0.2 * s, xr0 - 0.15 * s))]
    nozz = [cyl('vent', 0.012, CZ + RB, CZ + RB + 0.12, 'steel', 16, center=(xd + 0.15 * s, 0, 0)), cyl('drn', 0.015, CZ - RB - 0.12, CZ - RB, 'steel', 16, center=(xd + 0.3 * s, 0, 0)),
            cyl('psi', 0.008, CZ + RB, CZ + RB + 0.06, 'brass', 12, center=(xr0 - 0.3 * s, 0, 0))]
    P(m, 'barrel', 'Oversize Barrel (Major Barrel), Reducer, Saddles, Vent & Drain', 'vessel', bar + sad + nozz, explode=(0, 0, -0.35), ref='pig_barrel')
    xa, xb = sorted((xd - 0.05 * s, xd - 0.075 * s))
    door = join('door', [cyl('dr', RB + T + 0.03, xa, xb, 'paint_grey', 64, axis='X', center=(0, 0, CZ), ch=0.005),
                         box('hng', (0.05, 0.03, 0.08), (xd - 0.06 * s, RB + 0.05, CZ), 'steel_dark'),
                         cyl('lk', 0.02, -0.03, 0.03, 'steel_dark', 16, axis='Y', center=(xd - 0.06 * s, -RB - 0.05, CZ)),
                         box('dav', (0.03, 0.03, 0.35), (xd - 0.06 * s, RB + 0.05, CZ + 0.2), 'steel_dark')])
    P(m, 'closure', 'Quick-Opening Closure Door (with safety pressure-warning lock)', 'closure', door, explode=(-0.4 * s, 0, 0), ref='pig_closure')
    kx = xd + 0.35 * s
    ZK = CZ + RB + 0.35
    line = [hollow_pipe('ml', [(xr1, 0, CZ), (1.4 * s, 0, CZ)], R, 'paint_grey', 48, t=T)]
    if launcher:
        kick = [hollow_pipe('kk', [(kx, 0, CZ + RB), (kx, 0, ZK), (0.7, 0, ZK), (0.7, 0, CZ + R)], 0.035, 'paint_grey', 32, bend=0.08, t=0.006),
                hollow_pipe('sup', [(0.7, 0, ZK), (0.7, 0, ZK + 0.45)], 0.035, 'paint_grey', 32, t=0.006)]
        vals = [gate_valve('trap_v', (0.3, 0, CZ), R, 'X'), gate_valve('kick_v', (0.1, 0, ZK), 0.035, 'X'), gate_valve('main_v', (0.7, 0, CZ + RB + 0.12), 0.035, 'Z')]
        vname = 'Trap Valve, Kicker Valve & Mainline (bypass) Valve'
    else:
        kick = [hollow_pipe('kk', [(kx, 0, CZ + RB), (kx, 0, ZK), (kx, -0.7, ZK)], 0.035, 'paint_grey', 32, bend=0.08, t=0.006)]
        vals = [gate_valve('trap_v', (-0.3, 0, CZ), R, 'X'), gate_valve('kick_v', (kx, -0.35, ZK), 0.035, 'Y')]
        vname = 'Trap Valve & Outlet (to station) Valve'
    P(m, 'pipeline_kicker', 'Pipeline Tie-in and Kicker / Outlet Line', 'system_piping', line + kick, explode=(0, 0.4, 0), ref='pig_lines')
    P(m, 'valves', vname, 'valves', vals, explode=(0, -0.4, 0.2), ref='pig_valves', section='keep')
    sig = join('sig', [cyl('sg', 0.02, CZ + R + T, CZ + R + T + 0.08, 'paint_red', 16, center=(1.15 * s, 0, 0)), box('flag', (0.004, 0.05, 0.03), (1.15 * s, 0.02, CZ + R + T + 0.07), 'paint_yellow')])
    P(m, 'pig_signaller', 'Pig Passage Indicator (Signaller)', 'instrumentation', sig, explode=(0, 0, 0.3), ref='pig_signaller', section='keep')
    pig = join('pig', [cyl('pb', R - 0.006, -0.12, 0.12, 'steel_dark', 32, axis='X')] +
               [cyl(f'cp{k}', R + 0.002, x - 0.008, x + 0.008, 'foam', 48, axis='X') for k, x in enumerate((-0.1, -0.03, 0.04, 0.11))])
    transform(pig, Matrix.Translation((0, 0, CZ)))
    x_start, x_end = (xd + 0.25, 1.28) if launcher else (-1.28, xd - 0.25)
    pp = P(m, 'pig', 'Cleaning Pig (cup/disc type) — moves with the flow', 'pig', pig, explode=(0, -0.6, 0), ref='pig_pig', section='keep')
    keys_loop(m, pp, lambda t: ((x_start + (x_end - x_start) * min(1.0, (t / 0.75) ** 1.3)) if t < 0.95 else x_start, 0, 0))
    if launcher:
        m.flow('kicker_flow', [(0.7, 0, ZK + 0.45), (0.7, 0, ZK), (kx, 0, ZK), (kx, 0, CZ), (1.4, 0, CZ)], 'flow_suction', 0.008, 0.2, active=[(0.0, 0.8)])
        m.flow('bypass_flow', [(0.7, 0.01, ZK + 0.45), (0.7, 0.01, CZ), (1.4, 0.01, CZ)], 'flow_suction', 0.008, 0.2, active=[(0.8, 1.0)])
    else:
        m.flow('arrival_flow', [(-1.4, 0, CZ), (kx, 0, CZ), (kx, 0, ZK), (kx, -0.7, ZK)], 'flow_suction', 0.008, 0.2)
    return m.export(out)


def pig_launcher(out):
    return _pig_trap(out, 'pig_launcher', 'Pig Launcher (Pipeline Pig Trap — Launching)', META['pig_launcher'], True)


def pig_receiver(out):
    return _pig_trap(out, 'pig_receiver', 'Pig Receiver (Pipeline Pig Trap — Receiving)', META['pig_receiver'], False)


# =============================================================== EQ-139 Pipe insulation system
def pipe_insulation_system(out):
    m = Model('pipe_insulation_system', 'Pipe Insulation System (Hot Service, Layered Cutaway)', CAT, META['pipe_insulation_system'])
    CZ, R, T = 0.4, 0.06, 0.007
    P(m, 'process_pipe', 'Process Pipe', 'piping', [hollow_pipe('pp', [(-0.9, 0, CZ), (0.9, 0, CZ)], R, 'steel', 48, t=T)], explode=(0, 0, -0.4), ref='pi_pipe')
    P(m, 'coating', 'Anti-Corrosion Coating (CUI protection)', 'insulation', [cyl('ct', R + T + 0.002, -0.75, 0.9, 'coating', 64, axis='X', center=(0, 0, CZ), r_in=R + T)],
      explode=(0, 0, -0.2), ref='pi_coating')
    ins = [cyl('i1', R + T + 0.002 + 0.05, -0.55, 0.9, 'insulation', 64, axis='X', center=(0, 0, CZ), r_in=R + T + 0.002),
           cyl('i2', R + T + 0.002 + 0.1, -0.35, 0.9, 'insulation', 64, axis='X', center=(0, 0, CZ), r_in=R + T + 0.052)]
    P(m, 'insulation', 'Insulation Layers (2 × 50 mm, staggered joints)', 'insulation', ins, explode=(0, 0, 0.25), ref='pi_insulation')
    rc = R + T + 0.102
    clad = [cyl('cl', rc + 0.0015, -0.15, 0.9, 'cladding', 64, axis='X', center=(0, 0, CZ), r_in=rc)]
    for x in (0.0, 0.3, 0.6):
        clad.append(cyl(f'bd{x}', rc + 0.004, x - 0.01, x + 0.01, 'stainless', 64, axis='X', center=(0, 0, CZ), r_in=rc + 0.0015))
    P(m, 'cladding', 'Metal Cladding (weatherproof jacket) & Banding', 'insulation', clad, explode=(0, 0, 0.5), ref='pi_cladding')
    sup = [box('sh', (0.25, 0.3, 0.02), (0.75, 0, CZ - rc - 0.03), 'steel_dark'), lathe('sd', [(rc + 0.002, -0.1), (rc + 0.012, -0.1), (rc + 0.012, 0.1), (rc + 0.002, 0.1)], 'steel_dark', 48,
                                                                                               a0=math.pi, a1=TAU, axis='X', center=(0.75, 0, CZ), cap_mat='steel_dark'),
           box('blk', (0.2, 0.2, CZ - rc - 0.04), (0.75, 0, (CZ - rc - 0.04) / 2), 'steel_dark')]
    P(m, 'support', 'Insulated Pipe Support (shoe & cradle)', 'support', sup, explode=(0, 0, -0.5), ref='pi_support')
    m.flow('hot', [(-0.9, 0, CZ), (0.9, 0, CZ)], 'flow_discharge', 0.012, 0.25)
    arrows = []
    from pumpforge.shapes import cone_arrow
    for i, a in enumerate([0, 1.57, 3.14, 4.71]):
        for x, L in ((-0.8, 0.22), (0.45, 0.07)):
            y0, z0 = (R + T + 0.004) * math.cos(a), CZ + (R + T + 0.004) * math.sin(a)
            y1, z1 = (R + T + L) * math.cos(a), CZ + (R + T + L) * math.sin(a)
            arrows += [sweep_tube(f'ha{i}{x}', [(x, y0, z0), (x, y1, z1)], 0.004 if L > 0.1 else 0.0025, 'heat', 8),
                       cone_arrow(f'hc{i}{x}', Vector((x, y1, z1)), Vector((0, math.cos(a), math.sin(a))), 0.02, 0.01 if L > 0.1 else 0.006, 'heat')]
    m.overlay('heat_loss', join('hl', arrows), 'Heat loss', 'Bare pipe (left) loses heat strongly by convection and radiation; under the insulation (right) the heat '
              'flow is a fraction of that. Heat loss per metre ≈ 2πk(T_pipe − T_surface)/ln(r_out/r_in). Insulation also keeps the surface below '
              'touch-safe temperature (personnel protection, typically ≤ 60 °C — verify local regulations).', split=True)
    m.annotate('heat_loss', 'Bare pipe: high heat loss', (-0.8, 0, CZ + 0.3))
    m.annotate('heat_loss', 'Insulated: small heat loss', (0.45, 0, CZ + 0.3))
    return m.export(out)


# =============================================================== EQ-140 Pipe tracing system
def pipe_tracing_system(out):
    m = Model('pipe_tracing_system', 'Pipe Tracing System (Steam Tracing & Electric Heat Tracing)', CAT, META['pipe_tracing_system'])
    CZ, R, T = 0.4, 0.05, 0.006
    P(m, 'process_pipe', 'Process Pipe (product kept warm)', 'piping', [hollow_pipe('pp', [(-1.0, 0, CZ), (1.0, 0, CZ)], R, 'steel', 48, t=T)], explode=(0, 0, -0.4), ref='pt_pipe')
    rt = R + T + 0.009
    a_bot = -math.pi / 2 + 0.6
    ty, tz = rt * math.cos(a_bot), CZ + rt * math.sin(a_bot)
    tr = [hollow_pipe('tr', [(-0.95, ty, tz), (-0.05, ty, tz)], 0.008, 'copper', 16, t=0.0015),
          hollow_pipe('ts', [(-0.95, ty, tz), (-0.95, ty, tz - 0.25)], 0.008, 'copper', 16, t=0.0015)]
    cem = [cyl('hc', 0.0, -0.9, -0.05, 'steel_dark', 4)] if False else []
    P(m, 'steam_tracer', 'Steam Tracer Tube (with heat-transfer cement)', 'tracing', tr + cem, explode=(0, -0.3, -0.2), ref='pt_steam_tracer')
    trap = join('trap', [cyl('tb', 0.035, -0.12, 0.0, 'cast_iron', 32, axis='X', center=(0, ty, tz - 0.15)), sweep_tube('tl', [(-0.05, ty, tz), (-0.05, ty, tz - 0.15)], 0.008, 'copper', 12)])
    P(m, 'tracer_trap', 'Tracer Steam Trap (thermodynamic)', 'tracing', trap, explode=(0, -0.2, -0.3), ref='pt_trap')
    cab = []
    pts = []
    for k in range(161):
        t = k / 160
        x = 0.05 + 0.9 * t
        a = TAU * 6 * t
        pts.append((x, (R + T + 0.005) * math.cos(a), CZ + (R + T + 0.005) * math.sin(a)))
    cab.append(sweep_tube('cable', pts, 0.004, 'thermoplastic', 8))
    cab.append(box('jb', (0.1, 0.08, 0.1), (0.05, 0, CZ + R + T + 0.16), 'paint_grey', bevel=0.006))
    cab.append(cyl('st', 0.012, CZ + R + T, CZ + R + T + 0.11, 'paint_grey', 16, center=(0.05, 0, 0)))
    cab.append(box('ctrl', (0.06, 0.03, 0.08), (0.95, 0, CZ + R + T + 0.1), 'paint_grey', bevel=0.004))
    P(m, 'electric_tracer', 'Self-Regulating Heating Cable, Power Box & Thermostat', 'tracing', cab, explode=(0, 0, 0.35), ref='pt_electric')
    rc = R + T + 0.06
    P(m, 'insulation', 'Insulation over Pipe and Tracers (shown partly removed)', 'insulation',
      [cyl('ins', rc, -0.6, -0.3, 'insulation', 64, axis='X', center=(0, 0, CZ), r_in=R + T + 0.02), cyl('ins2', rc, 0.5, 0.75, 'insulation', 64, axis='X', center=(0, 0, CZ), r_in=R + T + 0.012),
       cyl('cl1', rc + 0.0015, -0.6, -0.3, 'cladding', 64, axis='X', center=(0, 0, CZ), r_in=rc), cyl('cl2', rc + 0.0015, 0.5, 0.75, 'cladding', 64, axis='X', center=(0, 0, CZ), r_in=rc)],
      explode=(0, 0, 0.6), ref='pi_insulation')
    m.flow('product', [(-1.0, 0, CZ), (1.0, 0, CZ)], 'flow_suction', 0.01, 0.25)
    m.flow('steam', [(-0.95, ty, tz - 0.25), (-0.95, ty, tz), (-0.05, ty, tz), (-0.05, ty, tz - 0.15)], 'steam', 0.004, 0.12)
    from pumpforge.shapes import cone_arrow
    arr = []
    for x in (-0.7, -0.4, -0.15):
        arr += [sweep_tube(f'hs{x}', [(x, ty * 0.9, tz + 0.006), (x, ty * 0.55, tz + 0.03)], 0.003, 'heat', 8)]
    for k in range(10):
        p0 = pts[8 + k * 15]
        d = Vector((0, -(p0[1]), -(p0[2] - CZ))).normalized()
        q = Vector(p0) + d * 0.02
        arr += [sweep_tube(f'he{k}', [p0, tuple(q)], 0.0025, 'heat', 8)]
    m.overlay('heat_input', join('hi', arr), 'Heat input', 'Tracers replace the heat the pipe loses through its insulation, keeping the product above its freezing, '
              'congealing or crystallisation temperature (e.g. caustic, heavy oil, sulphur, water lines in winter). Steam tracing: heat from condensing steam; '
              'electric: a self-regulating polymer cable whose output falls as the pipe warms.', split=True)
    m.annotate('heat_input', 'Steam tracer heats the pipe bottom', (-0.4, 0, CZ - 0.2))
    m.annotate('heat_input', 'Electric cable spiral wound', (0.5, 0, CZ + 0.2))
    return m.export(out)


META = {
    'pipe_spool': {
        'summary': ('A pipe spool is a prefabricated section of piping — pipe, fittings and flanges welded together in a shop — that is shipped to site and '
                    'bolted or welded into the line. Fabricating spools under shop conditions gives better weld quality, inspection and schedule control. '
                    'Each spool carries a tag with its line and spool number and weld identification for traceability.'),
        'classification': {'family': 'Piping component', 'type': 'Prefabricated flanged spool (elbow, tee branch, reducer)'},
        'model_configuration': {'joints': 'Butt welds (shop), flanged field joint with gasket and stud bolts', 'size': 'Fits within transport limits (typically ≤ 12 m × 3 m × 3 m — verify)'},
        'standards': _std(('ASME B31.3', 'Process Piping', 'Design, fabrication, examination and testing.'), ('ASME B16.5 / B16.9', 'Flanges / butt-welding fittings', 'Dimensions and ratings.'),
                          ('ISO 15614 / ASME IX', 'Welding procedure qualification', 'Weld quality.')),
        'references': ['Piping fabrication practice guides (isometrics, spool drawings)'],
        'components': {
            'ps_pipe': C('Carries the fluid; the spool body.', 'Seamless or welded pipe with long-radius elbow, butt welded.', 'Carbon steel, stainless, alloy steel.', 'Weld examination per code (RT/UT).',
                         ['Weld defects', 'Corrosion/erosion at elbows'], ['NDT records, thickness survey']),
            'ps_tee': C('Branches flow and changes size.', 'Butt-weld tee and concentric reducer.', 'As pipe.', 'Erosion at tee branch.', ['Erosion'], ['UT thickness']),
            'ps_flanges': C('Allow the spool to be bolted into the line.', 'Weld-neck flanges.', 'Forged steel.', 'Face finish and alignment matter for sealing.', ['Face damage'], ['Inspect faces before assembly']),
            'ps_joint': C('Field joint between spool and line.', 'Mating flange, spiral-wound/soft gasket and stud bolts.', 'Steel, graphite/PTFE gaskets.', 'Controlled tightening sequence (ASME PCC-1).',
                          ['Flange leakage'], ['Torque/tension records']),
            'ps_tag': C('Identifies the spool for installation and traceability.', 'Stamped or engraved tag.', 'Stainless.', '—', ['Lost tag'], ['Check against isometric']),
        },
    },
    'pipe_manifold': {
        'summary': ('A pipe manifold (header) collects or distributes flow among several branches from one large pipe. Each branch has its own isolation '
                    'valve so lines can be opened, closed or maintained independently — typical of cooling-water, steam, gas and chemical distribution.'),
        'classification': {'family': 'Piping component', 'type': 'Distribution header with valved branches'},
        'model_configuration': {'branches': 4, 'animation': 'Branch valves open in sequence; flow appears in each opened branch'},
        'standards': _std(('ASME B31.3', 'Process Piping', 'Header and branch reinforcement design.'),),
        'references': ['Piping design handbooks — headers and branch connections'],
        'components': {
            'pm_header': C('Carries the total flow and feeds the branches.', 'Large-bore header, branch outlets (weldolets/tees) and supports.', 'Carbon steel/stainless.',
                           'Header velocity kept low for even distribution.', ['Uneven distribution', 'Corrosion at dead ends'], ['Thickness survey']),
            'pm_valves': C('Isolate each branch.', 'Quarter-turn ball valves.', 'Stainless.', '—', ['Seat leakage'], ['Operate periodically']),
            'pm_lever': C('Operates the branch valve (in line with pipe = open).', 'Lever handle.', 'Steel.', '—', ['—'], ['—']),
            'pm_instruments': C('Shows header pressure; drains the header.', 'Gauge and drain valve.', 'Stainless.', '—', ['—'], ['Calibrate gauge']),
        },
    },
    'orifice_plate': {
        'summary': ('An orifice plate flowmeter is a thin plate with a precise sharp-edged hole clamped between two flanges. The restriction speeds the flow '
                    'up and lowers its pressure; the pressure difference between upstream and downstream taps is measured by a DP transmitter, and the flow '
                    'rate is proportional to the square root of that difference (ISO 5167-2). Simple, cheap and standardised, but with a high permanent pressure loss.'),
        'classification': {'family': 'Differential-pressure flowmeter', 'type': 'Concentric square-edged orifice, flange taps'},
        'model_configuration': {'beta_ratio': '≈ 0.6 (d/D)', 'equation': 'q_m = C/√(1−β⁴) · ε · (π/4)d² · √(2ΔP·ρ1)', 'straight_runs': 'Required upstream/downstream lengths per ISO 5167-2 tables'},
        'standards': _std(('ISO 5167-1 / -2', 'Measurement of fluid flow by pressure differential devices — orifice plates', 'Geometry, discharge coefficient, uncertainty.'),
                          ('AGA Report No. 3', 'Orifice metering of natural gas', 'Gas custody transfer.')),
        'references': ['Miller, Flow Measurement Engineering Handbook', 'ISO 5167 (verify current edition)'],
        'components': {
            'op_flanges': C('Hold the plate and provide the pressure taps.', 'Orifice flanges with drilled taps.', 'Carbon/stainless steel.', 'Tap positions defined by the standard.', ['Plugged taps'], ['Blow down impulse lines']),
            'op_plate': C('Creates the restriction that produces the differential pressure.', 'Flat plate with sharp square-edged bore and handle tab.', 'Stainless steel.',
                          'Edge sharpness and flatness affect accuracy; install bevel downstream.', ['Edge rounding/erosion', 'Plate bowing', 'Deposits'], ['Pull and inspect plate edge']),
            'fm_run': C('Provides a fully developed velocity profile at the meter.', 'Straight pipe lengths upstream and downstream.', 'As line.', 'Fittings too close cause errors.', ['Swirl/profile distortion'], ['Check straight lengths']),
            'fm_dp': C('Measures the pressure difference across the element.', 'DP transmitter, impulse lines, root valves and 3-valve manifold.', 'Stainless.', 'Zero check with equalising valve.',
                       ['Plugged/leaking impulse lines', 'Gas in liquid lines'], ['Zero check, line blow-down']),
        },
    },
    'flow_nozzle': {
        'summary': ('A flow nozzle is a differential-pressure flow element with a smooth, curved inlet leading to a cylindrical throat. It is more robust than an '
                    'orifice plate and handles high-velocity, high-temperature and erosive flows such as boiler steam and feedwater, with a lower permanent '
                    'loss than an orifice but higher than a venturi (ISO 5167-3).'),
        'classification': {'family': 'Differential-pressure flowmeter', 'type': 'ISA 1932 flow nozzle between flanges'},
        'model_configuration': {'beta_ratio': '≈ 0.6', 'taps': 'Upstream ~1D, throat/corner tap downstream'},
        'standards': _std(('ISO 5167-3', 'Nozzles and Venturi nozzles', 'Geometry and coefficients.'), ('ASME PTC 6 / PTC 19.5', 'Flow measurement for performance tests', 'Turbine tests.')),
        'references': ['Miller, Flow Measurement Engineering Handbook'],
        'components': {
            'fn_flanges': C('Clamp the nozzle into the line.', 'Carrier flanges and bolting.', 'Steel.', '—', ['Leaks'], ['Visual']),
            'fn_nozzle': C('Accelerates the flow smoothly to create a measurable ΔP.', 'Machined nozzle with elliptical inlet and cylindrical throat.', 'Stainless/alloy steel.', 'Throat diameter must be accurate.',
                           ['Erosion/deposits in throat'], ['Inspect throat']),
            'fm_run': C('Straight pipe for a developed flow profile.', 'Upstream and downstream pipe.', 'As line.', '—', ['—'], ['—']),
            'fm_dp': C('Measures the ΔP.', 'DP transmitter with impulse lines.', 'Stainless.', '—', ['Plugged lines'], ['Zero check']),
        },
    },
    'venturi_tube': {
        'summary': ('A venturi tube measures flow with a smooth convergent cone, a short cylindrical throat and a gentle divergent cone. Pressure falls in the '
                    'throat as velocity rises (Bernoulli), and the long diffuser recovers most of it, so permanent pressure loss is very low — ideal for large '
                    'water mains and energy-sensitive services. It also tolerates dirty fluids better than an orifice (ISO 5167-4).'),
        'classification': {'family': 'Differential-pressure flowmeter', 'type': 'Classical Herschel venturi tube (machined convergent)'},
        'model_configuration': {'beta_ratio': '≈ 0.55', 'cones': 'Convergent ~21°, divergent 7–15° (ISO 5167-4)', 'taps': 'Piezometer rings at inlet and throat'},
        'standards': _std(('ISO 5167-4', 'Classical Venturi tubes', 'Geometry and coefficients.'),),
        'references': ['Miller, Flow Measurement Engineering Handbook'],
        'components': {
            'vt_body': C('Creates a pressure drop proportional to flow², then recovers it.', 'Inlet cylinder, convergent cone, throat, divergent cone; piezometer rings.', 'Cast iron, steel, stainless.',
                         'Long; needs straight upstream pipe.', ['Deposits in throat', 'Tap blockage'], ['Inspect taps']),
            'fm_run': C('Straight pipe for a developed flow profile.', 'Upstream and downstream pipe.', 'As line.', '—', ['—'], ['—']),
            'fm_dp': C('Measures the ΔP between inlet and throat.', 'DP transmitter with impulse lines.', 'Stainless.', '—', ['Plugged lines'], ['Zero check']),
        },
    },
    'pig_launcher': {
        'summary': ('A pig launcher is the pipeline trap used to insert a "pig" — a cleaning, gauging or inspection device — into a flowing pipeline. The pig '
                    'is loaded through the closure door into the oversize barrel; after closing and pressurising, the kicker line and valves are lined up so the '
                    'flow pushes the pig through the reducer into the pipeline.'),
        'classification': {'family': 'Pipeline equipment', 'type': 'Horizontal pig launching trap'},
        'model_configuration': {'sequence': 'Isolate → depressurise & drain → open door → load pig → close → fill & vent → pressurise → open trap valve → open kicker → close mainline valve → pig launched',
                                'safety': 'Pressure-warning lock prevents opening the door under pressure'},
        'standards': _std(('ASME B31.4 / B31.8', 'Pipeline transportation systems for liquids / gas', 'Pipeline design.'), ('ASME BPVC VIII', 'Pressure vessels', 'Barrel and closure design.'),
                          ('DNV-RP-F116 / operator standards', 'Pigging', 'Pigging practice.')),
        'references': ['Pipeline Pigging Handbook (Clarion/Tiratsoo)'],
        'components': {
            'pig_barrel': C('Holds the pig before launching; larger than the pipeline so the pig can be loaded.', 'Major barrel, eccentric/concentric reducer, saddles, vent, drain and pressure gauge.',
                            'Carbon steel.', 'Rated as pipeline.', ['Corrosion, sludge build-up'], ['Thickness survey']),
            'pig_closure': C('Gives quick access to the barrel.', 'Quick-opening closure door with davit and safety interlock.', 'Forged steel.', 'Never open under pressure.', ['Seal damage', 'Interlock failure'],
                             ['Check seal and interlock each use']),
            'pig_lines': C('Connects the trap to the pipeline and supplies the kicker flow behind the pig.', 'Pipeline tie-in and kicker (bypass) line.', 'Carbon steel.', '—', ['—'], ['—']),
            'pig_valves': C('Isolate the trap and direct flow behind the pig.', 'Full-bore trap valve, kicker valve, mainline valve.', 'Steel.', 'Trap valve must be full-bore for pig passage.', ['Leakage'], ['Seat tests']),
            'pig_signaller': C('Confirms the pig has passed.', 'Intrusive/non-intrusive pig signaller.', 'Steel.', '—', ['Missed signal'], ['Function test']),
            'pig_pig': C('Cleans, separates products, gauges or inspects the pipeline.', 'Body with polyurethane cups/discs (or foam, smart pigs).', 'Steel body, polyurethane.', 'Driven by differential pressure.',
                         ['Stuck pig', 'Cup wear'], ['Inspect after run']),
        },
    },
    'pig_receiver': {
        'summary': ('A pig receiver is the trap at the downstream end of a pipeline section that catches the arriving pig. Flow is diverted through the '
                    'barrel so the pig is carried in; once it has arrived the trap is isolated, drained and depressurised, and the pig and collected debris '
                    'are removed through the closure door.'),
        'classification': {'family': 'Pipeline equipment', 'type': 'Horizontal pig receiving trap'},
        'model_configuration': {'sequence': 'Open trap valve & bypass → pig arrives in barrel → signaller confirms → isolate → drain & vent → open door → remove pig & debris'},
        'standards': _std(('ASME B31.4 / B31.8', 'Pipeline transportation systems', 'Pipeline design.'), ('ASME BPVC VIII', 'Pressure vessels', 'Barrel and closure.')),
        'references': ['Pipeline Pigging Handbook'],
        'components': {
            'pig_barrel': C('Receives and holds the arriving pig and debris.', 'Oversize barrel with reducer, drains and vents.', 'Carbon steel.', 'Size for debris volume.', ['Sludge, pyrophoric deposits'], ['Clean and inspect']),
            'pig_closure': C('Access to remove the pig.', 'Quick-opening closure with interlock.', 'Forged steel.', 'Check for pressure and gas before opening.', ['Seal damage'], ['Interlock check']),
            'pig_lines': C('Bypass/kicker line around the trap.', 'Pipe connections.', 'Carbon steel.', '—', ['—'], ['—']),
            'pig_valves': C('Isolate and line up the trap.', 'Trap, bypass and mainline valves.', 'Steel.', '—', ['Leakage'], ['Seat tests']),
            'pig_signaller': C('Shows the pig has arrived/passed.', 'Pig signaller.', 'Steel.', '—', ['—'], ['Function test']),
            'pig_pig': C('Cleaning or inspection pig arriving with the flow.', 'Cup/disc pig.', 'Steel, polyurethane.', '—', ['Wear'], ['Inspect cups']),
        },
    },
    'pipe_insulation_system': {
        'summary': ('A pipe insulation system reduces heat loss (or gain) from piping, keeps process temperatures stable, protects personnel from hot '
                    'surfaces and prevents condensation on cold lines. A typical hot-service system has an anti-corrosion coating on the pipe, one or more '
                    'insulation layers with staggered joints, and a weatherproof metal cladding held by bands, plus insulated supports.'),
        'classification': {'family': 'Piping system', 'type': 'Hot-service insulation (mineral wool / calcium silicate) with metal cladding'},
        'model_configuration': {'layers': 'Coating → 2 × 50 mm insulation → aluminium/stainless cladding', 'hazard': 'Corrosion under insulation (CUI) where water gets in'},
        'standards': _std(('ASTM C585 / C547 / C533', 'Insulation materials and sizes', 'Material specifications.'), ('CINI Manual', 'Insulation for industries', 'Design and installation practice.'),
                          ('API RP 583 / NACE SP0198', 'Corrosion under insulation', 'CUI prevention and inspection.')),
        'references': ['US DOE — 3E Plus / insulation guides', 'CINI Manual (verify edition)'],
        'components': {
            'pi_pipe': C('Carries the hot process fluid.', 'Steel pipe.', 'Carbon/alloy steel.', '—', ['CUI'], ['CUI inspection']),
            'pi_coating': C('Protects the pipe surface from corrosion under insulation.', 'High-temperature coating system.', 'Epoxy phenolic, TSA, silicone.', 'Must suit operating temperature.',
                            ['Coating breakdown'], ['Inspect during insulation repairs']),
            'pi_insulation': C('Reduces heat flow through low thermal conductivity material.', 'Pre-formed sections, staggered joints.', 'Mineral wool, calcium silicate, cellular glass, aerogel.',
                               'Wet insulation loses most of its value.', ['Wetting', 'Mechanical damage'], ['Thermography survey']),
            'pi_cladding': C('Keeps weather and water out and protects the insulation.', 'Overlapped metal jacketing with bands and sealant.', 'Aluminium, stainless steel.',
                             'Overlaps must shed water.', ['Damaged/open seams → water ingress'], ['Visual inspection']),
            'pi_support': C('Supports the pipe without crushing the insulation or creating a thermal bridge.', 'Pipe shoe/cradle.', 'Steel with insulating blocks.', '—', ['Corrosion at support'], ['Visual']),
        },
    },
    'pipe_tracing_system': {
        'summary': ('A pipe tracing system adds heat to a pipe to replace what it loses through its insulation, keeping the product above its freezing, '
                    'congealing or crystallisation temperature (for example caustic and liquor lines in alumina refineries, heavy fuel oil, sulphur and water '
                    'lines in winter). Steam tracing uses small tubes carrying steam alongside the pipe, drained by a trap; electric tracing uses a '
                    'self-regulating heating cable controlled by a thermostat.'),
        'classification': {'family': 'Piping system', 'type': 'Steam tracing and electric (self-regulating) heat tracing'},
        'model_configuration': {'steam': 'Copper/stainless tracer with heat-transfer cement, thermodynamic trap', 'electric': 'Self-regulating cable spiral, power box, thermostat'},
        'standards': _std(('IEC/IEEE 60079-30-1 / IEEE 515', 'Electrical resistance trace heating', 'Design and installation (hazardous areas).'),
                          ('API RP 2000 / owner standards', 'Steam tracing practice', 'Tracer design (company standards common).')),
        'references': ['Chemelex / nVent / Thermon tracing design guides (generic)'],
        'components': {
            'pt_pipe': C('Carries the product that must stay warm.', 'Process pipe.', 'Steel.', '—', ['Plugging if tracing fails'], ['Temperature monitoring']),
            'pt_steam_tracer': C('Carries steam whose condensing heat warms the pipe.', 'Small tube fixed along the pipe, often with heat-transfer cement.', 'Copper, stainless.',
                                 'Tracer must be continuous and free-draining.', ['Leaks', 'Waterlogging (failed trap)'], ['Trap survey, thermography']),
            'pt_trap': C('Drains condensate from the tracer while holding steam.', 'Thermodynamic disc trap.', 'Stainless.', '—', ['Blowing steam / blocked'], ['Ultrasonic test']),
            'pt_electric': C('Electric heat source whose output self-limits with temperature.', 'Self-regulating polymer heating cable, power connection box, thermostat.', 'Polymer core, copper buses.',
                             'Hazardous-area certification and earth-leakage protection required.', ['Cable damage', 'Ground faults'], ['Insulation resistance test']),
            'pi_insulation': C('Keeps the supplied heat in.', 'Insulation and cladding over pipe and tracer.', 'Mineral wool/aluminium.', '—', ['Wet insulation'], ['Visual, thermography']),
        },
    },
}

BUILDERS = {'pipe_spool': pipe_spool, 'pipe_manifold': pipe_manifold, 'orifice_plate': orifice_plate, 'flow_nozzle': flow_nozzle, 'venturi_tube': venturi_tube,
            'pig_launcher': pig_launcher, 'pig_receiver': pig_receiver, 'pipe_insulation_system': pipe_insulation_system, 'pipe_tracing_system': pipe_tracing_system}
