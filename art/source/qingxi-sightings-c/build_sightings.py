"""青溪見聞道具 — Eli-0731, Blender 4.5.3 LTS.
Each prop is modelled only after its AI three-view is saved in art/references/qingxi-sightings-c/<id>-three-view.png.
Pipeline per prop: named parts with tiled source materials → unique-UV bake into one material
(albedo with AO + edge wear, tangent normal, URP mask, glTF ORM) → LOD1 ≈ 50 %, LOD2 ≈ 15 % → FBX/GLB.
Collection size limit (shelf slot): 0.35 × 0.30 × 0.35 m. Origin: bottom centre, Z-up, no ground plate.
blender -b --factory-startup -P build_sightings.py -- A2-F01 [A2-F02 ...]
"""
import bpy,bmesh,json,math,sys,random
from pathlib import Path
from mathutils import Vector,Matrix
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
REF=ROOT/'art/references/qingxi-sightings-c';TEX=ROOT/'art/textures/qingxi-sightings-c';OUT=ROOT/'art/exports/qingxi-sightings-c'
for p in (TEX,OUT):p.mkdir(parents=True,exist_ok=True)
LIMIT=(.35,.30,.35);RES=1024
FONT='C:/Windows/Fonts/msjh.ttc'

# ---------------- tiled source textures (generated once per run, 512², tileable) ----------------
R=512;rng=np.random.default_rng(1031)
def tile_noise(cx,cy):
    g=rng.random((cy,cx));x=np.linspace(0,cx,R,endpoint=False);y=np.linspace(0,cy,R,endpoint=False)
    xi=x.astype(int);yi=y.astype(int);fx=x-xi;fy=y-yi;fx=fx*fx*(3-2*fx);fy=fy*fy*(3-2*fy)
    a=g[np.ix_(yi%cy,xi%cx)];b=g[np.ix_(yi%cy,(xi+1)%cx)];c=g[np.ix_((yi+1)%cy,xi%cx)];d=g[np.ix_((yi+1)%cy,(xi+1)%cx)]
    fx=fx[None,:];fy=fy[:,None];return (a*(1-fx)+b*fx)*(1-fy)+(c*(1-fx)+d*fx)*fy
def fbm(c0,oct=4,aniso=1):
    v=0;amp=.5;tot=0
    for o in range(oct):v=v+amp*tile_noise(c0*2**o,max(1,int(c0*2**o/aniso)));tot+=amp;amp*=.5
    return v/tot
def lerp(a,b,t):return np.asarray(a)[None,None,:]*(1-t[...,None])+np.asarray(b)[None,None,:]*t[...,None]
def img(name,rgb,data=False):
    im=bpy.data.images.new(name,R,R)
    if data:im.colorspace_settings.name='Non-Color'
    a=np.ones((R,R,4),np.float32);a[...,:3]=np.clip(rgb,0,1);im.pixels.foreach_set(a.ravel());im.pack();return im
def nmap(name,h,s):
    dx=(np.roll(h,-1,1)-np.roll(h,1,1))*s;dy=(np.roll(h,-1,0)-np.roll(h,1,0))*s
    n=np.dstack([-dx,-dy,np.ones_like(h)]);n/=np.linalg.norm(n,axis=2,keepdims=True);return img(name,n*.5+.5,True)
X=np.arange(R)[None,:]/R;Y=np.arange(R)[:,None]/R
def make_sources():
    S={}
    warp=fbm(2,2);streak=fbm(24,3,aniso=8);grain=(.5+.5*np.sin(math.tau*(X*11+warp*.45)))**3;cr=np.clip((fbm(40,2,aniso=12)-.68)*7,0,1)
    t=np.clip(.58-.16*grain+.22*(streak-.5)-.30*cr,0,1)
    S['wood']=(lerp((.25,.17,.11),(.52,.38,.26),t),.6*grain-.5*streak+1.4*cr,3.0,.74,0)
    pat=np.clip((fbm(6,4)-.52)*2.6,0,1)
    S['bronze']=(lerp((.47,.37,.21),(.27,.38,.32),pat)*(.85+.25*fbm(32,2))[...,None],fbm(16,3)+.6*pat,2.4,.50,.45)
    S['iron']=(lerp((.20,.17,.15),(.50,.27,.12),np.clip((fbm(8,4)-.40)*2.2,0,1)),fbm(24,3),3.0,.82,.25)
    st=fbm(8,5);sp=np.clip((fbm(110,2)-.70)*5,0,1);S['stone']=(lerp((.30,.34,.37),(.52,.55,.56),st)*(1-.18*sp[...,None])+.06*sp[...,None],st+.4*fbm(40,2)+.5*sp,5.0,.86,0)
    tw=.5+.5*np.sin(math.tau*((X+Y)*16));S['hemp']=(lerp((.33,.25,.16),(.58,.47,.31),np.clip(tw*.7+.3*fbm(32,2),0,1)),tw,1.2,.92,0)
    gl=fbm(4,4);spk=np.clip((fbm(80,2)-.74)*6,0,1);S['stoneware']=(lerp((.40,.35,.28),(.54,.58,.56),np.clip(gl+.06*np.sin(Y*260+gl*4),0,1))*(1-.55*spk[...,None]),gl+.4*fbm(48,2)+.6*spk,1.6,.40,0)
    S['clay']=(lerp((.45,.24,.15),(.62,.38,.26),fbm(10,4)),fbm(20,3),2.0,.9,0)
    S['glaze']=(lerp((.20,.40,.38),(.33,.52,.48),fbm(6,3)),.3*fbm(30,2)+fbm(6,3),.8,.20,0)
    S['moss']=(lerp((.17,.24,.12),(.33,.40,.20),fbm(16,4)),fbm(16,4),4.0,.95,0)
    nodes=np.clip(1-np.abs(((Y*4)%1)-.5)*40,0,1);S['bamboo']=(lerp((.42,.40,.22),(.62,.56,.33),.5*streak+.5*fbm(6,2))*(1-.3*nodes[...,None]),.4*streak+nodes,2.0,.6,0)
    wx=((X*24)%1<.5);wy=((Y*24)%1<.5);ov=np.where(wx^wy,.5+.5*np.sin(X*24*math.pi*2)**2,.5+.5*np.sin(Y*24*math.pi*2)**2)
    S['weave']=(lerp((.30,.26,.15),(.55,.47,.30),ov*.8+.2*fbm(20,2))*np.where(((Y*6)%1<.18)[...,None],np.array([.72,.92,.78]),1),ov,3.0,.8,0)
    S['oilpaper']=(lerp((.30,.22,.12),(.52,.40,.24),np.clip(fbm(5,4)+.25*fbm(40,2),0,1)),fbm(30,3)+np.clip((fbm(12,2,aniso=1)-.6)*3,0,1),2.0,.45,0)
    S['paper']=(lerp((.74,.70,.60),(.86,.83,.74),fbm(20,3))*(1-.5*np.clip((fbm(30,2)-.7)*6,0,1))[...,None],fbm(40,2),1.0,.9,0)
    S['seal']=(lerp((.55,.10,.07),(.72,.18,.10),fbm(20,2)),fbm(20,2),1.0,.8,0)
    S['cloth']=(lerp((.10,.13,.17),(.20,.24,.28),np.clip(fbm(6,4)+.2*np.sin((X+Y)*300),0,1)),.5*np.sin(X*500)+.5*np.sin(Y*500)+fbm(8,3),1.4,.88,0)
    S['bone']=(lerp((.70,.66,.56),(.86,.83,.74),fbm(10,4))*(1-.25*np.clip((fbm(6,3)-.62)*4,0,1))[...,None],fbm(30,3),2.0,.6,0)
    sw=.5+.5*np.sin(X*96*math.pi*2+np.sin(Y*30)*.6);S['straw']=(lerp((.48,.38,.18),(.72,.58,.32),np.clip(sw*.7+.3*fbm(20,2),0,1)),sw,1.4,.85,0)
    S['glow']=(lerp((.35,.80,.78),(.55,.95,.90),fbm(30,2)),fbm(60,2),1.0,.5,0)
    S['pebble']=(lerp((.18,.22,.22),(.34,.38,.36),fbm(4,4)),fbm(20,3),1.0,.28,0)
    out={}
    for k,(alb,h,s,r,m) in S.items():
        mat=bpy.data.materials.new('src_'+k);mat.use_nodes=True;nt=mat.node_tree;bs=nt.nodes['Principled BSDF']
        bs.inputs['Roughness'].default_value=r;bs.inputs['Metallic'].default_value=m
        uvn=nt.nodes.new('ShaderNodeUVMap');uvn.uv_map='Tiled'
        ta=nt.nodes.new('ShaderNodeTexImage');ta.image=img('alb_'+k,alb);nt.links.new(uvn.outputs['UV'],ta.inputs['Vector']);nt.links.new(ta.outputs['Color'],bs.inputs['Base Color'])
        tn=nt.nodes.new('ShaderNodeTexImage');tn.image=nmap('nrm_'+k,h,s);nt.links.new(uvn.outputs['UV'],tn.inputs['Vector'])
        nm=nt.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.8;nt.links.new(tn.outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
        out[k]=(mat,m)
    return out

# ---------------- geometry helpers ----------------
parts=[]
def link(o):bpy.context.scene.collection.objects.link(o);parts.append(o);return o
def finish(name,bm,mat,scale=.12):
    """box-projected tiled UV (scale = metres per tile; small props use a finer tile)"""
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces);uv=bm.loops.layers.uv.get('Tiled') or bm.loops.layers.uv.new('Tiled')
    pts=np.array([v.co[:] for v in bm.verts]);c=pts.mean(0);_,_,vt=np.linalg.svd(pts-c,full_matrices=False);A,S1,S2=[Vector(v) for v in vt]
    for f in bm.faces:
        n=f.normal;k=int(np.argmax([abs(n.dot(A)),abs(n.dot(S1)),abs(n.dot(S2))]))
        for l in f.loops:
            p=l.vert.co-Vector(c);u,v={0:(p.dot(S1),p.dot(S2)),1:(p.dot(S2),p.dot(A)),2:(p.dot(S1),p.dot(A))}[k];l[uv].uv=(u/scale,v/scale)
    me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free();o=bpy.data.objects.new(name,me);me.materials.append(mat)
    return link(o)
