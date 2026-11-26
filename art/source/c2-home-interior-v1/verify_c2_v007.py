"""核對 C2 v007 只換材質、後門定位與兩件 FBX 可回匯。"""
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / 'art/source/c2-home-interior-v1'
OUT = ROOT / 'art/exports/c2-home-interior-v1/v007'


def signature():
    prefixes = ('Rear_Door_Threshold', 'Rear_Door_Outer_Jamb',
                'RearDoor_SM_IK_door_threshold_LOD0', 'RearDoor_SM_IK_door_jamb_')
    meshes = {o.name: (len(o.data.vertices), len(o.data.polygons),
                       tuple(round(v, 5) for v in o.dimensions))
              for o in bpy.data.objects if o.type == 'MESH'}
    rear = {o.name: (tuple(round(v, 5) for v in o.matrix_world.translation),
                     tuple(round(v, 5) for v in o.dimensions))
            for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(prefixes)}
    return meshes, rear


for old, new in (('StarterHouse_reardoor_v006.blend', 'StarterHouse_reardoor_v007.blend'),
                 ('lodging-room-reardoor-v031.blend', 'lodging-room-reardoor-v032.blend')):
    bpy.ops.wm.open_mainfile(filepath=str(SRC / old))
    before = signature()
    bpy.ops.wm.open_mainfile(filepath=str(SRC / new))
    assert signature() == before, new
    print('幾何與後門未變', new, len(before[0]), flush=True)

for name in ('StarterHouse_reardoor_v007.fbx', 'lodging-room-reardoor-v032.fbx'):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(OUT / name))
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    tris = sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes)
    assert tris > 0
    print('FBX 回匯', name, '網格', len(meshes), '三角面', tris, flush=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(OUT / 'StarterHouse_reardoor_v007.glb'))
assert any(o.type == 'MESH' for o in bpy.data.objects)
print('GLB 回匯通過', flush=True)
