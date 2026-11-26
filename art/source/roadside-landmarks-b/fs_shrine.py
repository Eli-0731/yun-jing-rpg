"""FS01 tiny roadside field shrine in the A6 rice fields (work pack 2026-11-09 B-112h, batch B, FS01).

A small stone niche under a low dark tile roof on a stepped stone base, empty inside (no statue), a small stone incense burner in
front, worn and rain-stained, no writing (chosen sheet FS01-cand-6). Not the RK06 earth-god shrine nor the fallen D3 shrine: this one
is a squared niche block, dressed stone below and lime plaster above with stone quoins at the front corners, a timber lintel ring on
top and a hanging-gable roof whose ridge runs across the front.

The roof is the VL pan-and-roll roof (vh_roof.py) built at 0.6 scale: a shrine this small uses smaller tiles, and vl_roof keeps 12
courses a slope whatever its depth, so at full size the tiles would come out short and wide. Everything in the roof frame (tiles,
boards, barge boards, rafters, ridge) is scaled together.

Sizes (limit 2.4 x 2.0 x 2.6 m): base 1.60 x 1.37 x 0.28 m (two courses) and one step in front; niche block 1.44 x 0.95 x 1.40 m on it,
opening 0.80 m wide, 1.08 m high with coved top corners, 0.80 m deep; eaves 0.98 m out in front (kept 2.5 cm inside the limit, so nothing is flattened onto it), ridge top about 2.56 m.
Origin: footprint centre, bottom z = 0, front (the niche opening) -Y.
"""
import math, random
from mathutils import Matrix
from ti_core import S, box, cyl, lathe, torus, socket, extrude_profile, xf, T, boolean
from cr_parts import rbox
import fr_parts as FP
import vl_mats, cr_mats as cm, ti_mats as tm
import vl_roof as RF
import vh_roof as VR

W, D, H = 2.4, 2.0, 2.6
POD = (-.80, .80, -.75, .62)                 # base: x0, x1, y0, y1; two courses 0..0.14..0.28
STEP = (-.55, .55, -.95, -.75)               # one step, 0..0.14
BODY = (-.72, .72, -.40, .55, .28, 1.68)     # niche block: x0, x1, y0, y1, z0, z1
SILL_Z, OPEN_W, OPEN_TOP, ARCH_R = .36, .80, 1.44, .15     # ARCH_R: the inward-curving (cove) top corners, as on the sheet
BACK_T = .15
BAND_Z = .70                                 # dressed stone below, plaster above
BEAM = (1.68, 1.80)
SC, YC = .6, .075                            # the roof frame: scale, ridge line y
ROOF = dict(z0=2.683, rise=1.083, depth_front=1.05 / SC, depth_back=.875 / SC, xh=1.0 / SC, lift_eave=.15, lift_end=.08)
BURNER = (0., -.58, .28)


def under_w(x, y):
    """Underside of the roof boards at world (x, y)."""
    return SC * VR.under(x / SC, (y - YC) / SC)


def palette():
    P = vl_mats.palette('elderly')
    # an old field shrine: the lime coat is greyer and has fallen off in more places than on a lived-in house (stone shows through)
    P['plaster'] = vl_mats.plaster('Shrine_Lime_Plaster', peel=.36, repair=0., grime=1., damp=1.2, moss=.15, tone=.6, seed=(3.1, 1.7, 0.))
    P['roof'] = RF.roof_material()
    P['ash'] = tm.plain('Incense_Ash', (.3, .29, .27), rough=.95, noise=.5, scale=90.)
    P['incense'] = tm.plain('Incense_Stick', (.2, .06, .035), rough=.8, noise=.2, scale=200.)
    P['quoin'] = [cm.stone(f'Quoin_Stone_{i}', light=l, dark=d, ochre=(.24, .2, .14), moss=.5, lichen=.6, crack=.4)
                  for i, (l, d) in enumerate((((.22, .21, .185), (.1, .095, .082)), ((.2, .19, .165), (.085, .08, .07))))]
    P['burner'] = cm.stone('Burner_Stone', light=(.215, .205, .185), dark=(.09, .085, .075), ochre=(.2, .17, .12), moss=.7, lichen=.6, crack=.3)
    return P


