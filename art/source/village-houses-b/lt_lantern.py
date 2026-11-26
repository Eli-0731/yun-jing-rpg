"""LT01 village-gate stone lantern, Chinese (work pack 2026-11-09 B-112h, batch A, LT01).

The G01 lantern of qingxi-day12-c reads Japanese (a toro). LT01 is squared off and sturdy: a stepped square base of three
courses, a plain square post, a projecting collar, a square lantern chamber with simple rectangular openings (wide ones front and
back, narrow ones at the sides) and a low heavy square cap, a shallow four-sided slope whose corners lift only a few centimetres,
with a small square boss on top. Inside the chamber: a stone oil dish with a wick flame (the glow, emission baked into the atlas,
strength set by the game) and Socket_Light at the chamber centre for a point light.

Sizes from the work pack (0.7 x 0.7 x 1.8 m, limit), origin as G01: footprint centre, bottom z = 0, front -Y. G01 itself is
0.59 x 0.59 x 2.13 m, so LT01 is 0.33 m lower: the work pack's 1.8 m wins (G01's original files are not touched).
Reference: art/references/LT01/LT01-fix-cand-1.png (proportions from the written sizes, not measured off the picture).
One 1024 atlas (Main, with Detail_Small: moss and weeds).
"""
import math, random
from mathutils import Vector
import ti_mats as tm
import cr_mats as cm
import fr_parts as FP
from cr_parts import rbox
from ti_core import S, cyl, sphere, socket, mesh, boolean
from vl_checks import _bvh

W = .70; H = 1.80
BASE = [(.62, 0., .15), (.52, .147, .27), (.43, .267, .39)]     # (width, z0, z1) of the three base courses
POST = (.32, .386, 1.026)
COLLAR = [(.46, 1.022, 1.066), (.56, 1.062, 1.152)]
CH = (.44, 1.148, 1.482)                                        # chamber block: width, z0, z1 (its top sinks 7 mm into the cap)
CAV = (.30, 1.200, 1.420)                                       # hollow inside: width, floor, ceiling
WIN_FB = (.22, 1.235, 1.385)                                    # front / back openings: width, z0, z1
WIN_S = (.10, 1.220, 1.400)                                     # side openings
CAP = [(.300, 1.474, 0.), (.338, 1.493, .016), (.348, 1.502, .022), (.348, 1.585, .026), (.333, 1.601, .022), (.125, 1.690, 0.), (.085, 1.700, 0.)]
CAP_TOP = 1.703
BOSS = [(.18, 1.697, 1.800)]                                     # one low square knob, its top 0.75 of its foot
LIGHT = (0., 0., 1.30)


def palette():
    P = {}
    P['stone'] = cm.stone('Lantern_Stone', light=(.2, .19, .17), dark=(.085, .08, .07), ochre=(.21, .175, .12), moss=.9, lichen=.7, crack=.6)
    P['stone_base'] = cm.stone('Lantern_Stone_Base', light=(.185, .175, .155), dark=(.075, .07, .06), ochre=(.19, .16, .11), moss=1.3, lichen=.6, crack=.5, wet_z=.3)
    P['soot'] = cm.stone('Lantern_Chamber_Soot', light=(.14, .13, .12), dark=(.05, .045, .04), ochre=(.12, .09, .06), moss=0., lichen=0., crack=.3)
    P['flame'] = tm.flame('Lantern_Flame', 'Main')
    tm.set_emission(P['flame'], 3.)       # preview only: the bake reads the emission colour; the game sets the glow strength
    P['moss'] = cm.moss_tuft('Lantern_Moss', soft=True)
    P['grass'] = cm.weed_leaf('Lantern_Weed', (.03, .06, .02), (.1, .17, .045), (.2, .24, .07))
    P['dry'] = cm.weed_leaf('Lantern_Dry_Grass', (.1, .075, .03), (.25, .19, .08), (.4, .31, .14))
    return P


def _cap(P):
    """The cap: square rings from the soffit up to the top, 14 points a side; a ring's corners lift by its lift (|s|^5 along each side)."""
    n = 14; verts, faces = [], []
    def ring(hw, z, lift):
        pts = []
        for side in range(4):
            for i in range(n):
                s = -1 + 2 * i / n                                 # -1 at this side's first corner
                x, y = {0: (s * hw, -hw), 1: (hw, s * hw), 2: (-s * hw, hw), 3: (-hw, -s * hw)}[side]
                pts.append((x, y, z + lift * abs(s) ** 5))
        return pts
    for hw, z, lift in CAP:
        verts.extend(ring(hw, z, lift))
    m = 4 * n
    for r in range(len(CAP) - 1):
        for i in range(m):
            a, b = r * m + i, r * m + (i + 1) % m
            faces.append((a, b, b + m, a + m))
    bot = len(verts); verts.append((0., 0., CAP[0][1])); top = len(verts); verts.append((0., 0., CAP_TOP))
    for i in range(m):
        faces.append((bot, (i + 1) % m, i))
        faces.append(((len(CAP) - 1) * m + i, (len(CAP) - 1) * m + (i + 1) % m, top))
    o = mesh('Lantern_Cap', verts, faces, P['stone'], grain='x', group='Main')
    import bmesh
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    for f in o.data.polygons: f.use_smooth = False
    return o


