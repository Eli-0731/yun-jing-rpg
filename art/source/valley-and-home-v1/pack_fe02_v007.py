"""Pack FE02 ferry hull, switchable canopy, pole, optional detail and LODs."""
import bpy,json
from pathlib import Path
from mathutils import Vector

root=Path(__file__).resolve().parents[3]
src=root/'art/source/valley-and-home-v1/FE02/FE02-ferry-qa-v005.blend'
outblend=root/'art/source/valley-and-home-v1/FE02/FE02-ferry-pack-v007.blend'
out=root/'art/exports/valley-and-home-v1/FE02/v007';out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(src))
def group(names,name):
    if not names:raise ValueError(name+' empty')
    bpy.ops.object.select_all(action='DESELECT')
    for n in names:bpy.data.objects[n].select_set(True)
    ob=bpy.data.objects[names[0]];bpy.context.view_layer.objects.active=ob
    bpy.ops.object.join();ob.name=name;ob.data.name=name+'_Mesh'
    bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    return ob
meshes=[o.name for o in bpy.data.objects if o.type=='MESH']
main=group(sorted(n for n in meshes if n.startswith('SM_FE02_') and
    not n.startswith(('SM_FE02_Canopy','SM_FE02_PushPole'))),'SM_FE02_FerryHull_LOD0')
canopy=group(sorted(n for n in meshes if n.startswith(('SM_FE02_Canopy','Detail_FE02_Canopy'))),'SM_FE02_Canopy_LOD0')
pole=group(sorted(n for n in meshes if n.startswith(('SM_FE02_PushPole','Detail_FE02_Pole'))),'SM_FE02_PushPole_LOD0')
detail=group(sorted(n for n in meshes if n.startswith('Detail_FE02_HullPatch')),
    'Detail_FE02_HullPatches_LOD0')
objects=[main,canopy,pole,detail]
for base,ratios in ((main,((1,.85),(2,.82))),(canopy,((1,.8),(2,.55)))):
    for lod,ratio in ratios:
        ob=base.copy();ob.data=base.data.copy();ob.name=base.name.replace('LOD0',f'LOD{lod}')
        bpy.context.collection.objects.link(ob)
        mod=ob.modifiers.new(f'FE02_Decimate_LOD{lod}','DECIMATE');mod.ratio=ratio
        bpy.context.view_layer.objects.active=ob;bpy.ops.object.modifier_apply(modifier=mod.name)
        objects.append(ob)
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,-.13))
collision=bpy.context.object;collision.name='SM_FE02_Ferry_Collision'
collision.dimensions=(1.22,5.65,.10)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
collision.hide_render=True;objects.append(collision)
for im in bpy.data.images:
    if im.source=='FILE' and im.has_data:im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(outblend))
bpy.ops.object.select_all(action='DESELECT')
for ob in objects:ob.select_set(True)
bpy.context.view_layer.objects.active=main
bpy.ops.export_scene.fbx(filepath=str(out/'FE02_Ferry.fbx'),use_selection=True,
    apply_unit_scale=True,mesh_smooth_type='FACE',path_mode='COPY',embed_textures=True)
bpy.ops.export_scene.gltf(filepath=str(out/'FE02_Ferry.glb'),export_format='GLB',
    use_selection=True,export_apply=True,export_extras=True,export_vertex_color='NONE')
info={ob.name:{'vertices':len(ob.data.vertices),
    'triangles':sum(len(p.vertices)-2 for p in ob.data.polygons),
    'dimensions_m':[round(x,5) for x in ob.dimensions],
    'origin_m':[round(x,5) for x in ob.location]}
    for ob in objects}
vertices=[ob.matrix_world@v.co for ob in (main,canopy,pole,detail) for v in ob.data.vertices]
lo=[min(v[i] for v in vertices) for i in range(3)]
hi=[max(v[i] for v in vertices) for i in range(3)]
envelope=[hi[i]-lo[i] for i in range(3)]
info.update({'minTier':'standard','switchableCanopy':'SM_FE02_Canopy_LOD0',
    'detailObjects':[detail.name],'waterline_origin_m':[0,0,0],
    'overall_envelope_m':[round(x,5) for x in envelope],
    'overall_bounds_z_m':[round(lo[2],5),round(hi[2],5)],
    'source':str(outblend.relative_to(root)).replace('\\','/'),
    'status':'export candidate; reimport and visual QA pending'})
(out/'model_info.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
print('@@FE02PACK@@'+json.dumps({'envelope':info['overall_envelope_m'],
    'triangles':{o.name:info[o.name]['triangles'] for o in objects}},ensure_ascii=False))
