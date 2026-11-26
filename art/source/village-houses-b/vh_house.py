"""VH01 two-storey farmhouse (work pack 2026-11-09 B-112h, batch A): a house that reads as another kind than VL01-05 from far off.

Three-view: art/references/VH01/VH01-cand-1.png (AI, Codex image_gen; proportions from the work pack's written sizes, not the image).
Size limit 8 x 7 x 7.5 m. Origin: centre of the ground-floor footprint at ground level, front -Y.

Ground floor: rubble stone walls (face stones in courses, bigger quoins at the corners) on a stone footing, a timber lintel over each
opening, a plank double door and small lattice windows. Upper floor: a timber frame (sill beam, posts, top plate, one tie rail at the
window heads, all square-on: no diagonal braces) with lime-plaster infill, set out 0.2 m past the stone walls at the sides and back on
the floor joists; in front a narrow gallery (0.7 m) on stepped cantilever beams through the stone wall, with a square-baluster rail.
Roof: the VL pan-and-roll tiles on a steeper curve (35 degrees at the ridge against VL's 29), restrained curled ridge ends.
Shared with VL01-05: the material set (vl_mats, the 'elderly' palette: old dark timber, plaster with repairs, moss on the stone),
the roof-tile texture (VL_Shared) and the three-atlas scheme (Main, Stone, Wood) of the export pipeline.
"""
import math, random
import bmesh
from mathutils import Vector
from ti_core import S, box, cyl, mesh, lathe, socket, extrude_profile, xf, T, RZ
from cr_parts import rbox, sheet
import fr_parts as FP
import vl_mats
import vl_roof as RF
import vh_roof as VR
import vh_wood as vw

# ------------------------------------------------------------------ VH01 layout (metres)
PL = .28                    # top of the stone footing = ground-floor level
STONE_TOP = 2.45            # top of the face-stone courses; a timber wall plate runs on top of them
GF_TOP = 2.65               # top of the wall plate
UF = 2.85                   # upper floor (deck top)
XW, YW = 3.2, 2.3           # stone walls: outer face lines (face stones stand 0.09 proud of them)
WT = .42                    # stone wall thickness
XU, YUB = 3.42, 2.52        # upper floor: side and back outer faces (about 0.1 m past the stone faces, plaster face)
GAL = -3.0                  # gallery edge line
UT = 5.0                    # top of the upper-floor top plate
ROOF = dict(z0=5.25, rise=1.75, depth_front=3.45, depth_back=3.0, xh=3.72, lift_end=.12)
PROUD = .09

WALLS_GF = {   # name: ((x, y), angle, length along the wall, openings (cx, w, sill, head, kind)) in wall-local x
    'Front': ((0., -YW), 0., 2 * XW, [(-2.0, .75, 1.15, 1.85, 'window'), (0., 1.1, PL, 2.2, 'door'), (2.0, .75, 1.15, 1.85, 'window')]),
    'Rear': ((0., YW), math.pi, 2 * XW, [(-.9, .7, 1.2, 1.85, 'window')]),
    'Right': ((XW, 0.), math.pi / 2, 2 * YW, [(.7, .6, 1.25, 1.85, 'window')]),
    'Left': ((-XW, 0.), -math.pi / 2, 2 * YW, [(-.7, .6, 1.25, 1.85, 'window')]),
}
WALLS_UF = {
    'Front': ((0., -YW), 0., 2 * XU, [(-2.2, 1.0, 3.55, 4.35, 'window'), (0., .9, UF, 4.7, 'door'), (2.2, 1.0, 3.55, 4.35, 'window')], (-XU, -1.1, 1.1, XU)),
    'Rear': ((0., YUB), math.pi, 2 * XU, [(-1.55, .9, 3.6, 4.35, 'window'), (1.55, .9, 3.6, 4.35, 'window')], (-XU, 0., XU)),
    'Right': ((XU, (YUB - YW) / 2), math.pi / 2, YUB + YW, [(0., .9, 3.6, 4.35, 'window')], (-(YUB + YW) / 2, -.85, .85, (YUB + YW) / 2)),
    'Left': ((-XU, (YUB - YW) / 2), -math.pi / 2, YUB + YW, [(0., .9, 3.6, 4.35, 'window')], (-(YUB + YW) / 2, -.85, .85, (YUB + YW) / 2)),
}
GAL_POSTS = (-3.3, -1.1, 1.1, 3.3)


def frame(d, name):
    (wx, wy), a, L, ops = d[name][:4]
    return T(wx, wy, 0) @ RZ(a), L, ops


