"""RS02 review fixes (2026-11-10): parts circled on the Unity shots as crude are rebuilt in place, same footprint and height.

Blacksmith: the forge (about 70 firebricks, each 20-80 cm, the hood and back wall one block each, so the brick texture smeared) becomes
real coursed brickwork: ~25 x 7 cm bricks on a mortar core, running bond with alternating corner bond, a radial voussoir arch with a
keystone over the fire mouth, a corbelled brick hood stepping in course by course to the chimney, a brick chimney up to the source cap.
The anvil (body, a 5 cm light steel slab and a heel block stacked) becomes one forged London-pattern shape: four feet, waist, body,
heel, step and horn, with a thin worn steel face set into the top. Its octagonal stump becomes a round log section with two iron hoops.
Materials shop: the 14 glazed jars (one egg shape, glossy) become three thrown shapes with foot ring, neck and lip; some tied with a
cloth cover, some with a wooden lid; semi-matte glazes, unglazed clay foot.
"""
import math, random, bpy, bmesh
import numpy as np
from mathutils import Vector
import ti_core, ti_mats as tm, cr_mats as cm
from ti_core import S

mk = __import__('mk_mats')


def _bounds(o):
    c = np.array([v.co[:] for v in o.data.vertices]); return c.min(0), c.max(0)


def _tris(objs):
    return sum(len(p.vertices) - 2 for o in objs for p in o.data.polygons)


def _take(pred, want, label):
    hit = [q for q in S['parts'] if q.type == 'MESH' and pred(q.name, *_bounds(q))]
    assert len(hit) == want, (label, len(hit), [q.name for q in hit][:12])
    n = _tris(hit)
    for q in hit:
        S['parts'].remove(q); bpy.data.objects.remove(q, do_unlink=True)
    return n, len(hit)


def _obj(name, verts, faces):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    me.uv_layers.new(name='UVMap')
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    return o


def box(name, lo, hi, mat, group, grain='x', detail=0):
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return ti_core.finish(_obj(name, v, f), name, mat, grain=grain, group=group, detail=detail)


def loft(name, rings, mat, group, cap0=True, cap1=True, smooth=True, grain='x', detail=0):
    """rings: list of equal-length point loops; caps are n-gons (triangulated by the pipeline)."""
    k = len(rings[0]); v = [p for r in rings for p in r]; f = []
    for i in range(len(rings) - 1):
        a, b = i * k, (i + 1) * k
        f += [(a + j, a + (j + 1) % k, b + (j + 1) % k, b + j) for j in range(k)]
    if cap0: f.append(tuple(range(k))[::-1])
    if cap1: f.append(tuple(range((len(rings) - 1) * k, len(rings) * k)))
    o = _obj(name, v, f)
    return ti_core.finish(o, name, mat, grain=grain, group=group, smooth=smooth, detail=detail)


def lathe(name, prof, c, mat, group, seg=24, jitter=None, grain='z', detail=0):
    """prof: (r, z) bottom to top, r = 0 at both ends closes with a pole."""
    v, rings = [], []
    for r, z in prof:
        if r < 1e-6: rings.append([len(v)]); v.append((c[0], c[1], z)); continue
        ring = []
        for i in range(seg):
            a = i * math.tau / seg; rr = r * (jitter(a, z) if jitter else 1.)
            ring.append(len(v)); v.append((c[0] + rr * math.cos(a), c[1] + rr * math.sin(a), z))
        rings.append(ring)
    f = []
    for A, B in zip(rings, rings[1:]):
        if len(A) == 1: f += [(A[0], B[(i + 1) % seg], B[i]) for i in range(seg)]
        elif len(B) == 1: f += [(A[i], A[(i + 1) % seg], B[0]) for i in range(seg)]
        else: f += [(A[i], A[(i + 1) % seg], B[(i + 1) % seg], B[i]) for i in range(seg)]
    return ti_core.finish(_obj(name, v, f), name, mat, grain=grain, group=group, smooth=True, detail=detail)


def band(name, c, ri, ro, z0, z1, mat, group, seg=36, detail=0):
    v, f = [], []
    for i in range(seg):
        a = i * math.tau / seg; ca, sa = math.cos(a), math.sin(a)
        v += [(c[0] + r * ca, c[1] + r * sa, z) for r, z in ((ri, z0), (ro, z0), (ro, z1), (ri, z1))]
    for i in range(seg):
        a, b = 4 * i, 4 * ((i + 1) % seg)
        f += [(a + q, b + q, b + (q + 1) % 4, a + (q + 1) % 4) for q in range(4)]
    return ti_core.finish(_obj(name, v, f), name, mat, grain='z', group=group, smooth=False, detail=detail)


def _se(w, h, n, k):
    out = []
    for t in range(k):
        a = math.tau * t / k; c, s = math.cos(a), math.sin(a)
        out.append((w * math.copysign(abs(c) ** (2 / n), c), h * math.copysign(abs(s) ** (2 / n), s), a))
    return out


# ---------------------------------------------------------------- blacksmith

YC = -.75                                         # anvil and stump centre line (source)
BODY = [  # x, half width, bottom z, top z, squareness  (heel -> face -> step -> horn)
    (-.52, .095, 1.065, 1.128, 6), (-.46, .12, 1.05, 1.128, 6), (-.36, .155, 1.03, 1.128, 7), (-.24, .19, 1.0, 1.128, 8),
    (-.14, .205, .975, 1.128, 8), (.05, .21, .965, 1.128, 8), (.30, .21, .965, 1.128, 8), (.46, .205, .975, 1.128, 8),
    (.58, .19, .99, 1.128, 8), (.62, .175, 1.0, 1.128, 7), (.625, .16, 1.0, 1.10, 6), (.70, .15, 1.0, 1.10, 5),
    (.72, .135, .975, 1.095, 3), (.80, .11, .99, 1.085, 2.4), (.88, .08, 1.005, 1.075, 2.2), (.95, .05, 1.02, 1.066, 2.),
    (1.0, .026, 1.032, 1.058, 2.), (1.04, .004, 1.044, 1.05, 2.)]


