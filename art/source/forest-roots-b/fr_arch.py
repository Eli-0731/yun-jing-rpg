"""FR02 root arch (work pack B-104h part 2): 5 x 3 x 3.5 m, two giant roots crossing overhead into an arch a person walks under.

Three-view FR02 candidate-02 (README pick: the only candidate whose clear height scales to about 2.4 m; 01 and 03 are about 1.9 m
and have hanging roots in the way). Root A rises from the ground front-left and comes down back-right, root B from back-left to
front-right; over the path they cross and twist round each other, smaller roots wound round both. Each foot spreads into plank
roots gripping big stones, on a low mound of earth. A trodden earth path runs through along Y; root tendrils hang from the crown
but stop above 2.3 m over the path.
Origin: centre of the footprint at ground level; the path runs from -Y (front) to +Y. Clear height under the crown >= 2.2 m.
"""
import math, random
from mathutils import Vector, noise
from ti_core import S, socket
import fr_parts as FP

CROWN_Z = 2.9
PATH_W = 1.3
RADII = [.62, .52, .44, .37, .33, .32, .33, .37, .44, .52, .62]


def main_path(sx, sy):
    """Root from the foot at (-1.86 sx, -0.82 sy) over the crown to (1.86 sx, 0.82 sy)."""
    pts = [(-1.86, -.82, -.35), (-1.8, -.74, .6), (-1.62, -.56, 1.55), (-1.15, -.3, 2.4), (-.45, -.1, 2.82), (0., 0., CROWN_Z),
           (.45, .1, 2.82), (1.15, .3, 2.4), (1.62, .56, 1.55), (1.8, .74, .6), (1.86, .82, -.35)]
    out = []
    for i, (x, y, z) in enumerate(pts):
        f = math.sin(i / (len(pts) - 1) * math.pi)
        out.append((sx * x, sy * y + .13 * f * sy * sx, z + (.06 if sy > 0 else -.04) * f))   # the two roots pass either side of each other at the crown
    return out


def flare(P, R, foot, out_dir):
    """Plank roots spreading from a foot over the ground and into it, kept out of the path strip."""
    fx, fy = foot
    for k in range(5):
        a = math.atan2(out_dir[1], out_dir[0]) + (-1.5 + 3. * k / 4) + R.uniform(-.12, .12)
        d = Vector((math.cos(a), math.sin(a), 0)); L = R.uniform(.6, .9)
        pts = [tuple(Vector((fx, fy, .8)) - d * .15), tuple(Vector((fx, fy, .4)) + d * L * .35), tuple(Vector((fx, fy, .16)) + d * L * .7),
               tuple(Vector((fx, fy, -.12)) + d * L)]
        pts = [(max(-2.2, min(2.2, x)), max(-1.22, min(1.22, y)), z) for x, y, z in pts]
        if any(abs(x) < PATH_W / 2 + .12 for x, y, z in pts): continue
        FP.sweep('Root_Flare', pts, [.34, .26, .17, .11], R.choice(P['bark']), aspect=.62, step=.05, fiss=.2, seed=R.randrange(999))


def wound(P, R, sx, sy, ph0):
    """A thinner root wound round a main root for most of its length."""
    C, Rr, Sv = FP.resample(main_path(sx, sy), RADII, .12)
    pts, rr = [], []
    for i in range(6, len(C) - 6, 2):
        t = (C[min(len(C) - 1, i + 1)] - C[max(0, i - 1)]).normalized()
        n = (Vector((0, 0, 1)) - t * t.z).normalized() if abs(t.z) < .95 else Vector((1, 0, 0))
        b = t.cross(n); ph = ph0 + Sv[i] * 2.1; rm = Rr[i] + .07
        d = n * math.cos(ph) + b * math.sin(ph)
        # over the path the wrap stays on the upper half of the main root so it never hangs into head room
        w = 1 - min(1, max(0, (abs(C[i].x) - .55) / .5)); w = w * w * (3 - 2 * w)
        d.z = d.z * (1 - w) + abs(d.z) * .45 * w
        pts.append(tuple(C[i] + d.normalized() * rm)); rr.append(.07 + .07 * math.sin(i / len(C) * math.pi) ** 2 * (1 + .25 * math.sin(i * 1.7)))
    FP.sweep('Root_Wound', pts, rr, R.choice(P['bark']), aspect=1., step=.05, fiss=.2, plates=3., nring=14, lump=.14, seed=R.randrange(999))


