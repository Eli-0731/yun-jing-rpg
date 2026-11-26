"""CW02 yard gate, open and closed (work pack 2026-11-11 B-40h, batch A).

Chosen sheet CW02-cand-2: two square timber posts on stone plinths carry a lintel, a beam over it and two short tie beams front to back;
a small gable of the same dark grey (#3A4048) pan-and-roll tiles as the CW01 coping sits on purlins over them, barge boards at both
gable ends. Two old plank doors (vertical boards, three battens on the yard side, a pivot post on the hinge edge turning in a stone
socket below and a wooden keeper above, an iron ring on the street side); a worn stone threshold with a step stone in front. Short
rammed earth stubs either side, built exactly like CW01 (same footing, lifts, eave course and coping) so the wall runs on from them.
No door-god prints, no writing.

Frame: ground z = 0, front (street) -Y, gate centre on x = 0. Sockets: Socket_A at x -1.2, Socket_B at x +1.2 (end faces of the stubs,
ground level, wall centre line), the same as a CW01 straight's ends; Socket_HingeL / Socket_HingeR on the door pivot axes at the
threshold top. Doors are their own objects (Detail_DoorL, Detail_DoorR) with the pivot axis as the place to turn them about.
  CW02_A open: both doors turned 90 deg into the yard (+y);   CW02_B closed.
Opening between the posts 1.34 m; with the doors open, 1.24 m clear.
"""
import math, random
from mathutils import Matrix, Vector, noise
from ti_core import S, box, cyl, torus, socket, xf, T
from cr_parts import rbox
import fr_parts as FP
import vl_mats, cr_mats as cm, mk_mats as mm
import cw_parts as CP
import cw_wall as CW

W, D, H = 2.4, 1.2, 2.8
PX, POST = .75, .16                 # post centres, post section
INNER = PX - POST / 2               # 0.67: inner face of a post
THR_H = .12                         # threshold top
LINTEL_Z = 2.14                     # underside of the lintel
DOOR_Y = -.08                       # door plane (front of the post centre line)
LEAF_W = INNER - .004
ROOF = dict(half=.565, z_eave=2.45, z_ridge=2.698)
RX = 1.0                            # roof (tiles) to x +-1.0
STUB0 = PX + POST / 2 + .005        # stubs from 0.835 to 1.2


def palette():
    P = CW.palette()
    P['timber'] = cm.wood('Gate_Timber', (.05, .028, .014), (.19, .105, .05), grey=.4, ground_h=.15, moss=False)
    P['door'] = cm.wood('Door_Plank', (.045, .026, .013), (.2, .115, .056), grey=.5, ground_h=.12, polish=0.)
    P['iron'] = vl_mats.iron('Door_Iron')
    P['thr'] = cm.stone('Threshold_Stone', light=(.24, .23, .21), dark=(.1, .095, .088), ochre=(.2, .18, .14), moss=.3, lichen=.2, crack=.4,
                        polish=(.42, .4, .37))
    return P


def stubs(P, R):
    for sx in (-1, 1):
        a, b = (-W / 2, -STUB0) if sx < 0 else (STUB0, W / 2)
        CW.run(P, R, f'Stub_{sx}', a, b, flat_lo=sx < 0, flat_hi=sx > 0, seed=10 + sx)


