"""Static Equipment — EQ-171 … EQ-179: heat exchangers, jacketed vessel and reactors."""
import math
from mathutils import Matrix, Vector
from pumpforge.core import Model, lathe, cyl, box, csg, split, join, rotate, extrude_poly, hex_prism, TAU, OPERATE_FRAMES
from pumpforge.valvekit import P, keys_loop, smooth_pulse, spring, sphere, shape_key, morph_loop
from pumpforge.parts import add_tracers, hollow_pipe, pressure_gauge
from pumpforge.vesselkit import (half, vessel, liquid, liquid_v, animate_level, nozzle, saddles, legs, skirt, mesh_pad, packing, tray, helix_coil, ladder, platform, droplets)
from pumpforge.rotkit import blade_row, ring_of, flow_ring
from pumpforge.shapes import sweep_tube, cone_arrow
from pumpforge.common_meta import C

CAT = '8 · Static Equipment – Additional Equipment'


def _model(pid, title):
    return Model(pid, title, CAT, META[pid])


def _temp_overlay(m, segs, title, desc, axis='X', r_in=0.0, r_out=0.0, cz=0.0, kind='temperature'):
    objs = []
    for i, (a, b, lev, rr) in enumerate(segs):
        objs.append(cyl(f'tb{i}', rr + 0.012, a, b, f'pressure_{lev}', 48, axis=axis, center=(0, 0, cz) if axis == 'X' else (0, 0, 0), r_in=rr + 0.004))
    m.overlay(kind, join(kind, objs), title, desc, split=True)


def _agitator(m, pid, name, z_top, z_imps, R_imp, cz_motor, kind='pbt', revs=2, ref='ag_agitator', mat='stainless'):
    """Top-entry agitator: drive (motor + gearbox), shaft and impellers about Z."""
    parts = [cyl(pid + 'sh', 0.025, min(z_imps) - 0.05, z_top + 0.25, mat, 24)]
    for k, z in enumerate(z_imps):
        parts.append(cyl(f'{pid}hb{k}', 0.05, z - 0.04, z + 0.04, mat, 32))
        if kind == 'rushton':
            parts.append(cyl(f'{pid}dk{k}', R_imp * 0.7, z - 0.005, z + 0.005, mat, 48))
            for i in range(6):
                b = box(f'{pid}bl{k}{i}', (R_imp * 0.35, 0.008, R_imp * 0.4), (R_imp * 0.82, 0, z), mat)
                parts.append(rotate(b, TAU * i / 6, 'Z'))
        else:
            for i in range(4):
                b = box(f'{pid}bl{k}{i}', (R_imp - 0.04, 0.008, R_imp * 0.35), ((R_imp + 0.04) / 2, 0, z), mat)
                b = rotate(b, math.radians(45), 'X', (0, 0, z))
                parts.append(rotate(b, TAU * i / 4, 'Z'))
    p = P(m, pid, name, 'rotating_element', parts, explode=(0, -0.0, 0.9), ref=ref, section='keep')
    p.spin('Z', revs)
    drv = [cyl(pid + 'gb', 0.12, z_top + 0.25, z_top + 0.45, 'paint_blue', 48), cyl(pid + 'mt', 0.1, z_top + 0.45, z_top + 0.8, 'paint_motor', 48, ch=0.01),
           cyl(pid + 'ln', 0.16, z_top + 0.02, z_top + 0.25, 'paint_blue', 48, r_in=0.05)]
    P(m, pid + '_drive', 'Agitator Drive: Motor, Gearbox & Lantern with Mechanical Seal', 'drive', drv, explode=(0, 0, 1.1), ref='ag_drive')
    return p


# =============================================================== EQ-171 Double pipe heat exchanger
def double_pipe_heat_exchanger(out):
    m = _model('double_pipe_heat_exchanger', 'Double Pipe (Hairpin) Heat Exchanger — Counter-Current')
    Z1, Z2, X0, X1 = 0.45, 0.85, -0.9, 0.7
    Ri, Ro = 0.03, 0.065
    outer = [hollow_pipe(f'o{k}', [(X0, 0, z), (X1, 0, z)], Ro, 'paint_grey', 48, t=0.006) for k, z in enumerate((Z1, Z2))]
    outer += [cyl(f'oc{k}{s}', Ro + 0.012, x - 0.02, x, 'paint_grey', 48, axis='X', center=(0, 0, z), r_in=Ri + 0.003) if s else
              cyl(f'oc{k}{s}', Ro + 0.012, x, x + 0.02, 'paint_grey', 48, axis='X', center=(0, 0, z), r_in=Ri + 0.003)
              for k, z in enumerate((Z1, Z2)) for s, x in ((0, X0 - 0.02), (1, X1 + 0.02))]
    P(m, 'shell_pipes', 'Outer Pipes (Shell Legs) with End Closures', 'casing', outer, explode=(0, 0.35, 0), ref='dp_outer')
    inner = [hollow_pipe('in', [(X0 - 0.35, 0, Z1), (X1 + 0.1, 0, Z1), (X1 + 0.1 + (Z2 - Z1) / 2, 0, (Z1 + Z2) / 2), (X1 + 0.1, 0, Z2), (X0 - 0.35, 0, Z2)], Ri, 'copper', 32, bend=(Z2 - Z1) / 2 - 0.001, t=0.004)]
    P(m, 'inner_tube', 'Inner Tube with Return Bend (hairpin)', 'tubes', inner, explode=(0, -0.35, 0), ref='dp_inner')
    noz = [nozzle('n1', (X1 - 0.08, 0, Z1 + Ro), (0, 0, 1), 0.025, 0.12), nozzle('n2', (X0 + 0.08, 0, Z2 + Ro), (0, 0, 1), 0.025, 0.12),
           cyl('rb', 0.075, X1 + 0.12, X1 + 0.32, 'paint_grey', 48, axis='X', center=(0, 0, (Z1 + Z2) / 2))]
    noz += [box('bk', (0.02, 0.22, Z2 - Z1 + 0.2), (X1 + 0.22, 0, (Z1 + Z2) / 2), 'paint_grey')]
    P(m, 'nozzles', 'Annulus Nozzles & Return-Bend Housing', 'nozzles', noz, explode=(0, 0, 0.3), ref='dp_nozzles')
    sup = [box(f's{i}', (0.06, 0.2, Z2 + 0.08), (x, 0, (Z2 + 0.08) / 2), 'paint_grey') for i, x in enumerate((X0 + 0.2, X1 - 0.3))]
    P(m, 'supports', 'Supports', 'structure', sup, explode=(0, 0, -0.3), ref='dp_supports', section='keep')
    m.flow('hot_tube_side', [(X0 - 0.35, 0, Z1), (X1 + 0.1, 0, Z1), (X1 + 0.2, 0, (Z1 + Z2) / 2), (X1 + 0.1, 0, Z2), (X0 - 0.35, 0, Z2)], 'flow_discharge', 0.012, 0.25)
    m.flow('cold_annulus', [(X0 + 0.08, 0, Z2 + Ro + 0.12), (X0 + 0.08, 0, Z2 + Ri + 0.018), (X1 - 0.12, 0, Z2 + Ri + 0.018), (X1 - 0.12, 0, Z2 - Ri - 0.018),
                            (X1 - 0.08, 0, Z1 + Ri + 0.018), (X0 + 0.12, 0, Z1 + Ri + 0.018), (X0 + 0.12, 0, Z1 - Ri - 0.018), (X1 - 0.08, 0, Z1 - Ri - 0.018), (X1 - 0.08, 0, Z1 + Ro + 0.12)],
           'flow_suction', 0.009, 0.25)
    _temp_overlay(m, [(X0, -0.4, 9, Ro), (-0.4, 0.1, 7, Ro), (0.1, X1, 6, Ro)], 'Temperature along the hot stream',
                  'Counter-current flow: the hot fluid (inner tube) cools as it travels while the cold fluid in the annulus flows the opposite way and warms up. '
                  'Counter-flow keeps a temperature difference along the whole length, so it transfers more heat than parallel flow.', cz=Z1)
    return m.export(out)


