"""VL04-05 lived-in houses (work pack B-40h, 2026-11-08): the StarterHouse v004 outline (vl_house) dressed for the people who live in it.

  VL04 diligent family (three-view VL04 candidate-01): a crossed-bamboo drying rack on the left of the porch with three pieces of washing
       over the pole, a neat stack of split firewood against the right gable wall on two rails between stakes under a straw mat held down
       by two stones, a shallow bamboo tray of dried chillies and garlic on the right front window sill, a pair of straw sandals at the
       door. Repaired plaster, swept porch, faded but cared-for timber (palette 'diligent').
  VL05 elderly couple (three-view VL05 candidate-01): a low bamboo chair right of the door, seven bundles of dried corn hung from the
       porch header over the steps, newer paper patches pasted over the old yellowed window and door paper, an old pine bonsai in an
       oval stoneware pot left of the door. Very old dark timber, moss on the stone base, roof tiles of every age (palette 'elderly').

The small things at the door (rack, washing, tray, sandals) are Detail_Small so a low quality tier can drop them; the woodpile is Main
(it is part of the silhouette and has its own collision box).
Every piece that stands on something is recorded in S['lived_rest'] (label, x, y, bottom z) for the rest-on-surface check.
"""
import math, random
from mathutils import Vector, noise
from ti_core import S, box, cyl, mesh, lathe, sphere, tube
from cr_parts import rbox, sheet, pole, xlash
import cr_mats as cm
import ti_mats as tm

FLOOR = .54
DET = dict(group='Detail_Small', detail=0)


def rest(label, x, y, z):
    S.setdefault('lived_rest', []).append((label, round(x, 4), round(y, 4), round(z, 4)))


# ------------------------------------------------------------------ materials
def end_grain(name, light=(.36, .23, .12), dark=(.16, .09, .045), bark=(.05, .035, .022), slot='Main'):
    """Sawn log end on 'cuv' (x = 0 at the pith .. 1 at the bark, y = angle / tau): growth rings, a darker heart, radial checks,
    a thin bark rim and grey weathering towards the edge."""
    m, g = tm._new(name, slot)
    P = g.geo('Position')
    C = g.attr('cuv'); cs = g.node('ShaderNodeSeparateXYZ'); g.link(C, cs.inputs[0])
    rr, aa = cs.outputs['X'], cs.outputs['Y']
    wob = g.math('MULTIPLY', g.math('SUBTRACT', g.noise(P, 9.0, 3, .5), .5), .12)
    rw = g.math('ADD', rr, wob)
    rings = g.math('POWER', g.math('ABSOLUTE', g.math('SINE', g.math('MULTIPLY', rw, 34.0))), 6.0)
    heart = g.maprange(rr, .55, .2)
    col = g.ramp(g.math('ADD', g.math('MULTIPLY', g.noise(P, 30.0, 3, .5), .5), g.math('MULTIPLY', heart, .35)),
                 [(.25, light), (.6, tuple(c * .8 for c in light)), (.9, tuple((a + b) / 2 for a, b in zip(light, dark)))])
    col = g.mix(g.math('MULTIPLY', rings, .45), col, dark)
    chk = g.maprange(g.math('ABSOLUTE', g.math('SUBTRACT', g.math('FRACT', g.math('MULTIPLY', g.math('ADD', aa, g.math('MULTIPLY', g.noise(P, 4., 2, .5), .08)), 5.0)), .5)), .015, .0)
    chk = g.math('MULTIPLY', chk, g.maprange(rr, .2, .45))
    col = g.mix(g.math('MULTIPLY', chk, .8), col, tuple(c * .4 for c in dark))
    rim = g.maprange(rr, .86, .95)
    col = g.mix(rim, col, bark)
    grey = g.math('MULTIPLY', g.maprange(rr, .5, .9), g.maprange(g.noise(P, 3.0, 3, .5), .4, .65))
    col = g.mix(g.math('MULTIPLY', grey, .35), col, (.2, .18, .15))
    ao = g.ao(.03)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.4, .38, .36)), (1, (1, 1, 1))]))
    tm._finish(g, col, .82, 0.0, g.bump(g.math('ADD', rings, g.math('MULTIPLY', chk, -2.)), .3, .0015), spec=.2)
    return m


def reed_mat(name, dark=(.1, .075, .04), light=(.36, .29, .15)):
    """Straw mat over the woodpile: reeds laid down the slope (along x), read in 2-3 cm tone bands across y so they survive the
    ~120 px/m bake, tied with three dark cords across the reeds at x 3.92 / 4.12 / 4.32."""
    m, g = tm._new(name, 'Main')
    P = g.geo('Position'); sep = g.node('ShaderNodeSeparateXYZ'); g.link(P, sep.inputs[0])
    X = sep.outputs['X']
    reed = g.noise(g.vmath('MULTIPLY', P, (.06, 1., .06)), 42., 3, .5)
    fine = g.noise(g.vmath('MULTIPLY', P, (.03, 1., .03)), 150., 2, .5)
    big = g.noise(P, 1.6, 3, .5)
    t = g.math('ADD', g.math('ADD', g.math('MULTIPLY', reed, .6), g.math('MULTIPLY', fine, .15)), g.math('MULTIPLY', big, .25))
    col = g.ramp(t, [(.32, tuple(c * .7 for c in dark)), (.45, dark), (.62, light), (.72, tuple(min(1., c * 1.12) for c in light))])
    grey = g.maprange(big, .45, .62)
    col = g.mix(g.math('MULTIPLY', grey, .3), col, (.2, .18, .14))                     # sun-greyed where it lies longest
    cd = g.math('ABSOLUTE', g.math('SUBTRACT', g.math('FRACT', g.math('DIVIDE', g.math('SUBTRACT', X, 3.82), .2)), .5))
    cord = g.maprange(cd, .035, .02)                                                   # 0.8-1.4 cm wide
    col = g.mix(g.math('MULTIPLY', cord, .85), col, (.06, .045, .025))
    ao = g.ao(.08)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.32, .3, .28)), (1, (1, 1, 1))]))
    h = g.math('ADD', g.math('MULTIPLY', reed, .7), g.math('MULTIPLY', cord, -.5))
    tm._finish(g, col, .9, 0.0, g.bump(h, .8, .008), spec=.1)
    return m


