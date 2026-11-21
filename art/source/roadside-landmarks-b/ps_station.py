"""PS01 old post station (work pack 2026-11-09 B-112h, batch B): an abandoned roadside post station on the south stretch of the A9 road.

Three-view: art/references/PS01/PS01-cand-3.png (AI, Codex image_gen; proportions from the work pack's written sizes, not the image).
Size limit 14 x 10 x 6 m. Origin: centre of the whole lot at ground level, front (the road side) -Y.

A main single-storey hall on the left on a stone plinth (rubble stone dado, faded lime plaster, timber posts square-on, no braces), an
open front walk under the eave on four columns, steps up to a plank double door (one leaf ajar, too narrow to pass), two lattice windows
with torn paper. On the right a row of three open-fronted stable stalls under a lower roof that leans against the hall's gable: plank back
wall, plank partitions, a feed trough, one half-gate closed, one hanging from one hinge, one stall open; straw on the floor. In front a
yard of worn paving slabs with grass in the gaps and a hitching rail (log rail on four posts, iron rings, rope wraps).
Half abandoned, not collapsed: tiles missing in patches with the battens showing, plaster peeled back to the stone, weeds at every base.
Shares with VL01-05: the material set (vl_mats, 'abandoned' palette), the VL roof tiles and their shared 1024 texture (VL_Shared, read
only) on the VH roof curve (vh_roof.py, copied from art/b-1109-vh-village-houses), and the village-houses-b export pipeline.
"""
import math, random
import bmesh
from mathutils import Vector, noise
from ti_core import S, box, cyl, mesh, lathe, torus, socket, extrude_profile, xf, T, RZ
from cr_parts import rbox, sheet, log
import fr_parts as FP
import vl_mats, cr_mats as cm, ti_mats as tm
import vl_roof as RF
import vh_roof as VR

# ------------------------------------------------------------------ layout (metres, world)
MX, MY = -3.0, 1.8          # hall centre (its local frame: ridge along x at local y 0)
HX, HY = 3.4, 2.3           # hall walls: outer faces at local x +-HX, y +-HY
PL = .4                     # plinth top = hall floor
WT = .3                     # wall thickness
WTOP = 3.15                 # top of the wall plates
HALL_ROOF = dict(z0=2.95, rise=1.9, depth_front=3.3, depth_back=3.15, xh=3.7, lift_end=.12)
SX, SY = 3.475, 2.25        # stable centre
SHX, SHY = 3.025, 2.05      # stable: x .45..6.5, front post line y .2, back wall y 4.3
STABLE_ROOF = dict(z0=2.25, rise=1.1, depth_front=2.55, depth_back=2.55, xh=3.12, lift_end=.08, lift_eave=.08)
YARD_Y = (-5.0, MY - HY - .8)   # paved yard, road edge to the plinth
STABLE_X0 = MX + HX + .05       # plinth's right edge = where the stable bay starts
APRON_Y = SY - SHY - .15        # paving in front of the stable stops at the post bases
RAIL_Y = -4.5
RAIL_POSTS = (-1.6, .6, 2.8, 5.0)
STALLS = (.45, 2.65, 4.6, 6.5)   # stall bounds (world x): A closed gate, B open, C gate hanging

HALL_WALLS = {   # local frame of the hall; ((x, y), angle, length, openings (cx, w, sill, head, kind))
    'Front': ((0., -HY), 0., 2 * HX, [(-2.1, .9, 1.25, 2.2, 'window'), (0., 1.6, PL, 2.55, 'door'), (2.1, .9, 1.25, 2.2, 'window')]),
    'Rear': ((0., HY), math.pi, 2 * HX, [(1.2, .7, 1.45, 2.15, 'window')]),
    'Right': ((HX, 0.), math.pi / 2, 2 * HY, []),
    'Left': ((-HX, 0.), -math.pi / 2, 2 * HY, [(.6, .7, 1.45, 2.15, 'window')]),
}


def palette():
    P = vl_mats.palette('abandoned')
    # timber and door boards: the same woods as VL 'abandoned', but the grey silvering follows the grain (the shared one reads as fog patches up close)
    P['timber'] = cm.wood('Frame_Timber_PS01', vl_mats.WOOD[2], vl_mats.WOOD[1], grey=.75, ground_h=.12, grey_grain=True)
    P['door'] = cm.wood('Door_Board_PS01', vl_mats.WOOD[2], vl_mats.WOOD[0], grey=.75, ground_h=0., grey_grain=True)
    P['plank'] = cm.wood('Porch_Plank_PS01', vl_mats.WOOD[0], (.26, .14, .06), grey=.675, ground_h=0., grey_grain=True)
    P['roof'] = RF.roof_material()
    P['straw'] = tm.plain('Straw_Litter', (.33, .25, .11), rough=.95, noise=.45, scale=60.)
    P['rope'] = tm.plain('Old_Rope', (.2, .15, .085), rough=.95, noise=.35, scale=80.)
    P['wall_stone'] = P['stone'] + [cm.stone('Dado_Stone_Warm', light=(.2, .19, .165), dark=(.085, .08, .07), ochre=(.24, .2, .14), moss=.9, lichen=.6, crack=.5)]
    P['slab'] = [cm.stone(f'Yard_Slab_{i}', light=l, dark=d, ochre=(.2, .18, .13), moss=.45, lichen=.4, crack=.8)
                 for i, (l, d) in enumerate(((vl_mats.STONE[2], vl_mats.STONE[1]), ((.19, .185, .165), (.08, .078, .07))))]
    return P


