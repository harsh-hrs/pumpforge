"""
Submersible Sewage Pump — close-coupled submersible pump with a 2-channel
non-clog impeller, volute casing, oil chamber with tandem mechanical seals,
dry submersible motor, and guide-rail auto-coupling (duckfoot) installation.
Axis Z; wet-well floor at z = 0.
"""
import math
from pumpforge.core import (Model, lathe, lathe_split, ring_profile, cyl, box, csg, split, join, merge_halves, split_faces,
                            split_many, group_by, TAU)
from pumpforge.parts import V_FRAME, place, radial_impeller, volute_casing, add_impeller, ball_bearing, seal_cartridge, pipe, nozzle_bolts
from pumpforge.shapes import sweep_tube
from pumpforge.common_meta import C

ID = 'submersible_sewage_pump'
ZE = 0.16        # impeller eye plane


def build(out_dir):
    m = Model(ID, 'Submersible Sewage Pump (Non-Clog, Guide-Rail Installation)', 'A · Centrifugal & Special Hydraulic Pumps', META)
    Mx = V_FRAME(ZE)
    core, shroud, imp = radial_impeller('impeller', 0.25, 0.06, 0.06, 0.02, n_blades=2, mat='cast_iron', wrap=2.6, t=0.008)
    cas, geo = volute_casing('volute', imp, 'paint_blue_dark', r_suc=0.07, L_suc=0.08, r_dis=0.05, H_dis=0.17, t=0.014)
    place(cas, Mx)
    zb = ZE + geo['z_back']
    feet = [box(f'ft{i}', (0.04, 0.04, ZE - 0.08), (0.14 * math.cos(a), 0.14 * math.sin(a), (ZE - 0.08) / 2), 'paint_blue_dark')
            for i, a in enumerate((math.pi / 4, 3 * math.pi / 4, 5 * math.pi / 4))]
    cas = csg('casing', [cas] + feet, [], 'paint_blue_dark')
    cb, cf = split(cas)
    p = m.part('volute_casing', 'Volute Casing', 'casing', section='split', explode=(0, 0, -0.3), info={'ref': 'volute_casing'})
    p.add_split(cb, cf, smooth_angle=40)
    add_impeller(m, 'impeller', 'Two-Channel Non-Clog Impeller', core, shroud, Mx, (0, 0, ZE), axis='Z', explode=(0.0, 0, -0.12),
                 ref='impeller_nonclog', revs=2)
    # motor housing + oil chamber
    R = 0.15
    z_oc = zb + 0.02
    z_m0, z_m1 = z_oc + 0.12, z_oc + 0.52
    hs = csg('housing', [lathe('hs', [(0.03, zb), (geo['r_bf'], zb), (geo['r_bf'], zb + 0.02), (R, zb + 0.04), (R, z_m1 + 0.02),
                                      (R - 0.02, z_m1 + 0.06), (0.05, z_m1 + 0.08), (0.0, z_m1 + 0.08), (0.0, z_m1 + 0.06), (0.03, z_m1 + 0.06)],
                                'paint_blue_dark', 96),
                          cyl('cable_entry', 0.03, z_m1 + 0.06, z_m1 + 0.13, 'paint_blue_dark', 32, center=(-0.06, 0, 0), ch=0.004)],
             [lathe('hsi', [(0.025, zb - 0.01), (0.07, zb + 0.03), (R - 0.012, zb + 0.05), (R - 0.012, z_oc + 0.1), (0.03, z_oc + 0.11),
                            (0.03, z_oc + 0.13), (R - 0.012, z_oc + 0.13), (R - 0.012, z_m1 + 0.04), (0.0, z_m1 + 0.05), (0, zb - 0.01)],
                    'paint_blue_dark', 96)], 'paint_blue_dark')
    hb, hf = split(hs)
    p = m.part('motor_housing', 'Motor Housing & Oil Chamber', 'motor', section='split', explode=(0, 0, 0.55), info={'ref': 'sub_motor_housing'})
    p.add_split(hb, hf, smooth_angle=40)
    handle = sweep_tube('handle', [(-0.08, 0, z_m1 + 0.07), (-0.08, 0, z_m1 + 0.18), (0.08, 0, z_m1 + 0.18), (0.08, 0, z_m1 + 0.07)], 0.012,
                        'stainless', 16)
    p = m.part('lifting_handle', 'Lifting Handle', 'installation', explode=(0, 0, 0.8), info={'ref': 'lifting'})
    p.add(handle, smooth_angle=60)
    st = merge_halves('stator', [lathe_split('st', [(0.07, z_m0 + 0.05), (R - 0.012, z_m0 + 0.05), (R - 0.012, z_m1 - 0.05), (0.07, z_m1 - 0.05)],
                                             'lamination', 96),
                                 lathe_split('w1', [(0.072, z_m0 + 0.01), (0.11, z_m0 + 0.01), (0.11, z_m0 + 0.05), (0.072, z_m0 + 0.05)], 'copper', 64),
                                 lathe_split('w2', [(0.072, z_m1 - 0.05), (0.11, z_m1 - 0.05), (0.11, z_m1 - 0.01), (0.072, z_m1 - 0.01)], 'copper', 64)])
    p = m.part('stator', 'Stator', 'motor', section='split', explode=(-0.5, 0, 0.5), info={'ref': 'stator'})
    p.add_split(*st)
    rot = [cyl('rotor', 0.067, z_m0 + 0.055, z_m1 - 0.055, 'lamination', 64),
           cyl('shaft', 0.02, ZE + imp['z_back'] - 0.03, z_m1 + 0.03, 'stainless', 32, ch=0.002)]
    p = m.part('rotor', 'Rotor & Shaft', 'rotating_element', explode=(0.5, 0, 0.5), info={'ref': 'rotor'})
    p.add(join('rotor', rot)); p.spin('Z', 2)
    br = merge_halves('brg', [ball_bearing('b1', 0.02, 0.045, z_oc + 0.13, z_oc + 0.155, 10, axis='Z'),
                              ball_bearing('b2', 0.02, 0.045, z_m1 + 0.005, z_m1 + 0.03, 10, axis='Z')])
    p = m.part('bearings', 'Motor Bearings', 'bearings', section='split', explode=(0.5, 0, 0.8), info={'ref': 'motor_bearings'})
    p.add_split(*br)
    s1 = seal_cartridge('seal_lo', zb - 0.01, zb + 0.05, 0.02, 0.042, axis='Z')
    s2 = seal_cartridge('seal_up', z_oc + 0.03, z_oc + 0.09, 0.02, 0.042, axis='Z')
    p = m.part('mechanical_seals', 'Tandem Mechanical Seals (in Oil Chamber)', 'mechanical_seal', section='split', explode=(-0.45, 0, 0.1),
               info={'ref': 'tandem_seals'})
    p.add_split(*merge_halves('seals', [s1, s2]))
    # duckfoot, guide rails, discharge riser
    xn = geo['H_dis']
    yn = -geo['Rend']
    zd = ZE + imp['zc']
    claw = csg('claw', [box('cl', (0.04, 0.2, 0.14), (xn + 0.02, yn, zd + 0.02), 'paint_blue_dark', bevel=0.01),
                        cyl('cfl', 0.1, xn - 0.02, xn + 0.0, 'paint_blue_dark', 48, axis='X', center=(0, yn, zd))],
               [cyl('clb', 0.05, xn - 0.05, xn + 0.06, 'paint_blue_dark', 48, axis='X', center=(0, yn, zd))], 'paint_blue_dark')
    p = m.part('guide_claw', 'Guide Claw & Sealing Flange', 'installation', explode=(0.1, -0.1, 0.2), info={'ref': 'guide_claw'})
    p.add(claw, smooth_angle=40)
    xf = xn + 0.04
    df_out = [pipe('dfo', [(xf, yn, zd), (xf + 0.22, yn, zd), (xf + 0.22, yn, 1.4)], 0.062, 'paint_blue_dark', 40, bend=0.12),
              box('dfb', (0.32, 0.3, 0.025), (xf + 0.16, yn, 0.0125), 'paint_blue_dark', bevel=0.004),
              box('dfw', (0.1, 0.14, zd - 0.06), (xf + 0.2, yn, zd / 2), 'paint_blue_dark'),
              cyl('dfl', 0.1, xf, xf + 0.02, 'paint_blue_dark', 48, axis='X', center=(0, yn, zd))]
    df = csg('duckfoot', df_out, [pipe('dfi', [(xf - 0.02, yn, zd), (xf + 0.22, yn, zd), (xf + 0.22, yn, 1.45)], 0.05, 'paint_blue_dark', 40,
                                       bend=0.12)], 'paint_blue_dark')
    db, dff = split_many('duckfoot', [df], 'y', yn)
    p = m.part('duckfoot', 'Duckfoot Bend (Auto-Coupling Base) & Riser', 'installation', section='split', explode=(0.35, 0, 0),
               info={'ref': 'duckfoot'})
    p.add_split(db, dff, smooth_angle=40)
    rails = [cyl(f'rail{i}', 0.022, 0.03, 1.6, 'stainless', 24, center=(xf + 0.05, yn + sy * 0.07, 0)) for i, sy in enumerate((1, -1))]
    p = m.part('guide_rails', 'Guide Rails (2 in pipe)', 'installation', explode=(0.5, 0, 0), info={'ref': 'guide_rails'})
    p.add(join('rails', rails), smooth_angle=50)
    chain = []
    for i in range(14):
        z = z_m1 + 0.19 + i * 0.05
        lk = lathe(f'lk{i}', [(0.012, -0.003), (0.018, -0.003), (0.018, 0.003), (0.012, 0.003)], 'steel_dark', 16, axis='X' if i % 2 else 'Y',
                   center=(0, 0, z))
        lk.data.transform(__import__('mathutils').Matrix.Diagonal((1, 1, 1.6, 1)) if False else __import__('mathutils').Matrix.Identity(4))
        chain.append(lk)
    cab = sweep_tube('cable', [(-0.06, 0, z_m1 + 0.13), (-0.06, 0, z_m1 + 0.25), (-0.12, 0.05, z_m1 + 0.5), (-0.14, 0.05, 1.6)], 0.012, 'rubber', 12)
    p = m.part('chain_cable', 'Lifting Chain & Power Cable', 'installation', explode=(-0.3, 0, 0.9), info={'ref': 'drop_cable'})
    p.add(join('chain_cable', chain + [cab]), smooth_angle=60)
    fl = join('float', [sweep_tube('fc', [(-0.35, 0.2, 1.5), (-0.35, 0.2, 0.75), (-0.3, 0.2, 0.62)], 0.004, 'rubber', 8),
                        lathe('fb', [(0, -0.05), (0.035, -0.04), (0.04, 0.0), (0.03, 0.05), (0, 0.06)], 'paint_red', 32, center=(-0.3, 0.2, 0.58))])
    p = m.part('float_switch', 'Float Level Switch', 'controls', explode=(-0.3, 0, 0.3), info={'ref': 'level_sensor'})
    p.add(fl, smooth_angle=60)

    Y = 0.0
    m.flow('flow_suction', [(0.0, Y, -0.25), (0.0, Y, 0.0), (0.0, Y, ZE - 0.01)], 'flow_suction', 0.008, 0.12)
    spiral = []
    for i in range(25):
        th = math.pi / 2 + 1.5 * math.pi * i / 24
        Rr = geo['r3'] + 0.8 * geo['a_max'] * (0.4 + 0.6 * i / 24)
        spiral.append((Rr * math.sin(th), -Rr * math.cos(th), zd))
    m.flow('flow_discharge', [(0, 0, ZE + 0.02), (0.0, -0.06, zd)] + spiral + [(xn, yn, zd), (xf + 0.22, yn, zd + 0.05), (xf + 0.22, yn, 1.6)],
           'flow_discharge', 0.008, 0.12)
    return m.export(out_dir)