def lathe(name,profile,mat,seg=48,scale=.12,smooth=True):
    """profile: [(r,z)...] bottom→top; revolved around Z"""
    bm=bmesh.new();rings=[]
    for r,z in profile:
        rings.append([bm.verts.new((r*math.cos(math.tau*i/seg),r*math.sin(math.tau*i/seg),z)) if r>1e-6 else None for i in range(seg)])
    for a,b in zip(rings,rings[1:]):
        for i in range(seg):
            j=(i+1)%seg
            if a[0] is None:bm.faces.new((b[j],b[i],bm.verts.new((0,0,0))) ) if False else None
            if a[0] is not None and b[0] is not None:bm.faces.new((a[i],a[j],b[j],b[i]))
    # caps for zero-radius ends
    for idx,(r,z) in [(0,profile[0]),(len(profile)-1,profile[-1])]:
        if r<=1e-6:
            nb=rings[1] if idx==0 else rings[-2];c=bm.verts.new((0,0,z))
            for i in range(seg):
                j=(i+1)%seg;bm.faces.new((nb[j],nb[i],c) if idx==0 else (nb[i],nb[j],c))
    bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-7)
    for f in bm.faces:f.smooth=smooth
    return finish(name,bm,mat,scale)
def tube(name,pts,r,mat,sides=8,scale=.06):
    pts=[Vector(p) for p in pts];bm=bmesh.new();rings=[]
    for i,p in enumerate(pts):
        t=(pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]).normalized();u=t.orthogonal().normalized();v=t.cross(u)
        rings.append([bm.verts.new(p+(u*math.cos(math.tau*k/sides)+v*math.sin(math.tau*k/sides))*r) for k in range(sides)])
    for a,b in zip(rings,rings[1:]):
        for k in range(sides):bm.faces.new((a[k],a[(k+1)%sides],b[(k+1)%sides],b[k]))
    bm.faces.new(list(reversed(rings[0])));bm.faces.new(rings[-1])
    for f in bm.faces:f.smooth=True
    return finish(name,bm,mat,scale)
def rope(name,pts,r,mat,plies=3,twist=9,sides=5):
    """twisted 3-ply rope along a polyline"""
    P=[Vector(p) for p in pts];L=sum((b-a).length for a,b in zip(P,P[1:]));res=[]
    dense=[];acc=0
    for a,b in zip(P,P[1:]):
        n=max(2,int((b-a).length/(r*1.2)))
        for i in range(n):dense.append(a+(b-a)*(i/n))
    dense.append(P[-1])
    for k in range(plies):
        path=[];s=0
        for i,p in enumerate(dense):
            if i:s+=(p-dense[i-1]).length
            t=(dense[min(i+1,len(dense)-1)]-dense[max(i-1,0)]).normalized();u=t.orthogonal().normalized();v=t.cross(u)
            ang=math.tau*k/plies+s/L*twist*math.tau;path.append(p+(u*math.cos(ang)+v*math.sin(ang))*r*.55)
        res.append(tube(f'{name}_ply{k+1}',path,r*.52,mat,sides,.03))
    return res
def box_bm(size,center=(0,0,0)):
    bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
    for v in bm.verts:v.co=Vector([center[i]+v.co[i]*size[i] for i in range(3)])
    return bm
def bevel(o,w,segs=2,angle=35):
    m=o.modifiers.new('wear','BEVEL');m.width=w;m.segments=segs;m.limit_method='ANGLE';m.angle_limit=math.radians(angle);m.use_clamp_overlap=True
    bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.modifier_apply(modifier=m.name);o.select_set(False)
def jitter(o,amt,seed=1,freq=40):
    r=random.Random(seed);ph=[r.uniform(0,9) for _ in range(6)]
    for v in o.data.vertices:
        p=v.co;n=v.normal;d=amt*(math.sin(p.x*freq+ph[0])*math.sin(p.y*freq*1.3+ph[1])+.6*math.sin(p.z*freq*.8+ph[2])*math.sin((p.x+p.y)*freq*2.1+ph[3]))
        v.co=p+n*d
def text_mesh(name,s,size,mat,depth,vertical=True,spacing=1.05,bold=False):
    """CJK carving via Microsoft JhengHei; returns joined mesh object lying in XY, glyphs top→bottom"""
    font=bpy.data.fonts.load(FONT.replace('msjh.ttc','msjhbd.ttc') if bold else FONT,check_existing=True);objs=[]
    for i,ch in enumerate(s):
        cu=bpy.data.curves.new(f'{name}_{i}','FONT');cu.body=ch;cu.font=font;cu.size=size;cu.extrude=depth/2;cu.align_x='CENTER';cu.align_y='CENTER'
        o=bpy.data.objects.new(f'{name}_{i}',cu);bpy.context.scene.collection.objects.link(o);o.location=(0,-i*size*spacing,0) if vertical else (i*size*spacing,0,0);objs.append(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0];bpy.ops.object.convert(target='MESH');bpy.ops.object.join();j=bpy.context.object;j.name=name
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    bm=bmesh.new();bm.from_mesh(j.data);bpy.data.objects.remove(j);return bm

