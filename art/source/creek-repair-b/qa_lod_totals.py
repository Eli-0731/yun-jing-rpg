"""LOD triangle totals counted from a fresh import of each final FBX, against the lod_totals in model_info.json.

blender --background --factory-startup --python qa_lod_totals.py
Writes art/references/creek-repair-b-lod-totals.json. Objects ending _LOD1/_LOD2 count for that level; any other mesh except _Collision counts as LOD0
(F01_Field names its LOD0 pieces F01, F01_weir, F01_weir_wheel). Water FBX files are not counted.
"""
import bpy, json, os, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]; X = ROOT / 'art' / 'exports' / 'creek-repair-b'
out, bad = {}, 0
for a in sorted(os.listdir(X)):
    d = X / a; f = d / f'{a}_v001.fbx'
    if not f.exists(): f = d / f'{a}.fbx'
    if not f.exists() or not (d / 'model_info.json').exists(): continue
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(f))
    t = {'LOD0': 0, 'LOD1': 0, 'LOD2': 0}
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.name.endswith('_Collision'): continue
        m = re.search(r'_LOD(\d)$', o.name.split('.')[0]); k = f'LOD{m.group(1)}' if m else 'LOD0'
        o.data.calc_loop_triangles(); t[k] += len(o.data.loop_triangles)
    info = json.loads((d / 'model_info.json').read_text(encoding='utf-8')).get('lod_totals') or {}
    same = all(t[k] == info.get(k) for k in t); bad += not same
    out[a] = {'fbx_reimport': t, 'model_info': info, 'match': same}
    print('LOD_TOTALS', a, t, info, 'OK' if same else 'MISMATCH', flush=True)
(ROOT / 'art' / 'references' / 'creek-repair-b-lod-totals.json').write_text(json.dumps({'tool': 'Blender FBX import, loop triangles', 'mismatches': bad, 'assets': out}, indent=1), encoding='utf-8')
print('LOD_TOTALS_DONE mismatches', bad)
