"""LG01 fallen giant tree bridge (work pack 2026-11-09 B-112h batch C, D5 mushroom valley): 22 x 5 x 4 m.

Three-view LG01-cand-3: a far bigger tree than FR04, fallen across the valley floor, the root plate torn up at one end, the crown
end snapped off with broken limbs, moss and shelf fungus on the bark, a walking line worn along the top of the trunk. No planks,
no rope (cand-1/2/4 had them).
Proportions from the pack's sizes, not measured off the image.

Layout (x along the tree, front -Y, origin at the centre of the footprint on the ground):
- trunk from the butt at x -6.4 (1.0 m radius) to the break at x 8.3 (0.52 m), lying on the two valley rims and bowed up over the
  middle: from x -3.4 to 4.4 its underside is clear of z 0 (up to 0.75 m), the ravine the level puts under it;
- the walking line: the top of the trunk worn flat and smooth (about 0.84 m wide, bark gone, silver-brown wood, moss creeping in
  from the edges), 2.1 m at the butt, 2.0 m over the middle, 1.0 m at the break;
- both ends meet the ground in a slope of earth: at the root end the half of the root plate that tore away lies as a heap of soil
  and roots up to the butt (x -11 to -6.4, 26 deg), at the crown end a bank of earth and stones runs up to the break (x 11 to 8.3,
  21 deg);
- the root flare (as LG01-cand-3 draws it): the butt flares into a mass of thick twisting roots (20 a side) that pour down over the
  earth heap to both sides and back into the ground, crossing and sometimes arching clear; behind the butt a tangle of medium
  roots torn out of the ground rises back and out (2.4-3.1 m) and ends snapped; small roots and stones between; the path goes up
  the middle of the heap, the roots keeping 0.62 m plus their radius off its line;
- four broken limbs and a few snapped branches spread sideways from the crown end; shelf fungus in tiers on the lower flanks.
Colours: moss #3F5A2E, dark bark #2B2018 (the C-batch language).
"""
import math, random
import bmesh
from mathutils import Vector, Matrix, noise
from ti_core import S, socket, mesh, surface
import fr_parts as FP
import fr_mats as fm
from cr_parts import set_attr_list
from fr_bridge import _bark_ring, _cap
from fr_arch import collision_tube

X_B, X_E = -6.4, 8.3            # butt face, break
HW = .42                        # half width of the worn walking band
XW, YW, ZH = 11., 2.45, 4.      # half length, half width (inside the 5 m), height limit


def t_of(x): return max(0., min(1., (x - X_B) / (X_E - X_B)))
def r_at(x): return .52 + .38 * (1 - t_of(x)) ** 1.15 + .1 * max(0., 1 - (x - X_B) / 1.3) ** 2
def base_at(x): return .15 + .6 * math.exp(-((x - .3) / 4.6) ** 2)
def cy_at(x): return .1 * math.sin(x * .23 + .4)
def cz_at(x): return base_at(x) + r_at(x)
def deck_at(x):
    r = r_at(x); return cz_at(x) + math.sqrt(max(r * r - HW * HW, .01))


SOFT = .06


def flatten(z, deck):
    """Everything above the deck is laid onto it with a soft shoulder: the band is slightly crowned, its edges rounded off."""
    if z <= deck - SOFT: return z
    return deck - SOFT + SOFT * math.tanh((z - deck + SOFT) / SOFT)


def palette():
    P = FP.palette()
    P['worn'] = fm.worn_top('Trunk_Worn_Top')
    P['fungus'] = fm.bracket_fungus('Shelf_Fungus')
    P['trod'] = fm.forest_earth('Heap_Earth', moss=1.0, trodden=.3)
    return P


# ------------------------------------------------------------------ trunk
def splinter_len(k, nv, R):
    th = 2 * math.pi * k / nv
    if math.sin(th) > .5: return .02                       # the top (the walking band) broke off clean, the bank covers it
    v = max(0., noise.noise(Vector((math.cos(th) * 2.3, math.sin(th) * 2.3, 7.1)))) ** 1.4
    return .12 + 1.1 * v


def trunk(P):
    R = random.Random('LG01_trunk'); so = Vector((R.uniform(-50, 50), R.uniform(-50, 50), R.uniform(-50, 50)))
    nv = 96; xs = []; x = X_B
    while x < X_E - .04: xs.append(x); x += .09
    xs.append(X_E)
    ext = [X_E + .06 * i for i in range(1, 12)]
    L = [splinter_len(k, nv, R) for k in range(nv)]
    L = [(L[k - 1] + 2 * L[k] + L[(k + 1) % nv]) / 4 for k in range(nv)]      # splinters a few vertices wide
    knots = [(-4.6, 200, .12), (-1.2, 330, .1), (1.9, 215, .09), (3.6, 310, .08), (-2.8, 25, .06), (5.2, 160, .07)]
    verts, flat_v, attr_b, attr_a = [], [], [], []
    for x in xs + ext:
        xc = min(x, X_E); s = x - X_B; r, cy, cz, deck = r_at(xc), cy_at(xc), cz_at(xc), deck_at(xc)
        for k in range(nv):
            th = 2 * math.pi * k / nv
            f, F, bump = _bark_ring(so, s, r, th, plates=2.4, fiss=.16, lump=.04)
            for xk, tk, a in knots:
                dt = (th - math.radians(tk) + math.pi) % math.tau - math.pi
                f += a * math.exp(-((x - xk) ** 2 + (dt * .9) ** 2) / .05)
            if x > X_E:
                f *= max(.04, 1 - (x - X_E) / L[k])
            y = cy + math.cos(th) * r * f; z = cz + math.sin(th) * r * f
            zf = flatten(z, deck)
            on = zf >= deck - .022 and x <= X_E
            if zf != z:
                y = cy + math.cos(th) * r * (1 + .4 * bump) if abs(math.cos(th)) * r < HW + .05 else y
                yr = y - cy
                zf -= .006 * max(0., 1 - (yr / HW) ** 2) - .003 * noise.noise(Vector((x * 1.3, yr * 2.5, 3.)))
            verts.append((x, y, zf)); flat_v.append(on or x > X_E)
            attr_b.append((s, th * r, F)); attr_a.append((x, y - cy, 1. if on else 0.))
    nr = len(xs) + len(ext)
    faces, mat_i = [], []
    for i in range(nr - 1):
        for k in range(nv):
            a = i * nv + k; b = i * nv + (k + 1) % nv
            faces.append((a, b, b + nv, a + nv)); mat_i.append(1 if all(flat_v[v] for v in (a, b, b + nv, a + nv)) else 0)
    n = _cap(verts, faces, attr_b, attr_a, [(nr - 1) * nv + k for k in range(nv)], (ext[-1] + .03, cy_at(X_E), cz_at(X_E)), 2, 'x')
    mat_i += [1] * n
    n = _cap(verts, faces, attr_b, attr_a, list(range(nv))[::-1], (X_B, cy_at(X_B), cz_at(X_B)), 5, 'x', lambda f: Vector((-.16 * (1 - f * f), 0, 0)))
    mat_i += [0] * n
    o = mesh('Trunk', verts, faces, P['bark'][0], smooth=True, grain='x')
    o.data.materials.append(P['worn'])
    for p, m in zip(o.data.polygons, mat_i): p.material_index = m
    set_attr_list(o, 'bark', attr_b); set_attr_list(o, 'adze', attr_a)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    return o


