"""Rotating Equipment — EQ-141 … EQ-145, EQ-155 … EQ-158: compressors, blowers and vacuum equipment.
Each builder: geometry + named parts + cutaway + Explode + Operate animation + flow paths (+ teaching overlays)."""
import math
from mathutils import Matrix
from pumpforge.core import Model, lathe, cyl, box, csg, split, join, split_many, rotate, extrude_poly, hex_prism, TAU, OPERATE_FRAMES
from pumpforge.valvekit import P, flange, bolts_x, keys_loop, smooth_pulse, spring, sphere
from pumpforge.parts import add_motor_h, add_coupling, add_baseplate, add_drive_y, add_tracers, hollow_pipe, pressure_gauge
from pumpforge.recip import power_end, motion_keys, RECIP_META
from pumpforge.rotkit import (add_vanes, slotted_rotor, radial_blades, pedestal, flow_ring)
from pumpforge.shapes import twisted_extrude, lobed_profile, sweep_tube
from pumpforge.common_meta import C

CAT = '7 · Rotating Equipment – Additional Machinery'


def _model(pid, title):
    return Model(pid, title, CAT, META[pid])


def _phases(lk, sign):
    """Loop-phase intervals where the crosshead moves in direction sign (+1/-1)."""
    n = len(lk) - 1
    out, start = [], None
    for k in range(n):
        v = lk[k + 1][1][0] - lk[k][1][0]
        on = v * sign > 1e-6
        if on and start is None:
            start = k / n
        if not on and start is not None:
            out.append((start, k / n)); start = None
    if start is not None:
        out.append((start, 1.0))
    return out


def _bands(m, segs, cz, r_in, r_out, title, desc, axis='X', center=None):
    rings = []
    for i, (a, b, lev) in enumerate(segs):
        if axis == 'X':
            rings.append(cyl(f'pb{i}', r_out, a, b, f'pressure_{lev}', 48, axis='X', center=(0, 0, cz), r_in=r_in))
        else:
            rings.append(cyl(f'pb{i}', r_out, a, b, f'pressure_{lev}', 48, axis='Z', center=center or (0, 0, 0), r_in=r_in))
    m.overlay('pressure', join('bands', rings), title, desc, split=True)


# =============================================================== EQ-141 Reciprocating compressor
def reciprocating_compressor(out):
    m = _model('reciprocating_compressor', 'Reciprocating Compressor (Horizontal, Double-Acting, Crosshead Type)')
    CZ, XC, R, L = 0.42, 0.62, 0.05, 0.28
    cyls, pe = power_end(m, (0.0,), CZ, XC, R, L, [0.0], 0.0, mat='paint_blue', revs=1.0, rod_to=None, bp=0.0)
    lk = cyls[0]['lk']
    x0c = cyls[0]['x0']
    OFF = 0.5                                       # crosshead -> piston centre
    xp0 = x0c - OFF
    # --- cylinder (water-jacketed) with valve pockets
    xh0, xh1 = -0.27, -0.05                          # bore length
    RB = 0.056
    vx = {'he': -0.235, 'ce': -0.085}
    outs = [cyl('cy', 0.105, xh0 - 0.03, xh1 + 0.03, 'cast_iron', 64, axis='X', center=(0, 0, CZ)),
            box('vp_top', (0.24, 0.12, 0.08), (-0.16, 0, CZ + 0.12), 'cast_iron', bevel=0.01),
            box('vp_bot', (0.24, 0.12, 0.08), (-0.16, 0, CZ - 0.12), 'cast_iron', bevel=0.01),
            cyl('ns', 0.05, CZ + 0.15, CZ + 0.26, 'cast_iron', 48, center=(-0.16, 0, 0)),
            cyl('nd', 0.045, CZ - 0.26, CZ - 0.15, 'cast_iron', 48, center=(-0.16, 0, 0)),
            cyl('hd1', 0.11, xh0 - 0.05, xh0 - 0.03, 'cast_iron', 64, axis='X', center=(0, 0, CZ)),
            cyl('hd2', 0.11, xh1 + 0.03, xh1 + 0.05, 'cast_iron', 64, axis='X', center=(0, 0, CZ))]
    ins = [cyl('bore', RB, xh0, xh1, 'cast_iron', 64, axis='X', center=(0, 0, CZ)),
           cyl('jk', 0.092, xh0 + 0.02, xh1 - 0.02, 'cast_iron', 64, axis='X', center=(0, 0, CZ), r_in=0.07),
           box('pl_s', (0.21, 0.09, 0.05), (-0.16, 0, CZ + 0.125), 'cast_iron'),
           box('pl_d', (0.21, 0.09, 0.05), (-0.16, 0, CZ - 0.125), 'cast_iron'),
           cyl('nsi', 0.04, CZ + 0.14, CZ + 0.27, 'cast_iron', 48, center=(-0.16, 0, 0)),
           cyl('ndi', 0.035, CZ - 0.27, CZ - 0.14, 'cast_iron', 48, center=(-0.16, 0, 0)),
           cyl('rodb', 0.02, xh1 - 0.01, xh1 + 0.06, 'cast_iron', 32, axis='X', center=(0, 0, CZ))]
    for k, x in vx.items():
        ins += [cyl(f'ps{k}', 0.022, CZ + RB - 0.01, CZ + 0.105, 'cast_iron', 32, center=(x, 0, 0)),
                cyl(f'pd{k}', 0.022, CZ - 0.105, CZ - RB + 0.01, 'cast_iron', 32, center=(x, 0, 0))]
    body = csg('rc_cyl', outs, ins, 'cast_iron')
    P(m, 'cylinder', 'Compressor Cylinder (Water-Jacketed) with Heads', 'casing', body, explode=(-0.35, 0, 0), ref='rc_cylinder')
    dp = csg('rc_dp', [box('dpb', (0.2, 0.16, 0.16), (0.07, 0, CZ), 'paint_blue', bevel=0.01)],
             [box('dpi', (0.16, 0.12, 0.12), (0.07, 0, CZ), 'paint_blue'), cyl('dpr', 0.02, -0.06, 0.2, 'paint_blue', 32, axis='X', center=(0, 0, CZ))], 'paint_blue')
    pk = cyl('pack', 0.032, -0.03, 0.02, 'ptfe', 32, axis='X', center=(0, 0, CZ), r_in=0.0165)
    P(m, 'distance_piece', 'Distance Piece & Rod Packing', 'casing', [dp, pk], explode=(0, 0, 0.3), ref='rc_distance_piece')
    pis = join('rc_pis', [cyl('pp', RB - 0.0015, xp0 - 0.03, xp0 + 0.03, 'aluminium', 64, axis='X', center=(0, 0, CZ)),
                          cyl('pr1', RB - 0.0005, xp0 - 0.018, xp0 - 0.01, 'ptfe', 64, axis='X', center=(0, 0, CZ)),
                          cyl('pr2', RB - 0.0005, xp0 + 0.01, xp0 + 0.018, 'ptfe', 64, axis='X', center=(0, 0, CZ)),
                          cyl('prod', 0.016, xp0, x0c - 0.05, 'chrome', 32, axis='X', center=(0, 0, CZ))])
    pp = P(m, 'piston', 'Piston, Rider/Piston Rings & Piston Rod', 'rotating_element', pis, explode=(-0.6, 0, -0.25), ref='rc_piston')
    for mesh in pp.meshes:
        m.keyframes(mesh, 'Operate', 'location', lk)
    # plate valves (4): suction on top, discharge below
    sel = {('he', 's'): 'suction', ('he', 'd'): 'discharge', ('ce', 's'): 'discharge', ('ce', 'd'): 'suction'}
    for (end, sd), how in sel.items():
        x = vx[end]
        z = CZ + 0.095 if sd == 's' else CZ - 0.095
        v = join(f'v{end}{sd}', [cyl(f'vs{end}{sd}', 0.03, z - 0.004, z + 0.004, 'steel', 32, center=(x, 0, 0), r_in=0.006),
                                 cyl(f'vp{end}{sd}', 0.026, z - 0.012, z - 0.008, 'steel_dark', 32, center=(x, 0, 0)),
                                 spring(f'vsp{end}{sd}', (x, 0, 0), 0.01, z - 0.006, z + 0.012, 0.0015, 3)])
        nm = f'{"Head-End" if end == "he" else "Crank-End"} {"Suction" if sd == "s" else "Discharge"} Valve'
        pv = P(m, f'valve_{end}_{sd}', nm + ' (Plate Type)', 'valves', v, explode=(0, 0, 0.3 if sd == 's' else -0.3), ref='rc_valve')
        lift = motion_keys(lk, how)
        for mesh in pv.meshes:
            m.keyframes(mesh, 'Operate', 'location', [(f, (0, 0, -0.006 * a)) for f, a in lift])
    # drive
    add_drive_y(m, pe['y1'] + 0.36, CZ, 0.0, 0.028, motor_R=0.16, motor_L=0.46, revs=1.0, x_off=XC, base=False)
    # suction / discharge pulsation bottles + piping
    pip = [hollow_pipe('sp', [(-0.16, 0, CZ + 0.26), (-0.16, 0, CZ + 0.45), (-0.7, 0, CZ + 0.45)], 0.04, 'paint_grey', 32, bend=0.06, t=0.004),
           hollow_pipe('dp', [(-0.16, 0, CZ - 0.26), (-0.16, 0, 0.08), (-0.7, 0, 0.08)], 0.035, 'paint_grey', 32, bend=0.05, t=0.004),
           cyl('sbt', 0.09, -0.62, -0.34, 'paint_grey', 48, axis='X', center=(0, 0, CZ + 0.45)),
           cyl('dbt', 0.08, -0.62, -0.34, 'paint_grey', 48, axis='X', center=(0, 0, 0.1))]
    P(m, 'pulsation_bottles', 'Suction & Discharge Pulsation Dampers (Bottles) and Piping', 'system_piping', pip, explode=(-0.3, 0.25, 0), ref='rc_bottles')
    he_s, ce_s = _phases(lk, +1), _phases(lk, -1)
    m.flow('suction_head_end', [(-0.75, 0, CZ + 0.45), (-0.16, 0, CZ + 0.45), (-0.16, 0, CZ + 0.13), (vx['he'], 0, CZ + 0.13), (vx['he'], 0, CZ), (vx['he'] + 0.03, 0, CZ)],
           'air', 0.006, 0.12, active=he_s)
    m.flow('discharge_head_end', [(vx['he'] + 0.03, 0, CZ), (vx['he'], 0, CZ - 0.02), (vx['he'], 0, CZ - 0.13), (-0.16, 0, CZ - 0.13), (-0.16, 0, 0.08), (-0.75, 0, 0.08)],
           'flow_discharge', 0.006, 0.12, active=ce_s)
    m.flow('suction_crank_end', [(-0.75, 0, CZ + 0.45), (-0.16, 0, CZ + 0.45), (-0.16, 0, CZ + 0.13), (vx['ce'], 0, CZ + 0.13), (vx['ce'], 0, CZ), (vx['ce'] - 0.02, 0, CZ)],
           'air', 0.006, 0.12, active=ce_s)
    m.flow('discharge_crank_end', [(vx['ce'] - 0.02, 0, CZ), (vx['ce'], 0, CZ - 0.02), (vx['ce'], 0, CZ - 0.13), (-0.16, 0, CZ - 0.13), (-0.16, 0, 0.08), (-0.75, 0, 0.08)],
           'flow_discharge', 0.006, 0.12, active=he_s)
    return m.export(out)


