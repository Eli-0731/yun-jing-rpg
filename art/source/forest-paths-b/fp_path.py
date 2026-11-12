"""FP forest-path pieces (work pack B 11/08). FP01: the straight section, 6 x 2.0 x 0.3 m (the work pack's 1.6 m
widened to 2.0 m on 2026-11-09 at the user's request; see fp_parts.widen).

Three-view FP01 candidate-01: a narrow trodden dirt footpath through the old forest. Packed dark-brown soil sunk between two soft
banks, a worn centre line, two thin roots crossing the tread diagonally with their tops showing, small stones pushed out onto the
banks, moss creeping in from the edges, fallen maple and lance leaves drifted along the banks, ferns arching over both edges.
Unlike MountainStonePath / MountainStoneStairs (cut stone), qingxi-winding-road and the road-props village roads (wide, gravelled,
cart ruts), TE03 (tea-field walk between stone edging) and TY10 (gravel): no stone paving, no gravel, no edging, earth only.
Origin: centre of the footprint at ground level; walk along X, west end (s = 0) at -X.
"""
import math, random
from mathutils import Vector, noise
from ti_core import S, socket
import fr_parts as FP
import fr_mats as fm
import cr_mats as cm
import fp_mats as pm
import fp_parts as PP


def palette():
    P = FP.palette()
    P['root'] = [fm.bark(f'Path_Root_{i}', tone=t, moss=mo) for i, (t, mo) in enumerate(((.85, .3), (.78, .4)))]
    P['fern'] = pm.fern_leaf('Fern_Pinnae'); P['fern_old'] = pm.fern_leaf('Fern_Pinnae_Old', old=True); P['fern_stem'] = pm.fern_stem('Fern_Stem')
    P['leaf'] = {k: pm.fallen_leaf(f'Fallen_Leaf_{k.title()}', k) for k in ('orange', 'brown', 'yellow')}
    return P


def palette_wood():
    """FP04 / FP05: FR01's giant-root bark, FR04's heartwood (the foot-worn notch and log tops) and sawn rings."""
    P = palette()
    P['big_bark'] = fm.bark('Path_BigRoot_Bark', tone=1.12, moss=1.25)
    P['log_bark'] = [fm.bark(f'Step_Log_Bark_{i}', tone=t, moss=mo) for i, (t, mo) in enumerate(((1.0, 1.1), (.92, 1.3)))]
    P['log_new'] = fm.bark('Step_Log_Bark_New', tone=1.8, moss=.08)          # the one replaced log, not yet weathered
    P['stake'] = fm.bark('Step_Stake_Bark', tone=1.3, moss=.45)
    P['heart'] = fm.heartwood('Path_Heartwood'); P['rings'] = fm.rings('Path_Rings')
    return P


def collision(RL, V, F, ds=.5, dt=.1, s_list=None, col_h=None):
    """The walking surface as one closed slab: the bare kit section (no relief: it stays within 2 cm of what shows) every 0.5 m
    along (or at s_list) and 0.1 m across, a bottom on the piece's base, walls round it. col_h(s, t) replaces the bare section
    where the walking height is not the section (FP04 over the root, FP05 up the steps). Both end walls are the same section, so
    the collision of one piece meets the next with no step."""
    Fr = RL.F
    if s_list is None:
        n_ = int(round(Fr.L / ds)); s_list = [Fr.L * i / n_ for i in range(n_ + 1)]
    col_h = col_h or (lambda s, t: Fr.ground(s) + PP.section(t))
    ni = len(s_list) - 1; nj = int(round(2 * PP.HW / dt)); cu = nj + 1; b0 = len(V)
    for s in s_list:
        for j in range(cu):
            t = -PP.HW + 2 * PP.HW * j / nj; V.append(tuple(Fr.p(s, t, col_h(s, t))))
    for s in s_list:
        for j in range(cu):
            t = -PP.HW + 2 * PP.HW * j / nj; V.append(tuple(Fr.p(s, t, Fr.base(s))))
    nb = (ni + 1) * cu
    for i in range(ni):
        for j in range(nj):
            a = b0 + i * cu + j
            F.append((a, a + cu, a + cu + 1, a + 1)); F.append((a + nb, a + nb + 1, a + nb + cu + 1, a + nb + cu))
    ring = [i * cu for i in range(ni + 1)] + [ni * cu + j for j in range(1, cu)] + [i * cu + nj for i in range(ni - 1, -1, -1)] + [j for j in range(nj - 1, 0, -1)]
    for k in range(len(ring)):
        a, b = b0 + ring[k], b0 + ring[(k + 1) % len(ring)]
        F.append((a, a + nb, b + nb, b))