# ------------------------------------------------------------------ earth at both ends
def toe(u, k=.12):
    u = max(0., min(1., u))
    return (u * u / (2 * k) if u < k else u - k / 2) / (1 - k / 2)


def side_fall(d, flat, run):
    if d <= flat: return 1.
    if d >= flat + run: return 0.
    return .5 * (1 + math.cos(math.pi * (d - flat) / run))


def lump(a, b, s):
    return .035 * noise.noise(Vector((a * 1.1 + s, b * 1.1, s))) + .015 * noise.noise(Vector((a * 3.3, b * 3.3 + s, 2 * s)))


def root_heap_h(a, b):
    """Root end: the torn half of the root plate as a heap of soil and roots, a path up its crest to the butt; a bank under the butt."""
    D = deck_at(X_B); cy = cy_at(X_B)
    d = abs(b - cy)
    if a <= X_B: crest = D * toe((a + XW) / (X_B + XW))
    else: crest = deck_at(a) - .02 - 2.5 * max(0., a - X_B - .35)
    h = crest * side_fall(d, .55, 1.85)
    if d > .5:                                   # off the path the torn soil is clods and hollows, not a smooth cone
        clods = 2.4 * lump(a, b, 1.7) + .06 * noise.noise(Vector((a * .7, b * .7, 9.1))) + .07 * noise.noise(Vector((a * 2.3, b * 2.3, 5.7))) + .03 * noise.noise(Vector((a * 6., b * 6., 3.3)))
        h += clods * min(1., (d - .5) / .45) * min(1., crest)
    xa = max(X_B, min(a, X_B + 3.2))           # the bank sits under the butt only: r_at() keeps growing past the butt, so it is held there and faded out
    bank = (base_at(xa) + .35 * r_at(xa)) * side_fall(abs(b - cy_at(xa)), r_at(xa) * .8, 1.3) * (1 - smooth(-4.4, -3.4, a)) * smooth(X_B - 1.4, X_B - .2, a)
    return max(.004, max(h, bank) * edge_fade(a, b, -XW, -3.3))


def edge_fade(a, b, x0, x1):
    """1 inside, 0 on the mound's outline: the heap runs out into the ground instead of ending in a low wall round a rectangle."""
    d = min(YW - abs(b) + .35, a - x0 + .3, x1 - a + .3)          # the mapped outline rounds the sides; fade the ends
    return smooth(0., .55, d)


def crown_heap_h(a, b):
    D = deck_at(X_E); cy = cy_at(X_E)
    d = abs(b - cy)
    if a >= X_E: crest = D * toe((XW - a) / (XW - X_E))
    else: crest = deck_at(a) - .02 - 2.5 * max(0., X_E - .35 - a)
    h = crest * side_fall(d, .55, 1.55)
    if d > .5: h += lump(a, b, 4.2) * min(1., (d - .5) / .4) * min(1., crest + .2)
    xa = min(X_E, max(a, X_E - 3.4))
    bank = (base_at(xa) + .35 * r_at(xa)) * side_fall(abs(b - cy_at(xa)), r_at(xa) * .8, 1.2) * smooth(4.4, 5.4, a) * (1 - smooth(X_E + .2, X_E + 1.4, a))
    return max(.004, max(h, bank) * edge_fade(a, b, 4.3, XW))


def smooth(e0, e1, x):
    t = max(0., min(1., (x - e0) / (e1 - e0))); return t * t * (3 - 2 * t)


def outline_map(x_out, x_in, seed):
    """(a, b), b in [-1, 1] -> plan (x, y): the heap's half width rounds off to the outer end (a quarter ellipse over its outer 45 %)
    and a little towards the trunk end, and wanders; no rectangle on the ground."""
    span = x_in - x_out
    def mp(a, b):
        u = (a - x_out) / span
        w = math.sqrt(max(0., 1 - (1 - min(1., u / .45)) ** 2)) * (.55 + .45 * math.sqrt(max(0., 1 - (1 - min(1., (1 - u) / .12)) ** 2)))
        w *= .9 + .08 * noise.noise(Vector((a * .45, seed, 1.))) + .03 * noise.noise(Vector((a * 1.7, seed, 3.)))
        return (a, b * YW * max(.04, min(1., w)) + cy_at(a) * (1 - abs(b)))
    return mp


def heaps(P):
    m1 = outline_map(-XW, -3.3, 2.); m2 = outline_map(XW, 4.3, 5.)
    FP.mound('Root_Heap', lambda a, b: max(.004, root_heap_h(*m1(a, b)) * smooth(0., .12, 1 - abs(b))), -XW, -3.3, -1., 1., P['trod'], nx=84, ny=46, mapfn=m1)
    FP.mound('Crown_Heap', lambda a, b: max(.004, crown_heap_h(*m2(a, b)) * smooth(0., .12, 1 - abs(b))), XW, 4.3, -1., 1., P['trod'], nx=72, ny=46, mapfn=m2)


# ------------------------------------------------------------------ root plate wings
def ring_pt(x, phi, rho, cy, cz):
    return (x, cy + math.cos(phi) * rho, cz + math.sin(phi) * rho)


GAP = .86                     # half width of the gap the path goes up through (from the trunk line)


def clampv(q, m):
    """keep a tube point (and its radius m) inside the 22 x 5 x 4 m box"""
    return (max(-XW + m, q[0]), max(-YW + m, min(YW - m, q[1])), min(ZH - m - .12, q[2]))


PATH_CLEAR = .62                # roots keep this far (plus their radius) from the path line on the heap


def heap_top(x, y):
    return max(0., root_heap_h(x, y)) if x < -3.3 else 0.


