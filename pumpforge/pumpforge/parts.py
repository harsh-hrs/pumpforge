"""
Reusable engineering assemblies (Blender Z-up, metres).
Convention for horizontal machines: shaft along +X (suction/pump end at -X,
driver at +X), cutaway plane y = 0 keeps the +Y half (section_role 'back').
"""
import math
from mathutils import Vector, Matrix
from .core import (lathe, lathe_split, ring_profile, cyl, box, csg, split, join, move, rotate, transform,
                   extrude_poly, hex_prism, bolt_circle, group_by, merge_halves, split_faces, TAU, M)
from .shapes import vane, sweep_tube


# ---------------------------------------------------------------- frames
def frame_matrix(origin, z_dir, y_dir):
    z = Vector(z_dir).normalized()
    y = Vector(y_dir).normalized()
    x = y.cross(z)
    o = Vector(origin)
    return Matrix(((x.x, y.x, z.x, o.x), (x.y, y.y, z.y, o.y), (x.z, y.z, z.z, o.z), (0, 0, 0, 1)))


def place(obj, Mx):
    if obj is not None:
        transform(obj, Mx)
    return obj


# horizontal end-suction frame: local z -> +X (shaft), local y -> +Z (up)
def H_FRAME(x0, cz):
    return frame_matrix((x0, 0, cz), (1, 0, 0), (0, 0, 1))


def V_FRAME(z0):
    """vertical, suction from below: local z -> +Z, local y -> +X."""
    return frame_matrix((0, 0, z0), (0, 0, 1), (1, 0, 0))


# ---------------------------------------------------------------- hydraulics
def _quarter(r0, z0, r1, z1, n=8, axial_first=True):
    """Quarter-ellipse meridional curve from (r0,z0) to (r1,z1)."""
    pts = []
    for i in range(n + 1):
        f = (math.pi / 2) * i / n
        if axial_first:
            pts.append((r0 + (r1 - r0) * (1 - math.cos(f)), z0 + (z1 - z0) * math.sin(f)))
        else:
            pts.append((r0 + (r1 - r0) * math.sin(f), z0 + (z1 - z0) * (1 - math.cos(f))))
    return pts


def _offset(curve, t, sign=1):
    out = []
    n = len(curve)
    for i in range(n):
        a = curve[max(0, i - 1)]
        b = curve[min(n - 1, i + 1)]
        dr, dz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dr, dz) or 1
        out.append((curve[i][0] + sign * t * dz / L, curve[i][1] - sign * t * dr / L))
    return out


def radial_impeller(name, d2, b2, r_eye, r_shaft, n_blades=6, mat='bronze', closed=True, wrap=1.8,
                    t=None, double_suction=False, expeller=False, segs=96):
    """Closed/open radial impeller in LOCAL frame: axis +z, eye at z=0 facing -z.
    Returns ((hub, blades), front_shroud_or_None, info); see add_impeller()."""
    r2 = d2 / 2
    t = t or max(0.0035, 0.03 * r2)
    zf = 0.55 * r_eye
    rc = min(0.55 * r_eye, 0.7 * (r2 - r_eye))
    r_hub = max(r_shaft * 1.45, 0.45 * r_eye)
    shroud = _quarter(r_eye, 0.0, r_eye + rc, zf) + [(r2, zf)]
    z_h0 = 0.2 * zf
    hub = _quarter(r_hub, z_h0, r_eye + rc, zf + b2) + [(r2, zf + b2)]
    if double_suction:
        hub = [(r_hub, zf + b2 / 2 - 0.0001), (r2, zf + b2 / 2 + 0.0001)]
    parts = []
    # back shroud / hub
    zb = zf + b2
    boss = 0.55 * r_eye
    if double_suction:
        # mirror: symmetric about z = zf + b2/2, eye on both sides; centre disc
        zm = zf + b2 / 2
        prof = [(r_shaft, zm - 0.6 * r_eye), (r_hub, zm - 0.6 * r_eye), (r_hub * 1.1, zm - t / 2 - 0.02 * r2),
                (r2, zm - t / 2), (r2, zm + t / 2), (r_hub * 1.1, zm + t / 2 + 0.02 * r2), (r_hub, zm + 0.6 * r_eye),
                (r_shaft, zm + 0.6 * r_eye)]
    else:
        prof = [(r_shaft, z_h0)] + hub + [(r2, zb + t), (r_hub * 1.25, zb + t + 0.15 * r_eye),
                                         (r_hub * 1.25, zb + t + boss), (r_shaft, zb + t + boss)]
    parts.append(lathe(name + '_hub', prof, mat, segs))
    if not double_suction:
        parts.append(lathe(name + '_nut', [(0, z_h0 - 0.55 * r_hub), (0.35 * r_hub, z_h0 - 0.5 * r_hub),
                                           (0.85 * r_hub, z_h0 - 0.1 * r_hub), (0.85 * r_hub, z_h0 + 0.002),
                                           (0, z_h0 + 0.002)], 'steel', 32))
    # blades
    def mk_blades(hub_c, shr_c, sgn=1, zmir=None):
        bl = []
        for i in range(n_blades):
            th0 = TAU * i / n_blades
            hc = hub_c if zmir is None else [(r, 2 * zmir - z) for r, z in hub_c]
            sc = shr_c if zmir is None else [(r, 2 * zmir - z) for r, z in shr_c]
            bl.append(vane(f'{name}_b{i}_{sgn}', hc, sc, lambda s, tt, th0=th0: th0 - wrap * (s ** 1.15),
                           max(0.003, 0.035 * r2), mat, ns=20, nt=5, t_ext=0.08))
        return bl
    bh = [p for p in hub]
    bs = [p for p in shroud]
    parts += mk_blades(bh, bs)
    if double_suction:
        parts += mk_blades(bh, bs, -1, zmir=zf + b2 / 2)
    if expeller:  # pump-out vanes on back shroud (slurry)
        for i in range(n_blades):
            b = box(f'{name}_ex{i}', (r2 * 0.55, 0.006, 0.012), (r2 * 0.68, 0, zb + t + 0.006), mat)
            parts.append(rotate(b, TAU * (i + 0.5) / n_blades))
    isb = [o.name.startswith(name + '_b') or o.name.startswith(name + '_ex') for o in parts]
    bl_list = [o for o, f in zip(parts, isb) if f]
    hub_list = [o for o, f in zip(parts, isb) if not f]
    hub_o = join(name + '_hubnut', hub_list)
    blades_o = join(name + '_blades', bl_list)
    core = (hub_o, blades_o)
    front = None
    if closed:
        neck = 0.35 * r_eye
        inner = [(r_eye, -neck)] + shroud
        outer = _offset(shroud, t, sign=1)
        poly = inner + [(r2, zf - t)] + list(reversed(outer[:-1])) + [(r_eye + t, -neck)]
        front = lathe(name + '_shroud', poly, mat, segs)
        if double_suction:
            fm = lathe(name + '_shroud2', [(r, 2 * (zf + b2 / 2) - z) for r, z in poly], mat, segs)
            front = join(name + '_shrouds', [front, fm])
    info = dict(r2=r2, zf=zf, b2=b2, zc=zf + b2 / 2, z_back=zb + t + boss, t=t, r_eye=r_eye,
                r_wear=r_eye + t, neck=0.35 * r_eye)
    return core, front, info