def frame(name):
    (wx, wy), a, L, ops = HALL_WALLS[name]
    return T(wx, wy, 0) @ RZ(a), L, ops


def slab(name, L, ops, z0, z1, y0, y1, mat_out, mat_in, uv_in=.12):
    """Closed wall slab in wall-local coordinates (exterior face at y0), openings as reveals (from vh_house)."""
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


# ------------------------------------------------------------------ hall
def plinth(P, R):
    """Stone plinth (台基) of dressed slabs on edge, the front walk under the eave, three steps to the door."""
    x0, x1, y0, y1 = -HX - .15, HX + .05, -HY - .8, HY + .15
    box('Plinth_Core', ((x0 + x1) / 2, (y0 + y1) / 2, PL / 2 - .02), (x1 - x0 - .1, y1 - y0 - .1, PL - .04), P['mortar'], bevel=0., uvw=.12)
    k = [0]
    def blk(c, s):
        rbox('Plinth_Stone', c, s, P['stone'][k[0] % 2], r=.025, amp=.006, freq=2.5, hew=1, chips=1, seed=k[0], div=.25, flat='Z', group='Stone'); k[0] += 1
    def run(a, b, fixed, along_x):
        x = a
        while x < b - .05:
            L = min(R.uniform(.6, 1.0), b - x)
            if b - x - L < .3: L = b - x
            c = x + L / 2
            blk((c, fixed, PL / 2) if along_x else (fixed, c, PL / 2), (L - .015, .28, PL) if along_x else (.28, L - .015, PL))
            x += L
    run(x0, x1, y0 + .14, True); run(x0, x1, y1 - .14, True)
    run(y0 + .28, y1 - .28, x0 + .14, False); run(y0 + .28, y1 - .28, x1 - .14, False)
    # walk under the front eave: big flat slabs, two cracked, one sunk
    x = x0 + .28
    while x < x1 - .3:
        L = min(R.uniform(.7, 1.1), x1 - .28 - x)
        rbox('Walk_Slab', (x + L / 2, (y0 + .28 - HY) / 2 - .0, PL - .03 - (.02 if R.random() < .15 else 0.)), (L - .02, (-HY) - (y0 + .28) - .02, .06),
             P['stone'][R.randrange(2)], r=.015, amp=.004, freq=3., hew=1, chips=1, seed=200 + int(x * 10), div=.25, flat='zZ', group='Stone')
        x += L
    for j in range(3):          # steps, 0.133 m each, 0.3 m treads
        h = PL * (j + 1) / 3
        rbox('Hall_Step', (0., y0 - .3 * (3 - j) + .15, h / 2), (1.9 - j * .1, .32, h), P['stone'][j % 2], r=.02, amp=.004, freq=3., hew=1, chips=1,
             seed=300 + j, div=.25, flat='zZ', group='Stone')


def column(P, R, x, y, top, name='Column'):
    rbox(name + '_Base', (x, y, PL + .09), (.34, .34, .18), P['stone'][1], r=.03, amp=.004, freq=3., hew=1, chips=1, seed=int(x * 100) % 97, div=.25, flat='z', group='Stone')
    cyl(name, (x, y, (PL + .18 + top) / 2), .1, top - PL - .18, P['timber'], verts=12, group='Wood', grain='z')


def hall_walls(P, R):
    for wname in HALL_WALLS:
        M, L, ops = frame(wname)
        long_wall = wname in ('Front', 'Rear')
        with xf(M):
            slab(f'Hall_Wall_{wname}', L - .02, ops, PL, WTOP - .14, .0, WT, P['plaster'], P['plaster_in'])
            box(f'Hall_Plate_{wname}', (0., .1, WTOP - .07), (L + (.14 if long_wall else -.2), .26, .14), P['timber'], bevel=.012, seg=2, group='Wood', grain='x')
            box(f'Hall_Sill_Beam_{wname}', (0., -.06, PL + .05), (L - .02, .08, .1), P['timber'], bevel=.01, seg=2, group='Wood', grain='x', uvw=.6)
            # rubble dado on the outside, 0.4 .. 1.15 m, broken by the door; face stones show where the plaster has fallen
            blocked = [(cx - w / 2 - .08, cx + w / 2 + .08) for cx, w, sill, head, kind in ops if kind == 'door']
            z = PL; zs = []
            while z < 1.12:
                h = R.uniform(.22, .3); zs.append((z, min(z + h, 1.15))); z += h
            for c, (za, zb) in enumerate(zs):
                x = -L / 2 + .12 + (.18 if c % 2 else 0.)
                while x < L / 2 - .14:
                    Ls = min(R.uniform(.32, .66), L / 2 - .12 - x)
                    if Ls < .14: break
                    if not any(a < x + Ls / 2 < b for a, b in blocked):
                        rbox(f'Dado_Stone_{wname}', (x + Ls / 2, -.04, (za + zb) / 2), (Ls - .02, .12, zb - za - .02), P['wall_stone'][R.randrange(3)],
                             r=.025, amp=.009, freq=2.4, hew=2, chips=1, seed=int(x * 50 + c * 7 + len(wname)), div=.3, group='Stone')
                    x += Ls
            # posts square-on at the wall ends (the corner posts belong to the front and rear walls; a side wall's own would sit inside them);
            # 0.22 m along the wall so they stand 1 cm proud of the side walls, foot 2 cm into the plinth (no face shared with the plaster)
            for px in ((-L / 2 + .1, L / 2 - .1) if long_wall else ()):
                box(f'Hall_Post_{wname}', (px, -.03, (PL - .02 + WTOP) / 2), (.22, .2, WTOP - PL + .02), P['timber'], bevel=.014, seg=2, group='Wood', grain='z')
            for cx, w, sill, head, kind in ops:
                box(f'Hall_Lintel_{wname}', (cx, -.03, head + .06), (w + .3, .16, .16), P['timber'], bevel=.01, seg=2, group='Wood', grain='x')
                if kind == 'window': window(P, R, f'Hall_Window_{wname}_{cx:+.1f}', cx, sill, w, head - sill)
                else: door(P, cx, w, head)
            if long_wall:
                box(f'Hall_Mid_Rail_{wname}', (0., -.02, 2.75), (L - .2, .12, .1), P['timber'], bevel=.01, seg=2, group='Wood', grain='x')


