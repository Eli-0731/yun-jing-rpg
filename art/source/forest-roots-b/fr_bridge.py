"""FR04 log bridge (work pack B-104h part 2): 7 x 1 x 1.2 m, one old log laid across a gap, its top adzed flat to walk on.

Three-view FR04 candidate-04 (flat walkable top, stepping wood) with candidate-02's stone piers. The log lies along X on two
pairs of flat stones; its top is hewn flat at 0.85 m (about 0.55-0.64 m wide, foot-worn down the middle). West end (-X): the
butt, rounded, with plank roots spreading down to the ground and two roots broken off short beside the step. East end (+X):
sawn square, growth rings showing. Four stepping rounds (sawn log rounds stood on end, tops 0.17 / 0.34 / 0.51 / 0.68 m) climb
to the deck at each end. Broken branch stubs on the sides, moss along the flanks below the hewn edge.
Unlike A03 (a round fallen log on the ground): this one is raised on stones, hewn flat on top, stepped at both ends.
Origin: centre of the footprint at ground level; walk along X, west end at -X.
"""
import math, random
import bmesh
from mathutils import Vector, noise
from ti_core import S, socket, mesh
import fr_parts as FP
import fr_mats as fm
from cr_parts import set_attr_list

DECK = .85
CZ = .6
X0, X1 = -2.1, 2.2            # log butt (west) and sawn end (east)
STEP_H = (.68, .51, .34, .17)  # nearest the deck first
STEP_R = .22                  # 0.44 m rounds: a foot-wide tread, not a post top (v001 review: 0.28 m was too small to step onto)
STEP_RUN = .26                # each round stands 0.26 m beyond the next taller one, overlapping it: the exposed tread is 0.26 m deep


def r_at(x):
    t = (x - X0) / (X1 - X0)
    return .36 + .045 * (1 - t) + .08 * max(0., 1 - (x - X0) / .55) ** 2


def ry_at(x): return min(r_at(x), .44)
def cy_at(x): return .03 * noise.noise(Vector((x * .35, 1.3, 2.)))


KNOTS = ((-1.25, 215, .13), (.35, 325, .11), (1.55, 205, .1), (-.3, 150, .07), (.95, 30, .07))   # (x, angle round the log, swell)


def knot(x, th):
    """Burls on the lower flanks where old limbs grew out: a local swell of the radius."""
    out = 0.
    for xk, tk, a in KNOTS:
        dt = (th - math.radians(tk) + math.pi) % math.tau - math.pi
        out += a * math.exp(-((x - xk) ** 2 + (dt * .42) ** 2) / .018)
    return out
def cz_at(x): return CZ + .012 * noise.noise(Vector((x * .5, 4.1, .7)))


def _bark_ring(so, s, r, th, twist=.25, plates=2.8, crack=.32, fiss=.22, lump=.05):
    """Radius factor, fissure value and lump at one point of a bark ring (fr_parts.sweep's crack recipe): deep cracks on the
    flanks and underside, none on the top."""
    rho = max(.6, plates * r)
    q = so + Vector((math.cos(th + twist * s) * rho, math.sin(th + twist * s) * rho, s * .42))
    F = max(0., 1. - abs(noise.noise(q)) / crack) ** 1.3
    facing = max(0., math.sin(th))
    depth = fiss * F * (1. - facing ** 1.5)
    bump = lump * noise.noise(so * .7 + Vector((math.cos(th) * 1.3, math.sin(th) * 1.3, s * .55)))
    return 1. + bump + .015 * noise.noise(q * 3.1) - depth, F * (1. - facing ** 1.5), bump


