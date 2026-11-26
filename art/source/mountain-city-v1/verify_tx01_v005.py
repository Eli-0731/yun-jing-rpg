"""回匯 TX01 v005 的 FBX、GLB，核對 LOD 與碰撞網格。"""
from pathlib import Path
import bpy

root = Path(__file__).resolve().parents[3]
folder = root / 'art/exports/mountain-city-v1/TX01/v005'
for kind in ('Board', 'Plaque'):
    for ext in ('fbx', 'glb'):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        path = folder / f'TX01_{kind}.{ext}'
        if ext == 'fbx':
            bpy.ops.import_scene.fbx(filepath=str(path))
        else:
            bpy.ops.import_scene.gltf(filepath=str(path))
        meshes = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
        expected = {f'SM_TX01_{kind}_LOD{i}' for i in range(3)}
        assert expected <= meshes.keys(), (path, expected - meshes.keys())
        assert any(n.startswith('UCX_TX01_') for n in meshes), path
        counts = {n: sum(len(p.vertices) - 2 for p in meshes[n].data.polygons) for n in expected}
        assert all(v > 0 for v in counts.values()), (path, counts)
        print('TX01_V005_REIMPORT_PASS', path.name, counts, 'meshes', len(meshes), flush=True)
