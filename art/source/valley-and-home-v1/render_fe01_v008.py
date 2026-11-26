"""輸出 FE01 新版三段同角度預覽。"""
from pathlib import Path
import bpy, math, sys
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[3]
variants=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['Straight','Corner','End']
for variant in variants:
    src=ROOT/f'art/source/valley-and-home-v1/FE01/FE01-{variant.lower()}-pack-v008.blend'
    out=ROOT/f'art/previews/valley-and-home-v1/FE01/v008/FE01_{variant}_threequarter.png'
    out.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(src))
    sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE'
    sc.render.resolution_x=1000;sc.render.resolution_y=900;sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG';sc.render.film_transparent=False
    for ob in bpy.data.objects:
        if ob.type=='MESH':
            ob.hide_render=not ob.name.endswith('_LOD0') or ob.name.endswith('_Collision')
            ob.hide_viewport=False
    world=bpy.data.worlds.new('FE01_ReviewWorld');world.use_nodes=True
    world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.75,.79,.80,1)
    world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.6
    sc.world=world
    bpy.ops.object.camera_add(location=(3.8,-5.1,2.8))
    cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,.25))-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.type='ORTHO';cam.data.ortho_scale=4.5;sc.camera=cam
    bpy.ops.object.light_add(type='AREA',location=(-2,-3,5))
    light=bpy.context.object;light.data.energy=550;light.data.size=5
    sc.render.filepath=str(out);bpy.ops.render.render(write_still=True)
    print('FE01_PREVIEW',variant,out)
