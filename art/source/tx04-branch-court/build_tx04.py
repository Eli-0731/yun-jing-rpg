"""承天 · 11/05 A 包 TX04 太玄分院模組（Johnnnny0823）。Exports go to art/exports/tx04-branch-court.

Same hand and the same shared 2048 trim sheet as MC01 (art/textures/mountain-street-houses-a, M_MountainStreet_Trim / _Glow),
so the academy batches with the street. The geometry helpers come from the MC01 builder (approved on PR #80).

TX04 additions (D3 §5):
- `M_TX04_Accent`: the sect colour. Its base colour is a parameter (Taixuan lacquer #8E2F25 by default) multiplied over the
  plaster strip of the trim sheet, so wear and streaks stay while another sect only changes one colour. Objects using it are
  merged into the `<ID>_Accent` group; at most 10 % of a building's visible surface (checked and written to model_info).
- `Socket_Plaque` / `Socket_Emblem`: empty objects, no plaque, emblem or text is modelled.
4 m grid; origin at the footprint centre, bottom at z = 0, Blender -Y is the front. LOD0 keeps the modelled detail; LOD1 <= 50 %
(<=100k), LOD2 <= 15 % (<=25k).

    blender -b --factory-startup -P art/source/tx04-branch-court/build_tx04.py -- GATE WALL_ST
"""
import bpy, bmesh, json, math, sys, random
from pathlib import Path
from mathutils import Vector, Matrix
import numpy as np

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'art/source/mountain-street-houses-a'))
import build_mc01 as mc

PKG = 'tx04-branch-court'; OUT = ROOT / 'art/exports' / PKG; PRE = ROOT / 'art/previews' / PKG
for p in (OUT, PRE): p.mkdir(parents=True, exist_ok=True)
ACCENT_DEFAULT = '#8E2F25'
LIMITS = {}; TIER = {}; SOCKETS = []

def accent_material(hexcol=ACCENT_DEFAULT):
    """M_TX04_Accent: trim albedo (UV on the plaster strip) x a colour parameter; trim normal and smoothness kept"""
    trim = mc.MAT[0]; mat = bpy.data.materials.new('M_TX04_Accent'); mat.use_nodes = True; nt = mat.node_tree; bs = nt.nodes['Principled BSDF']
    src = {n.image.name: n.image for n in trim.node_tree.nodes if n.type == 'TEX_IMAGE'}
    def tex(name):
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = next(v for k, v in src.items() if name in k); return t
    rgb = nt.nodes.new('ShaderNodeRGB'); rgb.name = 'AccentColor'; rgb.label = 'Accent colour (sect)'
    c = [int(hexcol[i:i + 2], 16) / 255 for i in (1, 3, 5)]; rgb.outputs[0].default_value = (*[x ** 2.2 for x in c], 1)
    mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1
    a = tex('Albedo'); nt.links.new(a.outputs['Color'], mul.inputs['A']); nt.links.new(rgb.outputs[0], mul.inputs['B'])
    nt.links.new(mul.outputs['Result'], bs.inputs['Base Color'])
    n = tex('Normal'); nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(n.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], bs.inputs['Normal'])
    bs.inputs['Roughness'].default_value = .55
    mat['accentDefault'] = hexcol; mc.MAT['accent'] = mat; return mat

def accent(o):
    """move a finished part onto the accent material/group (its UVs are re-projected onto the plaster strip)"""
    mc.reuv(o, 'plaster'); o.data.materials.clear(); o.data.materials.append(mc.MAT['accent']); o['grp'] = 'Accent'; return o

WALLTEX = ROOT / 'art/textures' / PKG
def wall_material():
    """M_TX04_Wall: the TX04 lime-plaster tile (gen_wall_tex.py, 4 x 4 m per 1024 px), irregular blotches and rain streaks"""
    mat = bpy.data.materials.new('M_TX04_Wall'); mat.use_nodes = True; nt = mat.node_tree; bs = nt.nodes['Principled BSDF']
    a = nt.nodes.new('ShaderNodeTexImage'); a.image = bpy.data.images.load(str(WALLTEX / 'T_TX04_Wall_Albedo.png'))
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(str(WALLTEX / 'T_TX04_Wall_Normal.png')); n.image.colorspace_settings.name = 'Non-Color'
    nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = .6
    nt.links.new(a.outputs['Color'], bs.inputs['Base Color']); nt.links.new(n.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], bs.inputs['Normal'])
    bs.inputs['Roughness'].default_value = .92; mc.MAT['wall'] = mat; return mat

def roof_material():
    """M_TX04_Roof: the trim sheet again, normal strength 0.5 (review #90: the tile faces read like wool up close; the large
    tile rows stay, the fine noise is halved). Only parts whose UVs sit on the tile / tile_moss strips use it."""
    trim = mc.MAT[0]; mat = trim.copy(); mat.name = 'M_TX04_Roof'
    for n in mat.node_tree.nodes:
        if n.type == 'NORMAL_MAP': n.inputs['Strength'].default_value = .5
    mat['normalScale'] = .5; mc.MAT['roof'] = mat; return mat

def roofmat(parts):
    v0 = mc.V0['tile'][0] / mc.SHEET; v1 = (mc.V0['tile_moss'][0] + mc.V0['tile_moss'][1]) / mc.SHEET
    for o in parts:
        if not o.data.materials or o.data.materials[0] != mc.MAT[0] or not o.data.uv_layers: continue
        vs = np.array([l.uv[1] for l in o.data.uv_layers[0].data])
        if len(vs) and vs.min() >= v0 - 1e-4 and vs.max() <= v1 + 1e-4: o.data.materials[0] = mc.MAT['roof']

def wallmat(o, ztop, seed=0):
    """put a plaster part on M_TX04_Wall: side faces U = along the face, V = height with the part's top edge at the tile top
    (streaks hang from under the coping / lintel); a random U offset per part so neighbouring walls never repeat"""
    bm = bmesh.new(); bm.from_mesh(o.data); lay = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
    uoff = random.Random(seed * 131 + len(bm.verts)).random()
    for f in bm.faces:
        nrm = f.normal
        for l in f.loops:
            p = l.vert.co
            if abs(nrm.z) < .7:
                a = Vector((-nrm.y, nrm.x, 0)).normalized(); l[lay].uv = (p.dot(a) / 4 + uoff, 1 - (ztop - p.z) / 4)
            else: l[lay].uv = (p.x / 4 + uoff, p.y / 4)
    bm.to_mesh(o.data); bm.free(); o.data.materials.clear(); o.data.materials.append(mc.MAT['wall']); return o

def socket(name, loc, rot=(0, 0, 0)):
    e = bpy.data.objects.new(name, None); e.empty_display_type = 'ARROWS'; e.empty_display_size = .3
    e.location = loc; e.rotation_euler = rot; bpy.context.scene.collection.objects.link(e); SOCKETS.append(e); return e

def area(o):
    return sum(p.area for p in o.data.polygons)

def build(mid):
    mc.clear(); mc.load_trim(); accent_material(); wall_material(); roof_material(); SOCKETS.clear()
    meta = globals()[mid]() or {}; parts = mc.parts; lim = LIMITS[mid]; tag = f'TX04_{mid}'; roofmat(parts)
    bad = []
    for o in parts:
        cs = np.array([v.co[:] for v in o.data.vertices])
        if len(cs) and (np.abs(cs[:, 0]).max() > lim[0] / 2 + .003 or np.abs(cs[:, 1]).max() > lim[1] / 2 + .003 or cs[:, 2].max() > lim[2] + .003):
            bad.append((o.name, np.round(cs.min(0), 3).tolist(), np.round(cs.max(0), 3).tolist()))
    for b in bad[:20]: print('OVER', *b, flush=True)
    groups = {}
    for o in parts: groups.setdefault(o['grp'], []).append(o)
    lod0 = {}
    for g, objs in groups.items():
        nm = tag if g == 'Main' else (f'{tag}_Accent' if g == 'Accent' else g)
        lod0[g] = mc.join(objs, f'{nm}_LOD0'); bpy.ops.object.select_all(action='DESELECT')
    acc_share = area(lod0['Accent']) / sum(area(o) for o in lod0.values()) if 'Accent' in lod0 else 0.0
    T = {g: mc.tris(o) for g, o in lod0.items()}; tot = sum(T.values()); out = {}
    for lv, frac, cap in ((1, .5, 100_000), (2, .15, 25_000)):
        budget = min(tot * frac, cap); w = {g: math.sqrt(t) for g, t in T.items()}; tw = sum(w.values())
        for g, o in lod0.items():
            tgt = max(min(T[g] * (.5 if lv == 1 else .15), budget * w[g] / tw), 12)
            c = o.copy(); c.data = o.data.copy(); c.name = o.name.replace('_LOD0', f'_LOD{lv}'); bpy.context.scene.collection.objects.link(c)
            m = c.modifiers.new('d', 'DECIMATE'); m.ratio = min(1.0, tgt / max(T[g], 1)); m.use_collapse_triangulate = True; mc.apply(c, m)
            out.setdefault(lv, {})[g] = c
    cols = []
    for i, (kind, c, s) in enumerate(meta.get('collision', [])):
        bm = mc.box_bm(s, c); me = bpy.data.meshes.new(f'{tag}_Collision{i}'); bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new(me.name, me); bpy.context.scene.collection.objects.link(o); cols.append(o)
    if cols: mc.join(cols, f'{tag}_Collision')
    mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
    for o in lod0.values():
        for v in o.data.vertices: mn = Vector(map(min, mn, v.co)); mx = Vector(map(max, mx, v.co))
    dims = mx - mn
    assert all(dims[i] <= lim[i] + .005 for i in range(3)), f'{mid} over limit {tuple(round(d, 3) for d in dims)} > {lim}'
    assert mn.z > -.005, f'{mid} bottom below 0: {mn.z}'
    assert acc_share <= .10 + 1e-6, f'{mid} accent {acc_share:.3f} > 10 %'
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE / f'{tag}.blend'))
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.fbx(filepath=str(OUT / f'{tag}.fbx'), use_selection=True, object_types={'MESH', 'EMPTY'}, global_scale=1.0, apply_unit_scale=True,
                             apply_scale_options='FBX_SCALE_ALL', bake_space_transform=True, axis_forward='-Z', axis_up='Y', use_mesh_modifiers=True,
                             mesh_smooth_type='FACE', use_tspace=False, add_leaf_bones=False, bake_anim=False, path_mode='STRIP', embed_textures=False)
    lods = [{'lod': lv, 'triangles': sum(mc.tris(o) for o in d.values()), 'objects': len(d), 'materials': len({m.name for o in d.values() for m in o.data.materials})}
            for lv, d in ((0, lod0), (1, out[1]), (2, out[2]))]
    info = {'id': f'TX04-{mid.replace("_", "-")}', 'package': 'docs/execution/2026-11-05/A-48h-mountain-city-architecture.md', 'author': 'A (Johnnnny0823)',
            'version': 'v002', 'status': 'Exported; Imported/Visually Verified/In-game Verified: 未驗',
            'dimensions_m': [round(d, 3) for d in dims], 'limit_m': list(lim), 'grid_m': 4.0, 'origin': 'footprint centre, bottom z = 0, -Y = front',
            'minTier': TIER[mid], 'lods': lods, 'objectsLOD0': [o.name for o in lod0.values()],
            'detailObjects': [g for g in lod0 if g.startswith('Detail_')], 'glowObjects': [g for g in lod0 if g == 'Glow'],
            'materials': sorted({m.name for o in lod0.values() for m in o.data.materials}),
            'textures': {**{n: '2048x2048' for n in ('T_MountainStreet_Albedo', 'T_MountainStreet_Normal', 'T_MountainStreet_MetallicSmoothness', 'T_MountainStreet_Emission')},
                         **{n: '1024x1024' for n in ('T_TX04_Wall_Albedo', 'T_TX04_Wall_Normal')}},
            'materialNotes': {'M_TX04_Roof': 'same textures as M_MountainStreet_Trim, normal map strength 0.5 (Unity: _BumpScale 0.5)',
                              'M_TX04_Wall': 'T_TX04_Wall_Albedo / _Normal, normal strength 0.6, smoothness 0.08',
                              'M_TX04_Accent': 'trim Albedo x AccentColor (Unity: _BaseColor), trim Normal, smoothness 0.45'},
            'textureNote': 'shared MC01 trim sheet (art/textures/mountain-street-houses-a); the accent material reuses Albedo/Normal; '
                           'M_TX04_Wall uses the TX04 plaster tile (art/textures/tx04-branch-court, 4 x 4 m per tile, tiles along U)',
            'accent': {'material': 'M_TX04_Accent', 'object': f'{tag}_Accent' if 'Accent' in lod0 else None, 'defaultColor': ACCENT_DEFAULT,
                       'surfaceShare': round(acc_share, 4), 'limit': .10, 'howToRecolor': 'set the base colour (Unity: _BaseColor) of M_TX04_Accent'},
            'sockets': [{'name': e.name, 'location_m': [round(x, 3) for x in e.location], 'rotation_deg': [round(math.degrees(r), 1) for r in e.rotation_euler]} for e in SOCKETS],
            'collision': f'{tag}_Collision ({len(cols)} boxes)', 'extra': {k: v for k, v in meta.items() if k != 'collision'},
            'fbx': f'art/exports/{PKG}/{tag}.fbx', 'fps': '不寫（手機未實測）'}
    (OUT / f'{tag}.model_info.json').write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding='utf-8')
    print(mid, 'LOD tris', [l['triangles'] for l in lods], 'objects', [l['objects'] for l in lods], 'dims', info['dimensions_m'], 'accent', round(acc_share, 3), flush=True)

