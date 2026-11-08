"""Building blocks for rotating machinery (compressors, fans, turbines, engines, drives).
Conventions follow valvekit: cut plane y = 0 keeps +y unless a builder says otherwise."""
import math
from mathutils import Matrix
from .core import (lathe, cyl, box, csg, join, rotate, extrude_poly, hex_prism, TAU, OPERATE_FRAMES)
from .shapes import twisted_extrude, involute_gear_profile, sweep_tube


# ------------------------------------------------------------------ blades
def _foil(chord, thick, n=6):
    """Closed symmetric aerofoil-like lens (u along chord, v thickness)."""
    up = [(-chord / 2 + chord * i / n, thick / 2 * math.sin(math.pi * i / n) ** 0.7) for i in range(n + 1)]
    lo = [(u, -v) for u, v in up[-2:0:-1]]
    return up + lo


def blade_row(name, x, r_hub, r_tip, n, mat, chord=0.03, thick=0.004, stagger=0.6, twist=0.5, cz=0.0, phase=0.0, steps=4):
    """n twisted blades about the X axis, leading edge toward -x.  stagger/twist in rad."""
    pts = _foil(chord, thick)
    c, s = math.cos(stagger), math.sin(stagger)
    pts = [(u * c - v * s, u * s + v * c) for u, v in pts]
    L = r_tip - r_hub
    lead = TAU * L / twist if abs(twist) > 1e-6 else 1e6
    objs = []
    for i in range(n):
        b = twisted_extrude(f'{name}{i}', pts, r_hub - 0.001, r_tip, lead, mat, steps=steps, axis='Z', center=(x, 0, cz))
        objs.append(rotate(b, phase + TAU * i / n, 'X', (0, 0, cz)))
    return join(name, objs)


def radial_blades(name, y0, y1, r0, r1, n, mat, curve=0.6, t=0.004, cx=0.0, cz=0.0, phase=0.0, k=8):
    """Curved plate blades between radii r0..r1, extruded along Y (axis Y).  curve>0 = backward for clockwise rotation."""
    objs = []
    for i in range(n):
        a0 = phase + TAU * i / n
        side1, side2 = [], []
        for j in range(k + 1):
            f = j / k
            r = r0 + (r1 - r0) * f
            a = a0 + curve * f
            da = t / r
            side1.append((cx + r * math.cos(a), cz + r * math.sin(a)))
            side2.append((cx + r * math.cos(a + da), cz + r * math.sin(a + da)))
        objs.append(extrude_poly(f'{name}{i}', side1 + side2[::-1], y0, y1, mat, plane='XZ'))
    return join(name, objs)


def scroll_polys(cx, cz, r0, r1, xout, t, n=72):
    """Spiral volute outline (clockwise growth, outlet at top toward +x) — returns (outer, inner, duct_outer, duct_inner)."""
    def spiral(off):
        pts = []
        for i in range(n + 1):
            th = TAU * i / n
            r = r0 + (r1 - r0) * th / TAU + off
            a = math.pi / 2 - th
            pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
        return pts
    return spiral(t), spiral(0.0), (cx, xout, cz + r0 - t, cz + r1 + t), (cx - 0.01, xout + 0.2, cz + r0, cz + r1)


# ------------------------------------------------------------------ gears
def helical_gear(name, mod, z, y0, y1, mat, cx=0.0, cz=0.0, helix_deg=15.0, hand=1, phase=0.0, bore=0.0, steps=None):
    """Helical (or spur, helix 0) gear about the Y axis.  Returns (obj, rp)."""
    pts, g = involute_gear_profile(mod, z, 20.0, steps=5, backlash=mod * 0.04, root_steps=3)
    c, s = math.cos(phase), math.sin(phase)
    pts = [(u * c - v * s, u * s + v * c) for u, v in pts]
    if helix_deg:
        lead = math.pi * mod * z / math.tan(math.radians(helix_deg))
        o = twisted_extrude(name, pts, y0, y1, lead, mat, steps=steps or 6, axis='Y', center=(cx, 0, cz), hand=hand)
    else:
        o = extrude_poly(name, [(cx + u, cz + v) for u, v in pts], y0, y1, mat, plane='XZ')
    if bore:
        o = csg(name, [o], [cyl(name + 'b', bore, y0 - 0.01, y1 + 0.01, mat, 32, axis='Y', center=(cx, 0, cz))], mat)
    return o, g['rp']