def joints(RL):
    """Socket_Path_W at s = 0, Socket_Path_E at s = L, both on the centre line at ground level, local +Y pointing out of the piece."""
    Fr = RL.F; t0, t1 = Fr.tangent(0.), Fr.tangent(Fr.L)
    socket('Socket_Path_W', tuple(Fr.p(0., 0., Fr.ground(0.))), rot=(0, 0, math.atan2(-t0.y, -t0.x) - math.pi / 2))
    socket('Socket_Path_E', tuple(Fr.p(Fr.L, 0., Fr.ground(Fr.L))), rot=(0, 0, math.atan2(t1.y, t1.x) - math.pi / 2))


def dress(P, RL, R, stones, roots, ferns, n_leaves=210, n_moss=22, grass=8, s_margin=.4):
    """Everything on top of the slab, in the order that lets each thing rest on what is already there."""
    L = RL.F.L
    for k, (a, b, r) in enumerate(roots):
        PP.root_across('Path_Root', RL, a, b, r, P['root'][k % 2], R)
    for s, t, size in stones:                                  # pushed out of the tread: half sunk in the bank soil
        sz = size * .6; c = RL.world(s, t, sz * .25)
        FP.pebble('Path_Stone', tuple(c), size, R.choice(P['stone']), seed=R.randrange(999), flat=.6, detail=0 if size >= .09 else 1)
    Rm = random.Random(S['asset'] + '_moss'); placed = []
    for i in range(n_moss * 3):                               # moss creeping in over the bank crests and outer edge
        if len(placed) >= n_moss: break
        s = Rm.uniform(s_margin, L - s_margin); r_ = Rm.uniform(.09, .16); t = Rm.choice((-1, 1)) * Rm.uniform(.5, .79 - r_ * 1.3)
        q = RL.world(s, t, .3); hit = FP.snap(tuple(q), (0, 0, -1))
        if not hit or any((hit[0] - p).length < .3 for p in placed): continue
        if hit[0].z > RL.world(s, t).z + .015: continue           # landed on a stone or a root, not on the bank soil
        placed.append(hit[0].copy())
        FP.moss_patch('Bank_Moss', tuple(hit[0]), tuple(hit[1]), r_, P['moss'], seed=i, snap_each=True, flat=.9)
    Rl = random.Random(S['asset'] + '_leaves'); n = 0
    for i in range(n_leaves * 2):                              # leaves drifted along the banks, a few kicked onto the tread
        if n >= n_leaves: break
        s = Rl.uniform(.2, L - .2)
        t = Rl.choice((-1, 1)) * (Rl.uniform(.36, .77) if Rl.random() < .72 else Rl.uniform(0., .36))
        kind = 'maple' if Rl.random() < .55 else 'lance'
        Lf = Rl.uniform(.09, .13) if kind == 'maple' else Rl.uniform(.055, .085)
        tone = Rl.choices(('orange', 'brown', 'yellow'), (.48, .36, .16))[0]
        q = RL.world(s, t)
        o = PP.leaf('Fallen_Leaf', q.x, q.y, Rl.uniform(0, math.tau), Lf, kind, P['leaf'][tone], Rl,
                    detail=1 if n % 3 == 0 else 2)          # one leaf in three stays at LOD1, so the banks don't go bare at once
        if o is not None: n += 1
    S['leaves_laid'] = n
    Rf = random.Random(S['asset'] + '_ferns')
    for k, (s, t, L_, nf, young) in enumerate(ferns):
        PP.fern_clump('Edge_Fern', RL, s, t, L_, nf, (P['fern'], P['fern_old'], P['fern_stem']), Rf, young=young,
                      detail=2 if young else 1)
    Rg = random.Random(S['asset'] + '_grass')
    for i in range(grass):
        s = Rg.uniform(s_margin, L - s_margin); t = Rg.choice((-1, 1)) * Rg.uniform(.72, .77)
        FP.grass_tuft('Edge_Grass', tuple(RL.world(s, t, -.004)), Rg.randint(3, 5), Rg.uniform(.07, .11), P['grass'], Rg, spread=.02)


