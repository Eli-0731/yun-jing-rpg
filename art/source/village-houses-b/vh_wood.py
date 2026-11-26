"""VH01-03 wood (2026-11-10 rework after review: "木材看起來很假").

What made the old timber read fake (the shared cr_mats.wood):
  - one saturated red-brown everywhere (R:G:B about 4:2:1), so beams, doors and logs looked like stained furniture veneer;
  - only fine straight streaks along the grain: they blur to a smooth gradient in the ~130 px/m bake, no figure, no checks;
  - no weathering logic: exposed faces and sheltered faces, end grain and side grain all the same tone;
  - door leaves were one flat slab each; firewood was the same timber material on 7-sided cylinders (no bark, no split face, no end grain).

This module, used only by the VH palettes (VL01-05 keep their materials):
  old_wood()   weathered softwood: per-member tone, flame figure big enough to survive the bake, sparse drying checks along the grain,
               darker end grain, sun-greyed exposed faces and browner sheltered ones, rain streaks, worn lighter edges, raised latewood.
  firewood()   split billets read from per-vertex 'bark' (1 = bark) and 'lc' (along m, cross-section u/R, v/R): furrowed bark with lichen,
               fibrous split faces, end grain with heartwood, rings and radial checks.
  split_log()  billet geometry: round, half, third or quarter splits, slanted saw cuts, bark faces smooth, split faces and ends flat.
  plank_leaf() a door or gate leaf of separate boards (varied widths, uneven feet, V-seams) with battens on one side and nail heads.
"""
import math, random
import bpy
from mathutils import Vector, Matrix
import ti_mats as tm
import mk_mats as mm
from mk_mats import dabs
from ti_core import box, mesh, cyl
from cr_parts import set_float, set_attr_list


def _p(g):
    P = g.geo('Position'); sep = g.node('ShaderNodeSeparateXYZ'); g.link(P, sep.inputs[0])
    nz = g.node('ShaderNodeSeparateXYZ'); g.link(g.geo('Normal'), nz.inputs[0])
    return P, sep.outputs['Z'], nz.outputs['Z'], sep


def _sep(g, v):
    s = g.node('ShaderNodeSeparateXYZ'); g.link(v, s.inputs[0]); return s.outputs['X'], s.outputs['Y'], s.outputs['Z']


def _vec(g, x, y, z):
    c = g.node('ShaderNodeCombineXYZ')
    for i, v in enumerate((x, y, z)): g._in(c.inputs[i], v)
    return c.outputs[0]


def _lerp(a, b, t): return tuple(x + (y - x) * t for x, y in zip(a, b))


