"""Vertical-pump building blocks (bowl stages, discharge case, suction bell, column),
generalised from the vertical turbine pump model.  Axis = Blender Z, cut plane y = 0.
Dimensions scale with `s` (s = 1 -> ~300 mm bowl OD)."""
import math
from .core import (lathe, lathe_split, ring_profile, cyl, box, join, split, rotate, merge_halves, group_by,
                   bolt_circle, split_faces, TAU)
from .shapes import vane, sweep_tube

H = 0.26
R_SH = 0.0215

BOWL = [(0.093, 0.0), (0.195, 0.0), (0.195, 0.022), (0.152, 0.034), (0.152, 0.226), (0.195, 0.238), (0.195, 0.26),
        (0.093, 0.26), (0.098, 0.235), (0.115, 0.205), (0.135, 0.17), (0.142, 0.135), (0.138, 0.115), (0.123, 0.094),
        (0.104, 0.062), (0.093, 0.032)]
BHUB = [(0.028, 0.134), (0.074, 0.134), (0.076, 0.15), (0.071, 0.18), (0.061, 0.215), (0.05, 0.245), (0.046, 0.258),
        (0.028, 0.258)]
D_HUB = [(0.075, 0.14), (0.071, 0.18), (0.061, 0.215), (0.05, 0.245)]
D_WALL = [(0.142, 0.14), (0.135, 0.17), (0.115, 0.205), (0.098, 0.235)]
I_HUB = [(0.0215, 0.005), (0.036, 0.005), (0.045, 0.04), (0.06, 0.085), (0.075, 0.12), (0.072, 0.128), (0.0215, 0.128)]
I_SHR = [(0.079, 0.002), (0.085, 0.002), (0.085, 0.028), (0.100, 0.060), (0.119, 0.092), (0.134, 0.112), (0.132, 0.118),
         (0.127, 0.116), (0.113, 0.097), (0.094, 0.066), (0.079, 0.034)]
B_HUB = [(0.04, 0.03), (0.05, 0.06), (0.063, 0.09), (0.075, 0.118)]
B_SHR = [(0.079, 0.034), (0.094, 0.066), (0.113, 0.097), (0.128, 0.116)]


def _S(pr, s, z0):
    return [(r * s, z * s + z0) for r, z in pr]


def nut_ring(name, n, pcd, af, h0, h1):
    o = bolt_circle(name, n, pcd, af, h0, h1, stud=(af * 0.62, h0 - 0.004 if h1 > h0 else h0 + 0.004,
                                                     h1 + 0.012 if h1 > h0 else h1 - 0.012))
    return split_faces(o, 'y', 0.0)


def radial_rib(name, r0, r1, z0, z1, ang, t, mat):
    o = box(name, (r1 - r0, t, z1 - z0), ((r0 + r1) / 2, 0, (z0 + z1) / 2), mat)
    return rotate(o, ang)


