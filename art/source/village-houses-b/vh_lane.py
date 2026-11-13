"""VH03 narrow long cottage (work pack 2026-11-09 B-112h, batch A): a lane-filler with its gable end to the lane.

Three-view: art/references/VH03/VH03-cand-2.png (AI, Codex image_gen; proportions from the work pack's written sizes, not the image).
Size limit 5 x 9 x 5 m. Origin: centre of the lot at ground level, front (the lane, the gable end) -Y.

A single-storey house 3.6 m wide and 5.8 m long on a low 0.25 m stone footing, its ridge along y so the gable faces the lane. The
entrance is on the long east side (a plank double door, one leaf ajar, one stone step up), two lattice windows on each long side, a
small window in the lane gable. Walls: lime plaster over a rubble stone dado, timber corner posts, wall plates, a middle rail and a
king post in each gable, all square-on (no diagonal braces). Roof: the VL pan-and-roll tiles on the VH roof curve (vh_roof.py), ridge
along y with low curled ends. At the back a low lean-to shed (2 m deep) on three timber posts against the rear gable: a single-slope
plank roof with battens, plank walls on the west and back, open to the east with firewood stacked inside.
The 0.5 m strip between the east footing and the lot edge holds what an old household keeps by the door: a lidded jar, a low bench, a
round bamboo tray hung on a peg, bamboo poles against the wall, a small firewood pile and a basket (the woven props from vh_court.py).
Materials: vl_mats 'elderly' palette (repaired plaster), timber from vh_wood.py (weathered, split firewood), the VL roof tiles, the three-atlas scheme.
"""
import math, random
import bmesh
from mathutils import Vector
from ti_core import S, box, cyl, mesh, socket, xf, T, RZ, RX
from cr_parts import rbox
import mk_mats as mm
import fr_parts as FP
import vl_mats
import vl_roof as RF
import vh_roof as VR
import vh_wood as vw
from vh_court import along, slab, window, door, plinth_rect, clay_jar, bamboo_basket, bamboo_tray

# ------------------------------------------------------------------ layout (metres, world; front -Y = the lane)
WT = .3                                  # wall thickness
XW = 1.8                                 # long walls' outer faces at x = +-1.8
YF, YB = -3.8, 2.0                       # lane gable and rear gable outer faces
YC = (YF + YB) / 2                       # ridge centre along y
PL, WTOP = .25, 2.8                      # footing top (= floor), top of the wall plates
DOOR_Y, DOOR_W, DOOR_H = -.9, 1.1, 2.2   # east door: centre y, clear width, head
ROOF = dict(z0=2.75, rise=1.7, depth_front=2.25, depth_back=2.25, xh=3.25, lift_eave=.12, lift_end=.03)
SB = 3.95                                # lean-to shed: back posts' line; it runs from the rear gable (YB) to here
SX = 1.65                                # shed posts at x = +-1.65
SH_HI, SH_LO = 2.3, 1.85                 # shed roof top at the gable and at its lower (back) edge, y = SB + .2
SH_END = SB + .2

# wall specs in world frames: ((x, y), angle, length, openings (cx, w, sill, head, kind) in wall-local x, posts at ends (a, b))
# local +y points into the house; for the long walls local x runs along world +y (east) or -y (west)
WALLS = {
    'Front': ((0., YF), 0., 2 * XW - 2 * WT - .02, [(0., .6, 1.35, 1.95, 'window')], (0, 0)),
    'Rear': ((0., YB), math.pi, 2 * XW - 2 * WT - .02, [], (0, 0)),
    'East': ((XW, YC), math.pi / 2, YB - YF, [(-2.0, .8, 1.25, 2.05, 'window'), (DOOR_Y - YC, DOOR_W, PL, DOOR_H, 'door'), (1.7, .8, 1.25, 2.05, 'window')], (1, 1)),
    'West': ((-XW, YC), -math.pi / 2, YB - YF, [(1.4, .8, 1.25, 2.05, 'window'), (-1.6, .7, 1.35, 2.0, 'window')], (1, 1)),
}


