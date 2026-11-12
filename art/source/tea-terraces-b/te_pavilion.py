"""TE05_Pavilion  east-slope viewing pavilion above the tea terraces, 5 x 5 x 5 m (AI three-view TE05/PAVILION candidate-04).

A square four-post timber pavilion with a pyramidal tile roof (a pointed hip roof, the four hips meeting at a finial):
- a warm-grey stone plinth 0.5 m high, rubble-faced in two courses, paved on top, three steps on the front (-Y);
- four round posts on drum bases, a deep top beam and a slim lower beam on each side with short struts between, curved braces;
- a plate, bracket blocks and a round eave purlin carrying the roof; diagonal corner beams under the hips; rafters under the eaves;
- blue-grey pan-and-cover tiles in stepped courses, the eave corners lifting into curled hip ends, moss on the hips;
  one corner (front-right) re-laid with newer, paler tiles;
- an L-shaped bench with a railing along the back and the right side; a blank board panel on the back half of the left side,
  a low railing on its front half; a clay water jar with a lid and bamboo dipper on the plinth by the front-left post.

Unlike creek-repair-b WM09 (a round bamboo pavilion with a thatch roof on a round slab) this one is square, timber and tile, on a raised plinth.
Blender Z-up, 1 unit = 1 m, front -Y (the steps), origin at the bottom centre (z = 0 under the plinth).
"""
import math, random
from mathutils import Vector, Matrix, noise
from ti_core import S, cyl, lathe, mesh, surface, tube, socket
import mk_mats as mm
import cr_mats as cm
from cr_parts import rbox, between as _between, set_float, tuft, sheet, pole, set_attr_list


def between(name, a, b, *args, **kw):
    """cr_parts.between, with the run always pointing +X or +Y: for a run straight along -X the rotation between the two axes is a half turn
    about an arbitrary axis, which tipped the back side's beams, rails and plate over."""
    A, B = Vector(a), Vector(b); d = B - A
    if d.x < -1e-6 or (abs(d.x) <= 1e-6 and d.y < -1e-6): A, B = B, A
    return _between(name, tuple(A), tuple(B), *args, **kw)

# ------------------------------------------------------------------ dimensions
PL = 1.75            # plinth half size
Z_P = .5             # plinth top (paving)
STEP_W, STEP_R, STEP_T = 1.9, .125, .25    # steps: width, rise, tread
PX = 1.4             # post centres at (+-PX, +-PX)
R_POST = (.135, .12)
Z_TOP = 3.25         # post tops
Z_BEAM, H_BEAM = 3.07, .26     # top beam (centre, height)
Z_LOW, H_LOW = 2.69, .14       # lower beam
R_E, E_X, R_A = 2.15, .05, .14 # eave half size at mid-edge, corner extension, apex half size
Z_E, H_R = 3.55, 1.05          # eave height at mid-edge, rise to the apex
LC = .36                       # corner lift at the eave tips
NC = 10                        # tile courses from eave to apex
ST = .028                      # course step (tile thickness showing at each course)
PITCH, ROLL_W = .22, .052      # cover-tile spacing and half width
SOFFIT = .14                   # soffit below the tile deck


def palette():
    P = {}
    P['stone'] = cm.stone('Plinth_Stone', light=(.4, .375, .32), dark=(.19, .175, .15), moss=.9, crack=.6, lichen=.5)
    P['pave'] = cm.stone('Paving_Stone', light=(.42, .4, .35), dark=(.2, .19, .165), moss=.5, crack=.4, lichen=.25)
    P['core'] = cm.stone('Plinth_Core', light=(.2, .19, .16), dark=(.1, .095, .08), moss=0., crack=0., lichen=0.)
    P['post'] = cm.wood('Post_Timber', (.07, .038, .02), (.34, .2, .1), ground_h=.95, grey=.2)       # sun-faded, darker and damp at the foot
    P['beam'] = cm.wood('Beam_Timber', (.065, .036, .02), (.3, .18, .095), ground_h=0., grey=.18)
    P['board'] = cm.wood('Panel_Board', (.08, .048, .027), (.34, .22, .12), ground_h=.75, grey=.3)
    P['bench'] = cm.wood('Bench_Timber', (.1, .058, .03), (.34, .21, .11), ground_h=0., polish=.12, grey=.2)
    P['rafter'] = cm.wood('Rafter_Timber', (.08, .046, .026), (.26, .16, .09), ground_h=0., grey=.2)
    P['tile'] = cm.tile('Roof_Tile', base=(.028, .04, .04), light=(.062, .08, .076), moss=1.0, edge_amt=.22, tone='tone')
    P['tile_new'] = cm.tile('Roof_Tile_New', base=(.1, .1, .1), light=(.19, .19, .18), moss=.0)
    P['ridge'] = cm.tile('Ridge_Tile', base=(.025, .035, .036), light=(.058, .072, .07), moss=1.3, edge_amt=.25)
    P['finial'] = cm.clay('Finial_Clay', body=(.13, .12, .11), glaze=(.07, .08, .085))
    P['jar'] = cm.clay('Water_Jar', body=(.2, .105, .05), glaze=(.075, .042, .022))
    P['lid'] = cm.wood('Jar_Lid', (.1, .06, .032), (.3, .19, .1), ground_h=0., grey=.3)
    P['culm'] = cm.culm('Dipper_Bamboo', green=(.1, .1, .03), straw=(.32, .23, .085), mud_h=0.)
    P['moss'] = cm.moss_tuft('Ridge_Moss', soft=True)
    P['moss_g'] = cm.moss_tuft('Footing_Moss')
    return P


