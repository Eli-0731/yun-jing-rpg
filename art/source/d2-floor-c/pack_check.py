"""Whole-pack check for C's 11/15 D2 small-life pack (C-300h-D2-small-life.md, 全包檢查): A (DP01–04 mushrooms), B (DP06–13 moss and
small plants), C (DP14–22 floor smalls) and SH01, set out as (1) a 5 × 5 m forest-floor corner framed like setting view V6 and
(2) a root foot (one of Josh's D2 roots with mushrooms, moss and vines) framed like the lower left of V2.
Blender 4.5.3:  blender -b --factory-startup -P pack_check.py -- --dirs <export dir> [<export dir> ...] --out <dir> [--samples 96]
The export dirs are searched in order for <ID>_v002.glb, then <ID>_v001.glb (and for Josh's DR roots / logs in their sub-folders).
The ground, the puddle water and the fog are preview fixtures only (John's DS01 forest floor and DS03 puddle are not on main).
Every prop sits on what is under it: a ray straight down onto the ground, logs, roots and stumps placed before it."""
import bpy,math,sys,argparse,random
from pathlib import Path
from mathutils import Vector,Matrix,Euler
from mathutils.bvhtree import BVHTree
a=argparse.ArgumentParser();a.add_argument('--dirs',nargs='+');a.add_argument('--out');a.add_argument('--samples',type=int,default=96);a.add_argument('--only')
A=a.parse_args(sys.argv[sys.argv.index('--')+1:]);out=Path(A.out).resolve();out.mkdir(parents=True,exist_ok=True)

def find(pid):
    for d in A.dirs:
        d=Path(d)
        for v in ('v006','v002','v001'):
            for p in (d/f'{pid}_{v}.glb',*d.glob(f'*/{pid}_{v}.glb'),*d.glob(f'{pid}*/{pid}*_{v}.glb')):
                if p.exists():return p
    raise FileNotFoundError(pid)

def setup():
    bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene
    sc.render.engine='CYCLES';sc.cycles.samples=A.samples;sc.cycles.use_denoising=True
    try:
        pr=bpy.context.preferences.addons['cycles'].preferences;pr.compute_device_type='OPTIX';pr.get_devices()
        for d in pr.devices:d.use=d.type=='OPTIX'
        sc.cycles.device='GPU'
    except Exception:sc.cycles.device='CPU'
    sc.render.resolution_x,sc.render.resolution_y=1600,900;sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
    w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;nt=w.node_tree;bg=nt.nodes['Background']   # overcast D2 sky, grey-blue
    bg.inputs['Color'].default_value=(.50,.56,.62,1);bg.inputs['Strength'].default_value=1.15
    bpy.ops.mesh.primitive_cube_add(size=1,location=(0,6,5));fog=bpy.context.object;fog.name='Preview forest haze';fog.scale=(40,40,10.5)   # a bounded haze box (a world volume would swallow the sky)
    fm=bpy.data.materials.new('haze');fm.use_nodes=True;fn=fm.node_tree.nodes;fn.remove(fn['Principled BSDF']);vol=fn.new('ShaderNodeVolumePrincipled')
    vol.inputs['Color'].default_value=(.66,.72,.78,1);vol.inputs['Density'].default_value=.03;fm.node_tree.links.new(vol.outputs[0],fn['Material Output'].inputs['Volume']);fog.data.materials.append(fm)
    sun=bpy.data.objects.new('overcast sun',bpy.data.lights.new('sun','SUN'));sun.data.energy=2.4;sun.data.angle=math.radians(25);sun.data.color=(1.,.95,.88)
    sun.rotation_euler=(math.radians(38),math.radians(8),math.radians(150));sc.collection.objects.link(sun)
    return sc

def mat_noise(name,dark,light,scale,rough,bump):
    m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;b=n['Principled BSDF'];b.inputs['Roughness'].default_value=rough
    t=n.new('ShaderNodeTexNoise');t.inputs['Scale'].default_value=scale;t.inputs['Detail'].default_value=12.;t.inputs['Roughness'].default_value=.72
    r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].color=(*dark,1);r.color_ramp.elements[1].color=(*light,1);r.color_ramp.elements[0].position=.2;r.color_ramp.elements[1].position=.85
    l.new(t.outputs['Fac'],r.inputs[0]);l.new(r.outputs[0],b.inputs['Base Color'])
    bp=n.new('ShaderNodeBump');bp.inputs['Distance'].default_value=bump;bp.inputs['Strength'].default_value=.6;l.new(t.outputs['Fac'],bp.inputs['Height']);l.new(bp.outputs[0],b.inputs['Normal'])
    return m