def palette():
    P = vl_mats.palette('elderly')
    vw.apply(P, 'elderly')                                   # weathered timber, plank doors (vh_wood.py)
    P['roof'] = RF.roof_material()
    cm = __import__('cr_mats')
    # ground-floor rubble: the VL valley stones (cool blue-grey) mixed with warmer grey field stone, a lime mortar lighter than VL's plinth joints
    P['stone'] = P['stone'] + [cm.stone('Wall_Stone_Dark', light=vl_mats.STONE[0], dark=(.045, .055, .05), ochre=(.2, .18, .14), moss=.9, lichen=.6, crack=.5)]
    P['wall_stone'] = P['stone'][:2] + [cm.stone('Wall_Stone_Warm', light=(.2, .19, .165), dark=(.085, .08, .07), ochre=(.24, .2, .14), moss=.7, lichen=.6, crack=.5),
                                        cm.stone('Wall_Stone_Field', light=(.16, .16, .145), dark=(.07, .07, .065), ochre=(.2, .18, .13), moss=.8, lichen=.5, crack=.6),
                                        P['stone'][2]]
    P['wall_mortar'] = __import__('ti_mats').plain('Wall_Mortar', (.12, .115, .1), rough=.92, noise=.35)
    return P


# ------------------------------------------------------------------ generic slab with openings (plaster or mortar core)
def slab(name, L, ops, z0, z1, y0, y1, mat_out, mat_in, uv_in=.12, xr=None):
    """Closed slab of one wall in wall-local coordinates (exterior face at y0, interior at y1), openings as reveals."""
    xa, xb = xr or (-L / 2, L / 2)
    xs = {xa, xb}; zs = {z0, z1}
    for cx, w, sill, head, kind in ops:
        xs |= {cx - w / 2, cx + w / 2}; zs |= {max(z0, sill), min(z1, head)}
    xs, zs = sorted(xs), sorted(zs)
    def opening(x, z):
        return any(cx - w / 2 < x < cx + w / 2 and sill < z < head for cx, w, sill, head, kind in ops)
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


# ------------------------------------------------------------------ ground floor: footing and rubble stone walls
def footing(P, R):
    """Stone footing 0.12 m proud of the wall faces, flat dressed stones in one course; a step and a threshold at the door."""
    box('Footing_Core', (0., 0., PL / 2 - .01), (2 * XW + .2, 2 * YW + .2, PL - .02), P['mortar'], bevel=0., uvw=.15)
    k = [0]
    def blk(c, s, flat='Z'):
        rbox('Footing_Stone', c, s, P['stone'][k[0] % 3], r=.025, amp=.006, freq=2.5, hew=1, chips=1, seed=k[0], div=.25, flat=flat, group='Stone'); k[0] += 1
    X, Y = XW + .12, YW + .12
    def run(a, b, fixed, along_x):
        x = a
        while x < b - .05:
            L = min(R.uniform(.55, .95), b - x)
            if b - x - L < .3: L = b - x
            c = x + L / 2
            blk((c, fixed, PL / 2) if along_x else (fixed, c, PL / 2), (L - .015, .3, PL) if along_x else (.3, L - .015, PL))
            x += L
    run(-X, X, -Y + .15, True); run(-X, X, Y - .15, True)
    run(-Y + .3, Y - .3, -X + .15, False); run(-Y + .3, Y - .3, X - .15, False)
    # entry step and threshold
    for j, xc in enumerate((-.45, .45)):
        rbox('Entry_Step', (xc, -Y - .17, .07), (.88, .34, .14), P['stone'][j], r=.02, amp=.004, freq=3., hew=1, seed=60 + j, div=.25, flat='zZ', group='Stone')
    rbox('Door_Threshold', (0., -YW + .1, PL + .04), (1.3, .26, .08), P['stone'][2], r=.015, amp=.002, freq=3., hew=0, seed=70, div=.25, flat='zZ', group='Stone')


def courses(R):
    """One set of course heights for all four walls, so the quoins of two walls meet course for course at each corner."""
    out = []; z = PL
    while z < STONE_TOP - .05:
        h = R.uniform(.2, .36)
        if STONE_TOP - (z + h) < .16: h = STONE_TOP - z
        out.append((z, z + h)); z += h
    return out


