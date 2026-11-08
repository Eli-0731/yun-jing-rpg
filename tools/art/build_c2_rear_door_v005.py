"""Adapt the approved StarterHouse v004 rear window into a centered rear door.

The original collaborator file remains untouched. Rear door details reuse the
original front door meshes, scaled to the approved 1.2 × 2.2 m opening.
"""
from pathlib import Path
import bpy
from mathutils import Matrix, Vector

root=Path(__file__).resolve().parents[2]
src=root/'art/incoming/dondon/StarterHouse/v004/StarterHouse_v004.blend'
out=root/'art/source/c2-home-interior-v1/StarterHouse_reardoor_v005.blend'
preview=root/'art/previews/c2-home-interior-v1/rear-door-v005.png'
out.parent.mkdir(parents=True,exist_ok=True);preview.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(src))

for ob in list(bpy.data.objects):
    if ob.name.startswith('Rear_Window_0_') or ob.name=='Rear_Below_0':
        bpy.data.objects.remove(ob,do_unlink=True)

# The old window was 1.4 m wide; narrow its center opening to 1.2 m.
for name,x in [('Rear_Last_Pier',-2.1),('Rear_Pier_0',2.1)]:
    ob=bpy.data.objects[name]
    ob.location.x += x-ob.matrix_world.translation.x
    ob.dimensions.x=3.0

above=bpy.data.objects['Rear_Above_0']
above.location.z += 0.045
above.dimensions.z=.61  # opening from raised floor 0.54 to lintel 2.74

# A full-width rear rail would cross the doorway at ankle height. Keep the
# timber band on the left and right and use a short walkable threshold.
rail=bpy.data.objects['Rear_Horizontal_Beam']
rail_mat=rail.active_material
bpy.data.objects.remove(rail,do_unlink=True)
def cube(name,loc,size,material):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    ob=bpy.context.object;ob.name=name;ob.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if material:ob.data.materials.append(material)
    return ob
cube('Rear_Door_LeftRail',(-2.1,2.635,.65),(3.0,.18,.15),rail_mat)
cube('Rear_Door_RightRail',(2.1,2.635,.65),(3.0,.18,.15),rail_mat)
cube('Rear_Door_Threshold',(0,2.635,.58),(1.20,.24,.08),rail_mat)

# The front door has paper lattice, wood backing and metal rings. Copy its
# exact mesh/material language, rotating to face the back and fitting the
# smaller approved opening. No external asset is altered in place.
fit=Matrix(((-1.2/1.7,0,0,0),(0,-1,0,0),
            (0,0,2.2/2.41,.54*(1-2.2/2.41)),(0,0,0,1)))
for original in list(bpy.data.objects):
    if not (original.name.startswith(('Door_-1_','Door_1_','Door_Outer_Jamb'))
            or original.name=='Door_Lintel'):
        continue
    world=original.matrix_world.copy()
    dup=original.copy()
    if original.data:dup.data=original.data.copy()
    bpy.context.collection.objects.link(dup)
    dup.parent=None;dup.matrix_world=fit @ world
    dup.name='Rear_'+original.name

bpy.ops.wm.save_as_mainfile(filepath=str(out))
export=root/'art/exports/c2-home-interior-v1'
export.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='DESELECT')
for ob in bpy.context.view_layer.objects:
    if ob.type=='MESH':ob.select_set(True)
bpy.ops.export_scene.fbx(filepath=str(export/'StarterHouse_reardoor_v005.fbx'),use_selection=True)
bpy.ops.export_scene.gltf(filepath=str(export/'StarterHouse_reardoor_v005.glb'),
                          export_format='GLB',use_selection=True)

# Render the north elevation using the source house's own materials.
for o in bpy.data.objects:
    if o.type=='CAMERA':o.hide_render=True
camera_data=bpy.data.cameras.new('RearReviewCamera')
camera=bpy.data.objects.new('RearReviewCamera',camera_data)
bpy.context.collection.objects.link(camera)
camera.location=(8,12,6)
camera.rotation_euler=(Vector((0,0,1.9))-camera.location).to_track_quat('-Z','Y').to_euler()
camera_data.lens=40;bpy.context.scene.camera=camera
sun_data=bpy.data.lights.new('RearReviewSun','SUN');sun_data.energy=2
sun=bpy.data.objects.new('RearReviewSun',sun_data)
bpy.context.collection.objects.link(sun);sun.rotation_euler=(.55,-.35,-.7)
bpy.context.scene.render.engine='BLENDER_EEVEE'
bpy.context.scene.render.resolution_x=1200
bpy.context.scene.render.resolution_y=900
bpy.context.scene.render.filepath=str(preview)
bpy.ops.render.render(write_still=True)
print('C2_REAR_DOOR_V005',out,preview)
