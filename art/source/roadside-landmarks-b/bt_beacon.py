"""BT01 old beacon tower on the A7 east ridge (work pack 2026-11-09 B-112h, batch B, BT01).

A round dry-laid stone platform tower, slightly battered, half fallen: on the back-right side the wall has slumped out in a V-shaped
breach and the fill has run down into a rubble slope that spreads towards the back-right corner; the rest stands to the top, a
paved flat top with a few broken stubs of the old parapet. A narrow stone stair climbs round the outside of the wall from the front
to the back-left and arrives on the top, so a player can go up, stand on the top and look out. Dry grass in the joints and on the
top, moss low down. Only the stone (the sheet's timber rails and props are left out, as the pick notes say); no writing.

Sizes (limit 8 x 8 x 7 m): wall radius 2.75 m at the foot, 2.45 m at the top (5.4 m), 18 courses; the stair 0.9 m wide, 27 risers
of 0.2 m, about 0.29 m treads on its middle line, from -100 deg (front) round to 120 deg (back-left), angles from +X towards +Y;
the breach centred on 45 deg (back-right), its floor at 2.2 m; parapet stubs up to 0.9 m over the top (highest point about 6.3 m).
Origin: centre of the tower at ground level, z = 0; front -Y.
Walking: the collision is a height field (the top at 5.4 m, the breach and the rubble slope as they lie, the ground round it) plus
the stair as a ramp on its nosing line; the stair has no rail (the sheet's timber rail is not made).
Reference: art/references/BT01/BT01-cand-4.png.
"""
import math, random
from mathutils import Vector, Euler, noise
import cr_mats as cm
import fr_parts as FP
from cr_parts import rbox
from ti_core import S, socket, surface

W, D, H = 8.0, 8.0, 7.0
R0, RT, TOP = 2.75, 2.45, 5.4
NC = 18
COURSE = TOP / NC                            # 0.3
WALL_T = .45
TH0, TH1 = math.radians(-100), math.radians(-240)     # the stair, front round to the back-left (clockwise)
NSTEP, RISER, SW = 27, .2, .9
THC = math.radians(45)                       # the breach
SPREAD = math.radians(62)                    # half-width of the rubble fan
LIM = 3.95                                   # keep inside the 8 m square


def _courses():
    """Course tops: the bottom three courses tall (big footing stones), the rest uneven, 0.2-0.38 m, scaled to reach TOP."""
    Rc = random.Random('BT01_courses')
    hs = [Rc.uniform(.36, .44) if c < 3 else Rc.uniform(.2, .38) for c in range(NC)]
    k = TOP / sum(hs); z = [0.]
    for h in hs: z.append(z[-1] + h * k)
    return z


ZS = _courses()


def rad(z): return R0 + (RT - R0) * z / TOP


def ang(a, b):
    return (a - b + math.pi) % math.tau - math.pi


def breach_a(phi):
    return abs(ang(phi, THC)) / SPREAD


def wall_top(phi):
    """How high the wall still stands at angle phi: a V-shaped breach, floor 2.2 m, back to full height at 80% of the fan."""
    a = breach_a(phi)
    return TOP + 1 if a >= .8 else 2.2 + (TOP - 2.2) * (a / .8) ** 2


def rubble_in(rho, phi):
    """Inside the tower: the fill slumps from the breach floor up towards the middle (1.6 m a metre)."""
    a = breach_a(phi)
    if a >= .8: return TOP
    return min(TOP, wall_top(phi) - .25 + (rad(2.) - rho) * 1.6)


def rubble_out(rho, phi):
    """Outside: the spill runs out from the breach and reaches the ground just inside the square, thinning to nothing at the fan's edges."""
    a = breach_a(phi)
    if a >= 1: return 0.
    h0 = 1.95 * (1 - a * a)                                   # against the wall: the spill through the notch, thinning to the fan's edges
    run = rho_max(phi) - rad(2.) - .15
    f = max(0., 1 - (rho - rad(2.)) / run)
    return h0 * f ** 1.25


def rho_max(phi):
    return min(5.3, LIM / max(abs(math.cos(phi)), abs(math.sin(phi))))