def _body_w(x):
    xs = [s[0] for s in BODY[:10]]; ws = [s[1] for s in BODY[:10]]
    return float(np.interp(x, xs, ws))


def anvil(P, xc=.15):
    k = 32
    rings = [[(x, YC + y, (zb + zt) / 2 + z) for y, z, _ in _se(w, (zt - zb) / 2, n, k)] for x, w, zb, zt, n in BODY]
    loft('Anvil_Body', rings, P['anvil_iron'], 'Main')
    W = [(.681, .32, .185, .34), (.70, .32, .185, .34), (.72, .30, .175, .30), (.75, .26, .155, .22), (.79, .215, .135, .12),
         (.83, .19, .12, .04), (.87, .18, .115, 0.), (.91, .195, .125, 0.), (.94, .23, .15, 0.), (.97, .28, .185, 0.), (.995, .31, .20, 0.)]
    rings = []
    for z, L, Wd, dent in W:
        n = 4 if z < .93 else 6
        rings.append([(xc + x * (1 - dent * (1 - abs(math.sin(2 * a))) ** 2), YC + y * (1 - dent * (1 - abs(math.sin(2 * a))) ** 2), z)
                      for x, y, a in _se(L, Wd, n, k)])
    loft('Anvil_Waist_Feet', rings, P['anvil_iron'], 'Main', grain='z')
    xs = [-.50, -.46, -.36, -.24, -.14, .05, .30, .46, .58, .608]
    rings = [[(x, YC + y, 1.13 + z) for y, z, _ in _se(_body_w(x) - .022, .012, 12, k)] for x in xs]   # inside the body's rounded top edge
    face = loft('Anvil_Steel_Face', rings, P['anvil_face'], 'Main')
    body = [q for q in S['parts'] if q.name == 'Anvil_Body'][-1]
    # hardy hole (2.6 cm square) and pritchel hole (1.8 cm round) through the heel
    for cut in (_box_cutter((-.413, YC - .013, .98), (-.387, YC + .013, 1.2)), _cyl_cutter((-.305, YC), .009, .98, 1.2)):
        for t in (body, face): _apply_cut(t, cut)
        bpy.data.objects.remove(cut, do_unlink=True)
    hammer(P)


def _box_cutter(lo, hi):
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    return _obj('cut', v, [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])


def _cyl_cutter(c, r, z0, z1, k=16):
    v = [(c[0] + r * math.cos(math.tau * i / k), c[1] + r * math.sin(math.tau * i / k), z) for z in (z0, z1) for i in range(k)]
    f = [tuple(range(k))[::-1], tuple(range(k, 2 * k))] + [(i, (i + 1) % k, k + (i + 1) % k, k + i) for i in range(k)]
    return _obj('cut', v, f)


def _apply_cut(target, cutter):
    m = target.modifiers.new('Hole', 'BOOLEAN'); m.object = cutter; m.operation = 'DIFFERENCE'; m.solver = 'EXACT'
    m.material_mode = 'INDEX'          # 'TRANSFER' would add the material-less cutter as an empty slot (uv_atlas reads every slot's name)
    with bpy.context.temp_override(object=target, active_object=target):
        bpy.ops.object.modifier_apply(modifier=m.name)
    me = target.data
    for i in reversed(range(len(me.materials))):     # belt and braces: no empty slot may reach the bake
        if me.materials[i] is None:
            assert not any(p.material_index == i for p in me.polygons), (target.name, 'faces on an empty slot')
            me.materials.pop(index=i)
    # the cut leaves slivers where the hole meets the face edges; orient_faces would drop them later, after the shape-edit count
    # and fans of needle triangles round the holes: some flip in UV and fold the anvil-face piece over itself (UV check: 214 texels).
    # Triangulate, then re-pick the diagonals inside each flat face (beautify) so no needle is left
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges[:])
    dead = [f for f in bm.faces if f.calc_area() < 1e-10]
    if dead: bmesh.ops.delete(bm, geom=dead, context='FACES_ONLY')
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    flat = [e for e in bm.edges if len(e.link_faces) == 2 and e.link_faces[0].normal.dot(e.link_faces[1].normal) > .99999]
    bmesh.ops.beautify_fill(bm, faces=bm.faces[:], edges=flat)
    dead = [f for f in bm.faces if f.calc_area() < 1e-10]
    if dead: bmesh.ops.delete(bm, geom=dead, context='FACES_ONLY')
    bm.normal_update(); bm.to_mesh(me); bm.free(); me.update()


def hammer(P):
    """A cross-peen hammer left on the face, handle over the front edge."""
    k = 16; y = YC + .06; zc = 1.142 + .002 + .019
    st = [(.17, .012, .013, 3), (.178, .017, .017, 5), (.26, .019, .019, 6), (.285, .017, .017, 5), (.305, .007, .016, 3), (.308, .002, .013, 3)]
    loft('Hammer_Head', [[(x, y + a, zc + b) for a, b, _ in _se(w, h, n, k)] for x, w, h, n in st], P['forged_iron'], 'Main')
    xh = .222; zh = 1.142 + .002 + .0135
    hs = [(y + .012, .0105, .0135), (y - .08, .011, .0145), (y - .25, .012, .016), (y - .40, .0125, .017), (y - .405, .009, .013)]
    loft('Hammer_Handle', [[(xh + a, yy, zh + b) for a, b, _ in _se(w, h, 2.2, k)] for yy, w, h in hs], P['timber'], 'Main', grain=(0., 1., 0.))


