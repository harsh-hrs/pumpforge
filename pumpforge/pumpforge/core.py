"""
PumpForge core: procedural, engineering-proportioned pump models for real-time
viewers (glTF 2.0 / GLB).

Conventions (see docs/MODEL_SPEC.md):
  * Modelled in Blender Z-up metres; exported as glTF Y-up metres.
  * Every component is a "part": an Empty node carrying glTF `extras`
    (part_id, part_name, group, section_role, explode_offset) with one or more
    mesh children.  Rotating/reciprocating motion is applied to mesh children,
    explode motion to the part node, so both clips can play together.
  * Cutaway: parts are either whole ('keep' / 'hide') or split into
    '<id>__back' (section_role 'back') and '<id>__front' (section_role 'front').
    The app hides 'front' and 'hide' nodes to show the section.  Cut faces use
    the SECTION material.
  * Animation clips: "Operate" (seamless loop) and "Explode" (0 -> exploded).
"""
import bpy, bmesh, math, json, os
from mathutils import Vector, Matrix

FPS = 30
OPERATE_FRAMES = 60   # 2.0 s loop
EXPLODE_FRAMES = 30   # 1.0 s
TAU = 2 * math.pi


# --------------------------------------------------------------------------
# colour / materials
# --------------------------------------------------------------------------
def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexcol(h):
    h = h.lstrip('#')
    return tuple(_lin(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)) + (1.0,)


MAT_LIBRARY = {
    # name: (sRGB hex, metallic, roughness, emissive hex or None)
    'paint_blue':      ('#1f4e8c', 0.0, 0.42, None),   # pump casing enamel
    'paint_blue_dark': ('#173a66', 0.0, 0.45, None),
    'paint_motor':     ('#3d4a57', 0.0, 0.48, None),   # motor enamel (slate)
    'paint_green':     ('#2f6b4f', 0.0, 0.45, None),
    'paint_red':       ('#b3261e', 0.0, 0.42, None),
    'paint_grey':      ('#8a9099', 0.0, 0.50, None),
    'paint_yellow':    ('#e0a800', 0.0, 0.45, None),   # safety guards
    'cast_iron':       ('#5b5e63', 0.75, 0.62, None),  # unpainted cast surfaces
    'ductile_iron':    ('#6a6d72', 0.80, 0.55, None),
    'steel':           ('#a7abb1', 1.0, 0.32, None),   # machined carbon steel
    'steel_dark':      ('#5f646b', 1.0, 0.40, None),   # fasteners
    'stainless':       ('#c4c8cd', 1.0, 0.22, None),
    'chrome':          ('#dfe3e8', 1.0, 0.10, None),
    'bronze':          ('#b07a3a', 1.0, 0.30, None),
    'brass':           ('#c9a046', 1.0, 0.28, None),
    'copper':          ('#c46a3a', 1.0, 0.33, None),
    'aluminium':       ('#cfd3d8', 1.0, 0.38, None),
    'lamination':      ('#4a4f57', 0.85, 0.42, None),  # electrical steel
    'rubber':          ('#1b1c1e', 0.0, 0.82, None),   # NBR/EPDM/neoprene
    'ptfe':            ('#ece9e2', 0.0, 0.55, None),
    'polypropylene':   ('#d9d4c7', 0.0, 0.50, None),
    'carbon':          ('#24262a', 0.2, 0.35, None),   # carbon-graphite
    'silicon_carbide': ('#3a3f45', 0.3, 0.25, None),
    'thermoplastic':   ('#2a2d31', 0.0, 0.40, None),   # terminal covers etc
    'nameplate':       ('#d7dbe0', 1.0, 0.25, None),
    'section':         ('#d64a2b', 0.0, 0.60, None),   # cutaway section faces
    'flow_suction':    ('#1f8fff', 0.0, 0.50, '#0b3f7a'),
    'flow_discharge':  ('#ff5a14', 0.0, 0.50, '#7a2606'),
    'air':             ('#7cc832', 0.0, 0.50, '#2f5a10'),
    # valves & piping
    'glass':           ('#c6e6f2', 0.0, 0.06, None),
    'water':           ('#3d8fd6', 0.0, 0.18, '#0b2f55'),
    'flame':           ('#ff7a1a', 0.0, 0.40, '#ff4500'),
    'steam':           ('#eef3f7', 0.0, 0.45, '#8a99a8'),
    'hydraulic_oil':   ('#d9a227', 0.0, 0.35, '#5c420a'),
    'insulation':      ('#e3cf7c', 0.0, 0.92, None),
    'cladding':        ('#d5d9de', 1.0, 0.33, None),
    'coating':         ('#7d3a2b', 0.0, 0.55, None),
    'foam':            ('#f0c419', 0.0, 0.85, None),
    'heat':            ('#ff3b30', 0.0, 0.45, '#7a1208'),
    'electric':        ('#ffcc00', 0.0, 0.40, '#b38600'),
    'flue_gas':        ('#9c8878', 0.0, 0.55, '#3d3029'),
    'exhaust':         ('#c9772f', 0.0, 0.50, '#6b3510'),
    'pcb':             ('#1f6b3a', 0.0, 0.45, None),
    'magnet_n':        ('#c0392b', 0.3, 0.35, None),
    'magnet_s':        ('#2e5eaa', 0.3, 0.35, None),
    'paint_orange':    ('#e2711d', 0.0, 0.45, None),
    'belt':            ('#1d1e20', 0.0, 0.70, None),
    'power':           ('#d63384', 0.0, 0.40, '#7a1240'),
    'ore':             ('#7a6a58', 0.0, 0.85, None),
    'coal':            ('#2b2b2e', 0.0, 0.70, None),
    'sand':            ('#c8b38a', 0.0, 0.90, None),
    'refractory':      ('#c79a72', 0.0, 0.92, None),
    'hot_glow':        ('#ffb347', 0.0, 0.45, '#ff7a00'),
    'powder':          ('#eee3c8', 0.0, 0.90, None),
    'brine':           ('#7fb8c9', 0.0, 0.15, None),
    'bauxite':         ('#a0522d', 0.0, 0.85, None),
    'red_mud':         ('#8b3a1a', 0.0, 0.70, None),
    'liquor':          ('#c9a46a', 0.0, 0.20, None),
    'resin_cation':    ('#6b2f12', 0.0, 0.55, None),
    'resin_anion':     ('#e2c27f', 0.0, 0.55, None),
    'uv_glow':         ('#c9b3ff', 0.0, 0.30, '#7a3cff'),
    'sludge':          ('#5a4a32', 0.0, 0.80, None),
    # teaching overlays
    'thrust':          ('#d81b60', 0.0, 0.45, '#5a0b28'),   # axial thrust arrows
    'counter_force':   ('#2e9d4a', 0.0, 0.45, '#0f3d1b'),   # balancing force arrows
    'wear_light':      ('#f4d03f', 0.0, 0.55, '#6b5a12'),
    'wear_moderate':   ('#e0399a', 0.0, 0.50, '#5c0f3a'),
    'wear_severe':     ('#6c2bd9', 0.0, 0.45, '#2a0b66'),
}
# pressure gradient for stage-by-stage overlays (low -> high)
for _i, _hx in enumerate(['#2b6cb0', '#2f8fb8', '#33a89a', '#5cb85c', '#a6c23a', '#e0b52b', '#ef8a2b', '#e4572e', '#c0262c', '#8e1b2e']):
    MAT_LIBRARY[f'pressure_{_i}'] = (_hx, 0.0, 0.5, None)

