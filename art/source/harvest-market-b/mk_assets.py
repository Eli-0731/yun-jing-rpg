"""MK01 steelyard, MK02 harvest sieve + three herb grades, MK03 price board + coins, MK04 back basket.

Shapes follow the selected AI three-views (art/references/MK0N/v002/selected.png) and the work-pack size
limits in 02-B 2.1–2.4. Blender Z-up, 1 unit = 1 m, front -Y. Builders place parts around the origin; the
pipeline re-centres afterwards (MK04 then moves its origin onto the back-contact face, as the work pack asks).
"""
import math, random
from mathutils import Vector, Matrix
from ti_core import S, box, cyl, sphere, torus, lathe, surface, tube, mesh, boolean, socket, rng
import ti_mats as tm
import mk_mats as mm
import mk_herbs as hb


def palette():
    P = {}
    P['beam'] = mm.painted_wood('Beam_Hardwood', (.035, .018, .01), (.13, .07, .035), ground_h=0, polish=.22, moss=False)
    P['brass'] = mm.brass('Brass')
    P['iron'] = mm.cast_iron('Weight_Iron')
    P['hemp'] = mm.hemp('Hemp_Cord', (.17, .11, .05))
    P['twine'] = mm.hemp('Hemp_Twine', (.2, .14, .065), twist=220.0)
    P['strap'] = mm.hemp('Strap_Braid', (.1, .058, .03), twist=70.0)
    P['weave'] = mm.weave('Bamboo_Weave', (.26, .17, .07), (.1, .065, .028), reed=.006, block=.024)
    P['weave_sieve'] = mm.weave('Sieve_Weave', (.25, .16, .06), (.09, .058, .022), reed=.0045, block=.018, green_cast=.55)
    P['weave_patch'] = mm.weave('Patch_Weave', (.15, .13, .095), (.06, .05, .034), reed=.005, block=.02)
    P['weave_basket'] = mm.weave('Basket_Weave', (.37, .21, .075), (.17, .095, .035), reed=.016, block=.03, plain=True, green_cast=.04, ground_h=.045, sweat=.3)
    P['strap_braid'] = mm.weave('Strap_Weave', (.17, .1, .05), (.06, .035, .018), reed=.0045, block=.009, sweat=.3)
    P['bamboo_warm'] = mm.bamboo('Split_Bamboo_Warm', green=(.1, .07, .025), straw=(.34, .19, .07))
    P['bamboo'] = mm.bamboo('Split_Bamboo')
    P['bamboo_old'] = mm.bamboo('Split_Bamboo_Old', green=(.09, .085, .05), straw=(.3, .24, .14), ground_h=.06)
    P['timber'] = mm.painted_wood('Old_Timber', (.07, .042, .022), (.24, .155, .085))
    P['pine'] = mm.painted_wood('Weathered_Pine', (.045, .027, .015), (.16, .1, .055), ground_h=.0, chalk=((.05, -.03, .36), .16), moss=False)
    P['pine_tag'] = mm.painted_wood('Tag_Pine', (.08, .05, .028), (.22, .15, .085), ground_h=.0, moss=False)
    P['nail'] = tm.metal('Nail_Iron', (.06, .055, .05), (.13, .07, .035), rough=.55, patina_amt=.6)
    P['coin'] = mm.bronze_coin('Coin_Bronze')
    P['indigo'] = mm.cloth('Indigo_Cotton', (.025, .033, .065), worn=.5)
    P['indigo_patch'] = mm.cloth('Indigo_Patch', (.05, .055, .07), worn=.3)
    P['cord_red'] = mm.hemp('Coin_Cord', (.2, .07, .04), twist=260.0)
    P['soil'] = mm.soil('Soil')
    P['root'] = mm.root('Root')
    P['stem'] = mm.stem('Herb_Stem')
    P['leaf_top'] = mm.leaf('Leaf_Top', 'top', slot='Glow')
    P['leaf_mid'] = mm.leaf('Leaf_Mid', 'mid')
    P['leaf_low'] = mm.leaf('Leaf_Low', 'low')
    return P


def wuv(o, fn):
    """Per-vertex weave coordinates (metres) for mk_mats.weave."""
    hb.set_attr(o, 'wuv', lambda co: (*fn(co), 0.0))


# ================================================================ MK01 桿秤
BEAM_Z = .47           # beam axis height; pan bottom at 0, hook top just under 0.6
FULCRUM_X = -.30       # fulcrum / pan hang point near the thick end
WEIGHT_X0 = -.22       # counterweight rest; slides +0.5 m along the beam (local X 0–0.5)