def base(P, R):
    x0, x1, y0, y1 = POD
    for c, (z0, z1) in enumerate(((0., .14), (.14, .28))):
        # each course: blocks along the front and back faces, a filler between; joints staggered between courses
        cuts = [x0, -.28 + c * .2, .3 + c * .15, x1] if c == 0 else [x0, -.5, .05, .55, x1]
        for k in range(len(cuts) - 1):
            a, b = cuts[k] + .003, cuts[k + 1] - .003
            rbox(f'Base_Course_{c}_{k}', ((a + b) / 2, (y0 + y1) / 2, (z0 + z1) / 2 + .0015 * c), (b - a, y1 - y0 - .004 * c, z1 - z0 + .003 * c),
                 R.choice(P['stone']), r=.015, amp=.003, freq=3., hew=3, chips=2, seed=c * 10 + k, div=.06, flat='z' if c == 0 else '', group='Stone')
    sx0, sx1, sy0, sy1 = STEP
    for k, (a, b) in enumerate(((sx0, -.05), (-.044, sx1))):
        rbox(f'Step_{k}', ((a + b) / 2, (sy0 + sy1 + .01) / 2, .07), (b - a, sy1 - sy0 + .01, .14), P['stone'][k % 2], r=.015, amp=.003, freq=3.,
             hew=3, chips=2, seed=30 + k, div=.06, flat='zY', group='Stone')


def niche(P, R):
    x0, x1, y0, y1, z0, z1 = BODY
    h = OPEN_W / 2
    # dressed stone band: two side blocks, the back block and the niche floor (sill)
    for k, (a, b) in enumerate(((x0 - .01, -h), (h, x1 + .01))):
        rbox(f'Band_Side_{k}', ((a + b) / 2, (y0 - .01 + y1 + .01) / 2, (z0 + BAND_Z) / 2), (b - a, y1 - y0 + .02, BAND_Z - z0), R.choice(P['stone']),
             r=.012, amp=.003, freq=3., hew=3, chips=2, seed=40 + k, div=.06, group='Stone')
    rbox('Band_Back', (0., y1 - BACK_T / 2 + .005, (z0 + BAND_Z) / 2), (OPEN_W + .02, BACK_T + .01, BAND_Z - z0), P['stone'][0], r=.01, amp=.002,
         hew=2, seed=44, div=.06, group='Stone')
    rbox('Niche_Sill', (0., (y0 + y1 - BACK_T) / 2 - .005, (z0 + SILL_Z) / 2), (OPEN_W + .02, y1 - y0 - BACK_T + .01, SILL_Z - z0), P['stone'][1],
         r=.01, amp=.002, hew=2, chips=1, seed=45, div=.06, group='Stone')
    # plaster upper body, the opening (straight jambs, rounded upper corners) cut through it; the cut faces take the inside plaster
    up = rbox('Niche_Body', (0., (y0 + y1) / 2, (BAND_Z + z1) / 2), (x1 - x0, y1 - y0, z1 - BAND_Z), P['plaster'], r=.012, amp=.003, freq=2.,
              hew=2, seed=46, div=.06, group='Main')
    # the top corners are coves: a quarter circle centred on the corner itself, so a rounded ear of plaster reaches into the opening
    out = [(-h, BAND_Z - .1), (h, BAND_Z - .1), (h, OPEN_TOP - ARCH_R)]
    out += [(h - ARCH_R * math.sin(a), OPEN_TOP - ARCH_R * math.cos(a)) for a in [math.pi / 2 * q / 8 for q in range(1, 9)]]
    out += [(-h + ARCH_R * math.cos(a), OPEN_TOP - ARCH_R * math.sin(a)) for a in [math.pi / 2 * q / 8 for q in range(0, 9)]]
    depth = (y1 - BACK_T) - (y0 - .2)
    cut = extrude_profile('Cut_Niche', out, depth, P['plaster_in'], plane='xz', p=(0., (y1 - BACK_T + y0 - .2) / 2, 0.), bevel=0, group='Main')
    boolean(up, cut)
    # stone quoins at the two front corners, a centimetre proud of the plaster, long and short in turn
    for sx in (-1, 1):
        for k in range(4):
            za = BAND_Z + k * .245 + .003; zb = za + .239; L = .24 if k % 2 == 0 else .17; d = .14 if k % 2 == 0 else .2
            xa, xb = sorted((sx * (x1 + .01), sx * (x1 + .01 - L)))
            rbox(f'Quoin_{sx}_{k}', ((xa + xb) / 2, y0 - .01 + d / 2, (za + zb) / 2), (xb - xa, d, zb - za), P['quoin'][k % 2], r=.01, amp=.002,
                 hew=2, chips=0, seed=50 + k + (sx > 0) * 10, div=.06, group='Stone')