# ------------------------------------------------------------------ modules (each modelled after its picked three-view)

def hipgable(pre, Ex, Ey, zr, base_z=0.0, wx=None, wy=None, ze=.34, p=1.3, hip_run=.98, lift_h=.16, seed=0, res=1.0):
    """RF01's hip-and-gable roof (approved on PR #80) generalised to any Ex x Ey half extent: concave slopes, modelled pan and cover
    tiles, eave caps, main ridge with scroll ends, hip ridges, verge ridges, gable boards with battens, bargeboards and 懸魚,
    rafters, eave purlins, frieze boards and a dark ceiling. wx / wy: wall lines (purlins); the roof sits at base_z."""
    rg = random.Random(seed); n0 = len(mc.parts); wx = wx if wx is not None else Ex - .7; wy = wy if wy is not None else Ey - .7
    xg = Ex - hip_run; zgb = ze + (zr - ze) * .37; xr = xg + .02; sp = .24
    def lift(x, y):
        s = abs(x) / Ex + abs(y) / Ey; c = max(0.0, (s - 1.556) / (2 - 1.556)); return lift_h * c ** 2.0
    def z_fb(y): t = max(0.0, min(1.0, (Ey - abs(y)) / Ey)); return ze + (zr - ze) * t ** p
    def z_side(x): t = max(0.0, min(1.0, (Ex - abs(x)) / (Ex - xg))); return ze + (zgb - ze) * t ** p
    def z_at(x, y): return min(z_fb(y), z_side(x) if abs(x) > xg else 9) + lift(x, y)
    nx, ny = int(2 * Ex / (.06 * res)), int(2 * Ey / (.06 * res)); bm = bmesh.new(); vs = {}   # res > 1: coarser pan grid / cover tubes for big roofs
    for i in range(nx + 1):
        for j in range(ny + 1):
            x = -Ex + 2 * Ex * i / nx; y = -Ey + 2 * Ey * j / ny; z = z_at(x, y)
            on_side = abs(x) > xg and z_side(x) < z_fb(y); ch = y if on_side else x
            vs[i, j] = bm.verts.new((x, y, z - .018 * (.5 + .5 * math.cos(ch / sp * math.tau))))
    for i in range(nx):
        for j in range(ny): bm.faces.new((vs[i, j], vs[i + 1, j], vs[i + 1, j + 1], vs[i, j + 1]))
    pan = mc.finish(f'{pre}_pan', bm, 'tile', 'Main', axis=(1, 0, 0), smooth=True)
    m = pan.modifiers.new('t', 'SOLIDIFY'); m.thickness = .05; m.offset = -1; mc.apply(pan, m); mc.reuv(pan, 'tile', (1, 0, 0))
    def row(path_fn, n, name):
        pts, rad = [], []
        for k in range(n + 1):
            s_ = k / n; P = path_fn(s_)
            if P is None: break
            pts.append(P); rad.append(.052 + .010 * (((s_ * n * .5) % 1) < .18))
        if len(pts) <= 7: return []
        mc.tube(name, pts, .05, 'tile' if rg.random() > .3 else 'tile_moss', 'Main', sides=8, radii=rad); return pts
    eaves = []; ncov = 0
    for sgn in (-1, 1):
        for x in np.arange(-Ex + sp / 2, Ex, sp):
            if abs(x) > xg and z_side(x) < z_fb(sgn * Ey) - .005: continue
            def pf(s_, x=x, sgn=sgn):
                y = sgn * (Ey + .015 - s_ * (Ey + .015))
                if abs(x) > xg and z_side(x) < z_fb(y) + .06: return None
                return (x, y, z_at(x, y) + .02)
            pts = row(pf, max(16, int(Ey / (.07 * res))), f'{pre}_covfb{ncov}'); ncov += 1
            if pts: eaves.append((Vector(pts[0]), Vector((0, sgn, 0))))
        for y in np.arange(-Ey + sp / 2, Ey, sp):
            def ps(s_, y=y, sgn=sgn):
                x = sgn * (Ex + .015 - s_ * (Ex + .015 - xg))
                if z_side(x) > z_fb(y) - .06: return None
                return (x, y, z_at(x, y) + .02)
            if z_side(sgn * Ex) > z_fb(y) - .005: continue
            pts = row(ps, max(12, int(24 * (Ex - xg) / .98 / res)), f'{pre}_covs{ncov}'); ncov += 1
            if pts: eaves.append((Vector(pts[0]), Vector((sgn, 0, 0))))
    for k, (P, d) in enumerate(eaves):
        c = P + d * .008 + Vector((0, 0, -.004)); mc.lathe(f'{pre}_cap{k}', [(.004, -.015), (.062, -.015), (.062, .015), (.004, .015)], 'tile', 'Main', seg=12)
        o = mc.parts[-1]; t = d.normalized(); u = Vector((0, 0, 1)); s = u.cross(t)
        o.data.transform(Matrix(((s.x, u.x, t.x, c.x), (s.y, u.y, t.y, c.y), (s.z, u.z, t.z, c.z), (0, 0, 0, 1))))
    mc.tube(f'{pre}_ridge', [Vector((-xr - .1, 0, zr + .06)), Vector((xr + .1, 0, zr + .06))], .13, 'tile', 'Main', sides=10)
    for x in (-xr - .1, xr + .1):
        sx = 1 if x > 0 else -1; c = Vector((x - sx * .03, 0, zr + .06))   # starts inside the ridge end, never on its cap
        curl = [c + Vector((sx * .06 * math.sin(a) * (1 - a / 6), 0, .13 * (1 - math.cos(a)) * (1 - a / 8))) for a in np.linspace(0, 4.2, 14)]
        mc.tube(f'{pre}_ornament{sx:+d}', curl, .07, 'tile', 'Main', sides=10, radii=list(np.linspace(.09, .04, 14)))
    yfoot = Ey * (1 - ((zgb - ze) / (zr - ze)) ** (1 / p))
    def hip_y(x): return Ey * (1 - ((z_side(x) - ze) / (zr - ze)) ** (1 / p))
    for sx in (-1, 1):
        for sy in (-1, 1):
            pts = [Vector((sx * x, sy * hip_y(x), 0)) for x in np.linspace(xg, Ex - .04, 16)]
            pts = [Vector((q.x, q.y, z_at(q.x, q.y) + .065 - .02 * k / 15)) for k, q in enumerate(pts)]   # review #90: thinner, sits on the slope
            mc.tube(f'{pre}_hip{sx:+d}{sy:+d}', pts + [pts[-1] + Vector((sx * .025, sy * .025, .035))], .07, 'tile', 'Main', sides=10,
                    radii=list(np.linspace(.07, .04, 17)))
            mc.tube(f'{pre}_verge{sx:+d}{sy:+d}', [Vector((sx * (xg + .08), sy * yy, z_fb(yy) + .08)) for yy in np.linspace(.05, yfoot, 12)], .07, 'tile', 'Main', sides=10)
        poly = [(yy, z_fb(yy) - .02) for yy in np.linspace(-yfoot, yfoot, 25)] + [(yfoot, zgb), (-yfoot, zgb)]
        bm = bmesh.new(); v = [bm.verts.new((sx * (xg + .03), y, z)) for y, z in poly]; bm.faces.new(v if sx > 0 else list(reversed(v)))
        g = mc.finish(f'{pre}_gable{sx:+d}', bm, 'plank', 'Main', axis=(0, 0, 1))
        m = g.modifiers.new('t', 'SOLIDIFY'); m.thickness = .04; m.offset = 0; mc.apply(g, m); mc.reuv(g, 'plank', (0, 0, 1))
        for k, yy in enumerate(np.linspace(-yfoot + .12, yfoot - .12, max(3, int(yfoot / .2)))):
            zt = z_fb(yy) - .06
            if zt > zgb + .05: mc.box(f'{pre}_batten{sx:+d}{k}', (.03, .05, zt - zgb), (sx * (xg + .064), yy, (zt + zgb) / 2), 'beam', 'Main', bev=.004, axis=(0, 0, 1))
        for sy in (-1, 1):
            mc.tube(f'{pre}_barge{sx:+d}{sy:+d}', [Vector((sx * (xg + .09), sy * yy, z_fb(yy) - .03)) for yy in np.linspace(0, yfoot + .1, 14)], .045, 'beam', 'Main', sides=6)
        fh = min(.45, (zr - zgb) * .6)
        fish = [(0, zr - .12)] + [((.10 + .05 * math.sin(t * 3)), zr - .12 - fh * .8 * t) for t in np.linspace(.05, 1, 8)] + \
               [(0, zr - .12 - fh)] + [(-(.10 + .05 * math.sin(t * 3)), zr - .12 - fh * .8 * t) for t in np.linspace(1, .05, 8)]
        bm = bmesh.new(); v = [bm.verts.new((sx * (xg + .11), y, z)) for y, z in fish]; bm.faces.new(v)
        f = mc.finish(f'{pre}_fish{sx:+d}', bm, 'beam', 'Main', axis=(0, 0, 1)); m = f.modifiers.new('t', 'SOLIDIFY'); m.thickness = .03; mc.apply(f, m); mc.reuv(f, 'beam', (0, 0, 1))
    for sgn in (-1, 1):
        for x in np.arange(-wx + .1, wx, .22):
            y0, y1 = sgn * wy, sgn * (Ey - .06)
            mc.tube(f'{pre}_raftfb{sgn:+d}{x:+.2f}', [(x, y0, z_at(x, y0) - .10), (x, y1, z_at(x, y1) - .08)], .04, 'beam', 'Main', sides=8)
        for y in np.arange(-wy + .1, wy, .22):
            x0, x1 = sgn * wx, sgn * (Ex - .06)
            mc.tube(f'{pre}_rafts{sgn:+d}{y:+.2f}', [(x0, y, z_at(x0, y) - .10), (x1, y, z_at(x1, y) - .08)], .04, 'beam', 'Main', sides=8)
    zpf, zps = z_fb(wy) - .22, z_side(wx) - .22
    for sgn in (-1, 1):
        mc.beam(f'{pre}_purlinfb{sgn:+d}', (-wx - .05, sgn * wy, zpf), (wx + .05, sgn * wy, zpf), .16, .16, 'beam', 'Main', bev=.012)
        mc.beam(f'{pre}_purlins{sgn:+d}', (sgn * wx, -wy - .062, zps), (sgn * wx, wy + .062, zps), .148, .148, 'beam', 'Main', bev=.012)
        mc.box(f'{pre}_friezefb{sgn:+d}', (2 * wx - .1, .05, zpf - .07), (0, sgn * (wy - .02), (zpf - .07) / 2), 'plank', 'Main', bev=.004, axis=(1, 0, 0))
        mc.box(f'{pre}_friezes{sgn:+d}', (.05, 2 * wy - .14, zps - .07), (sgn * (wx - .02), 0, (zps - .07) / 2), 'plank', 'Main', bev=.004, axis=(0, 1, 0))
    mc.box(f'{pre}_ceiling', (2 * (wx - .045), 2 * (wy - .045), .03), (0, 0, .02), 'dark', 'Main', bev=0)
    if base_z:
        for o in mc.parts[n0:]: o.data.transform(Matrix.Translation((0, 0, base_z)))
    return {'ridge_z': base_z + zr + .06, 'eave_z': base_z + ze}

