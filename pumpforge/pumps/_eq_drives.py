"""Rotating Equipment — EQ-159 … EQ-170: generators, motor drives, couplings and mechanical drives, rotor assembly."""
import math
from mathutils import Matrix
from pumpforge.core import Model, lathe, cyl, box, csg, split, join, split_many, rotate, extrude_poly, hex_prism, TAU, OPERATE_FRAMES
from pumpforge.valvekit import P, keys_loop, smooth_pulse, spring
from pumpforge.parts import add_motor_h, add_coupling, add_baseplate, hollow_pipe, transform_parts
from pumpforge.rotkit import (add_inline_engine, helical_gear, sprocket, open_path, centre_for_links, pedestal, ring_of, radial_blades)
from pumpforge.shapes import sweep_tube, cone_arrow
from pumpforge.common_meta import C

CAT = '7 · Rotating Equipment – Additional Machinery'


def _model(pid, title):
    return Model(pid, title, CAT, META[pid])


def _spin_keys(m, part, axis, theta_fn, n=60):
    k = 'XYZ'.index(axis)
    for mesh in part.meshes:
        keys = []
        for i in range(n + 1):
            r = [0.0, 0.0, 0.0]
            r[k] = theta_fn(i / n)
            keys.append((1 + OPERATE_FRAMES * i / n, tuple(r)))
        m.keyframes(mesh, 'Operate', 'rotation_euler', keys)


def _speed_profile(revs, shape):
    """theta(t) for a loop with relative speed shape(t) >= 0, ending exactly at revs turns."""
    N = 400
    acc = [0.0]
    for i in range(N):
        acc.append(acc[-1] + shape((i + 0.5) / N) / N)
    tot = acc[-1]

    def th(t):
        f = t * N
        i = min(N - 1, int(f))
        return TAU * revs * (acc[i] + (acc[i + 1] - acc[i]) * (f - i)) / tot
    return th


def _waveforms(m, kind, x0, z0, w, h, y, series, title, desc):
    objs = []
    for j, (nm, mat, fn, zoff) in enumerate(series):
        pts = [(x0 + w * i / 160, y, z0 + zoff + h * fn(i / 160)) for i in range(161)]
        objs.append(sweep_tube(f'wf{j}', pts, 0.004, mat, 8))
        objs.append(box(f'ax{j}', (w, 0.002, 0.002), (x0 + w / 2, y, z0 + zoff), 'steel_dark'))
    m.overlay(kind, join(kind, objs), title, desc)
    return objs


def _generator(m, pfx, x0, cz, R, L, foot_z, revs, label='Generator', mat='paint_blue', exciter=True, poles=4, explode=0.6):
    x1 = x0 + L
    fr = csg(pfx + 'fr', [cyl(pfx + 'fo', R, x0, x1, mat, 96, axis='X', center=(0, 0, cz)),
                          box(pfx + 'ft', (L * 0.8, R * 1.7, cz - R * 0.6 - foot_z), (x0 + L / 2, 0, foot_z + (cz - R * 0.6 - foot_z) / 2), mat, bevel=0.01),
                          box(pfx + 'tb', (L * 0.3, R * 0.6, R * 0.35), (x0 + L * 0.55, 0, cz + R + R * 0.12), mat, bevel=0.01)],
             [cyl(pfx + 'fi', R - 0.02, x0 + 0.02, x1 - 0.02, mat, 96, axis='X', center=(0, 0, cz)),
              cyl(pfx + 'sb', 0.035, x0 - 0.01, x1 + 0.01, mat, 32, axis='X', center=(0, 0, cz))], mat)
    P(m, pfx + 'frame', f'{label} – Frame, End Shields & Terminal Box', 'generator', fr, explode=(0, 0, -0.2), ref='gen_frame')
    core = csg(pfx + 'core', [cyl(pfx + 'co', R - 0.022, x0 + 0.08, x1 - 0.08, 'lamination', 96, axis='X', center=(0, 0, cz))],
               [cyl(pfx + 'ci', R * 0.6, x0, x1, 'lamination', 96, axis='X', center=(0, 0, cz))] +
               [cyl(f'{pfx}sl{i}', 0.012, x0 + 0.07, x1 - 0.07, 'lamination', 12, axis='X',
                    center=(0, R * 0.62 * math.cos(TAU * i / 36), cz + R * 0.62 * math.sin(TAU * i / 36))) for i in range(36)], 'lamination')
    ends = [cyl(f'{pfx}ew{k}', R * 0.82, xx - 0.04, xx + 0.04, 'copper', 64, axis='X', center=(0, 0, cz), r_in=R * 0.62) for k, xx in enumerate((x0 + 0.06, x1 - 0.06))]
    cond = [cyl(f'{pfx}cd{i}', 0.009, x0 + 0.04, x1 - 0.04, 'copper', 8, axis='X',
                center=(0, R * 0.62 * math.cos(TAU * i / 36), cz + R * 0.62 * math.sin(TAU * i / 36))) for i in range(36)]
    P(m, pfx + 'stator', f'{label} – Stator Core & 3-Phase Armature Winding', 'generator', [core] + ends + cond, explode=(0, 0, R * 2.4), ref='gen_stator')
    rp = R * 0.58
    rot = [cyl(pfx + 'sh', 0.035, x0 - 0.25, x1 + (0.32 if exciter else 0.08), 'steel', 32, axis='X', center=(0, 0, cz), ch=0.003),
           cyl(pfx + 'yk', R * 0.3, x0 + 0.1, x1 - 0.1, 'steel', 48, axis='X', center=(0, 0, cz))]
    for i in range(poles):
        a = TAU * i / poles

        def pl(nm, w, d, h, r0):
            b = box(nm, (L - 0.24, w, d), (x0 + L / 2, 0, cz + r0 + d / 2), 'steel')
            return rotate(b, a, 'X', (0, 0, cz))
        rot += [pl(f'{pfx}pb{i}', R * 0.3, rp - R * 0.3 - 0.02, 0, R * 0.29), pl(f'{pfx}ps{i}', R * 0.5, 0.02, 0, rp - 0.02),
                rotate(box(f'{pfx}fc{i}', (L - 0.2, R * 0.42, rp - R * 0.34 - 0.04), (x0 + L / 2, 0, cz + R * 0.31 + (rp - R * 0.34 - 0.04) / 2), 'copper', bevel=0.006), a, 'X', (0, 0, cz))]
    rot.append(ring_of(pfx + 'fan', 8, lambda i: box(f'{pfx}fb{i}', (0.05, 0.006, R * 0.35), (x1 - 0.06, 0, cz + R * 0.42), 'aluminium'), cz=cz))
    if exciter:
        rot += [cyl(pfx + 'ea', R * 0.32, x1 + 0.08, x1 + 0.16, 'copper', 48, axis='X', center=(0, 0, cz)),
                cyl(pfx + 'rr', R * 0.3, x1 + 0.2, x1 + 0.23, 'aluminium', 48, axis='X', center=(0, 0, cz))]
        rot += [cyl(f'{pfx}dd{i}', 0.012, x1 + 0.23, x1 + 0.25, 'steel_dark', 12, axis='X',
                    center=(0, R * 0.2 * math.cos(TAU * i / 6), cz + R * 0.2 * math.sin(TAU * i / 6))) for i in range(6)]
    pr = P(m, pfx + 'rotor', f'{label} – Rotor: {poles} Salient Poles with Field Coils{", Exciter Armature & Rotating Rectifier" if exciter else ""}',
           'rotating_element', rot, explode=(0, -R * 2.6, 0), ref='gen_rotor', section='keep', pivot=(0, 0, cz))
    pr.spin('X', revs)
    if exciter:
        ex = csg(pfx + 'ex', [cyl(pfx + 'exo', R * 0.5, x1 + 0.05, x1 + 0.3, mat, 64, axis='X', center=(0, 0, cz))],
                 [cyl(pfx + 'exi', R * 0.34, x1 + 0.06, x1 + 0.4, mat, 64, axis='X', center=(0, 0, cz))], mat)
        exs = cyl(pfx + 'exs', R * 0.34, x1 + 0.08, x1 + 0.16, 'lamination', 48, axis='X', center=(0, 0, cz), r_in=R * 0.33)
        P(m, pfx + 'exciter', f'{label} – Exciter Stator & Cover', 'generator', [ex, exs], explode=(0.4, 0, 0), ref='gen_exciter')
    return dict(x1=x1 + (0.3 if exciter else 0.0), rp=rp)


# =============================================================== EQ-159 Engine-driven generator (gas engine)
def engine_driven_generator(out):
    m = _model('engine_driven_generator', 'Engine-Driven Generator (Spark-Ignition Gas Engine, Inline-4)')
    CZ = 0.42
    eng = add_inline_engine(m, 'e_', -0.55, CZ, 4, 0.11, 0.12, 0.22, mat='paint_orange', revs=2, label='Gas Engine', head_label='Cylinder Head, Valves & Spark Plugs')
    fw = join('fw', [cyl('fwd', 0.2, eng['x1'] + 0.03, eng['x1'] + 0.08, 'cast_iron', 64, axis='X', center=(0, 0, CZ)),
                     ring_of('ft', 60, lambda i: box(f'ftt{i}', (0.05, 0.01, 0.012), (eng['x1'] + 0.055, 0, CZ + 0.205), 'steel'), cz=CZ)])
    pf = P(m, 'flywheel', 'Flywheel with Starter Ring Gear', 'rotating_element', fw, explode=(0.2, -0.4, 0), ref='edg_flywheel', section='keep', pivot=(0, 0, CZ))
    pf.spin('X', 2)
    fh = csg('fh', [cyl('fho', 0.23, eng['x1'] - 0.02, eng['x1'] + 0.14, 'paint_orange', 64, axis='X', center=(0, 0, CZ))],
             [cyl('fhi', 0.215, eng['x1'] - 0.01, eng['x1'] + 0.15, 'paint_orange', 64, axis='X', center=(0, 0, CZ))], 'paint_orange')
    P(m, 'flywheel_housing', 'Flywheel Housing (SAE adaptor to generator)', 'engine', fh, explode=(0, 0, 0.3), ref='edg_flywheel')
    g = _generator(m, 'g_', eng['x1'] + 0.16, CZ, 0.24, 0.5, 0.06, 2, label='Generator', exciter=True)
    rad = csg('rad', [box('ro', (0.08, 0.7, 0.62), (-0.85, 0, CZ + 0.12), 'paint_grey', bevel=0.006)], [box('ri', (0.1, 0.62, 0.54), (-0.85, 0, CZ + 0.12), 'paint_grey')], 'paint_grey')
    core = box('rcore', (0.05, 0.62, 0.54), (-0.85, 0, CZ + 0.12), 'aluminium')
    P(m, 'radiator', 'Radiator (coolant–air heat exchanger)', 'cooling', [rad, core], explode=(-0.4, 0, 0), ref='edg_radiator')
    fan = join('fan', [cyl('fh2', 0.04, -0.78, -0.72, 'steel', 24, axis='X', center=(0, 0, CZ + 0.1))] +
               [rotate(box(f'fb{i}', (0.02, 0.07, 0.24), (-0.75, 0, CZ + 0.1 + 0.14), 'paint_yellow', bevel=0.004), TAU * i / 6, 'X', (0, 0, CZ + 0.1)) for i in range(6)])
    pfn = P(m, 'cooling_fan', 'Engine Cooling Fan', 'cooling', fan, explode=(-0.3, 0, 0.3), ref='edg_fan', section='keep', pivot=(0, 0, CZ + 0.1))
    pfn.spin('X', 4)
    add_baseplate(m, -0.95, g['x1'] + 0.05, 0.75, 0.06)
    mts = [box(f'em{i}', (0.08, 0.36, 0.13 - 0.06), (x, 0, 0.06 + 0.035), 'paint_orange') for i, x in enumerate((eng['xs'][0], eng['xs'][-1]))]
    P(m, 'engine_mounts', 'Engine Mounts', 'engine', mts, explode=(0, 0, -0.2), ref='edg_flywheel', section='keep')
    exh = [hollow_pipe('em', [(-0.45, 0.13, eng['deck'] - 0.02), (eng['x1'] - 0.05, 0.13, eng['deck'] - 0.02), (eng['x1'] - 0.05, 0.13, eng['top'] + 0.25)], 0.03, 'exhaust', 16, bend=0.05, t=0.004)]
    P(m, 'exhaust', 'Exhaust Manifold & Outlet', 'engine', exh, explode=(0, 0.4, 0), ref='edg_exhaust', section='keep')
    cp = box('cp', (0.3, 0.12, 0.4), (g['x1'] - 0.2, 0.36, CZ + 0.35), 'paint_grey', bevel=0.01)
    P(m, 'control_panel', 'Generator Control Panel (AVR, protection, synchroniser)', 'controls', cp, explode=(0, -0.3, 0.2), ref='edg_panel', section='keep')
    m.flow('power_flow', [(-0.4, 0, CZ), (eng['x1'], 0, CZ), (eng['x1'] + 0.16, 0, CZ), (g['x1'] - 0.3, 0, CZ), (g['x1'] - 0.3, 0, CZ + 0.3), (g['x1'] - 0.2, 0.3, CZ + 0.35)],
           'power', 0.01, 0.2)
    m.flow('exhaust_gas', [(-0.45, 0.13, eng['deck'] - 0.02), (eng['x1'] - 0.05, 0.13, eng['deck'] - 0.02), (eng['x1'] - 0.05, 0.13, eng['top'] + 0.3)], 'exhaust', 0.008, 0.15)
    m.flow('cooling_air', [(-1.2, 0, CZ + 0.15), (-0.6, 0, CZ + 0.15), (-0.4, 0, CZ + 0.4)], 'air', 0.008, 0.15)
    return m.export(out)


