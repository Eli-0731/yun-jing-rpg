"""FP forest-path kit (work pack B 11/08): the shared path section and the small growth along it.

Coordinates: Blender Z-up, 1 unit = 1 m. Every piece is described in path space (s, t, h): s = metres along the centre line from the
piece's start, t = metres across it (+ = left of the walking direction), h = height above the piece's ground at that s.

SECTION   one cross-section for the whole kit (FP01-FP05 and the 40 m sample): 2.0 m wide; a trodden tread 1.16 m wide sunk about
          6 cm between two soft soil banks (crests 0.12 m at 0.82 m out), a worn centre line 8 mm deep down the middle, the outer
          edge feathered down to 1.2 cm so it meets the forest floor. (Widened from 1.6 m on 2026-11-09 at the user's request: t is
          a logical across coordinate on the old 1.6 m section; widen(t) is the metres out from the centre line, see below.) section(t) is that height; the ends of every piece are exactly
          this section, all relief fades out over the last 0.4 m (taper), so any end meets any other end.
Straight  the FP01 frame: centre line along +X, s = 0 at x = -L/2.
slab()    the walking surface: a grid in (s, t) every 5 cm along and 4 cm across, skirts down to the ground on all four sides, an
          underside of one quad per row. Writes 'pth' (s, t, h) for the earth shader and for the row-dropping LODs (fp build: ground_lods).
fern_clump(), leaf(), root_across(), tri_tube(): the growth, leaves and roots laid on it.
"""
import math, random
import bmesh
from mathutils import Vector, noise
from ti_core import S, mesh
from cr_parts import set_attr_list
import fr_parts as FP

Z = Vector((0, 0, 1))
HW = .8              # half width of the section in logical t (the old 1.6 m section); widen(HW) = 1.0 m
TREAD_T, TREAD_W = .38, .58     # the tread edge: logical t .38 is .58 m out; the tread is stretched by .58 / .38, the banks only moved out
K_TREAD = TREAD_W / TREAD_T


def widen(t):
    """Metres out from the centre line at logical t: the tread (|t| < .38) stretched to 0.58 m, the banks (0.42 m) moved out by 0.2 m."""
    a = abs(t); return math.copysign(min(a, TREAD_T) * K_TREAD + max(a - TREAD_T, 0.), t)


def narrow(y):
    """The inverse of widen."""
    a = abs(y); return math.copysign(min(a, TREAD_W) / K_TREAD + max(a - TREAD_W, 0.), y)
DS, DT = .05, .04    # slab grid along and across
TAPER = .4           # relief fades to the bare section over the last 0.4 m of each end


def _ss(x):
    x = max(0., min(1., x)); return x * x * (3 - 2 * x)


def section(t):
    """The kit's path section: height (m) at t metres from the centre line."""
    a = abs(t)
    crown = .01 * max(0., 1 - (a / .45) ** 2)
    groove = -.008 * math.exp(-(a / .085) ** 2)
    bank = .065 * _ss((a - .36) / .26)
    fall = .108 * _ss((a - .63) / .17)
    return .055 + crown + groove + bank - fall


def section_slope(t, e=1e-4):
    """d height / d metres across (not per logical t)."""
    return (section(t + e) - section(t - e)) / (widen(t + e) - widen(t - e))


class Straight:
    """FP01: the centre line runs along +X from x = -L/2 (s = 0, west end) to x = +L/2 (east end); left (+t) is +Y."""
    def __init__(self, L=6.):
        self.L = L

    def p(self, s, t, h): return Vector((s - self.L / 2, widen(t), h))
    def ground(self, s): return 0.
    def base(self, s): return 0.          # the underside of the piece (a slope or a flight of steps is a solid wedge down to z = 0)
    def inv(self, x, y): return x + self.L / 2, narrow(y)
    def tangent(self, s): return Vector((1, 0, 0))
    def left(self, s): return Vector((0, 1, 0))


class Slope(Straight):
    """FP03: FP01's frame climbing rise metres; smoothstep profile, level at both ends (zero gradient), steepest 1.5 rise / L."""
    def __init__(self, L, rise):
        super().__init__(L); self.rise = rise

    def ground(self, s): return self.rise * _ss(s / self.L)


