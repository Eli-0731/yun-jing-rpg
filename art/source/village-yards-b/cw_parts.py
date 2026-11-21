"""Shared parts for the yard walls (CW01) and the yard gate (CW02): a small tiled coping / gable of dark grey (#3A4048) pan-and-roll
tiles, a four-sided tiled pier cap, a coursed stone footing and a rammed-earth body laid in lifts.

The coping is built here and not with vl_roof: a wall cap is two short slopes (0.25 m each) with the rolls running down them, which
vl_roof's twelve-course house roof cannot be scaled to. Its tiles carry the pack's 黛瓦 colour (cr_mats.tile), not the shared VL tile
texture.
Local frame of every run: along +x, wall centre line y = 0, ground z = 0; callers place runs with ti_core.xf.
"""
import math, random
from mathutils import Vector, noise
from ti_core import S, box, cyl, lathe, mesh
from cr_parts import rbox
import fr_parts as FP

FOOT_H, FOOT_T = .42, .44            # stone footing height and thickness
BODY_T0, BODY_T1 = .40, .36          # rammed earth thickness at the foot / under the eave course
LIFT = .16                           # rammed earth lift height


# ------------------------------------------------------------------ mesh helpers
class Acc:
    """Collects quads/tris into one mesh."""
    def __init__(self): self.V, self.F = [], []
    def grid(self, rows, closed=False):
        """rows: list of equal-length point lists; quads between consecutive rows."""
        b = len(self.V); m = len(rows[0])
        for r in rows: self.V.extend(tuple(p) for p in r)
        for i in range(len(rows) - 1):
            for k in range(m if closed else m - 1):
                a = b + i * m + k; c = b + i * m + (k + 1) % m
                self.F.append((a, c, c + m, a + m))
        return b
    def cap(self, idx):
        self.F.append(tuple(idx))
    def make(self, name, mat, **kw):
        if not self.F: return None
        o = mesh(name, self.V, self.F, mat, **kw)
        import bmesh
        bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
        return o


def extrude_x(name, prof, x0, x1, mat, **kw):
    """Closed (y, z) outline, counter-clockwise seen from +x, extruded from x0 to x1, ends capped."""
    a = Acc(); m = len(prof)
    a.grid([[(x0, y, z) for y, z in prof], [(x1, y, z) for y, z in prof]], closed=True)
    a.cap([i for i in range(m)][::-1]); a.cap([m + i for i in range(m)])
    return a.make(name, mat, **kw)


# ------------------------------------------------------------------ tiled coping (ridge along x)
def cap_profile(half, z_eave, z_ridge):
    """Top of the boards under the tiles at |y|: a slightly dished slope from the ridge to the eave."""
    return lambda y: z_ridge - (z_ridge - z_eave) * (1 - (1 - min(1., abs(y) / half)) ** 1.25)