def mats(P, cond):
    P['bamboo'] = cm.culm('Rack_Bamboo', green=(.13, .11, .045), straw=(.3, .22, .09), mud_h=0.)
    P['twine'] = tm.plain('Twine', (.17, .12, .06), rough=.92, noise=.45, scale=60.)
    P['tray'] = tm.straw('Bamboo_Tray', (.44, .35, .17), (.13, .09, .035), reed=.009, block=.04, wear=False)    # blocks big enough for the bake
    P['sandal'] = tm.straw('Straw_Sandal', (.4, .32, .16), (.2, .15, .07), reed=.005, block=.018, wear=False)
    P['chilli'] = tm.plain('Dried_Chilli', (.42, .035, .016), rough=.38, noise=.45, scale=30.)
    P['chilli_stem'] = tm.plain('Chilli_Stem', (.07, .07, .025), rough=.7, noise=.3)
    P['garlic'] = tm.plain('Garlic_Skin', (.47, .39, .3), rough=.66, noise=.35, scale=40.)
    P['radish'] = tm.plain('Dried_Radish', (.34, .24, .13), rough=.8, noise=.5, scale=25.)
    P['wash'] = [cm.canvas('Washing_Undyed', base=(.66, .63, .55), stain=(.36, .3, .2), faded=.25, dirt=.18),
                 cm.canvas('Washing_Indigo', base=(.07, .1, .2), stain=(.03, .04, .08), faded=.45, dirt=.12),
                 cm.canvas('Washing_GreyBlue', base=(.22, .27, .31), stain=(.1, .11, .12), faded=.3, dirt=.15)]
    P['bark_fw'] = cm.wood('Firewood_Bark', (.03, .022, .015), (.12, .09, .06), grey=.55, ground_h=0.)
    P['split_fw'] = cm.wood('Firewood_Split', (.15, .09, .045), (.38, .25, .13), grey=.3, ground_h=0.)
    P['end_fw'] = end_grain('Firewood_End')
    P['mat_straw'] = reed_mat('Woodpile_Straw_Mat')
    if cond == 'elderly' and 'corn' not in P: mats_elderly(P)


# ------------------------------------------------------------------ drying rack and washing (VL04)
def drying_rack(P, R):
    """Two crossed-bamboo trestles (legs spread front to back, lashed where they cross) carrying one pole along the porch."""
    yc = -3.38; spread = .22; zc = 2.05; top = 2.42; rl = .017
    f = (zc - FLOOR) / (top - FLOOR); t = spread / f - spread          # leg tops run past the crossing by t
    frames = (-3.32, -1.25)
    for k, x0 in enumerate(frames):
        legs = []
        for s in (-1, 1):
            xs = x0 + s * (rl + .0015)                                  # the two legs pass side by side
            a = (xs, yc + s * spread, FLOOR - .004); b = (xs, yc - s * t, top)
            pole('Rack_Leg', a, b, rl + .002, rl, P['bamboo'], node_gap=.4, seed=k * 2 + (s > 0), seg=8, **DET)
            legs.append((Vector(a), Vector(b)))
            rest('rack_leg', a[0], a[1], FLOOR)
        (a1, b1), (a2, b2) = legs
        xlash('Rack_Lash', (x0, yc, zc), b1 - a1, rl * 1.9, b2 - a2, rl * 1.9, .0032, P['twine'], seg=6, step=.01, group='Detail_Small')
    rp = .021
    zp = zc + (rp + rl) / t * (top - zc) + .002                         # where the V between the leg tops is as wide as pole + leg
    pole('Rack_Pole', (frames[0] - .3, yc, zp), (frames[1] + .3, yc, zp - .008), rp, rp * .85, P['bamboo'], node_gap=.38, bend=.01, seed=9, seg=10, **DET)
    S['rack'] = dict(y=yc, z=round(zp, 3), r=rp)
    for i, (x0, x1, lf, lb) in enumerate(((-3.2, -2.72, .8, .6), (-2.64, -2.1, .86, .66), (-2.02, -1.6, .64, .5))):
        washing(P, R, i, x0, x1, yc, zp - .004 * (i + 1), rp, lf, lb)


def washing(P, R, i, x0, x1, y, zp, rp, lf, lb):
    """One piece of washing folded over the pole: back drop, over the top, front drop. Folds start at the pole and deepen towards the
    hem (two wave trains of different length), the hem flares a little, hangs unevenly and one corner is lower."""
    rw = rp + .004; arc = math.pi * rw; L = lb + arc + lf
    ph1, ph2 = R.uniform(0, 6.3), R.uniform(0, 6.3); k1, k2 = R.uniform(2.2, 3.2), R.uniform(5., 7.)
    tilt = R.uniform(-.05, .05); W = x1 - x0
    def fn(u, v):
        d = v * L
        if d < lb:                                    # back: hangs down at +y, d = 0 is the back hem
            yy, zz, far, side = y + rw, zp - (lb - d), (lb - d) / lb, 1
        elif d < lb + arc:                            # over the pole
            a = (d - lb) / rw                          # 0 at the back, pi at the front
            yy, zz, far, side = y + rw * math.cos(a), zp + rw * math.sin(a), 0., 0
        else:
            yy, zz, far, side = y - rw, zp - (d - lb - arc), (d - lb - arc) / lf, -1
        f = far ** .7
        fold = (math.sin(u * math.pi * 2 * k1 + ph1) * .024 + math.sin(u * math.pi * 2 * k2 + ph2) * .008) * f
        fold += noise.noise(Vector((u * 4.1 + i * 3, d * 3.3, 1.7))) * .012 * f
        x = x0 + W * u + (u - .5) * W * .05 * f + math.sin(u * math.pi * 2 * k1 + ph1 + 1.57) * .012 * f     # folds pull the cloth in and out
        if side:
            yy += side * (.02 * f + fold)
            zz += (tilt * (u - .5) * 2 - .018 * (1 - (2 * u - 1) ** 2) + noise.noise(Vector((u * 7., i * 1.3, 4.))) * .012) * f
        return (x, yy, zz)
    sheet(f'Washing_{i}', 14, 28, fn, P['wash'][i], solid=.0025, **DET)['both_sides'] = .006