def palette():
    P = vl_mats.palette('elderly')
    vw.apply(P, 'elderly')                                   # weathered timber, plank doors, split firewood (vh_wood.py)
    P['roof'] = RF.roof_material()
    cm = __import__('cr_mats')
    P['wall_stone'] = P['stone'] + [cm.stone('Dado_Stone_Warm', light=(.2, .19, .165), dark=(.085, .08, .07), ochre=(.24, .2, .14), moss=.8, lichen=.6, crack=.6)]
    P['weave_tray'] = mm.weave('Tray_Weave', (.38, .28, .14), (.1, .07, .036), reed=.012, block=.036, green_cast=.12, wobble=.006, strip_var=.42)
    P['weave_basket'] = mm.weave('Basket_Weave', (.3, .22, .11), (.11, .078, .04), reed=.016, block=.03, plain=True, green_cast=.04, wobble=.004)
    P['hoop'] = mm.bamboo('Split_Bamboo_Hoop', green=(.08, .078, .05), straw=(.27, .22, .13))
    P['pole'] = mm.bamboo('Bamboo_Pole', green=(.09, .085, .045), straw=(.3, .23, .12))
    P['twine'] = mm.hemp('Hemp_Twine', (.18, .13, .065), twist=220.0)
    return P


# ------------------------------------------------------------------ the roof in world coordinates (frame T(0, YC) @ RZ(90 deg))
def under_world(wx, wy):
    """Underside of the main roof's boards above (wx, wy): local x = wy - YC (along the ridge), local y = -wx."""
    return VR.under(wy - YC, -wx)


def wframe(name):
    (wx, wy), a, L, ops, posts = WALLS[name]
    return T(wx, wy, 0) @ RZ(a), L, ops, posts


def walls(P, R):
    for wname in WALLS:
        M, L, ops, posts = wframe(wname)
        long_wall = any(posts)
        with xf(M):
            slab(f'Wall_{wname}', L - .02, ops, PL - .02, WTOP - .14, .0, WT, P['plaster'], P['plaster_in'])
            box(f'Wall_Plate_{wname}', (0., .1, WTOP - .07), (L + (.14 if long_wall else -.2), .26, .14), P['timber'], bevel=.012, seg=2, group='Wood', grain='x')
            box(f'Wall_Sill_Beam_{wname}', (0., -.06, PL + .05), (L - .02, .08, .1), P['timber'], bevel=.01, seg=2, group='Wood', grain='x', uvw=.6)
            blocked = [(cx - w / 2 - .08, cx + w / 2 + .08) for cx, w, sill, head, kind in ops if kind.startswith('door')]
            z = PL; zs = []
            while z < PL + .68:
                h = R.uniform(.2, .27); zs.append((z, min(z + h, PL + .72))); z += h
            for c, (za, zb) in enumerate(zs):
                x = -L / 2 + .12 + (.16 if c % 2 else 0.)
                while x < L / 2 - .14:
                    Ls = min(R.uniform(.32, .62), L / 2 - .12 - x)
                    if Ls < .14: break
                    if not any(a < x + Ls / 2 < b for a, b in blocked):
                        rbox(f'Dado_Stone_{wname}', (x + Ls / 2, -.04, (za + zb) / 2), (Ls - .02, .12, zb - za - .02), R.choice(P['wall_stone']),
                             r=.025, amp=.008, freq=2.4, hew=2, chips=1, seed=int(x * 50 + c * 7 + len(wname)), div=.3, group='Stone')
                    x += Ls
            for end, on in zip((-1, 1), posts):
                if on:
                    # corner post: reaches in through the wall to the gable slab's end, so the seam between the two plaster walls is covered
                    box(f'Wall_Post_{wname}', (end * (L / 2 - .1), .095, (PL - .02 + WTOP) / 2), (.22, .45, WTOP - PL + .02), P['timber'], bevel=.014, seg=2, group='Wood', grain='z')
            for cx, w, sill, head, kind in ops:
                box(f'Lintel_{wname}', (cx, -.03, head + .06), (w + .3, .16, .16), P['timber'], bevel=.01, seg=2, group='Wood', grain='x')
                if kind == 'window': window(P, R, f'Window_{wname}_{cx:+.1f}', cx, sill, w, head - sill)
                else: door(P, cx, w, head, PL, ajar=True)
            if long_wall:
                # the middle rail runs above the door and window lintels, clear of them
                box(f'Wall_Mid_Rail_{wname}', (0., -.02, WTOP - .3), (L - .2, .12, .1), P['timber'], bevel=.01, seg=2, group='Wood', grain='x')


