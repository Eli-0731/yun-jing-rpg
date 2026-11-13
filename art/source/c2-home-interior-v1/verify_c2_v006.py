"""核對 C2 後門前後位置、尺寸及兩件新 FBX 的可回匯性。"""
import bpy
from pathlib import Path

root = Path(__file__).resolve().parents[3]
source = root / 'art/source/c2-home-interior-v1'
export = root / 'art/exports/c2-home-interior-v1/v006'


def rear():
    out = {}
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        name = obj.name
        if name.startswith(('Rear_Door_Threshold', 'Rear_Door_Outer_Jamb',
                            'RearDoor_SM_IK_door_threshold_LOD0', 'RearDoor_SM_IK_door_jamb_')):
            out[name] = (tuple(round(v, 5) for v in obj.matrix_world.translation),
                         tuple(round(v, 5) for v in obj.dimensions))
    return out


for old, new, label in [
    ('StarterHouse_reardoor_v005.blend', 'StarterHouse_reardoor_v006.blend', '外屋'),
    ('lodging-room-reardoor-v030.blend', 'lodging-room-reardoor-v031.blend', '室內'),
]:
    bpy.ops.wm.open_mainfile(filepath=str(source / old))
    prior = rear()
    bpy.ops.wm.open_mainfile(filepath=str(source / new))
    current = rear()
    assert prior and current == prior, (label, prior, current)
    print('後門對位通過', label, len(prior), flush=True)

for filename in ('StarterHouse_reardoor_v006.fbx', 'lodging-room-reardoor-v031.fbx'):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(export / filename))
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    count = sum(sum(len(poly.vertices) - 2 for poly in o.data.polygons) for o in meshes)
    assert meshes and count > 0, filename
    print('FBX 回匯通過', filename, '網格', len(meshes), '三角面', count, flush=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(export / 'StarterHouse_reardoor_v006.glb'))
assert sum(o.type == 'MESH' for o in bpy.data.objects) > 0
print('GLB 回匯通過', flush=True)
