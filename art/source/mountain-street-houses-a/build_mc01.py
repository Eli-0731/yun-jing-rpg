"""承天 · 11/05 A 包 MC01 山城街屋模組（Johnnnny0823）。樣品批：SB01 石基直段、SF01 開敞店面、RF01 歇山屋頂。
Exports go to art/exports/mountain-street-houses-a (the 11/08 SF street furniture uses mountain-street-a).

All modules share ONE 2048 trim sheet (D3 §4: 共用同一組 2048 材質才能合批): M_MountainStreet_Trim, plus M_MountainStreet_Glow
for lantern paper. The trim sheet is composed from the same painterly tileable sources the 11/03 world models used, one
horizontal strip per surface (granite, cedar, plaster, tile, bronze, cloth, paper, dark), all at 256 px/m. Each part is
UV-projected onto its strip in its own frame (grain along the part's long axis); strips tile along U, V stays inside the strip.
4 m grid; origin at the footprint centre, bottom at z = 0, Blender -Y is the street front. LOD0 keeps the full modelled
detail (quality-tiers: LOD0 not reduced); LOD1 ~50 % (<=100k), LOD2 ~15 % (<=25k). Groups: the merged main mesh, Detail_*
(removable dressing, listed in model_info.detailObjects) and Glow (emissive lantern paper).
Each module is modelled only after its four AI three-view candidates are saved in art/references/<ID>/ and one is picked
("選用：" in prompt.txt).

    blender -b --factory-startup -P build_mc01.py -- trim SB01 SF01 RF01 [assembly]
"""
import bpy, bmesh, json, math, sys, random
from pathlib import Path
from mathutils import Vector, Matrix
import numpy as np

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; PKG = 'mountain-street-houses-a'
TEX = ROOT / 'art/textures' / PKG; OUT = ROOT / 'art/exports' / PKG; PRE = ROOT / 'art/previews' / PKG
for p in (TEX, OUT, PRE): p.mkdir(parents=True, exist_ok=True)
LIMITS = {'DT05': (4.0, .36, .2), 'DT06': (.7, .16, .9), 'DT03': (.4, .4, .7), 'DT04': (2.5, .4, 1.3), 'DT01': (.6, .6, 2.5), 'DT02': (1.0, .2, 1.8), 'CP01': (4.0, 3.0, 3.1), 'CP02': (4.0, 3.0, 3.1), 'RF02': (4.0, 5.8, 2.6), 'RF03': (5.6, 5.8, 2.6), 'RF04': (4.0, 5.8, 2.6), 'HM01': (4, 4, 3), 'HM02': (4, 4, 3), 'HM03': (4, 4, 3), 'SF02': (4, 4, 3), 'SF03': (4, 4, 3), 'SB01': (4, 4, 2), 'SB02': (4, 4, 2), 'SB03': (4, 4, 2), 'SB04': (4, 4, 2), 'SB05': (4, 4, 1), 'SF01': (4, 4, 3), 'RF01': (5.8, 5.8, 2.6)}   # RF: 4 m bay + 0.7 m eave overhang + ridge ornaments
TIER = {'DT05': 'low', 'DT06': 'low', 'DT03': 'low', 'DT04': 'low', 'DT01': 'low', 'DT02': 'low', 'CP01': 'low', 'CP02': 'low', 'RF02': 'low', 'RF03': 'low', 'RF04': 'low', 'HM01': 'low', 'HM02': 'low', 'HM03': 'low', 'SF02': 'low', 'SF03': 'low', 'SB01': 'low', 'SB02': 'low', 'SB03': 'low', 'SB04': 'low', 'SB05': 'low', 'SF01': 'low', 'RF01': 'low'}
GRID = 4.0

# ------------------------------------------------------------------ trim sheet
R = 512; rng = np.random.default_rng(1105)
def tile_noise(cx, cy):
    g = rng.random((cy, cx)); x = np.linspace(0, cx, R, endpoint=False); y = np.linspace(0, cy, R, endpoint=False)
    xi = x.astype(int); yi = y.astype(int); fx = x - xi; fy = y - yi; fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy)
    a = g[np.ix_(yi % cy, xi % cx)]; b = g[np.ix_(yi % cy, (xi + 1) % cx)]; c = g[np.ix_((yi + 1) % cy, xi % cx)]; d = g[np.ix_((yi + 1) % cy, (xi + 1) % cx)]
    fx = fx[None, :]; fy = fy[:, None]; return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy
def fbm(c0, oct=4, aniso=1):
    v = 0; amp = .5; tot = 0
    for o in range(oct): v = v + amp * tile_noise(c0 * 2 ** o, max(1, int(c0 * 2 ** o / aniso))); tot += amp; amp *= .5
    return v / tot
def lerp(a, b, t): return np.asarray(a)[None, None, :] * (1 - t[..., None]) + np.asarray(b)[None, None, :] * t[..., None]
X = np.arange(R)[None, :] / R; Y = np.arange(R)[:, None] / R
def strokes(c, aniso, lo=.62): return np.clip((fbm(c, 2, aniso) - lo) * 4, 0, 1)

def sources():
    """512² tileable painterly sources: (albedo, height, normal strength, roughness, metallic, glow). Grain runs along X (= U)."""
    S = {}; soft = fbm(2, 3); warp = fbm(2, 2)
    big = fbm(3, 4); lich = np.clip((fbm(40, 2) - .72) * 5, 0, 1); st = strokes(5, 3, .6); blot = np.clip((fbm(2, 3) - .45) * 2.2, 0, 1)
    gt = np.clip(big * .8 + .25 * blot + .15 * st - .05, 0, 1)
    # granite #C9C6BD family (D3 §0), warm-grey with soft painted patches; a mossy/stained variant for low courses
    S['granite'] = (lerp((.50, .49, .46), (.80, .78, .73), gt) * (1 - .08 * lich[..., None]) + lich[..., None] * np.array([.05, .07, .02]), big + .5 * fbm(24, 2) + .6 * lich, 3.0, .88, 0, 0)
    moss = np.clip((fbm(6, 3) - .60) * 2.6, 0, 1); stain = np.clip((fbm(3, 2, aniso=.3) - .45) * 2, 0, 1) * (1 - Y) ** 1.5
    S['granite_moss'] = (lerp((.44, .43, .40), (.72, .70, .65), gt) * (1 - .22 * stain[..., None]) * (1 - .6 * moss[..., None]) + moss[..., None] * np.array([.17, .24, .09]), big + .5 * fbm(24, 2) + .9 * moss, 3.2, .92, 0, 0)
    S['granite_top'] = (lerp((.56, .54, .50), (.84, .82, .76), np.clip(big * .7 + .3 * soft, 0, 1)), .6 * big + .3 * fbm(16, 2), 2.0, .74, 0, 0)
    # cedar: aged dark brown, long grain along X
    grain = (.5 + .5 * np.sin(math.tau * (Y * 7 + warp * .6))) ** 2; cr = np.clip((fbm(30, 2, aniso=1 / 14) - .70) * 6, 0, 1); st2 = strokes(6, 1 / 6)
    t = np.clip(.50 + .30 * (soft - .5) * 2 - .12 * grain + .12 * st2 - .30 * cr, 0, 1)
    S['plank'] = (lerp((.24, .16, .11), (.46, .32, .21), t) * (1 - .35 * ((Y * 4) % 1 < .03))[..., None], .5 * grain + 1.5 * ((Y * 4) % 1 < .03) + cr, 2.6, .8, 0, 0)
    S['beam'] = (lerp((.20, .13, .09), (.40, .27, .17), t), .5 * grain + 1.2 * cr + .3 * st2, 2.4, .74, 0, 0)
    S['oldwood'] = (lerp((.28, .24, .20), (.52, .46, .38), np.clip(t * 1.1 - .05, 0, 1)) * (1 - .25 * cr[..., None]), .8 * grain + 1.6 * cr, 2.8, .86, 0, 0)
    # lime plaster with rain streaks
    streak = np.clip((fbm(8, 2, aniso=.12) - .55) * 3, 0, 1) * (.4 + .6 * Y)
    S['plaster'] = (lerp((.72, .68, .60), (.90, .87, .80), np.clip(soft * .7 + .3 * fbm(10, 2), 0, 1)) * (1 - .18 * streak[..., None]), .4 * fbm(20, 3) + .3 * streak, 1.2, .9, 0, 0)
    # roof tile 黛瓦 #3A4048
    S['tile'] = (lerp((.17, .19, .22), (.32, .36, .40), np.clip(soft * .8 + .2 * strokes(8, 2), 0, 1)), fbm(20, 2), 1.4, .72, 0, 0)
    tm = np.clip((fbm(5, 3) - .5) * 2.4, 0, 1)
    S['tile_moss'] = (lerp((.17, .19, .22), (.32, .36, .40), soft) * (1 - .6 * tm[..., None]) + tm[..., None] * np.array([.14, .20, .08]), fbm(20, 2) + .6 * tm, 1.6, .8, 0, 0)
    S['bronze'] = (lerp((.22, .18, .11), (.44, .35, .19), np.clip(soft + .15 * fbm(12, 2), 0, 1)) + np.clip((fbm(6, 3) - .6) * 3, 0, 1)[..., None] * np.array([.04, .13, .10]), fbm(14, 3), 1.2, .45, .75, 0)
    S['cloth'] = (lerp((.12, .18, .30), (.20, .28, .42), np.clip(soft * .7 + .3 * (1 - Y) ** 2, 0, 1)) * (1 - .05 * (np.sin(X * 900) > .6))[..., None], .5 * np.sin(X * 700) + .5 * np.sin(Y * 700), .7, .95, 0, 0)
    S['paper'] = (lerp((.86, .74, .52), (.97, .88, .66), fbm(4, 3)) * (1 - .12 * np.clip((fbm(10, 2) - .62) * 4, 0, 1))[..., None], .5 + .5 * np.sin(Y * math.tau * 12), .6, .85, 0, 1)
    S['dark'] = (lerp((.03, .025, .02), (.07, .055, .045), fbm(4, 2)), fbm(8, 2) * .2, .3, .95, 0, 0)
    # v002 ageing (review on PR #80): base stays 花崗白 #C9C6BD (spec §11); blocks differ in tone (low-frequency tone along U,
    # each block samples a random U offset), rain streaks hang from the top of each wall block (granite walls are UV-anchored
    # to the strip top), granite_moss is the darker bottom / shaded variant with dirt and moss rising from the bed.
    # (new noise is drawn after every older source so the other strips stay byte-identical)
    tone = .5 + .5 * np.sin(math.tau * (X * 2 + .35 * fbm(2, 2))) * (.6 + .4 * fbm(3, 2))   # ~4 tone patches per 2 m of U
    rain = np.clip((fbm(9, 3, aniso=7) - .58) * 3.0, 0, 1) * np.clip((fbm(3, 2) - .35) * 2.5, 0, 1) * np.clip(Y * 1.5 - .2, 0, 1) ** 1.3
    pits = np.clip((fbm(48, 2) - .76) * 5, 0, 1)
    a, h, s_, r_, m_, g_ = S['granite']
    a = a * (.80 + .26 * tone[..., None]) * (1 - .28 * rain[..., None]) + rain[..., None] * np.array([.010, .012, .004]) - .03 * pits[..., None]
    S['granite'] = (a, h - .45 * lich + .2 * rain + .2 * pits, s_, r_, m_, g_)
    dirt = np.clip(1 - Y * 1.6, 0, 1) ** 1.3; moss2 = np.clip((fbm(7, 3) - .52) * 2.8, 0, 1) * np.clip(1.15 - Y * 1.5, 0, 1)
    a, h, s_, r_, m_, g_ = S['granite_moss']
    a = a * (.78 + .22 * tone[..., None]) * (1 - .38 * dirt[..., None]) * (1 - .55 * moss2[..., None]) + moss2[..., None] * np.array([.11, .17, .05])
    S['granite_moss'] = (a, h - .45 * lich + .8 * moss2, s_, r_, m_, g_)
    a, h, s_, r_, m_, g_ = S['granite_top']
    S['granite_top'] = (a * (.95 - .06 * pits[..., None]), h + .15 * pits, s_, r_, m_, g_)
    # plaster ageing: grey-buff tone, rain streaks under the lintel (UV anchored to the strip top), damp dirt rising from the sill
    pr_ = np.clip((fbm(12, 3, aniso=8) - .52) * 2.6, 0, 1) * np.clip(Y * 1.6 - .25, 0, 1) ** 1.2
    pd_ = np.clip(1 - Y * 2.2, 0, 1) ** 1.4 * (.6 + .4 * fbm(6, 2))
    a, h, s_, r_, m_, g_ = S['plaster']
    S['plaster'] = (a * (.86 + .1 * tone[..., None]) * (1 - .26 * pr_[..., None]) * (1 - .3 * pd_[..., None]) + pd_[..., None] * np.array([.02, .02, .0]),
                    h + .3 * pr_ + .2 * pd_, s_, r_, m_, g_)
    mc = np.clip(fbm(9, 3) * 1.2 - .1, 0, 1)
    S['moss'] = (lerp((.07, .11, .03), (.22, .30, .09), mc), fbm(30, 2) + .5 * mc, 2.4, .95, 0, 0)
    return S

# strip name -> (source, height px). Rows stack bottom-up from V = 0. 256 px per metre everywhere.
STRIPS = [('granite', 256), ('granite_moss', 256), ('granite_top', 128), ('plank', 256), ('beam', 256), ('oldwood', 128),
          ('plaster', 256), ('tile', 128), ('tile_moss', 128), ('bronze', 64), ('cloth', 64), ('paper', 64), ('dark', 32), ('moss', 32)]
SHEET = 2048; PXM = 256; PAD = 3
V0 = {}; _v = 0
for _n, _h in STRIPS: V0[_n] = (_v, _h); _v += _h
assert _v == SHEET, _v
MAT = {}

def make_trim():
    S = sources(); A = np.zeros((SHEET, SHEET, 3), np.float32); N = np.zeros((SHEET, SHEET, 3), np.float32)
    MS = np.zeros((SHEET, SHEET, 4), np.float32); EM = np.zeros((SHEET, SHEET, 3), np.float32)
    for name, h in STRIPS:
        alb, hgt, s, r, m, glow = S[name]; k = R // h
        alb = np.broadcast_to(alb, (R, R, 3)); hgt = np.broadcast_to(hgt, (R, R))
        a = alb.reshape(h, k, h, k, 3).mean((1, 3)); hh = hgt.reshape(h, k, h, k).mean((1, 3))
        dx = (np.roll(hh, -1, 1) - np.roll(hh, 1, 1)) * s; dy = (np.roll(hh, -1, 0) - np.roll(hh, 1, 0)) * s
        n = np.dstack([-dx, -dy, np.ones_like(hh)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
        reps = SHEET // h; v0 = V0[name][0]
        A[v0:v0 + h] = np.tile(a, (1, reps, 1)); N[v0:v0 + h] = np.tile(n * .5 + .5, (1, reps, 1))
        MS[v0:v0 + h, :, 0] = m; MS[v0:v0 + h, :, 3] = 1 - r
        if glow: EM[v0:v0 + h] = np.tile(a, (1, reps, 1))
    def save(nm, arr, data):
        im = bpy.data.images.new(nm, SHEET, SHEET, alpha=arr.shape[2] == 4)
        if data: im.colorspace_settings.name = 'Non-Color'
        px = np.ones((SHEET, SHEET, 4), np.float32); px[..., :arr.shape[2]] = np.clip(arr, 0, 1); im.pixels.foreach_set(px.ravel())
        if nm.startswith('_'): im.pack(); return im   # helper maps for the Blender preview material only, not shipped
        im.filepath_raw = str(TEX / f'{nm}.png'); im.file_format = 'PNG'; im.save(); return im
    ims = {'alb': save('T_MountainStreet_Albedo', A, False), 'nrm': save('T_MountainStreet_Normal', N, True),
           'ms': save('T_MountainStreet_MetallicSmoothness', MS, True), 'em': save('T_MountainStreet_Emission', EM, False)}
    rough = np.ones((SHEET, SHEET, 3), np.float32) * (1 - MS[..., 3:4]); metal = np.repeat(MS[..., :1], 3, 2)
    ims['rough'] = save('_rough', rough, True); ims['metal'] = save('_metal', metal, True)
    for nm, glow in (('M_MountainStreet_Trim', 0), ('M_MountainStreet_Glow', 1)):
        mat = bpy.data.materials.new(nm); mat.use_nodes = True; nt = mat.node_tree; bs = nt.nodes['Principled BSDF']
        def tex(im): t = nt.nodes.new('ShaderNodeTexImage'); t.image = im; return t
        nt.links.new(tex(ims['alb']).outputs['Color'], bs.inputs['Base Color'])
        nt.links.new(tex(ims['rough']).outputs['Color'], bs.inputs['Roughness']); nt.links.new(tex(ims['metal']).outputs['Color'], bs.inputs['Metallic'])
        nm_ = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tex(ims['nrm']).outputs['Color'], nm_.inputs['Color']); nt.links.new(nm_.outputs['Normal'], bs.inputs['Normal'])
        if glow:
            nt.links.new(tex(ims['em']).outputs['Color'], bs.inputs['Emission Color']); bs.inputs['Emission Strength'].default_value = 4.0
        MAT[glow] = mat
    return ims

def load_trim():
    """reuse the saved trim sheet PNGs (modules rebuilt without repainting)"""
    ims = {k: bpy.data.images.load(str(TEX / f'T_MountainStreet_{n}.png')) for k, n in
           (('alb', 'Albedo'), ('nrm', 'Normal'), ('ms', 'MetallicSmoothness'), ('em', 'Emission'))}
    for k in ('nrm', 'ms'): ims[k].colorspace_settings.name = 'Non-Color'
    for nm, glow in (('M_MountainStreet_Trim', 0), ('M_MountainStreet_Glow', 1)):
        mat = bpy.data.materials.new(nm); mat.use_nodes = True; nt = mat.node_tree; bs = nt.nodes['Principled BSDF']
        def tex(im): t = nt.nodes.new('ShaderNodeTexImage'); t.image = im; return t
        nt.links.new(tex(ims['alb']).outputs['Color'], bs.inputs['Base Color'])
        ms = tex(ims['ms']); sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(ms.outputs['Color'], sep.inputs['Color'])
        inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1
        nt.links.new(ms.outputs['Alpha'], inv.inputs[1]); nt.links.new(inv.outputs[0], bs.inputs['Roughness']); nt.links.new(sep.outputs['Red'], bs.inputs['Metallic'])
        nm_ = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tex(ims['nrm']).outputs['Color'], nm_.inputs['Color']); nt.links.new(nm_.outputs['Normal'], bs.inputs['Normal'])
        if glow:
            nt.links.new(tex(ims['em']).outputs['Color'], bs.inputs['Emission Color']); bs.inputs['Emission Strength'].default_value = 4.0
        MAT[glow] = mat