def build_lt01(P):
    R = random.Random('LT01')
    kw = dict(group='Main')
    # stepped base: three courses, each sunk 3 mm into the one below, chisel facets and a few chipped corners
    for k, (w, z0, z1) in enumerate(BASE):
        rbox(f'Base_Course_{k}', (0., 0., (z0 + z1) / 2), (w, w, z1 - z0), P['stone_base'], r=.012, amp=.003, freq=4., hew=3, chips=2 - (k == 2),
             seed=k, div=.05, flat='z' if k == 0 else '', rot=(0, 0, math.radians(R.uniform(-.6, .6))), **kw)
    rbox('Post', (0., 0., (POST[1] + POST[2]) / 2), (POST[0], POST[0], POST[2] - POST[1]), P['stone'], r=.01, amp=.002, freq=3., hew=3, chips=1,
         seed=11, div=.06, **kw)
    for k, (w, z0, z1) in enumerate(COLLAR):
        rbox(f'Collar_{k}', (0., 0., (z0 + z1) / 2), (w, w, z1 - z0), P['stone'], r=.01, amp=.002, freq=4., hew=2, chips=k, seed=20 + k, div=.05, **kw)
    # the chamber: one block, hollowed and pierced (boolean cuts; the cut faces take the soot stone)
    ch = rbox('Chamber', (0., 0., (CH[1] + CH[2]) / 2), (CH[0], CH[0], CH[2] - CH[1]), P['stone'], r=.01, amp=.0015, freq=4., hew=2, chips=1, seed=30, div=.04, **kw)
    cut = lambda name, c, s: rbox(name, c, s, P['soot'], r=.002, div=.5, **kw)
    boolean(ch, cut('Cut_Cavity', (0., 0., (CAV[1] + CAV[2]) / 2), (CAV[0], CAV[0], CAV[2] - CAV[1])))
    boolean(ch, cut('Cut_Window_FB', (0., 0., (WIN_FB[1] + WIN_FB[2]) / 2), (WIN_FB[0], .8, WIN_FB[2] - WIN_FB[1])))
    boolean(ch, cut('Cut_Window_S', (0., 0., (WIN_S[1] + WIN_S[2]) / 2), (.8, WIN_S[0], WIN_S[2] - WIN_S[1])))
    _cap(P)
    for k, (w, z0, z1) in enumerate(BOSS):
        rbox(f'Cap_Boss_{k}', (0., 0., (z0 + z1) / 2), (w, w, z1 - z0), P['stone'], r=.012, amp=.001, freq=4., hew=1, seed=40 + k, div=.04, taper=(.75, .75), **kw)
    # the lamp: a stone oil dish on the chamber floor, a wick and its flame
    cyl('Oil_Dish', (0., .02, CAV[1] + .011), .055, .024, P['stone'], verts=20, r2=.045, group='Main')
    cyl('Wick', (0., .02, CAV[1] + .03), .004, .02, P['soot'], verts=6, bevel=0, group='Main')
    sphere('Flame', (0., .02, CAV[1] + .058), .015, P['flame'], scale=(1., 1., 2.3), seg=12, ring=8, group='Main')
    # moss at the foot and on the base treads, a little on the cap; weeds at the corners
    for k, (w, z0, z1) in enumerate(BASE):
        for j in range(4 - k):
            a = R.uniform(0, math.tau); r = w / 2 - .03
            q = (math.cos(a) * r, math.sin(a) * r, z1)
            FP.moss_patch('Base_Moss', q, (0, 0, 1), R.uniform(.03, .06), P['moss'], seed=k * 10 + j, flat=.7, snap_each=True)
    for j, (x, y) in enumerate(((-.12, -.17), (.15, .16), (.17, -.12))):
        FP.moss_patch('Post_Foot_Moss', (x * .9, y * .9, .41), (0, 0, 1), .045, P['moss'], seed=50 + j, flat=.6, snap_each=True)
    for j in range(3):
        a = R.uniform(0, math.tau); FP.moss_patch('Cap_Moss', (math.cos(a) * .2, math.sin(a) * .2, 1.70), (0, 0, 1), .04, P['moss'], seed=60 + j, flat=.5, snap_each=True)
    for j, (x, y) in enumerate(((-.32, -.32), (.32, -.325), (-.325, .32), (.32, .32), (0., -.325), (.325, .05))):
        FP.grass_tuft('Base_Weed', (x, y, 0.), R.randint(12, 18), R.uniform(.1, .2), P['grass'] if j % 3 else P['dry'], R, lean=.2, detail=1, spread=.02)
    socket('Socket_Light', LIGHT)
    S['collision_mesh'] = collision()
    S['part_notes'] = {'base_courses_m': BASE, 'post_m': POST, 'collar_m': COLLAR, 'chamber_m': CH, 'cavity_m': CAV, 'openings_front_back_m': WIN_FB,
                       'openings_sides_m': WIN_S, 'cap_rings_halfwidth_z_lift_m': CAP, 'boss_m': BOSS, 'light_socket_m': LIGHT,
                       'glow': 'the flame only: emission baked into the Main atlas (Emission map); the material starts at strength 0, the game sets it',
                       'g01_note': 'G01 is 0.59 x 0.59 x 2.13 m with G01_LightSocket at z 1.553; LT01 follows the work pack 0.7 x 0.7 x 1.8 m, origin as G01'}


