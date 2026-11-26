"""FO02 glowing mushroom clusters (work pack 2026-11-09 B-112h batch C, D5 mushroom valley): three clusters A / B / C,
each inside 1.2 x 1.2 x 0.8 m.

Three-view FO02-cand-1: mushrooms of very different sizes growing together out of moss and dark soil; thick domed caps with a
rolled rim, curved fleshy stems swelling at the foot, real gills under the caps. Muted dark caps; the glow (cyan, emission) only on
the gills, strongest on the gill edges of the inner half and gone at the rim: a small part of the cluster lights.
(The pack: the earlier Codex version was too simple and toy-like; this one is not Eli's GC04 wild mushroom either.)
Proportions from the pack's sizes, not measured off the image (the image's mushrooms are taller).

Each mushroom: a stem swept along a bent curve (a bulb at the foot, a flare under the cap); a cap turned from a profile (dome top,
thick rim rolled under, the gill field arching up to the stem) round 4 x n_gills segments, the rim wavy and the cap tilted with the
stem; the gill field carries the gills as thin plates hanging from it (a sharp ridge every 1 / n_gills of a turn, deepest midway).
Origin: centre of the footprint on the ground. Socket_GlowLight under the biggest cap for the game's cyan point light.
"""
import math, random
from pathlib import Path
import bmesh
from mathutils import Vector, Matrix, noise
from ti_core import S, socket, mesh
import fr_parts as FP
import fr_mats as fm
from cr_parts import set_attr_list

HALF, HMAX = .6, .8


def palette():
    P = FP.palette()
    P['cap'] = [fm.mushroom_cap('Mushroom_Cap_0'), fm.mushroom_cap('Mushroom_Cap_1', tone=(1.12, 1.05, .95))]
    P['stem'] = fm.mushroom_stem('Mushroom_Stem')
    P['gill'] = fm.mushroom_gill('Mushroom_Gill_Glow', slot='Glow')     # own slot: the baked material carries the Emission map
    return P


def _bez(a, b, c, d, t):
    s = 1 - t
    return a * s ** 3 + b * 3 * s * s * t + c * 3 * s * t * t + d * t ** 3