def flare_root(P, R, side, phi_d, back, out, rad0, arch, made, name='Root_Flare', emb=.5, snap=False):
    """One root of the flare: leaves the butt at angle phi_d (from the horizontal outward, up +), pours down over the heap toward
    a ground point `back` m behind the butt and `out` m to the side, half sunk in the earth, sometimes arching clear of it."""
    cy, cz, r = cy_at(X_B), cz_at(X_B), r_at(X_B)
    ph = math.radians(phi_d); c, sn = math.cos(ph), math.sin(ph)
    p0 = Vector((X_B + .75, cy + side * c * r * .55, cz + sn * r * .55))
    p1 = Vector((X_B + .05, cy + side * c * r * 1.05, cz + sn * r * 1.05))
    y1 = c * r * 1.05; yE = max(y1 + .2, out); n = 7
    pts, rr = [p0, p1], [rad0 * 1.3, rad0 * 1.15]
    wob = R.uniform(-.25, .25); so = R.uniform(0, 50)
    for k in range(1, n + 1):
        t = k / n
        x = X_B - .05 - back * t ** 1.05
        yy = y1 + (yE - y1) * (1 - (1 - t) ** 2) + wob * math.sin(math.pi * t) + .08 * noise.noise(Vector((t * 3., so, 1.)))
        y = cy + side * max(PATH_CLEAR + rad0 + .05, yy)
        rad = rad0 * (1.05 - .8 * t)
        g = heap_top(x, y)
        zs = g + rad * (1 - emb * 2) * (1 if t < .999 else 0) + rad * .2
        zt = p1.z + (g - p1.z) * (3 * t * t - 2 * t ** 3) ** .8          # out of the butt, then down onto the earth
        z = max(zs, zt * (1 - t) + zs * t) + arch * math.sin(math.pi * min(1., t * 1.15))
        if k == n and not snap: z = min(z, rad * .2)                         # the tip goes into the ground
        pts.append(Vector((x, y, z))); rr.append(rad)
    if snap:                                                               # torn off short of the ground: the end lifts a little
        pts[-1].z = max(pts[-1].z, heap_top(pts[-1].x, pts[-1].y) + rr[-1] * 1.4 + .05)
    pts = [clampv(tuple(q), m * 1.15 + .05) for q, m in zip(pts, rr)]
    FP.sweep(name, pts, rr, R.choice(P['bark']), aspect=.78, step=.07, fiss=.26, twist=R.uniform(.3, .8), seed=R.randrange(999),
             tip=(P['tip'], .3) if snap else None)
    made.append(pts)
    return pts, rr


