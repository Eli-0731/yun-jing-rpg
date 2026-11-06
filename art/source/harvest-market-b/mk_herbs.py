"""Qingling herb (青靈草) plants and bundles for MK02 and the MK04 fill.

A plant: a crown of soil-caked roots, two or three stems, serrated lance leaves in alternate pairs.
Grade shows only in the leaves: top = whole leaves with glowing tips (Glow slot), mid = whole, plain,
low = leaves with real holes (faces removed), torn tips, yellowing (material). Every leaf and stem carries a
'leaf' point attribute (x across -1..1, y base→tip) that mk_mats.leaf / stem read.
"""
import math, random
from mathutils import Vector, Matrix
from ti_core import S, mesh, tube, sphere, torus


def set_attr(o, name, fn):
    me = o.data
    at = me.attributes.get(name) or me.attributes.new(name, 'FLOAT_VECTOR', 'POINT')
    vals = []
    for v in me.vertices: vals.extend(fn(v.co))
    at.data.foreach_set('vector', vals)


def _frame(d):
    d = d.normalized()
    side = d.cross(Vector((0, 0, 1)))
    if side.length < 1e-3: side = Vector((1, 0, 0))
    side.normalize(); up = side.cross(d).normalized()
    return d, side, up


def leaf_blade(name, base, direction, length, width, mat, droop=.25, fold=.18, twist=0.0, holes=(), torn=0.0,
               teeth=9, group='Main', detail=0, rnd=None, res=(4, 18)):
    """Serrated lance leaf as a grid (res = quads across × along, default 4 × 18), solidified 1.2 mm. Faces whose (u, v) centre falls in a
    hole circle are left out, so the holes are real. torn > 0 shortens the tip unevenly."""
    rnd = rnd or random.Random(name)
    d, side, up = _frame(Vector(direction))
    if twist: side = Matrix.Rotation(twist, 3, d) @ side; up = Matrix.Rotation(twist, 3, d) @ up
    base = Vector(base); NU, NV = res
    vmax = 1.0 - torn
    verts, faces, uvs = [], [], []
    for j in range(NV + 1):
        v = vmax * j / NV
        w = width * math.sin(math.pi * min(.98, v) ** .78) ** .85
        tooth = abs(((v * teeth) % 1.0) - .5) * 2           # 1 at the tooth tip, 0 in the notch
        bend = -droop * v * v * length                        # leaves arch outwards and down
        for i in range(NU + 1):
            u = -1 + 2 * i / NU
            ww = w * (1 + .3 * tooth * (abs(u) ** 6) * (1 - v * .3))
            p = base + d * (v * length) + side * (u * ww) + up * (fold * abs(u) * ww + bend + .02 * length * math.sin(v * math.pi * 1.5))
            verts.append(tuple(p)); uvs.append((u, v))
    for j in range(NV):
        for i in range(NU):
            uc, vc = -1 + 2 * (i + .5) / NU, vmax * (j + .5) / NV
            if any((uc - hu) ** 2 / (hr * 2.2) ** 2 + (vc - hv) ** 2 / hr ** 2 < 1 for hu, hv, hr in holes): continue
            a = j * (NU + 1) + i
            faces.append((a, a + 1, a + NU + 2, a + NU + 1))
    used = sorted({i for f in faces for i in f}); remap = {old: new for new, old in enumerate(used)}
    verts = [verts[i] for i in used]; uvs = [uvs[i] for i in used]
    faces = [tuple(remap[i] for i in f) for f in faces]
    o = mesh(name, verts, faces, mat, smooth=True, solid=.0012, rim=False, grain=tuple(d), group=group, detail=detail)   # no 1.2 mm side strips: sub-texel, they baked dark
    # foliage normals: blend toward rays from a point below the leaf base, so the underside is lit like the top
    # (URP Lit has no translucency; plain flipped normals left every leaf underside near-black in Unity)
    ne = o.modifiers.new('FoliageNormals', 'NORMAL_EDIT'); ne.mode = 'RADIAL'
    ne.offset = tuple(base - Vector((0, 0, length * .8))); ne.mix_mode = 'COPY'; ne.mix_factor = .6
    me = o.data; at = me.attributes.new('leaf', 'FLOAT_VECTOR', 'POINT')
    at.data.foreach_set('vector', [c for u, v in uvs for c in (u, v, 0.0)])   # from_pydata keeps vertex order
    return o


def _stem_attr(o, z0, z1):
    set_attr(o, 'leaf', lambda co: (0, max(0., min(1., (co.z - z0) / max(z1 - z0, 1e-4))), 0))


