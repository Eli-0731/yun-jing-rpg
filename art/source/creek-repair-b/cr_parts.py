"""Shape helpers for creek-repair-b: nothing here is a plain cube or a plain cylinder.

rbox     subdivided box with rounded edges, low-frequency wobble and chipped corners (stones, planks)
rope     real twisted cord swept along a path; lash / xlash wrap it around poles
pole     bamboo culm with node bulges, a slight bend, an open cut top and a per-vertex 'bam' attribute
sheet    cloth or paper grid that can lose faces (torn edges) and carries its own 'cuv' attribute
log      lumpy round timber swept along a path
"""
import bmesh, math, random
from mathutils import Vector, Matrix, Euler, noise
from ti_core import S, mesh, _catmull


def set_attr_list(o, name, values):
    me = o.data
    at = me.attributes.get(name) or me.attributes.new(name, 'FLOAT_VECTOR', 'POINT')
    flat = []
    for v in values: flat.extend(v)
    at.data.foreach_set('vector', flat)


def set_float(o, name, fn):
    me = o.data
    at = me.attributes.get(name) or me.attributes.new(name, 'FLOAT', 'POINT')
    at.data.foreach_set('value', [fn(v.co) for v in me.vertices])


def _sharp(me, degrees=38):
    """Mark hard edges so chipped facets keep a crisp line while the rest shades smooth."""
    bm = bmesh.new(); bm.from_mesh(me)
    lim = math.radians(degrees); flags = []
    for e in bm.edges:
        flags.append(len(e.link_faces) != 2 or e.calc_face_angle(0.0) > lim)
    bm.free()
    at = me.attributes.get('sharp_edge') or me.attributes.new('sharp_edge', 'BOOLEAN', 'EDGE')
    at.data.foreach_set('value', flags)


def _n(v, freq, seed):
    return noise.noise(v * freq + Vector((seed * 3.17, seed * 1.73, seed * 2.39)))


