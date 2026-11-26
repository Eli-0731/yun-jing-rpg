"""RS01 v002 (2026-11-10, the user's call after the v001 interior shots): the inn's stair rebuilt so a walker gets upstairs.

v001 kept the source stair: 17 open treads 25 cm deep and 20 cm apart (38.7 deg), no risers, its foot in the corner against the south
wall (no room in front of the first tread), its top straight into the guest-room partition with the stair well on the other side: a
1.75 m walker could not get onto it from the front and could not get off it at the top.

v002 takes those parts out (17 treads, the two stringers, the hand rail, the 30 cm floor strip over the well) and builds a dog-leg
stair in the same well (x -3.15..-0.99, y -5.84..-1.45), the rest of the inn untouched:
  * 20 risers of 17.3 cm from the ground floor (0.49) to the upper floor (3.95), treads 28 cm (+2 cm nosing), 32 deg, closed risers;
  * flight 1 by the west wall, its foot at the north end facing the dining room, 12 risers south up to a half landing (2.57) at the
    south wall; flight 2 beside it, 8 risers north up to a top landing (3.95) that opens east onto the upper corridor (x > -0.99), so
    neither the partition nor the bed has to move (the 2026-10-20 UE fix moved both);
  * a lime-plaster spine wall with a timber frame between the flights, its sloped top capped with a hand rail; a wall rail along
    flight 1; the space under flight 2 closed by a plaster and timber screen on the dining-room side, as the inn's own partitions;
  * square edges like every other part of the inn (no bevel), so the triangle count is exact;
  * a balustrade on the upper floor along the well edge, built like the balcony's (8 cm posts, 3 cm balusters ~28 cm apart,
    10 x 8 cm hand rail at 0.9 m, 8 x 6 cm bottom rail);
  * (2026-11-11, the user's marks on the v002 shots) the guest rooms' east wall (lime plaster, x 0.46..0.56) ran on 1.70 m south past
    the guest-room partition (y -1.35) to y -3.05, a lone wall 1.5 m in front of the top landing that a walker coming up had to go
    round; its free end is moved north to y -1.36 (1 cm proud of the partition face, so the two faces are not coplanar), the same
    bevelled box with the same 108 faces, so the top landing opens straight onto the upper hall;
  * (2026-11-11, the user's mark on the upper-hall shot: "open to the outside") the upper hall's east wall onto the balcony is five
    bays, each a 0.9 m plaster dado (z 3.85..4.75) under a mullioned window (three 4 cm mullions, z 4.75..6.75) that was shut by one
    8 cm plank board behind the mullions; the five boards are taken out, so the hall looks out over the balcony to the street.
    Then (the user: "plank windows that open and close", side-hung pairs opening out onto the balcony): in each bay the two quarter
    mullions and the mid rail are taken out, the centre mullion stays; a timber sill (z 4.72..4.80, its ends let 2 cm into the
    posts) and head rail (z 6.20..6.26) frame two openings of 1.04 x 1.38 m, a fixed plank transom fills 6.26..6.75 as the old board
    did; each opening has two plank leaves (three upright boards on two battens, 0.518 x 1.38 m) hung at its sides and shown open
    90 deg out onto the balcony, 0.52 m deep (the balcony is 0.89 m clear, so a walker on it is stopped by them). The leaves are
    part of the Wood group (fixed open), not separate objects: closing them in the game needs a later version;
  * (2026-11-11, the user: an interact key at the guest rooms that opens a room of the player's own) three sockets, one at each
    guest-room door: Socket_GuestRoom_1..3 on the upper floor at the foot of each door board (x 0.62, the boards hang on the rooms'
    solid east wall, so nobody walks through them), their +Y (Unity forward) pointing out of the door into the hall.
"""
import math
import bpy
import numpy as np
import ti_core
from ti_core import S
from rs02_props import _take, _obj, _bounds as _bnd

