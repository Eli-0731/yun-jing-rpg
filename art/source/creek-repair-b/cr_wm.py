"""A3 West Creek: WM01 mill house, WM02 water wheel, WM04 millstones, WM05 washing steps, WM07 stone bridge, WM09 bamboo pavilion.
All minTier standard; no water surfaces (core team's material). Sizes from the work pack; bridge long axis is Y, front faces -Y."""
import math, random
from mathutils import Vector, noise
from ti_core import S, RX, RY, RZ, T, cyl, lathe, socket, sphere, surface, torus, xf
import ti_mats as tm
import mk_mats as mm
import cr_mats as cm
from cr_parts import rbox, rope, lash, xlash, pole, sheet, log, between, tuft


def worn(mat, drop):
    """Lower the roughness of a finished material by `drop`, through its output node."""
    mat.node_tree.nodes['OUT_ROUGH'].inputs[1].default_value = -drop
    return mat


def ferns(name, q, mat, seed, n=6, L=.2, **kw):
    R = random.Random(seed)
    for b in range(n):
        a = R.uniform(0, 6.28); base = Vector(q)
        sheet(name, 1, 5, lambda u, v, a=a, base=base: tuple(base + Vector((math.cos(a) * (v * L * .8 + (u - .5) * .03 * (1 - v)), math.sin(a) * (v * L * .8 + (u - .5) * .03 * (1 - v)), math.sin(v * 2.4) * L * .5))), mat, solid=.001, detail=2, grain='z', **kw)


def stone_set(name, n=3, **kw):
    """A few stones of one quarry, a little lighter, darker, warmer, so that a wall is not one flat colour."""
    light = kw.pop('light', (.33, .315, .27)); dark = kw.pop('dark', (.165, .155, .13))
    shade = [(1., 1., 1.), (.84, .84, .85), (1.1, 1.05, .96), (.93, .96, .98)]
    return [cm.stone(f'{name}_{i}', light=tuple(c * f for c, f in zip(light, shade[i])), dark=tuple(c * f for c, f in zip(dark, shade[i])), **kw) for i in range(n)]


def moss_patch(name, q, n, r, mat, seed=0, flat=1., **kw):
    """Moss grows in thin broken colonies along joints and corners, not as one cushion: a main lobe and a few strays, each hugging the face (n = its outward normal)."""
    n = Vector(n).normalized(); a = n.cross(Vector((0, 0, 1)) if abs(n.z) < .9 else Vector((1, 0, 0))).normalized(); b = n.cross(a); q = Vector(q)
    kw.setdefault('detail', 2); R = random.Random(seed * 13 + 5)
    for k in range(4):
        rk = r * (.66 if k == 0 else R.uniform(.24, .4)); off = 0 if k == 0 else r * R.uniform(.55, .85); turn = R.uniform(0, math.tau); s_ = seed + k * 3.7
        c = q + a * (math.cos(turn) * off * 1.3) + b * (math.sin(turn) * off * .8)
        def fn(u, v, c=c, rk=rk, s_=s_):
            t = u * math.tau; cx, cy = math.cos(t), math.sin(t)
            e = rk * v * (.72 + .75 * noise.noise(Vector((cx * 1.2 + s_, cy * 1.2, s_ * .3))) + .28 * noise.noise(Vector((cx * 3.4 + s_, cy * 3.4, s_))) + .05 * math.sin(t * 9 + s_))
            h = flat * (rk * .075 * (1 - v * v) ** .5 + rk * .025 * noise.noise(Vector((cx * v * 7, cy * v * 7, s_))))
            p = c + a * (cx * e * 1.3) + b * (cy * e * .8) + n * (h - rk * .018)
            return (p.x, p.y, max(p.z, .003))
        surface(name, 20 if k == 0 else 10, 4 if k == 0 else 2, fn, mat, closed_u=True, **{**kw, 'detail': kw['detail'] + (k > 0)})


# ------------------------------------------------------------------ WM02 water wheel
R_TIP, R_RIM, W = 2.3, 2.03, 1.2


def wheel_palette():
    P = {'oak': cm.wood('Wet_Oak', (.03, .02, .012), (.13, .082, .045), ground_h=0, grey=.28), 'paddle': cm.wood('Paddle_Oak', (.035, .023, .014), (.15, .095, .05), ground_h=0, grey=.3)}
    P['algae'] = cm.wood('Paddle_Algae', (.026, .034, .018), (.085, .105, .05), ground_h=0, grey=.15); P['new'] = cm.wood('Paddle_New', (.12, .075, .036), (.34, .22, .11), ground_h=0, grey=.03)
    P['iron'] = mm.cast_iron('Band_Iron'); P['hemp'] = mm.hemp('Hemp_Rope', (.09, .06, .032), twist=40.0); P['axle'] = cm.wood('Axle_Oak', (.05, .03, .016), (.17, .1, .052), ground_h=0, polish=.25, grey=.1)
    return P


def wm02(P):
    # axle along X: a true round, 64 sides, turned ends
    cyl('Axle', (0, 0, 0), .15, W, P['axle'], axis='x', verts=64, bevel=.006, grain='x')
    for sx in (-1, 1):
        x = sx * .42
        # hub flange and its iron
        cyl('Hub', (x, 0, 0), .34, .2, P['oak'], axis='x', verts=48, bevel=.012, grain='z')
        with xf(T(x, 0, 0) @ RY(math.pi / 2)):
            torus('Hub_Band', (0, 0, -.09), .335, .012, P['iron'], major=48, minor=8, grain='z')
            torus('Hub_Band', (0, 0, .09), .335, .012, P['iron'], major=48, minor=8, grain='z')
        # sixteen felloes make the rim, slightly stepped and hewn; eight spokes
        for i in range(16):
            a = i / 16 * math.tau + math.pi / 16
            r = R_RIM; L = 2 * r * math.tan(math.pi / 16) + .03
            rbox('Felloe', (x, -math.sin(a) * r, math.cos(a) * r), (.11, L, .26), P['oak'], r=.012, amp=.002, seed=i + int(sx * 3 + 3), div=.1, rot=(a, 0, 0), grain='y')
            bolt = a + math.pi / 16
            cyl('Rim_Bolt', (x + sx * .05, -math.sin(bolt) * r, math.cos(bolt) * r), .017, .02, P['iron'], axis='x', verts=10, bevel=.003, detail=1, grain='x')
        for i in range(4):
            a = i / 4 * math.tau + math.pi / 16 * 0
            rbox('Rim_Strap', (x + sx * .056, -math.sin(a) * R_RIM, math.cos(a) * R_RIM), (.008, .3, .27), P['iron'], r=.003, div=.1, rot=(a, 0, 0), detail=1)
        for i in range(16):
            a = i / 16 * math.tau
            L = R_RIM - .3; c = .3 + L / 2 - .02
            rbox('Spoke', (x, -math.sin(a) * c, math.cos(a) * c), (.085, .1, L), P['oak'], r=.01, amp=.002, seed=i * 3, div=.12, rot=(a, 0, 0), grain='z')
            # a rope X where the spoke meets the rim
            q = Vector((x + sx * .062, -math.sin(a) * (R_RIM - .03), math.cos(a) * (R_RIM - .03))); tg = Vector((0, -math.cos(a), -math.sin(a))); rd = Vector((0, -math.sin(a), math.cos(a)))
            for d in (tg + rd, tg - rd):
                for off in (-.012, .012):
                    o_ = q + tg * off
                    rope('Joint_X', [tuple(o_ - d * .085), tuple(o_ + d * .085)], .0075, P['hemp'], ply=1, tw=0., seg=5, amp=0., detail=1)
    # sixteen paddles between the rims, one new, the bottom of the wheel greened
    for i in range(16):
        a = i / 16 * math.tau
        down = math.cos(a) < -.35
        mat = P['new'] if i == 0 else P['algae'] if down else P['paddle']
        r = (R_TIP + 1.84) / 2
        for j, (off, h) in enumerate(((-.122, .216), (.113, .234))):
            rm = r + off
            rbox('Paddle', (0, -math.sin(a) * rm, math.cos(a) * rm), (.86, .05, h), mat, r=.008, amp=.003, freq=8., seed=i * 2 + j, div=.1, rot=(a, 0, 0), grain='x')
        # the floor of the bucket, running to the next paddle, and its two cheeks
        b = a + math.pi / 16; rf = R_RIM - .045; Lf = 2 * rf * math.tan(math.pi / 16) * .98
        rbox('Paddle_Floor', (0, -math.sin(b) * rf, math.cos(b) * rf), (.86, Lf, .04), mat, r=.006, amp=.003, seed=i + 70, div=.12, rot=(b, 0, 0), grain='y')
        for sx in (-1, 1):
            rbox('Paddle_Cheek', (sx * .44, -math.sin(a) * (R_TIP + 1.98) / 2, math.cos(a) * (R_TIP + 1.98) / 2), (.03, .1, R_TIP - 1.98), P['oak'], r=.005, seed=i + sx, div=.1, rot=(a, 0, 0), grain='z')
    # round about the axle, so it stays on the wheel whatever angle the game turns it to
    ring = [(sx * .5, math.sin(k / 24 * math.tau) * 2.3, math.cos(k / 24 * math.tau) * 2.3) for sx in (-1, 1) for k in range(24)]
    S['collision_mesh'] = (ring, [(k, (k + 1) % 24, 24 + (k + 1) % 24, 24 + k) for k in range(24)] + [tuple(range(23, -1, -1)), tuple(range(24, 48))])
    S['collision'] = []


# ------------------------------------------------------------------ WM04 millstones and sacks
def mills_palette():
    P = {'stone': cm.stone('Millstone', light=(.27, .255, .215), dark=(.12, .11, .09), moss=.45, crack=.4, lichen=.25), 'stone2': cm.stone('Millstone_Plain', light=(.25, .235, .195), dark=(.11, .1, .08), moss=.7, crack=.5, lichen=.35), 'old': cm.stone('Base_Stone', light=(.3, .28, .23), dark=(.13, .12, .095), moss=1.0, crack=.7, lichen=.4), 'crack': tm.plain('Stone_Crack', (.02, .018, .016), rough=.9, noise=.1)}
    P['sack'] = mm.cloth('Hemp_Sack', (.135, .095, .052), dirt=1., weave_=380.0)
    P['hemp'] = mm.hemp('Sack_Tie', (.2, .125, .055), twist=40.0); P['wood'] = cm.wood('Scoop_Wood', (.09, .055, .028), (.27, .17, .09), ground_h=0, polish=.2, grey=.1); P['flour_dust'] = tm.plain('Flour_Dust', (.4, .37, .3), rough=.95, noise=.3)
    P['moss'] = cm.moss_tuft('Moss_Soft', soft=True)
    return P


