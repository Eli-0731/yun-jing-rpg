"""SG02 turning landing (work pack B-104h part 2): 4 x 4 x 0.4 m, a flight of SG01 can meet any edge, a lantern base in one corner.

Three-view SG02/LANDING candidate-01: a ring of dressed edging stones round a 3 x 3 field of large slabs, a round lotus base in a corner.
Origin: centre of the footprint at the bottom; the walking surface is level at z = 0.4.
SG01 joins an edge with its Socket_Top on the landing's Socket_Edge_*: the top tread of SG01 (z 1.6 in SG01) is flush with the landing top.
A flight leaving the landing stands on the ground at the landing-top level with its first riser on the edge (its Socket_Bottom on Socket_Edge_*).
Turn the landing so the lantern corner sits between the two edges no flight uses.
"""
import math, random
from mathutils import Vector, Matrix
from ti_core import S, socket, lathe, surface
import mk_mats as mk
from cr_parts import rbox
import sg_parts as SG

HALF, TOP, RING = 2., .4, .4
FIELD = HALF - RING                  # 1.6: the slab field is 3.2 m square
LANTERN = (1.32, 1.32)               # corner lotus base centre (the +X +Y corner)
POST = HALF - .2                     # balustrade post centres on the edging ring, 0.2 m in from the outer face


def palette():
    P = SG.palette()
    P['iron'] = mk.cast_iron('Cramp_Iron')
    return P


def ring(P, R):
    """Edging ring: four corner blocks and dressed stones along each side between them; full 0.4 m height, top flush with the slabs."""
    for cx in (-1, 1):
        for cy in (-1, 1):
            rbox('Ring_Corner', (cx * (HALF - RING / 2), cy * (HALF - RING / 2), TOP / 2), (RING - .003, RING - .003, TOP), R.choice(P['cope']), r=.016, amp=.002,
                 freq=4., hew=3, chips=0, seed=R.randrange(999), div=.08, flat='zZ' + ('X' if cx < 0 else 'x') + ('Y' if cy < 0 else 'y'))
    for side in range(4):          # 0: -Y, 1: +X, 2: +Y, 3: -X ; built on the -Y side, then turned
        ang = side * math.pi / 2
        y = -FIELD; first = True
        while y < FIELD - .02:
            L = R.uniform(.62, 1.05) if not first else R.uniform(.45, .8)
            first = False
            if FIELD - (y + L) < .35: L = FIELD - y
            pos = Matrix.Rotation(ang, 3, 'Z') @ Vector((y + L / 2, -(HALF - RING / 2), TOP / 2))
            rbox(f'Ring_{side}', tuple(pos), (L - .003, RING - .003, TOP), R.choice(P['cope']), r=.016, amp=.002, freq=4., hew=4, chips=0,
                 seed=R.randrange(999), div=.08, flat='zZY', rot=(0, 0, ang))
            y += L


def field(P, R):
    """3 x 3 slabs, 0.15 m thick, 8 mm soil joints; the middle row and column polished by feet."""
    n = 3; step = 2 * FIELD / n; gap = .008
    for i in range(n):
        for j in range(n):
            x0, y0 = -FIELD + i * step, -FIELD + j * step
            xa, xb = x0 + (gap / 2 if i else .0015), x0 + step - (gap / 2 if i < n - 1 else .0015)
            ya, yb = y0 + (gap / 2 if j else .0015), y0 + step - (gap / 2 if j < n - 1 else .0015)
            o = rbox(f'Slab_{i}{j}', ((xa + xb) / 2, (ya + yb) / 2, TOP - .075), (xb - xa, yb - ya, .15), R.choice(P['tread']), r=.012, amp=.002, freq=3.5,
                     hew=2, chips=0, seed=i * 7 + j, div=.09, flat='zZ')
            SG.set_wear(o, lambda p: .45 * (math.exp(-(p.x / .8) ** 2) + math.exp(-(p.y / .8) ** 2) - .5 * math.exp(-((p.x ** 2 + p.y ** 2) / 1.2))))   # a worn cross, lighter than a flight's treads
            o['tread'] = True
    for k in range(1, n):          # soil in the joints, a little below the top
        c = -FIELD + k * step
        rbox('Joint_Soil', (c, 0, TOP - .03), (gap + .004, 2 * FIELD - .01, .05), P['soil'], r=.002, div=.2, seed=k)
        rbox('Joint_Soil', (0, c, TOP - .032), (2 * FIELD - .01, gap + .004, .05), P['soil'], r=.002, div=.2, seed=k + 5)


