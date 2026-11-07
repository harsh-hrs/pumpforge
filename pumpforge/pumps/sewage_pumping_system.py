"""
Sewage Pumping System (Lift Station) — circular wet well with inlet pipe and
screen basket, two submersible non-clog pumps on guide rails (duty/standby),
discharge risers into an adjacent valve chamber with check and gate valves,
common rising main, float level controls, vent and control kiosk.
Ground level at z = 0; wet well and valve chamber shown cut away.
"""
import math
from pumpforge.core import Model, lathe, cyl, box, csg, split, join, split_many, TAU
from pumpforge.parts import (frame_matrix, place, radial_impeller, volute_casing, add_impeller, hollow_pipe, gate_valve, check_valve, add_tracers, pipe)
from pumpforge.shapes import sweep_tube
from pumpforge.common_meta import C

ID = 'sewage_pumping_system'
ZF = -3.0       # wet-well floor
RW = 1.2        # wet-well radius


def pump_unit(m, tag, px, py, label):
    ze = ZF + 0.2
    Mx = frame_matrix((px, py, ze), (0, 0, 1), (1, 0, 0))
    core, shroud, imp = radial_impeller(f'imp_{tag}', 0.24, 0.05, 0.06, 0.02, n_blades=2, mat='cast_iron', wrap=2.5, t=0.008)
    cas, geo = volute_casing(f'vol_{tag}', imp, 'paint_blue_dark', r_suc=0.07, L_suc=0.07, r_dis=0.05, H_dis=0.15, t=0.014, flange=False)
    place(cas, Mx)
    zb = ze + geo['z_back']
    zt = zb + 0.6
    shell = csg(f'mh_{tag}', [lathe(f'mho_{tag}', [(0.0, zb), (geo['r_bf'], zb), (0.15, zb + 0.04), (0.15, zt - 0.05), (0.12, zt), (0.0, zt)], 'paint_blue_dark', 64, center=(px, py, 0))],
                [cyl(f'mhi_{tag}', 0.132, zb + 0.07, zt - 0.03, 'paint_blue_dark', 64, center=(px, py, 0)),
                 cyl(f'mhb_{tag}', 0.024, zb - 0.01, zb + 0.08, 'paint_blue_dark', 32, center=(px, py, 0))], 'paint_blue_dark')
    lift = sweep_tube(f'lh_{tag}', [(px - 0.07, py, zt - 0.01), (px - 0.07, py, zt + 0.06), (px + 0.07, py, zt + 0.06), (px + 0.07, py, zt - 0.01)], 0.012, 'stainless', 12)
    claw = box(f'claw_{tag}', (0.08, 0.2, 0.08), (px + 0.17, py, ze + 0.06), 'paint_blue_dark', bevel=0.006)
    legs = [box(f'ft{tag}{i}', (0.04, 0.04, ze - ZF), (px + 0.12 * math.cos(a), py + 0.12 * math.sin(a), (ZF + ze) / 2), 'paint_blue_dark')
            for i, a in enumerate((2 * math.pi / 3, math.pi, 4 * math.pi / 3))]
    b, f = split_many(f'pump_{tag}', [cas, shell, claw] + legs, 'y', py)
    p = m.part(f'pump_{tag}', f'{label} Submersible Pump (Volute + Motor Housing)', 'pumps', section='split', explode=(0, 0, 0.9), info={'ref': 'ss_pump'})
    p.add_split(join(f'pb_{tag}', [b, lift]), f, smooth_angle=40)
    stator = lathe(f'st_{tag}', [(0.088, zb + 0.16), (0.131, zb + 0.16), (0.131, zb + 0.46), (0.088, zb + 0.46)], 'lamination', 64, center=(px, py, 0))
    wind = [lathe(f'ew{k}_{tag}', [(0.092, z0), (0.125, z0), (0.12, z0 + d), (0.097, z0 + d)], 'copper', 48, center=(px, py, 0))
            for k, (z0, d) in enumerate(((zb + 0.16, -0.045), (zb + 0.46, 0.045)))]
    sb_, sf_ = split_many(f'stator_{tag}', [stator] + wind, 'y', py)
    p = m.part(f'stator_{tag}', f'{label} Pump – Motor Stator & Windings', 'motor', section='split', explode=(0, 0, 1.4), info={'ref': 'stator'})
    p.add_split(sb_, sf_, smooth_angle=40)
    rot = [cyl(f'sh_{tag}', 0.02, ze + 0.02, zt - 0.05, 'stainless', 24, center=(px, py, 0)),
           cyl(f'ro_{tag}', 0.084, zb + 0.17, zb + 0.45, 'lamination', 48, center=(px, py, 0)),
           cyl(f'rr1_{tag}', 0.084, zb + 0.16, zb + 0.17, 'aluminium', 48, center=(px, py, 0)), cyl(f'rr2_{tag}', 0.084, zb + 0.45, zb + 0.46, 'aluminium', 48, center=(px, py, 0))]
    p = m.part(f'rotor_{tag}', f'{label} Pump – Rotor & Shaft', 'rotating_element', pivot=(px, py, ze), explode=(0, 0, 1.15), info={'ref': 'rotor'})
    p.add(join(f'rotor_{tag}', rot), smooth_angle=40); p.spin('Z', 2)
    brg = [lathe(f'bru{k}_{tag}', [(0.02, z0), (0.045, z0), (0.045, z0 + 0.025), (0.02, z0 + 0.025)], 'steel', 32, center=(px, py, 0)) for k, z0 in enumerate((zb + 0.09, zb + 0.5))]
    seal = lathe(f'ms_{tag}', [(0.02, zb + 0.005), (0.04, zb + 0.005), (0.04, zb + 0.06), (0.02, zb + 0.06)], 'silicon_carbide', 32, center=(px, py, 0))
    bb_, bf_ = split_many(f'brg_{tag}', brg + [seal], 'y', py)
    p = m.part(f'seals_{tag}', f'{label} Pump – Bearings & Tandem Mechanical Seals', 'bearings', section='split', explode=(0.4, 0, 1.0), info={'ref': 'mechanical_seal'})
    p.add_split(bb_, bf_, smooth_angle=40)
    add_impeller(m, f'impeller_{tag}', f'{label} Pump – Non-Clog Impeller', core, shroud, Mx, (px, py, ze), axis='Z', explode=(0, 0, 0.5), ref='impeller_nonclog_s', split_axis='y', split_at=py)
    xn, yn, zd = px + geo['H_dis'], py - geo['Rend'], ze + imp['zc']
    xr = xn + 0.24
    duck = [hollow_pipe(f'dk_{tag}', [(xn, yn, zd), (xr, yn, zd), (xr, yn, zd + 0.3)], 0.065, 'paint_blue_dark', 32, bend=0.14),
            cyl(f'dkf_{tag}', 0.11, xn, xn + 0.02, 'paint_blue_dark', 48, axis='X', center=(0, yn, zd)),
            box(f'dkp_{tag}', (0.16, 0.16, zd - ZF - 0.05), (xr, yn, ZF + (zd - ZF - 0.05) / 2), 'paint_blue_dark'),
            box(f'dkb_{tag}', (0.34, 0.28, 0.03), (xr - 0.04, yn, ZF + 0.015), 'paint_blue_dark', bevel=0.004)]
    riser = hollow_pipe(f'riser_{tag}', [(xr, yn, zd + 0.3), (xr, yn, -0.6), (1.75, yn, -0.6)], 0.055, 'paint_grey', 32, bend=0.15)
    rails = [cyl(f'rl{tag}{i}', 0.018, zd + 0.1, 0.2, 'stainless', 16, center=(xn + 0.12, yn + s_ * 0.08, 0)) for i, s_ in enumerate((1, -1))]
    rb_, rf_ = split_many(f'riser_{tag}', duck + [riser], 'y', yn)
    p = m.part(f'riser_{tag}', f'{label} Duckfoot Bend, Guide Rails & Discharge Riser', 'system_piping', section='split', explode=(0.3, 0, 0), info={'ref': 'ss_riser'})
    p.add_split(join(f'rbk_{tag}', [rb_] + rails), rf_, smooth_angle=50)
    return dict(xn=xn, yn=yn, zd=zd, ze=ze, xr=xr)