def sprocket(name, z, pitch, roller_r, y0, y1, mat, cx=0.0, cz=0.0, phase=0.0):
    """Roller-chain sprocket about Y: pitch circle R = p / (2 sin(pi/z)); tooth gaps at roller seats."""
    R = pitch / (2 * math.sin(math.pi / z))
    ra = R + roller_r * 0.9
    body = cyl(name + 'b', ra, y0, y1, mat, max(48, z * 4), axis='Y', center=(cx, 0, cz))
    gaps = []
    for i in range(z):
        a = phase + TAU * i / z
        gaps.append(cyl(f'{name}g{i}', roller_r * 1.06, y0 - 0.01, y1 + 0.01, mat, 16, axis='Y', center=(cx + R * math.cos(a), 0, cz + R * math.sin(a))))
    return csg(name, [body], gaps, mat), R


# ------------------------------------------------------------------ open belt / chain path (pulleys about Y, in XZ)
def open_path(r1, r2, C, x1=0.0, cz=0.0):
    """Closed open-belt path around pulley 1 (centre x1, radius r1) and pulley 2 (x1 + C, r2), travelling clockwise.
    Returns (pos(s) -> (x, z, ang_deg_of_travel), total length)."""
    al = math.asin((r2 - r1) / C)
    th = math.pi / 2 + al
    st = math.sqrt(C * C - (r2 - r1) ** 2)
    a2 = r2 * (math.pi + 2 * al)
    a1 = r1 * (math.pi - 2 * al)
    L = 2 * st + a1 + a2
    c1, c2 = (x1, cz), (x1 + C, cz)

    def on(c, r, a):
        return c[0] + r * math.cos(a), c[1] + r * math.sin(a)

    p1u, p2u = on(c1, r1, th), on(c2, r2, th)
    p2l, p1l = on(c2, r2, -th), on(c1, r1, -th)
    d_top = math.atan2(p2u[1] - p1u[1], p2u[0] - p1u[0])
    d_bot = math.atan2(p1l[1] - p2l[1], p1l[0] - p2l[0])

    def pos(s):
        s %= L
        if s < st:
            f = s / st
            return p1u[0] + (p2u[0] - p1u[0]) * f, p1u[1] + (p2u[1] - p1u[1]) * f, d_top
        s -= st
        if s < a2:
            a = th - s / r2
            x, z = on(c2, r2, a)
            return x, z, a - math.pi / 2
        s -= a2
        if s < st:
            f = s / st
            return p2l[0] + (p1l[0] - p2l[0]) * f, p2l[1] + (p1l[1] - p2l[1]) * f, d_bot
        s -= st
        a = -th - s / r1
        x, z = on(c1, r1, a)
        return x, z, a - math.pi / 2
    return pos, L


def centre_for_links(r1, r2, pitch, n_links, c_guess):
    """Centre distance so that the open path length equals n_links * pitch (bisection)."""
    lo, hi = abs(r2 - r1) + 1e-3, c_guess * 4
    for _ in range(80):
        mid = (lo + hi) / 2
        if open_path(r1, r2, mid)[1] < n_links * pitch:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# ------------------------------------------------------------------ rotary vane chamber (axis Y)
def vane_reach(e, Rs, phi):
    """Distance from rotor centre (offset -e in z from the stator centre) to the stator bore along angle phi."""
    d_u = -e * math.sin(phi)
    return -d_u + math.sqrt(d_u * d_u - e * e + Rs * Rs)