def dougong(pre, cx, y, z0, z1, depth=.2, arm=.36, grp='Main'):
    """一斗三升 bracket set between z0 (lintel top) and z1 (purlin / plate bottom), built in XZ at x = cx, centred on y"""
    za0 = z0 + (z1 - z0) * .32; za1 = za0 + (z1 - z0) * .26
    def dou(name, x, wt, wb, a, b, d):
        zm = b - (b - a) * .4
        mc.prism_xz(name, [(x - wb / 2, a), (x + wb / 2, a), (x + wt / 2, zm), (x + wt / 2, b), (x - wt / 2, b), (x - wt / 2, zm)], d, y - d / 2, 'beam', grp, bev=.004)
    dou(f'{pre}_dou', cx, .22, .16, z0 - .01, za0 + .004, depth)
    curve = lambda s: [(cx + s * (arm - .08 * (1 - math.cos(t * math.pi / 2))), za1 - .03 - (za1 - za0 - .03) * math.sin(t * math.pi / 2)) for t in np.linspace(0, 1, 5)]
    pts = [(cx - arm, za1), (cx + arm, za1)] + curve(1) + curve(-1)[::-1]
    mc.prism_xz(f'{pre}_gong', pts, depth * .5, y - depth * .25, 'beam', grp, bev=.003)
    for j, dx in enumerate((-arm * .8, 0, arm * .8)): dou(f'{pre}_sheng{j}', cx + dx, .14, .10, za1 - .006, z1 + .008, depth * .7)

def stone_block(name, size, center, strip='granite', amt=.008, bev=.02, seed=0):
    o = mc.box(name, size, center, strip, 'Main', bev=0, cuts=1 if max(size) > .6 else 0); mc.chisel(o, amt, 2.6, seed=seed, keep_bed=False); mc.bevel(o, bev, 2, 30); return o