def mk01_steelyard(P):
    beam, brass, iron, hemp = P['beam'], P['brass'], P['iron'], P['hemp']
    # beam: 0.70 m, thick end at the fulcrum, eight-sided so the polish catches light along the facets
    cyl('Beam', (0, 0, BEAM_Z), .0155, .70, beam, axis='x', r2=.0115, verts=8, bevel=.0025, grain='x')
    for x, r in ((-.346, .0175), (.344, .0133)):
        cyl('Beam_Ferrule', (x, 0, BEAM_Z), r, .026, brass, axis='x', verts=24)
    sphere('Beam_EndKnob', (.36, 0, BEAM_Z), .0128, brass, scale=(.9, 1, 1), seg=16, ring=8)
    sphere('Beam_EndKnob2', (-.362, 0, BEAM_Z), .0158, brass, scale=(.8, 1, 1), seg=16, ring=8)
    # brass star dots on top and front: groups of one and three, a bigger star every fifth
    for k in range(18):
        x = -.24 + k * .033; r_beam = .0155 + (.0115 - .0155) * (x + .35) / .70
        big = k % 5 == 0
        for dx in ((-.004, 0, .004) if big else (0,)):
            sphere('Star_Top', (x + dx, 0, BEAM_Z + r_beam - .0006), .0021 if big else .0017, brass, scale=(1, 1, .45), seg=10, ring=5, detail=2)
        sphere('Star_Front', (x + .016, -r_beam + .0006, BEAM_Z), .0016, brass, scale=(1, .45, 1), seg=10, ring=5, detail=2)
    # fulcrum block with rivets, hook loop on top, pan ring underneath
    box('Fulcrum_Block', (FULCRUM_X, 0, BEAM_Z), (.042, .04, .044), brass, bevel=.004)
    for sy in (-1, 1):
        cyl('Fulcrum_Rivet', (FULCRUM_X, sy * .0205, BEAM_Z), .0055, .004, brass, axis='y', verts=16, detail=1)
    box('Fulcrum_Lug', (FULCRUM_X, 0, BEAM_Z + .026), (.012, .01, .02), brass, bevel=.003)
    torus('Hook_Eye', (FULCRUM_X, 0, BEAM_Z + .048), .012, .0042, brass, rot=(math.pi / 2, 0, 0), major=24, minor=8)
    # hook: up from the eye, over the top and curling down and out toward +X
    hook = [(FULCRUM_X, 0, BEAM_Z + .057), (FULCRUM_X - .002, 0, BEAM_Z + .075)]
    cx, cz, R = FULCRUM_X + .02, BEAM_Z + .094, .021
    for k in range(13):
        a = math.pi - k * math.radians(17)
        hook.append((cx + R * math.cos(a), 0, cz + R * math.sin(a)))
    hook.append((cx + R * .55, 0, cz - R * 1.25))
    tube('Hook', hook, .0056, brass, radii=[1.1, 1] + [1 - .25 * k / 13 for k in range(13)] + [.55], res=8, grain='z')
    sphere('Hook_Tip', hook[-1], .0028, brass, seg=10, ring=6)
    socket('SOCKET_hook', (cx - R * .1, 0, cz + R * .95))
    # pan hanger ring under the fulcrum (the pan group pivots here)
    torus('Pan_Ring', (FULCRUM_X, 0, BEAM_Z - .03), .0085, .0026, brass, rot=(math.pi / 2, 0, 0), major=20, minor=8, group='Pan')
    box('Pan_Ring_Lug', (FULCRUM_X, 0, BEAM_Z - .019), (.01, .008, .01), brass, bevel=.002)
    socket('SOCKET_pan', (FULCRUM_X, 0, BEAM_Z - .022))
    mk01_pan(P)
    mk01_weight(P)
    socket('SOCKET_weight_rest', (WEIGHT_X0, 0, BEAM_Z))
    socket('SOCKET_weight_max', (WEIGHT_X0 + .5, 0, BEAM_Z))