def _cap(verts, faces, attr_b, attr_a, ring, centre, n_in, axis, push=None):
    """Close a ring with n_in concentric rings and a centre vertex. push(f) offsets the inner rings (a dome). The 'adze' attribute
    gets (radius from the centre across the face, angle, 0) so the rings shader can draw growth rings. Returns the new faces."""
    c = Vector(centre); m = len(ring); rings = [ring]; push = push or (lambda f: Vector((0, 0, 0)))
    ia, ib = (1, 2) if axis == 'x' else (0, 1)
    def polar(p):
        d = Vector(p) - c; return (math.hypot(d[ia], d[ib]), math.atan2(d[ib], d[ia]), 0.)
    for k in ring: attr_a[k] = polar(verts[k])
    for j in range(1, n_in + 1):
        f = 1 - j / (n_in + 1); idx = []
        for k in ring:
            p = c + (Vector(verts[k]) - c) * f + push(f)
            verts.append(tuple(p)); idx.append(len(verts) - 1); attr_b.append((0., 0., 0.)); attr_a.append(polar(p))
        rings.append(idx)
    verts.append(tuple(c + push(0.))); ci = len(verts) - 1; attr_b.append((0., 0., 0.)); attr_a.append((0., 0., 0.))
    out = []
    for a_, b_ in zip(rings, rings[1:]):
        for k in range(m): out.append((a_[k], a_[(k + 1) % m], b_[(k + 1) % m], b_[k]))
    for k in range(m): out.append((rings[-1][k], rings[-1][(k + 1) % m], ci))
    faces.extend(out)
    return len(out)


def _finish_mesh(o, mat_i, attr_b, attr_a):
    for p, m in zip(o.data.polygons, mat_i):
        p.material_index = m
        if m: p.use_smooth = False          # hewn and sawn faces are flat
    set_attr_list(o, 'bark', attr_b); set_attr_list(o, 'adze', attr_a)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    return o


def log(P):
    """The hewn log: bark sections along X; every point that would stand above DECK is laid on the deck plane (very slightly
    dished down the middle where feet wear it). Faces wholly on the deck take the heartwood material; the sawn east end the
    rings material; the west butt is a rounded bark dome."""
    R = random.Random('FR04_log'); so = Vector((R.uniform(-50, 50), R.uniform(-50, 50), R.uniform(-50, 50)))
    nv = 40; xs = []; x = X0
    while x < X1 - .03: xs.append(x); x += .06
    xs.append(X1)
    verts, flat_v, attr_b, attr_a = [], [], [], []
    for x in xs:
        s = x - X0; r, ry, cy, cz = r_at(x), ry_at(x), cy_at(x), cz_at(x)
        for k in range(nv):
            th = 2 * math.pi * k / nv
            f, F, bump = _bark_ring(so, s, r, th); f += knot(x, th)
            y = cy + math.cos(th) * ry * f; z = cz + math.sin(th) * r * f
            on = z > DECK
            if on:
                y = cy + math.cos(th) * ry * (1 + .5 * bump); yr = y - cy
                z = DECK - .006 * max(0., 1 - (yr / .3) ** 2) + .003 * noise.noise(Vector((x * 1.7, yr * 3., 5.)))
            verts.append((x, y, z)); flat_v.append(on)
            attr_b.append((s, th * r, F)); attr_a.append((x, y - cy, 1.))
    faces, mat_i = [], []
    for i in range(len(xs) - 1):
        for k in range(nv):
            a = i * nv + k; b = i * nv + (k + 1) % nv
            faces.append((a, b, b + nv, a + nv)); mat_i.append(1 if all(flat_v[v] for v in (a, b, b + nv, a + nv)) else 0)
    n = _cap(verts, faces, attr_b, attr_a, [(len(xs) - 1) * nv + k for k in range(nv)], (X1, cy_at(X1), cz_at(X1)), 4, 'x')
    mat_i += [2] * n                                                    # east: sawn square
    n = _cap(verts, faces, attr_b, attr_a, list(range(nv))[::-1], (X0, cy_at(X0), cz_at(X0)), 4, 'x', lambda f: Vector((-.12 * (1 - f * f), 0, 0)))
    mat_i += [0] * n                                                    # west: the butt, rounded off
    o = mesh('Log_Deck', verts, faces, P['bark'][0], smooth=True, grain='x')
    o.data.materials.append(P['heart']); o.data.materials.append(P['rings'])
    return _finish_mesh(o, mat_i, attr_b, attr_a)


