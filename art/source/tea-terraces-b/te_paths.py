"""TE03 ways through the tea terraces: a stone stair up a TE01 wall, a trodden earth path and a run of stepping stones. All 1.2 m wide.

Shared with TE01: the stone, soil, grass and moss materials (te_terrace.palette) and the 1 m grid.
  TE03_Stair     six risers of 1/6 m and 0.40 m goings, from the lower tread (z = 0) to the upper soil (z = 1.0).
                 Origin: centre of the stair's back edge on the TE01 footprint front line (y = 0), z = 0 at the lower tread.
                 Stand it against any straight TE01 wall: the stair runs out to y = -2.4 over the lower tread.
  TE03_Path      4.0 m of packed earth, low edging stones; both ends share one cross-section, so lengths chain on the grid.
  TE03_Stepping  2.0 m: four flat stones bedded in the soil, a 0.6 m stride.
"""
import math, random
from mathutils import Vector, noise
from ti_core import S, mesh, surface, socket
import cr_mats as cm
from cr_parts import rbox
import te_terrace as TT

W = 1.2
N_STEP, RISE_STEP, GOING = 6, 1. / 6, .40
Y0 = -N_STEP * GOING           # -2.4: front of the bottom step


def palette():
    P = TT.palette()
    P['path'] = cm.packed_earth('Path_Earth', dark=(.05, .035, .02), light=(.118, .08, .045), rough=.9, crumb=.5, wet_top=.006, wet_low=-.002, dry_low=5., dry_top=6., period_x=4., strata_amt=0.)   # close to the tread soil so a run's end line does not show; pattern repeats every 4 m so pieces join without a tone step; low margin darker
    return P