def bowl_stage(m, k, z0, s=1.0, mat='paint_blue', imp_mat='bronze', ex=None, x_rot=0.8, x_int=-0.7, revs=2,
               imp_blades=5, wrap=1.25, closed=True, label='Stage'):
    """One bowl (diffuser casing) + impeller + wear ring + bowl bearing + collet. Returns top z."""
    ex = ex or (lambda z, dx=0.0: (dx, 0, 0.35 * z))
    zc = z0 + H * s / 2
    wall = lathe_split(f'bowl{k}_wall', _S(BOWL, s, z0), mat, 96)
    hubp = lathe_split(f'bowl{k}_hub', _S(BHUB, s, z0), mat, 64)
    vanes = [vane(f'dv{k}_{i}', _S(D_HUB, s, z0), _S(D_WALL, s, z0),
                  lambda a, t, th0=TAU * i / 7 + 0.2: th0 + 0.55 * (1 - (1 - a) ** 2), 0.006 * s, mat, ns=14, nt=4)
             for i in range(7)]
    vb, vf = split(join(f'dvanes{k}', vanes))
    nb = nut_ring(f'bowl{k}_n', 8, 0.35 * s, 0.024 * s, z0 + 0.022 * s, z0 + 0.04 * s)
    p = m.part(f'bowl_{k}', f'Bowl – {label} {k}', 'bowl_assembly', section='split', explode=ex(zc), info={'ref': 'bowl'})
    p.add_split(*merge_halves(f'bowl_{k}', [wall, hubp, (vb, vf), nb]))
    p = m.part(f'wear_ring_{k}', f'Bowl Wear Ring – {label} {k}', 'bowl_assembly', section='split', explode=ex(zc, x_int * 0.5),
               info={'ref': 'wear_ring'})
    p.add_split(*lathe_split(f'wr{k}', ring_profile(0.0865 * s, 0.093 * s, z0 + 0.001 * s, z0 + 0.03 * s), 'bronze', 64))
    p = m.part(f'bowl_bearing_{k}', f'Bowl Bearing – {label} {k}', 'bearings', section='split', explode=ex(zc, x_int),
               info={'ref': 'bowl_bearing'})
    p.add_split(*lathe_split(f'bbr{k}', ring_profile(R_SH * s + 0.0005, 0.028 * s, z0 + 0.138 * s, z0 + 0.255 * s), 'bronze', 48))
    hubo = lathe(f'imp{k}_hub', _S(I_HUB, s, z0), imp_mat, 64)
    blades = [vane(f'ib{k}_{i}', _S(B_HUB, s, z0), _S(B_SHR, s, z0),
                   lambda a, t, th=TAU * i / imp_blades: th - wrap * a - 0.12 * t * a, 0.005 * s, imp_mat, ns=18, nt=5)
              for i in range(imp_blades)]
    p = m.part(f'impeller_{k}', f'Impeller – {label} {k}', 'rotating_element', explode=ex(zc, x_rot), info={'ref': 'impeller_mixed'})
    p.add(join(f'impeller_{k}', [hubo] + blades), 'keep')
    if closed:
        sb, sf = lathe_split(f'imp{k}_shroud', _S(I_SHR, s, z0), imp_mat, 96)
        p.add(sb, 'back').name = f'impeller_{k}_shroud__back'
        p.add(sf, 'front').name = f'impeller_{k}_shroud__front'
    p.spin('Z', revs)
    col = lathe(f'collet{k}', [(R_SH * s, z0 - 0.004 * s), (0.024 * s, z0 - 0.004 * s), (0.029 * s, z0 + 0.04 * s),
                               (R_SH * s, z0 + 0.04 * s)], 'steel', 32)
    p = m.part(f'collet_{k}', f'Taper Lock Collet – {label} {k}', 'rotating_element', explode=ex(zc - 0.12, x_rot), info={'ref': 'collet'})
    p.add(col); p.spin('Z', revs)
    return z0 + H * s


