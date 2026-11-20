"""PS02 broken stone arch bridge at the end of the A9 road (work pack 2026-11-09 B-112h, batch B, PS02).

An old humped stone arch bridge washed out by a flood: the two ends survive, each a coursed ashlar abutment with a stone stair
climbing between two balustrades (posts with ball finials, panels with cloud-shaped openings) up to a short landing, and under it
the start of the arch (a ring of voussoirs proud of the wall, a coursed barrel under it). The middle is gone: rough broken faces,
the courses stepping back unevenly, the ring snapped a little behind the deck edge; the river bed between is paved with old bed
stones and scattered with fallen blocks and a few voussoirs. Grey weathered masonry, moss low down and in the joints, ferns.
Different from WM07 (a whole 12 m bridge with a ramped deck and plain rails) and the Dondon StoneArchBridge: this one is broken,
14 m long, stepped, with pierced balustrades. No timber props (the sheet's props are left out, as the pick notes say), no writing.

Walking: each stair is 20 risers of 0.175 m on a humped nosing line (z = 3.5 (1 - t^1.3): treads about 0.22 m at the foot, 38 deg,
widening towards the top) to a landing at 3.5 m; the collision is a ramp on that line, the balustrades are walls, and at each broken
edge a 1.1 m invisible lip across the deck stops a walker at the gap (the work pack: "碰撞要讓人走到斷口就停下來").

Sizes (limit 14 x 4 x 5 m): x along the bridge (-7..7), the stair foot at |x| 6.95, the springings at |x| 3.6 (z 0.35), the arch
would have risen 2.5 m (radius 3.84 m); the deck between the walls 3.04 m wide, the walls' faces at y +-1.86; the left half breaks
at about x -0.95, the right one at about x 1.35 (a 2.3 m gap at deck level). Front -Y looks at the side of the bridge.
Origin: centre of the footprint at the river bed (ground) level, z = 0.
Reference: art/references/PS02/PS02-cand-1.png.
"""
import math, random
from mathutils import Vector, Euler, noise
import cr_mats as cm
import fr_parts as FP
from cr_parts import rbox
from ti_core import S, cyl, lathe, socket, extrude_profile, boolean

W, D, H = 14.0, 4.0, 5.0
XE, LAND_X, LAND_Z, HUMP = 6.95, 1.2, 3.5, 1.3     # stair foot |x|, landing |x|, landing z, the hump's curve exponent
NSTEP = 20
RISER = LAND_Z / NSTEP                       # 0.175
XS, ZS, RISE = 3.6, .35, 2.5                 # springing |x|, springing z, rise of the (lost) arch
RAD = (XS * XS + RISE * RISE) / (2 * RISE)   # 3.84
CZ = ZS + RISE - RAD
RING = .5
DECK_HW = 1.52
WALL_Y, WALL_T = 1.69, .34                   # wall centre line and thickness (outer face at 1.86)
COURSE = .34
BREAK = {-1: .95, 1: 1.35}                  # deck-level break |x| for the left (-1) and right (+1) halves


def nose(x):
    """The stair's nosing line at |x|: a humped curve, steepest at the foot (38 deg) and easing onto the landing; flat on the landing."""
    a = abs(x)
    if a >= XE: return 0.
    if a <= LAND_X: return LAND_Z
    t = (a - LAND_X) / (XE - LAND_X)
    return LAND_Z * (1 - t ** HUMP)


def riser_x(k):
    """|x| of the k-th riser (k = 0 at the foot): where the nosing line reaches k risers."""
    t = (1 - min(1., k * RISER / LAND_Z)) ** (1 / HUMP)
    return LAND_X + t * (XE - LAND_X)


def intrados(x):
    a = abs(x)
    return CZ + math.sqrt(max(0., RAD * RAD - a * a)) if a < XS else 0.


def extrados(x):
    a = abs(x); r = RAD + RING
    return CZ + math.sqrt(max(0., r * r - a * a)) if a < r else 0.