def volute_casing(name, imp, mat, r_suc, L_suc, r_dis, H_dis, t=None, r_back=None, z_back=None,
                  suction=True, flange=True, segs=96):
    """Single-volute casing in LOCAL frame (axis z, suction from -z).  Spiral grows with
    +theta (rotation direction); discharge leaves tangentially along local +y.
    Returns (casing_obj, geometry dict)."""
    r2, zf, b2 = imp['r2'], imp['zf'], imp['b2']
    t = t or max(0.008, 0.06 * r2)
    r3 = 1.06 * r2
    zc = zf + b2 / 2
    a_min, a_max = 0.25 * b2 + 0.004, max(0.75 * r_dis, 0.6 * b2)
    th0 = 0.45
    path, rad = [], []
    for i in range(41):
        th = th0 + (TAU - th0) * i / 40
        a = a_min + (a_max - a_min) * (th - th0) / (TAU - th0)
        R = r3 + 0.8 * a
        path.append((R * math.cos(th), R * math.sin(th), zc))
        rad.append(a)
    Rend = path[-1][0]
    n2 = 8
    for i in range(1, n2 + 1):
        y = H_dis * i / n2
        path.append((Rend, y, zc))
        f = min(1.0, i / (0.5 * n2))
        rad.append(a_max + (r_dis - a_max) * f)
    outer = sweep_tube(name + '_vo', path, [r + t for r in rad], mat, 32)
    ipath = path + [(Rend, H_dis + 0.02, zc)]
    inner = sweep_tube(name + '_vi', ipath, rad + [r_dis], mat, 32)
    r_w = imp['r_wear'] + 0.0015
    r_back = r_back or (r3 * 0.92)
    z_back = z_back if z_back is not None else zf + b2 + 2.5 * t
    r_bf = max(r3 + a_min + t, r_back + 2.2 * t)
    outs = [outer]
    body = [(r_suc + t, -L_suc if suction else -imp['neck'] - t), (r_suc + t, -0.45 * L_suc if suction else -imp['neck'] - t),
            (r_w + t, -imp['neck']), (r3 + a_min, zf - t), (r3 + a_min + 0.5 * t, zf + b2 + t),
            (r_bf, z_back - 1.2 * t), (r_bf, z_back), (0, z_back)]
    body = [(0, body[0][1])] + body
    outs.append(lathe(name + '_body', body, mat, segs))
    cav = [(0, -L_suc - 0.05), (r_suc, -L_suc - 0.05), (r_suc, -0.45 * L_suc), (r_w, -imp['neck'] - 0.002),
           (r_w, 0.0), (r3, zf - 0.006), (r3, zf + b2 + 0.006), (r_back, zf + b2 + 0.02),
           (r_back, z_back + 0.05), (0, z_back + 0.05)]
    if not suction:
        cav[0:3] = [(0, -imp['neck'] - 0.05), (r_w, -imp['neck'] - 0.05)]
    ins = [lathe(name + '_cav', cav, mat, segs), inner]
    tf = max(0.012, 0.25 * t + 0.008)
    if flange:
        outs.append(lathe(name + '_dfl', [(r_dis * 0.9, H_dis - tf), (r_dis + 2.2 * t + 0.02, H_dis - tf),
                                          (r_dis + 2.2 * t + 0.02, H_dis), (r_dis * 0.9, H_dis)], mat, 64,
                          axis='Y', center=(Rend, 0, zc)))
        if suction:
            outs.append(lathe(name + '_sfl', [(r_suc * 0.9, -L_suc), (r_suc + 2.2 * t + 0.02, -L_suc),
                                              (r_suc + 2.2 * t + 0.02, -L_suc + tf), (r_suc * 0.9, -L_suc + tf)],
                              mat, 64))
    cas = csg(name, outs, ins, mat)
    geo = dict(Rend=Rend, zc=zc, H_dis=H_dis, r3=r3, r_bf=r_bf, z_back=z_back, r_back=r_back, t=t,
               a_max=a_max, L_suc=L_suc, r_dis=r_dis, r_suc=r_suc, tf=tf,
               dflange_r=r_dis + 2.2 * t + 0.02, sflange_r=r_suc + 2.2 * t + 0.02)
    return cas, geo


# ---------------------------------------------------------------- bearings / seals
def ball_bearing(name, ri, ro, h0, h1, n, axis='X', center=(0, 0, 0)):
    """Deep-groove ball bearing as (back, front) halves around `axis`."""
    rm = (ri + ro) / 2
    w = h1 - h0
    rb = min(w, ro - ri) * 0.3
    pairs = [lathe_split(name + '_ir', [(ri, h0), (rm - rb * 0.55, h0), (rm - rb * 0.55, h1), (ri, h1)], 'steel', 48,
                         axis=axis, center=center),
             lathe_split(name + '_or', [(rm + rb * 0.55, h0), (ro, h0), (ro, h1), (rm + rb * 0.55, h1)], 'steel', 48,
                         axis=axis, center=center)]
    balls = []
    hm = (h0 + h1) / 2
    for i in range(n):
        a = (i + 0.5) * TAU / n
        prof = [(rb * math.sin(k * math.pi / 8), -rb * math.cos(k * math.pi / 8)) for k in range(9)]
        if axis == 'X':
            c = (center[0] + hm, center[1] + rm * math.sin(a), center[2] + rm * math.cos(a))
            bo = lathe(name + f'_b{i}', prof, 'chrome', 12, axis='X', center=c)
        else:
            c = (center[0] + rm * math.cos(a), center[1] + rm * math.sin(a), center[2] + hm)
            bo = lathe(name + f'_b{i}', prof, 'chrome', 12, axis='Z', center=c)
        balls.append(bo)
    pairs.append(group_by(balls, name + '_balls'))
    return merge_halves(name, pairs)


