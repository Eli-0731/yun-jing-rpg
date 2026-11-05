"""CR05 work shelter and tea: four bamboo posts tied with hemp, one patched canvas roof, a bench, a separate tea bucket,
ladle, crate and bowls. Limit 4 x 3 x 2.8 m. Rear (+Y) is the high side; the roof falls to the front, so its top and patch face the viewer."""
import math
from mathutils import Vector, noise
from ti_core import S, cyl, lathe, socket, sphere
import ti_mats as tm
import mk_mats as mm
import cr_mats as cm
from cr_parts import rbox, rope, lash, xlash, pole, sheet, log, between, set_float, tuft

PX, PY = 1.72, 1.2        # post centres
TOP_F, TOP_B = 2.4, 2.72  # post tops, front and rear
BEAM_F, BEAM_B = 2.26, 2.56
OFF = .098                # beam axis to post axis


def palette():
    P = {}
    P['culm'] = cm.culm('Bamboo_Post', green=(.07, .08, .022), straw=(.27, .19, .065), mud_h=.7)
    P['culm_beam'] = cm.culm('Bamboo_Beam', green=(.08, .09, .03), straw=(.32, .23, .085), mud_h=0)
    P['hemp'] = mm.hemp('Hemp_Lashing', (.2, .125, .052), twist=40.0)
    P['canvas'] = cm.canvas('Canvas_Roof', base=(.34, .27, .16), stain=(.12, .08, .036), faded=.16, seams=(.34, .62,), dirt=1.)
    P['patch'] = cm.canvas('Canvas_Patch', base=(.11, .14, .17), stain=(.06, .065, .06), faded=.1, dirt=.7)
    P['towel'] = cm.canvas('Towel_Cloth', base=(.55, .52, .44), stain=(.26, .2, .13), faded=.2, dirt=.45)
    P['towel2'] = cm.canvas('Towel_Grey', base=(.32, .33, .32), stain=(.16, .13, .09), faded=.3, dirt=.5)
    P['sack'] = cm.canvas('Sack_Hemp', base=(.3, .22, .12), stain=(.12, .08, .04), faded=.15, dirt=.5)
    P['bench'] = cm.wood('Bench_Rough', (.075, .045, .024), (.27, .17, .09), ground_h=.14, moss=True, moss_amt=.45)
    P['crate'] = cm.wood('Crate_Pine', (.09, .055, .028), (.3, .19, .095), ground_h=.1, grey=.35)
    P['stave'] = cm.wood('Bucket_Stave', (.085, .048, .024), (.28, .16, .08), wet_z=.2, ground_h=0, grey=.15)
    P['ladle'] = cm.wood('Ladle_Wood', (.12, .07, .034), (.36, .22, .11), ground_h=0, polish=.2, grey=0)
    P['iron'] = tm.metal('Nail_Iron', (.06, .055, .05), (.13, .07, .035), rough=.55, patina_amt=.6)
    P['tea'] = cm.tea('Tea_Surface')
    P['bowl'] = cm.clay('Bowl_Clay')
    P['moss'] = cm.moss_tuft('Moss_Tuft')
    P['mud'] = mm.soil('Foot_Mud')
    return P


def posts(P):
    tops = {(-1, -1): TOP_F, (1, -1): TOP_F - .02, (-1, 1): TOP_B + .015, (1, 1): TOP_B}
    leans = {(-1, -1): (-.03, -.012), (1, -1): (.018, -.02), (-1, 1): (-.02, .015), (1, 1): (.024, .01)}
    for i, ((sx, sy), z) in enumerate(tops.items()):
        lx, ly = leans[(sx, sy)]
        pole('Post', (sx * PX, sy * PY, 0), (sx * PX + lx, sy * PY + ly, z), .082, .068, P['culm'], node_gap=.42, bend=.012, seed=i + 1, cut=.55)


def px(sx, sy, z):
    """Post centre at height z, including its lean."""
    H = TOP_F if sy < 0 else TOP_B
    lean = {(-1, -1): (-.03, -.012), (1, -1): (.018, -.02), (-1, 1): (-.02, .015), (1, 1): (.024, .01)}[(sx, sy)]
    t = z / H
    return Vector((sx * PX + lean[0] * t, sy * PY + lean[1] * t, z))