# =============================================================== EQ-160 Alternator
def alternator(out):
    m = _model('alternator', 'Brushless Synchronous Alternator (4-Pole, Self-Excited)')
    CZ = 0.45
    g = _generator(m, 'a_', -0.35, CZ, 0.3, 0.7, 0.0, 1, label='Alternator', exciter=True, mat='paint_blue')
    brg = [cyl('b1', 0.06, -0.39, -0.33, 'steel', 32, axis='X', center=(0, 0, CZ), r_in=0.035), cyl('b2', 0.06, 0.33, 0.39, 'steel', 32, axis='X', center=(0, 0, CZ), r_in=0.035)]
    P(m, 'bearings', 'Bearings (DE & NDE)', 'bearings', brg, explode=(0, 0.5, 0), ref='motor_bearings')
    avr = box('avr', (0.18, 0.06, 0.14), (0.0, -0.08, CZ + 0.42), 'pcb', bevel=0.004)
    P(m, 'avr', 'Automatic Voltage Regulator (AVR) in Terminal Box', 'controls', avr, explode=(0, -0.3, 0.3), ref='alt_avr', section='keep')
    hub = cyl('hub', 0.08, -0.62, -0.58, 'steel', 48, axis='X', center=(0, 0, CZ))
    ph = P(m, 'drive_hub', 'Drive Hub / Coupling Disc (from prime mover)', 'power_transmission', hub, explode=(-0.3, 0, 0), ref='alt_hub', section='keep', pivot=(0, 0, CZ))
    ph.spin('X', 1)
    arcs = []
    for i in range(4):
        a = TAU * i / 4 + math.pi / 4
        pts = []
        for k in range(13):
            f = k / 12
            aa = a - math.pi / 4 + f * math.pi / 2
            rr = 0.2 + 0.06 * math.sin(math.pi * f)
            pts.append((0.0, rr * math.cos(aa), CZ + rr * math.sin(aa)))
        arcs.append(sweep_tube(f'fl{i}', pts, 0.006, 'magnet_n' if i % 2 else 'magnet_s', 8))
    m.overlay('magnetic_field', join('mf', arcs), 'Rotating magnetic field', 'DC in the field coils makes the rotor poles alternately N and S. As the rotor turns, this '
              'field sweeps past the stator conductors and induces a 3-phase AC voltage. Frequency = poles × rpm / 120 (4 poles at 1500 rpm → 50 Hz).')
    m.annotate('magnetic_field', 'Flux crosses the air gap pole → stator → next pole', (0.0, 0, CZ + 0.4))
    m.flow('power', [(-0.7, 0, CZ), (-0.35, 0, CZ), (0.0, 0.12, CZ + 0.12), (0.0, 0.0, CZ + 0.28), (0.0, 0, CZ + 0.42), (0.1, -0.15, CZ + 0.5)], 'power', 0.01, 0.2)
    m.flow('excitation', [(g['x1'] - 0.15, 0, CZ + 0.17), (g['x1'] - 0.08, 0, CZ + 0.07), (0.0, 0, CZ + 0.1)], 'electric', 0.006, 0.1)
    m.flow('cooling_air', [(0.6, 0.0, CZ + 0.2), (0.3, 0, CZ + 0.2), (-0.3, 0, CZ + 0.2), (-0.4, 0, CZ + 0.32)], 'air', 0.006, 0.15)
    return m.export(out)


# =============================================================== EQ-161 Diesel generator set
def diesel_generator_set(out):
    m = _model('diesel_generator_set', 'Diesel Generator Set (Inline-6, Turbocharged, Skid-Mounted)')
    CZ = 0.55
    eng = add_inline_engine(m, 'e_', -0.75, CZ, 6, 0.12, 0.14, 0.25, mat='paint_yellow', revs=2, label='Diesel Engine')
    tc = join('tc', [cyl('tcc', 0.07, -0.05, 0.05, 'stainless', 32, axis='Y', center=(eng['x1'] - 0.15, 0.25, eng['deck'] + 0.1)),
                     cyl('tct', 0.06, -0.05, 0.05, 'paint_grey', 32, axis='Y', center=(eng['x1'] - 0.3, 0.25, eng['deck'] + 0.1))])
    tc.data.transform(Matrix.Translation((0, 0.0, 0)))
    P(m, 'turbocharger', 'Turbocharger (exhaust turbine drives intake compressor)', 'engine', tc, explode=(0, 0.4, 0.3), ref='dg_turbo', section='keep')
    fw = cyl('fw', 0.22, eng['x1'] + 0.03, eng['x1'] + 0.09, 'cast_iron', 64, axis='X', center=(0, 0, CZ))
    pf = P(m, 'flywheel', 'Flywheel', 'rotating_element', fw, explode=(0.2, -0.4, 0), ref='edg_flywheel', section='keep', pivot=(0, 0, CZ))
    pf.spin('X', 2)
    g = _generator(m, 'g_', eng['x1'] + 0.14, CZ, 0.27, 0.55, 0.24, 2, label='Alternator', exciter=True)
    rad = csg('rad', [box('ro', (0.1, 0.9, 0.8), (-1.08, 0, CZ + 0.15), 'paint_grey', bevel=0.006)], [box('ri', (0.12, 0.82, 0.72), (-1.08, 0, CZ + 0.15), 'paint_grey')], 'paint_grey')
    core = box('rcore', (0.06, 0.82, 0.72), (-1.08, 0, CZ + 0.15), 'aluminium')
    P(m, 'radiator', 'Radiator & Charge-Air Cooler', 'cooling', [rad, core], explode=(-0.4, 0, 0), ref='edg_radiator')
    fan = join('fan', [cyl('fh', 0.05, -1.0, -0.94, 'steel', 24, axis='X', center=(0, 0, CZ + 0.15))] +
               [rotate(box(f'fb{i}', (0.025, 0.09, 0.3), (-0.97, 0, CZ + 0.15 + 0.18), 'paint_grey', bevel=0.004), TAU * i / 7, 'X', (0, 0, CZ + 0.15)) for i in range(7)])
    pfn = P(m, 'cooling_fan', 'Radiator Fan (engine-driven)', 'cooling', fan, explode=(-0.3, 0, 0.3), ref='edg_fan', section='keep', pivot=(0, 0, CZ + 0.15))
    pfn.spin('X', 3)
    base = csg('base', [box('bo', (g['x1'] + 1.25, 1.0, 0.2), ((g['x1'] - 1.2) / 2, 0, 0.1), 'paint_grey', bevel=0.01)], [box('bi', (g['x1'] + 1.15, 0.92, 0.17), ((g['x1'] - 1.2) / 2, 0, 0.09), 'paint_grey')], 'paint_grey')
    fuel = box('fuel', (g['x1'] + 1.13, 0.9, 0.12), ((g['x1'] - 1.2) / 2, 0, 0.075), 'hydraulic_oil')
    avm = [cyl(f'av{i}', 0.04, 0.2, 0.24, 'rubber', 24, center=(x, y, 0)) for i, (x, y) in enumerate(((-0.6, 0.3), (-0.6, -0.3), (0.2, 0.3), (0.2, -0.3), (g['x1'] - 0.3, 0.3), (g['x1'] - 0.3, -0.3)))]
    P(m, 'base_frame', 'Base Frame with Integral Fuel Tank & Anti-Vibration Mounts', 'baseplate', [base, fuel] + avm, explode=(0, 0, -0.3), ref='dg_base')
    supp = [box('es', (0.1, 0.5, CZ - 0.3), (eng['xs'][0], 0, 0.24 + (CZ - 0.3) / 2), 'paint_yellow'), box('es2', (0.1, 0.5, CZ - 0.3), (eng['x1'] - 0.1, 0, 0.24 + (CZ - 0.3) / 2), 'paint_yellow')]
    P(m, 'engine_mounts', 'Engine Feet / Mounting Brackets', 'engine', supp, explode=(0, 0, -0.2), ref='dg_base', section='keep')
    sil = [cyl('sil', 0.12, -0.2, 0.5, 'paint_grey', 48, axis='X', center=(0, 0.1, eng['top'] + 0.45), ch=0.01),
           hollow_pipe('ep', [(eng['x1'] - 0.15, 0.25, eng['deck'] + 0.17), (eng['x1'] - 0.15, 0.25, eng['top'] + 0.3), (0.5, 0.1, eng['top'] + 0.45)], 0.04, 'exhaust', 16, bend=0.05, t=0.004),
           hollow_pipe('tail', [(-0.2, 0.1, eng['top'] + 0.45), (-0.4, 0.1, eng['top'] + 0.45), (-0.4, 0.1, eng['top'] + 0.75)], 0.04, 'steel', 16, bend=0.05, t=0.004)]
    P(m, 'exhaust_silencer', 'Exhaust Pipe, Flexible Bellows & Silencer', 'engine', sil, explode=(0, 0, 0.5), ref='dg_silencer', section='keep')
    cp = box('cp', (0.4, 0.15, 0.6), (g['x1'] - 0.2, 0.46, CZ + 0.25), 'paint_grey', bevel=0.01)
    P(m, 'control_panel', 'Genset Controller & Circuit Breaker', 'controls', cp, explode=(0, -0.3, 0.2), ref='edg_panel', section='keep')
    m.flow('power_flow', [(-0.6, 0, CZ), (eng['x1'], 0, CZ), (g['x1'] - 0.3, 0, CZ), (g['x1'] - 0.3, 0, CZ + 0.32), (g['x1'] - 0.2, 0.4, CZ + 0.3)], 'power', 0.012, 0.25)
    m.flow('exhaust_gas', [(eng['xs'][0], 0.15, eng['deck'] - 0.02), (eng['x1'] - 0.3, 0.25, eng['deck'] + 0.1), (eng['x1'] - 0.15, 0.25, eng['top'] + 0.3), (0.5, 0.1, eng['top'] + 0.45),
                           (-0.4, 0.1, eng['top'] + 0.45), (-0.4, 0.1, eng['top'] + 0.8)], 'exhaust', 0.01, 0.2)
    m.flow('coolant', [(-0.7, 0.2, eng['deck']), (-1.03, 0.3, CZ + 0.45), (-1.03, 0.3, CZ - 0.15), (-0.7, 0.2, CZ - 0.1)], 'water', 0.008, 0.15)
    m.flow('fuel', [(0.3, 0.3, 0.08), (0.3, 0.3, 0.3), (eng['xs'][2], 0.18, eng['deck'] + 0.08)], 'hydraulic_oil', 0.006, 0.15)
    return m.export(out)


# =============================================================== helpers: cabinet & simple motor
def _cabinet(m, x0, x1, z0, z1, d, label, ref):
    cab = csg('cab', [box('co', (x1 - x0, d, z1 - z0), ((x0 + x1) / 2, 0, (z0 + z1) / 2), 'paint_grey', bevel=0.008)],
              [box('ci', (x1 - x0 - 0.03, d - 0.03, z1 - z0 - 0.03), ((x0 + x1) / 2, 0, (z0 + z1) / 2), 'paint_grey')], 'paint_grey')
    P(m, 'enclosure', label, 'enclosure', cab, explode=(0, 0.4, 0), ref=ref)
    door = box('door', (x1 - x0 - 0.01, 0.015, z1 - z0 - 0.01), ((x0 + x1) / 2, -d / 2 - 0.008, (z0 + z1) / 2), 'paint_grey', bevel=0.004)
    P(m, 'door', 'Front Door (hidden in cutaway)', 'enclosure', door, explode=(0, -0.6, 0), ref=ref, section='hide')


def _simple_motor(m, x0, cz, R, L, theta_fn, label='Driven Motor'):
    fr = csg('mfr', [cyl('mo', R, x0, x0 + L, 'paint_motor', 64, axis='X', center=(0, 0, cz)), box('mft', (L * 0.7, R * 1.6, 0.04), (x0 + L / 2, 0, cz - R - 0.02), 'paint_motor')],
             [cyl('mi', R - 0.012, x0 + 0.012, x0 + L - 0.012, 'paint_motor', 64, axis='X', center=(0, 0, cz))], 'paint_motor')
    fins = ring_of('mfin', 20, lambda i: box(f'mf{i}', (L * 0.9, 0.006, 0.014), (x0 + L / 2, 0, cz + R + 0.005), 'paint_motor'), cz=cz)
    P(m, 'motor_frame', f'{label} – Frame', 'motor', [fr, fins], explode=(0, 0, -0.2), ref='motor_frame_h')
    st = cyl('mst', R - 0.014, x0 + 0.04, x0 + L - 0.04, 'lamination', 64, axis='X', center=(0, 0, cz), r_in=R * 0.55)
    P(m, 'motor_stator', f'{label} – Stator & Windings', 'motor', st, explode=(0, 0, R * 2.4), ref='stator')
    rot = join('mr', [cyl('mrc', R * 0.53, x0 + 0.05, x0 + L - 0.05, 'aluminium', 48, axis='X', center=(0, 0, cz)),
                      cyl('msh', R * 0.18, x0 - 0.18, x0 + L + 0.05, 'steel', 32, axis='X', center=(0, 0, cz)),
                      box('mky', (0.12, 0.012, 0.012), (x0 - 0.1, 0, cz + R * 0.18), 'paint_red'),
                      cyl('mdisc', R * 0.9, x0 - 0.2, x0 - 0.18, 'paint_red', 48, axis='X', center=(0, 0, cz)),
                      box('mmark', (0.01, R * 0.2, R * 0.6), (x0 - 0.21, 0, cz + R * 0.5), 'paint_yellow')])
    pr = P(m, 'motor_rotor', f'{label} – Rotor, Shaft & Speed Marker Disc', 'rotating_element', rot, explode=(0, -R * 2.6, 0), ref='rotor', section='keep', pivot=(0, 0, cz))
    _spin_keys(m, pr, 'X', theta_fn)


