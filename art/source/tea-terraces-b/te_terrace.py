"""TE01 east-slope tea terraces: six dry-stone terrace modules sharing one wall builder.

Every piece is built in a flat parameter space and then bent onto its footprint:
  s  distance along the wall (0 at the left connector as seen from the front, L at the right one)
  d  distance behind the front edge of the footprint (0 front, DEPTH = 4 m back)
  z  height (0 = the lower terrace's soil, 1.0 = this terrace's soil)
MAP[kind](s, d) -> (x, y). Straight pieces translate; the bends wrap s round a quarter circle, so the
connector cross-sections of every piece are identical and land on whole metres.
Front faces -Y (Blender). Origin: footprint centre on the 1 m grid, z = 0 at the lower terrace.
"""
import bpy, math, random
from mathutils import Vector, Matrix, noise
from ti_core import S, mesh, surface, socket
import ti_mats as tm
import mk_mats as mm
import cr_mats as cm
from cr_parts import rbox, sheet, log, tuft

DEPTH = 4.0          # tread depth, front edge to back edge
RISE = 1.0           # soil to soil: every TE01 piece steps up exactly 1 m
FACE0 = .07          # wall face foot behind the footprint front edge
BATTER = .12         # the face leans back 12 cm per metre (about 7 degrees)
FOOT_T = .24         # foot course height
COP_T = .17          # coping slab thickness; slab top sits 1-3 cm above the soil
GAP = .009           # dry joint between stones

R_OUT, R_IN = 8.0, 4.0   # bend radii of the wall face: outer bend (spur) 8 m, inner bend (cove) 4 m

GREY_OCHRE = (.25, .225, .175)


# ------------------------------------------------------------------ footprint maps
def map_straight(L):
    return lambda s, d: (s - L / 2, -2. + d)

def map_outer(s, d):
    """Convex bend round a spur: wall on radius 8, tread inward to radius 4. Enters heading +X (front -Y), leaves heading +Y (front +X)."""
    a = -math.pi / 2 + s / R_OUT; r = R_OUT - d
    return (r * math.cos(a) - 4., r * math.sin(a) + 4.)

def map_inner(s, d):
    """Concave bend round a cove: wall on radius 4 facing the centre, tread outward to radius 8. Enters heading +X (front -Y), leaves heading -Y (front -X)."""
    a = math.pi / 2 - s / R_IN; r = R_IN + d
    return (r * math.cos(a) - 4., r * math.sin(a) - 4.)


def smooth(t):
    t = max(0., min(1., t)); return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ palette
def stone_set(name, n=4, **kw):
    light = kw.pop('light', (.33, .31, .27)); dark = kw.pop('dark', (.16, .15, .125))
    shade = [(1., 1., 1.), (.76, .75, .74), (1.12, 1.01, .84), (.88, .93, .98)]
    return [cm.stone(f'{name}_{i}', light=tuple(c * f for c, f in zip(light, shade[i])), dark=tuple(c * f for c, f in zip(dark, shade[i])), **kw) for i in range(n)]


JOINT_SOIL = (.07, .047, .026)   # the soil pattern's average colour, used on every joint line
JOINT_FADE = .35


def joint_fade(o, L):
    """Write joint_fade on a mesh built in (s, d, z) piece coordinates: 1 at s = 0 and s = L, 0 from JOINT_FADE inward."""
    me = o.data; vals = []
    for v in me.vertices:
        e = min(v.co.x, L - v.co.x); t = max(0., min(1., 1 - e / JOINT_FADE)); vals.append(t * t * (3 - 2 * t))
    at = me.attributes.new('joint_fade', 'FLOAT', 'POINT'); at.data.foreach_set('value', vals)
    return o


def tread_soil(name, dark=(.04, .026, .015), light=(.112, .072, .04), slot='Main'):
    """Tended tea-field soil: warm brown, crumbly clods, darker damp patches, a scatter of fine stubble and old leaf litter, paler where feet pass along the rows."""
    m, g = tm._new(name, slot)
    P = g.geo('Position'); sep = g.node('ShaderNodeSeparateXYZ'); g.link(P, sep.inputs[0])
    big = g.noise(P, 1.6, 4, .55); mid = g.noise(P, 6.0, 4, .58); fine = g.noise(P, 38.0, 4, .6); grit = g.noise(P, 140.0, 2, .5)
    t = g.math('ADD', g.math('MULTIPLY', big, .45), g.math('ADD', g.math('MULTIPLY', mid, .35), g.math('MULTIPLY', fine, .2)))
    col = g.ramp(t, [(.3, dark), (.5, tuple((a + b) / 2 for a, b in zip(dark, light))), (.72, light)])
    clod = g.noise(P, 17.0, 3, .62)
    col = g.mix(g.math('MULTIPLY', g.maprange(clod, .44, .62), .3), col, tuple(min(1, c * 1.3) for c in light))
    col = g.mix(g.math('MULTIPLY', g.maprange(clod, .38, .28), .55), col, tuple(c * .55 for c in dark))
    damp = g.maprange(g.noise(P, 2.3, 3, .5), .52, .66)
    col = g.mix(g.math('MULTIPLY', damp, .5), col, tuple(c * .7 for c in dark))
    stub = g.math('MULTIPLY', g.maprange(g.noise(P, 95.0, 2, .5), .66, .72), g.maprange(g.noise(P, 3.0, 2, .5), .45, .62))
    col = g.mix(g.math('MULTIPLY', stub, .75), col, (.1, .12, .035))
    litter = g.math('MULTIPLY', g.maprange(g.noise(P, 60.0, 2, .5), .69, .74), .7)
    col = g.mix(litter, col, (.045, .03, .016))
    # drifts of fallen tea leaves and prunings: olive-brown flecks gathered in broad patches
    drift = g.maprange(g.noise(P, .9, 3, .5), .5, .64)
    fleck = g.maprange(g.noise(P, 48.0, 2, .5), .6, .66)
    col = g.mix(g.math('MULTIPLY', g.math('MULTIPLY', drift, fleck), .8), col, (.07, .062, .025))
    col = g.mix(g.math('MULTIPLY', drift, .25), col, (.03, .022, .012))
    grain = g.maprange(grit, .62, .7)
    col = g.mix(g.math('MULTIPLY', grain, .25), col, (.2, .17, .13))
    # piece joints: the vertex attribute joint_fade (1 on a joint line, 0 from 0.35 m in) blends the pattern to one flat colour,
    # so two neighbouring pieces meet with the same soil colour whatever their own noise does there
    jf = g.node('ShaderNodeAttribute'); jf.attribute_name = 'joint_fade'; jfac = jf.outputs['Fac']
    col = g.mix(jfac, col, JOINT_SOIL)
    ao = g.ao(.05)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.5, .46, .42)), (1, (1, 1, 1))]))
    h = g.math('ADD', g.math('MULTIPLY', clod, 1.6), g.math('ADD', g.math('MULTIPLY', fine, .6), g.math('MULTIPLY', grit, .3)))
    h = g.math('MULTIPLY', h, g.math('SUBTRACT', 1., jfac))
    tm._finish(g, col, g.maprange(damp, 0., 1., .9, .8), 0.0, g.bump(h, .55, .012), spec=.3)
    return m


