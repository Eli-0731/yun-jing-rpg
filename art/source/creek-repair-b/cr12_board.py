"""CR12 ranking notice board: timber frame, small tiled roof, wide backing, twelve separate blank slips, polished rail, chipped cup.
Limit 3 x 0.6 x 2.8 m. Backing front face at y = 0; rail in front at y = -0.2; roof symmetric about y = 0."""
import math, random
from mathutils import Vector, noise
from ti_core import S, box, cyl, sphere, lathe, boolean, socket, mesh, extrude_profile
import ti_mats as tm
import mk_mats as mm
import cr_mats as cm
from cr_parts import rbox, rope, sheet, between, set_float, tuft, lash

HW_POST = 1.2; EAVE_HW = 1.5; RIDGE_Z = 2.655; EAVE_Z = 2.34; EAVE_Y = .275
BACK_Z0, BACK_Z1 = .96, 2.2; RAIL_Z = 1.0; RAIL_Y = -.205; RAIL_HW = 1.38


def palette():
    P = {}
    P['timber'] = cm.wood('Frame_Timber', (.05, .027, .014), (.24, .14, .07), ground_h=.22, moss=True, moss_amt=.5, grey=.16)
    P['back'] = cm.wood('Backing_Boards', (.042, .023, .012), (.19, .108, .052), ground_h=0, holes=.9, grey=.12)
    P['core'] = cm.wood('Back_Core', (.02, .012, .008), (.04, .025, .015), ground_h=0, grey=0)
    P['rail'] = cm.wood('Rail_Polished', (.06, .032, .015), (.27, .155, .075), ground_h=0, polish=.3, grey=.1)
    P['tile'] = cm.tile('Roof_Tile', base=(.02, .028, .036), light=(.052, .066, .078), moss=1.)
    P['ridge'] = cm.tile('Ridge_Tile', base=(.028, .038, .05), light=(.07, .088, .1), moss=.7)
    P['plinth'] = cm.stone('Plinth_Stone', moss=1.0)
    P['iron'] = mm.cast_iron('Band_Iron')
    P['nail'] = tm.metal('Nail_Iron', (.06, .055, .05), (.13, .07, .035), rough=.55, patina_amt=.6)
    P['paper_new'] = cm.paper('Slip_Paper', base=(.33, .265, .165), edge=(.13, .08, .035), age=1.0)
    P['paper_old'] = cm.paper('Slip_Paper_Oldest', base=(.24, .17, .09), edge=(.09, .05, .022), age=1.0)
    P['scrap'] = cm.paper('Old_Scraps', base=(.36, .28, .17), edge=(.12, .08, .04), age=.9)
    P['cup'] = cm.porcelain('Cup_Porcelain')
    P['moss'] = cm.moss_tuft('Moss_Tuft')
    return P


def frame(P):
    t = P['timber']
    for sx in (-1, 1):
        x = sx * HW_POST
        rbox('Plinth', (x, 0, .085), (.27, .26, .17), P['plinth'], r=.02, amp=.012, freq=7., chips=3, seed=sx + 1, div=.03, taper=(.85, .85))
        rbox('Post', (x, 0, 1.28), (.15, .15, 2.24), t, r=.012, amp=.003, freq=3., chips=1, seed=sx + 3, div=.07, grain='z')
        rbox('Head_Corbel', (x, 0, 2.12), (.3, .1, .08), t, r=.012, amp=.002, seed=sx + 5, div=.04)
    between('Head_Beam', (-HW_POST - .08, 0, 2.28), (HW_POST + .08, 0, 2.28), .13, .16, t, r=.012, amp=.003, seed=7, div=.08)
    between('Sill_Beam', (-HW_POST + .07, .015, BACK_Z0 - .04), (HW_POST - .07, .015, BACK_Z0 - .04), .09, .08, t, r=.01, amp=.002, seed=8, div=.08)


