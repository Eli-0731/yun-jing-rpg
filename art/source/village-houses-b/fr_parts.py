"""FR ancient-forest root kit (work pack B-104h part 2): shared geometry and palette.

Coordinates: Blender Z-up, 1 unit = 1 m, front of every piece = -Y.

sweep()    a root: a swept section along a smoothed path, the section flattened towards the ground (plank roots), deep bark
           fissures that run along the root and spiral slowly round it (the elder-world-tree-hero-v1 root look), shallower on the
           top where the bark is worn smooth. Writes the per-vertex 'bark' attribute (x = metres along, y = metres round,
           z = fissure 0..1) that the bark shader reads.
Arc        the FR01 wall sections are laid along a plan arc: (u, v) = (metres along the wall, metres behind its centre line).
mound()    packed earth between the roots: a closed heightfield slab whose bottom is z = 0.
pebble()   a rounded, flattened forest stone.
fern / moss_patch / grass_tuft / snap: the SG kit's small-growth helpers (same look as the stair kit beside it).
"""
import bpy, bmesh, math, random
import numpy as np
from mathutils import Vector, Matrix, noise
from ti_core import S, mesh, surface
import ti_mats as tm
import cr_mats as cm
import fr_mats as fm
from cr_parts import sheet, set_attr_list

Z = Vector((0, 0, 1))


# ------------------------------------------------------------------ palette
def palette():
    P = {}
    P['bark'] = [fm.bark(f'Root_Bark_{i}', tone=t, moss=mo) for i, (t, mo) in enumerate(((1.18, 1.2), (1.04, 1.35), (1.28, 1.05)))]
    P['tip'] = fm.root_tip('Root_Tip')
    P['earth'] = fm.forest_earth('Root_Earth')
    P['stone'] = [cm.stone(f'Forest_Stone_{i}', light=l, dark=d, ochre=(.24, .2, .14), moss=1.6, lichen=.7, crack=.35)
                  for i, (l, d) in enumerate((((.12, .115, .105), (.05, .047, .043)), ((.11, .112, .11), (.045, .047, .046))))]
    P['moss'] = cm.moss_tuft('Root_Moss', soft=True)
    P['fern'] = cm.fern('Root_Fern')
    P['grass'] = cm.weed_leaf('Forest_Grass', (.035, .055, .016), (.12, .16, .04), (.24, .25, .07))
    P['litter'] = cm.weed_leaf('Leaf_Litter', (.06, .042, .02), (.15, .095, .04), (.22, .15, .065))
    return P


# ------------------------------------------------------------------ curves
def _crspline(pts, n):
    """Catmull-Rom through pts (any dimension), n samples per span."""
    P = [np.array(p, float) for p in pts]; P = [P[0] * 2 - P[1]] + P + [P[-1] * 2 - P[-2]]; out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            out.append(.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2]); return np.array(out)


def resample(pts, radii, step):
    """Smooth path through pts with radii, resampled every step metres: (points, radii, arc length at each)."""
    d = _crspline([tuple(p) + (r,) for p, r in zip(pts, radii)], 16)
    seg = np.linalg.norm(np.diff(d[:, :3], axis=0), axis=1); s = np.concatenate([[0.], np.cumsum(seg)])
    n = max(2, int(math.ceil(s[-1] / step)) + 1); t = np.linspace(0., s[-1], n)
    out = np.stack([np.interp(t, s, d[:, k]) for k in range(4)], 1)
    return [Vector(q[:3]) for q in out], [max(.002, q[3]) for q in out], list(t)


