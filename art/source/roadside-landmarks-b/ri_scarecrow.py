"""RI04 rice-field scarecrows, two kinds (work pack 2026-11-09 B-112h, batch B, RI04; placed in the A6 rice fields).

The Codex version did not pass for being stiff, like pipes put together; this one is built from loose straw. Every straw is its own
thin ribbon (one mesh per bundle): the head is a bundle tied at the neck and folded over at the top, straw bursts out of both sleeve
cuffs and out along the cross bar, hangs in a ragged fringe under the tunic and pokes out at the collar, so the outline is soft and
irregular. A rough wooden cross frame, a worn conical straw hat, a faded tunic with a torn hem and cuffs, cloth patches, a straw-rope
sash, rope ties at the neck, the wrists and the foot of the post. No face, no writing.

  RI04_Scarecrow_A  upright (chosen sheet RI04-cand-4)
  RI04_Scarecrow_B  the second kind, leaning about 7 degrees to its left with the bar tipped, an indigo tunic (RI04-cand-2)

Limit 1.2 x 0.5 x 1.9 m each. Origin: the foot of the post, bottom z = 0, front (the tunic's front) -Y. One 1024 atlas.
"""
import math, random
from mathutils import Vector, noise
from ti_core import S, mesh, lathe, socket, xf, T, RY, RX, cyl
from cr_parts import sheet, log, rope, set_attr_list
import fr_parts as FP
import cr_mats as cm, mk_mats as mm

W, D, H = 1.2, .5, 1.9
BAR_Z, BAR_X = 1.30, .55
NECK_Z, HEAD_TOP = 1.47, 1.73
HAT = (.238, 1.655, 1.835)       # brim radius, brim z, apex z
WAIST_Z, HEM_Z = 1.02, .52       # a long worn robe to the knee, as on the sheets
VARIANTS = {
    'A': dict(lean=0., bar_tilt=0., tunic=(.075, .058, .062), patches=((.125, .065, .04), (.03, .045, .085), (.14, .1, .04)), trim=(.035, .03, .032), seed=4, hat_tilt=(.0, .05), box_x=(-W / 2, W / 2)),
    'B': dict(lean=math.radians(-7.), bar_tilt=math.radians(5.), tunic=(.025, .035, .06), patches=((.14, .105, .045), (.13, .05, .03)), trim=(.07, .062, .05), seed=2, hat_tilt=(.12, -.06),
          box_x=(-.755, .445)),     # leaning left: the 1.2 m box moves 0.155 m left with it, the post foot stays on the origin
}


def palette_for(kind):
    v = VARIANTS[kind]
    def palette():
        P = {}
        P['straw'] = cm.weed_leaf(f'Loose_Straw_{kind}', (.16, .1, .035), (.42, .31, .12), (.55, .45, .2))
        P['straw_old'] = cm.weed_leaf(f'Old_Straw_{kind}', (.12, .085, .04), (.3, .22, .1), (.38, .31, .16))
        P['tunic'] = mm.cloth(f'Tunic_Cloth_{kind}', v['tunic'], weave_=500., dirt=.9, worn=.3, coarse=1.6, ground_h=.0)
        P['trim'] = mm.cloth(f'Collar_Trim_{kind}', v['trim'], weave_=600., dirt=.7, worn=.2, coarse=1.2)
        P['patch'] = [mm.cloth(f'Patch_Cloth_{kind}_{i}', c, weave_=420., dirt=.7, worn=.2, coarse=1.2) for i, c in enumerate(v['patches'])]
        P['hat'] = mm.weave(f'Hat_Weave_{kind}', (.3, .21, .085), (.1, .065, .025), reed=.008, block=.028, green_cast=.06, wobble=.004)
        P['rope'] = mm.hemp(f'Straw_Rope_{kind}', (.24, .18, .08), twist=160.)
        P['pole'] = cm.wood(f'Scarecrow_Pole_{kind}', (.06, .042, .026), (.2, .15, .09), grey=.45, ground_h=.15, moss=True, moss_amt=.5)
        P['grass'] = cm.weed_leaf(f'Field_Weed_{kind}', (.03, .06, .02), (.1, .17, .045), (.2, .24, .07))
        P['pebble'] = cm.stone(f'Field_Pebble_{kind}', light=(.2, .19, .17), dark=(.085, .08, .07), moss=.5)
        return P
    return palette


