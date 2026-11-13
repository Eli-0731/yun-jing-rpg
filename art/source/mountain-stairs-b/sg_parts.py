"""SG mountain-city stair kit (work pack B-104h part 2): geometry and palette.

Coordinates: Blender Z-up, 1 unit = 1 m, the stair climbs towards +Y, so the model front (-Y) is the foot of the flight.
SG01 origin: centre of the footprint at ground level (z = 0 under the first riser).

Step rule (modeling-style-spec-v1 section 4, a world constant): rise 0.15-0.18 m, tread 0.28-0.32 m.
The pack lists SG01 as "3 x 6 x 3 m (10 steps)"; ten steps over 3 m would be 0.30 m risers, so the run keeps ten steps at
0.16 x 0.32 m: 1.6 m rise over 3.2 m, inside the 3 x 6 x 3 m limit.
"""
import bpy, math, random
from mathutils import Vector, Matrix, noise
from ti_core import S, mesh, surface, socket, box, boolean
import cr_mats as cm
from cr_parts import rbox, sheet, set_attr_list

# ------------------------------------------------------------------ SG01 dimensions
N, RISE, TREAD = 10, .16, .32
Y0, Y1 = -N * TREAD / 2, N * TREAD / 2          # -1.6 .. 1.6
KX0, KX1, PX = 1.2, 1.48, 1.5                   # kerb inner face, kerb outer face, plinth outer face
WALK = 2 * KX0
SLOPE = math.atan2(RISE, TREAD)
COPE_UP, COPE_T = .26, .2                       # coping top above the nosing line; coping thickness (vertical)
SEAT_UP = .4                                    # post seats: top on a line parallel to the nosings, 0.4 m above it
POST_Y = (Y0 + .2, 0., Y1 - .2)                 # post seat centres (bottom newel, middle seat, top newel): 1.4 m apart
KXC = (KX0 + KX1) / 2
SOCK = .15                                      # square post socket, 0.15 m, 0.1 m deep


def nose_z(y):
    """Line through the step nosings: nosing of step k sits at (Y0 + (k-1) TREAD, k RISE)."""
    return RISE + (y - Y0) * RISE / TREAD


def seat_top(y): return nose_z(y) + SEAT_UP
def cope_top(y): return nose_z(y) + COPE_UP


# ------------------------------------------------------------------ palette
def _stone_set(name, n, light, dark, **kw):
    shade = [(1., 1., 1.), (.84, .85, .87), (1.07, 1.02, .93), (.93, .97, 1.02)]
    return [cm.stone(f'{name}_{i}', light=tuple(c * f for c, f in zip(light, shade[i])), dark=tuple(c * f for c, f in zip(dark, shade[i])), **kw) for i in range(n)]


def palette():
    P = {}
    # treads: warm grey, foot-polished down the middle (wear attribute); risers and kerbs: the blue-grey granite of the pack
    P['tread'] = _stone_set('Tread_Granite', 3, light=(.26, .255, .24), dark=(.12, .118, .112), ochre=(.3, .26, .19), moss=.55, lichen=.25, crack=.4,
                            wear='wear', polish=(.3, .285, .255))
    P['wall'] = _stone_set('Kerb_Granite', 4, light=(.215, .245, .265), dark=(.085, .1, .112), ochre=(.24, .22, .17), moss=1.15, lichen=.55, crack=.5)
    P['cope'] = _stone_set('Coping_Granite', 2, light=(.215, .232, .243), dark=(.095, .104, .112), ochre=(.28, .25, .19), moss=.85, lichen=.5, crack=.45)
    P['repair'] = cm.stone('Repair_Granite', light=(.4, .395, .37), dark=(.2, .195, .18), ochre=(.31, .29, .23), moss=.05, lichen=.03, crack=.25)
    P['soil'] = cm.packed_earth('Joint_Earth', dark=(.03, .021, .013), light=(.075, .052, .032), wet_top=-1., wet_low=-2., dry_low=5., dry_top=6.)
    P['moss'] = cm.moss_tuft('Joint_Moss', soft=True)
    P['grass'] = cm.weed_leaf('Crack_Grass', (.04, .062, .018), (.15, .19, .045), (.3, .29, .085))
    P['dry'] = cm.weed_leaf('Crack_Grass_Dry', (.07, .07, .025), (.2, .18, .065), (.33, .27, .11))
    P['fern'] = cm.fern('Wall_Fern')
    return P


