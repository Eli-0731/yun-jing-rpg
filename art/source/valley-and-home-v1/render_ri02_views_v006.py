"""RI02 exported GLB turnarounds, wire, lighting and LOD comparison."""
import bpy
from pathlib import Path
from mathutils import Vector

root=Path(__file__).resolve().parents[3]
out=root/'art/previews/valley-and-home-v1/RI02/v006'
out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(root/'art/exports/valley-and-home-v1/RI02/v006/RI02_Rice.glb'))
rice={o.name:o for o in bpy.data.objects if o.type=='MESH'}
scene=bpy.context.scene
world=bpy.data.worlds.new('RI02 Preview World');scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(0.74,0.76,0.78,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=0.75
light=bpy.data.lights.new('RI02 Shared Area','AREA');lo=bpy.data.objects.new('RI02 Shared Area',light)
bpy.context.collection.objects.link(lo);lo.location=(-3,-5,6);light.energy=1300;light.size=5
camera=bpy.data.cameras.new('RI02 Orthographic');co=bpy.data.objects.new('RI02 Orthographic',camera)
bpy.context.collection.objects.link(co);scene.camera=co;camera.type='ORTHO';camera.ortho_scale=1.55
scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=800;scene.render.resolution_y=800
scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX'
def look(pos,target=(0,0,0.4),scale=1.55):
    co.location=pos;co.rotation_euler=(Vector(target)-co.location).to_track_quat('-Z','Y').to_euler()
    camera.ortho_scale=scale
def show(names):
    for name,obj in rice.items():obj.hide_render=name not in names
def render(name):
    scene.render.filepath=str(out/name);bpy.ops.render.render(write_still=True)
views={'front':(0,-5,1.6),'side':(5,0,1.6),'back':(0,5,1.6),'threequarter':(3.4,-5,2.3)}
for stage in ('Seedling','Green','Golden'):
    show({f'SM_RI02_Rice_{stage}_LOD0'})
    for name,pos in views.items():
        look(pos);render(f'RI02_{stage}_{name}_neutral.png')

# Material override for wireframe without touching the exported materials.
wire=bpy.data.materials.new('RI02 Wire Preview');wire.use_nodes=True
nodes=wire.node_tree.nodes;nodes.clear();links=wire.node_tree.links
output=nodes.new('ShaderNodeOutputMaterial');mix=nodes.new('ShaderNodeMixShader')
links.new(mix.outputs[0],output.inputs['Surface'])
wf=nodes.new('ShaderNodeWireframe');wf.use_pixel_size=True;wf.inputs['Size'].default_value=1.25
links.new(wf.outputs['Fac'],mix.inputs[0])
for idx,color in ((1,(0.53,0.55,0.51,1)),(2,(0.06,0.06,0.06,1))):
    em=nodes.new('ShaderNodeEmission');em.inputs['Color'].default_value=color
    links.new(em.outputs[0],mix.inputs[idx])
scene.view_layers[0].material_override=wire
for stage in ('Green','Golden'):
    show({f'SM_RI02_Rice_{stage}_LOD0'})
    look(views['threequarter']);render(f'RI02_{stage}_threequarter_wire.png')
scene.view_layers[0].material_override=None

# Warmer valley lighting comparison on final GLB materials.
world.node_tree.nodes['Background'].inputs['Color'].default_value=(0.68,0.63,0.54,1)
light.color=(1.0,0.77,0.53);light.energy=1500
for stage in ('Seedling','Green','Golden'):
    show({f'SM_RI02_Rice_{stage}_LOD0'})
    look(views['threequarter']);render(f'RI02_{stage}_threequarter_game_light.png')
world.node_tree.nodes['Background'].inputs['Color'].default_value=(0.74,0.76,0.78,1)
light.color=(1,1,1);light.energy=1300

# LODs and a preview-only neutral 1.75 m scale figure; not part of the asset.
for stage in ('Green','Golden'):
    for lod in range(3):
        show({f'SM_RI02_Rice_{stage}_LOD{lod}'})
        look(views['threequarter']);render(f'RI02_{stage}_LOD{lod}_detail_off.png')

scale_mat=bpy.data.materials.new('Preview Scale Gray');scale_mat.diffuse_color=(0.35,0.36,0.35,1)
scale_mat.use_nodes=True
scale_mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=scale_mat.diffuse_color
def scale_part(name,loc,dim):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    ob=bpy.context.object;ob.name=name;ob.dimensions=dim
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ob.data.materials.append(scale_mat)
scale_part('PREVIEW_ONLY_175cm_torso',(1.5,0,1.13),(0.24,0.11,0.58))
scale_part('PREVIEW_ONLY_175cm_head',(1.5,0,1.58),(0.19,0.15,0.23))
for side in (-1,1):
    scale_part(f'PREVIEW_ONLY_leg_{side}',(1.5+0.067*side,0,0.43),(0.08,0.10,0.86))
    scale_part(f'PREVIEW_ONLY_arm_{side}',(1.5+0.17*side,0,1.11),(0.07,0.09,0.56))
for stage in ('Seedling','Green','Golden'):
    show({f'SM_RI02_Rice_{stage}_LOD0'})
    look((2,-6,2.6),target=(0.75,0,0.85),scale=2.45)
    render(f'RI02_{stage}_with_175cm_scale.png')
print('@@RI02PREVIEWS@@',len(list(out.glob('RI02_*.png'))))
