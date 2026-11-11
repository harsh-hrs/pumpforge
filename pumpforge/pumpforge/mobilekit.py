"""Mobile-equipment kit (real scale, metres, Blender Z up, x = forward): earthmover tyres and rims, crawler
track assemblies, operator cabs with ROPS/FOPS, hydraulic cylinders that animate between two moving pins,
lights and mirrors. Used by the Mine-to-Port mining fleet (haul truck, excavator, dozer, loader, drill, grader)."""
import math
from mathutils import Matrix, Vector
from .core import lathe, cyl, box, join, transform, TAU, OPERATE_FRAMES
from .plant3d import frame, placed, bar, rod
from .shapes import sweep_tube

V = Vector


# ------------------------------------------------------------------ tyres & rims
def otr_tyre(name, R, W, center, lugs=36, mat='tyre', tread=True):
    """Off-the-road radial tyre (E-4 rock type) on an axle along Y: rounded carcass + staggered chevron lugs."""
    cx, cy, cz = center
    rb = R * 0.58                                    # bead seat (rim flange) radius
    sw = W / 2
    prof = [(rb, -sw * 0.82), (R * 0.80, -sw), (R * 0.93, -sw * 0.96), (R * 0.985, -sw * 0.78), (R - 0.04, -sw * 0.45), (R - 0.04, sw * 0.45),
            (R * 0.985, sw * 0.78), (R * 0.93, sw * 0.96), (R * 0.80, sw), (rb, sw * 0.82)]
    objs = [lathe(name + 'c', prof, mat, 72, axis='Y', center=(cx, cy, cz))]
    if tread:
        lw, lh = W * 0.42, 0.06
        for k in range(lugs):
            for s in (-1, 1):
                a = TAU * (k + (0.5 if s > 0 else 0.0)) / lugs
                lug = box(f'{name}l{k}{s}', (R * TAU / lugs * 0.55, lw, lh), (0, s * (sw * 0.47), 0), mat)
                lug.data.transform(Matrix.Rotation(s * 0.28, 4, 'Z'))
                lug.data.transform(Matrix.Translation((0, 0, R - 0.04 + lh / 2 - 0.01)))
                lug.data.transform(Matrix.Rotation(a, 4, 'Y'))
                lug.data.transform(Matrix.Translation((cx, cy, cz)))
                objs.append(lug)
    return join(name, objs)


def otr_rim(name, R_tyre, W, center, side=1, nuts=24, mat='paint_grey', dual_inner=False):
    """Five-piece earthmover rim (base, flanges, bead seat band, lock ring) with mounting disc and wheel nuts.
    side = +1 if the outer face is +y."""
    cx, cy, cz = center
    rb = R_tyre * 0.58
    sw = W / 2
    objs = [lathe(name + 'b', [(rb - 0.05, -sw * 0.9), (rb, -sw * 0.9), (rb + 0.06, -sw * 0.84), (rb + 0.06, -sw * 0.78), (rb, -sw * 0.74),
                               (rb, sw * 0.74), (rb + 0.06, sw * 0.78), (rb + 0.06, sw * 0.84), (rb, sw * 0.9), (rb - 0.05, sw * 0.9)], mat, 64, axis='Y', center=(cx, cy, cz))]
    zf = side * sw * 0.2
    objs.append(cyl(name + 'd', rb - 0.04, cy + zf - 0.03, cy + zf + 0.03, mat, 48, axis='Y', center=(cx, 0, cz), r_in=rb * 0.38))
    objs.append(cyl(name + 'h', rb * 0.4, cy + zf - 0.12, cy + zf + 0.14 * side, 'steel_dark', 40, axis='Y', center=(cx, 0, cz)))
    for k in range(nuts):
        a = TAU * k / nuts
        x, z = cx + rb * 0.48 * math.cos(a), cz + rb * 0.48 * math.sin(a)
        y0 = cy + zf + side * 0.03
        objs.append(cyl(f'{name}n{k}', 0.028, min(y0, y0 + side * 0.05), max(y0, y0 + side * 0.05), 'steel_dark', 6, axis='Y', center=(x, 0, z)))
    # lock ring gap marker and valve stem
    objs.append(box(name + 'lr', (0.03, 0.03, 0.06), (cx, cy + side * sw * 0.86, cz + rb + 0.03), 'steel_dark'))
    objs.append(cyl(name + 'vs', 0.012, cy + side * sw * 0.7, cy + side * (sw * 0.7 + 0.06), 'brass', 8, axis='Y', center=(cx + rb * 0.7, 0, cz - rb * 0.7)))
    return join(name, objs)