def stone_set(name, n=4, light=(.22, .208, .18), dark=(.095, .088, .075), **kw):
    shade = [(1., 1., 1.), (.86, .86, .87), (1.08, 1.04, .96), (.94, .96, .98)]
    return [cm.stone(f'{name}_{i}', light=tuple(c * f for c, f in zip(light, shade[i])), dark=tuple(c * f for c, f in zip(dark, shade[i])), **kw) for i in range(n)]


def palette():
    P = {}
    P['wall'] = stone_set('Bridge_Ashlar', 4, ochre=(.25, .225, .175), moss=1.0, lichen=.45, crack=.5, wet_z=.8, moss_low_z=1.2, slot='Stone')
    P['ring'] = cm.stone('Bridge_Voussoir', light=(.2, .19, .162), dark=(.088, .08, .068), ochre=(.24, .21, .16), moss=.9, lichen=.4, crack=.45, slot='Stone')
    P['step'] = [cm.stone(f'Bridge_Step_{i}', light=l, dark=d, ochre=(.25, .22, .17), moss=.7, lichen=.35, crack=.55, slot='Rail', polish=(.36, .34, .3))
                 for i, (l, d) in enumerate((((.2, .19, .165), (.09, .084, .072)), ((.185, .178, .158), (.08, .076, .066))))]
    P['rail'] = cm.stone('Bridge_Rail', light=(.205, .195, .17), dark=(.09, .085, .072), ochre=(.24, .21, .155), moss=1.1, lichen=.6, crack=.4, slot='Rail')
    P['fallen'] = stone_set('Fallen_Block', 3, ochre=(.25, .225, .175), moss=1.2, lichen=.4, crack=.5, wet_z=.4)
    P['bed'] = cm.stone('River_Bed_Stone', light=(.2, .19, .165), dark=(.08, .075, .065), moss=.9, wet_z=.25)
    P['moss'] = cm.moss_tuft('Bridge_Moss', soft=True)
    P['fern'] = cm.fern('Bridge_Fern')
    P['grass'] = cm.weed_leaf('Bridge_Grass', (.03, .06, .02), (.1, .17, .045), (.2, .24, .07))
    P['dry'] = cm.weed_leaf('Bridge_Dry_Grass', (.1, .075, .03), (.25, .19, .08), (.4, .31, .14))
    return P


# ------------------------------------------------------------------ one surviving half (s = -1 left, +1 right)
def x_where(f, target, lo, hi):
    """|x| in [lo, hi] where the falling curve f reaches target (f(lo) >= target >= f(hi))."""
    for _ in range(40):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if f(m) > target else (lo, m)
    return (lo + hi) / 2


def break_x(s, z, R):
    """|x| of the broken face at height z: the deck edge at BREAK[s], the courses below stepping back further, unevenly."""
    return BREAK[s] + .18 * max(0., LAND_Z - z) / 1.2 + R.uniform(-.06, .2)


def walls(P, s, R):
    for sy in (-1, 1):
        y = sy * WALL_Y; row = 0; z = 0.
        while z < LAND_Z + .05:
            xb = break_x(s, z + COURSE / 2, R)
            a = XE + .04 - (row % 2) * .38
            ends = [XE + .04]
            while a > xb + .05:
                ends.append(a); a -= R.uniform(.6, 1.0)
            ends.append(xb)
            ends = sorted(set(round(e, 3) for e in ends))
            for x0, x1 in zip(ends, ends[1:]):
                bottom, top = z, z + COURSE
                if nose(x1) < bottom + .08: x1 = x_where(nose, bottom + .08, LAND_X, XE)          # the stair line cuts the course's outer end
                if intrados(x0) > top - .08 and intrados(XS - 1e-6) < top - .08:
                    x0 = max(x0, x_where(intrados, top - .08, 0., XS - 1e-6))                   # the arch cuts its inner end
                if x1 - x0 < .12: continue
                c = (x0 + x1) / 2
                xs = [x0 + (x1 - x0) * k / 6 for k in range(7)]
                hi = max(nose(v) for v in xs); lo = min(intrados(v) for v in xs)
                if not (bottom < hi - .02 and top > lo + .02): continue
                broken = x0 <= xb + .001
                def warp(q, c=c, zc=(bottom + top) / 2, broken=broken):
                    wx = c + s * q.x; wz = zc + q.z
                    wz = min(wz, nose(wx) - .01)
                    wz = max(wz, intrados(wx))
                    q.z = wz - zc
                    if broken and s * q.x < -(x1 - x0) / 2 + .1:    # the broken end: torn back unevenly
                        q.x += s * .09 * (noise.noise(Vector((q.y * 7, q.z * 7, c))) + .3)
                rbox('Wall_Block', (s * c, y, (bottom + top) / 2), (x1 - x0 - .006, WALL_T, COURSE - .005), R.choice(P['wall']),
                     r=.025, amp=.008 if not broken else .02, freq=5., chips=1 if not broken else 3, hew=3, seed=row * 31 + int(c * 17) + (s > 0) * 500,
                     div=.17, warp=warp, group='Stone')
            z += COURSE; row += 1


