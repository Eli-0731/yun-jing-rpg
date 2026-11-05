"""UP05_Burner, the small bronze incense burner of the qi lesson set. Blender 4.5.3, run from the repository root:
  blender -b --factory-startup -P art/source/qingxi-day34-c/build_up05_burner.py
Built by Codex (GPT-6-Astra, reasoning high, 2026-11-05) from the chosen reference art/references/qingxi-day34-c/UP05/v2/UP05-v2-cand-4.png,
then wired into the day 3-4 package (names, texture set, model_info) so it replaces the build_day34.py burner. No external meshes or photos.
"""
import bpy,bmesh,math,json
from pathlib import Path
from mathutils import Vector
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'art/source/qingxi-day34-c'
OUT=ROOT/'art/exports/qingxi-day34-c'
TEX=ROOT/'art/textures/qingxi-day34-c'
for d in (SRC,OUT,TEX):d.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=1
bpy.context.preferences.filepaths.save_version=0
TAU=2*math.pi;parts=[]
roles=['body','rim','relief','leg','ear','ash','incense','char']
dummy=[bpy.data.materials.new('paint_zone_'+r) for r in roles]
def mesh(name,vs,fs,role,smooth=True):
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update()
    ob=bpy.data.objects.new(name,me);sc.collection.objects.link(ob)
    me.materials.append(dummy[roles.index(role)])
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]);bm.to_mesh(me);bm.free()
    for p in me.polygons:p.use_smooth=smooth
    parts.append(ob);return ob

def lathe(name,profile,n,role):
    vs=[];fs=[];rings=[]
    for r,z in profile:
        if r==0:rings.append([len(vs)]);vs.append((0,0,z))
        else:
            rings.append(list(range(len(vs),len(vs)+n)))
            vs.extend((r*math.cos(TAU*j/n),r*math.sin(TAU*j/n),z) for j in range(n))
    for a,b in zip(rings,rings[1:]):
        for j in range(n):
            k=(j+1)%n
            if len(a)==1:fs.append((a[0],b[j],b[k]))
            elif len(b)==1:fs.append((a[j],b[0],a[k]))
            else:fs.append((a[j],b[j],b[k],a[k]))
    return mesh(name,vs,fs,role)

profile=[(0,.026),(.025,.026),(.038,.028),(.049,.033),(.058,.040),(.064,.049),
 (.067,.058),(.0665,.067),(.063,.076),(.057,.083),(.0565,.086),(.062,.087),
 (.066,.089),(.067,.091),(.067,.093),(.0655,.095),(.061,.095),(.0595,.093),
 (.0595,.090),(.0545,.086),(.054,.080),(.058,.069),(.059,.058),(.054,.047),
 (.043,.038),(.025,.036),(0,.036)]
body=lathe('Cast_bowl',profile,96,'body');body.data.materials.append(dummy[1])
for p in body.data.polygons:
    if p.center.z>.0865:p.material_index=1

def radius_at(z):return np.interp(z,[p[1] for p in profile[:11]],[p[0] for p in profile[:11]])
def rounded_rect(hw,hh,c,steps=6):
    pts=[]
    for cx,cy,start in [(hw-c,hh-c,0),(-hw+c,hh-c,90),(-hw+c,-hh+c,180),(hw-c,-hh+c,270)]:
        for j in range(steps):
            a=math.radians(start+j*90/(steps-1));pts.append((cx+c*math.cos(a),cy+c*math.sin(a)))
    return pts

def relief(name,angle,hw,hh,corner,tube,zc,steps=6):
    path=rounded_rect(hw,hh,corner,steps);vs=[];fs=[];cross=6
    for k,(s,zz) in enumerate(path):
        tangent=(Vector(path[(k+1)%len(path)])-Vector(path[k-1])).normalized()
        across=Vector((tangent.y,-tangent.x))
        for j in range(cross):
            ph=TAU*j/cross;ss=s+across.x*tube*math.cos(ph);z=zc+zz+across.y*tube*math.cos(ph)
            a=angle+ss/.066;r=float(radius_at(z))+.00015+tube*math.sin(ph)
            vs.append((r*math.cos(a),r*math.sin(a),z))
    for k in range(len(path)):
        for j in range(cross):fs.append((k*cross+j,k*cross+(j+1)%cross,((k+1)%len(path))*cross+(j+1)%cross,((k+1)%len(path))*cross+j))
    return mesh(name,vs,fs,'relief')
