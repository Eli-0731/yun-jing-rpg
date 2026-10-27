"""Hand-off check of a packaged copy of this kit (writes handoff_check.json in the package root).

  blender -b --python-exit-code 1 --python <pkg>/05_Scripts/check_incoming.py -- --pkg <pkg>

Run it on the copy made by make_incoming_package.py, at its final location.  It (1) re-imports every FBX under
02_Exports/ and compares object names and sizes with the export records (06_Reports/qa/fbx_export_*.json, or
model_info.json for the bridges), and (2) re-opens every .blend in the package (01_Blender/ and the assembly-test
and showcase scenes that link it) and lists objects, triangles, materials, every image and linked library with
whether its file is found from this location (relative paths intact).  Nothing is
saved.  Only facts measured here go into the report.
"""
import sys, json, re
from pathlib import Path
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit_blender as KB
import export_fbx as EX


def tris(o): return sum(len(p.vertices) - 2 for p in o.data.polygons)


def expected_sizes(pkg):
    out = {}
    for f in (pkg / '06_Reports' / 'qa').glob('fbx_export_*.json'):
        for mid, r in json.loads(f.read_text())['modules'].items():
            out[r['fbx']] = ([b - a for a, b in zip(r['bounds_min'], r['bounds_max'])], sorted(r['objects']))
    for mi in (pkg / '04_Previews' / 'Individual').glob('D0*/model_info.json'):
        m = json.loads(mi.read_text())
        out[m['files']['fbx']] = ([b - a for a, b in zip(m['bounds_min_m'], m['bounds_max_m'])], None)
    return out


def main():
    a = sys.argv[sys.argv.index('--') + 1:]
    pkg = Path(a[a.index('--pkg') + 1]).resolve()
    KB.start_session(); report = {'blender': bpy.app.version_string, 'package': str(pkg), 'fbx': [], 'blend': []}
    exp = expected_sizes(pkg)
    for fbx in sorted((pkg / '02_Exports').rglob('*.fbx')):
        rel = str(fbx.relative_to(pkg)); before = set(bpy.data.objects)
        bpy.ops.import_scene.fbx(filepath=str(fbx)); new = [o for o in bpy.data.objects if o not in before]
        meshes = [o for o in new if o.type == 'MESH']
        rec = {'file': rel, 'objects': len(new), 'mesh_objects': len(meshes), 'triangles': sum(tris(o) for o in meshes)}
        if meshes:
            lo, hi = EX.world_bounds(meshes); size = [b - a for a, b in zip(lo, hi)]; rec['size_m'] = size
            if rel in exp:
                want, names = exp[rel]
                if 'LOD0' in ''.join(o.name for o in meshes) or names is None:
                    rec['size_error_m'] = max(abs(x - y) for x, y in zip(size, want))
                if names: rec['names_match'] = sorted(re.sub(r'\.\d{3}$', '', o.name) for o in new) == names
        report['fbx'].append(rec)
        for o in new: bpy.data.objects.remove(o, do_unlink=True)
        for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.images):
            for d in list(coll):
                if d.users == 0: coll.remove(d)
        print('FBX', rel, rec.get('size_error_m'), flush=True)
    for blend in sorted(pkg.rglob('*.blend')):                     # 01_Blender plus the assembly-test and showcase scenes (they link 01_Blender)
        bpy.ops.wm.open_mainfile(filepath=str(blend))              # read-only: never saved
        meshes = [o for o in bpy.data.objects if o.type == 'MESH']
        imgs = [{'name': i.name, 'path': i.filepath, 'found': Path(bpy.path.abspath(i.filepath, library=i.library)).exists()}
                for i in bpy.data.images if i.filepath]
        libs = [{'path': l.filepath, 'found': Path(bpy.path.abspath(l.filepath)).exists()} for l in bpy.data.libraries]
        report['blend'].append({'file': str(blend.relative_to(pkg)), 'opened': True, 'objects': len(bpy.data.objects), 'mesh_objects': len(meshes),
                                'triangles_all_objects': sum(tris(o) for o in meshes), 'materials': len(bpy.data.materials),
                                'images': len(imgs), 'images_missing': [i['path'] for i in imgs if not i['found']],
                                'libraries': [l['path'] for l in libs], 'libraries_missing': [l['path'] for l in libs if not l['found']],
                                'scene_unit_scale': bpy.context.scene.unit_settings.scale_length})
        print('BLEND', blend.relative_to(pkg), len(imgs), 'missing', len(report['blend'][-1]['images_missing']), 'libs', len(libs),
              'missing', len(report['blend'][-1]['libraries_missing']), flush=True)
    errs = [r['size_error_m'] for r in report['fbx'] if 'size_error_m' in r]
    report['summary'] = {'fbx_files': len(report['fbx']), 'fbx_max_size_error_m': max(errs) if errs else None,
                         'fbx_name_mismatches': [r['file'] for r in report['fbx'] if r.get('names_match') is False],
                         'blend_files': len(report['blend']), 'blend_missing_images': sum(len(b['images_missing']) for b in report['blend']),
                         'blend_missing_libraries': sum(len(b['libraries_missing']) for b in report['blend']),
                         'not_done': ['Unity import', 'URP materials', 'mobile performance', 'in-engine collision and walking']}
    (pkg / 'handoff_check.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print('SUMMARY', json.dumps(report['summary']), flush=True)


if __name__ == '__main__':
    main()
