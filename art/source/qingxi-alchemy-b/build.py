"""Build, bake, export, render and validate kit assets.

  blender -b --python-exit-code 1 --python build.py -- B01 B02        (all states of the listed assets)
  blender -b --python-exit-code 1 --python build.py -- B01 --no-render

Outputs per asset state <key> = <ID>_<Name>[_<state>]:
  art/source/qingxi-alchemy-b/blend/<key>_v001.blend      procedural parts (hidden) + baked game mesh + LODs
  art/exports/qingxi-alchemy-b/<ID>_<Name>/v001/<key>.glb  LOD0, embedded textures
  .../<key>.fbx (+ textures/ beside it, LOD0-2 for Unity LOD Group) and <key>_model_info.json
  art/previews/qingxi-alchemy-b/<ID>/<state>/               10 neutral views, 4 stylized, 2 close-ups, wireframe
"""
import bpy, sys, json, math, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import qa_lib as Q
import qa_assets as A

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
RENDER = '--no-render' not in argv
QUICK = '--quick' in argv
ids = [a for a in argv if not a.startswith('--')] or sorted(A.ASSETS)


def key_of(a, st):
    return f"{a['id']}_{a['name']}" + ('' if st == 'default' else f'_{st}')


def build_state(a, st):
    t0 = time.time(); s = Q.reset(); key = key_of(a, st)
    src = Q.coll('10_Procedural_Source'); Q.ACTIVE['coll'] = src
    parts, info = a['build'](st)
    bpy.context.view_layer.update()
    game = Q.coll('00_Game_Export'); Q.ACTIVE['coll'] = game
    G, K = Q.game_mesh(key, parts, game)
    adir = Q.EXPORTS / f"{a['id']}_{a['name']}" / Q.VER; tdir = adir / 'textures'
    imgs, alpha = Q.bake_asset(G, key, tdir, a['res'])
    gm = Q.game_material(key, imgs, alpha); G.data.materials.clear(); G.data.materials.append(gm)
    if K:
        Q.select_only([G, K], G); bpy.ops.object.join(); G = bpy.context.view_layer.objects.active
    G.name = f'{key}_LOD0'
    lods = Q.make_lods(G, gcoll=game)
    for l, nm in zip(lods, ('LOD1', 'LOD2')): l.name = f'{key}_{nm}'
    nodes = Q.split_nodes(G, key)
    src.hide_render = True; src.hide_viewport = True
    for o in src.objects: o.hide_render = True
    for l in lods: l.hide_render = True; l.hide_set(True)
    # export
    glb = adir / f'{key}.glb'; fbx = adir / f'{key}.fbx'
    for l in lods: l.hide_set(False)
    Q.export(nodes, glb, fbx, nodes + lods)
    for l in lods: l.hide_set(True)
    blend = Q.HERE / 'blend' / f'{key}_{Q.VER}.blend'; blend.parent.mkdir(parents=True, exist_ok=True)
    for img in bpy.data.images:
        if img.filepath_raw and img.filepath_raw.startswith(str(tdir)): img.filepath = img.filepath_raw
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), compress=True, relative_remap=True)
    bpy.ops.file.make_paths_relative(); bpy.ops.wm.save_mainfile(compress=True)
    # validation
    mn, mx = Q.bbox(nodes); dims = [round(mx[i] - mn[i], 4) for i in range(3)]
    tris = [sum(Q.tri_count(o) for o in nodes)] + [Q.tri_count(o) for o in lods]
    hs = [Q.mesh_health(o) for o in nodes]; health = {k: sum(h[k] for h in hs) for k in hs[0]}
    rt_tris, rmn, rmx, rmats = Q.glb_roundtrip(glb)
    v = {
        'asset': a['id'], 'key': key, 'state': st, 'version': Q.VER,
        'dimensions_m': dims, 'bbox_min': [round(x, 4) for x in mn], 'bbox_max': [round(x, 4) for x in mx],
        'target_size_m': a['size'], 'trianglesLOD': tris, 'budgetLOD0': a['budget'], 'withinBudget': tris[0] <= a['budget'],
        'vertices': sum(len(o.data.vertices) for o in nodes), 'materials': [m.name for m in G.data.materials], 'textureResolution': a['res'],
        'nodes': [o.name for o in nodes],
        'textures': sorted(p.name for p in tdir.glob(f'T_{key}_*.png') if p.stem[len(key) + 3:] in ('BaseColor', 'ORM', 'Normal', 'Emissive')),
        'originAtBase': abs(mn[2]) < 0.003, 'meshHealth': health,
        'glbRoundTrip': {'triangles': rt_tris, 'trianglesMatch': rt_tris == tris[0],
                         'bboxMatch': all(abs(a_ - b_) < 0.002 for a_, b_ in zip(rmn + rmx, mn + mx)), 'materials': rmats},
        'files': {p.name: {'bytes': p.stat().st_size, 'sha256': Q.sha(p)} for p in (glb, fbx)},
        'alphaClip': alpha, 'glbAlphaModes': (am := glb_alpha_modes(glb)),
        'alphaModeOk': am.get(gm.name) == ('MASK' if alpha else 'OPAQUE'), 'buildSeconds': round(time.time() - t0, 1),
        'notChecked': ['Unity import', 'in-game lighting', 'mobile performance', 'LOD screen-size thresholds'],
    }
    mi = dict(id=a['id'], name=a['name'], key=key, state=st, units='metre', forward='-Y (Blender) / +Z (glTF)', origin='base centre',
              dimensions_m=dims, triangles=tris[0], lod_triangles=tris, collision=a['collision'], **info, validation=v)
    (adir / f'{key}_model_info.json').write_text(json.dumps(mi, indent=1, ensure_ascii=False), encoding='utf-8')
    print(f'[{key}] tris {tris} dims {dims} health {health} roundtrip {rt_tris} {time.time() - t0:.0f}s', flush=True)
    if RENDER: previews(a, st, nodes)
    return v


