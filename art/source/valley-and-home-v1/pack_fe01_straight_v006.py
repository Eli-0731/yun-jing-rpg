"""FE01 straight boardwalk LODs, optional details, deck collision and exports."""
import bpy
import json
from pathlib import Path

root=Path(__file__).resolve().parents[3]
src=root/'art/source/valley-and-home-v1/FE01/FE01-straight-qa-v005.blend'
outblend=root/'art/source/valley-and-home-v1/FE01/FE01-straight-pack-v006.blend'
out=root/'art/exports/valley-and-home-v1/FE01/Straight/v006';out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(src))
def join_group(names,newname):
    bpy.ops.object.select_all(action='DESELECT')
    for name in names:bpy.data.objects[name].select_set(True)
    active=bpy.data.objects[names[0]]
    bpy.context.view_layer.objects.active=active
    bpy.ops.object.join()
    active.name=newname;active.data.name=newname+'_Mesh'
    bpy.context.scene.cursor.location=(0,0,0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    return active
main_names=sorted(o.name for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('SM_FE01_'))
detail_names=sorted(o.name for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Detail_FE01_'))
main=join_group(main_names,'SM_FE01_Straight_LOD0')
detail=join_group(detail_names,'Detail_FE01_Straight_RopeBamboo_LOD0')
objects=[main,detail]
for lod,ratio in ((1,.90),(2,.64)):
    ob=main.copy();ob.data=main.data.copy();ob.name=f'SM_FE01_Straight_LOD{lod}'
    bpy.context.collection.objects.link(ob)
    modifier=ob.modifiers.new(f'FE01_Decimate_LOD{lod}','DECIMATE');modifier.ratio=ratio
    bpy.context.view_layer.objects.active=ob
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    objects.append(ob)
# Simple walkable-top proxy only: not a runtime or gameplay change.
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,.38))
collision=bpy.context.object;collision.name='SM_FE01_Straight_Collision'
collision.dimensions=(1.58,2.98,.14)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
collision.hide_render=True;objects.append(collision)
for im in bpy.data.images:
    if im.source=='FILE' and im.has_data:im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(outblend))
bpy.ops.object.select_all(action='DESELECT')
for ob in objects:ob.select_set(True)
bpy.context.view_layer.objects.active=main
bpy.ops.export_scene.fbx(filepath=str(out/'FE01_Straight.fbx'),use_selection=True,
    apply_unit_scale=True,mesh_smooth_type='FACE',path_mode='COPY',embed_textures=True)
bpy.ops.export_scene.gltf(filepath=str(out/'FE01_Straight.glb'),export_format='GLB',
    use_selection=True,export_apply=True,export_extras=True,export_vertex_color='NONE')
info={ob.name:{'vertices':len(ob.data.vertices),
    'triangles':sum(len(p.vertices)-2 for p in ob.data.polygons),
    'dimensions_m':[round(x,5) for x in ob.dimensions],
    'origin_m':[round(x,5) for x in ob.location]}
    for ob in objects}
info.update({'minTier':'standard','detailObjects':[detail.name],
    'waterline_z_m':0,'deck_top_z_m':.45,'pile_bottom_z_m':-1,
    'source':str(outblend.relative_to(root)).replace('\\','/'),
    'status':'export candidate; reimport and visual QA pending'})
(out/'model_info.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
print('@@FE01PACK@@'+json.dumps({k:v for k,v in info.items() if k.startswith(('SM_','Detail_'))},ensure_ascii=False))
