"""CW01 rammed-earth yard wall set (work pack 2026-11-11 B-40h, batch A): straight section, corner, end and a breached section.

Chosen sheet CW01-cand-2: warm yellow-grey rammed earth in lifts on two courses of dressed stone, a grey brick course under a single
coping of dark grey (#3A4048) pan-and-roll tiles running down both sides from a round ridge; the corner and the end are square earth
piers with a four-sided tiled cap and a small finial; the breached section has its top corner fallen in steps along the lifts, the
crumbled core showing and earth, clods and broken tiles heaped at its foot. Houses' yard walls: taller and neater than R01 / R02.

Every piece is in the same frame: ground z = 0, front -Y, wall centre line on y = 0 (the corner's second leg on x = 0), height 1.8 m
to the top of the ridge roll. Sockets on the end faces at ground level: Socket_A at the -x end, Socket_B at the +x end (the corner's
on its +y end); pieces join face to face, the footing and body end faces lie in those planes.
  CW01_A straight 4.0 m      x -2 .. +2
  CW01_B corner, 2 m legs    x -2 .. +0.3 and y -0.3 .. +2, pier 0.6 m square at the origin
  CW01_C end, 1.2 m          x -0.6 .. +0.6, the pier on x 0 .. 0.6
  CW01_D breach 4.0 m        x -2 .. +2, the +x top corner down to 0.78 m
"""
import math, random
from mathutils import Matrix, Vector, noise
from ti_core import S, box, cyl, socket, xf, T
from cr_parts import rbox
import fr_parts as FP
import vl_mats, cr_mats as cm, ti_mats as tm
import cw_parts as CP

H = 1.8
BODY_TOP = 1.54
EAVE_Z, RIDGE_Z = 1.60, 1.705            # coping eave and ridge (ridge roll top 1.797)
HALF = .22                               # coping half width at the eave (0.5 m overall with the eave discs)
PIER = .30                               # pier half size
BREACH_LOW = .78
PIER_RISE = .2
PIER_TOP = BODY_TOP + PIER_RISE
H_PIER = 2.0


def palette():
    P = vl_mats.palette('diligent')
    P['earth'] = cm.packed_earth('Rammed_Earth', dark=(.25, .175, .095), light=(.47, .345, .19), rough=.9, wet_top=.62, wet_low=.47, dry_low=1.0, dry_top=1.5,
                                 strata_amt=.35)
    P['core'] = cm.packed_earth('Earth_Core', dark=(.1, .068, .036), light=(.3, .2, .1), rough=.95, crumb=.9, wet_top=.0, wet_low=-.1, dry_low=3., dry_top=4.,
                                strata_amt=0.)
    P['mortar'] = cm.packed_earth('Footing_Mortar', dark=(.05, .04, .03), light=(.14, .11, .08), wet_top=.2, wet_low=.1, dry_low=1., dry_top=2., strata_amt=0.)
    P['stone'] = [cm.stone(f'Footing_Stone_{i}', light=l, dark=d, ochre=(.22, .19, .14), moss=.9, lichen=.5, crack=.5)
                  for i, (l, d) in enumerate((((.23, .22, .2), (.1, .096, .088)), ((.21, .2, .185), (.09, .087, .08)), ((.25, .235, .21), (.11, .1, .09))))]
    P['bed'] = cm.stone('Eave_Course', light=(.2, .2, .19), dark=(.085, .085, .08), ochre=(.18, .17, .14), moss=.4, lichen=.3, crack=.3)
    P['captile'] = cm.tile('Cap_Tile', base=(.042, .05, .062), light=(.085, .092, .105), moss=.6)
    return P


def cap_run(P, name, x0, x1, keep=lambda x, side: True, ends=(False, False), seed=0):
    CP.eave_course(P, name, x0, x1, BODY_TOP)
    CP.tile_cap(P, name + '_Cap', x0, x1, HALF, EAVE_Z, RIDGE_Z, keep=keep, ends=ends, seed=seed)