def seal_cartridge(name, h0, h1, r_shaft, r_out, axis='X', center=(0, 0, 0)):
    """Cartridge mechanical seal halves (sleeve, faces, spring, gland, collar)."""
    L = h1 - h0
    ri = r_shaft
    pr = [
        lathe_split(name + '_sl', [(ri, h0), (ri + 0.004, h0), (ri + 0.004, h1), (ri, h1)], 'stainless', 48, axis=axis, center=center),
        lathe_split(name + '_seat', [(ri + 0.006, h0 + 0.18 * L), (r_out * 0.78, h0 + 0.18 * L), (r_out * 0.78, h0 + 0.34 * L),
                                     (ri + 0.006, h0 + 0.34 * L)], 'silicon_carbide', 48, axis=axis, center=center),
        lathe_split(name + '_face', [(ri + 0.007, h0 + 0.34 * L), (r_out * 0.7, h0 + 0.34 * L), (r_out * 0.7, h0 + 0.46 * L),
                                     (ri + 0.007, h0 + 0.46 * L)], 'carbon', 48, axis=axis, center=center),
        lathe_split(name + '_spr', [(ri + 0.008, h0 + 0.46 * L), (r_out * 0.72, h0 + 0.46 * L), (r_out * 0.72, h0 + 0.62 * L),
                                    (ri + 0.008, h0 + 0.62 * L)], 'stainless', 48, axis=axis, center=center),
        lathe_split(name + '_gl', [(ri + 0.0045, h0 + 0.62 * L), (r_out, h0 + 0.62 * L), (r_out, h0 + 0.8 * L),
                                   (ri + 0.0045, h0 + 0.8 * L)], 'stainless', 48, axis=axis, center=center),
        lathe_split(name + '_col', [(ri + 0.004, h0 + 0.84 * L), (r_out * 0.6, h0 + 0.84 * L), (r_out * 0.6, h1),
                                    (ri + 0.004, h1)], 'stainless', 48, axis=axis, center=center),
    ]
    return merge_halves(name, pr)


