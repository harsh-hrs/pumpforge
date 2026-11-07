"""Engineering shape generators: hydraulic vanes, involute gears, helpers."""
import math
from .core import mesh_from, TAU


def _lerp(a, b, t):
    return a + (b - a) * t


def _curve(pts, s):
    """Piecewise-linear interpolation of a list of (r, z) at s in [0,1]."""
    n = len(pts) - 1
    x = max(0.0, min(1.0, s)) * n
    i = min(int(x), n - 1)
    f = x - i
    return (_lerp(pts[i][0], pts[i + 1][0], f), _lerp(pts[i][1], pts[i + 1][1], f))


def vane(name, hub, shroud, theta_fn, thickness, mat, ns=18, nt=6, t_ext=0.06, axis_z=0.0,
         taper=0.35):
    """Closed (watertight) 3-D vane lofted between a hub and a shroud meridional
    curve.  theta_fn(s, t) -> wrap angle (rad).  Thickness is measured
    circumferentially and tapers toward leading/trailing edges.
    Returns a mesh object (axis = Z, z offset `axis_z`)."""
    verts = []

    def P(s, t, side):
        t2 = -t_ext + (1 + 2 * t_ext) * t
        rh, zh = _curve(hub, s)
        rs, zs = _curve(shroud, s)
        r = _lerp(rh, rs, t2)
        z = _lerp(zh, zs, t2)
        edge = min(s, 1 - s) / 0.5
        th = thickness * (taper + (1 - taper) * math.sin(min(1.0, edge) * math.pi / 2))
        th = max(th, thickness * 0.25)
        a = theta_fn(s, t2) + side * (th / 2) / max(r, 1e-4)
        return (r * math.cos(a), r * math.sin(a), z + axis_z)

    for side in (-1, 1):
        for i in range(ns + 1):
            for j in range(nt + 1):
                verts.append(P(i / ns, j / nt, side))
    N = (ns + 1) * (nt + 1)

    def V(side, i, j):
        return (0 if side < 0 else N) + i * (nt + 1) + j
    faces = []
    for i in range(ns):
        for j in range(nt):
            faces.append([V(-1, i, j), V(-1, i + 1, j), V(-1, i + 1, j + 1), V(-1, i, j + 1)])
            faces.append([V(1, i, j), V(1, i, j + 1), V(1, i + 1, j + 1), V(1, i + 1, j)])
    for i in range(ns):  # hub & shroud edges
        faces.append([V(-1, i, 0), V(1, i, 0), V(1, i + 1, 0), V(-1, i + 1, 0)])
        faces.append([V(-1, i, nt), V(-1, i + 1, nt), V(1, i + 1, nt), V(1, i, nt)])
    for j in range(nt):  # leading & trailing edges
        faces.append([V(-1, 0, j), V(-1, 0, j + 1), V(1, 0, j + 1), V(1, 0, j)])
        faces.append([V(-1, ns, j), V(1, ns, j), V(1, ns, j + 1), V(-1, ns, j + 1)])
    return mesh_from(name, verts, faces, [mat])


def involute_gear_profile(m, z, alpha_deg=20.0, steps=8, backlash=0.0, root_steps=4):
    """2-D polygon (u, v) of a spur gear by the standard involute construction.
    m = module [m], z = teeth.  Tooth k is centred on angle 2*pi*k/z."""
    a = math.radians(alpha_deg)
    rp = m * z / 2
    rb = rp * math.cos(a)
    ra = rp + m
    rf = rp - 1.25 * m
    inv = lambda x: math.tan(x) - x
    psi_p = math.pi / (2 * z) - backlash / (2 * rp)
    psi_b = psi_p + inv(a)

    def psi(r):
        if r <= rb:
            return psi_b
        return psi_b - inv(math.acos(rb / r))
    r0 = max(rb, rf)
    radii = [r0 + (ra - r0) * (i / steps) ** 0.8 for i in range(steps + 1)]
    pts = []
    for k in range(z):
        c = TAU * k / z
        # root -> right flank (angle c - psi)
        if rf < rb:
            pts.append((rf, c - psi_b))
        for r in radii:
            pts.append((r, c - psi(r)))
        # tip arc
        pts.append((ra, c))
        for r in reversed(radii):
            pts.append((r, c + psi(r)))
        if rf < rb:
            pts.append((rf, c + psi_b))
        # root arc to next tooth
        a0 = c + psi_b
        a1 = c + TAU / z - psi_b
        for i in range(1, root_steps):
            t = a0 + (a1 - a0) * i / root_steps
            pts.append((rf, t))
    return [(r * math.cos(t), r * math.sin(t)) for r, t in pts], dict(rp=rp, rb=rb, ra=ra, rf=rf)


