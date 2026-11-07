"""
External Gear Pump — industrial foot-mounted transfer pump.
Two equal 12-tooth involute spur gears (module 6 mm, 25° pressure angle) in a
figure-8 bore; sleeve bushings in both covers; single mechanical seal on the
drive shaft; integral spring-loaded pressure-relief valve returning to suction.

Shafts along Blender Y (front cover at -Y).  Inlet port -X, outlet port +X.
Drive gear (top) rotates +Y, idler (bottom) -Y: liquid is carried around the
outside of each gear from inlet to outlet; teeth re-meshing at the centre
displace it into the outlet.
"""
import math
from pumpforge.core import (Model, lathe, lathe_split, ring_profile, cyl, box, csg, split, split_keep,
                            join, move, rotate, extrude_poly, bolt_circle, hex_prism, group_by,
                            merge_halves, split_faces, TAU)
from pumpforge.shapes import involute_gear_profile, sweep_tube

ID = 'external_gear_pump'
MOD, Z_T, ALPHA, FACE = 0.006, 12, 25.0, 0.06
ZC = 0.16                          # pump centre height above foot underside
A = MOD * Z_T                      # centre distance = pitch diameter
ZD, ZI = ZC + A / 2, ZC - A / 2    # drive / idler centre heights
R_S = 0.016                        # shaft radius
HW, HH, RC = 0.078, 0.102, 0.03    # body outline half width / half height / corner radius


def rounded_rect(hw, hh, r, cz, n=8):
    pts = []
    for cx_, cz_, a0 in ((hw - r, hh - r, 0), (-hw + r, hh - r, 90), (-hw + r, -hh + r, 180),
                         (hw - r, -hh + r, 270)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx_ + r * math.cos(a), cz + cz_ + r * math.sin(a)))
    return pts


OUTLINE = rounded_rect(HW, HH, RC, ZC)
BOLTS = [(0.054, ZC + 0.077), (-0.054, ZC + 0.077), (0.054, ZC - 0.077), (-0.054, ZC - 0.077)]


def socket_screws(name, y0, y1, skip=()):
    objs = []
    for i, (x, z) in enumerate(BOLTS):
        if i in skip:
            continue
        objs.append(cyl(f'{name}{i}', 0.0085, y0, y1, 'steel_dark', 24, axis='Y', center=(x, 0, z), ch=0.001))
        # hex socket
        objs.append(hex_prism(f'{name}h{i}', 0.008, y1, y1 + (0.0005 if y1 > y0 else -0.0005), 'thermoplastic',
                              axis='Y', center=(x, 0, z), ch=False))
    return join(name, objs)