# ------------------------------------------------------------------ TX04-GATE
LIMITS['GATE'] = (6.0, 3.0, 6.0); TIER['GATE'] = 'low'
def GATE():
    """院門 6 x 3 x 6 m (picked three-view option 4): a coursed granite platform with three front steps between cheek stones, a
    single-bay gatehouse of dark cedar columns on drum bases, plastered side bays over a stone dado, a pair of red-lacquer doors
    (the only accent) with bronze door nails and ring knockers, a front lintel with a blank framed plaque board, five bracket
    sets front and back, and a hip-and-gable tiled roof. Socket_Plaque on the plaque face, Socket_Emblem on the ridge centre."""
    rg = random.Random(7401); Wp, Dp, Hp = 5.2, 2.1, .45; y0p = .04   # platform centre: the three steps fit in front inside the 3 m depth
    # platform: edge stones + paving
    for side, (L, ang, dist) in enumerate(((Wp, 0, Dp / 2), (Dp - .68, math.pi / 2, Wp / 2), (Wp, math.pi, Dp / 2), (Dp - .68, -math.pi / 2, Wp / 2))):
        x = -L / 2; k = 0
        while x < L / 2 - 1e-3:
            l = min(rg.uniform(.7, 1.2), L / 2 - x)
            if L / 2 - (x + l) < .3: l = L / 2 - x
            o = stone_block(f'GATE_edge{side}_{k}', (l - .014, .34, Hp), (x + l / 2, -dist + .17, Hp / 2), 'granite_moss' if side == 2 else 'granite', seed=7400 + side * 10 + k)
            mc.rotz(o, ang); o.data.transform(Matrix.Translation((0, y0p + .0, 0))); x += l; k += 1
    mc.box('GATE_platcore', (Wp - .1, Dp - .1, Hp - .04), (0, y0p, (Hp - .04) / 2 + .01), 'dark', 'Main', bev=0)   # reaches into every edge stone
    for i, x in enumerate(np.linspace(-Wp / 2 + .34, Wp / 2 - .34, 5)[:-1]):
        for j, y in enumerate(np.linspace(-Dp / 2 + .34, Dp / 2 - .34, 3)[:-1]):
            w_ = (Wp - .68) / 4; d_ = (Dp - .68) / 2
            o = mc.box(f'GATE_pave{i}{j}', (w_ - .014, d_ - .014, .1), (x + w_ / 2, y0p + y + d_ / 2, Hp - .05 - .003 * ((i + j) % 2)), 'granite_top', 'Main', bev=0); mc.bevel(o, .012, 2, 30)
    # steps (front, between cheek stones)
    sw, ns, ys = 2.2, 3, y0p - Dp / 2
    for s in range(ns):
        zt = Hp * (s + 1) / (ns + 0); tread = .16
        hs_ = Hp * (s + 1) / ns - .004 * s   # each step a little narrower and lifted 4 mm: overlapping steps never share a plane
        dep = tread * (ns - s) + .02 + .02 * s   # backs staggered too
        stone_block(f'GATE_step{s}', (sw - .012 * s, dep, hs_), (0, ys - tread * (ns - s) + dep / 2, .004 * (s + 1) + hs_ / 2), 'granite_top', amt=.01, bev=.025, seed=7450 + s)
    for sx in (-1, 1):
        stone_block(f'GATE_cheek{sx:+d}', (.28, ns * .16 + .04, Hp), (sx * (sw / 2 + .14), ys - ns * .16 / 2 + .02, Hp / 2), 'granite', seed=7460 + sx)
    # columns: door posts at x = +-0.75, corner posts at +-2.05; front row y = -0.55, back row y = +0.55
    zb, zc1 = Hp, 3.55; colx = (-2.05, -.75, .75, 2.05); rows = (y0p - .55, y0p + .55); pr = .13
    petals = lambda th, i: (.05 * max(0.0, math.cos(8 * th)) ** 1.5) if 1 <= i <= 3 else 0.0
    for r_, y in enumerate(rows):
        for c_, x in enumerate(colx):
            mc.lathe(f'GATE_base{r_}{c_}', [(.06, zb - .015), (.17, zb - .015), (.205, zb + .05), (.19, zb + .13), (.15, zb + .175), (.06, zb + .175)], 'granite', 'Main', seg=32, center=(x, y, 0), wob=petals)
            mc.lathe(f'GATE_col{r_}{c_}', [(pr * 1.03, zb + .15)] + [(pr * (1 - .06 * t), zb + .2 + t * (zc1 - zb - .2)) for t in np.linspace(0, 1, 10)], 'beam', 'Main', seg=32, center=(x, y, 0))
    # side bays: stone dado + plaster between columns, front, back and the two ends
    def bay(name, a, b, y, axis='x'):
        za, zd = zb, zb + .8
        if axis == 'x':
            stone_block(f'{name}_dado', (b - a - .26, .30, zd - za), ((a + b) / 2, y, (za + zd) / 2), 'granite', seed=hash(name) % 997)
            wallmat(mc.box(f'{name}_plaster', (b - a - .24, .22, 3.35 - zd), ((a + b) / 2, y, (zd + 3.35) / 2), 'plaster', 'Main', bev=0), 3.35, len(mc.parts))
        else:
            stone_block(f'{name}_dado', (.30, b - a - .26, zd - za), (y, (a + b) / 2, (za + zd) / 2), 'granite', seed=hash(name) % 991)
            wallmat(mc.box(f'{name}_plaster', (.22, b - a - .24, 3.35 - zd), (y, (a + b) / 2, (zd + 3.35) / 2), 'plaster', 'Main', bev=0), 3.35, len(mc.parts))
    for r_, y in enumerate(rows):
        bay(f'GATE_bayL{r_}', colx[0], colx[1], y); bay(f'GATE_bayR{r_}', colx[2], colx[3], y)
    for sx in (-1, 1): bay(f'GATE_end{sx:+d}', rows[0], rows[1], sx * 2.05, axis='y')
    # lintels and plates around the bay, the plaque board above the doors
    for r_, y in enumerate(rows):
        mc.beam(f'GATE_lintel{r_}', (-2.25, y, 3.45), (2.25, y, 3.45), .2, .24, 'beam', 'Main', bev=.012)
        mc.beam(f'GATE_plate{r_}', (-2.3, y, 4.06), (2.3, y, 4.06), .26, .12, 'beam', 'Main', bev=.012)
        mc.box(f'GATE_frieze{r_}', (4.3, .05, .47), (0, y + (.03 if r_ == 0 else -.03), 3.815), 'plank', 'Main', bev=.003, axis=(1, 0, 0))
        for k, cx in enumerate((-2.05, -1.0, 0.0, 1.0, 2.05)): dougong(f'GATE_dg{r_}{k}', cx, y, 3.57, 4.0)
    for sx in (-1, 1):
        mc.beam(f'GATE_tie{sx:+d}', (sx * 2.05, rows[0] - .07, 3.45), (sx * 2.05, rows[1] + .07, 3.45), .188, .228, 'beam', 'Main', bev=.012)
    yd = (rows[0] + rows[1]) / 2 - .05; zd0, zd1 = zb + .02, 3.33
    # the door plane: jamb posts, a middle beam tied into the end ties, and walled bays either side of the doorway
    for sx in (-1, 1):
        mc.box(f'GATE_jamb{sx:+d}', (.18, .2, 3.45 - zb), (sx * .72, yd, (zb + 3.45) / 2), 'beam', 'Main', bev=.012, axis=(0, 0, 1))
        stone_block(f'GATE_middado{sx:+d}', (2.05 - .81 - .14, .26, .8), (sx * (.81 + (2.05 - .81 - .14) / 2), yd, zb + .4), 'granite', seed=7480 + sx)
        wallmat(mc.box(f'GATE_midplaster{sx:+d}', (2.05 - .81 - .13, .18, 3.35 - zb - .8), (sx * (.81 + (2.05 - .81 - .13) / 2), yd, (zb + .8 + 3.35) / 2), 'plaster', 'Main', bev=0), 3.35, len(mc.parts))
    mc.beam('GATE_midbeam', (-2.0, yd, 3.5), (2.0, yd, 3.5), .176, .2, 'beam', 'Main', bev=.012)
    mc.beam('GATE_doorhead', (-.75, yd, zd1 + .05), (.75, yd, zd1 + .05), .2, .1, 'beam', 'Main', bev=.01)
    mc.beam('GATE_sill', (-.62, yd, zb + .06), (.62, yd, zb + .06), .2, .16, 'oldwood', 'Main', bev=.012)   # sunk 2 cm into the paving
    for sx in (-1, 1):
        zl0, zl1 = zb + .135, zd1 + .005   # review #90: the leaf used to stop 4.5 cm above the sill (a light line); now it sits 5 mm into the sill and the door head
        leaf = mc.box(f'GATE_door{sx:+d}', (.6, .07, zl1 - zl0), (sx * .305, yd, (zl0 + zl1) / 2), 'plaster', 'Main', bev=.008, axis=(0, 0, 1)); accent(leaf)
        for i in range(5):
            for j in range(5):
                mc.lathe(f'GATE_nail{sx:+d}{i}{j}', [(.004, 0), (.022, 0), (.02, .012), (.008, .022), (.004, .024)], 'bronze', 'Main', seg=10)
                o = mc.parts[-1]; o.data.transform(Matrix.Translation((sx * (.08 + .11 * j), yd - .035, zd0 + .55 + .45 * i)) @ Vector((0, -1, 0)).to_track_quat('Z', 'Y').to_matrix().to_4x4())
        mc.tube(f'GATE_ring{sx:+d}', [(sx * .1 + .055 * math.cos(a), yd - .06, 1.75 + .055 * math.sin(a)) for a in np.linspace(0, math.tau, 17)], .008, 'bronze', 'Main', sides=6, caps=False)
        mc.lathe(f'GATE_boss{sx:+d}', [(.004, 0), (.05, 0), (.045, .014), (.004, .02)], 'bronze', 'Main', seg=12); o = mc.parts[-1]
        o.data.transform(Matrix.Translation((sx * .1, yd - .035, 1.81)) @ Vector((0, -1, 0)).to_track_quat('Z', 'Y').to_matrix().to_4x4())
    # review #90: a dark board right behind the leaves closes the side and middle gaps (they read as light lines from the front)
    mc.box('GATE_doorback', (1.30, .02, zl1 - zl0 - .01), (0, yd + .035 + .014, (zl0 + zl1) / 2), 'dark', 'Main', bev=0)
    # blank plaque board on the front frieze: frame + blank field; the plaque socket sits on its face
    yp = rows[0] - .13
    accent(mc.box('GATE_plaqueframe', (1.36, .06, .5), (0, yp, 3.81), 'beam', 'Main', bev=.012, axis=(1, 0, 0)))
    # review #90: lacquer only on the doors, the plaque frame and a thin band along the lintels (front and courtyard faces)
    for r_, y in enumerate(rows):
        sy = -1 if r_ == 0 else 1
        accent(mc.box(f'GATE_lintelband{r_}', (4.46, .014, .045), (0, y + sy * (.1 + .005), 3.375), 'beam', 'Main', bev=.003, axis=(1, 0, 0)))
    mc.box('GATE_plaquefield', (1.16, .03, .34), (0, yp - .035, 3.81), 'oldwood', 'Main', bev=.004, axis=(1, 0, 0))
    socket('Socket_Plaque', (0, yp - .05, 3.81), (math.radians(90), 0, 0))
    roof = hipgable('GATE_roof', 2.92, 1.38, 1.32, base_z=4.12, wx=2.15, wy=.55, hip_run=.9, seed=7470)
    for o in mc.parts:
        if o.name.startswith('GATE_roof'): o.data.transform(Matrix.Translation((0, y0p, 0)))
    socket('Socket_Emblem', (0, y0p, roof['ridge_z'] + .13))
    cols = [('box', (0, y0p, Hp / 2), (Wp, Dp, Hp))] + [('box', (0, ys - .24, Hp / 4), (sw, .48, Hp / 2))]
    cols += [('box', (sx * 1.4, y0p, Hp + 1.5), (1.4, 1.4, 3.0)) for sx in (-1, 1)] + [('box', (0, y0p, 4.9), (6.0, 3.0, 1.6))]
    return {'collision': cols, 'doorway_m': [1.24, 2.86], 'walkTop': Hp}

# ------------------------------------------------------------------ courtyard walls (ST / CO / DO share one wall builder)
WALL_T, WALL_HF, WALL_HW = .40, .62, 2.08          # thickness, footing top, plaster top
COPE_W2 = .31; COPE_Z0 = WALL_HW + .02; COPE_ZR = WALL_HW + .30

def wall_arm(pre, x0, x1, post0=True, end='square', seed=7500):
    """one run of courtyard wall along X from x0 to x1 at y = 0: two coursed granite footing courses, lime plaster (M_TX04_Wall),
    a timber frieze with small brackets on both faces, a double-pitch tiled coping. post0: dark cedar post + stone base at x0.
    end: 'square' (cut flat to join the next segment), 'corner' (x1 = 0 is the corner post centre, the coping is mitred along
    x = -y so a copy reflected over that line closes the L), 'jamb' (the body and coping stop against a doorway jamb at x1)."""
    rg = random.Random(seed); T, Hf, Hw = WALL_T, WALL_HF, WALL_HW
    corner = end.startswith('corner'); inner = 1 if end == 'corner' else -1   # 'corner': outer corner at -Y, 'corner+': at +Y
    trim = .2 if corner else {'square': 0.0, 'jamb': .17}[end]; a1 = x1 - trim
    for ci, (z0, z1) in enumerate(((0, .34), (.34, Hf))):
        x = x0 + (0 if ci % 2 == 0 else -.25); k = 0
        while x < a1 - 1e-3:
            a = max(x, x0); l = rg.uniform(.55, .95); b = min(x + l, a1)
            if a1 - b < .25: b = a1
            stone_block(f'{pre}_st{ci}_{k}', (b - a - (.014 if b < a1 else .004), T + .06 - .01 * ci, z1 - z0 - .012),
                        ((a + b) / 2, 0, (z0 + z1) / 2), 'granite_moss' if ci == 0 else 'granite', amt=.009, bev=.02, seed=seed + ci * 30 + k)
            x = b; k += 1
    mc.box(f'{pre}_core', (a1 - x0 - .1, T - .06, Hf - .05), ((x0 + a1) / 2, 0, (Hf - .05) / 2 + .03), 'dark', 'Main', bev=0)
    wallmat(mc.box(f'{pre}_plaster', (a1 - x0 - .01, T, Hw - Hf), ((x0 + a1) / 2, 0, (Hf + Hw) / 2), 'plaster', 'Main', bev=0), Hw, seed + 2)
    if post0:   # dark cedar like the gate columns (review #90)
        mc.box(f'{pre}_post', (.26, T + .08, Hw + .08 - .02), (x0 + .13, 0, (Hw + .08 + .02) / 2), 'beam', 'Main', bev=.012, axis=(0, 0, 1))
        stone_block(f'{pre}_postbase', (.3, T + .12, .2), (x0 + .17, 0, .1), 'granite_top', seed=seed + 90)
    fx0 = x0 + (.25 if post0 else 0.0)
    for sy in (-1, 1):
        mc.beam(f'{pre}_frieze{sy:+d}', (fx0, sy * (T / 2 + .03), Hw - .1), (a1 - (.015 if corner and sy == inner else 0), sy * (T / 2 + .03), Hw - .1), .06, .12, 'beam', 'Main', bev=.008)
        for j, xx in enumerate(np.arange(x0 + .7, a1 - .2, .8)):
            mc.prism_xz(f'{pre}_bracket{sy:+d}{j}', [(xx - .07, Hw - .17), (xx + .07, Hw - .17), (xx + .09, Hw - .04), (xx + .09, Hw + .02), (xx - .09, Hw + .02), (xx - .09, Hw - .04)],
                        .09, sy * (T / 2 + .03) - .045, 'beam', 'Main', bev=.004)
    # coping: two sloped tile slabs, cover-tile rows, eave caps, ridge; a corner run is mitred along x = x1 - y
    zc0, W2, zr = COPE_Z0, COPE_W2, COPE_ZR
    if end == 'corner': xe = lambda yy: x1 - yy
    elif end == 'corner+': xe = lambda yy: x1 + yy
    elif end == 'jamb': xe = lambda yy: a1
    else: xe = lambda yy: x1
    for sy in (-1, 1):
        bm = bmesh.new(); vs = {}; nx_, ny_ = max(8, int(round((x1 - x0) / 4 * 66))) + (1 if sy < 0 else 0), 6   # the two pans never share a vertex column
        for i in range(nx_ + 1):
            for j in range(ny_ + 1):
                t = j / ny_ * .96; yy = sy * (W2 - t * W2); xx = x0 + (xe(yy) - (0 if corner or sy > 0 else .003) - x0) * i / nx_   # the two pans' end faces never share a plane
                zz = zc0 + (zr - zc0) * t ** 1.2 - .012 * (.5 + .5 * math.cos(xx / .2 * math.tau))
                vs[i, j] = bm.verts.new((xx, yy, zz))
        for i in range(nx_):
            for j in range(ny_): bm.faces.new((vs[i, j], vs[i + 1, j], vs[i + 1, j + 1], vs[i, j + 1]))
        pan = mc.finish(f'{pre}_pan{sy:+d}', bm, 'tile', 'Main', axis=(1, 0, 0), smooth=True)
        m = pan.modifiers.new('t', 'SOLIDIFY'); m.thickness = .04; m.offset = -1; mc.apply(pan, m); mc.reuv(pan, 'tile', (1, 0, 0))
        for k, xx in enumerate(np.arange(x0 + .1, max(xe(sy * W2), xe(0)) - .05, .2)):
            pts = [(xx, sy * (W2 + .017 - t * (W2 + .017)), zc0 + (zr - zc0) * t ** 1.2 + .019) for t in np.linspace(0, .86, 8)]
            pts = [q for q in pts if q[0] < xe(q[1]) - .045]
            if len(pts) < 3: continue
            mc.tube(f'{pre}_cov{sy:+d}{k}', pts, .036, 'tile' if rg.random() > .3 else 'tile_moss', 'Main', sides=8)
            if abs(pts[0][1]) < W2: continue   # the eave end was clipped by the mitre: no cap
            mc.lathe(f'{pre}_cap{sy:+d}{k}', [(.004, -.011), (.044, -.011), (.044, .011), (.004, .011)], 'tile', 'Main', seg=12)
            o = mc.parts[-1]; t_ = Vector((0, sy, 0)); u = Vector((0, 0, 1)); s_ = u.cross(t_); c = Vector(pts[0]) + t_ * .009 + Vector((0, 0, -.003))
            o.data.transform(Matrix(((s_.x, u.x, t_.x, c.x), (s_.y, u.y, t_.y, c.y), (s_.z, u.z, t_.z, c.z), (0, 0, 0, 1))))
    be = x1 - (T + .02) / 2 if corner else {'square': x1 - .002, 'jamb': a1 - .01}[end]
    mc.box(f'{pre}_copingbed', (be - x0 - .002, T + .02, .06), ((x0 + .002 + be) / 2, 0, Hw + .02), 'granite_top', 'Main', bev=.004)
    xr = x1 if corner else xe(0) - .01
    mc.tube(f'{pre}_ridge', [(x0 + .01, 0, zr + .03), (xr, 0, zr + .03)], .07, 'tile', 'Main', sides=10)