def ring(P, s, R):
    """Voussoirs proud of both wall faces, and the barrel under the arch as coursed blocks, both snapped near the break."""
    a_s = math.asin(XS / RAD); N = 27; da = 2 * a_s / N
    xb = BREAK[s] + .12
    for i in range(N):
        a = -a_s + (i + .5) * da
        if s * math.sin(a) <= 0: continue
        depth = RING + (.06 if i % 2 else 0)
        if abs(RAD * math.sin(a)) < xb: continue
        for sy in (-1, 1):
            rm = RAD + depth / 2
            rbox('Voussoir', (math.sin(a) * rm, sy * (WALL_Y + .025), CZ + math.cos(a) * rm), (2 * RAD * math.sin(da / 2) + .004, WALL_T + .01, depth),
                 P['ring'], r=.014, amp=.004, chips=1, hew=3, seed=i * 2 + (sy > 0) + (s > 0) * 100, div=.12, rot=(0, a, 0), group='Stone')
        # the barrel: four staggered blocks across the soffit, 0.26 m thick, with open joints so the courses read in the shade under the arch
        cuts = [-DECK_HW, -.8 + (i % 2) * .4, (i % 2) * .4, .8 + (i % 2) * .4, DECK_HW] if i % 2 else [-DECK_HW, -.8, 0., .8, DECK_HW]
        rm = RAD + .13
        for y0, y1 in zip(cuts, cuts[1:]):
            rbox('Barrel_Block', (math.sin(a) * rm, (y0 + y1) / 2, CZ + math.cos(a) * rm), (2 * RAD * math.sin(da / 2) - .014, y1 - y0 - .022, .26),
                 R.choice(P['wall']), r=.022, amp=.005, chips=1, hew=2, seed=i * 7 + int(y0 * 10) + (s > 0) * 200, div=.2, rot=(0, a, 0), group='Stone')
    # the snapped end of the ring: one voussoir each side left hanging, cracked and tipped
    a = math.asin(min(.99, (xb + .15) / RAD)) * s
    for sy in (-1, 1):
        rm = RAD + RING / 2
        rbox('Voussoir_Broken', (math.sin(a) * rm - s * .05, sy * (WALL_Y + .025), CZ + math.cos(a) * rm - .06), (.3, WALL_T, RING * .8),
             P['ring'], r=.02, amp=.025, freq=6., chips=4, hew=2, seed=300 + (sy > 0) + (s > 0) * 7, div=.07, rot=(0, a + s * .12, 0), group='Stone')


def core(P, s, R):
    """The rubble fill under the stair: one rough mass between the walls, its broken end showing at the gap."""
    x0, x1 = BREAK[s] + .2, XE - .05
    c = (x0 + x1) / 2
    zc = 2.
    def warp2(q, c=c):
        wx = c + q.x * s
        bot = intrados(wx) + .2 if abs(wx) < XS else .06; top = max(nose(wx) - .26, bot + .02)
        q.z = bot + (q.z + 2.) / 4. * (top - bot) - zc     # scaled into [bot, top], not clamped: clamping pressed the sides flat into the top (thousands of coplanar faces)
    rbox('Fill_Core', (s * c, 0., zc), (x1 - x0, 2 * DECK_HW - .02, 4.), P['wall'][1], r=.05, amp=.015, freq=2.5, chips=0, div=.25, warp=warp2, group='Stone')