def wheel_keys(m, part, revs=1.0, axis='Y'):
    part.spin(axis, revs)


# ------------------------------------------------------------------ crawler tracks
def crawler_track(name, x0, x1, y, z_axle, R_idler, width, shoe_pitch=0.3, rollers=8, carriers=2, mat='steel_dark', frame_mat='mine_yellow', grouser=True, sprocket_rear=True):
    """Crawler undercarriage on one side: track frame, front idler, rear (or front) drive sprocket, track rollers, carrier
    rollers, and a continuous chain of shoes with grousers. Returns (static, moving_shoes) objects."""
    zt = z_axle                                        # idler / sprocket centre height
    L = x1 - x0
    st = [box(name + 'tf', (L - 2 * R_idler * 1.05, width * 0.42, R_idler * 0.62), ((x0 + x1) / 2, y, zt + R_idler * 0.12), frame_mat, bevel=0.02)]
    for k in range(int((L - 2 * R_idler) / 0.9)):                                    # roller guards / frame webs
        st.append(box(f'{name}wb{k}', (0.06, width * 0.44, R_idler * 0.5), (x0 + R_idler * 1.3 + k * 0.9, y, zt - R_idler * 0.3), frame_mat))
    st.append(cyl(name + 'id', R_idler, y - width * 0.2, y + width * 0.2, 'steel', 40, axis='Y', center=(x1 - R_idler, 0, zt)))
    xs = x0 + R_idler if sprocket_rear else x1 - R_idler
    st.append(cyl(name + 'sp', R_idler * 1.05, y - width * 0.18, y + width * 0.18, 'steel', 40, axis='Y', center=(x0 + R_idler, 0, zt + 0.0)))
    for k in range(int(R_idler * 2 * math.pi / 0.25)):
        a = TAU * k / int(R_idler * 2 * math.pi / 0.25)
        st.append(box(f'{name}st{k}', (0.09, width * 0.34, 0.12), (x0 + R_idler + math.cos(a) * R_idler * 1.08, y, zt + math.sin(a) * R_idler * 1.08), 'steel'))
    # final drive hub (outboard of sprocket)
    st.append(cyl(name + 'fd', R_idler * 0.8, y + (width * 0.18 if y > 0 else -width * 0.5), y + (width * 0.5 if y > 0 else -width * 0.18), frame_mat, 40, axis='Y', center=(x0 + R_idler, 0, zt)))
    zr = zt - R_idler + 0.17
    for k in range(rollers):
        x = x0 + R_idler * 1.6 + (L - R_idler * 3.2) * k / max(1, rollers - 1)
        st.append(cyl(f'{name}tr{k}', 0.15, y - width * 0.2, y + width * 0.2, 'steel', 20, axis='Y', center=(x, 0, zr)))
    for k in range(carriers):
        x = x0 + L * (0.33 + 0.34 * k / max(1, carriers - 1) if carriers > 1 else 0.5)
        st.append(cyl(f'{name}cr{k}', 0.11, y - width * 0.15, y + width * 0.15, 'steel', 16, axis='Y', center=(x, 0, zt + R_idler - 0.12)))
    # shoes along the loop (straight top/bottom, semicircles round idler and sprocket)
    xa, xb = x0 + R_idler, x1 - R_idler
    Rt = R_idler + 0.06
    per = 2 * (xb - xa) + TAU * Rt
    n = int(per / shoe_pitch)
    mv = []
    for k in range(n):
        s = per * k / n
        mv.append(_shoe_at(f'{name}s{k}', s, xa, xb, zt, Rt, y, width, shoe_pitch, mat, grouser))
    return join(name + 'S', st), join(name + 'M', mv), (xa, xb, zt, Rt, per)


def track_point(s, xa, xb, zt, Rt):
    """Point and outward normal angle on the track loop at arc length s (bottom run goes forward)."""
    L = xb - xa
    per = 2 * L + TAU * Rt
    s %= per
    if s < L:                                        # bottom run, rear -> front
        return V((xa + s, 0, zt - Rt)), -math.pi / 2
    s -= L
    if s < math.pi * Rt:                             # round the front idler
        a = -math.pi / 2 + s / Rt
        return V((xb + Rt * math.cos(a), 0, zt + Rt * math.sin(a))), a
    s -= math.pi * Rt
    if s < L:                                        # top run, front -> rear
        return V((xb - s, 0, zt + Rt)), math.pi / 2
    s -= L
    a = math.pi / 2 + s / Rt
    return V((xa + Rt * math.cos(a), 0, zt + Rt * math.sin(a))), a