# ------------------------------------------------------------------ TX04-WALL-ST
LIMITS['WALL_ST'] = (4.0, .76, 2.5); TIER['WALL_ST'] = 'low'
def WALL_ST():
    """straight courtyard wall 4 x 0.68 x 2.5 m (picked option 2): post at the -X end only (the next segment's post closes +X,
    so a run gets one post per 4 m), both ends cut square to join."""
    wall_arm('WALL', -2.0, 2.0, post0=True, end='square', seed=7501)
    return {'collision': [('box', (0, 0, WALL_HW / 2 + .1), (4.0, WALL_T + .1, WALL_HW + .2))], 'post': '-X end only', 'joins': ['-X', '+X']}

# ------------------------------------------------------------------ TX04-WALL-CO
LIMITS['WALL_CO'] = (4.0, 4.0, 2.5); TIER['WALL_CO'] = 'low'
def WALL_CO():
    """90-degree corner (picked option 2) on the 4 m grid: the two wall centre lines run on the cell's middle lines, arm A from
    the -X cell edge and arm B to the +Y cell edge, meeting at a square dark cedar corner post on a stone base at the cell
    centre. The coping is mitred on the outer diagonal with a hip ridge. Arm A carries a post at its far end like WALL_ST;
    arm B ends square, the next straight wall closes it with its own -X post."""
    T, Hw = WALL_T, WALL_HW
    wall_arm('CO_a', -2.0, 0.0, post0=True, end='corner', seed=7601)
    n0 = len(mc.parts); wall_arm('CO_b', -2.0, 0.0, post0=False, end='corner+', seed=7651)
    for o in mc.parts[n0:]: o.data.transform(Matrix.Rotation(-math.pi / 2, 4, 'Z'))   # (x, y) -> (y, -x): arm B along +Y, outer corner at (+X, -Y)
    mc.box('CO_post', (.48, .48, Hw + .08 - .02), (0, 0, (Hw + .08 + .02) / 2), 'beam', 'Main', bev=.014, axis=(0, 0, 1))
    stone_block('CO_postbase', (.56, .56, .22), (0, 0, .11), 'granite_top', seed=7690)
    mc.box('CO_copingbed', (T + .02, T + .02, .06), (0, 0, Hw + .02), 'granite_top', 'Main', bev=.004)
    W2 = COPE_W2; mc.tube('CO_hip', [(.01, -.01, COPE_ZR + .03), (W2 + .01, -W2 - .01, COPE_Z0 + .03)], .06, 'tile', 'Main', sides=10)
    return {'collision': [('box', (-1.0, 0, Hw / 2 + .1), (2.0, T + .1, Hw + .2)), ('box', (0, 1.0, Hw / 2 + .1), (T + .1, 2.0, Hw + .2))],
            'layout': 'wall centre lines on the cell middle lines: arm A x -2..0 at y 0, arm B y 0..2 at x 0; outer corner at (+X, -Y)',
            'joins': ['-X (arm A, has its own post)', '+Y (arm B, cut square)']}

# ------------------------------------------------------------------ TX04-WALL-DO
LIMITS['WALL_DO'] = (4.0, .76, 2.6); TIER['WALL_DO'] = 'low'
def WALL_DO():
    """4 m wall ending at a doorway (picked option 2): post at -X like WALL_ST, a heavier dark cedar jamb post at +X on a tall
    stone base, rising above the coping with a capping block and a small two-slope tile cap. The opening beyond +X and any
    door leaf are not part of this piece; mirror a second one for the other side of the opening."""
    T, Hw = WALL_T, WALL_HW
    wall_arm('DO', -2.0, 2.0, post0=True, end='jamb', seed=7701)
    xj = 2.0 - .17; zt = Hw + .2
    mc.box('DO_jamb', (.32, T + .14, zt - .26), (xj, 0, (zt + .26) / 2), 'beam', 'Main', bev=.014, axis=(0, 0, 1))
    stone_block('DO_jambbase', (.34, T + .2, .28), (xj, 0, .14), 'granite_top', seed=7790)
    mc.box('DO_jambcap', (.34, T + .18, .06), (xj, 0, zt + .03), 'oldwood', 'Main', bev=.008)
    for sy in (-1, 1):   # small two-slope tile cap over the jamb
        bm = bmesh.new(); hw_, h0, h1 = .16, zt + .05, zt + .17; y0, y1 = sy * (T / 2 + .1), 0.0
        vs = [bm.verts.new(v) for v in ((xj - hw_, y0, h0), (xj + hw_, y0, h0), (xj + hw_, y1, h1), (xj - hw_, y1, h1))]
        bm.faces.new(vs); cap = mc.finish(f'DO_jambtile{sy:+d}', bm, 'tile', 'Main', axis=(1, 0, 0))
        m = cap.modifiers.new('t', 'SOLIDIFY'); m.thickness = .035; m.offset = -1; mc.apply(cap, m); mc.reuv(cap, 'tile', (1, 0, 0))
    mc.tube('DO_jambridge', [(xj - .15, 0, zt + .18), (xj + .13, 0, zt + .18)], .04, 'tile', 'Main', sides=10)
    return {'collision': [('box', (0, 0, Hw / 2 + .1), (4.0, T + .1, Hw + .2))], 'post': '-X post, +X doorway jamb', 'joins': ['-X'],
            'doorway': '+X end; mirror a second WALL_DO (rotate 180 degrees) for the other jamb'}

# ------------------------------------------------------------------ shared building helpers (HALL / SIDE)
def platform(pre, Wp, Dp, Hp, yc=0.0, seed=0, moss_back=True):
    """coursed granite platform: edge stones all round (long sides full length, short sides between them), a dark core reaching
    into every edge stone, granite_top paving alternating 3 mm in height so neighbours never share a plane"""
    rg = random.Random(seed)
    for side, (L, ang, dist) in enumerate(((Wp, 0, Dp / 2), (Dp - .68, math.pi / 2, Wp / 2), (Wp, math.pi, Dp / 2), (Dp - .68, -math.pi / 2, Wp / 2))):
        x = -L / 2; k = 0
        while x < L / 2 - 1e-3:
            l = min(rg.uniform(.8, 1.3), L / 2 - x)
            if L / 2 - (x + l) < .35: l = L / 2 - x
            o = stone_block(f'{pre}_edge{side}_{k}', (l - .014, .34, Hp), (x + l / 2, -dist + .17, Hp / 2), 'granite_moss' if (side == 2 and moss_back) else 'granite', seed=seed + side * 40 + k)
            mc.rotz(o, ang); o.data.transform(Matrix.Translation((0, yc, 0))); x += l; k += 1
    mc.box(f'{pre}_platcore', (Wp - .1, Dp - .1, Hp - .04), (0, yc, (Hp - .04) / 2 + .01), 'dark', 'Main', bev=0)
    nx = max(2, int(round((Wp - .68) / 1.1))); ny = max(2, int(round((Dp - .68) / 1.1)))
    w_ = (Wp - .68) / nx; d_ = (Dp - .68) / ny
    for i in range(nx):
        for j in range(ny):
            x = -Wp / 2 + .34 + w_ * i; y = -Dp / 2 + .34 + d_ * j
            o = mc.box(f'{pre}_pave{i}_{j}', (w_ - .014, d_ - .014, .1), (x + w_ / 2, yc + y + d_ / 2, Hp - .05 - .003 * ((i + j) % 2)), 'granite_top', 'Main', bev=0)
            mc.bevel(o, .012, 2, 30)

def stairs(pre, sw, ns, Hp, yedge, tread=.28, seed=0, cheek=True):
    """ns steps from the ground up to Hp in front of yedge (-Y side), narrower / lifted / staggered by a few mm per step so
    no two steps share a plane, with sloping cheek stones either side"""
    for s in range(ns):
        hs_ = Hp * (s + 1) / ns - .004 * s; dep = tread * (ns - s) + .02 + .02 * s
        stone_block(f'{pre}_step{s}', (sw - .012 * s, dep, hs_), (0, yedge - tread * (ns - s) + dep / 2, .004 * (s + 1) + hs_ / 2), 'granite_top', amt=.01, bev=.025, seed=seed + s)
    if cheek:
        for sx in (-1, 1):
            L = ns * tread + .04; bm = bmesh.new()
            prof = [(yedge + .02, 0), (yedge - L, 0), (yedge - L, .16), (yedge + .02, Hp + .04)]
            v = [bm.verts.new((sx * (sw / 2 + .15) - .15, y, z)) for y, z in prof] + [bm.verts.new((sx * (sw / 2 + .15) + .15, y, z)) for y, z in prof]
            for f in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)): bm.faces.new([v[i] for i in f])
            o = mc.finish(f'{pre}_cheek{sx:+d}', bm, 'granite', 'Main'); mc.bevel(o, .02, 2, 30)

