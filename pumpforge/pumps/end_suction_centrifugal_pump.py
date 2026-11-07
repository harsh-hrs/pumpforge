"""
End Suction Centrifugal Pump (API 610 OH1 / ISO 2858 / ASME B73.1 style) — frame-mounted,
back-pull-out, single-stage overhung pump: axial suction, top-centreline discharge, closed
impeller with front and back wear rings and balance holes, casing cover with cartridge seal,
bearing frame (radial + duplex thrust bearings), spacer coupling, foot-mounted motor.
Shaft along +X (suction at -X), cut plane y = 0.
"""
import math
from mathutils import Vector
from pumpforge.core import Model, lathe, cyl, box, csg, split, join, split_faces, split_many
from pumpforge.parts import (H_FRAME, place, radial_impeller, volute_casing, add_impeller, nozzle_bolts, add_oh_drive,
                             add_baseplate, pressure_gauge)
from pumpforge.common_meta import C

ID = 'end_suction_centrifugal_pump'
CZ = 0.36
BP = 0.10


def build(out_dir):
    m = Model(ID, 'End Suction Centrifugal Pump (OH1, Back-Pull-Out)', '1 · Centrifugal & Rotodynamic Pumps', META)
    Mx = H_FRAME(0.0, CZ)
    W = lambda p: tuple(Mx @ Vector(p))
    core, shroud, imp = radial_impeller('impeller', 0.26, 0.026, 0.055, 0.022, n_blades=6, mat='bronze', wrap=1.8)
    cas, geo = volute_casing('volute', imp, 'paint_blue_dark', r_suc=0.062, L_suc=0.16, r_dis=0.045, H_dis=0.27, flange=True)
    place(cas, Mx)
    zb, r3 = geo['z_back'], geo['r3']
    # casing foot (centreline-ish support under the volute) and drain boss
    foot = box('cfoot', (0.09, 0.30, CZ - r3 - BP), (zb - 0.06, 0, BP + (CZ - r3 - BP) / 2 + 0.01), 'paint_blue_dark', bevel=0.004)
    drain = cyl('drain', 0.014, CZ - r3 - 0.05, CZ - r3 + 0.0, 'steel_dark', 6, center=(imp['zc'], 0.04, 0))
    body = join('casing', [cas, foot])
    cb, cf = split(body)
    dx, dy, _ = W((geo['Rend'], geo['H_dis'], geo['zc']))
    bolts = [nozzle_bolts('sfb', 8, geo['sflange_r'] - 0.016, 0.009, -geo['L_suc'] - 0.012, -geo['L_suc'] + geo['tf'] + 0.012, 'X', (0, 0, CZ), math.pi / 8),
             nozzle_bolts('dfb', 8, geo['dflange_r'] - 0.016, 0.009, CZ + geo['H_dis'] - geo['tf'] - 0.012, CZ + geo['H_dis'] + 0.012, 'Z', (dx, dy, 0), math.pi / 8)]
    bb, bf = split_faces(join('bolts', bolts + [drain]), 'y', 0.0)
    p = m.part('casing', 'Volute Casing (Axial Suction, Top Discharge)', 'casing', section='split', explode=(-0.5, 0, 0), info={'ref': 'volute_casing'})
    p.add_split(join('cb', [cb, bb]), join('cf', [cf, bf]), smooth_angle=40)
    # wear rings: casing ring at the eye, back ring on the cover side
    rw, nk = imp['r_wear'], imp['neck']
    wr = [lathe('wr_front', [(rw + 0.0012, -nk), (rw + 0.008, -nk), (rw + 0.008, 0.002), (rw + 0.0012, 0.002)], 'bronze', 96, axis='Z'),
          lathe('wr_back', [(0.05, imp['zf'] + imp['b2'] + 0.006), (0.062, imp['zf'] + imp['b2'] + 0.006), (0.062, imp['zf'] + imp['b2'] + 0.018),
                            (0.05, imp['zf'] + imp['b2'] + 0.018)], 'bronze', 96, axis='Z')]
    for o in wr:
        place(o, Mx)
    wb, wf = split_many('wear_rings', wr)
    p = m.part('wear_rings', 'Casing Wear Rings (Front & Back)', 'casing', section='split', explode=(-0.3, 0, -0.15), info={'ref': 'wear_ring'})
    p.add_split(wb, wf)
    add_impeller(m, 'impeller', 'Closed Impeller (6 vanes, balance holes)', core, shroud, Mx, (0, 0, CZ), explode=(-0.22, 0, 0.15), ref='impeller_closed')
    add_oh_drive(m, zb, CZ, BP, 0.022, imp['zf'] - 0.01, frame_R=0.08, frame_L=0.36, motor_R=0.14, motor_L=0.48,
                 frame_mat='paint_blue', cover_r=geo['r_bf'])
    add_baseplate(m, -geo['L_suc'] - 0.1, 1.72, 0.52, BP)
    g = [pressure_gauge('gs', (-geo['L_suc'] + 0.06, 0.0, CZ + geo['r_suc'] + 0.02)), pressure_gauge('gd', (dx, dy, CZ + geo['H_dis'] - 0.06))]
    p = m.part('gauges', 'Suction & Discharge Pressure Gauges', 'instrumentation', explode=(0, -0.3, 0.3), info={'ref': 'pressure_gauge'})
    p.add(join('gauges', g), smooth_angle=50)
    zc = geo['zc']
    m.flow('flow_suction', [(-geo['L_suc'] - 0.3, 0, CZ), W((0, 0, -0.04)), W((0, 0, zc - 0.01))], 'flow_suction', 0.009, 0.12)
    pts = [W((0.02, 0.0, zc)), W((r3 * 0.8, 0.0, zc))]
    for i in range(1, 15):
        th = 0.45 + (2 * math.pi - 0.45) * i / 14
        R = r3 + 0.3 * geo['a_max'] * (0.3 + 0.7 * i / 14)
        pts.append(W((R * math.cos(th), R * math.sin(th), zc)))
    pts += [W((geo['Rend'], geo['H_dis'] * 0.6, zc)), W((geo['Rend'], geo['H_dis'] + 0.2, zc))]
    m.flow('flow_discharge', pts, 'flow_discharge', 0.008, 0.12)
    return m.export(out_dir)