# ------------------------------------------------------------------ geometry helpers
parts = []
def link(o, grp): bpy.context.scene.collection.objects.link(o); o['grp'] = grp; parts.append(o); return o

def trim_uv(bm, strip, axis=None, seed=0):
    """project every face onto `strip` in the part's own frame. axis = grain / U direction (default: longest PCA axis)."""
    lay = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
    pts = np.array([v.co[:] for v in bm.verts]); c = pts.mean(0)
    if axis is not None:
        A = Vector(axis).normalized(); S1 = A.orthogonal().normalized(); S2 = A.cross(S1)
    else:
        try: _, _, vt = np.linalg.svd(pts - c, full_matrices=False); A, S1, S2 = [Vector(v) for v in vt]
        except Exception: A, S1, S2 = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
    frames = {0: (S1, S2), 1: (A, S2), 2: (A, S1)}
    v0, h = V0[strip]; cap = (h - 2 * PAD) / PXM
    proj = {k: (np.array([[Vector(p).dot(a), Vector(p).dot(b)] for p in pts])) for k, (a, b) in frames.items()}
    rng_ = random.Random(seed * 7919 + len(pts)); uoff = rng_.random()
    face_k = []
    for f in bm.faces:
        n = f.normal; face_k.append(int(np.argmax([abs(n.dot(A)), abs(n.dot(S1)), abs(n.dot(S2))])))
    wall = strip in ('granite', 'granite_moss', 'plaster'); zs = pts[:, 2]; zmin, zmax = zs.min(), zs.max(); zsc = min(1.0, cap / max(zmax - zmin, 1e-6))
    for f, k in zip(bm.faces, face_k):
        n = f.normal
        if wall and abs(n.z) < .7:   # wall stone side faces: V = +Z, granite anchored to the strip top (rain streaks), moss to the bottom
            a = Vector((-n.y, n.x, 0)).normalized()
            for l in f.loops:
                p = l.vert.co; u = p.dot(a) * PXM / SHEET + uoff
                t = cap - (zmax - p.z) * zsc if strip in ('granite', 'plaster') else (p.z - zmin) * zsc
                l[lay].uv = (u, (v0 + PAD + t * PXM) / SHEET)
            continue
        a, b = frames[k]; tmin, tmax = proj[k][:, 1].min(), proj[k][:, 1].max(); sc = min(1.0, cap / max(tmax - tmin, 1e-6))
        for l in f.loops:
            p = l.vert.co; u = p.dot(a) * PXM / SHEET + uoff; t = (p.dot(b) - tmin) * sc
            l[lay].uv = (u, (v0 + PAD + t * PXM) / SHEET)

def finish(name, bm, strip, grp, axis=None, smooth=False, glow=False):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces: f.smooth = smooth
    trim_uv(bm, strip, axis, seed=len(parts))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me)
    me.materials.append(MAT[1 if glow else 0]); o['strip'] = strip; return link(o, grp)

def reuv(o, strip, axis=None):
    bm = bmesh.new(); bm.from_mesh(o.data); trim_uv(bm, strip, axis, seed=len(parts)); bm.to_mesh(o.data); bm.free()

def apply(o, m):
    bpy.context.view_layer.objects.active = o; o.select_set(True); bpy.ops.object.modifier_apply(modifier=m.name); o.select_set(False)
def bevel(o, w, segs=2, angle=35):
    m = o.modifiers.new('wear', 'BEVEL'); m.width = w; m.segments = segs; m.limit_method = 'ANGLE'; m.angle_limit = math.radians(angle); m.use_clamp_overlap = True; apply(o, m)
def subdiv(o, cuts):
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=cuts, use_grid_fill=True); bm.to_mesh(o.data); bm.free()

def vnoise3(x, y, z, f, seed=0):
    x, y, z = x * f + seed * 17.3, y * f + seed * 5.1, z * f + seed * 11.7; xi, yi, zi = np.floor(x), np.floor(y), np.floor(z); u, v, w = x - xi, y - yi, z - zi
    u, v, w = u * u * (3 - 2 * u), v * v * (3 - 2 * v), w * w * (3 - 2 * w); xi, yi, zi = xi.astype(np.int64), yi.astype(np.int64), zi.astype(np.int64)
    def hh(a, b, c):
        n = (a * 73856093) ^ (b * 19349663) ^ (c * 83492791) ^ (seed * 2654435761); n = (n ^ (n >> 13)) * 1274126177; return ((n ^ (n >> 16)) & 0xffff) / 65535.0
    l = lambda a, b, t: a + (b - a) * t
    return l(l(l(hh(xi, yi, zi), hh(xi + 1, yi, zi), u), l(hh(xi, yi + 1, zi), hh(xi + 1, yi + 1, zi), u), v),
             l(l(hh(xi, yi, zi + 1), hh(xi + 1, yi, zi + 1), u), l(hh(xi, yi + 1, zi + 1), hh(xi + 1, yi + 1, zi + 1), u), v), w)
def vfbm3(x, y, z, f, oct=3, seed=0):
    t = 0; a = 1; n = 0
    for o in range(oct): t += a * vnoise3(x, y, z, f * 2 ** o, seed + o); n += a; a *= .5
    return t / n

def chisel(o, amt, freq, seed, keep_bed=True, keep_faces=None):
    """dressed-stone surface: vfbm3 displacement along the snapshotted vertex normal; bed (down-facing) faces stay flat so
    courses sit on each other; keep_faces=(axis,sign) keeps the outer joint plane flat (seams stay <=2 mm)."""
    me = o.data; me.update(); n = len(me.vertices)
    co = np.empty(n * 3); me.vertices.foreach_get('co', co); co = co.reshape(n, 3); nr = np.empty(n * 3); me.vertices.foreach_get('normal', nr); nr = nr.reshape(n, 3)
    d = -vfbm3(co[:, 0], co[:, 1], co[:, 2], freq, 3, seed) * amt   # inward only: faces never pass the 4 m grid plane
    if keep_bed: d[nr[:, 2] < -.6] = 0
    d[nr[:, 2] > .6] *= .35
    out = co + nr * d[:, None]; me.vertices.foreach_set('co', out.ravel()); me.update()

def box_bm(size, center=(0, 0, 0)):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1)
    for v in bm.verts: v.co = Vector([center[i] + v.co[i] * size[i] for i in range(3)])
    return bm
def box(name, size, center, strip, grp, bev=.01, segs=2, cuts=0, axis=None, rot=None):
    o = finish(name, box_bm(size), strip, grp, axis)
    if cuts: subdiv(o, cuts)
    if bev: bevel(o, bev, segs)
    if rot: o.data.transform(rot)
    o.data.transform(Matrix.Translation(center)); return o
def beam(name, a, b, w, h, strip, grp, bev=.008, up=(0, 0, 1)):
    a, b = Vector(a), Vector(b); t = (b - a); L = t.length; t.normalize(); up = Vector(up)
    if abs(t.dot(up)) > .99: up = Vector((0, 1, 0)) if abs(t.y) < .9 else Vector((1, 0, 0))   # vertical member: any horizontal 'up'
    s = t.cross(up).normalized(); u = t.cross(s)
    if u.dot(up) < 0: s = -s; u = t.cross(s)
    o = finish(name, box_bm((L, w, h)), strip, grp, axis=(1, 0, 0)); bevel(o, bev, 2)
    o.data.transform(Matrix(((t.x, s.x, u.x, 0), (t.y, s.y, u.y, 0), (t.z, s.z, u.z, 0), (0, 0, 0, 1)))); o.data.transform(Matrix.Translation((a + b) / 2)); return o
def lathe(name, profile, strip, grp, seg=32, center=(0, 0, 0), glow=False, wob=None):
    """wob(theta, ring_index) -> relative radius offset (carved petals etc.)"""
    bm = bmesh.new(); rings = []
    for ri, (r, z) in enumerate(profile):
        rings.append([bm.verts.new((r * (1 + (wob(math.tau * i / seg, ri) if wob else 0)) * math.cos(math.tau * i / seg),
                                    r * (1 + (wob(math.tau * i / seg, ri) if wob else 0)) * math.sin(math.tau * i / seg), z)) for i in range(seg)])
    for a, b in zip(rings, rings[1:]):
        for i in range(seg): j = (i + 1) % seg; bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    o = finish(name, bm, strip, grp, axis=(0, 0, 1), smooth=True, glow=glow); o.data.transform(Matrix.Translation(center)); return o
def tube(name, pts, r, strip, grp, sides=8, radii=None, caps=True):
    pts = [Vector(p) for p in pts]; bm = bmesh.new(); rings = []; prev = None
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        u = (prev - t * prev.dot(t)).normalized() if prev is not None else t.orthogonal().normalized(); prev = u; v = t.cross(u); rr = radii[i] if radii else r
        rings.append([bm.verts.new(p + (u * math.cos(math.tau * k / sides) + v * math.sin(math.tau * k / sides)) * rr) for k in range(sides)])
    for a, b in zip(rings, rings[1:]):
        for k in range(sides): bm.faces.new((a[k], a[(k + 1) % sides], b[(k + 1) % sides], b[k]))
    if caps: bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    ax = (pts[-1] - pts[0]); return finish(name, bm, strip, grp, axis=ax if ax.length > 1e-6 else None, smooth=True)
def prism_xz(name, poly, depth, y0, strip, grp, bev=.004, axis=(1, 0, 0)):
    """2D polygon in XZ extruded along +Y from y0"""
    bm = bmesh.new(); a = [bm.verts.new((x, y0, z)) for x, z in poly]; b = [bm.verts.new((x, y0 + depth, z)) for x, z in poly]; n = len(poly)
    bm.faces.new(a); bm.faces.new(list(reversed(b)))
    for i in range(n): j = (i + 1) % n; bm.faces.new((a[j], a[i], b[i], b[j]))
    o = finish(name, bm, strip, grp, axis)
    if bev: bevel(o, bev, 1, 30); reuv(o, strip, axis)   # re-project: bevel faces interpolated across a UV seam can collapse
    return o
def rotz(o, ang, pivot=(0, 0, 0)):
    p = Vector(pivot); o.data.transform(Matrix.Translation(p) @ Matrix.Rotation(ang, 4, 'Z') @ Matrix.Translation(-p))

