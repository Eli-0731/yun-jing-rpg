"""D2 look-match shots for the 11/15 standard (00-300h-共同標準.md §三/§四): render the asset under the
local overcast D2 look-development fixture, with wet soil, leaf litter and a root,
so it can sit next to the matching crop of art/references/blocks/D2/V*.png (Eli-0731, Blender 4.5.3 LTS).
  eye     elevated quality review
  crouch  ground-level game prop framing; pass --baseline for a locked v001 / v002 pair
blender -b --factory-startup -P render_d2match.py -- --glb <path> --out <dir> --tag <ID> [--samples 96]
"""
import bpy,math,sys,argparse,random
from pathlib import Path
from mathutils import Vector
a=argparse.ArgumentParser();a.add_argument('--glb');a.add_argument('--out');a.add_argument('--tag');a.add_argument('--samples',type=int,default=96)
a.add_argument('--baseline');a.add_argument('--fig',type=int,default=1);a.add_argument('--small',type=int,default=0)
A=a.parse_args(sys.argv[sys.argv.index('--')+1:]);out=Path(A.out).resolve();out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene
(bpy.ops.import_scene.fbx if A.glb.lower().endswith('.fbx') else bpy.ops.import_scene.gltf)(filepath=A.glb)
for o in list(sc.objects):
    if any(s in o.name for s in ('Collision','_LOD1','_LOD2')):bpy.data.objects.remove(o)
obs=[o for o in sc.objects if o.type=='MESH'];bpy.context.view_layer.update()
pts=[o.matrix_world@Vector(c) for o in obs for c in o.bound_box];lo=Vector([min(p[i] for p in pts) for i in range(3)]);hi=Vector([max(p[i] for p in pts) for i in range(3)])
lo.z=max(lo.z,0.);ctr=(lo+hi)/2;H=hi.z;D=max(hi.x-lo.x,hi.y-lo.y,H)
sc.render.engine='CYCLES';sc.cycles.samples=A.samples;sc.cycles.use_denoising=True
try:
    pr=bpy.context.preferences.addons['cycles'].preferences;pr.compute_device_type='OPTIX';pr.get_devices()
    for d in pr.devices:d.use=d.type=='OPTIX'
    sc.cycles.device='GPU'
except Exception:sc.cycles.device='CPU'
sc.render.resolution_x,sc.render.resolution_y=1280,960;sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Base Contrast'
# overcast sky: grey-blue, low saturation, no hard sun
world=bpy.data.worlds.new('w');sc.world=world;world.use_nodes=True;nt=world.node_tree;bg=nt.nodes['Background']
bg.inputs['Color'].default_value=(.50,.54,.58,1);bg.inputs['Strength'].default_value=1.15
# Local D2 look-development set. These fixtures are used only in previews.
def textured(name,dark,light,scale,roughness,bump):
    material=bpy.data.materials.new(name);material.use_nodes=True
    nodes=material.node_tree.nodes;links=material.node_tree.links
    bsdf=nodes['Principled BSDF'];bsdf.inputs['Roughness'].default_value=roughness
    n=nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=scale
    n.inputs['Detail'].default_value=3.0;n.inputs['Roughness'].default_value=.70
    coord=nodes.new('ShaderNodeTexCoord');links.new(coord.outputs['Object'],n.inputs['Vector'])
    ramp=nodes.new('ShaderNodeValToRGB')
    for entry,pos,c in zip(ramp.color_ramp.elements,(.26,.76),(dark,light)):
        entry.position=pos;entry.color=(*c,1.)
    links.new(n.outputs['Fac'],ramp.inputs[0]);links.new(ramp.outputs['Color'],bsdf.inputs['Base Color'])
    detail=nodes.new('ShaderNodeBump');detail.inputs['Strength'].default_value=.52
    detail.inputs['Distance'].default_value=bump
    links.new(n.outputs['Fac'],detail.inputs['Height']);links.new(detail.outputs[0],bsdf.inputs['Normal'])
    return material

