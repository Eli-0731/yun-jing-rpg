"""Reimports every delivered FBX and writes the numbers the handover asks for: LOD triangles, size against model_info, origin,
collision, Detail objects against detailObjects, plus the error total from qa_report.json. art/references/creek-repair-b-handoff.json

blender --background --factory-startup --python art/source/creek-repair-b/qa_handoff.py
"""
import bpy, json
from pathlib import Path
from mathutils import Vector

ART = Path(__file__).resolve().parents[2]
X = ART / 'exports/creek-repair-b'
out = {}
for d in sorted(p for p in X.iterdir() if p.is_dir()):
    aid = d.name; fbx = sorted(f for f in d.glob('*.fbx') if '_water' not in f.name)[0]
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=str(fbx))
    info = json.loads((d / 'model_info.json').read_text(encoding='utf-8')); qa = json.loads((d / 'qa_report.json').read_text(encoding='utf-8'))
    lods = {'LOD0': 0, 'LOD1': 0, 'LOD2': 0}; lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3); col = 0; details = set()
    for o in bpy.data.objects:
        if o.type != 'MESH': continue
        me = o.data; me.calc_loop_triangles(); n = len(me.loop_triangles); name = o.name.split('.')[0]
        if name.endswith('_Collision'): col = n; continue
        k = 'LOD0' if name in ('F01', 'F01_weir', 'F01_weir_wheel') else name[-4:]
        if k in lods: lods[k] += n
        if 'Detail_' in name and k == 'LOD0': details.add(name[name.index('Detail_'):-5])
        if k == 'LOD0':
            for v in me.vertices:
                c = o.matrix_world @ v.co
                lo = Vector(map(min, lo, c)); hi = Vector(map(max, hi, c))
    size = hi - lo
    if aid == 'F01_Field':   # cut_field_gap.py writes only a short model_info, and its validation measures the field without the weir
        info.update(lod_totals=lods, dimensions_m=[round(x, 4) for x in size], collision_faces=col)
        (d / 'model_info.json').write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding='utf-8')
    stated = info.get('dimensions_m')
    errors = sum(v.get('degenerate', 0) + v.get('inverted_closed', 0) + v.get('black_faces', 0) for v in qa.values() if isinstance(v, dict))
    wanted = {str(x).replace(aid + '_', '') for x in info.get('detailObjects', [])}
    out[aid] = {'fbx': fbx.name, 'lod_tris': lods, 'reimport_size_m': [round(x, 4) for x in size], 'model_info_size_m': stated,
                'size_error_m': round(max(abs(a - b) for a, b in zip(size, stated)), 4) if stated else None,
                'origin_offset_m': [round((lo.x + hi.x) / 2, 4), round((lo.y + hi.y) / 2, 4)], 'bottom_z_m': round(lo.z, 4), 'collision_tris': col,
                'minTier': info.get('minTier'), 'detail_in_fbx': sorted(details), 'detailObjects': info.get('detailObjects', []),
                'detail_match': details == {w[:-5] if w.endswith('_LOD0') else w for w in wanted}, 'qa_errors': errors}
    print('HANDOFF', aid, flush=True)
(ART / 'references/creek-repair-b-handoff.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