class Arc:
    """FP02: the centre line bends through angle (radians) on radius R, to the left (side = +1) or right (-1), starting along +X;
    the strip's outline is centred on the origin."""
    def __init__(self, angle, R, side):
        self.A, self.R, self.sg = angle, R, side; self.L = R * angle; self.off = Vector((0, 0, 0))
        pts = [self.p(self.L * i / 60, t, 0) for i in range(61) for t in (-HW, HW)]
        lo = Vector((min(q.x for q in pts), min(q.y for q in pts), 0)); hi = Vector((max(q.x for q in pts), max(q.y for q in pts), 0))
        self.off = -(lo + hi) / 2

    def tangent(self, s): f = s / self.R; return Vector((math.cos(f), self.sg * math.sin(f), 0))
    def left(self, s): f = s / self.R; return Vector((-self.sg * math.sin(f), math.cos(f), 0))

    def p(self, s, t, h):
        f = s / self.R
        q = Vector((self.R * math.sin(f), self.sg * self.R * (1 - math.cos(f)), 0)) + self.left(s) * widen(t) + self.off
        q.z = h; return q

    def ground(self, s): return 0.
    def base(self, s): return 0.

    def inv(self, x, y):
        d = Vector((x, y, 0)) - self.off - Vector((0, self.sg * self.R, 0))
        return self.R * math.atan2(d.x, -self.sg * d.y), narrow(self.sg * (self.R - d.length))


class StairsY:
    """FP05: walk along +Y from y = -L/2 (s = 0, the foot) up a flight of steps; left (+t) is -X. Each riser climbs rise metres
    over run metres centred on its s (hidden under the step log)."""
    def __init__(self, L, risers, rise, run=.1):
        self.L, self.rs, self.h, self.run = L, risers, rise, run

    def p(self, s, t, h): return Vector((-widen(t), s - self.L / 2, h))
    def inv(self, x, y): return y + self.L / 2, narrow(-x)
    def tangent(self, s): return Vector((0, 1, 0))
    def left(self, s): return Vector((-1, 0, 0))
    def ground(self, s): return sum(self.h * _ss((s - a) / self.run + .5) for a in self.rs)
    def base(self, s): return 0.


class Relief:
    """The surface of one piece: section + per-piece relief (banks wander, lumps, foot-hollows), all faded out at the ends.
    extras: functions (s, t) -> extra height (FP03 rain rills, FP04 soil heaped against the root).
    inner: (side, lower, shift) for a bend: the inside bank worn lower and the centre line drawn towards the inside, both
    largest mid-bend and zero at the ends."""
    def __init__(self, frame, seed, extras=(), inner=None):
        self.F = frame; R = random.Random(seed)
        self.o = [Vector((R.uniform(-60, 60), R.uniform(-60, 60), R.uniform(-60, 60))) for _ in range(6)]
        self.extras = list(extras); self.inner = inner

    def w(self, s): return _ss(min(s, self.F.L - s) / TAPER)

    def h(self, s, t):
        """Height above the piece's ground at (s, t)."""
        w = self.w(s); o = self.o; a = abs(t); side = 0 if t > 0 else 1
        wob = .055 * noise.noise(o[side] + Vector((s * .55, 0, 0)))          # each bank crest wanders in and out on its own
        a2 = max(0., a - w * wob * _ss((a - .18) / .2))                     # (the tread and its centre line stay put)
        z = section(a2)
        bank = _ss((a - .3) / .3)
        z += w * bank * .016 * noise.noise(o[2] + Vector((s * 2.1, t * 2.6, 0)))            # lumpy banks
        z += w * (1 - bank) * (.004 * noise.noise(o[3] + Vector((s * 5.5, t * 7., 0))) + .0025 * noise.noise(o[5] + Vector((s * 16., t * 16., 0))))   # packed, barely uneven
        dent = max(0., noise.noise(o[4] + Vector((s * 2.2, t * 4., 0))) - .25)              # shallow foot-hollows along the tread
        z -= w * (1 - bank) * .02 * dent
        if self.inner:                                                      # people cut the corner
            sg, low, sh = self.inner; k = w * math.sin(math.pi * s / self.F.L)
            if sg * t > 0: z -= low * k * _ss((a - .3) / .25) * (1 - _ss((a - .68) / .12))
            gv = lambda x: -.008 * math.exp(-(x / .085) ** 2)
            z += gv(t - sg * sh * k) - gv(t)
        for f in self.extras: z += f(s, t)
        return max(.008, z)

    def world(self, s, t, dz=0.):
        return self.F.p(s, t, self.F.ground(s) + self.h(s, t) + dz)


