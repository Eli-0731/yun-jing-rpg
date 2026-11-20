"""XB01 low stone slab bridge and a set of five stepping stones (work pack 2026-11-11 B-40h, batch A).

Chosen sheet XB01-cand-3: long rough-cut slabs, two side by side, in three spans over four short piers of stacked dressed stone that
batter in towards the top, each pier capped with a long bearing stone across the bridge; no railings; slab edges worn round, joints
open a finger's width, moss and dark wet stone up to the waterline on the piers, grass at their feet. Separately, five flat-topped
stepping stones of different sizes. Not WM07 (an arch) and not the QX creek plank.

Frame: z = 0 is the stream bed under the piers (the bridge stands in the water; the banks are the core team's terrain), front -Y,
bridge along x. Deck top about 1.0 m; the slabs end flush at x -3 / +3 so the bank meets them there.
  XB01_A bridge     6.0 x 1.8 x ~1.1 m
  XB01_B stepping stones: five in a slight curve along x, tops 0.2-0.28 m above the bed, gaps 0.1-0.18 m.
"""
import math, random
from mathutils import Matrix, Vector, noise
from ti_core import S, box, socket, xf, T
from cr_parts import rbox
import fr_parts as FP
import vl_mats, cr_mats as cm
import cw_parts as CP

L, WB, DECK = 6.0, 1.8, 1.0
SLAB_T = .2
SUPPORTS = (-2.58, -.9, .9, 2.58)
WET = .38                      # waterline on the piers


def palette():
    P = vl_mats.palette('diligent')
    P['slab'] = [cm.stone(f'Bridge_Slab_{i}', light=l, dark=d, ochre=(.24, .2, .14), moss=.6, lichen=.5, crack=.45, polish=(.4, .38, .34))
                 for i, (l, d) in enumerate((((.26, .235, .2), (.11, .1, .085)), ((.24, .22, .19), (.1, .092, .08)), ((.27, .25, .215), (.12, .108, .09))))]
    P['pier'] = [cm.stone(f'Pier_Stone_{i}', light=l, dark=d, ochre=(.22, .19, .14), moss=1.1, lichen=.5, crack=.5, wet_z=WET, moss_low_z=.6)
                 for i, (l, d) in enumerate((((.23, .22, .2), (.1, .096, .088)), ((.21, .2, .185), (.09, .087, .08)), ((.25, .235, .21), (.11, .1, .09))))]
    P['bed'] = cm.stone('Pier_Bed_Stone', light=(.2, .19, .17), dark=(.08, .075, .07), moss=1.2, lichen=.2, crack=.3, wet_z=WET + .1)
    P['step'] = [cm.stone(f'Stepping_Stone_{i}', light=l, dark=d, ochre=(.22, .2, .15), moss=.9, lichen=.4, crack=.35, wet_z=.16, polish=(.38, .36, .33))
                 for i, (l, d) in enumerate((((.24, .23, .21), (.1, .096, .088)), ((.22, .21, .19), (.09, .087, .08))))]
    return P


# ------------------------------------------------------------------ bridge
def pier(P, R, k, x, end):
    """Stacked dressed stone, 4-5 courses, battered; a long bearing stone on top across the bridge."""
    top = DECK - SLAB_T - .16                         # under the bearing stone
    w0, w1 = (.78, .6) if not end else (.8, .64)      # along x at the foot / top
    d0, d1 = 1.66, 1.52                                # across
    n = 3; zs = [0.]
    for i in range(n): zs.append(top * (i + 1) / n + (R.uniform(-.02, .02) if i < n - 1 else 0.))
    for i in range(n):
        za, zb = zs[i], zs[i + 1]; t = (za + zb) / 2 / top
        w = w0 + (w1 - w0) * t; d = d0 + (d1 - d0) * t
        y = -d / 2
        while y < d / 2 - .1:
            Ls = R.uniform(.38, .75)
            if d / 2 - (y + Ls) < .2: Ls = d / 2 - y
            # each course: one stone through the pier where it is short, else two facing stones with rubble between
            for sx, ww in (((0,), w),) if w < .7 else (((-1, 1), w / 2 - .01),):
                for s_ in (sx if isinstance(sx, tuple) else (sx,)):
                    cx = x + s_ * (w / 4 + .005) if s_ else x
                    rbox(f'Pier_{k}_Stone', (cx + R.uniform(-.012, .012), y + Ls / 2, (za + zb) / 2), (ww + R.uniform(-.02, .02), Ls - .014, zb - za - .012),
                         R.choice(P['pier']), r=.05, amp=.02, freq=2.8, chips=4, hew=4, seed=k * 100 + i * 10 + int(y * 10) + 50, div=.06,
                         flat='z' if i == 0 else '', group='Stone')
            y += Ls
        box(f'Pier_{k}_Core', (x, 0., (za + zb) / 2), (w - .08, d - .08, zb - za), P['bed'], bevel=.01, group='Stone')
    # bearing stone across the top, a little longer than the deck is wide
    rbox(f'Pier_{k}_Cap', (x, 0., top + .08), (w1 + .08, WB + .06, .16), R.choice(P['slab']), r=.03, amp=.01, chips=3, hew=3, seed=k * 7 + 3, div=.06,
         group='Stone')
    # bed stones round the foot, half buried
    for j in range(7):
        a = R.uniform(0, math.tau)
        FP.pebble(f'Pier_{k}_Foot_Stone', (max(-2.86, min(2.86, x + math.cos(a) * (w0 / 2 + .04))), math.sin(a) * (d0 / 2 - .02), .04), R.uniform(.07, .14), P['bed'], seed=k * 20 + j,
                  flat=.55, seg=10, ring=6, group='Stone')


