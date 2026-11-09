"""SG03 stone balustrade kit (work pack B-104h part 2): straight bay, sloped run for SG01, corner / line post, end post.

Three-view SG03/BALUSTRADE candidate-01 (round handrail on two small blocks over a framed panel and a sill, square posts with a plinth
and a cap); the end post takes the cloud-scroll cap of candidate-04.
World constant (modeling-style-spec-v1 section 4): balustrade 0.9-1.05 m above the walking surface.

Posts: 0.2 m square shaft on a 0.26 m plinth, a 0.14 m square tenon 0.095 m long under the plinth: it drops into the 0.15 m sockets
of SG01 (0.1 m deep) with 5 mm play on every side, so no face of the tenon lies in a face of the hole.
Rail sections never carry their own posts; each end runs 5 mm into the post it meets, so the seam between rail and post is closed.
"""
import bpy, math, random
from mathutils import Vector
from ti_core import S, socket, boolean, box, torus, extrude_profile
import cr_mats as cm
from cr_parts import rbox, set_attr_list
import sg_parts as SG

POST_W, PLINTH_W, TENON, TENON_D = .2, .26, .14, .095
BAY = 1.8                       # straight bay: post centres 1.8 m apart, 2.0 m over the post outer faces
RAIL_TOP = .9                   # straight bay handrail top above the walking surface
INTO = .005                     # rail ends run 5 mm into the posts
STAIR_RAIL = 1.02               # sloped run: handrail top above the SG01 nosing line


def palette():
    P = SG.palette()
    P['rail'] = SG._stone_set('Rail_Granite', 3, light=(.235, .255, .268), dark=(.1, .11, .118), ochre=(.27, .24, .18), moss=.7, lichen=.85, crack=.45)
    P['lichen'] = cm.moss_tuft('Lichen_Crust', soft=True)
    return P


def shear(t):
    """warp for rbox: local z follows the slope along local y (ends stay vertical)."""
    def w(q): q.z += q.y * t
    return w


def post(P, R, name, z0, h, cap='square', base_cut=None, x=0., y=0., moss_side=1):
    """A square post standing on z0 (the walking or seat surface) at (x, y): tenon, plinth, shaft, cap. Returns the cap top z.
    base_cut = (point, normal) saws the plinth bottom along a sloped seat (normal pointing down into the seat)."""
    mat = R.choice(P['rail'])
    ext = .16 if base_cut else 0.            # a sloped seat: the plinth runs deeper and is sawn along the slope
    rbox(f'{name}_Tenon', (x, y, z0 - TENON_D / 2 + .002), (TENON, TENON, TENON_D + .004), mat, r=.004, div=.07, flat='xXyYzZ')
    pl = rbox(f'{name}_Plinth', (x, y, z0 + (.1 - ext) / 2), (PLINTH_W, PLINTH_W, .1 + ext), mat, r=.014, amp=.0015, freq=5., hew=3, chips=R.choice((0, 1)),
              seed=R.randrange(999), div=.06, flat='z')
    if base_cut: SG.cut_above(pl, base_cut[0], base_cut[1])
    top = z0 + h
    sh = rbox(f'{name}_Shaft', (x, y, (z0 + .1 + top) / 2), (POST_W, POST_W, top - z0 - .1 + .004), mat, r=.016, amp=.0015, freq=5., hew=4,
              chips=R.choice((0, 1)), seed=R.randrange(999), div=.07, flat='xXyYzZ')
    # all four shaft faces stay in their planes (no chisel facet sinks them): a rail end runs 5 mm into whichever face it meets, and a
    # facet up to 10 mm deep opened a 3 mm seam there; the plinth and the cap keep the hewn facets
    # a shallow sunk panel on the two faces along the rail line ends below the cap: reads as carved, not cast
    if cap == 'square':
        c = rbox(f'{name}_Cap', (x, y, top + .06), (.24, .24, .12), mat, r=.018, amp=.0015, freq=5., hew=3, chips=R.choice((0, 1)), seed=R.randrange(999), div=.06, flat='zZ')
        rbox(f'{name}_Cap_Top', (x, y, top + .12 + .022), (.2, .2, .05), mat, r=.014, amp=.001, div=.05, taper=(.62, .62), flat='z', seed=R.randrange(99))
        ztop = top + .17
    else:   # cloud scroll (candidate-04): a cap block and a three-lobed cloud head carved through, a spiral cut on both faces of each lobe
        rbox(f'{name}_Cap', (x, y, top + .05), (.24, .24, .1), mat, r=.016, amp=.0015, freq=5., hew=3, seed=R.randrange(999), div=.06, flat='zZ')
        lobes = [(-.065, .075, .075), (.065, .075, .075), (0., .15, .082)]
        pts = []
        for i in range(72):
            a = math.tau * i / 72; d = Vector((math.cos(a), math.sin(a)))
            best = 0.
            for cx, cz, r in lobes:   # farthest exit of the ray from (0, .09) through the union of the three circles
                o = Vector((-cx, .09 - cz)); b = o.dot(d); c = o.length_squared - r * r; disc = b * b - c
                if disc >= 0: best = max(best, -b + math.sqrt(disc))
            best = max(best, .02)
            p = Vector((0, .09)) + d * best
            pts.append((max(-.12, min(.12, p.x)), max(0., p.y)))
        head = extrude_profile(f'{name}_Cloud', pts, .19, mat, plane='xz', p=(x, y, top + .1 - .004), bevel=.008)
        for cx, cz, r in lobes:
            for s in (-1, 1):
                cut = torus(f'{name}_Scroll_Cut', (x + cx, y + s * .095, top + .1 + cz - .004), r * .55, .011, None, rot=(math.pi / 2, 0, 0), major=28, minor=6)
                boolean(head, cut)
        ztop = top + .1 + .232
    # lichen crust and a little moss low on the shaded face
    from sg_parts import moss_patch
    moss_patch(f'{name}_Lichen', (x + moss_side * POST_W / 2, y + R.uniform(-.04, .04), z0 + R.uniform(.25, .55)), (moss_side, 0, 0), R.uniform(.035, .05), P['lichen'], seed=R.randrange(99), flat=.4)
    moss_patch(f'{name}_Moss', (x + moss_side * PLINTH_W / 2, y, z0 + .07), (moss_side, 0, 0), .045, P['moss'], seed=R.randrange(99), flat=.6)
    return ztop