def stump(P, c=(.15, YC)):
    j = lambda a, z: 1 + .014 * math.sin(3 * a + .7) + .009 * math.sin(7 * a + 2.1) + .004 * math.sin(13 * a + z * 9)
    prof = [(0, .18), (.43, .18), (.436, .2), (.418, .26), (.407, .4), (.401, .55), (.398, .655), (.39, .672), (.376, .68), (0, .68)]
    # a solid hardwood log section, end grain up (how anvils are set), bark on: no hoops, so it does not read as a hollow barrel.
    # The VH firewood material reads per-corner 'bark' and per-point 'lc' (along, u/R, v/R) the way vh_wood.split_log writes them.
    o = lathe('Anvil_Stump_Log', prof, c, P['firewood'], 'Wood', seg=36, jitter=j, grain=(0., 0., 1.))
    me = o.data; R0 = .40
    bark = [abs(p.normal.z) < .7 for p in me.polygons]
    for p, b in zip(me.polygons, bark): p.use_smooth = b
    at = me.attributes.new('bark', 'FLOAT', 'CORNER')
    at.data.foreach_set('value', [1. if bark[p.index] else 0. for p in me.polygons for _ in p.loop_indices])
    lc = me.attributes.new('lc', 'FLOAT_VECTOR', 'POINT')
    lc.data.foreach_set('vector', [x for v in me.vertices for x in (v.co.z - .18, (v.co.x - c[0]) / R0, (v.co.y - c[1]) / R0)])


# forge envelope (source): body x -2.70..-0.90, y 0.28..1.84 on the bluestone plinth at z 0.63; fire mouth centred x -1.80;
# chimney x -2.23..-1.37, y 0.62..1.48 from 2.78 up to the cap at 5.20
FX0, FX1, FY0, FY1, FZ0, FZ1 = -2.70, -.90, .28, 1.84, .63, 1.97
MX, MR, RING, NC = -1.80, .48, .18, 16
H = (FZ1 - FZ0) / NC                                # 0.08375: course height; springing on course 8 (z 1.30)
ZS = FZ0 + 8 * H
JT, DEP, LNOM = .012, .035, .26                     # joint, brick depth (0.015 into the core), nominal brick length
CX0, CX1, CY0, CY1 = -2.23, -1.37, .62, 1.48
ZH, ZC = 2.78, 5.199


class Bricks:
    def __init__(self, P, rng):
        self.P, self.r, self.n = P, rng, 0

    def mat(self, xm=None, zm=None, front=False):
        # soot: the front over the fire mouth and up the hood is smoke-blackened, densest just above the arch
        if front and zm is not None and ZS - .08 < zm < ZH:
            h = zm - ZS; half = .5 + .35 * max(h, 0.)
            if abs(xm - MX) < half and self.r.random() < .92 - .25 * abs(xm - MX) / half - .12 * max(h, 0.):
                return self.P['forge_soot_brick']
        q = self.r.random()
        return self.P['firebrick_b'] if q < .4 else self.P['firebrick_c'] if q < .52 else self.P['firebrick']

    def run(self, axis, a, b, fixed, out, z0, parity, cut=None):
        """One course of bricks along `axis` ('x' or 'y') from a to b; the face is at `fixed`, outward sign `out`."""
        L = b - a; n = max(1, round(L / LNOM)); l = L / n
        edges = [a] + [a + l / 2 + l * i for i in range(n)] + [b] if parity else [a + l * i for i in range(n + 1)]   # half-brick bond
        for e0, e1 in zip(edges, edges[1:]):
            pieces = [(e0 + JT / 2, e1 - JT / 2)]
            if cut:
                c0, c1 = cut(z0)
                if c1 > c0: pieces = [(max(p0, q0), min(p1, q1)) for p0, p1 in pieces for q0, q1 in ((-9, c0), (c1, 9))]
            for p0, p1 in pieces:
                if p1 - p0 < .05: continue
                self.brick(axis, p0, p1, fixed, out, z0)

    def brick(self, axis, p0, p1, fixed, out, z0):
        r = self.r; pro = r.uniform(-.003, .004); z0b = z0 + JT / 2 + r.uniform(-.002, .002); z1b = z0 + H - JT / 2 + r.uniform(-.002, .002)
        face = fixed + out * pro; back = fixed - out * DEP
        lo_n, hi_n = min(face, back), max(face, back)
        if axis == 'x': lo, hi = (p0, lo_n, z0b), (p1, hi_n, z1b)
        else: lo, hi = (lo_n, p0, z0b), (hi_n, p1, z1b)
        m = self.mat((p0 + p1) / 2, (z0b + z1b) / 2, front=axis == 'x' and out < 0)
        box('Forge_Brick', lo, hi, m, 'Stone', grain='x' if axis == 'x' else 'y'); self.n += 1

    def ring(self, x0, x1, y0, y1, z0, parity, cut_front=None):
        """A course around the rectangle: corners belong to the front/back runs on even courses, to the side runs on odd ones."""
        if parity % 2 == 0:
            self.run('x', x0, x1, y0, -1, z0, 0, cut_front); self.run('x', x0, x1, y1, 1, z0, 0)
            self.run('y', y0 + DEP, y1 - DEP, x0, -1, z0, 1); self.run('y', y0 + DEP, y1 - DEP, x1, 1, z0, 1)
        else:
            self.run('y', y0, y1, x0, -1, z0, 0); self.run('y', y0, y1, x1, 1, z0, 0)
            self.run('x', x0 + DEP, x1 - DEP, y0, -1, z0, 1, cut_front); self.run('x', x0 + DEP, x1 - DEP, y1, 1, z0, 1)