def stair_phi(t): return TH0 + (TH1 - TH0) * t


def palette():
    P = {}
    shade = [(1., 1., 1.), (.86, .86, .87), (1.08, 1.04, .96), (.94, .96, .98)]
    light, dark = (.2, .186, .158), (.085, .078, .066)
    P['stone'] = [cm.stone(f'Beacon_Stone_{i}', light=tuple(c * f for c, f in zip(light, shade[i])), dark=tuple(c * f for c, f in zip(dark, shade[i])),
                           ochre=(.27, .23, .16), moss=.8, lichen=.6, crack=.5, moss_low_z=1.0, slot='Stone') for i in range(4)]
    P['pave'] = cm.stone('Beacon_Paving', light=(.22, .205, .178), dark=(.095, .088, .075), ochre=(.27, .23, .16), moss=.6, lichen=.7, crack=.6, slot='Stone')
    P['rubble'] = [cm.stone(f'Beacon_Rubble_{i}', light=l, dark=d, ochre=(.26, .22, .15), moss=1.0, lichen=.5, crack=.4)
                   for i, (l, d) in enumerate((((.22, .205, .18), (.095, .088, .075)), ((.2, .19, .165), (.085, .08, .068))))]
    P['bed'] = cm.stone('Rubble_Bed', light=(.15, .14, .12), dark=(.07, .064, .055), ochre=(.2, .16, .1), moss=1.2, lichen=.3, crack=.3)
    P['moss'] = cm.moss_tuft('Beacon_Moss', soft=True)
    P['dry'] = cm.weed_leaf('Ridge_Dry_Grass', (.12, .09, .04), (.32, .25, .11), (.48, .4, .2))
    P['grass'] = cm.weed_leaf('Ridge_Grass', (.05, .07, .025), (.16, .19, .06), (.3, .3, .1))
    return P


def ring_block(name, phi, r_out, z0, z1, L, depth, mat, seed, R, group='Stone', jitter=0., **kw):
    """A block laid on the curve: its outer face on radius r_out (give or take `jitter`), bent to the circle."""
    r_out += R.uniform(-jitter, jitter * .6)
    rc = r_out - depth / 2
    def warp(q, rr=r_out):
        q.y += q.x * q.x / (2 * rr)
    return rbox(name, (rc * math.cos(phi), rc * math.sin(phi), (z0 + z1) / 2), (L, depth, z1 - z0), mat, r=.03, amp=.018, freq=4., chips=3, hew=3,
                seed=seed, div=.2, rot=(0, 0, phi + math.pi / 2), warp=warp, group=group, **kw)