def build(out_dir):
    m = Model(ID, 'External Gear Pump (Foot-Mounted, with Relief Valve)',
              'B · Rotary Positive-Displacement Pumps', META)

    # ================= BODY ===============================================
    outers = [
        extrude_poly('body', OUTLINE, -0.03, 0.03, 'paint_green', plane='XZ'),
        cyl('boss_in', 0.04, -0.115, -0.06, 'paint_green', 64, axis='X', center=(0, 0, ZC)),
        cyl('boss_out', 0.04, 0.06, 0.115, 'paint_green', 64, axis='X', center=(0, 0, ZC)),
        box('fl_in', (0.022, 0.11, 0.11), (-0.12, 0, ZC), 'paint_green', bevel=0.006),
        box('fl_out', (0.022, 0.11, 0.11), (0.12, 0, ZC), 'paint_green', bevel=0.006),
        box('web', (0.12, 0.06, ZC - HH - 0.012), (0, 0, (ZC - HH + 0.016) / 2 + 0.004), 'paint_green'),
        box('foot', (0.25, 0.15, 0.018), (0, 0, 0.009), 'paint_green', bevel=0.004),
    ]
    inners = [
        cyl('bore_d', MOD * (Z_T + 2) / 2 + 0.0004, -0.05, 0.05, 'paint_green', 96, axis='Y', center=(0, 0, ZD)),
        cyl('bore_i', MOD * (Z_T + 2) / 2 + 0.0004, -0.05, 0.05, 'paint_green', 96, axis='Y', center=(0, 0, ZI)),
        cyl('port_in', 0.022, -0.2, 0.0, 'paint_green', 48, axis='X', center=(0, 0, ZC)),
        cyl('port_out', 0.022, 0.0, 0.2, 'paint_green', 48, axis='X', center=(0, 0, ZC)),
        cyl('drill_d', 0.006, ZC, ZC + HH + 0.01, 'paint_green', 24, center=(0.05, 0, 0)),
        cyl('drill_s', 0.006, ZC, ZC + HH + 0.01, 'paint_green', 24, center=(-0.05, 0, 0)),
    ] + [cyl(f'fh{i}', 0.008, -0.01, 0.03, 'paint_green', 24, center=(sx * 0.1, sy * 0.05, 0))
         for i, (sx, sy) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1)))] \
      + [cyl(f'bh{i}', 0.0065, -0.05, 0.05, 'paint_green', 20, axis='Y', center=(x, 0, z))
         for i, (x, z) in enumerate(BOLTS)]
    body = csg('pump_body', outers, inners, 'paint_green')
    bb, bf = split(body, 'y', 0.0)
    pb = [bolt_circle(f'pfb{s}', 4, 0.115, 0.022, s * 0.131, s * 0.147, axis='X', center=(0, 0, ZC),
                      phase=math.pi / 4, stud=(0.014, s * 0.125, s * 0.16)) for s in (1, -1)]
    pbb, pbf = split_faces(join('port_bolts', pb), 'y', 0.0)
    p = m.part('pump_body', 'Pump Body (Gear Housing)', 'casing', section='split')
    p.add_split(join('body_b', [bb, pbb]), join('body_f', [bf, pbf]), smooth_angle=40)

    # ================= COVERS =============================================
    fc_in = [cyl(f'fcb{i}', 0.021, -0.065, -0.029, 'paint_green', 48, axis='Y', center=(0, 0, z))
             for i, z in enumerate((ZD, ZI))]
    fc_in += [cyl(f'fch{i}', 0.0065, -0.09, -0.02, 'paint_green', 20, axis='Y', center=(x, 0, z))
              for i, (x, z) in enumerate(BOLTS)]
    fc = csg('front_cover', [extrude_poly('fc', OUTLINE, -0.075, -0.03, 'paint_green', plane='XZ')], fc_in,
             'paint_green')
    # cast "trapped-volume" relief grooves are machined in the cover face; shown as shallow pockets
    p = m.part('front_cover', 'Front (End) Cover', 'casing', section='hide', explode=(0, -0.32, 0))
    plate = box('fc_plate', (0.07, 0.002, 0.045), (0, -0.076, ZC), 'nameplate', bevel=0.001)
    arrow = extrude_poly('fc_arrow', [(-0.02, ZC + 0.04), (0.012, ZC + 0.04), (0.012, ZC + 0.047), (0.026, ZC + 0.036),
                                      (0.012, ZC + 0.025), (0.012, ZC + 0.032), (-0.02, ZC + 0.032)],
                         -0.0765, -0.075, 'paint_red', plane='XZ')
    p.add(join('front_cover', [fc, plate, arrow, socket_screws('fc_scr', -0.075, -0.084)]), smooth_angle=40)

    rc_out = [extrude_poly('rc', OUTLINE, 0.03, 0.07, 'paint_green', plane='XZ'),
              lathe('seal_boss', [(0, 0.069), (0.05, 0.069), (0.05, 0.075), (0.045, 0.08), (0.045, 0.115),
                                  (0, 0.115)], 'paint_green', 64, axis='Y', center=(0, 0, ZD))]
    rc_in = [cyl('rc_shaft', R_S + 0.0012, 0.0, 0.2, 'paint_green', 48, axis='Y', center=(0, 0, ZD)),
             cyl('rc_seal', 0.032, 0.074, 0.13, 'paint_green', 64, axis='Y', center=(0, 0, ZD)),
             cyl('rcb_d', 0.021, 0.029, 0.065, 'paint_green', 48, axis='Y', center=(0, 0, ZD)),
             cyl('rcb_i', 0.021, 0.029, 0.065, 'paint_green', 48, axis='Y', center=(0, 0, ZI))]
    rc_in += [cyl(f'rch{i}', 0.0065, 0.02, 0.09, 'paint_green', 20, axis='Y', center=(x, 0, z))
              for i, (x, z) in enumerate(BOLTS)]
    rc = csg('rear_cover', rc_out, rc_in, 'paint_green')
    rcb, rcf = split_keep(rc, 'x', 0.0, keep_positive=False)
    sb_, sf_ = split_faces(socket_screws('rc_scr', 0.07, 0.079), 'x', 0.0, keep_positive=False)
    p = m.part('rear_cover', 'Rear (Seal-Side) Cover', 'casing', section='split', explode=(0, 0.28, 0))
    p.add_split(join('rc_b', [rcb, sb_]), join('rc_f', [rcf, sf_]), smooth_angle=40)

    # ================= BUSHINGS ===========================================
    for side, (y0, y1) in (('front', (-0.063, -0.031)), ('rear', (0.031, 0.063))):
        for g, z in (('drive', ZD), ('idler', ZI)):
            pid = f'bushing_{side}_{g}'
            prof = [(R_S + 0.0003, y0), (0.021, y0), (0.021, y1), (R_S + 0.0003, y1)]
            ey = -0.2 if side == 'front' else 0.18
            if side == 'front':
                p = m.part(pid, f'Sleeve Bushing – {side.title()}, {g.title()} Shaft', 'bearings', section='hide',
                           explode=(0, ey, 0), info={'ref': 'bushing'})
                p.add(lathe(pid, prof, 'bronze', 48, axis='Y', center=(0, 0, z)))
            else:
                p = m.part(pid, f'Sleeve Bushing – {side.title()}, {g.title()} Shaft', 'bearings', section='split',
                           explode=(0, ey, 0), info={'ref': 'bushing'})
                p.add_split(*lathe_split(pid, prof, 'bronze', 48, axis='Y', center=(0, 0, z), phase=math.pi / 2))

    # ================= GEARS ==============================================
    pts, g = involute_gear_profile(MOD, Z_T, ALPHA, steps=8, backlash=0.0004)
    hf = FACE / 2 - 0.0002

    def gear(name, zc, phase):
        pp = [(x * math.cos(phase) - y * math.sin(phase), y * math.cos(phase) + x * math.sin(phase) + zc)
              for x, y in pts]
        o = extrude_poly(name, pp, -hf, hf, 'steel', plane='XZ')
        return o
    dg = gear('drive_gear', ZD, 0.0)
    ds = lathe('drive_shaft', [(0, -0.062), (R_S - 0.001, -0.062), (R_S, -0.061), (R_S, 0.215),
                               (R_S - 0.0015, 0.2165), (0, 0.2165)], 'steel', 40, axis='Y', center=(0, 0, ZD))
    key = box('key', (0.006, 0.032, 0.006), (0, 0.19, ZD + R_S), 'steel_dark', bevel=0.0008)
    p = m.part('drive_gear_shaft', 'Drive Gear & Shaft', 'rotating_element', pivot=(0, 0, ZD),
               explode=(0, -0.17, 0.10), info={'ref': 'drive_gear'})
    p.add(join('drive_gear_shaft', [dg, ds, key]), smooth_angle=30)
    p.spin('Y', 1)
    ig = gear('idler_gear', ZI, math.pi / Z_T)
    is_ = lathe('idler_shaft', [(0, -0.062), (R_S - 0.001, -0.062), (R_S, -0.061), (R_S, 0.061),
                                (R_S - 0.001, 0.062), (0, 0.062)], 'steel', 40, axis='Y', center=(0, 0, ZI))
    p = m.part('idler_gear_shaft', 'Idler (Driven) Gear & Shaft', 'rotating_element', pivot=(0, 0, ZI),
               explode=(0, -0.17, -0.10), info={'ref': 'idler_gear'})
    p.add(join('idler_gear_shaft', [ig, is_]), smooth_angle=30)
    p.spin('Y', -1)

    # ================= MECHANICAL SEAL ====================================
    c = (0, 0, ZD)
    seal = [
        lathe_split('ms_sleeve', [(R_S, 0.08), (R_S + 0.004, 0.08), (R_S + 0.004, 0.122), (R_S, 0.122)],
                    'stainless', 40, axis='Y', center=c, phase=math.pi / 2),
        lathe_split('ms_spring', [(0.022, 0.098), (0.029, 0.098), (0.029, 0.11), (0.022, 0.11)],
                    'stainless', 40, axis='Y', center=c, phase=math.pi / 2),
        lathe_split('ms_face', [(0.0205, 0.086), (0.028, 0.086), (0.028, 0.098), (0.0205, 0.098)],
                    'carbon', 40, axis='Y', center=c, phase=math.pi / 2),
        lathe_split('ms_seat', [(0.0205, 0.076), (0.031, 0.076), (0.031, 0.086), (0.0205, 0.086)],
                    'silicon_carbide', 40, axis='Y', center=c, phase=math.pi / 2),
    ]
    p = m.part('mechanical_seal', 'Mechanical Seal', 'mechanical_seal', section='split', explode=(0, 0.42, 0))
    p.add_split(*merge_halves('mechanical_seal', seal))
    gl = lathe_split('gland', [(R_S + 0.0015, 0.115), (0.05, 0.115), (0.05, 0.127), (R_S + 0.0015, 0.127)],
                     'stainless', 64, axis='Y', center=c, phase=math.pi / 2)
    gn = split_faces(join('gl_n', [hex_prism(f'gn{i}', 0.013, 0.127, 0.136, 'steel_dark', axis='Y',
                                             center=(sx * 0.038, 0, ZD)) for i, sx in enumerate((1, -1))]),
                     'x', 0.0, keep_positive=False)
    p = m.part('seal_gland', 'Seal Gland Plate', 'mechanical_seal', section='split', explode=(0, 0.5, 0))
    p.add_split(*merge_halves('seal_gland', [gl, gn]))

    # ================= RELIEF VALVE =======================================
    zv = ZC + HH + 0.032
    vh_out = [cyl('rv_body', 0.03, -0.068, 0.068, 'paint_green', 64, axis='X', center=(0, 0, zv), ch=0.003),
              box('rv_pad', (0.13, 0.06, 0.03), (0, 0, ZC + HH + 0.013), 'paint_green', bevel=0.003),
              cyl('rv_bonnet', 0.021, -0.1, -0.06, 'paint_green', 48, axis='X', center=(0, 0, zv), ch=0.002)]
    vh_in = [cyl('rv_spring_ch', 0.0165, -0.11, 0.03, 'paint_green', 48, axis='X', center=(0, 0, zv)),
             cyl('rv_seat', 0.008, 0.02, 0.05, 'paint_green', 32, axis='X', center=(0, 0, zv)),
             cyl('rv_in_ch', 0.0145, 0.044, 0.062, 'paint_green', 48, axis='X', center=(0, 0, zv)),
             cyl('rv_d1', 0.006, ZC + HH - 0.01, zv, 'paint_green', 24, center=(0.05, 0, 0)),
             cyl('rv_d2', 0.006, ZC + HH - 0.01, zv, 'paint_green', 24, center=(-0.05, 0, 0))]
    vh = csg('rv_housing', vh_out, vh_in, 'paint_green')
    vb, vf = split(vh, 'y', 0.0)
    vbolts = split_faces(join('rv_bolts', [cyl(f'rvb{i}', 0.007, ZC + HH + 0.028, ZC + HH + 0.036, 'steel_dark', 24,
                                               center=(sx * 0.058, sy * 0.022, 0), ch=0.001)
                                           for i, (sx, sy) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1)))]),
                         'y', 0.0)
    p = m.part('relief_valve_body', 'Relief Valve Body', 'relief_valve', section='split', explode=(0, 0, 0.16))
    p.add_split(*merge_halves('relief_valve_body', [(vb, vf), vbolts]), smooth_angle=40)

    pop = lathe('poppet', [(0, 0.0), (0.006, 0.0), (0.006, 0.012), (0.0145, 0.014), (0.0145, 0.026),
                           (0.011, 0.03), (0.004, 0.04), (0, 0.041)], 'stainless', 48, axis='X',
                center=(0, 0, zv))
    p = m.part('relief_poppet', 'Relief Valve Poppet', 'relief_valve', explode=(0.13, 0, 0.16))
    p.add(pop)
    n_turns, x0, x1, rc_, rw = 7, -0.058, 0.0, 0.011, 0.0021
    path = []
    for i in range(n_turns * 24 + 1):
        t = i / (n_turns * 24)
        a = TAU * n_turns * t
        path.append((x0 + (x1 - x0) * t, rc_ * math.cos(a), zv + rc_ * math.sin(a)))
    p = m.part('relief_spring', 'Relief Valve Spring', 'relief_valve', explode=(-0.05, 0, 0.26))
    p.add(sweep_tube('relief_spring', path, rw, 'steel', 10), smooth_angle=80)
    scr = [cyl('adj_plate', 0.0155, -0.066, -0.058, 'steel', 40, axis='X', center=(0, 0, zv)),
           cyl('adj_screw', 0.009, -0.135, -0.066, 'steel', 6, axis='X', center=(0, 0, zv)),
           hex_prism('lock_nut', 0.026, -0.112, -0.1, 'steel_dark', axis='X', center=(0, 0, zv))]
    p = m.part('relief_adjuster', 'Adjusting Screw & Lock Nut', 'relief_valve', explode=(-0.16, 0, 0.16))
    p.add(join('relief_adjuster', scr))
    cap = lathe('cap', [(0, -0.172), (0.012, -0.172), (0.017, -0.164), (0.017, -0.112), (0.0095, -0.112),
                        (0.0095, -0.162), (0, -0.162)], 'steel_dark', 48, axis='X', center=(0, 0, zv))
    p = m.part('relief_cap', 'Valve Cap', 'relief_valve', section='hide', explode=(-0.24, 0, 0.16))
    p.add(cap)

    # ================= FLOW PATHS =========================================
    yf = -0.034
    rm = (g['ra'] + g['rf']) / 2
    for sgn, zc_ in ((1, ZD), (-1, ZI)):
        arc = []
        for i in range(25):
            ph = math.radians(200 - 220 * i / 24) if sgn > 0 else math.radians(160 + 220 * i / 24)
            arc.append((rm * math.cos(ph), yf, zc_ + rm * math.sin(ph)))
        start = [(-0.25, yf, ZC), (-0.12, yf, ZC), (-0.06, yf, ZC + sgn * 0.004)]
        m.flow(f'flow_suction_{sgn:+d}', start + arc[:14], 'flow_suction', 0.0035, 0.06)
        m.flow(f'flow_discharge_{sgn:+d}', arc[13:] + [(0.06, yf, ZC + sgn * 0.004), (0.12, yf, ZC),
                                                       (0.25, yf, ZC)], 'flow_discharge', 0.0035, 0.06)
    return m.export(out_dir)


