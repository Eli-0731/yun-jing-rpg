"""Build Environment Transition Kit modules in a fresh background Blender session (PHASE 2-4).

  blender -b --python-exit-code 1 --python 05_Scripts/generate_modules.py -- --stage blockout --ids A01,A02,B01,C01,C02 --out 01_Blender/Blockout/blockout_representatives_v01.blend
  blender -b --python-exit-code 1 --python 05_Scripts/generate_modules.py -- --stage final --group A --out 01_Blender/road_edge_modules_v01.blend

blockout: canonical geometry from kit_spec only (no relief noise, no details), flat layer colours.
final:    interior-only micro relief and mask variation, detail objects, LOD1/LOD2, collision proxy and
          the baked PBR materials from 03_Textures/.
Connector boundaries are identical in both stages.  The output .blend is never overwritten.
"""
import sys, math, json, random, zlib
from pathlib import Path
import bpy
from mathutils import Vector, noise
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit_spec as K
import kit_blender as KB


def cli():
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    def get(k, d=None): return a[a.index(k) + 1] if k in a else d
    return get('--stage', 'blockout'), get('--group'), get('--ids'), get('--out')


def seed_of(mid):
    return zlib.crc32(mid.encode()) % 10007


def fbm(x, y, s, sc=0.9, octaves=4):
    return noise.fractal(Vector((x * sc + s, y * sc - s * 0.7, s * 0.31)), 1.0, 2.0, octaves) * 0.6


# ---- final-stage variation (always multiplied by the boundary window, so connectors never change) ----
def amp_of(sf, u, v):
    """Relief amplitude.  Varies smoothly; a jump here would make a step in the surface (and dark shading)."""
    k = sf.kind
    if k in ('road_strip', 'road_full', 'road_end'):
        a = K.end_distance(u, v) if k == 'road_end' else abs(v)
        return 0.010 + 0.018 * K.S((a - 1.35) / 0.35)
    if k in ('bank', 'bank_end'):
        return 0.035 + 0.025 * K.S(-v / 0.4)
    if k == 'c06':
        return 0.006
    a = abs(v); walk = (1.0 - K.S((a - 1.35) / 0.35)) if sf.zone == 'approach' else 0.0
    slope = K.S((-0.02 - K.c_H(u, v)) / 0.12)
    return (0.03 + 0.02 * slope) * (1.0 - walk) + 0.008 * walk


def make_fns(mod, stage):
    s = seed_of(mod['id'])
    def zfun_of(sf):
        if stage == 'blockout': return sf.z
        def z(u, v):
            w = sf.window(u, v)
            if w <= 0: return sf.z(u, v)
            x, y = sf.xy(u, v)
            return sf.z(u, v) + w * amp_of(sf, u, v) * fbm(x, y, s)
        return z
    def mask_of(sf):
        if stage == 'blockout': return sf.mask
        zf = zfun_of(sf); moss_gain = 1.6 if mod.get('variant') in ('stones', 'steep') else 1.0
        def m(u, v):
            wet, grass, gravel, moss = sf.mask(u, v); w = sf.window(u, v)
            if w <= 0: return (wet, grass, gravel, moss)
            x, y = sf.xy(u, v); z = zf(u, v)
            grass += w * 0.28 * fbm(x, y, s + 23, 1.3)
            gravel += w * 0.22 * fbm(x, y, s + 37, 1.6) * (1.0 if sf.walkable(u, v) else 0.4)
            wet += w * 0.15 * fbm(x, y, s + 11, 1.1) * K.S((-0.3 - z) / 0.3)
            if mod.get('variant') == 'riprap':
                gravel = max(gravel, w * K.S((v + 1.55) / 0.12) * K.S((0.02 - v) / 0.1) * (0.75 + 0.5 * fbm(x, y, s + 71, 1.8)))
            slope_or_verge = (sf.kind.startswith('bank') and v < 0.2) or (sf.kind.startswith('road') and abs(v) > 1.6) or (sf.kind == 'c_grid' and z < -0.05)
            if slope_or_verge:
                moss += w * moss_gain * max(0.0, 0.9 * fbm(x, y, s + 51, 1.4) - 0.12)
            return (wet, grass, gravel, moss)
        return m
    return zfun_of, mask_of


# ---- detail helpers --------------------------------------------------------------------------------
def surf_pt(sf, zf, u, v):
    x, y = sf.xy(u, v); return Vector((x, y, zf(u, v)))