def tower(P, R):
    occ = [[] for _ in range(NC + 1)]           # angle spans already filled by a tall stone from the course below
    for c in range(NC):
        z0, z1 = ZS[c], ZS[c + 1]
        ro = rad((z0 + z1) / 2) + R.uniform(-.015, .015)
        start = R.uniform(0, math.tau); end = start + math.tau; phi = start
        spans = sorted((start + (a - start) % math.tau, start + (a - start) % math.tau + (b - a)) for a, b in occ[c])
        gap = .014 / ro
        while phi < end - .05:
            hit = next((sp for sp in spans if sp[0] - gap * .5 <= phi < sp[1]), None)
            if hit: phi = hit[1] + gap * .2; continue
            big = c < 3
            L = (R.uniform(.6, 1.35) if big else R.uniform(.32, 1.15)) if R.random() < .8 else R.uniform(.22, .38)
            dphi = L / ro
            nxt = min((sp[0] for sp in spans if sp[0] > phi), default=None)
            if nxt is not None and phi + dphi > nxt - gap:
                dphi = nxt - phi; L = dphi * ro
                if L < .2: phi = nxt; continue
            if phi + dphi > end - .1: dphi = end - phi; L = dphi * ro
            mid = phi + dphi / 2
            if (z0 + z1) / 2 < wall_top(mid):
                ragged = breach_a(mid) < .8 and (z1 > wall_top(mid) - (z1 - z0) * 1.2)
                tall = (not ragged and 2 <= c < NC - 3 and breach_a(mid) > 1.05 and .45 < L < 1.0 and R.random() < .13)
                if tall:        # a tall stone across two courses: the course above leaves it room
                    zt = ZS[c + 2]
                    b = ring_block('Wall_Stone', mid, ro, z0 + R.uniform(0, .01), zt - .006 - R.uniform(0, .015), L - .012 - R.uniform(0, .02), WALL_T,
                                   R.choice(P['stone']), c * 97 + int(mid * 50) + 3, R, jitter=.02)
                    b.rotation_euler.z += R.uniform(-.012, .012)
                    occ[c + 1].append((phi % math.tau, phi % math.tau + dphi))
                    phi += dphi; continue
                if L > .6 and R.random() < .2:       # now and then two thin stones in the course instead of one
                    zm = z0 + (z1 - z0) * R.uniform(.4, .6)
                    for q, (za, zb) in enumerate(((z0, zm - .005), (zm, z1 - .006))):
                        ring_block('Wall_Stone', mid + R.uniform(-.02, .02), ro, za, zb, L * R.uniform(.75, .98) - .012, WALL_T, R.choice(P['stone']), c * 97 + int(mid * 50) + q * 7, R, jitter=.02)
                    phi += dphi; continue
                b = ring_block('Wall_Stone', mid, ro, z0 + R.uniform(0, .018), z1 - .006 - R.uniform(0, .028), L - .012 - R.uniform(0, .03), WALL_T, R.choice(P['stone']),
                               c * 97 + int(mid * 50), R, jitter=.03)
                b.rotation_euler.z += R.uniform(-.015, .015)
                b.rotation_euler.x += R.uniform(-.012, .012)     # not laid dead level
                if ragged:      # the blocks along the breach lean out a little and lose their corners
                    b.rotation_euler.x += R.uniform(-.06, .06); b.rotation_euler.z += R.uniform(-.05, .05)
            phi += dphi


def core_and_top(P, R):
    rc = RT - WALL_T + .02
    # the fill: one height field from the middle out to just inside the wall's outer face (flat under the paving, slumped in the
    # breach where it meets the notch floor); the wall ring hides its edge everywhere else
    def top_fn(u, v):
        phi = u * math.tau
        z_edge = min(TOP - .12, rubble_in(rad(2.) - .05, phi) - .05)
        rho = .25 + (rad(max(0., z_edge)) - .1 - .25) * v
        z = min(TOP - .12, rubble_in(rho, phi) - .05)
        return (rho * math.cos(phi), rho * math.sin(phi), z)
    surface('Fill_Top', 120, 12, top_fn, P['bed'], closed_u=True, group='Main', grain='z')
    # the paving: slabs on a grid inside the parapet course, kept where the top has not slumped
    # rows of old flags of uneven length and width, the joints staggered, a few missing
    y = -rc; j = 0
    while y < rc:
        dy = R.uniform(.42, .66); x = -rc + R.uniform(0, .3)
        while x < rc:
            dx = R.uniform(.4, .9); cx, cy = x + dx / 2, y + dy / 2
            rho = math.hypot(cx, cy); phi = math.atan2(cy, cx)
            ok = rho + .5 * max(dx, dy) < rc + .05 and rubble_in(rho, phi) >= TOP - .02 and R.random() > .04
            if ok:
                rbox('Top_Slab', (cx, cy, TOP - .06 + R.uniform(-.008, .006)), (dx - .014, dy - .014, .12), P['pave'], r=.015, amp=.005, chips=2, hew=2,
                     seed=j * 31 + int(x * 10), div=.12, flat='z', rot=(R.uniform(-.008, .008), R.uniform(-.008, .008), R.uniform(-.02, .02)), group='Stone')
            x += dx
        y += dy; j += 1
    # the top course of the wall as a coping ring is the last wall course already; the parapet stubs stand on it
    stubs = [(-78, -60, .9), (-150, -131, .75), (-178, -163, .55), (152, 168, .85), (172, 186, .5)]
    for k, (a0, a1, h) in enumerate(stubs):
        a0, a1 = math.radians(a0), math.radians(a1)
        if breach_a((a0 + a1) / 2) < .9: continue
        rows = max(1, int(h / .3 + .5))
        for r_ in range(rows):
            shrink = r_ * .25 * (a1 - a0)
            b0, b1 = a0 + shrink * R.uniform(.2, .6), a1 - shrink * R.uniform(.2, .6)
            nb = max(1, int((b1 - b0) * RT / .5))
            for q in range(nb):
                ba, bb = b0 + (b1 - b0) * q / nb, b0 + (b1 - b0) * (q + 1) / nb
                ring_block('Parapet_Stone', (ba + bb) / 2, RT + .02, TOP + r_ * .3, TOP + (r_ + 1) * .3 - .008, (bb - ba) * RT - .012, .42, R.choice(P['stone']),
                           900 + k * 13 + r_ * 5 + q, R)
    # a merlon toppled onto the top
    rbox('Fallen_Merlon', (-1.1, -1.4, TOP + .14), (.5, .38, .28), P['stone'][2], r=.025, amp=.012, chips=3, hew=2, seed=990, div=.12, rot=(.08, -.05, .7), group='Stone')