def _mouth_cut(z0):
    """x interval of the front course kept clear: the fire mouth below the springing, the voussoir ring above it."""
    if z0 < FZ0 + H - 1e-6: return (0, 0)                              # first course: the sill runs across
    if z0 < ZS - 1e-6: return (MX - MR, MX + MR)
    dz = z0 - ZS; Ro = MR + RING + JT
    if dz >= Ro: return (0, 0)
    f = math.sqrt(Ro * Ro - dz * dz); return (MX - f, MX + f)


def forge(P):
    global H
    rng = np.random.default_rng(1110)
    class R:  # numpy rng with random.random-style calls
        random = staticmethod(lambda: float(rng.random())); uniform = staticmethod(lambda a, b: float(rng.uniform(a, b)))
    br = Bricks(P, R)
    mort, soot = P['forge_mortar'], P['forge_soot']
    # mortar core (inset 2 cm from the brick face), hollow fire chamber with a barrel vault
    i = .02
    box('Forge_Core', (FX0 + i, FY0 + i, FZ0), (MX - MR, FY1 - i, FZ1), mort, 'Stone')
    box('Forge_Core', (MX + MR, FY0 + i, FZ0), (FX1 - i, FY1 - i, FZ1), mort, 'Stone')
    box('Forge_Core', (MX - MR, 1.56, FZ0), (MX + MR, FY1 - i, FZ1), mort, 'Stone')
    box('Forge_Core', (MX - MR, FY0 + i, FZ0), (MX + MR, 1.56, FZ0 + H), mort, 'Stone')                    # hearth floor under the coal bed
    arc = [(MX + MR * math.cos(math.pi * t / 24), ZS + MR * math.sin(math.pi * t / 24)) for t in range(25)]
    out = [(MX + MR, ZS), (MX + MR, FZ1), (MX - MR, FZ1), (MX - MR, ZS)] + arc[::-1][1:-1]   # rectangle above the springing minus the vault
    out = out[::-1] if sum((b[0] - a[0]) * (b[1] + a[1]) for a, b in zip(out, out[1:] + out[:1])) > 0 else out
    ti_core.extrude_profile('Forge_Core', out, 1.56 - (FY0 + i), mort, plane='xz', p=(0, (1.56 + FY0 + i) / 2, 0), bevel=0, group='Stone')
    # soot lining of the chamber (sunk 5 mm into the core so no face lies on another)
    box('Forge_Soot_Lining', (MX - MR - .005, FY0 + .005, FZ0 + H), (MX - MR + .012, 1.565, ZS), soot, 'Stone')
    box('Forge_Soot_Lining', (MX + MR - .012, FY0 + .005, FZ0 + H), (MX + MR + .005, 1.565, ZS), soot, 'Stone')
    back = [(MX - MR + .012, FZ0 + H), (MX + MR - .012, FZ0 + H), (MX + MR - .012, ZS)] + \
           [(MX + (MR - .012) * math.cos(math.pi * t / 24), ZS + (MR - .012) * math.sin(math.pi * t / 24)) for t in range(1, 24)] + [(MX - MR + .012, ZS)]
    ti_core.extrude_profile('Forge_Soot_Lining', back, .017, soot, plane='xz', p=(0, 1.5515, 0), bevel=0, group='Stone')
    vault = [(MX + (MR + .005) * math.cos(math.pi * t / 24), ZS + (MR + .005) * math.sin(math.pi * t / 24)) for t in range(25)] + \
            [(MX + (MR - .012) * math.cos(math.pi * t / 24), ZS + (MR - .012) * math.sin(math.pi * t / 24)) for t in range(24, -1, -1)]
    ti_core.extrude_profile('Forge_Soot_Lining', vault, 1.543 - FY0 - .005, soot, plane='xz', p=(0, (1.543 + FY0 + .005) / 2, 0), bevel=0, group='Stone')
    box('Forge_Coal_Bed', (MX - MR + .01, FY0 + .03, FZ0 + H - .006), (MX + MR - .01, 1.55, FZ0 + H + .012), P['charcoal'], 'Main')
    # body courses
    for c in range(NC):
        br.ring(FX0, FX1, FY0, FY1, FZ0 + c * H, c, cut_front=_mouth_cut)
    # voussoirs: 17 wedge bricks on edge, the keystone 1.5 cm proud and a little longer
    nv = 17; gap = JT / (MR + RING / 2)
    for q in range(nv):
        a0 = math.pi * q / nv + gap / 2; a1 = math.pi * (q + 1) / nv - gap / 2; key = q == nv // 2
        ro = MR + RING + (.03 if key else 0); y0 = FY0 - (.015 if key else R.uniform(-.003, .003))
        pts = [(MX + r * math.cos(a), ZS + r * math.sin(a)) for r, a in ((MR, a0), (ro, a0), (ro, a1), (MR, a1))]
        v = [(x, y0, z) for x, z in pts] + [(x, FY0 + DEP, z) for x, z in pts]
        f = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
        am = (a0 + a1) / 2
        ti_core.finish(_obj('Forge_Voussoir', v, f), 'Forge_Voussoir', br.mat(MX + .57 * math.cos(am), ZS + .57 * math.sin(am), front=True),
                       grain='x', group='Stone'); br.n += 1
    # corbelled hood: ten courses stepping in to the chimney
    nh = 10; hh = (ZH - FZ1) / nh
    H0 = H; H = hh
    for c in range(nh):
        dx = (CX0 - FX0) * (c + 1) / nh; dy = (CY0 - FY0) * (c + 1) / nh
        x0, x1, y0, y1 = FX0 + dx, FX1 - dx, FY0 + dy, FY1 - dy; z0 = FZ1 + c * hh
        box('Forge_Hood_Core', (x0 + i, y0 + i, z0), (x1 - i, y1 - i, z0 + hh), mort, 'Stone')
        br.ring(x0, x1, y0, y1, z0, c)
    # chimney: hollow brick shaft on a mortar tube, up to the source bluestone cap
    nc = 29; H = (ZC - ZH) / nc
    t = .12
    box('Forge_Chimney_Core', (CX0 + i, CY0 + i, ZH), (CX1 - i, CY0 + i + t, ZC), mort, 'Stone')
    box('Forge_Chimney_Core', (CX0 + i, CY1 - i - t, ZH), (CX1 - i, CY1 - i, ZC), mort, 'Stone')
    box('Forge_Chimney_Core', (CX0 + i, CY0 + i + t, ZH), (CX0 + i + t, CY1 - i - t, ZC), mort, 'Stone')
    box('Forge_Chimney_Core', (CX1 - i - t, CY0 + i + t, ZH), (CX1 - i, CY1 - i - t, ZC), mort, 'Stone')
    for c in range(nc):
        br.ring(CX0, CX1, CY0, CY1, ZH + c * H, c)
    H = H0
    return br.n