META = {
    'summary': ('A centrifugal pump and its sealed electric motor form one unit that sits on the floor of a sewage wet well, '
                'fully submerged. Raw sewage enters through the bottom inlet into a two-channel non-clog impeller whose wide '
                'passages pass solids and fibres. Two mechanical seals with an oil chamber between them keep water out of '
                'the motor. The pump slides down two guide rails and couples automatically to the duckfoot bend on the floor, '
                'so it can be lifted out for service without entering the well.'),
    'classification': {'family': 'Rotodynamic (centrifugal), radial flow', 'configuration': 'Submersible, close-coupled, vertical, guide-rail installed'},
    'model_configuration': {'impeller': 'Closed two-channel non-clog (vortex and cutter impellers are alternatives)', 'free_passage_note': 'Free passage (largest sphere passed) is a key selection value — check data sheet.',
                            'seals': 'Tandem mechanical seals with oil barrier and moisture sensor (typical)', 'installation': 'Guide rails + duckfoot auto-coupling'},
    'standards': [
        {'id': 'EN 12050-1', 'title': 'Wastewater lifting plants for buildings and sites', 'relevance': 'Applies to packaged lifting plants (building drainage).', 'edition': 'to be verified'},
        {'id': 'ANSI/HI 11.6', 'title': 'Submersible pump tests', 'relevance': 'Testing of submersible pumps.', 'edition': 'to be verified'},
        {'id': 'IEC 60079 / ATEX', 'title': 'Explosive atmospheres', 'relevance': 'Sewage wet wells may be hazardous areas; explosion-proof motors as required.', 'edition': 'to be verified'},
        {'id': 'ANSI/HI 9.8', 'title': 'Pump Intake Design', 'relevance': 'Wet-well geometry and submergence.', 'edition': 'to be verified'},
    ],
    'references': ['WEF MOP FD-4 / Design of Wastewater and Stormwater Pumping Stations.', 'Manufacturer submersible sewage pump manuals (generic practice).'],
    'components': {
        'impeller_nonclog': C('Pumps sewage containing solids and rags with minimum clogging.', 'Closed impeller with one or two wide channels and rounded leading edges; statically and dynamically balanced.',
                              'Cast iron, ductile iron, hardened high-chrome iron for grit.', 'Free passage and hydraulic efficiency trade off.', ['Rag build-up on leading edges', 'Wear-ring/suction cover wear'],
                              ['Check clearance', 'Remove fibrous build-up']),
        'sub_motor_housing': C('Watertight housing for the motor; oil chamber between the two seals; cable entry and lifting points.', 'Cast iron housing with O-ring sealed joints; cooled by the surrounding liquid (or cooling jacket for dry-pit use).',
                               'Cast iron, stainless steel.', 'Motor must normally be submerged for cooling unless jacketed.', ['Seal leakage into motor', 'Cable entry leak'], ['Oil inspection for water', 'Moisture/thermal sensor tests']),
        'tandem_seals': C('Two mechanical seals in series: the lower seal faces sewage, the upper seal faces the motor; oil between them lubricates and acts as barrier.', 'Lower: SiC/SiC or tungsten carbide faces; upper: carbon/ceramic.',
                          'Silicon carbide, tungsten carbide, carbon, ceramic.', 'Oil condition shows lower-seal health.', ['Lower seal wear from grit', 'Water in oil'], ['Oil check per schedule']),
        'lifting': C('Point for lifting the pump out along the rails.', 'Stainless handle/bail.', 'Stainless steel.', 'Rated for pump weight.', ['Corrosion'], ['Visual']),
        'guide_claw': C('Slides on the guide rails and seals the pump discharge against the duckfoot flange by the pump weight.', 'Bracket with sealing flange (often with rubber profile seal).',
                        'Cast iron with elastomer seal.', 'Leakage at the coupling recirculates flow.', ['Worn seal', 'Misaligned rails'], ['Seal condition']),
        'duckfoot': C('Floor-mounted discharge bend that receives the pump and turns the flow up into the discharge riser.', 'Cast bend with base anchored to the floor; rail brackets.',
                      'Cast iron.', 'Carries riser loads.', ['Anchor corrosion', 'Debris on mating face'], ['Visual during pump lift']),
        'guide_rails': C('Guide the pump down to the duckfoot and back up for service.', 'Two pipes from duckfoot to upper rail bracket.', 'Galvanised or stainless steel.',
                         'Must be vertical and parallel.', ['Corrosion', 'Bent rails'], ['Visual']),
        'level_sensor': C('Starts and stops the pump at set levels and gives high-level alarm.', 'Tilting float switches or hydrostatic level transmitter.', 'Polymer, stainless.',
                          'Set points limit starts per hour and keep the motor submerged.', ['Fouling with grease/rags'], ['Clean and test']),
        'drop_cable': C('Supplies power from the control panel to the motor; chain lifts the pump.', 'Submersible cable with strain relief; galvanised/stainless chain.', 'Rubber-sheathed copper; steel chain.',
                        'Cable must not carry pump weight.', ['Cable chafing'], ['Insulation resistance']),
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
