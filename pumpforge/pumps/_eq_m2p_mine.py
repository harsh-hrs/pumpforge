"""Mine to Port — Area A01 Mine: detailed real-scale models of the bauxite mining fleet and primary sizing.
Dimensions follow published specification envelopes for each equipment CLASS (generic, unbranded); see META references.
Coordinates: metres, x = forward (machine front), y = left, z = up; cut plane y = 0 keeps +y."""
import math
from mathutils import Matrix, Vector
from pumpforge.core import Model, lathe, cyl, box, join, rotate, extrude_poly, mesh_from, TAU
from pumpforge.valvekit import P
from pumpforge.common_meta import C
from pumpforge import plant3d as K
from pumpforge import mobilekit as MK
from pumpforge.shapes import sweep_tube
from pumpforge.plant3d import rod, bar

V = Vector
CAT = 'M2P · A01 Mine'


def _ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


# =============================================================== 01-HT  Rigid rear-dump haul truck (~90 t class)
def m2p_haul_truck(out):
    FR = 900                                             # 30 s dump cycle, real time
    m = Model('m2p_haul_truck', 'Rigid Rear-Dump Haul Truck (~90 t payload class, mechanical drive)', CAT, META['m2p_haul_truck'], operate_frames=FR)
    WB, RT = 4.57, 1.345                                 # wheelbase, tyre radius (27.00R49 class)
    XF, XR = WB / 2, -WB / 2
    W = 0.77                                             # tyre section width
    YF = 4.16 / 2                                        # front track
    YRI, YRO = 1.925 - 0.48, 1.925 + 0.48                # rear duals (dual centre track 3.85 m, ~0.96 m dual spacing)
    ZD = 3.05                                            # upper deck height
    # ---------------- frame
    fr = []
    for s in (-1, 1):
        y = s * 0.68
        fr.append(box(f'rail{s}', (8.0, 0.26, 0.58), (0.3, y, 1.33), 'mine_yellow', bevel=0.02))
        fr.append(box(f'horn{s}', (0.9, 0.3, 0.95), (-3.55, s * 0.9, 1.75), 'mine_yellow', bevel=0.02))          # body pivot horns
        fr.append(cyl(f'pin{s}', 0.09, 0.72 if s > 0 else -1.08, 1.08 if s > 0 else -0.72, 'steel', 20, axis='Y', center=(-3.55, 0, 2.15)))
        fr.append(box(f'riser{s}', (3.0, 0.26, 0.88), (-2.4, s * 0.68, 2.06), 'mine_yellow', bevel=0.02))        # rear frame kick-up over the axle
        for x in (-1.2, -3.0):
            fr.append(box(f'pad{s}{x}', (0.3, 0.3, 0.1), (x, s * 0.68, 2.55), 'rubber'))                           # body pads (body seats here)
        fr.append(box(f'rsb{s}', (0.4, 0.45, 0.25), (XR + 0.25, s * 1.0, 2.5), 'mine_yellow'))                    # rear strut upper brackets
    for x in (4.25, 2.6, 0.9, -0.9, -3.0):
        fr.append(box(f'xm{x}', (0.3, 1.36, 0.42), (x, 0, 1.33), 'mine_yellow'))
    fr.append(box('bump', (0.5, 4.3, 0.75), (4.55, 0, 1.3), 'mine_yellow', bevel=0.04))
    fr.append(box('tow', (0.15, 0.4, 0.25), (4.85, 0, 1.0), 'steel_dark'))
    for s in (-1, 1):
        fr.append(box(f'hoistbr{s}', (0.4, 0.25, 0.35), (0.9, s * 1.0, 1.2), 'mine_yellow'))                     # hoist cylinder lower mounts
    P(m, 'frame', 'Main Frame (box-section rails, cross-members, front bumper, body pivot horns)', 'structure', fr, explode=(0, 0, -0.9), ref='ht_frame', section='keep')
    # ---------------- wheels
    fw = []
    for s in (-1, 1):
        c = (XF, s * YF, RT)
        fw += [MK.otr_tyre(f'ft{s}', RT, W, c), MK.otr_rim(f'fr{s}', RT, W, c, side=s)]
    P(m, 'front_wheels', 'Front Wheels: 27.00R49-class radial OTR tyres on five-piece rims (steer)', 'running_gear', fw, explode=(0, 0, 0), ref='ht_tyre', section='keep')
    rw = []
    for s in (-1, 1):
        for k, yy in enumerate((YRI, YRO)):
            c = (XR, s * yy, RT)
            rw += [MK.otr_tyre(f'rt{s}{k}', RT, W, c), MK.otr_rim(f'rr{s}{k}', RT, W, c, side=s if k == 1 else -s)]
    P(m, 'rear_wheels', 'Rear Dual Wheels (driven): 4 tyres on five-piece rims', 'running_gear', rw, explode=(0, 0, 0), ref='ht_tyre', section='keep')
    # ---------------- suspension & steering
    su = []
    for s in (-1, 1):
        su.append(cyl(f'fsc{s}', 0.2, 1.45, 2.55, 'mine_yellow', 28, center=(XF, s * 1.45, 0)))                     # strut cylinder
        su.append(cyl(f'fsr{s}', 0.13, 1.0, 1.5, 'chrome', 24, center=(XF, s * 1.45, 0)))                            # strut rod
        su.append(box(f'fsp{s}', (0.5, 0.6, 0.3), (XF, s * 1.6, 1.0), 'steel_dark'))                                  # spindle
        su.append(cyl(f'fsn{s}', 0.42, s * 1.55 if s < 0 else 1.55, s * 1.75 if s < 0 else 1.75, 'steel_dark', 32, axis='Y', center=(XF, 0, RT)) if s > 0 else cyl(f'fsn{s}', 0.42, -1.75, -1.55, 'steel_dark', 32, axis='Y', center=(XF, 0, RT)))
        b, r = MK.hydraulic_cylinder(f'stc{s}', (XF + 0.9, s * 0.45, 1.1), (XF + 0.35, s * 1.35, 1.05), 0.07)
        r = r[0]
        su += [b, r]
        su.append(cyl(f'rsc{s}', 0.2, 2.0, 2.4, 'mine_yellow', 28, center=(XR + 0.25, s * 1.0, 0)))                   # rear strut cylinders (to the frame kick-up)
        su.append(cyl(f'rsr{s}', 0.13, 1.67, 2.05, 'chrome', 24, center=(XR + 0.25, s * 1.0, 0)))
    su.append(K.bar('panhard', (XR + 0.5, -1.0, 1.55), (XR + 0.5, 0.75, 2.05), 0.12, 0.14, 'steel_dark'))              # lateral (panhard) link
    su.append(K.rod('tie', (XF + 0.5, -1.4, 1.0), (XF + 0.5, 1.4, 1.0), 0.06, 'steel_dark'))
    su.append(sweep_tube('afr', [(XR, -0.9, 1.35), (-0.7, 0, 1.15), (XR, 0.9, 1.35)], 0.12, 'mine_yellow', 16))       # rear A-frame to centre ball joint
    P(m, 'suspension', 'Suspension (nitrogen-over-oil struts, rear A-frame) & Steering Cylinders', 'running_gear', su, explode=(0, 0, -0.5), ref='ht_suspension', section='keep')
    # ---------------- drivetrain
    en = [box('crank', (2.1, 1.0, 0.7), (2.55, 0, 1.85), 'paint_motor', bevel=0.05), box('pan', (1.8, 0.8, 0.35), (2.55, 0, 1.35), 'paint_motor')]
    for s in (-1, 1):
        bank = box(f'bank{s}', (2.0, 0.5, 0.55), (0, 0, 0), 'paint_motor', bevel=0.03)
        bank.data.transform(Matrix.Translation((2.55, s * 0.42, 2.38)) @ Matrix.Rotation(-s * 0.52, 4, 'X'))
        en.append(bank)
        vc = box(f'vc{s}', (1.95, 0.32, 0.1), (0, 0, 0), 'steel_dark')
        vc.data.transform(Matrix.Translation((2.55, s * 0.57, 2.66)) @ Matrix.Rotation(-s * 0.52, 4, 'X'))
        en.append(vc)
        en.append(lathe(f'turbo{s}', [(0.0, -0.18), (0.22, -0.16), (0.24, 0.0), (0.22, 0.16), (0.0, 0.18)], 'stainless', 24, axis='Y', center=(1.45, s * 0.55, 2.55)))
        en.append(rod(f'exm{s}', (3.4, s * 0.62, 2.55), (1.5, s * 0.62, 2.55), 0.07, 'steel_dark'))
    en.append(cyl('aftc', 0.22, 1.55, 3.55, 'aluminium', 24, axis='X', center=(0, 0, 2.75)))
    en.append(cyl('fwh', 0.62, 1.3, 1.5, 'paint_motor', 40, axis='X', center=(0, 0, 1.8)))
    P(m, 'engine', 'Diesel Engine (V12, ~32 L, ~750 kW class, twin turbo, air-to-air aftercooled)', 'drive', en, explode=(0.0, 0, 2.4), ref='ht_engine', section='keep')
    rad = [box('core', (0.35, 2.0, 1.4), (4.05, 0, 2.3), 'aluminium'), cyl('fan', 0.75, 3.62, 3.82, 'steel_dark', 32, axis='X', center=(0, 0, 2.3)),
           cyl('shroud', 0.8, 3.6, 3.9, 'mine_yellow', 40, axis='X', center=(0, 0, 2.3), r_in=0.76)]
    for k in range(14):
        rad.append(box(f'gr{k}', (0.03, 2.1, 0.04), (4.3, 0, 1.65 + k * 0.1), 'steel_dark'))
    P(m, 'radiator', 'Radiator, Fan & Shroud (front-mounted cooling module)', 'drive', rad, explode=(1.3, 0, 0), ref='ht_radiator', section='keep')
    tr = [box('trans', (1.4, 0.8, 0.75), (0.45, 0, 1.55), 'paint_motor', bevel=0.05), lathe('tconv', [(0, 1.2), (0.55, 1.2), (0.6, 1.35), (0.55, 1.5), (0, 1.5)], 'paint_motor', 32, axis='X', center=(0, 0, 1.75))]
    tr.append(sweep_tube('dshaft', [(-0.3, 0, 1.45), (XR + 0.6, 0, 1.36)], 0.08, 'steel', 16))
    tr += [cyl(f'uj{k}', 0.12, x - 0.08, x + 0.08, 'steel_dark', 16, axis='X', center=(0, 0, z)) for k, (x, z) in enumerate(((-0.3, 1.45), (XR + 0.6, 1.36)))]
    P(m, 'transmission', 'Torque Converter, 7-speed Planetary Powershift Transmission & Drive Shaft', 'drive', tr, explode=(0, 0, -1.6), ref='ht_transmission', section='keep')
    ax = [cyl('axh', 0.32, -1.25, 1.25, 'mine_yellow', 32, axis='Y', center=(XR, 0, RT)), lathe('diff', [(0, -0.55), (0.45, -0.5), (0.6, 0), (0.45, 0.5), (0, 0.55)], 'mine_yellow', 32, axis='Y', center=(XR, 0, RT))]
    for s in (-1, 1):
        ax.append(cyl(f'brk{s}', 0.58, s * 1.15 if s > 0 else -1.45, s * 1.45 if s > 0 else -1.15, 'steel_dark', 40, axis='Y', center=(XR, 0, RT)))       # oil-cooled disc brakes
        ax.append(cyl(f'fd{s}', 0.6, s * 1.45 if s > 0 else -2.35, s * 2.35 if s > 0 else -1.45, 'paint_grey', 40, axis='Y', center=(XR, 0, RT)))         # planetary final drive
    P(m, 'rear_axle', 'Rear Axle: Differential, Oil-Cooled Multi-Disc Brakes & Planetary Final Drives', 'drive', ax, explode=(0, 0, -1.2), ref='ht_axle', section='keep')
    # ---------------- hood, deck, access
    hd = [box('hood', (3.0, 2.3, 1.45), (2.75, 0, 2.3), 'mine_yellow', bevel=0.04)]
    for s in (-1, 1):
        for k in range(5):
            hd.append(box(f'lv{s}{k}', (0.4, 0.02, 0.06), (2.0 + k * 0.45, s * 1.16, 2.5), 'steel_dark'))
    P(m, 'hood', 'Engine Enclosure (hood) with service doors', 'casing', hd, explode=(0, 0, 1.4), ref='ht_hood', section='split')
    dk = [box('deck', (3.15, 5.4, 0.08), (3.15, 0, ZD - 0.04), 'grating')]
    dk.append(K.handrail('dkr', [(1.6, 2.7, ZD), (4.72, 2.7, ZD), (4.72, -2.7, ZD), (1.6, -2.7, ZD)], 1.0))
    dk.append(K.stair('lad', (4.98, -1.85, 0.75), (4.98, 1.15, ZD), width=0.62))
    dk.append(box('lstep', (0.35, 0.8, 0.04), (4.98, -2.15, 0.55), 'grating'))
    for s in (-1, 1):
        dk.append(box(f'dsup{s}', (0.12, 0.12, ZD - 1.6), (4.6, s * 2.4, (ZD + 1.6) / 2), 'mine_yellow'))
    dk.append(cyl('aircl1', 0.28, 3.4, 4.4, 'mine_yellow', 24, axis='X', center=(0, -1.85, ZD + 0.35)))
    dk.append(cyl('aircl2', 0.28, 3.4, 4.4, 'mine_yellow', 24, axis='X', center=(0, -1.15, ZD + 0.35)))
    dk.append(sweep_tube('exh', [(1.6, -0.62, 2.6), (1.6, -1.6, 2.9), (1.6, -1.6, ZD + 0.9)], 0.11, 'steel_dark', 16))
    dk.append(cyl('muff', 0.24, ZD + 0.1, ZD + 0.75, 'steel_dark', 24, center=(1.6, -1.6, 0)))
    for s in (-1, 1):
        dk.append(MK.headlight(f'hl{s}a', (4.82, s * 1.55, 1.38)))
        dk.append(MK.headlight(f'hl{s}b', (4.82, s * 1.85, 1.38)))
        dk.append(MK.headlight(f'fl{s}', (4.65, s * 2.35, ZD + 1.15)))
        dk.append(MK.mirror(f'mir{s}', (4.6, s * 2.6, ZD + 0.6), (4.75, s * 3.05, ZD + 1.05)))
        dk.append(box(f'mud{s}', (0.04, 0.9, 0.9), (XF - 1.5, s * YF, 1.0), 'rubber'))
    dk += [cyl(f'fsb{k}', 0.12, ZD, ZD + 0.8, 'paint_red', 16, center=(4.3, -2.2 + k * 0.3, 0)) for k in range(2)]      # fire-suppression agent bottles
    dk.append(box('alube', (0.4, 0.3, 0.5), (1.0, -0.95, 1.85), 'paint_grey'))                                              # auto-lube pump/reservoir
    dk.append(K.rod('whip', (4.65, 2.62, ZD + 1.0), (4.65, 2.62, ZD + 4.5), 0.015, 'paint_orange'))                         # buggy whip
    dk.append(box('flag', (0.02, 0.35, 0.25), (4.65, 2.8, ZD + 4.35), 'paint_orange'))
    dk.append(box('rcam', (0.15, 0.15, 0.12), (-3.95, 0, 1.95), 'steel_dark'))                                              # rear camera / radar
    P(m, 'deck', 'Upper Deck, Front Stairway, Handrails, Air Cleaners, Exhaust, Lights, Mirrors, Fire Suppression, Buggy Whip', 'structure', dk, explode=(0.6, 0, 0.8), ref='ht_deck', section='keep')
    cb = [MK.cab('cab', 1.75, 3.55, 0.85, 2.6, ZD, 4.85, door_side=+1)]
    cb.append(box('seat', (0.55, 0.55, 0.5), (2.35, 1.85, ZD + 0.55), 'thermoplastic'))
    cb.append(box('seatb', (0.12, 0.55, 0.75), (2.05, 1.85, ZD + 1.05), 'thermoplastic'))
    cb.append(K.rod('stc', (3.05, 1.85, ZD + 0.6), (2.75, 1.85, ZD + 1.1), 0.04, 'steel_dark'))
    cb.append(lathe('stw', [(0.17, -0.02), (0.2, -0.02), (0.2, 0.02), (0.17, 0.02)], 'thermoplastic', 24, axis='X', center=(2.72, 1.85, ZD + 1.14)))
    cb.append(box('dash', (0.3, 1.5, 0.4), (3.3, 1.72, ZD + 0.9), 'thermoplastic'))
    cb.append(K.rod('gnss', (2.0, 1.1, 4.85), (2.0, 1.1, 5.25), 0.025, 'steel_dark'))
    cb.append(cyl('gnssd', 0.1, 5.25, 5.3, 'paint_white', 16, center=(2.0, 1.1, 0)))
    P(m, 'cab', 'ROPS/FOPS Operator Cab (pressurised, air-conditioned)', 'casing', cb, explode=(0, 1.6, 1.2), ref='ht_cab', section='keep')
    tk = [box('fuel', (1.3, 1.15, 1.15), (0.08, 1.75, 1.6), 'mine_yellow', bevel=0.08), cyl('fcap', 0.08, 2.18, 2.28, 'steel_dark', 16, center=(0.3, 1.75, 0)),
          box('hyd', (1.3, 1.15, 1.15), (0.08, -1.75, 1.6), 'mine_yellow', bevel=0.08), cyl('hsg', 0.05, -0.01, 0.01, 'glass', 16, axis='Y', center=(0.3, -2.34, 1.6)),
          box('batt', (0.6, 0.5, 0.45), (1.3, -1.9, 1.15), 'steel_dark')]
    P(m, 'tanks', 'Fuel Tank (left), Hoist/Brake Hydraulic Tank (right), Battery Box', 'auxiliaries', tk, explode=(0, 0, -0.6), ref='ht_tanks', section='keep')
    # ---------------- dump body (rotates about the pivot pins)
    PIV = V((-3.55, 0, 2.15))
    BW = 2.75
    ZFL = 2.95                                           # body floor underside (clears tyres + bump travel)
    by = [box('flr', (6.4, 2 * BW - 0.1, 0.12), (-1.8, 0, ZFL + 0.06), 'mine_yellow'),
          extrude_poly('tail', [(-5.35, ZFL + 0.35), (-5.0, ZFL), (-5.0, ZFL + 0.12), (-5.3, ZFL + 0.42)], -BW + 0.05, BW - 0.05, 'mine_yellow', plane='XZ')]   # tail chute (raised lip)
    for s in (-1, 1):
        by.append(extrude_poly(f'side{s}', [(-5.35, ZFL), (1.4, ZFL), (1.4, 4.45), (-5.35, 4.45)], s * BW - 0.04 if s > 0 else -BW, s * BW if s > 0 else -BW + 0.04, 'mine_yellow', plane='XZ'))
        by.append(box(f'toprail{s}', (6.8, 0.22, 0.2), (-1.97, s * (BW - 0.05), 4.45), 'mine_yellow', bevel=0.03))
        for k in range(5):
            by.append(box(f'rib{s}{k}', (0.12, 0.12, 1.5), (-4.7 + k * 1.45, s * (BW + 0.05), ZFL + 0.75), 'mine_yellow'))
        by.append(box(f'ej{s}', (0.08, 0.08, 0.9), (XR - 0.95, s * 1.925, ZFL - 0.45), 'steel_dark'))                  # rock ejector (hangs between the duals)
        by.append(box(f'pivbr{s}', (0.45, 0.25, ZFL - 2.0), (-3.55, s * 0.9, (ZFL + 2.0) / 2), 'mine_yellow'))         # body pivot brackets down to the pins
        by.append(box(f'hbr{s}', (0.35, 0.25, 0.3), (-0.6, s * 1.0, ZFL - 0.1), 'mine_yellow'))
    by.append(box('front', (0.08, 2 * BW, 4.45 - ZFL), (1.4, 0, (4.45 + ZFL) / 2), 'mine_yellow'))
    by.append(box('canopy', (3.75, 2 * BW, 0.12), (3.25, 0, 5.05), 'mine_yellow', bevel=0.02))
    by.append(extrude_poly('cslope', [(1.4, 4.45), (1.4, 4.99), (2.2, 4.99)], -BW, BW, 'mine_yellow', plane='XZ'))
    for k in range(5):
        by.append(box(f'cnr{k}', (0.14, 2 * BW - 0.2, 0.16), (1.7 + k * 0.82, 0, 4.91), 'mine_yellow'))                 # transverse canopy ribs
    for k in range(6):
        by.append(box(f'lng{k}', (6.4, 0.16, 0.14), (-1.9, -1.8 + k * 0.72, ZFL - 0.07), 'mine_yellow'))
    pb = P(m, 'body', 'Dump Body (~60 m³ heaped, flat floor with tail chute, canopy over the cab, rock ejectors)', 'casing', by, explode=(-1.0, 0, 1.6), ref='ht_body', section='keep', pivot=tuple(PIV))
    # load (shrinks toward the tail while dumping)
    ld = [box('ldb', (6.4, 2 * BW - 0.3, 4.4 - ZFL - 0.12), (-1.9, 0, (4.4 + ZFL + 0.12) / 2), 'bauxite')]
    heap = cyl('ldh', 1.0, -5.05, 1.25, 'bauxite', 32, axis='X', center=(0, 0, 4.4))
    heap.data.transform(Matrix.Translation((0, 0, 4.4)) @ Matrix.Diagonal((1, 2.45, 0.55, 1)) @ Matrix.Translation((0, 0, -4.4)))
    ld.append(heap)
    pl = P(m, 'payload', 'Payload: ~90 t of run-of-mine bauxite (≈ 60–64 m³ loose, heaped 2:1)', 'payload', ld, explode=(-1.0, 0, 3.0), ref='ht_payload', section='keep', pivot=(-5.35, 0, ZFL + 0.15))
    # hoist cylinders (3-stage telescopic), lower pins on the frame, upper pins on the body
    LO = [V((0.9, s * 1.0, 1.35)) for s in (-1, 1)]
    UP0 = [V((-0.6, s * 1.0, ZFL - 0.15)) for s in (-1, 1)]
    hb, hs = [], [[], [], []]
    for k, s in enumerate((-1, 1)):
        b, st = MK.hydraulic_cylinder(f'hc{s}', LO[k], UP0[k], 0.17, 'mine_yellow', stages=3)
        hb.append(b)
        for j in range(3):
            hs[j].append(st[j])
    pbar = P(m, 'hoist_barrels', 'Hoist Cylinders: barrels (lower pins on the frame)', 'actuator', hb, ref='ht_hoist', section='keep', pivot=tuple(LO[0]))
    pst = [P(m, f'hoist_stage{j + 1}', f'Hoist Cylinders: telescopic stage {j + 1}' + (' (rod eye pinned to the body)' if j == 2 else ''), 'actuator', hs[j], ref='ht_hoist', section='keep', pivot=tuple(LO[0])) for j in range(3)]

    # ---------------- dump-cycle animation
    TMAX = math.radians(48)

    def theta(t):
        if t < 0.05:
            return 0.0
        if t < 0.50:
            return TMAX * _ease((t - 0.05) / 0.45)        # raise ~13.5 s
        if t < 0.62:
            return TMAX
        if t < 0.95:
            return TMAX * (1 - _ease((t - 0.62) / 0.33))  # lower ~10 s, then FLOAT
        return 0.0

    def body_pt(p0, t):
        a = theta(t)
        d = V(p0) - PIV
        # rotation about +Y by -a lifts the front (x > pivot) upward
        x = d.x * math.cos(a) - d.z * math.sin(a)
        z = d.x * math.sin(a) + d.z * math.cos(a)
        return V((PIV.x + x, d.y, PIV.z + z))

    MK.rotate_part_keys(m, pb, lambda t: -theta(t), 'Y')
    MK.animate_cylinder(m, pbar, pst, lambda t: LO[0], lambda t: body_pt(UP0[0], t))
    # payload pivots at the tail with the body and slides out (shrinks toward the tail lip) as the angle passes ~15 deg
    tail = V((-5.35, 0, ZFL + 0.15))

    def pl_scale(t):
        a = theta(t)
        if t > 0.6:
            return 0.05 if t < 0.97 else 1.0              # ~5 % carry-back stays in the body
        f = max(0.0, min(1.0, (math.degrees(a) - 23) / 22))   # moist clayey bauxite starts to slide at ~23°
        return 1.0 - 0.95 * _ease(f)

    kr, kl, ks = [], [], []
    for f in range(FR + 1):
        t = f / FR
        tp = body_pt(tail, t)
        kr.append((1 + f, (0.0, -theta(t), 0.0)))
        kl.append((1 + f, tuple(tp - tail)))
        sc = pl_scale(t)
        ks.append((1 + f, (sc, sc, sc)))
    for mesh in pl.meshes:
        m.keyframes(mesh, 'Operate', 'rotation_euler', kr)
        m.keyframes(mesh, 'Operate', 'location', kl)
        m.keyframes(mesh, 'Operate', 'scale', ks)
    # ---------------- teaching overlays
    pw = [sweep_tube('pw1', [(2.55, 0, 1.85), (1.3, 0, 1.75), (0.45, 0, 1.55), (-0.3, 0, 1.45), (XR + 0.6, 0, 1.36), (XR, 0, RT)], 0.06, 'power', 12),
          sweep_tube('pw2', [(XR, -2.3, RT), (XR, 2.3, RT)], 0.06, 'power', 12)]
    m.overlay('power', join('pwr', pw), 'Power flow: engine → torque converter → transmission → differential → final drives',
              'Diesel power passes through the torque converter (which multiplies torque when starting on a grade) into the planetary powershift transmission, '
              'down the drive shaft to the rear differential and out to the planetary final drives in each rear wheel, which multiply torque again (about 4.8 : 1). '
              'Only the rear duals are driven; the front wheels steer.')
    m.flow('dump', [(-5.4, 0, 3.1), (-6.2, 0, 1.6), (-6.8, 0, 0.3)], 'flow_discharge', 0.08, 0.5)
    m.flow_title, m.flow_desc = 'Material path: body → tail chute → hopper / ROM pad', 'The bauxite slides over the tail chute when the body passes about 23–25°.'
    return m.export(out)


# =============================================================== 01-EX  Hydraulic backhoe excavator (~200 t class)
def _poly_band(pts, half):
    """Outline polygon of a thick polyline in XZ: offset each point by `half` (list or scalar) along the normal."""
    P_ = [V((x, 0, z)) for x, z in pts]
    hs = half if isinstance(half, (list, tuple)) else [half] * len(P_)
    top, bot = [], []
    for i, p in enumerate(P_):
        if i == 0:
            d = P_[1] - P_[0]
        elif i == len(P_) - 1:
            d = P_[-1] - P_[-2]
        else:
            d = (P_[i + 1] - P_[i]).normalized() + (P_[i] - P_[i - 1]).normalized()
        d.normalize()
        n = V((-d.z, 0, d.x))
        top.append((p.x + n.x * hs[i], p.z + n.z * hs[i]))
        bot.append((p.x - n.x * hs[i], p.z - n.z * hs[i]))
    return top + bot[::-1]


def _ry(p, c, a):
    """Rotate point p (x, z) about c by angle a (counter-clockwise in the XZ view, x right / z up)."""
    x, z = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * math.cos(a) - z * math.sin(a), c[1] + x * math.sin(a) + z * math.cos(a))


def _circ_int(c1, r1, c2, r2, pick):
    """Intersection of two circles in the XZ plane; pick(p) -> bool chooses the branch."""
    dx, dz = c2[0] - c1[0], c2[1] - c1[1]
    d = math.hypot(dx, dz)
    d = min(max(d, abs(r1 - r2) + 1e-6), r1 + r2 - 1e-6)
    a = (r1 * r1 - r2 * r2 + d * d) / (2 * d)
    h = math.sqrt(max(0.0, r1 * r1 - a * a))
    xm, zm = c1[0] + a * dx / d, c1[1] + a * dz / d
    s1 = (xm + h * dz / d, zm - h * dx / d)
    s2 = (xm - h * dz / d, zm + h * dx / d)
    return s1 if pick(s1) else s2


def _M_rot_y_about(c, a):
    """4x4: rotation by a (CCW in the XZ view) about the axis parallel to Y through point c=(x, z)."""
    T = Matrix.Translation((c[0], 0, c[1]))
    return T @ Matrix.Rotation(-a, 4, 'Y') @ T.inverted()


def _key_rigid(m, part, mats):
    """Keyframe every mesh of `part` with the rigid world transforms mats[f] (4x4) per frame."""
    p0 = part.pivot
    kr, kl = [], []
    prev = None
    for f, Mx in enumerate(mats):
        R = Mx.to_3x3()
        e = R.to_euler('XYZ', prev) if prev is not None else R.to_euler('XYZ')
        prev = e
        kr.append((1 + f, (e.x, e.y, e.z)))
        kl.append((1 + f, tuple(Mx @ p0 - p0)))
    for mesh in part.meshes:
        m.keyframes(mesh, 'Operate', 'rotation_euler', kr)
        m.keyframes(mesh, 'Operate', 'location', kl)


def _ex_geom():
    """Front-attachment geometry of the ~200 t backhoe at its rest pose (upper-local XZ). Shared by the excavator model and the
    area overview, which drives the same kinematics with its own (top-loading) poses."""
    B0 = (1.4, 3.05)                                     # boom foot pin
    KN = (B0[0] + 4.8 * math.cos(math.radians(62)), B0[1] + 4.8 * math.sin(math.radians(62)))
    A0 = (KN[0] + 3.9 * math.cos(math.radians(15)), KN[1] + 3.9 * math.sin(math.radians(15)))   # boom tip / arm pin
    da = (math.cos(math.radians(-80)), math.sin(math.radians(-80)))
    K0 = (A0[0] + 3.6 * da[0], A0[1] + 3.6 * da[1])      # bucket hinge pin
    na = (-da[1], da[0])                                 # arm normal (points forward / +x side)
    AT = (A0[0] - 1.15 * da[0] + 0.35 * na[0], A0[1] - 1.15 * da[1] + 0.35 * na[1])     # arm crowd-lever pin (above A0)
    BB = (B0[0] + 3.6 * math.cos(math.radians(62)) + 0.55 * math.sin(math.radians(62)), B0[1] + 3.6 * math.sin(math.radians(62)) - 0.55 * math.cos(math.radians(62)))
    BF = (2.5, 2.3)                                      # boom cylinder pins on the frame nose lugs
    BA = (KN[0] + 0.15, KN[1] + 0.85)                    # arm cylinder pin on the boom (top)
    LP = (K0[0] - 0.95 * da[0] + 0.3 * na[0], K0[1] - 0.95 * da[1] + 0.3 * na[1])      # side-link pivot on the arm
    AC = (A0[0] - 0.25 * da[0] + 0.55 * na[0], A0[1] - 0.25 * da[1] + 0.55 * na[1])   # bucket-cylinder pin on the arm
    N0 = (K0[0] + 0.55 * na[0] + 0.05 * da[0], K0[1] + 0.55 * na[1] + 0.05 * da[1])   # H-link pin on the bucket
    R_SL, R_HL = 0.8, 0.85
    pick = lambda p: (p[0] - K0[0]) * na[0] + (p[1] - K0[1]) * na[1] > 0.45            # linkage joint on the cylinder side
    J0 = _circ_int(LP, R_SL, N0, R_HL, pick)
    return dict(B0=B0, KN=KN, A0=A0, da=da, K0=K0, na=na, AT=AT, BB=BB, BF=BF, BA=BA, LP=LP, AC=AC, N0=N0, R_SL=R_SL, R_HL=R_HL, pick=pick, J0=J0, ZF=2.15)