def mk01_pan(P):
    hemp, brass = P['hemp'], P['brass']
    R, H = .118, .036
    cx = FULCRUM_X
    prof = [(0, .0), (.07, .002), (.1, .008), (.113, .02), (R - .002, H - .004), (R - .006, H - .006),
            (.104, .021), (.09, .012), (0, .008)]
    o = lathe('Pan_Dish', prof, (cx, 0, 0), P['weave_sieve'], seg=64, group='Pan')
    wuv(o, lambda co: (co.x, co.y + co.z * .4))
    torus('Pan_Rim', (cx, 0, H - .002), R, .0055, P['bamboo'], major=72, minor=10, group='Pan', grain='z')
    torus('Pan_RimInner', (cx, 0, H - .006), R - .008, .0035, P['bamboo'], major=72, minor=8, group='Pan', grain='z', detail=1)
    for k in range(6):   # brass rim clips
        a = k / 6 * math.tau + .25
        torus('Pan_Clip', (cx + R * math.cos(a), R * math.sin(a), H - .003), .0075, .0022, brass,
              rot=(math.pi / 2, 0, a + math.pi / 2), major=16, minor=6, group='Pan', detail=1)
    knot = Vector((cx, 0, .395))
    for k in range(3):
        a = k / 3 * math.tau + math.pi / 2
        rim = Vector((cx + (R - .002) * math.cos(a), (R - .002) * math.sin(a), H + .002))
        mid = rim.lerp(knot, .5) + Vector((0, 0, .004))
        tube('Pan_Cord', [tuple(rim), tuple(mid), tuple(knot)], .0034, hemp, res=6, group='Pan', grain=tuple((knot - rim).normalized()))
        torus('Pan_Cord_Tie', tuple(rim + Vector((0, 0, .004))), .006, .0024, hemp, rot=(math.pi / 2, 0, a + math.pi / 2), major=14, minor=6, group='Pan', detail=1)
    sphere('Pan_Knot', tuple(knot), .0095, hemp, scale=(1, 1, 1.25), seg=14, ring=8, group='Pan')
    for k in range(5):   # frayed tuft under the knot
        a = k / 5 * math.tau
        tube('Pan_Fray', [tuple(knot + Vector((0, 0, -.006))), tuple(knot + Vector((math.cos(a) * .006, math.sin(a) * .006, -.022 - k * .002)))],
             .0009, hemp, radii=[1, .4], res=4, group='Pan', detail=2)
    tube('Pan_Lead', [tuple(knot + Vector((0, 0, .006))), (cx + .001, .0, BEAM_Z - .06), (cx, 0, BEAM_Z - .038)], .0038, hemp, res=6, group='Pan', grain='z')
    torus('Pan_LeadLoop', (cx, 0, BEAM_Z - .034), .006, .0024, hemp, rot=(math.pi / 2, 0, math.pi / 2), major=14, minor=6, group='Pan')


def mk01_weight(P):
    hemp, iron, brass = P['hemp'], P['iron'], P['brass']
    x = WEIGHT_X0
    torus('Weight_SlideRing', (x, 0, BEAM_Z), .0185, .0042, brass, rot=(0, math.pi / 2, 0), major=24, minor=8, group='Weight')
    top = Vector((x, 0, BEAM_Z - .02)); knot = Vector((x, 0, .37)); bell_top = .305
    tube('Weight_Cord', [tuple(top), tuple(top.lerp(knot, .5) + Vector((.001, 0, 0))), tuple(knot)], .0032, hemp, res=6, group='Weight', grain='z')
    sphere('Weight_Knot', tuple(knot), .008, hemp, scale=(1, 1, 1.3), seg=12, ring=8, group='Weight')
    for k in range(4):
        a = k / 4 * math.tau + .3
        tube('Weight_Fray', [tuple(knot + Vector((0, 0, -.004))), tuple(knot + Vector((math.cos(a) * .007, math.sin(a) * .007, -.018 - k * .003)))],
             .0008, hemp, radii=[1, .4], res=4, group='Weight', detail=2)
    tube('Weight_CordLow', [tuple(knot), (x, 0, bell_top + .022)], .003, hemp, res=6, group='Weight', grain='z')
    torus('Weight_Loop', (x, 0, bell_top + .014), .0105, .0042, iron, rot=(math.pi / 2, 0, 0), major=20, minor=8, group='Weight')
    # eight-sided cast bell, wider at the foot, with a dent on the front
    prof = [(0, bell_top - .078), (.036, bell_top - .078), (.038, bell_top - .072), (.036, bell_top - .058), (.031, bell_top - .024),
            (.026, bell_top - .007), (.019, bell_top), (.011, bell_top + .005), (0, bell_top + .005)]
    bell = lathe('Weight_Bell', prof, (x, 0, 0), iron, seg=8, group='Weight')
    bell.modifiers.new('Soft_edges', 'BEVEL').width = .0018
    boolean(bell, sphere('Weight_Dent_Cut', (x + .007, -.037, bell_top - .04), .009, None, scale=(1.2, .6, .9)))
    lathe('Weight_FootBand', [(.037, bell_top - .077), (.0392, bell_top - .072), (.0392, bell_top - .066), (.0372, bell_top - .062)],
          (x, 0, 0), iron, seg=8, group='Weight', detail=1)