def build(out_dir):
    m = Model(ID, 'Sewage Pumping System (Wet-Well Lift Station)', 'E · Industrial Pump Applications', META)
    # wet well (cut-away half shell) with benching and slab
    ww = lathe('wetwell', [(RW, ZF - 0.25), (RW + 0.25, ZF - 0.25), (RW + 0.25, 0.25), (RW, 0.25)], 'paint_grey', 96, a0=0.0, a1=math.pi, cap_mat='paint_grey')
    floor = lathe('floor', [(0, ZF - 0.25), (RW + 0.25, ZF - 0.25), (RW + 0.25, ZF), (0.6, ZF), (0.3, ZF + 0.0), (0, ZF)], 'paint_grey', 96, a0=0.0, a1=math.pi, cap_mat='paint_grey')
    bench = lathe('bench', [(0.75, ZF), (RW, ZF), (RW, ZF + 0.45)], 'paint_grey', 96, a0=0.0, a1=math.pi, cap_mat='paint_grey')
    lvl = lathe('lvl', [(RW - 0.02, -1.6), (RW, -1.6), (RW, -1.59), (RW - 0.02, -1.59)], 'flow_suction', 96, a0=0.0, a1=math.pi, cap_mat='flow_suction')
    p = m.part('wet_well', 'Wet Well (Concrete, shown cut away) with Benching', 'structure', explode=(0, 0.6, 0), info={'ref': 'ss_wetwell'})
    p.add(join('wet_well', [ww, floor, bench, lvl]), smooth_angle=40)
    slab = csg('slab', [lathe('sl', [(0, 0.25), (RW + 0.25, 0.25), (RW + 0.25, 0.45), (0, 0.45)], 'paint_grey', 96, a0=0.0, a1=math.pi, cap_mat='paint_grey')],
               [box('hatch', (0.9, 1.4, 0.4), (0.25, 0.0, 0.35), 'paint_grey')], 'paint_grey')
    hatch = box('hatch_cover', (0.92, 0.7, 0.02), (0.25, 0.35, 0.46), 'aluminium', bevel=0.004)
    p = m.part('cover_slab', 'Cover Slab & Access Hatch', 'structure', section='hide', explode=(0, 0, 0.8), info={'ref': 'ss_slab'})
    p.add(join('cover_slab', [slab, hatch]), smooth_angle=40)
    # inlet with screen basket
    inl = hollow_pipe('inlet', [(-RW - 0.8, 0.2, -1.2), (-RW + 0.05, 0.2, -1.2)], 0.12, 'paint_grey', 32)
    basket = join('basket', [box('bk', (0.4, 0.4, 0.4), (-RW + 0.3, 0.2, -1.35), 'steel_dark', bevel=0.01)])
    basket = csg('basket', [basket], [box('bki', (0.36, 0.36, 0.4), (-RW + 0.3, 0.2, -1.32), 'steel_dark')], 'steel_dark')
    rails = [cyl('br1', 0.015, -1.15, 0.25, 'stainless', 12, center=(-RW + 0.3, 0.42, 0)), cyl('br2', 0.015, -1.15, 0.25, 'stainless', 12, center=(-RW + 0.3, -0.02, 0))]
    p = m.part('inlet_screen', 'Inlet Pipe & Screen Basket (on Rails)', 'inlet', explode=(-0.5, 0, 0.3), info={'ref': 'ss_inlet'})
    p.add(join('inlet_screen', [inl, basket] + rails), smooth_angle=40)
    a = pump_unit(m, 'duty', -0.1, 0.45, 'Duty')
    b = pump_unit(m, 'standby', -0.1, -0.35, 'Standby')
    # valve chamber with valves and rising main
    vc = csg('valve_chamber', [box('vco', (1.2, 1.9, 1.5), (2.2, 0.0, -0.55), 'paint_grey', bevel=0.01)],
             [box('vci', (1.0, 1.7, 1.5), (2.2, 0.0, -0.4), 'paint_grey'), box('vcw', (0.3, 1.6, 0.3), (1.65, 0.05, -0.6), 'paint_grey')], 'paint_grey')
    vcb, vcf = split(vc, 'y', 0.0)
    p = m.part('valve_chamber', 'Valve Chamber (Concrete)', 'structure', section='split', explode=(0.6, 0, 0), info={'ref': 'ss_valve_chamber'})
    p.add_split(vcb, vcf, smooth_angle=40)
    vl = []
    for u in (a, b):
        vl += [check_valve(f'cv{u["yn"]}', (1.95, u['yn'], -0.6), 0.055), gate_valve(f'gv{u["yn"]}', (2.3, u['yn'], -0.6), 0.055)]
    hdr = hollow_pipe('header', [(2.45, a['yn'], -0.6), (2.55, a['yn'], -0.6), (2.55, b['yn'], -0.6), (2.55, b['yn'], -0.6)], 0.06, 'paint_grey', 32)
    rm = hollow_pipe('rising_main', [(2.55, (a['yn'] + b['yn']) / 2, -0.6), (3.4, (a['yn'] + b['yn']) / 2, -0.6)], 0.075, 'paint_grey', 32)
    lines = [pipe(f'vl{i}', [(1.75, u['yn'], -0.6), (2.55, u['yn'], -0.6)], 0.055, 'paint_grey', 24) for i, u in enumerate((a, b))]
    p = m.part('station_valves', 'Non-Return & Gate Valves, Header and Rising Main', 'valves', explode=(0.6, 0, 0.6), info={'ref': 'check_valve'})
    p.add(join('station_valves', vl + [hdr, rm] + lines), smooth_angle=40)
    # level controls, vent, kiosk
    fl = []
    for i, z in enumerate((-2.3, -1.9, -1.4, -0.9)):
        fl.append(sweep_tube(f'fc{i}', [(0.75, -0.7 + 0.08 * i, 0.25), (0.75, -0.7 + 0.08 * i, z + 0.15), (0.8, -0.7 + 0.08 * i, z)], 0.005, 'rubber', 8))
        fl.append(lathe(f'fb{i}', [(0, -0.05), (0.035, -0.04), (0.04, 0.0), (0.03, 0.05), (0, 0.06)], 'paint_red' if i == 3 else 'paint_yellow', 24, center=(0.82, -0.7 + 0.08 * i, z - 0.03)))
    p = m.part('float_switches', 'Float Switches (Stop / Duty Start / Standby Start / High Alarm)', 'controls', explode=(0.3, -0.4, 0.3), info={'ref': 'level_sensor'})
    p.add(join('floats', fl), smooth_angle=60)
    kiosk = join('kiosk', [box('ks', (0.6, 0.35, 1.3), (-0.2, -RW - 1.0, 0.65 + 0.25), 'paint_green', bevel=0.02), box('kb', (0.7, 0.45, 0.25), (-0.2, -RW - 1.0, 0.125), 'paint_grey'),
                           pipe('vent', [(-0.6, -0.8, 0.45), (-0.6, -0.8, 2.0), (-0.6, -0.65, 2.15)], 0.05, 'paint_grey', 16, bend=0.1)])
    p = m.part('control_kiosk', 'Control Kiosk (Starters, Level Controller, Telemetry) & Vent', 'controls', explode=(0, -0.5, 0.3), info={'ref': 'control_panel'})
    p.add(kiosk, smooth_angle=40)
    add_tracers(m, 'sewage_in', 'Incoming Sewage (Tracers)', [(-RW - 0.7, 0.2, -1.2), (-RW + 0.3, 0.2, -1.3), (-0.4, 0.4, -2.4), (-0.1, 0.45, ZF + 0.05)], n=12, radius=0.03, mat='flow_suction')
    add_tracers(m, 'sewage_out', 'Pumped Sewage (Tracers)', [(a['xn'], a['yn'], a['zd']), (a['xr'], a['yn'], a['zd']), (a['xr'], a['yn'], -0.6), (2.55, a['yn'], -0.6),
                                                           (2.55, (a['yn'] + b['yn']) / 2, -0.6), (3.4, (a['yn'] + b['yn']) / 2, -0.6)], n=14, radius=0.03, mat='flow_discharge')
    m.flow('flow_in', [(-RW - 0.9, 0.2, -1.2), (-RW + 0.3, 0.2, -1.3), (-0.4, 0.4, -2.4), (-0.1, 0.45, ZF + 0.05)], 'flow_suction', 0.02, 0.5)
    m.flow('flow_out', [(a['xn'], a['yn'], a['zd']), (a['xr'], a['yn'], a['zd']), (a['xr'], a['yn'], -0.6), (2.55, a['yn'], -0.6), (2.55, 0.05, -0.6), (3.5, 0.05, -0.6)],
           'flow_discharge', 0.02, 0.5)
    return m.export(out_dir)


