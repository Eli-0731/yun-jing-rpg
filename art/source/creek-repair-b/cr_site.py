"""Work-site kit: CR03 stockpiles in three stages, CR04 tools, CR06 earth channel, CR08 flume and its trestles.

Stages are three objects sharing one origin (Stage_Low / Stage_Mid / Stage_High); the game shows one at a time.
CR06 / CR08 keep the B02 channel interface at both ports: clear width 0.40, floor top z 0.10, wall top z 0.40, water z 0.28.
"""
import math, random
from mathutils import Vector, noise
from ti_core import S, RX, RZ, T, cyl, lathe, mesh, socket, sphere, surface, torus, xf
import ti_mats as tm
import mk_mats as mm
import cr_mats as cm
from cr_parts import rbox, rope, lash, xlash, pole, sheet, log, between, tuft

STAGES = ('Stage_Low', 'Stage_Mid', 'Stage_High')
CLEAR, FLOOR, WALL, WATER = .2, .1, .4, .28


def collide(*boxes): S['collision'] = list(boxes)


# ------------------------------------------------------------------ CR03 stone
def stone_palette():
    P = {'stone': cm.stone('Granite_Block', light=(.3, .285, .25), dark=(.13, .12, .1), ochre=(.27, .22, .14), moss=.55, lichen=.4, crack=.7), 'broken': cm.stone('Granite_Broken', light=(.36, .33, .27), dark=(.17, .155, .125), moss=.1, lichen=.1, crack=.9)}
    P['chip'] = cm.stone('Granite_Chips', moss=0, lichen=0, crack=.2); P['moss'] = cm.moss_tuft('Joint_Moss', soft=True)
    return P


def cr03_stone(P):
    """Big rough-split blocks in three courses, uneven sizes, the top course stepped in; a broken wedge set aside at the front."""
    R = random.Random(303)
    # x, y, bottom z, w, d, h
    blocks = [(-.1, -.3, 0, .74, .62, .46), (.64, -.26, 0, .64, .6, .38), (-.74, -.28, 0, .46, .56, .34), (-.5, .34, 0, .8, .62, .4), (.34, .36, 0, .86, .6, .44),
              (.84, .38, 0, .28, .48, .28), (-.42, -.18, .35, .66, .54, .3), (.28, -.1, .46, .74, .6, .3), (-.3, .34, .41, .62, .5, .26), (.34, .38, .45, .5, .46, .24), (-.1, .08, .71, .6, .42, .28)]
    placed = []
    for x, y, z, w, d, h in blocks:
        placed.append(((x + R.uniform(-.015, .015), y + R.uniform(-.015, .015), z + h / 2 - (.03 if z > 0 else 0)), (w, d + (.03 if z > 0 else 0), h + (.03 if z > 0 else 0)), R.uniform(-.09, .09), R.randint(1, 900)))
    counts = {'Stage_Low': 3, 'Stage_Mid': 6, 'Stage_High': 11}
    for st in STAGES:
        for i, (c, sz, yaw, seed) in enumerate(placed[:counts[st]]):
            rbox('Block', c, sz, P['stone'], r=.022, amp=.028, freq=6., chips=14, hew=20, seed=seed, div=.04, rot=(0, 0, yaw), group=st)
            if i < 6:
                for k in range(5):
                    a = R.uniform(0, 6.28)
                    tuft('Joint_Moss', (c[0] + math.cos(a) * sz[0] * .52, c[1] + math.sin(a) * sz[1] * .52, R.uniform(.015, .05)), R.uniform(.022, .045), P['moss'], seed=k + i, group=st)
        rbox('Broken', (-.66, -.62, .11), (.42, .3, .22), P['broken'], r=.012, amp=.012, freq=9., chips=7, hew=8, seed=71, div=.04, rot=(.04, .05, .38), group=st, skew=(.12, .02), taper=(.5, .8))
        for k in range(5 if st == 'Stage_Low' else 9):
            a = R.uniform(3.4, 6.1); d = R.uniform(.72, .95)
            rbox('Chip', (math.cos(a) * d * .95, math.sin(a) * d * .72, .025), (R.uniform(.05, .11), R.uniform(.04, .08), R.uniform(.03, .05)), P['chip'], r=.004, amp=.004, freq=30., chips=2, seed=k, div=.03, rot=(R.uniform(-.3, .3), R.uniform(-.3, .3), a), group=st, detail=1)
    collide(((-.96, -.72, 0), (.96, .68, 1.0)))


# ------------------------------------------------------------------ CR03 timber
def timber_palette():
    P = {'frame': cm.wood('Rack_Cedar', (.06, .034, .018), (.2, .118, .06), ground_h=.15, grey=.3), 'log': cm.wood('Log_Cedar', (.075, .043, .022), (.27, .165, .085), ground_h=0, grey=.15)}
    P['plank'] = cm.wood('Plank_New', (.15, .09, .045), (.4, .27, .14), ground_h=0, grey=.04); P['hemp'] = mm.hemp('Hemp_Rope', (.2, .125, .055), twist=40.0)
    return P