def stone_wall(P, R, wname, COURSES):
    """Face stones laid in courses on the wall-local face (exterior -y), bigger quoins at both ends; mortar core behind; plaster inside;
    a timber wall plate on top. At a corner the quoin of one wall runs to the corner and the other wall's stops behind it, swapping
    every course."""
    M, L, ops = frame(WALLS_GF, wname)
    long_wall = wname in ('Front', 'Rear')
    seed0 = sum(map(ord, wname))
    with xf(M):
        slab(f'Wall_Core_{wname}', L, ops, PL, STONE_TOP, -.05, WT, P['wall_mortar'], P['plaster_in'])   # the wall plate sits on it, full depth
        box(f'Wall_Plate_{wname}', (0., (WT - .08) / 2, (STONE_TOP + GF_TOP) / 2), (L + (2 * PROUD + .02 if long_wall else -(2 * WT + .01)), WT + .08, GF_TOP - STONE_TOP), P['timber'],
            bevel=.014, seg=2, group='Wood', grain='x')
        # timber lintels and frames first, the courses keep clear of them
        blocked = []
        for cx, w, sill, head, kind in ops:
            lw = w + .5
            box(f'Lintel_{wname}', (cx, -.04, head + .08), (lw, .2, .2), P['timber'], bevel=.012, seg=2, group='Wood', grain='x')   # 2 cm into the opening: no face shared with the reveal
            blocked.append((cx - w / 2 - .02, cx + w / 2 + .02, sill - (0 if kind == 'door' else .08), head))
            blocked.append((cx - lw / 2 - .01, cx + lw / 2 + .01, head, head + .19))
            if kind == 'window':
                rbox(f'Window_Sill_{wname}', (cx, -.06, sill - .05), (w + .24, .26, .1), P['stone'][1], r=.015, amp=.002, freq=3., hew=1,
                     seed=sum(map(ord, wname)) % 50 + int(cx * 10), div=.25, flat='Z', group='Stone')
                gf_window(P, f'Window_GF_{wname}_{cx:+.1f}', cx, sill, w, head - sill)
        k = 0
        ext = L / 2 + PROUD
        for c, (z0, z1) in enumerate(COURSES):
            h = z1 - z0
            # quoins: the wall that owns the corner this course runs its quoin out to the corner, the other stops behind it
            own = (c % 2 == 0) == long_wall
            q = .6 if own else .42
            qa = ext - (0. if own else 2 * PROUD + .02)          # outer end of this wall's quoin
            free = [(-qa + q, qa - q)]
            for a, b, s0, s1 in blocked:
                if s1 <= z0 + .01 or s0 >= z1 - .01: continue
                nf = []
                for fa, fb in free:
                    if b <= fa or a >= fb: nf.append((fa, fb)); continue
                    if a > fa: nf.append((fa, a))
                    if b < fb: nf.append((b, fb))
                free = nf
            for side in (-1, 1):          # quoins
                qx = side * (qa - q / 2)
                rbox(f'Quoin_{wname}', (qx, -.0, (z0 + z1) / 2), (q - .02, .2, h - .02), P['wall_stone'][(c + (side > 0)) % 4], r=.03, amp=.009, freq=2.2,
                     hew=2, chips=1, seed=1000 + c * 7 + side + seed0, div=.3, group='Stone')
            W = P['wall_stone']
            pick = lambda: W[R.choices(range(5), (3, 2, 3, 3, 1))[0]]
            for fa, fb in free:
                x = fa
                while x < fb - .04:
                    Ls = min(R.uniform(.3, .78), fb - x)
                    if fb - x - Ls < .22: Ls = fb - x
                    if Ls < .1: break
                    if h > .27 and Ls < .5 and R.random() < .35:
                        # two small stones stacked in one course (snecked rubble), so the face does not read as brick courses
                        zs = z0 + h * R.uniform(.4, .6)
                        for a, b in ((z0, zs), (zs, z1)):
                            Lp = Ls - R.uniform(0, .06)
                            rbox(f'Wall_Stone_{wname}', (x + Lp / 2, -.01 + R.uniform(-.008, .008), (a + b) / 2), (Lp - .022, R.uniform(.14, .17), b - a - .022),
                                 pick(), r=.025, amp=.009, freq=2.6, hew=2, chips=1, seed=k + seed0 * 7, div=.3, group='Stone'); k += 1
                        x += Ls; continue
                    hh = h - .02 - R.uniform(0, .03); dz = R.uniform(-.008, .008)
                    rbox(f'Wall_Stone_{wname}', (x + Ls / 2, -.01 + R.uniform(-.008, .008), (z0 + z1) / 2 + dz), (Ls - .022, R.uniform(.15, .18), hh),
                         pick(), r=.03, amp=.01, freq=2.4, hew=2, chips=1, seed=k + seed0 * 7, div=.3, group='Stone')
                    x += Ls; k += 1


def gf_window(P, name, cx, sill, w, h):
    """Small ground-floor window: timber frame, plain vertical bars, paper behind."""
    zc = sill + h / 2
    for x in (cx - w / 2 + .05, cx + w / 2 - .05):
        box(name + '_Jamb', (x, .02, zc), (.1, .16, h), P['timber'], bevel=.01, seg=2, group='Wood', grain='z')
    box(name + '_Rail', (cx, .02, sill + .04), (w, .16, .08), P['timber'], bevel=.01, seg=2, group='Wood', grain='x')
    box(name + '_Head', (cx, .02, sill + h - .04), (w, .16, .08), P['timber'], bevel=.01, seg=2, group='Wood', grain='x')
    n = 5
    for j in range(1, n):
        box(name + '_Bar', (cx - w / 2 + .1 + j * (w - .2) / n, -.0, zc), (.03, .04, h - .12), P['timber'], bevel=0., group='Wood', grain='z')
    sheet(name + '_Paper', 4, 4, lambda u, v: (cx - w / 2 + .08 + (w - .16) * u, .06, sill + .07 + (h - .14) * v), P['paper'], solid=.003, grain='x')


