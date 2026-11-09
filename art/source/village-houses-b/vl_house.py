"""VL01-03 empty-house variants (work pack B-104h part 2): the Dondon StarterHouse v004 in three conditions.

Outline and sizes are StarterHouse v004's (art/incoming/dondon/StarterHouse/v004, build_starter_house.py; that file is not touched):
walls 7.2 x 5.2 m on a 0.54 m stone plinth with a 1.08 m porch in front and three 0.18 m steps, timber posts and beams, a double
door with a lattice window on each side, one lattice window in each other wall, the curved gable roof (front slope over the porch),
porch posts with braces, a bench and two jars. Same origin as StarterHouse (centre of the wall footprint at ground level, front -Y),
so a variant drops into a StarterHouse slot unchanged.

  VL01 long empty (three-view VL01 candidate-04): door and windows boarded over with nailed planks (rust runs under the nails), paper
       torn behind them, tiles missing in three patches with the battens and a rafter showing, grass on the ridge and in the eaves,
       moss on the tiles, plaster fallen off in blobs showing the mud brick, fallen leaves drifted on the porch and steps.
  VL02 just moved into (VL02 candidate-02): fresh window paper, porch swept clean, a broom by the door, a pot of flowers on the right
       window sill, a few replaced tiles of a paler firing, older plaster patched with fresher lime.
  VL03 half collapsed (VL03 candidate-01): the right gable end of the roof caved in (back slope and the top of the front slope) with
       broken rafters, the right wall fallen into a heap of mud brick and tiles outside so the empty room shows, a young tree growing
       up through the gap, blackened damp timber, moss and weeds. Collision closes the gap and covers the heap.
"""
import math, random
import bmesh
from mathutils import Vector, noise
from ti_core import S, box, cyl, mesh, lathe, torus, socket, extrude_profile, xf, T, RZ, surface
from cr_parts import rbox, between, sheet
import fr_parts as FP
import vl_mats
import vl_roof as RF
from vl_roof import roof_z, DEPTH

FLOOR, WALL_TOP = .54, 3.35
HEAP_X = 4.82          # VL03: the rubble runs out 0.3 m past StarterHouse's eave line on the right (within the 0.35 m outline tolerance)
WALLS = {'Front': ((0., -2.6), 0., 7.2, [(-2.35, 1.35, 1.35, 2.65, 'window'), (0., 1.7, .54, 2.95, 'door'), (2.35, 1.35, 1.35, 2.65, 'window')]),
         'Rear': ((0., 2.6), math.pi, 7.2, [(0., 1.4, 1.35, 2.65, 'window')]),
         'Right': ((3.6, 0.), math.pi / 2, 5.2, [(0., 1.4, 1.35, 2.65, 'window')]),
         'Left': ((-3.6, 0.), -math.pi / 2, 5.2, [(0., 1.4, 1.35, 2.65, 'window')])}
COND = {'VL01_LongEmptyHouse': 'abandoned', 'VL02_MovedInHouse': 'moved_in', 'VL03_HalfCollapsedHouse': 'collapsed'}


def frame(name):
    (wx, wy), a, L, ops = WALLS[name]
    return T(wx, wy, 0) @ RZ(a), L, ops


def palette_for(cond):
    def pal():
        P = vl_mats.palette(cond)
        P['roof'] = RF.roof_material()
        P['brick'] = vl_mats.plaster('Mud_Brick', peel=3., grime=.6, damp=.6, seed=(2.2, 9.1, 0.))
        return P
    return pal


# ------------------------------------------------------------------ plinth, floor, porch, steps
def plinth(P, R, cond):
    box('Plinth_Core', (0., -.45, .235), (7.56, 6.66, .47), P['mortar'], bevel=0., uvw=.15)
    k = 0
    def blk(name, c, s):
        nonlocal k
        rbox(name, c, s, P['stone'][k % 2], r=.03, amp=.004, freq=3., hew=0, chips=0, seed=k, div=.13, flat='Z', group='Stone'); k += 1
    for y in (-3.65, 2.75):
        for i in range(10): blk('Plinth_Block', (-3.42 + i * .76, y, .235), (.745, .30, .47))
    for x in (-3.65, 3.65):
        for i in range(8): blk('Plinth_Block', (x, -3.115 + i * .76, .235), (.30, .75, .47))
    box('Floor_Boards', (0., .05, .50), (7.15, 5.1, .08), P['plank'], bevel=0., grain='x')
    for i in range(22):
        box('Porch_Plank', (-3.52 + i * .335, -3.12, .50), (.325, 1.08, .08), P['plank'], bevel=.006, seg=1, grain='y')
    for i in range(3):
        top = (i + 1) * .18
        for j in range(3):
            rbox('Entry_Step', (-.78 + j * .78, -4.55 + i * .34, top / 2), (.77, .34, top), P['stone'][(i + j) % 2], r=.02, amp=.003, freq=3.,
                 hew=0, seed=40 + i * 3 + j, div=.13, flat='zZ', group='Stone')