def glb_alpha_modes(path):
    """alphaMode per material as written in the GLB JSON chunk (what engines will actually use)."""
    import struct
    b = path.read_bytes(); n = struct.unpack_from('<I', b, 12)[0]
    return {m.get('name', ''): m.get('alphaMode', 'OPAQUE') for m in json.loads(b[20:20 + n]).get('materials', [])}


def previews(a, st, nodes):
    G = nodes[0]
    out = Q.PREVIEWS / a['id'] / st
    Q.gpu(bpy.context.scene, 48); Q.studio('neutral')
    if QUICK:
        for nm, yaw, pitch, mg in (('q_front', 0, 8, 1.18), ('q_threequarter', 35, 16, 1.18), ('q_back', 160, 14, 1.18), ('q_close', 15, 10, 0.6)):
            Q.camera_fit(nodes, yaw, pitch, margin=mg); Q.render(out / f'{nm}.png', 900, 40)
        return
    for nm, yaw, pitch in Q.VIEWS:
        Q.camera_fit(nodes, yaw, pitch); Q.render(out / f'neutral_{nm}.png', 768, 40)
    for nm, yaw, pitch, mg in (('close_front', 0, 10, 0.62), ('close_side', 90, 12, 0.62)):
        Q.camera_fit(nodes, yaw, pitch, margin=mg); Q.render(out / f'{nm}.png', 1024, 64)
    # wireframe on a copy
    wm, nt, b = Q.new_mat('QA_Wire'); w = Q.N(nt, 'ShaderNodeWireframe', use_pixel_size=True); w.inputs['Size'].default_value = 1.0
    col = Q.mix(nt, w.outputs['Fac'], (0.72, 0.72, 0.70), (0.05, 0.05, 0.06)); Q.L(nt, col, b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.8
    keep = [list(o.data.materials) for o in nodes]   # swap slot contents in place: clear() would reset face material indices
    for o in nodes:
        for i in range(len(o.data.materials)): o.data.materials[i] = wm
    Q.camera_fit(nodes, 35, 18); Q.render(out / 'wireframe.png', 1024, 24)
    for o, ms in zip(nodes, keep):
        for i, m in enumerate(ms): o.data.materials[i] = m
    for o in list(bpy.data.objects):
        if o.name.startswith('QA_') and o.type in ('LIGHT', 'MESH'): bpy.data.objects.remove(o)
    Q.studio('stylized')
    for nm, yaw, pitch in (('01_front', 0, 8), ('02_three_quarter', 35, 16), ('03_right', 90, 8), ('05_back', 180, 8)):
        Q.camera_fit(nodes, yaw, pitch); Q.render(out / f'stylized_{nm}.png', 1024, 64)


report = {}
for aid in ids:
    a = A.ASSETS[aid]
    for st in a['states']:
        report[key_of(a, st)] = build_state(a, st)
    vdir = Q.EXPORTS / f"{a['id']}_{a['name']}" / Q.VER
    (vdir / 'validation.json').write_text(json.dumps({k: v for k, v in report.items() if k.startswith(aid)}, indent=1), encoding='utf-8')
print('DONE', ', '.join(report))
