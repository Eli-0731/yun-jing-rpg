"""SG04 half-way rest shelter (work pack B-104h part 2): 4 x 3 x 4 m, a half-open stone shelter backed against the cliff.

Three-view SG04/REST-SHELTER candidate-01: two square stone columns at the front on carved bases, a stone architrave with a cloud
relief and corner brackets, a single-slope blue-grey tile roof leaning back into the cliff, the back and the right side are the
rough cliff itself, a long stone bench along the cliff with a cracked corner repaired by a fitted stone, a stone basin fed by a
bamboo spout. All-stone frame, single slope, one open side: it does not read as a four-post timber pavilion (TE05, RK03) or a
round bamboo pavilion (WM09).
Origin: centre of the footprint at ground level; the open front faces -Y; the cliff is at +Y (back) and +X (right side).
World constants: eave underside >= 2.6 m, seat 0.45 m.
"""
import math, random
from mathutils import Vector
from ti_core import S, socket, boolean, cyl, torus, extrude_profile, surface, tube
import ti_mats as tm
import cr_mats as cm
from cr_parts import rbox, pole
import sg_parts as SG

COL_X, COL_Y, COL_W = 1.65, -1.0, .3
BEAM_Z0, BEAM_H = 2.75, .34
K = math.tan(math.radians(17))              # roof pitch
Y_EAVE, Y_BACK = -1.47, 1.0
FLOOR = .06
SEAT = .45


def zb(y): return BEAM_Z0 + BEAM_H + (y - COL_Y) * K       # underside of the rafters


def zt(y): return zb(y) + .11                               # top of the roof boards


def palette():
    P = SG.palette()
    P['pillar'] = SG._stone_set('Pillar_Stone', 2, light=(.3, .29, .27), dark=(.13, .125, .118), ochre=(.29, .25, .18), moss=.7, lichen=.6, crack=.5)
    P['rock'] = [cm.stone(f'Cliff_Rock_{i}', light=l, dark=d, ochre=(.3, .25, .17), moss=1.3, lichen=.7, crack=.95)
                 for i, (l, d) in enumerate((((.28, .265, .24), (.1, .093, .085)), ((.25, .245, .235), (.09, .088, .085))))]
    P['wood'] = cm.wood('Rafter_Wood', dark=(.05, .032, .02), light=(.19, .125, .07), moss=True)
    P['tile'] = cm.tile('Roof_Tile', base=(.034, .045, .06), light=(.085, .1, .118), moss=.95)
    P['bamboo'] = cm.culm('Spout_Bamboo', mud_h=-1.)
    P['water'] = tm.plain('Basin_Water', (.025, .075, .07), rough=.08, noise=.25, bump=.02)
    P['stream'] = tm.plain('Spout_Stream', (.32, .42, .42), rough=.1, noise=.2, bump=.02)
    return P


def cloud_outline(scale, cx=0., cz=0.):
    lobes = [(-.065, .075, .075), (.065, .075, .075), (0., .15, .082), (-.15, .05, .05), (.15, .05, .05)]
    pts = []
    for i in range(96):
        a = math.tau * i / 96; d = Vector((math.cos(a), math.sin(a))); best = .02
        for lx, lz, r in lobes:
            o = Vector((-lx, .09 - lz)); b = o.dot(d); c = o.length_squared - r * r; disc = b * b - c
            if disc >= 0: best = max(best, -b + math.sqrt(disc))
        p = Vector((0, .09)) + d * best
        pts.append((cx + p.x * scale, cz + max(0., p.y) * scale))
    return pts