# ------------------------------------------------------------------ small growth (same helpers as tea-terraces-b te_terrace.py)
def grass_tuft(name, c, n, h, mat, R, lean=.3, detail=2, spread=.05):
    c = Vector(c)
    for b in range(n):
        a = R.uniform(0, math.tau); L = h * R.uniform(.55, 1.); wid = R.uniform(.011, .019)
        base = c + Vector((math.cos(a), math.sin(a), 0)) * R.uniform(0, spread) - Vector((0, 0, .01))
        bend = R.uniform(.15, lean); turn = a + R.uniform(-.5, .5); side = Vector((-math.sin(turn), math.cos(turn), 0))
        def fn(u, v, base=base, L=L, wid=wid, bend=bend, turn=turn, side=side):
            out = Vector((math.cos(turn), math.sin(turn), 0))
            p = base + out * (L * bend * v * v) + Vector((0, 0, L * (v - .35 * bend * v * v)))
            return tuple(p + side * ((u - .5) * 2 * wid * (1 - v * .85)))
        sheet(name, 1, 3, fn, mat, solid=.0012, rim=False, detail=detail, grain='z')


def fern(name, q, mat, R, n=7, L=.24, out=(0, -1, 0), detail=2):
    q = Vector(q); o = Vector(out).normalized()
    for b in range(n):
        a = math.atan2(o.y, o.x) + R.uniform(-1.2, 1.2); up = R.uniform(-.1, .7); Lb = L * R.uniform(.6, 1.)
        dirv = Vector((math.cos(a), math.sin(a), 0)); side = Vector((-dirv.y, dirv.x, 0))
        def fn(u, v, dirv=dirv, side=side, Lb=Lb, up=up):
            p = q + dirv * (Lb * v) + Vector((0, 0, Lb * (up * v - .55 * v * v)))
            w = .035 * math.sin(math.pi * min(v * 1.1, 1.))
            return tuple(p + side * ((u - .5) * 2 * w))
        sheet(name, 2, 6, fn, mat, solid=.001, detail=detail, grain='z')


def moss_patch(name, q, n, r, mat, seed=0, flat=1., snap_each=False, **kw):
    """Thin broken colonies along a joint, hugging the face (n = outward normal)."""
    n = Vector(n).normalized(); a = n.cross(Vector((0, 0, 1)) if abs(n.z) < .9 else Vector((1, 0, 0))).normalized(); b = n.cross(a); q = Vector(q)
    kw.setdefault('detail', 2); R = random.Random(seed * 13 + 5)
    for k in range(3):
        rk = r * (.66 if k == 0 else R.uniform(.26, .4)); off = 0 if k == 0 else r * R.uniform(.55, .85); turn = R.uniform(0, math.tau); s_ = seed + k * 3.7
        c = q + a * (math.cos(turn) * off * 1.3) + b * (math.sin(turn) * off * .8)
        if snap_each:   # each colony sits on the stone it actually covers (neighbouring blocks differ by a few mm)
            hit = snap(tuple(c + n * .2), tuple(-n))
            if hit is None or hit[1].dot(n) < .95: continue
            c = hit[0]
        def fn(u, v, c=c, rk=rk, s_=s_):
            t = u * math.tau; cx, cy = math.cos(t), math.sin(t)
            e = rk * v * (.72 + .75 * noise.noise(Vector((cx * 1.2 + s_, cy * 1.2, s_ * .3))) + .28 * noise.noise(Vector((cx * 3.4 + s_, cy * 3.4, s_))))
            h = flat * (rk * .075 * (1 - v * v) ** .5)
            p = c + a * (cx * e * 1.3) + b * (cy * e * .8) + n * (h - .004 * (1 - (1 - v * v) ** .5) - rk * .015)   # rim buried 4 mm in the stone
            return (p.x, p.y, max(p.z, .003))
        surface(name, 16 if k == 0 else 8, 3 if k == 0 else 2, fn, mat, closed_u=True, **{**kw, 'detail': kw['detail']})


# ------------------------------------------------------------------ helpers
def snap(origin, direction):
    """First stone surface hit from origin along direction (location, normal) among the parts built so far, or None."""
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    ok, loc, nrm, *_ = bpy.context.scene.ray_cast(dg, Vector(origin), Vector(direction).normalized())
    return (loc, nrm) if ok else None