def backing(P):
    b = P['back']; n = 13; W = 2 * (HW_POST - .07)
    for i in range(n):
        x = -W / 2 + (i + .5) * W / n
        rbox('Back_Plank', (x, .015, (BACK_Z0 + BACK_Z1) / 2), (W / n - .003, .03, BACK_Z1 - BACK_Z0), b, r=.003, amp=.0015, freq=5., seed=i, div=.06, grain='z')
    rbox('Back_Core', (0, .017, (BACK_Z0 + BACK_Z1) / 2), (W + .004, .01, BACK_Z1 - BACK_Z0 + .004), P['core'], r=.001, div=.2, detail=1)
    # rear: ledgers, battens and iron straps
    for z in (1.14, 1.56, 1.98):
        rbox('Ledger', (0, .046, z), (W, .034, .1), P['timber'], r=.006, amp=.002, seed=int(z * 10), div=.08)
    for x in (-.74, .74):
        rbox('Batten', (x, .071, (BACK_Z0 + BACK_Z1) / 2), (.1, .022, BACK_Z1 - BACK_Z0 - .03), P['timber'], r=.005, amp=.002, seed=int(x * 10) + 20, div=.08, grain='z')
    for x, z in ((-.74, 1.14), (-.74, 1.98), (.74, 1.14), (.74, 1.98), (-.74, 1.56), (.74, 1.56)):
        rbox('Strap', (x, .083, z), (.13, .004, .13), P['iron'], r=.0016, amp=.0006, seed=int(z * 7 + x * 3), div=.03, detail=1)
        for dx, dz in ((-.05, -.05), (.05, -.05), (-.05, .05), (.05, .05)):
            sphere('Strap_Nail', (x + dx, .086, z + dz), .007, P['nail'], scale=(1, .55, 1), seg=10, ring=6, detail=2)
    # front rows of old nails where slips used to hang
    R = S['rng']
    for k in range(34):
        x = R.uniform(-1.08, 1.08); z = R.uniform(BACK_Z0 + .03, BACK_Z1 - .03)
        sphere('Old_Nail', (x, -.001, z), .0048, P['nail'], scale=(1, .5, 1), seg=8, ring=5, detail=2)


def scraps(P):
    """Layers of old torn paper between and behind the slips, darker than the live ones."""
    spots = [(-1.07, 1.92, .11, .17), (-1.0, 1.3, .1, .22), (-.86, 2.08, .12, .1), (.94, 1.76, .1, .2), (1.05, 1.32, .09, .24), (1.0, 2.05, .15, .12),
             (.72, 1.04, .13, .08), (-.7, 1.02, .16, .07), (-.32, 1.03, .1, .06), (.28, 1.45, .06, .08), (-.17, 1.47, .05, .07), (.62, 1.86, .1, .05), (-.58, 1.84, .08, .05),
             (-.98, 1.65, .08, .12), (1.08, 2.14, .1, .07)]
    for i, (x, z, w, h) in enumerate(spots):
        def fn(u, v, x=x, z=z, w=w, h=h, i=i):
            uu = (u - .5) * w; vv = (v - .5) * h
            q = Vector((u * 4 + i, v * 4, i * .7))
            return (x + uu + noise.noise(q) * .012, -.0012 - .0006 * (i % 3) - .0012 * abs(noise.noise(q * 2)), z + vv + noise.noise(q + Vector((3, 1, 0))) * .012)
        def keep(u, v, i=i):
            e = min(u, 1 - u, v, 1 - v)
            return e > .24 * max(0., noise.noise(Vector((u * 5 + i, v * 5, 1.))) + .25)
        sheet('Scrap', 12, 14, fn, P['scrap'], solid=.0006, keep=keep, grain='z', detail=1)


def slip(P, n, cx, cz, w, h, curl, mat, seed, roll=False):
    """One blank slip: a slightly wavy sheet, curled corners, an uneven torn foot. Nails belong to the slip."""
    g = f'Slip_{n:02d}'
    def fn(u, v):
        x, z = (u - .5) * w, (v - .5) * h
        q = Vector((u * 3 + seed, v * 3, seed * .5))
        y = -.003 - .004 * (noise.noise(q) + .5) - .0016 * math.sin(u * 7 + seed)
        # bottom hangs away from the board a little, and its foot is uneven
        y -= .012 * (1 - v) ** 2
        foot = (1 - v) ** 6 * noise.noise(Vector((u * 9 + seed, 3., 0.))) * .018
        z += foot
        for cu, cv, k in ((0, 0, 1.), (1, 0, 1.), (0, 1, .55), (1, 1, .55)):
            d = math.hypot((u - cu) * w, (v - cv) * h)
            rad = curl * k
            if rad and d < rad * 2.4:
                t = 1 - d / (rad * 2.4); ang = t * t * (2.8 if roll else 1.8)
                lift = rad * (1 - math.cos(ang)) * 1.5
                pull = rad * (ang - math.sin(ang)) * 1.1
                y -= lift
                dirx = .5 - cu; dirz = .5 - cv
                x += dirx * 2 * pull * .6; z += dirz * 2 * pull * .6
        return (cx + x, y, cz + z)
    def keep(u, v):
        e = min(u, 1 - u, v * 1.2, (1 - v) * 1.6)
        return e > .03 * max(0., noise.noise(Vector((u * 13 + seed, v * 13, 2.))) + .12)
    o = sheet(f'Slip_{n:02d}', 34 if roll else 18, 20 if roll else 24, fn, mat, solid=.0012, keep=keep, group=g, grain='z')
    # nails through the top edge; small rust halo comes from AO
    nails = 4 if roll else 2
    for k in range(nails):
        u = (k + .5) / nails if roll else (.14 if k == 0 else .86)
        p = fn(u, .95)
        sphere('Slip_Nail', (p[0], p[1] - .002, p[2]), .0062, P['nail'], scale=(1, .55, 1), seg=10, ring=6, group=g)
    if n in (4, 9):                     # a few slips have a bottom nail too, which pins the foot down
        p = fn(.5, .06)
        sphere('Slip_Nail', (p[0], p[1] - .002, p[2]), .0055, P['nail'], scale=(1, .55, 1), seg=10, ring=6, group=g, detail=1)
    return o