def root_wings(P, R):
    """The root flare (LG01-cand-3): thick twisting roots pour out of the butt and down over the heap to both sides into the ground,
    crossing and arching; a few torn roots rise behind the butt and end snapped and forked; small roots and stones between."""
    cy, cz, r = cy_at(X_B), cz_at(X_B), r_at(X_B)
    made = []; S['lg01_lift'] = []
    for side in (1, -1):
        Rf = random.Random('LG01_flare_%d' % side)
        # the big roots: a fan round the butt, from its top flank down to under it
        n = 20
        for k in range(n):
            phi = -62 + 102 * (k + Rf.uniform(.2, .8)) / n
            u = (phi + 62) / 102                                               # 0 low on the butt .. 1 high on its flank
            back = Rf.uniform(1.2, 2.2) + 2.6 * u * Rf.uniform(.6, 1.1)        # roots from higher up run further back down the heap
            out = Rf.uniform(1.3, 2.3) - .6 * u
            arch = Rf.uniform(.05, .3) if Rf.random() < .35 else 0.
            flare_root(P, Rf, side, phi, back, out, Rf.uniform(.17, .28), arch, made, snap=Rf.random() < .25)
        # roots torn up out of the ground behind the butt: a tangle of medium roots rising back, up and out at different angles, snapped
        for k in range(7):
            phi = math.radians(Rf.uniform(0, 42)); c, sn = math.cos(phi), math.sin(phi)
            rad = Rf.uniform(.1, .17)
            p0 = Vector((X_B + .6, cy + side * c * r * .6, cz + sn * r * .6))
            p1 = Vector((X_B + .0, cy + side * c * r * 1.03, cz + sn * r * 1.03))
            back = Rf.uniform(.9, 2.6); outw = Rf.uniform(.3, 1.2); top = Rf.uniform(2.4, 3.1)
            bend = Rf.uniform(-.25, .25)
            p2 = Vector((X_B - back * .35, p1.y + side * (outw * .35 + bend), p1.z + (top - p1.z) * .55))
            p3 = Vector((X_B - back * .7, p1.y + side * (outw * .7 - bend * .5), top))
            p4 = Vector((X_B - back, p1.y + side * outw, top + Rf.uniform(-.05, .15)))      # keeps reaching: no hooked-over horn tip
            pts = [p0, p1, p2, p3, p4]; rr = [rad * 1.3, rad * 1.05, rad * .7, rad * .42, rad * .2]
            kp, kr = [pts[0], pts[1]], [rr[0], rr[1]]                  # kinks: a torn root bends at knots, it is not one smooth tentacle curve
            for a_, b_, ra, rb in zip(pts[1:], pts[2:], rr[1:], rr[2:]):
                m_ = a_.lerp(b_, Rf.uniform(.4, .6)) + Vector((Rf.uniform(-.09, .09), Rf.uniform(-.09, .09), Rf.uniform(-.06, .06)))
                kp += [m_, b_]; kr += [(ra + rb) / 2, rb]
            pts, rr = kp, kr
            pts = [clampv(tuple(q), m * 1.15 + .05) for q, m in zip(pts, rr)]
            if min(abs(q[1] - cy) for q in pts[2:]) < PATH_CLEAR + .2: continue
            FP.sweep('Root_Torn_Up', pts, rr, Rf.choice(P['bark']), aspect=.85, step=.06, fiss=.26, twist=Rf.uniform(.4, .9), seed=Rf.randrange(999),
                     tip=(P['tip'], .3) if Rf.random() < .4 else None, ground=None)
            made.append(pts); S['lg01_lift'].append((pts, rr))
            # the torn end splits into thinner roots, each snapped or trailing into hair: a torn root is a brush, not a tusk
            q3, q4 = Vector(pts[-3]), Vector(pts[-1]); fw = (q4 - q3).normalized()
            for f in range(Rf.randint(2, 4)):
                a_ = q3.lerp(q4, Rf.uniform(.25, .85)); dv = (fw + Vector((Rf.uniform(-.8, .5), side * Rf.uniform(-.3, .9), Rf.uniform(-.7, .5)))).normalized()
                L = Rf.uniform(.3, .7); m_ = a_ + dv * L * .5 + Vector((0, 0, Rf.uniform(-.05, .08))); e_ = a_ + dv * L + Vector((0, 0, -Rf.uniform(0., .2)))
                r0 = rad * Rf.uniform(.22, .32)
                FP.sweep('Root_Torn_Fork', [tuple(a_), tuple(m_), tuple(e_)], [r0, r0 * .6, r0 * .22], Rf.choice(P['bark']), step=.04, fiss=.2,
                         seed=Rf.randrange(999), tip=(P['tip'], .12) if Rf.random() < .5 else None, ground=None, detail=1)
        # small roots between the big ones, branching off them into the earth
        for k in range(22):
            pts = Rf.choice(made[-19:])
            if len(pts) < 5: continue
            j = Rf.randint(2, len(pts) - 2); a = Vector(pts[j])
            if a.z > 1.4: continue                                         # from low on the flare only: no poles from up high
            d = Vector((-Rf.uniform(.1, .7), side * Rf.uniform(-.2, .7), 0.)).normalized() * Rf.uniform(.5, 1.2)
            b = a + d; b.y = cy + side * max(PATH_CLEAR + .1, side * (b.y - cy))
            g = heap_top(b.x, b.y); b.z = g * .9
            m = a.lerp(b, .5); m.z = max(heap_top(m.x, m.y) + .03, (a.z + b.z) / 2 + Rf.uniform(-.05, .08))
            w = Rf.uniform(.04, .08)
            q = [clampv(tuple(x), ww * 1.15 + .05) for x, ww in zip((a, m, b), (w, w * .7, w * .35))]
            FP.sweep('Root_Small', q, [w, w * .7, w * .35], Rf.choice(P['bark']), step=.05, fiss=.16, seed=Rf.randrange(999), detail=1)
        # stones held between the roots on the heap
        for k in range(6):
            x = X_B - Rf.uniform(.6, 3.5); y = cy + side * Rf.uniform(.95, 2.0); sz = Rf.uniform(.18, .34)
            g = heap_top(x, y)
            FP.pebble('Flare_Stone', (x, y, max(g - .03, sz * .5 * 1.12)), sz, Rf.choice(P['stone']), seed=Rf.randrange(999), flat=.55)
    # dressing as in LG01-cand-3: moss on the tops of the roots, ferns, grass and litter in the crotches, moss beards hanging
    Rd = random.Random('LG01_flare_dress')
    big = [q for q in made if len(q) >= 7]
    for i in range(46):                                                    # moss colonies on the upper sides of the big roots
        pts = Rd.choice(big); j = Rd.randint(1, len(pts) - 3); q = Vector(pts[j]).lerp(Vector(pts[j + 1]), Rd.random())
        hit = FP.snap((q.x, q.y, q.z + .6), (0, 0, -1))
        if not hit or hit[1].z < .45 or abs(hit[0].z - q.z) > .35: continue
        FP.moss_patch('Flare_Moss', tuple(hit[0]), tuple(hit[1]), Rd.uniform(.1, .2), P['moss'], seed=500 + i, snap_each=True, flat=.9)
    for i in range(60):                                                    # ferns, grass and leaf litter between the roots, off the path
        side = Rd.choice((-1, 1)); x = X_B - Rd.uniform(.3, 4.6); y = cy + side * Rd.uniform(PATH_CLEAR + .35, 2.15)
        hit = FP.snap((x, y, 4.5), (0, 0, -1))
        if not hit or hit[1].z < .55 or hit[0].z < .3: continue
        if hit[0].z - heap_top(hit[0].x, hit[0].y) > .1: continue         # on the earth between the roots, never on a root's top
        q = tuple(hit[0]); k = Rd.random()
        if k < .35 and abs(y) < YW - .45:
            FP.fern('Flare_Fern', q, P['fern'], Rd, n=Rd.randint(5, 8), L=Rd.uniform(.22, .4), out=(-.3, side, 0), detail=1, up_bias=.55, spread=1.3)
        elif k < .7:
            FP.grass_tuft('Flare_Grass', q, Rd.randint(5, 10), Rd.uniform(.12, .26), P['grass'], Rd, lean=.3, detail=1, spread=.05)
        else:
            FP.grass_tuft('Flare_Litter', q, Rd.randint(3, 6), Rd.uniform(.05, .09), P['litter'], Rd, lean=.6, detail=1, spread=.08)
    torn = [q for q, _ in S['lg01_lift']] + [q for q in big if max(v[2] for v in q) > 2.]
    for i in range(34):                                                    # moss beards hanging off the torn and arching roots
        pts = Rd.choice(torn); j = Rd.randint(1, len(pts) - 2); q = Vector(pts[j]).lerp(Vector(pts[j + 1]), Rd.random())
        g = heap_top(q.x, q.y)
        if abs(q.y - cy) < PATH_CLEAR + .1 or q.z - g < .5: continue
        for k in range(Rd.randint(3, 5)):                              # a tuft of fine strands, not one green spike
            L = min(Rd.uniform(.1, .32), q.z - g - .1); o_ = Vector((Rd.uniform(-.05, .05), Rd.uniform(-.04, .04), 0))
            sway = Vector((Rd.uniform(-.06, .06), Rd.uniform(-.06, .06), 0))
            line = [q + o_ - Vector((0, 0, .02)), q + o_ - Vector((0, 0, L * .5)) + sway * .6, q + o_ - Vector((0, 0, L)) + sway]
            FP.sweep('Moss_Beard', [tuple(v) for v in line], [.011, .008, .003], P['moss'], step=.035, fiss=.05, nring=5, seed=Rd.randrange(999),
                     ground=None, detail=1)
    # hair roots hanging from the torn and arching roots
    Rh = random.Random('LG01_hair')
    for i in range(60):
        pts = Rh.choice(made); j = Rh.randint(1, len(pts) - 2); q = Vector(pts[j]).lerp(Vector(pts[j + 1]), Rh.random())
        g = heap_top(q.x, q.y)
        if abs(q.y - cy) < PATH_CLEAR + .1 or q.z - g < .45: continue
        L = min(Rh.uniform(.25, .65), q.z - g - .05); dx, dy = Rh.uniform(-.15, .1), Rh.uniform(-.1, .1)
        tip = (q.x + dx, max(-YW + .05, min(YW - .05, q.y + dy)), max(.05, q.z - L))
        mid = ((q.x + tip[0]) / 2 + Rh.uniform(-.06, .06), (q.y + tip[1]) / 2, (q.z + tip[2]) / 2 + .05)
        FP.sweep('Hair_Root', [tuple(q), mid, tip], [.03, .02, .008], P['tip'] if Rh.random() < .3 else Rh.choice(P['bark']), step=.05, fiss=.1, nring=6,
                 seed=Rh.randrange(999), ground=None, detail=1)


