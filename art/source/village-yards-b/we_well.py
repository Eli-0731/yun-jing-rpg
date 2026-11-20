"""WE01 village well under a small pavilion, in daily use, at the A1 village centre (work pack 2026-11-11 B-40h, batch A, WE01; the batch sample).

Chosen sheet WE01-cand-4: a round dressed-stone well ring with a coping course, water a little way down inside; a wooden windlass on
two uprights beside the ring, the drum wound with rope, a crank on the right, the rope hanging down into the water; one wooden bucket
on the paving by the ring. Four square timber posts on stone pads carry a small hanging-gable roof of dark grey pan-and-roll tiles
(the VL tiles, ridge along x, curled ridge ends), with a lower beam and a plate on the long sides, an open king-post truss in each gable
and knee braces lashed to the posts with rope. Underfoot an irregular round pad of flagstones, worn smooth and darkened wet in front of
the well and round the bucket, grass in the joints and at the edge. Not the D3 dry well: this one is in use (clean water, rope on the
drum, wet stones). No people, no writing.

Sizes (limit 3.5 x 3.5 x 3.6 m): pad about 3.3 m across; posts on a 2.56 x 2.10 m grid, plinths 0.38 m square and 0.32 m tall; well ring
1.12 m across, 0.76 m tall, water 0.45 m below the rim; eaves at y +-1.72 m, about 2.35 m above the ground at the front; ridge about 3.45 m.
The roof is the VL roof frame at 0.65 scale (vl_roof keeps 12 courses a slope; at full scale the courses would come out short and wide).
A walker comes in between the front posts (2.18 m clear) and stands at the ring to draw water; the back is open the same way.
Origin: centre of the pad, bottom z = 0, front (the crank side faces +x; the open long side) -Y.
"""
import math, random
from mathutils import Matrix, Vector, noise
from ti_core import S, box, cyl, lathe, torus, socket, mesh, xf, T
from cr_parts import rbox, rope, lash
import fr_parts as FP
import vl_mats, cr_mats as cm, ti_mats as tm, mk_mats as mm
import vl_roof as RF
import vh_roof as VR

W, D, H = 3.5, 3.5, 3.6
PAD_R, PAD_TOP = 1.62, .05
PX, PY = 1.28, 1.05                     # post centres
PLINTH, PLINTH_H, POST = .38, .32, .18
RING_R, RING_IN, RING_TOP = .56, .40, .81   # outer / inner radius, rim height (on the pad)
WATER_Z = RING_TOP - .45
WIND_X, AXLE_Z, DRUM_R = .64, 1.18, .075
BUCKET = (.66, -.74)
SC, YC = .65, 0.
ROOF = dict(z0=3.60, rise=1.46, depth_front=1.72 / SC, depth_back=1.72 / SC, xh=1.5 / SC, lift_eave=.15, lift_end=.06)


def under_w(x, y):
    """Underside of the roof boards at world (x, y)."""
    return SC * VR.under(x / SC, (y - YC) / SC)


def palette():
    P = vl_mats.palette('diligent')          # a well everyone uses: kept up, little peel or moss
    # the sheet's timber is a weathered mid brown, a little lighter than the smoke-dark VL05 frames
    P['timber'] = cm.wood('Pavilion_Timber', (.06, .032, .015), (.22, .125, .06), grey=.35, ground_h=.15, moss=False)
    P['windlass'] = cm.wood('Windlass_Wood', (.05, .028, .014), (.2, .115, .055), grey=.3, ground_h=0., polish=.35)   # hands polish the drum and crank
    P['stave'] = cm.wood('Bucket_Stave', (.06, .034, .017), (.22, .13, .065), wet_z=.18, ground_h=0., grey=.2)
    P['roof'] = RF.roof_material()
    P['hemp'] = mm.hemp('Well_Rope', (.2, .15, .075), twist=150.)
    P['ring'] = [cm.stone(f'Well_Ring_Stone_{i}', light=l, dark=d, ochre=(.22, .2, .16), moss=.55, lichen=.4, crack=.35, wet_z=.42)
                 for i, (l, d) in enumerate((((.24, .23, .21), (.11, .105, .095)), ((.22, .215, .2), (.1, .097, .09))))]
    P['coping'] = cm.stone('Well_Coping', light=(.25, .24, .22), dark=(.11, .105, .095), ochre=(.2, .18, .14), moss=.25, lichen=.3, crack=.3,
                           polish=(.5, .48, .44))
    P['pave'] = [cm.stone(f'Well_Paving_{i}', light=l, dark=d, ochre=(.22, .19, .14), moss=.7, lichen=.4, crack=.45)
                 for i, (l, d) in enumerate((((.23, .22, .2), (.1, .096, .088)), ((.21, .2, .185), (.09, .087, .08)), ((.25, .235, .21), (.11, .1, .09))))]
    # flags in front of the ring and round the bucket: darkened by spilt water every day
    P['pave_wet'] = cm.stone('Well_Paving_Wet', light=(.1, .098, .092), dark=(.04, .039, .036), ochre=(.12, .11, .09), moss=.5, lichen=.1, crack=.4,
                             polish=(.3, .29, .27))
    P['plinth'] = cm.stone('Post_Plinth', light=(.23, .22, .2), dark=(.1, .095, .085), ochre=(.22, .19, .14), moss=.9, lichen=.6, crack=.5)
    P['earth'] = cm.packed_earth('Pad_Earth', dark=(.05, .04, .028), light=(.16, .125, .085), moss=.4)
    P['water'] = tm.plain('Well_Water', (.012, .04, .042), rough=.08, noise=.25, scale=6.)
    P['shaft'] = cm.stone('Well_Shaft', light=(.08, .085, .08), dark=(.025, .027, .026), moss=1.2, lichen=0., crack=.2)
    return P