def stair(P, s, R):
    xb = BREAK[s]
    for k in range(NSTEP + 1):
        if k < NSTEP:
            xo, xi = riser_x(k), riser_x(k + 1)
        else:
            xo, xi = LAND_X, xb
        if xo <= xb + .05: break
        last = xi < xb + .02
        xi = max(xi, xb)
        top = (k + 1) * RISER if k < NSTEP else LAND_Z
        cuts = [-DECK_HW, R.uniform(-.7, -.2), R.uniform(.3, .8), DECK_HW] if k % 2 else [-DECK_HW, R.uniform(-.2, .3), DECK_HW]
        for j, (y0, y1) in enumerate(zip(cuts, cuts[1:])):
            th = min(.3, top - .002) if k < NSTEP else .26
            xij = xi + (R.uniform(.0, .32) if last else 0.)       # at the break each stone of the step snapped off at its own length
            if xo - xij < .1: continue
            def warp(q, L=xo - xij):
                if last and q.x * s < -L / 2 + .08: q.z += .03 * noise.noise(Vector((q.y * 9, 0, 1)))
            rbox('Step', (s * (xo + xij) / 2, (y0 + y1) / 2, top - th / 2), (xo - xij + (.02 if k < NSTEP else 0), y1 - y0 - .006, th), P['step'][(k + j) % 2],
                 r=.018, amp=.004, freq=4., chips=2 if not last else 5, hew=3, seed=k * 5 + j + (s > 0) * 300, div=.12, flat='z', warp=warp, group='Rail', grain='y')
        if R.random() < .5:
            FP.moss_patch('Step_Moss', (s * (xi + .03), R.choice((-1, 1)) * R.uniform(1.25, 1.55), top + .002), (0, 0, 1), R.uniform(.06, .11), P['moss'], seed=k + (s > 0) * 50, flat=.45, detail=1)


def balustrade(P, s, R):
    xb = BREAK[s]
    posts = [6.75, 5.55, 4.35, 3.15, 1.95]
    for sy in (-1, 1):
        y = sy * WALL_Y
        # coping along the wall top
        x = XE + .03; k = 0
        while x > xb + .1:
            L = min(R.uniform(.7, 1.0), x - xb)
            c = x - L / 2
            def warp(q, c=c):
                q.z += nose(c + s * q.x) - nose(c)
            rbox('Coping', (s * c, y, nose(c) + .06), (L - .006, WALL_T + .04, .12), P['rail'], r=.02, amp=.004, chips=1, hew=2,
                 seed=k * 3 + (sy > 0) + (s > 0) * 40, div=.12, warp=warp, group='Rail')
            x -= L; k += 1
        base = lambda x: nose(x) + .12
        for i, px in enumerate(posts):
            if px < xb + .15: continue
            z0 = base(px)
            rbox('Rail_Post', (s * px, y, z0 + .34), (.2, .2, .68), P['rail'], r=.018, amp=.003, chips=1, hew=2, seed=i + (sy > 0) * 9 + (s > 0) * 70, div=.1, group='Rail', grain='z')
            rbox('Post_Cap', (s * px, y, z0 + .705), (.24, .24, .05), P['rail'], r=.012, amp=.002, seed=i + 3, div=.08, group='Rail')
            lathe('Post_Ball', [(0, 0), (.06, 0), (.065, .02), (.04, .04), (.075, .085), (.08, .11), (.07, .15), (.035, .185), (0, .195)], (s * px, y, z0 + .73), P['rail'], seg=16, group='Rail')
        for i in range(len(posts) - 1):
            xa, xc = posts[i] - .1, posts[i + 1] + .1
            broken = xc < xb + .15
            if broken: xc = xb + R.uniform(.05, .2)
            if xa - xc < .25: continue
            c = (xa + xc) / 2; zc = (base(xa) + base(xc)) / 2
            def warp(q, c=c, zc=zc):
                q.z += base(c + q.x * s) - zc
            pan = rbox('Rail_Panel', (s * (c + (0. if not broken else .01)), y, zc + .2475), (xa - xc + (.04 if not broken else .02), .1, .515), P['rail'], r=.008, amp=.002 if not broken else .012, chips=0 if not broken else 3,
                       seed=i + 20 + (s > 0) * 70, div=.08, warp=warp, group='Rail')
            rbox('Rail_Top', (s * c, y, zc + .54), (xa - xc + .02, .13, .08), P['rail'], r=.016, amp=.002, seed=i + 30, div=.12, warp=warp, group='Rail')
            # the cloud-shaped opening: a lobed slot through the panel, one per bay, following the slope
            if not broken:
                ang = math.atan2(base(xa) - base(xc), xa - xc) * s
                L = (xa - xc) * .62
                out = []
                for q in range(40):
                    t = math.tau * q / 40
                    rx, rz = L / 2, .085
                    k = 1 + .14 * math.cos(3 * t) ** 2
                    out.append((rx * math.cos(t) * (1 - .12 * math.cos(2 * t)), rz * math.sin(t) * k))
                cut = extrude_profile('Cut_Cloud', out, .3, P['rail'], plane='xz', p=(s * c, y, zc + .26), rot=(0, -ang, 0), bevel=0, group='Rail')
                boolean(pan, cut)