def frame(P, R):
    t = P['timber']
    post_top = 2.30                                          # tie beams 2.30-2.44, under the roof boards
    for sx in (-1, 1):
        x = sx * PX
        rbox(f'Post_Plinth_{sx}', (x, 0., .14), (.3, .34, .28), P['thr'], r=.02, amp=.006, hew=3, chips=2, seed=20 + sx, div=.05, flat='z', taper=(.9, .9), group='Stone')
        rbox(f'Post_{sx}', (x, 0., (.28 + post_top) / 2), (POST, POST, post_top - .28), t, r=.012, amp=.003, freq=2., hew=4, seed=24 + sx, div=.06, group='Wood', grain='z')
        # tie beam front to back on the post top, carrying the eave purlins; a knee brace under it each way
        rbox(f'Tie_Beam_{sx}', (x, 0., post_top + .07), (.14, 2 * ROOF['half'] - .12, .14), t, r=.01, amp=.003, hew=2, seed=26 + sx, div=.06, group='Wood', grain='y')
        for sy in (-1, 1):
            CP_brace(f'Knee_Brace_{sx}_{sy}', (x, sy * .1, post_top - .32), (x, sy * .4, post_top - .002), t)
        # door keeper (連楹) on the inside of the lintel and the stone pivot socket (門枕石) at the threshold end
        rbox(f'Pivot_Stone_{sx}', (sx * (INNER - .05), DOOR_Y + .17, .07), (.22, .26, .14), P['thr'], r=.02, amp=.005, chips=2, hew=2, seed=30 + sx, div=.05, flat='z',
             group='Stone')
    rbox('Lintel', (0., 0., LINTEL_Z + .08), (2 * PX + .16, .14, .16), t, r=.01, amp=.003, hew=2, seed=40, div=.06, group='Wood', grain='x')
    rbox('Door_Keeper', (0., DOOR_Y + .13, LINTEL_Z + .03), (2 * INNER + .06, .1, .08), t, r=.008, amp=.002, seed=41, div=.06, group='Wood', grain='x')
    # purlins: ridge and both eaves, to the barge boards; a strut from the tie beams up to the ridge purlin
    zt = CP.cap_profile(ROOF['half'], ROOF['z_eave'], ROOF['z_ridge'])
    for y in (-.42, 0., .42):
        zz = zt(y) - .06
        rbox(f'Purlin_{y:+.2f}', (0., y, zz - .05), (2 * RX + .08, .09, .1), t, r=.008, amp=.002, seed=44, div=.08, group='Wood', grain='x')
    for sx in (-1, 1):
        x = sx * PX
        box(f'Ridge_Strut_{sx}', (x, 0., (post_top + .14 + zt(0.) - .16) / 2), (.09, .09, zt(0.) - .16 - post_top - .14), t, bevel=.006, group='Wood', grain='z')
        # barge boards along both slopes at the gable end
        xb = sx * (RX + .055)
        for sy in (-1, 1):
            pts = [(xb, sy * ROOF['half'] * q / 8, zt(sy * ROOF['half'] * q / 8) - .02) for q in range(9)]
            import vl_roof as RF
            RF.sweep_box(f'Barge_Board_{sx}_{sy}', pts, .03, .1, t, up=(0, 0, 1), group='Wood', grain='y')
    S['frame'] = dict(post_top=round(post_top, 3), lintel_underside=LINTEL_Z)


def CP_brace(name, a, b, mat):
    import vl_roof as RF
    RF.sweep_box(name, [a, b], .07, .08, mat, up=(1, 0, 0), group='Wood', grain='y')


def threshold(P, R):
    rbox('Threshold', (0., DOOR_Y + .02, THR_H / 2), (2 * INNER + .02, .2, THR_H), P['thr'], r=.025, amp=.006, chips=2, hew=3, seed=50, div=.05, flat='zxX',
         group='Stone', warp=lambda q: _worn(q))
    rbox('Step_Stone', (0., DOOR_Y - .3, .045), (1.5, .36, .09), P['thr'], r=.02, amp=.008, chips=3, hew=3, seed=51, div=.05, flat='z', group='Stone',
         warp=lambda q: _worn(q, .006))
    for k, x in enumerate((-.42, .0, .42)):
        rbox('Yard_Flag', (x + R.uniform(-.02, .02), DOOR_Y + .4, .03), (.4, .38, .06), P['stone'][k], r=.02, amp=.006, chips=2, hew=2, seed=52 + k, div=.05,
             flat='z', group='Stone')


def _worn(q, d=.012):
    """Feet have worn a shallow dip into the middle of the top."""
    if q.z > 0: q.z -= d * math.exp(-(q.x / .45) ** 2)