def gf_door(P):
    """Plank double door in a timber frame, set back in the stone reveal; iron rings."""
    M, L, ops = frame(WALLS_GF, 'Front')
    cx, w, sill, head, kind = ops[1]
    with xf(M):
        for x in (cx - w / 2 + .06, cx + w / 2 - .06):
            box('Door_Jamb', (x, .08, (sill + head) / 2), (.12, .2, head - sill), P['timber'], bevel=.012, seg=2, group='Wood', grain='z')
        rnd = random.Random(2120)
        for side in (-1, 1):
            xl = side * (w / 2 - .12) / 2
            # separate boards with ledges across the outside (vh_wood.plank_leaf)
            vw.plank_leaf('Door_Leaf', xl, .12, PL + .01, (w - .24) / 2 - .01, head - PL - .02, .05, P['door'], rnd, battens=(PL + .35, head - .35), batten_side=-1, uvw=1.4)
            from ti_core import torus
            torus('Door_Ring', (side * .09, .07, 1.25), .055, .01, P['iron'], rot=(math.pi / 2, 0, 0), major=14, minor=6)
            box('Door_Plate', (side * .09, .085, 1.3), (.09, .01, .12), P['iron'], bevel=.004, seg=1)


# ------------------------------------------------------------------ floor: joists, deck, cantilever beams under the gallery
def floor(P, R):
    zt = UF; zb = GF_TOP
    box('Deck', (0., (GAL - .06 + YUB) / 2, zt - .03), (2 * XU + .02, YUB - GAL + .06, .06), P['plank'], bevel=.004, seg=1, grain='x', uvw=.5)
    nj = 13
    for i in range(nj):
        x = -XU + .1 + i * (2 * XU - .2) / (nj - 1)
        box('Joist', (x, (GAL + YUB) / 2, zb + .08), (.12, YUB - GAL - .02, .16), P['timber'], bevel=.01, seg=1, group='Wood', grain='y', uvw=.5)
    for y, nm in ((GAL - .03, 'Gallery_Edge_Beam'), (YUB - .05, 'Rear_Edge_Beam')):
        box(nm, (0., y, zb + .09), (2 * XU + .1, .14, .2), P['timber'], bevel=.012, seg=2, group='Wood', grain='x')
    for x in (-XU + .05, XU - .05):
        box('Side_Edge_Beam', (x, (GAL + YUB) / 2, zb + .09), (.14, YUB - GAL, .2), P['timber'], bevel=.012, seg=2, group='Wood', grain='y')
    # stepped cantilever beams (挑枋) through the wall plate under the gallery, a short corbel under each; square ends
    y_in, y_out = -YW + .3, GAL - .12
    for x in (-3.0, -1.1, 1.1, 3.0):
        box('Cantilever_Beam', (x, (y_in + y_out) / 2, zb - .1), (.16, y_in - y_out, .22), P['timber'], bevel=.012, seg=2, group='Wood', grain='y')
        box('Cantilever_Corbel', (x, (-YW - PROUD - .45 + -YW - PROUD) / 2, zb - .29), (.14, .45, .16), P['timber'], bevel=.012, seg=2, group='Wood', grain='y')
    for x in (-2.95, 2.95):
        box('Rear_Corbel', (x, YW + .1, zb - .1), (.16, .34, .22), P['timber'], bevel=.012, seg=2, group='Wood', grain='y')
    for y in (-1.2, 1.2):
        for sx in (-1, 1):
            box('Side_Corbel', (sx * (XW + .1), y, zb - .1), (.34, .16, .22), P['timber'], bevel=.012, seg=2, group='Wood', grain='x')


# ------------------------------------------------------------------ upper floor: timber frame with plaster infill
def upper_walls(P, R):
    for wname in WALLS_UF:
        M, L, ops = frame(WALLS_UF, wname)
        posts = WALLS_UF[wname][4]
        with xf(M):
            top = UT
            slab(f'Upper_Plaster_{wname}', L, ops, UF + .14, top - .1, .025, .16, P['plaster'], P['plaster_in'], xr=(-L / 2 + .05, L / 2 - .05))
            box(f'Upper_Sill_{wname}', (0., .04, UF + .07), (L + (.0 if wname in ('Front', 'Rear') else -.02), .2, .14), P['timber'], bevel=.012, seg=2, group='Wood', grain='x')
            box(f'Upper_Plate_{wname}', (0., .04, top - .075), (L + (.12 if wname in ('Front', 'Rear') else -.03), .2, .15), P['timber'], bevel=.012, seg=2, group='Wood', grain='x')
            heads = sorted({head for cx, w, sill, head, kind in ops if kind == 'window'})
            zr = heads[0] + .075 if heads else 4.4          # tie bottom 1.5 cm above the opening soffit (behind the window head board)
            # tie rail at the window heads, broken by the door
            xs = [-L / 2 + .09]
            for cx, w, sill, head, kind in ops:
                if kind == 'door' and head > zr - .06: xs += [cx - w / 2 - .06, cx + w / 2 + .06]
            xs.append(L / 2 - .09)
            for a, b in zip(xs[::2], xs[1::2]):
                box(f'Upper_Tie_{wname}', ((a + b) / 2, .03, zr), (b - a, .17, .12), P['timber'], bevel=.01, seg=2, group='Wood', grain='x')
            for px in posts:
                pxc = max(-L / 2 + .09, min(L / 2 - .09, px))
                box(f'Upper_Post_{wname}', (pxc, .035, (UF + top) / 2), (.18, .19, top - UF - .02), P['timber'], bevel=.014, seg=2, group='Wood', grain='z')
            for cx, w, sill, head, kind in ops:
                if kind == 'window': uf_window(P, f'Window_UF_{wname}_{cx:+.1f}', cx, sill, w, head - sill)
                else: uf_door(P, cx, w, head)