def fp01_straight(P):
    RL = PP.Relief(PP.Straight(6.), 'FP01'); R = random.Random('FP01_PathStraight')
    S['relief'] = RL
    PP.slab('Path_Ground', RL, pm.path_earth('Path_Earth', RL.F.L), group='Ground')
    roots = [((.95, .7), (2.55, -.68), .032), ((3.55, -.7), (5.0, .66), .026), ((4.3, .02), (4.75, -.62), .015), ((1.75, .02), (1.45, .55), .012)]
    stones = [(1.0, .6, .11), (2.05, .67, .065), (3.25, .56, .14), (3.52, .71, .055), (5.05, .62, .085), (.62, .55, .045),
              (1.62, -.61, .13), (2.85, -.7, .06), (4.1, -.6, .1), (4.48, -.73, .05), (5.3, -.56, .07), (2.25, -.5, .04),
              (2.6, .31, .035), (3.95, -.34, .03), (1.0, -.29, .028), (5.6, .45, .03), (3.3, -.42, .032)]
    ferns = [(.6, .7, .44, 8, False), (1.75, .71, .4, 7, False), (2.85, .7, .46, 8, False), (4.15, .7, .42, 8, False), (5.35, .7, .4, 7, False),
             (1.1, -.7, .45, 8, False), (2.35, -.71, .42, 7, False), (3.6, -.7, .44, 8, False), (4.85, -.7, .46, 8, False),
             (3.45, .64, .2, 5, True), (.4, -.66, .18, 4, True), (5.65, -.67, .19, 5, True), (2.25, .63, .17, 4, True)]
    dress(P, RL, R, stones, roots, ferns)
    joints(RL)
    V, F = [], []; collision(RL, V, F)
    S['collision_mesh'] = (V, F)
    S['prop'] = dict(kind='path')


NOTE_01 = ('林間土路直段（三視圖 FP01 candidate-01）：長 6 m、寬 2.0 m（工作包原寫 1.6 m，2026-11-09 依使用者指示加寬：踏面 1.16 m、兩側土埂各 0.42 m）、高 0.3 m 以內。踩實的深褐林土路面，比兩側土埂低約 6 cm，'
           '中間有一道踩出的淺溝（深 8 mm）；兩條細樹根斜斜橫過路面、只露出上半；小石頭被踢到兩側土埂上，苔從外緣爬上埂頂，'
           '落葉（楓葉與長葉，橘、褐、黃）沿兩側堆、少數散在路面，兩側各三到四叢蕨拱向路面。'
           '兩端截面就是套件共用截面（最後 0.4 m 起伏漸平），任一段的端口可接任一段；路面貼圖沿路方向以 6 m 為週期，兩端顏色相同。'
           '和石板山路、山城石階、村路、茶田步道、碎石小徑不同：沒有石板、碎石、路緣，只有土。'
           '碰撞：一塊共用截面的簡化土板（不含起伏、樹根、石頭、植物）；接口 Socket_Path_W／Socket_Path_E（兩端中線地面，朝外）。')