def bay(P, R, name, ya, yb, zb, zt_rail, t=0., x=0., grass=True):
    """One rail section along Y between two post faces (ya, yb already include the 5 mm run into the posts).
    zb(y): underside of the sill; zt_rail(y): top of the handrail; t: slope (dz/dy) of both lines (0 for a level bay)."""
    L = yb - ya; ym = (ya + yb) / 2; w = shear(t)
    z0 = zb(ym); zr = zt_rail(ym)
    sill_h, rail_d, block_h = .12, .14, .15
    mat = R.choice(P['rail'])
    rbox(f'{name}_Sill', (x, ym, z0 + sill_h / 2), (.2, L, sill_h), mat, r=.014, amp=.0015, freq=5., hew=3, chips=1, seed=R.randrange(999), div=.08, flat='yYz', warp=w)
    p_lo, p_hi = z0 + sill_h - .004, zr - rail_d - block_h
    pan = rbox(f'{name}_Panel', (x, ym, (p_lo + p_hi) / 2), (.12, L - .002, p_hi - p_lo + .004), R.choice(P['rail']), r=.01, amp=.0008, freq=5., hew=0,
               seed=R.randrange(999), div=.07, flat='yYzZ', warp=w)
    # sunk panel on both faces (candidate-01): a recess 8 mm deep, 7 cm in from the edges, its corners stepped in by 4 cm
    fl, fh = p_lo + .07, p_hi - .07
    for s in (-1, 1):
        for dl, dh in ((0., .04), (.04, 0.)):
            cut = rbox(f'{name}_Frame_Cut', (x + s * .067, ym, (fl + fh) / 2), (.03, L - .2 - 2 * dl, fh - fl - 2 * dh), None, r=.0, div=.5, warp=w)
            boolean(pan, cut)
    for e in (-1, 1):   # two small bearing blocks under the handrail, waisted
        yb_ = ym + e * (L / 2 - .2)
        rbox(f'{name}_Block', (x, yb_, p_hi + block_h / 2 + (yb_ - ym) * t), (.1, .16, block_h + .01), mat, r=.012, amp=.001, div=.05,
             taper=(.8, 1.25), seed=R.randrange(99), flat='zZ', warp=shear(t))
    rbox(f'{name}_Handrail', (x, ym, zr - rail_d / 2), (rail_d, L, rail_d), R.choice(P['rail']), r=.062, amp=.0015, freq=4., hew=0,
         chips=0, seed=R.randrange(999), div=.035, flat='yY', warp=w, sharp=80)
    if grass:   # soil and grass at the sill foot on the shaded side
        from sg_parts import grass_tuft
        for i in range(2):
            yy = ya + L * R.uniform(.15, .85)
            grass_tuft(f'{name}_Grass', (x + .12, yy, zb(yy) + .002), R.randint(4, 6), R.uniform(.06, .1), P['grass'] if R.random() < .7 else P['dry'], R, spread=.025)


