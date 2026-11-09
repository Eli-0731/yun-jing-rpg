"""FR01 giant root wall sections (work pack B-104h part 2): three shapes, each within 6 x 2 x 2.2 m.

Three-view FR01 candidates 03 + 04 + 01 (README picks): 03 parallel roots stacked with earth and stones packed between them (the
most wall-like), 04 thick roots braided round each other, 01 one huge root rising and diving in waves with smaller roots wound
along it. All three lie along the same plan arc (6 m chord, each end turned 10 deg), so any three in a row make a 60 deg curved
wall, and their ends are the same: every root dives into one earth bank whose section at the joint is identical in all three.
Origin: centre of the chord at ground level; the front (-Y) is the concave side. Sockets Socket_Join_W / Socket_Join_E sit on
the joint line, each pointing out along the wall: put the next section's Socket_Join_W on this one's Socket_Join_E, facing back.

Not A06 RootStump (a low stump, 0.45 m) and not A03 FallenLog (one round log lying on the ground): these are living surface roots
of a tree out of frame, taller than a person, flattened like planks where they run level, with packed earth between them.
"""
import math, random
from mathutils import Vector, noise
from ti_core import S, socket
import fr_parts as FP

ARC = FP.Arc(5.7, math.radians(10))   # 5.7 m on the centre line = 6 m along the back edge, so the radial joint cuts stay inside 6 m
V0, V1 = -.85, .85              # earth bank across the depth (metres behind the centre line)
H_END = .18                     # bank height on the joint line (the roots dive into the ground before it)


def bell(v): return max(0., 1. - (abs(v) / .85) ** 2) ** .9


def bank(u, v, Hc, seed):
    """Earth bank height. Hc(u) the crest along the wall; at the joints (|u| = U) only the shared end section remains."""
    U = ARC.U; k = max(0., min(1., (U - abs(u)) / 1.3)); k = k * k * (3 - 2 * k)     # 0 on the joint line, 1 from 1.3 m in
    h = (H_END + (Hc(u) - H_END) * k) * bell(v)
    h += k * bell(v) ** .3 * (.1 * noise.noise(Vector((u * .9, v * 1.6, seed))) + .04 * noise.noise(Vector((u * 3., v * 3., seed + 3.))) + .015 * noise.noise(Vector((u * 9., v * 9., seed + 5.))))
    return max(.004, h)


def W(pts):
    """(u, v, z) along the arc -> world points."""
    return [tuple(ARC.p(u, v, z)) for u, v, z in pts]


def root(name, pts, radii, P, R, aspect=.82, mat=None, dive=True, jitter=1., **kw):
    """A root along (u, v, z) points, made less regular: the path is re-sampled every 0.45 m and each point nudged (a root
    meanders and swells at knots). dive: an end that comes down below 0.8 m carries on into the ground (cut at the surface),
    stopping short of the joint line by its own radius so nothing crosses the 6 m limit."""
    pts = list(pts); radii = list(radii)
    if dive:
        for i in (0, -1):
            u, v, z = pts[i]; r = radii[i]
            if z < .8:
                lim = ARC.U - .12 - r * 1.15
                pts[i] = (max(-lim, min(lim, u)), v, -.5 * r)
        # drop inner points that lie beyond a pulled-in end (they made the root double back into a hook)
        ue0, ue1 = pts[0][0], pts[-1][0]; lo_, hi_ = min(ue0, ue1), max(ue0, ue1)
        mid = [p for p in pts[1:-1] if lo_ + .25 < p[0] < hi_ - .25] if abs(ue1 - ue0) > 1. else pts[1:-1]
        keep = [k for k, p in enumerate(pts) if k in (0, len(pts) - 1) or p in mid]
        pts = [pts[k] for k in keep]; radii = [radii[k] for k in keep]
    if jitter:
        sm = FP._crspline([p + (r,) for p, r in zip(pts, radii)], 8)
        L = sum(((sm[i + 1][0] - sm[i][0]) ** 2 + (sm[i + 1][1] - sm[i][1]) ** 2 + (sm[i + 1][2] - sm[i][2]) ** 2) ** .5 for i in range(len(sm) - 1))
        n = max(len(pts), int(L / .45) + 1); idx = [round(k * (len(sm) - 1) / (n - 1)) for k in range(n)]
        out, rr = [], []
        for k, i in enumerate(idx):
            u, v, z, r = sm[i]; end = k in (0, n - 1)
            j = 0. if end else jitter
            out.append((u + j * R.uniform(-.05, .05), v + j * R.uniform(-.07, .07), z + j * R.uniform(-.06, .06)))
            rr.append(r * (1. + (0. if end else jitter * R.uniform(-.1, .14))))
        pts, radii = out, rr
    return FP.sweep(name, W(pts), radii, mat or R.choice(P['bark']), aspect=aspect, seed=R.randrange(9999), **kw)


