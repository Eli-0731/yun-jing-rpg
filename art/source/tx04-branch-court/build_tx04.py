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

def socket(name, loc, rot=(0, 0, 0)):
    e = bpy.data.objects.new(name, None); e.empty_display_type = 'ARROWS'; e.empty_display_size = .3
    e.location = loc; e.rotation_euler = rot; bpy.context.scene.collection.objects.link(e); SOCKETS.append(e); return e

def area(o):
    return sum(p.area for p in o.data.polygons)

def build(mid):
    mc.clear(); mc.load_trim(); accent_material(); SOCKETS.clear()
    meta = globals()[mid]() or {}; parts = mc.parts; lim = LIMITS[mid]; tag = f'TX04_{mid}'
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
            'version': 'v001', 'status': 'Exported; Imported/Visually Verified/In-game Verified: 未驗',
            'dimensions_m': [round(d, 3) for d in dims], 'limit_m': list(lim), 'grid_m': 4.0, 'origin': 'footprint centre, bottom z = 0, -Y = front',
            'minTier': TIER[mid], 'lods': lods, 'objectsLOD0': [o.name for o in lod0.values()],
            'detailObjects': [g for g in lod0 if g.startswith('Detail_')], 'glowObjects': [g for g in lod0 if g == 'Glow'],
            'materials': sorted({m.name for o in lod0.values() for m in o.data.materials}),
            'textures': {n: '2048x2048' for n in ('T_MountainStreet_Albedo', 'T_MountainStreet_Normal', 'T_MountainStreet_MetallicSmoothness', 'T_MountainStreet_Emission')},
            'textureNote': 'shared MC01 trim sheet (art/textures/mountain-street-houses-a); the accent material reuses Albedo/Normal',
            'accent': {'material': 'M_TX04_Accent', 'object': f'{tag}_Accent' if 'Accent' in lod0 else None, 'defaultColor': ACCENT_DEFAULT,
                       'surfaceShare': round(acc_share, 4), 'limit': .10, 'howToRecolor': 'set the base colour (Unity: _BaseColor) of M_TX04_Accent'},
            'sockets': [{'name': e.name, 'location_m': [round(x, 3) for x in e.location], 'rotation_deg': [round(math.degrees(r), 1) for r in e.rotation_euler]} for e in SOCKETS],
            'collision': f'{tag}_Collision ({len(cols)} boxes)', 'extra': {k: v for k, v in meta.items() if k != 'collision'},
            'fbx': f'art/exports/{PKG}/{tag}.fbx', 'fps': '不寫（手機未實測）'}
    (OUT / f'{tag}.model_info.json').write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding='utf-8')
    print(mid, 'LOD tris', [l['triangles'] for l in lods], 'objects', [l['objects'] for l in lods], 'dims', info['dimensions_m'], 'accent', round(acc_share, 3), flush=True)

# ------------------------------------------------------------------ modules (each modelled after its picked three-view)