def leaf(P, side, open_):
    """One door leaf in its own group. side -1 = left (hinge at x -INNER), +1 = right. Built closed about its pivot, then turned."""
    grp = 'Detail_DoorL' if side < 0 else 'Detail_DoorR'
    hx = side * INNER
    ang = (-side * math.pi / 2) if open_ else 0.             # left leaf turns counter-clockwise into +y, right leaf clockwise
    M = T(hx, DOOR_Y, 0.) @ Matrix.Rotation(ang, 4, 'Z')
    Rl = random.Random(f'leaf{side}')
    z0, z1 = THR_H + .012, LINTEL_Z - .012
    with xf(M):
        # local: pivot on the origin, the leaf runs along -side*x (towards the middle), front face at -y
        n = 5; wb = LEAF_W / n
        for k in range(n):
            xc = -side * (wb * (k + .5)); th = .045 + Rl.uniform(-.003, .003)
            top = z1 - Rl.uniform(0, .015) - (.02 if k == n - 1 else 0.)
            rbox(f'Door_Plank_{side}_{k}', (xc, 0., (z0 + top) / 2), (wb - .006, th, top - z0), P['door'], r=.006, amp=.003, freq=3., chips=1 if Rl.random() < .4 else 0,
                 seed=60 + k + (side > 0) * 10, div=.06, group=grp, grain='z')
        # pivot post on the hinge edge, its pins into the socket stone and the keeper
        cyl(f'Door_Pivot_{side}', (side * .005, 0., (z0 + z1) / 2), .035, z1 - z0 + .02, P['door'], verts=12, group=grp, grain='z')
        cyl(f'Door_Pin_{side}', (side * .005, 0., z0 - .05), .02, .1, P['door'], verts=10, group=grp, grain='z')
        cyl(f'Door_Pin_Top_{side}', (side * .005, 0., z1 + .06), .02, .12, P['door'], verts=10, group=grp, grain='z')
        # three battens across the yard side
        for z in (z0 + .22, (z0 + z1) / 2, z1 - .22):
            rbox(f'Door_Batten_{side}', (-side * LEAF_W / 2, .045, z + Rl.uniform(-.02, .02)), (LEAF_W - .04, .028, .11), P['door'], r=.006, amp=.002, seed=80, div=.06,
                 group=grp, grain='x')
        # iron ring pull on the street side near the meeting edge, with its round back plate
        rx = -side * (LEAF_W - .1); rz = 1.02
        cyl(f'Ring_Plate_{side}', (rx, -.027, rz), .045, .008, P['iron'], axis='y', verts=16, group=grp)
        torus(f'Door_Ring_{side}', (rx, -.04, rz - .055), .05, .007, P['iron'], rot=(math.pi / 2, 0, 0), major=20, minor=6, group=grp)
        # an old patch: a short board nailed across a split low on the right leaf
        if side > 0:
            rbox('Door_Patch', (-LEAF_W * .62, -.03, z0 + .32), (.3, .018, .1), P['door'], r=.004, amp=.002, chips=1, seed=90, div=.05, rot=(0, .12, 0), group=grp, grain='x')
    socket(f'Socket_Hinge{"L" if side < 0 else "R"}', (hx, DOOR_Y, THR_H))


def roof(P, R):
    CP.tile_cap(P, 'Gate_Roof', -RX, RX, ROOF['half'], ROOF['z_eave'], ROOF['z_ridge'], pitch=.2, roll_r=.042, ends=(True, True), seed=7,
                board_mat=P['timber'], board_group='Wood')


def growth(P, R):
    for _ in range(14):
        x = R.uniform(-1.15, 1.15); y = R.choice((-1, 1)) * R.uniform(.2, .45)
        if abs(x) < .8 and -.6 < y < .6: continue
        FP.grass_tuft('Gate_Grass', (x, y, 0.), R.randint(5, 9), R.uniform(.1, .22), P['grass'] if R.random() < .7 else P['dry'], R, lean=.3, detail=1, spread=.03)
    for k in range(4):
        FP.moss_patch('Roof_Moss', (R.uniform(-.8, .8), R.choice((-1, 1)) * .35, 2.65), (0, 0, 1), R.uniform(.05, .09), P['moss'], seed=600 + k, flat=.5, snap_each=True)
    for sx in (-1, 1):
        FP.moss_patch('Plinth_Moss', (sx * PX, -.17, .08), (0, -1, .2), .07, P['moss'], seed=620 + sx, flat=.6, snap_each=True)