def rootlets(P, R, n, hfn, roots_low, side):
    """Fine roots that leave a big root low down and creep out over the earth bank, lying on it, then slip in; the last 0.2 m pale."""
    for i in range(n):
        u0, v0, z0 = R.choice(roots_low); u0 = max(-2.3, min(2.3, u0 + R.uniform(-.3, .3)))
        du = R.uniform(-.5, .5); reach = R.uniform(.3, .5); wig = R.uniform(-.12, .12); r0 = R.uniform(.03, .05)
        pts, rr = [], []
        for k in range(8):
            t = k / 7; u = u0 + du * t + wig * math.sin(t * 6.); v = max(-.8, min(.8, v0 + side * reach * t))
            r = r0 * (1 - .75 * t) + .008
            z = hfn(u, v) + (r * .7 if k < 7 else -.02)
            if k == 0: z += .06
            pts.append((u, v, z)); rr.append(r)
        FP.sweep('Rootlet', W(pts), rr, R.choice(P['bark']), step=.055, fiss=.1, plates=2., lump=.06, nring=6,
                 seed=R.randrange(999), tip=(P['tip'], .2), detail=1)


def stones(P, R, hfn, n, side, uband=2.6):
    for i in range(n):
        u = R.uniform(-uband, uband); s = R.uniform(.09, .19); v = side * R.uniform(.45, (.72 if side < 0 else .6) - s)
        FP.pebble('Earth_Stone', tuple(ARC.p(u, v, hfn(u, v) - s * .35)), s, R.choice(P['stone']), seed=R.randrange(999), flat=.62, detail=1)


def growth(P, R, hfn, n_fern=9, n_moss=18, n_grass=12):
    spots = []
    for i in range(n_fern):          # ferns where the roots meet the bank, fronds fanning along the wall (no room to lean far out)
        side = -1 if i % 3 else 1
        for _ in range(20):          # clumps on one face at least 0.35 m apart (overlapping fronds lie in one plane)
            u = R.uniform(-2.3, 2.3)
            if all(abs(u - a) > .35 for a, b in spots if b == side): break
        spots.append((u, side)); v = side * R.uniform(.5, .6)
        ph = u / ARC.R; tang = Vector((math.cos(ph), -math.sin(ph), 0.)); nrm = Vector((math.sin(ph), math.cos(ph), 0.)) * side
        for k, sgn in enumerate((-1, 1)):
            uu = u + .07 * sgn          # two clumps side by side: fronds from one base point would lie in one plane near it
            FP.fern('Root_Fern', tuple(ARC.p(uu, v, hfn(uu, v) - .02)), P['fern'], R, n=R.randint(4, 6), L=R.uniform(.34, .48),
                    out=tuple((tang * sgn + nrm * .45).normalized()), up_bias=.3, spread=.55)
    for i in range(n_moss):          # moss cushions on the root tops, snapped onto the bark
        u = R.uniform(-2.3, 2.3); q = ARC.p(u, R.uniform(-.3, .35), 3.)
        hit = FP.snap(tuple(q), (0, 0, -1))
        if hit and hit[1].z > .5 and .6 < hit[0].z < 2.05: FP.moss_patch('Root_Moss', tuple(hit[0]), tuple(hit[1]), R.uniform(.12, .2), P['moss'], seed=i, snap_each=True)
    for i in range(n_grass):
        u = R.uniform(-2.6, 2.6); side = R.choice((-1, 1)); v = side * R.uniform(.62, .72 if side < 0 else .62)
        FP.grass_tuft('Earth_Grass', tuple(ARC.p(u, v, hfn(u, v) - .05)), R.randint(3, 5), R.uniform(.08, .14), P['grass'], R, spread=.03)