def beams(P):
    c, h = P['culm_beam'], P['hemp']
    # cross beams along X, tied on the outside of each post pair, ends running past the posts
    for k, (sy, z) in enumerate(((-1, BEAM_F), (1, BEAM_B))):
        a = px(-1, sy, z) + Vector((0, sy * OFF, 0)); b = px(1, sy, z) + Vector((0, sy * OFF, 0))
        o = (b - a).normalized()
        pole('Beam_X', tuple(a - o * .225), tuple(b + o * .225), .056, .048, c, node_gap=.5, bend=.02, seed=10 + k, cut=.3)
        for sx in (-1, 1):
            q = px(sx, sy, z) + Vector((0, sy * .05, 0))
            xlash('Lash_XZ', q, (0, 0, 1), .074, o, .052, .0145, h, tail=(sx * .03, sy * .03, -.22) if sx * sy < 0 else None)
    # side rails run front to rear, sloped, just under the cross beams
    for k, sx in enumerate((-1, 1)):
        a = px(sx, -1, BEAM_F - .1) + Vector((sx * OFF, 0, 0)); b = px(sx, 1, BEAM_B - .1) + Vector((sx * OFF, 0, 0))
        o = (b - a).normalized()
        pole('Rail_Y', tuple(a - o * .15), tuple(b + o * .15), .046, .04, c, node_gap=.5, bend=.018, seed=20 + k, cut=.3)
        for sy, q0 in ((-1, a), (1, b)):
            xlash('Lash_YZ', q0 - Vector((sx * .05, 0, 0)), (0, 0, 1), .074, o, .044, .012, h)
    # the towel rope, slack, between the two left posts (the rope the towels hang on)
    a = px(-1, -1, 1.68) + Vector((-.07, 0, 0)); b = px(-1, 1, 1.68) + Vector((-.07, 0, 0))
    S['towel_line'] = (a.copy(), b.copy())
    rope('Towel_Line', [tuple(a), tuple(a.lerp(b, .33) + Vector((0, 0, -.045))), tuple(a.lerp(b, .66) + Vector((0, 0, -.05))), tuple(b)], .0105, h, tw=70.)
    for q, y in ((a, 0), (b, 0)):
        lash('Towel_Tie', q + Vector((.07, 0, 0)), (0, 0, 1), .074, .05, .011, h, turns=4)
    # a slack brace rope, front left
    q0 = px(-1, -1, 2.02) + Vector((.06, 0, 0)); q1 = px(-1, -1, BEAM_F) + Vector((.55, -OFF, -.03))
    rope('Brace', [tuple(q0), tuple(q0.lerp(q1, .5) + Vector((0, 0, -.035))), tuple(q1)], .0098, h, tw=70.)
    lash('Brace_Tie', q1, (1, 0, 0), .056, .04, .0095, h, turns=3)
    # a tie below the rail on each front post
    for sx in (-1, 1):
        lash('Post_Band', px(sx, -1, 1.2), (0, 0, 1), .076, .07, .011, h, turns=6, detail=2)


def roof_z(u_y):
    """Height of the taut sheet at y between the two beams (0 front beam .. 1 rear beam)."""
    return BEAM_F + .058 + (BEAM_B - BEAM_F) * u_y