for k in range(8):
    a=-math.pi/2+k*TAU/8
    relief('Belly_frame_%02d'%k,a,.018,.011,.006,.00135,.060)
    relief('Inset_pill_%02d'%k,a,.009,.0038,.0034,.0010,.060,5)

for k in range(3):
    a=-math.pi/2+k*TAU/3;vs=[];fs=[];n=12
    for z,r,w,d in [(0,.054,.0062,.0055),(.002,.054,.0068,.006),(.005,.052,.0055,.005),
                     (.014,.049,.0058,.0057),(.025,.046,.008,.0075),(.034,.045,.009,.008)]:
        for j in range(n):
            t=TAU*j/n;rr=r+d*math.cos(t);side=w*math.sin(t)
            vs.append((rr*math.cos(a)-side*math.sin(a),rr*math.sin(a)+side*math.cos(a),z))
    for ring in range(5):
        for j in range(n):fs.append((ring*n+j,ring*n+(j+1)%n,(ring+1)*n+(j+1)%n,(ring+1)*n+j))
    fs.extend([tuple(reversed(range(n))),tuple(range(5*n,6*n))]);mesh('Foot_%d'%k,vs,fs,'leg')

for sign in (-1,1):
    x0=sign*.063;outer=[(-.012,.088),(.012,.088),(.012,.120),(-.012,.120)]
    inner=[(-.006,.094),(.006,.094),(.006,.114),(-.006,.114)];vs=[];fs=[]
    for y in (-.0045,.0045):
        for contour in (outer,inner):vs.extend((sign*(.063+(z-.088)/.032*.0075)+y,x,z) for x,z in contour)
    for j in range(4):
        k=(j+1)%4
        fs.extend([(j,k,4+k,4+j),(8+j,12+j,12+k,8+k),(j,8+j,8+k,k),(4+j,4+k,12+k,12+j)])
    ob=mesh('Square_ear_'+str(sign),vs,fs,'ear',False)
    bpy.context.view_layer.objects.active=ob;ob.select_set(True)
    mod=ob.modifiers.new('Cast_edge_rounding','BEVEL');mod.width=.0009;mod.segments=2
    bpy.ops.object.modifier_apply(modifier=mod.name);ob.select_set(False)
    for p in ob.data.polygons:p.use_smooth=True
    mod=ob.modifiers.new('Weighted_corner_normals','WEIGHTED_NORMAL');mod.keep_sharp=True;mod.weight=30
    bpy.ops.object.modifier_apply(modifier=mod.name)

def ash_z(x,y):
    rr=np.sqrt(x*x+y*y)
    return .0856+.0042*np.maximum(0,1-(rr/.055)**2)+.00012*np.sin(x*620+y*211)*np.sin(y*511-x*187)+.0012*np.exp(-((x+.012)/.014)**2-((y-.006)/.017)**2)
vs=[(0,0,float(ash_z(0,0)))];fs=[];n=64;nr=6
for ring in range(1,nr+1):
    for j in range(n):
        a=TAU*j/n;r=.055*ring/nr;x=r*math.cos(a);y=r*math.sin(a);vs.append((x,y,float(ash_z(x,y))))
for j in range(n):fs.append((0,1+j,1+(j+1)%n))
for ring in range(nr-1):
    s=1+ring*n
    for j in range(n):fs.append((s+j,s+n+j,s+n+(j+1)%n,s+(j+1)%n))
last=1+(nr-1)*n;bottom=len(vs);vs.append((0,0,.083))
for j in range(n):fs.append((last+j,bottom,last+(j+1)%n))
mesh('Incense_ash',vs,fs,'ash')
rng=np.random.default_rng(405)
for i in range(22):
    a=float(rng.uniform(0,TAU));r=float(rng.uniform(.006,.044));x=r*math.cos(a);y=r*math.sin(a)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(x,y,float(ash_z(x,y))-.0003))
    ob=bpy.context.object;ob.name='Embedded_ash_clump_%02d'%i
    ob.scale=(float(rng.uniform(.0013,.0031)),float(rng.uniform(.001,.0026)),float(rng.uniform(.0008,.0020)))
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    ob.data.materials.append(dummy[5]);parts.append(ob)
for i,(x,y,h,dx,dy) in enumerate([(-.014,.003,.013,-.001,.0004),(.003,.014,.017,.0004,-.0009),(.015,-.009,.010,.0009,.0004)]):
    z=float(ash_z(x,y))-.0015;n=10;vs=[];fs=[]
    for level,r in [(0,.00115),(.80,.00110),(1,.0010)]:
        for j in range(n):
            t=TAU*j/n;vs.append((x+dx*level+r*math.cos(t),y+dy*level+r*math.sin(t),z+h*level))
    for ring in range(2):
        for j in range(n):fs.append((ring*n+j,ring*n+(j+1)%n,(ring+1)*n+(j+1)%n,(ring+1)*n+j))
    fs.extend([tuple(reversed(range(n))),tuple(range(2*n,3*n))])
    ob=mesh('Burnt_incense_%d'%i,vs,fs,'incense');ob.data.materials.append(dummy[7])
    for p in ob.data.polygons:
        if p.center.z>z+h*.79:p.material_index=1
