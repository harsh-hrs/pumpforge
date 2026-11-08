"""Process-plant building blocks: thickeners, agitated tanks, rotating drums, hydrocyclones, silos, settling particles.
Cut plane y = 0 keeps +y."""
import math
from mathutils import Matrix, Vector
from .core import lathe, cyl, box, csg, join, rotate, TAU, OPERATE_FRAMES
from .valvekit import P, keys_loop, smooth_pulse
from .vesselkit import vessel, nozzle, legs, half, animate_level, liquid_v
from .parts import hollow_pipe
from .shapes import sweep_tube


def ball(name, r, mat, center=(0, 0, 0)):
    return lathe(name, [(r * math.sin(k * math.pi / 6), -r * math.cos(k * math.pi / 6)) for k in range(7)], mat, 10, center=center)


def particles_path(m, pid, name, fn, n, mat='sand', r=0.015, ref='flow_tracers', scale_fn=None):
    """n particles whose position is fn(i, s) with s = phase 0..1 (looping); optional scale_fn(i, s)."""
    p = m.part(pid, name, 'flow_tracers', explode=(0, 0, 0), info={'ref': ref})
    for i in range(n):
        ph = (i / n + 0.13 * (i % 3)) % 1.0
        ms = p.add(ball(f'{pid}{i}', r, mat), smooth_angle=80)
        lk, sk = [], []
        for f in range(OPERATE_FRAMES + 1):
            s = ((f / OPERATE_FRAMES) + ph) % 1.0
            lk.append((1 + f, tuple(fn(i, s))))
            if scale_fn:
                v = scale_fn(i, s)
                sk.append((1 + f, (v, v, v)))
        ms.location = lk[0][1]
        m.keyframes(ms, 'Operate', 'location', lk)
        if sk:
            m.keyframes(ms, 'Operate', 'scale', sk)
    return p


def thickener(m, prefix, R, H, cone_h, cx=0.0, label='Thickener', ref='th', mat='paint_grey', liquid='water', mud='ore', rake_revs=0.25, bridge=True, level=None):
    """Circular thickener / clarifier: tank with conical floor, central feedwell, rotating rake arms,
    peripheral overflow launder, underflow cone. Returns z of tank bottom apex."""
    z0 = cone_h + 0.15                                             # floor edge height (tank wall base)
    tank = csg(prefix + 'tk', [lathe(prefix + 'tko', [(0.0, 0.1), (0.25, 0.1), (R + 0.03, z0), (R + 0.03, z0 + H), (0.0, z0 + H)], mat, 96, center=(cx, 0, 0))],
               [lathe(prefix + 'tki', [(0.0, 0.13), (0.22, 0.13), (R, z0 + 0.03), (R, z0 + H + 0.1), (0.0, z0 + H + 0.1)], mat, 96, center=(cx, 0, 0))], mat)
    ld = csg(prefix + 'ld', [cyl(prefix + 'ldo', R + 0.18, z0 + H - 0.15, z0 + H, mat, 96, center=(cx, 0, 0))], [cyl(prefix + 'ldi', R + 0.03, z0 + H - 0.2, z0 + H + 0.05, mat, 96, center=(cx, 0, 0)),
                                                                                                          cyl(prefix + 'ldc', R + 0.15, z0 + H - 0.12, z0 + H + 0.05, mat, 96, center=(cx, 0, 0))], mat)
    P(m, prefix + 'tank', f'{label}: Tank with Conical Floor & Overflow Launder', 'tank', [tank, ld], explode=(0, 0.7, 0), ref=ref + '_tank')
    lv = level or (z0 + H - 0.16)
    clear = lathe(prefix + 'cl', [(0.0, z0 + H * 0.45), (R - 0.005, z0 + H * 0.45), (R - 0.005, lv), (0.0, lv)], liquid, 64, a0=0.0, a1=math.pi, center=(cx, 0, 0), cap_mat=liquid)
    mudb = lathe(prefix + 'md', [(0.0, 0.14), (0.22, 0.14), (R - 0.005, z0 + 0.03), (R - 0.005, z0 + H * 0.45), (0.0, z0 + H * 0.45)], mud, 64, a0=0.0, a1=math.pi, center=(cx, 0, 0), cap_mat=mud)
    P(m, prefix + 'clear', f'{label}: Clear Overflow Zone', 'fluid', clear, explode=(0, -0.4, 0.2), ref=ref + '_zones', section='keep')
    pm = P(m, prefix + 'mud', f'{label}: Settling / Compression Zone (mud bed)', 'fluid', mudb, explode=(0, -0.4, -0.1), ref=ref + '_zones', section='keep', pivot=(cx, 0, 0.14))
    keys_loop(m, pm, lambda t: (1, 1, 1 + 0.05 * math.sin(TAU * t)), 'scale')
    fw = csg(prefix + 'fw', [cyl(prefix + 'fwo', R * 0.22, z0 + H * 0.45, z0 + H + 0.05, 'steel', 48, center=(cx, 0, 0))], [cyl(prefix + 'fwi', R * 0.22 - 0.015, z0 + H * 0.4, z0 + H + 0.1, 'steel', 48, center=(cx, 0, 0))], 'steel')
    P(m, prefix + 'feedwell', f'{label}: Central Feedwell (dissipates feed energy, mixes flocculant)', 'internals', fw, explode=(0, -0.3, 0.6), ref=ref + '_feedwell', section='split')
    rk = [cyl(prefix + 'sh', 0.05, 0.25, z0 + H + 0.35, 'steel', 24, center=(cx, 0, 0))]
    for s in (-1, 1):
        a0 = Vector((cx + s * 0.2, 0, 0.25 + 0.05))
        a1 = Vector((cx + s * (R - 0.05), 0, z0 + 0.1))
        d = a1 - a0
        arm = box(prefix + f'ar{s}', (d.length, 0.06, 0.06), (0, 0, 0), 'steel')
        arm.data.transform(Matrix.Translation((a0 + a1) / 2) @ Matrix.Rotation(-math.atan2(d.z, d.x), 4, 'Y'))
        rk.append(arm)
        for k in range(6):
            u = (k + 0.5) / 6
            pnt = a0 + d * u
            bl = box(prefix + f'bl{s}{k}', (0.12, 0.01, 0.07), (pnt.x, 0.0, pnt.z - 0.05), 'steel')
            rk.append(rotate(bl, 0.6 * s, 'Z', (pnt.x, 0, pnt.z)))
    prk = P(m, prefix + 'rakes', f'{label}: Rake Arms & Blades (move mud to the centre cone)', 'rotating_element', rk, explode=(0, -0.8, 0.3), ref=ref + '_rake', section='keep', pivot=(cx, 0, 0))
    prk.spin('Z', rake_revs)
    if bridge:
        br = [box(prefix + 'br', (2 * R + 0.5, 0.35, 0.12), (cx, 0, z0 + H + 0.25), 'paint_yellow'), box(prefix + 'dh', (0.5, 0.5, 0.35), (cx, 0, z0 + H + 0.48), 'paint_blue'),
              cyl(prefix + 'mt', 0.1, z0 + H + 0.65, z0 + H + 0.95, 'paint_motor', 24, center=(cx + 0.15, 0, 0))]
        P(m, prefix + 'drive', f'{label}: Bridge & Rake Drive (slow, high torque, overload protection)', 'drive', br, explode=(0, 0, 0.7), ref=ref + '_drive', section='keep')
    return z0