def set_wear(o, fn):
    """Per-vertex 'wear' (x = 0..1) from the world position: how polished by feet the stone is there."""
    me = o.data; M = o.matrix_world; N3 = M.to_3x3()
    up = lambda v: max(0., min(1., ((N3 @ v.normal).normalized().z - .35) / .5))   # tops polish, risers only near the nosing
    set_attr_list(o, 'wear', [(max(0., min(1., fn(M @ v.co))) * (.25 + .75 * up(v)), 0., 0.) for v in me.vertices])


def cut_socket(o, c, name, sloped=False):
    """Square socket for a balustrade post: a 0.15 m hole with a flat floor 0.1 m below c (the top surface at the hole centre).
    On the sloped coping the hole is vertical, so its uphill lip stands higher than c by half the hole times the slope."""
    up = .06 + (SOCK / 2 * math.tan(SLOPE) if sloped else 0.)
    cutter = box(name + '_Cut', (c[0], c[1], c[2] - .1 + (.1 + up) / 2), (SOCK, SOCK, .1 + up), None, bevel=0)
    boolean(o, cutter)


def prism(V, F, prof, x0, x1):
    """Convex yz profile (counter-clockwise seen from +X) extruded from x0 to x1, appended to a collision mesh."""
    b = len(V); n = len(prof)
    V += [(x0, y, z) for y, z in prof] + [(x1, y, z) for y, z in prof]
    F.append(tuple(b + i for i in reversed(range(n)))); F.append(tuple(b + n + i for i in range(n)))
    for i in range(n):
        j = (i + 1) % n; F.append((b + i, b + j, b + n + j, b + n + i))


def cut_above(o, co, no):
    """Remove the part of o above the plane through co with normal no (world space; o is only translated) and cap the cut flat."""
    import bmesh
    from cr_parts import _sharp
    me = o.data; mi = o.matrix_world.inverted()
    bm = bmesh.new(); bm.from_mesh(me)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=mi @ Vector(co), plane_no=Vector(no).normalized(), clear_outer=True)
    edges = [e for e in bm.edges if len(e.link_faces) == 1]
    if edges: bmesh.ops.holes_fill(bm, edges=edges, sides=0)
    seen, islands = set(), []          # a chipped corner can leave a crumb above the cut: drop islands under 30 vertices
    for v in bm.verts:
        if v in seen: continue
        stack, comp = [v], []
        seen.add(v)
        while stack:
            q = stack.pop(); comp.append(q)
            for e in q.link_edges:
                w = e.other_vert(q)
                if w not in seen: seen.add(w); stack.append(w)
        islands.append(comp)
    small = [v for comp in islands if len(comp) < 30 for v in comp]
    if small and len(islands) > 1: bmesh.ops.delete(bm, geom=small, context='VERTS')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free(); me.update(); _sharp(me)


