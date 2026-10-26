"""Export one FBX per module (PHASE 6) and verify every FBX by re-importing it.

  blender -b --python-exit-code 1 --python 05_Scripts/export_fbx.py -- --file 01_Blender/road_edge_modules_v01.blend
  blender -b --python-exit-code 1 --python 05_Scripts/export_fbx.py -- --verify --name fbx_reimport_v01

Export: opens one kit file (never saved), moves each module root to the origin in memory, unhides its
LOD1/LOD2/COL and exports exactly that module's collection to 02_Exports/<Group>/<Module_ID>.fbx.  Settings
are the common Unity-friendly ones: Forward -Z, Up Y, Apply Scalings "FBX All", Apply Transform, linear vertex
colours (the Mask attribute is data, not colour), custom properties on.  Test objects (COL_TEST_Only) never go
into a module FBX; with --helpers they are exported on their own to 02_Exports/_TestHelpers/.  Module-space
facts for the re-import check go to 06_Reports/qa/fbx_export_<group>.json.

Verify: fresh session; imports each FBX alone and compares with the export record: object names, triangle
counts, bounds and every connector vertex (<= 1 mm), UVs, the Mask colour layer, material slot names and the
absence of TEST objects.  This is a Blender round trip only; it is not an engine (Unity/Unreal) import test.
Never overwrites.
"""
import sys, json, math, re
from pathlib import Path
import bpy
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit_spec as K
import kit_blender as KB

FBX_EXPORT = dict(use_selection=True, object_types={'EMPTY', 'MESH'}, global_scale=1.0, apply_unit_scale=True,
                  apply_scale_options='FBX_SCALE_ALL', bake_space_transform=True, axis_forward='-Z', axis_up='Y',
                  use_mesh_modifiers=True, mesh_smooth_type='FACE', colors_type='LINEAR', use_tspace=True,
                  use_custom_props=True, add_leaf_bones=False, bake_anim=False, path_mode='RELATIVE', embed_textures=False)


def cli():
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    def get(k, d=None): return a[a.index(k) + 1] if k in a else d
    return get('--file'), '--verify' in a, get('--name', 'fbx_reimport'), '--helpers' in a


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def world_bounds(objs):
    pts = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
    return [min(p[i] for p in pts) for i in range(3)], [max(p[i] for p in pts) for i in range(3)]


def select_only(objs):
    for o in bpy.context.view_layer.objects: o.select_set(False)
    for o in objs:
        o.hide_set(False); o.hide_viewport = False; o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]


def export_file(path, helpers):
    KB.start_session()
    KB.open_kit_file(KB.kit_path(path))
    kit = bpy.data.collections['KIT_Modules']; records = {}; group = None
    for coll in kit.children:
        mod = K.BY_ID.get(coll.name)
        if not mod: continue
        group = mod['group']
        root = next(o for o in coll.objects if o.type == 'EMPTY' and o.name == mod['id'])
        root.location = (0.0, 0.0, 0.0)                     # in memory only: the kit file is never saved
        objs = [root] + sorted((o for o in coll.objects if o is not root), key=lambda o: o.name)
        assert all(not o.name.startswith('TEST_') for o in objs)
        select_only(objs); bpy.context.view_layer.update()
        rel = '02_Exports/%s/%s.fbx' % (K.GROUP_EXPORT_DIR[mod['group']], mod['id'])
        out = KB.new_output(rel)
        bpy.ops.export_scene.fbx(filepath=str(out), **FBX_EXPORT)
        meshes = [o for o in objs if o.type == 'MESH']
        lo, hi = world_bounds(meshes)
        terrain = next((o for o in meshes if o.name.endswith('_Terrain_LOD0')), None)
        records[mod['id']] = {
            'code': mod['code'], 'fbx': rel, 'bytes': out.stat().st_size,
            'objects': {o.name: {'type': o.type, 'tris': tris(o) if o.type == 'MESH' else 0,
                                 'materials': [s.material.name for s in o.material_slots if s.material] if o.type == 'MESH' else []} for o in objs},
            'bounds_min': lo, 'bounds_max': hi,
            'connector_vertices': [list(p) for c in K.connectors(mod) for p in c['vertices']] if terrain else [],
            'terrain': terrain.name if terrain else None}
        print('EXPORTED', mod['code'], rel, records[mod['id']]['bytes'], flush=True)
    rec_path = KB.new_output('06_Reports/qa/fbx_export_%s.json' % K.GROUP_FILES[group])
    rec_path.write_text(json.dumps({'source': path, 'blender': bpy.app.version_string, 'settings': {k: (sorted(v) if isinstance(v, set) else v) for k, v in FBX_EXPORT.items()},
                                    'modules': records}, indent=2))
    if helpers:   # placement helpers for engine-side tests, moved (in memory) into the module frames
        test = bpy.data.collections['COL_TEST_Only']
        for o in test.objects:
            rel = '02_Exports/_TestHelpers/%s.fbx' % o.name
            if KB.kit_path(rel).exists():
                print('SKIP helper (already exported)', o.name, flush=True); continue
            lo, _ = world_bounds([o])
            shift = {'TEST_RoadCore_3m': (-lo[0], -(lo[1] + K.ROAD_HALF)), 'TEST_BridgeDeck_3m': (K.RAMP_L - lo[0], -(lo[1] + K.DECK_HALF))}.get(o.name, (0.0, 0.0))
            o.data.transform(Matrix.Translation((shift[0], shift[1], 0.0)))
            select_only([o])
            bpy.ops.export_scene.fbx(filepath=str(KB.new_output(rel)), **FBX_EXPORT)
            print('EXPORTED helper', o.name, flush=True)
    print('DONE export', len(records), flush=True)