def column(P, R, side):
    x = side * COL_X; mat = P['pillar'][0 if side < 0 else 1]
    base = rbox(f'Column_Base_{side}', (x, COL_Y, .191), (.48, .48, .378), mat, r=.02, amp=.002, freq=4., hew=3, chips=1, seed=3 + side, div=.07, flat='z')
    for nx, ny in ((0, -1), (side, 0), (-side, 0)):            # a sunk square panel with a ring medallion on three faces
        c = Vector((x + nx * .24, COL_Y + ny * .24, .2)); t = Vector((ny, nx, 0)) if nx == 0 else Vector((0, 1, 0))
        cut = rbox('Base_Panel_Cut', tuple(c), (.03 if nx else .32, .03 if ny else .32, .24), None, r=0., div=.5)
        boolean(base, cut)
        rot = (math.pi / 2, 0, 0) if ny else (0, math.pi / 2, 0)
        ring = torus('Base_Ring_Cut', tuple(c - Vector((nx, ny, 0)) * .016), .06, .012, None, rot=rot, major=28, minor=6)
        boolean(base, ring)
    rbox(f'Column_Shaft_{side}', (x, COL_Y, (.38 + BEAM_Z0) / 2), (COL_W, COL_W, BEAM_Z0 - .38 + .004), mat, r=.024, amp=.002, freq=3., hew=5, chips=1,
         seed=7 + side, div=.09, flat='zZ')
    # corner bracket (que ti) under the architrave on the inner face: a scrolled stone corbel
    pts = [(0., 0.), (-.42, 0.), (-.4, -.035), (-.34, -.05), (-.3, -.035), (-.26, -.045)]
    for i in range(1, 9):
        u = i / 9; pts.append((-.26 + .26 * u, -.045 - .21 * math.sin(u * math.pi / 2) ** 1.3))
    pts.append((0., -.26))
    pts = [(side * (COL_X - COL_W / 2) + side * px, pz) for px, pz in pts]     # px <= 0: measured in from the column's inner face
    extrude_profile(f'Bracket_{side}', [(px, BEAM_Z0 + .004 + pz) for px, pz in pts], .16, mat, plane='xz', p=(0, COL_Y, 0), bevel=.006)
    return base


def architrave(P, R):
    mat = P['pillar'][0]
    beam = rbox('Architrave', (0, COL_Y, BEAM_Z0 + BEAM_H / 2), (2 * COL_X + .36, .3, BEAM_H), mat, r=.022, amp=.002, freq=3., hew=4, chips=1, seed=21, div=.09)
    # cloud relief on the front: a raised cloud head 3 cm proud, with a sunk border line framing it
    extrude_profile('Architrave_Cloud', cloud_outline(1.2, 0., BEAM_Z0 + .025), .05, mat, plane='xz', p=(0, COL_Y - .15 - .005, 0), bevel=.006)
    for s in (-1, 1):
        cut = rbox('Architrave_Line_Cut', (s * .62, COL_Y - .15, BEAM_Z0 + BEAM_H / 2), (.02, .02, .2), None, r=0., div=.5)
        boolean(beam, cut)
    # side beams from the columns back into the cliff, the right one resting on the rock
    for s in (-1, 1):
        rbox(f'Side_Beam_{s}', (s * COL_X, (COL_Y + 1.3) / 2, BEAM_Z0 + .15), (.26, 1.3 - COL_Y - .15, .3), mat, r=.02, amp=.002, freq=3., hew=3, chips=1,
             seed=30 + s, div=.09, flat='Y')