def millstone(name, R, thick, mat, seed, grooved=True, **kw):
    """Disc on its axis Z, centred; curved furrows cut into the +Z face of a dressed stone, a rough-picked face on a plain one; hacked rim.
    One surface from the eye across the face, round the rim, across the back and through the eye, so the normals agree."""
    def fn(u, v):
        a = u * math.tau; ca, sa = math.cos(a), math.sin(a)
        if v < .62:      # face
            t = v / .62; r = R * (.14 + .86 * t); dep = 0.
            if grooved and .1 < t < .95:
                sec = (a + seed) % (math.tau / 8) / (math.tau / 8)     # one harp of eight: furrows parallel to its master, each cut with a steep and a slanted wall
                off = r * math.sin(sec * math.tau / 8) + .012 * noise.noise(Vector((ca * 3, sa * 3, r * 4)))
                saw = (off / .052) % 1.
                dep = .022 * (saw / .22 if saw < .22 else max(0., 1 - (saw - .22) / .3)) * min(1., (t - .1) / .1) * min(1., (.95 - t) / .05)
            wear = noise.fractal(Vector((ca * r * 5, sa * r * 5, seed)), 1., 2., 3) * (.006 if grooved else .022)
            drop = thick * .05 * (t - .9) / .1 if t > .9 else 0
            return (ca * r, sa * r, thick / 2 - dep + wear - drop)
        if v < .76:      # rim
            t = (v - .62) / .14; hack = noise.fractal(Vector((ca * 4 + seed, sa * 4, t * 2.2)), 1., 2., 3) * .009
            return (ca * (R + hack), sa * (R + hack), (.5 - t) * thick * .98)
        if v < .9:       # back
            t = (v - .76) / .14; r = R * (1 - .86 * t)
            return (ca * r, sa * r, -thick / 2 - .001)
        t = (v - .9) / .1  # eye
        return (ca * R * .14, sa * R * .14, (t - .5) * thick)
    surface(name, 176 if grooved else 72, 50, fn, mat, closed_u=True, grain='z', **kw)


def sack(P, name, c, s, seed, mat, yaw=0., **kw):
    """A filled hemp sack: squarish, slumped belly, gathered neck tied with rope, a ragged mouth above the tie."""
    ca, sa = math.cos(yaw), math.sin(yaw)
    keys = [(0., 0.), (.012, .72), (.05, 1.02), (.26, 1.1), (.56, 1.), (.76, .76), (.87, .4), (.9, .24), (.93, .23), (.96, .3), (1., .33)]
    def prof(h):
        for (h0, r0), (h1, r1) in zip(keys, keys[1:]):
            if h <= h1:
                t = (h - h0) / (h1 - h0); t = t * t * (3 - 2 * t)
                return r0 + (r1 - r0) * t
        return keys[-1][1]
    def fn(u, v):
        a = u * math.tau; sq = (abs(math.cos(a)) ** 3.4 + abs(math.sin(a)) ** 3.4) ** (-1 / 3.4)         # squarish below, round at the neck
        sq = 1 + (sq - 1) * max(0., 1 - v / .72)
        fold = max(0., (v - .28) / .56) ** 1.4 * (1 - max(0., (v - .84) / .16) * .5)
        wrinkle = (math.sin(a * 7 + seed + 2.2 * noise.noise(Vector((math.cos(a), math.sin(a), seed)))) * .085 + math.sin(a * 13 + seed * 2) * .04) * fold
        wrinkle += .018 * math.sin(v * 26 + 3 * noise.noise(Vector((math.cos(a) * 1.6, math.sin(a) * 1.6, seed)))) * max(0., 1 - abs(v - .16) / .16) + .02 * noise.noise(Vector((math.cos(a) * 5 + seed, math.sin(a) * 5, v * 9)))
        lump = noise.noise(Vector((math.cos(a) * 1.4 + seed, math.sin(a) * 1.4, v * 2.4))) * .17 * (1 - fold) + .07 * math.sin(a + seed) * (1 - v)
        rag = noise.noise(Vector((math.cos(a) * 2, math.sin(a) * 2, seed))) * .012 * max(0., (v - .9) / .1)
        r = prof(v) * sq * (1 + wrinkle + lump)
        x, y = math.cos(a) * s[0] * r + s[0] * .34 * math.cos(seed) * v * v, math.sin(a) * s[1] * r + s[1] * .34 * math.sin(seed) * v * v
        return (c[0] + x * ca - y * sa, c[1] + x * sa + y * ca, c[2] + (v + rag) * s[2])
    surface(name, 44, 26, fn, mat, closed_u=True, grain='z', **kw)
    # the inside of the mouth, dark
    surface(name + '_Mouth', 18, 3, lambda u, v: (c[0] + math.cos(u * math.tau) * s[0] * .31 * (1 - v), c[1] + math.sin(u * math.tau) * s[1] * .31 * (1 - v), c[2] + s[2] * (.97 - .1 * v)), mat, closed_u=True, grain='z', **kw)
    rr = .24 * min(s[0], s[1])
    for z in (.885, .905):
        rope(name + '_Tie', [(c[0] + math.cos(t) * rr * 1.04, c[1] + math.sin(t) * rr * 1.04, c[2] + s[2] * z) for t in [k / 12 * math.tau for k in range(13)]], .009, P['hemp'], curve=2, detail=1, **kw)


def wm04(P):
    # a low mossy base stone, and on it two old stones leaning head to head
    def base(u, v):
        a = u * math.tau; r = .42 * v ** .6 * (1 + .08 * math.sin(a * 3 + 1) + .05 * math.sin(a * 7))
        return (.3 + math.cos(a) * r, .02 + math.sin(a) * r * .9, .13 * (1 - v ** 6) + noise.fractal(Vector((math.cos(a) * r * 6, math.sin(a) * r * 6, 3.)), 1., 2., 3) * .02 * (1 - v ** 6))
    surface('Base_Stone', 48, 12, base, P['old'], closed_u=True, grain='z')
    with xf(T(.3, -.22, .445) @ RX(math.pi / 2 - .34)):
        millstone('Stone_A', .46, .17, P['stone'], 1.)
        # the crack: from the eye out to the rim on two sides
        for j, (a0, wig) in enumerate(((1.45, .05),)):
            def crack(u, v, a0=a0, wig=wig, j=j):
                r = .46 * (.58 + .42 * v); a = a0 + wig * math.sin(v * 9 + j) + (u - .5) * .005 * v
                return (math.cos(a) * r, math.sin(a) * r, .17 / 2 + .002)
            sheet('Stone_Crack', 1, 16, crack, P['crack'], solid=.004, detail=1)
    with xf(T(.3, .24, .41) @ RX(-(math.pi / 2 - .36))):
        millstone('Stone_B', .42, .15, P['stone2'], 2., grooved=False)
    for k, (q, n, r) in enumerate((((.0, -.3, .2), (-.6, -.75, .3), .09), ((.56, -.32, .12), (.5, -.8, .3), .08), ((.3, -.05, .135), (0, 0, 1), .15), ((.62, .1, .125), (.4, 0, 1), .1), ((-.02, .15, .12), (-.4, 0, 1), .09), ((.05, .3, .22), (-.7, .55, .3), .08))):
        moss_patch('Moss', q, n, r, P['moss'], seed=k + 1)
    sack(P, 'Sack_1', (-.52, .22, 0), (.27, .22, .84), 3., P['sack'], yaw=.2)
    sack(P, 'Sack_2', (-.36, -.2, 0), (.25, .2, .66), 7., P['sack'], yaw=-.3)
    with xf(T(-.74, -.34, .135) @ RZ(-.75) @ RX(-1.5)):
        sack(P, 'Sack_3', (0, 0, -.18), (.15, .13, .5), 11., P['sack'])
    # the wooden scoop: an open-fronted tray, narrowing to a short handle
    with xf(T(-.1, -.55, 0) @ RZ(.35)):
        def tray(u, v):
            w = .15 - .075 * v; a = (u - .5) * 2; h = .1 * (.45 + .55 * v)
            return (a * w, -.17 + v * .34, abs(a) ** 2.6 * h + .012)
        surface('Scoop_Tray', 18, 12, tray, P['wood'], solid=.012, grain='y')
        rbox('Scoop_Back', (0, .172, .06), (.15, .022, .1), P['wood'], r=.006, seed=2, div=.05, grain='x')
        log('Scoop_Handle', [(0, .18, .08), (0, .29, .09)], .018, P['wood'], seg=9, lump=.02, grain='y')
        surface('Scoop_Flour', 12, 6, lambda u, v: (math.cos(u * math.tau) * v * .1 * (.8 + .4 * noise.noise(Vector((math.cos(u * math.tau) * 2, math.sin(u * math.tau) * 2, 1.)))), -.03 + math.sin(u * math.tau) * v * .11, .018 + .034 * (1 - v * v) ** 1.5), P['flour_dust'], closed_u=True, grain='z', group='Detail_Flour')
    Rp = random.Random(4)
    for k in range(8):
        a = Rp.uniform(0, 6.28); r = Rp.uniform(.62, .72)
        q = Rp.uniform(.6, 1.1); rbox('Pebble', (.3 + math.cos(a) * r * 1., -.05 + math.sin(a) * r * .75, .026 * q), (.08 * q, .06 * q, .052 * q), P['old'], r=.024 * q, amp=.012, chips=1, seed=k, div=.018, rot=(0, 0, a), detail=1)
    S['collision'] = [((-.2, -.52, 0), (.78, .55, .85)), ((-1., -.4, 0), (-.2, .46, .7))]


# ------------------------------------------------------------------ WM05 washing steps
def steps_palette():
    P = {'stone': stone_set('Step_Granite', 4, light=(.235, .205, .155), dark=(.1, .085, .062), wet_z=.45, moss=1., lichen=.35, crack=.55), 'wall': stone_set('Cheek_Rubble', 4, light=(.26, .235, .185), dark=(.11, .095, .075), wet_z=.35, moss=.9, lichen=.4, crack=.6)}
    P['low'] = worn(cm.stone('Step_Lowest_Worn', light=(.27, .245, .2), dark=(.12, .11, .085), moss=.1, lichen=0, crack=.2, wet_z=.5), .32)
    P['scrub'] = worn(cm.stone('Scrub_Stone', light=(.26, .24, .205), moss=0, lichen=0, crack=.2), .12); P['wood'] = cm.wood('Tie_Post', (.05, .03, .016), (.18, .11, .058), wet_z=.45, ground_h=.1, polish=.2, grey=.35)
    P['hemp'] = mm.hemp('Hemp_Rope', (.18, .11, .05), twist=40.0); P['moss'] = cm.moss_tuft('Moss_Soft', soft=True); P['fern'] = cm.fern('Fern_Green')
    return P