def infill(P, name, p0, p1, z0, mat, n=16, inset=.08, t=.1):
    """Board or plaster infill from z0 up to the roof boards along the wall line p0 -> p1 (world), inset from its outer face (right of p0 -> p1)."""
    (ax, ay), (bx, by) = p0, p1
    L = math.hypot(bx - ax, by - ay); ux, uy = (bx - ax) / L, (by - ay) / L; nx, ny = uy, -ux
    V, F = [], []
    for q in range(n + 1):
        x, y = ax + (bx - ax) * q / n, ay + (by - ay) * q / n
        zt = under_world(x, y) + .005
        for s in (inset - t / 2, inset + t / 2):
            V.append((x - nx * s, y - ny * s, z0 - .01)); V.append((x - nx * s, y - ny * s, max(zt, z0 + .02)))
    for q in range(n):
        a = q * 4; b = a + 4
        F += [(a, b, b + 1, a + 1), (a + 2, a + 3, b + 3, b + 2), (a + 1, b + 1, b + 3, a + 3), (a, a + 2, b + 2, b)]
    F += [(0, 1, 3, 2), (n * 4, n * 4 + 2, n * 4 + 3, n * 4 + 1)]
    o = mesh(name, V, F, mat, group='Wood' if mat is P['timber'] else 'Main', grain='x', uvw=.5)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    return o


def roof_fill(P):
    """Boards from the wall plates up to the roof along the long walls; plaster gables with a king post and a rake board at each end."""
    infill(P, 'Eave_Infill_East', (XW, YF + .06), (XW, YB - .06), WTOP, P['timber'], n=24)
    infill(P, 'Eave_Infill_West', (-XW, YB - .06), (-XW, YF + .06), WTOP, P['timber'], n=24)
    infill(P, 'Gable_Front', (-XW, YF), (XW, YF), WTOP - .012, P['plaster'], n=24, t=.16, inset=.1)
    infill(P, 'Gable_Rear', (XW, YB), (-XW, YB), WTOP - .012, P['plaster'], n=24, t=.16, inset=.1)
    for y in (YF - .07, YB + .07):
        zk = under_world(0., y) - .1
        box('Gable_King_Post', (0., y, (WTOP + zk) / 2), (.16, .08, zk - WTOP), P['timber'], bevel=.01, seg=2, group='Wood', grain='z')
    for y in (YF - .06, YB + .06):
        RF.sweep_box('Gable_Rake', [(x, y, under_world(x, y) - .001) for x in [-XW + 2 * XW * j / 16 for j in range(17)]], .16, .14, P['timber'], group='Wood', grain='x')


# ------------------------------------------------------------------ footing, step
def footing(P, R):
    plinth_rect(P, R, 'Footing', -XW - .15, XW + .15, YF - .15, YB + .15, PL, 'FBLR')
    rbox('Door_Step', (XW + .15 + .17, DOOR_Y, PL / 4), (.34, 1.2, PL / 2), P['stone'][0], r=.02, amp=.004, freq=3., hew=1, chips=1, seed=330, div=.25,
         flat='zZ', group='Stone')


# ------------------------------------------------------------------ the lean-to shed at the back
def shed_z(y):
    """Top of the shed's roof boards at y (a straight slope from the gable down to the back edge)."""
    return SH_HI + (SH_LO - SH_HI) * (y - YB) / (SH_END - YB)