def plant(prefix, at, height, grade, mats, seed, group='Main', lean=(0, 0), crown=True, soil=True, detail_leaf=0, leaf_res=(4, 18), roots=True):
    """One herb standing on its root tips at `at` (bottom of the roots). Returns the stem-top points."""
    rnd = random.Random(seed); at = Vector(at)
    root_len = height * .14; crown_z = at.z + root_len
    c = Vector((at.x, at.y, crown_z))
    # roots: wiry, kinked, fanning down from the crown
    for k in range((7 if grade != 'low' else 6) if roots else 0):
        a = k / 7 * math.tau + rnd.uniform(-.3, .3); spread = rnd.uniform(.012, .028)
        pts = [c]
        for s in range(1, 5):
            t = s / 4
            pts.append(c + Vector((math.cos(a) * spread * t + rnd.uniform(-.003, .003), math.sin(a) * spread * t + rnd.uniform(-.003, .003),
                                   -root_len * t * rnd.uniform(.85, 1.0))))
        tube(f'{prefix}_Root{k}', [tuple(p) for p in pts], .0016, mats['root'], radii=[1, .8, .6, .4, .2], res=4, grain='z', group=group, detail=2 if k > 3 else 1)
    if soil and roots:   # soil still on the roots
        for k in range(4):
            off = Vector((rnd.uniform(-.008, .008), rnd.uniform(-.008, .008), -root_len * rnd.uniform(.25, .6)))
            sphere(f'{prefix}_Soil{k}', tuple(c + off), rnd.uniform(.006, .01), mats['soil'],
                   scale=(1, rnd.uniform(.7, 1.1), rnd.uniform(.6, .9)), seg=10, ring=6, group=group, detail=1 if k < 2 else 2)
    tops = []
    lean = Vector((lean[0], lean[1], 0))
    nst = 3 if height > .2 else 2
    for s in range(nst):
        a = s / nst * math.tau + rnd.uniform(-.4, .4)
        sway = Vector((math.cos(a), math.sin(a), 0)) * rnd.uniform(.006, .016)
        h = height * rnd.uniform(.62, .78) - root_len
        pts = [c + Vector((0, 0, -.002))]
        for t in (.3, .6, 1.0):
            pts.append(c + sway * t * 1.6 + lean * t * h + Vector((0, 0, h * t)))
        o = tube(f'{prefix}_Stem{s}', [tuple(p) for p in pts], .0022, mats['stem'], radii=[1.15, 1, .85, .6], res=6, grain='z', group=group)
        _stem_attr(o, c.z, c.z + h)
        tops.append((pts, a))
    # leaves: alternate pairs up each stem, then a rising tuft at the top
    lmat = mats['leaf_' + grade]
    n = 0
    for pts, a in tops:
        for k, t in enumerate((.3, .45, .6, .75, .9)):
            p = pts[0].lerp(pts[-1], t)
            ang = a + (k % 2) * math.pi + rnd.uniform(-.5, .5)
            rise = .75 + t * .9 + rnd.uniform(-.15, .15)
            d = Vector((math.cos(ang), math.sin(ang), rise)) + lean * 2
            L = height * rnd.uniform(.34, .44) * (1.15 - t * .35); W = L * rnd.uniform(.11, .135)
            holes, torn = (), 0.0
            if grade == 'low':
                holes = tuple((rnd.uniform(-.55, .55), rnd.uniform(.3, .75), rnd.uniform(.07, .11)) for _ in range(rnd.choice((1, 1, 2))))
                torn = rnd.choice((0, 0, .08, .14))
            leaf_blade(f'{prefix}_Leaf{n}', p, d, L, W, lmat, droop=.12 + (1 - t) * .2, fold=.28, twist=rnd.uniform(-.3, .3),
                       holes=holes, torn=torn, group=group, detail=detail_leaf if k < 2 else 0, rnd=rnd, res=leaf_res)
            n += 1
        top = pts[-1]
        for k in range(2):   # rising tip pair
            ang = a + k * math.pi + rnd.uniform(-.3, .3)
            d = Vector((math.cos(ang) * .25, math.sin(ang) * .25, 1)) + lean
            L = height * rnd.uniform(.26, .32); W = L * .13
            holes = ((rnd.uniform(-.4, .4), .5, .09),) if grade == 'low' and k == 0 else ()
            leaf_blade(f'{prefix}_Tip{n}', top, d, L, W, lmat, droop=.1, fold=.22, holes=holes, group=group, rnd=rnd, res=leaf_res)
            n += 1
    return c


def bundle(prefix, at, length, grade, mats, seed, group='Main', plants=4, lean=(0, 0), leaf_res=(4, 18), roots=True):
    """Herbs gathered at the crown and tied with hemp twine just above the roots."""
    rnd = random.Random(seed); at = Vector(at)
    for k in range(plants):
        a = k / plants * math.tau + rnd.uniform(-.3, .3); r = .011 if k else 0
        p = at + Vector((math.cos(a) * r, math.sin(a) * r, rnd.uniform(0, .006)))
        lean_k = (lean[0] + math.cos(a) * .12, lean[1] + math.sin(a) * .12)
        plant(f'{prefix}_P{k}', p, length * rnd.uniform(.92, 1.0), grade, mats, seed * 31 + k, group, lean=lean_k, soil=k < 2, leaf_res=leaf_res, roots=roots)
    tz = at.z + length * .2
    for k in range(4):   # twine wraps, one diagonal and a knot with two tails
        torus(f'{prefix}_Twine{k}', (at.x, at.y, tz + k * .006), .021 - k * .0007, .0022, mats['twine'], rot=(rnd.uniform(-.06, .06), rnd.uniform(-.06, .06), 0),
              major=28, minor=6, grain='z', group=group)
    torus(f'{prefix}_TwineCross', (at.x, at.y, tz + .009), .021, .002, mats['twine'], rot=(.32, 0, .4), major=28, minor=6, grain='z', group=group, detail=1)
    k0 = Vector((at.x + .02, at.y - .006, tz + .012))
    sphere(f'{prefix}_TwineKnot', tuple(k0), .0045, mats['twine'], scale=(1, .8, .9), seg=10, ring=6, group=group)
    for s, (dx, dz) in enumerate(((.012, -.02), (.016, -.012))):
        tube(f'{prefix}_TwineTail{s}', [tuple(k0), tuple(k0 + Vector((dx * .5, -.004, dz * .5))), tuple(k0 + Vector((dx, -.006, dz)))],
             .0016, mats['twine'], radii=[1, .9, .6], res=4, group=group, detail=1)