def surf_n(sf, zf, u, v, h=1e-3):
    n = (surf_pt(sf, zf, u + h, v) - surf_pt(sf, zf, u - h, v)).cross(surf_pt(sf, zf, u, v + h) - surf_pt(sf, zf, u, v - h))
    return n.normalized()


def scatter(rng, n, urange, vrange, cond=lambda u, v: True, min_dist=0.12, tries=4000):
    pts = []
    for _ in range(tries):
        if len(pts) >= n: break
        u = rng.uniform(*urange); v = rng.uniform(*vrange)
        if not cond(u, v): continue
        if any((u - a) ** 2 + (v - b) ** 2 < min_dist * min_dist for a, b in pts): continue
        pts.append((u, v))
    return pts


class Detail:
    """Per-module detail accumulators.  Named <ID>_<Part>_LOD0 so Unity groups them with LOD0."""

    def __init__(self):
        self.stones = KB.Parts(); self.grass = KB.Parts(); self.rocks = KB.Parts(); self.extra = {}


class Guard:
    """Keeps every detail piece behind the module's entry/exit connector planes.

    A piece (one stone, one grass card) whose vertices cross a plane is removed again, so details never
    intrude into the neighbouring module.  Seam connectors (e.g. the road core edge) are not guarded."""
    planes = []; dropped = 0

    @classmethod
    def arm(cls, mod):
        cls.planes = [(Vector(c['location']), Vector((math.cos(math.radians(c['heading_deg'])), math.sin(math.radians(c['heading_deg'])), 0.0)),
                       1.0 if c['role'] == 'exit' else -1.0) for c in K.connectors(mod) if c['role'] in ('entry', 'exit')]
        cls.dropped = 0

    @classmethod
    def ok(cls, verts):
        return all(sgn * (Vector(p) - loc).dot(d) <= 1e-6 for p in verts for loc, d, sgn in cls.planes)


def guarded(fn):
    def place(parts, *a, **k):
        nv, nf = len(parts.v), len(parts.f)
        fn(parts, *a, **k)
        if Guard.ok(parts.v[nv:]): return True
        del parts.v[nv:]; del parts.f[nf:]; del parts.m[nf:]; del parts.uv[nf:]; del parts.sm[nf:]
        Guard.dropped += 1
        return False
    return place


pebble, grass_card, chunk, rock, dressed_stone = (guarded(f) for f in (KB.pebble, KB.grass_card, KB.chunk, KB.rock, KB.dressed_stone))


def _hanging_card(parts, rng, loc, size=1.0, mat=0):
    w = rng.uniform(0.25, 0.4) * size; hgt = rng.uniform(0.12, 0.22) * size; a0 = rng.uniform(-0.4, 0.4)
    for k in range(2):
        a = a0 + k * 0.9; dx, dy = math.cos(a) * w / 2, math.sin(a) * w / 2
        x, y, z = loc
        quad = [(x - dx, y - dy, z + 0.02), (x + dx, y + dy, z + 0.02), (x + dx, y + dy - 0.04, z - hgt), (x - dx, y - dy - 0.04, z - hgt)]
        parts.add(quad, [(0, 1, 2, 3)], mat, uvs=[[(0, 1), (1, 1), (1, 0), (0, 0)]])


hanging_card = guarded(_hanging_card)