def discharge_case(m, zb, s=1.0, mat='paint_blue', ex=None, x_int=-0.7, top_r=0.101):
    ex = ex or (lambda z, dx=0.0: (dx, 0, 0.35 * z))
    S = lambda pr: [(r * s if r > 0.11 else r * s, zb + z * s) for r, z in pr]
    prof = [(0.093, 0), (0.195, 0), (0.195, 0.022), (0.132, 0.045), (0.13, 0.15), (0.122, 0.225), (0.17, 0.235), (0.17, 0.26),
            (top_r / s, 0.26), (top_r / s, 0.2), (0.113, 0.11), (0.111, 0.05), (0.098, 0.02)]
    dcs = [lathe_split('dcase', S(prof), mat, 96),
           lathe_split('dcase_hub', S([(0.028, 0), (0.047, 0), (0.047, 0.15), (0.035, 0.19), (0.028, 0.19)]), mat, 48)]
    ribs = [radial_rib(f'dr{i}', 0.04 * s, 0.112 * s, zb + 0.03 * s, zb + 0.15 * s, TAU * (i + 0.5) / 4, 0.012 * s, mat) for i in range(4)]
    dcs.append(group_by(ribs, 'dc_ribs'))
    dcs.append(nut_ring('dc_n', 8, 0.35 * s, 0.024 * s, zb + 0.022 * s, zb + 0.04 * s))
    dcs.append(nut_ring('dc_n2', 8, 0.29 * s, 0.03 * s, zb + 0.235 * s, zb + 0.215 * s))
    p = m.part('discharge_case', 'Discharge Case (Top Bowl)', 'bowl_assembly', section='split', explode=ex(zb + 0.13))
    p.add_split(*merge_halves('discharge_case', dcs))
    p = m.part('discharge_case_bearing', 'Discharge Case Bearing', 'bearings', section='split', explode=ex(zb + 0.1, x_int),
               info={'ref': 'bowl_bearing'})
    p.add_split(*lathe_split('dcb', ring_profile(R_SH * s + 0.0005, 0.028 * s, zb + 0.01 * s, zb + 0.18 * s), 'bronze', 48))
    return zb + 0.26 * s


def suction_bell(m, zb, s=1.0, mat='paint_blue', ex=None, x_int=-0.7, strainer=True, lip_r=0.222):
    """Bell below a bowl whose bottom face is at zb. Returns bottom z."""
    ex = ex or (lambda z, dx=0.0: (dx, 0, 0.35 * z))
    k = lip_r / 0.222
    pr = [(0.093, 0), (0.195, 0), (0.195, -0.022), (0.122, -0.04), (0.128, -0.12), (0.165 * k, -0.215), (0.212 * k, -0.268),
          (0.222 * k, -0.282), (0.214 * k, -0.292), (0.2 * k, -0.285), (0.155 * k, -0.235), (0.118, -0.135), (0.105, -0.05)]
    bs = [lathe_split('bell', [(r * s, zb + z * s) for r, z in pr], mat, 96),
          lathe_split('bell_hub', [(r * s, zb + z * s) for r, z in [(0.028, -0.02), (0.047, -0.02), (0.047, -0.22), (0.035, -0.25),
                                                                    (0.0, -0.255), (0.0, -0.24), (0.028, -0.24)]], mat, 48)]
    ribs = [radial_rib(f'br{i}', 0.04 * s, 0.125 * s, zb - 0.19 * s, zb - 0.06 * s, math.radians(a), 0.012 * s, mat)
            for i, a in enumerate((30, 150, 270))]
    bs.append(group_by(ribs, 'bell_ribs'))
    p = m.part('suction_bell', 'Suction Bell', 'bowl_assembly', section='split', explode=ex(zb - 0.15))
    p.add_split(*merge_halves('suction_bell', bs))
    p = m.part('bell_bearing', 'Suction Bell Bearing', 'bearings', section='split', explode=ex(zb - 0.13, x_int),
               info={'ref': 'bowl_bearing'})
    p.add_split(*lathe_split('bellb', ring_profile(R_SH * s + 0.0005, 0.028 * s, zb - 0.235 * s, zb - 0.025 * s), 'bronze', 48))
    zs = zb - 0.29 * s
    if strainer:
        rods = []
        for i in range(16):
            a = (i + 0.5) * TAU / 16
            rods.append(sweep_tube(f'rod{i}', [(0.212 * k * s * math.cos(a), 0.212 * k * s * math.sin(a), zs),
                                               (0.04 * s * math.cos(a), 0.04 * s * math.sin(a), zs - 0.24 * s)], 0.004, 'stainless', 8))
        rings = [lathe_split('srt', [(0.205 * k * s, zs - 0.004), (0.226 * k * s, zs - 0.004), (0.226 * k * s, zs + 0.01),
                                     (0.205 * k * s, zs + 0.01)], 'stainless', 96),
                 lathe_split('scap', [(0, zs - 0.25 * s), (0.05 * s, zs - 0.25 * s), (0.05 * s, zs - 0.235 * s), (0, zs - 0.235 * s)],
                             'stainless', 48), group_by(rods, 'rods')]
        p = m.part('strainer', 'Cone Strainer', 'bowl_assembly', section='split', explode=ex(zs - 0.35))
        p.add_split(*merge_halves('strainer', rings))
        return zs - 0.25 * s
    return zs