def _shoe_at(name, s, xa, xb, zt, Rt, y, width, pitch, mat, grouser):
    p, a = track_point(s, xa, xb, zt, Rt)
    objs = [box(name + 'p', (pitch * 0.92, width, 0.035), (0, 0, 0), mat)]
    if grouser:
        objs.append(box(name + 'g', (0.04, width, 0.07), (0, 0, -0.05), mat))
    objs.append(box(name + 'l', (pitch * 0.95, width * 0.32, 0.09), (0, 0, 0.06), 'steel'))
    o = join(name, objs)
    # local -z points outward (grouser to the ground on the bottom run)
    rot = Matrix.Rotation(-(a + math.pi / 2), 4, 'Y')
    o.data.transform(Matrix.Translation((p.x, y, p.z)) @ rot)
    return o


# ------------------------------------------------------------------ cabs, ROPS, access, lights
def cab(name, x0, x1, y0, y1, z0, z1, frame_mat='mine_yellow', door_side=+1, wipers=True):
    """Pressurised operator cab: ROPS/FOPS posts, roof, tinted glass on all sides, door, wipers, beacon."""
    t = 0.07
    objs = [box(name + 'fl', (x1 - x0, y1 - y0, 0.12), ((x0 + x1) / 2, (y0 + y1) / 2, z0 + 0.06), frame_mat),
            box(name + 'rf', (x1 - x0 + 0.12, y1 - y0 + 0.12, 0.14), ((x0 + x1) / 2, (y0 + y1) / 2, z1 - 0.07), frame_mat, bevel=0.03),
            box(name + 'gl', (x1 - x0 - 0.04, y1 - y0 - 0.04, z1 - z0 - 0.4), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2 + 0.06), 'cab_glass')]
    for x in (x0, x1):
        for yy in (y0, y1):
            objs.append(box(f'{name}p{x:.2f}{yy:.2f}', (t, t, z1 - z0), (x + (t / 2 if x == x0 else -t / 2), yy + (t / 2 if yy == y0 else -t / 2), (z0 + z1) / 2), frame_mat))
    xm = (x0 + x1) / 2
    for yy in (y0, y1):
        objs.append(box(f'{name}pm{yy:.2f}', (t * 0.8, t, z1 - z0), (xm, yy + (t / 2 if yy == y0 else -t / 2), (z0 + z1) / 2), frame_mat))
    objs.append(box(name + 'kb', (x1 - x0, y1 - y0 + 0.01, 0.35), ((x0 + x1) / 2, (y0 + y1) / 2, z0 + 0.3), frame_mat))      # lower panels
    yd = y1 if door_side > 0 else y0
    objs.append(box(name + 'dh', (0.18, 0.04, 0.03), (xm - 0.25, yd + 0.02 * door_side, (z0 + z1) / 2), 'steel_dark'))
    if wipers:
        objs.append(bar(name + 'wp', (x1 + 0.02, (y0 + y1) / 2 - 0.3, z0 + 0.6), (x1 + 0.02, (y0 + y1) / 2 + 0.1, z0 + 1.2), 0.02, 0.01, 'steel_dark'))
    objs.append(cyl(name + 'bc', 0.07, z1, z1 + 0.14, 'paint_orange', 16, center=(x0 + 0.2, y0 + 0.2, 0)))
    objs.append(cyl(name + 'ac', 0.18, z1, z1 + 0.18, frame_mat, 24, center=(xm, (y0 + y1) / 2, 0)))                         # HVAC / pressuriser
    return join(name, objs)


def headlight(name, pos, direction=(1, 0, 0), r=0.09):
    d = V(direction).normalized()
    return join(name, [placed(cyl(name + 'h', r * 1.25, -0.12, 0.0, 'steel_dark', 20), frame(pos, d)), placed(cyl(name + 'l', r, 0.0, 0.015, 'glass', 20), frame(pos, d))])


def mirror(name, base, arm_to, w=0.35, h=0.45):
    b, e = V(base), V(arm_to)
    return join(name, [rod(name + 'a', b, e, 0.025, 'steel_dark'), box(name + 'g', (0.05, w, h), (e.x, e.y, e.z), 'cab_glass')])