def loose(P, s, R):
    """Broken lumps still lodged in the torn face: a few rough stones sticking out of the fill and the wall ends at the gap."""
    xb = BREAK[s]
    for k in range(9):
        y = R.uniform(-DECK_HW + .15, DECK_HW - .15) if k < 6 else R.choice((-1, 1)) * WALL_Y
        z = R.uniform(intrados(xb + .3) + .25, nose(xb) - .25)
        sz = (R.uniform(.22, .4), R.uniform(.2, .35), R.uniform(.16, .28))
        rbox('Break_Lump', (s * (xb + .16 + R.uniform(-.04, .1)), y, z), sz, R.choice(P['wall']), r=.02, amp=.03, freq=6., chips=5, hew=2, seed=700 + k + (s > 0) * 20,
             div=.07, rot=(R.uniform(-.4, .4), R.uniform(-.4, .4), R.uniform(-.5, .5)), group='Stone')


def half(P, s):
    R = random.Random(f'PS02{s}')
    walls(P, s, R); ring(P, s, R); core(P, s, R); stair(P, s, R); balustrade(P, s, R); loose(P, s, R)
    # ferns in the wall joints and moss along the foot, only where there is wall
    placed = tries = 0
    while placed < 14 and tries < 400:
        tries += 1
        x = R.uniform(BREAK[s] + .5, XE); z = R.uniform(.25, nose(x) - .3); sy = R.choice((-1, 1))
        if z <= intrados(x) + .15: continue
        FP.fern('Wall_Fern', (s * x, sy * (WALL_Y + WALL_T / 2 + .005), z), P['fern'], R, n=6, L=.13, out=(0, sy * .5, 1.), detail=1, up_bias=.7, spread=.8)
        placed += 1
    for k in range(22):
        x = R.uniform(BREAK[s] + .3, XE); sy = R.choice((-1, 1))
        z = R.uniform(.05, .5) if k < 10 else R.uniform(.5, max(.6, nose(x) - .2))
        if k >= 10 and z < intrados(x) + .1: continue
        FP.moss_patch('Wall_Moss', (s * x, sy * (WALL_Y + WALL_T / 2 + .005), z), (0, sy, .1), R.uniform(.1, .2) if k < 10 else R.uniform(.06, .12), P['moss'], seed=k + (s > 0) * 30)
    for k in range(8):          # foot grass stays inside the 4 m depth (a 0.35 m blade leaning out from 1.92 m crossed it)
        x = R.uniform(XS, 6.8); sy = R.choice((-1, 1))
        FP.grass_tuft('Foot_Grass', (s * x, sy * (WALL_Y + WALL_T / 2 + .035), 0.), R.randint(8, 14), R.uniform(.14, .3), P['grass'] if R.random() < .7 else P['dry'], R, lean=.18, detail=1, spread=.04)


