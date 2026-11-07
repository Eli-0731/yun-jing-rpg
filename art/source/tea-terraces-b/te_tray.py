"""TE04_Tray  shallow tea-drying tray, 1.2 x 0.74 x 0.12 m (AI three-view TE04/TRAY candidate-04, elevations from candidate-04-r1).

A rounded-rectangle tray, not a round sieve: one flat-woven split-bamboo mat whose edge is bent up into a low wall, clamped
at the top between an outer and an inner strip of weathered cedar, bound with dark rattan at twelve points (three on each
long side, one on each short side, one at each corner). Two square repairs: one on the floor near the back-right corner,
one on the front wall left of centre. A thin single layer of withering tea leaves spread over the left two-thirds.

Blender Z-up, 1 unit = 1 m, front -Y (a long side), origin at the bottom centre (z = 0 under the floor).
"""
import math, random
from mathutils import Vector, noise
from ti_core import S, surface, tube, mesh
import mk_mats as mm
import cr_mats as cm
from cr_parts import set_attr_list
from te_props import wuv
from cr_parts import sheet


def palette():
    P = {}
    P['weave'] = mm.weave('Tray_Weave', (.5, .28, .07), (.11, .058, .016), reed=.0105, block=.042, green_cast=.18, wobble=.006, strip_var=.42)
    P['strip'] = mm.bamboo('Darn_Bamboo', green=(.12, .12, .045), straw=(.38, .26, .085))   # newer strips, a little greener than the old mat
    P['cedar'] = cm.wood('Rim_Cedar', (.1, .042, .018), (.32, .15, .062), ground_h=0., grey=.14)
    P['rattan'] = mm.bamboo('Rim_Rattan', green=(.035, .024, .014), straw=(.11, .066, .03))   # split rattan cane, dark and a little glossy
    P['twine'] = mm.hemp('Tray_Patch_Twine', (.13, .085, .04), twist=260.0)
    # half-withered leaves: darker olive than the fresh leaves in the basket, a few still bright
    P['leaf'] = [cm.weed_leaf('Withering_Leaf_A', (.026, .038, .011), (.068, .085, .024), (.11, .105, .034)),    # soft olive
                 cm.weed_leaf('Withering_Leaf_B', (.035, .04, .013), (.09, .09, .03), (.14, .11, .04)),        # yellowing
                 cm.weed_leaf('Withering_Leaf_C', (.02, .034, .012), (.05, .072, .024), (.08, .09, .03))]      # still dark green
    return P


# ------------------------------------------------------------------ outline: rounded rectangle, exact inward offsets
A0, B0, RC0 = .58, .35, .21    # half length / half depth / corner radius of the woven mat's top edge
LX, LY = 2 * (A0 - RC0), 2 * (B0 - RC0)
ARC = math.pi / 2 * RC0
PERIM = 2 * LX + 2 * LY + 4 * ARC
CX, CY = A0 - RC0, B0 - RC0      # corner centres at (+-CX, +-CY)
# woven mat profile: flat floor, then a quarter-ellipse up to the rim
D_F = .075                       # floor edge, inset from the top edge
Z_F = .003                       # floor mid-surface (the 6 mm mat sits on z = 0)
H_W = .1                         # wall rise from the floor to the woven top edge
RIM_Z = .098                     # centre height of the two cedar strips
N_U = 120


SEGS = (('s', LX / 2, (0., -B0), (1, 0), (0, -1)), ('c', ARC, (CX, -CY), -math.pi / 2), ('s', LY, (A0, -CY), (0, 1), (1, 0)),
        ('c', ARC, (CX, CY), 0.), ('s', LX, (CX, B0), (-1, 0), (0, 1)), ('c', ARC, (-CX, CY), math.pi / 2),
        ('s', LY, (-A0, CY), (0, -1), (-1, 0)), ('c', ARC, (-CX, -CY), math.pi), ('s', LX / 2, (-CX, -B0), (1, 0), (0, -1)))


def outline(u, d=0.):
    """Point and outward normal on the outline inset by d, at arc position u (metres along the d = 0 outline, 0 = front centre, CCW).
    The straight runs do not change length with d and the corners keep their centres, so every inset is an exact offset."""
    u %= PERIM; acc = 0.
    for sg in SEGS:
        L = sg[1]
        if u <= acc + L + 1e-12 or sg is SEGS[-1]:
            f = min(1., (u - acc) / L)
            if sg[0] == 'c':
                (cx, cy), a = sg[2], sg[3] + f * math.pi / 2
                n = (math.cos(a), math.sin(a)); return (cx + (RC0 - d) * n[0], cy + (RC0 - d) * n[1]), n
            (x0, y0), t, n = sg[2], sg[3], sg[4]
            return (x0 + t[0] * f * L - n[0] * d, y0 + t[1] * f * L - n[1] * d), n
        acc += L


