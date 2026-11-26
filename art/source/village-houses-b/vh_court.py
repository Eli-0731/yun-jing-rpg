"""VH02 L-shaped courtyard house (work pack 2026-11-09 B-112h, batch A): two single-storey wings round a small yard.

Three-view: art/references/VH02/VH02-cand-1.png (AI, Codex image_gen; proportions from the work pack's written sizes, not the image).
Size limit 12 x 10 x 5.5 m. Origin: centre of the lot at ground level, front (the lane side, where the gate is) -Y.

Main wing across the back, the full width (ridge along x), on a 0.4 m stone plinth with an open walk under its front eave on four
columns; a side wing on the right coming forward to the lane (ridge along y, its gable to the front), on a lower plinth. The two roofs
meet in a valley: each roof drops the tiles, boards and eave parts that lie under the other one, and a tiled valley gutter covers the
line where they cross. The yard in the corner between them is packed earth, closed by a low wall (rubble stone base, lime plaster,
tile coping) with one small gate under its own little tiled roof; the gate leaves stand open against the wall, so the yard can be
walked into. A 5 x 4 m patch of the yard on the left is left empty for a vegetable plot (the plot itself is not part of this asset).
Walls: lime plaster over a rubble stone dado, timber posts and plates square-on (no diagonal braces), lattice windows with paper.
Shared with VL01-05 and VH01: the material set (vl_mats, the 'diligent' palette: kept up, little moss), the VL roof tiles and their
shared 1024 texture on the VH roof curve (vh_roof.py), the three-atlas scheme (Main, Stone, Wood) of the export pipeline.
"""
import math, random, re
import bmesh
from mathutils import Vector, Matrix
from ti_core import S, box, cyl, mesh, lathe, torus, socket, extrude_profile, xf, T, RZ, RX
from cr_parts import rbox, sheet, set_float, set_attr_list
import mk_mats as mm
import fr_parts as FP
import vl_mats
import vl_roof as RF
import vh_roof as VR
import vh_wood as vw

# ------------------------------------------------------------------ layout (metres, world; front -Y)
WT = .3                                 # wall thickness
MY, HX, HY = 2.8, 5.3, 1.5              # main wing: walls x -5.3..5.3, y 1.3..4.3
MF = MY - HY                            # main front wall line
PL_M, WTOP_M = .4, 3.0                  # main plinth top (= floor and walk), top of the wall plates
SX, SYC = 4.05, -1.15                   # side wing roof frame (ridge along y through x = SX)
SW0, SW1, SF = 2.8, 5.3, -4.3           # side wing walls: x 2.8..5.3, front gable wall y -4.3, back into the main wing at y 1.3
PL_S, WTOP_S = .25, 3.05
WALK_Y = -.05                           # front edge of the walk plinth
COL_Y = .25                             # eave columns
MAIN_ROOF = dict(z0=3.0, rise=1.9, depth_front=3.25, depth_back=2.15, xh=5.61, lift_eave=.15, lift_end=.03)
SIDE_ROOF = dict(z0=3.1, rise=1.35, depth_front=1.65, depth_back=1.65, xh=3.47, lift_eave=.12, lift_end=.06)
YW_Y, YW_X, YW_T, YW_H = -4.6, -5.7, .34, 1.35      # yard walls: front wall line, left wall line, thickness, top of the plaster
YARD = (-5.53, SW0 - .15, -4.43, WALK_Y)     # packed-earth yard inside the walls
PATCH = (-5.5, -.5, -4.4, -.4)          # 5.0 x 4.0 m left empty for the vegetable plot
GATE_X, GATE_W = .8, .9                 # gate centre and clear width
MAIN_DOOR_X = .6
COLS = (-5.15, -2.5, .0, SW0 - .3)        # eave columns along the walk

# wall specs in world frames: ((x, y), angle, length, openings (cx, w, sill, head, kind) in wall-local x, posts at ends (a, b), floor, top)
WALLS = {
    'M_Front': (((-5.3 + SW0) / 2, MF), 0., SW0 + 5.3, [(-3.7 - (-5.3 + SW0) / 2, .9, 1.3, 2.25, 'window'), (-1.4 - (-5.3 + SW0) / 2, .9, 1.3, 2.25, 'window'),
                                                       (MAIN_DOOR_X - (-5.3 + SW0) / 2, 1.2, PL_M, 2.45, 'door')], (1, 0), PL_M, WTOP_M),
    'M_Rear': ((0., 4.3), math.pi, 10.6, [(-2.6, .8, 1.4, 2.2, 'window'), (2.6, .8, 1.4, 2.2, 'window')], (1, 1), PL_M, WTOP_M),
    'M_Left': ((-5.3, MY), -math.pi / 2, 2 * HY - 2 * WT - .02, [(0., .7, 1.45, 2.15, 'window')], (0, 0), PL_M, WTOP_M),
    'M_Right': ((5.3, MY), math.pi / 2, 2 * HY - 2 * WT - .02, [(0., .7, 1.45, 2.15, 'window')], (0, 0), PL_M, WTOP_M),
    'S_West': ((SW0, (SF + MF) / 2), -math.pi / 2, MF - SF - .02, [(.25, 1.0, PL_S, 2.25, 'door2'), (1.85, .8, 1.25, 2.05, 'window'), (-1.5, .8, 1.25, 2.05, 'window')], (1, 1), PL_S, WTOP_S),
    'S_East': ((SW1, (SF + MF) / 2), math.pi / 2, MF - SF - .02, [(-.35, .7, 1.35, 2.05, 'window')], (1, 1), PL_S, WTOP_S),
    'S_Front': ((SX, SF), 0., SW1 - SW0 - 2 * WT - .02, [(0., .6, 1.35, 1.95, 'window')], (0, 0), PL_S, WTOP_S),
}

R_ = {}                                  # the two roofs: curve, depths, frame (filled in build)


def palette():
    P = vl_mats.palette('diligent')
    vw.apply(P, 'diligent')                                  # weathered timber, plank doors, split firewood (vh_wood.py)
    P['roof'] = RF.roof_material()
    cm = __import__('cr_mats')
    P['wall_stone'] = P['stone'] + [cm.stone('Dado_Stone_Warm', light=(.2, .19, .165), dark=(.085, .08, .07), ochre=(.24, .2, .14), moss=.5, lichen=.5, crack=.5)]
    P['yard'] = cm.packed_earth('Yard_Earth', dark=(.09, .07, .045), light=(.26, .19, .115), moss=.15)
    # woven props: split-bamboo weave read from each part's own 'wuv' coordinates, bamboo hoops, hemp lashing
    P['weave_tray'] = mm.weave('Tray_Weave', (.41, .3, .145), (.105, .072, .036), reed=.012, block=.036, green_cast=.18, wobble=.006, strip_var=.42)
    P['weave_basket'] = mm.weave('Basket_Weave', (.34, .24, .115), (.13, .088, .042), reed=.016, block=.03, plain=True, green_cast=.04, wobble=.004)
    P['hoop'] = mm.bamboo('Split_Bamboo_Hoop', green=(.09, .085, .05), straw=(.3, .24, .14))
    P['twine'] = mm.hemp('Hemp_Twine', (.2, .14, .065), twist=220.0)
    return P


# ------------------------------------------------------------------ the two roof surfaces in world coordinates
def _local(name, wx, wy):
    r = R_[name]
    if name == 'main': return wx, wy - MY
    return wy - SYC, SX - wx                  # side frame = T(SX, SYC) @ RZ(90 deg): local x along world y, local -y towards +x (east)