# ------------------------------------------------------------------ woodpile (VL04)
def _section(r, kind, rot, R):
    """Cross-section (y, z, face) of one piece around the origin: 'round', 'half' or 'quarter', 'b' bark / 's' split edges."""
    if kind == 'round':
        sec = [(r * (1 + .06 * math.sin(3 * a + R.random())) * math.cos(a), r * (1 + .06 * math.sin(3 * a)) * math.sin(a), 'b')
               for a in [k * math.tau / 9 for k in range(9)]]
        centre = (0., 0.)
    elif kind == 'half':
        sec = [(r * R.uniform(.9, 1.06) * math.cos(a), r * R.uniform(.9, 1.06) * math.sin(a), 'b') for a in [k * math.pi / 5 for k in range(6)]]
        sec[-1] = (sec[-1][0], sec[-1][1], 's')        # the edge from the last arc point back to the first is the split face
        centre = (0., 0.)
    else:
        span = R.uniform(1.25, 1.85)
        sec = [(0., 0., 's')] + [(r * R.uniform(.9, 1.08) * math.cos(a), r * R.uniform(.9, 1.08) * math.sin(a), 'b') for a in [k * span / 3 for k in range(4)]]
        sec[-1] = (sec[-1][0], sec[-1][1], 's')
        centre = None
    ca, sa = math.cos(rot), math.sin(rot)
    return [(p * ca - q * sa, p * sa + q * ca, f) for p, q, f in sec]


def _profile(sec, ys):
    """Lowest and highest z of a section at each y column (None where the column misses it)."""
    lo, hi = [None] * len(ys), [None] * len(ys)
    n = len(sec)
    for i in range(n):
        (ya, za, _), (yb, zb, _) = sec[i], sec[(i + 1) % n]
        if abs(yb - ya) < 1e-9: continue
        for k, y in enumerate(ys):
            t = (y - ya) / (yb - ya)
            if 0 <= t <= 1:
                z = za + (zb - za) * t
                lo[k] = z if lo[k] is None else min(lo[k], z); hi[k] = z if hi[k] is None else max(hi[k], z)
    return lo, hi


def _log(V, F, MI, CUV, x0, x1, pts, r, kind):
    """One piece of firewood along x from its placed section: bark / split faces, sawn ends with end grain."""
    n = len(pts)
    if kind == 'round': pith = (sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n)
    elif kind == 'half': pith = ((pts[0][0] + pts[-1][0]) / 2, (pts[0][1] + pts[-1][1]) / 2)
    else: pith = (pts[0][0], pts[0][1])
    def cuv(a, b):
        dy, dz = a - pith[0], b - pith[1]
        return (min(1., math.hypot(dy, dz) / r), (math.atan2(dz, dy) / math.tau) % 1., 0.)
    base = len(V)
    for x in (x0, x1):
        for a, b, f in pts: V.append((x, a, b)); CUV.append(cuv(a, b))
    for i in range(n):
        j = (i + 1) % n
        F.append((base + i, base + j, base + n + j, base + n + i)); MI.append(1 if pts[i][2] == 's' else 0)
    for end, x in enumerate((x0, x1)):           # sawn ends: end grain; a fan from the pith (the wedge apex is a corner already)
        off = base + end * n
        if kind == 'quarter':
            F.append(tuple(off + i for i in range(n))); MI.append(2); continue
        ci = len(V); V.append((x, pith[0], pith[1])); CUV.append((0., 0., 0.))
        for i in range(n):
            if kind == 'half' and i == n - 1: continue          # that edge is the split face itself
            j = (i + 1) % n
            F.append((ci, off + i, off + j)); MI.append(2)
    return pts


def woodpile(P, R):
    x0, x1 = 3.86, 4.34
    y0, y1 = -1.52, 1.32
    # two rails on the ground and four stakes at the ends
    for xr in (3.97, 4.23):
        rbox('Woodpile_Rail', (xr, (y0 + y1) / 2, .035), (.07, y1 - y0 + .2, .07), P['bark_fw'], r=.012, amp=.004, freq=4., seed=int(xr * 10), div=.1, flat='z', group='Main')
        rest('woodpile_rail', xr, 0., 0.)
    V, F, MI, CUV = [], [], [], []
    pitch_y = .135
    # every piece is dropped onto what is already there: a height line along the pile (1 mm columns) that starts at the rail tops;
    # the piece's own section outline comes down until its lowest point over any column meets that line, pressed 2.5 mm in. All
    # pieces run the same way (x 3.85-4.37, over both rails), so the outline in y-z is the whole contact problem.
    G = .001; ny = int((y1 - y0 + .2) / G) + 1; gy0 = y0 - .1
    H = [.07] * ny
    tops = []; logs = []; ends = []
    for row in range(8):
        off = (row % 2) * pitch_y / 2
        y = y0 + .066 + off
        while y < y1 - .06:
            r = R.uniform(.05, .066); yy = y + R.uniform(-.004, .004)
            kind = R.choices(('round', 'half', 'quarter'), (.25, .35, .4))[0]
            sec = _section(r, kind, R.uniform(0, math.tau), R)
            k0 = int((yy - r * 1.15 - gy0) / G); k1 = int((yy + r * 1.15 - gy0) / G) + 1
            ks = list(range(max(0, k0), min(ny, k1)))
            lo, hi = _profile(sec, [gy0 + k * G - yy for k in ks])
            zc = max(H[k] - l for k, l in zip(ks, lo) if l is not None) - .0025
            for k, h in zip(ks, hi):
                if h is not None: H[k] = max(H[k], zc + h)
            pts = [(yy + a, zc + b, f) for a, b, f in sec]
            bb = (min(q[0] for q in pts), max(q[0] for q in pts), min(q[1] for q in pts), max(q[1] for q in pts))
            touching = [e for e in ends if e[0][0] < bb[1] + .005 and e[0][1] > bb[0] - .005 and e[0][2] < bb[3] + .005 and e[0][3] > bb[2] - .005]
            for _ in range(40):      # flush on the wall side, ragged outside; sawn ends of touching pieces never share a plane
                jx0 = x0 + R.uniform(-.01, .01); jx1 = jx0 + R.uniform(.42, .5)
                if all(abs(jx0 - e[1]) > .003 and abs(jx1 - e[2]) > .003 for e in touching): break
            ends.append((bb, jx0, jx1))
            _log(V, F, MI, CUV, jx0, jx1, pts, r, kind)
            tops.append(max(p[1] for p in pts)); logs.append([(round(a, 5), round(b, 5)) for a, b, _ in pts])
            y += pitch_y
    S['woodpile_logs'] = logs
    o = mesh('Woodpile_Logs', V, F, P['bark_fw'], grain='x', group='Main')
    o.data.materials.append(P['split_fw']); o.data.materials.append(P['end_fw'])
    o.data.polygons.foreach_set('material_index', MI)
    import bmesh
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    from cr_parts import set_attr_list
    set_attr_list(o, 'cuv', CUV)
    top = max(tops)
    S['woodpile_top'] = round(top, 3)
    # straw mat over the top, sloping off the wall, the outer edge drooping over the log ends; two stones hold it down
    zt = top + .012
    def fn(u, v):
        y = y0 - .1 + (y1 - y0 + .2) * u; x = 3.82 + .62 * v
        z = zt + .045 * (1 - v) + .008 * math.sin(u * 17.) * (1 - v)
        if x > 4.37: z -= (x - 4.37) * 1.1
        if u < .03 or u > .97: z -= .02
        return (x, y, z + .006 * noise.noise(Vector((u * 9., v * 5., .3))))
    mo = sheet('Woodpile_Mat', 22, 6, fn, P['mat_straw'], solid=.022, group='Main', grain='y'); mo['both_sides'] = .015
    # four stakes at the ends hold the stack; the mat is laid over their tops, so each stake stops 3 mm under the mat's underside,
    # measured on the thickened mat itself: rays straight up from under the stack at the stake's centre and eight points on its rim
    import bpy
    from mathutils.bvhtree import BVHTree
    bpy.context.view_layer.update()
    mt = BVHTree.FromObject(mo, bpy.context.evaluated_depsgraph_get())
    def mat_under(x, y):
        zs = []
        for k in range(9):
            a = k * math.tau / 8; rr = 0. if k == 8 else .033
            h = mt.ray_cast(Vector((x + rr * math.cos(a), y + rr * math.sin(a), .2)), Vector((0, 0, 1)), 3.)
            if h[0] is not None: zs.append(h[0].z)
        return min(zs)
    stakes = []
    for yy in (y0 - .075, y1 + .075):
        for xs in (3.9, 4.3):
            h = mat_under(xs, yy) - .003
            cyl('Woodpile_Stake', (xs, yy, h / 2), .033, h, P['bark_fw'], verts=8, bevel=.006, group='Main', grain='z')
            rest('woodpile_stake', xs, yy, 0.); stakes.append((xs, yy, round(h, 4)))
    S['woodpile_stakes'] = stakes
    from vl_house import snap0
    import bpy
    for i, yy in enumerate((y0 + .45, y1 - .5)):
        hit = snap0((4.08, yy, 3.), (0, 0, -1))
        st = rbox('Mat_Weight_Stone', (4.08, yy, hit[0].z + .06), (.2, .16, .1), P['stone'][i % 2], r=.035, amp=.012, freq=3., seed=80 + i, div=.05,
                  rot=(0, .06 - .12 * i, .3 * i), group='Main')
        bpy.context.view_layer.update()
        low = min((st.matrix_world @ v.co).z for v in st.data.vertices)
        st.location.z -= low - (hit[0].z - .008)                     # pressed 8 mm into the straw