bpy.ops.object.select_all(action='DESELECT')
for ob in parts:ob.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join();lod0=bpy.context.object;lod0.name='UP05_Burner_Burner_LOD0'
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
bm=bmesh.new();bm.from_mesh(lod0.data);bmesh.ops.triangulate(bm,faces=bm.faces[:]);bm.to_mesh(lod0.data);bm.free()
for p in lod0.data.polygons:p.select=lod0.data.materials[p.material_index].name not in ('paint_zone_body','paint_zone_rim')
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.009,area_weight=.1,correct_aspect=True,scale_to_bounds=True)
bpy.ops.object.mode_set(mode='OBJECT')
# Give the vessel a continuous, high-density cylindrical strip in the lower 60%.
# Remaining individually unwrapped parts share the upper 37%, with padded gutters.
uvdata=lod0.data.uv_layers.active.data
pr=np.array(profile,dtype=float);s=np.zeros(len(pr));s[1:]=np.cumsum(np.linalg.norm(np.diff(pr,axis=0),axis=1));s/=s[-1]
for poly in lod0.data.polygons:
    if lod0.data.materials[poly.material_index].name in ('paint_zone_body','paint_zone_rim'):
        positions=[lod0.data.vertices[j].co for j in poly.vertices]
        radii=[math.hypot(p.x,p.y) for p in positions]
        us=[math.atan2(p.y,p.x)%TAU/TAU if r>1e-6 else None for p,r in zip(positions,radii)]
        nonzero=[v for v in us if v is not None]
        if max(nonzero)-min(nonzero)>.5:us=[v+1 if v is not None and v<.5 else v for v in us]
        mid=sum(v for v in us if v is not None)/len(nonzero)
        for loop,p,r,u in zip(poly.loop_indices,positions,radii,us):
            j=int(np.argmin((pr[:,0]-r)**2+(pr[:,1]-p.z)**2))
            uvdata[loop].uv=(.015+.97*(mid if u is None else u),.015+.585*s[j])
    else:
        for loop in poly.loop_indices:
            u,v=uvdata[loop].uv;uvdata[loop].uv=(.015+.97*u,.625+.36*v)
print('PAINTING_ATLAS',len(lod0.data.polygons),flush=True)
N=1024
albedo=np.zeros((N,N,4),np.float32);normal=np.zeros_like(albedo);orm=np.zeros_like(albedo);used=np.zeros((N,N),bool)
srng=np.random.default_rng(123);strokes=[]
for i in range(29):strokes.append((float(srng.uniform(-math.pi,math.pi)),float(srng.uniform(.033,.083)),float(srng.uniform(.025,.08)),float(srng.uniform(.00025,.0008))))
# Deliberate finite paint dabs, not a noise texture.
paint_dabs={}
for role,count,zlo,zhi in [('body',53,.029,.087),('rim',26,.087,.095),('ear',24,.088,.120),('leg',36,.001,.034)]:
    paint_dabs[role]=[(float(srng.uniform(-math.pi,math.pi)),float(srng.uniform(zlo,zhi)),float(srng.uniform(.035,.16)),float(srng.uniform(.0010,.0035)),float(srng.uniform(-.7,.7))) for _ in range(count)]
def chipped_mask(a,z,role):
    mask=np.zeros_like(a)
    for sa,sz,sw,sh,tilt in paint_dabs.get(role,[]):
        da=(a-sa+math.pi)%TAU-math.pi;u=da/sw;v=(z-sz-da*tilt*.006)/sh
        boundary=1+.13*np.sin(u*8+v*3)+.09*np.sin(v*13-u*5)
        dist=(np.abs(u)**3+np.abs(v)**3)**(1/3)
        mask=np.maximum(mask,np.clip((boundary-dist)*6+.5,0,1))
    return mask