def tile_cap(P, name, x0, x1, half, z_eave, z_ridge, keep=lambda x, side: True, pitch=.19, seed=0, ridge=True, ends=(False, False),
             roll_r=.034, group='Stone', board_mat=None, board_group=None):
    """Two slopes of pans and rolls running down from a ridge along x; boards under them; a ridge body with a round cap tile.
    keep(x, side) drops the tile row at x on that side (broken copings); ends=(lo, hi) put an end disc on the ridge at that end."""
    Rt = random.Random(f'{name}:{seed}')
    zt = cap_profile(half, z_eave, z_ridge)
    # boards: across both slopes, 4 cm thick, ending 1 cm short of the tile eave
    ys = [-(half - .01) + 2 * (half - .01) * i / 16 for i in range(17)]
    prof = [(y, zt(y) - .016) for y in ys] + [(y, zt(y) - .056) for y in ys[::-1]]
    extrude_x(name + '_Boards', prof[::-1], x0, x1, board_mat or P['bed'], group=board_group or group, grain='x')
    pans, rolls, discs = Acc(), Acc(), Acc()
    n = max(2, int(round((x1 - x0) / pitch))); step = (x1 - x0) / n
    for side in (-1, 1):
        for i in range(n + 1):
            xc = x0 + i * step                                    # pan centre; the end pans are halves, so two pieces meet in a whole pan
            xr = xc + step / 2                                    # roll over the joint to the next pan
            jit = Rt.uniform(-.004, .004) if 0 < i < n else 0.
            if keep(xc, side):
                xp = xc + jit; w = step * .5
                ua, ub = max(-1., (x0 - xp) / w), min(1., (x1 - xp) / w)
                # a pan: shallow trough, 12 mm thick, from under the ridge to 1.5 cm past the eave
                rows = []
                for v in range(5):
                    t = v / 4; y = side * (.03 + (half + .015 - .03) * t)
                    lift = .004 * math.sin(t * math.pi * 3) ** 2                     # the step where one course laps the next
                    row = []
                    for u in range(6):
                        s = ua + (ub - ua) * u / 5
                        row.append((xp + s * w, y, zt(y) - .006 + .016 * s * s + lift))
                    rows.append(row)
                pans.grid(rows)                                                      # solidified below: 12 mm thick
            if i < n and keep(xc, side) and keep(xc + step, side):
                # a roll: half tube over the joint, a little fatter at each course end
                rows = []
                ylen = half + .022
                for v in range(7):
                    t = v / 6; y = side * (.02 + (ylen - .02) * t)
                    r = roll_r * (1 + .1 * ((t * 3) % 1.))
                    rows.append([(xr + jit + r * math.cos(math.pi * u / 6), y, zt(y) + .002 + r * math.sin(math.pi * u / 6) * .95) for u in range(7)])
                rolls.grid(rows)
                ye = side * ylen
                discs.grid([[(xr + jit + (roll_r + .006) * math.cos(math.tau * u / 10), ye, zt(ye) + .004 + (roll_r + .006) * math.sin(math.tau * u / 10)) for u in range(10)],
                            [(xr + jit + (roll_r + .006) * math.cos(math.tau * u / 10), ye + side * .012, zt(ye) + .004 + (roll_r + .006) * math.sin(math.tau * u / 10)) for u in range(10)]],
                           closed=True)
                b = len(discs.V) - 20
                discs.cap([b + u for u in range(10)][::(-1 if side > 0 else 1)]); discs.cap([b + 10 + u for u in range(10)][::(1 if side > 0 else -1)])
    pans.make(name + '_Pans', P['captile'], smooth=True, group=group, grain='y', solid=.012)
    rolls.make(name + '_Rolls', P['captile'], smooth=True, group=group, grain='y', solid=.01)
    discs.make(name + '_EaveDiscs', P['captile'], smooth=False, group=group, grain='y')
    if ridge:
        xs0 = x0 + .002; xs1 = x1 - .002
        # keep the ridge where both slopes still have their rolls (broken copings lose the ridge too)
        segs, cur = [], None
        N = int((x1 - x0) / .05)
        for k in range(N + 1):
            x = x0 + (x1 - x0) * k / N; ok = keep(x, -1) and keep(x, 1)
            if ok and cur is None: cur = x
            if (not ok or k == N) and cur is not None: segs.append((cur, x)); cur = None
        for a, b in segs:
            if b - a < .1: continue
            rbox(name + '_Ridge_Body', ((a + b) / 2, 0., z_ridge + .01), (b - a, .12, .08), P['captile'], r=.01, amp=.002, seed=seed, div=.08, flat='xX',
                 group=group, grain='x')
            cyl(name + '_Ridge_Roll', ((a + b) / 2, 0., z_ridge + .05), .042, b - a, P['captile'], axis='x', verts=14, group=group, grain='x')
        for e, x in zip(ends, (x0, x1)):
            if e: cyl(name + '_Ridge_End', (x, 0., z_ridge + .05), .05, .02, P['captile'], axis='x', verts=14, group=group)


