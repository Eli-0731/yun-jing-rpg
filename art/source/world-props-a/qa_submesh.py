"""Asset QA for exported world props whose LOD0 is above the QA's 300k-triangle scan limit (Johnnnny0823, 11/05 review round).
qa_check skips its z-fighting and floating scans above max_tris, so an empty list there is not a pass. This runs the same
blender-asset-qa qa_check (game profile, same eps/tol) once per LOD0 sub-mesh, with max_tris raised to that sub-mesh's own
count so every scan runs, and writes one row per sub-mesh. Cross-sub-mesh contact (pieces of one group resting on another) is
covered by qa_locate-style whole-item scans in the review notes.
blender -b --factory-startup -P qa_submesh.py -- <out.json> <ID> [<ID> ...]
"""
import bpy, sys, os, json, time
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'exports', 'world-props-a')
QA = os.path.expanduser(r'~/.claude/skills/blender-asset-qa/scripts')
sys.path.insert(0, QA); import qa_check
a = sys.argv[sys.argv.index('--') + 1:]; out = a[0]; ids = a[1:]
res = json.load(open(out, encoding='utf-8')) if os.path.exists(out) else {}
for k in ids:
    if os.environ.get('WA_GEOM'):   # geometry-only build of build_world_a.py (no bake/export): its joined LOD0 groups
        bpy.ops.wm.open_mainfile(filepath=os.path.join(os.environ['WA_GEOM'], k + '_geom.blend'))
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.fbx(filepath=os.path.join(R, k + '.fbx'))
    for o in bpy.data.objects: o.select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects[0]
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    rows = {}
    for ob in sorted((o for o in bpy.data.objects if o.type == 'MESH' and o.name.endswith('_LOD0')), key=lambda o: o.name):
        n = sum(len(p.vertices) - 2 for p in ob.data.polygons); t0 = time.time()
        r = qa_check.run(objects=[ob.name], profile='game', max_tris=max(300000, n + 1))
        rows[ob.name] = {'tris': n, 'errors': r['errors'], 'warnings': r['warnings'], 'sec': round(time.time() - t0, 1),
                         'skipped': any('max_tris' in w for w in r['warnings'])}
        print('SUB', k, ob.name, n, len(r['errors']), rows[ob.name]['sec'], flush=True)
    res[k] = rows
    json.dump(res, open(out, 'w', encoding='utf-8'), indent=1)
print('SUBMESH_DONE')