def palette():
    P = {}
    P['wall'] = stone_set('Wall_Fieldstone', 4, light=(.29, .265, .225), dark=(.12, .108, .088), ochre=(.27, .22, .15), moss=1.0, lichen=.5, crack=.55)
    P['cope'] = stone_set('Coping_Slab', 3, light=(.31, .29, .25), dark=(.13, .12, .1), ochre=(.27, .23, .16), moss=.7, lichen=.45, crack=.45)
    P['fresh'] = stone_set('Repair_Stone', 2, light=(.42, .395, .345), dark=(.2, .19, .16), ochre=(.3, .27, .21), moss=.08, lichen=.04, crack=.3)
    P['wet'] = cm.stone('Runoff_Stone', light=(.25, .235, .2), dark=(.1, .095, .08), ochre=(.16, .17, .11), moss=1.0, lichen=.1, crack=.4)
    P['joint'] = cm.packed_earth('Joint_Earth', dark=(.03, .021, .013), light=(.075, .052, .032), wet_top=-1., wet_low=-2., dry_low=5., dry_top=6.)
    P['soil'] = tread_soil('Tread_Soil')
    P['grass'] = cm.weed_leaf('Grass_Blade', (.04, .062, .018), (.15, .19, .045), (.3, .29, .085))
    P['dry_grass'] = cm.weed_leaf('Grass_Dry', (.07, .07, .025), (.2, .18, .065), (.33, .27, .11))
    P['moss'] = cm.moss_tuft('Moss_Soft', soft=True)
    P['fern'] = cm.fern('Fern_Green')
    P['stake'] = cm.wood('Stake_Wood', (.05, .03, .016), (.17, .105, .055), ground_h=.12, grey=.45)
    P['withy'] = cm.wood('Withy', (.07, .045, .022), (.2, .13, .065), ground_h=0, grey=.2)
    return P


# ------------------------------------------------------------------ terrace heights
class Terrace:
    """Height rules of one piece: Hw(s) wall height (coping top), top(s, d) soil top, slump for the broken bank."""
    def __init__(self, L, kind, rng, hw=None, slump=None, path_dip=None):
        self.L, self.kind, self.R = L, kind, rng
        self._hw = hw or (lambda s: RISE)
        self.slump = slump            # (s) -> how far the bank sank at the front, metres
        self.path_dip = path_dip      # (s, d) -> runoff groove depth
        self.seed = rng.uniform(0, 100)

    def Hw(self, s): return self._hw(min(max(s, 0.), self.L))

    def top(self, s, d):
        h = self.Hw(s)
        fade = smooth(min(s, self.L - s) / .45) * smooth((DEPTH - d) / .45) * smooth((d - .55) / .4)
        v = Vector((s * .8 + self.seed, d * .8, self.seed))
        bump = .013 * noise.noise(v) + .006 * noise.noise(v * 2.7)
        z = h + bump * fade * min(1., h / RISE)
        if self.slump:
            k = self.slump(s)
            if k > 0: z -= k * (1 - smooth((d - .25) / 1.45))
        if self.path_dip: z -= self.path_dip(s, d)
        return max(z, 0.)

    def cop_bot(self, s): return self.Hw(s) - COP_T

    def face_d(self, z): return FACE0 + BATTER * z


# ------------------------------------------------------------------ geometry builders
def soil_body(T, P, ds=.2, dd=.2, nf=7):
    """Closed soil mass: battered front face behind the stones (joint earth), the tread (soil), the cut ends and back."""
    L = T.L; ns = max(4, int(round(L / ds))); dmin = T.face_d(0) + .15
    d_top = [dmin + (DEPTH - dmin) * k / max(1, int(round((DEPTH - dmin) / dd))) for k in range(int(round((DEPTH - dmin) / dd)) + 1)]
    rings, mats = [], []
    for i in range(ns + 1):
        s = L * i / ns; top_front = T.top(s, dmin + .25)
        prof = []
        for k in range(nf):
            z = top_front * k / nf
            prof.append((dmin + BATTER * min(z, max(0., T.cop_bot(s) - .02)), z))
        zb = max(0., T.cop_bot(s) - .02)
        dfront = dmin + BATTER * min(top_front, zb)
        for k, d in enumerate(d_top):
            dd_ = dfront + (DEPTH - dfront) * k / (len(d_top) - 1)
            prof.append((dd_, T.top(s, dd_)))
        prof.append((DEPTH, 0.)); prof.append((dmin + (DEPTH - dmin) * .5, 0.))
        rings.append([(s, d, z) for d, z in prof])
    n = len(rings[0]); verts = [v for r in rings for v in r]; faces = []; fmat = []
    for i in range(ns):
        for k in range(n):
            a = i * n + k; b = i * n + (k + 1) % n
            faces.append((a, b, b + n, a + n))
            fmat.append(0 if k < nf else 1 if k < nf + len(d_top) - 1 else 2)
    for i in (0, ns):
        c = len(verts); r = rings[i]
        verts.append((r[0][0], sum(p[1] for p in r) / n, sum(p[2] for p in r) / n))
        for k in range(n):
            f = (c, i * n + k, i * n + (k + 1) % n)
            faces.append(f if i == ns else f[::-1]); fmat.append(2)
    o = mesh('Soil_Body', verts, faces, P['joint'], grain='y', detail=0)
    o.data.materials.append(P['soil'])
    for p, m in zip(o.data.polygons, fmat): p.material_index = 1 if m == 1 else 0
    for p in o.data.polygons: p.use_smooth = True
    return joint_fade(o, L)