# ------------------------------------------------------------------ FP02-FP05
def layout(L, R, n_roots=2, free=lambda s, side: True, young=2, tread_stones=4, fern_L=(.4, .46), margin=.45):
    """Stones, ferns and thin roots by FP01's recipe (FP01 itself is laid out by hand): a fern crown every 1.05-1.35 m along each
    bank, stones between them, a few pebbles on the tread edges, n_roots thin roots crossing diagonally. free(s, side) keeps a
    stretch clear (FP04's root)."""
    ferns, stones, roots = [], [], []
    for side in (1, -1):
        s = R.uniform(margin, margin + .35)
        while s < L - margin:
            if free(s, side): ferns.append((s, side * R.uniform(.69, .71), R.uniform(*fern_L), R.choice((7, 8)), False))
            s += R.uniform(1.05, 1.35)
        s = R.uniform(.5, .9)
        while s < L - .5:
            if free(s, side) and all(abs(s - f[0]) > .32 or f[1] * side < 0 for f in ferns):
                stones.append((s, side * R.uniform(.55, .71), R.choice((.045, .055, .065, .085, .1, .12, .14))))
            s += R.uniform(.45, .8)
    for k in range(young):
        for _ in range(20):
            s = R.uniform(margin, L - margin); side = R.choice((1, -1))
            if free(s, side) and all(abs(s - f[0]) > .35 for f in ferns if f[1] * side > 0): break
        ferns.append((s, side * R.uniform(.63, .66), R.uniform(.17, .2), R.choice((4, 5)), True))
    for k in range(tread_stones):
        s = R.uniform(.6, L - .6); side = R.choice((1, -1))
        if free(s, side): stones.append((s, side * R.uniform(.28, .45), R.uniform(.028, .035)))
    for k in range(n_roots):
        s0 = L * (k + .5) / n_roots + R.uniform(-.3, .3); side = (-1) ** k
        if free(s0, 1) and free(s0, -1):
            roots.append(((s0 - .75, side * .7), (s0 + .75, -side * .68), R.uniform(.024, .032)))
    s0 = R.uniform(1., L - 1.)
    if free(s0, 1): roots.append(((s0, .02), (s0 - .3, .55), .012))
    return ferns, stones, roots


def _finish_path(RL, **col):
    joints(RL)
    V, F = [], []; collision(RL, V, F, **col)
    S['collision_mesh'] = (V, F)
    S['prop'] = dict(kind='path')


def fp02_curve(deg, side):
    """FP02: a 5.5 m bend of deg degrees to the left (side +1) or right (-1); the inside bank worn lower and the centre line drawn
    in towards it where people cut the corner."""
    def build(P):
        aid = S['asset']; Fr = PP.Arc(math.radians(deg), 5.5 / math.radians(deg), side)
        big = deg > 45
        RL = PP.Relief(Fr, aid, inner=(side, .035 if big else .02, .1 if big else .05)); S['relief'] = RL
        R = random.Random(aid)
        PP.slab('Path_Ground', RL, pm.path_earth('Path_Earth', Fr.L), group='Ground')
        ferns, stones, roots = layout(Fr.L, R)
        dress(P, RL, R, stones, roots, ferns, n_leaves=int(210 * Fr.L / 6))
        _finish_path(RL, s_list=[Fr.L * i / 11 for i in range(12)])
    return build


def fp03_slope(P):
    """FP03: 6 m climbing 1.2 m (smoothstep, steepest 16.7 deg mid-way, level at both ends), a solid wedge down to z = 0. Two rain
    rills down the tread either side of the centre line, deepest where it is steepest; three flat stones pressed into the steep
    middle for footing; two roots across holding the slope."""
    Fr = PP.Slope(6., 1.2)
    def rills(s, t):
        k = math.sin(math.pi * s / Fr.L) ** 2; out = 0.
        for sg, o in ((1, 0.), (-1, 7.)):
            c = sg * (.19 + .05 * noise.noise(Vector((s * .7 + o, 3.1, .5))))
            out -= .014 * math.exp(-((t - c) / .045) ** 2)
        return out * k
    RL = PP.Relief(Fr, 'FP03', extras=[rills]); S['relief'] = RL; R = random.Random('FP03_PathSlope')
    PP.slab('Path_Ground', RL, pm.path_earth('Path_Earth', Fr.L), group='Ground')
    for k, (s, t, size) in enumerate(((2.45, .08, .2), (2.95, -.12, .22), (3.45, .13, .19))):      # footing stones, tops ~1.5 cm proud
        c = RL.world(s, t, .015 - size * .25)
        FP.pebble('Footing_Stone', tuple(c), size, P['stone'][k % 2], seed=40 + k, flat=.25, detail=0)
    ferns, stones, roots = layout(Fr.L, R, n_roots=0, tread_stones=2)
    roots = [((1.55, .72), (2.45, -.7), .03), ((3.95, -.72), (4.65, .66), .028), ((3.2, .68), (3.42, .4), .014)]
    dress(P, RL, R, stones, roots, ferns)
    _finish_path(RL, s_list=[Fr.L * i / 24 for i in range(25)])