# =============================================================== EQ-142 Rotary screw compressor
def rotary_screw_compressor(out):
    m = _model('rotary_screw_compressor', 'Oil-Injected Rotary Screw Compressor Package (4/6 Lobe Rotors)')
    CZ, X0, X1 = 0.55, -0.22, 0.22
    RM, RF = 0.075, 0.07
    zm, zf = CZ + 0.063, CZ - 0.063
    # casing with two intersecting bores
    outs = [box('cs', (X1 - X0 + 0.08, 0.22, 0.34), (0, 0, CZ), 'cast_iron', bevel=0.02),
            cyl('inl', 0.07, CZ + 0.16, CZ + 0.26, 'cast_iron', 48, center=(X0 + 0.07, 0, 0)),
            cyl('dis', 0.05, CZ - 0.27, CZ - 0.16, 'cast_iron', 48, center=(X1 - 0.05, 0, 0))]
    ins = [cyl('bm', RM + 0.002, X0, X1, 'cast_iron', 96, axis='X', center=(0, 0, zm)), cyl('bf', RF + 0.002, X0, X1, 'cast_iron', 96, axis='X', center=(0, 0, zf)),
           cyl('inli', 0.058, CZ + 0.05, CZ + 0.27, 'cast_iron', 48, center=(X0 + 0.07, 0, 0)), cyl('disi', 0.04, CZ - 0.28, CZ - 0.05, 'cast_iron', 48, center=(X1 - 0.05, 0, 0)),
           cyl('shm', 0.022, X1 - 0.01, X1 + 0.06, 'cast_iron', 32, axis='X', center=(0, 0, zm))]
    P(m, 'casing', 'Rotor Casing (Inlet Port top, Discharge Port bottom)', 'casing', csg('sc_case', outs, ins, 'cast_iron'), explode=(0, 0.35, 0), ref='sc_casing')
    Lr = X1 - X0 - 0.004
    lead_m = Lr * 360 / 300
    prof_m = lobed_profile(0.045, RM, 4, n=96, land=0.55, sharp=2.6)
    prof_f = lobed_profile(0.05, RF, 6, n=120, land=0.32, sharp=3.0)
    male = join('male', [twisted_extrude('mr', prof_m, X0 + 0.002, X1 - 0.002, lead_m, 'steel', axis='X', center=(0, 0, zm), hand=1),
                         cyl('ms', 0.02, X0 - 0.06, X1 + 0.15, 'steel', 32, axis='X', center=(0, 0, zm), ch=0.002)])
    pm = P(m, 'male_rotor', 'Male Rotor (4 lobes) — driven by the motor', 'rotating_element', male, explode=(0, -0.4, 0.25), ref='sc_male', section='keep', pivot=(0, 0, zm))
    pm.spin('X', 3)
    fem = join('female', [twisted_extrude('fr', prof_f, X0 + 0.002, X1 - 0.002, lead_m * 6 / 4, 'stainless', axis='X', center=(0, 0, zf), hand=-1),
                          cyl('fs', 0.018, X0 - 0.05, X1 + 0.06, 'steel', 32, axis='X', center=(0, 0, zf), ch=0.002)])
    pf = P(m, 'female_rotor', 'Female Rotor (6 flutes)', 'rotating_element', fem, explode=(0, -0.4, -0.25), ref='sc_female', section='keep', pivot=(0, 0, zf))
    pf.spin('X', -2)
    brg = [cyl(f'b{i}', 0.04, x - 0.02, x + 0.02, 'steel', 32, axis='X', center=(0, 0, z), r_in=0.02) for i, (x, z) in
           enumerate(((X0 - 0.04, zm), (X0 - 0.04, zf), (X1 + 0.03, zm), (X1 + 0.03, zf)))]
    P(m, 'bearings', 'Rotor Bearings (radial rollers + discharge-end thrust bearings)', 'bearings', brg, explode=(0, -0.2, 0.45), ref='sc_bearings')
    add_coupling(m, 'coupling', X1 + 0.08, X1 + 0.17, zm, 0.05, 0.02, explode=(0.3, 0, 0), revs=3, foot_z=0.08)
    add_motor_h(m, 'm_', X1 + 0.19, zm, 0.15, 0.45, 0.08, 0.02, 0.05, explode_dx=0.6, revs=3)
    # inlet valve + filter
    iv = join('inv', [cyl('ivb', 0.075, CZ + 0.26, CZ + 0.34, 'aluminium', 48, center=(X0 + 0.07, 0, 0)),
                      cyl('ivf', 0.11, CZ + 0.34, CZ + 0.52, 'paint_grey', 48, center=(X0 + 0.07, 0, 0), ch=0.006)])
    P(m, 'inlet_valve_filter', 'Air Filter & Inlet (Suction-Throttle) Valve', 'valves', iv, explode=(0, 0, 0.4), ref='sc_inlet')
    # oil separator vessel + piping
    SX = -0.62
    sep = csg('sep', [cyl('sv', 0.16, 0.08, 0.9, 'paint_orange', 64, center=(SX, 0.0, 0)), sphere('sd', (SX, 0, 0.9), 0.16, 'paint_orange', 32)],
              [cyl('svi', 0.15, 0.09, 0.92, 'paint_orange', 64, center=(SX, 0, 0))], 'paint_orange')
    el = cyl('elem', 0.09, 0.62, 0.92, 'polypropylene', 48, center=(SX, 0, 0), r_in=0.05)
    oil = cyl('oil', 0.149, 0.09, 0.3, 'hydraulic_oil', 64, center=(SX, 0, 0))
    P(m, 'oil_separator', 'Oil Separator Vessel, Separator Element & Oil Sump', 'vessel', [sep, el, oil], explode=(0.4, 0, 0), ref='sc_separator')
    pip = [hollow_pipe('dl', [(X1 - 0.05, 0, CZ - 0.27), (X1 - 0.05, 0, 0.2), (SX + 0.16, 0, 0.2)], 0.035, 'steel', 24, bend=0.05, t=0.004),
           hollow_pipe('ol', [(SX + 0.16, 0, 0.13), (0.0, 0, 0.13), (0.0, 0, CZ - 0.17)], 0.014, 'copper', 16, bend=0.03, t=0.003),
           hollow_pipe('al', [(SX, 0, 1.06), (SX, 0, 1.15), (SX - 0.35, 0, 1.15)], 0.03, 'steel', 24, bend=0.04, t=0.004)]
    P(m, 'piping', 'Discharge Line, Oil Injection Line & Service Air Outlet', 'system_piping', pip, explode=(0.3, 0.3, 0), ref='sc_piping')
    add_baseplate(m, -0.85, 0.85, 0.5, 0.08)
    m.flow('air', [(X0 + 0.07, 0, CZ + 0.55), (X0 + 0.07, 0, CZ + 0.1), (X0 + 0.1, 0, CZ), (X1 - 0.08, 0, CZ), (X1 - 0.05, 0, CZ - 0.1), (X1 - 0.05, 0, 0.2),
                   (SX + 0.1, 0, 0.2), (SX, 0, 0.45), (SX, 0, 0.75), (SX, 0, 1.15), (SX - 0.38, 0, 1.15)], 'air', 0.009, 0.2,
           speed=[1, 1.2, 1.2, 0.8, 1.6, 1.8, 1.4, 0.7, 0.6, 1.5, 1.5])
    m.flow('oil_injection', [(SX + 0.1, 0, 0.13), (0.0, 0, 0.13), (0.0, 0, CZ - 0.12), (0.03, 0, CZ - 0.06)], 'hydraulic_oil', 0.006, 0.15)
    _bands(m, [(X0, X0 + 0.11, 1), (X0 + 0.11, X0 + 0.2, 2), (X0 + 0.2, X0 + 0.28, 4), (X0 + 0.28, X0 + 0.36, 6), (X0 + 0.36, X1, 9)], CZ, 0.175, 0.19,
           'Pressure along the rotors', 'Air trapped between the lobes is carried from the inlet end toward the discharge end; the pocket shrinks and the pressure '
           'rises until the pocket reaches the discharge port (built-in volume ratio).')
    m.annotate('pressure', 'Inlet: atmospheric', (X0 + 0.03, 0, CZ + 0.24))
    m.annotate('pressure', 'Discharge: e.g. 7–8 bar(g)', (X1, 0, CZ - 0.24))
    return m.export(out)


