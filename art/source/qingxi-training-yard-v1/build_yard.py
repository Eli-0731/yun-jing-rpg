"""Original Qingxi prop kit. Run only in a separate background Blender process.
Preserves six independent collections, image PBR maps, UVs and editable bevels.
"""
import bpy,bmesh,math,json,hashlib,random,os
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;PROJECT=ROOT.parents[2]
EXPORT=PROJECT/'art/exports/qingxi-training-yard-v1';PREVIEW=PROJECT/'art/previews/qingxi-training-yard-v1'
TEX=ROOT/'textures';TEX.mkdir(exist_ok=True)
IDS=['training-shelter','qi-striking-post','agility-post','weapon-rack','engraved-training-stone','training-banner']
for name in IDS:assert (PROJECT/'art/references/qingxi-training-yard-v1'/f'{name}-three-view.png').is_file(),name
for ob in list(bpy.data.objects):bpy.data.objects.remove(ob,do_unlink=True)
s=bpy.context.scene;s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True
s.render.resolution_x=1440;s.render.resolution_y=900;s.render.resolution_percentage=100
s.world.color=(.25,.25,.25);s.world.use_nodes=True
s.world.node_tree.nodes.get('Background').inputs[0].default_value=(.35,.43,.46,1)
s.world.node_tree.nodes.get('Background').inputs[1].default_value=.45
s.view_settings.view_transform='AgX'
random.seed(27)
COL=None
def image(name,arr,data=False):
    h,w=arr.shape[:2];a=np.ones((h,w,4),dtype=np.float32)
    a[:,:,:3]=arr[:,:,None] if arr.ndim==2 else arr
    im=bpy.data.images.new(name,width=w,height=h);im.colorspace_settings.name='Non-Color' if data else 'sRGB'
    im.pixels.foreach_set(a.ravel());im.filepath_raw=str(TEX/(name+'.png'));im.file_format='PNG';im.save();im.pack();return im
N=512;y,x=np.mgrid[0:N,0:N].astype(float)/N
rng=np.random.default_rng(27)
noise=np.zeros((N,N))
for freq,amp in [(2,.28),(7,.13),(19,.07),(53,.035),(123,.02)]:
    noise+=amp*np.sin(math.tau*(x*freq+y*(freq*.67))+rng.random()*6)*np.cos(math.tau*(y*freq-x*.31)+rng.random()*6)