def slab(name, RL, mat, keep_s=(), **kw):
    """The walking surface grid with skirts, 'pth' = (s, t, h). Rows every DS along, columns every DT across. keep_s: rows that
    every LOD keeps (FP05: the foot and head of each riser), besides the LOD's own every-n-th rows."""
    F = RL.F; ni = int(round(F.L / DS)); nj = int(round(2 * HW / DT)); cu = nj + 1
    verts, pth = [], []
    for i in range(ni + 1):
        s = F.L * i / ni
        for j in range(cu):
            t = -HW + 2 * HW * j / nj; h = RL.h(s, t)
            verts.append(tuple(F.p(s, t, F.ground(s) + h))); pth.append((s, t, h))
    faces = [(i * cu + j, (i + 1) * cu + j, (i + 1) * cu + j + 1, i * cu + j + 1) for i in range(ni) for j in range(nj)]
    # closed shell: a ground vertex under each long edge vertex only, so the long skirts and the underside are one quad per row
    # (the row-dropping LODs keep them quads) and each end is a single cap (the section over its ground line); no T-junctions
    bot = {}
    for i in range(ni + 1):
        for j in (0, nj):
            s, t, h = pth[i * cu + j]; bot[i * cu + j] = len(verts)
            # a wedge's tall side: 'across' carries on outward with the depth, so the soil pattern keeps changing down the side
            verts.append(tuple(F.p(s, t, F.base(s)))); pth.append((s, math.copysign(HW + F.ground(s) - F.base(s), t), 0.))
    for i in range(ni):
        a, b = i * cu, (i + 1) * cu                                  # right skirt (t = -HW), facing out
        faces.append((a, bot[a], bot[b], b))
        a, b = (i + 1) * cu + nj, i * cu + nj                        # left skirt (t = +HW)
        faces.append((a, bot[a], bot[b], b))
        faces.append((bot[i * cu], bot[i * cu + nj], bot[(i + 1) * cu + nj], bot[(i + 1) * cu]))   # underside, facing down
    e = ni * cu                                                      # east cap (+s), then west cap
    caps = []; tall = []
    for sgn, r0 in ((1, e), (-1, 0)):
        s_e = F.L if sgn > 0 else 0.; m = int(math.ceil((F.ground(s_e) - F.base(s_e)) / .12))
        if m <= 1:                                                   # a low end: one polygon, the section over its ground line
            caps.append(tuple([e, bot[e], bot[e + nj]] + [e + j for j in range(nj, 0, -1)]) if sgn > 0 else
                        tuple([nj, bot[nj], bot[0]] + [j for j in range(0, nj)]))
            continue
        # a wedge's tall end (FP03 / FP05 top): a grid of m levels; 'along' carries on past the end with the depth, so the soil
        # pattern changes down the face, and 'h' is minus the depth (the shader's cut-soil profile). Its edge vertices are threaded into the neighbouring skirt and underside faces (no T-joints).
        zb = F.base(s_e); V = [[r0 + j for j in range(cu)]]; tall.append(ni - 1 if sgn > 0 else 1)
        for l in range(1, m + 1):
            row = []
            for j in range(cu):
                if l == m and j in (0, nj): row.append(bot[r0 + j]); continue
                ztop = verts[r0 + j][2]; z = zb + (ztop - zb) * (1 - l / m); q = list(verts[r0 + j]); q[2] = z
                row.append(len(verts)); verts.append(tuple(q)); pth.append((s_e + sgn * (ztop - z), pth[r0 + j][1], z - ztop))
            V.append(row)
        for l in range(m):
            for j in range(nj):
                caps.append((V[l][j], V[l + 1][j], V[l + 1][j + 1], V[l][j + 1]) if sgn > 0 else
                            (V[l][j + 1], V[l + 1][j + 1], V[l + 1][j], V[l][j]))
        c0 = [V[l][0] for l in range(1, m)]; cn = [V[l][nj] for l in range(1, m)]; bm_ = [V[m][j] for j in range(1, nj)]
        i = ni - 1 if sgn > 0 else 0; k = ni * nj + 3 * i
        if sgn > 0:
            a, b = i * cu, (i + 1) * cu; faces[k] = tuple([a, bot[a], bot[b]] + c0[::-1] + [b])
            a, b = (i + 1) * cu + nj, i * cu + nj; faces[k + 1] = tuple([a] + cn + [bot[a], bot[b], b])
            faces[k + 2] = tuple([bot[i * cu], bot[i * cu + nj]] + [bot[(i + 1) * cu + nj]] + bm_[::-1] + [bot[(i + 1) * cu]])
        else:
            a, b = i * cu, (i + 1) * cu; faces[k] = tuple([a] + c0 + [bot[a], bot[b], b])
            a, b = (i + 1) * cu + nj, i * cu + nj; faces[k + 1] = tuple([a, bot[a], bot[b]] + cn[::-1] + [b])
            faces[k + 2] = tuple([bot[i * cu]] + bm_ + [bot[i * cu + nj], bot[(i + 1) * cu + nj], bot[(i + 1) * cu]])
    faces += caps
    o = mesh(name, verts, faces, mat, smooth=True, **{'grain': 'z', **kw})
    set_attr_list(o, 'pth', pth)
    # texel weight per face (ti_pipeline scales each UV island by it): the underside, never seen, gets almost no atlas
    w = [1.] * len(faces)
    for i in range(ni): w[ni * nj + 3 * i + 2] = .02
    at = o.data.attributes.new('uvw', 'FLOAT', 'FACE'); at.data.foreach_set('value', w)
    # rows next to a tall end are kept at every LOD: its skirt and underside faces carry the end grid's edge vertices
    S['slab'] = dict(ni=ni, nj=nj, L=F.L, keep=sorted({int(round(s / (F.L / ni))) for s in keep_s} | set(tall)))
    if tall:
        bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    return o


