"""FA01 瀑布卡：先存灰模，再加透明貼圖匯出。"""
from pathlib import Path
import bpy, json

root=Path.cwd()
out=root/'art/exports/sky-and-distance-v1/FA'
out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
scene.unit_settings.scale_length=1.0
# 正面朝 -Y；原點在底部中心；4 m × 40 m。
verts=[(-2,0,0),(2,0,0),(-2,0,40),(2,0,40)]
faces=[(0,1,3),(0,3,2)]
mesh=bpy.data.meshes.new('FA01_CardMesh')
mesh.from_pydata(verts,[],faces);mesh.update()
obj=bpy.data.objects.new('FA01_LOD0',mesh);scene.collection.objects.link(obj)
uv=mesh.uv_layers.new(name='UVMap')
coords={0:(0,0),1:(1,0),2:(0,1),3:(1,1)}
for poly in mesh.polygons:
    for li in poly.loop_indices:uv.data[li].uv=coords[mesh.loops[li].vertex_index]
gray=bpy.data.materials.new('M_FA01_Gray');gray.diffuse_color=(.53,.58,.62,1)
mesh.materials.append(gray)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'FA01_gray.blend'))
mesh.materials.clear()
mat=bpy.data.materials.new('M_FA01_Water');mat.use_nodes=True
mat.surface_render_method='BLENDED'
mat.use_transparency_overlap=False
nodes=mat.node_tree.nodes
bsdf=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
bsdf.inputs['Roughness'].default_value=.9
tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(out/'FA01.png'))
tex.extension='REPEAT';tex.interpolation='Linear'
mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
mat.node_tree.links.new(tex.outputs['Alpha'],bsdf.inputs['Alpha'])
mesh.materials.append(mat)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'FA01.blend'))
bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
bpy.ops.export_scene.gltf(filepath=str(out/'FA01.glb'),export_format='GLB',use_selection=True,export_materials='EXPORT',export_image_format='AUTO')
bpy.ops.export_scene.fbx(filepath=str(out/'FA01.fbx'),use_selection=True,apply_unit_scale=True,axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='FACE',use_triangles=True,add_leaf_bones=False,bake_anim=False)
info={
 'id':'FA01','name':'遠景瀑布卡','units':'m','dimensions_m':[4,0,40],
 'pivot':'底部中心','front':'-Y',
 'reference':'art/references/sky-and-distance-v1/FA01/three-view.png',
 'lods':[{'name':'LOD0','triangles':2,'materials':1,'textures':[{'name':'FA01.png','size':[1024,1024],'channels':'RGBA'}]}],
 'uv_animation':{'axis':'V','speed_uv_per_second':-0.12,'wrap':'Repeat'},
 'status':'Blender 灰模與匯出已完成；Unity 6000.3.28f1 實機未驗'
}
(out/'model_info.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
print('FA01_DONE',len(mesh.polygons),len(mesh.materials),tuple(obj.dimensions))