def add_vanes(m, prefix, n, Rr, Rs, e, W, cz, lv, tv, mat='carbon', revs=1.0, explode=(0, -0.3, 0.2), ref='vane', name='Vane'):
    """Vanes that turn with a rotor centred (0, cz - e) and slide out to touch a stator bore of radius Rs centred (0, cz)."""
    czr = cz - e
    for i in range(n):
        a = TAU * i / n
        v = box(f'{prefix}{i}', (lv, W - 0.002, tv), (Rr - lv / 2 - 0.0005, W / 2, 0), mat)
        v = rotate(v, -a, 'Y')
        v.data.transform(Matrix.Translation((0, 0, czr)))
        p = m.part(f'{prefix}{i + 1}', f'{name} {i + 1}', 'rotating_element', pivot=(0, 0, czr),
                   explode=(explode[0], explode[1], explode[2] + 0.03 * i), info={'ref': ref})
        mesh = p.add(v, smooth_angle=30)
        rk, lk = [], []
        for f in range(OPERATE_FRAMES + 1):
            th = TAU * revs * f / OPERATE_FRAMES
            phi = a - th
            d = max(0.0, vane_reach(e, Rs, phi) - (Rr - 0.0005))
            rk.append((1 + f, (0.0, th, 0.0)))
            lk.append((1 + f, (d * math.cos(phi), 0.0, d * math.sin(phi))))
        d0 = max(0.0, vane_reach(e, Rs, a) - (Rr - 0.0005))
        mesh.data.transform(Matrix.Translation((d0 * math.cos(a), 0, d0 * math.sin(a))))
        lk = []
        for f in range(OPERATE_FRAMES + 1):
            phi = a - TAU * revs * f / OPERATE_FRAMES
            d = max(0.0, vane_reach(e, Rs, phi) - (Rr - 0.0005)) - d0
            lk.append((1 + f, (d * math.cos(phi), 0.0, d * math.sin(phi))))
        m.keyframes(mesh, 'Operate', 'rotation_euler', rk)
        m.keyframes(mesh, 'Operate', 'location', lk)


def slotted_rotor(name, Rr, W, n, lv, tv, czr, mat='steel', shaft_r=0.02, y_sh0=-0.03, y_sh1=0.4):
    slots = []
    for i in range(n):
        s = box(f'{name}s{i}', (lv + 0.004, W + 0.02, tv + 0.0008), (Rr - lv / 2 + 0.002, W / 2, 0), mat)
        s = rotate(s, -TAU * i / n, 'Y')
        s.data.transform(Matrix.Translation((0, 0, czr)))
        slots.append(s)
    return csg(name, [cyl(name + 'r', Rr - 0.0004, 0.0005, W - 0.0005, mat, 96, axis='Y', center=(0, 0, czr)),
                      cyl(name + 'sh', shaft_r, y_sh0, y_sh1, 'steel', 32, axis='Y', center=(0, 0, czr), ch=0.002)], slots, mat)


