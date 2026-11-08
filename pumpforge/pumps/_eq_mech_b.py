"""Mechanical Components & Maintenance — part B (EQ-334 … EQ-345): rotor, stator, gears, lubrication systems,
alignment & balancing, vibration and online condition monitoring."""
import math
from mathutils import Matrix, Vector
from pumpforge.core import Model, lathe, cyl, box, csg, join, rotate, TAU, OPERATE_FRAMES
from pumpforge.valvekit import P, keys_loop, spring, smooth_pulse
from pumpforge.parts import hollow_pipe, pressure_gauge, add_tracers
from pumpforge.vesselkit import vessel, nozzle, legs, droplets, half, animate_level
from pumpforge.plantkit import ball, particles_path
from pumpforge.shapes import sweep_tube, cone_arrow
from pumpforge.rotkit import helical_gear, axis_rot_keys
from pumpforge.common_meta import C
from pumps._eq_thermal_a import _pump, _fan_rotor
from pumps._eq_mech_a import _torus, _ov, _std, _c, _comp

CAT = '14 · Mechanical Components & Maintenance'


def _model(pid, title):
    return Model(pid, title, CAT, META[pid])


def _motor(name, x0, x1, cz, R, mat='paint_motor', foot_z=0.0, y=0.0):
    """TEFC motor body along +X from x0 (drive end) to x1, with fins, feet, terminal box and fan cowl."""
    o = [cyl(name + 'b', R, x0, x1, mat, 48, axis='X', center=(0, y, cz), ch=0.01)]
    o += [rotate(box(name + f'f{k}', (x1 - x0 - 0.04, 0.012, R * 0.2), ((x0 + x1) / 2, y, cz + R + R * 0.05), mat), TAU * k / 12 + math.pi / 12, 'X', (0, y, cz)) for k in range(12)]
    o += [cyl(name + 'cw', R * 0.95, x1, x1 + R * 0.6, mat, 48, axis='X', center=(0, y, cz)), box(name + 'tb', (R * 0.8, R * 0.7, R * 0.5), ((x0 + x1) / 2, y, cz + R + R * 0.2), mat)]
    for s in (-1, 1):
        o.append(box(name + f'ft{s}', (x1 - x0 - 0.06, R * 0.35, cz - R * 0.6 - foot_z), ((x0 + x1) / 2, y + s * R * 0.7, foot_z + (cz - R * 0.6 - foot_z) / 2), mat))
    return join(name, o)


# =============================================================== EQ-334 Rotor (squirrel-cage)
def rotor(out):
    m = _model('rotor', 'Induction Motor Rotor (Squirrel Cage) on V-Block Stands')
    CZ, L, Rr = 0.45, 0.5, 0.15
    core = [cyl('cr', Rr, -L / 2, L / 2, 'lamination', 96, axis='X', r_in=0.045)]
    for k in range(28):
        a = TAU * k / 28
        b = box(f'bar{k}', (L + 0.02, 0.016, 0.022), (0, 0, Rr - 0.016), 'copper')
        b = rotate(b, math.radians(8), 'Z', (0, 0, Rr - 0.016))
        core.append(rotate(b, a, 'X'))
    for o in core:
        o.data.transform(Matrix.Translation((0, 0, CZ)))
    er = [cyl(f'er{k}', Rr - 0.002, x0, x1, 'aluminium', 96, axis='X', center=(0, 0, CZ), r_in=Rr - 0.04) for k, (x0, x1) in enumerate(((-L / 2 - 0.035, -L / 2), (L / 2, L / 2 + 0.035)))]
    fins = [rotate(box(f'cf{k}', (0.03, 0.006, 0.03), (L / 2 + 0.05, 0, CZ + Rr - 0.04), 'aluminium'), TAU * k / 10, 'X', (0, 0, CZ)) for k in range(10)]
    sh = [cyl('sh', 0.045, -0.62, 0.62, 'steel', 48, axis='X', center=(0, 0, CZ), ch=0.003), cyl('jd', 0.04, -0.62, -0.45, 'chrome', 48, axis='X', center=(0, 0, CZ)),
          cyl('jn', 0.04, 0.45, 0.62, 'chrome', 48, axis='X', center=(0, 0, CZ)), box('kw', (0.1, 0.012, 0.008), (-0.55, 0, CZ + 0.04), 'steel_dark'),
          cyl('fan', 0.12, 0.5, 0.52, 'thermoplastic', 48, axis='X', center=(0, 0, CZ), r_in=0.04)] + [rotate(box(f'fb{k}', (0.06, 0.004, 0.07), (0.54, 0, CZ + 0.085), 'thermoplastic'), TAU * k / 8, 'X', (0, 0, CZ)) for k in range(8)]
    bw = [box(f'bw{k}', (0.02, 0.02, 0.015), (x, 0, CZ + Rr - 0.045), 'brass') for k, x in enumerate((-L / 2 - 0.017, L / 2 + 0.017))]
    pr = P(m, 'rotor_core_bars', 'Laminated Core with Skewed Rotor Bars (copper / die-cast aluminium)', 'rotating_element', core, explode=(0, -0.4, 0.3), ref='rot_core', section='keep', pivot=(0, 0, CZ))
    pr.spin('X', 1)
    pe = P(m, 'end_rings', 'Short-Circuit End Rings, Cooling Fins & Balance Weights', 'rotating_element', er + fins + bw, explode=(0, -0.3, 0.5), ref='rot_rings', section='keep', pivot=(0, 0, CZ))
    pe.spin('X', 1)
    ps = P(m, 'shaft_fan', 'Shaft (journals, keyway) & Cooling Fan', 'rotating_element', sh, explode=(0, 0.3, 0.3), ref='rot_shaft', section='keep', pivot=(0, 0, CZ))
    ps.spin('X', 1)
    st = []
    for k, x in enumerate((-0.53, 0.53)):
        st += [box(f'vb{k}', (0.1, 0.16, CZ - 0.05), (x, 0, (CZ - 0.05) / 2), 'paint_grey'), box(f'vr{k}', (0.1, 0.03, 0.06), (x, 0.04, CZ - 0.06), 'brass'), box(f'vl{k}', (0.1, 0.03, 0.06), (x, -0.04, CZ - 0.06), 'brass')]
    P(m, 'v_block_stands', 'V-Block / Roller Stands (inspection and balancing)', 'structure', st, explode=(0, 0, -0.3), ref='rot_stands', section='keep')
    m.flow('cooling_air', [(0.75, 0, CZ + 0.05), (0.55, 0.004, CZ + 0.1), (0.45, 0.004, CZ + 0.17), (-0.4, 0.004, CZ + 0.2)], 'air', 0.008, 0.1)
    lines = []
    for k in range(4):
        a = TAU * k / 4
        pts = [(0.0, (Rr - 0.02 + 0.1 * math.sin(math.pi * t)) * math.cos(a + 1.2 * t), CZ + (Rr - 0.02 + 0.1 * math.sin(math.pi * t)) * math.sin(a + 1.2 * t)) for t in [j / 12 for j in range(13)]]
        lines.append(sweep_tube(f'fl{k}', pts, 0.004, 'magnet_n' if k % 2 == 0 else 'magnet_s', 8, cap=True))
    m.overlay('magnetic_field', join('mf', lines), 'Rotating field induces current in the bars', 'The stator\'s rotating magnetic field sweeps past the rotor bars faster than they move (slip ≈ 0.5–5 % at load). '
              'This induces voltage and large currents in the short-circuited cage; the current in the field produces torque. Bars are skewed (≈ one slot pitch) to smooth torque and reduce noise. '
              'Broken bars or cracked end rings show up as current side-bands at slip frequency and as hot spots.', split=False)
    return m.export(out)