def mushroom(P, name, foot, H, Rc, lean, bend, seed, cap_i=0, detail=0):
    """foot: (x, y) on the ground; H: top of the cap; Rc: cap radius; lean: (dx, dy) of the cap centre from the foot;
    bend: sideways bow of the stem. Returns the cap centre and its underside height."""
    R = random.Random(seed); so = Vector((R.uniform(-40, 40), R.uniform(-40, 40), seed * .31))
    Hc = Rc * R.uniform(.5, .62)                     # cap thickness at the centre (thick dome)
    zr = Rc * .13                                    # rim thickness
    rs = Rc * R.uniform(.2, .25)                     # stem radius under the cap
    gz = Hc * .42                                    # the gill field rises to this height at the stem
    top_z = H - Hc                                   # cap rim plane
    a = Vector((foot[0], foot[1], max(.003, S['ground_h'](*foot) - .025)))   # the foot sinks 2.5 cm into the mound, never below its flat z = 0 base
    d = Vector((foot[0] + lean[0], foot[1] + lean[1], top_z + gz * .6))
    side = Vector((-lean[1], lean[0], 0)); side = side.normalized() if side.length > 1e-6 else Vector((1, 0, 0))
    b = a + Vector((0, 0, (d.z - a.z) * .4)) + side * bend
    c = d - Vector((lean[0], lean[1], 0)) * .25 + Vector((0, 0, -(d.z - a.z) * .3)) - side * bend * .3
    # ---- stem
    n = max(8, int((d - a).length / .02)); nv = max(12, int(rs * 2 * math.pi / .012)) if Rc > .1 else 10
    C = [_bez(a, b, c, d, i / n) for i in range(n + 1)]
    T = [(C[min(n, i + 1)] - C[max(0, i - 1)]).normalized() for i in range(n + 1)]
    N0 = T[0].orthogonal().normalized(); Ns = [N0]
    for i in range(1, n + 1):
        nn = Ns[-1] - Ns[-1].dot(T[i]) * T[i]; Ns.append(nn.normalized())
    V, F, A = [], [], []
    length = sum((C[i + 1] - C[i]).length for i in range(n)); acc = 0.
    for i in range(n + 1):
        if i: acc += (C[i] - C[i - 1]).length
        u = i / n
        r = rs * (1.55 * math.exp(-((u - .02) / .14) ** 2) + .82 + .3 * u ** 6)   # bulb at the foot, slim, flare under the cap
        Bv = T[i].cross(Ns[i])
        for k in range(nv):
            th = math.tau * k / nv
            dv = Ns[i] * math.cos(th) + Bv * math.sin(th)
            rr = r * (1 + .06 * noise.noise(so + Vector((math.cos(th) * 1.4, math.sin(th) * 1.4, acc * 6.))) + .02 * math.sin(th * 7 + acc * 30))
            V.append(tuple(C[i] + dv * rr)); A.append((acc, th * rs, u))
    for i in range(n):
        for k in range(nv):
            p, q = i * nv + k, i * nv + (k + 1) % nv
            F.append((p, q, q + nv, p + nv))
    V.append(tuple(C[0] - Vector((0, 0, .01)))); A.append((0., 0., 0.)); ci = len(V) - 1
    for k in range(nv): F.append(((k + 1) % nv, k, ci))
    V.append(tuple(C[-1] + T[-1] * .01)); A.append((acc, 0., 1.)); ce = len(V) - 1
    for k in range(nv): F.append((n * nv + k, n * nv + (k + 1) % nv, ce))
    st = mesh(f'{name}_Stem', V, F, P['stem'], smooth=True, grain='z', detail=detail)
    set_attr_list(st, 'adze', A)
    # ---- cap: profile (r, z) from the top centre round the rim to the gill field's inner edge, inside the stem
    prof = []
    for j in range(12):                              # dome top
        rho = j / 12
        prof.append((Rc * rho, zr + (Hc - zr) * (1 - rho ** 2) ** .62, 'cap'))
    prof += [(Rc * 1.0, zr * 1.0, 'cap'), (Rc * 1.035, zr * .62, 'cap'), (Rc * 1.02, zr * .2, 'cap'), (Rc * .975, 0., 'cap')]
    ng = max(14, int(Rc * 210)); seg = 4 * ng
    rin = rs * .75
    nu = 9
    for j in range(nu + 1):                          # gill field: from just inside the rim up to the stem
        t = j / nu
        r = Rc * .955 - (Rc * .955 - rin) * t
        prof.append((r, gz * t ** 1.3, 'gill'))
    nring = len(prof)
    tilt_axis = Vector((-lean[1], lean[0], 0)); tilt = math.atan2(math.hypot(*lean), max(.05, H)) * .9
    M = Matrix.Rotation(tilt, 3, tilt_axis.normalized()) if tilt_axis.length > 1e-6 and tilt > 1e-3 else Matrix.Identity(3)
    origin = Vector((d.x, d.y, top_z))
    # the rim is not a lathe circle: it waves up and down a little, and the big caps have split once at the edge
    nwave, wph, wamp = R.randint(5, 8), R.uniform(0, math.tau), Rc * R.uniform(.025, .045)
    notch = (R.uniform(0, math.tau), R.uniform(.07, .12), R.uniform(.09, .14)) if Rc > .17 else None
    V, F, A, MI = [], [], [], []
    for i, (r0, z0, kind) in enumerate(prof):
        for k in range(seg):
            th = math.tau * k / seg
            wob = 1 + .055 * noise.noise(so + Vector((math.cos(th) * 1.1, math.sin(th) * 1.1, 2.))) + .025 * noise.noise(so + Vector((math.cos(th) * 3., math.sin(th) * 3., 5.)))
            rr = r0 * (wob if r0 > Rc * .3 else 1 + (wob - 1) * r0 / (Rc * .3))
            dz = Rc * .05 * noise.noise(so + Vector((math.cos(th) * 1.6, math.sin(th) * 1.6, 9.))) * min(1., r0 / Rc) ** 2
            fr = min(1., r0 / Rc)
            dz += wamp * math.sin(th * nwave + wph + .6 * math.sin(th * 3 + wph)) * fr ** 4
            if notch:
                da = abs((th - notch[0] + math.pi) % math.tau - math.pi)
                if da < notch[1]: rr *= 1 - notch[2] * (1 - da / notch[1]) ** 1.5 * fr ** 6
            z = z0 + dz
            crest = 0.
            if kind == 'gill':
                tg = (Rc * .955 - r0) / max(1e-6, Rc * .955 - rin)                        # 0 at the rim .. 1 at the stem
                ph = (th * ng / math.tau) % 1.
                crest = max(0., 1 - abs(ph - .5) * 2) ** 6                                # a sharp plate every 1 / ng of a turn
                depth = Rc * .16 * math.sin(math.pi * min(1., tg * 1.15)) ** .8
                z -= depth * crest
                A.append((1 - tg, crest, 0.))
            else:
                A.append((min(1., r0 / Rc), 0., 0.))
            if kind == 'cap' and r0 < 1e-6: rr = 0.
            p = Vector((math.cos(th) * rr, math.sin(th) * rr, z))
            V.append(tuple(origin + M @ p))
    for i in range(nring - 1):
        for k in range(seg):
            p, q = i * seg + k, i * seg + (k + 1) % seg
            if prof[i][0] < 1e-6:                    # the top centre: a fan
                F.append((p, p + seg, q + seg) if False else (q + seg, p + seg, p)); MI.append(0); continue
            F.append((p, p + seg, q + seg, q)); MI.append(1 if prof[i][2] == 'gill' and prof[i + 1][2] == 'gill' else 0)
    cp = mesh(f'{name}_Cap', V, F, P['cap'][cap_i], smooth=True, grain='z', detail=detail)
    cp.data.materials.append(P['gill'])
    for poly, m in zip(cp.data.polygons, MI): poly.material_index = m
    set_attr_list(cp, 'adze', A)
    bm = bmesh.new(); bm.from_mesh(cp.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:seg], dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(cp.data); bm.free()
    S.setdefault('caps', []).append(dict(name=name, centre=(d.x, d.y), top=H, rim_z=top_z, R=Rc, Hc=Hc, under=top_z + gz))
    return d, top_z