def stair(P, R):
    for k in range(NSTEP):
        t0, t1 = k / NSTEP, (k + 1) / NSTEP
        top = (k + 1) * RISER
        mid = stair_phi((t0 + t1) / 2); ri = rad(top) - .01; ro = ri + SW
        dphi = abs(stair_phi(t1) - stair_phi(t0))
        L = dphi * (ri + SW / 2) + .02
        rbox('Stair_Tread', ((ri + SW / 2) * math.cos(mid), (ri + SW / 2) * math.sin(mid), top - .09), (L, SW, .18), P['stone'][k % 4],
             r=.02, amp=.006, freq=4., chips=2, hew=3, seed=1000 + k, div=.14, flat='z', rot=(0, 0, mid + math.pi / 2),
             warp=lambda q, rr=ri + SW / 2: setattr(q, 'y', q.y + q.x * q.x / (2 * rr)), group='Stone')
    # the stair's base: a solid curved ramp of coursed blocks under the treads, two steps a column
    for k in range(0, NSTEP - 1, 2):
        t0, t1 = k / NSTEP, (k + 2) / NSTEP
        mid = stair_phi((t0 + t1) / 2); under = (k + 1) * RISER - .18
        ro = rad(0.) - .01 + SW
        L = abs(stair_phi(t1) - stair_phi(t0)) * (ro - SW / 2) - .015
        z = 0.; c = 0
        while z < under - .05:
            hgt = min(.4, under - z)
            ring_block('Stair_Base', mid, rad(z) + SW - .01, z, z + hgt - .006, L, SW, R.choice(P['stone']), 1100 + k * 11 + c, R)
            z += hgt; c += 1