WALL_END = -1.36                           # the guest rooms' east wall now ends here (partition faces y -1.35)
FL1, FL2 = .49, 3.95                       # ground-floor and upper-floor board tops (rays on the source)
N1, N2 = 12, 8                             # risers in flight 1 / flight 2
R = (FL2 - FL1) / (N1 + N2)                # 0.173
T, NOSE, BOARD = .28, .02, .04
XW = (-3.165, -2.145)                      # flight 1 (west): its west string 3 mm off the wall posts (x -3.17), east one 6 mm off the spine wall
XE = (-2.05, -1.05)                        # flight 2 (east)
Y_FOOT = -1.55                             # nosing line of flight 1's first tread
Y_SOUTH, Y_NORTH, X_EDGE = -5.827, -1.356, -.99  # south wall face (-5.828), partition face (-1.353), upper floor's west edge (Board_Part.052)
Y_HALF = Y_FOOT - (N1 - 1) * T             # -4.63: north edge of the half landing
Z_HALF = FL1 + N1 * R                      # 2.566
Y_TOP = Y_HALF + (N2 - 1) * T              # -2.67: south edge of the top landing
SPINE = (-2.14, -2.06)                     # spine wall between the flights
RAIL_H = .9


def _prism(name, poly_yz, x0, x1, mat, group, grain='x', detail=0, bevel=0.):
    """The (y, z) outline (counter-clockwise seen from +x) pushed out from x0 to x1."""
    k = len(poly_yz)
    v = [(x0, y, z) for y, z in poly_yz] + [(x1, y, z) for y, z in poly_yz]
    f = [tuple(range(k))[::-1], tuple(range(k, 2 * k))] + [(i, (i + 1) % k, k + (i + 1) % k, k + i) for i in range(k)]
    return ti_core.finish(_obj(name, v, f), name, mat, grain=grain, group=group, detail=detail, bevel=bevel)


def _prism_x(name, poly_xz, y0, y1, mat, group, grain='y', detail=0, bevel=0.):
    """The (x, z) outline pushed out along y."""
    k = len(poly_xz)
    v = [(x, y0, z) for x, z in poly_xz] + [(x, y1, z) for x, z in poly_xz]
    f = [tuple(range(k)), tuple(range(k, 2 * k))[::-1]] + [(k + i, k + (i + 1) % k, (i + 1) % k, i) for i in range(k)]
    return ti_core.finish(_obj(name, v, f), name, mat, grain=grain, group=group, detail=detail, bevel=bevel)


def _box(name, lo, hi, mat, group, grain='x', detail=0, bevel=0.):
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    return _prism(name, [(y0, z0), (y1, z0), (y1, z1), (y0, z1)], x0, x1, mat, group, grain=grain, detail=detail, bevel=bevel)


def _bar(name, a, b, w, h, mat, group, detail=0):
    """A straight rail of w (across, in x) by h (vertical) from a to b, both (x, y, z) at the bar's top centre line; x stays fixed."""
    (x, ya, za), (_, yb, zb) = a, b
    d = np.array([yb - ya, zb - za]); d /= np.linalg.norm(d)
    return _prism(name, [(ya, za - h), (yb, zb - h), (yb, zb), (ya, za)], x - w / 2, x + w / 2, mat, group,
                  grain=(0., float(d[0]), float(d[1])), detail=detail)


def _tread(name, x0, x1, y_nose, dirn, top, mat):
    """One closed step: board (28 cm + 2 cm nosing, 2 cm under the next riser) and the riser below its nosing. dirn -1 climbs to -y."""
    def y(s): return y_nose + dirn * s
    pts = [(-NOSE, top), (T + .02, top), (T + .02, top - BOARD), (.02, top - BOARD), (.02, top - R + .001), (0., top - R + .001),
           (0., top - BOARD), (-NOSE, top - BOARD)]
    poly = [(y(s), z) for s, z in pts]
    if dirn > 0: poly = poly[::-1]                 # keep the outline counter-clockwise seen from +x
    return _prism(name, poly, x0, x1, mat, 'Wood', grain='x')


def _stringer(name, x0, x1, y_a, z_a, y_b, z_b, floor, mat):
    """Closed string board along a flight: its top 6 cm over the nosing line, 30 cm deep, its foot cut level with the floor it starts on."""
    t = (floor - (z_a - .24)) / (z_b - z_a)
    pts = [(y_a, z_a + .06), (y_b, z_b + .06), (y_b, z_b - .24), (y_a + t * (y_b - y_a), floor), (y_a, floor)]
    d = np.array([y_b - y_a, z_b - z_a]); d /= np.linalg.norm(d)
    return _prism(name, _ccw(pts), x0, x1, mat, 'Wood', grain=(0., float(d[0]), float(d[1])))


