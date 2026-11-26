"""SG05 wide stair run and SG06 wide turning landing (work pack 2026-11-09 B-112h, batch C), grey-white granite #C9C6BD.

SG05 (three-view SG05-cand-1): 6 x 3.2 x 2.1 m. The same ten steps as SG01 (rise 0.16 m, tread 0.32 m, 1.6 m up over 3.2 m), the same
kerbs (0.28 m wide), coping line, newel caps and post sockets (same y and z as SG01, x at +-2.84 m), so the SG03 balustrades sit on it
unchanged. A carved 'imperial way' slab (御路石, 1.24 m wide) runs up the middle: its top follows the line of the step nosings, a raised frame
round a field of low-relief clouds (curls with incised spirals, a winding tail between them); a flight of steps 2.08 m wide on each side.
Origin: centre of the footprint at ground level; the flight climbs towards +Y. 2.1 m is the top of the newel caps (2.06 m).

SG06 (three-view SG06-cand-3): 7 x 7 x 0.8 m, walking surface level at z 0.8. The SG02 language at a larger size: a ring of dressed
coping stones (0.5 m) round a field of 1 m slabs with soil joints, a carved square 'heart stone' (方心石, 2 x 2 m) in the middle, its cloud
medallion cut below the walking surface (nothing stands above z 0.8). Under the coping a plinth and two courses of wall with a carved
cloud plaque in the middle of each face. A round drum seat in each corner (diameter 0.86 m, 0.3 m tall, the size of SG02's lotus base)
with Socket_Lantern_* on its top for the existing lanterns. SG05's Socket_Top meets Socket_Edge_*.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix
from ti_core import S, mesh, socket, lathe, sphere
import cr_mats as cm
from cr_parts import rbox
import sg_parts as SG

N, RISE, TREAD, Y0, Y1, SLOPE = SG.N, SG.RISE, SG.TREAD, SG.Y0, SG.Y1, SG.SLOPE
KX0, KX1, PX = 2.70, 2.98, 3.0                 # kerb inner face, kerb outer face, plinth outer face (SG01: 1.2 / 1.48 / 1.5)
KXC = (KX0 + KX1) / 2
PW = .62                                       # half width of the imperial-way slab bay
FLIGHT = KX0 - PW                              # 2.08 m of steps on each side
POST_Y = SG.POST_Y
PANEL_Y0, PANEL_Y1 = Y0 - .015, Y1 - TREAD - .018   # the slab runs from the first nosing to the riser of the top step


def smooth(a, b, x):
    t = max(0., min(1., (x - a) / (b - a))); return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ palette (the RS03 gate granite: #C9C6BD under the game's light)
def palette():
    P = {}
    # three tread stones from three quarry faces (paler, warmer, greyer): the RS03 granite white overall, but a field of slabs no longer reads as one sheet
    P['tread'] = [cm.stone(f'Tread_GraniteWhite_{i}', light=l, dark=d, ochre=(.52, .49, .42), moss=.65, lichen=.85, crack=.45, wear='wear', polish=(.9, .88, .82))
                  for i, (l, d) in enumerate((((.82, .80, .74), (.6, .585, .53)), ((.81, .77, .69), (.56, .53, .46)), ((.74, .735, .71), (.52, .515, .49))))]
    # walls and kerbs: a little rain-darkened, more lichen and moss low down
    P['wall'] = SG._stone_set('Kerb_GraniteWhite', 4, light=(.7, .69, .64), dark=(.46, .45, .41), ochre=(.46, .44, .37), moss=1.0, lichen=.8, crack=.5, wet_z=.3)
    P['cope'] = SG._stone_set('Coping_GraniteWhite', 2, light=(.8, .785, .73), dark=(.58, .565, .515), ochre=(.5, .47, .4), moss=.45, lichen=.4, crack=.35)
    P['repair'] = cm.stone('Repair_GraniteWhite', light=(.9, .885, .83), dark=(.68, .665, .61), ochre=(.55, .52, .45), moss=.03, lichen=.03, crack=.2)
    P['carve'] = cm.stone('Carved_GraniteWhite', light=(.84, .82, .76), dark=(.56, .545, .5), ochre=(.5, .47, .4), moss=.25, lichen=.35, crack=.15, wear='wear',
                          polish=(.9, .88, .82))
    # the cut-back field of a relief: grime and lichen settle there, so the raised clouds read against it
    P['carve_low'] = cm.stone('Carved_Recess_Granite', light=(.4, .39, .36), dark=(.23, .225, .205), ochre=(.33, .3, .24), moss=.7, lichen=.6, crack=.1)
    P['soil'] = cm.packed_earth('Joint_Earth', dark=(.03, .021, .013), light=(.075, .052, .032), wet_top=-1., wet_low=-2., dry_low=5., dry_top=6.)
    P['moss'] = cm.moss_tuft('Joint_Moss', soft=True)
    P['grass'] = cm.weed_leaf('Crack_Grass', (.04, .062, .018), (.15, .19, .045), (.3, .29, .085))
    P['dry'] = cm.weed_leaf('Crack_Grass_Dry', (.07, .07, .025), (.2, .18, .065), (.33, .27, .11))
    return P


# ------------------------------------------------------------------ carved relief
def curl(dx, dy, R, hand, turns=1.55, w=.0085):
    """A cloud curl: (body 0..1 with a soft edge, incised spiral groove 0..1) at offset (dx, dy) from its centre."""
    rho = math.hypot(dx, dy)
    body = 1 - smooth(R - .007, R + .003, rho)
    if rho > R - .012 or rho < .006: return body, 0.
    th = (math.atan2(dy, dx) * hand) % math.tau
    a = (R - .016) / (math.tau * turns)
    k0 = round((rho / a - th) / math.tau)
    d = min(abs(rho - a * (th + math.tau * k)) for k in (k0 - 1, k0, k0 + 1) if k >= 0 and k <= turns + .5)
    return body, (1 - smooth(w * .45, w, d)) * smooth(.006, .02, rho)


def cloud_field(s, t, heads, tails):
    """Layered clouds: tails first, heads over them (a later head covers the grooves of earlier ones). Returns (body, groove)."""
    body = groove = 0.
    for sc_fn, wid in tails:
        d = abs(s - sc_fn(t)); w = wid(t)
        if w <= 0: continue
        b = 1 - smooth(w - .006, w + .003, d)
        if b > 0:
            g = 1 - smooth(.0028, .0065, d)
            if b >= body: groove = g * b
            body = max(body, b)
    for cs, ct, R, hand in heads:
        b, g = curl(s - cs, t - ct, R, hand)
        if b > .02:
            groove = g if b > .5 else max(groove * (1 - b), g)
            body = max(body, b)
    return body, groove


def spiral_path(cx, cy, R, hand, turns=1.3, ds=.01, phase=0.):
    """A cloud curl as a line: from the rim (angle `phase`) spiralling in `turns` times towards the centre; hand +1 / -1."""
    th_max = turns * math.tau; pts = []; th = 0.
    while th <= th_max:
        r = R * (1 - .8 * th / th_max)
        a = phase + hand * th
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a), (1 - .45 * th / th_max) * min(1., max(.55, R / .15))))   # small curls take a thinner line
        th += ds / max(r, .02)
    return pts


def wave_path(fn, t0, t1, wfn=lambda t: 1., ds=.012):
    """A stream line s = fn(t) from t0 to t1, width factor wfn(t)."""
    n = max(2, int(abs(t1 - t0) / ds)); return [(fn(t0 + (t1 - t0) * i / n), t0 + (t1 - t0) * i / n, wfn(t0 + (t1 - t0) * i / n)) for i in range(n + 1)]


def circle_path(R, ds=.012):
    n = int(math.tau * R / ds); return [(R * math.cos(math.tau * i / n), R * math.sin(math.tau * i / n), 1.) for i in range(n + 1)]


def scroll_relief(name, paths, frame, nrm, mat, w=.016, h=.014, sink=.004, **kw):
    """Raised rounded scroll lines: a half-ellipse (half width w * path width, height h) swept along each path of (u, v, width)
    points, standing on the field surface frame(u, v) with outward normal nrm, its foot `sink` below the field. Ends taper and close."""
    V, F = [], []; prof = 7
    for path in paths:
        if len(path) < 3: continue
        P3 = [Vector(frame(u, v)) for u, v, _ in path]; base = len(V); n = len(path)
        closed = (P3[0] - P3[-1]).length < 1e-6               # a ring: no tapered ends, the tangent wraps round, no seam
        if closed: path, P3, n = path[:-1], P3[:-1], n - 1
        for i, (u, v, wf) in enumerate(path):
            if closed: t = (P3[(i + 1) % n] - P3[(i - 1) % n]).normalized()
            else: t = (P3[min(i + 1, n - 1)] - P3[max(i - 1, 0)]).normalized()
            N = Vector(nrm(u, v)); b = N.cross(t).normalized()
            end = min(i, n - 1 - i); taper = 1. if closed else min(1., .35 + .65 * end / 4)
            ww = w * wf * taper; hh = h * (.55 + .45 * wf) * taper
            for k in range(prof):
                a = math.pi * k / (prof - 1)
                V.append(tuple(P3[i] + b * (ww * math.cos(a)) + N * (hh * math.sin(a) - sink)))
        for i in range(n if closed else n - 1):
            j = (i + 1) % n
            for k in range(prof - 1):
                a0 = base + i * prof + k; b0 = base + j * prof + k; F.append((a0, a0 + 1, b0 + 1, b0))
        if not closed:
            F.append(tuple(base + k for k in range(prof)))
            F.append(tuple(base + (n - 1) * prof + k for k in range(prof - 1, -1, -1)))
    o = mesh(name, V, F, mat, smooth=True, **kw)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free(); o.data.update()
    return o


def ruyi_cloud(c, sc, sg, ang=0., tail_to=None):
    """One 如意 cloud in a local (u, v) frame: a big lobe, two side lobes curling in, a small lobe under (the head points +v,
    turned by ang), and a tail streaming from under the head to tail_to, thinning, ending in a small curl.
    Returns (balls [(u, v, R)], curls [[(u, v, width)]])."""
    ca, sa = math.cos(ang), math.sin(ang)
    rot = lambda x, y: Vector((c[0] + sc * (x * ca - y * sa), c[1] + sc * (x * sa + y * ca)))
    balls, curls = [], []
    for x, y, R, h, ph in ((0., 0., .13, sg, 0.), (-.15, -.05, .085, 1, 0.), (.15, -.05, .085, -1, 0.), (0., -.12, .06, -sg, math.pi)):
        q = rot(x, y); balls.append((q.x, q.y, R * sc))
        qc = rot(x, y + .01)
        curls.append(spiral_path(qc.x, qc.y, R * sc * .72, h, turns=1.25 if R > .1 else 1.05, phase=math.pi / 2 * h + ph + ang, ds=.006))
    if tail_to is not None:
        P0 = rot(sg * .08, -.14); P3 = Vector(tail_to); d = P3 - P0; nrm = Vector((-d.y, d.x)).normalized()
        P1 = P0 + d / 3 + nrm * d.length * .28; P2 = P0 + d * 2 / 3 - nrm * d.length * .28       # an S: the stream swings one way, then back
        L = d.length + 1e-6; m = max(10, int(L / (.01 * sc / .6)))
        line = []
        for k in range(m + 1):
            t = k / m; q = (1 - t) ** 3 * P0 + 3 * t * (1 - t) ** 2 * P1 + 3 * t * t * (1 - t) * P2 + t ** 3 * P3
            balls.append((q.x, q.y, sc * (.042 * (1 - t) + .022 * t))); line.append((q.x, q.y, 1. - .5 * t))
        # the tail does not end in a blob: it rolls on into a tightening curl turned back toward the head (卷雲收尾)
        tan = (P3 - P2).normalized(); back = P0 - P3; side = Vector((-tan.y, tan.x))
        if side.dot(back) < 0: side = -side
        r0 = sc * .045; C = P3 + side * r0; a0 = math.atan2(P3.y - C.y, P3.x - C.x)
        turn = 1 if Vector((-math.sin(a0), math.cos(a0))).dot(tan) > 0 else -1
        hook = []; nk = max(18, int(math.tau * r0 / (.006 * sc / .6)))
        for k in range(1, nk + 1):
            u = k / nk; a_ = a0 + turn * u * math.tau * .95; r = r0 * (1 - .5 * u)
            q = C + Vector((math.cos(a_), math.sin(a_))) * r
            balls.append((q.x, q.y, sc * (.02 - .007 * u))); hook.append((q.x, q.y, .5 - .25 * u))
        curls.append(line[:-1] + hook[:-2])
    return balls, curls


def mini_cloud(c, sc, sg, ang=0.):
    """A small 如意 head without a tail: fills the gaps."""
    return ruyi_cloud(c, sc * .5, sg, ang)


def cloud_relief(name, balls, curls, M, mat, ht=.02, curl_w=.011, curl_h=.007, res=.008, **kw):
    """Cloud bodies on a flat field: metaball lobes (u, v, R) in a local frame whose w = 0 is the field and +w points out of it,
    each lobe's dome rising ht above the field (smaller ones a little less), joined smoothly; what lies under the field is dropped,
    so the body meets the field in a clean outline. Raised half-round curl lines (width curl_w, height curl_h) lie on the domes.
    M (4x4) takes the local frame to the piece. Returns (body, curls) objects."""
    import bpy
    from mathutils.bvhtree import BVHTree
    mb = bpy.data.metaballs.new('MB_' + name); mb.resolution = res; mb.threshold = .6
    for x, y, R in balls:
        h = ht if R > .045 else ht * .8
        e = mb.elements.new(type='ELLIPSOID'); e.co = (x, y, -.015); e.radius = R / .575
        e.size_x = e.size_y = 1.; e.size_z = min(1., (.015 + h) / R); e.stiffness = 2.
    mo = bpy.data.objects.new('MB_' + name, mb); bpy.context.scene.collection.objects.link(mo)
    dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(mo.evaluated_get(dg))
    bpy.data.objects.remove(mo); bpy.data.metaballs.remove(mb)
    LV = [v.co.copy() for v in me.vertices]
    LF = [tuple(pl.vertices) for pl in me.polygons if max(LV[i].z for i in pl.vertices) > -.006]   # keep a hidden skirt under the field
    a0 = ht - .005                                       # where lobes overlap their fields add up: soft-cap the domes at ht
    for v in LV:
        if v.z > a0: v.z = a0 + .005 * math.tanh((v.z - a0) / .005)
    bpy.data.meshes.remove(me)
    used = sorted({i for f in LF for i in f}); remap = {o: n for n, o in enumerate(used)}
    LV = [LV[i] for i in used]; LF = [tuple(remap[i] for i in f) for f in LF]
    bvh = BVHTree.FromPolygons(LV, LF)
    body = mesh(name + '_Body', [tuple(M @ v) for v in LV], LF, mat, smooth=True, **kw)
    V, F = [], []; prof = 7; N = Vector((0, 0, 1))
    for path in curls:
        P3 = []
        for u, v, wf in path:
            hit = bvh.ray_cast(Vector((u, v, .3)), Vector((0, 0, -1)))
            P3.append(Vector((u, v, hit[0].z if hit[0] else 0.)))
        n = len(P3)
        if n < 3: continue
        base = len(V)
        for i in range(n):
            t = P3[min(i + 1, n - 1)] - P3[max(i - 1, 0)]; t.z = 0
            if t.length < 1e-9: t = Vector((1, 0, 0))
            t.normalize(); b = N.cross(t)
            end = min(i, n - 1 - i); taper = min(1., .35 + .65 * end / 4); wf = path[i][2]
            ww = curl_w * wf * taper; hh = curl_h * (.6 + .4 * wf) * taper
            for k in range(prof):
                a = math.pi * k / (prof - 1); V.append(tuple(M @ (P3[i] + b * (ww * math.cos(a)) + N * (hh * math.sin(a) - .003))))
        for i in range(n - 1):
            for k in range(prof - 1):
                a0 = base + i * prof + k; F.append((a0, a0 + 1, a0 + prof + 1, a0 + prof))
        F.append(tuple(base + k for k in range(prof)))
        F.append(tuple(base + (n - 1) * prof + k for k in range(prof - 1, -1, -1)))
    cu = mesh(name + '_Curls', V, F, mat, smooth=True, **kw)
    for o in (body, cu):
        bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free(); o.data.update()
    return body, cu


def heads_tails_paths(heads, tails, t0=0., t1=1.):
    paths = [spiral_path(cx, cy, R, hand, turns=1.25 if R > .09 else 1.05, phase=(math.pi / 2 if hand > 0 else -math.pi / 2) + cx * 3.1)
             for cx, cy, R, hand in heads]
    for fn, wfn, a, b in tails: paths.append(wave_path(fn, a, b, wfn))
    return paths


def yulu_height(s, t, hw, L, heads, tails):
    """SG05 slab top relative to the nosing line: frame +12 mm, a groove inside it, the field at -3 mm, clouds up to +10 mm."""
    FR = .075
    d = min(hw - abs(s), t, L - t)
    if d < FR:                                  # raised frame, its outer arris eased
        return .012 - .007 * (1 - min(1., d / .012)) ** 2 - .02 * smooth(FR - .006, FR + .004, d)
    if d < FR + .022:
        return -.01 + .003 * smooth(FR + .008, FR + .022, d)
    return -.007                                 # the cut-back field; the clouds stand on it as scroll lines


def relief_mesh(name, nu, nv, top, back, mat, mat_low=None, low=None, **kw):
    """Grid top(i, j) -> xyz with walls from its boundary down to back(xyz) -> xyz; the back stays open (it is buried)."""
    V, F, idx = [], [], {}; H = []
    for j in range(nv + 1):
        for i in range(nu + 1):
            idx[i, j] = len(V); xyz, hh = top(i, j); V.append(tuple(xyz)); H.append(hh)
    for j in range(nv):
        for i in range(nu):
            F.append((idx[i, j], idx[i + 1, j], idx[i + 1, j + 1], idx[i, j + 1]))
    ring = [(i, 0) for i in range(nu)] + [(nu, j) for j in range(nv)] + [(i, nv) for i in range(nu, 0, -1)] + [(0, j) for j in range(nv, 0, -1)]
    bot = {}
    for ij in ring:
        bot[ij] = len(V); V.append(tuple(back(Vector(V[idx[ij]]))))
    nf_top = len(F)
    for a, b in zip(ring, ring[1:] + ring[:1]):
        F.append((idx[b], idx[a], bot[a], bot[b]))
    o = mesh(name, V, F, mat, smooth=True, **kw)
    if mat_low is not None:                        # faces whose mean relief is below `low` (the cut-back field, the grooves) take the recess stone
        o.data.materials.append(mat_low)
        for fi in range(nf_top):
            if sum(H[v] for v in F[fi]) / len(F[fi]) < low: o.data.polygons[fi].material_index = 1
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free(); o.data.update()
    from cr_parts import _sharp
    _sharp(o.data, 50)
    return o


def yulu_panel(P):
    hw = PW - .003
    L = (PANEL_Y1 - PANEL_Y0) / math.cos(SLOPE)
    sp = (L - .9) / 4
    heads, tails = [], []
    for i in range(5):                          # five cloud heads up the slab, swinging side to side, each with two smaller curls
        ct = .45 + i * sp; sg = 1 if i % 2 == 0 else -1; cs = .17 * sg
        heads += [(cs - sg * .2, ct - .1, .085, sg), (cs + sg * .06, ct + .15, .095, -sg), (cs, ct, .15, sg)]
    tails.append((lambda t: .17 * math.cos(math.pi * (t - .45) / sp), lambda t: 1., .3, L - .3))           # the main stream swinging under the heads
    tails.append((lambda t: -.3 * math.cos(math.pi * (t - .45) / sp + .9), lambda t: .6, .45, L - .45))      # a thinner second stream
    heads += [(-.36, .2, .085, 1), (.36, .2, .085, -1), (-.36, L - .2, .07, -1), (.36, L - .2, .07, 1)]   # scroll ends at the foot and the head
    cell = .025; nu = int(round(2 * hw / cell)); nv = int(round(L / cell))
    cosA = math.cos(SLOPE); sinA = math.sin(SLOPE)

    def top(i, j):
        s = -hw + 2 * hw * i / nu; t = L * j / nv
        y = PANEL_Y0 + t * cosA
        hh = yulu_height(s, t, hw, L, heads, tails)
        return (s, y, SG.nose_z(y) + hh), hh
    o = relief_mesh('Yulu_Carved_Slab', nu, nv, top, lambda p: (p.x, p.y, 0.), P['carve'], mat_low=P['carve_low'], low=-.002, grain='y')
    SG.set_wear(o, lambda p: .35 * math.exp(-(p.x / .4) ** 2))
    M = Matrix.Translation((0., PANEL_Y0, SG.nose_z(PANEL_Y0) - .007)) @ Matrix(((1, 0, 0, 0), (0, cosA, -sinA, 0), (0, sinA, cosA, 0), (0, 0, 0, 1)))
    balls, curls = [], []
    n = 5; spc = (L - .85) / (n - 1)
    for i in range(n):
        sg = 1 if i % 2 == 0 else -1; cy_ = .42 + i * spc
        b, c = ruyi_cloud((.12 * sg, cy_), 1.42, sg, 0., tail_to=(-.34 * sg, min(cy_ + .38 * spc, L - .17))); balls += b; curls += c
        if i < n - 1:
            b, c = mini_cloud((.35 * sg, cy_ + .6 * spc), 1.3, -sg); balls += b; curls += c
    b, c = mini_cloud((-.34, .18), 1.3, 1); balls += b; curls += c
    b, c = mini_cloud((.34, L - .18), 1.3, -1); balls += b; curls += c
    for o in cloud_relief('Yulu_Clouds', balls, curls, M, P['carve'], ht=.014, curl_w=.015, curl_h=.009, grain='y'):
        SG.set_wear(o, lambda p: .45 * math.exp(-(p.x / .4) ** 2))
    S['prop_panel'] = dict(hw=hw, L=L, cells=[nu, nv])
    return o


# ------------------------------------------------------------------ SG05
def sg05_wide_run(P):
    R = random.Random('SG05_WideRun')
    for k in range(1, N + 1):
        yf = Y0 + (k - 1) * TREAD
        back = .05 if k < N else 0.
        lo_z = max(0., (k - 1) * RISE - .03)
        ya, yb = yf - .015, (yf + TREAD + back if k < N else Y1)
        for side in (-1, 1):                    # three blocks per flight, joints kept off the walking lines (0.87, 1.66, 2.45 m)
            if (k + (side > 0)) % 2: j1, j2 = R.uniform(1.06, 1.34), R.uniform(1.9, 2.18)
            else: j1, j2 = R.uniform(1.28, 1.52), R.uniform(2.06, 2.3)
            xs = [PW + .003, j1, j2, KX0 + .01]
            for i in range(3):
                xa, xb = xs[i] + (.003 if i else 0), xs[i + 1] - (.003 if i < 2 else 0)
                repair = (k, side, i) in ((6, 1, 2), (3, -1, 0))
                o = rbox(f'Step_{k:02d}_{"LR"[side > 0]}{i}', (side * (xa + xb) / 2, (ya + yb) / 2, (lo_z + k * RISE) / 2), (xb - xa, yb - ya, k * RISE - lo_z),
                         P['repair'] if repair else R.choice(P['tread']), r=.014 if not repair else .008, amp=.0025, freq=4.5, chips=1 if R.random() < .3 else 0,
                         hew=4, seed=k * 10 + i + (side > 0) * 5, div=.08, flat='zZyY' if k == N else 'zZy')
                SG.set_wear(o, lambda p, yf=yf: math.exp(-((abs(p.x) - 1.66) / .7) ** 2) * (.55 + .45 * max(0., 1 - (p.y - yf) / TREAD)))
                o['tread'] = True
        if k == N:                              # the top tread runs across the head of the carved slab
            o = rbox('Step_10_Head', (0, (PANEL_Y1 + .003 + Y1) / 2, (lo_z + N * RISE) / 2), (2 * PW - .006, Y1 - PANEL_Y1 - .003, N * RISE - lo_z), R.choice(P['tread']),
                     r=.014, amp=.0025, freq=4.5, hew=4, seed=401, div=.08, flat='zZyY')
            SG.set_wear(o, lambda p: .5 * math.exp(-(p.x / .8) ** 2)); o['tread'] = True
    yulu_panel(P)
    Rb = random.Random('SG05_back')               # back wall under the top tread
    z = 0.; c = 0
    while z < (N - 1) * RISE - .03 - .01:
        h = min(Rb.uniform(.28, .36), (N - 1) * RISE - .03 - z)
        x = -KX0 - .005; first = True
        while x < KX0 - .02:
            L = Rb.uniform(.6, 1.2) if not (first and c % 2) else Rb.uniform(.3, .5)
            first = False
            if KX0 - (x + L) < .3: L = KX0 + .005 - x
            rbox(f'Back_Wall_{c}', (x + L / 2, Y1 - .15, z + h / 2), (L - .002, .3, h - .002), Rb.choice(P['wall']), r=.012, amp=.002, freq=5., hew=3,
                 chips=Rb.choice((0, 1)), seed=Rb.randrange(9999), div=.09, flat='Y')
            x += L
        z += h; c += 1
    # kerbs: SG01's, moved out to +-2.84 m
    nrm = Vector((0, -math.sin(SLOPE), math.cos(SLOPE)))
    yb0, yb1 = POST_Y[0] + .2, POST_Y[2] - .2
    cap_bot = [SG.seat_top(POST_Y[0]) - .3, SG.seat_top(POST_Y[2]) - .3]
    for side in (-1, 1):
        sd = 'L' if side < 0 else 'R'
        Rs = random.Random(f'SG05_kerb{side}')
        bed_c = lambda y: SG.cope_top(y) - SG.COPE_T + .02
        zones = [(Y0, yb0, lambda y: cap_bot[0] + .01, None), (yb0, yb1, bed_c, ((0., 0., bed_c(0.)), tuple(nrm))), (yb1, Y1, lambda y: cap_bot[1] + .01, None)]
        SG.wall_courses(P, Rs, side, zones, name=f'Kerb_{sd}', x0=KX0, x1=KX1, px=PX)
        for i, py in ((0, POST_Y[0]), (2, POST_Y[2])):
            top = SG.seat_top(py); zb = top - .3
            cap = rbox(f'Newel_Cap_{sd}{i}', (side * KXC, py, (zb + top) / 2), (KX1 - KX0 + .03, .4, .3), Rs.choice(P['cope']),
                       r=.016, amp=.002, freq=4., hew=3, chips=0, seed=40 + i + side, div=.07, flat='Z')
            SG.cut_socket(cap, (side * KXC, py, top), f'Socket_Hole_{sd}{i}')
            socket(f'Socket_Post_{sd}{i}', (side * KXC, py, top))
        joint = .42 if side > 0 else .36
        for ya, yb in ((yb0 - .05, joint - .001), (joint + .001, yb1 + .05)):
            ym = (ya + yb) / 2; Ls = (yb - ya) / math.cos(SLOPE)
            c = Vector((side * KXC, ym, SG.cope_top(ym))) - nrm * (SG.COPE_T * math.cos(SLOPE) / 2)
            cs = rbox(f'Coping_{sd}', tuple(c), (KX1 - KX0 + .02, Ls, SG.COPE_T * math.cos(SLOPE)), Rs.choice(P['cope']), r=.018, amp=.002, freq=4.,
                      hew=3, chips=1, seed=int(ym * 100) + side, div=.08, rot=(SLOPE, 0, 0), flat='Z')
            if ya < POST_Y[1] < yb:
                SG.cut_socket(cs, (side * KXC, POST_Y[1], SG.cope_top(POST_Y[1])), f'Socket_Hole_{sd}1', sloped=True)
        socket(f'Socket_Post_{sd}1', (side * KXC, POST_Y[1], SG.cope_top(POST_Y[1])))
    # growth: less than SG01 (a kept main stair): moss in the inner corners of the shaded (+X) flight and by the slab, a few weeds
    Rg = random.Random('SG05_growth')
    for k in range(1, N + 1):
        yf = Y0 + (k - 1) * TREAD
        for x, p in ((KX0 - .02, .6), (-(KX0 - .02), .25), (PW + .03, .3), (-(PW + .03), .15)):
            if Rg.random() < p:
                SG.moss_patch('Corner_Moss', (x, yf + Rg.uniform(.08, .26), k * RISE + .002), (0, 0, 1), Rg.uniform(.035, .055), P['moss'], seed=k * 7 + int(x * 10), flat=.7)
        for x, p in ((KX0 - .025, .3), (-(KX0 - .025), .12)):
            if Rg.random() < p:
                SG.grass_tuft('Crack_Grass', (x, yf + Rg.uniform(.12, .28), k * RISE), Rg.randint(4, 7), Rg.uniform(.07, .12), P['grass'] if Rg.random() < .7 else P['dry'], Rg)
    for i in range(8):
        y = Rg.uniform(Y0 + .2, Y1 - .3); zt = min(Rg.uniform(.24, .7), SG.cope_top(y) - .3)
        if zt < .22: continue                       # above the plinth: a patch on its bevelled top edge tilts out past the 6 m footprint
        hit = SG.snap((PX + .2, y, zt), (-1, 0, 0))
        if hit is None or hit[1].x < .95: continue
        SG.moss_patch('Wall_Moss', tuple(hit[0]), tuple(hit[1]), Rg.uniform(.05, .09), P['moss'], seed=50 + i, snap_each=True)
    for side, y in ((1, .42), (-1, .36)):
        SG.grass_tuft('Coping_Grass', (side * (KX0 + .05), y, SG.cope_top(y) - .005), Rg.randint(4, 6), Rg.uniform(.07, .1), P['grass'], Rg, spread=.03)
    socket('Socket_Bottom', (0, Y0, 0), rot=(0, 0, math.pi))
    socket('Socket_Top', (0, Y1, N * RISE))
    S['prop'] = dict(kind='wide_stair', steps=N, rise=RISE, tread=TREAD, flight_w=FLIGHT, panel_half=PW, y0=Y0, y1=Y1, posts=len(POST_Y))
    V, F = [], []
    for k in range(1, N + 1):
        yf = Y0 + (k - 1) * TREAD
        SG.prism(V, F, [(yf, (k - 1) * RISE), (Y1, (k - 1) * RISE), (Y1, k * RISE), (yf, k * RISE)], -KX0, KX0)
    for side in (-1, 1):
        xa, xb = sorted((side * KX0, side * PX))
        SG.prism(V, F, [(Y0, 0.), (POST_Y[0] + .2, 0.), (POST_Y[0] + .2, SG.seat_top(POST_Y[0])), (Y0, SG.seat_top(POST_Y[0]))], xa, xb)
        SG.prism(V, F, [(POST_Y[0] + .2, 0.), (POST_Y[2] - .2, 0.), (POST_Y[2] - .2, SG.cope_top(POST_Y[2] - .2)), (POST_Y[0] + .2, SG.cope_top(POST_Y[0] + .2))], xa, xb)
        SG.prism(V, F, [(POST_Y[2] - .2, 0.), (Y1, 0.), (Y1, SG.seat_top(POST_Y[2])), (POST_Y[2] - .2, SG.seat_top(POST_Y[2]))], xa, xb)
    S['collision_mesh'] = (V, F)


# ------------------------------------------------------------------ SG06
HALF, TOP, RING = 3.5, .8, .5
FIELD = HALF - RING                            # 3.0: a 6 m slab field
HEART = 1.0                                    # the carved heart stone is 2 x 2 m
DRUM_C = HALF - .47                            # drum seat centres (radius 0.43 m)
WALL_F = HALF - .03                            # wall face under the coping (the coping and plinth stand 3 / 2 cm proud of it)


def medallion_height(u, v):
    """SG06 heart stone, cut below the walking surface: frame 0, field -6 mm, the raised clouds back up to -1 mm."""
    d = HEART - .003 - max(abs(u), abs(v))
    if d < .07: return -.004 * (1 - min(1., d / .01)) ** 2
    if d < .09: return -.022 + .004 * smooth(.078, .09, d)
    return -.018                                # the cut-back field; ring and clouds stand on it as scroll lines


def medallion_heads():
    heads = []
    for k in range(4):                        # four curls round the centre, turning the same way, and a small one in the middle
        a = math.pi / 4 + k * math.pi / 2
        heads.append((.3 * math.cos(a), .3 * math.sin(a), .19, 1))
        heads.append((.47 * math.cos(a + .55), .47 * math.sin(a + .55), .1, -1))
    heads.append((0., 0., .13, -1))
    for cx in (-1, 1):                        # corner spandrels: a curl in each corner outside the ring
        for cy in (-1, 1):
            heads.append((cx * .74, cy * .74, .12, cx * cy))
    return heads


def plaque_height(u, v, hu, hv):
    d = min(hu - abs(u), hv - abs(v))
    if d < .04: return .012 - .006 * (1 - min(1., d / .01)) ** 2
    if d < .055: return -.006
    return -.004                                # the field; the clouds stand on it as scroll lines


PLAQUE_HEADS = [(-.5, .0, .09, 1), (-.25, .02, .065, -1), (.0, -.01, .1, 1), (.25, .02, .065, -1), (.5, 0., .09, -1)]


def heart_stone(P):
    cell = .03; n = int(round(2 * (HEART - .003) / cell)); h = HEART - .003
    def top(i, j):
        u = -h + 2 * h * i / n; v = -h + 2 * h * j / n
        hh = medallion_height(u, v)
        return (u, v, TOP + hh), hh
    o = relief_mesh('Heart_Stone', n, n, top, lambda p: (p.x, p.y, TOP - .15), P['carve'], mat_low=P['carve_low'], low=-.011, grain='x')
    SG.set_wear(o, lambda p: .3 * (math.exp(-(p.x / .7) ** 2) + math.exp(-(p.y / .7) ** 2)))
    o['tread'] = True
    sc = scroll_relief('Heart_Ring', [circle_path(.64), circle_path(.6)], lambda u, v: (u, v, TOP - .018), lambda u, v: (0., 0., 1.), P['carve'],
                       w=.03, h=.013, sink=.003, grain='x')
    SG.set_wear(sc, lambda p: .45 * (math.exp(-(p.x / .7) ** 2) + math.exp(-(p.y / .7) ** 2)))
    sc['tread'] = True
    balls, curls = [], []
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2; c = (.36 * math.cos(a), .36 * math.sin(a)); a2 = a + 1.0
        b, cc = ruyi_cloud(c, .95, 1, a - math.pi / 2, tail_to=(.5 * math.cos(a2), .5 * math.sin(a2))); balls += b; curls += cc
    b, cc = mini_cloud((-.04, 0.), 1.2, 1); balls += b; curls += cc
    for cx in (-1, 1):
        for cy_ in (-1, 1):
            b, cc = mini_cloud((cx * .76, cy_ * .76), 1.25, cx * cy_, math.atan2(cy_, cx) + math.pi / 2); balls += b; curls += cc
    for o in cloud_relief('Heart_Clouds', balls, curls, Matrix.Translation((0, 0, TOP - .018)), P['carve'], ht=.011, curl_w=.013, curl_h=.0065, res=.009, grain='x'):
        SG.set_wear(o, lambda p: .45 * (math.exp(-(p.x / .7) ** 2) + math.exp(-(p.y / .7) ** 2))); o['tread'] = True
    return o


def cloud_plaques(P):
    hu, hv = .8, .17; cell = .022; nu = int(round(2 * hu / cell)); nv = int(round(2 * hv / cell)); zc = .37
    for side in range(4):
        a = side * math.pi / 2
        out = Vector((math.sin(a), -math.cos(a), 0)); along = Vector((math.cos(a), math.sin(a), 0))
        face = WALL_F + .022
        def top(i, j, out=out, along=along, face=face):
            u = -hu + 2 * hu * i / nu; v = -hv + 2 * hv * j / nv
            hh = plaque_height(u, v, hu, hv)
            p = out * (face + hh - .012) + along * u + Vector((0, 0, zc + v))
            return tuple(p), hh
        relief_mesh(f'Cloud_Plaque_{side}', nu, nv, top, lambda p, out=out: tuple(p - out * .07), P['carve'], mat_low=P['carve_low'], low=.0, grain='x')
        balls, curls = [], []
        for sg in (-1, 1):
            b, c = ruyi_cloud((.3 * sg, .02), .56, -sg, 0., tail_to=(.66 * sg, -.035)); balls += b; curls += c
        b, c = mini_cloud((-.03, -.005), .8, 1); balls += b; curls += c
        o0 = out * (face - .016) + Vector((0, 0, zc))
        M = Matrix(((along.x, 0, out.x, o0.x), (along.y, 0, out.y, o0.y), (0, 1, 0, o0.z), (0, 0, 0, 1)))
        cloud_relief(f'Plaque_Clouds_{side}', balls, curls, M, P['carve'], ht=.012, curl_w=.01, curl_h=.006, res=.007, grain='x')


def walls(P, R):
    """Plinth (z 0-0.14, face 1 cm in), two wall courses (0.14-0.6, face 3 cm in), 0.4 m thick; the +-Y sides run the full length."""
    def side_boxes(name, z0, h, face, depth, lmin, lmax, seed, chips):
        Rk = random.Random(seed)
        for s in range(4):
            full = s % 2 == 0
            ext = face if full else face - depth
            sign = -1 if s in (0, 3) else 1
            u = -ext; first = True
            while u < ext - .02:
                L = Rk.uniform(lmin, lmax) if not (first and seed % 2) else Rk.uniform(lmin * .5, lmin)
                first = False
                if ext - (u + L) < lmin * .5: L = ext - u
                zc = z0 + h / 2 if z0 > 0 else (h - .003) / 2          # the plinth stands on z = 0
                if s % 2 == 0: c, sz = (u + L / 2, sign * (face - depth / 2), zc), (L - .003, depth - .003, h - .003)
                else: c, sz = (sign * (face - depth / 2), u + L / 2, zc), (depth - .003, L - .003, h - .003)
                rbox(name, c, sz, Rk.choice(P['wall']), r=.012, amp=.002, freq=5., hew=3, chips=Rk.choice(chips), seed=Rk.randrange(9999), div=.15, flat='zZ')
                u += L
    side_boxes('Plinth', 0., .14, HALF - .01, .42, .9, 1.5, 11, (0,))
    side_boxes('Wall_Course_0', .14, .23, WALL_F, .4, .7, 1.3, 12, (0, 1))
    side_boxes('Wall_Course_1', .37, .23, WALL_F, .4, .7, 1.3, 13, (0, 0, 1))


def coping_ring(P, R):
    for cx in (-1, 1):
        for cy in (-1, 1):
            rbox('Ring_Corner', (cx * (HALF - RING / 2), cy * (HALF - RING / 2), .7), (RING - .003, RING - .003, .2), R.choice(P['cope']), r=.016, amp=.002,
                 freq=4., hew=3, chips=0, seed=R.randrange(999), div=.08, flat='zZ' + ('X' if cx < 0 else 'x') + ('Y' if cy < 0 else 'y'))
    from mathutils import Matrix
    for side in range(4):
        ang = side * math.pi / 2
        y = -FIELD; first = True
        while y < FIELD - .02:
            L = R.uniform(.9, 1.4) if not first else R.uniform(.6, 1.)
            first = False
            if FIELD - (y + L) < .5: L = FIELD - y
            pos = Matrix.Rotation(ang, 3, 'Z') @ Vector((y + L / 2, -(HALF - RING / 2), .7))
            rbox(f'Ring_{side}', tuple(pos), (L - .003, RING - .003, .2), R.choice(P['cope']), r=.016, amp=.002, freq=4., hew=4, chips=0,
                 seed=R.randrange(999), div=.08, flat='zZY', rot=(0, 0, ang))
            y += L


def field(P, R):
    """6 x 6 slabs of 1 m (the middle 2 x 2 is the heart stone), 0.15 m thick, 8 mm soil joints; a worn cross through the middle."""
    n = 6; step = 2 * FIELD / n; gap = .008
    for i in range(n):
        for j in range(n):
            if i in (2, 3) and j in (2, 3): continue
            x0, y0 = -FIELD + i * step, -FIELD + j * step
            xa, xb = x0 + (gap / 2 if i else .0015), x0 + step - (gap / 2 if i < n - 1 else .0015)
            ya, yb = y0 + (gap / 2 if j else .0015), y0 + step - (gap / 2 if j < n - 1 else .0015)
            repair = (i, j) in ((4, 1),)
            o = rbox(f'Slab_{i}{j}', ((xa + xb) / 2, (ya + yb) / 2, TOP - .075), (xb - xa, yb - ya, .15), P['repair'] if repair else R.choice(P['tread']),
                     r=.012, amp=.002, freq=3.5, hew=2, chips=0, seed=i * 7 + j, div=.13, flat='zZ')
            SG.set_wear(o, lambda p: .45 * (math.exp(-(p.x / 1.1) ** 2) + math.exp(-(p.y / 1.1) ** 2) - .5 * math.exp(-((p.x ** 2 + p.y ** 2) / 2.))))
            o['tread'] = True
    for k in range(1, n):
        c = -FIELD + k * step
        segs = [(-FIELD, -HEART), (HEART, FIELD)] if abs(c) < .01 else [(-FIELD, FIELD)]
        for a, b in segs:
            m = (a + b) / 2; L = b - a - .01
            rbox('Joint_Soil', (c, m, TOP - .03), (gap + .004, L, .05), P['soil'], r=.002, div=.2, seed=k)
            rbox('Joint_Soil', (m, c, TOP - .032), (L, gap + .004, .05), P['soil'], r=.002, div=.2, seed=k + 9)


def drum_seats(P):
    """Round drum seats (cand-3) on the four corners: a drum with two rows of studs and rolled lips; Socket_Lantern_* on the top centre."""
    prof = [(0., 0.), (.43, 0.), (.43, .03), (.415, .045), (.395, .05), (.39, .07), (.405, .09), (.412, .15), (.405, .21), (.39, .23), (.395, .25),
            (.415, .255), (.43, .27), (.43, .3), (0., .3)]
    for cx, cy, nm in ((1, 1, 'NE'), (-1, 1, 'NW'), (-1, -1, 'SW'), (1, -1, 'SE')):
        x, y = cx * DRUM_C, cy * DRUM_C; z0 = TOP - .01
        lathe(f'Drum_Seat_{nm}', prof, (x, y, z0), P['cope'][0 if cx > 0 else 1], seg=56)
        for row, zz in enumerate((.085, .235)):
            for k in range(18):
                a = math.tau * (k + .5 * row) / 18
                sphere('Drum_Stud', (x + math.cos(a) * .392, y + math.sin(a) * .392, z0 + zz), .014, P['cope'][0], scale=(1, 1, .8), seg=8, ring=5, detail=1)
        socket(f'Socket_Lantern_{nm}', (x, y, z0 + .3))


def growth(P):
    Rg = random.Random('SG06_growth')
    step = 1.
    for k in range(1, 6):
        c = -FIELD + k * step
        for i in range(5):
            t = Rg.uniform(-FIELD + .2, FIELD - .2)
            for x, y in ((c, t), (t, c)):
                if abs(x) < HEART + .05 and abs(y) < HEART + .05: continue
                if abs(x) < .6 or abs(y) < .6: continue          # the worn cross stays clean
                if x < .3 or Rg.random() < .3:
                    SG.moss_patch('Joint_Moss', (x, y, TOP + .001), (0, 0, 1), Rg.uniform(.04, .065), P['moss'], seed=int(t * 100) + k, flat=.6)
    for i in range(16):
        a = Rg.uniform(-FIELD + .2, FIELD - .2); s = Rg.choice((-1, 1))
        if abs(a) > FIELD - .7: continue                      # not under the drum seats
        x, y = (a, s * (FIELD + .002)) if Rg.random() < .5 else (s * (FIELD + .002), a)
        SG.grass_tuft('Edge_Grass', (x, y, TOP), Rg.randint(3, 6), Rg.uniform(.06, .11), P['grass'] if Rg.random() < .7 else P['dry'], Rg, spread=.02)
    for cx, cy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
        for a in (Rg.uniform(0, 6.3), Rg.uniform(0, 6.3)):
            x, y = cx * DRUM_C + math.cos(a) * .45, cy * DRUM_C + math.sin(a) * .45
            if max(abs(x), abs(y)) > HALF - .1: continue
            SG.grass_tuft('Base_Grass', (x, y, TOP), Rg.randint(4, 6), Rg.uniform(.07, .11), P['grass'], Rg, spread=.03)
    for i in range(14):                                       # moss low on the wall faces, more on the shaded -X / +Y sides
        s = Rg.choice((0, 1, 2, 3, 3, 2)); u = Rg.uniform(-HALF + .3, HALF - .3); zt = Rg.uniform(.05, .5)
        a = s * math.pi / 2; out = Vector((math.sin(a), -math.cos(a), 0)); along = Vector((math.cos(a), math.sin(a), 0))
        if abs(u) < .9 and .18 < zt < .56: continue           # not over the carved plaque
        o = out * (HALF + .3) + along * u + Vector((0, 0, zt))
        hit = SG.snap(tuple(o), tuple(-out))
        if hit is None or hit[1].dot(out) < .95: continue      # only on a flat wall face, not a bevel that tilts the patch outward
        SG.moss_patch('Wall_Moss', tuple(hit[0]), tuple(hit[1]), Rg.uniform(.05, .1), P['moss'], seed=80 + i, snap_each=True)


def sg06_wide_landing(P):
    R = random.Random('SG06_WideLanding')
    walls(P, R); coping_ring(P, R); field(P, R); heart_stone(P); cloud_plaques(P); drum_seats(P); growth(P)
    for nm, (x, y, a) in {'S': (0, -HALF, math.pi), 'N': (0, HALF, 0.), 'E': (HALF, 0, -math.pi / 2), 'W': (-HALF, 0, math.pi / 2)}.items():
        socket(f'Socket_Edge_{nm}', (x, y, TOP), rot=(0, 0, a))
    S['prop'] = dict(kind='wide_landing', top=TOP, half=HALF)
    V, F = [], []
    SG.prism(V, F, [(-HALF, 0.), (HALF, 0.), (HALF, TOP), (-HALF, TOP)], -HALF, HALF)
    for cx in (-1, 1):
        for cy in (-1, 1):
            x, y, r = cx * DRUM_C, cy * DRUM_C, .43
            SG.prism(V, F, [(y - r, TOP - .01), (y + r, TOP - .01), (y + r, TOP + .29), (y - r, TOP + .29)], x - r, x + r)
    S['collision_mesh'] = (V, F)


# ------------------------------------------------------------------ checks (called from build_mountain_stairs_b.py)
def wide_stair_checks(aid, check, bvh, main):
    p = S['prop']; down, up, along = bvh([main])
    n, Rr, Tr = p['steps'], p['rise'], p['tread']
    lines = [-(KX0 - .25), -(PW + FLIGHT / 2), -(PW + .25), PW + .25, PW + FLIGHT / 2, KX0 - .25]
    rows = {round(x, 3): [down(x, Y0 + (k + .5) * Tr) for k in range(n)] for x in lines}
    ok_rows = all(z is not None for zs in rows.values() for z in zs)
    rises = []
    if ok_rows:
        for zs in rows.values():
            prev = 0.
            for z in zs: rises.append(z - prev); prev = z
    check('ten_equal_risers_both_flights', ok_rows and max(rises) - min(rises) <= .008 and .15 <= min(rises) and max(rises) <= .18,
          {'tread_z_m_by_line': {k: [round(z, 4) if z else None for z in v] for k, v in rows.items()},
           'rise_min_max_m': [round(min(rises), 4), round(max(rises), 4)] if rises else None, 'design_rise_m': Rr, 'same_as': 'SG01'})
    deps = {}
    for x in (-(PW + FLIGHT / 2), PW + FLIGHT / 2):
        noses = []
        for k in range(1, n):
            hit = along((x, Y0 - .5, k * Rr - .07), (0, 1, 0)); noses.append(hit[0].y if hit else None)
        deps[round(x, 3)] = [round(b - a, 4) for a, b in zip(noses, noses[1:])] if all(v is not None for v in noses) else None
    check('equal_treads_both_flights', all(d is not None and max(d) - min(d) <= .01 and .28 <= min(d) and max(d) <= .325 for d in deps.values()),
          {'tread_depths_m': deps, 'design_tread_m': Tr})
    clear = []
    for side in (-1, 1):
        for k in (1, 4, 8):
            z = k * Rr + .05; y = Y0 + (k - .5) * Tr; xc = side * (PW + FLIGHT / 2)
            a = along((xc, y, z), (side, 0, 0)); b = along((xc, y, z), (-side, 0, 0))
            clear.append(round(abs((a[0].x if a else 9) - (b[0].x if b else -9)), 4))
    check('clear_flight_width', min(clear) >= FLIGHT - .02, {'kerb_to_carved_slab_m': clear, 'design_m': FLIGHT, 'note': 'each flight, 5 cm above the tread'})
    hw, L = S['prop_panel']['hw'], S['prop_panel']['L']
    rel = []
    for s in (-.45, -.25, 0., .25, .45):
        for i in range(40):
            y = PANEL_Y0 + (.1 + (L - .2) * i / 39) * math.cos(SLOPE)
            z = down(s, y)
            rel.append(None if z is None else z - SG.nose_z(y))
    okr = all(r is not None for r in rel)
    check('carved_slab_follows_nosing_line', okr and min(rel) >= -.012 and max(rel) <= .016 and max(rel) - min(rel) >= .008,
          {'relief_vs_nosing_line_m': [round(min(rel), 4), round(max(rel), 4)] if okr else None, 'samples': len(rel),
           'note': 'the slab top stays within -12 / +16 mm of the line through the step nosings: carved, and no lip to catch a foot'})
    top = [down(x, Y1 - .1) for x in (-(KX0 - .2), -1.66, 0., 1.66, KX0 - .2)]
    check('top_flush_with_landing', all(t is not None and abs(t - n * Rr) <= .006 for t in top), {'top_tread_z_m': [round(t, 4) if t else None for t in top], 'design_m': round(n * Rr, 4)})
    over = []
    for side in (-1, 1):
        for x in (KX0 + .03, KXC, KX1 - .03):
            y = POST_Y[0] + .25
            while y < POST_Y[2] - .25:
                z = down(side * x, y)
                if z is not None and z > SG.cope_top(y) + .012: over.append([round(side * x, 3), round(y, 3), round(z - SG.cope_top(y), 4)])
                y += .02
    check('nothing_above_sloped_coping', not over, {'points_above_m': over[:12], 'count': len(over)})
    need = {'Socket_Bottom', 'Socket_Top'} | {f'Socket_Post_{s}{i}' for s in 'LR' for i in range(3)}
    check('sockets_present', need <= set(S['sockets']), {'missing': sorted(need - set(S['sockets']))})
    dev = []
    for s in 'LR':
        for i in range(3):
            o = S['sockets'].get(f'Socket_Post_{s}{i}')
            if o is None: continue
            q = o.matrix_world.translation; want_z = SG.cope_top(POST_Y[1]) if i == 1 else SG.seat_top(POST_Y[i])
            dev.append(max(abs(abs(q.x) - KXC), abs(q.y - POST_Y[i]), abs(q.z - want_z)))
    check('post_sockets_as_sg01', len(dev) == 6 and max(dev) < .001,
          {'max_deviation_m': round(max(dev), 5) if dev else None, 'post_y_m': list(POST_Y), 'post_x_m': KXC,
           'note': 'same y and z as SG01 Socket_Post_*: SG03 rails fit without change'})
    return {'steps': n, 'rise_m': Rr, 'tread_m': Tr, 'flight_width_m': FLIGHT, 'carved_slab_width_m': round(2 * PW, 3), 'top_z_m': round(n * Rr, 4),
            'newel_top_m': round(SG.seat_top(POST_Y[2]), 4), 'sockets': sorted(S['sockets'])}


def wide_landing_checks(aid, check, bvh, main):
    down, up, along = bvh([main])
    pts = []
    for i in range(21):
        for j in range(21):
            x, y = -HALF + .25 + 6.5 * i / 20, -HALF + .25 + 6.5 * j / 20
            if min(math.hypot(x - cx * DRUM_C, y - cy * DRUM_C) for cx in (-1, 1) for cy in (-1, 1)) < .5: continue
            if abs(x) < HEART and abs(y) < HEART: continue          # the carved heart stone is checked on its own below
            zz = [down(x + dx, y + dy) for dx, dy in ((0, 0), (.03, 0), (-.03, 0), (0, .03), (0, -.03))]
            pts.append(max((v for v in zz if v is not None), default=None))
    ok = all(z is not None for z in pts); zs = [z for z in pts if z is not None]
    check('walking_surface_level', ok and max(zs) - min(zs) <= .008 and abs(sum(zs) / len(zs) - TOP) <= .004,
          {'samples': len(pts), 'z_min_max_m': [round(min(zs), 4), round(max(zs), 4)], 'design_m': TOP})
    hz = [down(x, y) for x in (-.8, -.4, 0., .4, .8) for y in (-.8, -.4, 0., .4, .8)]
    check('heart_stone_cut_below_surface', all(z is not None and TOP - .025 <= z <= TOP + .001 for z in hz) and max(hz) - min(hz) >= .008,
          {'z_min_max_m': [round(min(hz), 4), round(max(hz), 4)], 'note': 'the medallion is cut up to 2.2 cm into the stone, nothing above z 0.8'})
    edge = {nm: down(x, y) for nm, (x, y) in {'S': (0, -HALF + .05), 'N': (0, HALF - .05), 'E': (HALF - .05, 0), 'W': (-HALF + .05, 0)}.items()}
    check('edges_flush_with_sg05_top', all(v is not None and abs(v - TOP) <= .006 for v in edge.values()), {k: round(v, 4) if v else None for k, v in edge.items()})
    drums = {}
    for nm in ('NE', 'NW', 'SW', 'SE'):
        o = S['sockets'].get(f'Socket_Lantern_{nm}')
        if o is None: continue
        q = o.matrix_world.translation; drums[nm] = [round(q.x, 3), round(q.y, 3), round(q.z, 4), down(q.x, q.y)]
    check('four_lantern_seats', len(drums) == 4 and all(abs(d[3] - d[2]) <= .004 and max(abs(d[0]), abs(d[1])) + .43 <= HALF for d in drums.values()),
          {'socket_xyz_and_seat_top_m': {k: v[:3] + [round(v[3], 4) if v[3] else None] for k, v in drums.items()}, 'seat_diameter_m': .86})
    need = {f'Socket_Edge_{k}' for k in 'SNEW'} | {f'Socket_Lantern_{k}' for k in ('NE', 'NW', 'SW', 'SE')}
    check('sockets_present', need <= set(S['sockets']), {'missing': sorted(need - set(S['sockets']))})
    return {'top_z_m': TOP, 'size_m': [7, 7], 'heart_stone_m': 2 * HEART, 'lantern_seats': 4, 'sockets': sorted(S['sockets'])}


SG05_NOTE = ('寬版大石階直段（三視圖 SG05-cand-1）：寬 6 m、深 3.2 m，10 階，每階高 0.16 m、深 0.32 m（和 SG01 相同），一段升 1.6 m；兩端柱座石頂 2.06 m。'
             '正中一條 1.24 m 寬的雕花御路石，石面順著踏步前緣線（高低在 −12～+16 mm 之內，不絆腳），外圈一道凸框，框內淺浮雕雲紋：五組雲頭左右擺、'
             '雲頭上刻陰線渦卷，中間一條雲尾連起來，底端和頂端各兩個小卷雲收頭；兩側各一段 2.08 m 寬的踏步。'
             '側欄、壓頂石、端柱座石、三個 0.15 m 方形柱孔和 SG01 相同（柱孔的 y、z 一樣，x 在 ±2.84 m），可直接接 SG03 欄杆。'
             '灰白花崗石（花崗白 #C9C6BD，和 RS03 山門台基同一組數值）；第 3 階左、第 6 階右各一塊較新的補石；苔只長在右側內角和御路石邊，少量雜草。'
             '接口：Socket_Bottom 在第一階前緣地面、Socket_Top 在頂端（y +1.6、z 1.6），接 SG06 的 Socket_Edge_*。工作包的物件句寫 13 階，照「階高、踏面和 SG01 相同」做 10 階。')
SG06_NOTE = ('寬版轉折平台（三視圖 SG06-cand-3）：7 × 7 m、高 0.8 m，走面水平在 z 0.8。鋪法照 SG02：外圍一圈 0.5 m 寬的收邊壓頂石，中間 6 × 6 m 的 1 m 大石板，'
             '接縫填土、長苔，中間十字被腳磨亮；正中一塊 2 × 2 m 的方心石，雲紋團花（四個雲頭繞中心、外一圈圓環、四角岔角卷雲）刻在石面以下，沒有東西高過走面。'
             '壓頂石下面一道勒腳、兩層牆石，四面正中各一塊雲紋浮雕石板。四角各一座圓鼓形燈座（直徑 0.86 m、高 0.3 m，兩圈鼓釘，和 SG02 蓮瓣燈座同大），'
             '頂面中心 Socket_Lantern_NE／NW／SW／SE 放現成石燈（G01 或 LT01）。四邊中點 Socket_Edge_S／N／E／W（z 0.8、朝外）：SG05 的 Socket_Top 對上就是上來的段；'
             '往上走的段立在與平台頂同高的地面上，Socket_Bottom 對上 Socket_Edge_*。')


def register(ASSETS):
    ASSETS['SG05_WideStairRun'] = dict(zh='寬版大石階直段', kind='wide_stair', palette=palette, build=sg05_wide_run, limit=(6., 3.2, 2.1), tex=2048, ver='v001',
        box=((-3., Y0 - .02, 0.), (3., Y1 + .001, 2.1)), ref='SG05/SG05-cand-1', slot='B1_SectGateStairs', minTier='standard', clamp_max=.03,
        origin='centre of the footprint at ground level; the flight climbs towards +Y, its foot (first riser) faces -Y', note=SG05_NOTE)
    ASSETS['SG06_WideLanding'] = dict(zh='寬版轉折平台', kind='wide_landing', palette=palette, build=sg06_wide_landing, limit=(7., 7., .8), tex=2048, ver='v001',
        box=((-3.5, -3.5, 0.), (3.5, 3.5, 1.11)), ref='SG06/SG06-cand-3', slot='B1_SectGateStairs', minTier='standard', clamp_max=.03,
        origin='centre of the footprint at the bottom; the walking surface is level at z 0.8', note=SG06_NOTE)