def tile_pyramid(P, name, cx, cy, half, z_eave, z_top, pitch=.13, group='Stone'):
    """Four tiled slopes up to a point (a pier cap), hip rolls on the diagonals and a small round finial."""
    zt = lambda d: z_top - (z_top - z_eave) * (d / half) ** 1.1          # d = distance in from the apex (Chebyshev)
    # boards: a square pyramid slab 4 cm thick
    a = Acc(); ring = lambda h, dz: [(cx + h * sx, cy + h * sy, zt(h) + dz) for sx, sy in ((1, -1), (1, 1), (-1, 1), (-1, -1))]
    b0 = a.grid([ring(half - .005, -.016), ring(half - .005, -.056)], closed=True)
    a.V.append((cx, cy, z_top - .016)); apex = len(a.V) - 1
    for k in range(4): a.F.append((b0 + k, b0 + (k + 1) % 4, apex))
    a.cap([b0 + 4 + k for k in range(4)][::-1])
    a.make(name + '_Boards', P['bed'], group=group, grain='z')
    # one continuous tiled skin per slope: dished pans with round rolls between them (like the wall coping), so the cap reads as
    # a little tiled roof and not as loose rolls lying on a board. Each slope is clipped at the hips; the hip rolls cover the seams.
    skin, discs = Acc(), Acc()
    n = max(2, int(round(2 * half / pitch))); g = 2 * half / n; rr = .028
    rolls_e = [-half + g * i for i in range(1, n)]
    def corr(e):
        s = min(abs(e - r) for r in rolls_e)
        if s < rr: return math.sqrt(rr * rr - s * s)
        return -.008 * math.sin(math.pi / 2 * min(1., (s - rr) / (g / 2 - rr)))
    m = 49
    for k, (dx, dy) in enumerate(((0, -1), (1, 0), (0, 1), (-1, 0))):
        tx, ty = -dy, dx                                                       # along the eave of this face
        rows = []
        for v in range(8):
            t = v / 7; row = []
            for j in range(m):
                e = -half + 2 * half * j / (m - 1)
                d = abs(e) + (half + .02 - abs(e)) * t                         # from the hip (t = 0) out past the eave (t = 1)
                row.append((cx + dx * d + tx * e, cy + dy * d + ty * e, zt(min(d, half)) + .006 + corr(e) * min(1., .4 + 2 * t)))
            rows.append(row)
        skin.grid(rows)
        for e in rolls_e:
            x = cx + dx * (half + .02) + tx * e; y = cy + dy * (half + .02) + ty * e
            discs.grid([[(x + tx * .031 * math.cos(math.tau * u / 10) + dx * w, y + ty * .031 * math.cos(math.tau * u / 10) + dy * w, zt(half) + .006 + .031 * math.sin(math.tau * u / 10))
                         for u in range(10)] for w in (0., .012)], closed=True)
            bb = len(discs.V) - 20; discs.cap([bb + u for u in range(10)]); discs.cap([bb + 10 + u for u in range(10)][::-1])
    skin.make(name + '_Tiles', P['captile'], smooth=True, group=group, grain='y', solid=.012)
    hips = Acc()
    for sx, sy in ((1, -1), (1, 1), (-1, 1), (-1, -1)):
        rows = []
        for v in range(6):
            d = (half + .012) * v / 5                                            # hips stop at the corner, no logs sticking out
            c = Vector((cx + sx * d, cy + sy * d, zt(min(d, half)) + .026))
            side = Vector((-sy, sx, 0)).normalized()
            rows.append([tuple(c + side * (.036 * math.cos(math.pi * u / 6)) + Vector((0, 0, .036 * math.sin(math.pi * u / 6)))) for u in range(7)])
        hips.grid(rows)
        # end tile closing the hollow of the hip roll at the corner
        dv = Vector((sx, sy, 0)).normalized(); c = Vector((cx + sx * (half + .012), cy + sy * (half + .012), zt(half) + .026))
        semi = [c + side * (.04 * math.cos(math.pi * u / 8)) + Vector((0, 0, .04 * math.sin(math.pi * u / 8) - .006)) for u in range(9)]
        bb = discs.grid([[tuple(p + dv * w) for p in semi] for w in (-.014, .0)], closed=True)
        discs.cap([bb + u for u in range(9)]); discs.cap([bb + 9 + u for u in range(9)][::-1])
    hips.make(name + '_Hips', P['captile'], smooth=True, group=group, grain='x', solid=.01)
    discs.make(name + '_EaveDiscs', P['captile'], smooth=False, group=group, grain='y')
    lathe(name + '_Finial', [(0., 0.), (.045, .0), (.05, .018), (.038, .035), (.018, .046), (0., .05)], (cx, cy, z_top + .02), P['captile'], seg=14, group=group)