def wall_courses(P, R, side, zones, z0=0., name='Kerb_Wall', x0=KX0, x1=KX1, plinth=True, px=PX):
    """Coursed dressed blocks on one side wall. zones = [(y0, y1, bed(y), plane)] with plane = (point, normal) cutting the top,
    or None where the bed is level. Courses keep their joints at the zone edges; each block is a whole dressed stone,
    its top sawn along the bed plane (no squashed vertices). side = +1 / -1 (x sign)."""
    gap = .002; out = []
    ya_all, yb_all = zones[0][0], zones[-1][1]
    if plinth:   # base course 2 cm proud of the wall face, a plain dressed plinth
        y = ya_all
        while y < yb_all - .05:
            L = min(R.uniform(.7, 1.1), yb_all - y)
            if yb_all - (y + L) < .3: L = yb_all - y
            o = rbox(f'{name}_Plinth', (side * (x0 + px) / 2, y + L / 2, .07), (px - x0, L - gap, .14), R.choice(P['wall']),
                     r=.012, amp=.002, freq=5., hew=3, chips=R.choice((0, 0, 1)), seed=R.randrange(999), div=.09, flat='zZ')
            out.append(o); y += L
    heights = []
    z = .14 if plinth else z0
    top_max = max(zz[2](zz[1]) for zz in zones)
    while z < top_max - .01:
        h = R.uniform(.26, .36); heights.append((z, h)); z += h
    for zi, (yz0, yz1, bed, plane) in enumerate(zones):
        zh = list(heights)
        if plane is None:   # level zone: the top course takes up whatever is left, never a thin sliver under the cap
            top = bed(yz0); zh = []
            for z, h in heights:
                if z >= top - .01: break
                if top - (z + h) < .14: zh.append((z, top - z)); break
                zh.append((z, h))
        for course, (z, h) in enumerate(zh):
            if max(bed(yz0), bed(yz1)) <= z + .01: continue
            y = yz0; first = True
            while y < yz1 - .02:
                L = R.uniform(.55, 1.05)
                if first and course % 2: L = R.uniform(.25, .45)
                first = False
                if yz1 - (y + L) < .25: L = yz1 - y
                ya, yb = y, y + L; y = yb
                if max(bed(ya), bed(yb)) <= z + .01: continue
                if plane is not None and min(bed(ya), bed(yb)) < z + .02:
                    t = ya   # the sawn top meets this course: start the stone where the bed is 2 cm above the course bottom (the coping covers the rest)
                    while t < yb and bed(t) < z + .02: t += .004
                    ya = t
                    if yb - ya < .05: continue
                hh = h if plane is not None else min(h, bed(ya) - z)
                if hh < .02: continue
                o = rbox(f'{name}_{zi}_{course}', (side * (x0 + x1) / 2, (ya + yb) / 2, z + hh / 2), (x1 - x0, yb - ya - gap, hh - gap), R.choice(P['wall']),
                         r=.012, amp=.002, freq=5., hew=3, chips=R.choice((0, 1)) if plane is None else 0, seed=R.randrange(9999), div=.08, flat='zZ')
                if plane is not None and min(bed(ya), bed(yb)) < z + hh:   # any part of the top above the bed is sawn off
                    cut_above(o, plane[0], plane[1])
                out.append(o)
    return out