# =============================================================== EQ-162 VFD
def variable_frequency_drive(out):
    m = _model('variable_frequency_drive', 'Variable Frequency Drive (VFD) — 6-Pulse Rectifier, DC Link, IGBT Inverter')
    X0, X1, Z0, Z1, D = -0.35, 0.35, 0.3, 1.5, 0.4
    _cabinet(m, X0, X1, Z0, Z1, D, 'Drive Enclosure (IP-rated cabinet)', 'vfd_enclosure')
    yb = 0.12
    rx = join('rx', [box('rxc', (0.22, 0.08, 0.16), (-0.18, yb, Z1 - 0.2), 'lamination')] +
              [cyl(f'rxw{i}', 0.035, Z1 - 0.26, Z1 - 0.14, 'copper', 24, center=(-0.25 + 0.07 * i, yb, 0), r_in=0.018) for i in range(3)])
    P(m, 'line_reactor', 'Input Line Reactor (choke) — limits harmonics & inrush', 'power_input', rx, explode=(0, -0.4, 0.2), ref='vfd_reactor', section='keep')
    rect = join('rect', [box('rm', (0.16, 0.06, 0.1), (0.12, yb, Z1 - 0.22), 'thermoplastic', bevel=0.004)] +
                [cyl(f'rt{i}', 0.008, Z1 - 0.17, Z1 - 0.155, 'brass', 8, center=(0.07 + 0.05 * i, yb - 0.01, 0)) for i in range(3)])
    P(m, 'rectifier', 'Rectifier Module (6 diodes: AC → DC)', 'power_section', rect, explode=(0, -0.45, 0.1), ref='vfd_rectifier', section='keep')
    caps = [cyl(f'cp{i}', 0.04, Z1 - 0.62, Z1 - 0.42, 'paint_blue_dark', 32, center=(-0.24 + 0.095 * i, yb, 0), ch=0.004) for i in range(6)]
    bus = box('bus', (0.56, 0.01, 0.03), (-0.0, yb - 0.045, Z1 - 0.4), 'copper')
    P(m, 'dc_bus', 'DC Link: Capacitor Bank & Bus Bars', 'power_section', caps + [bus], explode=(0, -0.5, 0), ref='vfd_dc_link', section='keep')
    hs = join('hs', [box('hsb', (0.5, 0.02, 0.28), (0.0, 0.17, Z1 - 0.9), 'aluminium')] +
              [box(f'hf{i}', (0.006, 0.06, 0.28), (-0.24 + 0.024 * i, 0.2, Z1 - 0.9), 'aluminium') for i in range(21)])
    igbt = [box(f'ig{i}', (0.12, 0.04, 0.1), (-0.15 + 0.15 * i, yb, Z1 - 0.9), 'thermoplastic', bevel=0.004) for i in range(3)]
    P(m, 'inverter', 'IGBT Inverter Modules (DC → variable-frequency AC) on Heatsink', 'power_section', [hs] + igbt, explode=(0, -0.55, -0.1), ref='vfd_inverter', section='keep')
    fan = join('cf', [cyl('cfh', 0.03, Z0 + 0.12, Z0 + 0.15, 'thermoplastic', 24, center=(0.0, 0.15, 0))] +
               [rotate(box(f'cb{i}', (0.08, 0.02, 0.004), (0.045, 0.15, Z0 + 0.135), 'thermoplastic'), TAU * i / 7, 'Z', (0.0, 0.15, 0)) for i in range(7)])
    pfan = P(m, 'cooling_fan', 'Heatsink Cooling Fan', 'cooling', fan, explode=(0, -0.3, -0.3), ref='vfd_fan', section='keep', pivot=(0.0, 0.15, Z0 + 0.135))
    pfan.spin('Z', 6)
    cb = [box('pcb', (0.26, 0.012, 0.2), (0.18, yb - 0.02, Z1 - 0.62), 'pcb'), box('kp', (0.1, 0.02, 0.14), (0.2, -D / 2 - 0.02, Z1 - 0.3), 'thermoplastic', bevel=0.004),
          box('lcd', (0.07, 0.003, 0.04), (0.2, -D / 2 - 0.031, Z1 - 0.27), 'glass')]
    P(m, 'control', 'Control Board (PWM modulator, protection) & Keypad', 'controls', cb, explode=(0, -0.7, 0.2), ref='vfd_control', section='keep')
    trm = [box(f'tm{i}', (0.04, 0.03, 0.05), (-0.1 + 0.07 * i, yb, Z0 + 0.06), 'brass') for i in range(6)]
    P(m, 'terminals', 'Line (L1–L3) & Motor (U–V–W) Terminals', 'power_input', trm, explode=(0, -0.4, -0.3), ref='vfd_terminals', section='keep')
    cab = [hollow_pipe('mc', [(0.15, yb, Z0), (0.15, yb, 0.1), (0.75, 0.0, 0.1), (0.75, 0.0, 0.3)], 0.018, 'thermoplastic', 12, bend=0.05, t=0.004)]
    P(m, 'motor_cable', 'Screened Motor Cable', 'power_input', cab, explode=(0.2, 0, -0.2), ref='vfd_terminals', section='keep')
    th = _speed_profile(3, lambda t: 0.08 + 0.92 * smooth_pulse(t, 0.3, 0.3, 0.3))
    _simple_motor(m, 0.62, 0.42, 0.13, 0.36, th, label='Motor (speed follows the VFD)')
    stand = box('pl', (2.0, 0.8, 0.05), (0.2, 0, 0.025), 'cast_iron')
    P(m, 'plinth', 'Plinth', 'baseplate', stand, explode=(0, 0, -0.3), ref='vfd_enclosure', section='keep')
    m.flow('power', [(-0.25, yb, Z1 + 0.1), (-0.25, yb, Z1 - 0.2), (0.12, yb, Z1 - 0.2), (0.0, yb, Z1 - 0.5), (0.0, yb, Z1 - 0.9), (0.15, yb, Z0 + 0.06), (0.15, yb, 0.1),
                     (0.75, 0.0, 0.1), (0.75, 0, 0.3)], 'electric', 0.01, 0.2)
    m.flow('cooling_air', [(0.0, 0.18, Z0 + 0.02), (0.0, 0.2, Z1 - 0.9), (0.0, 0.2, Z1 + 0.05)], 'air', 0.008, 0.15)
    sine = lambda t: math.sin(TAU * 2 * t)

    def pwm(t):
        carrier = 2 * abs((t * 40) % 2 - 1) - 1
        return 1.0 if sine(t) > carrier else -1.0
    _waveforms(m, 'waveforms', -0.35, Z1 + 0.35, 0.7, 0.08, -D / 2 - 0.05,
               [('AC in (50 Hz)', 'electric', lambda t: math.sin(TAU * 4 * t), 0.36), ('DC link', 'paint_red', lambda t: 0.9, 0.18), ('PWM output', 'paint_blue', pwm, 0.0),
                ('Motor current (≈ sine at the set frequency)', 'power', sine, -0.18)],
               'Waveforms: AC → DC → PWM → motor', 'The rectifier turns fixed-frequency AC into DC; the capacitors smooth it. The IGBTs switch the DC on and off thousands '
               'of times per second (PWM) so the average voltage follows a sine wave of any chosen frequency. Motor speed ≈ 120 × f / poles, so changing f changes speed.')
    for txt, z in (('Mains AC: fixed 50/60 Hz', 0.36), ('DC link (smoothed)', 0.18), ('PWM pulses', 0.0), ('Motor current at set frequency', -0.18)):
        m.annotate('waveforms', txt, (-0.45, -D / 2 - 0.05, Z1 + 0.35 + z))
    return m.export(out)


# =============================================================== EQ-163 Soft starter
def soft_starter(out):
    m = _model('soft_starter', 'Soft Starter with Bypass Contactor (3-Phase Thyristor Control)')
    X0, X1, Z0, Z1, D = -0.3, 0.3, 0.3, 1.3, 0.35
    _cabinet(m, X0, X1, Z0, Z1, D, 'Starter Enclosure', 'ss_enclosure')
    yb = 0.1
    hs = [box(f'hs{i}', (0.12, 0.05, 0.22), (-0.16 + 0.16 * i, yb + 0.06, Z1 - 0.55), 'aluminium') for i in range(3)]
    scr = []
    for i in range(3):
        x = -0.16 + 0.16 * i
        scr += [cyl(f'sc{i}a', 0.03, yb + 0.005, yb + 0.035, 'steel_dark', 24, axis='Y', center=(x, 0, Z1 - 0.5)),
                cyl(f'sc{i}b', 0.03, yb + 0.005, yb + 0.035, 'steel_dark', 24, axis='Y', center=(x, 0, Z1 - 0.6))]
    P(m, 'thyristors', 'Thyristor (SCR) Pairs — one anti-parallel pair per phase — on Heatsinks', 'power_section', hs + scr, explode=(0, -0.45, 0), ref='ss_scr', section='keep')
    ct = [cyl(f'ct{i}', 0.03, Z1 - 0.82, Z1 - 0.8, 'thermoplastic', 24, center=(-0.16 + 0.16 * i, yb, 0), r_in=0.015) for i in range(3)]
    P(m, 'current_transformers', 'Current Transformers (current limit & protection)', 'controls', ct, explode=(0, -0.4, -0.2), ref='ss_ct', section='keep')
    kb = box('kb', (0.36, 0.1, 0.14), (0.0, yb, Z1 - 0.25), 'thermoplastic', bevel=0.006)
    P(m, 'bypass_contactor', 'Bypass Contactor Body & Coil', 'power_section', kb, explode=(0, -0.5, 0.2), ref='ss_bypass', section='keep')
    cont = join('ctc', [box(f'cc{i}', (0.05, 0.02, 0.02), (-0.12 + 0.12 * i, yb - 0.06, Z1 - 0.22), 'copper') for i in range(3)])
    pc = P(m, 'bypass_contacts', 'Bypass Contacts (close after the ramp)', 'power_section', cont, explode=(0, -0.6, 0.3), ref='ss_bypass', section='keep')
    keys_loop(m, pc, lambda t: (0, 0.02 * (1 - (1.0 if 0.45 <= t < 0.92 else 0.0)), 0))
    ctl = [box('ctl', (0.2, 0.03, 0.14), (0.0, -D / 2 - 0.015, Z1 - 0.95), 'thermoplastic', bevel=0.004), box('dsp', (0.08, 0.003, 0.04), (0.0, -D / 2 - 0.031, Z1 - 0.93), 'glass')]
    P(m, 'control_module', 'Control Module (ramp time, initial voltage, current limit)', 'controls', ctl, explode=(0, -0.6, -0.1), ref='ss_control', section='keep')
    trm = [box(f'tm{i}', (0.04, 0.03, 0.05), (-0.1 + 0.07 * i, yb, Z0 + 0.06), 'brass') for i in range(6)]
    P(m, 'terminals', 'Line & Motor Terminals', 'power_input', trm, explode=(0, -0.4, -0.3), ref='ss_terminals', section='keep')
    th = _speed_profile(3, lambda t: (min(1.0, t / 0.45) ** 1.5) if t < 0.92 else max(0.0, 1 - (t - 0.92) / 0.08) * 1.0)
    _simple_motor(m, 0.55, 0.4, 0.13, 0.36, th, label='Motor (soft-started)')
    stand = box('pl', (1.8, 0.8, 0.05), (0.2, 0, 0.025), 'cast_iron')
    P(m, 'plinth', 'Plinth', 'baseplate', stand, explode=(0, 0, -0.3), ref='ss_enclosure', section='keep')
    m.flow('ramp_current', [(0.0, yb, Z1 + 0.1), (0.0, yb, Z1 - 0.4), (-0.16, yb, Z1 - 0.5), (-0.16, yb, Z1 - 0.81), (0.04, yb, Z0 + 0.06), (0.7, 0, 0.12), (0.7, 0, 0.3)],
           'electric', 0.009, 0.2, active=[(0.0, 0.45)])
    m.flow('bypass_current', [(0.0, yb, Z1 + 0.1), (0.0, yb - 0.06, Z1 - 0.22), (0.0, yb - 0.06, Z1 - 0.81), (0.04, yb, Z0 + 0.06), (0.7, 0, 0.12), (0.7, 0, 0.3)],
           'power', 0.009, 0.2, active=[(0.45, 0.92)])

    def chopped(alpha):
        def f(t):
            ph = (TAU * 3 * t) % math.pi
            return math.sin(TAU * 3 * t) if ph > alpha else 0.0
        return f
    _waveforms(m, 'waveforms', -0.3, Z1 + 0.3, 0.6, 0.08, -D / 2 - 0.05,
               [('Start: late firing', 'electric', chopped(2.2), 0.24), ('Mid ramp', 'electric', chopped(1.2), 0.08), ('End of ramp / bypass: full sine', 'power', chopped(0.0), -0.08)],
               'Voltage ramp by phase-angle control', 'At start the thyristors fire late in each half-cycle, so only part of the sine wave reaches the motor (low voltage, '
               'low torque and current). The firing angle is advanced over the ramp time until the full voltage is applied; then the bypass contactor closes.')
    for txt, z in (('Start: reduced voltage', 0.24), ('Ramp: firing advanced', 0.08), ('Full voltage → bypass', -0.08)):
        m.annotate('waveforms', txt, (-0.4, -D / 2 - 0.05, Z1 + 0.3 + z))
    return m.export(out)