META = {
    'summary': ('A sewage lift station collects wastewater flowing by gravity into a wet well and pumps it up through a rising '
                'main to a higher sewer or treatment plant. Submersible non-clog pumps sit on the wet-well floor on guide rails, '
                'so they can be lifted out without entering the well. Float switches (or a level transmitter) start the duty '
                'pump at a set level, start the standby pump if the level keeps rising, stop the pumps at the low level and '
                'raise a high-level alarm. Non-return and isolation valves in a separate valve chamber allow each pump to be '
                'serviced while the other keeps running.'),
    'classification': {'family': 'Package / system', 'configuration': 'Wet-well submersible lift station, duty/standby', 'application': 'Municipal and building wastewater, storm water'},
    'model_configuration': {'pumps': '2 × submersible non-clog pumps (duty/standby, alternating)', 'controls': '4 float switches: stop, duty start, standby start, high-level alarm',
                            'design_note': 'Wet-well volume is sized to limit motor starts per hour (manufacturer limit) and septic retention time.'},
    'standards': [
        {'id': 'EN 752 / EN 16932', 'title': 'Drain and sewer systems outside buildings; pumping systems', 'relevance': 'European design requirements for sewage pumping stations.', 'edition': 'to be verified'},
        {'id': 'Ten States Standards (Recommended Standards for Wastewater Facilities)', 'title': 'US design guidance', 'relevance': 'Wet-well, redundancy and alarm requirements.', 'edition': 'to be verified'},
        {'id': 'ANSI/HI 9.8', 'title': 'Pump Intake Design', 'relevance': 'Wet-well geometry and submergence for solids-bearing liquids.', 'edition': 'to be verified'},
        {'id': 'NFPA 820', 'title': 'Fire Protection in Wastewater Treatment and Collection Facilities', 'relevance': 'Hazardous-area classification of wet wells.', 'edition': 'to be verified'},
    ],
    'references': ['WEF/ASCE — Design of Municipal Wastewater Treatment Plants / Pumping stations manuals.', 'Jones G.M. et al., Pumping Station Design (Butterworth-Heinemann).'],
    'components': {
        'ss_wetwell': C('Receives and stores incoming sewage between pump cycles.', 'Precast or cast-in-situ concrete chamber with sloped benching to prevent solids settling.', 'Reinforced concrete with corrosion-resistant lining.',
                        'H₂S corrosion and gas hazards — ventilation and gas detection needed.', ['Concrete corrosion', 'Grease/rag build-up'], ['Periodic cleaning, lining inspection']),
        'ss_slab': C('Covers the well and provides access for pump lifting.', 'Concrete slab with lockable aluminium hatch and safety grid.', 'Concrete, aluminium.', 'Fall protection required.', ['Hatch corrosion'], ['Visual']),
        'ss_inlet': C('Brings incoming sewage into the well and removes large debris.', 'Inlet pipe with removable screen basket on guide rails.', 'Stainless steel basket, concrete/PVC pipe.',
                      'Basket must be emptied regularly.', ['Blockage'], ['Empty basket']),
        'ss_pump': C('Lifts sewage from the well into the rising main.', 'Submersible close-coupled motor-pump with non-clog impeller and tandem seals.', 'Cast iron, stainless shaft.',
                     'Motor cooled by surrounding liquid; duty alternates between pumps.', ['Rag clogging', 'Seal leakage', 'Overheating if run dry'], ['Current monitoring, oil checks']),
        'impeller_nonclog_s': C('Passes solids and fibrous material with minimum clogging.', 'Closed two-channel impeller with large free passage.', 'Cast iron, hardened iron.',
                                'Free passage is a key selection value.', ['Rag build-up', 'Wear'], ['Clearance']),
        'ss_riser': C('Guides the pump to its duckfoot coupling and carries discharge up to the valve chamber.', 'Duckfoot bend on the floor, twin guide rails and riser pipe.', 'Ductile iron, stainless rails.',
                      'Pump seals on duckfoot by its own weight.', ['Coupling leakage', 'Rail corrosion'], ['Visual during lifts']),
        'ss_valve_chamber': C('Dry chamber housing the valves so they can be maintained without entering the wet well.', 'Concrete chamber with access cover.', 'Concrete.', 'Drained to wet well.',
                              ['Flooding'], ['Drain check']),
        'check_valve': C('Prevents rising-main backflow into the well and reverse rotation of the pumps; gate valves isolate each pump.', 'Ball or swing non-return valves suitable for sewage; resilient-seat gate valves.',
                         'Ductile iron.', 'Non-clogging designs for raw sewage.', ['Fouling', 'Slam'], ['Exercise valves']),
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