# ---------------- props ----------------
def A2_F01(M):
    """遠客鈴: bronze bell 0.07 m body, cloud-wave relief band, wooden clapper, hemp loop with overhand knot"""
    H=.070;prof=[(0,0.0),(.030,.0)]  # placeholder start replaced below
    prof=[(.0255,.0),(.0300,.0015),(.0312,.004),(.0300,.0055),(.0275,.008),(.0262,.014),(.0245,.024),(.0228,.034),(.0208,.046),(.0185,.056),(.0150,.064),(.0095,.069),(.0035,.0705),(0,.0706)]
    inner=[(r-.0028,z) for r,z in prof[:-3]]
    shell=prof+[(0,.0706)]
    # outer + inner surfaces as one closed lathe: outer up, inner back down
    full=prof[:-1]+[(0,.0706)]
    o=lathe('Bell_Shell',[(.0225,.0006)]+[(r-.0030,z) for r,z in reversed(prof[3:-3])][::-1][:0]+prof,M['bronze'][0],64,.05)
    # hollow mouth: inner skirt as separate inward-facing lathe (dark inside)
    lathe('Bell_Inner',[(.0228,.0003),(.0238,.008),(.0222,.024),(.0198,.040),(.0160,.054),(.0100,.062),(0,.0635)],M['bronze'][0],64,.05)
    for z,r in ((.0115,.0268),(.0175,.0258),(.0385,.0224),(.044,.0213)):  # raised bands framing the relief
        lathe(f'Bell_Band_{z:.3f}',[(r-.0006,z-.0011),(r+.0009,z-.0007),(r+.0011,z),(r+.0009,z+.0007),(r-.0006,z+.0011)],M['bronze'][0],64,.03)
    # cloud-wave relief: swirls as tubes wrapped on the cone between bands
    def on_cone(a,z,off=.0009):
        r=np.interp(z,[p[1] for p in prof],[p[0] for p in prof])+off;return (r*math.cos(a),r*math.sin(a),z)
    for k in range(6):
        a0=k*math.tau/6
        wave=[on_cone(a0+t*math.tau/6,.0255+.0045*math.sin(t*math.tau)) for t in np.linspace(0,1,30)]
        tube(f'Bell_Wave_{k}',wave,.0011,M['bronze'][0],6,.02)
        for j,(da,zc,sc_) in enumerate(((.28,.0318,1.0),(.62,.0302,.8),(.95,.0322,.65))):  # cloud scrolls above the wave line
            sw=[on_cone(a0+da+.10*sc_*math.cos(u)*(1-u/14),zc+.0040*sc_*math.sin(u)*(1-u/14)) for u in np.linspace(0,12,34)]
            tube(f'Bell_Cloud_{k}_{j}',sw,.00095,M['bronze'][0],6,.02)
    # crown loop (canon)
    pts=[(.0,0,.0700)]+[(.0075*math.cos(t),0,.0775+.0075*math.sin(t)) for t in np.linspace(-.2,math.pi+.2,18)]
    lathe('Bell_Crown_Stem',[(.0062,.0688),(.0058,.0718),(.0050,.0742),(0,.0745)],M['bronze'][0],24,.02)
    tube('Bell_Crown',[(.0072*math.cos(t),0,.0742+.0078*math.sin(t)) for t in np.linspace(-.18,math.pi+.18,20)],.0030,M['bronze'][0],10,.02)
    # wooden clapper on a short cord, hanging below the mouth
    lathe('Clapper',[(0,.0012),(.0035,.0020),(.0062,.006),(.0072,.012),(.0066,.018),(.0048,.023),(.0028,.0265),(0,.0275)],M['wood'][0],16,.03)
    rope('Clapper_Cord',[(0,0,.0270),(0,0,.0600)],.0016,M['hemp'][0],twist=4)
    # hemp loop through the crown, ending in an overhand knot and frayed tail
    loop=[(.0,.0,.0805),(.006,.004,.090),(.014,.010,.084),(.020,.014,.072),(.026,.016,.060),(.030,.017,.050)]
    rope('Hang_Cord',loop,.0021,M['hemp'][0],twist=6)
    knot=[(.030+.0045*math.cos(t),.017+.0045*math.sin(t),.047-.0012*t) for t in np.linspace(0,math.tau*1.4,22)]
    tube('Hang_Knot',knot,.0024,M['hemp'][0],7,.03)
    for k in range(5):
        a=k*1.25;tube(f'Hang_Fray_{k}',[(.0305,.017,.041),(.0305+.004*math.cos(a),.017+.004*math.sin(a),.030+.003*math.sin(k))],.0006,M['hemp'][0],4,.02)
    return {'wear_zone':'rim','mud':False}

def A2_F02(M):
    """缺月碗: rough stoneware tea bowl Ø0.13 × 0.06, drippy glaze, rim chip, notched-moon mark in the foot"""
    prof=[(.0,.0),(.026,.0),(.030,.0015),(.031,.006),(.034,.009),(.045,.014),(.055,.024),(.062,.037),(.065,.050),(.0655,.058),(.064,.0605),(.0615,.0600),(.0598,.052),(.055,.038),(.047,.026),(.037,.018),(.024,.0125),(0,.0115)]
    o=lathe('Bowl_Body',prof,M['stoneware'][0],72,.08)
    o.data.materials.append(M['clay'][0])
    for p in o.data.polygons:
        c=p.center;n=p.normal;outward=n.x*c.x+n.y*c.y>0
        if (c.z<.019 and (outward or n.z<-.5)):p.material_index=1   # raw clay on the outside below the glaze line and the foot
    jitter(o,.0004,3,60)
    # rim chip
    bm=bmesh.new();bm.from_mesh(o.data)
    for v in bm.verts:
        a=math.atan2(v.co.y,v.co.x);d=abs(((a-.9+math.pi)%math.tau)-math.pi)
        if v.co.z>.054 and d<.16:v.co.z-=.006*(1-d/.16)
    bm.to_mesh(o.data);bm.free()
    # foot ring underside: carved notched moon (circle with a bite)
    pts=[];R_=.0105
    for t in np.linspace(0,math.tau,40):
        p=Vector((R_*math.cos(t),R_*math.sin(t)))
        c2=Vector((.0075,.0055))
        if (p-c2).length<.0072:p=c2+(p-c2).normalized()*.0072
        pts.append(p)
    ring=[]
    for k,p in enumerate(pts):ring.append((p.x,p.y,.0004))
    tube('Foot_MoonMark',ring+[ring[0]],.00055,M['clay'][0],5,.02)
    # glaze drips: thicker teardrops on the outside below the glaze line
    r=random.Random(2)
    for k in range(9):
        a=r.uniform(0,math.tau);zt=.040;zb=r.uniform(.016,.028)
        path=[]
        for z in np.linspace(.026,zb-.004,8):
            rr=np.interp(z,[p[1] for p in prof[:11]],[p[0] for p in prof[:11]])+.0002;path.append((rr*math.cos(a),rr*math.sin(a),z))
        tube(f'Glaze_Drip_{k}',path,.0009,M['stoneware'][0],6,.02)  # glaze runs over the raw clay, nearly flush
    return {'wear_zone':'rim','mud':False}

