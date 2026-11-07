"""RI03_GreatWheel  great irrigation water wheel for the rice fields, 9 m across (AI three-view RI03/GREAT-WHEEL candidate-04).

Three separate export parts, so the game can turn the wheel and leave the rest standing:
  Wheel         axle, hubs, 2 x 16 spokes, a double outer rim and an inner ring on each side, 32 paddles, 32 bamboo lifting tubes.
                It turns about the axle (Blender X); its pivot is the origin.
  Seat          two tapered rubble-stone pillars carrying the axle in timber bearing blocks, on footing slabs.
  Trough        a timber trough beside the wheel at the top (the -X side) on a frame of four posts and a crossbeam, with a wide catch head
                where the tubes empty, running out past the +Y frame post towards the fields.
  Detail_Wheel  rope lashings that turn with the wheel (spoke-rim joints, tube ties).
  Detail_Small  static lashings, moss, water in the trough.

How it works (and how it differs from the reference): the tubes are tied on the outside of the -X rim, leaning 12 degrees out, mouth leading.
They fill as they dip through the channel and, just past the top, tip their water sideways into the catch head beside the wheel.
The reference shows the trough over the wheel; a trough there would be struck by the tubes, so it sits beside the wheel instead.
Unlike creek-repair-b WM02 (a 4.6 m undershot mill wheel with iron straps that drives a mill) this one is twice the size, has no iron,
and lifts water with bamboo tubes.

Blender Z-up, 1 unit = 1 m, the wheel turns about X, front -Y faces the wheel's edge... origin at the axle centre, ground (bank) at z = -4.0.
"""
import math, random
from mathutils import Vector, Matrix, noise
from ti_core import S, cyl, lathe, mesh, surface, tube, socket
import mk_mats as mm
import cr_mats as cm
import ti_mats as tm
from cr_parts import rbox, between, pole, tuft
from te_pavilion import box_sweep

R_OUT = 4.5                 # outermost reach (the tube walls)
R_TUBE_C, R_TUBE = 4.42, .065    # the tube ends reach sqrt(4.42^2 + 0.39^2) + 0.065 = 4.50 m
R_RIM1, R_RIM2, R_RING = 4.05, 3.72, 2.0
X_SIDE = .4                 # spoke / rim planes at x = +-X_SIDE
N_SPOKE, N_PADDLE = 16, 32
GROUND = -4.0
X_TR = -.95                 # trough and frame line
TUBE_TILT = math.radians(12)
X_TUBE = -.60               # closed end of each tube: just outside the -X rim (outer face x = -0.53)
X_PADDLE = (-.62, .45)      # paddles run out past the -X rim to carry the tubes


def palette():
    P = {}
    P['oak'] = cm.wood('Wheel_Oak', (.042, .028, .017), (.21, .135, .075), ground_h=0, grey=.3, moss=True, moss_amt=.35)
    P['spoke'] = cm.wood('Spoke_Oak', (.05, .032, .019), (.24, .155, .085), ground_h=0, grey=.26)
    P['paddle'] = cm.wood('Paddle_Wet', (.032, .026, .017), (.13, .1, .06), ground_h=0, grey=.12, moss=True, moss_amt=.3)   # wet every turn: dark brown, a little green film (v1 read all green)
    P['axle'] = cm.wood('Axle_Oak', (.05, .03, .016), (.17, .1, .052), ground_h=0, polish=.25, grey=.1)
    P['tube'] = cm.culm('Lift_Tube', green=(.06, .066, .03), straw=(.2, .165, .085), mud_h=0.)   # old wet bamboo, grey-brown (v1 read bright yellow in URP)
    P['hemp'] = mm.hemp('Wheel_Rope', (.13, .09, .048), twist=40.0)
    P['stone'] = cm.stone('Seat_Stone', light=(.38, .36, .31), dark=(.18, .17, .145), moss=1.0, crack=.6, lichen=.5, wet_z=-3.4)
    P['footing'] = cm.stone('Footing_Stone', light=(.34, .32, .28), dark=(.16, .15, .13), moss=1.1, crack=.5, lichen=.4, wet_z=-3.6)
    P['frame'] = cm.wood('Frame_Timber', (.055, .035, .02), (.25, .16, .088), ground_h=.6, grey=.3)
    P['trough'] = cm.wood('Trough_Board', (.05, .036, .022), (.2, .13, .072), wet_z=3.92, ground_h=0, grey=.3, moss=True, moss_amt=.5)
    P['water'] = tm.plain('Trough_Water', (.025, .05, .052), rough=.08, noise=.15, scale=6.0)   # shallow water over dark wet wood, not pool blue
    P['moss'] = cm.moss_tuft('Seat_Moss', soft=True)
    return P