def cr03_timber(P):
    """Round posts and rails tied with rope. Logs lie on the upper bars, sawn planks stack on the lower ones."""
    R = random.Random(304)
    X, Y = 1.03, .37
    for sx in (-1, 1):
        for sy in (-1, 1):
            log('Rack_Post', [(sx * X, sy * Y, 0), (sx * X + R.uniform(-.008, .008), sy * Y, .6), (sx * X, sy * Y, 1.2)], .052, P['frame'], seg=12, lump=.05, seed=int(sx * 3 + sy + 7), grain='z')
        for z, r in ((.17, .046), (.62, .042)):
            log('Rack_Bar', [(sx * X, -Y - .07, z), (sx * X, 0, z + .004), (sx * X, Y + .07, z)], r, P['frame'], seg=10, lump=.05, seed=int(z * 40 + sx), grain='y')
        between('Rack_Brace', (sx * X, -Y + .05, .2), (sx * X, Y - .05, .6), .06, .035, P['frame'], r=.005, amp=.002, seed=3 + sx, div=.08)
        between('Side_Brace', (sx * X, -Y - .06, .66), (sx * (X - .42), -Y - .06, 1.1), .06, .035, P['frame'], r=.005, amp=.002, seed=5 + sx, div=.08)
    for sy in (-1, 1):
        for z, r in ((1.1, .044), (.17, .044)):
            log('Rack_Rail', [(-1.24, sy * (Y + .06), z), (0, sy * (Y + .06), z + .006), (1.24, sy * (Y + .06), z)], r, P['frame'], seg=12, lump=.05, seed=int(z * 30 + sy), grain='x')
        for sx in (-1, 1):
            for z in (1.1, .62, .17):
                bar_x = abs(z - .62) < .01
                xlash('Rack_Lash', (sx * X, sy * (Y + (.0 if bar_x else .06)), z), (0, 0, 1), .046, (0, 1, 0) if bar_x else (1, 0, 0), .036, .0062, P['hemp'], tail=(sx * .02, 0, -.09) if z > 1 and sy < 0 else None, detail=1)
    # a newer board nailed over a cracked rail
    rbox('Mend_Board', (-.1, -Y - .112, .17), (.52, .016, .11), P['plank'], r=.003, amp=.001, seed=4, div=.08, rot=(.02, .05, 0))
    def logs(st, items, seed):
        for k, (y, z, r) in enumerate(items):
            log('Log', [(-1.18, y, z), (0, y + R.uniform(-.01, .01), z + .004), (1.18 - .03 * k, y, z)], r, P['log'], seg=16, lump=.05, seed=seed + k, group=st, grain='x')
    def planks(st, layers, seed):
        for L in range(layers):
            z = .216 + .03 + L * .048
            for c, (x0, length) in enumerate(((-.5, .95), (.5, .95))):
                if L == layers - 1 and c == 1 and layers > 2: length = .72
                for k, y in enumerate((-.22, 0, .22)):
                    rbox('Plank', (x0 + (.03 if L % 2 else -.03), y, z), (length, .21, .044), P['plank'], r=.004, amp=.0018, freq=8., seed=seed + L * 9 + c * 3 + k, div=.09, group=st, grain='x')
    z0 = .662
    row = [(-.2, z0 + .075, .075), (-.02, z0 + .08, .08), (.17, z0 + .072, .072)]
    top = [(-.11, z0 + .21, .07), (.08, z0 + .205, .066)]
    planks('Stage_Low', 2, 10)
    planks('Stage_Mid', 3, 30); logs('Stage_Mid', row[:2], 50)
    planks('Stage_High', 5, 70); logs('Stage_High', row + top, 90)
    collide(((-1.25, -.52, 0), (1.25, .52, 1.2)))


# ------------------------------------------------------------------ CR03 mud
def mud_palette():
    P = {'mud': cm.mud('Creek_Silt'), 'plank': cm.wood('Walk_Plank', (.1, .062, .032), (.3, .2, .11), ground_h=0, grey=.3, wet_z=None), 'stone': cm.stone('Silt_Stones', light=(.2, .185, .155), dark=(.08, .07, .055), moss=.2, lichen=0, crack=.2)}
    return P


def cr03_mud(P):
    """A rough heap of creek silt: lumps and shovel slumps, footprints trodden into it, a long plank down one side to wheel a barrow up."""
    steps = [(-.34, -.42), (-.1, -.5), (.12, -.38), (-.5, -.2)]
    R = random.Random(305)
    for st, rad, h, seed, plank in (('Stage_Low', .62, .22, 3., None), ('Stage_Mid', .82, .48, 7., (.8, .62)), ('Stage_High', .98, .74, 11., (1., .86))):
        def edge(a, seed=seed):
            return min(1., (1 + .1 * math.sin(a * 3 + seed) + .06 * math.sin(a * 5 + seed * 2) + .03 * math.sin(a * 11)) * .9)
        def height(x, y, a, d, rad=rad, h=h, seed=seed, plank=plank):
            dome = max(0., 1 - d) ** .8
            fall = min(1., dome * 2.5)
            n = noise.fractal(Vector((x * 2.2 / rad + seed, y * 2.2 / rad, 0)), 1., 2., 4) * .13
            lumps = (abs(noise.noise(Vector((x * 6.5, y * 6.5, seed)))) * .1 + abs(noise.noise(Vector((x * 15, y * 15, seed + 4)))) * .055 + abs(noise.noise(Vector((x * 34, y * 34, seed + 9)))) * .022) * fall
            z = h * dome * (1 + n) + lumps
            if h > .4:
                for fx, fy in steps:
                    q = math.hypot((x - fx) / .06, (y - fy) / .12)
                    if q < 1: z -= .035 * (1 - q * q)
            return min(.795, max(0., z))
        def fn_(u, v, rad=rad):
            a = u * math.tau; d = v ** .85; r = d * edge(a) * rad
            x, y = math.cos(a) * r, math.sin(a) * r
            return (x, y, height(x, y, a, d))
        surface('Heap', 128, 56, fn_, P['mud'], closed_u=True, group=st, grain='z')
        if plank:
            # a board laid up the slope from the ground: raised until nothing of the heap pokes through it
            foot = Vector((rad * .92, -rad * .46, .018)); run = Vector((-rad * 1.3, rad * .24, 0)).normalized(); L = plank[1] * 1.5; slope = 0.
            for k in range(1, 40):
                t = k / 39 * L; q = foot + run * t
                for off in (-.12, 0., .12):
                    x_, y_ = q.x - run.y * off, q.y + run.x * off; r_ = math.hypot(x_, y_); a_ = math.atan2(y_, x_) % math.tau
                    d_ = r_ / (edge(a_) * rad)
                    if d_ < 1: slope = max(slope, (height(x_, y_, a_, d_) + .018 - foot.z) / t)
            slope *= .94; L = min(L, .7 / max(slope, .01)); top = foot + run * L + Vector((0, 0, slope * L))
            between('Walk_Plank', tuple(top), tuple(foot), .25, .036, P['plank'], r=.005, amp=.004, freq=5., chips=3, seed=int(seed), div=.07, group=st)
        for k, (a, d) in enumerate(((.5, 1.), (2.6, .98), (4.3, 1.), (5.5, .95))):
            rbox('Old_Stone', (math.cos(a) * rad * d * .9, math.sin(a) * rad * d * .9, .04), (.14, .11, .08), P['stone'], r=.012, amp=.01, freq=14., chips=4, hew=5, seed=k + int(seed), div=.03, rot=(0, 0, a), group=st, detail=1)
    S['collision'] = [((-.68, -.68, 0), (.68, .68, .46))]


