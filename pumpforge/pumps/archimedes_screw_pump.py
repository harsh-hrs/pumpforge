"""
Archimedes Screw Pump — an inclined open screw (3 helical flights welded to a
central tube) turns slowly in a close-fitting trough.  Each flight scoops water
from the lower basin and lifts it in pockets to the upper outlet.  Inclination
30 deg, upper bearing + gear reducer + motor at the top, submerged lower bearing.
"""
import math
from mathutils import Matrix, Vector
from pumpforge.core import Model, lathe, lathe_split, ring_profile, cyl, box, csg, split, join, merge_halves, split_many, TAU
from pumpforge.shapes import twisted_extrude
from pumpforge.parts import add_motor_h, add_tracers
from pumpforge.common_meta import C

ID = 'archimedes_screw_pump'
ANG = math.radians(30)
LS = 3.6          # screw length
RO, RT = 0.5, 0.16
LEAD = 1.3
NF = 3


def flights_profile(n_per=10):
    """Three thin radial blades from tube to outer radius (cross-section)."""
    pts = []
    t = 0.012
    for k in range(NF):
        a = TAU * k / NF
        da = t / RO
        dt = t / RT
        pts += [(RT * math.cos(a - dt), RT * math.sin(a - dt)), (RO * math.cos(a - da), RO * math.sin(a - da)),
                (RO * math.cos(a + da), RO * math.sin(a + da)), (RT * math.cos(a + dt), RT * math.sin(a + dt))]
        # arc along tube to next blade
        a2 = TAU * (k + 1) / NF
        for i in range(1, 8):
            b = a + dt + (a2 - dt - a - dt) * i / 8
            pts.append((RT * math.cos(b), RT * math.sin(b)))
    return pts


def build(out_dir):
    m = Model(ID, 'Archimedes Screw Pump (Inclined, Open Trough)', 'D · Special-Purpose Pumping Systems', META)
    # everything below is built in the screw's local frame (axis +X, lower end at x = 0, axis at z = 0)
    parts_local = []
    fl = twisted_extrude('flights', flights_profile(), 0.25, LS, LEAD, 'paint_blue_dark', axis='X', hand=1, steps=360)
    tube = cyl('tube', RT, 0.0, LS + 0.25, 'paint_blue_dark', 64, axis='X', ch=0.01)
    ends = [cyl('st_lo', 0.06, -0.2, 0.0, 'steel', 32, axis='X'), cyl('st_hi', 0.07, LS + 0.25, LS + 0.75, 'steel', 32, axis='X')]
    p = m.part('screw', 'Screw (Central Tube + 3 Helical Flights)', 'rotating_element', explode=(0, 0, 0.0), info={'ref': 'arch_screw'})
    p.add(join('screw', [fl, tube] + ends), smooth_angle=50); p.spin('X', 0.5)
    parts_local.append(p)
    tr = lathe('trough', [(RO + 0.015, 0.1), (RO + 0.25, 0.1), (RO + 0.25, LS + 0.1), (RO + 0.015, LS + 0.1)], 'paint_grey', 64,
               a0=0.55 * math.pi, a1=1.45 * math.pi, axis='X', cap_mat='paint_grey')
    p = m.part('trough', 'Trough (Concrete/Steel, Close Clearance)', 'structure', explode=(0, 0, -0.6), info={'ref': 'arch_trough'})
    p.add(tr, smooth_angle=40)
    parts_local.append(p)
    lb = join('lower_bearing', [cyl('lbh', 0.12, -0.3, -0.12, 'paint_blue', 48, axis='X', ch=0.01),
                                box('lbs', (0.18, 0.2, 0.5), (-0.21, 0, -0.3), 'paint_blue', bevel=0.01)])
    p = m.part('lower_bearing', 'Lower (Submerged) Bearing & Support', 'bearings', explode=(-0.5, 0, 0), info={'ref': 'arch_lower_bearing'})
    p.add(lb, smooth_angle=40)
    parts_local.append(p)
    ub = join('upper_bearing', [cyl('ubh', 0.13, LS + 0.35, LS + 0.55, 'paint_blue', 48, axis='X', ch=0.01),
                                box('ubs', (0.24, 0.3, 0.45), (LS + 0.45, 0, -0.32), 'paint_blue', bevel=0.01)])
    p = m.part('upper_bearing', 'Upper Bearing (Radial + Thrust)', 'bearings', explode=(0.4, 0, 0.2), info={'ref': 'thrust_bearing'})
    p.add(ub, smooth_angle=40)
    parts_local.append(p)
    gb = join('reducer', [box('gb', (0.4, 0.5, 0.5), (LS + 0.8, 0, 0.05), 'paint_grey', bevel=0.03),
                          box('gbb', (0.45, 0.55, 0.06), (LS + 0.8, 0, -0.23), 'paint_grey', bevel=0.01)])
    p = m.part('gear_reducer', 'Gear Reducer (High Ratio)', 'power_transmission', explode=(0.7, 0, 0.4), info={'ref': 'gear_reducer_a'})
    p.add(gb, smooth_angle=40)
    parts_local.append(p)
    n0 = len(m.parts)
    add_motor_h(m, 'm_', LS + 1.05, 0.0, 0.16, 0.48, -0.23, 0.03, 0.05, explode_dx=1.2, revs=10)
    parts_local += m.parts[n0:]
    # tilt: put lower end at (0,0,0.55) and rotate all parts about Y by -ANG (raise the +X end)
    T = Matrix.Translation((0.0, 0.0, 0.55)) @ Matrix.Rotation(-ANG, 4, 'Y')
    for p in parts_local:
        p.pivot = T @ p.pivot
        p.node.location = p.pivot
        p.node.rotation_euler = (0.0, -ANG, 0.0)
        p.explode = T.to_3x3() @ p.explode
        from pumpforge.core import bl2gl
        p.node['explode_offset'] = bl2gl(p.explode)
    # basins (world frame)
    zlo = 0.55 - 0.1
    xb = math.cos(ANG) * LS
    zt = 0.55 + math.sin(ANG) * LS
    low = csg('lower_basin', [box('lb', (1.6, 1.6, 0.9), (-0.5, 0, 0.45), 'paint_grey', bevel=0.01)],
              [box('lbi', (1.5, 1.5, 0.9), (-0.5, 0, 0.5), 'paint_grey', bevel=0.005), box('lbo', (0.6, 1.2, 0.6), (0.2, 0, 0.75), 'paint_grey')], 'paint_grey')
    p = m.part('lower_basin', 'Inlet Basin (Lower Level)', 'structure', section='split', explode=(-0.6, 0, -0.3), info={'ref': 'arch_basin'})
    p.add_split(*split(low), smooth_angle=40)
    up = csg('outlet', [box('ob', (1.0, 1.5, 0.4), (xb + 0.2, 0, zt - 0.55), 'paint_grey', bevel=0.01)],
             [box('obi', (0.9, 1.4, 0.4), (xb + 0.2, 0, zt - 0.5), 'paint_grey', bevel=0.005)], 'paint_grey')
    p = m.part('outlet_channel', 'Outlet Channel (Upper Level)', 'structure', section='split', explode=(0.6, 0, 0.3), info={'ref': 'arch_basin'})
    p.add_split(*split(up), smooth_angle=40)
    # water pockets as tracers along the screw
    path = []
    for k in range(101):
        s = 0.3 + (LS - 0.3) * k / 100
        a = -math.pi / 2 + 0.25
        local = Vector((s, (RO * 0.75) * math.cos(a + 0.0), (RO * 0.75) * math.sin(a)))
        path.append(tuple(T @ local))
    add_tracers(m, 'water_pockets', 'Water Pockets (Tracers)', [(-0.6, 0.0, 0.55)] + path + [(xb + 0.5, 0.0, zt - 0.45)], n=14, radius=0.05, mat='flow_suction')
    m.flow('flow_water', [(-0.9, 0.0, 0.6), (-0.1, 0.0, 0.5)] + path[::5] + [(xb + 0.6, 0.0, zt - 0.4)], 'flow_suction', 0.03, 0.5)
    return m.export(out_dir)