def wm05(P):
    R = random.Random(505); W, RISE = 5.04, .22
    y0 = -1.46; TR = .73
    for s in range(4):
        z0 = 0; z1 = RISE * (s + 1); yf = y0 + s * TR; depth = 2.92 - s * TR
        # rear of the block runs under the steps above, only its front and top show
        x = -W / 2; i = 0
        while x < W / 2 - .05:
            w = min(R.uniform(.72, 1.25), W / 2 - x)
            if W / 2 - x - w < .35: w = W / 2 - x
            mat = P['low'] if s == 0 else P['stone'][R.randrange(4)]
            dy, dz = R.uniform(-.018, .018), R.uniform(-.014, .004)
            rbox('Step_Block', (x + w / 2, yf + depth / 2 + dy, (z0 + z1) / 2 + dz / 2), (w - .008, depth, z1 - z0 + dz), mat, r=.045 if s == 0 else .03, amp=.008 if s == 0 else .012, freq=3.5, chips=0 if s == 0 else 1, hew=0, seed=s * 20 + i, div=.12)
            x += w; i += 1
    # masonry walls either side, stepping down toward the water
    for sx in (-1, 1):
        for row in range(5):
            # the top course stops short of the tie post on the right wall
            zb = row * .225; y = (y0, y0 + .5, y0 + 1., y0 + 1., y0 + 1.7)[row]; n = 0; end = .62 if row == 4 and sx > 0 else 1.46
            while y < end - .01:
                L = min(R.uniform(.42, .72), end - y)
                if end - y - L < .2: L = end - y
                rbox('Cheek', (sx * 2.74, y + L / 2, zb + .112), (.46, L - .008, .218), P['wall'][R.randrange(4)], r=.035, amp=.034, freq=5., chips=4, hew=3, seed=R.randint(1, 900), div=.09)
                y += L; n += 1
        def wall_top(y): return .225 if y < y0 + .5 else .45 if y < y0 + 1. else .9 if y < y0 + 1.7 or (sx > 0 and y > .62) else 1.125
        for k, y in enumerate((y0 + .3, y0 + .9, y0 + 1.4, y0 + 1.6 if sx < 0 else y0 + 2.3)):   # none on the top course: it would break the 1.2 m limit
            z = wall_top(y) + .01
            ferns('Wall_Fern', (sx * (2.5 if k % 2 else 2.72), y, z), P['fern'], k + sx + 7, n=9, L=.28)
        for k, y in enumerate((y0 + .8, y0 + 1.3, y0 + 2.1)):
            moss_patch('Moss', (sx * 2.74, y, wall_top(y) - .002), (0, 0, 1), .19, P['moss'], seed=k + sx + 12, flat=.5)
    # flat scrubbing stones: one big one on the second step, a small one and a block on the first, tilted a little toward the water
    rbox('Scrub_Stone', (-.8, y0 + TR * 1.45, RISE * 2 + .055), (1.0, .56, .11), P['scrub'], r=.05, amp=.012, freq=4., seed=1, div=.05, rot=(-.05, 0, .05))
    rbox('Scrub_Stone', (1.55, y0 + TR * .45, RISE + .04), (.42, .3, .08), P['scrub'], r=.035, amp=.008, seed=2, div=.04, rot=(-.05, 0, -.2))
    rbox('Scrub_Stone', (1.98, y0 + TR * .35, RISE + .025), (.2, .14, .05), P['scrub'], r=.012, amp=.004, seed=3, div=.03)
    # a post for tying baskets on top of the right wall, with the rope still on it
    log('Tie_Post', [(2.76, .95, .88), (2.77, .94, 1.03), (2.76, .95, 1.165)], .065, P['wood'], seg=12, lump=.05, seed=5, grain='z')
    lash('Post_Rope', (2.76, .95, 1.0), (0, 0, 1), .067, .09, .009, P['hemp'], detail=1)
    rope('Post_Tail', [(2.82, .94, .97), (2.86, .85, .92), (2.84, .72, .9)], .007, P['hemp'], curve=6, detail=1)
    # moss along the waterline: the bottom two risers and the wet corners
    for k in range(11):
        x = R.uniform(-2.45, 2.45); st = k % 2
        moss_patch('Moss', (x, y0 + st * TR - .012, R.uniform(.02, .1) + st * RISE), (0, -1, .15), R.uniform(.05, .09), P['moss'], seed=k + 1, flat=.3)
    for sx in (-1, 1):
        moss_patch('Moss', (sx * 2.4, y0 + .3, RISE + .012), (0, 0, 1), .09, P['moss'], seed=sx + 30, flat=.3)
        moss_patch('Moss', (sx * 2.38, y0 + TR + .1, 2 * RISE + .012), (0, 0, 1), .07, P['moss'], seed=sx + 40, flat=.3)
    S['collision'] = [((-2.52, y0 + s * TR, 0), (2.52, 1.46, RISE * (s + 1))) for s in range(4)] + [((sx * 2.76 - .24, y0, 0), (sx * 2.76 + .24, 1.46, .9)) for sx in (-1, 1)] + [((-3., y0 + 1.7, .9), (-2.52, 1.46, 1.125)), ((2.52, y0 + 1.7, .9), (3., .62, 1.125))]


# ------------------------------------------------------------------ WM07 stone bridge
ZC, SLOPE, SPAN, RISE_, SPRING = 3.2, .245, 6.0, 2.2, .3
HALF = 1.2                        # half of the 2.4 m deck


def deck_z(y):
    """Rounded crown, straight 13.8 deg ramps. Never over 15 deg."""
    a = abs(y); b = 1.6
    return ZC - (a * a * SLOPE / (2 * b) if a < b else (SLOPE * b / 2 + (a - b) * SLOPE))


def arch_z(y):
    """Segmental arch between y = +-3: rise 2.2 above the springing."""
    R_ = (9 + RISE_ * RISE_) / (2 * RISE_)
    if abs(y) >= 3: return 0.
    return SPRING + RISE_ - R_ + math.sqrt(R_ * R_ - y * y)


def bridge_palette():
    P = {'stones': stone_set('Bridge_Granite', 4, light=(.27, .24, .185), dark=(.12, .105, .08), wet_z=.9, moss=.85, lichen=.45, crack=.45), 'deck': worn(cm.stone('Deck_Worn', light=(.235, .208, .16), dark=(.115, .1, .075), moss=.12, lichen=.05, crack=.25), .16)}
    P['rail'] = cm.stone('Rail_Granite', light=(.24, .215, .165), dark=(.11, .098, .075), moss=.7, lichen=.5, crack=.4); P['stone'] = P['stones'][0]; P['moss'] = cm.moss_tuft('Moss_Soft', soft=True); P['fern'] = cm.fern('Fern_Green')
    return P


def wall_courses(P, x, th):
    R = random.Random(int(x * 100) + 707); course = .34; z = 0.; row = 0
    while z < ZC + .2:
        y = -6.0 + (row % 2) * .32 - .32 * (row % 2)
        first = True
        while y < 6.0:
            L = R.uniform(.62, 1.05); L = min(L, 6.0 - y)
            if 6.0 - y - L < .25: L = 6.0 - y
            y0, y1 = y, y + L; c = (y0 + y1) / 2
            bottom = max(z, 0.); top = z + course
            samples = [y0 + (y1 - y0) * k / 6 for k in range(7)]
            high = max(deck_z(v) - .02 for v in samples); low = min(arch_z(v) if abs(v) < 3 else 0. for v in samples)
            if bottom < high and top > low:
                def warp(q, c=c, zc=(bottom + top) / 2):
                    wy = c + q.y; wz = zc + q.z
                    wz = min(wz, deck_z(wy) - .015)
                    if abs(wy) < 3: wz = max(wz, arch_z(wy))
                    q.z = wz - zc
                rbox('Wall_Block', (x, c, (bottom + top) / 2), (th, L - .005, course - .004), P['stones'][R.randrange(4)], r=.02, amp=.006, freq=5., chips=1, seed=int(y * 13) + row * 7, div=.16, warp=warp)
            y += L; first = False
        z += course; row += 1