def agitated_tank(m, prefix, R, Z0, H, label, ref, cx=0.0, mat='paint_grey', liquid='ore', level=None, imp='pbt', revs=1.5, open_top=True, baffles=True, draft_tube=False, legs_=True):
    """Vertical agitated tank with flat/cone bottom, baffles, top-entry agitator (motor, gearbox, shaft, impellers)."""
    if open_top:
        sh = csg(prefix + 'sh', [cyl(prefix + 'so', R + 0.015, Z0, Z0 + H, mat, 96, center=(cx, 0, 0))], [cyl(prefix + 'si', R, Z0 + 0.03, Z0 + H + 0.1, mat, 96, center=(cx, 0, 0))], mat)
    else:
        sh = vessel(prefix + 'sh', R, H, 0.012, mat, heads=('flat', '2:1'), z0=Z0, center=(cx, 0, 0))
    objs = [sh]
    if baffles:
        objs += [rotate(box(prefix + f'bf{k}', (R * 0.1, 0.02, H * 0.85), (cx + R * 0.92, 0, Z0 + H * 0.47), 'steel'), TAU * k / 4 + math.pi / 4, 'Z', (cx, 0, 0)) for k in range(4)]
    if draft_tube:
        objs.append(cyl(prefix + 'dt', R * 0.38, Z0 + 0.25 * H, Z0 + 0.85 * H, 'steel', 64, center=(cx, 0, 0), r_in=R * 0.36))
    P(m, prefix + 'tank', f'{label}: Tank, Baffles' + (' & Draft Tube' if draft_tube else ''), 'tank', objs, explode=(0, 0.7, 0), ref=ref + '_tank')
    lv = level or (Z0 + H * 0.85)
    pl = P(m, prefix + 'slurry', f'{label}: Slurry / Liquor', 'fluid', lathe(prefix + 'lq', [(0.0, Z0 + 0.03), (R - 0.005, Z0 + 0.03), (R - 0.005, lv), (0.0, lv)], liquid, 64, a0=0.0, a1=math.pi, center=(cx, 0, 0), cap_mat=liquid),
           explode=(0, -0.4, 0), ref=ref + '_slurry', section='keep')
    animate_level(m, pl, lv - 0.01, 0.02, lambda t: 0.5 + 0.5 * math.sin(TAU * t))
    zt = Z0 + H + (0.02 if open_top else R * 0.5)
    zi = [Z0 + 0.3 * H] if not draft_tube else [Z0 + 0.55 * H]
    if H > 2.5 * R and not draft_tube:
        zi.append(Z0 + 0.65 * H)
    Ri = R * (0.33 if draft_tube else 0.45)
    parts = [cyl(prefix + 'ash', 0.04, min(zi) - 0.05, zt + 0.25, 'steel', 24, center=(cx, 0, 0))]
    for k, z in enumerate(zi):
        parts.append(cyl(f'{prefix}hb{k}', 0.07, z - 0.05, z + 0.05, 'steel', 32, center=(cx, 0, 0)))
        for i in range(4 if imp == 'pbt' else 3):
            if imp == 'pbt':
                b = box(f'{prefix}b{k}{i}', (Ri - 0.06, 0.012, Ri * 0.3), (cx + (Ri + 0.06) / 2, 0, z), 'steel')
                b = rotate(b, math.radians(45), 'X', (cx, 0, z))
            else:                                                     # hydrofoil (narrow, twisted)
                b = box(f'{prefix}b{k}{i}', (Ri - 0.06, 0.01, Ri * 0.22), (cx + (Ri + 0.06) / 2, 0, z), 'steel')
                b = rotate(b, math.radians(25), 'X', (cx, 0, z))
            parts.append(rotate(b, TAU * i / (4 if imp == 'pbt' else 3), 'Z', (cx, 0, 0)))
    pa = P(m, prefix + 'agitator', f'{label}: Agitator Shaft & Impeller' + ('s' if len(zi) > 1 else ''), 'rotating_element', parts, explode=(0, -0.2, 1.0), ref=ref + '_agitator', section='keep', pivot=(cx, 0, 0))
    pa.spin('Z', revs)
    drv = [box(prefix + 'bm', (2 * R + 0.3, 0.25, 0.1), (cx, 0, zt + 0.05), 'paint_grey') if open_top else cyl(prefix + 'np', 0.2, zt - 0.05, zt + 0.05, 'steel', 32, center=(cx, 0, 0)),
           cyl(prefix + 'gb', 0.16, zt + 0.1, zt + 0.35, 'paint_blue', 48, center=(cx, 0, 0)), cyl(prefix + 'mt', 0.13, zt + 0.35, zt + 0.75, 'paint_motor', 48, center=(cx, 0, 0), ch=0.01)]
    P(m, prefix + 'drive', f'{label}: Agitator Drive (motor + gearbox' + (', bridge beam)' if open_top else ', mounting nozzle)'), 'drive', drv, explode=(0, 0, 1.2), ref=ref + '_drive', section='keep')
    return zt