def panel_relief(a,z):
    aa=(a+math.pi/2+math.pi/8)%(math.pi/4)-math.pi/8
    result=np.zeros_like(a)
    for hw,hh,c,thick,h in ((.018,.011,.006,.00115,.0011),(.009,.0038,.0034,.0009,.0008)):
        qx=np.abs(aa*.066)-(hw-c);qy=np.abs(z-.060)-(hh-c)
        sd=np.sqrt(np.maximum(qx,0)**2+np.maximum(qy,0)**2)+np.minimum(np.maximum(qx,qy),0)-c
        result+=h*np.exp(-(sd/thick)**2)
    return result
def paint(p,n,role):
    x,y,z=p.T;r=np.sqrt(x*x+y*y);a=np.arctan2(y,x)
    wash=(np.sin(x*68+y*27+z*21)+.55*np.cos(y*103-z*73)+.3*np.sin(x*139+y*91+z*53))/1.85
    patch=.5+.5*np.sin(a*5+z*102+1.4*np.sin(a*3-z*70))
    bronze=np.array([.40,.303,.185]);patina=np.array([.38,.51,.455])
    green=np.clip(.28+.34*wash+.23*patch,0,.85);warm=np.zeros_like(x)
    if role=='body':
        band=np.exp(-((z-.061)/.016)**6);green=np.clip(green+.18*band,0,.9)
        aa=(a+math.pi/2+math.pi/8)%(math.pi/4)-math.pi/8
        qx=np.abs(aa*.066)-(.018-.006);qy=np.abs(z-.060)-(.011-.006)
        sdf=np.sqrt(np.maximum(qx,0)**2+np.maximum(qy,0)**2)+np.minimum(np.maximum(qx,qy),0)-.006
        recess=np.exp(-((sdf-.0018)/.0017)**2);green=np.clip(green+.34*recess,0,.94)
        warm=.10*np.maximum(0,-n[:,2]);inner=(r<.060)&(z>.036)&(np.sum(p[:,:2]*n[:,:2],axis=1)<0)
    else:inner=np.zeros_like(x,dtype=bool)
    if role=='rim':green=np.clip(.13+.25*wash+.16*patch,0,.6);warm=.35+.20*np.maximum(n[:,2],0)
    elif role=='relief':
        facing=(x*n[:,0]+y*n[:,1])/np.maximum(r,1e-5)
        green=np.clip(.33+.2*wash-.32*facing,0,.65);warm=np.clip(facing*.45,0,.5)
    elif role=='ear':green=np.clip(.25+.24*wash,0,.7);warm=np.clip((np.abs(n[:,0])+.75*np.maximum(n[:,2],0))*.4,0,.55)
    elif role=='leg':green=np.clip(.34+.27*wash,0,.8);warm=.15+.23*np.maximum(n[:,2],0)
    col=bronze[None,:]*(1-green[:,None])+patina[None,:]*green[:,None]
    col+=warm[:,None]*np.array([.22,.17,.09]);col*=1+wash[:,None]*.095
    # Broken oxide with a pale, scumbled margin, and interrupted bronze edge wear.
    pa=a
    if role=='ear':pa=y*230+(np.abs(x)-.068)*35
    chips=chipped_mask(pa,z,role);edge=4*chips*(1-chips)
    oxide=np.array([.43,.565,.49])[None,:]*(1+.13*wash[:,None])
    col=col*(1-.57*chips[:,None])+oxide*.57*chips[:,None]
    col+=edge[:,None]*np.array([.035,.045,.035])
    if role in ('rim','ear','relief','leg'):
        if role=='rim':edgewear=np.clip(n[:,2]*.85+.1,0,.9)
        elif role=='ear':edgewear=np.clip(np.abs(n[:,1])*.8+np.maximum(n[:,2],0)*.85,0,.9)
        elif role=='relief':edgewear=np.clip((x*n[:,0]+y*n[:,1])/np.maximum(r,1e-5)*.65,0,.65)
        else:edgewear=np.clip((.22+.3*np.sin(pa*7+z*200))*(1-chips),0,.45)
        broken=np.clip(.55+.55*np.sin(pa*13+z*421)+.25*np.sin(pa*29-z*189),0,1)
        edgewear*=.4+.6*broken
        col=col*(1-edgewear[:,None])+np.array([.70,.526,.295])*edgewear[:,None]
    rub=np.zeros_like(x)
    if role in ('body','leg','ear'):
        for sa,sz,sw,sh in strokes:
            da=(a-sa+math.pi)%TAU-math.pi;s=np.exp(-(da/sw)**6-((z-sz-da*.004)/sh)**4);rub=np.maximum(rub,s)
        col=col*(1-.48*rub[:,None])+np.array([.66,.50,.29])*.48*rub[:,None]
    if role=='body':
        reliefpaint=np.clip(panel_relief(a,z)/.0011,0,1)*.85
        col=col*(1-reliefpaint[:,None])+np.array([.57,.425,.238])*reliefpaint[:,None]
    col[inner]*=.64
    ao=np.clip(.90+.07*n[:,2]-.12*green,.64,1);rough=np.clip(.68+.16*green+.10*chips-.10*warm,.52,.89);metal=np.clip(.72-.40*green-.12*chips,.25,.78)
    if role=='ash':
        flakes=.5+.5*np.sin(x*183+y*97)*np.sin(y*211-x*133);v=.49+.09*wash+.035*flakes
        col=np.stack((v*1.04,v*1.01,v*.91),axis=1);ao=np.full_like(x,.92);rough=np.full_like(x,.94);metal=np.zeros_like(x)
    elif role in ('incense','char'):
        v=.5+.5*np.sin(z*1500+x*490)
        if role=='char':col=np.stack((.18+.06*v,.16+.05*v,.14+.04*v),axis=1)
        else:col=np.stack((.35+.07*v,.26+.05*v,.15+.04*v),axis=1)
        ao=np.full_like(x,.90);rough=np.full_like(x,.9);metal=np.zeros_like(x)
    return np.clip(col,.04,.90),np.stack((ao,rough,metal),axis=1)