def road_details(mod, sf, zf, mf, rng, D):
    L = sf.L; k = sf.kind; var = mod.get('variant')
    sides = [mod['side']] if k == 'road_strip' else [1, -1]
    ulo, uhi = (0.25, L - 0.25) if k != 'road_end' else (0.25, L - 0.3)
    def on_road(u, v):
        return k != 'road_end' or K.end_distance(u, v) <= K.ROAD_OUTER + 0.15
    for sg in sides:
        for u, v in scatter(rng, 9, (ulo, uhi), (1.55, 1.95), lambda u, v: on_road(u, sg * v), 0.25):
            pebble(D.stones, rng, surf_pt(sf, zf, u, sg * v), rng.uniform(0.025, 0.055), rng.randint(0, 1))
        for u, v in scatter(rng, 2, (ulo + 0.2, uhi - 0.2), (1.8, 2.12), lambda u, v: on_road(u, sg * v), 0.8):
            sz = rng.uniform(0.09, 0.15); p = surf_pt(sf, zf, u, sg * v); n = surf_n(sf, zf, u, sg * v)
            chunk(D.stones, rng, p - n * sz * 0.25, (sz * 1.3, sz, sz * 0.8), n, rng.uniform(0, 6.3), mat=0, roundness=(0.45, 0.7), tilt=0.4)
        for u, v in scatter(rng, 7, (ulo, uhi), (1.85, 2.3), lambda u, v: on_road(u, sg * v) and mf(u, sg * min(v, 2.25))[1] > 0.35, 0.35):
            grass_card(D.grass, rng, surf_pt(sf, zf, u, sg * min(v, 2.25)), rng.uniform(0.75, 1.15))
    if k == 'road_full':
        for u, v in scatter(rng, 6, (ulo, uhi), (-1.1, 1.1), lambda u, v: abs(abs(v) - 0.75) < 0.3, 0.3):
            pebble(D.stones, rng, surf_pt(sf, zf, u, v), rng.uniform(0.018, 0.035), 1)
    if var == 'grass':
        for u, v in scatter(rng, 16, (1.0, L - 0.3), (-1.4, 1.4), lambda u, v: rng.random() < K.S((u - 0.8) / 3.0), 0.35):
            grass_card(D.grass, rng, surf_pt(sf, zf, u, v), rng.uniform(0.55, 0.9))
    if var == 'gravel':
        for u, v in scatter(rng, 48, (0.5, L - 0.2), (-1.45, 1.45), lambda u, v: rng.random() < K.S((u - 0.6) / 3.0), 0.12):
            pebble(D.stones, rng, surf_pt(sf, zf, u, v), rng.uniform(0.015, 0.035), rng.randint(0, 1))
    if var == 'damaged':
        for cs, cv, r in K.CHIPS:
            for u, v in scatter(rng, 4, (cs - r * 0.8, cs + r * 0.8), (abs(cv) - 0.3, min(2.2, abs(cv) + 0.3)), lambda u, v: True, 0.12):
                pebble(D.stones, rng, surf_pt(sf, zf, u, math.copysign(v, cv)), rng.uniform(0.03, 0.06), 0)
        for ps, pv, r, d in K.POTHOLES:
            for t in range(5):
                a = rng.uniform(0, math.tau); rr = r * rng.uniform(0.85, 1.05)
                pebble(D.stones, rng, surf_pt(sf, zf, ps + rr * math.cos(a), pv + rr * math.sin(a)), rng.uniform(0.015, 0.03), 1)
        cracks = KB.Parts()
        for c in range(6):
            u = rng.uniform(0.9, 3.1); v = rng.uniform(-1.1, 1.1); ang = rng.uniform(0, math.tau); pts = []
            for t in range(7):
                ang += rng.uniform(-0.6, 0.6); u += 0.07 * math.cos(ang); v += 0.07 * math.sin(ang)
                if 0.7 < u < 3.3 and abs(v) < 1.3: pts.append((u, v))
            for (ua, va), (ub, vb) in zip(pts, pts[1:]):
                pa = surf_pt(sf, zf, ua, va) + Vector((0, 0, 0.003)); pb = surf_pt(sf, zf, ub, vb) + Vector((0, 0, 0.003))
                d = (pb - pa); side = Vector((-d.y, d.x, 0)).normalized() * 0.006
                cracks.add([pa - side, pb - side, pb + side, pa + side], [(0, 1, 2, 3)], 0)
        D.extra['DET_Cracks'] = (cracks, ['WetSoil'])
    if k == 'road_end':
        for u, v in scatter(rng, 12, (1.0, L - 0.3), (-2.4, 2.4), lambda u, v: 1.75 < K.end_distance(u, v) < 2.4, 0.3):
            grass_card(D.grass, rng, surf_pt(sf, zf, u, max(-2.25, min(2.25, v))), rng.uniform(0.75, 1.1))