def column(m, pid, name, ztop, zbot, s=1.0, mat='paint_blue', ex=None, ref='column_pipe', note=None):
    ex = ex or (lambda z, dx=0.0: (dx, 0, 0.35 * z))
    r_i, r_o, r_f = 0.101 * s, 0.11 * s, 0.17 * s
    prof = [(r_i, zbot), (r_f, zbot), (r_f, zbot + 0.025), (0.125 * s, zbot + 0.03), (r_o, zbot + 0.045),
            (r_o, ztop - 0.045), (0.125 * s, ztop - 0.03), (r_f, ztop - 0.025), (r_f, ztop), (r_i, ztop)]
    b, f = lathe_split(pid, prof, mat, 96)
    nb, nf = nut_ring(pid + '_n', 8, 0.29 * s, 0.03 * s, ztop - 0.025, ztop - 0.045)
    info = {'ref': ref}
    if note:
        info['note'] = note
    p = m.part(pid, name, 'column', section='split', explode=ex((ztop + zbot) / 2), info=info)
    p.add_split(join(pid + 'b', [b, nb]), join(pid + 'f', [f, nf]))


def lineshaft_bearing(m, k, zr, s=1.0, ex=None, x_int=-0.7):
    ex = ex or (lambda z, dx=0.0: (dx, 0, 0.35 * z))
    ret = [lathe_split(f'ret{k}_rim', ring_profile(0.101 * s, 0.17 * s, zr - 0.01, zr + 0.01), 'bronze', 96),
           lathe_split(f'ret{k}_hub', ring_profile(0.028 * s, 0.045 * s, zr - 0.05, zr + 0.05, 0.003), 'bronze', 48)]
    ribs = [radial_rib(f'rr{k}{i}', 0.04 * s, 0.106 * s, zr - 0.035, zr + 0.008, TAU * (i + 0.5) / 4, 0.012 * s, 'bronze') for i in range(4)]
    ret.append(group_by(ribs, f'ret{k}_ribs'))
    p = m.part(f'bearing_retainer_{k}', f'Bearing Retainer (Spider) {k}', 'column', section='split', explode=ex(zr, x_int * 0.5),
               info={'ref': 'bearing_retainer'})
    p.add_split(*merge_halves(f'bearing_retainer_{k}', ret))
    p = m.part(f'lineshaft_bearing_{k}', f'Line-Shaft Bearing {k}', 'bearings', section='split', explode=ex(zr, x_int),
               info={'ref': 'lineshaft_bearing'})
    p.add_split(*lathe_split(f'lsb{k}', ring_profile(R_SH * s + 0.0005, 0.028 * s, zr - 0.048, zr + 0.048), 'rubber', 48))


def stage_flow(z0, s=1.0, sx=1, Y=0.012):
    rz = [(0.06, 0.0), (0.062, 0.03), (0.075, 0.06), (0.095, 0.095), (0.11, 0.12), (0.112, 0.15), (0.1, 0.18), (0.083, 0.215),
          (0.07, 0.25)]
    return [(sx * r * s, Y, z0 + z * s) for r, z in rz]


