"""MM03–06：由已審三視圖擷取的透明中景卡，輸出灰模與遊戲格式。"""
from pathlib import Path
import bpy
import json
import numpy as np
from mathutils import Vector

ROOT=Path.cwd()
OUT=ROOT/'art/exports/midground-v1'
SPECS={
    'MM03':('樹丘甲',150,42),
    'MM04':('樹丘乙',180,55),
    'MM05':('斷崖牆',80,50),
    'MM06':('梯田遠坡',150,40),
}

def build(asset,name,width,target_visible_height):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    scene.unit_settings.system='METRIC'
    scene.unit_settings.scale_length=1
    folder=OUT/asset
    img=bpy.data.images.load(str(folder/(asset+'_Albedo.png')))
    iw,ih=img.size
    pixels=np.empty(iw*ih*4,dtype=np.float32)
    img.pixels.foreach_get(pixels)
    alpha=pixels.reshape(ih,iw,4)[:,:,3]
    ys,xs=np.where(alpha>.12)
    if len(xs)==0: raise ValueError(f'{asset}: empty alpha')
    bottom=ys.min()
    height=target_visible_height*ih/(ys.max()-bottom)
    z0=-height*bottom/ih
    verts=[(-width/2,0,z0),(width/2,0,z0),(width/2,0,z0+height),(-width/2,0,z0+height)]
    mesh=bpy.data.meshes.new(asset+'_CardMesh')
    mesh.from_pydata(verts,[],[(0,1,2),(0,2,3)])
    mesh.update()
    uv=mesh.uv_layers.new(name='UV0')
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            idx=mesh.loops[li].vertex_index
            uv.data[li].uv=((0,0),(1,0),(1,1),(0,1))[idx]
    obj=bpy.data.objects.new(asset+'_LOD0',mesh)
    scene.collection.objects.link(obj)
    gray=bpy.data.materials.new(asset+'_Gray')
    gray.diffuse_color=(.49,.52,.52,1)
    mesh.materials.append(gray)
    bpy.ops.wm.save_as_mainfile(filepath=str(folder/(asset+'_gray.blend')))
    mat=bpy.data.materials.new('M_'+asset+'_Card')
    nodes=mat.node_tree.nodes
    bsdf=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
    tex=nodes.new('ShaderNodeTexImage')
    tex.image=img
    img.pack()
    mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
    mat.node_tree.links.new(tex.outputs['Alpha'],bsdf.inputs['Alpha'])
    bsdf.inputs['Roughness'].default_value=1
    try: mat.surface_render_method='BLENDED'
    except TypeError: mat.surface_render_method='DITHERED'
    mat.use_backface_culling=False
    mesh.materials.clear()
    mesh.materials.append(mat)
    bpy.ops.wm.save_as_mainfile(filepath=str(folder/(asset+'.blend')))
    obj.select_set(True)
    bpy.context.view_layer.objects.active=obj
    bpy.ops.export_scene.gltf(filepath=str(folder/(asset+'.glb')),export_format='GLB',use_selection=True)
    bpy.ops.export_scene.fbx(filepath=str(folder/(asset+'.fbx')),use_selection=True,axis_forward='-Z',axis_up='Y',use_triangles=True,add_leaf_bones=False,bake_anim=False)
    info={'id':asset,'name_zh':name,'units':'m',
          'reference':f'art/references/midground-v1/{asset}/three-view.png',
          'type':'遠景透明卡片','pivot':'可見輪廓底部中央',
          'dimensions_m':[width,0,round(height,2)],
          'visible_height_m':target_visible_height,
          'lods':[{'name':'LOD0','triangles':2,'materials':1,
                   'textures':[{'name':asset+'_Albedo.png','resolution':[iw,ih],'channels':'RGBA'}]}],
          'unity_material':'URP Unlit 或 Lit，Transparent、雙面；Alpha Blend；由核心組實測透明排序',
          'collision':False,'unity_import':'未驗證'}
    (folder/'model_info.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
    # 預覽只含資產與霧色背景，並非實機擺位。
    scene.render.engine='BLENDER_EEVEE'
    scene.render.resolution_x=1200
    scene.render.resolution_y=700
    scene.render.image_settings.file_format='PNG'
    world=bpy.data.worlds.new('ReviewWorld')
    world.use_nodes=True
    bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND')
    bg.inputs['Color'].default_value=(.53,.60,.65,1)
    bg.inputs['Strength'].default_value=.8
    scene.world=world
    cam_data=bpy.data.cameras.new('ReviewCam')
    cam=bpy.data.objects.new('ReviewCam',cam_data)
    scene.collection.objects.link(cam)
    top=height*ys.max()/ih+z0
    cam.location=(0,-width*1.6,max(0,top)/2)
    cam.rotation_euler=(Vector((0,0,max(0,top)/2))-cam.location).to_track_quat('-Z','Y').to_euler()
    cam_data.type='ORTHO'
    cam_data.ortho_scale=max(width*1.10,max(0,top)*1.25*1200/700)
    scene.camera=cam
    light_data=bpy.data.lights.new('ReviewSun','SUN')
    light=bpy.data.objects.new('ReviewSun',light_data)
    scene.collection.objects.link(light)
    light_data.energy=2
    light.rotation_euler=(.3,-.4,.2)
    scene.render.filepath=str(folder/(asset+'_preview.png'))
    bpy.ops.render.render(write_still=True)
    print('DONE',asset,'image',iw,ih,'visible_height',round(top,2))

for key,(name,width,target_height) in SPECS.items():
    build(key,name,width,target_height)