def river_bed(P):
    R = random.Random('PS02bed')
    # old bed stones, flat, half sunk, between the abutments
    for k in range(70):
        x = R.uniform(-XS + .1, XS - .1); y = R.uniform(-1.85, 1.85)
        sz = R.uniform(.12, .26)   # centre a little under its half height, so the bottom sits about 2 cm into the bed (inside the box)
        FP.pebble('Bed_Stone', (x, y, sz * .22 * .78), sz, P['bed'], seed=k, flat=.22, detail=1, group='Main')
    # fallen blocks: ashlar and a few voussoirs from the lost crown, tumbled and half buried
    blocks = []
    for k in range(17):
        for _ in range(30):
            x = R.uniform(-2.9, 2.9); y = R.uniform(-1.7, 1.7)
            if all(math.hypot(x - bx, y - by) > .75 for bx, by, _ in blocks): break
        sz = (R.uniform(.45, .85), R.uniform(.3, .4), R.uniform(.28, .36)) if k % 4 else (R.uniform(.35, .45), WALL_T, RING)
        rot = (R.uniform(-.5, .5), R.uniform(-.6, .6), R.uniform(0, math.pi))
        m = Euler(rot).to_matrix()
        lowest = sum(abs(m[2][i]) * sz[i] / 2 for i in range(3))       # rest it on the bed (bottom corner at z 0, sunk 1 cm)
        rbox('Fallen_Block', (x, y, lowest - .01), sz, R.choice(P['fallen']), r=.03, amp=.012, freq=4., chips=4, hew=2, seed=500 + k, div=.12, rot=rot, group='Main')
        blocks.append((x, y, max(sz[:2])))
        if R.random() < .5:
            FP.moss_patch('Block_Moss', (x, y, 2 * lowest - .02), (0, 0, 1), R.uniform(.07, .12), P['moss'], seed=600 + k, flat=.5, snap_each=True, detail=1)
    for k in range(14):
        FP.grass_tuft('Bed_Grass', (R.uniform(-3.3, 3.3), R.uniform(-1.72, 1.72), 0.), R.randint(7, 12), R.uniform(.12, .3), P['grass'] if R.random() < .6 else P['dry'], R, lean=.3, detail=1, spread=.04)
    S['fallen_blocks'] = blocks


def build_ps02(P):
    for s in (-1, 1): half(P, s)
    river_bed(P)
    for s, nm in ((-1, 'L'), (1, 'R')):
        socket(f'Socket_RoadEnd_{nm}', (s * 7., 0., 0.), rot=(0, 0, -s * math.pi / 2))
    S['collision_mesh'] = collision()
    S['part_notes'] = {'stair': {'riser_m': RISER, 'treads_m': [round(riser_x(k) - riser_x(k + 1), 3) for k in range(NSTEP)], 'steps': NSTEP, 'landing_z_m': LAND_Z,
                                 'landing_inner_x_m': LAND_X, 'foot_x_m': XE, 'hump': 'nosing line z = 3.5 (1 - t^1.3), steepest 38 deg at the foot'},
                       'arch': {'springing_x_m': XS, 'springing_z_m': ZS, 'rise_m': RISE, 'radius_m': round(RAD, 3), 'ring_m': RING},
                       'break_deck_x_m': {'left': -BREAK[-1], 'right': BREAK[1]}, 'deck_width_m': 2 * DECK_HW, 'walls_outer_y_m': WALL_Y + WALL_T / 2,
                       'collision': 'ramp on the stair nosing line, balustrade walls 0.85 m over it, a 1.1 m invisible lip across the deck at each broken edge, the four biggest fallen blocks',
                       'sockets': 'Socket_RoadEnd_L / R at the foot of each stair, +Y (Unity forward) pointing away from the bridge'}