def polar(x, a, r):
    """a = 0 at the top, increasing towards -Y (the same convention as creek-repair-b WM02)."""
    return Vector((x, -math.sin(a) * r, math.cos(a) * r))


def wheel(P, R):
    G = dict(group='Wheel')
    GD = dict(group='Detail_Wheel', detail=1)
    cyl('Axle', (0, 0, 0), .16, 2.06, P['axle'], axis='x', verts=32, bevel=.008, grain='x', **G)
    for sx in (-1, 1):
        cyl('Axle_End', (sx * 1.04, 0, 0), .2, .05, P['axle'], axis='x', verts=32, bevel=.01, grain='z', **G)
    cyl('Hub_Drum', (0, 0, 0), .42, .62, P['oak'], axis='x', verts=32, bevel=.02, grain='z', **G)
    for sx in (-1, 1):
        x = sx * X_SIDE
        cyl('Hub', (x, 0, 0), .62, .2, P['oak'], axis='x', verts=40, bevel=.02, grain='z', **G)
        # pegs round the hub face
        for i in range(8):
            a = i / 8 * math.tau + math.pi / 16
            cyl('Hub_Peg', tuple(polar(x + sx * .105, a, .5)), .028, .03, P['axle'], axis='x', verts=12, bevel=0., detail=1, grain='x', group='Wheel')
        # spokes from the hub to the outer rim
        for i in range(N_SPOKE):
            a = i / N_SPOKE * math.tau
            a0, a1 = polar(x, a, .5), polar(x, a, R_RIM1 + .02)
            between('Spoke', tuple(a0), tuple(a1), .13, .12, P['spoke'], r=.012, amp=.003, chips=2, seed=i + int(sx * 20), div=.3, **G)
        # rims: an outer felloe ring, a second ring just inside it (the double rim), and an inner ring at half radius; 24 / 24 / 12 lengths
        for name, rc, w, h, nseg, mat in (('Rim_Outer', R_RIM1, .16, .26, 24, P['oak']), ('Rim_Second', R_RIM2, .13, .19, 24, P['oak']), ('Ring_Inner', R_RING, .11, .15, 12, P['spoke'])):
            off = R.uniform(0, math.tau / nseg)
            for k in range(nseg):
                a0 = off + k / nseg * math.tau; a1 = off + (k + 1) / nseg * math.tau     # lengths butt end to end (a gap left the ones between spokes floating)
                pts = [polar(x, a0 + (a1 - a0) * j / 5, rc) for j in range(6)]
                box_sweep(name, pts, w, h, mat, up_hint=Vector((1, 0, 0)), **G)
        # rope lashings where each spoke crosses the double rim and the inner ring
        for i in range(N_SPOKE):
            a = i / N_SPOKE * math.tau
            for rc, span in ((R_RIM2, .16), (R_RING, .14)):
                wrap_x(P, polar(x, a, rc), a, span, .095, .115, **GD)
    # paddles across the outer rims, and the lifting tubes tied on the outside of the -X rim
    for i in range(N_PADDLE):
        a = (i + .5) / N_PADDLE * math.tau
        c = polar(sum(X_PADDLE) / 2, a, R_RIM1 + .13)
        rbox('Paddle', tuple(c), (X_PADDLE[1] - X_PADDLE[0], .05, .36), P['paddle'], r=.008, amp=.003, freq=8., seed=i, div=.15, rot=(a, 0, 0), grain='x', **G)
        tube_at(P, R, a, i)
    S['part_notes'] = {'Wheel': 'turns about the axle (Blender X, Unity X); pivot at the origin; about 1 turn per 40-60 s for a slow current (not verified in game)',
                       'Detail_Wheel': 'rope lashings on the wheel: parent to / turn with Wheel',
                       'Seat': 'static: two stone pillars and bearing blocks', 'Trough': 'static: trough, catch head and its frame',
                       'Detail_Small': 'static lashings, moss and the water in the trough'}


