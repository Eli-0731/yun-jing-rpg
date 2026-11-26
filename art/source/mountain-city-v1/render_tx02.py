"""TX02 材質預覽。"""
from pathlib import Path
import bpy
from mathutils import Vector

folder=Path.cwd()/'art/exports/mountain-city-v1/TX02'
bpy.ops.wm.open_mainfile(filepath=str(folder/'TX02.blend'))
sc=bpy.context.scene
sc.render.engine='BLENDER_EEVEE'
sc.render.resolution_x=1200
sc.render.resolution_y=900
sc.render.resolution_percentage=100
world=bpy.data.worlds.new('ReviewWorld')
world.use_nodes=True
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND')
bg.inputs['Color'].default_value=(.56,.59,.61,1)
bg.inputs['Strength'].default_value=.7
sc.world=world
cam_data=bpy.data.cameras.new('ReviewCam')
cam=bpy.data.objects.new('ReviewCam',cam_data)
sc.collection.objects.link(cam)
cam.location=(9,-12,9)
target=Vector((0,0,3.2))
cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
cam_data.type='ORTHO'
cam_data.ortho_scale=10.3
sc.camera=cam
sun_data=bpy.data.lights.new('ReviewSun','SUN')
sun=bpy.data.objects.new('ReviewSun',sun_data)
sc.collection.objects.link(sun)
sun.rotation_euler=(.55,-.4,.2)
sun_data.energy=2.5
sc.render.image_settings.file_format='PNG'
sc.render.filepath=str(folder/'TX02_preview.png')
bpy.ops.render.render(write_still=True)
print('PREVIEW',sc.render.filepath)