# ------------------------------------------------------------------ the pad: Voronoi flagstones on an earth disc
def _wobble(phi):
    return PAD_R + .06 * noise.noise(Vector((math.cos(phi) * 1.3, math.sin(phi) * 1.3, 2.))) + .025 * noise.noise(Vector((math.cos(phi) * 4, math.sin(phi) * 4, 5.)))


def pad(P, R):
    # earth bed under the flags, its rim following the same wobbled outline as the outer flags (no even ring showing past them)
    n = 96; rings = ((-.12, .024), (-.03, .016), (.03, 0.))
    V = [(0., 0., .024)]
    for dr, z in rings:
        V += [((_wobble(math.tau * i / n) + dr) * math.cos(math.tau * i / n), (_wobble(math.tau * i / n) + dr) * math.sin(math.tau * i / n), z) for i in range(n)]
    F = [(0, 1 + i, 1 + (i + 1) % n) for i in range(n)]
    for r_ in range(len(rings) - 1):
        F += [(1 + r_ * n + i, 1 + (r_ + 1) * n + i, 1 + (r_ + 1) * n + (i + 1) % n, 1 + r_ * n + (i + 1) % n) for i in range(n)]
    F.append(tuple(1 + (len(rings) - 1) * n + i for i in range(n - 1, -1, -1)))
    mesh('Pad_Earth', V, F, P['earth'], smooth=True, group='Main', grain='z')
    Rp = random.Random('WE01_pad')
    # dart-throwing: big flags where feet go round the ring, smaller ones and slivers at the rim, no grid left in it
    sites = []
    for _ in range(4000):
        x, y = Rp.uniform(-PAD_R, PAD_R), Rp.uniform(-PAD_R, PAD_R); r = math.hypot(x, y)
        if r > PAD_R - .04: continue
        dmin = .46 if r < 1.15 else .34
        if all(math.hypot(x - a, y - b) > dmin * Rp.uniform(.85, 1.1) for a, b in sites): sites.append((x, y))
    wet = lambda x, y: (y < -.2 and abs(x) < .9 and math.hypot(x, y) < 1.3) or math.hypot(x - BUCKET[0], y - BUCKET[1]) < .45
    n_ray = 22
    for k, (sx, sy) in enumerate(sites):
        if math.hypot(sx, sy) < RING_R - .12: continue                       # under the ring: nothing shows
        poly = []
        for q in range(n_ray):
            a = math.tau * q / n_ray; d = Vector((math.cos(a), math.sin(a)))
            t = _wobble(math.atan2(sy + d.y * .5, sx + d.x * .5)) * 1.0
            # the disc's edge along this ray
            px, py = sx, sy; b = px * d.x + py * d.y; c = px * px + py * py - _wobble(a) ** 2
            tdisc = -b + math.sqrt(max(0., b * b - c))
            t = tdisc
            for (ox, oy) in sites:
                if (ox, oy) == (sx, sy): continue
                v = Vector((ox - sx, oy - sy)); dv = v.dot(d)
                if dv > 1e-6: t = min(t, v.length_squared / (2 * dv))
            t -= .012 + .012 * (1 + noise.noise(Vector((sx * 3 + d.x * .6, sy * 3 + d.y * .6, k * .37))))      # hand-dressed edges: gaps 1.2-3.6 cm
            poly.append((sx + d.x * t, sy + d.y * t))
        area = sum(poly[i][0] * poly[(i + 1) % n_ray][1] - poly[(i + 1) % n_ray][0] * poly[i][1] for i in range(n_ray)) / 2
        if area < .015: continue
        top = PAD_TOP + Rp.uniform(-.008, .008); tx, ty = Rp.uniform(-.02, .02), Rp.uniform(-.02, .02)
        zt = lambda x, y: top + tx * (x - sx) + ty * (y - sy) + .0015 * noise.noise(Vector((x * 6, y * 6, k)))
        bev = .01
        inner = [(sx + (x - sx) * .95, sy + (y - sy) * .95) for x, y in poly]
        V = [(sx, sy, zt(sx, sy))]
        V += [(x, y, zt(x, y)) for x, y in inner]
        V += [(x, y, zt(x, y) - bev) for x, y in poly]
        V += [(x, y, .006) for x, y in poly]          # bottoms inside the earth disc, not on its underside
        F = []
        for i in range(n_ray):
            j = (i + 1) % n_ray
            F.append((0, 1 + i, 1 + j))
            F.append((1 + i, 1 + n_ray + i, 1 + n_ray + j, 1 + j))
            F.append((1 + n_ray + i, 1 + 2 * n_ray + i, 1 + 2 * n_ray + j, 1 + n_ray + j))
        F.append(tuple(1 + 2 * n_ray + i for i in range(n_ray - 1, -1, -1)))
        mat = P['pave_wet'] if wet(sx, sy) else Rp.choice(P['pave'])
        mesh('Pad_Flag', V, F, mat, smooth=False, group='Stone', grain='z')      # dressed flags: crisp arris, flat face
    S['pad_sites'] = len(sites)