def shed(P, R):
    slope = math.atan2(SH_HI - SH_LO, SH_END - YB)
    under = lambda y: shed_z(y) - .034                       # underside of the boards (1.5 mm into them)
    # earth floor, three posts at the back on stone pads; a ledger fixed to the gable wall and a beam over the posts carry the rafters
    box('Shed_Floor', (0., (YB + .15 + SB + .1) / 2, .01), (2 * SX + .1, SB + .1 - YB - .15, .02), P['earth'], bevel=0., uvw=.3)
    for x in (-SX, 0., SX):
        rbox('Shed_Post_Pad', (x, SB, .05), (.24, .24, .1), P['stone'][1], r=.02, amp=.004, freq=3., hew=1, chips=1, seed=int(x * 10) + 500, div=.25, flat='zZ', group='Stone')
        box('Shed_Post', (x, SB, (.1 + under(SB) - .14) / 2), (.13, .13, under(SB) - .14 - .1), P['timber'], bevel=.01, seg=2, group='Wood', grain='z')
    box('Shed_Beam', (0., SB, under(SB) - .07), (2 * SX + .3, .14, .14), P['timber'], bevel=.01, seg=2, group='Wood', grain='x')
    box('Shed_Ledger', (0., YB + .075, under(YB + .075) - .07), (2 * SX + .3, .14, .14), P['timber'], bevel=.01, seg=2, group='Wood', grain='x')
    # rafters down the slope, the plank roof on them, battens over the plank joints
    L = (SH_END - YB + .06) / math.cos(slope); ym = (YB + SH_END) / 2 + .03
    for x in (-SX, -.55, .55, SX):
        box('Shed_Rafter', (x, ym, (under(ym) - .05)), (.09, L, .1), P['timber'], bevel=.008, seg=2, rot=(-slope, 0, 0), group='Wood', grain='y')
    nb = 13; W = 2 * SX + .4
    for i in range(nb):
        x = -W / 2 + W * (i + .5) / nb
        box('Shed_Roof_Board', (x + R.uniform(-.004, .004), ym, shed_z(ym) - .02), (W / nb - .012, L + R.uniform(-.03, .03), .025), P['boards'], bevel=.003, seg=1,
            rot=(-slope, 0, 0), group='Wood', grain='y')
    for i in range(1, nb):
        x = -W / 2 + W * i / nb
        box('Shed_Roof_Batten', (x, ym, shed_z(ym) + .002), (.05, L - .04, .022), P['timber'], bevel=.004, seg=1, rot=(-slope, 0, 0), group='Wood', grain='y', detail=1)
    # plank walls: the back and the west side, boards on end with small gaps; the east side is left open so one can walk in
    k = 0
    def plank(name, p, s):
        nonlocal k; k += 1
        box(name, p, s, P['boards'], bevel=.004, seg=1, group='Wood', grain='z', uvw=.8)
    for z in (.45, 1.3):     # girts behind the boards, post to post
        box('Shed_Girt', (0., SB + .035, z), (2 * SX + .06, .06, .09), P['timber'], bevel=.006, seg=1, group='Wood', grain='x', uvw=.5)
        box('Shed_Girt', (-SX - .035, (YB + SB) / 2, z + .1), (.06, SB - YB - .02, .09), P['timber'], bevel=.006, seg=1, group='Wood', grain='y', uvw=.5)
    n = 18
    for i in range(n):
        x = -SX - .02 + (2 * SX + .04) * (i + .5) / n; top = under(SB + .077) - .012 - R.uniform(0., .015)
        plank('Shed_Wall_Back', (x, SB + .077, (.003 + top) / 2), ((2 * SX + .04) / n - .015, .025, top - .003))
    n = 10
    for i in range(n):
        y = YB + .02 + (SB - .07 - YB - .02) * (i + .5) / n; top = under(y) - .012 - R.uniform(0., .015)
        plank('Shed_Wall_West', (-SX - .077, y, (.003 + top) / 2), (.025, (SB - .07 - YB - .02) / n - .015, top - .003))
    # split firewood stacked against the back wall, ends to the clear floor (half, third and quarter splits and a few small rounds,
    # each resting on what is below it); the front 1.2 m of the floor stays clear to walk in
    vw.stack('Shed_Firewood', -1.6, 1.2, SB - .075, 0., .02, .93, P['firewood'], R, L=.5, stagger=True, cut=.015, uvw=1.5)