def joints_and_collision(Hc_fn):
    """Sockets on the joint line, a collision loft that follows the real tops (rays down across the depth)."""
    for side, nm in ((-1, 'W'), (1, 'E')):
        q, head = ARC.end(side)
        socket(f'Socket_Join_{nm}', tuple(q), rot=(0, 0, head + (math.pi if side < 0 else 0.)))
    V, F = [], []; secs = []
    vs = [-.62, -.4, -.18, .05, .28, .5, .66]
    for i in range(15):
        u = -ARC.U + .02 + (2 * ARC.U - .04) * i / 14
        tops = []
        for v in vs:
            hit = FP.snap(tuple(ARC.p(u, v, 4.)), (0, 0, -1)); tops.append(max(.3, (hit[0].z if hit else .3) - .04))
        sec = [tuple(ARC.p(u, -.8, 0.)), tuple(ARC.p(u, .8, 0.))] + [tuple(ARC.p(u, v, z)) for v, z in reversed(list(zip(vs, tops)))]
        secs.append(sec)
    FP.hull_loft(V, F, secs)
    S['collision_mesh'] = (V, F)


# ------------------------------------------------------------------ the three shapes
def stacked(P):
    """Candidate 03: parallel roots stacked in three tiers, front and back, earth and stones packed between."""
    R = random.Random('FR01_Stacked')
    Hc = lambda u: 1.5 - .25 * (u / ARC.U) ** 2
    hfn = lambda u, v: bank(u, v, Hc, 1.)
    FP.mound('Earth_Bank', hfn, -ARC.U, ARC.U, V0, V1, P['earth'], nx=72, ny=24, mapfn=lambda a, b: ARC.xy(a, b))
    low = []
    spec = [  # (u, v, z) path, radii
        ([(-2.95, -.32, .3), (-2.2, -.4, .5), (-1., -.44, .55), (.3, -.4, .58), (1.6, -.43, .52), (2.5, -.36, .45), (2.95, -.3, .3)], [.38, .42, .44, .43, .42, .4, .36]),
        ([(-2.9, .3, .3), (-1.8, .34, .52), (-.4, .36, .58), (1., .32, .55), (2.2, .34, .5), (2.95, .3, .3)], [.36, .4, .42, .41, .39, .35]),
        ([(-2.85, -.18, .55), (-2.1, -.28, 1.0), (-.9, -.3, 1.2), (.5, -.24, 1.16), (1.7, -.28, 1.05), (2.6, -.2, .7), (2.95, -.12, .45)], [.3, .36, .38, .37, .36, .33, .3]),
        ([(-2.9, .18, .5), (-1.9, .24, 1.0), (-.5, .24, 1.15), (1., .2, 1.12), (2.3, .24, .9), (2.95, .16, .5)], [.3, .35, .37, .36, .34, .3]),
        ([(-2.9, .02, .6), (-2.2, -.02, 1.25), (-1.2, .02, 1.62), (0., .06, 1.7), (1.2, .02, 1.62), (2.2, .0, 1.25), (2.95, -.02, .62)], [.3, .36, .4, .41, .4, .36, .3]),
    ]
    for k, (pts, rr) in enumerate(spec):
        root('Root_Tier', pts, rr, P, R, aspect=.8, mat=P['bark'][k % 3], step=.075, fiss=.17, twist=.18)
        if pts[2][2] < .8: low += [(u, v, z) for u, v, z in pts[1:-1]]
    # a root climbing diagonally across the tiers from low left-front to high right, and one dropping from the top tier to the ground
    root('Root_Diagonal', [(-2.6, -.6, .28), (-1.6, -.5, .62), (-.5, -.38, 1.05), (.6, -.22, 1.42), (1.6, -.08, 1.62), (2.3, .0, 1.25), (2.7, .05, .6)],
         [.2, .24, .26, .27, .26, .24, .2], P, R, aspect=.85, step=.06, fiss=.15, twist=.3)
    root('Root_Drop', [(-1.3, .1, 1.5), (-1.5, .4, 1.15), (-1.62, .52, .6), (-1.7, .56, .05)], [.18, .19, .22, .27], P, R, aspect=1., step=.06, fiss=.16, dive=False)
    root('Root_Drop', [(1.05, -.05, 1.55), (1.22, -.4, 1.2), (1.34, -.55, .62), (1.42, -.6, .05)], [.18, .19, .22, .27], P, R, aspect=1., step=.06, fiss=.16, dive=False)
    # small roots wound over the tiers
    for k in range(4):
        u0 = R.uniform(-2.2, 1.2); side = R.choice((-1, 1))
        pts = [(u0 + d, side * (.25 + .3 * math.sin(d * 2.2 + k)), 1.0 + .5 * math.sin(d * 1.3 + k) + .25 * side) for d in (0., .4, .8, 1.2, 1.6)]
        root('Root_Small', pts, [.08, .11, .12, .1, .07], P, R, aspect=1., step=.05, fiss=.12, plates=3.5, detail=1)
    rootlets(P, R, 9, hfn, low, -1); rootlets(P, R, 7, hfn, low, 1)
    stones(P, R, hfn, 14, -1); stones(P, R, hfn, 9, 1)
    growth(P, R, hfn)
    joints_and_collision(Hc)
    S['prop'] = dict(kind='wall', shape='stacked')