# ------------------------------------------------------------------ dried vegetables on the window sill (VL04)
def sill_tray(P, R):
    """The stone sill stands only 9 cm proud of the window rail (rail face y -2.75, sill edge -2.84), too little for a tray, so the
    family has laid a board on it that runs 13.5 cm further out, carried by two braces down to the wall under the sill. On the board a
    long bamboo drying tray: red chillies, strips of dried radish and a few garlic heads. Board and braces are part of the house
    (Main); the tray and what is in it are Detail."""
    from cr_parts import rbox as _rb
    by0, by1, bz = -2.748, -2.975, 1.29                       # board back (2 mm off the rail), front, underside = sill top
    bt = .022; bw = .56; bcy = (by0 + by1) / 2
    _rb('Sill_Board', (2.2, bcy, bz + bt / 2), (bw, by0 - by1, bt), P['plank'], r=.004, amp=.002, freq=4., seed=31, div=.06, group='Main')
    rest('sill_board', 2.2, -2.80, bz)
    for i, xb in enumerate((2.2 - .2, 2.2 + .2)):
        lo = Vector((xb, -2.61 - .012, .9)); hi = Vector((xb, by1 + .02, bz - .004))   # foot 1.2 cm into the plaster, head under the board
        v = hi - lo; ang = math.atan2(-v.y, v.z)
        _rb('Sill_Brace', tuple((lo + hi) / 2), (.034, .034, v.length), P['timber'], r=.004, amp=.002, seed=33 + i, div=.06, rot=(ang, 0, 0), group='Main')
    cx, cy, z0 = 2.2, bcy - .004, bz + bt
    TW, TD, RH, RT = .46, .18, .034, .012                       # tray outside size, rim height and thickness
    _rb('Bamboo_Tray', (cx, cy, z0 + .004), (TW, TD, .008), P['tray'], r=.003, div=.05, **DET)
    for sx in (-1, 1):
        _rb('Bamboo_Tray_Rim', (cx + sx * (TW - RT) / 2, cy, z0 + RH / 2), (RT, TD, RH), P['tray'], r=.004, div=.05, **DET)
    for sy in (-1, 1):
        _rb('Bamboo_Tray_Rim', (cx, cy + sy * (TD - RT) / 2, z0 + RH / 2), (TW - 2 * RT + .002, RT, RH), P['tray'], r=.004, div=.05, **DET)
    rest('tray', cx, cy, z0)
    fz = z0 + .008
    IX, IY = TW / 2 - RT - .004, TD / 2 - RT - .004             # inside half sizes
    placed = []
    def free(px, py, rad):
        return all(math.hypot(px - qx, (py - qy) / .9) > rad + qr for qx, qy, qr in placed)
    for i, (dx, dy) in enumerate(((-.16, .03), (-.1, -.035), (.15, .032), (.09, -.03), (.005, .036))):
        c = (cx + dx, cy + dy, fz + .021)
        sphere('Garlic', c, .026, P['garlic'], scale=(1., 1., .8), seg=14, ring=8, **DET)
        lathe('Garlic_Neck', [(.008, 0.), (.005, .012), (.002, .022), (0., .025)], (c[0], c[1], c[2] + .016), P['garlic'], seg=8, **DET)
        placed.append((c[0], c[1], .03))
    rad = .0085
    inside = lambda e: abs(e.x - cx) <= IX - rad and abs(e.y - cy) <= IY - rad
    def chilli(pts, d):
        tube('Chilli', [tuple(q) for q in pts], rad, P['chilli'], radii=[1., .85, .22] if len(pts) == 3 else [1., .92, .78, .22], res=6, **DET)
        p0 = pts[0]
        tube('Chilli_Stem', [tuple(p0 + d * .004), tuple(p0 - d * .016 + Vector((0, 0, .007)))], .0028, P['chilli_stem'], res=4, group='Detail_Small', detail=1)
    first = []
    for k in range(300):                      # first layer, lying on the tray
        if len(first) >= 18: break
        px, py = cx + R.uniform(-IX, IX), cy + R.uniform(-IY, IY)
        if not free(px, py, .016): continue
        yaw = R.uniform(0, math.tau); L = R.uniform(.08, .1); d = Vector((math.cos(yaw), math.sin(yaw), 0)); sd = Vector((-d.y, d.x, 0))
        c0 = Vector((px, py, fz + rad * .9))
        if not (inside(c0 + d * L / 2) and inside(c0 - d * L / 2)): continue
        bend = R.uniform(-.018, .018); p0 = c0 - d * L / 2
        chilli([p0, p0 + d * L * .45 + sd * bend, p0 + d * L + sd * bend * .3 + Vector((0, 0, -.003))], d)
        placed.append((px, py, .02)); first.append((c0, yaw))
    second = 0
    for k in range(200):                      # second layer: each one draped across one of the first layer
        if second >= 10: break
        c0, yaw0 = R.choice(first)
        yaw = yaw0 + math.pi / 2 + R.uniform(-.5, .5); L = R.uniform(.08, .1); d = Vector((math.cos(yaw), math.sin(yaw), 0))
        mid = c0 + d * R.uniform(-.02, .02) + Vector((0, 0, 2 * rad * .92))
        e0, e1 = mid - d * L / 2, mid + d * L / 2
        e0.z = e1.z = fz + rad * .9
        if not (inside(e0) and inside(e1)): continue
        chilli([e0, mid - d * .012, mid + d * .012, e1], d)
        second += 1
    n = len(first) + second
    m = 0
    for k in range(300):
        if m >= 12: break
        px, py = cx + R.uniform(-IX, IX), cy + R.uniform(-IY, IY)
        if not free(px, py, .01): continue
        yaw = R.uniform(0, math.tau); L = R.uniform(.06, .085); d = Vector((math.cos(yaw), math.sin(yaw), 0)); sd = Vector((-d.y, d.x, 0))
        if any(abs(e.x - cx) > IX - .008 or abs(e.y - cy) > IY - .008 for e in (Vector((px, py, 0)) + d * L / 2, Vector((px, py, 0)) - d * L / 2)): continue
        def fs(u, v, px=px, py=py, d=d, sd=sd, L=L):
            q = Vector((px, py, fz + .002 + .006 * math.sin(u * math.pi) ** 2)) + d * (u - .5) * L + sd * (v - .5) * .014
            return tuple(q + sd * .006 * math.sin(u * 5.))
        sheet('Dried_Radish', 6, 1, fs, P['radish'], solid=.003, **DET)
        placed.append((px, py, .012)); m += 1
    S['tray_items'] = dict(chillies=n, radish=m, garlic=5)