def toe(T, P, ds=.25):
    """Soil lip in front of the foot course: starts at the footprint front edge at z = 0, so the lower tread runs on into it."""
    L = T.L; ns = max(4, int(round(L / ds))); R = random.Random(int(T.seed * 10))
    def fn(u, v):
        s = L * u; prof = [(0., 0.), (.035, .022), (FACE0 + .02, .04), (FACE0 + .2, .03)]
        t = v * (len(prof) - 1); k = min(int(t), len(prof) - 2); f = t - k
        d = prof[k][0] * (1 - f) + prof[k + 1][0] * f; z = prof[k][1] * (1 - f) + prof[k + 1][1] * f
        edge = smooth(min(s, L - s) / .3)
        if 0 < v < 1: z += .008 * noise.noise(Vector((s * 3, v * 2, T.seed))) * edge
        return (s, d, z * min(1., T.Hw(s) / .3 + .2))
    return joint_fade(surface('Toe_Soil', ns, 6, fn, P['soil'], solid=.012, grain='x', detail=0), L)


def stone(T, P, name, s0, s1, z0, z1, d0, depth, mat, r=.06, amp=.012, chips=2, hew=0, seed=0, clamp=None, flat='', detail=0, div=.075, lean=True, tilt=0., roundness=.3, taper=None, skew=None):
    """One wall stone filling [s0,s1] x [z0,z1], face at d0. clamp(s) -> highest z a vertex may reach (sloping coping, breach).
    roundness caps the edge radius as a share of the smaller face side: .3 dressed, .45 a water-worn fieldstone."""
    w, h = s1 - s0, z1 - z0
    if w < .05 or h < .045: return None
    sc, zc = (s0 + s1) / 2, (z0 + z1) / 2; dc = d0 + depth / 2
    warp = None
    if clamp is not None:
        def warp(q, sc=sc, zc=zc):
            lim = clamp(sc + q.x) - zc
            if q.z > lim: q.z = lim
    rot = (-math.atan(BATTER) if lean else 0., tilt, 0.)
    return rbox(name, (sc, dc, zc), (w, depth, h), mat, r=min(r, w * roundness, h * roundness), amp=amp, freq=3.2 / max(min(w, h), .1), chips=chips, hew=hew,
                seed=seed, div=div, rot=rot, warp=warp, flat=flat, grain='x', detail=detail, taper=taper, skew=skew)


def end_flat(s0, s1, L):
    return ('x' if s0 <= 1e-6 else '') + ('X' if s1 >= L - 1e-6 else '')


def course_fill(T, P, s_a, s_b, z0, z1, wmin, wmax, mats, R, name='Wall_Stone', bulge=.012, r=.07, hew=0, clampfn=None, chink=True, occupied=(), recess=0., rubble=False, roundness=.3):
    """Fill one course between s_a and s_b with stones of random width; skips spans taken by bigger stones.
    rubble: each stone takes 62-100 % of the course height, sits on the bed, leans a little, and a thin shim stone fills a tall gap above it."""
    L = T.L; joints = []
    s = s_a
    while s < s_b - .04:
        blocked = next(((a, b) for a, b, za, zb in occupied if a - GAP < s + .05 and b + GAP > s and za < z1 - .02 and zb > z0 + .02), None)
        if blocked:
            s = blocked[1] + GAP; continue
        nxt = min([a for a, b, za, zb in occupied if a > s and za < z1 - .02 and zb > z0 + .02] + [s_b])
        w = R.uniform(wmin, wmax)
        if nxt - s - w < wmin * .6: w = nxt - s
        w = min(w, nxt - s)
        if rubble:
            h = (z1 - z0) * R.choice((R.uniform(.62, .8), R.uniform(.82, 1.), R.uniform(.9, 1.)))
            top = z0 + h
        else:
            top = z1 - R.uniform(0, .035) * (z1 - z0)
        d0 = T.face_d(z0) + R.uniform(-.014, .014) + recess
        tilt = R.uniform(-.07, .07) if rubble else R.uniform(-.012, .012)
        stone(T, P, name, s + GAP / 2, s + w - GAP / 2, z0 + GAP / 2, top - GAP / 2, d0, R.uniform(.34, .5), R.choice(mats), r=r, amp=bulge, chips=R.randint(1, 3), hew=hew,
              seed=R.randint(1, 9999), clamp=clampfn, flat=end_flat(s, s + w, L), tilt=tilt, roundness=roundness,
              taper=(R.uniform(.84, 1.04), 1.) if rubble else None, skew=(R.uniform(-.035, .035), 0.) if rubble else None)
        if rubble and z1 - top > .07 and w > .16:
            # shim: one or two flat stones packed into the gap above
            sw = w * R.uniform(.45, .8); so = s + R.uniform(0, w - sw)
            stone(T, P, 'Shim_Stone', so + GAP / 2, so + sw - GAP / 2, top + GAP / 2, z1 - GAP / 2, T.face_d(top) + .008, R.uniform(.25, .35), R.choice(mats), r=.03, amp=.006,
                  chips=1, seed=R.randint(1, 9999), clamp=clampfn, detail=1, div=.05, tilt=R.uniform(-.05, .05), flat=end_flat(so, so + sw, L))
        s += w
        if s < s_b - .05: joints.append((s, z0, z1))
    if chink:
        for js, za, zb in joints:
            if R.random() < .6:
                zz = R.uniform(za + .03, zb - .06); sz = R.uniform(.05, .1)
                if clampfn and zz + sz > clampfn(js) - .02: continue
                stone(T, P, 'Chink_Stone', js - sz / 2, js + sz / 2, zz, zz + sz * R.uniform(.6, .9), T.face_d(zz) + .02, .18, R.choice(mats), r=.02, amp=.004,
                      chips=1, seed=R.randint(1, 9999), detail=1, div=.035, tilt=R.uniform(-.3, .3))
    return joints