def wm07(P):
    for sx in (-1, 1):
        wall_courses(P, sx * 1.37, .34)
    # arch ring proud of the wall, voussoirs radial
    R_ = (9 + RISE_ * RISE_) / (2 * RISE_); cz = SPRING + RISE_ - R_; half = math.asin(3 / R_); N = 21
    for sx in (-1, 1):
        for i in range(N):
            a = -half + (i + .5) / N * 2 * half; depth = .52 + (.05 if i % 2 else 0)
            rm = R_ + depth / 2; c = (0, math.sin(a) * rm, cz + math.cos(a) * rm)
            th = 2 * R_ * math.sin(half / N) + .004
            rbox('Voussoir', (sx * 1.38, c[1], c[2]), (.42, th, depth), P['stone'], r=.012, amp=.003, chips=1, hew=3, seed=i + (0 if sx > 0 else 40), div=.12, rot=(-a, 0, 0), grain='z')
    # barrel under the arch, one smooth vault
    surface('Barrel', 6, 42, lambda u, v: ((.5 - u) * 2.4, math.sin(-half + v * 2 * half) * R_, cz + math.cos(-half + v * 2 * half) * R_ + .004), P['stone'], grain='y', solid=.06)
    # road ends: solid fill under the deck and a retaining face, then low rubble wings
    for sy in (-1, 1):
        ymid = sy * 4.6
        def fill(q, c=ymid):
            q.z = min(q.z, deck_z(c + q.y) - .08 - 1.65) if False else q.z
        for row, z0 in enumerate(k * .305 for k in range(6)):
            x = -1.2
            while x < 1.19:
                w = min(random.Random(row * 9 + int(x * 20) + sy).uniform(.5, .85), 1.2 - x)
                if 1.2 - x - w < .25: w = 1.2 - x
                rbox('End_Face', (x + w / 2, sy * 5.92, z0 + .152), (w - .006, .16, .3), P['stones'][int(abs(x * 7 + row)) % 4], r=.02, amp=.006, freq=5., chips=1, seed=row * 7 + int(x * 11), div=.08)
                x += w
        for sx in (-1, 1):
            for row, (y0, y1, z0) in enumerate(((4.3, 6., 0.), (4.8, 6., .34), (5.3, 6., .68))):
                y = y0; n = 0
                while y < y1 - .05:
                    L = min(random.Random(row * 13 + n + sx).uniform(.45, .75), y1 - y)
                    if y1 - y - L < .2: L = y1 - y
                    rbox('Wing', (sx * 1.74, sy * (y + L / 2), z0 + .17), (.3, L - .006, .335), P['stones'][(row + n) % 4], r=.05, amp=.018, freq=3.5, chips=1, seed=row * 5 + n + int(sy * 2 + sx + 5), div=.08)
                    y += L; n += 1
    rbox('Fill_Core', (0, -4.42, .9), (2.4, 2.84, 1.8), P['stones'][1], r=.01, div=.5)
    rbox('Fill_Core', (0, 4.42, .9), (2.4, 2.84, 1.8), P['stones'][1], r=.01, div=.5)
    # walking surface: slabs across, worn smooth, following the crown
    y = -6.0; i = 0; R = random.Random(77)
    while y < 6.0:
        L = R.uniform(.5, .78); L = min(L, 6.0 - y); c = y + L / 2
        hw = HALF + .03
        def warp(q, c=c):
            wy = c + q.y
            q.z += deck_z(wy) - deck_z(c)
        rbox('Deck_Slab', (0, c, deck_z(c) - .05), (2 * hw, L - .006, .1), P['deck'], r=.014, amp=.003, freq=4., seed=i, div=.14, warp=warp, grain='x')
        y += L; i += 1
    # rails, kept to z <= 3.95: posts, a top rail following the slope, panels with plain cloud relief
    posts = [-5.6 + 1.4 * k for k in range(9)]
    for sx in (-1, 1):
        for k, y in enumerate(posts):
            z = deck_z(y)
            rbox('Rail_Post', (sx * 1.34, y, z + .33), (.17, .17, .66), P['rail'], r=.016, amp=.003, chips=1, seed=k, div=.1, grain='z')
            rbox('Post_Cap', (sx * 1.34, y, z + .68), (.22, .22, .05), P['rail'], r=.012, amp=.003, seed=k, div=.08)
            rbox('Post_Cap', (sx * 1.34, y, z + .725), (.15, .15, .04), P['rail'], r=.018, amp=.003, seed=k + 3, div=.06)
        for k in range(len(posts) - 1):
            y0, y1 = posts[k], posts[k + 1]; c = (y0 + y1) / 2; L = y1 - y0 - .16
            zc = (deck_z(y0) + deck_z(y1)) / 2
            def warp(q, c=c, zc=zc):
                q.z += deck_z(c + q.y) - zc
            rbox('Rail_Panel', (sx * 1.34, c, zc + .24), (.09, L, .38), P['rail'], r=.008, amp=.002, seed=k + 9, div=.16, warp=warp)
            rbox('Rail_Top', (sx * 1.34, c, zc + .535), (.12, L + .02, .07), P['rail'], r=.016, amp=.002, seed=k + 19, div=.16, warp=warp)
            # cloud relief: three overlapping low discs and a tail, no letters
            for side in (-1, 1):
                x = sx * 1.34 + side * .046
                for j, (dy, dz, r) in enumerate(((-.2, 0, .075), (0, .03, .095), (.2, 0, .075), (.36, -.035, .045), (-.36, -.035, .045))):
                    yy = c + dy
                    cyl('Cloud', (x, yy, deck_z(yy) + .235 + dz), r, .014, P['rail'], axis='x', verts=18, bevel=.004, detail=1, grain='z')
    # ferns in the joints and moss at the waterline, only where there is wall behind them
    R = random.Random(9); placed = 0
    while placed < 40:
        sx = 1 if placed % 2 else -1; y = R.uniform(-5.6, 5.6); z = R.uniform(.2, deck_z(y) - .25)
        if z <= arch_z(y) + .1 or abs(abs(y) - 3.2) < .4: continue
        ferns('Fern', (sx * 1.545, y, z), P['fern'], placed, n=7, L=.3); placed += 1
    placed = 0
    while placed < 16:
        sx = 1 if placed % 2 else -1; y = R.uniform(-5.9, 5.9); z = R.uniform(.05, .55)
        if z <= arch_z(y) + .04 or 4.3 < abs(y): continue
        moss_patch('Moss', (sx * 1.54, y, z), (sx, 0, .1), R.uniform(.12, .22), P['moss'], seed=placed + 1); placed += 1
    # collision: walkable sloped deck plus rail walls and the piers
    ys = [-6 + k * .5 for k in range(25)]; verts, faces = [], []
    for y in ys:
        z = deck_z(y)
        verts += [(-1.25, y, z), (1.25, y, z), (1.25, y, z + .7), (-1.25, y, z + .7), (-1.25, y, z - .35), (1.25, y, z - .35)]
    for i in range(len(ys) - 1):
        a, b = i * 6, (i + 1) * 6
        faces += [(a, a + 1, b + 1, b), (a + 1, a + 2, b + 2, b + 1), (a + 3, a, b, b + 3), (a + 4, b + 4, b + 5, a + 5), (a + 5, b + 5, b + 1, a + 1), (a + 4, a, b, b + 4)]
    S['collision_mesh'] = (verts, faces)
    S['collision'] = [((-1.6, -6, 0), (1.6, -3, 1.6)), ((-1.6, 3, 0), (1.6, 6, 1.6))]
    socket('Socket_RoadEnd_Front', (0, -6, deck_z(6))); socket('Socket_RoadEnd_Rear', (0, 6, deck_z(6)))


# ------------------------------------------------------------------ WM09 pavilion
CR_, EAVE_R, PZ = 1.3, 1.56, 2.3


def pav_palette():
    P = {'culm': cm.culm('Sunbleached_Post', green=(.1, .1, .04), straw=(.3, .24, .11), mud_h=.3), 'beam': cm.culm('Bamboo_Beam', green=(.08, .09, .035), straw=(.27, .21, .095), mud_h=0)}
    P['thatch'] = cm.thatch('Thatch'); P['patch'] = cm.thatch('Thatch_Patch', dark=(.12, .09, .05), light=(.42, .34, .18)); P['roll'] = cm.thatch('Thatch_Roll', dark=(.05, .04, .024), light=(.2, .16, .09))
    P['stones'] = stone_set('Plinth_Round', 3, light=(.26, .248, .21), dark=(.125, .118, .098), moss=.8, lichen=.4, crack=.4); P['stone'] = P['stones'][0]; P['table'] = worn(cm.stone('Table_Stone', light=(.33, .3, .25), moss=.2, lichen=.15, crack=.25), .12)
    P['hemp'] = mm.hemp('Hemp_Old', (.1, .075, .04), twist=40.0); P['hemp_new'] = mm.hemp('Hemp_New', (.24, .17, .085), twist=40.0); P['moss'] = cm.moss_tuft('Peak_Moss', soft=True); P['leaf'] = cm.wood('Fallen_Leaf', (.12, .09, .03), (.3, .24, .08), ground_h=0, grey=0)
    return P


def hex_r(a, base):
    """Radius of a hexagon with corners at a = k * 60 deg + 30 deg."""
    s = (a - math.radians(30)) % (math.pi / 3) - math.pi / 6
    return base * math.cos(math.pi / 6) / math.cos(s)