def smithy_rework(P):
    S.setdefault('shape_edits', [])
    zone = lambda lo, hi: -.6 < (lo[0] + hi[0]) / 2 < 1.1 and -1.25 < (lo[1] + hi[1]) / 2 < -.25 and hi[2] < 1.3
    b_anvil, n_a = _take(lambda n, lo, hi: n.startswith(('Forged_Dark_Iron', 'Brushed_Sword_Steel', 'Smithy_Workbench_Wood')) and zone(lo, hi), 7, 'anvil')
    b_forge, n_f = _take(lambda n, lo, hi: n.startswith('Forge_Firebrick'), sum(1 for q in S['parts'] if q.name.startswith('Forge_Firebrick')), 'forge')
    b_bed, _ = _take(lambda n, lo, hi: n.startswith('Charcoal') and abs(lo[2] - .625) < .01 and hi[0] - lo[0] > 1., 1, 'coal bed slab')
    # the old hood's dark flue plate (53 x 53 x 8 cm at z 3.01-3.09): with that hood gone it floated inside the new chimney (FBX loose check)
    b_flue, _ = _take(lambda n, lo, hi: n.startswith('Charcoal') and abs(lo[2] - 3.01) < .02 and .4 < hi[0] - lo[0] < .7, 1, 'old flue plate')
    b_bed += b_flue
    chamber = lambda lo, hi: -2.3 < (lo[0] + hi[0]) / 2 < -1.25 and .5 < (lo[1] + hi[1]) / 2 < 1.5 and hi[2] < 1.
    b_coal, n_c = _take(lambda n, lo, hi: n.startswith(('Charcoal', 'Hot_Ember')) and chamber(lo, hi), 23, 'coal lumps')
    k0 = len(S['parts'])
    anvil(P); stump(P)
    a_anvil = _tris(S['parts'][k0:]); k1 = len(S['parts'])
    nb = forge(P); bellows(P); poker(P); k2 = len(S['parts'])
    a_forge = _tris(S['parts'][k1:k2])
    nl = coal_heap(P); a_coal = _tris(S['parts'][k2:])
    # a light socket in the fire chamber (2026-11-11): the embers glow by emission only and light nothing; the game can hang a
    # small warm point light here. Centred on the mouth (x -1.80), 0.27 m inside the front face (y 0.28), 0.23 m over the coal bed.
    ti_core.socket('Socket_ForgeLight', (MX, .55, .95))
    S['forge_light_socket'] = {'at_blender_xyz': [MX, .55, .95], 'use': 'a small warm point light (no shadows) for the forge fire',
                               'tested_in_unity': 'orange point light, range 3 m, intensity 2, editor batch shots only'}
    S['shape_edits'] += [
        {'part': 'anvil and stump', 'why': 'review (Unity shot): body, a 5 cm light steel slab and a heel block stacked; octagonal stump',
         'replaced_parts': n_a, 'triangles_before': b_anvil, 'triangles_after': a_anvil},
        {'part': 'forge', 'why': 'review (Unity shot): ~70 bricks of 20-80 cm, hood and back wall one block each, texture smeared',
         'replaced_parts': n_f + 2, 'new_bricks': nb, 'triangles_before': b_forge + b_bed, 'triangles_after': a_forge},
        {'part': 'forge fire', 'why': 'review: a few lumps with a giraffe-like glow pattern; a heap of coal, some burning (dark crust, glowing cracks)',
         'replaced_parts': n_c, 'new_lumps': nl, 'triangles_before': b_coal, 'triangles_after': a_coal}]