def braided(P):
    """Candidate 04: three thick roots braided round each other along an arching axis, two of them sending legs down into the earth."""
    R = random.Random('FR01_Braided')
    Hc = lambda u: 1.1 - .15 * (u / ARC.U) ** 2
    hfn = lambda u, v: bank(u, v, Hc, 2.)
    FP.mound('Earth_Bank', hfn, -ARC.U, ARC.U, V0, V1, P['earth'], nx=72, ny=24, mapfn=lambda a, b: ARC.xy(a, b))
    cu = lambda u: max(0., math.cos(min(1., abs(u) / ARC.U) * math.pi / 2))
    axis_z = lambda u: .55 + .86 * cu(u) ** 1.4
    rad = lambda u: .3 + .08 * cu(u)
    low = []
    for k in range(3):
        ph0 = k * math.tau / 3; pts, rr = [], []
        for i in range(25):
            u = -2.75 + 5.5 * i / 24; ph = ph0 + u * 1.25
            w = .32 * cu(u) ** .6 + .1
            pts.append((u, w * math.cos(ph) * 1.15, axis_z(u) + w * math.sin(ph))); rr.append(rad(u) * (1. - .08 * k))
        root(f'Root_Braid', pts, rr, P, R, aspect=.92, mat=P['bark'][k], step=.07, fiss=.2, twist=.35, jitter=0.)
        low += [p for p in pts if p[2] < .9]
    for u0, side in ((-1.6, -1), (-.3, 1), (1.4, -1), (2.2, 1)):      # legs down into the bank
        ph = u0 * 1.25; top = (u0, .2 * side, axis_z(u0) - .1)
        pts = [top, (u0 + .12, .38 * side, axis_z(u0) * .7), (u0 + .2, .5 * side, axis_z(u0) * .35), (u0 + .28, .55 * side, .05)]
        root('Root_Leg', pts, [.2, .2, .23, .28], P, R, aspect=1., step=.06, fiss=.17, dive=False)
    for k in range(3):                                   # a lower pair of thinner roots along the bank front and back
        side = (-1, 1, -1)[k]
        pts = [(-2.9, .5 * side, .35), (-1.5, .62 * side, .45), (0., .64 * side, .42 + .1 * k), (1.5, .6 * side, .46), (2.9, .48 * side, .33)]
        root('Root_Low', pts, [.16, .2, .2, .19, .15], P, R, aspect=.75, step=.07, fiss=.14, detail=0)
        low += pts[1:-1]
    for k in range(5):                                    # vine-thin roots spiralling round the braid
        ph0 = R.uniform(0, math.tau); u0 = R.uniform(-2.3, .8); pts = []
        for i in range(9):
            u = u0 + i * .2; ph = ph0 + i * .9
            pts.append((u, .5 * math.cos(ph), axis_z(u) + .5 * math.sin(ph)))
        root('Root_Small', pts, [.05 + .03 * math.sin(i / 8 * math.pi) for i in range(9)], P, R, aspect=1., step=.04, fiss=.1, plates=3., nring=10, detail=1, jitter=0.)
    rootlets(P, R, 8, hfn, low, -1); rootlets(P, R, 7, hfn, low, 1)
    stones(P, R, hfn, 13, -1); stones(P, R, hfn, 9, 1)
    growth(P, R, hfn, n_fern=7)
    joints_and_collision(Hc)
    S['prop'] = dict(kind='wall', shape='braided')