# ------------------------------------------------------------------ CR04 tools
def tools_palette():
    P = {'ash': cm.wood('Handle_Ash', (.085, .05, .026), (.25, .16, .085), ground_h=0, polish=.3, grey=.08), 'iron': mm.cast_iron('Dark_Iron'), 'hemp': mm.hemp('Hemp_Mend', (.22, .14, .06), twist=40.0)}
    P['mud'] = cm.mud('Blade_Mud'); P['strip'] = cm.wood('Bamboo_Strip', (.17, .115, .05), (.36, .26, .12), ground_h=0, grey=.05); P['strip2'] = cm.wood('Bamboo_Strip_Dark', (.11, .07, .03), (.27, .19, .085), ground_h=0, grey=.12)
    P['split'] = mm.bamboo('Bamboo_Rim'); P['block'] = cm.wood('Tamper_Block', (.05, .03, .016), (.17, .1, .05), ground_h=.1, grey=.3)
    P['stave'] = cm.wood('Bucket_Stave', (.06, .036, .018), (.2, .125, .065), ground_h=.05, grey=.25); P['mortar'] = cm.stone('Lime_Mortar', light=(.46, .44, .39), dark=(.27, .26, .23), ochre=(.4, .38, .33), moss=0, lichen=0, crack=.25)
    return P


def blade(name, c, w, L, mat, group, curl=.02, solid=.0035):
    """Round-nosed spade blade, shoulders square at the top, dished across."""
    def fn_(u, v):
        hw = w / 2 * max(.0, (1 - v ** 2.8)) ** .5
        x = (u - .5) * 2 * hw
        return (c[0] + x, c[1] + curl * ((u - .5) * 2) ** 2 + .012 * math.sin(v * 3.1), c[2] + L * (1 - v))
    return surface(name, 16, 22, fn_, mat, solid=solid, group=group, grain='z')