# ------------------------------------------------------------------ what an old household keeps by the door (east strip, 0.5 m)
def props(P, R):
    ex = XW + .15                                             # east footing face
    clay_jar(P, 'Jar', (ex + .25, -3.05, 0.), .6, lid=True, seed=.5)
    # a low bench by the jar
    bx, by = ex + .2, -2.08
    box('Bench_Seat', (bx, by, .42), (.3, 1.0, .05), P['plank'], bevel=.006, seg=2, group='Wood', grain='y')
    for dy in (-.4, .4):
        box('Bench_Leg', (bx, by + dy, .2), (.24, .05, .4), P['plank'], bevel=.005, seg=1, group='Wood', grain='z')
    box('Bench_Stretcher', (bx, by, .14), (.04, .76, .05), P['plank'], bevel=.004, seg=1, group='Wood', grain='y', detail=1)
    # a round bamboo tray hung on a peg over the bench, its face to the east
    cyl('Tray_Peg', (XW + .04, -2.08, 1.93), .018, .1, P['timber'], axis='x', verts=8, detail=1, group='Wood')
    with xf(T(XW + .033, -2.08, 1.62) @ RZ(math.pi / 2)):
        bamboo_tray(P, (0., 0., 0.), R=.3, tilt=math.radians(87))
    # bamboo poles leaning on the wall near the lane corner
    for i in range(6):
        y = -3.68 + i * .05 + R.uniform(-.008, .008); L = R.uniform(2.3, 2.6)
        b = (ex + .3 + R.uniform(-.03, .03), y, .007 + i * .003); top = (XW + .05, y + R.uniform(-.06, .06), math.sqrt(max(L * L - .3 ** 2, 1.)))   # bases just off the ground, each at its own height
        along('Bamboo_Pole', b, top, R.uniform(.02, .028), P['pole'], verts=8, group='Main', grain='z')
    # a small pile of split firewood against the footing behind the door, and a basket at the back corner
    vw.stack('Firewood', ex + .04, ex + .34, .95, 0., .006, .26, P['firewood'], R, R=(.05, .06), L=.78, stagger=True, cut=.015, uvw=1.5)
    bamboo_basket(P, 'Basket_0', (ex + .22, 1.55, 0.), s=.85)


def growth(P, R):
    for _ in range(34):
        side = R.random()
        if side < .3: x, y = R.uniform(-XW, XW), YF - .25                   # the lane gable's foot
        elif side < .55: x, y = -XW - .25, R.uniform(YF, SB)                 # the west side
        elif side < .75: x, y = XW + .23, R.uniform(YF, SB)                  # the east strip
        else: x, y = R.uniform(-SX, SX), SB + .25                            # behind the shed
        if abs(y - DOOR_Y) < .8 and x > 0: continue
        FP.grass_tuft('Base_Weed', (x, y, 0.), R.randint(4, 8), R.uniform(.12, .32), P['grass'] if R.random() < .7 else P['dry'], R, lean=.3, detail=1, spread=.025)