def slabs(P, R):
    """Two slabs side by side in each span, resting on the bearing stones; each its own size and a little twist, edges worn round."""
    ends = [-L / 2] + [(SUPPORTS[i] + SUPPORTS[i + 1]) / 2 * 0 + SUPPORTS[i] for i in (1, 2)] + [L / 2]
    spans = [(-L / 2, -.9), (-.9, .9), (.9, L / 2)]
    for s, (a, b) in enumerate(spans):
        for row, yc in enumerate((-.45, .45)):
            a1 = a + (.006 if s else 0.); b1 = b - (.006 if s < 2 else 0.)
            wid = .86 + R.uniform(-.05, .0); th = SLAB_T + R.uniform(-.02, .02)
            flat = ('x' if s == 0 else '') + ('X' if s == 2 else '')
            tilt = R.uniform(-.008, .008)
            rbox(f'Deck_Slab_{s}_{row}', ((a1 + b1) / 2, yc + R.uniform(-.008, .008), DECK - th / 2), (b1 - a1, wid, th), R.choice(P['slab']), r=.06, amp=.02, freq=1.9,
                 chips=7, hew=6, seed=300 + s * 10 + row, div=.07, flat=flat, rot=(tilt, 0, R.uniform(-.006, .006)), group='Stone',
                 warp=lambda q: _worn_top(q))


def _worn_top(q):
    """Feet have worn the middle of each slab a few millimetres lower and rounder."""
    if q.z > 0: q.z -= .008 * math.exp(-(q.y / .3) ** 2) - .008 * noise.noise(Vector((q.x * 2.5, q.y * 2.5, 4.)))


def bridge_growth(P, R):
    for k, x in enumerate(SUPPORTS):
        for j in range(6):
            sy = R.choice((-1, 1))
            FP.grass_tuft('Pier_Grass', (max(-2.85, min(2.85, x + R.uniform(-.4, .4))), sy * R.uniform(.72, .8), 0.), R.randint(6, 11), R.uniform(.14, .28), P['grass'], R,
                          lean=.15, detail=1, spread=.03)
        for j in range(4):
            sy = R.choice((-1, 1))
            FP.moss_patch('Pier_Moss', (x + R.uniform(-.3, .3), sy * .8, R.uniform(.1, WET)), (0, sy, .1), R.uniform(.08, .14), P['moss'], seed=k * 9 + j, flat=.6,
                          snap_each=True)
    for j in range(10):                                   # moss in the slab joints and along the deck edges
        x = R.choice((-.9, .9)) + R.uniform(-.05, .05) if j < 5 else R.uniform(-2.8, 2.8)
        y = R.uniform(-.2, .2) if j < 5 else R.choice((-1, 1)) * .86
        FP.moss_patch('Deck_Moss', (x, y, DECK + .01), (0, 0, 1), R.uniform(.04, .08), P['moss'], seed=500 + j, flat=.5, snap_each=True)


def build_a(P):
    R = random.Random('XB01_A')
    for k, x in enumerate(SUPPORTS): pier(P, R, k, x, k in (0, 3))
    slabs(P, R); bridge_growth(P, R)
    socket('Socket_BankA', (-L / 2, 0., DECK), rot=(0, 0, math.pi)); socket('Socket_BankB', (L / 2, 0., DECK))
    V, F = [], []
    def prism(x0, x1, y0, y1, z0, z1):
        FP.hull_loft(V, F, [[(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)] for z in (z0, z1)])
    prism(-L / 2, L / 2, -WB / 2, WB / 2, DECK - SLAB_T - .02, DECK)
    for x in SUPPORTS:
        prism(x - .42, x + .42, -.84, .84, 0., DECK - SLAB_T - .02)
    S['collision_mesh'] = (V, F)
    S['part_notes'] = {'deck_top_m': DECK, 'slab_thickness_m': SLAB_T, 'spans_m': [[-3., -.9], [-.9, .9], [.9, 3.]], 'supports_x_m': list(SUPPORTS),
                       'waterline_m': WET, 'z0': 'stream bed under the piers', 'Socket_BankA/B': 'deck ends at x -3 / +3, deck height: where the bank path meets the bridge',
                       'railings': 'none'}