def wm09(P):
    corners = [(math.cos(math.radians(30 + 60 * k)), math.sin(math.radians(30 + 60 * k))) for k in range(6)]
    # low round plinth with a step
    lathe('Plinth', [(0, .02), (1.5, .02), (1.56, .17), (1.53, .185), (0, .185)], (0, 0, 0), P['stone'], seg=48)
    # broken flagstones over it: rough wedges in two rings
    Rf = random.Random(55)
    for ring, (r0, r1, n) in enumerate(((.0, .78, 7), (.78, 1.52, 13))):
        for k in range(n):
            a0, a1 = (k + Rf.uniform(.02, .06)) / n * math.tau, (k + 1 - Rf.uniform(.02, .06)) / n * math.tau; ri0, ri1 = r0 + .012, r1 - .012 + Rf.uniform(-.03, 0); h = Rf.uniform(.004, .012)
            surface('Flagstone', 5, 3, lambda u, v, a0=a0, a1=a1, ri0=ri0, ri1=ri1, h=h: ((ri0 + (ri1 - ri0) * v) * math.cos(a0 + (a1 - a0) * u), (ri0 + (ri1 - ri0) * v) * math.sin(a0 + (a1 - a0) * u), .19 + h), P['stones'][k % 3], grain='z', solid=.012)
    for k in range(20):
        a = k / 20 * math.tau + .08
        rbox('Curb', (math.cos(a) * 1.6, math.sin(a) * 1.6, .1), (.24, .5, .2), P['stones'][k % 3], r=.04, amp=.01, freq=4., seed=k, div=.22, rot=(0, 0, a))
    for k, c in enumerate(corners):
        tx, ty = -c[1] * .055, c[0] * .055
        for j, sd in enumerate((-1, 1)):
            pole('Post', (c[0] * CR_ + sd * tx, c[1] * CR_ + sd * ty, .2), (c[0] * CR_ + sd * tx, c[1] * CR_ + sd * ty, PZ + .1), .05, .044, P['culm'], node_gap=.42, bend=.008, seed=k * 2 + j, cut=0., seg=10)
        lash('Post_Band', (c[0] * CR_, c[1] * CR_, .3), (0, 0, 1), .112, .08, .0085, P['hemp'], detail=1, turns=4)
        lash('Post_Band', (c[0] * CR_, c[1] * CR_, .86), (0, 0, 1), .112, .08, .0085, P['hemp'], detail=1, turns=4)
    for k in range(6):
        a, b = corners[k], corners[(k + 1) % 6]
        pole('Ring_Beam', (a[0] * CR_ * 1.06, a[1] * CR_ * 1.06, PZ), (b[0] * CR_ * 1.06, b[1] * CR_ * 1.06, PZ), .042, .04, P['beam'], node_gap=.4, seed=k + 20, seg=12)
        lash('Beam_Lash', (a[0] * CR_, a[1] * CR_, PZ - .01), (0, 0, 1), .112, .12, .0075, P['hemp_new'] if k == 2 else P['hemp'], detail=1, turns=6 if k != 2 else 8)
        if k == 4: continue    # the entrance
        A = Vector((a[0] * CR_, a[1] * CR_, 0)); B = Vector((b[0] * CR_, b[1] * CR_, 0))
        for z, r in ((.82, .03), (.5, .024)):
            pole('Rail', (A.x, A.y, z), (B.x, B.y, z), r, r, P['beam'], node_gap=.36, seed=k + int(z * 10), seg=10)
        for j in range(1, 7):
            q = A.lerp(B, j / 7)
            pole('Baluster', (q.x, q.y, .2), (q.x, q.y, .82), .014, .013, P['beam'], node_gap=.3, seed=j + k * 9, seg=8, detail=1)
    # rafters run up to the peak
    apex = 3.62
    for k, c in enumerate(corners):
        rope('Rafter', [(c[0] * 1.5, c[1] * 1.5, PZ + .1), (c[0] * .9, c[1] * .9, PZ + .46), (c[0] * .15, c[1] * .15, 3.5)], .036, P['beam'], ply=1, tw=0., seg=10, amp=.02, curve=6, step=.08, grain=(0, 0, 1))
    # the thatch: concave and deep, laid in four tiers so the slope steps and the eave is thick; corners a little raised
    def thatch(a, s, lift=0., shrink=1., seed=4.):
        r = hex_r(a, EAVE_R * shrink) * (1 - s) ** .9
        corner = abs(((a - math.radians(30)) % (math.pi / 3) - math.pi / 6)) / (math.pi / 6)
        sweep = (1 - corner) ** 2 * .2 * (1 - s) ** 3
        z = PZ + .12 + (3.72 - PZ - .12) * (max(0., s) ** 1.45) * (1 + .12 * math.sin(s * math.pi)) + sweep + lift
        z += noise.fractal(Vector((math.cos(a) * 2.2 + seed, math.sin(a) * 2.2, s * 4)), 1., 2., 3) * .022
        return Vector((math.cos(a) * r, math.sin(a) * r, z))
    tiers = ((0., .36), (.2, .58), (.42, .8), (.64, 1.))
    for ti, (s0, s1) in enumerate(tiers):
        def fn(u, v, s0=s0, s1=s1, ti=ti):
            a = u * math.tau
            rag = (noise.noise(Vector((math.cos(a) * 18, math.sin(a) * 18, ti * 3.))) * .012 + math.sin(a * 110 + ti) * .0025) * (1 - v) ** 3
            s = s0 + (s1 - s0) * v - rag
            bulge = math.sin(v * math.pi) * .018 + (1 - v) ** 4 * .03
            return tuple(thatch(a, s, lift=bulge + (3 - ti) * .0))
        surface('Thatch_Tier', 168 if ti == 0 else 120, 10, fn, P['thatch'], closed_u=True, grain='z')
    # the underside and the closing edge, so that the eave has thickness seen from below
    surface('Thatch_Under', 96, 6, lambda u, v: tuple(thatch(u * math.tau, v * .55, lift=-.11, shrink=.965, seed=9.)), P['thatch'], closed_u=True, grain='z', solid=.012)
    def skirt(u, v):
        a = u * math.tau
        rag = noise.noise(Vector((math.cos(a) * 18, math.sin(a) * 18, 0.))) * .012 + math.sin(a * 110) * .0025
        return tuple(thatch(a, -rag + .002).lerp(thatch(a, .01, lift=-.11, shrink=.965, seed=9.), v))
    surface('Thatch_Eave', 168, 2, lambda u, v: skirt(1 - u, v), P['thatch'], closed_u=True, grain='z', solid=.012)
    # a patched section of newer straw
    def patch(u, v):
        return tuple(thatch(.1 * math.tau + u * .66, .2 + v * .17, lift=.024 + .012 * math.sin(u * math.pi) * math.sin(v * math.pi)))
    surface('Thatch_Patch', 22, 14, patch, P['patch'], grain='z')
    # a bamboo frame tied over the patch
    pf = lambda u, v: tuple(thatch(.1 * math.tau + u * .66, .2 + v * .17, lift=.05))
    for j, ((a0, b0), (a1, b1)) in enumerate((((0, 0), (1, 0)), ((0, 1), (1, 1)), ((0, 0), (0, 1)), ((1, 0), (1, 1)))):
        log('Patch_Frame', [pf(a0, b0), pf((a0 + a1) / 2, (b0 + b1) / 2), pf(a1, b1)], .012, P['beam'], seg=7, lump=.01, seed=j, grain='z')
    # shaggy straw: strands hang over every tier's edge
    Rs = random.Random(21)
    for s0, nst, L0 in ((.0, 340, .26), (.2, 220, .2), (.42, 160, .17), (.64, 100, .14)):
        for k in range(nst):
            a = k / nst * math.tau + Rs.uniform(-.01, .01); q = thatch(a, s0 + .012, lift=.02); L = L0 * Rs.uniform(.6, 1.25); w = Rs.uniform(.018, .034); out = Vector((math.cos(a), math.sin(a), 0)); side = Vector((-math.sin(a), math.cos(a), 0)); droop = Rs.uniform(.72, 1.)
            sheet('Straw', 1, 2, lambda u, v, q=q, L=L, w=w, out=out, side=side, droop=droop: tuple(q + side * ((u - .5) * w * (1 - v * .7)) + out * (v * L * .55 + .01) + Vector((0, 0, -v * v * L * droop))), P['thatch'], solid=None, grain='z', group='Detail_Straw', detail=1)
    # the six hips: stout bamboo lying on the roof, running past the eave and lifting at the tip, with an open cut end
    for k in range(6):
        a = math.radians(30 + 60 * k); ca, sa = math.cos(a), math.sin(a)
        pts = [tuple(thatch(a, s, lift=.045)) for s in (.04, .2, .4, .6, .8, .93)]
        e0 = thatch(a, .0, lift=.05)
        pts = list(reversed(pts)) + [(e0.x + ca * .1, e0.y + sa * .1, e0.z + .012), (ca * 1.74, sa * 1.74, e0.z + .1)]
        pts = list(reversed(pts))[::-1]
        pole_pts = [Vector(q) for q in pts]
        rope('Hip_Bamboo', pts, .034, P['beam'], ply=1, tw=0., seg=10, amp=.004, curve=8, step=.07, grain=(0, 0, 1))
        torus('Hip_Cut', pts[-1], .03, .007, P['beam'], rot=(math.pi / 2 - .35, 0, math.pi / 2 + a), major=12, minor=5, detail=1)
        rope('Hip_Hollow', [pts[-1], tuple(Vector(pts[-1]) + Vector((-ca * .012, -sa * .012, -.006)))], .024, P['roll'], ply=1, tw=0., seg=8, amp=0., detail=1)
        for s_ in (.14, .44, .74):
            q = thatch(a, s_, lift=.045)
            lash('Hip_Tie', tuple(q), tuple((thatch(a, s_ + .02, lift=.045) - q).normalized()), .04, .04, .007, P['hemp'], detail=1, turns=3)
        q = thatch(a, .03, lift=.05)
        lash('Eave_Tie', tuple(q), (ca, sa, .12), .048, .1, .008, P['hemp'], detail=1, turns=6)
    # the tied peak: cut bamboo ends standing out of a bundle, vines creeping down from it
    for k in range(5):
        a = k / 5 * math.tau; q0 = (math.cos(a) * .035, math.sin(a) * .035, 3.68); q1 = (math.cos(a) * .05, math.sin(a) * .05, 3.97 - k % 2 * .025)
        pole('Peak_Bamboo', q0, q1, .02, .019, P['beam'], node_gap=.2, seed=k, seg=9, cut=0.)
    lash('Peak_Tie', (0, 0, 3.78), (0, 0, 1), .082, .11, .009, P['hemp'], turns=7, detail=1)
    Rv = random.Random(6)
    for k in range(70):
        a = Rv.uniform(0, 6.28); sv = Rv.uniform(.66, .97) if k > 30 else Rv.uniform(.82, .97); q = thatch(a, sv, lift=.05); yaw = Rv.uniform(0, 6.28); L = Rv.uniform(.07, .13)
        sheet('Vine_Leaf', 2, 4, lambda u, v, q=q, yaw=yaw, L=L: tuple(q + Vector((math.cos(yaw) * (v - .2) * L - math.sin(yaw) * (u - .5) * L * .6 * math.sin(v * 3.14), math.sin(yaw) * (v - .2) * L + math.cos(yaw) * (u - .5) * L * .6 * math.sin(v * 3.14), .015 * math.sin(v * 3.14)))), P['moss'], solid=.001, grain='z', group='Detail_Vines', detail=1)
    # round stone table and four stools
    lathe('Table', [(0, .2), (.24, .2), (.23, .3), (.2, .4), (.22, .58), (.24, .64), (.5, .66), (.53, .69), (.53, .755), (.5, .785), (0, .785)], (0, 0, 0), P['table'], seg=40)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        lathe('Stool', [(0, .2), (.15, .2), (.155, .3), (.15, .47), (.14, .51), (.12, .525), (0, .525)], (math.cos(a) * .78, math.sin(a) * .78, 0), P['table'], seg=20)
    # fallen bamboo leaves
    R = random.Random(9)
    for k in range(34):
        a = R.uniform(0, 6.28); r = R.uniform(.5, 1.6); q = Vector((math.cos(a) * r, math.sin(a) * r, .222 if r < 1.5 else .205)); yaw = R.uniform(0, 6.28); L = R.uniform(.06, .1)
        sheet('Leaf', 1, 4, lambda u, v, q=q, yaw=yaw, L=L: tuple(q + Vector((math.cos(yaw) * (v - .5) * L - math.sin(yaw) * (u - .5) * .018 * math.sin(v * 3.14), math.sin(yaw) * (v - .5) * L + math.cos(yaw) * (u - .5) * .018 * math.sin(v * 3.14), .001))), P['leaf'], solid=.0008, detail=2)
    S['collision'] = [((c[0] * CR_ - .07, c[1] * CR_ - .07, 0), (c[0] * CR_ + .07, c[1] * CR_ + .07, PZ)) for c in corners] + [((-.5, -.5, 0), (.5, .5, .78))]


# ------------------------------------------------------------------ WM01 mill house
BX, BY, PLINTH = 3.1, 2.0, .85    # wall half width and depth, plinth top
FLOOR2, EAVE_Z_, RIDGE_Z_ = 3.0, 4.2, 5.58
EHX, EHY = 3.8, 2.72               # eave half extents
TERR = -2.86                       # front of the stone terrace
PY, PZ_HI, PZ_LO = .62, 3.16, 2.72 # the pent eave: reach, height at the wall, height at its edge