# engineering notes for the blocks above (merged by pump scripts)
from .common_meta import C
VERTICAL_META = {
    'bowl': C('Diffuser casing for one stage: converts swirl leaving the impeller into pressure and guides flow to the next impeller.',
              'Casting with integral diffuser vanes, bearing hub and bolted flanges; often enamel-lined for efficiency.',
              'Cast iron, ductile iron, bronze, stainless or duplex.',
              'Pressure rises stage by stage; the lowest stage needs adequate submergence/NPSH margin.',
              ['Vane erosion by sand', 'Corrosion', 'Wear-ring seat wear'], ['Passage erosion', 'Wear-ring clearance', 'Bearing bore']),
    'impeller_mixed': C('Adds energy to the liquid; mixed-flow blades discharge diagonally (between radial and axial).',
                        'Enclosed mixed-flow impeller fixed to the shaft by a taper collet (semi-open designs are set with axial clearance).',
                        'Bronze, cast iron, stainless steel, duplex.',
                        'Rotates at driver speed; produces head and axial down-thrust.',
                        ['Cavitation erosion at blade inlet', 'Abrasive wear', 'Loose collet'], ['Inlet edges', 'Skirt clearance', 'Collet seating']),
    'collet': C('Locks the impeller on the shaft by friction.', 'Split tapered sleeve driven into the impeller hub.', 'Steel or stainless steel.',
                'Must resist torque and thrust.', ['Slipping', 'Corrosion seizure'], ['Seating and contact pattern']),
    'bowl_bearing': C('Radial support of the pump shaft in each bowl, the discharge case and the suction bell.', 'Product-lubricated sleeve bushing.',
                      'Bronze, rubber, carbon, engineered polymers.', 'Lubricated by the pumped liquid.', ['Abrasive wear', 'Dry-run seizure'], ['Clearance at overhaul']),
    'discharge_case': C('Top bowl: collects flow from the last diffuser and turns it into the column.', 'Casting with straightening ribs and bearing hub.',
                        'Cast iron, bronze, stainless.', 'Full discharge pressure at bowl level.', ['Erosion', 'Hub wear'], ['Bore and bearing wear']),
    'suction_bell': C('Guides liquid smoothly into the first-stage impeller and holds the bottom bearing.', 'Bell-mouth casting with ribs and bearing hub.',
                      'Cast iron, bronze, stainless.', 'Submergence above the bell must satisfy intake design (ANSI/HI 9.8) to avoid vortices.',
                      ['Vortex/air entrainment', 'Erosion', 'Debris blockage'], ['Bell and ribs', 'Water level vs minimum submergence']),
    'strainer': C('Keeps large debris out of the pump.', 'Clip-on cone or basket strainer.', 'Galvanised or stainless steel.',
                  'Clogging raises inlet loss and reduces NPSHa.', ['Clogging', 'Corrosion'], ['Clean at each pull']),
    'column_pipe': C('Carries liquid from the bowls to the head and suspends the bowl assembly.', 'Flanged pipe sections with bearing retainers at joints.',
                     'Carbon, galvanised or stainless steel.', 'Internal pressure plus tensile load from suspended weight.',
                     ['Corrosion and wall loss', 'Leaking joints', 'Misalignment'], ['Wall thickness', 'Flange faces', 'Straightness']),
    'bearing_retainer': C('Holds the line-shaft bearing concentric at each column joint.', 'Rim clamped between flanges, radial ribs, central hub.',
                          'Bronze, cast iron, stainless.', 'Flow passes between ribs.', ['Rib erosion', 'Hub wear'], ['Hub bore at overhaul']),
    'lineshaft_bearing': C('Supports the line shaft radially between head and bowls.', 'Fluted rubber or bronze sleeve, product lubricated.',
                           'Nitrile/neoprene rubber, bronze, polymers.', 'Rubber bearings need pre-lubrication if dry at start.',
                           ['Dry-run burn-out', 'Abrasive wear'], ['Clearance at overhaul']),
    'line_shaft': C('Transmits torque from the driver to the bowl shaft.', 'Ground shaft sections joined by threaded couplings.',
                    'Carbon steel, 416/316 stainless.', 'Elongates under hydraulic thrust; allow for it when setting impeller lift.',
                    ['Thread unscrewing on reverse rotation', 'Journal wear', 'Bent shaft'], ['Straightness', 'Journal wear']),
    'shaft_couplings': C('Join shaft sections.', 'Threaded sleeve couplings (tighten with normal rotation).', 'Stainless or carbon steel.',
                         'Backspin can unscrew them.', ['Unscrewing', 'Galling'], ['Shaft ends butted; thread condition']),
    'thrust_bearing_v': C('Carries hydraulic down-thrust plus rotor/shaft weight.', 'Angular-contact pair or spherical roller thrust bearing in the motor top bracket.',
                          'Bearing steel.', 'Rated for maximum (shut-off) thrust and momentary up-thrust.', ['Overload', 'Lubricant breakdown'],
                          ['Temperature, oil level, vibration']),
}