# =============================================================== EQ-143 Rotary vane compressor
def _vane_machine(m, pfx, CZ, Rs, Rr, e, W, NV, lv, tv, mats, ref_stator, ref_rotor, ref_vane, label):
    czr = CZ - e
    st = csg(pfx + 'st', [cyl('so', Rs + 0.04, 0.0, W, mats, 96, axis='Y', center=(0, 0, CZ))],
             [cyl('si', Rs, -0.01, W + 0.01, mats, 128, axis='Y', center=(0, 0, CZ)),
              box('pin', (0.06, W - 0.03, 0.09), (-Rs - 0.01, W / 2, CZ + 0.04), mats), box('pout', (0.06, W - 0.03, 0.06), (Rs + 0.01, W / 2, CZ - 0.07), mats)], mats)
    P(m, 'stator', f'{label} Stator (Cylinder) with Ports', 'casing', st, explode=(0, -0.15, 0), ref=ref_stator, section='keep')
    rot = slotted_rotor(pfx + 'rot', Rr, W, NV, lv, tv, czr, shaft_r=0.022, y_sh0=-0.06, y_sh1=W + 0.35)
    pr = P(m, 'rotor', 'Slotted Rotor & Shaft (eccentric)', 'rotating_element', rot, explode=(0, -0.35, 0), ref=ref_rotor, section='keep', pivot=(0, 0, czr))
    pr.spin('Y', 1)
    add_vanes(m, 'vane_', NV, Rr, Rs, e, W, CZ, lv, tv, mat='carbon', revs=1.0, explode=(0, -0.45, 0.2), ref=ref_vane)
    fh = join('fh', [cyl('fhd', Rs + 0.06, -0.045, 0.0, mats, 96, axis='Y', center=(0, 0, CZ)),
                     cyl('fhb', 0.05, -0.09, -0.045, mats, 48, axis='Y', center=(0, 0, czr))])
    P(m, 'front_head', 'Front End Cover (hidden in cutaway)', 'casing', fh, explode=(0, -0.6, 0), ref=ref_stator, section='hide')
    rh = csg('rh', [cyl('rhd', Rs + 0.06, W, W + 0.03, mats, 96, axis='Y', center=(0, 0, CZ)), cyl('rhb', 0.05, W + 0.03, W + 0.1, mats, 48, axis='Y', center=(0, 0, czr))],
             [cyl('rhs', 0.024, W - 0.01, W + 0.11, mats, 32, axis='Y', center=(0, 0, czr))], mats)
    P(m, 'rear_head', 'Rear End Cover & Bearing Housing', 'casing', rh, explode=(0, 0.3, 0), ref=ref_stator, section='keep')
    return czr


def rotary_vane_compressor(out):
    m = _model('rotary_vane_compressor', 'Oil-Flooded Rotary Vane Compressor (8 Vanes)')
    CZ, Rs, Rr, e, W = 0.42, 0.13, 0.105, 0.022, 0.26
    czr = _vane_machine(m, 'vc', CZ, Rs, Rr, e, W, 8, 0.05, 0.006, 'cast_iron', 'vc_stator', 'vc_rotor', 'vc_vane', 'Compressor')
    ft = box('ft', (0.3, W + 0.1, CZ - Rs - 0.04 - 0.12), (0, W / 2, 0.12 + (CZ - Rs - 0.04 - 0.12) / 2), 'cast_iron', bevel=0.006)
    P(m, 'support', 'Stator Support Foot', 'baseplate', ft, explode=(0, 0, -0.2), ref='vc_stator', section='keep')
    noz = [hollow_pipe('ni', [(-Rs - 0.25, W / 2, CZ + 0.04), (-Rs - 0.03, W / 2, CZ + 0.04)], 0.035, 'paint_grey', 24, t=0.004),
           hollow_pipe('no', [(Rs + 0.03, W / 2, CZ - 0.07), (Rs + 0.2, W / 2, CZ - 0.07), (Rs + 0.2, W / 2, CZ + 0.35)], 0.03, 'paint_grey', 24, bend=0.04, t=0.004),
           cyl('flt', 0.08, -Rs - 0.4, -Rs - 0.22, 'paint_grey', 48, axis='X', center=(0, W / 2, CZ + 0.04))]
    P(m, 'nozzles', 'Inlet Filter & Inlet / Discharge Connections', 'system_piping', noz, explode=(0, 0.3, 0.2), ref='vc_piping')
    sep = cyl('sep', 0.12, CZ + 0.22, CZ + 0.62, 'paint_orange', 48, center=(Rs + 0.2, W / 2 + 0.0, 0), ch=0.01)
    P(m, 'oil_separator', 'Air/Oil Separator Receiver', 'vessel', sep, explode=(0.35, 0, 0.2), ref='vc_separator', section='keep')
    add_drive_y(m, W + 0.12, czr, 0.12, 0.022, motor_R=0.13, motor_L=0.36, y_base0=-0.2, revs=1.0, base_w=0.6)
    m.flow('air', [(-Rs - 0.42, W / 2, CZ + 0.04), (-Rs + 0.01, W / 2, CZ + 0.04)] + flow_ring(0, CZ, Rs - 0.015, math.radians(165), math.radians(-40), 18, y=W / 2) +
           [(Rs + 0.03, W / 2, CZ - 0.07), (Rs + 0.2, W / 2, CZ - 0.07), (Rs + 0.2, W / 2, CZ + 0.62)], 'air', 0.007, 0.12,
           speed=[1, 1] + [0.8] * 10 + [1.4] * 9 + [1.6, 1.6, 1.6])
    return m.export(out)


# =============================================================== EQ-144 Roots blower
def roots_blower(out):
    m = _model('roots_blower', 'Roots (Rotary Lobe) Blower — Tri-Lobe, Timing Gears')
    CZ, W = 0.5, 0.3
    RT, RR, A = 0.1, 0.045, 0.148
    cx = (-A / 2, A / 2)
    rt = RT + 0.002
    outs = [box('bc', (2 * A + 0.06, W, 2 * rt + 0.06), (0, W / 2, CZ), 'cast_iron', bevel=0.01),
            box('fi', (0.2, W - 0.04, 0.1), (0, W / 2, CZ + rt + 0.06), 'cast_iron', bevel=0.006),
            box('fo', (0.2, W - 0.04, 0.1), (0, W / 2, CZ - rt - 0.06), 'cast_iron', bevel=0.006)]
    ins = [cyl(f'b{i}', rt, -0.01, W + 0.01, 'cast_iron', 128, axis='Y', center=(c, 0, CZ)) for i, c in enumerate(cx)]
    ins += [box('mid', (0.06, W + 0.02, 2 * rt - 0.04), (0, W / 2, CZ), 'cast_iron'),
            box('pi', (0.17, W - 0.07, 0.2), (0, W / 2, CZ + rt + 0.02), 'cast_iron'), box('po', (0.17, W - 0.07, 0.2), (0, W / 2, CZ - rt - 0.02), 'cast_iron')]
    P(m, 'casing', 'Blower Casing (Rotor Housing)', 'casing', csg('rb_case', outs, ins, 'cast_iron'), explode=(0, 0.0, 0), ref='rb_casing', section='keep')
    fc = box('fc', (2 * A + 0.08, 0.03, 2 * rt + 0.08), (0, -0.015, CZ), 'cast_iron', bevel=0.008)
    P(m, 'end_plate', 'Drive-Side End Plate (hidden in cutaway)', 'casing', fc, explode=(0, -0.5, 0), ref='rb_casing', section='hide')
    for i, (c, sg, nm) in enumerate(((cx[0], -1, 'Drive'), (cx[1], 1, 'Driven'))):
        prof = lobed_profile(RR, RT, 3, n=120, land=0.5, sharp=1.6)
        lob = extrude_poly(f'lob{i}', [(x + c, z + CZ) for x, z in prof], 0.002, W - 0.002, 'paint_blue_dark', plane='XZ')
        sh = cyl(f'rs{i}', 0.02, -0.08 - (0.25 if i == 0 else 0), W + 0.2, 'steel', 32, axis='Y', center=(c, 0, CZ), ch=0.002)
        p = P(m, f'rotor_{i + 1}', f'{nm} Rotor (tri-lobe) & Shaft', 'rotating_element', [lob, sh], explode=(c * 3, -0.35, 0), ref='rb_rotor', section='keep', pivot=(c, 0, CZ))
        p.spin('Y', 2 * sg)
    gb = csg('gb', [box('gbo', (2 * A + 0.1, 0.12, 0.22), (0, W + 0.1, CZ), 'paint_grey', bevel=0.01)], [box('gbi', (2 * A + 0.07, 0.09, 0.19), (0, W + 0.1, CZ), 'paint_grey')], 'paint_grey')
    P(m, 'gearbox', 'Timing Gear Case & Oil Sump', 'gearbox', gb, explode=(0, 0.4, 0), ref='rb_gears', section='keep')
    from pumpforge.rotkit import helical_gear
    for i, (c, sg) in enumerate(((cx[0], -1), (cx[1], 1))):
        g, _ = helical_gear(f'tg{i}', A / 30, 30, W + 0.07, W + 0.12, 'steel', cx=c, cz=CZ, helix_deg=0, phase=(math.pi / 30 if i else 0))
        p = P(m, f'timing_gear_{i + 1}', f'Timing Gear {i + 1}', 'gearbox', g, explode=(c * 2, 0.55, 0), ref='rb_gears', section='keep', pivot=(c, 0, CZ))
        p.spin('Y', 2 * sg)
    sil = [cyl('is', 0.13, CZ + rt + 0.11, CZ + rt + 0.5, 'paint_grey', 48, center=(0, W / 2, 0), ch=0.01),
           hollow_pipe('ds', [(0, W / 2, CZ - rt - 0.11), (0, W / 2, 0.22), (0.6, W / 2, 0.22)], 0.07, 'paint_grey', 32, bend=0.08, t=0.005),
           cyl('dsl', 0.13, 0.25, 0.6, 'paint_grey', 48, axis='X', center=(0, W / 2, 0.22))]
    P(m, 'silencers', 'Inlet Filter-Silencer & Discharge Silencer', 'system_piping', sil, explode=(0.4, 0, 0.3), ref='rb_silencers')
    mo = join('pul', [cyl('pu', 0.1, -0.33, -0.25, 'cast_iron', 48, axis='Y', center=(cx[0], 0, CZ))])
    pp = P(m, 'pulley', 'Drive Pulley (belt drive from motor)', 'power_transmission', mo, explode=(0, -0.7, 0), ref='rb_pulley', section='hide', pivot=(cx[0], 0, CZ))
    legs = [box(f'lg{i}', (0.06, W, CZ - rt - 0.03 - 0.1), (sx * (A + 0.0), W / 2, 0.1 + (CZ - rt - 0.03 - 0.1) / 2), 'cast_iron', bevel=0.005) for i, sx in enumerate((-1, 1))]
    P(m, 'feet', 'Casing Feet', 'baseplate', legs, explode=(0, 0, -0.2), ref='rb_casing', section='keep')
    pp.spin('Y', -2)
    add_baseplate(m, -0.4, 0.75, 0.6, 0.1)
    for side, c in ((0, cx[0]), (1, cx[1])):
        a0, a1 = (math.radians(100), math.radians(260)) if side == 0 else (math.radians(80), math.radians(-80))
        m.flow(f'pocket_{side + 1}', [(0, W / 2, CZ + rt + 0.48), (c * 0.6, W / 2, CZ + rt + 0.02)] +
               flow_ring(c, CZ, RT - 0.012, a0, a1, 14, y=W / 2) + [(0, W / 2, CZ - rt - 0.05), (0, W / 2, 0.22), (0.62, W / 2, 0.22)], 'air', 0.008, 0.15)
    return m.export(out)