def cr04(P):
    # spade: 1.3 m, lying on its back, blade up; a forked D-grip
    g = 'Spade'; x = -1.15
    with xf(T(x, 0, .036) @ RZ(.16) @ RX(-math.pi / 2) @ T(-x, 0, -.63)):
        blade('Spade_Blade', (x, 0, .0), .25, .34, P['iron'], g)
        rope('Spade_Spine', [(x, -.002, .1), (x, .004, .22), (x, .008, .35)], .012, P['iron'], ply=1, tw=0., seg=8, amp=0., group=g, grain='z', radius_fn=lambda t: .35 + .65 * t)
        for k, (dx, dz, r0) in enumerate(((-.05, .05, .03), (.03, .03, .026), (.065, .075, .022), (-.015, .1, .02))):
            sphere('Spade_Mud', (x + dx, -.006, dz), r0, P['mud'], scale=(1.25, .22, 1.), seg=10, ring=7, group=g, detail=1)
        lathe('Spade_Socket', [(.024, .33), (.021, .45), (.019, .47)], (x, .012, 0), P['iron'], seg=14, group=g)
        log('Spade_Shaft', [(x, .012, .44), (x, .014, .78), (x, .012, 1.06)], .0185, P['ash'], seg=10, lump=.015, seed=3, group=g, grain='z')
        for sd in (-1, 1):
            log('Spade_Fork', [(x + sd * .006, .012, 1.03), (x + sd * .04, .012, 1.12), (x + sd * .062, .012, 1.235)], .012, P['ash'], seg=8, lump=.01, seed=sd + 4, group=g, grain='z')
        log('Spade_Grip', [(x - .082, .012, 1.255), (x, .012, 1.262), (x + .082, .012, 1.255)], .018, P['ash'], seg=10, lump=.01, seed=5, group=g, grain='x')
        lash('Spade_Mend', (x, .012, .98), (0, 0, 1), .019, .1, .0048, P['hemp'], group=g, turns=8, detail=1)
        rope('Spade_Mend_Tail', [(x + .02, .0, .94), (x + .028, -.006, .9), (x + .024, -.006, .86)], .004, P['hemp'], group=g, detail=1, curve=4)
        socket('Socket_Hand_Spade', (x, .012, 1.05))
    # dirt basket: a dustpan of woven strips, flat floor open at the front, walls rising to a high back, a bent bamboo handle
    g = 'Basket'; x = -.45
    def ss(a, b, t):
        k = max(0., min(1., (t - a) / (b - a))); return k * k * (3 - 2 * k)
    def bfn(u, v):
        a = (u - .5) * 2; d = v
        side = ss(.68, 1., abs(a)) * (.02 + .25 * d)
        back = ss(.68, 1., d) * .27
        return (x + a * (.27 - .025 * d), -.21 + d * .4, .012 + max(side, back))
    def bpt(u, v, off):
        q = Vector(bfn(u, v)); return tuple(q + Vector((0, 0, off)))
    NW, NU = 15, 15
    for i in range(NW):
        u0 = (i + .1) / NW; u1 = (i + .9) / NW
        def warp(a, b, i=i, u0=u0, u1=u1):
            v = b; n = NU * v; off = .004 * math.sin(math.pi * (n + i))
            return bpt(u0 + (u1 - u0) * a, v, off)
        sheet('Warp', 1, 38, warp, P['strip'], solid=.002, group=g, grain='y', detail=0)
    for j in range(NU):
        v0 = (j + .08) / NU; v1 = (j + .92) / NU
        def weft(a, b, j=j, v0=v0, v1=v1):
            n = NW * a; off = -.004 * math.sin(math.pi * (n + j))
            return bpt(a, v0 + (v1 - v0) * b, off)
        sheet('Weft', 30, 1, weft, P['strip2'], solid=.002, group=g, grain='x', detail=0)
    surface('Basket_Backing', 22, 22, lambda u, v: bpt(u, v, -.007), P['strip2'], solid=.003, group=g, grain='y', detail=0)
    rim = [bfn(0, 0), bfn(0, .35), bfn(0, .7), bfn(0, 1), bfn(.25, 1), bfn(.5, 1), bfn(.75, 1), bfn(1, 1), bfn(1, .7), bfn(1, .35), bfn(1, 0)]
    log('Basket_Rim', [tuple(Vector(p_) + Vector((0, 0, .008))) for p_ in rim], .0125, P['split'], seg=9, lump=.02, seed=4, group=g, grain='y')
    log('Basket_Lip', [bfn(0, 0), bfn(.5, 0), bfn(1, 0)], .011, P['split'], seg=8, lump=.02, seed=7, group=g, grain='x')
    a0, a1 = bfn(0, .72), bfn(1, .72)
    log('Basket_Handle', [a0, (x - .24, .13, .36), (x - .12, .17, .44), (x, .18, .46), (x + .12, .17, .44), (x + .24, .13, .36), a1], .0125, P['split'], seg=9, lump=.02, seed=9, group=g, grain='x')
    lash('Basket_Grip', (x, .18, .46), (1, 0, 0), .0125, .1, .0048, P['hemp'], group=g, turns=9, detail=1)
    for sd, q in ((-1, a0), (1, a1)):
        lash('Basket_Tie', q, (.5 * sd, .3, .8), .016, .05, .004, P['hemp'], group=g, turns=4, detail=1)
    socket('Socket_Hand_Basket', (x, .18, .46))
    # tamper: 1.1 m, a heavy square block on a long handle, its grain split with age; tipped over, block and handle end on the ground
    g = 'Tamper'; x = .15
    with xf(T(x, 0, .116) @ RZ(-.1) @ RX(-math.pi / 2 - .075) @ T(-x, 0, -.55)):
        rbox('Tamper_Block', (x, 0, .11), (.24, .2, .22), P['block'], r=.012, amp=.004, freq=9., chips=6, hew=8, seed=12, div=.03, grain='z', group=g)
        for sd in (-.045, .05):
            rbox('Tamper_Split', (x + sd, -.1, .1), (.004, .006, .17), P['iron'], r=.001, seed=3, div=.04, rot=(0, .03 * sd * 20, 0), grain='z', detail=1, group=g)
        lathe('Tamper_Collar', [(.036, .215), (.032, .25), (.026, .27)], (x, 0, 0), P['iron'], seg=14, group=g)
        log('Tamper_Shaft', [(x, 0, .25), (x, .003, .65), (x, 0, 1.03)], .024, P['ash'], seg=11, lump=.02, seed=8, group=g, grain='z')
        sphere('Tamper_Head', (x, 0, 1.05), .032, P['ash'], scale=(1, 1, 1.5), seg=12, ring=8, group=g)
        lash('Tamper_Lash', (x, .001, .68), (0, 0, 1), .025, .09, .0048, P['hemp'], group=g, turns=7, detail=1)
        socket('Socket_Hand_Tamper', (x, 0, .85))
    # mortar bucket: staves bound with rope, a rope bail between two ears
    g = 'MortarBucket'; x = .72
    N = 15
    for i in range(N):
        a = i / N * math.tau; w = .1 * math.tau / N * 1.02
        q0 = Vector((x + math.cos(a) * .104, math.sin(a) * .104, 0)); q1 = Vector((x + math.cos(a) * .138, math.sin(a) * .138, .22 + .006 * (i % 3)))
        run = (q1 - q0).normalized(); side = Vector((-math.sin(a), math.cos(a), 0)); out = run.cross(side)
        w0, w1, t = .1 * math.tau / N * .5, .135 * math.tau / N * .5, .007
        vs = []
        for q, w_ in ((q0, w0), (q1, w1)):
            for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                vs.append(tuple(q + side * (sa * w_ * .97) + out * (sb * t)))
        mesh('Stave', vs, [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], P['stave'], group=g, grain=tuple(run))
    lathe('Bucket_Floor', [(0, .012), (.104, .012), (.104, .03), (0, .03)], (x, 0, 0), P['stave'], seg=24, group=g)
    for z, r in ((.045, .117), (.185, .14)):
        pts = [(x + math.cos(k / 28 * math.tau) * r, math.sin(k / 28 * math.tau) * r, z + .004 * math.sin(k * 1.7)) for k in range(29)]
        rope('Bucket_Hoop', pts, .0082, P['hemp'], group=g, curve=2)
    def mfn(u, v):
        a = u * math.tau; r = v * .127
        return (x + math.cos(a) * r, math.sin(a) * r, .16 + .012 * math.sin(a * 2 + 1) * v + .018 * noise.noise(Vector((math.cos(a) * r * 18, math.sin(a) * r * 18, 2))))
    surface('Mortar_Fill', 24, 8, mfn, P['mortar'], closed_u=True, group=g, grain='z')
    for sd in (-1, 1):
        rbox('Bucket_Ear', (x + sd * .149, 0, .235), (.016, .05, .1), P['stave'], r=.004, seed=sd + 2, div=.03, group=g, grain='z')
    rope('Bucket_Bail', [(x - .15, 0, .27), (x - .12, 0, .36), (x, .0, .405), (x + .12, 0, .36), (x + .15, 0, .27)], .0085, P['hemp'], group=g, curve=8)
    socket('Socket_Hand_MortarBucket', (x, 0, .405))
    # trowel: a pointed triangular blade on a cranked tang
    g = 'Trowel'; x = 1.12
    def tfn(u, v):
        w = .056 * (1 - v)
        return (x + (u - .5) * 2 * w, -.09 + v * .2, .008 + .002 * v)
    surface('Trowel_Blade', 8, 12, tfn, P['iron'], solid=.002, group=g, grain='y')
    log('Trowel_Neck', [(x, -.075, .012), (x, -.1, .016), (x, -.112, .05), (x, -.135, .055)], .0042, P['iron'], seg=6, lump=0, group=g, grain='y', curve=3)
    log('Trowel_Ferrule', [(x, -.132, .055), (x, -.155, .055)], .0115, P['iron'], seg=8, lump=0, group=g, grain='y')
    rope('Trowel_Handle', [(x, -.155, .055), (x, -.21, .057), (x, -.275, .055)], .0165, P['ash'], ply=1, tw=0., seg=9, amp=0., group=g, grain='y', radius_fn=lambda t: .82 + .3 * math.sin(t * 3.1))
    socket('Socket_Hand_Trowel', (x, -.21, .057))


# ------------------------------------------------------------------ CR06 earth channel
def path_straight(t): return Vector((0, -1 + 2 * t, 0)), Vector((1, 0, 0))
def path_short(t): return Vector((0, -.25 + .5 * t, 0)), Vector((1, 0, 0))


