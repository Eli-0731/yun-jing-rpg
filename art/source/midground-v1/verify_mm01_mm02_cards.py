"""MM01–02 新卡片的尺寸、材質、輸出與回匯檢查。"""
from pathlib import Path
import bpy

root = Path.cwd() / 'art/exports/midground-v1'
for key in ('MM01', 'MM02'):
    folder = root / key
    bpy.ops.wm.open_mainfile(filepath=str(folder / f'{key}.blend'))
    obj = bpy.data.objects[f'{key}_LOD0']
    assert len(obj.data.polygons) == 12
    assert all(len(p.vertices) == 3 for p in obj.data.polygons)
    assert len(obj.data.uv_layers) == 1
    assert len(obj.data.materials) == 1
    assert obj.data.materials[0].use_backface_culling is False
    for suffix in ('_Albedo.png', '.blend', '.fbx', '.glb', '_gray.blend', '_preview.png'):
        path = folder / f'{key}{suffix}'
        assert path.exists() and path.stat().st_size > 0, path
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(folder / f'{key}.fbx'))
    fbx_tris = sum(sum(len(p.vertices)-2 for p in o.data.polygons)
                   for o in bpy.data.objects if o.type == 'MESH')
    assert fbx_tris == 12, (key, fbx_tris)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(folder / f'{key}.glb'))
    glb_tris = sum(sum(len(p.vertices)-2 for p in o.data.polygons)
                   for o in bpy.data.objects if o.type == 'MESH')
    assert glb_tris == 12, (key, glb_tris)
    print('回匯通過', key, 'FBX', fbx_tris, 'GLB', glb_tris, flush=True)