# =============================================================== EQ-145 Side channel blower
def side_channel_blower(out):
    m = _model('side_channel_blower', 'Side Channel (Regenerative) Blower — Single Stage')
    CZ, XA, XB = 0.36, -0.05, 0.05
    RO, RC, rch = 0.2, 0.13, 0.026
    hub = cyl('hb', 0.07, XA + 0.005, XB - 0.005, 'aluminium', 64, axis='X', center=(0, 0, CZ))
    disc = cyl('dk', RC - rch, XA + 0.035, XA + 0.045, 'aluminium', 96, axis='X', center=(0, 0, CZ))

    def bl(i):
        return box(f'bl{i}', (0.032, 0.0035, 2 * rch), (XA + 0.02, 0, CZ + RC), 'aluminium')
    from pumpforge.rotkit import ring_of
    blades = ring_of('blades', 40, bl, cz=CZ)
    ring = cyl('rg', RC + rch + 0.002, XA + 0.005, XA + 0.04, 'aluminium', 96, axis='X', center=(0, 0, CZ), r_in=RC + rch - 0.002)
    imp = P(m, 'impeller', 'Impeller (40 radial blades)', 'rotating_element', [hub, disc, blades, ring], explode=(-0.4, 0, 0), ref='scb_impeller', pivot=(0, 0, CZ))
    imp.spin('X', 4)
    chan = lathe('chan', [(RC - rch, XA - 0.04), (RC + rch, XA - 0.04), (RC + rch, XA + 0.05), (RC - rch, XA + 0.05)], 'aluminium', 96, axis='X', center=(0, 0, CZ))
    hs_o = [cyl('ho', RO, XA - 0.06, XB + 0.01, 'aluminium', 96, axis='X', center=(0, 0, CZ)),
            box('pt', (0.12, 0.3, 0.1), (XA - 0.01, 0, CZ + RO + 0.02), 'aluminium', bevel=0.01)]
    hs_i = [chan, cyl('hc', RC - rch + 0.004, XA - 0.0, XB + 0.02, 'aluminium', 64, axis='X', center=(0, 0, CZ)),
            cyl('pi', 0.028, CZ + RC - 0.01, CZ + RO + 0.08, 'aluminium', 32, center=(XA - 0.02, -0.08, 0)),
            cyl('po', 0.028, CZ + RC - 0.01, CZ + RO + 0.08, 'aluminium', 32, center=(XA - 0.02, 0.08, 0))]
    hs_o2 = [box('fin%d' % i, (0.004, 2 * RO - 0.02, 0.02), (XA - 0.05 + 0.02 * i, 0, CZ - RO + 0.02), 'aluminium') for i in range(5)]
    P(m, 'housing', 'Housing with Side Channel, Ports & Interrupter', 'casing', [csg('hs', hs_o, hs_i, 'aluminium')] + hs_o2, explode=(-0.6, 0, 0), ref='scb_housing')
    cov = csg('cv', [cyl('cvo', RO, XB + 0.01, XB + 0.04, 'aluminium', 96, axis='X', center=(0, 0, CZ))], [cyl('cvi', 0.03, XB, XB + 0.05, 'aluminium', 32, axis='X', center=(0, 0, CZ))], 'aluminium')
    P(m, 'motor_flange', 'Motor-Side Cover / Flange', 'casing', cov, explode=(0.2, 0, 0), ref='scb_housing')
    sil = [cyl(f'sl{s}', 0.045, CZ + RO + 0.07, CZ + RO + 0.3, 'paint_grey', 32, center=(XA - 0.02, s * 0.08, 0), ch=0.004) for s in (-1, 1)]
    P(m, 'silencers', 'Inlet & Outlet Silencers', 'system_piping', sil, explode=(0, 0, 0.3), ref='scb_silencers', section='keep')
    add_motor_h(m, 'm_', XB + 0.06, CZ, 0.14, 0.34, 0.08, 0.02, 0.15, explode_dx=0.5, revs=4)
    feet = box('ft', (0.3, 0.32, 0.03), (0.02, 0, 0.095), 'paint_grey', bevel=0.004)
    P(m, 'feet', 'Foot Bracket', 'baseplate', feet, explode=(0, 0, -0.2), ref='baseplate', section='keep')
    path = [(XA - 0.02, -0.08, CZ + RO + 0.3), (XA - 0.02, -0.08, CZ + RC + 0.01)]
    n = 220
    for k in range(n + 1):
        th = math.radians(128) + math.radians(284) * k / n
        ph = TAU * 19 * k / n
        rr = RC + 0.012 * math.cos(ph)
        xx = XA + 0.005 - 0.022 * math.sin(ph) - 0.008
        path.append((xx, rr * math.cos(th), CZ + rr * math.sin(th)))
    path += [(XA - 0.02, 0.08, CZ + RC + 0.01), (XA - 0.02, 0.08, CZ + RO + 0.3)]
    m.flow('helical_flow', path, 'air', 0.004, 0.06)
    return m.export(out)


# =============================================================== EQ-155 Rotary (oil-sealed vane) vacuum pump
def rotary_vacuum_pump(out):
    m = _model('rotary_vacuum_pump', 'Oil-Sealed Rotary Vane Vacuum Pump')
    CZ, Rs, Rr, e, W = 0.32, 0.075, 0.06, 0.013, 0.16
    czr = _vane_machine(m, 'vp', CZ, Rs, Rr, e, W, 3, 0.04, 0.005, 'cast_iron', 'rv_stator', 'rv_rotor', 'rv_vane', 'Pump')
    ob = csg('ob', [box('obo', (0.42, W + 0.06, 0.34), (0.02, W / 2, CZ + 0.03), 'paint_green', bevel=0.012)],
             [box('obi', (0.39, W + 0.03, 0.31), (0.02, W / 2, CZ + 0.03), 'paint_green')], 'paint_green')
    b, f = split(ob, 'y', W / 2)
    oil = csg('oil', [box('oilb', (0.385, W + 0.025, 0.13), (0.02, W / 2, CZ - 0.07), 'hydraulic_oil')], [cyl('oc', Rs + 0.041, -0.1, W + 0.1, 'hydraulic_oil', 64, axis='Y', center=(0, 0, CZ))], 'hydraulic_oil')
    ob_, of_ = split(oil, 'y', W / 2)
    pob = m.part('oil_casing', 'Oil Casing (Oil Box) with Oil Charge', 'casing', section='split', explode=(0, 0, -0.25), info={'ref': 'rv_oilbox'})
    pob.add_split(join('obk', [b, ob_]), join('obf', [f, of_]), smooth_angle=40)
    ev = box('evf', (0.006, W - 0.04, 0.07), (Rs + 0.045, W / 2, CZ - 0.07), 'rubber')
    pev = P(m, 'exhaust_valve', 'Exhaust Valve (flap) — opens when gas is compressed above atmospheric', 'valves', ev, explode=(0.3, 0, 0), ref='rv_exhaust_valve', section='keep')
    keys_loop(m, pev, lambda t: (0.008 * smooth_pulse((t * 3) % 1.0, 0.1, 0.15, 0.1), 0, 0))
    con = [hollow_pipe('in', [(-Rs - 0.03, W / 2, CZ + 0.04), (-0.14, W / 2, CZ + 0.04), (-0.14, W / 2, CZ + 0.32)], 0.025, 'stainless', 24, bend=0.03, t=0.003),
           cyl('if', 0.045, CZ + 0.3, CZ + 0.32, 'stainless', 48, center=(-0.14, W / 2, 0)),
           cyl('xf', 0.06, CZ + 0.19, CZ + 0.36, 'paint_grey', 48, center=(0.14, W / 2, 0), ch=0.005),
           join('gb', [cyl('gbv', 0.015, CZ + 0.19, CZ + 0.24, 'brass', 16, center=(0.02, W / 2, 0)), cyl('gbk', 0.022, CZ + 0.24, CZ + 0.25, 'paint_red', 24, center=(0.02, W / 2, 0))])]
    P(m, 'connections', 'Inlet (vacuum) Flange, Gas-Ballast Valve & Exhaust Demister', 'system_piping', con, explode=(0, 0, 0.35), ref='rv_connections', section='keep')
    sg = cyl('sg', 0.03, -0.004, 0.006, 'glass', 32, axis='Y', center=(0.15, 0, CZ - 0.07))
    P(m, 'sight_glass', 'Oil-Level Sight Glass', 'instrument', sg, explode=(0, -0.2, 0), ref='rv_sightglass', section='keep')
    add_drive_y(m, W + 0.12, czr, 0.1, 0.02, motor_R=0.1, motor_L=0.28, y_base0=-0.08, revs=1.0, base_w=0.5)
    m.flow('gas', [(-0.14, W / 2, CZ + 0.33), (-0.14, W / 2, CZ + 0.04), (-Rs + 0.01, W / 2, CZ + 0.04)] +
           flow_ring(0, CZ, Rs - 0.01, math.radians(165), math.radians(-25), 14, y=W / 2) +
           [(Rs + 0.05, W / 2, CZ - 0.03), (0.14, W / 2, CZ + 0.1), (0.14, W / 2, CZ + 0.38)], 'air', 0.005, 0.08)
    return m.export(out)


