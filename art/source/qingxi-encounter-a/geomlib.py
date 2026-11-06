"""Geometry helpers (copied from art/source/qingxi-training-yard-v1/yardlib.py, PR #38, same author).

Blender convention: metres, Z-up, asset front faces -Y, origin at ground centre.
Every generator writes explicit UVs so textures keep a consistent texel density.
"""
import math
import bpy
import numpy as np
from mathutils import Vector, Matrix

TEXEL = 1.0  # one texture repeat per metre unless a generator overrides it


# ---------------------------------------------------------------- mesh core
def make_mesh(name, verts, faces, uvs=None, mats=None, face_mats=None, coll=None,
              smooth_angle=None, node=None):
    """Create an object. `uvs` is per-vertex (len == verts) or per-face-corner list."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.update()
    uv = me.uv_layers.new(name='UVMap')
    if uvs is None:
        box_uv(me)
    elif len(uvs) == len(verts):
        for loop in me.loops:
            uv.data[loop.index].uv = uvs[loop.vertex_index]
    else:
        flat = [c for f in uvs for c in f]
        for i, loop in enumerate(me.loops):
            uv.data[i].uv = flat[i]
    ob = bpy.data.objects.new(name, me)
    for m in (mats or []):
        me.materials.append(m)
    if face_mats is not None:
        for p, mi in zip(me.polygons, face_mats):
            p.material_index = mi
    if smooth_angle is not None:
        me.shade_smooth()
        me.set_sharp_from_angle(angle=math.radians(smooth_angle))
    if node:
        ob['node'] = node
    (coll or bpy.context.scene.collection).objects.link(ob)
    return ob


def box_uv(me, scale=TEXEL, offset=(0.0, 0.0)):
    uv = me.uv_layers.active
    for p in me.polygons:
        n = p.normal
        axis = max(range(3), key=lambda j: abs(n[j]))
        # keep the long grain direction (Z for walls, X for floors) on V
        a, b = {0: (1, 2), 1: (0, 2), 2: (0, 1)}[axis]
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = (co[a] * scale + offset[0], co[b] * scale + offset[1])


def bevel(ob, width=0.012, segments=2, angle=40):
    m = ob.modifiers.new('Bevel', 'BEVEL')
    m.width = width
    m.segments = segments
    m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(angle)
    m.harden_normals = False
    return ob


def place(ob, loc=(0, 0, 0), rot=(0, 0, 0), scale=None):
    ob.location = loc
    ob.rotation_euler = rot
    if scale:
        ob.scale = scale
    return ob


# ---------------------------------------------------------------- primitives
def grid_surface(name, fn, nu, nv, coll, mats, uscale=1.0, vscale=1.0, closed_u=False,
                 smooth_angle=60, node=None, flip=False):
    """fn(u, v) -> (x, y, z) with u, v in [0, 1]."""
    verts, uvs, faces = [], [], []
    for j in range(nv + 1):
        for i in range(nu + 1):
            u, v = i / nu, j / nv
            verts.append(fn(u, v))
            uvs.append((u * uscale, v * vscale))
    w = nu + 1
    for j in range(nv):
        for i in range(nu):
            a, b, c, d = j * w + i, j * w + i + 1, (j + 1) * w + i + 1, (j + 1) * w + i
            faces.append((a, d, c, b) if flip else (a, b, c, d))
    return make_mesh(name, verts, faces, uvs, mats, coll=coll, smooth_angle=smooth_angle, node=node)


def lathe(name, profile, seg, coll, mats, cap_bottom=True, cap_top=True, smooth_angle=50,
          vscale=None, node=None, start=0.0):
    """profile: list of (radius, z) from bottom to top. Returns closed solid of revolution.
    A zero radius at either end becomes the cap centre instead of a collapsed ring."""
    z_bot = z_top = None
    if profile[0][0] < 1e-4:
        z_bot, profile = profile[0][1], profile[1:]
    if profile[-1][0] < 1e-4:
        z_top, profile = profile[-1][1], profile[:-1]
    lengths = [0.0]
    for (r0, z0), (r1, z1) in zip(profile, profile[1:]):
        lengths.append(lengths[-1] + math.hypot(r1 - r0, z1 - z0))
    circ = 2 * math.pi * max(r for r, _ in profile)
    verts, uvs, faces = [], [], []
    for j, (r, z) in enumerate(profile):
        for i in range(seg + 1):
            a = start + 2 * math.pi * i / seg
            verts.append((r * math.cos(a), r * math.sin(a), z))
            uvs.append((i / seg * circ, (lengths[j] if vscale is None else lengths[j] * vscale)))
    w = seg + 1
    for j in range(len(profile) - 1):
        for i in range(seg):
            faces.append((j * w + i, j * w + i + 1, (j + 1) * w + i + 1, (j + 1) * w + i))
    corner = [[uvs[v] for v in f] for f in faces]
    if cap_bottom:
        _cap(verts, faces, corner, [verts[i] for i in range(seg)], (0, 0, profile[0][1] if z_bot is None else z_bot), True)
    if cap_top:
        base = (len(profile) - 1) * w
        _cap(verts, faces, corner, [verts[base + i] for i in range(seg)],
             (0, 0, profile[-1][1] if z_top is None else z_top), False)
    return make_mesh(name, verts, faces, corner, mats, coll=coll, smooth_angle=smooth_angle, node=node)


def _cap(verts, faces, corner, ring, centre, flip):
    """Fan cap with its own vertices and planar UVs (avoids zero-area UV triangles)."""
    c = Vector(centre)
    rmax = max((Vector(p) - c).length for p in ring) or 1.0
    ref = (Vector(ring[0]) - c).normalized()
    nrm = (Vector(ring[1]) - c).cross(Vector(ring[0]) - c).normalized()
    bit = nrm.cross(ref)
    ci = len(verts)
    verts.append(tuple(c))
    start = len(verts)
    verts.extend(tuple(p) for p in ring)
    def uv(p):
        d = Vector(p) - c
        return (0.5 + 0.5 * d.dot(ref) / rmax * min(rmax * 4, 1), 0.5 + 0.5 * d.dot(bit) / rmax * min(rmax * 4, 1))
    n = len(ring)
    for i in range(n):
        f = (ci, start + (i + 1) % n, start + i) if flip else (ci, start + i, start + (i + 1) % n)
        faces.append(f)
        corner.append([uv(verts[k]) for k in f])


def _frames(points):
    """Parallel-transport frames along a polyline."""
    pts = [Vector(p) for p in points]
    tangents = []
    for i in range(len(pts)):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        tangents.append((b - a).normalized())
    t0 = tangents[0]
    ref = Vector((0, 0, 1)) if abs(t0.z) < 0.9 else Vector((1, 0, 0))
    n = t0.cross(ref).normalized()
    frames = []
    for t in tangents:
        n = (n - t * n.dot(t)).normalized()
        frames.append((t, n, t.cross(n).normalized()))
    return pts, frames


def tube(name, points, radius, seg, coll, mats, caps=True, smooth_angle=70, node=None,
         arc=None, vscale=1.0):
    """Sweep a circle (or arc range in radians) along points. radius may be callable(t)."""
    pts, frames = _frames(points)
    lengths = [0.0]
    for a, b in zip(pts, pts[1:]):
        lengths.append(lengths[-1] + (b - a).length)
    total = lengths[-1] or 1.0
    a0, a1 = arc if arc else (0.0, 2 * math.pi)
    verts, uvs, faces = [], [], []
    for k, (p, (t, n, b)) in enumerate(zip(pts, frames)):
        r = radius(lengths[k] / total) if callable(radius) else radius
        for i in range(seg + 1):
            a = a0 + (a1 - a0) * i / seg
            verts.append(tuple(p + (n * math.cos(a) + b * math.sin(a)) * r))
            uvs.append((i / seg * (a1 - a0) * max(r, 0.02), lengths[k] * vscale))
    w = seg + 1
    for k in range(len(pts) - 1):
        for i in range(seg):
            faces.append((k * w + i, k * w + i + 1, (k + 1) * w + i + 1, (k + 1) * w + i))
    corner = [[uvs[v] for v in f] for f in faces]
    if caps and not arc:
        for k, flip in ((0, True), (len(pts) - 1, False)):
            ring = [verts[k * w + i] for i in range(seg)]
            _cap(verts, faces, corner, ring, tuple(pts[k]), flip)
    return make_mesh(name, verts, faces, corner, mats, coll=coll, smooth_angle=smooth_angle, node=node)


def helix(radius, z0, z1, turns, steps_per_turn=20, phase=0.0, cx=0.0, cy=0.0):
    n = max(2, int(turns * steps_per_turn))
    return [(cx + radius * math.cos(phase + 2 * math.pi * turns * i / n),
             cy + radius * math.sin(phase + 2 * math.pi * turns * i / n),
             z0 + (z1 - z0) * i / n) for i in range(n + 1)]


def prism(name, poly, depth, coll, mats, plane='XZ', offset=0.0, node=None, uv_scale=TEXEL):
    """Extrude a 2D polygon (counter-clockwise) by depth. plane picks the 2D axes."""
    n = len(poly)
    def to3(p, d):
        a, b = p
        if plane == 'XZ':
            return (a, offset + d, b)
        if plane == 'YZ':
            return (offset + d, a, b)
        return (a, b, offset + d)  # XY
    h = depth / 2
    verts = [to3(p, -h) for p in poly] + [to3(p, h) for p in poly]
    faces = [tuple(range(n))[::-1], tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    ob = make_mesh(name, verts, faces, None, mats, coll=coll, smooth_angle=30, node=node)
    recalc_normals(ob)
    box_uv(ob.data, uv_scale)
    return ob


def recalc_normals(ob):
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()


def block(name, size, loc, coll, mats, bev=0.012, rot=(0, 0, 0), node=None, taper=0.0):
    """Axis-aligned box centred at loc; taper shrinks the bottom face (for dou blocks)."""
    sx, sy, sz = (s / 2 for s in size)
    bx, by = sx * (1 - taper), sy * (1 - taper)
    verts = [(-bx, -by, -sz), (bx, -by, -sz), (bx, by, -sz), (-bx, by, -sz),
             (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    ob = make_mesh(name, verts, faces, None, mats, coll=coll, smooth_angle=30, node=node)
    place(ob, loc, rot)
    # box UVs in world-ish metres so stacked planks do not repeat identically
    box_uv(ob.data, TEXEL, offset=(loc[0] * 0.37 + loc[2] * 0.21, loc[1] * 0.53))
    if bev:
        bevel(ob, bev)
    return ob


def beam_between(name, p0, p1, w, h, coll, mats, bev=0.012, node=None):
    """Rectangular timber from p0 to p1 (centre line), width w, height h."""
    a, b = Vector(p0), Vector(p1)
    d = b - a
    ob = block(name, (d.length, w, h), (0, 0, 0), coll, mats, bev, node=node)
    ob.data.transform(Matrix.Identity(4))
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = Vector((1, 0, 0)).rotation_difference(d.normalized())
    ob.location = (a + b) / 2
    return ob


# ---------------------------------------------------------------- textures
def _spectrum_noise(n, beta, seed, aniso=(1.0, 1.0)):
    """Tileable fractal noise via inverse FFT, normalised to [0, 1]."""
    rng = np.random.default_rng(seed)
    fx = np.fft.fftfreq(n)[None, :] * n * aniso[0]
    fy = np.fft.fftfreq(n)[:, None] * n * aniso[1]
    f = np.sqrt(fx ** 2 + fy ** 2)
    f[0, 0] = 1
    amp = 1 / f ** beta
    amp[0, 0] = 0
    phase = rng.random((n, n)) * 2 * np.pi
    field = np.real(np.fft.ifft2(amp * np.exp(1j * phase)))
    return (field - field.min()) / (field.max() - field.min())


def noise(n, beta=1.8, seed=0, aniso=(1.0, 1.0)):
    return _spectrum_noise(n, beta, seed, aniso)


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def mix(a, b, t):
    t = t[..., None] if np.ndim(t) == 2 else t
    return np.asarray(a) * (1 - t) + np.asarray(b) * t


def normal_from_height(h, strength):
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * strength
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * strength
    nrm = np.stack((-dx, -dy, np.ones_like(h)), -1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    return nrm * 0.5 + 0.5
