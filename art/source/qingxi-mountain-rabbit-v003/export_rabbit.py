"""Export v003 rigged rabbit and clips. Run after rabbit_model.py."""
import json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[3]
BLEND=ROOT/'art/source/qingxi-mountain-rabbit-v003/QingxiMountainRabbit_v003.blend'
OUT=ROOT/'art/exports/qingxi-mountain-rabbit-v003'
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BLEND))
arm=bpy.data.objects['RIG_QingxiRabbit']
lods=[bpy.data.objects[f'SK_QingxiRabbit_LOD{i}'] for i in range(3)]
def select(mesh):
 bpy.ops.object.select_all(action='DESELECT')
 mesh.hide_viewport=False;mesh.hide_set(False);mesh.hide_render=False
 arm.select_set(True);mesh.select_set(True)
 bpy.context.view_layer.objects.active=arm
 assert mesh.select_get(), mesh.name

def fbx(path,all_actions):
 bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'ARMATURE','MESH'},
  axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',
  bake_space_transform=False,add_leaf_bones=False,use_armature_deform_only=True,
  mesh_smooth_type='FACE',bake_anim=True,bake_anim_use_nla_strips=False,
  bake_anim_use_all_actions=all_actions,bake_anim_force_startend_keying=True,
  bake_anim_step=1.0,bake_anim_simplify_factor=0.0,path_mode='RELATIVE')

select(lods[0]);arm.animation_data.action=bpy.data.actions['Rabbit_Idle']
fbx(OUT/'QingxiMountainRabbit_v003.fbx',True)
for name in ('Rabbit_Idle','Rabbit_Hop','Rabbit_Flee','Rabbit_Hit','Rabbit_Death'):
 arm.animation_data.action=bpy.data.actions[name]
 scene=bpy.context.scene
 scene.frame_start=1;scene.frame_end=int(bpy.data.actions[name]['frames'])
 fbx(OUT/(name+'.fbx'),False)
for i in (1,2):
 select(lods[i]);arm.animation_data.action=bpy.data.actions['Rabbit_Idle']
 bpy.ops.export_scene.fbx(filepath=str(OUT/f'QingxiMountainRabbit_v003_LOD{i}.fbx'),
  use_selection=True,object_types={'ARMATURE','MESH'},axis_forward='-Z',axis_up='Y',
  apply_unit_scale=True,add_leaf_bones=False,use_armature_deform_only=True,
  bake_anim=False,mesh_smooth_type='FACE')
select(lods[0]);scene.frame_start=1;scene.frame_end=48
arm.animation_data.action=bpy.data.actions['Rabbit_Idle']
bpy.ops.export_scene.gltf(filepath=str(OUT/'QingxiMountainRabbit_v003.glb'),export_format='GLB',
 use_selection=True,export_animations=True,export_animation_mode='ACTIONS',
 export_force_sampling=True,export_apply=False,export_image_format='AUTO')
print('RABBIT_EXPORT_PASS',[(p.name,p.stat().st_size) for p in OUT.iterdir() if p.is_file()])