# ------------------------------------------------------------------ SB01 straight foundation bay
def SB(mid, H, seed, style='random', chamfer=0.0, drain=False, notch_x=None):
    """v002 random-coursed granite shell, 4 x 4 x H m (review on PR #80): a tall bottom course of big blocks, courses of
    varying height with blocks of varying length, some blocks running through two courses, per-block setback and joint width
    (joints read deep and shallow), blocks skewed by an inward-only chisel. Ageing: per-block tone from the trim strip, rain
    streaks hanging from each block, darker bottom course and shaded back face (granite_moss), moss cushions pressed into the
    shaded bed joints (Detail_Moss). Top: perimeter coping stones (收邊石, flush with the 4 m grid, walk-worn on the street
    edge) with drainage notches, a slightly lower inner paving field. Faces are low-poly: detail lives in the normal map."""
    rg = random.Random(seed); half = GRID / 2; depth = .34; cope_h = .16; zc = H - cope_h; edge = .42; c = chamfer
    # wall faces: (angle, plane distance, x range with full corner blocks, x range with short corner blocks). The local frame is
    # the front face (-Y) rotated by `angle`; side 1 is +X (its local +x runs to the back). A chamfer cuts the front-right corner.
    faces = []
    for sd in range(4):
        xa, xb = -half, half; sa, sb = -half + depth, half - depth
        if c and sd == 0: xb = sb = half - c
        if c and sd == 1: xa = sa = -half + c
        faces.append((sd * math.pi / 2, half, (xa, xb), (sa, sb)))
    if c:
        dc = math.sqrt(2) * (half - c / 2); w = c / math.sqrt(2) - .07; faces.append((math.pi / 4, dc, (-w, w), (-w, w)))   # 6 cm short of the corners: the face blocks' ends show as quoins
    ci_ = half - depth + .03
    if c:   # core with the corner cut parallel to the chamfer face, (depth - .03) behind it
        kk = 2 * (half - c / 2) - math.sqrt(2) * (depth - .03) * math.sqrt(2)   # core corner line: x - y = kk
        poly = [(-ci_, -ci_), (kk - ci_, -ci_), (ci_, ci_ - kk), (ci_, ci_), (-ci_, ci_)]
        bmc = bmesh.new(); lo_v = [bmc.verts.new((x, y, .01)) for x, y in poly]; hi_v = [bmc.verts.new((x, y, H - .13)) for x, y in poly]
        bmc.faces.new(lo_v); bmc.faces.new(list(reversed(hi_v)))
        for i in range(5):
            j = (i + 1) % 5; bmc.faces.new((lo_v[i], lo_v[j], hi_v[j], hi_v[i]))
        finish(f'{mid}_core', bmc, 'dark', 'Main')
    else:
        box(f'{mid}_core', (2 * ci_, 2 * ci_, H - .14), (0, 0, (H - .14) / 2 + .01), 'dark', 'Main', bev=0)
    for sd, (ang, dist, (xa, xb), _) in enumerate(faces):   # mortar backing just behind the block faces: shows in the joints
        if sd < 4: ma, mb = (xa + .04 if xa <= -half + 1e-6 else xa), (xb - .04 if xb >= half - 1e-6 else xb)
        else: ma, mb = xa + .12, xb - .12
        o = box(f'{mid}_mortar{sd}', (mb - ma, .02, zc - .03 - sd * .004), ((ma + mb) / 2, -dist + .075, (zc - .03 - sd * .004) / 2 + .01 + sd * .002), 'granite_moss', 'Main', bev=0)
        rotz(o, ang)
    h0 = .52 if H > 1.5 else .42; rest = zc - h0; n = max(1, round(rest / .34))
    raw = [rg.uniform(.65, 1.35) if style == 'random' else 1.0 for _ in range(n)]; hs = [h0] + [rest * r / sum(raw) for r in raw]
    zs = [sum(hs[:i]) for i in range(len(hs))]
    notches = notch_x or {0: (-.95, .95), 2: (-.95, .95), 1: (0.0,), 3: (0.0,)}
    occupied = {}; moss_n = 0
    if drain: occupied[(0, 0)] = [(-.36, .36)]
    for ci, ch in enumerate(hs):
        z = zs[ci]; bottom = ci == 0; top_course = ci == len(hs) - 1
        for side, (ang, dist, full, short) in enumerate(faces):
            runs_full = side >= 4 or (side % 2 == 0) == (ci % 2 == 0)   # quoins: corner blocks alternate per course
            x0, x1 = full if runs_full else short
            occ = sorted(occupied.get((ci, side), [])); x = x0; k = 0
            first = style == 'stagger' and not bottom and ci % 2 == 1 and side < 4   # running bond: odd courses start with a half block
            while x < x1 - 1e-3:
                hit = next((iv for iv in occ if iv[0] - 1e-4 <= x < iv[1] - 1e-4), None)
                if hit: x = hit[1]; continue
                nxt = min([iv[0] for iv in occ if iv[0] > x + 1e-4] + [x1])
                L = rg.uniform(.85, 1.55) if bottom else (rg.uniform(.38, 1.15) if style == 'random' else rg.uniform(.74, .9))
                if first: L *= .5; first = False
                if nxt - (x + L) < .3: L = nxt - x
                double = (style == 'random' and side < 4 and not bottom and ci + 1 < len(hs) and rg.random() < .2 and L < 1.0 and x - x0 > .75 and x1 - (x + L) > .75)
                hh = ch + hs[ci + 1] if double else ch
                if double: occupied.setdefault((ci + 1, side), []).append((x, x + L))
                ends_top = top_course or (double and ci + 1 == len(hs) - 1)
                inset = 0 if bottom else (rg.uniform(.018, .055) if style == 'random' else rg.uniform(.026, .036)); gap = rg.uniform(.016, .042) if style == 'random' else .02
                lo = x + gap / 2 if x > x0 + 1e-4 else x + (inset if runs_full else 0)
                hi = x + L - gap / 2 if x + L < x1 - 1e-4 else x + L - (inset if runs_full else 0)
                zb = z + (gap / 2 if not bottom else 0); zt = z + hh + .008 if ends_top else z + hh - gap / 2
                if side >= 4: zb += .004; zt -= .004   # chamfer blocks overlap the face blocks: keep their beds off the same planes
                shaded = side == 2 or (side in (1, 3) and ci == 0)
                strip = 'granite_moss' if (bottom or (shaded and ci <= 1)) else ('granite_top' if rg.random() < .12 else 'granite')
                d_ = (depth if side < 4 else .22) - inset   # chamfer blocks shallower: they never reach into the face blocks' beds
                o = box(f'{mid}_c{ci}s{side}_{k}', (hi - lo, d_, zt - zb), ((lo + hi) / 2, -dist + inset + d_ / 2, (zb + zt) / 2), strip, 'Main',
                        bev=0, cuts=1 if hi - lo > .7 else 0)
                chisel(o, rg.uniform(.008, .016), 2.4, seed=seed + ci * 100 + side * 10 + k, keep_bed=False)
                bevel(o, rg.uniform(.016, .036), 2, 30)
                rotz(o, ang)
                # moss cushion pressed into the shaded bed joint under this block (touches the block below and this one)
                if not bottom and (shaded or ci == 1) and rg.random() < (.7 if shaded else .25) and hi - lo > .45:
                    mx0 = rg.uniform(lo + .05, hi - .4); mlen = rg.uniform(.25, min(.8, hi - mx0 - .03)); yy = -dist + inset + .035
                    npt = 7; pts = [(mx0 + mlen * i / (npt - 1), yy, z + rg.uniform(-.004, .004)) for i in range(npt)]
                    rad = [.016 + .016 * math.sin(math.pi * i / (npt - 1)) ** .7 for i in range(npt)]
                    m_ = tube(f'Detail_Moss_{mid}_{moss_n}', pts, .03, 'moss', 'Detail_Moss', sides=6, radii=rad); moss_n += 1
                    rotz(m_, ang)
                x += L; k += 1
    if drain:   # drain outlet in the street-face bottom course under the coping notch: two jamb stones, a lintel, dark culvert
        g = .02
        for nm, a, b, z0, z1 in (('jl', -.36, -.13, 0, hs[0] - g / 2), ('jr', .13, .36, 0, hs[0] - g / 2), ('lin', -.13 + g / 2, .13 - g / 2, .25, hs[0] - g / 2)):
            o = box(f'{mid}_drain_{nm}', (b - a - (g if nm != 'lin' else 0), depth, z1 - z0), ((a + b) / 2, -half + depth / 2, (z0 + z1) / 2), 'granite_moss', 'Main', bev=0, cuts=1)
            chisel(o, .01, 2.4, seed=seed + 950 + len(nm)); bevel(o, .02, 2, 30)
        box(f'{mid}_drain_hole', (.25, .30, .245), (0, -half + .05 + .15, .1245), 'dark', 'Main', bev=0)
        o = box(f'{mid}_drain_sill', (.30, .36, .04), (0, -half + .18, .02), 'granite_moss', 'Main', bev=0); bevel(o, .012, 2, 30)
    # coping: perimeter edge stones (top = H) and corner stones; drainage notches; inner paving a touch lower
    for side in range(4):
        street = side == 0; spans = []; cur = -half + (c if (c and side == 1) else edge); end = half - (c if (c and side == 0) else edge)
        for nx_ in sorted(notches[side]): spans += [(cur, nx_ - .07, False), (nx_ - .07, nx_ + .07, True)]; cur = nx_ + .07
        spans.append((cur, end, False)); final = []
        for a, b, nt in spans:
            if nt: final.append((a, b, True)); continue
            xs = [a]
            while b - xs[-1] > 1.1: xs.append(xs[-1] + rg.uniform(.6, .85))
            xs.append(b); final += [(p, q, False) for p, q in zip(xs, xs[1:])]
        for k, (a, b, notch) in enumerate(final):
            g = .012; top = H - .06 if notch else H; th = top - zc
            o = box(f'{mid}_edge{side}_{k}', (b - a - g, edge - .01, th), ((a + b) / 2, -half + (edge - .01) / 2, zc + th / 2), 'granite_top', 'Main',
                    bev=0, cuts=1 if b - a > .6 else 0)
            chisel(o, .008 if street else .005, 2.6, seed=seed + 700 + side * 20 + k)
            bevel(o, (.03 if street else .018) if not notch else .01, 3 if street else 2, 30)
            rotz(o, side * math.pi / 2)
        if c and side == 1: continue   # the front-right corner is the chamfer stone below
        o = box(f'{mid}_corner{side}', (edge - .012, edge - .012, cope_h), (-half + edge / 2, -half + edge / 2, zc + cope_h / 2), 'granite_top', 'Main', bev=0)
        chisel(o, .01, 2.6, seed=seed + 790 + side); bevel(o, .035, 2, 30); rotz(o, side * math.pi / 2)
    if c:
        g = .006; poly = [(half - c + g, -half), (half, -half + c - g), (half - edge + g, -half + c - g), (half - edge + g, -half + edge - g), (half - c + g, -half + edge - g)]
        bmc = bmesh.new(); lo_v = [bmc.verts.new((x, y, zc)) for x, y in poly]; hi_v = [bmc.verts.new((x, y, H)) for x, y in poly]
        bmc.faces.new(lo_v); bmc.faces.new(list(reversed(hi_v)))
        for i in range(5):
            j = (i + 1) % 5; bmc.faces.new((lo_v[i], lo_v[j], hi_v[j], hi_v[i]))
        o = finish(f'{mid}_corner_chamfer', bmc, 'granite_top', 'Main'); bevel(o, .02, 2, 30); reuv(o, 'granite_top')
    lo_, hi_ = -half + edge + .006, half - edge - .006; xs = [lo_]
    while xs[-1] < hi_ - .25: xs.append(min(hi_, xs[-1] + rg.uniform(.55, .95)))
    xs[-1] = hi_
    for i in range(len(xs) - 1):
        ys = [lo_]
        while ys[-1] < hi_ - .25: ys.append(min(hi_, ys[-1] + rg.uniform(.5, .9)))
        ys[-1] = hi_
        for j in range(len(ys) - 1):
            th = .12; top = H - .012 - rg.uniform(0, .006)
            o = box(f'{mid}_pave{i}_{j}', (xs[i + 1] - xs[i] - .018, ys[j + 1] - ys[j] - .018, th), ((xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2, top - th / 2),
                    'granite_top', 'Main', bev=0)
            bevel(o, .014, 2, 30)
    cols = [('box', (0, 0, H / 2), (GRID, GRID, H))] if not c else \
           [('box', (-c / 2, 0, H / 2), (GRID - c, GRID, H)), ('box', (half - c / 2, c / 2, H / 2), (c, GRID - c, H))]
    meta = {'collision': cols, 'walkTop': H, 'courses_m': [round(h, 3) for h in hs]}
    if c: meta['chamfer_m'] = c
    if drain: meta['drainOutlet_m'] = [0, -half, 0]
    return meta

def SB01(): return SB('SB01', 2.0, 5101)
def SB02(): return SB('SB02', 2.0, 5102, style='stagger', drain=True, notch_x={0: (0.0,), 2: (-.95, .95), 1: (0.0,), 3: (0.0,)})
def SB03(): return SB('SB03', 2.0, 5103, chamfer=.8, notch_x={0: (-.95,), 2: (-.95, .95), 1: (.4,), 3: (0.0,)})
def SB05(): return SB('SB05', 1.0, 5105)

def SB04():
    """stair bay 4 x 4 x 2 m: 11 granite steps (rise 18.2 cm, tread 36.4 cm) climbing from the street (-Y, z = 0) to the 2 m
    terrace at the back, each step two or three stones with walk-worn rounded noses (more wear in the middle); stepped granite
    cheek walls 0.6 m wide on both sides with a parapet ~0.5 m above the treads and coping stones; a dark wedge core closes
    the void under the flight."""
    rg = random.Random(5104); half = GRID / 2; n = 11; r = 2.0 / n; t = GRID / n; cw = .6; xi = half - cw
    bmc = bmesh.new(); pts = [(-half + .05, .01), (half - .05, .01), (half - .05, 2.0 - .06)]
    a = [bmc.verts.new((-xi + .01, y, z)) for y, z in pts]; b = [bmc.verts.new((xi - .01, y, z)) for y, z in pts]
    bmc.faces.new(a); bmc.faces.new(list(reversed(b)))
    for i in range(3):
        j = (i + 1) % 3; bmc.faces.new((a[i], a[j], b[j], b[i]))
    finish('SB04_core', bmc, 'dark', 'Main')
    cols = []
    for i in range(n):
        y0 = -half + i * t; y1 = min(half, y0 + t + .02); z1 = (i + 1) * r; z0 = max(0.0, i * r - .06)
        e_ = .02 + .006 * (i % 2); W = 2 * xi + 2 * e_; kk = rg.choice((2, 3)); xs = [-xi - e_] + [-xi - e_ + W * j / kk + rg.uniform(-.15, .15) for j in range(1, kk)] + [xi + e_]
        for k, (p, q) in enumerate(zip(xs, xs[1:])):
            mid_ = abs((p + q) / 2) < .7
            o = box(f'SB04_step{i}_{k}', (q - p - .014, y1 - y0, z1 - z0), ((p + q) / 2, (y0 + y1) / 2, (z0 + z1) / 2), 'granite_moss' if i < 2 else 'granite_top', 'Main',
                    bev=0, cuts=1)
            chisel(o, .012 if mid_ else .007, 2.2, seed=6000 + i * 10 + k, keep_bed=False); bevel(o, .035 if mid_ else .02, 3, 30)
        cols.append(('box', (0, (y0 + y0 + t) / 2, z1 / 2), (2 * xi, t, z1)))
    for sx in (-1, 1):
        for si, (ya, yb, top) in enumerate(((-half, -1.0, .9), (-1.0, 0.0, 1.4), (0.0, half, 2.0))):
            zc_ = top - .14; nc = max(1, round(zc_ / .38)); hs = [zc_ / nc] * nc; z = 0
            for ci, ch in enumerate(hs):
                ys = [ya]
                while yb - ys[-1] > 1.05: ys.append(ys[-1] + rg.uniform(.45, .75))
                ys.append(yb)
                for k, (p, q) in enumerate(zip(ys, ys[1:])):
                    g = .018; ins = rg.uniform(0, .03); front = p <= -half + 1e-6
                    p2 = p + (g / 2 if not front else ins); q2 = q - g / 2 if q < half - 1e-6 else q
                    zt = z + ch + (.008 if ci == nc - 1 else -g / 2); zb = z + (g / 2 if ci else 0)
                    xo = sx * (half - ins); xin = sx * (xi - .02)
                    o = box(f'SB04_cheek{sx:+d}{si}{ci}{k}', (abs(xo - xin), q2 - p2, zt - zb), ((xo + xin) / 2, (p2 + q2) / 2, (zb + zt) / 2),
                            'granite_moss' if ci == 0 else ('granite_top' if rg.random() < .12 else 'granite'), 'Main', bev=0, cuts=1 if q2 - p2 > .7 else 0)
                    chisel(o, rg.uniform(.008, .014), 2.4, seed=6500 + si * 100 + ci * 10 + k + (50 if sx > 0 else 0), keep_bed=False)
                    bevel(o, rg.uniform(.016, .03), 2, 30)
                z += ch
            o = box(f'SB04_coping{sx:+d}{si}', (cw - .004, yb - ya - .012, .14), (sx * (half - cw / 2 - .002), (ya + yb) / 2, zc_ + .07), 'granite_top', 'Main', bev=0)
            chisel(o, .006, 2.6, seed=6900 + si + (5 if sx > 0 else 0)); bevel(o, .03, 3, 30)
            cols.append(('box', (sx * (half - cw / 2), (ya + yb) / 2, top / 2), (cw, yb - ya, top)))
    return {'collision': cols, 'walkTop': 2.0, 'steps': {'count': n, 'rise_m': round(r, 4), 'tread_m': round(t, 4)}}



def moss_tuft(name, rg):
    bm = bmesh.new()
    for i in range(rg.randint(5, 8)):
        a = rg.uniform(0, math.tau); L = rg.uniform(.05, .11); w = rg.uniform(.012, .02); d = Vector((math.cos(a) * .6, math.sin(a) * .25, 1)).normalized()
        s = Vector((-math.sin(a), math.cos(a), 0)) * w; b = Vector((rg.uniform(-.04, .04), rg.uniform(-.01, .01), 0))
        v = [bm.verts.new(b - s), bm.verts.new(b + s), bm.verts.new(b + d * L)]; bm.faces.new(v)
    return finish(name, bm, 'granite_moss', 'Detail_Moss')

# ------------------------------------------------------------------ SF01 open shopfront bay
def SF(mid, seed, lattice=False, corner=False, counter=-1, mid_sets=True):
    """v002 (review on PR #80) 4 x 4 x 3 m: front 3 m open veranda (stall space), rear 1 m closed plank room with a dark doorway.
    Round cedar posts on carved drum bases (鼓墩 with lotus petals on a square plinth), bronze foot bands; front lintel 額枋 with
    霸王拳 beam heads; a few bracket sets 斗栱 (一斗三升 with a projecting 耍頭) on the front between lintel and top plate,
    carved brackets 雀替; plank walls with rails; wear and repairs (bronze hoops on split posts, an inlaid patch, a splice plate
    on the lintel, replaced boards); plank floor with a worn front threshold 門檻 and a counter edge at the front left for a stall
    to lean on; blank indigo noren, two paper lanterns. Top plate at 3.0 m carries the roof bay.
    Variants: lattice (SF02) closes both veranda sides with lattice screens over a plank dado; corner (SF03) dresses the +X side as
    a second open shopfront (bracket sets, noren, threshold, beam head, brackets) so the veranda turns the street corner."""
    rg = random.Random(seed); half = GRID / 2; H = 3.0; pr = .12; zb = .30
    front_y = -half + .2; enc_y = 1.0; back_y = half - .2; px = half - .2
    zl0, zl1 = 2.34, 2.56; zp0 = H - .14            # 額枋 2.34-2.56, bracket zone 2.56-2.86, top plate 2.86-3.0
    posts = [(-px, front_y), (px, front_y), (-px, enc_y), (px, enc_y), (-px, back_y), (px, back_y)]
    petals = lambda th, i: (.06 * max(0.0, math.cos(8 * th)) ** 1.5) if 1 <= i <= 4 else 0.0
    for i, (x, y) in enumerate(posts):
        o = box(f'{mid}_plinth{i}', (.40, .40, .10), (x, y, .05), 'granite_top', 'Main', bev=0); chisel(o, .004, 4, 300 + i); bevel(o, .02, 2, 30)
        lathe(f'{mid}_drum{i}', [(.150, .095), (.168, .11), (.180, .15), (.182, .20), (.172, .25), (.150, .285), (.135, zb)], 'granite', 'Main',
              seg=48, center=(x, y, 0), wob=petals)
        lathe(f'{mid}_post{i}', [(pr * 1.04, zb - .01)] + [(pr * (1 - .07 * t) + .003 * math.sin(t * 40 + i), zb + .1 + t * (zl1 - .015 - zb - .1)) for t in np.linspace(0, 1, 14)],
              'beam', 'Main', seg=32, center=(x, y, 0))
        lathe(f'{mid}_band{i}', [(pr + .012, zb - .005), (pr + .014, zb + .015), (pr + .014, zb + .085), (pr + .01, zb + .10)], 'bronze', 'Main', seg=20, center=(x, y, 0))
    # repairs on the posts: two bronze hoops on a split front post, an inlaid patch on a rear post
    for zz in (1.05, 1.32):
        r_ = pr * (1 - .07 * (zz - zb - .1) / (zl1 - zb - .1)) + .004
        lathe(f'{mid}_hoop{zz}', [(r_ - .004, zz - .025), (r_ + .008, zz - .022), (r_ + .008, zz + .022), (r_ - .004, zz + .025)], 'bronze', 'Main', seg=24, center=(px, front_y, 0))
    box(f'{mid}_postpatch', (.035, .09, .34), (-px - .095, front_y + .02, .95), 'oldwood', 'Main', bev=.006)
    # lintels: 額枋 + top plate around the bay; front and back lintels end in carved 霸王拳 heads past the corner posts
    for nm, a, b in (('front', (-px + .02, front_y, 0), (px - .02, front_y, 0)), ('enc', (-half + .06, enc_y, 0), (half - .06, enc_y, 0)),
                     ('back', (-px + .02, back_y, 0), (px - .02, back_y, 0)),
                     ('left', (-px, front_y + .02, 0), (-px, back_y - .02, 0)), ('right', (px, front_y + .02, 0), (px, back_y - .02, 0))):
        a = Vector(a); b = Vector(b)
        sd = .012 if nm in ('left', 'right') else 0   # side members a hair smaller: no shared faces where beams cross
        if nm in ('front', 'back'): a = a - Vector((.06, 0, 0)); b = b + Vector((.06, 0, 0))
        beam(f'{mid}_lintel_{nm}', a + Vector((0, 0, (zl0 + zl1) / 2)), b + Vector((0, 0, (zl0 + zl1) / 2)), .16 - sd, zl1 - zl0 - sd, 'beam', 'Main', bev=.012)
        pa = Vector((-half + .06, a.y, 0)) if nm in ('front', 'back') else a; pb = Vector((half - .06, b.y, 0)) if nm in ('front', 'back') else b
        if nm in ('left', 'right'): pa = Vector((a.x, -half + .06, 0)); pb = Vector((a.x, half - .06, 0))
        beam(f'{mid}_plate_{nm}', pa + Vector((0, 0, H - .07 - sd / 2)), pb + Vector((0, 0, H - .07 - sd / 2)), .22 - sd, .14 - sd, 'beam', 'Main', bev=.012)
    head = [(0, zl1 - .003), (.10, zl1 - .003), (.135, zl1 - .02), (.15, zl1 - .06), (.128, zl1 - .09), (.152, zl1 - .125), (.15, zl1 - .17), (.12, zl0 + .008), (0, zl0 + .003)]
    for y in (front_y, back_y):
        for sx in (-1, 1):
            poly = [(sx * (px - .02 + dx), z) for dx, z in head]
            if sx < 0: poly = list(reversed(poly))
            prism_xz(f'{mid}_head{y:+.1f}{sx:+d}', poly, .15, y - .075, 'beam', 'Main', bev=.004)
    # splice plate repair on the front lintel, bronze joint plates at the front posts
    box(f'{mid}_splice', (.42, .02, .16), (.55, front_y - .089, (zl0 + zl1) / 2), 'oldwood', 'Main', bev=.004)
    for k, xx in enumerate((.40, .70)):
        lathe(f'{mid}_splicenail{k}', [(.002, 0), (.011, 0), (.009, .006), (.002, .008)], 'bronze', 'Main', seg=8)
        nl = parts[-1]; q = Vector((0, -1, 0)).to_track_quat('Z', 'Y').to_matrix().to_4x4(); nl.data.transform(Matrix.Translation((xx, front_y - .096, (zl0 + zl1) / 2)) @ q)
    for x in (-px, px):
        s = -1 if x > 0 else 1
        box(f'{mid}_plate_br{x:+.1f}', (.16, .012, .2), (x + s * .2, front_y - .085, (zl0 + zl1) / 2), 'bronze', 'Main', bev=.003)
    # bracket sets 斗栱 (一斗三升 + 耍頭) on the front: over the two front posts and two between; frieze boards fill the zone
    def dou(name, cx, cy, w_top, w_bot, z0, z1, depth):
        zm = z1 - (z1 - z0) * .4
        poly = [(cx - w_bot / 2, z0), (cx + w_bot / 2, z0), (cx + w_top / 2, zm), (cx + w_top / 2, z1), (cx - w_top / 2, z1), (cx - w_top / 2, zm)]
        prism_xz(name, poly, depth, cy - depth / 2, 'beam', 'Main', bev=.004)
    za0, za1 = 2.64, 2.725
    def bracket_set(k, cx, Ll=None, Lr=None):
        if Ll is None: Ll = .38 if cx > -px + .1 else half - .005 - abs(cx)
        if Lr is None: Lr = .38 if cx < px - .1 else half - .005 - abs(cx)
        dou(f'{mid}_dou{k}', cx, front_y, .22, .16, zl1 - .025, za0 + .004, .20)
        arm = [(cx - Ll, za1), (cx + Lr, za1)] + [(cx + Lr - .08 * (1 - math.cos(t * math.pi / 2)), za1 - .03 - .055 * math.sin(t * math.pi / 2)) for t in np.linspace(0, 1, 5)] +               [(cx - Ll + .08 * (1 - math.cos(t * math.pi / 2)), za1 - .03 - .055 * math.sin(t * math.pi / 2)) for t in np.linspace(1, 0, 5)]
        prism_xz(f'{mid}_gong{k}', arm, .10, front_y - .05, 'beam', 'Main', bev=.003)
        for j, dx in enumerate((-.30, 0, .30)):
            if abs(cx + dx) > half - .075: continue
            dou(f'{mid}_sheng{k}{j}', cx + dx, front_y, .14, .10, za1 - .006, zp0 + .009, .14)
        nose = [(-.10, za0 + .006), (.13, za0 + .006), (.183, za0 + .035), (.183, za1 - .004), (-.10, za1 - .004)]
        o = prism_xz(f'{mid}_shua{k}', nose, .09, -.045, 'beam', 'Main', bev=.004)
        rotz(o, -math.pi / 2); o.data.transform(Matrix.Translation((cx, front_y, 0)))
    for k, cx in enumerate((-px, -.6, .6, px) if mid_sets else (-px, px)): bracket_set(k, cx)
    def turned(fn):   # build front-face parts, then turn them onto the +X side (front local x -> world y)
        n0 = len(parts); fn()
        for o in parts[n0:]: rotz(o, math.pi / 2)
    box(f'{mid}_frieze_front', (2 * px - .1, .03, zp0 - zl1 + .012), (0, front_y + .028, (zl1 + zp0) / 2), 'plank', 'Main', bev=.003, axis=(1, 0, 0))
    for nm, c, s in (('back', (0, back_y, (zl1 + zp0) / 2), (2 * px - .1, .04, zp0 - zl1 + .012)), ('enc', (0, enc_y, (zl1 + zp0) / 2), (2 * px - .1, .04, zp0 - zl1 + .012)),
                     ('l', (-px, (front_y + back_y) / 2, (zl1 + zp0) / 2), (.04, back_y - front_y - .1, zp0 - zl1 + .012)),
                     ('r', (px, (front_y + back_y) / 2, (zl1 + zp0) / 2), (.04, back_y - front_y - .1, zp0 - zl1 + .012))):
        box(f'{mid}_frieze_{nm}', s, c, 'plank', 'Main', bev=.003, axis=(1, 0, 0) if s[0] > s[1] else (0, 1, 0))
    # carved brackets 雀替 under the front lintel: scroll profile in XZ, inner side of each front post
    prof = []
    for i in range(13):
        t = i / 12; prof.append((.12 + .86 * t, zl0 - .46 * (1 - t) ** 1.5 - .03 * math.sin(t * math.pi * 3)))
    prof = [(.12, zl0), (.98, zl0)] + prof[::-1][1:]
    def brackets(pairs, tag=''):
        lift_ = .01 if tag else 0.0   # the side lintels are 12 mm smaller: turned brackets rise to meet them
        for x, sgn in pairs:
            poly = [(x + sgn * dx, z + lift_) for dx, z in prof] if sgn > 0 else [(x + sgn * dx, z + lift_) for dx, z in reversed(prof)]
            prism_xz(f'{mid}_bracket{tag}{x:+.1f}', poly, .12, front_y - .06, 'beam', 'Main', bev=0)
    brackets(((-px, 1), (px, -1)))
    if corner:   # second open face on +X: bracket sets between the posts, beam head at the front end, 雀替 at both posts
        turned(lambda: [bracket_set(10 + k, cx) for k, cx in enumerate((-.6, .2, enc_y))])
        turned(lambda: brackets(((-px, 1), (enc_y, -1)), 'R'))
        hd = [(dx, min(z, zl1 - .009) if z > (zl0 + zl1) / 2 else max(z, zl0 + .009)) for dx, z in head]
        turned(lambda: prism_xz(f'{mid}_headR', list(reversed([(-(px - .02 + dx), z) for dx, z in hd])), .14, front_y - .07, 'beam', 'Main', bev=.004))
    if lattice:   # lattice screens over a plank dado on both veranda sides (between the front post base and the enclosure post)
        ya, yb_ = front_y + .21, enc_y - .13
        for sx in (-1, 1):
            xw = sx * px
            for k, yy in enumerate(np.arange(ya + .1, yb_ - .05, .2)):
                box(f'{mid}_dado{sx:+d}{k}', (.035, .19, .86), (xw, yy, .043 + .43), 'plank' if rg.random() > .2 else 'oldwood', 'Main', bev=.004, axis=(0, 0, 1))
            for nm, zz, hh in (('rail_lo', .92, .07), ('rail_hi', zl0 - .03, .06)):
                box(f'{mid}_lat{nm}{sx:+d}', (.07, yb_ - ya - .02, hh), (xw, (ya + yb_) / 2, zz), 'beam', 'Main', bev=.006, axis=(0, 1, 0))
            for nm, yy in (('a', ya + .03), ('b', yb_ - .03)):
                box(f'{mid}_latpost{nm}{sx:+d}', (.08, .06, zl0 - .06 - .047), (xw, yy, .047 + (zl0 - .06 - .047) / 2), 'beam', 'Main', bev=.006, axis=(0, 0, 1))
            zl_a, zl_b = .955, zl0 - .06
            # diamond lattice (as the picked reference, option 2): two sets of 45-degree bars clipped to the panel, sets 5 mm apart
            y_a, y_b = ya + .055, yb_ - .055; z_a, z_b = zl_a - .005, zl_b + .005; sp = .16
            for dset, (sgn, dx) in enumerate(((1, -.004), (-1, .004))):
                for k, c0 in enumerate(np.arange(-(z_b - z_a) - (y_b - y_a), (z_b - z_a) + (y_b - y_a), sp)):
                    # line z - z_a = sgn * (y - y_a) + c0, clipped to the rectangle
                    pts = []
                    for yy in (y_a, y_b):
                        zz = z_a + sgn * (yy - y_a) + c0
                        if z_a <= zz <= z_b: pts.append((yy, zz))
                    for zz in (z_a, z_b):
                        yy = y_a + sgn * (zz - z_a - c0)
                        if y_a <= yy <= y_b: pts.append((yy, zz))
                    pts = sorted(set((round(p, 5), round(q, 5)) for p, q in pts))
                    if len(pts) < 2 or math.dist(pts[0], pts[-1]) < .08: continue
                    (y0_, z0_), (y1_, z1_) = pts[0], pts[-1]
                    beam(f'{mid}_latd{sx:+d}{dset}_{k}', (xw + dx, y0_, z0_), (xw + dx, y1_, z1_), .018, .022, 'beam', 'Main', bev=.003)
    # rear room: plank walls (back, two sides, front-of-room with a dark doorway), rails, patch boards, dark room box
    def plank_wall(tag, x0, x1, y, z0, z1, skip=None, axis='x'):
        x = x0; k = 0
        while x < x1 - 1e-3:
            w = min(rg.uniform(.20, .30), x1 - x)
            if x1 - (x + w) < .08: w = x1 - x
            cx = x + w / 2
            if skip and skip[0] < cx < skip[1]:
                zz0 = skip[2]
                if zz0 >= z1 - .02: x += w; k += 1; continue
                lo = zz0
            else: lo = z0
            st = 'plank' if rg.random() > .18 else 'oldwood'   # replaced boards read darker / greyer
            if axis == 'x': o = box(f'{mid}_{tag}{k}', (w - .006, .045, z1 - lo), (cx, y, (lo + z1) / 2), st, 'Main', bev=.006, axis=(0, 0, 1))
            else: o = box(f'{mid}_{tag}{k}', (.045, w - .006, z1 - lo), (y, cx, (lo + z1) / 2), st, 'Main', bev=.006, axis=(0, 0, 1))
            for zr_ in (.42, 1.45):   # nail heads where the board crosses a rail
                if lo < zr_ < z1:
                    off = .0225 + .05; pos = (cx, y - off if y < 1.5 else y + off, zr_) if axis == 'x' else ((y - off if y < 0 else y + off), cx, zr_)
                    lathe(f'{mid}_nail_{tag}{k}_{zr_}', [(.002, 0), (.012, 0), (.010, .006), (.002, .008)], 'bronze', 'Main', seg=8, center=(0, 0, 0))
                    nl = parts[-1]; ax = Vector((0, -1 if y < 1.5 else 1, 0)) if axis == 'x' else Vector((-1 if y < 0 else 1, 0, 0))
                    q = ax.to_track_quat('Z', 'Y').to_matrix().to_4x4(); nl.data.transform(Matrix.Translation(pos) @ q)
            x += w; k += 1
    zw0, zw1 = .06, zl0
    plank_wall('back', -px + pr, px - pr, back_y + .07, zw0, zw1)
    plank_wall('lw', enc_y + pr, back_y - pr, -px - .0, zw0, zw1, axis='y'); plank_wall('rw', enc_y + pr, back_y - pr, px + .0, zw0, zw1, axis='y')
    door = (-.75, .75, 2.0)
    plank_wall('front_room', -px + pr, px - pr, enc_y + .07, zw0, zw1, skip=(-.8, .8, zl1))
    zt0, zt1 = door[2] + .12, zl0 - .01
    for k, xx in enumerate(np.linspace(-.72, .72, 9)): box(f'{mid}_lat_v{k}', (.022, .03, zt1 - zt0), (xx, enc_y + .07, (zt0 + zt1) / 2), 'beam', 'Main', bev=.003, axis=(0, 0, 1))
    for k, zz in enumerate(np.linspace(zt0, zt1, 3)): box(f'{mid}_lat_h{k}', (1.40, .026, .022), (0, enc_y + .07, zz), 'beam', 'Main', bev=.003, axis=(1, 0, 0))
    for xx in (-.75, .75): box(f'{mid}_lat_post{xx:+.1f}', (.06, .06, zl0 + .004 - door[2] - .03), (xx, enc_y + .07, (zl0 + .004 + door[2] + .03) / 2), 'beam', 'Main', bev=.006, axis=(0, 0, 1))
    yb = back_y + .07 + .0465; yf = enc_y + .07 - .0465
    for nm, (a, b) in (('back', ((-px, yb), (px, yb))), ('fr', ((-px, yf), (-.8, yf))), ('fr2', ((.8, yf), (px, yf)))):
        for zr in (.42, 1.45):
            beam(f'{mid}_rail_{nm}{zr}', (a[0], a[1], zr), (b[0], b[1], zr), .05, .1, 'beam', 'Main', bev=.006)
    for nm, x in (('l', -px - .0465), ('r', px + .0465)):
        for zr in (.42, 1.45): beam(f'{mid}_rail_{nm}{zr}', (x, enc_y, zr), (x, back_y, zr), .05, .1, 'beam', 'Main', bev=.006)
    for x in (-.8, .8): beam(f'{mid}_jamb{x:+.1f}', (x, enc_y + .02, .05), (x, enc_y + .02, door[2] + .08), .1, .12, 'beam', 'Main', bev=.008)
    beam(f'{mid}_doorhead', (-.88, enc_y + .02, door[2] + .06), (.88, enc_y + .02, door[2] + .06), .14, .12, 'beam', 'Main', bev=.008)
    beam(f'{mid}_doorsill', (-.8, enc_y + .02, .07), (.8, enc_y + .02, .07), .14, .1, 'oldwood', 'Main', bev=.01)
    box(f'{mid}_patch', (.34, .02, .22), (1.25, enc_y + .07 - .0315, 1.05), 'oldwood', 'Main', bev=.004)
    box(f'{mid}_patch2', (.02, .26, .18), (-px - .0315, 1.5, .8), 'oldwood', 'Main', bev=.004)
    box(f'{mid}_room', (2 * px - .34, back_y - enc_y - .14, zl0 - .04), (0, (enc_y + back_y) / 2 + .09, (zl0 - .04) / 2 + .01), 'dark', 'Main', bev=0)
    # veranda floor: planks along X on low sleepers; rows that meet the post bases stop short of them
    y = front_y + .085; k = 0
    while y < enc_y - .06:
        w = min(rg.uniform(.20, .28), enc_y - .06 - y); yc = y + w / 2
        near = abs(yc - front_y) < .26 or abs(yc - enc_y) < .26
        x_lo = -(px - .215) if near else (-(px - .045) if lattice else -(half - .02))
        x_hi = (px - .215) if near else (px - .06 if corner else (px - .045 if lattice else half - .02))
        box(f'{mid}_floor{k}', (x_hi - x_lo, w - .008, .045), ((x_lo + x_hi) / 2, yc, .0225), 'plank' if rg.random() > .2 else 'oldwood', 'Main', bev=.005, axis=(1, 0, 0))
        y += w; k += 1
    for k, xx in enumerate((-1.0, 0.0, 1.0)):   # sleepers under the boards tie floor, front sill and door sill together
        box(f'{mid}_sleeper{k}', (.10, enc_y - front_y + .05, .025), (xx, (front_y + enc_y) / 2 + .015, .0175), 'beam', 'Main', bev=.004, axis=(0, 1, 0))
    # worn front threshold 門檻 between the front post bases (centre dipped by feet) and the counter edge at the front left
    for nm, x0, x1, ht in (('l', -px + .2, -.55, .14), ('m', -.55, .55, .10), ('r', .55, px - .2, .14)):
        o = box(f'{mid}_sill_{nm}', (x1 - x0 - .004, .14, ht), ((x0 + x1) / 2, front_y, ht / 2), 'oldwood', 'Main', bev=0, cuts=1)
        chisel(o, .006, 3, 520 + len(nm)); bevel(o, .03 if nm == 'm' else .015, 2, 30)
    if corner:   # threshold along the +X open face (centre dipped), built on the front and turned
        def rsill():
            for nm, x0, x1, ht in (('Rl', front_y + .2, -.55, .14), ('Rm', -.55, .3, .10), ('Rr', .3, enc_y - .2, .14)):
                o = box(f'{mid}_sill_{nm}', (x1 - x0 - .004, .14, ht), ((x0 + x1) / 2, front_y, ht / 2), 'oldwood', 'Main', bev=0, cuts=1)
                chisel(o, .006, 3, 540 + len(nm)); bevel(o, .03 if nm == 'Rm' else .015, 2, 30)
        turned(rsill)
    cx0, cx1, cy, cd, ch = (-px + .22, -.55, front_y + .33, .40, .84) if counter < 0 else (.55, px - .22, front_y + .33, .40, .84)
    box(f'{mid}_counter_body', (cx1 - cx0, cd - .06, ch - .04), ((cx0 + cx1) / 2, cy, .04 + (ch - .04) / 2), 'dark', 'Main', bev=0)
    for k, xx in enumerate(np.arange(cx0 + .1, cx1 - .05, .2)):
        box(f'{mid}_counter_board{k}', (.19, .025, ch - .09), (xx, cy - (cd - .06) / 2 - .010, .07 + (ch - .09) / 2), 'plank' if k % 3 else 'oldwood', 'Main', bev=.004, axis=(0, 0, 1))
    box(f'{mid}_counter_top', (cx1 - cx0 + .06, cd, .05), ((cx0 + cx1) / 2, cy - .02, ch + .02), 'beam', 'Main', bev=.012, axis=(1, 0, 0))
    for e, xe in (('a', cx0 - .0125 + .002), ('b', cx1 + .0125 - .002)):   # end panels: the dark core never shows
        box(f'{mid}_counter_end{e}', (.025, cd - .06 + .02, ch - .05), (xe, cy - .01, .045 + (ch - .05) / 2), 'plank', 'Main', bev=.004, axis=(0, 0, 1))
    box(f'{mid}_counter_kick', (cx1 - cx0, .05, .07), ((cx0 + cx1) / 2, cy - (cd - .06) / 2 - .03, .08), 'beam', 'Main', bev=.006, axis=(1, 0, 0))
    # blank indigo noren on a rod between the front posts (Detail_Cloth); three panels, gentle wave, no writing
    rod_z = zl0 - .05
    tube('Detail_Cloth_rod', [(-1.25, front_y - .02, rod_z), (1.25, front_y - .02, rod_z)], .018, 'beam', 'Detail_Cloth', sides=8)
    for k, x0 in enumerate((-1.2, -.38, .44)):
        bm = bmesh.new(); W, Hc, nx, nz = .76, .62, 10, 8; vs = []
        for j in range(nz + 1):
            row = []
            for i in range(nx + 1):
                u = i / nx; v = j / nz; yy = front_y - .03 + .025 * math.sin(u * math.pi * 3 + k) * v
                row.append(bm.verts.new((x0 + u * W, yy, rod_z - v * Hc)))
            vs.append(row)
        for j in range(nz):
            for i in range(nx): bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
        o = finish(f'Detail_Cloth_{k}', bm, 'cloth', 'Detail_Cloth', axis=(1, 0, 0))
        m = o.modifiers.new('t', 'SOLIDIFY'); m.thickness = .006; apply(o, m); reuv(o, 'cloth', (1, 0, 0))
    def noren(xs0, tag, rod=(-1.25, 1.25)):
        tube(f'Detail_Cloth_rod{tag}', [(rod[0], front_y - .02, rod_z), (rod[1], front_y - .02, rod_z)], .018, 'beam', 'Detail_Cloth', sides=8)
        for k, x0 in enumerate(xs0):
            bm = bmesh.new(); W, Hc, nx, nz = .76, .62, 10, 8; vs = []
            for j in range(nz + 1):
                row = []
                for i in range(nx + 1):
                    u = i / nx; v = j / nz; yy = front_y - .03 + .025 * math.sin(u * math.pi * 3 + k) * v
                    row.append(bm.verts.new((x0 + u * W, yy, rod_z - v * Hc)))
                vs.append(row)
            for j in range(nz):
                for i in range(nx): bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
            o = finish(f'Detail_Cloth{tag}_{k}', bm, 'cloth', 'Detail_Cloth', axis=(1, 0, 0))
            m = o.modifiers.new('t', 'SOLIDIFY'); m.thickness = .006; apply(o, m); reuv(o, 'cloth', (1, 0, 0))
    if corner: turned(lambda: noren((-1.45, -.66), 'R', rod=(-1.5, .14)))
    lantern_x = [-px + .38, px - .38]
    def lantern(x):
        y = front_y + .02; ztop = zl0 - .05
        tube(f'Detail_Lanterns_cord{x:+.1f}', [(x, y, zl0), (x, y, ztop - .02)], .006, 'bronze', 'Detail_Lanterns', sides=5)
        lathe(f'Detail_Lanterns_capT{x:+.1f}', [(.05, ztop - .02), (.075, ztop - .05), (.075, ztop - .07), (.05, ztop - .075)], 'bronze', 'Detail_Lanterns', seg=16, center=(x, y, 0))
        prof = [(.06 + .12 * math.sin(math.pi * t) ** .8, ztop - .07 - .38 * t) for t in np.linspace(0, 1, 11)]
        lathe(f'Glow_lantern{x:+.1f}', prof, 'paper', 'Glow', seg=24, center=(x, y, 0), glow=True)
        for r in range(8):
            a = math.tau * r / 8; pts = [(x + (p[0] + .004) * math.cos(a), y + (p[0] + .004) * math.sin(a), p[1]) for p in prof]
            tube(f'Detail_Lanterns_rib{x:+.1f}_{r}', pts, .004, 'beam', 'Detail_Lanterns', sides=4, caps=False)
        zb_ = ztop - .45
        lathe(f'Detail_Lanterns_capB{x:+.1f}', [(.05, zb_ + .005), (.07, zb_), (.07, zb_ - .02), (.04, zb_ - .03)], 'bronze', 'Detail_Lanterns', seg=16, center=(x, y, 0))
        tube(f'Detail_Lanterns_tassel{x:+.1f}', [(x, y, zb_ - .03), (x, y, zb_ - .22)], .012, 'cloth', 'Detail_Lanterns', sides=6, radii=[.008, .014])
    for x in lantern_x: lantern(x)
    if corner: turned(lambda: lantern(.55))
    cols = [('box', (x, y, 1.5), (.3, .3, 3)) for x, y in posts]
    cols += [('box', (0, back_y + .07, 1.4), (2 * px, .12, 2.8)), ('box', (-px, (enc_y + back_y) / 2, 1.4), (.12, back_y - enc_y, 2.8)),
             ('box', (px, (enc_y + back_y) / 2, 1.4), (.12, back_y - enc_y, 2.8)), ('box', (-1.3, enc_y + .07, 1.4), (1.0, .12, 2.8)),
             ('box', (1.3, enc_y + .07, 1.4), (1.0, .12, 2.8)), ('box', (0, enc_y + .07, 2.5), (1.6, .12, 1.0)),
             ('box', (0, (front_y + enc_y) / 2, .025), (2 * px, enc_y - front_y, .05)), ('box', ((cx0 + cx1) / 2, cy, ch / 2 + .02), (cx1 - cx0, cd, ch + .04))]
    if lattice: cols += [('box', (sx * px, (front_y + enc_y) / 2, 1.2), (.08, enc_y - front_y - .3, 2.3)) for sx in (-1, 1)]
    return {'collision': cols, 'veranda': [-half, enc_y], 'openFaces': ['-Y', '+X'] if corner else ['-Y'], 'counterEdge_m': [round(cx0, 3), round(cx1, 3), round(cy - cd / 2, 3), round(ch + .045, 3)]}

def SF01(): return SF('SF01', 5201)
def SF02(): return SF('SF02', 5202, lattice=True, counter=1, mid_sets=False)
def SF03(): return SF('SF03', 5203, corner=True)

# ------------------------------------------------------------------ HM upper home bays
def HM(mid, seed, windows, braces=False, right_windows=()):
    """upper home bay 4 x 4 x 3 m on the SF / HM top plate: square cedar corner posts, sill plate, waist rail, lintel and the same
    top plate as SF (z 2.86-3.0) so every roof bay fits; lime-plaster infill (recessed behind the timber) with repair patches and
    rain streaks; narrow paper-lattice windows (paper is Glow) with sills and frames; a plank apron band under the front windows;
    optional diagonal braces (HM02). windows / right_windows: list of (x_centre, width) on the front (-Y) / right (+X) face."""
    rg = random.Random(seed); half = GRID / 2; px = half - .2; H = 3.0
    zs0, zs1, zw0, zw1, zl0, zl1 = 0.0, .18, .95, 1.07, 2.6, 2.86
    wz0, wz1 = 1.18, 2.22
    for i, (x, y) in enumerate(((-px, -px), (px, -px), (px, px), (-px, px))):
        o = box(f'{mid}_post{i}', (.22, .22, zl1 - .014), (x, y, (zl1 - .014) / 2 + .004), 'beam', 'Main', bev=.014, axis=(0, 0, 1))
    def face(side, wins, brace):
        n0 = len(parts); sd = .012 if side % 2 else 0
        L0, L1 = -px - .09, px + .09
        beam(f'{mid}_sill{side}', (L0, -px, (zs0 + zs1) / 2), (L1, -px, (zs0 + zs1) / 2), .2 - sd, zs1 - zs0 - sd, 'beam', 'Main', bev=.012)
        beam(f'{mid}_lintel{side}', (L0 + .02, -px, (zl0 + zl1) / 2), (L1 - .02, -px, (zl0 + zl1) / 2), .16 - sd, zl1 - zl0 - sd, 'beam', 'Main', bev=.012)
        beam(f'{mid}_plate{side}', (-half + .06, -px, H - .07 - sd / 2), (half - .06, -px, H - .07 - sd / 2), .22 - sd, .14 - sd, 'beam', 'Main', bev=.012)
        if True:
            beam(f'{mid}_waist{side}', (-px, -px, (zw0 + zw1) / 2), (px, -px, (zw0 + zw1) / 2), .14 - sd, zw1 - zw0, 'beam', 'Main', bev=.01)
        # infill rectangles around the window holes
        x0, x1 = -px + .11, px - .11
        lo = zw1
        holes = sorted((c - w / 2 - .06, c + w / 2 + .06) for c, w in wins)
        rects = []; xc = x0
        for a, b in holes:
            rects.append((xc, a, lo, zl0)); rects.append((a, b, lo, wz0 - .06)); rects.append((a, b, wz1 + .06, zl0)); xc = b
        rects.append((xc, x1, lo, zl0))
        studs = [] if any(abs(c) < w / 2 + .3 for c, w in wins) else [0.0]   # centre stud where no window sits
        rects_low = [(x0, x1, zs1, zw0)]
        if studs:
            rects = [r2 for r in rects for r2 in ((r[0], -.06, r[2], r[3]), (.06, r[1], r[2], r[3])) if r[0] < 0 < r[1]] + [r for r in rects if not (r[0] < 0 < r[1])]
            rects_low = [(x0, -.06, zs1, zw0), (.06, x1, zs1, zw0)] if side else rects_low
            beam(f'{mid}_stud{side}', (0, -px, zs1), (0, -px, zl0), .13, .12, 'beam', 'Main', bev=.01)
        for k, (a, b, z0, z1) in enumerate(rects):
            if b - a < .02 or z1 - z0 < .02: continue
            box(f'{mid}_plaster{side}_{k}', (b - a + .01, .08 + .004 * (k % 2), z1 - z0 + .01), ((a + b) / 2, -px, (z0 + z1) / 2), 'plaster', 'Main', bev=0)
        if side == 0:   # plank apron under the windows, vertical boards with a batten
            xa = x0
            while xa < x1 - .01:
                w = min(rg.uniform(.2, .28), x1 - xa)
                if x1 - (xa + w) < .08: w = x1 - xa
                box(f'{mid}_apron{k}_{xa:.2f}', (w - .006, .04, zw0 - zs1 + .01), (xa + w / 2, -px - .03, (zs1 + zw0) / 2), 'plank' if rg.random() > .2 else 'oldwood', 'Main', bev=.005, axis=(0, 0, 1))
                xa += w
            beam(f'{mid}_apronbatten', (x0, -px - .06, (zs1 + zw0) / 2), (x1, -px - .06, (zs1 + zw0) / 2), .025, .07, 'beam', 'Main', bev=.005)
        else:
            for k, (a, b, z0, z1) in enumerate(rects_low):
                box(f'{mid}_plasterlow{side}_{k}', (b - a + .01, .086 + .004 * (k % 2), z1 - z0 + .01), ((a + b) / 2, -px, (z0 + z1) / 2), 'plaster', 'Main', bev=0)
        for k, (c, w) in enumerate(wins):   # window: studs, head, sill board, lattice, paper
            for sx in (-1, 1): beam(f'{mid}_wstud{side}{k}{sx}', (c + sx * (w / 2 + .03), -px, lo), (c + sx * (w / 2 + .03), -px, zl0), .12, .06, 'beam', 'Main', bev=.006)
            beam(f'{mid}_whead{side}{k}', (c - w / 2 - .06, -px, wz1 + .03), (c + w / 2 + .06, -px, wz1 + .03), .11, .06, 'beam', 'Main', bev=.006)
            beam(f'{mid}_wsill{side}{k}', (c - w / 2 - .1, -px - .03, wz0 - .035), (c + w / 2 + .1, -px - .03, wz0 - .035), .16, .05, 'beam', 'Main', bev=.008)
            for j, xx in enumerate(np.linspace(c - w / 2, c + w / 2, 4)[1:-1]):
                box(f'{mid}_wbarv{side}{k}{j}', (.018, .02, wz1 - wz0 + .02), (xx, -px - .03, (wz0 + wz1) / 2), 'beam', 'Main', bev=.003, axis=(0, 0, 1))
            for j, zz in enumerate(np.linspace(wz0, wz1, 7)[1:-1]):
                box(f'{mid}_wbarh{side}{k}{j}', (w + .02, .018, .018), (c, -px - .026, zz), 'beam', 'Main', bev=.003, axis=(1, 0, 0))
            for nm, a_, b_ in (('l', (c - w / 2 - .11, wz0 - .07), (c - w / 2 - .11, wz1 + .1)), ('r', (c + w / 2 + .11, wz0 - .07), (c + w / 2 + .11, wz1 + .1)),
                               ('t', (c - w / 2 - .14, wz1 + .1), (c + w / 2 + .14, wz1 + .1))):
                beam(f'{mid}_warch{side}{k}{nm}', (a_[0], -px - .045, a_[1]), (b_[0], -px - .045, b_[1]), .04, .06, 'beam', 'Main', bev=.006)
            box(f'Glow_window{side}{k}', (w + .02, .006, wz1 - wz0 + .02), (c, -px - .012, (wz0 + wz1) / 2), 'paper', 'Glow', bev=0)
            parts[-1].data.materials.clear(); parts[-1].data.materials.append(MAT[1])
        if brace:   # diagonal braces in the panels beside the window
            for sx in (-1, 1):
                inner = min((abs(c) - w / 2 - .12 for c, w in wins if c * sx >= 0), default=.4)
                xa_, xb_ = sx * (px - .14), sx * max(.3, inner)
                beam(f'{mid}_brace{side}{sx}', (xa_, -px - .035, lo + .04), (xb_, -px - .035, zl0 - .04), .05, .11, 'beam', 'Main', bev=.008)
        # repair patches on the plaster (slightly proud, a different tone from the trim strip)
        for k in range(rg.randint(2, 4)):
            a, b, z0, z1 = rg.choice([r for r in rects if r[1] - r[0] > .35 and r[3] - r[2] > .35])
            w_, h_ = rg.uniform(.16, min(.45, b - a - .08)), rg.uniform(.12, min(.35, z1 - z0 - .08))
            cx_, cz_ = rg.uniform(a + w_ / 2 + .04, b - w_ / 2 - .04), rg.uniform(z0 + h_ / 2 + .04, z1 - h_ / 2 - .04)
            poly = [(cx_ + w_ / 2 * (.75 + .25 * rg.random()) * math.cos(a_), cz_ + h_ / 2 * (.75 + .25 * rg.random()) * math.sin(a_)) for a_ in np.linspace(0, math.tau, 10, endpoint=False)]
            prism_xz(f'{mid}_patch{side}{k}', poly, .012, -px - .049 + .0015 * k, 'granite_moss' if k % 2 == 0 else 'plaster', 'Main', bev=.003)
        for o in parts[n0:]: rotz(o, side * math.pi / 2)
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):   # bronze corner straps where the posts meet sill and lintel
        for zz in (.09, zl0 + .13):
            box(f'{mid}_strapx{i}{zz:.2f}', (.12, .012, .14), (sx * (px + .05), sy * (px + .116), zz), 'bronze', 'Main', bev=.003)
            box(f'{mid}_strapy{i}{zz:.2f}', (.012, .12, .14), (sx * (px + .116), sy * (px + .05), zz), 'bronze', 'Main', bev=.003)
    face(0, windows, braces); face(1, list(right_windows), braces); face(2, [], braces); face(3, [], braces)
    box(f'{mid}_floor', (2 * px - .1, 2 * px - .1, .04), (0, 0, zs1 - .024), 'plank', 'Main', bev=0, axis=(1, 0, 0))
    box(f'{mid}_ceil', (2 * px - .1, 2 * px - .1, .03), (0, 0, zl0 - .015), 'dark', 'Main', bev=0)
    return {'collision': [('box', (0, 0, H / 2), (2 * px + .22, 2 * px + .22, H))], 'windows': {'front': windows, 'right': list(right_windows)}}