# =============================================================== EQ-164 Magnetic coupling
def magnetic_coupling(out):
    m = _model('magnetic_coupling', 'Magnetic (Synchronous Permanent-Magnet) Coupling with Containment Shell')
    CZ = 0.4
    Ro, Ri, n = 0.12, 0.085, 12
    outer = [lathe('oc', [(0.03, -0.18), (Ro + 0.02, -0.18), (Ro + 0.02, 0.1), (Ro, 0.1), (Ro, -0.155), (0.03, -0.155)], 'steel', 96, axis='X', center=(0, 0, CZ)),
             cyl('osh', 0.025, -0.45, -0.17, 'steel', 32, axis='X', center=(0, 0, CZ))]
    for i in range(n):
        a = TAU * i / n
        mg = box(f'om{i}', (0.22, 0.04, 0.016), (-0.03, 0, CZ + Ro - 0.008), 'magnet_n' if i % 2 else 'magnet_s')
        outer.append(rotate(mg, a, 'X', (0, 0, CZ)))
    po = P(m, 'outer_rotor', 'Outer (Driving) Magnet Rotor on Motor Shaft — alternating N/S magnets', 'rotating_element', outer, explode=(-0.45, 0, 0), ref='mc_outer', pivot=(0, 0, CZ))
    po.spin('X', 2)
    can = csg('can', [lathe('cn', [(0.0, -0.15), (Ro - 0.022, -0.15), (Ro - 0.022, 0.13), (Ro + 0.04, 0.13), (Ro + 0.04, 0.15), (0.0, 0.15)], 'stainless', 96, axis='X', center=(0, 0, CZ))],
              [lathe('cni', [(0.0, -0.145), (Ro - 0.026, -0.145), (Ro - 0.026, 0.16), (0.0, 0.16)], 'stainless', 96, axis='X', center=(0, 0, CZ))], 'stainless')
    P(m, 'containment_shell', 'Containment Shell (Can) — static seal between atmosphere and process', 'casing', can, explode=(0, 0, 0.35), ref='mc_can')
    inner = [cyl('ih', Ri - 0.016, -0.13, 0.08, 'steel', 64, axis='X', center=(0, 0, CZ)), cyl('ish', 0.025, -0.1, 0.5, 'steel', 32, axis='X', center=(0, 0, CZ))]
    for i in range(n):
        a = TAU * i / n
        mg = box(f'im{i}', (0.2, 0.034, 0.016), (-0.03, 0, CZ + Ri - 0.008), 'magnet_s' if i % 2 else 'magnet_n')
        inner.append(rotate(mg, a, 'X', (0, 0, CZ)))
    pi_ = P(m, 'inner_rotor', 'Inner (Driven) Magnet Rotor on Pump/Load Shaft', 'rotating_element', inner, explode=(0.45, 0, 0), ref='mc_inner', pivot=(0, 0, CZ))
    pi_.spin('X', 2)
    hs = [pedestal('pm', -0.33, CZ, 0.025, 0.0), pedestal('pl', 0.35, CZ, 0.025, 0.0)]
    P(m, 'bearing_housings', 'Bearing Housings (motor side & load side)', 'bearings', hs, explode=(0, 0.4, 0), ref='mc_bearings')
    add_motor_h(m, 'm_', -0.95, CZ, 0.14, 0.4, 0.0, 0.025, 0.1, explode_dx=-0.6, revs=2)
    n0 = [p for p in m.parts if p.id.startswith('m_')]
    transform_parts(m, n0, Matrix.Translation((-1.5, 0, 0)) @ Matrix.Rotation(math.pi, 4, 'Z'))
    arcs = []
    for i in range(n):
        a = TAU * (i + 0.5) / n
        pts = []
        for k in range(9):
            f = k / 8
            aa = a - math.pi / n + f * TAU / n
            rr = (Ri + Ro) / 2 + 0.03 * math.sin(math.pi * f) * (1 if i % 2 else -1)
            pts.append((-0.03, rr * math.cos(aa), CZ + rr * math.sin(aa)))
        arcs.append(sweep_tube(f'fl{i}', pts, 0.003, 'magnet_n' if i % 2 else 'magnet_s', 6))
    m.overlay('magnetic_field', join('mf', arcs), 'Magnetic field through the can', 'Each outer magnet attracts the opposite pole on the inner rotor through the thin, '
              'non-magnetic containment shell. Torque is transmitted without contact; if the load torque exceeds the coupling rating the rotors slip ("decouple").')
    m.annotate('magnetic_field', 'Flux passes through the shell — no shaft seal needed', (-0.03, 0, CZ + 0.22))
    m.flow('torque_path', [(-0.6, 0, CZ), (-0.17, 0, CZ), (-0.03, 0.0, CZ + Ro - 0.008), (-0.03, 0.0, CZ + Ri - 0.008), (0.05, 0, CZ), (0.5, 0, CZ)], 'power', 0.008, 0.15)
    return m.export(out)


# =============================================================== EQ-165 Torque limiter
def torque_limiter(out):
    m = _model('torque_limiter', 'Friction Torque Limiter (Slip Clutch) with Chain Sprocket')
    CZ = 0.2
    th_hub = lambda t: TAU * 2 * t
    th_spr = lambda t: TAU * 2 * min(t, 0.5)
    hub = join('hub', [cyl('h', 0.045, -0.06, 0.1, 'steel', 48, axis='X', center=(0, 0, CZ)), cyl('hf', 0.1, -0.06, -0.045, 'steel', 64, axis='X', center=(0, 0, CZ)),
                       cyl('sh', 0.025, -0.36, 0.12, 'steel', 32, axis='X', center=(0, 0, CZ), ch=0.002),
                       box('mk', (0.01, 0.02, 0.03), (-0.065, 0, CZ + 0.08), 'paint_yellow')])
    ph = P(m, 'hub', 'Hub on Driving Shaft (with marker)', 'rotating_element', hub, explode=(-0.3, 0, 0), ref='tl_hub', pivot=(0, 0, CZ))
    _spin_keys(m, ph, 'X', th_hub)
    fac = [cyl(f'f{i}', 0.095, x - 0.004, x + 0.004, 'carbon', 64, axis='X', center=(0, 0, CZ), r_in=0.047) for i, x in enumerate((-0.04, 0.0))]
    P(m, 'friction_facings', 'Friction Facings (linings)', 'friction', fac, explode=(0, -0.0, 0.25), ref='tl_facings')
    spr_, R = sprocket('sp', 24, 0.019, 0.006, -0.032, -0.008, 'steel_dark', cx=0, cz=0)
    spr_ = rotate(spr_, -math.pi / 2, 'Z')
    spr_.data.transform(Matrix.Translation((0, 0, CZ)))
    spr = csg('spr', [spr_], [cyl('sb', 0.047, -0.1, 0.1, 'steel', 32, axis='X', center=(0, 0, CZ))], 'steel_dark')
    spr = join('sprk', [spr, box('smk', (0.01, 0.02, 0.03), (-0.035, 0, CZ + R - 0.03), 'paint_red')])
    ps = P(m, 'sprocket', 'Sprocket (driven member, free on a bush) — stops on overload', 'rotating_element', spr, explode=(0, -0.35, 0), ref='tl_sprocket', pivot=(0, 0, CZ))
    _spin_keys(m, ps, 'X', th_spr)
    pp = cyl('pp', 0.095, 0.005, 0.02, 'steel', 64, axis='X', center=(0, 0, CZ), r_in=0.046)
    disc = [lathe(f'ds{i}', [(0.048, 0.025 + 0.012 * i), (0.052, 0.025 + 0.012 * i), (0.085, 0.031 + 0.012 * i), (0.081, 0.033 + 0.012 * i)], 'steel', 64,
                  axis='X', center=(0, 0, CZ)) for i in range(3)]
    nut = join('nut', [hex_prism('n', 0.11, 0.065, 0.085, 'steel', axis='X', center=(0, 0, CZ))] +
               [cyl(f'ls{i}', 0.005, 0.085, 0.095, 'steel_dark', 8, axis='X', center=(0, 0.04 * math.cos(TAU * i / 3), CZ + 0.04 * math.sin(TAU * i / 3))) for i in range(3)])
    pps = P(m, 'pressure_plate', 'Pressure Plate, Disc (Belleville) Springs & Adjusting Nut', 'friction', [pp] + disc + [nut], explode=(0.3, 0, 0), ref='tl_springs', pivot=(0, 0, CZ))
    _spin_keys(m, pps, 'X', th_hub)
    chain = []
    for k in range(10):
        a = math.pi / 2 + (k - 4.5) * TAU / 24
        chain.append(cyl(f'cr{k}', 0.006, -0.03, -0.01, 'steel', 12, axis='X', center=(0, R * math.cos(a), CZ + R * math.sin(a))))
    for k in range(6):
        chain.append(cyl(f'cs{k}', 0.006, -0.03, -0.01, 'steel', 12, axis='X', center=(0, -R * 0.0 - 0.019 * (k + 1) + R * math.cos(math.pi / 2 + 4.5 * TAU / 24), CZ + R * math.sin(math.pi / 2 + 4.5 * TAU / 24))))
    P(m, 'chain', 'Roller Chain to Driven Machine (stalls on jam)', 'power_transmission', chain, explode=(0, 0, 0.3), ref='tl_chain', section='keep')
    hs = [pedestal('pb', -0.14, CZ, 0.025, 0.0), pedestal('pb2', -0.3, CZ, 0.025, 0.0)]
    P(m, 'bearings', 'Shaft Bearings', 'bearings', hs, explode=(0, 0.4, 0), ref='tl_bearings', section='keep')
    arr = [sweep_tube('ta', [(0.15, 0.14 * math.cos(a), CZ + 0.14 * math.sin(a)) for a in [0.3 + 1.6 * k / 10 for k in range(11)]], 0.006, 'power', 8),
           cone_arrow('tah', (0.15, 0.14 * math.cos(1.9), CZ + 0.14 * math.sin(1.9)), (0, -math.sin(1.9), math.cos(1.9)), 0.03, 0.015, 'power'),
           sweep_tube('tb', [(-0.08, 0.17 * math.cos(a), CZ + 0.17 * math.sin(a)) for a in [3.6 + 1.4 * k / 10 for k in range(11)]], 0.006, 'paint_red', 8),
           cone_arrow('tbh', (-0.08, 0.17 * math.cos(3.6), CZ + 0.17 * math.sin(3.6)), (0, math.sin(3.6), -math.cos(3.6)), 0.03, 0.015, 'paint_red')]
    m.overlay('torque', join('tq', arr), 'Driving torque vs load torque', 'Disc springs clamp the sprocket between the friction facings. While the load torque (red) '
              'is below the set slip torque, the friction transmits the drive torque (magenta) and everything turns together. On a jam the load torque exceeds '
              'the setting: the facings slip, the hub keeps turning and the sprocket stops — protecting the drive. Tighten the nut to raise the setting.')
    m.annotate('torque', 'Normal: hub and sprocket turn together', (0.15, 0, CZ + 0.25))
    m.annotate('torque', 'Overload: sprocket stops, facings slip', (-0.1, 0, CZ - 0.25))
    m.flow('power', [(-0.4, 0, CZ), (-0.05, 0, CZ + 0.02), (-0.04, 0, CZ + 0.08), (-0.02, 0, CZ + R), (-0.02, -0.12, CZ + R + 0.01)], 'power', 0.006, 0.1, active=[(0.0, 0.5)])
    return m.export(out)


# =============================================================== EQ-166 Speed reducer
def speed_reducer(out):
    m = _model('speed_reducer', 'Two-Stage Helical Speed Reducer (Parallel Shaft, 6:1)')
    CZ = 0.45
    mod = 0.008
    xi, xm, xo = -0.22, -0.22 + mod * (16 + 32) / 2, -0.22 + mod * (16 + 32) / 2 + mod * (15 + 45) / 2
    y1a, y1b, y2a, y2b = -0.07, -0.02, 0.02, 0.08
    hous = csg('hs', [box('ho', (xo - xi + 0.52, 0.28, 0.6), ((xi + xo) / 2, 0.0, CZ + 0.02), 'paint_blue', bevel=0.02),
                      box('hf', (xo - xi + 0.62, 0.36, 0.04), ((xi + xo) / 2, 0, CZ - 0.3), 'paint_blue', bevel=0.004)] +
               [cyl(f'bb{i}{s}', 0.065, s * 0.14 - 0.02, s * 0.14 + 0.02, 'paint_blue', 48, axis='Y', center=(x, 0, CZ)) for i, x in enumerate((xi, xm, xo)) for s in (-1, 1)],
               [box('hi', (xo - xi + 0.48, 0.24, 0.56), ((xi + xo) / 2, 0, CZ + 0.02), 'paint_blue')] +
               [cyl(f'sb{i}', 0.042, -0.2, 0.2, 'paint_blue', 32, axis='Y', center=(x, 0, CZ)) for i, x in enumerate((xi, xm, xo))], 'paint_blue')
    P(m, 'housing', 'Gear Housing (split, front half removed in cutaway)', 'casing', hous, explode=(0, 0, 0), ref='sr_housing')
    oil = csg('oil', [box('oi', (xo - xi + 0.47, 0.23, 0.14), ((xi + xo) / 2, 0, CZ - 0.19), 'hydraulic_oil')],
              [cyl('og', 0.29, -0.2, 0.2, 'hydraulic_oil', 64, axis='Y', center=(xo, 0, CZ))], 'hydraulic_oil')
    P(m, 'oil_bath', 'Oil Bath (splash lubrication)', 'lubrication', oil, explode=(0, 0, -0.3), ref='sr_oil')
    g1, rp1 = helical_gear('g1', mod, 16, y1a, y1b, 'steel', cx=xi, cz=CZ, helix_deg=15, hand=1)
    s1 = cyl('s1', 0.028, -0.4, 0.17, 'steel', 32, axis='Y', center=(xi, 0, CZ), ch=0.002)
    p1 = P(m, 'input_shaft', 'Input Shaft & Pinion (z = 16)', 'rotating_element', [g1, s1], explode=(-0.25, -0.4, 0.3), ref='sr_input', section='keep', pivot=(xi, 0, CZ))
    p1.spin('Y', 6)
    g2, _ = helical_gear('g2', mod, 32, y1a, y1b, 'steel', cx=xm, cz=CZ, helix_deg=15, hand=-1, phase=math.pi + math.pi / 32)
    g3, _ = helical_gear('g3', mod, 15, y2a, y2b, 'steel', cx=xm, cz=CZ, helix_deg=12, hand=1)
    s2 = cyl('s2', 0.03, -0.17, 0.17, 'steel', 32, axis='Y', center=(xm, 0, CZ), ch=0.002)
    p2 = P(m, 'intermediate_shaft', 'Intermediate Shaft: Gear (z = 32) & Pinion (z = 15)', 'rotating_element', [g2, g3, s2], explode=(0, -0.5, 0.45), ref='sr_intermediate', section='keep', pivot=(xm, 0, CZ))
    p2.spin('Y', -3)
    g4, _ = helical_gear('g4', mod, 45, y2a, y2b, 'steel', cx=xo, cz=CZ, helix_deg=12, hand=-1, phase=math.pi + math.pi / 45)
    s3 = join('s3', [cyl('s3s', 0.04, -0.17, 0.45, 'steel', 32, axis='Y', center=(xo, 0, CZ), ch=0.002), box('ky', (0.012, 0.12, 0.012), (xo, 0.36, CZ + 0.04), 'steel_dark')])
    p3 = P(m, 'output_shaft', 'Output Shaft & Gear (z = 45)', 'rotating_element', [g4, s3], explode=(0.3, -0.55, 0.3), ref='sr_output', section='keep', pivot=(xo, 0, CZ))
    p3.spin('Y', 1)
    brg = [cyl(f'br{i}{s}', 0.06, s * 0.14 - 0.018, s * 0.14 + 0.018, 'steel', 32, axis='Y', center=(x, 0, CZ), r_in=0.03) for i, x in enumerate((xi, xm, xo)) for s in (-1, 1)]
    P(m, 'bearings', 'Shaft Bearings (taper-roller / ball)', 'bearings', brg, explode=(0, 0.45, 0), ref='sr_bearings')
    br = join('brt', [cyl('br', 0.015, CZ + 0.32, CZ + 0.38, 'brass', 16, center=(xm, 0.05, 0)), cyl('dp', 0.02, xo + 0.26, xo + 0.29, 'brass', 6, axis='X', center=(0, 0.0, CZ - 0.2))])
    P(m, 'breather', 'Breather, Oil Fill & Drain Plugs', 'lubrication', br, explode=(0, 0, 0.3), ref='sr_breather', section='keep')
    m.flow('power', [(xi, -0.42, CZ), (xi, -0.045, CZ), (xi + rp1, -0.045, CZ + 0.01), (xm, -0.045, CZ), (xm, 0.05, CZ), (xm + 0.06, 0.05, CZ), (xo, 0.05, CZ), (xo, 0.46, CZ)],
           'power', 0.009, 0.15, speed=[3, 3, 3, 1.5, 1.5, 1.5, 0.6, 0.6])
    return m.export(out)


