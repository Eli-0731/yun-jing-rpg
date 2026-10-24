"""Model AFTER approved-process AI reference generation. Run with Blender --background --python.
Source reference set: art/references/irrigation-v1. No external models or textures used.
"""
import bpy, math, json, random
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / 'art/references/irrigation-v1'
for name in ('spirit-bed', 'cistern', 'water-channel'):
    if not (REF / (name + '.png')).exists():
        raise RuntimeError('AI reference sheet required before modeling: ' + name)
OUT = ROOT / 'art/exports/irrigation-v1'
UNITY = ROOT / 'apps/game/Assets/YunJing/Models/Irrigation'
for path in (OUT, UNITY, ROOT/'art/source', ROOT/'art/previews'):
    path.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
random.seed(10424)

def material(name, color, metallic=0, roughness=.78):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    shader=m.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value=(*color,1)
    shader.inputs['Metallic'].default_value=metallic
    shader.inputs['Roughness'].default_value=roughness
    return m
wood=material('Cedar',(.36,.25,.145)); woodlight=material('Cedar endgrain',(.49,.36,.22))
soil=material('Rich soil',(.13,.075,.035)); soilridge=material('Cultivation furrows',(.19,.115,.06))
bronze=material('Aged bronze',(.25,.31,.21),.55,.4)
stone=[material('Warm stone '+str(i),(.43+i*.025,.44+i*.023,.37+i*.022)) for i in range(4)]
water=material('Jade water',(.065,.32,.28),.15,.25)
leafmats=[material('Herb leaf '+str(i),(.17+i*.05,.38+i*.04,.22+i*.04)) for i in range(3)]
moss=material('Moss',(.23,.29,.13))
assets={}; current=[]

def finish(obj,name,mat,bevel=0):
    obj.name=name; obj.data.materials.append(mat)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod=obj.modifiers.new('Soft crafted edges','BEVEL');mod.width=bevel;mod.segments=1
        bpy.ops.object.modifier_apply(modifier=mod.name)
    current.append(obj);return obj
def box(name,loc,size,mat,bevel=.015):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj=bpy.context.object;obj.dimensions=size
    return finish(obj,name,mat,bevel)
def cylinder(name,loc,radius,depth,mat,rotation=(0,0,0),vertices=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc,rotation=rotation)
    return finish(bpy.context.object,name,mat,.005)
def leaf(name,loc,angle,length,mat):
    x,y,z=loc;direction=Vector((math.cos(angle),math.sin(angle),0));side=Vector((-direction.y,direction.x,0))
    base=Vector((x,y,z));tip=base+direction*length+Vector((0,0,length*.5));middle=base+direction*length*.5+Vector((0,0,length*.4))
    verts=[base,middle+side*length*.23,middle+Vector((0,0,.025)),middle-side*length*.23,tip]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],[(0,1,2),(0,2,3),(1,4,2),(2,4,3)])
    mesh.update();obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj);obj.data.materials.append(mat);current.append(obj)
def complete_asset(name):
    # Keep water as a separate render surface; consolidate other parts to reduce object count.
    objects=list(current);joined=[]
    for group in ([obj for obj in objects if obj.data.materials[0]!=water],[obj for obj in objects if obj.data.materials[0]==water]):
        if not group:continue
        bpy.ops.object.select_all(action='DESELECT')
        for obj in group:obj.select_set(True)
        bpy.context.view_layer.objects.active=group[0]
        bpy.ops.object.join();obj=bpy.context.object;obj.name=name+('-water' if obj.data.materials[0]==water else '-mesh')
        bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.025);bpy.ops.object.mode_set(mode='OBJECT')
        joined.append(obj)
    assets[name]=joined;current.clear()

# 2.4 x 3.2 m bed, four furrows, six seedlings per furrow, bronze corner straps.
box('Soil bed',(0,0,.11),(2.12,2.92,.20),soil,.025)
for x in (-1.12,1.12):box('Long cedar border',(x,0,.14),(.16,3.2,.28),wood,.025)
for y in (-1.52,1.52):box('Short cedar border',(0,y,.14),(2.24,.16,.28),wood,.025)
for x in (-1.10,1.10):
    for y in (-1.50,1.50):
        box('Corner post',(x,y,.15),(.20,.20,.30),woodlight,.025)
        box('Bronze strap',(x,y,.17),(.214,.214,.055),bronze,.004)
        for dx in (-.055,.055):cylinder('Strap pin',(x+dx,y-.109,.17),.014,.012,bronze,(math.pi/2,0,0),8)
for row in range(4):
    x=-.78+row*.52;box('Raised furrow',(x,0,.23),(.25,2.76,.065),soilridge,.026)
    for j in range(6):
        y=-1.17+j*.47
        cylinder('Seedling stem',(x,y,.31),.012,.16,leafmats[0],vertices=6)
        for k in range(3):leaf('Herb leaf',(x,y,.31),k*2.094+j*.8,.14+(j%2)*.03,leafmats[k])
complete_asset('spirit-bed')