def rbox(name, p, s, mat, r=.01, amp=0., freq=6., chips=0, hew=0, seed=0, div=.04, rot=(0, 0, 0), flat='', taper=None, skew=None, warp=None, sharp=38, **kw):
    """s = full size. flat: letters x/X/y/Y/z/Z keep that face inside its plane (mating faces, channel walls).
    taper = (sx, sy) scale of the top relative to the bottom. skew = (dx, dy) shift of the top.
    hew = number of chisel facets: planes nearly parallel to a face, so the stone reads cut rather than pillowed.
    warp(q) edits a local vertex in place (sloped tops)."""
    hx, hy, hz = s[0] / 2, s[1] / 2, s[2] / 2
    nx, ny, nz = (max(2, int(round(v / div))) for v in s)
    index, verts, faces = {}, [], []
    def vid(i, j, k):
        key = (i, j, k)
        if key not in index:
            index[key] = len(verts); verts.append(Vector((-hx + 2 * hx * i / nx, -hy + 2 * hy * j / ny, -hz + 2 * hz * k / nz)))
        return index[key]
    for j in range(ny):
        for k in range(nz):
            faces.append((vid(nx, j, k), vid(nx, j + 1, k), vid(nx, j + 1, k + 1), vid(nx, j, k + 1)))
            faces.append((vid(0, j, k), vid(0, j, k + 1), vid(0, j + 1, k + 1), vid(0, j + 1, k)))
    for i in range(nx):
        for k in range(nz):
            faces.append((vid(i, ny, k), vid(i, ny, k + 1), vid(i + 1, ny, k + 1), vid(i + 1, ny, k)))
            faces.append((vid(i, 0, k), vid(i + 1, 0, k), vid(i + 1, 0, k + 1), vid(i, 0, k + 1)))
    for i in range(nx):
        for j in range(ny):
            faces.append((vid(i, j, nz), vid(i + 1, j, nz), vid(i + 1, j + 1, nz), vid(i, j + 1, nz)))
            faces.append((vid(i, j, 0), vid(i, j + 1, 0), vid(i + 1, j + 1, 0), vid(i + 1, j, 0)))
    rr = min(r, hx * .9, hy * .9, hz * .9)
    planes = []
    R = random.Random(f'{name}:{seed}')
    for _ in range(chips):
        c = Vector((R.choice((-1, 1)) * (1 + R.random()), R.choice((-1, 1)) * (1 + R.random()), R.choice((-1, 1)) * (1 + R.random()))).normalized()
        corner = Vector((hx * (1 if c.x > 0 else -1), hy * (1 if c.y > 0 else -1), hz * (1 if c.z > 0 else -1)))
        planes.append((c, corner.dot(c) - R.uniform(.04, .17) * min(s)))
    for _ in range(hew):
        ax = R.randrange(3); sg = R.choice((-1, 1))
        if 'xyz'[ax] in flat and sg < 0 or 'XYZ'[ax] in flat and sg > 0: continue
        half = (hx, hy, hz)[ax]; tilt = .022 / max(max(hx, hy, hz), .05)
        c = Vector((R.uniform(-tilt, tilt), R.uniform(-tilt, tilt), R.uniform(-tilt, tilt))); c[ax] = sg
        c.normalize()
        planes.append((c, c[ax] * sg * half - R.uniform(.002, .012)))
    for v in verts:
        inner = Vector((max(-hx + rr, min(hx - rr, v.x)), max(-hy + rr, min(hy - rr, v.y)), max(-hz + rr, min(hz - rr, v.z))))
        d = v - inner
        n = d.normalized() if d.length > 1e-7 else Vector((0, 0, 1))
        q = inner + n * rr
        if amp:
            q += n * (_n(q, freq, seed) * amp + _n(q, freq * 3.1, seed + 1) * amp * .3)
        for c, off in planes:
            ex = q.dot(c) - off
            if ex > 0: q -= c * ex
        if taper or skew:
            t = (q.z + hz) / (2 * hz)
            if taper: q.x *= 1 + (taper[0] - 1) * t; q.y *= 1 + (taper[1] - 1) * t
            if skew: q.x += skew[0] * t; q.y += skew[1] * t
        if warp: warp(q)
        if 'x' in flat: q.x = max(q.x, -hx)
        if 'X' in flat: q.x = min(q.x, hx)
        if 'y' in flat: q.y = max(q.y, -hy)
        if 'Y' in flat: q.y = min(q.y, hy)
        if 'z' in flat: q.z = max(q.z, -hz)
        if 'Z' in flat: q.z = min(q.z, hz)
        v.xyz = q
    kw.setdefault('grain', 'x')
    o = mesh(name, [tuple(v) for v in verts], faces, mat, smooth=True, **kw)
    _sharp(o.data, sharp)
    o.matrix_world = S['M'][-1] @ Matrix.Translation(Vector(p)) @ Euler(rot).to_matrix().to_4x4()
    return o


def between(name, a, b, w, d, mat, **kw):
    """rbox timber running from a to b; w is the width across, d the depth. Its grain follows the run."""
    A, B = Vector(a), Vector(b); L = (B - A).length; ax = (B - A).normalized()
    q = Vector((1, 0, 0)).rotation_difference(ax)
    kw.setdefault('grain', 'x')
    return rbox(name, tuple((A + B) / 2), (L, w, d), mat, rot=tuple(q.to_euler()), **kw)


def rope(name, pts, r, mat, ply=3, tw=120., seg=9, step=None, amp=.17, curve=6, radius_fn=None, **kw):
    """Twisted cord: a ring with `ply` lobes that rotates along the path, capped at both ends."""
    path = _catmull(pts, curve) if len(pts) > 2 else [Vector(pts[0]), Vector(pts[1])]
    step = step or max(r * 1.5, .003)
    even = [path[0]]; left = step
    for a, b in zip(path, path[1:]):
        seglen = (b - a).length; t = 0.
        while seglen - t >= left and seglen > 0:
            t += left; even.append(a.lerp(b, t / seglen)); left = step
        left -= seglen - t
    if (even[-1] - path[-1]).length > step * .3: even.append(path[-1])
    t0 = (even[1] - even[0]).normalized()
    n = t0.cross(Vector((0, 0, 1)) if abs(t0.z) < .9 else Vector((1, 0, 0))).normalized()
    verts, faces = [], []; s = 0.; prev = t0; N = len(even)
    for i, p in enumerate(even):
        t = (even[min(i + 1, N - 1)] - even[max(i - 1, 0)]).normalized()
        n = (prev.rotation_difference(t) @ n).normalized(); prev = t
        b = t.cross(n)
        rad0 = r * (radius_fn(i / max(N - 1, 1)) if radius_fn else 1.)
        for j in range(seg):
            a = math.tau * j / seg
            rad = rad0 * (1 + amp * math.cos(ply * a + tw * s))
            verts.append(tuple(p + (n * math.cos(a) + b * math.sin(a)) * rad))
        s += step
    for i in range(N - 1):
        for j in range(seg):
            k = (j + 1) % seg
            faces.append((i * seg + j, i * seg + k, (i + 1) * seg + k, (i + 1) * seg + j))
    faces.append(tuple(range(seg - 1, -1, -1)))
    faces.append(tuple((N - 1) * seg + j for j in range(seg)))
    kw.setdefault('grain', tuple((even[-1] - even[0]).normalized()) if (even[-1] - even[0]).length > 1e-3 else 'z')
    return mesh(name, verts, faces, mat, smooth=True, **kw)