_mats = {}


def M(name):
    """Get (or create) a PBR material from the library."""
    if name in _mats and _mats[name].name in bpy.data.materials:
        return _mats[name]
    hx, metal, rough, emit = MAT_LIBRARY[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = hexcol(hx)
    b.inputs['Metallic'].default_value = metal
    b.inputs['Roughness'].default_value = rough
    if emit:
        b.inputs['Emission Color'].default_value = hexcol(emit)
        b.inputs['Emission Strength'].default_value = 1.0
    m.diffuse_color = hexcol(hx)
    _mats[name] = m
    return m


# --------------------------------------------------------------------------
# mesh construction
# --------------------------------------------------------------------------
def _link(obj):
    bpy.context.scene.collection.objects.link(obj)
    return obj


def mesh_from(name, verts, faces, mats, face_mat=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.validate(clean_customdata=False)
    for m in mats:
        me.materials.append(m if isinstance(m, bpy.types.Material) else M(m))
    if face_mat:
        for p, i in zip(me.polygons, face_mat):
            p.material_index = i
    obj = _link(bpy.data.objects.new(name, me))
    recalc_normals(obj)
    return obj


def recalc_normals(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()


def _axis_map(axis):
    # returns f(r, theta, h) -> (x, y, z); theta in [0, pi] is the BACK half (y > 0)
    if axis == 'Z':
        return lambda r, t, h: (r * math.cos(t), r * math.sin(t), h)
    if axis == 'X':
        return lambda r, t, h: (h, r * math.sin(t), r * math.cos(t))
    if axis == 'Y':
        return lambda r, t, h: (r * math.cos(t), h, r * math.sin(t))
    raise ValueError(axis)


def lathe(name, profile, mat, segs=64, a0=0.0, a1=TAU, axis='Z', center=(0, 0, 0),
          cap_mat='section'):
    """Revolve a closed (r, h) polygon.  Partial revolutions are capped with
    the profile polygon (material `cap_mat`, used for cutaway section faces)."""
    full = abs((a1 - a0) - TAU) < 1e-9
    f = _axis_map(axis)
    cx, cy, cz = center
    nring = segs if full else segs + 1
    verts, faces, fmat = [], [], []
    idx = []  # idx[i][j]
    for (r, h) in profile:
        if r < 1e-9:
            x, y, z = f(0, 0, h)
            verts.append((x + cx, y + cy, z + cz))
            idx.append([len(verts) - 1] * nring)
        else:
            row = []
            for j in range(nring):
                t = a0 + (a1 - a0) * j / segs
                x, y, z = f(r, t, h)
                verts.append((x + cx, y + cy, z + cz))
                row.append(len(verts) - 1)
            idx.append(row)
    n = len(profile)
    for i in range(n):
        i2 = (i + 1) % n
        for j in range(segs):
            j2 = (j + 1) % nring if full else j + 1
            q = [idx[i][j], idx[i2][j], idx[i2][j2], idx[i][j2]]
            qq = []
            for v in q:
                if v not in qq:
                    qq.append(v)
            if len(qq) >= 3:
                faces.append(qq)
                fmat.append(0)
    if not full:
        faces.append([idx[i][0] for i in range(n)])
        fmat.append(1)
        faces.append([idx[i][nring - 1] for i in range(n)][::-1])
        fmat.append(1)
    return mesh_from(name, verts, faces, [mat, cap_mat], fmat)


def lathe_split(name, profile, mat, segs=64, axis='Z', center=(0, 0, 0), phase=0.0):
    """Return (back, front) half solids of revolution with section caps.
    phase rotates the cut: default keeps +y (axes Z, X) or +z (axis Y);
    axis Y with phase=pi/2 keeps -x."""
    h = max(8, segs // 2)
    back = lathe(name + '__back', profile, mat, h, phase, phase + math.pi, axis, center)
    front = lathe(name + '__front', profile, mat, h, phase + math.pi, phase + TAU, axis, center)
    return back, front


def ring_profile(r_in, r_out, h0, h1, ch=0.0):
    """Rectangular annulus profile with optional outer-edge chamfer."""
    if ch <= 0:
        return [(r_in, h0), (r_out, h0), (r_out, h1), (r_in, h1)]
    return [(r_in, h0), (r_out - ch, h0), (r_out, h0 + ch), (r_out, h1 - ch),
            (r_out - ch, h1), (r_in, h1)]


def cyl(name, r, h0, h1, mat, segs=48, axis='Z', center=(0, 0, 0), ch=0.0, r_in=0.0):
    return lathe(name, ring_profile(r_in, r, h0, h1, ch), mat, segs, axis=axis, center=center)


def extrude_poly(name, pts, z0, z1, mat, plane='XZ', offset=(0, 0, 0), side_mat=None):
    """Extrude a 2-D polygon (u, v) between z0..z1 along the plane normal.
    plane 'XZ' -> extrusion along Y, 'XY' -> along Z, 'YZ' -> along X."""
    n = len(pts)

    def P(u, v, w):
        if plane == 'XZ':
            p = (u, w, v)
        elif plane == 'XY':
            p = (u, v, w)
        else:
            p = (w, u, v)
        return (p[0] + offset[0], p[1] + offset[1], p[2] + offset[2])
    verts = [P(u, v, z0) for u, v in pts] + [P(u, v, z1) for u, v in pts]
    faces = [list(range(n))[::-1], list(range(n, 2 * n))]
    fm = [0, 0]
    for i in range(n):
        j = (i + 1) % n
        faces.append([i, j, n + j, n + i])
        fm.append(1 if side_mat else 0)
    mats = [mat, side_mat] if side_mat else [mat]
    return mesh_from(name, verts, faces, mats, fm)


def box(name, size, center, mat, bevel=0.0, segs=2):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=bm.edges[:] + bm.verts[:], offset=bevel, segments=segs,
                        profile=0.5, affect='EDGES', clamp_overlap=True)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(M(mat) if isinstance(mat, str) else mat)
    me.materials.append(M('section'))
    obj = _link(bpy.data.objects.new(name, me))
    recalc_normals(obj)
    return obj


def hex_prism(name, af, h0, h1, mat, axis='Z', center=(0, 0, 0), ch=True):
    """Hexagon across-flats `af`; chamfered top like a real nut/bolt head."""
    rc = af / math.sqrt(3)  # corner radius
    pts = [(rc * math.cos(math.pi / 6 + i * math.pi / 3), rc * math.sin(math.pi / 6 + i * math.pi / 3))
           for i in range(6)]
    plane = {'Z': 'XY', 'Y': 'XZ', 'X': 'YZ'}[axis]
    o = extrude_poly(name, pts, h0, h1, mat, plane=plane, offset=center)
    if ch:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=af * 0.06, segments=1, affect='EDGES',
                        clamp_overlap=True)
        bm.to_mesh(o.data)
        bm.free()
    return o


def transform(obj, mat4):
    obj.data.transform(mat4)
    obj.data.update()
    return obj


def move(obj, v):
    return transform(obj, Matrix.Translation(Vector(v)))


def rotate(obj, angle, axis='Z', origin=(0, 0, 0)):
    o = Vector(origin)
    m = Matrix.Translation(o) @ Matrix.Rotation(angle, 4, axis) @ Matrix.Translation(-o)
    return transform(obj, m)


def delete(obj):
    me = obj.data
    bpy.data.objects.remove(obj, do_unlink=True)
    if me and me.users == 0:
        bpy.data.meshes.remove(me)


def join(name, objs):
    """Merge mesh objects (world space) into one, unifying material slots."""
    objs = [o for o in objs if o is not None]
    mats, bm = [], bmesh.new()
    for o in objs:
        me = o.data.copy()
        me.transform(o.matrix_world)
        remap = []
        for m in me.materials:
            if m not in mats:
                mats.append(m)
            remap.append(mats.index(m))
        nf = len(bm.faces)
        bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        for f in bm.faces[nf:]:
            f.material_index = remap[f.material_index] if remap else 0
        bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    me.validate(clean_customdata=False)
    for o in objs:
        delete(o)
    return _link(bpy.data.objects.new(name, me))


def boolean(target, tool, op='DIFFERENCE', keep_tool=False):
    """Apply a boolean with the Manifold solver (falls back to Exact)."""
    for solver in ('MANIFOLD', 'EXACT'):
        mod = target.modifiers.new('bool', 'BOOLEAN')
        mod.operation = op
        mod.object = tool
        mod.solver = solver
        if solver == 'EXACT':
            mod.use_self = False
        tool.hide_set(True)
        dg = bpy.context.evaluated_depsgraph_get()
        ev = target.evaluated_get(dg)
        new = bpy.data.meshes.new_from_object(ev)
        target.modifiers.remove(mod)
        if len(new.polygons) > 0 or op == 'INTERSECT':
            old = target.data
            target.data = new
            # keep tool materials (new_from_object includes them)
            if old.users == 0:
                bpy.data.meshes.remove(old)
            break
        bpy.data.meshes.remove(new)
    if not keep_tool:
        delete(tool)
    else:
        tool.hide_set(False)
    return target


def csg(name, outers, inners=(), mat=None):
    """Union of outer solids minus union of inner solids."""
    base = outers[0]
    for o in outers[1:]:
        boolean(base, o, 'UNION')
    for i in inners:
        boolean(base, i, 'DIFFERENCE')
    base.name = name
    base.data.name = name
    if mat is not None:
        _set_single_material(base, mat)
    return base


def _set_single_material(obj, mat):
    me = obj.data
    me.materials.clear()
    me.materials.append(M(mat) if isinstance(mat, str) else mat)
    me.materials.append(M('section'))
    for p in me.polygons:
        p.material_index = 0


def mark_section(obj, axis='y', value=0.0, tol=1e-4):
    me = obj.data
    names = [m.name for m in me.materials]
    if 'section' not in names:
        me.materials.append(M('section'))
        names.append('section')
    si = names.index('section')
    k = 'xyz'.index(axis)
    for p in me.polygons:
        if all(abs(me.vertices[v].co[k] - value) < tol for v in p.vertices):
            p.material_index = si


def split(obj, axis='y', value=0.0):
    """Split a closed solid into (back = coordinate > value, front) halves."""
    k = 'xyz'.index(axis)
    size = [200.0, 200.0, 200.0]
    c = [0.0, 0.0, 0.0]
    c[k] = value + 100.0
    name = obj.name
    back = obj.copy()
    back.data = obj.data.copy()
    _link(back)
    cutter = box('cutter', size, c, 'section')
    boolean(back, cutter, 'INTERSECT')
    cutter = box('cutter', size, c, 'section')
    boolean(obj, cutter, 'DIFFERENCE')
    for o in (back, obj):
        mark_section(o, axis, value)
    back.name = name + '__back'
    obj.name = name + '__front'
    return back, obj


def smooth(obj, angle_deg=32.0):
    """Smooth shading with hard edges above `angle_deg` (CAD-style shading)."""
    thr = math.radians(angle_deg)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        if not e.is_manifold:
            e.smooth = False
            continue
        a = e.calc_face_angle(None)
        mats = {f.material_index for f in e.link_faces}
        e.smooth = not ((a is not None and a > thr) or len(mats) > 1)
    bm.to_mesh(obj.data)
    bm.free()
    return obj


def bolt_circle(name, n, pcd, af, h0, h1, axis='Z', center=(0, 0, 0), phase=None, mat='steel_dark',
                stud=None):
    """Ring of hex nuts (+ optional stud ends) on a flange face."""
    phase = math.pi / n if phase is None else phase
    parts = []
    f = _axis_map(axis)
    for i in range(n):
        t = phase + TAU * i / n
        x, y, z = f(pcd / 2, t, 0)
        c = (center[0] + x, center[1] + y, center[2] + z)
        parts.append(hex_prism(f'{name}_{i}', af, h0, h1, mat, axis=axis, center=c))
        if stud:
            ds, sh0, sh1 = stud
            parts.append(cyl(f'{name}_s{i}', ds / 2, sh0, sh1, mat, 12, axis=axis, center=c, ch=ds * 0.1))
    return join(name, parts)


# --------------------------------------------------------------------------
# model / part graph, animation, export
# --------------------------------------------------------------------------
def bl2gl(v):
    """Blender Z-up -> glTF Y-up."""
    return [round(v[0], 5), round(v[2], 5), round(-v[1], 5)]


def _linearize(act):
    """Force LINEAR interpolation on every key of an action (Blender 5 slotted actions aware)."""
    fcs = []
    try:
        fcs = list(act.fcurves)
    except Exception:
        fcs = []
    if not fcs and hasattr(act, 'layers'):
        for layer in act.layers:
            for strip in layer.strips:
                for cb in getattr(strip, 'channelbags', []):
                    fcs += list(cb.fcurves)
    for fc in fcs:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
    return len(fcs)


class Part:
    def __init__(self, model, pid, name, group, pivot=(0, 0, 0), explode=(0, 0, 0),
                 section='keep', info=None):
        self.model, self.id, self.name, self.group = model, pid, name, group
        self.pivot = Vector(pivot)
        self.explode = Vector(explode)
        self.section = section
        self.info = info or {}
        e = bpy.data.objects.new(pid, None)
        e.empty_display_size = 0.02
        e.location = self.pivot
        e.parent = model.root
        _link(e)
        e['part_id'] = pid
        e['part_name'] = name
        e['group'] = group
        e['section_role'] = section
        e['explode_offset'] = bl2gl(self.explode)
        self.node = e
        self.meshes = []
        model.parts.append(self)

    def add(self, obj, role=None, smooth_angle=32.0):
        if obj is None:
            return None
        role = role or ('keep' if self.section == 'split' else self.section)
        if smooth_angle:
            smooth(obj, smooth_angle)
        obj.data.transform(Matrix.Translation(-self.pivot))
        obj.parent = self.node
        obj.location = (0, 0, 0)
        obj['part_id'] = self.id
        obj['section_role'] = role
        self.meshes.append(obj)
        return obj

    def add_split(self, back, front, smooth_angle=32.0):
        b = self.add(back, 'back', smooth_angle)
        f = self.add(front, 'front', smooth_angle)
        if b is not None:
            b.name = self.id + '__back'
        if f is not None:
            f.name = self.id + '__front'
        return b, f

    # --- Operate clip helpers (act on mesh children) ---
    def spin(self, axis='Z', revs=1.0):
        k = 'XYZ'.index(axis)
        for m in self.meshes:
            keys = []
            for i in range(0, 9):
                fr = 1 + OPERATE_FRAMES * i / 8
                rot = [0.0, 0.0, 0.0]
                rot[k] = TAU * revs * i / 8
                keys.append((fr, tuple(rot)))
            self.model.keyframes(m, 'Operate', 'rotation_euler', keys)

    def cycle_translate(self, samples):
        """samples: list of (phase 0..1, (dx,dy,dz)) - must start/end equal."""
        for m in self.meshes:
            keys = [(1 + OPERATE_FRAMES * p, tuple(d)) for p, d in samples]
            self.model.keyframes(m, 'Operate', 'location', keys)


class Model:
    def __init__(self, pump_id, title, category, meta):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        _mats.clear()
        sc = bpy.context.scene
        sc.render.fps = FPS
        sc.frame_start, sc.frame_end = 1, 1 + OPERATE_FRAMES
        sc.frame_current = 1
        bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
        self.id, self.title, self.category, self.meta = pump_id, title, category, meta
        self.root = _link(bpy.data.objects.new(pump_id, None))
        self.root['pump_id'] = pump_id
        self.root['title'] = title
        self.root['model_type'] = 'explanatory_engineering_model'
        self.root['disclaimer'] = DISCLAIMER
        self.parts = []
        self._anims = {}   # (id_data_name, clip) -> list
        self.flow_root = None
        self.flow_paths = []    # polylines for app-side animated particles
        self.overlays = {}      # kind -> root empty (exported to <id>_<kind>.glb)
        self.overlay_info = {}  # kind -> dict(title, description, annotations)

    def overlay(self, kind, obj, title=None, description=None, smooth_angle=50, split=False, xray=None):
        """Attach a mesh to a named teaching overlay (wear, pressure, thrust ...).
        Each overlay is exported as its own GLB with the same origin as the model."""
        if kind not in self.overlays:
            r = _link(bpy.data.objects.new(f'{self.id}_{kind}', None))
            r['overlay'] = kind
            self.overlays[kind] = r
            self.overlay_info[kind] = {'file': f'{self.id}_{kind}.glb', 'title': title or kind, 'description': description or '', 'render': 'normal', 'annotations': []}
        if title:
            self.overlay_info[kind]['title'] = title
        if description:
            self.overlay_info[kind]['description'] = description
        if xray is not None:
            self.overlay_info[kind]['render'] = 'xray' if xray else 'normal'
        if obj is not None and split:
            # cutaway-aware overlay: halves tagged like part meshes so the app hides the front one
            b, f = split_many(obj.name, [obj], 'y', 0.0)
            for o, role in ((b, 'back'), (f, 'front')):
                if o is not None:
                    o['section_role'] = role
                    self.overlay(kind, o, smooth_angle=smooth_angle, xray=xray)
            return b
        if obj is not None:
            if smooth_angle:
                smooth(obj, smooth_angle)
            obj.parent = self.overlays[kind]
        return obj

    def annotate(self, kind, text, pos, value=None):
        """Text annotation for an overlay (rendered by the app as a label at pos)."""
        self.overlay(kind, None)
        a = {'text': text, 'anchor': bl2gl(Vector(pos))}
        if value is not None:
            a['value'] = value
        self.overlay_info[kind]['annotations'].append(a)

    def flow(self, name, path, kind='flow_discharge', radius=0.01, arrow_every=0.35, speed=None, active=None):
        """Flow-path overlay (exported to <id>_flow.glb): tube + arrow heads.  The polyline is also stored in the
        metadata (flow_paths) so the app can animate particles along it; `speed` = optional relative speed per point."""
        from .shapes import sweep_tube, cone_arrow
        fp = {'name': name, 'kind': kind, 'radius': radius, 'points': [bl2gl(Vector(q)) for q in path]}
        if speed:
            fp['speed'] = list(speed)
        if active:
            fp['active'] = [list(a) for a in active]   # loop phases (0..1) when this path carries flow
        self.flow_paths.append(fp)
        if self.flow_root is None:
            self.flow_root = _link(bpy.data.objects.new(self.id + '_flow', None))
            self.flow_root['overlay'] = 'flow_path'
        objs = [sweep_tube(name, path, radius, kind)]
        acc = 0.0
        for a, b in zip(path[:-1], path[1:]):
            a, b = Vector(a), Vector(b)
            seg = (b - a).length
            acc += seg
            if acc >= arrow_every and seg > 1e-6:
                acc = 0.0
                d = (b - a).normalized()
                objs.append(cone_arrow(name + '_a', b - d * radius * 3, d, radius * 5, radius * 2.6, kind))
        o = join(name, objs)
        smooth(o, 60)
        o.parent = self.flow_root
        o['flow_kind'] = kind
        return o

    def part(self, *a, **k):
        return Part(self, *a, **k)

    def keyframes(self, id_data, clip, path, keys):
        """Store keyframes; baked into per-clip NLA tracks at export."""
        self._anims.setdefault((id_data, clip), []).append((path, keys))

    def morph(self, obj, key_name, clip, keys):
        self.keyframes(obj.data.shape_keys, clip, f'key_blocks["{key_name}"].value',
                       [(f, (v,)) for f, v in keys])

    def _bake(self):
        # Explode clip for every part node
        for p in self.parts:
            if p.explode.length > 1e-6:
                self.keyframes(p.node, 'Explode', 'location',
                               [(1, tuple(p.pivot)), (1 + EXPLODE_FRAMES, tuple(p.pivot + p.explode))])
        for (idd, clip), chans in self._anims.items():
            ad = idd.animation_data_create()
            act = bpy.data.actions.new(f'{clip}_{idd.name}')
            ad.action = act
            rest = {}
            for path, keys in chans:
                try:
                    rest[path] = tuple(idd.path_resolve(path)) if not path.endswith('.value') \
                        else idd.path_resolve(path)
                except Exception:
                    rest[path] = None
                for fr, val in keys:
                    if path.endswith('.value'):
                        exec_path = path.rsplit('.', 1)[0]
                        kb = idd.path_resolve(exec_path)
                        kb.value = val[0]
                        kb.keyframe_insert('value', frame=fr)
                    else:
                        setattr(idd, path, val)
                        idd.keyframe_insert(path, frame=fr)
            # restore rest pose
            for path, v in rest.items():
                if v is None:
                    continue
                if path.endswith('.value'):
                    idd.path_resolve(path.rsplit('.', 1)[0]).value = v
                else:
                    setattr(idd, path, v)
            _linearize(act)
            tr = ad.nla_tracks.new()
            tr.name = clip
            tr.strips.new(clip, 1, act)
            ad.action = None

    def export(self, out_dir):
        os.makedirs(os.path.join(out_dir, 'glb'), exist_ok=True)
        os.makedirs(os.path.join(out_dir, 'meta'), exist_ok=True)
        # remove construction leftovers that never became part of the model
        for o in list(bpy.context.scene.objects):
            if o.type == 'MESH' and o.parent is None:
                print(f'NOTE: removing stray object {o.name}')
                delete(o)
        bpy.context.view_layer.update()
        meta = self._metadata()
        self._bake()
        bpy.context.scene.frame_set(1)
        flow = set()
        if self.flow_root:
            flow = {self.flow_root} | set(self.flow_root.children_recursive)
        ovl = {k: {r} | set(r.children_recursive) for k, r in self.overlays.items()}
        for objs in ovl.values():
            flow |= objs
        for o in bpy.context.scene.objects:
            o.hide_set(False)
            o.select_set(o not in flow)
        path = os.path.join(out_dir, 'glb', f'{self.id}.glb')
        self._gltf(path)
        if flow:
            for o in bpy.context.scene.objects:
                o.select_set(o in flow)
            fl = {self.flow_root} | set(self.flow_root.children_recursive) if self.flow_root else set()
            if fl:
                for o in bpy.context.scene.objects:
                    o.select_set(o in fl)
                self._gltf(os.path.join(out_dir, 'glb', f'{self.id}_flow.glb'), anim=False)
            for k, objs in ovl.items():
                for o in bpy.context.scene.objects:
                    o.select_set(o in objs)
                self._gltf(os.path.join(out_dir, 'glb', f'{self.id}_{k}.glb'), anim=False)
        with open(os.path.join(out_dir, 'meta', f'{self.id}.json'), 'w') as fh:
            json.dump(meta, fh, indent=2, ensure_ascii=False)
        return path

    def _gltf(self, path, anim=True):
        bpy.ops.export_scene.gltf(
            filepath=path, export_format='GLB', export_extras=True, export_yup=True, use_selection=True,
            export_apply=True, export_animations=anim, export_animation_mode='NLA_TRACKS',
            export_morph=True, export_morph_normal=True, export_force_sampling=True,
            export_frame_step=1, export_materials='EXPORT', export_cameras=False,
            export_lights=False, export_def_bones=False)

    def _metadata(self):
        parts = []
        tri = 0
        for p in self.parts:
            pts = []
            for m in p.meshes:
                mw = p.node.matrix_world
                for v in m.data.vertices:
                    pts.append(mw @ v.co)
                tri += sum(len(poly.vertices) - 2 for poly in m.data.polygons)
            if pts:
                lo = Vector((min(v.x for v in pts), min(v.y for v in pts), min(v.z for v in pts)))
                hi = Vector((max(v.x for v in pts), max(v.y for v in pts), max(v.z for v in pts)))
            else:
                lo = hi = p.pivot
            c = (lo + hi) / 2
            gl_lo, gl_hi = bl2gl(lo), bl2gl(hi)
            parts.append({
                'id': p.id, 'name': p.name, 'group': p.group,
                'section_role': p.section,
                'nodes': [m.name for m in p.meshes],
                'pivot': bl2gl(p.pivot),
                'explode_offset': bl2gl(p.explode),
                'bbox_min': [min(a, b) for a, b in zip(gl_lo, gl_hi)],
                'bbox_max': [max(a, b) for a, b in zip(gl_lo, gl_hi)],
                'label_anchor': bl2gl(Vector((c.x, lo.y, c.z))),
                'center': bl2gl(c),
                'info_ref': p.info.get('ref', p.id),
                **({'note': p.info['note']} if 'note' in p.info else {}),
            })
        m = dict(self.meta)
        from .common_meta import COMMON
        allc = {**COMMON, **m.pop('components')}
        used = [p['info_ref'] for p in parts]
        missing = sorted({u for u in used if u not in allc})
        if missing:
            print('WARNING: no component info for', missing)
        comps = {u: allc[u] for u in dict.fromkeys(used) if u in allc}
        cat, entry = _catalog_entry(self.id)
        overlays = {'flow': {'file': f'{self.id}_flow.glb', 'title': 'Flow path', 'description': 'Suction and discharge flow paths with direction arrows.', 'annotations': []}} if self.flow_root else {}
        overlays.update(self.overlay_info)
        return {
            'schema': 'pumpforge.model/1.1',
            'pump_id': self.id, 'title': self.title,
            'category': f"{cat['id']} · {cat['name']}" if cat else self.category,
            'library': ({'no': entry['no'], 'phase': entry['phase'], **({'eq_id': entry['eq_id'], 'subcategory': entry['subcategory']} if 'eq_id' in entry else {}), 'hi_family': cat['hi_family'], 'flagship': entry.get('flagship', False),
                         **({'api_610_type': entry['api_610_type']} if 'api_610_type' in entry else {}),
                         **({'built_from': entry['built_from']} if 'built_from' in entry else {})} if entry else {}),
            'overlays': overlays,
            'flow_paths': self.flow_paths,
            'units': 'metre', 'up_axis': '+Y', 'front_axis': '+Z',
            'disclaimer': DISCLAIMER,
            'animations': {
                'Operate': {'duration_s': OPERATE_FRAMES / FPS, 'loop': True},
                'Explode': {'duration_s': EXPLODE_FRAMES / FPS, 'loop': False,
                            'note': 'Play forward to explode, reverse to assemble; or lerp part nodes by explode_offset.'},
            },
            'cutaway': {'hide_section_roles': ['front', 'hide'],
                        'plane': 'XY (glTF), section faces use material "section"'},
            'stats': {'triangles': tri, 'parts': len(parts)},
            **m,
            'parts': parts,
            'components': comps,
        }


def _catalog_entry(pid):
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'catalog.json')
    try:
        cat = json.load(open(path, encoding='utf-8'))
    except Exception:
        return None, None
    for c in cat['categories']:
        for p in c['pumps']:
            if p['id'] == pid:
                return c, p
    return None, None


DISCLAIMER = ('Explanatory 3-D engineering model generated procedurally from typical '
              'published arrangements. Proportions are representative, not a certified '
              'manufacturer drawing. Do not use for fabrication, dimensional checks or '
              'compliance verification.')


# --------------------------------------------------------------------------
# side-grouping helpers for cutaway halves
# --------------------------------------------------------------------------
def _centroid(o, k):
    vs = o.data.vertices
    return sum(v.co[k] for v in vs) / max(1, len(vs))


def group_by(objs, name, axis='y', value=0.0, keep_positive=True):
    """Group separate closed objects into (back, front) by centroid along axis.
    'back' is the kept half (positive side unless keep_positive=False)."""
    k = 'xyz'.index(axis)
    b, f = [], []
    for o in objs:
        pos = _centroid(o, k) > value
        (b if pos == keep_positive else f).append(o)
    return (join(name + '__b', b) if b else None, join(name + '__f', f) if f else None)


def merge_halves(name, pairs):
    backs = [p[0] for p in pairs if p[0] is not None]
    fronts = [p[1] for p in pairs if p[1] is not None]
    return (join(name + '__back', backs) if backs else None,
            join(name + '__front', fronts) if fronts else None)


def split_faces(obj, axis='y', value=0.0, keep_positive=True):
    """Divide a multi-island object (e.g. a bolt ring) by face centroid, no cutting."""
    k = 'xyz'.index(axis)
    out = []
    for want_back in (True, False):
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        kill = [f for f in bm.faces
                if ((f.calc_center_median()[k] > value) == keep_positive) != want_back]
        bmesh.ops.delete(bm, geom=kill, context='FACES')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        me = bpy.data.meshes.new(obj.name + ('_b' if want_back else '_f'))
        bm.to_mesh(me)
        bm.free()
        for mm in obj.data.materials:
            me.materials.append(mm)
        out.append(_link(bpy.data.objects.new(me.name, me)) if len(me.polygons) else None)
    delete(obj)
    return out[0], out[1]


def split_keep(obj, axis='y', value=0.0, keep_positive=True):
    """split() with a choice of which side is kept ('back')."""
    a, b = split(obj, axis, value)
    if keep_positive:
        return a, b
    a.name, b.name = b.name.replace('__front', '__back'), a.name.replace('__back', '__front')
    return b, a


def split_many(name, objs, axis='y', value=0.0):
    """Split a list of closed objects about a plane: straddling objects are cut
    (with section faces), the rest are grouped by side.  Returns (back, front)."""
    k = 'xyz'.index(axis)
    backs, fronts = [], []
    for o in objs:
        if o is None:
            continue
        cs = [v.co[k] for v in o.data.vertices]
        if min(cs) < value - 1e-5 and max(cs) > value + 1e-5:
            b, f = split(o, axis, value)
            backs.append(b)
            fronts.append(f)
        elif sum(cs) / len(cs) > value:
            backs.append(o)
        else:
            fronts.append(o)
    return (join(name + '__back', backs) if backs else None,
            join(name + '__front', fronts) if fronts else None)
