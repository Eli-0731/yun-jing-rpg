"""FE04 net-drying rack and mooring posts at the A5 ferry (work pack 2026-11-09 B-112h, batch B, FE04).

Two rough wooden posts carry three bamboo rails lashed on with rope (top, middle, bottom); an old teal fishing net hangs off the middle
rail in a deep sag with two more lengths of net hanging from the top rail at the ends, torn in places, mended with canvas patches;
two gourd floats on a cord by the right post; a strip of cloth wound round the top rail. In front at each end a thick short mooring
post, damp and cracked, with rope worn grooves and a rope coil (two kinds: a fat split one on the left, a taller one with two slanting
grooves on the right). Flat stones and grass along the foot. No people, no writing (chosen sheet FE04-cand-2).

The net is real twine (a 6 cm mesh drawn as 6 mm strands by a wireframe over the draped grid), in the group Detail_Net as the pack
asks; it is see-through. The twine is never decimated: LOD1 keeps the main net whole and leaves the two drapes out, LOD2 leaves the net out.

Sizes (limit 3 x 1 x 2 m): rack posts 2.0 m apart, 1.93 / 1.98 m high; rails at 1.59, 1.30 and 0.36 m; mooring posts 0.28 m x 0.66 m
and 0.25 m x 0.74 m at x -1.33 / +1.32. Origin: footprint centre, bottom z = 0, front (the net side) -Y.
Reference: art/references/FE04/FE04-cand-2.png (proportions read off the sheet at about 262 px a metre).
"""
import math, random
from mathutils import Vector, noise
import cr_mats as cm, mk_mats as mm, ti_mats as tm
import fr_parts as FP
from cr_parts import rbox, rope, log, lash, sheet
from ti_core import S, cyl, torus, lathe, socket, mesh, boolean

W, D, H = 3.0, 1.0, 2.0
POSTS = ((-1.0, 1.93), (1.0, 1.98))          # rack posts: x, top
RAIL_Y = -.065                                # rails lashed to the front of the posts
TOP_Z, MID_Z, LOW_Z = 1.59, 1.30, .36
NET_Y = -.105                                 # the net hangs just in front of the rails
MOOR = ((-1.33, -.02, .14, .66), (1.32, -.02, .125, .74))     # x, y, radius, height
CELL = .06


def palette():
    P = {}
    P['post'] = cm.wood('Rack_Post_Wood', (.05, .036, .022), (.21, .155, .095), grey=.55, ground_h=.25, moss=True, moss_amt=.6)
    P['moor'] = cm.wood('Mooring_Post_Wood', (.04, .03, .02), (.19, .14, .085), grey=.6, ground_h=.35, moss=True, moss_amt=1.)
    P['bamboo'] = mm.bamboo('Rail_Bamboo', green=(.06, .07, .025), straw=(.2, .14, .055))
    P['rope'] = mm.hemp('Lashing_Rope', (.22, .16, .075), twist=150.)
    P['net'] = mm.hemp('Net_Twine', (.05, .105, .09), twist=260.)
    P['canvas'] = cm.canvas('Net_Patch_Canvas', base=(.2, .165, .1), stain=(.1, .07, .035), faded=.2)
    P['gourd'] = tm.plain('Gourd_Float', (.2, .135, .055), rough=.55, noise=.35, scale=30.)
    P['stone'] = cm.stone('Foot_Stone', light=(.15, .14, .125), dark=(.06, .056, .05), moss=1.1, wet_z=.06)
    P['moss'] = cm.moss_tuft('Foot_Moss', soft=True)
    P['grass'] = cm.weed_leaf('Bank_Grass', (.03, .06, .02), (.1, .17, .045), (.2, .24, .07))
    P['dry'] = cm.weed_leaf('Bank_Dry_Grass', (.1, .075, .03), (.25, .19, .08), (.4, .31, .14))
    return P