def mesh(name,verts,faces,material):
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
    obj=bpy.data.objects.new(name,data);sc.collection.objects.link(obj);data.materials.append(material)
    return obj

def lit(name,where,aim_at,power,size,color):
    light=bpy.data.objects.new(name,bpy.data.lights.new(name,'AREA'))
    sc.collection.objects.link(light);light.location=where;light.data.energy=power
    light.data.shape='DISK';light.data.size=size;light.data.color=color
    light.rotation_euler=(Vector(aim_at)-light.location).to_track_quat('-Z','Y').to_euler()

ground=textured('Preview wet forest soil',(.018,.012,.007),(.080,.047,.024),40,.76,.012)
stone=textured('Preview fractured grey stone',(.045,.052,.052),(.22,.23,.22),5,.69,.011)
wood=textured('Preview old dark root',(.012,.008,.005),(.062,.041,.021),10,.71,.019)
leaf=textured('Preview dead chestnut leaf',(.045,.024,.008),(.18,.100,.033),6,.80,.004)
sc.view_settings.look='AgX - Medium High Contrast'
bg.inputs['Color'].default_value=(.46,.52,.59,1);bg.inputs['Strength'].default_value=.42
path=nt.nodes.new('ShaderNodeLightPath');back=nt.nodes.new('ShaderNodeBackground')
back.inputs['Color'].default_value=(.023,.042,.032,1);back.inputs['Strength'].default_value=.55
mix=nt.nodes.new('ShaderNodeMixShader')
nt.links.new(path.outputs['Is Camera Ray'],mix.inputs[0])
nt.links.new(bg.outputs[0],mix.inputs[1]);nt.links.new(back.outputs[0],mix.inputs[2])
nt.links.new(mix.outputs[0],nt.nodes['World Output'].inputs[0])
origin=Vector((ctr.x,ctr.y,0))
lit('Diffuse overcast key',origin+Vector((-.46,-.36,.55)),origin,7.,.68,(1.,.95,.86))
lit('Cool forest bounce',origin+Vector((.38,-.51,.28)),origin,2.8,.78,(.83,.91,1.))
lit('Canopy separation',origin+Vector((.04,.63,.69)),origin,9.,.70,(.89,.97,1.))
rng=random.Random(2491)
span=max(.70,D*1.35)
n=61
verts=[]
for iy in range(n):
    for ix in range(n):
        x=(ix/(n-1)-.5)*span*4;y=(iy/(n-1)-.5)*span*4
        # This set has a level contact zone so scale and the pivot remain observable.
        falloff=min(1.,max(0.,(math.hypot(x,y)-D*.47)/(D*.36+.03)))
        z=-.001+falloff*(.009*math.sin(18*x+7*y)*math.cos(13*y-3*x)+rng.uniform(-.004,.004))
        verts.append((ctr.x+x,ctr.y+y,z))
faces=[(j*n+i,j*n+i+1,(j+1)*n+i+1,(j+1)*n+i) for j in range(n-1) for i in range(n-1)]
base=mesh('Preview forest floor',verts,faces,ground)
for f in base.data.polygons:f.use_smooth=True

def rock(x,y,z,sx,sy,sz):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=origin+Vector((x,y,z)))
    o=bpy.context.object;o.name='Preview fractured stone'
    for v in o.data.vertices:
        v.co*=rng.uniform(.84,1.13)
        v.co.x*=sx;v.co.y*=sy;v.co.z*=sz
    o.rotation_euler.z=rng.uniform(-2,2);o.data.materials.append(stone)
    bevel=o.modifiers.new('Worn edges','BEVEL');bevel.width=min(.004,sz*.16);bevel.segments=2