def HM01(): return HM('HM01', 5301, [(-.7, .46), (.7, .46)])
def HM02(): return HM('HM02', 5302, [(0.0, .5)], braces=True)
def HM03(): return HM('HM03', 5303, [(-.5, .42)], right_windows=[(.3, .42)])

# ------------------------------------------------------------------ RF01 hip-and-gable roof bay
def RF01():
    """歇山 roof over a 4 x 4 m bay, base z = 0 on the SF/HM top plate. Concave slopes (z ~ t^1.6 from eave to ridge) with
    lifted corners; modelled pan-tile surface with channels, cover-tile rows (each tile a bump), eave end caps, main ridge
    with scroll end ornaments, hip ridges with upturned ends, gable triangle boards + bargeboards + 懸魚, visible rafters and
    a soffit under the overhang."""
    rg = random.Random(5301); E = 2.7; ze = .34; zr = 1.55; xg = 1.72; zgb = .82; p = 1.3; xr = xg + .02
    def lift(x, y):   # 翹角: corners rise near the eave
        c = max(0.0, (abs(x) + abs(y) - 4.2) / (2 * E - 4.2)); return .16 * c ** 2.0
    def z_fb(y): t = max(0.0, min(1.0, (E - abs(y)) / E)); return ze + (zr - ze) * t ** p
    def z_side(x): t = max(0.0, min(1.0, (E - abs(x)) / (E - xg))); return ze + (zgb - ze) * t ** p
    def z_at(x, y):
        a = z_fb(y); b = z_side(x) if abs(x) > xg else 9; return min(a, b) + lift(x, y)
    # base surface grid (pan tiles): solidified 5 cm, channels between cover rows
    sp = .24; nx = int(2 * E / .06); bm = bmesh.new(); vs = {}
    for i in range(nx + 1):
        for j in range(nx + 1):
            x = -E + 2 * E * i / nx; y = -E + 2 * E * j / nx; z = z_at(x, y)
            on_side = abs(x) > xg and z_side(x) < z_fb(y)
            ch = (x if not on_side else y); z -= .018 * (.5 + .5 * math.cos(ch / sp * math.tau))
            vs[i, j] = bm.verts.new((x, y, z))
    for i in range(nx):
        for j in range(nx): bm.faces.new((vs[i, j], vs[i + 1, j], vs[i + 1, j + 1], vs[i, j + 1]))
    pan = finish('RF01_pan', bm, 'tile', 'Main', axis=(1, 0, 0), smooth=True)
    m = pan.modifiers.new('t', 'SOLIDIFY'); m.thickness = .05; m.offset = -1; apply(pan, m); reuv(pan, 'tile', (1, 0, 0))
    # cover-tile rows: one tube per row following the active slope from the eave up to the ridge / hip line, a bump per tile
    def row(path_fn, n, name):
        pts = []; rad = []
        for k in range(n + 1):
            s = k / n; P = path_fn(s)
            if P is None: break
            pts.append(P); seg = (s * n * .5) % 1; rad.append(.052 + .010 * (seg < .18))   # P sits 2 cm above the pan: tube bottom buried in the 5 cm pan slab
        if len(pts) <= 7: return []   # stub under the hip ridge: no tile, no eave cap
        tube(name, pts, .05, 'tile' if rg.random() > .3 else 'tile_moss', 'Main', sides=8, radii=rad)
        return pts
    ncov = 0; eaves = []
    for sgn in (-1, 1):   # front / back slopes: rows along y
        for x in np.arange(-E + sp / 2, E, sp):
            def pf(s, x=x, sgn=sgn):
                y = sgn * (E + .015 - s * (E + .015))   # cover tiles overhang the pan edge by 1.5 cm
                if abs(x) > xg and z_side(x) < z_fb(y) + .06: return None   # stop short of the hip crease (the hip ridge covers it)
                return (x, y, z_at(x, y) + .02)
            # start at the eave even where the hip is active at the corners: only keep rows whose eave point is on this slope
            if abs(x) > xg and z_side(x) < z_fb(sgn * E) - .005:
                continue
            pts = row(pf, 40, f'RF01_cov_fb{sgn:+d}_{ncov}'); ncov += 1
            if pts: eaves.append((Vector(pts[0]), Vector((0, sgn, 0))))
    for sgn in (-1, 1):   # side hip slopes: rows along x, stop at the hip line / gable base
        for y in np.arange(-E + sp / 2, E, sp):
            def ps(s, y=y, sgn=sgn):
                x = sgn * (E + .015 - s * (E + .015 - xg))
                if z_side(x) > z_fb(y) - .06: return None
                return (x, y, z_at(x, y) + .02)
            if z_side(sgn * E) > z_fb(y) - .005: continue
            pts = row(ps, 24, f'RF01_cov_s{sgn:+d}_{ncov}'); ncov += 1
            if pts: eaves.append((Vector(pts[0]), Vector((sgn, 0, 0))))
    # eave end caps 瓦當 (discs) and drip tiles 滴水 (small wedges between)
    for k, (P, d) in enumerate(eaves):
        c = P + d * .008 + Vector((0, 0, -.004)); lathe(f'RF01_cap{k}', [(.004, -.015), (.062, -.015), (.062, .015), (.004, .015)], 'tile', 'Main', seg=12, center=(0, 0, 0))
        o = parts[-1]; t = d.normalized(); u = Vector((0, 0, 1)); s = u.cross(t)   # right-handed (s, u, t)
        o.data.transform(Matrix(((s.x, u.x, t.x, c.x), (s.y, u.y, t.y, c.y), (s.z, u.z, t.z, c.z), (0, 0, 0, 1))))
    # ridges: main ridge (stacked tile courses), hip ridges from the gable foot to the lifted corners, gable verge ridges
    def ridge(name, pts, w=.11, h=.16):
        tube(name, [Vector(q) for q in pts], w, 'tile', 'Main', sides=10, radii=None)
    ridge('RF01_ridge', [(-xr - .1, 0, zr + .06), (xr + .1, 0, zr + .06)], .13)
    for x in (-xr - .1, xr + .1):
        s = 1 if x > 0 else -1; c = Vector((x, 0, zr + .06))
        curl = [c + Vector((s * .06 * math.sin(a) * (1 - a / 6), 0, .13 * (1 - math.cos(a)) * (1 - a / 8))) for a in np.linspace(0, 4.2, 14)]
        tube(f'RF01_ornament{s:+d}', curl, .07, 'tile', 'Main', sides=10, radii=list(np.linspace(.09, .04, 14)))
    yfoot = E * (1 - ((zgb - ze) / (zr - ze)) ** (1 / p))   # where the front slope reaches the gable base height
    def hip_y(x):   # true hip line: z_fb(y) == z_side(x)
        return E * (1 - ((z_side(x) - ze) / (zr - ze)) ** (1 / p))
    for sx in (-1, 1):
        for sy in (-1, 1):
            pts = [Vector((sx * x, sy * hip_y(x), 0)) for x in np.linspace(xg, E - .04, 16)]
            pts = [Vector((q.x, q.y, z_at(q.x, q.y) + .09)) for q in pts]
            tip = pts[-1] + Vector((sx * .03, sy * .03, .08))
            ridge(f'RF01_hip{sx:+d}{sy:+d}', pts + [tip], .085)
            # verge ridge along the gable edge from the main ridge down to the gable foot
            vp = [Vector((sx * (xg + .08), sy * yy, z_fb(yy) + .08)) for yy in np.linspace(0, yfoot, 12)]
            ridge(f'RF01_verge{sx:+d}{sy:+d}', vp, .07)
    # gable triangles: vertical boards at x = ±xg, bargeboards along the slope, 懸魚 at the apex
    for sx in (-1, 1):
        poly = [(yy, z_fb(yy) - .02) for yy in np.linspace(-yfoot, yfoot, 25)] + [(yfoot, zgb), (-yfoot, zgb)]
        bm = bmesh.new(); v = [bm.verts.new((sx * (xg + .03), y, z)) for y, z in poly]; bm.faces.new(v if sx > 0 else list(reversed(v)))
        bmesh.ops.triangle_fill(bm, use_beauty=True, edges=bm.edges) if False else None
        g = finish(f'RF01_gable{sx:+d}', bm, 'plank', 'Main', axis=(0, 0, 1))
        m = g.modifiers.new('t', 'SOLIDIFY'); m.thickness = .04; m.offset = 0; apply(g, m); reuv(g, 'plank', (0, 0, 1))
        for k, yy in enumerate(np.linspace(-yfoot + .12, yfoot - .12, 9)):   # vertical battens on the gable boards
            zt = z_fb(yy) - .06
            if zt > zgb + .05: box(f'RF01_batten{sx:+d}{k}', (.03, .05, zt - zgb), (sx * (xg + .064), yy, (zt + zgb) / 2), 'beam', 'Main', bev=.004, axis=(0, 0, 1))
        for sy in (-1, 1):
            pts = [Vector((sx * (xg + .09), sy * yy, z_fb(yy) - .03)) for yy in np.linspace(0, yfoot + .1, 14)]
            for k in range(len(pts) - 1): pass
            tube(f'RF01_barge{sx:+d}{sy:+d}', pts, .045, 'beam', 'Main', sides=6)
        fish = [(0, zr - .12)] + [(sy * (.10 + .05 * math.sin(t * 3)), zr - .12 - .35 * t) for sy in (1,) for t in np.linspace(.05, 1, 8)] + \
               [(0, zr - .55)] + [(-(.10 + .05 * math.sin(t * 3)), zr - .12 - .35 * t) for t in np.linspace(1, .05, 8)]
        bm = bmesh.new(); v = [bm.verts.new((sx * (xg + .11), y, z)) for y, z in fish]; bm.faces.new(v)
        f = finish(f'RF01_fish{sx:+d}', bm, 'beam', 'Main', axis=(0, 0, 1)); m = f.modifiers.new('t', 'SOLIDIFY'); m.thickness = .03; apply(f, m); reuv(f, 'beam', (0, 0, 1))
    # rafters 椽 under the overhang (round, every 22 cm) and the soffit boards; eave purlin at the wall line
    # rafters sit just under the tile surface from the wall line to the eave; an eave purlin 檐檩 carries them on the wall
    # line and a frieze board 墊板 closes the gap down to the top plate (z = 0)
    w = GRID / 2 - .05
    for sgn in (-1, 1):
        for x in np.arange(-w + .1, w, .22):
            y0 = sgn * w; y1 = sgn * (E - .06)
            tube(f'RF01_raft_fb{sgn:+d}{x:+.2f}', [(x, y0, z_at(x, y0) - .10), (x, y1, z_at(x, y1) - .08)], .04, 'beam', 'Main', sides=8)
        for y in np.arange(-w + .1, w, .22):
            x0 = sgn * w; x1 = sgn * (E - .06)
            tube(f'RF01_raft_s{sgn:+d}{y:+.2f}', [(x0, y, z_at(x0, y) - .10), (x1, y, z_at(x1, y) - .08)], .04, 'beam', 'Main', sides=8)
    zp_fb = z_fb(w) - .22; zp_s = z_side(w) - .22
    for sgn in (-1, 1):
        beam(f'RF01_purlin_fb{sgn:+d}', (-GRID / 2, sgn * w, zp_fb), (GRID / 2, sgn * w, zp_fb), .16, .16, 'beam', 'Main', bev=.012)
        beam(f'RF01_purlin_s{sgn:+d}', (sgn * w, -GRID / 2, zp_s), (sgn * w, GRID / 2, zp_s), .16, .16, 'beam', 'Main', bev=.012)
        box(f'RF01_frieze_fb{sgn:+d}', (GRID - .1, .05, zp_fb - .07), (0, sgn * (w - .02), (zp_fb - .07) / 2), 'plank', 'Main', bev=.004, axis=(1, 0, 0))
        box(f'RF01_frieze_s{sgn:+d}', (.05, GRID - .14, zp_s - .07), (sgn * (w - .02), 0, (zp_s - .07) / 2), 'plank', 'Main', bev=.004, axis=(0, 1, 0))
    box('RF01_ceiling', (2 * (w - .045), 2 * (w - .045), .03), (0, 0, .02), 'dark', 'Main', bev=0)
    return {'collision': [('box', (0, 0, .9), (2 * E, 2 * E, 1.6))]}