# =============================================================== EQ-156 Liquid ring vacuum pump
def liquid_ring_vacuum_pump(out):
    m = _model('liquid_ring_vacuum_pump', 'Liquid Ring Vacuum Pump (Single Stage, Port Plate)')
    CZ, Rc, e, W = 0.42, 0.17, 0.035, 0.18
    czi = CZ + e
    st = csg('lr', [cyl('o', Rc + 0.025, 0, W, 'cast_iron', 96, axis='Y', center=(0, 0, CZ)),
                    box('ft', (0.3, W, 0.1), (0, W / 2, CZ - Rc - 0.03), 'cast_iron', bevel=0.006)],
             [cyl('i', Rc, -0.01, W + 0.01, 'cast_iron', 128, axis='Y', center=(0, 0, CZ))], 'cast_iron')
    P(m, 'casing', 'Casing (eccentric to impeller)', 'casing', st, explode=(0, 0, -0.2), ref='lr_casing', section='keep')
    wr = csg('ring', [cyl('wo', Rc - 0.002, 0.004, W - 0.004, 'water', 128, axis='Y', center=(0, 0, CZ))],
             [cyl('wi', Rc - 0.06, -0.01, W + 0.01, 'water', 128, axis='Y', center=(0, 0, CZ))], 'water')
    P(m, 'liquid_ring', 'Liquid Ring (service liquid thrown out by the impeller)', 'fluid', wr, explode=(0, -0.25, 0.0), ref='lr_ring', section='keep')
    hub = cyl('hub', 0.05, 0.003, W - 0.003, 'stainless', 64, axis='Y', center=(0, 0, czi))
    bl = radial_blades('bl', 0.003, W - 0.003, 0.048, Rc - e - 0.012, 12, 'stainless', curve=-0.5, t=0.005, cx=0, cz=czi)
    shr = cyl('shr', Rc - e - 0.01, W - 0.012, W - 0.003, 'stainless', 96, axis='Y', center=(0, 0, czi), r_in=0.05)
    sh = cyl('sh', 0.024, -0.05, W + 0.42, 'steel', 32, axis='Y', center=(0, 0, czi), ch=0.002)
    pi = P(m, 'impeller', 'Impeller (12 forward-curved blades) & Shaft — eccentric', 'rotating_element', [hub, bl, shr, sh], explode=(0, -0.5, 0), ref='lr_impeller',
           section='keep', pivot=(0, 0, czi))
    pi.spin('Y', 2)
    XS, ZS, XD, ZD = 0.075, czi - 0.025, -0.07, czi + 0.04
    ppl = csg('pp', [cyl('ppd', Rc + 0.025, W, W + 0.025, 'cast_iron', 96, axis='Y', center=(0, 0, CZ))],
              [cyl('spp', 0.032, W - 0.01, W + 0.03, 'cast_iron', 40, axis='Y', center=(XS, 0, ZS)),
               cyl('dpp', 0.024, W - 0.01, W + 0.03, 'cast_iron', 32, axis='Y', center=(XD, 0, ZD)),
               cyl('shh', 0.026, W - 0.01, W + 0.03, 'cast_iron', 32, axis='Y', center=(0, 0, czi))], 'cast_iron')
    P(m, 'port_plate', 'Port Plate (suction & discharge ports) & Head', 'casing', ppl, explode=(0, 0.3, 0), ref='lr_port_plate', section='keep')
    fh = cyl('fh', Rc + 0.025, -0.025, 0.0, 'cast_iron', 96, axis='Y', center=(0, 0, CZ))
    P(m, 'front_head', 'Front Head (hidden in cutaway)', 'casing', fh, explode=(0, -0.7, 0), ref='lr_port_plate', section='hide')
    con = [hollow_pipe('sn', [(XS, W + 0.06, ZS), (XS, W + 0.06, CZ + 0.42)], 0.03, 'paint_grey', 24, t=0.004),
           hollow_pipe('dn', [(XD, W + 0.06, ZD), (XD, W + 0.06, CZ + 0.3), (-0.45, W + 0.06, CZ + 0.3)], 0.024, 'paint_grey', 24, bend=0.04, t=0.004),
           box('hd', (0.32, 0.08, 0.2), (0.0, W + 0.065, czi), 'cast_iron', bevel=0.01)]
    P(m, 'connections', 'Suction & Discharge Nozzles (via head)', 'system_piping', con, explode=(0, 0.45, 0.2), ref='lr_connections', section='keep')
    sep = cyl('sep', 0.14, 0.1, 0.75, 'paint_blue', 48, center=(-0.6, W + 0.06, 0), ch=0.01)
    sw = hollow_pipe('sw', [(-0.6, W + 0.06, 0.12), (-0.6, W + 0.06, 0.05), (0.0, W + 0.06, 0.05), (0.0, W / 2, CZ - Rc - 0.03)], 0.012, 'copper', 16, bend=0.02, t=0.003)
    P(m, 'separator', 'Discharge Separator & Service-Liquid Return', 'vessel', [sep, sw], explode=(-0.35, 0, 0), ref='lr_separator', section='keep')
    add_drive_y(m, W + 0.42 - 0.02, czi, 0.12, 0.024, motor_R=0.14, motor_L=0.38, y_base0=-0.1, revs=2, base_w=0.7)
    m.flow('gas', [(XS, W + 0.06, CZ + 0.42), (XS, W + 0.06, ZS), (XS, W / 2, ZS)] + flow_ring(0, czi, 0.085, math.radians(-20), math.radians(-210), 16, y=W / 2) +
           [(XD, W / 2, ZD), (XD, W + 0.06, ZD), (XD, W + 0.06, CZ + 0.3), (-0.6, W + 0.06, CZ + 0.3), (-0.6, W + 0.06, 0.78)], 'air', 0.006, 0.1)
    m.flow('service_liquid', [(-0.6, W + 0.06, 0.12), (-0.6, W + 0.06, 0.05), (0.0, W + 0.06, 0.05), (0.0, W / 2, CZ - Rc + 0.02)], 'water', 0.005, 0.12)
    return m.export(out)


# =============================================================== EQ-157 Dry screw vacuum pump
def dry_screw_vacuum_pump(out):
    m = _model('dry_screw_vacuum_pump', 'Dry Screw Vacuum Pump (Variable-Pitch Screws, Timing Gears)')
    CZ, X0, X1 = 0.45, -0.3, 0.3
    RO, RI = 0.07, 0.028
    zs = (CZ + 0.05, CZ - 0.05)
    outs = [box('c', (X1 - X0 + 0.04, 0.2, 0.3), (0, 0, CZ), 'cast_iron', bevel=0.02),
            cyl('in', 0.06, CZ + 0.14, CZ + 0.24, 'cast_iron', 48, center=(X0 + 0.07, 0, 0)), cyl('ou', 0.035, CZ - 0.24, CZ - 0.14, 'cast_iron', 32, center=(X1 - 0.04, 0, 0))]
    ins = [cyl(f'b{i}', RO + 0.0015, X0, X1, 'cast_iron', 96, axis='X', center=(0, 0, z)) for i, z in enumerate(zs)]
    ins += [cyl('ini', 0.05, CZ + 0.05, CZ + 0.25, 'cast_iron', 48, center=(X0 + 0.07, 0, 0)), cyl('oui', 0.025, CZ - 0.25, CZ - 0.05, 'cast_iron', 32, center=(X1 - 0.04, 0, 0)),
            cyl('wj', 0.14, X0 + 0.02, X1 - 0.02, 'cast_iron', 64, axis='X', center=(0, 0, CZ), r_in=0.125)]
    P(m, 'casing', 'Stator Casing (water-cooled) — Inlet top, Exhaust bottom', 'casing', csg('ds_case', outs, ins, 'cast_iron'), explode=(0, 0.35, 0), ref='ds_casing')
    prof = lobed_profile(RI, RO, 1, n=64, land=0.5, sharp=3.5)
    segs = [(X0 + 0.002, X0 + 0.22, 0.16), (X0 + 0.22, X0 + 0.42, 0.09), (X0 + 0.42, X1 - 0.002, 0.05)]
    for i, (z, hand) in enumerate(((zs[0], 1), (zs[1], -1))):
        pieces, acc = [], 0.0
        for k, (a, b, lead) in enumerate(segs):
            c, s = math.cos(acc), math.sin(acc)
            pr = [(u * c - v * s, u * s + v * c) for u, v in prof]
            if i == 1:
                pr = [(u, -v) for u, v in pr]
            pieces.append(twisted_extrude(f's{i}{k}', pr, a, b, lead, 'stainless' if i == 0 else 'steel', steps=max(10, int((b - a) / lead * 20)), axis='X', center=(0, 0, z), hand=hand))
            acc += TAU * (b - a) / lead
        pieces.append(cyl(f'sh{i}', 0.018, X0 - 0.06, X1 + 0.2 + (0.25 if i == 0 else 0), 'steel', 32, axis='X', center=(0, 0, z), ch=0.002))
        p = P(m, f'screw_{i + 1}', f'{"Drive" if i == 0 else "Driven"} Screw Rotor (pitch decreases toward exhaust)', 'rotating_element', pieces,
              explode=(0, -0.4, 0.25 if i == 0 else -0.25), ref='ds_screw', section='keep', pivot=(0, 0, z))
        p.spin('X', 3 if i == 0 else -3)
    from pumpforge.rotkit import helical_gear
    for i, z in enumerate(zs):
        g, _ = helical_gear(f'tg{i}', 0.1 / 40, 40, -0.02, 0.02, 'steel', cx=0, cz=0, helix_deg=0, phase=(math.pi / 40 if i else 0))
        g.data.transform(Matrix.Translation((X1 + 0.08, 0, z)) @ Matrix.Rotation(math.pi / 2, 4, 'Z'))
        p = P(m, f'timing_gear_{i + 1}', f'Timing Gear {i + 1}', 'gearbox', g, explode=(0.3, 0, 0.15 * (1 - 2 * i)), ref='ds_gears', section='keep', pivot=(0, 0, z))
        p.spin('X', 3 if i == 0 else -3)
    gb = csg('gb', [box('gbo', (0.12, 0.2, 0.3), (X1 + 0.08, 0, CZ), 'paint_grey', bevel=0.01)], [box('gbi', (0.09, 0.17, 0.27), (X1 + 0.08, 0, CZ), 'paint_grey')], 'paint_grey')
    P(m, 'gearbox', 'Gear Case (oil-lubricated, sealed from the gas)', 'gearbox', gb, explode=(0.4, 0, 0), ref='ds_gears')
    add_coupling(m, 'coupling', X1 + 0.2, X1 + 0.29, zs[0], 0.045, 0.018, explode=(0.4, 0, 0), revs=3, foot_z=0.1)
    add_motor_h(m, 'm_', X1 + 0.31, zs[0], 0.13, 0.36, 0.1, 0.018, 0.0, explode_dx=0.7, revs=3)
    add_baseplate(m, X0 - 0.12, X1 + 0.82, 0.45, 0.1)
    con = [cyl('inf', 0.09, CZ + 0.24, CZ + 0.26, 'stainless', 48, center=(X0 + 0.07, 0, 0)),
           hollow_pipe('ex', [(X1 - 0.04, 0, CZ - 0.24), (X1 - 0.04, 0, 0.16), (X1 + 0.1, 0.25, 0.16)], 0.025, 'stainless', 24, bend=0.03, t=0.003)]
    P(m, 'connections', 'Inlet Flange & Exhaust Line (with silencer/check valve downstream)', 'system_piping', con, explode=(0, 0.3, 0.2), ref='ds_connections')
    m.flow('gas', [(X0 + 0.07, 0, CZ + 0.4), (X0 + 0.07, 0, CZ + 0.08), (X0 + 0.2, 0, CZ), (X1 - 0.1, 0, CZ), (X1 - 0.04, 0, CZ - 0.08), (X1 - 0.04, 0, 0.16), (X1 + 0.12, 0.27, 0.16)],
           'air', 0.006, 0.12, speed=[1, 1, 0.9, 0.6, 0.6, 0.8, 1])
    _bands(m, [(X0, X0 + 0.22, 0), (X0 + 0.22, X0 + 0.42, 2), (X0 + 0.42, X1 - 0.08, 5), (X1 - 0.08, X1, 7)], CZ, 0.155, 0.17,
           'Pressure along the screws', 'Gas trapped in the screw threads is carried from the vacuum (inlet) end to the exhaust; the shorter pitch near the exhaust '
           'compresses it internally up to slightly above atmospheric pressure. No oil or liquid is in the compression chamber.')
    m.annotate('pressure', 'Inlet: deep vacuum (e.g. < 1 mbar)', (X0 + 0.05, 0, CZ + 0.3))
    m.annotate('pressure', 'Exhaust: ~ atmospheric', (X1, 0, CZ - 0.3))
    return m.export(out)