# ------------------------------------------------------------------ collision
def collision():
    V, F = [], []
    def prism(x0, x1, y0, y1, z0, z1):
        FP.hull_loft(V, F, [[(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)] for z in (z0, z1)])
    prism(-XW - .15, XW + .15, YF - .15, YB + .15, 0., WTOP)                 # the house on its footing, flush (no ledge), door closed
    prism(XW + .15, XW + .49, DOOR_Y - .6, DOOR_Y + .6, 0., PL / 2)         # the door step
    # the shed: open to the east and walkable inside; its back wall, west wall, back corner post and the firewood stack block
    prism(-SX - .1, SX + .07, SB - .07, SB + .1, 0., SH_LO)                  # back wall with its posts
    prism(-SX - .1, -SX + .07, YB + .15, SB - .07, 0., SH_LO)               # west wall
    prism(-1.62, 1.22, SB - .62, SB - .07, 0., .95)                          # firewood stack
    ex = XW + .15
    prism(ex + .02, ex + .47, -3.3, -2.8, 0., .58)                           # jar
    prism(ex + .05, ex + .35, -2.6, -1.56, 0., .45)                         # bench
    prism(ex + .02, ex + .3, .1, 1.0, 0., .3)                                # firewood pile
    return V, F


# ------------------------------------------------------------------ build
def build_vh03(P):
    R = random.Random('VH03')
    VR.configure(**ROOF)
    footing(P, R); walls(P, R); roof_fill(P)
    def cell(kind, side, x, k, r):          # old roof: old and dark-fired tiles, moss low on the west slope
        if side == 1 and k < 5 and r < .3: return 2 + (4 if kind == 'roll' else 0)
        if r > .93: return 3 + (4 if kind == 'roll' else 0)
        return (0 if r < .6 else 1) + (4 if kind == 'roll' else 0)
    with xf(T(0., YC, 0.) @ RZ(math.pi / 2)):
        VR.build(P, cell=cell)
    shed(P, R)
    props(P, R); growth(P, R)
    socket('Socket_Door', (XW, DOOR_Y, PL), rot=(0, 0, -math.pi / 2))
    socket('Socket_Lane', (0., YF - .5, 0.), rot=(0, 0, math.pi))
    socket('Socket_Shed', (0., (YB + SB) / 2, .02))
    S['collision_mesh'] = collision()
    S['prop'] = dict(kind='vlane')
    __import__('vl_house').occluded_uvw()


NOTE = ('窄長小屋（三視圖 VH03-cand-2）：山牆朝巷子的窄長單層屋，3.6 × 5.8 m，坐在 0.25 m 石基上，屋脊順著長向。'
        '門開在東側長邊（木板對開門，一扇半開，門前一級踏石），長邊各兩扇直欞窗，山牆一扇小窗。'
        '牆是石灰泥加亂石牆腳，轉角木柱、牆頂木樑、腰枋、山牆中柱都橫平豎直，沒有斜撐。屋頂用 VL 的筒瓦與板瓦，屋脊兩端低調起翹。'
        '屋後靠山牆接一段 2 m 深的矮棚：單坡木板頂加壓條，西面和背面是木板牆，東面敞開，後半堆柴、前半留空地，人可以走進去。'
        '老人家：舊而深色的木頭、補過的灰泥、石腳長苔；東側門邊放有木蓋的陶缸、矮板凳、掛在木釘上的竹匾、靠牆的竹竿、一小堆柴、一個竹籃（竹匾、竹籃、草在 Detail_Small）。'
        '碰撞：屋子連石基（門關著）、門前踏石、矮棚的背牆、西牆與柴堆（棚子東面敞開，前半可以走進去）、陶缸、板凳、柴堆。')


def register(ASSETS):
    ASSETS['VH03_NarrowCottage'] = dict(
        zh='窄長小屋', kind='vlane', cond='elderly', palette=palette, build=build_vh03, limit=(5., 9., 5.), tex=2048, ver='v001',
        box=((-2.5, -4.5, 0.), (2.5, 4.5, 5.)), ref='VH03/VH03-cand-2', slot='A1_QingxiVillage_House', minTier='standard', clamp_max=.03, uv_shape='CONVEX',
        atlases={'Main': ['Main', 'Detail_Small'], 'Stone': ['Stone'], 'Wood': ['Wood']},
        origin='centre of the lot at ground level, front (the lane, the gable end) -Y',
        method='procedural mesh construction (art/source/village-houses-b/vh_lane.py, vh_roof.py, props from vh_court.py); procedural shaders baked to three 2048 atlases (Main, Stone, Wood); roof tiles on the shared 1024 VL tile texture (VL_Shared)',
        based_on='new outline (work pack 2026-11-09 VH03); materials and roof tiles shared with VL01-05, VH01 and VH02',
        note=NOTE)