def run(P, R, name, x0, x1, cut=lambda z: 0., keep=lambda x, side: True, flat_lo=True, flat_hi=True, cap_x1=None, seed=0):
    CP.footing(P, R, name, x0, x1, seed=seed)
    CP.lifts(P, R, name, x0, x1, CP.FOOT_H - .01, BODY_TOP + .004, cut=cut, flat_lo=flat_lo, flat_hi=flat_hi, seed=seed)
    cap_run(P, name, x0, cap_x1 if cap_x1 is not None else x1, keep=keep, seed=seed)


def pier(P, R, name, cx, cy, seed=0):
    """A square earth pier on a stone plinth course, its own tiled four-sided cap and finial."""
    h = PIER
    with xf(T(cx, cy, 0.)):
        CP.footing(P, R, name + '_Pier', -h, h, h=CP.FOOT_H, t=2 * h - .02, seed=seed)
        # the pier stands 20 cm above the wall, so the wall's coping and ridge die into its face
        CP.lifts(P, R, name + '_Pier', -h + .015, h - .015, CP.FOOT_H - .01, PIER_TOP + .004, seed=seed, t0=2 * h - .02, t1=2 * h - .06)
        rbox(name + '_Pier_Eave_Course', (0., 0., PIER_TOP + .025), (2 * h - .02, 2 * h - .02, .05), P['bed'], r=.008, amp=.002, seed=5, div=.1, group='Stone')
        CP.tile_pyramid(P, name + '_Pier_Cap', 0., 0., h - .04, EAVE_Z + PIER_RISE, 1.925)   # ~30° cap: reads as a little roof, not a flat slab of logs


def growth(P, R, segs):
    """Grass along both feet of every run, moss on the footing and a few patches on the coping. segs: (frame, x0, x1)."""
    for M, x0, x1 in segs:
        with xf(M):
            n = int((x1 - x0) * 5)
            for k in range(n):
                x = R.uniform(x0 + .05, x1 - .05); side = R.choice((-1, 1))
                FP.grass_tuft('Foot_Grass', (x, side * (CP.FOOT_T / 2 + R.uniform(-.01, .02)), 0.), R.randint(5, 10), R.uniform(.1, .26),
                              P['grass'] if R.random() < .75 else P['dry'], R, lean=.15, detail=1, spread=.015)
            for k in range(int((x1 - x0) * 1.5)):
                x = R.uniform(x0 + .1, x1 - .1); side = R.choice((-1, 1))
                FP.moss_patch('Footing_Moss', (x, side * CP.FOOT_T / 2, R.uniform(.06, .3)), (0, side, .2), R.uniform(.05, .1), P['moss'], seed=int(x * 100) + side,
                              flat=.6, snap_each=True)
            for k in range(int((x1 - x0) * .8)):
                x = R.uniform(x0 + .1, x1 - .1); side = R.choice((-1, 1))
                FP.moss_patch('Cap_Moss', (x, side * .12, RIDGE_Z - .02), (0, side * .45, 1), R.uniform(.04, .07), P['moss'], seed=900 + k, flat=.5, snap_each=True)