def hydrocyclone(name, x, y, z_top, D=0.25, L_cyl=0.3, L_cone=0.9, mat='rubber', shell='paint_grey'):
    """Hydrocyclone (axis Z): inlet head with tangential inlet, cylinder, cone, apex spigot, vortex finder & overflow pipe.
    Returns list of objects and dict of key points."""
    R = D / 2
    zc = z_top - L_cyl
    za = zc - L_cone
    body = csg(name, [lathe(name + 'o', [(0.0, za - 0.05), (R * 0.25 + 0.02, za - 0.05), (R + 0.02, zc), (R + 0.02, z_top), (0.0, z_top)], shell, 48, center=(x, y, 0))],
               [lathe(name + 'i', [(0.0, za - 0.1), (R * 0.25, za - 0.1), (R * 0.25, za - 0.05), (R, zc), (R, z_top - 0.02), (0.0, z_top - 0.02)], shell, 48, center=(x, y, 0))], shell)
    vf = cyl(name + 'vf', R * 0.35, z_top - L_cyl * 0.8, z_top + 0.25, 'steel', 32, center=(x, y, 0), r_in=R * 0.3)
    inl = box(name + 'in', (R * 1.2, R * 0.6, R * 0.6), (x - R * 0.6, y + R * 0.7, z_top - R * 0.4), shell)
    return [body, vf, inl], {'R': R, 'za': za, 'zc': zc}


def drum(name, R, x0, x1, cz, mat='paint_grey', r_in=None, ends=True, axis_y=0.0):
    """Horizontal cylindrical drum along X (shell with optional end rings)."""
    objs = [cyl(name, R, x0, x1, mat, 96, axis='X', center=(0, axis_y, cz), r_in=r_in or R - 0.03)]
    if ends:
        objs += [cyl(name + f'e{k}', R, x, x + 0.04, mat, 96, axis='X', center=(0, axis_y, cz), r_in=R * 0.35) for k, x in enumerate((x0, x1 - 0.04))]
    return objs


def silo(name, R, z_cone, H, mat='paint_grey', cx=0.0, cy=0.0, cone='cone'):
    """Vertical silo: cylinder on conical (or flat) bottom with roof."""
    return vessel(name, R, H, 0.012, mat, heads=(cone, 'flat'), z0=z_cone, center=(cx, cy, 0))
