"""TE04 tea-picking props for the east-slope tea terraces (work pack B-48h, part 1 of 2026-11-07).

TE04_Basket  low wide-mouth picking basket, 0.5 m across and 0.4 m tall (AI three-view TE04/BASKET candidate-01).
             Unlike harvest-market-b MK04 (a tall rectangular back basket on stakes, a wooden base frame and shoulder straps)
             this one is round, low and open: a tapered herringbone split-bamboo wall, a doubled rim of two bamboo hoops
             lashed through the wall with hemp, a foot hoop, one stitched repair patch and a few fresh tea leaves.

Blender Z-up, 1 unit = 1 m, front -Y, origin at the bottom centre (z = 0 under the foot hoop).
The weave, bamboo and hemp shaders are mk_mats (shared with harvest-market-b), so the kits read as one village.
"""
import math, random
from mathutils import Vector, noise
from ti_core import S, surface, tube, socket, mesh
import mk_mats as mm
import cr_mats as cm
from cr_parts import set_attr_list, helix, sheet


def palette():
    P = {}
    # herringbone split bamboo: wide strips, a little green left in some, darker where hands hold the rim, grime at the foot
    P['weave'] = mm.weave('Picking_Weave', (.5, .28, .07), (.11, .058, .016), reed=WEAVE_REED, block=WEAVE_BLOCK, green_cast=.25, sweat=.35, ground_h=.085,
                           wobble=.007, strip_var=.46)
    P['weave_patch'] = mm.weave('Repair_Weave', (.34, .25, .12), (.12, .085, .042), reed=.009, block=.034, green_cast=.08)
    P['hoop'] = mm.bamboo('Rim_Bamboo', green=(.12, .1, .03), straw=(.42, .24, .07))
    P['hoop_old'] = mm.bamboo('Foot_Bamboo', green=(.09, .08, .035), straw=(.3, .19, .08), ground_h=.035)
    P['hemp'] = mm.hemp('Lashing_Hemp', (.19, .125, .055), twist=200.0)
    P['twine'] = mm.hemp('Patch_Twine', (.13, .085, .04), twist=260.0)
    P['leaf'] = cm.weed_leaf('Fresh_Tea_Leaf', (.018, .04, .01), (.055, .1, .022), (.12, .17, .04))   # deep glossy tea green, lighter young tip
    return P


# ------------------------------------------------------------------ basket shape
Z_FOOT = .014              # foot hoop centre; its tube radius equals this, so the basket stands on z = 0
Z_BOT, Z_TOP = .024, .372  # woven wall from the floor to the rim
R_BOT, R_TOP = .182, .228  # wall radius at floor and rim
OVAL = .965                # a hand-made basket is never quite round: slightly narrower front to back
RIM_Z = .379               # centre line of the two rim hoops
N_LASH_RIM, N_LASH_FOOT = 12, 9
WEAVE_REED, WEAVE_BLOCK = .0125, .05   # strip width and block length (4 strips per block)
DENT_A, DENT_D = .45, .011             # hip dent: angle (rad, 0 = +X) and depth (m)
N_BLOCKS = 18                          # weave blocks per turn round the wall along each diagonal (wall reads at about 0.2 m radius)


def wall_r(t, a=0.):
    """Radius of the woven wall at height fraction t (0 floor, 1 rim): flared, a soft belly, small hand-made wobble."""
    r = R_BOT + (R_TOP - R_BOT) * t ** .8 + .006 * math.sin(math.pi * t)
    r += .0045 * noise.noise(Vector((math.cos(a) * 1.3, math.sin(a) * 1.3, t * 1.7 + 4.)))
    # a shallow dent on the right-back side where the basket rides against the picker's hip
    da = math.atan2(math.sin(a - DENT_A), math.cos(a - DENT_A))
    r -= DENT_D * math.exp(-(da / .38) ** 2 - ((t - .48) / .24) ** 2)
    return r


def ring(a, r, z):
    return (r * math.cos(a), r * math.sin(a) * OVAL, z)