def column(pre, x, y, zb, zt, r, base_r):
    petals = lambda th, i: (base_r * .24 * max(0.0, math.cos(8 * th)) ** 1.5) if 1 <= i <= 3 else 0.0
    k = base_r / .205
    mc.lathe(f'{pre}_base', [(.06, zb - .015), (.17 * k, zb - .015), (.205 * k, zb + .05 * k), (.19 * k, zb + .13 * k), (.15 * k, zb + .175 * k), (.06, zb + .175 * k)],
             'granite', 'Main', seg=32, center=(x, y, 0), wob=petals)
    mc.lathe(f'{pre}_col', [(r * 1.03, zb + .15 * k)] + [(r * (1 - .06 * t), zb + .2 * k + t * (zt - zb - .2 * k)) for t in np.linspace(0, 1, 10)], 'beam', 'Main', seg=32, center=(x, y, 0))

def slat_bay(pre, a, b, y, z0, z1, rg, door=False):
    """直櫺 bay between two columns (x a..b, plane y): dark cedar frame, a plank dado panel, vertical slats above, a dark board
    behind (no see-through, no light lines); door=True adds a middle rail and two leaves' meeting stile"""
    w = b - a; cx = (a + b) / 2; zd = z0 + (.95 if not door else .9)
    mc.box(f'{pre}_back', (w - .02, .02, z1 - z0 - .02), (cx, y + .06, (z0 + z1) / 2), 'dark', 'Main', bev=0)
    for sx in (-1, 1): mc.box(f'{pre}_stile{sx:+d}', (.08, .1, z1 - z0), (cx + sx * (w / 2 - .04), y, (z0 + z1) / 2), 'beam', 'Main', bev=.006, axis=(0, 0, 1))
    for nm, z in (('sill', z0 + .04), ('rail', zd), ('head', z1 - .04)):
        mc.box(f'{pre}_{nm}', (w - .16, .1, .08), (cx, y - .002, z), 'beam', 'Main', bev=.006, axis=(1, 0, 0))
    mc.box(f'{pre}_dado', (w - .16, .04, zd - z0 - .12), (cx, y + .01, (z0 + .08 + zd - .04) / 2), 'plank', 'Main', bev=.004, axis=(0, 0, 1))
    if door: mc.box(f'{pre}_meet', (.06, .1, z1 - z0 - .18), (cx, y - .004, (z0 + z1) / 2), 'beam', 'Main', bev=.005, axis=(0, 0, 1))
    n = max(5, int((w - .16) / .09)); xs = np.linspace(a + .08 + .045, b - .08 - .045, n)
    for k, x in enumerate(xs):
        if door and abs(x - cx) < .06: continue
        mc.box(f'{pre}_slat{k}', (.035, .04, z1 - zd - .12), (x, y + .012 * (k % 2) * .1, (zd + .04 + z1 - .08) / 2), 'beam', 'Main', bev=.003, axis=(0, 0, 1))

# ------------------------------------------------------------------ TX04-HALL
LIMITS['HALL'] = (14.0, 10.0, 8.0); TIER['HALL'] = 'mid'
def HALL():
    """正堂 14 x 10 x 8 m (picked three-view option 3): a seven-bay single-storey hall on a granite platform with five front
    steps, a front verandah of dark cedar columns on lotus drum bases, the door plane with 直櫺 lattice doors and windows in
    six bays and red-lacquer double doors in the middle bay (accent, with nails and ring knockers, a dark backing board behind),
    plastered end and back walls over a stone dado, bracket sets on every column and mid-bay, a blank framed plaque on the front
    frieze (frame in lacquer) and a hip-and-gable roof with deep eaves. Socket_Plaque on the plaque, Socket_Emblem on the ridge."""
    rg = random.Random(8001); yo = .525                      # footprint centred: steps front -4.95, roof back +3.9
    Hp = .75; Wp, Dp = 13.3, 7.1; zb = Hp; zc1 = 4.34
    colx = [-5.95, -4.3, -2.65, -1.0, 1.0, 2.65, 4.3, 5.95]; yv, yd, yb = -2.9 + yo, -1.6 + yo, 2.9 + yo
    platform('HALL_plat', Wp, Dp, Hp, yc=yo, seed=8000)
    stairs('HALL_st', 3.4, 5, Hp, yo - Dp / 2, tread=.28, seed=8050)
    for r_, y in enumerate((yv, yd, yb)):
        for c_, x in enumerate(colx):
            column(f'HALL_c{r_}{c_}', x, y, zb, zc1, .19, .29)
    # door plane: red doors in the middle bay, lattice doors / windows in the others
    for c_ in range(7):
        a, b = colx[c_] + .2, colx[c_ + 1] - .2
        if c_ == 3:
            zl0, zl1 = zb + .1, 3.6
            mc.beam('HALL_sill', (a, yd, zb + .08), (b, yd, zb + .08), .22, .16, 'oldwood', 'Main', bev=.012)
            mc.beam('HALL_doorhead', (a, yd, zl1 + .1), (b, yd, zl1 + .1), .22, .2, 'beam', 'Main', bev=.012)
            mc.box('HALL_doorback', (b - a - .02, .02, zl1 - zl0), (0, yd + .06, (zl0 + zl1) / 2), 'dark', 'Main', bev=0)
            for sx in (-1, 1):
                lw = (b - a) / 2 - .01
                accent(mc.box(f'HALL_door{sx:+d}', (lw, .08, zl1 - zl0 + .01), (sx * (lw / 2 + .005), yd, (zl0 + zl1) / 2), 'plaster', 'Main', bev=.008, axis=(0, 0, 1)))
                for i in range(6):
                    for j in range(4):
                        mc.lathe(f'HALL_nail{sx:+d}{i}{j}', [(.004, 0), (.024, 0), (.022, .013), (.009, .024), (.004, .026)], 'bronze', 'Main', seg=10)
                        o = mc.parts[-1]; o.data.transform(Matrix.Translation((sx * (.12 + (lw - .24) / 3 * j), yd - .04, zl0 + .45 + .45 * i)) @ Vector((0, -1, 0)).to_track_quat('Z', 'Y').to_matrix().to_4x4())
                mc.tube(f'HALL_ring{sx:+d}', [(sx * .13 + .06 * math.cos(t), yd - .065, 1.95 + .06 * math.sin(t)) for t in np.linspace(0, math.tau, 17)], .009, 'bronze', 'Main', sides=6, caps=False)
                mc.lathe(f'HALL_boss{sx:+d}', [(.004, 0), (.055, 0), (.05, .015), (.004, .022)], 'bronze', 'Main', seg=12); o = mc.parts[-1]
                o.data.transform(Matrix.Translation((sx * .13, yd - .04, 2.01)) @ Vector((0, -1, 0)).to_track_quat('Z', 'Y').to_matrix().to_4x4())
        else:
            slat_bay(f'HALL_bay{c_}', a, b, yd, zb + .02, 3.72, rg, door=c_ in (2, 4))
            mc.box(f'HALL_bayhead{c_}', (b - a, .16, zc1 - 3.72 - .02), ((a + b) / 2, yd, (3.72 + zc1 - .02) / 2), 'plank', 'Main', bev=.004, axis=(1, 0, 0))
    # end and back walls: stone dado + plaster (M_TX04_Wall), between the columns
    def wall_bay(name, a, b, c, axis):
        za, zdd, zt = zb, zb + .85, zc1 - .06
        if axis == 'x':
            stone_block(f'{name}_dado', (b - a - .36, .34, zdd - za), ((a + b) / 2, c, (za + zdd) / 2), 'granite', seed=hash(name) % 997)
            wallmat(mc.box(f'{name}_plaster', (b - a - .34, .236, zt - zdd), ((a + b) / 2, c, (zdd + zt) / 2), 'plaster', 'Main', bev=0), zt, len(mc.parts))
        else:
            stone_block(f'{name}_dado', (.34, b - a - .36, zdd - za), (c, (a + b) / 2, (za + zdd) / 2), 'granite', seed=hash(name) % 991)
            wallmat(mc.box(f'{name}_plaster', (.236, b - a - .34, zt - zdd), (c, (a + b) / 2, (zdd + zt) / 2), 'plaster', 'Main', bev=0), zt, len(mc.parts))
    for c_ in range(7): wall_bay(f'HALL_back{c_}', colx[c_], colx[c_ + 1], yb, 'x')
    for sx in (-1, 1): wall_bay(f'HALL_end{sx:+d}', yd, yb, sx * 5.95, 'y')
    # beams: lintels on every row and both ends, plates on the outer rows, verandah tie beams, friezes, bracket sets
    for r_, y in enumerate((yv, yd, yb)):
        mc.beam(f'HALL_lintel{r_}', (-6.2, y, zc1 - .12), (6.2, y, zc1 - .12), .26, .3, 'beam', 'Main', bev=.012)
    for sx in (-1, 1):
        mc.beam(f'HALL_endlintel{sx:+d}', (sx * 5.95, yv - .2, zc1 - .12 + .003), (sx * 5.95, yb + .2, zc1 - .12 + .003), .246, .284, 'beam', 'Main', bev=.012)
    for x in colx[1:-1]:
        mc.beam(f'HALL_tie{x:+.2f}', (x, yv + .1, zc1 - .3), (x, yd - .1, zc1 - .3), .16, .2, 'beam', 'Main', bev=.01)
    zp = 4.98
    for r_, y in enumerate((yv, yb)):
        mc.beam(f'HALL_plate{r_}', (-6.25, y, zp), (6.25, y, zp), .3, .14, 'beam', 'Main', bev=.012)
        mc.box(f'HALL_frieze{r_}', (12.1, .05, zp - zc1 - .14), (0, y + (.03 if r_ == 0 else -.03), (zc1 + .02 + zp - .07) / 2), 'plank', 'Main', bev=.003, axis=(1, 0, 0))
        xs = sorted(set(colx + [(colx[i] + colx[i + 1]) / 2 for i in range(7)]))
        for k, cx in enumerate(xs): dougong(f'HALL_dg{r_}{k}', cx, y, zc1 + .04, zp - .07, depth=.26, arm=.42)
    for sx in (-1, 1):
        mc.beam(f'HALL_endplate{sx:+d}', (sx * 5.95, yv - .22, zp + .003), (sx * 5.95, yb + .22, zp + .003), .286, .134, 'beam', 'Main', bev=.012)
    # lacquer: a thin band along the front lintel (review #90) and the plaque frame
    accent(mc.box('HALL_lintelband', (12.36, .014, .05), (0, yv - .13 - .005, zc1 - .245), 'beam', 'Main', bev=.003, axis=(1, 0, 0)))
    yp = yv - .16
    accent(mc.box('HALL_plaqueframe', (2.1, .07, .62), (0, yp, (zc1 + zp) / 2 + .02), 'beam', 'Main', bev=.014, axis=(1, 0, 0)))
    mc.box('HALL_plaquefield', (1.86, .03, .44), (0, yp - .04, (zc1 + zp) / 2 + .02), 'oldwood', 'Main', bev=.004, axis=(1, 0, 0))
    socket('Socket_Plaque', (0, yp - .06, (zc1 + zp) / 2 + .02), (math.radians(90), 0, 0))
    roof = hipgable('HALL_roof', 6.95, 3.9, 2.62, base_z=zp + .07, wx=5.95, wy=2.9, hip_run=2.2, lift_h=.26, ze=.36, seed=8070, res=2.0)
    for o in mc.parts:
        if o.name.startswith('HALL_roof'): o.data.transform(Matrix.Translation((0, yo, 0)))
    socket('Socket_Emblem', (0, yo, roof['ridge_z'] + .2))
    cols = [('box', (0, yo, Hp / 2), (Wp, Dp, Hp)), ('box', (0, yo - Dp / 2 - .7, Hp / 4), (3.4, 1.4, Hp / 2)),
            ('box', (0, (yd + yb) / 2, zb + 1.8), (12.2, yb - yd + .3, 3.6)), ('box', (0, yo, 6.3), (13.9, 7.8, 3.2))]
    return {'collision': cols, 'doorway_m': [round(2.0 - .4, 2), round(3.6 - zb - .1, 2)], 'walkTop': Hp, 'bays': 7}