# ------------------------------------------------------------------ straw sandals at the door (VL04)
def sandals(P, R):
    for i, (x, y, yaw) in enumerate(((-.17, -3.0, .08), (.09, -3.03, -.12))):
        d = Vector((-math.sin(yaw), math.cos(yaw), 0)); s = Vector((d.y, -d.x, 0))     # d: toe direction (towards the door)
        rbox('Sandal_Sole', (x, y, FLOOR + .009), (.095, .245, .018), P['sandal'], r=.008, amp=.002, freq=8., seed=30 + i, div=.03,
             rot=(0, 0, yaw), flat='z', **DET)
        rest('sandal', x, y, FLOOR)
        c = Vector((x, y, FLOOR + .018))
        toe = c + d * .085 + Vector((0, 0, .002))
        for sg in (-1, 1):
            side = c + s * sg * .043 - d * .01
            tube('Sandal_Strap', [tuple(side), tuple(c + s * sg * .03 + d * .045 + Vector((0, 0, .028))), tuple(toe + Vector((0, 0, .012))), tuple(toe)],
                 .006, P['twine'], res=4, **DET)
        heel = c - d * .1
        tube('Sandal_Heel_Loop', [tuple(heel + s * .03), tuple(heel - d * .015 + Vector((0, 0, .018))), tuple(heel - s * .03)], .004, P['twine'], res=4, **DET)


# ------------------------------------------------------------------ entry points
def dress(P, R, cond):
    mats(P, cond)
    if cond == 'diligent':
        drying_rack(P, R)
        woodpile(P, R)
        sill_tray(P, R)
        sandals(P, R)
        __import__('vl_house').plinth_grass(P, R, 6)
    elif cond == 'elderly':
        bamboo_chair(P, R)
        corn_string(P, R)
        bonsai(P, R)
        door_patches(P, R)
        H = __import__('vl_house')
        H.moss_on_roof(P, R, 10); H.plinth_grass(P, R, 16)


def collision(prism, cond):
    if cond == 'diligent':
        prism(3.8, 4.45, -1.65, 1.45, 0., round(S['woodpile_top'] + .07, 3))          # the woodpile; the drying rack has its own box in detail_collision


# props in Detail_Small, with the yaw of the box that wraps them (the chair is turned towards the steps)
DETAIL_PROPS = {'diligent': [('drying_rack', ('Rack_', 'Washing_'), 0.)],
                'elderly': [('bamboo_chair', ('Chair_',), -.35), ('bonsai', ('Bonsai_',), 0.)]}