def hipgable(pre, Ex, Ey, zr, base_z=0.0, wx=None, wy=None, ze=.34, p=1.3, hip_run=.98, lift_h=.16, seed=0):
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
    nx, ny = int(2 * Ex / .06), int(2 * Ey / .06); bm = bmesh.new(); vs = {}
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
            pts = row(pf, max(16, int(Ey / .07)), f'{pre}_covfb{ncov}'); ncov += 1
            if pts: eaves.append((Vector(pts[0]), Vector((0, sgn, 0))))
        for y in np.arange(-Ey + sp / 2, Ey, sp):
            def ps(s_, y=y, sgn=sgn):
                x = sgn * (Ex + .015 - s_ * (Ex + .015 - xg))
                if z_side(x) > z_fb(y) - .06: return None
                return (x, y, z_at(x, y) + .02)
            if z_side(sgn * Ex) > z_fb(y) - .005: continue
            pts = row(ps, 24, f'{pre}_covs{ncov}'); ncov += 1
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
            pts = [Vector((q.x, q.y, z_at(q.x, q.y) + .09)) for q in pts]
            mc.tube(f'{pre}_hip{sx:+d}{sy:+d}', pts + [pts[-1] + Vector((sx * .03, sy * .03, .08))], .085, 'tile', 'Main', sides=10)
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
            mc.box(f'{name}_plaster', (b - a - .24, .22, 3.35 - zd), ((a + b) / 2, y, (zd + 3.35) / 2), 'plaster', 'Main', bev=0)
        else:
            stone_block(f'{name}_dado', (.30, b - a - .26, zd - za), (y, (a + b) / 2, (za + zd) / 2), 'granite', seed=hash(name) % 991)
            mc.box(f'{name}_plaster', (.22, b - a - .24, 3.35 - zd), (y, (a + b) / 2, (zd + 3.35) / 2), 'plaster', 'Main', bev=0)
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
        mc.box(f'GATE_midplaster{sx:+d}', (2.05 - .81 - .13, .18, 3.35 - zb - .8), (sx * (.81 + (2.05 - .81 - .13) / 2), yd, (zb + .8 + 3.35) / 2), 'plaster', 'Main', bev=0)
    mc.beam('GATE_midbeam', (-2.0, yd, 3.5), (2.0, yd, 3.5), .176, .2, 'beam', 'Main', bev=.012)
    mc.beam('GATE_doorhead', (-.75, yd, zd1 + .05), (.75, yd, zd1 + .05), .2, .1, 'beam', 'Main', bev=.01)
    mc.beam('GATE_sill', (-.62, yd, zb + .06), (.62, yd, zb + .06), .2, .16, 'oldwood', 'Main', bev=.012)   # sunk 2 cm into the paving
    for sx in (-1, 1):
        leaf = mc.box(f'GATE_door{sx:+d}', (.6, .07, zd1 - zd0 - .17), (sx * .305, yd, (zd0 + .16 + zd1) / 2), 'plaster', 'Main', bev=.008, axis=(0, 0, 1)); accent(leaf)
        for i in range(5):
            for j in range(5):
                mc.lathe(f'GATE_nail{sx:+d}{i}{j}', [(.004, 0), (.022, 0), (.02, .012), (.008, .022), (.004, .024)], 'bronze', 'Main', seg=10)
                o = mc.parts[-1]; o.data.transform(Matrix.Translation((sx * (.08 + .11 * j), yd - .035, zd0 + .55 + .45 * i)) @ Vector((0, -1, 0)).to_track_quat('Z', 'Y').to_matrix().to_4x4())
        mc.tube(f'GATE_ring{sx:+d}', [(sx * .1 + .055 * math.cos(a), yd - .06, 1.75 + .055 * math.sin(a)) for a in np.linspace(0, math.tau, 17)], .008, 'bronze', 'Main', sides=6, caps=False)
        mc.lathe(f'GATE_boss{sx:+d}', [(.004, 0), (.05, 0), (.045, .014), (.004, .02)], 'bronze', 'Main', seg=12); o = mc.parts[-1]
        o.data.transform(Matrix.Translation((sx * .1, yd - .035, 1.81)) @ Vector((0, -1, 0)).to_track_quat('Z', 'Y').to_matrix().to_4x4())
    # blank plaque board on the front frieze: frame + blank field; the plaque socket sits on its face
    yp = rows[0] - .13
    mc.box('GATE_plaqueframe', (1.36, .06, .5), (0, yp, 3.81), 'beam', 'Main', bev=.012, axis=(1, 0, 0))
    mc.box('GATE_plaquefield', (1.16, .03, .34), (0, yp - .035, 3.81), 'oldwood', 'Main', bev=.004, axis=(1, 0, 0))
    socket('Socket_Plaque', (0, yp - .05, 3.81), (math.radians(90), 0, 0))
    roof = hipgable('GATE_roof', 2.92, 1.38, 1.32, base_z=4.12, wx=2.15, wy=.55, hip_run=.9, seed=7470)
    for o in mc.parts:
        if o.name.startswith('GATE_roof'): o.data.transform(Matrix.Translation((0, y0p, 0)))
    socket('Socket_Emblem', (0, y0p, roof['ridge_z'] + .13))
    cols = [('box', (0, y0p, Hp / 2), (Wp, Dp, Hp))] + [('box', (0, ys - .24, Hp / 4), (sw, .48, Hp / 2))]
    cols += [('box', (sx * 1.4, y0p, Hp + 1.5), (1.4, 1.4, 3.0)) for sx in (-1, 1)] + [('box', (0, y0p, 4.9), (6.0, 3.0, 1.6))]
    return {'collision': cols, 'doorway_m': [1.24, 2.86], 'walkTop': Hp}