def rubble(P, R):
    # the slope's bed: a height field from the breach out to the corner, under the loose stones
    def fn(u, v):
        phi = THC + (u * 2 - 1) * SPREAD
        rho = rad(1.) - .3 + (rho_max(phi) - rad(1.) + .3) * v
        return (rho * math.cos(phi), rho * math.sin(phi), max(.0, rubble_out(rho, phi) - .08) + .005)
    surface('Rubble_Bed', 40, 16, fn, P['bed'], group='Main', grain='z')
    placed = []; tries = 0
    while len(placed) < 85 and tries < 3000:
        tries += 1
        phi = THC + R.uniform(-1, 1) * SPREAD * .95
        rho = R.uniform(rad(1.) - .1, rho_max(phi) - .25)
        z = rubble_out(rho, phi) if rho > rad(2.) else max(rubble_out(rho, phi), 0.)
        if z < .05 and R.random() < .6: continue
        x, y = rho * math.cos(phi), rho * math.sin(phi)
        s = R.uniform(.22, .62) * (1.15 if z < .6 else 1.)
        if any(math.hypot(x - a, y - b) < (s + sb) * .45 for a, b, sb in placed): continue
        sz = (s, s * R.uniform(.6, .85), s * R.uniform(.45, .7))
        lim = max(abs(x), abs(y)) + s * .55
        if lim > LIM: continue
        rot = (R.uniform(-.5, .5), R.uniform(-.5, .5), R.uniform(0, math.pi)); m = Euler(rot).to_matrix()
        low = sum(abs(m[2][i]) * sz[i] / 2 for i in range(3))
        rbox('Rubble_Stone', (x, y, max(z + sz[2] * .2, low - .01)), sz, R.choice(P['rubble']), r=.03, amp=.02, freq=4., chips=4, hew=2, seed=2000 + len(placed), div=.11,
             rot=rot, group='Main')
        placed.append((x, y, s))
    # inside the breach: the slumped fill is covered in loose stones and a few big wall blocks, closely packed
    inner = []; tries = 0
    while len(inner) < 60 and tries < 3000:
        tries += 1
        phi = THC + R.uniform(-1, 1) * SPREAD * .8; rho = R.uniform(.6, rad(2.) - .05)
        z = rubble_in(rho, phi)
        if z > TOP - .2: continue
        x, y = rho * math.cos(phi), rho * math.sin(phi)
        s = R.uniform(.22, .5) if len(inner) > 8 else R.uniform(.45, .65)
        if any(math.hypot(x - a, y - b) < (s + sb) * .38 for a, b, sb in inner): continue
        rbox('Rubble_Stone', (x, y, z - .06 + s * .2), (s, s * R.uniform(.6, .8), s * R.uniform(.45, .6)), R.choice(P['rubble']), r=.03, amp=.022, chips=3, hew=2,
             seed=2500 + len(inner), div=.12, rot=(R.uniform(-.5, .5), R.uniform(-.5, .5), R.uniform(0, math.pi)), group='Main')
        inner.append((x, y, s))
    S['rubble_n'] = len(placed)


def growth(P, R):
    for k in range(26):         # round the foot
        phi = R.uniform(0, math.tau)
        if breach_a(phi) < .9 and R.random() < .7: continue
        on_stair = -abs(TH1 - TH0) - .05 < ang(phi, TH0) < .05 or ang(phi, TH0) > math.tau - abs(TH1 - TH0)
        rho = R0 + R.uniform(.05, .4) + (SW if on_stair else 0)
        rho = min(rho, rho_max(phi) - .2)
        FP.grass_tuft('Foot_Grass', (rho * math.cos(phi), rho * math.sin(phi), 0.), R.randint(9, 15), R.uniform(.18, .4), P['dry'] if R.random() < .65 else P['grass'], R, lean=.35, detail=1, spread=.05)
    for k in range(14):         # on the top, along the parapet course and between slabs
        phi = R.uniform(0, math.tau)
        if breach_a(phi) < .95: continue
        rho = R.uniform(.6, RT - .5)
        FP.grass_tuft('Top_Grass', (rho * math.cos(phi), rho * math.sin(phi), TOP), R.randint(6, 11), R.uniform(.12, .28), P['dry'], R, lean=.4, detail=1, spread=.04)
    for k in range(18):         # in the wall joints
        phi = R.uniform(0, math.tau); z = R.uniform(.5, TOP - .4)
        if z > wall_top(phi) - .3: continue
        if -2.5 < ang(phi, TH0) < .05 and z < (abs(ang(phi, TH0)) / abs(TH1 - TH0)) * TOP + .3: continue
        r_ = rad(z) + .01
        FP.grass_tuft('Joint_Grass', (r_ * math.cos(phi), r_ * math.sin(phi), min(ZS, key=lambda q: abs(q - z))), R.randint(4, 8), R.uniform(.08, .18), P['dry'], R, lean=.6, detail=1, spread=.02)
    for k in range(16):
        phi = R.uniform(0, math.tau); z = R.uniform(.05, .9)
        FP.moss_patch('Wall_Moss', (rad(z) * math.cos(phi), rad(z) * math.sin(phi), z), (math.cos(phi), math.sin(phi), .1), R.uniform(.12, .25), P['moss'], seed=k)