def lantern_base(P):
    """Round lotus base (candidate-01): a plinth, a belt of 16 petals, a drum; Socket_Lantern on its top centre for the existing G01."""
    x, y = LANTERN; mat = P['cope'][0]; z0 = TOP - .02
    prof = [(0., 0.), (.43, 0.), (.43, .06), (.41, .085), (.32, .095), (.32, .215), (.31, .225), (.31, .3), (.355, .315), (.355, .36), (.335, .375), (0., .375)]
    lathe('Lantern_Base', prof, (x, y, z0), mat, seg=48)
    for k in range(16):
        a = math.tau * k / 16
        c = Vector((x + math.cos(a) * .318, y + math.sin(a) * .318, z0 + .09)); out = Vector((math.cos(a), math.sin(a), 0)); side = Vector((-out.y, out.x, 0))
        def fn(u, v, c=c, out=out, side=side):
            t = (u - .5) * 2
            bulge = .07 * math.sin(math.pi * min(v * .62 + .2, 1.)) * (1 - t * t) * (1 - .55 * v)
            w = .068 * (1 - .75 * v ** 2.2)
            return tuple(c + side * (t * w) + Vector((0, 0, .135 * v)) + out * (bulge - .004))
        surface('Lantern_Petal', 6, 5, fn, mat, solid=.01, grain='z')
    socket('Socket_Lantern', (x, y, z0 + .375))


def growth(P):
    Rg = random.Random('SG02_growth')
    step = 2 * FIELD / 3
    for k in range(1, 3):       # moss along the slab joints, more on the -X (shaded) half, none in the worn middle
        c = -FIELD + k * step
        for i in range(4):
            t = Rg.uniform(-FIELD + .2, FIELD - .2)
            for x, y in ((c, t), (t, c)):
                if abs(x) < .5 and abs(y) < .5: continue
                if x < .3 or Rg.random() < .35:
                    SG.moss_patch('Joint_Moss', (x, y, TOP + .001), (0, 0, 1), Rg.uniform(.04, .065), P['moss'], seed=int(t * 100) + k, flat=.6)
    for i in range(10):         # grass where the field meets the ring
        a = Rg.uniform(-FIELD + .15, FIELD - .15); s = Rg.choice((-1, 1))
        x, y = (a, s * (FIELD + .002)) if Rg.random() < .5 else (s * (FIELD + .002), a)
        SG.grass_tuft('Edge_Grass', (x, y, TOP), Rg.randint(3, 6), Rg.uniform(.06, .11), P['grass'] if Rg.random() < .7 else P['dry'], Rg, spread=.02)
    lx, ly = LANTERN
    for a in (2.6, 3.4, 4.1):   # and at the lantern base foot
        SG.grass_tuft('Base_Grass', (lx + math.cos(a) * .45, ly + math.sin(a) * .45, TOP), Rg.randint(4, 7), Rg.uniform(.08, .13), P['grass'], Rg, spread=.03)
    # no moss on the outer ring faces: they are the 4 m footprint, and a patch standing on them was pressed flat into the face plane