def base(P, seed, rx, ry):
    """Low mound of dark soil and moss the cluster grows from."""
    so = seed * 1.37
    def h(a, b):
        e = (a / rx) ** 2 + (b / ry) ** 2
        lump = .012 * noise.noise(Vector((a * 7 + so, b * 7, so))) + .006 * noise.noise(Vector((a * 19, b * 19 + so, 2 * so)))
        return max(.004, .07 * max(0., 1 - e) ** 1.4 + lump * max(0., 1 - e))
    def disc(a, b):                                  # square grid -> a round, wobbly outline (no square soil tile under the cluster)
        x, y = a * math.sqrt(max(0., 1 - b * b / 2)), b * math.sqrt(max(0., 1 - a * a / 2))
        th = math.atan2(y, x); cs, sn = math.cos(th), math.sin(th)
        R = .54 + .045 * noise.noise(Vector((cs * 1.3 + so, sn * 1.3, 5.))) + .02 * noise.noise(Vector((cs * 3.5, sn * 3.5 + so, 7.)))
        return (x * R, y * R)
    FP.mound('Soil_Base', lambda a, b: h(*disc(a, b)), -1., 1., -1., 1., P['earth'], nx=40, ny=40, mapfn=disc)
    return h


CLUSTERS = {
    # (foot x, y, cap top H, cap radius, lean dx, dy, bend, cap tone)
    'A': [(.02, .06, .74, .29, .04, .02, .05, 0), (-.27, -.1, .44, .17, -.12, -.06, -.04, 1), (.28, -.12, .36, .15, .11, -.06, .03, 0),
          (-.08, -.3, .18, .085, -.03, -.06, .01, 1), (.1, -.33, .13, .065, .03, -.05, -.01, 0), (-.36, .2, .11, .055, -.04, .02, .01, 0),
          (.33, .22, .08, .04, .02, .03, 0., 1)],
    'B': [(-.15, .08, .62, .25, -.12, .03, .05, 1), (.2, .02, .52, .22, .13, -.02, -.04, 0), (.0, -.27, .3, .13, .01, -.09, .03, 0),
          (-.38, -.18, .16, .075, -.05, -.04, .01, 0), (.36, -.25, .12, .06, .04, -.04, -.01, 1), (.05, .34, .2, .09, .02, .07, .02, 1),
          (-.2, -.36, .08, .04, -.02, -.03, 0., 0)],
    'C': [(-.04, .03, .4, .26, -.02, .02, .03, 0), (-.34, .16, .3, .16, -.11, .05, -.03, 1), (.3, .2, .26, .14, .1, .06, .02, 0),
          (.24, -.24, .29, .1, .09, -.08, -.03, 1), (-.22, -.28, .15, .085, -.06, -.06, .02, 0), (.0, -.4, .1, .05, 0., -.04, 0., 0),
          (.42, -.02, .1, .05, .04, 0., 0., 1), (-.43, -.08, .07, .035, -.03, -.01, 0., 0)],
}