def detail_collision(cond):
    """One box per door-front prop that sits in Detail_Small (VL04 drying rack with its washing, VL05 bamboo chair, bonsai), from the
    porch floor to the prop's top, 1 cm outside the prop's own vertices (modifiers applied), turned with the prop. They go into
    <ID>_Detail_Collision, apart from <ID>_Collision, so the game switches them off together with Detail_Small and no invisible
    block is left behind. Things under 2.3 m (porch floor + 1.75 m figure + 1 cm) decide the box; the rack pole and the leg tops
    above that are left out so the box ends where a head would touch."""
    import bpy
    dg = bpy.context.evaluated_depsgraph_get()
    V, F = [], []
    boxes = []
    for label, prefixes, yaw in DETAIL_PROPS.get(cond, []):
        ca, sa = math.cos(yaw), math.sin(yaw)
        pts = []
        for o in S['parts']:
            if o.type != 'MESH' or not o.name.startswith(prefixes): continue
            ev = o.evaluated_get(dg); me = ev.to_mesh(); mw = o.matrix_world
            pts += [mw @ v.co for v in me.vertices]
            ev.to_mesh_clear()
        assert pts, label
        loc = [(p.x * ca + p.y * sa, -p.x * sa + p.y * ca, p.z) for p in pts]          # into the prop's turned frame
        low = [q for q in loc if q[2] <= FLOOR + 1.76]
        u0 = min(q[0] for q in low) - .01; u1 = max(q[0] for q in low) + .01
        v0 = min(q[1] for q in low) - .01; v1 = max(q[1] for q in low) + .01
        top = round(min(max(p.z for p in pts) + .01, FLOOR + 1.76), 3)
        corners = [(u * ca - v * sa, u * sa + v * ca) for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1))]
        __import__('fr_parts').hull_loft(V, F, [[(x, y, z) for x, y in corners] for z in (FLOOR, top)])
        boxes.append({'prop': label, 'yaw': yaw, 'corners_xy': [[round(x, 4), round(y, 4)] for x, y in corners], 'z': [FLOOR, top],
                      'centre_xy': [round(sum(c[0] for c in corners) / 4, 4), round(sum(c[1] for c in corners) / 4, 4)],
                      'half_m': [round((u1 - u0) / 2, 4), round((v1 - v0) / 2, 4)],
                      'prop_top_m': round(max(p.z for p in pts), 3), 'vertices': len(pts)})
    S['detail_boxes'] = boxes
    return (V, F) if V else None


# ================================================================== VL05 elderly couple
def mats_elderly(P):
    P['chair_bamboo'] = cm.culm('Chair_Bamboo', green=(.09, .065, .028), straw=(.27, .18, .075), mud_h=0.)     # old honey-brown bamboo
    P['chair_slat'] = cm.wood('Chair_Slat', (.1, .06, .025), (.3, .2, .085), grey=.25, ground_h=0., polish=.35)  # split bamboo, polished by use
    P['corn'] = tm.plain('Dried_Corn', (.66, .27, .025), rough=.5, noise=.4, scale=55.)          # orange-gold, as dried flint corn
    P['husk'] = cm.paper('Corn_Husk', base=(.44, .36, .2), edge=(.27, .19, .09), age=.4)
    P['patch_new'] = cm.paper('Paper_Patch_New', base=(.86, .83, .73), edge=(.62, .57, .45), age=.08)
    P['patch_mid'] = cm.paper('Paper_Patch_Older', base=(.62, .55, .4), edge=(.42, .34, .21), age=.3)
    P['bonsai_pot'] = cm.clay('Bonsai_Pot', body=(.14, .17, .15), glaze=(.08, .11, .1))
    P['bonsai_bark'] = cm.wood('Bonsai_Bark', (.03, .024, .018), (.13, .1, .075), grey=.55, ground_h=0.)
    P['pine'] = tm.plain('Bonsai_Pine', (.04, .085, .03), rough=.9, noise=.75, scale=90., bump=.7)


def paper_patches(P, name, cx, sill, w, h):
    """VL05: pieces of newer paper pasted over holes, in wall-local coordinates (called inside the wall's transform by vl_house.window):
    one patch per lattice cell, never in two neighbouring cells (so no two patches overlap), between the paper and the lattice."""
    if 'patch_new' not in P: mats_elderly(P)            # the walls are built before dress() sets up the VL05 materials
    R = random.Random('patch' + name)
    wall = name.split('_')[1]
    n = 7 if wall == 'Front' else R.choice((4, 5))
    cw, ch = w / 6, h / 5
    pw, ph = w - .1, h - .1
    used = []
    M = S['M'][-1]
    for _ in range(600):
        if len(used) >= n: break
        i, k = R.randrange(6), R.randrange(5)
        two = i < 5 and R.random() < .3                          # pasted across a bar, over two cells
        cells = [(i, k)] + ([(i + 1, k)] if two else [])
        if any(abs(c[0] - a) <= 1 and abs(c[1] - b) <= 1 for c in cells for a, b in used): continue
        used += cells
        sx, sz = cw * (R.uniform(1.2, 1.6) if two else R.uniform(.45, .8)), ch * R.uniform(.4, .75)
        x = cx - w / 2 + (i + (1. if two else .5)) * cw + R.uniform(-.35, .35) * max(0., (2 if two else 1) * cw - sx)
        z = sill + (k + .5) * ch + R.uniform(-.35, .35) * (ch - sz)
        x = min(max(x, cx - pw / 2 + sx / 2 + .006), cx + pw / 2 - sx / 2 - .006)
        z = min(max(z, sill + .05 + sz / 2 + .006), sill + .05 + ph - sz / 2 - .006)
        jit = [(R.uniform(-.007, .007), R.uniform(-.007, .007)) for _ in range(4)]
        def fn(u, v, x=x, z=z, sx=sx, sz=sz, jit=jit):
            a = jit[int(round(u)) + 2 * int(round(v))] if u in (0, 1) and v in (0, 1) else (0., 0.)
            return (x - sx / 2 + sx * u + a[0], -.0345, z - sz / 2 + sz * v + a[1])
        sheet(f'{name}_Patch', 2, 2, fn, P['patch_new'] if R.random() < .55 else P['patch_mid'], solid=.0015, grain='x', detail=1)
        S.setdefault('paper_patches', []).append((tuple(M @ Vector((x, -.0345, z))), tuple((M.to_3x3() @ Vector((0, -1, 0))).normalized()), .00075))


def door_patches(P, R):
    """VL05: two or three patches on each door leaf's paper, each inside one lattice cell (clear of the bars and rails in front)."""
    for side in (-1, 1):
        cxl = side * (.84 - .415)
        used = []
        n = R.choice((2, 3))
        for _ in range(100):
            if len(used) >= n: break
            i, k = R.randrange(4), R.randrange(4)
            if any(abs(i - a) <= 1 and abs(k - b) <= 1 for a, b in used): continue
            used.append((i, k))
            xc = cxl - .28 + .07 + i * .14; zc = 1.85 + .115 + k * .23
            iw, ih = .14 - .025 - .008, .23 - .035 - .008                 # the cell inside the bars, 4 mm clear of each
            sx, sz = iw * R.uniform(.5, .95), ih * R.uniform(.45, .9)
            x = xc + R.uniform(-.5, .5) * (iw - sx); z = zc + R.uniform(-.5, .5) * (ih - sz)
            sheet('Door_Paper_Patch', 2, 2, lambda u, v, x=x, z=z, sx=sx, sz=sz: (x - sx / 2 + sx * u, -2.7236, z - sz / 2 + sz * v),
                  P['patch_new'] if R.random() < .5 else P['patch_mid'], solid=.0008, grain='x', detail=1)
            S.setdefault('paper_patches', []).append(((x, -2.7236, z), (0., -1., 0.), .0004))


