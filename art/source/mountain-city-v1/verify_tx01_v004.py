"""Reimport both interchange formats and verify the delivered TX01 mesh set."""
from pathlib import Path
import bpy

root=Path(__file__).resolve().parents[3]
folder=root/'art/exports/mountain-city-v1/TX01/v004'
for kind in ('Board','Plaque'):
    for ext in ('fbx','glb'):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        path=folder/f'TX01_{kind}.{ext}'
        if ext=='fbx':bpy.ops.import_scene.fbx(filepath=str(path))
        else:bpy.ops.import_scene.gltf(filepath=str(path))
        names={o.name for o in bpy.data.objects if o.type=='MESH'}
        expected={f'SM_TX01_{kind}_LOD{i}' for i in range(3)}
        assert expected <= names,(path,expected-names)
        assert any(n.startswith('UCX_TX01_') for n in names),path
        tris={o.name:sum(len(p.vertices)-2 for p in o.data.polygons)
              for o in bpy.data.objects if o.type=='MESH'}
        assert all(tris[n]>0 for n in expected),(path,tris)
        print('TX01_REIMPORT_PASS',path.name,'lod_triangles',
              [tris[n] for n in sorted(expected)],'meshes',len(names))