def old_wood(name, dark, light, weather=(.12, .115, .1), grey=.45, slot='Main', ground_h=.12, period=.042, checks=1., wear=.45, sheen=0.):
    """dark/light: the sheltered timber's range; weather: the sun-greyed tone exposed faces drift to (grey = how far)."""
    m, g = tm._new(name, slot)
    co, r = tm._grain_coords(g, (1, 1, 1))
    u, v, w = _sep(g, co)                                          # u along the grain (m); v, w across it, offset per part
    P, Z, up, ps = _p(g)
    # -- flame figure: growth bands across the grain, bent by slow noise along it so they meet in arches and long flames
    bend = g.math('MULTIPLY', g.math('SUBTRACT', g.noise(_vec(g, g.math('MULTIPLY', u, .9), g.math('MULTIPLY', v, 3.), g.math('MULTIPLY', w, 3.)), 1.0, 3, .5), .5), .16)
    wob = g.math('MULTIPLY', g.math('SUBTRACT', g.noise(_vec(g, g.math('MULTIPLY', u, 6.), v, w), 1.0, 2, .5), .5), .025)
    band = g.math('ADD', g.math('ADD', v, g.math('MULTIPLY', w, .83)), g.math('ADD', bend, wob))
    s = g.math('SINE', g.math('MULTIPLY', band, 2 * math.pi / period))
    late = g.maprange(s, .35, .92)                                 # the darker, harder latewood band (about a third of each ring)
    # -- broad tone: per member, long soft shifts, a few painterly patches
    long = g.noise(_vec(g, g.math('MULTIPLY', u, .5), g.math('MULTIPLY', v, 7.), g.math('MULTIPLY', w, 7.)), 1.0, 3, .5)
    dab = dabs(g, _vec(g, g.math('MULTIPLY', u, .6), g.math('MULTIPLY', v, 4.), g.math('MULTIPLY', w, 4.)), 5.0)
    t = g.math('ADD', g.math('ADD', g.math('MULTIPLY', r, .42), g.math('MULTIPLY', long, .38)), g.math('MULTIPLY', dab, .2))
    mid = _lerp(dark, light, .5)
    col = g.ramp(t, [(.22, tuple(c * .8 for c in dark)), (.45, dark), (.62, mid), (.85, light)])
    col = g.mix(g.math('MULTIPLY', late, .5), col, tuple(c * .62 for c in dark))
    # -- fibre: coarse streaks along the grain (about 1-2 bake pixels wide)
    fib = g.maprange(g.noise(_vec(g, g.math('MULTIPLY', u, .7), g.math('MULTIPLY', v, 55.), g.math('MULTIPLY', w, 55.)), 1.0, 2, .5), .42, .68)
    col = g.mix(g.math('MULTIPLY', fib, .22), col, tuple(c * .7 for c in dark))
    # -- end grain (faces across the grain): darker, rougher, the bands read as rings
    gA = g.attr('gA')
    endm = g.maprange(g.math('ABSOLUTE', g.vmath('DOT_PRODUCT', g.geo('Normal'), gA)), .55, .85)
    col = g.mix(g.math('MULTIPLY', endm, .55), col, tuple(c * .5 for c in dark))
    # -- weathering: exposed faces go silver-grey in irregular patches; sheltered faces (low AO) stay brown
    ao = g.ao(.06)
    expo = g.math('ADD', g.math('MULTIPLY', g.maprange(ao, .55, 1.), .7), g.math('MULTIPLY', g.maprange(up, .2, .9), .3))
    patch = g.maprange(g.noise(P, 2.4, 3, .55), .3, .72)
    gw = g.math('MULTIPLY', g.math('MULTIPLY', expo, g.math('ADD', .35, g.math('MULTIPLY', patch, .65))), grey)
    gw = g.math('MULTIPLY', gw, g.math('SUBTRACT', 1., g.math('MULTIPLY', late, .35)))     # latewood weathers slower: stripes survive in the grey
    col = g.mix(gw, col, weather)
    # -- drying checks: long thin cracks along the grain, a few per member, fading out at their ends
    ck = g.voronoi(_vec(g, g.math('MULTIPLY', u, .55), g.math('MULTIPLY', v, 16.), g.math('MULTIPLY', w, 16.)), 1.0)
    keep = g.math('MULTIPLY', g.maprange(g.noise(_vec(g, g.math('MULTIPLY', u, 1.3), g.math('MULTIPLY', v, 5.), g.math('MULTIPLY', w, 5.)), 1.0, 2, .5), .52, .66), checks)
    crack = g.math('MULTIPLY', g.maprange(ck, .07, .015), keep)
    col = g.mix(g.math('MULTIPLY', crack, .9), col, tuple(c * .3 for c in dark))
    # -- rain streaks down vertical faces, earth grime at the foot
    streak = g.maprange(g.noise(_vec(g, g.math('MULTIPLY', ps.outputs['X'], 26.), g.math('MULTIPLY', ps.outputs['Y'], 26.), g.math('MULTIPLY', Z, 1.6)), 1.0, 3, .5), .55, .72)
    col = g.mix(g.math('MULTIPLY', g.math('MULTIPLY', streak, g.maprange(g.math('ABSOLUTE', up), .5, .1)), .3), col, tuple(c * .6 for c in dark))
    if ground_h: col = mm.ground(g, col, Z, P, ground_h, False)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.32, .29, .27)), (1, (1, 1, 1))]))
    # -- worn, rounded edges: lighter and greyer where hands and weather rub
    e = g.edge(.006)
    col = g.mix(g.math('MULTIPLY', e, wear), col, tuple(min(1., (a + b) * .62 + .02) for a, b in zip(light, weather)))
    rough = g.math('SUBTRACT', g.math('ADD', .9, g.math('MULTIPLY', endm, .05)), g.math('ADD', g.math('MULTIPLY', late, .05), g.math('MULTIPLY', e, .08)))
    if sheen: rough = g.math('SUBTRACT', rough, g.math('MULTIPLY', sheen, g.math('SUBTRACT', 1., endm)))
    h = g.math('ADD', g.math('MULTIPLY', late, .55), g.math('MULTIPLY', fib, .3))
    h = g.math('SUBTRACT', h, g.math('MULTIPLY', crack, 1.4))
    tm._finish(g, col, rough, 0.0, g.bump(h, .6, .003), spec=.22)
    return m