# ------------------------------------------------------------------ SG01
def sg01_straight_run(P):
    R = random.Random('SG01_StraightRun')
    # steps: three dressed blocks per tread, joints staggered and kept off the walking lines (x = 0, +-0.95) the checks measure
    for k in range(1, N + 1):
        yf = Y0 + (k - 1) * TREAD
        back = .05 if k < N else 0.
        nose = .015
        lo_z = max(0., (k - 1) * RISE - .03)
        ya, yb = yf - nose, yf + TREAD + back
        if k == N: yb = Y1
        if k % 2: j1, j2 = R.uniform(-.74, -.48), R.uniform(.24, .52)
        else: j1, j2 = R.uniform(-.52, -.24), R.uniform(.48, .74)
        xs = [-KX0 - .01, j1, j2, KX0 + .01]
        for i in range(3):
            xa, xb = xs[i] + (.003 if i else 0), xs[i + 1] - (.003 if i < 2 else 0)
            repair = (k == 6 and i == 2)
            mat = P['repair'] if repair else R.choice(P['tread'])
            chips = 1 if R.random() < .35 else 0
            o = rbox(f'Step_{k:02d}_{i}', ((xa + xb) / 2, (ya + yb) / 2, (lo_z + k * RISE) / 2), (xb - xa, yb - ya, k * RISE - lo_z), mat,
                     r=.014 if not repair else .008, amp=.0025, freq=4.5, chips=chips, hew=4, seed=k * 10 + i, div=.08, flat='zZyY' if k == N else 'zZy')
            set_wear(o, lambda p, yf=yf: math.exp(-(p.x / .75) ** 2) * (.55 + .45 * max(0., 1 - (p.y - yf) / TREAD)))
            o['tread'] = True
    # back wall under the top tread (seen from the top end of the run until the landing is set against it)
    Rb = random.Random('SG01_back')
    z = 0.; c = 0
    while z < (N - 1) * RISE - .03 - .01:
        h = min(Rb.uniform(.28, .36), (N - 1) * RISE - .03 - z)
        x = -KX0 - .005; first = True
        while x < KX0 - .02:
            L = Rb.uniform(.5, .95) if not (first and c % 2) else Rb.uniform(.25, .4)
            first = False
            if KX0 - (x + L) < .25: L = KX0 + .005 - x
            rbox(f'Back_Wall_{c}', (x + L / 2, Y1 - .15, z + h / 2), (L - .002, .3, h - .002), Rb.choice(P['wall']), r=.012, amp=.002, freq=5., hew=3,
                 chips=Rb.choice((0, 1)), seed=Rb.randrange(9999), div=.09, flat='Y')
            x += L
        z += h; c += 1
    # kerbs (side walls), sloped coping with the middle post socket, newel caps at both ends
    nrm = Vector((0, -math.sin(SLOPE), math.cos(SLOPE)))
    yb0, yb1 = POST_Y[0] + .2, POST_Y[2] - .2          # newel caps occupy y < yb0 and y > yb1
    cap_bot = [seat_top(POST_Y[0]) - .3, seat_top(POST_Y[2]) - .3]
    for side in (-1, 1):
        sd = 'L' if side < 0 else 'R'
        Rs = random.Random(f'SG01_kerb{side}')
        bed_c = lambda y: cope_top(y) - COPE_T + .02          # sloped bed: 2 cm into the coping
        zones = [(Y0, yb0, lambda y: cap_bot[0] + .01, None),
                 (yb0, yb1, bed_c, ((0., 0., bed_c(0.)), tuple(nrm))),
                 (yb1, Y1, lambda y: cap_bot[1] + .01, None)]
        wall_courses(P, Rs, side, zones, name=f'Kerb_{sd}')
        # newel caps: flat tops on the post-seat line, a square post socket in each
        for i, py in ((0, POST_Y[0]), (2, POST_Y[2])):
            top = seat_top(py); zb = top - .3
            cap = rbox(f'Newel_Cap_{sd}{i}', (side * KXC, py, (zb + top) / 2), (KX1 - KX0 + .03, .4, .3), Rs.choice(P['cope']),
                       r=.016, amp=.002, freq=4., hew=3, chips=0, seed=40 + i + side, div=.07, flat='Z')
            cut_socket(cap, (side * KXC, py, top), f'Socket_Hole_{sd}{i}')
            socket(f'Socket_Post_{sd}{i}', (side * KXC, py, top))
        # sloped coping: two long stones from newel to newel, the joint kept off the middle socket
        joint = .42 if side > 0 else .36
        for ya, yb in ((yb0 - .05, joint - .001), (joint + .001, yb1 + .05)):
            ym = (ya + yb) / 2; Ls = (yb - ya) / math.cos(SLOPE)
            c = Vector((side * KXC, ym, cope_top(ym))) - nrm * (COPE_T * math.cos(SLOPE) / 2)
            cs = rbox(f'Coping_{sd}', tuple(c), (KX1 - KX0 + .02, Ls, COPE_T * math.cos(SLOPE)), Rs.choice(P['cope']), r=.018, amp=.002, freq=4.,
                      hew=3, chips=1, seed=int(ym * 100) + side, div=.08, rot=(SLOPE, 0, 0), flat='Z')
            if ya < POST_Y[1] < yb:
                cut_socket(cs, (side * KXC, POST_Y[1], cope_top(POST_Y[1])), f'Socket_Hole_{sd}1', sloped=True)
        socket(f'Socket_Post_{sd}1', (side * KXC, POST_Y[1], cope_top(POST_Y[1])))
    # growth: moss only in the shaded (+X) joints and the inner corners, a few weeds at the tread ends, ferns at the wall foot
    Rg = random.Random('SG01_growth')
    for k in range(1, N + 1):
        yf = Y0 + (k - 1) * TREAD
        for side in (-1, 1):
            if Rg.random() < (.75 if side > 0 else .3):
                moss_patch('Corner_Moss', (side * (KX0 - .02), yf + Rg.uniform(.08, .26), k * RISE + .002), (0, 0, 1), Rg.uniform(.035, .06), P['moss'], seed=k * 3 + side, flat=.7)
            if Rg.random() < (.35 if side > 0 else .15):
                grass_tuft('Crack_Grass', (side * (KX0 - .025), yf + Rg.uniform(.12, .28), k * RISE), Rg.randint(4, 7), Rg.uniform(.07, .13),
                           P['grass'] if Rg.random() < .7 else P['dry'], Rg)
    for i in range(7):   # moss on the shaded kerb face joints, low down
        y = Rg.uniform(Y0 + .2, Y1 - .3); zt = min(Rg.uniform(.1, .7), cope_top(y) - .3)
        if zt < .05: continue
        hit = snap((PX + .2, y, zt), (-1, 0, 0))
        if hit is None: continue
        moss_patch('Wall_Moss', tuple(hit[0]), tuple(hit[1]), Rg.uniform(.05, .09), P['moss'], seed=50 + i, snap_each=True)
    for side, y in ((1, .42), (1, -1.16), (-1, .36)):   # grass in the coping joints (kept inside the 3 m width)
        grass_tuft('Coping_Grass', (side * (KX0 + .05), y, cope_top(y) - .005), Rg.randint(4, 6), Rg.uniform(.07, .11), P['grass'], Rg, spread=.03)
    # sockets and the design numbers the checks use
    socket('Socket_Bottom', (0, Y0, 0), rot=(0, 0, math.pi))
    socket('Socket_Top', (0, Y1, N * RISE))
    S['prop'] = dict(kind='stair', steps=N, rise=RISE, tread=TREAD, walk_w=WALK, y0=Y0, y1=Y1, posts=len(POST_Y))
    # collision: the ten steps as boxes, the two kerbs as newel boxes and a sloped prism
    V, F = [], []
    for k in range(1, N + 1):
        yf = Y0 + (k - 1) * TREAD
        prism(V, F, [(yf, (k - 1) * RISE), (Y1, (k - 1) * RISE), (Y1, k * RISE), (yf, k * RISE)], -KX0, KX0)
    for side in (-1, 1):
        xa, xb = sorted((side * KX0, side * PX))
        prism(V, F, [(Y0, 0.), (POST_Y[0] + .2, 0.), (POST_Y[0] + .2, seat_top(POST_Y[0])), (Y0, seat_top(POST_Y[0]))], xa, xb)
        prism(V, F, [(POST_Y[0] + .2, 0.), (POST_Y[2] - .2, 0.), (POST_Y[2] - .2, cope_top(POST_Y[2] - .2)), (POST_Y[0] + .2, cope_top(POST_Y[0] + .2))], xa, xb)
        prism(V, F, [(POST_Y[2] - .2, 0.), (Y1, 0.), (Y1, seat_top(POST_Y[2])), (POST_Y[2] - .2, seat_top(POST_Y[2]))], xa, xb)
    S['collision_mesh'] = (V, F)