# ------------------------------------------------------------------ the net: a draped grid turned into twine by a wireframe
def net(name, fn, nu, nv, mat, keep=None, detail=1, knot_mat=None):
    """Diamond mesh, as a fishing net hangs from its edge (not a square wire grid): lattice points (a, b) with a + b even on a
    2nu x 2nv grid, one diamond round every odd point. nu, nv are given for a square grid of the same cell side: the diamonds'
    diagonals are sqrt 2 x that, so the twine is no denser than a square grid's. A small knot at every crossing (LOD0 only)."""
    nu, nv = max(2, round(nu / 1.414)), max(2, round(nv / 1.414))
    V, F, idx = [], [], {}
    for b in range(1, 2 * nv):
        for a in range(1, 2 * nu):
            if (a + b) % 2 == 0: continue
            if keep and not keep(a / (2 * nu), b / (2 * nv)): continue
            q = []
            for pa, pb in ((a - 1, b), (a, b + 1), (a + 1, b), (a, b - 1)):
                if (pa, pb) not in idx: idx[(pa, pb)] = len(V); V.append(tuple(fn(pa / (2 * nu), pb / (2 * nv))))
                q.append(idx[(pa, pb)])
            F.append(tuple(q))
    if knot_mat is not None:            # knots: a small bipyramid (6 tris) at each crossing, no thicker front to back than the twine
        KV, KF = [], []
        for x, y, z in V:
            o = len(KV)
            KV += [(x + .0075, y, z), (x - .004, y, z + .0068), (x - .004, y, z - .0068), (x, y - .0032, z), (x, y + .0032, z)]
            for f in ((0, 1, 3), (1, 2, 3), (2, 0, 3), (1, 0, 4), (2, 1, 4), (0, 2, 4)):
                KF.append(tuple(o + i for i in f))
        mesh(name + '_Knots', KV, KF, knot_mat, smooth=True, group='Detail_Net', grain='z', detail=2)
    # the twine is never decimated (cfg no_decimate): the main net (detail 1) is whole at LOD0 and LOD1 and left out of LOD2,
    # the two drapes (detail 2) are only at LOD0
    o = mesh(name, V, F, mat, smooth=True, group='Detail_Net', grain='z', detail=detail)
    m = o.modifiers.new('Twine', 'WIREFRAME'); m.thickness = .006; m.use_replace = True; m.use_boundary = True
    m.use_even_offset = False; m.use_relative_offset = False
    return o


def main_net(u, v):
    """One big swag: its two top corners are tied up to the top rail by the posts, the middle hangs off the middle rail in scallops
    between the ties, and the slack bellies forward and down to about 0.42 m in the middle; folds run down it."""
    x = -.9 + 1.75 * u
    xn = (x + .07) / .83
    ties = 9; f = (u * (ties - 1)) % 1.
    lift = max(0., (abs(xn) - .72) / .28); lift = lift * lift * (3 - 2 * lift)
    top = MID_Z - .015 - .075 * math.sin(math.pi * f) ** 1.5 * (1 - lift) + (TOP_Z - .02 - MID_Z) * lift
    bottom = .42 + .5 * xn * xn + .035 * math.sin(x * 5.)
    z = top - (top - bottom) * v
    y = (NET_Y - .13 * math.sin(math.pi * min(1., v * 1.1)) * (1 - .7 * abs(xn) ** 2)
         - .035 * math.sin(x * 9 + v * 2.5) * v - .015 * math.sin(v * 17 + x * 3))
    x += .04 * math.sin(v * 5 + u * 3) * v - .06 * xn * v * v      # the slack draws in towards the middle as it falls
    return (x, y, z)


def drape(x0, x1, xg, z_end, gather=.35, seed=0.):
    """A length of net hanging from the top rail, gathered into a narrow twisted strip lower down."""
    def fn(u, v):
        xt = x0 + (x1 - x0) * u
        k = v ** .6
        x = xt + (xg + (xt - (x0 + x1) / 2) * gather - xt) * k
        z = TOP_Z - .02 - (TOP_Z - .02 - z_end - .12 * math.sin(u * 7 + seed) * v) * v
        y = NET_Y - .015 - .045 * math.sin(math.pi * v) - .03 * math.sin(u * 17 + seed + v * 6) * k
        return (x, y, z)
    return fn


def ragged(seed, start=.8, holes=()):
    def keep(u, v):
        for (hu, hv, r) in holes:
            if math.hypot((u - hu) * 1.8, v - hv) < r: return False
        if v > start:
            n = noise.noise(Vector((u * 13, seed, 0))) * .5 + .5 + .3 * noise.noise(Vector((u * 37, seed, 3)))
            return n > (v - start) / (1 - start) * 1.05
        return True
    return keep