def growth(P, h, seed, caps):
    Rg = random.Random(f'FO02_growth{seed}')
    for i in range(30):                               # moss over the mound, round the stem feet
        a = Rg.uniform(-.48, .48); b = Rg.uniform(-.48, .48)
        if a * a + b * b > .23: continue
        FP.moss_patch('Base_Moss', (a, b, h(a, b) + .002), (0, 0, 1), Rg.uniform(.05, .11), P['moss'], seed=seed * 50 + i, flat=.9)
    def clear(a, b, m):
        return all((a - c['centre'][0]) ** 2 + (b - c['centre'][1]) ** 2 > (c['R'] * .35 + m) ** 2 for c in caps)
    for i in range(14):                               # leaf litter drifted against the mound
        a = Rg.uniform(-.52, .52); b = Rg.uniform(-.5, .5)
        if a * a + b * b > .27 or not clear(a, b, .05): continue
        FP.grass_tuft('Base_Litter', (a, b, h(a, b)), Rg.randint(3, 6), Rg.uniform(.04, .07), P['litter'], Rg, lean=.7, detail=1, spread=.07)
    for i in range(3):                                # a few dead twigs lying across it
        a = Rg.uniform(-.35, .35); b = Rg.uniform(-.35, .35); ang = Rg.uniform(0, math.tau); L = Rg.uniform(.16, .3); r_ = Rg.uniform(.005, .009)
        pts = [(a + math.cos(ang) * L * t, b + math.sin(ang) * L * t) for t in (-.5, 0., .5)]
        if any(x * x + y * y > .24 or not clear(x, y, .02) for x, y in pts): continue
        FP.sweep('Base_Twig', [(x, y, h(x, y) + r_ * .5) for x, y in pts], [r_, r_ * .85, r_ * .6], P['bark'][0], step=.02, fiss=.08, nring=6,
                 seed=seed * 7 + i, ground=None, detail=1)
    nb = 0
    for i in range(12):                               # little buttons just pushing up out of the moss
        if nb >= 3: break
        a = Rg.uniform(-.4, .4); b = Rg.uniform(-.4, .4)
        if a * a + b * b > .16 or not clear(a, b, .08): continue
        r_ = Rg.uniform(.018, .03)
        mushroom(P, f'Mushroom_Button_{nb}', (a, b), h(a, b) + r_ * Rg.uniform(1.6, 2.4), r_, (Rg.uniform(-.01, .01), Rg.uniform(-.01, .01)), 0.,
                 seed * 1000 + 50 + i, cap_i=Rg.randint(0, 1), detail=1)
        nb += 1
    for i in range(5):
        a = Rg.uniform(-.5, .5); b = Rg.uniform(-.5, .5)
        if a * a + b * b > .26 or any((a - c['centre'][0]) ** 2 + (b - c['centre'][1]) ** 2 < (c['R'] * .9) ** 2 for c in caps): continue
        FP.grass_tuft('Base_Grass', (a, b, h(a, b)), Rg.randint(4, 7), Rg.uniform(.08, .16), P['grass'] if Rg.random() < .6 else P['litter'], Rg, lean=.35, detail=1, spread=.03)
    for i in range(2):
        a = Rg.choice((-1, 1)) * Rg.uniform(.3, .38); b = Rg.uniform(-.26, .26)     # inside the soil disc: the fronds stay over it, not drooping past its edge
        FP.fern('Base_Fern', (a, b, h(a, b)), P['fern'], Rg, n=5, L=.17, out=(1 if a > 0 else -1, 0, 0), detail=1, up_bias=.4, spread=.9)
    for i in range(3):
        a = Rg.uniform(-.45, .45); b = Rg.uniform(-.45, .45)
        if a * a + b * b > .2: continue
        sz = Rg.uniform(.04, .07)
        FP.pebble('Base_Stone', (a, b, max(h(a, b) - .005, sz * .5 * 1.12)), sz, Rg.choice(P['stone']), seed=seed * 9 + i, flat=.5, detail=1)