def slips(P):
    # the top slip: oldest, biggest, corners curled right over
    slip(P, 1, -.1, 1.98, .98, .32, .095, P['paper_old'], 1.1, roll=True)
    x6 = [-.92 + k * .368 for k in range(6)]
    for k, x in enumerate(x6):
        slip(P, 2 + k, x + (k % 2) * .005, 1.61 - (k % 3) * .006, .262, .34, .012 + .004 * (k % 3), P['paper_new'], 2.3 + k * 1.7)
    x5 = [-.76 + k * .38 for k in range(5)]
    for k, x in enumerate(x5):
        slip(P, 8 + k, x - (k % 2) * .007, 1.2 + (k % 2) * .008, .262, .34, .014 + .005 * ((k + 1) % 3), P['paper_new'], 9.1 + k * 1.3)


def railing(P):
    t, r = P['timber'], P['rail']
    y = RAIL_Y
    for sx in (-1, 1):
        x = sx * RAIL_HW
        rbox('Rail_Plinth', (x, y, .07), (.17, .17, .14), P['plinth'], r=.018, amp=.006, freq=8., chips=3, seed=sx + 11, div=.03, taper=(.84, .84))
        rbox('Rail_Post', (x, y, .64), (.11, .11, 1.04), t, r=.01, amp=.0025, freq=3., seed=sx + 13, div=.06, grain='z')
        # finial: turned onion on a collar (plain, no carving)
        lathe('Finial', [(0, 0), (.058, 0), (.062, .012), (.05, .028), (.05, .036), (.058, .052), (.05, .085), (.028, .112), (.012, .13), (.006, .142), (0, .15)], (x, y, 1.16), P['rail'], seg=24)
        for z in (RAIL_Z + .1, .55):
            rbox('Iron_Band', (x, y, z), (.118, .118, .03), P['iron'], r=.003, amp=.0008, seed=int(z * 10) + sx, div=.03, detail=1)
        # tie from rail post back to the main post, at rail and mid height
        for z in (RAIL_Z - .03, .55):
            between('Tie', (x - sx * .03, y, z), (sx * HW_POST, -.03, z), .05, .06, t, r=.007, amp=.002, seed=int(z * 10) + 2 * sx, div=.05)
    # polished top rail with a soft dip where people lean
    def rail_pts(u, w):
        return u
    o = rbox('Top_Rail', (0, y, RAIL_Z), (2 * RAIL_HW - .09, .13, .09), r, r=.024, amp=.0025, freq=2.2, seed=21, div=.05)
    for v in o.data.vertices:
        if v.co.z > .02:
            v.co.z -= .006 * math.exp(-((v.co.x - .35) / .55) ** 2) + .006 * math.exp(-((v.co.x + .55) / .4) ** 2)
    rbox('Under_Rail', (0, y + .006, RAIL_Z - .065), (2 * RAIL_HW - .09, .06, .05), t, r=.008, amp=.002, seed=22, div=.08)
    rbox('Mid_Rail', (0, y, .55), (2 * RAIL_HW - .09, .07, .08), t, r=.01, amp=.002, seed=23, div=.08)
    for x in (-.46, .46):
        rbox('Stub', (x, y, .755), (.09, .06, .33), t, r=.008, amp=.002, seed=int(x * 10) + 30, div=.05, grain='z')
    rbox('Mid_Post', (0, y, .3), (.1, .08, .5), t, r=.009, amp=.002, seed=31, div=.05, grain='z')
    rbox('Mid_Foot', (0, y, .05), (.15, .15, .1), P['plinth'], r=.016, amp=.007, freq=9., chips=2, seed=32, div=.03, taper=(.86, .86))