# ---------------------------------------------------------------- drivers / transmission
def add_motor_h(m, prefix, x_de, cz, R, L, foot_z, shaft_r, shaft_len, explode_dx=0.5, revs=2,
                mat='paint_motor', label='Electric Motor', feet=True, flange_r=None):
    """Horizontal foot-mounted TEFC motor; drive end at x_de facing -X.  Returns dict."""
    x1 = x_de + L
    e = 0.09 * L
    feet_on = feet
    sh = [lathe_split(prefix + 'esd', [(shaft_r * 1.3, x_de), (R * 0.97, x_de), (R, x_de + e), (R * 0.9, x_de + e),
                                        (R * 0.9, x_de + 0.4 * e), (shaft_r * 2.4, x_de + 0.4 * e), (shaft_r * 2.4, x_de + 0.15 * e),
                                        (shaft_r * 1.3, x_de + 0.15 * e)], mat, 96, axis='X'),
          lathe_split(prefix + 'tube', [(R * 0.9, x_de + e), (R, x_de + e), (R, x1 - e), (R * 0.9, x1 - e)], mat, 96, axis='X'),
          lathe_split(prefix + 'esn', [(R * 0.9, x1 - e), (R, x1 - e), (R * 0.97, x1), (shaft_r * 1.3, x1),
                                        (shaft_r * 1.3, x1 - 0.15 * e), (shaft_r * 2.4, x1 - 0.15 * e), (shaft_r * 2.4, x1 - 0.4 * e),
                                        (R * 0.9, x1 - 0.4 * e)], mat, 96, axis='X')]
    for k in range(len(sh)):
        b, f = sh[k]
        transform(b, Matrix.Translation((0, 0, cz)))
        transform(f, Matrix.Translation((0, 0, cz)))
    fins = []
    nf = 28
    for i in range(nf):
        a = (i + 0.5) * TAU / nf
        if math.sin(a) < -0.7:
            continue  # leave the underside clear for the feet
        fb = box(f'{prefix}fin{i}', (L - 2.2 * e, 0.006 + 0.012 * R, 0.12 * R), (x_de + L / 2, 0, R + 0.05 * R), mat)
        fins.append(rotate(fb, a - math.pi / 2, 'X', (0, 0, 0)))
    for f_ in fins:
        transform(f_, Matrix.Translation((0, 0, cz)))
    fb_, ff_ = group_by(fins, prefix + 'fins')
    feet = []
    for xx in ((x_de + 0.22 * L, x1 - 0.22 * L) if feet_on else ()):
        feet.append(box(f'{prefix}ft', (0.2 * L, 1.55 * R, 0.035 + 0.05 * R), (xx, 0, foot_z + (0.035 + 0.05 * R) / 2), mat, bevel=0.004))
        feet.append(box(f'{prefix}fw', (0.14 * L, 0.5 * R, cz - foot_z - 0.6 * R), (xx, 0, foot_z + (cz - foot_z - 0.6 * R) / 2 + 0.02), mat))
    tb = [box(prefix + 'tb', (0.32 * L, 0.55 * R, 0.35 * R), (x_de + 0.45 * L, 0, cz + R + 0.16 * R), mat, bevel=0.006),
          box(prefix + 'tbl', (0.34 * L, 0.6 * R, 0.04 * R + 0.006), (x_de + 0.45 * L, 0, cz + 1.34 * R), mat, bevel=0.004),
          cyl(prefix + 'gl', 0.022 + 0.04 * R, 0, 0.06 * R + 0.02, 'brass', 6, axis='Y', center=(x_de + 0.45 * L, 0.275 * R, cz + 1.14 * R))]
    plate = box(prefix + 'np', (0.22 * L, 0.004, 0.32 * R), (x_de + 0.6 * L, -R * 0.995 - 0.002, cz + 0.1 * R), 'nameplate', bevel=0.002)
    if flange_r:
        feet.append(lathe(prefix + 'mfl', [(R * 0.8, x_de - 0.025), (flange_r, x_de - 0.025), (flange_r, x_de - 0.005),
                                            (R * 0.8, x_de + 0.01)], mat, 96, axis='X', center=(0, 0, cz)))
    hb, hf = split(join(prefix + 'feet_tb', feet + tb))
    fb2, ff2 = merge_halves(prefix + 'motor_frame', sh + [(fb_, ff_), (hb, hf), (None, plate)])
    p = m.part(prefix + 'motor_frame', f'{label} – Frame & End Shields', 'motor', section='split',
               explode=(explode_dx, 0, 0), info={'ref': 'motor_frame_h'})
    p.add_split(fb2, ff2, smooth_angle=40)
    # stator
    stb, stf = merge_halves(prefix + 'stator', [
        lathe_split(prefix + 'st', [(R * 0.58, x_de + 1.6 * e), (R * 0.9, x_de + 1.6 * e), (R * 0.9, x1 - 1.6 * e),
                                    (R * 0.58, x1 - 1.6 * e)], 'lamination', 96, axis='X', center=(0, 0, cz)),
        lathe_split(prefix + 'w1', [(R * 0.6, x_de + 1.0 * e), (R * 0.82, x_de + 1.0 * e), (R * 0.82, x_de + 1.6 * e),
                                    (R * 0.6, x_de + 1.6 * e)], 'copper', 64, axis='X', center=(0, 0, cz)),
        lathe_split(prefix + 'w2', [(R * 0.6, x1 - 1.6 * e), (R * 0.82, x1 - 1.6 * e), (R * 0.82, x1 - 1.0 * e),
                                    (R * 0.6, x1 - 1.0 * e)], 'copper', 64, axis='X', center=(0, 0, cz))])
    slots = []
    for i in range(24):
        a0 = TAU * (i + 0.5) / 24
        yy, zz = R * 0.59 * math.cos(a0), cz + R * 0.59 * math.sin(a0)
        slots.append(sweep_tube(f'{prefix}cu{i}', [(x_de + 1.2 * e, yy, zz), (x1 - 1.2 * e, yy, zz)], max(0.0025, R * 0.014), 'copper', 6))
    from .core import split_many as _sm
    sb2, sf2 = _sm(prefix + 'slots', slots)
    stb = join(prefix + 'stb', [o for o in (stb, sb2) if o is not None])
    stf = join(prefix + 'stf', [o for o in (stf, sf2) if o is not None])
    p = m.part(prefix + 'stator', f'{label} – Stator', 'motor', section='split', explode=(explode_dx, 0, 2.6 * R),
               info={'ref': 'stator'})
    p.add_split(stb, stf)
    # squirrel-cage rotor: laminated core, skewed aluminium bars and short-circuit end rings
    xr0, xr1 = x_de + 1.65 * e, x1 - 1.65 * e
    cage = [lathe(prefix + 'er1', [(R * 0.36, xr0 - 0.03 * L), (R * 0.565, xr0 - 0.03 * L), (R * 0.565, xr0 + 0.004), (R * 0.36, xr0 + 0.004)], 'aluminium', 64,
                  axis='X', center=(0, 0, cz)),
            lathe(prefix + 'er2', [(R * 0.36, xr1 - 0.004), (R * 0.565, xr1 - 0.004), (R * 0.565, xr1 + 0.03 * L), (R * 0.36, xr1 + 0.03 * L)], 'aluminium', 64,
                  axis='X', center=(0, 0, cz))]
    for i in range(22):
        a0 = TAU * i / 22
        pts = [(xr0 + (xr1 - xr0) * t / 5, R * 0.555 * math.cos(a0 + 0.22 * t / 5), cz + R * 0.555 * math.sin(a0 + 0.22 * t / 5)) for t in range(6)]
        cage.append(sweep_tube(f'{prefix}bar{i}', pts, max(0.0025, R * 0.022), 'aluminium', 6))
    rot = [cyl(prefix + 'rc', R * 0.545, xr0, xr1, 'lamination', 96, axis='X', center=(0, 0, cz))] + cage + [
           cyl(prefix + 'rs', shaft_r, x_de - shaft_len, x1 + 0.02, 'steel', 32, axis='X', center=(0, 0, cz), ch=0.002),
           box(prefix + 'key', (shaft_len * 0.7, shaft_r * 0.5, shaft_r * 0.5), (x_de - shaft_len * 0.55, 0, cz + shaft_r * 0.95), 'steel_dark')]
    p = m.part(prefix + 'rotor', f'{label} – Rotor & Shaft', 'motor', pivot=(x_de, 0, cz), explode=(explode_dx, -2.8 * R, 0),
               info={'ref': 'rotor'})
    p.add(join(prefix + 'rotor', rot)); p.spin('X', revs)
    bb = [ball_bearing(prefix + 'b1', shaft_r, shaft_r * 2.4, x_de + 0.15 * e, x_de + 0.4 * e + 0.004, 9, center=(0, 0, cz)),
          ball_bearing(prefix + 'b2', shaft_r, shaft_r * 2.4, x1 - 0.4 * e - 0.004, x1 - 0.15 * e, 9, center=(0, 0, cz))]
    p = m.part(prefix + 'motor_bearings', f'{label} – Bearings (DE & NDE)', 'bearings', section='split',
               explode=(explode_dx, -2.8 * R, 1.6 * R), info={'ref': 'motor_bearings'})
    p.add_split(*merge_halves(prefix + 'mb', bb))
    fan = [cyl(prefix + 'fh', shaft_r * 1.8, x1 + 0.01, x1 + 0.05 * L, 'polypropylene', 32, axis='X', center=(0, 0, cz))]
    for i in range(9):
        b = box(f'{prefix}fb{i}', (0.045 * L, 0.004, R * 0.72), (x1 + 0.03 * L, 0, cz + R * 0.45), 'polypropylene')
        fan.append(rotate(b, TAU * i / 9, 'X', (0, 0, cz)))
    p = m.part(prefix + 'motor_fan', f'{label} – Cooling Fan', 'motor', pivot=(x1, 0, cz), explode=(explode_dx + 0.5 * L, 0, 0),
               info={'ref': 'motor_fan'})
    p.add(join(prefix + 'fan', fan)); p.spin('X', revs)
    cb, cf = lathe_split(prefix + 'fcov', [(R * 0.97, x1 - 0.02), (R * 1.02, x1 - 0.02), (R * 1.02, x1 + 0.08 * L),
                                           (R * 0.9, x1 + 0.13 * L), (0, x1 + 0.135 * L), (0, x1 + 0.128 * L),
                                           (R * 0.88, x1 + 0.123 * L), (R * 0.995, x1 + 0.077 * L), (R * 0.995, x1 - 0.02)],
                         mat, 96, axis='X', center=(0, 0, cz))
    gr = [lathe_split(prefix + f'gr{k}', [(r0, x1 + 0.1355 * L), (r0 + 0.006, x1 + 0.1355 * L), (r0 + 0.006, x1 + 0.14 * L),
                                          (r0, x1 + 0.14 * L)], 'steel_dark', 64, axis='X', center=(0, 0, cz))
          for k, r0 in enumerate((R * 0.2, R * 0.4, R * 0.6))]
    p = m.part(prefix + 'fan_cover', f'{label} – Fan Cover', 'motor', section='split', explode=(explode_dx + 0.9 * L, 0, 0),
               info={'ref': 'fan_cover'})
    p.add_split(*merge_halves(prefix + 'fc', [(cb, cf)] + gr))
    return dict(x_shaft_end=x_de - shaft_len, x1=x1 + 0.14 * L)


