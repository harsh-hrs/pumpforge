"""Water Treatment & Utilities — EQ-296 … EQ-308: clarification, disinfection, ion exchange, degassing, chemical systems."""
import math
from mathutils import Matrix, Vector
from pumpforge.core import Model, lathe, cyl, box, csg, join, rotate, TAU, OPERATE_FRAMES
from pumpforge.valvekit import P, keys_loop, smooth_pulse
from pumpforge.parts import hollow_pipe, pressure_gauge, add_tracers
from pumpforge.vesselkit import vessel, nozzle, legs, droplets, liquid_v, half, animate_level, packing, mesh_pad
from pumpforge.plantkit import thickener, agitated_tank, particles_path, ball, silo
from pumpforge.shapes import sweep_tube
from pumpforge.common_meta import C
from pumps._eq_thermal_a import _bands_z, _bands_x, _pump, _fan_rotor

CAT = '13 · Water Treatment & Utilities'


def _model(pid, title):
    return Model(pid, title, CAT, META[pid])


def _press(m, objs, title, desc, kind='pressure'):
    m.overlay(kind, join(kind, objs), title, desc, split=True)


def _rect_tank(name, x0, x1, W, H, mat='cast_iron', t=0.08, z0=0.0):
    """Open rectangular (concrete) tank."""
    return csg(name, [box(name + 'o', (x1 - x0 + 2 * t, W + 2 * t, H), ((x0 + x1) / 2, 0, z0 + H / 2), mat)], [box(name + 'i', (x1 - x0, W, H), ((x0 + x1) / 2, 0, z0 + H / 2 + t), mat)], mat)


def _water_box(name, x0, x1, W, z0, z1, mat='water'):
    """Half (y >= 0) water body in a rectangular tank."""
    return box(name, (x1 - x0 - 0.01, W / 2 - 0.01, z1 - z0), ((x0 + x1) / 2, W / 4, (z0 + z1) / 2), mat)


def _ix_vessel(m, pid, label, cx, R, Z0, L, resin_layers, ref, mat='paint_blue', distributor=True):
    """Ion-exchange / filter vessel with resin layers (list of (z0, z1, mat, name)), distributor & collector."""
    v = vessel(pid, R, L, 0.01, mat, heads=('2:1', '2:1'), z0=Z0, center=(cx, 0, 0))
    P(m, pid, label, 'vessel', v, explode=(0, 0.6, 0), ref=ref + '_vessel')
    beds = [lathe(f'{pid}r{k}', [(0.0, z0), (R - 0.012, z0), (R - 0.012, z1), (0.0, z1)], mt, 48, a0=0.0, a1=math.pi, center=(cx, 0, 0), cap_mat=mt) for k, (z0, z1, mt, _) in enumerate(resin_layers)]
    P(m, pid + '_resin', label.split(' (')[0] + ': ' + ' / '.join(n for *_, n in resin_layers), 'media', beds, explode=(0, -0.5, 0), ref=ref + '_resin', section='keep')
    if distributor:
        it = [cyl(pid + 'dh', 0.03, Z0 + L - 0.1, Z0 + L + R * 0.5, 'polypropylene', 16, center=(cx, 0, 0)), cyl(pid + 'dd', R * 0.6, Z0 + L - 0.12, Z0 + L - 0.1, 'polypropylene', 32, center=(cx, 0, 0)),
              cyl(pid + 'cl', 0.03, Z0 - R * 0.5, Z0 + 0.05, 'polypropylene', 16, center=(cx, 0, 0))] + [cyl(f'{pid}la{k}', 0.015, cx - R * 0.8, cx + R * 0.8, 'polypropylene', 8, axis='X', center=(0, y, Z0 + 0.03)) for k, y in enumerate((-0.1, 0.0, 0.1))]
        P(m, pid + '_internals', label.split(' (')[0] + ': Inlet Distributor & Underdrain Collector (laterals with nozzles)', 'internals', it, explode=(0, -0.3, 0.3), ref=ref + '_internals', section='keep')


# =============================================================== EQ-296 Clariflocculator
def clariflocculator(out):
    m = _model('clariflocculator', 'Clariflocculator (Central Flocculation Zone + Peripheral Clarifier)')
    z0 = thickener(m, 'cf_', 1.4, 1.0, 0.45, label='Clariflocculator', ref='cfl', mat='cast_iron', liquid='water', mud='sludge', rake_revs=0.2)
    fz = csg('fz', [cyl('fzo', 0.62, z0 + 0.25, z0 + 1.0, 'cast_iron', 64)], [cyl('fzi', 0.58, z0 + 0.2, z0 + 1.1, 'cast_iron', 64)], 'cast_iron')
    P(m, 'flocculation_zone', 'Central Flocculation Compartment (skirt wall)', 'internals', fz, explode=(0, -0.4, 0.6), ref='cfl_floc', section='split')
    pd = []
    for k in range(4):
        a = TAU * k / 4
        for j, r in enumerate((0.25, 0.45)):
            p_ = box(f'pd{k}{j}', (0.04, 0.12, 0.5), (r, 0, z0 + 0.6), 'steel')
            pd.append(rotate(p_, a, 'Z'))
        pd.append(rotate(box(f'pa{k}', (0.5, 0.03, 0.03), (0.27, 0, z0 + 0.88), 'steel'), a, 'Z'))
    pd.append(cyl('ps', 0.035, z0 + 0.3, z0 + 1.4, 'steel', 16))
    ppd = P(m, 'flocculator_paddles', 'Slow-Speed Paddle Flocculator (gentle mixing grows flocs)', 'rotating_element', pd, explode=(0, -0.7, 0.7), ref='cfl_floc', section='keep')
    ppd.spin('Z', 0.6)
    pp = [hollow_pipe('in', [(-2.2, 0, 0.1), (0.0, 0, 0.1), (0.0, 0, z0 + 0.4)], 0.06, 'cast_iron', 16, bend=0.1), hollow_pipe('cg', [(-2.2, 0.4, 0.35), (-2.2, 0.4, z0 + 1.5), (-0.2, 0.4, z0 + 1.5), (-0.2, 0.2, z0 + 0.95)], 0.02, 'paint_green', 8, bend=0.04),
          box('dp', (0.3, 0.22, 0.2), (-2.2, 0.4, 0.22), 'paint_green'), box('dpb', (0.4, 0.3, 0.12), (-2.2, 0.4, 0.06), 'cast_iron'),
          nozzle('of', (1.55, 0, z0 + 0.85), (1, 0, 0), 0.07, 0.4)]
    P(m, 'piping', 'Raw-Water Inlet (central riser), Coagulant/Polymer Dosing Pump & Line, Clarified-Water Outlet', 'piping', pp, explode=(0, 0, 0.4), ref='cfl_piping', section='keep')
    particles_path(m, 'flocs', 'Flocs growing in the Flocculation Zone then settling', lambda i, s: ((0.3 + 0.9 * s) * math.cos(TAU * (i / 12)), abs((0.3 + 0.9 * s) * math.sin(TAU * (i / 12))) + 0.03, z0 + 0.8 - 0.6 * s), 12,
                   mat='sludge', r=0.012, scale_fn=lambda i, s: 0.6 + 1.6 * s)
    m.flow('coagulant', [(-2.2, 0.4, 0.35), (-2.2, 0.4, z0 + 1.5), (-0.2, 0.4, z0 + 1.5), (-0.2, 0.2, z0 + 0.95)], 'flow_discharge', 0.012, 0.25)
    m.flow('raw_water', [(-2.3, 0, 0.1), (0, 0, 0.1), (0, 0.05, z0 + 0.9), (0.4, 0.05, z0 + 0.4), (1.2, 0.05, z0 + 0.85), (1.95, 0, z0 + 0.85)], 'water', 0.025, 0.4)
    m.flow('sludge', [(0, 0.05, 0.2), (0, 0.05, 0.05)], 'sand', 0.02, 0.2)
    _press(m, [cyl('fz1', 0.65, z0 + 0.25, z0 + 1.0, 'pressure_6', 64, r_in=0.63), cyl('cz1', 1.45, z0 + 0.5, z0 + 1.0, 'pressure_2', 96, r_in=1.43)], 'Flocculate, then settle',
           'Coagulated raw water first passes through the central flocculation zone, where slow paddles (velocity gradient G ≈ 20–70 s⁻¹) let tiny particles collide and grow into flocs. The water then '
           'moves outward and upward through the clarifier zone at low surface loading (≈ 1–2 m/h); flocs settle and are raked to the central sludge pit; clear water overflows the peripheral weir.')
    return m.export(out)


# =============================================================== EQ-297 Flash mixer
def flash_mixer(out):
    m = _model('flash_mixer', 'Flash (Rapid) Mixer for Coagulant Dispersion')
    R, Z0, H = 0.5, 0.3, 1.0
    agitated_tank(m, 'fm_', R, Z0, H, 'Flash Mixing Tank', 'fmx', liquid='water', imp='pbt', revs=8, open_top=True)
    pp = [hollow_pipe('in', [(-1.4, 0, Z0 + 0.2), (-R, 0, Z0 + 0.2)], 0.06, 'cast_iron', 16), nozzle('out', (R, 0, Z0 + H - 0.2), (1, 0, 0), 0.07, 0.4),
          hollow_pipe('cg', [(-1.2, 0.3, 0.3), (-1.2, 0.3, Z0 + H + 0.5), (-0.1, 0.3, Z0 + H + 0.5), (-0.1, 0.25, Z0 + 0.5)], 0.015, 'paint_green', 8, bend=0.03),
          box('dp', (0.28, 0.2, 0.18), (-1.2, 0.3, 0.2), 'paint_green'), box('dpb', (0.36, 0.28, 0.11), (-1.2, 0.3, 0.055), 'cast_iron')]
    P(m, 'piping', 'Raw-Water Inlet (bottom), Coagulant Metering Pump & Dosing Point (at impeller), Outlet to Flocculation', 'piping', pp, explode=(0, 0, 0.4), ref='fmx_piping', section='keep')
    P(m, 'foundation', 'Concrete Plinth', 'structure', box('fd', (1.3, 1.3, Z0), (0, 0, Z0 / 2), 'cast_iron'), explode=(0, 0, -0.3), ref='fmx_tank', section='split')
    particles_path(m, 'coagulant', 'Coagulant dispersed in seconds by the high-speed impeller', lambda i, s: ((0.05 + 0.4 * s) * math.cos(TAU * (3 * s + i / 10)), abs((0.05 + 0.4 * s) * math.sin(TAU * (3 * s + i / 10))) + 0.02, Z0 + 0.4 + 0.4 * math.sin(TAU * s + i)), 12, mat='paint_green', r=0.012)
    m.flow('water', [(-1.5, 0, Z0 + 0.2), (-0.2, 0.05, Z0 + 0.25), (0.3, 0.05, Z0 + H - 0.2), (R + 0.5, 0, Z0 + H - 0.2)], 'water', 0.02, 0.3)
    m.flow('coagulant', [(-1.2, 0.3, 0.3), (-1.2, 0.3, Z0 + H + 0.5), (-0.1, 0.3, Z0 + H + 0.5), (-0.1, 0.25, Z0 + 0.45)], 'flow_discharge', 0.012, 0.2)
    _press(m, [cyl('gz', R + 0.05, Z0, Z0 + H, 'pressure_8', 64, r_in=R + 0.03)], 'High velocity gradient, short time',
           'Coagulants (alum, ferric salts, PACl) react within seconds, so they must be spread through the whole flow almost instantly. Flash mixers use high energy — velocity gradient G ≈ 300–1000 s⁻¹ — '
           'with short detention (≈ 10–60 s). Too little mixing wastes chemical; too long or too intense mixing is not useful at this stage.')
    return m.export(out)