def bank_details(mod, sf, zf, mf, rng, D):
    L = sf.L; var = mod.get('variant'); k = sf.kind
    n_grass = 40 if var == 'grassy' else 10
    vlo = -1.0 if var == 'grassy' else 0.2
    for u, v in scatter(rng, n_grass, (0.25, L - 0.25), (vlo, 0.95), lambda u, v: mf(u, v)[1] > 0.3 or var == 'grassy', 0.28 if var != 'grassy' else 0.2):
        grass_card(D.grass, rng, surf_pt(sf, zf, u, v), rng.uniform(0.75, 1.2) * (1.15 if var == 'grassy' else 1.0))
    for u, v in scatter(rng, {'stones': 20, 'riprap': 4}.get(var, 10), (0.25, L - 0.25), (-1.65, -1.2), lambda u, v: True, 0.18):
        pebble(D.stones, rng, surf_pt(sf, zf, u, v), rng.uniform(0.025, 0.06), rng.randint(0, 1))
    if var == 'stones':
        for u, v in scatter(rng, 9, (0.4, L - 0.4), (-1.4, 0.2), lambda u, v: True, 0.4):
            sz = rng.uniform(0.08, 0.17); p = surf_pt(sf, zf, u, v); n = surf_n(sf, zf, u, v)
            chunk(D.stones, rng, p - n * sz * 0.3, (sz * 1.3, sz, sz * 0.55), n, rng.uniform(0, 6.3), mat=0,
                     roundness=(0.45, 0.7), rough=0.2, tilt=0.2, dome=0.1)
    elif k == 'bank':
        for i, (u, v) in enumerate(scatter(rng, 4, (0.6, L - 0.6), (-1.55, -0.45), lambda u, v: True, 0.7)):
            sz = rng.uniform(0.10, 0.17); p = surf_pt(sf, zf, u, v); n = surf_n(sf, zf, u, v)
            chunk(D.stones, rng, p - n * sz * 0.3, (sz * 1.35, sz, sz * 0.55), n, rng.uniform(0, 6.3), mat=0,
                     roundness=(0.45, 0.7), tilt=0.2, dome=0.1)
    if var == 'gentle':
        for i, (u, v) in enumerate([(1.55, 0.35), (1.85, -0.2), (2.2, -0.7), (2.5, -1.15)]):
            p = surf_pt(sf, zf, u, v); n = surf_n(sf, zf, u, v)
            rock(D.rocks, rng, p - n * 0.02, (0.24, 0.19, 0.05), subdiv=2, flatten=0.2, base_mat=0, normal_up=n)
    if var == 'steep':
        for u, v in scatter(rng, 8, (0.95, 3.05), (-0.95, -0.25), lambda u, v: True, 0.45):
            sz = rng.uniform(0.22, 0.4); p = surf_pt(sf, zf, u, v); n = surf_n(sf, zf, u, v)
            chunk(D.rocks, rng, p - n * sz * 0.35, (sz * 1.3, sz, sz * 0.8), n, rng.uniform(0, 6.3), mat=0, moss_mat=1, moss_cut=0.55,
                     roundness=(0.4, 0.6), rough=0.22, tilt=0.35, dome=0.2, cuts=2)
    if var == 'riprap':   # dry-laid stone revetment: mixed rounded stones sunk into a gravel bed, ragged ends that fade into the bank
        for row, vc in enumerate((-0.08, -0.39, -0.70, -1.01, -1.32)):
            u0, u1 = rng.uniform(0.15, 0.85), L - rng.uniform(0.15, 0.85)      # each row starts and stops at a different place
            u = rng.uniform(0.10, 0.30)
            while u < L - 0.08:
                big = rng.random() < 0.7
                lx = rng.uniform(0.26, 0.38) if big else rng.uniform(0.14, 0.22)
                inside = u0 <= u <= u1
                if inside or rng.random() < 0.18:                                # a few stragglers beyond the ragged end
                    v = vc + rng.uniform(-0.08, 0.08); p = surf_pt(sf, zf, u, v); n = surf_n(sf, zf, u, v)
                    for shrink in (1.0, 0.8, 0.62):   # next to a connector face the stone shrinks until it stays inside
                        sz = (lx * shrink, lx * rng.uniform(0.75, 0.95) * shrink, rng.uniform(0.17, 0.24) * (1.0 if big else 0.7))
                        if chunk(D.rocks, rng, p - n * sz[2] * 0.30, sz, n, rng.uniform(0, math.tau), mat=0,
                                 roundness=(0.55, 0.78), rough=0.25, tilt=0.18, dome=0.25, facets=(1, 3)): break
                u += lx * rng.uniform(0.92, 1.05) if inside else lx * 1.6
    if var == 'grassy':
        sod = KB.Parts(); us = [0.5 + 0.25 * i for i in range(13)]
        for ua, ub in zip(us, us[1:]):
            a1 = surf_pt(sf, zf, ua, 0.18) + Vector((0, 0, 0.03)); b1 = surf_pt(sf, zf, ub, 0.18) + Vector((0, 0, 0.03))
            a2 = surf_pt(sf, zf, ua, 0.0) + Vector((0, 0, 0.012)); b2 = surf_pt(sf, zf, ub, 0.0) + Vector((0, 0, 0.012))
            a2 = Vector((a2.x, a2.y - 0.14, a2.z)); b2 = Vector((b2.x, b2.y - 0.14, b2.z))
            t = Vector((0, 0, 0.06))
            sod.add([a1, b1, b2, a2, a1 - t, b1 - t, b2 - t, a2 - t], [(0, 1, 2, 3), (7, 6, 5, 4), (3, 2, 6, 7), (0, 3, 7, 4), (1, 0, 4, 5), (2, 1, 5, 6)], 0)
            for j in range(2):
                uu = rng.uniform(ua, ub); hanging_card(D.grass, rng, tuple(surf_pt(sf, zf, uu, 0.0) + Vector((0, -0.13, 0.0))), 1.0)
        D.extra['SodLip_LOD0'] = (sod, ['Grass'])
    if var == 'eroded':
        for sc, hw, d in K.RILLS:
            for t in range(5):
                pebble(D.stones, rng, surf_pt(sf, zf, sc + rng.uniform(-hw, hw) * 0.5, rng.uniform(-1.35, -0.2)), rng.uniform(0.02, 0.04), 0)