def inside(x, y, d):
    """True when (x, y) lies inside the outline inset by d."""
    dx, dy = max(abs(x) - CX, 0.), max(abs(y) - CY, 0.)
    return abs(x) <= A0 - d and abs(y) <= B0 - d and math.hypot(dx, dy) <= RC0 - d


def lift(x, y):
    """A mat is never dead flat: the floor rises up to 2.4 mm in soft bumps (never below z = 0)."""
    return .0012 * (noise.noise(Vector((x * 2.3, y * 2.3, 7.))) + 1)


def frame(u, d=0.):
    (x, y), n = outline(u, d)
    return Vector((x, y, 0.)), Vector((n[0], n[1], 0.)), Vector((-n[1], n[0], 0.))   # point, outward normal, CCW tangent


def wall(u, phi, off=0.):
    """Mat surface on the curved wall: phi 0 at the floor edge (horizontal tangent) to pi/2 at the top edge (vertical); off along the outward normal."""
    p, n, _ = frame(u, D_F * (1 - math.sin(phi)))
    z = Z_F + H_W * (1 - math.cos(phi))
    no = Vector((H_W * math.sin(phi), D_F * math.cos(phi)))    # outward-down normal in the (n, z) plane
    no.normalize()
    wob = .0025 * math.sin(2 * phi) * noise.noise(Vector((p.x * 3, p.y * 3, 2.)))   # the bent-up edge bulges a little, unevenly
    return p + n * (no.x * off + wob) + Vector((0, 0, z - no.y * off))


def profile_len(phi, steps=24):
    s, prev = 0., Vector((0., Z_F))
    for k in range(1, steps + 1):
        f = phi * k / steps; q = Vector((D_F * math.sin(f), Z_F + H_W * (1 - math.cos(f))))
        s += (q - prev).length; prev = q
    return s


def te04_tray(P):
    R = random.Random(402)
    # one woven mat: a floor fan (centre + scaled outlines) running straight into the bent-up wall, so there is no seam at the turn
    NV_F, NV_W = 5, 9
    us = [k / N_U * PERIM for k in range(N_U)]
    verts, wv = [(0., 0., Z_F + lift(0, 0))], [(0., 0.)]
    for j in range(1, NV_F + 1):
        f = j / NV_F
        for u in us:
            p, _, _ = frame(u, D_F); x, y = p.x * f, p.y * f
            verts.append((x, y, Z_F + lift(x, y))); wv.append((x, y))
    for j in range(1, NV_W + 1):
        phi = math.pi / 2 * j / NV_W; t = profile_len(phi)
        for u in us:
            p, n, _ = frame(u, D_F); q = wall(u, phi)
            verts.append(tuple(q)); e = p + n * t; wv.append((e.x, e.y))
    rows = NV_F + NV_W
    faces = [(0, 1 + i, 1 + (i + 1) % N_U) for i in range(N_U)]
    faces += [(1 + (j - 1) * N_U + i, 1 + j * N_U + i, 1 + j * N_U + (i + 1) % N_U, 1 + (j - 1) * N_U + (i + 1) % N_U) for j in range(1, rows) for i in range(N_U)]
    m = mesh('Tray_Mat', verts, faces, P['weave'], smooth=True, solid=.006, grain='z')
    # 45-degree weave on the mat's flattened coordinates (floor x, y; the wall unrolled outward from the floor edge)
    diag = lambda a, b: ((a + b) * .7071, (a - b) * .7071)
    set_attr_list(m, 'wuv', [(*diag(*w), 0.) for w in wv])   # carried through the solidify modifier to both faces
    # rim: twelve rattan bindings; both cedar strips are butted at every binding so each length keeps its grain along its own chord
    q = math.pi / 4 * RC0
    lash_u = [0., .3, LX / 2 + q, LX / 2 + ARC + LY / 2, LX / 2 + 2 * ARC - q + LY, LX / 2 + 2 * ARC + LY + (CX - .3)]
    lash_u += [u + PERIM / 2 for u in lash_u]
    lash_u = sorted((u + R.uniform(-.012, .012)) % PERIM for u in lash_u)
    for name, d, w, h, z in (('Rim_Outer', -.0115, .022, .04, RIM_Z), ('Rim_Inner', .0095, .016, .032, RIM_Z - .002)):
        for i, u0 in enumerate(lash_u):
            u1 = lash_u[(i + 1) % len(lash_u)] + (PERIM if i == len(lash_u) - 1 else 0.)
            strip(name, u0 + .001, u1 - .001, d, z, w, h, P['cedar'], R)
    for u in lash_u:
        p, n, t = frame(u, 0.)
        bind(p + n * .0025 + Vector((0, 0, RIM_Z)), n, t, .0185, .0185, .034, .0032, P['rattan'], turns=4)   # bedded 1.5 mm into the strips
    repairs(P, R)
    spread_leaves(P, R)
    # collision: a 24-sided slab round the outer rim, floor to rim top
    ring = [frame(k / 24 * PERIM, -.026)[0] for k in range(24)]
    cverts = [(p.x, p.y, 0.) for p in ring] + [(p.x, p.y, RIM_Z + .022) for p in ring]
    cfaces = [(k, (k + 1) % 24, 24 + (k + 1) % 24, 24 + k) for k in range(24)] + [tuple(range(23, -1, -1)), tuple(range(24, 48))]
    S['collision_mesh'] = (cverts, cfaces)
    S['prop'] = dict(kind='tray', rim_top=RIM_Z + .02, half_len=A0 + .0225, half_depth=B0 + .0225, floor_z=Z_F + .003)