# ------------------------------------------------------------------ loose straw: one ribbon per straw, one mesh per bundle
def strands(name, specs, mat, nv=4, detail=0):
    """specs: (base, direction, length, width, droop, curl_seed). Each straw is a ribbon of nv quads, tapering to its tip, drooping
    under its own weight (droop x length x v^2), its side turned at random about its length."""
    V, F, UV = [], [], []
    for b, d, L, w, droop, sd in specs:
        b, d = Vector(b), Vector(d).normalized()
        R = random.Random(sd)
        ax = Vector((R.uniform(-1, 1), R.uniform(-1, 1), R.uniform(-1, 1)))
        side = d.cross(ax).normalized() if d.cross(ax).length > 1e-4 else d.orthogonal().normalized()
        bend = Vector((R.uniform(-1, 1), R.uniform(-1, 1), R.uniform(-1, 1))) * .12
        i0 = len(V)
        for j in range(nv + 1):
            v = j / nv
            c = b + d * (L * v) + Vector((0, 0, -droop * L * v * v)) + bend * (L * v * v)
            hw = w * .5 * (1 - .7 * v)
            V += [tuple(c - side * hw), tuple(c + side * hw)]; UV += [(0., v, 0.), (1., v, 0.)]
        for j in range(nv):
            a = i0 + 2 * j; F.append((a, a + 1, a + 3, a + 2))
    # a closed sliver (rim on): the pipeline turns each closed piece outward, so Unity's back-face culling shows the straw from both
    # sides (open double layers were each re-oriented on their own and often ended up facing the same way)
    o = mesh(name, V, F, mat, smooth=True, solid=.0012, rim=True, detail=detail, grain='z')
    set_attr_list(o, 'cuv', UV)
    return o


def _cone_dirs(axis, n, spread, R):
    axis = Vector(axis).normalized(); a = axis.orthogonal().normalized(); b = axis.cross(a)
    out = []
    for _ in range(n):
        t = R.uniform(0, math.tau); s = spread * math.sqrt(R.random())
        out.append((axis * math.cos(s) + (a * math.cos(t) + b * math.sin(t)) * math.sin(s)).normalized())
    return out


def head(P, R):
    """A sheaf tied at the neck, opening into a round bundle and folded over at the top, a few loose ends."""
    specs = []
    for k in range(150):
        t = math.tau * k / 150 + R.uniform(-.02, .02); r0 = R.uniform(.025, .045)
        b = (r0 * math.cos(t), r0 * math.sin(t) * .85, NECK_Z - .02)
        bulge = R.uniform(.09, .115)
        # three segments up the bundle: out, up, in over the top (each its own ribbon, so the outline stays rounded)
        p1 = Vector((bulge * math.cos(t), bulge * .85 * math.sin(t), NECK_Z + .1))
        p2 = Vector((bulge * .8 * math.cos(t), bulge * .7 * math.sin(t), HEAD_TOP - .05))
        p3 = Vector((R.uniform(-.02, .02), R.uniform(-.02, .02), HEAD_TOP + R.uniform(-.01, .01)))
        for a_, c_ in ((Vector(b), p1), (p1, p2), (p2, p3)):
            specs.append((a_, c_ - a_, (c_ - a_).length * 1.04, R.uniform(.007, .011), 0., R.random() * 1e6))
    strands('Head_Straw', specs, P['straw'], nv=2)
    # straw below the neck tie, flaring down into the collar
    specs = [((R.uniform(-.03, .03), R.uniform(-.025, .025), NECK_Z - .01), d, R.uniform(.08, .16), R.uniform(.006, .01), .2, R.random() * 1e6)
             for d in _cone_dirs((0, 0, -1), 60, .9, R)]
    strands('Collar_Straw', specs, P['straw'], nv=3, detail=1)
    rope('Neck_Tie', [(.05 * math.cos(a), .044 * math.sin(a), NECK_Z + .005 * math.sin(3 * a)) for a in [math.tau * q / 12 for q in range(13)]], .009, P['rope'], ply=2, tw=90., seg=6)