# ------------------------------------------------------------------ roof surface
def rot(k):
    return Matrix.Rotation(k * math.pi / 2, 3, 'Z')


def roof_r(q, t):
    return R_E * (1 + E_X * abs(q) ** 3) * (1 - t) + R_A * t


def deck_z(q, t):
    """Tile deck height on the front face at (q across -1..1, t eave 0 .. apex 1): concave rise, corners lifting, course steps."""
    k = min(int(t * NC), NC - 1); f = t * NC - k
    return Z_E + H_R * t ** 1.5 + LC * abs(q) ** 4 * (1 - t) ** 2.2 + ST * (1 - f)


def smooth_z(q, t):
    return Z_E + H_R * t ** 1.5 + LC * abs(q) ** 4 * (1 - t) ** 2.2


def face_pt(k, q, t, dz=0.):
    r = roof_r(q, t)
    return rot(k) @ Vector((q * r, -r, 0.)) + Vector((0, 0, deck_z(q, t) + dz))


def q_for_x(x, t):
    """q at which the front face passes through x at height parameter t (|q| <= 1), by fixed-point iteration."""
    q = x / roof_r(0., t)
    for _ in range(8):
        q = x / roof_r(q, t)
    return q


def t_rows():
    rows = []
    for k in range(NC):
        rows += [k / NC, k / NC + .5 / NC, (k + 1) / NC - .004]
    return rows + [1.]


def corr(x, q):
    """Pan tiles: concave channels between the cover rolls, fading out at the hips so neighbouring faces meet."""
    fr = (x / PITCH) % 1.
    return -.024 * math.sin(math.pi * fr) * (1 - abs(q) ** 10)