# =============================================================== belt & chain drives (common layout)
def _motor_y(m, x, cz, y_de, R, L, foot_z, shaft_r, shaft_len, revs, label):
    n0 = len(m.parts)
    add_motor_h(m, 'm_', y_de, cz, R, L, foot_z, shaft_r, shaft_len, explode_dx=0.4, revs=revs, label=label)
    transform_parts(m, m.parts[n0:], Matrix.Translation((x, 0, 0)) @ Matrix.Rotation(math.pi / 2, 4, 'Z'))


def _movers(m, pid, name, pos, L, n, dist, maker, group, ref):
    p = m.part(pid, name, group, explode=(0, -0.3, 0.2), info={'ref': ref})
    for i in range(n):
        s0 = L * i / n
        x, z, a = pos(s0)
        o = maker(i)
        ms = p.add(o, smooth_angle=30)
        lk, rk = [], []
        for f in range(OPERATE_FRAMES + 1):
            xx, zz, aa = pos(s0 + dist * f / OPERATE_FRAMES)
            lk.append((1 + f, (xx, 0.0, zz)))
            rk.append((1 + f, (0.0, -aa, 0.0)))
        ms.location = (x, 0, z)
        ms.rotation_euler = (0, -a, 0)
        m.keyframes(ms, 'Operate', 'location', lk)
        m.keyframes(ms, 'Operate', 'rotation_euler', rk)
    return p


def belt_drive_assembly(out):
    m = _model('belt_drive_assembly', 'V-Belt Drive Assembly (3 Belts, Motor on Tensioning Slide Base)')
    CZ = 0.42
    r1, r2 = 0.075, 0.075 * 2.5
    C = centre_for_links(r1, r2, TAU * r1, 6, 0.7)
    pos, L = open_path(r1, r2, C, 0.0, CZ)
    ys = (-0.03, 0.0, 0.03)

    def sheave(nm, r, x, spokes):
        prof = [(0.03, -0.05), (r + 0.006, -0.05)]
        for y in ys:
            prof += [(r + 0.006, y - 0.013), (r - 0.012, y - 0.004), (r - 0.012, y + 0.004), (r + 0.006, y + 0.013)]
        prof += [(r + 0.006, 0.05), (0.03, 0.05)]
        rim = lathe(nm + 'r', [(rr, yy) for rr, yy in prof], 'cast_iron', 96, axis='Y', center=(x, 0, CZ))
        web = csg(nm + 'w', [cyl(nm + 'wd', r - 0.02, -0.012, 0.012, 'cast_iron', 64, axis='Y', center=(x, 0, CZ))],
                  [cyl(f'{nm}h{i}', (r - 0.06) * 0.35, -0.02, 0.02, 'cast_iron', 24, axis='Y',
                       center=(x + (r * 0.55) * math.cos(TAU * i / spokes), 0, CZ + (r * 0.55) * math.sin(TAU * i / spokes))) for i in range(spokes)] if r > 0.1 else [], 'cast_iron')
        hub = cyl(nm + 'hb', 0.045, -0.06, 0.06, 'cast_iron', 32, axis='Y', center=(x, 0, CZ))
        return join(nm, [rim, web, hub])
    revs1 = L / 2 / (TAU * r1)
    s1 = P(m, 'driver_sheave', 'Driver Sheave (small, on motor shaft) — Taper-Lock bush', 'power_transmission', sheave('s1', r1, 0.0, 4), explode=(0, -0.35, 0),
           ref='bd_sheave', section='keep', pivot=(0, 0, CZ))
    s1.spin('Y', revs1)
    sh2 = join('ds', [sheave('s2', r2, C, 5), cyl('s2sh', 0.03, -0.08, 0.55, 'steel', 32, axis='Y', center=(C, 0, CZ), ch=0.002)])
    s2 = P(m, 'driven_sheave', 'Driven Sheave (large) & Driven Shaft', 'power_transmission', sh2, explode=(0.3, -0.35, 0), ref='bd_sheave', section='keep', pivot=(C, 0, CZ))
    s2.spin('Y', revs1 * r1 / r2)
    belts = []
    for j, y in enumerate(ys):
        pts = []
        for k in range(161):
            x, z, _ = pos(L * k / 160)
            pts.append((x, y, z))
        belts.append(sweep_tube(f'b{j}', pts, 0.009, 'belt', 10))
    P(m, 'belts', 'Matched Set of V-Belts (3)', 'power_transmission', belts, explode=(0.15, -0.6, 0.3), ref='bd_belts', section='keep')
    _movers(m, 'belt_markers', 'Belt Motion Markers', pos, L, 18, L / 2, lambda i: box(f'bm{i}', (0.012, 0.075, 0.003), (0, 0, 0.0), 'paint_yellow'), 'power_transmission', 'bd_belts')
    _motor_y(m, 0.0, CZ, 0.1, 0.13, 0.36, 0.14, 0.03, 0.17, revs1, 'Drive Motor')
    sb = [box('sb', (0.42, 0.62, 0.04), (0.0, 0.32, 0.12), 'paint_grey'), box('rl1', (0.04, 0.62, 0.02), (-0.18, 0.32, 0.15), 'steel'),
          box('rl2', (0.04, 0.62, 0.02), (0.18, 0.32, 0.15), 'steel'), cyl('ts', 0.008, -0.35, -0.0, 'steel', 12, axis='X', center=(0, 0.32, 0.17)),
          hex_prism('tn', 0.025, -0.37, -0.35, 'steel', axis='X', center=(0, 0.32, 0.17))]
    P(m, 'slide_base', 'Motor Slide Base & Tensioning Screw', 'baseplate', sb, explode=(-0.3, 0.2, -0.2), ref='bd_slide_base', section='keep')
    peds = [pedestal('p1', 0.12, CZ, 0.03, 0.1, axis='Y'), pedestal('p2', 0.45, CZ, 0.03, 0.1, axis='Y')]
    for p_ in peds:
        p_.data.transform(Matrix.Translation((C, 0, 0)))
    P(m, 'driven_bearings', 'Driven Shaft Plummer Blocks', 'bearings', peds, explode=(0.3, 0.3, 0), ref='bd_bearings', section='keep')
    fr = box('fr', (C + 0.7, 0.9, 0.1), (C / 2, 0.25, 0.05), 'paint_grey')
    P(m, 'frame', 'Base Frame', 'baseplate', fr, explode=(0, 0, -0.3), ref='bd_slide_base', section='keep')
    gd = csg('gd', [box('go', (C + r1 + r2 + 0.12, 0.16, 2 * r2 + 0.1), (C / 2 + (r2 - r1) / 2, -0.0, CZ), 'paint_yellow', bevel=0.02)],
             [box('gi', (C + r1 + r2 + 0.1, 0.14, 2 * r2 + 0.08), (C / 2 + (r2 - r1) / 2, 0, CZ), 'paint_yellow')], 'paint_yellow')
    P(m, 'guard', 'Belt Guard (hidden in cutaway)', 'guard', gd, explode=(0, -0.8, 0), ref='bd_guard', section='hide')
    pts = [(0, -0.3, CZ), (0, 0.0, CZ)] + [(pos(L * k / 20)[0], 0.0, pos(L * k / 20)[1] + 0.02) for k in range(0, 9)] + [(C, 0.0, CZ), (C, 0.55, CZ)]
    m.flow('power', pts, 'power', 0.007, 0.15)
    return m.export(out)


def chain_drive_assembly(out):
    m = _model('chain_drive_assembly', 'Roller Chain Drive Assembly (Simplex, 15T / 30T Sprockets)')
    CZ = 0.42
    p, z1, z2, NL = 0.03, 15, 30, 62
    R1 = p / (2 * math.sin(math.pi / z1))
    R2 = p / (2 * math.sin(math.pi / z2))
    C = centre_for_links(R1, R2, p, NL, 0.6)
    pos, L = open_path(R1, R2, C, 0.0, CZ)
    sp1, _ = sprocket('sp1', z1, p, 0.0085, -0.012, 0.012, 'steel_dark', cx=0.0, cz=CZ)
    sp2, _ = sprocket('sp2', z2, p, 0.0085, -0.012, 0.012, 'steel_dark', cx=C, cz=CZ)
    h1 = cyl('h1', 0.04, -0.04, 0.04, 'steel', 32, axis='Y', center=(0, 0, CZ))
    a1 = P(m, 'driver_sprocket', f'Driver Sprocket ({z1} teeth)', 'power_transmission', [sp1, h1], explode=(0, -0.35, 0), ref='cd_sprocket', section='keep', pivot=(0, 0, CZ))
    dist = z1 * p
    a1.spin('Y', dist / (TAU * R1) * (TAU * R1) / (z1 * p))
    sh = cyl('s2sh', 0.03, -0.06, 0.55, 'steel', 32, axis='Y', center=(C, 0, CZ), ch=0.002)
    a2 = P(m, 'driven_sprocket', f'Driven Sprocket ({z2} teeth) & Shaft', 'power_transmission', [sp2, sh], explode=(0.3, -0.35, 0), ref='cd_sprocket', section='keep', pivot=(C, 0, CZ))
    a2.spin('Y', z1 / z2)

    def link(i):
        parts = [cyl(f'rl{i}', 0.0085, -0.011, 0.011, 'steel', 12, axis='Y', center=(0, 0, 0))]
        outer = i % 2 == 0
        w = 0.0215 if outer else 0.016
        for s in (-1, 1):
            parts.append(box(f'lp{i}{s}', (p + 0.016, 0.003, 0.02 if outer else 0.018), (p / 2, s * (w / 2 + 0.002), 0), 'steel_dark' if outer else 'chrome', bevel=0.004))
        return join(f'lk{i}', parts)
    _movers(m, 'chain', 'Roller Chain (rollers, inner & outer link plates)', pos, L, NL, dist, link, 'power_transmission', 'cd_chain')
    _motor_y(m, 0.0, CZ, 0.1, 0.12, 0.34, 0.14, 0.03, 0.17, 1.0, 'Gearmotor')
    Ri = p / (2 * math.sin(math.pi / 12))
    zi = CZ - (R1 + 0.55 * (R2 - R1)) - Ri - 0.014
    idl, _ = sprocket('idl', 12, p, 0.0085, -0.012, 0.012, 'steel', cx=C * 0.55, cz=zi)
    arm = box('arm', (0.18, 0.012, 0.025), (C * 0.55 + 0.09, 0.03, zi), 'steel')
    P(m, 'tensioner', 'Idler Sprocket Tensioner (slack side)', 'power_transmission', [idl, arm], explode=(0, -0.3, -0.3), ref='cd_tensioner', section='keep')
    lub = join('lub', [cyl('lb', 0.03, CZ + R1 + 0.06, CZ + R1 + 0.16, 'glass', 24, center=(0.2, 0, 0)), cyl('lt', 0.004, CZ + R1 + 0.02, CZ + R1 + 0.06, 'brass', 8, center=(0.2, 0, 0))])
    P(m, 'lubricator', 'Drip Lubricator', 'lubrication', lub, explode=(0, 0, 0.3), ref='cd_lubricator', section='keep')
    peds = [pedestal('p1', 0.12, CZ, 0.03, 0.1, axis='Y'), pedestal('p2', 0.45, CZ, 0.03, 0.1, axis='Y')]
    for p_ in peds:
        p_.data.transform(Matrix.Translation((C, 0, 0)))
    P(m, 'driven_bearings', 'Driven Shaft Plummer Blocks', 'bearings', peds, explode=(0.3, 0.3, 0), ref='bd_bearings', section='keep')
    fr = box('fr', (C + 0.7, 0.9, 0.1), (C / 2, 0.25, 0.05), 'paint_grey')
    mb = box('mb', (0.36, 0.5, 0.04), (0, 0.32, 0.12), 'paint_grey')
    P(m, 'frame', 'Base Frame & Motor Base', 'baseplate', [fr, mb], explode=(0, 0, -0.3), ref='bd_slide_base', section='keep')
    gd = csg('gd', [box('go', (C + R1 + R2 + 0.12, 0.08, 2 * R2 + 0.1), (C / 2 + (R2 - R1) / 2, -0.0, CZ), 'paint_yellow', bevel=0.02)],
             [box('gi', (C + R1 + R2 + 0.1, 0.06, 2 * R2 + 0.08), (C / 2 + (R2 - R1) / 2, 0, CZ), 'paint_yellow')], 'paint_yellow')
    P(m, 'guard', 'Chain Guard (hidden in cutaway)', 'guard', gd, explode=(0, -0.8, 0), ref='bd_guard', section='hide')
    pts = [(0, -0.3, CZ), (0, 0.0, CZ)] + [(pos(L * k / 20)[0], 0.0, pos(L * k / 20)[1] + 0.02) for k in range(0, 9)] + [(C, 0.0, CZ), (C, 0.55, CZ)]
    m.flow('power', pts, 'power', 0.007, 0.15)
    return m.export(out)