def window(P, R, name, cx, sill, w, h):
    """Lattice window: frame, square lattice, paper torn in two or three holes."""
    zc = sill + h / 2
    for x in (cx - w / 2 - .04, cx + w / 2 + .04):
        box(name + '_Jamb', (x, -.02, zc), (.08, .14, h + .08), P['timber'], bevel=.01, seg=2, group='Wood', grain='z')
    box(name + '_Sill', (cx, -.04, sill - .03), (w + .2, .18, .07), P['timber'], bevel=.01, seg=2, group='Wood', grain='x')
    for j in range(1, 6):
        box(name + '_Bar', (cx - w / 2 + j * w / 6, -.02, zc), (.025, .04, h - .02), P['timber'], bevel=0., group='Wood', grain='z')
    for j in range(1, 6):
        box(name + '_Bar_Rail', (cx, -.02, sill + j * h / 6), (w + .02, .035, .025), P['timber'], bevel=0., group='Wood', grain='x')
    holes = [(R.uniform(.2, .8), R.uniform(.25, .85), R.uniform(.12, .24)) for _ in range(R.randint(2, 3))]
    keep = lambda u, v: all((u - a) ** 2 + (v - b) ** 2 > r * r for a, b, r in holes)
    sheet(name + '_Paper', 8, 8, lambda u, v: (cx - w / 2 + w * u, .03, sill + h * v), P['paper'], solid=.003, keep=keep, grain='x')


def door(P, cx, w, head):
    """Plank double door: the left leaf shut, the right one ajar about 30 degrees (a gap too narrow to walk through)."""
    for x in (cx - w / 2 - .06, cx + w / 2 + .06):
        box('Door_Jamb', (x, -.02, (PL + head) / 2), (.12, .18, head - PL), P['timber'], bevel=.012, seg=2, group='Wood', grain='z')
    rbox('Door_Threshold', (cx, .05, PL + .03), (w + .1, .2, .06), P['stone'][1], r=.01, amp=.002, freq=3., hew=0, seed=7, div=.25, flat='zZ', group='Stone')
    lw = w / 2 - .01; zc = (PL + .06 + head) / 2; hh = head - PL - .08
    box('Door_Leaf', (cx - w / 4, .1, zc), (lw, .05, hh), P['door'], bevel=.006, seg=1, group='Wood', grain='z')
    for zb in (PL + .4, head - .4):
        box('Door_Batten', (cx - w / 4, .135, zb), (lw - .06, .025, .1), P['door'], bevel=.005, seg=1, group='Wood', grain='x', uvw=.4)
    hinge = Vector((cx + w / 2, .1, 0.)); a = math.radians(32)
    with xf(T(*hinge) @ RZ(a)):
        box('Door_Leaf_Ajar', (-lw / 2, 0., zc), (lw, .05, hh), P['door'], bevel=.006, seg=1, group='Wood', grain='z')
        for zb in (PL + .4, head - .4):
            box('Door_Batten', (-lw / 2, .035, zb), (lw - .06, .025, .1), P['door'], bevel=.005, seg=1, group='Wood', grain='x', uvw=.4)
    torus('Door_Ring', (cx - .08, .07, 1.35), .05, .009, P['iron'], rot=(math.pi / 2, 0, 0), major=14, minor=6)
    # the floor inside, seen through the gap
    box('Hall_Floor', (0., HY / 2 - .1, PL - .01), (2 * HX - 2 * WT, HY * 2 - 2 * WT, .02), P['earth'], bevel=0., uvw=.15)


def gables(P):
    for sx in (-1, 1):
        x = sx * (HX - .1)
        ys = [-HY + .02 + (2 * HY - .04) * j / 24 for j in range(25)]
        prof = [(y, VR.under(x, y) - .02) for y in ys]
        pts = [(ys[0], WTOP - .02), (ys[-1], WTOP - .02)] + prof[::-1]
        extrude_profile(f'Hall_Gable_{sx}', pts, .16, P['plaster'], plane='yz', p=(x, 0, 0), bevel=0., grain='y')
        zk = VR.under(x, 0.) - .1
        box('Gable_King_Post', (x + sx * .07, 0., (WTOP + zk) / 2), (.08, .16, zk - WTOP), P['timber'], bevel=.01, seg=2, group='Wood', grain='z')
        RF.sweep_box(f'Gable_Rake_{sx}', [(x + sx * .06, y, VR.under(x, y) - .001) for y, _ in prof], .16, .14, P['timber'], group='Wood', grain='y')


