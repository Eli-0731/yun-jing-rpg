"""Mountain-city street dressing and the creek-side celebration: CR07 set, CR10 charm stall, CR11 noodle stall.
Charm strings pivot at their own top so the game can sway them; each lantern has a separate _Lit shell; noodle bowls are separate."""
import math, random
from mathutils import Vector, noise
from ti_core import S, RX, RY, RZ, T, cyl, lathe, socket, sphere, surface, torus, xf
import ti_mats as tm
import mk_mats as mm
import cr_mats as cm
from cr_parts import rbox, rope, lash, xlash, pole, sheet, log, between, tuft


def dipper(name, q, handle_dir, mat, group=None, **kw):
    """The same plain bamboo dipper as the tea shelter: a small cup with a straight handle on its rim."""
    k = dict(kw, **({'group': group} if group else {}))
    lathe(name + '_Cup', [(0, 0), (.05, 0), (.052, .006), (.052, .08), (.046, .08), (.046, .008), (0, .008)], q, mat, seg=18, **k)
    d = Vector(handle_dir).normalized(); a = Vector(q) + Vector((0, 0, .06)) + d * .05
    cyl_pts = [tuple(a), tuple(a + d * .34)]
    log(name + '_Handle', cyl_pts, .008, mat, seg=7, lump=.01, grain='x', **k)


# ------------------------------------------------------------------ CR07 celebration set
def cele_palette():
    P = {'plank': [cm.wood('Plank_Weathered', (.1, .075, .05), (.36, .28, .18), ground_h=0, grey=.5), cm.wood('Plank_Red', (.1, .058, .034), (.3, .19, .12), ground_h=0, grey=.4), cm.wood('Plank_Blue', (.075, .072, .062), (.25, .235, .2), ground_h=0, grey=.6), cm.wood('Plank_Honey', (.13, .08, .04), (.42, .29, .15), ground_h=0, grey=.2)]}
    P['trestle'] = cm.wood('Trestle', (.06, .036, .018), (.22, .13, .07), ground_h=.15, grey=.25); P['ring'] = tm.plain('Water_Ring', (.09, .055, .035), rough=.5, noise=.1); P['iron'] = mm.cast_iron('Table_Iron')
    P['culm'] = cm.culm('Pole_Bamboo', green=(.14, .17, .05), straw=(.34, .27, .12), mud_h=.25); P['hemp'] = mm.hemp('Hemp_Rope', (.3, .2, .09), twist=40.0); P['paper'] = cm.paper('Lantern_Paper', base=(.66, .56, .34), edge=(.42, .27, .13), age=.15); P['mend'] = cm.paper('Lantern_Mend', base=(.42, .2, .13), age=.4)
    P['paper_old'] = cm.paper('Lantern_Paper_Old', base=(.5, .39, .21), edge=(.3, .18, .08), age=.35); P['lit'] = tm.paper('Lantern_Lit', (.85, .62, .3), 'Main', emit=(1., .68, .32)); P['rib'] = mm.bamboo('Lantern_Rib'); P['brass'] = mm.brass('Lantern_Brass', base=(.46, .27, .1), amt=.3); P['tassel'] = mm.cloth('Lantern_Tassel', (.36, .09, .06), dirt=.3)
    P['jar'] = cm.clay('Wine_Jar', body=(.2, .085, .045), glaze=(.13, .055, .03)); P['jar2'] = cm.clay('Wine_Jar_Small', body=(.17, .08, .04), glaze=(.1, .05, .028)); P['cap'] = mm.cloth('Jar_Cap', (.3, .055, .04), dirt=.3)
    P['basket'] = mm.bamboo('Basket_Bamboo'); P['grass'] = cm.moss_tuft('Foot_Grass', soft=True); P['rag'] = cm.canvas('Line_Rag', base=(.62, .55, .4), stain=(.34, .27, .16), faded=.2, dirt=.5)
    P['orange'] = tm.plain('Fruit_Orange', (.66, .34, .06), rough=.5, noise=.12); P['peach'] = tm.plain('Fruit_Peach', (.68, .25, .17), rough=.6, noise=.2); P['leaf'] = tm.plain('Fruit_Leaf', (.08, .17, .04), rough=.6, noise=.2)
    return P


def lantern(P, i, c):
    g = f'Lantern_{i:02d}'; R, H = .15 * (1 + .07 * math.sin(i * 2.3)), .13 * (1 + .09 * math.sin(i * 4.1 + 1.))
    prof = [(max(.035, R * math.cos(t)), H * math.sin(t)) for t in [-1.3 + k * 2.6 / 12 for k in range(13)]]
    prof = [(0, prof[0][1])] + prof + [(0, prof[-1][1])]
    lathe('Paper', prof, c, P['paper_old'] if i % 3 == 1 else P['paper'], seg=20, group=g)
    if i == 3:   # the mended lantern: two stitched-on squares
        for j, (a0, h0, da, dh) in enumerate(((-1.95, -.1, .75, .75), (-.9, .2, .5, .55))):
            def mend(u, v, a0=a0, h0=h0, da=da, dh=dh):
                a = a0 + u * da; h = h0 - .5 + v * dh; r = R * math.cos(h * 1.3) * 1.018 + .001
                return (c[0] + math.cos(a) * r, c[1] + math.sin(a) * r, c[2] + H * math.sin(h * 1.3) * 1.018)
            sheet('Mend', 6, 6, mend, P['mend'], solid=.0015, group=g, detail=1)
    for h in (-.7, -.35, 0., .35, .7):
        q = h * 1.3
        torus('Rib', (c[0], c[1], c[2] + H * math.sin(q)), R * math.cos(q) + .0006, .0022, P['rib'], major=20, minor=3, group=g, detail=1)
    for sz in (-1, 1):
        lathe('Brass_Cap', [(0, sz * H * 1.08), (.05, sz * H * 1.08), (.056, sz * H * .96), (.05, sz * H * .9)], c, P['brass'], seg=14, group=g)
    torus('Hook', (c[0], c[1], c[2] + H * 1.08 + .015), .014, .0028, P['brass'], rot=(math.pi / 2, 0, 0), major=10, minor=4, group=g, detail=1)
    z = c[2] - H * 1.08
    rope('Tassel_Cord', [(c[0], c[1], z), (c[0], c[1], z - .05)], .003, P['tassel'], ply=1, tw=0., seg=4, amp=0., group=g, detail=1)
    rope('Tassel', [(c[0], c[1], z - .05), (c[0], c[1], z - .14)], .012, P['tassel'], ply=1, tw=0., seg=7, amp=0., group=g, radius_fn=lambda t: .55 + .75 * t)
    lathe('Glow', prof, c, P['lit'], seg=20, scale=(1.012, 1.012, 1.01), group=g + '_Lit')


def jar(P, name, q, s, mat):
    prof = [(0, 0), (.13 * s, 0), (.15 * s, .012), (.235 * s, .16 * s), (.25 * s, .27 * s), (.2 * s, .4 * s), (.1 * s, .46 * s), (.09 * s, .49 * s), (.105 * s, .51 * s), (.095 * s, .52 * s), (0, .52 * s)]
    lathe('Jar', prof, q, mat, seg=28, group=name)
    # the red cloth tied over the mouth: a soft dome and a pleated skirt falling over the shoulder
    def cap(u, v):
        a = u * math.tau; flare = .12 * s * (.15 + .85 * min(1., v * 2.)) + .1 * s * max(0., v - .5) * 2
        rr = flare * (1 + .045 * math.sin(a * 9) * v)
        return (q[0] + math.cos(a) * rr, q[1] + math.sin(a) * rr, q[2] + s * (.57 - .05 * min(1., v * 2.) - .085 * max(0., v - .5) * 2 + .018 * math.sin(a * 5) * max(0., v - .5)))
    surface('Cap', 28, 10, cap, P['cap'], closed_u=True, grain='z', group=name)
    torus('Cap_Tie', (q[0], q[1], q[2] + s * .505), .1 * s, .0055, P['hemp'], major=20, minor=5, group=name, detail=1)
    for sd in (-1, 1):
        rope('Cap_Tail', [(q[0] + .05 * s * sd, q[1] - .09 * s, q[2] + s * .5), (q[0] + .08 * s * sd, q[1] - .13 * s, q[2] + s * .44), (q[0] + .07 * s * sd, q[1] - .15 * s, q[2] + s * .38)], .004, P['hemp'], ply=1, tw=0., seg=5, amp=0., curve=4, group=name, detail=1)


