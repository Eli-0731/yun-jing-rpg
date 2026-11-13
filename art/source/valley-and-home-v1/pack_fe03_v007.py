"""Pack FE03 shed, optional detail, detached mooring post, LODs and simple wall collision."""
import bpy,json
from pathlib import Path

root=Path(__file__).resolve().parents[3]
src=root/'art/source/valley-and-home-v1/FE03/FE03-ferry-shed-material-v006.blend'
outblend=root/'art/source/valley-and-home-v1/FE03/FE03-ferry-shed-pack-v007.blend'
out=root/'art/exports/valley-and-home-v1/FE03/v007';out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(src))
def group(names,name,cursor=(0,0,0)):
    if not names:raise ValueError(name+' empty')
    bpy.ops.object.select_all(action='DESELECT')
    for n in names:bpy.data.objects[n].select_set(True)
    ob=bpy.data.objects[names[0]];bpy.context.view_layer.objects.active=ob
    bpy.ops.object.join();ob.name=name;ob.data.name=name+'_Mesh'
    bpy.context.scene.cursor.location=cursor;bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    return ob
meshes=[o.name for o in bpy.data.objects if o.type=='MESH']
mooring_names=sorted(n for n in meshes if 'Mooring' in n)
detail_names=sorted(n for n in meshes if n.startswith('Detail_FE03_') and n not in mooring_names)
main_names=sorted(n for n in meshes if n.startswith('SM_FE03_') and n not in mooring_names)
main=group(main_names,'SM_FE03_FerryShed_LOD0')
detail=group(detail_names,'Detail_FE03_FerryShed_LOD0')
mooring=group(mooring_names,'SM_FE03_MooringPost_LOD0',(-1.75,-.89,0))
objects=[main,detail,mooring]
for lod,ratio in ((1,.82),(2,.62)):
    ob=main.copy();ob.data=main.data.copy();ob.name=f'SM_FE03_FerryShed_LOD{lod}'
    bpy.context.collection.objects.link(ob)
    mod=ob.modifiers.new(f'FE03_Decimate_LOD{lod}','DECIMATE');mod.ratio=ratio
    bpy.context.view_layer.objects.active=ob;bpy.ops.object.modifier_apply(modifier=mod.name)
    objects.append(ob)
for name,center,dim in (
        ('SM_FE03_RearWall_Collision',(0,.94,.72),(2.38,.10,1.46)),
        ('SM_FE03_LeftWall_Collision',(-1.25,.01,.72),(.10,1.90,1.46)),
        ('SM_FE03_RightWall_Collision',(1.25,.01,.72),(.10,1.90,1.46))):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center)
    ob=bpy.context.object;ob.name=name;ob.dimensions=dim
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    ob.hide_render=True;objects.append(ob)
for im in bpy.data.images:
    if im.source=='FILE' and im.has_data:im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(outblend))
bpy.ops.object.select_all(action='DESELECT')
for ob in objects:ob.select_set(True)
bpy.context.view_layer.objects.active=main
bpy.ops.export_scene.fbx(filepath=str(out/'FE03_FerryShed.fbx'),use_selection=True,
    apply_unit_scale=True,mesh_smooth_type='FACE',path_mode='COPY',embed_textures=True)
bpy.ops.export_scene.gltf(filepath=str(out/'FE03_FerryShed.glb'),export_format='GLB',
    use_selection=True,export_apply=True,export_extras=True,export_vertex_color='NONE')
info={ob.name:{'vertices':len(ob.data.vertices),'triangles':sum(len(p.vertices)-2 for p in ob.data.polygons),
    'dimensions_m':[round(x,5) for x in ob.dimensions],
    'origin_m':[round(x,5) for x in ob.location]} for ob in objects}
vertices=[ob.matrix_world@v.co for ob in (main,detail) for v in ob.data.vertices]
lo=[min(v[i] for v in vertices) for i in range(3)]
hi=[max(v[i] for v in vertices) for i in range(3)]
info.update({'minTier':'standard','detailObjects':[detail.name],
    'shed_envelope_m':[round(hi[i]-lo[i],5) for i in range(3)],
    'mooring_post_assembly_offset_m':[-1.75,-.89,0],
    'shed_origin_m':[0,0,0],
    'source':str(outblend.relative_to(root)).replace('\\','/'),
    'status':'export candidate; reimport and visual QA pending'})
(out/'model_info.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
print('@@FE03PACK@@'+json.dumps({'envelope':info['shed_envelope_m'],
    'triangles':{o.name:info[o.name]['triangles'] for o in objects}},ensure_ascii=False))
