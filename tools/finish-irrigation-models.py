"""Refine the three AI-reference-based v1 assets into versioned textured game assets.
Uses original v1 exports; never replaces user-edited Blender source files.
"""
import bpy, bmesh, math, json, hashlib
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parent.parent
REF=ROOT/'art/references/irrigation-v1'
OUT=ROOT/'art/exports/irrigation-v2'
UNITY=ROOT/'apps/game/Assets/YunJing/Models/IrrigationV2'
TEX=UNITY/'Textures'
for name in ('spirit-bed','cistern','water-channel'):
    assert (REF/(name+'.png')).is_file(), 'AI three-view reference required before modeling'
for path in (OUT,TEX,ROOT/'art/source',ROOT/'art/previews'):path.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.bake.margin=8
assets={};report=[]

def select(objects):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]

def material_detail(mat):
    nodes=mat.node_tree.nodes;links=mat.node_tree.links
    shader=nodes.get('Principled BSDF')
    base=tuple(shader.inputs['Base Color'].default_value)
    tex=nodes.new('ShaderNodeTexNoise');tex.inputs['Detail'].default_value=3;tex.inputs['Roughness'].default_value=.7
    coord=nodes.new('ShaderNodeTexCoord');scale=nodes.new('ShaderNodeVectorMath');scale.operation='MULTIPLY'
    name=mat.name.lower()
    if 'cedar' in name:values=(28,2.5,35);strength=.12;contrast=(.35,1.5)
    elif 'soil' in name or 'furrow' in name:values=(35,35,35);strength=.10;contrast=(.45,1.6)
    elif 'stone' in name:values=(11,11,11);strength=.10;contrast=(.55,1.25)
    elif 'water' in name:values=(10,10,3);strength=.025;contrast=(.65,1.5)
    elif 'bronze' in name:values=(19,19,19);strength=.04;contrast=(.35,1.5)
    else:values=(5,5,5);strength=.02;contrast=(.7,1.25)
    scale.inputs[1].default_value=values;links.new(coord.outputs['Generated'],scale.inputs[0]);links.new(scale.outputs[0],tex.inputs['Vector'])
    ramp=nodes.new('ShaderNodeValToRGB')
    for element,value in zip(ramp.color_ramp.elements,contrast):element.color=(*[min(.95,c*value) for c in base[:3]],1)
    links.new(tex.outputs['Fac'],ramp.inputs[0]);links.new(ramp.outputs['Color'],shader.inputs['Base Color'])
    bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.32;bump.inputs['Distance'].default_value=strength
    links.new(tex.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],shader.inputs['Normal'])

def subset(obj,foliage):
    result=obj.copy();result.data=obj.data.copy();bpy.context.collection.objects.link(result)
    bm=bmesh.new();bm.from_mesh(result.data)
    remove=[face for face in bm.faces if ('Herb leaf' in result.data.materials[face.material_index].name)!=foliage]
    bmesh.ops.delete(bm,geom=remove,context='FACES')
    loose=[v for v in bm.verts if not v.link_faces]
    if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
    bm.to_mesh(result.data);bm.free();result.data.update()
    result.name='spirit-bed-foliage' if foliage else 'spirit-bed-body'
    return result

def export(name,objects,lod):
    select(objects);stem=name+('-lod1' if lod else '')
    bpy.ops.export_scene.gltf(filepath=str(OUT/(stem+'.glb')),export_format='GLB',use_selection=True,export_apply=True)
    bpy.ops.export_scene.fbx(filepath=str(UNITY/(stem+'.fbx')),use_selection=True,object_types={'MESH'},apply_unit_scale=True,axis_forward='-Z',axis_up='Y',bake_anim=False,mesh_smooth_type='FACE',path_mode='RELATIVE')
    triangles=0
    for obj in objects:obj.data.calc_loop_triangles();triangles+=len(obj.data.loop_triangles)
    report.append({'name':name,'lod':lod,'triangles':triangles,'objects':[o.name for o in objects],
                   'material_slots':sum(len(o.data.materials) for o in objects),'fbx_bytes':(UNITY/(stem+'.fbx')).stat().st_size})