META = {
    'summary': ('Two meshing spur gears turn inside a close-fitting figure-8 housing. On the inlet side the '
                'teeth come out of mesh, opening volume that draws liquid in; the liquid is carried around '
                'the outside of each gear in the tooth spaces and is displaced into the outlet where the '
                'teeth re-mesh. Flow is nearly proportional to speed; pressure is set by the system, so '
                'over-pressure protection (relief valve) is essential.'),
    'classification': {
        'family': 'Positive displacement – rotary',
        'configuration': 'External gear, two shafts, gears supported between bearings (sleeve bushings)',
        'drive': 'One driven (drive) gear transmits torque to the idler through the tooth mesh',
    },
    'model_configuration': {
        'gears': f'{Z_T} teeth, module {MOD*1000:.0f} mm, pressure angle {ALPHA:.0f}°, face width {FACE*1000:.0f} mm',
        'centre_distance_mm': A * 1000,
        'theoretical_displacement_note': ('Approximate geometric displacement per revolution ≈ 2·π·m²·z·b '
                                          '(standard-gear approximation); with these values ≈ 0.16 L/rev. '
                                          'Verify any real pump against manufacturer data.'),
        'theoretical_displacement_l_per_rev': round(2 * math.pi * MOD ** 2 * Z_T * FACE * 1000, 3),
        'shaft_seal': 'Single mechanical seal in rear cover',
        'relief_valve': 'Integral spring-loaded poppet valve, discharge → suction (internal recirculation)',
        'rotation': 'Drive gear clockwise viewed from the drive-shaft end (rear); inlet on left, outlet on right in default view',
    },
    'standards': [
        {'id': 'API 676', 'title': 'Positive Displacement Pumps – Rotary',
         'relevance': 'Requirements for rotary PD pumps in petroleum, petrochemical and gas industry services.',
         'edition': 'to be verified'},
        {'id': 'ANSI/HI 3.1-3.5', 'title': 'Rotary Pumps for Nomenclature, Definitions, Application, and Operation',
         'relevance': 'Terminology, application and operation of rotary pumps.', 'edition': 'to be verified'},
        {'id': 'ANSI/HI 3.6', 'title': 'Rotary Pump Tests', 'relevance': 'Performance test methods.',
         'edition': 'to be verified'},
        {'id': 'ISO 4409', 'title': 'Hydraulic fluid power – Positive-displacement pumps, motors and integral transmissions – Methods of testing and presenting basic steady-state performance',
         'relevance': 'Applies where gear pumps are used in hydraulic power systems.', 'edition': 'to be verified'},
    ],
    'references': [
        'Karassik et al. – Pump Handbook, rotary pump chapters.',
        'Hydraulic Institute ANSI/HI 3.1-3.5 (rotary pumps).',
        'Standard involute gear geometry (ISO 53 basic rack, ISO 21771) for the tooth form.',
    ],
    'components': {
        'pump_body': {
            'function': 'Forms the figure-8 gear chamber, the inlet and outlet ports and the mounting feet; its bore wall seals the tooth tips.',
            'construction': 'Cast body machined with two intersecting bores; ports are opposite each other at the gear mesh; bolt holes and dowels locate the covers.',
            'material': 'Cast iron or ductile iron (general/oil service), cast steel, stainless steel (CF8M) for corrosive or food service.',
            'operating_conditions': 'Pressure rises around the periphery from inlet to outlet, producing a radial load on the gears toward the inlet side.',
            'failure_modes': ['Bore wear on the inlet side from radial gear load', 'Erosion from abrasive particles', 'Cracking from over-pressure if relief protection fails'],
            'inspection': ['Measure tip-to-bore clearance', 'Inspect inlet-side bore for scoring', 'Check port flanges for cracks'],
        },
        'front_cover': {
            'function': 'Closes the gear chamber and carries the front bushings; its inner face controls the gear end clearance.',
            'construction': 'Machined cover with bushing bores; often includes relief grooves that vent liquid trapped between meshing teeth.',
            'material': 'Same as body.',
            'operating_conditions': 'End clearance is a major internal leakage (slip) path.',
            'failure_modes': ['Face wear increasing end clearance and slip', 'Bushing bore wear'],
            'inspection': ['Measure gear end clearance (shim/gasket thickness controls it on some designs)', 'Check face flatness'],
        },
        'rear_cover': {
            'function': 'Closes the chamber on the drive side, carries the rear bushings and forms the seal chamber for the drive shaft.',
            'construction': 'Machined cover with through-bore for the drive shaft and a seal chamber; blind bore for the idler shaft.',
            'material': 'Same as body.',
            'operating_conditions': 'Seal chamber is commonly vented to suction pressure through internal passages.',
            'failure_modes': ['Seal chamber corrosion', 'Bushing bore wear'],
            'inspection': ['Seal-chamber bore and face run-out', 'Bushing fit'],
        },
        'bushing': {
            'function': 'Radial support for the gear shafts on both sides of the gears.',
            'construction': 'Plain sleeve bearing pressed into the cover; lubricated by the pumped liquid ("product-lubricated").',
            'material': 'Bronze, carbon-graphite, silicon carbide or PTFE-lined steel depending on fluid lubricity and abrasives.',
            'operating_conditions': 'Requires a liquid with adequate lubricity; very low viscosity or dry running causes rapid wear.',
            'failure_modes': ['Wear allowing gear tips to contact the bore', 'Seizure on dry running', 'Abrasive wear'],
            'inspection': ['Shaft-to-bushing clearance', 'Bore scoring on the inlet side (sign of bushing wear)'],
        },
        'drive_gear': {
            'function': 'Receives torque from the driver and drives the idler gear through the mesh; displaces liquid.',
            'construction': 'Involute spur gear integral with, or keyed to, the drive shaft which passes through the seal to the coupling.',
            'material': 'Carburised/hardened alloy steel for oil service; stainless steel or nitrided steel for corrosive service.',
            'operating_conditions': 'Speed typically limited by viscosity and NPSH; rotation direction fixes which port is the inlet.',
            'failure_modes': ['Tooth wear and pitting', 'Tooth breakage from over-pressure or debris', 'Shaft fatigue at keyway'],
            'inspection': ['Tooth profile wear, tip and face scoring', 'Shaft run-out and journal wear'],
        },
        'idler_gear': {
            'function': 'Meshes with the drive gear to form the second displacement path; rotates in the opposite direction.',
            'construction': 'Identical tooth form to the drive gear on a short shaft supported in two bushings.',
            'material': 'As drive gear.',
            'operating_conditions': 'Driven only through the mesh; no external shaft.',
            'failure_modes': ['Tooth wear', 'Bushing wear'],
            'inspection': ['As drive gear'],
        },
        'mechanical_seal': {
            'function': 'Seals the drive shaft where it leaves the pump.',
            'construction': 'Rotating carbon face loaded by a spring against a stationary silicon carbide seat; secondary elastomer seals. Packing or lip seals are alternatives on some pumps.',
            'material': 'Carbon / SiC faces; stainless steel metal parts; elastomers per fluid.',
            'operating_conditions': 'Faces must stay lubricated; seal chamber pressure depends on internal venting.',
            'failure_modes': ['Dry running', 'Crystallising or high-viscosity fluids holding faces open', 'Elastomer attack'],
            'inspection': ['Leakage, temperature', 'Face condition at overhaul'],
        },
        'seal_gland': {
            'function': 'Holds the stationary seat and closes the seal chamber.',
            'construction': 'Bolted plate with static gasket/O-ring.',
            'material': 'Stainless steel.',
            'operating_conditions': 'Static.',
            'failure_modes': ['Uneven bolt tightening distorting the seat'],
            'inspection': ['Tighten evenly; check perpendicularity'],
        },
        'relief_valve_body': {
            'function': 'Houses the relief poppet and connects the discharge side to suction to limit maximum pressure.',
            'construction': 'Housing on top of the body with internal drillings to the inlet and outlet passages.',
            'material': 'Same as body.',
            'operating_conditions': 'An internal relief valve is for protection only; continuous recirculation heats the liquid. A separate system relief valve is normally required by the system design.',
            'failure_modes': ['Seat erosion', 'Sticking poppet', 'Incorrect set pressure'],
            'inspection': ['Verify set pressure on test', 'Check seat and poppet for wear'],
        },
        'relief_poppet': {
            'function': 'Seals on the seat until discharge pressure overcomes spring force, then opens to bypass flow to suction.',
            'construction': 'Guided cone-tipped poppet.',
            'material': 'Stainless or hardened steel.',
            'operating_conditions': 'Opens at set pressure plus accumulation; full-flow bypass pressure is higher than cracking pressure.',
            'failure_modes': ['Chatter', 'Seat wear', 'Sticking'],
            'inspection': ['Seat contact pattern'],
        },
        'relief_spring': {
            'function': 'Sets the cracking pressure of the relief valve.',
            'construction': 'Helical compression spring between poppet and adjusting plate.',
            'material': 'Spring steel or stainless spring steel.',
            'operating_conditions': 'Spring range must suit the required set pressure.',
            'failure_modes': ['Relaxation lowering set pressure', 'Corrosion fatigue'],
            'inspection': ['Free length and set-pressure check'],
        },
        'relief_adjuster': {
            'function': 'Adjusts spring compression (set pressure); lock nut fixes the setting.',
            'construction': 'Threaded screw with spring plate and lock nut.',
            'material': 'Steel / stainless steel.',
            'operating_conditions': 'Adjust only per manufacturer procedure with a pressure gauge.',
            'failure_modes': ['Setting drift if lock nut loose'],
            'inspection': ['Witness-mark the setting'],
        },
        'relief_cap': {
            'function': 'Covers the adjusting screw and prevents tampering/leakage.',
            'construction': 'Threaded cap with gasket.',
            'material': 'Steel.',
            'operating_conditions': 'Static.',
            'failure_modes': ['Gasket leakage'],
            'inspection': ['Visual'],
        },
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