def height(p,role):
    x,y,z=p.T
    if role=='ash':return .000028*np.sin(x*321+y*197)*np.sin(y*411-x*223)
    if role in ('incense','char'):return .000012*np.sin(z*1500+x*490)
    base=.000028*np.sin(x*170+y*95+z*110)*np.sin(y*140-z*160)
    if role=='body':base+=panel_relief(np.arctan2(y,x),z)
    return base
me=lod0.data;uv=me.uv_layers.active.data
for poly in me.polygons:
    ids=list(poly.vertices);P=np.array([me.vertices[j].co[:] for j in ids],dtype=np.float64)
    NN=np.array([me.vertices[j].normal[:] for j in ids],dtype=np.float64);U=np.array([uv[i].uv[:] for i in poly.loop_indices])*(N-1)
    xmin=max(0,int(np.floor(U[:,0].min())));xmax=min(N-1,int(np.ceil(U[:,0].max())))
    ymin=max(0,int(np.floor(U[:,1].min())));ymax=min(N-1,int(np.ceil(U[:,1].max())))
    X,Y=np.meshgrid(np.arange(xmin,xmax+1),np.arange(ymin,ymax+1))
    d=(U[1,1]-U[2,1])*(U[0,0]-U[2,0])+(U[2,0]-U[1,0])*(U[0,1]-U[2,1])
    if abs(d)<1e-12:continue
    w0=((U[1,1]-U[2,1])*(X-U[2,0])+(U[2,0]-U[1,0])*(Y-U[2,1]))/d
    w1=((U[2,1]-U[0,1])*(X-U[2,0])+(U[0,0]-U[2,0])*(Y-U[2,1]))/d
    w2=1-w0-w1;mask=(w0>=-1e-5)&(w1>=-1e-5)&(w2>=-1e-5)
    if not np.any(mask):continue
    W=np.stack((w0[mask],w1[mask],w2[mask]),axis=1);pos=W@P;norm=W@NN
    norm/=np.maximum(np.linalg.norm(norm,axis=1,keepdims=True),1e-12)
    role=me.materials[poly.material_index].name.removeprefix('paint_zone_');col,packed=paint(pos,norm,role)
    duv=(U[1:]-U[0])/(N-1);dp=P[1:]-P[0];det=duv[0,0]*duv[1,1]-duv[0,1]*duv[1,0]
    tangent=(dp[0]*duv[1,1]-dp[1]*duv[0,1])/det;bitan=(-dp[0]*duv[1,0]+dp[1]*duv[0,0])/det
    tangent/=max(np.linalg.norm(tangent),1e-12);bitan/=max(np.linalg.norm(bitan),1e-12);eps=.00012
    dhdu=(height(pos+eps*tangent,role)-height(pos-eps*tangent,role))/(2*eps)
    dhdv=(height(pos+eps*bitan,role)-height(pos-eps*bitan,role))/(2*eps)
    nm=np.stack((-dhdu,-dhdv,np.ones_like(dhdu)),axis=1);nm/=np.linalg.norm(nm,axis=1,keepdims=True)
    yy=Y[mask];xx=X[mask];used[yy,xx]=True
    albedo[yy,xx,:3]=col;normal[yy,xx,:3]=nm*.5+.5;orm[yy,xx,:3]=packed
    albedo[yy,xx,3]=normal[yy,xx,3]=orm[yy,xx,3]=1