def collision():
    V, F = [], []
    def poly_extrude(pts, y0, y1):
        n = len(pts); i0 = len(V)
        V.extend((x, y0, z) for x, z in pts); V.extend((x, y1, z) for x, z in pts)
        F.append(tuple(i0 + k for k in range(n))[::-1]); F.append(tuple(i0 + n + k for k in range(n)))
        for k in range(n):
            j = (k + 1) % n; F.append((i0 + k, i0 + j, i0 + n + j, i0 + n + k))
    def prism(x0, x1, y0, y1, z0, z1):
        FP.hull_loft(V, F, [[(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)] for z in (z0, z1)])
    for s in (-1, 1):
        xb = BREAK[s]
        xs_arch = [XS - (XS - xb) * k / 8 for k in range(9)]
        curve = [(XE - (XE - LAND_X) * k / 12, nose(XE - (XE - LAND_X) * k / 12)) for k in range(13)]
        curve = [(x, z) for x, z in curve if x > xb + .02] + [(xb, nose(xb))]
        prof = [(XE + .04, 0.)] + curve + [(x, intrados(x)) for x in xs_arch[::-1]] + [(XS, 0.)]
        pts = [(s * x, z) for x, z in prof]
        if s < 0: pts = pts[::-1]
        poly_extrude(pts, -WALL_Y - WALL_T / 2, WALL_Y + WALL_T / 2)
        for sy in (-1, 1):      # the balustrades: walls 0.85 m over the nosing line
            top = [(x, nose(x) + .97) for x in [XE + .04 - (XE + .04 - xb) * k / 10 for k in range(11)]]
            bot = [(x, max(0., nose(x) - .3)) for x in [xb + (XE + .04 - xb) * k / 10 for k in range(11)]]
            pts = [(s * x, z) for x, z in top + bot]
            if s < 0: pts = pts[::-1]
            yi, yo = sorted((sy * DECK_HW, sy * (WALL_Y + WALL_T / 2)))
            poly_extrude(pts, yi, yo)
        # the lip at the broken edge
        a, b = sorted((s * xb, s * (xb + .1)))
        prism(a, b, -DECK_HW, DECK_HW, nose(xb) - .05, nose(xb) + 1.1)
    for x, y, r in sorted(S.get('fallen_blocks', []), key=lambda t: -t[2])[:4]:
        prism(x - r * .4, x + r * .4, y - r * .4, y + r * .4, 0., .3)
    return V, F


def register(ASSETS):
    ASSETS['PS02_BrokenBridge'] = dict(
        kind='bridge', zh='斷橋', palette=palette, build=build_ps02, tex=2048, tex_atlas={'Stone': 4096}, ver='v001',
        atlases={'Main': ['Main', 'Detail_Small'], 'Stone': ['Stone'], 'Rail': ['Rail']},
        limit=[W, D, H], box=((-W / 2, -D / 2, 0.), (W / 2, D / 2, H)), slot='A9_RoadEnd_BrokenBridge', ref='PS02/PS02-cand-1',
        clamp_max=.03, uv_shape='CONVEX', uv_detach_zero=True, minTier='standard',
        origin='footprint centre at river-bed level, z = 0; the bridge runs along X, front (-Y) looks at its side',
        note='路盡頭被山洪沖斷的石拱橋（三視圖 PS02-cand-1）：兩端橋頭還在，各是一段條石砌的橋台，中間一道弓背石階（20 級，每級高 0.175 m，下段陡、上段緩）夾在兩道石欄杆之間，爬到 3.5 m 的小平台；'
             '石欄杆是方柱加圓珠頂、欄板開雲形透孔、上面壓扶手。橋下是拱的起頭：拱圈石凸出牆面一圈，拱底也是一塊塊條石。中段沖掉了：斷面粗糙，各層石頭參差往後退，拱圈斷在平台邊緣後面一點，'
             '左右斷口不一樣（左邊 x -0.95、右邊 x 1.35，平台處缺口約 2.3 m）。河床鋪舊卵石，散著十幾塊落石和幾塊拱圈石。灰色舊石、牆腳和縫裡長苔，牆面長蕨。'
             '圖上的木支撐不做；不寫字。碰撞：石階是一條斜坡、兩邊欄杆是牆、斷口處平台上有 1.1 m 的透明擋（人走到斷口就停），加四塊最大的落石。',
        method='procedural mesh construction (art/source/roadside-landmarks-b/ps_bridge.py: ashlar courses clipped to the stair and the arch, '
               'voussoirs and barrel blocks, cloud openings cut by booleans); procedural stone, moss and plant shaders baked to three 2048 atlases (Main, Stone, Rail)',
        based_on='original (Blender procedural); masonry approach after WM07 (art/source/creek-repair-b/cr_wm.py), not its shape')


