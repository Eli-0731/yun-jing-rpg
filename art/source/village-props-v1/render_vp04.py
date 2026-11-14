"""材質預覽，與模型交付分離。"""
from pathlib import Path
import bpy
from mathutils import Vector

folder=Path.cwd()/'art/exports/village-props-v1/VP04'
bpy.ops.wm.open_mainfile(filepath=str(folder/'VP04.blend'))
sc=bpy.context.scene
sc.render.engine='BLENDER_EEVEE'
sc.render.resolution_x=1200
sc.render.resolution_y=900
sc.render.resolution_percentage=100
world=bpy.data.worlds.new('ReviewWorld')
world.use_nodes=True
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND')
bg.inputs['Color'].default_value=(.57,.60,.62,1)
bg.inputs['Strength'].default_value=.65
sc.world=world
cam_data=bpy.data.cameras.new('ReviewCam')
cam=bpy.data.objects.new('ReviewCam',cam_data)
sc.collection.objects.link(cam)
cam.location=(6,-8,5)
target=Vector((0,0,1.45))
cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
cam_data.type='ORTHO'
cam_data.ortho_scale=5.6
sc.camera=cam
sun_data=bpy.data.lights.new('ReviewSun','SUN')
sun=bpy.data.objects.new('ReviewSun',sun_data)
sc.collection.objects.link(sun)
sun.rotation_euler=(.45,-.5,.35)
sun_data.energy=2.2
sc.render.image_settings.file_format='PNG'
sc.render.filepath=str(folder/'VP04_preview.png')
bpy.ops.render.render(write_still=True)
print('PREVIEW',sc.render.filepath)