def roof_curve(name, wx, wy):
    """The roof's tile curve at (wx, wy), or None outside its plan."""
    r = R_[name]; lx, ly = _local(name, wx, wy)
    D = r['depth'][-1 if ly < 0 else 1]
    if abs(lx) > r['xedge'] or abs(ly) > D + r.get('reach', 0.): return None      # side roof: reach 0.12 m past its eaves, so main eave parts sticking out under its eave edge go too
    return r['z'](lx, abs(ly) / D)


def under_world(wx, wy):
    """Underside of the roof boards actually there: where both roofs pass over a point the higher one is kept (the lower one is cut)."""
    zs = [z for z in (roof_curve('main', wx, wy), roof_curve('side', wx, wy)) if z is not None]
    return max(zs) + RF.UNDER_TOP - RF.UNDER_T if zs else None


def _to_world(name, lx, ly):
    if name == 'main': return lx, ly + MY
    return SX - ly, SYC + lx


def under_roof(name, wx, wy):
    """Underside of the boards of one roof at (wx, wy)."""
    z = roof_curve(name, wx, wy)
    return None if z is None else z + RF.UNDER_TOP - RF.UNDER_T


def under_other(name, lx, ly, z, margin=0.):
    """True when the point of roof `name` at local (lx, ly) and height z lies under the other roof and is cut away. The main roof is cut
    wherever it passes under the side roof. The side roof runs on under the main roof's eave overhang (it tucks under the main eave, as
    on a real house, so no hole shows from the side) and is cut only inside the main wing's walls."""
    other = 'side' if name == 'main' else 'main'
    wx, wy = _to_world(name, lx, ly)
    if name == 'side' and wy < MF - .05: return False
    zo = roof_curve(other, wx, wy)
    return zo is not None and z + margin < zo


def roof(P, name, cell):
    r = R_[name]
    def hole(side, x, k):
        D = r['depth'][side]
        return all(under_other(name, x + dx, side * t * D, r['z'](x + dx, t), .03) for t in RF.course_t(k) for dx in (-.12, .12))
    def cut(side, x, t):
        D = r['depth'][side]
        return under_other(name, x, side * t * D, r['z'](x, t), .02)
    n0 = len(S['parts'])
    for side in (-1, 1):
        RF.tiles(P, side, hole=hole, cell=cell)
        VR.underlay(P, side, cut=cut)
        VR.eave_caps(P, side)
    if name == 'main': VR.ridge(P)
    else: side_ridge(P)
    VR.barge_boards(P); VR.eave_rafters(P)
    # eave parts, barge boards and ridge ends wholly under the other roof go (inside the side wing, or hanging in the walk's corner)
    import bpy
    M = S['M'][-1]
    gone = []
    for o in S['parts'][n0:]:
        if o.name.startswith('Roof_Tiles') or o.name.startswith('Roof_Boards'): continue
        cs = [o.matrix_world @ Vector(c) for c in o.bound_box]
        if all((lambda zo: zo is not None and c.z + .01 < zo)(roof_curve('side' if name == 'main' else 'main', c.x, c.y)) for c in cs):
            gone.append(o)
    for o in gone:
        S['parts'].remove(o); bpy.data.objects.remove(o, do_unlink=True)
    S[f'{name}_roof_parts_dropped'] = len(gone)


def side_ridge(P):
    """The side wing's ridge: curled at the gable (front) end only; the back end runs on into the main roof's slope and stops inside it."""
    x0 = -(abs(VR.CFG['x0']) + .05)
    x1 = 2.6 - SYC                                # world y 2.6: the ridge body top is under the main roof's tiles there
    import numpy as np
    xs = np.linspace(x0, x1, 41); zr = lambda x: VR.z(x, 0.)
    RF.sweep_box('Ridge_Body', [(x, 0., zr(x) + .19) for x in xs], .3, .22, P['tile'], up=(0, 0, 1), grain='x', group='Stone')
    V, F = [], []; seg = 8
    for x in xs:
        for q in range(seg + 1):
            a = math.pi * q / seg; V.append((x, .085 * math.cos(a), zr(x) + .19 + .075 * math.sin(a)))
    for k in range(len(xs) - 1):
        for q in range(seg):
            a = k * (seg + 1) + q; F.append((a, a + seg + 1, a + seg + 2, a + 1))
    mesh('Ridge_Cap', V, F, P['tile'], smooth=True, grain='x', solid=.012, group='Stone')
    sx = -1; x = x0
    pts = [(x - sx * .3, 0., zr(x) + .19), (x - sx * .08, 0., zr(x) + .2), (x + sx * .05, 0., zr(x) + .26), (x + sx * .1, 0., zr(x) + .33)]
    RF.sweep_box('Ridge_Curl_-1', pts, .22, .16, P['tile'], grain='x', group='Stone')
    cyl('Ridge_End_Cap', (x - sx * .02, 0., zr(x) + .19), .095, .02, P['tile'], axis='x', verts=14, group='Stone')


def valley(P):
    """Where the roofs cross: a tiled gutter along each crossing line (main eave line up to where the side ridge enters the main slope)."""
    out = []
    for s, nm in ((1, 'West'), (-1, 'East')):     # side-roof slope +1 faces the yard (-x), -1 the outside (+x)
        pts = []
        wy = MY - MAIN_ROOF['depth_front'] - .02
        while wy < 2.6:
            lo, hi = 0., R_['side']['depth'][s]
            f = lambda ly: roof_curve('side', SX - s * ly, wy) - (roof_curve('main', SX - s * ly, wy) or -9)
            if f(lo) < 0: break
            if f(hi) > 0: wy += .1; continue
            for _ in range(40):
                m = (lo + hi) / 2
                if f(m) > 0: lo = m
                else: hi = m
            wx = SX - s * lo
            pts.append((wx, wy, roof_curve('side', wx, wy) + .055))
            wy += .1
        if len(pts) > 2:
            RF.sweep_box(f'Valley_Gutter_{nm}', pts, .34, .09, P['tile'], up=(0, 0, 1), grain='y', group='Stone')
            for a, b in zip(pts[::2], pts[2::2]):
                along('Valley_Roll', (a[0], a[1], a[2] + .045), (b[0], b[1], b[2] + .045), .05, P['tile'], verts=8, group='Stone')
        out.append(len(pts))
    S['valley_points'] = out


def along(name, p0, p1, r, mat, **kw):
    """Cylinder from p0 to p1 (its axis along the segment)."""
    a, b = Vector(p0), Vector(p1); d = b - a
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_euler()
    return cyl(name, tuple((a + b) / 2), r, d.length, mat, rot=tuple(rot), **kw)


# ------------------------------------------------------------------ walls (from ps_station / vh_house: plaster slab with reveals, rubble dado)
def wframe(name):
    (wx, wy), a, L, ops, posts, pl, top = WALLS[name]
    return T(wx, wy, 0) @ RZ(a), L, ops, posts, pl, top