def sweep(name, pts, radii, mat, step=.07, aspect=1., fiss=.24, twist=.25, seed=0, plates=2.8, worn=.6, lump=.09, nring=None,
          cap=True, tip=None, ground=.004, crack=.32, **kw):
    """A root along pts. aspect < 1 flattens the section vertically (plank roots), > 1 makes it taller than wide.
    fiss: fissure depth as a share of the radius. twist: radians per metre the fissures turn round the root.
    plates: how many bark plates round a 1 m girth. worn: how much shallower the fissures are on the upper side.
    tip: (material, length) — the last length metres get that material (pale exposed root tips)."""
    C, Rr, Sv = resample(pts, radii, step)
    n = len(C); rmax = max(Rr)
    nv = nring or max(8, min(36, int(round(2 * math.pi * rmax / .055))))
    T = []
    for i in range(n):
        a, b = C[max(0, i - 1)], C[min(n - 1, i + 1)]
        T.append((b - a).normalized())
    # parallel-transport frame from a start normal as close to world up as the tangent allows
    N0 = Z - Z.dot(T[0]) * T[0]
    N0 = N0.normalized() if N0.length > .2 else T[0].orthogonal().normalized()
    Ns = [N0]
    for i in range(1, n):
        ax = T[i - 1].cross(T[i])
        if ax.length < 1e-8: Ns.append(Ns[-1].copy()); continue
        ang = math.asin(max(-1., min(1., ax.length))); q = Matrix.Rotation(ang, 3, ax.normalized())
        nn = q @ Ns[-1]; nn = (nn - nn.dot(T[i]) * T[i]).normalized(); Ns.append(nn)
    verts, attr = [], []
    R = random.Random(seed)
    so = Vector((R.uniform(-50, 50), R.uniform(-50, 50), R.uniform(-50, 50)))
    for i in range(n):
        t, N = T[i], Ns[i]; B = t.cross(N).normalized(); r = Rr[i]; s = Sv[i]
        up = Z - Z.dot(t) * t; w = up.length; up = up.normalized() if w > 1e-6 else up
        k_up = max(0., min(1., (w - .25) / .5))       # aspect only where the root runs roughly level
        rho = max(.6, plates * r)                      # noise-space radius: about plates fissures per metre of girth
        for k in range(nv):
            th = 2 * math.pi * k / nv
            d = N * math.cos(th) + B * math.sin(th)
            if k_up: d = d + (aspect - 1) * k_up * d.dot(up) * up
            ph = th + twist * s
            q = so + Vector((math.cos(ph) * rho, math.sin(ph) * rho, s * .42))
            F = max(0., 1. - abs(noise.noise(q)) / crack) ** 1.3     # a V-shaped crack where the noise crosses zero
            facing = max(0., d.normalized().dot(Z))
            depth = fiss * F * (1. - worn * facing ** 1.5)
            bump = lump * noise.noise(so * .7 + Vector((math.cos(th) * 1.3, math.sin(th) * 1.3, s * .55)))
            fine = .018 * noise.noise(q * 3.1)
            rr = r * (1. + bump + fine - depth)
            verts.append(tuple(C[i] + d * rr)); attr.append((s, th * r, F * (1. - worn * facing ** 1.5)))
    faces = []
    for i in range(n - 1):
        for k in range(nv):
            a = i * nv + k; b = i * nv + (k + 1) % nv
            faces.append((a, b, b + nv, a + nv))
    if cap:
        for i, sgn in ((0, -1), (n - 1, 1)):
            verts.append(tuple(C[i] + T[i] * sgn * Rr[i] * .2)); attr.append((Sv[i], 0., 0.)); c = len(verts) - 1
            ring = [i * nv + k for k in range(nv)]
            for k in range(nv):
                a, b = ring[k], ring[(k + 1) % nv]
                faces.append((b, a, c) if sgn < 0 else (a, b, c))
    o = mesh(name, verts, faces, mat, smooth=True, **{'grain': 'z', **kw})
    set_attr_list(o, 'bark', attr)
    if tip:
        tmat, L = tip; o.data.materials.append(tmat); total = Sv[-1]
        for p in o.data.polygons:
            if p.vertices[0] < n * nv and Sv[min(n - 1, p.vertices[0] // nv)] > total - L: p.material_index = 1
    bm = bmesh.new(); bm.from_mesh(o.data)
    if ground is not None:     # each root cut at its own height (2.1 mm apart): two cut faces in one plane would z-fight in QA, even buried
        S['cut_n'] = S.get('cut_n', -1) + 1; ground = ground + (S['cut_n'] % 24) * .0021
    if ground is not None and min(v[2] for v in verts) < ground:
        # the root goes into the ground at full size: cut it off just above z = 0 and close the cut (hidden in the earth)
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, ground), plane_no=(0, 0, 1), clear_inner=True)
        edges = [e for e in bm.edges if e.is_boundary]
        if edges: bmesh.ops.holes_fill(bm, edges=edges, sides=0)
        big = [f for f in bm.faces if len(f.verts) > 4]
        if big: bmesh.ops.triangulate(bm, faces=big)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    o['root_axis'] = [tuple(c) for c in C[::max(1, n // 40)]]
    return o


# ------------------------------------------------------------------ plan arc for the wall sections
class Arc:
    """Plan arc: chord L along X, the two end tangents turned +-half_turn from X, bulging towards +Y. (u, v) -> (x, y)."""
    def __init__(self, L=6., half_turn=math.radians(10)):
        self.L, self.ht = L, half_turn
        self.R = (L / 2) / math.sin(half_turn); self.sag = self.R * (1 - math.cos(half_turn))
        self.y_mid = self.sag / 2; self.C = Vector((0, self.y_mid - self.R, 0))
        self.U = self.R * half_turn                  # half the arc length

    def xy(self, u, v):
        ph = u / self.R
        return Vector((self.C.x + (self.R + v) * math.sin(ph), self.C.y + (self.R + v) * math.cos(ph), 0.))

    def p(self, u, v, z): q = self.xy(u, v); q.z = z; return q

    def end(self, side):
        """Joint point at the arc end (side -1 west, +1 east) on the centre line, and its outward heading (radians about Z)."""
        u = side * self.U; q = self.xy(u, 0.)
        return q, -u / self.R


def mound(name, hfn, x0, x1, y0, y1, mat, nx=60, ny=22, mapfn=None, **kw):
    """Closed earth slab: top z = hfn(a, b) (>= .004), flat bottom at z = 0, vertical rim faces round the outline.
    (a, b) runs over [x0, x1] x [y0, y1]; mapfn(a, b) -> plan (x, y) lays the grid along something else (the FR01 arc)."""
    cu = nx + 1; verts = []; plan = []
    for j in range(ny + 1):
        for i in range(cu):
            a = x0 + (x1 - x0) * i / nx; b = y0 + (y1 - y0) * j / ny
            x, y = (mapfn(a, b)[:2] if mapfn else (a, b))
            verts.append((x, y, max(.004, hfn(a, b)))); plan.append((x, y))
    n = len(verts)
    for x, y in plan: verts.append((x, y, 0.))
    faces = []
    for j in range(ny):
        for i in range(nx):
            a = j * cu + i
            faces.append((a, a + 1, a + 1 + cu, a + cu)); faces.append((n + a, n + a + cu, n + a + 1 + cu, n + a + 1))
    ring = [i for i in range(cu)] + [j * cu + nx for j in range(1, ny + 1)] + [ny * cu + i for i in range(nx - 1, -1, -1)] + [j * cu for j in range(ny - 1, 0, -1)]
    for k in range(len(ring)):
        a, b = ring[k], ring[(k + 1) % len(ring)]
        faces.append((a, b, n + b, n + a))
    o = mesh(name, verts, faces, mat, smooth=True, **{'grain': 'z', **kw})
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    return o


def pebble(name, c, size, mat, seed=0, flat=.6, seg=14, ring=8, **kw):
    """A rounded forest stone, flattened, lumpy, its bottom sunk into what it sits on."""
    R = random.Random(seed); so = Vector((R.uniform(-40, 40), R.uniform(-40, 40), seed * .37))
    sx, sy, sz = size * R.uniform(.85, 1.15), size * R.uniform(.7, 1.), size * flat
    rot = R.uniform(0, math.tau); cs, sn = math.cos(rot), math.sin(rot)
    verts = [(c[0], c[1], c[2] - sz)]
    for j in range(1, ring):
        ph = math.pi * j / ring - math.pi / 2
        for i in range(seg):
            th = math.tau * i / seg; d = Vector((math.cos(ph) * math.cos(th), math.cos(ph) * math.sin(th), math.sin(ph)))
            k = 1 + .14 * noise.noise(so + d * 1.6) + .05 * noise.noise(so + d * 4.)
            x, y = d.x * sx * k, d.y * sy * k
            verts.append((c[0] + x * cs - y * sn, c[1] + x * sn + y * cs, c[2] + d.z * sz * k))
    verts.append((c[0], c[1], c[2] + sz))
    faces = []
    for i in range(seg): faces.append((0, 1 + (i + 1) % seg, 1 + i))
    for j in range(ring - 2):
        for i in range(seg):
            a = 1 + j * seg + i; b = 1 + j * seg + (i + 1) % seg
            faces.append((a, b, b + seg, a + seg))
    top = len(verts) - 1; base = 1 + (ring - 2) * seg
    for i in range(seg): faces.append((base + i, base + (i + 1) % seg, top))
    return mesh(name, verts, faces, mat, smooth=True, **{'grain': 'z', **kw})


# ------------------------------------------------------------------ small growth (sg_parts helpers, same look as the stair kit)
def grass_tuft(name, c, n, h, mat, R, lean=.3, detail=2, spread=.05):
    c = Vector(c)
    for b in range(n):
        a = R.uniform(0, math.tau); L = h * R.uniform(.55, 1.); wid = R.uniform(.011, .019)
        base = c + Vector((math.cos(a), math.sin(a), 0)) * R.uniform(0, spread) - Vector((0, 0, .01))
        bend = R.uniform(.15, lean); turn = a + R.uniform(-.5, .5); side = Vector((-math.sin(turn), math.cos(turn), 0))
        def fn(u, v, base=base, L=L, wid=wid, bend=bend, turn=turn, side=side):
            out = Vector((math.cos(turn), math.sin(turn), 0))
            p = base + out * (L * bend * v * v) + Vector((0, 0, L * (v - .35 * bend * v * v)))
            return tuple(p + side * ((u - .5) * 2 * wid * (1 - v * .85)))
        sheet(name, 1, 3, fn, mat, solid=.0012, rim=False, detail=detail, grain='z')


def fern(name, q, mat, R, n=7, L=.24, out=(0, -1, 0), detail=2, up_bias=0., spread=1.2):
    """Fronds fanned evenly over +-spread round out (jittered), each from its own point 1-2 cm out from the clump centre and a few
    mm higher or lower, so no two fronds start in one plane."""
    q = Vector(q); o = Vector(out).normalized(); a0 = math.atan2(o.y, o.x)
    for b in range(n):
        a = a0 + spread * (-1 + 2 * (b + .5) / n) + R.uniform(-.3, .3) * spread / n
        up = R.uniform(-.1, .7) + up_bias; Lb = L * R.uniform(.6, 1.)
        dirv = Vector((math.cos(a), math.sin(a), 0)); side = Vector((-dirv.y, dirv.x, 0))
        q0 = q + dirv * R.uniform(.01, .02) + Vector((0, 0, (b % 3 - 1) * .004))
        def fn(u, v, dirv=dirv, side=side, Lb=Lb, up=up, q0=q0):
            p = q0 + dirv * (Lb * v) + Vector((0, 0, Lb * (up * v - .55 * v * v)))
            w = .035 * (Lb / .24) ** .5 * math.sin(math.pi * min(v * 1.1, 1.))
            return tuple(p + side * ((u - .5) * 2 * w))
        sheet(name, 2, 6, fn, mat, solid=.001, detail=detail, grain='z')


def moss_patch(name, q, n, r, mat, seed=0, flat=1., snap_each=False, **kw):
    """Thin broken colonies hugging a surface (n = outward normal); each colony re-snapped onto what it covers."""
    n = Vector(n).normalized(); a = n.cross(Vector((0, 0, 1)) if abs(n.z) < .9 else Vector((1, 0, 0))).normalized(); b = n.cross(a); q = Vector(q)
    kw.setdefault('detail', 2); R = random.Random(seed * 13 + 5)
    for k in range(3):
        rk = r * (.66 if k == 0 else R.uniform(.26, .4)); off = 0 if k == 0 else r * R.uniform(.55, .85); turn = R.uniform(0, math.tau); s_ = seed + k * 3.7
        c = q + a * (math.cos(turn) * off * 1.3) + b * (math.sin(turn) * off * .8); nn = n
        if snap_each:
            hit = snap(tuple(c + n * .25), tuple(-n))
            if hit is None or hit[1].dot(n) < .7: continue
            c, nn = hit[0], hit[1]
        aa = nn.cross(Vector((0, 0, 1)) if abs(nn.z) < .9 else Vector((1, 0, 0))).normalized(); bb = nn.cross(aa)
        def fn(u, v, c=c, rk=rk, s_=s_, nn=nn, aa=aa, bb=bb):
            t = u * math.tau; cx, cy = math.cos(t), math.sin(t)
            e = rk * v * (.72 + .75 * noise.noise(Vector((cx * 1.2 + s_, cy * 1.2, s_ * .3))) + .28 * noise.noise(Vector((cx * 3.4 + s_, cy * 3.4, s_))))
            h = flat * (rk * .09 * (1 - v * v) ** .5)
            p = c + aa * (cx * e * 1.3) + bb * (cy * e * .8) + nn * (h - .006 * (1 - (1 - v * v) ** .5) - rk * .02)
            return (p.x, p.y, max(p.z, .003))
        surface(name, 16 if k == 0 else 8, 3 if k == 0 else 2, fn, mat, closed_u=True, **{**kw, 'detail': kw['detail']})


def snap(origin, direction):
    """First surface hit from origin along direction (location, normal) among the parts built so far, or None."""
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    ok, loc, nrm, *_ = bpy.context.scene.ray_cast(dg, Vector(origin), Vector(direction).normalized())
    return (loc, nrm) if ok else None


def hull_loft(V, F, sections):
    """Collision: a closed loft through convex sections (each a list of (x, y, z), same count, in order round the section)."""
    base = len(V); m = len(sections[0])
    for sec in sections: V.extend(sec)
    for i in range(len(sections) - 1):
        for k in range(m):
            a = base + i * m + k; b = base + i * m + (k + 1) % m
            F.append((a, b, b + m, a + m))
    F.append(tuple(base + k for k in range(m))[::-1]); F.append(tuple(base + (len(sections) - 1) * m + k for k in range(m)))