def strip(name, u0, u1, d, zc, w, h, mat, R, step=.04):
    """A cedar strip with a softened rectangular section (w across the rim, h tall) bent along the outline from u0 to u1."""
    n_s = max(2, int((u1 - u0) / step))
    rr = .3 * min(w, h)   # corner rounding radius (m); three points per corner, 45 degrees apart
    pts2 = []
    for (sx, sy), a0 in (((1, -1), -math.pi / 2), ((1, 1), 0.), ((-1, 1), math.pi / 2), ((-1, -1), math.pi)):
        for k in range(3):
            a = a0 + k * math.pi / 4
            pts2.append(((sx * (w / 2 - rr) + rr * math.cos(a)) / w, (sy * (h / 2 - rr) + rr * math.sin(a)) / h))
    verts, faces = [], []
    sag = R.uniform(-.0015, .0015)
    for k in range(n_s + 1):
        f = k / n_s; u = u0 + (u1 - u0) * f
        p, n, _ = frame(u, d)
        zz = zc + sag * math.sin(math.pi * f) + .0008 * noise.noise(Vector((u * 4, d * 9, 1.)))
        for a, b in pts2:
            verts.append(tuple(p + n * (a * w) + Vector((0, 0, zz + b * h))))
    m = len(pts2)
    for k in range(n_s):
        for i in range(m):
            faces.append((k * m + i, k * m + (i + 1) % m, (k + 1) * m + (i + 1) % m, (k + 1) * m + i))
    faces += [tuple(range(m - 1, -1, -1)), tuple(n_s * m + i for i in range(m))]
    (pa, _, _), (pb, _, _) = frame(u0, d), frame(u1, d)
    chord = (pb - pa).normalized()
    o = mesh(name, verts, faces, mat, smooth=True, grain=tuple(chord))
    from cr_parts import _sharp
    _sharp(o.data, 50)   # only the butt-end caps stay crisp
    return o


def bind(c, n, t, rx, rz, span, r, mat, turns, per_turn=6):
    """Rattan binding wrapped tight round both cedar strips and the mat edge between them, running along the rim tangent t."""
    up = Vector((0, 0, 1)); m = int(turns * per_turn); pts = []
    for i in range(m + 1):
        s = i / m; ang = s * turns * math.tau
        pts.append(tuple(c + t * (span * (s - .5)) + n * ((rx + r) * math.cos(ang)) + up * ((rz + r) * math.sin(ang))))
    return tube('Rim_Binding', pts, r, mat, res=2, grain=tuple(t), detail=1)


def repairs(P, R):
    """Two darned repairs as in the reference: a few newer split-bamboo strips woven over a worn spot, crossing in a small grid,
    sewn down at the corners. One on the floor near the back-right corner, one on the outside of the front wall left of centre."""
    cx, cy, hw, hd, rot = .33, .17, .075, .062, .12
    ca, sa = math.cos(rot), math.sin(rot)
    def floor_at(u, v, off):   # u, v in 0..1 over the patch; off above the mat's mid-surface
        x, y = (u - .5) * 2 * hw, (v - .5) * 2 * hd
        X, Y = cx + x * ca - y * sa, cy + x * sa + y * ca
        return Vector((X, Y, Z_F + lift(X, Y) + off))
    darn(P, R, 'Floor_Darn', floor_at, 2 * hw, 2 * hd, Vector((ca, sa, 0)))
    u0, du, ph0, ph1 = PERIM - .26, .07, .3, 1.5   # the wall is only ~0.1 m tall: use most of it so the strips do not crowd
    def wall_at(u, v, off):
        return wall(u0 + (u - .5) * 2 * du, ph0 + v * (ph1 - ph0), off)
    darn(P, R, 'Wall_Darn', wall_at, 2 * du, profile_len(ph1) - profile_len(ph0), Vector((1, 0, 0)))


