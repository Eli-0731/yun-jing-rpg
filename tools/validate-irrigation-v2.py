"""Blender round-trip validation of textured LOD assets and presentation layers."""
import bpy, json, math, struct
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'art/exports/irrigation-v2'
UNITY=ROOT/'apps/game/Assets/YunJing/Models/IrrigationV2'
results=[];textures=[]
for name,expected in [('spirit-bed',(2.414,3.222,.403)),('cistern',(2,2.28,1.1)),('water-channel',(.6,2,.24))]:
    for channel in ('albedo','normal'):
        image=bpy.data.images.load(str(UNITY/'Textures'/(name+'-'+channel+'.png')),check_existing=False)
        assert tuple(image.size)==(1024,1024)
        pixels=list(image.pixels);sample=pixels[::16]
        assert max(sample)-min(sample)>.08, (name,channel,'blank image')
        textures.append({'asset':name,'channel':channel,'size':[1024,1024],'bytes':(UNITY/'Textures'/(name+'-'+channel+'.png')).stat().st_size})
    for lod in (0,1):
        stem=name+('-lod1' if lod else '')
        glb=(OUT/(stem+'.glb')).read_bytes()
        length,kind=struct.unpack_from('<II',glb,12);assert kind==0x4E4F534A
        description=json.loads(glb[20:20+length]);assert len(description['images'])==2
        assert all('bufferView' in img for img in description['images']), 'GLB textures must be embedded'
        for format in ('glb','fbx'):
            bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
            if format=='glb':bpy.ops.import_scene.gltf(filepath=str(OUT/(stem+'.glb')))
            else:bpy.ops.import_scene.fbx(filepath=str(UNITY/(stem+'.fbx')))
            meshes=[obj for obj in bpy.context.scene.objects if obj.type=='MESH']
            assert len(meshes)==2,(stem,format,'Expected body plus foliage/water')
            layer='foliage' if name=='spirit-bed' else 'water'
            assert any(obj.name.endswith('-'+layer) or obj.name.endswith('-'+layer+'-lod1') for obj in meshes)
            points=[obj.matrix_world@Vector(corner) for obj in meshes for corner in obj.bound_box]
            bounds=[max(p[i] for p in points)-min(p[i] for p in points) for i in range(3)]
            assert all(abs(a-b)<.06 for a,b in zip(bounds,expected)),(stem,format,bounds)
            triangles=0
            for obj in meshes:
                assert len(obj.data.materials)==1,(stem,'Too many material slots')
                assert obj.data.uv_layers
                assert all(math.isfinite(value) for vertex in obj.data.vertices for value in vertex.co)
                assert all(-.001<=value<=1.001 for uv in obj.data.uv_layers.active.data for value in uv.uv)
                obj.data.calc_loop_triangles();triangles+=len(obj.data.loop_triangles)
            results.append({'asset':name,'lod':lod,'format':format,'triangles':triangles,'bounds_m':bounds,'status':'passed'})
    full=next(r['triangles'] for r in results if r['asset']==name and r['lod']==0)
    low=next(r['triangles'] for r in results if r['asset']==name and r['lod']==1)
    assert low<full*.65,(name,'LOD did not reduce enough')
(OUT/'validation.json').write_text(json.dumps({'textures':textures,'exports':results},indent=2),encoding='utf8')
print('PASS: 12 GLB/FBX LOD round-trips; 6 nonblank 1024px textures; layer separation; embedded GLB maps; bounds; UVs.')

# Show the actual empty-bed and drained-basin configurations from the packed source.
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/source/irrigation-v2.blend'))
scene=bpy.context.scene;camera=scene.camera
for asset,layer in [('spirit-bed','foliage'),('cistern','water')]:
    target=[obj for obj in scene.objects if obj.type=='MESH' and obj.get('asset_version')=='2' and obj.name.startswith(asset)]
    for obj in scene.objects:
        if obj.type=='MESH' and obj.get('asset_version')=='2':obj.hide_render=obj not in target or obj.get('game_layer')==layer
    center=target[0].location+Vector((0,0,.4));camera.location=center+Vector((4,-6,5))
    camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=4.8
    scene.render.resolution_x=1000;scene.render.resolution_y=1000
    scene.render.filepath=str(ROOT/'art/previews'/(asset+'-empty-v2.png'));bpy.ops.render.render(write_still=True)