def elbow_head(m, r_col, ex, x_noz=1.0, z_bend=0.6, mat='paint_blue', motor_R=0.26, motor_L=0.7, shaft_r=0.043, revs=2):
    """Above-floor fabricated discharge elbow + floor plate + stuffing box + motor stand + coupling + motor.
    Column flange at z = 0.  Returns dict."""
    from .core import csg, split, lathe, cyl, box, join, bolt_circle, split_faces, lathe_split, merge_halves
    from .parts import add_motor_v, nozzle_bolts, pipe
    t = 0.012
    R = r_col
    path = [(0, 0, -0.01), (0, 0, z_bend), (x_noz, 0, z_bend)]
    outs = [pipe('el_o', path, R + t, mat, 48, bend=R * 1.6),
            cyl('el_fl', R + 0.11, x_noz - 0.035, x_noz, mat, 64, axis='X', center=(0, 0, z_bend), ch=0.004),
            cyl('el_bfl', R + 0.11, 0.0, 0.035, mat, 64, ch=0.004),
            box('floor', (2.2 * R + 0.5, 2.2 * R + 0.5, 0.04), (0, 0, -0.02), 'paint_grey', bevel=0.006),
            cyl('boss', shaft_r * 2.4, z_bend, z_bend + R + 0.22, mat, 48, ch=0.004)]
    ins = [pipe('el_i', [(0, 0, -0.05)] + path[1:] + [(x_noz + 0.05, 0, z_bend)], R, mat, 48, bend=R * 1.6),
           cyl('bossb', shaft_r + 0.003, z_bend - 0.1, z_bend + R + 0.3, mat, 32)]
    hd = csg('elbow_head', outs, ins, mat)
    hb, hf = split(hd)
    bolts = [nozzle_bolts('elb_n', 12, 2 * (R + 0.075), 0.03, x_noz - 0.035, x_noz - 0.055, 'X', (0, 0, z_bend), math.pi / 12),
             nozzle_bolts('elb_b', 12, 2 * (R + 0.075), 0.03, 0.035, 0.055, 'Z', (0, 0, 0), math.pi / 12)]
    bb, bf = split_faces(join('elb_bolts', bolts), 'y', 0.0)
    p = m.part('discharge_elbow', 'Discharge Elbow Head & Floor Plate', 'discharge_head', section='split', explode=ex(0.6),
               info={'ref': 'discharge_elbow'})
    p.add_split(join('eb', [hb, bb]), join('ef', [hf, bf]), smooth_angle=40)
    zs = z_bend + R + 0.22
    sb, sf = merge_halves('packing', [lathe_split(f'pk{i}', ring_profile(shaft_r + 0.001, shaft_r * 2.4 - 0.004, zs - 0.09 + i * 0.016,
                                                                         zs - 0.076 + i * 0.016), 'ptfe', 48) for i in range(4)] +
                          [lathe_split('gl', [(shaft_r + 0.002, zs - 0.012), (shaft_r * 2.4 - 0.004, zs - 0.012), (shaft_r * 2.4 - 0.004, zs),
                                              (shaft_r * 3.4, zs), (shaft_r * 3.4, zs + 0.02), (shaft_r + 0.002, zs + 0.02)], 'steel', 48)])
    p = m.part('stuffing_box', 'Stuffing Box Packing & Gland', 'shaft_seal', section='split', explode=ex(zs, -0.6),
               info={'ref': 'gland_packing_v'})
    p.add_split(sb, sf)
    z1 = zs + 0.4
    st = csg('stand', [lathe('st', [(0.0, zs + 0.02), (shaft_r * 4.5, zs + 0.02), (shaft_r * 4.5, zs + 0.06), (motor_R * 0.8, zs + 0.1),
                                    (motor_R * 0.8, z1 - 0.04), (motor_R * 1.15, z1 - 0.03), (motor_R * 1.15, z1), (0, z1)], mat, 96)],
             [cyl('sti', motor_R * 0.72, zs + 0.11, z1 + 0.01, mat, 96), cyl('stb', shaft_r * 1.4, zs, zs + 0.12, mat, 48),
              box('stw', (motor_R * 0.9, motor_R * 2.5, 0.2), (0, 0, zs + 0.24), mat, bevel=0.02)], mat)
    p = m.part('motor_stand', 'Motor Stand', 'discharge_head', section='split', explode=ex(z1), info={'ref': 'motor_stand_v'})
    p.add_split(*split(st), smooth_angle=40)
    cp = lathe('cp', [(shaft_r, zs + 0.17), (shaft_r * 2.6, zs + 0.17), (shaft_r * 2.6, zs + 0.21), (shaft_r * 1.6, zs + 0.22),
                      (shaft_r * 1.6, zs + 0.25), (shaft_r * 2.6, zs + 0.26), (shaft_r * 2.6, zs + 0.3), (shaft_r, zs + 0.3)], 'steel', 64)
    p = m.part('coupling', 'Adjustable Spacer Coupling', 'power_transmission', pivot=(0, 0, zs + 0.23), explode=ex(z1, 0.8),
               info={'ref': 'coupling_vertical_s'})
    p.add(cp); p.spin('Z', revs)
    add_motor_v(m, 'm_', z1 + 0.025, motor_R, motor_L, shaft_r * 0.8, z1 + 0.025 - (zs + 0.27), explode_dz=0.9, revs=revs,
                flange_r=motor_R * 1.15)
    return dict(zs=zs, z_shaft_top=zs + 0.17)