def collision():
    V, F = [], []
    def prism(w, z0, z1):
        FP.hull_loft(V, F, [[(-w / 2, -w / 2, z), (w / 2, -w / 2, z), (w / 2, w / 2, z), (-w / 2, w / 2, z)] for z in (z0, z1)])
    prism(.62, 0., .39); prism(.46, .39, 1.48); prism(.70, 1.48, 1.80)
    return V, F


NOTE = ('Chinese village-gate stone lantern, to stand in for G01 at the village gate (Gate_Lantern_L / _R). Squared off and sturdy, no writing. '
        'The flame glows by the baked emission map (strength set by the game: 0 = unlit); Socket_Light at the chamber centre for a small warm point light.')


def register(ASSETS):
    ASSETS['LT01_VillageStoneLantern'] = dict(
        zh='村口石燈（中式）', kind='lantern', palette=palette, build=build_lt01, limit=(W, W, H), tex=1024, ver='v001',
        box=((-W / 2, -W / 2, 0.), (W / 2, W / 2, H)), ref='LT01/LT01-fix-cand-1', slot='A1_QingxiVillage_Gate', minTier='standard', clamp_max=.045, uv_shape='CONVEX', uv_detach_zero=True,
        atlases={'Main': ['Main', 'Detail_Small']},
        origin='footprint centre, bottom z = 0, front -Y (as G01)',
        method='procedural mesh construction (art/source/village-houses-b/lt_lantern.py: chiselled stone blocks, boolean-hollowed chamber, lofted cap); '
               'procedural stone, moss and flame shaders baked to one 1024 atlas (Main, with an Emission map for the flame)',
        based_on='new piece (work pack 2026-11-09 LT01) replacing G01 (art/exports/qingxi-day12-c/G01, not changed); size and origin per the work pack and G01',
        note=NOTE)


# ------------------------------------------------------------------ measured checks
def lantern_checks(aid, check, cfg):
    body = _bvh([o for g, o in S['lods'][0].items() if not g.startswith('Detail_')])
    col = _bvh([S['collision_obj']]) if S.get('collision_obj') else None
    down = lambda x, y: (lambda h: round(h[0].z, 4) if h else None)(body((x, y, 5.), (0, 0, -1)))
    # the cap: low and heavy, corners lifted only a few cm over the middle of its edge
    corner, mid_edge, top = down(.335, .335), down(0., .335), down(0., 0.)
    lift = round(corner - mid_edge, 4) if corner and mid_edge else None
    check('cap_corners_lift_a_little', lift is not None and .005 < lift < .06 and top and abs(top - H) < .005,
          {'cap_corner_top_m': corner, 'cap_edge_middle_top_m': mid_edge, 'lift_m': lift, 'top_m': top})
    # the openings go through: a level ray through the front opening's middle reaches the back opening, beside it the wall stops it
    zc = (WIN_FB[1] + WIN_FB[2]) / 2 + .03
    thru = body((0., -3., zc), (0, 1, 0)); wall = body((.17, -3., zc), (0, 1, 0))
    side = body((-3., 0., (WIN_S[1] + WIN_S[2]) / 2 + .03), (1, 0, 0))
    ok = (thru is None or thru[0].y > CH[0] / 2 - .01) and wall is not None and wall[0].y < -CH[0] / 2 + .02 and (side is None or side[0].x > CH[0] / 2 - .01)
    check('chamber_openings_see_through', ok, {'through_front_first_hit_y_m': round(thru[0].y, 3) if thru else None,
                                               'beside_opening_hit_y_m': round(wall[0].y, 3) if wall else None, 'through_side_first_hit_x_m': round(side[0].x, 3) if side else None})
    # the light socket in the hollow, over the flame
    sk = S['sockets']['Socket_Light'].matrix_world.translation
    check('light_socket_in_chamber', abs(sk.x) < CAV[0] / 2 and abs(sk.y) < CAV[0] / 2 and CAV[1] + .07 < sk.z < CAV[2],
          {'socket_m': [round(v, 3) for v in sk], 'cavity_m': CAV})
    out = {'cap_lift_m': lift, 'socket_m': [round(v, 3) for v in sk]}
    if col:
        hits = {'front': col((0., -3., .2), (0, 1, 0)), 'left': col((-3., 0., .2), (1, 0, 0))}
        top_c = col((0., 0., 5.), (0, 0, -1))
        check('collision_box_matches', all(h is not None for h in hits.values()) and top_c is not None and abs(top_c[0].z - H) < .01,
              {'front_hit_y_m': round(hits['front'][0].y, 3) if hits['front'] else None, 'left_hit_x_m': round(hits['left'][0].x, 3) if hits['left'] else None,
               'top_m': round(top_c[0].z, 3) if top_c else None})
    return out