def ground(size=30,path=None,seed=1):
    """the preview forest floor: wet brown soil, gently uneven; path: (x0,x1) a lighter trodden strip running along y"""
    sc=bpy.context.scene;rng=random.Random(seed);n=120;vs=[];fs=[]
    for j in range(n+1):
        for i in range(n+1):
            x=(i/n-.5)*size;y=(j/n-.5)*size;z=.025*math.sin(1.7*x+.6)*math.cos(1.3*y)+.012*math.sin(5.1*x+3*y)
            if path and path[0]<x<path[1] and -3<y<4:z-=.03*math.sin(math.pi*(x-path[0])/(path[1]-path[0]))
            vs.append((x,y,z))
    fs=[(j*(n+1)+i,j*(n+1)+i+1,(j+1)*(n+1)+i+1,(j+1)*(n+1)+i) for j in range(n) for i in range(n)]
    me=bpy.data.meshes.new('ground');me.from_pydata(vs,[],fs);o=bpy.data.objects.new('Preview forest floor',me);sc.collection.objects.link(o)
    for p in me.polygons:p.use_smooth=True
    me.materials.append(mat_noise('Preview wet soil',(.03,.021,.013),(.15,.10,.065),4,.72,.03));return o

def load(pid,x,y,rot=0.,scale=1.,sink=.004,support=None,tilt=True,z=None):
    """import one export (LOD0 only), turn it by rot about z and set it down on whatever is under (x, y)"""
    sc=bpy.context.scene;before=set(sc.objects);bpy.ops.import_scene.gltf(filepath=str(find(pid)))
    new=[o for o in sc.objects if o not in before]
    for o in list(new):
        if o.type=='MESH' and any(s in o.name for s in ('LOD1','LOD2','Collision')):bpy.data.objects.remove(o);new.remove(o)
    root=bpy.data.objects.new(pid,None);sc.collection.objects.link(root)
    for o in new:
        if o.parent is None:o.parent=root
    if z is None:
        hit=surface(x,y,support);z=hit[0]-sink
        if tilt and hit[1] is not None:
            nz=hit[1];ax=Vector((0,0,1)).cross(nz)
            if ax.length>1e-4 and nz.z>.6:root.rotation_mode='QUATERNION';root.rotation_quaternion=Vector((0,0,1)).rotation_difference(nz)@Euler((0,0,rot)).to_quaternion()
            else:root.rotation_euler.z=rot
        else:root.rotation_euler.z=rot
    else:root.rotation_euler.z=rot
    root.location=(x,y,z);root.scale=(scale,)*3;return root

SUP=[]   # BVH trees of the support surfaces (ground, roots, logs, stumps)
def add_support(obj):
    dg=bpy.context.evaluated_depsgraph_get();bpy.context.view_layer.update()
    for o in ([obj]+list(obj.children_recursive)):
        if o.type!='MESH':continue
        e=o.evaluated_get(dg);me=e.to_mesh();mw=o.matrix_world
        SUP.append(BVHTree.FromPolygons([mw@v.co for v in me.vertices],[tuple(p.vertices) for p in me.polygons]));e.to_mesh_clear()
def surface(x,y,support=None):
    best=(0.,None)
    for t in (support or SUP):
        h=t.ray_cast(Vector((x,y,20)),Vector((0,0,-1)))
        if h[0] is not None and (best[1] is None or h[0].z>best[0]):best=(h[0].z,h[1] if h[1].z>0 else -h[1])
    return best

def puddle(x,y,rx,ry):
    """preview water: a still dark mirror slightly sunk into the soil (DS03 stands in later)"""
    sc=bpy.context.scene;bpy.ops.mesh.primitive_circle_add(vertices=40,radius=1,fill_type='NGON',location=(x,y,surface(x,y)[0]-.004));o=bpy.context.object
    o.scale=(rx,ry,1);rng=random.Random(5)
    for v in o.data.vertices:
        if v.co.length>.5:a_=math.atan2(v.co.y,v.co.x);v.co*=1+.12*math.sin(3*a_+1)+.06*math.sin(7*a_)
    m=bpy.data.materials.new('Preview puddle water');m.use_nodes=True;b=m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value=(.02,.025,.025,1);b.inputs['Roughness'].default_value=.12;b.inputs['IOR'].default_value=1.33;o.data.materials.append(m);return o

def camera(loc,target,lens):
    sc=bpy.context.scene;c=bpy.data.objects.new('cam',bpy.data.cameras.new('cam'));sc.collection.objects.link(c);sc.camera=c
    c.location=loc;c.rotation_euler=(Vector(target)-Vector(loc)).to_track_quat('-Z','Y').to_euler();c.data.lens=lens;c.data.clip_end=200;return c