def hydraulic_cylinder(name, p0, p1, r_barrel, mat='mine_yellow', retracted_len=None, rod_mat='chrome', stages=1):
    """Hydraulic cylinder between the barrel pin p0 and the rod-eye pin p1 in the RETRACTED pose.
    Returns (barrel, [stage_1 .. stage_n]); the last stage carries the rod eye. Telescopic stages nest inside the
    barrel and each other; animate_cylinder() extends them in proportion."""
    a, b = V(p0), V(p1)
    d = b - a
    L = d.length
    Lb = retracted_len or (L - 0.25)
    Lb = min(Lb, L - 0.15)
    Mx = frame(a, d, (0, 0, 1) if abs(d.normalized().z) < 0.95 else (1, 0, 0))
    bar_ = [cyl(name + 'b', r_barrel, 0.08, Lb, mat, 28), cyl(name + 'bh', r_barrel * 1.1, Lb - 0.1, Lb, mat, 28),
            cyl(name + 'bc', r_barrel * 1.06, 0.06, 0.16, mat, 28),
            cyl(name + 'e0', r_barrel * 0.72, -0.06, 0.12, mat, 24),
            cyl(name + 'pp', r_barrel * 0.42, -r_barrel * 0.6, r_barrel * 0.6, 'steel', 16, axis='X')]
    b_o = join(name + 'B', bar_)
    transform(b_o, Mx)
    st = []
    for k in range(stages):
        rk = r_barrel * (0.86 - 0.62 * (k + 1) / (stages + 1)) if stages > 1 else r_barrel * 0.6
        top = Lb + 0.06 * (k + 1) if k < stages - 1 else L - 0.12
        objs = [cyl(f'{name}s{k}', rk, 0.25, top, rod_mat, 24)]
        if k < stages - 1:
            objs.append(cyl(f'{name}g{k}', rk * 1.06, top - 0.05, top, 'steel_dark', 24))      # stage gland
        else:
            objs.append(cyl(name + 'ey', r_barrel * 0.6, L - 0.14, L + 0.04, 'steel', 20))
            objs.append(cyl(name + 'ep', r_barrel * 0.4, -r_barrel * 0.55, r_barrel * 0.55, 'steel', 16, axis='X', center=(0, 0, L)))
        o = join(f'{name}S{k}', objs)
        transform(o, Mx)
        st.append(o)
    return b_o, st


def animate_cylinder(m, barrel_part, stage_parts, pin0_fn, pin1_fn, frames=None, plane_axis='Y'):
    """Keyframe a (telescopic) cylinder whose pins move: pin0_fn(t), pin1_fn(t) -> world points (t = 0..1 over the
    Operate clip). Every part (barrel and stages) must have its pivot at pin0 at t = 0. Motion in the XZ plane
    (rotation about Y) or the YZ plane (plane_axis='X'). Stage k slides out by (k+1)/n of the extension."""
    frames = frames or m.operate_frames
    a0, b0 = V(pin0_fn(0.0)), V(pin1_fn(0.0))
    d0 = b0 - a0
    L0 = d0.length
    n = len(stage_parts)

    def ang(d):
        return math.atan2(d.z, d.x) if plane_axis == 'Y' else math.atan2(d.z, d.y)
    th0 = ang(d0)
    kr, kb, ks = [], [], [[] for _ in range(n)]
    for f in range(frames + 1):
        t = f / frames
        a, b = V(pin0_fn(t)), V(pin1_fn(t))
        d = b - a
        phi = -(ang(d) - th0) if plane_axis == 'Y' else (ang(d) - th0)
        rot = (0.0, phi, 0.0) if plane_axis == 'Y' else (phi, 0.0, 0.0)
        kr.append((1 + f, rot))
        kb.append((1 + f, tuple(a - a0)))
        ext = d.length - L0
        for k in range(n):
            ks[k].append((1 + f, tuple(a - a0 + d.normalized() * ext * (k + 1) / n)))
    for mesh in barrel_part.meshes:
        m.keyframes(mesh, 'Operate', 'rotation_euler', kr)
        m.keyframes(mesh, 'Operate', 'location', kb)
    for k, sp in enumerate(stage_parts):
        for mesh in sp.meshes:
            m.keyframes(mesh, 'Operate', 'rotation_euler', kr)
            m.keyframes(mesh, 'Operate', 'location', ks[k])


def rotate_part_keys(m, part, angle_fn, axis='Y', frames=None, offset_fn=None):
    """Rotation (about the part pivot) and optional translation keyframes from angle_fn(t)."""
    frames = frames or m.operate_frames
    k = 'XYZ'.index(axis)
    kr, kl = [], []
    for f in range(frames + 1):
        t = f / frames
        r = [0.0, 0.0, 0.0]
        r[k] = angle_fn(t)
        kr.append((1 + f, tuple(r)))
        if offset_fn:
            kl.append((1 + f, tuple(offset_fn(t))))
    for mesh in part.meshes:
        m.keyframes(mesh, 'Operate', 'rotation_euler', kr)
        if offset_fn:
            m.keyframes(mesh, 'Operate', 'location', kl)