def hat(P, R, tilt):
    r, z0, z1 = HAT
    prof = [(0., z1), (.03, z1 - .012), (r * .45, z0 + (z1 - z0) * .5), (r * .85, z0 + .045), (r, z0), (r - .012, z0 - .006), (r * .82, z0 + .028),
            (r * .42, z0 + (z1 - z0) * .45), (.0, z1 - .03)]
    with xf(T(0, 0, z0) @ RX(tilt[1]) @ RY(tilt[0]) @ T(0, 0, -z0)):
        h = lathe('Hat', prof, (0, 0, 0), P['hat'], seg=64, grain='z')
        # the weave runs on 'wuv' (u round the crown, v down the slope): without it the shader sees one flat point and the hat bakes plain
        set_attr_list(h, 'wuv', [(math.atan2(v.co.y, v.co.x) * .16, math.hypot(v.co.x, v.co.y) * 1.05, 0.) for v in h.data.vertices])
        # frayed brim: short straws sticking out of the weave all round, more where it is worn
        specs = []
        for k in range(150):
            t = R.uniform(0, math.tau); rr = r - R.uniform(.0, .03)
            b = Vector((rr * math.cos(t), rr * math.sin(t), z0 + .008))
            d = Vector((math.cos(t), math.sin(t), R.uniform(-.5, .15)))
            L = R.uniform(.025, .07) * (1.6 if math.cos(t - 2.3) > .7 else 1.)
            L = max(.012, min(L, (.215 - abs(b.y)) / max(abs(d.normalized().y), .05)))     # front and back: the piece is only 0.5 m deep
            specs.append((b, d, L, R.uniform(.005, .008), .15, R.random() * 1e6))
        strands('Hat_Fray', specs, P['straw_old'], nv=2, detail=1)
        cyl('Hat_Crown_Knot', (0, 0, z1 - .004), .022, .02, P['rope'], verts=10)


def frame(P, R, bar_tilt):
    log('Post', [(0, 0, -.0), (.004, -.003, .7), (0, 0, HEAD_TOP - .06)], .042, P['pole'], seg=10, lump=.06, seed=1, grain='z')
    with xf(T(0, 0, BAR_Z) @ RY(bar_tilt) @ T(0, 0, -BAR_Z)):
        log('Cross_Bar', [(-BAR_X, 0, BAR_Z), (0, .004, BAR_Z + .006), (BAR_X, 0, BAR_Z)], .033, P['pole'], seg=10, lump=.07, seed=2, grain='x')
        rope('Cross_Tie', [(-.05, -.05, BAR_Z + .05), (.05, -.05, BAR_Z - .05), (.05, .05, BAR_Z - .05), (-.05, .05, BAR_Z + .05), (-.05, -.05, BAR_Z + .05)],
             .008, P['rope'], ply=2, tw=90., seg=6)
        for sx in (-1, 1):       # wrist ties where the sleeve straw is bound to the bar
            x = sx * .40
            rope(f'Wrist_Tie_{sx}', [(x + .006 * math.sin(a), .045 * math.cos(a), BAR_Z + .045 * math.sin(a)) for a in [math.tau * q / 10 for q in range(11)]],
                 .008, P['rope'], ply=2, tw=90., seg=6)


