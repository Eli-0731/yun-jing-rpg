"""Round-trip exported GLB/FBX in Blender; check scale, finite geometry and UVs."""
import bpy, json, math
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parent.parent
results=[]
for name,expected in [('spirit-bed',(2.4,3.214,.45)),('cistern',(2,2.28,1.1)),('water-channel',(.6,2,.24))]:
    for format in ('glb','fbx'):
        bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
        if format=='glb':bpy.ops.import_scene.gltf(filepath=str(root/'art/exports/irrigation-v1'/(name+'.glb')))
        else:bpy.ops.import_scene.fbx(filepath=str(root/'apps/game/Assets/YunJing/Models/Irrigation'/(name+'.fbx')))
        meshes=[obj for obj in bpy.context.scene.objects if obj.type=='MESH']
        assert meshes,name
        points=[obj.matrix_world@Vector(corner) for obj in meshes for corner in obj.bound_box]
        bounds=[max(p[i] for p in points)-min(p[i] for p in points) for i in range(3)]
        for actual,target in zip(bounds,expected):assert abs(actual-target)<.10,(name,format,bounds,expected)
        triangles=0
        for obj in meshes:
            assert obj.data.uv_layers,name+' missing UVs'
            assert all(math.isfinite(value) for vertex in obj.data.vertices for value in vertex.co)
            obj.data.calc_loop_triangles();triangles+=len(obj.data.loop_triangles)
        assert triangles<10000
        results.append({'name':name,'format':format,'roundtrip_bounds_m':bounds,'triangles':triangles,'uv':True,'status':'passed'})
(root/'art/exports/irrigation-v1/validation.json').write_text(json.dumps(results,indent=2),encoding='utf8')
print('VALIDATED '+json.dumps(results))