# ================================================================ MK02 收成竹篩＋三級草藥捆
SIEVE_R, SIEVE_H = .289, .074


def mk02_harvest_set(P):
    mk02_sieve(P)
    # three bundles standing in a row behind the sieve, three single plants in front (model sheet layout;
    # each is its own object with its own bottom-centre pivot)
    mats = P
    for k, grade in enumerate(('top', 'mid', 'low')):
        x = -.2 + k * .2
        hb.bundle(f'Bundle_{grade}', (x, .5, 0), .35, grade, mats, 100 + k, group=f'Bundle{grade.title()}', plants=4, lean=(0, -.02))
        hb.plant(f'Plant_{grade}', (x + .05, -.48, 0), .30, grade, mats, 200 + k, group=f'Plant{grade.title()}', lean=(.02, 0))


def mk02_sieve(P):
    R, H = SIEVE_R, SIEVE_H
    # floor: shallow dish of woven split bamboo
    def floor(u, v):
        r = (R - .012) * v; a = u * math.tau
        return (r * math.cos(a), r * math.sin(a), .006 + .01 * (v ** 2))
    f = surface('Sieve_Floor', 64, 16, floor, P['weave_sieve'], closed_u=True, solid=.004)
    wuv(f, lambda co: (co.x, co.y))
    def wall(u, v):
        a = u * math.tau; r = R - .012 + .006 * v
        return (r * math.cos(a), r * math.sin(a), .014 + v * (H - .026))
    w = surface('Sieve_Wall', 96, 4, wall, P['weave_sieve'], closed_u=True, solid=.004)
    wuv(w, lambda co: (math.atan2(co.y, co.x) * R, co.z * 1.0))
    # rim: outer and inner bamboo hoops clamping the wall, rattan lashing every 30°
    torus('Sieve_RimOuter', (0, 0, H - .008), R - .002, .0085, P['bamboo'], major=96, minor=12, grain='z')
    torus('Sieve_RimInner', (0, 0, H - .01), R - .02, .0065, P['bamboo'], major=96, minor=10, grain='z')
    torus('Sieve_FootHoop', (0, 0, .012), R - .006, .007, P['bamboo_old'], major=96, minor=10, grain='z', detail=1)
    for k in range(12):
        a = k / 12 * math.tau
        if 1.7 < a < 2.6: continue   # the mended section has its own wrapping
        for s in range(3):
            aa = a + (s - 1) * .028
            torus('Sieve_Lash', ((R - .011) * math.cos(aa), (R - .011) * math.sin(aa), H - .009), .0135, .0021, P['twine'],
                  rot=(math.pi / 2, 0, aa + math.pi / 2), major=16, minor=6, detail=1 if s else 0, grain=(math.cos(aa), math.sin(aa), 0))
    # mended rim: a greyer replacement strip bound tight with fresh twine
    for k in range(9):
        aa = 1.85 + k * .075
        torus('Sieve_MendWrap', ((R - .011) * math.cos(aa), (R - .011) * math.sin(aa), H - .009), .0142, .0024, P['hemp'],
              rot=(math.pi / 2, 0, aa + math.pi / 2), major=16, minor=6, grain=(math.cos(aa), math.sin(aa), 0))
    pts = [((R + .004) * math.cos(1.8 + k * .05), (R + .004) * math.sin(1.8 + k * .05), H - .009) for k in range(16)]
    tube('Sieve_MendStrip', pts, .006, P['bamboo_old'], res=6, grain='z')
    # cross braces under the floor (seen from the back)
    for a in (0, math.pi / 2):
        box('Sieve_Brace', (0, 0, .006), (2 * R - .03, .02, .007), P['bamboo_old'], bevel=.002, rot=(0, 0, a))
    box('Sieve_BraceTie', (0, 0, .0105), (.026, .026, .004), P['twine'], bevel=.001, rot=(0, 0, .785))
    # a few loose leaves and soil crumbs on the floor: their own Litter group, so an empty sieve (a sort tray) can hide them
    rnd = random.Random(17)
    for k in range(7):
        a = rnd.uniform(0, math.tau); r = rnd.uniform(.05, .22)
        base = (r * math.cos(a), r * math.sin(a), .017 + .01 * (r / R) ** 2)
        d = (math.cos(a + 1.3), math.sin(a + 1.3), .05)
        hb.leaf_blade(f'Sieve_LooseLeaf{k}', base, d, rnd.uniform(.06, .09), rnd.uniform(.012, .016),
                      P['leaf_mid'] if k % 3 else P['leaf_low'], droop=-.02, fold=.1, twist=rnd.uniform(-.2, .2), detail=1, group='Litter')
    for k in range(14):
        a = rnd.uniform(0, math.tau); r = rnd.uniform(.03, .24)
        sphere('Sieve_Crumb', (r * math.cos(a), r * math.sin(a), .017 + .01 * (r / R) ** 2), rnd.uniform(.003, .007), P['soil'],
               scale=(1, rnd.uniform(.7, 1.2), .55), seg=8, ring=5, detail=2, group='Litter')