# =============================================================== EQ-298 Flocculation tank
def flocculation_tank(out):
    m = _model('flocculation_tank', 'Horizontal-Paddle Flocculation Tank (Three Tapered-Energy Stages)')
    X0, X1, W, H = -2.0, 2.0, 1.2, 1.3
    P(m, 'tank', 'Flocculation Basin, Over-and-Under Baffle Walls (3 compartments), Inlet & Outlet', 'tank', [_rect_tank('tk', X0, X1, W, H)] + [box('bw0', (0.06, W, H - 0.38), (-0.67, 0, 0.38 + (H - 0.38) / 2), 'cast_iron'), box('bw1', (0.06, W, 0.87), (0.67, 0, 0.08 + 0.87 / 2), 'cast_iron')]
      + [nozzle('fin', (X0, 0, 0.9), (-1, 0, 0), 0.08, 0.35), nozzle('fout', (X1, 0, 0.35), (1, 0, 0), 0.08, 0.35)],
      explode=(0, 0.7, 0), ref='ft_tank')
    pw = P(m, 'water', 'Coagulated Water', 'fluid', _water_box('wt', X0, X1, W, 0.08, H - 0.15), explode=(0, -0.4, 0), ref='ft_tank', section='keep')
    for k, (xc, rev) in enumerate(((-1.33, 1.2), (0.0, 0.8), (1.33, 0.5))):
        reel = [cyl(f'sh{k}', 0.035, -W / 2 - 0.1, W / 2 + 0.25, 'steel', 16, axis='Y', center=(xc, 0, 0.65))]
        for a in range(4):
            for y in (-0.35, 0.0, 0.35):
                reel.append(rotate(box(f'pb{k}{a}{y}', (0.08, 0.25, 0.03), (xc, y, 0.65 + 0.4), 'polypropylene'), TAU * a / 4, 'Y', (xc, 0, 0.65)))
            reel.append(rotate(box(f'ar{k}{a}', (0.03, 0.04, 0.4), (xc, -0.5, 0.65 + 0.2), 'steel'), TAU * a / 4, 'Y', (xc, 0, 0.65)))
        pr = P(m, f'paddle_reel_{k + 1}', f'Paddle Reel {k + 1} (speed tapers stage by stage)', 'rotating_element', reel, explode=(0, -0.8, 0.3), ref='ft_paddles', section='keep', pivot=(xc, 0, 0.65))
        pr.spin('Y', rev)
    dr = [join(f'dr{k}', [box(f'gb{k}', (0.25, 0.25, 0.25), (xc, W / 2 + 0.35, 0.65), 'paint_blue'), cyl(f'mt{k}', 0.09, W / 2 + 0.5, W / 2 + 0.85, 'paint_motor', 24, axis='Y', center=(xc, 0, 0.65))]) for k, xc in enumerate((-1.33, 0.0, 1.33))]
    P(m, 'drives', 'Variable-Speed Gearmotor Drives', 'drive', dr, explode=(0, 0.5, 0), ref='ft_drive', section='keep')
    particles_path(m, 'flocs', 'Flocs growing from pin-point to large settleable flocs', lambda i, s: (X0 + 0.2 + (X1 - X0 - 0.4) * s, 0.1 + 0.4 * ((i * 0.37) % 1), 0.3 + 0.8 * ((i * 0.53) % 1) + 0.1 * math.sin(TAU * 3 * s)), 16,
                   mat='sludge', r=0.012, scale_fn=lambda i, s: 0.5 + 2.0 * s)
    m.flow('water', [(X0 - 0.35, 0, 0.9), (-0.85, 0.05, 0.9), (-0.85, 0.05, 0.22), (-0.5, 0.05, 0.22), (-0.5, 0.05, 1.05), (0.85, 0.05, 1.05), (0.85, 0.05, 0.35), (X1 + 0.35, 0, 0.35)], 'water', 0.025, 0.4)
    _press(m, [box(f'gz{k}', (1.3, 0.02, 0.2), (x, 0.1, H + 0.12), f'pressure_{lev}') for k, (x, lev) in enumerate(((-1.33, 7), (0.0, 5), (1.33, 3)))], 'Tapered mixing energy',
           'Flocculation needs gentle mixing for 15–30 min. Energy is highest in the first stage (G ≈ 50–70 s⁻¹) to promote collisions and lowest in the last (G ≈ 10–20 s⁻¹) so the large, fragile flocs are not '
           'broken up before settling. The product G·t (≈ 10⁴–10⁵) is a key design number.')
    return m.export(out)


# =============================================================== EQ-299 Lamella clarifier
def lamella_clarifier(out):
    m = _model('lamella_clarifier', 'Lamella (Inclined-Plate) Clarifier')
    X0, X1, W, H = -1.3, 1.3, 1.0, 1.8
    tk = _rect_tank('tk', X0, X1, W, H, mat='paint_blue', t=0.04, z0=0.6)
    hp = lathe('hp', [(0.0, 0.05), (0.08, 0.05), (W * 0.7, 0.6), (0.0, 0.6)], 'paint_blue', 4, a0=math.pi / 4, a1=math.pi / 4 + TAU, center=(0.3, 0, 0))
    P(m, 'tank', 'Clarifier Tank, Inlet Channel & Sludge Hopper', 'tank', [tk, hp, box('ic', (0.04, W, H - 0.4), (X0 + 0.35, 0, 0.6 + (H - 0.4) / 2 + 0.3), 'paint_blue')], explode=(0, 0.7, 0), ref='lc_tank')
    pl = [rotate(box(f'lp{k}', (0.008, W - 0.06, 1.1), (-0.5 + 0.13 * k, 0, 1.35), 'polypropylene'), math.radians(-30), 'Y', (-0.5 + 0.13 * k, 0, 1.35)) for k in range(11)]
    P(m, 'plate_pack', 'Inclined Lamella Plate Pack (≈ 55–60°)', 'internals', pl, explode=(0, -0.8, 0.3), ref='lc_plates', section='split')
    ld = [box(f'ld{k}', (0.06, W - 0.06, 0.08), (-0.4 + 0.3 * k, 0, 0.6 + H - 0.1), 'stainless') for k in range(5)]
    P(m, 'launders', 'Collection Launders above the Plates (V-notch weirs)', 'launders', ld, explode=(0, 0, 0.5), ref='lc_launders', section='split')
    P(m, 'water', 'Water', 'fluid', _water_box('wt', X0, X1, W, 0.68, 0.6 + H - 0.12), explode=(0, -0.4, 0), ref='lc_tank', section='keep')
    P(m, 'sludge', 'Sludge in the Hopper', 'fluid', lathe('sl', [(0.0, 0.06), (0.08, 0.06), (W * 0.45, 0.4), (0.0, 0.4)], 'sludge', 4, a0=0.0, a1=math.pi, center=(0.3, 0, 0), cap_mat='sludge'), explode=(0, -0.4, -0.2), ref='lc_tank', section='keep')
    nz = [nozzle('in', (X0, 0, 1.9), (-1, 0, 0), 0.06, 0.3), nozzle('out', (X1, 0, 2.2), (1, 0, 0), 0.06, 0.3), nozzle('sd', (0.3, 0, 0.05), (0, 0, -1), 0.04, 0.2)]
    P(m, 'nozzles', 'Inlet, Clarified Outlet & Sludge Drain', 'nozzles', nz, explode=(0, 0, -0.3), ref='lc_tank', section='keep')
    P(m, 'supports', 'Support Frame', 'structure', [box(f'sp{k}', (0.08, 0.08, 0.62), (sx * (X1 - 0.05), sy * (W / 2 - 0.05), 0.31), 'paint_grey') for k, (sx, sy) in enumerate(((-1, -1), (-1, 1), (1, -1), (1, 1)))],
      explode=(0, 0, -0.3), ref='lc_tank', section='keep')
    particles_path(m, 'settling', 'Particles settling a short distance onto the plates and sliding down', lambda i, s: (-0.5 + 0.13 * (i % 10) + 0.35 * (1 - s) - 0.2, 0.15, 0.85 + 0.9 * (1 - s) * ((i * 0.37) % 1) + 0.2 * (1 - s)), 12, mat='sludge', r=0.012)
    m.flow('water', [(X0 - 0.35, 0, 1.9), (X0 + 0.25, 0.1, 1.9), (X0 + 0.25, 0.1, 0.8), (0.2, 0.1, 0.8), (0.6, 0.1, 2.1), (X1 + 0.35, 0, 2.2)], 'water', 0.02, 0.4)
    m.flow('sludge', [(0.3, 0.05, 0.4), (0.3, 0, -0.1)], 'sand', 0.015, 0.2)
    _press(m, [box('az', (1.4, 0.02, 1.0), (-0.1, -W / 2 - 0.06, 1.35), 'pressure_6')], 'Projected plate area does the work',
           'Settling depends on surface area. Each inclined plate adds its horizontal projected area, so a lamella clarifier provides many times the settling area of a conventional clarifier of the same '
           'footprint. Particles only fall a few centimetres to the plate, then slide down into the hopper while clarified water flows up between the plates to the launders.')
    return m.export(out)