def c_details(mod, surfs, zfs, mfs, rng, D):
    mid = mod['id']
    for sf, zf, mf in zip(surfs, zfs, mfs):
        x0, x1, y0, y1 = getattr(sf, 'rect', (0.0, 1.5, -K.DECK_HALF, K.DECK_HALF))   # C06 has its own frame, no rect
        if mid == 'SM_Bridgehead_RoadTransition_A':
            for sg in (1, -1):
                for u, v in scatter(rng, 5, (0.2, 1.8), (1.55, 1.95), lambda u, v: True, 0.25):
                    pebble(D.stones, rng, surf_pt(sf, zf, u, sg * v), rng.uniform(0.025, 0.05), rng.randint(0, 1))
                for u, v in scatter(rng, 5, (0.2, 1.8), (1.9, 2.22), lambda u, v: True, 0.3):
                    grass_card(D.grass, rng, surf_pt(sf, zf, u, sg * v), rng.uniform(0.75, 1.0))
        elif mid in ('SM_Bridgehead_SideTrim_L_A', 'SM_Bridgehead_SideTrim_R_A'):
            sg = 1 if y0 > 0 else -1
            for u, v in scatter(rng, 10, (0.2, 1.8), (2.32, 2.98), lambda u, v: True, 0.25):
                grass_card(D.grass, rng, surf_pt(sf, zf, u, sg * v), rng.uniform(0.8, 1.2))
            for u, v in scatter(rng, 5, (0.25, 1.75), (2.4, 2.9), lambda u, v: True, 0.35):
                sz = rng.uniform(0.07, 0.12); p = surf_pt(sf, zf, u, sg * v); n = surf_n(sf, zf, u, sg * v)
                chunk(D.stones, rng, p - n * sz * 0.25, (sz * 1.3, sz, sz * 0.8), n, rng.uniform(0, 6.3), mat=0, roundness=(0.45, 0.7), tilt=0.4)
        elif mid == 'SM_Bridgehead_BankTransition_A':
            sg = 1 if y0 > 0 else -1; a0, a1 = sorted((abs(y0), abs(y1)))
            for u, v in scatter(rng, 9, (2.1, 2.95), (a0 + 0.1, a1 - 0.35), lambda u, v: True, 0.28):
                grass_card(D.grass, rng, surf_pt(sf, zf, u, sg * v), rng.uniform(0.8, 1.15))
            for u, v in scatter(rng, 7, (4.2, 4.6), (a0 + 0.1, a1 - 0.1), lambda u, v: True, 0.2):
                pebble(D.stones, rng, surf_pt(sf, zf, u, sg * v), rng.uniform(0.025, 0.055), rng.randint(0, 1))
            u, v = 3.6, sg * (a0 + a1) / 2; sz = 0.14; n = surf_n(sf, zf, u, v)
            chunk(D.stones, rng, surf_pt(sf, zf, u, v) - n * sz * 0.3, (sz * 1.3, sz, sz * 0.8), n, rng.uniform(0, 6.3), mat=0,
                     roundness=(0.45, 0.7), tilt=0.35, dome=0.25)
        elif mid == 'SM_Bridgehead_WaterEdge_A':
            for u, v in scatter(rng, 40, (3.35, 4.9), (-2.15, 2.15), lambda u, v: mf(u, v)[2] > 0.3 or rng.random() < 0.3, 0.16):
                pebble(D.stones, rng, surf_pt(sf, zf, u, v), rng.uniform(0.02, 0.05), rng.randint(0, 1))
            for y in (-1.0, 0.1, 1.05):      # scour boulders as close to the stone base as the X=3.25 plane allows
                sz = rng.uniform(0.2, 0.28)
                for step in range(20):
                    u = 3.45 + 0.04 * step; n = surf_n(sf, zf, u, y)
                    if rock(D.rocks, rng, surf_pt(sf, zf, u, y) - n * sz * 0.35, (sz * 1.3, sz, sz * 0.8), subdiv=2, moss_mat=1, base_mat=0, normal_up=n, facets=3): break
        elif mid == 'SM_Bridgehead_CornerCap_A':
            sg = 1 if y0 > 0 else -1
            for i in range(5):
                x = K.RAMP_L + 0.08 + i * 0.235; zt = max(K.c_H(x + 0.11, sg * 1.6), K.DECK_BOTTOM) + 0.03
                dressed_stone(D.rocks, rng, (x + 0.11, sg * 1.6, (zt + (-0.12)) / 2), (0.22, 0.19, zt + 0.12), bevel=0.018, mat=0)
            zq = max(K.c_H(K.BASE_FACE_X, sg * 1.6), K.DECK_BOTTOM) + 0.06
            dressed_stone(D.rocks, rng, (K.BASE_FACE_X - 0.125, sg * 1.62, (zq - 0.55) / 2), (0.24, 0.26, zq + 0.55), bevel=0.022, mat=0, moss_mat=1)
            for u, v in scatter(rng, 4, (2.35, 2.9), (1.85, 2.2), lambda u, v: True, 0.25):
                grass_card(D.grass, rng, surf_pt(sf, zf, u, sg * v), rng.uniform(0.7, 1.0))
        elif mid == 'SM_Bridgehead_SlopeFix_A':
            for sg in (1, -1):
                for u, v in scatter(rng, 3, (0.2, 1.3), (1.3, 1.45), lambda u, v: True, 0.25):
                    pebble(D.stones, rng, surf_pt(sf, zf, u, sg * v), rng.uniform(0.02, 0.04), 0)