# ================================================================ MK03 價目木牌＋錢串
BOARD_W, BOARD_D, BOARD_H = .5, .04, .62    # rope loop above to 0.70


def mk03_market_set(P):
    mk03_board(P)
    mk03_coins(P)
    mk03_purse(P)


def mk03_board(P):
    pine, nail = P['pine'], P['nail']
    W, D, H = BOARD_W, BOARD_D, BOARD_H
    # frame: rails over stiles, four blank planks set slightly back
    for z in (H - .035, .035):
        box('Board_Rail', (0, 0, z), (W, D, .072), pine, bevel=.007, grain='x', rot=(0, .006 if z > .3 else -.004, 0))
    for x in (-W / 2 + .03, W / 2 - .03):
        box('Board_Stile', (x, .002, H / 2), (.06, D - .006, H - .1), pine, bevel=.004, grain='z')
    rnd = random.Random(3)
    xs, ws = [-.168, -.064, .046, .158], [.1, .104, .112, .096]
    for k, (x, w) in enumerate(zip(xs, ws)):
        box('Board_Plank', (x, .006 + rnd.uniform(-.002, .002), H / 2), (w - .004, .022, H - .13), pine, bevel=.003, grain='z', rot=(0, rnd.uniform(-.006, .006), 0))
    # backing board behind the plank joints, so the uneven joints read as dark seams and never show sky
    box('Board_Back', (0, .0165, H / 2), (W - .07, .006, H - .11), pine, bevel=.002, grain='z')
    for x in (-W / 2 + .03, W / 2 - .03):
        for z in (H - .035, .035):
            sphere('Board_Nail', (x, -D / 2 - .0005, z), .0065, nail, scale=(1, .45, 1), seg=14, ring=7)
    # rope through two holes in the top rail, up to a knot
    for x in (-.15, .15):
        cyl('Board_RopeHole', (x, -D / 2 - .0004, H - .03), .009, .002, P['nail'], axis='y', verts=16, detail=1)
    lt = (0, 0, .686)
    for s in (-1, 1):
        x = s * .15
        tube('Board_Rope', [(x, -.012, H - .03), (x * .9, -.012, H + .005), (x * .5, -.006, H + .045), (s * .01, 0, .681)],
             .0045, P['hemp'], res=6, grain=(-s, 0, 1))
    sphere('Board_RopeKnot', lt, .009, P['hemp'], scale=(1.3, 1, .9), seg=14, ring=8)
    # chalk ledge marks and a nail peg for the removable tag
    cyl('Board_TagPeg', (0, -D / 2 - .004, H - .1), .0045, .008, nail, axis='y', verts=14)   # stays inside the 0.05 m depth
    socket('SOCKET_plate_demand', (0, -D / 2 - .0065, H - .1))
    mk03_plate(P)


def mk03_plate(P):
    """Plate_Demand: removable blank tag hung on the peg (today's demand icon is a decal on its front)."""
    z = BOARD_H - .1
    o = box('Plate_Demand_Body', (0, -BOARD_D / 2 - .0065, z - .07), (.1, .012, .13), P['pine_tag'], bevel=.003, grain='z', group='PlateDemand')
    boolean(o, cyl('Plate_Hole_Cut', (0, -BOARD_D / 2 - .0065, z - .012), .0065, .03, None, axis='y', bevel=0, verts=16))
    for x in (-.05, .05):   # clipped top corners
        boolean(o, box('Plate_Corner_Cut', (x, -BOARD_D / 2 - .0065, z), (.03, .03, .03), None, bevel=0, rot=(0, math.pi / 4, 0)))
    torus('Plate_Demand_Loop', (0, -BOARD_D / 2 - .0065, z - .004), .009, .0018, P['twine'], rot=(math.pi / 2, 0, 0), major=16, minor=6, group='PlateDemand')
    socket('SOCKET_demand_icon', (0, -BOARD_D / 2 - .0135, z - .075))