def fo02_cluster(kind):
    def build(P):
        seed = 'ABC'.index(kind) + 1
        S['caps'] = []
        h = base(P, seed, .5, .46); S['ground_h'] = h
        for i, (x, y, H, Rc, lx, ly, bend, ci) in enumerate(CLUSTERS[kind]):
            mushroom(P, f'Mushroom_{i}', (x, y), H, Rc, (lx, ly), bend, seed * 100 + i, cap_i=ci, detail=1 if Rc < .05 else 0)
        growth(P, h, seed, S['caps'])
        big = max(S['caps'], key=lambda c: c['R'])
        socket('Socket_GlowLight', (big['centre'][0], big['centre'][1], big['under'] - .06))
        V, F = [], []                                  # collision: a post up each big cap's stem to its top (players brush past the small ones)
        for c in S['caps']:
            if c['R'] < .12: continue
            x, y, r = c['centre'][0], c['centre'][1], c['R'] * .5           # half the cap: wide enough not to be slid round, still under it
            ring = lambda z: [(x + math.cos(k * math.tau / 8) * r, y + math.sin(k * math.tau / 8) * r, z) for k in range(8)]
            FP.hull_loft(V, F, [ring(0.), ring(max(c['top'], .45))])      # up to the cap top and well over a 0.3 m step: not stepped over
        S['collision_mesh'] = (V, F)
        S['prop'] = dict(kind='mushroom', caps=[dict(c) for c in S['caps']])
    return build