def add_coupling(m, pid, x0, x1, cz, r, r_shaft, explode=(0, 0, 0), revs=2, guard=True, foot_z=None):
    xm = (x0 + x1) / 2
    g = 0.004
    hubs = [lathe(pid + 'h1', [(r_shaft, x0), (r * 0.62, x0), (r * 0.62, xm - 0.45 * (x1 - x0)), (r, xm - 0.4 * (x1 - x0)),
                               (r, xm - g), (r_shaft, xm - g)], 'steel', 64, axis='X', center=(0, 0, cz)),
            lathe(pid + 'h2', [(r_shaft, xm + g), (r, xm + g), (r, xm + 0.4 * (x1 - x0)), (r * 0.62, xm + 0.45 * (x1 - x0)),
                               (r * 0.62, x1), (r_shaft, x1)], 'steel', 64, axis='X', center=(0, 0, cz))]
    pins = [cyl(f'{pid}p{i}', r * 0.11, xm - g - 0.02 * r, xm + g + 0.02 * r, 'rubber', 16, axis='X',
                center=(0, r * 0.72 * math.sin(TAU * i / 8), cz + r * 0.72 * math.cos(TAU * i / 8)))
            for i in range(8)]
    pins += [bolt_circle(pid + 'nb', 8, r * 1.44, r * 0.18, xm - 0.4 * (x1 - x0), xm - 0.4 * (x1 - x0) - 0.012, axis='X',
                         center=(0, 0, cz), phase=0)]
    p = m.part(pid, 'Flexible Coupling', 'power_transmission', pivot=(xm, 0, cz), explode=explode,
               info={'ref': 'coupling_flex'})
    p.add(join(pid, hubs + pins)); p.spin('X', revs)
    if guard:
        gr = r * 1.45
        a = math.radians(110)
        gd = lathe(pid + 'guard', [(gr, x0 - 0.01), (gr + 0.003, x0 - 0.01), (gr + 0.003, x1 + 0.01), (gr, x1 + 0.01)],
                   'paint_yellow', 48, a0=-a, a1=a, axis='X', center=(0, 0, cz), cap_mat='paint_yellow')
        legs = []
        if foot_z is not None:
            for xx in (x0, x1):
                legs.append(box(pid + 'gl', (0.004, 2 * gr * math.sin(a) + 0.01, cz - foot_z - gr * 0.3),
                                (xx - 0.012 if xx == x0 else xx + 0.012, 0, foot_z + (cz - foot_z - gr * 0.3) / 2), 'paint_yellow'))
        p = m.part(pid + '_guard', 'Coupling Guard', 'power_transmission', section='hide', explode=(0, 0, 0.6 * r + 0.15),
                   info={'ref': 'coupling_guard'})
        p.add(join(pid + '_guard', [gd] + legs), smooth_angle=50)


def add_baseplate(m, x0, x1, w, h, pid='baseplate', z0=0.0):
    ch = []
    t = 0.008
    for sy in (-1, 1):
        y = sy * (w / 2 - 0.04)
        pts = [(-0.04, 0), (0.04, 0), (0.04, t), (-0.04 + t, t), (-0.04 + t, h - t), (0.04, h - t), (0.04, h), (-0.04, h)]
        if sy < 0:
            pts = [(-u, v) for u, v in pts]
        c = extrude_poly(f'{pid}c{sy}', [(u + y, v + z0) for u, v in pts], x0, x1, 'paint_grey', plane='YZ')
        ch.append(c)
    n = max(3, int((x1 - x0) / 0.5) + 1)
    for i in range(n):
        x = x0 + 0.03 + (x1 - x0 - 0.06) * i / (n - 1)
        ch.append(box(f'{pid}x{i}', (0.06, w - 0.16, h * 0.8), (x, 0, z0 + h * 0.45), 'paint_grey'))
    ch.append(box(pid + 'top', (x1 - x0, w - 0.02, 0.006), (x0 + (x1 - x0) / 2, 0, z0 + h - 0.003 + 0.0001), 'paint_grey'))
    for i, (sx, sy) in enumerate(((0, -1), (0, 1), (1, -1), (1, 1))):
        x = x0 + 0.07 if sx == 0 else x1 - 0.07
        ch.append(hex_prism(f'{pid}ab{i}', 0.03, z0 + h, z0 + h + 0.022, 'steel_dark', center=(x, sy * (w / 2 - 0.04), 0)))
    p = m.part(pid, 'Baseplate', 'baseplate', explode=(0, 0, -0.25), info={'ref': 'baseplate'})
    p.add(join(pid, ch), smooth_angle=30)
    return z0 + h