def A2_F03(M):
    """鎮石殘碑: snapped stele fragment 0.30 × 0.12 × 0.24 with carved column of characters, moss in grooves"""
    W,D,Hh=.29,.11,.23
    bm=bmesh.new();bmesh.ops.create_grid(bm,x_segments=24,y_segments=18,size=.5)
    bm.free()
    # body: subdivided box with a jagged snapped top
    bm=box_bm((W,D,Hh),(0,0,Hh/2));bmesh.ops.subdivide_edges(bm,edges=bm.edges[:],cuts=8,use_grid_fill=True)
    r=random.Random(5)
    for v in bm.verts:
        x=v.co.x
        if v.co.z>Hh-.001:   # one slanting break, high on the left, with a stepped chip on the right (three-view front)
            v.co.z=Hh-.055*(x+W/2)/W-(.022 if x>.04 else 0)+.006*math.sin(x*40+1.3)+r.uniform(-.003,.003)
        if v.co.z<.02:v.co.x*=1+r.uniform(-.03,.03)
        if abs(v.co.y)>D/2-.001 and v.co.z>.06:v.co.y*=1+.04*math.sin(v.co.z*30+x*20)   # uneven back/front faces
    for v in bm.verts:   # thicker at the foot, thinner toward the break (three-view side profile)
        if v.co.y>0:v.co.y=D/2+.06*(1-v.co.z/Hh)+(v.co.y-D/2)   # taper only the back, so the inscribed front stays a carving plane
    o=finish('Stele_Body',bm,M['stone'][0],.15);bevel(o,.018,3,30)
    def lumps(o,amp,freq,seed):
        r=random.Random(seed);ph=[r.uniform(0,9) for _ in range(9)]
        for v in o.data.vertices:
            p=v.co;d=sum(math.sin(p.x*freq*k1+ph[i])*math.sin(p.y*freq*k2+ph[i+3])*math.sin(p.z*freq*k3+ph[i+6]) for i,(k1,k2,k3) in enumerate(((1,1.3,.9),(2.1,1.7,2.4),(4.3,3.9,4.7))))
            front=p.y<-D/2+.004 and .02<p.z<.21 and abs(p.x)<.10   # keep the inscribed panel flat enough to carve
            v.co=p+v.normal*amp*d*(.08 if front else 1)
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.subdivide_edges(bm,edges=[e for e in bm.edges if e.calc_length()>.02],cuts=1);bm.to_mesh(o.data);bm.free()
    lumps(o,.006,9,7);jitter(o,.0012,8,60)   # weathered rock: big lumps + fine grain
    # carved characters: boolean-cut 3 mm into the front face, two columns read top→bottom, right→left
    cutters=[]
    for col,(txt,x) in enumerate((('各守一方',.050),('以石鎮',.004))):
        tb=text_mesh(f'Glyph_{col}',txt,.036,M['stone'][0],.016,bold=True)
        bmesh.ops.rotate(tb,verts=tb.verts,cent=(0,0,0),matrix=Matrix.Rotation(math.radians(90),3,'X'))
        bmesh.ops.translate(tb,verts=tb.verts,vec=Vector((x,-D/2-.0005,.172)))
        me=bpy.data.meshes.new(f'cut{col}');tb.to_mesh(me);tb.free();c=bpy.data.objects.new(f'cut{col}',me);bpy.context.scene.collection.objects.link(c);cutters.append(c)
    for x0,z0,x1,z1 in ((-.085,.030,.085,.030),(-.085,.030,-.085,.19),(.085,.030,.085,.19),(-.035,.03,-.035,.19)):   # chiselled panel frame
        b=box_bm((abs(x1-x0)+.004,.016,abs(z1-z0)+.004),((x0+x1)/2,-D/2-.0005,(z0+z1)/2));me=bpy.data.meshes.new('cutf');b.to_mesh(me);b.free()
        c=bpy.data.objects.new('cutf',me);bpy.context.scene.collection.objects.link(c);cutters.append(c)
    for c in cutters:
        m=o.modifiers.new('carve','BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=c
        bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(c)
    bm=bmesh.new();bm.from_mesh(o.data);o.data.uv_layers.remove(o.data.uv_layers['Tiled']);me=o.data;parts.remove(o);bpy.data.objects.remove(o)
    o=finish('Stele_Body',bm,M['stone'][0],.15)   # boolean leaves new faces without UVs: project again
    # moss tufts on the broken top
    for k in range(5):
        x=r.uniform(-.12,.12);b=bmesh.new();bmesh.ops.create_icosphere(b,subdivisions=2,radius=.014)
        for v in b.verts:v.co=Vector((v.co.x*1.4,v.co.y*1.1,v.co.z*.45))
        bmesh.ops.translate(b,verts=b.verts,vec=Vector((x,r.uniform(-.03,.03),Hh-.03+.02*math.sin(x*21+1.3)*.6)))
        m=finish(f'Moss_{k}',b,M['moss'][0],.05);jitter(m,.002,k,90)
        m.data.transform(Matrix.Translation((0,0,-.008)))
    return {'wear_zone':'top','mud':True}

def A2_F04(M):
    """暮園陶片: crescent rim shard of a glazed jar (~0.18 × 0.10 m): rolled lip, teal glaze, cream band painted with
    golden fruits, blue vines and green leaves (painted into the texture), red clay body on the inside and broken edges"""
    Rj=.12;th=.010;r=random.Random(9);W=.090
    def to_cyl(x,y,off):  # (arc length x, height y) on a jar wall of radius Rj, facing -Y
        a=x/Rj;rr=Rj+off;return Vector((rr*math.sin(a),Rj-rr*math.cos(a),y))
    # crescent outline: nearly straight top (the jar's shoulder), convex bottom, chipped edges
    top=[(x,.050+r.uniform(-.003,.003)) for x in np.linspace(-W,W,13)]
    bot=[(x,.050-.095*math.cos(x/W*math.pi/2)**.7+r.uniform(-.005,.005)) for x in np.linspace(W,-W,17)[1:-1]]
    outline=[Vector(p) for p in top+bot];n=len(outline);ctr=sum(outline,Vector((0,0)))/n
    bm=bmesh.new();rings=6
    grid=[[ctr+(p-ctr)*(k/rings) for p in outline] for k in range(1,rings+1)]
    oc=bm.verts.new(to_cyl(ctr.x,ctr.y,0));ic=bm.verts.new(to_cyl(ctr.x,ctr.y,-th))
    outer=[[bm.verts.new(to_cyl(p.x,p.y,0)) for p in rr] for rr in grid];inner=[[bm.verts.new(to_cyl(p.x,p.y,-th)) for p in rr] for rr in grid]
    for i in range(n):
        j=(i+1)%n;bm.faces.new((oc,outer[0][i],outer[0][j]));bm.faces.new((ic,inner[0][j],inner[0][i]))
    for a,b in zip(outer,outer[1:]):
        for i in range(n):bm.faces.new((a[i],b[i],b[(i+1)%n],a[(i+1)%n]))
    for a,b in zip(inner,inner[1:]):
        for i in range(n):bm.faces.new((a[(i+1)%n],b[(i+1)%n],b[i],a[i]))
    for i in range(n):j=(i+1)%n;bm.faces.new((outer[-1][i],inner[-1][i],inner[-1][j],outer[-1][j]))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    o=finish('Shard_Body',bm,M['glaze'][0],.06);o.data.materials.append(M['clay'][0])
    for p in o.data.polygons:
        c=p.center;rr=math.hypot(c.x,c.y-Rj)
        if rr<Rj-.0015:p.material_index=1          # inside wall and broken faces → raw red clay
    bevel(o,.0012,2,40);jitter(o,.0004,4,120)
    # rolled lip along the top edge (glazed)
    tube('Shard_Lip',[to_cyl(x,.050,.002) for x in np.linspace(-W+.002,W-.002,30)],.0065,M['glaze'][0],10,.04)
    return {'wear_zone':'edge','mud':True,'paint':'hesper','Rj':Rj}

def carve(o,cutters):
    """boolean-cut each cutter object out of o, then drop the stray UV layers booleans leave behind"""
    for c in cutters:
        m=o.modifiers.new('carve','BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=c
        bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(c)
        assert len(o.data.polygons)>0,f'{o.name}: boolean removed everything'
def cutter(bm,name='cut'):
    me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free();c=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(c);return c
def reproject(o,mat,scale):
    """re-run the tiled box projection after booleans (new faces have no UVs)"""
    bm=bmesh.new();bm.from_mesh(o.data);name=o.name;parts.remove(o);bpy.data.objects.remove(o)
    for l in [l for l in bm.loops.layers.uv.keys() if l!='Tiled']:bm.loops.layers.uv.remove(bm.loops.layers.uv[l])
    mats=None
    n=finish(name,bm,mat,scale);return n
def lie(objs_before):
    """rotate everything made since objs_before to lie along X (long props rest on the shelf on their side)"""
    for o in parts[objs_before:]:o.data.transform(Matrix.Rotation(math.radians(90),4,'Y'))

def A2_F05(M):
    """枯線鐵楔: hand-forged square wedge stake 0.28 m, hammered head, three diagonal chisel grooves, rust"""
    n0=len(parts);L=.25
    bm=bmesh.new();loops=[]
    for i,(z,w) in enumerate([(0,.0012),(.02,.007),(.08,.015),(.16,.021),(.22,.025),(L,.028)]):
        loops.append([bm.verts.new((x*w/2,y*w/2,z)) for x,y in ((1,1),(-1,1),(-1,-1),(1,-1))])
    for a,b in zip(loops,loops[1:]):
        for k in range(4):bm.faces.new((a[k],a[(k+1)%4],b[(k+1)%4],b[k]))
    bm.faces.new(list(reversed(loops[0])));bm.faces.new(loops[-1])
    shank=finish('Wedge_Shank',bm,M['iron'][0],.06);bevel(shank,.0012,1,40)
    hb=box_bm((.056,.054,.018),(0,0,L+.008));head=finish('Wedge_Head',hb,M['iron'][0],.06);bevel(head,.004,2,30)
    for o in (shank,head):
        bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.subdivide_edges(bm,edges=bm.edges[:],cuts=3,use_grid_fill=True);bm.to_mesh(o.data);bm.free()
        jitter(o,.0008,11,90);jitter(o,.0004,12,240)   # hammer facets + scale
    cs=[]
    for k in range(3):   # diagonal grooves on the +X face, upper third
        b=box_bm((.004,.03,.0024),(0,0,0));bmesh.ops.rotate(b,verts=b.verts,cent=(0,0,0),matrix=Matrix.Rotation(math.radians(35),3,'Y'))
        z=.205-.018*k;w=np.interp(z,[0,.02,.08,.16,.22,L],[.0012,.007,.015,.021,.025,.028])
        bmesh.ops.translate(b,verts=b.verts,vec=Vector((w/2,0,z)));cs.append(cutter(b))
    carve(shank,cs);reproject(shank,M['iron'][0],.06)
    lie(n0);return {'mud':True}

def A3_F01(M):
    """螢砂木齒: replaced mill-gear tooth — trapezoid block with tenon, split crack packed with glowing sand, two nails"""
    bm=bmesh.new()
    def trap(z0,z1,wb,wt,d):
        lo=[bm.verts.new((x*wb/2,y*d/2,z0)) for x,y in ((1,1),(-1,1),(-1,-1),(1,-1))];hi=[bm.verts.new((x*wt/2,y*d*.86/2,z1)) for x,y in ((1,1),(-1,1),(-1,-1),(1,-1))]
        bm.faces.new(list(reversed(lo)));bm.faces.new(hi)
        for k in range(4):bm.faces.new((lo[k],lo[(k+1)%4],hi[(k+1)%4],hi[k]))
    trap(.075,.22,.22,.15,.085)
    body=finish('Cog_Body',bm,M['wood'][0],.12);bevel(body,.006,2,30)
    tb=box_bm((.055,.055,.08),(0,0,.04));tenon=finish('Cog_Tenon',tb,M['wood'][0],.12);bevel(tenon,.004,2,30)
    for o in (body,tenon):
        bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.subdivide_edges(bm,edges=bm.edges[:],cuts=4,use_grid_fill=True);bm.to_mesh(o.data);bm.free()
        jitter(o,.0012,21,60)
    # split crack (cut) and the sand filling it
    crack=[(-.010+.006*math.sin(z*60),-.05,z) for z in np.linspace(.08,.222,14)]
    def front_y(z):return -(.085*(1-(z-.075)/.145*(1-.86)))/2-.0006   # front face of the tapering block
    for s in (-1,1):   # split lips: dark, slightly raised wood either side of the crack
        tube(f'Crack_Lip_{s}',[(x+s*.0032,front_y(z),z) for x,_,z in crack],.0016,M['wood'][0],5,.02)
    for k,(x,y,z) in enumerate(crack[1:-1]):
        g=bmesh.new();bmesh.ops.create_icosphere(g,subdivisions=1,radius=.0034)
        for v in g.verts:v.co=Vector((v.co.x*.7,v.co.y*9,v.co.z))
        for v in g.verts:v.co=Vector((v.co.x,v.co.y/9*.5,v.co.z))
        bmesh.ops.translate(g,verts=g.verts,vec=Vector((x,front_y(z),z)));finish(f'Glow_Sand_{k}',g,M['glow'][0],.02)
    for k,(x,z) in enumerate(((-.055,.175),(.04,.135))):   # forged nails
        lathe(f'Nail_{k}',[(0,0),(.0075,0),(.0072,.0018),(.005,.0032),(0,.0036)],M['iron'][0],16,.02).data.transform(Matrix.Translation((x,-.0405+.0,z))@Matrix.Rotation(math.radians(90),4,'X'))
    return {'mud':False}

def A3_F02(M):
    """無名刻石: flat river slab 0.26 × 0.05 × 0.17, five invented glyphs (not any real script), bamboo roots wrapped round"""
    W,T,H=.25,.045,.165;r=random.Random(31)
    outline=[((W/2)*math.cos(t)*(1+.06*math.sin(3*t+1)),(H/2)*math.sin(t)*(1+.08*math.cos(2*t))+H/2) for t in np.linspace(0,math.tau,40,endpoint=False)]
    bm=bmesh.new();n=len(outline);rings=[]
    for y,s in ((-T/2,.9),(-T/2+.006,1.0),(T/2-.006,1.0),(T/2,.88)):
        rings.append([bm.verts.new((x*s,y,(z-H/2)*s+H/2)) for x,z in outline])
    for a,b in zip(rings,rings[1:]):
        for i in range(n):bm.faces.new((a[i],a[(i+1)%n],b[(i+1)%n],b[i]))
    bm.faces.new(list(reversed(rings[0])));bm.faces.new(rings[-1])
    o=finish('Slab',bm,M['stone'][0],.12);bevel(o,.004,2,30)
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.subdivide_edges(bm,edges=[e for e in bm.edges if e.calc_length()>.012],cuts=2,use_grid_fill=True);bm.to_mesh(o.data);bm.free()
    jitter(o,.0018,33,30);jitter(o,.0007,34,110)
    # invented glyphs: stroke paths cut 2.5 mm into the -Y face
    G=[[[(0,.03),(-.008,.0),(.008,-.012),(0,-.03)],[(-.012,.012),(.012,.012)]],
       [[(-.012,.015),(.0,.028),(.012,.015),(.0,.0),(-.012,.015)],[(0,0),(0,-.03)],[(-.01,-.018),(.01,-.018)]],
       [[(.006,.03),(-.006,.012),(.008,-.004),(-.004,-.03)],[(.014,.02)],[(.014,.006)],[(.014,-.008)]],
       [[(-.014,.0),(-.004,.02),(.008,.0),(-.002,-.02),(.012,-.03)],[(.012,.026),(.002,.012)]],
       [[(0,.03),(0,-.03)],[(-.014,.008),(.0,-.006),(.014,.008)],[(-.012,-.02)]]]
    cs=[]
    for k,g in enumerate(G):
        cx=-.085+k*.042
        for s in g:
            pts=[(cx+x,-T/2+.0005,H*.52+z) for x,z in s]
            if len(pts)==1:
                b=bmesh.new();bmesh.ops.create_icosphere(b,subdivisions=2,radius=.0032);bmesh.ops.translate(b,verts=b.verts,vec=Vector(pts[0]));cs.append(cutter(b))
            else:   # one cutter per stroke segment: merged overlapping cutters self-intersect and break the boolean
                P=[Vector(p) for p in pts];dense=[P[0]]
                for a_,b_ in zip(P,P[1:]):
                    for t in np.linspace(0,1,4)[1:]:dense.append(a_+(b_-a_)*t)
                for p,q in zip(dense,dense[1:]):
                    c=bmesh.new();bmesh.ops.create_cone(c,cap_ends=True,segments=8,radius1=.0022,radius2=.0022,depth=(q-p).length+.0018)
                    bmesh.ops.rotate(c,verts=c.verts,cent=(0,0,0),matrix=(q-p).to_track_quat('Z','Y').to_matrix());bmesh.ops.translate(c,verts=c.verts,vec=(p+q)/2)
                    cs.append(cutter(c))
    carve(o,cs);o=reproject(o,M['stone'][0],.12)
    # bamboo roots wrapping the slab + one culm stub with nodes
    for k in range(5):
        a0=r.uniform(0,math.tau);sp=r.uniform(.8,1.6);pts=[]
        for t in np.linspace(0,1,22):
            a=a0+t*sp*math.pi;rx=(W/2+.004)*math.cos(a);rz=(H/2+.004)*math.sin(a)+H/2;pts.append((rx,(T/2+.003)*math.sin(t*math.tau*1.5+k),rz))
        tube(f'Root_{k}',pts,r.uniform(.0018,.0034),M['bamboo'][0],6,.04)
    cpts=[(-W/2+.012,0,.0),(-W/2+.006,0,.06),(-W/2+.016,0,.13),(-W/2+.03,.0,.175)]
    tube('Bamboo_Culm',cpts,.0065,M['bamboo'][0],10,.05)
    for z in (.055,.115):lathe(f'Culm_Node_{z}',[(.0066,-.002),(.0078,0),(.0066,.002)],M['bamboo'][0],12,.02).data.transform(Matrix.Translation(Vector(np.interp(z,[p[2] for p in cpts],[p[0] for p in cpts]).item() if False else (-W/2+.007+.0,0,z))))
    return {'mud':True}

def A3_F03(M):
    """拭石魚簍: woven bamboo creel 0.25 m, crushed on one side, wooden lid peg, hemp shoulder loop, seven rubbed pebbles"""
    prof=[(0,0),(.070,0),(.080,.004),(.095,.04),(.103,.09),(.098,.14),(.082,.185),(.066,.215),(.064,.228)]
    o=lathe('Creel_Wall',prof,M['weave'][0],40,.06,smooth=False)
    inner=lathe('Creel_Inside',[(.0,.004),(.074,.004),(.090,.04),(.098,.09),(.093,.14),(.078,.185),(.060,.226)][::-1],M['weave'][0],40,.06,smooth=False)
    for p in inner.data.polygons:p.flip()
    for ob in (o,inner):   # crushed dent on the -Y side
        for v in ob.data.vertices:
            a=math.atan2(v.co.y,v.co.x);d=abs(((a+math.pi/2+math.pi)%math.tau)-math.pi)
            if d<.7 and .03<v.co.z<.16:v.co.xy*=1-.16*(1-d/.7)*math.sin((v.co.z-.03)/.13*math.pi)
    lathe('Creel_Rim',[(.060,.222),(.072,.224),(.074,.232),(.068,.238),(.058,.234)],M['bamboo'][0],40,.04)
    for z in (.205,.06):tube(f'Creel_Hoop_{z}',[(np.interp(z,[p[1] for p in prof],[p[0] for p in prof])+.002)*Vector((math.cos(t),math.sin(t),0))+Vector((0,0,z)) for t in np.linspace(0,math.tau,41)],.0028,M['bamboo'][0],6,.04)
    tube('Lid_Peg',[(-.085,0,.247),(.085,0,.247)],.008,M['wood'][0],10,.05)
    for x in (-.0,):tube('Peg_Lash',[(x+.009*math.cos(t),.011*math.sin(t),.247+.011*math.cos(t)*0) for t in np.linspace(0,math.tau*3,30)],.0022,M['hemp'][0],6,.03)
    rope('Shoulder_Loop',[(-.098,0,.20),(-.12,.0,.13),(-.10,.0,.05),(0,0,.01),(.10,0,.05),(.12,0,.13),(.098,0,.20)],.0045,M['hemp'][0],twist=14)
    r=random.Random(7)
    for k in range(7):   # seven rubbed pebbles filling the neck
        a=k/6*math.tau if k else 0;rr=0 if k==0 else .034
        b=bmesh.new();bmesh.ops.create_icosphere(b,subdivisions=3,radius=.022)
        for v in b.verts:v.co=Vector((v.co.x*1.25,v.co.y*.95,v.co.z*.75))
        bmesh.ops.rotate(b,verts=b.verts,cent=(0,0,0),matrix=Matrix.Rotation(r.uniform(0,3),3,'Z'))
        bmesh.ops.translate(b,verts=b.verts,vec=Vector((rr*math.cos(a),rr*math.sin(a),.205+.006*(k%2))))
        p=finish(f'Pebble_{k}',b,M['pebble'][0],.03)
        for poly in p.data.polygons:poly.use_smooth=True
    return {'mud':True}

def A3_F04(M):
    """三村契紙: oiled-paper bundle 0.20 × 0.13 × 0.09 tied with hemp string and bow; torn corner shows a deed with a red seal"""
    b=box_bm((.20,.13,.085),(0,0,.0425));o=finish('Bundle',b,M['oilpaper'][0],.08);bevel(o,.012,3,30)
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.subdivide_edges(bm,edges=bm.edges[:],cuts=6,use_grid_fill=True);bm.to_mesh(o.data);bm.free()
    jitter(o,.0016,41,70);jitter(o,.0006,42,200)
    carve(o,[cutter(box_bm((.08,.03,.05),(.075,-.064,.048)),'tear')]);o=reproject(o,M['oilpaper'][0],.08)
    for k in range(3):   # layered deed sheets inside the tear
        dp=box_bm((.07,.002,.04),(.072-.004*k,-.054+.004*k,.046+.003*k));bmesh.ops.rotate(dp,verts=dp.verts,cent=(.072,-.054,.046),matrix=Matrix.Rotation(math.radians(-8+5*k),3,'Y'))
        finish(f'Deed_Sheet_{k}',dp,M['paper'][0],.05)
    sl=lathe('Seal',[(0,0),(.009,0),(.009,.0006),(0,.0006)],M['seal'][0],20,.02);sl.data.transform(Matrix.Translation((.092,-.0545,.04))@Matrix.Rotation(math.radians(90),4,'X'))
    flap=box_bm((.07,.0025,.035),(.07,-.072,.074));bmesh.ops.rotate(flap,verts=flap.verts,cent=(.07,-.066,.074),matrix=Matrix.Rotation(math.radians(-35),3,'X'))
    f=finish('Torn_Flap',flap,M['oilpaper'][0],.05);jitter(f,.0008,43,150)
    # string: one band round the long way, one round the short way, bow on top
    def band(axis):
        pts=[]
        for t in np.linspace(0,math.tau,49):
            c,s=math.cos(t),math.sin(t);y=.068*np.sign(c)*min(1,abs(c)*1.6);z=.0425+.046*np.sign(s)*min(1,abs(s)*1.6)
            pts.append((0,y,z) if axis=='x' else (y*1.55,0,z))
        return pts
    rope('String_Short',band('x'),.0022,M['hemp'][0],twist=26);rope('String_Long',band('y'),.0022,M['hemp'][0],twist=38)
    for s in (-1,1):
        loop=[(0,0,.089)]+[(s*(.012+.012*math.cos(t)),.014*math.sin(t),.091+.004*math.sin(t)) for t in np.linspace(math.pi,0 if s>0 else math.tau,14)]
        rope(f'Bow_{s}',[(s*.024*abs(math.cos(t))*(1 if s>0 else 1),.012*math.sin(t),.090) for t in np.linspace(0,math.pi,14)],.002,M['hemp'][0],twist=6)
        rope(f'Tail_{s}',[(0,0,.090),(s*.018,.02,.088),(s*.03,.036,.087)],.002,M['hemp'][0],twist=4)
    k_=bmesh.new();bmesh.ops.create_icosphere(k_,subdivisions=2,radius=.0055);bmesh.ops.translate(k_,verts=k_.verts,vec=Vector((0,0,.091)));finish('Bow_Knot',k_,M['hemp'][0],.02)
    return {'mud':False,'paint':'deed'}

def A3_F05(M):
    """空心骨: hollow long bone 0.24 m, flared broken ends, five small holes along one side, water-polished"""
    n0=len(parts)
    prof=[(.016,0),(.024,.004),(.025,.014),(.019,.034),(.0145,.07),(.0135,.12),(.0145,.17),(.019,.205),(.024,.226),(.023,.236),(.016,.24)]
    o=lathe('Bone_Outer',prof,M['bone'][0],28,.06)
    inner=lathe('Bone_Inner',[(r*.62,z) for r,z in prof][::-1],M['bone'][0],28,.06)
    for p in inner.data.polygons:p.flip()
    for ob in (o,inner):   # broken, uneven rims and a slight bend
        for v in ob.data.vertices:
            a=math.atan2(v.co.y,v.co.x)
            if v.co.z<.006:v.co.z+=.003*math.sin(a*5)+.002*math.sin(a*11)
            if v.co.z>.234:v.co.z+=.003*math.sin(a*4+1)+.0015*math.sin(a*9)
            v.co.x+=.006*math.sin(v.co.z/.24*math.pi)
    jitter(o,.0007,51,80)
    cs=[]
    for k in range(5):
        c=bmesh.new();bmesh.ops.create_cone(c,cap_ends=True,segments=12,radius1=.0028-.0002*k,radius2=.0028-.0002*k,depth=.04)
        bmesh.ops.rotate(c,verts=c.verts,cent=(0,0,0),matrix=Matrix.Rotation(math.radians(90),3,'X'));bmesh.ops.translate(c,verts=c.verts,vec=Vector((.004,-.02,.165-.023*k)))
        cs.append(cutter(c))
    carve(o,cs);o=reproject(o,M['bone'][0],.06)
    lie(n0);return {'mud':False}

def HOME_F01(M):
    """刻痕小刀: small whittling chisel with cord-wrapped handle, beside a door-frame offcut with height notches and 遠"""
    n0=len(parts)
    # chisel, built along +Z then laid flat at y = +0.03
    lathe('Chisel_Handle',[(0,.068),(.0105,.068),(.0125,.08),(.0135,.11),(.0128,.14),(.0115,.158),(.0105,.163),(0,.164)],M['wood'][0],20,.04)
    for z0,z1 in ((.062,.071),(.160,.168)):lathe(f'Ferrule_{z0}',[(.0098,z0),(.0118,z0+.001),(.0118,z1-.001),(.0098,z1)],M['iron'][0],20,.02)
    tube('Cord_Wrap',[(.0132*math.cos(t),.0132*math.sin(t),.084+.0035*t/math.tau) for t in np.linspace(0,math.tau*7,140)],.0019,M['hemp'][0],5,.02)
    bl=bmesh.new();loops=[]
    for z,w,th in ((0,.022,.0012),(.004,.022,.004),(.040,.018,.0055),(.052,.007,.006),(.064,.007,.006)):
        loops.append([bm_v for bm_v in [bl.verts.new((x*w/2,y*th/2,z)) for x,y in ((1,1),(-1,1),(-1,-1),(1,-1))]])
    for a,b in zip(loops,loops[1:]):
        for k in range(4):bl.faces.new((a[k],a[(k+1)%4],b[(k+1)%4],b[k]))
    bl.faces.new(list(reversed(loops[0])));bl.faces.new(loops[-1])
    blade=finish('Chisel_Blade',bl,M['iron'][0],.04);bevel(blade,.0006,1,40)
    for o in parts[n0:]:o.data.transform(Matrix.Translation((0,.034,-.082)))
    lie(n0)
    for o in parts[n0:]:o.data.transform(Matrix.Translation((0,0,.0136)))
    # door-frame offcut lying flat, notches on its edge, 遠 carved near the top notch
    p=box_bm((.15,.042,.016),(0,-.03,.008));plank=finish('Frame_Offcut',p,M['wood'][0],.08);bevel(plank,.0015,2,30)
    bm=bmesh.new();bm.from_mesh(plank.data);bmesh.ops.subdivide_edges(bm,edges=bm.edges[:],cuts=4,use_grid_fill=True);bm.to_mesh(plank.data);bm.free();jitter(plank,.0006,61,90)
    cs=[cutter(box_bm((.0035,.014,.03),(x,-.051+.006,.008)),'notch') for x in (-.055,-.03,-.004,.024,.05)]
    tb=text_mesh('Yuan','遠',.022,M['wood'][0],.006,bold=True);bmesh.ops.translate(tb,verts=tb.verts,vec=Vector((.050,-.026,.0162)));cs.append(cutter(tb,'yuan'))
    carve(plank,cs);reproject(plank,M['wood'][0],.08)
    return {'mud':False}

def HOME_F02(M):
    """未遠草鞋: pair of straw sandals standing sole to sole, bound with an indigo oiled cloth tied in a careful knot"""
    def sole(x,name):
        out=[((.045)*math.cos(t)*(1-.12*math.sin(t)),(.115)*math.sin(t)) for t in np.linspace(0,math.tau,32,endpoint=False)]
        bm=bmesh.new();n=len(out);rs=[]
        for y,s in ((-.008,.94),(-.006,1.0),(.006,1.0),(.008,.94)):
            rs.append([bm.verts.new((x+y,px*s,pz*s+.118)) for px,pz in out])
        for a,b in zip(rs,rs[1:]):
            for i in range(n):bm.faces.new((a[i],a[(i+1)%n],b[(i+1)%n],b[i]))
        bm.faces.new(list(reversed(rs[0])));bm.faces.new(rs[-1])
        o=finish(name,bm,M['straw'][0],.05);jitter(o,.0008,len(parts),120)
        rope(name+'_Rim',[(x+(.0095 if x>0 else -.0095),(.047)*math.cos(t)*(1-.12*math.sin(t)),(.117)*math.sin(t)+.118) for t in np.linspace(0,math.tau,40)],.0042,M['straw'][0],twist=40)
        sx=x+(.012 if x>0 else -.012)
        rope(name+'_Strap',[(sx,-.03,.07),(sx+(.012 if x>0 else -.012),-.012,.15),(sx+(.006 if x>0 else -.006),0,.205),(sx+(.012 if x>0 else -.012),.012,.15),(sx,.03,.07)],.0026,M['straw'][0],twist=12)
    sole(-.024,'Sandal_L');sole(.024,'Sandal_R')
    n0=len(parts)
    # thin cloth band wrapped round both soles (elliptical ring, 5 cm tall, 4 mm thick, wrinkled), knot and ragged ends at the front
    bm=bmesh.new();seg=48;rows=[]
    for zi,z in enumerate(np.linspace(.092,.142,5)):
        for rr in (0,1):
            rows.append([bm.verts.new(((.104+.004*rr)*math.cos(t)*(1+.03*math.sin(5*t+zi)),(.024+.004*rr)*math.sin(t)*(1+.05*math.cos(4*t)),z+.004*math.sin(3*t+zi))) for t in np.linspace(0,math.tau,seg,endpoint=False)])
    inner=rows[0::2];outer=rows[1::2]
    for L,flip in ((outer,False),(inner,True)):
        for a_,b_ in zip(L,L[1:]):
            for i in range(seg):
                q=(a_[i],a_[(i+1)%seg],b_[(i+1)%seg],b_[i]);bm.faces.new(q[::-1] if flip else q)
    for i in range(seg):
        j=(i+1)%seg;bm.faces.new((inner[0][i],inner[0][j],outer[0][j],outer[0][i]));bm.faces.new((outer[-1][i],outer[-1][j],inner[-1][j],inner[-1][i]))
    band=finish('Cloth_Band',bm,M['cloth'][0],.05);jitter(band,.0012,70,80)
    k=bmesh.new();bmesh.ops.create_icosphere(k,subdivisions=2,radius=.015)
    for v in k.verts:v.co=Vector((v.co.x*1.3,v.co.y*.8,v.co.z))
    bmesh.ops.translate(k,verts=k.verts,vec=Vector((0,-.034,.118)));kn=finish('Cloth_Knot',k,M['cloth'][0],.03);jitter(kn,.0016,71,60)
    for s in (-1,1):
        e=box_bm((.034,.003,.03),(s*.026,-.036,.094));bmesh.ops.subdivide_edges(e,edges=e.edges[:],cuts=3,use_grid_fill=True)
        bmesh.ops.rotate(e,verts=e.verts,cent=(0,-.036,.118),matrix=Matrix.Rotation(math.radians(s*35),3,'Y'));ee=finish(f'Cloth_End_{s}',e,M['cloth'][0],.04);jitter(ee,.0018,72+s,90)
    # soles were built in the YZ plane: turn the pair so the soles face the front (-Y), like the three-view
    for o in parts[:n0]:
        o.data.transform(Matrix.Rotation(math.radians(90),4,'Z'))
        o.data.transform(Matrix.Translation((-.050,.024,0) if 'Sandal_L' in o.name else (.050,-.024,0)))   # side by side, both soles to the front
    return {'mud':False}

PROPS={'A2-F01':A2_F01,'A2-F02':A2_F02,'A2-F03':A2_F03,'A2-F04':A2_F04,'A2-F05':A2_F05,'A3-F01':A3_F01,'A3-F02':A3_F02,
       'A3-F03':A3_F03,'A3-F04':A3_F04,'A3-F05':A3_F05,'HOME-F01':HOME_F01,'HOME-F02':HOME_F02}

# ---------------- bake / LOD / export ----------------
def run(pid):
    assert (REF/f'{pid}-three-view.png').stat().st_size>10000,f'{pid}: AI three-view must be saved before modelling'
    bpy.ops.wm.read_factory_settings(use_empty=True);parts.clear()
    sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=16;sc.render.bake.margin=10
    M=make_sources();meta=PROPS[pid](M)
    def sel(*obs):
        bpy.ops.object.select_all(action='DESELECT')
        for o in obs:o.select_set(True)
        bpy.context.view_layer.objects.active=obs[0]
    # ground the prop: bottom at z=0, centred on XY
    pts=np.array([(o.matrix_world@v.co)[:] for o in parts for v in o.data.vertices]);lo,hi=pts.min(0),pts.max(0)
    off=Vector((-(lo[0]+hi[0])/2,-(lo[1]+hi[1])/2,-lo[2]))
    for o in parts:o.data.transform(Matrix.Translation(off))
    meta['offset']=np.array(off[:])
    srcparts=list(parts)
    cp=[]
    for o in srcparts:d=o.copy();d.data=o.data.copy();sc.collection.objects.link(d);cp.append(d)
    sel(*cp);bpy.ops.object.join();L0=bpy.context.object;L0.name=L0.data.name=f'{pid}_LOD0'
    bm=bmesh.new();bm.from_mesh(L0.data);bmesh.ops.triangulate(bm,faces=bm.faces);bm.to_mesh(L0.data);bm.free()
    for u in [u for u in L0.data.uv_layers if u.name!='Tiled']:L0.data.uv_layers.remove(u)   # stray layers (e.g. from booleans) would shadow the bake UV
    for o in sc.objects:o.hide_render=o is not L0
    bu=L0.data.uv_layers.new(name='Bake');L0.data.uv_layers.active=bu;sel(L0)
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(55),island_margin=.003,area_weight=0,scale_to_bounds=False);bpy.ops.uv.pack_islands(margin=.003,rotate=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    mats=list(L0.data.materials);metal={m.name:v for m,v in M.values()}
    def target(name,data=False):
        im=bpy.data.images.new(name,RES,RES,alpha=False,float_buffer=data)
        for m in mats:
            nt=m.node_tree;t=nt.nodes.get('BAKE_TARGET') or nt.nodes.new('ShaderNodeTexImage');t.name='BAKE_TARGET';t.image=im;nt.nodes.active=t
        return im
    def bake(name,type,data=False,**kw):
        im=target(name,data);sel(L0);bpy.ops.object.bake(type=type,**kw);return np.array(im.pixels[:],dtype=np.float32).reshape(RES,RES,4)
    def emit(fn):
        saved=[]
        for m in mats:
            nt=m.node_tree;out=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL');old=out.inputs['Surface'].links[0].from_socket
            em=nt.nodes.new('ShaderNodeEmission');fn(nt,m,em);nt.links.new(em.outputs[0],out.inputs['Surface']);saved.append((nt,out,old,em))
        return saved
    def restore(s):
        for nt,out,old,em in s:nt.links.new(old,out.inputs['Surface']);nt.nodes.remove(em)
    alb=bake('alb','DIFFUSE',pass_filter={'COLOR'});sc.cycles.samples=64;ao=bake('ao','AO',True)[...,0];sc.cycles.samples=16
    rough=bake('rough','ROUGHNESS',True)[...,0];nrm=bake('nrm','NORMAL',True,normal_space='TANGENT')
    s=emit(lambda nt,m,em:em.inputs['Color'].__setattr__('default_value',(metal.get(m.name,0),)*3+(1,)));met=bake('met','EMIT',True)[...,0];restore(s)
    def edges(nt,m,em):
        g=nt.nodes.new('ShaderNodeNewGeometry');r=nt.nodes.new('ShaderNodeValToRGB');r.color_ramp.elements[0].position=.53;r.color_ramp.elements[1].position=.62
        nt.links.new(g.outputs['Pointiness'],r.inputs['Fac']);nt.links.new(r.outputs['Color'],em.inputs['Color'])
    s=emit(edges);edge=bake('edge','EMIT',True)[...,0];restore(s)
    s=emit(lambda nt,m,em:nt.links.new(nt.nodes.new('ShaderNodeNewGeometry').outputs['Position'],em.inputs['Color']));pos=bake('pos','EMIT',True)[...,:3];restore(s)
    filled=np.abs(pos).sum(2)>1e-7;pz=pos[...,2]
    col=alb[...,:3]*(.60+.40*ao[...,None])
    wear=np.clip(edge,0,1)[...,None];lift=np.where(met[...,None]>.1,np.array([.20,.16,.08]),np.array([.05,.035,.015]))  # bronze edges polish to bright metal
    col=np.clip(col*(1+.40*wear)+wear*lift,0,1);rough=np.clip(rough-.25*wear[...,0]*(met>.1),0,1)
    if meta.get('mud'):
        mudn=np.clip(np.sin(pos[...,0]*300)*np.sin(pos[...,1]*270)*.5+.5,0,1);mud=filled*np.clip((.03-pz)/.03,0,1)*(.5+.5*mudn)
        col=col*(1-mud[...,None])+np.array([.24,.19,.13])*mud[...,None];rough=np.clip(rough+.1*mud,0,1)
    if meta.get('paint')=='hesper':   # painted band on the outer glaze: cream band, golden fruits, green leaves, blue vine lines
        Rj=meta['Rj'];q=pos-meta['offset'];px,py=q[...,0],q[...,1];rr=np.hypot(px,py-Rj);a=np.arctan2(px,Rj-py)*Rj;z=q[...,2]
        outer=filled&(rr>Rj-.001)&(rr<Rj+.003)
        band=outer&(z>.004)&(z<.032);col=np.where(band[...,None],col*.15+np.array([.80,.74,.58])*.85,col)
        for zl in (.001,.0042,.0318,.035):
            ln=outer&(np.abs(z-zl)<.0007);col=np.where(ln[...,None],np.array([.14,.24,.42]),col)
        vine=band&(np.abs(z-(.018+.006*np.sin(a*90)))<.0007);col=np.where(vine[...,None],np.array([.16,.28,.46]),col)
        for k in range(-3,4):
            ax=k*.028;d=np.hypot(a-ax,z-.018);fr=band&(d<.0085)
            col=np.where(fr[...,None],np.array([.80,.62,.18])*(1-.25*np.clip(d/.0085,0,1)[...,None]**2),col)
            for s in (-1,1):
                lx,lz=a-(ax+s*.013),z-(.022+.003*s);lf=band&((lx/.0068)**2+(lz/.0030)**2<1)
                col=np.where(lf[...,None],np.array([.20,.36,.27]),col)
        crack=outer&(np.abs(np.sin(px*900+np.sin(z*700)*2))<.02);col=np.where(crack[...,None],col*.7,col)   # crazing in the glaze
    if meta.get('paint')=='deed':   # blurred ink columns on the exposed deed sheet
        q=pos-meta['offset'];ink=filled&(np.abs(q[...,1]+.054)<.004)&(q[...,0]>.04)&(q[...,0]<.085)&(q[...,2]>.03)&(q[...,2]<.064)
        strokes=(np.abs(np.sin(q[...,0]*520))<.35)&(np.abs(np.sin(q[...,2]*900+np.sin(q[...,0]*300)))<.6)
        col=np.where((ink&strokes)[...,None],col*.35+np.array([.06,.06,.07])*.65,col)
    def save(name,rgba,data=False):
        im=bpy.data.images.new(name,RES,RES,alpha=True)
        if data:im.colorspace_settings.name='Non-Color'
        im.pixels.foreach_set(np.ascontiguousarray(rgba,dtype=np.float32).ravel());im.filepath_raw=str(TEX/f'{name}.png');im.file_format='PNG';im.save();return im
    one=np.ones((RES,RES),np.float32)
    ALB=save(f'{pid}_Albedo',np.dstack([col,one]));NRM=save(f'{pid}_Normal',nrm,True)
    save(f'{pid}_MaskURP',np.dstack([met,ao,0*one,1-rough]),True);ORM=save(f'{pid}_ORM',np.dstack([ao,rough,met,one]),True)
    fm=bpy.data.materials.new(f'{pid}_Baked');fm.use_nodes=True;nt=fm.node_tree;bs=nt.nodes['Principled BSDF']
    def tex(im):t=nt.nodes.new('ShaderNodeTexImage');t.image=im;return t
    nt.links.new(tex(ALB).outputs['Color'],bs.inputs['Base Color'])
    nmn=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex(NRM).outputs['Color'],nmn.inputs['Color']);nt.links.new(nmn.outputs['Normal'],bs.inputs['Normal'])
    sp=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex(ORM).outputs['Color'],sp.inputs['Color']);nt.links.new(sp.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sp.outputs['Blue'],bs.inputs['Metallic'])
    lods=[L0]
    for L,ratio in ((1,.5),(2,.15)):
        d=L0.copy();d.data=L0.data.copy();sc.collection.objects.link(d);d.name=d.data.name=f'{pid}_LOD{L}'
        m=d.modifiers.new('d','DECIMATE');m.ratio=ratio;m.use_collapse_triangulate=True;sel(d);bpy.ops.object.modifier_apply(modifier='d');lods.append(d)
    for d in lods:
        uvs=d.data.uv_layers;uvs.remove(uvs['Tiled']);uvs['Bake'].name='UVMap';d.data.materials.clear();d.data.materials.append(fm);d.hide_render=d is not L0
    root=bpy.data.objects.new(f'{pid}_GroundOrigin',None);sc.collection.objects.link(root)
    for d in lods:d.parent=root
    pts=np.array([v.co[:] for v in L0.data.vertices]);lo,hi=pts.min(0),pts.max(0);dims=hi-lo
    fits=bool(all(dims[i]<=LIMIT[i]+1e-6 for i in range(3)) or all(sorted(dims)[i]<=sorted(LIMIT)[i]+1e-6 for i in range(3)))
    src=bpy.data.collections.new(f'{pid}_SourceParts');sc.collection.children.link(src)
    for o in srcparts:
        for c in list(o.users_collection):c.objects.unlink(o)
        src.objects.link(o);o.hide_render=True
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE/f'{pid}.blend'))
    sel(root,L0);bpy.ops.export_scene.gltf(filepath=str(OUT/f'{pid}.glb'),use_selection=True,export_format='GLB',export_apply=True)
    sel(root,*lods);bpy.ops.export_scene.fbx(filepath=str(OUT/f'{pid}.fbx'),use_selection=True,object_types={'MESH','EMPTY'},global_scale=1.0,apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_ALL',bake_space_transform=True,axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='FACE',
        use_tspace=True,add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE',embed_textures=False)
    tri=lambda o:sum(len(p.vertices)-2 for p in o.data.polygons)
    info={'id':pid,'dimensions_xyz_m':[round(float(x),4) for x in dims],'collection_limit_m':LIMIT,'fits_shelf':fits,
          'triangles':{f'LOD{i}':tri(o) for i,o in enumerate(lods)},'materials':1,'source_parts':len(srcparts),
          'reference':f'art/references/qingxi-sightings-c/{pid}-three-view.png','origin':'bottom centre','textures':f'{RES}² Albedo/Normal/MaskURP/ORM',
          'collision':{'shape':'box','size_m':[round(float(x),3) for x in dims]}}
    print('SIGHT_DONE',json.dumps(info,ensure_ascii=False));return info
ids=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else list(PROPS)
infos=[run(i) for i in ids]
mf=OUT/'model_info.json';old=json.loads(mf.read_text(encoding='utf-8')) if mf.exists() else {}
old.update({i['id']:i for i in infos});mf.write_text(json.dumps(old,ensure_ascii=False,indent=1),encoding='utf-8')