def _ex_mats(G, psi, beta, gamma, kappa):
    """Rigid transforms (from the rest pose, excavator-local) of every moving excavator part for swing psi and boom/arm/bucket
    angles beta/gamma/kappa (radians, relative to rest)."""
    B0, A0, K0, LP, N0, J0 = G['B0'], G['A0'], G['K0'], G['LP'], G['N0'], G['J0']
    ZF = G['ZF']
    Mu = Matrix.Rotation(psi, 4, 'Z')
    Mb = Mu @ _M_rot_y_about(B0, beta)
    Ma = Mb @ _M_rot_y_about(A0, gamma)
    Mk = Ma @ _M_rot_y_about(K0, kappa)
    N = _ry(N0, K0, kappa)
    J = _circ_int(LP, G['R_SL'], N, G['R_HL'], G['pick'])
    a_sl = math.atan2(J[1] - LP[1], J[0] - LP[0]) - math.atan2(J0[1] - LP[1], J0[0] - LP[0])
    Msl = Ma @ _M_rot_y_about(LP, a_sl)
    a_hl = math.atan2(J[1] - N[1], J[0] - N[0]) - math.atan2(J0[1] - N0[1], J0[0] - N0[0])
    Mhl = Ma @ Matrix.Translation((N[0] - N0[0], 0, N[1] - N0[1])) @ _M_rot_y_about(N0, a_hl)
    st = math.atan2(ZF + 0.54 - 0.15, 4.35 - 1.15)        # access stair raised (kept up all shift)
    Mst = Mu @ Matrix.Translation((0, 2.55, 0)) @ _M_rot_y_about((1.15, ZF + 0.54), st) @ Matrix.Translation((0, -2.55, 0))
    out = dict(upper=Mu, power_module=Mu, boom=Mb, arm=Ma, bucket=Mk, bucket_load=Mk, side_links=Msl, h_link=Mhl, access_stair=Mst)
    Mui = Mu.inverted()

    def cyl(key, pa, parent, child_pt):                   # child_pt: current child pin in the upper-local frame
        pb0 = {'boomcyl': G['BB'], 'armcyl': G['AT'], 'bktcyl': J0}[key]
        th0 = math.atan2(pb0[1] - pa[1], pb0[0] - pa[0])
        L0 = math.hypot(pb0[0] - pa[0], pb0[1] - pa[1])
        a = (Mui @ parent) @ V((pa[0], 0, pa[1]))
        dx, dz = child_pt[0] - a.x, child_pt[1] - a.z
        L = math.hypot(dx, dz)
        Mrot = _M_rot_y_about((pa[0], pa[1]), math.atan2(dz, dx) - th0)
        out[key + '_barrel'] = Mu @ Matrix.Translation((a.x - pa[0], 0, a.z - pa[1])) @ Mrot
        ext = L - L0
        out[key + '_rod'] = Mu @ Matrix.Translation((a.x - pa[0] + ext * dx / L, 0, a.z - pa[1] + ext * dz / L)) @ Mrot

    def loc(Mx, p):
        q = (Mui @ Mx) @ V((p[0], 0, p[1]))
        return (q.x, q.z)
    cyl('boomcyl', G['BF'], Mu, loc(Mb, G['BB']))
    cyl('armcyl', G['BA'], Mb, loc(Ma, G['AT']))
    cyl('bktcyl', G['AC'], Ma, loc(Ma, J))
    return out


def m2p_hydraulic_excavator(out):
    FR = 900                                             # 30 s real-time cycle: dig, loaded swing, dump, return
    m = Model('m2p_hydraulic_excavator', 'Hydraulic Backhoe Excavator (~200 t class, diesel)', CAT, META['m2p_hydraulic_excavator'], operate_frames=FR)
    # ---------------- undercarriage (static)
    GA = 4.4 / 2                                         # track gauge / 2 (centre of shoes)
    SW = 0.81                                            # shoe width
    uc = []
    for s in (-1, 1):
        st, mv, _ = MK.crawler_track(f'tk{s}', -3.2, 3.3, s * GA, 0.72, 0.68, SW, shoe_pitch=0.34, rollers=8, carriers=2)
        uc += [st, mv]
    uc.append(box('carbody', (3.2, 2 * GA - SW, 0.9), (0, 0, 1.25), 'mine_yellow', bevel=0.06))
    uc.append(box('carbx', (2.2, 3.6, 0.7), (0, 0, 1.25), 'mine_yellow', bevel=0.06))
    uc.append(cyl('rjoint', 0.35, 1.6, 1.95, 'steel_dark', 24))                                          # centre (rotary) joint
    P(m, 'undercarriage', 'Undercarriage: carbody, track frames, idlers, rollers, sprockets, final drives & track chains', 'running_gear', uc, explode=(0, 0, -1.4), ref='ex_undercarriage', section='keep')
    P(m, 'swing_ring', 'Swing Circle: large slewing bearing with internal ring gear', 'drive',
      [cyl('sbo', 1.75, 1.7, 1.95, 'steel', 72, r_in=1.25), cyl('sbi', 1.55, 1.95, 2.15, 'steel_dark', 72, r_in=1.15)] +
      [box(f'sg{k}', (0.08, 0.12, 0.2), (1.2 * math.cos(TAU * k / 90), 1.2 * math.sin(TAU * k / 90), 1.82), 'steel_dark') for k in range(0, 90, 3)],
      explode=(0, 0, -0.5), ref='ex_swing', section='keep')
    # ---------------- upper structure (swings)
    ZF = 2.15                                            # top of swing bearing = underside of revolving frame
    up = [box('rframe', (5.2, 3.0, 0.55), (-0.6, 0, ZF + 0.27), 'mine_yellow', bevel=0.04)]
    for s in (-1, 1):
        up.append(extrude_poly(f'bfb{s}', [(0.6, ZF + 0.3), (2.0, ZF + 0.3), (1.95, 3.25), (1.1, 3.35), (0.6, 3.0)], s * 0.45 - 0.06, s * 0.45 + 0.06, 'mine_yellow', plane='XZ'))   # boom foot brackets
        up.append(box(f'deckw{s}', (5.6, 0.9, 0.08), (-0.9, s * 1.95, ZF + 0.5), 'grating'))
    up.append(box('cw', (1.4, 4.2, 1.9), (-4.35, 0, ZF + 1.35), 'mine_yellow', bevel=0.12))                        # counterweight
    up.append(box('enghouse', (3.0, 3.4, 1.9), (-2.4, 0, ZF + 1.45), 'mine_yellow', bevel=0.08))                  # power module housing
    for k in range(6):
        up.append(box(f'lou{k}', (0.5, 0.02, 0.06), (-3.3 + k * 0.5, -1.71, ZF + 1.6), 'steel_dark'))
    up.append(box('cool', (0.9, 3.4, 1.7), (-0.5, 0, ZF + 1.35), 'mine_yellow', bevel=0.05))                       # cooler / pump room
    up.append(box('htank', (0.9, 1.1, 1.3), (0.55, -1.2, ZF + 1.15), 'mine_yellow', bevel=0.05))                  # hydraulic tank
    up.append(box('nose', (1.0, 2.0, 0.6), (2.45, 0, ZF + 0.25), 'mine_yellow', bevel=0.04))                       # frame nose carrying the boom-cylinder lugs
    for s_ in (-1, 1):
        up.append(box(f'bclug{s_}', (0.5, 0.08, 0.5), (2.5, s_ * 0.72, 2.35), 'mine_yellow'))
    up.append(box('ftank', (1.3, 1.2, 1.8), (-0.75, -2.05, ZF + 1.4), 'mine_yellow', bevel=0.06))                   # fuel tank (~3,000–3,500 L)
    for s_ in (-1, 1):
        up.append(K.rod(f'gnss{s_}', (-4.6, s_ * 1.6, ZF + 2.3), (-4.6, s_ * 1.6, ZF + 2.8), 0.025, 'steel_dark'))
        up.append(cyl(f'gnssd{s_}', 0.1, ZF + 2.8, ZF + 2.85, 'paint_white', 16, center=(-4.6, s_ * 1.6, 0)))
    up.append(box('alube', (0.4, 0.3, 0.5), (-1.2, 1.9, ZF + 0.8), 'paint_grey'))                                    # auto-lube pump
    up += [cyl(f'fsb{k}', 0.12, ZF + 0.55, ZF + 1.35, 'paint_red', 16, center=(-3.4 + k * 0.3, 2.1, 0)) for k in range(2)]
    up.append(sweep_tube('exhx', [(-2.6, -0.5, ZF + 2.4), (-2.6, -0.5, ZF + 3.0)], 0.12, 'steel_dark', 16))
    up.append(sweep_tube('exhy', [(-2.6, 0.5, ZF + 2.4), (-2.6, 0.5, ZF + 3.0)], 0.12, 'steel_dark', 16))
    up.append(K.handrail('uhr', [(1.0, 2.35, ZF + 0.54), (-3.6, 2.35, ZF + 0.54), (-3.6, -2.35, ZF + 0.54), (1.0, -2.35, ZF + 0.54)], 1.0))
    up.append(K.handrail('uhr2', [(-3.8, 1.65, ZF + 2.4), (-1.0, 1.65, ZF + 2.4), (-1.0, -1.65, ZF + 2.4), (-3.8, -1.65, ZF + 2.4)], 1.0))
    up.append(box('cabriser', (1.6, 1.6, 1.4), (1.25, 1.75, ZF + 1.2), 'mine_yellow', bevel=0.04))
    up.append(MK.cab('cab', 0.45, 2.15, 1.0, 2.55, ZF + 1.9, ZF + 4.1, door_side=+1))
    up.append(box('seat', (0.55, 0.55, 0.5), (1.2, 1.8, ZF + 2.35), 'thermoplastic'))
    for s in (-1, 1):
        up.append(box(f'joy{s}', (0.12, 0.1, 0.35), (1.45, 1.8 + s * 0.4, ZF + 2.4), 'thermoplastic'))
    up.append(box('opg', (0.08, 1.7, 2.0), (2.25, 1.78, ZF + 3.0), 'mine_yellow'))                                # front guard frame
    for k in range(5):
        up.append(box(f'opgb{k}', (0.06, 0.05, 2.0), (2.28, 1.1 + k * 0.34, ZF + 3.0), 'steel_dark'))
    for s in (-1, 1):
        up.append(MK.headlight(f'wl{s}', (2.2, s * 1.4, ZF + 4.0), (1, 0, -0.2)))
        up.append(MK.headlight(f'wlr{s}', (-5.05, s * 1.5, ZF + 2.4), (-1, 0, 0)))
    up = [o for o in up if o is not None]
    pu = P(m, 'upper', 'Revolving Upper Structure: frame, counterweight, power module (engine & pumps), coolers, tanks, walkways', 'casing', up, explode=(-0.8, 0, 1.0), ref='ex_upper', section='keep')
    en = [box('eng', (2.2, 1.2, 1.0), (-2.4, 0, ZF + 1.15), 'paint_motor', bevel=0.05), box('pd', (0.8, 1.2, 0.7), (-1.05, 0, ZF + 1.0), 'paint_grey', bevel=0.04)]
    for k in range(3):
        en.append(cyl(f'pump{k}', 0.2, -0.65, -0.2, 'paint_grey', 20, axis='X', center=(0, -0.45 + k * 0.45, ZF + 1.0)))
    en.append(box('mcv', (1.0, 1.2, 0.6), (0.6, 0.0, ZF + 1.1), 'paint_grey', bevel=0.03))                         # main control valves
    for s in (-1, 1):
        en.append(cyl(f'swm{s}', 0.22, ZF + 0.6, ZF + 1.5, 'paint_grey', 20, center=(-0.2, s * 1.05, 0)))              # swing motors + reducers
        en.append(cyl(f'swr{s}', 0.3, ZF - 0.4, ZF + 0.6, 'mine_yellow', 24, center=(-0.2, s * 1.05, 0)))
    pe = P(m, 'power_module', 'Power Module: diesel engine (~700–800 kW class), pump drive, main hydraulic pumps, control valves, swing motors & reducers', 'drive', en, explode=(0, 0, 2.6), ref='ex_power', section='keep')
    lad = [K.stair('acc', (4.35, 2.55, 0.15), (1.15, 2.55, ZF + 0.54), width=0.7)]
    pl = P(m, 'access_stair', 'Hydraulically Lowered Access Stairway (swing locked while lowered)', 'structure', lad, ref='ex_access', section='keep', pivot=(1.15, 2.55, ZF + 0.54))

    # ---------------- front attachment geometry at the rest pose (upper-local = world at rest)
    G = _ex_geom()
    B0, KN, A0, da, K0, na, AT, BB, BF, BA, LP, AC, N0, R_SL, R_HL, pick, J0 = (G[k] for k in ('B0', 'KN', 'A0', 'da', 'K0', 'na', 'AT', 'BB', 'BF', 'BA', 'LP', 'AC', 'N0', 'R_SL', 'R_HL', 'pick', 'J0'))
    YB = 0.0
    # boom: banana box section
    boom = [extrude_poly('boom', _poly_band([B0, KN, A0], [0.45, 0.7, 0.38]), YB - 0.55, YB + 0.55, 'mine_yellow', plane='XZ')]
    for s in (-1, 1):
        boom.append(cyl(f'bpin{s}', 0.16, YB + s * 0.55 if s > 0 else YB - 0.7, YB + 0.7 if s > 0 else YB - 0.55, 'steel', 20, axis='Y', center=(B0[0], 0, B0[1])))
        boom.append(box(f'bcb{s}', (0.35, 0.18, 0.4), (BB[0], s * 0.62, BB[1]), 'mine_yellow'))
    boom.append(box('bab', (0.4, 0.5, 0.35), (BA[0], 0, BA[1] - 0.1), 'mine_yellow'))
    boom.append(sweep_tube('bhose', [(B0[0] + 0.3, -0.58, B0[1] + 0.6), (KN[0] + 0.2, -0.58, KN[1] + 0.5), (A0[0] - 0.4, -0.58, A0[1] + 0.25)], 0.05, 'rubber', 10))
    pbm = P(m, 'boom', 'Boom (welded box section, banana shape)', 'structure', boom, explode=(0.0, -1.2, 0.8), ref='ex_boom', section='keep', pivot=(B0[0], 0, B0[1]))
    arm = [extrude_poly('arm', _poly_band([AT, A0, K0], [0.33, 0.42, 0.28]), -0.42, 0.42, 'mine_yellow', plane='XZ'),
           cyl('apin', 0.15, -0.6, 0.6, 'steel', 20, axis='Y', center=(A0[0], 0, A0[1])), cyl('kpin', 0.13, -0.75, 0.75, 'steel', 20, axis='Y', center=(K0[0], 0, K0[1])),
           box('acb', (0.35, 0.4, 0.35), (AC[0], 0, AC[1]), 'mine_yellow'), cyl('lpin', 0.1, -0.6, 0.6, 'steel', 16, axis='Y', center=(LP[0], 0, LP[1]))]
    par = P(m, 'arm', 'Arm (stick) with crowd lever', 'structure', arm, explode=(0.8, -1.2, 0.2), ref='ex_arm', section='keep', pivot=(A0[0], 0, A0[1]))
    # bucket: wrapper, side plates, lip, teeth (local shape given relative to K0 with the arm hanging at rest)
    def bk(u, v):                                         # bucket-local (u along -arm normal = mouth side, v along -arm) -> world XZ
        return (K0[0] + u * na[0] + v * da[0], K0[1] + u * na[1] + v * da[1])
    wrap = [(-0.9, -0.1), (0.0, -0.25), (0.6, -0.05), (0.8, 0.6), (0.7, 1.45), (0.35, 2.1), (-0.25, 2.45), (-1.05, 2.45)]
    WB_ = 1.55                                            # half bucket width (~3.1 m)
    pts = [bk(u, v) for u, v in wrap]
    # wrapper as a thin extruded band, side plates as polygons
    band = _poly_band(pts, 0.04)
    bkt = [extrude_poly('wrap', band, -WB_, WB_, 'mine_yellow', plane='XZ')]
    side = pts + [bk(-1.0, 1.9), bk(-1.0, 0.2)]
    for s in (-1, 1):
        bkt.append(extrude_poly(f'sp{s}', side, s * WB_ - (0.05 if s > 0 else 0), s * WB_ + (0 if s > 0 else 0.05), 'mine_yellow', plane='XZ'))
        bkt.append(extrude_poly(f'wp{s}', _poly_band([bk(0.7, 0.6), bk(0.65, 1.6), bk(0.2, 2.25)], 0.05), s * (WB_ - 0.02) - 0.03, s * (WB_ - 0.02) + 0.03, 'steel_dark', plane='XZ'))
        bkt.append(cyl(f'hb{s}', 0.2, s * 0.62 if s > 0 else -0.85, s * 0.85 if s > 0 else -0.62, 'mine_yellow', 20, axis='Y', center=(K0[0], 0, K0[1])))
        bkt.append(cyl(f'nb{s}', 0.17, s * 0.5 if s > 0 else -0.72, s * 0.72 if s > 0 else -0.5, 'mine_yellow', 20, axis='Y', center=(N0[0], 0, N0[1])))
    lip0, lip1 = bk(-0.25, 2.45), bk(-1.05, 2.45)
    bkt.append(extrude_poly('lip', _poly_band([lip0, lip1], 0.07), -WB_, WB_, 'steel_dark', plane='XZ'))
    tdir = V((lip1[0] - lip0[0], 0, lip1[1] - lip0[1])).normalized()
    for k in range(5):
        y = -WB_ + 0.3 + k * (2 * WB_ - 0.6) / 4
        a = V((lip1[0], y, lip1[1]))
        bkt.append(bar(f'ad{k}', a - tdir * 0.15, a + tdir * 0.22, 0.2, 0.16, 'steel_dark', up=(0, 0, 1)))
        bkt.append(bar(f'tt{k}', a + tdir * 0.2, a + tdir * 0.5, 0.17, 0.1, 'steel', up=(0, 0, 1)))
    pbk = P(m, 'bucket', 'Bucket (~11–12 m³ heaped) with cast lip, adapters, teeth and wear plates', 'casing', bkt, explode=(1.2, 0, -0.6), ref='ex_bucket', section='keep', pivot=(K0[0], 0, K0[1]))
    lode = cyl('lode', 1.0, -WB_ + 0.1, WB_ - 0.1, 'bauxite', 24, axis='Y', center=(0, 0, 0))
    c_ = bk(-0.15, 1.25)
    lode.data.transform(Matrix.Translation((c_[0], 0, c_[1])) @ Matrix.Diagonal((0.85, 1, 1.05, 1)))
    ppl = P(m, 'bucket_load', 'Bucket load (~15–17 t of bauxite per pass)', 'payload', [lode], ref='ex_load', section='keep', pivot=(K0[0], 0, K0[1]))
    # linkage
    sl_geo = [K.bar(f'slb{s}', (LP[0], s * 0.5, LP[1]), (J0[0], s * 0.5, J0[1]), 0.12, 0.22, 'mine_yellow', up=(0, 0, 1)) for s in (-1, 1)]
    sl_geo.append(cyl('jpin', 0.1, -0.62, 0.62, 'steel', 16, axis='Y', center=(J0[0], 0, J0[1])))
    psl = P(m, 'side_links', 'Bucket Side Links (arm to linkage joint)', 'actuator', sl_geo, ref='ex_linkage', section='keep', pivot=(LP[0], 0, LP[1]))
    phl = P(m, 'h_link', 'H-Link (power link to the bucket)', 'actuator', [K.bar(f'hl{s}', (N0[0], s * 0.42, N0[1]), (J0[0], s * 0.42, J0[1]), 0.14, 0.26, 'mine_yellow', up=(0, 0, 1)) for s in (-1, 1)], ref='ex_linkage', section='keep', pivot=(N0[0], 0, N0[1]))
    # cylinders (built at rest), each: (pin_a on parent link, pin_b on child link, radius, stages, y offsets)
    CYL = {}

    def mk_cyl(key, pa, pb, r, ys, label, ref):
        bs, ss = [], []
        for y in ys:
            b, st = MK.hydraulic_cylinder(f'{key}{y}', (pa[0], y, pa[1]), (pb[0], y, pb[1]), r, 'mine_yellow', stages=1)
            bs.append(b)
            ss.append(st[0])
        pb_ = P(m, key + '_barrel', label + ' (barrel)', 'actuator', bs, ref=ref, section='keep', pivot=(pa[0], 0, pa[1]))
        pr_ = P(m, key + '_rod', label + ' (rod)', 'actuator', ss, ref=ref, section='keep', pivot=(pa[0], 0, pa[1]))
        CYL[key] = (pb_, pr_, pa, pb)
    mk_cyl('boomcyl', BF, BB, 0.2, (-0.72, 0.72), 'Boom Cylinders (2)', 'ex_cylinders')
    mk_cyl('armcyl', BA, AT, 0.21, (0.0,), 'Arm (Stick) Cylinder', 'ex_cylinders')
    mk_cyl('bktcyl', AC, J0, 0.19, (0.0,), 'Bucket Cylinder', 'ex_cylinders')

    # ---------------- dig – swing – dump cycle (joint angles relative to the rest pose, radians)
    D = math.radians
    # (t, swing, boom, arm, bucket, -) — real-time 30 s cycle; loaded swing ~65° at < 4 rpm
    POSES = [(0.00, 0, 0, 0, 0, 0), (0.05, 0, 0, 0, 0, 0), (0.14, 0, D(-35), D(30), D(20), 0), (0.27, 0, D(-38), D(0), D(-10), 1),
             (0.34, 0, D(-30), D(-15), D(-50), 1), (0.54, D(65), D(26), D(-8), D(-62), 1), (0.62, D(65), D(26), D(18), D(40), 0),
             (0.86, 0, D(0), D(0), D(0), 0), (1.00, 0, 0, 0, 0, 0)]

    def pose(t):
        for i in range(len(POSES) - 1):
            a, b = POSES[i], POSES[i + 1]
            if a[0] <= t <= b[0]:
                u = _ease((t - a[0]) / max(1e-6, b[0] - a[0]))
                return tuple(a[j] + (b[j] - a[j]) * u for j in range(1, 6))
        return POSES[-1][1:]

    def load_scale(t):
        if t < 0.15:
            return 0.02
        if t < 0.34:
            return 0.02 + 0.98 * _ease((t - 0.15) / 0.19)
        if t < 0.56:
            return 1.0
        if t < 0.62:
            return 1.0 - 0.98 * _ease((t - 0.56) / 0.06)
        return 0.02

    PM = {}
    for f in range(FR + 1):
        psi, beta, gamma, kappa, _ = pose(f / FR)
        for k, Mx in _ex_mats(G, psi, beta, gamma, kappa).items():
            PM.setdefault(k, []).append(Mx)
    for part in (pu, pe, pbm, par, pbk, psl, phl, pl):
        _key_rigid(m, part, PM[part.id])
    for key in ('boomcyl', 'armcyl', 'bktcyl'):
        _key_rigid(m, CYL[key][0], PM[key + '_barrel'])
        _key_rigid(m, CYL[key][1], PM[key + '_rod'])
    # bucket load: bucket transform + scale (fills while digging, empties at the dump)
    kr, kl, ks = [], [], []
    prev = None
    for f, Mx in enumerate(PM['bucket']):
        R = Mx.to_3x3()
        e = R.to_euler('XYZ', prev) if prev is not None else R.to_euler('XYZ')
        prev = e
        kr.append((1 + f, (e.x, e.y, e.z)))
        kl.append((1 + f, tuple(Mx @ ppl.pivot - ppl.pivot)))
        sc = load_scale(f / FR)
        ks.append((1 + f, (sc, sc, sc)))
    for mesh in ppl.meshes:
        m.keyframes(mesh, 'Operate', 'rotation_euler', kr)
        m.keyframes(mesh, 'Operate', 'location', kl)
        m.keyframes(mesh, 'Operate', 'scale', ks)
    # ---------------- overlays
    hz = [sweep_tube('hy1', [(-1.0, 0.3, ZF + 1.0), (0.6, 0.3, ZF + 1.1), (BF[0], 0.6, BF[1])], 0.05, 'hydraulic_oil', 10),
          sweep_tube('hy2', [(0.6, -0.3, ZF + 1.1), (B0[0] + 0.3, -0.6, B0[1] + 0.6), (KN[0] + 0.2, -0.6, KN[1] + 0.5), (A0[0] - 0.4, -0.6, A0[1] + 0.25)], 0.05, 'hydraulic_oil', 10)]
    m.overlay('hydraulics', join('hyd', hz), 'Hydraulic power: engine → pumps → control valves → cylinders & motors',
              'The diesel drives several variable-displacement piston pumps. The operator\'s joysticks pilot the main control valves, which send oil at up to ~30–32 MPa '
              'to the boom, arm and bucket cylinders, the swing motors and the travel motors. Pump output is shared electronically so the engine is never overloaded.')
    # bench: the machine works on top and digs ~3 m down to the floor in front (class maximum 8–9 m)
    bench = [box('bench', (14.0, 14.0, 3.2), (-2.6, 0, -1.6), 'ore_layer'), box('bfloor', (14.0, 18.0, 0.3), (11.4, 0, -3.35), 'clay_floor'),
             box('btop', (14.0, 14.0, 0.06), (-2.6, 0, -0.02), 'laterite')]
    P(m, 'bench', 'Working bench (ore horizon) — the backhoe digs below its own track level', 'structure', bench, ref='ex_bench', section='keep')
    m.flow('cycle', [(9.5, 0, -2.6), (5.2, 0, -1.2), (5.0, 0, 3.0), (3.0, 6.0, 6.0)], 'flow_discharge', 0.1, 0.8)
    m.flow_title, m.flow_desc = 'Material path: face → bucket → truck', 'Ore is dug at the face below track level, carried in the bucket and dumped into the truck on the operator side.'
    return m.export(out)