def coin(name, at, mat, axis='z', group='Main', rot=None, detail=0):
    """Round cash with a square hole and a raised rim (2.4 cm)."""
    o = cyl(name, at, .012, .0018, mat, axis=axis, verts=32, bevel=.0004, group=group, detail=detail, rot=rot)
    cut = box(name + '_Hole', at, (.0062, .0062, .01) if axis == 'z' else (.01, .0062, .0062) if axis == 'x' else (.0062, .01, .0062),
              None, bevel=0, rot=rot or (0, 0, 0))
    boolean(o, cut)
    rim = torus(name + '_Rim', at, .0112, .0006, mat, rot=rot or ((0, math.pi / 2, 0) if axis == 'x' else (math.pi / 2, 0, 0) if axis == 'y' else (0, 0, 0)),
                major=32, minor=4, group=group, detail=max(detail, 1))
    return o


def mk03_coins(P):
    # ten coins strung face to face on a red-brown cord, 0.12 m with the knots, lying on the table
    x0, y0 = .35, -.12; zc = .012
    for k in range(10):
        x = x0 - .045 + k * .01
        coin(f'CoinString_Coin{k}', (x, y0, zc), P['coin'], axis='x', group='CoinString', rot=(math.radians(rng().uniform(-4, 4)), math.pi / 2, 0))
    tube('CoinString_Cord', [(x0 - .06, y0, zc), (x0 + .06, y0, zc)], .0022, P['cord_red'], res=6, grain='x', group='CoinString')
    for s in (-1, 1):
        sphere('CoinString_Knot', (x0 + s * .058, y0, zc), .0045, P['cord_red'], seg=12, ring=7, group='CoinString')
    for k, (dx, dy, a) in enumerate(((-.02, .06, .3), (.012, .07, 1.1), (.03, .052, 2.0))):
        coin(f'LooseCoin{k}', (x0 + dx, y0 + dy, .0009), P['coin'], axis='z', group='LooseCoins', rot=(0, 0, a))


def mk03_purse(P):
    """Drawstring indigo coin purse, 0.15 m: soft pouch, gathered neck with folds, cord and tails, a patch."""
    cx, cy = -.38, -.1
    def pouch(u, v):
        a = u * math.tau
        r = .062 * math.sin(math.pi * min(v * 1.12, 1) ** .9) ** .55 if v < .82 else .022 + .012 * (v - .82) / .18
        r *= 1 + .025 * math.sin(a * 5 + v * 3) * (v > .7) + .02 * math.sin(a * 3)
        z = .118 * v ** .95
        return (cx + r * math.cos(a) * 1.05, cy + r * math.sin(a) * .88, z)
    o = surface('Purse_Body', 48, 24, pouch, P['indigo'], closed_u=True, solid=.002)
    def ruffle(u, v):
        a = u * math.tau; r = .022 + .012 * v * v + .0035 * math.sin(a * 9) * v
        return (cx + r * math.cos(a), cy + r * math.sin(a) * .9, .116 + .024 * v - .006 * v * v + .003 * math.sin(a * 9 + 1) * v)
    surface('Purse_Ruffle', 66, 4, ruffle, P['indigo'], closed_u=True, solid=.0018)
    torus('Purse_Draw', (cx, cy, .117), .0235, .0032, P['hemp'], rot=(0, 0, 0), major=28, minor=8, grain='z')
    torus('Purse_Draw2', (cx, cy, .111), .026, .0028, P['hemp'], rot=(.08, 0, 0), major=28, minor=8, grain='z', detail=1)
    for s in (-1, 1):
        p0 = (cx + s * .02, cy - .016, .114)
        tube('Purse_Tail', [p0, (cx + s * .035, cy - .03, .095), (cx + s * .045, cy - .036, .07)], .0026, P['hemp'], res=6, grain='z')
        sphere('Purse_TailKnot', (cx + s * .046, cy - .037, .066), .0052, P['hemp'], seg=12, ring=7)
        for k in range(3):
            tube('Purse_Fray', [(cx + s * .046, cy - .037, .062), (cx + s * (.046 + .004 * (k - 1)), cy - .037 - .003 * k, .05)], .0008,
                 P['hemp'], radii=[1, .4], res=4, detail=2)
    def patch(u, v):
        a = -1.75 + (u - .5) * .6; z = .04 + v * .034
        r = .0625 * math.sin(math.pi * min(z / .118 * 1.12, 1) ** .9) ** .55 + .0016
        return (cx + r * math.cos(a) * 1.05, cy + r * math.sin(a) * .88, z)
    surface('Purse_Patch', 8, 6, patch, P['indigo_patch'], solid=.0012)
    for k in range(10):   # running stitches round the patch
        t = k / 10
        a = -1.75 + (-.3 + .6 * t * 2 if k < 5 else .3 - .6 * (t - .5) * 2); z = .041 if k < 5 else .073
        r = .066
        box('Purse_Stitch', (cx + r * math.cos(a) * 1.05, cy + r * math.sin(a) * .88, z), (.006, .0015, .0015), P['twine'], bevel=0, rot=(0, 0, a + math.pi / 2), detail=2)
    socket('SOCKET_coins_drop', (.35, -.12, 0))