def uf_window(P, name, cx, sill, w, h):
    """Upper window: timber frame, plain vertical lattice (seven bars), paper behind; a narrow timber sill board."""
    zc = sill + h / 2
    for x in (cx - w / 2 - .04, cx + w / 2 + .04):
        box(name + '_Jamb', (x, .0, zc), (.09, .15, h + .1), P['timber'], bevel=.01, seg=2, group='Wood', grain='z')
    box(name + '_Sill', (cx, -.02, sill - .03), (w + .2, .2, .07), P['timber'], bevel=.01, seg=2, group='Wood', grain='x')
    box(name + '_Head', (cx, .0, sill + h + .03), (w + .14, .15, .07), P['timber'], bevel=.01, seg=2, group='Wood', grain='x')
    n = 8
    for j in range(1, n):
        box(name + '_Bar', (cx - w / 2 + j * w / n, -.01, zc), (.028, .045, h - .02), P['timber'], bevel=0., group='Wood', grain='z')
    for zf in (sill + .02, sill + h - .02):
        box(name + '_Bar_Rail', (cx, -.01, zf), (w, .04, .03), P['timber'], bevel=0., group='Wood', grain='x')
    sheet(name + '_Paper', 5, 4, lambda u, v: (cx - w / 2 + w * u, .04, sill + h * v), P['paper'], solid=.003, grain='x')


def uf_door(P, cx, w, head):
    for x in (cx - w / 2 - .05, cx + w / 2 + .05):
        box('Upper_Door_Jamb', (x, .0, (UF + head) / 2), (.1, .16, head - UF), P['timber'], bevel=.01, seg=2, group='Wood', grain='z')
    box('Upper_Door_Head', (cx, .0, head + .035), (w + .2, .16, .08), P['timber'], bevel=.01, seg=2, group='Wood', grain='x')
    vw.plank_leaf('Upper_Door_Leaf', cx, .07, UF + .01, w - .02, head - UF - .02, .05, P['door'], random.Random(2970), battens=(UF + .3, (UF + head) / 2, head - .3),
                  batten_side=-1, uvw=1.2)


def gables(P):
    """Plaster gable above the side top plates, following the board underside, with a king post and a collar tie (square-on)."""
    for sx in (-1, 1):
        x = sx * (XU - .08)
        ys = [-YW + .02 + (YUB + YW - .04) * j / 24 for j in range(25)]
        prof = [(y, VR.under(x, y) - .02) for y in ys]
        pts = [(ys[0], UT - .02), (ys[-1], UT - .02)] + prof[::-1]
        extrude_profile(f'Gable_{sx}', pts, .14, P['plaster'], plane='yz', p=(x, 0, 0), bevel=0., grain='y')
        rake = [(x + sx * .05, y, VR.under(x, y) - .001) for y, _ in prof]
        RF.sweep_box(f'Gable_Rake_{sx}', rake, .16, .14, P['timber'], group='Wood', grain='y')
        zk = VR.under(x, 0.) - .1
        box('Gable_King_Post', (x + sx * .06, 0., (UT + zk) / 2), (.08, .16, zk - UT), P['timber'], bevel=.01, seg=2, group='Wood', grain='z')
        zc = UT + (zk - UT) * .45
        y_c = [y for y, zz in prof if zz > zc + .05]
        box('Gable_Collar', (x + sx * .06, (y_c[0] + y_c[-1]) / 2, zc), (.08, y_c[-1] - y_c[0], .13), P['timber'], bevel=.01, seg=2, group='Wood', grain='y')


def eave_infill(P):
    """Boards on the front and back upper wall lines closing the gap from the top plate to the roof boards."""
    for y, side in ((-YW + .04, -1), (YUB - .04, 1)):
        x0, x1 = -XU + .1, XU - .1
        n = 14; V = []; F = []
        for q in range(n + 1):
            x = x0 + (x1 - x0) * q / n; zt = VR.under(x, y) + .005
            for yy in (y - .05, y + .05):
                V.append((x, yy, UT - .01)); V.append((x, yy, zt))
        for q in range(n):
            a = q * 4; b = a + 4
            F += [(a, b, b + 1, a + 1), (a + 2, a + 3, b + 3, b + 2), (a + 1, b + 1, b + 3, a + 3), (a, a + 2, b + 2, b)]
        F += [(0, 1, 3, 2), (n * 4, n * 4 + 2, n * 4 + 3, n * 4 + 1)]
        o = mesh(f'Eave_Infill_{side}', V, F, P['timber'], group='Wood', grain='x')
        bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()