def fruit_basket(P, q):
    g = 'FruitBasket'; R0, R1, H = .13, .2, .13
    for k in range(20):
        a = k / 20 * math.tau
        rope('Basket_Rib', [(q[0] + math.cos(a) * R0, q[1] + math.sin(a) * R0, q[2]), (q[0] + math.cos(a) * R1, q[1] + math.sin(a) * R1, q[2] + H)], .007, P['basket'], ply=1, tw=0., seg=5, amp=0., group=g)
    for j in range(7):
        h = (j + .5) / 7; r = R0 + (R1 - R0) * h
        torus('Basket_Band', (q[0], q[1], q[2] + h * H), r, .0078, P['basket'], major=36, minor=5, group=g)
    torus('Basket_Rim', (q[0], q[1], q[2] + H), R1, .014, P['basket'], major=36, minor=8, group=g)
    cyl('Basket_Floor', (q[0], q[1], q[2] + .006), R0, .012, P['basket'], verts=20, group=g)
    # the bent bamboo handle over the top
    pts = [(q[0] - R1 * math.cos(t), q[1], q[2] + H + math.sin(t) * .2) for t in [k / 10 * math.pi for k in range(11)]]
    log('Basket_Handle', pts, .01, P['basket'], seg=8, lump=.01, grain='x', group=g, curve=4)
    for sd in (-1, 1):
        lash('Handle_Tie', (q[0] + sd * R1, q[1], q[2] + H + .01), (0, 0, 1), .013, .035, .0035, P['hemp'], group=g, turns=4, detail=1)
    R = random.Random(7)
    for k in range(9):
        a = R.uniform(0, 6.28); rr = R.uniform(.04, .13) if k > 2 else .03
        z = q[2] + .1 + (k > 5) * .05 + (k < 2) * .075
        r = R.uniform(.044, .055); mat = P['orange'] if k % 3 else P['peach']
        sphere('Fruit', (q[0] + math.cos(a) * rr, q[1] + math.sin(a) * rr, z), r, mat, scale=(1, 1, .92), seg=16, ring=10, group=g)
    for k in range(5):
        a = k * 1.3 + .4
        sheet('Fruit_Leaf', 1, 4, lambda u, v, a=a: (q[0] + math.cos(a) * (.08 + v * .1) - math.sin(a) * (u - .5) * .04 * math.sin(v * 3.14), q[1] + math.sin(a) * (.08 + v * .1) + math.cos(a) * (u - .5) * .04 * math.sin(v * 3.14), q[2] + .17 + .02 * math.sin(v * 3) - v * .02), P['leaf'], solid=.001, group=g, detail=1)


def tripod_pole(P, sx, Z):
    x0 = sx * 2.98
    pole('Lantern_Pole', (x0, 0, 0), (x0, 0, Z + .17), .05, .038, P['culm'], node_gap=.42, bend=.012, seed=sx + 3, cut=.0)
    knot = 1.02
    for k, (dx, dy) in enumerate(((-sx * .44, .0), (sx * .2, .4), (sx * .2, -.4))):
        pole('Tripod_Brace', (x0 + dx, dy, 0), (x0 + dx * .08, dy * .08, knot + .1), .034, .028, P['culm'], node_gap=.36, bend=.01, seed=k + sx * 4 + 9, cut=.0)
    lash('Tripod_Lash', (x0, 0, knot), (0, 0, 1), .07, .13, .0085, P['hemp'], turns=7, detail=1)
    lash('Line_Tie', (x0, 0, Z), (0, 0, 1), .044, .075, .0075, P['hemp'], turns=6, detail=1)
    rope('Line_Tail', [(x0 + sx * .03, -.03, Z - .02), (x0 + sx * .06, -.045, Z - .16), (x0 + sx * .05, -.045, Z - .3)], .0055, P['hemp'], curve=4, detail=1)
    for k, (dx, dy) in enumerate(((.13, .1), (-.12, .16), (.05, -.16), (-.2, -.08))):
        tuft('Foot_Grass', (x0 + dx, dy, 0), .1, P['grass'], seed=k + sx + 5)


def cr07(P):
    # patchwork table: mismatched planks of different stock, ends not flush
    R = random.Random(707); y = -.45; i = 0; TZ = .78
    while y < .44:
        w = R.uniform(.14, .25); w = min(w, .45 - y)
        if .45 - y - w < .1: w = .45 - y
        x0, x1 = -1.5 + R.uniform(0, .07), 1.5 - R.uniform(0, .08)
        if i % 2 == 0:         # this run is two boards of different stock
            xm = R.uniform(-.6, .7)
            rbox('Table_Plank', ((x0 + xm) / 2, y + w / 2, TZ - .02), (xm - x0 - .006, w - .008, .045), P['plank'][i % 4], r=.009, amp=.005, chips=2, seed=i, div=.2, group='Table', grain='x')
            rbox('Table_Plank', ((xm + x1) / 2, y + w / 2, TZ - .02 + .004), (x1 - xm - .006, w - .008, .045), P['plank'][(i + 1) % 4], r=.009, amp=.005, chips=2, seed=i + 31, div=.2, group='Table', grain='x')
        else:
            rbox('Table_Plank', ((x0 + x1) / 2, y + w / 2, TZ - .02 + .006), (x1 - x0, w - .008, .045), P['plank'][(i + 3) % 4], r=.009, amp=.005, chips=2, seed=i, div=.2, group='Table', grain='x')
        y += w; i += 1
    for sx in (-1, 1):
        x = sx * 1.22
        rbox('Trestle_Top', (x, 0, TZ - .08), (.09, .86, .09), P['trestle'], r=.01, amp=.003, seed=sx + 3, div=.12, group='Table', grain='y')
        for sy in (-1, 1):
            rbox('Trestle_Leg', (x, sy * .32, (TZ - .1) / 2), (.1, .09, TZ - .1), P['trestle'], r=.012, amp=.004, chips=2, seed=int(sx * 2 + sy + 5), div=.12, group='Table', grain='z')
            lash('Leg_Lash', (x, sy * .32, TZ - .22), (0, 0, 1), .068, .1, .0075, P['hemp'], group='Table', turns=6, detail=1)
            between('Knee_Brace', (x, sy * .32, .3), (x - sx * .4, sy * .32, TZ - .12), .05, .07, P['trestle'], r=.008, amp=.003, seed=int(sx + sy + 9), div=.1, group='Table')
        rbox('Trestle_Foot', (x, 0, .2), (.06, .68, .07), P['trestle'], r=.008, seed=sx + 9, div=.12, group='Table', grain='y')
    for sy in (-1, 1):
        rbox('Table_Rail', (0, sy * .32, TZ - .12), (2.4, .05, .08), P['trestle'], r=.01, amp=.003, seed=sy + 4, div=.15, group='Table', grain='x')
        rbox('Low_Stretcher', (0, sy * .32, .2), (2.4, .05, .06), P['trestle'], r=.008, amp=.003, seed=sy + 7, div=.15, group='Table', grain='x')
        rbox('Centre_Post', (.3 * sy, sy * .32, .36), (.07, .055, .36), P['trestle'], r=.008, seed=sy + 12, div=.1, group='Table', grain='z')
    # the mend nailed across the front rail
    rbox('Mend_Board', (.2, -.355, TZ - .13), (.46, .022, .13), P['plank'][3], r=.006, amp=.004, chips=2, seed=71, div=.08, group='Table', grain='x', rot=(0, .03, 0))
    for dx in (-.19, .19):
        cyl('Mend_Nail', (.2 + dx, -.368, TZ - .13), .012, .012, P['iron'], axis='y', verts=8, bevel=.002, group='Table', detail=1)
    for k, (x, y_, r) in enumerate(((-.82, -.1, .06), (-.68, -.14, .05), (-.56, -.08, .055))):
        torus('Water_Ring', (x, y_, TZ + .011), r, .003, P['ring'], major=28, minor=4, group='Detail_Rings')
    fruit_basket(P, (1.08, 0, TZ + .01))
    jar(P, 'Jar_1', (.62, 0, TZ + .01), .78, P['jar']); jar(P, 'Jar_2', (.15, .03, TZ + .01), .54, P['jar2'])
    # the lantern string: two tripod-braced bamboo poles 6 m apart, a sagging hemp line, one lantern every 0.6 m
    Y = 0; Z = 2.55
    for sx in (-1, 1): tripod_pole(P, sx, Z)
    sag = lambda x: Z - .26 * (1 - (x / 2.96) ** 2)
    rope('Lantern_Line', [(x, Y, sag(x)) for x in [-2.96 + 5.92 * k / 16 for k in range(17)]], .0075, P['hemp'], curve=4, step=.05, amp=.1)
    for k in range(9):
        x = -2.4 + k * .6; c = (x, Y, sag(x) - .23)
        rope('Lantern_Hanger', [(x, Y, sag(x)), (x, Y, c[2] + .16)], .0035, P['hemp'], ply=1, tw=0., seg=4, amp=0., detail=1, group=f'Lantern_{k + 1:02d}')
        lantern(P, k + 1, c)
    # rag strips tied on the line where an old one wore through
    for j, x in enumerate((-2.1, 2.1)):
        def rag(u, v, x=x, j=j):
            return (x + (u - .5) * .07 * (1 - .4 * (1 - v)) + .01 * math.sin(v * 7 + j), .012 * math.sin(v * 5 + j), sag(x) - .02 - (1 - v) * .26)
        sheet('Line_Rag', 3, 8, rag, P['rag'], solid=.0012, grain='z', keep=lambda u, v, j=j: v > .15 or abs(math.sin(u * 19 + j)) > .3)
        lash('Rag_Knot', (x, Y, sag(x)), (1, 0, 0), .012, .035, .0045, P['rag'], turns=3, detail=1)
    socket('Socket_TableCentre', (0, 0, TZ + .01))
    S['collision'] = [((-1.5, -.45, 0), (1.5, .45, TZ)), ((-3.05, -.05, 0), (-2.91, .05, 2.7)), ((2.91, -.05, 0), (3.05, .05, 2.7))]