def rack(P, R):
    for k, (x, top) in enumerate(POSTS):
        log(f'Rack_Post_{k}', [(x, 0., -.02), (x + .006, .004, top * .5), (x - .008, 0., top)], .058, P['post'], seg=10, lump=.08, seed=3 + k, grain='z')
    for nm, z, x0, x1, r in (('Top', TOP_Z, -1.28, 1.3, .036), ('Mid', MID_Z, -1.07, 1.08, .03), ('Low', LOW_Z, -1.11, 1.1, .03)):
        log(f'Rail_{nm}', [(x0, RAIL_Y, z - .008), (0., RAIL_Y - .003, z + .006), (x1, RAIL_Y, z + .01)], r, P['bamboo'], seg=10, lump=.025, seed=len(nm), grain='x')
        n = int((x1 - x0) / .32)
        for q in range(1, n + 1):          # node rings, a little proud
            xq = x0 + (x1 - x0) * q / (n + 1) + R.uniform(-.04, .04)
            torus(f'Rail_{nm}_Node', (xq, RAIL_Y, z + .006 * (xq / 1.3)), r * 1.02, .0045, P['bamboo'], rot=(0, math.pi / 2, 0), major=14, minor=4, detail=1)
        for k, (px, _) in enumerate(POSTS):
            # each crossing: a wrap round the post above and below the rail and an X across the front of the rail
            lash(f'Lash_{nm}_{k}', (px, -.005, z + .07), (0, 0, 1), .058, .045, .009, P['rope'], turns=3)
            lash(f'Lash_{nm}_{k}', (px, -.005, z - .07), (0, 0, 1), .058, .045, .009, P['rope'], turns=3)
            for s in (-1, 1):
                rope(f'Lash_X_{nm}_{k}', [(px - .075, RAIL_Y - r - .004, z + s * .065), (px, RAIL_Y - r - .012, z), (px + .075, RAIL_Y - r - .004, z - s * .065)],
                     .009, P['rope'], ply=3, tw=120., seg=6, detail=1)
    # cloth wound round the top rail near the right post
    cyl('Rail_Cloth', (.48, RAIL_Y, TOP_Z + .004), .047, .22, P['canvas'], axis='x', verts=16, bevel=.004)
    for x in (.38, .58):
        torus('Rail_Cloth_Tie', (x, RAIL_Y, TOP_Z + .004), .049, .006, P['rope'], rot=(0, math.pi / 2, 0), major=16, minor=5, detail=1)