# ------------------------------------------------------------------ gallery: posts, eave purlin, square-baluster rail
def gallery(P):
    yp = GAL + .06
    for x in GAL_POSTS:
        top = VR.under(x, yp) - .17
        box('Gallery_Post', (x, yp, (UF + top) / 2), (.15, .15, top - UF), P['timber'], bevel=.012, seg=2, group='Wood', grain='z')
    xs = [-XU + .05 + (2 * XU - .1) * i / 20 for i in range(21)]
    RF.sweep_box('Eave_Purlin', [(x, yp, VR.under(x, yp) - .002) for x in xs], .17, .17, P['timber'], group='Wood', grain='x')
    RF.sweep_box('Wall_Purlin', [(x, -YW + .05, VR.under(x, -YW + .05) - .002) for x in xs], .14, .12, P['timber'], group='Wood', grain='x', uvw=.4)
    for x in GAL_POSTS[:1] + GAL_POSTS[-1:]:
        RF.sweep_box('Gallery_Tie', [(x, yp, VR.under(x, yp) - .2), (x, -YW + .05, VR.under(x, -YW + .05) - .2)], .1, .12, P['timber'], group='Wood', grain='y')
    rail_h = UF + .92
    def rail(a, b):
        A, B = Vector(a), Vector(b); L = (B - A).length; d = (B - A).normalized()
        alongx = abs(d.x) > .5
        c = (A + B) / 2
        box('Gallery_Rail', (c.x, c.y, rail_h), (L, .09, .07) if alongx else (.09, L, .07), P['timber'], bevel=.01, seg=2, group='Wood', grain='x' if alongx else 'y')
        box('Gallery_Bottom_Rail', (c.x, c.y, UF + .06), (L, .07, .07) if alongx else (.07, L, .07), P['timber'], bevel=.008, seg=1, group='Wood', grain='x' if alongx else 'y')
        n = max(2, int(L / .13))
        for i in range(1, n):
            p = A + (B - A) * (i / n)
            box('Gallery_Baluster', (p.x, p.y, (UF + .1 + rail_h - .035) / 2), (.035, .035, rail_h - .035 - UF - .1), P['timber'], bevel=0., group='Wood', grain='z', uvw=.6)
    for a, b in zip(GAL_POSTS, GAL_POSTS[1:]):
        rail((a + .075, yp, 0), (b - .075, yp, 0))
    for x in (GAL_POSTS[0], GAL_POSTS[-1]):
        rail((x, yp + .075, 0), (x, -YW - .02, 0))


# ------------------------------------------------------------------ lived-in, unadorned: a few things by the door
def props(P, R):
    prof = [(.21, 0), (.31, .10), (.36, .36), (.30, .58), (.18, .68), (.19, .74), (.145, .74), (.14, .66), (.25, .56), (.30, .35), (.25, .13), (.14, .07), (0., .07)]
    for name, (x, y), s in (('Jar_Large', (1.25, -YW - .45), .95), ('Jar_Small', (1.78, -YW - .38), .62)):
        lathe(name, [(r * s, z * s) for r, z in [(0., 0.)] + prof], (x, y, 0.), P['clay'], seg=20)
    # split firewood poles leaning on the stone wall left of the door
    for i in range(6):
        x = -1.15 - i * .085 + R.uniform(-.02, .02); lean = .38 + R.uniform(-.04, .05); L = R.uniform(1.55, 1.85)
        a = Vector((x, -YW - .1 - lean, .0)); b = Vector((x + R.uniform(-.06, .06), -YW - .1, L * .92))
        from cr_parts import log
        log('Firewood_Pole', [tuple(a), tuple(a + (b - a) * .5), tuple(b)], R.uniform(.028, .04), P['timber'], seg=8, lump=.06, seed=i, group='Wood', grain='y')
    # a cloth airing over the gallery rail (Detail_Small)
    rail_h = UF + .92; x0 = -2.55
    cloth = __import__('cr_mats').canvas('Cloth_Faded', base=(.33, .3, .24), stain=(.14, .11, .07), faded=.6, dirt=.6)
    def drape(u, v):
        s = (v - .5) * 2                                   # -1 front hem .. +1 back hem, over the rail at 0
        y = GAL + .06 + math.copysign(.055 + .02 * abs(s), s) * min(1., abs(s) * 6)
        return (x0 + .7 * u + .015 * math.sin(v * 7.), y, rail_h + .045 - .52 * abs(s) ** 1.3 + .015 * math.sin(u * 9. + v * 3.))
    sheet('Airing_Cloth', 7, 12, drape, cloth, solid=.004, detail=1, grain='x')


def growth(P, R):
    """Grass at the footing, moss low on the stones (Detail_Small)."""
    for i in range(30):
        side = R.choice(('front', 'back', 'left', 'right'))
        X, Y = XW + .25, YW + .25
        if side == 'front': x, y = R.uniform(-X, X), -Y
        elif side == 'back': x, y = R.uniform(-X, X), Y
        else: x, y = (X if side == 'right' else -X), R.uniform(-Y, Y)
        if side == 'front' and abs(x) < 1.0: continue
        if side == 'front' and .9 < x < 2.1: continue          # the jars
        FP.grass_tuft('Footing_Grass', (x, y, 0.), R.randint(4, 8), R.uniform(.1, .24), P['grass'] if R.random() < .7 else P['dry'], R, lean=.35, detail=1, spread=.05)
    for i in range(14):
        side = R.choice(((0, -1), (0, 1), (-1, 0), (1, 0)))
        if side[1]: x, y = R.uniform(-XW + .3, XW - .3), side[1] * (YW + .6)
        else: x, y = side[0] * (XW + .6), R.uniform(-YW + .3, YW - .3)
        zq = R.uniform(.3, .7)
        hit = FP.snap((x, y, zq), (-side[0], -side[1], 0))
        if hit: FP.moss_patch('Stone_Moss', tuple(hit[0]), tuple(hit[1]), R.uniform(.06, .12), P['moss'], seed=i, flat=.8, detail=1)