# ------------------------------------------------------------------ shared small tiled gable, ridge along X
def gable_tiles(P, XR, YR, zf, pitch=.17, courses=5, solid=.01):
    n = int((2 * XR - .05) / pitch); x0 = -pitch * (n - 1) / 2
    for ys in (-1, 1):
        for ci in range(n):
            x = x0 + ci * pitch
            for cover in (0, 1):
                xc = x + (pitch / 2 if cover else 0)
                if cover and ci == n - 1: continue
                w = pitch * (.3 if cover else .6)
                for k in range(courses):
                    s0 = .02 + k * .98 / courses - (.02 if k else 0); s1 = .02 + (k + 1) * .98 / courses
                    Rj = random.Random(ci * 100 + k * 7 + cover * 3 + ys); dx, dz = Rj.uniform(-.004, .004), Rj.uniform(-.004, .005)
                    def fn(u, v, xc=xc, w=w, s0=s0, s1=s1, cover=cover, k=k, ys=ys, dx=dx, dz=dz):
                        s = s0 + (s1 - s0) * v; y = ys * s * YR; a = (u - .5) * math.pi
                        return (xc + dx + math.sin(a) * w, y, zf(y, xc) + dz + math.cos(a) * w * (.66 if cover else -.2) + (.014 if cover else 0.) + .02 * (1 - v) ** 2 + .003 * k + .012)
                    sheet('Tile', 4, 2, fn, P['tile'], solid=solid, grain='y')
                if cover:
                    y = ys * YR * .995
                    cyl('Tile_Cap', (xc, y, zf(y, xc) + .04), w * .7, .014, P['ridge'], axis='y', verts=12, detail=1, grain='z', bevel=.002)
    surface('Roof_Deck', 20, 14, lambda u, v: ((u - .5) * 2 * (XR - .01), (v - .5) * 2 * YR, zf((v - .5) * 2 * YR, (u - .5) * 2 * (XR - .01)) - .018), P['deck'], grain='y', solid=.022)


# ------------------------------------------------------------------ CR10 charm stall
def charm_palette():
    P = {'old': cm.wood('Old_Timber', (.07, .04, .022), (.26, .155, .08), ground_h=.15, grey=.25), 'green': cm.wood('Painted_Green', (.05, .075, .06), (.15, .23, .18), ground_h=.1, grey=.2), 'gold': mm.brass('Peeling_Gilt', base=(.56, .38, .1), amt=.4)}
    P['slip'] = cm.paper('Charm_Yellow', base=(.72, .54, .13), edge=(.5, .32, .08), age=.3); P['ink'] = tm.plain('Cinnabar_Swirl', (.5, .06, .03), rough=.65, noise=.15); P['thread'] = mm.hemp('Red_Thread', (.42, .06, .04), twist=40.0)
    P['banner'] = cm.canvas('Pale_Banner', base=(.42, .345, .235), stain=(.2, .145, .085), faded=.12, dirt=.8); P['patch'] = cm.canvas('Banner_Patch', base=(.34, .265, .17), stain=(.18, .125, .075), faded=.2, dirt=.4)
    P['red'] = mm.cloth('Red_Valance', (.36, .075, .05), dirt=.45); P['yellow'] = mm.cloth('Yellow_Stripe', (.62, .4, .08), dirt=.4); P['cushion'] = mm.cloth('Worn_Cushion', (.3, .07, .06), dirt=.5, worn=.4)
    P['brick'] = cm.stone('Prop_Brick', light=(.36, .16, .1), dark=(.16, .07, .045), ochre=(.28, .13, .08), moss=.1, crack=.3, lichen=0); P['gourd'] = mm.brass('Gilded_Gourd', base=(.6, .4, .1), amt=.2); P['bell'] = mm.brass('Tiny_Bell', base=(.5, .32, .09), amt=.3)
    P['tile'] = cm.tile('Roof_Tile'); P['ridge'] = cm.tile('Ridge_Tile', base=(.03, .04, .052), light=(.075, .09, .1), moss=.7); P['deck'] = cm.wood('Roof_Deck', (.03, .02, .014), (.09, .06, .04), ground_h=0, grey=.1)
    P['vine'] = cm.moss_tuft('Roof_Vine', soft=True); P['leaf'] = tm.plain('Vine_Leaf', (.16, .24, .05), rough=.6, noise=.2); P['basket'] = mm.bamboo('Goods_Basket'); P['scroll'] = cm.paper('Scroll_Paper', base=(.66, .5, .2), age=.3)
    return P


def plate(name, c, yaw, r, w, mat, group, turn=1., seg=18):
    """A red ring or spiral brushed on a slip; thicker than the paper so it shows from both sides. Abstract, no letters."""
    ca, sa = math.cos(yaw), math.sin(yaw)
    def fn(u, v):
        a = v * turn * math.tau; rr = (r if turn == 1. else r * (.2 + .8 * v)) + (u - .5) * w
        return (c[0] + math.cos(a) * rr * ca, c[1] + math.cos(a) * rr * sa, c[2] + math.sin(a) * rr)
    sheet(name, 1, seg, fn, mat, solid=.0028, group=group, detail=1)


def charm_string(P, i, x, y, ztop, n, seed):
    g = f'CharmString_{i:02d}'; R = random.Random(seed)
    socket(f'Socket_Charm_{i:02d}', (x, y, ztop))
    H, GAP = .135, .03; L = n * (H + GAP)
    rope('Thread', [(x, y, ztop), (x, y, ztop - L - .02)], .0028, P['thread'], ply=1, tw=0., seg=4, amp=0., group=g, detail=1)
    z = ztop - GAP
    for k in range(n):
        yaw = R.uniform(-.22, .22); w = .096; h = H; ca, sa = math.cos(yaw), math.sin(yaw); curl = R.uniform(-.012, .012); zk = z
        def fn(u, v, ca=ca, sa=sa, zk=zk, curl=curl, w=w, h=h):
            lx = (u - .5) * w
            return (x + lx * ca, y + lx * sa + curl * (1 - v) ** 2, zk - (1 - v) * h)
        sheet('Slip', 2, 3, fn, P['slip'], solid=.0009, group=g)
        c = (x, y, zk - h * .5)
        plate('Ring', c, yaw, .032, .009, P['ink'], g)
        plate('Swirl', c, yaw, .018, .006, P['ink'], g, turn=1.4, seg=10)
        z -= H + GAP
    if i % 3 == 0:     # a small bell closes this string
        lathe('Bell', [(0, 0), (.026, 0), (.028, .006), (.018, .034), (.007, .046), (0, .046)], (x, y, z - .035), P['bell'], seg=10, group=g, detail=1)
        z -= .04
    rope('Tassel', [(x, y, z + .01), (x, y, z - .09)], .0085, P['thread'], ply=1, tw=0., seg=6, amp=0., group=g, radius_fn=lambda t: .55 + .8 * t)


def gourd(P, q, s, group, mat=None):
    prof = [(0, 0), (.04 * s, .002), (.06 * s, .03 * s), (.062 * s, .055 * s), (.042 * s, .09 * s), (.024 * s, .105 * s), (.032 * s, .125 * s), (.033 * s, .14 * s), (.02 * s, .158 * s), (.008 * s, .165 * s), (.008 * s, .185 * s), (0, .185 * s)]
    lathe('Gourd', prof, q, mat or P['gourd'], seg=14, group=group, detail=1)
    torus('Gourd_Tie', (q[0], q[1], q[2] + .106 * s), .025 * s, .0028, P['thread'], major=10, minor=4, group=group, detail=1)


def cloud_paint(P, c, s, axis, sign):
    """A plain gold cloud brushed on a panel: three curls and a trailing line. Not writing."""
    def put(a, b):
        return (c[0] + a, c[1] + sign * .002, c[2] + b) if axis == 'x' else (c[0] + sign * .002, c[1] + a, c[2] + b)
    for dx, dz, r, t in ((-.11, 0., .07, 1.5), (.03, .035, .09, 1.7), (.16, -.005, .06, 1.4)):
        def curl(u, v, dx=dx, dz=dz, r=r, t=t):
            a = v * t * math.tau; rr = r * (.2 + .8 * v) * s + (u - .5) * .012 * s
            return put((dx * s + math.cos(a) * rr), (dz * s + math.sin(a) * rr))
        sheet('Cloud_Paint', 1, 20, curl, P['gold'], solid=.003, detail=1)
    sheet('Cloud_Paint', 1, 10, lambda u, v: put((-.2 + v * .55) * s, (-.075 + .012 * math.sin(v * 6) + (u - .5) * .014) * s), P['gold'], solid=.003, detail=1)