# FP04: one thick root straight across the path, worn into a notch where people step over it
S0, SKEW = 3., .12
ROOT = [(-.5, .2, .27), (-.3, .135, .255), (0., .12, .25), (.3, .128, .255), (.5, .2, .27)]   # over the tread: (across, centre height, radius)
# beyond the tread the root swings along the bank (an S), rises into a knee on the crest and dives into an earth mound
def _root_ends():
    """Beyond the tread the root turns along the bank on a quarter circle of radius 0.31 m (wider than the root is thick, so its
    inner side never folds), rises into a knee on the crest, then runs on along the bank and dives into an earth mound."""
    R_, sk = .31, SKEW * .5
    pts = []
    for k, (z, r) in enumerate(((.24, .265), (.21, .23), (.14, .18))):
        ph = math.radians(30 * (k + 1))
        pts.append((sk - R_ + R_ * math.cos(ph), .5 + R_ * math.sin(ph), z, r))
    pts += [(sk - R_ - .25, .8, .03, .15), (sk - R_ - .5, .8, -.06, .12)]
    return {1: pts, -1: [(-ds, -t, z, r) for ds, t, z, r in pts]}


ROOT_ENDS = _root_ends()   # (ds, t, z, r)


def _root_at(t):
    for (t0, z0, r0), (t1, z1, r1) in zip(ROOT, ROOT[1:]):
        if t0 <= t <= t1:
            u = (t - t0) / (t1 - t0); return z0 + (z1 - z0) * u, r0 + (r1 - r0) * u
    return None


def _notch(t):
    """The worn flat on top of the root: 0.32 m over the tread (a strip about 0.3 m wide), rising into the uncut root over the bank
    crests."""
    a = abs(t)
    if a < .38: return .32
    if a < .54: return .32 + (a - .38) / .16 * .24
    return None


def _heap(s, t):
    """Soil heaped and trodden up against both faces of the root: 0.13 m at the root, gone 0.95 m away."""
    m = abs(s - (S0 + SKEW * t))
    return .13 * (1. if m < .16 else PP._ss(1 - (m - .16) / .8))


