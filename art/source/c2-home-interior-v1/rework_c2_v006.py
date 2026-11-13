"""C2 材質重做：VL 外屋、TI 室內；保留後門及既有家具幾何。"""
import bpy
import json
import sys
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / 'art/source/c2-home-interior-v1'
OUT = ROOT / 'art/exports/c2-home-interior-v1/v006'
PRE = ROOT / 'art/previews/c2-home-interior-v1/v006'
TEX = OUT / 'Textures'
for p in (OUT, PRE, TEX):
    p.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(SRC / 'shared'))
import vl_mats as vl
import ti_mats as ti


def make_plane():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.mesh.primitive_plane_add(size=3, location=(0, 0, 1.5), rotation=(1.57079632679, 0, 0))
    plane = bpy.context.object
    plane.name = '材質烘焙平面'
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    # TI 木紋使用的局部軸與隨機值。
    for name, kind, value in [('gA', 'FLOAT_VECTOR', (1, 0, 0)),
                              ('gB', 'FLOAT_VECTOR', (0, 0, 1)),
                              ('gC', 'FLOAT_VECTOR', (0, 1, 0)),
                              ('part_rand', 'FLOAT', .37)]:
        attr = plane.data.attributes.new(name, kind, 'POINT')
        for item in attr.data:
            if kind == 'FLOAT_VECTOR':
                item.vector = value
            else:
                item.value = value
    bpy.ops.object.camera_add(location=(0, -6, 1.5))
    camera = bpy.context.object
    camera.rotation_euler = (Vector((0, 0, 1.5)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = 3
    scene = bpy.context.scene
    scene.camera = camera
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 8
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = False
    scene.world = bpy.data.worlds.new('材質烘焙背景')
    scene.world.color = (.5, .5, .5)
    return plane


def bake_swatch(plane, key, mat):
    plane.data.materials.clear()
    plane.data.materials.append(mat)
    nodes = mat.node_tree.nodes
    output = nodes['OUTPUT']
    old = output.inputs['Surface'].links[0].from_socket
    emit = nodes.new('ShaderNodeEmission')
    mat.node_tree.links.new(nodes['OUT_COLOR'].outputs[0], emit.inputs['Color'])
    mat.node_tree.links.new(emit.outputs[0], output.inputs['Surface'])
    path = TEX / f'C2_{key}_BaseColor.png'
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    mat.node_tree.links.new(old, output.inputs['Surface'])
    nodes.remove(emit)
    print('SWATCH', key, path, flush=True)


plane = make_plane()
vlpal = vl.palette('elderly')
swatches = {
    'VL_plaster': vlpal['plaster'],
    'VL_wood': vlpal['timber'],
    'VL_plank': vlpal['plank'],
    'VL_stone': vlpal['stone'][0],
    'VL_tile': vlpal['tile'],
    'VL_paper': vlpal['paper'],
    'TI_wood': ti.wood('C2_TI_UsedWood', (.055, .028, .015), (.27, .17, .09), rough=.82, wear=.7, grime=.45),
    'TI_stone': ti.plain('C2_TI_Stone', (.19, .21, .20), rough=.9, noise=.35, scale=18),
    'TI_plaster': vlpal['plaster_in'],
    'TI_paper': ti.paper('C2_TI_Paper', (.72, .66, .49), 'Main'),
}
for key, mat in swatches.items():
    bake_swatch(plane, key, mat)


def image_mat(key):
    mat = bpy.data.materials.new('M_C2_' + key)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bs = nodes.get('Principled BSDF')
    image = bpy.data.images.load(str(TEX / f'C2_{key}_BaseColor.png'), check_existing=True)
    image.pack()
    texture = nodes.new('ShaderNodeTexImage')
    texture.image = image
    texture.extension = 'REPEAT'
    mat.node_tree.links.new(texture.outputs['Color'], bs.inputs['Base Color'])
    bs.inputs['Roughness'].default_value = .85 if 'plaster' in key or 'paper' in key else .77
    return mat


def project_uv(obj):
    mesh = obj.data
    uv = mesh.uv_layers.get('C2_v006') or mesh.uv_layers.new(name='C2_v006')
    mesh.uv_layers.active = uv
    for poly in mesh.polygons:
        normal = (obj.matrix_world.to_3x3() @ poly.normal).normalized()
        ax = max(range(3), key=lambda i: abs(normal[i]))
        for li in poly.loop_indices:
            p = obj.matrix_world @ mesh.vertices[mesh.loops[li].vertex_index].co
            if ax == 0:
                uv.data[li].uv = (p.y / 3, p.z / 3)
            elif ax == 1:
                uv.data[li].uv = (p.x / 3, p.z / 3)
            else:
                uv.data[li].uv = (p.x / 3, p.y / 3)


def rear_signature():
    result = {}
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        if obj.name.startswith('Rear_Door_Threshold') or obj.name.startswith('Rear_Door_Outer_Jamb') \
           or obj.name.startswith('RearDoor_SM_IK_door_threshold_LOD0') or obj.name.startswith('RearDoor_SM_IK_door_jamb_'):
            result[obj.name] = {'center': [round(v, 5) for v in obj.matrix_world.translation],
                                'size': [round(v, 5) for v in obj.dimensions]}
    return result


def category(matname, area):
    n = matname.lower()
    if area == 'outer':
        if 'plaster' in n:
            return 'VL_plaster'
        if 'tile' in n:
            return 'VL_tile'
        if 'blue_stone' in n:
            return 'VL_stone'
        if 'window_paper' in n:
            return 'VL_paper'
        if 'porch' in n:
            return 'VL_plank'
        if 'timber' in n:
            return 'VL_wood'
    else:
        if 'm_ik_limeplaster' in n:
            return 'TI_plaster'
        if 'm_ik_greystone' in n:
            return 'TI_stone'
        if 'm_ik_windowpaper' in n or 'warm_window_paper' in n:
            return 'TI_paper'
        if 'm_ik_agedtimber' in n or 'warm_timber' in n or 'dark_chestnut' in n:
            return 'TI_wood'
    return None


def rework(area, file, target):
    bpy.ops.wm.open_mainfile(filepath=str(SRC / file))
    before = rear_signature()
    mats = {key: image_mat(key) for key in swatches}
    changed = {}
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        mapping = [(i, category(old.name, area) if old else None)
                   for i, old in enumerate(obj.data.materials)]
        if any(key for _, key in mapping):
            # 原室內多物件共用網格但材質槽不同；各自複製後再重配，避免 FBX 索引歧義。
            obj.data = obj.data.copy()
        used = False
        for i, key in mapping:
            if key:
                obj.data.materials[i] = mats[key]
                changed[key] = changed.get(key, 0) + 1
                used = True
        if used:
            project_uv(obj)
        if area == 'interior' and obj.name.startswith('RearDoor_Leaf_'):
            obj.hide_render = False
    assert before == rear_signature(), '後門位置或尺寸改變'
    # 新貼圖已各自打包；既有 TI 貼圖沿原分支路徑，避免把整屋重複嵌入輸出。
    out_blend = SRC / target
    bpy.ops.wm.save_as_mainfile(filepath=str(out_blend))
    if area == 'outer':
        bpy.ops.export_scene.fbx(filepath=str(OUT / 'StarterHouse_reardoor_v006.fbx'), path_mode='COPY', embed_textures=True)
        bpy.ops.export_scene.gltf(filepath=str(OUT / 'StarterHouse_reardoor_v006.glb'), export_format='GLB')
        bpy.ops.object.camera_add(location=(8, 10, 6))
        rear_cam = bpy.context.object
        rear_cam.rotation_euler = (Vector((0, 0, 2)) - rear_cam.location).to_track_quat('-Z', 'Y').to_euler()
        rear_cam.data.type = 'ORTHO'
        rear_cam.data.ortho_scale = 11
        bpy.context.scene.camera = rear_cam
        preview = PRE / 'rear-door-v006.png'
    else:
        bpy.ops.export_scene.fbx(filepath=str(OUT / 'lodging-room-reardoor-v031.fbx'), path_mode='AUTO')
        bpy.context.scene.camera = bpy.data.objects.get('Camera_DoorEye')
        preview = PRE / 'interior-reardoor-v031.png'
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = str(preview)
    bpy.ops.render.render(write_still=True)
    if area == 'outer':
        scene.camera = bpy.data.objects.get('House_Overview')
        scene.render.filepath = str(PRE / 'front-v006.png')
        bpy.ops.render.render(write_still=True)
    return {'source': str(out_blend.relative_to(ROOT)), 'materials_changed': changed,
            'rear_door': before, 'preview': str(preview.relative_to(ROOT))}


info = {'outer': rework('outer', 'StarterHouse_reardoor_v005.blend', 'StarterHouse_reardoor_v006.blend'),
        'interior': rework('interior', 'lodging-room-reardoor-v030.blend', 'lodging-room-reardoor-v031.blend')}
(OUT / 'model_info.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
print('C2_DONE', {k: v['materials_changed'] for k, v in info.items()}, flush=True)