def rubble(P, R, x_end, z_low):
    """The fallen part of the breach: a heap of earth both sides of the wall, clods, broken tiles and a stone that rolled out."""
    import random as _r
    # one heap of fallen earth straddling the wall foot (its middle is inside the wall), oval, lumpy, thinning out to nothing
    cx, Rx, Ry, Hh = x_end - .62, .78, .8, .44
    acc = CP.Acc(); n, m = 40, 12
    def hp(a, r):
        x = cx + Rx * r * math.cos(a) * (1 + .12 * noise.noise(Vector((math.cos(a) * 2, math.sin(a) * 2, 3.))))
        y = Ry * r * math.sin(a) * (1 + .12 * noise.noise(Vector((math.cos(a) * 2, math.sin(a) * 2, 7.))))
        x = min(x, 1.98)
        z = Hh * (1 - r * r) ** 1.6 + .035 * noise.noise(Vector((x * 5, y * 5, 1.))) * (1 - r) - .012
        return (x, y, max(.0, z))
    acc.V.append(hp(0., 0.))
    rings = [acc.grid([[hp(math.tau * k / n, (q + 1) / m) for k in range(n)]], closed=True) for q in range(m)]
    for k in range(n): acc.F.append((0, rings[0] + k, rings[0] + (k + 1) % n))
    for q in range(m - 1):
        for k in range(n):
            a, b = rings[q] + k, rings[q] + (k + 1) % n
            acc.F.append((a, a + n, b + n, b))
    acc.make('Breach_Heap', P['core'], smooth=True, group='Main', grain='z')
    hz = lambda x, y: max(0., Hh * (1 - min(1., ((x - cx) / Rx) ** 2 + (y / Ry) ** 2)) ** 1.6 - .012)
    for k in range(26):
        side = R.choice((-1, 1)); x = R.uniform(x_end - 1.3, x_end - .12); y = side * R.uniform(.25, .8)
        z = hz(x, y) * .9; sz = R.uniform(.04, .09)
        FP.pebble('Earth_Clod', (x, y, max(z + .01, sz * .7 * .8)), sz, P['core'], seed=40 + k, flat=.7, seg=8, ring=5, group='Main')
    for k in range(9):
        side = R.choice((-1, 1)); x = R.uniform(x_end - 1.3, x_end - .12); y = side * R.uniform(.3, .8)
        z = hz(x, y) * .9
        L = R.uniform(.06, .14)
        rbox('Tile_Shard', (x, y, z + .012), (L, L * R.uniform(.6, 1.), .014), P['captile'], r=.004, amp=.003, chips=2, seed=70 + k, div=.04,
             rot=(R.uniform(-.4, .4), R.uniform(-.4, .4), R.uniform(0, 3.1)), group='Detail_Small')
    x = x_end - .25
    rbox('Fallen_Footing_Stone', (x - .55, -.78, .08), (.34, .24, .17), P['stone'][0], r=.022, amp=.01, chips=2, hew=2, seed=88, div=.06, rot=(0, .06, .5), group='Stone')


# ------------------------------------------------------------------ the four pieces
def build_a(P):
    R = random.Random('CW01_A'); run(P, R, 'Wall', -2., 2.)
    growth(P, R, [(Matrix(), -2., 2.)])
    socket('Socket_A', (-2., 0., 0.), rot=(0, 0, math.pi)); socket('Socket_B', (2., 0., 0.))
    S['collision_mesh'] = collision([(Matrix(), -2., 2., None)])
    notes('A', 'straight 4 m')


def build_b(P):
    R = random.Random('CW01_B')
    run(P, R, 'Wall_Leg1', -2., -PIER + .02, flat_hi=False, seed=1)
    M2 = Matrix.Rotation(math.pi / 2, 4, 'Z')
    with xf(M2):
        run(P, R, 'Wall_Leg2', PIER - .02, 2., flat_lo=False, seed=2)
    pier(P, R, 'Corner', 0., 0., seed=3)
    growth(P, R, [(Matrix(), -2., -PIER), (M2, PIER, 2.)])
    socket('Socket_A', (-2., 0., 0.), rot=(0, 0, math.pi)); socket('Socket_B', (0., 2., 0.), rot=(0, 0, math.pi / 2))
    S['collision_mesh'] = collision([(Matrix(), -2., -PIER, None), (M2, PIER, 2., None)], piers=[(0., 0.)])
    notes('B', 'corner, two 2 m legs (wall centre lines) meeting at a 0.6 m pier')