def shot(name):
    sc=bpy.context.scene;sc.render.filepath=str(out/f'{name}.png');bpy.ops.render.render(write_still=True);print('PACKCHECK',name)

def scatter(rng,ids,n,box,avoid=()):
    for k in range(n):
        for _ in range(30):
            x,y=rng.uniform(box[0],box[1]),rng.uniform(box[2],box[3])
            if all(math.hypot(x-ax,y-ay)>ar for ax,ay,ar in avoid):break
        load(rng.choice(ids),x,y,rng.uniform(0,math.tau))

# ---------------- 1: 5 × 5 m forest corner, framed like V6 (low, along a muddy path; soil bank, stump and broken branches on the
# left, a mossy fallen trunk with ferns, white mushrooms and ground cover on the right; stones, twigs, leaves and a puddle on the path)
def corner():
    setup();SUP.clear();rng=random.Random(1115)
    g=ground(path=(-.55,.55));add_support(g)
    log=load('DR06_FallenTrunk_A',4.6,-1.6,-.79,z=0.);bpy.context.view_layer.update();add_support(log)   # Josh's D2 fallen trunk, lying on the soil
    st=load('DP21_04',-1.75,1.0,.6);add_support(st)
    s2=load('DP21_02',-.7,2.3,2.1);add_support(s2)
    for pid,x,y,r in (('DP15_02',-1.1,.05,.35),('DP15_05',-1.85,-1.25,-.25),('DP15_06',.1,2.05,1.25),('DP20_05',-1.35,-.45,.2),('DP20_06',.25,1.35,.1),
                      ('DP20_03',1.2,-.25,0.),('DP19_03',-.75,.75,1.45),('DP19_02',.95,-1.4,.6),('DP19_01',-.25,.3,2.)):load(pid,x,y,r)
    for pid,x,y,r in (('DP01_02',-1.25,.55,.3),('DP01_03',-1.62,.2,-.4),('DP01_01',-2.05,.75,1.),('DP01_04',-.95,-.1,2.),('DP03_02',-1.95,1.45,-.6),
                      ('DP02_03',1.45,-1.05,.4),('DP02_01',1.15,-.9,1.2),('DP02_02',1.65,-.85,2.3),('DP04_01',1.05,-.15,0.),('DP04_02',-1.5,.9,1.)):load(pid,x,y,r)
    for pid,x,y,r in (('DP06_03',.95,.25,.5),('DP06_05',1.3,-.55,1.),('DP06_02',-1.45,-1.0,.2),('DP06_06',2.1,-.6,0.),('DP06_01',-.55,-1.25,1.5),('DP07_02',.75,-.2,.3),
                      ('DP08_01',-1.3,-1.6,.3),('DP08_02',-2.15,-.55,1.),('DP08_03',2.0,-.25,0.),('DP08_01',2.25,.95,2.),('DP08_02',1.55,1.6,.4),
                      ('DP09_01',1.4,-1.55,0.),('DP09_02',1.85,-1.3,.8),('DP09_04',.9,-1.75,1.6),('DP09_03',-1.75,-.9,.4),('DP11_02',-2.2,1.75,0.),('DP11_01',2.3,1.9,1.),
                      ('DP12_02',1.05,2.35,.3),('DP12_01',-2.3,2.3,1.),('SH01',-2.4,3.2,.5),('DP13_01',-.4,-.2,0.)):load(pid,x,y,r)
    for pid,x,y,r in (('DP17_08',1.05,-.5,.4),('DP17_07',-.35,-1.75,1.),('DP17_06',.35,-1.5,2.2),('DP17_04',-.15,-.95,.3),('DP17_05',-.95,-.55,1.1),
                      ('DP14_06',.75,-.95,.5),('DP14_05',.85,-.75,.3),('DP14_08',.45,-.35,1.3),('DP14_07',-.4,.9,.2),('DP16_06',-1.3,.35,.9),('DP16_05',-1.05,.85,2.)):load(pid,x,y,r)
    load('DP22_01',.05,-.6,.3,sink=0.);puddle(.05,-.6,.32,.22)
    scatter(rng,['DP17_01','DP17_02','DP17_03','DP14_01','DP14_02','DP14_03','DP14_04','DP16_01','DP16_02','DP16_03','DP16_04','DP18_01','DP18_02','DP18_03'],34,(-2.4,2.4,-2.2,2.4),
            avoid=((2.7,0.,.9),(-1.75,1.,.7),(.05,-.6,.35)))
    green=['DP09_01','DP09_02','DP09_03','DP09_04','DP06_01','DP06_06','DP06_02','DP08_01','DP08_02','DP08_03','DP11_01','DP07_02','DP07_05']
    scatter(rng,green,34,(-2.5,-.75,-2.3,2.5),avoid=((-1.75,1.,.75),))   # V6: hardly a bare patch beside the path
    scatter(rng,green,30,(.75,2.5,-2.3,1.2),avoid=((2.7,0.,.9),))
    scatter(rng,['DP09_01','DP09_03','DP06_01','DP04_01','DP04_02','DP13_02'],8,(-.6,.6,-1.,2.2),avoid=((.05,-.6,.4),))
    camera((.15,-2.75,.62),(-.05,1.6,.32),24);shot('v6-corner')
    camera((3.6,-4.6,2.4),(0,.2,0),30);shot('v6-corner-overview')   # the same set from above: the whole 5 × 5 m patch