def timber(P, R):
    x0, x1, y0, y1, z0, z1 = BODY; b0, b1 = BEAM
    t = P['timber']
    box('Lintel_Front', (0., y0 - .01, (b0 + b1) / 2), (x1 - x0 + .26, .13, b1 - b0), t, bevel=.008, group='Wood', grain='x')
    box('Lintel_Back', (0., y1 + .005, (b0 + b1) / 2), (x1 - x0 + .26, .13, b1 - b0), t, bevel=.008, group='Wood', grain='x')
    for sx in (-1, 1):
        box(f'Side_Plate_{sx}', (sx * (x1 - .05), (y0 + y1) / 2, b0 + .045), (.12, y1 - y0 - .14, .09), t, bevel=.006, group='Wood', grain='y')
        # a short bracket block under each end of the front lintel, on the quoin, and a bearing block on top
        box(f'Bracket_{sx}', (sx * (x1 - .07), y0 - .02, b0 - .05), (.14, .11, .1), t, bevel=.006, group='Wood', grain='x')
        box(f'Bearing_{sx}', (sx * (x1 - .1), y0 - .01, b1 + .035), (.12, .12, .07), t, bevel=.006, group='Wood', grain='x')
    box('Bearing_Mid', (0., y0 - .01, b1 + .035), (.12, .12, .07), t, bevel=.006, group='Wood', grain='x')
    # purlins under the boards, front and back, and the gables under the hanging roof (plank infill on the side plates)
    xs = [x0 - .3 + (x1 - x0 + .6) * q / 8 for q in range(9)]
    for nm, y in (('Front', y0 - .01), ('Back', y1 + .03)):
        RF.sweep_box(f'Eave_Purlin_{nm}', [(x, y, under_w(x, y) - .002) for x in xs], .1, .1, t, group='Wood', grain='x')
    for sx in (-1, 1):
        x = sx * (x1 - .05); ys = [y0 + .07 + (y1 - y0 - .14) * q / 10 for q in range(11)]
        prof = [(ys[0], b0 + .09), (ys[-1], b0 + .09)] + [(y, under_w(x, y) - .012) for y in ys][::-1]
        extrude_profile(f'Gable_{sx}', prof, .035, P['plank'], plane='yz', p=(x, 0., 0.), bevel=0, group='Wood', grain='y')
        box(f'King_Post_{sx}', (x + sx * .025, YC, (b0 + .09 + under_w(x, YC)) / 2), (.03, .09, under_w(x, YC) - b0 - .1), t, bevel=.004, group='Wood', grain='z')


def roof(P, R):
    def cell(kind, side, x, k, r):           # old roof: a few dark-fired tiles, moss in the low courses near the ends
        if k < 4 and abs(x) > 1.0 and r < .45: return 2 + (4 if kind == 'roll' else 0)
        if r > .9: return 3 + (4 if kind == 'roll' else 0)
        return (0 if r < .6 else 1) + (4 if kind == 'roll' else 0)
    with xf(T(0., YC, 0.) @ Matrix.Scale(SC, 4)):
        for side in (-1, 1):
            RF.tiles(P, side, cell=cell)
            VR.underlay(P, side)
            VR.eave_caps(P, side)
        VR.ridge(P); VR.barge_boards(P); VR.eave_rafters(P, spacing=.45, reach=.7)


def burner(P, R):
    """A stone censer as on the sheet: a round bellied bowl with a rolled lip, two raised bead bands round the belly, two upright loop
    ears on the rim, three stubby feet; ash and three burnt-down sticks in it."""
    bx, by, bz = BURNER; lift = .055
    prof = [(0., .0), (.1, .0), (.13, .02), (.15, .06), (.155, .1), (.147, .135), (.16, .15), (.165, .168), (.14, .168), (.135, .155),
            (.13, .1), (.1, .05), (0., .045)]
    lathe('Burner_Bowl', [(r, z + lift) for r, z in prof], (bx, by, bz), P['burner'], seg=32, group='Main')
    for z, r in ((.075, .152), (.122, .153)):
        torus('Burner_Band', (bx, by, bz + lift + z), r, .006, P['burner'], major=32, minor=6, group='Main')
    for k in range(3):
        a = math.tau * k / 3 + math.pi / 2
        cyl('Burner_Foot', (bx + .1 * math.cos(a), by + .1 * math.sin(a), bz + lift / 2 + .004), .03, lift + .012, P['burner'], verts=10, r2=.022, group='Main')
    for sx in (-1, 1):
        box(f'Burner_Ear_Post_{sx}', (bx + sx * .13, by, bz + lift + .178), (.03, .028, .03), P['burner'], bevel=.006, group='Main')
        torus(f'Burner_Ear_{sx}', (bx + sx * .13, by, bz + lift + .222), .036, .011, P['burner'], rot=(math.pi / 2, 0, 0), major=14, minor=6, group='Main')
    cyl('Burner_Ash', (bx, by, bz + lift + .14), .134, .01, P['ash'], verts=24, bevel=0, group='Main')
    for k, (dx, dy, hh, lean) in enumerate(((-.035, .01, .13, .08), (.0, -.025, .1, -.05), (.04, .02, .055, .12))):
        cyl('Incense_Stick', (bx + dx, by + dy, bz + lift + .14 + hh / 2), .003, hh, P['incense'], verts=5, bevel=0, rot=(lean, lean * .5, 0), detail=1, group='Main')


