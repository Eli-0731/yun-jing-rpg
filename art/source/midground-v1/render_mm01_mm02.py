"""輸出石峰材質預覽與輪廓檢查圖。"""
from pathlib import Path
import bpy, math
from mathutils import Vector
root=Path.cwd()/'art/exports/midground-v1'
for name in ('MM01','MM02'):
    bpy.ops.wm.open_mainfile(filepath=str(root/name/f'{name}.blend'))
    scene=bpy.context.scene
    scene.render.engine='BLENDER_EEVEE'
    scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.world=bpy.data.worlds.new('ReviewWorld');scene.world.color=(.45,.51,.55)
    cam_data=bpy.data.cameras.new('ReviewCam');cam=bpy.data.objects.new('ReviewCam',cam_data);scene.collection.objects.link(cam)
    cam.location=(115,-175,95);target=Vector((0,0,50));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam_data.type='ORTHO';cam_data.ortho_scale=165
    scene.camera=cam
    light_data=bpy.data.lights.new('ReviewSun','SUN');light=bpy.data.objects.new('ReviewSun',light_data);scene.collection.objects.link(light)
    light.rotation_euler=(math.radians(25),math.radians(-20),math.radians(30));light_data.energy=2.0
    scene.render.filepath=str(root/name/f'{name}_preview.png');bpy.ops.render.render(write_still=True)
    print('RENDERED',name,scene.render.filepath)
