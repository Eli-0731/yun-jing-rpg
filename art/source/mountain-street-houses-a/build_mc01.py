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
LIMITS = {'SB01': (4, 4, 2), 'SF01': (4, 4, 3), 'RF01': (5.8, 5.8, 2.6)}   # RF: 4 m bay + 0.7 m eave overhang + ridge ornaments
TIER = {'SB01': 'low', 'SF01': 'low', 'RF01': 'low'}
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
    return S

# strip name -> (source, height px). Rows stack bottom-up from V = 0. 256 px per metre everywhere.
STRIPS = [('granite', 256), ('granite_moss', 256), ('granite_top', 128), ('plank', 256), ('beam', 256), ('oldwood', 128),
          ('plaster', 256), ('tile', 128), ('tile_moss', 128), ('bronze', 64), ('cloth', 64), ('paper', 64), ('dark', 64)]
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
    for f, k in zip(bm.faces, face_k):
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
def lathe(name, profile, strip, grp, seg=32, center=(0, 0, 0), glow=False):
    bm = bmesh.new(); rings = []
    for r, z in profile: rings.append([bm.verts.new((r * math.cos(math.tau * i / seg), r * math.sin(math.tau * i / seg), z)) for i in range(seg)])
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
    if bev: bevel(o, bev, 1, 30)
    return o
def rotz(o, ang, pivot=(0, 0, 0)):
    p = Vector(pivot); o.data.transform(Matrix.Translation(p) @ Matrix.Rotation(ang, 4, 'Z') @ Matrix.Translation(-p))