# ================================================================ MK04 背簍
BW_TOP, BD_TOP, BW_BOT, BD_BOT = .375, .245, .3, .2
BODY_Z0, BODY_Z1 = .07, .45


def _rrect(a, w, d, n=4.0):
    """Superellipse point (rounded rectangle) for angle a, half sizes w/2, d/2."""
    c, s = math.cos(a), math.sin(a)
    return (w / 2 * math.copysign(abs(c) ** (2 / n), c), d / 2 * math.copysign(abs(s) ** (2 / n), s))


def _section(z):
    t = (z - BODY_Z0) / (BODY_Z1 - BODY_Z0)
    return BW_BOT + (BW_TOP - BW_BOT) * t, BD_BOT + (BD_TOP - BD_BOT) * t


def strap_band(name, path, width, thick, mat):
    """Flat braided shoulder band following a smoothed path; width across X, face toward +Y (the wearer's back).
    Edges roll slightly so the band reads as woven hemp, not a plank."""
    from ti_core import _catmull
    pts = _catmull(path, 8); nv = len(pts) - 1
    def fn(u, v):
        i = min(int(round(v * nv)), nv); p = pts[i]
        q = pts[min(i + 1, nv)] - pts[max(i - 1, 0)]; q.normalize()
        side = Vector((1, 0, 0)); nrm = side.cross(q).normalized()
        if nrm.y < 0: nrm = -nrm
        x = (u - .5) * 2; w = width * (1 + .12 * math.sin(v * math.pi)) / 2
        return tuple(p + side * (x * w) - nrm * (.004 * x * x))
    o = surface(name, 6, nv, fn, mat, solid=thick, grain='z')
    return o