# ------------------------------------------------------------------ stepping stones
STONES = [(-1.22, -.04, .56, .48, .24), (-.6, .06, .5, .42, .26), (0., .1, .64, .54, .28), (.6, .04, .46, .4, .22), (1.18, -.08, .52, .46, .25)]   # x, y, along, across, top


def build_b(P):
    R = random.Random('XB01_B')
    for k, (x, y, a, b, top) in enumerate(STONES):
        # a boulder set in the bed: rounded body, the top ground flat and worn smooth by feet; wet and mossy below the water mark
        boulder(f'Stepping_Stone_{k}', (x, y), a, b, top, P['step'][k % 2], seed=700 + k, rot=R.uniform(-.4, .4))
        for j in range(3):
            ang = R.uniform(0, math.tau)
            FP.moss_patch('Step_Moss', (x + math.cos(ang) * a * .45, y + math.sin(ang) * b * .45, .1), (math.cos(ang), math.sin(ang), .2), R.uniform(.05, .09), P['moss'],
                          seed=800 + k * 5 + j, flat=.6, snap_each=True)
        for j in range(4):
            ang = R.uniform(0, math.tau)
            FP.pebble('Bed_Pebble', (x + math.cos(ang) * (a / 2 + .06), y + math.sin(ang) * (b / 2 + .05), .0), R.uniform(.03, .07), P['bed'], seed=900 + k * 5 + j,
                      flat=.5, seg=8, ring=5, group='Stone')
    socket('Socket_StartStone', (STONES[0][0], STONES[0][1], STONES[0][4])); socket('Socket_EndStone', (STONES[-1][0], STONES[-1][1], STONES[-1][4]))
    V, F = [], []
    for x, y, a, b, top in STONES:
        n = 10
        FP.hull_loft(V, F, [[(x + a / 2 * .92 * math.cos(math.tau * i / n), y + b / 2 * .92 * math.sin(math.tau * i / n), z) for i in range(n)] for z in (0., top)])
    S['collision_mesh'] = (V, F)
    gaps = [round(STONES[i + 1][0] - STONES[i + 1][2] / 2 - (STONES[i][0] + STONES[i][2] / 2), 3) for i in range(4)]
    S['part_notes'] = {'stones_m': [{'x': x, 'y': y, 'along': a, 'across': b, 'top': t} for x, y, a, b, t in STONES], 'gaps_m': gaps,
                       'z0': 'stream bed', 'note': 'tops ground flat; a step of 0.6-0.7 m centre to centre'}


def boulder(name, c, a, b, top, mat, seed=0, rot=0., bury=.1):
    """A lumpy river boulder (a x b in plan), its crown ground flat at z = top, its foot buried in the bed."""
    from ti_core import mesh
    so = Vector((seed * 1.7, seed * .3, seed * .11)); cs, sn = math.cos(rot), math.sin(rot)
    seg, ring = 24, 12; h = top + bury
    V = []
    for j in range(ring + 1):
        ph = -math.pi / 2 + math.pi * j / ring
        for i in range(seg):
            th = math.tau * i / seg; d = Vector((math.cos(ph) * math.cos(th), math.cos(ph) * math.sin(th), math.sin(ph)))
            k = 1 + .16 * noise.noise(so + d * 1.3) + .06 * noise.noise(so + d * 3.6)
            x, y = d.x * a / 2 * k, d.y * b / 2 * k
            Rv = h / 1.35; z = top - .35 * Rv + d.z * Rv * k
            if z > top - .004: z = top - .004 + (z - top) * .05 + .0025 * noise.noise(Vector((x * 9, y * 9, seed)))   # ground flat, a little dished by feet
            V.append((c[0] + x * cs - y * sn, c[1] + x * sn + y * cs, z))
    F = []
    for j in range(ring):
        for i in range(seg):
            a0 = j * seg + i; b0 = j * seg + (i + 1) % seg
            F.append((a0, b0, b0 + seg, a0 + seg))
    return mesh(name, V, F, mat, smooth=True, group='Stone', grain='z')