def bellows(P):
    """A Chinese box bellows beside the forge (push-pull rod, T handle), its nozzle into the forge base."""
    x0, x1, y0, y1, z0, z1 = -.85, -.53, .50, 1.38, .205, .60
    box('Bellows_Box', (x0, y0, z0), (x1, y1, z1), P['plank'], 'Wood', grain='y')
    for xa in ((-.84, -.80), (-.58, -.54)):
        box('Bellows_Skid', (xa[0], y0 + .03, .1815), (xa[1], y1 - .03, z0 + .01), P['timber'], 'Wood', grain='y')
    for yy in (y0, y1):                                     # corner posts, proud 1.2 cm
        for xx in (x0, x1):
            box('Bellows_Post', (xx - .012 if xx == x0 else xx - .03, yy - .012 if yy == y0 else yy - .03, z0 - .005),
                (xx + .03 if xx == x0 else xx + .012, yy + .03 if yy == y0 else yy + .012, z1 + .012), P['timber'], 'Wood', grain='z')
    for zz in (z0 + .02, z1 - .05):                         # rails along the visible long side
        box('Bellows_Rail', (x1 - .01, y0 + .03, zz), (x1 + .01, y1 - .03, zz + .03), P['timber'], 'Wood', grain='y')
    box('Bellows_Lid_Batten', (x0 + .03, (y0 + y1) / 2 - .02, z1 - .01), (x1 - .03, (y0 + y1) / 2 + .02, z1 + .014), P['timber'], 'Wood', grain='x')
    k = 14; xr, zr = -.69, .44
    loft('Bellows_Rod', [[(xr + a, yy, zr + b) for a, b, _ in _se(.011, .011, 2., k)] for yy in (y0 + .02, .24)], P['timber'], 'Wood', grain=(0., 1., 0.))
    loft('Bellows_Handle', [[(xx, .235 + a, zr + b) for a, b, _ in _se(.016, .016, 2., k)] for xx in (-.80, -.58)], P['timber'], 'Wood')
    loft('Bellows_Nozzle', [[(xx, .95 + a, .32 + b) for a, b, _ in _se(.028, .028, 2., k)] for xx in (x0 + .02, -.885)], P['forged_iron'], 'Main')


def poker(P):
    """A fire hook leaning against the forge front, right of the mouth."""
    pts = [(-1.13, .17, .19), (-1.16, .268, 1.12), (-1.162, .262, 1.165), (-1.164, .238, 1.185), (-1.165, .215, 1.175)]
    k = 10; rings = []
    for i, p in enumerate(pts):
        q0 = Vector(pts[max(i - 1, 0)]); q1 = Vector(pts[min(i + 1, len(pts) - 1)]); t = (q1 - q0).normalized()
        u = t.cross(Vector((1, 0, 0))).normalized(); w = t.cross(u)
        rings.append([tuple(Vector(p) + (u * math.cos(math.tau * j / k) + w * math.sin(math.tau * j / k)) * .008) for j in range(k)])
    loft('Forge_Poker', rings, P['forged_iron'], 'Main')


def coal_heap(P, n=72):
    rng = np.random.default_rng(1111); out = 0
    for q in range(n):
        x = MX + rng.uniform(-.43, .43); y = rng.uniform(.36, 1.5)
        d2 = (x - MX) ** 2 / .08 + (y - .95) ** 2 / .12
        s = rng.uniform(.032, .065) * (1.15 if d2 < 1 else 1.)
        z = FZ0 + H + .012 + .085 * math.exp(-d2) - s * .25
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.)
        sx, sy, sz = (rng.uniform(.8, 1.25) for _ in range(3))
        for v in bm.verts:
            v.co = Vector((v.co.x * sx, v.co.y * sy, v.co.z * sz * .8)) * s * float(rng.uniform(.86, 1.12))
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=__import__('mathutils').Euler(tuple(rng.uniform(0, 6.3, 3))).to_matrix())
        bmesh.ops.translate(bm, verts=bm.verts, vec=(x, y, z))
        me = bpy.data.meshes.new('Coal'); bm.to_mesh(me); bm.free(); me.uv_layers.new(name='UVMap')
        o = bpy.data.objects.new('Coal', me); bpy.context.scene.collection.objects.link(o)
        hot = rng.random() < .85 * math.exp(-d2 * .45)
        ti_core.finish(o, 'Forge_Ember_Coal' if hot else 'Forge_Coal', P['ember2'] if hot else P['charcoal'], grain='z', group='Detail_Small', detail=1)
        out += 1
    return out


def ember_mat(name, emit=(1., .33, .06)):
    """Burning coal: dark crust with ash-grey patches, thin glowing cracks and a few hot patches (the old ember glowed in wide cells)."""
    m, g = tm._new(name, 'Main')
    Pp = g.geo('Position')
    crack = g.math('MULTIPLY', g.maprange(g.voronoi(Pp, 60.0), .0, .018, 1, 0), g.maprange(g.noise(Pp, 7.0, 3, .5), .38, .62))
    hot = g.math('MULTIPLY', g.maprange(g.noise(Pp, 14.0, 4, .55), .56, .74), .75)
    gm = g.math('MAXIMUM', crack, hot)
    ash = g.maprange(g.noise(Pp, 40.0, 3, .6), .5, .7)
    crust = g.mix(ash, (.025, .022, .02), (.1, .095, .09))
    col = g.mix(gm, crust, tuple(c * .5 for c in emit))
    em = g.ramp(gm, [(0., (0., 0., 0.)), (.3, (.22, .05, .008)), (.8, emit), (1., (1., .75, .35))])
    tm._finish(g, col, .9, 0., g.bump(ash, .25, .001), emit=em)
    return m


def palette_extra_smithy(P):
    P['ember2'] = ember_mat('Forge_Burning_Coal'); tm.set_emission(P['ember2'], 3.)
    # the body under forge scale: near-black, dull, rust in the dents, worn bright only on the edges. tm.metal (metallic .92) mirrored
    # the sky in the URP shot and read as chrome; only the face is polished steel
    P['anvil_iron'] = __import__('mk_mats').cast_iron('Anvil_Iron')
    P['anvil_face'] = tm.metal('Anvil_Face_Steel', (.27, .27, .265), (.07, .06, .05), rough=.36, patina_amt=.22, hammered=.12, patina_scale=24.)
    P['forge_mortar'] = cm.stone('Forge_Mortar', light=(.075, .066, .058), dark=(.03, .026, .023), ochre=(.05, .035, .025), moss=0., lichen=0., crack=.2)
    P['forge_soot'] = cm.stone('Forge_Soot', light=(.04, .032, .027), dark=(.012, .01, .009), ochre=(.05, .025, .012), moss=0., lichen=0., crack=.3)
    P['forge_soot_brick'] = cm.stone('Forge_Brick_Sooted', light=(.075, .055, .045), dark=(.022, .017, .014), ochre=(.07, .04, .025), moss=0., lichen=0., crack=.45)
    P['firebrick_c'] = cm.stone('Forge_Brick_C', light=(.2, .14, .095), dark=(.075, .05, .036), ochre=(.17, .1, .055), moss=0., lichen=0., crack=.4)