def tri_tube(name, pts, radii, mat, sides=3, **kw):
    """A thin closed-section tube (3 or 4 sides) through pts: rachis, stalks, crown stubs. Open ends are too small to see."""
    P = [Vector(p) for p in pts]; n = len(P); verts, faces = [], []
    for i in range(n):
        T = (P[min(n - 1, i + 1)] - P[max(0, i - 1)]).normalized()
        a = T.cross(Z if abs(T.z) < .95 else Vector((1, 0, 0))).normalized(); b = T.cross(a)
        for k in range(sides):
            th = math.tau * k / sides + i * .4
            verts.append(tuple(P[i] + (a * math.cos(th) + b * math.sin(th)) * radii[i]))
    for i in range(n - 1):
        for k in range(sides):
            c, d = i * sides + k, i * sides + (k + 1) % sides
            faces.append((c, d, d + sides, c + sides))
    return mesh(name, verts, faces, mat, smooth=True, **{'grain': 'z', **kw})


# ------------------------------------------------------------------ ferns (after the BM09 look: arching fronds, pinnae, browned tips)
def frond(name, q0, d, L, mat, stem_mat, R, rise, droop, bend, n_pairs=12, detail=1, ylim=None, roll=0., lat=lambda p: abs(p.y)):
    """One arching frond from q0 along heading d (horizontal unit vector): a thin rachis and n_pairs of lance pinnae on each side,
    angled forward, longest a third of the way out, tiny at the tip. Returns the frond's lowest point above its base."""
    d = Vector(d).normalized(); side = Vector((-d.y, d.x, 0))
    def at(v):
        return q0 + d * (L * v) + Z * (L * (rise * v - droop * v * v)) + side * (L * bend * v * v)
    ns = 9; spine = [at(k / (ns - 1)) for k in range(ns)]
    tri_tube(name + '_Rachis', spine, [.0032 - .0024 * k / (ns - 1) for k in range(ns)], stem_mat, detail=detail)
    verts, faces, cuv = [], [], []
    for k in range(n_pairs):
        for sg in (-1, 1):
            v = .1 + .87 * k / (n_pairs - 1) + sg * .012
            b = at(v); T = (at(min(1., v + .02)) - at(max(0., v - .02))).normalized()
            Sd = T.cross(Z).normalized(); N = Sd.cross(T).normalized()
            Sd, N = (Sd * math.cos(roll) + N * math.sin(roll)).normalized(), (N * math.cos(roll) - Sd * math.sin(roll)).normalized()   # this frond's lean
            pl = L * .19 * max(.14, math.sin(math.pi * (.06 + .88 * v))) ** .75
            w = pl * .29
            dirv = (Sd * sg * .8 + T * .55 + N * (.16 - .42 * v)).normalized()
            ws = dirv.cross(N).normalized(); lift = N * w * .2
            pts = [b, b + dirv * pl * .3 + ws * w * .5 + lift, b + dirv * pl * .3 - ws * w * .5 + lift,
                   b + dirv * pl * .66 + ws * w * .42 + lift * .8, b + dirv * pl * .66 - ws * w * .42 + lift * .8, b + dirv * pl]
            if ylim is not None:                               # a pinna reaching past the strip edge is drawn shorter, not flattened
                far = max(lat(p) for p in pts); lb = lat(b)
                if far > ylim and lb < ylim - .005:
                    f = (ylim - lb) / (far - lb); pts = [b + (p - b) * f for p in pts]
            i0 = len(verts); verts += [tuple(p) for p in pts]
            cuv += [(.5, v, 0.), (0., v, 0.), (1., v, 0.), (0., v, 0.), (1., v, 0.), (.5, v, 0.)]
            faces += [(i0, i0 + 1, i0 + 2), (i0 + 2, i0 + 1, i0 + 3, i0 + 4), (i0 + 4, i0 + 3, i0 + 5)]
    o = mesh(name, verts, faces, mat, smooth=True, solid=.0008, rim=False, **{'grain': 'z', 'detail': detail})
    set_attr_list(o, 'cuv', cuv)
    return min(p[2] for p in verts) - q0.z