def base_name(n):
    return re.sub(r'\.\d{3}$', '', n)


def verify(name):
    KB.start_session()
    out_json = KB.new_output('06_Reports/qa/%s.json' % name)
    results = {}; all_ok = True
    for grp in ('road_edge_modules', 'riverbank_modules', 'bridgehead_modules'):
        rec = json.loads(KB.kit_path('06_Reports/qa/fbx_export_%s.json' % grp).read_text())
        for mid, r in rec['modules'].items():
            before = set(bpy.data.objects)
            bpy.ops.import_scene.fbx(filepath=str(KB.kit_path(r['fbx'])), use_custom_normals=True)
            new = [o for o in bpy.data.objects if o not in before]
            names = {base_name(o.name): o for o in new}
            issues = []
            missing = sorted(set(r['objects']) - set(names)); extra = sorted(set(names) - set(r['objects']))
            if missing: issues.append('missing objects: %s' % missing)
            if extra: issues.append('unexpected objects: %s' % extra)
            if any(n.startswith('TEST_') for n in names): issues.append('TEST object inside module FBX')
            tri_diff = {n: (r['objects'][n]['tris'], tris(o)) for n, o in names.items() if o.type == 'MESH' and n in r['objects'] and tris(o) != r['objects'][n]['tris']}
            if tri_diff: issues.append('triangle count changed: %s' % tri_diff)
            meshes = [o for o in new if o.type == 'MESH']
            lo, hi = world_bounds(meshes)
            bound_err = max(max(abs(a - b) for a, b in zip(lo, r['bounds_min'])), max(abs(a - b) for a, b in zip(hi, r['bounds_max'])))
            if bound_err > K.TOL: issues.append('bounds differ by %.4f m' % bound_err)
            con_err = 0.0
            if r['terrain']:
                t = names.get(r['terrain'])
                if t is None: issues.append('terrain missing')
                else:
                    pts = [t.matrix_world @ v.co for v in t.data.vertices]; kd = KDTree(len(pts))
                    for i, p in enumerate(pts): kd.insert(p, i)
                    kd.balance()
                    con_err = max(kd.find(Vector(p))[2] for p in r['connector_vertices'])
                    if con_err > K.TOL: issues.append('connector vertices moved by %.4f m' % con_err)
                    if 'Mask' not in t.data.color_attributes: issues.append('Mask colour layer missing (have %s)' % [c.name for c in t.data.color_attributes])
            no_uv = [base_name(o.name) for o in meshes if not o.data.uv_layers]
            if no_uv: issues.append('no UVs: %s' % no_uv)
            mat_diff = {}
            for n, o in names.items():
                if o.type != 'MESH' or n not in r['objects']: continue
                got = [base_name(s.material.name) for s in o.material_slots if s.material]
                if got != r['objects'][n]['materials']: mat_diff[n] = (r['objects'][n]['materials'], got)
            if mat_diff: issues.append('material slots differ: %s' % mat_diff)
            ok = not issues; all_ok &= ok
            results[mid] = {'code': r['code'], 'fbx': r['fbx'], 'objects': len(names), 'max_bounds_error_m': bound_err,
                            'max_connector_vertex_error_m': con_err, 'issues': issues, 'pass': ok}
            print('REIMPORT', r['code'], 'PASS' if ok else 'FAIL', '%.6f %.6f' % (bound_err, con_err), issues[:2], flush=True)
            for o in new: bpy.data.objects.remove(o, do_unlink=True)
            for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.images):
                for d in list(coll):
                    if d.users == 0: coll.remove(d)
    out_json.write_text(json.dumps({'name': name, 'blender': bpy.app.version_string, 'scope': 'Blender FBX round trip (not an engine import)',
                                    'tolerance_m': K.TOL, 'pass': all_ok, 'modules': results}, indent=2))
    print('RESULT', 'PASS' if all_ok else 'FAIL', out_json, flush=True)


def main():
    path, do_verify, name, helpers = cli()
    if do_verify: verify(name)
    else: export_file(path, helpers)


if __name__ == '__main__':
    main()