# ---------------------------------------------------------------- materials shop

PROF = {   # normalised (r / R, z / H) of the thrown body, from just inside the foot ring to the mouth
    'ovoid': [(.62, .07), (.80, .16), (.93, .30), (1., .48), (.96, .64), (.80, .78), (.58, .86), (.46, .89), (.44, .93), (.49, .965), (.47, .985), (.40, .99), (0, .975)],
    'guan':  [(.60, .07), (.72, .14), (.86, .30), (.97, .52), (1., .66), (.93, .78), (.70, .88), (.50, .92), (.48, .95), (.53, .975), (.50, .995), (.40, 1.), (0, .985)],
    'globe': [(.64, .07), (.86, .18), (.98, .35), (1., .50), (.94, .68), (.78, .82), (.60, .90), (.58, .95), (.62, .985), (.58, 1.), (.48, 1.), (0, .975)],
}
FOOT = [(0, 0.), (.60, 0.), (.65, .012), (.685, .05), (.70, .095), (0, .095)]
# jar order as listed in the source: Counter_Medicine_Jar_0-5, Interior_Jar_0-3, Shelf_Jar_0-3 (sorted by name); shape, cover
PLAN = [('ovoid', 'cloth'), ('globe', None), ('guan', 'lid'), ('guan', 'lid'), ('ovoid', 'cloth'), ('globe', None),
        ('guan', 'lid'), ('globe', None), ('ovoid', 'cloth'), ('guan', 'lid'),
        ('globe', None), ('ovoid', 'cloth'), ('guan', 'lid'), ('globe', None)]


LABELS = {0, 1, 4, 5, 7, 8, 10, 11}


def label(c, rz, z0, Hj, mat, ac=-math.pi / 2, span=.30, nz=4, na=7, ink=None):
    """A faded red paper label pasted on the belly, facing the shop front: a thin curved shell 1.2-2.4 mm off the glaze;
    with `ink`, brush marks 1.0-1.8 mm off the paper: the name as three marks of uneven size down the middle, a little left of centre,
    and a short second column of two small marks on the right (the maker or the date), each jar with its own hand."""
    _patch(c, rz, z0, Hj, mat, ac, span, .40, .60, .0012, .0024, nz, na, 'Jar_Label')
    if ink is not None:
        rng = random.Random(round(c[0] * 1000) * 7919 + round(c[1] * 1000))
        col = [(ac - .03 + rng.uniform(-.012, .012), rng.uniform(.045, .075), zc + rng.uniform(-.006, .006), rng.uniform(.013, .02))
               for zc in (.452, .50, .548)]
        col += [(ac + .17 + rng.uniform(-.008, .008), rng.uniform(.022, .032), zc, rng.uniform(.008, .011)) for zc in (.47, .515)]
        for a, w, zc, h in col:
            _patch(c, rz, z0, Hj, ink, a, w, zc - h, zc + h, .0034, .0042, 1, 2, 'Jar_Label_Ink')


def _patch(c, rz, z0, Hj, mat, ac, span, za, zb, off0, off1, nz, na, name):
    v = []
    for off in (off1, off0):
        for i in range(nz + 1):
            zf = za + (zb - za) * i / nz; r = rz(zf) + off
            for j in range(na + 1):
                a = ac - span + 2 * span * j / na
                v.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a), z0 + zf * Hj))
    W = na + 1; N = (nz + 1) * W; f = []
    for i in range(nz):
        for j in range(na):
            q = i * W + j; f.append((q, q + 1, q + W + 1, q + W)); f.append((N + q, N + q + W, N + q + W + 1, N + q + 1))
    ring = list(range(W)) + [i * W + na for i in range(1, nz + 1)] + [nz * W + j for j in range(na - 1, -1, -1)] + [i * W for i in range(nz - 1, 0, -1)]
    for a, b in zip(ring, ring[1:] + ring[:1]): f.append((a, b, N + b, N + a))
    ti_core.finish(_obj(name, v, f), name, mat, grain='z', group='Detail_Small', detail=1)


def palette_extra_shop(P):
    P['jar_label'] = tm.plain('Jar_Label_Paper', (.2, .055, .04), rough=.88, noise=.4)          # faded red, sun-bleached
    P['jar_ink'] = tm.plain('Jar_Label_Ink', (.012, .01, .009), rough=.7, noise=.3)
    P['g_celadon'] = tm.glaze('Jar_Matte_Celadon', (.05, .072, .058), (.02, .03, .024), rough=.42, crackle=30., mottle=.45)
    P['g_tea'] = tm.glaze('Jar_Matte_TeaDust', (.05, .05, .03), (.02, .02, .012), rough=.55, crackle=25., mottle=.5)
    P['g_brown'] = tm.glaze('Jar_Matte_Brown', (.085, .048, .025), (.035, .02, .01), rough=.45, mottle=.45)
    P['g_black'] = tm.glaze('Jar_Matte_Tenmoku', (.022, .016, .011), (.06, .035, .018), rough=.4, mottle=.5)
    P['g_buff'] = tm.glaze('Jar_Matte_Buff', (.30, .265, .19), (.14, .12, .08), rough=.5, mottle=.4)
    P['jar_clay'] = tm.plain('Jar_Foot_Clay', (.2, .13, .08), rough=.9, noise=.3)
    P['jar_cloth'] = mk.cloth('Jar_Cover_Cloth', (.15, .07, .045), dirt=.35, worn=.2)
    P['jar_tie'] = mk.hemp('Jar_Tie_Hemp')