# =============================================================== EQ-158 Vacuum (steam jet) ejector
def vacuum_ejector(out):
    m = _model('vacuum_ejector', 'Steam Jet Vacuum Ejector (Single Stage)')
    CZ = 0.5
    sc = csg('sc', [cyl('scb', 0.06, -0.62, -0.42, 'steel', 48, axis='X', center=(0, 0, CZ)), cyl('scf', 0.09, -0.64, -0.62, 'steel', 48, axis='X', center=(0, 0, CZ))],
             [cyl('sci', 0.045, -0.66, -0.4, 'steel', 48, axis='X', center=(0, 0, CZ))], 'steel')
    noz = csg('nz', [lathe('no', [(0.0, -0.44), (0.05, -0.44), (0.03, -0.32), (0.012, -0.27), (0.025, -0.18), (0.0, -0.18)], 'stainless', 48, axis='X', center=(0, 0, CZ))],
              [lathe('ni', [(0.0, -0.45), (0.04, -0.45), (0.022, -0.33), (0.007, -0.28), (0.02, -0.17), (0.0, -0.17)], 'stainless', 48, axis='X', center=(0, 0, CZ))], 'stainless')
    P(m, 'steam_chest', 'Motive Steam Chest & Inlet Flange', 'body', sc, explode=(-0.35, 0, 0), ref='ej_steam_chest')
    P(m, 'nozzle', 'Converging–Diverging Steam Nozzle', 'body', noz, explode=(-0.2, -0.3, 0), ref='ej_nozzle')
    bd = csg('bd', [cyl('bo', 0.12, -0.42, -0.05, 'steel', 64, axis='X', center=(0, 0, CZ)), cyl('su', 0.07, CZ + 0.08, CZ + 0.3, 'steel', 48, center=(-0.26, 0, 0)),
                    cyl('suf', 0.11, CZ + 0.28, CZ + 0.3, 'steel', 48, center=(-0.26, 0, 0))],
             [cyl('bi', 0.105, -0.405, -0.04, 'steel', 64, axis='X', center=(0, 0, CZ)), cyl('sui', 0.058, CZ + 0.05, CZ + 0.31, 'steel', 48, center=(-0.26, 0, 0)),
              cyl('nh', 0.05, -0.44, -0.4, 'steel', 48, axis='X', center=(0, 0, CZ))], 'steel')
    P(m, 'suction_chamber', 'Suction Chamber & Suction Flange (load connection)', 'body', bd, explode=(0, 0, 0.3), ref='ej_suction_chamber')
    df = csg('df', [lathe('dfo', [(0.115, -0.05), (0.06, 0.15), (0.045, 0.3), (0.1, 0.75), (0.1, 0.77), (0.0, 0.77), (0.0, -0.05)], 'steel', 64, axis='X', center=(0, 0, CZ)),
                    cyl('dff', 0.15, 0.75, 0.77, 'steel', 64, axis='X', center=(0, 0, CZ))],
             [lathe('dfi', [(0.105, -0.06), (0.05, 0.15), (0.035, 0.3), (0.09, 0.75), (0.09, 0.78), (0.0, 0.78), (0.0, -0.06)], 'steel', 64, axis='X', center=(0, 0, CZ))], 'steel')
    P(m, 'diffuser', 'Diffuser (converging inlet, throat, diverging outlet)', 'body', df, explode=(0.35, 0, 0), ref='ej_diffuser')
    pip = [hollow_pipe('st', [(-1.0, 0, CZ), (-0.66, 0, CZ)], 0.045, 'insulation', 24, t=0.004),
           hollow_pipe('ld', [(-0.26, 0, CZ + 0.3), (-0.26, 0, CZ + 0.5), (-0.7, 0, CZ + 0.5)], 0.06, 'paint_grey', 32, bend=0.06, t=0.004),
           hollow_pipe('dc', [(0.77, 0, CZ), (1.05, 0, CZ)], 0.09, 'paint_grey', 32, t=0.005),
           pressure_gauge('pg', (-0.26, 0.06, CZ + 0.42), r=0.035, facing=(0, 1, 0))]
    P(m, 'piping', 'Motive Steam Line, Suction (process) Line & Discharge to Condenser', 'system_piping', pip, explode=(0, 0.35, 0), ref='ej_piping')
    sup = [box('s1', (0.05, 0.2, CZ - 0.12), (-0.3, 0, (CZ - 0.12) / 2), 'paint_grey'), box('s2', (0.05, 0.2, CZ - 0.1), (0.5, 0, (CZ - 0.1) / 2), 'paint_grey')]
    P(m, 'supports', 'Supports', 'structure', sup, explode=(0, 0, -0.2), ref='ej_supports', section='keep')
    add_tracers(m, 'steam_jet', 'Motive Steam Jet (tracers)', [(-0.9, 0, CZ), (-0.44, 0, CZ), (-0.28, 0, CZ), (-0.05, 0, CZ), (0.3, 0, CZ), (1.0, 0, CZ)], n=14, radius=0.009, mat='steam', loops=2)
    add_tracers(m, 'entrained_gas', 'Entrained Gas (tracers)', [(-0.6, 0, CZ + 0.5), (-0.26, 0, CZ + 0.5), (-0.26, 0, CZ + 0.08), (-0.12, 0, CZ + 0.03), (0.15, 0, CZ), (1.0, 0, CZ)],
                n=10, radius=0.008, mat='air', loops=1)
    m.flow('motive_steam', [(-1.0, 0, CZ), (-0.44, 0, CZ), (-0.28, 0, CZ), (-0.17, 0, CZ), (0.15, 0, CZ), (0.3, 0, CZ), (1.05, 0, CZ)], 'steam', 0.007, 0.15,
           speed=[1, 1.4, 3, 3.5, 2.5, 1.5, 1])
    m.flow('suction_gas', [(-0.7, 0, CZ + 0.5), (-0.26, 0, CZ + 0.5), (-0.26, 0, CZ + 0.1), (-0.15, 0, CZ + 0.05), (0.15, 0, CZ + 0.01), (0.3, 0, CZ + 0.01), (1.05, 0, CZ + 0.01)],
           'air', 0.006, 0.15, speed=[1, 1, 1.4, 2.2, 2.5, 1.5, 1])
    _bands(m, [(-0.62, -0.44, 9), (-0.44, -0.3, 6), (-0.3, -0.05, 0), (-0.05, 0.15, 1), (0.15, 0.3, 3), (0.3, 0.55, 5), (0.55, 0.77, 6)], CZ, 0.155, 0.17,
           'Pressure through the ejector', 'High-pressure motive steam expands in the nozzle to supersonic speed and very low pressure, entraining gas from the suction '
           'chamber. In the diffuser the mixture slows down and its pressure recovers (shock in the throat) to the discharge (condenser) pressure.')
    m.annotate('pressure', 'Motive steam: high pressure', (-0.55, 0, CZ + 0.18))
    m.annotate('pressure', 'Suction chamber: lowest pressure (vacuum)', (-0.2, 0, CZ - 0.2))
    m.annotate('pressure', 'Diffuser: pressure recovery', (0.45, 0, CZ + 0.2))
    return m.export(out)


# ===================================================================== metadata
def _std(*items):
    return [{'id': i, 'title': t, 'relevance': r, 'edition': 'to be verified'} for i, t, r in items]