VERTICAL_META.update({
    'discharge_elbow': C('Turns the flow from the vertical column into the horizontal discharge pipe, supports the pump from the floor and carries the motor.',
                         'Fabricated steel elbow welded to a floor (sole) plate, with stuffing-box boss where the shaft passes through the elbow wall.',
                         'Carbon steel, stainless; coated internally for seawater.', 'Carries thrust reaction and discharge pressure; elbow shape affects losses.',
                         ['Corrosion/erosion in the bend', 'Floor plate grout failure'], ['Coating condition', 'Anchor bolts']),
    'gland_packing_v': C('Seals the shaft where it leaves the discharge elbow.', 'Braided packing rings compressed by a split gland.',
                         'PTFE/aramid/graphite packing.', 'Requires slight leakage for cooling; mechanical seals are an alternative.',
                         ['Over-tightening, sleeve scoring', 'Excessive leakage'], ['Adjust gland for steady drip']),
    'motor_stand_v': C('Supports the vertical motor and gives access to coupling and gland.', 'Fabricated stand with windows.', 'Steel.',
                       'Stand + motor natural frequency must avoid running speed.', ['Reed resonance'], ['Vibration at motor top']),
    'coupling_vertical_s': C('Transmits torque and axial thrust to the motor thrust bearing; nut sets impeller/propeller axial position.',
                             'Adjustable spacer coupling.', 'Steel.', 'Carries full down-thrust.', ['Incorrect setting', 'Loose bolts'], ['Setting check']),
})