# =============================================================== EQ-172 Air-cooled heat exchanger
def air_cooled_heat_exchanger(out):
    m = _model('air_cooled_heat_exchanger', 'Air-Cooled Heat Exchanger (Forced Draft, Finned-Tube Bundle)')
    ZB, L, W = 1.6, 2.0, 1.0
    rows, cols = 4, 9
    tubes = []
    for r in range(rows):
        for c in range(cols):
            y = -W / 2 + 0.06 + (W - 0.12) * (c + 0.5 * (r % 2)) / cols
            z = ZB + 0.04 + r * 0.045
            tubes.append(cyl(f't{r}{c}', 0.01, -L / 2, L / 2, 'copper', 12, axis='X', center=(0, y, z)))
            tubes.append(cyl(f'f{r}{c}', 0.02, -L / 2 + 0.02, L / 2 - 0.02, 'aluminium', 12, axis='X', center=(0, y, z), r_in=0.0105))
    P(m, 'tube_bundle', 'Finned-Tube Bundle (aluminium fins on carbon-steel tubes)', 'tubes', tubes, explode=(0, 0, 0.5), ref='ac_bundle', section='keep')
    hd = []
    for s in (-1, 1):
        x = s * (L / 2 + 0.08)
        o = box(f'hb{s}', (0.16, W + 0.04, 0.26), (x, 0, ZB + 0.11), 'paint_grey', bevel=0.006)
        i = box(f'hi{s}', (0.12, W, 0.22), (x, 0, ZB + 0.11), 'paint_grey')
        hd.append(csg(f'hd{s}', [o], [i], 'paint_grey'))
        hd += [hex_prism(f'pl{s}{c}', 0.03, ZB + 0.08, ZB + 0.1, 'brass', axis='X', center=(0, -W / 2 + 0.06 + (W - 0.12) * c / cols, ZB + 0.11)) for c in range(0, cols, 2)] if False else []
    hd.append(box('pp', (0.03, W, 0.01), (L / 2 + 0.08, 0, ZB + 0.11), 'paint_grey'))
    P(m, 'headers', 'Plug-Type Header Boxes (inlet/return; pass partition)', 'headers', hd, explode=(0, 0, 0.6), ref='ac_headers')
    noz = [nozzle('ni', (-L / 2 - 0.08, 0.25, ZB + 0.24), (0, 0, 1), 0.05, 0.25), nozzle('no', (-L / 2 - 0.08, -0.25, ZB - 0.02), (0, 0, -1), 0.04, 0.2)]
    P(m, 'nozzles', 'Process Inlet (top) & Outlet (bottom) Nozzles', 'nozzles', noz, explode=(-0.3, 0, 0.3), ref='ac_nozzles', section='keep')
    pl = csg('plen', [lathe('po', [(0.42, ZB - 0.02), (0.46, ZB - 0.02), (0.47, ZB - 0.55), (0.43, ZB - 0.55)], 'paint_grey', 64, center=(-0.45, 0, 0)),
                      lathe('po2', [(0.42, ZB - 0.02), (0.46, ZB - 0.02), (0.47, ZB - 0.55), (0.43, ZB - 0.55)], 'paint_grey', 64, center=(0.45, 0, 0))], [], 'paint_grey') if False else \
        join('plen', [box('pw1', (L, 0.02, 0.5), (0, W / 2, ZB - 0.27), 'paint_grey'), box('pw2', (L, 0.02, 0.5), (0, -W / 2, ZB - 0.27), 'paint_grey'),
                      box('pw3', (0.02, W, 0.5), (L / 2, 0, ZB - 0.27), 'paint_grey'), box('pw4', (0.02, W, 0.5), (-L / 2, 0, ZB - 0.27), 'paint_grey')] +
             [cyl(f'fr{i}', 0.44, ZB - 0.56, ZB - 0.5, 'paint_grey', 64, center=(x, 0, 0), r_in=0.42) for i, x in enumerate((-0.48, 0.48))])
    P(m, 'plenum', 'Fan Plenum & Fan Rings', 'casing', pl, explode=(0, 0.6, 0), ref='ac_plenum')
    for i, x in enumerate((-0.48, 0.48)):
        hub = cyl(f'fh{i}', 0.06, ZB - 0.6, ZB - 0.54, 'aluminium', 32, center=(x, 0, 0))
        bl = [rotate(rotate(box(f'fb{i}{k}', (0.36, 0.06, 0.008), (x + 0.22, 0, ZB - 0.57), 'aluminium'), 0.35, 'X', (x, 0, ZB - 0.57)), TAU * k / 4, 'Z', (x, 0, 0)) for k in range(4)]
        pf = P(m, f'fan_{i + 1}', f'Axial Fan {i + 1} (adjustable-pitch blades)', 'rotating_element', [hub] + bl, explode=(0, -0.6, -0.3), ref='ac_fan', section='keep', pivot=(x, 0, 0))
        pf.spin('Z', 3)
        drv = [cyl(f'sh{i}', 0.02, ZB - 1.2, ZB - 0.6, 'steel', 16, center=(x, 0, 0)), cyl(f'mo{i}', 0.1, ZB - 1.45, ZB - 1.2, 'paint_motor', 32, center=(x, 0, 0))]
        P(m, f'drive_{i + 1}', f'Fan Drive {i + 1} (motor & shaft)', 'drive', drv, explode=(0, -0.4, -0.5), ref='ac_drive', section='keep')
    st = [box(f'col{i}', (0.08, 0.08, ZB - 0.02), (sx * (L / 2 - 0.04), sy * (W / 2 + 0.04), (ZB - 0.02) / 2), 'paint_grey') for i, (sx, sy) in enumerate(((-1, -1), (-1, 1), (1, -1), (1, 1)))]
    st += [box('br', (L, 0.06, 0.06), (0, W / 2 + 0.04, ZB - 1.3), 'paint_grey'), box('br2', (L, 0.06, 0.06), (0, -W / 2 - 0.04, ZB - 1.3), 'paint_grey'),
           box('mb', (L, 0.1, 0.06), (0, 0, ZB - 1.48), 'paint_grey')]
    P(m, 'structure', 'Support Structure & Drive Beams', 'structure', st, explode=(0, 0, -0.3), ref='ac_structure', section='keep')
    for j, y in enumerate((-0.25, 0.25)):
        m.flow(f'air_{j}', [(-0.48 + 0.96 * j, y, ZB - 1.0), (-0.48 + 0.96 * j, y, ZB - 0.3), (-0.48 + 0.96 * j, y, ZB + 0.3), (-0.48 + 0.96 * j, y, ZB + 0.9)], 'air', 0.02, 0.3)
    m.flow('process', [(-L / 2 - 0.08, 0.25, ZB + 0.5), (-L / 2 - 0.08, 0.25, ZB + 0.17), (L / 2, 0.25, ZB + 0.17), (L / 2 + 0.08, 0, ZB + 0.11), (L / 2, -0.25, ZB + 0.06),
                       (-L / 2 - 0.08, -0.25, ZB + 0.04), (-L / 2 - 0.08, -0.25, ZB - 0.25)], 'flow_discharge', 0.015, 0.3)
    return m.export(out)


# =============================================================== EQ-173 Spiral heat exchanger
def spiral_heat_exchanger(out):
    m = _model('spiral_heat_exchanger', 'Spiral Plate Heat Exchanger (two spiral channels, counter-current)')
    CZ, W = 0.6, 0.35
    R0, gap, turns = 0.05, 0.035, 4.0
    t = 0.004

    def spiral(off, n=320):
        return [((R0 + off + 2 * gap * a / TAU) * math.cos(a), (R0 + off + 2 * gap * a / TAU) * math.sin(a)) for a in [turns * TAU * i / n for i in range(n + 1)]]

    def plate(nm, off, mat):
        s = spiral(off)
        n1 = [(x * (1 + t / math.hypot(x, z)), z * (1 + t / math.hypot(x, z))) for x, z in s]
        poly = [(x, CZ + z) for x, z in s] + [(x, CZ + z) for x, z in n1[::-1]]
        return extrude_poly(nm, poly, -W / 2, W / 2, mat, plane='XZ')
    plates = [plate('pa', 0.0, 'stainless'), plate('pb', gap, 'stainless')]
    P(m, 'spiral_plates', 'Two Spiral Plates forming Two Channels (spacer studs)', 'core', plates, explode=(0, 0.0, 0), ref='sp_plates', section='keep')
    Rmax = R0 + 2 * gap * turns + gap + 0.01
    sh = csg('shell', [cyl('so', Rmax + 0.02, -W / 2, W / 2, 'paint_blue', 96, axis='Y', center=(0, 0, CZ))], [cyl('si', Rmax, -W / 2 - 0.01, W / 2 + 0.01, 'paint_blue', 96, axis='Y', center=(0, 0, CZ))], 'paint_blue')
    tn = [nozzle('nh', (Rmax + 0.01, 0.08, CZ + 0.0), (1, 0, 0), 0.035, 0.18), nozzle('nc', (-Rmax - 0.01, -0.08, CZ), (-1, 0, 0), 0.035, 0.18)]
    P(m, 'shell', 'Outer Shell with Tangential Nozzles', 'casing', [sh] + tn, explode=(0, 0, -0.0), ref='sp_shell', section='keep')
    cv = [join('cvf', [cyl('cf', Rmax + 0.05, -W / 2 - 0.04, -W / 2, 'paint_blue', 96, axis='Y', center=(0, 0, CZ)), nozzle('cfn', (0, -W / 2 - 0.04, CZ), (0, -1, 0), 0.035, 0.18)])]
    P(m, 'front_cover', 'Front Cover with Centre Nozzle (hidden in cutaway)', 'casing', cv, explode=(0, -0.6, 0), ref='sp_covers', section='hide')
    cb = join('cvb', [cyl('cb', Rmax + 0.05, W / 2, W / 2 + 0.04, 'paint_blue', 96, axis='Y', center=(0, 0, CZ)), nozzle('cbn', (0, W / 2 + 0.04, CZ), (0, 1, 0), 0.035, 0.18)])
    P(m, 'rear_cover', 'Rear Cover with Centre Nozzle', 'casing', cb, explode=(0, 0.6, 0), ref='sp_covers', section='keep')
    sup = [box(f'st{i}', (0.06, W + 0.1, CZ - Rmax + 0.02), (sx * 0.2, 0, (CZ - Rmax + 0.02) / 2), 'paint_grey') for i, sx in enumerate((-1, 1))]
    P(m, 'supports', 'Supports', 'structure', sup, explode=(0, 0, -0.3), ref='sp_supports', section='keep')
    def sflow(off, inward):
        s = spiral(off + gap / 2, 120)
        pts = [(x, 0.0, CZ + z) for x, z in s]
        return pts[::-1] if inward else pts
    m.flow('hot_inward', [(Rmax + 0.2, 0.0, CZ)] + sflow(0.0, True) + [(0, 0, CZ), (0, -W / 2 - 0.22, CZ)], 'flow_discharge', 0.007, 0.2)
    m.flow('cold_outward', [(0, W / 2 + 0.22, CZ), (0, 0, CZ)] + sflow(gap, False) + [(-Rmax - 0.2, 0, CZ)], 'flow_suction', 0.007, 0.2)
    return m.export(out)