def firewood(name, slot='Main', bark=((.032, .027, .022), (.085, .072, .056)), split=((.075, .062, .047), (.15, .126, .094)), heart=(.09, .056, .033)):
    m, g = tm._new(name, slot)
    co, r = tm._grain_coords(g, (1, 1, 1))
    P, Z, up, ps = _p(g)
    bk = g.attr('bark', 'Fac')
    la, cu, cv = _sep(g, g.attr('lc'))                      # along (m), cross-section / R
    rad = g.vmath('LENGTH', _vec(g, cu, cv, 0.))
    ang = g.math('ARCTAN2', cv, cu)
    gA = g.attr('gA')
    endm = g.maprange(g.math('ABSOLUTE', g.vmath('DOT_PRODUCT', g.geo('Normal'), gA)), .55, .85)
    # rings: about four per billet, wobbling a little; heartwood darker
    rw = g.math('ADD', rad, g.math('MULTIPLY', g.math('SUBTRACT', g.noise(_vec(g, g.math('MULTIPLY', la, 3.), cu, cv), 4.0, 2, .5), .5), .12))
    ring = g.maprange(g.math('SINE', g.math('MULTIPLY', rw, 2 * math.pi * 4.2)), .3, .95)
    # split face: fibrous, rings show as long stripes where the split crosses them
    fib = g.maprange(g.noise(_vec(g, g.math('MULTIPLY', la, 1.2), g.math('MULTIPLY', cu, 9.), g.math('MULTIPLY', cv, 9.)), 1.0, 3, .5), .35, .7)
    t = g.math('ADD', g.math('ADD', g.math('MULTIPLY', fib, .45), g.math('MULTIPLY', r, .35)), g.math('MULTIPLY', ring, .2))
    sc = g.ramp(t, [(.2, split[0]), (.5, _lerp(*split, .5)), (.85, split[1])])
    sc = g.mix(g.math('MULTIPLY', g.maprange(rad, .62, .35), .55), sc, heart)
    sc = g.mix(g.math('MULTIPLY', ring, .32), sc, tuple(c * .55 for c in split[0]))
    # end grain: same rings, sawn surface darker in the dirt, radial checks from the pith on some billets
    chk = g.math('MULTIPLY', g.maprange(g.math('ABSOLUTE', g.math('SINE', g.math('ADD', g.math('MULTIPLY', ang, 1.5), g.math('MULTIPLY', r, 40.)))), .035, .0),
                 g.math('MULTIPLY', g.maprange(rad, .05, .25), g.maprange(r, .35, .5)))
    ec = g.mix(g.math('MULTIPLY', ring, .5), sc, tuple(c * .5 for c in split[0]))
    ec = g.mix(g.math('MULTIPLY', chk, .95), ec, (.02, .016, .012))
    ec = g.mix(g.math('MULTIPLY', g.maprange(rad, .85, 1.02), .8), ec, bark[0])            # the bark rim seen on the end
    wood_c = g.mix(endm, sc, ec)
    # bark: deep furrows running along the billet, lichen flecks
    fur = g.noise(_vec(g, g.math('MULTIPLY', la, 2.5), g.math('MULTIPLY', cu, 7.), g.math('MULTIPLY', cv, 7.)), 1.0, 4, .6)
    bc = g.ramp(fur, [(.32, tuple(c * .7 for c in bark[0])), (.5, bark[0]), (.7, bark[1])])
    li = g.math('MULTIPLY', g.maprange(g.noise(P, 30.0, 3, .6), .6, .7), g.maprange(g.noise(P, 4.0, 2, .5), .45, .6))
    bc = g.mix(g.math('MULTIPLY', li, .7), bc, (.15, .155, .11))
    bm_ = g.math('MULTIPLY', bk, g.math('SUBTRACT', 1., endm))
    col = g.mix(bm_, wood_c, bc)
    # stacked a while: grey on what faces out, dark in the gaps
    ao = g.ao(.05)
    col = g.mix(g.math('MULTIPLY', g.math('MULTIPLY', g.maprange(ao, .6, 1.), g.maprange(g.noise(P, 3.0, 2, .5), .3, .7)), .35), col, (.13, .12, .105))
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.25, .22, .2)), (1, (1, 1, 1))]))
    e = g.edge(.004)
    col = g.mix(g.math('MULTIPLY', g.math('MULTIPLY', e, g.math('SUBTRACT', 1., bk)), .35), col, (.26, .22, .16))
    rough = g.math('ADD', .86, g.math('MULTIPLY', bk, .1))
    h = g.math('ADD', g.math('MULTIPLY', g.math('MULTIPLY', fur, bk), 1.2), g.math('MULTIPLY', g.math('MULTIPLY', fib, g.math('SUBTRACT', 1., bk)), .4))
    h = g.math('SUBTRACT', g.math('ADD', h, g.math('MULTIPLY', ring, .25)), g.math('MULTIPLY', chk, 1.2))
    tm._finish(g, col, rough, 0.0, g.bump(h, .7, .004), spec=.2)
    return m