def eave_front(P):
    """Four eave columns on the front walk, the eave purlin they carry, ties back to the wall; infill boards over the wall plates."""
    yc = -HY - .62
    for x in (-HX + .2, -1.1, 1.1, HX - .2):
        top = VR.under(x, yc) - .17
        column(P, None, x, yc, top, 'Eave_Column')
        RF.sweep_box('Eave_Tie', [(x, yc, VR.under(x, yc) - .2), (x, -HY + .1, VR.under(x, -HY + .1) - .2)], .1, .12, P['timber'], group='Wood', grain='y')
    xs = [-HX - .05 + (2 * HX + .1) * i / 20 for i in range(21)]
    RF.sweep_box('Eave_Purlin', [(x, yc, VR.under(x, yc) - .002) for x in xs], .17, .17, P['timber'], group='Wood', grain='x')
    for y, nm in ((-HY + .08, 'Front'), (HY - .08, 'Rear')):
        n = 14; V = []; F = []
        x0, x1 = -HX + .05, HX - .05
        for q in range(n + 1):
            x = x0 + (x1 - x0) * q / n; zt = VR.under(x, y) + .005
            for yy in (y - .05, y + .05):
                V.append((x, yy, WTOP - .01)); V.append((x, yy, zt))
        for q in range(n):
            a = q * 4; b = a + 4
            F += [(a, b, b + 1, a + 1), (a + 2, a + 3, b + 3, b + 2), (a + 1, b + 1, b + 3, a + 3), (a, a + 2, b + 2, b)]
        F += [(0, 1, 3, 2), (n * 4, n * 4 + 2, n * 4 + 3, n * 4 + 1)]
        o = mesh(f'Eave_Infill_{nm}', V, F, P['timber'], group='Wood', grain='x', uvw=.5)
        bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()


def roof(P, patches, R):
    """VL tiles on the configured curve; missing patches (slope, x, course, half-width m, half-height courses) with battens under."""
    def hole(side, x, k):
        for s, xc, kc, hw, hk in patches:
            if s != side: continue
            j = noise.noise(Vector((x * 3.1, k * .7, s * 1.3 + xc))) * .35
            if ((x - xc) / hw) ** 2 + ((k - kc) / hk) ** 2 < 1 + j: return True
        return False
    def cut(side, x, t):
        k = (1 - t) * RF.N_COURSE - .5
        return any(s == side and ((x - xc) / (hw - .12)) ** 2 + ((k - kc) / (hk - .25)) ** 2 < 1 for s, xc, kc, hw, hk in patches)
    cell = lambda kind, side, x, k, r: (0 if r < .5 else 1 if r < .84 else 2) + (4 if kind == 'roll' else 0)   # cell 2 = the mossy one
    for side in (-1, 1):
        RF.tiles(P, side, hole=hole, cell=cell)
        VR.underlay(P, side, cut=cut)
        VR.eave_caps(P, side)
    VR.ridge(P); VR.barge_boards(P); VR.eave_rafters(P)
    for s, xc, kc, hw, hk in patches:          # battens across each hole, one rafter under it
        D = VR.CFG['depth'][s]
        for k in range(int(kc - hk) - 1, int(kc + hk) + 2):
            t = 1 - (k + .5) / RF.N_COURSE
            RF.sweep_box('Batten', [(x, s * t * D, VR.z(x, t) - .045) for x in (xc - hw - .05, xc, xc + hw + .05)], .045, .03, P['timber'],
                         up=(0, -s * .3, 1), group='Wood', grain='x', detail=1)
        t0, t1 = 1 - (kc + hk + 1.2) / RF.N_COURSE, 1 - (kc - hk - 1.2) / RF.N_COURSE
        RF.sweep_box('Rafter', [(xc + .08, s * t * D, VR.under(xc, s * t * D) - .001) for t in (t0, (t0 + t1) / 2, t1)], .09, .12, P['timber'],
                     group='Wood', grain='y', detail=1)