def canvas(P):
    """Taut over the beams, bellied between them, then hanging as a short valance: long at the front, short at the rear and sides."""
    hx = 1.82                          # side rails
    yf, yb = -PY - .115, PY + .115     # beam tops
    over_f, over_b, over_s = .3, .17, .17
    span_x = 2 * (hx + over_s); span_y = (yb - yf) + over_f + over_b
    def fn(u, v):
        xp = (u - .5) * span_x
        yp = yf - over_f + v * span_y
        ox = max(0., abs(xp) - hx)
        x = math.copysign(min(abs(xp), hx + min(ox, .05)), xp)
        y = min(max(yp, yf), yb)
        t = (y - yf) / (yb - yf)
        z = roof_z(t)
        across = max(0., 1 - (x / hx) ** 2)
        z -= .26 * math.sin(math.pi * t) ** .85 * across ** .6 + .07 * across * (1 - math.sin(math.pi * t))
        d_f = max(0., yf - yp); d_b = max(0., yp - yb)
        if d_f:
            y = yf - min(d_f, .05) - (.03 * math.sin(x * 5.1 + 1.) + .014 * math.sin(x * 11.3)) * min(1, d_f * 4)
            z -= (max(0., d_f - .03) + .03 * d_f) * (.86 + .14 * math.sin(x * 2.3 + .4))
        if d_b:
            y = yb + min(d_b, .05) + (.024 * math.sin(x * 5.7) + .01 * math.sin(x * 12.1)) * min(1, d_b * 5)
            z -= max(0., d_b - .03) + .03 * d_b
        if ox:
            z -= max(0., ox - .03) + .03 * ox
            x += math.copysign(.022 * math.sin(y * 6.3) * min(1, ox * 5), xp)
        p = Vector((x, y, 0))
        for (cx, cy) in ((-1.72, -1.28), (1.72, -1.28), (-1.72, 1.28), (1.72, 1.28)):
            d = p - Vector((cx, cy, 0))
            ang = math.atan2(d.y, d.x); dist = d.length
            z += .036 * math.sin(ang * 9 + cx) * math.exp(-dist / .62)
        z += .016 * noise.noise(p * 1.6) + .005 * noise.noise(p * 6.)
        z += (.036 * math.sin(x * 4.9 + 1.5 * math.sin(y * 1.7) + .8) + .014 * math.sin(x * 11.3 + 2.6 * math.sin(y * 2.3))) * math.sin(math.pi * t) * across ** .5 - .05 * math.sin(math.pi * t) * across ** .5
        edge = min(u, 1 - u, v, 1 - v)
        q = Vector((u * 22, v * 22, 2.))
        z += .05 * math.exp(-edge / .02) * noise.noise(q)          # hem not quite level
        return (x, y, z)
    def keep(u, v):
        # whole cloth; only the very edge frays
        edge = min(u, 1 - u, v, 1 - v)
        if edge > .05: return True
        return edge > .004 * max(0., noise.noise(Vector((u * 70, v * 70, 1.))) + .12)
    sheet('Canvas', 120, 96, fn, P['canvas'], solid=.005, keep=keep, group='Canopy', grain='y')
    S['canvas_fn'] = fn
    # newer patch: blue-grey cloth with its own rough stitches
    u0, u1, v0, v1 = .62, .79, .3, .5
    def pf(a, b):
        x, y, z = fn(u0 + (u1 - u0) * a, v0 + (v1 - v0) * b)
        return (x, y, z + .011)
    def pkeep(a, b):
        return min(a, 1 - a, b, 1 - b) > .012 + .018 * max(0., noise.noise(Vector((a * 14, b * 14, 4.))))
    sheet('Patch', 26, 30, pf, P['patch'], solid=.003, keep=pkeep, group='Canopy', grain='y')
    n = 0
    for side in range(4):
        for k in range(9):
            t = (k + .5) / 9
            a, b = {0: (t, 0.), 1: (1., t), 2: (t, 1.), 3: (0., t)}[side]
            ia = a + (.5 - a) * .07; ib = b + (.5 - b) * .07
            oa = a - (.5 - a) * .05; ob = b - (.5 - b) * .05
            p0 = Vector(pf(ia, ib)) + Vector((0, 0, .004)); p1 = Vector(pf(oa, ob)) + Vector((0, 0, .002))
            rope('Stitch', [tuple(p0), tuple(p1)], .0034, P['hemp'], group='Canopy', detail=2, seg=5, step=.02, ply=2); n += 1
    # corner ties pulling the cloth onto the beam ends
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        z = BEAM_F if sy < 0 else BEAM_B
        q = px(sx, sy, z) + Vector((sx * .17, sy * OFF, 0))
        u = .5 + sx * .49; v = (.5 + sy * .36)
        qc = Vector(fn(u, v))
        rope('Corner_Tie', [tuple(qc + Vector((0, 0, .004))), tuple(qc.lerp(q, .5) + Vector((0, 0, .008))), tuple(q)], .0085, P['hemp'], group='Canopy')
    # a few thin torn strips hanging from the front hem and the right side
    for i, (u, L) in enumerate(((.2, .16), (.39, .1), (.66, .18), (.87, .12))):
        top = Vector(fn(u, .002))
        def tf(a, b, top=top, L=L, i=i):
            w = .04 + (i % 3) * .014
            jag = .35 + .65 * (.5 + .5 * math.sin(a * 9 + i * 2)) if b > .85 else 1.
            return tuple(top + Vector(((a - .5) * 2 * w * (1 - b * .25) + math.sin(b * 4 + i) * .012, math.cos(b * 3 + i) * .012 - .004, .006 - L * b * jag)))
        sheet('Tatter', 4, 8, tf, P['canvas'], solid=.003, group='Canopy', grain='z', detail=1)