def fern_clump(prefix, RL, s, t, L, n, mats, R, ylim=.785, headings=None, detail=1, young=False):
    """A fern crown on the path edge: n fronds fanned round it (headings in radians, or spread round the full circle), a few dead
    stubs at the base, one fiddlehead. Fronds that would reach past ylim across the path are turned to run along it."""
    base = RL.world(s, t, -.012); F = RL.F
    green, old, stem = mats
    reach = L * 1.2; Tn, Lf = F.tangent(s), F.left(s); lat = lambda p: abs(F.inv(p.x, p.y)[1])
    hi, lo = (ylim - .03 - t) / reach, (-ylim + .03 - t) / reach      # keep inside the strip: swing along the path
    if headings: hs = [a + R.uniform(-.2, .2) for a in headings]
    else:            # fan the fronds evenly over the headings that stay inside the strip, so no two run side by side
        M = 720; ok = [lo <= math.sin(i * math.tau / M) <= hi for i in range(M)]
        st = next((i for i in range(M) if ok[i] and not ok[i - 1]), R.randrange(M))
        arc = [(st + i) % M for i in range(M) if ok[(st + i) % M]]
        step = len(arc) / n; off = R.uniform(0, step) if all(ok) else step / 2
        hs = [arc[min(len(arc) - 1, int(off + k * step + R.uniform(-.25, .25) * step))] * math.tau / M for k in range(n)]
        R.shuffle(hs)
    for k, a in enumerate(hs):
        sn, cs = math.sin(a), math.cos(a)
        if not lo <= sn <= hi:
            sn = max(lo, min(hi, sn)) * R.uniform(.35, .95)            # spread out: fronds swung to one limit would lie on top of each other
            cs = math.copysign(math.sqrt(max(0., 1 - sn * sn)), cs if abs(cs) > .05 else R.choice((-1, 1)))
            a = math.atan2(sn, cs)
        d = (Tn * math.cos(a) + Lf * math.sin(a)).normalized()          # a: heading from the path direction, + to the left
        q0 = base + d * R.uniform(.008, .02) + Z * ((k - len(hs) / 2) * .003)    # every frond starts at its own height
        Lk = L * R.uniform(.7, 1.); rise = R.uniform(.75, 1.15) if not young else R.uniform(1., 1.4)
        droop = rise * R.uniform(.92, 1.12)
        sx, sy = F.inv(*(q0 + d * Lk)[:2]); end_h = RL.world(sx, sy).z
        while q0.z + Lk * (rise - droop) < end_h + .02 and droop > .3: droop -= .05        # the tip stays off the soil
        oldf = (not young) and R.random() < .3
        frond(f'{prefix}_Frond', q0, d, Lk, old if oldf else green, stem, R, rise, droop, R.uniform(-.12, .12),
              n_pairs=12 if Lk > .25 else 8, detail=detail, ylim=ylim, roll=(-1) ** k * R.uniform(.09, .2), lat=lat)   # neighbours lean opposite ways: no two share a plane
    for k in range(2 if not young else 0):                    # dead stubs, brown, lying out from the crown
        a = R.uniform(0, math.tau); d = Vector((math.cos(a), math.sin(a), 0)); Ls = R.uniform(.05, .09)
        pts = [base + Z * .008, base + d * Ls * .5 + Z * .022, base + d * Ls + Z * .012]
        tri_tube(f'{prefix}_DeadStub', pts, [.0028, .0022, .0014], stem, detail=2)
    a = R.uniform(0, math.tau); d = Vector((math.cos(a), math.sin(a), 0)); side = Vector((-d.y, d.x, 0))
    pts = [base + Z * .005, base + d * .012 + Z * .05]
    c = base + d * .026 + Z * .062; rr = .012
    for k in range(10):                                       # fiddlehead: the young frond still coiled
        th = math.pi * .5 - k / 9 * math.tau * .95; rk = rr * (1 - k / 13)
        pts.append(c + d * (math.cos(th) * rk) + Z * (math.sin(th) * rk) + side * (k * .0006))
    tri_tube(f'{prefix}_Fiddlehead', pts, [.0034] * 2 + [.0034 - .0018 * k / 9 for k in range(10)], green, detail=2)