def cr10(P):
    BX, BY = 1.22, .5; CZ, BED = .86, .3; RX_, RY_ = 1.55, .8; RIDGE, EAVE = 2.2, 1.9
    # roof line: straight fall with a sweep at the eave, the corners lifted
    def zf(y, x=0.):
        s = min(1., abs(y) / RY_); fx = max(0., (abs(x) - (RX_ - .45)) / .45)
        return RIDGE - (RIDGE - EAVE) * (.55 * s + .45 * (1 - (1 - s) ** 2.2)) + .07 * fx * fx * s
    # four corner posts: the right pair run to the ground (one short, on bricks); the left pair stop on the bed over the wheels
    for sy in (-1, 1):
        rbox('Post', (-BX + .04, sy * .44, (BED + EAVE) / 2), (.1, .1, EAVE - BED), P['old'], r=.012, amp=.004, chips=2, seed=sy + 3, div=.2, grain='z')
    rbox('Post', (BX - .04, .44, EAVE / 2), (.1, .1, EAVE), P['old'], r=.012, amp=.004, chips=2, seed=5, div=.2, grain='z')
    rbox('Post', (BX - .04, -.44, (.11 + EAVE) / 2), (.1, .1, EAVE - .11), P['old'], r=.012, amp=.004, chips=2, seed=6, div=.2, grain='z')
    for k, (dx, z) in enumerate(((0, .03), (.12, .03), (.06, .085))):
        rbox('Prop_Brick', (BX - .1 + dx, -.44, z), (.11, .13, .055), P['brick'], r=.006, amp=.004, chips=2, seed=k + 3, div=.04)
    # the body: frame rails, painted boards with the paint worn off
    for z, h in ((BED, .07), (CZ - .03, .06)):
        for sy in (-1, 1):
            rbox('Rail', (0, sy * BY, z), (2 * BX + .1, .07, h), P['old'], r=.01, amp=.004, chips=1, seed=int(z * 9 + sy), div=.2, grain='x')
        for sx in (-1, 1):
            rbox('Rail', (sx * BX, 0, z), (.07, 2 * BY + .1, h), P['old'], r=.01, amp=.004, chips=1, seed=int(z * 7 + sx), div=.2, grain='y')
    rbox('Bed', (0, 0, BED + .03), (2 * BX, 2 * BY, .04), P['old'], r=.006, seed=6, div=.25, grain='x')
    R = random.Random(10)
    for sy in (-1, 1):
        x = -BX + .04
        while x < BX - .05:
            w = min(R.uniform(.2, .3), BX - .04 - x)
            rbox('Panel', (x + w / 2, sy * (BY - .005), (BED + CZ) / 2), (w - .008, .025, CZ - BED - .08), P['green'], r=.005, amp=.003, chips=2, seed=R.randint(1, 900), div=.12, grain='z')
            x += w
    for sx in (-1, 1):
        y = -BY + .04
        while y < BY - .05:
            w = min(R.uniform(.2, .28), BY - .04 - y)
            rbox('Panel', (sx * (BX - .005), y + w / 2, (BED + CZ) / 2), (.025, w - .008, CZ - BED - .08), P['green'], r=.005, amp=.003, chips=2, seed=R.randint(1, 900), div=.12, grain='z')
            y += w
    between('Panel_Brace', (BX - .1, BY + .02, BED + .05), (BX - .6, BY + .02, CZ - .05), .05, .03, P['old'], r=.006, amp=.003, seed=2, div=.1)
    between('Panel_Brace', (-BX - .02, -.42, BED + .05), (-BX - .02, .1, CZ - .05), .03, .05, P['old'], r=.006, amp=.003, seed=4, div=.1)
    cloud_paint(P, (.42, -BY - .02, .55), 1., 'x', -1); cloud_paint(P, (-.1, BY + .02, .55), 1.5, 'x', 1); cloud_paint(P, (.82, BY + .02, .68), .7, 'x', 1)
    cloud_paint(P, (-BX - .02, .12, .55), .9, 'y', -1); cloud_paint(P, (BX + .02, -.05, .55), .9, 'y', 1)
    rbox('Counter', (0, 0, CZ + .01), (2 * BX + .24, 2 * BY + .16, .05), P['old'], r=.012, amp=.004, chips=2, seed=1, div=.2, grain='x')
    # one big cart wheel at each side of the left end
    WX, WZ, WR = -.82, .47, .47
    for sy in (-1, 1):
        y = sy * (BY + .07)
        cyl('Wheel_Hub', (WX, y, WZ), .075, .12, P['old'], axis='y', verts=18, bevel=.008, grain='y')
        cyl('Hub_Iron', (WX, y, WZ), .05, .135, P['bell'], axis='y', verts=14, bevel=.004, grain='y', detail=1)
        with xf(T(WX, y, WZ) @ RX(math.pi / 2)):
            lathe('Wheel_Rim', [(WR - .06, -.03), (WR - .01, -.035), (WR, -.025), (WR, .025), (WR - .01, .035), (WR - .06, .03), (WR - .06, -.03)], (0, 0, 0), P['old'], seg=40, grain='z')
        for k in range(8):
            a = k / 8 * math.tau + .2
            between('Wheel_Spoke', (WX + math.cos(a) * .06, y, WZ + math.sin(a) * .06), (WX + math.cos(a) * (WR - .05), y, WZ + math.sin(a) * (WR - .05)), .034, .034, P['old'], r=.006, amp=.002, seed=k, div=.1)
    cyl('Axle', (WX, 0, WZ), .025, 2 * BY + .24, P['old'], axis='y', verts=10, bevel=.003, grain='y')
    # roof timbers
    for sx in (-1, 1):
        x = sx * (BX - .04)
        rbox('Tie_Beam', (x, 0, EAVE - .03), (.09, 2 * RY_ - .1, .09), P['old'], r=.01, amp=.003, seed=sx + 8, div=.15, grain='y')
        rbox('King_Post', (x, 0, (EAVE + RIDGE) / 2 - .03), (.08, .08, RIDGE - EAVE), P['old'], r=.01, amp=.003, seed=sx + 2, div=.12, grain='z')
        for sy in (-1, 1):
            between('Rafter', (x, 0, RIDGE - .02), (x, sy * (RY_ - .02), zf(RY_, x) - .05), .07, .08, P['old'], r=.008, amp=.003, seed=int(sx + sy + 12), div=.15)
    for sy in (-1, 1):
        rbox('Eave_Beam', (0, sy * (RY_ - .1), EAVE - .03), (2 * RX_ - .3, .07, .08), P['old'], r=.01, amp=.003, seed=sy + 14, div=.2, grain='x')
    gable_tiles(P, RX_, RY_, zf)
    rbox('Ridge_Core', (0, 0, RIDGE + .04), (2 * RX_ - .2, .13, .09), P['ridge'], r=.025, amp=.005, freq=4., seed=41, div=.08, grain='x')
    for sx in (-1, 1):
        rope('Ridge_End', [(sx * (RX_ - .34), 0, RIDGE + .07), (sx * (RX_ - .18), 0, RIDGE + .085), (sx * (RX_ - .08), 0, RIDGE + .12), (sx * (RX_ - .05), 0, RIDGE + .155)], .032, P['ridge'], ply=1, tw=0., amp=.004, curve=8, step=.03, grain='x')
        sphere('Ridge_Bead', (sx * (RX_ - .05), 0, RIDGE + .165), .022, P['gold'], seg=10, ring=7)
        for sy in (-1, 1):
            cyl('Corner_Disc', (sx * (RX_ - .02), sy * (RY_ - .02), zf(RY_, RX_) + .03), .05, .018, P['gold'], axis='x', verts=16, bevel=.004, grain='x')
    # vines creeping over the ridge
    Rv = random.Random(3)
    for j, (x0, x1) in enumerate(((-1.35, -.55), (.5, 1.25))):
        pts = [(x0 + (x1 - x0) * t, -.04 - .35 * abs(math.sin(t * 5 + j)) * t, 0.) for t in [k / 7 for k in range(8)]]
        pts = [(x, y, zf(y, x) + .07) for x, y, _ in pts]
        rope('Vine', pts, .005, P['vine'], ply=1, tw=0., seg=5, amp=0., curve=3, detail=1)
        for q in pts:
            for k in range(2):
                a = Rv.uniform(0, 6.28)
                sheet('Vine_Leaf', 1, 3, lambda u, v, a=a, q=q: (q[0] + math.cos(a) * v * .08 - math.sin(a) * (u - .5) * .05 * math.sin(v * 3.14), q[1] + math.sin(a) * v * .08 + math.cos(a) * (u - .5) * .05 * math.sin(v * 3.14), q[2] + .012), P['leaf'], solid=.001, detail=1)
    # the valance under the eaves: red with two yellow stripes, a wavy hem
    def val(name, a, b, y, mat, top, drop, sign):
        def fn(u, v):
            x = a + (b - a) * u
            bot = top - drop - .035 * math.sin(x * 5.5) - .02 * math.sin(x * 13)
            return (x, y + sign * (.016 * math.sin(x * 9) * (1 - v) + .02 * (1 - v)), bot + (top - bot) * v)
        sheet(name, max(2, int((b - a) * 16)), 5, fn, mat, solid=.002, grain='z')
    for sign, y in ((-1, -RY_ + .1), (1, RY_ - .1)):
        for a, b, m in ((-1.32, -1.1, 'yellow'), (-1.1, -.82, 'red'), (-.82, -.62, 'yellow'), (-.62, .62, 'red'), (.62, .82, 'yellow'), (.82, 1.1, 'red'), (1.1, 1.32, 'yellow')):
            val('Valance', a, b, y, P[m], EAVE - .03, .3, sign)
    for sx in (-1, 1):
        def side(u, v, sx=sx):
            y = (u - .5) * (2 * RY_ - .2); bot = EAVE - .03 - .22 - .03 * math.sin(y * 7)
            return (sx * 1.32 + sx * .012 * math.sin(y * 9), y, bot + (EAVE - .03 - bot) * v)
        sheet('Valance', 18, 4, side, P['red'], solid=.002, grain='z')
    # the hanging rods and the goods on them: 14 strings in front, 10 behind, each its own object
    RZ_ = 1.55
    for k, y in enumerate((-BY - .1, BY - .05)):
        log('Hang_Rod', [(-BX - .04, y, RZ_), (BX + .04, y, RZ_)], .014, P['old'], seg=8, lump=.01, seed=k, grain='x')
    cn = 0
    for k in range(14):
        cn += 1
        charm_string(P, cn, -1.08 + k * (2.16 / 13), -BY - .1, RZ_ - .01, 2 + (k * 7 % 2), 10 + k)
    for k in range(10):
        cn += 1
        charm_string(P, cn, -1.05 + k * (2.1 / 9), BY - .05, RZ_ - .01, 2 + (k * 5 % 2), 40 + k)
    S['charm_count'] = cn
    # bells on their own rod, behind the first strings
    log('Bell_Rod', [(-BX, .0, 1.58), (BX, .0, 1.58)], .012, P['old'], seg=8, lump=.01, seed=5, grain='x')
    for k in range(9):
        x = -1.02 + k * .255
        rope('Bell_Cord', [(x, 0, 1.57), (x, 0, 1.49)], .003, P['thread'], ply=1, tw=0., seg=4, amp=0., group='Detail_Bells', detail=1)
        lathe('Bell', [(0, 0), (.032, 0), (.034, .007), (.022, .04), (.008, .054), (0, .054)], (x, 0, 1.435), P['bell'], seg=10, group='Detail_Bells', detail=1)
    # shelves of gourds, a basket of tags, a box, scrolls in a bowl; the cloth over the counter
    SZ = CZ + .035
    rbox('Goods_Shelf', (0, .24, SZ + .24), (2.1, .2, .03), P['old'], r=.005, seed=30, div=.2, grain='x')
    for sx in (-1, 1):
        rbox('Goods_Shelf_Leg', (sx * 1., .24, SZ + .115), (.05, .15, .23), P['old'], r=.005, seed=sx + 31, div=.1, grain='z')
    Rg = random.Random(11)
    for k in range(11):
        gourd(P, (-.92 + k * .184 + Rg.uniform(-.01, .01), .24 + Rg.uniform(-.03, .03), SZ + .255), Rg.uniform(.8, 1.1), 'Detail_Gourds')
    for k in range(7):
        gourd(P, (-.2 + k * .1, -.02 + Rg.uniform(-.05, .05) + (k % 2) * .07, SZ), Rg.uniform(.75, 1.), 'Detail_Gourds')
    for k in range(10):
        a = k / 10 * math.tau
        rope('Basket_Rib', [(-.82 + math.cos(a) * .1, -.12 + math.sin(a) * .1, SZ), (-.82 + math.cos(a) * .15, -.12 + math.sin(a) * .15, SZ + .1)], .007, P['basket'], ply=1, tw=0., seg=4, amp=0., group='Detail_Goods')
    for j in range(4):
        h = (j + .5) / 4
        torus('Basket_Band', (-.82, -.12, SZ + h * .1), .1 + .05 * h, .0085, P['basket'], major=20, minor=4, group='Detail_Goods')
    for k in range(5):
        rbox('Basket_Tag', (-.82 + (k - 2) * .035, -.12, SZ + .14), (.03, .1, .14), P['slip'], r=.001, div=.1, rot=(0, (k - 2) * .1, 0), group='Detail_Goods', detail=1)
    rbox('Goods_Box', (-.43, -.1, SZ + .055), (.42, .22, .11), P['old'], r=.01, amp=.003, seed=7, div=.1, group='Detail_Goods', grain='x')
    rbox('Box_Latch', (-.43, -.213, SZ + .07), (.05, .006, .05), P['gold'], r=.002, div=.05, group='Detail_Goods', detail=1)
    lathe('Goods_Bowl', [(0, 0), (.06, 0), (.11, .05), (.13, .1), (.12, .1), (.095, .05), (.05, .01), (0, .01)], (.92, -.1, SZ), P['red'], seg=18, group='Detail_Goods')
    for k in range(6):
        a = k * 1.1
        cyl_c = Vector((.92 + math.cos(a) * .04, -.1 + math.sin(a) * .04, SZ + .03)); d = Vector((math.cos(a) * .08, math.sin(a) * .08, .3))
        rope('Scroll', [tuple(cyl_c), tuple(cyl_c + d)], .018, P['scroll'], ply=1, tw=0., seg=8, amp=0., group='Detail_Goods')
    def cloth(a, b, mat):
        def fn(u, v):
            x = a + (b - a) * u; t = v * 1.; edge = -BY - .07
            hemz = .56 - .035 * math.sin(x * 11) - .012 * math.sin(x * 29)
            if t < .4:
                k = t / .4
                return (x, -.22 + (edge + .22) * k, CZ + .04)
            k = (t - .4) / .6; rr = min(1., k * 3.); ang = rr * math.pi / 2
            return (x, edge - .025 * math.sin(ang) - .012 * math.sin(x * 8) * k, CZ + .04 - .025 * (1 - math.cos(ang)) - (CZ - hemz) * k)
        sheet('Counter_Cloth', max(2, int((b - a) * 14)), 12, fn, mat, solid=.003, grain='z')
    for a, b, m in ((-.3, .05, 'red'), (.05, .3, 'yellow'), (.3, .78, 'red')):
        cloth(a, b, P[m])
    # the stool with its shop-worn cushion, out front
    SX, SY = .55, -.86
    rbox('Stool_Top', (SX, SY, .36), (.3, .26, .035), P['old'], r=.006, amp=.003, seed=44, div=.08, group='Stool', grain='x')
    for sx in (-1, 1):
        for sy in (-1, 1):
            between('Stool_Leg', (SX + sx * .115, SY + sy * .09, .345), (SX + sx * .135, SY + sy * .1, 0), .04, .04, P['old'], r=.005, seed=int(sx * 2 + sy + 4), div=.07, group='Stool')
        rbox('Stool_Rail', (SX, SY + sx * .09, .13), (.24, .025, .03), P['old'], r=.004, seed=sx + 3, div=.07, group='Stool', grain='x')
    def cush(u, v):
        a = u * math.tau; r = v
        return (SX + math.cos(a) * r * .16, SY + math.sin(a) * r * .125, .378 + .075 * (1 - r * r) ** .55 + .008 * noise.noise(Vector((math.cos(a) * r * 3, math.sin(a) * r * 3, 0))))
    surface('Cushion', 22, 8, cush, P['cushion'], closed_u=True, grain='z', group='Stool')
    surface('Cushion_Patch', 12, 4, lambda u, v: (SX + .05 + math.cos(u * math.tau) * v * .06, SY - .02 + math.sin(u * math.tau) * v * .05, .378 + .075 * (1 - min(1., (.31 + v * .38)) ** 2) ** .55 + .004), P['yellow'], closed_u=True, grain='z', group='Stool', detail=1)
    # the big bell on its arm, past the right post
    rbox('Bell_Arm', (BX + .2, -.44, 1.56), (.44, .05, .05), P['old'], r=.006, seed=9, div=.1, grain='x')
    lathe('Big_Bell', [(0, 0), (.1, 0), (.105, .01), (.075, .1), (.03, .14), (0, .15)], (BX + .34, -.44, 1.34), P['bell'], seg=20)
    rope('Bell_Cord', [(BX + .34, -.44, 1.54), (BX + .34, -.44, 1.49)], .005, P['thread'], ply=1, tw=0., seg=5, amp=0., detail=1)
    for k, dx in enumerate((-.04, .04)):
        lathe('Small_Bell', [(0, 0), (.028, 0), (.03, .006), (.02, .035), (.007, .048), (0, .048)], (BX + .34 + dx, -.44, 1.22), P['bell'], seg=10, detail=1)
        rope('Bell_Tassel', [(BX + .34 + dx, -.44, 1.22), (BX + .34 + dx, -.44, 1.1)], .008, P['thread'], ply=1, tw=0., seg=5, amp=0., radius_fn=lambda t: .5 + .7 * t, detail=1)
    # the crooked banner: a rough pole lashed to the ridge end, a branch across, plain torn cloth, nothing written on it
    base = (-1.42, 0, RIDGE + .02); top = (-1.14, 0, 2.78)
    log('Banner_Pole', [base, ((base[0] + top[0]) / 2, 0, (base[2] + top[2]) / 2), top], .022, P['old'], seg=8, lump=.05, seed=8, grain='z')
    lash('Pole_Tie', (-1.4, 0, RIDGE + .08), (0, 0, 1), .03, .09, .006, P['thread'], turns=5, detail=1)
    lash('Pole_Tie', (-1.19, 0, 2.68), (0, 0, 1), .03, .08, .006, P['thread'], turns=5, detail=1)
    log('Banner_Arm', [(-1.3, 0, 2.69), (-.6, -.01, 2.66), (.05, 0, 2.7), (.42, 0, 2.74)], .012, P['old'], seg=8, lump=.05, seed=5, grain='x')
    arm = lambda x: 2.69 + (x + 1.3) * .03 * (1 if x > -.3 else -.8)
    def bn(u, v):
        x = -1.22 + u * 1.56; zt = arm(x) - .015; bot = 2.38 + .05 * abs(math.sin(u * 23)) * abs(math.sin(u * 61 + 1)) + .04 * abs(noise.noise(Vector((u * 14, 2, 0)))) + max(0., u - .84) * 1.5
        return (x, .012 * math.sin(u * 13 + v * 3) * (1 - v), bot + (zt - bot) * v)
    sheet('Banner', 70, 8, bn, P['banner'], solid=.0018, grain='z', group='Banner', keep=lambda u, v: not (.68 < u < .74 and .1 < v < .35))
    sheet('Banner_Patch', 4, 4, lambda u, v: (-1.14 + u * .2, -.003, 2.44 + v * .13 + .01 * math.sin(u * 7)), P['patch'], solid=.0015, grain='z', group='Banner', detail=1)
    for x in (-1.0, -.55, -.1, .25):
        lash('Cloth_Tie', (x, 0, arm(x) - .005), (1, 0, 0), .016, .03, .004, P['thread'], turns=3, group='Banner', detail=1)
    S['collision'] = [((-BX - .1, -BY - .08, 0), (BX + .1, BY + .08, CZ + .03)), ((-BX - .02, .39, CZ), (BX + .02, .49, 1.9)), ((WX - .47, -BY - .13, 0), (WX + .47, -BY - .01, .94)), ((WX - .47, BY + .01, 0), (WX + .47, BY + .13, .94))]