# ------------------------------------------------------------------ collision
def collision():
    V, F = [], []
    def prism(x0, x1, y0, y1, z0, z1):
        FP.hull_loft(V, F, [[(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)] for z in (z0, z1)])
    prism(-XW - .12, XW + .12, -YW - .12, YW + .12, 0., PL)                 # footing
    prism(-.9, .9, -YW - .46, -YW - .12, 0., .14)                            # step
    # stone storey, door closed: flush with the footing box, so there is no 3 cm ledge at 0.28 m for a 0.3 m step offset to catch on
    prism(-XW - .12, XW + .12, -YW - .12, YW + .12, PL, GF_TOP)
    prism(-XU, XU, GAL - .05, YUB, GF_TOP - .2, UT)                          # upper storey and gallery: out of reach, closed
    prism(-1.68, -1.02, -2.88, -YW - PROUD, 0., 1.6)                          # firewood poles against the wall
    prism(.9, 1.6, -3.1, -2.4, 0., .7)                                       # the large jar
    prism(1.55, 2.01, -2.91, -2.45, 0., .46)                                 # the small jar
    return V, F


# ------------------------------------------------------------------ build
def build_vh01(P):
    R = random.Random('VH01')
    VR.configure(**ROOF)
    footing(P, R)
    C = courses(R)
    for w in WALLS_GF: stone_wall(P, R, w, C)
    gf_door(P)
    floor(P, R)
    upper_walls(P, R)
    gables(P)
    eave_infill(P)
    gallery(P)
    def cell(kind, side, x, k, r):          # old roof kept up: old and dark-fired tiles, a little moss low on the back slope
        if side == 1 and k < 4 and r < .25: return 2 + (4 if kind == 'roll' else 0)
        if side == -1 and abs(x - 1.4) < .4 and abs(k - 6) <= 1 and r < .8: return 3 + (4 if kind == 'roll' else 0)
        return (0 if r < .6 else 1) + (4 if kind == 'roll' else 0)
    VR.build(P, cell=cell)
    props(P, R)
    growth(P, R)
    socket('Socket_Door', (0., -YW, PL), rot=(0, 0, math.pi))
    socket('Socket_Path', (0., -YW - .34, 0.), rot=(0, 0, math.pi))
    socket('Socket_Gallery', (0., -2.65, UF))
    S['collision_mesh'] = collision()
    S['prop'] = dict(kind='vhouse')
    __import__('vl_house').occluded_uvw()      # faces nobody can see (board tops under the tiles, faces against a beam) get little atlas


NOTES = {
    'VH01_TwoStoreyHouse': '兩層民居（三視圖 VH01-cand-1）：底層亂石砌牆（石塊分層砌、轉角用大塊角石、每個門窗上一根木過樑），石基高 0.28 m、門前一級石階；'
        '木板對開門、兩扇小直欞窗。二層是木構架（地栿、柱、頂樑、窗頂一道穿枋，全是橫平豎直，沒有斜撐）加石灰泥牆，兩側和後面在樓板樑上往外出挑 0.2 m；'
        '正面一道 0.7 m 窄外廊，由穿過石牆的兩層挑枋托住，方木欄杆。屋頂用 VL 的筒瓦與板瓦，坡度比 VL 陡（屋脊處約 35 度，VL 約 29 度），屋脊兩端低調起翹。'
        '舊而深色的木頭、補過的灰泥、石腳長苔；門邊兩只陶缸、幾根靠牆的柴、外廊欄杆上晾一塊布（布和草、苔在 Detail_Small）。'
        '碰撞：石基、台階、整個石砌一層（門關著）、二層連外廊一整塊（人上不去）。',
}


def register(ASSETS):
    ASSETS['VH01_TwoStoreyHouse'] = dict(
        zh='兩層民居', kind='vhouse', cond='elderly', palette=palette, build=build_vh01, limit=(8., 7., 7.5), tex=2048, ver='v001',
        box=((-4., -3.5, 0.), (4., 3.5, 7.5)), ref='VH01/VH01-cand-1', slot='A1_QingxiVillage_House', minTier='standard', clamp_max=.03, uv_shape='CONVEX',
        atlases={'Main': ['Main', 'Detail_Small'], 'Stone': ['Stone'], 'Wood': ['Wood']},
        origin='centre of the ground-floor stone walls at ground level, front -Y',
        method='procedural mesh construction (art/source/village-houses-b/vh_house.py, vh_roof.py); procedural shaders baked to three 2048 atlases (Main, Stone, Wood); roof tiles on the shared 1024 VL tile texture (VL_Shared)',
        based_on='new outline (work pack 2026-11-09 VH01); materials and roof tiles shared with VL01-05',
        note=NOTES['VH01_TwoStoreyHouse'])