def wrap_x(P, c, a, span, rx, rz, **kw):
    """A rope binding round a rim member at c (tangent along the rim), 3 turns."""
    t = Vector((0, -math.cos(a), -math.sin(a))); n = Vector((0, -math.sin(a), math.cos(a))); X = Vector((1, 0, 0))
    m = 24; pts = []
    for i in range(m + 1):
        s = i / m; ang = s * 3 * math.tau
        pts.append(tuple(c + t * (span * (s - .5)) + X * (rx * math.cos(ang)) + n * (rz * math.sin(ang))))
    tube('Rim_Lash', pts, .011, P['hemp'], res=2, grain=tuple(t), **kw)


def tube_at(P, R, a, i):
    """One bamboo lifting tube: closed node end tied to the paddle end, open mouth leading and leaning out to -X."""
    t = Vector((0, -math.cos(a), -math.sin(a)))       # direction of travel at the top of a turn (mouth leads)
    tilt = TUBE_TILT - math.radians(R.uniform(0., 2.5))   # hand-tied: no two lean quite the same; never more than 12 deg, or the tube mouth sweeps into the side trough
    d = (t * math.cos(tilt) - Vector((1, 0, 0)) * math.sin(tilt)).normalized()
    L = .8 - R.uniform(0, .05)   # 32 tubes on a 4.42 m radius are 0.87 m apart along the rim: 0.8 m tubes leave a hand's gap
    # centred on its paddle end, lying on the paddle's outer edge: the closed end at x = X_TUBE, the mouth leaning out to -X over the catch head
    mid = polar(X_TUBE - L * .5 * math.sin(tilt), a, R_TUBE_C)
    a_end, b_end = mid - d * (L * .5), mid + d * (L * .5)
    pole('Lift_Tube', tuple(a_end), tuple(b_end), R_TUBE, R_TUBE * .96, P['tube'], node_gap=.42, seed=i, seg=10, group='Wheel')
    # tie: rope round the tube and the paddle end
    n = Vector((0, -math.sin(a), math.cos(a)))
    c = polar(X_TUBE + .02, a, R_TUBE_C) - n * .02
    pts = []
    for k in range(19):
        s = k / 18; ang = s * 3 * math.tau
        side = d.cross(n).normalized()
        pts.append(tuple(c + d * (.06 * (s - .5)) + side * (.09 * math.cos(ang)) + n * (.075 * math.sin(ang) - .03)))
    tube('Tube_Tie', pts, .009, P['hemp'], res=2, grain=tuple(d), group='Detail_Wheel', detail=1)


# ------------------------------------------------------------------ seat: stone pillars
def seat(P, R):
    G = dict(group='Seat')
    for sx in (-1, 1):
        x0, x1 = sx * .6, sx * 1.0
        xc = (x0 + x1) / 2; th = abs(x1 - x0)
        rbox('Footing_Slab', (xc + sx * .04, 0, GROUND + .1), (th + .04, 1.75, .2), P['footing'], r=.03, amp=.01, chips=3, hew=2, seed=int(sx * 3), div=.2, grain='x', **G)
        z = GROUND + .2; top = -.36; nc = 9; hc = (top - z) / nc
        for c in range(nc):
            f = (c + .5) / nc; half = .72 + (.38 - .72) * f                # tapering in y
            split = R.uniform(-.25, .25) * half
            for y0, y1 in ((-half, split), (split, half)):
                hh = hc + .006
                rbox('Pillar_Stone', (xc, (y0 + y1) / 2, z + hc / 2), (th - .01 + R.uniform(0, .03), y1 - y0 + .006, hh), P['stone'], r=.035, amp=.008, chips=2, hew=2,
                     seed=c * 7 + int(y0 * 10) + int(sx * 50), div=.16, grain='x', **G)
            z += hc
        # timber bearing block with a half-round cradle for the axle
        rbox('Bearing_Block', (xc, 0, -.27), (th + .04, .62, .18), P['frame'], r=.015, div=.15, chips=1, seed=int(sx * 9), grain='y', **G)
        lathe('Bearing_Cap', [(0., -.01), (.19, -.01), (.2, .02), (.19, .05), (0., .05)], (0, 0, 0), P['frame'], seg=18, grain='z', **G).matrix_world = \
            Matrix.Translation((xc, 0, -.18)) @ Matrix.Scale(1., 4)
        # moss at the pillar foot and on the shaded course ledges
        for k in range(4):
            r = R.uniform(.06, .1)
            tuft('Seat_Moss', (xc + R.uniform(-.15, .15), R.choice((-1, 1)) * R.uniform(.5, .75), GROUND + .2 + r * .3), r, P['moss'], seed=k + int(sx * 7), group='Detail_Small')