# ------------------------------------------------------------------ fallen leaves, draped onto what is under them
def leaf_outline(kind, L, R):
    """Leaf outline in local (along, across) metres with 'cuv' per point; kind 'maple' (five lobes) or 'lance'."""
    if kind == 'maple':
        # five broad lobes (angle from the tip direction, length), each drawn shoulder - point - shoulder, notches between them
        lobes = [(-118, .52), (-58, .86), (0, 1.), (58, .86), (118, .52)]
        out = [(180, .16)]
        for k, (ang, r) in enumerate(lobes):
            ang += R.uniform(-5, 5); r *= R.uniform(.9, 1.06)
            out += [(ang - 17, r * .62), (ang, r), (ang + 17, r * .62)]
            if k < 4: out.append((ang + 29, r * .44))
        P = [(0., 0.)]; C = [(.5, 0., 0.)]
        for ang, r in out:
            a = math.radians(ang); rr = r * L * .5
            P.append((math.sin(a) * rr, math.cos(a) * rr)); C.append((.5 + .5 * math.sin(a), r, 0.))
        faces = [(0, k, k % (len(P) - 1) + 1) for k in range(1, len(P))]
        return P, C, faces
    W = L * R.uniform(.32, .45)
    P = [(0., -L / 2), (W * .42, -L * .22), (W * .5, L * .15), (0., L / 2), (-W * .5, L * .15), (-W * .42, -L * .22)]
    C = [(.5, 0., 0.), (1., .28, 0.), (1., .65, 0.), (.5, 1., 0.), (0., .65, 0.), (0., .28, 0.)]
    return P, C, [(0, 1, 2, 3, 4, 5)]