def coping(T, P, R, s_a=0., s_b=None, skip=(), mats=None, min_h=.36):
    """Dressed cap slabs: top 1-3 cm above the soil, slight overhang, following Hw(s) when it slopes."""
    L = T.L; s_b = L if s_b is None else s_b; s = s_a; mats = mats or P['cope']
    while s < s_b - .03:
        w = R.choice((R.uniform(.32, .55), R.uniform(.5, .85)))
        if s_b - s - w < .25: w = s_b - s
        sc = s + w / 2
        if any(a < sc < b for a, b in skip) or T.Hw(sc) < min_h:
            s += w; continue
        hc = T.Hw(sc); lift = R.uniform(-.004, .03)
        z0 = hc - COP_T - R.uniform(0, .04); z1 = hc + lift; d0 = T.face_d(z0) - R.uniform(.01, .045)
        def warp(q, sc=sc, hc=hc):
            q.z += T.Hw(sc + q.x) - hc
        dep = R.uniform(.4, .56)
        rbox('Coping_Slab', (sc, d0 + dep / 2, (z0 + z1) / 2), (w - GAP * 1.5, dep, z1 - z0), R.choice(mats), r=R.uniform(.03, .06), amp=.012, freq=3., chips=R.randint(1, 3),
             hew=2, seed=R.randint(1, 9999), div=.08, rot=(R.uniform(-.03, .02), R.uniform(-.025, .025), R.uniform(-.03, .03) if 0 < s and s + w < L else 0), warp=warp,
             flat=end_flat(s, s + w, L), grain='x', taper=(R.uniform(.9, 1.), R.uniform(.92, 1.)))
        s += w


def foot_course(T, P, R, mats=None, s_a=0., s_b=None, skip=(), clampfn=None):
    mats = mats or P['wall']; L = T.L; s_b = L if s_b is None else s_b
    s = s_a
    while s < s_b - .03:
        w = R.uniform(.38, .95)
        if s_b - s - w < .3: w = s_b - s
        if any(a < s + w / 2 < b for a, b in skip):
            s += w; continue
        h = FOOT_T - R.uniform(0, .05)
        stone(T, P, 'Foot_Stone', s + GAP / 2, s + w - GAP / 2, 0., h, T.face_d(0) - .02 + R.uniform(-.015, .01), R.uniform(.42, .55), R.choice(mats), r=.1, amp=.02,
              chips=R.randint(1, 3), seed=R.randint(1, 9999), clamp=clampfn, flat=end_flat(s, s + w, L) + 'z', roundness=.36, tilt=R.uniform(-.03, .03), taper=(R.uniform(.88, 1.), 1.))
        s += w


def boulders(T, R, s_a, s_b, z0, z1, n, wr=(.55, .92), keep_out=()):
    out = []
    for _ in range(n * 12):
        if len(out) >= n: break
        w = R.uniform(*wr); h = R.uniform(max(.3, (z1 - z0) * .72), z1 - z0)
        sc = R.uniform(s_a + w / 2 + .15, s_b - w / 2 - .15)
        a, b = sc - w / 2, sc + w / 2
        if any(a < bb + .35 and b > aa - .35 for aa, bb, _, _ in out): continue
        if any(a < bb + .1 and b > aa - .1 for aa, bb in keep_out): continue
        za = z0 + R.uniform(0, (z1 - z0) - h)
        out.append((a, b, za, za + h))
    return out


def place_boulders(T, P, R, bs, mats, clampfn=None):
    for a, b, za, zb in bs:
        stone(T, P, 'Boulder', a + GAP / 2, b - GAP / 2, za + GAP / 2, zb - GAP / 2, T.face_d((za + zb) / 2) - .03 - BATTER * (zb - za) / 2 + R.uniform(-.01, .015), R.uniform(.45, .6),
              R.choice(mats), r=.4, amp=.028, chips=R.randint(0, 2), seed=R.randint(1, 9999), div=.07, clamp=clampfn, roundness=.47, tilt=R.uniform(-.08, .08), taper=(R.uniform(.85, 1.), 1.))