# ------------------------------------------------------------------ trough and frame
def trough(P, R):
    G = dict(group='Trough')
    zb = lambda y: 3.78 - .015 * (y + .45)          # trough floor, falling 1.5 cm per metre towards the field (+Y)
    # catch head beside the top of the wheel: wide, open towards +Y into the narrow trough
    hx0, hx1, hy0, hy1 = -1.06, -.66, -.45, 1.45
    tx0, tx1, ty1 = -1.06, -.86, 5.4       # the narrow run on towards the field
    def floor_board(name, x0, x1, y0, y1):
        between(name, ((x0 + x1) / 2, y0, zb(y0) - .02), ((x0 + x1) / 2, y1, zb(y1) - .02), x1 - x0, .04, P['trough'], r=.006, div=.3, seed=int(y0 * 10), **G)
    floor_board('Trough_Floor', hx0, hx1, hy0, hy1)
    for x in (hx0 + .02, hx1 - .02):
        between('Trough_Side', (x, hy0, zb(hy0) + .1), (x, hy1, zb(hy1) + .1), .04, .2, P['trough'], r=.006, div=.3, seed=int(x * 10), **G)
    between('Trough_End', (hx0, hy0 + .02, zb(hy0) + .1), (hx1, hy0 + .02, zb(hy0) + .1), .04, .2, P['trough'], r=.006, div=.2, seed=3, grain='x', **G)
    between('Trough_Step', (tx1, hy1 - .02, zb(hy1) + .1), (hx1, hy1 - .02, zb(hy1) + .1), .04, .2, P['trough'], r=.006, div=.2, seed=4, grain='x', **G)
    # the narrow run: from the head to past the +Y frame post
    floor_board('Trough_Floor', tx0, tx1, hy1 - .02, ty1)
    for x in (tx0 + .02, tx1 - .02):
        between('Trough_Side', (x, hy1 - .02, zb(hy1) + .1), (x, ty1, zb(ty1) + .1), .04, .2, P['trough'], r=.006, div=.3, seed=int(x * 10) + 5, **G)
    # cross ties over the trough every metre, holding the sides
    for y in (0., 2.4, 3.6, 4.8):
        x0, x1 = (hx0, hx1) if y < hy1 else (tx0, tx1)
        between('Trough_Tie', (x0 + .005, y, zb(y) + .215), (x1 - .005, y, zb(y) + .215), .04, .04, P['frame'], r=.006, div=.2, seed=int(y * 3), grain='x', detail=1, group='Detail_Small')
    # water: a sheet inside, 9 cm deep, darker towards the outlet
    def water(u, v, x0, x1, y0, y1):
        y = y0 + (y1 - y0) * v; return (x0 + (x1 - x0) * u, y, zb(y) + .09)
    surface('Trough_Water', 2, 6, lambda u, v: water(u, v, hx0 + .045, hx1 - .045, hy0 + .045, hy1 - .045), P['water'], grain='y', group='Detail_Small', detail=1)
    surface('Trough_Water', 2, 12, lambda u, v: water(u, v, tx0 + .045, tx1 - .045, hy1 - .045, ty1), P['water'], grain='y', group='Detail_Small', detail=1)
    # frame: four posts on footing stones, a crossbeam under the trough, braces
    xb = (tx0 + tx1) / 2 + .005
    zc = zb(5.4) - .04 - .09    # crossbeam centre: its top touches the trough floor at the outlet end
    for y in (-4.85, -2.7, 2.7, 4.85):     # the inner posts stand at 2.7 m: nearer the axle the tubes sweep past their footings
        rbox('Post_Footing', (xb, y, GROUND + .09), (.22, .36, .18), P['footing'], r=.03, amp=.008, chips=2, seed=int(y * 10), div=.15, grain='x', group='Seat')
        between('Frame_Post', (xb, y, GROUND + .18), (xb, y, zc - .09), .18, .18, P['frame'], r=.014, amp=.003, chips=2, seed=int(y * 7), div=.4, **G)
    between('Crossbeam', (xb, -5.0, zc), (xb, 5.0, zc), .18, .18, P['frame'], r=.014, amp=.003, chips=2, seed=11, div=.4, **G)
    for y0, s in ((-4.85, 1), (4.85, -1), (-2.7, 1), (2.7, -1)):
        between('Brace', (xb, y0, zc - 1.0), (xb, y0 + s * .9, zc - .09), .13, .13, P['frame'], r=.012, div=.3, seed=int(y0 * 5), **G)
    for y in (-4.85, -2.7):   # through-tenons on the two posts with no trough above them: the post end shows on top of the crossbeam, split by a wedge
        rbox('Post_Tenon', (xb, y, zc + .09 + .025 - .004), (.1, .12, .05), P['frame'], r=.008, div=.1, seed=int(y * 3) + 40, grain='z', **G)
        rbox('Tenon_Wedge', (xb, y, zc + .09 + .05 - .004 + .007 - .003), (.022, .1, .014), P['axle'], r=.003, div=.1, seed=int(y * 3) + 41, grain='y', **G)
    # a low tie beam between the posts near the ground
    between('Ground_Tie', (xb, -4.85, GROUND + .7), (xb, 4.85, GROUND + .7), .15, .15, P['frame'], r=.012, amp=.003, div=.4, seed=21, **G)
    for y in (-4.85, -2.7, 2.7, 4.85):
        for z in (zc, GROUND + .7):
            c = Vector((xb, y, z)); pts = []
            for k in range(25):
                s = k / 24; ang = s * 4 * math.tau
                pts.append(tuple(c + Vector((1, 0, 0)) * (.1 * math.cos(ang)) + Vector((0, 1, 1)).normalized() * (.13 * math.sin(ang)) + Vector((0, .06 * (s - .5), 0))))
            tube('Frame_Lash', pts, .011, P['hemp'], res=2, grain='y', group='Detail_Small', detail=1)
    S['trough_out'] = (xb, ty1, zb(ty1) + .09)