def _perp(a):
    a = Vector(a).normalized()
    u = a.cross(Vector((0, 0, 1)) if abs(a.z) < .9 else Vector((1, 0, 0))).normalized()
    return a, u, a.cross(u).normalized()


def helix(c, axis, R, span, turns, per_turn=14, phase=0.):
    a, u, v = _perp(axis); c = Vector(c); n = int(turns * per_turn); out = []
    for i in range(n + 1):
        t = i / n; ang = phase + t * turns * math.tau
        out.append(tuple(c + a * (span * (t - .5)) + (u * math.cos(ang) + v * math.sin(ang)) * R))
    return out


def lash(name, c, axis, R, span, r, mat, turns=5, **kw):
    """Tight wrap around a pole."""
    kw.setdefault('detail', 1)
    return rope(name, helix(c, axis, R + r * .8, span, turns), r, mat, curve=2, **kw)


def xlash(name, c, a1, R1, a2, R2, r, mat, tail=None, **kw):
    """Crossing lashing: wraps on both poles either side of the joint plus two diagonal figure-eight loops."""
    c = Vector(c); a1 = Vector(a1).normalized(); a2 = Vector(a2).normalized()
    kw.setdefault('detail', 1)
    w = r * 2.1
    for sign in (-1, 1):
        lash(name + '_A', c + a1 * sign * (R2 + w * 1.3), a1, R1, w * 2.2, r, mat, turns=2.5, **kw)
        lash(name + '_B', c + a2 * sign * (R1 + w * 1.1), a2, R2, w * 1.8, r, mat, turns=2, **kw)
    n = a1.cross(a2).normalized(); L = math.hypot(R1, R2) * 1.1 + r; Rf = max(R1, R2) * 1.02 + r
    for d, ph in (((a1 + a2).normalized(), 0.), ((a1 - a2).normalized(), .6)):
        pts = []
        for i in range(25):
            t = i / 24 * math.tau + ph
            pts.append(tuple(c + d * (L * math.cos(t)) + n * (Rf * math.sin(t))))
        rope(name + '_X', pts, r, mat, curve=2, **kw)
    if tail:
        e0 = c + n * (Rf + r * .4)
        rope(name + '_Tail', [tuple(e0), tuple(e0 + Vector(tail) * .4 + n * .006), tuple(e0 + Vector(tail))], r * .85, mat,
             radius_fn=lambda t: 1 - .35 * t * t, **kw)