# ------------------------------------------------------------------ CR11 noodle stall
def noodle_palette():
    P = {'post': cm.wood('Round_Post', (.05, .03, .017), (.2, .125, .065), ground_h=.15, grey=.2), 'beam': cm.wood('Smoked_Beam', (.04, .025, .015), (.16, .1, .055), ground_h=0, grey=.15), 'board': cm.wood('Worn_Table', (.1, .06, .03), (.34, .22, .11), ground_h=0, polish=.3, grey=.12), 'bench': cm.wood('Bench_Plank', (.08, .048, .025), (.28, .17, .09), ground_h=.1, grey=.25), 'wall': cm.wood('Wall_Plank', (.055, .035, .02), (.2, .13, .075), ground_h=.15, grey=.35)}
    P['canvas'] = cm.canvas('Awning', base=(.19, .145, .085), stain=(.09, .062, .035), faded=.04, dirt=1.); P['blue'] = cm.canvas('Awning_Blue', base=(.09, .088, .078), stain=(.05, .046, .038), faded=.03, dirt=.7); P['rust'] = cm.canvas('Awning_Rust', base=(.085, .05, .034), stain=(.05, .032, .022), faded=.03, dirt=.6)
    P['brick'] = [cm.stone(f'Stove_Brick_{i}', light=l, dark=tuple(c * .42 for c in l), ochre=tuple(c * .8 for c in l), moss=.15, crack=.3, lichen=0) for i, l in enumerate(((.36, .17, .1), (.28, .15, .1), (.24, .19, .14)))]
    P['clay'] = cm.stone('Stove_Mud', light=(.2, .15, .1), dark=(.06, .045, .035), ochre=(.14, .1, .06), moss=0, crack=.8, lichen=0); P['iron'] = mm.cast_iron('Pot_Iron'); P['fire'] = tm.emissive('Stove_Fire', (.04, .03, .025), (1., .45, .12), 'Main'); P['soot'] = tm.plain('Soot', (.025, .022, .02), rough=.95, noise=.1)
    P['bowl'] = cm.clay('Coarse_Bowl', body=(.5, .46, .36), glaze=(.36, .32, .24)); P['leaf'] = tm.plain('Bowl_Leaf', (.1, .2, .2), rough=.5, noise=.2); P['noodle'] = tm.plain('Noodles', (.68, .55, .28), rough=.5, noise=.1); P['broth'] = tm.plain('Broth', (.26, .16, .05), rough=.2, noise=.1); P['scallion'] = tm.plain('Scallion', (.14, .3, .06), rough=.6, noise=.2); P['meat'] = tm.plain('Braised_Meat', (.22, .09, .05), rough=.45, noise=.2); P['flour'] = tm.plain('Flour_Dust', (.6, .57, .5), rough=.95, noise=.12)
    P['culm'] = cm.culm('Stall_Bamboo', green=(.12, .13, .05), straw=(.32, .25, .11), mud_h=.3); P['hemp'] = mm.hemp('Hemp_Rope', (.25, .165, .08), twist=40.0); P['sign'] = cm.canvas('Cloth_Sign', base=(.62, .54, .37), stain=(.34, .26, .15), faded=.3, dirt=.6); P['dip'] = mm.bamboo('Ladle_Bamboo')
    P['stone'] = cm.stone('Base_Stone', light=(.33, .31, .26), dark=(.16, .15, .12), moss=.5, lichen=.2); P['jar'] = cm.clay('Store_Jar', body=(.16, .1, .06), glaze=(.08, .055, .035)); P['grass'] = cm.moss_tuft('Foot_Grass', soft=True)
    return P