def build_c(P):
    R = random.Random('CW01_C')
    run(P, R, 'Wall', -.6, .02, flat_hi=False, seed=4)
    pier(P, R, 'End', PIER, 0., seed=5)
    growth(P, R, [(Matrix(), -.6, 0.)])
    socket('Socket_A', (-.6, 0., 0.), rot=(0, 0, math.pi))
    S['collision_mesh'] = collision([(Matrix(), -.6, 0., None)], piers=[(PIER, 0.)])
    notes('C', 'end: 0.6 m of wall and a 0.6 m pier; Socket_A only')


def breach_cut(z):
    """How far the earth is gone back from x = +2 at height z: nothing below 0.78 m, then back along the lifts to 1.7 m at the top."""
    if z < BREACH_LOW: return 0.
    t = (z - BREACH_LOW) / (BODY_TOP - BREACH_LOW)
    return .35 + 1.35 * t ** .85


def build_d(P):
    R = random.Random('CW01_D')
    jag = {}
    cut = lambda z: breach_cut(z) + jag.setdefault(round(z, 2), R.choice((-.16, -.05, .08, .2)) + R.uniform(-.04, .04)) if breach_cut(z) > 0 else 0.
    top_end = 2. - breach_cut(BODY_TOP) - .02
    Rk = random.Random('CW01_D_keep'); lost = {}
    def keep(x, side):
        k = (round(x, 2), side)
        if k not in lost: lost[k] = x > top_end - Rk.uniform(0., .3)
        return not lost[k]
    run(P, R, 'Wall', -2., 2., cut=cut, keep=keep, cap_x1=top_end + .02, seed=6)
    rubble(P, R, 2., BREACH_LOW)
    n = max(1, int(round((BODY_TOP - CP.FOOT_H) / CP.LIFT))); hz_ = (BODY_TOP - CP.FOOT_H) / n
    # the top of what still stands under the breach is weathered: lumps of crumbled core along it, not a clean lift top
    i_top = max(i for i in range(n) if cut(CP.FOOT_H + (i + .5) * hz_) <= .01)
    z_top = CP.FOOT_H + (i_top + 1) * hz_
    x_from = 2. - cut(z_top + hz_ / 2)
    for k in range(5):
        x = x_from + (2. - x_from) * (k + R.uniform(.1, .9)) / 5
        Lw = R.uniform(.18, .3)
        rbox('Weathered_Top', (min(x, 1.97 - Lw / 2), R.uniform(-.06, .06), z_top + .005), (Lw, CP.BODY_T1 - R.uniform(.04, .12), R.uniform(.03, .07)), P['core'],
             r=.025, amp=.015, freq=5., chips=4, seed=300 + k, div=.035, group='Main', grain='z')
    for i in range(n):
        za = CP.FOOT_H + i * hz_; zb = za + hz_
        c = cut((za + zb) / 2); c_up = cut((zb + zb + hz_) / 2) if i < n - 1 else 9.
        if c > .01 and c_up - c > .12:                            # a tread: crumbs on it, a tuft of grass in the dust
            for k in range(3):
                FP.pebble('Step_Crumb', (2. - c - R.uniform(.04, min(.25, c_up - c - .03)), R.uniform(-.12, .12), zb + .02), R.uniform(.025, .05), P['core'], seed=200 + i * 5 + k,
                          flat=.6, seg=8, ring=5, group='Main')
            if R.random() < .6:
                FP.grass_tuft('Step_Grass', (2. - c - .08, R.uniform(-.1, .1), zb), R.randint(4, 7), R.uniform(.08, .16), P['dry'], R, lean=.3, detail=1, spread=.03)
    growth(P, R, [(Matrix(), -2., 2.)])
    socket('Socket_A', (-2., 0., 0.), rot=(0, 0, math.pi)); socket('Socket_B', (2., 0., 0.))
    S['collision_mesh'] = collision([(Matrix(), -2., 2., breach_cut)])
    notes('D', 'breach: the +x top corner fallen in steps along the lifts down to 0.78 m, heap at its foot')