def mill_palette():
    P = {'plinths': stone_set('Plinth_Granite', 4, light=(.3, .28, .225), dark=(.13, .12, .095), wet_z=.65, moss=1., lichen=.4, crack=.55), 'timber': cm.wood('Frame_Timber', (.05, .03, .016), (.18, .105, .055), ground_h=0, grey=.28), 'plank': cm.wood('Wall_Plank', (.07, .043, .023), (.23, .14, .075), ground_h=0, grey=.34)}
    P['plaster'] = cm.lime_plaster('Lime_Plaster'); P['paper'] = cm.paper('Window_Paper', base=(.62, .55, .4), age=.25); P['tile'] = cm.tile('Roof_Tile'); P['tile_new'] = cm.tile('Roof_Tile_New', base=(.1, .12, .14), light=(.2, .22, .24), moss=0)
    P['ridge'] = cm.tile('Ridge_Tile', base=(.028, .038, .05), light=(.07, .088, .1), moss=1.3); P['deck'] = cm.wood('Roof_Deck', (.05, .045, .04), (.13, .115, .1), ground_h=0, grey=.1); P['dark'] = tm.plain('Interior_Dark', (.07, .056, .042), rough=.9, noise=.15); P['floor'] = cm.wood('Floor_Boards', (.045, .028, .016), (.13, .08, .045), ground_h=0, grey=.1)
    P['mill'] = cm.stone('House_Millstone', light=(.46, .43, .36), dark=(.24, .22, .18), moss=0, lichen=0, crack=.3); P['sack'] = mm.cloth('Grain_Sack', (.27, .21, .12), dirt=.45); P['hemp'] = mm.hemp('Sack_Tie', (.2, .125, .055), twist=40.0); P['iron'] = mm.cast_iron('Door_Iron'); P['flour'] = tm.plain('Flour_Dust', (.7, .67, .59), rough=.95, noise=.12); P['moss'] = cm.moss_tuft('Moss_Soft', soft=True)
    return P


def roof_z_(y, x=0.):
    s = min(1., abs(y) / EHY)
    z = RIDGE_Z_ - (RIDGE_Z_ - EAVE_Z_) * (.5 * s + .5 * (1 - (1 - s) ** 2.4))     # steep at the ridge, swept out at the eave
    fx = max(0., (abs(x) - (EHX - 1.1)) / 1.1)
    return z + .42 * fx * fx * s


def mill_tiles(P):
    pitch = .29; n = int((2 * EHX - .1) / pitch); x0 = -pitch * (n - 1) / 2; courses = 4
    for ys in (-1, 1):
        for ci in range(n):
            x = x0 + ci * pitch
            for cover in (0, 1):
                xc = x + (pitch / 2 if cover else 0)
                if cover and ci == n - 1: continue
                w = pitch * (.3 if cover else .6)
                newer = ys < 0 and xc > EHX - 1.5 and True
                for k in range(courses):
                    s0 = .03 + k * .97 / courses - (.03 if k else 0); s1 = .03 + (k + 1) * .97 / courses
                    def fn(u, v, xc=xc, w=w, s0=s0, s1=s1, cover=cover, k=k, ys=ys):
                        s = s0 + (s1 - s0) * v; y = ys * s * EHY; a = (u - .5) * math.pi
                        return (xc + math.sin(a) * w, y, roof_z_(y, xc) + math.cos(a) * w * (.82 if cover else -.2) + (.02 if cover else 0.) + .012 * (1 - v) + .003 * k + .012)
                    sheet('Tile', 4, 2, fn, P['tile_new'] if newer else P['tile'], solid=.016, grain='y')
                if cover:
                    y = ys * EHY * .995
                    cyl('Tile_Cap', (xc, y, roof_z_(y, xc) + .05), w * .78, .018, P['ridge'], axis='y', verts=14, detail=1, grain='z', bevel=.002)
    for sx in (-1, 1):
        for ys in (-1, 1):
            pts = [(sx * (EHX - .05), ys * s * EHY, roof_z_(ys * s * EHY, sx * (EHX - .05)) + .07) for s in (0., .3, .6, .85, .98)]
            rope('Verge_Roll', pts, .04, P['ridge'], ply=1, tw=0., amp=.02, seg=12, step=.06, grain='y')
    rbox('Ridge_Core', (0, 0, RIDGE_Z_ + .02), (2 * EHX - .3, .15, .1), P['ridge'], r=.03, amp=.006, freq=4., seed=41, div=.08)
    rbox('Ridge_Cap', (0, 0, RIDGE_Z_ + .085), (2 * EHX - .42, .09, .03), P['ridge'], r=.012, amp=.003, seed=42, div=.08)
    for sx in (-1, 1):
        # the ridge turns up at each end
        for ys in (-1, 1):
            horn(P, sx * (EHX - .02), ys * (EHY - .02), roof_z_(EHY, EHX) + .05, sx, ys, .3)
        rope('Ridge_Curl', [(sx * (EHX - .95), 0, RIDGE_Z_ + .1), (sx * (EHX - .55), 0, RIDGE_Z_ + .13), (sx * (EHX - .28), 0, RIDGE_Z_ + .2), (sx * (EHX - .14), 0, RIDGE_Z_ + .31)], .055, P['ridge'], ply=1, tw=0., amp=.006, curve=8, step=.05, grain='x')
    # the deck under the tiles so nothing shows through
    def under(u, v, ys=1):
        y = (v - .5) * 2 * EHY; x = (u - .5) * 2 * (EHX - .02)
        return (x, y, roof_z_(y, x) - .02)
    surface('Roof_Deck', 32, 28, under, P['deck'], grain='y', solid=.03)
    for sx in (-1, 1):
        for ys in (-1, 1):
            for k in range(3):
                t = (k + 1) * .25
                moss_y = ys * t * EHY
                moss_patch('Moss_Roof', (sx * (1.2 + k * .8), moss_y, roof_z_(moss_y, sx * (1.2 + k * .8)) + .1), (0, ys * .4, 1), .13, P['moss'], seed=k + int(sx + ys + 7))