def tunic_fn(u, v):
    """Torso surface: u round the body (0 = front middle), v from the collar (0) to the hem (1)."""
    z = (NECK_Z - .05) + (HEM_Z - NECK_Z + .05) * v
    # half-widths: narrow collar, broad shoulders, the sash pulls it in, flaring to the hem
    def prof(v):
        w = (NECK_Z - .05 - WAIST_Z) / (NECK_Z - .05 - HEM_Z)          # the sash line (v about 0.44)
        pts = [(0., .08, .07), (.1, .2, .125), (w - .08, .16, .115), (w, .14, .1), (w + .08, .17, .12), (1., .26, .18)]
        for (v0, a0, b0), (v1, a1, b1) in zip(pts, pts[1:]):
            if v <= v1:
                k = (v - v0) / (v1 - v0); return a0 + (a1 - a0) * k, b0 + (b1 - b0) * k
        return pts[-1][1:]
    a, b = prof(v); t = -math.pi / 2 + math.tau * u
    wob = 1 + .06 * noise.noise(Vector((math.cos(t) * 2, math.sin(t) * 2, v * 4))) * v
    fold = .02 * math.sin(t * 7 + v * 3) * v + .012 * math.sin(t * 13 + 1.3) * max(0., v - .55)
    # the sash gathers the cloth: tight little pleats just above and below it, dying away up and down
    w = (NECK_Z - .05 - WAIST_Z) / (NECK_Z - .05 - HEM_Z)
    fold += .009 * math.sin(t * 19 + 2.1 * noise.noise(Vector((t, 0., 3.)))) * math.exp(-((v - w) / .07) ** 2)
    # drag folds from the shoulders down towards the sash, and slack cloth sagging across the chest
    fold += .006 * math.sin(t * 5 - v * 6 + .7) * math.exp(-((v - .2) / .12) ** 2)
    fold += .004 * noise.noise(Vector((math.cos(t) * 6, math.sin(t) * 6, v * 14)))
    return (a * math.cos(t) * wob + fold * math.cos(t), b * math.sin(t) * wob + fold * math.sin(t), z)