def mushroom_checks(aid, check, cfg):
    """FO02: thick domed caps (measured through each cap by rays), the glow only under the caps and on a small share of the surface."""
    import bpy
    from fr_checks import _bvh
    objs = list(S['lods'][0].values()); down, up, cast = _bvh(objs)
    caps = S['prop']['caps']; thick = []
    for c in caps:
        if c['R'] < .05: continue
        x, y = c['centre'][0] + c['R'] * .45, c['centre'][1]
        t = down(x, y, 2.); h = cast((x, y, c['rim_z'] - .02), (0, 0, 1))
        thick.append([round(c['R'], 3), round(t - h[0].z, 4) if (t is not None and h) else None])
    check('caps_thick_and_domed', all(v is not None and v >= .22 * r for r, v in thick),
          {'cap_radius_and_thickness_at_half_radius_m': thick, 'need': 'thickness >= 0.22 x cap radius at half radius (a domed cap with body, not a disc)'})
    # the glow is measured on what ships: the baked Emission atlas, sampled at each LOD0 face's UV centre (material names are gone after baking)
    import numpy as np
    me_area = glow_area = glow_down = 0.; glow_up = 0.
    em_path = S.get('tex', {}).get('Emission')
    if em_path:
        im = bpy.data.images.load(str(em_path), check_existing=True); W, H = im.size
        px = np.array(im.pixels[:], np.float32).reshape(H, W, 4)[..., :3].max(axis=2)
        for o in objs:
            uv = o.data.uv_layers.active.data if o.data.uv_layers.active else None
            for p in o.data.polygons:
                a = p.area; me_area += a
                if uv is None: continue
                u = sum(uv[li].uv[0] for li in p.loop_indices) / p.loop_total; v = sum(uv[li].uv[1] for li in p.loop_indices) / p.loop_total
                if px[min(H - 1, max(0, int(v * H))), min(W - 1, max(0, int(u * W)))] > .08:
                    nz = (o.matrix_world.to_3x3() @ p.normal).normalized().z
                    glow_area += a; glow_down += a * nz; glow_up += a * (nz > .2)
    share = glow_area / max(me_area, 1e-9); mean_nz = glow_down / max(glow_area, 1e-9); up_share = glow_up / max(glow_area, 1e-9)
    check('glow_only_under_caps', glow_area > 0 and share <= .3 and mean_nz < -.2 and up_share < .05,
          {'glow_surface_share': round(share, 3), 'glow_faces_mean_normal_z': round(mean_nz, 3), 'glow_area_facing_up_share': round(up_share, 3),
           'emission_atlas': Path(str(em_path)).name if em_path else None,
           'note': 'faces whose baked Emission texel (at the UV centre) is above 0.08: a small share of the surface, facing down under the caps'})
    check('sockets_present', 'Socket_GlowLight' in S['sockets'], sorted(S['sockets']))
    return {'mushrooms': len(caps), 'cap_radii_m': sorted(round(c['R'], 3) for c in caps), 'glow_surface_share': round(share, 3), 'sockets': sorted(S['sockets'])}


NOTE = ('發光蕈群（三視圖 FO02-cand-1）：三種叢 A／B／C，每叢在 1.2 × 1.2 × 0.8 m 內，從一小丘深色土和苔長出來。每叢 7–8 朵、大小差很多'
        '（蕈傘半徑 0.04–0.29 m）：蕈傘是有厚度的圓頂，邊緣厚、往內捲，傘緣微波浪、跟著蕈柄歪；傘底是真的放射狀菌褶（一片片薄褶從傘底垂下）。'
        '蕈柄彎、肉質，腳下膨大、傘下微微外擴。傘面暗紫褐、不鮮豔，頂上有苔；只有菌褶發青光（Emission，內半圈的褶緣最亮、到傘緣淡掉），發光面積少。'
        '和 Eli 的普通野菇 GC04 不同：這是 D5 蕈谷的發光大蕈叢。Socket_GlowLight 在最大那朵傘下，給遊戲放一盞青色點光；發光強度由遊戲設定（0 = 不亮）。'
        '碰撞：大朵蕈柄各一根八角柱（做到傘頂、至少 0.45 m 高），小朵不擋。')


def register(ASSETS):
    for k in 'ABC':
        ASSETS[f'FO02_GlowMushroom_{k}'] = dict(zh=f'發光蕈群 {k}', kind='mushroom', palette=palette, build=fo02_cluster(k), limit=(1.2, 1.2, .8), tex=1024,
            ver='v001', box=((-.6, -.6, 0.), (.6, .6, .8)), ref='FO02/FO02-cand-1', slot='D5_MushroomValley', minTier='standard', clamp_max=.03,
            uv_shape='CONVEX', origin='centre of the footprint on the ground', note=NOTE)