def wm01(P):
    R = random.Random(101)
    # plinth in courses, rising straight from the water's edge
    course = .29; z = 0.; row = 0; YC = (TERR + BY + .1) / 2; YL = BY + .1 - TERR
    while z < PLINTH - .01:
        for (cx, cy, L, along) in ((0, TERR, 2 * BX + .3, 'x'), (0, BY + .1, 2 * BX + .3, 'x'), (-BX - .1, YC, YL, 'y'), (BX + .1, YC, YL, 'y')):
            u = -L / 2 + (row % 2) * .22
            if row % 2:
                pass
            while u < L / 2 - .02:
                w = R.uniform(.5, .95); w = min(w, L / 2 - u)
                if L / 2 - u - w < .25: w = L / 2 - u
                c = u + w / 2
                pos = (cx + (c if along == 'x' else 0), cy + (c if along == 'y' else 0), z + course / 2)
                size = (w - .006, .36, course - .004) if along == 'x' else (.36, w - .006, course - .004)
                # the stairs cut through the front of the terrace
                if not (along == 'x' and cy < 0 and abs(pos[0]) < 1.25):
                    rbox('Plinth_Block', pos, size, P['plinths'][R.randrange(4)], r=.028, amp=.016, freq=5., chips=3, hew=2, seed=R.randint(1, 900), div=.14)
                u += w
            if row % 2:     # the course closes at the corner
                rbox('Plinth_Block', (cx + (-L / 2 + .11 if along == 'x' else 0), cy + (-L / 2 + .11 if along == 'y' else 0), z + course / 2), (.21, .36, course - .004) if along == 'x' else (.36, .21, course - .004), P['plinths'][row % 4], r=.028, amp=.012, chips=2, seed=row + 90, div=.1) if not (along == 'x' and cy < 0 and False) else None
        z += course; row += 1
    rbox('Plinth_Core', (0, (TERR + BY) / 2, PLINTH / 2 - .06), (2 * BX + .1, YL - .2, PLINTH - .12), P['dark'], r=.002, div=.6) if False else None
    rbox('Floor', (0, 0, PLINTH - .05), (2 * BX + .1, 2 * BY + .1, .1), P['floor'], r=.004, seed=3, div=.2)
    # the terrace: paved either side of the stairs
    for sx in (-1, 1):
        x0, x1 = sx * 1.25, sx * (BX + .12)
        y = TERR + .1; k = 0
        while y < -BY - .02:
            L = min(.46, -BY - y)
            xx = min(x0, x1)
            while xx < max(x0, x1) - .02:
                w = min(R.uniform(.42, .7), max(x0, x1) - xx)
                rbox('Terrace_Slab', (xx + w / 2, y + L / 2, PLINTH - .05), (w - .008, L - .008, .1), P['plinths'][R.randrange(4)], r=.012, amp=.004, chips=1, seed=R.randint(1, 900), div=.12)
                xx += w
            y += L; k += 1
        rbox('Terrace_Face', (sx * 1.25, (TERR + -BY) / 2, PLINTH / 2 - .02), (.06, -BY - TERR, PLINTH - .06), P['plinths'][1], r=.01, amp=.006, chips=1, seed=sx + 8, div=.14)
    rbox('Plinth_Back', (0, BY - .06, PLINTH / 2), (2 * BX + .1, .1, PLINTH), P['plinths'][2], r=.008, div=.5) if False else None
    NS = 4; TR = (-BY - .02 - TERR) / NS
    for k in range(NS):
        z1 = (k + 1) * PLINTH / NS
        rbox('Door_Step', (0, TERR + k * TR + (-BY - .02 - (TERR + k * TR)) / 2, z1 / 2), (2.42, -BY - .02 - (TERR + k * TR), z1), P['plinths'][k], r=.025, amp=.008, chips=1, seed=k + 50, div=.14)
    # frame: posts at every bay
    bays_x = [-BX, -BX / 3, BX / 3, BX]; bays_y = [-BY, 0, BY]
    for x in bays_x:
        for y in (-BY, BY):
            rbox('Post', (x, y, (PLINTH + EAVE_Z_) / 2), (.2, .2, EAVE_Z_ - PLINTH), P['timber'], r=.012, amp=.003, seed=int(x * 3 + y), div=.2, grain='z')
    for x in (-BX, BX):
        rbox('Post', (x, 0, (PLINTH + RIDGE_Z_ - .22) / 2), (.2, .2, RIDGE_Z_ - .22 - PLINTH), P['timber'], r=.012, amp=.003, seed=int(x + 17), div=.2, grain='z')
    for z, h in ((PLINTH + .08, .16), (FLOOR2 + .18, .2), (EAVE_Z_ - .08, .18)):
        for y in (-BY, BY):
            rbox('Beam', (0, y, z), (2 * BX + .34, .17, h), P['timber'], r=.012, amp=.003, seed=int(z * 7 + y), div=.25, grain='x')
        for x in (-BX, BX):
            rbox('Beam', (x, 0, z), (.17, 2 * BY + .34, h), P['timber'], r=.012, amp=.003, seed=int(z * 5 + x), div=.25, grain='y')
    # brackets carry the eave
    for x in bays_x:
        for ys in (-1, 1):
            for k, (dy, dz, L) in enumerate(((.18, -.2, .3), (.34, -.09, .34), (.5, .02, .34))):
                rbox('Bracket', (x, ys * (BY + dy), EAVE_Z_ + dz), (.12, L, .11), P['timber'], r=.01, seed=k, div=.1, grain='y')
    for ys in (-1, 1):
        rbox('Eave_Purlin', (0, ys * (BY + .6), roof_z_(BY + .6) - .13), (2 * EHX - .55, .12, .13), P['timber'], r=.012, amp=.003, seed=5, div=.25, grain='x')
    pent_roof(P)
    # lower walls: lime plaster with a door and windows left open
    def plaster(name, x0, x1, y, z0, z1):
        def fn(u, v):
            n = noise.noise(Vector((u * 9, v * 9, y))) * .006
            return (x0 + (x1 - x0) * u, y + n, z0 + (z1 - z0) * v)
        sheet(name, max(2, int((x1 - x0) * 4)), max(2, int((z1 - z0) * 4)), fn, P['plaster'], solid=.05, grain='z')
    def plaster_y(name, y0, y1, x, z0, z1, flip=False):
        def fn(u, v):
            n = noise.noise(Vector((u * 9, v * 9, x))) * .006
            return (x + n, y0 + (y1 - y0) * (1 - u if flip else u), z0 + (z1 - z0) * v)
        sheet(name, max(2, int((y1 - y0) * 4)), max(2, int((z1 - z0) * 4)), fn, P['plaster'], solid=.05, grain='z')
    z0, z1 = PLINTH + .05, FLOOR2 + .1
    # front: door in the middle, one window a bay either side
    plaster('Wall_Front', -BX, -2.25, -BY, z0, z1); plaster('Wall_Front', 2.25, BX, -BY, z0, z1); plaster('Wall_Front', -1.0 - .15, -1.0, -BY, z0, z1); plaster('Wall_Front', 1.0, 1.15, -BY, z0, z1)
    for sx in (-1, 1):
        a, b = (-2.25, -1.15) if sx < 0 else (1.15, 2.25)
        plaster('Wall_Front', a, b, -BY, z0, z0 + .75); plaster('Wall_Front', a, b, -BY, z1 - .35, z1)
        window(P, (a + b) / 2, -BY, z0 + 1.2, b - a - .08, .92, 'x')
        if sx < 0: awning(P, (a + b) / 2, -BY, z0 + 1.72, b - a + .1, -1)
    plaster('Wall_Front', -1.0, 1.0, -BY, 2.45, z1)
    plaster('Wall_Back', -BX, BX, BY, z0, z1)
    for x in (-1.75, 1.75):
        window(P, x, BY + .04, z0 + 1.1, .68, .68, 'x', dark=True)
    # side walls; +X has the wheel-axle opening
    plaster_y('Wall_West', -BY, BY, -BX, z0, z1)
    AZ = 1.75
    plaster_y('Wall_East', -BY, -.42, BX, z0, z1); plaster_y('Wall_East', .42, BY, BX, z0, z1); plaster_y('Wall_East', -.42, .42, BX, z0, AZ - .42); plaster_y('Wall_East', -.42, .42, BX, AZ + .42, z1)
    for k in range(18):
        a = k / 18 * math.tau; rr = .5
        rbox('Port_Stone', (BX + .04, math.cos(a) * rr, AZ + math.sin(a) * rr), (.14, .17, .21), P['plinths'][k % 4], r=.016, amp=.008, chips=1, seed=k, div=.06, rot=(a, 0, 0))
    cyl('Port_Dark', (BX - .1, 0, AZ), .42, .04, P['dark'], axis='x', verts=24, grain='x')
    socket('Socket_WheelAxle', (BX + .08, 0, AZ))
    # upper walls: vertical planks
    for (ys, y) in ((-1, -BY), (1, BY)):
        x = -BX
        while x < BX - .03:
            w = R.uniform(.2, .3); w = min(w, BX - x)
            if True:
                rbox('Plank', (x + w / 2, y, (FLOOR2 + .1 + EAVE_Z_) / 2), (w - .008, .035, EAVE_Z_ - FLOOR2 - .2), P['plank'], r=.004, amp=.002, seed=R.randint(1, 900), div=.25, grain='z')
            x += w
    for x, w, aw in ((-1.9, .95, True), (.35, .85, False), (1.75, .7, False)):
        window(P, x, -BY - .02, FLOOR2 + .62, w, .62, 'x')
        if aw: awning(P, x, -BY - .02, FLOOR2 + 1.02, w + .2, -1)
    for x, w, aw in ((-1.9, .68, False), (0, .68, False), (1.9, .82, True)):
        window(P, x, BY + .06, FLOOR2 + .62, w, .62, 'x', dark=True)
        if aw: awning(P, x, BY + .03, FLOOR2 + 1.02, w + .2, 1)
    for x in (-BX, BX):
        y = -BY
        while y < BY - .03:
            w = R.uniform(.2, .3); w = min(w, BY - y)
            top = roof_z_(y + w / 2) - .15
            rbox('Plank_Gable', (x, y + w / 2, (FLOOR2 + top) / 2), (.035, w - .008, top - FLOOR2), P['plank'], r=.004, amp=.002, seed=R.randint(1, 900), div=.25, grain='z')
            y += w
        # the gable truss shows on the face
        sxx = 1 if x > 0 else -1; fx = x + sxx * .04
        rbox('Gable_Tie', (fx, 0, EAVE_Z_ + .05), (.08, 2 * BY + .2, .12), P['timber'], r=.01, amp=.003, seed=31, div=.2, grain='y')
        for sy in (-1, 1):
            between('Gable_Strut', (fx, sy * .05, RIDGE_Z_ - .35), (fx, sy * (BY - .1), EAVE_Z_ + .08), .07, .09, P['timber'], r=.01, amp=.003, seed=sy + 33, div=.2)
            between('Gable_Brace', (fx, sy * .05, EAVE_Z_ + .1), (fx, sy * .95, roof_z_(.95) - .17), .06, .07, P['timber'], r=.008, amp=.003, seed=sy + 35, div=.15)
    # doors: wide leaves standing open, flour on the frame
    for sx in (-1, 1):
        rbox('Door_Post', (sx * 1.07, -BY - .01, (z0 + 2.5) / 2), (.15, .17, 2.5 - z0), P['timber'], r=.012, amp=.003, seed=sx + 9, div=.2, grain='z')
        with xf(T(sx * 1.0, -BY + .02, z0) @ RZ(sx * 1.2)):
            for j in range(4):
                rbox('Door_Plank', (sx * (.11 + j * .235), 0, .78), (.228, .05, 1.53), P['plank'], r=.005, amp=.002, seed=j + sx + 5, div=.2, grain='z')
            for h in (.3, 1.25):
                rbox('Door_Band', (sx * .47, -.03, h), (.86, .012, .05), P['iron'], r=.003, div=.2, detail=1)
    rbox('Door_Lintel', (0, -BY - .01, 2.5), (2.35, .19, .16), P['timber'], r=.012, amp=.003, seed=4, div=.2, grain='x')
    # inside: dark room, upper ceiling, the millstones you can see from the door, nothing else
    rbox('Ceiling', (0, 0, FLOOR2 - .1), (2 * BX, 2 * BY, .06), P['dark'], r=.001, div=.5)
    for x, sy in ((-BX + .08, 0), (BX - .08, 0)):
        pass
    rbox('Back_Liner', (0, BY - .06, 1.9), (2 * BX - .1, .02, 2.1), P['dark'], r=.001, div=.5)
    MY = -.75
    lathe('Mill_Bed', [(0, 0), (.72, 0), (.76, .05), (.76, .38), (.7, .42), (0, .42)], (0, MY, PLINTH), P['mill'], seg=36)
    lathe('Mill_Upper', [(0, .42), (.6, .42), (.64, .46), (.64, .64), (.58, .68), (.2, .68), (.17, .65), (.1, .65), (0, .65)], (0, MY, PLINTH), P['mill'], seg=36)
    log('Mill_Shaft', [(0, MY, PLINTH + .64), (0, MY, 2.62)], .06, P['timber'], seg=12, lump=.02, grain='z')
    rbox('Mill_Beam', (0, MY + .55, 2.2), (2.3, .16, .18), P['timber'], r=.012, amp=.003, seed=61, div=.2, grain='x')
    rbox('Mill_Arm', (0, MY + .28, 2.15), (.14, .6, .12), P['timber'], r=.01, amp=.003, seed=62, div=.15, grain='y')
    for sx in (-1, 1):
        rbox('Mill_Frame', (sx * 1.0, MY + .55, (PLINTH + 2.2) / 2), (.15, .15, 2.2 - PLINTH), P['timber'], r=.012, amp=.003, seed=sx + 63, div=.2, grain='z')
    # a rush lamp and a hanging basket at the door post
    rope('Lamp_Cord', [(1.3, -BY - .22, 2.72), (1.3, -BY - .22, 2.42)], .005, P['hemp'], ply=1, tw=0., seg=4, amp=0., detail=1)
    lathe('Lamp', [(0, 0), (.06, 0), (.09, .08), (.08, .2), (.03, .26), (0, .26)], (1.3, -BY - .22, 2.16), P['paper'], seg=14, detail=1)
    # sacks stacked under the front eave
    for k, (x, y, z_, s) in enumerate(((2.25, -2.42, PLINTH, 1.), (2.78, -2.4, PLINTH, .95), (2.5, -2.48, PLINTH + .36, .9))):
        sack(P, 'Grain_Sack', (x, y, z_), (.28 * s, .24 * s, .56 * s), k + 2., P['sack'], yaw=k * .7, group='Detail_Sacks')
    # moss on the north plinth (rear)
    # moss on the rear plinth and along the moss-covered ridge
    for k in range(14):
        moss_patch('Moss', (R.uniform(-BX, BX), BY + .21, R.uniform(.05, .7)), (0, 1, .1), R.uniform(.12, .22), P['moss'], seed=k + 1)
    for k in range(16):
        sx_ = -1 if k % 2 else 1; moss_patch('Moss', (R.uniform(-BX, BX), TERR - .17, R.uniform(.05, .55)), (0, -1, .1), R.uniform(.1, .2), P['moss'], seed=k + 40)
    for k in range(8):
        moss_patch('Moss', (BX + .28, R.uniform(TERR, BY), R.uniform(.05, .6)), (1, 0, .1), R.uniform(.1, .2), P['moss'], seed=k + 60)
    # vines climbing the rear corner
    Rv = random.Random(8); pts = [(BX - .25 + .05 * math.sin(k), BY + .1, .45 + k * .36) for k in range(11)]
    rope('Wall_Vine', pts, .012, P['moss'], ply=1, tw=0., seg=6, amp=0., curve=4, detail=1)
    for q in pts:
        for k in range(5):
            dx, dz = Rv.uniform(-.2, .2), Rv.uniform(-.14, .14)
            moss_patch('Vine_Leaves', (q[0] + dx, BY + .1, q[2] + dz), (0, 1, .1), .055, P['moss'], seed=k + int(q[2] * 9), flat=.4)
    for k in range(9):
        moss_patch('Moss_Ridge', (-EHX + .9 + k * .77, (-1) ** k * .07, RIDGE_Z_ + .06), ((-1) ** k * .35, (-1) ** k * .1, 1), .15, P['moss'], seed=k + 20)
    mill_tiles(P)
    S['collision'] = [((-BX - .3, BY - .1, 0), (BX + .3, BY + .28, EAVE_Z_)), ((-BX - .3, TERR - .18, 0), (-BX + .1, BY + .28, EAVE_Z_)), ((BX - .1, TERR - .18, 0), (BX + .3, BY + .28, EAVE_Z_)), ((-BX - .22, -BY - .22, 0), (-1.0, -BY + .1, EAVE_Z_)), ((1.0, -BY - .22, 0), (BX + .22, -BY + .1, EAVE_Z_)), ((-1.0, -BY - .22, 2.5), (1.0, -BY + .1, EAVE_Z_)), ((-BX, TERR - .18, 0), (-1.25, -BY, PLINTH)), ((1.25, TERR - .18, 0), (BX, -BY, PLINTH))]