def add_bearing_frame(m, pid, x0, x1, cz, r_shaft, R, foot_z, mat='paint_blue', explode=(0, 0, 0)):
    """Overhung-pump bearing frame from x0 (casing side) to x1 (coupling side)."""
    L = x1 - x0
    outer = lathe(pid + 'o', [(0, x0), (R * 1.25, x0), (R * 1.25, x0 + 0.06 * L), (R * 0.75, x0 + 0.12 * L),
                              (R * 0.75, x0 + 0.24 * L), (R, x0 + 0.3 * L), (R, x1 - 0.05 * L), (R * 0.8, x1), (0, x1)],
                  mat, 96, axis='X', center=(0, 0, cz))
    sump = box(pid + 'sump', (0.6 * L, 1.4 * R, R * 0.7), (x0 + 0.62 * L, 0, cz - R * 0.75), mat, bevel=0.006)
    foot = box(pid + 'foot', (0.3 * L, 1.8 * R, cz - R - foot_z), (x0 + 0.62 * L, 0, foot_z + (cz - R - foot_z) / 2), mat, bevel=0.004)
    sg = cyl(pid + 'sg', 0.018 + 0.05 * R, 0, 0.012, 'chrome', 32, axis='Y', center=(x0 + 0.62 * L, -0.7 * R - 0.012, cz - 0.75 * R))
    inner = [lathe(pid + 'i', [(0, x0 - 0.01), (r_shaft * 1.15, x0 - 0.01), (r_shaft * 1.15, x0 + 0.3 * L), (R * 0.82, x0 + 0.33 * L),
                               (R * 0.82, x1 - 0.12 * L), (r_shaft * 1.15, x1 - 0.1 * L), (r_shaft * 1.15, x1 + 0.01), (0, x1 + 0.01)],
                   mat, 64, axis='X', center=(0, 0, cz)),
             box(pid + 'si', (0.5 * L, 1.2 * R, R * 0.55), (x0 + 0.62 * L, 0, cz - R * 0.72), mat)]
    fr = csg(pid, [outer, sump, foot], inner, mat)
    b, f = split(fr)
    p = m.part(pid, 'Bearing Frame', 'bearing_housing', section='split', explode=explode, info={'ref': 'bearing_frame'})
    p.add_split(b, join(pid + 'ff', [f, sg]), smooth_angle=40)
    rb = ball_bearing(pid + 'rb', r_shaft, r_shaft * 2.2, x0 + 0.3 * L, x0 + 0.3 * L + 0.24 * R, 10, center=(0, 0, cz))
    p = m.part(pid + '_radial_bearing', 'Radial Bearing (Inboard)', 'bearings', section='split',
               explode=(explode[0], explode[1] - 2.5 * R, explode[2]), info={'ref': 'radial_bearing'})
    p.add_split(*rb)
    tb = merge_halves(pid + 'tb', [
        ball_bearing(pid + 'tb1', r_shaft, r_shaft * 2.2, x1 - 0.12 * L - 0.44 * R, x1 - 0.12 * L - 0.22 * R, 10, center=(0, 0, cz)),
        ball_bearing(pid + 'tb2', r_shaft, r_shaft * 2.2, x1 - 0.12 * L - 0.22 * R, x1 - 0.12 * L, 10, center=(0, 0, cz))])
    p = m.part(pid + '_thrust_bearing', 'Thrust Bearings (Duplex Angular-Contact, Outboard)', 'bearings', section='split',
               explode=(explode[0] + 0.1, explode[1] - 2.5 * R, explode[2]), info={'ref': 'thrust_bearing'})
    p.add_split(*tb)


# ---------------------------------------------------------------- piping & instruments (for systems)
def flange_pair(name, r_pipe, h, axis='X', center=(0, 0, 0), mat='paint_grey'):
    rf = r_pipe * 1.9 + 0.03
    return lathe(name, [(r_pipe * 0.95, h - 0.012), (rf, h - 0.012), (rf, h + 0.012), (r_pipe * 0.95, h + 0.012)], mat, 48,
                 axis=axis, center=center)


def pipe(name, pts, r, mat='paint_grey', segs=24, bend=0.0):
    """Solid pipe run along polyline (rounded corners when bend > 0)."""
    P = [Vector(p) for p in pts]
    if bend > 0 and len(P) > 2:
        out = [P[0]]
        for i in range(1, len(P) - 1):
            a, b, c = P[i - 1], P[i], P[i + 1]
            d1, d2 = (b - a).normalized(), (c - b).normalized()
            rr = min(bend, (b - a).length / 2, (c - b).length / 2)
            p0, p1 = b - d1 * rr, b + d2 * rr
            for k in range(7):
                t = k / 6
                out.append((1 - t) ** 2 * p0 + 2 * (1 - t) * t * b + t * t * p1)
        out.append(P[-1])
        P = out
    return sweep_tube(name, [tuple(p) for p in P], r, mat, segs)


def gate_valve(name, center, r_pipe, axis='X', mat='paint_blue_dark'):
    cx, cy, cz = center
    L = r_pipe * 3.2
    objs = [cyl(name + 'b', r_pipe * 1.35, -L / 2, L / 2, mat, 48, axis=axis, center=center, ch=0.004),
            flange_pair(name + 'f1', r_pipe, -L / 2, axis, center, mat), flange_pair(name + 'f2', r_pipe, L / 2, axis, center, mat),
            box(name + 'bon', (r_pipe * 1.4, r_pipe * 1.4, r_pipe * 2.2), (cx, cy, cz + r_pipe * 1.6), mat, bevel=0.01),
            cyl(name + 'st', r_pipe * 0.12, cz + r_pipe * 2.6, cz + r_pipe * 4.1, 'stainless', 16, center=(cx, cy, 0)),
            lathe(name + 'hw', [(r_pipe * 1.0, cz + r_pipe * 3.6), (r_pipe * 1.15, cz + r_pipe * 3.6), (r_pipe * 1.15, cz + r_pipe * 3.75),
                                (r_pipe * 1.0, cz + r_pipe * 3.75)], 'paint_red', 48, center=(cx, cy, 0))]
    for i in range(3):
        b = box(f'{name}sp{i}', (r_pipe * 2.1, r_pipe * 0.1, r_pipe * 0.08), (cx, cy, cz + r_pipe * 3.68), 'paint_red')
        objs.append(rotate(b, TAU * i / 6, 'Z', (cx, cy, 0)))
    return join(name, objs)