# =============================================================== EQ-174 Jacketed vessel
def jacketed_vessel(out):
    m = _model('jacketed_vessel', 'Jacketed Vessel (Conventional Jacket, Heating/Cooling Medium)')
    R, L, Z0 = 0.4, 0.8, 0.55
    v = vessel('v', R, L, 0.01, 'stainless', heads=('2:1', '2:1'), z0=Z0)
    P(m, 'vessel', 'Inner Vessel (shell & dished heads)', 'vessel', v, explode=(0, 0, 0), ref='jv_vessel')
    jk = csg('jk', [lathe('jo', [(0.0, Z0 - R / 2 - 0.07), (R + 0.06, Z0 - 0.02), (R + 0.06, Z0 + L * 0.8), (R + 0.0, Z0 + L * 0.8), (0.0, Z0 + L * 0.8)], 'paint_grey', 96)],
             [vessel('vi', R + 0.05, L, 0.0001, 'paint_grey', z0=Z0) if False else lathe('ji', [(0.0, Z0 - R / 2 - 0.06), (R + 0.05, Z0 - 0.02), (R + 0.05, Z0 + L * 0.8 - 0.01), (0.0, Z0 + L * 0.8 - 0.01)], 'paint_grey', 96)], 'paint_grey')
    jk = csg('jacket', [jk], [lathe('cut', [(0.0, Z0 - R / 2 - 0.01), (R + 0.002, Z0), (R + 0.002, Z0 + L), (0.0, Z0 + L)], 'paint_grey', 96)], 'paint_grey')
    P(m, 'jacket', 'Jacket (annular space for steam / hot oil / cooling water)', 'jacket', jk, explode=(0, 0.45, 0), ref='jv_jacket')
    sp = sweep_tube('spir', [(R + 0.025 * math.cos(0) * 0 + (R + 0.025) * math.cos(TAU * 4 * i / 160) - R - 0.025 + (R + 0.025) * 0, (R + 0.025) * math.sin(TAU * 4 * i / 160), Z0 + 0.04 + (L * 0.72) * i / 160)
                                  for i in range(161)], 0.006, 'steel', 6)
    sp = sweep_tube('spir', [((R + 0.025) * math.cos(TAU * 4 * i / 160), (R + 0.025) * math.sin(TAU * 4 * i / 160), Z0 + 0.04 + (L * 0.72) * i / 160) for i in range(161)], 0.006, 'steel', 6)
    P(m, 'spiral_baffle', 'Spiral Baffle in Jacket (directs medium flow)', 'jacket', sp, explode=(0, 0.6, 0), ref='jv_baffle')
    lq = liquid_v('lq', R - 0.012, Z0, Z0 + L * 0.65)
    pl = P(m, 'product', 'Product (liquid level animated: filling and emptying)', 'fluid', lq, explode=(0, -0.3, 0), ref='jv_product', section='keep')
    animate_level(m, pl, Z0 + 0.1, -0.35, lambda t: 0.5 - 0.5 * math.cos(TAU * t))
    noz = [nozzle('jin', (R + 0.06, 0, Z0 + L * 0.72), (1, 0, 0), 0.025, 0.15), nozzle('jout', (R + 0.06, 0, Z0 + 0.05), (1, 0, 0), 0.025, 0.15),
           nozzle('top1', (0.15, 0, Z0 + L + R / 2 - 0.03), (0, 0, 1), 0.04, 0.2), nozzle('top2', (-0.18, 0, Z0 + L + R / 2 - 0.04), (0, 0, 1), 0.03, 0.18),
           nozzle('bot', (0, 0, Z0 - R / 2 - 0.07), (0, 0, -1), 0.04, 0.2), pressure_gauge('pg', (-0.18, 0.0, Z0 + L + R / 2 + 0.14), r=0.04, facing=(0, -1, 0))]
    P(m, 'nozzles', 'Nozzles: Jacket In/Out, Feed, Vent, Bottom Outlet & Gauge', 'nozzles', noz, explode=(0, 0, 0.4), ref='jv_nozzles', section='keep')
    lg = legs('lg', R + 0.08, 0.0, Z0 + 0.15, 4)
    P(m, 'legs', 'Support Legs', 'structure', lg, explode=(0, 0, -0.3), ref='jv_supports', section='keep')
    m.flow('heating_medium', [(R + 0.21, 0, Z0 + L * 0.72), (R + 0.03, 0, Z0 + L * 0.72)] + [((R + 0.03) * math.cos(TAU * 4 * i / 60 + 0.0), (R + 0.03) * math.sin(TAU * 4 * i / 60), Z0 + L * 0.72 - (L * 0.66) * i / 60) for i in range(61)] +
           [(R + 0.21, 0, Z0 + 0.05)], 'steam', 0.008, 0.2)
    return m.export(out)


# =============================================================== EQ-175 Agitated reactor
def agitated_reactor(out):
    m = _model('agitated_reactor', 'Agitated (Stirred-Tank) Reactor — Jacketed, Baffled, Dual Impeller')
    R, L, Z0 = 0.5, 1.0, 0.75
    v = vessel('v', R, L, 0.012, 'stainless', z0=Z0)
    P(m, 'vessel', 'Reactor Vessel (shell & dished heads)', 'vessel', v, explode=(0, 0, 0), ref='ar_vessel')
    jk = csg('jk', [cyl('jo', R + 0.06, Z0 - 0.05, Z0 + L * 0.85, 'paint_grey', 96)], [cyl('ji', R + 0.002, Z0 - 0.06, Z0 + L * 0.86, 'paint_grey', 96)], 'paint_grey')
    P(m, 'jacket', 'Cooling / Heating Jacket', 'jacket', jk, explode=(0, 0.6, 0), ref='ar_jacket')
    bf = [rotate(box(f'bf{i}', (0.05, 0.01, L * 0.95), (R - 0.04, 0, Z0 + L * 0.48), 'stainless'), TAU * i / 4 + math.pi / 4, 'Z') for i in range(4)]
    P(m, 'baffles', 'Four Wall Baffles (stop swirling, improve mixing)', 'internals', bf, explode=(0, 0, 0.0), ref='ar_baffles', section='keep')
    lq = liquid_v('lq', R - 0.013, Z0, Z0 + L * 0.8)
    pl = P(m, 'contents', 'Reaction Mass', 'fluid', lq, explode=(0, -0.4, 0), ref='ar_contents', section='keep')
    _agitator(m, 'agitator', 'Agitator: Shaft & Two Pitched-Blade Turbines', Z0 + L + R / 2, [Z0 + 0.15, Z0 + 0.6], R * 0.4, 0, kind='pbt', revs=2, ref='ar_agitator')
    coil, cpts = helix_coil('coil', R * 0.72, Z0 + 0.05, Z0 + L * 0.7, 5, 0.012, 'stainless')
    P(m, 'cooling_coil', 'Internal Cooling Coil', 'internals', coil, explode=(0, 0, 0), ref='ar_coil', section='keep')
    noz = [nozzle('f1', (0.3, 0, Z0 + L + R / 2 - 0.12), (0, 0, 1), 0.04, 0.25), nozzle('f2', (-0.3, 0, Z0 + L + R / 2 - 0.12), (0, 0, 1), 0.035, 0.25),
           nozzle('mh', (0.0, 0.3, Z0 + L + R / 2 - 0.1), (0, 0, 1), 0.12, 0.15), nozzle('bo', (0, 0, Z0 - R / 2 - 0.01), (0, 0, -1), 0.05, 0.22),
           nozzle('ji', (R + 0.06, 0, Z0 + 0.0), (1, 0, 0), 0.03, 0.15), nozzle('jo', (R + 0.06, 0, Z0 + L * 0.82), (1, 0, 0), 0.03, 0.15),
           cyl('tw', 0.01, Z0 + 0.1, Z0 + L + R / 2, 'chrome', 12, center=(-0.25, -0.2, 0))]
    P(m, 'nozzles', 'Feed, Manway, Bottom Outlet, Jacket Nozzles & Thermowell', 'nozzles', noz, explode=(0, 0, 0.5), ref='ar_nozzles', section='keep')
    lg = legs('lg', R + 0.1, 0.0, Z0 + 0.2, 4)
    P(m, 'legs', 'Support Legs / Lugs', 'structure', lg, explode=(0, 0, -0.3), ref='ar_supports', section='keep')
    for j, sx in enumerate((1, -1)):
        loop = [(sx * 0.12, 0.02, Z0 + 0.45), (sx * 0.22, 0.02, Z0 + 0.12), (sx * 0.42, 0.02, Z0 + 0.12), (sx * 0.43, 0.02, Z0 + 0.7), (sx * 0.3, 0.02, Z0 + 0.82), (sx * 0.12, 0.02, Z0 + 0.7), (sx * 0.12, 0.02, Z0 + 0.45)]
        m.flow(f'circulation_{j}', loop, 'flow_suction', 0.01, 0.12)
    m.flow('coolant', [(cp[0], cp[1], cp[2]) for cp in cpts[::6]], 'water', 0.006, 0.2)
    return m.export(out)