def irregular_wall(T, P, R, s_a=0., s_b=None, n_boulders=None, keep_out=(), mats=None, clampfn=None, small_zone=None):
    """Fieldstone wall: big rounded boulders, rubble courses round them whose bed line wanders every metre or two, shims and chinks in the joints."""
    L = T.L; s_b = L if s_b is None else s_b; mats = mats or P['wall']
    za, zb = FOOT_T, T.cop_bot((s_a + s_b) / 2)
    n_boulders = int((s_b - s_a) / 2.1) if n_boulders is None else n_boulders
    ko = list(keep_out) + ([small_zone] if small_zone else [])
    clamp = clampfn or (lambda s: T.cop_bot(s) - GAP)
    bs = boulders(T, R, s_a, s_b, za, zb, n_boulders, keep_out=ko)
    place_boulders(T, P, R, bs, mats, clamp)
    occ = [(a, b, z0, z1) for a, b, z0, z1 in bs] + [(a, b, 0., 9.) for a, b in keep_out]
    # the bed between the two rubble courses changes height every chunk
    cuts = [s_a]
    while cuts[-1] < s_b - .01:
        cuts.append(min(s_b, cuts[-1] + R.uniform(1.0, 2.2)))
        if s_b - cuts[-1] < .5: cuts[-1] = s_b
    for c_a, c_b in zip(cuts, cuts[1:]):
        zm = za + (zb - za) * R.uniform(.38, .62)
        for (c0, c1) in ((za, zm), (zm, zb)):
            if small_zone and c_a < small_zone[1] and c_b > small_zone[0]:
                a, b = max(c_a, small_zone[0]), min(c_b, small_zone[1])
                if a > c_a: course_fill(T, P, c_a, a, c0, c1, .24, .5, mats, R, occupied=occ, clampfn=clamp, rubble=True, roundness=.42)
                cm_ = (c0 + c1) / 2
                for q0, q1 in ((c0, cm_), (cm_, c1)):
                    course_fill(T, P, a, b, q0, q1, .12, .22, mats, R, name='Small_Stone', bulge=.008, r=.05, occupied=occ, clampfn=clamp, chink=False, rubble=True, roundness=.42)
                if b < c_b: course_fill(T, P, b, c_b, c0, c1, .24, .5, mats, R, occupied=occ, clampfn=clamp, rubble=True, roundness=.42)
            else:
                course_fill(T, P, c_a, c_b, c0, c1, .22, .52, mats, R, occupied=occ, clampfn=clamp, rubble=True, r=.09, bulge=.012, roundness=.33, hew=2)


def coursed_wall(T, P, R, s_a=0., s_b=None, mats=None, n=3, wr=(.55, 1.05), hew=3, r=.035, bulge=.006, clampfn=None):
    """Offset courses of long dressed stones, running bond."""
    L = T.L; s_b = L if s_b is None else s_b; mats = mats or P['wall']
    za, zb = FOOT_T, T.cop_bot((s_a + s_b) / 2)
    hs = [R.uniform(.9, 1.1) for _ in range(n)]; tot = sum(hs); z = za
    clamp = clampfn or (lambda s: T.cop_bot(s) - GAP)
    for k, f in enumerate(hs):
        z1 = z + (zb - za) * f / tot
        off = (k % 2) * R.uniform(.25, .4)
        if off > .05:
            course_fill(T, P, s_a, s_a + off, z, z1, off, off, mats, R, r=r, bulge=bulge, hew=hew, clampfn=clamp, chink=False)
        course_fill(T, P, s_a + off, s_b, z, z1, wr[0], wr[1], mats, R, r=r, bulge=bulge, hew=hew, clampfn=clamp, chink=False)
        z = z1


def grass_tuft(name, c, n, h, mat, R, lean=.3, detail=2, spread=.05):
    """A clump of thin blades fanning from one root, each a narrow curved strip."""
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
    """Fern from a wall joint: fronds arch out and down from the face."""
    q = Vector(q); o = Vector(out).normalized()
    for b in range(n):
        a = math.atan2(o.y, o.x) + R.uniform(-1.2, 1.2); up = R.uniform(-.1, .7); Lb = L * R.uniform(.6, 1.)
        dirv = Vector((math.cos(a), math.sin(a), 0)); side = Vector((-dirv.y, dirv.x, 0))
        def fn(u, v, dirv=dirv, side=side, Lb=Lb, up=up):
            p = q + dirv * (Lb * v) + Vector((0, 0, Lb * (up * v - .55 * v * v)))
            w = .035 * math.sin(math.pi * min(v * 1.1, 1.))
            return tuple(p + side * ((u - .5) * 2 * w))
        sheet(name, 2, 6, fn, mat, solid=.001, detail=detail, grain='z')


def moss_patch(name, q, n, r, mat, seed=0, flat=1., **kw):
    """Thin broken colonies along a joint, hugging the face (n = outward normal)."""
    n = Vector(n).normalized(); a = n.cross(Vector((0, 0, 1)) if abs(n.z) < .9 else Vector((1, 0, 0))).normalized(); b = n.cross(a); q = Vector(q)
    kw.setdefault('detail', 2); R = random.Random(seed * 13 + 5)
    for k in range(3):
        rk = r * (.66 if k == 0 else R.uniform(.26, .4)); off = 0 if k == 0 else r * R.uniform(.55, .85); turn = R.uniform(0, math.tau); s_ = seed + k * 3.7
        c = q + a * (math.cos(turn) * off * 1.3) + b * (math.sin(turn) * off * .8)
        def fn(u, v, c=c, rk=rk, s_=s_):
            t = u * math.tau; cx, cy = math.cos(t), math.sin(t)
            e = rk * v * (.72 + .75 * noise.noise(Vector((cx * 1.2 + s_, cy * 1.2, s_ * .3))) + .28 * noise.noise(Vector((cx * 3.4 + s_, cy * 3.4, s_))))
            h = flat * (rk * .075 * (1 - v * v) ** .5)
            p = c + a * (cx * e * 1.3) + b * (cy * e * .8) + n * (h - rk * .015)
            return (p.x, p.y, max(p.z, .003))
        surface(name, 16 if k == 0 else 8, 3 if k == 0 else 2, fn, mat, closed_u=True, **{**kw, 'detail': kw['detail']})