def growth(P, R):
    x0, x1, y0, y1 = POD
    for _ in range(26):
        side = R.random()
        if side < .35: x, y = R.uniform(x0, x1), y1 + .03
        elif side < .6: x, y = x0 - .03, R.uniform(y0, y1)
        elif side < .85: x, y = x1 + .03, R.uniform(y0, y1)
        else: x, y = R.choice((-1, 1)) * R.uniform(.58, .78), y0 - .04
        FP.grass_tuft('Base_Weed', (x, y, 0.), R.randint(8, 14), R.uniform(.12, .3), P['grass'] if R.random() < .7 else P['dry'], R, lean=.3, detail=1, spread=.03)
    for j in range(7):
        q = (R.choice((-1, 1)) * R.uniform(.6, .76), R.uniform(y0 + .05, y1 - .05), .33)
        FP.moss_patch('Base_Moss', q, (0, 0, 1), R.uniform(.05, .09), P['moss'], seed=j, flat=.6, snap_each=True)
    for j in range(3):
        FP.moss_patch('Step_Moss', (R.uniform(-.5, .5), -.86, .19), (0, 0, 1), R.uniform(.04, .07), P['moss'], seed=20 + j, flat=.6, snap_each=True)


def build_fs01(P):
    R = random.Random('FS01')
    VR.configure(**ROOF)              # first: the timber and gables read the roof's underside
    base(P, R); niche(P, R); timber(P, R); roof(P, R); burner(P, R); growth(P, R)
    socket('Socket_Offering', (0., (BODY[2] + BODY[3] - BACK_T) / 2, SILL_Z), rot=(0, 0, math.pi))
    S['collision_mesh'] = collision()
    S['part_notes'] = {'base_m': {'xy': POD, 'courses_z': [0., .14, .28]}, 'step_m': {'xy': STEP, 'z': [0., .14]}, 'niche_block_m': BODY,
                       'opening_m': {'width': OPEN_W, 'sill_z': SILL_Z, 'top_z': OPEN_TOP, 'corner_radius': ARCH_R, 'depth': round(BODY[3] - BACK_T - BODY[2], 3)},
                       'roof': {'scale': SC, 'ridge_y_m': YC, 'eave_front_y_m': round(YC - ROOF['depth_front'] * SC, 3), 'eave_back_y_m': round(YC + ROOF['depth_back'] * SC, 3),
                                'note': 'VL tiles at 0.6 scale (vl_roof keeps 12 courses a slope)'},
                       'burner_m': {'at': BURNER, 'bowl_radius': .165, 'height_to_ears': .29}, 'Socket_Offering': 'centre of the niche floor, for an offering placed by the game',
                       'inside': 'empty, no statue, no writing'}


def collision():
    V, F = [], []
    def prism(x0, x1, y0, y1, z0, z1):
        FP.hull_loft(V, F, [[(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)] for z in (z0, z1)])
    prism(*POD, 0., .28); prism(*STEP, 0., .14)
    prism(BODY[0] - .01, BODY[1] + .01, BODY[2] - .07, BODY[3] + .07, .28, 1.88)        # the niche block with its lintels (closed)
    prism(-.18, .18, BURNER[1] - .16, BURNER[1] + .16, .28, .58)                          # the burner
    # the roof as one slab under the tiles: a small shrine, its eave (1.7 m) is lower than a walker, so they stop at the eave
    ye, yb = YC - ROOF['depth_front'] * SC, YC + ROOF['depth_back'] * SC
    zf, zr, zb = under_w(0., ye + .01), under_w(0., YC), under_w(0., yb - .01)
    FP.hull_loft(V, F, [[(x, ye, zf), (x, YC, zr), (x, yb, zb), (x, yb, zb + .25), (x, YC, zr + .3), (x, ye, zf + .25)] for x in (-1.05, 1.05)])
    return V, F