# =============================================================== EQ-176 Pressure reactor
def pressure_reactor(out):
    m = _model('pressure_reactor', 'High-Pressure Stirred Reactor (Bolted Closure, Magnetic-Drive Agitator)')
    R, L, Z0 = 0.25, 0.7, 0.6
    body = csg('body', [cyl('bo', R + 0.06, Z0, Z0 + L, 'stainless', 96), lathe('bh', [((R + 0.06) * math.cos(math.pi / 2 * k / 10), Z0 - (R + 0.06) * math.sin(math.pi / 2 * k / 10)) for k in range(10, -1, -1)] + [(0.0, Z0)], 'stainless', 96),
                        cyl('fl', R + 0.16, Z0 + L - 0.08, Z0 + L, 'stainless', 96)],
               [cyl('bi', R, Z0, Z0 + L + 0.01, 'stainless', 96), lathe('bhi', [(R * math.cos(math.pi / 2 * k / 10), Z0 - R * math.sin(math.pi / 2 * k / 10)) for k in range(10, -1, -1)] + [(R, Z0 + 0.001), (0.0, Z0 + 0.001)], 'stainless', 96)], 'stainless')
    P(m, 'body', 'Thick-Walled Forged Body with Integral Flange', 'vessel', body, explode=(0, 0, -0.2), ref='pr_body')
    cov = csg('cov', [cyl('co', R + 0.16, Z0 + L, Z0 + L + 0.12, 'stainless', 96)], [cyl('ch', 0.04, Z0 + L - 0.01, Z0 + L + 0.13, 'stainless', 32)], 'stainless')
    bolts = [join(f'bt{i}', [cyl(f'bs{i}', 0.014, Z0 + L - 0.1, Z0 + L + 0.16, 'steel_dark', 12, center=((R + 0.11) * math.cos(TAU * i / 16), (R + 0.11) * math.sin(TAU * i / 16), 0)),
                             hex_prism(f'bn{i}', 0.036, Z0 + L + 0.12, Z0 + L + 0.15, 'steel_dark', center=((R + 0.11) * math.cos(TAU * i / 16), (R + 0.11) * math.sin(TAU * i / 16), 0))]) for i in range(16)]
    gk = cyl('gk', R + 0.03, Z0 + L - 0.002, Z0 + L + 0.002, 'chrome', 96, r_in=R)
    P(m, 'closure', 'Bolted Cover (16 studs) & Metal Seal Ring', 'closure', [cov, gk] + bolts, explode=(0, 0, 0.5), ref='pr_closure')
    md = join('md', [cyl('mh', 0.08, Z0 + L + 0.12, Z0 + L + 0.38, 'stainless', 48), cyl('mm', 0.09, Z0 + L + 0.38, Z0 + L + 0.62, 'paint_motor', 48, ch=0.01)])
    P(m, 'magnetic_drive', 'Magnetic Drive (sealless — containment can) & Motor', 'drive', md, explode=(0, 0, 1.0), ref='pr_magdrive')
    sh = [cyl('sh', 0.018, Z0 + 0.05, Z0 + L + 0.3, 'stainless', 24)]
    for k, z in enumerate((Z0 + 0.12, Z0 + 0.42)):
        sh.append(cyl(f'dk{k}', R * 0.3, z - 0.004, z + 0.004, 'stainless', 32))
        sh += [rotate(box(f'rb{k}{i}', (R * 0.16, 0.006, R * 0.2), (R * 0.36, 0, z), 'stainless'), TAU * i / 6, 'Z') for i in range(6)]
    pa = P(m, 'agitator', 'Agitator Shaft with Gas-Dispersion (Rushton) Turbines', 'rotating_element', sh, explode=(0, -0.0, 1.1), ref='pr_agitator', section='keep')
    pa.spin('Z', 3)
    cl, cpts = helix_coil('cl', R * 0.78, Z0 + 0.05, Z0 + L * 0.8, 4, 0.008, 'stainless')
    sp = join('sp', [cyl('spr', R * 0.4, Z0 + 0.03, Z0 + 0.045, 'stainless', 32, r_in=R * 0.36), cyl('spd', 0.008, Z0 + 0.04, Z0 + L + 0.15, 'stainless', 12, center=(-R * 0.38, 0, 0))])
    P(m, 'internals', 'Cooling Coil & Gas Sparger Ring', 'internals', [cl, sp], explode=(0, 0, 0), ref='pr_internals', section='keep')
    lq = liquid('lq', R - 0.002, Z0 - R * 0.6, Z0 + L * 0.7)
    lq = liquid('lqq', R - 0.002, Z0 + 0.001, Z0 + L * 0.7)
    pl = P(m, 'contents', 'Reaction Liquid', 'fluid', lq, explode=(0, -0.4, 0), ref='pr_contents', section='keep')
    sf = [join('psv', [cyl('pv', 0.03, Z0 + L + 0.12, Z0 + L + 0.3, 'brass', 24, center=(R * 0.65, 0, 0)), cyl('pvb', 0.05, Z0 + L + 0.3, Z0 + L + 0.42, 'paint_red', 24, center=(R * 0.65, 0, 0))]),
          join('rd', [cyl('rd', 0.035, Z0 + L + 0.12, Z0 + L + 0.2, 'stainless', 24, center=(-R * 0.65, 0, 0)), cyl('rdh', 0.045, Z0 + L + 0.2, Z0 + L + 0.24, 'stainless', 24, center=(-R * 0.65, 0, 0))]),
          pressure_gauge('pg', (0.0, R * 0.65, Z0 + L + 0.2), r=0.045, facing=(0, -1, 0)), cyl('tw', 0.008, Z0 + 0.15, Z0 + L + 0.2, 'chrome', 12, center=(0, -R * 0.6, 0))]
    P(m, 'safety_instruments', 'Safety Valve, Rupture Disc, Pressure Gauge & Thermowell', 'safety', sf, explode=(0, 0, 0.7), ref='pr_safety', section='keep')
    st = [box('fr', (0.9, 0.9, 0.05), (0, 0, 0.025), 'paint_grey')] + [box(f'p{i}', (0.06, 0.06, Z0 - 0.0), (sx * 0.38, sy * 0.38, Z0 / 2), 'paint_grey') for i, (sx, sy) in
                                                                      enumerate(((-1, -1), (-1, 1), (1, -1), (1, 1)))] + [cyl('ring', R + 0.12, Z0 + 0.1, Z0 + 0.14, 'paint_grey', 64, r_in=R + 0.06)]
    P(m, 'stand', 'Support Stand & Lifting Ring', 'structure', st, explode=(0, 0, -0.3), ref='pr_stand', section='keep')
    m.flow('gas_feed', [(-R * 0.38, 0, Z0 + L + 0.15), (-R * 0.38, 0, Z0 + 0.04), (0, 0, Z0 + 0.04), (0.02, 0.02, Z0 + 0.3), (0.05, 0.05, Z0 + L * 0.7)], 'air', 0.007, 0.1)
    m.flow('coolant', [p for p in cpts[::8]], 'water', 0.005, 0.15)
    for j, sx in enumerate((1, -1)):
        m.flow(f'mixing_{j}', [(sx * 0.05, 0.02, Z0 + 0.12), (sx * 0.2, 0.02, Z0 + 0.12), (sx * 0.2, 0.02, Z0 + 0.42), (sx * 0.05, 0.02, Z0 + 0.42), (sx * 0.05, 0.02, Z0 + 0.12)], 'flow_suction', 0.006, 0.08)
    return m.export(out)