# =============================================================== EQ-300 Chlorination system
def chlorination_system(out):
    m = _model('chlorination_system', 'Gas Chlorination System (Vacuum-Operated Chlorinator, Ejector, Diffuser)')
    cyls = [join(f'tc{k}', [cyl(f'tcb{k}', 0.38, -0.95, 0.95, 'paint_yellow', 48, axis='X', center=(0, y, 0.55)), cyl(f'tcv{k}', 0.05, 0.95, 1.05, 'brass', 16, axis='X', center=(0, y, 0.65))]) for k, y in enumerate((-0.5, 0.5))]
    sc = [box('sc', (2.2, 1.9, 0.12), (0, 0, 0.06), 'paint_grey')] + [cyl(f'tr{k}{s}', 0.08, -1.0, -0.8, 'rubber', 16, axis='X', center=(0, s, 0.2)) for k in range(1) for s in (-0.8, -0.2, 0.2, 0.8)]
    P(m, 'containers_scale', 'Chlorine Ton Containers on Trunnion Rollers & Weighing Scale', 'storage', cyls + sc, explode=(0, 0, -0.3), ref='cl_containers', section='keep')
    vr = [join(f'vr{k}', [box(f'vrb{k}', (0.12, 0.12, 0.18), (1.15, y, 0.75), 'paint_grey'), cyl(f'vrd{k}', 0.07, 1.06, 1.1, 'paint_blue', 24, axis='X', center=(0, y, 0.75))]) for k, y in enumerate((-0.5, 0.5))]
    vr.append(box('aso', (0.4, 0.15, 0.3), (1.6, 0, 1.2), 'paint_grey'))
    P(m, 'vacuum_regulators', 'Vacuum Regulators on the Container Valves & Automatic Switchover', 'control', vr, explode=(0.3, 0, 0.3), ref='cl_regulator', section='keep')
    pn = join('pn', [box('pnb', (0.5, 0.15, 0.8), (2.4, 0, 1.4), 'paint_grey'), cyl('rm', 0.03, 1.3, 1.6, 'glass', 12, center=(2.4, -0.08, 0)), cyl('rf', 0.012, 1.42, 1.48, 'paint_red', 8, center=(2.4, -0.1, 0))])
    pfl = P(m, 'chlorinator', 'Chlorinator Panel: Rotameter, Rate Valve & Differential Regulator', 'control', pn, explode=(0.4, 0, 0), ref='cl_chlorinator', section='keep')
    ej = join('ej', [cyl('ejb', 0.05, 2.7, 3.2, 'paint_grey', 24, axis='X', center=(0, 0, 0.6)), lathe('ejn', [(0.0, 2.85), (0.05, 2.85), (0.02, 2.95), (0.0, 2.95)], 'steel', 16, axis='X', center=(0, 0, 0.6))])
    vl = [hollow_pipe('vl', [(1.6, 0, 1.2), (2.4, 0, 1.0), (2.95, 0, 1.0), (2.95, 0, 0.65)], 0.015, 'polypropylene', 8, bend=0.03), hollow_pipe('mw', [(2.2, 0.4, 0.6), (2.7, 0.4, 0.6), (2.7, 0, 0.6)], 0.03, 'paint_blue', 12, bend=0.04),
          hollow_pipe('sl', [(3.2, 0, 0.6), (3.6, 0, 0.6), (3.6, 0, 0.0), (4.0, 0, 0.0)], 0.03, 'polypropylene', 12, bend=0.04)]
    P(m, 'ejector_lines', 'Ejector (water-jet vacuum source), Vacuum Line, Motive Water & Solution Line', 'piping', [ej] + vl, explode=(0, -0.3, 0), ref='cl_ejector', section='keep')
    ct = _rect_tank('ct', 3.8, 5.6, 0.9, 0.9, t=0.05, z0=-0.6)
    df = cyl('df', 0.025, 3.9, 4.6, 'polypropylene', 12, axis='X', center=(0, 0, -0.45))
    P(m, 'contact_tank', 'Chlorine Contact Tank (serpentine baffles give contact time)', 'tank', [ct] + [box(f'cb{k}', (0.04, 0.6, 0.85), (4.2 + 0.4 * k, (-0.15 if k % 2 else 0.15), -0.15), 'cast_iron') for k in range(3)],
      explode=(0, 0.5, 0), ref='cl_contact', section='split')
    P(m, 'diffuser', 'Solution Diffuser (perforated pipe across the inlet)', 'piping', df, explode=(0, -0.3, 0.3), ref='cl_contact', section='keep')
    P(m, 'ct_water', 'Water in the Contact Tank', 'fluid', _water_box('ctw', 3.8, 5.6, 0.9, -0.55, 0.2), explode=(0, -0.4, 0), ref='cl_contact', section='keep')
    P(m, 'detector', 'Chlorine Gas Leak Detector & Alarm', 'safety', join('dt', [box('dtb', (0.15, 0.08, 0.2), (-1.2, 0.9, 0.3), 'paint_red'), cyl('dts', 0.03, 0.15, 0.2, 'steel', 12, center=(-1.2, 0.9, 0))]), explode=(-0.3, 0.3, 0), ref='cl_safety', section='keep')
    droplets(m, 'solution', 'Chlorine Solution dispersed from the Diffuser', 3.95, 4.55, -0.42, -0.05, n=8, mat='paint_green', y=0.1, r=0.012)
    m.flow('chlorine_gas_vacuum', [(1.15, -0.5, 0.75), (1.6, 0, 1.2), (2.4, 0, 1.45), (2.4, 0, 1.0), (2.95, 0, 1.0), (2.95, 0, 0.65)], 'air', 0.012, 0.3)
    m.flow('motive_water', [(2.1, 0.4, 0.6), (2.7, 0.4, 0.6), (2.7, 0, 0.6), (3.6, 0, 0.6), (3.6, 0, 0.0), (4.6, 0, -0.45)], 'water', 0.015, 0.3)
    _press(m, [cyl('vz', 0.03, 1.0, 2.9, 'pressure_1', 12, axis='X', center=(0, -0.2, 1.05), r_in=0.02)], 'Vacuum operation is a safety feature',
           'Gas is drawn from the container by vacuum created at the ejector. If the vacuum is lost (line break, ejector failure) the vacuum regulator at the container valve closes automatically, so chlorine '
           'gas under pressure never travels through the building. Dose is set on the rotameter (e.g. kg/day); disinfection depends on C·t (residual × contact time).')
    return m.export(out)


# =============================================================== EQ-301 UV disinfection
def uv_disinfection_system(out):
    m = _model('uv_disinfection_system', 'Closed-Vessel UV Disinfection Reactor')
    R, X0, X1, CZ = 0.3, -0.9, 0.9, 0.9
    ch = join('ch', [cyl('cs', R, X0, X1, 'stainless', 64, axis='X', center=(0, 0, CZ), r_in=R - 0.008)] + [cyl(f'fl{k}', R + 0.05, x - 0.03, x, 'stainless', 64, axis='X', center=(0, 0, CZ)) for k, x in enumerate((X0 + 0.03, X1))])
    nz = [nozzle('in', (X0 + 0.2, 0, CZ - R), (0, 0, -1), 0.12, 0.3), nozzle('out', (X1 - 0.2, 0, CZ + R), (0, 0, 1), 0.12, 0.3)]
    P(m, 'chamber', 'Stainless Reactor Chamber with Inlet & Outlet', 'vessel', [ch] + nz, explode=(0, 0.6, 0), ref='uv_chamber')
    pos = [(0.0, 0.0), (0.15, 0.1), (-0.15, 0.1), (0.15, -0.1), (-0.15, -0.1)]
    qs = [cyl(f'qs{k}', 0.035, X0 + 0.03, X1, 'glass', 24, axis='X', center=(0, y, CZ + z), r_in=0.03) for k, (y, z) in enumerate(pos)]
    P(m, 'quartz_sleeves', 'Quartz Sleeves (protect lamps, transmit UV-C)', 'lamps', qs, explode=(0, -0.5, 0.3), ref='uv_sleeves', section='keep')
    lp = [cyl(f'lp{k}', 0.015, X0 + 0.05, X1 - 0.02, 'uv_glow', 12, axis='X', center=(0, y, CZ + z)) for k, (y, z) in enumerate(pos)]
    plp = P(m, 'uv_lamps', 'UV Lamps (low-pressure amalgam or medium-pressure, 254 nm)', 'lamps', lp, explode=(0, -0.8, 0.4), ref='uv_lamps', section='keep')
    keys_loop(m, plp, lambda t: (1, 1 + 0.15 * math.sin(TAU * 4 * t), 1 + 0.15 * math.sin(TAU * 4 * t)), 'scale')
    wp = join('wp', [cyl('wpr', R - 0.02, -0.02, 0.02, 'rubber', 48, axis='X', center=(0, 0, CZ), r_in=R - 0.05)] + [cyl(f'wr{k}', 0.045, -0.02, 0.02, 'rubber', 24, axis='X', center=(0, y, CZ + z), r_in=0.035) for k, (y, z) in enumerate(pos)])
    pwp = P(m, 'wiper', 'Automatic Sleeve Wiper (keeps quartz clean)', 'cleaning', wp, explode=(0, -0.4, 0.6), ref='uv_wiper', section='keep')
    keys_loop(m, pwp, lambda t: (X0 + 0.15 + (X1 - X0 - 0.3) * (0.5 - 0.5 * math.cos(TAU * t)), 0, 0))
    pn = join('pn', [box('pb', (0.5, 0.2, 0.8), (1.6, 0, 0.9), 'paint_grey'), box('sn', (0.06, 0.06, 0.1), (0.2, 0, CZ + R + 0.05), 'paint_blue_dark')])
    P(m, 'control_sensor', 'Ballast/Control Panel & UV-Intensity Sensor', 'controls', pn, explode=(0.4, 0, 0), ref='uv_control', section='keep')
    P(m, 'supports', 'Supports', 'structure', [box(f'sp{k}', (0.12, 0.5, CZ - R), (x, 0, (CZ - R) / 2), 'paint_grey') for k, x in enumerate((X0 + 0.4, X1 - 0.4))], explode=(0, 0, -0.3), ref='uv_chamber', section='keep')
    add_tracers(m, 'microbes', 'Microorganisms receiving the UV Dose as they pass the Lamps', [(X0 + 0.2, 0.1, CZ - R - 0.3), (X0 + 0.2, 0.1, CZ - 0.1), (X1 - 0.2, 0.15, CZ + 0.1), (X1 - 0.2, 0.1, CZ + R + 0.3)], n=10, radius=0.015, mat='paint_green')
    m.flow('water', [(X0 + 0.2, 0, CZ - R - 0.35), (X0 + 0.2, 0.2, CZ - 0.15), (X1 - 0.2, 0.2, CZ + 0.15), (X1 - 0.2, 0, CZ + R + 0.35)], 'water', 0.02, 0.3)
    m.flow('power', [(1.6, 0, 1.3), (X1 + 0.05, 0, CZ)], 'electric', 0.012, 0.2)
    _press(m, [cyl('dz', R + 0.04, X0, X1, 'pressure_7', 48, axis='X', center=(0, 0, CZ), r_in=R + 0.025)], 'UV dose damages microbial DNA',
           'UV-C light near 254 nm damages the DNA/RNA of bacteria, viruses and protozoa (Cryptosporidium, Giardia) so they cannot reproduce. Dose = intensity × exposure time (mJ/cm²; drinking water often '
           '≈ 40 mJ/cm²). UV leaves no residual, so a small chlorine dose is often added for the distribution network; water UV transmittance and sleeve fouling control performance.')
    return m.export(out)