def slab(name, L, ops, z0, z1, y0, y1, mat_out, mat_in, uv_in=.12):
    xa, xb = -L / 2, L / 2
    xs = {xa, xb}; zs = {z0, z1}
    for cx, w, sill, head, kind in ops:
        xs |= {cx - w / 2, cx + w / 2}; zs |= {max(z0, sill), min(z1, head)}
    xs, zs = sorted(xs), sorted(zs)
    opening = lambda x, z: any(cx - w / 2 < x < cx + w / 2 and sill < z < head for cx, w, sill, head, kind in ops)
    kept = {(i, j) for i in range(len(xs) - 1) for j in range(len(zs) - 1) if not opening((xs[i] + xs[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2)}
    idx = {}; V = []
    def vid(s, i, j):
        if (s, i, j) not in idx: idx[(s, i, j)] = len(V); V.append((xs[i], y0 if s == 0 else y1, zs[j]))
        return idx[(s, i, j)]
    F, W, MI = [], [], []
    for i, j in kept:
        F.append((vid(0, i, j), vid(0, i + 1, j), vid(0, i + 1, j + 1), vid(0, i, j + 1))); W.append(1.); MI.append(0)
        F.append((vid(1, i, j), vid(1, i, j + 1), vid(1, i + 1, j + 1), vid(1, i + 1, j))); W.append(uv_in); MI.append(1)
        for (di, dj), (a, b) in (((0, -1), ((i, j), (i + 1, j))), ((1, 0), ((i + 1, j), (i + 1, j + 1))), ((0, 1), ((i + 1, j + 1), (i, j + 1))), ((-1, 0), ((i, j + 1), (i, j)))):
            if (i + di, j + dj) in kept: continue
            F.append((vid(0, *b), vid(0, *a), vid(1, *a), vid(1, *b))); W.append(.5); MI.append(0)
    o = mesh(name, V, F, mat_out, grain='x')
    o.data.materials.append(mat_in)
    o.data.polygons.foreach_set('material_index', MI)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    at = o.data.attributes.new('uvw', 'FLOAT', 'FACE'); at.data.foreach_set('value', W)
    return o


def walls(P, R):
    for wname in WALLS:
        M, L, ops, posts, pl, top = wframe(wname)
        with xf(M):
            slab(f'Wall_{wname}', L - .02, ops, pl - .02, top - .14, .0, WT, P['plaster'], P['plaster_in'])
            box(f'Wall_Plate_{wname}', (0., .1, top - .07), (L + (.14 if any(posts) else -.2), .26, .14), P['timber'], bevel=.012, seg=2, group='Wood', grain='x')
            box(f'Wall_Sill_Beam_{wname}', (0., -.06, pl + .05), (L - .02, .08, .1), P['timber'], bevel=.01, seg=2, group='Wood', grain='x', uvw=.6)
            blocked = [(cx - w / 2 - .08, cx + w / 2 + .08) for cx, w, sill, head, kind in ops if kind.startswith('door')]
            z = pl; zs = []
            while z < pl + .68:
                h = R.uniform(.2, .27); zs.append((z, min(z + h, pl + .72))); z += h
            for c, (za, zb) in enumerate(zs):
                x = -L / 2 + .12 + (.16 if c % 2 else 0.)
                while x < L / 2 - .14:
                    Ls = min(R.uniform(.32, .62), L / 2 - .12 - x)
                    if Ls < .14: break
                    if not any(a < x + Ls / 2 < b for a, b in blocked):
                        rbox(f'Dado_Stone_{wname}', (x + Ls / 2, -.04, (za + zb) / 2), (Ls - .02, .12, zb - za - .02), R.choice(P['wall_stone']),
                             r=.025, amp=.008, freq=2.4, hew=2, chips=1, seed=int(x * 50 + c * 7 + len(wname)), div=.3, group='Stone')
                    x += Ls
            for end, on in zip((-1, 1), posts):
                if on:
                    box(f'Wall_Post_{wname}', (end * (L / 2 - .1), -.03, (pl - .02 + top) / 2), (.22, .2, top - pl + .02), P['timber'], bevel=.014, seg=2, group='Wood', grain='z')
            for cx, w, sill, head, kind in ops:
                box(f'Lintel_{wname}', (cx, -.03, head + .06), (w + .3, .16, .16), P['timber'], bevel=.01, seg=2, group='Wood', grain='x')
                if kind == 'window': window(P, R, f'Window_{wname}_{cx:+.1f}', cx, sill, w, head - sill)
                elif kind == 'door': door(P, cx, w, head, pl, ajar=True)
                else: door(P, cx, w, head, pl, ajar=False)
            if any(posts) and L > 5:
                box(f'Wall_Mid_Rail_{wname}', (0., -.02, top - .44), (L - .2, .12, .1), P['timber'], bevel=.01, seg=2, group='Wood', grain='x')


def window(P, R, name, cx, sill, w, h):
    zc = sill + h / 2
    for x in (cx - w / 2 - .035, cx + w / 2 + .035):
        box(name + '_Jamb', (x, -.02, zc), (.08, .14, h + .08), P['timber'], bevel=.01, seg=2, group='Wood', grain='z')
    box(name + '_Sill', (cx, -.04, sill - .03), (w + .2, .18, .07), P['timber'], bevel=.01, seg=2, group='Wood', grain='x')
    n = max(4, int(round(w / .13)))
    for j in range(1, n):
        box(name + '_Bar', (cx - w / 2 + j * w / n, -.02, zc), (.025, .04, h - .02), P['timber'], bevel=0., group='Wood', grain='z')
    for j in (1, 2):
        box(name + '_Bar_Rail', (cx, -.02, sill + j * h / 3), (w + .02, .035, .025), P['timber'], bevel=0., group='Wood', grain='x')
    sheet(name + '_Paper', 6, 6, lambda u, v: (cx - w / 2 + w * u, .03, sill + h * v), P['paper'], solid=.003, grain='x')


def door(P, cx, w, head, pl, ajar):
    """Plank double door; ajar: the right leaf open about 30 degrees (a gap too narrow to walk through), the floor inside seen through it."""
    for x in (cx - w / 2 - .055, cx + w / 2 + .055):
        box('Door_Jamb', (x, -.02, (pl - .01 + head) / 2), (.12, .18, head - pl + .01), P['timber'], bevel=.012, seg=2, group='Wood', grain='z')
    rbox('Door_Threshold', (cx, .05, pl + .03), (w + .1, .2, .06), P['stone'][1], r=.01, amp=.002, freq=3., hew=0, seed=7, div=.25, flat='zZ', group='Stone')
    lw = w / 2 - .01; zc = (pl + .06 + head) / 2; hh = head - pl - .08
    rnd = random.Random(int(cx * 1000) + 17)
    # separate boards (vh_wood.plank_leaf): battens inside, nail heads outside over each batten
    vw.plank_leaf('Door_Leaf', cx - w / 4, .1, zc - hh / 2, lw, hh, .05, P['door'], rnd, battens=(pl + .4, head - .4), nails=P['iron'], uvw=1.4)
    a = math.radians(30 if ajar else 0)
    with xf(T(cx + w / 2, .1, 0.) @ RZ(a)):
        vw.plank_leaf('Door_Leaf_Right', -lw / 2, 0., zc - hh / 2, lw, hh, .05, P['door'], rnd, battens=(pl + .4, head - .4), nails=P['iron'], uvw=1.4)
    # iron pull rings hanging from round plates
    zr = 1.25 + pl * .5
    def ring(x, y):
        cyl('Door_Ring_Plate', (x, y, zr), .034, .01, P['iron'], axis='y', verts=12, bevel=.002)
        torus('Door_Ring', (x, y - .012, zr - .036), .045, .0065, P['iron'], rot=(math.pi / 2, 0, 0), major=16, minor=6)
    ring(cx - .07, .07)
    with xf(T(cx + w / 2, .1, 0.) @ RZ(a)):
        ring(-w / 2 + .07, -.03)
    if ajar:
        box('Room_Floor', (cx, .925, pl - .015), (2.4, 1.65, .02), P['earth'], bevel=0., uvw=.15)
        box('Room_Back', (cx, 1.75, (pl + head) / 2 + .2), (2.4, .05, head - pl + .4), P['plaster_in'], bevel=0., uvw=.15)


def infill(P, name, p0, p1, z0, mat, n=16, inset=.08, t=.1, roof='main'):
    """Board or plaster infill from z0 up to the roof boards along the wall line p0 -> p1 (world), inset into the wall from its outer face."""
    (ax, ay), (bx, by) = p0, p1
    L = math.hypot(bx - ax, by - ay); ux, uy = (bx - ax) / L, (by - ay) / L; nx, ny = uy, -ux     # n: the outside (right of p0 -> p1)
    V, F = [], []
    for q in range(n + 1):
        x, y = ax + (bx - ax) * q / n, ay + (by - ay) * q / n
        zt = under_roof(roof, x, y)
        zt = (zt if zt is not None else z0) + .005
        for s in (inset - t / 2, inset + t / 2):
            V.append((x - nx * s, y - ny * s, z0 - .01)); V.append((x - nx * s, y - ny * s, max(zt, z0 + .02)))
    for q in range(n):
        a = q * 4; b = a + 4
        F += [(a, b, b + 1, a + 1), (a + 2, a + 3, b + 3, b + 2), (a + 1, b + 1, b + 3, a + 3), (a, a + 2, b + 2, b)]
    F += [(0, 1, 3, 2), (n * 4, n * 4 + 2, n * 4 + 3, n * 4 + 1)]
    o = mesh(name, V, F, mat, group='Wood' if mat is P['timber'] else 'Main', grain='x', uvw=.5)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    return o


def roof_fill(P):
    """Boards from the wall plates up to the roof along the eave walls; plaster gables on the gable walls (the outer face is p0 -> p1 right side)."""
    infill(P, 'Eave_Infill_Main_Front', (-5.24, MF), (SW0, MF), WTOP_M, P['timber'])
    infill(P, 'Eave_Infill_Main_Rear', (5.24, 4.3), (-5.24, 4.3), WTOP_M, P['timber'])
    infill(P, 'Eave_Infill_Side_West', (SW0, MF), (SW0, SF + .1), WTOP_S, P['timber'], n=26, roof='side')
    infill(P, 'Eave_Infill_Side_East', (SW1, SF + .1), (SW1, MF), WTOP_S, P['timber'], n=26, roof='side')
    infill(P, 'Gable_Main_Left', (-5.3, 4.3), (-5.3, MF), WTOP_M - .012, P['plaster'], n=24, t=.16, inset=.1)
    infill(P, 'Gable_Main_Right', (5.3, MF), (5.3, 4.3), WTOP_M - .012, P['plaster'], n=24, t=.16, inset=.1)
    infill(P, 'Gable_Side_Front', (SW0, SF), (SW1, SF), WTOP_S - .012, P['plaster'], n=24, t=.16, roof='side', inset=.1)
    # king posts and rakes on the three gables
    for (x, y), ax in (((-5.3 - .07, MY), 'y'), ((5.3 + .07, MY), 'y'), ((SX, SF - .07), 'x')):
        zk = under_roof('main' if ax == 'y' else 'side', x, y) - .1; zb = WTOP_M if ax == 'y' else WTOP_S
        box('Gable_King_Post', (x, y, (zb + zk) / 2), (.08, .16, zk - zb) if ax == 'y' else (.16, .08, zk - zb), P['timber'], bevel=.01, seg=2, group='Wood', grain='z')
    for x in (-5.3 - .06, 5.3 + .06):
        RF.sweep_box('Gable_Rake', [(x, y, under_world(x, y) - .001) for y in [MF + 2 * HY * j / 16 for j in range(17)]], .16, .14, P['timber'], group='Wood', grain='y')
    RF.sweep_box('Gable_Rake', [(x, SF - .06, under_roof('side', x, SF - .06) - .001) for x in [SW0 + (SW1 - SW0) * j / 16 for j in range(17)]], .16, .14, P['timber'], group='Wood', grain='x')


# ------------------------------------------------------------------ plinths, walk, steps
def plinth_rect(P, R, name, x0, x1, y0, y1, h, sides):
    box(name + '_Core', ((x0 + x1) / 2, (y0 + y1) / 2, h / 2 - .02), (x1 - x0 - .12, y1 - y0 - .12, h - .04), P['mortar'], bevel=0., uvw=.12)
    k = [0]
    def run(a, b, fixed, along_x):
        x = a
        while x < b - .05:
            L = min(R.uniform(.6, 1.0), b - x)
            if b - x - L < .3: L = b - x
            c = x + L / 2
            rbox(name + '_Stone', (c, fixed, h / 2) if along_x else (fixed, c, h / 2), (L - .015, .28, h) if along_x else (.28, L - .015, h),
                 P['stone'][k[0] % 2], r=.025, amp=.006, freq=2.5, hew=1, chips=1, seed=k[0] + len(name) * 17, div=.25, flat='Z', group='Stone')
            k[0] += 1; x += L
    if 'F' in sides: run(x0, x1, y0 + .14, True)
    if 'B' in sides: run(x0, x1, y1 - .14, True)
    ya, yb = y0 + (.28 if 'F' in sides else 0.), y1 - (.28 if 'B' in sides else 0.)
    if 'L' in sides: run(ya, yb, x0 + .14, False)
    if 'R' in sides: run(ya, yb, x1 - .14, False)


def plinths(P, R):
    plinth_rect(P, R, 'Main_Plinth', -5.45, 5.45, MF - .15, 4.45, PL_M, 'BLR')
    plinth_rect(P, R, 'Walk_Plinth', -5.45, SW0 - .15, WALK_Y, MF - .15, PL_M, 'FL')
    plinth_rect(P, R, 'Side_Plinth', SW0 - .15, SW1 + .15, SF - .15, MF - .15, PL_S, 'FLR')
    # the walk: big flat slabs between the edge stones and the wall
    x = -5.45 + .28
    while x < SW0 - .2:
        L = min(R.uniform(.7, 1.1), SW0 - .15 - x)
        rbox('Walk_Slab', (x + L / 2, (WALK_Y + .28 + MF) / 2, PL_M - .03), (L - .02, MF - WALK_Y - .28 - .02, .06), P['stone'][R.randrange(2)],
             r=.015, amp=.004, freq=3., hew=1, chips=1, seed=200 + int(x * 10), div=.25, flat='zZ', group='Stone')
        x += L
    for j in range(3):          # steps 0.133 m, 0.3 m treads, down into the yard in front of the door
        h = PL_M * (j + 1) / 3
        rbox('Walk_Step', (MAIN_DOOR_X, WALK_Y - .3 * (3 - j) + .15, h / 2), (1.7 - j * .1, .32, h), P['stone'][j % 2], r=.02, amp=.004, freq=3., hew=1, chips=1,
             seed=300 + j, div=.25, flat='zZ', group='Stone')
    # one step stone at the side wing's door
    rbox('Side_Door_Step', (SW0 - .45, (SF + MF) / 2 - .25, .06), (.5, 1.1, .12), P['stone'][0], r=.02, amp=.004, freq=3., hew=1, chips=1, seed=330, div=.25, flat='zZ', group='Stone')


def columns(P):
    """Four eave columns on the walk, the purlin they carry and ties back to the wall."""
    xs = COLS
    for x in xs:
        top = under_world(x, COL_Y) - .17
        rbox('Column_Base', (x, COL_Y, PL_M + .09), (.34, .34, .18), P['stone'][1], r=.03, amp=.004, freq=3., hew=1, chips=1, seed=int(x * 100) % 97, div=.25, flat='z', group='Stone')
        cyl('Column', (x, COL_Y, (PL_M + .18 + top) / 2), .1, top - PL_M - .18, P['timber'], verts=12, group='Wood', grain='z')
        RF.sweep_box('Eave_Tie', [(x, COL_Y, under_world(x, COL_Y) - .2), (x, MF + .1, under_world(x, MF + .1) - .2)], .1, .12, P['timber'], group='Wood', grain='y')
    pts = [(x, COL_Y, under_world(x, COL_Y) - .002) for x in [-5.45 + (SW0 - .02 + 5.45) * i / 20 for i in range(21)]]
    RF.sweep_box('Eave_Purlin', pts, .17, .17, P['timber'], group='Wood', grain='x')


# ------------------------------------------------------------------ yard, yard walls, gate
def yard(P, R):
    x0, x1, y0, y1 = YARD
    box('Yard_Earth', ((x0 + x1) / 2, (y0 + y1) / 2, .01), (x1 - x0, y1 - y0, .02), P['yard'], bevel=0., uvw=.35)
    # a trodden path from the gate to the steps, a few flat stones in it
    for i, (fx, fy) in enumerate(((GATE_X, -4.2), (GATE_X - .05, -3.55), (GATE_X - .1, -2.9), (GATE_X - .05, -2.25), (MAIN_DOOR_X, -1.6))):
        rbox('Path_Stone', (fx + R.uniform(-.05, .05), fy, .035), (R.uniform(.42, .55), R.uniform(.34, .44), .05), P['stone'][i % 2], r=.02, amp=.004, freq=3.,
             hew=1, chips=1, seed=400 + i, div=.25, flat='zZ', rot=(0, 0, R.uniform(-.2, .2)), group='Stone')


def yard_wall_run(P, R, name, a, b, along_x, fixed, gaps=()):
    """Straight run of yard wall from a to b (world) on the line `fixed`: plaster core, rubble base on both faces, tile coping."""
    c = (a + b) / 2; L = b - a
    pos = lambda u, v, z: (u, v, z) if along_x else (v, u, z)
    size = lambda su, sv, sz: (su, sv, sz) if along_x else (sv, su, sz)
    segs = []; s = a
    for g0, g1 in sorted(gaps):
        segs.append((s, g0)); s = g1
    segs.append((s, b))
    for u0, u1 in segs:
        box(f'{name}_Core', pos((u0 + u1) / 2, fixed, YW_H / 2), size(u1 - u0, YW_T - .08, YW_H), P['plaster'], bevel=.01, seg=2, grain='x')
        for face in (-1, 1):
            z = 0.; zs = []
            while z < .62:
                h = R.uniform(.2, .26); zs.append((z, min(z + h, .7))); z += h
            for ci, (za, zb) in enumerate(zs):
                u = u0 + (.18 if ci % 2 else 0.)
                if ci % 2:
                    rbox(f'{name}_Stone', pos(u0 + .09, fixed + face * (YW_T / 2 - .06), (za + zb) / 2), size(.16, .14, zb - za - .02), R.choice(P['wall_stone']),
                         r=.025, amp=.008, freq=2.4, hew=2, chips=1, seed=int(u0 * 31 + ci + face * 5), div=.3, group='Stone')
                while u < u1 - .1:
                    Ls = min(R.uniform(.34, .7), u1 - u)
                    if u1 - u - Ls < .12: Ls = u1 - u
                    rbox(f'{name}_Stone', pos(u + Ls / 2, fixed + face * (YW_T / 2 - .06), (za + zb) / 2), size(Ls - .02, .14, zb - za - .02), R.choice(P['wall_stone']),
                         r=.025, amp=.008, freq=2.4, hew=2, chips=1, seed=int(u * 50 + ci * 7 + face * 3 + len(name)), div=.3, group='Stone')
                    u += Ls
        # coping: a low two-slope tile cap with a round ridge tile
        prof = [(-.22, 0.), (.22, 0.), (.22, .04), (0., .14), (-.22, .04)]
        L1 = u1 - u0
        if along_x:
            extrude_profile(f'{name}_Coping', [(p[0], p[1]) for p in prof], L1, P['tile'], plane='yz', p=((u0 + u1) / 2, fixed, YW_H), bevel=.004, group='Stone', grain='x')
        else:
            extrude_profile(f'{name}_Coping', [(p[0], p[1]) for p in prof], L1, P['tile'], plane='xz', p=(fixed, (u0 + u1) / 2, YW_H), bevel=.004, group='Stone', grain='y')
        cyl(f'{name}_Coping_Ridge', pos((u0 + u1) / 2, fixed, YW_H + .14), .05, L1 + .02, P['tile'], axis='x' if along_x else 'y', verts=10, group='Stone')


def yard_walls(P, R):
    g0, g1 = GATE_X - GATE_W / 2 - .12, GATE_X + GATE_W / 2 + .12
    yard_wall_run(P, R, 'Yard_Wall_Front', YW_X - YW_T / 2, SW0 - .15, True, YW_Y, gaps=[(g0, g1)])
    yard_wall_run(P, R, 'Yard_Wall_Left', YW_Y + YW_T / 2, MF + .1, False, YW_X)


def gate(P, R):
    """Small gate: two posts on stone bases, a lintel and a little two-slope tiled roof; plank leaves standing open against the wall inside."""
    xa, xb = GATE_X - GATE_W / 2 - .06, GATE_X + GATE_W / 2 + .06
    for x in (xa, xb):
        rbox('Gate_Post_Base', (x, YW_Y, .1), (.3, .4, .2), P['stone'][1], r=.02, amp=.004, freq=3., hew=1, chips=1, seed=int(x * 10) + 50, div=.25, flat='zZ', group='Stone')
        box('Gate_Post', (x, YW_Y, 1.15), (.14, .16, 1.9), P['timber'], bevel=.012, seg=2, group='Wood', grain='z')
    rbox('Gate_Sill', (GATE_X, YW_Y, .03), (GATE_W, .3, .06), P['stone'][0], r=.01, amp=.003, freq=3., hew=0, seed=61, div=.25, flat='zZ', group='Stone')
    box('Gate_Lintel', (GATE_X, YW_Y, 2.14), (GATE_W + .5, .18, .16), P['timber'], bevel=.012, seg=2, group='Wood', grain='x')
    box('Gate_Head_Board', (GATE_X, YW_Y, 2.3), (GATE_W + .3, .1, .2), P['timber'], bevel=.01, seg=2, group='Wood', grain='x')
    # little roof: ridge along x, slopes to the lane and to the yard, rolls down each slope
    w, d, z0, rise = GATE_W + 1.0, .34, 2.42, .26
    prof = [(-d - .04, z0 - .02), (-d - .04, z0 + .04), (0., z0 + rise), (d + .04, z0 + .04), (d + .04, z0 - .02), (0., z0 + rise - .1)]
    extrude_profile('Gate_Roof', prof, w, P['tile'], plane='yz', p=(GATE_X, YW_Y, 0.), bevel=.004, group='Stone', grain='y')
    n = int(w / .2)
    for i in range(n + 1):
        x = GATE_X - w / 2 + .05 + (w - .1) * i / n
        for s in (-1, 1):
            along('Gate_Roof_Roll', (x, YW_Y + s * .03, z0 + rise + .005), (x, YW_Y + s * (d + .03), z0 + .075), .035, P['tile'], verts=8, detail=1, group='Stone')
    cyl('Gate_Roof_Ridge', (GATE_X, YW_Y, z0 + rise + .03), .06, w + .1, P['tile'], axis='x', verts=10, group='Stone')
    # leaves open: swung in, standing against the inside face of the wall
    lw = GATE_W / 2 + .02
    rnd = random.Random(4470)
    for side, hx in ((-1, xa + .08), (1, xb - .08)):
        with xf(T(hx, YW_Y + .12, 0.) @ RZ(side * math.radians(-82))):
            vw.plank_leaf('Gate_Leaf', side * lw / 2, .03, .15, lw, 1.7, .045, P['door'], rnd, battens=(.45, 1.55), nails=P['iron'], uvw=1.0)


# ------------------------------------------------------------------ lived-in props and growth (Detail_Small where it can go)
PROP_UVW = 5.0          # woven props get ~2.2x the house's texel density, so the weave survives the bake


def _lash(name, R, z, n, P, r=.016, wraps=2, a0=.3):
    """Hemp lashing round a rim at radius R: n bindings of a few turns, each ring's axis along the rim."""
    for k in range(n):
        a = a0 + k / n * math.tau
        for w in range(wraps):
            aa = a + (w - (wraps - 1) / 2) * .011 / R
            torus(name, (R * math.cos(aa), R * math.sin(aa), z), r, .0024, P['twine'], rot=(math.pi / 2, 0, aa), major=12, minor=4,
                  detail=1, grain=(-math.sin(aa), math.cos(aa), 0), uvw=PROP_UVW)


def bamboo_tray(P, p, R=.42, tilt=math.radians(76)):
    """Round split-bamboo tray (a shallow dish with a low wall), two bamboo hoops lashed with hemp, crossed braces underneath.
    Built flat with its face up, then stood on its rim leaning back (tilt about x)."""
    with xf(T(*p) @ RX(tilt)):
        prof = [(0., .007), (.13, .009), (.26, .013), (R - .045, .018), (R - .035, .019), (R - .03, .02), (R - .02, .044), (R - .012, .046), (R - .01, .02),
                (R - .02, .006), (R - .03, .004), (R - .04, .003), (.26, 0.), (.13, -.001), (0., -.001)]
        prof = prof[::-1]   # bottom centre first, like the other lathes: faces wind outward (inward faces read as hidden and lost their texels)
        o = lathe('Bamboo_Tray', prof, (0., 0., 0.), P['weave_tray'], seg=64, detail=1, grain='z', uvw=PROP_UVW)
        k = 1 / math.sqrt(2)
        set_attr_list(o, 'wuv', [((v.co.x + v.co.y) * k, (v.co.y - v.co.x) * k, 0.) if math.hypot(v.co.x, v.co.y) < R - .038 else
                                 (math.atan2(v.co.y, v.co.x) * R, v.co.z + R, 0.) for v in o.data.vertices])
        torus('Bamboo_Tray_Hoop', (0., 0., .043), R - .004, .009, P['hoop'], major=72, minor=8, detail=1, grain='z', uvw=PROP_UVW)
        torus('Bamboo_Tray_Hoop_In', (0., 0., .04), R - .027, .0065, P['hoop'], major=72, minor=6, detail=1, grain='z', uvw=PROP_UVW)
        _lash('Bamboo_Tray_Lash', R - .015, .042, 8, P, r=.0175)
        for i, a in enumerate((math.radians(40), math.radians(130))):   # the second, deeper brace crosses under the first; both reach the floor at their ends
            box('Bamboo_Tray_Brace', (0., 0., (-.004, -.007)[i]), (2 * R - .07, .026, (.009, .019)[i]), P['hoop'], bevel=.002, rot=(0, 0, a), detail=1, grain='x', uvw=PROP_UVW)


def bamboo_basket(P, name, p, s=1.):
    """Round split-bamboo basket: a plain-weave shell 8 mm thick, a foot hoop, a doubled rim lashed with hemp."""
    with xf(T(*p) @ Matrix.Diagonal((s, s, s, 1.))):
        prof = [(0., .008), (.15, .008), (.168, .022), (.196, .08), (.21, .15), (.205, .208), (.2, .224), (.191, .224), (.196, .208),
                (.2, .15), (.186, .084), (.157, .03), (0., .024)]
        o = lathe(name, prof, (0., 0., 0.), P['weave_basket'], seg=48, detail=1, grain='z', uvw=PROP_UVW)
        set_attr_list(o, 'wuv', [((math.atan2(v.co.y, v.co.x) * .2, v.co.z, 0.) if math.hypot(v.co.x, v.co.y) > .155 or v.co.z > .03 else
                                  (v.co.x, v.co.y, 0.)) for v in o.data.vertices])
        torus(name + '_Foot', (0., 0., .008), .157, .0075, P['hoop'], major=48, minor=6, detail=1, grain='z', uvw=PROP_UVW)
        torus(name + '_Rim', (0., 0., .217), .207, .0085, P['hoop'], major=48, minor=8, detail=1, grain='z', uvw=PROP_UVW)
        torus(name + '_Rim_In', (0., 0., .215), .188, .0065, P['hoop'], major=48, minor=6, detail=1, grain='z', uvw=PROP_UVW)
        _lash(name + '_Lash', .197, .216, 6, P, r=.0155, a0=.7)


def clay_jar(P, name, p, s, lid=False, seed=0.):
    """Coarse clay jar: dark glaze from a wavering line above the foot to under the lip (the lip and foot stay bare clay),
    a raised rib on the shoulder, and a two-board wooden lid on the ones in use."""
    prof = [(.21, 0), (.31, .10), (.36, .36), (.30, .58), (.18, .68), (.19, .74), (.145, .74), (.14, .66), (.25, .56), (.30, .35), (.25, .13), (.14, .07), (0., .07)]
    o = lathe(name, [(r * s, zz * s) for r, zz in [(0., 0.)] + prof], p, P['clay'], seg=36, uvw=2.5)
    def glazed(co):
        a = math.atan2(co.y, co.x)
        foot = (.13 + .03 * math.sin(3 * a + seed) + .015 * math.sin(7 * a + 2 * seed)) * s
        outer = math.hypot(co.x, co.y) > .2 * s or co.z > .66 * s
        return 1. if outer and foot < co.z < .725 * s else 0.
    set_float(o, 'gmask', glazed)
    rib = torus(name + '_Rib', (p[0], p[1], p[2] + .5 * s), .325 * s, .0065, P['clay'], major=72, minor=6, uvw=2.5)
    set_float(rib, 'gmask', lambda co: 1.)
    if lid:
        r = .2 * s; z = p[2] + .74 * s
        cyl(name + '_Lid', (p[0], p[1], z + .0115), r, .022, P['door'], verts=32, bevel=.004, group='Wood', grain='y', uvw=1.5)   # round board lid, a batten across it
        box(name + '_Lid_Batten', (p[0], p[1], z + .0235 + .012), (2 * r * .8, .045, .024), P['door'], bevel=.004, seg=1, group='Wood', grain='x', uvw=1.5)


def props(P, R):
    for name, (x, y, z), s, lid, seed in (('Jar_Large', (SW0 - .45, -.85, .02), .95, True, 0.), ('Jar_Small', (SW0 - .42, -.35, .02), .65, False, 1.7),
                                          ('Jar_Walk', (-4.75, MF - .45, PL_M), .7, True, 3.1)):
        clay_jar(P, name, (x, y, z), s, lid=lid, seed=seed)
    # a tidy pile of split firewood against the side wing's plinth, ends flush to the lane (vh_wood.stack)
    vw.stack('Firewood', SW0 - .7, SW0 - .16, -3.42, 0., .006, .36, P['firewood'], R, R=(.055, .068), L=.86, uvw=1.5)
    # a round bamboo tray stood on its rim leaning back by the dado stones, two baskets beside it, a broom by the main door (Detail_Small)
    bamboo_tray(P, (-3.6, MF - .215, PL_M + .4025))
    bamboo_basket(P, 'Basket_0', (-2.86, MF - .31, PL_M))
    bamboo_basket(P, 'Basket_1', (-2.36, MF - .34, PL_M), s=.85)
    broom(P, R, (MAIN_DOOR_X + 1.0, MF - .423, PL_M + .005))


def broom(P, R, p, lean=math.radians(15.3)):
    """Straw broom stood on its fan by the door, the handle leaning back so its tip rests on the plaster above the dado."""
    with xf(T(*p) @ RX(-lean)):
        # the fan is worn short on one corner from years of sweeping
        worn = lambda x: .004 + .03 * max(0., (-x - .02) / .13) ** 1.5
        extrude_profile('Broom_Head', [(-.14, worn(-.14)), (-.07, worn(-.07)), (0., worn(0.)), (.15, worn(.15)), (.055, .3), (-.055, .3)], .035, P['dry'],
                        plane='xz', bevel=.004, detail=1, grain='z')
        for side in (-1, 1):
            for k in range(16):
                f = k / 15 - .5 + R.uniform(-.015, .015)
                xb = f * .31 + R.uniform(-.012, .012)
                along('Broom_Strand', (f * .1, side * (.0185 + R.uniform(0., .003)), .3), (xb, side * (.019 + R.uniform(0., .008)), worn(xb) + R.uniform(.0, .012)),
                      R.uniform(.0032, .0048), P['dry'], verts=5, bevel=0., detail=1, grain='z')
        lathe('Broom_Neck', [(0., .29), (.034, .29), (.026, .36), (.02, .4), (0., .4)], (0., 0., 0.), P['dry'], seg=12, detail=1)
        box('Broom_Binding', (0., 0., .25), (.15, .043, .018), P['twine'], bevel=.003, seg=1, detail=1, grain='x', uvw=PROP_UVW)
        torus('Broom_Binding_Neck', (0., 0., .345), .029, .0055, P['twine'], major=16, minor=5, detail=1, grain='z', uvw=PROP_UVW)
        along('Broom_Handle', (0., 0., .33), (0., 0., 1.555), .016, P['timber'], verts=8, detail=1, group='Wood', grain='z')


def growth(P, R):
    pts = []
    for _ in range(46):
        side = R.random()
        if side < .3: x, y = R.uniform(-5.7, SW0 - .3), YW_Y - .2             # lane side of the front wall
        elif side < .45: x, y = YW_X - .2, R.uniform(-4.7, MF)
        elif side < .6: x, y = R.uniform(-5.4, 5.4), 4.6
        elif side < .75: x, y = SW1 + .2, R.uniform(-4.2, MF - .2)
        elif side < .85: x, y = R.uniform(-5.4, -.6), YW_Y + .3                # inside the front wall, along the plot's edge
        else: x, y = R.uniform(-5.4, SW0 - .4), WALK_Y - .12
        if abs(x - GATE_X) < .7 and abs(y - YW_Y) < .6: continue
        if abs(x - MAIN_DOOR_X) < 1.0 and y > -1.4 and y < WALK_Y + .1: continue
        FP.grass_tuft('Base_Weed', (x, y, .0 if not (YARD[0] < x < YARD[1] and YARD[2] < y < YARD[3]) else .02), R.randint(4, 8), R.uniform(.12, .3),
                      P['grass'] if R.random() < .75 else P['dry'], R, lean=.3, detail=1, spread=.08 if side >= .45 else .025)


# ------------------------------------------------------------------ collision
def collision():
    V, F = [], []
    def prism(x0, x1, y0, y1, z0, z1):
        FP.hull_loft(V, F, [[(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)] for z in (z0, z1)])
    prism(-5.45, 5.45, MF - .15, 4.45, 0., WTOP_M)                              # main wing on its plinth, flush (no ledge), doors closed
    prism(-5.45, SW0 - .15, WALK_Y, MF - .15, 0., PL_M)                          # the walk
    for j in range(3):
        h = PL_M * (j + 1) / 3; yy = WALK_Y - .3 * (3 - j)
        prism(MAIN_DOOR_X - .85 + j * .05, MAIN_DOOR_X + .85 - j * .05, yy, WALK_Y, 0., h)
    for x in COLS:
        prism(x - .12, x + .12, COL_Y - .12, COL_Y + .12, PL_M, 2.7)        # eave columns
    prism(SW0 - .15, SW1 + .15, SF - .15, MF - .15, 0., WTOP_S)                 # side wing on its plinth, flush, door closed
    g0, g1 = GATE_X - GATE_W / 2, GATE_X + GATE_W / 2
    prism(YW_X - YW_T / 2, g0, YW_Y - YW_T / 2, YW_Y + YW_T / 2, 0., YW_H + .14)   # front yard wall, left of the gate (posts included)
    prism(g1, SW0 - .15, YW_Y - YW_T / 2, YW_Y + YW_T / 2, 0., YW_H + .14)          # ... right of the gate
    prism(YW_X - YW_T / 2, YW_X + YW_T / 2, YW_Y + YW_T / 2, MF + .1, 0., YW_H + .14)  # left yard wall
    for x0 in (g0, g1 - .07):
        prism(x0, x0 + .07, YW_Y + .12, YW_Y + .12 + GATE_W / 2 + .05, 0., 1.75)     # the open leaves against the wall
    prism(SW0 - .78, SW0 - .1, -1.2, -.1, 0., .72)                          # the two jars by the side wing
    prism(SW0 - .72, SW0 - .1, -4.35, -3.35, 0., .42)                       # firewood
    prism(-5.1, -4.4, MF - .8, MF - .1, PL_M, PL_M + .55)                             # jar on the walk
    return V, F


# ------------------------------------------------------------------ build
def build_vh02(P):
    R = random.Random('VH02')
    # the side roof's curve first (the main roof needs it to know where it is covered), then the main roof's
    VR.configure(**SIDE_ROOF); R_['side'] = dict(z=VR.CFG['roof_z'], depth=dict(VR.CFG['depth']), xedge=abs(VR.CFG['x0']) + .2, reach=.12)
    VR.configure(**MAIN_ROOF); R_['main'] = dict(z=VR.CFG['roof_z'], depth=dict(VR.CFG['depth']), xedge=abs(VR.CFG['x0']) + .2)
    plinths(P, R); walls(P, R); roof_fill(P); columns(P)
    yard(P, R); yard_walls(P, R); gate(P, R)
    def cell(kind, side, x, k, r):           # kept-up roof: a few newer pale tiles, little moss
        if r > .96: return 3 + (4 if kind == 'roll' else 0)
        return (0 if r < .55 else 1 if r < .9 else 2) + (4 if kind == 'roll' else 0)
    with xf(T(0., MY, 0.)):
        roof(P, 'main', cell)
    S['main_roof_cfg'] = dict(S['roof_cfg'])
    VR.configure(**SIDE_ROOF)
    with xf(T(SX, SYC, 0.) @ RZ(math.pi / 2)):
        roof(P, 'side', cell)
    S['side_roof_cfg'] = dict(S['roof_cfg'])
    for o in S['parts']:             # the second roof's tile objects get '.001' names; keep the _LOD<n> ending the preview and LOD code look for
        m = re.fullmatch(r'Roof_Tiles_(-?1)_LOD(\d)\.\d+', o.name)
        if m: o.name = f'Roof_Tiles_Side_{m.group(1)}_LOD{m.group(2)}'
    valley(P)
    props(P, R); growth(P, R)
    socket('Socket_Gate', (GATE_X, YW_Y - YW_T / 2, 0.), rot=(0, 0, math.pi))
    socket('Socket_Door', (MAIN_DOOR_X, MF, PL_M), rot=(0, 0, math.pi))
    socket('Socket_Yard_Plot', ((PATCH[0] + PATCH[1]) / 2, (PATCH[2] + PATCH[3]) / 2, .02))
    S['collision_mesh'] = collision()
    S['prop'] = dict(kind='vcourt')
    __import__('vl_house').occluded_uvw()


NOTE = ('曲尺形院落民居（三視圖 VH02-cand-1）：後面一棟正屋橫跨整個寬度，前面右邊一棟廂房往巷子伸出來，兩棟都是單層，圍出左前方的小院。'
        '正屋坐在 0.4 m 石台基上，前簷四根簷柱下一道走廊，三級石階下到院子，木板對開門一扇半開；廂房台基較低，山牆朝巷子，向院子開一扇門兩扇窗。'
        '兩個屋頂交成一道天溝（各自去掉被另一個屋頂蓋住的瓦、板和簷口零件，交線上鋪一道天溝瓦）。'
        '院子是夯土地，矮院牆（下段亂石、上段石灰泥、頂上壓瓦）圍住，前牆一扇有小瓦頂的木門，兩扇門板開著靠在牆內，人可以走進院子。'
        '院子左邊留一塊 5 × 4 m 空地給菜圃（菜圃不在這件裡）。牆是石灰泥加亂石牆腳，木柱、木樑橫平豎直，沒有斜撐；直欞窗糊紙。'
        '有人住、照顧得好：灰泥少剝落、窗紙新、苔少；廂房牆邊一堆柴、兩只陶缸，走廊上竹匾、兩個竹籃、一只陶缸、門邊一把掃帚（竹匾、竹籃、掃帚、草在 Detail_Small）。'
        '碰撞：兩棟屋（和台基對齊，不留小台階，門都算關著）、走廊台基與石階、簷柱、院牆（大門開口留 0.9 m）、開著的門板、陶缸、柴堆。')


def register(ASSETS):
    ASSETS['VH02_LCourtyardHouse'] = dict(
        zh='曲尺形院落民居', kind='vcourt', cond='diligent', palette=palette, build=build_vh02, limit=(12., 10., 5.5), tex=2048, ver='v001',
        box=((-6., -5., 0.), (6., 5., 5.5)), ref='VH02/VH02-cand-1', slot='A1_QingxiVillage_House', minTier='standard', clamp_max=.03, uv_shape='CONVEX',
        atlases={'Main': ['Main', 'Detail_Small'], 'Stone': ['Stone'], 'Wood': ['Wood']},
        origin='centre of the lot at ground level, front (gate side) -Y',
        method='procedural mesh construction (art/source/village-houses-b/vh_court.py, vh_roof.py); procedural shaders baked to three 2048 atlases (Main, Stone, Wood); roof tiles on the shared 1024 VL tile texture (VL_Shared)',
        based_on='new outline (work pack 2026-11-09 VH02); materials and roof tiles shared with VL01-05 and VH01',
        note=NOTE)


# ------------------------------------------------------------------ measured checks
def vcourt_checks(aid, check, cfg):
    import bpy, numpy as np
    from vl_checks import _bvh
    body = _bvh([o for g, o in S['lods'][0].items() if not g.startswith('Detail_')])
    col = _bvh([S['collision_obj']]) if S.get('collision_obj') else None
    out = {}
    # two ridgelines, the side one lower
    zr = lambda x, y: (lambda h: round(h[0].z, 3) if h else None)(body((x, y, 12.), (0, 0, -1)))
    rm, rs = zr(-2., MY), zr(SX, -3.2)
    check('two_ridgelines', rm and rs and rm > rs + .3 and rm <= 5.5, {'main_ridge_top_m': rm, 'side_ridge_top_m': rs})
    # the vegetable patch: nothing between 0.05 and 2.0 m over the whole 5 x 4 m (rays down from under the eaves)
    worst = 0.; n = 0
    for x in np.linspace(PATCH[0] + .05, PATCH[1] - .05, 21):
        for y in np.linspace(PATCH[2] + .05, PATCH[3] - .05, 17):
            h = body((float(x), float(y), 2.0), (0, 0, -1)); n += 1
            if h: worst = max(worst, h[0].z)
    check('yard_patch_5x4_empty', worst < .05, {'patch_m': PATCH, 'size_m': [round(PATCH[1] - PATCH[0], 2), round(PATCH[3] - PATCH[2], 2)], 'rays': n, 'highest_hit_m': round(worst, 3)})
    # the valley: no tile of the side roof sticks out of the main roof's slope behind the crossing line, and the gutter is there
    vp = S.get('valley_points', [])
    check('roofs_meet_in_a_valley', len(vp) == 2 and min(vp) >= 5, {'gutter_points_west_east': vp,
          'roof_parts_dropped_main_side': [S.get('main_roof_parts_dropped'), S.get('side_roof_parts_dropped')]})
    if col:
        hy = lambda p, d, ax: (lambda h: round(h[0][ax], 3) if h else None)(col(p, d))
        through_gate = hy((GATE_X, -9., .9), (0, 1, 0), 1)
        wall = hy((-3., -9., .9), (0, 1, 0), 1)
        left = hy((-9., -2., .9), (1, 0, 0), 0)
        check('gate_open_walls_closed', through_gate is not None and through_gate > YW_Y + .5 and wall is not None and abs(wall - (YW_Y - YW_T / 2)) < .02
              and left is not None and abs(left - (YW_X - YW_T / 2)) < .02, {'first_hit_through_gate_y_m': through_gate, 'front_wall_face_y_m': wall, 'left_wall_face_x_m': left})
        cg = {'rear': hy((0., 9., 1.2), (0, -1, 0), 1), 'right_main': hy((9., 2.6, 1.2), (-1, 0, 0), 0), 'right_side': hy((9., -2., 1.2), (-1, 0, 0), 0),
              'side_front': hy((SX, -9., 1.2), (0, 1, 0), 1), 'main_left': hy((-9., 2.6, 1.2), (1, 0, 0), 0)}
        walk = col((-2., (WALK_Y + MF) / 2, 2.5), (0, 0, -1))
        check('collision_houses_closed_walk_walkable', all(v is not None for v in cg.values()) and walk and abs(walk[0].z - PL_M) < .01,
              {'collision_faces_m': cg, 'walk_top_m': round(walk[0].z, 3) if walk else None})
        out['collision'] = cg
    return out