def stump(P, R, name, cx, cy, h, r, zg=0.):
    """A sawn log round stood on end: bark round the side flaring a little into the ground, chamfered sawn top (rings)."""
    so = Vector((R.uniform(-50, 50), R.uniform(-50, 50), R.uniform(-50, 50))); nv = 22
    zs = [zg]; z = .04
    while z < h - .03: zs.append(z); z += .04
    zs.append(h - .014)
    verts, attr_b, attr_a = [], [], []
    for z in zs:
        r0 = r * (1 + .2 * max(0., 1 - z / .14) ** 2)
        for k in range(nv):
            th = 2 * math.pi * k / nv
            f, F, _ = _bark_ring(so, z, r0, th, twist=.4, plates=3.2, fiss=.16, lump=.06)
            verts.append((cx + math.cos(th) * r0 * f, cy + math.sin(th) * r0 * f, z)); attr_b.append((z, th * r0, F)); attr_a.append((0., 0., 0.))
    for k in range(nv):                                               # chamfer ring: the sawn face's edge
        th = 2 * math.pi * k / nv; rr = r * .93
        verts.append((cx + math.cos(th) * rr, cy + math.sin(th) * rr, h)); attr_b.append((h, th * rr, 0.)); attr_a.append((0., 0., 0.))
    nring = len(zs) + 1; faces = []
    for i in range(nring - 1):
        for k in range(nv):
            a = i * nv + k; b = i * nv + (k + 1) % nv
            faces.append((a, b, b + nv, a + nv))
    mat_i = [0] * len(faces)
    n = _cap(verts, faces, attr_b, attr_a, [(nring - 1) * nv + k for k in range(nv)], (cx, cy, h), 3, 'z')
    mat_i += [1] * n
    faces.append(tuple(range(nv))[::-1]); mat_i.append(0)               # buried bottom
    o = mesh(name, verts, faces, P['bark'][2], smooth=True, grain='z')
    o.data.materials.append(P['rings'])
    return _finish_mesh(o, mat_i, attr_b, attr_a)


def step_positions():
    """(x, y, top) of the stepping rounds, west then east, nearest the deck first on each side."""
    out = []
    for side, xe in ((-1, X0 - .12), (1, X1)):
        for j, h in enumerate(STEP_H):
            out.append((xe + side * (STEP_R + .01 + STEP_RUN * j), (.03 if j % 2 else -.03) * side, h))
    return out


def roots_west(P, R):
    """Plank roots from the butt down to the ground, kept beside the stepping rounds; two roots broken off short by the step."""
    for th, xe in ((200, -2.4), (160, -2.34), (340, -2.44), (20, -2.3)):
        th = math.radians(th); r = r_at(X0); sgn = 1 if math.cos(th) > 0 else -1; low = math.sin(th) < -.8
        p0 = Vector((X0 + .14, cy_at(X0) + math.cos(th) * .55 * r, CZ + math.sin(th) * .55 * r))
        p1 = Vector((X0 - .04, max(-.3, min(.3, cy_at(X0) + math.cos(th) * .95 * r)), CZ + math.sin(th) * .95 * r - .06))
        p2, p3 = ((Vector((xe + .08, sgn * .2, .1)), Vector((xe, sgn * .26, -.12))) if low else
                  (Vector((xe + .14, sgn * .34, .14)), Vector((xe, sgn * .38, -.12))))
        FP.sweep('Root_Flare', [tuple(p0), tuple(p1), tuple(p2), tuple(p3)], [.2, .17, .12, .08], R.choice(P['bark']), aspect=.7, step=.05,
                 fiss=.2, seed=R.randrange(999))
    for sgn in (-1, 1):            # broken roots beside the top step: short, snapped, pale at the break
        FP.sweep('Root_Broken', [(X0 + .05, sgn * .28, .7), (X0 - .14, sgn * .36, .84), (X0 - .3, sgn * .39, .92)], [.1, .08, .06],
                 R.choice(P['bark']), step=.04, fiss=.18, nring=14, seed=R.randrange(999), tip=(P['tip'], .07), ground=None)