# ------------------------------------------------------------------ the well
def ring_block(name, phi, r_out, z0, z1, L, depth, mat, seed, tilt=0., **kw):
    """A block laid on the circle: outer face on r_out, bent to the curve."""
    rc = r_out - depth / 2
    def warp(q, rr=r_out):
        q.y += q.x * q.x / (2 * rr)
    return rbox(name, (rc * math.cos(phi), rc * math.sin(phi), (z0 + z1) / 2), (L, depth, z1 - z0), mat, r=.02, amp=.01, freq=5., chips=3, hew=3,
                seed=seed, div=.04, rot=(tilt, 0, phi + math.pi / 2), warp=warp, **kw)


def well(P, R):
    Rw = random.Random('WE01_well')
    # three courses of dressed blocks of uneven length, joints broken course to course, each block a little proud or sunk and leaning
    courses = [(PAD_TOP - .02, .25), (.25, .44), (.44, .62)]
    for c, (z0, z1) in enumerate(courses):
        cuts = [0.]
        while cuts[-1] < math.tau - .5:
            cuts.append(cuts[-1] + Rw.uniform(.5, .85))
        cuts[-1] = math.tau
        ph = Rw.uniform(0, math.tau)
        for i in range(len(cuts) - 1):
            a0, a1 = ph + cuts[i], ph + cuts[i + 1]; mid = (a0 + a1) / 2
            L = (a1 - a0) * RING_R - Rw.uniform(.012, .02)
            ring_block('Ring_Block', mid, RING_R + Rw.uniform(-.01, .012), z0 + .004, z1 - .005 - Rw.uniform(0, .01),
                       L, RING_R - RING_IN, Rw.choice(P['ring']), seed=c * 40 + i, tilt=Rw.uniform(-.025, .025), group='Stone')
    # coping: eight curved slabs, a little proud of the ring outside and in, worn smooth on top
    cuts = [0.]
    while cuts[-1] < math.tau - .6:
        cuts.append(cuts[-1] + Rw.uniform(.65, 1.05))
    cuts[-1] = math.tau; ph = Rw.uniform(0, math.tau)
    for i in range(len(cuts) - 1):
        a0, a1 = ph + cuts[i], ph + cuts[i + 1]; mid = (a0 + a1) / 2
        ro = RING_R + .035 + Rw.uniform(-.008, .008)
        ring_block('Ring_Coping', mid, ro, .62, RING_TOP - Rw.uniform(0, .012), (a1 - a0) * ro - Rw.uniform(.01, .016), ro - (RING_IN - .025), P['coping'],
                   seed=90 + i, tilt=Rw.uniform(-.015, .015), group='Stone')
    # inside: the dark shaft wall from the water up under the coping, and the water
    lathe('Well_Shaft', [(RING_IN - .005, WATER_Z - .02), (RING_IN - .005, .63), (RING_IN + .02, .63), (RING_IN + .02, WATER_Z - .02)], (0., 0., 0.), P['shaft'],
          seg=40, group='Stone')
    lathe('Well_Water', [(0., WATER_Z), (RING_IN - .004, WATER_Z), (RING_IN - .004, WATER_Z - .02), (0., WATER_Z - .02)], (0., 0., 0.), P['water'], seg=40, group='Main')
    socket('Socket_WellWater', (0., 0., WATER_Z))
    # moss low round the foot of the ring, more on the shaded back
    for j in range(22):
        a = Rw.uniform(0, math.tau); r = RING_R + .01
        if math.sin(a) < -.3 and Rw.random() < .5: continue
        zc = Rw.choice((PAD_TOP + .04, PAD_TOP + .06, .25, .44)) if math.sin(a) > -.2 else PAD_TOP + .04     # foot all round, joints on the shaded back
        FP.moss_patch('Ring_Moss', (r * math.cos(a), r * math.sin(a), zc), (math.cos(a), math.sin(a), .15), Rw.uniform(.07, .13), P['moss'],
                      seed=300 + j, flat=.7, snap_each=True)