def register(ASSETS):
    ASSETS['FS01_FieldShrine'] = dict(
        kind='shrine', zh='田間小廟', palette=palette, build=build_fs01, tex=1024, ver='v001',
        atlases={'Main': ['Main', 'Detail_Small'], 'Stone': ['Stone'], 'Wood': ['Wood']},
        limit=[W, D, H], box=((-W / 2, -D / 2, 0.), (W / 2, D / 2, H)), slot='A6_RiceFields_FieldShrine', ref='FS01/FS01-cand-6', clamp_max=.03, uv_detach_zero=True,
        origin='footprint centre, bottom z = 0, front (the niche opening) -Y',
        note='稻田邊的小石龕（三視圖 FS01-cand-6）：兩層石台基加一級台階，龕身下段石砌、上段石灰泥，前面兩角有長短相間的角石，龕口直邊、上方兩角內凹成海棠角，龕內空著、沒有神像、不寫字；'
             '頂上一圈木額枋，懸山黛瓦頂（屋脊和正面平行，瓦是 VL 瓦片縮成 0.6 倍），兩側山牆木板封；龕前石台上一只三足石香爐（雙立耳、腹部兩道凸箍），爐裡香灰和三支殘香。台基四周長草，台面和台階有苔。'
             '碰撞：台基、台階、龕身（龕口算封住）、香爐、屋頂一整片（屋簷 1.7 m，比人低，人走到簷下就停）。',
        method='procedural mesh construction (art/source/roadside-landmarks-b/fs_shrine.py, vh_roof.py at 0.6 scale); procedural shaders baked to three 1024 atlases '
               '(Main, Stone, Wood); roof tiles on the shared 1024 VL tile texture (VL_Shared, read only)',
        based_on='original (Blender procedural); VL material set and roof tiles from art/source/village-houses-b')


def shrine_checks(aid, check, cfg):
    from vl_checks import _bvh
    body = _bvh([o for g, o in S['lods'][0].items() if not g.startswith('Detail_')])
    col = _bvh([S['collision_obj']]) if S.get('collision_obj') else None
    down = lambda x, y: (lambda h: round(h[0].z, 3) if h else None)(body((x, y, 6.), (0, 0, -1)))
    # the niche is open and empty: a level ray into the opening goes to the back wall's inner face
    inner_back = BODY[3] - BACK_T
    rays = {z: body((0., -3., z), (0, 1, 0)) for z in (.6, 1.0, 1.3)}
    hits = {z: round(h[0].y, 3) if h else None for z, h in rays.items()}
    # (the burner stands in front of the opening at z < 0.5, so the low ray is taken over it from above: z 0.6 clears it)
    check('niche_open_and_empty', all(v is not None and abs(v - inner_back) < .03 for v in hits.values()), {'ray_hits_y_m': hits, 'back_wall_inner_y_m': inner_back})
    # hanging-gable roof, ridge across the front: high over the ridge line, lower front and back, about level along the ridge
    ridge = [down(x, YC) for x in (-.8, 0., .8)]; front, back = down(0., -.8), down(0., .8)
    check('roof_ridge_across_front', all(ridge) and front and back and min(ridge) > front + .25 and min(ridge) > back + .2 and max(ridge) - min(ridge) < .08 and max(ridge) <= H,
          {'ridge_top_m': ridge, 'front_slope_m': front, 'back_slope_m': back})
    under = lambda x, y: (lambda h: round(h[0].z, 3) if h else None)(body((x, y, 1.2), (0, 0, -1)))      # from under the eave (it covers the burner)
    bt, st = under(BURNER[0] + .07, BURNER[1] + .06), under(.3, -.86)
    check('burner_in_front', bt is not None and .44 < bt < .53 and st is not None and abs(st - .14) < .02,
          {'burner_ash_top_m': bt, 'step_top_m': st, 'note': 'rays from 1.2 m down, under the eave'})
    out = {'niche_hits_y_m': hits, 'ridge_m': ridge}
    if col:
        f = col((0., -3., .07), (0, 1, 0)); g = col((0., -3., 1.0), (0, 1, 0)); e = col((0., -3., 1.85), (0, 1, 0))
        check('collision_step_body_eave', f and g and e and abs(f[0].y - STEP[2]) < .02 and abs(g[0].y - (BODY[2] - .07)) < .02 and e[0].y < -.8,
              {'step_front_y_m': round(f[0].y, 3) if f else None, 'body_y_m': round(g[0].y, 3) if g else None, 'eave_y_m_at_1.85': round(e[0].y, 3) if e else None})
    return out