# ------------------------------------------------------------------ measured checks
def vlane_checks(aid, check, cfg):
    from vl_checks import _bvh
    body = _bvh([o for g, o in S['lods'][0].items() if not g.startswith('Detail_')])
    col = _bvh([S['collision_obj']]) if S.get('collision_obj') else None
    down = lambda x, y: (lambda h: round(h[0].z, 3) if h else None)(body((x, y, 12.), (0, 0, -1)))
    hit = lambda p, d, ax, f=body: (lambda h: round(h[0][ax], 3) if h else None)(f(p, d))
    # the gable faces the lane: the ridge runs along y (high at both ends of the house, low over the long walls), the lane face is a plaster gable
    ridge = [down(0., y) for y in (YF + .4, YC, YB - .4)]
    eaves = [down(x, YC) for x in (-XW, XW)]
    gable = hit((0., -12., 3.4), (0, 1, 0), 1)
    check('gable_end_faces_lane', all(ridge) and all(eaves) and min(ridge) > max(eaves) + 1.2 and max(ridge) <= 5. and gable is not None and abs(gable - YF) < .3,
          {'ridge_top_along_y_m': ridge, 'roof_over_long_walls_m': eaves, 'lane_face_hit_y_m': gable, 'gable_wall_y_m': YF})
    # door on the long side: a ray at door height goes into the reveal (the leaves stand back in the wall), beside it the wall face stops it
    at_door = hit((9., DOOR_Y - .25, 1.3), (-1, 0, 0), 0); beside = hit((9., DOOR_Y - 1.5, 1.6), (-1, 0, 0), 0)
    check('door_on_long_side', at_door is not None and beside is not None and at_door < beside - .05 and YB - YF > 2 * XW + 1.,
          {'hit_at_door_x_m': at_door, 'hit_beside_door_x_m': beside, 'long_side_m': round(YB - YF, 2), 'gable_width_m': 2 * XW})
    # the lean-to: its roof lower than the main eave, reaching back from the rear gable
    sh = [down(0., y) for y in (YB + .8, SB - .2)]
    check('rear_lean_to_lower', all(sh) and max(sh) < min(eaves) - .3 and sh[0] > sh[1] and min(sh) > 1.5,
          {'shed_roof_top_m': sh, 'main_eave_over_walls_m': eaves, 'shed_back_m': SH_END})
    out = {'ridge_m': ridge, 'shed_roof_m': sh}
    if col:
        cg = {'lane': hit((0., -12., 1.2), (0, 1, 0), 1, col), 'east': hit((12., -3.3, 1.2), (-1, 0, 0), 0, col), 'west': hit((-12., -1., 1.2), (1, 0, 0), 0, col),
              'shed_back': hit((0., 12., 1.2), (0, -1, 0), 1, col)}
        step = col((XW + .3, DOOR_Y, 2.), (0, 0, -1))
        check('collision_closed_step_up', all(v is not None for v in cg.values()) and step and abs(step[0].z - PL / 2) < .01,
              {'collision_faces_m': cg, 'step_top_m': round(step[0].z, 3) if step else None})
        inside = col((0., (YB + .15 + SB - .62) / 2, 1.8), (0, 0, -1))
        side_open = col((9., (YB + .15 + SB - .62) / 2, 1.0), (-1, 0, 0))
        check('shed_open_to_walk_in', side_open is not None and side_open[0].x < -SX + .1 and (inside is None or inside[0].z < .05),
              {'ray_through_open_side_first_hit_x_m': round(side_open[0].x, 3) if side_open else None, 'west_wall_inner_x_m': round(-SX + .07, 3),
               'clear_floor_y_m': [round(YB + .15, 2), round(SB - .62, 2)]})
        out['collision'] = cg
    return out