# =============================================================== EQ-177 Autoclave
def autoclave(out):
    m = _model('autoclave', 'Industrial Autoclave (Horizontal, Quick-Opening Door)')
    R, L, CZ, X0 = 0.6, 2.0, 0.85, -1.0
    sh = csg('sh', [cyl('so', R + 0.02, X0, X0 + L, 'stainless', 96, axis='X', center=(0, 0, CZ)), lathe('rh', [(R + 0.02, X0 + L), (R * 0.7, X0 + L + R * 0.3), (0.0, X0 + L + R * 0.4), (0.0, X0 + L)], 'stainless', 96, axis='X', center=(0, 0, CZ)),
                    cyl('fr', R + 0.12, X0 - 0.06, X0 + 0.04, 'stainless', 96, axis='X', center=(0, 0, CZ))],
             [cyl('si', R, X0 - 0.1, X0 + L, 'stainless', 96, axis='X', center=(0, 0, CZ)), lathe('rhi', [(R, X0 + L - 0.001), (R * 0.68, X0 + L + R * 0.28), (0.0, X0 + L + R * 0.38), (0.0, X0 + L - 0.001)], 'stainless', 96, axis='X', center=(0, 0, CZ))], 'stainless')
    P(m, 'shell', 'Pressure Shell, Dished Rear Head & Door Ring', 'vessel', sh, explode=(0, 0, 0), ref='ac_shell')
    ins = csg('ins', [cyl('io', R + 0.1, X0 + 0.05, X0 + L, 'cladding', 96, axis='X', center=(0, 0, CZ))], [cyl('ii', R + 0.025, X0, X0 + L + 0.01, 'cladding', 96, axis='X', center=(0, 0, CZ))], 'cladding')
    P(m, 'insulation', 'Insulation & Cladding', 'insulation', ins, explode=(0, 0.5, 0), ref='ac_insulation')
    door = join('door', [lathe('dr', [(0.0, X0 - 0.06), (R + 0.1, X0 - 0.06), (R + 0.1, X0 - 0.12), (R * 0.7, X0 - 0.12 - R * 0.25), (0.0, X0 - 0.12 - R * 0.3)], 'stainless', 96, axis='X', center=(0, 0, CZ)),
                         box('hd', (0.04, 0.3, 0.06), (X0 - 0.12 - R * 0.3, 0, CZ), 'chrome')])
    pdr = P(m, 'door', 'Quick-Opening Door (bayonet/lock-ring closure)', 'closure', door, explode=(-0.5, 0, 0), ref='ac_door', section='keep')
    hinge = (X0 - 0.06, R + 0.14, CZ)
    for mesh in pdr.meshes:
        from pumpforge.rotkit import local_pivot, axis_rot_keys
        local_pivot(mesh, hinge)
        axis_rot_keys(m, mesh, (0, 0, 1), lambda t: -1.4 * smooth_pulse(t, 0.15, 0.3, 0.15))
    lr = join('lr', [cyl('lrc', R + 0.14, X0 - 0.07, X0 - 0.02, 'steel_dark', 96, axis='X', center=(0, 0, CZ), r_in=R + 0.1)] +
              [rotate(box(f'lg{i}', (0.05, 0.04, 0.04), (X0 - 0.045, 0, CZ + R + 0.085), 'steel_dark'), TAU * i / 8, 'X', (0, 0, CZ)) for i in range(8)])
    plr = P(m, 'lock_ring', 'Locking Ring (rotates to lock/unlock the door lugs)', 'closure', lr, explode=(-0.3, 0, 0.3), ref='ac_lock_ring', section='keep', pivot=(0, 0, CZ))
    keys_loop(m, plr, lambda t: (0.3 * (1 - smooth_pulse(t, 0.1, 0.4, 0.1)) - 0.3, 0, 0), 'rotation_euler')
    rails = [box(f'rl{s}', (L, 0.04, 0.03), (X0 + L / 2, s * 0.3, CZ - R * 0.6), 'steel') for s in (-1, 1)]
    cart = [box('ct', (L * 0.6, 0.55, 0.04), (X0 + L * 0.45, 0, CZ - R * 0.52), 'steel'), box('ld1', (0.4, 0.4, 0.3), (X0 + L * 0.3, 0, CZ - R * 0.35), 'polypropylene'),
            box('ld2', (0.4, 0.4, 0.3), (X0 + L * 0.65, 0, CZ - R * 0.35), 'polypropylene')]
    P(m, 'rails', 'Internal Rails', 'internals', rails, explode=(0, 0, -0.2), ref='ac_rails', section='keep')
    P(m, 'load_cart', 'Load Cart with Product (e.g. composite parts / goods to sterilise)', 'internals', cart, explode=(-1.2, 0, 0), ref='ac_cart', section='keep')
    spd = sweep_tube('spd', [(X0 + 0.1, 0, CZ + R - 0.06), (X0 + L - 0.1, 0, CZ + R - 0.06)], 0.02, 'stainless', 12)
    fan = join('fan', [cyl('fh', 0.06, X0 + L - 0.15, X0 + L - 0.1, 'stainless', 24, axis='X', center=(0, 0, CZ))] +
               [rotate(box(f'fb{i}', (0.02, 0.05, 0.25), (X0 + L - 0.125, 0, CZ + 0.15), 'stainless'), TAU * i / 6, 'X', (0, 0, CZ)) for i in range(6)])
    P(m, 'steam_distributor', 'Steam Distributor Pipe', 'internals', spd, explode=(0, 0, 0.3), ref='ac_distributor', section='keep')
    pf = P(m, 'circulation_fan', 'Circulation Fan (uniform temperature)', 'rotating_element', fan, explode=(0.4, 0, 0), ref='ac_fan', section='keep', pivot=(0, 0, CZ))
    pf.spin('X', 3)
    noz = [nozzle('st', (X0 + 0.4, 0, CZ + R + 0.02), (0, 0, 1), 0.035, 0.3), nozzle('vac', (X0 + L - 0.4, 0, CZ + R + 0.02), (0, 0, 1), 0.04, 0.3),
           nozzle('dr', (X0 + L * 0.5, 0, CZ - R - 0.02), (0, 0, -1), 0.025, 0.15), join('psv', [cyl('pv', 0.03, CZ + R + 0.1, CZ + R + 0.35, 'brass', 24, center=(X0 + 1.0, 0.15, 0))]),
           pressure_gauge('pg', (X0 + 0.7, 0.0, CZ + R + 0.2), r=0.05, facing=(0, -1, 0))]
    P(m, 'nozzles', 'Steam Inlet, Vacuum Connection, Condensate Drain, Safety Valve & Gauge', 'nozzles', noz, explode=(0, 0, 0.4), ref='ac_nozzles', section='keep')
    sd = saddles('sd', (X0 + 0.4, X0 + L - 0.3), R + 0.1, CZ, 0.0)
    P(m, 'saddles', 'Saddle Supports', 'structure', sd, explode=(0, 0, -0.3), ref='ac_saddles', section='keep')
    m.flow('steam', [(X0 + 0.4, 0, CZ + R + 0.32), (X0 + 0.4, 0, CZ + R - 0.06), (X0 + L - 0.1, 0, CZ + R - 0.06), (X0 + L - 0.2, 0, CZ), (X0 + 0.3, 0, CZ - 0.1), (X0 + L * 0.5, 0, CZ - R - 0.15)],
           'steam', 0.012, 0.3, active=[(0.0, 0.1), (0.62, 1.0)])
    return m.export(out)