# ------------------------------------------------------------------ crown end
LIMBS = ((4.7, 1, 18, 2.15, 1.5, .3), (5.9, -1, 22, 2.2, 1.9, .27), (6.9, 1, 30, 2.1, 2.3, .24), (7.7, -1, 12, 2.0, 1.1, .22))


def limb_pts(xl, side, phi_d, reach, rise):
    cy, cz, r = cy_at(xl), cz_at(xl), r_at(xl)
    phi = math.radians(phi_d if side > 0 else 180 - phi_d)
    p0 = (xl - .25, cy + math.cos(phi) * r * .45, cz + math.sin(phi) * r * .45)
    p1 = (xl + .2, cy + math.cos(phi) * (r + .2), cz + math.sin(phi) * (r + .2) + .1)
    p2 = (xl + .75, cy + side * (r + reach * .55), cz + rise * .55)
    p3 = (xl + 1.15, cy + side * (r + reach), cz + rise)
    return [(q[0], max(-YW + .1, min(YW - .1, q[1])), min(ZH - .2, q[2])) for q in (p0, p1, p2, p3)]


def crown(P, R):
    for i, (xl, side, phi_d, reach, rise, rad) in enumerate(LIMBS):
        pts = limb_pts(xl, side, phi_d, reach, rise)
        FP.sweep('Limb', pts, [rad * 1.2, rad, rad * .8, rad * .62], R.choice(P['bark']), step=.07, fiss=.18, seed=R.randrange(999),
                 tip=(P['worn'], .12), ground=None)
        for j in range(2):                                   # snapped side branches off each limb
            q = Vector(pts[2]).lerp(Vector(pts[3]), .2 + .5 * j)
            d = Vector((R.uniform(.2, .6), side * R.uniform(.1, .5), R.uniform(.3, .8))).normalized() * R.uniform(.5, .9)
            e = q + d; e.y = max(-YW + .06, min(YW - .06, e.y)); e.z = min(ZH - .1, e.z)
            FP.sweep('Branch_Snapped', [tuple(q), tuple(q.lerp(e, .5) + Vector((0, 0, .05))), tuple(e)], [rad * .4, rad * .3, rad * .22], R.choice(P['bark']),
                     step=.05, fiss=.14, nring=12, seed=R.randrange(999), tip=(P['worn'], .06), ground=None, detail=1)
    for side in (1, -1):                                    # two short broken limbs out of the break itself
        cy, cz, r = cy_at(X_E), cz_at(X_E), r_at(X_E)
        pts = [(X_E - .3, cy + side * r * .3, cz - .1), (X_E + .4, cy + side * (r + .3), cz - .05), (X_E + .9, cy + side * (r + .75), cz + .25)]
        FP.sweep('Limb_End', pts, [.2, .16, .12], R.choice(P['bark']), step=.06, fiss=.16, seed=R.randrange(999), tip=(P['worn'], .1), ground=None)


def crown_dressing(P):
    """The crown end is not bare wood: thin twigs still on the limb ends, moss along the limbs' upper sides, dead sticks fallen on the bank."""
    Rc = random.Random('LG01_crown_dress')
    for i, (xl, side, phi_d, reach, rise, rad) in enumerate(LIMBS):
        pts = [Vector(q) for q in limb_pts(xl, side, phi_d, reach, rise)]
        axis = (pts[3] - pts[2]).normalized()
        for j in range(Rc.randint(4, 6)):                  # twigs off the outer half of the limb, forking once
            q = pts[1].lerp(pts[2], Rc.uniform(.4, 1.)) if j < 2 else pts[2].lerp(pts[3], Rc.uniform(.2, .95))
            d = (axis * Rc.uniform(.3, .8) + Vector((Rc.uniform(-.4, .4), side * Rc.uniform(-.2, .6), Rc.uniform(.1, .9)))).normalized()
            L = Rc.uniform(.6, 1.15); e = q + d * L
            e.y = max(-YW + .05, min(YW - .05, e.y)); e.z = min(ZH - .08, e.z)
            m = q.lerp(e, .5) + Vector((0, 0, Rc.uniform(-.03, .05)))
            FP.sweep('Limb_Twig', [tuple(q), tuple(m), tuple(e)], [rad * .24, rad * .15, rad * .06], Rc.choice(P['bark']),
                     step=.04, fiss=.1, nring=8, seed=Rc.randrange(999), tip=(P['worn'], .03), ground=None, detail=1)
            f0 = q.lerp(e, Rc.uniform(.45, .7)); fd = (d + Vector((Rc.uniform(-.6, .6), Rc.uniform(-.6, .6), Rc.uniform(0, .5)))).normalized()
            f1 = f0 + fd * L * Rc.uniform(.3, .5); f1.y = max(-YW + .05, min(YW - .05, f1.y)); f1.z = min(ZH - .08, f1.z)
            FP.sweep('Limb_Twig', [tuple(f0), tuple(f0.lerp(f1, .5)), tuple(f1)], [rad * .11, rad * .07, rad * .035], Rc.choice(P['bark']),
                     step=.03, fiss=.08, nring=6, seed=Rc.randrange(999), ground=None, detail=1)
        for k in range(Rc.randint(3, 5)):                  # moss on the upper side of the limb, patchy
            t = Rc.uniform(.05, .85); q = pts[0].lerp(pts[1], t * 3) if t < .33 else (pts[1].lerp(pts[2], (t - .33) * 3) if t < .66 else pts[2].lerp(pts[3], (t - .66) * 3))
            hit = FP.snap((q.x + Rc.uniform(-.05, .05), q.y + Rc.uniform(-.05, .05), q.z + rad * 3), (0, 0, -1))
            if not hit or abs(hit[0].z - (q.z + rad)) > rad * .6 or hit[1].z < .4: continue
            FP.moss_patch('Limb_Moss', tuple(hit[0]), tuple(hit[1]), Rc.uniform(.06, .12), P['moss'], seed=1300 + i * 10 + k, snap_each=True, flat=.85)
    def bank(x, y):
        hit = FP.snap((x, y, 4.5), (0, 0, -1))
        return hit if hit and abs(hit[0].z - crown_heap_h(x, y)) < .1 and hit[1].z > .4 else None
    nb = {'try': 0, 'hit': 0}
    for i in range(240):                                   # the bank: moss spreading, ferns and grass clumps, litter, off the path
        a = Rc.uniform(4.7, XW - .25); b = Rc.uniform(-YW + .2, YW - .2)
        if abs(b - cy_at(a)) < .5: continue
        nb['try'] += 1; hit = bank(a, b)
        if not hit: continue
        nb['hit'] += 1
        q = tuple(hit[0]); k = Rc.random(); off = abs(b - cy_at(a))
        if k < .3: FP.moss_patch('Bank_Moss', q, tuple(hit[1]), Rc.uniform(.15, .3), P['moss'], seed=1500 + i, snap_each=True, flat=.9)
        elif k < .47 and off > .65 and q[2] > .2: FP.fern('Bank_Fern', q, P['fern'], Rc, n=Rc.randint(6, 9), L=Rc.uniform(.28, .45), out=(0, 1 if b > cy_at(a) else -1, 0), detail=1, up_bias=.5, spread=1.4)
        elif k < .77: FP.grass_tuft('Bank_Grass', q, Rc.randint(10, 18), Rc.uniform(.2, .38), P['grass'] if Rc.random() < .7 else P['litter'], Rc, lean=.3, detail=1, spread=.07)
        else: FP.grass_tuft('Bank_Litter', q, Rc.randint(4, 7), Rc.uniform(.05, .09), P['litter'], Rc, lean=.7, detail=1, spread=.1)
    print('CROWN_BANK', nb)
    for i in range(16):                                    # dead sticks fallen on the crown bank, off the path
        a = Rc.uniform(4.9, XW - .6); b = Rc.uniform(-YW + .3, YW - .3)
        if abs(b - cy_at(a)) < .55: continue
        ang_ = Rc.uniform(0, math.tau); L = Rc.uniform(.35, .9); r_ = Rc.uniform(.012, .028); line = []
        for k in range(4):
            x = a + math.cos(ang_) * L * k / 3; y = max(-YW + .05, min(YW - .05, b + math.sin(ang_) * L * k / 3))
            hit = FP.snap((x, y, 4.5), (0, 0, -1))
            if not hit or abs(hit[0].z - crown_heap_h(x, y)) > .08: line = []; break
            line.append((hit[0].x, hit[0].y, hit[0].z + r_ * .4))
        if line:
            FP.sweep('Fallen_Stick', line, [r_, r_ * .85, r_ * .6], Rc.choice(P['bark']), step=.04, fiss=.1, nring=6, seed=Rc.randrange(999),
                     tip=(P['worn'], .02), ground=None, detail=1)