def ri03_great_wheel(P):
    R = random.Random(903)
    wheel(P, R)
    seat(P, R)
    trough(P, R)
    # collision: the wheel as a 24-sided drum about the axle, the pillars, the frame posts and the trough
    verts, faces = [], []
    ring = [(sx * .5, math.sin(k / 24 * math.tau) * R_OUT, math.cos(k / 24 * math.tau) * R_OUT) for sx in (-1, 1) for k in range(24)]
    verts += ring; faces += [(k, (k + 1) % 24, 24 + (k + 1) % 24, 24 + k) for k in range(24)] + [tuple(range(23, -1, -1)), tuple(range(24, 48))]
    boxes = [((.58, -.88, GROUND), (1.02, .88, -.18)), ((-1.02, -.88, GROUND), (-.58, .88, -.18)), ((-1.06, -.46, 3.68), (-.66, 1.45, 4.0)), ((-1.06, 1.45, 3.6), (-.86, 5.4, 3.95))]
    for y in (-4.85, -2.7, 2.7, 4.85):
        boxes.append(((-1.07, y - .18, GROUND), (-.85, y + .18, 3.6)))
    for (x0, y0, z0), (x1, y1, z1) in boxes:
        b = len(verts)
        verts += [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        faces += [(b, b + 3, b + 2, b + 1), (b + 4, b + 5, b + 6, b + 7), (b, b + 1, b + 5, b + 4), (b + 1, b + 2, b + 6, b + 5), (b + 2, b + 3, b + 7, b + 6), (b + 3, b, b + 4, b + 7)]
    S['collision_mesh'] = (verts, faces)
    socket('Socket_Axle', (0., 0., 0.), (0, math.pi / 2, 0))
    socket('Socket_Ground', (0., 0., GROUND))
    socket('Socket_Trough_Out', S['trough_out'])
    S['prop'] = dict(kind='wheel', r_out=R_OUT, ground=GROUND)