def mat(name,color,kind='stone',rough=.8,metal=0):
    m=bpy.data.materials.new(name);nt=m.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
    if kind=='wood':
        # Uneven grain, darker end checks and broad grey weathering patches.
        warp=.035*np.sin(y*17)+.018*np.sin(y*43+x*5)+noise*.08
        phase=(x+warp)*29
        h=.51+.10*np.sin(phase*math.tau)+.04*np.sin(phase*math.tau*2.5)+noise*.45
        h-=.16*np.maximum(0,np.cos((x+warp)*math.tau*73))**30
        h-=.10*np.maximum(0,np.sin(y*math.tau*2.2+x*7))**7
        for cx,cy,rx,ry in [(.29,.35,.065,.085),(.72,.70,.035,.12),(.81,.19,.027,.065)]:
            knot=((x-cx)/rx)**2+((y-cy)/ry)**2
            h-=.17*np.exp(-knot*2.2)
            h+=.08*np.exp(-((np.sqrt(knot)-1.1)/.22)**2)
    elif kind=='cloth':h=.5+.09*np.sin(x*math.tau*140)*np.cos(y*math.tau*140)+noise*.12
    elif kind=='rope':h=.5+.13*np.cos((x*40+y*7)*math.tau)+noise*.15
    elif kind=='leather':h=.49+noise*.42+.08*np.sin((x*53+y*19)*math.tau)
    else:h=.52+noise+.055*rng.standard_normal((N,N))
    rgb=np.clip(np.array(color)[None,None,:]*(.80+.32*h[:,:,None]),0,1)
    if name=='JadeCloth':
        distance=np.sqrt((x-.5)**2+((y-.5)*.92)**2)
        def stripe(d,lo,hi):return np.clip((d-lo)/.003,0,1)*np.clip((hi-d)/.003,0,1)
        print_mask=np.maximum(stripe(distance,.145,.158),stripe(distance,.207,.219))
        print_mask=np.maximum(print_mask,stripe(np.abs(x-.5)+.38*np.abs(y-.5),.152,.161))
        border=np.maximum.reduce([(.035-x)/.005,(x-.965)/.005,(.035-y)/.005,(y-.965)/.005])
        print_mask=np.maximum(print_mask,np.clip(border,0,1))
        rgb=rgb*(1-print_mask[:,:,None])+np.array([.58,.42,.19])[None,None,:]*print_mask[:,:,None]
    base=image(name+'_BaseColor',rgb);r=image(name+'_Roughness',np.clip(rough+(h-.5)*.18,.1,1),True)
    dx=np.roll(h,-1,1)-np.roll(h,1,1);dy=np.roll(h,-1,0)-np.roll(h,1,0)
    normal=np.stack((-dx*.35,-dy*.35,np.ones_like(h)),axis=-1);normal/=np.linalg.norm(normal,axis=-1)[:,:,None]
    ni=image(name+'_Normal',normal*.5+.5,True)
    for im,socket in [(base,'Base Color'),(r,'Roughness')]:
        node=nt.nodes.new('ShaderNodeTexImage');node.image=im;nt.links.new(node.outputs['Color'],bs.inputs[socket])
    node=nt.nodes.new('ShaderNodeTexImage');node.image=ni;n=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(node.outputs['Color'],n.inputs['Color']);nt.links.new(n.outputs['Normal'],bs.inputs['Normal'])
    bs.inputs['Metallic'].default_value=metal;m.diffuse_color=(*color,1)
    return m
WOOD=mat('Elm',(.34,.23,.13),'wood');DARKWOOD=mat('DarkElm',(.21,.135,.075),'wood')
STONE=mat('Limestone',(.44,.46,.43));TILE=mat('BlueClay',(.19,.25,.28),rough=.72)
ROPE=mat('Hemp',(.63,.49,.30),'rope');LEATHER=mat('Leather',(.37,.25,.14),'leather',rough=.65)
JADE=mat('JadeCloth',(.14,.32,.29),'cloth');OCHRE=mat('OchreCloth',(.58,.42,.19),'cloth')
RUST=mat('RustCloth',(.46,.17,.10),'cloth');IRON=mat('Iron',(.16,.17,.16),rough=.52,metal=1)
INLAY=mat('MineralInlay',(.18,.36,.32),rough=.7)
def uv_box(ob):
    uv=ob.data.uv_layers.new(name='UVMap')
    for p in ob.data.polygons:
        normal=p.normal;axis=max(range(3),key=lambda j:abs(normal[j]));axes=[j for j in range(3) if j!=axis]
        for li in p.loop_indices:
            co=ob.data.vertices[ob.data.loops[li].vertex_index].co
            uv.data[li].uv=(co[axes[0]]*.85+.17,co[axes[1]]*.85+.29)
def mesh(name,v,f,material,bevel=0,smooth=False):
    me=bpy.data.meshes.new(name);me.from_pydata(v,[],f);me.update();ob=bpy.data.objects.new(name,me);COL.objects.link(ob);me.materials.append(material)
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free();me.update();uv_box(ob)
    for p in me.polygons:p.use_smooth=smooth
    if bevel:
        m=ob.modifiers.new('Worn edge bevel','BEVEL');m.width=bevel;m.segments=2;m.limit_method='ANGLE'
        n=ob.modifiers.new('Face weighted normals','WEIGHTED_NORMAL');n.keep_sharp=True
    return ob