def masonry(rng, final):
    """C05 stone base: two courses under the test deck, top Z=-0.05, front face X=3.25.

    Final stage returns (LOD0 chamfered cut stones over a recessed mortar core, LOD1 plain blocks)."""
    P = KB.Parts()
    if not final:
        KB.block(P, ((K.RAMP_L + K.BASE_FACE_X) / 2, 0.0, -0.30), (K.BASE_FACE_X - K.RAMP_L, 2 * K.DECK_HALF, 0.5), mat=0)
        return P, None
    L1 = KB.Parts(); x0, x1 = K.RAMP_L, K.BASE_FACE_X; depth = x1 - x0
    KB.block(P, ((x0 + x1) / 2 + 0.005, 0.0, -0.30), (depth - 0.07, 2 * K.DECK_HALF - 0.04, 0.49), mat=0)   # mortar core seen in the joints, recessed 4 cm from the back and 3 cm from the front so no face is coplanar with a stone
    for zc, hgt, widths in ((-0.175, 0.25, (0.62, 0.55, 0.70, 0.48, 0.65)), (-0.425, 0.25, (0.45, 0.66, 0.58, 0.72, 0.59))):
        y = -K.DECK_HALF
        for w in widths:
            inset = rng.uniform(0.0, 0.014)       # hand-laid faces, never proud of the X=3.25 plane
            KB.dressed_stone(P, rng, (x0 + (depth - inset) / 2, y + w / 2, zc), (depth - inset, w - 0.014, hgt - 0.012),
                             bevel=rng.uniform(0.022, 0.034), mat=0)
            KB.block(L1, ((x0 + x1) / 2, y + w / 2, zc), (depth - 0.01, w - 0.012, hgt - 0.01), mat=0)
            y += w
    return P, L1


# ---- module assembly -------------------------------------------------------------------------------
def slot_of(mod):
    if mod['code'] in ('A01', 'A02'): return 'A_straight'
    if mod['group'] == 'C' and mod['kind'] != 'c06': return 'C_bridgehead'
    return mod['code']


