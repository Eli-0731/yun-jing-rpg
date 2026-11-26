"""BS01 blank boundary stone at the foot of the mountain (work pack 2026-11-09 B-112h, batch B, BS01; placed at D6).

An old plain granite stele on a simple rectangular base, no writing and no carving: the face is left smooth for Socket_Inscription
(on the front face, at the middle of the writing field, its +Y = Unity forward pointing out of the face, -Y Blender), so the game
can put an inscription there later. The top has rounded shoulders and one chipped shoulder (front right, as in the chosen sheet);
moss on the lower part of the stele and on the base, a few small plants on the base beside the foot.

Sizes from the work pack (limit 1 x 0.5 x 2 m): base 1.00 x 0.50 x 0.30 m, stele 0.80 wide, 0.20 thick, top at 2.00 m.
Origin: footprint centre, bottom z = 0, front (the blank face) -Y. One 1024 atlas (Main with Detail_Small).
Reference: art/references/BS01/BS01-cand-2.png (proportions from the written sizes, not measured off the picture).
"""
import math, random
from mathutils import Vector
import cr_mats as cm
import fr_parts as FP
from cr_parts import rbox
from ti_core import S, socket, boolean

W, D, H = 1.0, .5, 2.0
BASE = (1.0, .5, .30)                     # w, d, h
ST = (.80, .20, .30 - .03, 2.0)            # stele: width, thickness, bottom (sunk 3 cm into the base), top
SHOULDER = .21                             # radius of the rounded top corners
INSCRIPTION = (0., -ST[1] / 2, 1.22)       # middle of the blank writing field on the front face


def palette():
    P = {}
    P['granite'] = cm.stone('Stele_Granite', light=(.2, .19, .17), dark=(.085, .08, .07), ochre=(.21, .175, .12), moss=1.0, lichen=.8, crack=.35, moss_low_z=1.0)
    P['granite_base'] = cm.stone('Stele_Base_Stone', light=(.185, .175, .155), dark=(.075, .07, .06), ochre=(.19, .16, .11), moss=1.3, lichen=.6, crack=.5, wet_z=.3)
    P['moss'] = cm.moss_tuft('Stele_Moss', soft=True)
    P['fern'] = cm.fern('Stele_Fern')
    P['grass'] = cm.weed_leaf('Stele_Weed', (.03, .06, .02), (.1, .17, .045), (.2, .24, .07))
    P['dry'] = cm.weed_leaf('Stele_Dry_Grass', (.1, .075, .03), (.25, .19, .08), (.4, .31, .14))
    return P


def _shoulders(hx, hz, r):
    """warp for rbox: round the two top corners (in the block's local frame, centre at the origin)."""
    cx, cz = hx - r, hz - r
    def warp(q):
        if abs(q.x) > cx and q.z > cz:
            dx, dz = abs(q.x) - cx, q.z - cz; L = math.hypot(dx, dz)
            if L > r:
                q.x = math.copysign(cx + dx * r / L, q.x); q.z = cz + dz * r / L
    return warp


def build_bs01(P):
    R = random.Random('BS01')
    kw = dict(group='Main')
    # the base: two blocks side by side (a long one and a short one), as laid stone rather than one cast block; a tight 3 mm joint,
    # small arrises so it does not read as a wide V groove, the short block set a hair out of square so the joint is not ruler straight
    for k, (x0, x1) in enumerate(((-W / 2, .1285), (.1315, W / 2))):
        rbox(f'Stele_Base_{k}', ((x0 + x1) / 2, 0., BASE[2] / 2), (x1 - x0 - (.004 if k else 0.), BASE[1] - (.004 if k else 0.), BASE[2]), P['granite_base'],
             r=.005, amp=.004, freq=3., hew=4, chips=2, seed=1 + k, div=.05, flat='zxX' if k == 0 else 'zx',
             rot=(0., 0., math.radians(.7) if k else 0.), **kw)
    w, t, z0, z1 = ST; hz = (z1 - z0) / 2
    st = rbox('Stele', (0., 0., (z0 + z1) / 2), (w, t, z1 - z0), P['granite'], r=.012, amp=.0015, freq=2.5, hew=2, chips=0, seed=2, div=.035,
              warp=_shoulders(w / 2, hz, SHOULDER), **kw)
    # the chipped shoulder, front right: two tilted cuts, a fresh break and an older one behind it
    for k, (c, s, rot) in enumerate((((.39, -.03, 1.93), (.24, .34, .2), (math.radians(14), math.radians(-34), math.radians(9))),
                                     ((.26, .03, 2.0), (.16, .34, .12), (math.radians(-8), math.radians(-16), math.radians(-6))))):
        cut = rbox(f'Cut_Chip_{k}', c, s, P['granite'], r=.015, amp=.012, freq=7., seed=10 + k, div=.015, rot=rot, **kw)
        boolean(st, cut)
    # moss: the stele's material thickens it from the foot up to about 1 m (moss_low_z); clumps on the base top round the foot; a few plants
    for j in range(5):
        x = R.choice((-1, 1)) * R.uniform(.12, .45); y = R.choice((-1, 1)) * R.uniform(.13, .2)
        FP.moss_patch('Base_Moss', (x, y, BASE[2] + .05), (0, 0, 1), R.uniform(.04, .07), P['moss'], seed=20 + j, flat=.6, snap_each=True)
    FP.fern('Base_Fern', (-.32, -.12, BASE[2]), P['fern'], R, n=6, L=.1, out=(-.3, -1, 0), detail=1, up_bias=.4, spread=1.1)
    FP.fern('Base_Fern', (.36, -.12, BASE[2]), P['fern'], R, n=5, L=.09, out=(.4, -1, 0), detail=1, up_bias=.4, spread=1.)
    for x, y in ((-.44, .16), (.44, .17), (.1, .19)):
        FP.grass_tuft('Base_Weed', (x, y, BASE[2]), R.randint(7, 11), R.uniform(.08, .14), P['grass'] if R.random() < .7 else P['dry'], R, lean=.25, detail=1, spread=.015)
    socket('Socket_Inscription', INSCRIPTION, rot=(0, 0, math.pi))     # +Y of the empty points out of the face (-Y)
    S['collision_mesh'] = collision()
    S['part_notes'] = {'base_m': BASE, 'stele_width_thickness_bottom_top_m': ST, 'shoulder_radius_m': SHOULDER,
                       'chipped': 'front right shoulder, two tilted cuts (about 0.12 m down at the corner)',
                       'Socket_Inscription': {'at_blender_xyz': list(INSCRIPTION), 'forward': 'out of the blank front face (-Y Blender)',
                                              'field_m': [.56, .9], 'use': 'the game can place an inscription decal here; the face itself has no writing'}}