def leaf(name, x, y, a, L, kind, mat, R, lift=.0022, curl=.006, detail=2):
    """Lay one leaf at (x, y), heading a, every corner dropped onto the first surface under it, edges and tip curled up a little.
    Returns the object, or None where nothing is under it."""
    P, C, faces = leaf_outline(kind, L, R)
    ca, sa = math.cos(a), math.sin(a); V = []; hz = []
    for (u, v), c in zip(P, C):
        px, py = x + u * ca - v * sa, y + u * sa + v * ca
        hit = FP.snap((px, py, 4.), (0, 0, -1))
        if hit is None: return None
        hz.append(hit[0].z)
        rim = min(1., (abs(c[0] - .5) * 2) ** 2 + max(0., c[1] - .8) * 2)
        V.append((px, py, hit[0].z + lift + curl * rim))
    if max(hz) - min(hz) > L * .3: return None          # would stand up the side of a stone or a root: a leaf lies flat or slides off
    o = mesh(name, V, faces, mat, smooth=True, solid=.001, rim=False, **{'grain': 'z', 'detail': detail})
    set_attr_list(o, 'cuv', C)
    return o


# ------------------------------------------------------------------ thin roots under the tread
def root_across(name, RL, a, b, r, mat, R, wiggle=.06, expose=.38, step=.045):
    """A thin root crossing the path from a = (s, t) to b: it rises out of the soil, runs just under the surface with its top showing
    (expose = share of the diameter above the soil in the middle), and dives back in. Follows the relief, wanders a little."""
    n = 9; pts, radii = [], []
    ax, bx = Vector((a[0], a[1], 0)), Vector((b[0], b[1], 0)); d = (bx - ax); perp = Vector((-d.y, d.x, 0)).normalized()
    ph = R.uniform(0, math.tau)
    for k in range(n):
        u = k / (n - 1); q = ax + d * u + perp * (wiggle * math.sin(ph + u * math.pi * 2.2) * math.sin(math.pi * u))
        rk = r * (1.15 - .4 * u)
        sink = 1.9 - (1.9 - (1 - 2 * expose)) * math.sin(math.pi * min(1., max(0., (u - .04) / .92))) ** .6   # centre depth in radii
        pts.append(tuple(RL.world(q.x, q.y, -rk * sink))); radii.append(rk)
    return FP.sweep(name, pts, radii, mat, step=step, aspect=.8, fiss=.16, nring=10, seed=R.randrange(999), worn=.85, lump=.06)


# ------------------------------------------------------------------ logs and thick roots (FR04 log recipe, any direction)
def bark_ring(so, s, r, th, twist=.25, plates=2.8, crack=.32, fiss=.22, lump=.05):
    """Radius factor, fissure value and lump at one point of a bark ring (fr_parts.sweep's crack recipe, as FR04): deep cracks on
    the flanks and underside, none on top (th = pi/2 faces up)."""
    rho = max(.6, plates * r)
    q = so + Vector((math.cos(th + twist * s) * rho, math.sin(th + twist * s) * rho, s * .42))
    F = max(0., 1. - abs(noise.noise(q)) / crack) ** 1.3
    facing = max(0., math.sin(th))
    depth = fiss * F * (1. - facing ** 1.5)
    bump = lump * noise.noise(so * .7 + Vector((math.cos(th) * 1.3, math.sin(th) * 1.3, s * .55)))
    return 1. + bump + .015 * noise.noise(q * 3.1) - depth, F * (1. - facing ** 1.5), bump


def _cap(verts, faces, attr_b, attr_a, ring, centre, n_in, ax, ay, push):
    """Close a ring with n_in concentric rings and a centre vertex; push(f) offsets the inner rings (a dome). 'adze' gets
    (radius from the centre, angle, 0) for the rings shader. Returns the number of new faces."""
    c = Vector(centre); m = len(ring); rings = [ring]
    def polar(p):
        d = Vector(p) - c; x, y = d.dot(ax), d.dot(ay); return (math.hypot(x, y), math.atan2(y, x), 0.)
    for k in ring: attr_a[k] = polar(verts[k])
    for j in range(1, n_in + 1):
        f = 1 - j / (n_in + 1); idx = []
        for k in ring:
            p = c + (Vector(verts[k]) - c) * f + push(f)
            verts.append(tuple(p)); idx.append(len(verts) - 1); attr_b.append((0., 0., 0.)); attr_a.append(polar(p))
        rings.append(idx)
    verts.append(tuple(c + push(0.))); ci = len(verts) - 1; attr_b.append((0., 0., 0.)); attr_a.append((0., 0., 0.))
    n0 = len(faces)
    for a_, b_ in zip(rings, rings[1:]):
        for k in range(m): faces.append((a_[k], a_[(k + 1) % m], b_[(k + 1) % m], b_[k]))
    for k in range(m): faces.append((rings[-1][k], rings[-1][(k + 1) % m], ci))
    return len(faces) - n0


