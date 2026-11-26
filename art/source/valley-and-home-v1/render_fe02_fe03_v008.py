"""FE02／FE03 v008 同規格材質預覽。"""
from pathlib import Path
import bpy, math
from mathutils import Vector
root=Path(__file__).resolve().parents[3]
for code,camloc,target,scale in (
    ('FE02',(4.7,-7.3,3.2),(0,0,.35),7.6),
    ('FE03',(4.2,-5.2,3.4),(0,0,1.15),5.1)):
    src=root/f'art/source/valley-and-home-v1/{code}/{code.lower()}-rework-pack-v008.blend'
    out=root/f'art/previews/valley-and-home-v1/{code}/v008/{code}_threequarter.png'
    out.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(src))
    sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=1200;sc.render.resolution_y=900;sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG';sc.render.film_transparent=False
    for ob in bpy.data.objects:
        if ob.type=='MESH':ob.hide_render=not ob.name.endswith('_LOD0') or 'Collision' in ob.name
    world=bpy.data.worlds.new('ReviewWorld');world.use_nodes=True
    world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.68,.73,.76,1)
    world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.7
    sc.world=world
    bpy.ops.object.camera_add(location=camloc)
    cam=bpy.context.object;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.type='ORTHO';cam.data.ortho_scale=scale;sc.camera=cam
    bpy.ops.object.light_add(type='AREA',location=(-3,-4,5));bpy.context.object.data.energy=650;bpy.context.object.data.size=5
    sc.render.filepath=str(out);bpy.ops.render.render(write_still=True)
    print('PREVIEW',code,out,flush=True)