def path_bend(t):
    """A quarter circle of radius 1.25 m: enters going +Y, leaves going +X; about 2 m long. Same turn as B03, doubled."""
    a = t * math.pi / 2
    return Vector((1.25 - 1.25 * math.cos(a) - .625, -.625 + 1.25 * math.sin(a), 0)), Vector((math.cos(a), -math.sin(a), 0))


EARTH = [(-.44, 0.), (-.44, .2), (-.44, .385), (-.42, .405), (-.36, .415), (-.29, .405), (-.245, .37), (-.215, .31), (-.198, .28), (-.19, .2), (-.16, .115), (-.12, .1), (0, .1), (.12, .1), (.16, .115), (.19, .2), (.198, .28), (.215, .31), (.245, .37), (.29, .405), (.36, .415), (.42, .405), (.44, .385), (.44, .2), (.44, 0.)]


def channel_palette():
    P = {'earth': cm.mud('Packed_Earth', dark=(.05, .034, .02), light=(.15, .1, .06), rough=.85), 'stake': cm.wood('Weathered_Stake', (.09, .055, .028), (.27, .18, .1), ground_h=.1, grey=.35)}
    P['willow'] = cm.wood('Willow_Withy', (.09, .052, .022), (.24, .145, .06), ground_h=0, grey=.1); P['stone'] = cm.stone('Old_Channel_Stone', light=(.2, .19, .155), dark=(.1, .095, .08), ochre=(.17, .15, .1), moss=.75, wet_z=.3); P['hemp'] = mm.hemp('Withy_Tie', (.17, .105, .05), twist=40.0)
    P['grass'] = cm.moss_tuft('Bank_Grass'); P['moss'] = cm.moss_tuft('Bank_Moss', soft=True)
    return P


def end_cap(name, path, t, section, mat, depth=.012):
    """A section across the path, closed as a thin slab set just inside the module's end."""
    from ti_core import mesh
    p, n = path(t); q, _ = path(min(1., t + .01) if t < .5 else max(0., t - .01)); inward = (q - p).normalized() * depth
    verts = [tuple(p + n * x + Vector((0, 0, z))) for x, z in section] + [tuple(p + inward + n * x + Vector((0, 0, z))) for x, z in section]
    k = len(section)
    faces = [tuple(range(k)), tuple(range(2 * k - 1, k - 1, -1))] + [(i, k + i, k + (i + 1) % k, (i + 1) % k) for i in range(k)]
    return mesh(name, verts, faces, mat, grain='z')


def channel(P, path, seed, amount=1.):
    R = random.Random(seed); N = len(EARTH) - 1   # amount: how much of a 2 m piece's stakes and growth this piece carries
    def prof(u):
        f = u * N; i = min(int(f), N - 1); k = f - i
        return EARTH[i][0] * (1 - k) + EARTH[i + 1][0] * k, EARTH[i][1] * (1 - k) + EARTH[i + 1][1] * k
    def fn_(u, v):
        p, n = path(v); x, z = prof(u)
        c = min(1., min(v, 1 - v) * 14)
        top = .25 < abs(x) < .43
        lump = noise.fractal(Vector((p.x * 5.1, p.y * 5.1, seed + (1 if x > 0 else 0) * 3)), 1., 2., 4) * .022 * c if top else noise.noise(Vector((p.x * 7, p.y * 7, seed))) * .004 * c
        dent = 0.
        q = math.hypot((v - .36) / .05, (x + .36) / .05)
        if q < 1: dent = .018 * (1 - q * q)
        return tuple(p + n * x + Vector((0, 0, max(0., z + lump - dent) if z > 0 else 0.)))
    surface('Earth_Bed', len(EARTH) * 4, 72, fn_, P['earth'], grain='y')
    for t in (0., 1.):
        for sx in (-1, 1):
            pts = [q for q in EARTH if q[0] * sx >= .16 - 1e-6] + [(sx * .16, 0.)]
            end_cap('Bank_End', path, t, pts, P['earth'])
        end_cap('Floor_End', path, t, ((-.16, 0.), (.16, 0.), (.16, .115), (.12, .1), (-.12, .1), (-.16, .115)), P['earth'])
    for sx in (-1, 1):
        # outside the bank: stout stakes driven in, willow woven between them and bound at each stake
        stakes = max(2, round(6 * amount))
        at = [i / (stakes - 1) * .96 + .02 for i in range(stakes)]
        for i, t in enumerate(at):
            p, n = path(t); q = p + n * sx * .462
            top = .455 + R.uniform(-.035, .04)
            log('Stake', [(q.x, q.y, 0.), (q.x + R.uniform(-.004, .004), q.y + R.uniform(-.004, .004), .25), (q.x, q.y, top)], .03 + R.uniform(-.002, .004), P['stake'], seg=10, lump=.08, seed=i + sx, grain='z')
            for z in (.13, .34):
                lash('Stake_Tie', (q.x, q.y, z), (0, 0, 1), .032, .045, .0052, P['hemp'], turns=3, detail=1)
        for row in range(7):
            rowz = .05 + row * .05; pts = []
            for i in range(121):
                t = i / 120; p, n = path(t)
                s_ = math.sin(t * (stakes - 1) * 2 * math.pi + row * math.pi)
                pts.append(tuple(p + n * sx * (.46 + .012 * s_) + Vector((0, 0, rowz + .004 * math.sin(i * .7 + row)))))
            rope('Withy', pts, .0085 + .0015 * (row % 2), P['willow'], ply=1, tw=0, seg=4, amp=0, curve=1, step=.07, detail=1, grain='y')
        # crossing rods in each bay, so it reads woven rather than stacked
        for b in range(stakes - 1):
            for k, (z0, z1) in enumerate(((.07, .36), (.34, .08))):
                t0, t1 = at[b] + .02, at[b + 1] - .02
                pa, na = path(t0); pb, nb = path(t1); pm, nm = path((t0 + t1) / 2)
                rope('Withy', [tuple(pa + na * sx * .452 + Vector((0, 0, z0))), tuple(pm + nm * sx * .478 + Vector((0, 0, (z0 + z1) / 2))), tuple(pb + nb * sx * .452 + Vector((0, 0, z1)))], .0075, P['willow'], ply=1, tw=0, seg=6, amp=0, curve=4, step=.03, detail=1)
        # bank top: moss cushions and young grass, it has settled for a season
        for i in range(round(18 * amount)):
            t = R.uniform(.02, .98); p, n = path(t); d = R.uniform(.27, .43)
            q = p + n * sx * d
            tuft('Bank_Moss', (q.x, q.y, .405 if d > .29 else .39), R.uniform(.018, .04), P['moss'], seed=i + seed)
        for i in range(round(30 * amount)):
            t = R.uniform(.03, .97); p, n = path(t); d = R.uniform(.29, .42)
            q = p + n * sx * d; z = .405
            for b in range(5):
                a = R.uniform(0, 6.28); base = q + Vector((math.cos(a) * .03, math.sin(a) * .03, z - .01))
                sheet('Grass', 1, 4, lambda u, v, base=base, a=a: tuple(base + Vector((math.cos(a) * .012 * (u - .5) * (1 - v) + math.cos(a + 1) * v * v * .045, math.sin(a) * .012 * (u - .5) * (1 - v) + math.sin(a + 1) * v * v * .045, v * .095))), P['grass'], solid=None, grain='z', detail=2)
        for i, t in enumerate((.3, .72)[:max(0, round(2 * amount))]):
            p, n = path(t + .04 * sx); q = p + n * sx * .33
            rbox('Old_Stone', (q.x, q.y, .42), (.13, .1, .07), P['stone'], r=.012, amp=.008, freq=14., chips=4, hew=5, seed=i + 15 + sx, div=.03, rot=(0, 0, i * .7), detail=1)
    for i in range(round(26 * amount)):
        t = R.uniform(.03, .97); p, n = path(t)
        sphere('Pebble', tuple(p + n * R.uniform(-.13, .13) + Vector((0, 0, .102))), R.uniform(.007, .016), P['stone'], scale=(1.2, 1, .55), seg=8, ring=5, detail=2)
    S['water_path'] = path          # the water is its own model: build_creek_repair_b.export_water
    a, an = path(0), path(1)
    socket('Socket_PortIn', tuple(a[0] + Vector((0, 0, FLOOR)))); socket('Socket_PortOut', tuple(an[0] + Vector((0, 0, FLOOR))))
    S['collision'] = []