def bowl(P, name, q, full=False, group=None):
    prof = [(0, 0), (.05, 0), (.052, .01), (.046, .016), (.075, .04), (.095, .068), (.102, .082), (.097, .083), (.088, .068), (.065, .04), (.04, .022), (0, .018)]
    lathe(name, prof, q, P['bowl'], seg=24, group=group)
    for a0 in (2.0, 5.1):        # a plain brushed leaf on the side, no writing
        def lf(u, v, a0=a0):
            a = a0 + (v - .5) * .9; h = .05 + (u - .5) * .018 * math.sin(v * 3.14) + (v - .5) * .02; r = .078 + (h - .05) * .9 + .0018
            return (q[0] + math.cos(a) * r, q[1] + math.sin(a) * r, q[2] + h)
        sheet(name + '_Leaf', 2, 5, lf, P['leaf'], solid=.0006, group=group, detail=1)
    if full:
        lathe(name + '_Broth', [(0, .06), (.089, .06)], q, P['broth'], seg=24, group=group)
        R = random.Random(int(abs(q[0]) * 100))
        for k in range(7):
            a = R.uniform(0, 6.28)
            pts = [(q[0] + math.cos(a + t * 3.2) * (.016 + t * .058), q[1] + math.sin(a + t * 3.2) * (.016 + t * .058), q[2] + .064 + .003 * math.sin(t * 9)) for t in [j / 7 for j in range(8)]]
            rope('Noodle', pts, .0042, P['noodle'], ply=1, tw=0., seg=5, amp=0., curve=3, step=.02, group=group)
        for k in range(3):
            rbox('Meat', (q[0] - .012 + k * .026, q[1] + .022, q[2] + .072), (.022, .06, .012), P['meat'], r=.003, amp=.001, seed=k, div=.02, group=group, rot=(0, 0, .25), detail=1)
        for k in range(6):
            a = R.uniform(0, 6.28); r = R.uniform(.01, .06)
            sphere('Scallion', (q[0] + math.cos(a) * r, q[1] + math.sin(a) * r, q[2] + .07), .006, P['scallion'], scale=(1, 1, .7), seg=6, ring=4, group=group, detail=1)


def weave(P, name, x0, x1, y0, y1, z0, z1, n, m):
    """A panel of split bamboo strips, verticals behind, horizontals in front; runs from (x0, y0) to (x1, y1)."""
    L = Vector((x1 - x0, y1 - y0, 0)); nrm = Vector((L.y, -L.x, 0)).normalized()
    along_x = abs(x1 - x0) > .01
    for i in range(n):
        q = Vector((x0, y0, 0)) + L * ((i + .5) / n); w = L.length / n * .86
        rbox(name, (q.x, q.y, (z0 + z1) / 2), (w, .012, z1 - z0) if along_x else (.012, w, z1 - z0), P['dip'], r=.002, div=.3, detail=1, seed=i, grain='z')
    for j in range(m):
        z = z0 + (j + .5) / m * (z1 - z0); off = nrm * .007; h = (z1 - z0) / m * .84
        rbox(name, ((x0 + x1) / 2 + off.x, (y0 + y1) / 2 + off.y, z), (L.length, .012, h) if along_x else (.012, L.length, h), P['dip'], r=.002, div=.3, detail=1, seed=j, grain='x' if along_x else 'y')