def windlass(P, R):
    t = P['windlass']
    for sx in (-1, 1):
        x = sx * WIND_X
        # an upright standing on the pad beside the ring, a shallow fork at the top cradling the axle
        rbox(f'Windlass_Post_{sx}', (x, 0., (PAD_TOP + AXLE_Z + .07) / 2), (.13, .15, AXLE_Z + .07 - PAD_TOP), P['timber'], r=.012, amp=.003, hew=3, seed=200 + sx,
             div=.05, group='Wood', grain='z')
        for dy in (-1, 1):
            box(f'Windlass_Fork_{sx}_{dy}', (x, dy * .06, AXLE_Z + .1), (.13, .035, .07), P['timber'], bevel=.006, group='Wood', grain='z')
        # a brace from the ring's coping to each upright
        box(f'Windlass_Foot_{sx}', (x - sx * .02, 0., PAD_TOP + .06), (.2, .17, .12), P['timber'], bevel=.01, group='Wood', grain='x')
    # the axle with its drum, a crank on the right
    cyl('Windlass_Axle', (.08, 0., AXLE_Z), .035, 2 * WIND_X + .36, t, axis='x', verts=14, group='Wood', grain='x')
    cyl('Windlass_Drum', (0., 0., AXLE_Z), DRUM_R, 2 * WIND_X - .2, t, axis='x', verts=20, group='Wood', grain='x')
    for sx in (-1, 1):
        cyl(f'Drum_Collar_{sx}', (sx * (WIND_X - .1), 0., AXLE_Z), DRUM_R + .018, .035, t, axis='x', verts=20, group='Wood', grain='x')
    xc = WIND_X + .17
    box('Crank_Arm', (xc, 0., AXLE_Z - .1), (.04, .05, .26), t, bevel=.008, group='Wood', grain='z')
    cyl('Crank_Handle', (xc + .08, 0., AXLE_Z - .2), .022, .17, t, axis='x', verts=10, group='Wood', grain='x')
    # rope wound on the drum, the free end down into the water
    turns, span = 19, .44
    pts = [((-span / 2 + span * i / (turns * 16)), (DRUM_R + .011) * math.sin(i / 16 * math.tau), AXLE_Z + (DRUM_R + .011) * math.cos(i / 16 * math.tau))
           for i in range(turns * 16 + 1)]
    rope('Drum_Rope', pts, .011, P['hemp'], ply=3, tw=150., curve=2, group='Detail_Small')
    x_end = span / 2
    drop = [(x_end, -(DRUM_R + .011), AXLE_Z), (x_end, -(DRUM_R + .012), AXLE_Z - .3), (x_end - .01, -(DRUM_R + .01), .75), (x_end - .02, -.07, WATER_Z + .04)]
    rope('Drop_Rope', drop, .011, P['hemp'], ply=3, tw=150., curve=6, group='Detail_Small')
    # the end hook knot just above the water (the second bucket is down in the well, not modelled)
    torus('Rope_Knot', (x_end - .02, -.07, WATER_Z + .05), .02, .01, P['hemp'], major=10, minor=6, detail=1, group='Detail_Small')