CROSS = .75


def cross_height(x, y, seed):
    """Earth at (x, y): each arm has the channel's section at its port, and the banks round off where two arms meet. Below 0 means outside the bank."""
    d = min(abs(x), abs(y)); E = [q for q in EARTH if q[0] >= 0 and q[1] > 0]
    if d >= E[-1][0]: return max(0., E[-1][1] - (d - E[-1][0]) * 7) if d < .5 else -1.
    for (a, za), (b, zb) in zip(E, E[1:]):
        if a <= d <= b:
            z = za + (zb - za) * (d - a) / max(b - a, 1e-6)
            break
    edge = min(1., (CROSS - max(abs(x), abs(y))) * 14)
    return z + (noise.fractal(Vector((x * 5.1, y * 5.1, seed)), 1., 2., 4) * .022 * edge if .25 < d < .43 else noise.noise(Vector((x * 7, y * 7, seed))) * .004 * edge)


def cr15_cross(P):
    """Where the main channel meets the canal: in from the south, out west, east and north. Every port is the CR06 section, 0.75 m from the middle."""
    seed, N = 151, 72; R = random.Random(seed); verts, faces, index = [], [], {}
    step = 2 * CROSS / N
    def at(i, j):
        if (i, j) not in index:
            x, y = -CROSS + i * step, -CROSS + j * step
            index[i, j] = len(verts); verts.append((x, y, max(0., cross_height(x, y, seed))))
        return index[i, j]
    for j in range(N):
        for i in range(N):
            corners = [(-CROSS + (i + a) * step, -CROSS + (j + b) * step) for a, b in ((0, 0), (1, 0), (1, 1), (0, 1))]
            if all(cross_height(x, y, seed) < 0 for x, y in corners): continue
            faces.append((at(i, j), at(i + 1, j), at(i + 1, j + 1), at(i, j + 1)))
    mesh('Earth_Bed', verts, faces, P['earth'], grain='y', smooth=True)
    for sx in (-1, 1):
        for sy in (-1, 1):
            # the same staked, woven outer face as CR06, round each inner corner
            line = [(sx * .462, sy * CROSS), (sx * .462, sy * .462), (sx * CROSS, sy * .462)]
            def on(t):
                u = t * 2; a, b = (line[0], line[1]) if u < 1 else (line[1], line[2]); k = u if u < 1 else u - 1
                return Vector((a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, 0))
            for i, t in enumerate((.04, .5, .96)):
                q = on(t); top = .455 + R.uniform(-.035, .04)
                log('Stake', [(q.x, q.y, 0.), (q.x + R.uniform(-.004, .004), q.y + R.uniform(-.004, .004), .25), (q.x, q.y, top)], .03 + R.uniform(-.002, .004), P['stake'], seg=10, lump=.08, seed=i + sx * 3 + sy, grain='z')
                for z in (.13, .34): lash('Stake_Tie', (q.x, q.y, z), (0, 0, 1), .032, .045, .0052, P['hemp'], turns=3, detail=1)
            for row in range(7):
                rowz = .05 + row * .05
                rope('Withy', [tuple(on(i / 40) + Vector((0, 0, rowz + .004 * math.sin(i * .7 + row)))) for i in range(41)], .0085 + .0015 * (row % 2), P['willow'], ply=1, tw=0, seg=4, amp=0, curve=1, step=.07, detail=1, grain='y')
            # the bank top between the two arms
            for i in range(6):
                x, y = sx * R.uniform(.27, .44), sy * R.uniform(.27, .7)
                if i % 2: x, y = sx * abs(y), sy * abs(x)
                tuft('Bank_Moss', (x, y, .4), R.uniform(.018, .04), P['moss'], seed=i + seed + sx + sy * 7)
            for i in range(9):
                x, y = sx * R.uniform(.3, .43), sy * R.uniform(.3, .68)
                if i % 2: x, y = sx * abs(y), sy * abs(x)
                for b in range(5):
                    a = R.uniform(0, 6.28); base = Vector((x + math.cos(a) * .03, y + math.sin(a) * .03, .395))
                    sheet('Grass', 1, 4, lambda u, v, base=base, a=a: tuple(base + Vector((math.cos(a) * .012 * (u - .5) * (1 - v) + math.cos(a + 1) * v * v * .045, math.sin(a) * .012 * (u - .5) * (1 - v) + math.sin(a + 1) * v * v * .045, v * .095))), P['grass'], solid=None, grain='z', detail=2)
    for i in range(22):
        along = R.uniform(-.7, .7); across = R.uniform(-.13, .13); x, y = (across, along) if i % 2 else (along, across)
        sphere('Pebble', (x, y, .102), R.uniform(.007, .016), P['stone'], scale=(1.2, 1, .55), seg=8, ring=5, detail=2)
    S['water_cross'] = CROSS
    for name, q in (('Socket_PortIn', (0, -CROSS)), ('Socket_PortWest', (-CROSS, 0)), ('Socket_PortEast', (CROSS, 0)), ('Socket_PortNorth', (0, CROSS))): socket(name, (q[0], q[1], FLOOR))
    S['collision'] = []