# =============================================================== EQ-169 Flywheel assembly
def flywheel_assembly(out):
    m = _model('flywheel_assembly', 'Flywheel Assembly on a Crank Press Drive')
    CZ = 0.75
    th = _speed_profile(2, lambda t: 1.0 - 0.35 * max(0.0, math.cos(TAU * 2 * t)) ** 6)
    Rf = 0.42
    fw = [lathe('rim', [(Rf - 0.07, -0.08), (Rf, -0.08), (Rf, 0.08), (Rf - 0.07, 0.08)], 'cast_iron', 96, axis='X', center=(0, 0, CZ)),
          cyl('hub', 0.08, -0.09, 0.09, 'cast_iron', 48, axis='X', center=(0, 0, CZ)),
          ring_of('sp', 6, lambda i: box(f'sp{i}', (0.05, 0.06, Rf - 0.12), (0, 0, CZ + 0.07 + (Rf - 0.12) / 2), 'cast_iron', bevel=0.01), cz=CZ),
          box('key', (0.18, 0.018, 0.014), (0, 0, CZ + 0.048), 'steel_dark')]
    pf = P(m, 'flywheel', 'Flywheel: Rim, Spokes, Hub & Key (stores kinetic energy)', 'rotating_element', fw, explode=(0, -0.6, 0), ref='fly_flywheel', section='keep', pivot=(0, 0, CZ))
    _spin_keys(m, pf, 'X', th)
    sh = join('sh', [cyl('s', 0.04, -0.6, 0.95, 'steel', 32, axis='X', center=(0, 0, CZ), ch=0.003),
                     cyl('cw', 0.11, 0.62, 0.66, 'steel', 48, axis='X', center=(0, 0, CZ)),
                     cyl('cp', 0.03, 0.66, 0.72, 'steel', 24, axis='X', center=(0, 0, CZ - 0.08))])
    psh = P(m, 'shaft_crank', 'Shaft, Crank Disc & Crank Pin', 'rotating_element', sh, explode=(0, -0.3, 0.3), ref='fly_shaft', section='keep', pivot=(0, 0, CZ))
    _spin_keys(m, psh, 'X', th)
    r, Lr = 0.08, 0.38

    def ypin(t):
        a = th(t)
        return r * math.sin(a), CZ - r * math.cos(a)
    y0, z0 = ypin(0)
    ram_z = lambda t: ypin(t)[1] - math.sqrt(Lr * Lr - ypin(t)[0] ** 2)
    zr0 = ram_z(0)
    rod = join('rod', [box('rb', (0.03, 0.03, Lr - 0.05), (0.69, 0, zr0 + Lr / 2), 'steel', bevel=0.006), cyl('re', 0.045, 0.675, 0.705, 'steel', 24, axis='X', center=(0, 0, zr0 + Lr)),
                       cyl('rs', 0.025, 0.675, 0.705, 'steel', 24, axis='X', center=(0, 0, zr0))])
    prd = P(m, 'connecting_rod', 'Connecting Rod (pitman)', 'mechanism', rod, explode=(0.3, 0, 0), ref='fly_rod', section='keep')
    ram = join('ram', [box('rm', (0.12, 0.14, 0.14), (0.69, 0, zr0 - 0.05), 'paint_grey'), box('pn', (0.03, 0.03, 0.08), (0.69, 0, zr0 - 0.16), 'chrome')])
    prm = P(m, 'ram', 'Ram & Punch (the load)', 'mechanism', ram, explode=(0.4, 0, -0.2), ref='fly_ram', section='keep')
    for mesh in prd.meshes:
        local = mesh
        from pumpforge.rotkit import local_pivot
        local_pivot(local, (0.69, 0, zr0))
        lk, rk = [], []
        for f in range(OPERATE_FRAMES + 1):
            t = f / OPERATE_FRAMES
            yp, zp = ypin(t)
            zr = ram_z(t)
            lk.append((1 + f, (0.69, 0.0, zr)))
            ang = math.atan2(yp, zp - zr)
            rk.append((1 + f, (-ang, 0.0, 0.0)))
        m.keyframes(local, 'Operate', 'location', lk)
        m.keyframes(local, 'Operate', 'rotation_euler', rk)
    for mesh in prm.meshes:
        m.keyframes(mesh, 'Operate', 'location', [(1 + f, (0, 0, ram_z(f / OPERATE_FRAMES) - zr0)) for f in range(OPERATE_FRAMES + 1)])
    frame = [box('c1', (0.06, 0.06, CZ + 0.15), (0.6, -0.16, (CZ + 0.15) / 2), 'paint_blue'),
             box('c2', (0.06, 0.06, CZ + 0.15), (0.6, 0.16, (CZ + 0.15) / 2), 'paint_blue'), box('c3', (0.3, 0.38, 0.06), (0.69, 0, 0.1), 'paint_blue'),
             box('die', (0.16, 0.18, 0.05), (0.69, 0, 0.155), 'steel_dark'), box('gd1', (0.02, 0.2, 0.32), (0.6, 0, zr0 - 0.05), 'chrome')]
    P(m, 'press_frame', 'Press Frame, Ram Guides & Die', 'structure', frame, explode=(0.5, 0, 0), ref='fly_frame', section='keep')
    peds = [pedestal('b1', -0.25, CZ, 0.04, 0.0), pedestal('b2', 0.35, CZ, 0.04, 0.0)]
    P(m, 'bearings', 'Main Bearings (pedestals)', 'bearings', peds, explode=(0, 0.4, 0), ref='fly_bearings', section='keep')
    add_coupling(m, 'coupling', -0.62, -0.52, CZ, 0.07, 0.04, explode=(-0.3, 0, 0), revs=2, foot_z=0.0)
    add_motor_h(m, 'm_', -1.3, CZ, 0.15, 0.42, 0.45, 0.04, 0.03, explode_dx=-0.5, revs=2)
    n0 = [pp for pp in m.parts if pp.id.startswith('m_')]
    transform_parts(m, n0, Matrix.Translation((-1.94, 0, 0)) @ Matrix.Rotation(math.pi, 4, 'Z'))
    mbase = box('mbase', (0.6, 0.45, 0.45), (-0.93, 0, 0.225), 'cast_iron')
    P(m, 'motor_base', 'Motor Pedestal', 'baseplate', mbase, explode=(0, 0, -0.3), ref='fly_frame', section='keep')
    m.flow('power', [(-1.1, 0, CZ), (-0.55, 0, CZ), (0.0, 0, CZ + Rf - 0.04), (0.35, 0, CZ), (0.69, 0, CZ - 0.08), (0.69, 0, 0.2)], 'power', 0.01, 0.2)
    return m.export(out)


# =============================================================== EQ-170 Rotor assembly
def rotor_assembly(out):
    m = _model('rotor_assembly', 'Multistage Pump Rotor Assembly on a Balancing Stand')
    CZ = 0.5
    xs = [-0.3, -0.12, 0.06, 0.24]
    sh = cyl('sh', 0.03, -0.75, 0.78, 'steel', 48, axis='X', center=(0, 0, CZ), ch=0.003)
    psh = P(m, 'shaft', 'Shaft (stepped, ground journals)', 'rotating_element', sh, explode=(0, 0, 0), ref='ra_shaft', section='keep', pivot=(0, 0, CZ))
    psh.spin('X', 2)
    for i, x in enumerate(xs):
        prof_back = lathe(f'ib{i}', [(0.032, x + 0.04), (0.14, x + 0.03), (0.14, x + 0.04), (0.032, x + 0.05)], 'bronze', 64, axis='X', center=(0, 0, CZ))
        shroud = lathe(f'is{i}', [(0.06, x - 0.025), (0.066, x - 0.025), (0.14, x + 0.004), (0.14, x + 0.012), (0.06, x - 0.017)], 'bronze', 64, axis='X', center=(0, 0, CZ))
        hub = cyl(f'ih{i}', 0.045, x - 0.0, x + 0.05, 'bronze', 32, axis='X', center=(0, 0, CZ))
        bl = radial_blades(f'ibl{i}', -0.008, 0.008, 0.05, 0.138, 6, 'bronze', curve=0.9, t=0.005)
        bl = rotate(bl, -math.pi / 2, 'Z')
        bl.data.transform(Matrix.Translation((x + 0.022, 0, CZ)))
        pi_ = P(m, f'impeller_{i + 1}', f'Impeller Stage {i + 1} (keyed)', 'rotating_element', [prof_back, shroud, hub, bl], explode=(0.12 * (i + 1), 0, 0.42),
                ref='ra_impeller', section='split', pivot=(0, 0, CZ))
        pi_.spin('X', 2)
        if i < 3:
            sv = cyl(f'sv{i}', 0.04, x + 0.05, xs[i + 1], 'stainless', 32, axis='X', center=(0, 0, CZ))
            ps = P(m, f'sleeve_{i + 1}', f'Interstage Sleeve {i + 1}', 'rotating_element', sv, explode=(0.12 * (i + 1) + 0.06, 0, 0.25), ref='ra_sleeve', section='split', pivot=(0, 0, CZ))
            ps.spin('X', 2)
    bd = cyl('bd', 0.075, 0.32, 0.42, 'chrome', 48, axis='X', center=(0, 0, CZ))
    pb = P(m, 'balance_drum', 'Balance Drum (axial thrust balancing)', 'rotating_element', bd, explode=(0.6, 0, 0.3), ref='ra_balance_drum', section='split', pivot=(0, 0, CZ))
    pb.spin('X', 2)
    tc = cyl('tc', 0.09, 0.58, 0.61, 'steel', 48, axis='X', center=(0, 0, CZ))
    ln = [hex_prism(f'ln{i}', 0.07, x, x + 0.02, 'steel_dark', axis='X', center=(0, 0, CZ)) for i, x in enumerate((0.43, 0.615))]
    pt = P(m, 'thrust_collar', 'Thrust Collar & Locknuts', 'rotating_element', [tc] + ln, explode=(0.8, 0, 0.2), ref='ra_thrust_collar', section='keep', pivot=(0, 0, CZ))
    pt.spin('X', 2)
    ch = join('ch', [cyl('chh', 0.07, -0.74, -0.66, 'steel', 48, axis='X', center=(0, 0, CZ)), box('ky', (0.08, 0.012, 0.01), (-0.7, 0, CZ + 0.032), 'steel_dark')])
    pc = P(m, 'coupling_hub', 'Coupling Hub & Key (shrink fit)', 'rotating_element', ch, explode=(-0.5, 0, 0.2), ref='ra_coupling_hub', section='keep', pivot=(0, 0, CZ))
    pc.spin('X', 2)
    stand = []
    for x in (-0.55, 0.52):
        stand += [box(f'st{x}', (0.08, 0.3, CZ - 0.06 - 0.1), (x, 0, 0.1 + (CZ - 0.16) / 2), 'paint_blue'),
                  cyl(f'rl{x}a', 0.03, x - 0.03, x + 0.03, 'chrome', 32, axis='X', center=(0, 0.045, CZ - 0.06)),
                  cyl(f'rl{x}b', 0.03, x - 0.03, x + 0.03, 'chrome', 32, axis='X', center=(0, -0.045, CZ - 0.06))]
    stand += [box('bed', (1.6, 0.5, 0.1), (0, 0, 0.05), 'cast_iron'), box('sens', (0.04, 0.06, 0.05), (-0.55, 0.12, CZ - 0.13), 'paint_yellow')]
    P(m, 'balancing_stand', 'Balancing Machine: Roller Supports, Bed & Vibration Sensors', 'structure', stand, explode=(0, 0, -0.3), ref='ra_stand', section='keep')
    planes = [cyl(f'cp{i}', 0.16, x - 0.004, x + 0.004, 'paint_yellow', 64, axis='X', center=(0, 0, CZ), r_in=0.15) for i, x in enumerate((xs[0], xs[-1]))]
    planes += [cone_arrow('ua', (xs[0], 0, CZ + 0.17), (0, 0, 1), 0.06, 0.02, 'paint_red'), cone_arrow('ub', (xs[-1], 0, CZ - 0.17), (0, 0, -1), 0.06, 0.02, 'paint_red')]
    m.overlay('balance', join('bal', planes), 'Two-plane balancing', 'The rotor is spun on the balancing machine; sensors measure the vibration at each support. '
              'Correction weights are removed or added in two planes (yellow) so that both static and couple unbalance (red) are within the ISO 21940-11 grade (e.g. G2.5).')
    m.annotate('balance', 'Correction plane 1', (xs[0], 0, CZ + 0.27))
    m.annotate('balance', 'Correction plane 2', (xs[-1], 0, CZ - 0.27))
    path = [(-0.4, 0, CZ + 0.07)]
    for x in xs:
        path += [(x - 0.03, 0, CZ + 0.065), (x + 0.01, 0, CZ + 0.14), (x + 0.07, 0, CZ + 0.15), (x + 0.12, 0, CZ + 0.07)]
    m.flow('liquid_through_stages', path + [(0.33, 0, CZ + 0.12)], 'flow_discharge', 0.006, 0.08)
    return m.export(out)


# ===================================================================== metadata
def _std(*items):
    return [{'id': i, 'title': t, 'relevance': r, 'edition': 'to be verified'} for i, t, r in items]


