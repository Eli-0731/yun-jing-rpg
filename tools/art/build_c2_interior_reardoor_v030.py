"""Replace the v029 lodging room north center wall with a 1.2 m rear door."""
from pathlib import Path
import bpy
from mathutils import Vector, Matrix
from math import radians

root=Path(__file__).resolve().parents[2]
old=root/'art/source/c2-home-interior-v1/lodging-interior-kit-dimensions-v028.blend'
out=root/'art/source/c2-home-interior-v1/lodging-room-reardoor-v030.blend'
preview=root/'art/previews/c2-home-interior-v1/interior-reardoor-v030.png'
out.parent.mkdir(parents=True,exist_ok=True);preview.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(old))
textures=root/'art/textures/c2-home-interior-v1'
for img in bpy.data.images:
    candidate=textures/Path(img.filepath).name
    if candidate.is_file():
        img.filepath=str(candidate)
        img.reload()
room=bpy.data.collections['IK_LodgingRoom_Blockout']
door=bpy.data.collections['IK05_DoorWall3']

# Two 1 m / 2 m modules straddled the rear centerline; their solid plaster
# cannot coexist with a door. The existing 2 m panels on either side remain.
for ob in list(room.objects):
    p=ob.matrix_world.translation
    if ob.type=='MESH' and p.y>2.25 and -1.5<p.x<1.5 and \
            ob.name.startswith(('SM_IK_plain1_','SM_IK_brace_')):
        bpy.data.objects.remove(ob,do_unlink=True)

def resize(obj,x=None,z=None,width=None,height=None):
    if x is not None:obj.location.x=x
    if z is not None:obj.location.z=z
    if width is not None:obj.dimensions.x=width
    if height is not None:obj.dimensions.z=height

new=[]
for source in door.objects:
    if source.type!='MESH':continue
    ob=source.copy();ob.data=source.data.copy();room.objects.link(ob)
    ob.parent=None;ob.matrix_world=source.matrix_world.copy()
    ob.location.y=2.5
    ob.name='RearDoor_'+source.name
    n=source.name
    if 'pier_-1' in n:resize(ob,x=-1.05,width=.9)
    elif 'pier_1' in n:resize(ob,x=1.05,width=.9)
    elif 'header' in n:resize(ob,z=2.7,width=1.2,height=1.0)
    elif 'lintel' in n:resize(ob,z=2.23,width=1.44)
    elif 'jamb_-1' in n:resize(ob,x=-.67,z=1.1,height=2.2)
    elif 'jamb_1' in n:resize(ob,x=.67,z=1.1,height=2.2)
    elif 'threshold' in n:resize(ob,width=1.2)
    elif 'stone_base' in n or 'rail_base' in n:
        bpy.data.objects.remove(ob,do_unlink=True);continue
    new.append(ob)

# Keep the lower stone/wood band on either side, leaving a clear 1.2 m walk.
for source in door.objects:
    if source.type!='MESH' or not any(k in source.name for k in ('stone_base','rail_base')):continue
    for side in (-1,1):
        ob=source.copy();ob.data=source.data.copy();room.objects.link(ob)
        ob.parent=None;ob.matrix_world=source.matrix_world.copy()
        ob.location.x=side*1.05;ob.location.y=2.5;ob.dimensions.x=.9
        ob.name=f'RearDoor_{source.name}_{side}'
        new.append(ob)

# Duplicate the already authored pair of front door leaves; fit the narrower
# opening while retaining their hand-painted material and lattice detail.
front=[o for o in room.objects if o.type=='MESH' and ('door' in o.name.lower())
       and o.matrix_world.translation.y < -2.2]
for source in front:
    if 'RearDoor_' in source.name:continue
    ob=source.copy();ob.data=source.data.copy();room.objects.link(ob)
    ob.parent=None;ob.matrix_world=source.matrix_world.copy()
    ob.location.x=-source.matrix_world.translation.x*(1.2/1.7)
    ob.location.y=2.5+(source.matrix_world.translation.y+2.5)
    ob.location.z=source.matrix_world.translation.z*(2.2/2.4)
    ob.rotation_euler.z += 3.141592653589793
    ob.scale.x *= 1.2/1.7;ob.scale.z *= 2.2/2.4
    ob.name='RearDoor_Leaf_'+source.name
    new.append(ob)