def branches(P, R):
    """Branch stubs broken off along the log's flanks, pale where they snapped."""
    # (x, side, rise): limbs that grew up and out along the log, snapped off; they lie back along the flank, not up like posts
    for x, side, rise, L in ((1.75, 1, .3, .42), (-.85, 1, .26, .34), (1.15, -1, -.3, .36), (-1.5, -1, .22, .3)):
        r = r_at(x); cy = cy_at(x)
        a = Vector((x - .08, cy + side * r * .55, CZ + (.1 if rise > 0 else -.1)))
        b = Vector((x + L * .45, cy + side * min(.37, r), CZ + rise * .75 + (.08 if rise > 0 else -.04)))
        c = Vector((x + L, cy + side * .39, CZ + rise + (.12 if rise > 0 else -.02)))
        FP.sweep('Branch_Stub', [tuple(a), tuple(b), tuple(c)], [.095, .07, .05], R.choice(P['bark']), step=.04, fiss=.16, nring=14,
                 seed=R.randrange(999), tip=(P['tip'], .06), ground=None)


def sills(P, R):
    """Candidate-02's stone piers: two flat stones under each end with a small chock, the log resting on them."""
    for x in (-1.9, 1.95):
        bot = cz_at(x) - r_at(x) * .96
        for sy in (-.17, .17):                 # two flat footing stones side by side
            sz = R.uniform(.2, .22); hz = sz * .3
            FP.pebble('Sill_Stone', (x + R.uniform(-.05, .05), sy + R.uniform(-.02, .02), hz * 1.15 + .005), sz, R.choice(P['stone']),
                      seed=R.randrange(999), flat=.3)
        sz = .19; hz = sz * .32                  # the bearing stone across them, the log bedded on it
        FP.pebble('Sill_Stone', (x + R.uniform(-.03, .03), R.uniform(-.03, .03), max(.13 + hz, bot - hz * .4)), sz, R.choice(P['stone']),
                  seed=R.randrange(999), flat=.32)
        FP.pebble('Sill_Chock', (x + .28, R.uniform(-.06, .06), .05), .085, R.choice(P['stone']), seed=R.randrange(999), flat=.55, detail=1)


def growth(P):
    Rg = random.Random('FR04_growth'); placed = []
    for i in range(22):                      # moss along both flanks, below the hewn edge
        x = Rg.uniform(X0 + .55, X1 - .1); side = Rg.choice((-1, 1)); z = Rg.uniform(.3, .7)
        hit = FP.snap((x, side * 1.2, z), (0, -side, 0))
        if not hit or any((hit[0] - q).length < .32 for q in placed) or hit[0].z > DECK - .1: continue
        placed.append(hit[0].copy())
        FP.moss_patch('Log_Moss', tuple(hit[0]), tuple(hit[1]), Rg.uniform(.09, .14), P['moss'], seed=i, snap_each=True, flat=.8)
    for x, sy, out in ((-1.68, -.3, (1, 0, 0)), (1.75, .3, (-1, 0, 0)), (-2.12, .3, (1, 0, 0))):   # tucked against the footing stones
        FP.fern('Sill_Fern', (x, sy, .04), P['fern'], Rg, n=6, L=.22, out=out, up_bias=.6, spread=.9)
    for x, y, h in step_positions():
        if h > .3: continue
        for k in range(2):
            a = Rg.choice((-1, 1)) * math.pi / 2 + Rg.uniform(-.6, .6); d = STEP_R + .05
            FP.grass_tuft('Step_Grass', (x + math.cos(a) * d, max(-.38, min(.38, y + math.sin(a) * d)), .014), Rg.randint(3, 5),
                          Rg.uniform(.09, .14), P['grass'], Rg, spread=.025)