def tread_dressing(T, P, R, n_edge=None, n_back=None, avoid=()):
    """Grass in the joint behind the coping, along the back where the next wall's foot is, a few clumps on the soil; pebbles."""
    L = T.L
    def ok(s): return .25 < s < L - .25 and not any(a < s < b for a, b in avoid)
    # grass grows in drifts along the joint behind the coping: runs of clumps with bare stretches between
    s = R.uniform(.2, .8)
    while s < L - .2:
        run = R.uniform(.4, 1.3); end = min(L - .2, s + run)
        while s < end:
            if ok(s):
                d = R.uniform(.52, .7); z = T.top(s, d)
                grass_tuft('Grass_Edge', (s, d, z), R.randint(9, 15), R.uniform(.14, .32), R.choice((P['grass'], P['grass'], P['dry_grass'])), R, lean=.42, spread=.07)
            s += R.uniform(.09, .17)
        s += R.uniform(.25, .9)
    # the wall foot: tufts on the toe lip leaning out from the stones
    for k in range(int(L * 1.7)):
        s = R.uniform(.2, L - .2)
        if not ok(s) or T.Hw(s) < .1: continue
        d = R.uniform(.015, .06)
        grass_tuft('Grass_Foot', (s, d + .03, .02 + d * .3), R.randint(6, 10), R.uniform(.1, .2), R.choice((P['grass'], P['dry_grass'])), R, lean=.25, spread=.03)
    for k in range(n_back if n_back is not None else int(L * 1.5)):
        s = R.uniform(.2, L - .2)
        if not ok(s): continue
        d = R.uniform(3.72, 3.86); z = T.top(s, d)
        grass_tuft('Grass_Back', (s, d, z), R.randint(5, 8), R.uniform(.1, .2), R.choice((P['grass'], P['dry_grass'])), R)
    # weeds in loose drifts over the field: a few clumps close together, then bare soil
    for k in range(int(L * .45)):
        s0 = R.uniform(.5, L - .5); d0 = R.uniform(1., 3.3)
        for j in range(R.randint(2, 5)):
            s = s0 + R.uniform(-.25, .25); d = d0 + R.uniform(-.2, .2)
            if not ok(s): continue
            grass_tuft('Grass_Field', (s, d, T.top(s, d)), R.randint(3, 7), R.uniform(.06, .14), R.choice((P['dry_grass'], P['grass'])), R, spread=.03)
    for k in range(int(L * 1.2)):
        s = R.uniform(.3, L - .3); d = R.uniform(.8, 3.6)
        if not ok(s): continue
        sz = R.uniform(.035, .075)
        rbox('Pebble', (s, d, T.top(s, d) + sz * .12), (sz, sz * R.uniform(.6, .9), sz * .5), R.choice(P['wall']), r=sz * .3, amp=sz * .08, seed=R.randint(1, 999), div=sz * .4, rot=(0, 0, R.uniform(0, 3)), detail=2)


def face_dressing(T, P, R, n_moss=None, n_fern=2, ferns_at=None):
    """Moss in the shaded low joints and under the coping overhang; ferns where the wall holds damp."""
    L = T.L
    for k in range(n_moss if n_moss is not None else int(L * 1.1)):
        s = R.uniform(.3, L - .3)
        z = R.choice((R.uniform(.02, .12), R.uniform(.2, .3), T.cop_bot(s) - R.uniform(.0, .04)))
        if z > T.Hw(s) - .1 or z < 0.01: continue
        moss_patch('Moss', (s, T.face_d(z) - .045, z), (0, -1, .1), R.uniform(.05, .1), P['moss'], seed=R.randint(1, 999), flat=.4)
    for s in (ferns_at if ferns_at is not None else [R.uniform(.8, L - .8) for _ in range(n_fern)]):
        z = R.uniform(.3, min(.75, T.cop_bot(s) - .08))
        if z < .15: continue
        fern('Wall_Fern', (s, T.face_d(z) - .02, z), P['fern'], R, n=R.randint(6, 9), L=R.uniform(.2, .3))


def collision_mesh(T, Mfn, ds=.25):
    """Prism under the walkable top: front at the wall face, top sampled from the soil (the coping is within 3 cm of it)."""
    L = T.L; ns = max(4, int(round(L / ds))); dfs = FACE0 + .04
    ds_ = [dfs, .5, .9, 1.3, 1.7, 2.4, 3.2, DEPTH]
    rings = []
    for i in range(ns + 1):
        s = L * i / ns
        prof = [(dfs, 0.)] + [(d, max(T.top(s, d), T.Hw(s) if d < .55 and T.Hw(s) > T.top(s, d) else 0., .0)) for d in ds_] + [(DEPTH, 0.)]
        prof = [(d, z) for d, z in prof]
        rings.append(prof)
    n = len(rings[0]); verts = []; faces = []
    for i, r in enumerate(rings):
        s = L * i / ns
        for d, z in r:
            x, y = Mfn(s, d); verts.append((x, y, z))
    for i in range(ns):
        for k in range(n):
            a = i * n + k; b = i * n + (k + 1) % n
            faces.append((a, a + n, b + n, b))
    for i in (0, ns):
        idx = [i * n + k for k in range(n)]
        faces.append(tuple(idx) if i == 0 else tuple(idx[::-1]))
    return verts, faces


def map_all(Mfn):
    """Bend every part from (s, d, z) onto the footprint."""
    for o in S['parts']:
        if o.type != 'MESH': continue
        me = o.data; me.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)
        for v in me.vertices:
            # nothing reaches past the front edge of the footprint or below the lower terrace's soil
            x, y = Mfn(v.co.x, max(v.co.y, 0.)); v.co.x, v.co.y = x, y; v.co.z = max(v.co.z, 0.)
        me.update()
    for k, e in S['sockets'].items():
        p = e.matrix_world.translation; x, y = Mfn(p.x, p.y)
        x2, y2 = Mfn(p.x + .01, p.y); yaw = math.atan2(y2 - y, x2 - x)
        e.matrix_world = Matrix.Translation((x, y, p.z)) @ Matrix.Rotation(yaw, 4, 'Z')


def finish_piece(T, Mfn, name):
    S['collision_mesh'] = collision_mesh(T, Mfn)
    S['terrace'] = T; S['map'] = Mfn
    # connectors: the soil top at the front corner of each end, facing out of the piece
    socket('Socket_Left', (0., 0., RISE if T.Hw(0) >= RISE - 1e-6 else T.Hw(0)))
    socket('Socket_Right', (T.L, 0., T.Hw(T.L)))
    socket('Socket_NextRowFront', (T.L / 2, DEPTH, T.top(T.L / 2, DEPTH)))
    map_all(Mfn)