# =============================================================== EQ-178 Packed bed reactor
def packed_bed_reactor(out):
    m = _model('packed_bed_reactor', 'Fixed (Packed) Bed Catalytic Reactor — Two Beds with Interbed Quench')
    R, L, Z0 = 0.35, 2.0, 0.6
    v = vessel('v', R, L, 0.015, 'paint_grey', z0=Z0)
    P(m, 'vessel', 'Reactor Shell & Heads', 'vessel', v, explode=(0, 0, 0), ref='pb_vessel')
    sk = skirt('sk', R, 0.0, Z0 - R / 2 + 0.02)
    P(m, 'skirt', 'Support Skirt', 'structure', sk, explode=(0, 0, -0.3), ref='pb_skirt')
    beds = []
    for k, (zb, zt) in enumerate(((Z0 + 0.15, Z0 + 0.85), (Z0 + 1.1, Z0 + 1.8))):
        beds.append(cyl(f'bed{k}', R - 0.016, zb, zt, 'carbon', 96))
        beds.append(cyl(f'cb{k}', R - 0.016, zb - 0.05, zb, 'polypropylene', 96))
        beds.append(cyl(f'ct{k}', R - 0.016, zt, zt + 0.04, 'polypropylene', 96))
        beds.append(cyl(f'gr{k}', R - 0.016, zb - 0.07, zb - 0.05, 'steel_dark', 96))
    P(m, 'catalyst_beds', 'Catalyst Beds with Inert Ceramic Ball Layers & Support Grids', 'internals', [half(b, b.data.materials[0].name if b.data.materials else 'carbon') for b in beds], explode=(0, -0.5, 0), ref='pb_catalyst', section='keep')
    dist = [tray('dt', R - 0.02, Z0 + 1.93, holes=True, weir=False), cyl('ib', 0.08, Z0 + 1.96, Z0 + 2.08, 'stainless', 32)]
    q = [tray('qt', R - 0.02, Z0 + 0.98, holes=True, weir=False), sweep_tube('qr', [((R * 0.6) * math.cos(TAU * i / 40), (R * 0.6) * math.sin(TAU * i / 40), Z0 + 1.02) for i in range(41)], 0.012, 'stainless', 8)]
    P(m, 'distributors', 'Inlet Diffuser, Distribution Tray & Quench Mixing Zone', 'internals', dist + q, explode=(0, 0.5, 0), ref='pb_distributor', section='keep')
    noz = [nozzle('in', (0, 0, Z0 + L + R / 2 - 0.02), (0, 0, 1), 0.06, 0.3), nozzle('out', (0.0, 0.0, Z0 - R / 2 + 0.0), (1, 0, 0) if False else (0, 0, -1), 0.06, 0.05),
           nozzle('qn', (R + 0.0, 0, Z0 + 1.02), (1, 0, 0), 0.03, 0.25)] + [nozzle(f'tw{i}', (-R, 0, z), (-1, 0, 0), 0.012, 0.12) for i, z in enumerate((Z0 + 0.4, Z0 + 0.75, Z0 + 1.4, Z0 + 1.7))]
    oc = join('oc', [cyl('ocb', 0.1, Z0 - 0.15, Z0 + 0.12, 'stainless', 32, r_in=0.09)] + [cyl(f'oh{i}', 0.02, Z0 - 0.0, Z0 + 0.1, 'stainless', 8, center=(0.1 * math.cos(TAU * i / 8), 0.1 * math.sin(TAU * i / 8), 0)) for i in range(0)])
    P(m, 'nozzles', 'Inlet, Outlet Collector, Quench Gas Nozzle & Thermocouples', 'nozzles', noz + [oc], explode=(0, 0, 0.5), ref='pb_nozzles', section='keep')
    for j, x in enumerate((-0.2, 0.0, 0.2)):
        m.flow(f'process_{j}', [(x * 0.2, 0, Z0 + L + R / 2 + 0.28), (x * 0.2, 0, Z0 + 1.96), (x, 0.02, Z0 + 1.9), (x, 0.02, Z0 + 1.1), (x * 0.9, 0.02, Z0 + 0.98), (x, 0.02, Z0 + 0.85),
                                (x, 0.02, Z0 + 0.12), (x * 0.3, 0.02, Z0 - 0.1), (0, 0.02, Z0 - R / 2 - 0.08)], 'flow_discharge', 0.009, 0.25, speed=[1, 1, 0.6, 0.6, 0.8, 0.6, 0.6, 1, 1])
    m.flow('quench', [(R + 0.25, 0, Z0 + 1.02), (R * 0.6, 0, Z0 + 1.02), (0.0, 0.05, Z0 + 1.0)], 'flow_suction', 0.007, 0.15)
    _temp_overlay(m, [(Z0 + 0.15, Z0 + 0.5, 5, R + 0.01), (Z0 + 0.5, Z0 + 0.85, 8, R + 0.01), (Z0 + 0.85, Z0 + 1.1, 4, R + 0.01), (Z0 + 1.1, Z0 + 1.45, 6, R + 0.01), (Z0 + 1.45, Z0 + 1.8, 8, R + 0.01)][::-1],
                  'Temperature profile (exothermic reaction)', 'Feed enters cool at the top. The reaction releases heat, so temperature rises down each bed; cold quench gas '
                  'between the beds brings it back down so the catalyst stays within its safe temperature range.', axis='Z')
    return m.export(out)


# =============================================================== EQ-179 Fluidized bed reactor
def fluidized_bed_reactor(out):
    m = _model('fluidized_bed_reactor', 'Fluidized Bed Reactor (Bubbling Bed, Internal Cyclones)')
    R, L, Z0 = 0.45, 2.0, 0.7
    v = vessel('v', R, L, 0.012, 'paint_grey', heads=('cone', '2:1'), z0=Z0)
    P(m, 'vessel', 'Reactor Vessel (conical bottom, freeboard section)', 'vessel', v, explode=(0, 0, 0), ref='fb_vessel')
    lg = legs('lg', R + 0.05, 0.0, Z0 + 0.3, 4)
    P(m, 'legs', 'Supports', 'structure', lg, explode=(0, 0, -0.3), ref='fb_supports', section='keep')
    dp = csg('dp', [cyl('dpp', R - 0.012, Z0 + 0.05, Z0 + 0.07, 'stainless', 96)], [], 'stainless') if False else cyl('dpp', R - 0.012, Z0 + 0.05, Z0 + 0.07, 'stainless', 96)
    caps = [join(f'bc{i}', [cyl(f'bcs{i}', 0.012, Z0 + 0.07, Z0 + 0.12, 'stainless', 12, center=(x, y, 0)), cyl(f'bch{i}', 0.025, Z0 + 0.12, Z0 + 0.14, 'stainless', 16, center=(x, y, 0))])
            for i, (x, y) in enumerate([(R * 0.6 * math.cos(TAU * k / 8), R * 0.6 * math.sin(TAU * k / 8)) for k in range(8)] + [(R * 0.25 * math.cos(TAU * k / 4), R * 0.25 * math.sin(TAU * k / 4)) for k in range(4)])]
    P(m, 'distributor', 'Gas Distributor Plate with Bubble Caps (nozzles)', 'internals', [dp] + caps, explode=(0, -0.5, 0), ref='fb_distributor')
    bed = liquid('bed', R - 0.013, Z0 + 0.07, Z0 + 0.95, mat='polypropylene')
    pbd = P(m, 'bed', 'Fluidized Particle Bed (expands with gas flow)', 'fluid', bed, explode=(0, -0.0, 0), ref='fb_bed', section='keep')
    animate_level(m, pbd, Z0 + 0.5, 0.12, lambda t: 0.5 + 0.5 * math.sin(TAU * 3 * t) * 0.6 + 0.2)
    bub = m.part('bubbles', 'Gas Bubbles Rising through the Bed', 'flow_tracers', explode=(0, 0, 0), info={'ref': 'flow_tracers'})
    for i in range(14):
        a = TAU * i / 14 * 2.3
        r_ = R * (0.2 + 0.6 * ((i * 0.37) % 1))
        x, y = r_ * math.cos(a), abs(r_ * math.sin(a)) + 0.02
        o = sphere(f'bb{i}', (0, 0, 0), 0.03 + 0.015 * (i % 3), 'air', 12)
        ms = bub.add(o, smooth_angle=60)
        ph = (i * 0.31) % 1.0
        keys = [(1 + f, (x, y, Z0 + 0.12 + 0.8 * (((f / OPERATE_FRAMES) * 2 + ph) % 1.0))) for f in range(OPERATE_FRAMES + 1)]
        ms.location = keys[0][1]
        m.keyframes(ms, 'Operate', 'location', keys)
    cyc = []
    for s in (-1, 1):
        cx = s * R * 0.45
        cyc += [cyl(f'cy{s}', 0.1, Z0 + 1.6, Z0 + 1.85, 'stainless', 32, center=(cx, 0.05, 0), r_in=0.092), lathe(f'cn{s}', [(0.1, Z0 + 1.6), (0.108, Z0 + 1.6), (0.03, Z0 + 1.35), (0.022, Z0 + 1.35)], 'stainless', 32, center=(cx, 0.05, 0)),
                cyl(f'dl{s}', 0.022, Z0 + 0.5, Z0 + 1.35, 'stainless', 16, center=(cx, 0.05, 0), r_in=0.016), cyl(f'vf{s}', 0.04, Z0 + 1.75, Z0 + L + 0.18, 'stainless', 16, center=(cx, 0.05, 0), r_in=0.034),
                box(f'ci{s}', (0.12, 0.05, 0.08), (cx - s * 0.1, 0.05, Z0 + 1.78), 'stainless')]
    P(m, 'cyclones', 'Internal Cyclones with Diplegs (return fines to the bed)', 'internals', cyc, explode=(0, 0.6, 0.2), ref='fb_cyclones', section='keep')
    noz = [nozzle('gi', (0, 0, Z0 - R - 0.01), (0, 0, -1), 0.06, 0.2), nozzle('go', (0, 0, Z0 + L + R / 2 - 0.02), (0, 0, 1), 0.07, 0.3),
           nozzle('sf', (R, 0, Z0 + 0.6), (1, 0, 0), 0.05, 0.25), nozzle('sd', (-R, 0, Z0 + 0.2), (-1, 0, 0), 0.05, 0.25)]
    P(m, 'nozzles', 'Fluidizing Gas Inlet, Product Gas Outlet, Solids Feed & Solids Draw-off', 'nozzles', noz, explode=(0, 0, 0.4), ref='fb_nozzles', section='keep')
    m.flow('fluidizing_gas', [(0, 0, Z0 - R - 0.2), (0, 0, Z0 + 0.0), (0.15, 0.03, Z0 + 0.14), (0.15, 0.03, Z0 + 1.2), (R * 0.45 - 0.1, 0.05, Z0 + 1.78), (R * 0.45, 0.05, Z0 + 1.9),
                              (R * 0.45, 0.05, Z0 + L + 0.18), (0, 0, Z0 + L + R / 2 + 0.3)], 'air', 0.012, 0.25)
    m.flow('solids_return', [(-R * 0.45, 0.05, Z0 + 1.6), (-R * 0.45, 0.05, Z0 + 0.5)], 'flow_discharge', 0.01, 0.2)
    return m.export(out)


# ===================================================================== metadata
def _std(*items):
    return [{'id': i, 'title': t, 'relevance': r, 'edition': 'to be verified'} for i, t, r in items]