def nets(P, R):
    nu, nv = int(1.75 / CELL), 16
    net('Net_Main', main_net, nu, nv, P['net'], knot_mat=P['net'], keep=ragged(1.3, .8, holes=((.36, .58, .09), (.74, .42, .07), (.16, .3, .05))))
    net('Net_Drape_L', drape(-.97, -.58, -.86, .52, seed=1.), 6, 17, P['net'], keep=ragged(4.1, .82), detail=2, knot_mat=P['net'])
    net('Net_Drape_R', drape(.6, .82, .74, .86, gather=.4, seed=2.), 4, 12, P['net'], keep=ragged(7.7, .8), detail=2, knot_mat=P['net'])
    # ties where the net hangs on the middle rail and the drapes on the top rail
    for q in range(1, 8):
        x = -.9 + 1.75 * q / 8
        torus('Net_Tie', (x, RAIL_Y, MID_Z), .036, .005, P['rope'], rot=(0, math.pi / 2, 0), major=12, minor=4, detail=1)
    for x in (-.95, -.88, -.8, -.64, .62, .78, .85):
        torus('Drape_Tie', (x, RAIL_Y, TOP_Z), .042, .005, P['rope'], rot=(0, math.pi / 2, 0), major=12, minor=4, detail=1)
    # two canvas mends laid over the net, a few millimetres in front
    # (thin cloth following the net, a cut-and-torn outline, fine creases, a running stitch of twine round the edge: not a cushion)
    for k, (uc, vc, du, dv) in enumerate(((.66, .38, .075, .14), (.24, .62, .06, .17))):
        sd = 11.3 * (k + 1)
        def edge(u, v, sd=sd):            # the outline: each side a little wavy and frayed
            return 1. + .07 * noise.noise(Vector((u * 4., v * 4., sd))) + .03 * noise.noise(Vector((u * 17., v * 17., sd + 3.)))
        def pf(u, v, uc=uc, vc=vc, du=du, dv=dv, sd=sd):
            a, b = 2 * u - 1, 2 * v - 1                                   # rounded corners (a squircle), then a soft wavy edge
            a, b = a * math.sqrt(1 - .42 * b * b), b * math.sqrt(1 - .42 * a * a)
            e = edge(u, v); uu = .5 + a * .5 * e; vv = .5 + b * .5 * e
            x, y, z = main_net(uc - du + 2 * du * uu, vc - dv + 2 * dv * vv)
            crease = .0022 * noise.noise(Vector((u * 6., v * 9., sd + 7.))) + .001 * math.sin(v * 21. + u * 4.)
            return (x, y - .0045 + crease, z)
        sheet(f'Net_Patch_{k}', 12, 12, pf, P['canvas'], solid=.0012, grain='z')
        n = 22
        for q in range(n):                # running stitch just inside the edge, every other gap a stitch through the net
            if q % 2: continue
            t0, t1 = q / n, (q + .7) / n
            def ring(t, ins=.06):
                side = int(t * 4) % 4; f = t * 4 - int(t * 4)
                u, v = ((f, 0.), (1., f), (1 - f, 1.), (0., 1 - f))[side]
                return .5 + (u - .5) * (1 - ins), .5 + (v - .5) * (1 - ins)
            a_, b_ = pf(*ring(t0)), pf(*ring(t1))
            rope(f'Net_Patch_Stitch_{k}', [(a_[0], a_[1] - .0012, a_[2]), ((a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2 - .0022, (a_[2] + b_[2]) / 2), (b_[0], b_[1] - .0012, b_[2])],
                 .0016, P['rope'], ply=2, tw=60., seg=4, detail=1)
    # gourd floats on a cord by the right post
    rope('Float_Cord', [(.84, RAIL_Y, TOP_Z - .03), (.85, -.11, 1.3), (.845, -.12, 1.0)], .005, P['rope'], ply=2, tw=90., seg=5, detail=1)
    for k, (z, s) in enumerate(((.97, 1.35), (.77, 1.25))):
        prof = [(0, 0), (.04, .002), (.06, .03), (.062, .055), (.042, .09), (.024, .105), (.032, .125), (.033, .14), (.02, .158), (.008, .165), (.008, .185), (0, .185)]
        lathe('Gourd_Float', [(r * s, zz * s) for r, zz in prof], (.845, -.125, z - .185 * s + .01), P['gourd'], seg=16)
        torus('Gourd_Tie', (.845, -.125, z - .185 * s + .01 + .106 * s), .025 * s, .003, P['rope'], major=10, minor=4, detail=1)


def mooring(P, R):
    for k, (x, y, r, h) in enumerate(MOOR):
        p = log(f'Mooring_Post_{k}', [(x, y, -.02), (x + .004, y, h * .5), (x - .003, y + .003, h)], r, P['moor'], seg=16, lump=.05, seed=11 + k, grain='z')
        # rope-worn grooves: rings cut into the wood (the left one level, the right one two slanting)
        cuts = ((.47, 0.),) if k == 0 else ((.5, .14), (.61, -.1))
        for gz, tilt in cuts:
            c = torus(f'Cut_Groove_{k}', (x, y, gz), r + .004, .02, P['moor'], rot=(tilt, 0, 0), major=24, minor=6)
            boolean(p, c)
        if k == 0:     # the fat one is split from the top
            c = rbox('Cut_Split', (x + .02, y, h - .06), (.022, r * 2.4, .2), P['moor'], r=.004, amp=.004, freq=6., div=.02, rot=(0, .12, .5))
            boolean(p, c)
        # a coil of rope round the foot, and one loop lying in the upper groove
        lash(f'Mooring_Coil_{k}', (x, y, .2 if k == 0 else .24), (0, 0, 1), r, .1, .014, P['rope'], turns=3, detail=0)
        gz, tilt = cuts[0]
        # the old line lies in the groove round the back only; the front of the groove shows bare, worn wood
        loop = [(x + (r - .006) * math.cos(a), y + (r - .006) * math.sin(a) * math.cos(tilt), gz + (r - .006) * math.sin(a) * math.sin(tilt)) for a in [math.pi * (-.12 + 1.24 * q / 12) for q in range(13)]]
        rope(f'Mooring_Loop_{k}', loop, .013, P['rope'], ply=3, tw=120., seg=7)
    socket('Socket_Mooring_L', (MOOR[0][0], MOOR[0][1] - MOOR[0][2], .47), rot=(0, 0, math.pi))
    socket('Socket_Mooring_R', (MOOR[1][0], MOOR[1][1] - MOOR[1][2], .5), rot=(0, 0, math.pi))


def ground(P, R):
    # a band of flat bank stones along the foot, half sunk: a few big slabs, the gaps between them packed with smaller stones,
    # thinning out towards the band's edges (not a row of equal coins)
    Rg = random.Random('FE04_ground'); placed = []
    def try_put(sz, tries, ymin, ymax):
        for _ in range(tries):
            x = Rg.uniform(-1.3, 1.3); y = Rg.uniform(ymin, ymax)
            if all(math.hypot(x - px, y - py) > (sz + ps) * .78 for px, py, ps in placed):
                placed.append((x, y, sz)); return True
        return False
    for _ in range(11): try_put(Rg.uniform(.13, .2), 60, -.24, .12)
    for _ in range(26): try_put(Rg.uniform(.06, .11), 60, -.3, .18)
    for _ in range(22): try_put(Rg.uniform(.03, .055), 60, -.34, .22)
    for k, (x, y, sz) in enumerate(placed):
        edge = min(1., abs(y + .06) / .28)
        fl = Rg.uniform(.15, .22) if sz > .1 else Rg.uniform(.28, .45); half = sz * fl * 1.12
        sink = half * Rg.uniform(.45, .6) * (1 - .3 * edge)            # half sunk, a bit less at the band's edges; the clamp flattens at most 1.6 cm
        FP.pebble('Foot_Stone', (x, y, max(half - .016, half - sink)), sz, P['stone'], seed=500 + k * 7, flat=fl, detail=1, group='Main')
    for x in (-1.0, 1.0, -1.33, 1.32):
        for j in range(2):
            a = R.uniform(0, math.tau)
            FP.grass_tuft('Foot_Grass', (x + .17 * math.cos(a), .17 * math.sin(a) - .02, 0.), R.randint(8, 13), R.uniform(.12, .26),
                          P['grass'] if R.random() < .7 else P['dry'], R, lean=.3, detail=1, spread=.03)
        FP.moss_patch('Foot_Moss', (x + .05, -.12, .02), (0, 0, 1), R.uniform(.05, .08), P['moss'], seed=int(x * 10), flat=.6, snap_each=True)


def bank_grass(P, R):
    for k in range(16):       # grass coming up between the stones
        x = R.uniform(-1.3, 1.3); y = R.choice((-.27, .17)) + R.uniform(-.05, .05)
        FP.grass_tuft('Bank_Grass', (x, y, 0.), R.randint(6, 11), R.uniform(.08, .2), P['grass'] if R.random() < .65 else P['dry'], R, lean=.35, detail=1, spread=.03)


def build_fe04(P):
    R = random.Random('FE04')
    rack(P, R); nets(P, R); mooring(P, R); ground(P, R); bank_grass(P, R)
    S['collision_mesh'] = collision()
    S['part_notes'] = {'rack_posts_x_top_m': POSTS, 'rails_z_m': [TOP_Z, MID_Z, LOW_Z], 'net': {'mesh_m': CELL, 'twine_m': .006, 'lod': 'LOD0 and LOD1 whole, left out of LOD2', 'group': 'Detail_Net',
                       'hangs_from': 'middle rail (main net), top rail (two drapes)', 'see_through': True},
                       'mooring_posts_x_y_r_h_m': MOOR, 'sockets': {'Socket_Mooring_L/R': 'in the front of each post\'s rope groove, +Y (Unity forward) pointing out, for a boat\'s mooring line'}}


def collision():
    V, F = [], []
    def prism(x0, x1, y0, y1, z0, z1):
        FP.hull_loft(V, F, [[(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)] for z in (z0, z1)])
    for x, top in POSTS: prism(x - .06, x + .06, -.06, .06, 0., top)
    prism(-.94, .94, -.16, -.03, .36, 1.62)              # the rails and the net between the posts: a walker stops at it
    for x, y, r, h in MOOR: prism(x - r, x + r, y - r, y + r, 0., h)
    return V, F


def register(ASSETS):
    ASSETS['FE04_NetRackMooring'] = dict(
        kind='netrack', zh='曬網架與繫纜樁', palette=palette, build=build_fe04, tex=2048, ver='v001',
        atlases={'Main': ['Main', 'Detail_Small', 'Detail_Net']},
        limit=[W, D, H], box=((-W / 2, -D / 2, 0.), (W / 2, D / 2, H)), slot='A5_Ferry_NetRack', ref='FE04/FE04-cand-2',
        clamp_max=.03, uv_shape='CONVEX', uv_detach_zero=True, no_decimate=('Detail_Net',),
        origin='footprint centre, bottom z = 0, front (the net side) -Y',
        note='渡口的曬網架（三視圖 FE04-cand-2）：兩根粗木柱、三根竹橫桿用麻繩綁（上中下），一張青綠舊漁網從中桿垂下兜成一大彎，兩端另有兩段網從上桿垂下收成一束；'
             '網有破洞、補了兩塊帆布；右柱旁一條繩吊兩顆葫蘆浮子，上桿纏一段布。兩端前面各一根粗短繫纜木樁（左邊粗、頂上裂開，一道磨出的繩溝；右邊較高，兩道斜的繩溝），'
             '樁腳有繩圈。地上一排扁石、草和苔。網是真的網線（6 cm 網目、6 mm 線），放在 Detail_Net；網線不減面：LOD1 只留主網、拿掉兩段垂網，LOD2 不帶網。不寫字。'
             '碰撞：兩根架柱、架子和網之間一片（人走到網前就停）、兩根繫纜樁。Socket_Mooring_L/R：繫纜樁繩溝正面，給船纜。',
        method='procedural mesh construction (art/source/roadside-landmarks-b/fe_netrack.py: logs, lashings, the net as a draped grid turned into twine by a '
               'wireframe, rope grooves cut by boolean rings); procedural wood, bamboo, hemp, canvas and stone shaders baked to one 1024 atlas (Main)',
        based_on='original (Blender procedural); material functions from art/source/village-houses-b')


def netrack_checks(aid, check, cfg):
    from vl_checks import _bvh
    lod0 = S['lods'][0]
    body = _bvh([o for g, o in lod0.items()])
    netb = _bvh([lod0['Detail_Net']]) if 'Detail_Net' in lod0 else None
    # the net is see-through: of level rays from the front across the net, most pass between the twine
    hits = tot = 0
    for i in range(15):
        for j in range(9):
            x, z = -.7 + 1.3 * i / 14, .65 + .5 * j / 8
            tot += 1; h = netb((x, -3., z), (0, 1, 0)) if netb else None
            if h and h[0].y < 0.: hits += 1
    share = hits / tot
    check('net_see_through', netb is not None and .04 < share < .55, {'rays': tot, 'blocked_by_twine': hits, 'share': round(share, 3)})
    # the net hangs off the middle rail in front of the rails, clear of the ground
    import numpy as np
    o = lod0.get('Detail_Net')
    if o is not None:
        co = np.array([o.matrix_world @ v.co for v in o.data.vertices])
        main = co[(co[:, 0] > -.5) & (co[:, 0] < .5)]; upper = main[main[:, 2] > 1.1]
        check('net_hangs_from_middle_rail', abs(main[:, 2].max() - MID_Z) < .04 and main[:, 2].min() > .3 and upper[:, 1].max() < RAIL_Y - .02,
              {'top_m': round(float(main[:, 2].max()), 3), 'lowest_m': round(float(main[:, 2].min()), 3), 'back_y_m_over_1.1m': round(float(upper[:, 1].max()), 3),
               'note': 'over 1.1 m the net is in front of the rail it hangs on; lower down it swings free'})
    # rope grooves: a level ray at the groove reaches further in than just above it
    gr = {}
    for k, (x, y, r, h) in enumerate(MOOR):
        gz, tilt = (.47, 0.) if k == 0 else (.5, .14)
        gz -= r * math.sin(tilt)                   # the slanting groove is lower at the front, where the ray meets it
        a = body((x + .03, -3., gz + .002), (0, 1, 0)); b = body((x + .03, -3., gz + .085), (0, 1, 0))
        gr[k] = (round(a[0].y, 4) if a else None, round(b[0].y, 4) if b else None)
    check('mooring_rope_grooves', all(a is not None and b is not None and a - b > .006 for a, b in gr.values()),
          {'groove_vs_above_front_y_m': gr, 'note': 'the rope loop lies in the groove; the ray at the groove meets the loop or the cut, both deeper than the face'})
    col = _bvh([S['collision_obj']]) if S.get('collision_obj') else None
    if col:
        f = col((0., -3., 1.), (0, 1, 0)); m = col((MOOR[0][0], -3., .3), (0, 1, 0))
        check('collision_net_and_posts', f and m and abs(f[0].y + .16) < .01 and abs(m[0].y - (MOOR[0][1] - MOOR[0][2])) < .01,
              {'net_front_y_m': round(f[0].y, 3) if f else None, 'mooring_front_y_m': round(m[0].y, 3) if m else None})
    return {'net_blocked_share': round(share, 3), 'grooves': gr}
