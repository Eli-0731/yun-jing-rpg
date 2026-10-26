"""Render measured Blender previews from the v003 source; not Unity screenshots."""
import json
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3]
BLEND=ROOT/'art/source/qingxi-mountain-rabbit-v003/QingxiMountainRabbit_v003.blend'
OUT=ROOT/'art/previews/qingxi-mountain-rabbit-v003'
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BLEND))
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.samples=16
scene.render.resolution_x=720;scene.render.resolution_y=720;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
scene.world.color=(.15,.16,.17)
for name,location,power,size in [('Key',(-1,-1,2),220,1.3),('Fill',(1,-.6,1.6),100,1.0),('Rim',(0,1.4,2),180,1.2)]:
 data=bpy.data.lights.new('Rabbit_'+name,'AREA');data.energy=power;data.shape='DISK';data.size=size
 ob=bpy.data.objects.new('Rabbit_'+name,data);scene.collection.objects.link(ob);ob.location=location
 direction=Vector((0,0,.32))-ob.location;ob.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
camdata=bpy.data.cameras.new('RabbitPreviewCamera');camera=bpy.data.objects.new('RabbitPreviewCamera',camdata)
scene.collection.objects.link(camera);scene.camera=camera
camdata.type='ORTHO';camdata.ortho_scale=1.15;camdata.lens=50
arm=bpy.data.objects['RIG_QingxiRabbit']
mesh=bpy.data.objects['SK_QingxiRabbit_LOD0']
mesh.hide_render=False
for i in (1,2):bpy.data.objects[f'SK_QingxiRabbit_LOD{i}'].hide_render=True
shots={}
def capture(label,action,frame,position):
 arm.animation_data.action=bpy.data.actions[action];scene.frame_set(frame)
 camdata.ortho_scale=1.45 if label=='death' else 1.15
 camera.location=position;camera.rotation_euler=(Vector((0,0,.36))-camera.location).to_track_quat('-Z','Y').to_euler()
 scene.render.filepath=str(OUT/(label+'.png'));bpy.ops.render.render(write_still=True)
 shots[label]={'action':action,'frame':frame,'camera':list(position)}
for name,position in [('front',(0,-1.8,.85)),('side',(1.8,0,.8)),('rear',(0,1.8,.85)),('three_quarter',(1.35,-1.35,.85))]:
 capture(name,'Rabbit_Idle',1,position)
for name,frame in [('idle',24),('hop',12),('flee',8),('hit',4),('death',24)]:
 capture(name,'Rabbit_'+name.title(),frame,(1.35,-1.35,.85))
for name,action,frame in [('crouch','Rabbit_Hop',1),('jump_start','Rabbit_Hop',6),('jump_air','Rabbit_Hop',13),('jump_land','Rabbit_Hop',19)]:
 capture(name,action,frame,(1.8,0,.8))
(OUT/'shots.json').write_text(json.dumps(shots,indent=2)+'\n')
print('RABBIT_PREVIEWS_PASS',len(shots))