def fp04_root(P):
    Fr = PP.Straight(6.); RL = PP.Relief(Fr, 'FP04', extras=[_heap]); S['relief'] = RL; R = random.Random('FP04_PathRootCrossing')
    PP.slab('Path_Ground', RL, pm.path_earth('Path_Earth', Fr.L), group='Ground')
    pts, radii = [], []
    for ds, t, z, r in ROOT_ENDS[-1][::-1]:
        pts.append(tuple(Fr.p(S0 + ds, t, z))); radii.append(r)
    for t, z, r in ROOT:
        pts.append(tuple(Fr.p(S0 + SKEW * t, t, z))); radii.append(r)
    for ds, t, z, r in ROOT_ENDS[1]:
        pts.append(tuple(Fr.p(S0 + ds, t, z))); radii.append(r)
    def flat(p):
        s, t = Fr.inv(p.x, p.y); return _notch(t)
    # the notch keeps the bark material: its foot-polished top is the bark shader's worn tone (light, warm, no cracks on top);
    # a separate heartwood face showed a saw-toothed edge along the ring quads
    PP.bark_log('Path_BigRoot', pts, radii, (P['big_bark'], P['big_bark'], P['rings']), 'FP04_root', step=.05, nv=40, flat=flat,
                caps=('dome', 'dome'), fiss=.26, lump=.08, ground_cut=.004)
    for k, side in enumerate((1, -1)):          # a side root off each knee, the other way along the bank
        q = [Fr.p(S0 + side * .02, side * .66, .2), Fr.p(S0 + side * .35, side * .76, .12), Fr.p(S0 + side * .7, side * .8, -.06)]
        FP.sweep('Path_SideRoot', [tuple(v) for v in q], [.12, .09, .065], P['big_bark'], step=.05, fiss=.2, seed=60 + k, worn=.7, lump=.08)
    for side in (1, -1):              # the earth the root dives into beyond each bank: a humus heap from the path edge to the 2 m edge
        def out(a, b):               # the grid's outer edge is an ellipse: a rounded heap, no square plate beyond the path
            return .802 + (b - .802) * math.sqrt(max(.02, 1 - (a / 1.1) ** 2))
        def hfn(a, b):               # starts 2 mm outside the slab at the slab's edge height (no shared faces), peaks 0.2 m over the root
            u = (b - .802) / .193        # across the grid (0 at the slab, 1 at the rim): the heap comes down to the ground all round
            return .012 * (1 - u) + .21 * math.exp(-(a / .6) ** 2) * math.sin(math.pi * min(1., u)) ** .8
        FP.mound('Root_Mound', hfn, -1.1, 1.1, .802, .995, P['earth'], nx=44, ny=10,
                 mapfn=lambda a, b, side=side: tuple(Fr.p(S0 + a, side * out(a, b), 0.)))
    free = lambda s, side: abs(s - S0) > 1.15
    ferns, stones, roots = layout(Fr.L, R, n_roots=2, free=free)
    roots = [r for r in roots if abs((r[0][0] + r[1][0]) / 2 - S0) > 1.6]
    dress(P, RL, R, stones, roots, ferns)
    def col_h(s, t):
        soil = Fr.ground(s) + PP.section(t) + _heap(s, t)
        zr = _root_at(t)
        if zr is None: return soil
        cz, r = zr; d = s - (S0 + SKEW * t)
        if abs(d) >= r: return soil
        top = cz + r * math.sqrt(1 - (d / r) ** 2); n = _notch(t)
        return max(soil, min(top, n) if n is not None else top)
    sl = sorted({round(v, 4) for v in [.25 * i for i in range(25)] + [S0 - .5 + .04 * i for i in range(26)]})
    _finish_path(RL, s_list=sl, col_h=col_h)


# FP05: six half-buried log steps, each held by two stakes on the downhill side
STEP_S = [.5 + .4 * k for k in range(6)]; STEP_RISE = .25


def fp05_steps(P):
    Fr = PP.StairsY(3., STEP_S, STEP_RISE, run=.1); RL = PP.Relief(Fr, 'FP05'); S['relief'] = RL; R = random.Random('FP05_PathLogSteps')
    keep = [a + d for a in STEP_S for d in (-.05, .05)]
    PP.slab('Path_Ground', RL, pm.path_earth('Path_Earth', Fr.L), group='Ground', keep_s=keep)
    noses = []
    for k, sk in enumerate(STEP_S):
        r = R.uniform(.128, .142); top = (k + 1) * STEP_RISE + PP.section(0.) + .012; zc = top - r
        bow = R.uniform(-.012, .012); pts = []
        for i in range(9):
            t = -.77 + 1.54 * i / 8
            pts.append(tuple(Fr.p(sk + bow * math.sin(math.pi * i / 8), t, zc + R.uniform(-.004, .004))))
        bark = P['log_new'] if k == 2 else P['log_bark'][k % 2]
        PP.bark_log('Step_Log', pts, [r * R.uniform(.96, 1.04) for _ in pts], (bark, P['heart'], P['rings']), f'FP05_log{k}', step=.06,
                    nv=30, flat=lambda p, z=top - .012: z, fiss=.16 if k == 2 else .2, lump=.04)
        noses.append(sk - .55 * r)
        for side in (1, -1):                                   # stakes on the downhill side, pale tops a hand above the log
            t = side * R.uniform(.5, .56); ss_ = sk - r - .045; rs = R.uniform(.032, .04)
            b = Fr.p(ss_, t, k * STEP_RISE + .02); tp = Fr.p(ss_, t, top + R.uniform(.05, .08))
            PP.bark_log('Step_Stake', [tuple(b), tuple((b + tp) / 2), tuple(tp)], [rs] * 3, (P['stake'], P['heart'], P['rings']), f'FP05_st{k}{side}',
                        step=.05, nv=12, fiss=.12, lump=.03)
    S['step_noses'] = noses
    ferns = []
    for k, sk in enumerate(STEP_S[:-1]):
        side = 1 if k % 2 == 0 else -1
        ferns.append((sk + .2, side * .71, R.uniform(.3, .34), 6, False))
    ferns.append((STEP_S[1] + .2, .66, .17, 4, True)); ferns.append((STEP_S[3] + .2, -.66, .17, 4, True))
    stones = [(.18, .6, .09), (.22, -.62, .12), (2.82, .62, .07), (2.78, -.6, .06), (.3, .3, .03)]
    dress(P, RL, R, stones, [], ferns, n_leaves=95, n_moss=10, grass=6, s_margin=.3)
    def col_h(s, t):
        return sum(STEP_RISE for n in noses if s >= n - .001) + PP.section(t)     # s_list is rounded to 0.1 mm
    sl = sorted({round(v, 4) for v in [.1 * i for i in range(31)] + [n - .002 for n in noses] + noses})
    _finish_path(RL, s_list=sl, col_h=col_h)