# ------------------------------------------------------------------ split firewood billets
KINDS = {'round': 2 * math.pi, 'half': math.pi, 'third': 2 * math.pi / 3, 'quarter': math.pi / 2}


def section(kind, R, rnd):
    """Cross-section (y, z) of a billet around its log axis: bark arc points and, for splits, the apex the split faces meet at."""
    span = KINDS[kind]
    n = {'round': 9, 'half': 7, 'third': 5, 'quarter': 4}[kind]
    rr = lambda: R * (1. + rnd.uniform(-.06, .06))
    if kind == 'round':
        arc = [(rr() * math.cos(2 * math.pi * i / n), rr() * math.sin(2 * math.pi * i / n)) for i in range(n)]
        return arc, None
    a0 = -span / 2
    arc = [(rr() * math.cos(a0 + span * i / n), rr() * math.sin(a0 + span * i / n)) for i in range(n + 1)]
    if kind == 'half':
        apex = None                                                    # a half split: one flat face across the chord near the pith
    else:
        ax = R * rnd.uniform(.04, .14)                                 # wedges: the split faces meet a little off the pith
        apex = (ax, rnd.uniform(-.03, .03) * R)
    return arc, apex


def section_extent(kind, R, roll):
    """Width (across the log, horizontal) and height of a billet's section after rolling it about its axis (no noise)."""
    arc, apex = section(kind, R, random.Random(0))
    pts = arc + ([apex] if apex else [])
    c, s = math.cos(roll + math.pi / 2), math.sin(roll + math.pi / 2)          # the same roll split_log applies
    ys = [y * c - z * s for y, z in pts]; zs = [y * s + z * c for y, z in pts]
    return max(ys) - min(ys), max(zs) - min(zs), min(zs), (max(ys) + min(ys)) / 2


