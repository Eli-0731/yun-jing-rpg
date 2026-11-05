"""CR09 household diversion gate, two households.

Interface shared with the channels: clear width 0.40 m, floor top z = 0.10, outer walls reach x = +-0.30 and z = 0.40 at
both port faces (y = +-0.25), same as B02/B03. Water runs along Y through the gate. Limit 0.8 x 0.5 x 0.9 m including
the 0.3 m lift: closed top at 0.60, open top at 0.90. Board bottom stays 0.12 m inside the groove when fully open.

A  rope:  rough stones, a crooked branch for a handle, everything lashed; a split plank mended with rope.
B  tenon: tidy dressed stones with a capstone, a squared handle through-tenoned and wedged, battens pegged.
"""
import math
from mathutils import Vector
from ti_core import S, box, cyl, sphere, boolean, socket
import ti_mats as tm
import mk_mats as mm
import cr_mats as cm
from cr_parts import rbox, rope, lash, xlash, log, tuft

CLEAR = .2; FLOOR = .1; TOP = .52; BOARD_HW = .224; BOARD_T = .036; BOARD_TOP = .46; HANDLE_TOP = .6; WET = .28; RACK_X = .09; RACK_Z0 = .11; RACK_Z1 = .55


def palette(variant):
    P = {}
    if variant == 'A':
        P['stone'] = cm.stone('Stone_Rough', light=(.27, .255, .22), dark=(.125, .118, .1), wet_z=WET, moss=1.0, lichen=.6)
    else:
        P['stone'] = cm.stone('Stone_Dressed', light=(.29, .27, .225), dark=(.13, .12, .1), ochre=(.23, .19, .12), wet_z=WET, moss=.95, lichen=.45, crack=.6)
    P['board'] = cm.wood('Gate_Cedar', (.075, .04, .02), (.25, .14, .068), wet_z=WET, ground_h=0, grey=.18)
    P['board_new'] = cm.wood('Gate_Cedar_New', (.13, .07, .03), (.36, .21, .095), wet_z=WET, ground_h=0, grey=.05)
    P['core'] = cm.wood('Gate_Core', (.02, .012, .008), (.04, .025, .015), ground_h=0, grey=0)
    P['handle'] = cm.wood('Handle_Oak', (.06, .032, .016), (.2, .115, .058), ground_h=0, polish=.18, grey=.1)
    P['peg'] = cm.wood('Peg_Pale', (.17, .11, .055), (.36, .25, .13), ground_h=0, grey=0)
    P['hemp'] = mm.hemp('Hemp_Rope', (.19, .115, .05), twist=40.0)
    P['hemp_new'] = mm.hemp('Hemp_Rope_New', (.3, .2, .09), twist=40.0)
    P['moss'] = cm.moss_tuft('Moss_Tuft')
    return P