def mk04_back_basket(P):
    wv = P['weave_basket']
    def body(u, v):
        z = BODY_Z0 + v * (BODY_Z1 - BODY_Z0); w, d = _section(z)
        x, y = _rrect(u * math.tau, w, d)
        return (x, y, z)
    o = surface('Basket_Body', 128, 24, body, wv, closed_u=True, solid=.007)
    wuv(o, lambda co: (math.atan2(co.y / .7, co.x) * .19, co.z))
    def bottom(u, v):
        w, d = _section(BODY_Z0); x, y = _rrect(u * math.tau, w * v, d * v)
        return (x, y, BODY_Z0 + .004)
    b = surface('Basket_Bottom', 64, 6, bottom, wv, closed_u=True, solid=.006)
    wuv(b, lambda co: (co.x, co.y))
    # vertical bamboo stakes, slightly proud of the weave
    stakes = 10
    for k in range(stakes):
        a = (k + .5) / stakes * math.tau
        pts = []
        for z in (BODY_Z0 - .01, (BODY_Z0 + BODY_Z1) / 2, BODY_Z1 + .006):
            w, d = _section(min(max(z, BODY_Z0), BODY_Z1)); x, y = _rrect(a, w + .012, d + .012); pts.append((x, y, z))
        tube('Basket_Stake', pts, .0075, P['bamboo_warm'], res=5, grain='z', radii=[1, 1, .9])
    # horizontal binding hoops with rope lashings where they cross the stakes
    for z, rr in ((.11, .006), (.215, .0055), (.32, .0055), (.415, .0065)):
        w, d = _section(z)
        pts = [(*_rrect(k / 96 * math.tau, w + .018, d + .018), z) for k in range(97)]
        tube('Basket_Hoop', pts, rr, P['bamboo_warm'], res=6, grain='z')
        for k in range(stakes):
            a = (k + .5) / stakes * math.tau; x, y = _rrect(a, w + .02, d + .02)
            nrm = math.atan2(y, x)
            torus('Basket_Lash', (x, y, z), .008, .0018, P['twine'], rot=(math.pi / 2, 0, nrm + math.pi / 2), major=12, minor=5, detail=2 if k % 2 else 1,
                  grain=(math.cos(nrm), math.sin(nrm), 0))
    # rim: two thick hoops with a rope wrap spiral
    w, d = _section(BODY_Z1)
    for off, rr, zz in ((.02, .011, BODY_Z1 + .006), (-.006, .008, BODY_Z1 + .004)):
        pts = [(*_rrect(k / 120 * math.tau, w + off, d + off), zz) for k in range(121)]
        tube('Basket_Rim', pts, rr, P['bamboo_old'] if off < 0 else P['bamboo_warm'], res=8, grain='z')
    pts = []
    for k in range(361):
        a = k / 360 * math.tau; x, y = _rrect(a, w + .007, d + .007); tw = k * 1.2
        pts.append((x + .009 * math.cos(tw) * math.cos(a), y + .009 * math.cos(tw) * math.sin(a), BODY_Z1 + .005 + .009 * math.sin(tw)))
    tube('Basket_RimWrap', pts, .0022, P['twine'], res=4, grain='z', detail=1)
    # wooden base frame with corner blocks and feet
    zf = .035
    for s in (-1, 1):
        box('Base_Rail_X', (0, s * (BD_BOT / 2 + .006), zf), (BW_BOT + .05, .026, .03), P['timber'], bevel=.004, grain='x')
        box('Base_Rail_Y', (s * (BW_BOT / 2 + .006), 0, zf + .012), (.026, BD_BOT + .04, .026), P['timber'], bevel=.004, grain='y')
        for t in (-1, 1):
            box('Base_Foot', (s * (BW_BOT / 2 + .006), t * (BD_BOT / 2 + .006), .012), (.034, .034, .024), P['timber'], bevel=.004, grain='z')
            sphere('Base_Peg', (s * (BW_BOT / 2 + .006), t * (BD_BOT / 2 + .006) - t * .0, zf + .028), .006, P['timber'], scale=(1, 1, .5), seg=10, ring=5, detail=1)
    # mended patch on the front: a greyer woven square stitched on with twine
    pz, pw, ph = .27, .1, .09
    def patch(u, v):
        z = pz - ph / 2 + v * ph; w, d = _section(z); a = -math.pi / 2 + (u - .5) * pw / (w / 2) * .85
        x, y = _rrect(a, w + .016, d + .016)
        return (x, y, z)
    pt = surface('Basket_Patch', 10, 8, patch, P['weave_patch'], solid=.003)
    wuv(pt, lambda co: (co.x + .3, co.z + .3))
    for k in range(12):
        side = k // 3; t = (k % 3 + .5) / 3
        if side == 0: u, v = t, 0
        elif side == 1: u, v = 1, t
        elif side == 2: u, v = 1 - t, 1
        else: u, v = 0, 1 - t
        x, y, z = patch(u, v)
        torus('Patch_Stitch', (x, y - .002, z), .006, .0015, P['twine'], rot=(math.pi / 2, (k % 2) * .8, 0), major=10, minor=4, detail=1)
    # shoulder straps on the back (+Y): braided bands from the rim to the base frame corners
    for s in (-1, 1):
        x0 = s * .1
        path = [(x0, BD_TOP / 2 + .012, BODY_Z1 + .004), (x0 * 1.05, BD_TOP / 2 + .045, BODY_Z1 - .035), (x0 * 1.15, BD_TOP / 2 + .068, .3),
                (x0 * 1.3, BD_TOP / 2 + .055, .16), (x0 * 1.45, BD_BOT / 2 + .03, .07)]
        sb = strap_band(f'Strap_Band', path, .042, .007, P['strap_braid'])
        wuv(sb, lambda co: (co.x, co.z + co.y * .5))
        torus('Strap_TopWrap', (x0, BD_TOP / 2 + .006, BODY_Z1 + .006), .016, .004, P['twine'], rot=(0, math.pi / 2, 0), major=16, minor=6, grain='x')
        torus('Strap_FootLoop', (x0 * 1.45, BD_BOT / 2 + .025, .062), .016, .0045, P['strap'], rot=(0, math.pi / 2, 0), major=16, minor=6, grain='x')
        sphere('Strap_Knot', (x0 * 1.45, BD_BOT / 2 + .032, .082), .009, P['strap'], scale=(1, .9, 1.2), seg=12, ring=8)
    socket('Socket_Back', (0, BD_TOP / 2 + .075, .28))   # outer face of the strap bows, where they meet the back
    # Fill: three bundles of the same herb standing in the basket, tips out of the top, toggled as one object
    for k, (x, y) in enumerate(((-.08, .012), (0, -.02), (.08, .012))):
        hb.bundle(f'Fill_B{k}', (x, y, .32 + (.01 if k == 1 else 0)), .25, 'mid', P, 300 + k, group='Fill', plants=3, lean=(x * .9, -.02),
                  leaf_res=(3, 12), roots=False)   # roots sit inside the basket: never seen; lighter leaves (worn all the time)