def notes(k, what):
    S['part_notes'] = {'piece': what, 'height_m': H, 'footing_m': {'height': CP.FOOT_H, 'thickness': CP.FOOT_T},
                       'rammed_earth_m': {'thickness_foot': CP.BODY_T0, 'thickness_top': CP.BODY_T1, 'lift': CP.LIFT, 'top': BODY_TOP},
                       'coping_m': {'eave_z': EAVE_Z, 'ridge_z': RIDGE_Z, 'half_width': HALF, 'tile': 'cr_mats.tile #3A4048, pan and roll, not the VL tile texture'},
                       'sockets': 'Socket_A at the -x end face, Socket_B at the +x end face (corner: +y), both at ground level on the wall centre line'}
    if k == 'D': S['part_notes']['breach_low_m'] = BREACH_LOW


def collision(runs, piers=()):
    V, F = [], []
    t = CP.FOOT_T / 2
    for M, x0, x1, cut in runs:
        def P3(x, y, z, M=M): return tuple(M @ Vector((x, y, z)))
        if cut is None:
            secs = [[P3(x0, -t, z), P3(x1, -t, z), P3(x1, t, z), P3(x0, t, z)] for z in (0., EAVE_Z)]
        else:
            secs = [[P3(x0, -t, z), P3(x1 - cut(z), -t, z), P3(x1 - cut(z), t, z), P3(x0, t, z)] for z in (0., BREACH_LOW, EAVE_Z)]
        FP.hull_loft(V, F, secs)
    for cx, cy in piers:
        h = PIER + .01
        FP.hull_loft(V, F, [[(cx - h, cy - h, z), (cx + h, cy - h, z), (cx + h, cy + h, z), (cx - h, cy + h, z)] for z in (0., EAVE_Z + PIER_RISE)])
    return V, F


COMMON = dict(kind='yardwall', palette=palette, tex=2048, ver='v001', atlases={'Main': ['Main', 'Detail_Small'], 'Stone': ['Stone']},
              slot='A1_Yard_Wall', ref='CW01/CW01-cand-2', clamp_max=.03, uv_detach_zero=True,
              origin='ground z = 0 on the wall centre line; straight / breach: middle of the 4 m; corner: where the centre lines meet; end: middle of the 1.2 m; front -Y',
              method='procedural mesh construction (art/source/village-yards-b/cw_wall.py, cw_parts.py); procedural shaders baked to two 2048 atlases (Main, Stone)',
              based_on='original (Blender procedural); stone, grass and moss materials from the VL set in art/source/village-houses-b')
ZH_NOTE = ('夯土院牆（三視圖 CW01-cand-2）：暖黃灰夯土一版一版夯成（每版約 16 cm），下面兩層石腳，上面一層灰磚檐，再一排黛瓦（#3A4048）壓頂，'
           '筒瓦從屋脊往兩邊流、脊上一條圓脊瓦。轉角和端頭是方形夯土牆墩，四面瓦頂加一個小頂珠。缺口段的上角沿夯土層一階一階塌下，露出粗糙的土芯，'
           '腳下堆土、土塊和碎瓦。四件首尾相接：Socket_A 在 -x 端面、Socket_B 在 +x 端面（轉角在 +y 端），都在地面、牆中心線上。不寫字。')