# ------------------------------------------------------------------ assets
def sg03_straight(P):
    R = random.Random('SG03_RailStraight')
    half = BAY / 2 - POST_W / 2 + INTO        # 0.805
    # the bay runs along X in the model: build along Y, then turn the model a quarter
    S['M'].append(S['M'][-1] @ Matrix_rot_z())       # build along Y, the model runs along X
    bay(P, R, 'Rail', -half, half, lambda y: 0., lambda y: RAIL_TOP, x=0.)
    S['M'].pop()
    socket('Socket_Post_A', (-BAY / 2, 0, 0)); socket('Socket_Post_B', (BAY / 2, 0, 0))
    S['prop'] = dict(kind='rail', rail_top=RAIL_TOP, ends=(-half, half), axis='x')
    V, F = [], []
    SG.prism(V, F, [(-.1, 0.), (.1, 0.), (.1, RAIL_TOP), (-.1, RAIL_TOP)], -half, half)
    S['collision_mesh'] = (V, F)


def Matrix_rot_z():
    from mathutils import Matrix
    return Matrix.Rotation(-math.pi / 2, 4, 'Z')


def stair_line(y): return SG.nose_z(y) + STAIR_RAIL


def sg03_sloped(P):
    """One side of an SG01 flight: three posts in SG01's sockets and two sloped bays, in SG01's frame with x = 0 on the kerb centre line.
    Place at SG01's origin shifted by x = +-1.34 (both sides use the same model)."""
    R = random.Random('SG03_RailSloped'); t = math.tan(SG.SLOPE)
    py = SG.POST_Y
    nrm = Vector((0, -math.sin(SG.SLOPE), math.cos(SG.SLOPE)))
    tops = {}
    for i, y in enumerate(py):
        z0 = SG.seat_top(y) if i != 1 else SG.cope_top(y)
        cut = None if i != 1 else ((0., y, SG.cope_top(y)), tuple(-nrm))
        cap_top = stair_line(y) + .14 - .1           # cap block starts 4 cm above the handrail top
        tops[i] = post(P, R, f'Post_{i}', z0, cap_top - z0, cap='square', base_cut=cut, y=y)
        socket(f'Socket_Post_{i}', (0., y, z0))
    for b in range(2):
        ya, yb = py[b] + POST_W / 2 - INTO, py[b + 1] - POST_W / 2 + INTO
        bay(P, R, f'Rail_{b}', ya, yb, lambda y: SG.cope_top(y) - .02, stair_line, t=t, grass=False)   # the sill foot is buried in SG01's coping
    S['prop'] = dict(kind='rail_sloped', posts=list(py))
    V, F = [], []
    for i, y in enumerate(py):
        z0 = SG.seat_top(y) if i != 1 else SG.cope_top(y)
        SG.prism(V, F, [(y - .13, z0), (y + .13, z0), (y + .13, tops[i]), (y - .13, tops[i])], -.13, .13)
    for b in range(2):
        ya, yb = py[b] + .1, py[b + 1] - .1
        SG.prism(V, F, [(ya, SG.cope_top(ya)), (yb, SG.cope_top(yb)), (yb, stair_line(yb)), (ya, stair_line(ya))], -.1, .1)
    S['collision_mesh'] = (V, F)


def sg03_post(P, kind):
    R = random.Random(f'SG03_Post{kind}')
    top = post(P, R, 'Post', 0., .94, cap='square' if kind == 'Corner' else 'cloud')
    socket('Socket_Base', (0, 0, 0))
    for nm, d in (('N', (0, 1)), ('S', (0, -1)), ('E', (1, 0)), ('W', (-1, 0))):   # rail ends meet the post faces here
        socket(f'Socket_Rail_{nm}', (d[0] * POST_W / 2, d[1] * POST_W / 2, 0))
    S['prop'] = dict(kind='post', top=top)
    V, F = [], []
    SG.prism(V, F, [(-.13, -TENON_D), (.13, -TENON_D), (.13, top), (-.13, top)], -.13, .13)
    S['collision_mesh'] = (V, F)