def darn(P, R, name, at, Lu, Lv, side):
    """Four strips along u under four strips along v; the upper ones arch over the lower and bend down to the mat at their ends."""
    w = .0145; lo, hi, ends = .0042, .0059, .0040     # strip centre heights over the mat's mid-surface (mat top face at +3 mm, strips 1.6 mm thick)
    for k, c in enumerate((.13, .38, .62, .87)):
        for along in ('u', 'v'):
            L = Lu if along == 'u' else Lv; Wf = w / (Lv if along == 'u' else Lu)
            jit = R.uniform(-.02, .02); t0, t1 = -.08 + R.uniform(-.03, .03), 1.08 + R.uniform(-.03, .03)   # ragged ends: no two end caps share a plane
            def fn(i, j, along=along, c=c + jit, Wf=Wf, t0=t0, t1=t1):
                t = t0 + (t1 - t0) * j; acr = c + (i - .5) * Wf
                if along == 'u':
                    return tuple(at(t, acr, lo))
                bend = math.sin(math.pi * min(max(t, 0.), 1.)) ** .35
                return tuple(at(acr, t, ends + (hi - ends) * bend))
            o = sheet(name, 1, 10, fn, P['strip'], solid=.0016, grain='z')
            a, b = Vector(fn(.5, 0.)), Vector(fn(.5, 1.))
            o['grain'] = 'v'; o['grain_vec'] = list((b - a).normalized())
    # twine at the four corners of the darn
    for u, v in ((.06, .06), (.94, .06), (.06, .94), (.94, .94)):
        c = at(u, v, hi); o = (at(u, v, hi + .01) - c).normalized()
        up = o.cross(side).normalized(); sd = side.normalized()
        for s in (1, -1):
            d = (sd * s + up) * .007
            q = [tuple(c - d + o * .0006), tuple(c + o * .0028), tuple(c + d + o * .0006)]
            tube('Darn_Stitch', q, .0015, P['twine'], res=4, grain=tuple(d.normalized()), detail=1)


def withered_leaf(name, base, d, L, W, curl, twist, mat):
    """One withering leaf, single-sided (it lies on the mat and is only ever seen from above): narrow, edges rolling in, twisted along its length."""
    d = Vector(d).normalized(); up = Vector((0, 0, 1))
    side = d.cross(up).normalized(); nrm = side.cross(d).normalized()
    if nrm.z < 0: side, nrm = -side, -nrm
    b = Vector(base)
    def fn(u, v):
        w = W * (math.sin(math.pi * min(1., v * 1.04)) ** .8 + .04)
        x = (u - .5) * 2; tw = twist * v
        sd = side * math.cos(tw) + nrm * math.sin(tw); nn = nrm * math.cos(tw) - side * math.sin(tw)
        return tuple(b + d * (L * v) + sd * (x * w) + nn * (curl * v * v * L + .35 * W * x * x))
    o = sheet(name, 2, 5, fn, mat, solid=None, detail=2, grain=tuple(d), group='Main')
    me = o.data; me.update()
    if sum(p.normal.z for p in me.polygons) < 0:
        for p in me.polygons: p.flip()
        me.update()
    return o


def spread_leaves(P, R):
    """A thin single layer of withering leaves over the left two-thirds of the floor (the drying side faces the sun).
    Each leaf rests on the mat with its tip a few millimetres up and its own pitch and twist, so overlapping leaves cross instead of sharing a plane."""
    mids = []
    for _ in range(20000):
        if len(mids) == 230: break
        x = R.uniform(-.48, .3); y = R.uniform(-.26, .26)
        if x > .1 and R.random() < (x - .1) / .2: continue          # thinning out towards the edge of the spread
        if not inside(x, y, D_F + .03): continue
        if any((Vector((x, y)) - m).length < .021 for m in mids): continue
        mids.append(Vector((x, y)))
        ang = R.uniform(0, math.tau); L = R.uniform(.038, .058)
        pitch = R.uniform(.02, .1)
        d = (math.cos(ang) * math.cos(pitch), math.sin(ang) * math.cos(pitch), math.sin(pitch))
        base = Vector((x, y, 0.)) - Vector((d[0], d[1], 0.)) * (L / 2)
        base.z = Z_F + .003 + lift(base.x, base.y) + .0003
        withered_leaf('Drying_Leaf', base, d, L, R.uniform(.008, .013), R.uniform(.04, .3), R.uniform(-.9, .9), R.choice(P['leaf']))