# =============================================================== EQ-302 Ozonation system
def ozonation_system(out):
    m = _model('ozonation_system', 'Ozonation System (O₂ Feed, Ozone Generator, Diffuser Contactor, Off-Gas Destructor)')
    ox = join('ox', [vessel('lox', 0.25, 0.8, 0.008, 'paint_grey', heads=('2:1', '2:1'), z0=0.4, center=(-2.6, 0, 0)), cyl('vap', 0.08, 0.2, 1.4, 'aluminium', 16, center=(-2.0, 0.3, 0))])
    P(m, 'oxygen_supply', 'Oxygen Supply (LOX tank & vaporiser, or PSA oxygen)', 'gas', ox, explode=(-0.4, 0, 0), ref='oz_oxygen', section='keep')
    og = vessel('og', 0.3, 1.2, 0.008, 'stainless', axis='X', center=(0, 0, 1.0), heads=('flat', 'flat'), z0=-1.6)
    P(m, 'generator_vessel', 'Ozone Generator Vessel (cooled shell)', 'generator', og, explode=(0, 0.6, 0), ref='oz_generator')
    dt = [cyl(f'dt{k}', 0.04, -1.55, -0.45, 'glass', 16, axis='X', center=(0, y, 1.0 + z), r_in=0.03) for k, (y, z) in enumerate(((0, 0), (0.12, 0.1), (-0.12, 0.1), (0.12, -0.1), (-0.12, -0.1)))]
    pdt = P(m, 'dielectric_tubes', 'Dielectric Tubes / Electrodes (corona discharge: 3 O₂ → 2 O₃)', 'generator', dt, explode=(0, -0.6, 0.3), ref='oz_generator', section='keep')
    gl = [cyl(f'cg{k}', 0.025, -1.5, -0.5, 'uv_glow', 8, axis='X', center=(0, y, 1.0 + z)) for k, (y, z) in enumerate(((0, 0), (0.12, 0.1), (-0.12, 0.1), (0.12, -0.1), (-0.12, -0.1)))]
    pgl = P(m, 'corona', 'Corona Discharge Glow', 'generator', gl, explode=(0, -0.8, 0.3), ref='oz_generator', section='keep')
    keys_loop(m, pgl, lambda t: (1, 1 + 0.2 * math.sin(TAU * 8 * t), 1 + 0.2 * math.sin(TAU * 8 * t)), 'scale')
    ps = join('ps', [box('psu', (0.6, 0.4, 1.0), (-1.0, 0.8, 0.5), 'paint_grey')])
    P(m, 'power_supply', 'Medium-Frequency Power Supply Unit', 'electrical', ps, explode=(0, 0.5, 0), ref='oz_power', section='keep')
    X0, X1, W, H = 0.6, 2.8, 0.9, 1.6
    P(m, 'contactor', 'Ozone Contact Tank (covered; under/over baffles; counter-current first cell), Inlet & Outlet', 'tank', [_rect_tank('ct', X0, X1, W, H, t=0.05), box('cv', (X1 - X0 + 0.1, W + 0.1, 0.06), ((X0 + X1) / 2, 0, H + 0.03), 'cast_iron')] +
      [box(f'bf{k}', (0.05, W, H - 0.3), (x, 0, 0.05 + (H - 0.3) / 2 + (0.3 if k == 0 else 0)), 'cast_iron') for k, x in enumerate((1.3, 2.0))] +
      [nozzle('cin', (X0, 0, H - 0.3), (-1, 0, 0), 0.07, 0.3), nozzle('cout', (X1, 0, 0.3), (1, 0, 0), 0.07, 0.3)], explode=(0, 0.6, 0), ref='oz_contactor')
    P(m, 'water', 'Water in the Contactor', 'fluid', _water_box('wt', X0, X1, W, 0.05, H - 0.1), explode=(0, -0.4, 0), ref='oz_contactor', section='keep')
    df = [cyl(f'df{k}', 0.06, 0.08, 0.14, 'ptfe', 24, center=(x, 0.1, 0)) for k, x in enumerate((0.8, 1.0, 1.15))] + [hollow_pipe('og', [(-0.3, 0, 1.0), (0.3, 0, 1.0), (0.3, 0, 0.11), (1.15, 0.1, 0.11)], 0.02, 'stainless', 12, bend=0.05)]
    P(m, 'diffusers', 'Ozone Gas Line & Fine-Bubble Ceramic Diffusers', 'piping', df, explode=(0, -0.4, -0.2), ref='oz_diffusers', section='keep')
    dst = join('dst', [vessel('dsv', 0.18, 0.5, 0.006, 'stainless', heads=('2:1', '2:1'), z0=H + 0.3, center=(2.4, 0.3, 0)), hollow_pipe('dsp', [(2.4, 0.3, H + 0.06), (2.4, 0.3, H + 0.3)], 0.03, 'stainless', 12)])
    P(m, 'off_gas_destructor', 'Off-Gas Ozone Destructor (thermal/catalytic → O₂)', 'safety', dst, explode=(0, 0.3, 0.5), ref='oz_destructor', section='keep')
    droplets(m, 'bubbles', 'Ozone Bubbles rising and dissolving', 0.75, 1.2, 0.15, H - 0.15, n=12, mat='uv_glow', y=0.15, r=0.015)
    m.flow('oxygen', [(-2.6, 0, 1.3), (-2.0, 0.3, 1.4), (-1.7, 0, 1.0)], 'air', 0.015, 0.3)
    m.flow('ozone', [(-0.4, 0, 1.0), (0.3, 0, 1.0), (0.3, 0, 0.11), (1.15, 0.1, 0.11)], 'flow_discharge', 0.015, 0.3)
    m.flow('water', [(X0 - 0.35, 0, H - 0.3), (0.95, 0.2, H - 0.3), (0.95, 0.2, 0.2), (1.65, 0.2, 0.2), (1.65, 0.2, H - 0.15), (2.4, 0.2, H - 0.15), (2.4, 0.2, 0.3), (X1 + 0.35, 0, 0.3)], 'water', 0.02, 0.4)
    _press(m, [box('cz', (X1 - X0, 0.02, H - 0.2), ((X0 + X1) / 2, -W / 2 - 0.08, H / 2), 'pressure_6')], 'Strong oxidant, no lasting residual',
           'Ozone is a very strong oxidant: it disinfects (including Cryptosporidium at higher C·t), removes colour, taste and odour, and oxidises iron, manganese and micro-pollutants. It is made on site because '
           'it decomposes quickly. Transfer into water depends on bubble size and contact depth; leftover ozone in the off-gas is destroyed before venting because it is toxic (workplace limits ~ 0.1 ppm).')
    return m.export(out)


# =============================================================== EQ-303 Demineralization plant
def demineralization_plant(out):
    m = _model('demineralization_plant', 'Demineralization Plant (Strong-Acid Cation → Degasser → Strong-Base Anion)')
    R, Z0, L = 0.35, 0.6, 1.4
    _ix_vessel(m, 'cation', 'Cation Exchanger (H⁺ form)', -1.6, R, Z0, L, [(Z0 + 0.05, Z0 + 0.15, 'sand', 'Support Gravel'), (Z0 + 0.15, Z0 + 0.95, 'resin_cation', 'Strong-Acid Cation Resin')], 'dm')
    _ix_vessel(m, 'anion', 'Anion Exchanger (OH⁻ form)', 1.6, R, Z0, L, [(Z0 + 0.05, Z0 + 0.15, 'sand', 'Support Gravel'), (Z0 + 0.15, Z0 + 0.95, 'resin_anion', 'Strong-Base Anion Resin')], 'dm')
    dg = join('dg', [cyl('dgs', 0.25, 0.6, 2.6, 'polypropylene', 48, r_in=0.24), _rect_tank('dgt', -0.35, 0.35, 0.7, 0.6, mat='polypropylene', t=0.03)])
    P(m, 'degasser', 'Degasser Tower (removes CO₂ formed after the cation unit) & Degassed-Water Sump', 'vessel', dg, explode=(0, 0.6, 0.3), ref='dm_degasser', section='split')
    P(m, 'degasser_packing', 'Degasser Packing', 'internals', half(packing('dgp', 0.235, 1.3, 2.2), 'rubber'), explode=(0, -0.5, 0.3), ref='dm_degasser', section='keep')
    P(m, 'degasser_blower', 'Degasser Air Blower', 'air', [cyl('dgb', 0.12, 0.3, 0.5, 'paint_blue', 24, axis='Y', center=(0.45, 0, 0.75)), hollow_pipe('dga', [(0.45, 0.3, 0.75), (0.45, 0.0, 0.75), (0.25, 0.0, 0.75)], 0.05, 'polypropylene', 12, bend=0.04)],
      explode=(0.3, 0.3, 0), ref='dm_degasser', section='keep')
    pp = [hollow_pipe('c2d', [(-1.6, 0, Z0 - R * 0.5 - 0.05), (-1.6, 0, 0.3), (-1.0, 0, 0.3), (-1.0, 0, 2.8), (0, 0, 2.8), (0, 0, 2.6)], 0.04, 'polypropylene', 12, bend=0.06),
          hollow_pipe('d2a', [(0.35, 0, 0.3), (1.0, 0, 0.3), (1.0, 0, Z0 + L + R * 0.6), (1.6, 0, Z0 + L + R * 0.6), (1.6, 0, Z0 + L + R * 0.5)], 0.04, 'polypropylene', 12, bend=0.06),
          hollow_pipe('in', [(-2.4, 0, Z0 + L + R * 0.6), (-1.6, 0, Z0 + L + R * 0.6), (-1.6, 0, Z0 + L + R * 0.5)], 0.04, 'polypropylene', 12, bend=0.05), nozzle('out', (1.6, 0, Z0 - R * 0.5 - 0.02), (0, 0, -1), 0.04, 0.3)]
    pp += [box('cm', (0.08, 0.06, 0.15), (2.0, 0, 0.35), 'paint_blue_dark')]
    P(m, 'piping', 'Process Piping & Conductivity / Silica Analyser', 'piping', pp, explode=(0, 0, 0.4), ref='dm_piping', section='keep')
    rt = [vessel('at', 0.25, 0.7, 0.006, 'paint_red', heads=('flat', '2:1'), z0=0.05, center=(-2.6, 0.9, 0)), vessel('ct', 0.25, 0.7, 0.006, 'paint_yellow', heads=('flat', '2:1'), z0=0.05, center=(2.6, 0.9, 0))]
    P(m, 'regenerant_tanks', 'Regenerant Tanks: Acid (HCl/H₂SO₄) & Caustic (NaOH) with Dosing', 'chemicals', rt, explode=(0, 0.5, 0), ref='dm_regen', section='keep')
    _pump(m, 'transfer_pump', 'Degassed-Water Transfer Pump', 0.45, -0.6, 0.25, 'dm_piping', explode=(0, -0.4, 0))
    P(m, 'supports', 'Legs', 'structure', [legs(f'lg{k}', R, 0.0, Z0, n=4, cx=x) for k, x in enumerate((-1.6, 1.6))], explode=(0, 0, -0.3), ref='dm_vessel', section='keep')
    particles_path(m, 'ions', 'Cations captured in the cation bed; anions in the anion bed', lambda i, s: ((-1.6 if i % 2 == 0 else 1.6) + 0.2 * math.cos(i), 0.08, Z0 + L - 0.1 - (0.6 + 0.15 * ((i * 0.37) % 1)) * min(1.0, s * 1.5)), 12,
                   mat='paint_green', r=0.012)
    m.flow('air', [(0.45, 0.4, 0.75), (0.25, 0.05, 0.75), (0, 0.1, 1.0), (0, 0.1, 2.8)], 'air', 0.012, 0.3)
    droplets(m, 'co2', 'CO₂ stripped in the degasser', -0.15, 0.15, 1.3, 2.6, n=6, mat='air', y=0.08, r=0.015)
    m.flow('water', [(-2.5, 0, Z0 + L + R * 0.6), (-1.6, 0.05, Z0 + L), (-1.6, 0.05, Z0), (-1.6, 0, 0.3), (-1.0, 0, 0.3), (-1.0, 0, 2.8), (0, 0.05, 2.6), (0, 0.05, 0.4), (1.0, 0, 0.3),
                     (1.0, 0, Z0 + L + R * 0.6), (1.6, 0.05, Z0 + L), (1.6, 0.05, Z0), (1.6, 0, Z0 - R * 0.5 - 0.3)], 'water', 0.018, 0.5)
    _press(m, [cyl('pc', R + 0.04, Z0 + 0.15, Z0 + 0.95, 'pressure_7', 48, center=(-1.6, 0, 0), r_in=R + 0.02), cyl('pa', R + 0.04, Z0 + 0.15, Z0 + 0.95, 'pressure_2', 48, center=(1.6, 0, 0), r_in=R + 0.02)],
           'Ion exchange swaps salts for H⁺ and OH⁻', 'The cation resin exchanges Ca²⁺, Mg²⁺, Na⁺ for H⁺ (water becomes acidic); the degasser blows out the CO₂ formed from bicarbonate; the anion resin '
           'exchanges Cl⁻, SO₄²⁻, silica for OH⁻; H⁺ + OH⁻ → H₂O. Resins are regenerated with acid and caustic when exhausted (rising conductivity/silica or sodium slip). Typical outlet < 5–10 µS/cm, silica < ~ 0.1 mg/L.')
    return m.export(out)