def collision():
    V, F = [], []
    def prism(x0, x1, y0, y1, z0, z1):
        FP.hull_loft(V, F, [[(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)] for z in (z0, z1)])
    prism(-W / 2, W / 2, -D / 2, D / 2, 0., BASE[2])
    prism(-ST[0] / 2, ST[0] / 2, -ST[1] / 2, ST[1] / 2, BASE[2], H)
    return V, F


def register(ASSETS):
    ASSETS['BS01_BoundaryStone'] = dict(
        kind='stele', zh='山腳界碑', palette=palette, build=build_bs01, tex=1024, ver='v001',
        atlases={'Main': ['Main', 'Detail_Small']},
        limit=[W, D, H], box=((-W / 2, -D / 2, 0.), (W / 2, D / 2, H)), slot='D6_MountainFoot_BoundaryStone', ref='BS01/BS01-cand-2',
        clamp_max=.03, uv_shape='CONVEX', minTier='standard', uv_detach_zero=True,
        origin='footprint centre, bottom z = 0, front (the blank face) -Y',
        note='山腳的舊界碑（三視圖 BS01-cand-2）：灰白花崗石素面碑，立在長方石座上，碑頂兩肩圓，右前肩缺一角；碑身下半和石座長苔，石座上碑腳兩側幾叢小蕨和草。正面完全空白、不刻字，留 Socket_Inscription 給遊戲放字。碰撞：石座與碑身兩個方塊。',
        method='procedural mesh construction (art/source/roadside-landmarks-b/bs_stele.py: chiselled stone blocks, the chipped shoulder by boolean cuts); '
               'procedural granite, moss and plant shaders baked to one 1024 atlas (Main)',
        based_on='original (Blender procedural); material functions from art/source/village-houses-b')


def stele_checks(aid, check, cfg):
    from vl_checks import _bvh
    body = _bvh([o for g, o in S['lods'][0].items() if not g.startswith('Detail_')])
    col = _bvh([S['collision_obj']]) if S.get('collision_obj') else None
    # the blank face: rays from the front over the writing field all land within a few mm of one plane (no carving, nothing standing proud)
    ys = []
    for x in (-.25, -.1, .05, .2):
        for z in (.8, 1.0, 1.2, 1.4, 1.6):
            h = body((x, -3., z), (0, 1, 0)); ys.append(round(h[0].y, 4) if h else None)
    ok = all(y is not None for y in ys) and max(ys) - min(ys) < .012
    check('blank_face_flat', ok, {'face_hits_y_m': ys, 'spread_m': round(max(ys) - min(ys), 4) if ok else None, 'note': 'no writing, no carving'})
    # the top: rounded shoulders, the front right one chipped lower than the left
    down = lambda x, y: (lambda h: round(h[0].z, 3) if h else None)(body((x, y, 5.), (0, 0, -1)))
    left, right, mid = down(-.33, -.06), down(.33, -.06), down(0., 0.)
    check('top_chipped_shoulder', left and right and mid and abs(mid - H) < .01 and left - right > .03 and mid - left > .02,
          {'top_middle_m': mid, 'left_shoulder_m': left, 'right_shoulder_m': right})
    sk = S['sockets']['Socket_Inscription'].matrix_world.translation
    hit = body((sk.x, -3., sk.z), (0, 1, 0))
    check('inscription_socket_on_face', hit is not None and abs(hit[0].y - sk.y) < .015, {'socket_m': [round(v, 3) for v in sk], 'face_y_m': round(hit[0].y, 4) if hit else None})
    out = {'face_y_spread_m': round(max(ys) - min(ys), 4) if ok else None, 'top_m': [left, mid, right]}
    if col:
        f = col((0., -3., .1), (0, 1, 0)); s = col((0., -3., 1.), (0, 1, 0)); tp = col((0., 0., 5.), (0, 0, -1))
        check('collision_base_and_stele', f and s and tp and abs(f[0].y + D / 2) < .01 and abs(s[0].y + ST[1] / 2) < .01 and abs(tp[0].z - H) < .01,
              {'base_front_y_m': round(f[0].y, 3) if f else None, 'stele_front_y_m': round(s[0].y, 3) if s else None, 'top_m': round(tp[0].z, 3) if tp else None})
    return out