def towel(P, name, t, w, L1, L2, mat, seed):
    a, b = S['towel_line']
    c = a.lerp(b, t) + Vector((0, 0, -.045 * math.sin(math.pi * t) * 1.1))
    def fn(u, v, c=c):
        ang = (v - L2 / (L1 + L2)) * (L1 + L2)     # signed length along the cloth from the rope
        yy = (u - .5) * w
        fold = .012 * math.sin(u * 15 + seed) + .006 * math.sin(u * 37 + seed * 2)
        if abs(ang) < .025:
            th = ang / .025 * math.pi / 2
            return (c.x + .014 * math.sin(th), c.y + yy, c.z + .014 * math.cos(th))
        s = ang - math.copysign(.025, ang)
        side = 1 if ang > 0 else -1
        return (c.x + side * (.014 + abs(s) * .03) + fold * min(1, abs(s) * 5) * side, c.y + yy * (1 - abs(s) * .07), c.z - abs(s))
    def keep(u, v):
        e = min(v, 1 - v)
        return not (e < .03 and noise.noise(Vector((u * 40, seed, v * 5.))) > .1)
    sheet(name, 16, 40, fn, mat, solid=.003, keep=keep, grain='z')


def bench(P):
    b, g = P['bench'], 'Bench'
    L, cx, cy, top = 1.62, -.52, -.12, .445
    for i, (dy, w) in enumerate(((-.082, .158), (.088, .15))):
        rbox('Seat', (cx, cy + dy, top - .043), (L + i * .05 - .02, w, .086), b, r=.014, amp=.007, freq=4., chips=3, hew=5, seed=i + 2, div=.05, group=g, grain='x')
    # A-frame legs with a through tenon and a stretcher
    for sx in (-1, 1):
        x = cx + sx * (L / 2 - .2)
        for sy in (-1, 1):
            between('Leg', (x, cy + sy * .09, top - .06), (x + sx * .03, cy + sy * .17, 0), .105, .064, b, r=.01, amp=.003, seed=int(5 + sx + sy * 3), div=.04, group=g)
        rbox('Leg_Tie', (x, cy, .25), (.064, .3, .07), b, r=.008, amp=.002, seed=6 + sx, div=.04, group=g, grain='y')
        for sy in (-1, 1):
            rbox('Wedge', (x, cy + sy * .08, top + .002), (.03, .04, .006), P['crate'], r=.002, div=.02, group=g, grain='y', detail=1)
    rbox('Stretcher', (cx, cy, .25), (L - .42, .06, .062), b, r=.008, amp=.002, seed=9, div=.05, group=g, grain='x')
    socket('Socket_Sit_01', (cx - .4, cy, top))
    socket('Socket_Sit_02', (cx + .4, cy, top))