def tendrils(P, R):
    """Root tendrils hanging from the crown: short over the path (tips at 2.35 m or higher), longer towards the legs."""
    for k in range(16):
        x = R.uniform(-1.35, 1.35); y = R.uniform(-.25, .25)
        hit = FP.snap((x, y, 1.0), (0, 0, 1))
        if not hit or hit[1].z > -.3: continue
        top = hit[0]; over_path = abs(x) < PATH_W / 2 + .3
        low = max(2.35, top.z - R.uniform(.25, .5)) if over_path else max(1.1, top.z - R.uniform(.5, 1.3))
        if top.z - low < .15: continue
        sway = Vector((R.uniform(-.06, .06), R.uniform(-.06, .06), 0))
        pts = [tuple(top + Vector((0, 0, .06))), tuple(top + sway * .5 - Vector((0, 0, (top.z - low) * .45))), tuple(Vector((top.x, top.y, low)) + sway)]
        FP.sweep('Root_Tendril', pts, [.03, .018, .006], R.choice(P['bark']), step=.04, fiss=.06, plates=2., nring=6, ground=None,
                 seed=R.randrange(999), tip=(P['tip'], .12), detail=1)


def mound_at(P, cx, cy, h, rx, ry, seed):
    """Low earth mound round a foot: the grid is mapped square-to-disc, so its edge is an ellipse feathered to the ground."""
    disc = lambda a, b: (cx + rx * a * math.sqrt(max(0., 1 - b * b / 2)), cy + ry * b * math.sqrt(max(0., 1 - a * a / 2)))
    def hf(a, b):
        x, y = disc(a, b); d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
        return h * max(0., 1 - d) ** 1.4 + .012 * noise.noise(Vector((x * 5., y * 5., seed))) * max(0., 1 - d)
    FP.mound('Foot_Earth', hf, -1., 1., -1., 1., P['earth'], nx=20, ny=20, mapfn=disc)


def path(P, R):
    """Trodden earth path through the arch: a thin worn strip whose outline wanders and frays (the slab follows it, no straight
    border), slightly crowned, feathered to the ground at its edge; a few flat stones pressed in."""
    w = lambda y: PATH_W / 2 - .08 + .09 * noise.noise(Vector((0., y * 1.3, 3.))) + .04 * noise.noise(Vector((0., y * 5., 9.)))
    cx = lambda y: .06 * noise.noise(Vector((0., y * .8, 5.)))
    mp = lambda a, y: (cx(y) + a * w(y), y)
    def hf(a, y):
        e = max(0., 1. - abs(a) ** 3)
        return .012 * e + .003 * noise.noise(Vector((a * 4., y * 6., 7.))) * e
    FP.mound('Trodden_Path', hf, -1., 1., -1.48, 1.48, P['path'], nx=12, ny=40, mapfn=mp)
    for i in range(3):                          # three wide, thin stepping slabs worn into the path, not coins
        y = -.95 + i * .95 + R.uniform(-.1, .1); x = cx(y) + R.uniform(-.22, .22); sz = R.uniform(.2, .25)
        FP.pebble('Path_Stone', (x, y, sz * .17 * .9 + .005), sz, R.choice(P['stone']), seed=R.randrange(999), flat=.17, detail=1)


def collision_tube(V, F, pts, radii, n=8):
    C, Rr, Sv = FP.resample(pts, radii, .3)
    secs = []
    for i, c in enumerate(C):
        if c.z < -.05: continue
        t = (C[min(len(C) - 1, i + 1)] - C[max(0, i - 1)]).normalized()
        a = t.orthogonal().normalized(); b = t.cross(a)
        secs.append([tuple(c + (a * math.cos(k * math.tau / n) + b * math.sin(k * math.tau / n)) * Rr[i] * .92) for k in range(n)])
    FP.hull_loft(V, F, secs)