def bucket(P, R):
    bx, by = BUCKET; bz = PAD_TOP + .004
    Hb, R0, R1 = .3, .14, .17; n = 18
    for i in range(n):
        a = i / n * math.tau; a1 = (i + 1) / n * math.tau
        mid = (a + a1) / 2; w0 = R0 * math.tau / n * .485; w1 = R1 * math.tau / n * .485
        verts = []
        top = Hb + (.012 if i in (0, n // 2) else 0.)                          # the two lug staves stand proud for the bail
        for z, r, w in ((0, R0, w0), (Hb * .5, (R0 + R1) / 2 + .003, (w0 + w1) / 2), (top, R1, w1)):
            for rr, ww in ((r, w), (r - .016, w * .9)):
                cx, cy = math.cos(mid) * rr, math.sin(mid) * rr
                tx, ty = -math.sin(mid), math.cos(mid)
                for s in (-1, 1):
                    verts.append((bx + cx + tx * s * ww, by + cy + ty * s * ww, bz + z))
        faces = []
        for row in range(2):
            b = row * 4; t = b + 4
            faces += [(b + 0, b + 1, t + 1, t + 0), (b + 1, b + 3, t + 3, t + 1), (b + 3, b + 2, t + 2, t + 3), (b + 2, b + 0, t + 0, t + 2)]
        faces += [(8, 9, 11, 10), (0, 2, 3, 1)]
        o = mesh('Bucket_Stave', verts, faces, P['stave'], smooth=False, group='Main', grain='z')
        m = o.modifiers.new('Soft', 'BEVEL'); m.width = .0018; m.segments = 2; m.limit_method = 'ANGLE'
    lathe('Bucket_Floor', [(0, .01), (R0 - .01, .01), (R0 - .01, .026), (0, .026)], (bx, by, bz), P['stave'], seg=24, group='Main')
    lathe('Bucket_Water', [(0, Hb - .07), (R1 - .022, Hb - .07), (R1 - .022, Hb - .08), (0, Hb - .08)], (bx, by, bz), P['water'], seg=24, group='Main')
    for z, r in ((.05, R0 + (R1 - R0) * .17), (Hb - .04, R0 + (R1 - R0) * .87)):
        pts = [(bx + math.cos(k / 36 * math.tau) * (r + .004), by + math.sin(k / 36 * math.tau) * (r + .004), bz + z) for k in range(37)]
        rope('Bucket_Hoop', pts, .0065, P['hemp'], tw=60., curve=2, group='Main')
    # the bail: a rope handle tied through the two lug staves, hanging down over the side
    a0 = math.pi * .0; hz = bz + Hb + .006
    pts = [(bx + R1 * math.cos(a0), by + R1 * math.sin(a0), hz)]
    for q in range(1, 8):
        u = q / 8; ang = a0 + math.pi * u
        pts.append((bx + (R1 + .01) * math.cos(ang) * (1 - .15 * math.sin(math.pi * u)), by + (R1 + .01) * math.sin(ang), hz + .16 * math.sin(math.pi * u) * .4 - .02 * math.sin(math.pi * u)))
    pts.append((bx - R1, by, hz))
    rope('Bucket_Bail', pts, .007, P['hemp'], tw=80., curve=4, group='Detail_Small')


# ------------------------------------------------------------------ the pavilion
def frame(P, R):
    t = P['timber']
    plate_top = {sy: under_w(0., sy * PY) - .003 for sy in (-1, 1)}
    post_top = min(plate_top.values()) - .17
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * PX, sy * PY
            rbox(f'Plinth_{sx}_{sy}', (x, y, PLINTH_H / 2), (PLINTH, PLINTH, PLINTH_H), P['plinth'], r=.02, amp=.005, freq=4., hew=3, chips=2,
                 seed=10 + sx + 3 * sy, div=.05, flat='z', group='Stone', taper=(.88, .88))
            rbox(f'Post_{sx}_{sy}', (x, y, (PLINTH_H + post_top) / 2), (POST, POST, post_top - PLINTH_H), t, r=.012, amp=.003, freq=2., hew=4,
                 seed=20 + sx + 3 * sy, div=.06, group='Wood', grain='z')
            # rope lashing round the post where the knee braces meet it
            lash(f'Post_Lash_{sx}_{sy}', (x, y, post_top - .7), (0, 0, 1), POST * .62, .1, .011, P['hemp'], turns=4, group='Detail_Small')
            lash(f'Post_Lash_{sx}_{sy}', (x, y, post_top - .43), (0, 0, 1), POST * .62, .08, .011, P['hemp'], turns=3, group='Detail_Small')
            # knee braces: one to the long beam, one to the gable tie beam
            # long side: up under the lower beam (clear of a walker's head); gable side: up under the tie beam on the post tops
            for dx, dy, bz0, bz1, reach in ((-sx, 0, post_top - .72, post_top - .34, .42), (0, -sy, post_top - .45, post_top - .05, .4)):
                a = Vector((x + dx * .08, y + dy * .08, bz0)); b = Vector((x + dx * reach, y + dy * reach, bz1))
                RF.sweep_box(f'Knee_Brace_{sx}_{sy}', [tuple(a), tuple(b)], .08, .09, t, up=(dy, -dx, 0) if dx or dy else None, group='Wood', grain='y' if dy else 'x')
    # long sides: the plate on the post tops (carries the boards) and a lower beam with three struts between
    for sy in (-1, 1):
        y = sy * PY; zt = plate_top[sy]
        RF.sweep_box(f'Plate_{sy}', [(x, y, zt - .085) for x in (-PX - .3, 0., PX + .3)], .15, .17, t, up=(0, 0, 1), group='Wood', grain='x')
        RF.sweep_box(f'Lower_Beam_{sy}', [(x, y, post_top - .19) for x in (-PX - .14, PX + .14)], .12, .15, t, up=(0, 0, 1), group='Wood', grain='x')
        for k, x in enumerate((-PX * .55, 0., PX * .55)):
            box(f'Strut_{sy}_{k}', (x, y, (post_top - .19 + zt - .17) / 2), (.1, .1, (zt - .17) - (post_top - .19)), t, bevel=.006, group='Wood', grain='z')
    # gables: a tie beam across on the post tops, a king post to the ridge purlin, two raking struts
    zr = under_w(0., 0.) - .003
    RF.sweep_box('Ridge_Purlin', [(x, 0., zr - .07) for x in (-PX - .32, 0., PX + .32)], .14, .14, t, up=(0, 0, 1), group='Wood', grain='x')
    for sx in (-1, 1):
        x = sx * PX; zt = post_top + .02
        RF.sweep_box(f'Tie_Beam_{sx}', [(x, y, zt + .07) for y in (-PY - .16, PY + .16)], .13, .14, t, up=(0, 0, 1), group='Wood', grain='y')
        box(f'King_Post_{sx}', (x, 0., (zt + .14 + zr - .14) / 2), (.11, .11, (zr - .14) - (zt + .14)), t, bevel=.006, group='Wood', grain='z')
        for sy in (-1, 1):
            a = (x, sy * (PY - .2), zt + .14); b = (x, sy * .07, zr - .2)
            RF.sweep_box(f'Gable_Strut_{sx}_{sy}', [a, b], .08, .09, t, up=(1, 0, 0), group='Wood', grain='y')
    S['frame'] = dict(post_top=round(post_top, 3), plate_top={k: round(v, 3) for k, v in plate_top.items()}, ridge_purlin_top=round(zr, 3))


def roof(P, R):
    def cell(kind, side, x, k, r):           # a kept roof: mostly the darker firing (closer to the sheet's slate grey), moss low at the ends
        if k < 3 and abs(x) > 1.8 and r < .35: return 2 + (4 if kind == 'roll' else 0)
        return (0 if r < .3 else 1) + (4 if kind == 'roll' else 0)
    with xf(T(0., YC, 0.) @ Matrix.Scale(SC, 4)):
        for side in (-1, 1):
            RF.tiles(P, side, cell=cell)
            VR.underlay(P, side)
            VR.eave_caps(P, side)
        VR.ridge(P); VR.barge_boards(P); VR.eave_rafters(P, spacing=.5, reach=.95)


def growth(P, R):
    Rg = random.Random('WE01_growth')
    for _ in range(85):                               # grass along the pad's earth rim and in a few outer joints
        a = Rg.uniform(0, math.tau); r = _wobble(a) + Rg.uniform(-.06, .05)
        x, y = r * math.cos(a), r * math.sin(a)
        if abs(y + 1.4) < .5 and abs(x) < .7: continue                  # the trodden way in at the front stays bare
        FP.grass_tuft('Pad_Grass', (x, y, PAD_TOP - .01 if r < PAD_R - .05 else .01), Rg.randint(6, 12), Rg.uniform(.1, .24),
                      P['grass'] if Rg.random() < .75 else P['dry'], Rg, lean=.35, detail=1, spread=.04)
    for sx in (-1, 1):
        for sy in (-1, 1):
            for j in range(2):
                a = Rg.uniform(0, math.tau)
                FP.grass_tuft('Plinth_Grass', (sx * PX + .24 * math.cos(a), sy * PY + .24 * math.sin(a), PAD_TOP - .005), Rg.randint(5, 9), Rg.uniform(.08, .16),
                              P['grass'], Rg, lean=.3, detail=1, spread=.03)
            FP.moss_patch('Plinth_Moss', (sx * PX, sy * PY - sy * (PLINTH / 2 + .005), .08), (0, -sy, .2), Rg.uniform(.06, .1), P['moss'], seed=500 + sx + 3 * sy,
                          flat=.7, snap_each=True)


def build_we01(P):
    R = random.Random('WE01')
    VR.configure(**ROOF)
    pad(P, R); well(P, R); windlass(P, R); bucket(P, R); frame(P, R); roof(P, R); growth(P, R)
    socket('Socket_DrawWater', (0., -RING_R - .32, PAD_TOP), rot=(0, 0, 0))
    S['collision_mesh'] = collision()
    ye = YC - ROOF['depth_front'] * SC
    S['part_notes'] = {'pad_m': {'radius': PAD_R, 'top_z': PAD_TOP, 'flagstones': 'Voronoi cells, wet (darker) in front of the ring and round the bucket'},
                       'posts_m': {'grid_x': 2 * PX, 'grid_y': 2 * PY, 'section': POST, 'plinth': [PLINTH, PLINTH, PLINTH_H], **S['frame']},
                       'front_clear_m': round(2 * PX - PLINTH, 3),
                       'well_ring_m': {'outer_r': RING_R, 'inner_r': RING_IN, 'rim_z': RING_TOP, 'water_z': WATER_Z},
                       'windlass_m': {'uprights_x': WIND_X, 'axle_z': AXLE_Z, 'drum_r': DRUM_R, 'crank': '+x'},
                       'bucket_m': {'at': BUCKET, 'height': .3, 'radius_top': .17},
                       'roof': {'scale': SC, 'eave_y_m': round(ye, 3), 'eave_underside_front_m': round(under_w(0., ye + .02), 3),
                                'note': 'VL tiles at 0.65 scale (vl_roof keeps 12 courses a slope), hanging gable, ridge along x'},
                       'Socket_WellWater': 'water surface centre', 'Socket_DrawWater': 'where a character stands to draw water (in front of the ring, facing +y)'}


def collision():
    V, F = [], []
    def prism(x0, x1, y0, y1, z0, z1):
        FP.hull_loft(V, F, [[(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)] for z in (z0, z1)])
    def octa(cx, cy, r, z0, z1, n=12):
        FP.hull_loft(V, F, [[(cx + r * math.cos(math.tau * k / n), cy + r * math.sin(math.tau * k / n), z) for k in range(n)] for z in (z0, z1)])
    prism(-PAD_R, PAD_R, -PAD_R * .7, PAD_R * .7, 0., PAD_TOP)               # the pad, walked on (5 cm up)
    prism(-PAD_R * .7, PAD_R * .7, -PAD_R, PAD_R, 0., PAD_TOP)
    for sx in (-1, 1):
        for sy in (-1, 1):
            h = PLINTH / 2
            prism(sx * PX - h, sx * PX + h, sy * PY - h, sy * PY + h, 0., S['frame']['post_top'])
    octa(0., 0., RING_R + .04, 0., RING_TOP)                                    # the ring (walkers stop at it)
    for sx in (-1, 1):
        prism(sx * WIND_X - .1, sx * WIND_X + .1, -.09, .09, 0., AXLE_Z + .14)
    octa(BUCKET[0], BUCKET[1], .18, 0., .45, n=8)                            # taller than the 0.3 m step: nobody walks over the bucket
    return V, F


def register(ASSETS):
    ASSETS['WE01_VillageWell'] = dict(
        kind='well', zh='村中水井與井亭', palette=palette, build=build_we01, tex=2048, ver='v001',
        atlases={'Main': ['Main', 'Detail_Small'], 'Stone': ['Stone'], 'Wood': ['Wood']},
        limit=[W, D, H], box=((-W / 2, -D / 2, 0.), (W / 2, D / 2, H)), slot='A1_VillageCentre_Well', ref='WE01/WE01-cand-4', clamp_max=.03, uv_detach_zero=True,
        origin='centre of the pad, bottom z = 0, front (an open long side) -Y',
        note='村心天天有人用的水井（三視圖 WE01-cand-4）：石砌圓井圈加一圈壓頂石，井裡有水；井旁兩根立柱架木轆轤，軸上纏繩、右邊一支搖把，繩子垂進井裡；'
             '井邊石板上一只木桶。四根方木柱立在石柱礎上，撐一個懸山黛瓦小亭頂（VL 瓦片縮 0.65 倍，屋脊沿 x、兩端捲起），長邊有額枋和下枋、三根短柱，'
             '兩端山面是露明的抬梁（橫梁、脊瓜柱、兩根斜撐），柱和梁之間有斜撐、用麻繩綁。地上是一圈不規則石板，井前和木桶旁的石板被水弄濕變深，石縫和邊上長草。'
             '人從前面兩根柱子之間走進亭內（淨寬 2.18 m），站在井圈前打水，後面同樣開著。不寫字、沒有人。',
        method='procedural mesh construction (art/source/village-yards-b/we_well.py, vh_roof.py at 0.65 scale); procedural shaders baked to three 2048 atlases '
               '(Main, Stone, Wood); roof tiles on the shared 1024 VL tile texture (VL_Shared, read only)',
        based_on='original (Blender procedural); VL material set and roof tiles from art/source/village-houses-b')


def well_checks(aid, check, cfg):
    from vl_checks import _bvh
    body = _bvh([o for g, o in S['lods'][0].items()])
    col = _bvh([S['collision_obj']]) if S.get('collision_obj') else None
    down = lambda x, y, z=6.: (lambda h: round(h[0].z, 3) if h else None)(body((x, y, z), (0, 0, -1)))
    # open water in the ring: from under the roof straight down the shaft (between drum and rope) to the water
    w = [down(dx, dy, 1.05) for dx, dy in ((-.2, .15), (.2, .2), (-.15, -.2))]
    check('well_has_water_inside', all(v is not None and abs(v - WATER_Z) < .02 for v in w), {'hits_z_m': w, 'water_z_m': WATER_Z})
    rim = [down(RING_R - .07, 0., 1.05), down(0., RING_R - .07, 1.05)]
    check('ring_rim_height', all(v is not None and abs(v - RING_TOP) < .04 for v in rim), {'rim_hits_z_m': rim, 'rim_z_m': RING_TOP})
    # hanging-gable roof, ridge along x: high over the ridge, lower front and back, level along the ridge
    ridge = [down(x, 0.) for x in (-1., 0., 1.)]; front, back = down(0., -1.3), down(0., 1.3)
    check('roof_ridge_along_x', all(ridge) and front and back and min(ridge) > front + .4 and min(ridge) > back + .4 and max(ridge) - min(ridge) < .1 and max(ridge) <= H,
          {'ridge_top_m': ridge, 'front_slope_m': front, 'back_slope_m': back})
    # headroom under the front eave and the front beam
    up = lambda x, y, z: (lambda h: round(h[0].z, 3) if h else None)(body((x, y, z), (0, 0, 1)))
    hr = [up(0., -1.25, 1.0), up(0., -PY, 1.0), up(.8, -PY, 1.0)]
    check('headroom_front', all(v is not None and v > 1.95 for v in hr), {'first_hit_above_m': hr, 'note': 'from 1.0 m up: eave, lower beam'})
    out = {'water_hits_z_m': w, 'ridge_m': ridge, 'headroom_m': hr}
    if col:
        # walk in at the front: level rays along +y at shin, waist and head height across a 0.6 m wide body meet the ring, not a post
        hits = {}
        for x in (-.3, 0., .3):
            for z in (.15, .9, 1.7):
                h = col((x, -3., z), (0, 1, 0)); hits[f'{x},{z}'] = round(h[0].y, 3) if h else None
        ring_y = -(RING_R + .04)
        ok = all((v is None or v > ring_y - .05) for k, v in hits.items())
        check('walk_in_to_the_ring', ok, {'first_collision_y_m': hits, 'ring_front_y_m': round(ring_y, 3),
                                           'note': 'rays from y -3 m; z 1.7 passes over the ring (None or past it)'})
        lat = [col((-2.5, -PY + .02, z), (1, 0, 0)) for z in (.4, 1.2)]
        out['collision_front_posts_x_m'] = [round(h[0].x, 3) if h else None for h in lat]
    return out