def roof(P, R):
    wood = P['wood']
    # rafters running from the eave into the cliff, boards over them
    sh = lambda q: q.__setitem__(2, q.z + q.y * K)
    ym = (Y_EAVE + Y_BACK + .25) / 2; L = Y_BACK + .25 - Y_EAVE
    for i in range(10):
        x = -1.85 + i * 3.7 / 9
        rbox('Rafter', (x, ym, zb(ym) + .045), (.07, L, .09), wood, r=.008, amp=.0015, freq=6., hew=2, seed=i, div=.2, flat='Y', warp=sh, grain='y')
    rbox('Roof_Boards', (0, ym, zb(ym) + .1), (3.96, L, .02), wood, r=.003, div=.35, flat='Y', warp=sh, grain='x', seed=40)
    for s in (-1, 1):   # barge boards on both gable edges
        rbox('Barge_Board', (s * 1.985, (Y_EAVE + Y_BACK) / 2, zb((Y_EAVE + Y_BACK) / 2) + .1), (.028, Y_BACK - Y_EAVE, .24), wood, r=.004, div=.1, warp=sh, grain='y', seed=50 + s)
    # tiles: pan rows with roll rows over their joints, each row one strip whose courses step up 16 mm (the lap of the next tile)
    n = 8; c = (Y_BACK - Y_EAVE) / n; lift = .018
    def y_at(j):
        k, sub = divmod(j, 3); return Y_EAVE + k * c + (.002, c * .5, c - .002)[sub], (0., .5, 1.)[sub] * lift
    nv = 3 * n - 1
    for i in range(18):
        xc = -1.87 + i * .22
        def fn(u, v, xc=xc):
            y, l = y_at(round(v * nv)); t = 2 * u - 1
            return (xc + t * .108, y, zt(y) + .012 + l - .02 * (1 - t * t))
        surface('Pan_Tile_Row', 3, nv, fn, P['tile'], solid=.012, grain='y')
        # drip tile at the eave
        extrude_profile('Drip_Tile', [(xc - .1, 0.), (xc - .05, -.045), (xc, -.06), (xc + .05, -.045), (xc + .1, 0.)][::-1],
                        .018, P['tile'], plane='xz', p=(0, Y_EAVE - .004, zt(Y_EAVE) + .008), bevel=0.)
    xs = [-1.87 + i * .22 + .11 for i in range(17)] + [-1.94, 1.94]
    for i, xr in enumerate(xs):
        def fn(u, v, xr=xr):
            y, l = y_at(round(v * nv)); a = math.pi * u; r = .048 + l * .5
            return (xr + r * math.cos(a), y, zt(y) + .012 + l + r * math.sin(a) * .9)
        surface('Roll_Tile_Row', 4, nv, fn, P['tile'], solid=.01, grain='y')
        cap = cyl('Eave_Cap', (xr, Y_EAVE - .003, zt(Y_EAVE) + .03), .056, .022, P['tile'], axis='y', verts=12, bevel=0.)
    # mortared flashing where the roof runs into the cliff
    rbox('Roof_Flashing', (0, Y_BACK - .02, zt(Y_BACK) + .07), (3.96, .14, .14), P['pillar'][1], r=.03, amp=.006, freq=3., hew=2, seed=60, div=.1)
    Rg = random.Random('SG04_roofmoss')     # moss cushions on the lower courses
    for i in range(9):
        xr = Rg.choice(xs[:17]); y = Rg.uniform(Y_EAVE + .05, Y_EAVE + .9)
        hit = SG.snap((xr, y, 5.), (0, 0, -1))
        if hit: SG.moss_patch('Roof_Moss', tuple(hit[0]), tuple(hit[1]), Rg.uniform(.05, .08), P['moss'], seed=i, flat=1.2, snap_each=True)


def slab(name, nu, nv, fn, off, mat):
    """A closed rock slab: the grid fn(u, v) as the front, the same grid moved by off as the back, rims round the edges
    (a straight offset instead of a solidify modifier, so the slab never leaves its footprint)."""
    from ti_core import mesh
    cu = nu + 1; off = Vector(off)
    front = [Vector(fn(i / nu, j / nv)) for j in range(nv + 1) for i in range(cu)]
    verts = [tuple(v) for v in front] + [tuple(v + off) for v in front]
    n = len(front); faces = []
    for j in range(nv):
        for i in range(nu):
            a = j * cu + i
            faces.append((a, a + 1, a + 1 + cu, a + cu)); faces.append((n + a, n + a + cu, n + a + 1 + cu, n + a + 1))
    ring = [i for i in range(cu)] + [j * cu + nu for j in range(1, nv + 1)] + [nv * cu + i for i in range(nu - 1, -1, -1)] + [j * cu for j in range(nv - 1, 0, -1)]
    for k in range(len(ring)):
        a, b = ring[k], ring[(k + 1) % len(ring)]
        faces.append((a, n + a, n + b, b))
    o = mesh(name, verts, faces, mat, smooth=True, grain='z')
    import bmesh
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    return o