def _glaze_for(src_mat, k, P):
    if src_mat.endswith('_0'): return P['g_celadon'] if k % 2 == 0 else P['g_tea']
    if src_mat.endswith('_1'): return P['g_brown'] if k % 2 == 0 else P['g_black']
    return P['g_buff']


def shop_jars(P):
    S.setdefault('shape_edits', [])
    jars = sorted([q for q in S['parts'] if q.name.startswith('Shop_Glazed_Jar')], key=lambda q: (round(_bounds(q)[0][2], 2), round(_bounds(q)[0][0], 2), round(_bounds(q)[0][1], 2)))
    assert len(jars) == 14, len(jars)
    before = _tris(jars); info = []
    for q in jars:
        lo, hi = _bounds(q); info.append((lo, hi, q.get('group', 'Main'), q.name.split('_Part')[0]))
    for q in jars:
        S['parts'].remove(q); bpy.data.objects.remove(q, do_unlink=True)
    k0 = len(S['parts'])                      # after the removal: the new parts are the tail of the list
    for k, (lo, hi, group, src) in enumerate(info):
        shape, cover = PLAN[k]
        c = ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2); Hj = hi[2] - lo[2]; Rj = min(hi[0] - lo[0], hi[1] - lo[1]) / 2 * .92; z0 = lo[2]
        # the source jars hover up to 6.5 mm over their shelf (FBX loose check, measured on the shelf behind the counter): stand each one
        # on the top of what is under its centre, the foot ring's edge 0.5 mm above it (an edge, so nothing lies flat on the board)
        tops = [b[1][2] for b in (_bounds(q) for q in S['parts'][:k0] if q.type == 'MESH')
                if b[0][0] < c[0] < b[1][0] and b[0][1] < c[1] < b[1][1] and z0 - .03 < b[1][2] < z0 + .003]
        if tops: z0 = max(tops) + .0005 - .0015
        det = 1 if group == 'Detail_Small' else 0
        g = _glaze_for(src, k, P)
        # a thrown foot ring: the base is recessed and only a bevelled ring meets the shelf, 1.5 mm up, so no face lies flat on the
        # board (a flat base on the board made the pipeline split the board's faces around it)
        foot = [(0, z0 + .007), (.5 * Rj, z0 + .007), (.6 * Rj, z0 + .0015)] + [(r * Rj, z0 + z * Hj) for r, z in FOOT[2:]]
        lathe('Jar_Foot', foot, c, P['jar_clay'], group, seg=24, detail=det)
        prof = [(r * Rj, z0 + z * Hj) for r, z in PROF[shape]]
        prof = [(0, z0 + .07 * Hj)] + prof
        lathe('Jar_Body', prof, c, g, group, seg=24, detail=det)
        lip_r = max(r for r, z in PROF[shape][-4:]) * Rj; lip_z = z0 + max(z for r, z in PROF[shape]) * Hj
        zs_, rs_ = [z for r, z in PROF[shape][:-1]], [r for r, z in PROF[shape][:-1]]
        rz = lambda zf, zs_=zs_, rs_=rs_: Rj * float(np.interp(zf, zs_, rs_))
        if k in LABELS: label(c, rz, z0, Hj, P['jar_label'], ink=P['jar_ink'])
        if shape == 'guan':
            for a in (0., math.pi):
                rr = rz(.80) + .004
                ti_core.torus('Jar_Ear', (c[0] + rr * math.cos(a), c[1] + rr * math.sin(a), z0 + .80 * Hj), .014, .0055, g,
                              rot=(math.pi / 2, 0, a + math.pi / 2), major=12, minor=6, group=group, detail=det)
        if cover == 'lid':
            lathe('Jar_Lid', [(0, lip_z - .004), (lip_r + .012, lip_z - .004), (lip_r + .014, lip_z + .014), (lip_r + .004, lip_z + .02),
                              (.026, lip_z + .02), (.024, lip_z + .036), (.014, lip_z + .042), (0, lip_z + .043)],
                  c, P['plank'], 'Detail_Small', seg=20, grain=(1., 0., 0.), detail=1)
        elif cover == 'cloth':
            rm = lip_r
            lathe('Jar_Cloth_Cover', [(0, lip_z - .045), (rm * .98, lip_z - .045), (rm * .97, lip_z - .03), (rm * 1.1, lip_z - .012),
                                      (rm * 1.08, lip_z + .004), (rm * .85, lip_z + .02), (rm * .45, lip_z + .032), (0, lip_z + .036)],
                  c, P['jar_cloth'], 'Detail_Small', seg=24, detail=1)
            band('Jar_Cloth_Tie', c, rm * .965, rm * .965 + .007, lip_z - .036, lip_z - .027, P['jar_tie'], 'Detail_Small', seg=24, detail=1)
    after = _tris(S['parts'][k0:])
    S['shape_edits'].append({'part': '14 glazed jars', 'why': 'review (Unity shot): one egg shape, glossy highlight; rebuilt as three thrown shapes '
                             'with foot, neck and lip, cloth covers and lids, semi-matte glaze; footprint 8 % narrower so the rows do not crowd',
                             'triangles_before': before, 'triangles_after': after})