def cr11(P):
    PX, PYF, PYR = 1.98, -1.52, 1.46; front, rear = 2.1, 2.56
    def rz(y): return front + (y - PYF) / (PYR - PYF) * (rear - front)
    # round rough posts, tied with rope: front lower than rear, a one-slope lean-to falling to the front
    posts = ((-PX, PYF, front), (PX, PYF, front), (-PX, PYR, rear), (PX, PYR, rear), (0, PYR, rear), (-PX, .1, rz(.1)))
    for k, (x, y, h) in enumerate(posts):
        log('Post', [(x, y, 0), (x + .008 * math.sin(k), y, h * .5), (x, y, h + .05)], .07 if k < 2 else .058, P['post'], seg=14, lump=.08, seed=k, grain='z')
    # the left front post stands on a little stack of stones
    for k, (dx, dy, z, s) in enumerate(((.12, -.08, .05, 1.), (-.1, -.12, .05, .85), (.03, -.13, .13, .7))):
        rbox('Prop_Stone', (-PX + dx, PYF + dy, z), (.16 * s, .13 * s, .1 * s), P['stone'], r=.02, amp=.012, chips=2, seed=k + 3, div=.05)
    for k, (y, h) in enumerate(((PYF, front), (PYR, rear))):
        log('Beam', [(-PX - .2, y, h - .02), (0, y, h - .035), (PX + .2, y, h - .02)], .058, P['beam'], seg=12, lump=.05, seed=k + 8, grain='x')
    for x in (-PX, -PX / 2, 0, PX / 2, PX):
        log('Rafter', [(x, PYR + .1, rz(PYR + .1) + .06), (x, PYF - .16, rz(PYF - .16) + .06)], .042, P['beam'] if abs(x) < PX else P['post'], seg=10, lump=.05, seed=int(x * 5 + 11), grain='y')
        lash('Rafter_Lash', (x, PYF, rz(PYF) + .03), (1, 0, 0), .05, .1, .007, P['hemp'], turns=6, detail=1)
        lash('Rafter_Lash', (x, PYR, rz(PYR) + .03), (1, 0, 0), .05, .1, .007, P['hemp'], turns=6, detail=1)
    for y in (-.8, .2, 1.):
        log('Purlin', [(-PX - .08, y, rz(y) + .07), (PX + .08, y, rz(y) + .07)], .022, P['culm'], seg=8, lump=.01, seed=int(y * 9 + 7), grain='x')
    for sx in (-1, 1):
        between('Brace', (sx * PX, PYF, front - .52), (sx * PX, PYF + .5, front - .03), .06, .06, P['post'], r=.008, amp=.003, seed=sx + 3, div=.12)
        between('Brace', (sx * (PX - .45), PYF, front - .03), (sx * PX, PYF, front - .5), .05, .05, P['post'], r=.006, amp=.003, seed=sx + 5, div=.12)
    # the awning: old cream canvas, blue panels and a rust patch sewn on, torn along the front
    def tz(x, y): return rz(y) + .17 - .058 * math.sin(abs(x) * math.pi / .99) ** 2 - .012 * math.sin(y * 5.2 + x * 1.3) ** 2 + .009 * noise.noise(Vector((x * 5, y * 2.2, 2.)))
    def awn(u, v):
        x = (u - .5) * (2 * PX - .12); y = PYF - .19 + v * (PYR - PYF + .29)
        return (x, y, min(2.79, tz(x, y) + .006 * math.sin(x * 7 + y * 3)))
    sheet('Awning', 60, 30, awn, P['canvas'], solid=.005, grain='y')
    for j, (x0, y0, w, h, m) in enumerate(((-1.72, -.42, .72, .78, 'blue'), (.62, -1.28, .74, .62, 'blue'), (1.02, .62, .56, .48, 'rust'))):
        def pat(u, v, x0=x0, y0=y0, w=w, h=h):
            # hand-cut cloth: no edge is straight
            x = x0 + u * w + .035 * math.sin(v * 7 + x0 * 5) * (abs(u - .5) * 2); y = y0 + v * h + .03 * math.sin(u * 8 + y0 * 3) * (abs(v - .5) * 2)
            return (x, y, min(2.793, tz(x, y) + .006 * math.sin(x * 7 + y * 3) + .009))
        sheet('Awning_Patch', 14, 14, pat, P[m], solid=.002, grain='y')
        # big uneven stitches round it, in hemp
        for side, count in ((0, int(w / .085)), (1, int(w / .085)), (2, int(h / .085)), (3, int(h / .085))):
            for c in range(count):
                t = (c + .5) / count; uv = {0: (t, .012), 1: (t, .988), 2: (.012, t), 3: (.988, t)}[side]; out = {0: (0, -.03), 1: (0, .03), 2: (-.03, 0), 3: (.03, 0)}[side]
                p0 = pat(*uv); x1, y1 = p0[0] + out[0], p0[1] + out[1]
                rope('Patch_Stitch', [(p0[0] - out[0] * .3, p0[1] - out[1] * .3, p0[2] + .005), (x1, y1, tz(x1, y1) + .012)], .0028, P['hemp'], ply=1, tw=0., seg=3, amp=0., group='Detail_Stitches', detail=1)
    for x in (-PX / 2, 0, PX / 2):      # tied down along the rafters
        rope('Awning_Tie', [(x, PYF - .1 + t * (PYR - PYF + .1), tz(x, PYF - .1 + t * (PYR - PYF + .1)) + .012) for t in [j / 8 for j in range(9)]], .008, P['hemp'], curve=2, step=.08, detail=1)
    # the torn flap that hangs over the front beam
    def flap(u, v):
        x = (u - .5) * (2 * PX - .14); drop = (.15 + .035 * noise.noise(Vector((u * 11, 3, 0))) + .012 * noise.noise(Vector((u * 50, 1, 0)))) * (1 - .72 * max(math.exp(-((u - t) / .011) ** 2) for t in (.17, .46, .49, .81))); return (x, PYF - .17 - .012 * math.sin(x * 8) * (1 - v), rz(PYF - .17) + .13 - (1 - v) * drop + .02 * math.sin(x * 11))
    sheet('Awning_Flap', 110, 3, flap, P['canvas'], solid=.003, grain='z')
    # the rear wall: vertical boards with a band of woven bamboo; a stone footing
    R = random.Random(11)
    x = -PX
    while x < PX - .02:
        w = min(R.uniform(.16, .28), PX - x); xc = x + w / 2
        top = rz(PYR) - .1
        rbox('Wall_Plank', (xc, PYR + .03, top / 2 + .07), (w - .012, .035, top - .14), P['wall'], r=.005, amp=.004, chips=2, seed=R.randint(1, 900), div=.25, grain='z')
        x += w
    for x0, x1 in ((-.9, -.1), (.1, .9)):
        weave(P, 'Rear_Weave', x0, x1, PYR + .06, PYR + .06, .78, 1.72, 11, 13)
    for z in (.3, .76, 1.74, 2.3):
        log('Wall_Rail', [(-PX, PYR + .075, z), (PX, PYR + .075, z)], .02, P['culm'], seg=8, lump=.01, seed=int(z * 7), grain='x')
    for k in range(14):
        rbox('Foot_Stone', (-PX + .15 + k * .29, PYR + .03, .07), (.28, .14, .14), P['stone'], r=.02, amp=.01, chips=1, seed=k, div=.06)
    # the two end screens, only over the rear half
    for sx, y0 in ((-1, .1), (1, .45)):
        xw = sx * PX
        for z in (.3, 1.05, 1.75):
            log('Side_Rail', [(xw, y0, z), (xw, PYR, z)], .02, P['culm'], seg=8, lump=.01, seed=int(z * 9 + sx), grain='y')
        weave(P, 'Side_Weave', xw, xw, y0 + .03, PYR - .03, .32, 1.73, int((PYR - y0) * 13), 16)
    between('Side_Brace', (PX + .03, .5, .1), (PX + .03, PYR - .05, 1.72), .06, .04, P['post'], r=.006, amp=.003, seed=2, div=.15)
    # the stove on the right, red and grey brick round an arched fire mouth
    SX, SY, SW, SD, SH = 1.2, .95, 1.1, .85, .74
    course = .092; rows = int(SH / course); FM, FR = .2, .17
    rbox('Stove_Core', (SX, SY, SH / 2), (SW - .03, SD - .03, SH), P['clay'], r=.01, seed=3, div=.2)
    for r_ in range(rows):
        z = r_ * course + course / 2
        for sy, y in ((-1, SY - SD / 2), (1, SY + SD / 2)):
            x = SX - SW / 2 - (r_ % 2) * .09
            while x < SX + SW / 2 - .01:
                x1 = min(x + .24, SX + SW / 2); xa = max(x, SX - SW / 2); xm = (xa + x1) / 2
                inside = sy < 0 and abs(xm - SX) < FM + .14 and z < FR + FM + .12
                if not inside and x1 - xa > .03:
                    rbox('Brick', (xm, y, z), (x1 - xa - .006, .06, course - .006), P['brick'][R.randrange(3)], r=.006, amp=.003, chips=1, seed=R.randint(1, 900), div=.09)
                x += .24
        for sx, x in ((-1, SX - SW / 2), (1, SX + SW / 2)):
            y = SY - SD / 2 - (r_ % 2) * .09
            while y < SY + SD / 2 - .01:
                y1 = min(y + .24, SY + SD / 2); ya = max(y, SY - SD / 2)
                if y1 - ya > .03:
                    rbox('Brick', (x, (ya + y1) / 2, z), (.06, y1 - ya - .006, course - .006), P['brick'][R.randrange(3)], r=.006, amp=.003, chips=1, seed=R.randint(1, 900), div=.09)
                y += .24
    fy = SY - SD / 2 - .012
    rbox('Fire_Back', (SX, fy + .012, FR + .08), (2 * FM + .14, .02, 2 * FM + .16), P['soot'], r=.002, div=.2)
    rbox('Fire_Bed', (SX, fy, .12), (.3, .012, .14), P['fire'], r=.004, seed=4, div=.05)
    for k in range(9):      # the arch, and the jambs under it
        a = k / 8 * math.pi; c = (SX + math.cos(a) * (FM + .05), fy, FR + math.sin(a) * (FM + .05))
        rbox('Arch_Brick', c, (.1, .07, .058), P['brick'][k % 3], r=.005, amp=.002, seed=k, div=.05, rot=(0, -a + math.pi / 2, 0))
    for sx in (-1, 1):
        for j in range(3):
            rbox('Jamb_Brick', (SX + sx * (FM + .05), fy, .03 + j * .058), (.1, .07, .054), P['brick'][(j + 1) % 3], r=.005, amp=.002, seed=j, div=.05)
    for k in range(3):
        log('Fire_Log', [(SX - .12 + k * .12, fy - .1, .05 + k % 2 * .02), (SX - .09 + k * .09, fy + .08, .08)], .028, P['post'], seg=8, lump=.05, seed=k, grain='y')
    rbox('Stove_Slab', (SX, SY, SH + .012), (SW + .06, SD + .06, .03), P['clay'], r=.008, amp=.002, seed=8, div=.1)
    for k, (dx, dy) in enumerate(((-.48, -.33), (.47, -.3), (.5, .28))):
        rbox('Loose_Brick', (SX + dx, SY + dy, SH + .06), (.17, .09, .06), P['brick'][k], r=.006, amp=.003, chips=1, seed=k + 80, div=.05, rot=(0, 0, .15 * k))
    # the big iron pot, broth steaming: Socket_Steam
    PZ = SH + .025
    lathe('Pot', [(0, 0), (.12, 0), (.25, .05), (.33, .16), (.35, .28), (.385, .3), (.385, .325), (.34, .325), (.32, .17), (.24, .08), (.11, .03), (0, .03)], (SX, SY, PZ), P['iron'], seg=40)
    lathe('Pot_Broth', [(0, .25), (.335, .25)], (SX, SY, PZ), P['broth'], seg=40)
    for sx in (-1, 1):
        torus('Pot_Lug', (SX + sx * .4, SY, PZ + .3), .035, .009, P['iron'], rot=(math.pi / 2, 0, 0), major=12, minor=5)
    socket('Socket_Steam', (SX, SY, PZ + .3))
    cyl('Flue', (SX + .42, SY + .32, 1.65), .07, 1.8, P['soot'], verts=14, bevel=.004, grain='z')
    # the prep table with its board, floured, a hank of noodles and a cleaver
    TX, TY = -.2, 1.0
    rbox('Prep_Top', (TX, TY, .82), (1.32, .66, .06), P['board'], r=.012, amp=.004, chips=2, seed=20, div=.2, grain='x')
    for sx in (-1, 1):
        for sy in (-1, 1):
            rbox('Prep_Leg', (TX + sx * .58, TY + sy * .26, .4), (.08, .08, .8), P['post'], r=.008, seed=int(sx * 3 + sy + 21), div=.15, grain='z')
    rbox('Prep_Shelf', (TX, TY, .3), (1.2, .55, .03), P['bench'], r=.006, seed=25, div=.2, grain='x')
    for j, (dx, dy, r) in enumerate(((-.2, .05, .2), (.1, -.08, .15), (.3, .12, .12))):
        def fl(u, v, dx=dx, dy=dy, r=r, j=j):
            a = u * math.tau; rr = r * v * (.8 + .3 * noise.noise(Vector((math.cos(a) * 2 + j, math.sin(a) * 2, 0))))
            return (TX + dx + math.cos(a) * rr, TY + dy + math.sin(a) * rr, .8515 + .001 * (1 - v))
        surface('Flour', 20, 3, fl, P['flour'], closed_u=True, group='Detail_Flour')
    for h, (cx, cy) in enumerate(((TX - .2, TY + .02), (TX + .28, TY - .02))):
        for k in range(14):
            y = cy - .11 + k * .017
            pts = [(cx - .2 + t * .4, y + .008 * math.sin(t * 8 + k), .858 + .006 * (k % 3) + .02 * math.sin(t * 3.14) * (1 - abs(k - 7) / 8)) for t in [j / 6 for j in range(7)]]
            rope('Noodle_Hank', pts, .0052, P['noodle'], ply=1, tw=0., seg=5, amp=0., curve=3, step=.03, group='Detail_Noodles')
    rbox('Cleaver', (TX + .54, TY + .05, .86), (.09, .2, .008), P['iron'], r=.002, div=.05, rot=(0, 0, .25), detail=1)
    log('Cleaver_Grip', [(TX + .52, TY + .15, .862), (TX + .495, TY + .25, .862)], .012, P['bench'], seg=6, lump=.01, grain='y', detail=1)
    # shelves on the left of the back wall, with stacked bowls; ladles and a rag hung on a rail
    for z in (1.02, 1.46):
        rbox('Shelf', (-1.3, 1.26, z), (1.3, .36, .03), P['bench'], r=.006, amp=.003, seed=int(z * 9), div=.2, grain='x')
        for sx in (-1, 1):
            between('Shelf_Bracket', (-1.3 + sx * .55, PYR, z - .2), (-1.3 + sx * .55, 1.12, z - .02), .035, .035, P['post'], r=.005, seed=sx + 3, div=.08)
    for k, (x, y, z, n) in enumerate(((-1.72, 1.27, 1.035, 3), (-1.32, 1.27, 1.035, 4), (-.9, 1.27, 1.035, 2), (-1.68, 1.27, 1.475, 4), (-1.26, 1.27, 1.475, 3), (-.86, 1.27, 1.475, 3))):
        for j in range(n):
            lathe('Stack_Bowl', [(0, 0), (.05, 0), (.075, .03), (.102, .08), (.095, .082), (.07, .04), (.04, .02), (0, .018)], (x, y, z + j * .034), P['bowl'], seg=14, group='Detail_Bowls')
    log('Ladle_Rail', [(-.45, 1.36, 1.72), (.6, 1.36, 1.72)], .014, P['culm'], seg=8, lump=.01, grain='x')
    for k, x in enumerate((-.3, -.05, .2)):
        with xf(T(x, 1.32, 1.72 - .46)):
            dipper('Hung_Ladle', (0, 0, 0), (0, 0, 1), P['dip'], group='Detail_Ladles')
    def rag(u, v):
        return (.45 + (u - .5) * .16, 1.33 + .012 * math.sin(u * 9), 1.7 - (1 - v) * .42)
    sheet('Hung_Rag', 4, 7, rag, P['sign'], solid=.002, grain='z', keep=lambda u, v: v > .05 or u > .3, group='Detail_Ladles')
    # store jars and a little tub at the left
    for k, (x, y, s) in enumerate(((-1.62, .62, 1.), (-1.68, .2, .78))):
        lathe('Store_Jar', [(0, 0), (.13 * s, 0), (.2 * s, .13 * s), (.22 * s, .26 * s), (.17 * s, .42 * s), (.11 * s, .48 * s), (.12 * s, .52 * s), (0, .52 * s)], (x, y, 0), P['jar'], seg=22)
    lathe('Tub', [(0, 0), (.18, 0), (.2, .3), (.17, .3), (.16, .02), (0, .02)], (-1.0, .72, 0), P['bench'], seg=20)
    for z in (.06, .24):
        torus('Tub_Hoop', (-1.0, .72, z), .187 + z * .05, .008, P['hemp'], major=24, minor=5, detail=1)
    # the customer table in the middle: four boards on four legs, chopsticks in a bamboo cup
    QX, QY = 0., -.55; QZ = .78
    for k in range(4):
        rbox('Table_Top', (QX - .42 + k * .28, QY, QZ - .022), (.27, .96, .044), P['board'], r=.01, amp=.004, chips=2, seed=30 + k, div=.15, grain='y')
    for sx in (-1, 1):
        for sy in (-1, 1):
            rbox('Table_Leg', (QX + sx * .46, QY + sy * .38, (QZ - .044) / 2), (.08, .08, QZ - .044), P['post'], r=.008, amp=.003, seed=int(sx * 3 + sy + 31), div=.15, grain='z')
        rbox('Table_Rail', (QX, QY + sx * .38, QZ - .1), (.86, .03, .08), P['post'], r=.005, seed=sx + 40, div=.15, grain='x')
        rbox('Table_Rail', (QX + sx * .46, QY, QZ - .1), (.03, .7, .08), P['post'], r=.005, seed=sx + 42, div=.15, grain='y')
    # two benches, one with a short leg set on stones
    for sx, g, prop in ((-1, 'Bench_Front', True), (1, 'Bench_Back', False)):
        bx = QX + sx * 1.0
        for j in (-1, 1):
            rbox('Bench_Seat', (bx + j * .065, QY, .445), (.125, 1.25, .05), P['bench'], r=.01, amp=.004, chips=2, seed=j + sx + 50, div=.15, group=g, grain='y')
        for sy in (-1, 1):
            short = prop and sy < 0
            rbox('Bench_Leg', (bx, QY + sy * .46, (.42 + (.12 if short else 0)) / 2), (.2, .07, .42 - (.12 if short else 0)), P['bench'], r=.008, amp=.003, seed=int(sx + sy + 54), div=.1, group=g, grain='z')
            if short:
                for k, (dz, s) in enumerate(((.03, 1.), (.09, .75))):
                    rbox('Bench_Prop', (bx, QY + sy * .46, dz), (.2 * s, .14 * s, .06), P['stone'], r=.012, amp=.006, chips=2, seed=k + 4, div=.05, group=g)
        rbox('Bench_Rail', (bx, QY, .24), (.04, .86, .05), P['bench'], r=.005, seed=sx + 57, div=.12, group=g, grain='y')
    # one bowl full, one empty, each its own object; chopsticks in a cup
    bowl(P, 'Bowl', (QX - .22, QY - .22, QZ), full=True, group='Bowl_Full'); bowl(P, 'Bowl', (QX + .26, QY + .2, QZ), group='Bowl_Empty')
    lathe('Chop_Cup', [(0, 0), (.05, 0), (.052, .13), (.046, .13), (.046, .008), (0, .008)], (QX, QY, QZ), P['dip'], seg=14, group='Detail_Chopsticks')
    for k in range(9):
        a = k * .8; d = Vector((math.cos(a) * .035, math.sin(a) * .035, .24)).normalized()
        q = Vector((QX + math.cos(a) * .014, QY + math.sin(a) * .014, QZ + .012))
        rope('Chopstick', [tuple(q), tuple(q + d * .24)], .0035, P['bench'], ply=1, tw=0., seg=4, amp=0., group='Detail_Chopsticks', detail=1)
    # a plain cloth sign on a short bamboo arm, off the front left post; torn at the hem, no text
    log('Sign_Arm', [(-PX - .02, PYF, 1.82), (-PX + .56, PYF, 1.82)], .014, P['culm'], seg=8, lump=.01, grain='x', group='Sign')
    lash('Arm_Tie', (-PX + .03, PYF, 1.82), (0, 0, 1), .08, .08, .007, P['hemp'], turns=5, group='Sign', detail=1)
    def sg(u, v):
        drop = .62 + .05 * abs(math.sin(u * 23)) + .05 * abs(math.sin(u * 53)) + .02 * noise.noise(Vector((u * 30, 1, 0))); return (-PX + .1 + u * .42, PYF - .012 + .015 * math.sin(u * 7 + v * 2) * (1 - v), 1.8 - (1 - v) * drop)
    sheet('Cloth_Sign', 40, 8, sg, P['sign'], solid=.002, grain='z', group='Sign')
    for k, (x, y) in enumerate(((-2.1, -1.68), (2.1, -1.66), (2.08, 1.55), (-2.1, .15))):
        tuft('Foot_Grass', (x, y, 0), .09, P['grass'], seed=k + 3)
    S['collision'] = [((SX - SW / 2, SY - SD / 2, 0), (SX + SW / 2, SY + SD / 2, 1.1)), ((TX - .66, TY - .33, 0), (TX + .66, TY + .33, .85)), ((QX - .5, QY - .48, 0), (QX + .5, QY + .48, QZ)), ((QX - 1.1, QY - .62, 0), (QX - .9, QY + .62, .47)), ((QX + .9, QY - .62, 0), (QX + 1.1, QY + .62, .47)), ((-PX, PYR, 0), (PX, PYR + .08, rear))] + [((x - .07, y - .07, 0), (x + .07, y + .07, h)) for x, y, h in posts]