def RF(mid, kind, seed):
    """roof bays built with the RF01 hand (concave slopes, modelled pan + cover tiles, eave caps, ridge, rafters, purlins).
    kind 'gable' (RF02 硬山): ridge along X, front/back slopes with 0.7 m eaves, flush gable ends at X = ±2 m (verge tiles,
      bargeboards, plank gable infill) so bays join side by side along a street.
    kind 'end' (RF03): the -X end flush like RF02, the +X end a hip-and-gable corner with gently lifted eaves (ends a row).
    kind 'lean' (RF04): one slope from the street eave up to a higher wall at +Y with a row of fitted ridge tiles and a
      flashing board against that wall (tiered cliff streets: a lower roof tucked under the next terrace)."""
    rg = random.Random(seed); E = 2.7; ze = .34; zr = 1.55; p = 1.3; half = GRID / 2; sp = .24
    xg = 1.72; zgb = .82
    xa = -half; xb = E if kind == 'end' else half
    yb = half if kind == 'lean' else E; zt = 1.35
    def z_fb(y):
        if kind == 'lean':
            t = max(0.0, min(1.0, (y + E) / (E + half))); return ze + (zt - ze) * t ** p
        t = max(0.0, min(1.0, (E - abs(y)) / E)); return ze + (zr - ze) * t ** p
    def z_side(x): t = max(0.0, min(1.0, (E - x) / (E - xg))); return ze + (zgb - ze) * t ** p
    def lift(x, y):
        if kind != 'end' or x < 0: return 0.0
        c = max(0.0, (x + abs(y) - 4.2) / (2 * E - 4.2)); return .14 * c ** 2.0
    def hipped(x, y): return kind == 'end' and x > xg and z_side(x) < z_fb(y)
    def z_at(x, y): return (min(z_fb(y), z_side(x)) if kind == 'end' and x > xg else z_fb(y)) + lift(x, y)
    pa_, pb_ = xa + .014, (xb - .014 if kind != 'end' else xb)   # solidify widens the slab edge: keep flush ends inside the 4 m bay
    nx = int(round((pb_ - pa_) / .06)); ny = int(round((yb + E) / .06)); bm = bmesh.new(); vs = {}
    for i in range(nx + 1):
        for j in range(ny + 1):
            x = pa_ + (pb_ - pa_) * i / nx; y = -E + (yb + E) * j / ny; z = z_at(x, y)
            ch = y if hipped(x, y) else x; z -= .018 * (.5 + .5 * math.cos(ch / sp * math.tau))
            vs[i, j] = bm.verts.new((x, y, z))
    for i in range(nx):
        for j in range(ny): bm.faces.new((vs[i, j], vs[i + 1, j], vs[i + 1, j + 1], vs[i, j + 1]))
    pan = finish(f'{mid}_pan', bm, 'tile', 'Main', axis=(1, 0, 0), smooth=True)
    m = pan.modifiers.new('t', 'SOLIDIFY'); m.thickness = .05; m.offset = -1; apply(pan, m); reuv(pan, 'tile', (1, 0, 0))
    def row(path_fn, n, name):
        pts = []; rad = []
        for k in range(n + 1):
            s_ = k / n; P = path_fn(s_)
            if P is None: break
            pts.append(P); seg = (s_ * n * .5) % 1; rad.append(.052 + .010 * (seg < .18))
        if len(pts) <= 7: return []
        tube(name, pts, .05, 'tile' if rg.random() > .3 else 'tile_moss', 'Main', sides=8, radii=rad)
        return pts
    eaves = []; ncov = 0
    sgns = (-1,) if kind == 'lean' else (-1, 1)
    for sgn in sgns:
        for x in np.arange(xa + sp / 2, xb - .05, sp):
            if kind == 'end' and x > xg and z_side(x) < z_fb(sgn * E) - .005: continue
            top_y = yb - .08 if kind == 'lean' else 0.0
            def pf(s_, x=x, sgn=sgn, top_y=top_y):
                y0 = sgn * (E + .015); y = y0 + (top_y - y0) * s_
                if kind == 'end' and x > xg and z_side(x) < z_fb(y) + .06: return None
                return (x, y, z_at(x, y) + .02)
            pts = row(pf, 44 if kind == 'lean' else 40, f'{mid}_cov{sgn:+d}_{ncov}'); ncov += 1
            if pts: eaves.append((Vector(pts[0]), Vector((0, sgn, 0))))
    if kind == 'end':
        for y in np.arange(-E + sp / 2, E, sp):
            def ps(s_, y=y):
                x = E + .015 - s_ * (E + .015 - xg)
                if z_side(x) > z_fb(y) - .06: return None
                return (x, y, z_at(x, y) + .02)
            if z_side(E) > z_fb(y) - .005: continue
            pts = row(ps, 24, f'{mid}_covs_{ncov}'); ncov += 1
            if pts: eaves.append((Vector(pts[0]), Vector((1, 0, 0))))
    for k, (P, d) in enumerate(eaves):
        c = P + d * .008 + Vector((0, 0, -.004)); lathe(f'{mid}_cap{k}', [(.004, -.015), (.062, -.015), (.062, .015), (.004, .015)], 'tile', 'Main', seg=12)
        o = parts[-1]; t = d.normalized(); u = Vector((0, 0, 1)); s_ = u.cross(t)
        o.data.transform(Matrix(((s_.x, u.x, t.x, c.x), (s_.y, u.y, t.y, c.y), (s_.z, u.z, t.z, c.z), (0, 0, 0, 1))))
    def ornament(x, s_, z0):   # scroll end ornament curling back over the roof (stays inside the bay)
        c = Vector((x, 0, z0))
        curl = [c + Vector((-s_ * .06 * math.sin(a) * (1 - a / 6), 0, .13 * (1 - math.cos(a)) * (1 - a / 8))) for a in np.linspace(0, 4.2, 14)]
        tube(f'{mid}_ornament{s_:+d}', curl, .07, 'tile', 'Main', sides=10, radii=list(np.linspace(.09, .04, 14)))
    if kind in ('gable', 'end'):
        x1 = (xg + .12) if kind == 'end' else xb - .1
        tube(f'{mid}_ridge', [Vector((xa + .1, 0, zr + .06)), Vector((x1, 0, zr + .06))], .13, 'tile', 'Main', sides=10)
        ornament(xa + .14, -1, zr + .06)
        if kind == 'gable': ornament(xb - .14, 1, zr + .06)
        else:
            c = Vector((x1, 0, zr + .06)); curl = [c + Vector((.06 * math.sin(a) * (1 - a / 6), 0, .13 * (1 - math.cos(a)) * (1 - a / 8))) for a in np.linspace(0, 4.2, 14)]
            tube(f'{mid}_ornamentE', curl, .07, 'tile', 'Main', sides=10, radii=list(np.linspace(.09, .04, 14)))
    else:   # lean-to: fitted ridge tiles against the upper wall, one tile per 30 cm, plus the flashing board
        ztop = z_fb(yb)
        for k, x0 in enumerate(np.arange(xa + .05, xb - .05, .30)):
            x1_ = min(xb - .04, x0 + .33)
            tube(f'{mid}_ridgetile{k}', [Vector((x0, yb - .1, ztop + .03)), Vector((x1_, yb - .1, ztop + .03))], .085, 'tile' if k % 4 else 'tile_moss', 'Main', sides=10,
                 radii=[.08, .088])
        box(f'{mid}_flashing', (xb - xa - .04, .04, .42), (0, yb - .025, ztop + .12), 'plank', 'Main', bev=.006, axis=(1, 0, 0))
        beam(f'{mid}_flashcap', (xa + .03, yb - .05, ztop + .34), (xb - .03, yb - .05, ztop + .34), .1, .06, 'beam', 'Main', bev=.008)
    # flush gable ends: verge tiles + bargeboard along the slope edge, plank infill down to the top plate
    ends = [xa] if kind == 'end' else [xa, xb]
    for xe in ends:
        sx = 1 if xe > 0 else -1
        ys = np.linspace(-E, yb if kind == 'lean' else 0, 16)
        if kind != 'lean':
            for sy in (-1, 1):
                tube(f'{mid}_verge{sx:+d}{sy:+d}', [Vector((xe - sx * .07, sy * abs(y), z_fb(y) + .07)) for y in ys], .07, 'tile', 'Main', sides=10)
                tube(f'{mid}_barge{sx:+d}{sy:+d}', [Vector((xe - sx * .045, sy * abs(y), z_fb(y) - .05)) for y in ys], .04, 'beam', 'Main', sides=6)
        else:
            tube(f'{mid}_verge{sx:+d}', [Vector((xe - sx * .07, y, z_fb(y) + .07)) for y in ys], .07, 'tile', 'Main', sides=10)
            tube(f'{mid}_barge{sx:+d}', [Vector((xe - sx * .045, y, z_fb(y) - .05)) for y in ys], .04, 'beam', 'Main', sides=6)
        yy = np.linspace(-half + .02, half - .02, 21) if kind != 'lean' else np.linspace(-half + .02, half - .02, 21)
        poly = [(y, z_fb(y) - .07) for y in yy] + [(half - .02, .0), (-half + .02, .0)]
        bmg = bmesh.new(); v = [bmg.verts.new((xe - sx * .09, y, z)) for y, z in poly]; bmg.faces.new(v if sx > 0 else list(reversed(v)))
        g = finish(f'{mid}_gable{sx:+d}', bmg, 'plank', 'Main', axis=(0, 0, 1))
        m = g.modifiers.new('t', 'SOLIDIFY'); m.thickness = .04; m.offset = 0; apply(g, m); reuv(g, 'plank', (0, 0, 1))
        for k, y in enumerate(np.linspace(-half + .25, half - .25, 9)):
            ztop_ = z_fb(y) - .1
            if ztop_ > .1: box(f'{mid}_batten{sx:+d}{k}', (.03, .05, ztop_ - .02), (xe - sx * .126, y, (ztop_ + .02) / 2), 'beam', 'Main', bev=.004, axis=(0, 0, 1))
    if kind == 'end':   # +X hip-and-gable corner as RF01: hip ridges, verge at the gable, gable boards and 懸魚
        yfoot = E * (1 - ((zgb - ze) / (zr - ze)) ** (1 / p))
        def hip_y(x): return E * (1 - ((z_side(x) - ze) / (zr - ze)) ** (1 / p))
        for sy in (-1, 1):
            pts = [Vector((x, sy * hip_y(x), 0)) for x in np.linspace(xg, E - .04, 16)]
            pts = [Vector((q.x, q.y, z_at(q.x, q.y) + .09)) for q in pts]
            tube(f'{mid}_hip{sy:+d}', pts + [pts[-1] + Vector((.03, sy * .03, .08))], .085, 'tile', 'Main', sides=10)
            tube(f'{mid}_vergeH{sy:+d}', [Vector((xg + .08, sy * yy_, z_fb(yy_) + .08)) for yy_ in np.linspace(0, yfoot, 12)], .07, 'tile', 'Main', sides=10)
            tube(f'{mid}_bargeH{sy:+d}', [Vector((xg + .09, sy * yy_, z_fb(yy_) - .03)) for yy_ in np.linspace(0, yfoot + .1, 14)], .045, 'beam', 'Main', sides=6)
        poly = [(yy_, z_fb(yy_) - .02) for yy_ in np.linspace(-yfoot, yfoot, 25)] + [(yfoot, zgb), (-yfoot, zgb)]
        bmg = bmesh.new(); v = [bmg.verts.new((xg + .03, y, z)) for y, z in poly]; bmg.faces.new(v)
        g = finish(f'{mid}_gableH', bmg, 'plank', 'Main', axis=(0, 0, 1)); m = g.modifiers.new('t', 'SOLIDIFY'); m.thickness = .04; m.offset = 0; apply(g, m); reuv(g, 'plank', (0, 0, 1))
        fish = [(0, zr - .12)] + [((.10 + .05 * math.sin(t * 3)), zr - .12 - .35 * t) for t in np.linspace(.05, 1, 8)] + \
               [(0, zr - .55)] + [(-(.10 + .05 * math.sin(t * 3)), zr - .12 - .35 * t) for t in np.linspace(1, .05, 8)]
        bmf = bmesh.new(); v = [bmf.verts.new((xg + .11, y, z)) for y, z in fish]; bmf.faces.new(v)
        fo = finish(f'{mid}_fish', bmf, 'beam', 'Main', axis=(0, 0, 1)); m = fo.modifiers.new('t', 'SOLIDIFY'); m.thickness = .03; apply(fo, m); reuv(fo, 'beam', (0, 0, 1))
    # rafters under the eave overhang(s), eave purlins on the wall lines, frieze boards down to the top plate, dark ceiling
    w = half - .05
    for sgn in sgns:
        for x in np.arange(xa + .15, min(xb, w) - .05, .22):
            y0 = sgn * w; y1 = sgn * (E - .06)
            tube(f'{mid}_raft{sgn:+d}{x:+.2f}', [(x, y0, z_at(x, y0) - .10), (x, y1, z_at(x, y1) - .08)], .04, 'beam', 'Main', sides=8)
        zp = z_fb(sgn * w) - .22
        beam(f'{mid}_purlin{sgn:+d}', (xa + .1, sgn * w, zp), (min(xb, half) - .1, sgn * w, zp), .16, .16, 'beam', 'Main', bev=.012)
        box(f'{mid}_frieze{sgn:+d}', (GRID - .3, .05, zp - .07), (0, sgn * (w - .02), (zp - .07) / 2), 'plank', 'Main', bev=.004, axis=(1, 0, 0))
    if kind == 'end':
        for y in np.arange(-w + .1, w, .22):
            tube(f'{mid}_rafts{y:+.2f}', [(w, y, z_at(w, y) - .10), (E - .06, y, z_at(E - .06, y) - .08)], .04, 'beam', 'Main', sides=8)
        zp = z_side(w) - .22
        beam(f'{mid}_purlins', (w, -half + .1, zp), (w, half - .1, zp), .16, .16, 'beam', 'Main', bev=.012)
        box(f'{mid}_friezes', (.05, GRID - .3, zp - .07), (w - .02, 0, (zp - .07) / 2), 'plank', 'Main', bev=.004, axis=(0, 1, 0))
    if kind == 'lean':   # the back wall line of a lean-to sits on the wall: a plate beam carries the rafters' tops
        beam(f'{mid}_wallplate', (xa + .1, half - .12, z_fb(half - .12) - .2), (xb - .1, half - .12, z_fb(half - .12) - .2), .16, .16, 'beam', 'Main', bev=.012)
    box(f'{mid}_ceiling', (2 * (w - .045), 2 * (w - .045), .03), (0, 0, .02), 'dark', 'Main', bev=0)
    xs_c = (xa + xb) / 2
    return {'collision': [('box', (xs_c, (yb - E) / 2, .8), (xb - xa, yb + E, 1.5))], 'kind': kind, 'flushEnds': ['-X'] if kind == 'end' else ['-X', '+X']}