for name in ('spirit-bed','cistern','water-channel'):
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(ROOT/'art/exports/irrigation-v1'/(name+'.glb')))
    objects=[obj for obj in bpy.data.objects if obj not in before and obj.type=='MESH']
    if name=='spirit-bed':
        original=objects[0];objects=[subset(original,False),subset(original,True)];bpy.data.objects.remove(original,do_unlink=True)
    # Pack all parts together so each model uses one non-overlapping atlas.
    select(objects);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(island_margin=.015);bpy.ops.object.mode_set(mode='OBJECT')
    source_materials=set(mat for obj in objects for mat in obj.data.materials)
    for mat in source_materials:material_detail(mat)
    textures={}
    for channel in ('albedo','normal'):
        img=bpy.data.images.new(name+'-'+channel,width=1024,height=1024,alpha=False)
        if channel=='normal':img.colorspace_settings.name='Non-Color'
        for mat in source_materials:
            node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=img;mat.node_tree.nodes.active=node
        select(objects)
        if channel=='albedo':
            # Emit base color directly: diffuse baking loses the color of metallic bronze.
            temporary=[]
            for mat in source_materials:
                nodes=mat.node_tree.nodes;links=mat.node_tree.links
                shader=nodes.get('Principled BSDF');output=next(n for n in nodes if n.type=='OUTPUT_MATERIAL')
                emission=nodes.new('ShaderNodeEmission')
                links.new(shader.inputs['Base Color'].links[0].from_socket,emission.inputs['Color'])
                links.new(emission.outputs[0],output.inputs['Surface']);temporary.append((mat,shader,output,emission))
            bpy.ops.object.bake(type='EMIT',use_clear=True)
            for mat,shader,output,emission in temporary:
                mat.node_tree.links.new(shader.outputs['BSDF'],output.inputs['Surface']);mat.node_tree.nodes.remove(emission)
        else:bpy.ops.object.bake(type='NORMAL',use_clear=True)
        img.filepath_raw=str(TEX/(name+'-'+channel+'.png'));img.file_format='PNG';img.save();textures[channel]=img
    solid=bpy.data.materials.new(name+'-surface');solid.use_nodes=True
    water=bpy.data.materials.new(name+'-water');water.use_nodes=True
    for mat in (solid,water):
        nodes=mat.node_tree.nodes;links=mat.node_tree.links;shader=nodes.get('Principled BSDF')
        color=nodes.new('ShaderNodeTexImage');color.image=textures['albedo'];links.new(color.outputs['Color'],shader.inputs['Base Color'])
        normal=nodes.new('ShaderNodeTexImage');normal.image=textures['normal'];mapping=nodes.new('ShaderNodeNormalMap')
        links.new(normal.outputs['Color'],mapping.inputs['Color']);links.new(mapping.outputs['Normal'],shader.inputs['Normal'])
        shader.inputs['Roughness'].default_value=.27 if mat==water else .78
        shader.inputs['Metallic'].default_value=.08 if mat==water else 0
        mat.diffuse_color=(.4,.5,.4,1)
    for obj in objects:
        is_water='water' in obj.name and name!='water-channel' or obj.name.endswith('-water')
        # The original channel has distinct "water-channel-mesh" and "water-channel-water".
        obj.data.materials.clear();obj.data.materials.append(water if is_water else solid)
        for face in obj.data.polygons:face.material_index=0
        obj['ai_reference']='art/references/irrigation-v1/'+name+'.png'
        obj['asset_version']='2';obj['game_layer']='foliage' if 'foliage' in obj.name else 'water' if is_water else 'body'
    export(name,objects,0)
    lod=[]
    for obj in objects:
        low=obj.copy();low.data=obj.data.copy();bpy.context.collection.objects.link(low);lod.append(low)
        low.name=obj.name+'-lod1';select([low])
        if obj['game_layer']!='water':
            modifier=low.modifiers.new('LOD1 simplification','DECIMATE');modifier.ratio=.5
            bpy.ops.object.modifier_apply(modifier=modifier.name)
    export(name,lod,1)
    for low in lod:bpy.data.objects.remove(low,do_unlink=True)
    # Hide completed assets during subsequent bakes to avoid accidental intersections.
    for obj in objects:obj.hide_render=True;obj.hide_set(True)
    assets[name]=objects

# Restore and arrange for a real textured asset render, separate from AI reference images.
for name,offset in [('spirit-bed',(-2.8,0,0)),('cistern',(.55,.55,0)),('water-channel',(3,0,0))]:
    for obj in assets[name]:obj.hide_set(False);obj.hide_render=False;obj.location=offset
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.025));ground=bpy.context.object;ground.name='Preview-only ground'
mat=bpy.data.materials.new('Preview ground');mat.diffuse_color=(.15,.19,.18,1);ground.data.materials.append(mat)
scene.world.color=(.23,.28,.32)
for label,location,power,size in [('Key',(-4,-6,8),1000,5),('Fill',(4,2,5),650,4)]:
    bpy.ops.object.light_add(type='AREA',location=location);lamp=bpy.context.object;lamp.name=label;lamp.data.energy=power;lamp.data.shape='DISK';lamp.data.size=size
    lamp.rotation_euler=(Vector((0,0,0))-lamp.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(8,-12,10));camera=bpy.context.object;camera.rotation_euler=(Vector((0,0,.25))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=11.7;scene.camera=camera
scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.view_settings.view_transform='AgX'
scene.render.resolution_x=1800;scene.render.resolution_y=1125;scene.render.resolution_percentage=100
scene.render.filepath=str(ROOT/'art/previews/irrigation-v2.png')
for img in bpy.data.images:
    if img.source=='FILE' and img.filepath:img.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'art/source/irrigation-v2.blend'))
bpy.ops.render.render(write_still=True)
for name,objects in assets.items():
    for group in assets.values():
        for obj in group:obj.hide_render=obj not in objects
    center=objects[0].location+Vector((0,0,.4))
    camera.location=center+Vector((4,-6,5));camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=4.8
    scene.render.resolution_x=1000;scene.render.resolution_y=1000
    scene.render.filepath=str(ROOT/'art/previews'/(name+'-v2.png'));bpy.ops.render.render(write_still=True)
(OUT/'report.json').write_text(json.dumps({'blender':bpy.app.version_string,'references':[{ 'file':str(p.relative_to(ROOT)), 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(REF.glob('*.png'))], 'assets':report},indent=2),encoding='utf8')
print('IRRIGATION_V2_COMPLETE '+json.dumps(report))