NOTE_STRAIGHT = ('石欄杆直段（三視圖 SG03 candidate-01）：一段柱中心距 1.8 m、連兩端柱寬是 2.0 m；不含柱子，兩端各伸進柱子 5 mm，接縫是閉合的。'
                 '由下到上：地栿（0.2 × 0.12 m）、華板（0.12 m 厚，兩面各一個 8 mm 深的凹框、四角內收 4 cm）、兩個托墩、圓扶手（0.14 m）；扶手頂離走面 0.9 m（世界常數 0.9–1.05）。'
                 '模型沿 X 擺，原點在走面中線；Socket_Post_A／B 是兩端柱心。陰面地栿腳有土與小草。')
NOTE_SLOPED = ('石欄杆斜段（配 SG01）：一側整套——三根柱插進 SG01 的三個柱孔、兩段順坡欄板。座標跟 SG01 一樣（往 +Y 爬），x = 0 在側欄中線；'
               '放在 SG01 原點、x 偏 ±1.34 m，兩側用同一個模型。扶手頂在踏步前緣線上方 1.02 m（世界常數 0.9–1.05）；欄板底沿斜壓頂、埋入 2 cm。'
               '兩端柱站在端柱座平頂上；中柱在斜壓頂上，柱腳順坡鋸斜、比端柱長 0.14 m。柱下 0.14 m 方榫長 0.095 m，SG01 柱孔 0.15 m、深 0.1 m，四面各留 5 mm。')
NOTE_CORNER = ('石欄杆轉角柱（也當中間柱用）：0.2 m 方柱、0.26 m 柱座、0.24 m 方柱帽，柱頂 1.11 m；柱下 0.14 m 方榫長 0.095 m，可插 SG01 柱孔，'
               '放在平台上則榫埋在石裡。四面中心各有 Socket_Rail_N/S/E/W 給欄板對位（欄板伸進柱面 5 mm）。')
NOTE_END = ('石欄杆端柱：柱身同轉角柱，柱帽是三瓣雲頭（借三視圖 SG03 candidate-04），兩面每瓣各刻一圈圓渦；柱頂 1.27 m。'
            '柱下方榫同轉角柱。放在一段欄杆的盡頭。')


def register(ASSETS):
    common = dict(kind='rail', minTier='standard', clamp_max=.03, ver='v001', slot='B1_SectGateStairs')
    ASSETS['SG03_RailStraight'] = dict(common, zh='石欄杆直段', palette=palette, build=sg03_straight, limit=(2., .3, 1.), tex=1024,
        box=((-.81, -.15, 0.), (.81, .15, 1.)), ref='SG03/BALUSTRADE', origin='centre of the bay on the walking surface; the bay runs along X, its posts (not included) at x = +-0.9',
        note=NOTE_STRAIGHT)
    ASSETS['SG03_RailSloped'] = dict(common, kind='rail_sloped', zh='石欄杆斜段（配 SG01）', palette=palette, build=sg03_sloped, limit=(.3, 3.2, 3.), tex=2048, uv_shape='CONVEX',
        box=((-.15, -1.6, 0.), (.15, 1.6, 3.)), ref='SG03/BALUSTRADE', base_z=round(SG.cope_top(SG.POST_Y[0] + POST_W / 2 - INTO) - .02, 4),
        origin="SG01's origin moved onto the kerb centre line (x = +-1.34 in SG01); climbs towards +Y", note=NOTE_SLOPED)
    ASSETS['SG03_PostCorner'] = dict(common, kind='post', zh='石欄杆轉角柱', palette=palette, build=lambda P: sg03_post(P, 'Corner'), limit=(.3, .3, 1.25), tex=1024,
        box=((-.15, -.15, -.1), (.15, .15, 1.25)), ref='SG03/BALUSTRADE', base_z=-TENON_D,
        origin='post centre on the surface it stands on (the plinth bottom); the tenon reaches 0.095 m below', note=NOTE_CORNER)
    ASSETS['SG03_PostEnd'] = dict(common, kind='post', zh='石欄杆端柱（雲頭）', palette=palette, build=lambda P: sg03_post(P, 'End'), limit=(.3, .3, 1.4), tex=1024,
        box=((-.15, -.15, -.1), (.15, .15, 1.4)), ref='SG03/BALUSTRADE', base_z=-TENON_D,
        origin='post centre on the surface it stands on (the plinth bottom); the tenon reaches 0.095 m below', note=NOTE_END)