def polygon_circle(r, n, phase=0.0):
    return [(r * math.cos(phase + TAU * i / n), r * math.sin(phase + TAU * i / n)) for i in range(n)]


def sweep_tube(name, path, radius, mat, segs=16, cap=True):
    """Tube of circular section swept along a 3-D polyline (parallel transport)."""
    import mathutils
    V = mathutils.Vector
    pts = [V(p) for p in path]
    n = len(pts)
    tang = []
    for i in range(n):
        if i == 0:
            t = pts[1] - pts[0]
        elif i == n - 1:
            t = pts[-1] - pts[-2]
        else:
            t = (pts[i + 1] - pts[i - 1])
        tang.append(t.normalized())
    up = V((0, 0, 1)) if abs(tang[0].z) < 0.9 else V((1, 0, 0))
    nrm = tang[0].cross(up).normalized()
    verts, faces = [], []
    for i in range(n):
        if i > 0:
            nrm = (nrm - tang[i] * nrm.dot(tang[i])).normalized()
        b = tang[i].cross(nrm)
        for j in range(segs):
            a = TAU * j / segs
            rr = radius[i] if isinstance(radius, (list, tuple)) else radius
            verts.append(tuple(pts[i] + (nrm * math.cos(a) + b * math.sin(a)) * rr))
    for i in range(n - 1):
        for j in range(segs):
            j2 = (j + 1) % segs
            faces.append([i * segs + j, i * segs + j2, (i + 1) * segs + j2, (i + 1) * segs + j])
    if cap:
        faces.append(list(range(segs))[::-1])
        faces.append([(n - 1) * segs + j for j in range(segs)])
    return mesh_from(name, verts, faces, [mat])


def cone_arrow(name, base, direction, length, radius, mat, segs=20):
    """Arrow head (cone) at `base` pointing along `direction`."""
    import mathutils
    V = mathutils.Vector
    d = V(direction).normalized()
    up = V((0, 0, 1)) if abs(d.z) < 0.9 else V((1, 0, 0))
    u = d.cross(up).normalized()
    w = d.cross(u)
    b = V(base)
    verts = [tuple(b + (u * math.cos(TAU * j / segs) + w * math.sin(TAU * j / segs)) * radius)
             for j in range(segs)]
    verts.append(tuple(b + d * length))
    verts.append(tuple(b))
    faces = [[j, (j + 1) % segs, segs] for j in range(segs)]
    faces += [[(j + 1) % segs, j, segs + 1] for j in range(segs)]
    return mesh_from(name, verts, faces, [mat])


def twisted_extrude(name, pts, h0, h1, lead, mat, steps=None, axis='Y', center=(0, 0, 0), hand=1):
    """Helical (twisted) extrusion of a closed 2-D profile (u, v) about the axis.
    The section rotates 2*pi*hand per `lead` of axial travel.  Watertight."""
    L = h1 - h0
    steps = steps or max(8, int(abs(L / lead) * 48))
    n = len(pts)
    cx, cy, cz = center
    verts = []
    for k in range(steps + 1):
        h = h0 + L * k / steps
        a = hand * TAU * (h - h0) / lead
        ca, sa = math.cos(a), math.sin(a)
        for (u, v) in pts:
            uu, vv = u * ca - v * sa, u * sa + v * ca
            if axis == 'Y':
                verts.append((cx + uu, cy + h, cz + vv))
            elif axis == 'X':
                verts.append((cx + h, cy + uu, cz + vv))
            else:
                verts.append((cx + uu, cy + vv, cz + h))
    faces = []
    for k in range(steps):
        for i in range(n):
            j = (i + 1) % n
            faces.append([k * n + i, k * n + j, (k + 1) * n + j, (k + 1) * n + i])
    faces.append(list(range(n))[::-1])
    faces.append([steps * n + i for i in range(n)])
    return mesh_from(name, verts, faces, [mat])


def lobed_profile(r_root, r_tip, lobes, n=96, phase=0.0, land=0.5, sharp=4.0):
    """Closed polygon r(phi) with `lobes` raised lands (fraction `land` of each period)."""
    pts = []
    for i in range(n):
        p = TAU * i / n
        x = math.cos(lobes * (p - phase))
        f = 1 / (1 + math.exp(-sharp * 3 * (x - math.cos(math.pi * land))))
        r = r_root + (r_tip - r_root) * f
        pts.append((r * math.cos(p), r * math.sin(p)))
    return pts