def cliff(P, R):
    """The back and the right side are the cliff itself, not masonry: each face is split into tall fracture facets (anisotropic Voronoi
    cells, each a tilted plane), so the face steps at vertical joints and reads as split rock. Back face y 1.0-1.3 (forward bosses to
    0.8 above the bench), 0.2 m thick; right face x 1.56-1.8, stopping at 2.75 m where the side beam rests on it."""
    from mathutils import noise
    from cr_parts import _sharp
    def facets(seed, a0, a1, z1, n):
        Rf = random.Random(seed)
        return [(Rf.uniform(a0, a1), Rf.uniform(0, z1), Rf.uniform(0., .22), Rf.uniform(-.28, .28), Rf.uniform(-.12, .12)) for _ in range(n)]
    def relief(F, a, z, s):
        # tall cells (vertical joints), each a tilted plane; a soft pick (softmax over the cell distances) instead of the nearest cell,
        # so a joint is a crease about 0.1 m wide: a hard pick stepped at every grid row a diagonal joint crossed (a pixel staircase)
        e = [((a - f[0]) / .55) ** 2 + ((z - f[1]) / 1.4) ** 2 for f in F]; e0 = min(e)
        w = [math.exp(-(x - e0) / .12) for x in e]; ws = sum(w)
        d = sum(wi * (f[2] + f[3] * (a - f[0]) + f[4] * (z - f[1])) for wi, f in zip(w, F)) / ws
        d += .02 * noise.noise(Vector((a * 4., z * 1.5, s))) + .008 * noise.noise(Vector((a * 12., z * 9., s + 2.)))
        d += .04 * noise.noise(Vector((a * 2.2, z * .9, s + 5.)))                       # broad lumps across the facets
        j = 1. - abs(noise.noise(Vector((a * 3.2, z * .35, s + 7.))))                    # ridged noise: near-vertical joints,
        d -= .035 * j ** 3                                                               # each groove wider than two grid cells
        return max(0., min(.3, d))
    FB = facets('SG04_cliff_back', -2.2, 2.2, 4., 26); FS = facets('SG04_cliff_side', -.8, 1.2, 2.75, 10)
    def bulge(a, z):         # forward bosses above the bench, kept clear of the roof
        allow = max(0., min(1., (z - 1.15) / .4)) * max(0., min(1., (3.3 - z) / .3))
        return .2 * allow * max(0., noise.noise(Vector((a * .55, z * .45, 11.))) + .1)
    def back(u, v):
        x = -1.99 + 3.98 * u; top = 3.97 - .05 * (1 + noise.noise(Vector((x * 2., 0., 9.)))) / 2
        z = top * v
        return (x, 1.02 + min(.26, relief(FB, x, z, 1.)) * min(1., z / .2 + .3) - bulge(x, z), z)
    o = slab("Cliff_Back", 44, 36, back, (0, .22, 0), P['rock'][0]); _sharp(o.data, 20)
    def side(u, v):
        z = .003 + (BEAM_Z0 - .003) * v      # 3 mm up: its bottom never lies in the back slab's bottom
        y = -.6 + 1.75 * u + .09 * (1 - u) ** 2 * (1 + noise.noise(Vector((0., z * 1.6, 13.))))   # a broken front edge, not a sawn one
        return (1.6 + relief(FS, y, z, 4.) * .75, y, z)
    o = slab('Cliff_Side', 20, 24, side, (.2, 0, 0), P['rock'][1]); _sharp(o.data, 20)


def floor(P, R):
    rows = [-1.48, -1.0, -.5, 0., .5, 1.0]
    for j in range(len(rows) - 1):
        ya, yb = rows[j], rows[j + 1]; x = -1.98
        xmax = 1.56 if yb > -.6 else 1.98
        while x < xmax - .02:
            L = R.uniform(.45, .75)
            if xmax - (x + L) < .25: L = xmax - x
            o = rbox('Floor_Slab', (x + L / 2, (ya + yb) / 2, FLOOR / 2), (L - .006, yb - ya - .006, FLOOR), R.choice(P['tread']), r=.008, amp=.0015, freq=4., hew=2,
                     chips=R.choice((0, 0, 1)), seed=R.randrange(999), div=.16, flat='zZ')
            SG.set_wear(o, lambda p: math.exp(-((p.x + .2) / .9) ** 2) * max(0., 1 - (p.y + .4) ** 2 / 1.4))
            o['tread'] = True
            x += L