def build(open_):
    def f(P):
        R = random.Random('CW02' + ('open' if open_ else 'shut'))
        stubs(P, R); frame(P, R); threshold(P, R); roof(P, R)
        for side in (-1, 1): leaf(P, side, open_)
        CW.growth(P, R, [(Matrix(), -W / 2, -STUB0), (Matrix(), STUB0, W / 2)])
        growth(P, R)
        socket('Socket_A', (-W / 2, 0., 0.), rot=(0, 0, math.pi)); socket('Socket_B', (W / 2, 0., 0.))
        S['collision_mesh'] = collision(open_)
        S['part_notes'] = {'opening_between_posts_m': round(2 * INNER, 3), 'clear_with_doors_open_m': round(2 * INNER - 2 * .055, 3),
                           'threshold_top_m': THR_H, 'lintel_underside_m': LINTEL_Z, 'doors': 'own objects Detail_DoorL / Detail_DoorR; turn them about Socket_HingeL / Socket_HingeR (vertical axis)',
                           'door_leaf_m': {'width': round(LEAF_W, 3), 'height': round(LINTEL_Z - THR_H - .024, 3)}, 'roof': ROOF, **S.get('frame', {}),
                           'stubs': 'built with cw_wall.run, the same section as CW01; Socket_A / Socket_B at x -1.2 / +1.2 like a CW01 straight',
                           'state': 'open (doors turned 90 deg into the yard, +y)' if open_ else 'closed'}
    return f


def collision(open_):
    V, F = [], []
    def prism(x0, x1, y0, y1, z0, z1):
        FP.hull_loft(V, F, [[(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)] for z in (z0, z1)])
    t = CP.FOOT_T / 2
    for sx in (-1, 1):
        a, b = (-W / 2, -STUB0) if sx < 0 else (STUB0, W / 2)
        prism(a, b, -t, t, 0., CW.EAVE_Z)
        prism(sx * PX - .15, sx * PX + .15, -.17, .17, 0., 2.3)                          # post on its plinth
    prism(-INNER, INNER, DOOR_Y - .08, DOOR_Y + .12, 0., THR_H)                           # threshold: stepped over
    prism(-.75, .75, DOOR_Y - .48, DOOR_Y - .12, 0., .09)                                 # step stone
    if open_:
        for sx in (-1, 1):
            prism(sx * INNER - (.06 if sx > 0 else 0.), sx * INNER + (.06 if sx < 0 else 0.), DOOR_Y, DOOR_Y + LEAF_W + .02, THR_H, LINTEL_Z)
    else:
        prism(-INNER, INNER, DOOR_Y - .03, DOOR_Y + .06, THR_H, LINTEL_Z)
    prism(-PX - .15, PX + .15, -.08, .08, LINTEL_Z, 2.3)                                  # lintel and beams over the opening
    return V, F


COMMON = dict(kind='gate', palette=palette, tex=2048, ver='v001',
              atlases={'Main': ['Main', 'Detail_Small'], 'Stone': ['Stone'], 'Wood': ['Wood', 'Detail_DoorL', 'Detail_DoorR']},
              limit=[W, D, H], box=((-W / 2, -D / 2, 0.), (W / 2, D / 2, H)), slot='A1_Yard_Gate', ref='CW02/CW02-cand-2', clamp_max=.03, uv_detach_zero=True,
              origin='gate centre on the ground, front (street) -Y; stubs end at x -1.2 / +1.2 like a CW01 straight',
              method='procedural mesh construction (art/source/village-yards-b/cw_gate.py, cw_wall.py, cw_parts.py); procedural shaders baked to three 2048 atlases '
                     '(Main, Stone, Wood)',
              based_on='original (Blender procedural); stub walls the same as CW01; grass, moss and iron from the VL set in art/source/village-houses-b')