def cup(P):
    g = 'TeaCup'; cx, cy, cz = .98, RAIL_Y + .012, RAIL_Z + .045
    prof = [(0, 0), (.022, 0), (.024, .004), (.023, .012), (.03, .022), (.04, .048), (.044, .064), (.042, .066), (.038, .05), (.03, .03), (.018, .018), (0, .015)]
    o = lathe('Cup', prof, (cx, cy, cz), P['cup'], seg=36, group=g)
    set_float(o, 'cupv', lambda c: min(1., c.z / .066))
    # the chip in the rim (爛茶杯)
    c = rbox('Cup_Chip', (cx + .036, cy - .028, cz + .066), (.03, .03, .024), P['cup'], r=.003, amp=.003, freq=70., chips=2, seed=3, div=.008, group=g)
    boolean(o, c)


def roof_z(y, x=0.):
    s = min(1., abs(y) / EAVE_Y)
    z = RIDGE_Z - (RIDGE_Z - EAVE_Z) * s ** 1.5            # concave fall from ridge to eave
    fx = max(0., (abs(x) - 1.02) / (EAVE_HW - 1.02))
    return z + .16 * fx * fx * s                           # corners sweep up


def tiles(P):
    tm_, pitch = P['tile'], .158
    n = int((2 * EAVE_HW - .06) / pitch)
    x0 = -pitch * (n - 1) / 2
    courses = 5
    for ys in (-1, 1):
        for ci in range(n):
            x = x0 + ci * pitch
            for cover in (0, 1):
                xc = x + (pitch / 2 if cover else 0)
                if cover and ci == n - 1: continue
                w = pitch * (.3 if cover else .6)
                for k in range(courses):
                    s0 = .06 + k * .94 / courses - (.03 if k else 0)
                    s1 = .06 + (k + 1) * .94 / courses
                    Rj = random.Random(ci * 100 + k * 7 + cover * 3 + ys); dx_, dz_ = Rj.uniform(-.004, .004), Rj.uniform(-.004, .005)
                    def fn(u, v, xc=xc, w=w, s0=s0, s1=s1, cover=cover, k=k, dx_=dx_, dz_=dz_):
                        s = s0 + (s1 - s0) * v
                        y = ys * s * EAVE_Y
                        a = (u - .5) * math.pi
                        xx = xc + dx_ + math.sin(a) * w
                        arc = math.cos(a) * w * (.66 if cover else -.2)
                        lift = (.012 if cover else 0.) + .016 * (1 - v) ** 2 + .002 * k + dz_
                        z = roof_z(y, xc) + arc + lift + .012
                        return (xx, y, z)
                    o = sheet('Tile', 6, 4, fn, tm_, solid=.011, grain='y', detail=0)
                    o['grain'] = 'y'
                # eave end: disc on covers, plain drip on pans (no text, no face)
                y = ys * EAVE_Y * .995
                if cover:
                    z = roof_z(y, xc) + .012 + .014
                    cyl('Tile_Cap', (xc, y, z + .01), w * .68, .012, P['ridge'], axis='y', verts=16, detail=1, grain='z', bevel=.002)
    # gable-side cover rolls that frame the slope
    for sx in (-1, 1):
        for ys in (-1, 1):
            pts = [(sx * (EAVE_HW - .035), ys * s * EAVE_Y, roof_z(ys * s * EAVE_Y, sx * (EAVE_HW - .035)) + .05) for s in (0., .3, .6, .85, .98)]
            rope('Verge_Roll', pts, .026, P['ridge'], ply=1, tw=0., amp=.02, seg=12, step=.03)


def ridge(P):
    Z = RIDGE_Z + .012
    rbox('Ridge_Core', (0, 0, Z + .012), (2 * EAVE_HW - .2, .09, .07), P['ridge'], r=.018, amp=.004, freq=4., seed=41, div=.05)
    rbox('Ridge_Cap', (0, 0, Z + .054), (2 * EAVE_HW - .26, .055, .022), P['ridge'], r=.01, amp=.002, seed=42, div=.05)
    # end ornaments: a plain square scroll, abstract, rising to the 2.8 m limit
    prof = [(0, 0), (.1, 0), (.1, .05), (.14, .05), (.158, .07), (.158, .112), (.126, .112), (.108, .092), (.108, .078), (.055, .078), (.03, .046), (0, .036)]
    for sx in (-1, 1):
        pts = [(EAVE_HW - .22 + a if sx > 0 else -(EAVE_HW - .22 + a), b) for a, b in prof]
        if sx < 0: pts = pts[::-1]
        extrude_profile('Ridge_End', pts, .062, P['ridge'], plane='xz', p=(0, 0, Z + .0), bevel=.004, grain='x')