META = {
    'summary': ('The end suction pump is the most widely used centrifugal pump. Liquid enters axially into the eye of a single '
                'impeller, is accelerated outward by the rotating vanes, and is collected by a spiral volute that converts '
                'velocity into pressure before leaving through the top discharge nozzle. In the frame-mounted, back-pull-out '
                'design (API 610 OH1, ISO 2858 / ASME B73.1), the impeller, seal, bearing frame and shaft can be withdrawn '
                'towards the motor as one unit, using a spacer coupling, without disturbing the casing or the pipework.'),
    'classification': {'family': 'Rotodynamic (centrifugal), radial flow, single stage', 'configuration': 'Overhung, end suction, frame-mounted, foot-mounted casing',
                       'api_610_type': 'OH1 (foot-mounted overhung)', 'dimensional_standards': 'ISO 2858 / ASME B73.1 (chemical process) or EN 733 (water)'},
    'model_configuration': {'impeller': 'Closed, 6 backward-curved vanes, front and back wear rings, balance holes to reduce axial thrust',
                            'shaft_seal': 'Cartridge mechanical seal in a casing-cover seal chamber',
                            'bearings': 'Radial ball bearing (inboard) + duplex angular-contact thrust bearing (outboard), oil-lubricated frame',
                            'drive': 'Spacer coupling to a foot-mounted electric motor on a common baseplate (back pull-out)'},
    'standards': [
        {'id': 'API 610 / ISO 13709', 'title': 'Centrifugal pumps for petroleum, petrochemical and natural gas industries', 'relevance': 'OH1 type definition, heavy-duty requirements.', 'edition': 'to be verified'},
        {'id': 'ISO 2858', 'title': 'End-suction centrifugal pumps (rating 16 bar) — Designation, nominal duty point and dimensions', 'relevance': 'Interchangeable dimensions.', 'edition': 'to be verified'},
        {'id': 'ASME B73.1', 'title': 'Specification for Horizontal End Suction Centrifugal Pumps for Chemical Process', 'relevance': 'ANSI process pump dimensions and design.', 'edition': 'to be verified'},
        {'id': 'ANSI/HI 1.1-1.2, 1.3', 'title': 'Rotodynamic centrifugal pumps — nomenclature; design and application', 'relevance': 'Terminology and application.', 'edition': 'to be verified'},
        {'id': 'ISO 9906', 'title': 'Rotodynamic pumps — Hydraulic performance acceptance tests', 'relevance': 'Performance testing.', 'edition': 'to be verified'},
    ],
    'references': ['Hydraulic Institute — Pump Types (rotodynamic, overhung).', 'KSB Pump Lexicon — "Volute casing pump", "Back pull-out design".',
                   'US DOE — Improving Pumping System Performance: A Sourcebook for Industry.', 'Karassik et al., Pump Handbook.'],
    'components': {},
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