def cr06_straight(P): channel(P, path_straight, 61)
def cr06_bend(P): channel(P, path_bend, 62)
def cr06_short(P): channel(P, path_short, 63, .25)


# ------------------------------------------------------------------ CR08 flume
def flume_palette():
    P = {'plank': cm.wood('Cedar_Trough', (.1, .056, .026), (.32, .19, .09), wet_z=.3, ground_h=0, grey=.12), 'patch': cm.wood('Cedar_Patch', (.14, .085, .042), (.38, .25, .125), wet_z=.3, ground_h=0, grey=.04)}
    P['bam_cap'] = cm.wood('Split_Bamboo', (.1, .1, .035), (.3, .24, .1), ground_h=0, grey=.05); P['frame'] = cm.wood('Frame_Oak', (.05, .03, .015), (.17, .1, .05), ground_h=0, grey=.3); P['drip'] = tm.plain('Drip_Water', (.1, .24, .22), rough=.08, noise=.02); P['hemp'] = mm.hemp('Hemp_Rope', (.2, .125, .055), twist=40.0)
    return P


def sweep(name, path, x0, x1, z0, z1, mat, t0=0., t1=1., n=24, seed=0, bevel=.003, **kw):
    """A long hewn board following the path, its section x0..x1, z0..z1 across and up; wanders a little along its length."""
    from ti_core import mesh
    a0, a1 = path(t0)[1], path(t1)[1]
    if 'grain' not in kw and a0.angle(a1) > .3:
        parts = max(2, int(a0.angle(a1) / .22) + 1); os_ = []
        for k in range(parts):
            ta, tb = t0 + (t1 - t0) * k / parts, t0 + (t1 - t0) * (k + 1) / parts
            run = path(tb)[0] - path(ta)[0]
            os_.append(sweep(name, path, x0, x1, z0, z1, mat, t0=ta, t1=tb, n=max(2, n // parts), seed=seed + k, bevel=bevel, grain=tuple(run.normalized()), **kw))
        return os_[0]
    verts, faces = [], []
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / n; p, nn = path(t)
        wob = noise.noise(Vector((t * 9, seed * 1.7, 0))) * .003
        for x, z in ((x0, z0), (x1, z0), (x1, z1), (x0, z1)):
            verts.append(tuple(p + nn * (x + wob) + Vector((0, 0, z + wob * .6))))
    for i in range(n):
        a = i * 4
        for k in range(4):
            faces.append((a + k, a + (k + 1) % 4, a + 4 + (k + 1) % 4, a + 4 + k))
    faces.append((3, 2, 1, 0)); faces.append((n * 4, n * 4 + 1, n * 4 + 2, n * 4 + 3))
    kw.setdefault('grain', 'y')
    o = mesh(name, verts, faces, mat, **kw)
    if bevel:
        m = o.modifiers.new('Soft', 'BEVEL'); m.width = bevel; m.segments = 2; m.limit_method = 'ANGLE'
    return o


def flume(P, path, seed):
    R = random.Random(seed)
    xs = [-.24, -.12, .005, .125, .24]
    for k in range(4):
        sweep('Floor_Board', path, xs[k] + .002, xs[k + 1] - .002, .05, .1, P['plank'], seed=k + seed)
    sweep('Under_Board', path, -.2, .2, .014, .05, P['plank'], seed=seed + 9, bevel=.002)
    for sx in (-1, 1):
        a, b = (.2, .24) if sx > 0 else (-.24, -.2)
        sweep('Wall_Low', path, a, b, .05, .165, P['plank'], seed=sx + 20 + seed)
        sweep('Wall_Mid', path, a, b, .167, .285, P['plank'], seed=sx + 30 + seed)
        sweep('Wall_High', path, a, b, .287, .395, P['plank'], seed=sx + 35 + seed)
    # a newer board patched over the outside, tied across with rope
    pm, nm = path(.68); yaw = math.atan2(nm.y, nm.x); ax = Vector((-nm.y, nm.x, 0))
    q = pm + nm * .246
    rbox('Wall_Patch', (q.x, q.y, .24), (.018, .34, .17), P['patch'], r=.003, amp=.0015, seed=3, div=.06, rot=(0, 0, yaw), grain='y', chips=2)
    for d in (-1, 1):
        q0 = pm + nm * .257 + ax * (-.13 * d) + Vector((0, 0, .17)); q1 = pm + nm * .257 + ax * (.13 * d) + Vector((0, 0, .31))
        rope('Patch_Tie', [tuple(q0), tuple(q1)], .0048, P['hemp'], detail=1)
    # rims: a bamboo culm along each wall top, in short lengths round a bend
    parts = 1 if path is path_straight else 7
    for sx in (-1, 1):
        for k in range(parts):
            t0, t1 = k / parts, (k + 1) / parts
            pts = [tuple(path(t0 + (t1 - t0) * i / 6)[0] + path(t0 + (t1 - t0) * i / 6)[1] * sx * .222 + Vector((0, 0, .41))) for i in range(7)]
            run = Vector(pts[-1]) - Vector(pts[0])
            log('Rim_Bamboo', pts, .023, P['bam_cap'], seg=10, lump=.015, seed=sx + 40 + seed + k, grain=tuple(run.normalized()))
    # rope bands round the whole trough
    bands = 5
    for i in range(bands):
        t = (i + .5) / bands; p, n = path(t); ax = Vector((-n.y, n.x, 0))
        for w in (-.012, 0, .012):
            c = p + ax * w
            pts = [c + n * x_ + Vector((0, 0, z)) for x_, z in ((-.25, .008), (-.25, .39), (-.235, .445), (-.205, .44), (-.195, .405), (-.205, .395), (-.245, .395), (-.25, .39), (-.25, .008), (.25, .008), (.25, .39), (.235, .445), (.205, .44), (.195, .405), (.205, .395), (.245, .395), (.25, .39), (.25, .008), (-.25, .008))]
            rope('Band', [tuple(q_) for q_ in pts], .0052, P['hemp'], curve=1, detail=1)
    # two bearers that sit on the trestles
    for t in (.14, .86):
        p, n = path(t); yaw = math.atan2(n.y, n.x)
        rbox('Bearer', tuple(p + Vector((0, 0, .022))), (.68, .1, .044), P['frame'], r=.005, amp=.002, seed=int(t * 9), div=.08, rot=(0, 0, yaw), grain='x')
    # drips at a joint
    for k in range(4):
        p, n = path(.31 + k * .09)
        sphere('Drip', tuple(p + n * (-.12 + k * .08) + Vector((0, 0, .008))), .006, P['drip'], scale=(1, 1, 1.6), seg=8, ring=5, detail=2)
    S['water_path'] = path          # the water is its own model: build_creek_repair_b.export_water
    a, an = path(0), path(1)
    socket('Socket_PortIn', tuple(a[0] + Vector((0, 0, FLOOR)))); socket('Socket_PortOut', tuple(an[0] + Vector((0, 0, FLOOR))))
    S['collision'] = [((-.3, -1, 0), (.3, 1, WALL))] if path is path_straight else []
    if path is not path_straight:
        # the trough itself, along the bend: one cross-section every few degrees
        N = 8; verts = []; faces = []
        for i in range(N + 1):
            q, side = path(i / N)
            verts += [tuple(q + side * sx * .3 + Vector((0, 0, z))) for sx, z in ((-1, 0), (1, 0), (1, WALL), (-1, WALL))]
        for i in range(N):
            k = i * 4
            faces += [(k + a, k + (a + 1) % 4, k + 4 + (a + 1) % 4, k + 4 + a) for a in range(4)]
        S['collision_mesh'] = (verts, faces + [(0, 1, 2, 3), (N * 4 + 3, N * 4 + 2, N * 4 + 1, N * 4)])


def cr08_straight(P): flume(P, path_straight, 81)
def cr08_bend(P): flume(P, path_bend, 82)




def weed_palette():
    return {'blade': cm.moss_tuft('Weed_Blade', soft=True), 'root': cm.moss_tuft('Weed_Root', soft=True)}


def cr14_weed(P):
    """Waterweed the current laid over: strap leaves from one matted root, all leaning towards +Y, the way it has to be pulled."""
    R = random.Random(1401)
    tuft('Root', (0, 0, .012), .05, P['root'], seed=3)
    for b in range(16):
        a = R.uniform(0, math.tau); r = R.uniform(.005, .055)
        base = Vector((math.cos(a) * r, math.sin(a) * r * .8, .012))
        L, w, lean, side = R.uniform(.2, .36), R.uniform(.006, .011), R.uniform(.7, 1.), R.uniform(-.3, .3)
        def blade_at(u, v, base=base, L=L, w=w, lean=lean, side=side):
            up = math.sin(min(v * 2.4, 1.) * math.pi / 2) * L * .24 * (1 - .75 * v * v)     # up out of the mud, then over
            out = L * lean * v * v
            width = w * (1 - v ** 2.2) * (u - .5) * 2
            return tuple(base + Vector((side * out + width, out, up + abs(u - .5) * .004)))
        sheet('Blade', 2, 6, blade_at, P['blade'], solid=None, grain='z')
    collide(((-.08, -.08, 0), (.08, .08, .05)))


def trestle_palette():
    return {'frame': cm.wood('Trestle_Cedar', (.06, .035, .018), (.2, .125, .065), ground_h=.35, moss=True, grey=.3), 'hemp': mm.hemp('Hemp_Rope', (.2, .125, .055), twist=40.0), 'moss': cm.moss_tuft('Foot_Moss', soft=True)}


def trestle(P, h):
    """A heavy A-frame: square legs, one thick tie, a thick bearer on top whose upper face takes the trough (z = h). Rope X-lashed at every joint."""
    spread = .3 + h * .2; top = .17
    cap_z = h - .055
    zt = h * .3 if h > 1 else h * .36
    xt = spread + (top - spread) * zt / (h - .1)
    for sx in (-1, 1):
        A = Vector((sx * spread, 0, 0)); B = Vector((sx * top, 0, h - .1))
        between('Leg', tuple(A), tuple(B), .11, .1, P['frame'], r=.01, amp=.004, freq=6., chips=3, seed=int(h * 10 + sx), div=.08)
        ax = (B - A).normalized()
        xlash('Top_Lash', (sx * (top + .012), 0, h - .165), tuple(ax), .058, (1, 0, 0), .05, .0085, P['hemp'], detail=1)
        xlash('Tie_Lash', (sx * xt, 0, zt), tuple(ax), .06, (1, 0, 0), .05, .0085, P['hemp'], detail=1)
        for b in range(9):
            a = b * 2.4; zz = .02 + b * .022
            q = A + ax * (zz / max(ax.z, .1)) + Vector((math.cos(a) * .05, math.sin(a) * .046, 0))
            tuft('Foot_Moss', tuple(q), .015 + .002 * (b % 3), P['moss'], seed=b + sx)
    rbox('Cap', (0, 0, cap_z), (.8, .15, .11), P['frame'], r=.01, amp=.004, freq=6., chips=4, seed=2, div=.08)
    between('Tie', (-xt - .1, 0, zt), (xt + .1, 0, zt), .09, .085, P['frame'], r=.008, amp=.003, chips=2, seed=9, div=.1)
    socket('Socket_TroughSeat', (0, 0, h))
    S['collision'] = [((-spread - .08, -.09, 0), (spread + .08, .09, h))]


def cr08_t080(P): trestle(P, .8)
def cr08_t150(P): trestle(P, 1.5)
def cr08_t250(P): trestle(P, 2.5)