# 8 pixel mip-safe padding, no atlas overlap.
for iteration in range(8):
    old=used.copy()
    for dy,dx in ((0,1),(0,-1),(1,0),(-1,0)):
        candidate=np.roll(old,(dy,dx),(0,1))&~used
        if dy==1:candidate[0,:]=False
        if dy==-1:candidate[-1,:]=False
        if dx==1:candidate[:,0]=False
        if dx==-1:candidate[:,-1]=False
        for arr in (albedo,normal,orm):arr[candidate]=np.roll(arr,(dy,dx),(0,1))[candidate]
        used[candidate]=True
albedo[~used]=(.36,.36,.28,1);normal[~used]=(.5,.5,1,1);orm[~used]=(1,.75,.45,1)
def save_texture(name,arr,color):
    im=bpy.data.images.new('UP05_Burner_Burner_'+name,width=N,height=N,alpha=True);im.colorspace_settings.name=color
    im.pixels.foreach_set(arr.ravel());im.update();im.filepath_raw=str(TEX/('UP05_Burner_Burner_'+name+'.png'))
    im.file_format='PNG';im.save();return im
alb=save_texture('Albedo',albedo,'sRGB');nm=save_texture('Normal',normal,'Non-Color');packed=save_texture('ORM',orm,'Non-Color')
mask=np.zeros_like(orm);mask[...,0]=orm[...,2];mask[...,1]=orm[...,0];mask[...,3]=1-orm[...,1]   # Unity URP: R metal, G AO, A smoothness
save_texture('MaskURP',mask,'Non-Color')
mat=bpy.data.materials.new('UP05_Burner_Burner');mat.use_nodes=True
nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.7
for im,x,y in [(alb,-650,300),(nm,-650,-100),(packed,-650,-400)]:
    node=nodes.new('ShaderNodeTexImage');node.image=im;node.label=im.name;node.location=(x,y)
    if im==alb:links.new(node.outputs['Color'],bs.inputs['Base Color'])
    elif im==nm:
        normalnode=nodes.new('ShaderNodeNormalMap');normalnode.location=(-340,-60)
        links.new(node.outputs['Color'],normalnode.inputs['Color']);links.new(normalnode.outputs['Normal'],bs.inputs['Normal'])
    else:
        sep=nodes.new('ShaderNodeSeparateColor');sep.location=(-360,-360);links.new(node.outputs['Color'],sep.inputs['Color'])
        links.new(sep.outputs['Green'],bs.inputs['Roughness']);links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
        group=bpy.data.node_groups.new('glTF Material Output','ShaderNodeTree')
        group.interface.new_socket(name='Occlusion',in_out='INPUT',socket_type='NodeSocketFloat')
        gn=nodes.new('ShaderNodeGroup');gn.node_tree=group;gn.location=(-100,-430);links.new(sep.outputs['Red'],gn.inputs['Occlusion'])
extra_faces=[p.index for p in me.polygons if me.materials[p.material_index].name not in ('paint_zone_body','paint_zone_rim','paint_zone_relief')]
me.materials.clear();me.materials.append(mat)
for p in me.polygons:p.material_index=0
lods=[lod0]
for level,ratio in [(1,.50)]:
    ob=lod0.copy();ob.data=lod0.data.copy();sc.collection.objects.link(ob);ob.name='UP05_Burner_Burner_LOD%d'%level
    bpy.context.view_layer.objects.active=ob;dec=ob.modifiers.new('Silhouette_preserving_LOD','DECIMATE');dec.ratio=ratio;dec.use_collapse_triangulate=True
    bpy.ops.object.modifier_apply(modifier=dec.name)
    # Collapse can leave coincident vertices on very small ash fragments.
    # Clean before export, so source and FBX import contain identical triangles.
    bm=bmesh.new();bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm,verts=bm.verts[:],dist=1e-7)
    bmesh.ops.dissolve_degenerate(bm,edges=bm.edges[:],dist=1e-8)
    bmesh.ops.triangulate(bm,faces=bm.faces[:])
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
    bm.to_mesh(ob.data);bm.free();ob.data.validate(clean_customdata=False);ob.data.update()
    for v in ob.data.vertices:
        if v.co.z<.001:v.co.z=0
    ob.data.update()
    lods.append(ob)