def roof(P, R):
    rows = t_rows(); NQ = 96
    for k in range(4):
        verts, faces = [], []
        for t in rows:
            for j in range(NQ + 1):
                q = -1 + 2 * j / NQ; r = roof_r(q, t)
                x = q * r
                verts.append(tuple(rot(k) @ Vector((x, -r, 0.)) + Vector((0, 0, deck_z(q, t) + corr(x, q)))))
        W = NQ + 1
        faces = [(i * W + j, i * W + j + 1, (i + 1) * W + j + 1, (i + 1) * W + j) for i in range(len(rows) - 1) for j in range(NQ)]
        d = mesh('Roof_Deck', verts, faces, P['tile'], smooth=True, grain=tuple(rot(k) @ Vector((0, 1, 0))))
        set_attr_list(d, 'tone', [(tone_of(k, round((q_x - .5 * PITCH) / PITCH), i // 3), 0., 0.) for i, t in enumerate(rows) for q_x in
                                  [(-1 + 2 * j / NQ) * roof_r(-1 + 2 * j / NQ, t) for j in range(NQ + 1)]])
        # soffit: the boarded underside, smooth, SOFFIT below the deck; faces down
        sv = [tuple(rot(k) @ Vector((q * roof_r(q, t), -roof_r(q, t), 0.)) + Vector((0, 0, smooth_z(q, t) - SOFFIT)))
              for t in [i / 12 for i in range(13)] for q in [-1 + 2 * j / 24 for j in range(25)]]
        sf = [(i * 25 + j, (i + 1) * 25 + j, (i + 1) * 25 + j + 1, i * 25 + j + 1) for i in range(12) for j in range(24)]
        mesh('Soffit', sv, sf, P['rafter'], smooth=True, grain=tuple(rot(k) @ Vector((0, 1, 0))))
        # eave fascia board: from the deck edge down past the soffit edge, facing out
        fv = []
        for q in [-1 + 2 * j / 48 for j in range(49)]:
            r = roof_r(q, 0.); base = rot(k) @ Vector((q * r, -r, 0.))
            fv += [tuple(base + Vector((0, 0, smooth_z(q, 0.) + ST + corr(q * r, q) - .01))), tuple(base + Vector((0, 0, smooth_z(q, 0.) - SOFFIT - .03)))]
        ff = [(2 * j, 2 * j + 1, 2 * j + 3, 2 * j + 2) for j in range(48)]
        mesh('Eave_Fascia', fv, ff, P['rafter'], smooth=True, grain=tuple(rot(k) @ Vector((1, 0, 0))))
        # cover rolls
        for j in range(-11, 12):
            c = j * PITCH
            roll(P, R, k, c, rows)
        # rafters under the eave, at constant x like the tiles above
        for j in range(-6, 7):
            rafter(P, k, j * .32 + .16 * (j % 2 == 0) * 0)
    for k in range(4):
        hip(P, R, k)
    # finial: a stacked clay finial on the apex, a hanging post inside covering the apex from below
    zA = smooth_z(0., 1.) + ST
    lathe('Finial', [(0., zA - .02), (.22, zA - .02), (.23, zA + .05), (.16, zA + .1), (.16, zA + .14), (.2, zA + .17), (.2, zA + .21),
                     (.12, zA + .24), (.09, zA + .27), (.13, zA + .3), (.0, zA + .355)], (0, 0, 0), P['finial'], seg=24, grain='z')
    cyl('Apex_Post', (0, 0, (zA - .02 + zA - SOFFIT - .62) / 2), .12, .6 + SOFFIT, P['beam'], verts=16, grain='z')   # up into the finial's base
    return zA + .355


def tone_of(k, col, course):
    """A repeatable 0..1 firing shade for one tile (side k, column, course): neighbouring tiles differ, the same tile always matches."""
    h = (k * 73856093) ^ ((col + 97) * 19349663) ^ ((course + 13) * 83492791)
    return ((h * 2654435761) % 1000) / 999.


def roll(P, R, k, c, rows):
    """One run of cover tiles at x = c from the eave up to the hip, a half round sitting in the course steps."""
    pts = []
    for t in rows:
        q = q_for_x(c, t)
        if abs(q) > .96: break
        pts.append((t, q))
    if len(pts) < 3: return
    seg = 4
    def ring(t, q):
        r = roof_r(q, t); base = Vector((c, -r, deck_z(q, t)))
        return [tuple(rot(k) @ Vector((c + ROLL_W * math.cos(a), -r, 0.)) + Vector((0, 0, base.z + ROLL_W * .85 * math.sin(a) - .006)))
                for a in [math.pi * i / seg for i in range(seg + 1)]]
    # newer tiles on the front-right corner (front face x > 1.25, right face x < -1.25), the lowest four courses
    repaired = (k == 0 and c > 1.25) or (k == 1 and c < -1.25)
    cut = 4 if repaired else 0
    groups = [(pts[:cut * 3 + 1], P['tile_new']), (pts[cut * 3:], P['tile'])] if cut else [(pts, P['tile'])]
    for gp, mat in groups:
        if len(gp) < 2: continue
        verts = []; n = seg + 1
        for t, q in gp: verts += ring(t, q)
        faces = [(i * n + a, i * n + a + 1, (i + 1) * n + a + 1, (i + 1) * n + a) for i in range(len(gp) - 1) for a in range(seg)]
        # close the lower end with a round eave tile face at the eave, an open end elsewhere hidden by the next course
        o = mesh('Cover_Roll' if mat is P['tile'] else 'Cover_Roll_New', verts, faces, mat, smooth=True, grain=tuple(rot(k) @ Vector((0, 1, 0))))
        base_i = 0 if gp is pts else (cut * 3 if mat is P['tile'] else 0)
        set_attr_list(o, 'tone', [(tone_of(k, round(c / PITCH) + 50, (base_i + i) // 3), 0., 0.) for i in range(len(gp)) for _ in range(n)])
    # round tile end at the eave
    t0, q0 = pts[0]; r0 = roof_r(q0, t0)
    p0 = rot(k) @ Vector((c, -r0 - .012, 0.)) + Vector((0, 0, deck_z(q0, t0) - .004))
    o = cyl('Eave_Tile_End', tuple(p0), ROLL_W * 1.05, .024, P['tile_new'] if repaired else P['ridge'], verts=12, rot=(math.pi / 2 - .32, 0, k * math.pi / 2), detail=1, bevel=0.)


def rafter(P, k, x):
    """A rafter under the soffit at constant x, from the eave fascia up to where it meets the hip."""
    pts = []
    for t in [i / 16 for i in range(17)]:
        q = q_for_x(x, t)
        if abs(q) > .97: break
        r = roof_r(q, t)
        pts.append(rot(k) @ Vector((x, -r + .02, 0.)) + Vector((0, 0, smooth_z(q, t) - SOFFIT - .04)))
    if len(pts) < 2: return
    box_sweep('Rafter', pts, .07, .08, P['rafter'], up_hint=Vector((0, 0, 1)), detail=1)


def box_sweep(name, pts, w, h, mat, up_hint=Vector((0, 0, 1)), taper=None, **kw):
    """A softened rectangular section (w wide, h tall) swept through pts; taper(i/n) scales the section."""
    sec = []
    rr = .25 * min(w, h)
    for (sx, sy), a0 in (((1, -1), -math.pi / 2), ((1, 1), 0.), ((-1, 1), math.pi / 2), ((-1, -1), math.pi)):
        for j in range(2):
            a = a0 + j * math.pi / 2
            sec.append((sx * (w / 2 - rr) + rr * math.cos(a), sy * (h / 2 - rr) + rr * math.sin(a)))
    verts, faces = [], []; n = len(pts); m = len(sec)
    for i, p in enumerate(pts):
        tg = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        sd = tg.cross(up_hint).normalized(); up = sd.cross(tg).normalized()
        s = taper(i / (n - 1)) if taper else 1.
        for a, b in sec:
            verts.append(tuple(p + sd * (a * s) + up * (b * s)))
    for i in range(n - 1):
        for j in range(m):
            faces.append((i * m + j, i * m + (j + 1) % m, (i + 1) * m + (j + 1) % m, (i + 1) * m + j))
    faces += [tuple(range(m - 1, -1, -1)), tuple((n - 1) * m + j for j in range(m))]
    grain = (pts[-1] - pts[0]).normalized()
    from cr_parts import _sharp
    o = mesh(name, verts, faces, mat, smooth=True, grain=tuple(grain), **kw)
    _sharp(o.data, 50)
    return o


def hip(P, R, k):
    """The hip ridge between face k and face k+1 (it lies on face k at q = +1), ending in an upturned, curled tail at the eave corner."""
    ts = [i / 24 for i in range(25)]
    pts = [face_pt(k, 1., t, .04 - ST * 0) for t in ts]
    pts = [Vector((p.x, p.y, smooth_z(1., t) + .07)) for p, t in zip(pts, ts)]
    # tail: continues outward along the diagonal and sweeps up
    d = (pts[0] - pts[1]); d.z = 0; d.normalize()
    tail = [pts[0] + d * (.17 * s) + Vector((0, 0, .27 * s ** 1.6)) for s in [i / 6 for i in range(1, 7)]]
    path = list(reversed(tail)) + pts
    n = len(path); nt = len(tail)
    box_sweep('Hip_Ridge', path, .17, .15, P['ridge'], taper=lambda f: .55 + .45 * min(1., f * n / (nt + 1)) if f * n < nt + 1 else 1. - .2 * (f - (nt + 1) / n))
    # a curl at the very tip
    tip = path[0]; up = Vector((0, 0, 1))
    curl = [tip + d * (.05 * math.sin(a)) + up * (.06 * (1 - math.cos(a))) - d * .0 for a in [i / 5 * math.pi * .9 for i in range(6)]]
    tube('Hip_Curl', [tuple(p) for p in curl], .035, P['ridge'], res=4, grain=tuple(d), detail=1)
    # moss cushions along the hip's lower half
    for i in range(3):
        t = R.uniform(.15, .6); p = Vector((0, 0, 0)) + face_pt(k, 1., t)
        p.z = smooth_z(1., t) + .14
        tuft('Ridge_Moss', tuple(p), R.uniform(.05, .08), P['moss'], seed=k * 10 + i, rot=(0, 0, k * math.pi / 2 + math.pi / 4))


# ------------------------------------------------------------------ frame
def frame(P, R):
    zb = Z_P + .16
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * PX, sy * PX
            lathe('Post_Base', [(0., Z_P - .01), (.23, Z_P - .01), (.24, Z_P + .03), (.215, Z_P + .1), (.17, zb), (0., zb)], (x, y, 0), P['stone'], seg=24, grain='z')
            cyl('Post', (x, y, (zb + Z_TOP) / 2), R_POST[0], Z_TOP - zb, P['post'], verts=20, r2=R_POST[1], grain='z')
    # top beam and lower beam on each side, with three short struts between and a bracket block over each post
    for k in range(4):
        M = rot(k)
        a, b = M @ Vector((-PX - .17, -PX, 0)), M @ Vector((PX + .17, -PX, 0))
        between('Top_Beam', tuple(a + Vector((0, 0, Z_BEAM))), tuple(b + Vector((0, 0, Z_BEAM))), .15, H_BEAM, P['beam'], r=.012, div=.25, seed=k)
        a2, b2 = M @ Vector((-PX, -PX, 0)), M @ Vector((PX, -PX, 0))
        between('Low_Beam', tuple(a2 + Vector((0, 0, Z_LOW))), tuple(b2 + Vector((0, 0, Z_LOW))), .1, H_LOW, P['beam'], r=.01, div=.25, seed=k + 4)
        for x in (-.7, 0., .7):
            p = M @ Vector((x, -PX, 0)) + Vector((0, 0, (Z_LOW + H_LOW / 2 + Z_BEAM - H_BEAM / 2) / 2))
            rbox('Strut', tuple(p), (.1, .08, Z_BEAM - H_BEAM / 2 - Z_LOW - H_LOW / 2 + .01), P['beam'], r=.008, div=.2, rot=(0, 0, k * math.pi / 2), grain='z', seed=k * 3)
        # plate on the post tops
        a3, b3 = M @ Vector((-PX - .22, -PX, 0)), M @ Vector((PX + .22, -PX, 0))
        between('Plate', tuple(a3 + Vector((0, 0, Z_TOP + .04))), tuple(b3 + Vector((0, 0, Z_TOP + .04))), .22, .08, P['beam'], r=.01, div=.3, seed=k + 8)
        # bracket blocks: over each post corner and two between
        for x in (-.7, .7):
            p = M @ Vector((x, -PX, 0)) + Vector((0, 0, Z_TOP + .14))
            rbox('Bracket_Block', tuple(p), (.2, .2, .12), P['beam'], r=.012, div=.2, rot=(0, 0, k * math.pi / 2), grain='z', seed=k * 5)
        # curved braces under the top beam, both ends of each side
        for s in (-1, 1):
            brace(P, M, s)
    for sx in (-1, 1):
        for sy in (-1, 1):
            rbox('Bracket_Block', (sx * PX, sy * PX, Z_TOP + .14), (.24, .24, .12), P['beam'], r=.012, div=.2, grain='z', seed=int(sx + 2 * sy + 5))
    # bracket arms (gong): a crossed pair through each corner block and one along the face through each middle block, with a small cap
    # block on each arm end carrying the purlin: a simple one-tier bracket set instead of a bare block
    for k in range(4):
        M = rot(k)
        for x in (-PX, -.7, .7):
            za = Z_TOP + .135 + (.012 if k % 2 else 0.)      # crossed corner arms sit 12 mm apart so their faces never share a plane
            c = M @ Vector((x, -PX, 0)) + Vector((0, 0, za))
            L = .56 if x != -PX else .64
            rbox('Bracket_Arm', tuple(c), (L, .09, .1), P['beam'], r=.014, div=.15, rot=(0, 0, k * math.pi / 2), grain='x', seed=k * 11 + int(x * 10))
            for s in (-1, 1):
                e = M @ Vector((x + s * (L / 2 - .06), -PX, 0)) + Vector((0, 0, za + .05 - .005 + .035))
                rbox('Bracket_Cap', tuple(e), (.11, .12, .07), P['beam'], r=.01, div=.15, rot=(0, 0, k * math.pi / 2), grain='z', seed=k * 13 + s)
    # eave purlin: round timber over the bracket blocks on each side, running out to the corner beams
    zpu = Z_TOP + .2 + .09
    for k in range(4):
        M = rot(k)
        a, b = M @ Vector((-PX - .32, -PX - .05, zpu)), M @ Vector((PX + .32, -PX - .05, zpu))
        o = cyl('Eave_Purlin', tuple((a + b) / 2), .09, (b - a).length, P['beam'], verts=16, rot=(0, math.pi / 2, k * math.pi / 2), grain='x')
    # corner beams: from over each post out and up under the hip
    for k in range(4):
        M = rot(k)
        a = M @ Vector((PX - .1, -PX + .1, 0)) + Vector((0, 0, zpu + .02))
        p_end = face_pt(k, 1., .02)
        b = Vector((p_end.x, p_end.y, smooth_z(1., .02) - SOFFIT - .06)) * 1.0
        b.xy = b.xy * .985
        between('Corner_Beam', tuple(a), tuple(b), .13, .17, P['beam'], r=.012, div=.3, seed=k + 20)


def brace(P, M, s):
    """A curved bracket (que ti) under the top beam beside a post: deep at the post, thinning to a point along the beam.
    Built as a strip of quads between the curved underside and the beam line (a concave n-gon would triangulate over itself)."""
    L, Hh, th = .55, .3, .07
    z0 = Z_BEAM - H_BEAM / 2
    us = [i / 12 for i in range(12)]
    curve = [(u * L, -Hh * (1 - u) ** 1.6 - .015 * math.sin(u * math.pi)) for u in us] + [(L, 0.)]
    n = len(curve)
    def P3(x, z, side):
        return tuple(M @ Vector((-s * (PX - .12 - x), -PX + side, 0.)) + Vector((0, 0, z0 + z)))
    verts = []
    for side in (-th / 2, th / 2):
        for x, z in curve: verts.append(P3(x, z, side))           # underside curve
        for x, z in curve[:-1]: verts.append(P3(x, 0., side))     # beam line above it (the tip point is shared)
    m = 2 * n - 1
    def vid(side, i, top):   # i along the curve; top: on the beam line (the last point is the shared tip)
        if top and i == n - 1: return side * m + n - 1
        return side * m + (n + i if top else i)
    faces = []
    for side in (0, 1):
        for i in range(n - 1):
            q = (vid(side, i, False), vid(side, i + 1, False), vid(side, i + 1, True), vid(side, i, True))
            q = tuple(v for j, v in enumerate(q) if v != q[j - 1])     # the last quad meets the shared tip: drop the repeated corner
            faces.append(q if side == 0 else tuple(reversed(q)))
    for i in range(n - 1):   # underside band and top band between the two faces
        faces.append((vid(0, i, False), vid(1, i, False), vid(1, i + 1, False), vid(0, i + 1, False)))
        if i < n - 2: faces.append((vid(0, i, True), vid(0, i + 1, True), vid(1, i + 1, True), vid(1, i, True)))
    faces.append((vid(0, 0, False), vid(0, 0, True), vid(1, 0, True), vid(1, 0, False)))   # the end against the post
    o = mesh('Brace', verts, faces, P['beam'], smooth=False, grain=tuple(M @ Vector((1, 0, 0))))
    import bmesh
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    return o


# ------------------------------------------------------------------ plinth and steps
def plinth(P, R):
    rbox('Plinth_Core', (0, 0, (.02 + Z_P - .097) / 2), (2 * PL - .1, 2 * PL - .1, Z_P - .117), P['core'], r=.01, div=.4, grain='z', flat='zZ')   # the paving beds 3 mm into it; clear of the ground
    # rubble facing: two courses per side, random lengths, the joints staggered; corners alternate which side runs through
    for k in range(4):
        M = rot(k)
        for ci, (z0, h) in enumerate(((0., .24), (.24, .17))):
            x = -PL + (.0 if (ci + k) % 2 else .3); idx = 0
            if (ci + k) % 2 == 0:
                pass
            x = -PL - (.0 if (ci + k) % 2 else -.3)
            while x < PL - .05:
                Lst = min(R.uniform(.55, .95), PL - x)
                if PL - x - Lst < .25: Lst = PL - x
                c = M @ Vector((x + Lst / 2, -PL + .14, 0)) + Vector((0, 0, z0 + h / 2))
                rbox('Plinth_Stone', tuple(c), (Lst - .012, .3, h - .01), P['stone'], r=.025, amp=.006, freq=5., chips=2, hew=2, seed=k * 50 + ci * 20 + idx,
                     div=.14, rot=(0, 0, k * math.pi / 2), flat='Y', grain='x')
                x += Lst; idx += 1
    # coping: the paving's outer ring overhangs the facing a little; inner slabs in a loose grid
    zt = Z_P - .05
    n = 5; s = 2 * (PL + .03) / n
    for i in range(n):
        for j in range(n):
            x0, y0 = -PL - .03 + i * s, -PL - .03 + j * s
            jit = R.uniform(-.004, .006)
            rbox('Paving_Slab', (x0 + s / 2, y0 + s / 2, zt + jit / 2), (s - .014, s - .014, .1 + jit), P['pave'], r=.012, amp=.003, chips=1, hew=1, seed=i * 7 + j,
                 div=.2, grain='x')
    # three steps on the front, each in two stones
    for k in range(1, 4):
        z = k * STEP_R; yf = -PL - (4 - k) * STEP_T
        split = R.uniform(-.25, .25)
        yb = -PL + .1 - .025 * k          # backs staggered so no two share a plane
        zb = 0. if k == 1 else (k - 1) * STEP_R - .012   # each step sits 12 mm into the one below instead of sharing its underside on the ground
        for x0, x1 in ((-STEP_W / 2, split), (split, STEP_W / 2)):
            c = ((x0 + x1) / 2, (yf + yb) / 2, (zb + z) / 2)
            rbox('Step_Stone', c, (x1 - x0 - .012, yb - yf, z - zb), P['pave'], r=.02, amp=.004, chips=2, hew=2, seed=k * 9 + int(x0 * 10), div=.18, flat='Y', grain='x')
    # moss at the footing joints (shaded side: back and right)
    for i in range(10):
        k = R.choice((1, 2, 2, 3)); x = R.uniform(-PL + .1, PL - .1)
        rr = R.uniform(.05, .09)
        p = rot(k) @ Vector((x, -PL - .02, 0)) + Vector((0, 0, rr * .3))   # cushion rests on the ground: its half height is 0.275 r
        tuft('Footing_Moss', tuple(p), rr, P['moss_g'], seed=40 + i, rot=(0, 0, k * math.pi / 2))


# ------------------------------------------------------------------ bench, railing, panel, jar
def bench_rail(P, R):
    zs = Z_P + .45
    # L-shaped bench along the back (y = +1.13) and the right side (x = +1.13)
    for k, (a0, a1) in ((2, (-1.2, 1.25)), (1, (-1.25, .78))):
        M = rot(k)
        for i, off in enumerate((-.08, .1)):
            a, b = M @ Vector((a0, -(PX - .27 + off), 0)), M @ Vector((a1, -(PX - .27 + off), 0))
            between('Bench_Plank', tuple(a + Vector((0, 0, zs))), tuple(b + Vector((0, 0, zs))), .18, .05, P['bench'], r=.01, div=.3, seed=k * 3 + i)
        for i, off in enumerate((-.08, .1)):   # a stretcher under the middle of each plank: the plank rests on it along its length
            a, b = M @ Vector((a0 + .1, -(PX - .27 + off), 0)), M @ Vector((a1 - .1, -(PX - .27 + off), 0))
            between('Bench_Stretcher', tuple(a + Vector((0, 0, zs - .025 - .035))), tuple(b + Vector((0, 0, zs - .025 - .035))), .06, .07, P['bench'], r=.008, div=.3, seed=k + 40 + i)
        nleg = 4
        for i in range(nleg):
            x = a0 + .15 + (a1 - a0 - .3) * i / (nleg - 1)
            p = M @ Vector((x, -(PX - .28), 0)) + Vector((0, 0, (Z_P + zs - .025) / 2))
            rbox('Bench_Leg', tuple(p), (.07, .3, zs - .025 - Z_P), P['bench'], r=.008, div=.2, rot=(0, 0, k * math.pi / 2), grain='z', seed=k * 7 + i)
    # railings: back, right, and the front half of the left side (the back half of the left is the board panel)
    for k, (a0, a1) in ((2, (-PX + .14, PX - .14)), (1, (-PX + .14, PX - .14)), (3, (-PX + .14, -.1))):
        railing(P, R, rot(k), a0, a1, k)
    # board panel on the left side's back half, between the back-left post and a slim intermediate post
    M = rot(3)
    xm = .05
    cyl('Panel_Post', tuple(M @ Vector((xm - .02, -PX, 0)) + Vector((0, 0, (Z_P + Z_LOW) / 2))), .075, Z_LOW - Z_P, P['post'], verts=12, grain='z')
    planks = 5; w = (PX - .14 - xm - .07) / planks
    for i in range(planks):
        x = xm + .07 + w * (i + .5)
        p = M @ Vector((x, -PX, 0)) + Vector((0, 0, (Z_P + .08 + Z_LOW - H_LOW / 2) / 2))
        rbox('Panel_Board', tuple(p), (w - .006, .04, Z_LOW - H_LOW / 2 - Z_P - .08), P['board'], r=.006, amp=.002, div=.25, rot=(0, 0, 3 * math.pi / 2), grain='z', seed=60 + i)
    # a waist rail and a foot batten across the boards, inside and out, bedded 3 mm into the board faces
    for off in (-1, 1):
        for zr, hr in ((Z_P + .62, .07), (Z_P + .16, .05)):
            a, b = M @ Vector((xm + .04, -PX + off * (.02 + .015 - .003), 0)), M @ Vector((PX - .16, -PX + off * (.02 + .015 - .003), 0))
            between('Panel_Rail', tuple(a + Vector((0, 0, zr))), tuple(b + Vector((0, 0, zr))), .03, hr, P['beam'], r=.006, div=.3, seed=80 + int(zr * 10) + off)
    a, b = M @ Vector((xm, -PX, 0)), M @ Vector((PX - .12, -PX, 0))
    between('Panel_Sill', tuple(a + Vector((0, 0, Z_P + .05))), tuple(b + Vector((0, 0, Z_P + .05))), .08, .1, P['beam'], r=.008, div=.3, seed=70)
    jar(P, R)


def railing(P, R, M, a0, a1, k):
    zb, zt = Z_P + .14, Z_P + .82
    for z, hh, ww in ((zb, .06, .07), (zt, .07, .09)):
        a, b = M @ Vector((a0, -PX + .02, 0)), M @ Vector((a1, -PX + .02, 0))
        between('Rail', tuple(a + Vector((0, 0, z))), tuple(b + Vector((0, 0, z))), ww, hh, P['bench'], r=.01, div=.4, seed=k * 11)
    n = max(2, int((a1 - a0) / .13))
    for i in range(1, n):
        x = a0 + (a1 - a0) * i / n
        p = M @ Vector((x, -PX + .02, 0)) + Vector((0, 0, (zb + .03 + zt - .035) / 2))
        rbox('Baluster', tuple(p), (.035, .035, (zt - .035) - (zb + .03)), P['bench'], r=.006, div=.4, rot=(0, 0, 0), grain='z', seed=k * 31 + i)   # from the bottom rail's top to the top rail's underside
    # a rail foot block down to the paving at each end
    for x in (a0 + .02, a1 - .02):
        p = M @ Vector((x, -PX + .02, 0)) + Vector((0, 0, (Z_P + zb) / 2))
        rbox('Rail_Foot', tuple(p), (.06, .06, zb - Z_P), P['bench'], r=.006, div=.3, grain='z', seed=k * 13 + int(x * 10))


def jar(P, R):
    cx, cy = -1.02, -1.42
    prof = [(0., Z_P), (.15, Z_P), (.2, Z_P + .06), (.26, Z_P + .22), (.27, Z_P + .32), (.24, Z_P + .44), (.19, Z_P + .52), (.2, Z_P + .55),
            (.205, Z_P + .57), (.19, Z_P + .575), (.175, Z_P + .54), (.17, Z_P + .45)]
    o = lathe('Water_Jar', prof, (cx, cy, 0), P['jar'], seg=28, grain='z')
    set_float(o, 'gmask', lambda co: 1. if co.z > Z_P + .14 else 0.)
    # water inside, dark, a little below the rim
    surface('Jar_Water', 16, 1, lambda u, v: (cx + math.cos(u * math.tau) * .172 * v, cy + math.sin(u * math.tau) * .172 * v, Z_P + .5), P['core'], closed_u=True, grain='z', detail=1)
    # a lid half on, and a bamboo dipper resting across it
    cyl('Jar_Lid', (cx + .07, cy + .03, Z_P + .59), .2, .03, P['lid'], verts=24, rot=(.07, -.05, 0), grain='x', bevel=.006)
    pole('Dipper_Handle', (cx - .05, cy - .1, Z_P + .615), (cx + .4, cy + .12, Z_P + .7), .012, .011, P['culm'], seed=3, detail=1)
    lathe('Dipper_Cup', [(0., 0.), (.045, 0.), (.05, .1), (.042, .1), (.038, .012), (0., .012)], (cx - .08, cy - .12, Z_P + .615), P['culm'], seg=14, grain='z', detail=1)


def te05_pavilion(P):
    R = random.Random(505)
    plinth(P, R)
    frame(P, R)
    bench_rail(P, R)
    top = roof(P, R)
    # collision: plinth, three steps, four posts, the bench, the panel, the railings and the jar, as boxes (the roof is out of reach)
    boxes = [((-PL, -PL, 0.), (PL, PL, Z_P))]
    for k in range(1, 4):
        boxes.append(((-STEP_W / 2, -PL - (4 - k) * STEP_T, 0.), (STEP_W / 2, -PL, k * STEP_R)))
    for sx in (-1, 1):
        for sy in (-1, 1):
            boxes.append(((sx * PX - .15, sy * PX - .15, Z_P), (sx * PX + .15, sy * PX + .15, Z_TOP)))
    boxes += [((-PX + .1, PX - .45, Z_P), (PX - .1, PX + .05, Z_P + .86)), ((PX - .45, -PX + .1, Z_P), (PX + .05, PX - .1, Z_P + .86)),   # back and right bench + railing
              ((-PX - .05, .0, Z_P), (-PX + .05, PX, Z_LOW)), ((-PX - .05, -PX + .1, Z_P), (-PX + .05, .0, Z_P + .86)),                # left panel, left railing
              ((-1.3, -1.72, Z_P), (-.74, -1.14, Z_P + .62))]                                                                          # jar
    verts, faces = [], []
    for (x0, y0, z0), (x1, y1, z1) in boxes:
        b = len(verts)
        verts += [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        faces += [(b, b + 3, b + 2, b + 1), (b + 4, b + 5, b + 6, b + 7), (b, b + 1, b + 5, b + 4), (b + 1, b + 2, b + 6, b + 5), (b + 2, b + 3, b + 7, b + 6), (b + 3, b, b + 4, b + 7)]
    S['collision_mesh'] = (verts, faces)
    socket('Socket_Seat_Back', (0., PX - .28, Z_P + .475))
    socket('Socket_Seat_Right', (PX - .28, -.2, Z_P + .475))
    socket('Socket_Jar', (-1.02, -1.42, Z_P + .6))
    S['prop'] = dict(kind='pavilion', plinth_top=Z_P, step_rise=STEP_R, step_tread=STEP_T, clear_z=Z_LOW - H_LOW / 2, post_half=PX, finial_top=top,
                     opening=2 * PX - 2 * R_POST[0])