def _ccw(poly):
    a = sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(poly, poly[1:] + poly[:1]))
    return poly if a > 0 else poly[::-1]


def rebuild(P):
    plank, timber, lacquer, plaster = P['plank'], P['timber'], P['door'], P['plaster']
    removed = {}
    near = lambda a, b, tol=.012: abs(a - b) < tol
    removed['treads'] = _take(lambda n, lo, hi: n.startswith('Board_Part') and near(lo[0], -3.09) and near(hi[0], -1.99)
                              and near(hi[2] - lo[2], .08) and lo[1] > -5.8 and hi[1] < -1.45, 17, 'v001 treads')
    removed['stringers'] = _take(lambda n, lo, hi: n.startswith('Timber_Part') and near(hi[1] - lo[1], 4.428) and near(lo[2], .337)
                                 and (near(lo[0], -2.0) or near(lo[0], -3.14)), 2, 'v001 stringers')
    removed['hand_rail'] = _take(lambda n, lo, hi: n.startswith('Lacquer_Part') and near(lo[0], -1.98) and near(lo[2], 1.381), 1, 'v001 rail')
    removed['floor_strip'] = _take(lambda n, lo, hi: n.startswith('Board_Part') and near(lo[0], -3.289) and near(lo[2], 3.81)
                                   and near(hi[0], -2.99), 1, 'v001 floor strip over the well')
    # ---- the guest rooms' east wall: its free end south of the partition pulled back to the partition
    wall = [q for q in S['parts'] if q.type == 'MESH' and q.name.startswith('Plaster_Part') and near(_bnd(q)[0][0], .46) and near(_bnd(q)[1][0], .56)
            and near(_bnd(q)[0][1], -3.05) and near(_bnd(q)[1][1], 5.85)]
    assert len(wall) == 1, [q.name for q in wall]
    wall = wall[0]; assert all(abs(wall.matrix_world[i][j] - (i == j)) < 1e-9 for i in range(4) for j in range(4)), wall.name
    TRIM = WALL_END - (-3.05); moved = 0
    for v in wall.data.vertices:
        if v.co.y < -2.9: v.co.y += TRIM; moved += 1
    wall.data.update()
    assert moved and near(_bnd(wall)[0][1], WALL_END, .001), (moved, _bnd(wall))
    trimmed = {'part': wall.name, 'material': 'lime plaster', 'x_m': [.46, .56], 'y_m_before': [-3.05, 5.85], 'y_m_after': [WALL_END, 5.85],
               'vertices_moved': moved, 'faces': len(wall.data.polygons), 'triangles_changed': 0,
               'why': 'its free end stood 1.5 m in front of the top landing, past the guest-room partition (y -1.35)'}
    # ---- the upper hall's east windows: the plank boards shutting the five mullioned bays taken out
    removed['hall_window_boards'] = _take(lambda n, lo, hi: n.startswith('Board_Part') and near(lo[0], 5.47, .02) and near(hi[0], 5.55, .02)
                                          and near(lo[2], 4.75, .02) and near(hi[2], 6.75, .02), 5, 'upper hall east window boards')
    BAYS = [(-5.78, -3.66), (-3.42, -1.30), (-1.06, 1.06), (1.30, 3.42), (3.66, 5.78)]
    mid = lambda lo, hi: (lo[1] + hi[1]) / 2
    removed['hall_window_mullions'] = _take(lambda n, lo, hi: n.startswith('Timber_Part') and near(lo[0], 5.541, .01) and near(hi[0], 5.579, .01)
                                            and near(lo[2], 4.75, .02) and near(hi[2], 6.75, .02) and hi[1] - lo[1] < .06
                                            and any(near(mid(lo, hi), (a + b) / 2 + d, .02) for a, b in BAYS for d in (-.53, .53)), 10, 'quarter mullions')
    removed['hall_window_mid_rails'] = _take(lambda n, lo, hi: n.startswith('Timber_Part') and near(lo[0], 5.54, .01) and near(hi[0], 5.58, .01)
                                             and near(lo[2], 5.73, .02) and near(hi[2], 5.77, .02) and near(hi[1] - lo[1], 2.12, .02), 5, 'window mid rails')
    made = []
    # ---- the upper hall's east windows: sill, head rail, transom and two pairs of plank leaves per bay, open 90 deg out
    SILL, HEAD, TOP, XH, LT, BT = (4.72, 4.80), (6.20, 6.26), 6.75, 5.592, .025, .02     # leaves 4.81..6.19, hinged on x 5.592
    n_leaf = 0
    for b, (ya, yb) in enumerate(BAYS):
        made.append(_box(f'Hall_Window_Sill_{b}', (5.43, ya - .02, SILL[0]), (5.62, yb + .02, SILL[1]), timber, 'Wood'))
        made.append(_box(f'Hall_Window_Head_{b}', (5.50, ya - .02, HEAD[0]), (5.60, yb + .02, HEAD[1]), timber, 'Wood'))
        made.append(_box(f'Hall_Window_Transom_{b}', (5.47, ya - .02, HEAD[1] + .001), (5.55, yb + .02, TOP), plank, 'Wood', grain='z'))
        c = (ya + yb) / 2
        for o0, o1 in ((ya, c - .02), (c + .02, yb)):            # the two openings either side of the centre mullion
            w = (o1 - o0 - .004) / 2
            for hinge, sgn in ((o0, 1), (o1, -1)):              # a leaf hung at each side, its boards on the opening's side
                y0 = hinge + sgn * .002; y1 = y0 + sgn * LT; yb0, yb1 = y1, y1 + sgn * BT
                bw = (w - .004) / 3
                for k in range(3):
                    x0 = XH + k * (bw + .002)
                    made.append(_box(f'Hall_Shutter_{n_leaf:02d}_Board_{k}', (x0, min(y0, y1), SILL[1] + .01), (x0 + bw, max(y0, y1), HEAD[0] - .01), plank, 'Wood', grain='z'))
                for k, z in enumerate((SILL[1] + .16, HEAD[0] - .23)):
                    made.append(_box(f'Hall_Shutter_{n_leaf:02d}_Batten_{k}', (XH + .03, min(yb0, yb1), z), (XH + w - .03, max(yb0, yb1), z + .07), timber, 'Wood'))
                n_leaf += 1
    # ---- flight 1: north end, climbing south
    for i in range(1, N1):
        made.append(_tread(f'Stair1_Tread_{i:02d}', XW[0] + .031, XW[1] - .031, Y_FOOT - (i - 1) * T, -1, FL1 + i * R, plank))
    y_a, y_b = Y_FOOT + NOSE, Y_HALF
    for k, (x0, x1) in enumerate(((XW[0] + .001, XW[0] + .03), (XW[1] - .03, XW[1] - .001))):
        made.append(_stringer(f'Stair1_String_{k}', x0, x1, y_a, FL1 + R, y_b, Z_HALF, FL1 + .001, timber))
    # ---- half landing: boards on a frame, across both flights against the south wall
    made.append(_box('Stair_Landing_Half', (XW[0] + .001, Y_SOUTH + .001, Z_HALF - BOARD), (X_EDGE - .031, Y_HALF + NOSE, Z_HALF), plank, 'Wood'))
    made.append(_box('Stair_Landing_Half_Beam', (XW[0] + .001, Y_HALF + NOSE - .1, FL1 + (N1 - 1) * R + .001), (X_EDGE - .031, Y_HALF + NOSE - .001, Z_HALF - BOARD - .001),
                     timber, 'Wood'))
    # ---- flight 2: from the half landing, climbing north
    for j in range(1, N2):
        made.append(_tread(f'Stair2_Tread_{j:02d}', XE[0] + .031, XE[1] - .031, Y_HALF + (j - 1) * T, 1, Z_HALF + j * R, plank))
    for k, (x0, x1) in enumerate(((XE[0] + .001, XE[0] + .03), (XE[1] - .03, XE[1] - .001))):
        made.append(_stringer(f'Stair2_String_{k}', x0, x1, Y_HALF - NOSE, Z_HALF + R, Y_TOP - NOSE - .001, FL2 - (NOSE + .001) / T * R, Z_HALF + .001, timber))
    # ---- top landing, flush with the upper floor and open to it on the east
    made.append(_box('Stair_Landing_Top', (SPINE[1] + .006, Y_TOP - NOSE, FL2 - BOARD), (X_EDGE - .001, Y_NORTH, FL2), plank, 'Wood'))
    made.append(_box('Stair_Landing_Top_Beam', (SPINE[1] + .006, Y_TOP - NOSE + .001, Z_HALF + (N2 - 1) * R + .001), (X_EDGE - .031, Y_TOP - NOSE + .1, FL2 - BOARD - .001),
                     timber, 'Wood'))
    # ---- spine wall: plaster panel between the flights (under the half landing as its own panel, so its box stays below the landing)
    z_rail = lambda y: Z_HALF + (y - Y_HALF) / T * R + RAIL_H     # flight 2's nosing line + 0.9 m
    made.append(_box('Stair_Spine_Under_Landing', (SPINE[0], Y_SOUTH + .002, FL1 + .001), (SPINE[1], Y_HALF + NOSE - .101, Z_HALF - BOARD - .001), plaster, 'Main'))
    yp0, yp1 = Y_HALF + NOSE + .101, Y_NORTH - .101          # between the landing post and the north post
    poly = [(yp0, FL1 + .001), (yp1, FL1 + .001), (yp1, FL2 + RAIL_H - .081), (Y_TOP, FL2 + RAIL_H - .081), (yp0, z_rail(yp0) - .081)]
    made.append(_prism('Stair_Spine_Wall', _ccw(poly), SPINE[0], SPINE[1], plaster, 'Main'))
    sx = (SPINE[0] + SPINE[1]) / 2
    made.append(_bar('Stair_Spine_Rail_Slope', (sx, yp0, z_rail(yp0)), (sx, Y_TOP, FL2 + RAIL_H), .1, .08, lacquer, 'Wood'))
    made.append(_bar('Stair_Spine_Rail_Top', (sx, Y_TOP, FL2 + RAIL_H), (sx, yp1, FL2 + RAIL_H), .1, .08, lacquer, 'Wood'))
    made.append(_box('Stair_Spine_Post_North', (SPINE[0] - .005, Y_NORTH - .1, FL1 + .001), (SPINE[1] + .005, Y_NORTH, FL2 + RAIL_H + .04), timber, 'Wood', grain='z'))
    made.append(_box('Stair_Spine_Post_Landing', (SPINE[0] - .005, Y_HALF + NOSE + .001, FL1 + .001), (SPINE[1] + .005, Y_HALF + NOSE + .1, z_rail(Y_HALF + NOSE + .1) + .04),
                     timber, 'Wood', grain='z'))
    # wall rail along flight 1 on the spine wall's west face (6 x 6 cm on the wall, 0.85 m over the nosings)
    z1 = lambda y: FL1 + R + (Y_FOOT - y) / T * R + .85
    made.append(_bar('Stair1_Wall_Rail', (SPINE[0] - .036, Y_FOOT - .05, z1(Y_FOOT - .05)), (SPINE[0] - .036, yp0 - .001, z1(yp0 - .001)), .06, .06, lacquer, 'Wood'))
    # ---- screen closing the space under flight 2 and the top landing: plaster panels in a timber frame, on the dining-room side
    made.append(_box('Stair_Screen_East', (X_EDGE - .03, Y_SOUTH + .002, FL1 + .001), (X_EDGE - .001, Y_NORTH, 3.809), plaster, 'Main'))
    made.append(_box('Stair_Screen_North', (SPINE[1] + .006, Y_NORTH - .03, FL1 + .001), (X_EDGE - .031, Y_NORTH, FL2 - BOARD - .001), plaster, 'Main'))
    ys = (Y_SOUTH + .06, (Y_SOUTH + Y_NORTH) / 2, Y_NORTH - .06)
    for k, y in enumerate(ys):
        made.append(_box(f'Stair_Screen_Post_{k}', (X_EDGE + .001, y - .05, FL1 + .001), (X_EDGE + .08, y + .05, 3.808), timber, 'Wood', grain='z'))
    for k, z in enumerate((FL1 + .001, 2.2)):
        for m, (a, b) in enumerate(zip(ys[:-1], ys[1:])):
            made.append(_box(f'Stair_Screen_Rail_{k}{m}', (X_EDGE + .001, a + .051, z), (X_EDGE + .06, b - .051, z + (.12 if k == 0 else .1)), timber, 'Wood', grain='y'))
    # ---- upper-floor balustrade along the well edge, from the south wall to the top landing (as the balcony's)
    xb = X_EDGE + .04
    posts = np.linspace(Y_SOUTH + .06, Y_TOP - .06, 3)
    for k, y in enumerate(posts):
        made.append(_box(f'Well_Rail_Post_{k}', (xb - .04, y - .04, FL2 + .001), (xb + .04, y + .04, FL2 + RAIL_H - .081), lacquer, 'Wood', grain='z'))
    made.append(_box('Well_Rail_Top', (xb - .05, Y_SOUTH + .02, FL2 + RAIL_H - .08), (xb + .05, Y_TOP - .02, FL2 + RAIL_H), lacquer, 'Wood', grain='y'))
    n_bal = 0
    for m, (a, b) in enumerate(zip(posts[:-1], posts[1:])):
        made.append(_box(f'Well_Rail_Bottom_{m}', (xb - .03, a + .041, FL2 + .07), (xb + .03, b - .041, FL2 + .13), lacquer, 'Wood', grain='y'))
        m = int(round((b - a) / .28))
        for y in np.linspace(a, b, m + 1)[1:-1]:
            made.append(_box(f'Well_Rail_Baluster_{n_bal:02d}', (xb - .015, y - .015, FL2 + .131), (xb + .015, y + .015, FL2 + RAIL_H - .081), timber, 'Wood', grain='z', detail=1, bevel=0))
            n_bal += 1
    # ---- interaction sockets at the three guest-room door boards (Board, x 0.56..0.62, 0.9 m wide, on the rooms' solid east wall)
    doors = {}
    for k, y in enumerate((.17, 3.12, 5.30), 1):
        board = [q for q in S['parts'] if q.type == 'MESH' and q.name.startswith('Board_Part') and near(_bnd(q)[0][0], .56, .02) and near(_bnd(q)[1][0], .62, .02)
                 and near((_bnd(q)[0][1] + _bnd(q)[1][1]) / 2, y, .02)]
        assert len(board) == 1, (k, y, [q.name for q in board])
        ti_core.socket(f'Socket_GuestRoom_{k}', (.62, y, FL2), rot=(0, 0, -math.pi / 2)); doors[f'Socket_GuestRoom_{k}'] = [.62, y, FL2]
    S['stair_v002'] = {
        'removed_v001_parts': {k: v[1] for k, v in removed.items()}, 'removed_v001_triangles': sum(v[0] for v in removed.values()),
        'new_parts': len(made), 'new_triangles': sum(len(p.vertices) - 2 for o in made for p in o.data.polygons),
        'risers': N1 + N2, 'riser_m': round(R, 4), 'tread_m': T, 'nosing_m': NOSE, 'pitch_deg': round(math.degrees(math.atan2(R, T)), 1),
        'flight_widths_m': [round(XW[1] - XW[0], 3), round(XE[1] - XE[0], 3)], 'half_landing': {'z_m': round(Z_HALF, 3), 'y_m': [Y_SOUTH, round(Y_HALF, 3)]},
        'top_landing': {'z_m': FL2, 'y_m': [round(Y_TOP, 3), Y_NORTH], 'opens_east_onto_upper_floor_at_x_m': X_EDGE},
        'foot': {'y_m': Y_FOOT, 'faces': 'north (+y), the dining room'}, 'balusters': n_bal, 'trimmed_wall': trimmed,
        'hall_windows': {'bays': len(BAYS), 'openings_m': [1.04, 1.38], 'sill_z_m': SILL[1], 'head_z_m': HEAD[0], 'leaves': n_leaf,
                         'leaf_m': [round((1.04 - .004) / 2, 3), round(HEAD[0] - SILL[1] - .02, 3)], 'open_deg': 90, 'leaf_reach_onto_balcony_m': .52,
                         'balcony_clear_m': .89, 'closable_in_game': False},
        'guest_room_sockets': {'at_blender_xyz': doors, 'forward': '+x, out of the door into the upper hall',
                               'use': 'where the game puts the interact prompt; the door boards are fixed on a solid wall'}}
    print('STAIR_V002', S['stair_v002'], flush=True)