# =============================================================== EQ-335 Stator
def stator(out):
    m = _model('stator', 'Induction Motor Stator: Frame, Laminated Core, Three-Phase Windings & Terminal Box')
    CZ, L, Ri, Ro = 0.5, 0.5, 0.155, 0.27
    fr = csg('fr', [cyl('fro', 0.32, -0.33, 0.33, 'paint_motor', 96, axis='X', center=(0, 0, CZ)), box('frf', (0.5, 0.56, 0.05), (0, 0, 0.025 + 0.1), 'paint_motor')] +
             [cyl(f'rib{k}', 0.335, x - 0.01, x + 0.01, 'paint_motor', 96, axis='X', center=(0, 0, CZ)) for k, x in enumerate((-0.2, -0.1, 0.0, 0.1, 0.2))],
             [cyl('fri', Ro, -0.4, 0.4, 'paint_motor', 96, axis='X', center=(0, 0, CZ))], 'paint_motor')
    P(m, 'frame', 'Cast Frame with Cooling Ribs & Feet', 'casing', [fr] + [box(f'ft{s}', (0.5, 0.12, CZ - 0.25), (0, s * 0.22, (CZ - 0.25) / 2 + 0.1), 'paint_motor') for s in (-1, 1)], explode=(0, 0.6, 0), ref='sta_frame')
    core = csg('core', [cyl('co', Ro, -L / 2, L / 2, 'lamination', 96, axis='X', center=(0, 0, CZ))],
               [cyl('ci', Ri, -0.4, 0.4, 'lamination', 96, axis='X', center=(0, 0, CZ))] + [rotate(box(f'sl{k}', (L + 0.1, 0.022, 0.05), (0, 0, CZ + Ri + 0.022), 'lamination'), TAU * k / 36, 'X', (0, 0, CZ)) for k in range(36)], 'lamination')
    P(m, 'stator_core', 'Laminated Stator Core with 36 Slots (insulated electrical-steel sheets)', 'core', core, explode=(0, 0.35, 0.2), ref='sta_core')
    cols = ['copper', 'brass', 'bronze']
    wd = []
    for k in range(36):
        a = TAU * k / 36
        wd.append(rotate(box(f'cs{k}', (L + 0.02, 0.016, 0.04), (0, 0, CZ + Ri + 0.025), cols[(k // 2) % 3]), a, 'X', (0, 0, CZ)))
    for s in (-1, 1):
        for k in range(12):
            a0, a1 = TAU * k / 12, TAU * (k + 2.2) / 12
            pts = []
            for j in range(9):
                t = j / 8
                a = a0 + (a1 - a0) * t
                r = Ri + 0.03 + 0.015 * math.sin(math.pi * t)
                pts.append((s * (L / 2 + 0.01 + 0.05 * math.sin(math.pi * t)), r * math.cos(a), CZ + r * math.sin(a)))
            wd.append(sweep_tube(f'ew{s}{k}', pts, 0.008, cols[k % 3], 8, cap=True))
    P(m, 'windings', 'Three-Phase Windings: Coil Sides in Slots & End Windings (U, V, W)', 'windings', wd, explode=(0, -0.4, 0.3), ref='sta_windings', section='split')
    tb = [box('tbx', (0.2, 0.18, 0.12), (0, 0, CZ + 0.38), 'paint_motor'), box('tbl', (0.22, 0.2, 0.02), (0, 0, CZ + 0.45), 'paint_motor')] + [cyl(f'tt{k}', 0.01, CZ + 0.44, CZ + 0.47, 'brass', 12, center=(-0.06 + 0.06 * k, 0, 0)) for k in range(3)]
    tb += [hollow_pipe(f'ld{k}', [(L / 2 + 0.03, 0.05 * (k - 1), CZ + Ri + 0.07), (0.05, 0.05 * (k - 1), CZ + 0.3), (-0.06 + 0.06 * k, 0, CZ + 0.33)], 0.006, cols[k], 8, bend=0.02) for k in range(3)]
    P(m, 'terminal_box', 'Terminal Box, Leads & Terminals (U1 V1 W1)', 'electrical', tb, explode=(0, 0, 0.4), ref='sta_terminal', section='keep')
    rf = [cyl('rfn', 0.03, -0.012, 0.012, 'magnet_n', 24, axis='Y', center=(0, Ri - 0.03, CZ)), cyl('rfs', 0.03, -0.012, 0.012, 'magnet_s', 24, axis='Y', center=(0, -(Ri - 0.03), CZ)),
          cyl('rfa', 0.006, -(Ri - 0.06), Ri - 0.06, 'steel', 8, axis='Y', center=(0, 0, CZ))]
    rf = [rotate(o, math.pi / 2, 'X', (0, 0, CZ)) for o in rf]
    prf = P(m, 'rotating_field', 'Rotating Magnetic Field (N/S marker turning at synchronous speed)', 'field', rf, explode=(0, 0, 0), ref='sta_field', section='keep', pivot=(0, 0, CZ))
    prf.spin('X', 1)
    m.flow('supply', [(0, 0, CZ + 0.8), (0, 0, CZ + 0.47)], 'electric', 0.008, 0.1)
    arcs = []
    for k in range(4):
        a0 = TAU * k / 4
        pts = [(0.0, (Ri + 0.06 * math.sin(math.pi * t)) * math.cos(a0 + math.pi / 2 * t), CZ + (Ri + 0.06 * math.sin(math.pi * t)) * math.sin(a0 + math.pi / 2 * t)) for t in [j / 12 for j in range(13)]]
        arcs.append(sweep_tube(f'fa{k}', pts, 0.005, 'magnet_n' if k % 2 == 0 else 'magnet_s', 8, cap=True))
    m.overlay('magnetic_field', join('mf', arcs), 'Three phase currents make a rotating field', 'Three windings 120° apart carry currents 120° out of phase; their combined field rotates at synchronous speed '
              'n_s = 120·f / p (e.g. 1500 rpm for 4 poles at 50 Hz). The laminated core carries the flux with low eddy-current loss. Winding insulation (class F/H) is the life-limiting part: '
              'each ≈ 10 °C over its rating roughly halves insulation life, so overload, poor cooling and voltage unbalance matter. Test with insulation resistance / polarisation index.', split=False)
    return m.export(out)


# =============================================================== EQ-336 Gear assembly (spur train with idler)
def gear_assembly(out):
    m = _model('gear_assembly', 'Gear Assembly — Spur Gear Train (Pinion, Idler, Gear) with Shafts, Bearings & Keys')
    mod, CZ = 0.012, 0.5
    z1, z2, z3 = 16, 24, 48
    x1 = -mod * (z1 + z2) / 2
    x3 = mod * (z2 + z3) / 2
    y0, y1 = -0.04, 0.04
    g1, rp1 = helical_gear('g1', mod, z1, y0, y1, 'steel', cx=x1, cz=CZ, helix_deg=0)
    g2, rp2 = helical_gear('g2', mod, z2, y0, y1, 'steel', cx=0.0, cz=CZ, helix_deg=0, phase=math.pi / z2)
    g3, rp3 = helical_gear('g3', mod, z3, y0, y1, 'steel', cx=x3, cz=CZ, helix_deg=0)
    for nm, g, x, z, revs, label in (('pinion', g1, x1, z1, 3, 'Driving Pinion (z = 16)'), ('idler', g2, 0.0, z2, -2, 'Idler Gear (z = 24) — reverses direction, ratio unchanged'),
                                     ('gear', g3, x3, z3, 1, 'Driven Gear (z = 48)')):
        sh = [cyl(nm + 'sh', 0.022, -0.25, 0.2, 'steel', 32, axis='Y', center=(x, 0, CZ)), box(nm + 'ky', (0.012, 0.06, 0.01), (x, 0.0, CZ + 0.022), 'steel_dark'),
              box(nm + 'mk', (0.02, 0.01, 0.02), (x, y1 + 0.005, CZ + rp1 * 0.6 if nm == 'pinion' else CZ + (rp2 if nm == 'idler' else rp3) * 0.6), 'paint_yellow')]
        p = P(m, nm, label + ' on Keyed Shaft', 'rotating_element', [g] + sh, explode=(0, -0.3, 0.2 + 0.1 * (nm == 'idler')), ref='ga_gears', section='keep', pivot=(x, 0, CZ))
        p.spin('Y', revs)
    br = []
    for x in (x1, 0.0, x3):
        for yy in (-0.15, 0.15):
            br.append(cyl(f'br{x:.2f}{yy}', 0.045, yy - 0.015, yy + 0.015, 'chrome', 32, axis='Y', center=(x, 0, CZ), r_in=0.023))
    P(m, 'bearings', 'Rolling Bearings (two per shaft)', 'bearings', br, explode=(0, 0.3, 0.3), ref='ga_bearings', section='keep')
    fr = csg('fr', [box('fb', (0.95, 0.5, 0.06), (x3 / 2 + x1 / 2, 0, 0.03), 'paint_grey')] + [box(f'fp{s}', (0.95, 0.04, CZ + 0.06), (x3 / 2 + x1 / 2, s * 0.15, (CZ + 0.06) / 2), 'paint_grey') for s in (-1, 1)],
             [cyl(f'fh{k}{s}', 0.046, s * 0.15 - 0.03, s * 0.15 + 0.03, 'paint_grey', 32, axis='Y', center=(x, 0, CZ)) for k, x in enumerate((x1, 0.0, x3)) for s in (-1, 1)], 'paint_grey')
    P(m, 'frame', 'Gear Frame / Bearing Plates (housing removed for teaching)', 'structure', fr, explode=(0, 0.5, -0.2), ref='ga_frame')
    m.flow('power', [(x1, -0.3, CZ), (x1, -0.06, CZ), (x1 + rp1, -0.06, CZ + 0.005), (0.0, -0.06, CZ), (rp2, -0.06, CZ), (x3, -0.06, CZ), (x3, 0.25, CZ)], 'power', 0.006, 0.08, speed=[3, 3, 3, 2, 2, 1, 1])
    pa = math.radians(20)
    ol = []
    for k, xc in enumerate((x1 + rp1, rp2)):
        d = Vector((math.sin(pa), 0, math.cos(pa)))
        a, b = Vector((xc, y1 + 0.004, CZ)) - d * 0.05, Vector((xc, y1 + 0.004, CZ)) + d * 0.05
        ol.append(sweep_tube(f'loa{k}', [tuple(a), tuple(b)], 0.003, 'pressure_8', 8))
        ol.append(cyl(f'cp{k}', 0.01, y1, y1 + 0.006, 'pressure_9', 16, axis='Y', center=(xc, 0, CZ)))
    for k, (x, r) in enumerate(((x1, rp1), (0.0, rp2), (x3, rp3))):
        ol.append(cyl(f'pc{k}', r + 0.0015, y1 + 0.002, y1 + 0.004, 'pressure_4', 96, axis='Y', center=(x, 0, CZ), r_in=r - 0.0015))
    _ov(m, 'pressure', ol, 'Pitch circles roll; force acts along the line of action', 'Mating gears behave like pitch circles rolling without slipping: speed ratio = z_driven / z_driver (here 48/16 = 3; the idler '
        'changes direction only). Tooth force acts along the line of action at the pressure angle (20°), splitting into a tangential (torque) and a separating (radial) component that the bearings carry. '
        'Correct centre distance gives the designed backlash; contact pattern, lubrication and alignment decide gear life (pitting, scuffing, tooth breakage).')
    return m.export(out)


# =============================================================== EQ-337 Lubricating oil skid
def lubricating_oil_skid(out):
    m = _model('lubricating_oil_skid', 'Lubricating Oil Skid (Pressure-Fed, API 614 style) for a Turbomachine')
    rs = csg('rs', [box('rso', (2.0, 1.0, 0.8), (0, 0, 0.5), 'stainless')], [box('rsi', (1.94, 0.94, 0.8), (0, 0, 0.53), 'stainless')], 'stainless')
    P(m, 'reservoir', 'Oil Reservoir (≈ 3–8 min of flow; sloped bottom, baffles)', 'tank', [rs, box('rb', (0.02, 0.9, 0.5), (0.2, 0, 0.42), 'stainless'), box('rt', (2.04, 1.04, 0.03), (0, 0, 0.915), 'stainless'), box('sk', (2.3, 1.3, 0.1), (0, 0, 0.05), 'paint_grey')],
      explode=(0, 0.6, -0.2), ref='lo_reservoir')
    oil = box('oil', (1.93, 0.465, 0.55), (0, 0.233, 0.4), 'hydraulic_oil')
    po = P(m, 'oil', 'Lube Oil (ISO VG 32/46 turbine oil)', 'fluid', oil, explode=(0, -0.4, 0), ref='lo_reservoir', section='keep')
    animate_level(m, po, 0.6, -0.03, lambda t: 0.5 - 0.5 * math.cos(TAU * t))
    P(m, 'heater', 'Immersion Heater (keeps oil warm for start-up)', 'thermal', [cyl('ht', 0.03, -0.9, -0.4, 'hot_glow', 16, axis='X', center=(0, 0.25, 0.22)), box('hth', (0.12, 0.12, 0.12), (-1.06, 0.25, 0.22), 'paint_grey')],
      explode=(-0.3, 0, 0), ref='lo_reservoir', section='keep')
    for k, x in enumerate((-0.6, 0.3)):
        _pump(m, f'pump_{"main" if k == 0 else "standby"}', ('Main' if k == 0 else 'Standby (auto-start on low pressure)') + ' Lube Oil Pump', x, -0.25, 1.05, 'lo_pumps', explode=(0, -0.4, 0.2))
    P(m, 'pump_suctions', 'Pump Suction Lines (from reservoir)', 'piping', [hollow_pipe(f'ps{k}', [(x, -0.25, 0.93), (x, -0.25, 0.25)], 0.03, 'stainless', 12) for k, x in enumerate((-0.6, 0.3))], explode=(0, -0.2, 0), ref='lo_pumps', section='keep')
    cl = [vessel(f'cl{k}', 0.12, 0.7, 0.005, 'paint_blue', axis='X', center=(0, y, 1.5), heads=('flat', 'flat'), z0=-0.45) for k, y in enumerate((-0.2, 0.2))]
    cl += [hollow_pipe(f'cw{k}', [(-0.3, y, 1.62), (-0.3, y, 1.8), (-0.7, y, 1.8)], 0.02, 'paint_green', 8, bend=0.03) for k, y in enumerate((-0.2, 0.2))]
    cl += [box(f'cs{k}{j}', (0.06, 0.06, 0.45), (x, y, 1.155), 'paint_grey') for k, y in enumerate((-0.2, 0.2)) for j, x in enumerate((-0.35, 0.15))]
    P(m, 'coolers', 'Twin Oil Coolers (shell & tube; one in service)', 'heat_exchange', cl, explode=(0, 0, 0.5), ref='lo_coolers', section='keep')
    fl = [vessel(f'fl{k}', 0.1, 0.45, 0.004, 'paint_grey', heads=('flat', '2:1'), z0=1.05, center=(0.65, y, 0)) for k, y in enumerate((-0.2, 0.2))]
    fl += [box(f'fs{k}', (0.12, 0.12, 0.12), (0.65, y, 0.99), 'paint_grey') for k, y in enumerate((-0.2, 0.2))]
    fl += [box('tv', (0.12, 0.25, 0.12), (0.65, 0, 1.25), 'brass'), cyl('tvh', 0.04, 1.31, 1.4, 'paint_red', 16, center=(0.65, 0, 0)), box('dpi', (0.06, 0.04, 0.08), (0.78, 0, 1.55), 'paint_blue_dark')]
    P(m, 'filters', 'Duplex Filters with Six-Way Transfer Valve & ΔP Indicator', 'filters', fl, explode=(0.3, 0, 0.4), ref='lo_filters', section='keep')
    pp = [hollow_pipe('pd', [(-0.6, -0.25, 1.17), (-0.6, -0.25, 1.3), (0.3, -0.25, 1.3), (0.3, -0.25, 1.17)], 0.025, 'stainless', 12, bend=0.04),
          hollow_pipe('pc', [(-0.15, -0.25, 1.3), (-0.15, -0.2, 1.5), (-0.45, -0.2, 1.5)], 0.025, 'stainless', 12, bend=0.04), hollow_pipe('cf', [(0.25, 0.2, 1.5), (0.65, 0.2, 1.5), (0.65, 0.2, 1.42)], 0.025, 'stainless', 12, bend=0.04),
          hollow_pipe('hdr', [(0.65, 0, 1.05), (0.65, 0, 0.98), (1.25, 0, 0.98), (1.25, 0, 1.6), (1.6, 0, 1.6)], 0.03, 'stainless', 12, bend=0.05), box('pcv', (0.1, 0.1, 0.12), (1.25, 0, 1.3), 'brass'),
          hollow_pipe('ret', [(1.6, 0.35, 0.95), (0.8, 0.35, 0.95)], 0.05, 'stainless', 16), hollow_pipe('byp', [(1.25, 0, 1.15), (1.05, 0.3, 1.15), (1.05, 0.3, 0.93)], 0.02, 'stainless', 8, bend=0.03),
          vessel('acc', 0.1, 0.4, 0.005, 'paint_grey', heads=('2:1', '2:1'), z0=1.7, center=(1.45, 0, 0)), cyl('accn', 0.02, 1.6, 1.65, 'stainless', 8, center=(1.45, 0, 0)),
          pressure_gauge('pg', (1.25, -0.06, 1.45), r=0.035, facing=(0, -1, 0)), box('tt', (0.04, 0.04, 0.08), (1.4, -0.03, 1.66), 'paint_blue_dark')]
    P(m, 'header_controls', 'Discharge Header, Pressure-Control Valve (spill-back), Accumulator, Supply to Machine & Return Line, Gauges / Transmitters', 'piping', pp, explode=(0.4, 0, 0.3), ref='lo_controls', section='keep')
    m.flow('oil_circuit', [(-0.6, -0.25, 0.3), (-0.6, -0.25, 1.3), (-0.15, -0.25, 1.3), (-0.15, -0.2, 1.5), (0.25, -0.2, 1.5), (0.25, 0.2, 1.5), (0.65, 0.2, 1.42), (0.65, 0.2, 1.1), (0.65, 0, 0.98), (1.25, 0, 0.98), (1.25, 0, 1.6), (1.7, 0, 1.6)],
           'hydraulic_oil', 0.012, 0.25)
    m.flow('return', [(1.7, 0.35, 0.95), (0.8, 0.35, 0.95), (0.6, 0.3, 0.6)], 'hydraulic_oil', 0.015, 0.2)
    m.flow('cooling_water', [(-0.75, -0.2, 1.8), (-0.3, -0.2, 1.8), (-0.3, -0.2, 1.62)], 'water', 0.008, 0.15)
    _ov(m, 'pressure', [box('p0', (0.9, 0.02, 0.06), (-0.15, -0.32, 1.3), 'pressure_8'), box('p1', (0.6, 0.02, 0.06), (0.95, -0.08, 0.98), 'pressure_6'), box('p2', (0.4, 0.02, 0.06), (1.45, -0.08, 1.6), 'pressure_5'),
                        box('p3', (0.8, 0.02, 0.08), (1.2, 0.4, 0.95), 'pressure_1')], 'Clean, cool oil at controlled pressure', 'The main pump delivers more oil than the machine needs; the pressure-control valve spills '
        'the excess back to the reservoir to hold header pressure (typically ≈ 1–2.5 bar(g) at the bearings). Coolers keep supply ≈ 40–50 °C; duplex filters (≈ 10 µm) can be switched on-line. The '
        'standby pump starts automatically on falling pressure, and the accumulator / rundown tank covers the switch-over and coast-down so bearings are never starved.')
    return m.export(out)


# =============================================================== EQ-338 Grease lubrication system (bearing + single-point lubricator)
def grease_lubrication_system(out):
    m = _model('grease_lubrication_system', 'Grease Lubrication of a Plummer-Block Bearing — Grease Nipple, Relief Plug & Automatic Single-Point Lubricator')
    CZ = 0.25
    hs = csg('hs', [box('hso', (0.22, 0.24, 0.3), (0, 0, CZ), 'cast_iron'), box('hsb', (0.22, 0.5, 0.06), (0, 0, 0.06), 'cast_iron')],
             [cyl('hsi', 0.105, -0.08, 0.08, 'cast_iron', 64, axis='X', center=(0, 0, CZ)), cyl('hsx', 0.042, -0.2, 0.2, 'cast_iron', 64, axis='X', center=(0, 0, CZ)), cyl('nh', 0.006, CZ, CZ + 0.2, 'cast_iron', 8, center=(0.03, 0, 0)),
              cyl('dh', 0.008, 0.0, CZ, 'cast_iron', 8, center=(-0.03, 0, 0))] + [cyl(f'bh{s}', 0.012, 0.0, 0.2, 'cast_iron', 12, center=(0, s * 0.2, 0)) for s in (-1, 1)], 'cast_iron')
    P(m, 'plummer_block', 'Split Plummer-Block Housing (cap & base)', 'casing', hs, explode=(0, 0.5, 0), ref='gl_housing')
    _rs = [cyl('ir', 0.058, -0.035, 0.035, 'steel', 64, axis='X', center=(0, 0, CZ), r_in=0.04), cyl('or', 0.1, -0.035, 0.035, 'steel', 64, axis='X', center=(0, 0, CZ), r_in=0.085)]
    P(m, 'bearing_rings', 'Spherical Roller Bearing — Rings', 'bearing', _rs, explode=(0, 0.3, 0.3), ref='gl_bearing')
    rl = []
    for row, xr in enumerate((-0.017, 0.017)):
        for k in range(14):
            a = TAU * (k + 0.5 * row) / 14
            r = lathe(f'rl{row}{k}', [(0.0, -0.016), (0.011, -0.014), (0.012, 0.0), (0.011, 0.014), (0.0, 0.016)], 'chrome', 12, axis='X', center=(0, 0.072 * math.cos(a), CZ + 0.072 * math.sin(a)))
            r.data.transform(Matrix.Translation((xr, 0, 0)))
            rl.append(r)
    pr = P(m, 'rollers', 'Barrel Rollers in Two Rows (cage turns ≈ 0.4 × shaft speed)', 'bearing', rl, explode=(0, -0.3, 0.3), ref='gl_bearing', section='keep', pivot=(0, 0, CZ))
    pr.spin('X', 0.8)
    sh = [cyl('sh', 0.04, -0.35, 0.35, 'steel', 48, axis='X', center=(0, 0, CZ)), box('shm', (0.05, 0.01, 0.008), (0.28, 0, CZ + 0.041), 'steel_dark')]
    psh = P(m, 'shaft', 'Shaft (turning)', 'rotating_element', sh, explode=(0, -0.4, 0), ref='gl_shaft', section='keep', pivot=(0, 0, CZ))
    psh.spin('X', 2)
    gr = half(csg('gr', [cyl('gro', 0.104, -0.075, 0.075, 'powder', 64, axis='X', center=(0, 0, CZ))], [cyl('gri', 0.059, -0.1, 0.1, 'powder', 64, axis='X', center=(0, 0, CZ)),
                                                                                                     box('grt', (0.2, 0.3, 0.1), (0, 0, CZ + 0.1), 'powder')], 'powder'), 'powder')
    P(m, 'grease_fill', 'Grease Fill (bearing full; housing ≈ 30–50 % — never packed solid)', 'fluid', gr, explode=(0, -0.5, -0.1), ref='gl_grease', section='keep')
    P(m, 'seals', 'Housing Seals (labyrinth / V-ring) at both sides', 'seal', [cyl(f'sl{k}', 0.06, x0, x1, 'rubber', 64, axis='X', center=(0, 0, CZ), r_in=0.041) for k, (x0, x1) in enumerate(((-0.12, -0.11), (0.11, 0.12)))],
      explode=(0, 0, 0.2), ref='gl_housing', section='keep')
    nf = [join('np', [cyl('nps', 0.008, CZ + 0.15, CZ + 0.19, 'brass', 12, center=(0.03, 0, 0)), cyl('nph', 0.012, CZ + 0.19, CZ + 0.21, 'brass', 6, center=(0.03, 0, 0)), ball('npb', 0.008, 'brass', (0.03, 0, CZ + 0.218))]),
          join('rp', [cyl('rps', 0.012, CZ - 0.165, CZ - 0.15, 'brass', 6, center=(-0.03, 0, 0))])]
    P(m, 'nipple_relief', 'Grease Nipple (top) & Relief / Purge Plug (bottom)', 'fittings', nf, explode=(0, 0, 0.2), ref='gl_fittings', section='keep')
    lu = [hollow_pipe('lad', [(0.03, 0, CZ + 0.21), (0.03, 0, CZ + 0.28), (0.12, 0, CZ + 0.28), (0.12, 0, CZ + 0.32)], 0.008, 'brass', 8, bend=0.02),
          cyl('lcb', 0.045, CZ + 0.32, CZ + 0.5, 'glass', 32, center=(0.12, 0, 0)), cyl('lcc', 0.047, CZ + 0.5, CZ + 0.55, 'paint_red', 32, center=(0.12, 0, 0)),
          cyl('lcg', 0.042, CZ + 0.325, CZ + 0.42, 'powder', 32, center=(0.12, 0, 0))]
    P(m, 'single_point_lubricator', 'Automatic Single-Point Lubricator (gas-cell or electro-mechanical, set for 1–12 months)', 'lubricator', lu, explode=(0.2, 0, 0.3), ref='gl_lubricator', section='keep')
    pst = P(m, 'lubricator_piston', 'Lubricator Piston (advances slowly, pushing grease)', 'lubricator', cyl('lp', 0.043, CZ + 0.42, CZ + 0.435, 'paint_blue', 32, center=(0.12, 0, 0)), explode=(0.2, 0, 0.4), ref='gl_lubricator', section='keep')
    keys_loop(m, pst, lambda t: (0, 0, -0.08 * t))
    gg = [cyl('ggb', 0.03, -0.45, -0.2, 'paint_red', 24, axis='X', center=(0, 0.35, 0.03)), box('ggh', (0.12, 0.02, 0.03), (-0.14, 0.35, 0.015), 'steel_dark'), hollow_pipe('ggn', [(-0.2, 0.35, 0.03), (-0.08, 0.35, 0.05)], 0.006, 'steel', 8)]
    P(m, 'grease_gun', 'Manual Grease Gun (alternative: measured shots — count strokes)', 'tools', gg, explode=(-0.2, 0.2, 0), ref='gl_fittings', section='keep')
    m.flow('fresh_grease', [(0.12, 0.004, CZ + 0.42), (0.12, 0.004, CZ + 0.28), (0.03, 0.004, CZ + 0.28), (0.03, 0.004, CZ + 0.12), (0.0, 0.004, CZ + 0.09)], 'sand', 0.004, 0.06)
    m.flow('purged_grease', [(-0.02, 0.004, CZ - 0.09), (-0.03, 0.004, CZ - 0.15), (-0.03, 0.004, CZ - 0.2)], 'sand', 0.004, 0.05)
    _ov(m, 'temperature', [cyl('t0', 0.104, -0.035, 0.035, 'pressure_4', 64, axis='X', center=(0, 0, CZ), r_in=0.101), box('t1', (0.05, 0.005, 0.06), (0.0, 0.122, CZ - 0.12), 'pressure_7')],
        'Right amount, right interval', 'Grease = base oil held in a thickener; the bearing takes oil from it. Too little starves the bearing; too much churns and overheats it (temperature rises for '
        'hours after over-greasing). Relubricate with a quantity G ≈ 0.005 × D × B (grams; D = OD, B = width in mm) at intervals from the maker\'s charts (speed factor n·dm, temperature, '
        'contamination), with the relief plug open so old grease can escape. Never mix incompatible thickeners.')
    return m.export(out)


def _pillow(name, x, y, cz, r=0.03, mat='paint_grey'):
    return join(name, [box(name + 'b', (0.08, 0.16, 0.05), (x, y, cz - r - 0.045), mat), box(name + 'h', (0.08, 0.1, 2 * r + 0.04), (x, y, cz), mat),
                       cyl(name + 'r', r + 0.005, x - 0.04, x + 0.04, 'steel', 24, axis='X', center=(0, y, cz), r_in=r)])


# =============================================================== EQ-339 Centralized lubrication system (progressive)
def centralized_lubrication_system(out):
    m = _model('centralized_lubrication_system', 'Centralized (Progressive) Grease Lubrication System for a Conveyor Drive Station')
    rv = [cyl('rv', 0.15, 0.42, 0.95, 'glass', 48, center=(-1.2, 0, 0), r_in=0.145), cyl('rvl', 0.155, 0.95, 0.98, 'paint_grey', 48, center=(-1.2, 0, 0)),
          box('pb', (0.42, 0.32, 0.36), (-1.2, 0, 0.23), 'paint_blue'), cyl('pm', 0.07, 0.4, 0.62, 'paint_motor', 24, axis='Y', center=(-1.2, 0, 0.22)),
          box('prv', (0.05, 0.05, 0.08), (-0.96, 0.08, 0.32), 'paint_red'), box('fc', (0.06, 0.06, 0.05), (-1.43, 0, 0.3), 'brass')]
    P(m, 'pump_unit', 'Pump Unit: Transparent Reservoir, Electric Pump Element, Pressure-Relief Valve & Fill Coupling', 'pump', rv, explode=(-0.3, 0, 0), ref='cl_pump', section='keep')
    gf = lathe('gf', [(0.0, 0.42), (0.144, 0.42), (0.144, 0.85), (0.0, 0.85)], 'powder', 48, a0=0.0, a1=math.pi, center=(-1.2, 0, 0), cap_mat='powder')
    pg = P(m, 'grease_reservoir', 'Grease in the Reservoir (level falls as it is used)', 'fluid', gf, explode=(-0.3, -0.3, 0), ref='cl_pump', section='keep')
    animate_level(m, pg, 0.6, -0.12, lambda t: t)
    pd = [cyl('pds', 0.012, 0.42, 0.9, 'steel', 12, center=(-1.2, 0, 0))] + [rotate(box(f'pdb{k}', (0.24, 0.01, 0.06), (-1.2 + 0.12, 0, 0.5), 'steel'), TAU * k / 2, 'Z', (-1.2, 0, 0)) for k in range(2)]
    ppd = P(m, 'stirring_paddle', 'Stirring Paddle (feeds grease to the pump element, prevents cavities)', 'rotating_element', pd, explode=(-0.3, -0.4, 0.3), ref='cl_pump', section='keep', pivot=(-1.2, 0, 0))
    ppd.spin('Z', 1)
    dv = [box(f'ds{k}', (0.07, 0.07, 0.05), (-0.35, 0, 0.6 + 0.05 * k), 'brass') for k in range(6)] + [box('dvi', (0.07, 0.07, 0.03), (-0.35, 0, 0.56), 'steel_dark'), box('dve', (0.07, 0.07, 0.03), (-0.35, 0, 0.91), 'steel_dark')]
    P(m, 'divider_block', 'Progressive Divider Block (6 sections, pistons discharge in fixed sequence)', 'distributor', dv, explode=(0, -0.3, 0.3), ref='cl_divider')
    for k in range(6):
        pp = P(m, f'divider_piston_{k + 1}', f'Divider Piston {k + 1}', 'distributor', cyl(f'dp{k}', 0.01, -0.035, 0.035, 'chrome', 12, axis='Y', center=(-0.35, 0, 0.6 + 0.05 * k)), explode=(0, -0.4, 0.3), ref='cl_divider', section='keep')
        keys_loop(m, pp, lambda t, k=k: (0, 0.025 * smooth_pulse((t * 2 - k / 6) % 1.0, 0.03, 0.06, 0.03), 0))
    ci = P(m, 'cycle_indicator', 'Cycle Indicator Pin (moves once per complete cycle — proves all outlets delivered)', 'distributor', cyl('cip', 0.006, 0.925, 0.975, 'paint_red', 12, center=(-0.35, 0, 0)), explode=(0, 0, 0.3), ref='cl_divider', section='keep')
    keys_loop(m, ci, lambda t: (0, 0, 0.03 * smooth_pulse((2 * t) % 1.0, 0.05, 0.4, 0.05)))
    CZ = 0.35
    shafts = []
    pts = []
    for j, y in enumerate((0.0, 0.6)):
        shafts.append(cyl(f'cs{j}', 0.03, 0.15, 1.75, 'steel', 32, axis='X', center=(0, y, CZ)))
        for i, x in enumerate((0.3, 0.95, 1.6)):
            shafts.append(_pillow(f'pb{j}{i}', x, y, CZ))
            pts.append((x, y))
    P(m, 'lube_points', 'Lube Points: Six Plummer-Block Bearings on Two Conveyor Shafts', 'machine', shafts, explode=(0.3, 0, 0), ref='cl_points', section='keep')
    lines = [hollow_pipe('ml', [(-1.2, 0.16, 0.3), (-0.6, 0.16, 0.3), (-0.6, 0.0, 0.56), (-0.35, 0.0, 0.56)], 0.008, 'steel', 8, bend=0.03)]
    feeds = []
    for k, (x, y) in enumerate(pts):
        path = [(-0.31, 0.0, 0.6 + 0.05 * k), (-0.2 + 0.02 * k, 0.0, 0.6 + 0.05 * k), (-0.2 + 0.02 * k, y, 0.6 + 0.05 * k), (x, y, 0.6 + 0.05 * k), (x, y, CZ + 0.05)]
        feeds.append(path)
        lines.append(hollow_pipe(f'fl{k}', path, 0.004, 'polypropylene', 6, bend=0.02))
    P(m, 'lines', 'Main Line (high pressure) & Feed Lines to each Bearing', 'piping', lines, explode=(0, 0.2, 0.3), ref='cl_lines', section='keep')
    P(m, 'controller', 'Controller / Timer (pause–run cycles, low-level & cycle-fault alarms)', 'controls', [box('ctb', (0.2, 0.1, 0.25), (-1.65, 0, 0.55), 'paint_grey'), cyl('cts', 0.015, 0.0, 0.43, 'paint_grey', 8, center=(-1.65, 0, 0))],
      explode=(-0.3, 0, 0), ref='cl_pump', section='keep')
    for k, path in enumerate(feeds):
        add_tracers(m, f'grease_{k + 1}', f'Grease dose to bearing {k + 1}', path, n=2, radius=0.008, mat='powder')
    m.flow('main_line', [(-1.2, 0.16, 0.3), (-0.6, 0.16, 0.3), (-0.6, 0.0, 0.56), (-0.35, 0.0, 0.56)], 'sand', 0.006, 0.1)
    _ov(m, 'pressure', [box('mlz', (0.6, 0.02, 0.03), (-0.9, 0.17, 0.3), 'pressure_8'), box('dz', (0.075, 0.075, 0.32), (-0.35, 0, 0.735), 'pressure_6')] + [box(f'fz{k}', (abs(x + 0.2), 0.02, 0.02), ((x - 0.2) / 2, y, 0.62 + 0.05 * k), 'pressure_3') for k, (x, y) in enumerate(pts)],
        'One pump, many points, guaranteed sequence', 'A progressive divider has pistons that must each complete their stroke before the next can move, so every outlet receives its measured dose in turn. If any '
        'line or bearing blocks, the whole divider stops, pressure rises and the cycle indicator / pressure switch raises an alarm — a blocked point cannot go unnoticed. The controller runs short '
        'pump cycles followed by pauses, delivering small, frequent doses that suit bearings better than large manual shots.')
    return m.export(out)


# =============================================================== EQ-340 Oil mist lubrication system
def oil_mist_lubrication_system(out):
    m = _model('oil_mist_lubrication_system', 'Oil Mist Lubrication System — Mist Generator, Header, Drop Legs & Reclassifiers on Pump Bearings')
    cs = csg('cs', [box('cso', (0.5, 0.4, 1.0), (-1.6, 0, 0.5), 'paint_grey')], [box('csi', (0.46, 0.36, 0.96), (-1.6, -0.02, 0.5), 'paint_grey')], 'paint_grey')
    P(m, 'generator_console', 'Mist Generator Console (cabinet)', 'console', cs, explode=(-0.4, 0.3, 0), ref='om_generator')
    gn = [box('ort', (0.4, 0.3, 0.35), (-1.6, 0, 0.25), 'stainless'), box('olg', (0.02, 0.02, 0.25), (-1.38, -0.12, 0.25), 'glass'), cyl('mh', 0.06, 0.6, 0.9, 'stainless', 24, center=(-1.6, 0, 0)),
          box('afr', (0.08, 0.08, 0.15), (-1.75, 0, 0.7), 'brass'), box('ctl', (0.14, 0.04, 0.16), (-1.6, -0.17, 0.75), 'paint_blue_dark'), hollow_pipe('ai', [(-2.1, 0, 0.7), (-1.79, 0, 0.7)], 0.015, 'steel', 8)]
    P(m, 'mist_head', 'Oil Reservoir, Air Filter-Regulator, Venturi Mist Head & Controller', 'console', gn, explode=(-0.4, -0.3, 0), ref='om_generator', section='keep')
    hd = [hollow_pipe('hdr', [(-1.6, 0, 0.9), (-1.6, 0, 1.9), (1.6, 0, 1.95)], 0.035, 'paint_yellow', 12, bend=0.06)] + [cyl(f'hs{k}', 0.02, 0.0, 1.9, 'paint_grey', 8, center=(x, 0.1, 0)) for k, x in enumerate((-0.8, 0.6))]
    P(m, 'header', 'Distribution Header (sloped back to the console; carries ≈ 5 kPa mist)', 'piping', hd, explode=(0, 0, 0.4), ref='om_header', section='keep')
    xs = (-0.3, 0.8)
    dl = []
    for k, x in enumerate(xs):
        _pump(m, f'pump_{k + 1}', f'Process Pump {k + 1} (ball-bearing housing)', x, 0.0, 0.35, 'om_pumps', explode=(0, -0.4, 0))
        for j, dx in enumerate((0.12, 0.27)):
            dl += [hollow_pipe(f'dl{k}{j}', [(x + dx, 0, 1.94), (x + dx, 0, 2.02), (x + dx, 0.35, 2.02), (x + dx, 0.35, 0.55), (x + dx, 0.06, 0.55), (x + dx, 0.06, 0.42)], 0.008, 'stainless', 8, bend=0.02),
                   box(f'rc{k}{j}', (0.03, 0.03, 0.04), (x + dx, 0.06, 0.44), 'brass')]
        dl += [hollow_pipe(f'dr{k}', [(x + 0.2, 0.06, 0.24), (x + 0.2, 0.25, 0.24), (x + 0.2, 0.25, 0.05)], 0.008, 'stainless', 8, bend=0.02), cyl(f'cb{k}', 0.05, 0.05, 0.2, 'glass', 16, center=(x + 0.2, 0.32, 0))]
    P(m, 'drop_legs_reclassifiers', 'Drop Legs (taken from the top of the header), Reclassifier Fittings at each Bearing & Drain Bottles', 'piping', dl, explode=(0, 0.4, 0.2), ref='om_drops', section='keep')
    particles_path(m, 'mist', 'Oil mist (≈ 1–3 µm droplets) carried by air along the header', lambda i, s: (-1.6 + 3.2 * ((s + i / 14) % 1), 0.0, 1.9 + 0.05 * ((s + i / 14) % 1)), 14, mat='foam', r=0.012)
    for k, x in enumerate(xs):
        add_tracers(m, f'drop_{k + 1}', f'Mist to pump {k + 1} bearings', [(x + 0.12, 0, 1.95), (x + 0.12, 0, 2.02), (x + 0.12, 0.35, 2.02), (x + 0.12, 0.35, 0.55), (x + 0.12, 0.06, 0.55), (x + 0.12, 0.06, 0.42)], n=4, radius=0.01, mat='foam')
    m.flow('compressed_air', [(-2.2, 0, 0.7), (-1.79, 0, 0.7), (-1.6, 0, 0.75)], 'air', 0.008, 0.1)
    m.flow('mist_header', [(-1.6, 0, 0.9), (-1.6, 0, 1.9), (1.6, 0, 1.95)], 'air', 0.012, 0.3)
    _ov(m, 'pressure', [box('gz', (0.2, 0.02, 0.3), (-1.6, -0.2, 0.75), 'pressure_6'), box('hz', (3.2, 0.02, 0.05), (0.0, -0.06, 1.92), 'pressure_3')] + [box(f'bz{k}', (0.2, 0.02, 0.06), (x + 0.2, -0.04, 0.44), 'pressure_2') for k, x in enumerate(xs)],
        'A dry mist that condenses where it is needed', 'Compressed air through a venturi atomises oil into a very fine mist (≈ 1–3 µm) at a low header pressure (≈ 2–5 kPa). The mist travels without '
        'settling; at each bearing a reclassifier fitting (small orifice) makes the droplets coalesce so they wet the rolling elements. The slight positive pressure also keeps moisture and dust '
        'out of the housing. Oil use is very low and bearing life typically improves; drains and headers are sloped so condensed oil returns or is collected.')
    return m.export(out)


def _train(m, misalign=False, ref_pump='al_machines', ref_motor='al_machines', label_suffix='', frame_end=-0.12):
    """Pump + motor train on a baseplate; returns (CZ, motor part)."""
    CZ = 0.42
    P(m, 'baseplate', 'Common Baseplate (grouted)', 'structure', box('bp', (1.9, 0.6, 0.08), (0.05, 0, 0.04), 'paint_grey'), explode=(0, 0, -0.3), ref='al_base', section='keep')
    pu = [cyl('pc', 0.2, -0.75, -0.55, 'paint_blue', 48, axis='X', center=(0, 0, CZ)), cyl('pbf', 0.09, -0.55, frame_end, 'paint_blue', 32, axis='X', center=(0, 0, CZ)),
          box('pft', (0.5, 0.36, CZ - 0.18), (-0.45, 0, 0.08 + (CZ - 0.18) / 2), 'paint_blue'), nozzle('psn', (-0.75, 0, CZ), (-1, 0, 0), 0.07, 0.15), nozzle('pdn', (-0.65, 0, CZ + 0.2), (0, 0, 1), 0.06, 0.12)]
    P(m, 'pump', 'Pump (stationary machine — reference)' + label_suffix, 'machine', pu, explode=(-0.3, 0, 0), ref=ref_pump, section='keep')
    return CZ


# =============================================================== EQ-341 Shaft alignment system (dial indicators)
def shaft_alignment_system(out):
    m = _model('shaft_alignment_system', 'Shaft Alignment with Dial Indicators (Rim-and-Face) — Shims & Jacking Bolts')
    CZ = _train(m)
    def off(t):
        if t < 0.45:
            return 0.012
        if t < 0.6:
            return 0.012 * (0.5 + 0.5 * math.cos(math.pi * (t - 0.45) / 0.15))
        if t < 0.9:
            return 0.0
        return 0.012 * (0.5 - 0.5 * math.cos(math.pi * (t - 0.9) / 0.1))

    def rot(t):
        if t <= 0.4:
            return -math.pi * t / 0.4
        if t <= 0.65:
            return -math.pi
        return -math.pi + math.pi * (t - 0.65) / 0.35
    mo = [_motor('mt', 0.1, 0.6, CZ, 0.16, foot_z=0.1)] + [box(f'mfp{s}', (0.12, 0.08, 0.02), (x, s * 0.11, 0.11), 'paint_motor') for s in (-1, 1) for x in (0.18, 0.52)]
    pmo = P(m, 'motor', 'Motor (movable machine — shimmed and moved into line)', 'machine', mo, explode=(0.3, 0, 0), ref='al_machines', section='keep')
    keys_loop(m, pmo, lambda t: (0, 0, off(t)))
    sh = [P(m, 'pump_shaft_hub', 'Pump Shaft & Coupling Hub (turning with brackets)', 'rotating_element', [cyl('psh', 0.03, -0.15, -0.012, 'steel', 32, axis='X', center=(0, 0, CZ)), cyl('ph', 0.075, -0.06, -0.012, 'steel', 48, axis='X', center=(0, 0, CZ))],
            explode=(-0.2, -0.3, 0), ref='al_coupling', section='keep', pivot=(0, 0, CZ))]
    for ms in sh[0].meshes:
        axis_rot_keys(m, ms, (1, 0, 0), rot)
    mh = [cyl('msh', 0.03, 0.012, 0.15, 'steel', 32, axis='X', center=(0, 0, CZ)), cyl('mh', 0.075, 0.012, 0.06, 'steel', 48, axis='X', center=(0, 0, CZ))]
    pmh = P(m, 'motor_shaft_hub', 'Motor Shaft & Coupling Hub', 'rotating_element', mh, explode=(0.2, -0.3, 0), ref='al_coupling', section='keep', pivot=(0, 0, CZ))
    keys_loop(m, pmh, lambda t: (0, 0, off(t)))
    br = [box('bc', (0.04, 0.05, 0.07), (-0.035, 0, CZ + 0.1), 'paint_yellow'), cyl('bb', 0.01, -0.04, 0.1, 'steel', 12, axis='X', center=(0, 0, CZ + 0.13)),
          join('di1', [cyl('d1b', 0.035, -0.035, -0.01, 'chrome', 32, axis='Y', center=(0.04, 0, CZ + 0.165)), cyl('d1f', 0.03, -0.037, -0.035, 'ptfe', 32, axis='Y', center=(0.04, 0, CZ + 0.165)),
                       cyl('d1p', 0.004, CZ + 0.076, CZ + 0.13, 'steel', 8, center=(0.04, 0, 0))]),
          join('di2', [cyl('d2b', 0.035, -0.035, -0.01, 'chrome', 32, axis='Y', center=(0.1, 0, CZ + 0.06)), cyl('d2f', 0.03, -0.037, -0.035, 'ptfe', 32, axis='Y', center=(0.1, 0, CZ + 0.06)),
                       cyl('d2p', 0.004, 0.062, 0.1, 'steel', 8, axis='X', center=(0, 0, CZ + 0.06))])]
    pbr = P(m, 'indicator_bracket', 'Indicator Bracket with Rim (radial) & Face (axial) Dial Indicators', 'tools', br, explode=(0, -0.3, 0.3), ref='al_indicators', section='keep', pivot=(0, 0, CZ))
    for ms in pbr.meshes + pmh.meshes:
        axis_rot_keys(m, ms, (1, 0, 0), rot)
    shim = [box(f'sm{s}{x}', (0.13, 0.09, 0.008), (x, s * 0.11, 0.084 + 0.009 * j), 'brass') for s in (-1, 1) for x in (0.18, 0.52) for j in range(2)]
    jb = [join(f'jb{k}', [box(f'jbb{k}', (0.04, 0.04, 0.06), (x, s * 0.2, 0.11), 'paint_grey'), cyl(f'jbs{k}', 0.008, s * 0.14, s * 0.2, 'steel', 8, axis='Y', center=(x, 0, 0.12)) if s > 0 else
                          cyl(f'jbs{k}', 0.008, -0.2, -0.14, 'steel', 8, axis='Y', center=(x, 0, 0.12))]) for k, (x, s) in enumerate(((0.18, 1), (0.52, 1), (0.18, -1), (0.52, -1)))]
    P(m, 'shims_jacking_bolts', 'Precision Shims (vertical correction) & Jacking Bolts (horizontal moves)', 'tools', shim + jb, explode=(0, 0.3, -0.1), ref='al_shims', section='keep')
    m.flow('readings', [(0.05, 0.03, CZ + 0.15), (0.05, 0.03, CZ + 0.3)], 'electric', 0.004, 0.05)
    _ov(m, 'pressure', [cyl('pa', 0.004, -0.8, 0.0, 'pressure_2', 8, axis='X', center=(0, 0.25, CZ)), cyl('ma', 0.004, 0.0, 0.7, 'pressure_8', 8, axis='X', center=(0, 0.25, CZ + 0.012))],
        'Offset and angularity — measure, then correct', 'Two shafts are aligned when their rotational centrelines are collinear at running temperature. Misalignment has two parts: offset (parallel '
        'displacement) and angularity (slope), each vertical and horizontal. With the bracket on one hub, rotating both shafts together and reading the rim (radial) and face (axial) indicators at '
        '12, 3, 6 and 9 o\'clock gives offset (½ the rim reading change) and angularity (face difference ÷ diameter). Correct vertical errors with shims under the movable machine\'s feet, horizontal '
        'with jacking bolts; check soft foot first. Typical tolerances at 1500 rpm ≈ 0.05–0.08 mm offset (follow site / maker tables).')
    return m.export(out)


# =============================================================== EQ-345 Laser alignment equipment
def laser_alignment_equipment(out):
    m = _model('laser_alignment_equipment', 'Laser Shaft Alignment Equipment — Transmitter / Detector Units, Chain Brackets & Display')
    CZ = _train(m, frame_end=-0.32)
    mo = [_motor('mt', 0.32, 0.82, CZ, 0.16, foot_z=0.1)]
    P(m, 'motor', 'Motor (movable machine)', 'machine', mo, explode=(0.3, 0, 0), ref='al_machines', section='keep')
    ang = lambda t: -math.pi / 2 + math.pi * (0.5 - 0.5 * math.cos(TAU * t))
    for nm, x, label in (('stationary', -0.3, 'S-Unit on Pump Shaft (laser + detector)'), ('movable', 0.3, 'M-Unit on Motor Shaft (laser + detector)')):
        xs = -0.2 if nm == 'stationary' else 0.2
        u = [cyl(nm + 'sh', 0.03, (-0.4 if nm == 'stationary' else 0.012), (-0.012 if nm == 'stationary' else 0.4), 'steel', 32, axis='X', center=(0, 0, CZ)),
             cyl(nm + 'hb', 0.075, (-0.06 if nm == 'stationary' else 0.012), (-0.012 if nm == 'stationary' else 0.06), 'steel', 48, axis='X', center=(0, 0, CZ)),
             _torus(nm + 'ch', 0.034, 0.004, xs, 'steel_dark', cz=CZ), box(nm + 'vb', (0.04, 0.06, 0.05), (xs, 0, CZ + 0.05), 'aluminium'),
             cyl(nm + 'rd1', 0.005, CZ + 0.07, CZ + 0.2, 'chrome', 8, center=(xs, -0.015, 0)), cyl(nm + 'rd2', 0.005, CZ + 0.07, CZ + 0.2, 'chrome', 8, center=(xs, 0.015, 0)),
             box(nm + 'un', (0.05, 0.08, 0.09), (xs, 0, CZ + 0.24), 'paint_yellow' if nm == 'stationary' else 'paint_blue'), box(nm + 'ap', (0.006, 0.03, 0.03), (xs + (0.026 if nm == 'stationary' else -0.026), 0, CZ + 0.25), 'glass')]
        p = P(m, nm + '_unit', label + ' — shaft, hub, chain bracket, rods', 'tools', u, explode=((-0.3 if nm == 'stationary' else 0.3), -0.3, 0.2), ref='la_units', section='keep', pivot=(0, 0, CZ))
        for ms in p.meshes:
            axis_rot_keys(m, ms, (1, 0, 0), ang)
    bm = [cyl('lb', 0.003, -0.174, 0.174, 'flame', 8, axis='X', center=(0, 0, CZ + 0.25))]
    pbm = P(m, 'laser_beams', 'Laser Beams between the Units (rotate with the shafts)', 'tools', bm, explode=(0, -0.3, 0.3), ref='la_units', section='keep', pivot=(0, 0, CZ))
    for ms in pbm.meshes:
        axis_rot_keys(m, ms, (1, 0, 0), ang)
    dp = [box('dpb', (0.25, 0.04, 0.18), (1.15, -0.45, 0.7), 'paint_grey'), box('dps', (0.21, 0.005, 0.14), (1.15, -0.472, 0.7), 'pcb'), cyl('dpp', 0.015, 0.0, 0.61, 'paint_grey', 8, center=(1.15, -0.45, 0)),
          box('dpf', (0.3, 0.3, 0.02), (1.15, -0.45, 0.01), 'paint_grey')]
    P(m, 'display_unit', 'Display Unit / Tablet (wireless; shows offset & angularity, foot corrections)', 'tools', dp, explode=(0, -0.3, 0), ref='la_display', section='keep')
    for sname, xs in (('s', -0.2), ('m', 0.2)):
        add_tracers(m, 'radio_' + sname, 'Wireless data to the display', [(xs, -0.05, CZ + 0.3), (0.6, -0.3, 0.85), (1.15, -0.44, 0.72)], n=3, radius=0.006, mat='electric')
    m.flow('beam', [(-0.17, 0.004, CZ + 0.25), (0.17, 0.004, CZ + 0.25)], 'electric', 0.003, 0.05)
    _ov(m, 'pressure', [cyl('tz', 0.03, 0.172, 0.176, 'pressure_8', 24, axis='X', center=(0, 0, CZ + 0.25), r_in=0.02), cyl('tz2', 0.02, 0.172, 0.176, 'pressure_2', 24, axis='X', center=(0, 0, CZ + 0.25))],
        'The beam spot reveals misalignment', 'Each unit projects a laser onto the opposite unit\'s position detector (PSD). As both shafts are turned together through at least ≈ 70–140° (e.g. 9-12-3 o\'clock), '
        'the spot traces a path whose movement gives offset and angularity in both planes. The display calculates shim values and horizontal moves for each motor foot and can update live while '
        'moving. Advantages over dial indicators: no bracket sag, higher resolution (≈ 1 µm), faster. Check soft foot first and apply thermal-growth targets.')
    return m.export(out)


# =============================================================== EQ-342 Dynamic balancing machine
def dynamic_balancing_machine(out):
    m = _model('dynamic_balancing_machine', 'Horizontal Dynamic Balancing Machine (Soft-Bearing) with Fan Rotor — Two-Plane Balancing')
    CZ = 0.65
    P(m, 'bed', 'Machine Bed', 'structure', [box('bd', (2.2, 0.5, 0.3), (0, 0, 0.15), 'paint_grey'), box('rail', (2.0, 0.3, 0.04), (0, 0, 0.32), 'steel')], explode=(0, 0, -0.3), ref='db_bed', section='keep')
    for k, x in enumerate((-0.55, 0.55)):
        ped = [box(f'pd{k}', (0.16, 0.3, CZ - 0.42), (x, 0, 0.34 + (CZ - 0.42) / 2 - 0.0), 'paint_blue'), box(f'pt{k}', (0.16, 0.2, 0.06), (x, 0, CZ - 0.085), 'paint_blue')]
        ped += [cyl(f'rl{k}{s}', 0.03, x - 0.04, x + 0.04, 'chrome', 24, axis='X', center=(0, s * 0.035, CZ - 0.06)) for s in (-1, 1)]
        ped += [join(f'vp{k}', [cyl(f'vpb{k}', 0.02, 0.17, 0.22, 'paint_blue_dark', 16, axis='Y', center=(x, 0, CZ - 0.2)), hollow_pipe(f'vpc{k}', [(x, 0.22, CZ - 0.2), (x, 0.3, CZ - 0.3), (x, 0.3, 0.32)], 0.004, 'rubber', 6, bend=0.02)])]
        pp = P(m, f'pedestal_{k + 1}', f'Pedestal {k + 1}: Roller Carriage on Spring Suspension & Vibration Pick-up', 'pedestal', ped, explode=(0, 0.4, 0), ref='db_pedestals', section='keep')
        keys_loop(m, pp, lambda t, k=k: (0, 0.004 * math.sin(TAU * 3 * t + (0.0 if k == 0 else 1.2)), 0))
    ro = [cyl('rs', 0.03, -0.75, 0.75, 'steel', 32, axis='X', center=(0, 0, CZ)), cyl('rd', 0.33, -0.12, -0.1, 'steel', 96, axis='X', center=(0, 0, CZ)), cyl('rd2', 0.33, 0.1, 0.12, 'steel', 96, axis='X', center=(0, 0, CZ), r_in=0.12),
          cyl('rh', 0.07, -0.15, 0.15, 'steel', 48, axis='X', center=(0, 0, CZ))]
    ro += [rotate(box(f'rb{k}', (0.2, 0.012, 0.16), (0.0, 0, CZ + 0.24), 'steel'), TAU * k / 10, 'X', (0, 0, CZ)) for k in range(10)]
    ro += [box('hs', (0.03, 0.03, 0.03), (-0.11, 0, CZ + 0.29), 'paint_red'), box('cw', (0.03, 0.03, 0.03), (0.11, 0, CZ - 0.29), 'paint_green'), box('rt', (0.02, 0.012, 0.004), (0.7, 0, CZ + 0.031), 'chrome')]
    pr = P(m, 'rotor', 'Fan Rotor on Arbor: Heavy Spot (red) & Correction Weight (green), Reflective Reference Mark', 'rotating_element', ro, explode=(0, -0.5, 0.3), ref='db_rotor', section='keep', pivot=(0, 0, CZ))
    pr.spin('X', 3)
    dr = [box('dh', (0.3, 0.3, 0.3), (-1.0, 0, 0.62), 'paint_grey'), cyl('dm', 0.1, -1.35, -1.15, 'paint_motor', 32, axis='X', center=(0, 0, 0.62))]
    P(m, 'drive_head', 'Drive Head (motor, end-drive)', 'drive', dr, explode=(-0.4, 0, 0), ref='db_drive', section='keep')
    ds = [cyl('dsh', 0.02, -0.85, -0.75, 'steel', 16, axis='X', center=(0, 0, CZ)), cyl('duj', 0.035, -0.8, -0.77, 'steel_dark', 16, axis='X', center=(0, 0, CZ))]
    pds = P(m, 'drive_shaft', 'Universal-Joint Drive Shaft', 'rotating_element', ds, explode=(-0.3, -0.2, 0), ref='db_drive', section='keep', pivot=(0, 0, CZ))
    pds.spin('X', 3)
    cs = [box('cn', (0.5, 0.35, 0.9), (0.2, 1.1, 0.45), 'paint_grey'), box('scr', (0.36, 0.01, 0.26), (0.2, 0.92, 0.72), 'pcb'), box('kb', (0.4, 0.2, 0.03), (0.2, 0.88, 0.5), 'steel_dark'),
          join('ps', [box('psb', (0.04, 0.04, 0.05), (0.7, 0.3, CZ + 0.12), 'paint_blue_dark'), cyl('pss', 0.012, 0.32, CZ + 0.1, 'paint_grey', 8, center=(0.7, 0.3, 0))])]
    P(m, 'console_sensors', 'Measuring Console (amount & angle per plane) & Photo-Cell Reference Sensor', 'controls', cs, explode=(0, 0.4, 0), ref='db_console', section='keep')
    add_tracers(m, 'signals', 'Pick-up and reference signals to the console', [(0.55, 0.3, 0.33), (0.4, 0.5, 0.32), (0.2, 0.8, 0.35), (0.2, 0.93, 0.6)], n=3, radius=0.008, mat='electric')
    m.flow('drive', [(-1.35, 0, 0.62), (-0.85, 0, CZ), (0.0, 0, CZ)], 'power', 0.008, 0.1)
    _ov(m, 'pressure', [cyl('pl1', 0.335, -0.125, -0.095, 'pressure_7', 96, axis='X', center=(0, 0, CZ), r_in=0.3), cyl('pl2', 0.335, 0.095, 0.125, 'pressure_7', 96, axis='X', center=(0, 0, CZ), r_in=0.3)],
        'Two correction planes cancel static and couple unbalance', 'An unbalanced rotor\'s heavy spot creates a rotating centrifugal force F = m·e·ω², which shakes the soft pedestals at once per revolution. '
        'The pick-ups measure amplitude; the photo-cell gives the phase, so the console calculates the correction mass and angle for each of two planes (dynamic unbalance = static + couple). '
        'Residual unbalance is checked against the required grade, e.g. ISO 21940-11 G6.3 for fans and pump impellers or G2.5 for turbine rotors: U_per = G·m / ω (g·mm).')
    return m.export(out)


# =============================================================== EQ-343 Vibration monitoring system
def vibration_monitoring_system(out):
    m = _model('vibration_monitoring_system', 'Vibration Monitoring System — Accelerometers, Proximity Probes, Keyphasor & Monitor Rack (API 670 style)')
    CZ = _train(m, label_suffix=' with bearing housing')
    P(m, 'motor', 'Motor', 'machine', [_motor('mt', 0.1, 0.6, CZ, 0.16, foot_z=0.1)], explode=(0.3, 0, 0), ref='al_machines', section='keep')
    sh = [cyl('ps', 0.03, -0.12, 0.12, 'steel', 32, axis='X', center=(0, 0, CZ)), cyl('cp', 0.07, -0.05, 0.05, 'steel', 48, axis='X', center=(0, 0, CZ), r_in=0.03), box('kn', (0.02, 0.012, 0.008), (-0.09, 0, CZ + 0.031), 'steel_dark')]
    ps = P(m, 'shaft_coupling', 'Shaft & Coupling with Keyphasor Notch (once-per-turn reference)', 'rotating_element', sh, explode=(0, -0.3, 0.2), ref='vm_shaft', section='keep', pivot=(0, 0, CZ))
    ps.spin('X', 3)
    acc = []
    for k, (x, nm) in enumerate(((-0.5, 'P-NDE'), (-0.17, 'P-DE'), (0.13, 'M-DE'), (0.57, 'M-NDE'))):
        r = 0.09 if x < 0 else 0.16
        acc += [join(f'ah{k}', [cyl(f'ahb{k}', 0.015, -r - 0.04, -r, 'stainless', 6, axis='Y', center=(x, 0, CZ)), cyl(f'ahc{k}', 0.006, -r - 0.07, -r - 0.04, 'rubber', 8, axis='Y', center=(x, 0, CZ))]),
                join(f'av{k}', [cyl(f'avb{k}', 0.015, CZ + r, CZ + r + 0.04, 'stainless', 6, center=(x, 0, 0)), cyl(f'avc{k}', 0.006, CZ + r + 0.04, CZ + r + 0.07, 'rubber', 8, center=(x, 0, 0))])]
    acc += [cyl('aax', 0.015, 0.66, 0.7, 'stainless', 6, axis='X', center=(0, 0, CZ))]
    P(m, 'accelerometers', 'Accelerometers / Velocity Transducers at each Bearing (H, V and A directions)', 'sensors', acc, explode=(0, -0.3, 0.3), ref='vm_sensors', section='keep')
    pr = []
    for k, a in enumerate((math.radians(45), math.radians(135))):
        d = Vector((0, math.cos(a), math.sin(a)))
        b = Vector((-0.09, 0, CZ)) + d * 0.032
        e = Vector((-0.09, 0, CZ)) + d * 0.12
        pr.append(sweep_tube(f'xp{k}', [tuple(b), tuple(e)], 0.008, 'stainless', 12))
    pr.append(sweep_tube('kp', [(-0.09, 0, CZ + 0.035), (-0.09, 0, CZ + 0.13)], 0.008, 'paint_yellow', 12))
    P(m, 'proximity_probes', 'X–Y Proximity Probes (shaft relative displacement) & Keyphasor Probe', 'sensors', pr, explode=(0, -0.2, 0.4), ref='vm_probes', section='keep')
    rk = [box('rk', (0.5, 0.4, 1.4), (0.3, 1.2, 0.7), 'paint_grey'), box('rkd', (0.4, 0.01, 0.25), (0.3, 0.995, 1.15), 'pcb')] + [box(f'md{k}', (0.06, 0.02, 0.4), (0.12 + 0.07 * k, 0.995, 0.7), 'steel_dark') for k in range(6)]
    rk += [box(f'led{k}', (0.02, 0.01, 0.02), (0.12 + 0.07 * k, 0.985, 0.95), 'pressure_2' if k != 3 else 'pressure_8') for k in range(6)]
    rk += [box('jb', (0.2, 0.1, 0.2), (0.0, 0.45, 0.3), 'paint_grey'), hollow_pipe('mc', [(0.0, 0.5, 0.3), (0.0, 0.9, 0.3), (0.3, 1.0, 0.3)], 0.015, 'rubber', 8, bend=0.03)]
    P(m, 'monitor_rack', 'Junction Box, Cable & Monitor Rack (alarm / trip relays to DCS & shutdown system)', 'controls', rk, explode=(0, 0.4, 0), ref='vm_rack', section='keep')
    add_tracers(m, 'signals', 'Vibration signals to the monitor', [(-0.17, 0.0, CZ + 0.16), (-0.1, 0.3, 0.35), (0.0, 0.45, 0.3), (0.0, 0.9, 0.3), (0.3, 1.0, 0.5)], n=5, radius=0.008, mat='electric')
    m.flow('signal_cable', [(-0.17, 0.0, CZ + 0.16), (0.0, 0.45, 0.32), (0.0, 0.9, 0.3), (0.3, 1.0, 0.5)], 'electric', 0.005, 0.08)
    _ov(m, 'pressure', [cyl(f'vz{k}', (0.1 if x < 0 else 0.17), x - 0.03, x + 0.03, f'pressure_{lev}', 48, axis='X', center=(0, 0, CZ), r_in=(0.095 if x < 0 else 0.165)) for k, (x, lev) in enumerate(((-0.5, 2), (-0.17, 6), (0.13, 4), (0.57, 2)))],
        'Severity zones guide action', 'Casing vibration (velocity, mm/s RMS, 10–1000 Hz) is judged against ISO 20816 zones A (new) → B (unrestricted) → C (limited time) → D (damage likely); shaft '
        'displacement from proximity probes (µm pk-pk) is used on oil-film bearing machines. Trends and spectra reveal causes: 1× running speed — unbalance; 2× and axial — misalignment; bearing '
        'defect frequencies (BPFO / BPFI) — rolling bearing damage; sub-synchronous — oil whirl. The rack raises alerts and trips per API 670 logic (voting, delays).')
    return m.export(out)


# =============================================================== EQ-344 Online condition monitoring system
def online_condition_monitoring_system(out):
    m = _model('online_condition_monitoring_system', 'Online Condition Monitoring System — Wireless Sensors on a Fan, Pump & Gearbox, Gateway, Server & Dashboard')
    fh = csg('fh', [cyl('fho', 0.45, -0.25, 0.25, 'paint_green', 64, axis='Y', center=(-1.6, 0, 0.6))], [cyl('fhi', 0.42, -0.22, 0.22, 'paint_green', 64, axis='Y', center=(-1.6, 0, 0.6))], 'paint_green')
    P(m, 'fan', 'Process Fan (housing)', 'machine', [fh, box('fb', (0.9, 0.6, 0.15), (-1.6, 0, 0.075), 'paint_grey'), box('fmb', (0.12, 0.12, 0.12), (-1.6, 0.3, 0.6), 'paint_grey'), cyl('fmm', 0.11, 0.36, 0.7, 'paint_motor', 32, axis='Y', center=(-1.6, 0, 0.6))],
      explode=(-0.3, 0, 0), ref='ocm_machines')
    _fan_rotor(m, 'fan_rotor', 'Fan Impeller', (-1.6, 0, 0.6), 'Y', 0.36, 'ocm_machines', revs=3)
    _pump(m, 'pump', 'Process Pump & Motor', -0.2, 0.0, 0.35, 'ocm_machines', explode=(0, -0.4, 0))
    gb = [box('gbx', (0.45, 0.4, 0.4), (1.2, 0, 0.35), 'paint_blue'), cyl('gi', 0.03, 0.75, 0.97, 'steel', 16, axis='X', center=(0, 0, 0.42)), cyl('go', 0.05, 1.42, 1.7, 'steel', 16, axis='X', center=(0, 0, 0.3))]
    P(m, 'gearbox', 'Gearbox', 'machine', gb, explode=(0.3, 0, 0), ref='ocm_machines', section='keep')
    sens = []
    spots = [(-1.6, 0.27, 0.6), (-1.6, 0.0, 1.07), (-0.05, 0.0, 0.47), (0.25, 0.0, 0.47), (1.1, 0.0, 0.57), (1.3, 0.0, 0.57)]
    for k, (x, y, z) in enumerate(spots):
        sens += [cyl(f'sp{k}', 0.022, z, z + 0.05, 'paint_orange', 6, center=(x, y, 0)), cyl(f'sa{k}', 0.003, z + 0.05, z + 0.12, 'steel_dark', 6, center=(x, y, 0))]
    sens += [join('oq', [box('oqb', (0.06, 0.06, 0.08), (1.47, 0.15, 0.2), 'paint_blue_dark'), hollow_pipe('oqp', [(1.42, 0.15, 0.2), (1.38, 0.15, 0.2)], 0.008, 'steel', 6)])]
    sens += [join('ir', [box('irb', (0.08, 0.06, 0.06), (0.4, -0.7, 1.0), 'paint_grey'), cyl('irs', 0.012, 0.0, 0.97, 'paint_grey', 8, center=(0.4, -0.7, 0))])]
    P(m, 'wireless_sensors', 'Wireless Vibration / Temperature Sensors, Gearbox Oil-Quality Sensor & Fixed Thermal Camera', 'sensors', sens, explode=(0, -0.3, 0.3), ref='ocm_sensors', section='keep')
    gw = [cyl('gp', 0.03, 0.0, 2.0, 'paint_grey', 12, center=(0.2, 1.1, 0)), box('gwb', (0.2, 0.1, 0.25), (0.2, 1.05, 1.7), 'paint_grey'), cyl('gwa', 0.006, 1.82, 2.2, 'steel_dark', 6, center=(0.2, 1.05, 0))]
    P(m, 'gateway', 'Wireless Gateway (mesh network: WirelessHART / ISA100 / LoRaWAN, etc.)', 'network', gw, explode=(0, 0.3, 0.3), ref='ocm_network', section='keep')
    sv = [box('svr', (0.5, 0.5, 1.2), (2.3, 1.1, 0.6), 'paint_grey'), box('svs', (0.6, 0.02, 0.35), (2.3, 0.82, 1.05), 'pcb'), box('dsk', (0.6, 0.3, 0.04), (2.3, 0.6, 0.75), 'paint_grey'),
          box('mon', (0.5, 0.03, 0.3), (2.3, 0.5, 0.95), 'pcb'), hollow_pipe('net', [(0.2, 1.05, 1.6), (0.2, 1.05, 0.05), (2.3, 1.05, 0.05), (2.3, 1.05, 0.1)], 0.012, 'paint_blue', 8, bend=0.05)]
    P(m, 'server_dashboard', 'Edge Server / Historian, Analytics & Dashboard Screen (alerts to maintenance planning)', 'network', sv, explode=(0.4, 0.3, 0), ref='ocm_server', section='keep')
    for k, (x, y, z) in enumerate(spots):
        add_tracers(m, f'data_{k + 1}', f'Data packets from sensor {k + 1}', [(x, y, z + 0.12), ((x + 0.2) / 2, (y + 1.05) / 2, 2.0), (0.2, 1.05, 2.15)], n=2, radius=0.012, mat='electric')
    add_tracers(m, 'backhaul', 'Gateway to server', [(0.2, 1.05, 1.6), (0.2, 1.05, 0.05), (2.3, 1.05, 0.05), (2.3, 1.05, 0.2)], n=4, radius=0.014, mat='electric')
    m.flow('network', [(0.2, 1.05, 1.6), (0.2, 1.05, 0.05), (2.3, 1.05, 0.05), (2.3, 1.05, 0.2)], 'electric', 0.006, 0.15)
    _ov(m, 'pressure', [cyl('hf', 0.5, 0.0, 0.03, 'pressure_2', 48, center=(-1.6, 0, 0)), cyl('hp', 0.45, 0.0, 0.03, 'pressure_6', 48, center=(0.05, 0, 0)), cyl('hg', 0.4, 0.0, 0.03, 'pressure_9', 48, center=(1.2, 0, 0))],
        'Health status at a glance: OK – warning – alarm', 'Permanently installed sensors send vibration, temperature and oil-condition data at intervals (seconds to hours) through a gateway to a historian '
        'and analytics. Trends against baselines and alarm limits flag developing faults weeks ahead (P–F interval), so repairs are planned instead of reacting to breakdowns. Here the fan is healthy '
        '(green), the pump shows a rising trend (amber), and the gearbox oil sensor reports wear debris (red). Wireless sensors trade data rate / battery life against detail; critical machines '
        'still use wired protection systems (API 670).')
    return m.export(out)


# ===================================================================== metadata
_MOT = _std(('IEC 60034-1', 'Rotating electrical machines — rating and performance', 'Ratings, insulation classes.'), ('IEEE 43', 'Testing insulation resistance of electric machinery', 'IR / PI tests.'))
_LUB = _std(('API 614', 'Lubrication, shaft-sealing and oil-control systems and auxiliaries', 'Lube oil systems.'), ('ISO 4406', 'Hydraulic fluid power — solid particle contamination code', 'Oil cleanliness.'))
_ALN = _std(('ANSI/ASA S2.75', 'Shaft alignment methodology', 'Alignment practice (to be verified).'), ('API 686', 'Recommended practice for machinery installation', 'Alignment & soft foot.'))
_VIB = _std(('ISO 20816-1/-3', 'Mechanical vibration — measurement and evaluation of machine vibration', 'Severity zones.'), ('API 670', 'Machinery protection systems', 'Probes, monitors, trips.'))
_AL = _comp(('al_base', 'Support both machines.', 'Grouted baseplate.', 'Steel.'), ('al_machines', 'Driven and driver machines.', 'Pump and motor.', '—', '—', ['Soft foot', 'Pipe strain'], ['Feeler gauge / dial at each foot']))

META = {
    'rotor': {'summary': 'An induction-motor rotor is a laminated steel core carrying a squirrel cage of conducting bars joined by end rings, on a shaft with bearing journals and a cooling fan. The stator\'s rotating field induces currents in the bars that produce torque.',
              'classification': {'family': 'Rotating components', 'type': 'Squirrel-cage rotor'}, 'model_configuration': {'animation': 'Rotor turns on V-block stands; field lines shown in overlay'},
              'standards': _MOT, 'references': ['IEC 60034'],
              'components': _comp(('rot_core', 'Carries flux; holds bars.', 'Laminated core with skewed bars.', 'Electrical steel; copper/aluminium bars.', 'Slip ≈ 0.5–5 %.', ['Broken bars', 'Core hot spots'], ['Current signature analysis']),
                                  ('rot_rings', 'Short-circuit bars; fins; balance.', 'End rings, fins, balance weights.', 'Aluminium/copper.', '—', ['Cracked end ring'], ['Visual, growler test']),
                                  ('rot_shaft', 'Transmit torque; carry fan.', 'Shaft with journals and keyway.', 'Steel.', '—', ['Journal wear'], ['Runout']), ('rot_stands', 'Support for inspection.', 'V-blocks / rollers.', '—'))},
    'stator': {'summary': 'An induction-motor stator is the stationary part: a frame holding a laminated core whose slots carry three-phase windings. Three-phase current in the windings produces a magnetic field that rotates at synchronous speed.',
               'classification': {'family': 'Rotating components', 'type': 'Three-phase stator'}, 'model_configuration': {'animation': 'N/S marker shows the rotating field'},
               'standards': _MOT, 'references': ['IEC 60034'],
               'components': _comp(('sta_frame', 'Supports core; cools.', 'Cast frame with ribs and feet.', 'Cast iron/aluminium.'), ('sta_core', 'Carries flux.', 'Laminated slotted core.', 'Electrical steel.', '—', ['Core faults (shorted laminations)'], ['Loop / EL CID test']),
                                   ('sta_windings', 'Create the rotating field.', 'Coils in slots, end windings.', 'Copper, class F/H insulation.', '—', ['Insulation breakdown', 'Contamination', 'Overheating'], ['IR / PI, surge test']),
                                   ('sta_terminal', 'Supply connection.', 'Terminal box and leads.', '—'), ('sta_field', 'Teaching marker.', 'Rotating N/S marker.', '—'))},
    'gear_assembly': {'summary': 'A gear assembly transmits rotation and torque between shafts through meshing teeth. This spur train has a driving pinion, an idler that reverses direction, and a driven gear that turns slower with more torque.',
                      'classification': {'family': 'Power transmission', 'type': 'Spur gear train with idler'}, 'model_configuration': {'animation': 'Pinion, idler and gear turn at 3 : 2 : 1 speed'},
                      'standards': _std(('ISO 6336', 'Calculation of load capacity of spur and helical gears', 'Rating.'), ('AGMA 2001', 'Fundamental rating factors for involute spur and helical gear teeth', 'Rating.')), 'references': ['Maitra — Handbook of Gear Design'],
                      'components': _comp(('ga_gears', 'Transmit motion and torque.', 'Involute spur gears on keyed shafts.', 'Case-hardened alloy steel.', '—', ['Pitting', 'Scuffing', 'Tooth breakage'], ['Contact pattern, backlash, vibration']),
                                          ('ga_bearings', 'Support shafts.', 'Rolling bearings.', 'Bearing steel.'), ('ga_frame', 'Locate shafts.', 'Bearing plates on a base.', 'Steel.'))},
    'lubricating_oil_skid': {'summary': 'A lubricating oil skid supplies clean, cool oil at controlled pressure to the bearings (and often seals and controls) of a turbine, compressor or large pump, with main and standby pumps, coolers, duplex filters and a reservoir.',
                             'classification': {'family': 'Lubrication', 'type': 'Pressure-fed lube oil console'}, 'model_configuration': {'animation': 'Pumps run; oil circulates; level varies'},
                             'standards': _LUB, 'references': ['API 614'],
                             'components': _comp(('lo_reservoir', 'Store and de-aerate oil.', 'Stainless reservoir with heater and baffles.', 'Stainless steel.', 'Retention ≈ 3–8 min.', ['Water ingress', 'Foaming'], ['Oil analysis']),
                                                 ('lo_pumps', 'Deliver oil.', 'Main + auto-start standby pumps.', '—', '—', ['Wear, cavitation'], ['Auto-start test']),
                                                 ('lo_coolers', 'Remove heat.', 'Twin coolers with transfer valve.', 'Steel/copper alloy.'), ('lo_filters', 'Clean oil.', 'Duplex filters ≈ 10 µm, transfer valve, ΔP.', 'Steel.', '—', ['High ΔP'], ['Change elements on ΔP']),
                                                 ('lo_controls', 'Control pressure; protect.', 'PCV, accumulator, gauges, transmitters, piping.', 'Stainless.', '≈ 1–2.5 bar(g) at bearings.', ['PCV hunting'], ['Trip test']))},
    'grease_lubrication_system': {'summary': 'Grease lubrication feeds a bearing with grease — oil held in a thickener — through a grease nipple by hand or by an automatic single-point lubricator, with a relief plug so used grease can escape.',
                                  'classification': {'family': 'Lubrication', 'type': 'Grease-lubricated plummer block with single-point lubricator'}, 'model_configuration': {'animation': 'Rollers turn; lubricator piston advances'},
                                  'standards': _std(('ISO 6743-9 / NLGI grades', 'Lubricants — greases classification', 'Grease selection.'),), 'references': ['SKF Bearing Maintenance Handbook'],
                                  'components': _comp(('gl_housing', 'Hold bearing and grease.', 'Split plummer block with seals.', 'Cast iron.'), ('gl_bearing', 'Carry load.', 'Spherical roller bearing.', 'Bearing steel.', '—', ['Lubricant starvation', 'Over-greasing heat'], ['Temperature, ultrasound']),
                                                      ('gl_shaft', 'Rotating shaft.', 'Shaft.', 'Steel.'), ('gl_grease', 'Lubricate and seal.', 'Grease fill.', 'Lithium-complex / polyurea etc.', '—', ['Hardening, mixing incompatible greases'], ['Purged grease condition']),
                                                      ('gl_fittings', 'Supply and relief.', 'Nipple, relief plug, grease gun.', 'Brass/steel.'), ('gl_lubricator', 'Automatic dosing.', 'Single-point lubricator canister.', 'Plastic/steel.', '1–12 month settings.', ['Empty / blocked'], ['Check level indicator']))},
    'centralized_lubrication_system': {'summary': 'A centralized (progressive) lubrication system uses one pump unit and divider blocks to feed measured amounts of grease automatically to many bearings, in a fixed sequence with monitoring of every cycle.',
                                       'classification': {'family': 'Lubrication', 'type': 'Progressive grease system'}, 'model_configuration': {'animation': 'Paddle turns; divider pistons stroke in sequence; doses travel to bearings'},
                                       'standards': _std(('Maker standards (e.g. SKF Lincoln / Bijur)', 'Progressive systems', 'Design (to be verified).'),), 'references': ['SKF Lincoln system manuals'],
                                       'components': _comp(('cl_pump', 'Store and pump grease.', 'Reservoir, paddle, pump element, PRV, controller.', '—', '—', ['Empty reservoir', 'Air pockets'], ['Low-level alarm']),
                                                           ('cl_divider', 'Meter and sequence.', 'Progressive divider with cycle indicator.', 'Steel/brass.', '—', ['Blockage stops system'], ['Cycle switch']),
                                                           ('cl_points', 'Lubricated machine.', 'Plummer blocks on conveyor shafts.', '—'), ('cl_lines', 'Carry grease.', 'Main and feed lines.', 'Steel / nylon.', '—', ['Crushed / leaking line'], ['Walk-down']))},
    'oil_mist_lubrication_system': {'summary': 'An oil mist system atomises oil into a very fine mist carried by air through a header to many pump and motor bearings, where reclassifier fittings condense it into lubricating droplets.',
                                    'classification': {'family': 'Lubrication', 'type': 'Central oil mist (pure mist)'}, 'model_configuration': {'animation': 'Mist flows along the header and drop legs'},
                                    'standards': _std(('API 610 Annex / API RP 686', 'Oil mist lubrication', 'Application to pumps (to be verified).'),), 'references': ['Bloch — Oil Mist Lubrication: Practical Applications'],
                                    'components': _comp(('om_generator', 'Generate mist.', 'Console with reservoir, regulator, venturi head, controller.', 'Stainless.', '≈ 2–5 kPa header.', ['Low oil / air alarm'], ['Console checks']),
                                                        ('om_header', 'Distribute mist.', 'Sloped header.', 'Galvanised / stainless.'), ('om_pumps', 'Lubricated machines.', 'Pumps.', '—'),
                                                        ('om_drops', 'Feed bearings.', 'Top take-off drop legs, reclassifiers, drain bottles.', 'Stainless.', '—', ['Plugged reclassifier'], ['Check drain bottles']))},
    'shaft_alignment_system': {'summary': 'Shaft alignment with dial indicators measures how far the shafts of two coupled machines are offset and angled, so the movable machine can be shimmed and moved until both shafts share one centreline.',
                               'classification': {'family': 'Maintenance tools', 'type': 'Rim-and-face dial indicator alignment'}, 'model_configuration': {'animation': 'Shafts and bracket turn through 180°; motor is moved into line'},
                               'standards': _ALN, 'references': ['Piotrowski — Shaft Alignment Handbook'],
                               'components': {**_AL, **_comp(('al_coupling', 'Shafts and hubs.', 'Coupling hubs on shafts.', 'Steel.'), ('al_indicators', 'Measure readings.', 'Bracket with rim and face dial indicators.', 'Steel.', '—', ['Bracket sag'], ['Sag check']),
                                                             ('al_shims', 'Correct alignment.', 'Precision shims, jacking bolts.', 'Stainless / brass.'))}},
    'laser_alignment_equipment': {'summary': 'Laser alignment equipment uses laser transmitters and position detectors clamped to each shaft to measure misalignment precisely and calculate the shim and horizontal corrections for the movable machine.',
                                  'classification': {'family': 'Maintenance tools', 'type': 'Two-unit laser alignment system'}, 'model_configuration': {'animation': 'Units rotate 9-12-3 o\'clock with the shafts'},
                                  'standards': _ALN, 'references': ['Maker manuals (Easy-Laser, Prüftechnik, SKF)'],
                                  'components': {**_AL, **_comp(('la_units', 'Measure.', 'S- and M-units with lasers/PSDs, chain brackets.', '—', '—', ['Loose bracket'], ['Check before measuring']), ('la_display', 'Compute and show corrections.', 'Display unit / tablet.', '—'))}},
    'dynamic_balancing_machine': {'summary': 'A dynamic balancing machine spins a rotor on sensitive pedestals, measures the vibration caused by unbalance and its phase, and tells the operator how much mass to add or remove, and where, in two correction planes.',
                                  'classification': {'family': 'Maintenance tools', 'type': 'Horizontal soft-bearing balancing machine'}, 'model_configuration': {'animation': 'Rotor turns; pedestals vibrate once per revolution'},
                                  'standards': _std(('ISO 21940-11', 'Rotor balancing — procedures and tolerances for rigid rotors', 'Balance grades.'), ('ISO 21940-21', 'Description and evaluation of balancing machines', 'Machine capability.')), 'references': ['Schenck balancing handbook'],
                                  'components': _comp(('db_bed', 'Base.', 'Machine bed.', 'Cast/fabricated steel.'), ('db_pedestals', 'Support and sense.', 'Roller carriages on springs, pick-ups.', '—', '—', ['Roller wear'], ['Calibration']),
                                                      ('db_rotor', 'Workpiece.', 'Fan rotor on arbor.', 'Steel.'), ('db_drive', 'Spin rotor.', 'Drive head, universal shaft.', '—'), ('db_console', 'Measure and display.', 'Console, photo-cell.', '—'))},
    'vibration_monitoring_system': {'summary': 'A vibration monitoring system measures machine vibration continuously with accelerometers on bearing housings and proximity probes at shafts, and a monitor rack compares readings with alert and trip limits.',
                                    'classification': {'family': 'Condition monitoring', 'type': 'Permanently installed protection / monitoring system'}, 'model_configuration': {'animation': 'Shaft turns; signals travel to the rack'},
                                    'standards': _VIB, 'references': ['API 670', 'ISO 20816'],
                                    'components': {**_AL, **_comp(('vm_shaft', 'Rotating element with reference.', 'Shaft, coupling, keyphasor notch.', 'Steel.'), ('vm_sensors', 'Measure casing vibration.', 'Accelerometers / velocity transducers (H, V, A).', 'Stainless.', '—', ['Loose mounting'], ['Mounting check']),
                                                                  ('vm_probes', 'Measure shaft displacement.', 'X–Y eddy-current probes, keyphasor.', '—', '—', ['Gap drift'], ['Gap voltage']), ('vm_rack', 'Process, alarm, trip.', 'Junction box, cables, monitor rack.', '—'))}},
    'online_condition_monitoring_system': {'summary': 'An online condition monitoring system collects vibration, temperature and oil-condition data from sensors on many machines through a wireless or wired network, so analytics can spot developing faults early and maintenance can be planned.',
                                           'classification': {'family': 'Condition monitoring', 'type': 'Wireless sensor network with edge server & dashboard'}, 'model_configuration': {'animation': 'Data packets travel from sensors to gateway to server'},
                                           'standards': _VIB + _std(('ISO 13374', 'Condition monitoring and diagnostics — data processing, communication and presentation', 'Architecture.'), ('ISO 17359', 'Condition monitoring — general guidelines', 'Programme.')),
                                           'references': ['ISO 17359'],
                                           'components': _comp(('ocm_machines', 'Monitored assets.', 'Fan, pump, gearbox.', '—'), ('ocm_sensors', 'Measure condition.', 'Wireless vibration/temperature sensors, oil-quality sensor, thermal camera.', '—', '—', ['Battery depletion'], ['Battery status']),
                                                               ('ocm_network', 'Collect data.', 'Gateway (mesh network).', '—'), ('ocm_server', 'Store and analyse.', 'Edge server, historian, dashboard.', '—'))},
}
BUILDERS = {k: globals()[k] for k in META}