def RF02(): return RF('RF02', 'gable', 5402)
def RF03(): return RF('RF03', 'end', 5403)
def RF04(): return RF('RF04', 'lean', 5404)

# ------------------------------------------------------------------ CP cantilever platforms
def CP(mid, seed, corner=False):
    """timber cantilever platform 4 x 3 m projecting from a stone wall at +Y towards the street (-Y). Deck top at 1.8 m above
    the brace anchors (origin: footprint centre, z = 0 at the lowest anchor). Granite anchor blocks set into the wall line,
    cantilever joists with cut ends, rim beams, plank deck with replaced boards, diagonal braces from the low anchors up to the
    joists with bronze straps, a safe 1.05 m railing (posts, top and mid rails, balusters). corner (CP02): a second wall on -X,
    railing on the front and +X only, asymmetric braces including one long raking brace from the -X wall."""
    rg = random.Random(seed); W, D = GRID, 3.0; hx, hy = W / 2, D / 2; zd = 1.8; th = .06; jz = zd - th
    jx = (-1.62, -.55, .55, 1.62) if not corner else (-1.2, .1, 1.0, 1.62)
    # wall anchors (granite) on the wall line(s)
    for i, x in enumerate(jx):
        o = box(f'{mid}_anchorlo{i}', (.36, .3, .42), (x, hy - .15, .21), 'granite_moss', 'Main', bev=0, cuts=1); chisel(o, .01, 3, 7000 + i); bevel(o, .025, 2, 30)
        o = box(f'{mid}_anchorhi{i}', (.34, .24, .3), (x, hy - .12, jz - .24 - .15), 'granite', 'Main', bev=0, cuts=1); chisel(o, .008, 3, 7100 + i); bevel(o, .02, 2, 30)
    if corner:
        for i, y in enumerate((-.9, .3)):
            o = box(f'{mid}_anchorside{i}', (.3, .36, .42), (-hx + .15, y, .21), 'granite_moss', 'Main', bev=0, cuts=1); chisel(o, .01, 3, 7200 + i); bevel(o, .025, 2, 30)
    # joists, rims, deck
    for i, x in enumerate(jx):
        beam(f'{mid}_joist{i}', (x, hy - .02, jz - .12), (x, -hy + .1, jz - .12), .17, .24, 'beam', 'Main', bev=.012)
        prism_xz(f'{mid}_joistend{i}', [(x - .09, jz - .245), (x + .09, jz - .245), (x + .09, jz - .004), (x - .09, jz - .004)], .06, -hy + .03, 'beam', 'Main', bev=.006)
    beam(f'{mid}_rimF', (-hx + .04, -hy + .07, jz - .1), (hx - .04, -hy + .07, jz - .1), .12, .2, 'beam', 'Main', bev=.01)
    for sx in (-1, 1):
        if corner and sx < 0: continue
        beam(f'{mid}_rimS{sx:+d}', (sx * (hx - .06), -hy + .14, jz - .09), (sx * (hx - .06), hy - .04, jz - .09), .1, .18, 'beam', 'Main', bev=.01)
    if corner: beam(f'{mid}_ledger', (-hx + .06, -hy + .14, jz - .09), (-hx + .06, hy - .04, jz - .09), .1, .18, 'beam', 'Main', bev=.01)
    y = -hy + .01; k = 0
    while y < hy - .02:
        w = min(rg.uniform(.19, .26), hy - .01 - y); o = box(f'{mid}_deck{k}', (W - .02, w - .008, th), (0, y + w / 2, jz + th / 2 - .003), 'plank' if rg.random() > .18 else 'oldwood', 'Main', bev=.006, axis=(1, 0, 0))
        y += w; k += 1
    # diagonal braces from the low anchors to the joists; bronze straps at the top joint
    for i, x in enumerate(jx):
        yt = -.55 - (.25 if corner and i == 0 else 0) + (.2 if corner and i == 2 else 0)
        beam(f'{mid}_brace{i}', (x, hy - .25, .3), (x, yt, jz - .2), .15, .15, 'beam', 'Main', bev=.01)
        box(f'{mid}_strap{i}', (.19, .3, .012), (x, yt + .05, jz - .3), 'bronze', 'Main', bev=.003)
        beam(f'{mid}_knee{i}', (x, hy - .2, jz - .5), (x, hy - .6, jz - .2), .12, .12, 'beam', 'Main', bev=.008)
    if corner:   # long raking brace from the -X wall anchor to the front-right joist
        beam(f'{mid}_rake', (-hx + .25, -.9, .3), (jx[1], -hy + .35, jz - .2), .15, .15, 'beam', 'Main', bev=.01)
        beam(f'{mid}_rake2', (-hx + .25, .3, .3), (jx[0], -.4, jz - .2), .14, .14, 'beam', 'Main', bev=.01)
    # railing: posts ~1 m apart, top + mid rails, square balusters
    zr0 = zd; zr1 = zd + 1.05
    e_ = .07
    runs = [('F', (-hx + e_, -hy + e_), (hx - e_, -hy + e_))]
    runs.append(('R', (hx - e_, -hy + e_), (hx - e_, hy - .1)))
    if not corner: runs.append(('L', (-hx + e_, -hy + e_), (-hx + e_, hy - .1)))
    for nm, a, b in runs:
        a = Vector((a[0], a[1], 0)); b = Vector((b[0], b[1], 0)); L = (b - a).length; n = max(2, round(L / 1.0)); d = (b - a) / L
        for k in range(n + 1):
            if nm != 'F' and k == 0: continue   # the corner post belongs to the front run
            p = a + d * (L * k / n)
            box(f'{mid}_rpost{nm}{k}', (.1, .1, zr1 + .08 - jz), (p.x, p.y, (jz + zr1 + .08) / 2), 'beam', 'Main', bev=.01, axis=(0, 0, 1))
            lathe(f'{mid}_rcap{nm}{k}', [(.04, zr1 + .079), (.065, zr1 + .095), (.06, zr1 + .13), (.03, zr1 + .15)], 'bronze', 'Main', seg=12, center=(p.x, p.y, 0))
        sm = 0 if nm == 'F' else .008
        for zz, hh, ww in ((zr1, .07, .09), (zd + .45, .05, .06), (zd + .08, .05, .07)):
            beam(f'{mid}_rail{nm}{zz:.2f}', a + Vector((0, 0, zz)), b + Vector((0, 0, zz)), ww - sm, hh - sm, 'beam', 'Main', bev=.008)
        for k, t in enumerate(np.arange(.09, L - .05, .14)):
            p = a + d * t
            if any(abs(t - L * j / n) < .08 for j in range(n + 1)): continue
            box(f'{mid}_bal{nm}{k}', (.028, .028, zr1 - zd - .12), (p.x, p.y, (zd + .1 + zr1 - .02) / 2), 'beam', 'Main', bev=.004, axis=(0, 0, 1))
    cols = [('box', (0, 0, jz - .1), (W, D, .32))]
    cols += [('box', (0, -hy + .06, zd + .55), (W, .12, 1.1)), ('box', (hx - .06, 0, zd + .55), (.12, D, 1.1))]
    if not corner: cols.append(('box', (-hx + .06, 0, zd + .55), (.12, D, 1.1)))
    return {'collision': cols, 'deckTop_m': zd, 'wallSide': ['+Y', '-X'] if corner else ['+Y'], 'railing_m': 1.05}