def root():
    verts=[];faces=[]
    rings=33;sides=42
    for i in range(rings):
        u=i/(rings-1);x=(u-.5)*span*2.45;y=span*(.49+.40*math.sin(u*2.7)+.50*u)
        radius=span*(.14+.049*math.sin(u*5.0))
        for j in range(sides):
            a=j*math.tau/sides
            ridges=1+.13*math.sin(9*a+.9*u)+.07*math.sin(17*a-2*u)
            verts.append((ctr.x+x,ctr.y+y+radius*math.cos(a)*ridges,-.03+radius*math.sin(a)*ridges))
    for i in range(rings-1):
        for j in range(sides):
            k=(j+1)%sides
            faces.append((i*sides+j,i*sides+k,(i+1)*sides+k,(i+1)*sides+j))
    o=mesh('Preview furrowed root',verts,faces,wood)
    for f in o.data.polygons:f.use_smooth=True

root()
if A.tag=='DP01_02':
    lit('Wet-soil bounce into the gills',origin+Vector((-.11,-.21,.045)),origin+Vector((0,0,H*.78)),.60,.28,(1.,.91,.78))
if A.tag=='DP06_05':
    # Show the cap's hollow underside seated on a shallow visible stone shoulder.
    rock(0,.015,-H*.12,D*.48,D*.43,H*.40)
for k in range(26):
    a=rng.uniform(0,math.tau);r=rng.uniform(max(.075,D*.53),span*1.28)
    s=rng.uniform(.012,.057)*(1.45 if k<4 else .72)
    rock(math.cos(a)*r,math.sin(a)*r,-s*.24,s,s*rng.uniform(.56,1.),s*rng.uniform(.29,.75))
for k in range(31):
    a=rng.uniform(0,math.tau);r=rng.uniform(max(.075,D*.49),span);size=rng.uniform(.022,.069)
    x=ctr.x+math.cos(a)*r;y=ctr.y+math.sin(a)*r
    theta=rng.uniform(0,math.tau);verts=[]
    for vx,vy,vz in ((-1,0,0),(-.4,.4,.05),(.22,.31,.09),(1,0,.12),(.31,-.27,.06),(-.4,-.35,.04),(.04,0,.20)):
        verts.append((x+size*(vx*math.cos(theta)-vy*math.sin(theta)),y+size*(vx*math.sin(theta)+vy*math.cos(theta)),.002+size*vz))
    mesh('Preview damp fallen leaf',verts,[(i,(i+1)%6,6) for i in range(6)],leaf)
if A.fig:
    bpy.ops.mesh.primitive_cylinder_add(radius=.18,depth=1.75,location=(hi.x+.55,ctr.y+.3,.875));fig=bpy.context.object
    fm=bpy.data.materials.new('fig');fm.use_nodes=True;fm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.30,.42,.55,1);fig.data.materials.append(fm)
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.clip_end=300
def aim(p,t,lens):cam.location=Vector(p);cam.rotation_euler=(Vector(t)-Vector(p)).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
def shot(name):
    sc.render.filepath=str(out/f'{A.tag}-d2-{name}.png')
    bpy.ops.render.render(write_still=True)

before=[]
if A.baseline:
    existing=set(sc.objects)
    bpy.ops.import_scene.gltf(filepath=str(Path(A.baseline).resolve()))
    before=[o for o in sc.objects if o not in existing and o.type=='MESH']
    if not before:raise RuntimeError('Baseline GLB has no mesh')
    for obj in before:obj.hide_render=True

def pair(name):
    shot(name)
    if before:
        for obj in obs:obj.hide_render=True
        for obj in before:obj.hide_render=False
        shot(f'{name}-v001')
        for obj in before:obj.hide_render=True
        for obj in obs:obj.hide_render=False

t=Vector((ctr.x,ctr.y,H*.45))
dist=max(.32 if A.small else 3.5,D*2.45)
aim((ctr.x+dist*.24,ctr.y-dist*.97,(max(.21,H*1.8) if A.small else 1.6)),t,44)
pair('eye')
dc=max(.32 if A.small else 2.0,D*1.72)
height=(H*.38 if A.tag=='DP01_02' else max(.09,H*.86)) if A.small else .6
aim((ctr.x+dc*.30,ctr.y-dc*.95,height),(ctr.x,ctr.y,H*.53),41)
pair('crouch')
print('D2MATCH_DONE',A.tag)