def cramps(P):
    """A cracked ring stone on the -Y face held by two iron cramps (candidate-01): each flat bar lies in a channel cut 12 mm into the
    stone, its face 2 mm below the stone face. (Bars standing proud of the face crossed the 4 m footprint and the size clamp pressed
    them flat into the face plane.)"""
    from ti_core import boolean, box
    x0 = .35; z = .22; f = -HALF
    for k, (dx, dz) in enumerate(((-.09, 0.), (.09, .03))):
        x = x0 + dx
        for o in [o for o in S['parts'] if o.name.startswith('Ring_0')]:
            xs = [(o.matrix_world @ Vector(c)).x for c in o.bound_box]
            if min(xs) < x + .063 and max(xs) > x - .063:
                boolean(o, box(f'Cramp_Channel_{k}', (x, f + .002, z + dz), (.126, .02, .028), None, bevel=0))
        rbox('Cramp_Bar', (x, f + .006, z + dz), (.12, .008, .022), P['iron'], r=.003, div=.03, seed=k)


def sg02_landing(P):
    R = random.Random('SG02_Landing')
    ring(P, R); field(P, R)
    lantern_base(P)
    cramps(P)
    growth(P)
    for nm, (x, y, a) in {'S': (0, -HALF, math.pi), 'N': (0, HALF, 0.), 'E': (HALF, 0, -math.pi / 2), 'W': (-HALF, 0, math.pi / 2)}.items():
        socket(f'Socket_Edge_{nm}', (x, y, TOP), rot=(0, 0, a))
    for nm, (x, y) in {'SW': (-POST, -POST), 'SE': (POST, -POST), 'NE': (POST, POST), 'NW': (-POST, POST),
                       'S': (0, -POST), 'N': (0, POST), 'E': (POST, 0), 'W': (-POST, 0)}.items():
        socket(f'Socket_Post_{nm}', (x, y, TOP))
    S['prop'] = dict(kind='landing', top=TOP, half=HALF)
    V, F = [], []
    SG.prism(V, F, [(-HALF, 0.), (HALF, 0.), (HALF, TOP), (-HALF, TOP)], -HALF, HALF)
    lx, ly = LANTERN; r = .43; h = TOP - .02 + .375
    SG.prism(V, F, [(ly - r, TOP - .02), (ly + r, TOP - .02), (ly + r, h), (ly - r, h)], lx - r, lx + r)
    S['collision_mesh'] = (V, F)


NOTE = ('轉折平台（三視圖 SG02/LANDING candidate-01）：4 × 4 m、厚 0.4 m，走面水平在 z 0.4。外圍一圈 0.4 m 寬的收邊石（全高），中間 3 × 3 塊 0.15 m 厚大石板，'
        '接縫填土長苔，中間十字被腳磨亮。+X +Y 角一座蓮瓣圓燈座（直徑 0.86 m、高 0.375 m，16 瓣），頂面中心 Socket_Lantern 放現成 G01 石燈（底 0.6 m）。'
        '-Y 面一塊收邊石用兩支鐵鋦釘補著。四邊中點 Socket_Edge_S/N/E/W（z 0.4、朝外）：SG01 的 Socket_Top 對上就是上來的段，'
        'Socket_Bottom 對上就是往上走的段（那段立在與平台頂同高的地面上）；平台轉 90° 讓燈座落在沒有樓梯的兩邊之間。'
        '收邊石上 8 個 Socket_Post_*（離外緣 0.2 m，角與邊中點）給 SG03 欄杆柱，柱中心距 1.8 m；有樓梯的那邊不放邊中點的柱。')


def register(ASSETS):
    ASSETS['SG02_Landing'] = dict(zh='轉折平台', kind='landing', palette=palette, build=sg02_landing, limit=(4., 4., .8), tex=2048, ver='v001',
        box=((-2., -2., 0.), (2., 2., .8)), ref='SG02/LANDING', slot='B1_SectGateStairs', minTier='standard', clamp_max=.03,
        origin='centre of the footprint at the bottom; the walking surface is level at z 0.4', note=NOTE)