# ------------------------------------------------------------------ stable (local frame at SX, SY)
def stable(P, R):
    yf, yb = -SHY, SHY
    px = [x - SX for x in (.7, 2.65, 4.6, 6.3)]
    # packed-earth floor of the bays, and a low stone kerb between the post bases (worn down where stall B is open)
    fx0, fx1 = STABLE_X0 - SX, SHX
    box('Stable_Floor', ((fx0 + fx1) / 2, -.02, .006), (fx1 - fx0, 2 * SHY - .04, .006), P['earth'], bevel=0., uvw=.35)
    for i, (a, b) in enumerate(zip(px, px[1:])):
        h = .05 if i == 1 else .1
        x = a + .16
        while x < b - .2:
            L = min(R.uniform(.45, .75), b - .16 - x)
            if b - .16 - x - L < .25: L = b - .16 - x
            rbox('Stable_Kerb', (x + L / 2, yf + .02, h / 2), (L - .015, .22, h), P['stone'][R.randrange(2)], r=.02, amp=.005, freq=2.8, hew=1, chips=1,
                 seed=400 + int(x * 20) % 97, div=.25, flat='Z', group='Stone')
            x += L
    for x in px:
        top_f = VR.under(x, yf) - .15; top_b = VR.under(x, yb - .1) - .15
        rbox('Stable_Post_Stone', (x, yf, .08), (.3, .3, .16), P['stone'][x > 0], r=.025, amp=.004, freq=3., hew=1, chips=1, seed=int(x * 70) % 89, div=.25, flat='z', group='Stone')
        cyl('Stable_Post', (x, yf, (.16 + top_f) / 2), .09, top_f - .16, P['timber'], verts=10, group='Wood', grain='z')
        box('Stable_Back_Post', (x, yb - .12, top_b / 2), (.16, .16, top_b), P['timber'], bevel=.01, seg=2, group='Wood', grain='z')
        zt = min(top_f, top_b) - .05
        box('Stable_Tie_Beam', (x, 0., zt), (.14, 2 * SHY + .1, .16), P['timber'], bevel=.012, seg=2, group='Wood', grain='y')
        zk = VR.under(x, 0.) - .02
        box('Stable_King_Post', (x, 0., (zt + zk) / 2), (.1, .1, zk - zt), P['timber'], bevel=.01, seg=1, group='Wood', grain='z')
    xs = [-SHX + .05 + (2 * SHX - .1) * i / 18 for i in range(19)]
    for y, nm in ((yf, 'Front'), (yb - .12, 'Back')):
        RF.sweep_box(f'Stable_Purlin_{nm}', [(x, y, VR.under(x, y) - .002) for x in xs], .15, .15, P['timber'], group='Wood', grain='x')
    # plank back wall
    xa, xb = -SHX + .02, SHX - .1; n = int((xb - xa) / .24)
    for i in range(n):
        x = xa + (i + .5) * (xb - xa) / n; top = VR.under(x, yb) - .02
        box('Back_Plank', (x, yb - .02, top / 2), ((xb - xa) / n - .012, .04, top), P['plank'], bevel=.004, seg=1, group='Wood', grain='z', uvw=.8)
    # right gable: two rails between the end posts, a plank gable above the tie beam
    xr = px[-1]
    for z in (.55, 1.1):
        box('End_Rail', (xr + .02, 0., z), (.08, 2 * SHY - .1, .1), P['timber'], bevel=.01, seg=2, group='Wood', grain='y')
    ys = [-SHY + .02 + (2 * SHY - .04) * j / 16 for j in range(17)]
    zt = VR.under(xr, yf) - .2
    extrude_profile('Stable_Gable', [(ys[0], zt), (ys[-1], zt)] + [(y, VR.under(xr, y) - .02) for y in ys][::-1], .04, P['plank'], plane='yz', p=(xr + .02, 0, 0),
                    bevel=0., group='Wood', grain='z')
    # partitions and gates
    for x in px[1:3]:
        for z in (.35, .75, 1.15):
            box('Partition_Board', (x, (yb - .2 + -.85) / 2, z), (.04, yb - .2 + .85, .36), P['plank'], bevel=.004, seg=1, group='Wood', grain='y', uvw=.8)
        box('Partition_Post', (x, -.85, .68), (.12, .12, 1.36), P['timber'], bevel=.01, seg=2, group='Wood', grain='z')
    gy = -.85
    def gate(name, x0, x1, rot=0., drop=0.):
        Lg = x1 - x0 - .04
        with xf(T(x0 + .02, gy, -drop) @ RZ(0.) @ __import__('mathutils').Matrix.Rotation(rot, 4, 'Y')):
            for z in (.3, .95):
                box(name + '_Rail', (Lg / 2, 0., z), (Lg, .05, .1), P['boards'], bevel=.005, seg=1, group='Wood', grain='x')
            nb = int(Lg / .16)
            for i in range(nb):
                bx = .08 + i * (Lg - .16) / max(nb - 1, 1)
                box(name + '_Board', (bx, .04, .64), (.11, .025, 1.0), P['boards'], bevel=.004, seg=1, group='Wood', grain='z', uvw=.8)
                for z in (.3, .95):     # a nail through the board into each rail (the heads show 4 mm proud)
                    cyl(name + '_Nail', (bx, .04, z), .012, .034, P['iron'], axis='y', verts=6, bevel=0., detail=1)
    for x in (px[0], px[3]):          # hanging posts for the outer gates (the inner ends hang on the partition posts)
        box('Gate_Post', (x, gy, .68), (.12, .12, 1.36), P['timber'], bevel=.01, seg=2, group='Wood', grain='z')
    gate('Gate_A', px[0] + .03, px[1] - .03)                                        # rails run 1 cm into the posts at both ends
    gate('Gate_C', px[2] + .03, px[3] - .03, rot=math.radians(9), drop=-.1)          # hanging from its upper hinge, the free end sagged to the ground
    # feed trough along the back wall in each stall, a manger rail
    for a, b in zip(px, px[1:]):
        box('Feed_Trough', ((a + b) / 2, yb - .38, .45), (b - a - .3, .42, .1), P['plank'], bevel=.006, seg=1, group='Wood', grain='x', uvw=.7)
        for y in (yb - .58, yb - .18):
            box('Trough_Side', ((a + b) / 2, y, .6), (b - a - .3, .04, .3), P['plank'], bevel=.004, seg=1, group='Wood', grain='x', uvw=.7)
        for x in (a + .2, b - .2):
            box('Trough_Leg', (x, yb - .38, .2), (.08, .36, .4), P['timber'], bevel=.006, seg=1, group='Wood', grain='z', uvw=.6)
    # straw on the floor of each stall (lumpy, low) and a few loose tufts
    for a, b in zip(px, px[1:]):
        c = Vector(((a + b) / 2 + R.uniform(-.3, .3), .6 + R.uniform(-.2, .3), 0.))
        def mound(u, v, c=c, a=a, b=b, s=R.random()):
            r = .95 * math.sqrt(.02 + .98 * u); ang = 2 * math.pi * v
            x = c.x + r * math.cos(ang) * (b - a) * .38; y = c.y + r * math.sin(ang) * 1.05
            h = .16 * (1 - u) ** 1.4 + .03 * noise.noise(Vector((x * 4 + s * 9, y * 4, 0.)))
            return (x, y, max(.004, h))
        from ti_core import surface
        surface('Straw_Litter', 10, 16, mound, P['straw'], group='Main', grain='x', closed_u=False)
        for i in range(5):
            FP.grass_tuft('Straw_Tuft', (c.x + R.uniform(-.6, .6), c.y + R.uniform(-.5, .5), .02), R.randint(6, 10), R.uniform(.12, .22), P['dry'], R, lean=.8, detail=1, spread=.12)