# ------------------------------------------------------------------ the six pieces
L_STRAIGHT = 8.0


def te01_straight_a(P):
    """Irregular fieldstone wall with a runoff gap: a spillway notch in the coping, a wet streak down the face and a lintelled drain at the foot."""
    R = random.Random(101); L = L_STRAIGHT; sd = 2.9      # the runoff runs at s = 2.9
    groove = lambda s, d: .035 * math.exp(-((s - sd) / .16) ** 2) * (1 - smooth((d - .5) / 1.6))
    T = Terrace(L, 'straight', R, path_dip=groove)
    soil_body(T, P); toe(T, P)
    drain = (sd - .36, sd + .36)
    foot_course(T, P, R, skip=[drain])
    # the drain: two jamb stones, a lintel across, a sill that juts out as a spout, a dark wet throat behind
    stone(T, P, 'Drain_Jamb', drain[0], sd - .14, 0., .21, T.face_d(0) - .02, .55, P['wet'], r=.04, amp=.008, seed=11)
    stone(T, P, 'Drain_Jamb', sd + .14, drain[1], 0., .21, T.face_d(0) - .02, .55, P['wet'], r=.04, amp=.008, seed=12)
    stone(T, P, 'Drain_Lintel', drain[0] - .06, drain[1] + .06, .215, .335, T.face_d(.22) - .035, .62, P['cope'][0], r=.025, amp=.004, hew=3, seed=13, chips=1)
    rbox('Drain_Spout', (sd, .26, .022), (.34, .5, .044), P['wet'], r=.012, amp=.003, seed=14, div=.05, flat='z', grain='y')
    rbox('Drain_Throat', (sd, .62, .11), (.3, .1, .22), P['joint'], r=.01, seed=15, div=.05, grain='z')
    for k, dz in enumerate((.0, .09)):
        rbox('Drain_Floor', (sd, .42, .045 + dz * 0), (.27, .4, .02), P['wet'], r=.006, seed=16 + k, div=.05, grain='y')
    # the column above the drain is the wet streak: darker, mossier stones
    wet_zone = (sd - .3, sd + .3)
    irregular_wall(T, P, R, 0., wet_zone[0], keep_out=())
    for (c0, c1) in ((FOOT_T + .01, .52), (.52, T.cop_bot(sd) - GAP)):
        course_fill(T, P, wet_zone[0], wet_zone[1], c0, c1, .17, .3, [P['wet']], R, name='Wet_Stone', clampfn=lambda s: T.cop_bot(s) - GAP)
    irregular_wall(T, P, R, wet_zone[1], L)
    # spillway: the coping stops, a lower worn sill stone with pebbles in the notch
    coping(T, P, R, skip=[(sd - .22, sd + .22)])
    rbox('Spill_Sill', (sd, .33, RISE - .085), (.44, .46, .1), P['wet'], r=.03, amp=.006, seed=17, div=.06, rot=(-.12, 0, 0), grain='y')
    for k in range(5):
        rbox('Spill_Pebble', (sd + R.uniform(-.13, .13), R.uniform(.25, .5), RISE - .025), (.06, .045, .03), P['wall'][k % 4], r=.012, amp=.004, seed=30 + k, div=.02, detail=2)
    moss_patch('Moss', (sd, T.face_d(.6) - .05, .62), (0, -1, .1), .16, P['moss'], seed=5, flat=.5)
    moss_patch('Moss', (sd - .1, T.face_d(.3) - .05, .3), (0, -1, .1), .12, P['moss'], seed=6, flat=.5)
    tread_dressing(T, P, R, avoid=[(sd - .3, sd + .3)]); face_dressing(T, P, R, ferns_at=[1.3, 6.6])
    grass_tuft('Grass_Edge', (sd + .35, .12, .03), 6, .14, P['grass'], R)
    S['collision'] = []
    finish_piece(T, map_straight(L), 'StraightA')


def te01_straight_b(P):
    """Coursed wall of long offset stones; the right end was rebuilt with smaller, newer stones that have not mossed over yet."""
    R = random.Random(202); L = L_STRAIGHT; rep = L - 1.75
    T = Terrace(L, 'straight', R)
    soil_body(T, P); toe(T, P)
    foot_course(T, P, R)
    coursed_wall(T, P, R, 0., rep)
    # the repair: a stepped seam, small fresh stones, two courses per old one
    za, zb = FOOT_T, T.cop_bot(L)
    k = 0; z = za
    while z < zb - .05:
        z1 = min(z + R.uniform(.11, .15), zb); s0 = rep - (.35 if k % 3 == 0 else .12 if k % 3 == 1 else 0)
        course_fill(T, P, rep, L, z, z1, .18, .34, P['fresh'], R, name='Repair_Stone', r=.03, bulge=.006, hew=2, chink=False, clampfn=lambda s: T.cop_bot(s) - GAP)
        z = z1; k += 1
    coping(T, P, R, 0., rep + .02)
    coping(T, P, R, rep + .02, L, mats=P['fresh'])
    tread_dressing(T, P, R); face_dressing(T, P, R, ferns_at=[2.2])
    S['collision'] = []
    finish_piece(T, map_straight(L), 'StraightB')


def te01_inner(P):
    """Cove bend: the wall curves round a hollow in the slope; small stones packed tight at the deepest point."""
    R = random.Random(303); L = R_IN * math.pi / 2
    T = Terrace(L, 'inner', R)
    soil_body(T, P, ds=.17); toe(T, P, ds=.17)
    foot_course(T, P, R)
    irregular_wall(T, P, R, small_zone=(L / 2 - .6, L / 2 + .6), n_boulders=2)
    coping(T, P, R)
    tread_dressing(T, P, R); face_dressing(T, P, R, ferns_at=[L / 2 + .9])
    S['collision'] = []
    finish_piece(T, map_inner, 'InnerBend')


