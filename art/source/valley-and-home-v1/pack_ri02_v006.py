"""Make RI02 rice LOD variants and export one nine-mesh art asset."""
import bpy
import json
from pathlib import Path

root=Path(__file__).resolve().parents[3]
src=root/'art/source/valley-and-home-v1/RI02/RI02-rice-material-v004.blend'
outblend=root/'art/source/valley-and-home-v1/RI02/RI02-rice-pack-v006.blend'
export=root/'art/exports/valley-and-home-v1/RI02/v006'
export.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(src))
objects=[]
for stage in ('Seedling','Green','Golden'):
    original=bpy.data.objects[f'SM_RI02_Rice_{stage}_LOD0']
    original.hide_render=False
    objects.append(original)
    for lod,ratio in ((1,0.68),(2,0.42)):
        obj=original.copy();obj.data=original.data.copy()
        obj.name=f'SM_RI02_Rice_{stage}_LOD{lod}'
        bpy.context.collection.objects.link(obj)
        dec=obj.modifiers.new(f'RI02_LOD{lod}_Decimate','DECIMATE')
        dec.ratio=ratio
        bpy.context.view_layer.objects.active=obj
        bpy.ops.object.modifier_apply(modifier=dec.name)
        objects.append(obj)
for obj in objects:
    weights=obj.data.color_attributes['WindWeight']
    custom=obj.data.attributes.new(name='_WindWeight',type='FLOAT',domain='POINT')
    for i in range(len(obj.data.vertices)):
        custom.data[i].value=weights.data[i].color[0]
for im in bpy.data.images:
    if im.source=='FILE' and im.has_data:im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(outblend))
bpy.ops.object.select_all(action='DESELECT')
for obj in objects:obj.select_set(True)
bpy.context.view_layer.objects.active=objects[0]
bpy.ops.export_scene.fbx(filepath=str(export/'RI02_Rice.fbx'),use_selection=True,
    apply_unit_scale=True,mesh_smooth_type='FACE',path_mode='COPY',embed_textures=True)
bpy.ops.export_scene.gltf(filepath=str(export/'RI02_Rice.glb'),export_format='GLB',
    use_selection=True,export_apply=True,export_extras=True,export_vertex_color='NONE',export_attributes=True)
info={}
for obj in objects:
    info[obj.name]={'vertices':len(obj.data.vertices),
       'triangles':sum(len(p.vertices)-2 for p in obj.data.polygons),
       'dimensions_m':[round(x,5) for x in obj.dimensions],
       'wind_attribute':list(obj.data.color_attributes.keys())}
info['minTier']='standard'
info['detailObjects']=[]
info['source']=str(outblend.relative_to(root)).replace('\\','/')
info['texture_count']=len(list((root/'art/textures/valley-and-home-v1/RI02/v003').glob('*.png')))
(export/'model_info.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
print('@@RI02PACK@@'+json.dumps({k:v for k,v in info.items() if k.startswith('SM_')},ensure_ascii=False))
