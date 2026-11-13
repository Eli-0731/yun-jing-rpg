"""Package the approved TX01 material study into LODs and exportable meshes."""
from pathlib import Path
import bpy, json
from mathutils import Vector

root=Path(__file__).resolve().parents[3]
source=root/'art/source/mountain-city-v1/TX01'
export=root/'art/exports/mountain-city-v1/TX01/v004'
preview=root/'art/previews/mountain-city-v1/TX01/final-v004'
texture=root/'art/textures/mountain-city-v1/TX01/v004'
export.mkdir(parents=True,exist_ok=True);preview.mkdir(parents=True,exist_ok=True)

def count_tri(ob):return sum(len(p.vertices)-2 for p in ob.data.polygons)

def combine(source_objects,name):
    copies=[]
    for src in source_objects:
        obj=src.copy();obj.data=src.data.copy();bpy.context.collection.objects.link(obj)
        obj.parent=None;obj.matrix_world=src.matrix_world.copy();obj.hide_set(False);obj.hide_render=False
        copies.append(obj)
    bpy.ops.object.select_all(action='DESELECT')
    for ob in copies:ob.select_set(True)
    bpy.context.view_layer.objects.active=copies[0]
    bpy.ops.object.join()
    result=bpy.context.object;result.name=name;result.data.name=name+'_Mesh'
    bpy.context.scene.cursor.location=(0,0,0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    return result

def simplify(src,name,ratio):
    ob=src.copy();ob.data=src.data.copy();bpy.context.collection.objects.link(ob)
    ob.name=name;ob.data.name=name+'_Mesh'
    bpy.context.view_layer.objects.active=ob
    mod=ob.modifiers.new('LOD geometry simplification','DECIMATE');mod.ratio=ratio
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return ob

def collision_box(name,center,size):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center)
    ob=bpy.context.object;ob.name=name;ob.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return ob

def export_group(name,objects):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects:ob.select_set(True);ob.hide_set(False)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.fbx(filepath=str(export/(name+'.fbx')),use_selection=True,
        apply_unit_scale=True,bake_space_transform=False,path_mode='AUTO')
    bpy.ops.export_scene.gltf(filepath=str(export/(name+'.glb')),
        export_format='GLB',use_selection=True)

data={}
for file,label in [('TX01-ascension-board-material-v004.blend','Board'),
                   ('TX-Plaque-material-v004.blend','Plaque')]:
    bpy.ops.wm.open_mainfile(filepath=str(source/file))
    for img in bpy.data.images:
        candidate=texture/Path(img.filepath).name
        if candidate.is_file():
            img.filepath=str(candidate)
            img.reload()
    original=[o for o in bpy.data.objects if o.type=='MESH']
    core=[o for o in original if o.name.startswith('SM_')]
    detail=[o for o in original if o.name.startswith('Detail_')]
    assert core, 'source has no main meshes'
    for ob in original:ob.hide_render=True;ob.hide_set(True)
    base=combine(core,f'SM_TX01_{label}_LOD0')
    result=[base]
    if detail:result.append(combine(detail,f'Detail_TX01_{label}_LOD0'))
    result.append(simplify(base,f'SM_TX01_{label}_LOD1',.72))
    result.append(simplify(base,f'SM_TX01_{label}_LOD2',.35))
    if label=='Board':
        result.extend([collision_box('UCX_TX01_Board_Base',(0,0,.20),(7.8,1.95,.40)),
                       collision_box('UCX_TX01_Board_LeftPost',(-3.42,0,2.6),(.36,.40,5.2)),
                       collision_box('UCX_TX01_Board_RightPost',(3.42,0,2.6),(.36,.40,5.2)),
                       collision_box('UCX_TX01_Board_Panel',(0,.12,3.15),(6.35,.24,3.14))])
    else:result.append(collision_box('UCX_TX01_Plaque',(0,0,0),(2.4,.15,.8)))
    for ob in result:
        ob.hide_render=(ob.name!=base.name)
        ob.hide_set(False)
    bpy.ops.wm.save_as_mainfile(filepath=str(source/f'TX01-{label.lower()}-pack-v004.blend'))
    export_group(f'TX01_{label}',result)
    data[label]={'lods':{o.name:count_tri(o) for o in result if o.type=='MESH'},
                 'source_meshes':len(core),'detail_meshes':len(detail)}

    # Neutral three-quarter review at a known eye-height scale. Import QA is
    # performed separately, so this remains a source-model visual preview.
    bpy.ops.object.select_all(action='DESELECT')
    world=bpy.data.worlds.new('TX01_NeutralSky');world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Color'].default_value=(.65,.69,.71,1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=.7
    bpy.context.scene.world=world
    light_data=bpy.data.lights.new('ReviewSun','SUN');light_data.energy=2
    light=bpy.data.objects.new('ReviewSun',light_data);bpy.context.collection.objects.link(light)
    light.rotation_euler=(.55,-.4,-.7)
    cam_data=bpy.data.cameras.new('ReviewCamera');cam=bpy.data.objects.new('ReviewCamera',cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location=(10,-13,8) if label=='Board' else (4,-5,2.2)
    aim=Vector((0,0,2.8)) if label=='Board' else Vector((0,0,.2))
    cam.rotation_euler=(aim-cam.location).to_track_quat('-Z','Y').to_euler()
    cam_data.lens=48;bpy.context.scene.camera=cam
    bpy.context.scene.render.engine='BLENDER_EEVEE'
    bpy.context.scene.render.resolution_x=1200;bpy.context.scene.render.resolution_y=900
    bpy.context.scene.render.filepath=str(preview/f'TX01_{label}_threequarter_v004.png')
    bpy.ops.render.render(write_still=True)

(export/'model_info.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
print('TX01_PACKED',json.dumps(data))