def box(name,c,d,material,bevel=.01):
    v=[(c[0]+a*d[0]/2,c[1]+b*d[1]/2,c[2]+e*d[2]/2) for a,b,e in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
    return mesh(name,v,[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)],material,bevel)
def beam(name,a,b,w,depth,material=WOOD):
    a,b=Vector(a),Vector(b);ob=box(name,(0,0,0),(w,depth,(b-a).length),material,.012)
    rot=(b-a).to_track_quat('Z','Y');mid=(a+b)/2
    for v in ob.data.vertices:v.co=rot@v.co+mid
    return ob
def cylinder(name,a,b,r,material,segments=16,r2=None,bevel=.003):
    a,b=Vector(a),Vector(b);d=(b-a).normalized();u=d.cross(Vector((0,1,0)) if abs(d.y)<.9 else Vector((1,0,0))).normalized();w=d.cross(u)
    v=[]
    for end,rad in [(a,r),(b,r if r2 is None else r2)]:
        for j in range(segments):v.append(end+rad*(u*math.cos(math.tau*j/segments)+w*math.sin(math.tau*j/segments)))
    f=[tuple(reversed(range(segments))),tuple(range(segments,2*segments))]+[(j,(j+1)%segments,(j+1)%segments+segments,j+segments) for j in range(segments)]
    return mesh(name,v,f,material,bevel,True)
def tube(name,points,r,material,sides=6):
    v=[];f=[]
    for i,p in enumerate(points):
        p=Vector(p);d=(Vector(points[min(i+1,len(points)-1)])-Vector(points[max(i-1,0)])).normalized();u=d.cross(Vector((0,0,1)) if abs(d.z)<.9 else Vector((0,1,0))).normalized();w=d.cross(u)
        for j in range(sides):v.append(p+r*(u*math.cos(math.tau*j/sides)+w*math.sin(math.tau*j/sides)))
        if i:
            for j in range(sides):f.append(((i-1)*sides+j,(i-1)*sides+(j+1)%sides,i*sides+(j+1)%sides,i*sides+j))
    f.extend([tuple(reversed(range(sides))),tuple((len(points)-1)*sides+j for j in range(sides))]);return mesh(name,v,f,material,0,True)
