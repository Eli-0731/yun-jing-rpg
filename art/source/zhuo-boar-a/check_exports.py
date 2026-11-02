"""Re-imports every GLB and FBX and checks them against the numbers and limits in model_info.json. Writes validation.json.

  blender -b --python-exit-code 1 --python art/source/zhuo-boar-a/check_exports.py
"""
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitlib as K

report, failures = {}, []


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def meshes():
    return {o.name: o for o in bpy.data.objects if o.type == 'MESH'}


def extent(objs):
    pts = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
    return [round(max(p[i] for p in pts) - min(p[i] for p in pts), 3) for i in range(3)], round(min(p[2] for p in pts), 4)


for key in ('BR01_ZhuoBoar', 'BR02_YoungPine_A', 'BR02_YoungPine_B'):
    folder = K.EXPORTS / key
    info = json.loads((folder / f'{key}_model_info.json').read_text(encoding='utf-8'))
    r = {}
    for kind in ('glb', 'fbx'):
        clear()
        path = folder / f'{key}_v001.{kind}'
        if kind == 'glb': bpy.ops.import_scene.gltf(filepath=str(path))
        else: bpy.ops.import_scene.fbx(filepath=str(path))
        m = meshes()
        lods = {f'LOD{i}': next((o for n, o in m.items() if n.split('.')[0] == (key if i == 0 else f'{key}_LOD{i}')), None) for i in range(3)}
        col = next((o for n, o in m.items() if 'Collision' in n), None)
        got = {k: K.tri_count(o) if o else None for k, o in lods.items()}
        r[kind] = {'tris': got, 'collision': bool(col), 'bytes': path.stat().st_size}
        for k, want in info['tris'].items():
            if got[k] != want: failures.append(f'{key} {kind} {k}: {got[k]} tris, model_info says {want}')
        if not col: failures.append(f'{key} {kind}: no _Collision mesh')
        if lods['LOD0'] is not None:
            size, low = extent([lods['LOD0']])
            r[kind]['sizeXYZ'] = size; r[kind]['lowest'] = low
            lim = info['limitM']
            if key.startswith('BR01'):
                ok = size[0] <= lim['width'] + .005 and size[1] <= lim['length'] + .005 and size[2] <= lim['height'] + .005
            else:
                ok = size[0] <= lim['width'] + .005 and size[1] <= lim['depth'] + .005 and size[2] <= lim['height'] + .005
            if kind == 'glb' and not ok: failures.append(f'{key}: size {size} over the limit {lim}')
            if abs(low) > .01: failures.append(f'{key} {kind}: lowest vertex at {low}')
        if key.startswith('BR01'):
            arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
            bones = [b.name for b in arm.data.bones]
            acts = sorted(a.name.split('|')[-1] for a in bpy.data.actions)
            r[kind]['bones'] = len(bones)
            r[kind]['actions'] = acts
            if len(bones) != info['skeleton']['count']: failures.append(f'{key} {kind}: {len(bones)} bones')
            if any(b.startswith('IK_') for b in bones): failures.append(f'{key} {kind}: authoring bones exported')
            for clip in ('Idle', 'Paw', 'Charge', 'Daze', 'Cleanse', 'Flee'):
                if not any(a.startswith(clip) for a in acts): failures.append(f'{key} {kind}: no clip {clip} ({acts})')
    report[key] = r
    # Health of the source meshes.
    clear()
    bpy.ops.wm.open_mainfile(filepath=str(K.HERE / 'blend' / f'{key}_v001.blend'))
    report[key]['health'] = {o.name: K.mesh_health(o) for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(key)}
    for name, h in report[key]['health'].items():
        if h['looseVerts']: failures.append(f'{name}: {h["looseVerts"]} loose vertices')

(K.EXPORTS / 'validation.json').write_text(json.dumps({'failures': failures, 'assets': report}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print('EXPORT_CHECK', 'PASS' if not failures else 'FAIL', json.dumps(failures, ensure_ascii=False), flush=True)
sys.exit(1 if failures else 0)