# =============================================================== EQ-304 Mixed bed polisher
def mixed_bed_polisher(out):
    m = _model('mixed_bed_polisher', 'Mixed-Bed Ion-Exchange Polisher')
    R, Z0, L = 0.45, 0.6, 1.6
    _ix_vessel(m, 'mb', 'Mixed-Bed Vessel (rubber-lined)', 0.0, R, Z0, L, [(Z0 + 0.05, Z0 + 0.15, 'sand', 'Support Layer')], 'mb')
    mix = m.part('mixed_resin', 'Intimately Mixed Cation + Anion Resin (separated by backwash before regeneration)', 'media', explode=(0, -0.5, 0), info={'ref': 'mb_resin'})
    for k in range(10):
        z = Z0 + 0.17 + 0.07 * k
        mt = 'resin_cation' if k % 2 else 'resin_anion'
        ms = mix.add(lathe(f'mx{k}', [(0.0, z), (R - 0.013, z), (R - 0.013, z + 0.07), (0.0, z + 0.07)], mt, 48, a0=0.0, a1=math.pi, cap_mat=mt), smooth_angle=30)
        target = (Z0 + 0.17 + (0.0 if mt == 'resin_cation' else 0.35)) + 0.07 * (k // 2) - z
        m.keyframes(ms, 'Operate', 'location', [(1 + f, (0, 0, target * smooth_pulse(f / OPERATE_FRAMES, 0.25, 0.3, 0.25))) for f in range(OPERATE_FRAMES + 1)])
    sv = [box('sw', (0.12, 0.5, 0.6), (-R - 0.45, 0.25, Z0 + 0.9), 'paint_blue_dark'), cyl('swl', 0.03, 0.0, Z0 + 0.6, 'paint_grey', 12, center=(-R - 0.45, 0.25, 0)),
          hollow_pipe('swp', [(-R - 0.39, 0.25, Z0 + 1.0), (-R + 0.02, 0.25, Z0 + 1.0)], 0.025, 'paint_blue', 8),
          hollow_pipe('ai', [(-1.0, 0, 0.3), (-0.2, 0, 0.3), (-0.2, 0, Z0 - R * 0.5)], 0.025, 'paint_blue', 8, bend=0.04),
          box('sg', (0.06, 0.04, 0.5), (R + 0.04, 0, Z0 + 0.5), 'glass'), box('cm', (0.12, 0.08, 0.15), (0.8, 0, 0.55), 'paint_blue_dark'), cyl('cmp', 0.02, 0.0, 0.48, 'paint_grey', 8, center=(0.8, 0, 0)),
          hollow_pipe('smp', [(0.0, 0.0, Z0 - R * 0.5 - 0.05), (0.0, 0.0, 0.3), (0.8, 0.0, 0.3), (0.8, 0.0, 0.48)], 0.01, 'stainless', 8, bend=0.03)]
    P(m, 'instruments_air', 'Valve Nest, Air-Mix Line, Sight Glass & Conductivity / Silica Analyser', 'control', sv, explode=(0, 0, 0.3), ref='mb_control', section='keep')
    P(m, 'supports', 'Legs', 'structure', legs('lg', R, 0.0, Z0, n=4), explode=(0, 0, -0.3), ref='mb_vessel', section='keep')
    m.flow('water', [(0, 0, Z0 + L + R * 0.5 + 0.3), (0, 0.05, Z0 + L - 0.1), (0, 0.05, Z0 + 0.1), (0, 0, Z0 - R * 0.5 - 0.3)], 'water', 0.018, 0.3)
    _press(m, [cyl('qz', R + 0.04, Z0 + 0.15, Z0 + 0.9, 'pressure_1', 48, r_in=R + 0.02)], 'Thousands of tiny demineralisers in series',
           'In service the cation and anion beads are mixed, so the water meets alternate H⁺ and OH⁻ exchange sites thousands of times — like countless two-bed units in series. This "polishes" water to very '
           'high purity (conductivity < ~ 0.1 µS/cm, silica < ~ 10–20 µg/L) for high-pressure boilers and electronics. For regeneration the resins are separated by backwashing (lighter anion on top), '
           'regenerated separately, then re-mixed with air (the animation shows the separation and remixing).')
    return m.export(out)


# =============================================================== EQ-305 Water softener
def water_softener(out):
    m = _model('water_softener', 'Twin Water Softener (Sodium-Cycle Ion Exchange) with Brine Tank')
    R, Z0, L = 0.3, 0.3, 1.3
    for k, x in enumerate((-0.5, 0.3)):
        _ix_vessel(m, f'softener_{k + 1}', f'Softener Vessel {k + 1} (' + ('in service' if k == 0 else 'regenerating') + ')', x, R, Z0, L,
                   [(Z0 + 0.03, Z0 + 0.1, 'sand', 'Gravel'), (Z0 + 0.1, Z0 + 0.9, 'resin_cation', 'Cation Resin (Na⁺ form)')], 'ws', mat='paint_blue', distributor=True)
    hd = [join(f'mv{k}', [box(f'mvb{k}', (0.25, 0.2, 0.18), (x, 0, Z0 + L + R * 0.5 + 0.12), 'paint_grey'), cyl(f'mvt{k}', 0.06, Z0 + L + R * 0.5 + 0.2, Z0 + L + R * 0.5 + 0.3, 'paint_blue_dark', 16, center=(x, 0, 0))]) for k, x in enumerate((-0.5, 0.3))]
    hd += [hollow_pipe('in', [(-1.2, 0, Z0 + L + 0.6), (0.3, 0, Z0 + L + 0.6)], 0.03, 'polypropylene', 12), box('ctl', (0.15, 0.1, 0.2), (-0.1, 0.25, Z0 + L + 0.6), 'paint_grey')]
    P(m, 'control_valves', 'Multiport Control Valves, Meter-Based Controller & Headers', 'control', hd, explode=(0, 0, 0.4), ref='ws_valves', section='keep')
    bt = csg('bt', [cyl('bto', 0.32, 0.0, 1.1, 'polypropylene', 48, center=(1.2, 0, 0))], [cyl('bti', 0.3, 0.03, 1.2, 'polypropylene', 48, center=(1.2, 0, 0))], 'polypropylene')
    sb = lathe('sb', [(0.0, 0.03), (0.3, 0.03), (0.3, 0.35), (0.0, 0.42)], 'powder', 48, a0=0.0, a1=math.pi, center=(1.2, 0, 0), cap_mat='powder')
    bw = lathe('bw', [(0.0, 0.03), (0.299, 0.03), (0.299, 0.6), (0.0, 0.6)], 'brine', 48, a0=0.0, a1=math.pi, center=(1.2, 0, 0), cap_mat='brine')
    P(m, 'brine_tank', 'Brine Tank with Salt Bed & Brine Well', 'tank', [bt, cyl('bwl', 0.05, 0.03, 1.0, 'polypropylene', 16, center=(1.4, 0.15, 0))], explode=(0.4, 0, 0), ref='ws_brine')
    pbr = P(m, 'brine', 'Saturated Brine & Salt', 'fluid', [bw, sb], explode=(0.4, -0.3, 0), ref='ws_brine', section='keep')
    P(m, 'brine_line', 'Brine Draw Line', 'piping', hollow_pipe('bl', [(1.4, 0.15, 1.0), (1.4, 0.15, 1.3), (0.3, 0.15, 1.3), (0.3, 0.15, Z0 + L + R * 0.5 + 0.03)], 0.015, 'polypropylene', 8, bend=0.03),
      explode=(0, 0.3, 0.3), ref='ws_brine', section='keep')
    P(m, 'supports_outlet', 'Vessel Legs & Soft-Water Outlet Header', 'structure', [legs(f'lg{k}', R, 0.0, Z0, n=4, cx=x) for k, x in enumerate((-0.5, 0.3))] +
      [hollow_pipe('so', [(0.3, 0, Z0 - R * 0.5), (0.3, 0, 0.08), (-1.3, 0, 0.08)], 0.03, 'polypropylene', 12, bend=0.04), cyl('so2', 0.03, 0.08, Z0 - R * 0.5, 'polypropylene', 12, center=(-0.5, 0, 0))],
      explode=(0, 0, -0.3), ref='ws_vessel', section='keep')
    particles_path(m, 'hardness', 'Ca²⁺/Mg²⁺ captured by the resin (Na⁺ released)', lambda i, s: (-0.5 + 0.15 * math.cos(i), 0.08, Z0 + 0.9 - 0.7 * s * ((i * 0.37) % 1 + 0.3)), 10, mat='paint_red', r=0.012)
    m.flow('hard_water', [(-1.3, 0, Z0 + L + 0.6), (-0.5, 0, Z0 + L + 0.6), (-0.5, 0.05, Z0 + L), (-0.5, 0.05, Z0 + 0.05), (-0.5, 0, 0.08), (-1.4, 0, 0.08)], 'water', 0.015, 0.3)
    m.flow('brine', [(1.4, 0.15, 0.3), (1.4, 0.15, 1.3), (0.3, 0.15, 1.3), (0.3, 0.05, Z0 + L - 0.1), (0.3, 0.05, Z0 + 0.2)], 'flow_discharge', 0.012, 0.3)
    _press(m, [cyl('hz', R + 0.04, Z0 + 0.1, Z0 + 0.9, 'pressure_7', 48, center=(-0.5, 0, 0), r_in=R + 0.02)], 'Hardness exchanged for sodium',
           'Hard water passes down through cation resin in the sodium form: Ca²⁺ and Mg²⁺ are held by the resin and Na⁺ is released, so the water no longer forms scale (outlet hardness typically < 1 mg/L as CaCO₃). '
           'When the resin is exhausted it is regenerated with strong brine (NaCl ~ 10 %), which pushes the hardness off again; twin units give continuous soft water.')
    return m.export(out)


# =============================================================== EQ-306 Degasser tower
def degasser_tower(out):
    m = _model('degasser_tower', 'Forced-Draught Degasser (Decarbonator) Tower')
    R, Z0, H = 0.45, 1.0, 2.2
    tw = csg('tw', [cyl('two', R + 0.015, Z0, Z0 + H, 'polypropylene', 64)], [cyl('twi', R, Z0 - 0.1, Z0 + H + 0.1, 'polypropylene', 64)], 'polypropylene')
    P(m, 'tower', 'Tower Shell (FRP/PP)', 'vessel', [tw, cyl('tp', R + 0.015, Z0 + H, Z0 + H + 0.03, 'polypropylene', 64)], explode=(0, 0.6, 0), ref='dg_tower')
    P(m, 'packing', 'Random Packing — PP rings/saddles (high surface area for gas transfer)', 'internals', half(packing('pk', R - 0.01, Z0 + 0.5, Z0 + 1.8), 'rubber'), explode=(0, -0.5, 0), ref='dg_packing', section='keep')
    ds = [cyl('dsp', R - 0.02, Z0 + 1.95, Z0 + 1.97, 'polypropylene', 48)] + [cyl(f'dh{k}', 0.02, Z0 + 1.97, Z0 + 2.05, 'polypropylene', 8, center=(0.25 * math.cos(TAU * k / 6), 0.25 * math.sin(TAU * k / 6), 0)) for k in range(6)]
    ds += [half(mesh_pad('me', R - 0.01, Z0 + 2.05, Z0 + 2.12), 'steel')]
    P(m, 'distributor_eliminator', 'Water Distributor Tray & Mist Eliminator', 'internals', ds, explode=(0, -0.4, 0.4), ref='dg_distributor', section='keep')
    sp = join('spj', [_rect_tank('sp', -0.7, 0.7, 1.2, Z0, mat='polypropylene', t=0.03), csg('spc', [box('spco', (1.46, 1.26, 0.03), (0, 0, Z0 - 0.015), 'polypropylene')], [cyl('spch', R, Z0 - 0.1, Z0 + 0.1, 'polypropylene', 64)], 'polypropylene')])
    P(m, 'sump', 'Covered Degassed-Water Sump (tower sits on the cover)', 'tank', sp, explode=(0, 0.5, -0.3), ref='dg_sump')
    P(m, 'sump_water', 'Degassed Water', 'fluid', _water_box('sw', -0.7, 0.7, 1.2, 0.03, Z0 - 0.25), explode=(0, -0.4, -0.2), ref='dg_sump', section='keep')
    bh = csg('bh', [cyl('bho', 0.22, -0.12, 0.12, 'paint_blue', 48, axis='Y', center=(1.1, 0, Z0 + 0.3))], [cyl('bhi', 0.19, -0.1, 0.1, 'paint_blue', 48, axis='Y', center=(1.1, 0, Z0 + 0.3))], 'paint_blue')
    P(m, 'blower', 'Air Blower & Inlet Duct', 'air', [bh, hollow_pipe('bd', [(0.9, 0, Z0 + 0.3), (R, 0, Z0 + 0.3)], 0.08, 'polypropylene', 16)], explode=(0.4, 0, 0), ref='dg_blower', section='keep')
    _fan_rotor(m, 'blower_rotor', 'Blower Impeller', (1.1, 0, Z0 + 0.3), 'Y', 0.16, 'dg_blower', revs=6)
    nz = [hollow_pipe('in', [(-1.2, 0, Z0 + H + 0.3), (0, 0, Z0 + H + 0.3), (0, 0, Z0 + 2.0)], 0.04, 'polypropylene', 12, bend=0.06), nozzle('vent', (0, 0, Z0 + H + 0.03), (0, 0, 1), 0.08, 0.2)]
    P(m, 'nozzles', 'Water Inlet & Air/CO₂ Vent', 'nozzles', nz, explode=(0, 0, 0.4), ref='dg_tower', section='keep')
    droplets(m, 'water_film', 'Water trickling down over the Packing', -0.3, 0.3, Z0 + 1.95, Z0 - 0.2, n=12, mat='water', y=0.1, r=0.012)
    droplets(m, 'air_up', 'Air rising and carrying CO₂ out', -0.25, 0.25, Z0 + 0.35, Z0 + H + 0.2, n=8, mat='air', y=0.25, r=0.015)
    m.flow('water', [(-1.3, 0, Z0 + H + 0.3), (0, 0.05, Z0 + 2.0), (0, 0.05, Z0 - 0.2)], 'water', 0.02, 0.3)
    m.flow('air', [(1.4, 0, Z0 + 0.3), (0, 0.15, Z0 + 0.35), (0, 0.15, Z0 + H + 0.3)], 'air', 0.02, 0.3)
    _bands_z(m, [(Z0 + 1.4, Z0 + 1.8, 7), (Z0 + 0.9, Z0 + 1.4, 4), (Z0 + 0.5, Z0 + 0.9, 1)], R, 'CO₂ concentration falls down the tower',
             'After cation exchange, bicarbonate has turned into dissolved CO₂ (carbonic acid). Air blown up through the packing strips it out (Henry\'s law: the air has almost no CO₂), typically down to ~ 5 mg/L, '
             'which greatly reduces the load — and regenerant use — on the anion exchanger.', kind='pressure')
    return m.export(out)


# =============================================================== EQ-307 Chemical preparation tank
def chemical_preparation_tank(out):
    m = _model('chemical_preparation_tank', 'Chemical (Polymer / Lime / Coagulant) Preparation Tank with Powder Feeder')
    R, Z0, H = 0.55, 0.3, 1.3
    agitated_tank(m, 'cp_', R, Z0, H, 'Preparation Tank', 'cpt', liquid='brine', imp='pbt', revs=2, open_top=False)
    hp = join('hp', [lathe('hpp', [(0.06, 2.35), (0.08, 2.35), (0.3, 2.8), (0.28, 2.8), (0.06, 2.37)], 'stainless', 4, a0=math.pi / 4, a1=math.pi / 4 + TAU, center=(-0.9, 0, 0)), box('bt', (0.5, 0.5, 0.06), (-0.9, 0, 2.82), 'stainless')])
    sc = join('sc', [cyl('scb', 0.05, -0.9, -0.3, 'stainless', 16, axis='X', center=(0, 0, 2.3)), cyl('scm', 0.06, -1.15, -0.95, 'paint_motor', 16, axis='X', center=(0, 0, 2.3)), cyl('scd', 0.04, 2.0, 2.3, 'stainless', 12, center=(-0.3, 0, 0))])
    P(m, 'powder_feeder', 'Bag-Tip Hopper & Volumetric Screw Feeder (dry chemical)', 'feeder', [hp, sc], explode=(-0.4, 0, 0.4), ref='cpt_feeder', section='keep')
    wm = [hollow_pipe('wl', [(-1.5, 0.35, 2.1), (-0.2, 0.35, 2.1), (-0.2, 0.3, Z0 + H + 0.2)], 0.025, 'paint_blue', 12, bend=0.05), box('fm', (0.1, 0.08, 0.1), (-1.0, 0.35, 2.1), 'paint_blue_dark'),
          box('lt', (0.12, 0.12, 0.12), (0.3, 0.3, Z0 + H + 0.35), 'paint_blue_dark'), cyl('lts', 0.03, Z0 + H, Z0 + H + 0.3, 'stainless', 12, center=(0.3, 0.3, 0)), nozzle('out', (R, 0, Z0 + 0.15), (1, 0, 0), 0.04, 0.3)]
    P(m, 'water_instruments', 'Dilution-Water Line with Flowmeter, Level Transmitter & Outlet to Dosing Pumps', 'control', wm, explode=(0, 0.3, 0.3), ref='cpt_control', section='keep')
    P(m, 'supports', 'Legs', 'structure', legs('lg', R, 0.0, Z0, n=4), explode=(0, 0, -0.3), ref='cpt_tank', section='keep')
    particles_path(m, 'powder', 'Powder wetted and dissolved', lambda i, s: (-0.3 + 0.3 * s * math.cos(i), 0.05 + 0.2 * s, 2.0 - (2.0 - Z0 - 0.5) * s), 10, mat='powder', r=0.012, scale_fn=lambda i, s: max(0.05, 1.0 - 0.9 * s))
    m.flow('powder', [(-0.9, 0, 2.7), (-0.9, 0, 2.3), (-0.3, 0, 2.3), (-0.3, 0, Z0 + H + 0.1)], 'sand', 0.015, 0.3)
    m.flow('water', [(-1.6, 0.35, 2.1), (-0.2, 0.35, 2.1), (-0.2, 0.3, Z0 + H)], 'water', 0.015, 0.3)
    m.flow('solution', [(R - 0.1, 0, Z0 + 0.15), (R + 0.5, 0, Z0 + 0.15)], 'flow_discharge', 0.015, 0.2)
    _press(m, [cyl('cz', R + 0.05, Z0, Z0 + H, 'pressure_5', 64, r_in=R + 0.03)], 'Make-down: wetting, dissolving, ageing',
           'Dry chemicals must be wetted evenly and dissolved without lumps ("fish-eyes" with polymer). The feeder doses powder in proportion to the dilution water to reach the target strength '
           '(polymer often ~ 0.1–0.5 %, lime milk ~ 5–10 %). Polymer solutions need gentle mixing and ageing time (~ 30–60 min) to fully uncoil before use.')
    return m.export(out)


# =============================================================== EQ-308 Chemical injection skid
def chemical_injection_skid(out):
    m = _model('chemical_injection_skid', 'Chemical Injection Skid (Duty/Standby Diaphragm Metering Pumps)')
    sk = [box('sk', (2.0, 1.2, 0.08), (0, 0, 0.04), 'paint_grey'), csg('bd', [box('bdo', (2.0, 1.2, 0.15), (0, 0, 0.155), 'paint_yellow')], [box('bdi', (1.94, 1.14, 0.15), (0, 0, 0.19), 'paint_yellow')], 'paint_yellow')]
    P(m, 'skid_bund', 'Skid Base & Spill Bund', 'structure', sk, explode=(0, 0, -0.3), ref='ci_skid', section='keep')
    tk = vessel('tk', 0.3, 0.9, 0.006, 'polypropylene', heads=('flat', '2:1'), z0=0.25, center=(-0.6, 0.1, 0))
    P(m, 'storage_tank', 'Day Tank (chemical storage) with Level Gauge', 'tank', [tk, box('lg', (0.03, 0.03, 0.7), (-0.6 - 0.31, 0.1, 0.7), 'glass')], explode=(-0.3, 0.3, 0), ref='ci_tank')
    pl = P(m, 'chemical', 'Chemical in the Day Tank', 'fluid', liquid_v('cm', 0.29, 0.25, 0.9, head='flat', mat='brine', cx=-0.6, cy=0.1), explode=(-0.3, -0.2, 0), ref='ci_tank', section='keep')
    animate_level(m, pl, 0.89, 0.06, lambda t: 1 - t)
    for k, y in enumerate((-0.25, 0.3)):
        body = join(f'mp{k}', [box(f'mpb{k}', (0.25, 0.2, 0.2), (0.35, y, 0.4), 'paint_blue'), cyl(f'mpm{k}', 0.08, 0.48, 0.8, 'paint_motor', 24, axis='X', center=(0, y, 0.4)),
                               cyl(f'mph{k}', 0.1, 0.1, 0.22, 'stainless', 32, axis='X', center=(0, y, 0.4)), cyl(f'sk{k}', 0.04, 0.4, 0.45, 'paint_grey', 16, center=(0.35, y, 0))])
        P(m, f'metering_pump_{k + 1}', f'Diaphragm Metering Pump {k + 1} ' + ('(duty)' if k == 0 else '(standby)') + ': gearbox, motor, liquid end, stroke-length knob', 'pumps', body, explode=(0.3, -0.4 if k == 0 else 0.4, 0), ref='ci_pumps', section='keep')
        dp = cyl(f'dph{k}', 0.085, 0.085, 0.095, 'ptfe', 32, axis='X', center=(0, y, 0.4))
        pd = P(m, f'diaphragm_{k + 1}', f'Diaphragm {k + 1} (flexes to pump)', 'pumps', dp, explode=(0.3, -0.6 if k == 0 else 0.6, 0.2), ref='ci_pumps', section='keep', pivot=(0.09, y, 0.4))
        if k == 0:
            keys_loop(m, pd, lambda t: (0.6 + 0.4 * math.sin(TAU * 4 * t), 1, 1), 'scale')
    acc = [cyl('cc', 0.04, 0.3, 1.0, 'glass', 16, center=(-0.1, -0.45, 0)), vessel('pd', 0.07, 0.2, 0.004, 'stainless', heads=('2:1', '2:1'), z0=0.75, center=(0.8, -0.25, 0)),
           box('psv', (0.08, 0.08, 0.12), (0.8, 0.0, 0.62), 'paint_red'), box('bpv', (0.08, 0.08, 0.1), (0.9, -0.25, 0.55), 'brass'), pressure_gauge('pg', (0.7, -0.4, 0.62), r=0.035, facing=(0, -1, 0))]
    P(m, 'accessories', 'Calibration Column, Pulsation Dampener, Pressure Relief, Back-Pressure Valve & Gauge', 'accessories', acc, explode=(0, -0.4, 0.3), ref='ci_accessories', section='keep')
    pp = [hollow_pipe('suc', [(-0.6, 0.1, 0.28), (-0.6, -0.25, 0.28), (0.1, -0.25, 0.28), (0.1, -0.25, 0.4)], 0.012, 'polypropylene', 8, bend=0.03),
          hollow_pipe('dis', [(0.1, -0.25, 0.5), (0.1, -0.25, 0.62), (0.8, -0.25, 0.62), (1.4, -0.25, 0.62), (1.4, -0.25, 0.3), (1.8, -0.25, 0.3)], 0.012, 'stainless', 8, bend=0.03),
          hollow_pipe('main', [(1.6, -1.0, 0.3), (1.6, 0.8, 0.3)], 0.08, 'paint_blue', 24), cyl('quill', 0.01, 0.3, 0.45, 'stainless', 8, center=(1.6, -0.25, 0))]
    P(m, 'piping_quill', 'Suction & Discharge Lines and Injection Quill into the Process Main', 'piping', pp, explode=(0, 0, 0.3), ref='ci_quill', section='keep')
    add_tracers(m, 'pulses', 'Chemical pulses delivered with each stroke', [(0.1, -0.25, 0.45), (0.1, -0.25, 0.62), (1.4, -0.25, 0.62), (1.4, -0.25, 0.3), (1.6, -0.25, 0.3)], n=6, radius=0.015, mat='flow_discharge')
    m.flow('dosing', [(-0.6, 0.1, 0.3), (0.1, -0.25, 0.3), (0.1, -0.25, 0.62), (1.4, -0.25, 0.62), (1.6, -0.25, 0.3)], 'flow_discharge', 0.012, 0.3)
    m.flow('process', [(1.6, -1.1, 0.3), (1.6, 0.9, 0.3)], 'water', 0.02, 0.3)
    _press(m, [box('dzb', (0.7, 0.02, 0.02), (1.05, -0.25, 0.66), 'pressure_7')], 'Accurate, pressure-independent dosing',
           'A diaphragm metering pump delivers a fixed volume per stroke; flow is set by stroke length and stroke frequency (VFD). The back-pressure valve keeps a steady discharge pressure so dosing stays accurate, '
           'the pulsation dampener smooths flow, the relief valve protects against a closed outlet, and the calibration column verifies actual output (draw-down test).')
    return m.export(out)


# ===================================================================== metadata
def _std(*items):
    return [{'id': i, 'title': t, 'relevance': r, 'edition': 'to be verified'} for i, t, r in items]


def _c(fn, cons, mat, op='—', fm=('—',), insp=('Visual',)):
    return C(fn, cons, mat, op, list(fm), list(insp))


_WT = _std(('AWWA / Ten States Standards', 'Recommended Standards for Water Works', 'Design criteria.'), ('WHO Guidelines for Drinking-water Quality', 'Water quality', 'Targets.'))
_IX = _std(('ASME BPVC VIII-1', 'Pressure vessels', 'IX vessels.'), ('VGB-S-010 / EPRI guidelines', 'Boiler water quality', 'Make-up water targets (to be verified).'))
from pumpforge.plantkit import agitated_tank as _at  # noqa: E402  (keeps import for META helpers)


def _thk(ref):
    return {ref + '_tank': _c('Holds water; launder collects overflow.', 'Concrete tank, floor slope.', 'Concrete/steel.'), ref + '_zones': _c('Clear and sludge zones.', '—', '—'),
            ref + '_feedwell': _c('Calms inflow.', 'Feedwell.', 'Steel.'), ref + '_rake': _c('Moves sludge to the pit.', 'Rake arms.', 'Steel.', 'Slow.', ['Torque overload'], ['Torque']), ref + '_drive': _c('Turns rakes.', 'Bridge drive.', '—')}


def _agt(ref):
    return {ref + '_tank': _c('Holds liquid.', 'Tank with baffles.', 'Concrete/steel/PE.'), ref + '_slurry': _c('Process liquid.', '—', '—'),
            ref + '_agitator': _c('Mixes.', 'Shaft and impeller.', 'Stainless/coated.', '—', ['Wear'], ['Inspect']), ref + '_drive': _c('Drives agitator.', 'Motor and gearbox.', '—')}


def _ixc(ref):
    return {ref + '_vessel': _c('Pressure vessel for resin.', 'Lined steel/FRP vessel.', 'Rubber-lined steel / FRP.'), ref + '_resin': _c('Exchanges ions.', 'Resin beads on support layer.', 'Polystyrene-DVB resin.', '—', ['Fouling, attrition, oxidation'], ['Capacity test, analysis']),
            ref + '_internals': _c('Even flow distribution.', 'Distributor and underdrain laterals.', 'PP/stainless.', '—', ['Broken nozzles → resin loss'], ['Inspect'])}


META = {
    'clariflocculator': {'summary': ('A clariflocculator combines flocculation and clarification in one circular tank. Coagulated raw water enters a central compartment where slow paddles grow flocs; the water then flows outward under the skirt into the clarifier zone, where flocs settle and are raked to a central sludge pit while clear water overflows the peripheral weir.'),
                         'classification': {'family': 'Water treatment', 'type': 'Circular clariflocculator'}, 'model_configuration': {'animation': 'Paddles and rakes turn; flocs grow and settle'},
                         'standards': _WT, 'references': ['MWH — Water Treatment: Principles and Design'],
                         'components': {**_thk('cfl'), 'cfl_floc': _c('Grows flocs.', 'Flocculation compartment, paddle flocculator.', 'Concrete/steel.'), 'cfl_piping': _c('Inlet, dosing, outlet.', 'Pipes.', 'DI/steel.')}},
    'flash_mixer': {'summary': ('A flash mixer disperses coagulant through the raw water within seconds using a high-speed impeller, so the chemical reacts uniformly before flocculation.'),
                    'classification': {'family': 'Water treatment', 'type': 'Mechanical rapid mixer'}, 'model_configuration': {'animation': 'Fast impeller; coagulant disperses'},
                    'standards': _WT, 'references': ['MWH — Water Treatment'],
                    'components': {**_agt('fmx'), 'fmx_piping': _c('Inlet, dosing, outlet.', 'Pipes.', 'DI/PVC.')}},
    'flocculation_tank': {'summary': ('A flocculation tank gently stirs coagulated water so tiny particles collide and stick together into large flocs that settle easily. Horizontal paddle reels in three stages run at decreasing speeds.'),
                          'classification': {'family': 'Water treatment', 'type': 'Horizontal paddle flocculator (tapered)'}, 'model_configuration': {'stages': 3, 'animation': 'Reels turn; flocs grow'},
                          'standards': _WT, 'references': ['MWH — Water Treatment'],
                          'components': {'ft_tank': _c('Basin.', 'Concrete basin with baffles.', 'Concrete.'), 'ft_paddles': _c('Gentle mixing.', 'Paddle reels.', 'Steel/FRP.', '—', ['Bearing wear'], ['Inspect']), 'ft_drive': _c('Variable-speed drive.', 'Gearmotors.', '—')}},
    'lamella_clarifier': {'summary': ('A lamella clarifier uses a pack of closely spaced inclined plates. Each plate adds settling area, so particles only fall a short distance before sliding down into the sludge hopper, while clear water rises to the launders.'),
                          'classification': {'family': 'Water treatment', 'type': 'Inclined-plate settler'}, 'model_configuration': {'animation': 'Particles settle onto plates'},
                          'standards': _WT, 'references': ['MWH — Water Treatment'],
                          'components': {'lc_tank': _c('Tank and hopper.', 'Steel tank.', 'Coated steel/stainless.'), 'lc_plates': _c('Settling area.', 'Inclined plates.', 'PP/PVC/stainless.', '—', ['Fouling'], ['Clean']), 'lc_launders': _c('Collect clear water.', 'Launders with weirs.', 'Stainless.')}},
    'chlorination_system': {'summary': ('A gas chlorination system draws chlorine from ton containers under vacuum. The chlorinator meters the gas, an ejector dissolves it into a water stream, and the solution is injected into the contact tank to disinfect the water.'),
                            'classification': {'family': 'Disinfection', 'type': 'Vacuum gas chlorination'}, 'model_configuration': {'animation': 'Solution dispersed; rotameter float'},
                            'standards': _std(('Chlorine Institute Pamphlets', 'Chlorine handling and equipment', 'Safe practice.'), ('AWWA B301', 'Liquid chlorine', 'Product.')), 'references': ['White\'s Handbook of Chlorination'],
                            'components': {'cl_containers': _c('Chlorine storage.', 'Ton containers on scale.', 'Steel.'), 'cl_regulator': _c('Converts to vacuum; auto switchover.', 'Vacuum regulators.', 'PVC/Hastelloy.', '—', ['Leaks'], ['Ammonia test']),
                                           'cl_chlorinator': _c('Meters gas.', 'Rotameter panel.', 'PVC.'), 'cl_ejector': _c('Creates vacuum; dissolves gas.', 'Ejector and lines.', 'PVC.'), 'cl_contact': _c('Contact time.', 'Baffled tank, diffuser.', 'Concrete.'),
                                           'cl_safety': _c('Detects leaks.', 'Gas detector.', '—', '—', ['Sensor drift'], ['Bump test'])}},
    'uv_disinfection_system': {'summary': ('A closed-vessel UV system disinfects water by passing it close to UV lamps housed in quartz sleeves. UV-C light inactivates bacteria, viruses and protozoa; automatic wipers keep sleeves clean and a sensor monitors intensity.'),
                               'classification': {'family': 'Disinfection', 'type': 'Closed-vessel UV reactor'}, 'model_configuration': {'lamps': 5, 'animation': 'Lamps glow; wiper travels'},
                               'standards': _std(('US EPA UVDGM', 'UV Disinfection Guidance Manual', 'Validation.'), ('DVGW W 294 / ÖNORM M 5873', 'UV devices', 'Certification.')), 'references': ['US EPA UVDGM'],
                               'components': {'uv_chamber': _c('Reactor.', 'Stainless chamber.', '316L.'), 'uv_sleeves': _c('Protect lamps.', 'Quartz sleeves.', 'Quartz.', '—', ['Fouling'], ['Wiper, cleaning']), 'uv_lamps': _c('Emit UV-C.', 'LP/MP lamps.', '—', '—', ['Ageing'], ['Hours, sensor']),
                                              'uv_wiper': _c('Cleans sleeves.', 'Wiper.', 'EPDM.'), 'uv_control': _c('Power and monitoring.', 'Ballasts, sensor.', '—')}},
    'ozonation_system': {'summary': ('An ozonation system produces ozone on site by passing oxygen through a corona discharge, then bubbles it through water in a contact tank. Ozone disinfects and oxidises colour, taste/odour compounds and micro-pollutants; off-gas ozone is destroyed before venting.'),
                         'classification': {'family': 'Disinfection / oxidation', 'type': 'Corona-discharge ozone with diffuser contactor'}, 'model_configuration': {'animation': 'Corona glow; bubbles'},
                         'standards': _std(('IOA guidelines', 'International Ozone Association practice', 'Design.'),), 'references': ['Rakness — Ozone in Drinking Water Treatment'],
                         'components': {'oz_oxygen': _c('Oxygen feed.', 'LOX tank or PSA.', '—'), 'oz_generator': _c('Makes ozone.', 'Generator vessel, dielectrics.', 'Stainless/glass.', 'Cooling critical.', ['Dielectric failure'], ['Monitor']),
                                        'oz_power': _c('HV/MF power.', 'Power supply.', '—'), 'oz_contactor': _c('Contact.', 'Baffled covered tank.', 'Concrete.'), 'oz_diffusers': _c('Fine bubbles.', 'Ceramic diffusers.', 'Ceramic/PTFE.'),
                                        'oz_destructor': _c('Destroys off-gas ozone.', 'Thermal/catalytic destructor.', 'Stainless.')}},
    'demineralization_plant': {'summary': ('A demineralization plant removes dissolved salts by ion exchange. A strong-acid cation unit exchanges cations for H⁺, a degasser strips CO₂, and a strong-base anion unit exchanges anions for OH⁻, producing water for boilers and processes.'),
                               'classification': {'family': 'Water treatment', 'type': 'Two-bed demineraliser with degasser'}, 'model_configuration': {'animation': 'Ions captured; CO₂ stripped'},
                               'standards': _IX, 'references': ['Dow/DuPont ion exchange manuals'],
                               'components': {**_ixc('dm'), 'dm_degasser': _c('Removes CO₂.', 'Degasser tower, sump, blower.', 'PP/FRP.'), 'dm_piping': _c('Interconnections and analysis.', 'Pipes, analysers.', 'PP/lined steel.'),
                                              'dm_regen': _c('Regenerants.', 'Acid and caustic tanks.', 'PE/steel.')}},
    'mixed_bed_polisher': {'summary': ('A mixed-bed polisher contains cation and anion resins mixed together, producing very high-purity water. For regeneration the resins are separated by backwashing, regenerated separately and re-mixed with air.'),
                           'classification': {'family': 'Water treatment', 'type': 'Mixed-bed ion exchange'}, 'model_configuration': {'animation': 'Resins separate and remix'},
                           'standards': _IX, 'references': ['Ion exchange manuals'],
                           'components': {**_ixc('mb'), 'mb_control': _c('Valves, air mix, monitoring.', 'Valve nest, analyser.', '—')}},
    'water_softener': {'summary': ('A water softener removes hardness by exchanging calcium and magnesium for sodium on cation resin. Twin vessels alternate so one is always in service while the other regenerates with brine.'),
                       'classification': {'family': 'Water treatment', 'type': 'Twin sodium-cycle softener'}, 'model_configuration': {'animation': 'Hardness captured; brine draw'},
                       'standards': _std(('NSF/ANSI 44', 'Residential cation exchange softeners', 'Performance (similar principles industrially).'),), 'references': ['Ion exchange manuals'],
                       'components': {**_ixc('ws'), 'ws_valves': _c('Control regeneration.', 'Multiport valves, controller.', '—'), 'ws_brine': _c('Brine supply.', 'Brine tank, salt, draw line.', 'PE.')}},
    'degasser_tower': {'summary': ('A forced-draught degasser removes dissolved CO₂ from water after cation exchange. Water trickles down over packing while a blower sends air up; the CO₂ transfers into the air and is vented.'),
                       'classification': {'family': 'Water treatment', 'type': 'Forced-draught packed decarbonator'}, 'model_configuration': {'animation': 'Water trickles; air rises'},
                       'standards': _IX, 'references': ['Ion exchange manuals'],
                       'components': {'dg_tower': _c('Contact column.', 'FRP/PP tower.', 'FRP/PP.'), 'dg_packing': _c('Gas transfer area.', 'Random packing.', 'PP.'), 'dg_distributor': _c('Even water spread; mist removal.', 'Tray, eliminator.', 'PP.'),
                                      'dg_sump': _c('Collects water.', 'Sump.', 'PP/lined.'), 'dg_blower': _c('Supplies air.', 'Blower and duct.', '—')}},
    'chemical_preparation_tank': {'summary': ('A chemical preparation tank makes up solutions such as polymer, lime milk or coagulant from dry powder and water. A screw feeder doses powder, the agitator dissolves it, and the solution is held for ageing before dosing.'),
                                  'classification': {'family': 'Chemical systems', 'type': 'Make-down / preparation tank'}, 'model_configuration': {'animation': 'Powder dissolves'},
                                  'standards': _std(('Maker standards', 'Polymer make-down systems', 'Design.'),), 'references': ['Water chemical handling guides'],
                                  'components': {**_agt('cpt'), 'cpt_feeder': _c('Doses powder.', 'Hopper, screw feeder.', 'Stainless.'), 'cpt_control': _c('Water, level, outlet.', 'Flowmeter, LT.', '—')}},
    'chemical_injection_skid': {'summary': ('A chemical injection skid doses a precise flow of chemical into a process line. Diaphragm metering pumps draw from a day tank and deliver through a pulsation dampener and back-pressure valve to an injection quill.'),
                                'classification': {'family': 'Chemical systems', 'type': 'Duty/standby metering pump skid'}, 'model_configuration': {'animation': 'Diaphragm pulses; tank level falls'},
                                'standards': _std(('API 675', 'Positive displacement pumps — controlled volume', 'Metering pumps.'),), 'references': ['API 675'],
                                'components': {'ci_skid': _c('Base and bund.', 'Skid with spill bund.', 'Steel.'), 'ci_tank': _c('Day storage.', 'Tank.', 'PE/PP.'), 'ci_pumps': _c('Meter chemical.', 'Diaphragm pumps.', 'PVDF/PTFE/316.', '—', ['Diaphragm rupture, valve fouling'], ['Calibration']),
                                               'ci_accessories': _c('Accuracy and protection.', 'Calibration column, dampener, PSV, BPV.', '—'), 'ci_quill': _c('Delivers into process.', 'Lines and injection quill.', 'Stainless/PVC.')}},
}
BUILDERS = {k: globals()[k] for k in META}