def register(ASSETS):
    ASSETS['FP01_PathStraight'] = dict(zh='林間土路直段', kind='path', palette=palette, build=fp01_straight, limit=(6., 2., .3), tex=2048,
        ver='v001', box=((-3., -1., 0.), (3., 1., .3)), ref='FP01/candidate-01', slot='D1_ForestEdge_to_D2_ElderTree', minTier='standard',
        clamp_max=.03, uv_weight={'Ground': 1.6, 'Detail_Small': .45}, origin='centre of the footprint at ground level; walk along X, west end at -X',
        note=NOTE_01)
    common = dict(kind='path', tex=2048, ver='v001', slot='D1_ForestEdge_to_D2_ElderTree', minTier='standard', clamp_max=.03,
                  uv_weight={'Ground': 1.6, 'Detail_Small': .45})
    for deg in (30, 60):
        for side, tag, zh in ((1, 'L', '左'), (-1, 'R', '右')):
            ASSETS[f'FP02_PathCurve{deg}_{tag}'] = dict(common, zh=f'林間土路彎段 {deg}° {zh}彎', palette=palette, build=fp02_curve(deg, side),
                limit=(6., 6., .3), box=((-3., -3., 0.), (3., 3., .3)), ref='FP02/candidate-01',
                origin='centre of the strip outline at ground level; enters along +X at Socket_Path_W',
                note=NOTE_02.format(deg=deg, zh=zh, r=round(5.5 / math.radians(deg), 2), low='3.5' if deg > 45 else '2', sh='10' if deg > 45 else '5'))
    ASSETS['FP03_PathSlope'] = dict(common, zh='林間土路坡段', palette=palette, build=fp03_slope, limit=(6., 2., 1.6),
        box=((-3., -1., 0.), (3., 1., 1.6)), ref='FP03/candidate-01', slope_max=25.,
        origin='centre of the footprint at the foot of the slope (z = 0); climbs along +X', note=NOTE_03)
    ASSETS['FP04_PathRootCrossing'] = dict(common, palette=palette_wood, zh='巨根橫過路面', build=fp04_root, limit=(6., 2.4, .8),
        box=((-3., -1.2, 0.), (3., 1.2, .8)), ref='FP04/candidate-01', slope_max=35., step_max=.2,
        uv_pad=4., vis_skip=lambda s, t: abs(s - (S0 + SKEW * t)) < .32, uv_weight={'Ground': 1.6, 'Main': 1.2, 'Detail_Small': .45},
        origin='centre of the footprint at ground level; walk along X, west end at -X', note=NOTE_04)
    ASSETS['FP05_PathLogSteps'] = dict(common, palette=palette_wood, zh='原木階梯', build=fp05_steps, limit=(2., 3., 1.8),
        box=((-1., -1.5, 0.), (1., 1.5, 1.8)), ref='FP05/candidate-01', slope_max=12., step_max=.27,
        uv_shape='CONVEX', vis_skip=lambda s, t: any(-.2 < s - a < -.06 for a in STEP_S), uv_weight={'Ground': 1.3, 'Main': 1.3, 'Detail_Small': .45},
        origin='centre of the footprint at the foot of the steps (z = 0); climbs along +Y, front (-Y) is the foot', note=NOTE_05)