# ---------------- 2: a root foot framed like the lower left of V2: one of Josh's D2 roots with a row of brown mushrooms along its foot,
# moss on its back, vines hanging off its edge, ferns, ground cover, mossy stones and leaves in front
def rootfoot():
    setup();SUP.clear();rng=random.Random(215)
    g=ground(seed=2);add_support(g)
    rt=load('DR03_RootEnd',0,0,0.,z=0.);bpy.context.view_layer.update();n0=len(SUP);add_support(rt);RT=SUP[n0:]
    def prof(x):   # the root's cross-section at x: (y of its front foot, y and z of its top), found with rays straight down
        foot=None;top=(None,-9.)
        for k in range(400):
            y=-4.+k*.02;z=surface(x,y,RT)[0] if surface(x,y,RT)[1] is not None else -9.
            if foot is None and z>.12:foot=y
            if z>top[1]:top=(y,z)
        return foot,top
    W=[(x,)+prof(x) for x in [-3.+.25*i for i in range(13)]];W=[w for w in W if w[1] is not None]
    print('ROOT profile',[(round(x,2),round(f,2),round(t[1],2)) for x,f,t in W])
    for k,(x,f,t) in enumerate(W[::2]):   # a row of brown mushrooms along the front foot, one cluster at the start of the root
        load(('DP01_03','DP01_01','DP01_03','DP01_04','DP01_03','DP01_02','DP01_03')[k%7],x+rng.uniform(-.06,.06),f-.06,rng.uniform(-.25,.25)+(math.pi if k%2 else 0),support=[SUP[0]])
    for k,(x,f,t) in enumerate(W[1::2]):   # moss on the root's back, a little in front of the crest
        load(('DP06_04','DP07_03','DP06_02','DP07_05','DP06_05','DP06_01')[k%6],x,t[0]-.12,rng.uniform(0,6.3),support=RT)
    for k,(x,f,t) in enumerate(W[2::3]):   # vines hanging off the front: hung from the front face at two-thirds of the root's height, the strands down the face
        yy=f
        for j in range(200):
            yy+=.02;h=surface(x,yy,RT)
            if h[1] is not None and h[0]>t[1]*.66:break
        load(('DP10_02','DP10_04','DP10_01','DP10_02')[k%4],x,yy-.3,math.pi if k%2 else 0.,z=h[0]-(1.51 if k%4 in (0,3) else 1.21 if k%4==1 else .6)*.92,tilt=False)
    x0,x1=W[0][0],W[-1][0];ff=min(w[1] for w in W)
    for pid,x,y,r in (('DP08_02',x0-.3,ff-.7,.4),('DP08_01',x0+.4,ff-1.15,1.),('DP08_03',x0-.6,ff-.25,2.),('DP17_07',x0+1.3,ff-.95,.5),('DP17_04',x0+.9,ff-1.4,1.),
                      ('DP06_06',x0+1.8,ff-.6,0.),('DP09_02',x0+1.1,ff-.45,0.),('DP09_04',x0+2.0,ff-1.05,.7),('DP19_02',x0+.6,ff-.55,.3),('DP04_03',x0+1.5,ff-.2,.4),
                      ('DP02_01',x0+2.6,ff-.15,1.),('DP11_01',x0+2.9,ff-.8,.3)):load(pid,x,y,r,support=[SUP[0]])
    scatter(rng,['DP17_01','DP17_03','DP14_02','DP14_03','DP16_02','DP16_04'],12,(x0-.6,x1,ff-1.7,ff-.3))
    scatter(rng,['DP08_01','DP08_02','DP08_03','DP06_01','DP06_06','DP06_02','DP09_01','DP09_02','DP09_04','DP11_01','DP07_02'],30,(x0-1.2,x1+.3,ff-1.9,ff-.15))   # V2 lower left: ferns and moss right up to the root
    tz=max(w[2][1] for w in W);camera(((x0+x1)/2-.9,ff-3.1,.6),((x0+x1)/2,ff+.6,tz*.4),26);shot('v2-rootfoot')

if A.only in (None,'corner'):corner()
if A.only in (None,'root'):rootfoot()