def fr02_arch(P):
    R = random.Random('FR02_RootArch')
    P['path'] = __import__('fr_mats').forest_earth('Path_Earth', moss=.1, trodden=.75)
    path(P, R)
    roots = [(1, 1), (1, -1)]                 # A: front-left to back-right; B: back-left to front-right
    for k, (sx, sy) in enumerate(roots):
        FP.sweep('Root_Arch', main_path(sx, sy), RADII, P['bark'][k], aspect=1., step=.075, fiss=.22, twist=.3, seed=11 + k)
    for k, (sx, sy) in enumerate(roots):
        wound(P, R, sx, sy, k * 2.)
    feet = [(-1.86, -.82, (-1, -.6)), (1.86, .82, (1, .6)), (-1.86, .82, (-1, .6)), (1.86, -.82, (1, -.6))]
    for i, (fx, fy, od) in enumerate(feet):
        mound_at(P, fx * .97, fy * .93, .42, .62, .52, i)
        flare(P, R, (fx, fy), od)
        for j in range(2):                     # big stones gripped among the flare roots
            a = math.atan2(od[1], od[0]) + (-.9 if j else .9) + R.uniform(-.3, .3); d = R.uniform(.45, .6)
            x = max(-2.22, min(2.22, fx + math.cos(a) * d)); y = max(-1.22, min(1.22, fy + math.sin(a) * d))
            if abs(x) < PATH_W / 2 + .3: continue
            sz = R.uniform(.17, .24); FP.pebble('Foot_Stone', (x, y, sz * .7 * 1.2 + .006), sz, R.choice(P['stone']), seed=R.randrange(999), flat=.7)
    tendrils(P, R)
    Rg = random.Random('FR02_growth')
    placed = []
    for i in range(16):                        # moss on the crown and the upper legs, patches kept apart
        x = Rg.uniform(-1.5, 1.5); y = Rg.uniform(-.3, .3)
        hit = FP.snap((x, y, 5.), (0, 0, -1))
        if not hit or any((hit[0] - q).length < .36 for q in placed): continue
        if hit[1].z > .4 and hit[0].z < 3.3:
            placed.append(hit[0].copy()); FP.moss_patch('Arch_Moss', tuple(hit[0]), tuple(hit[1]), Rg.uniform(.1, .17), P['moss'], seed=i, snap_each=True)
    for i, (x, y) in enumerate(((-.45, .02), (.42, -.05))):   # small ferns rooted in the crown moss
        hit = FP.snap((x, y, 5.), (0, 0, -1))
        if hit: FP.fern('Crown_Fern', tuple(hit[0] - Vector((0, 0, .03))), P['fern'], Rg, n=6, L=.24, out=(0, 1 if i else -1, 0), up_bias=.45, spread=1.4)
    for i, (fx, fy, od) in enumerate(feet):
        x = max(-2.1, min(2.1, fx + od[0] * .3)); y = max(-1.1, min(1.1, fy + od[1] * .45))
        FP.fern('Foot_Fern', (x, y, .15), P['fern'], Rg, n=Rg.randint(6, 8), L=Rg.uniform(.3, .4), out=(od[0], od[1], 0), up_bias=.25, spread=1.)
        for k in range(3):
            a = math.atan2(od[1], od[0]) + Rg.uniform(-1.3, 1.3); d = Rg.uniform(.6, .75)
            x = fx + math.cos(a) * d; y = fy + math.sin(a) * d
            if abs(x) < PATH_W / 2 + .1: continue
            FP.grass_tuft('Foot_Grass', (max(-2.35, min(2.35, x)), max(-1.35, min(1.35, y)), .014), Rg.randint(3, 5), Rg.uniform(.1, .15), P['grass'], Rg, spread=.03)
    socket('Socket_Path_S', (0, -1.5, 0), rot=(0, 0, math.pi))
    socket('Socket_Path_N', (0, 1.5, 0))
    V, F = [], []
    for sx, sy in roots: collision_tube(V, F, main_path(sx, sy), RADII)
    S['collision_mesh'] = (V, F)
    S['prop'] = dict(kind='arch')


NOTE = ('根拱門（三視圖 FR02 candidate-02）：5 × 3 m、高 3.5 m。兩條巨根交叉成拱：A 根從左前拱起、越過頭頂落到右後，B 根從左後到右前，'
        '在路的正上方交錯、互相擦過，另有四條細根沿著兩條主根纏繞。根腳直徑約 1 m，各自散出板根、夾著大石頭，坐在一圈低土丘上，長蕨和草。'
        '中間一條踩實的土路（寬 1.3 m，沿 Y 從前到後）嵌幾塊扁石。拱頂長苔和小蕨；細根從拱頂垂下，路正上方的垂根末端都在 2.35 m 以上，'
        '往兩側較長。拱下淨高與寬度在 validation.json 量測（從路面往上打射線）。'
        '碰撞：兩條主根各一條簡化管（8 邊），土路與小石不擋。接口：Socket_Path_S（路的前端，朝外）、Socket_Path_N（後端）。')


def register(ASSETS):
    ASSETS['FR02_RootArch'] = dict(zh='根拱門', kind='arch', palette=FP.palette, build=fr02_arch, limit=(5., 3., 3.5), tex=2048, ver='v001',
        box=((-2.5, -1.5, 0.), (2.5, 1.5, 3.5)), ref='FR02/candidate-02', slot='D1_ForestEdge_to_D2_ElderTree', minTier='standard', clamp_max=.03,
        uv_shape='CONVEX', origin='centre of the footprint at ground level; the path runs through along Y, front at -Y', note=NOTE)
