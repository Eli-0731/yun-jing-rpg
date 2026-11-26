"""以 AI 三視圖及四張手繪透明圖重做飛鳥、蝴蝶雙面小卡。"""
from pathlib import Path
import json
import bpy

ROOT = Path.cwd()
OUT = ROOT / 'art/exports/life-v1'
SPECS = {
    'LF01': {'name': '遠處飛鳥', 'width': .50, 'variants': ('spread', 'folded'),
             'textures': ('LF01_Spread.png', 'LF01_Folded.png'), 'distance': 60},
    'LF02': {'name': '蝴蝶', 'width': .12, 'variants': ('ivory', 'ochre'),
             'textures': ('LF02_Ivory.png', 'LF02_Ochre.png'), 'distance': 3},
}


def new_card(key, width):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1
    half = width / 2
    mesh = bpy.data.meshes.new(key + '_CardMesh')
    mesh.from_pydata([(-half, -half, 0), (half, -half, 0),
                      (half, half, 0), (-half, half, 0)], [],
                     [(0, 1, 2), (0, 2, 3)])
    mesh.update()
    uv = mesh.uv_layers.new(name='UV0')
    for polygon in mesh.polygons:
        for li in polygon.loop_indices:
            idx = mesh.loops[li].vertex_index
            uv.data[li].uv = ((0, 0), (1, 0), (1, 1), (0, 1))[idx]
    obj = bpy.data.objects.new(key + '_Card', mesh)
    scene.collection.objects.link(obj)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    return obj


def set_texture(obj, key, texture_path):
    image = bpy.data.images.load(str(texture_path))
    image.pack()
    material = bpy.data.materials.new(f'M_{key}_{texture_path.stem}')
    material.use_backface_culling = False
    material.surface_render_method = 'BLENDED'
    nodes = material.node_tree.nodes
    bsdf = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = image
    material.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    material.node_tree.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
    bsdf.inputs['Roughness'].default_value = 1
    obj.data.materials.clear()
    obj.data.materials.append(material)


for key, spec in SPECS.items():
    folder = OUT / key
    for index, (variant, texture) in enumerate(zip(spec['variants'], spec['textures'])):
        obj = new_card(key, spec['width'])
        if index == 0:
            gray = bpy.data.materials.new(key + '_Gray')
            gray.diffuse_color = (.45, .47, .47, 1)
            obj.data.materials.append(gray)
            bpy.ops.wm.save_as_mainfile(filepath=str(folder / f'{key}_gray.blend'))
        set_texture(obj, key, folder / texture)
        blend_name = f'{key}.blend' if index == 0 else f'{key}_{variant}.blend'
        bpy.ops.wm.save_as_mainfile(filepath=str(folder / blend_name))
        bpy.ops.export_scene.gltf(filepath=str(folder / f'{key}_{variant}.glb'),
                                  export_format='GLB', use_selection=True)
        print('CARD_DONE', key, variant, flush=True)
    info = {'id': key, 'name_zh': spec['name'], 'units': 'm',
            'reference': f'art/references/life-v1/{key}/three-view.png',
            'type': '雙面透明小卡', 'distance_preview_m': spec['distance'],
            'width_m': spec['width'], 'lods': [{'name': 'LOD0', 'triangles': 2,
                                              'materials': 1, 'texture_resolution': [1024, 1024]}],
            'variants': dict(zip(spec['variants'], spec['textures'])),
            'runtime': '以影格或材質切換變體；不含 GLB 內建拍翅動畫',
            'unity_material': 'URP 雙面透明、Alpha Blend；關閉陰影',
            'collision': False, 'unity_import': '未驗證'}
    (folder / 'model_info.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