def pole(name, a, b, r0, r1, mat, node_gap=.36, bend=0., seed=0, cut=0., seg=20, **kw):
    """Bamboo culm from a to b. 'bam' attribute: x distance to the nearest node (m), y metres along, z per-pole tone."""
    A, B = Vector(a), Vector(b); L = (B - A).length
    ax, u, v = _perp(B - A)
    R = random.Random(f'{name}:{seed}')
    ang = R.uniform(0, 6.3); side = (u * math.cos(ang) + v * math.sin(ang)).normalized()
    nodes = []; d = R.uniform(.05, node_gap * .7)
    while d < L:
        nodes.append(d); d += node_gap * R.uniform(.9, 1.1)
    st = {0., L}
    for z in nodes:
        for dz in (-.03, -.012, -.005, 0, .005, .012, .03):
            if 0 < z + dz < L: st.add(round(z + dz, 4))
    d = 0.
    while d < L: st.add(round(d, 3)); d += .1
    st = sorted(st); merged = [st[0]]
    for z in st[1:]:
        if z - merged[-1] > .003: merged.append(z)
    if merged[-1] != L: merged[-1] = L
    st = merged; verts, faces, bam = [], [], []; tone = R.random()
    def nearest(z): return min((abs(z - n) for n in nodes), default=1.)
    def centre(z): return A + ax * z + side * (bend * math.sin(math.pi * z / L))
    for z in st:
        dn = nearest(z); rad = r0 + (r1 - r0) * z / L
        rad *= 1 + .085 * math.exp(-(dn / .01) ** 2) + .025 * math.exp(-(dn / .05) ** 2)
        c = centre(z)
        for j in range(seg):
            t = math.tau * j / seg; dirn = u * math.cos(t) + v * math.sin(t)
            q = c + dirn * rad * (1 + .012 * math.sin(3 * t + seed))
            if cut and z == L: q += ax * (cut * math.cos(t) * r1)
            verts.append(tuple(q)); bam.append((dn, z, tone))
    n = len(st)
    for i in range(n - 1):
        for j in range(seg):
            k = (j + 1) % seg
            faces.append((i * seg + j, i * seg + k, (i + 1) * seg + k, (i + 1) * seg + j))
    # open top: the wall folds inward and runs down, then a plug
    top = centre(L); wall = max(r1 * .2, .006); base = (n - 1) * seg
    for depth_i, (rr, dz) in enumerate(((r1 - wall, 0.), (r1 - wall, -.09))):
        for j in range(seg):
            t = math.tau * j / seg
            q = top + (u * math.cos(t) + v * math.sin(t)) * rr + ax * dz
            if cut and depth_i == 0: q += ax * (cut * math.cos(t) * rr)
            verts.append(tuple(q)); bam.append((1., L, tone))
    for depth_i in range(2):
        for j in range(seg):
            k = (j + 1) % seg
            r_a = base + depth_i * seg; r_b = base + (depth_i + 1) * seg
            faces.append((r_a + j, r_a + k, r_b + k, r_b + j))
    faces.append(tuple(base + 2 * seg + j for j in range(seg)))
    faces.append(tuple(range(seg - 1, -1, -1)))
    o = mesh(name, verts, faces, mat, smooth=True, grain=tuple(ax), **kw)
    set_attr_list(o, 'bam', bam)
    return o


def sheet(name, nu, nv, fn, mat, solid=.004, keep=None, **kw):
    """Grid fn(u, v) -> xyz, optional keep(u, v) -> bool dropping faces to tear the edge. 'cuv' holds u, v."""
    faces, used = [], {}
    pts = {}
    for j in range(nv):
        for i in range(nu):
            uu, vv = (i + .5) / nu, (j + .5) / nv
            if keep and not keep(uu, vv): continue
            q = []
            for a, b in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)):
                if (a, b) not in used:
                    used[(a, b)] = len(pts); pts[(a, b)] = fn(a / nu, b / nv)
                q.append(used[(a, b)])
            faces.append(tuple(q))
    ordered = sorted(used, key=used.get)
    verts = [tuple(pts[k]) for k in ordered]
    o = mesh(name, verts, faces, mat, smooth=True, solid=solid, **kw)
    set_attr_list(o, 'cuv', [(a / nu, b / nv, 0.) for a, b in ordered])
    return o


def log(name, pts, r, mat, seg=12, lump=.1, seed=0, **kw):
    """Round timber along a path with an irregular section."""
    def rf(t): return 1 + lump * math.sin(t * 17 + seed) * .6 + lump * math.sin(t * 5.3 + seed * 2)
    kw.setdefault('step', r * .8)
    return rope(name, pts, r, mat, ply=2, tw=0., seg=seg, amp=lump * .5, radius_fn=rf, **kw)


def tuft(name, c, r, mat, seed=0, **kw):
    """Low moss cushion, flattened and lumpy; sits in a joint."""
    kw.setdefault('detail', 2)
    return rbox(name, c, (r * 2, r * 1.5, r * .55), mat, r=r * .26, amp=r * .3, freq=1 / r * 1.1, seed=seed, div=r * .42, sharp=80, **kw)