def tunic(P, R):
    seed = R.random() * 100
    # torn hem: long ragged tongues hanging down between gaps up to 0.2 m deep. Each column of the cloth simply ends where its tear
    # is (the rows below .56 are squeezed into what is left), so the torn edge is a smooth jagged line, not a staircase of missing quads
    def hem_end(u):
        n = noise.noise(Vector((u * 11, seed, 0))) * .5 + .5 + .3 * noise.noise(Vector((u * 31, seed, 2)))
        return .56 + .44 * max(.04, min(1., n / 1.05))
    def torn(u, v):
        if v <= .56: return tunic_fn(u, v)
        return tunic_fn(u, .56 + (v - .56) / .44 * (hem_end(u % 1.) - .56))
    def keep(u, v):          # a hole or two higher up
        if .5 < v < .56 and abs(u - .3) < .025: return False
        if .25 < v < .3 and abs(u - .72) < .02: return False
        return True
    sheet('Tunic', 120, 36, torn, P['tunic'], solid=.004, keep=keep, grain='z')
    # the wrap-over collar: a darker band from the right of the neck across the chest to the left side above the sash
    def band(u, v):
        a, b = (.95 - .83 * v), (.03 + .4 * v)
        q = Vector(tunic_fn(a % 1., b + (u - .5) * .05)); n = Vector((q.x, q.y, 0)).normalized()
        return tuple(q + n * .006)
    sheet('Collar_Band', 2, 14, band, P['trim'], solid=.003, grain='z')
    # sleeves: from the shoulder out along the bar, hanging a little, flaring to a torn cuff
    for sx in (-1, 1):
        def sleeve(u, v, sx=sx):
            x = sx * (.12 + .27 * v); zc = BAR_Z - .03 - .02 * v; r = .085 + .035 * v
            t = math.tau * u; low = max(0., -math.sin(t))
            sag = (.04 + .1 * v) * low ** 1.5                                    # the empty sleeve hangs under the bar
            # crumpled where the sleeve is pushed along the bar: rings of folds that wander round, deeper underneath, plus a few long drag lines
            ring_f = .075 * math.sin(v * 24 + 1.8 * math.sin(t * 2 + sx) + 1.2 * noise.noise(Vector((u * 3, v * 5, sx * 4.)))) * (.4 + .6 * low)
            drag = .04 * math.sin(t * 5 + v * 2 + sx) * (1 - v) * low
            r *= 1 + ring_f + drag + .05 * noise.noise(Vector((math.cos(t) * 2, math.sin(t) * 2, v * 9 + sx * 3)))
            return (x + sx * .015 * low * v, r * math.cos(t) * .9, zc + r * math.sin(t) - sag)
        def cuff(u, v, sx=sx):           # the torn cuff, the same way: each column ends at its own tear
            if v <= .62: return sleeve(u, v)
            m = noise.noise(Vector((u * 9, seed + sx, 1))) * .5 + .5 + .25 * noise.noise(Vector((u * 23, seed + sx, 3)))
            return sleeve(u, .62 + (v - .62) / .38 * .38 * max(.05, min(1., m)))
        sheet(f'Sleeve_{sx}', 56, 30, cuff, P['tunic'], solid=.004, grain='x')
    # patches: small panels laid 4 mm over the cloth
    spots = [(.1, .3, .07, .09), (.62, .55, .06, .08), (.85, .25, .05, .06)][:len(P['patch'])]
    # (a cut-and-torn outline, a slight pucker where it is sewn down, a running stitch of thread round the edge: not a flat square)
    for i, (uc, vc, du, dv) in enumerate(spots):
        sd = 7.7 * (i + 1) + seed
        def pf(u, v, uc=uc, vc=vc, du=du, dv=dv, sd=sd, lift=.005):
            e = 1. + .18 * noise.noise(Vector((u * 4., v * 4., sd))) + .05 * noise.noise(Vector((u * 13., v * 13., sd + 3.)))
            uu = .5 + (u - .5) * e; vv = .5 + (v - .5) * e
            q = Vector(tunic_fn(uc - du + 2 * du * uu, vc - dv + 2 * dv * vv)); n = Vector((q.x, q.y, 0)).normalized()
            pucker = .0016 * noise.noise(Vector((u * 7., v * 7., sd + 9.))) + .0012 * math.sin(u * 3.1) * math.sin(v * 3.1)
            return tuple(q + n * (lift + pucker))
        sheet(f'Patch_{i}', 10, 10, pf, P['patch'][i], solid=.0015, grain='z')
        nst = 18
        for k in range(0, nst, 2):
            def ring(t, ins=.08):
                side = int(t * 4) % 4; f = t * 4 - int(t * 4)
                u, v = ((f, 0.), (1., f), (1 - f, 1.), (0., 1 - f))[side]
                return .5 + (u - .5) * (1 - ins), .5 + (v - .5) * (1 - ins)
            a_, b_ = Vector(pf(*ring(k / nst), lift=.0072)), Vector(pf(*ring((k + .7) / nst), lift=.0072))
            m_ = (a_ + b_) / 2; m_ += Vector((m_.x, m_.y, 0)).normalized() * .0008
            rope(f'Patch_Stitch_{i}', [tuple(a_), tuple(m_), tuple(b_)], .0013, P['rope'], ply=2, tw=60., seg=4, detail=1)
    # straw-rope sash with hanging ends
    a, b = .148, .108
    rope('Sash', [(a * math.cos(t), b * math.sin(t), WAIST_Z + .006 * math.sin(2 * t)) for t in [math.tau * q / 16 for q in range(17)]], .012, P['rope'], ply=3, tw=110., seg=7)
    for k, dx in enumerate((-.03, .02)):
        rope(f'Sash_End_{k}', [(dx + .05, -b + .01, WAIST_Z), (dx + .07, -b - .015, WAIST_Z - .12), (dx + .06 + k * .02, -b - .01, WAIST_Z - .24 - .04 * k)], .01, P['rope'], ply=3, tw=110., seg=7)


REACH = .575     # straw tips stop this far out along the bar (the bar ends at 0.55), so the leaning B still fits 1.2 m


def _cap(b, d, L):
    dx = abs(Vector(d).normalized().x)
    return max(.03, min(L, (REACH - abs(b[0])) / max(dx, .1)))