_GEN = {
    'gen_frame': C('Supports the stator, holds the bearings and protects the windings.', 'Fabricated frame with end shields, feet and terminal box.', 'Steel.', 'IP rating per site.', ['Corrosion', 'Loose feet'], ['Visual, soft-foot check']),
    'gen_stator': C('Carries the 3-phase armature winding in which the voltage is induced.', 'Laminated core with slots; insulated copper coils, end windings.', 'Electrical steel; copper; class F/H insulation.',
                    'Winding temperature limits output.', ['Insulation breakdown', 'Hot spots'], ['Insulation resistance (IR/PI), thermography']),
    'gen_rotor': C('Produces the magnetic field (DC excited) and is turned by the prime mover.', 'Salient poles with field coils; exciter armature and rotating rectifier on the shaft.', 'Steel; copper.',
                   'Balanced; overspeed tested.', ['Field winding shorts', 'Diode failure'], ['Field resistance, diode test']),
    'gen_exciter': C('Brushless exciter: supplies the rotor field current via rotating diodes.', 'Small AC generator stator.', 'Steel, copper.', 'Controlled by the AVR.', ['Loss of excitation'], ['AVR checks']),
}
_ENG = {
    'engine_block': C('Holds the cylinders and crankshaft; contains coolant passages and the oil sump.', 'Cast block and crankcase.', 'Cast iron.', '—', ['Cracks, liner wear'], ['Compression test, oil analysis']),
    'engine_head': C('Closes the cylinders and carries valves and injectors/spark plugs.', 'Cast head with valve train.', 'Cast iron/aluminium.', '—', ['Valve leakage, gasket failure'], ['Valve clearance, compression']),
    'engine_crankshaft': C('Turns the up-and-down motion of the pistons into rotation.', 'Forged crankshaft with throws and counterweights.', 'Forged steel.', '—', ['Bearing wear'], ['Oil pressure, analysis']),
    'engine_pistons': C('Transmit combustion pressure to the connecting rods.', 'Pistons with rings and gudgeon pins.', 'Aluminium alloy/steel.', '—', ['Ring wear, scuffing'], ['Blow-by, oil consumption']),
    'engine_conrods': C('Link the pistons to the crankshaft.', 'Forged rods with big-end bearings.', 'Forged steel.', '—', ['Big-end bearing failure'], ['Oil analysis']),
}