def check_valve(name, center, r_pipe, axis='X', mat='paint_blue_dark'):
    cx, cy, cz = center
    L = r_pipe * 3.0
    objs = [cyl(name + 'b', r_pipe * 1.45, -L / 2, L / 2, mat, 48, axis=axis, center=center, ch=0.004),
            flange_pair(name + 'f1', r_pipe, -L / 2, axis, center, mat), flange_pair(name + 'f2', r_pipe, L / 2, axis, center, mat),
            box(name + 'cov', (r_pipe * 2.2, r_pipe * 1.8, r_pipe * 0.4), (cx, cy, cz + r_pipe * 1.45), mat, bevel=0.008)]
    return join(name, objs)


def pressure_gauge(name, base, r=0.04, facing=(0, -1, 0)):
    bx, by, bz = base
    objs = [cyl(name + 'st', 0.006, bz, bz + 0.06, 'brass', 12, center=(bx, by, 0)),
            hex_prism(name + 'hx', 0.022, bz + 0.01, bz + 0.03, 'brass', center=(bx, by, 0)),
            cyl(name + 'case', r, -0.015, 0.015, 'stainless', 40, axis='Y', center=(bx, by, bz + 0.06 + r)),
            cyl(name + 'dial', r * 0.9, -0.0155, -0.0145, 'ptfe', 40, axis='Y', center=(bx, by, bz + 0.06 + r))]
    nd = box(name + 'nd', (0.003, 0.002, r * 0.75), (bx, by - 0.0165, bz + 0.06 + r + r * 0.3), 'paint_red')
    objs.append(rotate(nd, -0.6, 'Y', (bx, by, bz + 0.06 + r)))
    return join(name, objs)


def nozzle_bolts(name, n, pcd, af, h0, h1, axis, center, phase=None):
    return bolt_circle(name, n, pcd, af, h0, h1, axis=axis, center=center, phase=phase,
                       stud=(af * 0.62, h0 - (0.004 if h1 > h0 else -0.004), h1 + (0.01 if h1 > h0 else -0.01)))


def volute_flow(imp, geo, Mx, suction_len=0.3, y_off=0.012):
    """Suction + discharge flow-path polylines (world) through an end-suction volute pump.
    Paths run just behind the y=0 section plane in local coordinates mapped by Mx."""
    zc = geo['zc']
    suc = [(0.0, 0.0, -geo['L_suc'] - suction_len), (0.0, 0.0, -geo['L_suc'] * 0.5), (0.0, 0.0, -0.01)]
    dis = []
    r2 = imp['r2']
    for i in range(6):
        f = i / 5
        r = imp['r_eye'] * 0.6 + (r2 - imp['r_eye'] * 0.6) * f
        z = 0.0 + (zc - 0.0) * min(1, f * 1.6)
        dis.append((0.0, r, z))
    th0 = math.pi / 2
    for i in range(1, 25):
        th = th0 + (TAU - th0) * i / 24
        a = geo['a_max'] * (0.4 + 0.6 * i / 24)
        R = geo['r3'] + 0.8 * a
        dis.append((R * math.cos(th), R * math.sin(th), zc))
    for y in (0.3, 0.6, 1.0, 1.25):
        dis.append((geo['Rend'], geo['H_dis'] * y, zc))
    W = lambda pts: [tuple(Mx @ Vector(p)) for p in pts]
    return W(suc + [dis[0]]), W(dis)


def add_impeller(m, pid, name, core, shroud, Mx, pivot, axis='X', explode=(0, 0, 0), revs=2, ref='impeller_closed',
                 split_axis='y', split_at=0.0):
    """Place an impeller (from radial_impeller) and register it: hub and shroud are sectioned
    for the cutaway, blades stay whole; everything spins."""
    from .core import split_many
    hub, blades = core
    for o in (hub, blades, shroud):
        place(o, Mx)
    p = m.part(pid, name, 'rotating_element', pivot=pivot, explode=explode, info={'ref': ref})
    p.add(blades, 'keep').name = pid + '_blades'
    hb, hf = split_many(pid + '_hub', [hub], split_axis, split_at)
    p.add(hb, 'back').name = pid + '_hub__back'
    p.add(hf, 'front').name = pid + '_hub__front'
    if shroud is not None:
        sb, sf = split_many(pid + '_shroud', [shroud], split_axis, split_at)
        p.add(sb, 'back').name = pid + '_shroud__back'
        p.add(sf, 'front').name = pid + '_shroud__front'
    p.spin(axis, revs)
    return p


def add_oh_drive(m, x0, cz, bp_top, r_shaft, x_imp, frame_R=0.075, frame_L=0.36, motor_R=0.13, motor_L=0.42,
                 seal_len=0.06, frame_mat='paint_blue', explode0=0.25, cover_r=None, seal=True):
    """Overhung-pump drive train behind a casing back face at x0: casing cover with seal chamber,
    cartridge seal, bearing frame, shaft, coupling, motor.  Returns dict(x_end, x_motor_end)."""
    from .core import split
    cr = cover_r or frame_R * 1.6
    cov = lathe('casing_cover', [(r_shaft + 0.004, x0), (cr, x0), (cr, x0 + 0.018), (r_shaft * 2.4 + 0.012, x0 + 0.025),
                                 (r_shaft * 2.4 + 0.012, x0 + seal_len), (r_shaft * 2.4, x0 + seal_len),
                                 (r_shaft * 2.4, x0 + 0.02), (r_shaft + 0.004, x0 + 0.016)],
                frame_mat, 96, axis='X', center=(0, 0, cz))
    p = m.part('casing_cover', 'Casing Cover & Seal Chamber', 'casing', section='split', explode=(explode0 * 0.4, 0, 0),
               info={'ref': 'casing_cover'})
    p.add_split(*split(cov), smooth_angle=40)
    if seal:
        sb, sf = seal_cartridge('seal', x0 + 0.02, x0 + seal_len + 0.02, r_shaft, r_shaft * 2.3, center=(0, 0, cz))
        p = m.part('mechanical_seal', 'Cartridge Mechanical Seal', 'mechanical_seal', section='split',
                   explode=(explode0 * 0.7, -0.25, 0), info={'ref': 'mechanical_seal'})
        p.add_split(sb, sf)
    xf0 = x0 + seal_len + 0.025
    xf1 = xf0 + frame_L
    add_bearing_frame(m, 'bearing_frame', xf0, xf1, cz, r_shaft, frame_R, bp_top, mat=frame_mat, explode=(explode0, 0, 0))
    sh = cyl('pump_shaft', r_shaft, x_imp, xf1 + 0.07, 'steel', 32, axis='X', center=(0, 0, cz), ch=0.002)
    key = box('pkey', (0.05, r_shaft * 0.5, r_shaft * 0.5), (xf1 + 0.04, 0, cz + r_shaft * 0.95), 'steel_dark')
    p = m.part('pump_shaft', 'Pump Shaft', 'rotating_element', pivot=(x0, 0, cz), explode=(explode0, -0.5, 0),
               info={'ref': 'pump_shaft'})
    p.add(join('pump_shaft', [sh, key])); p.spin('X', 2)
    xc = xf1 + 0.075
    add_coupling(m, 'coupling', xc, xc + 0.09, cz, max(0.045, r_shaft * 2.2), r_shaft, explode=(explode0 + 0.3, 0, 0),
                 foot_z=bp_top)
    mo = add_motor_h(m, 'm_', xc + 0.11, cz, motor_R, motor_L, bp_top, r_shaft * 1.1, 0.11, explode_dx=explode0 + 0.55)
    return dict(x_end=mo['x1'], xf1=xf1)