# ------------------------------------------------------------------ walls
def wall_slab(name, L, ops, P, uv_in, keep=None, step=None, brick_edges=False, top=WALL_TOP):
    """The plaster of one wall as a single closed slab (exterior at local y = -0.01, interior at 0.21) with its openings as reveals.
    keep(x, z): extra cut (VL03 broken wall); step refines the grid so the cut edge is ragged."""
    xs = {-L / 2, L / 2}; zs = {FLOOR, top}
    for cx, w, sill, head, kind in ops:
        xs |= {cx - w / 2, cx + w / 2}; zs |= {sill, head}
    xs, zs = sorted(xs), sorted(zs)
    if step:
        fx, fz = [], []
        for a, b in zip(xs, xs[1:]):
            n = max(1, round((b - a) / step)); fx += [a + (b - a) * q / n for q in range(n)]
        for a, b in zip(zs, zs[1:]):
            n = max(1, round((b - a) / step)); fz += [a + (b - a) * q / n for q in range(n)]
        xs, zs = fx + [xs[-1]], fz + [zs[-1]]
    def opening(x, z):
        return any(cx - w / 2 < x < cx + w / 2 and sill < z < head for cx, w, sill, head, kind in ops)
    kept = {(i, j) for i in range(len(xs) - 1) for j in range(len(zs) - 1)
            if not opening((xs[i] + xs[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2) and (keep is None or keep((xs[i] + xs[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2))}
    idx = {}; V = []
    def vid(s, i, j):
        if (s, i, j) not in idx: idx[(s, i, j)] = len(V); V.append((xs[i], -.01 if s == 0 else .21, zs[j]))
        return idx[(s, i, j)]
    F, W, MI = [], [], []
    for i, j in kept:
        F.append((vid(0, i, j), vid(0, i + 1, j), vid(0, i + 1, j + 1), vid(0, i, j + 1))); W.append(1.); MI.append(0)
        F.append((vid(1, i, j), vid(1, i, j + 1), vid(1, i + 1, j + 1), vid(1, i + 1, j))); W.append(uv_in); MI.append(1)
        for (di, dj), (a, b) in (((0, -1), ((i, j), (i + 1, j))), ((1, 0), ((i + 1, j), (i + 1, j + 1))), ((0, 1), ((i + 1, j + 1), (i, j + 1))), ((-1, 0), ((i, j + 1), (i, j)))):
            if (i + di, j + dj) in kept: continue
            xm = (xs[a[0]] + xs[b[0]]) / 2; zm = (zs[a[1]] + zs[b[1]]) / 2
            broken = brick_edges and keep is not None and not keep(xm + di * .05, zm + dj * .05) and not opening(xm + di * .05, zm + dj * .05) \
                and 0 <= i + di < len(xs) - 1 and 0 <= j + dj < len(zs) - 1
            F.append((vid(0, *b), vid(0, *a), vid(1, *a), vid(1, *b))); W.append(1.); MI.append(2 if broken else 0)
    o = mesh(name, V, F, P['plaster'], grain='x')
    o.data.materials.append(P['plaster_in']); o.data.materials.append(P['brick'])
    o.data.polygons.foreach_set('material_index', MI)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    at = o.data.attributes.new('uvw', 'FLOAT', 'FACE'); at.data.foreach_set('value', W)
    return o


def window(P, name, cx, sill, w, h, cond, paper_keep=None):
    """Frame, stone sill, lattice and paper of one opening, in wall-local coordinates (exterior -y)."""
    zc = sill + h / 2
    for x in (cx - w / 2, cx + w / 2):
        box(name + '_Jamb', (x, -.06, zc), (.11, .17, h + .15), P['timber'], bevel=.012, seg=2, group='Wood', grain='z')
    for z in (sill, sill + h):
        box(name + '_Rail', (cx, -.06, z), (w + .12, .18, .11), P['timber'], bevel=.012, seg=2, group='Wood', grain='x')
    rbox(name + '_Sill', (cx, -.09, sill - .11), (w + .26, .30, .1), P['stone'][1], r=.015, amp=.002, freq=3., hew=0, seed=sum(map(ord, name)) % 97, div=.15, flat='Z', group='Stone')
    for j in range(1, 6):
        box(name + '_Lattice_V', (cx - w / 2 + j * w / 6, -.07, zc), (.025, .05, h - .08), P['timber'], bevel=0., group='Wood', grain='z')
    for j in range(1, 5):
        box(name + '_Lattice_H', (cx, -.075, sill + j * h / 5), (w - .08, .05, .025), P['timber'], bevel=0., group='Wood', grain='x')
    pw, ph = w - .1, h - .1
    sheet(name + '_Paper', 6, 5, lambda u, v: (cx - pw / 2 + pw * u, -.03, sill + .05 + ph * v), P['paper'], solid=.003, keep=paper_keep, grain='x')


def door(P, cond):
    """Double door (StarterHouse layout): plank lower halves, paper-and-lattice upper halves, ring handles."""
    for x in (-.9, .9):
        box('Door_Jamb', (x, -2.69, 1.77), (.14, .25, 2.5), P['timber'], bevel=.014, seg=2, group='Wood', grain='z')
    box('Door_Lintel', (0., -2.69, 3.0), (1.94, .26, .17), P['timber'], bevel=.014, seg=2, group='Wood', grain='x')
    box('Door_Sill', (0., -2.62, .565), (1.66, .22, .05), P['timber'], bevel=.008, seg=1, group='Wood', grain='x')
    for side in (-1, 1):
        cxl = side * (.84 - .415)
        box('Door_Backing', (cxl, -2.675, 1.72), (.82, .09, 2.30), P['door'], bevel=.008, seg=1, group='Wood', grain='z')
        for j in range(4):
            box('Door_Plank', (side * (.84 - .105 - j * .20), -2.735, 1.16), (.19, .04, 1.02), P['door'], bevel=.006, seg=1, group='Wood', grain='z')
        sheet('Door_Paper', 4, 5, lambda u, v, c=cxl: (c - .325 + .65 * u, -2.7215, 1.875 + .87 * v), P['paper'], solid=.002, grain='x')
        for j in range(5):
            box('Door_Lattice', (cxl - .28 + j * .14, -2.7425, 2.31), (.025, .035, .90), P['door'], bevel=0., group='Wood', grain='z')
        for z in (1.85, 2.08, 2.31, 2.54, 2.77):
            box('Door_Rail', (cxl, -2.7445, z), (.69, .04, .035), P['door'], bevel=0., group='Wood', grain='x')
        hx = side * .14
        box('Door_Plate', (hx, -2.766, 1.65), (.12, .024, .19), P['brass'], bevel=.008, seg=1)
        torus('Door_Ring', (hx, -2.788, 1.6), .065, .012, P['brass'], rot=(math.pi / 2, 0, 0), major=16, minor=6)


def walls(P, cond, uv_in):
    for name in WALLS:
        M, L, ops = frame(name)
        keep = step = None
        if cond == 'collapsed' and name == 'Right':
            keep, step = right_wall_keep, .1
        with xf(M):
            wall_slab(f'Wall_{name}', L, ops, P, uv_in, keep=keep, step=step, brick_edges=bool(keep),
                      top=WALL_TOP if name in ('Front', 'Rear') else WALL_TOP - .004)     # side walls 4 mm lower: no shared top plane at the corners
            for z in ((.65, 3.23) if name in ('Front', 'Rear') else (.642, 3.222)):     # side beams 8 mm lower: no shared plane where they cross at the corners
                if keep and z > 1.:
                    box('Wall_Beam_Stub', (-L / 2 + .45, -.035, z), (1.0, .18, .15), P['timber'], bevel=.012, seg=2, group='Wood', grain='x'); continue
                box('Wall_Beam', (0., -.035, z), (L + .10, .18, .15), P['timber'], bevel=.012, seg=2, group='Wood', grain='x')
            for cx, w, sill, head, kind in ops:
                if kind != 'window' or (keep and not keep(cx, sill + .1)): continue
                pk = paper_tear(name, cx) if cond == 'abandoned' else None
                window(P, f'Window_{name}_{cx:+.2f}', cx, sill, w, head - sill, cond, paper_keep=pk)
    for x in (-3.6, -1.08, 1.08, 3.6):
        for y in (-2.6, 2.6):
            h = 2.9
            if cond == 'collapsed' and x > 3 and y > 0: h = 1.75
            box('Wall_Post', (x, y, FLOOR - .004 + (h + .004) / 2), (.19, .24, h + .004), P['timber'], bevel=.014, seg=2, group='Wood', grain='z')


def paper_tear(wall, cx):
    R = random.Random(f'tear{wall}{cx}')
    holes = [(R.uniform(.2, .8), R.uniform(.2, .8), R.uniform(.12, .22)) for _ in range(2)]
    return lambda u, v: all((u - a) ** 2 + (v - b) ** 2 > r * r for a, b, r in holes)


def right_wall_keep(x, z):
    """VL03: the right wall (local x = global y) fell outwards; a ragged remnant stands at the front corner, a low stub elsewhere."""
    n = noise.noise(Vector((x * 2.3, z * 1.7, 4.2))) * .35 + noise.noise(Vector((x * 6.1, 1.3, 2.))) * .12
    h = .95 + n
    if x < -1.95: h = 3.6
    elif x < -1.15: h = .95 + (x + 1.15) / -.8 * 2.4 + n
    if x > 2.15: h = 1.25 + (x - 2.15) * 2. + n
    return z < h


# ------------------------------------------------------------------ gables, porch, eave infill
def gables(P, cond):
    for sx in (-1, 1):
        if cond == 'collapsed' and sx > 0:
            continue
        x = sx * 3.65; prof = []
        for j in range(25):
            y = 2.62 - j * 5.24 / 24
            prof.append((y, roof_z(x, abs(y) / (3.95 if y < 0 else 3.45)) - .17))
        pts = [(-2.62, 3.30), (2.62, 3.30)] + prof
        extrude_profile(f'Gable_{sx}', [(a, b) for a, b in pts], .16, P['plaster'], plane='yz', p=(x, 0, 0), bevel=0., grain='y')
        rake = [(x + sx * .02, y, roof_z(x, abs(y) / (3.95 if y < 0 else 3.45)) + RF.UNDER_TOP - RF.UNDER_T - .001) for y, _ in prof]
        RF.sweep_box(f'Gable_Rake_{sx}', rake, .14, .13, P['timber'], group='Wood', grain='y')
        box('Gable_Post', (x + sx * .1, 0., (3.31 + roof_z(x, 0) - .3) / 2), (.1, .14, roof_z(x, 0) - .3 - 3.31), P['timber'], bevel=.012, seg=2, group='Wood', grain='z')


def eave_infill(P, cond):
    """Board strip on the front and back wall lines closing the gap between the wall top and the roof boards."""
    for y, side in ((-2.6, -1), (2.6, 1)):
        D = DEPTH[side]; t = abs(y) / D
        x0, x1 = -3.585, 3.585          # inside the wall ends and the gables, not flush with them
        if cond == 'collapsed' and side > 0: x1 = 1.9
        n = 12; V = []; F = []
        for q in range(n + 1):
            x = x0 + (x1 - x0) * q / n; zt = roof_z(x, t) + RF.UNDER_TOP - RF.UNDER_T + .005
            for yy in (y - .05, y + .05):
                V.append((x, yy, 3.315)); V.append((x, yy, zt))
        for q in range(n):
            a = q * 4; b = a + 4
            F += [(a, b, b + 1, a + 1), (a + 2, a + 3, b + 3, b + 2), (a + 1, b + 1, b + 3, a + 3), (a, a + 2, b + 2, b)]
        F += [(0, 1, 3, 2), (n * 4, n * 4 + 2, n * 4 + 3, n * 4 + 1)]
        o = mesh(f'Eave_Infill_{side}', V, F, P['timber'], group='Wood', grain='x')
        bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()


def porch(P, cond):
    for x in (-3.5, 3.5):
        cyl('Porch_Socket', (x, -3.46, .67), .23, .26, P['stone'][0], verts=8, bevel=.012, group='Stone')
        cyl('Porch_Post', (x, -3.46, 2.03), .105, 2.55, P['timber'], verts=14, bevel=.01, group='Wood', grain='z')
        between('Porch_Brace', (x, -3.46, 2.85), (x - math.copysign(.55, x), -3.46, 3.30), .11, .11, P['timber'], r=.012, div=.2, group='Wood')
    box('Porch_Header', (0., -3.46, 3.32), (7.35, .2, .22), P['timber'], bevel=.014, seg=2, group='Wood', grain='x')


def props(P, cond):
    box('Bench_Seat', (2.5, -3.15, 1.03), (1.35, .43, .12), P['plank'], bevel=.012, seg=2, group='Wood', grain='x')
    for x in (2.02, 2.98):
        box('Bench_Leg', (x, -3.15, .76), (.16, .30, .44), P['timber'], bevel=.01, seg=1, group='Wood', grain='z')
    prof = [(.21, 0), (.31, .10), (.36, .36), (.30, .58), (.18, .68), (.19, .74), (.145, .74), (.14, .66), (.25, .56), (.30, .35), (.25, .13), (.14, .07), (0., .07)]
    for name, (x, y), s in (('Jar_Large', (-2.6, -3.13), 1.), ('Jar_Small', (-1.9, -3.18), .65)):
        o = lathe(name, [(r * s, z * s) for r, z in [(0., 0.)] + prof], (x, y, FLOOR), P['clay'], seg=20)
        if cond == 'collapsed' and name == 'Jar_Small':
            o.location = (x - .1, y - .05, FLOOR + .2); o.rotation_euler = (1.45, 0., .6)


# ------------------------------------------------------------------ roof assembly
def roof(P, cond, R):
    hole = lambda side, x, k: False; cut = lambda side, x, t: False
    cell = None
    if cond == 'abandoned':
        patches = [(-1, -2.45, 8.0, .45, 1.3), (-1, 1.7, 4.6, .38, 1.1), (1, -1.2, 5.5, .32, .9)]   # (slope, x, course, half-width m, half-height courses)
        def hole(side, x, k, patches=patches):
            for s, xc, kc, hw, hk in patches:
                if s != side: continue
                j = noise.noise(Vector((x * 3.1, k * .7, s))) * .35
                if ((x - xc) / hw) ** 2 + ((k - kc) / hk) ** 2 < 1 + j: return True
            return False
        def cut(side, x, t, patches=patches):
            k = (1 - t) * RF.N_COURSE - .5
            for s, xc, kc, hw, hk in patches:
                if s == side and ((x - xc) / (hw - .12)) ** 2 + ((k - kc) / (hk - .25)) ** 2 < 1: return True
            return False
        cell = lambda kind, side, x, k, r: (0 if r < .35 else 1 if r < .58 else 2) + (4 if kind == 'roll' else 0)
        S['holes'] = patches
    elif cond == 'moved_in':
        new = [(-1, -1.3, 6), (-1, 2.9, 3), (1, .6, 7)]
        def cell(kind, side, x, k, r, new=new):
            for s, xc, kc in new:
                if s == side and abs(x - xc) < .4 and abs(k - kc) <= 1 and r < .8: return 3 + (4 if kind == 'roll' else 0)
            return (0 if r < .6 else 1 if r < .9 else 2) + (4 if kind == 'roll' else 0)
    else:
        def gone(side, x, t):
            j = noise.noise(Vector((x * 1.7, t * 2.3, side * 3.))) * .3
            if side > 0: return x > 2.05 - .35 * (1 - t) + j
            return t < .62 and x > 2.75 + 1.6 * t + j
        hole = lambda side, x, k: gone(side, x, 1 - (k + .5) / RF.N_COURSE)
        cut = lambda side, x, t: gone(side, x - .1 if side > 0 else x - .1, t)
        cell = lambda kind, side, x, k, r: (0 if r < .3 else 1 if r < .5 else 2) + (4 if kind == 'roll' else 0)
        S['collapse'] = gone
    for side in (-1, 1):
        RF.tiles(P, side, hole=hole, cell=cell)
        RF.underlay(P, side, cut=cut)
        RF.eave_caps(P, side, keep=lambda x, side=side: not hole(side, x, 0))
    if cond == 'collapsed':
        RF.ridge(P, x0=-4.34, x1=1.75)
        RF.barge_boards(P, keep=lambda x, side, t: x < 0)          # the right gable end came down with its barge boards
        RF.eave_rafters(P, keep=lambda x, side: not (side > 0 and x > 1.8))
    else:
        RF.ridge(P)
        RF.barge_boards(P)
        RF.eave_rafters(P)
    return hole, cut


def battens_in_holes(P, R):
    """VL01: under each missing patch the board is gone too; battens across and one rafter below show through."""
    for s, xc, kc, hw, hk in S['holes']:
        D = DEPTH[s]
        for k in range(int(kc - hk) - 1, int(kc + hk) + 2):
            t = 1 - (k + .5) / RF.N_COURSE
            pts = [(x, s * t * D, roof_z(x, t) - .045) for x in (xc - hw - .05, xc, xc + hw + .05)]
            RF.sweep_box('Batten', pts, .045, .03, P['timber'], up=(0, -s * .3, 1), group='Wood', grain='x', detail=1)
        t0, t1 = 1 - (kc + hk + 1.2) / RF.N_COURSE, 1 - (kc - hk - 1.2) / RF.N_COURSE
        pts = [(xc + .08, s * t * D, roof_z(xc, t) + RF.UNDER_TOP - RF.UNDER_T - .001) for t in (t0, (t0 + t1) / 2, t1)]
        RF.sweep_box('Rafter', pts, .09, .12, P['timber'], group='Wood', grain='y', detail=1)


# ------------------------------------------------------------------ dressing per condition
def boards_over(P, R, cx, z0, z1, w, yf, name):
    """X of two planks and one across, nailed on, rust runs under the nails (wall-local, exterior -y, board face at yf)."""
    L = math.hypot(w + .3, z1 - z0) + .1; ang = math.atan2(z1 - z0, w + .3)
    for k, (a, dy) in enumerate(((ang, 0.), (-ang, -.03))):
        box(name + '_Board', (cx, yf + dy, (z0 + z1) / 2), (L, .028, .17), P['boards'], rot=(0, -a, 0), bevel=.006, seg=1, group='Wood', grain='x', detail=0)
        for e in (-1, 1):
            px = cx + e * (L / 2 - .1) * math.cos(a); pz = (z0 + z1) / 2 + e * (L / 2 - .1) * math.sin(a)
            for dz in (-.04, .04):
                cyl('Nail', (px, yf + dy - .016, pz + dz), .011, .01, P['iron'], axis='y', verts=6, bevel=0., detail=1)
                ry = yf + dy - .016      # 2 mm proud of the board face
                rust = [(px - .008, ry, pz + dz - .012), (px + .008, ry, pz + dz - .012),
                        (px + .004, ry, pz + dz - .13 - R.uniform(0, .06)), (px - .004, ry, pz + dz - .12)]
                mesh('Rust_Run', rust, [(0, 1, 2, 3)], P['iron'], grain='z', detail=2)
    zm = z0 + (z1 - z0) * R.uniform(.35, .6)
    box(name + '_Board_Across', (cx, yf - .057, zm), (w + .36, .028, .16), P['boards'], rot=(0, R.uniform(-.06, .06), 0), bevel=.006, seg=1, group='Wood', grain='x')


def leaves(P, R, n, x0, x1, y0, y1, z, name='Fallen_Leaf', pile=None, size=(.05, .08)):
    for i in range(n):
        x = R.uniform(x0, x1); y = R.uniform(y0, y1)
        if pile:
            a = R.uniform(0, math.tau); r = abs(R.gauss(0, pile[2])); x, y = pile[0] + math.cos(a) * r, pile[1] + math.sin(a) * r
        hit = snap0((x, y, z + .5), (0, 0, -1))
        if not hit or hit[0].z < z - .4: continue
        c = hit[0] + Vector((0, 0, .004 + .006 * R.random())); a = R.uniform(0, math.tau); L = R.uniform(*size); W = L * .45
        d = Vector((math.cos(a), math.sin(a), 0)); s = Vector((-d.y, d.x, 0))
        curl = R.uniform(.004, .012)
        up = Vector((0, 0, curl))      # leaf outline: stem end, two rounded shoulders each side, pointed tip; edges curl up
        V = [tuple(c - d * L / 2), tuple(c - d * L * .22 + s * W * .42 + up), tuple(c + d * L * .15 + s * W * .5 + up),
             tuple(c + d * L / 2 + up * .6), tuple(c + d * L * .15 - s * W * .5 + up), tuple(c - d * L * .22 - s * W * .42 + up)]
        mesh(name, V, [(0, 1, 2, 3, 4, 5)], P['leaf'], grain='z', detail=2, solid=.0012)


def weeds_on_roof(P, R, n_ridge=9, n_eave=14):
    for i in range(n_ridge):
        x = R.uniform(-4.0, 4.0)
        hit = snap0((x, R.uniform(-.1, .1), 6.), (0, 0, -1))
        if hit: FP.grass_tuft('Ridge_Grass', tuple(hit[0]), R.randint(4, 7), R.uniform(.12, .25), P['grass'] if R.random() < .6 else P['dry'], R, lean=.4, detail=1, spread=.04)
    for i in range(n_eave):
        side = -1 if R.random() < .65 else 1; x = R.uniform(-4.1, 4.1); t = R.uniform(.82, .96)
        hit = snap0((x, side * t * DEPTH[side], 6.), (0, 0, -1))
        if hit and hit[1].z > .5: FP.grass_tuft('Eave_Grass', tuple(hit[0]), R.randint(3, 6), R.uniform(.08, .16), P['grass'] if R.random() < .7 else P['dry'], R, lean=.35, detail=2, spread=.03)


def moss_on_roof(P, R, n):
    for i in range(n):
        side = -1 if R.random() < .6 else 1; x = R.uniform(-4.1, 4.1); t = R.uniform(.45, .97)
        hit = snap0((x, side * t * DEPTH[side], 6.), (0, 0, -1))
        if hit and hit[1].z > .4: FP.moss_patch('Roof_Moss', tuple(hit[0]), tuple(hit[1]), R.uniform(.06, .11), P['moss'], seed=i, flat=1.1, snap_each=True, detail=2)


def plinth_grass(P, R, n, h=(.1, .22), blades=(4, 8)):
    for i in range(n):
        side = R.choice(('front', 'back', 'left', 'right'))
        if side == 'front': x, y = R.uniform(-3.8, 3.8), -3.83
        elif side == 'back': x, y = R.uniform(-3.8, 3.8), 2.93
        else: x, y = (3.83 if side == 'right' else -3.83), R.uniform(-3.6, 2.8)
        if abs(x) < 1.25 and side == 'front': continue
        FP.grass_tuft('Plinth_Grass', (x, y, 0.), R.randint(*blades), R.uniform(*h), P['grass'] if R.random() < .7 else P['dry'], R, lean=.35, detail=2, spread=.05)


def broom(P):
    """VL02: a straw broom leaning against the door frame (right of the door)."""
    P['straw'] = __import__('ti_mats').straw('Broom_Straw', (.34, .25, .1), (.16, .1, .04))
    base = Vector((1.02, -2.86, FLOOR + .01)); top = Vector((1.06, -2.74, 1.95))
    cyl_pts = [base + (top - base) * q for q in (.3, 1.)]
    from ti_core import tube
    tube('Broom_Handle', [tuple(p) for p in cyl_pts], .014, P['timber'], res=6, group='Wood')
    hd = base + (top - base) * .3
    o = lathe('Broom_Head', [(0., -.36), (.11, -.34), (.1, -.2), (.06, -.05), (.025, .02), (0., .03)], tuple(hd), P['straw'], seg=14, scale=(1, .45, 1))
    ax = (top - base).normalized(); q = Vector((0, 0, 1)).rotation_difference(ax)
    o.rotation_euler = q.to_euler()
    lathe('Broom_Tie', [(.03, -.06), (.034, -.04), (.034, -.02), (.03, 0.)], tuple(hd), P['timber'], seg=10).rotation_euler = q.to_euler()


def flower_pot(P, R):
    """VL02: a small clay pot of pink flowers on the right front window sill."""
    P['petal'] = __import__('cr_mats').weed_leaf('Flower_Petal', (.5, .17, .22), (.75, .36, .42), (.85, .6, .62))
    P['leafg'] = __import__('cr_mats').weed_leaf('Pot_Leaf', (.03, .07, .02), (.08, .16, .04), (.15, .24, .07))
    c = (2.75, -2.77, 1.29)
    lathe('Flower_Pot', [(0., 0.), (.05, 0.), (.062, .1), (.07, .11), (.07, .125), (.061, .125), (.055, .11), (0., .1)], c, P['clay'], seg=16)
    top = Vector((c[0], c[1], c[2] + .11))
    for i in range(9):
        a = i * 2.4; r = .02 + .035 * R.random(); h = .1 + .08 * R.random()
        tip = top + Vector((math.cos(a) * r * 2.2, math.sin(a) * r * 1.6, h))
        from ti_core import tube
        tube('Flower_Stem', [tuple(top + Vector((math.cos(a) * r * .4, math.sin(a) * r * .4, 0))), tuple(tip)], .003, P['leafg'], res=4, detail=1)
        for k in range(5):
            b = k * math.tau / 5 + i
            d = Vector((math.cos(b), math.sin(b), .25)).normalized()
            pts = [tuple(tip), tuple(tip + d * .018 + Vector((-d.y, d.x, 0)) * .012), tuple(tip + d * .032), tuple(tip + d * .018 - Vector((-d.y, d.x, 0)) * .012)]
            mesh('Petal', pts, [(0, 1, 2, 3)], P['petal'], grain='z', detail=1, solid=.0012)
    for i in range(7):
        a = i * .9 + R.random(); d = Vector((math.cos(a), math.sin(a), .5)).normalized(); b0 = top + Vector((0, 0, .01))
        s = Vector((-d.y, d.x, 0)).normalized()
        mesh('Pot_Leaf', [tuple(b0), tuple(b0 + d * .04 + s * .018), tuple(b0 + d * .07 + Vector((0, 0, -.01))), tuple(b0 + d * .04 - s * .018)], [(0, 1, 2, 3)], P['leafg'], grain='z', detail=1, solid=.0012)


def cast(dg, origin, direction, distance, skip=None):
    """scene.ray_cast that looks through the LOD1/LOD2 roof copies built alongside LOD0 and the hidden collision mesh (dressing must
    rest on what LOD0 shows) and through the object skip (a piece being draped)."""
    import bpy
    o = origin.copy(); left = distance
    while left > 0:
        ok, loc, n, i, ob, m = bpy.context.scene.ray_cast(dg, o, direction, distance=left)
        if not ok: return False, None, None, None
        if ob and ('_LOD1' in ob.name or '_LOD2' in ob.name or '_Collision' in ob.name or (skip is not None and ob.name == skip.name)):
            step = (loc - o).length + .0002; o = loc + direction * .0002; left -= step; continue
        return True, loc, n, ob
    return False, None, None, None


def snap0(origin, direction):
    """FP.snap that sees only what LOD0 exports (the LOD1/LOD2 roof copies exist while the house is built)."""
    import bpy
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    ok, loc, n, _o = cast(dg, Vector(origin), Vector(direction).normalized(), 1e4)
    return (loc, n) if ok else None


def settle(prefixes, embed=.004, reach=.6, drop=False, move=True, tilt=True):
    """Drop each small dressing piece whose name starts with one of prefixes straight down until its lowest point is embed below the
    first surface under it (fallen leaves on leaves, grass blades over tile troughs, bricks on bricks), so nothing sits in the air."""
    import bpy
    moved = 0; dirty = True
    obs = [o for o in S['parts'] if o.type == 'MESH' and o.name.startswith(prefixes)]
    if prefixes[0] == 'Fallen_Leaf' and tilt:                          # tilt each leaf 2-5 degrees about its own centre
        import random as _r
        from mathutils import Matrix
        rr = _r.Random(91)
        for o in obs:
            c = sum((v.co for v in o.data.vertices), Vector()) / len(o.data.vertices)
            m = Matrix.Rotation(rr.uniform(.035, .09), 3, Vector((rr.uniform(-1, 1), rr.uniform(-1, 1), 0)).normalized())
            for v in o.data.vertices: v.co = c + m @ (v.co - c)
            o.data.update()
    obs.sort(key=lambda o: min((o.matrix_world @ v.co).z for v in o.data.vertices))   # lower pieces first: nothing lands on a piece that drops later
    for o in obs:
        if dirty: bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get(); dirty = False
        mw = o.matrix_world; lo = min((mw @ v.co for v in o.data.vertices), key=lambda c: c.z)
        if not tilt:                                                 # second pass: a piece whose foot is already inside a surface stays put
            up, _l, up_n, _o = cast(dg, lo + Vector((0, 0, .0005)), Vector((0, 0, 1)), .05, skip=o)
            if up and up_n.z > 0: continue
            # a tilted leaf on a pile can hang its lowest corner over a gap while another corner rests on a leaf: drop it by the
            # smallest gap under any of its corners, so the first corner to touch decides
            gaps = []
            for v in o.data.vertices:
                w = mw @ v.co
                ok_v, loc_v, _nv, _ov = cast(dg, w + Vector((0, 0, .0005)), Vector((0, 0, -1)), reach, skip=o)
                if ok_v: gaps.append(w.z - loc_v.z)
            if gaps and min(gaps) > .003:
                o.location.z -= min(gaps) - .0015; moved += 1; dirty = True
            continue
        ok, loc, _n, hit_o = cast(dg, lo - Vector((0, 0, .0005)), Vector((0, 0, -1)), reach)   # starts under the piece: never hits itself
        e = -.0015 if ok and hit_o and hit_o.name.startswith('Fallen_Leaf') and prefixes[0] == 'Fallen_Leaf' else embed   # a leaf on a leaf rests 1.5 mm above it (no flicker)
        z = loc.z if ok else (0. if lo.z < reach and not drop else None)     # nothing built under it near the ground: the terrain at z = 0
        if z is None:
            if drop:                                                 # grass or moss hanging past the eave edge: leave it out
                S['parts'].remove(o); bpy.data.objects.remove(o); moved += 1; dirty = True
            continue
        if move and lo.z - z > .003:
            o.location.z -= (lo.z - z) + e; moved += 1; dirty = True
    S.setdefault('settled', {})[prefixes[0] + ('' if tilt else '_pass2')] = moved


def drape(prefixes, lift=.002, reach=.08):
    """Roof moss: each colony is laid onto the first LOD0 surface under it, keeping its own dome (height above the plane through its rim),
    so it follows the tile crowns and troughs instead of bridging a trough; overlapping colonies are stacked 1.2 mm apart so none share
    a plane. Vertices with nothing within reach stay where they are."""
    import bpy
    import numpy as np
    n = 0
    for k, o in enumerate([o for o in S['parts'] if o.type == 'MESH' and o.name.startswith(prefixes)]):
        bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
        mw = o.matrix_world; inv = mw.inverted(); me = o.data
        W = [mw @ v.co for v in me.vertices]
        cnt = {}
        for poly in me.polygons:
            for ek in poly.edge_keys: cnt[ek] = cnt.get(ek, 0) + 1
        rim = sorted({i for ek, c in cnt.items() if c == 1 for i in ek}) or list(range(len(W)))
        A = np.array([[W[i].x, W[i].y, 1.] for i in rim]); z = np.array([W[i].z for i in rim])
        pa, pb, pc = np.linalg.lstsq(A, z, rcond=None)[0]
        lift_k = lift + .0012 * (k % 4)
        for v, w in zip(me.vertices, W):
            ok, loc, _n, _o = cast(dg, w + Vector((0, 0, reach / 2)), Vector((0, 0, -1)), reach, skip=o)
            if not ok: continue
            dome = max(0., w.z - (pa * w.x + pb * w.y + pc))
            v.co = inv @ Vector((w.x, w.y, loc.z + lift_k + dome)); n += 1
        me.update()
    S.setdefault('settled', {})['drape_' + prefixes[0]] = n


def settle_blades(prefixes, embed=.01, reach=.08):
    """Second pass for grass tufts on the sloped tiles: settle() moves a whole tuft by its lowest point, so the blades on the downhill side
    of a tuft are left up to a few cm above the tiles. Drop each blade (loose part) on its own; a blade with nothing under it is removed."""
    import bpy, bmesh
    moved = removed = 0
    for o in [o for o in S['parts'] if o.type == 'MESH' and o.name.startswith(prefixes)]:
        bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
        mw = o.matrix_world; inv = mw.inverted()
        bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
        seen, parts = set(), []
        for v in bm.verts:
            if v.index in seen: continue
            stack, isl = [v], []
            seen.add(v.index)
            while stack:
                w = stack.pop(); isl.append(w)
                for e in w.link_edges:
                    u = e.other_vert(w)
                    if u.index not in seen: seen.add(u.index); stack.append(u)
            parts.append(isl)
        kill = []
        for isl in parts:
            lo = min((mw @ v.co for v in isl), key=lambda c: c.z)
            up, _l, up_n, _o = cast(dg, lo + Vector((0, 0, .0005)), Vector((0, 0, 1)), .05)
            if up and up_n.z > 0: continue                           # the blade foot is already inside a tile: leave it
            ok, loc, _n, hit_o = cast(dg, lo - Vector((0, 0, .0005)), Vector((0, 0, -1)), reach)
            if not ok: kill += isl; removed += 1; continue
            d = lo.z - loc.z
            if d > .003:
                for v in isl: v.co = inv @ ((mw @ v.co) - Vector((0, 0, d + embed)))
                moved += 1
        if kill: bmesh.ops.delete(bm, geom=list({v.index: v for v in kill}.values()), context='VERTS')
        if len(bm.verts) == 0:
            bm.free(); S['parts'].remove(o); bpy.data.objects.remove(o); continue
        bm.to_mesh(o.data); bm.free(); o.data.update()
    S.setdefault('settled', {})['blades_' + prefixes[0]] = (moved, removed)


# ------------------------------------------------------------------ VL03 collapse
def collapse(P, R):
    gone = S['collapse']
    # rafters and a purlin exposed in the hole, snapped off; two sag into the room
    for side, xs in ((1, (2.3, 2.85, 3.4, 3.95)), (-1, (3.15, 3.75))):
        D = DEPTH[side]
        for i, x in enumerate(xs):
            t_end = 1.0; t_brk = .18 + .25 * R.random()
            if side < 0: t_brk = .35 + .2 * R.random()
            pts = [(x, side * t * D, roof_z(x, t) + RF.UNDER_TOP - RF.UNDER_T - .002) for t in (t_end, (t_end + t_brk) / 2, t_brk)]
            if i % 2 and side > 0:
                a = Vector(pts[0]); b = Vector(pts[-1]); drop = Vector((0, 0, -1.6)) + Vector((0, -side * .2, 0))
                pts = [tuple(a), tuple(a + (b - a) * .55 + drop * .35), tuple(a + (b - a) * .8 + drop)]
            RF.sweep_box('Broken_Rafter', pts, .1, .13, P['timber'], group='Wood', grain='y')
            tip = Vector(pts[-1]); d = (tip - Vector(pts[-2])).normalized()
            for k in range(3 if not (i % 2 and side > 0) else 0):     # splinters at the break (the two that sag into the room end in a clean snap)
                s = Vector((R.uniform(-.025, .025), R.uniform(-.025, .025), R.uniform(-.04, -.005)))      # from inside the broken end
                b0 = tip + s - d * .02          # rooted 2 cm inside the broken end
                mesh('Splinter', [tuple(b0), tuple(b0 + Vector((.015, 0, 0))), tuple(b0 + d * R.uniform(.1, .18) + Vector((.007, 0, .02)))],
                     [(0, 1, 2)], P['timber'], grain='y', solid=.01, detail=1, group='Wood')
    # purlin along x at the back, broken
    t = .5; pts = [(x, t * DEPTH[1], roof_z(x, t) + RF.UNDER_TOP - RF.UNDER_T - .14) for x in (1.2, 2.3, 3.15)]
    RF.sweep_box('Broken_Purlin', pts, .13, .15, P['timber'], group='Wood', grain='x')
    # heap of mud brick, plaster and tiles where the wall fell: a lumpy ridge against the wall line that runs out to nothing on the ground
    # (soft ends, no rim), highest in the middle of the fall, a tongue spilling onto the floor inside
    def env(b):
        lo, hi = -1.45, 2.45
        if b <= lo or b >= hi: return 0.
        u = min(b - lo, hi - b) / .9
        return 1. if u >= 1 else u * u * (3 - 2 * u)
    def h(a, b):
        e = env(b)
        if e == 0.: return 0.
        peak = .98 + .22 * noise.noise(Vector((b * .9, 7.1, 2.))) - .12 * max(0., b - 1.6)
        if a >= 3.66:
            q = (a - 3.66) / (HEAP_X - 3.66); prof = (1 - q) ** 1.6 if q < 1 else 0.
        else:
            q = (3.66 - a) / .8; prof = (FLOOR + .02 + (1 - FLOOR / peak) * peak * (1 - q) ** 1.4) / peak if q < 1 else 0.
        z = peak * prof * e
        lump = .14 * noise.noise(Vector((a * 1.9, b * 1.9, 3.3))) + .045 * noise.noise(Vector((a * 6.5, b * 6.5, 8.)))
        return max(0., z + lump * min(1., z * 2.5))
    o = FP.mound('Rubble_Heap', h, 2.82, HEAP_X, -1.5, 2.5, P['earth'], nx=30, ny=44, group='Main', uvw=.8)
    # keep only the heap itself: the flat part of the grid (and the slab's bottom and rim) would show as a rectangle of earth on the
    # ground; the heap's foot line is closed again with one bottom face
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if all(v.co.z < .012 for v in f.verts)], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    # the wall's top beam came down with it and lies across the heap; slabs of the wall face still holding their plaster
    a0 = Vector((3.75, -1.25, 0.)); a1 = Vector((4.3, 2.1, 0.))
    pts = [a0 + (a1 - a0) * q for q in (0., .5, 1.)]
    pts = [Vector((p.x, p.y, max(.1, (snap0((p.x, p.y, 3.), (0, 0, -1)) or [Vector((0, 0, .3))])[0].z + .07))) for p in pts]
    RF.sweep_box('Fallen_Wall_Beam', [tuple(p) for p in pts], .15, .18, P['timber'], group='Wood', grain='x')
    for i, (a, b, yaw, tilt, sz) in enumerate(((4.05, -.6, .25, .55, (.62, .17, .42)), (4.25, .9, -.35, .8, (.5, .17, .36)),
                                                (3.9, 1.75, .1, .35, (.7, .17, .33)), (4.5, .2, .6, .3, (.38, .15, .28)))):
        hit = snap0((a, b, 3.), (0, 0, -1))
        if not hit: continue
        o = rbox('Wall_Chunk', tuple(hit[0] + Vector((0, 0, sz[2] * .25))), sz, P['plaster'], r=.02, amp=.025, freq=4., chips=3, seed=70 + i, div=.08,
                 rot=(tilt, R.uniform(-.2, .2), math.pi / 2 + yaw))
        zmin = min((o.matrix_world @ v.co).z for v in o.data.vertices)
        if zmin < .005: o.location.z += .005 - zmin                      # sunk into the heap, never below the ground
        o.data.materials.append(P['brick'])
        for p in o.data.polygons:      # broken edges and the back show the mud brick; the old outer face (local -y) keeps its plaster
            if p.normal.y > -.7: p.material_index = 1
    for i in range(70):
        a = R.uniform(3.0, HEAP_X - .1); b = R.uniform(-1.3, 2.35)
        hit = snap0((a, b, 3.), (0, 0, -1))
        if not hit or hit[0].z < .09: continue          # bricks lie on the heap, not half sunk at its foot
        rbox('Fallen_Brick', tuple(hit[0] + Vector((0, 0, .025))), (.3 * R.uniform(.45, 1.), .15, .1), P['brick'], r=.012, amp=.01, freq=6., chips=2, seed=i, div=.1,
             rot=(R.uniform(-.6, .6), R.uniform(-.5, .5), R.uniform(0, math.pi)), detail=1 if i % 3 else 0)
    for i in range(22):
        a = R.uniform(3.1, HEAP_X - .15); b = R.uniform(-1.2, 2.3)
        hit = snap0((a, b, 3.), (0, 0, -1))
        if not hit: continue
        c = hit[0] + Vector((0, 0, .025)); yaw = R.uniform(0, math.pi); L = R.uniform(.14, .3)
        def fn(u, v, c=c, yaw=yaw, L=L):
            x = (u - .5) * .22; z = -.03 * (1 - (2 * u - 1) ** 2) * -1; y = (v - .5) * L
            return (c.x + x * math.cos(yaw) - y * math.sin(yaw), c.y + x * math.sin(yaw) + y * math.cos(yaw), c.z + z + .015 * v)
        sheet('Tile_Shard', 3, 2, fn, P['tile'], solid=.012, detail=1, grain='y')
    for i in range(16):
        a = R.uniform(3.2, HEAP_X - .1); b = R.uniform(-1.4, 2.4)
        hit = snap0((a, b, 3.), (0, 0, -1))
        if hit: FP.grass_tuft('Rubble_Weed', tuple(hit[0]), R.randint(4, 8), R.uniform(.12, .3), P['grass'] if R.random() < .7 else P['dry'], R, lean=.35, detail=2, spread=.05)
    tree(P, R)


def tree(P, R):
    """A young tree rooted inside by the fallen wall, leaning out through the gap."""
    P['bark'] = __import__('cr_mats').wood('Young_Bark', (.05, .045, .035), (.16, .14, .11), grey=.4, ground_h=0., moss=True, moss_amt=.4)
    P['tleaf'] = __import__('cr_mats').weed_leaf('Tree_Leaf', (.05, .1, .025), (.13, .22, .05), (.27, .33, .09))
    base = Vector((3.0, 1.45, .58))
    trunk = [base, base + Vector((.06, .02, .9)), base + Vector((.24, .1, 1.9)), base + Vector((.55, .2, 2.9)), base + Vector((.82, .26, 3.75)), base + Vector((.98, .3, 4.5))]
    from ti_core import tube
    tube('Tree_Trunk', [tuple(p) for p in trunk], .085, P['bark'], radii=[1.3, 1., .88, .72, .52, .32], res=8, group='Main', grain='z')
    def lerp(q):
        q *= len(trunk) - 1; k = min(int(q), len(trunk) - 2); f = q - k
        return trunk[k] + (trunk[k + 1] - trunk[k]) * f
    stems = []           # (start, end, radius) of every twig and branch end that carries leaves
    for i, (q, yaw, rise, L) in enumerate(((.42, 2.3, .55, .95), (.5, -.6, .5, 1.0), (.6, 1.1, .6, .85), (.66, -2.2, .7, .9), (.74, .2, .65, .8),
                                           (.8, 2.9, .75, .7), (.87, -1.3, .8, .6), (.93, .9, .9, .5))):
        a = lerp(q); d = Vector((math.cos(yaw), math.sin(yaw), rise)).normalized(); b = a + d * L
        b.x = min(b.x, HEAP_X - .45); b.z = min(b.z, 5.15)
        mid = (a + b) / 2 + Vector((0, 0, .07))
        tube('Tree_Branch', [tuple(a), tuple(mid), tuple(b)], .032, P['bark'], radii=[1., .72, .42], res=6, group='Main', grain='z')
        stems.append((mid, b, .032 * .5))
        for k, (f, s_) in enumerate(((.25, -1), (.45, 1), (.65, -1), (.85, 1))):     # four twigs along the outer half, alternating sides
            tw = mid + (b - mid) * f; e = (d + Vector((-d.y * s_ * .9, d.x * s_ * .9, .35))).normalized(); tb = tw + e * L * (.32 - .05 * k)
            tb.x = min(tb.x, HEAP_X - .35); tb.z = min(tb.z, 5.4)
            tube('Tree_Twig', [tuple(tw), tuple(tb)], .012, P['bark'], radii=[1., .5], res=4, group='Main', grain='z', detail=1)
            stems.append((tw, tb, .012 * .7))
    top = trunk[-1] + (trunk[-1] - trunk[-2]).normalized() * .25
    tube('Tree_Twig', [tuple(trunk[-1]), tuple(top)], .02, P['bark'], radii=[1., .45], res=4, group='Main', grain='z')
    stems.append((trunk[-2] + (trunk[-1] - trunk[-2]) * .5, top, .02 * .6))
    # leaves grow on the stems: each leaf's stalk end sits inside its twig, so every leaf is attached (no leaf hangs in the air)
    n = 0
    for a, b, rad in stems:
        ax = (b - a); Lst = ax.length; ax.normalize()
        p0 = ax.cross(Vector((0, 0, 1))); p0 = p0.normalized() if p0.length > 1e-3 else Vector((1, 0, 0)); p1 = ax.cross(p0)
        count = max(4, int(Lst / .045))
        for q in range(count):
            f = .12 + .88 * (q + R.random() * .6) / count
            ang = q * 2.4 + R.uniform(-.4, .4)
            radial = p0 * math.cos(ang) + p1 * math.sin(ang)
            c = a + ax * (Lst * f) + radial * rad * .5                     # stalk end inside the twig
            d = (radial * .9 + ax * .55 + Vector((0, 0, -.25)) + Vector((R.uniform(-.25, .25), R.uniform(-.25, .25), R.uniform(-.2, .2)))).normalized()
            L = R.uniform(.1, .14); W = L * .48; st = .025                  # 2.5 cm stalk, then the blade
            sd = d.cross(Vector((0, 0, 1))); sd = sd.normalized() if sd.length > 1e-3 else Vector((1, 0, 0)); up = sd.cross(d).normalized()
            c1 = c + d * st
            V = [tuple(c), tuple(c1 + d * L * .4 + sd * W / 2 + up * .01), tuple(c1 + d * L), tuple(c1 + d * L * .4 - sd * W / 2 + up * .01)]
            mesh('Tree_Leaf', V, [(0, 1, 2, 3)], P['tleaf'], grain='z', solid=.0015, detail=0 if q % 2 else 1); n += 1
    S['tree_leaves'] = n


def interior_uvw(w):
    """Faces inside the closed room (floor, inner faces of posts and frames, roof boards seen from below) get texel weight w."""
    import numpy as np
    for o in S['parts']:
        if o.type != 'MESH' or o.get('group') == 'Roof': continue
        me = o.data; mw = o.matrix_world; n = len(me.polygons)
        c = np.zeros(n * 3, np.float32); me.polygons.foreach_get('center', c); c = c.reshape(-1, 3)
        c = np.c_[c, np.ones(n)] @ np.array(mw).T
        inside = (np.abs(c[:, 0]) < 3.388) & (np.abs(c[:, 1]) < 2.388) & (c[:, 2] > .53) & (c[:, 2] < 5.3)
        if not inside.any(): continue
        at = me.attributes.get('uvw') or me.attributes.new('uvw', 'FLOAT', 'FACE')
        if 'uvw' not in o.keys() and at.data[0].value == 0.: pass
        cur = np.zeros(n, np.float32); at.data.foreach_get('value', cur)
        cur[cur == 0.] = float(o.get('uvw', 1.))
        cur[inside] *= w
        at.data.foreach_set('value', cur)


def occluded_uvw(reach=.3, w=.06):
    """Faces that cannot be seen (pressed against a wall, a beam or the ground: every probe ray from the face meets something within
    reach) get texel weight w. Five rays: along the normal and tilted 45 degrees four ways."""
    import bpy, numpy as np
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get(); sc = bpy.context.scene
    hidden = 0; total = 0
    for o in S['parts']:
        if o.type != 'MESH' or o.get('group') == 'Roof': continue
        me = o.data; mw = o.matrix_world; nm = mw.to_3x3().inverted().transposed()
        at = me.attributes.get('uvw') or me.attributes.new('uvw', 'FLOAT', 'FACE')
        cur = np.zeros(len(me.polygons), np.float32); at.data.foreach_get('value', cur); cur[cur == 0.] = float(o.get('uvw', 1.))
        for p in me.polygons:
            total += 1
            c = mw @ p.center; n = (nm @ p.normal).normalized()
            if c.z < .012 and n.z < -.5: cur[p.index] *= w; hidden += 1; continue
            a = n.cross(Vector((0, 0, 1)) if abs(n.z) < .9 else Vector((1, 0, 0))).normalized(); b = n.cross(a)
            blocked = True
            for d in (n, (n + a).normalized(), (n - a).normalized(), (n + b).normalized(), (n - b).normalized()):
                ok, *_ = cast(dg, c + n * .004, d, reach)
                if not ok: blocked = False; break
            if blocked: cur[p.index] *= w; hidden += 1
        at.data.foreach_set('value', cur)
    S['occluded_faces'] = (hidden, total)


# ------------------------------------------------------------------ collision
def collision(cond):
    V, F = [], []
    def prism(x0, x1, y0, y1, z0, z1):
        FP.hull_loft(V, F, [[(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)] for z in (z0, z1)])
    prism(-3.8, 3.8, -3.8, 2.9, 0., FLOOR)                       # plinth and porch floor
    for i in range(3):
        prism(-1.165, 1.165, -4.72 + i * .34, -3.8, 0., (i + 1) * .18)  # steps
    prism(-3.61, 3.61, -2.61, -2.39, FLOOR, WALL_TOP)            # walls (door closed)
    prism(-3.61, 3.61, 2.39, 2.61, FLOOR, WALL_TOP)
    prism(-3.61, -3.39, -2.39, 2.39, FLOOR, WALL_TOP)
    prism(3.39, 3.61, -2.39, 2.39, FLOOR, WALL_TOP)              # VL03: closes the gap where the wall fell
    for x in (-3.5, 3.5):
        sec = lambda z: [(x + math.cos(k * math.tau / 8) * .14, -3.46 + math.sin(k * math.tau / 8) * .14, z) for k in range(8)]
        FP.hull_loft(V, F, [sec(FLOOR), sec(3.3)])
    prism(1.82, 3.18, -3.37, -2.93, FLOOR, 1.09)                  # bench
    if cond == 'collapsed':
        FP.hull_loft(V, F, [[(3.61, -1.45, 0.), (HEAP_X, -1.2, 0.), (HEAP_X, 2.2, 0.), (3.61, 2.45, 0.)],
                            [(3.61, -.6, .9), (3.95, -.5, .75), (3.95, 1.6, .75), (3.61, 1.7, .9)]])     # the heap as a ramp off the wall line
    return V, F


# ------------------------------------------------------------------ build
def build_house(aid):
    cond = COND[aid]
    def build(P):
        R = random.Random(aid)
        uv_in = .7 if cond == 'collapsed' else .12
        plinth(P, R, cond)
        walls(P, cond, uv_in)
        door(P, cond)
        gables(P, cond)
        eave_infill(P, cond)
        porch(P, cond)
        props(P, cond)
        roof(P, cond, R)
        if cond == 'abandoned':
            battens_in_holes(P, R)
            for wname in WALLS:
                M, L, ops = frame(wname)
                with xf(M):
                    for cx, w, sill, head, kind in ops:
                        if kind == 'window': boards_over(P, R, cx, sill - .05, head + .05, w, -.16, f'Boarded_{wname}')
            boards_over(P, R, 0., .75, 2.85, 1.7, -2.83, 'Boarded_Door')      # back face on the door frame
            weeds_on_roof(P, R); moss_on_roof(P, R, 22); plinth_grass(P, R, 34, h=(.18, .4), blades=(6, 11))
            leaves(P, R, 90, -3.5, 3.5, -3.6, -2.75, FLOOR, size=(.08, .12))
            for px in (-3.2, -1.15, 1.2, 3.25):        # drifts where the wind leaves them: against the wall, the door sill and the posts
                leaves(P, R, 45, 0, 0, 0, 0, FLOOR, pile=(px, -2.83, .22), size=(.08, .12))
            leaves(P, R, 80, 0, 0, 0, 0, FLOOR, pile=(0., -2.95, .32), size=(.08, .12))
            leaves(P, R, 60, -1.1, 1.1, -4.7, -3.8, .5, size=(.08, .12))
            for x, y in ((-1.3, -4.35), (1.3, -4.15), (-3.95, -3.9), (3.95, -3.9)):   # banked at the foot of the steps and plinth corners
                leaves(P, R, 35, 0, 0, 0, 0, 0., pile=(x, y, .15), size=(.08, .12))
        elif cond == 'moved_in':
            broom(P); flower_pot(P, R)
            moss_on_roof(P, R, 6); plinth_grass(P, R, 8)
            leaves(P, R, 18, 1.4, 1.9, -4.75, -4.35, .2)        # the sweepings, pushed off beside the steps
        else:
            collapse(P, R)
            weeds_on_roof(P, R, n_ridge=4, n_eave=10); moss_on_roof(P, R, 18); plinth_grass(P, R, 26)
            leaves(P, R, 90, 1.0, 3.3, -2.3, 2.3, FLOOR)
            leaves(P, R, 60, -3.5, 3.5, -3.6, -2.75, FLOOR)
        socket('Socket_Door', (0., -2.72, FLOOR), rot=(0, 0, math.pi))
        socket('Socket_Porch', (0., -3.12, FLOOR))
        socket('Socket_Path', (0., -4.72, 0.), rot=(0, 0, math.pi))
        for pre in (('Fallen_Brick', 'Tile_Shard'), ('Fallen_Leaf',), ('Eave_Grass', 'Ridge_Grass', 'Rubble_Weed')):
            # grass on the tiles drops at most into a trough (6 cm) and moss stays put; either is left out when nothing is that close under it
            settle(pre, embed=.012 if pre[0] in ('Eave_Grass', 'Rubble_Weed') else .004, drop=pre[0] in ('Eave_Grass', 'Roof_Moss'), move=pre[0] != 'Roof_Moss',
                   reach={'Eave_Grass': .06, 'Roof_Moss': .015}.get(pre[0], .6))
        for _k in range(3):                                               # later passes: a leaf whose support moved after it landed drops again
            settle(('Fallen_Leaf',), tilt=False)
            if not S['settled']['Fallen_Leaf_pass2']: break
        settle_blades(('Eave_Grass', 'Ridge_Grass')); drape(('Roof_Moss',))
        print('SETTLED', S.get('settled'), flush=True)
        interior_uvw(uv_in); occluded_uvw()
        S['collision_mesh'] = collision(cond)
        S['prop'] = dict(kind='house', cond=cond)
    return build


NOTES = {
    'VL01_LongEmptyHouse': '久無人住的空屋（三視圖 VL01 candidate-04）：外框照 Dondon StarterHouse v004（牆 7.2 × 5.2 m、石基 0.54 m、前廊 1.08 m、三級 0.18 m 石階、曲面雙坡瓦頂、前坡蓋過前廊）。'
        '門和五扇窗用舊木板釘成 X 加一道橫板，釘頭下有鏽水痕；窗紙在木板後面破洞。前坡兩處、後坡一處缺瓦，缺口看得到掛瓦條和一根椽子；屋脊和簷口長草、瓦面長苔；'
        '灰泥一塊塊剝落露出土磚；前廊、門檻和台階上堆著落葉。',
    'VL02_MovedInHouse': '剛有人住的空屋（三視圖 VL02 candidate-02）：外框照 StarterHouse v004。新糊的白窗紙、前廊掃乾淨（掃起的落葉推到台階旁）、門邊靠一支掃帚、'
        '右窗台一盆粉紅小花；前坡兩處、後坡一處換了幾片顏色較淺的新瓦；舊灰泥上有較新的補灰。玩家第一天分到的就是這種。',
    'VL03_HalfCollapsedHouse': '半塌的空屋（三視圖 VL03 candidate-01）：外框照 StarterHouse v004。右山牆一端的屋頂塌陷（後坡整片、前坡靠屋脊的上半），斷椽外露、兩根垂進屋內；'
        '右牆往外倒成一堆土磚和碎瓦，只剩前角一段和低矮的牆根，從缺口看得到空屋內；一棵小樹從屋內長出、穿過缺口；木頭發黑受潮、瓦和瓦礫長苔、瓦礫上長草。'
        '碰撞：牆線照原屋封住（缺口處也擋），瓦礫堆另有一個斜面碰撞，人不會卡進屋內。',
}


def register(ASSETS):
    for aid, cond in COND.items():
        ASSETS[aid] = dict(zh={'abandoned': '久無人住的空屋', 'moved_in': '剛有人住的空屋', 'collapsed': '半塌的空屋'}[cond], kind='house', cond=cond,
                           palette=palette_for(cond), build=build_house(aid), limit=(9.05 if cond != 'collapsed' else 9.36, 8.19, 5.62), tex=2048, ver='v001',
                           box=((-4.53, -4.73, 0.), (4.53 if cond != 'collapsed' else HEAP_X + .02, 3.47, 5.62)), ref=f'{aid[:4]}/candidate-0{ {"abandoned": 4, "moved_in": 2, "collapsed": 1}[cond]}',
                           slot='A1_QingxiVillage_EmptyHouse', minTier='standard', clamp_max=.03, uv_shape='CONVEX',
                           atlases={'Main': ['Main', 'Detail_Small'], 'Stone': ['Stone'], 'Wood': ['Wood']},
                           origin='centre of the wall footprint at ground level, front -Y (same origin as StarterHouse v004, so a variant drops into its slot)',
                           note=NOTES[aid])