META = {
    'engine_driven_generator': {
        'summary': ('An engine-driven generator uses a reciprocating engine as the prime mover to turn a generator. In this spark-ignition gas engine, fuel–air mixture '
                    'burns in each cylinder and pushes the pistons down; the crankshaft turns the flywheel and the generator rotor, which induces AC voltage in the stator. '
                    'The governor holds the speed constant so the frequency stays at 50 or 60 Hz.'),
        'classification': {'family': 'Prime mover + generator', 'type': 'Gas-engine generating set (inline-4, spark ignition)'},
        'model_configuration': {'engine': 'Inline 4-cylinder, 4-stroke', 'speed': '1500 rpm (50 Hz, 4-pole) typical', 'cooling': 'Radiator with engine-driven fan'},
        'standards': _std(('ISO 8528', 'Reciprocating internal combustion engine driven AC generating sets', 'Ratings, performance classes.'),
                          ('IEC 60034-1', 'Rotating electrical machines — Rating and performance', 'Generator rating.')),
        'references': ['Manufacturer generating-set application guides (generic)'],
        'components': {**_ENG, **_GEN,
            'edg_flywheel': C('Smooths the engine\'s pulsating torque and carries the starter ring gear.', 'Heavy cast disc bolted to the crankshaft.', 'Cast iron/steel.', '—', ['Ring gear wear'], ['Inspect teeth']),
            'edg_radiator': C('Rejects engine heat from the coolant to air.', 'Finned tube core with tanks.', 'Aluminium/copper.', '—', ['Clogged fins, leaks'], ['Clean, pressure test']),
            'edg_fan': C('Pulls air through the radiator.', 'Engine-driven axial fan.', 'Steel/plastic.', '—', ['Blade damage'], ['Inspect']),
            'edg_exhaust': C('Carries exhaust gas away.', 'Manifold and outlet.', 'Cast iron/steel.', 'Hot surface.', ['Leaks'], ['Inspect']),
            'edg_panel': C('Controls, protects and synchronises the set.', 'Controller with AVR, governor interface and breaker.', '—', '—', ['Faults'], ['Function tests']),
        },
    },
    'alternator': {
        'summary': ('An alternator (synchronous AC generator) produces alternating current when its rotor field turns inside the stator winding. In a brushless design '
                    'a small exciter on the same shaft generates AC that rotating diodes rectify to feed the main rotor poles — no brushes or slip rings. The AVR '
                    'adjusts the exciter field to hold the output voltage constant.'),
        'classification': {'family': 'Electrical machine', 'type': 'Brushless synchronous generator, salient 4-pole rotor'},
        'model_configuration': {'poles': 4, 'frequency_rule': 'f = p × n / 120', 'excitation': 'Brushless exciter + rotating rectifier + AVR'},
        'standards': _std(('IEC 60034-1', 'Rotating electrical machines — Rating and performance', 'Ratings, temperature rise.'), ('NEMA MG 1', 'Motors and Generators', 'North American practice.'),
                          ('ISO 8528-3', 'Generating sets — AC generators', 'Generator requirements for gensets.')),
        'references': ['Chapman, Electric Machinery Fundamentals', 'Manufacturer alternator technical guides (generic)'],
        'components': {**_GEN,
            'alt_avr': C('Measures output voltage and adjusts the exciter field current.', 'Electronic regulator in the terminal box.', 'Electronics.', '—', ['Voltage hunting'], ['Set-point check']),
            'alt_hub': C('Connects the alternator to the prime mover.', 'Coupling disc / hub.', 'Steel.', 'Single-bearing alternators bolt to the engine flywheel.', ['—'], ['Alignment']),
        },
    },
    'diesel_generator_set': {
        'summary': ('A diesel generator set (genset) is a complete power plant on a skid: a diesel engine (compression ignition — fuel is injected into hot compressed air '
                    'and ignites by itself) drives an alternator through a flywheel. Radiator, fuel tank in the base frame, exhaust silencer and a controller make it '
                    'self-contained for prime, continuous or standby (emergency) power.'),
        'classification': {'family': 'Prime mover + generator', 'type': 'Diesel genset, inline-6, turbocharged, base-frame fuel tank'},
        'model_configuration': {'engine': 'Inline 6, 4-stroke, turbocharged', 'ratings': 'Standby / prime / continuous per ISO 8528-1', 'mounting': 'Anti-vibration mounts'},
        'standards': _std(('ISO 8528-1…-13', 'RIC engine driven AC generating sets', 'Ratings and performance classes G1–G4.'), ('NFPA 110', 'Emergency and Standby Power Systems', 'Emergency gensets.'),
                          ('ISO 3046-1', 'Reciprocating internal combustion engines — Performance', 'Engine ratings and site derating.')),
        'references': ['Caterpillar / Cummins genset application manuals (generic principles)'],
        'components': {**_ENG, **_GEN,
            'edg_flywheel': C('Smooths torque pulses and couples to the alternator.', 'Cast flywheel in SAE housing.', 'Cast iron.', '—', ['—'], ['—']),
            'edg_radiator': C('Cools engine jacket water and charge air.', 'Radiator + charge-air cooler.', 'Aluminium/copper.', 'Sized for site ambient.', ['Fouling'], ['Clean fins']),
            'edg_fan': C('Moves cooling air through the radiator.', 'Pusher/puller fan.', 'Steel/plastic.', '—', ['Belt wear'], ['Belt tension']),
            'edg_panel': C('Starts, stops, protects and synchronises the genset.', 'Digital controller, breaker.', '—', 'Auto-start on mains failure (standby).', ['Faults'], ['Weekly test run']),
            'dg_turbo': C('Uses exhaust energy to compress intake air for more power.', 'Turbine and compressor wheels on one shaft.', 'Ni-alloy turbine, aluminium compressor.', 'Very high speed.', ['Bearing wear, oil leaks'], ['Boost pressure']),
            'dg_base': C('Supports the engine and alternator, holds the fuel and isolates vibration.', 'Fabricated base with integral tank and AVMs.', 'Steel, rubber.', '—', ['Leaks, perished mounts'], ['Inspect']),
            'dg_silencer': C('Reduces exhaust noise and carries gas away safely.', 'Bellows, pipe and residential/critical silencer.', 'Steel.', 'Back-pressure limit.', ['Corrosion'], ['Back-pressure check']),
        },
    },
    'variable_frequency_drive': {
        'summary': ('A variable frequency drive (VFD, inverter) controls the speed of an AC motor by changing the frequency and voltage it supplies. The rectifier turns mains '
                    'AC into DC, the DC link capacitors smooth it, and the IGBT inverter switches the DC rapidly (PWM) to build a new AC waveform of any frequency. '
                    'Running pumps and fans at reduced speed instead of throttling saves a lot of energy (affinity laws: power ∝ speed³).'),
        'classification': {'family': 'Power electronic motor drive', 'type': 'Voltage-source inverter, 6-pulse diode front end, IGBT PWM'},
        'model_configuration': {'animation': 'Motor speed ramps up, runs, and ramps down as the output frequency changes', 'overlay': 'Waveforms through the drive'},
        'standards': _std(('IEC 61800-2 / -3 / -5-1', 'Adjustable speed electrical power drive systems', 'Ratings, EMC, safety.'), ('IEEE 519', 'Harmonic control in electric power systems', 'Line harmonics.'),
                          ('IEC 60034-25', 'AC motors designed for converter supply', 'Motor insulation for PWM.')),
        'references': ['ABB / Siemens drive technical guides (generic principles)'],
        'components': {
            'vfd_enclosure': C('Protects the electronics and guides cooling air.', 'Steel cabinet with filtered vents.', 'Steel.', 'Ambient temperature derating.', ['Dust build-up'], ['Clean filters']),
            'vfd_reactor': C('Reduces line harmonics and protects against surges.', 'Three-phase iron-core choke.', 'Steel laminations, copper.', '—', ['Overheating'], ['Thermography']),
            'vfd_rectifier': C('Converts AC to DC.', 'Six-diode bridge module.', 'Silicon on ceramic.', '—', ['Diode failure'], ['Diode test']),
            'vfd_dc_link': C('Stores energy and smooths the DC voltage.', 'Electrolytic/film capacitors on bus bars.', 'Aluminium electrolytic, copper.', 'Capacitors age with heat.',
                             ['Capacitor ageing, bulging'], ['Capacitance/ripple check, reform if stored']),
            'vfd_inverter': C('Switches DC to make variable-frequency AC.', 'IGBT modules on a finned heatsink.', 'Silicon, copper, aluminium.', 'Switching frequency ~2–16 kHz.',
                              ['IGBT failure (overheat, short)'], ['Heatsink temperature, fault log']),
            'vfd_fan': C('Cools the heatsink.', 'Axial fan.', 'Plastic.', 'Wear item.', ['Bearing failure'], ['Replace on schedule']),
            'vfd_control': C('Generates PWM, controls speed/torque, protects motor and drive.', 'Microcontroller board and keypad.', 'Electronics.', '—', ['Parameter errors'], ['Backup parameters']),
            'vfd_terminals': C('Connect mains and motor.', 'Terminals and screened cable.', 'Copper.', 'Screened cable reduces EMC.', ['Loose terminals'], ['Torque check']),
        },
    },
    'soft_starter': {
        'summary': ('A soft starter reduces the starting current and torque shock of an AC motor. Anti-parallel thyristor (SCR) pairs in each phase let through only part of '
                    'each half-cycle at first (reduced voltage); the firing angle is advanced over the ramp time until full voltage is reached, then a bypass contactor '
                    'closes. Unlike a VFD, it does not change the running speed — only how the motor starts and stops.'),
        'classification': {'family': 'Power electronic motor starter', 'type': '3-phase controlled soft starter with internal bypass'},
        'model_configuration': {'animation': 'Motor accelerates smoothly during the ramp; bypass contacts close; motor then coasts to stop'},
        'standards': _std(('IEC 60947-4-2', 'Low-voltage switchgear — AC semiconductor motor controllers and starters', 'Soft starters.'),),
        'references': ['ABB / Schneider soft starter application guides (generic)'],
        'components': {
            'ss_enclosure': C('Houses the starter.', 'Steel enclosure.', 'Steel.', '—', ['Dust'], ['Clean']),
            'ss_scr': C('Control the voltage applied during start/stop by phase-angle firing.', 'Anti-parallel thyristors per phase on heatsinks.', 'Silicon, aluminium.', 'Heat generated only during ramp.',
                        ['Thyristor short/open'], ['SCR test']),
            'ss_ct': C('Measure motor current for current-limit and protection.', 'Toroidal current transformers.', '—', '—', ['—'], ['—']),
            'ss_bypass': C('Short-circuits the SCRs after start to eliminate losses.', 'Contactor with main contacts.', 'Silver-alloy contacts.', '—', ['Contact wear'], ['Inspect contacts']),
            'ss_control': C('Sets ramp time, initial voltage, current limit; provides protection.', 'Control module with display.', 'Electronics.', '—', ['—'], ['—']),
            'ss_terminals': C('Line and motor connections.', 'Terminals.', 'Copper.', '—', ['Loose'], ['Torque check']),
        },
    },
    'magnetic_coupling': {
        'summary': ('A magnetic coupling transmits torque through a sealed wall without any shaft seal. Permanent magnets on an outer rotor (on the motor shaft) attract the '
                    'opposite poles of magnets on an inner rotor (on the pump or mixer shaft). A thin, non-magnetic containment shell separates the two, so the process '
                    'fluid is completely sealed — ideal for toxic, flammable or valuable liquids.'),
        'classification': {'family': 'Coupling (non-contact)', 'type': 'Synchronous coaxial permanent-magnet coupling'},
        'model_configuration': {'magnets': '12 per rotor, alternating N/S', 'shell': 'Stainless (eddy-current losses) — non-metallic shells avoid losses'},
        'standards': _std(('API 685', 'Sealless Centrifugal Pumps', 'Magnetic drive pumps.'),),
        'references': ['Manufacturer magnetic coupling guides (generic)'],
        'components': {
            'mc_outer': C('Carries the driving magnets.', 'Steel cup with bonded magnets.', 'Steel; NdFeB or SmCo magnets.', 'Magnets lose strength above their temperature limit.', ['Demagnetisation'], ['Torque check']),
            'mc_can': C('Seals the process side from atmosphere.', 'Thin-walled shell.', 'Stainless, Hastelloy, PEEK/ceramic.', 'Metal shells heat up from eddy currents.', ['Rubbing → leak'], ['Clearance, temperature']),
            'mc_inner': C('Carries the driven magnets on the load shaft.', 'Encapsulated magnet rotor.', 'Steel/stainless; magnets.', '—', ['Decoupling on overload'], ['—']),
            'mc_bearings': C('Support each shaft.', 'Bearing housings.', 'Cast iron.', '—', ['Wear'], ['Vibration']),
        },
    },
    'torque_limiter': {
        'summary': ('A torque limiter protects machines from overload. In this friction type, disc springs clamp a sprocket between friction facings on a hub. Up to the set '
                    'torque everything turns together; if the driven machine jams, the facings slip so the motor and gearbox are not damaged. The slip torque is set by '
                    'tightening the adjusting nut.'),
        'classification': {'family': 'Overload protection device', 'type': 'Friction slip clutch with chain sprocket'},
        'model_configuration': {'animation': 'Normal drive for half the loop, then the sprocket stops (jam) while the hub keeps turning'},
        'standards': _std(('Manufacturer setting data', 'Torque setting charts', 'Slip torque vs nut position.'),),
        'references': ['Manufacturer torque limiter catalogues (generic)'],
        'components': {
            'tl_hub': C('Mounted on the driving shaft; carries the friction facings and springs.', 'Hub with flange and threaded end.', 'Steel.', '—', ['Wear on bush seat'], ['Inspect']),
            'tl_facings': C('Transmit torque by friction and slip on overload.', 'Friction linings.', 'Non-asbestos organic / sintered.', 'Keep free of oil.', ['Glazing, wear'], ['Slip test']),
            'tl_sprocket': C('Driven member that transmits power to the chain.', 'Sprocket on a bush between the facings.', 'Steel.', '—', ['Tooth wear'], ['Inspect']),
            'tl_springs': C('Provide the clamping force that sets the slip torque.', 'Pressure plate, Belleville springs and adjusting nut with lock screws.', 'Spring steel.', '—', ['Fatigue'], ['Re-set torque']),
            'tl_chain': C('Carries power to the driven machine.', 'Roller chain.', 'Steel.', '—', ['Wear elongation'], ['Measure elongation']),
            'tl_bearings': C('Support the shaft.', 'Bearings.', 'Cast iron.', '—', ['—'], ['—']),
        },
    },
    'speed_reducer': {
        'summary': ('A speed reducer (gearbox) lowers speed and raises torque between a motor and a slow machine. In this two-stage helical reducer, a 16-tooth pinion drives a '
                    '32-tooth gear (2:1), and a 15-tooth pinion on the same intermediate shaft drives a 45-tooth gear (3:1) — 6:1 overall. Helical teeth run quietly and '
                    'carry high loads; the gears dip into an oil bath for lubrication.'),
        'classification': {'family': 'Gear drive', 'type': 'Parallel-shaft helical reducer, two stages'},
        'model_configuration': {'ratio': '2 × 3 = 6:1', 'teeth': '16/32, 15/45', 'lubrication': 'Splash (oil bath)'},
        'standards': _std(('AGMA 6013 / 6113', 'Industrial enclosed gear drives', 'Rating and design.'), ('ISO 6336', 'Calculation of load capacity of spur and helical gears', 'Gear rating.'),
                          ('AGMA 9005', 'Industrial gear lubrication', 'Lubricant selection.')),
        'references': ['Dudley, Handbook of Practical Gear Design'],
        'components': {
            'sr_housing': C('Holds the shafts in alignment, contains the oil.', 'Split cast housing with bearing bores.', 'Cast iron.', '—', ['Oil leaks, cracks'], ['Visual']),
            'sr_oil': C('Lubricates and cools gears and bearings.', 'Oil bath.', 'Mineral/synthetic gear oil (ISO VG per AGMA 9005).', 'Level and temperature critical.', ['Degradation, contamination'], ['Oil analysis']),
            'sr_input': C('High-speed input shaft with first pinion.', 'Integral pinion shaft.', 'Case-hardened alloy steel.', '—', ['Pitting'], ['Vibration, borescope']),
            'sr_intermediate': C('Transfers torque between the two stages.', 'Shaft with gear and pinion.', 'Case-hardened steel.', '—', ['Pitting'], ['As above']),
            'sr_output': C('Low-speed, high-torque output.', 'Shaft with large gear and keyway.', 'Alloy steel.', '—', ['Key wear'], ['Inspect']),
            'sr_bearings': C('Support shafts and carry helical axial loads.', 'Taper-roller / ball bearings.', 'Bearing steel.', '—', ['Fatigue'], ['Vibration']),
            'sr_breather': C('Vents pressure and allows filling/draining.', 'Breather, plugs.', 'Brass.', '—', ['Blocked breather'], ['Clean']),
        },
    },
    'belt_drive_assembly': {
        'summary': ('A V-belt drive transmits power between parallel shafts by friction between wedge-shaped belts and grooved sheaves. The speed ratio equals the ratio of '
                    'sheave diameters (here 2.5:1). Belts are tensioned by sliding the motor on its base; a guard protects people. Belt drives are simple, quiet, '
                    'absorb shock and allow speed changes by changing sheaves.'),
        'classification': {'family': 'Mechanical drive', 'type': 'Multi-groove classical/narrow V-belt drive'},
        'model_configuration': {'belts': 3, 'ratio': '2.5:1', 'tensioning': 'Motor slide base with screw'},
        'standards': _std(('ISO 4184', 'Belt drives — Classical and narrow V-belts — Lengths', 'Belt sizes.'), ('ISO 5292', 'V-belts — Calculation of power ratings', 'Rating.'),
                          ('RMA/MPTA IP-20/22', 'V-belt drive engineering standards', 'Design and installation.')),
        'references': ['Gates / Fenner V-belt drive design manuals (generic)'],
        'components': {
            'bd_sheave': C('Grip the belts and transmit torque.', 'Grooved cast-iron pulleys on taper bushes.', 'Cast iron.', 'Groove wear causes slip.', ['Groove wear'], ['Groove gauge']),
            'bd_belts': C('Transmit power by friction in the grooves.', 'Matched set of V-belts.', 'Rubber with polyester cords.', 'Replace as a matched set.', ['Slip, cracking, stretch'], ['Tension (deflection) check']),
            'bd_slide_base': C('Allows belt tensioning and alignment.', 'Slide rails with adjusting screw.', 'Steel.', '—', ['Misalignment'], ['Laser/straight-edge alignment']),
            'bd_bearings': C('Support the driven shaft.', 'Plummer blocks.', 'Cast iron.', 'Belt pull loads the bearings.', ['Overheating'], ['Temperature']),
            'bd_guard': C('Prevents contact with moving parts.', 'Enclosing guard.', 'Steel mesh/sheet.', 'Required by machinery safety rules.', ['Missing guard'], ['Check before start']),
        },
    },
    'chain_drive_assembly': {
        'summary': ('A roller chain drive transmits power positively (no slip) between sprockets. Rollers seat in the sprocket tooth gaps, so the speed ratio is exactly the tooth '
                    'ratio (30/15 = 2:1). Chains handle high torque at low speed; they need lubrication and correct slack, provided here by a drip lubricator and an idler '
                    'tensioner on the slack side.'),
        'classification': {'family': 'Mechanical drive', 'type': 'Simplex roller chain drive with idler'},
        'model_configuration': {'teeth': '15 / 30', 'links': 62, 'pitch_mm': 30},
        'standards': _std(('ISO 606', 'Short-pitch transmission precision roller chains and sprockets', 'Chain and sprocket dimensions.'), ('ANSI B29.1', 'Precision power transmission roller chains', 'US sizes.')),
        'references': ['Renold / Tsubaki chain drive design guides (generic)'],
        'components': {
            'cd_sprocket': C('Engage the chain rollers to transmit torque.', 'Toothed wheels with hubs.', 'Steel, induction-hardened teeth.', 'Odd tooth count on small sprocket evens wear.', ['Hooked teeth'], ['Tooth profile check']),
            'cd_chain': C('Carries the load between sprockets.', 'Rollers, bushes, pins, inner and outer link plates.', 'Alloy steel.', 'Replace at ~3 % elongation (typical).', ['Elongation, stiff links'], ['Measure elongation']),
            'cd_tensioner': C('Takes up slack and limits whip.', 'Spring-loaded idler sprocket.', 'Steel.', 'On the slack side.', ['Wear'], ['Check slack']),
            'cd_lubricator': C('Supplies oil to the chain joints.', 'Drip oiler.', 'Glass/brass.', 'Lubrication method depends on chain speed.', ['Dry running'], ['Check drip rate']),
            'bd_slide_base': C('Supports motor and shafts.', 'Base frame.', 'Steel.', '—', ['—'], ['—']),
            'bd_bearings': C('Support the driven shaft.', 'Plummer blocks.', 'Cast iron.', '—', ['—'], ['—']),
            'bd_guard': C('Prevents contact with the chain.', 'Guard.', 'Steel.', '—', ['—'], ['—']),
        },
    },
    'flywheel_assembly': {
        'summary': ('A flywheel is a heavy rotating wheel that stores kinetic energy (E = ½ I ω²). In this crank press the motor slowly keeps the flywheel spinning; when the '
                    'punch strikes, the flywheel gives up some energy and slows down a little, delivering a much larger peak power than the motor alone could. Between '
                    'strokes the motor brings it back up to speed. Flywheels also smooth the uneven torque of engines.'),
        'classification': {'family': 'Mechanical energy storage', 'type': 'Spoked cast-iron flywheel on a crank press'},
        'model_configuration': {'animation': 'Flywheel slows briefly at each punch stroke and recovers', 'rim': 'Most of the mass at the rim → high inertia'},
        'standards': _std(('ISO 16092', 'Machine tools safety — Presses', 'Press safety.'),),
        'references': ['Shigley, Mechanical Engineering Design — flywheels'],
        'components': {
            'fly_flywheel': C('Stores energy and evens out speed.', 'Rim, spokes and hub keyed to the shaft.', 'Cast iron / steel.', 'Rim speed limited by burst strength.', ['Cracks, loose key'], ['NDT, key check']),
            'fly_shaft': C('Carries the flywheel and crank.', 'Shaft with crank disc and pin.', 'Forged steel.', '—', ['Fatigue'], ['NDT']),
            'fly_rod': C('Converts crank rotation to ram motion.', 'Connecting rod (pitman).', 'Steel.', '—', ['Bearing wear'], ['Inspect']),
            'fly_ram': C('The load: punches the workpiece.', 'Ram with punch in guides.', 'Steel.', '—', ['Guide wear'], ['Gib adjustment']),
            'fly_frame': C('Supports the mechanism.', 'Frame and guides.', 'Steel/cast iron.', '—', ['—'], ['—']),
            'fly_bearings': C('Support the shaft.', 'Pedestal bearings.', 'Cast iron.', '—', ['Wear'], ['Temperature']),
        },
    },
    'rotor_assembly': {
        'summary': ('A rotor assembly is the complete rotating part of a machine — here a multistage pump rotor: shaft, impellers, interstage sleeves, balance drum, thrust collar, '
                    'locknuts and coupling hub. Each part is fitted in sequence with controlled fits, keys and stack-up; the assembled rotor is then dynamically balanced '
                    'in two planes before it goes into the casing.'),
        'classification': {'family': 'Rotating component assembly', 'type': 'Between-bearings multistage pump rotor on balancing machine'},
        'model_configuration': {'stages': 4, 'balancing': 'Two-plane dynamic balancing (ISO 21940-11)', 'explode': 'Shows assembly order along the shaft'},
        'standards': _std(('ISO 21940-11', 'Mechanical vibration — Rotor balancing — Rigid rotors', 'Balance quality grades.'), ('API 610 (Sect. 6.9 / 9)', 'Rotor balance and run-out requirements', 'Pump rotors.')),
        'references': ['Bloch & Geitner, Machinery Component Maintenance and Repair'],
        'components': {
            'ra_shaft': C('Carries all rotating parts and transmits torque.', 'Stepped, ground shaft with keyways.', 'Alloy/stainless steel.', 'Run-out limits at journals.', ['Bend, fretting'], ['Run-out check']),
            'ra_impeller': C('Add energy to the liquid in each stage.', 'Closed impellers keyed and shrunk/slid on the shaft.', 'Bronze, stainless.', '—', ['Wear, imbalance'], ['Balance, inspect']),
            'ra_sleeve': C('Locate impellers axially and protect the shaft.', 'Interstage sleeves.', 'Stainless.', 'Stack-up sets impeller positions.', ['Wear'], ['Measure']),
            'ra_balance_drum': C('Counteracts the axial thrust of the impellers.', 'Drum running in a close-clearance bush.', 'Hardened stainless.', '—', ['Clearance wear'], ['Measure clearance']),
            'ra_thrust_collar': C('Transfers residual thrust to the thrust bearing; locknuts lock the stack.', 'Collar and locknuts.', 'Steel.', '—', ['Loose nut'], ['Torque, lock']),
            'ra_coupling_hub': C('Connects to the driver coupling.', 'Hub with key, shrink fit.', 'Steel.', '—', ['Fretting'], ['Fit check']),
            'ra_stand': C('Supports and spins the rotor to measure unbalance.', 'Balancing machine with roller supports and sensors.', 'Steel.', '—', ['—'], ['Calibration']),
        },
    },
}

BUILDERS = {'engine_driven_generator': engine_driven_generator, 'alternator': alternator, 'diesel_generator_set': diesel_generator_set,
            'variable_frequency_drive': variable_frequency_drive, 'soft_starter': soft_starter, 'magnetic_coupling': magnetic_coupling,
            'torque_limiter': torque_limiter, 'speed_reducer': speed_reducer, 'belt_drive_assembly': belt_drive_assembly,
            'chain_drive_assembly': chain_drive_assembly, 'flywheel_assembly': flywheel_assembly, 'rotor_assembly': rotor_assembly}