# ------------------------------------------------------------------ yard, hitching rail, props, weeds
def yard(P, R):
    """Worn paving: slabs of uneven size laid in loose rows, each a little turned; some missing, packed earth and grass in the gaps."""
    y0, y1 = YARD_Y; x0, x1 = -6.6, 6.5
    ya = APRON_Y                    # beside the hall the paving runs on up to the stable's post bases
    box('Yard_Earth', ((x0 + x1) / 2, (y0 + y1) / 2 + .1, .006), (x1 - x0, y1 - y0 + .2, .006), P['earth'], bevel=0., uvw=.35)
    box('Yard_Earth_Apron', ((STABLE_X0 + x1) / 2, (y1 + .2 + SY - SHY) / 2, .006), (x1 - STABLE_X0, SY - SHY - y1 - .2, .006), P['earth'], bevel=0., uvw=.35)
    y = y0 + .03
    while y < ya - .1:
        H = min(R.uniform(.42, .8), (y1 if y < y1 - .05 else ya) - y)
        apron = y > y1 - .05
        x = (STABLE_X0 + .04 if apron else x0) + R.uniform(0, .25 if apron else .4)
        while x < x1 - .1:
            L = min(R.uniform(.45, 1.05), x1 - x)
            cx, cy = x + L / 2, y + H / 2
            under_trough = 4.7 < cx < 6.3 and -1.4 < cy < -.6
            worn = abs(cx - 3.62) < .85 and cy > -1.2 and R.random() < .65            # trodden path into the open stall B
            gone = under_trough or worn or R.random() < .18                            # slabs missing, packed earth between
            if not gone:
                gap = R.uniform(.035, .09)
                rbox('Yard_Slab', (x + L / 2 + R.uniform(-.02, .02), y + H / 2 + R.uniform(-.02, .02), .03 - R.uniform(0, .015)), (L - gap, H - gap, .06),
                     P['slab'][R.randrange(2)], rot=(0, 0, R.uniform(-.05, .05)), r=.025, amp=.008, freq=2.2, hew=1, chips=1,
                     seed=int(x * 31 + y * 17) % 997, div=.35, flat='zZ', group='Stone', uvw=.7)
            elif R.random() < .7:
                FP.grass_tuft('Yard_Grass', (x + L / 2, y + H / 2, 0.), R.randint(5, 9), R.uniform(.1, .22), P['grass'] if R.random() < .6 else P['dry'], R, lean=.4, detail=1, spread=.15)
            x += L
        y += H


def hitching_rail(P, R):
    for i, x in enumerate(RAIL_POSTS):
        h = 1.15 + R.uniform(-.04, .04)
        log('Rail_Post', [(x, RAIL_Y, .0), (x + R.uniform(-.02, .02), RAIL_Y, h * .5), (x + R.uniform(-.03, .03), RAIL_Y + R.uniform(-.02, .02), h)],
            .09, P['timber'], seg=10, lump=.08, seed=40 + i, group='Wood', grain='z')
        for dz in (0., .06):
            torus('Rope_Wrap', (x, RAIL_Y, 1.0 + dz - .03), .1, .016, P['rope'], major=12, minor=5, detail=1)
    for a, b in zip(RAIL_POSTS, RAIL_POSTS[1:]):
        sag = R.uniform(.01, .04)
        log('Hitching_Rail', [(a, RAIL_Y, 1.02), ((a + b) / 2, RAIL_Y + R.uniform(-.02, .02), 1.0 - sag), (b, RAIL_Y, 1.02)], .065, P['timber'], seg=10, lump=.05,
            seed=int(a * 10) + 60, group='Wood', grain='x')
        for f in (.3, .7):
            xr = a + (b - a) * f
            torus('Tether_Ring', (xr, RAIL_Y, .86), .07, .011, P['iron'], rot=(math.pi / 2, 0, 0), major=14, minor=6)
            torus('Ring_Staple', (xr, RAIL_Y, .95), .025, .008, P['iron'], rot=(0, math.pi / 2, 0), major=8, minor=4, detail=1)