def split_log(name, p, d, L, R, kind, roll, mat, seed=0, cut=.12, tilt=None, **kw):
    """Billet centred at p with its axis along unit vector d (horizontal or tilted), length L, bark radius R.
    roll: rotation of the section about the axis (0 = the arc's middle pointing up when d is horizontal)."""
    rnd = random.Random(seed)
    arc, apex = section(kind, R, rnd)
    a1, a2 = rnd.uniform(-cut, cut), rnd.uniform(-cut, cut)            # saw cuts a little off square
    b1, b2 = rnd.uniform(-cut, cut), rnd.uniform(-cut, cut)
    if tilt: a1, a2, b1, b2 = tilt                                      # caller-chosen cut angles (stack keeps touching ends from sharing a plane)
    xe = lambda end, y, z: end * L / 2 + (y * math.tan(a1) + z * math.tan(a2) if end > 0 else y * math.tan(b1) + z * math.tan(b2))
    # local frame: x along the log, the section in (y, z) rolled so the arc's middle points up
    cr, sr = math.cos(roll + math.pi / 2), math.sin(roll + math.pi / 2)
    rot = lambda y, z: (y * cr - z * sr, y * sr + z * cr)
    d = Vector(d).normalized()
    side = Vector((0, 0, 1)).cross(d)
    if side.length < 1e-4: side = Vector((1, 0, 0))
    side.normalize(); upv = d.cross(side).normalized()
    to_w = lambda x, y, z: tuple(Vector(p) + d * x + side * y + upv * z)
    # one closed mesh (shared verts, so normals stay consistent through every later recalc); 'bark' is stored per face corner,
    # so the bark / split / end boundary stays sharp without splitting the surface
    V, LC = [], []
    def vert(x, y, z):
        ry, rz = rot(y, z)
        V.append(to_w(x, ry, rz)); LC.append((x, y / R, z / R)); return len(V) - 1
    closed = kind == 'round'
    ring_a = [vert(xe(-1, *rot(y, z)), y, z) for y, z in arc]
    ring_b = [vert(xe(1, *rot(y, z)), y, z) for y, z in arc]
    F, kinds = [], []
    na = len(arc)
    for i in range(na if closed else na - 1):
        j = (i + 1) % na
        F.append((ring_a[i], ring_a[j], ring_b[j], ring_b[i])); kinds.append('bark')
    cap_a, cap_b = list(ring_a), list(ring_b)
    if not closed:
        if apex:
            ax_a, ax_b = vert(xe(-1, *rot(*apex)), *apex), vert(xe(1, *rot(*apex)), *apex)
            F.append((ring_a[-1], ax_a, ax_b, ring_b[-1])); kinds.append('split')
            F.append((ax_a, ring_a[0], ring_b[0], ax_b)); kinds.append('split')
            cap_a.append(ax_a); cap_b.append(ax_b)
        else:
            F.append((ring_a[-1], ring_a[0], ring_b[0], ring_b[-1])); kinds.append('split')
    F.append(tuple(cap_a)); kinds.append(('cap', -1))
    F.append(tuple(cap_b)); kinds.append(('cap', 1))
    # wind every face outward about the section centroid (inside every convex section, unlike the pith for a wedge)
    sec = arc + ([apex] if apex else [])
    sy = sum(q[0] for q in sec) / len(sec); sz = sum(q[1] for q in sec) / len(sec)
    cen = Vector(to_w(0., *rot(sy, sz)))
    out = []
    for f, k in zip(F, kinds):
        pts = [Vector(V[i]) for i in f]
        n = Vector((0, 0, 0))
        for i in range(len(pts)):
            n += pts[i].cross(pts[(i + 1) % len(pts)])
        fc = sum(pts, Vector()) / len(pts)
        if isinstance(k, tuple): ref = d * k[1]
        else:
            rel = fc - cen; ref = rel - d * rel.dot(d)
        out.append(f if n.dot(ref) >= 0 else tuple(reversed(f)))
    o = mesh(name, V, out, mat, grain=tuple(d), **kw)
    me = o.data
    isbark = [k == 'bark' for k in kinds]
    for poly, b in zip(me.polygons, isbark): poly.use_smooth = b
    at = me.attributes.get('bark') or me.attributes.new('bark', 'FLOAT', 'CORNER')
    at.data.foreach_set('value', [1. if isbark[poly.index] else 0. for poly in me.polygons for _ in poly.loop_indices])
    # sharp edges where bark meets a split face or an end, so the smooth bark does not bend their shading
    owner = {}
    for poly, b in zip(me.polygons, isbark):
        for ek in poly.edge_keys: owner.setdefault(ek, set()).add(b)
    sh = me.attributes.get('sharp_edge') or me.attributes.new('sharp_edge', 'BOOLEAN', 'EDGE')
    sh.data.foreach_set('value', [len(owner.get(e.key, ())) > 1 for e in me.edges])
    set_attr_list(o, 'lc', LC)
    return o