def hanging_loop(name,x):
    # A closed torus avoids collapsed end caps on the narrow leather hanger.
    segments=32;sides=8;v=[];f=[]
    for i in range(segments):
        a=math.tau*i/segments
        for j in range(sides):
            b=math.tau*j/sides
            v.append((x+.011*math.sin(b),-.04+(.063+.011*math.cos(b))*math.cos(a),2.375+(.063+.011*math.cos(b))*math.sin(a)))
    for i in range(segments):
        for j in range(sides):f.append((i*sides+j,i*sides+(j+1)%sides,((i+1)%segments)*sides+(j+1)%sides,((i+1)%segments)*sides+j))
    ob=mesh(name,v,f,ROPE,0,True)
    uv=ob.data.uv_layers.active
    for p in ob.data.polygons:
        for li in p.loop_indices:
            vid=ob.data.loops[li].vertex_index
            uv.data[li].uv=((vid//sides)/segments,(vid%sides)/sides)
    return ob
def leather_seam(name,a,b,radius):
    a,b=Vector(a),Vector(b);d=(b-a).normalized()
    u=d.cross(Vector((0,0,1)) if abs(d.z)<.9 else Vector((0,1,0))).normalized();w=d.cross(u)
    center=b-d*.018;sections=32;sides=6;v=[];f=[]
    for i in range(sections):
        angle=math.tau*i/sections;normal=u*math.cos(angle)+w*math.sin(angle)
        around=-u*math.sin(angle)+w*math.cos(angle)
        for j in range(sides):
            sweep=math.tau*j/sides;v.append(center+normal*(radius+.0025*math.cos(sweep))+d*.0025*math.sin(sweep))
    for i in range(sections):
        for j in range(sides):f.append((i*sides+j,i*sides+(j+1)%sides,((i+1)%sections)*sides+(j+1)%sides,((i+1)%sections)*sides+j))
    mesh(name,v,f,ROPE,0,True)
    for i in range(12):
        angle=math.tau*i/12;normal=u*math.cos(angle)+w*math.sin(angle)
        cylinder('HandStitch',b-d*.038+normal*radius,b-d*.006+normal*radius,.0025,ROPE,6,bevel=0)
def spiral(name,z0,z1,r,turns,material=ROPE):
    n=int(turns*32);return tube(name,[(r*math.cos(math.tau*turns*i/n),r*math.sin(math.tau*turns*i/n),z0+(z1-z0)*i/n) for i in range(n+1)],.009,material)
def stone(name,c,rx,ry,h,seed):
    rand=random.Random(seed);n=20;rs=[1+rand.uniform(-.08,.08) for i in range(n)];v=[]
    for z,k in [(c[2],.92),(c[2]+h*.12,1),(c[2]+h*.88,1),(c[2]+h,.90)]:
        for i in range(n):
            a=math.tau*i/n;v.append((c[0]+rx*rs[i]*math.cos(a)*k,c[1]+ry*rs[i]*math.sin(a)*k,z))
    f=[tuple(reversed(range(n))),tuple(range(3*n,4*n))]
    for row in range(3):
        for i in range(n):f.append((row*n+i,row*n+(i+1)%n,(row+1)*n+(i+1)%n,(row+1)*n+i))
    return mesh(name,v,f,STONE,.012)

def shelter():
    # Platform slabs with narrow actual joints; shallow ramp is walkable.
    box('FoundationBedding',(0,0,.025),(6.15,4.55,.04),STONE,.005)
    for i in range(8):
        for j in range(6):box(f'FoundationSlab_{i}_{j}',(-2.8+i*.8,-2+j*.8,.06),(.792,.792,.12),STONE,.018)
    mesh('EntranceRamp',[(-1.7,-3,.005),(1.7,-3,.005),(-1.7,-2.34,.12),(1.7,-2.34,.12),(-1.7,-2.34,0),(1.7,-2.34,0)],[(0,1,3,2),(0,4,5,1),(0,2,4),(1,5,3),(2,3,5,4)],STONE,.008)
    for x in [-2.4,2.4]:
        for y in [-1.8,1.8]:
            box('PostFoot',(x,y,.25),(.55,.55,.26),STONE,.035)
            cylinder('PostPlinth',(x,y,.34),(x,y,.46),.255,STONE,16)
            cylinder('ElmPost',(x,y,.40),(x,y,2.77),.175,WOOD,12,r2=.155)
            for dx in [-.48,.48]:beam('KneeBrace',(x,y,2.29),(x+dx,y,2.78),.12,.13,DARKWOOD)
            for dy in [-.43,.43]:beam('SideBrace',(x,y,2.35),(x,y+dy,2.75),.12,.13,DARKWOOD)
            cylinder('JoineryPeg',(x-.20,y-.01,2.59),(x+.20,y-.01,2.59),.026,DARKWOOD,12)
    for y in [-1.8,1.8]:box('LongBeam',(0,y,2.75),(5.55,.24,.28),WOOD,.025)
    for x in [-2.4,2.4]:
        box('TieBeam',(x,0,2.85),(.26,4.25,.25),WOOD,.018)
        beam('GableRafter',(x,-2.35,2.89),(x,0,3.60),.15,.15)
        beam('GableRafter',(x,0,3.60),(x,2.35,2.89),.15,.15)
        box('KingPost',(x,0,3.24),(.14,.14,.69),WOOD,.012)
    for y in [-1.7,-.85,0,.85,1.7]:box('RoofPurlin',(0,y,3.60-abs(y)*.30),(6.10,.13,.14),DARKWOOD,.01)
    for x in np.linspace(-2.95,2.95,20):
        if abs(abs(x)-2.4)<.20:continue
        for sign in [-1,1]:beam('ExposedRafter',(x,0,3.61),(x,sign*2.35,2.89),.095,.105,DARKWOOD)
    def roof(y):return 3.72-.92*abs(y)/2.4+.16*(abs(y)/2.4)**5
    # Closed curved sheets under individually curved ceramic tile channels.
    for sign in [-1,1]:
        v=[]
        for dz in [0,-.045]:
            for x in [-3.2,3.2]:
                for j in range(17):y=sign*2.4*j/16;v.append((x,y,roof(y)+dz))
        f=[]
        for j in range(16):f.extend([(j,j+1,17+j+1,17+j),(34+j,51+j,51+j+1,34+j+1),(j,34+j,34+j+1,j+1),(17+j,17+j+1,51+j+1,51+j)])
        f.extend([(0,17,51,34),(16,50,67,33)]);mesh('RoofBed',v,f,TILE)
        for row in range(9):
            y0=sign*(row*.264+.025);y1=sign*min(2.43,(row+1)*.264+.021)
            for k in range(25):
                xc=-3.07+k*.256;v=[]
                for yy in [y0,y1]:
                    for j in range(7):
                        a=math.pi*j/6;v.append((xc+.12*math.cos(a),yy,roof(yy)-.003+.070*math.sin(a)))
                    for j in range(7):
                        a=math.pi*j/6;v.append((xc+.105*math.cos(a),yy,roof(yy)-.003+.053*math.sin(a)))
                f=[]
                for j in range(6):f.extend([(j,j+1,14+j+1,14+j),(7+j,21+j,21+j+1,7+j+1),(j,7+j,7+j+1,j+1),(14+j,14+j+1,21+j+1,21+j)])
                f.extend([(0,14,21,7),(6,13,27,20)]);mesh('CeramicTile',v,f,TILE,0,True)
    cylinder('RidgeCap',(-3.25,0,3.77),(3.25,0,3.77),.095,TILE,16)
    for x in [-3.24,3.24]:
        tube('RidgeFinial',[(x,0,3.73),(x+math.copysign(.08,x),0,3.80),(x+math.copysign(.10,x),0,3.88)],.07,TILE,8)

def qi_post():
    for x in [-.165,.165]:
        for y in [-.165,.165]:box('SplitStoneFoot',(x,y,.13),(.32,.32,.26),STONE,.025)
    cylinder('OctagonalTrunk',(0,0,.12),(0,0,1.65),.172,WOOD,8,r2=.156)
    for a,b in [(.36,.52),(.72,.91),(1.08,1.27)]:spiral('ReplaceableHempWrap',a,b,.176,round((b-a)/.019))
    for y in [-.225,.225]:box('RetainingWedge',(0,y,.24),(.11,.09,.32),DARKWOOD,.008)
    cylinder('BreathMedallion',(0,-.150,1.47),(0,-.176,1.47),.065,INLAY,32)
    tube('CarvedSpiral',[(.047*(1-i/125)*math.cos(i/110*math.tau*2.2),-.181,1.47+.047*(1-i/125)*math.sin(i/110*math.tau*2.2)) for i in range(111)],.003,ROPE)
    for z in [1.32,1.37,1.42]:cylinder('RhythmDot',(0,-.157,z),(0,-.170,z),.012,IRON,12)

def agility():
    for sign in [-1,1]:beam('CrossFoot',(-.44,sign*.32,.08),(.44,-sign*.32,.08),.16,.16,DARKWOOD)
    cylinder('DummyTrunk',(0,0,.10),(0,0,1.60),.135,WOOD,16,r2=.12)
    cylinder('TopLeatherCap',(0,0,1.49),(0,0,1.65),.127,LEATHER,24)
    leather_seam('TopCapSeam',(0,0,1.49),(0,0,1.65),.127)
    spiral('TopBinding',1.45,1.49,.137,3)
    for side in [-1,1]:
        a=(side*.04,0,1.12);b=(side*.48,-.24,1.16)
        cylinder('BlockingArm',a,b,.057,WOOD,12)
        pad_a=(side*.42,-.21,1.154);pad_b=(side*.535,-.267,1.165)
        cylinder('LeatherPad',pad_a,pad_b,.082,LEATHER,20)
        leather_seam('PadSeam',pad_a,pad_b,.082)
        if side<0:cylinder('RedTimingWrap',(-.22,-.105,1.136),(-.39,-.19,1.152),.066,RUST,16)
        box('Socket',(side*.13,-.01,1.12),(.09,.20,.19),DARKWOOD,.009)
    cylinder('LowBar',(0,0,.47),(0,-.35,.35),.058,WOOD,12)
    cylinder('LowBarPad',(0,-.30,.37),(0,-.44,.32),.079,LEATHER,16)
    leather_seam('LowBarSeam',(0,-.30,.37),(0,-.44,.32),.079)
    for z in [.46,1.12]:cylinder('RetainingPin',(-.19,.04,z),(.19,.04,z),.022,DARKWOOD,12)

def rack():
    for x in [-.78,.78]:
        box('StableFoot',(x,0,.075),(.24,.65,.15),WOOD,.035)
        box('RackUpright',(x,0,.865),(.13,.14,1.57),WOOD,.02)
        for z in [.25,1.48]:box('IronStrap',(x,-.077,z),(.14,.015,.055),IRON,.006)
        for z in [.46,1.36]:cylinder('WoodenPeg',(x,-.105,z),(x,-.06,z),.025,DARKWOOD,12)
    # Profile includes five actual shallow semicircular notches, not decals.
    for z in [.46,1.36]:
        profile=[(-.9,z-.075),(.9,z-.075),(.9,z+.075)]
        for center in reversed([-.52,-.26,0,.26,.52]):
            profile.append((center+.09,z+.075))
            for j in range(1,13):
                a=math.pi*j/12;profile.append((center+.09*math.cos(a),z+.075-.075*math.sin(a)))
        profile.append((-.9,z+.075));n=len(profile);v=[(x,y,h) for y in [-.055,.055] for x,h in profile]
        f=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        mesh('NotchedRail',v,f,WOOD,.006)

def training_stone():
    # Rings built into top surface, with recessed teal mineral fill.
    n=96;radii=[.03,.13,.16,.175,.181,.19,.32,.33,.34,.49,.50,.51,.68,.69,.70,.87,1]
    v=[];f=[]
    def edge(a):return 1+.025*math.sin(a*5)+.018*math.cos(a*9)
    for r in radii:
        for j in range(n):
            a=math.tau*j/n;z=.278-(.012 if r in [.175,.181,.33,.50,.69] else 0)
            v.append((.90*r*edge(a)*math.cos(a),.75*r*edge(a)*math.sin(a),z))
    f.append(tuple(reversed(range(n))))
    for row in range(len(radii)-1):
        for j in range(n):f.append((row*n+j,row*n+(j+1)%n,(row+1)*n+(j+1)%n,(row+1)*n+j))
    for j in range(n):
        a=math.tau*j/n;v.append((.90*.96*edge(a)*math.cos(a),.75*.96*edge(a)*math.sin(a),0))
        f.append(((len(radii)-1)*n+j,(len(radii)-1)*n+(j+1)%n,len(radii)*n+(j+1)%n,len(radii)*n+j))
    f.append(tuple(reversed(range(len(radii)*n,(len(radii)+1)*n))))
    ob=mesh('EngravedSlab',v,f,STONE,0);ob.data.materials.append(INLAY)
    for p in ob.data.polygons:
        if all(abs(ob.data.vertices[i].co.z-.266)<.0001 for i in p.vertices):p.material_index=1
    for quarter in range(4):
        angle=math.tau*quarter/4;ca,sa=math.cos(angle),math.sin(angle)
        outline=[(0,.021),(.022,.045),(.018,.078),(0,.111),(-.018,.078),(-.022,.045)]
        top=[(.90*(xx*ca-yy*sa),.75*(xx*sa+yy*ca),.2792) for xx,yy in outline]
        bot=[(xx,yy,.275) for xx,yy,_ in top]
        count=len(outline)
        faces=[tuple(range(count)),tuple(reversed(range(count,2*count)))]+[(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
        mesh('FourPetalInlay',top+bot,faces,INLAY)

def banner():
    stone('BannerStone',(0,0,0),.275,.275,.25,34)
    box('PoleSocket',(0,0,.29),(.14,.14,.17),IRON,.015)
    cylinder('BannerPole',(0,0,.28),(0,0,2.61),.037,WOOD,16,r2=.028)
    cylinder('Crossbar',(-.46,0,2.40),(.46,0,2.40),.034,WOOD,16)
    cylinder('Finial',(0,0,2.60),(0,0,2.65),.047,OCHRE,16,r2=.025)
    vs=[];fs=[];nx=32;ny=50
    for row in range(ny+1):
        t=row/ny
        for j in range(nx+1):
            u=j/nx;vs.append((-.35+.70*u,-.095+.045*math.sin(u*math.tau*2+t*2)*t,2.34-1.40*t-.018*t**8*math.sin(u*25)**2))
    for row in range(ny):
        for j in range(nx):a=row*(nx+1)+j;fs.append((a,a+1,a+nx+2,a+nx+1))
    ob=mesh('JadeBannerCloth',vs,fs,JADE,0,True)
    uv=ob.data.uv_layers.active
    for p in ob.data.polygons:
        for li in p.loop_indices:
            v=ob.data.vertices[ob.data.loops[li].vertex_index].co;uv.data[li].uv=((v.x+.35)/.70,(v.z-.94)/1.4)
    m=ob.modifiers.new('Fabric thickness','SOLIDIFY');m.thickness=.003
    for x in [-.28,.28]:hanging_loop('BannerHangingLoop',x)

builders=[shelter,qi_post,agility,rack,training_stone,banner]
for name,build in zip(IDS,builders):
    COL=bpy.data.collections.new(name);s.collection.children.link(COL);build()
    for ob in COL.objects:ob['asset_id']=name;ob['author']='Johnnnny0823 / Codex';ob['source']='Original geometry from saved AI three-view; no third-party model'
    print('BUILT',name,len(COL.objects),flush=True)
# Save editable source before exports; collection transforms remain at local origin.
s['scope']='Six independent Qingxi training props, original kit; Unity not tested'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Qingxi_Training_Yard_v1.blend'))
report={}
for name in IDS:
    bpy.ops.object.select_all(action='DESELECT');obs=list(bpy.data.collections[name].objects)
    for ob in obs:ob.select_set(True)
    bpy.context.view_layer.objects.active=obs[0];bpy.context.view_layer.update()
    points=[ob.matrix_world@Vector(c) for ob in obs for c in ob.bound_box]
    dims=[max(p[j] for p in points)-min(p[j] for p in points) for j in range(3)]
    report[name]={'dimensions_m':dims,'origin':'ground center','forward':'Blender -Y; glTF +Z','mesh_parts':len(obs),'control_triangles':sum(sum(len(p.vertices)-2 for p in ob.data.polygons) for ob in obs)}
    if os.environ.get('YARD_EXPORT','1')=='1':
        bpy.ops.export_scene.gltf(filepath=str(EXPORT/(name+'.glb')),export_format='GLB',use_selection=True,export_apply=True,export_yup=True)
(EXPORT/'asset-manifest.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('BUILD_COMPLETE',json.dumps(report),flush=True)