_VSTD = _std(('ASME BPVC Section VIII Div. 1', 'Rules for Construction of Pressure Vessels', 'Design, fabrication, inspection.'),
             ('EN 13445', 'Unfired pressure vessels', 'European design code.'), ('PED 2014/68/EU', 'Pressure Equipment Directive', 'EU conformity.'))

META = {
    'double_pipe_heat_exchanger': {
        'summary': ('A double pipe (hairpin) heat exchanger is the simplest exchanger: one fluid flows in an inner tube, the other in the annulus between it and an outer pipe. '
                    'Running the two fluids in opposite directions (counter-current) gives the best heat transfer. Hairpins are compact, easy to clean and handle high pressure.'),
        'classification': {'family': 'Tubular heat exchanger', 'type': 'Double-pipe hairpin, counter-current'},
        'model_configuration': {'legs': 2, 'return': 'U-bend in a return housing', 'flow': 'Hot fluid in tube, cold fluid in annulus'},
        'standards': _std(('ASME BPVC VIII', 'Pressure vessels', 'Pressure parts.'), ('TEMA (where applicable)', 'Standards of the Tubular Exchanger Manufacturers Association', 'Practice.')),
        'references': ['Kern, Process Heat Transfer', 'Kakaç & Liu, Heat Exchangers'],
        'components': {
            'dp_outer': C('Contains the annulus fluid around the inner tube.', 'Outer pipe legs with end closures.', 'Carbon steel / stainless.', 'Annulus velocity sets the outer film coefficient.', ['Fouling, corrosion'], ['ΔP and outlet temperatures']),
            'dp_inner': C('Carries the tube-side fluid; its wall is the heat-transfer surface.', 'Inner tube with U-bend.', 'Copper, stainless, carbon steel; finned versions exist.', '—', ['Fouling, leaks'], ['Hydro-test, cleaning']),
            'dp_nozzles': C('Connect the annulus fluid; return housing protects the bend.', 'Nozzles, return-bend cover.', 'Steel.', '—', ['Leaks'], ['Visual']),
            'dp_supports': C('Support the hairpin.', 'Steel supports.', 'Steel.', '—', ['—'], ['—']),
        },
    },
    'air_cooled_heat_exchanger': {
        'summary': ('An air-cooled heat exchanger (fin-fan cooler) cools or condenses a process fluid using ambient air instead of water. The fluid flows through finned tubes '
                    'between header boxes; axial fans blow (forced draft) or pull (induced draft) air across the bundle. It saves cooling water and is common in refineries and gas plants.'),
        'classification': {'family': 'Air-cooled heat exchanger', 'type': 'Forced draft, plug-type headers, two fans'},
        'model_configuration': {'tube_rows': 4, 'fans': 2, 'passes': '2 (pass partition in the header)'},
        'standards': _std(('API 661 / ISO 13706', 'Air-cooled heat exchangers for general refinery service', 'Design and fabrication.'),),
        'references': ['GPSA Engineering Data Book Section 10'],
        'components': {
            'ac_bundle': C('Transfers heat from the process fluid to air.', 'Rows of tubes with extended aluminium fins.', 'Carbon steel tubes, aluminium fins.', 'Fin type (embedded, extruded, wrapped) limits temperature.',
                           ['Fin fouling', 'Tube corrosion'], ['Clean fins, IRIS tube inspection']),
            'ac_headers': C('Distribute the fluid to the tubes and turn it between passes.', 'Plug-type header boxes with pass partitions.', 'Carbon steel.', 'Plugs allow tube cleaning.', ['Plug leaks'], ['Re-gasket plugs']),
            'ac_nozzles': C('Process connections.', 'Flanged nozzles.', 'Steel.', '—', ['—'], ['—']),
            'ac_plenum': C('Guides air from the fans to the whole bundle.', 'Box plenum with fan rings.', 'Steel.', '—', ['—'], ['—']),
            'ac_fan': C('Move cooling air across the bundle.', 'Axial fans with adjustable pitch.', 'Aluminium/FRP blades.', 'Pitch or VFD adjusts duty with ambient temperature.', ['Imbalance, blade damage'], ['Vibration']),
            'ac_drive': C('Drive the fans.', 'Motor and shaft (belt or direct).', 'Steel.', '—', ['Bearing wear'], ['Lubrication']),
            'ac_structure': C('Supports bundle, fans and drives.', 'Steel structure.', 'Galvanised steel.', '—', ['Corrosion'], ['Inspect']),
        },
    },
    'spiral_heat_exchanger': {
        'summary': ('A spiral heat exchanger is made of two long metal plates rolled into a spiral, forming two separate channels. One fluid spirals in toward the centre, the other '
                    'spirals out — true counter-current flow in a single channel each. The curved single channel scrubs itself, so it handles fouling fluids and slurries well.'),
        'classification': {'family': 'Plate-type heat exchanger', 'type': 'Spiral, two-channel, counter-current, removable covers'},
        'model_configuration': {'turns': 4, 'covers': 'Bolted covers with centre nozzles'},
        'standards': _std(('ASME BPVC VIII', 'Pressure vessels', 'Pressure parts.'),),
        'references': ['Alfa Laval spiral heat exchanger literature (generic)'],
        'components': {
            'sp_plates': C('Form the two spiral channels and transfer heat.', 'Two plates wound with welded spacer studs.', 'Stainless, titanium, Hastelloy.', '—', ['Fouling, cracking'], ['Open covers and clean']),
            'sp_shell': C('Outer shell with tangential nozzles at the periphery.', 'Rolled shell.', 'Steel.', '—', ['—'], ['—']),
            'sp_covers': C('Close the channels; centre nozzles; open for cleaning.', 'Bolted flat covers with gaskets.', 'Steel.', 'Each channel is sealed on alternate sides.', ['Gasket leaks'], ['Gasket replacement']),
            'sp_supports': C('Supports.', 'Steel.', 'Steel.', '—', ['—'], ['—']),
        },
    },
    'jacketed_vessel': {
        'summary': ('A jacketed vessel has an outer jacket around the lower part of the vessel. A heating or cooling medium (steam, hot oil, chilled water) flows through the jacket '
                    'space and heats or cools the contents through the vessel wall without mixing with them. A spiral baffle guides the medium for better heat transfer.'),
        'classification': {'family': 'Pressure vessel with heat-transfer jacket', 'type': 'Conventional jacket with spiral baffle'},
        'model_configuration': {'animation': 'Product level rises and falls (batch fill / empty)', 'jacket': 'Covers ~80 % of the straight shell'},
        'standards': _VSTD, 'references': ['Perry\'s Chemical Engineers\' Handbook — jacketed vessels'],
        'components': {
            'jv_vessel': C('Holds the product.', 'Shell with dished heads.', 'Stainless steel / glass-lined.', 'Designed for internal and jacket pressure.', ['Corrosion'], ['Thickness check']),
            'jv_jacket': C('Holds the heating/cooling medium against the vessel wall.', 'Outer shell welded to the vessel.', 'Carbon steel / stainless.', 'Jacket pressure can buckle the inner shell — check external pressure.', ['Leaks, fouling'], ['Pressure test']),
            'jv_baffle': C('Forces the medium round in a spiral for higher velocity and heat transfer.', 'Spiral baffle bar.', 'Steel.', '—', ['—'], ['—']),
            'jv_product': C('Contents (level animated).', '—', '—', '—', ['—'], ['—']),
            'jv_nozzles': C('Process, vent, drain and jacket connections; gauge.', 'Nozzles.', 'Stainless.', '—', ['—'], ['—']),
            'jv_supports': C('Support legs.', 'Legs with base plates.', 'Steel.', '—', ['—'], ['—']),
        },
    },
    'agitated_reactor': {
        'summary': ('An agitated (stirred-tank) reactor mixes reactants in a vessel with a motor-driven agitator. Wall baffles stop the liquid simply swirling and turn the flow into '
                    'top-to-bottom circulation. A jacket and/or internal coil add or remove the reaction heat. It is the workhorse of batch chemical and pharmaceutical production.'),
        'classification': {'family': 'Reactor', 'type': 'Continuous stirred-tank / batch reactor, jacketed, baffled, dual impeller'},
        'model_configuration': {'impellers': '2 × pitched-blade turbine (axial flow)', 'baffles': 4, 'heat_transfer': 'Jacket + internal coil'},
        'standards': _VSTD + _std(('ASME BPE', 'Bioprocessing Equipment', 'Hygienic design (pharma).'),), 'references': ['Paul, Atiemo-Obeng & Kresta, Handbook of Industrial Mixing'],
        'components': {
            'ar_vessel': C('Contains the reaction.', 'Shell with dished heads.', 'Stainless / glass-lined / alloy.', '—', ['Corrosion'], ['Inspect']),
            'ar_jacket': C('Heats or cools through the wall.', 'Jacket.', 'Carbon steel.', '—', ['Fouling'], ['Clean']),
            'ar_baffles': C('Convert swirl into vertical circulation.', 'Four wall baffles at 90°.', 'Stainless.', 'Width ~ 1/10–1/12 of diameter (typical).', ['Cracking'], ['Inspect']),
            'ar_contents': C('Reaction mass.', '—', '—', '—', ['—'], ['—']),
            'ar_agitator': C('Mixes, suspends solids and improves heat transfer.', 'Shaft with pitched-blade turbines.', 'Stainless.', 'Power ∝ N³D⁵ (turbulent).', ['Shaft run-out, seal wear'], ['Vibration']),
            'ag_drive': C('Drives the agitator and seals the shaft.', 'Motor, gearbox, lantern with mechanical seal.', 'Steel.', '—', ['Seal leakage'], ['Seal monitoring']),
            'ar_coil': C('Extra heat-transfer area inside the vessel.', 'Helical coil.', 'Stainless.', '—', ['Fouling'], ['Clean']),
            'ar_nozzles': C('Feed, manway, outlet, jacket connections, thermowell.', 'Nozzles.', 'Stainless.', '—', ['—'], ['—']),
            'ar_supports': C('Supports.', 'Legs/lugs.', 'Steel.', '—', ['—'], ['—']),
        },
    },
    'pressure_reactor': {
        'summary': ('A high-pressure reactor carries out reactions (hydrogenation, polymerisation, oxidation) at high pressure and temperature. A thick forged body with a multi-stud '
                    'bolted cover and metal seal contains the pressure; a magnetic drive stirs without a shaft seal. Safety valve and rupture disc protect against over-pressure.'),
        'classification': {'family': 'Reactor (high pressure)', 'type': 'Stirred autoclave-type reactor, bolted closure, magnetic drive'},
        'model_configuration': {'impellers': 'Two Rushton turbines with gas sparger', 'protection': 'Safety valve + rupture disc'},
        'standards': _VSTD + _std(('ASME BPVC VIII Div. 2/3', 'Alternative rules / high-pressure vessels', 'High-pressure design.'),), 'references': ['Parr / Büchi high-pressure reactor guides (generic)'],
        'components': {
            'pr_body': C('Contains the high-pressure reaction.', 'Forged thick-walled body with integral flange.', 'Stainless, Hastelloy, titanium.', 'Design pressure/temperature on nameplate.', ['Cracking, corrosion'], ['NDT, hydro-test']),
            'pr_closure': C('Seals the cover to the body.', 'Bolted cover with studs and metal seal ring.', 'Alloy steel studs.', 'Tighten in a star pattern to specified torque.', ['Seal leakage'], ['Leak test']),
            'pr_magdrive': C('Drives the agitator without a dynamic seal.', 'Magnetic coupling with containment can, motor.', '—', '—', ['Decoupling'], ['Torque check']),
            'pr_agitator': C('Disperses gas and mixes.', 'Shaft with Rushton turbines.', 'Stainless.', '—', ['—'], ['—']),
            'pr_internals': C('Cooling coil removes reaction heat; sparger introduces gas.', 'Coil and ring sparger.', 'Stainless.', '—', ['Plugging'], ['Clean']),
            'pr_contents': C('Reaction liquid.', '—', '—', '—', ['—'], ['—']),
            'pr_safety': C('Protect and monitor.', 'Safety valve, rupture disc, gauge, thermowell.', '—', 'Relief sized for runaway scenarios.', ['Disc fatigue'], ['Replace disc per schedule']),
            'pr_stand': C('Supports.', 'Stand and lifting ring.', 'Steel.', '—', ['—'], ['—']),
        },
    },
    'autoclave': {
        'summary': ('An industrial autoclave is a pressure vessel that applies heat and pressure (usually steam or hot gas) to a load — for curing composites, vulcanising rubber, '
                    'treating wood or sterilising. A quick-opening door with a rotating locking ring allows fast loading; interlocks prevent opening under pressure.'),
        'classification': {'family': 'Pressure vessel (batch process)', 'type': 'Horizontal autoclave with quick-opening door'},
        'model_configuration': {'animation': 'Lock ring rotates, door swings open, then closes and locks; steam cycle', 'load': 'Cart on internal rails'},
        'standards': _VSTD + _std(('ASME BPVC VIII UG-35.2', 'Quick-actuating closures', 'Door interlocks.'),), 'references': ['Autoclave manufacturer guides (generic)'],
        'components': {
            'ac_shell': C('Pressure boundary.', 'Cylindrical shell, dished rear head, door ring.', 'Carbon/stainless steel.', '—', ['Corrosion, fatigue (cycling)'], ['Inspection']),
            'ac_insulation': C('Reduces heat loss.', 'Mineral wool + cladding.', '—', '—', ['Wet insulation'], ['Inspect']),
            'ac_door': C('Closes the vessel quickly.', 'Dished door hinged at the side.', 'Steel.', 'Must not open under pressure (interlock).', ['Seal wear'], ['Interlock test']),
            'ac_lock_ring': C('Locks the door lugs (bayonet).', 'Rotating ring with lugs.', 'Steel.', '—', ['Lug wear'], ['NDT of lugs']),
            'ac_rails': C('Guide the load cart.', 'Rails.', 'Steel.', '—', ['—'], ['—']),
            'ac_cart': C('Carries the product.', 'Cart.', 'Steel.', '—', ['—'], ['—']),
            'ac_distributor': C('Distributes steam evenly.', 'Perforated pipe.', 'Stainless.', '—', ['Blocked holes'], ['Clean']),
            'ac_fan': C('Circulates the atmosphere for uniform temperature.', 'Fan.', 'Stainless.', '—', ['—'], ['—']),
            'ac_nozzles': C('Steam, vacuum, drain, safety valve, gauge.', 'Nozzles.', '—', '—', ['—'], ['—']),
            'ac_saddles': C('Support the shell.', 'Saddles.', 'Steel.', '—', ['—'], ['—']),
        },
    },
    'packed_bed_reactor': {
        'summary': ('A packed (fixed) bed reactor passes gas or liquid through a bed of solid catalyst particles. Feed enters at the top through a distributor, reacts as it flows '
                    'down through the catalyst, and leaves through an outlet collector. For exothermic reactions, cold quench between beds controls the temperature.'),
        'classification': {'family': 'Reactor (catalytic)', 'type': 'Down-flow fixed-bed, two beds, interbed quench'},
        'model_configuration': {'beds': 2, 'grading': 'Inert ceramic balls above and below each bed'},
        'standards': _VSTD, 'references': ['Froment & Bischoff, Chemical Reactor Analysis and Design'],
        'components': {
            'pb_vessel': C('Pressure shell.', 'Shell and heads.', 'Cr-Mo steel (hydroprocessing) / carbon steel.', '—', ['Hydrogen attack (high T, H₂)'], ['NDT']),
            'pb_skirt': C('Supports the vessel.', 'Skirt.', 'Steel.', '—', ['—'], ['—']),
            'pb_catalyst': C('Speeds up the reaction.', 'Catalyst bed with support grids and inert ball layers.', 'Catalyst pellets; ceramic balls.', 'Pressure drop rises as fines build up.', ['Deactivation, crusting'], ['ΔP and temperature trends']),
            'pb_distributor': C('Spread flow evenly and mix quench gas.', 'Inlet diffuser, distribution tray, quench ring.', 'Stainless.', 'Poor distribution → hot spots.', ['Plugging'], ['Inspect at turnaround']),
            'pb_nozzles': C('Inlet, outlet collector, quench and thermocouples.', 'Nozzles.', '—', '—', ['—'], ['—']),
        },
    },
    'fluidized_bed_reactor': {
        'summary': ('In a fluidized bed reactor, gas blown up through a distributor plate lifts a bed of fine particles so they behave like a boiling liquid. Intense mixing gives '
                    'very uniform temperature and excellent heat and mass transfer. Internal cyclones catch entrained particles and return them through diplegs.'),
        'classification': {'family': 'Reactor (gas–solid)', 'type': 'Bubbling fluidized bed with internal cyclones'},
        'model_configuration': {'animation': 'Bed expands/bubbles; bubbles rise; fines return via diplegs', 'distributor': 'Bubble-cap plate'},
        'standards': _VSTD, 'references': ['Kunii & Levenspiel, Fluidization Engineering'],
        'components': {
            'fb_vessel': C('Contains the bed and the freeboard where particles disengage.', 'Shell with conical bottom.', 'Steel, refractory-lined at high T.', '—', ['Erosion'], ['Thickness survey']),
            'fb_supports': C('Supports.', 'Legs.', 'Steel.', '—', ['—'], ['—']),
            'fb_distributor': C('Spreads the fluidizing gas evenly.', 'Plate with bubble caps/nozzles.', 'Stainless.', 'ΔP across plate ensures even distribution.', ['Plugging, erosion'], ['ΔP check']),
            'fb_bed': C('Fluidized solids (catalyst or reactant).', 'Particles.', '—', 'Minimum fluidization velocity must be exceeded.', ['Agglomeration, defluidization'], ['ΔP across bed']),
            'fb_cyclones': C('Separate entrained solids from the gas.', 'Cyclones with diplegs and trickle valves.', 'Stainless / hard-faced.', '—', ['Erosion, dipleg plugging'], ['Inspect']),
            'fb_nozzles': C('Gas in/out, solids feed and draw-off.', 'Nozzles.', '—', '—', ['—'], ['—']),
        },
    },
}

BUILDERS = {k: globals()[k] for k in META}
