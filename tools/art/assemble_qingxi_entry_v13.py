"""Small Qingxi entrance composition using existing original assets.

This is an art-review Blender assembly. It does not imply a playable scene.
"""
from pathlib import Path
import json
import math
import bpy
from mathutils import Vector, Matrix

ROOT=Path(__file__).resolve().parents[2]
ASSETS=ROOT/'art/exports'
OUT=ROOT/'art/previews/qingxi-entry-v13'
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'

def collection(name):
    c=bpy.data.collections.new(name);scene.collection.children.link(c);return c

def import_glb(label,path,center,size,ground=0):
    old=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    objects=[o for o in bpy.data.objects if o not in old]
    c=collection(label)
    for o in objects:
        for previous in list(o.users_collection):previous.objects.unlink(o)
        c.objects.link(o)
    # Parent imported root objects to retain source hierarchy.
    roots=[o for o in objects if o.parent not in objects]
    corners=[o.matrix_world@Vector(v) for o in objects if o.type=='MESH' for v in o.bound_box]
    if not corners:raise RuntimeError(f'No mesh in {path}')
    lo=Vector(tuple(min(p[i] for p in corners) for i in range(3)))
    hi=Vector(tuple(max(p[i] for p in corners) for i in range(3)))
    center_source=(lo+hi)/2
    max_extent=max((hi-lo).x,(hi-lo).y)
    scale=size/max_extent
    pivot=bpy.data.objects.new('PIVOT_'+label,None);c.objects.link(pivot)
    for o in roots:o.parent=pivot;o.matrix_parent_inverse=Matrix.Identity(4)
    pivot.scale=(scale,)*3
    pivot.location=(center[0]-center_source.x*scale,center[1]-center_source.y*scale,ground-lo.z*scale)
    return {'file':str(path.relative_to(ROOT)),'scale':round(scale,4),'objects':len(objects)}

report={}
report['road']=import_glb('Road_v12',ASSETS/'qingxi-road-props-v12/qingxi-road-v12.glb',(0,0),12)
report['gate']=import_glb('VillageGate_v13',ASSETS/'qingxi-entry-assets-v13/village-gate-v13.glb',(0,5.9),5.4,.05)
report['guesthouse']=import_glb('ExistingGuesthouse_v1',ASSETS/'qingxi-riverside-house-v1/qingxi-riverside-house-v1.glb',(5.2,1.5),5.6,.05)
report['basket']=import_glb('HerbBasket_v13',ASSETS/'qingxi-entry-assets-v13/herb-basket-v13.glb',(3.1,-1.3),.55,.05)
report['character']=import_glb('Novice_v13',ASSETS/'qingxi-entry-assets-v13/novice-cultivator-v13.glb',(-.4,-2.0),.98,.08)
report['waymarker']=import_glb('ExistingWaymarker_v12',ASSETS/'qingxi-road-props-v12/qingxi-waymarker-v12.glb',(-3.2,1.5),.8,.05)
report['herb-rack']=import_glb('ExistingHerbRack_v12',ASSETS/'qingxi-road-props-v12/qingxi-herb-rack-v12.glb',(3.3,-2.8),1.2,.05)
report['bridge-rail']=import_glb('ExistingBridgeRail_v12',ASSETS/'qingxi-road-props-v12/qingxi-bridge-rail-v12.glb',(-5.4,1.5),2.3,.05)
for i,pos in enumerate(((-2.7,-3.9),(2.6,2.5))):
    report[f'road_dressing_{i}']=import_glb(f'RoadDressing_v13_{i}',ASSETS/'qingxi-entry-assets-v13/road-dressing-v13.glb',pos,2.2,.04)

# Small ground patch and river strip. Existing materials stay intact.
def mat(name,color,rough=.82):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough
    return m
meadow=mat('M_EntryMeadow',(.19,.31,.13));water=mat('M_EntryRiver',(.055,.32,.36),.24)
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,-.13));land=bpy.context.object;land.name='SM_EntryGround'
land.dimensions=(21,20,.23);land.data.materials.append(meadow)
verts=[]
for y in range(-10,11):
    edge=-6.0+.22*math.sin(y*.83)+.12*math.sin(y*2.17)
    verts.extend([(-8.9,y,.027),(edge,y,.027)])