def CP01(): return CP('CP01', 5501)
def CP02(): return CP('CP02', 5502, corner=True)

# ------------------------------------------------------------------ DT street details
def tile_cap(name, half_w, z0, z1, eave_lift=.05, at=(0, 0)):
    """small square hipped tile roof (lantern / post caps): a 4-sided lathe turned 45 degrees, concave sides, lifted corners"""
    r0 = half_w * math.sqrt(2)
    prof = [(.004, z1)] + [(r0 * t, z1 - (z1 - z0) * t ** .7 + eave_lift * t ** 6) for t in np.linspace(.08, 1, 8)] + [(r0 * .97, z0 - .02 + eave_lift), (r0 * .7, z0 - .015)]
    o = lathe(name, prof[::-1], 'tile', 'Main', seg=4); rotz(o, math.pi / 4)
    rr = max(.008, half_w * .07)
    for k in range(4):   # hip ridge tiles down the four corners, ending in a small upturn
        pts = [(r * math.cos(math.pi / 4 + k * math.pi / 2), r * math.sin(math.pi / 4 + k * math.pi / 2), z + rr * .5) for r, z in prof if r > .01][:-2]
        pts = [Vector((p[0] * .985, p[1] * .985, p[2])) for p in pts]
        tube(f'{name}_hip{k}', pts, rr, 'tile', 'Main', sides=6)
    if at != (0, 0):
        for p_ in [o] + parts[-4:]: p_.data.transform(Matrix.Translation((at[0], at[1], 0)))
    return o

def DT01():
    """street lantern 0.6 x 0.6 x 2.5 m: stepped granite base with a cloud relief, cedar post with bronze bands and small
    knee braces, a lantern box of four blank paper panels (Glow) behind lattice, a small hipped tile cap and a bronze finial."""
    rg = random.Random(5601)
    o = box('DT01_plinth', (.6, .6, .12), (0, 0, .06), 'granite_top', 'Main', bev=0, cuts=1); chisel(o, .006, 4, 8001); bevel(o, .02, 2, 30)
    o = box('DT01_pedestal', (.46, .46, .56), (0, 0, .12 + .28 - .002), 'granite', 'Main', bev=0, cuts=1); chisel(o, .008, 3, 8002); bevel(o, .022, 2, 30)
    o = box('DT01_cap', (.52, .52, .07), (0, 0, .675), 'granite_top', 'Main', bev=0); bevel(o, .015, 2, 30)
    for k in range(4):   # cloud relief on each face of the pedestal
        pts = [(.13 * math.cos(a) * (1 + .25 * math.cos(3 * a)), .40 + .09 * math.sin(a) * (1 + .3 * math.sin(2 * a))) for a in np.linspace(0, math.tau, 18, endpoint=False)]
        r = prism_xz(f'DT01_cloud{k}', pts, .014, -.23 - .01, 'granite_moss', 'Main', bev=.004); rotz(r, k * math.pi / 2)
    box('DT01_post', (.13, .13, 1.58 - .70), (0, 0, (.70 + 1.58) / 2), 'beam', 'Main', bev=.012, axis=(0, 0, 1))
    for zz in (.80, 1.42): box(f'DT01_band{zz}', (.145, .145, .04), (0, 0, zz), 'bronze', 'Main', bev=.004)
    for k in range(4):
        b = beam(f'DT01_knee{k}', (.06, 0, 1.36), (.2, 0, 1.56), .05, .05, 'beam', 'Main', bev=.006); rotz(b, k * math.pi / 2)
    zb, zt = 1.58, 2.12; h = .23
    box('DT01_floor', (2 * h + .04, 2 * h + .04, .05), (0, 0, zb + .025), 'beam', 'Main', bev=.008)
    box('DT01_top', (2 * h + .04, 2 * h + .04, .05), (0, 0, zt - .025), 'beam', 'Main', bev=.008)
    for i, (x, y) in enumerate(((-h, -h), (h, -h), (h, h), (-h, h))):
        box(f'DT01_col{i}', (.045, .045, zt - zb - .1), (x, y, (zb + zt) / 2), 'beam', 'Main', bev=.006, axis=(0, 0, 1))
    for k in range(4):
        n0 = len(parts)
        box(f'Glow_panel{k}', (2 * h - .03, .008, zt - zb - .12), (0, -h + .012, (zb + zt) / 2), 'paper', 'Glow', bev=0)
        parts[-1].data.materials.clear(); parts[-1].data.materials.append(MAT[1])
        for j, xx in enumerate(np.linspace(-h + .03, h - .03, 5)[1:-1]):
            box(f'DT01_lv{k}{j}', (.014, .016, zt - zb - .11), (xx, -h - .002, (zb + zt) / 2), 'beam', 'Main', bev=.002, axis=(0, 0, 1))
        for j, zz in enumerate(np.linspace(zb + .06, zt - .06, 5)[1:-1]):
            box(f'DT01_lh{k}{j}', (2 * h - .05, .014, .014), (0, -h - .004, zz), 'beam', 'Main', bev=.002, axis=(1, 0, 0))
        for o in parts[n0:]: rotz(o, k * math.pi / 2)
    tile_cap('DT01_roof', .29, zt - .005, 2.40)
    lathe('DT01_finial', [(.004, 2.5), (.03, 2.47), (.035, 2.44), (.02, 2.42), (.045, 2.395), (.004, 2.37)][::-1], 'bronze', 'Main', seg=12)
    return {'collision': [('box', (0, 0, .35), (.6, .6, .7)), ('box', (0, 0, 1.6), (.16, .16, 1.8))], 'glow': 'four paper panels'}