def register(ASSETS):
    ASSETS['CW01_A_StraightWall'] = dict(COMMON, zh='院牆直段 4 m', build=build_a, limit=[4., .5, H], box=((-2., -.25, 0.), (2., .25, H)),
                                         note=ZH_NOTE + ' 本件：直段 4 m。')
    ASSETS['CW01_B_CornerWall'] = dict(COMMON, zh='院牆轉角', build=build_b, limit=[2.3, 2.3, H_PIER], box=((-2., -.3, 0.), (.3, 2., H_PIER)),
                                       note=ZH_NOTE + ' 本件：轉角，兩邊各 2 m（中心線），交在 0.6 m 牆墩上；外框 2.3 × 2.3 m，每一邊都在 4 × 0.5 m 以內。牆墩比牆高 20 cm（頂珠到約 1.98 m），牆頂瓦脊收進牆墩側面。')
    ASSETS['CW01_C_EndWall'] = dict(COMMON, zh='院牆端頭', build=build_c, limit=[1.2, .6, H_PIER], box=((-.6, -.3, 0.), (.6, .3, H_PIER)),
                                    note=ZH_NOTE + ' 本件：端頭，0.6 m 牆加 0.6 m 牆墩，只有 Socket_A；牆墩 0.6 m 見方，比 0.5 m 牆厚寬 10 cm，比牆高 20 cm（頂珠到約 1.98 m）。')
    ASSETS['CW01_D_BreachWall'] = dict(COMMON, zh='院牆缺口段', build=build_d, limit=[4., 2.0, H], box=((-2., -1., 0.), (2., 1., H)),
                                       note=ZH_NOTE + ' 本件：缺口段 4 m，+x 端上角塌到 0.78 m；牆本身 0.5 m 厚，塌下來的土堆兩邊各攤出約 0.6 m（外框深約 1.9 m）。')


def yardwall_checks(aid, check, cfg):
    from vl_checks import _bvh
    body = _bvh([o for g, o in S['lods'][0].items() if not g.startswith('Detail_')])
    col = _bvh([S['collision_obj']]) if S.get('collision_obj') else None
    hit = lambda o, d: body(o, d)
    out = {}
    # joint faces: the end faces sit in the socket planes (footing and earth body), so the next piece meets face to face
    ends = {'A': [(-2., 0.)], 'B': [(-2., 0.), (0., 2.)], 'C': [(-.6, 0.)], 'D': [(-2., 0.), (2., 0.)]}[aid[5]]
    if aid.startswith('CW01_A'): ends = [(-2., 0.), (2., 0.)]
    res = []
    for ex, ey in ends:
        d = Vector((ex, ey, 0.)).normalized() if (ex, ey) != (0., 0.) else Vector((1, 0, 0))
        for z in (.2, .6):
            h = hit(tuple(Vector((ex, ey, z)) + d * .6), tuple(-d))
            res.append(round((h[0] - Vector((ex, ey, z))).dot(d), 4) if h else None)
    check('joint_faces_in_socket_planes', all(r is not None and abs(r) < .006 for r in res), {'offset_from_socket_plane_m': res, 'note': 'z 0.2 footing, z 0.6 earth'})
    out['joint_offsets_m'] = res
    top = (lambda h: round(h[0].z, 3) if h else None)(hit((-1. if not aid.startswith('CW01_C') else -.3, 0., 3.), (0, 0, -1)))
    check('coping_ridge_height', top is not None and 1.74 < top <= H, {'ridge_top_m': top})
    if col:
        xs = {'A': (-1.5, 0., 1.5), 'B': (-1.5, -.9), 'C': (-.3, .3), 'D': (-1.5, 0., 1.6)}['A' if aid.startswith('CW01_A') else aid[5]]
        stops = []
        for x in xs:
            for z in ((.3, .6) if aid.startswith('CW01_D') and x > 1 else (.3, 1.2)):      # under the breach only the low part stands
                h = col((x, -3., z), (0, 1, 0)); stops.append(round(h[0].y, 3) if h else None)
        check('wall_blocks_from_the_front', all(s is not None and -.32 < s < -.2 for s in stops), {'first_collision_y_m': stops, 'x_m': xs})
    if aid.startswith('CW01_D'):
        low = (lambda h: round(h[0].z, 3) if h else None)(hit((1.85, 0., 3.), (0, 0, -1)))
        full = (lambda h: round(h[0].z, 3) if h else None)(hit((-1.5, 0., 3.), (0, 0, -1)))
        check('breach_is_low_at_the_end', low is not None and .6 < low < 1.0 and full and full > 1.74, {'top_at_x1.85_m': low, 'top_at_x-1.5_m': full})
    return out