def wuv(o, fn):
    """Per-vertex weave coordinates (metres) for mk_mats.weave."""
    set_attr_list(o, 'wuv', [(*fn(v.co), 0.) for v in o.data.vertices])


def te04_basket(P):
    R = random.Random(401)
    # woven wall, solidified inward-and-outward so the rim shows a real edge
    def body(u, v):
        a = u * math.tau; z = Z_BOT + v * (Z_TOP - Z_BOT)
        return ring(a, wall_r(v, a), z)
    w = surface('Basket_Wall', 64, 10, body, P['weave'], closed_u=True, solid=.006, grain='z')
    # the weave coordinates are turned 45 degrees, so the strips run on the diagonal and the blocks alternate into a herringbone, as in the reference.
    # They are stored per face corner and unwrapped round each face's centre angle, and the scale makes one turn round the basket an exact whole
    # number of weave blocks along both diagonals, so the pattern closes on itself with no seam where the angle wraps from +pi to -pi.
    k = N_BLOCKS * WEAVE_BLOCK * math.sqrt(2) / math.tau
    diag = lambda s, z: ((s + z) * .7071, (s - z) * .7071)
    me = w.data; at = me.attributes.new('wuv', 'FLOAT_VECTOR', 'CORNER'); vals = []
    for p in me.polygons:
        c = p.center; ac = math.atan2(c.y / OVAL, c.x)
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            a = ac + (math.atan2(co.y / OVAL, co.x) - ac + math.pi) % math.tau - math.pi
            vals.extend((*diag(a * k, co.z), 0.))
    at.data.foreach_set('vector', vals)
    # floor: the same weave, flat, sitting a little above the foot hoop
    def floor(u, v):
        a = u * math.tau; r = wall_r(0., a) * v
        return ring(a, r, Z_BOT + .002 - .006 * (1 - v) ** 2)   # sags a touch in the middle from years of loads
    # one centre vertex and a triangle fan (a collapsed grid row would leave zero-area and overlapping faces at the centre)
    NU, NV = 40, 3
    fv = [floor(0., 0.)] + [floor(i / NU, j / NV) for j in range(1, NV + 1) for i in range(NU)]
    ff = [(0, 1 + (i + 1) % NU, 1 + i) for i in range(NU)]   # same winding as the old grid: floor faces up
    ff += [(1 + (j - 1) * NU + i, 1 + (j - 1) * NU + (i + 1) % NU, 1 + j * NU + (i + 1) % NU, 1 + j * NU + i) for j in range(1, NV) for i in range(NU)]
    f = mesh('Basket_Floor', fv, ff, P['weave'], smooth=True, solid=.005, grain='z')
    wuv(f, lambda co: diag(co.x, co.y))
    # lashing positions, a little uneven; the hoops are spliced from split-bamboo lengths whose joints hide under every other lashing
    rim_at = [(k + .5 + R.uniform(-.12, .12)) / N_LASH_RIM * math.tau for k in range(N_LASH_RIM)]
    foot_at = [(k + R.uniform(-.15, .15)) / N_LASH_FOOT * math.tau for k in range(N_LASH_FOOT)]
    # foot hoop: thick old bamboo the basket stands on, three lengths
    rf = wall_r(0.) + .004
    hoop('Foot_Hoop', foot_at[::3], rf, Z_FOOT, Z_FOOT, P['hoop_old'], res=4)
    # rim: an outer and an inner hoop clamp the top of the wall, six lengths each, the inner joints offset from the outer
    rt = wall_r(1.)
    hoop('Rim_Outer', rim_at[::2], rt + .011, RIM_Z, .0115, P['hoop'], res=6)
    hoop('Rim_Inner', rim_at[1::2], rt - .009, RIM_Z - .002, .0085, P['hoop'], res=4)
    # hemp lashings through the wall, pulled tight round both rim hoops and round the foot hoop
    for a in rim_at:
        wrap('Rim_Lash', a, rt + .0025, RIM_Z, .0185, .0100, .024, .0021, P['hemp'], turns=3)   # bedded 1.5 mm into the hoops: a cord resting on the surface would z-fight
    for a in foot_at:
        wrap('Foot_Lash', a, rf - .004, Z_FOOT + .004, .018, .0145, .018, .0019, P['hemp'], turns=2)
    repair_patch(P, R)
    loose_leaves(P, R)
    # collision: a 12-sided frustum around the wall, foot to rim
    verts, faces = [], []
    for z, r in ((0., rf + .014), (RIM_Z + .012, rt + .023)):
        verts += [ring(k / 12 * math.tau, r, z) for k in range(12)]
    faces = [(k, (k + 1) % 12, 12 + (k + 1) % 12, 12 + k) for k in range(12)] + [tuple(range(11, -1, -1)), tuple(range(12, 24))]
    S['collision_mesh'] = (verts, faces)
    S['prop'] = dict(kind='basket', rim_top=RIM_Z + .0115, rim_outer_r=rt + .0225, foot_r=rf)