def DT02():
    """blank cloth shop pennant on a timber arm, 1.0 x 0.2 x 1.8 m, for a post or wall at -X: back plate, arm with a carved end
    and bronze cap, knee brace, rod on two cords, swallow-tailed blank cloth (no writing) with two tassels."""
    rg = random.Random(5602); x0, x1 = -.48, .48
    box('DT02_plate', (.05, .14, .62), (x0 + .025, 0, 1.38), 'beam', 'Main', bev=.008, axis=(0, 0, 1))
    for zz in (1.16, 1.6): lathe(f'DT02_nail{zz}', [(.002, 0), (.014, 0), (.012, .008), (.002, .01)], 'bronze', 'Main', seg=8); nl = parts[-1]; nl.data.transform(Matrix.Translation((x0 + .05, 0, zz)) @ Vector((1, 0, 0)).to_track_quat('Z', 'Y').to_matrix().to_4x4())
    beam('DT02_arm', (x0 + .03, 0, 1.64), (x1 - .07, 0, 1.64), .07, .09, 'beam', 'Main', bev=.01)
    prism_xz('DT02_armend', [(x1 - .09, 1.595), (x1 - .02, 1.60), (x1, 1.63), (x1 - .01, 1.67), (x1 - .05, 1.69), (x1 - .09, 1.685)], .066, -.033, 'beam', 'Main', bev=.004)
    beam('DT02_knee', (x0 + .04, 0, 1.2), (x0 + .36, 0, 1.6), .055, .055, 'beam', 'Main', bev=.007)
    zr = 1.50
    tube('DT02_rod', [(-.28, 0, zr), (.42, 0, zr)], .014, 'beam', 'Main', sides=8)
    for xx in (-.22, .36): tube(f'DT02_cord{xx}', [(xx, 0, zr), (xx, 0, 1.6)], .006, 'cloth', 'Main', sides=5)
    bm = bmesh.new(); W, nx, nz = .58, 10, 14; xl = -.22 + .02; ztop = zr - .015; zbot = .22; vs = []
    for j in range(nz + 1):
        row = []
        for i in range(nx + 1):
            u = i / nx; v = j / nz; tail = .16 * (1 - abs(u - .5) * 2)   # swallow tail: the middle rises
            z = ztop - v * (ztop - zbot - tail * v ** 3); y = .02 * math.sin(u * math.pi * 2 + v * 2) * v
            row.append(bm.verts.new((xl + u * W, y, z)))
        vs.append(row)
    for j in range(nz):
        for i in range(nx): bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
    o = finish('DT02_cloth', bm, 'cloth', 'Main', axis=(1, 0, 0)); m = o.modifiers.new('t', 'SOLIDIFY'); m.thickness = .006; apply(o, m); reuv(o, 'cloth', (1, 0, 0))
    for uu in (.017, .983):
        xx = xl + uu * W; yy = .02 * math.sin(uu * math.pi * 2 + 2)
        tube(f'DT02_tassel{xx:.2f}', [(xx, yy, zbot + .012), (xx, yy, zbot - .215)], .012, 'cloth', 'Main', sides=6, radii=[.006, .016])
    return {'collision': [], 'mount': 'back plate on a post or wall at -X, arm along +X', 'noWriting': True}

def DT03():
    """small hanging lantern 0.4 x 0.4 x 0.7 m (origin under the tassel; hang it by the ring): bronze ring and stem, a small
    hipped tile cap, a timber frame with lattice and blank lit paper (Glow, no writing), a carved base, a jade bead and a tassel."""
    zt0, zt1 = .28, .52; h = .12
    tube('DT03_tassel', [(0, 0, .0), (0, 0, .13)], .02, 'cloth', 'Main', sides=8, radii=[.024, .006])
    lathe('DT03_bead', [(.004, .125), (.018, .13), (.024, .145), (.018, .16), (.004, .165)], 'bronze', 'Main', seg=12)
    tube('DT03_cord', [(0, 0, .16), (0, 0, .225)], .005, 'cloth', 'Main', sides=5)
    lathe('DT03_base', [(.004, .22), (.07, .225), (.12, .245), (.15, .27), (.15, .285), (.004, .285)], 'beam', 'Main', seg=4); rotz(parts[-1], math.pi / 4)
    for i, (x, y) in enumerate(((-h, -h), (h, -h), (h, h), (-h, h))):
        box(f'DT03_col{i}', (.026, .026, zt1 - zt0 + .02), (x, y, (zt0 + zt1) / 2), 'beam', 'Main', bev=.004, axis=(0, 0, 1))
    box('DT03_rimT', (2 * h + .03, 2 * h + .03, .025), (0, 0, zt1 + .005), 'beam', 'Main', bev=.004)
    for k in range(4):
        n0 = len(parts)
        box(f'Glow_lpanel{k}', (2 * h - .02, .006, zt1 - zt0 - .01), (0, -h + .006, (zt0 + zt1) / 2), 'paper', 'Glow', bev=0)
        parts[-1].data.materials.clear(); parts[-1].data.materials.append(MAT[1])
        box(f'DT03_lv{k}', (.012, .012, zt1 - zt0 - .01), (0, -h - .002, (zt0 + zt1) / 2), 'beam', 'Main', bev=.002, axis=(0, 0, 1))
        for j, zz in enumerate((zt0 + .07, zt1 - .07)): box(f'DT03_lh{k}{j}', (2 * h - .02, .012, .012), (0, -h - .0045, zz), 'beam', 'Main', bev=.002, axis=(1, 0, 0))
        for o in parts[n0:]: rotz(o, k * math.pi / 2)
    tile_cap('DT03_roof', .195, zt1 + .012, .62, eave_lift=.03)
    lathe('DT03_stem', [(.004, .61), (.02, .615), (.016, .64), (.004, .645)], 'bronze', 'Main', seg=10)
    rg_ = [(math.cos(a) * .035, 0, .666 + math.sin(a) * .025) for a in np.linspace(-math.pi / 2, 3 * math.pi / 2, 17)]
    tube('DT03_ring', rg_, .006, 'bronze', 'Main', sides=6, caps=False)
    return {'collision': [], 'hang': 'ring at the top, origin at the bottom of the tassel', 'noWriting': True}

def DT04():
    """bamboo drying pole 2.5 x 0.4 x 1.3 m: two cedar posts on granite foot blocks with bronze bands, small tile caps, knee
    braces, a worn bamboo pole (nodes as rings) lashed into the post forks with rope."""
    rg = random.Random(5604); xs = (-1.1, 1.1); zp = 1.12
    for i, x in enumerate(xs):
        o = box(f'DT04_foot{i}', (.3, .3, .16), (x, 0, .08), 'granite_moss', 'Main', bev=0, cuts=1); chisel(o, .008, 4, 8400 + i); bevel(o, .02, 2, 30)
        box(f'DT04_post{i}', (.11, .11, 1.18 - .155), (x, 0, (.155 + 1.18) / 2), 'beam', 'Main', bev=.01, axis=(0, 0, 1))
        box(f'DT04_band{i}', (.122, .122, .035), (x, 0, .24), 'bronze', 'Main', bev=.003)
        tile_cap(f'DT04_cap{i}', .12, 1.175, 1.3, eave_lift=.02, at=(x, 0))
        sgn = 1 if x < 0 else -1
        beam(f'DT04_knee{i}', (x + sgn * .05, 0, .82), (x + sgn * .3, 0, zp - .035), .045, .045, 'beam', 'Main', bev=.005)
        for j in range(3):   # rope lashing where the pole crosses the post
            ang = np.linspace(0, math.tau, 13)
            tube(f'DT04_rope{i}{j}', [(x + .068 * math.cos(a), .068 * math.sin(a), zp - .03 + j * .025) for a in ang], .007, 'cloth', 'Main', sides=5, caps=False)
    pts = [(x, 0, zp + .012 * math.sin((x + 1.25) / 2.5 * math.pi)) for x in np.linspace(-1.24, 1.24, 25)]
    tube('DT04_pole', pts, .03, 'oldwood', 'Main', sides=10)
    for k, x in enumerate(np.arange(-1.0, 1.05, .34)):
        zz = zp + .012 * math.sin((x + 1.25) / 2.5 * math.pi)
        lathe(f'DT04_node{k}', [(.029, -.008), (.034, -.003), (.034, .003), (.029, .008)], 'oldwood', 'Main', seg=10); o = parts[-1]
        o.data.transform(Matrix.Translation((x, 0, zz)) @ Matrix.Rotation(math.pi / 2, 4, 'Y'))
    return {'collision': [('box', (x, 0, .65), (.3, .3, 1.3)) for x in xs] + [('box', (0, 0, zp), (2.5, .08, .08))]}

def DT05():
    """narrow granite step-edge cap 4.0 x 0.36 x 0.2 m: four or five cap stones of different lengths, the street nose rounded
    by feet (more in the middle of each stone and of the run), a slight dish worn into the top, a drip groove under the nose."""
    rg = random.Random(5605); W, D, H = 4.0, .36, .2; xs = [-W / 2]
    while W / 2 - xs[-1] > 1.25: xs.append(xs[-1] + rg.uniform(.7, 1.15))
    xs.append(W / 2)
    for k, (a, b) in enumerate(zip(xs, xs[1:])):
        mid_ = abs((a + b) / 2) < 1.1; g = .006
        o = box(f'DT05_cap{k}', (b - a - 2 * g, D, H - .004), ((a + b) / 2, 0, (H - .004) / 2 + .002), 'granite_top', 'Main', bev=0, cuts=2)
        chisel(o, .016 if mid_ else .01, 2.6, seed=8500 + k); bevel(o, .045 if mid_ else .03, 3, 30)
        box(f'DT05_bed{k}', (b - a - 2 * g - .04, D - .1, .006), ((a + b) / 2, .03, .003), 'granite_moss', 'Main', bev=0)
    return {'collision': [('box', (0, 0, H / 2), (W, D, H))], 'walkTop': H}

def DT06():
    """veranda corner brace 0.7 x 0.12 x 0.9 m for a post-to-beam corner: a post stub and a beam stub joined by a through
    tenon with pegs, a carved scroll bracket (雀替) filling the corner, bronze L-plates with nail heads on both faces."""
    rg = random.Random(5606); W, T, H = .7, .12, .9; x0 = -W / 2; xp = x0 + .07; zb = H - .07
    box('DT06_post', (.13, T, H), (xp, 0, H / 2), 'beam', 'Main', bev=.01, axis=(0, 0, 1))
    box('DT06_beam', (W - .07, T - .01, .13), (x0 + .07 + (W - .07) / 2, 0, zb), 'beam', 'Main', bev=.01, axis=(1, 0, 0))
    box('DT06_tenon', (.05, T - .04, .08), (x0 + .027, 0, zb), 'oldwood', 'Main', bev=.006)
    for k, zz in enumerate((zb - .03, zb + .03)):
        lathe(f'DT06_peg{k}', [(.004, -T / 2 - .006), (.012, -T / 2 - .006), (.012, T / 2 + .006), (.004, T / 2 + .006)], 'oldwood', 'Main', seg=8)
        parts[-1].data.transform(Matrix.Translation((xp, 0, zz)) @ Matrix.Rotation(math.pi / 2, 4, 'X'))
    prof = []
    for i in range(15):
        t = i / 14; prof.append((xp + .065 + .52 * t, zb - .065 - .52 * (1 - t) ** 1.6 - .035 * math.sin(t * math.pi * 3)))
    poly = [(xp + .06, zb - .062), (xp + .06 + .53, zb - .062)] + prof[::-1][1:] + [(xp + .06, zb - .6)]
    prism_xz('DT06_bracket', poly, T - .03, -(T - .03) / 2, 'beam', 'Main', bev=.004)
    for k in range(3):   # carved scroll holes read as dark insets on both faces
        cx, cz = xp + .16 + k * .12, zb - .2 + k * .05; r = .035 - k * .006
        pts = [(cx + r * math.cos(a), cz + r * .8 * math.sin(a)) for a in np.linspace(0, math.tau, 12, endpoint=False)]
        prism_xz(f'DT06_cut{k}', pts, T - .024, -(T - .024) / 2, 'dark', 'Main', bev=0)
    for sy in (-1, 1):
        y = sy * (T / 2 + .004)
        for nm, size, c in (('v', (.1, .008, .22), (xp, y, zb - .14)), ('h', (.22, .008, .1), (xp + .12, y + sy * .002, zb))):
            box(f'DT06_plate{nm}{sy:+d}', size, c, 'bronze', 'Main', bev=.002)
        for k, (xx, zz) in enumerate(((xp, zb - .2), (xp, zb - .1), (xp + .1, zb), (xp + .2, zb))):
            lathe(f'DT06_nail{sy:+d}{k}', [(.002, 0), (.01, 0), (.008, .006), (.002, .007)], 'bronze', 'Main', seg=8)
            parts[-1].data.transform(Matrix.Translation((xx, y + sy * .004, zz)) @ Vector((0, sy, 0)).to_track_quat('Z', 'Y').to_matrix().to_4x4())
    return {'collision': [], 'mount': 'post stub on the -X side, beam stub along +X at the top'}

# ------------------------------------------------------------------ LOD, export, info
def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True); parts.clear(); MAT.clear()

def join(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]; bpy.ops.object.join(); o = bpy.context.object; o.name = name; o.data.name = name; return o

def tris(o): return sum(len(p.vertices) - 2 for p in o.data.polygons)

def build(mid):
    clear(); load_trim(); meta = globals()[mid]() or {}
    lim = LIMITS[mid]; bad = []
    for o in parts:
        cs = np.array([v.co[:] for v in o.data.vertices])
        if len(cs) and (np.abs(cs[:, 0]).max() > lim[0] / 2 + .003 or np.abs(cs[:, 1]).max() > lim[1] / 2 + .003 or cs[:, 2].max() > lim[2] + .003):
            bad.append((o.name, np.round(cs.min(0), 3).tolist(), np.round(cs.max(0), 3).tolist()))
    for b in bad[:20]: print('OVER', *b, flush=True)
    groups = {}
    for o in parts: groups.setdefault(o['grp'], []).append(o)
    lod0 = {}
    for g, objs in groups.items():
        nm = f'MC01_{mid}' if g == 'Main' else g
        o = join(objs, f'{nm}_LOD0'); bpy.ops.object.select_all(action='DESELECT')
        lod0[g] = o
    # LOD1 / LOD2 budgets shared by sqrt(group tris), LOD1 <= 50 % & 100k, LOD2 <= 15 % & 25k
    T = {g: tris(o) for g, o in lod0.items()}; tot = sum(T.values())
    out = {}
    for lv, frac, cap in ((1, .5, 100_000), (2, .15, 25_000)):
        budget = min(tot * frac, cap); w = {g: math.sqrt(t) for g, t in T.items()}; tw = sum(w.values())
        for g, o in lod0.items():
            tgt = max(min(T[g] * .5 if lv == 1 else T[g] * .15, budget * w[g] / tw), 12)
            c = o.copy(); c.data = o.data.copy(); c.name = o.name.replace('_LOD0', f'_LOD{lv}'); bpy.context.scene.collection.objects.link(c)
            m = c.modifiers.new('d', 'DECIMATE'); m.ratio = min(1.0, tgt / max(T[g], 1)); m.use_collapse_triangulate = True; apply(c, m)
            out.setdefault(lv, {})[g] = c
    # collision boxes
    cols = []
    for i, (kind, c, s) in enumerate(meta.get('collision', [])):
        bm = box_bm(s, c); me = bpy.data.meshes.new(f'MC01_{mid}_Collision{i}'); bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new(me.name, me); bpy.context.scene.collection.objects.link(o); cols.append(o)
    col = join(cols, f'MC01_{mid}_Collision') if cols else None
    # dims check against the package limit (main + details)
    mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
    for o in lod0.values():
        for v in o.data.vertices: mn = Vector(map(min, mn, v.co)); mx = Vector(map(max, mx, v.co))
    dims = mx - mn; lim = LIMITS[mid]
    assert all(dims[i] <= lim[i] + .005 for i in range(3)), f'{mid} over limit {tuple(round(d, 3) for d in dims)} > {lim}'
    assert mn.z > -.005, f'{mid} bottom below 0: {mn.z}'
    blend = HERE / f'MC01_{mid}.blend'; bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.object.select_all(action='SELECT')
    fbx = OUT / f'MC01_{mid}.fbx'
    bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True, object_types={'MESH', 'EMPTY'}, global_scale=1.0, apply_unit_scale=True,
                             apply_scale_options='FBX_SCALE_ALL', bake_space_transform=True, axis_forward='-Z', axis_up='Y', use_mesh_modifiers=True,
                             mesh_smooth_type='FACE', use_tspace=False, add_leaf_bones=False, bake_anim=False, path_mode='STRIP', embed_textures=False)
    lods = []
    for lv, d in ((0, lod0), (1, out[1]), (2, out[2])):
        lods.append({'lod': lv, 'triangles': sum(tris(o) for o in d.values()), 'objects': len(d), 'materials': len({m.name for o in d.values() for m in o.data.materials})})
    info = {'id': f'MC01-{mid}', 'package': 'docs/execution/2026-11-05/A-48h-mountain-city-architecture.md', 'author': 'A (Johnnnny0823)',
            'version': 'v001', 'status': 'Exported; Imported/Visually Verified/In-game Verified: 未驗',
            'dimensions_m': [round(d, 3) for d in dims], 'limit_m': list(lim), 'grid_m': GRID, 'origin': 'footprint centre, bottom z = 0, -Y = street front',
            'minTier': TIER[mid], 'lods': lods,
            'objectsLOD0': [o.name for o in lod0.values()], 'detailObjects': [g for g in lod0 if g.startswith('Detail_')],
            'glowObjects': [g for g in lod0 if g == 'Glow'],
            'materials': ['M_MountainStreet_Trim', 'M_MountainStreet_Glow'] if 'Glow' in lod0 else ['M_MountainStreet_Trim'],
            'textures': {n: '2048x2048' for n in ('T_MountainStreet_Albedo', 'T_MountainStreet_Normal', 'T_MountainStreet_MetallicSmoothness', 'T_MountainStreet_Emission')},
            'textureNote': 'one trim sheet shared by every MC01 module (D3 §4); 256 px/m', 'collision': f'MC01_{mid}_Collision ({len(cols)} boxes)',
            'extra': {k: v for k, v in meta.items() if k != 'collision'}, 'fbx': f'art/exports/{PKG}/MC01_{mid}.fbx',
            'fps': '不寫（手機未實測）'}
    (OUT / f'MC01_{mid}.model_info.json').write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding='utf-8')
    print(mid, 'LOD tris', [l['triangles'] for l in lods], 'objects', [l['objects'] for l in lods], 'dims', info['dimensions_m'], flush=True)

if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for a in args:
        if a == 'trim': clear(); make_trim(); print('trim sheet saved', flush=True)
        else: build(a)