def straw_bursts(P, R):
    # out of the cuffs and along the bar to its ends, drooping
    for sx in (-1, 1):
        specs = []
        for d in _cone_dirs((sx, 0, -.1), 110, .55, R):
            b = (sx * R.uniform(.36, .42), R.uniform(-.035, .035), BAR_Z + R.uniform(-.04, .03))   # rooted round the bar, not loose in the cuff
            specs.append((b, d, _cap(b, d, R.uniform(.1, .2)), R.uniform(.006, .01), R.uniform(.3, .9), R.random() * 1e6))
        for _ in range(50):       # bundled along the bar between the cuff and the bar end
            b = (sx * R.uniform(.3, .4), R.uniform(-.035, .035), BAR_Z + R.uniform(-.035, .035))
            d = (sx, R.uniform(-.15, .15), R.uniform(-.1, .1))
            specs.append((b, d, _cap(b, d, R.uniform(.12, .2)), R.uniform(.006, .009), R.uniform(.1, .4), R.random() * 1e6))
        strands(f'Sleeve_Straw_{sx}', specs, P['straw'], nv=3)
    # the fringe under the tunic: hanging from the waist down past the hem, ragged
    specs = []
    for k in range(240):
        t = R.uniform(0, math.tau); rr = R.uniform(.96, 1.)        # rooted against the cloth just under the sash, which holds them
        b = (.142 * rr * math.cos(t), .102 * rr * math.sin(t), WAIST_Z - .02 - R.uniform(0, .04))
        d = (math.cos(t) * R.uniform(.05, .3), math.sin(t) * R.uniform(.05, .25), -1)
        specs.append((b, d, R.uniform(.36, .58), R.uniform(.006, .011), R.uniform(-.1, .15), R.random() * 1e6))
    strands('Skirt_Straw', specs, P['straw'], nv=4)
    # a few out of the two tears in the tunic
    specs = []
    for (u, v) in ((.3, .63), (.72, .275)):
        q = Vector(tunic_fn(u, v)); n = Vector((q.x, q.y, 0)).normalized()
        for d in _cone_dirs(n, 8, .6, R):
            specs.append((q - n * .03, d, R.uniform(.05, .09), .007, .3, R.random() * 1e6))
    strands('Tear_Straw', specs, P['straw_old'], nv=2, detail=1)


def ground(P, R):
    rope('Foot_Tie', [(.05 * math.cos(a), .05 * math.sin(a), .55 + .004 * math.sin(2 * a)) for a in [math.tau * q / 10 for q in range(11)]], .008, P['rope'], ply=2, tw=90., seg=6)
    for k in range(4):
        a = R.uniform(0, math.tau); FP.grass_tuft('Foot_Weed', (.08 * math.cos(a), .08 * math.sin(a), 0.), R.randint(8, 13), R.uniform(.1, .22), P['grass'], R, lean=.3, detail=1, spread=.03)
    for k in range(4):
        a = R.uniform(0, math.tau); FP.pebble('Foot_Pebble', (.09 * math.cos(a), .09 * math.sin(a), .0), R.uniform(.02, .035), P['pebble'], seed=k, flat=.5, detail=1, group='Main')


def build_for(kind):
    v = VARIANTS[kind]
    def build(P):
        R = random.Random(f'RI04{kind}')
        with xf(RY(v['lean'])):
            frame(P, R, v['bar_tilt'])
            with xf(T(0, 0, BAR_Z) @ RY(v['bar_tilt'] * .6) @ T(0, 0, -BAR_Z)):
                head(P, R); tunic(P, R); straw_bursts(P, R)
            hat(P, R, v['hat_tilt'])
        ground(P, R)
        S['collision_mesh'] = collision(v['lean'])
        S['part_notes'] = {'kind': kind, 'lean_deg': round(math.degrees(v['lean']), 1), 'bar_tilt_deg': round(math.degrees(v['bar_tilt']), 1),
                           'bar_z_m': BAR_Z, 'neck_z_m': NECK_Z, 'hat': {'radius': HAT[0], 'brim_z': HAT[1], 'apex_z': HAT[2]},
                           'straw': 'each straw a separate thin ribbon (one mesh per bundle): head, collar, sleeves and bar, the fringe under the tunic, pokes',
                           'no_face': True}
    return build