# ------------------------------------------------------------------ small bamboo chair by the door (VL05)
def bamboo_chair(P, R):
    """A low bamboo chair right of the door, turned a little towards the steps: four culm legs (the back pair runs up into the back),
    seat rails, lower stretchers, six split-bamboo seat slats and three back slats."""
    cx, cy, yaw = 1.36, -3.1, -.35
    ca, sa = math.cos(yaw), math.sin(yaw)
    W = lambda x, y, z: (cx + x * ca - y * sa, cy + x * sa + y * ca, FLOOR + z)
    SZ, rl, rr, HW, BT = .4, .019, .014, .2, .85
    yb = lambda z: .17 + .05 * z / BT                         # the back legs lean back
    for sx in (-1, 1):
        x = sx * HW
        pole('Chair_Leg', W(x, -.17, -.003), W(x, -.17, SZ - .009), rl + .001, rl, P['chair_bamboo'], node_gap=.3, seed=40 + sx, seg=8, **DET)
        pole('Chair_Leg', W(x, yb(0), -.003), W(x, yb(BT), BT), rl + .001, rl * .92, P['chair_bamboo'], node_gap=.3, seed=42 + sx, seg=8, **DET)
        rest('chair_leg', *W(x, -.17, 0)[:2], FLOOR); rest('chair_leg', *W(x, yb(0), 0)[:2], FLOOR)
    zf = SZ - .008 - rr                                        # front and back rails carry the slats
    pole('Chair_Rail', W(-HW, -.17, zf), W(HW, -.17, zf), rr, rr, P['chair_bamboo'], node_gap=.5, seed=44, seg=8, **DET)
    pole('Chair_Rail', W(-HW, yb(zf), zf), W(HW, yb(zf), zf), rr, rr, P['chair_bamboo'], node_gap=.5, seed=45, seg=8, **DET)
    zs = zf - .03                                              # side rails a little lower, so they do not cross the others
    for sx in (-1, 1):
        pole('Chair_Rail', W(sx * HW, -.17, zs), W(sx * HW, yb(zs), zs), rr, rr, P['chair_bamboo'], node_gap=.5, seed=46 + sx, seg=8, **DET)
        pole('Chair_Stretcher', W(sx * HW, -.17, .11), W(sx * HW, yb(.11), .11), rr * .9, rr * .9, P['chair_bamboo'], node_gap=.5, seed=48 + sx, seg=8, **DET)
    pole('Chair_Stretcher', W(-HW, -.17, .14), W(HW, -.17, .14), rr * .9, rr * .9, P['chair_bamboo'], node_gap=.5, seed=50, seg=8, **DET)
    for k in range(6):                                         # seat slats along the depth, 1 cm apart
        x = -.1675 + k * .067
        y0, y1 = -.197, yb(zf) + .012
        rbox('Chair_Seat_Slat', W(x, (y0 + y1) / 2, SZ - .004), (.057, y1 - y0, .008), P['chair_slat'], r=.003, div=.04, rot=(0, 0, yaw), **DET)
    for z in (.56, .82):                                       # back rails
        pole('Chair_Back_Rail', W(-HW, yb(z), z), W(HW, yb(z), z), rr, rr, P['chair_bamboo'], node_gap=.5, seed=int(z * 100), seg=8, **DET)
    lean = math.atan2(.05, BT)
    for x in (-.1, 0., .1):                                     # back slats in front of the rails, touching them
        zm = .69; y = yb(zm) - rr - .004
        rbox('Chair_Back_Slat', W(x, y, zm), (.05, .008, .33), P['chair_slat'], r=.003, div=.04, rot=(-lean, 0, yaw), **DET)
    S['chair'] = dict(centre=(cx, cy), yaw=yaw, seat_m=SZ, back_top_m=BT)


# ------------------------------------------------------------------ dried corn under the eave (VL05)
def _cob(V, F, T, d, L, Rk, seg=14, ring=.011):
    """One cob from its stalk end T along d: kernel rows (alternate vertices proud / sunk), staggered kernel rings, rounded tip."""
    d = Vector(d).normalized(); u = d.orthogonal().normalized(); v = d.cross(u)
    n = max(6, int(L / ring)); base = len(V); rings = []
    for i in range(n + 1):
        t = i / n
        r = Rk * (.78 + .22 * min(1., t / .08)) * (1 - .3 * t ** 3)
        if i == 0: r *= .55
        if i == n - 1: r *= .82
        if i == n: r *= .4
        rs = []
        for j in range(seg):
            a = (j + .5 * (i % 2)) * math.tau / seg
            k = 1.1 if j % 2 == 0 else .88                     # a kernel row, then the groove between rows
            if 0 < i < n: k *= .92 if i % 2 else 1.
            rs.append(len(V)); V.append(tuple(T + d * (L * t) + (u * math.cos(a) + v * math.sin(a)) * r * k))
        rings.append(rs)
    for A, B in zip(rings, rings[1:]):
        for j in range(seg):
            F.append((A[j], A[(j + 1) % seg], B[(j + 1) % seg], B[j]))
    for cap, end, sgn in ((rings[0], T - d * .004, 1), (rings[-1], T + d * (L + .006), -1)):
        c = len(V); V.append(tuple(end))
        for j in range(seg):
            F.append((cap[(j + 1) % seg], cap[j], c) if sgn > 0 else (cap[j], cap[(j + 1) % seg], c))
    return base


