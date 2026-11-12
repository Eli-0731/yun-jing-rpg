"""實際載入 MM 石峰並以透明背景渲染，供 C 遠中景並排驗收。"""
from pathlib import Path
import bpy, math
from mathutils import Vector

root=Path.cwd()/'art/exports/midground-v1'
dest=root/'C-pack-review'; dest.mkdir(parents=True,exist_ok=True)
for code in ('MM01','MM02'):
    bpy.ops.wm.open_mainfile(filepath=str(root/code/f'{code}.blend'))
    sc=bpy.context.scene
    sc.render.engine='BLENDER_EEVEE'
    sc.render.resolution_x=800;sc.render.resolution_y=850;sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG';sc.render.film_transparent=True
    sc.world=bpy.data.worlds.new('ReviewWorld');sc.world.color=(.45,.51,.55)
    cam_data=bpy.data.cameras.new('ReviewCam');cam=bpy.data.objects.new('ReviewCam',cam_data);sc.collection.objects.link(cam)
    cam.location=(115,-175,95);target=Vector((0,0,54))
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cam_data.type='ORTHO';cam_data.ortho_scale=153;sc.camera=cam
    light_data=bpy.data.lights.new('ReviewSun','SUN');light=bpy.data.objects.new('ReviewSun',light_data);sc.collection.objects.link(light)
    light.rotation_euler=(math.radians(25),math.radians(-20),math.radians(30));light_data.energy=2.0
    sc.render.filepath=str(dest/f'{code}_transparent.png');bpy.ops.render.render(write_still=True)
    print('RENDERED',code)