def build_bt01(P):
    R = random.Random('BT01')
    tower(P, R); core_and_top(P, R); stair(P, R); rubble(P, R); growth(P, R)
    socket('Socket_Lookout', (-.6 * math.cos(THC), -.6 * math.sin(THC), TOP), rot=(0, 0, THC + math.pi / 2))
    f = stair_phi(0.); rf = R0 + SW / 2
    socket('Socket_StairFoot', (rf * math.cos(f), rf * math.sin(f), 0.), rot=(0, 0, f))
    S['collision_mesh'] = collision()
    S['part_notes'] = {'tower': {'radius_foot_m': R0, 'radius_top_m': RT, 'top_z_m': TOP, 'courses': NC, 'wall_thickness_m': WALL_T},
                       'stair': {'risers': NSTEP, 'riser_m': RISER, 'width_m': SW, 'from_deg': math.degrees(TH0), 'to_deg': math.degrees(TH1),
                                 'tread_on_middle_line_m': round(abs(TH1 - TH0) / NSTEP * (R0 + SW / 2 - .15), 3), 'rail': 'none (the sheet\'s timber rail is not made)'},
                       'breach': {'centre_deg': math.degrees(THC), 'floor_z_m': 2.2, 'fan_half_width_deg': math.degrees(SPREAD)},
                       'rubble_stones': S.get('rubble_n'), 'sockets': {'Socket_Lookout': 'on the top, looking out over the breach', 'Socket_StairFoot': 'at the stair foot'}}


def collision():
    V, F = [], []
    # height field over a polar grid: the top (and the slumped fill in the breach), the wall's edge, then the ground and the rubble
    rings = [.5, 1., 1.5, 1.9, 2.2, 2.6, 2.601, 2.9, 3.3, 3.7, 4.1, 4.6, 5.3]
    NPH = 96; idx = {}
    c0 = len(V); V.append((0., 0., TOP))
    for i in range(NPH):
        phi = math.tau * i / NPH; rm = rho_max(phi)
        for j, rho in enumerate(rings):
            rr = min(rho, rm)
            if rho <= 2.6:
                z = rubble_in(rho, phi)
                if breach_a(phi) < .8 and rho > 2.3: z = min(z, wall_top(phi))
            else: z = rubble_out(rr, phi)
            idx[(i, j)] = len(V); V.append((rr * math.cos(phi), rr * math.sin(phi), z))
    for i in range(NPH):          # wound so the faces look up (and out, on the wall's edge)
        k = (i + 1) % NPH
        F.append((c0, idx[(i, 0)], idx[(k, 0)]))
        for j in range(len(rings) - 1):
            F.append((idx[(i, j)], idx[(i, j + 1)], idx[(k, j + 1)], idx[(k, j)]))
    # the stair: a ramp on the nosing line, solid down to the ground
    rings_s = []
    for q in range(NSTEP * 2 + 1):
        t = q / (NSTEP * 2); phi = stair_phi(t); z = t * TOP
        ri, ro = 2.58, rad(0.) + SW
        rings_s.append([(ri * math.cos(phi), ri * math.sin(phi), z), (ro * math.cos(phi), ro * math.sin(phi), z),
                        (ro * math.cos(phi), ro * math.sin(phi), 0.), (ri * math.cos(phi), ri * math.sin(phi), 0.)])
    FP.hull_loft(V, F, rings_s)
    return V, F