def collision(lean):
    V, F = [], []
    c, s = math.cos(lean), math.sin(lean)
    def lean_p(x, y, z): return (x * c + z * s, y, -x * s + z * c)
    def prism(x0, x1, y0, y1, z0, z1):
        FP.hull_loft(V, F, [[lean_p(x0, y0, z), lean_p(x1, y0, z), lean_p(x1, y1, z), lean_p(x0, y1, z)] for z in (z0, z1)])
    prism(-.06, .06, -.06, .06, 0., HEM_Z)                    # the post (and the straw fringe round it)
    prism(-.2, .2, -.14, .14, HEM_Z, NECK_Z + .2)              # the body, the head
    return V, F


def register(ASSETS):
    for kind, zh, ref, note in (('A', '稻草人（直立）', 'RI04/RI04-cand-4',
                                 '稻草人第一種（三視圖 RI04-cand-4）：木十字架、稻草紮的頭、舊斗笠、褪色破短褂（下襬和袖口撕破、三塊補丁）、草繩腰帶，袖口、橫木兩端、下襬下面、領口都冒出鬆散的稻草，輪廓蓬鬆不規則。沒有臉、不寫字。'),
                                ('B', '稻草人（歪的）', 'RI04/RI04-cand-2',
                                 '稻草人第二種（三視圖 RI04-cand-2）：和第一種同一套做法，整個往左歪約 7°、橫木再斜 5°，藍黑色舊短褂、兩塊補丁，斗笠歪戴。沒有臉、不寫字。')):
        ASSETS[f'RI04_Scarecrow_{kind}'] = dict(
            kind='scarecrow', zh=zh, palette=palette_for(kind), build=build_for(kind), tex=2048, ver='v001',
            atlases={'Main': ['Main', 'Detail_Small']}, limit=[W, D, H], box=((VARIANTS[kind]['box_x'][0], -D / 2, 0.), (VARIANTS[kind]['box_x'][1], D / 2, H)), slot='A6_RiceFields_Scarecrow',
            ref=ref, clamp_max=.03, uv_detach_zero=True, uv_shape='CONVEX', origin='foot of the post, bottom z = 0, front -Y',
            note=note + ' 碰撞：柱子和身體兩個方塊（人撞到會停，稻草本身不擋）。',
            method='procedural mesh construction (art/source/roadside-landmarks-b/ri_scarecrow.py: every straw a thin ribbon, torn cloth sheets, twisted rope); '
                   'procedural straw, cloth, weave, rope and wood shaders baked to one 1024 atlas (Main)',
            based_on='original (Blender procedural); material functions from art/source/village-houses-b')


def scarecrow_checks(aid, check, cfg):
    from vl_checks import _bvh
    body = _bvh([o for g, o in S['lods'][0].items() if not g.startswith('Detail_')])
    # a soft outline: count straw ribbons and how far the silhouette spreads beyond the cloth (sleeve straw past the cuff, fringe past the hem)
    side = lambda x, z: body((x, -3., z), (0, 1, 0))
    reach = max((abs(x) for x in [i * .01 for i in range(30, 61)] for sx in (-1, 1) if side(sx * x, BAR_Z - .02)), default=0.)
    low = min((z for z in [i * .01 for i in range(20, 80)] if body((0., -3., z), (0, 1, 0)) and z < HEM_Z - .05), default=None)
    check('straw_outline_spreads', reach > .48 and low is not None and low < HEM_Z - .15,
          {'straw_reach_from_post_x_m': round(reach, 2), 'cuff_x_m': .40, 'lowest_straw_or_cloth_seen_from_front_m': low, 'hem_z_m': HEM_Z})
    lean = VARIANTS[aid[-1]]['lean']; ax = math.sin(lean) * (HAT[2] - .03)       # B leans: look for the crown where it went
    top = body((ax, 0., 5.), (0, 0, -1))
    check('hat_on_top', top is not None and top[0].z > HAT[1] + .1 and top[0].z <= H, {'crown_x_m': round(ax, 3), 'top_m': round(top[0].z, 3) if top else None})
    return {'straw_reach_m': round(reach, 2), 'lowest_m': low}