def props(P, R):
    prof = [(.21, 0), (.31, .10), (.36, .36), (.30, .58), (.18, .68), (.19, .74), (.145, .74), (.14, .66), (.25, .56), (.30, .35), (.25, .13), (.14, .07), (0., .07)]
    for name, (x, y), s in (('Jar_Large', (MX - 1.7, MY - HY - .5), .9), ('Jar_Small', (MX - 1.25, MY - HY - .42), .6)):
        lathe(name, [(r * s, z * s) for r, z in [(0., 0.)] + prof], (x, y, PL), P['clay'], seg=20)
    # stone water trough before the stable, green water stain, a crack
    tx, ty = 5.5, -1.0
    rbox('Water_Trough', (tx, ty, .28), (1.4, .55, .56), P['stone'][0], r=.03, amp=.006, freq=2.4, hew=1, chips=1, seed=91, div=.3, flat='z', group='Stone')
    box('Trough_Water', (tx, ty, .46), (1.2, .38, .02), P['mortar'], bevel=0., uvw=.3)
    # a fallen plank and a broken gate leaning on the stable post (Detail_Small)
    box('Fallen_Plank', (2.0, -.7, .03), (1.6, .2, .035), P['boards'], rot=(0, 0, .35), bevel=.004, seg=1, group='Wood', grain='x', detail=1)


def weeds(P, R):
    pts = []
    for i in range(70):
        side = R.random()
        if side < .35: x, y = R.uniform(-6.5, .4), MY - HY - .85          # plinth front edge
        elif side < .5: x, y = R.uniform(-6.5, .4), MY + HY + .2
        elif side < .6: x, y = -6.62, R.uniform(-1.3, 4.2)
        elif side < .8: x, y = R.uniform(.5, 6.4), SY + SHY + .1
        else: x, y = R.choice(RAIL_POSTS) + R.uniform(-.25, .25), RAIL_Y + R.uniform(-.2, .2)
        if abs(x - MX) < 1.2 and y < MY - HY - .5: continue          # in front of the steps: trodden bare
        FP.grass_tuft('Base_Weed', (x, y, 0.), R.randint(5, 10), R.uniform(.14, .38), P['grass'] if R.random() < .65 else P['dry'], R, lean=.4, detail=1, spread=.08)


# ------------------------------------------------------------------ collision
def collision():
    V, F = [], []
    def prism(x0, x1, y0, y1, z0, z1):
        FP.hull_loft(V, F, [[(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)] for z in (z0, z1)])
    hx0, hx1, hy0, hy1 = MX - HX - .15, MX + HX + .05, MY - HY - .8, MY + HY + .15
    prism(hx0, hx1, hy0, hy1, 0., PL)                                                    # plinth
    for j in range(3):
        h = PL * (j + 1) / 3; yy = hy0 - .3 * (3 - j)
        prism(MX - .95, MX + .95, yy, hy0, 0., h)                                         # steps
    prism(MX - HX, MX + HX, MY - HY, MY + HY, PL, WTOP)                                  # hall, door closed (the ajar leaf leaves 0.4 m)
    for x in (-HX + .2, -1.1, 1.1, HX - .2):
        prism(MX + x - .12, MX + x + .12, MY - HY - .74, MY - HY - .5, PL, 2.6)         # eave columns
    px = (.7, 2.65, 4.6, 6.3)
    for x in px: prism(x - .15, x + .15, SY - SHY - .15, SY - SHY + .15, 0., 2.2)        # stable front posts
    prism(.45, 6.42, SY + SHY - .2, SY + SHY + .02, 0., 2.2)                             # plank back wall
    prism(6.22, 6.42, SY - SHY, SY + SHY, 0., 1.2)                                       # end rails
    for x in px[1:3]: prism(x - .06, x + .06, SY - .91, SY + SHY - .2, 0., 1.35)         # partitions
    prism(px[0] + .06, px[1] - .06, SY - .89, SY - .81, 0., 1.15)                        # gate A shut
    prism(px[2] + .06, px[3] - .06, SY - .89, SY - .81, 0., 1.15)                        # gate C hanging
    for a, b in zip(px, px[1:]): prism(a + .1, b - .1, SY + SHY - .62, SY + SHY - .15, 0., .7)   # troughs
    prism(RAIL_POSTS[0] - .1, RAIL_POSTS[-1] + .1, RAIL_Y - .1, RAIL_Y + .1, 0., 1.15)   # hitching rail: nobody ducks under
    prism(4.78, 6.22, -1.3, -.7, 0., .58)                                                # water trough
    prism(MX - 2.05, MX - 1.05, MY - HY - .85, MY - HY - .2, PL, 1.1)                    # jars on the walk
    y0, y1 = YARD_Y
    prism(-6.6, 6.5, y0, y1, 0., .03)                                                    # the paving, so feet stay on the slabs
    prism(STABLE_X0, 6.5, y1 - .01, APRON_Y, 0., .03)                                    # ...and on the apron before the stable
    return V, F