def corn_string(P, R):
    """Six bundles of three dried cobs, their husks pulled back and twisted together, each tied on a short cord to the porch
    header above the steps (header underside z 3.21). The lowest cob ends well above a person's head on the porch."""
    hz, hy = 3.21, -3.46
    V, F = [], []
    low = 9.; hooks = []
    for b, xb in enumerate((-.95, -.57, -.19, .19, .57, .95)):
        xb += R.uniform(-.03, .03)
        cord = R.uniform(.12, .2)
        K = Vector((xb, hy + R.uniform(-.015, .015), hz - cord))
        ncob = 3
        a0 = R.uniform(0, math.tau)
        for j in range(ncob):
            a = a0 + j * math.tau / ncob + R.uniform(-.2, .2)
            th = R.uniform(.3, .38)
            d = Vector((math.sin(th) * math.cos(a), math.sin(th) * math.sin(a), -math.cos(th)))
            hl = R.uniform(.09, .105); L = R.uniform(.2, .24); Rk = R.uniform(.027, .031)
            T = K + d * hl
            _cob(V, F, T, d, L, Rk)
            low = min(low, (T + d * (L + .006)).z - Rk)
            uu = d.orthogonal().normalized(); vv = d.cross(uu)
            for q in range(3):                                   # husks pulled back from the stalk end up to the knot
                aq = a0 + q * math.tau / 3 + j * math.tau / 9
                hq = Vector((math.cos(aq), math.sin(aq), 0.)); out = (hq - d * hq.dot(d)).normalized(); tan = d.cross(out).normalized()   # same world direction for every cob
                B = T + out * Rk * .62 + d * .006
                def fn(s, t, B=B, out=out, tan=tan):
                    if t <= .7:                                      # from the cob up to the knot
                        tt = t / .7
                        p = B.lerp(K + out * .014, tt) + out * (.018 * math.sin(math.pi * tt)) + d * (-.012 * math.sin(math.pi * tt))
                        wd = .042 * (1 - tt) + .008 * tt
                    else:                                            # through the tie and up as a loose tail
                        tt = (t - .7) / .3
                        p = K + out * (.014 + .012 * tt) + Vector((0, 0, .06 * tt)) + tan * (.006 * math.sin(tt * 3))
                        wd = .008 + .006 * tt
                    return tuple(p + tan * (s - .5) * wd + out * (.004 * math.sin(math.pi * s)))
                sheet('Corn_Husk', 2, 6, fn, P['husk'], solid=.0012, **DET)['both_sides'] = .004
        lathe('Corn_Tie', [(0., -.008), (.016, -.008), (.019, 0.), (.019, .014), (.016, .022), (0., .022)], tuple(K), P['twine'], seg=10, **DET)
        tube('Corn_Cord', [tuple(K + Vector((0, 0, .02))), tuple(Vector((xb + .004, K.y + .003, hz + .006)))], .0035, P['twine'], res=4, **DET)
        hooks.append((round(xb, 3), round(K.y, 3), round(hz, 3)))
    o = mesh('Dried_Corn', V, F, P['corn'], smooth=True, grain='z', **DET)
    import bmesh
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    S['corn'] = dict(bundles=6, lowest_z=round(low, 3), cords=hooks)


# ------------------------------------------------------------------ old bonsai left of the door (VL05)
def bonsai(P, R):
    """An old pine in a shallow oval stoneware pot on four small feet: a twisted trunk with a flared root, four branches ending in
    cloud-pruned foliage pads and a crown pad, moss on the soil. Sizes in pot units k (1 = the 0.25 m pot radius / 0.25)."""
    bx, by, k = -1.36, -3.0, 1.35
    o = Vector((bx, by, FLOOR + .032))
    for q in range(4):
        a = math.pi / 4 + q * math.pi / 2
        fx, fy = bx + math.cos(a) * .12 * k, by + math.sin(a) * .09 * k
        rbox('Bonsai_Pot_Foot', (fx, fy, FLOOR + .017), (.05, .042, .034), P['bonsai_pot'], r=.007, div=.02, **DET)
        rest('bonsai_pot_foot', fx, fy, FLOOR)
    prof = [(0., 0.), (.15, 0.), (.163, .012), (.17, .1), (.185, .108), (.185, .125), (.171, .125), (.162, .112), (.156, .1), (0., .1)]
    lathe('Bonsai_Pot', [(r * k, z * k) for r, z in prof], tuple(o), P['bonsai_pot'], seg=28, scale=(1, .78, 1), **DET)
    lathe('Bonsai_Moss', [(r * k, z * k) for r, z in [(.157, .099), (.13, .108), (.07, .114), (0., .116)]], tuple(o), P['moss'], seg=22, scale=(1, .78, 1), **DET)
    K = lambda p: o + Vector(p) * k
    pts = [(0, 0, .095), (.02, 0, .16), (.06, .01, .22), (.035, -.01, .3), (-.035, 0, .36), (-.055, .02, .42), (-.02, .03, .485)]
    tube('Bonsai_Trunk', [tuple(K(p)) for p in pts], .036 * k, P['bonsai_bark'], radii=[1.5, 1., .88, .72, .58, .46, .34], res=8, **DET)
    pads = [((.06, .01, .22), (.15, -.02, .25), (.2, -.03, .27), (.22, .17, .075)),
            ((-.035, 0, .36), (-.12, .01, .375), (-.17, .0, .395), (.2, .16, .07)),
            ((-.02, .03, .485), (-.025, .03, .5), (-.03, .03, .51), (.2, .16, .085)),
            ((.035, -.01, .3), (.07, .03, .35), (.09, .05, .385), (.13, .11, .06)),
            ((-.055, .02, .42), (-.04, -.05, .43), (-.02, -.08, .44), (.12, .1, .055))]
    for i, (p0, p1, p2, size) in enumerate(pads):
        if i != 2:
            tube('Bonsai_Branch', [tuple(K(p)) for p in (p0, p1, p2)], .013 * k, P['bonsai_bark'], radii=[1., .75, .55], res=6, **DET)
        c = K(p2) + Vector((0, 0, size[2] * k * .3))
        w, dd, h = (x * k for x in size); a = R.uniform(0, math.pi)
        ax = Vector((math.cos(a), math.sin(a), 0.))
        for j, (off, f, dz) in enumerate(((0., .62, 0.), (-.3, .48, -.22), (.32, .44, -.18))):
            cc = c + ax * (off * w) + Vector((0, 0, dz * h))
            rbox('Bonsai_Pad', tuple(cc), (w * f, dd * (f + .2), h * (1 if j == 0 else .8)), P['pine'], r=h * .42, amp=.012, freq=26.,
                 seed=60 + i * 3 + j, div=.024, rot=(0, 0, a + R.uniform(-.3, .3)), **DET)
    S['bonsai'] = dict(centre=(bx, by), top_m=round(.032 + (.51 + .085 * .8) * k, 3))