def bark_log(name, pts, radii, mats, seed, step=.06, nv=28, flat=None, caps=('rings', 'rings'), fiss=.22, lump=.05, twist=.25,
             dome=.5, ground_cut=None, **kw):
    """A log or a thick root along pts with bark rings (FR04's log). flat(p) -> height or None: every ring point above it is laid
    on that height (foot-worn or hewn), and faces wholly on it take mats[1] (heartwood). Each end is closed with sawn rings
    (mats[2]) or a rounded bark dome ('dome'). ground_cut: cut off below that height and close the cut (the part in the soil)."""
    C, Rr, Sv = FP.resample(pts, radii, step); n = len(C)
    R = random.Random(seed); so = Vector((R.uniform(-50, 50), R.uniform(-50, 50), R.uniform(-50, 50)))
    fr = []
    for i in range(n):
        T = (C[min(n - 1, i + 1)] - C[max(0, i - 1)]).normalized()
        U = Z - Z.dot(T) * T; U = U.normalized() if U.length > .1 else T.orthogonal().normalized()
        fr.append((T, T.cross(U).normalized(), U))
    verts, flat_v, ab, aa = [], [], [], []
    for i in range(n):
        T, Sd, U = fr[i]
        for k in range(nv):
            th = math.tau * k / nv
            f, F_, bump = bark_ring(so, Sv[i], Rr[i], th, fiss=fiss, lump=lump, twist=twist)
            d = Sd * math.cos(th) + U * math.sin(th); p = C[i] + d * (Rr[i] * f)
            fz = flat(p) if flat else None; on = fz is not None and p.z > fz
            if on:
                p = C[i] + d * (Rr[i] * (1 + .5 * bump)); lat_ = (p - C[i]).dot(Sd)
                p.z = fz - .005 * max(0., 1 - (lat_ / (Rr[i] * .8)) ** 2) + .002 * noise.noise(so + p * 6.)
            verts.append(tuple(p)); flat_v.append(on); ab.append((Sv[i], th * Rr[i], F_)); aa.append((Sv[i], (p - C[i]).dot(Sd), 1.))
    faces, mi = [], []
    for i in range(n - 1):
        for k in range(nv):
            a = i * nv + k; b = i * nv + (k + 1) % nv
            faces.append((a, b, b + nv, a + nv)); mi.append(1 if all(flat_v[v] for v in (a, b, b + nv, a + nv)) else 0)
    for end, kind in ((0, caps[0]), (n - 1, caps[1])):
        T, Sd, U = fr[end]; sgn = -1. if end == 0 else 1.
        ring = [end * nv + k for k in range(nv)]
        if end == 0: ring = ring[::-1]
        h = (.004 if kind == 'rings' else dome) * Rr[end]
        cnt = _cap(verts, faces, ab, aa, ring, C[end], 4, Sd, U, lambda f, T=T, sgn=sgn, h=h: T * (sgn * h * (1 - f * f)))
        mi += [2 if kind == 'rings' else 0] * cnt
    o = mesh(name, verts, faces, mats[0], smooth=True, **{'grain': 'z', **kw})
    for m in mats[1:]: o.data.materials.append(m)
    for p, m in zip(o.data.polygons, mi):
        p.material_index = m
        if m: p.use_smooth = False                     # worn and sawn faces are flat
    set_attr_list(o, 'bark', ab); set_attr_list(o, 'adze', aa)
    bm = bmesh.new(); bm.from_mesh(o.data)
    if ground_cut is not None and min(v[2] for v in verts) < ground_cut:
        S['cut_n'] = S.get('cut_n', -1) + 1; gz = ground_cut + (S['cut_n'] % 24) * .0021
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, gz), plane_no=(0, 0, 1), clear_inner=True)
        edges = [e for e in bm.edges if e.is_boundary]
        if edges: bmesh.ops.holes_fill(bm, edges=edges, sides=0)
        big = [f for f in bm.faces if len(f.verts) > 4]
        if big: bmesh.ops.triangulate(bm, faces=big)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    return o