def extrude_x(profile, hw):
    """Closed prism: a (y, z) polygon swept from x = -hw to +hw."""
    n = len(profile); verts = [(-hw, y, z) for y, z in profile] + [(hw, y, z) for y, z in profile]
    faces = [(k, (k + 1) % n, n + (k + 1) % n, n + k) for k in range(n)] + [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    return verts, faces


def boxes(list_):
    """Several closed boxes (x0, y0, z0, x1, y1, z1) in one mesh."""
    verts, faces = [], []
    for x0, y0, z0, x1, y1, z1 in list_:
        k = len(verts)
        verts += [(x, y, z) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
        faces += [(k, k + 2, k + 3, k + 1), (k + 4, k + 5, k + 7, k + 6), (k, k + 1, k + 5, k + 4), (k + 2, k + 6, k + 7, k + 3), (k, k + 4, k + 6, k + 2), (k + 1, k + 3, k + 7, k + 5)]
    return verts, faces


# ------------------------------------------------------------------ stair
def step_front(i): return Y0 + i * GOING


def te03_stair(P):
    R = random.Random(301); top = N_STEP * RISE_STEP
    back = TT.FACE0 + TT.BATTER * .85 - .02        # just clear of the TE01 wall face, which leans back as it rises
    # earth core behind everything, kept inside the side stones
    prof = [(Y0 + .12, 0.)]
    for i in range(1, N_STEP):
        prof += [(step_front(i) + .06, (i - 1) * RISE_STEP + .02), (step_front(i) + .06, i * RISE_STEP - .005)]
    prof += [(.04, (N_STEP - 1) * RISE_STEP - .005), (.04, 0.)]
    v, f = extrude_x(prof, W / 2 - .12)
    mesh('Stair_Core', v, f, P['joint'], grain='y', detail=0)
    # treads: each step one or two long slabs resting on the back of the step below, nosing slightly proud and irregular
    for i in range(N_STEP):
        z1 = (i + 1) * RISE_STEP; z0 = i * RISE_STEP if i else -.04
        y0 = step_front(i) - R.uniform(.0, .025); y1 = (back if i == N_STEP - 1 else step_front(i + 1) + .14)
        cuts = [-W / 2, R.uniform(-.25, .2), W / 2] if R.random() < .6 else [-W / 2, R.uniform(-.38, -.22), R.uniform(.12, .3), W / 2]
        for k in range(len(cuts) - 1):
            x0, x1 = cuts[k] + (.008 if k else 0), cuts[k + 1] - (.008 if k < len(cuts) - 2 else 0)
            mat = R.choice(P['wall'] + P['cope'][:1])
            yf = y0 - R.uniform(-.02, .03)
            rbox('Step_Slab', ((x0 + x1) / 2, (yf + y1) / 2, (z0 + z1) / 2), (x1 - x0, y1 - yf, z1 - z0), mat,
                 r=.045, amp=.013, freq=4., chips=3, hew=1, seed=R.randint(1, 999), div=.065, rot=(R.uniform(-.012, .012), R.uniform(-.01, .01), R.uniform(-.03, .03)),
                 taper=(R.uniform(.975, 1.), R.uniform(.96, 1.)), flat='z', grain='x', detail=0)
            # dark moss in the joint behind the nosing of the step above, where rain sits
        if i:
            for k in range(R.randint(1, 3)):
                TT.moss_patch('Moss', (R.uniform(-.5, .5), step_front(i) + .02, i * RISE_STEP + .003), (0, -.4, 1), R.uniform(.03, .055), P['moss'], seed=R.randint(1, 999), flat=.5)
    # side faces: coursed rubble under the treads, set back 2 cm from the slab edges
    for side in (-1, 1):
        z = 0.
        while z < top - RISE_STEP - .02:
            h = min(R.uniform(.14, .24), top - RISE_STEP - z)
            if h < .06: break
            zb = z + h; k = max(1, math.ceil(zb / RISE_STEP - 1e-6)); y = step_front(k) + .015
            while y < .03:
                w = min(R.uniform(.24, .48), .03 - y)
                if w < .08: break
                rbox('Stair_Side_Stone', (side * (W / 2 - .13), y + w / 2, z + h / 2), (.22, w - .012, h - .012), R.choice(P['wall']),
                     r=min(.04, h * .3), amp=.008, freq=4., chips=1, seed=R.randint(1, 999), div=.075, rot=(R.uniform(-.03, .03), 0, 0), grain='y', detail=0)
                y += w
            z = zb
    # grass and moss where feet do not go: the side foot, the corners of the treads, the joints of the side stones
    for k in range(14):
        side = R.choice((-1, 1)); y = R.uniform(Y0 + .05, .0)
        TT.grass_tuft('Grass_Foot', (side * (W / 2 + .015), y, .0), R.randint(6, 10), R.uniform(.1, .2), R.choice((P['grass'], P['dry_grass'])), R, lean=.2, spread=.025)
    for i in range(1, N_STEP):
        for side in (-1, 1):
            if R.random() < .55:
                TT.moss_patch('Moss', (side * (W / 2 - .09), step_front(i) + .08, i * RISE_STEP + .004), (0, 0, 1), R.uniform(.06, .1), P['moss'], seed=R.randint(1, 999), flat=.6)
            if R.random() < .35:
                TT.grass_tuft('Grass_Step', (side * (W / 2 - .05), step_front(i) + GOING * .8, i * RISE_STEP), R.randint(3, 6), R.uniform(.06, .12), P['grass'], R, spread=.02)
    for k in range(8):
        side = R.choice((-1, 1)); y = R.uniform(Y0 + .3, -.05); z = R.uniform(.05, max(.08, (math.floor((y - Y0) / GOING)) * RISE_STEP - .03))
        TT.moss_patch('Moss', (side * (W / 2 - .015), y, z), (side, 0, 0), R.uniform(.035, .06), P['moss'], seed=R.randint(1, 999), flat=.4)
    prof = [(Y0, 0.)]
    for i in range(N_STEP):
        prof += [(step_front(i), (i + 1) * RISE_STEP), (step_front(i + 1) if i < N_STEP - 1 else back, (i + 1) * RISE_STEP)]
    prof += [(back, 0.)]
    S['collision_mesh'] = extrude_x(prof, W / 2)
    socket('Socket_Bottom', (0., Y0, 0.)); socket('Socket_Top', (0., 0., top))
    S['te03'] = dict(kind='stair', back=back)


# ------------------------------------------------------------------ path
L_PATH = 4.0


def path_z(x, y, seed):
    """Packed earth a little proud of the tread, dished down the middle where feet go, feathered to the soil at the sides; flat at both ends."""
    a = abs(y) / (W / 2)
    crown = .012 - .007 * max(0., 1 - (abs(y) / .34) ** 2)
    edge = 1 - TT.smooth((a - .6) / .4)
    end = TT.smooth(min(x + L_PATH / 2, L_PATH / 2 - x) / .45)
    n = .006 * noise.noise(Vector((x * 1.4 + seed, y * 2.2, seed))) + .003 * noise.noise(Vector((x * 6 + seed, y * 6, 1)))
    return max(0., crown * edge + n * end * edge)


def te03_path(P):
    R = random.Random(302); seed = 3.1
    # ragged sides: the half-width wanders with a wave periodic over the piece length, so both end lines stay identical and pieces join
    def half(x, side):
        t = x / L_PATH * math.tau; ph = 0. if side > 0 else 2.3
        w = .5 * math.sin(t + ph + 1) + .3 * math.sin(2 * t + ph * 1.7 + 2) + .2 * math.sin(3 * t + ph * .6 + .5)
        return W / 2 * (1 - .085 * (w + 1))
    def earth(u, v):
        x = (u - .5) * L_PATH; y = (v - .5) * 2; y = y * (half(x, 1) if y > 0 else half(x, -1))
        return (x, y, path_z(x, y, seed))
    surface('Path_Earth', 48, 14, earth, P['path'], grain='x', detail=0)
    # edging: half-buried stones along both sides, in runs with gaps, never on the end lines
    for side in (-1, 1):
        x = -L_PATH / 2 + R.uniform(.1, .3)
        while x < L_PATH / 2 - .2:
            if R.random() < .4: x += R.uniform(.25, .6); continue
            w = R.uniform(.12, .24); w = min(w, L_PATH / 2 - .06 - x)
            if w < .08: break
            d = R.uniform(.1, .17); h = R.uniform(.08, .11); y = side * (W / 2 - d / 2 - R.uniform(.02, .06))
            rbox('Edge_Stone', (x + w / 2, y, h / 2 - R.uniform(.06, .085)), (w, d, h), R.choice((P['wall'][1], P['wall'][3], P['wall'][0])), r=min(.04, h * .42), amp=.011, freq=4., seed=R.randint(1, 999),
                 div=.06, rot=(R.uniform(-.1, .1), R.uniform(-.1, .1), R.uniform(-.12, .12)), grain='x', detail=0)
            x += w + R.uniform(.02, .09)
    # a few flat flags set into the worn middle
    for k in range(5):
        x = -L_PATH / 2 + .45 + k * (L_PATH - .9) / 4 + R.uniform(-.25, .25); s = R.uniform(.2, .32)
        rbox('Path_Flag', (x, R.uniform(-.16, .16), .008), (s, s * R.uniform(.6, .9), .05), R.choice(P['wall']), r=.025, amp=.008, seed=R.randint(1, 999), div=.06, rot=(0, 0, R.uniform(0, 3)), flat='z', grain='x', detail=1)
    for k in range(40):
        x = R.uniform(-L_PATH / 2 + .2, L_PATH / 2 - .2); y = R.uniform(-.4, .4); sz = R.uniform(.02, .045)
        rbox('Pebble', (x, y, path_z(x, y, seed) + sz * .1), (sz, sz * R.uniform(.6, .9), sz * .5), R.choice(P['wall']), r=sz * .3, amp=sz * .08, seed=R.randint(1, 999), div=sz * .4, rot=(0, 0, R.uniform(0, 3)), detail=2)
    # grass along the outer edges, thinning into the trodden strip
    for k in range(70):
        x = R.uniform(-L_PATH / 2 + .1, L_PATH / 2 - .1); side = R.choice((-1, 1)); y = side * R.uniform(.42, .53)
        TT.grass_tuft('Grass_Verge', (x, y, path_z(x, y, seed)), R.randint(5, 10), R.uniform(.08, .2), R.choice((P['grass'], P['grass'], P['dry_grass'])), R, lean=.22, spread=.03)
    for k in range(10):
        x = R.uniform(-L_PATH / 2 + .2, L_PATH / 2 - .2); y = R.uniform(-.12, .12)
        TT.grass_tuft('Grass_Middle', (x, y, path_z(x, y, seed)), R.randint(2, 4), R.uniform(.04, .08), P['dry_grass'], R, spread=.02)
    S['collision_mesh'] = boxes([(-L_PATH / 2, -W / 2 + .05, 0., L_PATH / 2, W / 2 - .05, .012)])
    socket('Socket_Left', (-L_PATH / 2, 0., 0.)); socket('Socket_Right', (L_PATH / 2, 0., 0.))
    S['te03'] = dict(kind='path', seed=seed)


# ------------------------------------------------------------------ stepping stones
L_STEP = 2.0
STONES = ((-.74, .12, .48, .42, .07), (-.15, -.14, .46, .4, .06), (.43, .1, .5, .44, .065), (.88, -.22, .24, .24, .045))   # x, y, length, width, top


def te03_stepping(P):
    R = random.Random(303); col = []
    for k, (x, y, l, w, t) in enumerate(STONES):
        h = t + .07
        rbox('Step_Stone', (x, y, t - h / 2), (l, w, h), R.choice(P['wall']), r=.075, amp=.016, freq=3.5, chips=2, seed=R.randint(1, 999), div=.06,
             rot=(R.uniform(-.02, .02), R.uniform(-.02, .02), R.uniform(-.4, .4)), flat='z', grain='x', detail=0)
        # a collar of disturbed soil round the stone
        def collar(u, v, x=x, y=y, l=l, w=w, s=k * 1.7):
            a = u * math.tau; rag = 1 + .35 * noise.noise(Vector((math.cos(a) * 1.8 + s, math.sin(a) * 1.8, s))); e = .055 * v * rag
            px = x + math.cos(a) * (l / 2 * .97 + e); py = y + math.sin(a) * (w / 2 * .97 + e)
            return (px, py, max(0., .011 * (1 - v) ** 1.5 + .003 * noise.noise(Vector((math.cos(a) * 3 + s, math.sin(a) * 3, s))) * (1 - v)))
        surface('Stone_Collar', 20, 3, collar, P['soil'], closed_u=True, grain='z', detail=1)
        for j in range(R.randint(2, 4)):
            a = R.uniform(0, math.tau)
            TT.grass_tuft('Grass_Stone', (x + math.cos(a) * (l / 2 + .05), y + math.sin(a) * (w / 2 + .05), .01), R.randint(4, 8), R.uniform(.06, .15), R.choice((P['grass'], P['dry_grass'])), R, lean=.35, spread=.03)
        if R.random() < .7:
            TT.moss_patch('Moss', (x + R.uniform(-l / 4, l / 4), y + R.uniform(-w / 4, w / 4), t + .002), (0, 0, 1), R.uniform(.04, .07), P['moss'], seed=R.randint(1, 999), flat=.4)
        col.append((x - l / 2 * .85, y - w / 2 * .85, 0., x + l / 2 * .85, y + w / 2 * .85, t))
    for k in range(14):
        x = R.uniform(-L_STEP / 2 + .1, L_STEP / 2 - .1); y = R.choice((-1, 1)) * R.uniform(.35, .55)
        TT.grass_tuft('Grass_Verge', (x, y, 0.), R.randint(4, 8), R.uniform(.07, .16), R.choice((P['grass'], P['dry_grass'])), R, spread=.04)
    S['collision_mesh'] = boxes(col)
    socket('Socket_Left', (-L_STEP / 2, 0., 0.)); socket('Socket_Right', (L_STEP / 2, 0., 0.))
    S['te03'] = dict(kind='stepping')