def horn(P, x, y, z, sx, ys, L):
    """The eave corner sweeps out and curls up, ending in a small cut block."""
    k = Vector((sx, ys, 0)).normalized()
    pts = [(x - k.x * L * .9, y - k.y * L * .9, z - .05), (x - k.x * L * .3, y - k.y * L * .3, z - .03), (x + k.x * .06, y + k.y * .06, z + .03), (x + k.x * .15, y + k.y * .15, z + L * .55), (x + k.x * .1, y + k.y * .1, z + L * .95)]
    rope('Eave_Horn', pts, .05, P['ridge'], ply=1, tw=0., seg=10, amp=.004, curve=8, step=.04, grain='z', radius_fn=lambda t: 1. - .55 * t)


def pent_tiles(P, x0, x1, ys=None, xs=None):
    """A short lean-to run of tiles, from the wall down to the pent edge. Along X (front, ys = -1) or along Y (an end, xs = +-1)."""
    pitch = .28; L = x1 - x0; n = int(L / pitch)
    # the eave lifts at the corners of the front; an end run lifts only there, and stops level at the back
    lift = (lambda q: max(0., (abs(q) - (abs(x1) - .7)) / .7)) if ys is not None else (lambda q: max(0., (x0 + .7 - q) / .7))
    for ci in range(n):
        c = x0 + (ci + .5) * L / n
        for cover in (0, 1):
            w = pitch * (.3 if cover else .6); cc = c + (pitch / 2 if cover else 0)
            if cover and ci == n - 1: continue
            for k in range(2):
                s0 = k * .5 - (.03 if k else 0); s1 = (k + 1) * .5
                def fn(u, v, cc=cc, w=w, s0=s0, s1=s1, cover=cover, k=k):
                    s = s0 + (s1 - s0) * v; a = (u - .5) * math.pi; lat = cc + math.sin(a) * w; end = lift(lat)
                    z = PZ_HI - (PZ_HI - PZ_LO) * (.6 * s + .4 * (1 - (1 - s) ** 2)) + .16 * end * end * s + math.cos(a) * w * (.82 if cover else -.2) + (.018 if cover else 0.) + .012 * (1 - v) + .003 * k + .012
                    if ys is not None: return (lat, ys * (BY + s * PY), z)
                    return (xs * (BX + s * PY), lat, z)
                sheet('Pent_Tile', 4, 2, fn, P['tile'], solid=.016, grain='y')
            if cover:
                q = (cc, ys * (BY + PY * .99), 0) if ys is not None else (xs * (BX + PY * .99), cc, 0)
                end = lift(cc)
                cyl('Tile_Cap', (q[0], q[1], PZ_LO + .16 * end * end + .05), w * .78, .018, P['ridge'], axis='y' if ys is not None else 'x', verts=12, detail=1, grain='z', bevel=.002)


def pent_roof(P):
    """The lower eave round the front and both ends, on brackets and two front posts; its deck hides what is behind."""
    pent_tiles(P, -BX - .55, BX + .55, ys=-1)
    for xs in (-1, 1):
        pent_tiles(P, -BY - .05, 1.15, xs=xs)
    def deck(u, v, side):
        s = v
        z = PZ_HI - (PZ_HI - PZ_LO) * (.6 * s + .4 * (1 - (1 - s) ** 2)) - .012
        if side == 'f': return ((u - .5) * (2 * BX + 1.1), -BY - s * PY, z)
        return (side * (BX + s * PY), -BY - .05 + u * (BY + 1.2), z)
    surface('Pent_Deck', 18, 5, lambda u, v: deck(u, v, 'f'), P['deck'], grain='y', solid=.03)
    for xs in (-1, 1):
        surface('Pent_Deck', 12, 5, lambda u, v, xs=xs: deck(u, v, xs), P['deck'], grain='x', solid=.03)
    for x in (-BX, -BX / 3, BX / 3, BX):
        between('Pent_Bracket', (x, -BY, PZ_HI - .62), (x, -BY - PY + .08, PZ_LO - .06), .1, .1, P['timber'], r=.01, amp=.003, seed=int(x * 4 + 9), div=.15)
    rbox('Pent_Purlin', (0, -BY - PY + .05, PZ_LO - .05), (2 * BX + .9, .12, .12), P['timber'], r=.012, amp=.003, seed=5, div=.25, grain='x')
    for sx in (-1, 1):
        rbox('Pent_Post', (sx * 1.25, -BY - PY + .05, (PLINTH + PZ_LO) / 2), (.15, .15, PZ_LO - PLINTH), P['timber'], r=.012, amp=.004, chips=1, seed=sx + 7, div=.2, grain='z')
        rbox('Pent_Post', (sx * (BX + .1), -BY - PY + .05, (PLINTH + PZ_LO) / 2), (.15, .15, PZ_LO - PLINTH), P['timber'], r=.012, amp=.004, chips=1, seed=sx + 3, div=.2, grain='z')
        rbox('Post_Base', (sx * 1.25, -BY - PY + .05, PLINTH + .1), (.24, .24, .2), P['plinths'][1], r=.02, amp=.006, chips=1, seed=sx + 2, div=.08)
        rbox('Post_Base', (sx * (BX + .1), -BY - PY + .05, PLINTH + .1), (.24, .24, .2), P['plinths'][2], r=.02, amp=.006, chips=1, seed=sx + 4, div=.08)
        horn(P, sx * (BX + .55), -BY - PY, PZ_LO + .2, sx, -1, .22)
    for xs in (-1, 1):
        rbox('Pent_Purlin', (xs * (BX + PY - .05), -.3, PZ_LO - .05), (.12, 3.4, .12), P['timber'], r=.012, amp=.003, seed=6, div=.25, grain='y')
        between('Pent_End_Board', (xs * BX, 1.17, PZ_HI + .03), (xs * (BX + PY + .03), 1.17, PZ_LO + .03), .05, .2, P['timber'], r=.008, amp=.003, seed=xs + 12, div=.15)
        for y in (-1.2, .95):
            between('Pent_Bracket', (xs * BX, y, PZ_HI - .62), (xs * (BX + PY - .08), y, PZ_LO - .06), .1, .1, P['timber'], r=.01, amp=.003, seed=int(y * 3 + 4), div=.15)


def awning(P, x, y, z, w, sign):
    """A little board awning over a window, on two struts."""
    n = max(3, int(w / .13))
    for k in range(n):
        xx = x - w / 2 + (k + .5) * w / n
        between('Awning_Board', (xx, y + sign * .04, z), (xx, y + sign * .42, z - .24), w / n * .88, .018, P['plank'], r=.003, amp=.002, seed=k, div=.12)
    for sx in (-1, 1):
        between('Awning_Strut', (x + sx * (w / 2 - .06), y, z - .32), (x + sx * (w / 2 - .06), y + sign * .36, z - .23), .03, .03, P['timber'], r=.004, seed=sx + 3, div=.08)


def window(P, x, y, zc, w, h, axis, dark=False):
    rbox('Window_Paper', (x, y + .005, zc), (w - .1, .012, h - .1), P['dark'] if dark else P['paper'], r=.002, div=.1)
    for sx in (-1, 1):
        rbox('Window_Frame', (x + sx * (w / 2 - .035), y - .015, zc), (.07, .07, h), P['timber'], r=.006, seed=sx + 1, div=.1, grain='z')
    for sz in (-1, 1):
        rbox('Window_Frame', (x, y - .015, zc + sz * (h / 2 - .035)), (w, .07, .07), P['timber'], r=.006, seed=sz + 4, div=.1, grain='x')
    nx = max(2, int(w / .17)); nz = max(2, int(h / .17))
    for i in range(1, nx):
        rbox('Lattice', (x - w / 2 + w * i / nx, y - .012, zc), (.02, .025, h - .08), P['timber'], r=.002, detail=1, div=.12, grain='z')
    for k in range(1, nz):
        rbox('Lattice', (x, y - .012, zc - h / 2 + h * k / nz), (w - .08, .025, .02), P['timber'], r=.002, detail=1, div=.12, grain='x')