NOTE_02 = ('林間土路彎段 {deg}° {zh}彎（三視圖 FP02 candidate-01）：中線長 5.5 m、半徑 {r} m，寬 2.0 m（同 FP01 加寬）、高 0.3 m 以內，放得進 6×6 m。'
           '截面、土色、落葉、蕨、石頭和 FP01 同一套；彎道內側的土埂被抄近路的腳踩低 {low} cm、中間的淺溝往內側偏 {sh} cm，'
           '兩者在彎道中間最明顯、兩端歸零。兩端截面就是套件共用截面，可接 FP01 或任一段。'
           '碰撞：共用截面的簡化土板（每 0.5 m 一段弦）；接口 Socket_Path_W（入口）／Socket_Path_E（出口）。')
NOTE_03 = ('林間土路坡段（三視圖 FP03 candidate-01）：長 6 m、寬 2.0 m（同 FP01 加寬），上升 1.2 m；坡形是平滑 S 形，兩端水平，中間最陡 16.7°（要求 ≤ 25°）。'
           '整段是實心土楔，底面在 z = 0。踏面兩側各一道雨水沖出的淺溝（最深 1.4 cm，在最陡處）；最陡的中段壓著三塊扁石當踏腳，'
           '兩條樹根斜過路面把坡抓住。兩端截面就是套件共用截面；上端接口高 1.2 m。'
           '碰撞：共用截面沿坡形的簡化土板（每 0.25 m 一段）；接口 Socket_Path_W（坡腳）／Socket_Path_E（坡頂）。')
NOTE_04 = ('巨根橫過路面（三視圖 FP04 candidate-01，樹皮與苔照 FR01）：長 6 m、寬 2.4 m（工作包原寫 2 m；路面隨 FP01 加寬到 2.0 m，兩側土丘再各外推 0.2 m）、高 0.8 m 以內。一條粗根（直徑約 0.5 m）'
           '在踏面上斜約 5°、在土埂上斜約 7° 橫過路面，到兩側土埂各拱起一個根膝（根背約 0.52 m），再順著土埂彎成 S 形鑽進一堆橢圓的腐植土丘（高約 0.2 m）；'
           '路面正上方被踩出一道平的凹口（離地 0.32 m、寬約 0.3 m，仍是樹皮材質，被腳磨亮的暖淺色），兩個根膝各分出一條小根鑽進土裡。'
           '根兩面的土被踩成斜坡堆到 0.13 m，所以從土坡跨上凹口約 0.19 m。'
           '兩端截面就是套件共用截面。碰撞：土板加上根的形狀（凹口平台與兩側斜坡，根附近每 4 cm 一段）；接口同 FP01。')
NOTE_05 = ('原木階梯（三視圖 FP05 candidate-01）：寬 2.0 m（同 FP01 加寬）、長 3 m，踏面總共升高 1.5 m（六階，每階 0.25 m、踏深 0.4 m）。'
           '六根半埋的原木（直徑約 0.27 m、長約 1.95 m）橫在每一階前緣，頂面被踩出一條平的淺色木心，下坡側各兩根木樁擋住；第三根是後來換上的新木，'
           '顏色較淺、苔少。木頭後面填實的土就是踏面；整段是實心土楔，底面在 z = 0。'
           '工作包寫 1.6×3×1.5，寬度已依指示改 2.0；1.5 是踏面升高，加上兩側土埂與蕨，總高約 1.7 m。兩端截面就是套件共用截面；上端接口高 1.5 m。'
           '碰撞：每階一個垂直台階（在原木前緣 0.55 半徑處），台階高 0.25 m；接口 Socket_Path_W（階腳）／Socket_Path_E（階頂）。')