# =============================================================== 01-DZ  Crawler dozer with ripper (~70 t class)
def m2p_crawler_dozer(out):
    FR = 900                                             # 30 s: doze forward, reverse, rip forward, reverse
    m = Model('m2p_crawler_dozer', 'Crawler Dozer with Semi-U Blade and Single-Shank Ripper (~70 t class)', CAT, META['m2p_crawler_dozer'], operate_frames=FR)
    GA = 2.55 / 2
    ZC = 2.15                                            # cab floor
    uc = []
    for s in (-1, 1):
        st, mv, _ = MK.crawler_track(f'tk{s}', -2.6, 2.6, s * GA, 0.6, 0.55, 0.61, shoe_pitch=0.28, rollers=8, carriers=1)
        uc += [st, mv]
        uc.append(box(f'fend{s}', (4.9, 0.75, 0.06), (0.1, s * GA, 1.32), 'mine_yellow'))
        uc.append(cyl(f'trn{s}', 0.14, 1.15 if s > 0 else -1.80, 1.80 if s > 0 else -1.15, 'steel', 16, axis='Y', center=(0.35, 0, 0.62)))   # trunnion stubs between the track strands
    uc.append(box('eqbar', (0.3, 2 * GA + 0.3, 0.25), (0.6, 0, 0.75), 'steel_dark'))                                # equaliser bar
    pu = P(m, 'undercarriage', 'Undercarriage: track roller frames, idlers, sprockets, track chains with single-grouser shoes, equaliser bar', 'running_gear', uc, explode=(0, 0, -1.0), ref='dz_undercarriage', section='keep')
    bd = [box('mframe', (5.0, 1.5, 0.7), (0.1, 0, 1.0), 'mine_yellow', bevel=0.04),
          box('hood', (2.4, 1.7, 1.45), (1.5, 0, 2.15), 'mine_yellow', bevel=0.06), box('grillf', (0.2, 1.75, 1.6), (2.75, 0, 2.05), 'mine_yellow', bevel=0.03),
          box('ftank', (0.85, 2.3, 1.15), (-2.15, 0, 2.0), 'mine_yellow', bevel=0.08), box('deckc', (2.2, 2.5, 0.12), (-1.1, 0, ZC - 0.06), 'grating'),
          box('cabbase', (2.3, 2.0, 0.8), (-0.85, 0, 1.75), 'mine_yellow', bevel=0.04)]                               # encloses the drivetrain below the cab
    for k in range(10):
        bd.append(box(f'gr{k}', (0.04, 1.8, 0.05), (2.86, 0, 1.4 + k * 0.14), 'steel_dark'))
    bd.append(sweep_tube('exh', [(1.6, 0.4, 2.85), (1.6, 0.4, 3.45)], 0.1, 'steel_dark', 14))
    bd.append(cyl('precl', 0.18, 2.88, 3.3, 'mine_yellow', 20, center=(2.0, -0.45, 0)))
    bd.append(cyl('fcap', 0.07, 2.57, 2.65, 'steel_dark', 12, center=(-2.15, 0.8, 0)))
    for s in (-1, 1):
        bd.append(box(f'lcm{s}', (0.35, 0.3, 0.5), (2.45, s * 0.95, 2.45), 'mine_yellow'))                            # lift-cylinder mounts
        bd.append(MK.headlight(f'hl{s}', (2.9, s * 0.7, 2.95)))
        bd.append(K.rod(f'gnss{s}', (-1.8, s * 0.9, ZC + 2.0), (-1.8, s * 0.9, ZC + 2.4), 0.025, 'steel_dark'))
    bd.append(MK.cab('cab', -1.95, -0.1, -1.05, 1.05, ZC, ZC + 2.0, door_side=+1))
    bd.append(box('seat', (0.55, 0.55, 0.5), (-1.25, 0, ZC + 0.47), 'thermoplastic'))
    for s in (-1, 1):
        bd.append(box(f'jy{s}', (0.12, 0.1, 0.3), (-0.95, s * 0.4, ZC + 0.52), 'thermoplastic'))
    bd.append(K.handrail('hrl', [(-2.2, 1.24, ZC), (-0.05, 1.24, ZC)], 1.0))
    bd.append(K.handrail('hrr', [(-2.2, -1.24, ZC), (-0.05, -1.24, ZC)], 1.0))
    for k in range(2):                                                                                               # access steps on the door side
        bd.append(box(f'stp{k}', (0.4, 0.3, 0.04), (-0.8, 1.62, 0.55 + k * 0.45), 'grating'))
    pbody = P(m, 'body', 'Main Frame, Engine Enclosure, Radiator Guard, Fuel Tank & ROPS/FOPS Cab', 'casing', bd, explode=(0, 0, 1.4), ref='dz_body', section='keep')
    dt = [box('eng', (1.9, 1.1, 1.0), (1.4, 0, 1.85), 'paint_motor', bevel=0.05), box('tq', (0.6, 1.0, 0.8), (0.2, 0, 1.6), 'paint_grey', bevel=0.04),
          box('trans', (1.0, 1.0, 0.8), (-0.6, 0, 1.45), 'paint_grey', bevel=0.04)]
    for s in (-1, 1):
        dt.append(cyl(f'fd{s}', 0.48, s * (GA - 0.6) if s > 0 else -GA + 0.3, s * (GA - 0.3) if s > 0 else -GA + 0.6, 'mine_yellow', 32, axis='Y', center=(-2.05, 0, 0.62)))
        dt.append(cyl(f'ss{s}', 0.3, s * 0.5 if s > 0 else -GA + 0.6, s * (GA - 0.6) if s > 0 else -0.5, 'paint_grey', 24, axis='Y', center=(-2.05, 0, 0.62)))
    pdt = P(m, 'drivetrain', 'Drivetrain: diesel engine (~450 kW), torque converter, powershift transmission, steering clutches & brakes, double-reduction final drives', 'drive', dt, explode=(0, 0, 2.4), ref='dz_drive', section='keep')
    # ---------------- blade (semi-U) on push arms pivoting about the trunnions
    TRN = (0.35, 0.62)
    xb = 4.3                                             # blade cutting edge x at rest
    ctrl = [(xb, 0.05), (xb - 0.42, 0.95), (xb - 0.3, 1.75), (xb + 0.02, 2.08)]
    prof = []
    for k in range(13):
        u = k / 12
        b = [(1 - u) ** 3, 3 * u * (1 - u) ** 2, 3 * u * u * (1 - u), u ** 3]
        prof.append((sum(b[i] * ctrl[i][0] for i in range(4)), sum(b[i] * ctrl[i][1] for i in range(4))))
    blade = [extrude_poly('mb', _poly_band(prof, 0.05), -1.85, 1.85, 'mine_yellow', plane='XZ')]
    for s in (-1, 1):
        wing = extrude_poly(f'wing{s}', _poly_band(prof, 0.05), 0.0 if s > 0 else -0.65, 0.65 if s > 0 else 0.0, 'mine_yellow', plane='XZ')
        piv = V((xb - 0.3, s * 1.85, 0))
        wing.data.transform(Matrix.Translation(piv) @ Matrix.Rotation(-s * 0.42, 4, 'Z') @ Matrix.Translation((-piv.x, 0, 0)))
        blade.append(wing)
        blade.append(K.bar(f'pa{s}', (TRN[0], s * 1.75, TRN[1]), (xb - 0.45, s * 1.75, 0.45), 0.22, 0.3, 'mine_yellow', up=(0, 0, 1)))       # push arm (outboard of the track)
        blade.append(K.bar(f'tb{s}', (TRN[0] + 0.6, s * 1.75, TRN[1] + 0.25), (xb - 0.55, s * 1.2, 1.55), 0.1, 0.1, 'steel_dark'))          # tilt brace / tilt cylinder
        blade.append(box(f'eb{s}', (0.3, 0.12, 0.3), (xb + 0.25, s * 2.42, 0.12), 'steel_dark'))                                                 # end bits
    blade.append(box('cedge', (0.12, 3.7, 0.25), (xb + 0.02, 0, 0.12), 'steel_dark'))                                                           # cutting edge
    for k in range(5):
        blade.append(box(f'brc{k}', (0.08, 0.08, 1.5), (xb - 0.62, -1.6 + k * 0.8, 1.0), 'mine_yellow'))
    pbl = P(m, 'blade', 'Semi-U Blade (~4.9 m wide, ~18–19 m³) with cutting edges, end bits, push arms and tilt brace', 'casing', blade, explode=(1.4, 0, 0.3), ref='dz_blade', section='keep', pivot=(TRN[0], 0, TRN[1]))
    soil = cyl('soil', 0.75, -1.8, 1.8, 'laterite', 24, axis='Y', center=(0, 0, 0))
    soil.data.transform(Matrix.Translation((xb + 0.75, 0, 0.6)) @ Matrix.Diagonal((1.0, 1, 0.8, 1)))
    psl = P(m, 'blade_load', 'Material rolling in front of the blade', 'payload', [soil], ref='dz_load', section='keep', pivot=(xb, 0, 0.05))
    LCB = [V((2.45, s * 0.95, 2.45)) for s in (-1, 1)]
    LCT = [V((xb - 0.6, s * 1.1, 1.75)) for s in (-1, 1)]
    lb, ls = [], []
    for k in range(2):
        b_, st = MK.hydraulic_cylinder(f'lc{k}', LCB[k], LCT[k], 0.12, 'mine_yellow', stages=1)
        lb.append(b_)
        ls.append(st[0])
    plb = P(m, 'lift_barrels', 'Blade Lift Cylinders (barrels)', 'actuator', lb, ref='dz_cyl', section='keep', pivot=tuple(LCB[0]))
    pls = P(m, 'lift_rods', 'Blade Lift Cylinders (rods)', 'actuator', ls, ref='dz_cyl', section='keep', pivot=tuple(LCB[0]))
    # ---------------- ripper: parallelogram links (upper and lower rotate about their own pins), carrier translates
    RB_U, RB_L = (-2.8, 1.55), (-2.8, 0.85)              # frame pins
    LV = (-1.2, 1.2)                                     # link vector at the raised position
    rp = [box('rbr', (0.4, 1.1, 2.6), (-2.65, 0, 2.0), 'mine_yellow', bevel=0.03), box('rbt', (0.5, 0.9, 0.3), (-2.6, 0, 3.15), 'mine_yellow')]
    prf = P(m, 'ripper_frame', 'Ripper Mounting Frame', 'structure', rp, ref='dz_ripper', section='keep')
    plu_u = P(m, 'ripper_link_upper', 'Ripper Upper Link (parallelogram)', 'actuator', [K.bar(f'rlu{s}', (RB_U[0], s * 0.4, RB_U[1]), (RB_U[0] + LV[0], s * 0.4, RB_U[1] + LV[1]), 0.14, 0.2, 'mine_yellow', up=(0, 0, 1)) for s in (-1, 1)],
              ref='dz_ripper', section='keep', pivot=(RB_U[0], 0, RB_U[1]))
    plu_l = P(m, 'ripper_link_lower', 'Ripper Lower Link (parallelogram)', 'actuator', [K.bar(f'rll{s}', (RB_L[0], s * 0.4, RB_L[1]), (RB_L[0] + LV[0], s * 0.4, RB_L[1] + LV[1]), 0.14, 0.2, 'mine_yellow', up=(0, 0, 1)) for s in (-1, 1)],
              ref='dz_ripper', section='keep', pivot=(RB_L[0], 0, RB_L[1]))
    cx, cz = RB_L[0] + LV[0], RB_L[1] + LV[1]
    car = [box('rcar', (0.35, 1.0, 0.9), (cx - 0.1, 0, cz + 0.35), 'mine_yellow', bevel=0.03),
           extrude_poly('shank', [(cx - 0.25, cz + 1.25), (cx - 0.05, cz + 1.25), (cx - 0.05, cz - 0.6), (cx - 0.35, cz - 1.0), (cx - 0.45, cz - 0.8), (cx - 0.25, cz - 0.5)], -0.08, 0.08, 'mine_yellow', plane='XZ'),
           extrude_poly('tip', [(cx - 0.35, cz - 1.0), (cx - 0.45, cz - 0.8), (cx - 0.62, cz - 1.08), (cx - 0.5, cz - 1.15)], -0.07, 0.07, 'steel_dark', plane='XZ'),
           extrude_poly('sprot', [(cx - 0.05, cz - 0.6), (cx - 0.08, cz - 0.1), (cx - 0.16, cz - 0.1), (cx - 0.13, cz - 0.65)], -0.085, 0.085, 'steel_dark', plane='XZ')]
    for k in range(3):                                                                                               # depth-setting pin pockets
        car.append(cyl(f'pp{k}', 0.06, -0.09, 0.09, 'steel_dark', 12, axis='Y', center=(cx - 0.15, 0, cz + 0.55 + k * 0.25)))
    prc = P(m, 'ripper_shank', 'Ripper Shank Carrier, Shank (pin-pocket depth setting), Tip & Shank Protector', 'casing', car, explode=(-1.2, 0, 0), ref='dz_ripper', section='keep', pivot=(cx, 0, cz))
    RCB = [V((-2.55, s * 0.32, 3.15)) for s in (-1, 1)]
    PLL = (RB_L[0] + 0.6 * LV[0], RB_L[1] + 0.6 * LV[1])                   # cylinder rod eye on the lower link
    RCT = [V((PLL[0], s * 0.32, PLL[1])) for s in (-1, 1)]
    rb, rs = [], []
    for k in range(2):
        b_, st = MK.hydraulic_cylinder(f'rc{k}', RCB[k], RCT[k], 0.11, 'mine_yellow', stages=1)
        rb.append(b_)
        rs.append(st[0])
    prb = P(m, 'ripper_cyl_barrels', 'Ripper Lift Cylinders (barrels)', 'actuator', rb, ref='dz_cyl', section='keep', pivot=tuple(RCB[0]))
    prs = P(m, 'ripper_cyl_rods', 'Ripper Lift Cylinders (rods)', 'actuator', rs, ref='dz_cyl', section='keep', pivot=tuple(RCB[0]))

    # ---------------- animation (whole machine travels): doze 6 m in F1, reverse, set the tip and rip 3 m forward, lift, reverse
    D = math.radians

    def seg(t, pts):
        for i in range(len(pts) - 1):
            (t0, v0), (t1, v1) = pts[i], pts[i + 1]
            if t0 <= t <= t1:
                return v0 + (v1 - v0) * _ease((t - t0) / max(1e-6, t1 - t0)) if v0 != v1 else v0
        return pts[-1][1]
    X_ = [(0.0, 0.0), (0.10, 0.0), (0.35, 6.0), (0.40, 6.0), (0.55, 0.0), (0.60, 0.0), (0.85, 3.0), (0.89, 3.3), (1.0, 0.0)]
    BA = [(0.0, 0.0), (0.05, 0.0), (0.10, -D(4.5)), (0.35, -D(4.5)), (0.40, D(6)), (0.55, D(6)), (0.60, 0.0), (1.0, 0.0)]
    RA = [(0.0, 0.0), (0.55, 0.0), (0.60, D(22)), (0.68, D(90)), (0.85, D(90)), (0.89, 0.0), (1.0, 0.0)]
    LS = [(0.0, 0.02), (0.12, 0.02), (0.35, 1.0), (0.40, 0.02), (1.0, 0.02)]

    def off(t):
        return seg(t, X_)
    T_ = [Matrix.Translation((off(f / FR), 0, 0)) for f in range(FR + 1)]
    for part in (pu, pbody, pdt, prf):
        _key_rigid(m, part, T_)
    MBL = [T_[f] @ _M_rot_y_about(TRN, seg(f / FR, BA)) for f in range(FR + 1)]
    MRU = [T_[f] @ _M_rot_y_about(RB_U, seg(f / FR, RA)) for f in range(FR + 1)]
    MRL = [T_[f] @ _M_rot_y_about(RB_L, seg(f / FR, RA)) for f in range(FR + 1)]
    MRC = []
    for f in range(FR + 1):
        v = _ry((RB_L[0] + LV[0], RB_L[1] + LV[1]), RB_L, seg(f / FR, RA))
        MRC.append(T_[f] @ Matrix.Translation((v[0] - cx, 0, v[1] - cz)))
    for part, mats in ((pbl, MBL), (plu_u, MRU), (plu_l, MRL), (prc, MRC)):
        _key_rigid(m, part, mats)
    kr, kl, ks = [], [], []
    for f in range(FR + 1):
        Mx = MBL[f]
        e = Mx.to_3x3().to_euler('XYZ')
        kr.append((1 + f, (e.x, e.y, e.z)))
        kl.append((1 + f, tuple(Mx @ psl.pivot - psl.pivot)))
        sc = seg(f / FR, LS)
        ks.append((1 + f, (sc, sc, sc)))
    for mesh in psl.meshes:
        m.keyframes(mesh, 'Operate', 'rotation_euler', kr)
        m.keyframes(mesh, 'Operate', 'location', kl)
        m.keyframes(mesh, 'Operate', 'scale', ks)

    def cyl_keys(pb_, pr_, A, B, child_mats):
        a = (A.x, A.z)
        d0 = (B.x - A.x, B.z - A.z)
        L0 = math.hypot(*d0)
        th0 = math.atan2(d0[1], d0[0])
        mb, mr = [], []
        for f in range(FR + 1):
            b = T_[f].inverted() @ (child_mats[f] @ B)        # child pin in the tractor frame
            dx, dz = b.x - A.x, b.z - A.z
            L = math.hypot(dx, dz)
            Mr = _M_rot_y_about(a, math.atan2(dz, dx) - th0)
            mb.append(T_[f] @ Mr)
            mr.append(T_[f] @ Matrix.Translation(((L - L0) * dx / L, 0, (L - L0) * dz / L)) @ Mr)
        _key_rigid(m, pb_, mb)
        _key_rigid(m, pr_, mr)
    cyl_keys(plb, pls, LCB[0], LCT[0], MBL)
    cyl_keys(prb, prs, RCB[0], RCT[0], MRL)
    m.flow('push', [(xb + 0.6, 0, 0.3), (xb + 3.0, 0, 0.3)], 'flow_discharge', 0.08, 0.6)
    m.flow_title, m.flow_desc = 'Push direction', 'Direction the blade load is pushed; ripping is done travelling forward in first gear.'
    return m.export(out)


# =============================================================== 01-HP / 01-AF / 01-SZ / 01-CV  Primary sizing station
def _sizer_shafts(prefix, x0, x1, ys, zc, R_hub, R_tip, rings, mat_hub='steel_dark', mat_tooth='steel'):
    """Twin toothed shafts along X: hub barrel + rings of 3 horn teeth in a scroll pattern. Shaft B's rings are offset by half a
    ring pitch so each tooth runs between two rings of the other shaft (no clash — the shafts are not phase-locked)."""
    out = []
    pitch = (x1 - x0) / rings
    for j, y in enumerate(ys):
        objs = [cyl(f'{prefix}h{j}', R_hub, x0, x1, mat_hub, 32, axis='X', center=(0, y, zc)),
                cyl(f'{prefix}s{j}', R_hub * 0.45, x0 - 0.5, x1 + 0.6, 'steel', 20, axis='X', center=(0, y, zc))]
        nr = rings if j == 0 else rings - 1
        for r in range(nr):
            x = x0 + pitch * (r + 0.5 + 0.5 * j)
            objs.append(cyl(f'{prefix}r{j}{r}', R_hub * 1.06, x - 0.12, x + 0.12, mat_hub, 32, axis='X', center=(0, y, zc)))
            for k in range(3):
                a = TAU * k / 3 + r * 0.55 + (math.pi / 3 if j else 0.0)
                tooth = extrude_poly(f'{prefix}t{j}{r}{k}', [(R_hub * 0.95, -0.16), (R_tip, -0.06), (R_tip - 0.02, 0.09), (R_hub * 0.95, 0.19)], x - 0.1, x + 0.1, mat_tooth, plane='YZ')
                tooth.data.transform(Matrix.Translation((0, y, zc)) @ Matrix.Rotation(a, 4, 'X'))
                objs.append(tooth)
        out.append(join(f'{prefix}{j}', objs))
    return out


def m2p_primary_sizing_station(out):
    FR = 300
    m = Model('m2p_primary_sizing_station', 'Primary Sizing Station: Two-Sided Truck Dump, Rock Breaker, Apron Feeder, Twin-Shaft Sizer & Discharge Conveyor', CAT,
              META['m2p_primary_sizing_station'], operate_frames=FR)
    ZD = 10.0                                            # tipping-deck level (≈ 6 m above the feeder pans)
    HX0, HX1, HW = -6.0, 6.0, 4.3                        # hopper opening (x range, half-width)
    ZF = 3.9                                             # apron-feeder pan (carry) top level
    FX0, FX1 = -7.0, 8.0                                 # feeder tail / head sprocket centres
    PW = 3.0                                             # pan width (skirt opening 2.6 m ≈ 2 × the 1.2–1.5 m ROM top size)
    SK = 1.3                                             # skirt half-opening (inside the pan side flights)
    SX0, SX1, SZ = 9.4, 13.4, 2.6                        # sizer shaft span and shaft-centre level
    ZB = -0.95                                           # discharge-belt top level (conveyor in a trench under the sizer)
    # ---------------- civil: dump pocket walls, tipping decks, ramps, wheel stops
    cv = []
    for s in (-1, 1):
        yc = s * (HW + 0.4 + 14.0)
        cv.append(box(f'deck{s}', (32.0, 28.0, 0.6), (-4.0, yc, ZD - 0.3), 'concrete'))                                   # pad sized for a 90 t truck to turn and reverse
        cv.append(box(f'mse{s}', (32.0, 28.0, ZD - 0.6), (-4.0, yc, (ZD - 0.6) / 2), 'concrete'))                        # MSE / RC wall block
        cv.append(extrude_poly(f'ramp{s}', [(-20.0, 0.0), (-20.0, ZD), (-34.0, ZD - 1.4), (-34.0, 0.0)], yc - 14.0, yc + 14.0, 'concrete', plane='XZ'))
        cv.append(box(f'ws{s}', (12.5, 0.6, 1.55), (0.0, s * (HW + 0.7), ZD + 0.775), 'paint_yellow'))                  # wheel stop / bund (≥ ½ wheel height of the largest machine: loader)
        for k in range(5):
            cv.append(box(f'wsm{s}{k}', (0.6, 0.62, 0.25), (-5 + k * 2.5, s * (HW + 0.7), ZD + 1.0), 'paint_grey'))
        for xa, xb in ((-20.0, HX0 - 0.3), (HX1 + 0.3, 12.0)):                                                       # deck edges facing the pocket
            cv.append(K.handrail(f'pe{s}{xa}', [(xa, s * (HW + 0.5), ZD), (xb, s * (HW + 0.5), ZD)], 1.1))
        cv.append(box(f'eb{s}', (32.0, 1.5, 1.55), (-4.0, s * (HW + 27.65), ZD + 0.775), 'concrete'))                   # vehicle edge bund (≥ ½ largest wheel)
        cv.append(box(f'ebx{s}', (1.5, 26.9, 1.55), (11.25, s * (HW + 15.45), ZD + 0.775), 'concrete'))
        cv.append(K.handrail(f'dhr{s}', [(-20.0, s * (HW + 28.3), ZD + 1.55), (12.0, s * (HW + 28.3), ZD + 1.55), (12.0, s * (HW + 0.6), ZD + 1.55)], 1.1))
        cv.append(cyl(f'tlm{s}', 0.08, ZD, ZD + 4.0, 'paint_grey', 12, center=(-7.5, s * (HW + 1.5), 0)))                 # traffic light
        cv.append(box(f'tlh{s}', (0.3, 0.3, 0.9), (-7.5, s * (HW + 1.5), ZD + 4.2), 'steel_dark'))
        cv.append(cyl(f'tlr{s}', 0.09, -0.02, 0.02, 'signal_red', 16, axis='X', center=(-7.35, s * (HW + 1.5), ZD + 4.45)))
        cv.append(cyl(f'tlg{s}', 0.09, -0.02, 0.02, 'signal_green', 16, axis='X', center=(-7.35, s * (HW + 1.5), ZD + 4.0)))
    cv.append(box('tailw', (1.0, 2 * HW + 0.8, ZD - (ZF + 0.15)), (HX0 - 0.5, 0, (ZD + ZF + 0.15) / 2), 'concrete'))   # tail wall seals just above the pans
    cv.append(box('headl', (1.0, 2 * HW + 0.8, ZD - (ZF + 2.0)), (HX1 + 0.5, 0, (ZD + ZF + 2.0) / 2), 'concrete'))    # head lintel: ≥ 2 m discharge opening
    cv.append(box('apron', (60.0, 40.0, 0.3), (8.0, 0, -0.15), 'concrete'))
    # conveyor trench under the sizer and drives
    for s in (-1, 1):
        cv.append(box(f'trw{s}', (14.0, 0.3, 2.3), (13.6, s * 2.1, -1.15), 'concrete'))
    cv.append(box('trf', (14.0, 4.5, 0.3), (13.6, 0, -2.45), 'concrete'))
    P(m, 'civil', 'Dump Pocket: tipping pads (sized for a 90 t truck to turn and reverse) on MSE walls with 1.55 m edge bunds, ramps (shown cut short), 1.55 m wheel stops, traffic lights, conveyor trench', 'structure', cv, explode=(0, 0, 0), ref='ps_civil', section='split')
    # ---------------- hopper (steel, lined) inside the pocket
    hp = []
    for s in (-1, 1):
        hp.append(extrude_poly(f'hs{s}', [(s * HW, ZD), (s * (HW + 0.1), ZD), (s * (SK + 0.12), ZF + 1.6), (s * SK, ZF + 1.6)] if s > 0 else
                               [(s * (HW + 0.1), ZD), (s * HW, ZD), (s * SK, ZF + 1.6), (s * (SK + 0.12), ZF + 1.6)], HX0, HX1, 'steel', plane='YZ'))
        for k in range(6):                                # bolted liner segments (AR plate)
            z = ZF + 1.8 + k * (ZD - ZF - 2.0) / 6
            frac = (z - (ZF + 1.6)) / (ZD - ZF - 1.6)
            yy = SK + (HW - SK) * frac
            hp.append(box(f'ln{s}{k}', (11.6, 0.05, 0.9), (0, s * (yy - 0.08), z), 'steel_dark'))
        hp.append(box(f'rbx{s}', (12.0, 0.6, 0.35), (0, s * (HW - 0.3), ZD - 0.4), 'steel_dark'))                      # rock-box ledge (impact)
        hp.append(box(f'sk{s}', (HX1 - HX0 + 2.0, 0.12, 1.6), (0.5, s * SK, ZF + 0.8), 'steel'))                         # skirts inside the pan flights
        hp.append(K.rod(f'spr{s}', (-5.5, s * (HW - 0.3), ZD + 0.2), (5.5, s * (HW - 0.3), ZD + 0.2), 0.04, 'stainless'))  # spray header on the ledge
        for k in range(5):
            hp.append(cyl(f'spn{s}{k}', 0.05, ZD + 0.05, ZD + 0.25, 'brass', 8, center=(-4.4 + k * 2.2, s * (HW - 0.3), 0)))
    for k, x in enumerate((HX0, HX1)):
        hp.append(box(f'hend{k}', (0.12, 2 * HW, ZD - ZF - 2.0), (x, 0, (ZD + ZF + 2.0) / 2), 'steel'))
    for k in range(8):                                    # impact rails under the hopper section
        hp.append(box(f'irl{k}', (0.25, PW - 0.4, 0.15), (-5.0 + k * 1.4, 0, ZF - 0.3), 'steel_dark'))
    P(m, 'hopper', 'Dump Hopper (~200–300 t live): AR-plate liners, rock-box ledges, skirts, impact rails, dust-spray headers', 'casing', hp, explode=(0, 0, 3.5), ref='ps_hopper', section='split')
    # ---------------- rock breaker on a platform over the feeder outlet (off the tipping pads)
    RBc = V((HX1 + 2.0, 0.0, ZD))
    rb = [box('rbplat', (4.0, 10.0, 0.25), (HX1 + 2.5, 0, ZD - 0.12), 'grating'), cyl('rbp', 0.8, ZD, ZD + 1.4, 'concrete', 32, center=(RBc.x, RBc.y, 0)),
          cyl('rbs', 0.7, ZD + 1.4, ZD + 1.9, 'paint_yellow', 32, center=(RBc.x, RBc.y, 0))]
    b0 = RBc + V((0, 0, 2.1))
    b1 = b0 + V((-4.6, 0.0, 2.6))
    b2 = b1 + V((-3.4, 0.0, -3.4))
    rb += [K.bar('rbb', b0, b1, 0.45, 0.6, 'paint_yellow'), K.bar('rbst', b1, b2, 0.35, 0.45, 'paint_yellow'),
           K.bar('rbh', b2, b2 + V((-0.3, 0, -1.9)), 0.4, 0.45, 'steel_dark'), K.rod('rbt', b2 + V((-0.3, 0, -1.9)), b2 + V((-0.36, 0, -2.6)), 0.07, 'steel')]
    rb.append(box('rbcab', (2.0, 1.8, 2.4), (HX1 + 3.6, 3.0, ZD + 1.2), 'paint_grey', bevel=0.04))
    rb.append(box('rbcabw', (0.05, 1.5, 1.0), (HX1 + 2.58, 3.0, ZD + 1.7), 'cab_glass'))
    rb.append(box('rbpp', (1.6, 1.2, 1.3), (HX1 + 3.6, -3.2, ZD + 0.65), 'paint_grey', bevel=0.03))
    rb.append(K.handrail('rbhr', [(HX1 + 0.6, -4.9, ZD), (HX1 + 4.4, -4.9, ZD), (HX1 + 4.4, 4.9, ZD), (HX1 + 0.6, 4.9, ZD)], 1.1))
    P(m, 'rock_breaker', 'Pedestal Rock Breaker over the feeder outlet (boom, stick, ~2 t hammer, power pack, operator cabin) — tipping stops while it works', 'auxiliaries', rb, explode=(2.0, 0, 2.0), ref='ps_breaker', section='keep')
    # ---------------- apron feeder
    af = []
    for s in (-1, 1):
        af.append(box(f'afr{s}', (FX1 - FX0 + 1.0, 0.25, 0.9), ((FX0 + FX1) / 2, s * (PW / 2 + 0.25), ZF - 0.75), 'paint_grey'))
    for k in range(12):                                   # carry rollers
        x = FX0 + 0.8 + k * (FX1 - FX0 - 1.6) / 11
        af.append(cyl(f'cr{k}', 0.17, -PW / 2 + 0.15, PW / 2 - 0.15, 'steel', 16, axis='Y', center=(x, 0, ZF - 0.45)))
    af.append(cyl('hdsh', 0.45, -PW / 2 - 0.3, PW / 2 + 0.3, 'steel_dark', 24, axis='Y', center=(FX1, 0, ZF - 0.55)))
    af.append(cyl('tlsh', 0.42, -PW / 2 - 0.3, PW / 2 + 0.3, 'steel', 24, axis='Y', center=(FX0, 0, ZF - 0.55)))
    for s in (-1, 1):                                     # shaft-mounted planetary drives + motors (2 x ~132–160 kW)
        af.append(cyl(f'afg{s}', 0.48, PW / 2 + 0.35 if s > 0 else -PW / 2 - 1.05, PW / 2 + 1.05 if s > 0 else -PW / 2 - 0.35, 'paint_blue', 28, axis='Y', center=(FX1, 0, ZF - 0.55)))
        mo, _ = K.motor(f'afm{s}', (FX1 - 0.3, s * (PW / 2 + 0.7), ZF - 1.25), (1, 0, 0), 160)
        af.append(mo)
        af.append(box(f'ta{s}', (0.15, 0.15, 1.2), (FX1, s * (PW / 2 + 0.7), ZF - 1.5), 'steel_dark'))                     # torque arm
    af.append(box('tkup', (0.6, PW + 0.8, 0.5), (FX0 - 0.6, 0, ZF - 0.6), 'paint_grey'))                                     # screw take-ups
    for k in range(3):
        af.append(box(f'afsup{k}', (0.4, PW + 0.9, ZF - 1.3), (FX0 + k * (FX1 - FX0) / 2, 0, (ZF - 1.3) / 2), 'struct_grey'))
    af.append(K.grating_rect('afwk', FX0, -PW / 2 - 2.1, FX1 - 1.0, -PW / 2 - 1.1, ZF - 1.3, rail_sides=('s',)))
    af.append(box('dribble', (FX1 - FX0, 1.2, 0.35), ((FX0 + FX1) / 2, 0, 0.9), 'belt'))                                   # dribble belt under the feeder
    P(m, 'apron_feeder', 'Apron Feeder (3.0 m manganese-steel pans, ~0.03–0.25 m/s VFD): frame, carry rollers, head drive, tail take-up, dribble conveyor', 'drive', af, explode=(0, -4.5, 0), ref='ps_feeder', section='keep')
    # pans: each pan moves round the loop (carry run toward the sizer, return run back)
    Rp = 0.55
    zc_ = ZF - 0.55
    per = 2 * (FX1 - FX0) + TAU * Rp
    npan = int(per / 0.6)
    ppn = m.part('feeder_pans', 'Apron-Feeder Pans and Chains (carry run moves toward the sizer)', 'rotating_element', explode=(0, 0, 0), info={'ref': 'ps_feeder'})
    adv = 0.13 * FR / 30.0                               # ~0.13 m/s → 1.3 m per 10 s loop
    for k in range(npan):
        pan = join(f'pan{k}', [box(f'pp{k}', (0.6, PW, 0.06), (0, 0, 0), 'steel_dark'), box(f'pf{k}l', (0.6, 0.06, 0.35), (0, PW / 2 - 0.03, 0.2), 'steel_dark'),
                                box(f'pf{k}r', (0.6, 0.06, 0.35), (0, -PW / 2 + 0.03, 0.2), 'steel_dark')])
        ms = ppn.add(pan, smooth_angle=0)
        s0 = per * k / npan
        # loop direction in track_point is bottom-run forward; the carry (top) run must move +x, so travel the loop backwards
        lk, rk = [], []
        prev = None
        for f in range(FR + 1):
            sv = (s0 - adv * f / FR) % per
            pt, ang = MK.track_point(sv, FX0, FX1, zc_, Rp)
            a = -(ang - math.pi / 2)
            if prev is not None:
                while a - prev > math.pi:
                    a -= TAU
                while a - prev < -math.pi:
                    a += TAU
            prev = a
            lk.append((1 + f, (pt.x, 0.0, pt.z)))
            rk.append((1 + f, (0.0, a, 0.0)))
        ms.location = lk[0][1]
        ms.rotation_euler = rk[0][1]
        m.keyframes(ms, 'Operate', 'location', lk)
        m.keyframes(ms, 'Operate', 'rotation_euler', rk)
    # ---------------- twin-shaft sizer
    hz = [box('szb', (SX1 - SX0 + 0.6, 3.4, 0.3), ((SX0 + SX1) / 2, 0, SZ - 1.25), 'paint_grey')]
    for s in (-1, 1):
        hz.append(box(f'szs{s}', (SX1 - SX0 + 0.6, 0.12, 2.6), ((SX0 + SX1) / 2, s * 1.65, SZ), 'paint_grey'))
        hz.append(box(f'szcomb{s}', (SX1 - SX0, 0.3, 0.4), ((SX0 + SX1) / 2, s * 1.45, SZ - 0.5), 'steel_dark'))           # side breaker combs
        hz.append(cyl(f'brg{s}a', 0.32, SX0 - 0.6, SX0 - 0.3, 'paint_grey', 24, axis='X', center=(0, s * 0.55, SZ)))
        hz.append(cyl(f'brg{s}b', 0.32, SX1 + 0.3, SX1 + 0.6, 'paint_grey', 24, axis='X', center=(0, s * 0.55, SZ)))
    for k, x in enumerate((SX0 - 0.3, SX1 + 0.3)):
        hz.append(box(f'sze{k}', (0.12, 3.4, 2.6), (x, 0, SZ), 'paint_grey'))
    hz.append(box('szbar', (SX1 - SX0, 0.3, 0.35), ((SX0 + SX1) / 2, 0, SZ - 0.8), 'steel_dark'))                         # central breaker bar (third stage)
    hz.append(box('szcov', (SX1 - SX0 - 1.0, 3.4, 0.08), ((SX0 + 1.0 + SX1) / 2 + 0.05, 0, SZ + 1.32), 'paint_grey'))       # removable top covers
    hz.append(box('szchute', (SX1 - SX0, 2.0, SZ - 1.4 - (ZB + 0.55)), ((SX0 + SX1) / 2, 0, (SZ - 1.4 + ZB + 0.55) / 2), 'paint_grey'))   # discharge chute to the skirts
    for s in (-1, 1):
        for x in (SX0 + 0.2, SX1 - 0.2):
            hz.append(box(f'szleg{s}{x}', (0.4, 0.4, SZ - 1.4), (x, s * 1.85, (SZ - 1.4) / 2), 'struct_grey'))
    hz = [o for o in hz if o is not None]
    hz.append(K.grating_rect('szpl', FX1 + 0.6, -5.0, SX1 + 4.5, -1.95, SZ + 1.4, rail_sides=('s', 'e')))                  # sizer bay access platform
    P(m, 'sizer_housing', 'Twin-Shaft Sizer Housing: side liners, breaker combs, central breaker bar, top covers, bearings, discharge chute', 'casing', hz, explode=(0, 0, -2.0), ref='ps_sizer', section='split')
    shafts = _sizer_shafts('sz', SX0, SX1, (-0.55, 0.55), SZ, 0.4, 0.66, 7)
    psa = P(m, 'sizer_shaft_a', 'Sizer Shaft A (tooth rings, ~3 teeth per ring, scroll pattern)', 'rotating_element', [shafts[0]], explode=(0, -1.2, 2.5), ref='ps_shafts', section='keep', pivot=(0, -0.55, SZ))
    psb = P(m, 'sizer_shaft_b', 'Sizer Shaft B (counter-rotating, rings offset half a pitch)', 'rotating_element', [shafts[1]], explode=(0, 1.2, 2.5), ref='ps_shafts', section='keep', pivot=(0, 0.55, SZ))
    dr = []
    for s in (-1, 1):                                    # drive train per shaft: gear coupling, right-angle gearbox, fluid coupling, ~400 kW motor
        gb_c = V((SX1 + 1.4, s * 0.55, SZ))
        dr.append(K.rod(f'gc{s}', (SX1 + 0.6, s * 0.55, SZ), (SX1 + 0.9, s * 0.55, SZ), 0.22, 'steel_dark'))
        dr.append(box(f'gbx{s}', (1.0, 0.9, 1.3), tuple(gb_c), 'paint_blue', bevel=0.04))
        dr.append(K.rod(f'fcs{s}', gb_c + V((0, s * 0.45, 0)), gb_c + V((0, s * 1.3, 0)), 0.32, 'safety_yellow'))
        mo, _ = K.motor(f'szm{s}', tuple(gb_c + V((0, s * 1.35, 0))), (0, -s, 0), 400)
        dr.append(mo)
        dr.append(box(f'dbase{s}', (1.4, 3.2, 0.25), (gb_c.x, s * 2.2, SZ - 0.9), 'struct_grey'))
        for k in range(2):
            dr.append(box(f'dleg{s}{k}', (0.3, 0.3, SZ - 1.0), (gb_c.x + (k - 0.5) * 1.0, s * 2.9, (SZ - 1.0) / 2), 'struct_grey'))
    P(m, 'sizer_drives', 'Sizer Drive Trains (each shaft: gear coupling, right-angle gearbox, fluid coupling, ~400 kW motor)', 'drive', dr, explode=(3.0, 0, 0), ref='ps_drives', section='keep')
    # ---------------- discharge conveyor: horizontal in the trench under sizer and drives, then inclined at 12°
    zc0 = ZB - 0.45                                       # pulley-centre line (belt top ≈ ZB)
    pA, pB = V((SX0 - 2.8, 0, zc0)), V((20.0, 0, zc0))
    L2 = 40.0
    pC = pB + V((L2 * math.cos(math.radians(12)), 0, L2 * math.sin(math.radians(12))))
    c1s, c1b, path1 = K.conveyor('dc1', pA, pB, 1.4, idler_pitch=1.2, impact_len=SX1 - pA.x + 0.5, walkway='-', ground_z=-2.3, ends=(True, False), legs=False)
    c2s, c2b, path2 = K.conveyor('dc2', pB, pC, 1.4, idler_pitch=1.2, walkway='-', ground_z=0.0, ends=(False, True))
    P(m, 'discharge_conveyor', 'Sizer Discharge (sacrificial) Conveyor: 1,400 mm belt in a trench under the sizer, impact beds, then 12° incline with walkway', 'conveyor', [c1s, c2s], explode=(0, 0, -1.5), ref='ps_conveyor', section='keep')
    P(m, 'belt', 'Conveyor Belt (fabric EP, ~2.5–3 m/s)', 'conveyor', [c1b, c2b], ref='ps_conveyor', section='keep')
    org2, u2, _, upo2 = path2
    mg_c = org2 + u2 * 6.0 + upo2 + V((0, 0, 0.55))       # magnet ~14 m after the sizer discharge
    mg = [K.placed(box('mgb', (2.2, 1.6, 0.6), (0, 0, 0.3), 'paint_orange', bevel=0.03), K.frame(mg_c, (0, 0, 1), tuple(u2))),
          K.placed(box('mgbelt', (2.6, 1.7, 0.08), (0, 0, -0.05), 'belt'), K.frame(mg_c, (0, 0, 1), tuple(u2))),
          K.rod('mgh1', mg_c + V((0, 0, 0.6)), mg_c + V((0, 0, 2.8)), 0.04, 'steel_dark'),
          box('mgfr', (0.3, 3.2, 0.3), (mg_c.x, 0, mg_c.z + 2.9), 'struct_grey'),
          K.chute('mgch', [mg_c + V((1.1, 1.0, 0)), mg_c + V((1.1, 2.0, 0)), mg_c + V((1.6, 2.0, 0)), mg_c + V((1.6, 1.0, 0))],
                  [mg_c + V((1.4, 1.8, -2.2)), mg_c + V((1.4, 2.6, -2.2)), mg_c + V((1.9, 2.6, -2.2)), mg_c + V((1.9, 1.8, -2.2))], 'paint_grey')]
    for s in (-1, 1):
        mg.append(K.bar(f'mgpost{s}', (mg_c.x, s * 1.6, 0.0), (mg_c.x, s * 1.6, mg_c.z + 3.0), 0.2, 0.2, 'struct_grey'))
    md_c = org2 + u2 * 13.0 + upo2                        # detector ≥ ~26 m before the head pulley (stopping distance)
    md = [K.placed(lathe('mdc', [(0.95, -0.15), (1.15, -0.15), (1.15, 0.15), (0.95, 0.15)], 'polypropylene', 4, a0=math.pi / 4, a1=math.pi / 4 + TAU), K.frame(md_c, u2, (0, 0, 1)))]
    md.append(box('mdbox', (0.5, 0.3, 0.6), (md_c.x, -1.4, md_c.z), 'paint_grey'))
    md.append(cyl('mdsp', 0.06, md_c.z + 0.8, md_c.z + 1.0, 'paint_red', 12, center=(md_c.x + 0.8, 0, 0)))
    bs_c = org2 + u2 * 20.0 + upo2
    md.append(box('bscale', (3.0, 1.9, 0.18), (bs_c.x, 0, bs_c.z - 0.35), 'paint_blue'))                                    # belt scale
    md.append(box('ripdet', (0.3, 1.8, 0.1), (pA.x + 4.0, 0, zc0 - 0.95), 'paint_orange'))                                   # belt rip-detector loop
    P(m, 'tramp_metal', 'Self-Cleaning Overband Magnet, Metal Detector, Belt Scale & Rip Detector', 'auxiliaries', mg + md, explode=(0, 2.0, 2.0), ref='ps_tramp', section='keep')
    # ---------------- e-house / MCC, lighting
    eh = [box('ehouse', (12.0, 4.0, 3.6), (24.0, -14.0, 2.1), 'paint_white', bevel=0.04), box('ehroof', (12.4, 4.4, 0.15), (24.0, -14.0, 3.95), 'galvanised'),
          box('txf', (2.5, 2.0, 2.2), (32.5, -14.0, 1.1), 'paint_grey'), cyl('lmast', 0.15, 0, 22, 'galvanised', 12, center=(24.0, 8.0, 0)), box('lmh', (1.6, 0.6, 0.5), (24.0, 8.0, 22.2), 'steel_dark')]
    eh.append(K.stair('ehst', (18.5, -11.4, 0.0), (20.5, -11.4, 0.6), width=1.0))
    P(m, 'electrical', 'E-house (MCC, VFDs, PLC), Transformer and Lighting Mast', 'auxiliaries', eh, explode=(0, -3.0, 0), ref='ps_electrical', section='keep')
    # ---------------- animation: shafts rotate INWARD at the top (draw lumps into the nip)
    OPS = FR
    revs = 12                                            # 12 rev per 10 s ≈ 72 rpm
    for p_, sgn in ((psa, -1), (psb, 1)):
        for mesh in p_.meshes:
            m.keyframes(mesh, 'Operate', 'rotation_euler', [(1 + f, (sgn * TAU * revs * f / OPS, 0.0, 0.0)) for f in range(OPS + 1)])
    org1, u1, _, upo1 = path1

    def path_pt(sv):
        # 0..0.5 along the feeder, 0.5..0.6 drop through the sizer, 0.6..1 along the belt
        if sv < 0.5:
            return V((FX0 + 1.0 + (FX1 - FX0 - 1.0) * sv / 0.5, 0, ZF + 0.45))
        if sv < 0.6:
            q = (sv - 0.5) / 0.1
            return V((FX1 + 0.6 + (SX0 + 1.2 - FX1 - 0.6) * q, 0, ZF + 0.45 - (ZF + 0.45 - (ZB + 0.15)) * q))
        q = (sv - 0.6) / 0.4
        d = 3.0 + 45.0 * q
        if d < pB.x - pA.x:
            return org1 + u1 * d + upo1 + V((0, 0, 0.12))
        return org2 + u2 * (d - (pB.x - pA.x)) + upo2 + V((0, 0, 0.12))
    pore = m.part('ore', 'Bauxite: ROM lumps (≤ 1.2–1.5 m) to sized product (–200 mm)', 'payload', explode=(0, 0, 0), info={'ref': 'ps_ore'})
    NL = 36
    for i in range(NL):
        r = 0.6 if i % 3 == 0 else 0.38
        o = cyl(f'lump{i}', r, -r, r, 'bauxite', 7, center=(0, 0, 0))
        o.data.transform(Matrix.Rotation(i * 1.3, 4, 'Z') @ Matrix.Rotation(i * 0.7, 4, 'X'))
        ms = pore.add(o, smooth_angle=0)
        lk, sk = [], []
        ph = i / NL
        y_off = ((i * 37) % 7 - 3) * 0.3
        for f in range(OPS + 1):
            sv = (f / OPS + ph) % 1.0
            pnt = path_pt(sv) + V((0, y_off * (1.0 if sv < 0.55 else 0.3), 0))
            lk.append((1 + f, tuple(pnt)))
            scl = 1.0 if sv < 0.55 else 0.15
            sk.append((1 + f, (scl, scl, scl)))
        ms.location = lk[0][1]
        m.keyframes(ms, 'Operate', 'location', lk)
        m.keyframes(ms, 'Operate', 'scale', sk)
    m.flow('ore', [(FX0 + 1, 0, ZD + 2.0), (FX0 + 1, 0, ZF + 0.6), (FX1, 0, ZF + 0.6), (SX0 + 1.2, 0, SZ), (SX0 + 1.2, 0, ZB + 0.3),
                   tuple(org1 + u1 * 12 + upo1 + V((0, 0, 0.4))), tuple(org2 + u2 * 30 + upo2 + V((0, 0, 0.4)))], 'flow_discharge', 0.12, 2.0)
    m.flow_title, m.flow_desc = 'Ore path: truck → hopper → feeder → sizer → belt', 'Run-of-mine bauxite is tipped, fed, sized to –200 mm and conveyed to the overland conveyor.'
    return m.export(out)