# ------------------------------------------------------------------ TX04-WALL-ST
LIMITS['WALL_ST'] = (4.0, .76, 2.5); TIER['WALL_ST'] = 'low'
def WALL_ST():
    """straight courtyard wall 4 x 0.62 x 2.5 m (picked option 2): coursed granite footing, lime plaster, a red-lacquer post at the
    -X end only (the next segment's post closes +X, so a run gets one post per 4 m), a timber frieze beam with small brackets on
    both faces, and a double-pitch tiled coping with cover tiles, eave caps and a ridge. Both ends are cut square to join."""
    rg = random.Random(7501); L, T, Hf, Hw = 4.0, .40, .62, 2.08
    x = -L / 2; k = 0
    for ci, (z0, z1) in enumerate(((0, .34), (.34, Hf))):
        x = -L / 2 + (0 if ci % 2 == 0 else -.25); k = 0
        while x < L / 2 - 1e-3:
            a = max(x, -L / 2); l = rg.uniform(.55, .95); b = min(x + l, L / 2)
            if L / 2 - b < .25: b = L / 2
            o = stone_block(f'WALL_st{ci}_{k}', (b - a - (.014 if b < L / 2 else .004) - (.0 if a > -L / 2 else .0), T + .06 - .01 * ci, z1 - z0 - .012),
                            ((a + b) / 2, 0, (z0 + z1) / 2), 'granite_moss' if ci == 0 else 'granite', amt=.009, bev=.02, seed=7500 + ci * 30 + k)
            x = b; k += 1
    mc.box('WALL_core', (L - .1, T - .06, Hf - .05), (0, 0, (Hf - .05) / 2 + .03), 'dark', 'Main', bev=0)
    mc.box('WALL_plaster', (L - .01, T, Hw - Hf), (0, 0, (Hf + Hw) / 2), 'plaster', 'Main', bev=0)
    post = mc.box('WALL_post', (.26, T + .08, Hw + .08 - .02), (-L / 2 + .13, 0, (Hw + .08 + .02) / 2), 'plaster', 'Main', bev=.012, axis=(0, 0, 1)); accent(post)
    stone_block('WALL_postbase', (.3, T + .12, .2), (-L / 2 + .17, 0, .1), 'granite_top', seed=7590)
    for sy in (-1, 1):
        mc.beam(f'WALL_frieze{sy:+d}', (-L / 2 + .25, sy * (T / 2 + .03), Hw - .1), (L / 2, sy * (T / 2 + .03), Hw - .1), .06, .12, 'beam', 'Main', bev=.008)
        for j, xx in enumerate(np.arange(-L / 2 + .7, L / 2 - .2, .8)):
            mc.prism_xz(f'WALL_bracket{sy:+d}{j}', [(xx - .07, Hw - .17), (xx + .07, Hw - .17), (xx + .09, Hw - .04), (xx + .09, Hw + .02), (xx - .09, Hw + .02), (xx - .09, Hw - .04)],
                        .09, sy * (T / 2 + .03) - .045, 'beam', 'Main', bev=.004)
    # coping: two sloped tile slabs, cover-tile rows, eave caps, ridge
    zc0, W2 = Hw + .02, .31; zr = Hw + .30
    for sy in (-1, 1):
        bm = bmesh.new(); vs = {}
        nx_, ny_ = 66, 6
        for i in range(nx_ + 1):
            for j in range(ny_ + 1):
                xx = -L / 2 + L * i / nx_; t = j / ny_; yy = sy * (W2 - t * W2); zz = zc0 + (zr - zc0) * t ** 1.2 - .012 * (.5 + .5 * math.cos(xx / .2 * math.tau))
                vs[i, j] = bm.verts.new((xx, yy, zz))
        for i in range(nx_):
            for j in range(ny_): bm.faces.new((vs[i, j], vs[i + 1, j], vs[i + 1, j + 1], vs[i, j + 1]))
        pan = mc.finish(f'WALL_pan{sy:+d}', bm, 'tile', 'Main', axis=(1, 0, 0), smooth=True)
        m = pan.modifiers.new('t', 'SOLIDIFY'); m.thickness = .04; m.offset = -1; mc.apply(pan, m); mc.reuv(pan, 'tile', (1, 0, 0))
        for k, xx in enumerate(np.arange(-L / 2 + .1, L / 2 - .05, .2)):
            pts = [(xx, sy * (W2 + .012 - t * (W2 + .012)), zc0 + (zr - zc0) * t ** 1.2 + .016) for t in np.linspace(0, .9, 8)]
            mc.tube(f'WALL_cov{sy:+d}{k}', pts, .036, 'tile' if rg.random() > .3 else 'tile_moss', 'Main', sides=8)
            mc.lathe(f'WALL_cap{sy:+d}{k}', [(.004, -.011), (.044, -.011), (.044, .011), (.004, .011)], 'tile', 'Main', seg=12)
            o = mc.parts[-1]; t_ = Vector((0, sy, 0)); u = Vector((0, 0, 1)); s = u.cross(t_); c = Vector(pts[0]) + t_ * .006 + Vector((0, 0, -.003))
            o.data.transform(Matrix(((s.x, u.x, t_.x, c.x), (s.y, u.y, t_.y, c.y), (s.z, u.z, t_.z, c.z), (0, 0, 0, 1))))
    mc.box('WALL_copingbed', (L - .004, T + .02, .06), (0, 0, Hw + .02), 'granite_top', 'Main', bev=.004)
    mc.tube('WALL_ridge', [(-L / 2 + .01, 0, zr + .03), (L / 2 - .01, 0, zr + .03)], .07, 'tile', 'Main', sides=10)
    return {'collision': [('box', (0, 0, Hw / 2 + .1), (L, T + .1, Hw + .2))], 'post': '-X end only', 'joins': ['-X', '+X']}

if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for a in args: build(a)
