"""Check both new source files and FBX roundtrips without Unity claims."""
from pathlib import Path
import bpy

root=Path(__file__).resolve().parents[2]
src=root/'art/source/c2-home-interior-v1'
exports=root/'art/exports/c2-home-interior-v1'

bpy.ops.wm.open_mainfile(filepath=str(src/'StarterHouse_reardoor_v005.blend'))
names={o.name for o in bpy.data.objects}
assert not any(n.startswith('Rear_Window_0_') for n in names)
assert sum(n.startswith('Rear_Door_-1_') or n.startswith('Rear_Door_1_') for n in names)>=20
assert 'Rear_Door_Threshold' in names
print('C2_EXTERIOR_SOURCE_PASS',len(names))

bpy.ops.wm.open_mainfile(filepath=str(src/'lodging-room-reardoor-v030.blend'))
room=bpy.data.collections['IK_LodgingRoom_Blockout']
placed={o.name for o in room.objects if o.name.startswith('C2_Placed_TI')}
assert len({n.split('_')[2] for n in placed})==11,len(placed)
assert any(o.name.startswith('RearDoor_SM_IK_door_header') for o in room.objects)
print('C2_INTERIOR_SOURCE_PASS',len(placed),'placed meshes')

for filename in ('StarterHouse_reardoor_v005.fbx','lodging-room-reardoor-v030.fbx'):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(exports/filename))
    meshes=[o for o in bpy.data.objects if o.type=='MESH']
    assert len(meshes)>100,(filename,len(meshes))
    tris=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes)
    assert tris>1000,(filename,tris)
    print('C2_FBX_REIMPORT_PASS',filename,len(meshes),'meshes',tris,'tris')