def _flat_top(q, h):
    """Grind the top flat 2 cm under the boulder's crown (the bottom part stays rounded and is buried 10 cm in the bed)."""
    lim = h / 2 - .02
    if q.z > lim: q.z = lim + (q.z - lim) * .08


COMMON = dict(palette=palette, tex=2048, ver='v001', atlases={'Main': ['Main', 'Detail_Small'], 'Stone': ['Stone']}, slot='A1_to_A3_Creek_Crossing',
              ref='XB01/XB01-cand-3', clamp_max=.11, uv_detach_zero=True,
              method='procedural mesh construction (art/source/village-yards-b/xb_bridge.py); procedural shaders baked to two 2048 atlases (Main, Stone)',
              based_on='original (Blender procedural); stone, grass and moss materials from the VL set in art/source/village-houses-b')
NOTE = ('石板橋與踏石（三視圖 XB01-cand-3）：粗鑿長石板兩塊並排、分三跨，架在四個石砌矮墩上；墩用五層方石疊成、往上收分，頂上一條橫的承石；沒有欄杆。'
        '石板邊角磨圓、中間被踩出淺凹，板縫一指寬、長青苔；墩腳到水位線（0.38 m）石頭濕黑長苔，腳邊有草和半埋的河石。另一件是五顆大小不同、頂面磨平的踏石。不寫字。')


def register(ASSETS):
    ASSETS['XB01_A_SlabBridge'] = dict(COMMON, kind='slabbridge', zh='石板橋', build=build_a, limit=[L, WB, 1.2], box=((-L / 2, -WB / 2, 0.), (L / 2, WB / 2, 1.2)),
                                       origin='middle of the bridge on the stream bed (z 0 under the piers), front -Y, bridge along x; deck top 1.0 m',
                                       note=NOTE + ' 本件：橋，橋面頂 1.0 m（z 0 是墩腳的溪床），兩端 x ±3 m 平切，接岸。')
    ASSETS['XB01_B_SteppingStones'] = dict(COMMON, clamp_max=.17, kind='steppingstones', zh='溪中踏石（五顆）', build=build_b, limit=[3.2, 1.0, .4], box=((-1.6, -.5, 0.), (1.6, .5, .4)),
                                           origin='middle of the row on the stream bed, front -Y, row along x',
                                           note=NOTE + ' 本件：踏石五顆，沿 x 排成微彎一列，頂面離溪床 0.22–0.28 m，石間空隙 0.1–0.18 m，一步 0.6–0.7 m。')


def slabbridge_checks(aid, check, cfg):
    from vl_checks import _bvh
    body = _bvh([o for g, o in S['lods'][0].items() if not g.startswith('Detail_')])
    deck = []
    for x in (-2.9, -2., -.6, 0., 1.4, 2.9):
        for y in (-.65, -.3, .3, .65):
            h = body((x, y, 3.), (0, 0, -1)); deck.append(round(h[0].z, 3) if h else None)
    check('deck_walkable_level', all(d is not None and abs(d - DECK) < .05 for d in deck), {'deck_top_m': deck, 'note': 'x -2.9..2.9 on the slabs (not on the 4 cm joints between them)'})
    # no railings: a level ray along the deck edge 0.5 m up meets nothing
    rail = [body((-3.5, sy * .85, DECK + .5), (1, 0, 0)) for sy in (-1, 1)]
    check('no_railings', all(r is None for r in rail), {'hits': [tuple(round(v, 3) for v in r[0]) if r else None for r in rail]})
    under = [body((x, 0., .3), (0, 1, 0)) for x in (-1.8, 0., 1.8)]
    check('water_runs_under_the_spans', all(u is None for u in under), {'note': 'rays across under each span at 0.3 m'})
    return {'deck_m': deck}


def steppingstones_checks(aid, check, cfg):
    from vl_checks import _bvh
    body = _bvh([o for g, o in S['lods'][0].items() if not g.startswith('Detail_')])
    tops = []
    for x, y, a, b, t in STONES:
        h = body((x, y, 2.), (0, 0, -1)); tops.append(round(h[0].z, 3) if h else None)
    check('five_flat_tops', len(tops) == 5 and all(tp is not None and abs(tp - t) < .03 for tp, (*_, t) in zip(tops, STONES)), {'tops_m': tops})
    flat = []
    for x, y, a, b, t in STONES:
        zs = [body((x + dx * a * .25, y + dy * b * .25, 2.), (0, 0, -1)) for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1))]
        flat.append(round(max(z[0].z for z in zs if z) - min(z[0].z for z in zs if z), 3))
    check('tops_ground_flat', all(f < .025 for f in flat), {'top_relief_m': flat})
    return {'tops_m': tops}