# ------------------------------------------------------------------ inline piston engine (crank along X)
def add_inline_engine(m, prefix, x0, cz, n, bore, stroke, rod, mat='paint_green', revs=1.0, label='Engine', head_mat=None,
                      explode=0.4, head_label='Cylinder Head, Valves & Injectors'):
    """Inline engine: crank axis along X at height cz, cylinders vertical.  Builds block (split), head, crankshaft,
    pistons and connecting rods with slider-crank keyframes.  Returns dict(x1, deck, pitch)."""
    r = stroke / 2
    pitch = bore * 1.35
    xs = [x0 + pitch * (i + 0.5) for i in range(n)]
    x1 = x0 + pitch * n
    phases = {4: [0, math.pi, math.pi, 0], 6: [0, 4 * math.pi / 3, 2 * math.pi / 3, 2 * math.pi / 3, 4 * math.pi / 3, 0],
              2: [0, math.pi], 3: [0, 2 * math.pi / 3, 4 * math.pi / 3], 1: [0]}[n]
    zp_top = cz + r + rod                # piston pin at TDC
    deck = zp_top + bore * 0.55 + 0.01
    hm = head_mat or mat
    from .core import split_many as _sm
    blk_o = [box(prefix + 'blk', (x1 - x0 + 0.06, bore * 1.7, deck - (cz - r - 0.05)), ((x0 + x1) / 2, 0, (deck + cz - r - 0.05) / 2), mat, bevel=0.01),
             box(prefix + 'sump', (x1 - x0 + 0.02, bore * 1.5, r + 0.12), ((x0 + x1) / 2, 0, cz - r - 0.05 - (r + 0.12) / 2 + 0.01), mat, bevel=0.012)]
    blk_i = [cyl(prefix + f'bo{i}', bore / 2 + 0.002, cz + r * 0.2, deck + 0.01, mat, 48, center=(x, 0, 0)) for i, x in enumerate(xs)]
    blk_i += [box(prefix + 'cc', (x1 - x0 - 0.0, bore * 1.35, 2 * r + 0.12), ((x0 + x1) / 2, 0, cz), mat, bevel=0.02),
              box(prefix + 'si', (x1 - x0 - 0.04, bore * 1.25, r + 0.08), ((x0 + x1) / 2, 0, cz - r - 0.05 - (r + 0.12) / 2 + 0.03), mat)]
    blk_i += [cyl(prefix + 'cb', 0.022, x0 - 0.06, x1 + 0.06, mat, 32, axis='X', center=(0, 0, cz))]
    blk = csg(prefix + 'block', blk_o, blk_i, mat)
    b, f = _sm(prefix + 'block', [blk])
    p = m.part(prefix + 'block', f'{label} – Cylinder Block & Crankcase', 'engine', section='split', explode=(0, 0, -0.25), info={'ref': 'engine_block'})
    p.add_split(b, f, smooth_angle=35)
    hd = csg(prefix + 'head', [box(prefix + 'h', (x1 - x0 + 0.04, bore * 1.6, bore * 0.5), ((x0 + x1) / 2, 0, deck + bore * 0.25), hm, bevel=0.008),
                               box(prefix + 'rc', (x1 - x0 + 0.02, bore * 1.3, bore * 0.35), ((x0 + x1) / 2, 0, deck + bore * 0.5 + bore * 0.17), hm, bevel=0.01)],
             [cyl(prefix + f'cc{i}', bore / 2 - 0.004, deck - 0.01, deck + bore * 0.12, hm, 40, center=(x, 0, 0)) for i, x in enumerate(xs)], hm)
    inj = [cyl(prefix + f'in{i}', 0.008, deck + 0.02, deck + bore * 0.95, 'chrome', 16, center=(x, 0, 0)) for i, x in enumerate(xs)]
    b, f = _sm(prefix + 'head', [hd] + inj)
    p = m.part(prefix + 'head', f'{label} – {head_label}', 'engine', section='split', explode=(0, 0, explode), info={'ref': 'engine_head'})
    p.add_split(b, f, smooth_angle=35)
    # crankshaft
    cs = [cyl(prefix + 'csm', 0.02, x0 - 0.05, x1 + 0.08, 'steel', 32, axis='X', center=(0, 0, cz), ch=0.002)]
    for i, (x, ph) in enumerate(zip(xs, phases)):
        py, pz = r * math.sin(ph), cz + r * math.cos(ph)
        cs.append(cyl(prefix + f'cp{i}', 0.016, x - bore * 0.22, x + bore * 0.22, 'steel', 24, axis='X', center=(0, py, pz)))
        for sx in (-1, 1):
            w = box(prefix + f'w{i}{sx}', (0.012, 0.05, r + 0.06), (x + sx * (bore * 0.22 + 0.006), 0, cz + (r - 0.02) / 2), 'steel', bevel=0.006)
            cs.append(rotate(w, -ph, 'X', (0, 0, cz)))
    p = m.part(prefix + 'crankshaft', f'{label} – Crankshaft', 'engine', pivot=(0, 0, cz), explode=(0, -0.35, -0.1), info={'ref': 'engine_crankshaft'})
    p.add(join(prefix + 'crankshaft', cs), smooth_angle=40)
    p.spin('X', revs)
    pis_meshes, rod_meshes = [], []
    pp = m.part(prefix + 'pistons', f'{label} – Pistons & Rings', 'engine', explode=(0, 0, explode + 0.25), info={'ref': 'engine_pistons'})
    rp = m.part(prefix + 'conrods', f'{label} – Connecting Rods', 'engine', explode=(0, -0.3, explode * 0.5), info={'ref': 'engine_conrods'})

    def zpin(th):
        return cz + r * math.cos(th) + math.sqrt(rod * rod - (r * math.sin(th)) ** 2)

    def gam(th):
        return math.asin(r * math.sin(th) / rod)
    for i, (x, ph) in enumerate(zip(xs, phases)):
        z0 = zpin(ph)
        pis = join(prefix + f'pi{i}', [cyl(prefix + f'pc{i}', bore / 2 - 0.001, z0 - bore * 0.35, z0 + bore * 0.3, 'aluminium', 40, center=(x, 0, 0)),
                                       cyl(prefix + f'pr{i}', bore / 2 + 0.0003, z0 + bore * 0.18, z0 + bore * 0.2, 'steel_dark', 40, center=(x, 0, 0)),
                                       cyl(prefix + f'pg{i}', 0.008, x - bore * 0.3, x + bore * 0.3, 'steel', 16, axis='X', center=(0, 0, z0))])
        pm = pp.add(pis, smooth_angle=35)
        pm.data.transform(Matrix.Translation((0, 0, 0)))
        g0 = gam(ph)
        rd = join(prefix + f'rd{i}', [box(prefix + f'rb{i}', (0.014, 0.016, rod - 0.03), (x, 0, z0 - rod / 2), 'steel', bevel=0.004),
                                      cyl(prefix + f're{i}', 0.026, x - 0.012, x + 0.012, 'steel', 24, axis='X', center=(0, 0, z0 - rod)),
                                      cyl(prefix + f'rs{i}', 0.014, x - 0.01, x + 0.01, 'steel', 16, axis='X', center=(0, 0, z0))])
        rd = rotate(rd, g0, 'X', (0, 0, z0))
        rm = rp.add(rd, smooth_angle=35)
        # piston/rod meshes have parent origin at part pivot (0,0,0); animate around the pin
        lk, rk, ok = [], [], []
        for fr in range(OPERATE_FRAMES + 1):
            th = ph - TAU * revs * fr / OPERATE_FRAMES
            dz = zpin(th) - z0
            lk.append((1 + fr, (0.0, 0.0, dz)))
            # rotation about the pin: rotate around (x,0,z0) => location compensation
            gg = gam(th) - g0
            c, s = math.cos(gg), math.sin(gg)
            # point P=(0,0,z0) maps to R*P; keep the pin at (0,0,z0+dz)
            oy = -(-s * z0)
            oz = z0 + dz - (c * z0)
            rk.append((1 + fr, (gg, 0.0, 0.0)))
            ok.append((1 + fr, (0.0, oy, oz)))
        m.keyframes(pm, 'Operate', 'location', lk)
        m.keyframes(rm, 'Operate', 'rotation_euler', rk)
        m.keyframes(rm, 'Operate', 'location', ok)
    return dict(x1=x1, deck=deck, xs=xs, top=deck + bore * 0.7)