def under_roof(P):
    t = P['timber']
    # eave purlins, ridge purlin, tie beams at each post and gable ends; rafters visible from below
    for y, z in ((-.235, EAVE_Z + .012), (.235, EAVE_Z + .012)):
        between('Eave_Purlin', (-EAVE_HW + .07, y, z), (EAVE_HW - .07, y, z), .06, .06, t, r=.008, amp=.002, seed=int(y * 100) + 2, div=.08)
    between('Ridge_Purlin', (-EAVE_HW + .07, 0, RIDGE_Z - .05), (EAVE_HW - .07, 0, RIDGE_Z - .05), .08, .07, t, r=.009, amp=.002, seed=3, div=.08)
    for sx in (-1, 1):
        between('Tie_Beam', (sx * HW_POST, -.26, EAVE_Z - .01), (sx * HW_POST, .26, EAVE_Z - .01), .09, .1, t, r=.01, amp=.002, seed=sx + 5, div=.05)
        rbox('King_Post', (sx * HW_POST, 0, (EAVE_Z + RIDGE_Z) / 2 - .02), (.07, .07, RIDGE_Z - EAVE_Z), t, r=.008, amp=.002, seed=sx + 7, div=.05, grain='z')
        for ys in (-1, 1):
            # stepped bracket stubs under the eave beam
            rbox('Bracket', (sx * HW_POST, ys * .13, 2.2), (.08, .24, .07), t, r=.008, amp=.002, seed=sx + ys * 4 + 12, div=.04, grain='y')
            rbox('Bracket2', (sx * HW_POST, ys * .19, 2.27), (.08, .17, .06), t, r=.008, amp=.002, seed=sx + ys * 3 + 22, div=.04, grain='y')
    for ys in (-1, 1):
        for k in range(21):
            x = -1.4 + k * .14
            a = (x, ys * .07, roof_z(.07, x) - .008); b = (x, ys * .262, roof_z(.262, x) - .022)
            between('Rafter', a, b, .04, .032, t, r=.006, amp=.0012, seed=k * 2 + ys, div=.05, detail=1)
    # barge boards following the sweep at both gable ends, tip rising past the eave
    for sx in (-1, 1):
        x = sx * (EAVE_HW - .02)
        def fn(u, v, x=x):
            y = (u - .5) * 2 * EAVE_Y
            z = roof_z(y, x)
            return (x, y, z + .006 - v * .1)
        sheet('Barge', 20, 3, fn, t, solid=.03, grain='y')
    # short decking so no daylight shows between the rafters from below
    for ys in (-1, 1):
        def fn(u, v, ys=ys):
            x = (u - .5) * (2 * EAVE_HW - .1); s = .02 + v * .98
            y = ys * s * EAVE_Y
            return (x, y, roof_z(y, x) - .004)
        sheet('Decking', 30, 8, fn, P['ridge'], solid=.008, grain='y', detail=0)


def cr12(P):
    frame(P); backing(P); scraps(P); slips(P); railing(P); cup(P); under_roof(P); tiles(P); ridge(P)
    for i, q in enumerate(((-1.33, -.28, .015), (1.32, -.13, .015), (-1.3, .1, .015), (1.32, .09, .02), (.07, -.27, .012))):
        tuft('Foot_Moss', q, .035, P['moss'], seed=i)
    socket('Socket_LeanRail', (0, RAIL_Y - .07, RAIL_Z))
    S['collision'] = [((-HW_POST - .13, -.13, 0), (-HW_POST + .13, .13, 2.3)), ((HW_POST - .13, -.13, 0), (HW_POST + .13, .13, 2.3)),
                      ((-HW_POST + .07, -.01, BACK_Z0 - .08), (HW_POST - .07, .1, BACK_Z1)),
                      ((-RAIL_HW - .09, RAIL_Y - .09, 0), (-RAIL_HW + .09, RAIL_Y + .09, 1.1)), ((RAIL_HW - .09, RAIL_Y - .09, 0), (RAIL_HW + .09, RAIL_Y + .09, 1.1)),
                      ((-RAIL_HW, RAIL_Y - .06, .5), (RAIL_HW, RAIL_Y + .06, 1.04))]