# ------------------------------------------------------------------ growth
def shelf_fungus(P, c, n_out, R, size):
    """A shelf: a flattened half disc standing out level from the bark, domed on top, attachment at the bark."""
    out = Vector((n_out.x, n_out.y, 0)).normalized(); along = Vector((-out.y, out.x, 0))
    Rr = size; w = size * R.uniform(1.15, 1.45); th = .018 + size * .08
    def fn(u, v):          # u: attachment -> rim, v: across (-1 .. 1)
        a = (v - .5) * math.pi
        rad = Rr * u * (.92 + .08 * math.sin(v * 9.))
        p = Vector(c) + out * (math.cos(a) * rad - .03) + along * (math.sin(a) * w * u)
        p.z += th * (1 - u * u) * .7 - .01 * u
        return tuple(p)
    o = surface('Shelf_Fungus', 6, 9, lambda u, v: fn(u, v), P['fungus'], solid=th * .7, detail=1, grain='z')
    set_attr_list(o, 'adze', [(i / 6, 0., 0.) for j in range(10) for i in range(7)])
    return o


def growth(P):
    Rg = random.Random('LG01_growth')
    # shelf fungus in tiers on the lower flanks, both sides
    for i in range(11):
        x = Rg.uniform(X_B + 1.2, X_E - .8); side = Rg.choice((-1, 1))
        cy, cz, r = cy_at(x), cz_at(x), r_at(x)
        phi = math.radians(Rg.uniform(-25, 15)); yv = math.cos(phi) * side
        for t in range(Rg.randint(2, 4)):
            z = cz + math.sin(phi) * r * .6 - t * Rg.uniform(.11, .16)
            hit = FP.snap((x + Rg.uniform(-.15, .15), cy + side * (r + .8), z), (0, -side, 0))
            if not hit or hit[0].z < .15: continue
            shelf_fungus(P, tuple(hit[0]), hit[1], Rg, Rg.uniform(.09, .2) * (1 - .2 * t))
    # moss on the upper flanks below the worn band (not on the band), thicker on the shaded +Y side
    placed = []
    for i in range(60):
        x = Rg.uniform(X_B + .3, X_E - .2); side = 1 if Rg.random() < .62 else -1
        cy, cz, r = cy_at(x), cz_at(x), r_at(x)
        z = cz + r * Rg.uniform(.05, .6)
        hit = FP.snap((x, cy + side * (r + .6), z), (0, -side, 0))
        if not hit or any((hit[0] - q).length < .4 for q in placed) or hit[0].z > deck_at(x) - .12: continue
        placed.append(hit[0].copy())
        FP.moss_patch('Trunk_Moss', tuple(hit[0]), tuple(hit[1]), Rg.uniform(.12, .22), P['moss'], seed=i, snap_each=True, flat=.8)
    # on the heaps: ferns, grass and leaf litter off the path, stones bedded in the slopes and at the valley rims
    for i in range(150):
        root = i < 85
        a = Rg.uniform(-XW + .3, -3.7) if root else Rg.uniform(4.6, XW - .3)
        b = Rg.uniform(-YW + .25, YW - .25)
        if abs(b - cy_at(a)) < .75: continue
        h = root_heap_h(a, b) if root else crown_heap_h(a, b)
        if h < .02: continue
        hit = FP.snap((a, b, h + 1.), (0, 0, -1))
        if not hit or hit[1].z < .5 or hit[0].z - h > .08: continue     # on the heap's earth, not on a root lying over it
        q = tuple(hit[0]); k = Rg.random()
        if k < .3 and h > .25 and abs(b) < YW - .45: FP.fern('Heap_Fern', q, P['fern'], Rg, n=7, L=Rg.uniform(.25, .4), out=(0, 1 if b > 0 else -1, 0), detail=1, up_bias=.5, spread=1.4)
        elif k < .7: FP.grass_tuft('Heap_Grass', q, Rg.randint(6, 11), Rg.uniform(.14, .28), P['grass'] if Rg.random() < .7 else P['litter'], Rg, lean=.3, detail=1, spread=.04)
        elif k < .85 or not root:
            sz = Rg.uniform(.16, .4)
            FP.pebble('Heap_Stone', (q[0], q[1], max(q[2] - .02, sz * .5 * 1.12)), sz, Rg.choice(P['stone']), seed=Rg.randrange(999), flat=.5)
        else:                                    # stones half buried in the torn soil, a pair or three together
            for t in range(Rg.randint(2, 3)):
                sz = Rg.uniform(.1, .22); qx, qy = q[0] + Rg.uniform(-.25, .25), q[1] + Rg.uniform(-.2, .2)
                FP.pebble('Heap_Stone', (qx, qy, max(root_heap_h(qx, qy) - sz * .25, sz * .5 * 1.12)), sz, Rg.choice(P['stone']), seed=Rg.randrange(999), flat=.55)
    path_dressing(P); path_dressing(P, crown=True); crown_dressing(P)
    for x in (-3.5, -3.75, 4.5, 4.8):                         # rim stones where the ground drops away under the trunk
        for side in (-1, 1):
            y = cy_at(x) + side * Rg.uniform(.9, 1.6)
            sz = Rg.uniform(.35, .5)
            FP.pebble('Rim_Stone', (x + Rg.uniform(-.15, .15), y, sz * .45 * 1.12), sz, Rg.choice(P['stone']), seed=Rg.randrange(999), flat=.45)