# Hollow masonry basin. Front is -Y; outlet follows this orientation in exports.
box('Footing',(0,0,.07),(2.0,2.0,.14),stone[1],.035)
for level in range(2):
    z=.14+.36*(level+.5)
    for i in range(3):
        coordinate=-.59+i*.59
        for y in (-.87,.87):box('Masonry front back',(coordinate,y,z),(.575,.20,.35),stone[(i+level)%4],.022)
        for x in (-.87,.87):box('Masonry sides',(x,coordinate,z),(.20,.575,.35),stone[(i+level+1)%4],.022)
box('Basin floor',(0,0,.20),(1.75,1.75,.12),stone[0],.01)
for x in (-.90,.90):box('Rim',(x,0,.96),(.20,2.0,.18),stone[2],.022)
for y in (-.90,.90):box('Rim',(0,y,.96),(1.6,.20,.18),stone[2],.022)
for x in (-.86,.86):
    for y in (-.86,.86):box('Corner cap',(x,y,1.03),(.28,.28,.14),stone[3],.035)
box('Water',(0,0,.895),(1.56,1.56,.015),water,0)
box('Outlet flange',(0,-.985,.35),(.31,.05,.31),bronze,.02)
# Actual hollow pipe mesh with annular lip, rather than a filled cylinder.
verts=[];faces=[];n=16
for y,radius in ((-1.0,.115),(-1.28,.115),(-1.28,.085),(-1.0,.085)):
    verts.extend([(math.cos(i*2*math.pi/n)*radius,y,.35+math.sin(i*2*math.pi/n)*radius) for i in range(n)])
for ring in range(4):
    for i in range(n):faces.append((ring*n+i,ring*n+(i+1)%n,((ring+1)%4)*n+(i+1)%n,((ring+1)%4)*n+i))
mesh=bpy.data.meshes.new('Hollow outlet');mesh.from_pydata(verts,[],faces);mesh.update();obj=bpy.data.objects.new('Hollow outlet',mesh);bpy.context.collection.objects.link(obj);obj.data.materials.append(bronze);current.append(obj)
cylinder('Valve spindle',(0,-1.08,.50),.04,.12,bronze)
box('Wood valve lever',(0,-1.08,.66),(.07,.07,.25),woodlight,.015)
complete_asset('cistern')

# Open-ended channel: no end caps; 2m connection grid.
box('Trough base',(0,0,.04),(.6,2,.08),stone[1],.01)
for x in (-.25,.25):
    for i in range(4):box('Trough side',(x,-.75+i*.5,.16),(.10,.494,.16),stone[i],.008)
box('Flow surface',(0,0,.145),(.395,2,.008),water,0)
for x,y in ((-.285,-.7),(.285,.3),(-.285,.8)):box('Moss patch',(x,y,.085),(.018,.15,.035),moss,.006)
complete_asset('water-channel')

report={'reference_directory':'art/references/irrigation-v1','blender':bpy.app.version_string,'units':'meters','forward':'-Y in Blender; FBX -Z forward, Y up','assets':[]}
for name,objects in assets.items():
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.gltf(filepath=str(OUT/(name+'.glb')),export_format='GLB',use_selection=True,export_apply=True)
    bpy.ops.export_scene.fbx(filepath=str(UNITY/(name+'.fbx')),use_selection=True,object_types={'MESH'},apply_unit_scale=True,axis_forward='-Z',axis_up='Y',bake_anim=False,mesh_smooth_type='FACE')
    triangles=0;vertices=0
    for obj in objects:obj.data.calc_loop_triangles();triangles+=len(obj.data.loop_triangles);vertices+=len(obj.data.vertices)
    assert triangles<10000, (name,triangles)
    report['assets'].append({'name':name,'triangles':triangles,'vertices':vertices,'objects':len(objects),'glb_bytes':(OUT/(name+'.glb')).stat().st_size,'fbx_bytes':(UNITY/(name+'.fbx')).stat().st_size})

# Arrange exported meshes only after exporting each at its own ground-centered origin.
for name,offset in [('spirit-bed',(-2.8,0,0)),('cistern',(.55,.55,0)),('water-channel',(3.0,0,0))]:
    for obj in assets[name]:obj.location=offset
ground=material('Display ground',(.72,.73,.65));box('Preview ground',(0,0,-.08),(200,200,.1),ground,0)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.world.color=(.5,.5,.5)
for name,location,power,size in [('Key',(-3,-4,8),1600,7),('Fill',(5,3,6),1100,6)]:
    bpy.ops.object.light_add(type='AREA',location=location);light=bpy.context.object;light.name=name;light.data.energy=power;light.data.shape='DISK';light.data.size=size;light.rotation_euler=(Vector((0,0,0))-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(8,-12,10));camera=bpy.context.object;camera.rotation_euler=(Vector((0,0,.25))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=11.7;scene.camera=camera
scene.render.filepath=str(ROOT/'art/previews/irrigation-v1.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'art/source/irrigation-v1.blend'))
bpy.ops.render.render(write_still=True)
(OUT/'report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('YUNJING_ASSET_REPORT '+json.dumps(report))