META = {
    'reciprocating_compressor': {
        'summary': ('A reciprocating compressor squeezes gas with a piston moving in a cylinder. In this double-acting, crosshead-type machine both ends of the cylinder '
                    'work: while one end draws gas in through its suction valves, the other end compresses gas and pushes it out through its discharge valves. '
                    'Automatic plate valves open and close only by the pressure difference across them.'),
        'classification': {'family': 'Positive-displacement compressor (reciprocating)', 'type': 'Horizontal, single-stage, double-acting, crosshead, lubricated'},
        'model_configuration': {'cylinders': 1, 'action': 'Double-acting', 'valves': '4 automatic plate valves (2 suction, 2 discharge)', 'drive': 'Direct-coupled induction motor'},
        'standards': _std(('API 618', 'Reciprocating Compressors for Petroleum, Chemical, and Gas Industry Services', 'Process-gas reciprocating compressors.'),
                          ('ISO 13631 / API 11P', 'Packaged reciprocating gas compressors', 'Packaged units.'),
                          ('ISO 1217', 'Displacement compressors — Acceptance tests', 'Capacity and power tests.')),
        'references': ['Bloch & Hoefner, Reciprocating Compressors — Operation and Maintenance', 'GPSA Engineering Data Book, Section 13'],
        'components': {**RECIP_META,
            'rc_cylinder': C('Contains the piston and forms the compression chambers at both ends; holds the valves.', 'Cast cylinder with water jacket, liner, valve pockets and heads.',
                             'Cast iron, ductile iron, cast/forged steel.', 'Cooling jacket removes heat of compression.', ['Liner wear/scoring', 'Cracking'], ['Bore measurements, jacket inspection']),
            'rc_distance_piece': C('Separates the cylinder from the crankcase and houses the rod packing.', 'Open or closed distance piece with packing case.', 'Steel; PTFE/bronze packing rings.',
                                   'Vented to prevent process gas reaching the crankcase.', ['Packing leakage'], ['Monitor packing vent flow']),
            'rc_piston': C('Compresses the gas on both strokes.', 'Piston with piston rings and rider bands on a rod connected to the crosshead.', 'Aluminium/cast iron; PTFE rings.',
                           'Rider band wear lets the piston drop toward the liner.', ['Ring wear', 'Rod run-out'], ['Rod drop monitoring']),
            'rc_valve': C('Lets gas in and out at the right time automatically.', 'Plate or ring valves with springs in seat/guard assemblies.', 'Steel, PEEK, stainless springs.',
                          'Most common cause of unplanned shutdowns.', ['Plate breakage', 'Spring failure', 'Fouling'], ['Valve temperature monitoring, overhaul']),
            'rc_bottles': C('Damp pressure pulsations caused by the intermittent flow.', 'Pulsation bottles (volume bottles) on suction and discharge.', 'Carbon steel.',
                            'Designed by acoustic study (API 618).', ['Vibration', 'Fatigue cracking'], ['Vibration survey']),
        },
    },
    'rotary_screw_compressor': {
        'summary': ('An oil-injected rotary screw compressor uses two meshing helical rotors. Gas fills the spaces between the lobes at the inlet end; as the rotors turn '
                    'the pocket is sealed, carried along and made smaller until it opens to the discharge port. Injected oil seals, cools and lubricates; it is then '
                    'separated from the air in the separator vessel and returned.'),
        'classification': {'family': 'Positive-displacement compressor (rotary)', 'type': 'Twin-screw, oil-injected, single stage, direct drive'},
        'model_configuration': {'rotors': 'Male 4 lobes / female 6 flutes', 'capacity_control': 'Inlet (suction-throttle) valve; VFD on many units', 'separator': 'Two-stage separation'},
        'standards': _std(('API 619', 'Rotary-Type Positive-Displacement Compressors', 'Process screw compressors.'), ('ISO 1217', 'Displacement compressors — Acceptance tests', 'FAD and specific power.'),
                          ('ISO 8573-1', 'Compressed air — Contaminants and purity classes', 'Air quality after treatment.')),
        'references': ['Compressed Air & Gas Institute — Compressed Air & Gas Handbook', 'Atlas Copco Compressed Air Manual (generic principles)'],
        'components': {
            'sc_casing': C('Encloses the rotors with tight clearances; contains inlet and discharge ports.', 'Cast casing with intersecting bores.', 'Cast iron.', 'Port shapes set the built-in volume ratio.',
                           ['Bore wear', 'Rotor contact'], ['Clearance check at overhaul']),
            'sc_male': C('Driven rotor; with the female rotor it forms shrinking pockets of gas.', 'Four convex helical lobes.', 'Forged steel.', 'Typical tip speeds ~20–50 m/s (oil-injected).',
                         ['Lobe damage', 'Bearing wear'], ['Vibration, rotor end-float']),
            'sc_female': C('Meshes with the male rotor and is driven through the oil film.', 'Six concave flutes, turns at 4/6 of male speed.', 'Forged steel / ductile iron.', '—', ['Lobe damage'], ['As male']),
            'sc_bearings': C('Locate rotors radially and carry the axial gas thrust.', 'Roller bearings + angular-contact thrust bearings at the discharge end.', 'Bearing steel.',
                             'Bearing life is typically the overhaul interval driver.', ['Fatigue'], ['Vibration trending, SPM']),
            'sc_inlet': C('Cleans incoming air and controls capacity (load/unload or modulation).', 'Dry filter + butterfly or poppet inlet valve.', 'Aluminium, paper/synthetic media.', '—',
                          ['Blocked filter (higher power)'], ['ΔP indicator']),
            'sc_separator': C('Separates oil from the compressed air and stores the oil.', 'Pressure vessel with coalescing element and oil sump.', 'Carbon steel vessel; glass-fibre element.',
                              'Pressure vessel rules apply.', ['Oil carry-over', 'Element ΔP'], ['Change element per hours']),
            'sc_piping': C('Carries air/oil mixture to the separator, oil back to injection, and air to service.', 'Steel and copper lines.', 'Steel, copper.', '—', ['Leaks'], ['Leak check']),
        },
    },
    'rotary_vane_compressor': {
        'summary': ('A rotary vane compressor has a slotted rotor turning off-centre in a cylinder. Vanes slide out against the cylinder wall and divide the space into cells. '
                    'On one side the cells grow and draw air in; on the other side they shrink and compress the air before it leaves through the discharge port. '
                    'Oil injected into the cells seals and cools.'),
        'classification': {'family': 'Positive-displacement compressor (rotary)', 'type': 'Sliding-vane, oil-flooded, single stage'},
        'model_configuration': {'vanes': 8, 'drive': 'Direct, ~1500 rpm typical', 'note': 'Low rotor speed, few wear parts'},
        'standards': _std(('ISO 1217', 'Displacement compressors — Acceptance tests', 'Performance tests.'), ('ISO 8573-1', 'Compressed air purity', 'Air quality.')),
        'references': ['Compressed Air & Gas Handbook (CAGI)'],
        'components': {
            'vc_stator': C('Cylinder in which the rotor turns; contains inlet and outlet ports.', 'Cast stator with end covers.', 'Cast iron.', '—', ['Bore wear'], ['Bore measurement']),
            'vc_rotor': C('Carries the vanes; its eccentricity makes the cells change volume.', 'Slotted rotor integral with shaft.', 'Cast iron/steel.', 'Runs close to the stator at one point.',
                          ['Slot wear'], ['Slot width check']),
            'vc_vane': C('Seal against the stator wall and form the compression cells.', 'Flat vanes free in the slots, thrown out by centrifugal force.', 'Cast iron, steel or composite.',
                         'Wear is self-compensating.', ['Wear, breakage'], ['Vane height check']),
            'vc_piping': C('Inlet filter and connections.', '—', 'Steel.', '—', ['Blocked filter'], ['ΔP check']),
            'vc_separator': C('Separates oil from air and returns it.', 'Receiver with element.', 'Steel.', '—', ['Carry-over'], ['Element change']),
        },
    },
    'roots_blower': {
        'summary': ('A Roots blower moves air with two lobed rotors that turn in opposite directions without touching, kept in step by timing gears. Air is trapped between '
                    'each rotor and the casing and carried from the inlet to the outlet; there is no internal compression — the pressure rises when the pocket opens '
                    'to the higher-pressure discharge (backflow). Used for low pressure ratios such as aeration and pneumatic conveying.'),
        'classification': {'family': 'Positive-displacement blower (rotary lobe)', 'type': 'Tri-lobe Roots blower, belt driven'},
        'model_configuration': {'lobes': 3, 'flow': 'Vertical (inlet top, outlet bottom)', 'drive': 'V-belt from motor (pulley shown)'},
        'standards': _std(('ISO 1217', 'Displacement compressors — Acceptance tests', 'Performance tests.'), ('API 619', 'Rotary PD compressors', 'Process service blowers.')),
        'references': ['Manufacturer blower handbooks (Aerzen, Kaeser — generic principles)'],
        'components': {
            'rb_casing': C('Encloses the rotors and forms the inlet and outlet.', 'Cast casing with end plates.', 'Cast iron.', 'Small clearances (~0.2–0.5 mm).', ['Rubbing from thermal growth'], ['Clearance check']),
            'rb_rotor': C('Carry pockets of air from inlet to outlet.', 'Straight tri-lobe (or twisted) rotors with shafts.', 'Cast iron / ductile iron, steel shafts.', 'Never touch each other or the casing.',
                          ['Contact (bearing failure, overheating)'], ['Vibration, temperature']),
            'rb_gears': C('Keep the two rotors in exact phase.', 'Pair of spur/helical timing gears in an oil bath.', 'Hardened steel.', 'Oil level is critical.', ['Gear wear'], ['Oil level/quality']),
            'rb_silencers': C('Reduce the strong pulsation noise.', 'Absorptive/reactive silencers on inlet and outlet.', 'Steel with absorbent.', '—', ['Blocked filter'], ['ΔP']),
            'rb_pulley': C('Transmits power from the motor via V-belts.', 'Cast-iron sheave.', 'Cast iron.', '—', ['Belt slip'], ['Belt tension']),
        },
    },
    'side_channel_blower': {
        'summary': ('A side channel (regenerative) blower has an impeller with many blades running past a ring-shaped channel in the housing. Air enters, is flung outward '
                    'by the blades into the side channel, flows back to the blade roots and is picked up again — many times around one revolution. This helical '
                    'regeneration builds pressure like a multistage machine, oil-free and almost pulsation-free.'),
        'classification': {'family': 'Dynamic (kinetic) blower', 'type': 'Single-stage side channel blower, direct drive'},
        'model_configuration': {'blades': 40, 'drive': 'Impeller mounted on motor shaft', 'interrupter': 'Solid zone between outlet and inlet'},
        'standards': _std(('ISO 5801', 'Fans — Performance testing using standardized airways', 'Performance tests (adapted).'),),
        'references': ['Manufacturer side channel blower guides (generic principles)'],
        'components': {
            'scb_impeller': C('Accelerates the air repeatedly into the side channel.', 'Cast impeller with many radial blades.', 'Aluminium alloy.', 'Balanced to fine grade.', ['Blade fouling', 'Imbalance'], ['Vibration']),
            'scb_housing': C('Contains the side channel, ports and interrupter.', 'Cast housing with cooling fins.', 'Aluminium alloy.', '—', ['Fouling'], ['Clean channel']),
            'scb_silencers': C('Reduce noise at inlet and outlet.', 'Absorptive silencers.', 'Steel/plastic, foam.', '—', ['Clogging'], ['Clean/replace']),
        },
    },
    'rotary_vacuum_pump': {
        'summary': ('An oil-sealed rotary vane vacuum pump draws gas from a vessel by trapping it between vanes in an eccentric chamber, compressing it to just above '
                    'atmospheric pressure and expelling it through an oil-covered exhaust valve. The oil seals the small clearances, which lets these pumps reach '
                    'a rough to medium vacuum (typically down to ~0.1 mbar or below for two-stage designs).'),
        'classification': {'family': 'Positive-displacement vacuum pump', 'type': 'Oil-sealed rotary vane, single stage'},
        'model_configuration': {'vanes': 3, 'features': 'Gas ballast valve, exhaust demister, oil sight glass'},
        'standards': _std(('ISO 21360-1/-2', 'Vacuum technology — Standard methods for measuring vacuum-pump performance', 'Pumping speed and ultimate pressure.'),
                          ('PNEUROP 6602', 'Vacuum pumps acceptance specifications', 'Legacy reference.')),
        'references': ['Pfeiffer / Leybold vacuum technology fundamentals (generic)'],
        'components': {
            'rv_stator': C('Pumping chamber in which the eccentric rotor turns.', 'Precision-bored cylinder with end covers.', 'Cast iron.', '—', ['Wear, varnish'], ['Ultimate-pressure test']),
            'rv_rotor': C('Carries the vanes.', 'Slotted rotor and shaft.', 'Steel/cast iron.', '—', ['Slot wear'], ['Inspect']),
            'rv_vane': C('Sweep gas from inlet to exhaust.', 'Spring- or centrifugally-loaded vanes.', 'Composite/carbon.', '—', ['Wear, breakage'], ['Inspect']),
            'rv_oilbox': C('Holds the sealing oil that also covers the exhaust valve.', 'Oil casing around the pump stage.', 'Steel/aluminium; vacuum oil.', 'Correct oil grade is essential.',
                           ['Oil contamination', 'Low level'], ['Sight glass, oil change']),
            'rv_exhaust_valve': C('Lets compressed gas out and prevents back-flow.', 'Elastomer flap valve under oil.', 'FKM/NBR.', '—', ['Sticking'], ['Replace at service']),
            'rv_connections': C('Inlet flange, gas-ballast valve (prevents vapour condensation) and exhaust demister.', '—', 'Stainless/aluminium.', 'Open gas ballast for condensable vapours.',
                                ['Oil mist from exhaust'], ['Change demister']),
            'rv_sightglass': C('Shows the oil level and condition.', 'Glass window.', 'Glass.', '—', ['—'], ['Daily check']),
        },
    },
    'liquid_ring_vacuum_pump': {
        'summary': ('A liquid ring vacuum pump has a bladed impeller mounted off-centre in a round casing partly filled with liquid (usually water). As it turns, the liquid '
                    'is thrown out to form a ring concentric with the casing. Because the impeller is eccentric, the spaces between blades grow (drawing gas in through '
                    'the suction port) and then shrink (compressing it out through the discharge port). It tolerates wet, dirty and condensable gases.'),
        'classification': {'family': 'Positive-displacement vacuum pump / compressor', 'type': 'Liquid ring, single stage, flat port plate'},
        'model_configuration': {'blades': 12, 'service_liquid': 'Water (or process liquid)', 'separator': 'Discharge separator with liquid return'},
        'standards': _std(('ISO 21360-1', 'Vacuum pump performance measurement', 'Performance tests.'), ('API 681', 'Liquid Ring Vacuum Pumps and Compressors', 'Process service.')),
        'references': ['Manufacturer liquid ring pump handbooks (generic principles)'],
        'components': {
            'lr_casing': C('Holds the liquid ring; its centre is offset from the impeller.', 'Cylindrical casing.', 'Cast iron, stainless.', '—', ['Erosion/cavitation damage'], ['Inspect']),
            'lr_ring': C('Rotating ring of liquid that acts as the pistons and seals.', 'Service liquid thrown outward.', 'Water / process liquid.', 'Liquid temperature limits vacuum (vapour pressure).',
                         ['Too hot → loss of capacity, cavitation'], ['Monitor seal-liquid flow and temperature']),
            'lr_impeller': C('Rotates the liquid; its cells change volume.', 'Forward-curved bladed impeller, eccentric.', 'Bronze, stainless, ductile iron.', '—', ['Cavitation erosion'], ['Vibration/noise']),
            'lr_port_plate': C('Controls when cells connect to suction and discharge.', 'Flat plate (or cone) with crescent ports.', 'Cast iron/stainless.', 'Port geometry fixes the compression.',
                               ['Scaling/wear'], ['Inspect']),
            'lr_connections': C('Suction and discharge nozzles.', '—', 'Steel.', '—', ['—'], ['—']),
            'lr_separator': C('Separates the service liquid from discharged gas and returns it.', 'Vessel with return line.', 'Steel.', '—', ['Level faults'], ['Level check']),
        },
    },
    'dry_screw_vacuum_pump': {
        'summary': ('A dry screw vacuum pump has two parallel screw rotors that mesh without touching, synchronised by timing gears. Gas trapped in the threads is moved '
                    'from the inlet (vacuum side) to the exhaust; a shorter pitch toward the exhaust compresses it internally. No oil or water is in the gas path, '
                    'so the gas is not contaminated — ideal for chemical, pharmaceutical and semiconductor processes.'),
        'classification': {'family': 'Positive-displacement vacuum pump (dry)', 'type': 'Twin screw, variable pitch, water-cooled'},
        'model_configuration': {'pitch': 'Three-step decreasing pitch', 'gears': 'Timing gears in sealed oil case', 'purge': 'Shaft-seal gas purge (typical)'},
        'standards': _std(('ISO 21360-1/-2', 'Vacuum pump performance', 'Performance.'), ('ATEX 2014/34/EU', 'Equipment for explosive atmospheres', 'Where flammable gas is pumped.')),
        'references': ['Busch / Edwards dry vacuum technology notes (generic)'],
        'components': {
            'ds_casing': C('Encloses the screws with tight clearances; water jacket removes heat.', 'Cast casing with cooling jacket.', 'Cast iron (often coated).', '—', ['Deposits'], ['Flushing, inspection']),
            'ds_screw': C('Carry gas from inlet to exhaust and compress it.', 'Single-start screws with variable pitch.', 'Steel, coated.', 'Non-contacting.', ['Deposits, rubbing'], ['Current/temperature trend']),
            'ds_gears': C('Keep the screws synchronised.', 'Spur timing gears in sealed oil case.', 'Hardened steel.', 'Seals keep oil out of the gas path.', ['Gear wear'], ['Oil check']),
            'ds_connections': C('Inlet and exhaust connections.', '—', 'Stainless.', '—', ['—'], ['—']),
        },
    },
    'vacuum_ejector': {
        'summary': ('A steam jet vacuum ejector has no moving parts. High-pressure motive steam expands through a converging–diverging nozzle to very high (supersonic) '
                    'velocity and low pressure, which entrains gas from the suction chamber. In the diffuser the mixture slows down and its pressure rises to the discharge '
                    'pressure. Several ejectors in series with condensers reach deep vacuum.'),
        'classification': {'family': 'Kinetic (jet) vacuum device', 'type': 'Single-stage steam jet ejector'},
        'model_configuration': {'motive': 'Steam', 'discharge': 'To condenser or next stage'},
        'standards': _std(('HEI 2866', 'Standards for Steam Jet Vacuum Systems (Heat Exchange Institute)', 'Design and testing of ejector systems.'),),
        'references': ['Perry\'s Chemical Engineers\' Handbook — ejectors', 'Graham / Körting ejector notes (generic)'],
        'components': {
            'ej_steam_chest': C('Receives motive steam.', 'Flanged chest.', 'Carbon steel.', 'Steam must be dry and at design pressure.', ['Wet steam → poor performance'], ['Steam pressure check']),
            'ej_nozzle': C('Converts steam pressure into velocity.', 'Converging–diverging (de Laval) nozzle.', 'Stainless steel.', 'Throat size fixes steam flow.', ['Erosion, fouling'], ['Inspect throat']),
            'ej_suction_chamber': C('Where the jet entrains the process gas.', 'Body with suction flange.', 'Carbon steel.', '—', ['Leaks (air in-leakage)'], ['Leak test']),
            'ej_diffuser': C('Recovers pressure as the mixture slows down.', 'Converging inlet, throat, diverging outlet.', 'Carbon/stainless steel.', 'Discharge pressure above design causes "break" (loss of vacuum).',
                             ['Erosion, scaling'], ['Inspect']),
            'ej_piping': C('Motive steam, suction and discharge lines.', '—', 'Steel.', '—', ['—'], ['—']),
            'ej_supports': C('Support the ejector.', '—', 'Steel.', '—', ['—'], ['—']),
        },
    },
}

BUILDERS = {'reciprocating_compressor': reciprocating_compressor, 'rotary_screw_compressor': rotary_screw_compressor,
            'rotary_vane_compressor': rotary_vane_compressor, 'roots_blower': roots_blower, 'side_channel_blower': side_channel_blower,
            'rotary_vacuum_pump': rotary_vacuum_pump, 'liquid_ring_vacuum_pump': liquid_ring_vacuum_pump,
            'dry_screw_vacuum_pump': dry_screw_vacuum_pump, 'vacuum_ejector': vacuum_ejector}