def bench(P, R):
    """Long stone bench along the cliff, seat 0.45 m; its right end cracked off and repaired with a fitted paler stone.
    The left end stands 0.6 m clear of the basin: a narrower slot (it was 0.46 m) wedges a 0.5 m walker between the two."""
    y = .72
    for x in (-.18, 1.06):
        rbox('Bench_Leg', (x, y, (FLOOR + SEAT - .1) / 2), (.14, .34, SEAT - .1 - FLOOR + .004), P['pillar'][1], r=.012, amp=.0015, hew=3, seed=int(x * 10) + 5, div=.07, flat='zZ')
    rbox('Bench_Seat', (.52, y, SEAT - .05), (1.56, .42, .1), P['pillar'][0], r=.014, amp=.0015, hew=3, chips=1, seed=71, div=.08, flat='X')
    rbox('Bench_Seat_Repair', (1.385, y, SEAT - .0515), (.178, .42, .096), P['repair'], r=.008, amp=.001, hew=2, seed=72, div=.07, flat='x')


def basin(P, R):
    x0, x1, y0, y1, top = -1.48, -.86, .4, .94, .62
    mat = P['pillar'][1]
    rbox('Basin_Floor', ((x0 + x1) / 2, (y0 + y1) / 2, FLOOR + .05), (x1 - x0, y1 - y0, .1), mat, r=.01, div=.1, flat='z', seed=80)
    for s in (-1, 1):
        rbox('Basin_Wall', ((x0 + x1) / 2, (y0 + y1) / 2 + s * ((y1 - y0) / 2 - .045), (FLOOR + top) / 2), (x1 - x0, .09, top - FLOOR), mat, r=.014, amp=.002, hew=3,
             chips=1, seed=81 + s, div=.07, flat='z')
        rbox('Basin_Wall', ((x0 + x1) / 2 + s * ((x1 - x0) / 2 - .045), (y0 + y1) / 2, (FLOOR + top) / 2), (.09, y1 - y0 - .18 + .004, top - FLOOR), mat, r=.012, amp=.002,
             hew=2, seed=83 + s, div=.07, flat='zyY')
    rbox('Basin_Water', ((x0 + x1) / 2, (y0 + y1) / 2, top - .08), (x1 - x0 - .17, y1 - y0 - .17, .02), P['water'], r=.004, div=.1)
    # bamboo spout from a cleft in the rock, and the thin stream into the basin
    sx = (x0 + x1) / 2; a = Vector((sx, 1.4, 1.25)); b = Vector((sx, .74, 1.12))     # the culm starts deep in the rock cleft
    pole('Spout', tuple(a), tuple(b), .028, .026, P['bamboo'], node_gap=.3, seg=12)
    pts = [b + Vector((0, -.015, -.01)), b + Vector((0, -.04, -.12)), b + Vector((0, -.05, -.3)), Vector((sx, b.y - .05, top - .07))]
    tube('Spout_Stream', [tuple(p) for p in pts], .009, P['stream'], res=6)
    SG.moss_patch('Basin_Moss', (x0 + .05, y0 - .002, .2), (0, -1, 0), .07, P['moss'], seed=90)


def growth(P, R):
    Rg = random.Random('SG04_growth')
    for i, (x, y) in enumerate(((-1.85, .95), (-.6, .97), (1.52, -.1), (1.5, -.5), (1.52, .3))):    # ferns at the cliff foot
        SG.fern('Cliff_Fern', (x, y - .03, FLOOR + .2), P['fern'], Rg, n=6, L=Rg.uniform(.2, .28), out=(-.3 if x > 1.4 else 0, -1, 0))   # from crevices just above the floor
    for i in range(10):
        x = Rg.uniform(-1.9, 1.4); y = Rg.choice((-1.0, -.5, 0., .5)) + .003
        SG.grass_tuft('Floor_Grass', (x, y, FLOOR), Rg.randint(3, 5), Rg.uniform(.05, .09), P['grass'] if Rg.random() < .7 else P['dry'], Rg, spread=.02)
    for i in range(10):          # moss on the cliff face low down and along the rain line under the eave
        x = Rg.uniform(-1.8, 1.4); z = Rg.uniform(.3, 2.2)
        hit = SG.snap((x, -.5, z), (0, 1, 0))
        if hit and hit[0].y > .8: SG.moss_patch('Cliff_Moss', tuple(hit[0]), tuple(hit[1]), Rg.uniform(.07, .12), P['moss'], seed=100 + i, snap_each=True)