def stack(name, x0, x1, y_back, depth, z0, top, mat, rnd, R=(.058, .072), L=.5, detail=0, back_jitter=.01, stagger=False, cut=.05, **kw):
    """A tidy stack of split billets, ends flush to the front (-y) within a centimetre, laid in courses: halves flat face down,
    wedges on one split face, so each lies the way it would be stacked by hand. A heightmap keeps every piece resting on the
    course below it (sunk into its valleys, so none floats and the face reads solid). Returns the number of pieces."""
    res = .01; nx = int(round((x1 - x0) / res)); sky = [z0] * nx; count = 0
    placed = []                                                            # (x0, x1, z0, z1, front step, back step) of every piece (stagger)
    y_front = y_back - L
    for course in range(60):
        if min(sky) >= top - .04: break
        x = x0 + (.0 if course % 2 == 0 else rnd.uniform(.02, .05))          # courses start staggered so joints do not line up
        while True:
            kind = rnd.choices(('half', 'quarter', 'third'), (5, 3, 2))[0]
            r = rnd.uniform(*R)
            if kind == 'half': roll = rnd.uniform(-.06, .06)
            else: roll = rnd.choice((-1, 1)) * (math.pi / 2 - KINDS[kind] / 2) + rnd.uniform(-.05, .05)
            wdt, hgt, zmin, ymid = section_extent(kind, r, roll)
            if x + wdt > x1 + .005: break
            i0, i1 = max(0, int(round((x - x0) / res))), min(nx, int(round((x + wdt - x0) / res)))     # bins under the piece only (no overlap with the neighbour)
            c0, c1 = max(0, int(round((x + .2 * wdt - x0) / res))), min(nx, max(int(round((x + .8 * wdt - x0) / res)), int(round((x + .2 * wdt - x0) / res)) + 1))
            base = max(sky[c0:c1])                                        # rests on what is under its middle (the sides overlap the neighbours)
            if base + hgt > top + .01:
                x += wdt; continue
            sink = (.002 + (count % 4) * .0015 if stagger else .004) if base <= z0 + 1e-6 else .3 * hgt     # bottom course: neighbours at distinct depths; above: nests into the valleys
            cz = base - sink - zmin
            Ls = L + rnd.uniform(-back_jitter, back_jitter); yf = y_front + rnd.uniform(-.005, .005)     # front ends flush, back ends free
            if stagger:     # end offsets and undersides differ from every piece already placed that this one touches, so no two faces share a plane
                pz0, pz1 = cz + zmin, cz + zmin + hgt
                near = [q for q in placed if q[0] < x + wdt + .02 and q[1] > x - .02 and q[2] < pz1 + .02 and q[3] > pz0 - .02]
                for _ in range(8):
                    if all(abs(q[2] - pz0) > .003 for q in near): break
                    cz -= .004; pz0 -= .004; pz1 -= .004                   # sink a little deeper until the underside is clear of the others'
                fo = rnd.choice([k for k in range(9) if k not in {q[4] for q in near}] or [count % 9])
                bo = rnd.choice([k for k in range(11) if k not in {q[5] for q in near}] or [count % 11])
                ft = rnd.choice([k for k in range(9) if k not in {q[6] for q in near}] or [count % 9])     # end cut angles on a 3x3 grid, .03 rad apart,
                bt = rnd.choice([k for k in range(9) if k not in {q[7] for q in near}] or [count % 9])     # never the same as a touching piece's
                placed.append((x, x + wdt, pz0, pz1, fo, bo, ft, bt))
                g = (-.03, 0., .03); kw_t = dict(tilt=(g[ft % 3], g[ft // 3], g[bt % 3], g[bt // 3]))
                yf = y_front + fo * .002; Ls = L + bo * .006 - .03 - fo * .002
            split_log(name, (x + wdt / 2 - ymid, yf + Ls / 2, cz), (0., -1., 0.), Ls, r, kind, roll, mat, cut=cut,     # axis -y: local y = world x, local z = up
                      seed=rnd.randrange(1 << 30), detail=detail, group='Wood', **(kw_t if stagger else {}), **kw)
            for i in range(i0, i1): sky[i] = base - sink + hgt
            count += 1
            x += wdt * .9 + rnd.uniform(-.003, .003)                      # the tapering sides overlap a little, so no daylight between pieces
    return count


# ------------------------------------------------------------------ plank leaves
def plank_leaf(name, cx, y, zb, w, h, t, mat, rnd, battens=(), batten_side=1, batten_mat=None, nails=None, n=None, uvw=None, **kw):
    """A leaf of separate vertical boards between x = cx - w/2 .. cx + w/2, its back face at y + t/2 (batten_side +1) or front.
    Boards: varied widths, each a few mm proud or shy, the feet uneven; battens across on batten_side; nail heads on the other face."""
    n = n or max(2, int(round(w / .14)))
    ws = [rnd.uniform(.8, 1.2) for _ in range(n)]; k = w / sum(ws); ws = [a * k for a in ws]
    x = cx - w / 2; dys = []
    for i, bw in enumerate(ws):
        foot = rnd.uniform(0., .012); dy = rnd.uniform(-.0025, .0025) * -batten_side      # boards stand proud or shy only on the face away from the battens
        dy = max(dy, 0.) if batten_side < 0 else min(dy, 0.)
        dys.append(dy)
        box(f'{name}_Board', (x + bw / 2, y + dy, zb + foot + (h - foot) / 2), (bw - .001, t + abs(dy) * 2, h - foot), mat, bevel=.005, seg=1, group='Wood', grain='z',
            **({'uvw': uvw} if uvw else {}), **kw)
        x += bw
    by = y + batten_side * (t / 2 + .0125)
    for z in battens:
        box(f'{name}_Batten', (cx, by, z), (w - .06, .025, .1), batten_mat or mat, bevel=.005, seg=1, group='Wood', grain='x', uvw=.4, **kw)
    if nails is not None:
        x = cx - w / 2
        for bw, dy in zip(ws, dys):
            ny = y + 2 * dy - batten_side * (t / 2 + .0025)                 # the board's own outer face, the head 1.5 mm into it
            for z in battens:
                for dz in (-.025, .025):
                    cyl(f'{name}_Nail', (x + bw / 2 + rnd.uniform(-.015, .015), ny, z + dz), .0075, .008, nails, axis='y', verts=6, bevel=0., group='Main', detail=1)
            x += bw


# ------------------------------------------------------------------ palette hook
def apply(P, cond):
    """Replace the VL timber family in a VH palette. cond: 'elderly' (VH01, VH03) | 'diligent' (VH02).
    The VL materials of the same names are removed first, so the new ones keep the exact names the bake looks up."""
    for k in ('timber', 'door', 'plank', 'boards'):
        old = P.get(k)
        if old is not None and old.name in bpy.data.materials: bpy.data.materials.remove(old)
    if cond == 'elderly':
        P['timber'] = old_wood('Frame_Timber', (.026, .019, .014), (.078, .058, .042), weather=(.11, .105, .094), grey=.5)
        P['door'] = old_wood('Door_Board', (.03, .022, .016), (.09, .066, .047), weather=(.12, .113, .1), grey=.55, ground_h=.2, period=.05)
        P['plank'] = old_wood('Porch_Plank', (.045, .034, .025), (.13, .1, .072), weather=(.14, .13, .115), grey=.45, ground_h=0., sheen=.06)
        P['boards'] = old_wood('Nailed_Board', (.05, .044, .036), (.15, .132, .108), weather=(.16, .152, .135), grey=.7, ground_h=.25, period=.05, checks=1.3)
    else:
        P['timber'] = old_wood('Frame_Timber', (.032, .021, .014), (.098, .066, .044), weather=(.115, .105, .09), grey=.32)
        P['door'] = old_wood('Door_Board', (.036, .025, .017), (.11, .077, .052), weather=(.125, .115, .1), grey=.38, ground_h=.2, period=.05)
        P['plank'] = old_wood('Porch_Plank', (.05, .036, .025), (.15, .11, .076), weather=(.15, .138, .12), grey=.3, ground_h=0., sheen=.08)
        P['boards'] = old_wood('Nailed_Board', (.05, .044, .036), (.15, .132, .108), weather=(.16, .152, .135), grey=.6, ground_h=.25, period=.05)
    P['firewood'] = firewood('Firewood_Billet')
    return P