# ------------------------------------------------------------------ build
def build_ps01(P):
    R = random.Random('PS01')
    yard(P, R); hitching_rail(P, R)
    VR.configure(**HALL_ROOF)
    with xf(T(MX, MY, 0.)):
        plinth(P, R); hall_walls(P, R); gables(P); eave_front(P)
        roof(P, [(-1, 1.5, 6.5, .5, 1.6), (1, -1.6, 4.0, .38, 1.1)], R)
    S['hall_roof_cfg'] = dict(S['roof_cfg'])
    VR.configure(**STABLE_ROOF)
    with xf(T(SX, SY, 0.)):
        stable(P, R)
        roof(P, [(-1, 1.2, 4.5, .55, 1.4)], R)
    S['stable_roof_cfg'] = dict(S['roof_cfg'])
    import re
    for o in S['parts']:             # the second roof's tile objects get '.001' names; keep the _LOD<n> ending the preview and LOD code look for
        m = re.fullmatch(r'Roof_Tiles_(-?1)_LOD(\d)\.\d+', o.name)
        if m: o.name = f'Roof_Tiles_Stable_{m.group(1)}_LOD{m.group(2)}'
    props(P, R); weeds(P, R)
    socket('Socket_Door', (MX, MY - HY, PL), rot=(0, 0, math.pi))
    socket('Socket_Road', (0., YARD_Y[0], 0.), rot=(0, 0, math.pi))
    socket('Socket_Yard', (0., -2.6, 0.))
    S['collision_mesh'] = collision()
    S['prop'] = dict(kind='station')
    __import__('vl_house').occluded_uvw()


def register(ASSETS):
    ASSETS['PS01_OldPostStation'] = dict(
        kind='station', zh='舊驛站', palette=palette, build=build_ps01, tex=2048, tex_atlas={'Wood': 4096}, ver='v001',
        atlases={'Main': ['Main', 'Detail_Small'], 'Stone': ['Stone'], 'Wood': ['Wood']},
        limit=[14., 10., 6.], box=((-7., -5., 0.), (7., 5., 6.)), slot='A9_OfficialRoad_South_PostStation', ref='PS01/PS01-cand-3',
        note='官道邊半荒的舊驛站（三視圖 PS01-cand-3）：左邊主屋單層，坐在 0.4 m 石台基上，牆腳亂石砌、上段褪色石灰泥，柱樑橫平豎直沒有斜撐；前簷四根簷柱下一道走廊，三級石階上到木板對開門（一扇半掩，只開 0.4 m，人進不去），兩扇直欞窗、窗紙破了。右邊一排三間開敞馬廄，矮一截的屋頂靠在主屋山牆上：木板後牆、木板隔間、料槽、地上鋪草；A 間柵門關著、B 間敞開人可以走進去、C 間柵門只剩一邊掛著。前面一片舊石板院子，縫裡長草，主屋台階前和馬廄前踩出一條較禿的路；院前一道拴馬木欄（四根柱、圓木橫桿、鐵環、纏繩），馬廄前一只石水槽。半荒但沒有塌：屋頂幾處缺瓦露出掛瓦條，灰泥剝到見石，每個牆腳長草。碰撞：台基與台階、主屋（門算關著）、簷柱、馬廄柱與後牆、隔間、A／C 柵門、料槽、拴馬欄（1.15 m 高，人不能從下面鑽）、水槽、陶缸，以及院子和馬廄前的石板面（腳踩在石板上）。',
        method='procedural mesh construction (art/source/roadside-landmarks-b/ps_station.py, vh_roof.py); procedural shaders baked to three 2048 atlases '
               '(Main, Stone, Wood); roof tiles on the shared 1024 VL tile texture (VL_Shared, read only)',
        based_on='original (Blender procedural); VL material set and roof tiles from art/source/village-houses-b')


def station_checks(aid, check, cfg):
    import bpy
    from vl_checks import _bvh
    body = _bvh([o for g, o in S['lods'][0].items() if not g.startswith('Detail_')])
    col = _bvh([S['collision_obj']])
    down = lambda x, y, f=body: (lambda h: round(h[0].z, 3) if h else None)(f((x, y, 20.), (0, 0, -1)))
    ridge_hall = down(MX - .4, MY); ridge_stable = down(SX + .4, SY); eave = down(SX, SY - SHY - .1)
    check('hall_higher_than_stable', ridge_hall and ridge_stable and ridge_hall > ridge_stable + 1.0,
          {'hall_ridge_m': ridge_hall, 'stable_ridge_m': ridge_stable, 'stable_front_eave_m': eave})
    under = col((SX, SY - .2, .05), (0, 0, 1)); stall_b = col((3.6, SY - .2, .05), (0, 0, 1))
    check('stall_b_open_and_roofed', stall_b is None or stall_b[0].z > 2.0, {'collision_above_stall_b_floor_m': round(stall_b[0].z, 3) if stall_b else None})
    rail = col((2.0, -6., .6), (0, 1, 0))
    check('hitching_rail_blocks', rail is not None and abs(rail[0].y - (RAIL_Y - .1)) < .02, {'collision_face_y_m': round(rail[0].y, 3) if rail else None})
    holes = sum(1 for o in S['lods'][0].values() for m in o.data.materials if m and 'Roof' in m.name)
    return {'hall_ridge_m': ridge_hall, 'stable_ridge_m': ridge_stable, 'roof_patches_missing': 3}