def bridge_checks(aid, check, cfg):
    from vl_checks import _bvh
    lod0 = S['lods'][0]
    body = _bvh([o for g, o in lod0.items() if not g.startswith('Detail_')])
    down = lambda x, y, f=body: (lambda h: round(h[0].z, 3) if h else None)(f((x, y, 20.), (0, 0, -1)))
    # the stair: tread tops at the expected heights on both halves (mid-tread, mid-width away from the step joints)
    tr = {}
    for s in (-1, 1):
        got = [down(s * (riser_x(k) + riser_x(k + 1)) / 2, .9) for k in (2, 8, 14, 18)]
        tr[s] = got
    ok = all(g is not None and abs(g - (k + 1) * RISER) < .03 for s in (-1, 1) for g, k in zip(tr[s], (2, 8, 14, 18)))
    check('stair_treads', ok, {'tread_tops_m': {('left' if s < 0 else 'right'): tr[s] for s in tr}, 'expected_m': [round((k + 1) * RISER, 3) for k in (2, 8, 14, 18)]})
    # the gap: nothing over the middle, and the two broken deck edges stand apart
    mid = down(0., 0.)
    l = body((0., .3, LAND_Z - .3), (-1, 0, 0)); r = body((0., .3, LAND_Z - .3), (1, 0, 0))
    gap = (r[0].x - l[0].x) if l and r else None
    check('gap_open', (mid is None or mid < .6) and gap is not None and gap > 1.9,
          {'top_at_centre_m': mid, 'deck_edges_x_m': [round(l[0].x, 3) if l else None, round(r[0].x, 3) if r else None], 'gap_m': round(gap, 2) if gap else None})
    # the springings are there: the soffit over the bed near each springing
    so = [down(s * 3.0, 0.) for s in (-1, 1)]
    under = [body((s * 3.0, .2, .8), (0, 0, 1)) for s in (-1, 1)]      # y 0.2: clear of the barrel joints (cuts at 0 and +-0.4)
    check('arch_springs_both_sides', all(u is not None and abs(u[0].z - intrados(3.0)) < .08 for u in under),
          {'soffit_z_at_x_+-3_m': [round(u[0].z, 3) if u else None for u in under], 'expected_m': round(intrados(3.0), 3)})
    col = _bvh([S['collision_obj']]) if S.get('collision_obj') else None
    out = {'gap_m': round(gap, 2) if gap else None}
    if col:
        stops = [col((s * 5., 0., LAND_Z + .6), (-s, 0, 0)) for s in (-1, 1)]
        ramp = [col((s * 4.0, 0., 10.), (0, 0, -1)) for s in (-1, 1)]
        check('collision_stops_at_gap', all(h is not None and abs(abs(h[0].x) - (BREAK[s] + .1)) < .03 for h, s in zip(stops, (-1, 1))) and
              all(h is not None and abs(h[0].z - nose(4.0)) < .03 for h in ramp),
              {'lip_x_m': [round(h[0].x, 3) if h else None for h in stops], 'ramp_z_at_x_+-4_m': [round(h[0].z, 3) if h else None for h in ramp], 'nosing_m': round(nose(4.), 3)})
    return out