def hoop(name, joints, r, z, rad, mat, res, step=math.radians(5)):
    """A ring of split-bamboo lengths butted at the given joint angles. Each length is its own part with its grain along its chord,
    so the bamboo shader's streaks and node rings run round the hoop (one closed ring can only carry one grain axis)."""
    js = sorted(a % math.tau for a in joints)
    for i, a0 in enumerate(js):
        a1 = js[(i + 1) % len(js)] + (math.tau if i == len(js) - 1 else 0.)
        gap = .001 / r   # 2 mm butt gap at each splice (hidden under the lashing); touching end caps would z-fight
        a0g, a1g = a0 + gap, a1 - gap
        n = max(2, int((a1g - a0g) / step))
        pts = [ring(a0g + (a1g - a0g) * k / n, r, z) for k in range(n + 1)]
        mid = (a0 + a1) / 2; chord = Vector((-math.sin(mid), math.cos(mid) * OVAL, 0)).normalized()
        tube(name, pts, rad, mat, res=res, grain=tuple(chord))


def wrap(name, a, rc, zc, rx, rz, span, r, mat, turns, per_turn=7):
    """Hemp binding pulled tight round a hoop section: an elliptical helix (rx across the wall, rz up) that runs along the rim
    tangent at angle a. A light tube, since cr_parts.lash sweeps a 9-lobe cord, far too heavy for a 0.5 m prop."""
    c = Vector(ring(a, rc, zc)); t = Vector((-math.sin(a), math.cos(a) * OVAL, 0)).normalized()
    n = Vector((math.cos(a), math.sin(a) / OVAL, 0)).normalized(); up = Vector((0, 0, 1))
    m = int(turns * per_turn); pts = []
    for i in range(m + 1):
        s = i / m; ang = s * turns * math.tau
        pts.append(tuple(c + t * (span * (s - .5)) + n * ((rx + r) * math.cos(ang)) + up * ((rz + r) * math.sin(ang))))
    return tube(name, pts, r, mat, res=2, grain=tuple(t), detail=1)


def repair_patch(P, R):
    """A square of newer, greyer weave sewn over a hole on the front-left, with twine cross-stitches at the corners and edges."""
    a0, half_a = -math.pi / 2 - .62, .26          # centre angle (front-left) and half width in radians
    z0, z1 = .15, .255
    def patch(u, v):
        a = a0 + (u - .5) * 2 * half_a; t = (z0 + v * (z1 - z0) - Z_BOT) / (Z_TOP - Z_BOT)
        bulge = .0025 * math.sin(math.pi * u) * math.sin(math.pi * v)
        return ring(a, wall_r(t, a) + .0032 + bulge, z0 + v * (z1 - z0))
    p = surface('Repair_Patch', 10, 7, patch, P['weave_patch'], solid=.002, grain='z')
    wuv(p, lambda co: (math.atan2(co.y / OVAL, co.x) * .2 + .37, co.z + .41))
    # cross-stitches: two short twine strands per stitch, crossing over the patch edge
    marks = [(0, 0), (1, 0), (0, 1), (1, 1), (.5, 0), (.5, 1), (0, .5), (1, .5)]
    for u, v in marks:
        c = Vector(patch(u, v)); out = Vector((c.x, c.y / OVAL, 0)).normalized()
        up = Vector((0, 0, 1)); side = out.cross(up).normalized()
        for s in (1, -1):
            d = (side * s + up) * .0085
            pts = [tuple(c - d + out * .002), tuple(c + out * .0045), tuple(c + d + out * .002)]
            tube('Patch_Stitch', pts, .0016, P['twine'], res=4, grain=tuple(d.normalized()), detail=1)