# ------------------------------------------------------------------ misc
def pedestal(name, x, cz, r_shaft, foot_z, mat='cast_iron', w=None, axis='X'):
    """Plummer-block / pedestal bearing housing at x on an X shaft (axis='Y' -> at y on a Y shaft, x=0)."""
    R = r_shaft * 2.4
    w = w or R * 1.4
    if axis == 'X':
        h = cyl(name + 'h', R, x - w / 2, x + w / 2, mat, 40, axis='X', center=(0, 0, cz), r_in=r_shaft * 1.02)
        base = box(name + 'b', (w, R * 3.2, cz - foot_z - R * 0.4), (x, 0, foot_z + (cz - foot_z - R * 0.4) / 2), mat, bevel=0.004)
        ft = box(name + 'f', (w * 1.1, R * 4.2, 0.02), (x, 0, foot_z + 0.01), mat, bevel=0.003)
    else:
        h = cyl(name + 'h', R, x - w / 2, x + w / 2, mat, 40, axis='Y', center=(0, 0, cz), r_in=r_shaft * 1.02)
        base = box(name + 'b', (R * 3.2, w, cz - foot_z - R * 0.4), (0, x, foot_z + (cz - foot_z - R * 0.4) / 2), mat, bevel=0.004)
        ft = box(name + 'f', (R * 4.2, w * 1.1, 0.02), (0, x, foot_z + 0.01), mat, bevel=0.003)
    return join(name, [h, base, ft])


def ring_of(name, n, maker, cz=0.0, axis='X', phase=0.0):
    """Copies of maker(i) rotated about the X (or Y/Z) axis through (0,0,cz)."""
    return join(name, [rotate(maker(i), phase + TAU * i / n, axis, (0, 0, cz)) for i in range(n)])


def flow_ring(cx, cz, r, a0, a1, n=24, y=0.0, axis='Y'):
    """Polyline arc (for flow paths) in XZ about Y (axis='Y') from angle a0 to a1."""
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), y, cz + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def local_pivot(mesh, g):
    """Move a part mesh's own origin to world point g (relative to its part node at the origin) so rotation keys turn it about g."""
    from mathutils import Vector
    g = Vector(g) - mesh.parent.location
    mesh.data.transform(Matrix.Translation(-g))
    mesh.location = g
    return mesh


def axis_rot_keys(m, mesh, axis_vec, angle_fn, n=60):
    """Keyframe rotation of a mesh about an arbitrary axis (through its origin): angle_fn(phase 0..1) -> rad."""
    from mathutils import Vector
    ax = Vector(axis_vec).normalized()
    keys = []
    for k in range(n + 1):
        e = Matrix.Rotation(angle_fn(k / n), 4, ax).to_euler('XYZ')
        keys.append((1 + OPERATE_FRAMES * k / n, (e.x, e.y, e.z)))
    m.keyframes(mesh, 'Operate', 'rotation_euler', keys)