def frame(P, v):
    st = P['stone']; rough = v == 'A'
    amp, chips, hew, r = (.008, 9, 20, .01) if rough else (.0028, 2, 8, .008)
    seed = 1 if rough else 40
    def S_(name, lo, hi, flat='', **kw):
        c = tuple((a + b) / 2 for a, b in zip(lo, hi)); s = tuple(b - a for a, b in zip(lo, hi))
        nonlocal seed; seed += 1
        return rbox(name, c, s, st, r=r, amp=amp, freq=16., chips=chips, hew=hew, seed=seed, div=.018, flat=flat, **kw)
    # sill: channel floor, flush with B02's top of floor at z 0.10
    ys = (-.25, -.075, .06, .25) if rough else (-.25, -.05, .05, .25)
    for i in range(3):
        S_('Sill', (-CLEAR - .002, ys[i], 0), (CLEAR + .002, ys[i + 1], FLOOR), flat='Zz' + ('y' if i == 0 else 'Y' if i == 2 else ''))
    for sx in (-1, 1):
        inner = 'x' if sx > 0 else 'X'
        def X(a, b): return (a, b) if sx > 0 else (-b, -a)
        x0, x1 = X(CLEAR + .005, .4)
        if rough:
            # one big foot stone per side, split where that side's stone happened to break
            split = .05 if sx > 0 else -.11
            f1 = S_('Foot', (x0, -.25, 0), (x1, split + .004, .172 if sx > 0 else .158), flat='zy' + inner + ('X' if sx > 0 else 'x'))
            f2 = S_('Foot', (x0, split, 0), (x1, .25, .158 if sx > 0 else .178), flat='zY' + inner + ('X' if sx > 0 else 'x'))
            xb0, xb1 = X(CLEAR + .005, .372 if sx > 0 else .385)
            bw = xb1 - xb0
            def batter(q, h): q.x -= sx * .055 * max(0., (q.x * sx + bw / 2) / bw) * max(0., (q.z + h / 2) / h)
            # front buttress steps down to wall height at the port
            def slope_f(q):
                batter(q, .305); q.z += min(0., q.y / .08) * .03 * (q.z + .1525) / .305
            S_('Buttress_F', (xb0, -.25, .125), (xb1, -.085, .43), flat='y' + inner, warp=slope_f)
            # rear buttress leans back as one long wedge, the silhouette from the side
            def slope_b(q):
                batter(q, .36); q.z -= (q.y + .083) / .165 * .085 * (q.z + .18) / .36
            S_('Buttress_B', (xb0, .085, .125), (xb1, .25, .485), flat='Y' + inner, warp=slope_b)
            xo0, xo1 = X(.335, .385 if sx > 0 else .395)
            S_('Buttress_Out', (xo0 - (.012 if sx > 0 else 0), -.095, .125), (xo1 + (.012 if sx < 0 else 0), .095, .36))
        else:
            # dressed courses: three even layers, stepped in at the top
            f1 = S_('Foot', (x0, -.25, 0), (x1, .25, FLOOR + .03), flat='zyY' + inner + ('X' if sx > 0 else 'x'))
            f2 = None
            h1 = .27
            S_('Course2', (x0, -.25, FLOOR + .03), (x1, -.09, h1), flat='y' + inner + ('X' if sx > 0 else 'x'))
            S_('Course2', (x0, .09, FLOOR + .03), (x1, .25, h1), flat='Y' + inner + ('X' if sx > 0 else 'x'))
            xo0, xo1 = X(.335, .4)
            S_('Course2_Out', (xo0, -.09, FLOOR + .03), (xo1, .09, h1), flat='X' if sx > 0 else 'x')
            xm0, xm1 = X(CLEAR + .005, .372)
            S_('Course3', (xm0, -.25, h1), (xm1, -.09, .4), flat='y' + inner)
            S_('Course3', (xm0, .09, h1), (xm1, .25, .4), flat='Y' + inner)
            xo0, xo1 = X(.335, .372)
            S_('Course3_Out', (xo0, -.09, h1), (xo1, .09, .4))
        # post with the gate groove; the groove also runs through whatever foot stone it passes
        xp0, xp1 = X(CLEAR, .335)
        post_top = TOP if rough else TOP - .045
        post = S_('Post', (xp0, -.09, FLOOR), (xp1, .09, post_top), flat=inner)
        gx0, gx1 = X(CLEAR - .02, BOARD_HW + .008)
        c = box('GrooveCut', ((gx0 + gx1) / 2, 0, (FLOOR + TOP + .2) / 2), (gx1 - gx0, BOARD_T + .012, TOP + .2 - FLOOR + .02), st, bevel=0)
        targets = [post, f1, f2]
        if not rough:
            # a dressed capstone over the post, slotted so the board still rises through it
            xc0, xc1 = X(CLEAR, .35)
            targets.append(S_('Capstone', (xc0, -.105, post_top - .004), (xc1, .105, TOP), flat=inner))
        for tgt in targets:
            if tgt is not None: boolean(tgt, c)
    # moss in the joints and the groove (the part the prompt asks for)
    M = P['moss']
    spots = [(.205, -.034, .118), (-.205, .034, .14), (.203, -.034, .22), (-.203, .034, .3), (.3, -.22, .158), (-.3, .22, .158), (.2, .1, .104), (-.2, -.14, .104),
             (.345, .09, .158), (-.36, -.09, .158), (.1, -.22, .098), (-.08, .22, .098)]
    for i, q in enumerate(spots if rough else spots[::2]):
        tuft('Moss', q, .018 + .004 * (i % 3), M, seed=i)


def gate_board(P, v):
    b, bn, g = P['board'], P['board_new'], 'Gate'
    if v == 'A':
        xs = [-BOARD_HW, -.135, -.05, .055, .13, BOARD_HW]         # uneven planks
    else:
        xs = [-BOARD_HW + i * (2 * BOARD_HW) / 6 for i in range(7)]
    z0, z1 = FLOOR + .002, BOARD_TOP
    for i, (a, c) in enumerate(zip(xs, xs[1:])):
        mat = bn if v == 'A' and i == 3 else b
        h = z1 - z0 - (.012 if v == 'A' and i in (0, 2) else 0)
        rbox('Plank', ((a + c) / 2, 0, z0 + h / 2), (c - a - .0025, BOARD_T, h), mat, r=.004, amp=.0018, freq=11., seed=i + (0 if v == 'A' else 20), div=.03, group=g, grain='z')
    rbox('Core', (0, 0, (z0 + z1 - .016) / 2), (2 * BOARD_HW - .006, BOARD_T * .35, z1 - z0 - .016), P['core'], r=.001, div=.08, group=g, detail=1)
    tb = BOARD_T / 2
    if v == 'A':
        # front and rear battens, tied through with rope
        for y, z in ((-tb - .013, .415), (tb + .013, .17), (tb + .013, .405)):
            rbox('Batten', (0, y, z), (2 * BOARD_HW - .004, .024, .05 + (z < .2) * .012), P['board'], r=.006, amp=.003, freq=9., hew=5, seed=int(z * 100), div=.024, rot=(0, .012 * (1 if z < .2 else -1), 0), group=g, grain='x')
        for sx in (-1, 1):
            for z in (.415, .405):
                lash('Batten_Lash', (sx * .186, 0, z), (1, 0, 0), .034, .03, .0036, P['hemp'], turns=4, group=g)
        # the split plank, mended with a tight new wrap
        lash('Mend', (-.09, 0, .27), (0, 0, 1), .027, .042, .0044, P['hemp_new'], turns=6, group=g)
    else:
        for y, z in ((-tb - .011, .42), (tb + .011, .15), (tb + .011, .41)):
            rbox('Batten', (0, y, z), (2 * BOARD_HW - .012, .022, .046), P['board'], r=.004, amp=.0012, seed=int(z * 100), div=.03, group=g, grain='x')
            for k in range(6):
                x = -BOARD_HW + (k + .5) * (2 * BOARD_HW) / 6
                cyl('Peg', (x, y + (-.0115 if y < 0 else .0115), z), .0058, .006, P['peg'], axis='y', verts=10, group=g, detail=1, bevel=.0012)
        # a rack on the board's face for the wheel's pinion (B06, shaft along X, pinion centre at x .09, y -.093)
        rbox('Rack', (RACK_X, -.0315, (RACK_Z0 + RACK_Z1) / 2), (.03, .027, RACK_Z1 - RACK_Z0), P['board'], r=.003, amp=.0008, seed=7, div=.03, group=g, grain='z')
        k = 0; z = RACK_Z0 + .012
        while z < RACK_Z1 - .008:
            rbox('Rack_Tooth', (RACK_X, -.0515, z), (.03, .013, .009), P['peg'], r=.0015, seed=k, div=.02, group=g, detail=1, grain='x'); z += .022; k += 1