# =============================================================== 01-DR  Crawler blast-hole drill rig (89–127 mm)
def m2p_blasthole_drill(out):
    FR = 360
    m = Model('m2p_blasthole_drill', 'Crawler Blast-Hole Drill Rig (top-hammer / DTH, 89–127 mm holes)', CAT, META['m2p_blasthole_drill'], operate_frames=FR)
    GA = 2.2 / 2
    uc = []
    for s in (-1, 1):
        st, mv, _ = MK.crawler_track(f'tk{s}', -2.0, 2.0, s * GA, 0.42, 0.38, 0.4, shoe_pitch=0.2, rollers=5, carriers=1)
        uc += [st, mv]
    uc.append(box('ucb', (2.0, 1.4, 0.4), (0, 0, 0.75), 'mine_yellow'))
    P(m, 'undercarriage', 'Oscillating crawler undercarriage with hydraulic track motors', 'running_gear', uc, explode=(0, 0, -0.8), ref='dr_undercarriage', section='keep')
    ch = [box('frame', (5.6, 2.3, 0.4), (-0.2, 0, 1.15), 'mine_yellow', bevel=0.03),
          box('pp', (2.6, 2.2, 1.6), (-1.6, 0, 2.15), 'mine_yellow', bevel=0.06),                          # power pack + screw compressor
          box('cool', (0.3, 2.0, 1.4), (-2.95, 0, 2.15), 'steel_dark'),
          box('dc', (0.9, 0.8, 1.6), (-0.1, -0.7, 2.15), 'paint_grey', bevel=0.03),                         # dust collector
          cyl('dcf', 0.25, 2.95, 3.3, 'paint_grey', 16, center=(-0.1, -0.7, 0)),
          box('htank', (0.9, 0.7, 0.9), (-0.1, 0.65, 1.8), 'mine_yellow', bevel=0.03)]
    for k in range(8):
        ch.append(box(f'gr{k}', (0.03, 2.0, 0.05), (-3.1, 0, 1.6 + k * 0.15), 'steel_dark'))
    ch.append(MK.cab('cab', 0.55, 2.05, 0.15, 1.15, 1.35, 3.45, door_side=+1))
    ch.append(K.handrail('chr', [(-2.9, 1.18, 1.35), (0.4, 1.18, 1.35)], 1.0))
    ch.append(cyl('exh', 0.07, 2.95, 3.6, 'steel_dark', 12, center=(-1.0, -0.5, 0)))                    # exhaust stack
    ch.append(cyl('gnss_c', 0.08, 3.45, 3.5, 'paint_white', 16, center=(1.3, 0.65, 0)))                 # GNSS antenna on the cab roof
    ch.append(cyl('bcn', 0.07, 3.45, 3.6, 'safety_yellow', 12, center=(0.8, 0.95, 0)))                  # rotating beacon
    P(m, 'chassis', 'Chassis: diesel power pack & screw compressor, hydraulic tank, dust collector, ROPS/FOPS cab, exhaust, GNSS, beacon', 'casing', ch, explode=(0, 0, 1.2), ref='dr_chassis', section='keep')
    # ---------------- boom: lift / swing / feed-dump cylinders set the hole position and angle; the cradle carries the feed
    PIV = V((3.9, 0, 2.0))                               # feed-cradle pivot at the boom tip (~1.5 m ahead of the tracks)
    FL = 8.6                                             # feed beam length
    Z0F = -PIV.z                                         # feed-foot local z when fully extended (foot plate on the ground)
    EXT = 0.6                                            # feed extension stroke in the cradle
    RX = 0.40                                            # drill-string offset in front of the feed beam (local +x)
    bm = [K.bar('boom', (2.2, 0, 1.5), (3.6, 0, 1.94), 0.35, 0.35, 'mine_yellow'),
          box('bmft', (0.5, 0.6, 0.3), (2.25, 0, 1.45), 'mine_yellow', bevel=0.02)]
    for s in (-1, 1):
        bm.append(box(f'chk{s}', (0.5, 0.04, 0.42), (3.72, s * 0.31, 2.0), 'mine_yellow'))                # pivot cheeks outside the cradle side plates
        bm.append(cyl(f'ppin{s}', 0.07, s * 0.25 if s > 0 else -0.33, s * 0.33 if s > 0 else -0.25, 'steel', 16, axis='Y', center=tuple(PIV)))  # stub pins into the cradle
        lc_b, lc_s = MK.hydraulic_cylinder(f'blift{s}', (2.35, s * 0.27, 1.35), (3.2, s * 0.27, 1.80), 0.06, 'mine_yellow')   # boom lift cylinders beside the boom
        bm += [lc_b] + lc_s
        bm += [box(f'blg{s}', (0.2, 0.08, 0.15), (2.35, s * 0.27, 1.40), 'mine_yellow'), box(f'blb{s}', (0.2, 0.1, 0.2), (3.2, s * 0.22, 1.80), 'mine_yellow')]
    P(m, 'boom', 'Boom with lift, swing and feed-dump cylinders; sets the hole position and angle within the coverage area', 'structure', bm, explode=(0.6, 0, 0.4), ref='dr_boom', section='keep')
    # feed built along local +z from the foot and laid along +x (transport attitude) by ST; the cycle raises it CCW to vertical
    ST = Matrix.Translation((PIV.x, 0, PIV.z)) @ Matrix.Rotation(math.radians(90), 4, 'Y')            # local z -> +x, local x -> -z
    crd = [box('crd', (0.12, 0.5, 1.8), (-0.24, 0, 0), 'mine_yellow'),                                  # cradle: rear guide behind the beam
           box('crdl', (0.3, 0.3, 0.2), (-0.42, 0, -0.75), 'mine_yellow'),                              # dump-cylinder lug
           cyl('crdp', 0.06, -0.2, 0.2, 'steel', 12, axis='Y', center=(-0.5, 0, -0.75)),
           sweep_tube('hose_c', [(-0.05, -0.38, -0.9), (-0.2, -0.38, -0.3), (-0.3, -0.38, 0.05)], 0.06, 'rubber')]   # dust hose clipped to the cradle
    for s in (-1, 1):
        crd.append(box(f'crds{s}', (0.42, 0.03, 1.8), (-0.09, s * 0.235, 0), 'mine_yellow'))         # side plates wrapping the sliding feed beam
    for o in crd:
        o.data.transform(ST)
    pc = P(m, 'cradle', 'Feed cradle (feed slides in it to press the foot onto the ground)', 'structure', crd, explode=(1.0, 0, 0.6), ref='dr_boom', section='keep', pivot=tuple(PIV))
    fd = [box('beam', (0.32, 0.42, FL), (0, 0, Z0F + FL / 2), 'mine_yellow'),
          box('foot', (0.9, 0.7, 0.05), (0.25, 0, Z0F + 0.025), 'steel_dark'),                          # feed foot (foot plate)
          cyl('hood', 0.30, Z0F + 0.05, Z0F + 0.40, 'paint_grey', 24, center=(RX, 0, 0)),               # collar dust hood
          box('cent', (0.5, 0.6, 0.3), (RX, 0, Z0F + 0.6), 'steel_dark'),                               # centraliser (rod guide)
          box('rodb', (0.04, 0.5, 6.3), (-0.21, 0.55, Z0F + 3.4), 'paint_grey'),                       # open rod rack: back plate + end plates
          box('rode0', (0.45, 0.5, 0.08), (0, 0.55, Z0F + 0.3), 'paint_grey'), box('rode1', (0.45, 0.5, 0.08), (0, 0.55, Z0F + 6.5), 'paint_grey')]
    for k in range(5):
        fd.append(cyl(f'rod{k}', 0.03, Z0F + 0.35, Z0F + 6.45, 'steel', 10, center=(-0.12 + 0.06 * (k % 3), 0.55 + 0.08 * (k // 3), 0)))
    fd.append(cyl('sheave', 0.18, -0.2, 0.2, 'steel', 16, axis='Y', center=(0, 0, Z0F + FL - 0.15)))
    fd.append(cyl('gnss_f', 0.08, Z0F + FL, Z0F + FL + 0.05, 'paint_white', 16))                          # GNSS antenna on the feed top
    fd.append(sweep_tube('hose_f', [(RX - 0.05, -0.33, Z0F + 0.3), (-0.05, -0.38, Z0F + 0.8), (-0.05, -0.38, -0.95)], 0.06, 'rubber'))  # hood suction hose up the feed to the cradle
    for o in fd:
        o.data.transform(ST)
    pf = P(m, 'feed', 'Feed (mast) ~8.6 m: feed foot, collar dust hood, centraliser, open rod rack with 6.1 m rods, top sheave', 'structure', fd, explode=(1.4, 0, 1.0), ref='dr_feed', section='keep', pivot=tuple(PIV))
    hs = [sweep_tube('hose_s', [(PIV.x - 0.3, -0.38, PIV.z + 0.05), (3.0, -0.6, 2.3), (1.5, -0.85, 2.7), (0.35, -0.7, 2.4)], 0.07, 'rubber')]
    P(m, 'dust_hose', 'Dust-suction hose from the collar hood to the dust collector', 'pipe', hs, ref='dr_dust', section='keep')
    ZH = Z0F + 6.63                                       # rock-drill start position on the feed (6.1 m rod + bit below it)
    hm = [box('rd', (0.55, 0.5, 0.75), (RX, 0, ZH), 'paint_red', bevel=0.03), box('rdc', (0.15, 0.5, 0.9), (0.20, 0, ZH), 'steel_dark'),
          cyl('shank', 0.05, ZH - 0.65, ZH - 0.35, 'steel', 12, center=(RX, 0, 0))]
    rod_ = [cyl('drod', 0.03, Z0F + 0.18, ZH - 0.35, 'steel', 10, center=(RX, 0, 0)), cyl('cpl', 0.045, ZH - 0.45, ZH - 0.35, 'steel_dark', 10, center=(RX, 0, 0)),
            cyl('bit', 0.0575, Z0F + 0.02, Z0F + 0.18, 'steel_dark', 12, center=(RX, 0, 0))]
    for k in range(3):                                    # flushing-flat marks so the rotation reads
        rod_.append(box(f'fl{k}', (0.012, 0.02, 0.5), (RX + 0.03, 0, Z0F + 1.0 + 2.0 * k), 'paint_red'))
    for o in hm + rod_:
        o.data.transform(ST)
    ph = P(m, 'rock_drill', 'Rock drill (hydraulic top hammer) on its carriage, riding the feed guides', 'actuator', hm, ref='dr_hammer', section='keep', pivot=tuple(PIV))
    prd = P(m, 'drill_string', 'Drill string (GT60-class 6.1 m rod + 115 mm button bit) — single pass, rotates while drilling', 'rotating_element', rod_, ref='dr_string', section='keep', pivot=tuple(PIV))
    D = math.radians
    A_TR = D(105)                                         # tramming attitude: feed tilted ~15° back over the rig, foot clear

    def feed_ang(t):                                      # cycle starts and ends in the tramming attitude (seamless loop)
        if t < 0.08:
            return A_TR + (D(90) - A_TR) * _ease(t / 0.08)
        if t < 0.92:
            return D(90)
        return D(90) + (A_TR - D(90)) * _ease((t - 0.92) / 0.08)

    def feed_ext(t):                                      # 0 = retracted in the cradle, EXT = foot on the ground
        if t < 0.09:
            return 0.0
        if t < 0.15:
            return EXT * _ease((t - 0.09) / 0.06)
        if t < 0.85:
            return EXT
        if t < 0.91:
            return EXT * (1 - _ease((t - 0.85) / 0.06))
        return 0.0

    HD = 3.0                                              # hole depth = 2.5 m caprock + 0.5 m sub-drill

    def drill_s(t):                                       # rock-drill travel down the feed (m)
        if t < 0.18:
            return 0.0
        if t < 0.70:
            return HD * (t - 0.18) / 0.52
        if t < 0.83:
            return HD * (1 - _ease((t - 0.70) / 0.13))
        return 0.0

    def spin(t):                                          # string rotation (display ~1 rev/s, real 60–150 rpm)
        if t < 0.17:
            return 0.0
        return TAU * 6.0 * (min(t, 0.80) - 0.17) / 0.63

    # stowed coords: the feed axis is world +x; the rod axis is the line z = PIV.z - RX, y = 0
    ROD_AX = V((0, 0, PIV.z - RX))
    MC, MF, MH, MS = [], [], [], []
    for f in range(FR + 1):
        t = f / FR
        R = _M_rot_y_about((PIV.x, PIV.z), feed_ang(t))
        MC.append(R)
        Mf = R @ Matrix.Translation((EXT - feed_ext(t), 0, 0))        # retracted = feed shifted up its axis (foot lifted)
        MF.append(Mf)
        Mh = Mf @ Matrix.Translation((-drill_s(t), 0, 0))
        MH.append(Mh)
        MS.append(Mh @ Matrix.Translation(ROD_AX) @ Matrix.Rotation(spin(t), 4, 'X') @ Matrix.Translation(-ROD_AX))
    _key_rigid(m, pc, MC)
    _key_rigid(m, pf, MF)
    _key_rigid(m, ph, MH)
    _key_rigid(m, prd, MS)
    # feed-dump cylinder: boom pin -> cradle lug
    DP0 = V((2.85, 0, 1.55))
    DL = V((PIV.x - 0.75, 0, PIV.z + 0.5))               # cradle lug in stowed coords (local (-0.5, 0, -0.75))
    dpin1 = lambda t: _M_rot_y_about((PIV.x, PIV.z), feed_ang(t)) @ DL
    dc_b, dc_s = MK.hydraulic_cylinder('fdump', DP0, dpin1(0.0), 0.06, 'mine_yellow')
    pdb = P(m, 'dump_cyl', 'Feed-dump cylinder (sets the feed angle)', 'actuator', [dc_b], ref='dr_boom', section='keep', pivot=tuple(DP0))
    pds = [P(m, f'dump_cyl_r{k}', 'Feed-dump cylinder rod', 'actuator', [o], ref='dr_boom', section='keep', pivot=tuple(DP0)) for k, o in enumerate(dc_s)]
    MK.animate_cylinder(m, pdb, pds, lambda t: DP0, dpin1)
    # ---------------- bench: caprock over soft ore, the pattern, completed holes and the active hole
    HX = PIV.x + RX                                       # active hole collar
    pat = []
    for i in range(4):
        for j in range(5):
            if i == 0 and j == 2:
                continue                                  # the hole being drilled
            x, y = HX + i * 3.0, -7.0 + j * 3.5
            pat.append(cyl(f'col{i}{j}', 0.35, 0.0, 0.08, 'caprock', 12, center=(x, y, 0)))
            if i > 0 and j == 2:
                continue                                  # holes on the section line are drawn full depth below
            pat.append(cyl(f'hole{i}{j}', 0.0575, 0.0, 0.1, 'coal', 8, center=(x, y, 0)))
            pat.append(lathe(f'cut{i}{j}', [(0.06, 0.0), (0.6, 0.0), (0.3, 0.18), (0.06, 0.12)], 'caprock', 12, center=(x, y, 0)))
    P(m, 'blast_pattern', 'Drill pattern ~3.0 × 3.5 m (burden × spacing): pegged collars and drilled holes with cuttings cones', 'structure', pat, ref='dr_pattern', section='split')
    hl = []
    for i in range(1, 4):                                 # completed holes on the section line: caprock + 0.5 m sub-drill
        x = HX + i * 3.0
        hl.append(cyl(f'dh{i}', 0.0575, -HD, 0.1, 'coal', 10, center=(x, 0, 0)))
        hl.append(lathe(f'dc{i}', [(0.06, 0.0), (0.6, 0.0), (0.3, 0.18), (0.06, 0.12)], 'caprock', 12, center=(x, 0, 0)))
    xc = HX + 3 * 3.0                                     # the far hole on the section line is shown after charging
    hl.append(cyl('chg', 0.06, -HD, -HD + 1.0, 'paint_orange', 12, center=(xc, 0, 0)))               # ~1 m charge column (bulk emulsion)
    hl.append(cyl('stm', 0.06, -HD + 1.0, 0.0, 'concrete', 12, center=(xc, 0, 0)))                   # ~2 m stemming (crushed aggregate)
    P(m, 'drilled_holes', 'Completed holes through the ~2.5 m caprock and ~0.5 m sub-drill; the far one shown after charging (~1 m emulsion, ~2 m stemming)', 'structure', hl, ref='dr_pattern', section='keep')
    BX0, BX1 = -5.0, HX + 11.0
    pb = m.part('bench', 'Bench: ferricrete caprock (~2.5 m here) over friable gibbsitic bauxite', 'structure', section='split', info={'ref': 'dr_pattern'})
    halves = []
    for sgn in (1, -1):                                  # built as two halves so the cut face keeps the caprock / ore colours
        halves.append(join(f'bench{sgn}', [box(f'cap{sgn}', (BX1 - BX0, 8.5, 2.5), ((BX0 + BX1) / 2, sgn * 4.25, -1.25), 'caprock'),
                                            box(f'ore{sgn}', (BX1 - BX0, 8.5, 1.0), ((BX0 + BX1) / 2, sgn * 4.25, -3.0), 'ore_layer')]))
    pb.add_split(halves[0], halves[1])
    # flushing air: compressor -> hose -> flushing head on the rock drill -> down the rod bore -> bit; cuttings up the annulus to the hood -> dust collector
    m.flow('air', [(-1.6, 0.0, 2.2), (0.5, 0.0, 1.55), (2.3, 0.0, 1.6), (3.0, 0.0, 1.9), (HX, 0.3, 6.0), (HX, 0, 5.5), (HX, 0, -HD + 0.1)], 'air', 0.05, 0.8)
    m.flow('cuttings', [(HX, 0.12, -HD + 0.1), (HX, 0.12, 0.25), (3.6, -0.6, 2.3), (1.5, -0.85, 2.7), (0.35, -0.7, 2.4)], 'flow_discharge', 0.05, 0.8)
    m.flow_title, m.flow_desc = 'Flushing air and cuttings', 'Flushing air down the rods and out of the bit; cuttings and dust return up the annulus to the collar hood and the dust collector.'
    return m.export(out)


# =============================================================== 01-FL  Large wheel loader (~95–100 t class)
def m2p_wheel_loader(out):
    FR = 1200                                             # 40 s real-time V-cycle: fill, reverse & turn, lift to the target, dump, return
    m = Model('m2p_wheel_loader', 'Large Wheel Loader (~95–100 t class, articulated, Z-bar linkage)', CAT, META['m2p_wheel_loader'], operate_frames=FR)
    RT, WT = 1.44, 1.15                                   # 45/65R45-class tyres (OD ≈ 2.9 m)
    XF, XR, YW = 2.9, -2.9, 1.8                           # front / rear axle (hitch at the origin), wheel track / 2
    # ---------------- rear frame (engine, cab, counterweight)
    rr = [box('rframe', (5.2, 1.6, 0.7), (-3.0, 0, 1.45), 'mine_yellow', bevel=0.04), box('eng', (3.4, 2.6, 2.1), (-3.9, 0, 2.65), 'mine_yellow', bevel=0.08),
          box('cwt', (0.7, 3.0, 1.5), (-5.75, 0, 1.85), 'mine_yellow', bevel=0.1), box('grill', (0.12, 2.3, 1.7), (-5.6, 0, 2.9), 'steel_dark'),
          box('rdeck', (4.0, 4.4, 0.08), (-3.6, 0, 3.74), 'grating'), box('cabriser', (1.7, 2.1, 0.9), (-1.2, 0, 2.3), 'mine_yellow', bevel=0.04)]
    for k in range(10):
        rr.append(box(f'gr{k}', (0.04, 2.2, 0.05), (-5.67, 0, 2.15 + k * 0.15), 'mine_yellow'))
    rr.append(MK.cab('cab', -2.0, -0.35, -1.05, 1.05, 2.75, 5.9, door_side=+1))
    rr.append(box('seat', (0.55, 0.55, 0.5), (-1.3, 0, 3.2), 'thermoplastic'))
    rr.append(K.handrail('rhr', [(-1.8, 2.2, 3.74), (-5.4, 2.2, 3.74), (-5.4, -2.2, 3.74), (-1.8, -2.2, 3.74)], 1.0))
    for s_ in (-1, 1):
        rr.append(box(f'fend{s_}', (2.6, 1.3, 0.08), (XR, s_ * YW, RT * 2 + 0.15), 'mine_yellow'))
        rr.append(MK.headlight(f'rl{s_}', (-5.75, s_ * 1.2, 3.4), (-1, 0, 0)))
    rr.append(sweep_tube('exh', [(-3.4, -0.6, 3.7), (-3.4, -0.6, 4.4)], 0.12, 'steel_dark', 14))
    # main access: diagonal stairway on the left side, ahead of the rear tyre, to the cab platform (door side)
    for s2 in (-1, 1):                                    # inclined access ladder (~70°) with handrails both sides, ahead of the rear tyre
        rr.append(K.bar(f'als{s2}', (-0.5, 1.95 + s2 * 0.3, 0.55), (-1.35, 1.95 + s2 * 0.3, 2.75), 0.05, 0.12, 'mine_yellow'))
        rr.append(K.rod(f'alh{s2}', (-0.45, 1.95 + s2 * 0.32, 1.45), (-1.3, 1.95 + s2 * 0.32, 3.75), 0.025, 'safety_yellow'))
    for k in range(8):
        u = (k + 0.5) / 8
        rr.append(box(f'alr{k}', (0.18, 0.6, 0.04), (-0.5 - 0.85 * u, 1.95, 0.55 + 2.2 * u), 'grating'))
    rr.append(box('cabpl', (1.7, 1.2, 0.06), (-1.2, 1.7, 2.75), 'grating'))
    rr.append(K.handrail('cphr', [(-0.35, 2.3, 2.75), (-2.05, 2.3, 2.75), (-2.05, 1.1, 2.75)], 1.0))
    rr.append(cyl('rax', 0.35, -1.6, 1.6, 'mine_yellow', 28, axis='Y', center=(XR, 0, RT)))
    rr.append(cyl('rdiff', 0.55, -0.45, 0.45, 'mine_yellow', 28, axis='Y', center=(XR, 0, RT)))
    rr.append(box('fsup', (0.5, 0.4, 0.6), (-2.6, -1.1, 1.75), 'paint_red'))                        # fire-suppression cylinders
    for s_ in (-1, 1):
        rr.append(box(f'scl{s_}', (0.25, 0.2, 0.3), (-1.8, s_ * 0.86, 1.55), 'mine_yellow'))         # steering-cylinder barrel lugs
    rr = [o for o in rr if o is not None]
    prr = P(m, 'rear_frame', 'Rear Frame: engine (~650 kW class), cooling, counterweight, ROPS cab, access stairway, oscillating rear axle', 'casing', rr, explode=(-1.5, 0, 0.6), ref='wl_rear', section='keep')
    rw = []
    for s_ in (-1, 1):
        c = (XR, s_ * YW, RT)
        rw += [MK.otr_tyre(f'rt{s_}', RT, WT, c, lugs=30), MK.otr_rim(f'rrm{s_}', RT, WT, c, side=s_)]
    prw = P(m, 'rear_wheels', 'Rear wheels: 45/65R45-class tyres (~2.9 m), oscillating axle', 'running_gear', rw, explode=(-1.5, 0, 0), ref='wl_rear', section='keep', pivot=(XR, 0, RT))
    hc = [cyl('hpin', 0.18, 0.9, 2.2, 'steel', 20, center=(0, 0, 0)), box('hplt', (0.8, 1.2, 0.2), (0, 0, 2.2), 'mine_yellow'), cyl('hpl', 0.18, 0.4, 0.9, 'steel', 20)]
    phc = P(m, 'hitch', 'Centre Hitch (upper and lower articulation pins)', 'drive', hc, ref='wl_hitch', section='keep')
    SC0, SC1 = (-1.8, 0.95, 1.55), (1.0, 0.95, 1.55)     # steering-cylinder pins: barrel on the rear frame, rod eye on the front frame
    SC_MIN = 2.00                                         # pin-to-pin length at full lock (inside cylinder): 2.00 – 3.29 m over ±40°
    SCP = {}
    for s_ in (-1, 1):
        b_, st_ = MK.hydraulic_cylinder(f'sc{s_}', (SC0[0], s_ * SC0[1], SC0[2]), (SC0[0] + SC_MIN, s_ * SC0[1], SC0[2]), 0.11, 'mine_yellow', stages=1)
        SCP[s_] = (P(m, f'steer_cyl{"L" if s_ > 0 else "R"}', 'Steering cylinder (barrel)', 'actuator', [b_], ref='wl_hitch', section='keep'),
                   P(m, f'steer_rod{"L" if s_ > 0 else "R"}', 'Steering cylinder (rod)', 'actuator', [st_[0]], ref='wl_hitch', section='keep'))
    # ---------------- front frame, front axle, wheels
    ff = [box('fframe', (3.8, 1.5, 0.8), (2.0, 0, 1.45), 'mine_yellow', bevel=0.04), box('tower', (0.9, 2.6, 2.3), (2.25, 0, 2.6), 'mine_yellow', bevel=0.05),
          cyl('fax', 0.35, -1.6, 1.6, 'mine_yellow', 28, axis='Y', center=(XF, 0, RT)), cyl('fdiff', 0.55, -0.45, 0.45, 'mine_yellow', 28, axis='Y', center=(XF, 0, RT))]
    F = (2.75, 3.6)                                       # tilt-cylinder pin on the tower front
    ff.append(box('tfb', (0.5, 0.5, 0.45), (F[0] - 0.15, 0, F[1]), 'mine_yellow'))
    for s_ in (-1, 1):
        ff.append(box(f'ffd{s_}', (2.4, 1.3, 0.08), (XF, s_ * YW, RT * 2 + 0.15), 'mine_yellow'))
        ff.append(MK.headlight(f'fl{s_}', (3.2, s_ * 1.3, 3.4)))
    pff = P(m, 'front_frame', 'Front Frame: loader tower, fixed front axle and fenders (articulates for steering)', 'casing', ff, explode=(1.0, 0, 0), ref='wl_front', section='keep')
    fw = []
    for s_ in (-1, 1):
        c = (XF, s_ * YW, RT)
        fw += [MK.otr_tyre(f'ft{s_}', RT, WT, c, lugs=30), MK.otr_rim(f'frm{s_}', RT, WT, c, side=s_)]
    pfw = P(m, 'front_wheels', 'Front wheels: 45/65R45-class tyres on the fixed front axle', 'running_gear', fw, explode=(1.0, 0, 0), ref='wl_front', section='keep', pivot=(XF, 0, RT))
    # ---------------- loader linkage at rest (bucket flat on the ground). Z-bar proportions checked over the whole cycle:
    # bucket −125°…+45° relative to the arms; angle at C 50–128°, at the bucket pin 8–173° (near toggle at full dump and full rack-back:
    # the dump / rack-back stops take the load); tilt cylinder 1.85–2.55 m (ratio 1.38), clear of the cross-tube
    A = (2.3, 3.4)                                        # lift-arm pivot on the tower
    H = (6.35, 0.95)                                      # bucket hinge
    LA, LB = (1.35, 1.35), (4.05, 2.45)                   # lift-cylinder pins (frame, arm)
    B0 = (4.55, 2.75)                                     # bell-crank pivot (cross-tube on the arms)
    C0 = (3.81, 2.08)                                     # bell-crank lower end (to the link), behind and below B0
    D0 = (6.15, 1.55)                                     # link pin on the bucket bracket (behind / above the hinge)
    R_BC = math.hypot(C0[0] - B0[0], C0[1] - B0[1])
    R_CD = math.hypot(D0[0] - C0[0], D0[1] - C0[1])
    E0 = (B0[0] + (B0[0] - C0[0]) * 0.8 / R_BC, B0[1] + (B0[1] - C0[1]) * 0.8 / R_BC)   # bell-crank top (tilt-cylinder rod eye)
    cr = lambda u, v: u[0] * v[1] - u[1] * v[0]
    SIDE = cr((D0[0] - B0[0], D0[1] - B0[1]), (C0[0] - B0[0], C0[1] - B0[1])) > 0      # C stays on this side of line B0–D (no branch flip)
    TILT_MIN = 1.85                                        # tilt cylinder runs 1.85–2.55 m over the cycle (ratio 1.38)
    WB = 2.55                                             # half bucket width (~5.1 m)
    arms = []
    for s_ in (-1, 1):
        arms.append(extrude_poly(f'arm{s_}', _poly_band([A, (4.3, 2.55), H], [0.32, 0.38, 0.26]), s_ * 1.2 - 0.12, s_ * 1.2 + 0.12, 'mine_yellow', plane='XZ'))
    arms.append(cyl('xtube', 0.2, -1.3, 1.3, 'mine_yellow', 20, axis='Y', center=(B0[0], 0, B0[1])))
    for s_ in (-1, 1):
        arms.append(box(f'xtb{s_}', (0.5, 0.2, 0.6), (B0[0] - 0.15, s_ * 1.2, B0[1] - 0.2), 'mine_yellow'))
    pam = P(m, 'lift_arms', 'Lift Arms with cross-tube (bell-crank pivot)', 'structure', arms, explode=(1.0, 0, 1.0), ref='wl_arms', section='keep', pivot=(A[0], 0, A[1]))
    bc = [extrude_poly('bcrank', _poly_band([C0, B0, E0], [0.16, 0.24, 0.16]), -0.28, 0.28, 'mine_yellow', plane='XZ'),
          cyl('bce', 0.1, -0.32, 0.32, 'steel', 14, axis='Y', center=(E0[0], 0, E0[1])), cyl('bcc', 0.1, -0.32, 0.32, 'steel', 14, axis='Y', center=(C0[0], 0, C0[1])),
          cyl('bcb', 0.14, -0.32, 0.32, 'steel', 14, axis='Y', center=(B0[0], 0, B0[1]))]
    pbc = P(m, 'bell_crank', 'Z-bar Bell Crank', 'actuator', bc, ref='wl_zbar', section='keep', pivot=(B0[0], 0, B0[1]))
    plk = P(m, 'tilt_link', 'Tilt Link (bell crank to bucket)', 'actuator', [K.bar('lnk', (C0[0], 0, C0[1]), (D0[0], 0, D0[1]), 0.22, 0.2, 'mine_yellow', up=(0, 0, 1))],
            ref='wl_zbar', section='keep', pivot=(C0[0], 0, C0[1]))
    # bucket: back plate 0.25 m ahead of the hinge, hinge and link brackets behind it; struck ≈ 10 m³, heaped ≈ 11.5–12 m³ (ISO 7546)
    bpts = [(8.144, 0.05), (6.8, 0.05), (6.608, 0.29), (6.608, 1.442), (6.848, 1.778), (7.28, 1.874)]   # heaped ≈ 11.8 m³ (ISO 7546) at 5.1 m
    bk = [extrude_poly('bwrap', _poly_band(bpts, 0.05), -WB, WB, 'mine_yellow', plane='XZ')]
    for s_ in (-1, 1):
        bk.append(extrude_poly(f'bside{s_}', bpts, s_ * WB - (0.06 if s_ > 0 else 0), s_ * WB + (0 if s_ > 0 else 0.06), 'mine_yellow', plane='XZ'))
        bk.append(extrude_poly(f'bhbr{s_}', [(6.6, 0.55), (6.6, 1.25), (H[0] - 0.12, H[1] + 0.2), (H[0] - 0.12, H[1] - 0.2)], s_ * 1.2 - 0.13, s_ * 1.2 + 0.13, 'mine_yellow', plane='XZ'))
        bk.append(cyl(f'bhb{s_}', 0.17, s_ * 1.2 - 0.16, s_ * 1.2 + 0.16, 'steel', 16, axis='Y', center=(H[0], 0, H[1])))
    for s_ in (-1, 1):                                    # link bracket (two cheeks) behind the back plate
        bk.append(extrude_poly(f'bdbr{s_}', [(6.6, 1.2), (6.6, 1.75), (D0[0] - 0.12, D0[1] + 0.12), (D0[0] - 0.12, D0[1] - 0.15)], s_ * 0.2 - 0.05, s_ * 0.2 + 0.05, 'mine_yellow', plane='XZ'))
    bk.append(cyl('bdb', 0.11, -0.26, 0.26, 'steel', 14, axis='Y', center=(D0[0], 0, D0[1])))
    bk.append(box('lip', (0.38, 2 * WB, 0.1), (7.952, 0, 0.1), 'steel_dark'))
    bk.append(box('wear', (1.15, 2 * WB - 0.2, 0.05), (7.376, 0, 0.02), 'steel_dark'))
    for k in range(7):
        y = -WB + 0.35 + k * (2 * WB - 0.7) / 6
        bk.append(K.bar(f'bt{k}', (8.096, y, 0.1), (8.528, y, 0.08), 0.16, 0.1, 'steel'))
    pbk = P(m, 'bucket', 'Rock Bucket (~11.5–12 m³ heaped, ~5.1 m wide) with cast lip, teeth and wear plates', 'casing', bk, explode=(1.4, 0, 0), ref='wl_bucket', section='keep', pivot=(H[0], 0, H[1]))
    lode = cyl('lode', 0.85, -WB + 0.15, WB - 0.15, 'bauxite', 20, axis='Y', center=(0, 0, 0))
    lode.data.transform(Matrix.Translation((7.4, 0, 0.88)) @ Matrix.Diagonal((0.88, 1, 0.9, 1)))
    pld = P(m, 'bucket_load', 'Bucket load (~16 t bauxite)', 'payload', [lode], ref='wl_load', section='keep', pivot=(H[0], 0, H[1]))
    CY = {}
    FE = math.hypot(E0[0] - F[0], E0[1] - F[1])
    TB = (F[0] + (E0[0] - F[0]) * 1.85 / FE, F[1] + (E0[1] - F[1]) * 1.85 / FE)      # tilt cylinder built at its shortest length
    for key, pa, pb, ys, r, lab in (('liftcyl', LA, LB, (-0.85, 0.85), 0.2, 'Lift Cylinders (2)'), ('tiltcyl', F, TB, (0.0,), 0.22, 'Tilt Cylinder')):
        bs, ss = [], []
        for y in ys:
            b, st = MK.hydraulic_cylinder(f'{key}{y}', (pa[0], y, pa[1]), (pb[0], y, pb[1]), r, 'mine_yellow', stages=1)
            bs.append(b)
            ss.append(st[0])
        CY[key] = (P(m, key + '_barrel', lab + ' (barrel)', 'actuator', bs, ref='wl_cyl', section='keep', pivot=(pa[0], 0, pa[1])),
                   P(m, key + '_rod', lab + ' (rod)', 'actuator', ss, ref='wl_cyl', section='keep', pivot=(pa[0], 0, pa[1])), pa, pb)
    # the face of a ROM-pad finger (bauxite, ~35° sides) the loader fills from
    PT = 9.05                                             # pile toe (the teeth reach ~1.5 m into the pile)
    P(m, 'pile', 'Face of a ROM-pad grade-bin finger (bauxite, angle of repose ~35°)', 'structure', [_hipped('pile', PT + 13.0, 0.0, 26.0, 14.0, 12.0, 1.0, 5.0, 0.0, 'bauxite')],
      ref='wl_load', section='keep')
    # ---------------- cycle: machine path (articulated-steering kinematics) + linkage poses
    D = math.radians
    a_, b_ = XF, -XR                                      # hitch to front / rear axle
    # (t0, t1, rear-axle travel m, articulation start, end). S6/S7 retrace S4/S3, so the loop closes exactly.
    SEG = [(0.00, 0.12, 2.0, 0, 0), (0.12, 0.24, 0.0, 0, 0), (0.24, 0.29, -2.0, 0, 0), (0.29, 0.40, -7.0, 0, D(40)), (0.40, 0.50, 3.0, D(40), D(-40)),
           (0.50, 0.55, 2.0, D(-40), 0), (0.55, 0.66, 0.0, 0, 0), (0.66, 0.71, -2.0, 0, D(-40)), (0.71, 0.80, -3.0, D(-40), D(40)),
           (0.80, 0.95, 7.0, D(40), 0), (0.95, 1.00, 0.0, 0, 0)]                # frames straight for the last 2 m to the target and at the dump
    # (t, arm lift alpha, bucket kap relative to the arms); absolute bucket angle = alpha + kap
    POSES = [(0.00, 0, 0), (0.12, 0, 0), (0.24, D(6), D(39)), (0.29, D(6), D(39)), (0.42, D(40), D(15)), (0.55, D(80), D(-25)),
             (0.62, D(80), D(-125)), (0.66, D(80), D(-125)), (0.78, D(35), D(-35)), (0.95, 0, 0), (1.00, 0, 0)]

    def seg_at(t):
        for s in SEG:
            if s[0] <= t <= s[1]:
                u = _ease((t - s[0]) / (s[1] - s[0]))
                return s, u
        return SEG[-1], 1.0

    def pose(t):
        for i in range(len(POSES) - 1):
            p0, p1 = POSES[i], POSES[i + 1]
            if p0[0] <= t <= p1[0]:
                u = _ease((t - p0[0]) / max(1e-6, p1[0] - p0[0]))
                return p0[1] + (p1[1] - p0[1]) * u, p0[2] + (p1[2] - p0[2]) * u
        return POSES[-1][1:]
    # integrate the rear-axle path: dθr = (ds·sinφ − a·dφ)/(a + b·cosφ)
    def cum(t):                                           # (rear-axle travel so far, articulation) at cycle time t
        done = 0.0
        for s in SEG:
            if t >= s[1]:
                done += s[2]
                continue
            u = _ease(max(0.0, (t - s[0]) / (s[1] - s[0])))
            return done + s[2] * u, s[3] + (s[4] - s[3]) * u
        return done, SEG[-1][4]
    xr, yr, th = XR, 0.0, 0.0
    sub = 8
    state = []
    srear, sfront, prevF = 0.0, 0.0, None
    s_prev, ph_prev = cum(0.0)
    for f in range(FR + 1):
        if f > 0:
            for k in range(1, sub + 1):
                s_now, ph = cum((f - 1 + k / sub) / FR)
                ds, dph, phm = s_now - s_prev, ph - ph_prev, (ph + ph_prev) / 2
                dth = (ds * math.sin(phm) - a_ * dph) / (a_ + b_ * math.cos(phm))
                th += dth / 2
                xr += ds * math.cos(th)
                yr += ds * math.sin(th)
                th += dth / 2
                srear += ds
                s_prev, ph_prev = s_now, ph
        hx, hy = xr + b_ * math.cos(th), yr + b_ * math.sin(th)
        Fx, Fy = hx + a_ * math.cos(th + ph_prev), hy + a_ * math.sin(th + ph_prev)
        if prevF is not None:
            sfront += (Fx - prevF[0]) * math.cos(th + ph_prev) + (Fy - prevF[1]) * math.sin(th + ph_prev)
        prevF = (Fx, Fy)
        state.append((hx, hy, th, ph_prev, srear, sfront))
    print('loader loop closure (m, deg):', round(state[-1][0] - state[0][0], 3), round(state[-1][1] - state[0][1], 3), round(math.degrees(state[-1][2] - state[0][2]), 2))
    M = {k: [] for k in ('rr', 'rw', 'hc', 'ff', 'fw', 'arm', 'bk', 'bc', 'lk', 'sb1', 'sr1', 'sb-1', 'sr-1', 'lb', 'lr', 'tb', 'tr', 'ld')}
    for f in range(FR + 1):
        t = f / FR
        hx, hy, th, ph, sr_, sf_ = state[f]
        MR = Matrix.Translation((hx, hy, 0)) @ Matrix.Rotation(th, 4, 'Z')
        MF = Matrix.Translation((hx, hy, 0)) @ Matrix.Rotation(th + ph, 4, 'Z')
        M['rr'].append(MR)
        M['hc'].append(MR)
        M['ff'].append(MF)
        M['rw'].append(MR @ Matrix.Translation((XR, 0, RT)) @ Matrix.Rotation(sr_ / RT, 4, 'Y') @ Matrix.Translation((-XR, 0, -RT)))
        M['fw'].append(MF @ Matrix.Translation((XF, 0, RT)) @ Matrix.Rotation(sf_ / RT, 4, 'Y') @ Matrix.Translation((-XF, 0, -RT)))
        alpha, kap = pose(t)
        Ma = MF @ _M_rot_y_about(A, alpha)
        M['arm'].append(Ma)
        M['bk'].append(Ma @ _M_rot_y_about(H, kap))
        D_ = _ry(D0, H, kap)
        C_ = _circ_int(B0, R_BC, D_, R_CD, lambda p, D_=D_: (cr((D_[0] - B0[0], D_[1] - B0[1]), (p[0] - B0[0], p[1] - B0[1])) > 0) == SIDE)
        ab = math.atan2(C_[1] - B0[1], C_[0] - B0[0]) - math.atan2(C0[1] - B0[1], C0[0] - B0[0])
        M['bc'].append(Ma @ _M_rot_y_about(B0, ab))
        al = math.atan2(D_[1] - C_[1], D_[0] - C_[0]) - math.atan2(D0[1] - C0[1], D0[0] - C0[0])
        M['lk'].append(Ma @ Matrix.Translation((C_[0] - C0[0], 0, C_[1] - C0[1])) @ _M_rot_y_about(C0, al))
        # load: fills while racking back in the pile, slides out between −15° and −45° absolute at the dump
        absb = math.degrees(alpha + kap)
        if t < 0.12:
            sc = 0.02
        elif t < 0.24:
            sc = 0.02 + 0.98 * _ease((t - 0.12) / 0.12)
        elif t < 0.55:
            sc = 1.0
        elif t < 0.66:
            sc = max(0.02, min(1.0, 1.0 - (-15.0 - absb) / 30.0)) if absb < -15.0 else 1.0
        else:
            sc = 0.02
        c0 = V((7.4, 0, 0.88))
        M['ld'].append(M['bk'][-1] @ Matrix.Translation(c0) @ Matrix.Diagonal((sc, sc, sc, 1)) @ Matrix.Translation(-c0))
        # cylinders in the front-frame plane
        for key, child in (('l', _ry(LB, A, alpha)), ('t', _ry(_ry(E0, B0, ab), A, alpha))):
            pa, pb = (LA, LB) if key == 'l' else (F, E0)
            th0 = math.atan2(pb[1] - pa[1], pb[0] - pa[0])
            L0 = math.hypot(pb[0] - pa[0], pb[1] - pa[1]) if key == 'l' else TILT_MIN
            dx, dz = child[0] - pa[0], child[1] - pa[1]
            L = math.hypot(dx, dz)
            Mr = _M_rot_y_about(pa, math.atan2(dz, dx) - th0)
            M[key + 'b'].append(MF @ Mr)
            M[key + 'r'].append(MF @ Matrix.Translation(((L - L0) * dx / L, 0, (L - L0) * dz / L)) @ Mr)
        # steering cylinders: barrel pin on the rear frame, rod eye on the front frame
        for s_ in (-1, 1):
            p0 = MR @ V((SC0[0], s_ * SC0[1], SC0[2]))
            p1 = MF @ V((SC1[0], s_ * SC1[1], SC1[2]))
            d = p1 - p0
            ang = math.atan2(d.y, d.x)
            Mb = Matrix.Translation(p0) @ Matrix.Rotation(ang, 4, 'Z') @ Matrix.Translation(V((-SC0[0], -s_ * SC0[1], -SC0[2])))
            M[f'sb{s_}'].append(Mb)
            M[f'sr{s_}'].append(Matrix.Translation(d.normalized() * (d.length - SC_MIN)) @ Mb)
    for part, key in ((prr, 'rr'), (prw, 'rw'), (phc, 'hc'), (pff, 'ff'), (pfw, 'fw'), (pam, 'arm'), (pbk, 'bk'), (pbc, 'bc'), (plk, 'lk'),
                      (CY['liftcyl'][0], 'lb'), (CY['liftcyl'][1], 'lr'), (CY['tiltcyl'][0], 'tb'), (CY['tiltcyl'][1], 'tr'),
                      (SCP[1][0], 'sb1'), (SCP[1][1], 'sr1'), (SCP[-1][0], 'sb-1'), (SCP[-1][1], 'sr-1')):
        _key_rigid(m, part, M[key])
    kr, kl, ks = [], [], []
    prev = None
    for f, Mx in enumerate(M['ld']):
        loc, q, sc = Mx.decompose()
        e = q.to_euler('XYZ', prev) if prev is not None else q.to_euler('XYZ')
        prev = e
        kr.append((1 + f, (e.x, e.y, e.z)))
        kl.append((1 + f, tuple(Mx @ pld.pivot - pld.pivot)))
        ks.append((1 + f, tuple(sc)))
    for mesh in pld.meshes:
        m.keyframes(mesh, 'Operate', 'rotation_euler', kr)
        m.keyframes(mesh, 'Operate', 'location', kl)
        m.keyframes(mesh, 'Operate', 'scale', ks)
    m.flow('cycle', [(H[0] + 2.5, 0, 0.6), (H[0] + 1.0, 0, 0.8), (H[0] - 1.0, 0, 3.0), (5.0, -3.5, 8.5), (7.5, -6.5, 5.0)], 'flow_discharge', 0.08, 0.8)
    m.flow_title, m.flow_desc = 'Material path: pile → bucket → truck / hopper', 'Ore is crowded into the bucket at the pile face, racked back, lifted while the loader reverses and turns, and dumped at full lift.'
    return m.export(out)


# =============================================================== A01 Mine overview (area model)
def _import_glb(path, name):
    """Import a built model GLB as ONE static mesh (rest pose), dropping section faces and helper nodes."""
    import bpy
    import bmesh
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    bpy.context.view_layer.update()
    from pumpforge.core import join as _join
    for o in new:
        o.animation_data_clear()
    bpy.context.view_layer.update()
    flat = []
    for o in meshes:
        me = o.data.copy()
        me.transform(o.matrix_world)
        ob = bpy.data.objects.new(o.name + '_f', me)
        bpy.context.scene.collection.objects.link(ob)
        flat.append(ob)
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
    obj = _join(name, flat)
    _strip_section(obj)
    return obj


def _strip_section(obj):
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    sec = [i for i, mt in enumerate(obj.data.materials) if mt and mt.name.startswith('section')]
    kill = [f for f in bm.faces if f.material_index in sec]
    if kill:
        bmesh.ops.delete(bm, geom=kill, context='FACES')
    bm.to_mesh(obj.data)
    bm.free()


class _Rig:
    """A built model GLB imported as one object per part (rest geometry, model coordinates) with a sampler of its own
    Operate clip: rel(t_sec) -> {part_id: transform from rest}. Used to place posed / animated equipment in area models."""

    def __init__(self, path, name):
        import bpy
        sc = bpy.context.scene
        sc.render.fps = 30
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=path)
        self.new = [o for o in bpy.data.objects if o not in before]
        self.name = name
        self.parts = {}
        for o in self.new:
            if o.type == 'MESH' and o.parent is not None and o.parent.get('part_id'):
                self.parts.setdefault(o.parent['part_id'], []).append(o)
        for o in self.new:
            ad = o.animation_data
            if not ad:
                continue
            if o.type != 'MESH':
                o.animation_data_clear()
                continue
            for tr in ad.nla_tracks:
                for st in tr.strips:
                    if st.action and st.action.name.startswith('Operate'):
                        ad.action = st.action
                        try:
                            ad.action_slot = st.action_slot
                        except Exception:
                            pass
            for tr in list(ad.nla_tracks):
                ad.nla_tracks.remove(tr)
        bpy.context.view_layer.update()
        self.rest = {pid: ms[0].parent.matrix_world.copy() for pid, ms in self.parts.items()}
        self.cache = {}

    def geometry(self, pids, name, Mx=None):
        """One mesh object (model coordinates, rest pose, optionally transformed by Mx) from the listed parts."""
        import bpy
        flat = []
        for pid in pids:
            for o in self.parts.get(pid, []):
                me = o.data.copy()
                me.transform(o.parent.matrix_world)
                if Mx is not None:
                    me.transform(Mx)
                ob = bpy.data.objects.new(f'{name}_{pid}_f', me)
                bpy.context.scene.collection.objects.link(ob)
                flat.append(ob)
        ob = join(name, flat)
        _strip_section(ob)
        return ob

    def posed(self, pids, name, t_sec, Mx):
        """Static copy of the listed parts in the pose of clip time t_sec, placed by Mx."""
        import bpy
        rel = self.rel(t_sec)
        flat = []
        for pid in pids:
            for o in self.parts.get(pid, []):
                me = o.data.copy()
                me.transform(Mx @ rel[pid] @ o.parent.matrix_world)
                ob = bpy.data.objects.new(f'{name}_{pid}_f', me)
                bpy.context.scene.collection.objects.link(ob)
                flat.append(ob)
        ob = join(name, flat)
        _strip_section(ob)
        return ob

    def rel(self, t_sec):
        import bpy
        k = round(t_sec * 30.0)
        if k not in self.cache:
            sc = bpy.context.scene
            sc.frame_set(1 + k)
            self.cache[k] = {pid: ms[0].matrix_world @ self.rest[pid].inverted() for pid, ms in self.parts.items()}
        return self.cache[k]

    def all_parts(self):
        return list(self.parts)

    def remove(self):
        import bpy
        for o in self.new:
            try:
                bpy.data.objects.remove(o, do_unlink=True)
            except ReferenceError:
                pass


def _decimate(obj, ratio):
    """Collapse-decimate a mesh object in place (used for tyres of instanced equipment in area models)."""
    import bpy
    md = obj.modifiers.new('dec', 'DECIMATE')
    md.ratio = ratio
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    obj.modifiers.remove(md)
    old = obj.data
    obj.data = me
    bpy.data.meshes.remove(old)
    return obj


def _split_y(obj):
    """Split a mesh object into its y > 0 and y < 0 halves (e.g. left / right wheels) -> (left, right)."""
    import bpy
    import bmesh
    out = []
    for keep_pos in (True, False):
        me = obj.data.copy()
        bm = bmesh.new()
        bm.from_mesh(me)
        kill = [v for v in bm.verts if (v.co.y < 0) == keep_pos]
        bmesh.ops.delete(bm, geom=kill, context='VERTS')
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(obj.name + ('_L' if keep_pos else '_R'), me)
        bpy.context.scene.collection.objects.link(o)
        out.append(o)
    bpy.data.objects.remove(obj, do_unlink=True)
    return out


def _dp(vals, tol):
    """Douglas–Peucker on a per-frame series of channel tuples; returns the kept frame indices (linear interpolation
    between kept keys stays within tol[c] on every channel)."""
    n = len(vals)
    keep = {0, n - 1}
    stack = [(0, n - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        vi, vj = vals[i], vals[j]
        worst, wk = 1.0, None
        for k in range(i + 1, j):
            u = (k - i) / (j - i)
            vk = vals[k]
            for c in range(len(vk)):
                e = abs(vk[c] - (vi[c] + (vj[c] - vi[c]) * u)) / tol[c]
                if e > worst:
                    worst, wk = e, k
        if wk is not None:
            keep.add(wk)
            stack += [(i, wk), (wk, j)]
    return sorted(keep)


def _key_world(m, obj, mats, scale=False, tp=0.02, tr=0.003, ts=0.01):
    """Sparse keyframes for an object whose world matrix per frame (index 0 = frame 1) is mats[f]."""
    vals, prev = [], None
    for Mx in mats:
        loc, q, sc = Mx.decompose()
        e = q.to_euler('XYZ', prev) if prev is not None else q.to_euler('XYZ')
        prev = e
        vals.append(tuple(loc) + (e.x, e.y, e.z) + (tuple(sc) if scale else ()))
    tol = (tp,) * 3 + (tr,) * 3 + ((ts,) * 3 if scale else ())
    idx = _dp(vals, tol)
    m.keyframes(obj, 'Operate', 'location', [(1 + i, vals[i][0:3]) for i in idx])
    m.keyframes(obj, 'Operate', 'rotation_euler', [(1 + i, vals[i][3:6]) for i in idx])
    if scale:
        m.keyframes(obj, 'Operate', 'scale', [(1 + i, vals[i][6:9]) for i in idx])
    return len(idx)


def _fillet(pts, radii, step=0.5):
    """Dense 2-D polyline through corner points pts with a tangent arc of radius radii[i] at every interior corner."""
    P_ = [V((p[0], p[1], 0.0)) for p in pts]
    out = [P_[0]]
    for i in range(1, len(P_) - 1):
        a, b, c = P_[i - 1], P_[i], P_[i + 1]
        d1, d2 = (b - a).normalized(), (c - b).normalized()
        cosang = max(-1.0, min(1.0, d1.dot(d2)))
        th = math.acos(cosang)
        R = radii[i - 1] if isinstance(radii, (list, tuple)) else radii
        if th < 1e-4:
            out.append(b)
            continue
        tl = R * math.tan(th / 2)
        t1, t2 = b - d1 * tl, b + d2 * tl
        out.append(t1)
        turn = 1.0 if d1.cross(d2).z > 0 else -1.0
        nrm = V((-d1.y, d1.x, 0)) * turn
        cen = t1 + nrm * R
        a0 = math.atan2(t1.y - cen.y, t1.x - cen.x)
        n = max(2, int(R * th / step))
        for k in range(1, n):
            ang = a0 + turn * th * k / n
            out.append(cen + V((math.cos(ang), math.sin(ang), 0)) * R)
        out.append(t2)
    out.append(P_[-1])
    dense = [out[0]]
    for a, b in zip(out[:-1], out[1:]):
        L = (b - a).length
        n = max(1, int(L / step))
        for k in range(1, n + 1):
            dense.append(a + (b - a) * (k / n))
    return [(p.x, p.y) for p in dense]


def _windrow(name, pts, h=1.4, base=4.5, crest=0.5, mat='laterite', zf=None):
    """Trapezoid-section safety windrow (bund) along a 3-D centreline (base level), one prism per segment."""
    objs = []
    for k, (a, b) in enumerate(zip(pts[:-1], pts[1:])):
        a, b = V(a), V(b)
        d = V((b.x - a.x, b.y - a.y, 0))
        if d.length < 1e-6:
            continue
        d.normalize()
        n = V((-d.y, d.x, 0))
        prof = [(-base / 2, 0.0), (base / 2, 0.0), (crest / 2, h), (-crest / 2, h)]
        verts = []
        for p in (a, b):
            for u, v in prof:
                verts.append(p + n * u + V((0, 0, v)))
        faces = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
        objs.append(mesh_from(f'{name}{k}', verts, faces, [mat]))
    return join(name, objs)


def _hipped(name, cx, cy, bx, by, tx, ty, h, z0, mat):
    """Stockpile / pond-bank prism: rectangle bx × by at z0 rising to tx × ty at z0 + h (hipped ends)."""
    verts = [(cx - bx / 2, cy - by / 2, z0), (cx + bx / 2, cy - by / 2, z0), (cx + bx / 2, cy + by / 2, z0), (cx - bx / 2, cy + by / 2, z0),
             (cx - tx / 2, cy - ty / 2, z0 + h), (cx + tx / 2, cy - ty / 2, z0 + h), (cx + tx / 2, cy + ty / 2, z0 + h), (cx - tx / 2, cy + ty / 2, z0 + h)]
    faces = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return mesh_from(name, verts, faces, [mat])


def _heightfield(name, x0, x1, y0, y1, ztop, zbot, mat, nx=24, ny=12):
    """Closed slab whose top follows ztop(x, y) and bottom zbot(x, y) (both callables) — undulating contacts."""
    verts, faces = [], []
    for layer, fz in ((0, zbot), (1, ztop)):
        for j in range(ny + 1):
            for i in range(nx + 1):
                x = x0 + (x1 - x0) * i / nx
                y = y0 + (y1 - y0) * j / ny
                verts.append((x, y, fz(x, y)))
    W = nx + 1
    off = (nx + 1) * (ny + 1)
    for j in range(ny):
        for i in range(nx):
            a = j * W + i
            faces.append((a, a + W, a + W + 1, a + 1))                       # bottom (down)
            faces.append((off + a, off + a + 1, off + a + W + 1, off + a + W))   # top (up)
    for i in range(nx):                                                       # y0 and y1 sides
        a, b = i, i + 1
        faces.append((a, b, off + b, off + a))
        a, b = ny * W + i, ny * W + i + 1
        faces.append((b, a, off + a, off + b))
    for j in range(ny):                                                       # x0 and x1 sides
        a, b = j * W, (j + 1) * W
        faces.append((b, a, off + a, off + b))
        a, b = j * W + nx, (j + 1) * W + nx
        faces.append((a, b, off + b, off + a))
    return mesh_from(name, verts, faces, [mat])


def _tree(name, x, y, z, h, mat='vegetation'):
    return join(name, [cyl(name + 't', h * 0.05, z, z + h * 0.45, 'topsoil', 6, center=(x, y, 0)),
                       lathe(name + 'c', [(0, z + h * 0.3), (h * 0.28, z + h * 0.42), (h * 0.22, z + h * 0.75), (0, z + h)], mat, 7, center=(x, y, 0))])


def m2p_mine_overview(out):
    import os
    D = math.radians
    GLB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output', 'glb')
    # ------------------------------------------------------------------ haul cycle (computed first: it sets the clip length)
    ST0 = V((30.0, 290.0, 0.0))                                              # primary sizing station origin, rotated +90° (its ramps face the pit)
    Mst = Matrix.Translation(ST0) @ Matrix.Rotation(D(90), 4, 'Z')
    sl = lambda x, y: (ST0.x - y, ST0.y + x)                                  # station-local XY -> world XY
    TR_RX = 3.65                                                              # truck: rear-tyre back edge behind the truck origin
    PB_X = -1.9                                                               # truck: body / payload centre (truck-local x)

    def gz(x, y):                                                             # running-surface level
        if -45 <= x <= -18 and 60 <= y <= 130:
            return -7.0 + (y - 60.0) / 70.0 * 7.0                             # pit access ramp (box cut), 10 %
        if -70 <= x <= 0 and -60 <= y <= 60:
            return -7.0
        if (32.0 <= x <= 65.5 or -5.5 <= x <= 28.0) and y >= 170:
            if y <= 256:
                return (y - 170.0) / 86.0 * 8.6                               # station ramps, 10 %
            if y <= 270:
                return 8.6 + (y - 256.0) / 14.0 * 1.4
            return 10.0
        return 0.0
    # truck routes (world XY corner points + fillet radii); keep-left traffic; pit lanes x = -37 (out, loaded) / -26 (in, empty)
    SPOT = {'A': (-5.3, -17.4), 'B': (-5.3, 20.6)}
    DUMP = sl(0.0, -9.6)                                                      # truck origin when tipping (rear tyres ~0.65 m short of the 1.55 m bund; tail clears it at 48°)
    PRE = sl(0.0, -24.35)                                                      # end of the forward manoeuvre on the deck
    to_station = [(-37.0, 156.5), (43.7, 156.5), (43.7, 290.0), (PRE[0], PRE[1])]                    # last corner R 10.5 (fits the deck)
    loaded = {'A': ([SPOT['A'], (-5.3, -45.0), (-37.0, -45.0)] + to_station, [12, 10, 12, 10, 10.5]),
              'B': ([SPOT['B'], (-5.3, 8.6), (-37.0, 8.6)] + to_station, [12, 10, 12, 10, 10.5])}
    from_station = [DUMP, (53.7, 290.0), (53.7, 145.5), (-26.0, 145.5)]
    empty = {'A': (from_station + [(-26.0, 50.0), (-16.0, 35.0), (-16.0, 8.0), (-5.3, -7.0), SPOT['A']], [13.75, 10, 10, 20, 20, 20, 20]),
             'B': (from_station + [(-26.0, 41.75), (-5.3, 41.75), SPOT['B']], [13.75, 10, 10, 10.35, 10.35])}

    def speeds(xy, kind):
        """Target speed (m/s) at each point: real class speeds (loaded up 10 % ≈ 11 km/h, flat ≈ 30–40 km/h, curves slower)."""
        v = []
        n = len(xy)
        for i, (x, y) in enumerate(xy):
            a, b = xy[max(0, i - 4)], xy[min(n - 1, i + 4)]
            c = xy[i]
            h1 = math.atan2(c[1] - a[1], c[0] - a[0]) if (c[0] - a[0]) ** 2 + (c[1] - a[1]) ** 2 > 1e-6 else None
            h2 = math.atan2(b[1] - c[1], b[0] - c[0]) if (b[0] - c[0]) ** 2 + (b[1] - c[1]) ** 2 > 1e-6 else None
            curv = abs(math.remainder(h2 - h1, TAU)) if h1 is not None and h2 is not None else 0.0
            on_ramp = (-45 <= x <= -18 and 60 <= y <= 130) or ((32 <= x <= 65.5 or -5.5 <= x <= 28) and 170 <= y <= 270)
            deck = y > 262 and 28 <= x <= 66
            if kind == 'loaded':
                t = 3.0 if on_ramp else (6.0 if -70 <= x <= 0 and y < 60 else 9.0)
            else:
                t = 6.0 if on_ramp else (7.0 if -70 <= x <= 0 and y < 60 else 11.0)
            if curv > 0.05:
                t = min(t, 4.0)
            if deck:
                t = min(t, 2.5)
            v.append(t)
        return v

    def timed(xy, vt, acc=0.7, dec=1.0):
        """Time stamps along the dense path from target speeds with acceleration / braking limits (start and end at rest)."""
        n = len(xy)
        ds = [0.0] + [math.hypot(xy[i][0] - xy[i - 1][0], xy[i][1] - xy[i - 1][1]) for i in range(1, n)]
        v = [0.0] * n
        for i in range(1, n):
            v[i] = min(vt[i], math.sqrt(v[i - 1] ** 2 + 2 * acc * ds[i]))
        v[-1] = 0.0
        for i in range(n - 2, -1, -1):
            v[i] = min(v[i], math.sqrt(v[i + 1] ** 2 + 2 * dec * ds[i + 1]))
        v[0] = 0.0
        t = [0.0]
        for i in range(1, n):
            vm = max(0.15, (v[i] + v[i - 1]) / 2)
            t.append(t[-1] + ds[i] / vm)
        return t

    def leg(pts, radii, kind, reverse=False):
        xy = _fillet(pts, radii)
        vt = speeds(xy, kind) if not reverse else [1.5] * len(xy)
        return {'xy': xy, 't': timed(xy, vt), 'rev': reverse, 'kind': kind}
    PASS, NPASS = 30.0, 6                                                     # excavator pass time (s, real) and passes per truck
    TIP = 30.0                                                                # truck dump clip (raise ≈ 13.5 s, hold, lower ≈ 10 s)
    T_LOAD = 1.0 + PASS * (NPASS - 1) + 11.0 + 2.0                           # spotted -> last dump -> drive off
    circ = {}
    for c in ('A', 'B'):
        circ[c] = [('load', None), ('leg', leg(*loaded[c], 'loaded')), ('leg', leg([PRE, DUMP], [], 'loaded', reverse=True)),
                   ('tip', None), ('leg', leg(*empty[c], 'empty'))]
        circ[c + '_T'] = T_LOAD + sum(s[1]['t'][-1] for s in circ[c] if s[0] == 'leg') + TIP
    T = math.ceil(max(circ['A_T'], circ['B_T']) + 1.0)
    for c in ('A', 'B'):                                                      # the shorter circuit drives its empty leg slower instead of
        d = T - 1.0 - circ[c + '_T']                                         # waiting under the excavator (both machines would idle)
        if d > 0:
            L = circ[c][4][1]
            k = (L['t'][-1] + d) / L['t'][-1]
            L['t'] = [x * k for x in L['t']]
            circ[c + '_T'] += d
    FR = int(T * 30)

    def truck_state(c, tc):
        """(x, y, heading, pitch, s_dist, phase, local_t) of a truck on circuit c at cycle time tc (0 = spotted for loading)."""
        wait = T - circ[c + '_T']                                             # waiting for the excavator before loading starts
        t = tc % T
        if t < wait + T_LOAD:
            return ('load', max(0.0, t - wait), SPOT[c], -math.pi / 2, None)
        t -= wait + T_LOAD
        for kind, L in circ[c][1:]:
            if kind == 'tip':
                if t < TIP:
                    return ('tip', t, DUMP, 0.0, None)
                t -= TIP
                continue
            if t <= L['t'][-1]:
                ts = L['t']
                lo, hi = 0, len(ts) - 1
                while hi - lo > 1:
                    mid = (lo + hi) // 2
                    if ts[mid] <= t:
                        lo = mid
                    else:
                        hi = mid
                u = (t - ts[lo]) / max(1e-6, ts[hi] - ts[lo])
                a, b = L['xy'][lo], L['xy'][hi]
                x, y = a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u
                j0, j1 = max(0, lo - 2), min(len(ts) - 1, hi + 2)
                p0, p1 = L['xy'][j0], L['xy'][j1]
                hd = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
                if L['rev']:
                    hd += math.pi
                return ('drive', t, (x, y), hd, L)
            t -= L['t'][-1]
        return ('load', 0.0, SPOT[c], -math.pi / 2, None)

    # phases: two trucks per circuit half a cycle apart; circuit B offset searched for the best clearance
    def pos(c, ph, f):
        st = truck_state(c, f / 30.0 + ph)
        return st[2], st[3]

    def clearance(offB):
        worst = 1e9
        sched = [('A', 0.0), ('A', T / 2), ('B', offB), ('B', offB + T / 2)]
        for f in range(0, FR, 15):
            ps = []
            for c, ph in sched:
                (x, y), hd = pos(c, ph, f)
                ps.append([(x + 2.6 * math.cos(hd) * s, y + 2.6 * math.sin(hd) * s) for s in (-1, 1)])
            for i in range(4):
                for j in range(i + 1, 4):
                    d = min(math.hypot(a[0] - b[0], a[1] - b[1]) for a in ps[i] for b in ps[j])
                    worst = min(worst, d)
        return worst
    best = max(((clearance(o), o) for o in [T * k / 40 for k in range(40)]), key=lambda z: z[0])
    OFFB = best[1]
    print(f'overview haul cycle: T = {T:.0f} s (A {circ["A_T"]:.0f} s, B {circ["B_T"]:.0f} s), circuit-B offset {OFFB:.0f} s, min truck clearance {best[0]:.1f} m')
    SCHED = [('A', 0.0), ('A', T / 2), ('B', OFFB), ('B', OFFB + T / 2)]

    m = Model('m2p_mine_overview', 'Bauxite Mine — Area Overview (mining sequence from clearing to rehabilitation)', CAT, META['m2p_mine_overview'], operate_frames=FR)
    m.sparse_anim = True
    Y0, Y1 = -60.0, 60.0                                                      # mined block width (front section face at Y0)
    # lateritic profile (top of each layer below the plateau surface z = 0)
    LAY = [('topsoil', 0.0, -0.25), ('laterite', -0.25, -1.3), ('caprock', -1.3, -2.8), ('ore_layer', -2.8, -7.0), ('clay_floor', -7.0, -9.0)]
    contact = lambda x, y: -7.0 + min(1.0, max(0.0, x / 6.0)) * (0.7 * math.sin(x / 13.0 + 0.6) * math.cos(y / 17.0) + 0.3 * math.sin(y / 7.0 + x / 23.0))

    def column(x0, x1, y0, y1, top, name, undulate=False):
        objs = []
        for mat, zt, zb in LAY:
            zt2 = min(zt, top)
            if zt2 <= zb:
                continue
            if undulate and mat in ('ore_layer', 'clay_floor'):
                ft = (lambda x, y, zt2=zt2: zt2) if mat == 'ore_layer' else contact
                fb = contact if mat == 'ore_layer' else (lambda x, y: -9.0)
                objs.append(_heightfield(f'{name}{mat}', x0, x1, y0, y1, ft, fb, mat))
            else:
                objs.append(box(f'{name}{mat}', (x1 - x0, y1 - y0, zt2 - zb), ((x0 + x1) / 2, (y0 + y1) / 2, (zt2 + zb) / 2), mat))
        return objs
    terr = {}
    terr['cleared'] = column(55, 80, Y0, Y1, 0.0, 'cl', True)
    terr['stripped'] = column(25, 55, Y0, Y1, -1.3, 'st', True)                # topsoil & overburden removed, caprock exposed
    terr['blasted'] = column(12, 25, Y0, Y1, -2.8, 'bl', True)                 # caprock blasted: broken muck swelled ~1.3×
    terr['blasted'].append(box('muck', (13, Y1 - Y0, 1.95), (18.5, 0, -2.8 + 0.975), 'caprock'))
    rnd_ = __import__('random').Random(11)
    for k in range(50):
        rr = rnd_.uniform(0.45, 1.25)
        terr['blasted'].append(cyl(f'mk{k}', rr, -0.9, -0.9 + rr * 0.6, 'caprock', 6, center=(rnd_.uniform(13, 24.5), rnd_.uniform(Y0 + 2, Y1 - 2), 0)))
    terr['orebench'] = column(0, 12, Y0, Y1, -2.8, 'ob', True)                # caprock loaded out: ore surface exposed for selective mining
    terr['floor'] = column(-70, 0, Y0, Y1, -7.0, 'pf')
    terr['floor'].append(lathe('sump', [(0, -7.25), (5.0, -7.25), (6.5, -7.0), (0, -7.0)], 'water', 24, center=(-64, 53, 0)))
    # backfill: overburden + waste caprock × swell ≈ 2.5 m on the clay floor, battered at 37° toward the active pit
    bf = column(-100, -70, Y0, Y1, -7.0, 'bf')
    bf.append(extrude_poly('bfo', [(-100, -7.0), (-70.0, -7.0), (-73.3, -4.5), (-100, -4.5)], Y0, Y1, 'laterite', plane='XZ'))
    terr['backfill'] = bf
    rh = column(-160, -100, Y0, Y1, -7.0, 'rh') + [box('rho', (60, Y1 - Y0, 2.5), (-130, 0, -5.75), 'laterite'), box('rht', (60, Y1 - Y0, 0.25), (-130, 0, -4.375), 'topsoil')]
    # final landform: shallow depression, edges battered ≤ ~17° up to the surrounding plateau
    rh.append(extrude_poly('rhw', [(-175, 0.0), (-160, -4.25), (-160, -9.0), (-175, -9.0)], Y0, Y1 + 15, 'laterite', plane='XZ'))
    rh.append(extrude_poly('rhn', [(Y1, -4.25), (Y1 + 15, 0.0), (Y1 + 15, -9.0), (Y1, -9.0)], -175, -70, 'laterite', plane='YZ'))
    terr['rehab'] = rh
    # forest column: five profile layers as separate parts so the exploded view lifts the lateritic profile apart
    prof_names = {'topsoil': 'Topsoil (~0.1–0.3 m, the seed bank)', 'laterite': 'Overburden: lateritic soil / pisolitic gravel (~0.3–2 m)',
                  'caprock': 'Ferricrete caprock (~0.5–3 m, drilled & blasted)', 'ore_layer': 'Friable gibbsitic bauxite (ore, ~4–15 m by deposit)',
                  'clay_floor': 'Kaolinitic clay floor (left in place)'}
    for k, (mat, zt, zb) in enumerate(LAY):
        if mat in ('ore_layer', 'clay_floor'):
            ft = (lambda x, y, zt=zt: zt) if mat == 'ore_layer' else contact
            fb = contact if mat == 'ore_layer' else (lambda x, y: -9.0)
            o = _heightfield(f'fo{mat}', 80, 140, Y0, Y1, ft, fb, mat)
        else:
            o = box(f'fo{mat}', (60, Y1 - Y0, zt - zb), (110, 0, (zt + zb) / 2), mat)
        P(m, f'profile_{mat}', prof_names[mat], 'structure', [o], explode=(0, 0, 1.5 * (len(LAY) - k)), ref='mn_forest', section='keep')
    # surrounding plateau (full profile so every pit wall shows the layers); pit ramp cut as a box cut, x -45…-18
    gr = []
    for name, x0, x1, y0, y1 in (('g1', -70, -45, 60, 100), ('g2', -18, 150, 60, 100), ('g3', -175, -45, 75, 100), ('g4', -260, -115, 100, 350),
                                 ('g4b', -75, -45, 100, 350), ('g4c', -115, -75, 100, 103), ('g4d', -115, -75, 127, 350),
                                 ('g5', -18, 150, 100, 350), ('g6', -45, -18, 130, 350)):
        if name == 'g3':
            gr += column(-175, -70, 75, 100, 0.0, name)
            continue
        gr += column(x0, x1, y0, y1, 0.0, name)
    gr += column(-115, -75, 103, 127, -2.5, 'g4e')                          # ground under the sediment-pond basin
    ramp = extrude_poly('pramp', [(60.0, -7.0), (130.0, 0.0), (130.0, -9.0), (60.0, -9.0)], -45, -18, 'laterite', plane='YZ')
    rws = extrude_poly('pramps', [(60.0, -6.95), (130.0, 0.05), (130.0, 0.0), (60.0, -7.0)], -44, -19, 'haul_road', plane='YZ')
    for s, xd in ((-1, -44.6), (1, -18.4)):                                   # toe drains along both cut walls
        gr.append(extrude_poly(f'drn{s}', [(60.0, -6.98), (130.0, 0.02), (130.0, -0.03), (60.0, -7.03)], xd - 0.4, xd + 0.4, 'water', plane='YZ'))
    terr['ramp'] = [ramp, rws]
    labels = {'cleared': ('1 · Cleared (timber salvaged, vegetation mulched)', 'mn_cleared'),
              'stripped': ('2 · Topsoil and overburden stripped — caprock exposed, drilled', 'mn_stripped'),
              'blasted': ('3 · Caprock blasted (broken muck, swelled ~1.3×) — loaded out first, to the sizer or to backfill by grade', 'mn_blasted'),
              'orebench': ('4a · Caprock removed — ore surface exposed; ore dug in one or two flitches to the clay floor', 'mn_floor'),
              'floor': ('4 · Ore mined to the grade-control floor on the clay', 'mn_floor'), 'backfill': ('5 · Backfilled (battered toward the pit)', 'mn_backfill'),
              'rehab': ('6 · Rehabilitated: topsoil returned, ripped, replanted — left as a shallow depression', 'mn_rehab'),
              'ramp': ('Pit access ramp: two-lane box cut, 10 % grade, toe drains', 'mn_road')}
    for k, objs in terr.items():
        P(m, f'zone_{k}', labels[k][0], 'structure', objs, explode=(0, 0, 0), ref=labels[k][1], section='keep')
    P(m, 'plateau', 'Surrounding plateau (undisturbed lateritic profile)', 'structure', gr, ref='mn_forest', section='keep')
    # vegetation
    rnd = __import__('random').Random(3)
    tr = [_tree(f'ft{k}', rnd.uniform(82, 138), rnd.uniform(Y0 + 2, Y1 - 2), 0.0, rnd.uniform(12, 22)) for k in range(80)]
    tru = [_tree(f'fu{k}', rnd.uniform(84, 145), rnd.uniform(64, 133), 0.0, rnd.uniform(12, 20)) for k in range(50)]
    P(m, 'trees_plateau', 'Native vegetation on the plateau beyond the pit', 'structure', tru, ref='mn_forest', section='keep')
    P(m, 'trees_forest', 'Undisturbed native vegetation (forest or plateau grassland), left standing until the pit is scheduled', 'structure', tr, explode=(0, 0, 1.5 * len(LAY)), ref='mn_forest', section='keep')
    import random
    rnd = random.Random(7)
    tr2 = [_tree(f'rt{k}', rnd.uniform(-158, -102), rnd.uniform(Y0 + 2, Y1 - 2), -4.25, rnd.uniform(2.5, 6.5), 'paint_green') for k in range(110)]
    P(m, 'trees_rehab', 'Rehabilitation planting (local species, seeded and planted)', 'structure', tr2, ref='mn_rehab', section='keep')
    # topsoil stockpile and sediment pond (earth basin with spillway), pit sump pump and line, clean-water diversion drain
    P(m, 'topsoil_stockpile', 'Topsoil stockpile (low, < 2 m; used only when direct return is not possible; respread as soon as practicable, ideally < 12 months)',
      'structure', [_hipped('tsp', 110, 150, 50, 12, 44, 4, 1.8, 0.0, 'topsoil')], ref='mn_topsoil', section='keep')
    PX, PY, PW_, PL_ = -95.0, 115.0, 40.0, 24.0                               # pond crest (inner) size
    # excavated basin: crest at grade, 3:1 inner batters, floor at -2.5 m, water at -0.5 m (the plateau slab has a hole here)
    x0p, x1p, y0p, y1p, PD = PX - PW_ / 2, PX + PW_ / 2, PY - PL_ / 2, PY + PL_ / 2, 2.5
    ins = 3.0 * PD
    vs = [(x0p, y0p, 0), (x1p, y0p, 0), (x1p, y1p, 0), (x0p, y1p, 0),
          (x0p + ins, y0p + ins, -PD), (x1p - ins, y0p + ins, -PD), (x1p - ins, y1p - ins, -PD), (x0p + ins, y1p - ins, -PD)]
    pond = [mesh_from('pbasin', vs, [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)], ['clay_floor'])]
    wi = 3.0 * 0.5
    pond.append(box('pwt', (PW_ - 2 * wi, PL_ - 2 * wi, 0.04), (PX, PY, -0.52), 'water'))
    pond.append(box('spch', (6.0, 4.0, 0.1), (x0p - 2.5, PY, -0.55), 'caprock'))                        # spillway notch 0.5 m below the crest (west)
    for k in range(9):                                                        # rock armour lining the spillway
        pond.append(box(f'spw{k}', (1.1, 1.0, 0.5), (x0p - 0.5 - (k % 3) * 2.0, PY - 1.3 + (k // 3) * 1.3, -0.4), 'caprock'))
    P(m, 'sediment_pond', 'Sediment pond: earth basin (3:1 inner banks, ~2.5 m deep) with rock-armoured spillway; settled water reused for dust suppression',
      'structure', pond, ref='mn_pond', section='keep')
    pp = [box('sppump', (2.4, 1.4, 1.3), (-61.5, 53, -6.35), 'paint_grey', bevel=0.04), box('spskid', (2.8, 1.6, 0.15), (-61.5, 53, -6.95), 'steel_dark'),
          sweep_tube('hdpe', [(-61.5, 54, -6.0), (-68.5, 58.5, -6.6), (-68.5, 59.6, -6.6), (-68.5, 60.3, 0.3), (-70, 75, 0.3), (-72, 103, 0.3), (-74, 112, 0.3), (PX + PW_ / 2 - 1.0, PY, 0.1)],
                     0.16, 'rubber', 10)]
    P(m, 'pit_dewatering', 'Pit sump with skid-mounted dewatering pump (01-PP) and HDPE line to the sediment pond', 'pump', pp, ref='mn_pond', section='keep')
    P(m, 'diversion_drain', 'Clean-water diversion drain around the pit perimeter (keeps runoff out of the pit)', 'structure',
      [box('dd1', (26, 1.2, 0.04), (-62.0, 104, 0.02), 'water'), box('dd1b', (155, 1.2, 0.04), (60.5, 104, 0.02), 'water'),
       box('dd2', (1.2, 160, 0.04), (138, 24, 0.02), 'water')], ref='mn_pond', section='keep')
    # ------------------------------------------------------------------ roads, ramps and windrows (≥ half the 27.00R49 tyre ≈ 1.4 m)
    rd = [box('rew', (222.7, 22, 0.1), (-48.65, 151, 0.05), 'haul_road'), box('rpt', (25, 10, 0.1), (-31.5, 135, 0.05), 'haul_road'),
          box('rcx', (28, 8, 0.1), (48.7, 166, 0.05), 'haul_road'), box('rcw', (28, 8, 0.1), (11.3, 166, 0.05), 'haul_road'),
          box('rrom', (22, 20, 0.1), (-150, 172, 0.05), 'haul_road')]
    wr = [_windrow('wr_s1', [(-160, 137.75, 0), (-46.25, 137.75, 0)]), _windrow('wr_s2', [(-16.75, 137.75, 0), (66.2, 137.75, 0)]),
          _windrow('wr_e', [(64.95, 137.75, 0), (64.95, 170, 0)]), _windrow('wr_w', [(-162.25, 137.75, 0), (-162.25, 182, 0)]),
          _windrow('wr_n1', [(-137.75, 164.25, 0), (-7.2, 164.25, 0)]), _windrow('wr_n2', [(27.55, 164.25, 0), (32.45, 164.25, 0)], base=4.0),
          _windrow('wr_rt1', [(-47.3, 60, 0), (-47.3, 137.75, 0)]), _windrow('wr_rt2', [(-15.7, 60, 0), (-15.7, 137.75, 0)])]   # box-cut crests
    for name, xa, xb in (('east', 34.7, 62.7), ('west', -2.7, 25.3)):        # station ramp extensions (10 %) with windrows on both open edges
        rd.append(extrude_poly(f'sr_{name}', [(170.0, 0.0), (256.0, 8.6), (256.0, -0.01), (170.0, -0.01)], xa, xb, 'laterite', plane='YZ'))
        rd.append(extrude_poly(f'srs_{name}', [(170.0, 0.02), (256.0, 8.62), (256.0, 8.58), (170.0, -0.02)], xa + 0.3, xb - 0.3, 'haul_road', plane='YZ'))
        for xe in (xa + 2.5, xb - 2.5):                                    # on the running surface, both open edges; ≥ ½ the loader's tyre
            wr.append(_windrow(f'wr_{name}{xe:.0f}', [(xe, 170, 0.0), (xe, 256, 8.6), (xe, 270, 10.0)], h=1.55, base=5.0))
    P(m, 'haul_road', 'Haul roads and station ramps: two-lane ≥ 3–3.5 × truck width (~22–25 m), ≤ 10 % grade, compacted laterite with gravel wearing course',
      'structure', rd, ref='mn_road', section='keep')
    P(m, 'windrows', 'Safety windrows (trapezoid bunds ≥ ½ the tyre height of the largest machine using the road: 1.4 m for trucks, 1.55 m where the loader travels) on every open edge', 'structure', wr, ref='mn_road', section='keep')
    # ------------------------------------------------------------------ ROM pad (≈ 3 ha) with grade-bin fingers (~9 kt each, 35° sides)
    rp = [box('rompad', (200, 150, 0.3), (-110, 260, 0.15), 'laterite')]
    for k in range(5):
        rp.append(_hipped(f'rom{k}', -185 + k * 35, 255, 22, 80, 2, 60, 7.0, 0.3, 'bauxite'))
    P(m, 'rom_pad', 'ROM pad (~3 ha) with grade-bin finger stockpiles (~8–10 kt each; ~2–3 days of ROM blending reserve)', 'structure', rp, ref='mn_rompad', section='keep')

    def inst_static(pid, name, ref, objs, link):
        p_ = m.part(pid, name, 'equipment', section='keep', info={'ref': ref, 'link': link})
        for o in objs:
            p_.add(o)
        return p_
    # ------------------------------------------------------------------ static equipment (posed from their own clips)
    st = _import_glb(os.path.join(GLB, 'm2p_primary_sizing_station.glb'), 'stn')
    st.data.transform(Mst)
    inst_static('sizing_station', 'Primary sizing station (tap: open detailed model)', 'mn_station', [st], 'm2p_primary_sizing_station')
    rg = _Rig(os.path.join(GLB, 'm2p_blasthole_drill.glb'), 'drl')
    drl = rg.posed([p for p in rg.all_parts() if p not in ('bench', 'blast_pattern', 'drilled_holes')], 'drill0', 6.0,
                   Matrix.Translation((47.3, -24.0, -1.3)) @ Matrix.Rotation(D(180), 4, 'Z'))
    rg.remove()
    inst_static('drill', 'Blast-hole drill working toward the free face, at right angles to the crest (tap: open detailed model)', 'mn_drill', [drl], 'm2p_blasthole_drill')
    pat = []
    for i in range(8):                                                        # 3.0 × 3.5 m pattern: drilled rows behind the rig, pegs ahead
        for j in range(31):
            x, y = 28.0 + 3.0 * i, -52.0 + 3.5 * j
            if abs(y + 24.0) < 3 and 43 <= x <= 51:
                continue                                  # active hole and the pegs under the rig
            if x <= 40:
                pat.append(lathe(f'pc{i}_{j}', [(0.06, -1.3), (0.55, -1.3), (0.28, -1.15), (0.06, -1.18)], 'caprock', 8, center=(x, y, 0)))
                pat.append(cyl(f'ph{i}_{j}', 0.06, -1.31, -1.17, 'coal', 6, center=(x, y, 0)))
            else:
                pat.append(cyl(f'pg{i}_{j}', 0.03, -1.3, -0.7, 'safety_yellow', 6, center=(x, y, 0)))
    P(m, 'blast_pattern', 'Blast pattern ~3.0 × 3.5 m: drilled rows toward the free face, pegged collars behind the rig', 'structure', pat, ref='mn_pattern', section='keep')
    rg = _Rig(os.path.join(GLB, 'm2p_crawler_dozer.glb'), 'dz')
    dz = [rg.posed(rg.all_parts(), 'dozer0', 4.0, Matrix.Translation((66.0, 22.0, 0.0)) @ Matrix.Rotation(D(180), 4, 'Z')),
          rg.posed(rg.all_parts(), 'dozer1', 4.0, Matrix.Translation((50.0, 42.0, -1.3)) @ Matrix.Rotation(D(180), 4, 'Z'))]
    rg.remove()
    inst_static('dozers', 'Dozers stripping topsoil and overburden (tap: open detailed model)', 'mn_dozer', dz, 'm2p_crawler_dozer')
    rg = _Rig(os.path.join(GLB, 'm2p_wheel_loader.glb'), 'wl')
    wl = rg.posed(rg.all_parts(), 'loader0', 0.0, Matrix.Translation((-115.0, 307.0, 0.3)) @ Matrix.Rotation(D(-90), 4, 'Z'))
    rg.remove()
    inst_static('wheel_loader', 'Wheel loader reclaiming a ROM-pad finger for blending (tap: open detailed model)', 'mn_loader', [wl], 'm2p_wheel_loader')
    # grade control: RC/aircore collars on a 10 × 10 m grid ahead of mining, RC rig, grade-bin polygons on the bench and floor
    gc = []
    for i in range(6):
        for j in range(11):
            x, y = 27.0 + 10.0 * i, -50.0 + 10.0 * j
            if (38 <= x <= 53 and -30 <= y <= -18) or (63.5 <= x <= 68.5 and -47 <= y <= -32):
                continue                                  # under the drill rig / the RC rig
            if 27 <= x <= 50 and any(abs(x - (28.0 + 3.0 * a)) < 1.0 and abs(y - (-52.0 + 3.5 * b)) < 1.0 for a in range(8) for b in range(31)):
                continue                                  # keep clear of the blast-hole collars
            z = -1.3 if x < 55 else 0.0
            gc.append(cyl(f'gc{i}_{j}', 0.12, z, z + 0.35, 'paint_white', 8, center=(x, y, 0)))
    rc = [box('rcch', (8.5, 2.5, 0.6), (0, 0, 1.2), 'paint_white', bevel=0.04), box('rccab', (2.0, 2.5, 1.8), (3.4, 0, 2.4), 'paint_white', bevel=0.06),
          box('rcwin', (0.05, 2.1, 0.8), (4.42, 0, 2.8), 'cab_glass'), box('rccomp', (3.0, 2.3, 1.7), (-0.2, 0, 2.35), 'paint_grey', bevel=0.05),
          box('rcmast', (0.45, 0.5, 9.0), (-3.6, 0, 6.0), 'paint_red'), box('rchead', (0.6, 0.6, 0.8), (-3.95, 0, 7.0), 'steel_dark'),
          cyl('rccyc', 0.45, 0.6, 2.4, 'stainless', 16, center=(-3.2, 1.9, 0)), box('rcspl', (0.8, 0.8, 0.6), (-3.2, 1.9, 0.3), 'stainless'),
          box('rcrack', (2.6, 0.9, 0.5), (-1.0, -1.7, 1.8), 'paint_grey')]
    for k, x in enumerate((-2.9, -1.4, 2.9)):
        for s in (-1, 1):
            rc.append(cyl(f'rct{k}{s}', 0.55, s * 1.0, s * 1.45, 'tyre', 20, axis='Y', center=(x, 0, 0.55)))
    rcj = join('rcrig', rc)
    rcj.data.transform(Matrix.Translation((66.0, -38.0, 0.0)) @ Matrix.Rotation(D(90), 4, 'Z'))
    gc.append(rcj)
    P(m, 'gc_drilling', 'Grade-control drilling: RC/aircore holes on a ~10 × 10 m grid (0.5–1 m samples) and the RC rig', 'structure', gc, ref='mn_gc', section='keep')
    gb = []
    for k, (pts, z, mat) in enumerate((([(0.5, -58), (11.5, -58), (11.5, -22), (0.5, -17)], -2.8, 'signal_green'), ([(0.5, -17), (11.5, -22), (11.5, 18), (0.5, 24)], -2.8, 'safety_yellow'),
                                       ([(0.5, 24), (11.5, 18), (11.5, 58), (0.5, 58)], -2.8, 'paint_red'), ([(2, 44), (10, 44), (10, 56), (2, 56)], -2.78, 'paint_grey'))):
        for a, b in zip(pts, pts[1:] + pts[:1]):
            gb.append(K.bar(f'gb{k}{a[0]}{a[1]}', (a[0], a[1], z + 0.03), (b[0], b[1], z + 0.03), 0.35, 0.06, mat))
    P(m, 'grade_bins', 'Grade-control polygons (GPS guidance): grade bins A/B/C on the exposed ore surface and a waste pod (high reactive SiO₂) to leave or send to backfill', 'structure', gb, ref='mn_gc', section='keep')
    # ------------------------------------------------------------------ excavators (own kinematics, top-loading trucks on the floor)
    G = _ex_geom()
    B0, A0, K0 = G['B0'], G['A0'], G['K0']
    L1, L2 = math.hypot(A0[0] - B0[0], A0[1] - B0[1]), math.hypot(K0[0] - A0[0], K0[1] - A0[1])
    th1_0, th2_0 = math.atan2(A0[1] - B0[1], A0[0] - B0[0]), math.atan2(K0[1] - A0[1], K0[0] - A0[0])

    def ik(r, z, phi):
        tx, tz = r - B0[0], z - B0[1]
        d = min(L1 + L2 - 1e-3, math.hypot(tx, tz))
        al = math.acos(max(-1.0, min(1.0, (L1 ** 2 + d ** 2 - L2 ** 2) / (2 * L1 * d))))
        th1 = math.atan2(tz, tx) + al
        ax, az = B0[0] + L1 * math.cos(th1), B0[1] + L1 * math.sin(th1)
        th2 = math.atan2(z - az, r - ax)
        beta = th1 - th1_0
        gamma = (th2 - th2_0) - beta
        return beta, gamma, phi - beta - gamma
    EXC = [{'pos': (7.3, -10.0, -2.8), 'c': 'A'}, {'pos': (7.3, 28.0, -2.8), 'c': 'B'}]          # on the exposed ore, idlers ≥ 4 m from the crest
    SWING = math.atan2(5.5, 12.6)                                             # truck body ~5.5 m to the operator side at ~12.6 m (23.6°)
    DIG = -0.5                                                                # dig band swung ~12° away from the truck: loaded swing ≈ 35°
    # one pass (s, swing frac, K r, K z, bucket angle phi (deg, absolute), load) — starts and ends loaded at the face; 4.2 m flitch below the
    # tracks, lowest bucket point ~0.15 m above the clay floor; the bucket returns above the truck rail before dropping to the face
    PASSK = [(0.0, DIG, 8.2, 2.6, -95, 1), (6.0, 1, 12.4, 4.2, -80, 1), (9.0, 1, 12.6, 4.0, 40, 0), (11.0, 1, 12.6, 4.1, 40, 0), (14.0, 0.0, 9.0, 3.6, 30, 0),
             (17.0, DIG, 8.4, 1.4, 30, 0), (20.0, DIG, 8.6, -1.2, 10, 0), (26.0, DIG, 7.4, -0.3, -50, 0.6), (30.0, DIG, 8.2, 2.6, -95, 1)]

    def ex_pose(tp):
        for a, b in zip(PASSK[:-1], PASSK[1:]):
            if a[0] <= tp <= b[0]:
                u = _ease((tp - a[0]) / (b[0] - a[0]))
                return tuple(a[i] + (b[i] - a[i]) * u for i in range(1, 6))
        return PASSK[-1][1:]
    # truck arrival (spotted) times per excavator from the schedule
    arrivals = {'A': [], 'B': []}
    for c, ph in SCHED:
        wait = T - circ[c + '_T']
        arrivals[c].append(((-ph + wait) % T))                                 # cycle time 0 + wait = loading starts

    def ex_state(c, ts):
        """(swing, r, z, phi, load) of excavator c at loop time ts."""
        for a0 in arrivals[c]:
            dt = (ts - (a0 + 1.0)) % T
            if dt < PASS * NPASS:
                sf, r, z, ph, ld = ex_pose(dt % PASS)
                return sf * SWING, r, z, ph, ld
        return DIG * SWING, 8.2, 2.6, -95.0, 1.0                              # waiting: loaded bucket held at the face
    exr = _Rig(os.path.join(GLB, 'm2p_hydraulic_excavator.glb'), 'ex')
    MOV = ['upper', 'power_module', 'access_stair', 'boom', 'arm', 'bucket', 'bucket_load', 'side_links', 'h_link',
           'boomcyl_barrel', 'boomcyl_rod', 'armcyl_barrel', 'armcyl_rod', 'bktcyl_barrel', 'bktcyl_rod']
    pex = m.part('excavators', 'Hydraulic excavators top-loading trucks on the pit floor (tap: open detailed model)', 'equipment', section='keep',
                 info={'ref': 'mn_excavator', 'link': 'm2p_hydraulic_excavator'})
    nkeys = 0
    for e in EXC:
        Me = Matrix.Translation(e['pos']) @ Matrix.Rotation(math.pi, 4, 'Z')
        pex.add(exr.geometry(['undercarriage', 'swing_ring'], f'ex{e["c"]}_uc', Me))
        objs = {pid: pex.add(exr.geometry([pid], f'ex{e["c"]}_{pid}')) for pid in MOV}
        series = {pid: [] for pid in MOV}
        for f in range(FR + 1):
            psi, r, z, phi, ld = ex_state(e['c'], f / 30.0)
            beta, gamma, kappa = ik(r, z, D(phi))
            PMx = _ex_mats(G, psi, beta, gamma, kappa)
            for pid in MOV:
                Mx = Me @ PMx[pid]
                if pid == 'bucket_load':
                    sc = 0.02 + 0.98 * ld
                    c0 = V((K0[0], 0, K0[1]))
                    Mx = Mx @ Matrix.Translation(c0) @ Matrix.Diagonal((sc, sc, sc, 1)) @ Matrix.Translation(-c0)
                series[pid].append(Mx)
        for pid in MOV:
            nkeys += _key_world(m, objs[pid], series[pid], scale=(pid == 'bucket_load'))
    # third excavator on the blasted caprock muck (loads caprock out first: to the sizer or backfill by grade) — posed, static
    Me3 = Matrix.Translation((19.5, 42.0, -0.85)) @ Matrix.Rotation(math.pi, 4, 'Z')
    b3, g3, k3 = ik(9.0, 0.4, D(-20))                                          # teeth on the ore surface: caprock only
    PM3 = _ex_mats(G, 0.0, b3, g3, k3)
    pex.add(exr.geometry(['undercarriage', 'swing_ring'], 'exC_uc', Me3))
    for pid in MOV:
        if pid != 'bucket_load':
            pex.add(exr.geometry([pid], f'exC_{pid}', Me3 @ PM3[pid]))
    exr.remove()
    tkc = _Rig(os.path.join(GLB, 'm2p_haul_truck.glb'), 'tkc')
    Mtc = Matrix.Translation((16.5, 52.5, -0.85)) @ Matrix.Rotation(math.pi / 2, 4, 'Z')
    ctr = [tkc.geometry(['frame', 'suspension', 'engine', 'radiator', 'transmission', 'rear_axle', 'hood', 'deck', 'cab', 'tanks', 'body',
                         'hoist_barrels', 'hoist_stage1', 'hoist_stage2', 'hoist_stage3'], 'ctr_ch', Mtc)]
    whl = tkc.geometry(['front_wheels', 'rear_wheels'], 'ctr_wh', Mtc)
    _decimate(whl, 0.3)
    ctr.append(whl)
    pl_ = tkc.geometry(['payload'], 'ctr_pl', Mtc @ Matrix.Translation(V((PB_X, 0, 3.07))) @ Matrix.Diagonal((1, 1, 0.5, 1)) @ Matrix.Translation(-V((PB_X, 0, 3.07))))
    ctr.append(pl_)
    tkc.remove()
    P(m, 'caprock_truck', 'Truck taking blasted caprock: to the sizer if grade control classes it as ore, otherwise to backfill', 'equipment', ctr, ref='mn_truck', section='keep')
    # motor grader on the haul road (rolling resistance, crossfall, windrow upkeep) — proxy model
    gd = [box('gfr', (6.2, 0.6, 0.5), (1.2, 0, 1.75), 'mine_yellow'), box('geng', (2.6, 2.4, 1.6), (-3.0, 0, 2.0), 'mine_yellow', bevel=0.08),
          box('gcab', (1.6, 2.2, 1.9), (-0.9, 0, 3.0), 'cab_glass'), box('gcabr', (1.8, 2.4, 0.12), (-0.9, 0, 4.0), 'mine_yellow'),
          box('gcir', (1.6, 1.6, 0.15), (1.0, 0, 1.25), 'steel_dark'), box('gbld', (0.25, 4.3, 0.7), (1.2, 0, 0.45), 'steel_dark'),
          box('gfax', (0.3, 2.2, 0.3), (4.2, 0, 0.75), 'mine_yellow'), box('grip', (0.5, 2.0, 0.6), (-4.6, 0, 1.0), 'mine_yellow')]
    for xw in (4.2, -2.4, -3.9):
        for sw in (-1, 1):
            gd.append(cyl(f'gw{xw}{sw}', 0.75, sw * 0.95 if sw > 0 else -1.6, sw * 1.6 if sw > 0 else -0.95, 'tyre', 18, axis='Y', center=(xw, 0, 0.75)))
    gj = join('grader', gd)
    gj.data.transform(Matrix.Translation((-130.0, 145.5, 0.0)) @ Matrix.Rotation(math.pi, 4, 'Z'))
    P(m, 'grader', 'Motor grader maintaining the haul road (rolling resistance, crossfall, windrows)', 'equipment', [gj], ref='mn_grader', section='keep')
    # ------------------------------------------------------------------ light vehicles (parked bay) and a water cart
    LY = 176.0                                                                # bay north of the haul road, bund on the road side
    lv = [box('lvbay', (18, 10, 0.06), (-30.0, LY, 0.03), 'concrete'), _windrow('lvbund', [(-39.5, LY - 6.5, 0), (-20.5, LY - 6.5, 0)], h=1.0, base=3.0),
          box('lvacc', (8, 6, 0.06), (-44.0, LY - 3.0, 0.03), 'haul_road')]
    for k in range(3):
        x0 = -34.5 + k * 4.5
        lv += [box(f'lvb{k}', (1.9, 5.3, 1.0), (x0, LY, 0.85), 'paint_white', bevel=0.06), box(f'lvc{k}', (1.85, 2.2, 0.75), (x0, LY + 0.6, 1.7), 'paint_white', bevel=0.08),
               box(f'lvw{k}', (1.7, 0.05, 0.55), (x0, LY + 1.72, 1.75), 'cab_glass'), K.rod(f'lvwh{k}', (x0 + 0.8, LY - 2.0, 1.4), (x0 + 0.8, LY - 2.0, 5.4), 0.015, 'paint_orange'),
               box(f'lvfl{k}', (0.03, 0.45, 0.3), (x0 + 0.8, LY - 1.78, 5.2), 'paint_red')]
        for dy in (-1.7, 1.7):
            for dx in (-0.85, 0.85):
                lv.append(cyl(f'lvt{k}{dy}{dx}', 0.4, -0.15, 0.15, 'tyre', 14, axis='X', center=(x0 + dx, LY + dy, 0.4)))
        lv.append(box(f'lvln{k}', (0.12, 6.0, 0.02), (x0 + 2.25, LY, 0.07), 'paint_white'))
    P(m, 'light_vehicles', 'Light vehicles parked in a bunded bay set back from the haul road (buggy whips and flags; give way to haul trucks)', 'equipment', lv, ref='mn_lv', section='keep')
    tk_wc = _Rig(os.path.join(GLB, 'm2p_haul_truck.glb'), 'wc')
    wcM = Matrix.Translation((-100.0, 145.5, 0.0)) @ Matrix.Rotation(math.pi, 4, 'Z')
    wc = [tk_wc.geometry(['frame', 'front_wheels', 'rear_wheels', 'suspension', 'rear_axle', 'hood', 'deck', 'cab', 'tanks'], 'wc_ch', wcM)]
    _decimate(wc[0], 0.5)
    tank = [box('wct', (6.6, 4.0, 2.4), (-2.3, 0, 4.2), 'paint_white', bevel=0.25), cyl('wcsb', 0.08, -2.4, 2.4, 'steel', 12, axis='Y', center=(-5.75, 0, 2.4)),
            box('wcmb', (0.6, 0.6, 0.9), (0.6, 0, 5.7), 'paint_grey'), K.rod('wcmn', (0.6, 0, 6.15), (1.9, 0, 6.6), 0.09, 'steel')]
    for k in range(6):
        tank.append(cyl(f'wcn{k}', 0.06, 2.1, 2.3, 'brass', 8, center=(-5.75, -2.0 + k * 0.8, 0)))
    tj = join('wctank', tank)
    tj.data.transform(wcM)
    wc.append(tj)
    tk_wc.remove()
    P(m, 'water_cart', 'Water cart (truck chassis with ~70–100 kL tank, rear spray bar and cab-controlled cannon) — dust control and fire response', 'equipment', wc, ref='mn_wc', section='keep')
    # ------------------------------------------------------------------ haul trucks (own dump clip, wheels turn with distance)
    tk = _Rig(os.path.join(GLB, 'm2p_haul_truck.glb'), 'tk')
    CH = ['frame', 'suspension', 'engine', 'radiator', 'transmission', 'rear_axle', 'hood', 'deck', 'cab', 'tanks']
    TMOV = ['front_wheels', 'rear_wheels', 'body', 'payload', 'hoist_barrels', 'hoist_stage1', 'hoist_stage2', 'hoist_stage3']
    import mathutils
    wc = {}
    for pid in ('front_wheels', 'rear_wheels'):
        bb = [ms.parent.matrix_world @ mathutils.Vector(cn) for ms in tk.parts[pid] for cn in ms.bound_box]
        wc[pid] = V(((min(v.x for v in bb) + max(v.x for v in bb)) / 2, 0, (min(v.z for v in bb) + max(v.z for v in bb)) / 2))
    RT = 1.345
    PLC = V((PB_X, 0, 3.07))                                                  # payload base centre (scale origin while loading)
    ptk = m.part('haul_trucks', 'Haul trucks on the load–haul–dump cycle (tap: open detailed model)', 'equipment', section='keep',
                 info={'ref': 'mn_truck', 'link': 'm2p_haul_truck'})
    for n_, (c, ph) in enumerate(SCHED):
        objs = {'chassis': ptk.add(tk.geometry(CH, f'tk{n_}_ch'))}
        for pid in TMOV:
            g_ = tk.geometry([pid], f'tk{n_}_{pid}')
            if pid.endswith('wheels'):
                _decimate(g_, 0.3)
            if pid == 'front_wheels':                     # split into left / right so each steers about its own kingpin
                for side, g2 in zip((1, -1), _split_y(g_)):
                    objs[f'fw{side}'] = ptk.add(g2)
                continue
            objs[pid] = ptk.add(g_)
        series = {k: [] for k in objs}
        dist, prevxy, hd_prev, delta = 0.0, None, None, 0.0
        KP = {sd: V((wc['front_wheels'].x, sd * 2.08, wc['front_wheels'].z)) for sd in (1, -1)}
        for f in range(FR + 1):
            stt = truck_state(c, f / 30.0 + ph)
            kind, lt, (x, y), hd, L = stt
            step = 0.0
            if prevxy is not None:
                step = math.hypot(x - prevxy[0], y - prevxy[1])
                dist += -step if (L is not None and L['rev']) else step
            prevxy = (x, y)
            if hd_prev is not None and step > 0.02 and not (L is not None and L['rev']):
                kap = math.remainder(hd - hd_prev, TAU) / step                # path curvature -> Ackermann-ish steer angle (4.57 m wheelbase)
                delta += (max(-0.6, min(0.6, math.atan(4.57 * kap))) - delta) * 0.25
            elif step <= 0.02:
                pass
            else:
                delta *= 0.8
            hd_prev = hd
            z = gz(x, y)
            zf, zb = gz(x + 3.0 * math.cos(hd), y + 3.0 * math.sin(hd)), gz(x - 3.0 * math.cos(hd), y - 3.0 * math.sin(hd))
            pitch = math.atan2(zf - zb, 6.0)
            Mt = Matrix.Translation((x, y, z)) @ Matrix.Rotation(hd, 4, 'Z') @ Matrix.Rotation(-pitch, 4, 'Y')
            tclip = lt if kind == 'tip' else 0.0
            rel = tk.rel(tclip)
            series['chassis'].append(Mt)
            cw = wc['rear_wheels']
            series['rear_wheels'].append(Mt @ Matrix.Translation(cw) @ Matrix.Rotation(dist / RT, 4, 'Y') @ Matrix.Translation(-cw))
            for sd in (1, -1):
                kp = KP[sd]
                series[f'fw{sd}'].append(Mt @ Matrix.Translation(kp) @ Matrix.Rotation(delta, 4, 'Z') @ Matrix.Rotation(dist / RT, 4, 'Y') @ Matrix.Translation(-kp))
            for pid in ('body', 'hoist_barrels', 'hoist_stage1', 'hoist_stage2', 'hoist_stage3'):
                series[pid].append(Mt @ rel[pid])
            # payload: grows pass by pass while loading, rides loaded, slides out in the dump clip, hidden while empty
            if kind == 'load':
                k_ = 0
                for p_ in range(NPASS):
                    td = 1.0 + p_ * PASS + 9.0
                    if lt >= td:
                        k_ = p_ + min(1.0, (lt - td) / 1.0)
                frac = k_ / NPASS
                Mp = Mt @ Matrix.Translation(PLC) @ Matrix.Diagonal((1.0, 1.0, max(0.001, frac), 1)) @ Matrix.Translation(-PLC) if frac > 0 else \
                    Mt @ Matrix.Translation(PLC) @ Matrix.Diagonal((0.001, 0.001, 0.001, 1)) @ Matrix.Translation(-PLC)
            elif kind == 'tip':
                Mp = Mt @ rel['payload'] if lt < 26.0 else Mt @ Matrix.Translation(PLC) @ Matrix.Diagonal((0.001, 0.001, 0.001, 1)) @ Matrix.Translation(-PLC)
            elif L is not None and L['kind'] == 'loaded':
                Mp = Mt
            else:
                Mp = Mt @ Matrix.Translation(PLC) @ Matrix.Diagonal((0.001, 0.001, 0.001, 1)) @ Matrix.Translation(-PLC)
            series['payload'].append(Mp)
        for k, ms in series.items():
            nkeys += _key_world(m, objs[k], ms, scale=(k == 'payload'), tr=(0.02 if (k.endswith('wheels') or k.startswith('fw')) else 0.003))
    tk.remove()
    print(f'overview keyframes kept: {nkeys}')
    # ore path overlay (circuit A, loaded leg) lifted above the trucks
    lp = circ['A'][1][1]['xy']
    pts = [(x, y, gz(x, y) + 5.5) for x, y in lp[::12]] + [(DUMP[0], DUMP[1], 15.0), (ST0.x, ST0.y + 2, 6.0)]
    m.flow('ore', [(-0.5, -8.2, -4.5), (-4.7, -15.0, -0.5)] + pts, 'flow_discharge', 0.6, 25.0)
    m.flow_title, m.flow_desc = ('Ore path: face → truck → ramp → haul road → dump hopper',
                                 'Ore is dug at the face, top-loaded into trucks on the pit floor, hauled up the 10 % ramp and along the haul road, and tipped into the dump hopper of the primary sizing station.')
    return m.export(out)


def _c(fn, cons, mat, op='—', fails=None, insp=None):
    return C(fn, cons, mat, op, fails or [], insp or [])


META = {
    'm2p_wheel_loader': {
        'summary': ('The ~95–100 t articulated wheel loader is the flexible loading unit of the mine: it reclaims the ROM-pad grade bins into the dump hopper for '
                    'blending, back-up loads trucks when an excavator is down, cleans up spillage and moves quickly between pits on its tyres. A Z-bar linkage '
                    'gives strong breakout force for digging; the machine steers by articulating about the centre hitch.'),
        'classification': {'family': 'Mining — load & haul', 'type': 'Large wheel loader, ~95–100 t, articulated, Z-bar linkage'},
        'model_configuration': {'scale': 'Real size (metres)', 'animation': 'Real-time V-cycle (40 s): into the pile, rack back to fill, reverse while articulating, lift to full height on the way to the target, dump to −45°, return to the pile',
                                'basis': 'Generic ~95–100 t wheel-loader envelope (e.g. 992 / WA900 class)'},
        'standards': [{'code': 'ISO 7131 / ISO 7546', 'title': 'Loaders — terminology; bucket volumetric rating', 'relevance': 'Bucket capacity'},
                      {'code': 'ISO 3471 / ISO 3449', 'title': 'ROPS / FOPS', 'relevance': 'Cab protection'}],
        'references': ['OEM specification sheets for the ~95–100 t loader class (generic envelope)'],
        'components': {
            'wl_rear': _c('Carries the power train and the operator.', 'Rear frame with engine (~650 kW class), cooling package, counterweight, cab on a riser with a left-side access stairway, rear axle (oscillating) and wheels.', 'Steel.', '—', ['Radiator blockage'], ['Clean cores']),
            'wl_hitch': _c('Joins the front and rear frames and steers the machine.', 'Upper and lower hitch pins with two steering cylinders (barrel on the rear frame, rod on the front frame — one extends while the other retracts); articulation about ±40°.', 'Steel pins and bearings.', '—', ['Hitch pin/bearing wear'], ['Measure hitch play']),
            'wl_front': _c('Carries the loader linkage and the front axle.', 'Front frame with the loader tower, front axle (fixed), wheels and fenders.', 'Steel.', '—', ['Cracks at the tower'], ['Structural inspection']),
            'wl_arms': _c('Lift the bucket.', 'Two box-section lift arms pinned to the tower, joined by a cross-tube that carries the bell crank; ~80° of arm rotation.', 'High-strength steel.', 'Hinge pin ~7 m and dump clearance ~4.7 m at full lift (class).', ['Pin wear'], ['Grease; measure pins']),
            'wl_zbar': _c('Tilt the bucket with high breakout force.', 'Z-bar linkage: tilt cylinder → bell crank → tilt link → bucket.', 'Steel.', '—', ['Pin/bush wear'], ['Auto-lube']),
            'wl_bucket': _c('Digs and carries the material.', 'Rock bucket ~11–12 m³ with cast lip, teeth and wear plates.', 'AR steel.', '—', ['Lip and tooth wear'], ['Inspect GET each shift']),
            'wl_load': _c('Material per pass.', 'About 15–17 t of bauxite per pass at ~1.45–1.55 t/m³ loose (rated payload ~21–22 t).', '—', '—'),
            'wl_cyl': _c('Lift and tilt.', 'Two lift cylinders and one tilt cylinder (double-acting).', 'Steel, chrome rods.', '—', ['Seal leaks'], ['Drift test'])}},
    'm2p_blasthole_drill': {
        'summary': ('A self-propelled crawler drill rig drills the blast holes that break the hard ferricrete caprock (and any hard ore). The feed (mast) is raised '
                    'to vertical, the hydraulic rock drill (top hammer — or a down-the-hole hammer on larger rigs) hammers and rotates the drill string into '
                    'the rock while the screw compressor blows flushing air down the rods that carries the cuttings up to the collar hood and dust collector. Holes of 89–127 mm on a ~3.0 × 3.5 m pattern '
                    'are then charged with bulk emulsion/ANFO.'),
        'classification': {'family': 'Mining — drill & blast', 'type': 'Crawler surface drill rig, top-hammer/DTH, 89–127 mm'},
        'model_configuration': {'scale': 'Real size (metres)', 'animation': 'Feed tilted forward from the tramming position to the design angle (here vertical), foot pressed down, rock drill drills ~3 m (time-compressed ≈ 30×; real penetration ≈ 0.5–1.5 m/min), string withdrawn while flushing, foot lifted, feed back to the tramming position (12 s loop)',
                                'basis': 'Generic surface top-hammer rig class (e.g. 20–25 t class); reference-plant design basis A01'},
        'standards': [{'code': 'ISO 18758-1', 'title': 'Mining and earth-moving machinery — Rock drill rigs and rock reinforcement rigs — Part 1: Safety requirements', 'relevance': 'Rig safety (guards, interlocks, noise/dust, stability) — verify edition'},
                      {'code': 'Local explosives regulations', 'title': 'Blasting codes of practice', 'relevance': 'Charging and firing'}],
        'references': ['Surface drill rig class literature (generic)', 'Reference-plant design basis (A01)'],
        'components': {
            'dr_undercarriage': _c('Moves and levels the rig on rough benches.', 'Oscillating crawler tracks with hydraulic motors.', 'Steel.', 'Tramming ~3 km/h; levels for vertical holes.', ['Track wear'], ['Track tension']),
            'dr_chassis': _c('Carries the power and air.', 'Diesel power pack, screw compressor (flushing air), hydraulic pumps and tank, dust collector, ROPS/FOPS cab.', 'Steel.', '—', ['Dust ingress into the engine'], ['Air-filter service']),
            'dr_feed': _c('Guides and pushes the drill.', 'Aluminium/steel feed beam ~8.6 m with chain or cylinder feed; feed foot pressed on the ground, collar dust hood, centraliser (rod guide) at the foot, rod rack/changer, top sheave. The feed slides in its cradle (feed extension) to put the foot down.', 'Steel/aluminium.', 'Set to the designed angle (here vertical); tilted back for tramming, laid down only for transport.', ['Wear of guide slides'], ['Check feed alignment']),
            'dr_dust': _c('Carries dust-laden air from the collar hood to the dust collector.', 'Flexible wear-resistant rubber suction hose (~125–150 mm) from the collar hood up the feed and boom to the dust-collector inlet.', 'Rubber, wire-reinforced.', '—', ['Wear-through, blockage, hood not sealing'], ['Inspect for holes/blockage each shift']),
            'dr_boom': _c('Places the feed over the hole.', 'Hydraulic boom with lift, swing and feed-dump/tilt cylinders; sets hole position and angle within the coverage area so several holes can be drilled without tramming.', 'Steel.', '—', ['Pin and bush wear'], ['Grease pins; check cylinder seals']),
            'dr_hammer': _c('Breaks the rock at the bit by percussion and rotation.', 'Hydraulic top-hammer rock drill on the feed carriage (DTH hammer at the bit on larger rigs).', 'Steel.', 'Percussion ~40–60 Hz (class typical).', ['Accumulator/seal wear'], ['Service per percussion hours']),
            'dr_string': _c('Transmits energy to the bit and carries the flushing air.', 'Hollow threaded drill rods (GT60/T51 class, 3.66 or 6.1 m) with a button bit 89–127 mm (here 115 mm); holes ≤ 5 m are drilled in a single pass.', 'Alloy steel, tungsten-carbide buttons.', 'Rotation ~60–150 rpm (top hammer).', ['Thread wear', 'Bit button wear'], ['Regrind bits before the wear flat reaches ~1/3 of the button diameter']),
            'dr_pattern': _c('Hole layout that gives the right fragmentation.', 'Burden × spacing ~2.5–3.5 × 3.0–4.0 m (here 3.0 × 3.5 m); hole depth through the caprock plus ~0.3–0.5 m sub-drill into the soft ore.', 'Ferricrete caprock over gibbsitic bauxite.', 'Powder factor ≈ 0.3–0.6 kg/m³ from the blast design.')}},
    'm2p_mine_overview': {
        'summary': ('The bauxite mine area model shows the whole mining sequence on one plateau, from undisturbed forest on the right to rehabilitated land on the '
                    'left: clearing, topsoil and overburden stripping, caprock drill-and-blast, excavation of the ore down to the kaolinitic clay floor, backfill, '
                    'and rehabilitation. The cut face shows the lateritic profile: topsoil, laterite overburden, ferricrete caprock, friable gibbsitic bauxite and '
                    'clay. Trucks run the real-time load–haul–dump cycle from the excavators, up the 10 % box-cut ramp and along the haul road to the primary sizing station; the ROM pad '
                    'holds the grade-bin blending reserve.'),
        'classification': {'family': 'Mining — area overview', 'type': 'Open-cut plateau bauxite mine (strip mining with progressive rehabilitation)'},
        'model_configuration': {'scale': 'Real size (metres); profile thicknesses typical, not a survey', 'animation': 'Real-time haul cycle (~7 min loop): excavators top-load trucks in ~6 passes, trucks haul up the ramp to the sizing station, reverse to the wheel stop and tip. Distances compressed: real one-way haul 2–8 km, real cycle ≈ 25–30 min',
                                'basis': 'Reference-plant design basis A01 (knowledge-based)'},
        'standards': [{'code': 'ICMM (2019)', 'title': 'Integrated Mine Closure — Good Practice Guide, 2nd ed.', 'relevance': 'Closure and progressive rehabilitation'},
                      {'code': 'LPSDP (2016)', 'title': 'Leading Practice Sustainable Development Program — Mine Rehabilitation / Mine Closure handbooks (Australian Government)', 'relevance': 'Rehabilitation practice'},
                      {'code': 'Local regulation', 'title': 'Approved mine closure / progressive mine closure plan (e.g. India MCDR 2017; WA mine closure plan guidelines)', 'relevance': 'Statutory obligations'}],
        'references': ['Reference-plant design basis (A01)', 'Koch, J.M. (2007) Restoring a jarrah forest understorey after bauxite mining — Restoration Ecology', 'SME Mining Engineering Handbook, 3rd ed.'],
        'components': {
            'mn_forest': _c('Undisturbed ground ahead of mining.', 'Native vegetation (forest or plateau grassland) on the lateritic plateau; the forest block shows the full profile.', '—', '—'),
            'mn_cleared': _c('First step: remove vegetation.', 'Merchantable timber salvaged; the rest mulched and kept for rehabilitation.', '—', 'Typically months to ~1 year ahead of mining (keep open disturbed ground to a minimum).'),
            'mn_stripped': _c('Expose the caprock / ore.', 'Topsoil (~0.1–0.3 m, the seed bank) stripped separately; overburden (~0.3–2 m) dozed or loaded and hauled to backfill.', 'Topsoil, laterite.', 'Strip ratio typically ~0.3–0.6 t waste per t ore (engineering estimate).'),
            'mn_blasted': _c('Break the hard cemented ferricrete cap.', '~3.0 × 3.5 m pattern (burden × spacing) set by the blast design, tighter in thin caprock; 89–127 mm holes, bulk emulsion/ANFO; the broken muck (swelled ~1.3×) is loaded as ore where grade allows.', 'Ferricrete caprock.', 'Caprock ~0.5–3 m thick.'),
            'mn_floor': _c('Ore mined out down to the clay floor.', 'Friable gibbsitic bauxite dug by backhoe to the grade-control floor; kaolinitic clay below is left. The ore/clay contact undulates, so the GC model and GPS guidance set the floor.', 'Bauxite; clay floor.', 'Ore ~4–15 m thick (deposit dependent; ~4 m here).'),
            'mn_backfill': _c('Return the pit to a stable landform.', 'Overburden and waste caprock backfilled (~1.6–3.6 m after swell) and shaped; battered at ~37° toward the active pit; drainage designed.', 'Laterite.', 'Rehabilitated pits remain shallow depressions — the ore removed is not replaced.'),
            'mn_rehab': _c('Restore a self-sustaining ecosystem.', 'Topsoil returned (direct return preferred), deep ripping on the contour, seeding and planting of local species, monitoring to completion criteria.', '—', 'Clearing-to-rehab ~1–3 years per pit.'),
            'mn_road': _c('Truck access from the pit to the station.', 'Two-lane haul road ≥ 3–3.5 × truck width (~22–25 m) with drains and trapezoid windrows ≥ ½ tyre height on every open edge; ramp ≤ 10 %; keep-left traffic.', 'Compacted laterite with gravel wearing course.', 'Watered for dust; graded for low rolling resistance.'),
            'mn_topsoil': _c('Keep topsoil alive for rehabilitation.', 'Direct return preferred; low stockpiles (< 2 m) only when direct return is not possible, respread as soon as practicable (ideally < 12 months).', 'Topsoil.', '—'),
            'mn_pond': _c('Control sediment from pits and roads.', 'Earthen sediment pond (3:1 inner banks) with rock-armoured spillway at the low point; pit sump pumped to it by a skid-mounted pump; clean-water diversion drains keep runoff out of the pit; settled water reused for dust suppression.', 'Earth / clay.', 'Desilt before the wet season.'),
            'mn_rompad': _c('Blend and buffer ore.', 'ROM pad ~3–6 ha with grade-bin finger stockpiles (~8–10 kt each, 35–37° sides, ~2–3 days of ROM), reclaimed by wheel loader into trucks (or load-and-carry ≤ 150 m where the pad adjoins the tipping deck) to keep the feed within the blend targets.', 'Bauxite.', '—'),
            'mn_gc': _c('Define ore, waste and grade bins before digging.', 'RC/aircore grade-control holes on a ~7.5–15 m grid with 0.5–1 m samples assayed for available Al₂O₃ and reactive SiO₂; polygons loaded into excavator GPS guidance and the FMS.', '—', 'Drilled after clearing, ahead of stripping.'),
            'mn_drill': _c('Drill the caprock blast pattern.', 'See the detailed blast-hole drill model.', '—', '—'),
            'mn_pattern': _c('Holes ready for charging.', 'Blast pattern ~3.0 × 3.5 m (burden × spacing) drilled through the caprock with ~0.3–0.5 m sub-drill; holes logged and dipped before charging.', 'Caprock.', 'Front row ~3 m (one burden) from the free face.'),
            'mn_grader': _c('Keeps haul roads smooth, crowned and drained.', 'Motor grader (~14–16 ft blade) trims the wearing course, restores crossfall and drains and rebuilds windrows; works with the water cart.', '—', 'Every shift on main haul roads; rolling resistance target ~2–3 %.'),
            'mn_lv': _c('Move people and small loads around the mine.', 'Light vehicles with buggy whips, flags, beacons and FMS proximity tags; parked in bunded bays set back from haul roads; give way to haul trucks and keep out of their blind spots.', '—', 'Highest fatality risk: light/heavy vehicle interaction.'),
            'mn_wc': _c('Control dust and rolling resistance; first response to fires.', 'Haul-truck chassis with a ~70–100 kL water tank, rear spray bar and a cab-controlled cannon; fills from the sediment pond / standpipes.', 'Steel tank.', '~1–2 L/m² per pass, several passes per shift in the dry season; avoid over-watering ramps.'),
            'mn_loader': _c('Reclaim ROM-pad grade bins for blending.', 'Loads trucks at the fingers (or load-and-carry ≤ 150 m where the pad adjoins the tipping deck). See the detailed wheel loader model.', '—', '—'),
            'mn_excavator': _c('Primary loading units.', 'Stand on the exposed ore ≥ 4 m back from the crest and top-load trucks on the floor below, swinging ~30–45° to the side of the body (never over the cab); dig to ~0.1–0.3 m above the clay floor. See the detailed hydraulic excavator model.', '—', '—'),
            'mn_dozer': _c('Clearing, stripping, ripping, stockpiling.', 'See the detailed crawler dozer model.', '—', '—'),
            'mn_truck': _c('Haul ore to the sizing station.', 'See the detailed haul truck model.', '—', '—'),
            'mn_station': _c('Size the ore for the overland conveyor.', 'See the detailed primary sizing station model.', '—', '—')}},
    'm2p_primary_sizing_station': {
        'summary': ('The primary sizing station turns run-of-mine bauxite into a conveyable product. Haul trucks tip from two sides into a lined dump hopper; '
                    'a pedestal rock breaker deals with oversize; an apron feeder draws ore out at a controlled rate into a twin-shaft mineral sizer that '
                    'reduces lumps up to ~1.2–1.5 m to minus ~200 mm; the product drops onto a sacrificial conveyor that passes under a self-cleaning tramp '
                    'magnet and a metal detector before the overland conveyor.'),
        'classification': {'family': 'Mining — primary sizing', 'type': 'Two-sided truck dump, apron feeder, twin-shaft sizer, discharge conveyor'},
        'model_configuration': {'scale': 'Real size (metres)', 'animation': 'Feeder pans advance, sizer shafts counter-rotate, ore lumps are sized and conveyed (10 s)',
                                'basis': 'Reference-plant design basis A01 (nominal ~1,300–1,500 t/h, design 1,800 t/h to the overland; equipment rated ~2,000–2,400 t/h); generic twin-shaft sizer class'},
        'standards': [{'code': 'AS 1755 / ISO 5048', 'title': 'Conveyors — safety requirements / belt conveyor calculation', 'relevance': 'Discharge conveyor'},
                      {'code': 'ISO 14122', 'title': 'Safety of machinery — Permanent means of access', 'relevance': 'Platforms, stairs, handrails'},
                      {'code': 'Site dump-design standard / regulator guidance (e.g. WA & QLD mine dump and windrow guidance)', 'title': 'Dump-point wheel stops and windrows ≥ ½ the largest tyre diameter', 'relevance': 'Wheel stops'}],
        'references': ['Reference-plant design basis (A01) — knowledge-based', 'Sizer and apron-feeder vendor class literature (generic)', 'CEMA Belt Conveyors for Bulk Materials, 7th ed.'],
        'components': {
            'ps_civil': _c('Lets trucks reverse up and tip safely from both sides.', 'Mechanically stabilised earth (MSE) or RC walls retaining two tipping pads ~10 m high, each large enough for a 90 t truck to turn and reverse (≈ 30–35 m clear); ramps; concrete wheel-stop bunds ≥ ½ the wheel height of the largest machine using the dump (1.55 m: the 45/65R45 wheel loader also tips here); traffic lights tell drivers when to tip.', 'Reinforced concrete, compacted fill.', 'Truck tipping ~45–75 s.', ['Bund damage', 'Spillage on decks'], ['Inspect bunds and lighting each shift']),
            'ps_hopper': _c('Buffers truck deliveries so the feeder and sizer run steadily.', 'Steel hopper inside the concrete pocket; bolted 400–500 HB AR-plate liners, rock-box ledges at the impact zone, skirts down to the feeder, dust-spray ring.', 'AR steel liners.', 'Live capacity ~200–300 t (2–3 truck loads).', ['Liner wear', 'Bridging of sticky clayey ore'], ['Liner thickness survey', 'Keep a level to avoid direct impact on the pans']),
            'ps_breaker': _c('Breaks oversize and dislodges bridged ore without people entering the hopper.', 'Pedestal-mounted boom and stick with a ~2 t hydraulic hammer, slew base, power pack and an operator cabin overlooking the hopper.', 'Steel.', 'Boom reach ~8–10 m.', ['Hammer tool wear'], ['Hammer and boom inspection']),
            'ps_feeder': _c('Draws ore from the hopper at a controlled rate and protects the sizer from the dumping impact.', 'Heavy apron feeder: 3.0 m manganese-steel pans on two chain strands, skirts inside the pan flights (2.6 m clear), impact rails under the hopper, ~12 carry rollers, head shaft with two shaft-mounted planetary gearboxes and motors (~2 × 132–160 kW, VFD), tail take-ups and a dribble conveyor beneath.', 'Cast manganese steel pans, alloy chains.', 'Pan speed ~0.03–0.25 m/s; capacity up to ~2,400 t/h.', ['Pan cracking', 'Chain/roller wear', 'Spillage under the feeder'], ['Pan and chain inspection; clean the dribble belt']),
            'ps_sizer': _c('Contains the shafts and guides material through them.', 'Heavy fabricated box with replaceable side liners, breaker combs, bearing housings and a discharge chute.', 'Steel, wear liners.', '—', ['Liner wear'], ['Comb and liner gauging']),
            'ps_shafts': _c('Break the ore by tension and shear between counter-rotating teeth (low speed, high torque).', 'Two shafts with rings of three replaceable horn-type teeth in a scroll pattern; the rings of one shaft sit between those of the other; slow inward counter-rotation draws lumps into the nip; oversize is scrolled along; a central breaker bar beneath gives the third breaking stage.', 'Forged shafts; hard-faced tooth tips.', 'Speed ~50–100 rpm; product –200 mm.', ['Tooth tip wear → oversize product', 'Tramp steel damage'], ['Measure tooth height; rebuild by hardfacing']),
            'ps_drives': _c('Drive each shaft.', 'Per shaft: TEFC motor (~300–450 kW), fluid coupling (soft start, overload slip), right-angle gearbox and gear coupling; reversing on jam.', 'Steel.', 'Total installed ~2 × 300–450 kW.', ['Fluid-coupling fusible plug blow on jams'], ['Oil analysis; coupling oil level']),
            'ps_conveyor': _c('Carries sized ore from under the sizer to the overland transfer.', '1,400 mm fabric belt on 35° troughed idlers with impact beds in the loading zone, walkway and handrail, head drive at the transfer.', 'Rubber belt, steel structure.', 'Belt speed ~2.5–3 m/s; capacity up to ~2,400 t/h.', ['Belt rip from tramp steel', 'Spillage'], ['Daily belt walk; belt scanner']),
            'ps_tramp': _c('Remove and detect tramp steel (bucket teeth, drill steel) before it reaches the overland belt.', 'Suspended self-cleaning overband magnet discharging to a tramp chute; balanced-coil metal detector with non-metallic idler zone and marker spray, placed so the belt can stop before the metal reaches the head; belt scale and rip detector. Austenitic manganese steel (feeder pans, liners, hammer tools) is non-magnetic — only the metal detector catches it.', 'Steel, non-metallic frame.', '—', ['Missed detections when sensitivity drifts'], ['Test with test pieces each shift']),
            'ps_electrical': _c('Power and control for the station.', 'E-house with MCC, VFDs and PLC; transformer; lighting mast; CCTV for the tipping decks.', '—', '—'),
            'ps_ore': _c('Bauxite being sized.', 'ROM lumps up to ~1.2–1.5 m; product –200 mm (P80 ~100–130 mm).', 'Bauxite.', '—')}},
    'm2p_crawler_dozer': {
        'summary': ('The ~70 t crawler dozer clears vegetation, strips topsoil and overburden, rips the softer caprock and ore where blasting is not needed, '
                    'builds and maintains ROM-pad stockpiles and haul-road edges, and shapes the landform for rehabilitation. A semi-U blade pushes '
                    'material; a single-shank parallelogram ripper at the rear breaks hard ground to about 1–1.5 m depth.'),
        'classification': {'family': 'Mining — support & ground preparation', 'type': 'Crawler dozer, ~70 t class, semi-U blade, single-shank ripper'},
        'model_configuration': {'scale': 'Real size (metres)', 'animation': 'Real-time 30 s: dozes 6 m forward in F1 with the blade in the cut, reverses, sets the ripper tip and rips 3 m forward, lifts, reverses',
                                'basis': 'Generic ~70 t dozer envelope (published class data, e.g. D10 / D375 class); conventional oval undercarriage shown'},
        'standards': [{'code': 'ISO 6747', 'title': 'Earth-moving machinery — Dozers — Terminology and commercial specifications', 'relevance': 'Terms, blade capacity'},
                      {'code': 'ISO 9246', 'title': 'Earth-moving machinery — Crawler and wheel tractor dozer blades — Volumetric ratings', 'relevance': 'Blade capacity'},
                      {'code': 'ISO 3471 / ISO 3449', 'title': 'ROPS / FOPS', 'relevance': 'Cab protection'}],
        'references': ['OEM specification sheets for the ~70 t dozer class (generic envelope)', 'SME Mining Engineering Handbook, 3rd ed. — dozing and ripping'],
        'components': {
            'dz_undercarriage': _c('Gives traction and flotation for pushing and ripping.', 'Two track roller frames with idlers, rollers and rear drive sprockets; sealed and lubricated track chains with single-grouser shoes (~0.6 m); equaliser bar. Either conventional oval (shown) or elevated-sprocket design; the elevated sprocket keeps the final drives above ground impact and abrasive mud.', 'Forged and cast steel.', 'Ground speed ~ 3–4 km/h dozing.', ['Track wear in abrasive laterite'], ['Undercarriage measurement program']),
            'dz_body': _c('Carries the powertrain and protects the operator.', 'Main frame, engine enclosure, radiator guard, fuel tank, ROPS/FOPS cab (ROPS height ≈ 4.1–4.2 m) with joystick controls, GNSS antennas, access steps.', 'Steel.', '—', ['Radiator blockage from dust'], ['Clean cores; check guards']),
            'dz_drive': _c('Delivers power to the tracks and steers.', 'Diesel (~450 kW class), torque converter, planetary powershift transmission, steering by wet multi-disc steering clutches and brakes (differential steer is used mainly on smaller classes), double-reduction final drives.', 'Steel.', '—', ['Final-drive seal leaks'], ['Oil analysis']),
            'dz_blade': _c('Pushes material.', 'Semi-U blade (~4.9 m wide, ~18–19 m³) with replaceable cutting edges and end bits on push arms pinned to trunnions on the track frames; tilt brace/cylinder.', 'High-strength steel, through-hardened edges.', '—', ['Cutting-edge wear'], ['Turn/replace edges before the mouldboard wears']),
            'dz_load': _c('Material being pushed.', 'Laterite/topsoil roll in front of the blade.', '—', '—'),
            'dz_ripper': _c('Breaks hard ground so it can be dozed or dug.', 'Parallelogram linkage keeps the shank angle constant; single shank with pin-pocket depth setting, replaceable tip and shank protector; max penetration ≈ 1.5 m (standard shank), ≈ 2 m with a deep-ripping shank.', 'Alloy steel; cast tip.', 'Ripping speed slow (first gear); rip downhill when possible.', ['Tip wear/loss'], ['Inspect tip each shift']),
            'dz_cyl': _c('Lift the blade and the ripper.', 'Double-acting hydraulic cylinders.', 'Steel, chrome rods.', '—', ['Seal leaks'], ['Drift check'])}},
    'm2p_hydraulic_excavator': {
        'summary': ('The ~200 t diesel-hydraulic backhoe excavator is the primary loading unit in the bauxite pit. It digs the friable ore (and blasted caprock) '
                    'with an ~11–12 m³ bucket, swings and loads ~90 t trucks in about five to six passes. Everything moves hydraulically: the diesel '
                    'drives piston pumps; joysticks pilot the control valves that feed the boom, arm and bucket cylinders, swing motors and travel motors.'),
        'classification': {'family': 'Mining — load & haul', 'type': 'Hydraulic backhoe excavator, ~200 t class, diesel'},
        'model_configuration': {'scale': 'Real size (metres)', 'animation': 'Real-time 30 s cycle: dig ~3 m below track level (arm crowd + bucket curl), loaded swing ~65°, dump, return; stairway stays raised',
                                'basis': 'Generic ~200 t backhoe envelope (published class data, e.g. PC2000 / R9200 class); not any one product'},
        'standards': [{'code': 'ISO 6165', 'title': 'Earth-moving machinery — Basic types — Identification and terms', 'relevance': 'Terminology'},
                      {'code': 'ISO 7451 / ISO 7546', 'title': 'Hydraulic excavator buckets — volumetric rating', 'relevance': 'Bucket capacity'},
                      {'code': 'ISO 10262', 'title': 'Hydraulic excavators — Operator protective guards', 'relevance': 'Front/top guards (OPG)'},
                      {'code': 'ISO 2867', 'title': 'Earth-moving machinery — Access systems', 'relevance': 'Stairway, walkways, handrails'}],
        'references': ['OEM specification sheets for the ~200 t backhoe class (generic envelope)', 'SME Mining Engineering Handbook, 3rd ed. — loading equipment'],
        'components': {
            'ex_undercarriage': _c('Carries the machine and lets it travel and stand on soft pit floors.', 'Carbody with two track frames; each with front idler, rear drive sprocket on a planetary final drive and hydraulic travel motor, ~8 track rollers, carrier rollers and a chain of cast shoes (~0.8 m wide).', 'Cast and forged steel.', 'Ground pressure ~ 0.2–0.25 MPa; travel ~ 2–3 km/h.', ['Track pin/bushing and roller wear', 'Final-drive leaks'], ['Measure track sag and wear; check final-drive oil']),
            'ex_swing': _c('Lets the upper structure rotate 360° on the undercarriage.', 'Large three-row roller slewing bearing with an internal ring gear driven by the swing pinions; centre (rotary) joint passes oil to the travel motors.', 'Forged bearing steel.', 'Swing speed ~ 4–5 rpm (class typical).', ['Bearing wear/rocking', 'Pinion and ring-gear tooth wear'], ['Measure bearing rock (tilt) clearance; grease ring gear']),
            'ex_upper': _c('Carries the power module, cab, tanks and counterweight; balances the loaded front attachment.', 'Welded revolving frame with walkways and handrails; rear counterweight; elevated cab with operator guard; coolers; fuel tank (~3,000–3,500 L); GNSS antennas; auto-lube; fire-suppression bottles.', 'Steel.', 'Tail-swing radius ~ 5.3–5.6 m: keep people and vehicles clear of the swing zone.', ['Cracks at the boom-foot brackets'], ['Structural inspection of high-stress welds']),
            'ex_power': _c('Produces and controls the hydraulic power.', 'Diesel engine (~700–800 kW class, typically V12/V16) driving a pump drive gearbox with several variable-displacement axial-piston pumps; main control valve blocks; swing motors with planetary reducers.', 'Cast iron, steel.', 'System pressure up to ~30–32 MPa (class typical).', ['Hydraulic contamination', 'Pump wear → slow cycles'], ['Oil sampling and filter changes; cycle-time checks']),
            'ex_access': _c('Safe access from the ground to the machine.', 'Hydraulically raised and lowered stairway at about 40–45°; interlocked so the machine cannot swing or travel while it is down.', 'Steel, grating.', '—', ['Interlock faults'], ['Test the interlock daily']),
            'ex_boom': _c('Lifts the arm and bucket.', 'Welded high-strength-steel box section, banana-shaped; pinned to the upper frame at the boom foot and lifted by two boom cylinders.', 'High-strength steel.', 'Fatigue loading every pass.', ['Fatigue cracks at the boom foot and cylinder bosses'], ['NDT of known crack sites']),
            'ex_arm': _c('Pulls the bucket through the dig (crowd) and reaches out.', 'Welded box section pinned to the boom tip; the arm cylinder acts on the crowd lever above the arm pin.', 'High-strength steel.', '—', ['Cracks, pin and bush wear'], ['Measure pin clearances']),
            'ex_bucket': _c('Digs and carries the bauxite.', 'Backhoe bucket ~11–12 m³ heaped (~3.1 m wide) with cast lip, adapters and replaceable teeth, side cutters and wear plates.', 'Abrasion-resistant steel; cast teeth.', 'Fill factor ~0.9–1.0 in friable bauxite (engineering estimate).', ['Tooth loss → sizer damage', 'Lip wear'], ['Inspect teeth every shift; GET (ground-engaging tool) monitoring']),
            'ex_load': _c('Bauxite carried each pass.', 'About 14–17 t per pass (11.5 m³ × 0.9 fill × ~1.45–1.6 t/m³ loose; engineering estimate).', 'Bauxite.', '—'),
            'ex_bench': _c('Ground the machine stands and digs on.', 'Bench top at track level; ore dug down to the floor in front.', 'Bauxite / clay floor.', '—'),
            'ex_linkage': _c('Turns the bucket cylinder stroke into a large bucket rotation.', 'Side links from the arm and an H-link (power link) to the bucket, forming a four-bar linkage.', 'Steel, pins and bushes.', '—', ['Pin/bush wear'], ['Grease (auto-lube)']),
            'ex_cylinders': _c('Move the boom, arm and bucket.', 'Double-acting hydraulic cylinders: two boom cylinders, one arm cylinder, one bucket cylinder, with load-holding valves.', 'Steel barrels, chrome-plated rods.', 'Pressure up to ~30–32 MPa.', ['Rod scoring', 'Seal leaks → drift'], ['Drift test; inspect rods'])}},
    'm2p_haul_truck': {
        'summary': ('A rigid-frame rear-dump haul truck carries run-of-mine bauxite from the excavator face to the primary sizing station or the ROM pad. '
                    'This ~90 t payload class (≈ 163 t gross) is mechanical drive: a ~750 kW V12 diesel drives the rear duals through a torque converter, '
                    'a 7-speed planetary powershift transmission, a differential and planetary final drives. Two telescopic hoist cylinders tip the body to '
                    'about 45–50° to dump in roughly 12–15 s.'),
        'classification': {'family': 'Mining — load & haul', 'type': 'Rigid rear-dump haul truck, mechanical drive, ~90 t class'},
        'model_configuration': {'scale': 'Real size (metres)', 'animation': 'Dump cycle in real time (30 s): body raises to ~48° in ~13.5 s, payload slides from ~23°, body lowers in ~10 s',
                                'basis': 'Generic ~90 t class envelope (published specification sheets of this class, e.g. 777-class); not any one product'},
        'standards': [{'code': 'ISO 3471', 'title': 'Earth-moving machinery — Roll-over protective structures (ROPS)', 'relevance': 'Cab protection'},
                      {'code': 'ISO 3449', 'title': 'Earth-moving machinery — Falling-object protective structures (FOPS)', 'relevance': 'Cab protection'},
                      {'code': 'ISO 3450', 'title': 'Earth-moving machinery — Wheeled or high-speed rubber-tracked machines — Braking systems', 'relevance': 'Service, secondary and parking brakes'},
                      {'code': 'ISO 2867', 'title': 'Earth-moving machinery — Access systems', 'relevance': 'Stairway, handrails, deck'},
                      {'code': 'ISO 5010', 'title': 'Earth-moving machinery — Wheeled machines — Steering requirements', 'relevance': 'Steering'}],
        'references': ['Manufacturer performance handbooks for the ~90 t rigid truck class (e.g. Caterpillar Performance Handbook, 777-class)',
                       'SME Mining Engineering Handbook (3rd ed.) — haulage', 'Tyre and Rim Association — 27.00R49 OTR tyre data'],
        'components': {
            'ht_frame': _c('Carries every load: engine, cab, body and payload, and transmits them to the axles.', 'Two deep box-section rails of high-strength steel joined by cross-members; cast nodes at high-stress points; rear horns carry the body pivot pins.', 'High-strength low-alloy steel; cast steel nodes.', 'Fatigue loading on rough haul roads.', ['Fatigue cracks at welds and cross-member joints'], ['Frame crack inspection (visual/MPI) at service intervals']),
            'ht_tyre': _c('Supports the ~163 t gross machine and gives traction; the tyres are the largest operating cost after fuel and labour.', 'Radial OTR tyres (27.00R49 class, ~2.7 m diameter) on five-piece rims (rim base, bead seat band, flanges, lock ring); rear duals.', 'Rubber compounds with steel-cord carcass; steel rims.', 'Inflation ~6.5–7 bar cold (nitrogen recommended); limited by the tonne-km-per-hour (TKPH) rating.', ['Cuts from spillage rock', 'Heat separation when TKPH is exceeded', 'Rim/lock-ring failure — explosive energy'], ['Daily pressure and cut check', 'Keep haul roads clean', 'Never stand in line with the rim/lock-ring (sidewall) during inflation or deflation; inflate in a cage or with a remote inflator']),
            'ht_suspension': _c('Cushions the frame and gives ride comfort and tyre load sharing; steering turns the front wheels.', 'Self-contained nitrogen-over-oil suspension cylinders (struts) at each front wheel and two at the rear axle (mounted to the frame kick-up); rear axle located by an A-frame with a centre ball joint and a lateral (panhard) link; strut pressures feed the payload monitor; hydraulic steering cylinders and tie rod.', 'Steel, chrome-plated rods, nitrogen and oil.', 'Charge height and pressure set to the manufacturer chart.', ['Low strut charge (bottoming, frame cracks)', 'Seal leaks'], ['Check strut charge heights', 'Inspect for leaks']),
            'ht_engine': _c('Produces the driving power (~750 kW class).', 'V12 four-stroke diesel, about 32 L displacement, twin turbochargers and air-to-air aftercooling; electronic unit injection.', 'Cast iron block and heads.', 'Rated speed ~1,750 rpm; fuel use roughly 60–110 L/h depending on haul profile (engineering estimate).', ['Dust ingestion through damaged air cleaners', 'Overheating from a blocked radiator'], ['Air filter restriction indicator', 'Oil analysis (S·O·S) every service']),
            'ht_radiator': _c('Rejects engine and retarder heat to the air.', 'Modular core radiator, hydraulically or engine-driven fan, shroud, front grill.', 'Aluminium/copper cores.', 'Retarding on long downhill hauls loads the cooling system heavily.', ['Core blockage with dust/mud'], ['Wash cores; check coolant']),
            'ht_transmission': _c('Selects gear ratios so the engine stays in its best speed range.', 'Torque converter with lock-up clutch feeding a 7-speed planetary powershift transmission; drive shaft with universal joints to the differential.', 'Steel gears, clutch packs.', 'Electronic clutch pressure control; automatic shifting.', ['Clutch wear from abusive shifting'], ['Oil analysis; shift quality checks']),
            'ht_axle': _c('Divides torque between the rear wheels and multiplies it; brakes and retards the truck.', 'Differential and bevel gear set; planetary final drive in each wheel; oil-cooled multiple-disc service/retarder brakes at the rear (spring-applied, hydraulically released parking brake); dry-disc caliper service brakes on the front wheels; brake cooling oil passes through oil-to-water coolers to the radiator.', 'Steel gears, friction discs running in cooled oil.', 'Brakes double as the retarder on downhill hauls (oil cooled).', ['Brake oil overheating on long descents', 'Final drive gear wear'], ['Brake wear indicator', 'Oil analysis of final drives']),
            'ht_hood': _c('Encloses and protects the engine; doors give service access.', 'Formed sheet-steel enclosure with louvres and hinged doors.', 'Steel.', '—'),
            'ht_deck': _c('Safe access to the cab and service points; carries air cleaners, exhaust and lights.', 'Grated upper deck with handrails, diagonal front stairway (≈ 40°), air cleaners, muffler, LED work lights and mirrors.', 'Steel, galvanised grating.', 'Three points of contact on stairs; walk only on the deck.', ['Damaged handrails'], ['Pre-start walk-around']),
            'ht_cab': _c('Protects and houses the operator.', 'ROPS/FOPS certified, pressurised, air-conditioned cab on the left of the deck; seat with belt, steering wheel, dash and monitoring display.', 'Steel structure, laminated glass.', 'Pressurised to keep dust out.', ['Seal damage → dust ingress'], ['Check door seals and pressuriser filter']),
            'ht_tanks': _c('Store fuel and hydraulic oil; batteries for starting.', 'Fuel tank on the left frame rail; hoist/brake/steering hydraulic tank on the right with sight glass; lockable battery box.', 'Steel.', '—'),
            'ht_body': _c('Carries the payload and tips it out at the dump point.', 'Welded high-hardness steel body with flat floor and tail chute, side ribs, front canopy extending over the cab (protects it while loading) and rock ejectors that knock stones from between the rear duals.', 'Abrasion-resistant (≈ 400–500 HB) plate liners on the floor.', 'Heaped (2:1) capacity about 60–65 m³; dump angle about 45–50°.', ['Floor wear', 'Carry-back of sticky bauxite'], ['Measure floor thickness', 'Hose out carry-back']),
            'ht_payload': _c('Run-of-mine bauxite being hauled.', 'About 90 t per load (≈ 60–64 m³ at ~1.4–1.5 t/m³ loose — the body is close to full heaped capacity, so bauxite haulage tends to be volume-limited; body volume/sideboards are selected for the ore density).', 'Lateritic bauxite lumps and fines.', 'Over-loading beyond the 10/10/20 rule shortens frame and tyre life.', ['Spillage onto the road → tyre cuts'], ['Payload monitor reading each load']),
            'ht_hoist': _c('Raise and lower the body.', 'Two telescopic hoist cylinders (barrel on the frame, top stage on the body), fed by the hoist pump and a pilot-operated hoist valve with RAISE, HOLD, FLOAT and LOWER positions.', 'Steel barrels, chrome-plated stages.', 'Raise time ≈ 12–15 s, lower ≈ 10–14 s (class typical); travel with the lever in FLOAT so the body rests on the frame pads.', ['Seal leakage → body creep', 'Bent stage if dumping on a side slope'], ['Never travel with the body raised', 'Body safety pin/cable when working under a raised body'])}},
}

BUILDERS = {'m2p_haul_truck': m2p_haul_truck, 'm2p_hydraulic_excavator': m2p_hydraulic_excavator, 'm2p_crawler_dozer': m2p_crawler_dozer, 'm2p_primary_sizing_station': m2p_primary_sizing_station, 'm2p_mine_overview': m2p_mine_overview, 'm2p_blasthole_drill': m2p_blasthole_drill, 'm2p_wheel_loader': m2p_wheel_loader}