faces=[(2*i,2*i+1,2*i+3,2*i+2) for i in range(20)]
river_mesh=bpy.data.meshes.new('IrregularRiverSurface');river_mesh.from_pydata(verts,[],faces);river_mesh.update()
river=bpy.data.objects.new('SM_IrregularRiverReviewSurface',river_mesh);scene.collection.objects.link(river)
river.data.materials.append(water)

# Reuse the already authored, three-view-backed close-up stones and planting.
kit=ASSETS/'qingxi-detail-props-v2'
for kind,filename,positions,width in (
 ('Boulder','qingxi-moss-boulder-v2.glb',[(-6.2,-6.4),(-6.0,-3.0),(-6.3,1.1),(-5.8,4.1),(-6.0,7.0),(-3.8,-4.1),(3.4,3.7)],.6),
 ('Flowers','qingxi-fern-flower-v2.glb',[(-3.4,-4.4),(-2.9,-1.1),(2.6,-4.4),(3.0,.4),(3.4,3.7),(-5.0,5.4)],.75),
 ('Reeds','qingxi-river-reed-v2.glb',[(-6.0,-7),(-5.9,-4),(-6.1,-1),(-6.0,2),(-6.2,5)],.55),
):
    for i,pos in enumerate(positions):
        report[f'{kind}_{i}']=import_glb(f'{kind}_{i}',kit/filename,pos,width,.055)

# The Tree Companion source, not a generated substitute: append the trunk,
# branches, canopy and bark collections together; retain exact source meshes.
tree_source=ROOT/'art/source/qingxi-world-original-tree-v11.blend'
tree_groups=['生命樹_主體','生命樹_主枝','生命樹_前景葉冠','生命樹_後景葉冠','生命樹_盤根與樹皮']
with bpy.data.libraries.load(str(tree_source),link=False) as (data_from,data_to):
    data_to.collections=[name for name in tree_groups if name in data_from.collections]
tree_c=collection('OriginalTreeCompanion_Reused')
tree_objects=[]
copies={}
for imported in data_to.collections:
    if imported is None:continue
    for original in imported.objects:
        new=original.copy()
        if original.data:new.data=original.data
        tree_c.objects.link(new)
        tree_objects.append(new)
        copies[original]=new
if tree_objects:
    for old,new in copies.items():
        new.parent=copies.get(old.parent)
        new.matrix_parent_inverse=old.matrix_parent_inverse.copy()
        new.matrix_basis=old.matrix_basis.copy()
    bpy.context.view_layer.update()
    corners=[o.matrix_world@Vector(v) for o in tree_objects if o.type=='MESH' for v in o.bound_box]
    lo=Vector(tuple(min(p[i] for p in corners) for i in range(3)))
    hi=Vector(tuple(max(p[i] for p in corners) for i in range(3)))
    factor=5.6/(hi.z-lo.z)
    pivot=bpy.data.objects.new('PIVOT_OriginalTree',None);tree_c.objects.link(pivot)
    for o in tree_objects:
        if o.parent is None:
            world_matrix=o.matrix_world.copy()
            o.parent=pivot
            o.matrix_world=world_matrix
    pivot.scale=(factor,)*3
    pivot.location=(-4.7-(lo.x+hi.x)*.5*factor,5.0-(lo.y+hi.y)*.5*factor,-.65-lo.z*factor)
    report['original_tree']={'source':str(tree_source.relative_to(ROOT)),'objects':len(tree_objects),'scale':round(factor,4)}

world=bpy.data.worlds.new('QingxiMorning');world.use_nodes=True
world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.48,.63,.72,1)
world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.8;scene.world=world
bpy.ops.object.light_add(type='SUN',location=(-3,-4,11));sun=bpy.context.object;sun.data.energy=2.1
sun.rotation_euler=(.50,-.36,-.52)
bpy.ops.object.camera_add(location=(15,-23,16));cam=bpy.context.object
cam.rotation_euler=(Vector((0,0,1.4))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO';cam.data.ortho_scale=25;scene.camera=cam
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=1600;scene.render.resolution_y=1000
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.filepath=str(OUT/'entrance-overview.png')
bpy.ops.render.render(write_still=True)
(OUT/'assembly-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'art/source/qingxi-entry-assembly-v13.blend'))
print(json.dumps(report,ensure_ascii=False))