def crate(P):
    c, g = P['crate'], 'Crate'
    cx, cy = 1.06, -.42; W, D, H = .68, .5, .4
    for sy in (-1, 1):
        for k in range(4):
            z = .03 + k * .095
            rbox('Slat', (cx, cy + sy * (D / 2 - .009), z + .04), (W - .05, .018, .085 - (k % 2) * .004), c, r=.003, amp=.0018, seed=k + sy * 9, div=.05, group=g, grain='x')
    for sx in (-1, 1):
        for k in range(4):
            z = .03 + k * .095
            rbox('Slat', (cx + sx * (W / 2 - .009), cy, z + .04), (.018, D - .05, .085), c, r=.003, amp=.0018, seed=k + sx * 5 + 30, div=.05, group=g, grain='y')
        for sy in (-1, 1):
            rbox('Corner', (cx + sx * (W / 2 - .018), cy + sy * (D / 2 - .018), H / 2), (.04, .04, H), c, r=.005, amp=.002, seed=int(40 + sx + 3 * sy), div=.05, group=g, grain='z')
    for k in range(5):
        y = cy - D / 2 + (k + .5) * D / 5
        rbox('Lid', (cx, y, H + .007), (W + .02, D / 5 - .006, .018), c, r=.003, amp=.002, seed=k + 50, div=.05, group=g, grain='x')
        for sx in (-1, 1):
            cyl('Nail', (cx + sx * (W / 2 - .02), y, H + .0165), .0048, .004, P['iron'], verts=8, group=g, detail=2, bevel=.001)
    # cloth thrown over the corner of the lid
    def cf(u, v):
        x0, y0 = cx + .1, cy - D / 2 - .012
        x = x0 + u * .2
        s = v * .46
        if s < .2:
            return (x, y0 + .2 - s, H + .019 + .004 * math.sin(u * 9))
        d = s - .2
        return (x + .004 * math.sin(d * 18), y0 - .002 - d * .02 + .003 * math.sin(u * 13 + d * 12), H + .019 - d)
    sheet('Crate_Cloth', 10, 24, cf, P['towel'], solid=.0028, group=g, grain='y', detail=1)
    # low stand the bucket sits on
    sx0, sy0 = .55, .02
    for i in range(3):
        rbox('Stand_Top', (sx0, sy0 - .17 + i * .17, .285), (.55, .16, .03), c, r=.004, amp=.002, seed=i + 60, div=.05, group=g, grain='x')
    for dx in (-.21, .21):
        rbox('Stand_Leg', (sx0 + dx, sy0, .135), (.05, .46, .27), c, r=.006, amp=.002, seed=int(dx * 100), div=.05, group=g, grain='z')
    S['bucket_at'] = (sx0, sy0, .3)
    S['crate_top'] = (cx, cy, H + .016)


def bucket(P):
    g = 'TeaBucket'; bx, by, bz = S['bucket_at']
    H, R0, R1 = .34, .225, .27; n = 22
    for i in range(n):
        a = i / n * math.tau; a1 = (i + 1) / n * math.tau
        mid = (a + a1) / 2; w0 = R0 * math.tau / n * .485; w1 = R1 * math.tau / n * .485
        verts = []
        for z, r, w in ((0, R0, w0), (H * .5, (R0 + R1) / 2 + .004, (w0 + w1) / 2), (H, R1, w1)):
            for rr, ww in ((r, w), (r - .022, w * .9)):
                cx, cy = math.cos(mid) * rr, math.sin(mid) * rr
                tx, ty = -math.sin(mid), math.cos(mid)
                for s in (-1, 1):
                    verts.append((bx + cx + tx * s * ww, by + cy + ty * s * ww, bz + z + (.004 if i % 5 == 0 and z == H else 0)))
        faces = []
        for row in range(2):
            b = row * 4; t = b + 4
            faces += [(b + 0, b + 1, t + 1, t + 0), (b + 1, b + 3, t + 3, t + 1), (b + 3, b + 2, t + 2, t + 3), (b + 2, b + 0, t + 0, t + 2)]
        faces += [(8, 9, 11, 10), (0, 2, 3, 1)]
        from ti_core import mesh
        o = mesh('Stave', verts, faces, P['stave'], smooth=False, group=g, grain='z')
        m = o.modifiers.new('Soft', 'BEVEL'); m.width = .0022; m.segments = 2; m.limit_method = 'ANGLE'
    lathe('Bucket_Floor', [(0, .012), (R0 - .012, .012), (R0 - .012, .03), (0, .03)], (bx, by, bz), P['stave'], seg=32, group=g)
    # three wrapped hoops of rope and split wood
    for i, (z, r) in enumerate(((.055, R0 + (R1 - R0) * .16), (.17, (R0 + R1) / 2 + .004), (.3, R0 + (R1 - R0) * .88))):
        pts = [(bx + math.cos(k / 40 * math.tau) * (r + .004), by + math.sin(k / 40 * math.tau) * (r + .004), bz + z) for k in range(41)]
        rope('Hoop', pts, .0085, P['hemp'], tw=60., curve=2, group=g)
    # tea surface
    lathe('Tea', [(R1 - .03, H - .06), (R1 - .032, H - .05), (0, H - .05)], (bx, by, bz), P['tea'], seg=40, group=g)
    socket('Socket_TeaSurface', (bx, by, bz + H - .05))
    # ladle resting in the bucket, handle over the rim
    g = 'Ladle'
    # a bamboo dipper: a small open cylinder standing half in the tea, one straight thin handle resting on the bucket rim
    slope, cr, ch, wall = .17, .048, .092, .006
    rim = Vector((bx + R1 - .012, by - .05, bz + H + .012))
    d = Vector((rim.x - bx + .05, rim.y - by - .03, 0)).normalized()
    up = Vector((0, 0, slope))
    wall_at = rim - (d + up) * .2
    cup = wall_at - d * (cr - .004)
    top = cup.z + .022
    lathe('Ladle_Cup', [(0, -ch), (cr - .004, -ch), (cr, -ch + .005), (cr + .0015, -ch * .5), (cr, -.002), (cr - .002, 0), (cr - wall + .001, 0), (cr - wall, -.003), (cr - wall, -ch + .009), (0, -ch + .009)], (cup.x, cup.y, top), P['ladle'], seg=28, group=g)
    tip = rim + (d + up) * .36
    log('Ladle_Handle', [tuple(wall_at), tuple(rim), tuple(tip)], .0085, P['ladle'], seg=8, lump=.015, seed=2, group=g, grain=tuple((tip - wall_at).normalized()))