# ------------------------------------------------------------------ measured checks (read off the exported LOD0 by rays)
def vhouse_checks(aid, check, cfg):
    import bpy, numpy as np
    from vl_checks import _bvh
    objs = list(S['lods'][0].values()); cast = _bvh(objs)
    body = _bvh([o for g, o in S['lods'][0].items() if not g.startswith('Detail_')])
    col = _bvh([S['collision_obj']]) if S.get('collision_obj') else None
    hit = lambda p, d, ax, f=body: (lambda h: round(h[0][ax], 3) if h else None)(f(p, d))
    gf = {'front': hit((-1.2, -12, 1.6), (0, 1, 0), 1), 'rear': hit((-1.2, 12, 1.0), (0, -1, 0), 1), 'left': hit((-12, -.6, 1.0), (1, 0, 0), 0), 'right': hit((12, -.6, 1.0), (-1, 0, 0), 0)}
    want_gf = {'front': -YW - PROUD, 'rear': YW + PROUD, 'left': -XW - PROUD, 'right': XW + PROUD}
    check('ground_floor_stone_walls', all(v is not None and abs(v - want_gf[k]) < .05 for k, v in gf.items()),
          {'face_stone_hits_m': gf, 'design_m': want_gf, 'tolerance_m': .05, 'note': 'rays at 1.0-1.6 m on a pier; face stones are rough, 0.05 m allowed'})
    uf = {'left': hit((-12, .9, 3.3), (1, 0, 0), 0), 'right': hit((12, .9, 3.3), (-1, 0, 0), 0), 'rear': hit((-.4, 12, 3.3), (0, -1, 0), 1)}
    over = {'left': round(-uf['left'] - (XW + PROUD), 3) if uf['left'] else None, 'right': round(uf['right'] - (XW + PROUD), 3) if uf['right'] else None,
            'rear': round(uf['rear'] - (YW + PROUD), 3) if uf['rear'] else None}
    check('upper_floor_overhangs', all(v is not None and v > .05 for v in over.values()), {'upper_face_hits_m': uf, 'overhang_past_stone_faces_m': over})
    deck = cast((-.5, -2.65, 6.0), (0, 0, -1))
    deck_z = None
    if deck:
        h2 = body((-.5, -2.65, 4.5), (0, 0, -1)); deck_z = round(h2[0].z, 3) if h2 else None
    rail = hit((-.5, -12, UF + .9), (0, 1, 0), 1)
    head = cast((-.5, -2.75, UF + .2), (0, 0, 1)); headroom = round(head[0].z - UF, 3) if head else None
    check('front_gallery', deck_z is not None and abs(deck_z - UF) < .01 and rail is not None and rail < GAL + .2 and headroom and headroom > 2.0,
          {'deck_top_m': deck_z, 'rail_face_y_m': rail, 'gallery_edge_m': GAL, 'headroom_under_eave_m': headroom})
    zr = lambda y: (lambda h: h[0].z if h else None)(cast((-.6, y, 12.), (0, 0, -1)))
    za, zb = zr(-.4), zr(-.9)
    slope = math.degrees(math.atan2(za - zb, .5)) if za and zb else None
    vl = lambda d: 3.40 + 1.60 * (1 - d / 3.95) ** 1.35            # StarterHouse / VL01-05 front slope at d m from the ridge
    vl_slope = math.degrees(math.atan2(vl(.4) - vl(.9), .5))
    check('roof_steeper_than_vl', slope is not None and slope > vl_slope + 3, {'vh_front_slope_deg_0.4_to_0.9m_from_ridge': round(slope, 1) if slope else None,
          'vl_same_span_deg': round(vl_slope, 1)})
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        e = o.evaluated_get(dg); m = e.to_mesh()
        co = np.zeros(len(m.vertices) * 3, np.float32); m.vertices.foreach_get('co', co); co = co.reshape(-1, 3); e.to_mesh_clear()
        lo = Vector(np.minimum(lo, co.min(0))); hi = Vector(np.maximum(hi, co.max(0)))
    dims = [round(v, 3) for v in hi - lo]
    check('two_storeys_taller_than_vl', dims[2] > 5.6 + 1.2, {'height_m': dims[2], 'vl_height_m': 5.552})
    if col:
        cg = {k: hit((p[0], p[1], 1.2), d, ax, col) for k, (p, d, ax) in
              {'front': ((-2.4, -12), (0, 1, 0), 1), 'rear': ((1.2, 12), (0, -1, 0), 1), 'left': ((-12, .5), (1, 0, 0), 0), 'right': ((12, .5), (-1, 0, 0), 0)}.items()}
        under_gal = col((-2.4, -2.7, .1), (0, 0, 1))         # clear of the firewood and jars, which have their own boxes
        check('collision_closed_and_gallery_walkable_under', all(v is not None for v in cg.values()) and under_gal is not None and under_gal[0].z > 2.2,
              {'collision_faces_m': cg, 'collision_above_ground_under_gallery_m': round(under_gal[0].z, 3) if under_gal else None})
    return {'ridge_top_m': round(hi.z, 3), 'deck_m': deck_z, 'gallery_headroom_m': headroom}
