"""MM01–02：以 imagegen 石峰圖建立 12 三角面的微弧中景卡。"""
from pathlib import Path
import json
import bpy
import numpy as np
from mathutils import Vector

ROOT = Path.cwd()
OUT = ROOT / 'art/exports/midground-v1'
SPECS = {'MM01': ('喀斯特單峰', 78.0, 115.0),
         'MM02': ('喀斯特雙峰', 110.0, 100.0)}


def build(key, name, width, visible_height):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1
    folder = OUT / key
    image = bpy.data.images.load(str(folder / f'{key}_Albedo.png'))
    iw, ih = image.size
    assert (iw, ih) == (2048, 2048)
    pixels = np.empty(iw * ih * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    alpha = pixels.reshape(ih, iw, 4)[:, :, 3]
    ys, _ = np.where(alpha > .12)
    assert len(ys) > 0
    bottom = int(ys.min())
    top = int(ys.max())
    height = visible_height * ih / (top - bottom)
    z0 = -height * bottom / ih

    # 四列三行形成 3 × 2 × 2 = 12 個三角面；橫向向鏡頭微弧 2 m。
    verts = []
    for j in range(3):
        for i in range(4):
            u = i / 3
            v = j / 2
            verts.append(((u - .5) * width, -2.0 * np.sin(np.pi * u), z0 + v * height))
    faces = []
    for j in range(2):
        for i in range(3):
            a = j * 4 + i
            faces.extend(((a, a+1, a+5), (a, a+5, a+4)))
    mesh = bpy.data.meshes.new(f'{key}_CardMesh')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    uv = mesh.uv_layers.new(name='UV0')
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            idx = mesh.loops[li].vertex_index
            uv.data[li].uv = ((idx % 4) / 3, (idx // 4) / 2)
    obj = bpy.data.objects.new(f'{key}_LOD0', mesh)
    scene.collection.objects.link(obj)
    gray = bpy.data.materials.new(f'{key}_Gray')
    gray.diffuse_color = (.48, .49, .48, 1)
    mesh.materials.append(gray)
    bpy.ops.wm.save_as_mainfile(filepath=str(folder / f'{key}_gray.blend'))

    mat = bpy.data.materials.new(f'M_{key}_Card')
    nodes = mat.node_tree.nodes
    bsdf = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = image
    image.pack()
    mat.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    mat.node_tree.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
    bsdf.inputs['Roughness'].default_value = 1
    mat.surface_render_method = 'BLENDED'
    mat.use_backface_culling = False
    mesh.materials.clear()
    mesh.materials.append(mat)
    bpy.ops.wm.save_as_mainfile(filepath=str(folder / f'{key}.blend'))
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=str(folder / f'{key}.glb'),
                              export_format='GLB', use_selection=True)
    bpy.ops.export_scene.fbx(filepath=str(folder / f'{key}.fbx'),
                             use_selection=True, use_triangles=True,
                             axis_forward='-Z', axis_up='Y', bake_anim=False)
    info = {'id': key, 'name_zh': name, 'units': 'm',
            'reference': f'art/references/midground-v1/{key}/three-view.png',
            'type': '遠景透明微弧卡片', 'pivot': '可見輪廓底部中央',
            'dimensions_m': [width, 2.0, round(height, 2)],
            'visible_height_m': visible_height,
            'lods': [{'name': 'LOD0', 'triangles': 12, 'materials': 1,
                      'textures': [{'name': f'{key}_Albedo.png',
                                    'resolution': [iw, ih], 'channels': 'RGBA'}]}],
            'unity_material': 'URP 雙面透明、Alpha Blend；透明排序須實景檢查',
            'collision': False, 'unity_import': '未驗證'}
    (folder / 'model_info.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')

    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    world = bpy.data.worlds.new('ReviewWorld')
    world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs['Color'].default_value = (.55, .61, .65, 1)
    bg.inputs['Strength'].default_value = .8
    scene.world = world
    camera_data = bpy.data.cameras.new('ReviewCam')
    camera = bpy.data.objects.new('ReviewCam', camera_data)
    scene.collection.objects.link(camera)
    camera.location = (0, -width * 1.8, visible_height / 2)
    camera.rotation_euler = (Vector((0, 0, visible_height / 2))-camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera_data.type = 'ORTHO'
    camera_data.ortho_scale = max(width * 1.15, height * 1.18 * 1200 / 900)
    scene.camera = camera
    sun_data = bpy.data.lights.new('ReviewSun', 'SUN')
    sun = bpy.data.objects.new('ReviewSun', sun_data)
    scene.collection.objects.link(sun)
    sun_data.energy = 2
    sun.rotation_euler = (.3, -.4, .2)
    scene.render.filepath = str(folder / f'{key}_preview.png')
    bpy.ops.render.render(write_still=True)
    print('CARD_DONE', key, 'tris=12', 'size=', (iw, ih), flush=True)


for asset, spec in SPECS.items():
    build(asset, *spec)