SG01_NOTE = ('山城大石階直段（三視圖 SG01/STRAIGHT-RUN candidate-03）：10 階，每階高 0.16 m、深 0.32 m（世界常數：高 0.15–0.18、深 0.28–0.32），'
             '一段升 1.6 m、水平 3.2 m、坡度 26.6°；總寬 3.0 m，兩側各 0.28 m 側欄，中間淨寬 2.4 m。踏面每階三塊錯縫整石，中間被腳磨得較亮；'
             '踢面、側欄、背牆是青灰花崗岩整砌，底層一道勒腳。側欄頂是兩塊順坡的壓頂石（厚 0.2 m），兩端各一塊平頂端柱座石；三個 0.15 m 方形柱孔、孔底平、深 0.1 m，'
             '水平間距 1.4 m：兩端柱孔在平頂上（頂面高出踏步前緣線 0.4 m），中段柱孔直接開在斜壓頂上（頂面高出前緣線 0.26 m），'
             '所以 SG03 斜段中柱的柱腳要切斜、比端柱長 0.14 m。第 6 階右側一塊較新的補石；苔只長在右側（背光側）接縫與踏面內角。'
             '接口：Socket_Bottom 在第一階前緣地面（z 0）、Socket_Top 在頂端（y +1.6、z 1.6），接 SG02 平台頂面。'
             '工作包寫「3 × 6 × 3 m（10 階）」：10 階升 3 m 每階要 0.30 m，超出世界常數，所以保留 10 階、改成每階 0.16 m，尺寸在上限內。')


def register(ASSETS):
    ASSETS['SG01_StraightRun'] = dict(zh='山城大石階直段', kind='stair', palette=palette, build=sg01_straight_run, limit=(3., 6., 3.), tex=2048, ver='v001',
        box=((-1.5, Y0 - .02, 0.), (1.5, Y1 + .001, 3.)), ref='SG01/STRAIGHT-RUN', slot='B1_SectGateStairs', minTier='standard', clamp_max=.03,
        origin='centre of the footprint at ground level; the flight climbs towards +Y, its foot (first riser) faces -Y', note=SG01_NOTE)