NOTE = ('院門（三視圖 CW02-cand-2）：兩根方木柱立在石柱礎上，上有門楣、額枋和前後兩根橫梁，梁下斜撐；檁條上一個小懸山瓦頂，瓦和 CW01 壓頂同一種黛瓦（#3A4048），'
        '兩端博風板。兩扇舊木板門（直板、內側三道橫帶、門軸立在門枕石上、上面有連楹，外側一個鐵門環），右扇下方釘一塊補板；門檻石中間被踩出淺凹，門外一塊踏石。'
        '兩邊短夯土牆和 CW01 同一個斷面，x ±1.2 m 端面就是 Socket_A／Socket_B，可以直接接院牆。門扇是獨立物件（Detail_DoorL、Detail_DoorR），'
        '繞 Socket_HingeL／Socket_HingeR 的垂直軸轉就能開關。柱間淨寬 1.34 m，門全開後淨寬 1.24 m。不貼門神、不寫字。')


def register(ASSETS):
    ASSETS['CW02_A_GateOpen'] = dict(COMMON, zh='院門（開著）', build=build(True), note=NOTE + ' 本件：兩扇門往院內（+y）開 90°。')
    ASSETS['CW02_B_GateClosed'] = dict(COMMON, zh='院門（關著）', build=build(False), note=NOTE + ' 本件：兩扇門關著。')


def gate_checks(aid, check, cfg):
    from vl_checks import _bvh
    lod0 = S['lods'][0]
    body = _bvh([o for g, o in lod0.items()])
    col = _bvh([S['collision_obj']]) if S.get('collision_obj') else None
    out = {}
    # clear opening at shin, waist and head height across the gate, just inside the door plane
    widths = []
    for z in (.4, 1.1, 1.8):
        a = body((0., DOOR_Y + .3, z), (-1, 0, 0)); b = body((0., DOOR_Y + .3, z), (1, 0, 0))
        widths.append(round(b[0].x - a[0].x, 3) if a and b else None)
    if aid.startswith('CW02_A'):
        check('open_doorway_clear_at_least_1.2m', all(w is not None and w >= 1.2 for w in widths), {'clear_m_at_z_0.4_1.1_1.8': widths})
        thru = [body((x, -1.5, 1.0), (0, 1, 0)) for x in (-.3, 0., .3)]
        check('open_doorway_see_through', all(h is None or h[0].y > .55 for h in thru), {'first_hit_y_m': [round(h[0].y, 3) if h else None for h in thru]})
    else:
        shut = [body((x, -1.5, 1.0), (0, 1, 0)) for x in (-.4, 0.01, .4)]
        check('closed_doors_fill_the_opening', all(h and abs(h[0].y - (DOOR_Y - .02)) < .04 for h in shut), {'first_hit_y_m': [round(h[0].y, 3) if h else None for h in shut]})
    hd = body((0., 0., 1.2), (0, 0, 1))
    check('headroom_under_lintel', hd and hd[0].z >= 2.05, {'lintel_underside_m': round(hd[0].z, 3) if hd else None})
    res = []
    for ex in (-W / 2, W / 2):
        d = Vector((math.copysign(1, ex), 0, 0))
        for z in (.2, .6):
            h = body(tuple(Vector((ex, 0., z)) + d * .6), tuple(-d))
            res.append(round((h[0] - Vector((ex, 0., z))).dot(d), 4) if h else None)
    check('stub_ends_in_socket_planes', all(r is not None and abs(r) < .006 for r in res), {'offset_m': res})
    ridge = body((0., 0., 4.), (0, 0, -1))
    check('roof_ridge_height', ridge and 2.7 < ridge[0].z <= H, {'ridge_top_m': round(ridge[0].z, 3) if ridge else None})
    if col:
        h = col((0., -2., .6), (0, 1, 0))
        out['collision_first_hit_y_from_front_m'] = round(h[0].y, 3) if h else None
    out['clear_widths_m'] = widths
    return out
