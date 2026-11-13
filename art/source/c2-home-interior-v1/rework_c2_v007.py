"""將 v007 的兩張修正貼圖打包到原幾何，輸出檢查圖與遊戲檔。"""
from pathlib import Path
import json
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / 'art/source/c2-home-interior-v1'
OUT = ROOT / 'art/exports/c2-home-interior-v1/v007'
PRE = ROOT / 'art/previews/c2-home-interior-v1/v007'
PRE.mkdir(parents=True, exist_ok=True)
TEX = OUT / 'Textures'


def rear_signature():
    prefixes = ('Rear_Door_Threshold', 'Rear_Door_Outer_Jamb',
                'RearDoor_SM_IK_door_threshold_LOD0', 'RearDoor_SM_IK_door_jamb_')
    return {o.name: (tuple(round(v, 5) for v in o.matrix_world.translation),
                     tuple(round(v, 5) for v in o.dimensions))
            for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(prefixes)}


def mesh_signature():
    return {o.name: (len(o.data.vertices), len(o.data.polygons),
                     tuple(round(v, 5) for v in o.dimensions))
            for o in bpy.data.objects if o.type == 'MESH'}


def replace_texture(key):
    path = TEX / f'C2_{key}_BaseColor.png'
    image = bpy.data.images.load(str(path), check_existing=False)
    image.pack()
    changed = 0
    for material in bpy.data.materials:
        if not material.use_nodes:
            continue
        for node in material.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image and node.image.name.startswith(f'C2_{key}_BaseColor'):
                node.image = image
                changed += 1
    assert changed > 0, key
    return changed


def fix_plaster_uv():
    """v006 以 3 m 重複貼圖，牆頂落在 v=1 又取到牆腳磚；拉開高度避免接縫。"""
    count = 0
    for obj in bpy.data.objects:
        if obj.type != 'MESH' or not any(mat and mat.name == 'M_C2_TI_plaster' for mat in obj.data.materials):
            continue
        uv = obj.data.uv_layers.get('C2_v006')
        if uv is None:
            continue
        for loop in uv.data:
            loop.uv.y *= 3 / 3.5
        uv.active_render = True
        count += 1
    return count


def save_and_render(area, prior, name, export_name):
    bpy.ops.wm.open_mainfile(filepath=str(SRC / prior))
    rear = rear_signature()
    mesh = mesh_signature()
    count = replace_texture('VL_tile' if area == 'outer' else 'TI_plaster')
    uv_count = fix_plaster_uv() if area == 'interior' else 0
    assert rear_signature() == rear and mesh_signature() == mesh
    bpy.ops.wm.save_as_mainfile(filepath=str(SRC / name))
    bpy.ops.export_scene.fbx(filepath=str(OUT / export_name), path_mode='COPY', embed_textures=True)
    if area == 'outer':
        bpy.ops.export_scene.gltf(filepath=str(OUT / 'StarterHouse_reardoor_v007.glb'), export_format='GLB')
        bpy.ops.object.camera_add(location=(8, 10, 6))
        camera = bpy.context.object
        camera.rotation_euler = (Vector((0, 0, 2)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
        camera.data.type = 'ORTHO'
        camera.data.ortho_scale = 11
        bpy.context.scene.camera = camera
        pictures = [('rear-door-v007.png', camera), ('front-v007.png', bpy.data.objects['House_Overview'])]
    else:
        pictures = [('interior-reardoor-v032.png', bpy.data.objects['Camera_DoorEye'])]
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    for filename, camera in pictures:
        scene.camera = camera
        scene.render.filepath = str(PRE / filename)
        bpy.ops.render.render(write_still=True)
    return {'source': str(SRC / name), 'export': str(OUT / export_name),
            'meshes': len(mesh), 'tris': sum(sum(len(p.vertices)-2 for p in o.data.polygons)
                                           for o in bpy.data.objects if o.type == 'MESH'),
            'changed_texture_nodes': count, 'rear_door': rear,
            'plaster_uv_panels': uv_count,
            'previews': [str(PRE / filename) for filename, _ in pictures]}


info = {'outer': save_and_render('outer', 'StarterHouse_reardoor_v006.blend',
                                'StarterHouse_reardoor_v007.blend', 'StarterHouse_reardoor_v007.fbx'),
        'interior': save_and_render('interior', 'lodging-room-reardoor-v031.blend',
                                   'lodging-room-reardoor-v032.blend', 'lodging-room-reardoor-v032.fbx')}
(OUT / 'model_info.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
print('C2_V007_DONE', {k: (v['meshes'], v['tris']) for k, v in info.items()}, flush=True)