# ------------------------------------------------------------------ gable (懸山) roof for the side wing
def gableroof(pre, Ex, Ey, zr, base_z, wx, wy, ze=.3, p=1.25, seed=0, res=1.0):
    """two-slope 懸山 roof: concave pans with modelled cover tiles and eave caps, a main ridge with small scroll ends, verge
    ridges and bargeboards on the overhanging gable ends, rafters, purlins, friezes and a dark ceiling; the plastered gable
    triangles stand on the wall lines x = +-wx. Same tile vocabulary as hipgable (one ridge, no hips)."""
    rg = random.Random(seed); n0 = len(mc.parts); sp = .24
    def z_fb(y): t = max(0.0, min(1.0, (Ey - abs(y)) / Ey)); return ze + (zr - ze) * t ** p
    nx, ny = int(2 * Ex / (.06 * res)), int(2 * Ey / (.06 * res)) + 1; bm = bmesh.new(); vs = {}
    for i in range(nx + 1):
        for j in range(ny + 1):
            x = -Ex + 2 * Ex * i / nx; y = -Ey + 2 * Ey * j / ny
            vs[i, j] = bm.verts.new((x, y, z_fb(y) - .018 * (.5 + .5 * math.cos(x / sp * math.tau))))
    for i in range(nx):
        for j in range(ny): bm.faces.new((vs[i, j], vs[i + 1, j], vs[i + 1, j + 1], vs[i, j + 1]))
    pan = mc.finish(f'{pre}_pan', bm, 'tile', 'Main', axis=(1, 0, 0), smooth=True)
    m = pan.modifiers.new('t', 'SOLIDIFY'); m.thickness = .05; m.offset = -1; mc.apply(pan, m); mc.reuv(pan, 'tile', (1, 0, 0))
    k = 0
    for sgn in (-1, 1):
        for x in np.arange(-Ex + sp / 2 + .06, Ex - .06, sp):
            n = max(12, int(Ey / (.07 * res))); pts, rad = [], []
            for q in range(n + 1):
                s_ = q / n * .97; y = sgn * (Ey + .015 - s_ * (Ey + .015)); pts.append((x, y, z_fb(y) + .02)); rad.append(.05 + .01 * (((q * .5) % 1) < .18))
            mc.tube(f'{pre}_cov{k}', pts, .05, 'tile' if rg.random() > .3 else 'tile_moss', 'Main', sides=8, radii=rad)
            c = Vector(pts[0]) + Vector((0, sgn * .008, -.004)); mc.lathe(f'{pre}_cap{k}', [(.004, -.015), (.062, -.015), (.062, .015), (.004, .015)], 'tile', 'Main', seg=12)
            o = mc.parts[-1]; t = Vector((0, sgn, 0)); u = Vector((0, 0, 1)); s = u.cross(t)
            o.data.transform(Matrix(((s.x, u.x, t.x, c.x), (s.y, u.y, t.y, c.y), (s.z, u.z, t.z, c.z), (0, 0, 0, 1)))); k += 1
    mc.tube(f'{pre}_ridge', [Vector((-Ex - .02, 0, zr + .05)), Vector((Ex + .02, 0, zr + .05))], .11, 'tile', 'Main', sides=10)
    for sx in (-1, 1):
        c = Vector((sx * (Ex - .01), 0, zr + .05))
        curl = [c + Vector((sx * .05 * math.sin(a) * (1 - a / 6), 0, .1 * (1 - math.cos(a)) * (1 - a / 8))) for a in np.linspace(0, 4.0, 12)]
        mc.tube(f'{pre}_ornament{sx:+d}', curl, .06, 'tile', 'Main', sides=10, radii=list(np.linspace(.075, .035, 12)))
        for sy in (-1, 1):
            mc.tube(f'{pre}_verge{sx:+d}{sy:+d}', [Vector((sx * (Ex - .05), sy * yy, z_fb(yy) + .07)) for yy in np.linspace(.06, Ey + .01, 14)], .055, 'tile', 'Main', sides=10)
            mc.tube(f'{pre}_barge{sx:+d}{sy:+d}', [Vector((sx * (Ex - .03), sy * yy, z_fb(yy) - .07)) for yy in np.linspace(0, Ey - .02, 14)], .045, 'beam', 'Main', sides=6)
    for sgn in (-1, 1):
        for x in np.arange(-Ex + .12, Ex - .1, .22):
            if abs(abs(x) - wx) < .14: continue
            y0, y1 = sgn * (wy - .3 if abs(x) < wx else 0.05), sgn * (Ey - .06)
            mc.tube(f'{pre}_raft{sgn:+d}{x:+.2f}', [(x, y0, z_fb(y0) - .10), (x, y1, z_fb(y1) - .08)], .04, 'beam', 'Main', sides=8)
    zpf = z_fb(wy) - .22
    for sgn in (-1, 1):
        mc.beam(f'{pre}_purlin{sgn:+d}', (-Ex + .04, sgn * wy, zpf), (Ex - .04, sgn * wy, zpf), .16, .16, 'beam', 'Main', bev=.012)
        mc.box(f'{pre}_frieze{sgn:+d}', (2 * wx - .1, .05, zpf - .07), (0, sgn * (wy - .02), (zpf - .07) / 2), 'plank', 'Main', bev=.004, axis=(1, 0, 0))
    mc.beam(f'{pre}_ridgepurlin', (-Ex + .04, 0, zr - .2), (Ex - .04, 0, zr - .2), .18, .18, 'beam', 'Main', bev=.012)
    for sx in (-1, 1):   # plastered gable triangle on the wall line, under the slopes
        poly = [(yy, min(z_fb(yy) - .14, zr - .3)) for yy in np.linspace(-wy - .06, wy + .06, 21)] + [(wy + .06, .02), (-wy - .06, .02)]
        bm = bmesh.new(); v = [bm.verts.new((sx * wx, y, z)) for y, z in poly]; bm.faces.new(v if sx > 0 else list(reversed(v)))
        g = mc.finish(f'{pre}_gable{sx:+d}', bm, 'plaster', 'Main', axis=(0, 0, 1))
        m = g.modifiers.new('t', 'SOLIDIFY'); m.thickness = .22; m.offset = 0; mc.apply(g, m); wallmat(g, base_z + zr - .3, seed + sx)
    mc.box(f'{pre}_ceiling', (2 * (wx - .14), 2 * (wy - .045), .03), (0, 0, .02), 'dark', 'Main', bev=0)
    for o in mc.parts[n0:]: o.data.transform(Matrix.Translation((0, 0, base_z)))
    return {'ridge_z': base_z + zr + .05, 'eave_z': base_z + ze}