def register(ASSETS):
    ASSETS['BT01_OldBeaconTower'] = dict(
        kind='beacon', zh='舊烽台', palette=palette, build=build_bt01, tex=2048, tex_atlas={'Stone': 4096}, ver='v001',
        atlases={'Main': ['Main', 'Detail_Small'], 'Stone': ['Stone']},
        limit=[W, D, H], box=((-W / 2, -D / 2, 0.), (W / 2, D / 2, H)), slot='A7_EastSlope_Ridge_BeaconTower', ref='BT01/BT01-cand-4',
        clamp_max=.03, uv_shape='CONVEX', uv_detach_zero=True, minTier='standard',
        origin='centre of the tower at ground level, z = 0, front -Y',
        note='東坡山脊上塌了一半的圓形乾砌石烽台（三視圖 BT01-cand-4）：圓台底半徑 2.75 m、頂 2.45 m、高 5.4 m，18 層石頭，牆略往內收；右後方的牆塌出一個 V 形缺口（底在 2.2 m），'
             '裡面的填土石塌成一道碎石坡往右後角散開；其餘牆面完整到頂，頂上鋪石板，邊上幾段斷掉的矮垛。一道 0.9 m 寬的石階貼著外牆，從正面繞到左後方上到頂（27 級，每級 0.2 m），'
             '頂上可以站人看風景。石縫和頂上長乾草，牆腳有苔。圖上的木欄杆和木架不做，石階沒有扶手；不寫字。'
             '碰撞：一張高度場（頂面 5.4 m、缺口和碎石坡照實際高低、四周地面）加石階斜坡。',
        method='procedural mesh construction (art/source/roadside-landmarks-b/bt_beacon.py: dry-laid blocks bent to the circle course by course, the breach '
               'and the rubble fan from height fields); procedural stone, moss and grass shaders baked to two 2048 atlases (Main, Stone)',
        based_on='original (Blender procedural); material functions from art/source/village-houses-b')


def beacon_checks(aid, check, cfg):
    from vl_checks import _bvh
    lod0 = S['lods'][0]
    body = _bvh([o for g, o in lod0.items() if not g.startswith('Detail_')])
    down = lambda x, y, f=body: (lambda h: round(h[0].z, 3) if h else None)(f((x, y, 20.), (0, 0, -1)))
    # the stair: tread tops on its middle line climb a riser at a time
    got, exp = [], []
    for k in (1, 7, 13, 19, 25):
        phi = stair_phi((k + .5) / NSTEP); r_ = rad((k + 1) * RISER) + SW / 2
        got.append(down(r_ * math.cos(phi), r_ * math.sin(phi))); exp.append(round((k + 1) * RISER, 2))
    check('stair_climbs', all(g is not None and abs(g - e) < .03 for g, e in zip(got, exp)), {'tread_tops_m': got, 'expected_m': exp})
    # the top: standable paving over most of it, away from the breach
    pts = [(rho * math.cos(math.radians(a)), rho * math.sin(math.radians(a))) for a in range(0, 360, 20) for rho in (.4, 1.0, 1.6)]
    hits = [down(x, y) for x, y in pts]
    flat = sum(1 for h in hits if h is not None and abs(h - TOP) < .03 + .0)
    check('top_standable', flat / len(pts) > .6, {'points': len(pts), 'at_top_level': flat, 'share': round(flat / len(pts), 2), 'top_m': TOP})
    # the arrival: the last tread meets the top
    a = stair_phi(1.); r_ = rad(TOP) - .3
    arrive = down(r_ * math.cos(a), r_ * math.sin(a))
    check('stair_reaches_top', arrive is not None and abs(arrive - TOP) < .05, {'top_beside_last_tread_m': arrive})
    # the breach: rubble on the slope outside it, and the wall still full height away from it
    # (the standing wall is probed at -60 deg, between the stair foot and the breach: straight opposite the breach is the stair)
    sw = math.radians(-60)
    b = down(3.4 * math.cos(THC), 3.4 * math.sin(THC)); far = down(2.25 * math.cos(sw), 2.25 * math.sin(sw))
    check('breach_and_slope', b is not None and .3 < b < 2.6 and far is not None and TOP - .1 < far < TOP + 1., {'slope_at_3.4m_m': b, 'wall_top_at_-60deg_m': far})
    col = _bvh([S['collision_obj']]) if S.get('collision_obj') else None
    out = {'stair_m': got}
    if col:
        ct = col((0., 0., 20.), (0, 0, -1)); phi = stair_phi(.5); r_ = rad(2.7) + SW / 2
        cs = col((r_ * math.cos(phi), r_ * math.sin(phi), 20.), (0, 0, -1))
        check('collision_top_and_stair', ct and cs and abs(ct[0].z - TOP) < .02 and abs(cs[0].z - TOP * .5) < .12,
              {'top_m': round(ct[0].z, 3) if ct else None, 'stair_mid_m': round(cs[0].z, 3) if cs else None})
    return out