def handle(P, v):
    g = 'Gate'
    if v == 'A':
        for sx, lean in ((-1, .008), (1, -.01)):
            x = sx * .15
            log('Upright', [(x, 0, BOARD_TOP - .07), (x + lean * .4, .001, BOARD_TOP + .04), (x + lean, -.002, HANDLE_TOP - .022)], .0185, P['handle'], seg=10, seed=sx + 5, group=g, grain='z')
        hz = HANDLE_TOP - .036
        log('Branch', [(-.215, .004, hz + .003), (-.1, -.004, hz - .004), (.03, .003, hz + .003), (.135, -.003, hz - .002), (.222, .003, hz + .005)], .0165, P['handle'], seg=10, lump=.13, seed=9, group=g, grain='x')
        for sx in (-1, 1):
            xlash('Handle_Lash', (sx * .15, 0, hz), (0, 0, 1), .0185, (1, 0, 0), .0165, .0028, P['hemp'], group=g,
                  tail=(sx * .012, -.012, -.055) if sx > 0 else None)
        lash('Grip', (0, 0, hz), (1, 0, 0), .0165, .09, .0042, P['hemp_new'], turns=11, group=g, detail=0)
        # rope tail hanging from the grip, end frayed
        rope('Grip_Tail', [(.052, -.024, hz - .006), (.058, -.03, hz - .05), (.05, -.026, hz - .1), (.058, -.028, hz - .135)], .0048, P['hemp_new'],
             radius_fn=lambda t: 1 - .3 * t, group=g, detail=1)
        for k in range(5):
            a = k * 1.26
            rope('Fray', [(.058, -.028, hz - .135), (.058 + math.cos(a) * .008, -.028 + math.sin(a) * .008, hz - .16)], .0013, P['hemp_new'], group=g, detail=2, seg=5)
    else:
        for sx in (-1, 1):
            x = sx * .15
            rbox('Upright', (x, 0, (BOARD_TOP - .06 + HANDLE_TOP - .003) / 2), (.036, .032, HANDLE_TOP - .003 - BOARD_TOP + .06), P['handle'], r=.005, amp=.001, seed=sx + 30, div=.03, group=g, grain='z')
            rbox('Wedge', (x, 0, HANDLE_TOP - .0035), (.008, .03, .004), P['peg'], r=.0012, div=.012, group=g, grain='y', detail=1)
            cyl('Peg', (x, -.0165, BOARD_TOP - .03), .0058, .006, P['peg'], axis='y', verts=10, group=g, detail=1, bevel=.0012)
        hz = HANDLE_TOP - .03
        rbox('Handle_Bar', (0, 0, hz), (.42, .034, .034), P['handle'], r=.007, amp=.001, seed=33, div=.03, group=g, grain='x')
        # a short worn cord: one household's hand-tie, not structural
        lash('Grip', (0, 0, hz), (1, 0, 0), .023, .07, .0036, P['hemp'], turns=8, group=g)
    socket('Socket_GateHandle', (0, 0, hz))
    socket('Socket_GateOpen', (0, 0, FLOOR + .002 + .3))


def build(P, v):
    frame(P, v); gate_board(P, v); handle(P, v)
    socket('Socket_PortFront', (0, -.25, FLOOR))
    socket('Socket_PortBack', (0, .25, FLOOR))
    S['collision'] = [((-.4, -.25, 0), (-CLEAR, .25, .52)), ((CLEAR, -.25, 0), (.4, .25, .52))]


def cr09_a(P): build(P, 'A')
def cr09_b(P): build(P, 'B')