def leaf(name, base, direction, L, W, curl, mat, roll=0.):
    """One fresh tea leaf: pointed oval blade, slight serration wobble, curled along its length; 'cuv' for the leaf shader."""
    d = Vector(direction).normalized(); up = Vector((0, 0, 1))
    side = d.cross(up)
    if side.length < 1e-3: side = Vector((1, 0, 0))
    side.normalize(); nrm = side.cross(d).normalized()
    side = side * math.cos(roll) + nrm * math.sin(roll); nrm = side.cross(d).normalized()
    b = Vector(base)
    def fn(u, v):
        # small teeth along the edge; never quite zero wide at the stalk and tip, so no row of the grid collapses onto one point
        w = W * (math.sin(math.pi * min(1., v * 1.04)) ** .75 + .035) * (1 + .06 * math.sin(v * 40))
        x = (u - .5) * 2
        lift = curl * (v * v) * L + .12 * W * x * x                                             # tip curls up, the blade cups
        return tuple(b + d * (L * v) + side * (x * w) + nrm * lift)
    return sheet(name, 3, 6, fn, mat, solid=.0008, detail=2, grain=tuple(d), group='Main')


def loose_leaves(P, R):
    """A few just-picked leaves on the floor of the basket and two caught on the rim; they export as Detail_Small."""
    # floor leaves lie flat on the floor (1.2 mm above its top face) and are spread so no two overlap: two flat leaves
    # crossing at the same height would z-fight, and stacking them in steps left the upper ones floating
    mids = []
    for _ in range(400):
        if len(mids) == 9: break
        a = R.uniform(0, math.tau); r = R.uniform(.02, .13); ang = R.uniform(0, math.tau); L = R.uniform(.045, .065)
        d = Vector((math.cos(ang), math.sin(ang), 0.))
        mid = Vector(ring(a, r, 0.)) + d * (L / 2)
        if mid.xy.length > wall_r(0.) - .035 or any((mid - m).length < .052 for m in mids): continue
        mids.append(mid)
        v = r / wall_r(0., a)   # floor top face: the sagging centre surface plus half the 5 mm floor thickness
        base = Vector(ring(a, r, Z_BOT + .002 - .006 * (1 - v) ** 2 + .0025 + .0012))
        leaf('Tea_Leaf', base, d, L, R.uniform(.012, .017), R.uniform(.1, .3), P['leaf'], roll=R.uniform(-.12, .12))
    for a, tilt in ((-math.pi / 2 + .35, -.55), (math.pi / 2 - .9, -.4)):
        rt = wall_r(1.); base = Vector(ring(a, rt - .016, RIM_Z + .004))
        out = Vector((math.cos(a), math.sin(a) * OVAL, tilt)).normalized()
        leaf('Tea_Leaf_Rim', base, out, .058, .016, .25, P['leaf'], roll=.3)
    # a small fresh handful left leaning against the back wall: tips just show above the rim from the front, as in the reference
    for k in range(6):
        a = math.pi / 2 + R.uniform(-.6, .6); rt = wall_r(1.)
        base = Vector(ring(a, rt - .033 - .0055 * k, RIM_Z - R.uniform(.03, .05)))   # stepped inward so no two leaves share a plane
        ang = a + R.uniform(-.7, .7)                     # leaning back over the rim, not standing up like sprouts
        d = (math.cos(ang) * .8, math.sin(ang) * .8, R.uniform(.35, .6))
        leaf('Tea_Leaf_Top', base, d, R.uniform(.06, .075), R.uniform(.015, .019), R.uniform(.15, .3), P['leaf'], roll=R.uniform(-.6, .6))