def transform_parts(m, parts, Mx):
    """Rigidly move already-created parts (nodes, meshes, explode vectors, spin axes) by Mx
    (rotation about the origin + translation)."""
    from .core import bl2gl
    R3 = Mx.to_3x3()
    Rl = R3.to_4x4()
    for p in parts:
        p.pivot = Mx @ p.pivot
        p.node.location = p.pivot
        p.explode = R3 @ p.explode
        p.node['explode_offset'] = bl2gl(p.explode)
        for mesh in p.meshes:
            mesh.data.transform(Rl)
            mesh.data.update()
            for (idd, clip), chans in m._anims.items():
                if idd is mesh:
                    new = []
                    for path, keys in chans:
                        if path in ('rotation_euler', 'location'):
                            keys = [(f, tuple(R3 @ Vector(v))) for f, v in keys]
                        new.append((path, keys))
                    m._anims[(idd, clip)] = new


def add_motor_v(m, prefix, z_de, R, L, shaft_r, shaft_len, explode_dz=0.5, revs=2, flange_r=None, label='Vertical Motor',
                mat='paint_motor'):
    """Flange-mounted vertical motor above z_de (drive end facing down)."""
    n0 = len(m.parts)
    add_motor_h(m, prefix, 0.0, 0.0, R, L, -R, shaft_r, shaft_len, explode_dx=explode_dz, revs=revs, feet=False,
                flange_r=flange_r, label=label, mat=mat)
    Mx = Matrix.Translation((0, 0, z_de)) @ Matrix.Rotation(-math.pi / 2, 4, 'Y')
    transform_parts(m, m.parts[n0:], Mx)
    return dict(z_top=z_de + L * 1.14)


def add_drive_y(m, y0, cz, bp_top, shaft_r, motor_R=0.12, motor_L=0.38, y_base0=-0.4, revs=1.0, base_w=0.42,
                coupling_len=0.09, explode0=0.3, x_off=0.0, base=True):
    """Coupling + foot motor + baseplate laid out along +Y starting at y0 (pump shaft end).
    Built along X then rotated 90 deg about Z (so their cutaway keeps the -X half)."""
    n0 = len(m.parts)
    add_coupling(m, 'coupling', y0, y0 + coupling_len, cz, max(0.045, shaft_r * 2.3), shaft_r, explode=(explode0, 0, 0),
                 revs=revs, foot_z=bp_top)
    mo = add_motor_h(m, 'm_', y0 + coupling_len + 0.02, cz, motor_R, motor_L, bp_top, shaft_r, 0.11, explode_dx=explode0 + 0.3,
                     revs=revs)
    if base:
        add_baseplate(m, y_base0, mo['x1'] + 0.04, base_w, bp_top)
    transform_parts(m, m.parts[n0:], Matrix.Translation((x_off, 0, 0)) @ Matrix.Rotation(math.pi / 2, 4, 'Z'))
    return mo


def add_tracers(m, pid, name, path, n=10, radius=0.006, mat='flow_discharge', loops=1, group='flow_tracers', ref='flow_tracers',
                explode=(0, 0, 0)):
    """Small spheres that travel along a polyline in the Operate loop (visualises flow where nothing moves)."""
    from .core import OPERATE_FRAMES
    P = [Vector(p) for p in path]
    seg = [(P[i + 1] - P[i]).length for i in range(len(P) - 1)]
    total = sum(seg)

    def at(s):
        s = s % total
        for i, L in enumerate(seg):
            if s <= L or i == len(seg) - 1:
                return P[i] + (P[i + 1] - P[i]) * (s / L if L > 0 else 0)
            s -= L
    p = m.part(pid, name, group, explode=explode, info={'ref': ref})
    for k in range(n):
        s0 = total * k / n
        start = at(s0)
        prof = [(radius * math.sin(t * math.pi / 8), -radius * math.cos(t * math.pi / 8)) for t in range(9)]
        sph = lathe(f'{pid}_{k}', prof, mat, 12, center=tuple(start))
        mesh = p.add(sph, 'keep', smooth_angle=80)
        keys = []
        for f in range(OPERATE_FRAMES + 1):
            q = at(s0 + total * loops * f / OPERATE_FRAMES) - start
            keys.append((1 + f, tuple(q)))
        m.keyframes(mesh, 'Operate', 'location', keys)
    return p


def hollow_pipe(name, pts, r, mat='paint_grey', segs=32, bend=0.0, t=None):
    """Pipe with a real bore (so it sections properly in cutaway)."""
    from .core import csg
    t = t or max(0.004, 0.12 * r)
    P = [Vector(p) for p in pts]
    d0 = (P[1] - P[0]).normalized()
    d1 = (P[-1] - P[-2]).normalized()
    ext = [tuple(P[0] - d0 * 0.01)] + [tuple(p) for p in P[1:-1]] + [tuple(P[-1] + d1 * 0.01)]
    return csg(name, [pipe(name + '_o', pts, r, mat, segs, bend=bend)], [pipe(name + '_i', ext, r - t, mat, segs, bend=bend)], mat)