def collision(V, F):
    """The log as one flat-topped loft (its top is the deck), each stepping round an octagonal prism."""
    secs = []
    for x in [X0 - .1] + [X0 + i * .4 for i in range(1, 12)] + [X1]:
        xc = max(X0, min(X1, x)); r, ry, cy, cz = r_at(xc) * .97, ry_at(xc) * .97, cy_at(xc), cz_at(xc)
        te = math.asin(max(-1., min(1., (DECK - cz) / r))); span = math.pi + 2 * te; m = 10
        secs.append([(x, cy + math.cos(te - span * j / (m - 1)) * ry, min(DECK, cz + math.sin(te - span * j / (m - 1)) * r)) for j in range(m)])
    FP.hull_loft(V, F, secs)
    for x, y, h in step_positions():
        ring = lambda z: [(x + math.cos(k * math.tau / 8) * STEP_R, y + math.sin(k * math.tau / 8) * STEP_R, z) for k in range(8)]
        FP.hull_loft(V, F, [ring(0.), ring(h)])


def fr04_bridge(P):
    P['heart'] = fm.heartwood('Log_Heartwood'); P['rings'] = fm.rings('Log_Rings')
    R = random.Random('FR04_LogBridge')
    log(P)
    for i, (x, y, h) in enumerate(step_positions()):    # neighbours' flared feet overlap in plan: their buried bottoms 2.5 mm apart
        stump(P, R, 'Step_Round', x, y, h, STEP_R * R.uniform(.98, 1.03), zg=(i % 3) * .0025)
    roots_west(P, R)
    branches(P, R)
    sills(P, R)
    growth(P)
    socket('Socket_Path_W', (-3.5, 0, 0), rot=(0, 0, math.pi / 2))
    socket('Socket_Path_E', (3.5, 0, 0), rot=(0, 0, -math.pi / 2))
    socket('Socket_Deck', (0, 0, DECK))
    V, F = [], []; collision(V, F)
    S['collision_mesh'] = (V, F)
    S['prop'] = dict(kind='bridge')


NOTE = ('獨木橋（三視圖 FR04 candidate-04，墊石取 candidate-02）：7 × 1 m、高 1.2 m。一根老木沿 X 架在兩組扁石上，頂面削平成走道'
        '（長 4.3 m、高 0.85 m、寬約 0.55–0.64 m，中間有踩出的淺凹），兩端各四根直立的鋸切木墩當踏階（直徑 0.44 m、前後相疊，外露踏面深 0.26 m；頂高 0.17／0.34／0.51／0.68 m，每階 0.17 m）。'
        '西端是根部：圓鈍的樹頭、板根往下抓地，踏階旁兩條斷根；東端是平整鋸口，看得到年輪。側面有斷枝殘樁，削平邊緣以下的側面長苔。'
        '和 A03 倒木不同：A03 是圓木躺在地上；這根架高、頂面削平、兩端有踏階。'
        '碰撞：原木一條平頂簡化管（橋面即頂面）、八根木墩各一個八角柱；斷枝、斷根、苔、蕨、草不擋。'
        '接口：Socket_Path_W／Socket_Path_E（兩端地面，朝外）、Socket_Deck（橋面中點）。')


def register(ASSETS):
    ASSETS['FR04_LogBridge'] = dict(zh='獨木橋', kind='bridge', palette=FP.palette, build=fr04_bridge, limit=(7., 1., 1.2), tex=2048, ver='v001',
        box=((-3.5, -.5, 0.), (3.5, .5, 1.2)), ref='FR04/candidate-04', slot='D1_ForestEdge_to_D2_ElderTree', minTier='standard', clamp_max=.03,
        uv_shape='CONVEX', origin='centre of the footprint at ground level; walk along X, west (root) end at -X', note=NOTE)