def mats_for(stage):
    if stage == 'blockout':
        b = KB.blockout_material(); r = KB.flat_material('M_Blockout_Rock', (0.30, 0.31, 0.31))
        return {'terrain': b, 'Rock': r, 'Moss': r, 'PathGravel': r, 'Grass': b, 'GrassCard': b, 'WetSoil': r, 'DrySoil': b}
    m = {layer: KB.pbr_material(layer) for layer in KB.LAYERS}
    m['terrain'] = KB.terrain_material(); m['GrassCard'] = KB.grass_card_material()
    return m


def tri_count(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def build_module(mod, stage, parent_coll, loc, M, report):
    mid = mod['id']; final = stage == 'final'; rng = random.Random(seed_of(mid)); Guard.arm(mod)
    coll = bpy.data.collections.new(mid); parent_coll.children.link(coll)
    root = bpy.data.objects.new(mid, None); coll.objects.link(root); root.location = loc
    root.empty_display_type = 'ARROWS'; root.empty_display_size = 0.6
    cons = K.connectors(mod)
    root['kit_module_id'] = mid; root['kit_code'] = mod['code']; root['kit_stage'] = stage; root['kit_version'] = K.KIT_VERSION
    root['kit_pivot'] = 'bridgehead frame origin (C01 road entry)' if mod['group'] == 'C' and mod['kind'] != 'c06' else 'entry connector (0,0,0)' if mod['kind'] != 'c06' else 'ground below high edge'
    root['kit_connectors'] = json.dumps([{k: c[k] for k in ('name', 'role', 'type', 'location', 'heading_deg')} for c in cons])
    made = []
    if mod['kind'] == 'c_base':
        P, L1 = masonry(rng, final)
        made.append(P.build(mid + '_Masonry_LOD0', [M['Rock'], M['Moss']], coll, root))
        if final:
            made.append(L1.build(mid + '_Masonry_LOD1', [M['Rock']], coll, root))
            box = KB.Parts(); KB.block(box, ((K.RAMP_L + K.BASE_FACE_X) / 2, 0.0, -0.30), (K.BASE_FACE_X - K.RAMP_L, 2 * K.DECK_HALF, 0.5))
            made.append(box.build(mid + '_Masonry_LOD2', [M['Rock']], coll, root))
            col = box.build(mid + '_COL', [], coll, root); col.hide_render = True; col.display_type = 'WIRE'; made.append(col)
    else:
        surfs = [K.Surface(mod, i) for i in range(len(mod['parts']))] if mod['kind'] == 'c_grid' else [K.Surface(mod)]
        zfun_of, mask_of = make_fns(mod, stage)
        made.append(KB.lattice_multi(mid + '_Terrain_LOD0', surfs, zfun_of, mask_of, coll, root, [M['terrain']]))
        if final:
            made.append(KB.lattice_multi(mid + '_Terrain_LOD1', surfs, zfun_of, mask_of, coll, root, [M['terrain']], ku=2))
            made.append(KB.lattice_multi(mid + '_Terrain_LOD2', surfs, zfun_of, mask_of, coll, root, [M['terrain']], ku=4, kv=2))
            col = KB.lattice_multi(mid + '_COL', surfs, zfun_of, mask_of, coll, root, [], ku=4, kv=2)
            col.hide_render = True; col.display_type = 'WIRE'; made.append(col)
            D = Detail(); zfs = [zfun_of(sf) for sf in surfs]; mfs = [mask_of(sf) for sf in surfs]
            if mod['kind'].startswith('road'): road_details(mod, surfs[0], zfs[0], mfs[0], rng, D)
            elif mod['kind'].startswith('bank'): bank_details(mod, surfs[0], zfs[0], mfs[0], rng, D)
            else: c_details(mod, surfs, zfs, mfs, rng, D)
            for name, parts, mats in (('DET_Stones_LOD0', D.stones, [M['Rock'], M['PathGravel'], M['Moss']]),
                                      ('DET_Grass_LOD0', D.grass, [M['GrassCard']]),
                                      ('Rocks_LOD0', D.rocks, [M['Rock'], M['Moss']])):
                ob = parts.build('%s_%s' % (mid, name), mats, coll, root, smooth=(name != 'DET_Grass_LOD0'), uv_mode='given' if 'Grass' in name else 'box',
                                 sharp_angle=None if 'Grass' in name else 40.0)
                if ob: made.append(ob)
                if ob and name == 'Rocks_LOD0':
                    made.append(KB.decimated_copy('%s_Rocks_LOD1' % mid, ob, 0.5, coll, root))
            for name, (parts, layers) in D.extra.items():
                tag = name if name.endswith('_LOD0') else name + '_LOD0'
                ob = parts.build('%s_%s' % (mid, tag), [M[x] for x in layers], coll, root)
                if ob: made.append(ob)
    for o in made:   # only LOD0 parts are visible/rendered in the kit file; LOD1/LOD2/COL stay exportable
        if o.name.endswith(('_LOD1', '_LOD2', '_COL')):
            o.hide_render = True; o.hide_set(True)
    report[mid] = {'objects': [o.name for o in made], 'tris': {o.name: tri_count(o) for o in made if o.type == 'MESH'},
                   'lod0_tris': sum(tri_count(o) for o in made if o.type == 'MESH' and o.name.endswith('_LOD0')),
                   'details_dropped_at_connectors': Guard.dropped if final else 0}
    return root


def test_objects(scene, M, slots):
    coll = bpy.data.collections.new('COL_TEST_Only'); scene.collection.children.link(coll); coll['test_only'] = True
    mt = KB.test_material(); deck_m = KB.test_material('M_TEST_Deck', (0.42, 0.40, 0.50))
    if 'A_straight' in slots:
        sx = slots['A_straight']
        core = KB.Parts(); us = K.steps(0.0, 4.0, 0.25); vs = K.CORE_V
        verts = [(sx[0] + u, sx[1] + v, 0.0) for u in us for v in vs]; nv = len(vs)
        faces = [(i * nv + j, (i + 1) * nv + j, (i + 1) * nv + j + 1, i * nv + j + 1) for i in range(len(us) - 1) for j in range(nv - 1)]
        core.add(verts, faces, 0); core.build('TEST_RoadCore_3m', [mt], coll, None)
    if 'C_bridgehead' in slots:
        sx = slots['C_bridgehead']; d = KB.Parts()
        KB.block(d, (sx[0] + K.RAMP_L + 3.0, sx[1], (K.DECK_Z + K.DECK_BOTTOM) / 2), (6.0, 2 * K.DECK_HALF, K.DECK_Z - K.DECK_BOTTOM))
        d.build('TEST_BridgeDeck_3m', [deck_m], coll, None)
    cube = KB.Parts(); KB.block(cube, (-3.0, -3.0, 0.5), (1.0, 1.0, 1.0)); cube.build('TEST_ScaleCube_1m', [mt], coll, None)
    return coll


def main():
    stage, group, ids, out = cli()
    assert stage in ('blockout', 'final') and out, 'usage: -- --stage blockout|final (--group A|B|C | --ids A01,B01) --out <path inside kit>'
    scene = KB.start_session()
    out_path = KB.new_output(out)
    mods = [m for m in K.MODULES if (group and m['group'] in group.split(',')) or (ids and m['code'] in ids.split(','))]
    assert mods, 'no modules selected'
    M = mats_for(stage)
    kit_coll = bpy.data.collections.new('KIT_Modules'); scene.collection.children.link(kit_coll)
    slots = {}; row = {'A': 0.0, 'B': -12.0, 'C': -26.0}
    for mod in mods:
        key = slot_of(mod)
        if key not in slots:
            n = sum(1 for k in slots if k[0] == mod['group'])
            slots[key] = (n * 9.0, row[mod['group']], 0.0)
    report = {}
    for mod in mods:
        build_module(mod, stage, kit_coll, slots[slot_of(mod)], M, report)
        print('BUILT', mod['code'], mod['id'], report[mod['id']]['lod0_tris'], flush=True)
    test_objects(scene, M, slots)
    scene['kit_stage'] = stage; scene['kit_version'] = K.KIT_VERSION; scene['kit_report'] = json.dumps(report)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.context.view_layer.update()             # store correct world matrices for the parented parts
    bpy.ops.wm.save_as_mainfile(filepath=str(out_path))
    bpy.ops.file.make_paths_relative()          # textures referenced as //../03_Textures/... so the kit folder can move
    bpy.ops.wm.save_mainfile()
    (out_path.with_suffix('.build.json')).write_text(json.dumps({'stage': stage, 'blender': bpy.app.version_string, 'modules': report, 'slots': slots}, indent=2))
    print('SAVED', out_path, flush=True)


if __name__ == '__main__':
    main()