# Stage one placement of the collaborator B interior series. These are
# existing assets, not remodeled parts; their authored files stay unchanged.
library=root/'art/source/territory-interior-b/blend'
placements={
    'TI01_BoguShelf':((2.95,.65,0),90),
    'TI02_HomeFurnace':((2.55,-.55,0),-90),
    'TI03_JournalDesk':((1.8,-1.65,0),0),
    'TI04_PaperLamp':((2.45,-1.60,0),0),
    'TI05_LandscapeScreen':((-1.85,-1.35,0),0),
    'TI06_WovenMat':((.45,.75,0),0),
    'TI07_LinenCurtain':((3.34,.0,0),90),
    'TI08a_KeepsakeBox':((2.95,.65,1.10),0),
    'TI08b_PaperScroll':((1.85,-1.62,.85),0),
    'TI08c_CeladonJar':((2.95,.65,1.55),0),
    'TI08d_MedicinePot':((2.95,.65,.55),0),
}
for asset,(target,angle) in placements.items():
    blend=library/f'{asset}_v002.blend'
    with bpy.data.libraries.load(str(blend),link=False) as (src,dst):
        dst.objects=[n for n in src.objects if 'LOD0' in n and 'UCX' not in n]
    imported=[o for o in dst.objects if o and o.type=='MESH']
    for ob in imported:room.objects.link(ob)
    if not imported:raise RuntimeError(f'No LOD0 mesh in {blend}')
    bounds=[ob.matrix_world @ Vector(corner) for ob in imported for corner in ob.bound_box]
    centre=Vector(((min(v.x for v in bounds)+max(v.x for v in bounds))/2,
                   (min(v.y for v in bounds)+max(v.y for v in bounds))/2,
                   min(v.z for v in bounds)))
    transform=Matrix.Translation(Vector(target)) @ Matrix.Rotation(radians(angle),4,'Z') @ Matrix.Translation(-centre)
    for ob in imported:
        world=ob.matrix_world.copy();ob.parent=None;ob.matrix_world=transform @ world
        ob.name='C2_Placed_'+asset+'_'+ob.name

# Relink the appended furniture images to the committed texture library.
lookup={p.name:p for p in (root/'art/exports/territory-interior-b').glob('*/Textures/*.png')}
for img in bpy.data.images:
    candidate=lookup.get(Path(img.filepath).name)
    if candidate and candidate.stat().st_size>200:
        img.filepath=str(candidate);img.reload()

bpy.ops.wm.save_as_mainfile(filepath=str(out))
export=root/'art/exports/c2-home-interior-v1'
export.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='DESELECT')
for ob in room.objects:
    if ob.type=='MESH':ob.select_set(True)
bpy.ops.export_scene.fbx(filepath=str(export/'lodging-room-reardoor-v030.fbx'),use_selection=True)
bpy.ops.export_scene.gltf(filepath=str(export/'lodging-room-reardoor-v030.glb'),
                          export_format='GLB',use_selection=True)

# A neutral eye-level review of the north wall, from inside the room.
for ob in bpy.data.objects:
    if ob.type=='MESH':ob.hide_render=(ob.name not in {x.name for x in room.objects})
cam_data=bpy.data.cameras.new('RearDoorReviewCamera')
cam=bpy.data.objects.new('RearDoorReviewCamera',cam_data);room.objects.link(cam)
cam.location=(0,-1.5,1.6)
cam.rotation_euler=(Vector((0,2.5,1.6))-cam.location).to_track_quat('-Z','Y').to_euler()
cam_data.lens=26;bpy.context.scene.camera=cam
world=bpy.data.worlds.new('RoomReviewSky');world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.82,.84,.86,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.8
bpy.context.scene.world=world
light_data=bpy.data.lights.new('RoomReviewArea','AREA');light_data.energy=600;light_data.shape='DISK';light_data.size=6
light=bpy.data.objects.new('RoomReviewArea',light_data);room.objects.link(light)
light.location=(0,-1,3.0)
light.rotation_euler=(Vector((0,2.5,1))-light.location).to_track_quat('-Z','Y').to_euler()
bpy.context.scene.render.engine='BLENDER_EEVEE'
bpy.context.scene.render.resolution_x=1200;bpy.context.scene.render.resolution_y=900
bpy.context.scene.render.filepath=str(preview)
bpy.ops.render.render(write_still=True)
cam.location=(0,0,12)
cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler()
cam_data.type='ORTHO';cam_data.ortho_scale=10
for ob in room.objects:
    if ob.type=='MESH' and ('ceiling' in ob.name.lower() or 'beam' in ob.name.lower()):
        ob.hide_render=True
bpy.context.scene.render.filepath=str(preview.with_name('interior-furniture-top-v030.png'))
bpy.ops.render.render(write_still=True)
print('C2_INTERIOR_REAR_DOOR',len(new),out)