def sg04_shelter(P):
    R = random.Random('SG04_RestShelter')
    cliff(P, R); floor(P, R)
    for s in (-1, 1): column(P, R, s)
    architrave(P, R); bench(P, R); basin(P, R)
    roof(P, R); growth(P, R)
    socket('Socket_Front', (0, -1.5, 0), rot=(0, 0, math.pi))
    socket('Socket_Seat', (.52, .72, SEAT))
    socket('Socket_Basin', (-1.17, .67, .62))
    S['prop'] = dict(kind='shelter')
    V, F = [], []
    SG.prism(V, F, [(-1.5, 0.), (1.0, 0.), (1.0, FLOOR), (-1.5, FLOOR)], -2., 1.56)
    SG.prism(V, F, [(1.0, 0.), (1.5, 0.), (1.5, 4.), (1.0, 4.)], -2., 2.)                       # back cliff
    SG.prism(V, F, [(-.6, 0.), (1.0, 0.), (1.0, BEAM_Z0), (-.6, BEAM_Z0)], 1.56, 2.)            # side cliff
    for s in (-1, 1):
        SG.prism(V, F, [(COL_Y - .24, 0.), (COL_Y + .24, 0.), (COL_Y + .24, BEAM_Z0), (COL_Y - .24, BEAM_Z0)], s * COL_X - .24, s * COL_X + .24)
    SG.prism(V, F, [(.51, 0.), (.93, 0.), (.93, SEAT), (.51, SEAT)], -.26, 1.48)                # bench
    SG.prism(V, F, [(.4, 0.), (.94, 0.), (.94, .62), (.4, .62)], -1.48, -.86)                  # basin
    S['collision_mesh'] = (V, F)


NOTE = ('半途歇腳石亭（三視圖 SG04/REST-SHELTER candidate-01）：4 × 3 m、高 4 m，背靠崖壁的半開石亭。前面兩根 0.3 m 方石柱（中心距 3.3 m），'
        '柱礎三面各刻一個凹框圓紋；石額枋 0.34 m 高，正面浮一朵雲頭，柱與枋交角有石雀替；兩根側枋從柱子伸回崖壁（右側那根擱在岩石上）。'
        '單坡青瓦頂 17°，從崖壁斜下到前簷，簷下緣離地 2.95 m（世界常數 ≥ 2.6），額枋下淨高 2.75 m、雀替處 2.49 m。瓦是板瓦一列、筒瓦壓縫，前簷有瓦當和滴水，靠崖處一道壓脊灰縫，下段瓦面長苔。'
        '後面和右側是崖壁本身（不是砌牆）。沿崖一條石凳，座高 0.45 m，右端斷角用一塊較淺的石頭補上；左後角一個石水盆，竹管從岩縫引水。'
        '全石構、單坡、只有兩根前柱：和 TE05 四柱木亭、RK03 茶亭、WM09 竹亭一眼分得出。地面 0.06 m 石板。'
        '接口：Socket_Front（正面入口地面）、Socket_Seat（凳面中心）、Socket_Basin（盆口中心）。')


def register(ASSETS):
    ASSETS['SG04_RestShelter'] = dict(zh='半途歇腳石亭', kind='shelter', palette=palette, build=sg04_shelter, limit=(4., 3., 4.), tex=2048, ver='v001',
        box=((-2., -1.5, 0.), (2., 1.5, 4.)), ref='SG04/REST-SHELTER', slot='B1_SectGateStairs', minTier='standard', clamp_max=.03,
        origin='centre of the footprint at ground level; open front faces -Y, cliff at +Y and +X', note=NOTE)
