"""Blender asset QA (blender-asset-qa qa_check, game profile) on every exported MC01 LOD0 object, one row per sub-mesh,
max_tris raised to the object's own count so the z-fighting / floating scans always run (an empty list from a skipped
scan is not a pass). Also checks the 4 m grid footprint of the FBX re-import (<= 2 cm).

    blender -b --factory-startup -P qa_mc01.py -- <out.json> SB01 SF01 RF01
"""
import bpy, sys, os, json, time
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__)); EXP = os.path.join(HERE, '..', '..', 'exports', 'mountain-street-houses-a')
sys.path.insert(0, os.path.expanduser(r'~/.claude/skills/blender-asset-qa/scripts')); import qa_check
a = sys.argv[sys.argv.index('--') + 1:]; out = a[0]; ids = a[1:]
res = {}
for k in ids:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=os.path.join(EXP, f'MC01_{k}.fbx'))
    for o in bpy.data.objects: o.select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    info = json.load(open(os.path.join(EXP, f'MC01_{k}.model_info.json'), encoding='utf-8'))
    mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
    rows = {}
    for ob in sorted((o for o in bpy.data.objects if o.type == 'MESH' and o.name.endswith('_LOD0')), key=lambda o: o.name):
        for v in ob.data.vertices: mn = Vector(map(min, mn, v.co)); mx = Vector(map(max, mx, v.co))
        n = sum(len(p.vertices) - 2 for p in ob.data.polygons); t0 = time.time()
        r = qa_check.run(objects=[ob.name], profile='game', max_tris=max(300000, n + 1))
        rows[ob.name] = {'tris': n, 'errors': r['errors'], 'warnings': r['warnings'], 'sec': round(time.time() - t0, 1)}
        print('QA', k, ob.name, n, 'errors', len(r['errors']), 'warnings', len(r['warnings']), flush=True)
    # detail meshes that only make sense attached to another group: QA them joined (Glow paper on its caps, moss on the stone)
    glow_host = 'Detail_Lanterns_LOD0' if 'Detail_Lanterns_LOD0' in bpy.data.objects else f'MC01_{k}_LOD0'
    for a_, b_ in (('Glow_LOD0', glow_host), ('Detail_Moss_LOD0', f'MC01_{k}_LOD0')):
        if a_ in bpy.data.objects and b_ in bpy.data.objects:
            ca = bpy.data.objects[a_].copy(); ca.data = ca.data.copy(); cb = bpy.data.objects[b_].copy(); cb.data = cb.data.copy()
            for c in (ca, cb): bpy.context.scene.collection.objects.link(c)
            bpy.ops.object.select_all(action='DESELECT'); ca.select_set(True); cb.select_set(True); bpy.context.view_layer.objects.active = cb
            bpy.ops.object.join(); cb.name = f'JOINED_{a_}+{b_}'; n = sum(len(p.vertices) - 2 for p in cb.data.polygons)
            r = qa_check.run(objects=[cb.name], profile='game', max_tris=max(300000, n + 1))
            fl = [e for e in r['errors'] if 'floating' in e]
            rows[cb.name] = {'tris': n, 'floating_errors': fl, 'note': 'joined check: floating only'}
            print('QA', k, cb.name, 'floating', len(fl), flush=True)
            bpy.data.objects.remove(cb)
    dims = [round(d, 3) for d in (mx - mn)]
    err = [max(abs(d - e) for d, e in zip(dims, info['dimensions_m']))]
    res[k] = {'objects': rows, 'reimport_dims': dims, 'built_dims': info['dimensions_m'], 'reimport_error_m': round(err[0], 4)}
    print('DIMS', k, dims, 'vs', info['dimensions_m'], flush=True)
json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