def wave(P):
    """Candidate 01: one huge root rising and diving twice along the wall, smaller roots wound along it, a second root behind."""
    R = random.Random('FR01_Wave')
    Hc = lambda u: .95 + .25 * math.cos(u / ARC.U * math.pi / 2)
    hfn = lambda u, v: bank(u, v, Hc, 3.)
    FP.mound('Earth_Bank', hfn, -ARC.U, ARC.U, V0, V1, P['earth'], nx=72, ny=24, mapfn=lambda a, b: ARC.xy(a, b))
    main = [(-2.75, -.15, .45), (-2.25, -.2, 1.0), (-1.45, -.18, 1.42), (-.6, -.12, 1.15), (.35, -.08, .78), (1.2, -.06, 1.05), (1.85, -.1, 1.3),
            (2.3, -.15, .9), (2.7, -.15, .45)]
    mr = [.42, .5, .54, .52, .5, .5, .52, .48, .4]
    root('Root_Main', main, mr, P, R, aspect=.86, mat=P['bark'][0], step=.075, fiss=.2, twist=.2)
    # under the dip the root rests on a low hump of earth (the bank rises there by itself through Hc) and a second root behind
    back = [(-2.9, .45, .35), (-1.9, .5, .6), (-.6, .48, .95), (.6, .46, 1.05), (1.8, .5, .7), (2.9, .45, .35)]
    root('Root_Back', [(u, v - .08, z) for u, v, z in back], [.3, .34, .38, .38, .34, .3], P, R, aspect=.8, mat=P['bark'][1], step=.075, fiss=.17)
    low = [(u, v, z) for u, v, z in main + back if z < .9]
    # a smaller root arching out of the ground in front of the dip, and one behind it
    root('Root_Arch', [(-.9, -.5, .2), (-.35, -.58, .52), (.3, -.6, .6), (.95, -.52, .3)], [.17, .2, .2, .17], P, R, aspect=.85, step=.06, fiss=.17)
    root('Root_Arch', [(-.2, .55, .3), (.4, .5, .7), (1.1, .52, .5), (1.6, .5, .25)], [.16, .19, .19, .15], P, R, aspect=.85, step=.06, fiss=.17)
    for k in range(4):                                    # smaller roots wound round the big one
        ph0 = k * 1.6; u0 = -2.6 + k * 1.3; pts = []; rr = []
        for i in range(11):
            t = i / 10; u = u0 + t * 2.2
            if u > 2.85: break
            # the big root's centre at u (interpolated from its control points)
            j = max(0, min(len(main) - 2, sum(1 for p in main if p[0] <= u) - 1)); a_, b_ = main[j], main[j + 1]
            f = (u - a_[0]) / (b_[0] - a_[0]); cz = a_[2] + (b_[2] - a_[2]) * f; cv = a_[1] + (b_[1] - a_[1]) * f
            rm = (mr[j] + (mr[j + 1] - mr[j]) * f) * .95 + .08; ph = ph0 + t * 3.2
            pts.append((u, cv + rm * math.cos(ph), cz + rm * math.sin(ph) * .9)); rr.append(.1 + .05 * math.sin(t * math.pi))
        if len(pts) > 3: root('Root_Wound', pts, rr, P, R, aspect=1., step=.05, fiss=.12, plates=3.5, nring=12, jitter=0.)
    for u0, side in ((-1.5, -1), (2.1, 1), (-.1, 1)):     # buttress legs from the crests into the earth
        j = 2 if u0 < 0 else 6; top = main[j]
        pts = [(u0, top[1] + .1 * side, top[2] - .15), (u0 + .12, top[1] + .3 * side, top[2] * .72), (u0 + .22, top[1] + .42 * side, top[2] * .38),
               (u0 + .3, top[1] + .48 * side, .05)]
        root('Root_Leg', pts, [.24, .24, .27, .33], P, R, aspect=1., step=.06, fiss=.17, dive=False)
    rootlets(P, R, 9, hfn, low, -1); rootlets(P, R, 6, hfn, low, 1)
    stones(P, R, hfn, 14, -1); stones(P, R, hfn, 9, 1)
    growth(P, R, hfn, n_fern=7)
    joints_and_collision(Hc)
    S['prop'] = dict(kind='wall', shape='wave')