# ------------------------------------------------------------------ footing and earth body
def footing(P, R, name, x0, x1, flat_ends=True, h=FOOT_H, t=FOOT_T, seed=0):
    """Two courses of dressed stones through the wall, joints broken; a dark earth mortar core between them."""
    box(name + '_Core', ((x0 + x1) / 2, 0., (h - .02) / 2), (x1 - x0 - .01, t - .05, h - .02), P['mortar'], bevel=.004, group='Stone', grain='x')
    zs = [0., h * .52 + R.uniform(-.02, .02), h]
    for c in range(2):
        x = x0
        while x < x1 - .05:
            L = R.uniform(.24, .48)
            if x1 - (x + L) < .16: L = x1 - x
            lo, hi = x == x0, abs(x + L - x1) < 1e-6
            z0 = zs[c] + (.0 if c == 0 else .006 + R.uniform(-.03, .03)); z1 = zs[c + 1] - .006 - R.uniform(0, .03) if c == 0 else zs[c + 1] - .004 - R.uniform(0, .02)
            g = .012 if not hi else 0.
            sx = (x + .006 * (not lo)) ; ex = x + L - g / 2
            flat = 'z' + ('x' if lo and flat_ends else '') + ('X' if hi and flat_ends else '')
            rbox(name + '_Stone', ((sx + ex) / 2, R.uniform(-.008, .008), (z0 + z1) / 2), (ex - sx, t + R.uniform(-.02, .012), z1 - z0), R.choice(P['stone']),
                 r=.035, amp=.016, freq=3.5, chips=3, hew=3, seed=seed * 100 + c * 40 + int(x * 10), div=.06, flat=flat, group='Stone',
                 skew=(0., R.uniform(-.015, .015)))
            x += L


def lifts(P, R, name, x0, x1, z0, z1, cut=lambda z: 0., flat_lo=True, flat_hi=True, seed=0, t0=BODY_T0, t1=BODY_T1):
    """Rammed earth in lifts of about 16 cm, battered from t0 at the foot to t1 at the top. cut(z) takes the body back from x1 (a breach):
    the broken end of each lift is left rough, with a darker crumbled core showing."""
    n = max(1, int(round((z1 - z0) / LIFT))); hz = (z1 - z0) / n
    tz = lambda z: t0 + (t1 - t0) * (z - z0) / (z1 - z0)
    for i in range(n):
        za, zb = z0 + i * hz, z0 + (i + 1) * hz
        c = cut((za + zb) / 2); xe = x1 - c
        if xe - x0 < .12: continue
        broken = c > .01
        flat = ('x' if flat_lo else '') + ('X' if flat_hi and not broken else '')
        ta, tb = tz(za), tz(zb)
        rbox(name + '_Lift', ((x0 + xe) / 2, R.uniform(-.003, .003), (za + zb) / 2 + .004), (xe - x0, ta, hz + .016), P['earth'], r=.008, amp=.007,
             freq=1.4, chips=0, seed=seed * 50 + i, div=.07, flat=flat, taper=(1., tb / ta), group='Main', grain='z',
             warp=(lambda q, xe=xe, hz=hz: _broken_end(q, x0, xe, hz, seed * 50 + i)) if broken else None)
        if broken:
            # the crumbled core at the broken end: proud and rough, darker than the dressed face
            rbox(name + '_Core_Exposed', (xe - .06, 0., (za + zb) / 2), (.2, ta - .03, hz - .004), P['core'], r=.035, amp=.03, freq=5., chips=5, seed=seed * 50 + i + 7,
                 div=.035, group='Main', grain='z', warp=lambda q, xe=xe: _crumble(q, seed * 50 + i))


def _broken_end(q, x0, xe, hz, seed):
    """Lift's local frame (centred): the last 25 cm of a broken lift sags and crumbles back in an uneven line."""
    L = xe - x0; d = q.x - (L / 2 - .25)
    if d > 0:
        k = d / .25
        q.x -= .06 * k * (1 + noise.noise(Vector((q.y * 9, q.z * 9, seed))))
        q.z -= .03 * k * k * (q.z > 0)
        q.y *= 1 - .08 * k


def _crumble(q, seed):
    q.x += .03 * noise.noise(Vector((q.y * 7, q.z * 7, seed + .5)))
    q.z += .012 * noise.noise(Vector((q.x * 8, q.y * 8, seed + 1.5)))


def eave_course(P, name, x0, x1, z, w=BODY_T1 + .07, h=.05):
    """A course of grey lime-set bricks under the coping, a little proud of the earth face."""
    rbox(name + '_Eave_Course', ((x0 + x1) / 2, 0., z + h / 2), (x1 - x0, w, h), P['bed'], r=.008, amp=.002, seed=3, div=.1, flat='xX', group='Stone', grain='x')