# ------------------------------------------------------------------ collision
def path_dressing(P, crown=False):
    """The path up the root heap is trodden earth, not a bare slope: flat stones bedded flush in it, a few thin roots half buried
    across it (tops 2 cm proud, nothing to trip a 0.3 m step), moss creeping in and leaf litter drifted along both edges."""
    Rp = random.Random('LG01_path_crown' if crown else 'LG01_path')
    hfn = crown_heap_h if crown else root_heap_h
    def span(): return Rp.uniform(5.0, XW - .9) if crown else Rp.uniform(-XW + .9, -3.7)
    def ground(x, y):
        hit = FP.snap((x, y, 4.5), (0, 0, -1))
        if not hit: return None
        g = hfn(x, y)
        return hit if abs(hit[0].z - g) < .06 else None                 # the heap's own surface, not a root or a stone over it
    for i in range(16 if crown else 26):                                # flush stepping stones in the trodden line
        a = span(); b = cy_at(a) + Rp.uniform(-.38, .38); hit = ground(a, b)
        if not hit or hit[0].z < .3: continue
        size = Rp.uniform(.09, .17); sz = size * .32; n = Vector(hit[1]).normalized()
        c = Vector(hit[0]) + n * (.007 - sz * 1.12)                     # laid in the slope, not level: tilted to the ground, top 7 mm proud
        o = FP.pebble('Path_Stone', tuple(c), size, Rp.choice(P['stone']), seed=Rp.randrange(999), flat=.32)
        o.data.transform(Matrix.Translation(c) @ n.to_track_quat('Z', 'Y').to_matrix().to_4x4() @ Matrix.Translation(-c))
    for i in range(0 if crown else 6):                                 # thin roots half buried across the path
        a = -XW + 1.6 + i * 1.15 + Rp.uniform(-.3, .3); skew = Rp.uniform(-.35, .35); line = []
        for k in range(7):
            b = -.75 + .25 * k; x = a + skew * b; y = cy_at(x) + b; hit = ground(x, y)
            if hit: line.append((hit[0].x, hit[0].y, hit[0].z - .04 + .006 * Rp.random()))      # tops 0.5-1 cm proud
        if len(line) >= 4:
            FP.sweep('Path_Root', line, [.045, .045, .04], Rp.choice(P['bark']), step=.05, fiss=.12, nring=8, seed=Rp.randrange(999), ground=None, detail=1)
    for i in range(50 if crown else 70):                               # moss creeping in and litter along both edges of the path
        a = span(); side = Rp.choice((-1, 1)); b = cy_at(a) + side * Rp.uniform(.32, .72); hit = ground(a, b)
        if not hit or hit[0].z < .12: continue
        q = tuple(hit[0]); k = Rp.random()
        if k < .35: FP.moss_patch('Path_Moss', q, tuple(hit[1]), Rp.uniform(.07, .14), P['moss'], seed=900 + i, snap_each=True, flat=.9)
        elif k < .75: FP.grass_tuft('Path_Litter', q, Rp.randint(3, 6), Rp.uniform(.05, .08), P['litter'], Rp, lean=.6, detail=1, spread=.09)
        else: FP.grass_tuft('Path_Grass', q, Rp.randint(4, 8), Rp.uniform(.08, .16), P['grass'], Rp, lean=.35, detail=1, spread=.05)


def collision(V, F):
    secs = []
    for x in [X_B] + [X_B + .5 * i for i in range(1, 30) if X_B + .5 * i < X_E] + [X_E]:
        r, cy, cz, deck = r_at(x) * .97, cy_at(x), cz_at(x), deck_at(x)
        te = math.asin(max(-1., min(1., (deck - cz) / r))); span = math.pi + 2 * te; m = 12
        secs.append([(x, cy + math.cos(te - span * j / (m - 1)) * r, min(deck, cz + math.sin(te - span * j / (m - 1)) * r)) for j in range(m)])
    FP.hull_loft(V, F, secs)
    for fn, xs in ((root_heap_h, [-XW + .5 * i for i in range(10)] + [X_B]), (crown_heap_h, [X_E] + [X_E + .5 * i for i in range(1, 6)] + [XW])):
        secs = []
        for x in xs:
            H = fn(x, cy_at(x)); cy = cy_at(x)
            w = .55 + 1.85 * .5 if fn is root_heap_h else .55 + 1.55 * .5
            secs.append([(x, cy - w - .6, 0.), (x, cy + w + .6, 0.), (x, cy + .55, max(H, .01)), (x, cy - .55, max(H, .01))])
        FP.hull_loft(V, F, secs)
    cy, cz, r = cy_at(X_B), cz_at(X_B), r_at(X_B)
    for pts, rr in S.get('lg01_lift', []):                       # the torn-up roots behind the butt
        collision_tube(V, F, pts, rr)
    for (xl, side, phi_d, reach, rise, rad) in LIMBS:
        collision_tube(V, F, limb_pts(xl, side, phi_d, reach, rise), [rad * 1.2, rad, rad * .8, rad * .62])


def lg01_giant_log(P):
    R = random.Random('LG01_GiantLogBridge')
    trunk(P); heaps(P); root_wings(P, R); crown(P, random.Random('LG01_crown')); growth(P)
    socket('Socket_Path_W', (-XW, cy_at(-XW), 0), rot=(0, 0, math.pi / 2))
    socket('Socket_Path_E', (XW, cy_at(XW), 0), rot=(0, 0, -math.pi / 2))
    socket('Socket_Deck', (0, cy_at(0), deck_at(0)))
    V, F = [], []; collision(V, F)
    S['collision_mesh'] = (V, F)
    S['prop'] = dict(kind='giantlog')