def bowl(P, name, x, y, z, seed):
    prof = [(0, 0), (.032, 0), (.037, .004), (.035, .012), (.05, .022), (.07, .046), (.08, .068), (.083, .074), (.08, .077), (.076, .07), (.064, .05), (.04, .026), (0, .018)]
    prof = [(r, zz) for r, zz in prof]
    o = lathe(name, prof, (x, y, z), P['bowl'], seg=32, group=name)
    # glaze stops short of the foot and the lip
    set_float(o, 'gmask', lambda c: 0. if (c.z < .022 or c.z > .072) and (c.x * c.x + c.y * c.y) > .0005 else 1.)
    for v in o.data.vertices:
        v.co.x += .0014 * math.sin(v.co.z * 80 + seed); v.co.y += .0012 * math.cos(v.co.z * 70 + seed)


def bowls(P):
    cx, cy, top = S['crate_top']
    bowl(P, 'Bowl_01', cx - .16, cy - .1, top, 1)
    bowl(P, 'Bowl_02', cx + .02, cy + .1, top, 2)
    bowl(P, 'Bowl_03', cx + .02, cy + .1, top + .03, 3)    # nested in Bowl_02
    bowl(P, 'Bowl_04', cx + .2, cy - .06, top, 4)
    socket('Socket_Serve', (cx, cy, top))


def sack(P):
    def fn(u, v):
        a = u * math.tau; r = .13 * math.sin(math.pi * min(1, v * 1.02)) ** .55 * (1 + .1 * math.sin(a * 3 + v * 4))
        neck = max(0, v - .72) / .28
        r = r * (1 - neck * .72)
        return (.2 + r * math.cos(a), .42 + r * math.sin(a) * .9, v * .34)
    from ti_core import surface
    o = surface('Sack', 28, 26, fn, P['sack'], closed_u=True, grain='z')
    from cr_parts import set_attr_list
    set_attr_list(o, 'cuv', [(.5, .5, 0.)] * len(o.data.vertices))
    lash('Sack_Tie', (.2, .42, .265), (0, 0, 1), .052, .022, .0052, P['hemp'], turns=3)


def cr05(P):
    posts(P); beams(P); canvas(P)
    towel(P, 'Towel_A', .2, .36, .74, .34, P['towel'], 1)
    towel(P, 'Towel_B', .64, .3, .54, .26, P['towel2'], 4)
    crate(P); bench(P); bucket(P); bowls(P); sack(P)
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        tuft('Foot_Moss', (sx * (PX + .075), sy * PY, .008), .03, P['moss'], seed=i + 3)
        rbox('Foot_Mud', (sx * PX, sy * PY, .018), (.2, .185, .026), P['mud'], r=.012, amp=.014, freq=30., seed=i + 7, div=.02, sharp=70, detail=1)
    S['collision'] = [((sx * PX - .09, sy * PY - .09, 0), (sx * PX + .09, sy * PY + .09, (TOP_F if sy < 0 else TOP_B))) for sx in (-1, 1) for sy in (-1, 1)]