# LOD2 uses intentional lathe topology for a clean rim, not aggressive global collapse.
# Relief moves to the matching painted/bump contours; feet, ears, ash and stubs remain geometry.
indices=sorted({v for fi in extra_faces for v in me.polygons[fi].vertices});lookup={v:i for i,v in enumerate(indices)}
extra=mesh('LOD2_small_parts',[me.vertices[v].co[:] for v in indices],
    [tuple(lookup[v] for v in me.polygons[fi].vertices) for fi in extra_faces],'body')
extra.data.materials.clear();extra.data.materials.append(mat);extra.data.uv_layers.new(name='UVMap')
for p,fi in zip(extra.data.polygons,extra_faces):
    for li,orig in zip(p.loop_indices,me.polygons[fi].loop_indices):extra.data.uv_layers.active.data[li].uv=me.uv_layers.active.data[orig].uv
bpy.context.view_layer.objects.active=extra
mod=extra.modifiers.new('Reduce_secondary_parts','DECIMATE');mod.ratio=.30;mod.use_collapse_triangulate=True
bpy.ops.object.modifier_apply(modifier=mod.name)
lowbody=lathe('LOD2_regular_bowl',[profile[i] for i in (0,2,3,4,6,7,8,10,11,13,15,16,18,19,20,22,24,26)],32,'body')
lowbody.data.materials.clear();lowbody.data.materials.append(mat);lowbody.data.uv_layers.new(name='UVMap')
for poly in lowbody.data.polygons:
    positions=[lowbody.data.vertices[j].co for j in poly.vertices];radii=[math.hypot(p.x,p.y) for p in positions]
    us=[math.atan2(p.y,p.x)%TAU/TAU if r>1e-6 else None for p,r in zip(positions,radii)]
    nonzero=[v for v in us if v is not None]
    if max(nonzero)-min(nonzero)>.5:us=[v+1 if v is not None and v<.5 else v for v in us]
    mid=sum(v for v in us if v is not None)/len(nonzero)
    for loop,p,r,u in zip(poly.loop_indices,positions,radii,us):
        j=int(np.argmin((pr[:,0]-r)**2+(pr[:,1]-p.z)**2))
        lowbody.data.uv_layers.active.data[loop].uv=(.015+.97*(mid if u is None else u),.015+.585*s[j])
bpy.ops.object.select_all(action='DESELECT');lowbody.select_set(True);extra.select_set(True)
bpy.context.view_layer.objects.active=lowbody;bpy.ops.object.join();lowbody.name='UP05_Burner_Burner_LOD2'
bm=bmesh.new();bm.from_mesh(lowbody.data);bmesh.ops.remove_doubles(bm,verts=bm.verts[:],dist=1e-7)
bmesh.ops.dissolve_degenerate(bm,edges=bm.edges[:],dist=1e-8);bmesh.ops.triangulate(bm,faces=bm.faces[:])
bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]);bm.to_mesh(lowbody.data);bm.free();lowbody.data.validate(clean_customdata=False)
for v in lowbody.data.vertices:
    if v.co.z<.001:v.co.z=0
lowbody.data.update();lods.append(lowbody)
root=bpy.data.objects.new('UP05_Burner_GroundOrigin',None);sc.collection.objects.link(root)
root['id']='UP05_Burner';root['version']='Codex';root['minTier']='standard'
for ob in lods:ob.parent=root
socket=bpy.data.objects.new('Socket_Smoke',None);sc.collection.objects.link(socket)
socket.location=(0,0,.094);socket.empty_display_type='ARROWS';socket.empty_display_size=.012;socket.parent=root

def select(obs):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in obs:ob.hide_set(False);ob.select_set(True)
    bpy.context.view_layer.objects.active=lod0
select([root,lod0,socket])
bpy.ops.export_scene.gltf(filepath=str(OUT/'UP05_Burner.glb'),export_format='GLB',use_selection=True,
 export_apply=True,export_yup=True,export_texcoords=True,export_normals=True,export_tangents=True,export_materials='EXPORT',export_extras=True)