def giantlog_checks(aid, check, cfg):
    """LG01: the walking line from the ground at one end over the trunk to the ground at the other, its slope and smoothness,
    a flat band wide enough, nothing in the way above it, the span clear underneath."""
    from fr_checks import _bvh
    objs = list(S['lods'][0].values()); down, up, cast = _bvh(objs)
    xs = [-XW + .1 + .05 * i for i in range(int((2 * XW - .2) / .05) + 1)]
    prof = [(x, down(x, cy_at(x))) for x in xs]
    ok = all(z is not None for _, z in prof)
    jumps = [abs(b[1] - a[1]) for a, b in zip(prof, prof[1:])] if ok else [9.]
    slopes = []
    if ok:
        for i in range(0, len(prof) - 5, 5):
            slopes.append(math.degrees(math.atan2(abs(prof[i + 5][1] - prof[i][1]), .25)))
    check('walk_line_continuous_ground_to_ground', ok and prof[0][1] <= .06 and prof[-1][1] <= .06 and max(jumps) <= .04 and max(slopes) <= 30.,
          {'end_z_m': [round(prof[0][1], 3), round(prof[-1][1], 3)] if ok else None, 'largest_5cm_step_m': round(max(jumps), 4),
           'steepest_25cm_deg': round(max(slopes), 1) if slopes else None, 'deck_z_at_butt_middle_break_m': [round(deck_at(X_B + .3), 3), round(deck_at(0), 3), round(deck_at(X_E - .2), 3)],
           'need': 'ends on the ground (<= 6 cm), no step over 4 cm in 5 cm, no 25 cm stretch steeper than 30 deg'})
    widths = []
    x = X_B + .4
    while x < X_E - .25:
        cy = cy_at(x); zc = down(x, cy); lo = hi = 0.
        while lo > -1. and (lambda z: z is not None and abs(z - zc) <= .05)(down(x, cy + lo - .01)): lo -= .01
        while hi < 1. and (lambda z: z is not None and abs(z - zc) <= .05)(down(x, cy + hi + .01)): hi += .01
        widths.append(round(hi - lo, 2)); x += .5
    check('worn_band_wide_enough', min(widths) >= .6, {'band_width_m_every_0_5m': widths, 'need_m': .6, 'note': 'within 5 cm of the centre-line height'})
    blocked = []
    for dy in (-.25, 0., .25):
        for dz in (.15, .9, 1.75):
            for (x0, z0), (x1, z1) in zip(prof[::5], prof[5::5]):
                a = Vector((x0, cy_at(x0) + dy, z0 + dz)); b = Vector((x1, cy_at(x1) + dy, z1 + dz))
                h = cast(a, b - a)
                if h and h[1] < (b - a).length - 1e-4: blocked.append([round(x0, 2), dy, dz])
    check('walk_line_clear', not blocked, {'blocked_at': blocked[:12], 'count': len(blocked), 'rays': 'segment by segment along the line at y -0.25 / 0 / 0.25 m, 0.15 / 0.9 / 1.75 m above it'})
    under = [up(x, cy_at(x), .005) for x in (-2., -1., 0., 1., 2., 3.)]
    check('span_clear_underneath', all(u is not None and u >= .45 for u in under), {'underside_z_m': [round(u, 3) if u else None for u in under],
          'note': 'nothing between z 0 and the trunk over the middle: the ravine goes there'})
    lo, hi = Vector((9, 9, 9)), Vector((-9, -9, -9))
    for o in objs:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c); lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    check('torn_roots_rise', hi.z >= 2.8, {'top_z_m': round(hi.z, 3), 'note': 'the torn-up roots behind the butt'})
    check('sockets_present', {'Socket_Path_W', 'Socket_Path_E', 'Socket_Deck'} <= set(S['sockets']), sorted(S['sockets']))
    return {'deck_z_m': {'butt': round(deck_at(X_B + .3), 3), 'middle': round(deck_at(0), 3), 'break': round(deck_at(X_E - .2), 3)},
            'band_width_min_m': min(widths), 'steepest_deg': round(max(slopes), 1) if slopes else None, 'span_m': [-3.4, 4.4],
            'walk': 'Socket_Path_W (x -11, ground) -> root heap 26 deg -> trunk top -> crown bank -> Socket_Path_E (x +11, ground)', 'sockets': sorted(S['sockets'])}


NOTE = ('倒伏巨木橋（三視圖 LG01-cand-3）：22 × 5 × 4 m，一棵比 FR04 大很多的古樹倒在谷底上方。樹幹從樹頭（x −6.4，半徑 1.0 m）到斷口（x 8.3，半徑 0.52 m），'
        '兩端擱在谷邊、中段微微拱起，x −3.4～4.4 底下是空的（最高離地 0.75 m），谷由關卡地形放在下面。樹幹頂被走出一條約 0.84 m 寬的平滑路線：樹皮磨掉，'
        '露出銀褐色木面，中間踩得較深，苔從兩側邊緣長進來；路面高度樹頭 2.1 m、中段 2.0 m、斷口 1.0 m。兩端都用土坡和地面順接：樹根那頭是撕裂的半個根盤'
        '塌成的土堆（x −11 到樹頭，約 26°），樹梢那頭是一道土和石頭的坡（x 11 到斷口，約 21°）。樹頭照三視圖 cand-3 擴張成一大束粗扭根（每側 20 條），順著土坡往兩側、往後流下插進地面，互相交疊、偶爾拱起；'
        '樹頭後方一叢從土裡扯起的中型根往後上方翹（2.4–3.1 m）、末端斷頭；根之間夾細根和石頭；走道從土坡中間上去，根離走線至少 0.62 m 加根半徑。'
        '樹梢端四根斷掉的大枝往兩側張開，還有幾根折斷的小枝；下側面有一層層的層狀蕈。'
        '沒有木板、沒有繩子。苔綠 #3F5A2E、深樹皮 #2B2018。碰撞：樹幹一條平頂簡化管、兩個土坡、扯起的根各一條管、四根大枝各一條管。'
        '接口：Socket_Path_W／Socket_Path_E（兩端地面，朝外）、Socket_Deck（中段路面）。')


def register(ASSETS):
    ASSETS['LG01_GiantLogBridge'] = dict(zh='倒伏巨木橋', kind='giantlog', palette=palette, build=lg01_giant_log, limit=(22., 5., 4.), tex=2048, ver='v001',
        box=((-11., -2.5, 0.), (11., 2.5, 4.)), ref='LG01/LG01-cand-3', slot='D5_MushroomValley', minTier='standard', clamp_max=.03,
        uv_shape='CONVEX', origin='centre of the footprint at ground level; walk along X, root end at -X', note=NOTE)