META = {
    'summary': ('One of the oldest pumps: a large screw — helical flights welded around a central tube — is set at an angle in a '
                'close-fitting trough with its lower end in the inlet basin. As the screw turns slowly, each flight scoops '
                'water and carries it upward in a pocket bounded by the flights and the trough until it spills into the outlet '
                'channel. Flow adjusts itself to the inlet level, efficiency stays high over a wide range, and large solids and '
                'fish can pass, so screws are used for wastewater lift stations, storm water, land drainage and return sludge.'),
    'classification': {'family': 'Positive displacement (open screw) / kinetic lift', 'configuration': 'Inclined open screw in a trough, 3 flights'},
    'model_configuration': {'inclination_deg': 30, 'flights': NF, 'outer_diameter_m': 2 * RO, 'lead_m': LEAD,
                            'speed_note': 'Slow speeds (tens of rpm, decreasing with diameter) — high-ratio gear reducer required.'},
    'standards': [
        {'id': 'DWA-M 525 / national guidance', 'title': 'Screw pump design guidance (wastewater)', 'relevance': 'Design practice for screw pumping stations; confirm local standard.', 'edition': 'to be verified'},
        {'id': 'ANSI/HI 9.8', 'title': 'Pump Intake Design', 'relevance': 'General intake principles (basin layout).', 'edition': 'to be verified'},
    ],
    'references': ['Rorres C., "The Turn of the Screw: Optimal Design of an Archimedes Screw", J. Hydraulic Eng. 2000.', 'Manufacturer screw pump design guides (generic practice).'],
    'components': {
        'arch_screw': C('Lifts water in pockets formed between flights and trough.', 'Steel central tube with 1–3 helical flights welded on; shaft stubs at both ends.', 'Carbon steel (coated), stainless.',
                        'Gap to trough controls leakage back down; filling point depends on inlet level.', ['Flight edge wear', 'Corrosion', 'Fatigue cracks at welds'], ['Gap measurement', 'Coating']),
        'arch_trough': C('Close-fitting bed that seals the pockets.', 'Concrete trough screeded by turning the screw itself, or prefabricated steel trough.', 'Concrete, steel.',
                         'Clearance typically small (mm range, depends on diameter).', ['Erosion/cracking'], ['Gap, surface condition']),
        'arch_lower_bearing': C('Supports the submerged lower end.', 'Grease-lubricated plain or rolling bearing, sealed; or self-lubricating.', 'Steel, bronze, polymer.',
                                'Submerged — sealing and grease supply critical.', ['Seal failure, water ingress'], ['Grease supply check']),
        'arch_basin': C('Inlet and outlet structures.', 'Concrete basins/channels.', 'Concrete.', 'Inlet level determines filling of the screw.', ['Debris build-up'], ['Clean screens']),
        'gear_reducer_a': C('Reduces motor speed to the very low screw speed.', 'Shaft-mounted or foot-mounted helical/bevel reducer, often with V-belt stage.', 'Cast iron, alloy gears.',
                            'High torque.', ['Gear wear', 'Oil leak'], ['Oil level/analysis']),
    },
}

if __name__ == '__main__':
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else 'output')