# ------------------------------------------------------------------ TX04-SIDE
LIMITS['SIDE'] = (8.0, 5.0, 5.0); TIER['SIDE'] = 'low'
def SIDE():
    """廂房 8 x 5 x 5 m (picked three-view option 1): a four-bay single-storey side wing on a low granite platform, dark cedar
    columns on small drum bases, a stone dado and lime plaster all round, three 直櫺 windows and one plain cedar double door
    (no lacquer: review #90 keeps lacquer for the gate and hall doors) with three steps in front, simple bracket sets and a
    two-slope 懸山 tiled roof with overhanging gable ends."""
    rg = random.Random(8101); yo = .23; Hp = .45; zb = Hp; zc = 3.2
    colx = [-3.3, -1.65, 0.0, 1.65, 3.3]; yf, yb = -1.5 + yo, 1.5 + yo
    platform('SIDE_plat', 7.4, 3.9, Hp, yc=yo, seed=8100)
    n0 = len(mc.parts); stairs('SIDE_st', 1.5, 3, Hp, yo - 3.9 / 2, tread=.24, seed=8150)
    for o in mc.parts[n0:]: o.data.transform(Matrix.Translation((.825, 0, 0)))   # in front of the door bay
    for r_, y in enumerate((yf, yb)):
        for c_, x in enumerate(colx): column(f'SIDE_c{r_}{c_}', x, y, zb, zc, .14, .21)
    def bay(name, a, b, c, axis, zt):
        za, zd = zb, zb + .8
        if axis == 'x':
            stone_block(f'{name}_dado', (b - a - .26, .32, zd - za), ((a + b) / 2, c, (za + zd) / 2), 'granite', seed=hash(name) % 997)
            return wallmat(mc.box(f'{name}_plaster', (b - a - .24, .22, zt - zd), ((a + b) / 2, c, (zd + zt) / 2), 'plaster', 'Main', bev=0), zt, len(mc.parts))
        stone_block(f'{name}_dado', (.32, b - a - .26, zd - za), (c, (a + b) / 2, (za + zd) / 2), 'granite', seed=hash(name) % 991)
        return wallmat(mc.box(f'{name}_plaster', (.22, b - a - .24, zt - zd), (c, (a + b) / 2, (zd + zt) / 2), 'plaster', 'Main', bev=0), zt, len(mc.parts))
    zt = zc - .12 - .15
    # front: 直櫺 windows in bays 0, 1 and 3, the door in bay 2 (as the picked sheet)
    for c_ in range(4):
        a, b = colx[c_], colx[c_ + 1]; cx = (a + b) / 2
        if c_ == 2:   # door bay: a cedar-framed doorway filling the bay between the columns, plain plank leaves
            dw, dh = b - a - .44, 2.2; z0 = zb + .02
            for sx in (-1, 1):
                mc.box(f'SIDE_jamb{sx:+d}', (.12, .2, dh + .1), (cx + sx * (dw / 2 + .06), yf, z0 + (dh + .1) / 2 - .02), 'beam', 'Main', bev=.008, axis=(0, 0, 1))
            wallmat(mc.box('SIDE_doortop', (dw + .24, .22, zt - z0 - dh - .1), (cx, yf, (z0 + dh + .1 + zt) / 2), 'plaster', 'Main', bev=0), zt, 8167)
            mc.beam('SIDE_doorhead', (cx - dw / 2 - .14, yf, z0 + dh + .05), (cx + dw / 2 + .14, yf, z0 + dh + .05), .22, .12, 'beam', 'Main', bev=.008)
            mc.beam('SIDE_sill', (cx - dw / 2, yf, zb + .05), (cx + dw / 2, yf, zb + .05), .2, .12, 'oldwood', 'Main', bev=.01)
            mc.box('SIDE_doorback', (dw - .02, .02, dh - .1), (cx, yf + .05, z0 + .1 + (dh - .1) / 2), 'dark', 'Main', bev=0)
            for sx in (-1, 1):
                lw = dw / 2 - .008
                mc.box(f'SIDE_door{sx:+d}', (lw, .06, dh - .06), (cx + sx * (lw / 2 + .004), yf, z0 + .08 + (dh - .06) / 2 - .02), 'plank', 'Main', bev=.006, axis=(0, 0, 1))
                for zz in (z0 + .45, z0 + 1.75): mc.box(f'SIDE_doorbatten{sx:+d}{zz:.2f}', (lw - .08, .025, .1), (cx + sx * (lw / 2 + .004), yf - .04, zz), 'beam', 'Main', bev=.004, axis=(1, 0, 0))
                mc.lathe(f'SIDE_pull{sx:+d}', [(.004, 0), (.03, 0), (.026, .012), (.004, .018)], 'bronze', 'Main', seg=10); o = mc.parts[-1]
                o.data.transform(Matrix.Translation((cx + sx * .1, yf - .029, z0 + 1.1)) @ Vector((0, -1, 0)).to_track_quat('Z', 'Y').to_matrix().to_4x4())
        else:
            bay(f'SIDE_front{c_}', a, b, yf, 'x', zt)
            ww, wh, wz = .9, 1.0, zb + 1.2; yw = yf - .11
            mc.box(f'SIDE_winback{c_}', (ww - .1, .01, wh - .1), (cx, yw - .006, wz + wh / 2), 'dark', 'Main', bev=0)
            for sx in (-1, 1): mc.box(f'SIDE_winstile{c_}{sx:+d}', (.07, .1, wh), (cx + sx * (ww / 2 - .035), yw - .03, wz + wh / 2), 'beam', 'Main', bev=.005, axis=(0, 0, 1))
            for nm, z in (('winsill', wz + .035), ('winhead', wz + wh - .035)):
                mc.box(f'SIDE_{nm}{c_}', (ww - .14, .1, .07), (cx, yw - .032, z), 'beam', 'Main', bev=.005, axis=(1, 0, 0))
            for k, x in enumerate(np.linspace(cx - ww / 2 + .13, cx + ww / 2 - .13, 7)):
                mc.box(f'SIDE_winslat{c_}{k}', (.035, .04, wh - .14), (x, yw - .04 - .002 * (k % 2), wz + wh / 2), 'beam', 'Main', bev=.003, axis=(0, 0, 1))
    for c_ in range(4): bay(f'SIDE_back{c_}', colx[c_], colx[c_ + 1], yb, 'x', zt)
    for sx in (-1, 1): bay(f'SIDE_end{sx:+d}', yf, yb, sx * 3.3, 'y', zt)
    for r_, y in enumerate((yf, yb)):
        mc.beam(f'SIDE_lintel{r_}', (-3.5, y, zc - .12), (3.5, y, zc - .12), .2, .262, 'beam', 'Main', bev=.012)
        mc.beam(f'SIDE_plate{r_}', (-3.55, y, zc + .3), (3.55, y, zc + .3), .24, .12, 'beam', 'Main', bev=.012)
        mc.box(f'SIDE_frieze{r_}', (6.5, .05, .3), (0, y + (.03 if r_ == 0 else -.03), zc + .09), 'plank', 'Main', bev=.003, axis=(1, 0, 0))
        for k, cx in enumerate(colx): dougong(f'SIDE_dg{r_}{k}', cx, y, zc + .02, zc + .24, depth=.16, arm=.26)
    for sx in (-1, 1):
        mc.beam(f'SIDE_endlintel{sx:+d}', (sx * 3.3, yf - .14, zc - .12 + .003), (sx * 3.3, yb + .14, zc - .12 + .003), .186, .226, 'beam', 'Main', bev=.012)
        mc.box(f'SIDE_endfrieze{sx:+d}', (.2, yb - yf - .12, .42), (sx * 3.3, (yf + yb) / 2, zc + .19), 'plank', 'Main', bev=.004, axis=(0, 1, 0))   # closes lintel -> gable
    roof = gableroof('SIDE_roof', 3.88, 2.22, 1.15, base_z=zc + .37, wx=3.3, wy=1.5, seed=8170, res=1.4)
    for o in mc.parts:
        if o.name.startswith('SIDE_roof'): o.data.transform(Matrix.Translation((0, yo, 0)))
    cols = [('box', (0, yo, Hp / 2), (7.4, 3.9, Hp)), ('box', (.825, yo - 1.95 - .36, Hp / 4), (1.8, .72, Hp / 2)),
            ('box', (0, yo, zb + 1.5), (6.9, 3.3, 3.0)), ('box', (0, yo, zc + 1.0), (7.84, 4.6, 1.6))]
    return {'collision': cols, 'doorway_m': [round(1.65 - .44, 2), 2.2], 'walkTop': Hp, 'bays': 4}

# ------------------------------------------------------------------ TX04-PAVE
LIMITS['PAVE'] = (4.0, 4.0, .2); TIER['PAVE'] = 'low'
def PAVE():
    """院鋪地 one 4 x 4 m courtyard bay (picked three-view option 3): long granite kerb stones on the -X and -Y edges only, so
    a grid of bays shows one dividing kerb line every 4 m (never doubled); inside, staggered courses of long slabs 0.12 m
    thick, tops within +-3 mm of each other so characters walk smoothly, a dark bed underneath that hides every joint."""
    rg = random.Random(8201); H = .12; kw = .3
    mc.box('PAVE_bed', (3.98, 3.98, .05), (0, 0, .045), 'dark', 'Main', bev=0)   # bottom 2 cm up: ties kerbs and slabs, never on a kerb bottom
    for side, (L, ang, dist) in enumerate(((4.0, 0, 2.0), (4.0 - kw, -math.pi / 2, 2.0))):   # -Y kerb full length, -X kerb after it
        x = -L / 2; k = 0
        while x < L / 2 - 1e-3:
            l = min(rg.uniform(.9, 1.4), L / 2 - x)
            if L / 2 - (x + l) < .4: l = L / 2 - x
            o = stone_block(f'PAVE_kerb{side}_{k}', (l - .012, kw - .006, H + .01 - .002 * (k % 2)), (x + l / 2, -dist + kw / 2, (H + .01) / 2 + .002), 'granite',
                            amt=.004, bev=.018, seed=8200 + side * 20 + k)
            if side == 1: mc.rotz(o, ang); o.data.transform(Matrix.Translation((0, kw / 2, 0)))
            x += l; k += 1
    x0, y0 = -2.0 + kw, -2.0 + kw; rows = 6; d = (4.0 - kw) / rows
    for j in range(rows):
        x = x0 - (rg.uniform(.2, .6) if j % 2 else 0.0); k = 0
        while x < 2.0 - 1e-3:
            a = max(x, x0); l = rg.uniform(.7, 1.3); b = min(x + l, 2.0)
            if 2.0 - b < .3: b = 2.0
            if b - a < .2: x = b; continue
            moss = rg.random() < .18
            o = mc.box(f'PAVE_slab{j}_{k}', (b - a - .012, d - .012, .09), ((a + b) / 2, y0 + d * j + d / 2, H - .045 - .003 * ((j + k) % 2) - .0015 * (k % 3 == 2)),
                       'granite_moss' if moss else 'granite_top', 'Main', bev=0)
            mc.bevel(o, .01, 2, 30); x = b; k += 1
    return {'collision': [('box', (0, 0, H / 2), (4.0, 4.0, H))], 'walkTop': H, 'kerbs': '-X and -Y edges only (one kerb line per grid line when tiled)'}

# ------------------------------------------------------------------ TX04-STEPS
LIMITS['STEPS'] = (4.0, 2.0, .8); TIER['STEPS'] = 'low'
def STEPS():
    """石階 4 m wide, 2 m deep (picked three-view option 2): five worn granite steps rising 0.75 m to the back edge (the hall
    platform height), between two sloping granite cheek stones; sides in coursed stone, no lacquer, no tiles."""
    ns, Hp, tread, sw = 5, .75, .392, 3.39
    for s in range(ns):
        hs_ = Hp * (s + 1) / ns - .004 * s; dep = tread * (ns - s) + .02 * s + .0
        stone_block(f'STEPS_step{s}', (sw - .012 * s, dep - .004 - .004 * s, hs_), (0, 1.0 - (dep - .004 * s) / 2 - .002 - .004 * s, .004 * (s + 1) + hs_ / 2 - .004 * (s == 0)), 'granite_top', amt=.008, bev=.025, seed=8250 + s)
    for sx in (-1, 1):
        bm = bmesh.new(); prof = [(1.0, 0), (-1.0, 0), (-1.0, .2), (1.0, Hp + .05)]
        v = [bm.verts.new((sx * 1.85 - .15, y, z)) for y, z in prof] + [bm.verts.new((sx * 1.85 + .15, y, z)) for y, z in prof]
        for f in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)): bm.faces.new([v[i] for i in f])
        o = mc.finish(f'STEPS_cheek{sx:+d}', bm, 'granite', 'Main'); mc.bevel(o, .02, 2, 30)
        stone_block(f'STEPS_block{sx:+d}', (.32, .3, .26), (sx * 1.84, -.85, .13), 'granite_moss', amt=.008, bev=.02, seed=8270 + sx)
    cols = [('box', (0, 1.0 - tread * (ns - s) / 2, Hp * (s + 1) / ns / 2), (4.0, tread * (ns - s), Hp * (s + 1) / ns)) for s in range(ns)]
    return {'collision': cols, 'walkTop': Hp, 'rise_m': Hp, 'steps': ns, 'top': '+Y edge at 0.75 m (hall platform height)'}

if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for a in args: build(a)