def te01_outer(P):
    """Spur bend: the wall wraps round the nose of the slope in long rough courses."""
    R = random.Random(404); L = R_OUT * math.pi / 2
    T = Terrace(L, 'outer', R)
    soil_body(T, P, ds=.25); toe(T, P)
    foot_course(T, P, R)
    irregular_wall(T, P, R, n_boulders=5)
    coping(T, P, R)
    tread_dressing(T, P, R); face_dressing(T, P, R, ferns_at=[3.1, 9.4])
    S['collision'] = []
    finish_piece(T, map_outer, 'OuterBend')


def te01_end(P):
    """End of a row: the wall and the soil come down together to the slope, the courses dropping out one by one."""
    R = random.Random(505); L = L_STRAIGHT
    def hw(s):
        t = (s - 1.2) / (L - 1.2)
        return RISE if t <= 0 else RISE * (1 - smooth(t) * .985)
    T = Terrace(L, 'end', R, hw=hw)
    soil_body(T, P); toe(T, P)
    clamp = lambda s: T.cop_bot(s) - GAP if T.Hw(s) >= .36 else T.Hw(s) + .012
    foot_course(T, P, R, clampfn=lambda s: min(FOOT_T, T.Hw(s) + .015) if T.Hw(s) < .36 else 9.)
    irregular_wall(T, P, R, 0., 5.6, n_boulders=2, clampfn=clamp)
    coping(T, P, R, 0., 6.7)
    tread_dressing(T, P, R); face_dressing(T, P, R, ferns_at=[2.6])
    # where the wall has run out, grass takes the slope
    for k in range(14):
        s = R.uniform(6.2, L - .25); d = R.uniform(.1, .5)
        grass_tuft('Grass_End', (s, d, T.top(s, max(d, .6)) * (.4 + d)), R.randint(5, 8), R.uniform(.12, .2), R.choice((P['grass'], P['dry_grass'])), R)
    S['collision'] = []
    finish_piece(T, map_straight(L), 'End')


def te01_broken(P):
    """An old breach near the right end: the top courses fell, the bank slumped, and someone held it with stakes and woven withies.
    The fallen stones are heaped on the bank waiting to be set back. Still walkable along the whole tread."""
    R = random.Random(606); L = L_STRAIGHT; b0, b1 = 4.7, 7.1; bc = (b0 + b1) / 2
    def dip(s):
        if s <= b0 or s >= b1: return 0.
        t = (s - b0) / (b1 - b0)
        return .5 * math.sin(math.pi * t) ** 1.6 * (1 + .08 * math.sin(t * 11))   # zero slope where it meets the sound wall: walkable along the tread
    hw = lambda s: RISE - dip(s)
    T = Terrace(L, 'broken', R, hw=hw, slump=lambda s: dip(s) * .96)
    soil_body(T, P); toe(T, P)
    foot_course(T, P, R)
    clamp = lambda s: (T.cop_bot(s) - GAP) if dip(s) < .02 else (RISE - dip(s) - .02)
    irregular_wall(T, P, R, 0., b0 - .05, n_boulders=2)
    irregular_wall(T, P, R, b0 - .05, b1 + .05, n_boulders=1, clampfn=clamp)
    irregular_wall(T, P, R, b1 + .05, L, n_boulders=0)
    coping(T, P, R, skip=[(b0 - .1, b1 + .1)])
    # loose stones still on the broken top, tilted
    for k in range(5):
        s = R.uniform(b0 + .3, b1 - .3); z = RISE - dip(s)
        stone(T, P, 'Loose_Top', s - .16, s + .16, z - .06, z + .1, T.face_d(z) + .02, .32, R.choice(P['wall']), r=.05, amp=.012, seed=R.randint(1, 999), tilt=R.uniform(-.35, .35))
    # stakes and woven withies holding the slumped bank, set in just behind the broken face
    xs = [b0 + .25 + k * (b1 - b0 - .5) / 5 for k in range(6)]
    for k, s in enumerate(xs):
        zb = T.top(s, .42); top = zb + R.uniform(.22, .32)
        log('Stake', [(s, .42, zb - .12), (s + .005, .43, (zb + top) / 2), (s, .42, top)], .032, P['stake'], seg=8, lump=.06, seed=k, grain='z')
    for row in range(3):
        pts = []
        for k, s in enumerate(xs):
            zb = T.top(s, .42) + .03 + row * .055
            pts.append((s, .42 + (.02 if (k + row) % 2 else -.02), zb))
        log('Withy', pts, .014, P['withy'], seg=6, lump=.05, seed=row, grain='x', detail=1)
    # the heap of fallen stones carried up onto the bank
    for k in range(9):
        s = R.uniform(b1 - 1.2, b1 + .4); d = R.uniform(1.6, 2.2); sz = R.uniform(.16, .3)
        z = T.top(s, d)
        rbox('Fallen_Stone', (s, d, z + sz * .28 + (k > 5) * .1), (sz, sz * R.uniform(.7, 1.), sz * .62), R.choice(P['wall']), r=sz * .3, amp=sz * .06, chips=1, seed=R.randint(1, 999), div=.06, rot=(R.uniform(-.2, .2), R.uniform(-.2, .2), R.uniform(0, 3)), detail=1)
    # new grass on the slumped bank
    for k in range(16):
        s = R.uniform(b0 + .1, b1 - .1); d = R.uniform(.5, 1.5)
        grass_tuft('Grass_Bank', (s, d, T.top(s, d)), R.randint(5, 9), R.uniform(.1, .2), R.choice((P['grass'], P['grass'], P['dry_grass'])), R)
    tread_dressing(T, P, R, avoid=[(b0, b1)]); face_dressing(T, P, R, ferns_at=[1.9])
    S['collision'] = []
    finish_piece(T, map_straight(L), 'Broken')