select([root,*lods,socket])
bpy.ops.export_scene.fbx(filepath=str(OUT/'UP05_Burner.fbx'),use_selection=True,object_types={'MESH','EMPTY'},global_scale=1.0,   # same settings as build_day34.py
 apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',bake_space_transform=True,axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,
 mesh_smooth_type='FACE',use_tspace=True,path_mode='RELATIVE',embed_textures=False,add_leaf_bones=False,bake_anim=False)
for ob in lods[1:]:ob.hide_set(True);ob.hide_render=True
select([lod0])
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_distance=.29;area.spaces.active.region_3d.view_location=(0,0,.06)
        area.spaces.active.clip_start=.001;area.spaces.active.shading.type='MATERIAL'
for im in (alb,nm,packed):im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(SRC/'UP05_Burner.blend'))
bpy.context.view_layer.update();tris={}
for i,ob in enumerate(lods):ob.data.calc_loop_triangles();tris['LOD%d'%i]=len(ob.data.loop_triangles)
coords=np.array([v.co[:] for v in lod0.data.vertices]);dims=coords.max(axis=0)-coords.min(axis=0)
info={'id':'UP05_Burner','version':'Codex','dimensions_xyz_m':[round(float(x),6) for x in dims],
 'triangles':tris,'lod_ratios':{k:round(v/tris['LOD0'],4) for k,v in tris.items()},
 'texture_sizes':{k:[N,N] for k in ('Albedo','Normal','ORM')},
 'texture_files':{k:'art/textures/qingxi-day34-c/UP05_Burner_Burner_'+k+'.png' for k in ('Albedo','Normal','MaskURP','ORM')},
 'normal_convention':'tangent space +Y (OpenGL)','orm_channels':{'R':'ambient occlusion','G':'roughness','B':'metallic'},
 'minTier':'standard','Socket_Smoke':{'position_m':[0,0,.094],'space':'Blender local Z-up; front -Y'},
 'origin':[0,0,0],'lowest_z_m':round(float(coords[:,2].min()),8),'unit':'metre','collision':False,
 'material_count':1,'blender_version':bpy.app.version_string,
 'notes':['Independent scripted construction from the selected existing AI reference boards; no original builder or exports read.',
 'GLB contains LOD0 and Socket_Smoke; FBX contains LOD0/1/2 and Socket_Smoke.',
 'LOD2 uses a regular 32-sided lathe and transfers belly relief to Albedo/Normal; legs, open ears and flared rim remain geometry.',
 'Three feet, hollow bowl, flared lip, two square ears, eight double rounded relief panels, ash and three burnt incense stubs.',
 'Dimensions and ear orientation interpreted from non-orthographic AI reference; 0.15 m width and 0.12 m height take precedence.',
 'Script raster-painted atlas, no photos/no full-surface noise; broad washes and sparse rubs. ORM AO is authored crevice approximation.',
 'No smoke geometry, pedestal, ground, text or collision; no Unity or mobile runtime validation.']}
# replace the burner entry in the package's model_info.json, in the same shape as the other ten pieces
T=[tris['LOD%d'%i] for i in range(3)]
entry={'id':'UP05_Burner','slot':'LT_QiLesson','builder':'build_up05_burner.py (Codex, GPT-6-Astra high)','dimensions_xyz_m':info['dimensions_xyz_m'],
 'size_limit_m':[.15,.15,.12],'fits_limit':all(a<=b+1e-6 for a,b in zip(info['dimensions_xyz_m'],(.15,.15,.12))),
 'groups':{'Burner':{'material':'UP05_Burner_Burner','texture_px':N,'triangles':T,'maps':['alb','nrm','orm']}},'triangles_total':T,
 'reference':'art/references/qingxi-day34-c/UP05/prompt.txt','origin':'footprint centre, bottom z = 0, front = -Y (Blender) / -Z (FBX, Unity)',
 'textures':'Albedo / Normal / MaskURP (R metal, G AO, A smoothness) / ORM (glTF)','collision':{},'sockets':{'Socket_Smoke':[0.0,0.0,.094]},
 'notes':{'collision':'none (small prop)','build':info['notes']}}
mi=OUT/'model_info.json';d=json.loads(mi.read_text(encoding='utf-8'))
items=d if isinstance(d,list) else d.get('assets',d.get('items',d))
if isinstance(items,dict):items['UP05_Burner']=entry
else:items[:]=[entry if a.get('id')=='UP05_Burner' else a for a in items]
mi.write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding='utf-8')
print('BUILD_DONE',json.dumps(info),flush=True)