# ------------------------------------------------------------------ SB01 straight foundation bay
def SB01():
    """coursed granite ashlar shell, 4 x 4 x 2 m: projecting plinth course, staggered courses with quoins that alternate per
    course, dressed (chiselled) faces, recessed mortar joints over a dark mortar core, worn coping slabs as the walkable top."""
    rg = random.Random(5101); H = 2.0; half = GRID / 2; depth = .32; gap = .024
    box('SB01_core', (GRID - 2 * depth + .06, GRID - 2 * depth + .06, H - .14), (0, 0, (H - .14) / 2), 'dark', 'Main', bev=0)
    # mortar backing just behind the block faces (shows in the joints): granite_moss, slightly recessed
    for side in range(4):
        L = GRID - .24; o = box(f'SB01_mortar{side}', (L, .02, H - .16), (0, -half + .075, (H - .16) / 2 + .01), 'dark', 'Main', bev=0)
        rotz(o, side * math.pi / 2)
    # course heights: plinth .30, then 4 courses up to the coping (1.86)
    hs = [.30]; rest = 1.86 - .30; n = 4; raw = [rg.uniform(.82, 1.18) for _ in range(n)]; hs += [rest * r / sum(raw) for r in raw]
    z = 0
    for ci, ch in enumerate(hs):
        plinth = ci == 0; inset = 0 if plinth else .035   # plinth flush with the grid, upper courses set back 3.5 cm
        for side in range(4):
            # quoin rule: on even courses the front/back faces run to the corners, on odd courses the side faces do
            runs_full = (side % 2 == 0) == (ci % 2 == 0)
            x0, x1 = (-half + inset, half - inset) if runs_full else (-half + depth, half - depth)
            x = x0; k = 0
            while x < x1 - 1e-3:
                L = rg.uniform(.48, 1.05) if not plinth else rg.uniform(.7, 1.3)
                if x1 - (x + L) < .32: L = x1 - x
                cx = x + L / 2; strip = 'granite_moss' if ci == 0 or side == 2 else ('granite_top' if rg.random() < .22 else 'granite')
                d_ = depth - inset
                o = box(f'SB01_c{ci}s{side}_{k}', (L - gap, d_, ch - gap), (cx, -half + inset + d_ / 2, z + ch / 2), strip, 'Main',
                        bev=0, cuts=3)
                chisel(o, .010 if not plinth else .007, 3.2, seed=ci * 100 + side * 10 + k)
                bevel(o, .022 if not plinth else .03, 2, 30)
                rotz(o, side * math.pi / 2); x += L; k += 1
        z += ch
    # coping slabs (walkable top, 1.86 → 2.0): a grid of worn slabs, overhanging the face by 2 cm, top kept flat for walking
    zc = 1.86 - gap / 2; th = H - zc; xs = [-half]
    while xs[-1] < half - .2: xs.append(min(half, xs[-1] + rg.uniform(.8, 1.15)))
    xs[-1] = half
    for i in range(len(xs) - 1):
        ys = [-half]
        while ys[-1] < half - .2: ys.append(min(half, ys[-1] + rg.uniform(.6, 1.0)))
        ys[-1] = half
        for j in range(len(ys) - 1):
            o = box(f'SB01_cope{i}_{j}', (xs[i + 1] - xs[i] - gap, ys[j + 1] - ys[j] - gap, th), ((xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2, zc + th / 2),
                    'granite_top', 'Main', bev=0, cuts=2)
            chisel(o, .004, 2.5, seed=900 + i * 10 + j); bevel(o, .02, 2, 30)
    return {'collision': [('box', (0, 0, H / 2), (GRID, GRID, H))], 'walkTop': H}

def moss_tuft(name, rg):
    bm = bmesh.new()
    for i in range(rg.randint(5, 8)):
        a = rg.uniform(0, math.tau); L = rg.uniform(.05, .11); w = rg.uniform(.012, .02); d = Vector((math.cos(a) * .6, math.sin(a) * .25, 1)).normalized()
        s = Vector((-math.sin(a), math.cos(a), 0)) * w; b = Vector((rg.uniform(-.04, .04), rg.uniform(-.01, .01), 0))
        v = [bm.verts.new(b - s), bm.verts.new(b + s), bm.verts.new(b + d * L)]; bm.faces.new(v)
    return finish(name, bm, 'granite_moss', 'Detail_Moss')

# ------------------------------------------------------------------ SF01 open shopfront bay
def SF01():
    """4 x 4 x 3 m: front 3 m open veranda (stall space), rear 1 m closed plank room with a dark doorway (no interior).
    Round cedar posts on granite bases with bronze foot bands, carved brackets (雀替) under the front lintel, plank walls with
    rails and a patch board, a double lintel + top plate at 3.0 m for the roof bay, blank indigo noren, two paper lanterns."""
    rg = random.Random(5201); half = GRID / 2; H = 3.0; pr = .12; zb = .30
    front_y = -half + .2; enc_y = 1.0; back_y = half - .2; px = half - .2
    posts = [(-px, front_y), (px, front_y), (-px, enc_y), (px, enc_y), (-px, back_y), (px, back_y)]
    for i, (x, y) in enumerate(posts):
        o = box(f'SF01_base{i}', (.40, .40, zb), (x, y, zb / 2), 'granite', 'Main', bev=0, cuts=2); chisel(o, .006, 4, 300 + i); bevel(o, .03, 2, 30)
        lathe(f'SF01_post{i}', [(pr * 1.04, zb - .01)] + [(pr * (1 - .07 * t) + .003 * math.sin(t * 40 + i), zb + .1 + t * (H - .4 - zb - .1)) for t in np.linspace(0, 1, 14)], 'beam', 'Main', seg=32, center=(x, y, 0))
        lathe(f'SF01_band{i}', [(pr + .012, zb - .005), (pr + .014, zb + .015), (pr + .014, zb + .085), (pr + .01, zb + .10)], 'bronze', 'Main', seg=20, center=(x, y, 0))
        lathe(f'SF01_cap{i}', [(pr + .008, H - .48), (pr + .012, H - .46), (pr + .012, H - .40), (pr + .006, H - .38)], 'bronze', 'Main', seg=20, center=(x, y, 0))
    # lintels: 額枋 (.22 h) + top plate 平板枋 (.12 h) around the bay; the roof bay sits on z = 3.0
    zl0, zl1 = H - .40, H - .14
    for nm, a, b in (('front', (-half + .06, front_y, 0), (half - .06, front_y, 0)), ('enc', (-half + .06, enc_y, 0), (half - .06, enc_y, 0)),
                     ('back', (-half + .06, back_y, 0), (half - .06, back_y, 0)),
                     ('left', (-px, -half + .06, 0), (-px, half - .06, 0)), ('right', (px, -half + .06, 0), (px, half - .06, 0))):
        a = Vector(a); b = Vector(b)
        sd = .012 if nm in ('left', 'right') else 0   # side members a hair smaller: no shared faces where beams cross
        beam(f'SF01_lintel_{nm}', a + Vector((0, 0, (zl0 + zl1) / 2)), b + Vector((0, 0, (zl0 + zl1) / 2)), .16 - sd, zl1 - zl0 - sd, 'beam', 'Main', bev=.012)
        beam(f'SF01_plate_{nm}', a + Vector((0, 0, H - .07 - sd / 2)), b + Vector((0, 0, H - .07 - sd / 2)), .22 - sd, .14 - sd, 'beam', 'Main', bev=.012)
    # lintel joint plates (bronze) at the front posts
    for x in (-px, px):
        for s in (-1, 1):
            if s * x > 0: continue   # plates only on the inner side of each post (outer side would pass the grid)
            box(f'SF01_plate_br{x:+.1f}{s}', (.16, .012, .2), (x + s * .2, front_y - .085, (zl0 + zl1) / 2), 'bronze', 'Main', bev=.003)
    # carved brackets 雀替 under the front lintel: scroll profile in XZ, both sides of each front post
    prof = []
    for i in range(13):
        t = i / 12; prof.append((.12 + .86 * t, zl0 - .46 * (1 - t) ** 1.5 - .03 * math.sin(t * math.pi * 3)))
    prof = [(.12, zl0), (.98, zl0)] + prof[::-1][1:]   # top edge under the lintel, then the scroll back to the post
    for x, sgn in ((-px, 1), (px, -1)):
        poly = [(x + sgn * dx, z) for dx, z in prof] if sgn > 0 else [(x + sgn * dx, z) for dx, z in reversed(prof)]
        prism_xz(f'SF01_bracket_in{x:+.1f}', poly, .12, front_y - .06, 'beam', 'Main', bev=0)
    # rear room: plank walls (back, two sides, front-of-room with a dark doorway), rails, patch board, dark room box
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
            if axis == 'x': o = box(f'SF01_{tag}{k}', (w - .006, .045, z1 - lo), (cx, y, (lo + z1) / 2), 'plank' if rg.random() > .12 else 'oldwood', 'Main', bev=.006, axis=(0, 0, 1))
            else: o = box(f'SF01_{tag}{k}', (.045, w - .006, z1 - lo), (y, cx, (lo + z1) / 2), 'plank' if rg.random() > .12 else 'oldwood', 'Main', bev=.006, axis=(0, 0, 1))
            for zr_ in (.42, 1.45):   # nail heads where the board crosses a rail
                if lo < zr_ < z1:
                    off = .0225 + .05; pos = (cx, y - off if y < 1.5 else y + off, zr_) if axis == 'x' else ((y - off if y < 0 else y + off), cx, zr_)
                    lathe(f'SF01_nail_{tag}{k}_{zr_}', [(.002, 0), (.012, 0), (.010, .006), (.002, .008)], 'bronze', 'Main', seg=8, center=(0, 0, 0))
                    nl = parts[-1]; ax = Vector((0, -1 if y < 1.5 else 1, 0)) if axis == 'x' else Vector((-1 if y < 0 else 1, 0, 0))
                    q = ax.to_track_quat('Z', 'Y').to_matrix().to_4x4(); nl.data.transform(Matrix.Translation(pos) @ q)
            x += w; k += 1
    zw0, zw1 = .03, zl0
    plank_wall('back', -px + pr, px - pr, back_y + .07, zw0, zw1)
    plank_wall('lw', enc_y + pr, back_y - pr, -px - .0, zw0, zw1, axis='y'); plank_wall('rw', enc_y + pr, back_y - pr, px + .0, zw0, zw1, axis='y')
    door = (-.75, .75, 2.25)
    plank_wall('front_room', -px + pr, px - pr, enc_y + .07, zw0, zw1, skip=(-.8, .8, zl1))
    # lattice transom 橫披 over the doorway: frame + grid of square bars, dark room behind
    zt0, zt1 = door[2] + .12, zl0 - .01
    for k, xx in enumerate(np.linspace(-.72, .72, 9)): box(f'SF01_lat_v{k}', (.022, .03, zt1 - zt0), (xx, enc_y + .07, (zt0 + zt1) / 2), 'beam', 'Main', bev=.003, axis=(0, 0, 1))
    for k, zz in enumerate(np.linspace(zt0, zt1, 4)): box(f'SF01_lat_h{k}', (1.40, .026, .022), (0, enc_y + .07, zz), 'beam', 'Main', bev=.003, axis=(1, 0, 0))
    for xx in (-.75, .75): box(f'SF01_lat_post{xx:+.1f}', (.06, .06, zl0 - door[2] - .03), (xx, enc_y + .07, (zl0 + door[2] + .03) / 2), 'beam', 'Main', bev=.006, axis=(0, 0, 1))
    yb = back_y + .07 + .0465; yf = enc_y + .07 - .0465
    for nm, (a, b) in (('back', ((-px, yb), (px, yb))), ('fr', ((-px, yf), (-.8, yf))), ('fr2', ((.8, yf), (px, yf)))):
        for zr in (.42, 1.45):
            beam(f'SF01_rail_{nm}{zr}', (a[0], a[1], zr), (b[0], b[1], zr), .05, .1, 'beam', 'Main', bev=.006)
    for nm, x in (('l', -px - .0465), ('r', px + .0465)):
        for zr in (.42, 1.45): beam(f'SF01_rail_{nm}{zr}', (x, enc_y, zr), (x, back_y, zr), .05, .1, 'beam', 'Main', bev=.006)
    # door frame + head beam, threshold, patch board
    for x in (-.8, .8): beam(f'SF01_jamb{x:+.1f}', (x, enc_y + .02, .03), (x, enc_y + .02, door[2] + .08), .1, .12, 'beam', 'Main', bev=.008)
    beam('SF01_doorhead', (-.88, enc_y + .02, door[2] + .06), (.88, enc_y + .02, door[2] + .06), .14, .12, 'beam', 'Main', bev=.008)
    beam('SF01_threshold', (-.8, enc_y + .02, .07), (.8, enc_y + .02, .07), .14, .1, 'oldwood', 'Main', bev=.01)
    box('SF01_patch', (.34, .02, .22), (1.25, enc_y + .07 - .0315, 1.05), 'oldwood', 'Main', bev=.004)
    box('SF01_patch2', (.02, .26, .18), (-px - .0315, 1.5, .8), 'oldwood', 'Main', bev=.004)
    box('SF01_room', (2 * px - .34, back_y - enc_y - .14, zl0 - .04), (0, (enc_y + back_y) / 2 + .09, (zl0 - .04) / 2 + .01), 'dark', 'Main', bev=0)
    # blank indigo noren on a rod between the front posts (Detail_Cloth); three panels, gentle wave, no writing
    rod_z = zl0 - .05
    tube('Detail_Cloth_rod', [(-1.25, front_y - .02, rod_z), (1.25, front_y - .02, rod_z)], .018, 'beam', 'Detail_Cloth', sides=8)
    for k, x0 in enumerate((-1.2, -.38, .44)):
        bm = bmesh.new(); W, Hc, nx, nz = .76, .62, 10, 8; vs = []
        for j in range(nz + 1):
            row = []
            for i in range(nx + 1):
                u = i / nx; v = j / nz; y = front_y - .03 + .025 * math.sin(u * math.pi * 3 + k) * v
                row.append(bm.verts.new((x0 + u * W, y, rod_z - v * Hc)))
            vs.append(row)
        for j in range(nz):
            for i in range(nx): bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
        o = finish(f'Detail_Cloth_{k}', bm, 'cloth', 'Detail_Cloth', axis=(1, 0, 0))
        m = o.modifiers.new('t', 'SOLIDIFY'); m.thickness = .006; apply(o, m); reuv(o, 'cloth', (1, 0, 0))
    # two paper lanterns hanging inside the front posts (Detail_Lanterns + Glow paper)
    for x in (-px + .38, px - .38):
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
    cols = [('box', (x, y, 1.5), (.3, .3, 3)) for x, y in posts]
    cols += [('box', (0, back_y + .07, 1.4), (2 * px, .12, 2.8)), ('box', (-px, (enc_y + back_y) / 2, 1.4), (.12, back_y - enc_y, 2.8)),
             ('box', (px, (enc_y + back_y) / 2, 1.4), (.12, back_y - enc_y, 2.8)), ('box', (-1.3, enc_y + .07, 1.4), (1.0, .12, 2.8)),
             ('box', (1.3, enc_y + .07, 1.4), (1.0, .12, 2.8)), ('box', (0, enc_y + .07, 2.7), (1.6, .12, .6))]
    return {'collision': cols, 'veranda': [-half, enc_y]}

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