SHAPES = {'Stacked': (stacked, '03', '三層平行根堆疊成牆，前後兩排，根與根之間填土夾石'),
          'Braided': (braided, '04', '三條粗根沿拱起的軸互相絞纏，兩側各有支根插進土裡'),
          'Wave': (wave, '01', '一條巨根兩起兩伏如波浪，小根沿它纏繞，後面另有一條較低的根')}


def register(ASSETS):
    for key, (fn, cand, zh) in SHAPES.items():
        aid = f'FR01_RootWall_{key}'
        note = (f'巨根矮牆段（三視圖 FR01 candidate-{cand}）：{zh}。6 m 弦長、深 2 m、高不超過 2.2 m，沿半徑 17.3 m 的平面弧線擺，兩端各轉 10°，'
                '三段接成 60° 的彎牆；三種形的接頭斷面相同（所有根在接頭前鑽進同一道 0.95 m 高的土坡），可以任意混接。'
                '樹皮是縱向深裂、慢慢繞著根轉的老根皮（照 elder-world-tree-hero-v1 神木根的樣子），平躺處斷面壓扁成板根，上面磨得較平滑、較淺；'
                '背光面（+Y）和頂上長苔，接地處有泥，根腳有細根爬過土面、末端露出淺色根尖；土裡夾圓石，縫裡長蕨。'
                '和 A06 樹根樁（0.45 m 矮樁）、A03 倒木（一根橫躺的圓木）不同：這是比人高、從地底拱出來的活根。'
                '接口：Socket_Join_W／Socket_Join_E（接頭線中心，箭頭朝牆外延伸方向）。下一段的 Socket_Join_W 對上這段的 Socket_Join_E、方向相反。')
        ASSETS[aid] = dict(zh=f'巨根矮牆段（{ {"Stacked": "疊根", "Braided": "絞根", "Wave": "波浪根"}[key] }）', kind='wall', palette=FP.palette, build=fn,
                           limit=(6., 2., 2.2), tex=2048, ver='v001', box=((-3., -1., 0.), (3., 1., 2.2)), ref=f'FR01/candidate-{cand}',
                           slot='D1_ForestEdge_to_D2_ElderTree', minTier='standard', clamp_max=.03, uv_shape='CONVEX',
                           origin='centre of the 6 m chord at ground level; front (-Y) is the concave side of the arc', note=note)
