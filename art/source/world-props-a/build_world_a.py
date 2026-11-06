"""承天 · 11/03 A 包的世界模型（Johnnnny0823）：獵人工具棚、倒下的土地公小廟、熄掉的獵人營地、倒塌的歇腳亭、載貨板車、土地祠、
路牌、觀景石凳、草垛、路緣碎石、踏石、溪石、淨水蓮生長階段、練功器材（練功地面、碎石小徑是貼圖件，見 build_ground_a.py）。
Pipeline adapted from art/source/qingxi-day12-c/build_day12.py (painterly tiled sources -> grouped Cycles bake -> numpy finish ->
Albedo / Normal / MaskURP / ORM per group -> LOD1 <= 50 % and <= 100k tris, LOD2 <= 15 % and <= 25k (budget shared on sqrt of group size) -> _Collision -> .blend, FBX (all LODs + collision), no GLB since the 11/07 review: one format per item; FBX without tangents, Unity computes MikkTSpace on import).
Added for quality-tiers-v1 §4: groups named Detail_<Name> export as removable sub-objects Detail_<Name>_LOD0/1/2 and are listed in
model_info.json detailObjects; every item carries minTier; pivots (cart wheels) keep their origin on the axle; a Glow group is the
shrine's separate emissive mesh.
Each item is modelled only after its four AI three-view candidates are saved in art/references/<ID>/ and one is picked in prompt.txt
("選用：", AGENTS.md order).
Origin: footprint centre, bottom at z = 0, Blender -Y is the front. No ground plate.
blender -b --factory-startup -P build_world_a.py -- RK09 [WM08 ...]
"""
import bpy,bmesh,json,math,sys,random,os
from pathlib import Path
from mathutils import Vector,Matrix
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];PKG='world-props-a'
REF=ROOT/'art/references';TEX=ROOT/'art/textures'/PKG;OUT=ROOT/'art/exports'/PKG
for p in (TEX,OUT):p.mkdir(parents=True,exist_ok=True)
# size limits (W x D x H m) and quality tier from the package table
LIMITS={'SC04':(3.6,3,2.8),'SC01':(1.6,1.4,1.8),'SC02':(3,3,1.2),'SC03':(4,4,3.2),'RK05':(3.2,1.6,1.4),'RK06':(2.4,2,2.8),
        'RK01A':(1.2,.4,2.6),'RK01B':(1.2,.4,2.6),'RK09':(2,.8,.6),'RK10A':(2.4,2.4,2.2),'RK10B':(2.4,2.4,2.2),
        'RK12A':(2,2,.3),'RK12B':(2,2,.3),'RK12C':(2,2,.3),'RK12D':(2,2,.3),'WM08A':(1,1,.4),'WM08B':(1,1,.4),'WM08C':(1,1,.4),
        'WM10A':(.5,.5,.5),'TY03A':(.8,.8,.7),'TY03B':(.8,.8,.7),'TY03C':(.8,.8,.7),'TY03D':(.8,.8,.7),'WM10B':(1.2,1.2,.8),'WM10C':(3,3,1.4),'WM10D':(3,1.2,.8),'TY03':(.8,.8,.7),'TY06':(1.4,.8,.6)}
TIER={k:'standard' for k in LIMITS};TIER.update({'RK10B':'high','RK12A':'high','RK12B':'high','RK12C':'high','RK12D':'high'})
REFID=lambda pid:pid[:4]   # RK01A -> RK01 reference folder

# ---------------- painterly tiled source textures (512², tileable) ----------------
R=512;rng=np.random.default_rng(1101)
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
def strokes(c,aniso,lo=.62):  # a few visible brush strokes, not a field of noise
    return np.clip((fbm(c,2,aniso)-lo)*4,0,1)
GLOW={}
def make_sources():
    S={}
    soft=fbm(2,3);warp=fbm(2,2)
    # timber: palette #6a4630 → #a87a50, sun-faded grey, long soft grain, few cracks
    grain=(.5+.5*np.sin(math.tau*(X*7+warp*.6)))**2;cr=np.clip((fbm(30,2,aniso=14)-.70)*6,0,1);st=strokes(6,6)
    t=np.clip(.50+.30*(soft-.5)*2-.12*grain+.12*st-.30*cr,0,1)
    S['wood']=(lerp((.33,.25,.19),(.58,.46,.35),t)*(1-.10*(fbm(3,2)>.6)[...,None])+.05*np.array([.4,.4,.42])*fbm(4,2)[...,None],.5*grain+1.2*cr+.3*st,2.4,.78,0,0)
    S['oldwood']=(lerp((.25,.21,.17),(.50,.43,.35),np.clip(t*1.1-.05,0,1))*(1-.25*cr[...,None]),.8*grain+1.6*cr,2.8,.86,0,0)
    S['planks']=(lerp((.33,.23,.16),(.56,.41,.28),np.clip(t*.9+.1*((X*5)%1<.04),0,1))*(1-.35*((X*5)%1<.03))[...,None],.5*grain+1.5*((X*5)%1<.03)+cr,2.6,.8,0,0)
    # stone: warm granite (#8a8478 → #b8b0a0) with lichen dots; blue-grey garden stone
    big=fbm(3,4);lich=np.clip((fbm(40,2)-.72)*5,0,1);st=strokes(5,3,.6)
    blot=np.clip((fbm(2,3)-.45)*2.2,0,1);S['granite']=(lerp((.36,.34,.31),(.64,.61,.55),np.clip(big*.8+.25*blot+.15*st-.05,0,1))*(1-.10*lich[...,None])+lich[...,None]*np.array([.06,.08,.02]),big+.5*fbm(24,2)+.6*lich,3.2,.88,0,0)
    S['bluestone']=(lerp((.26,.30,.33),(.52,.56,.58),np.clip(big*.8+.25*blot+.15*st-.05,0,1))*(1-.08*lich[...,None])+lich[...,None]*np.array([.10,.12,.10]),big+.5*fbm(24,2)+.6*lich,3.2,.88,0,0)
    S['plinth']=(lerp((.42,.40,.36),(.64,.61,.55),np.clip(big+.12*st,0,1)),big+.4*fbm(16,2),3.0,.9,0,0)
    # roof tile: blue-grey #3e4e58 / #2c3640, soft tonal patches
    S['tile']=(lerp((.18,.22,.26),(.34,.40,.45),np.clip(soft*.8+.2*strokes(8,2),0,1)),fbm(20,2),1.4,.72,0,0)
    S['tile_new']=(lerp((.24,.29,.34),(.38,.45,.51),soft),fbm(20,2),1.2,.6,0,0)
    nodes=np.clip(1-np.abs(((Y*3)%1)-.5)*30,0,1);S['bamboo']=(lerp((.46,.42,.24),(.70,.63,.38),.6*soft+.4*fbm(4,2,aniso=6))*(1-.28*nodes[...,None]),.3*fbm(12,2,aniso=8)+nodes,1.8,.6,0,0)
    S['bamboo_old']=(lerp((.33,.29,.20),(.54,.48,.34),.6*soft+.4*fbm(4,2,aniso=6))*(1-.28*nodes[...,None]),.3*fbm(12,2,aniso=8)+nodes,1.8,.7,0,0)
    tw=.5+.5*np.sin(math.tau*((X+Y)*12));S['hemp']=(lerp((.38,.30,.20),(.60,.50,.34),np.clip(tw*.6+.4*soft,0,1)),tw,1.2,.92,0,0)
    S['rope_new']=(lerp((.62,.55,.38),(.80,.74,.56),np.clip(tw*.6+.4*soft,0,1)),tw,1.2,.9,0,0)
    S['paper']=(lerp((.78,.72,.58),(.90,.85,.72),fbm(4,3))*(1-.18*np.clip((fbm(10,2)-.62)*4,0,1))[...,None],fbm(30,2),.6,.9,0,1)
    S['lantern']=(lerp((.78,.60,.40),(.90,.74,.52),fbm(4,3)),.5+.5*np.sin(Y*math.tau*14),.8,.85,0,1)
    S['lacquer_red']=(lerp((.42,.10,.07),(.58,.18,.10),soft),fbm(10,2),.6,.55,0,0)
    S['clay']=(lerp((.40,.22,.14),(.62,.38,.25),np.clip(soft+.1*strokes(6,2),0,1)),fbm(14,3),1.6,.88,0,0)
    S['glaze']=(lerp((.12,.24,.23),(.27,.42,.38),np.clip(soft*.9+.2*fbm(5,3),0,1))*(1-.18*np.clip((fbm(3,2)-.55)*3,0,1))[...,None],.3*fbm(10,2),.5,.32,0,0)
    S['iron']=(lerp((.17,.15,.14),(.40,.24,.14),np.clip((fbm(6,4)-.35)*1.8,0,1)),fbm(18,3),2.4,.8,.3,0)
    S['linen']=(lerp((.70,.66,.56),(.84,.80,.70),soft)*(1-.06*(np.sin(X*900)>.6))[...,None],.5*np.sin(X*700)+.5*np.sin(Y*700),.7,.95,0,0)
    wx=((X*10)%1<.5);wy=((Y*10)%1<.5);ov=np.where(wx^wy,.5+.5*np.sin(X*10*math.tau)**2,.5+.5*np.sin(Y*10*math.tau)**2)
    S['weave']=(lerp((.26,.20,.12),(.54,.44,.27),ov*.75+.25*soft)*(1-.15*np.clip((fbm(3,2)-.5)*3,0,1))[...,None],ov,3.2,.85,0,0)
    S['moss']=(lerp((.22,.30,.12),(.42,.50,.20),fbm(8,3)),fbm(16,3),3.0,.95,0,0)
    S['bronze']=(lerp((.22,.20,.12),(.42,.36,.20),np.clip(soft+.15*fbm(12,2),0,1))+np.clip((fbm(6,3)-.62)*3,0,1)[...,None]*np.array([.05,.14,.10]),fbm(14,3),1.2,.45,.75,0)
    S['flame']=(lerp((.95,.62,.22),(1.0,.84,.48),fbm(3,2)),fbm(6,2)*.1,.2,.6,0,1)
    S['fruit_orange']=(lerp((.78,.38,.08),(.92,.56,.16),fbm(6,2)),fbm(30,2)*.3,.5,.45,0,0)
    S['fruit_red']=(lerp((.55,.14,.10),(.78,.30,.16),fbm(6,2)),fbm(30,2)*.3,.5,.45,0,0)
    sl=np.clip((.5+.5*np.sin(math.tau*(X*40+fbm(3,2)*2)))**3,0,1)
    S['straw']=(lerp((.58,.44,.18),(.86,.72,.40),np.clip(.55*sl+.45*fbm(5,2,aniso=8),0,1)),.8*sl+.3*fbm(20,2,aniso=10),1.6,.85,0,0)
    S['petal']=(lerp((.84,.88,.80),(.97,.96,.90),np.clip(fbm(4,2)*.7+.3*Y,0,1)),fbm(20,2)*.2,.3,.55,0,0)
    S['lotus_glow']=(lerp((.78,.86,.55),(.96,.94,.70),fbm(4,2)),fbm(10,2)*.1,.2,.5,0,1)
    S['hide']=(lerp((.46,.34,.22),(.70,.58,.42),np.clip(.6*fbm(4,3)+.4*fbm(16,2,aniso=3),0,1)),fbm(30,2)*.4,.8,.9,0,0)
    S['thatch']=(lerp((.30,.25,.16),(.58,.50,.32),np.clip(.5*sl+.5*fbm(5,2,aniso=6),0,1))*(1-.25*np.clip((fbm(3,2)-.55)*3,0,1))[...,None]+np.clip((fbm(4,3)-.6)*3,0,1)[...,None]*np.array([.02,.06,.0]),.8*sl+.3*fbm(20,2,aniso=10),1.8,.92,0,0)
    S['incense']=(lerp((.50,.14,.10),(.66,.22,.14),fbm(4,2)),fbm(30,2)*.2,.4,.8,0,0)
    S['soil']=(lerp((.28,.21,.14),(.45,.35,.24),fbm(8,3)),fbm(24,3),2.4,.95,0,0)
    S['water']=(lerp((.06,.16,.16),(.12,.26,.25),soft),fbm(6,2)*.2,.3,.05,0,0)
    S['charcoal']=(lerp((.05,.05,.05),(.20,.13,.10),fbm(20,2)),fbm(20,2),2,.9,0,0)
    S['ember']=(lerp((.55,.18,.06),(.85,.40,.12),fbm(20,2)),fbm(20,2),1,.9,0,1)
    for k,(c0,c1) in {'herb_green':((.20,.32,.12),(.38,.52,.22)),'herb_sage':((.36,.42,.30),(.56,.62,.46)),'herb_dry':((.40,.34,.18),(.62,.54,.30)),
                      'herb_olive':((.30,.32,.14),(.48,.50,.24)),'flower_violet':((.36,.30,.48),(.54,.46,.66)),'flower_gold':((.62,.46,.14),(.82,.66,.26)),
                      'leaf_fallen':((.42,.28,.14),(.66,.46,.22))}.items():
        S[k]=(lerp(c0,c1,np.clip(.6*fbm(6,2)+.4*(.5+.5*np.sin(X*math.tau*3)),0,1)),fbm(20,2),1,.85,0,0)
    out={}
    for k,(alb,h,s,r,m,glow) in S.items():
        mat=bpy.data.materials.new('src_'+k);mat.use_nodes=True;nt=mat.node_tree;bs=nt.nodes['Principled BSDF']
        bs.inputs['Roughness'].default_value=r;bs.inputs['Metallic'].default_value=m
        uvn=nt.nodes.new('ShaderNodeUVMap');uvn.uv_map='Tiled'
        ta=nt.nodes.new('ShaderNodeTexImage');ta.image=img('alb_'+k,alb);nt.links.new(uvn.outputs['UV'],ta.inputs['Vector']);nt.links.new(ta.outputs['Color'],bs.inputs['Base Color'])
        tn=nt.nodes.new('ShaderNodeTexImage');tn.image=nmap('nrm_'+k,h,s);nt.links.new(uvn.outputs['UV'],tn.inputs['Vector'])
        nm=nt.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.8;nt.links.new(tn.outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
        out[k]=mat;GLOW[mat.name]=(m,glow)
    return out

# ---------------- geometry helpers ----------------
parts=[]
def link(o,grp):bpy.context.scene.collection.objects.link(o);o['grp']=grp;parts.append(o);return o
def vnoise3(x,y,z,f,seed=0):
    """3D value noise on numpy arrays (positions in metres, f = cells per metre): hashed lattice, smoothstep trilinear blend"""
    x,y,z=x*f+seed*17.3,y*f+seed*5.1,z*f+seed*11.7;xi,yi,zi=np.floor(x),np.floor(y),np.floor(z);u,v,w=x-xi,y-yi,z-zi
    u,v,w=u*u*(3-2*u),v*v*(3-2*v),w*w*(3-2*w);xi,yi,zi=xi.astype(np.int64),yi.astype(np.int64),zi.astype(np.int64)
    def h(a,b,c):
        n=(a*73856093)^(b*19349663)^(c*83492791)^(seed*2654435761);n=(n^(n>>13))*1274126177;return ((n^(n>>16))&0xffff)/65535.0
    l=lambda a,b,t:a+(b-a)*t
    return l(l(l(h(xi,yi,zi),h(xi+1,yi,zi),u),l(h(xi,yi+1,zi),h(xi+1,yi+1,zi),u),v),
             l(l(h(xi,yi,zi+1),h(xi+1,yi,zi+1),u),l(h(xi,yi+1,zi+1),h(xi+1,yi+1,zi+1),u),v),w)

def vfbm3(x,y,z,f,oct=3,seed=0):
    t=0;a=1;n=0
    for o in range(oct):t+=a*vnoise3(x,y,z,f*2**o,seed+o);n+=a;a*=.5
    return t/n

def orient_out(bm):
    """recalc_face_normals can pick the inward side on a closed part whose noise/chip cuts fold it; flip any closed island
    whose signed volume is negative so every solid faces outward"""
    bm.verts.ensure_lookup_table();par=list(range(len(bm.verts)))
    def fd(i):
        while par[i]!=i:par[i]=par[par[i]];i=par[i]
        return i
    for e in bm.edges:
        a,b=fd(e.verts[0].index),fd(e.verts[1].index)
        if a!=b:par[a]=b
    closed={};vol={}
    for e in bm.edges:
        g=fd(e.verts[0].index);closed[g]=closed.get(g,True) and len(e.link_faces)==2
    for f in bm.faces:
        g=fd(f.verts[0].index);vs=[v.co for v in f.verts]
        vol[g]=vol.get(g,0)+sum(vs[0].dot(vs[i].cross(vs[i+1])) for i in range(1,len(vs)-1))/6
    bad=[f for f in bm.faces if closed.get(fd(f.verts[0].index)) and vol[fd(f.verts[0].index)]<-1e-12]
    if bad:bmesh.ops.reverse_faces(bm,faces=bad)

def finish(name,bm,mat,grp,scale=.4,uv=None):
    """tiled UV: box projection on principal axes, or uv=(u,v) callables of a world point for cylinders"""
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces);orient_out(bm);lay=bm.loops.layers.uv.get('Tiled') or bm.loops.layers.uv.new('Tiled')
    if uv:
        per=getattr(uv[0],'period',None)
        for f in bm.faces:
            us=[uv[0](l.vert.co) for l in f.loops]
            if per and max(us)-min(us)>per/2:us=[u+per if u<0 else u for u in us]   # face across the atan2 seam: keep it on one side
            for l,u in zip(f.loops,us):l[lay].uv=(u/scale,uv[1](l.vert.co)/scale)
    else:
        pts=np.array([v.co[:] for v in bm.verts]);c=pts.mean(0)
        try:_,_,vt=np.linalg.svd(pts-c,full_matrices=False);A,S1,S2=[Vector(v) for v in vt]
        except Exception:A,S1,S2=Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))
        for f in bm.faces:
            n=f.normal;k=int(np.argmax([abs(n.dot(A)),abs(n.dot(S1)),abs(n.dot(S2))]))
            for l in f.loops:
                p=l.vert.co-Vector(c);u,v={0:(p.dot(S1),p.dot(S2)),1:(p.dot(S2),p.dot(A)),2:(p.dot(S1),p.dot(A))}[k];l[lay].uv=(u/scale,v/scale)
    me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free();o=bpy.data.objects.new(name,me);me.materials.append(mat)
    return link(o,grp)
def cyl_uv(r):
    f=lambda p:math.atan2(p.y,p.x)*r;f.period=math.tau*r;return (f,lambda p:p.z)
def lathe(name,profile,mat,grp,seg=48,scale=.4,smooth=True,cyl=None,center=(0,0,0)):
    """profile: [(r,z)...] bottom→top; revolved around Z, then moved to center"""
    bm=bmesh.new();rings=[]
    for r,z in profile:
        rings.append([bm.verts.new((r*math.cos(math.tau*i/seg),r*math.sin(math.tau*i/seg),z)) if r>1e-6 else None for i in range(seg)])
    for a,b in zip(rings,rings[1:]):
        if a[0] is not None and b[0] is not None:
            for i in range(seg):j=(i+1)%seg;bm.faces.new((a[i],a[j],b[j],b[i]))
    for idx,(r,z) in [(0,profile[0]),(len(profile)-1,profile[-1])]:
        if r<=1e-6:
            nb=rings[1] if idx==0 else rings[-2];c=bm.verts.new((0,0,z))
            for i in range(seg):j=(i+1)%seg;bm.faces.new((nb[j],nb[i],c) if idx==0 else (nb[i],nb[j],c))
    bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-7)
    for f in bm.faces:f.smooth=smooth
    o=finish(name,bm,mat,grp,scale,uv=cyl_uv(max(r for r,z in profile)) if cyl else None)
    o.data.transform(Matrix.Translation(center));return o
def tube(name,pts,r,mat,grp,sides=8,scale=.3,caps=True,radii=None):
    pts=[Vector(p) for p in pts];bm=bmesh.new();rings=[];prev=None
    for i,p in enumerate(pts):
        t=(pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]).normalized()
        u=(prev-t*prev.dot(t)).normalized() if prev is not None else t.orthogonal().normalized();prev=u;v=t.cross(u);rr=radii[i] if radii else r
        rings.append([bm.verts.new(p+(u*math.cos(math.tau*k/sides)+v*math.sin(math.tau*k/sides))*rr) for k in range(sides)])
    for a,b in zip(rings,rings[1:]):
        for k in range(sides):bm.faces.new((a[k],a[(k+1)%sides],b[(k+1)%sides],b[k]))
    if caps:bm.faces.new(list(reversed(rings[0])));bm.faces.new(rings[-1])
    for f in bm.faces:f.smooth=True
    return finish(name,bm,mat,grp,scale)
def rope(name,pts,r,mat,grp,plies=3,twist=None,sides=5):
    P=[Vector(p) for p in pts];L=sum((b-a).length for a,b in zip(P,P[1:]));twist=twist or L/(r*14);dense=[]
    for a,b in zip(P,P[1:]):
        n=max(2,int((b-a).length/(r*1.0)))
        for i in range(n):dense.append(a+(b-a)*(i/n))
    dense.append(P[-1]);res=[]
    for k in range(plies):
        path=[];s=0
        for i,p in enumerate(dense):
            if i:s+=(p-dense[i-1]).length
            t=(dense[min(i+1,len(dense)-1)]-dense[max(i-1,0)]).normalized();u=t.orthogonal().normalized();v=t.cross(u)
            ang=math.tau*k/plies+s/L*twist*math.tau;path.append(p+(u*math.cos(ang)+v*math.sin(ang))*r*.55)
        res.append(tube(f'{name}_ply{k+1}',path,r*.52,mat,grp,sides,.1))
    return res
def lashing(name,center,axis,r,turns,mat,grp,width=None,cord=.006):
    """rope wrapped around a pole: helix of `turns` around `axis` through `center`"""
    axis=Vector(axis).normalized();u=axis.orthogonal().normalized();v=axis.cross(u);width=width or turns*cord*2.4;pts=[]
    n=turns*16
    for i in range(n+1):
        a=math.tau*i/16;pts.append(Vector(center)+axis*(-width/2+width*i/n)+(u*math.cos(a)+v*math.sin(a))*(r+cord))
    return tube(name,pts,cord,mat,grp,6,.1)
def box_bm(size,center=(0,0,0)):
    bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
    for v in bm.verts:v.co=Vector([center[i]+v.co[i]*size[i] for i in range(3)])
    return bm
def bevel(o,w,segs=2,angle=35):
    m=o.modifiers.new('wear','BEVEL');m.width=w;m.segments=segs;m.limit_method='ANGLE';m.angle_limit=math.radians(angle);m.use_clamp_overlap=True
    apply(o,m)
def solidify_uv(o,th,offset,scale):
    """solidify a sheet that keeps its continuous tiled UVs: the generated back shell's UVs are shifted by the sheet thickness
    (in tiled units) so the rim faces get a real strip of texture instead of zero UV area"""
    vg=o.vertex_groups.new(name='_shell');m=o.modifiers.new('t','SOLIDIFY');m.thickness=th;m.offset=offset;m.shell_vertex_group='_shell';apply(o,m)
    me=o.data;gi=o.vertex_groups['_shell'].index;sh=np.zeros(len(me.vertices),bool)
    for v in me.vertices:sh[v.index]=any(g.group==gi and g.weight>.5 for g in v.groups)
    d=th/scale/math.sqrt(2);lay=me.uv_layers['Tiled']
    for l in me.loops:
        if sh[l.vertex_index]:lay.data[l.index].uv+=Vector((d,d))
    o.vertex_groups.remove(o.vertex_groups['_shell'])

def apply(o,m):
    bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.modifier_apply(modifier=m.name);o.select_set(False)
def subdiv(o,cuts):
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.subdivide_edges(bm,edges=bm.edges,cuts=cuts,use_grid_fill=True);bm.to_mesh(o.data);bm.free()
def jitter(o,amt,seed=1,freq=6):
    # normals snapshotted first: reading v.normal after moving vertices re-derives it from the half-moved mesh and folds the surface
    r=random.Random(seed);ph=[r.uniform(0,9) for _ in range(6)];me=o.data;me.update();n=len(me.vertices)
    co=np.empty(n*3);me.vertices.foreach_get('co',co);co=co.reshape(n,3);nr=np.empty(n*3);me.vertices.foreach_get('normal',nr);nr=nr.reshape(n,3)
    x,y,z=co[:,0],co[:,1],co[:,2]
    d=amt*(np.sin(x*freq+ph[0])*np.sin(y*freq*1.3+ph[1])+.6*np.sin(z*freq*.8+ph[2])*np.sin((x+y)*freq*2.1+ph[3]))
    d[nr[:,2]<-.85]=0   # bed faces stay flat so stones sit on the ground / on each other
    out=co+nr*d[:,None];out[:,2]=np.maximum(out[:,2],z.min())
    me.vertices.foreach_set('co',out.ravel());me.update()
def box(name,size,center,mat,grp,bev=.01,segs=2,scale=.4,cuts=0,jit=0,seed=1,rot=None):
    o=finish(name,box_bm(size),mat,grp,scale)
    if cuts:subdiv(o,cuts)
    if bev:bevel(o,bev,segs)
    if jit:jitter(o,jit,seed,freq=4/max(size))
    if rot:o.data.transform(rot)
    o.data.transform(Matrix.Translation(center));return o
def beam(name,a,b,w,h,mat,grp,bev=.008,up=(0,0,1),scale=.5):
    """rectangular member from a to b (w across, h along `up`)"""
    a,b=Vector(a),Vector(b);t=(b-a);L=t.length;t.normalize();up=Vector(up);s=t.cross(up).normalized();u=t.cross(s)   # (t,s,u) right-handed: s.cross(t) mirrored the box inside out
    o=finish(name,box_bm((L,w,h)),mat,grp,scale);bevel(o,bev,2)
    o.data.transform(Matrix(((t.x,s.x,u.x,0),(t.y,s.y,u.y,0),(t.z,s.z,u.z,0),(0,0,0,1))));o.data.transform(Matrix.Translation((a+b)/2));return o
def solid_prism(bm,pts,vec):
    """closed prism: polygon pts (3D) swept by vec — both caps and the side walls"""
    a=[bm.verts.new(p) for p in pts];b=[bm.verts.new(Vector(p)+Vector(vec)) for p in pts];n=len(pts)
    bm.faces.new(a);bm.faces.new(list(reversed(b)))
    for i in range(n):j=(i+1)%n;bm.faces.new((a[j],a[i],b[i],b[j]))
    return bm
def prism(name,poly,depth,mat,grp,bev=.004,scale=.4):
    """2D polygon in XZ (front view) extruded along Y (depth, centred on y=0)"""
    bm=solid_prism(bmesh.new(),[(x,-depth/2,z) for x,z in poly],(0,depth,0));o=finish(name,bm,mat,grp,scale)
    if bev:bevel(o,bev,1,30)
    return o
def carve(o,cutters):
    for c in cutters:
        m=o.modifiers.new('carve','BOOLEAN');m.operation='DIFFERENCE';m.object=c;m.solver='EXACT';apply(o,m);bpy.data.objects.remove(c)
    assert len(o.data.polygons)>0,f'{o.name}: boolean emptied the mesh'
def cutter(bm,name='cut'):
    me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free();o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o);o.hide_render=True;return o
def leaf(name,base,direction,normal,L,W,mat,grp,curl=.25,seg=5):
    """lens-shaped leaf with a slight fold along the midrib"""
    d=Vector(direction).normalized();n=Vector(normal);s=d.cross(n).normalized();n=s.cross(d);bm=bmesh.new();mid=[];left=[];right=[]
    for i in range(seg+1):
        t=i/seg;w=W*math.sin(math.pi*t)**.8/2;c=Vector(base)+d*L*t-n*curl*L*t*t
        mid.append(bm.verts.new(c+n*w*.25))
        if 0<i<seg:left.append(bm.verts.new(c-s*w));right.append(bm.verts.new(c+s*w))
    for i in range(seg):
        if i==0:bm.faces.new((mid[0],left[0],mid[1]));bm.faces.new((mid[0],mid[1],right[0]))
        elif i==seg-1:bm.faces.new((mid[i],left[i-1],mid[i+1]));bm.faces.new((mid[i],mid[i+1],right[i-1]))
        else:bm.faces.new((mid[i],left[i-1],left[i],mid[i+1]));bm.faces.new((mid[i],mid[i+1],right[i],right[i-1]))
    for f in bm.faces:f.smooth=True
    return finish(name,bm,mat,grp,.05)
def join(objs,name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0];bpy.ops.object.join();o=bpy.context.object;o.name=name;return o

def hip_surface(name,hw,hd,ze,zr,p,U,mat,grp,step=.03,thick=.06,bump=None,xs=None,region=None):
    """concave hip roof z = ze + (zr-ze)·(d/dmax)^p with upturned corners.
    region=(x0,x1,y0,y1) limits the grid; gable=True variant handled by caller through `zf`."""
    dmax=min(hw,hd)
    def lift(x,y):
        sx=max(0,(abs(x)/hw-.58)/.42);sy=max(0,(abs(y)/hd-.58)/.42);return U*(sx*sy)**1.1
    def zf(x,y,d):return ze+(zr-ze)*(max(0,d)/dmax)**p+lift(x,y)
    x0,x1,y0,y1=region or (-hw,hw,-hd,hd);nx=max(2,int((x1-x0)/step));ny=max(2,int((y1-y0)/step))
    bm=bmesh.new();V=[]
    for j in range(ny+1):
        row=[]
        for i in range(nx+1):
            x=x0+(x1-x0)*i/nx;y=y0+(y1-y0)*j/ny;dx=hw-abs(x);dy=hd-abs(y);d=min(dx,dy);z=zf(x,y,xs(x,y) if xs else d)
            if bump:z+=bump(x,y,dx,dy)
            row.append(bm.verts.new((x,y,z)))
        V.append(row)
    for j in range(ny):
        for i in range(nx):bm.faces.new((V[j][i],V[j][i+1],V[j+1][i+1],V[j+1][i]))
    for f in bm.faces:f.smooth=True
    o=finish(name,bm,mat,grp,.5)
    m=o.modifiers.new('s','SOLIDIFY');m.thickness=thick;m.offset=-1;m.use_even_offset=True;apply(o,m)
    return o,zf

# ---------------- items ----------------

from mathutils import noise as mnoise
def unfold(bm,ref,iters=40):
    """the flat top/bottom squash, chip cuts and crack grooves can turn small facets over (pleats that lie coplanar on the top or
    bed). Facets whose normal no longer faces their original outward direction get their vertices relaxed until none are left."""
    for it in range(iters):
        bad=set()
        for f,r in zip(bm.faces,ref):
            f.normal_update()
            if f.normal.dot(r)<.2 or f.calc_area()<1e-12:bad.update(f.verts)
        if not bad:return 0
        bmesh.ops.smooth_vert(bm,verts=list(bad),factor=.5,use_axis_x=True,use_axis_y=True,use_axis_z=True)
    return len(bad)

def rock(name,dims,center,mat,grp,seed=1,sub=4,rough=.18,flat_top=None,flat_bottom=True,chips=0,split=None,squash=1.0,rot=0,boxy=2.4,cracks=0,fractures=0):
    """water-worn rock: icosphere -> ellipsoid -> layered noise (big lumps, softer facets) -> optional flat walkable top, chipped
    edges (planar cuts) and a split face; bottom flattened so it sits"""
    rng=random.Random(seed);bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=sub,radius=1)
    bm.faces.ensure_lookup_table();ref=[f.calc_center_median().normalized() for f in bm.faces]   # outward direction of every facet
    bm.verts.ensure_lookup_table();dz={v:v.co.z for v in bm.verts}   # sphere direction height: tells top from side
    off=Vector((rng.uniform(-50,50),rng.uniform(-50,50),rng.uniform(-50,50)))
    for v in bm.verts:
        d=v.co.normalized();sq=Vector([math.copysign(abs(c)**(2/boxy),c) for c in d])   # superellipsoid: boxy>2 squares it up
        n=mnoise.noise(d*1.3+off)*.55+mnoise.noise(d*2.9+off*1.7)*.25+mnoise.noise(d*6.0+off*2.3)*.08
        f=mnoise.noise(d*2.0+off*.7);n+=.10*(round(f*3)/3-f)   # slight faceting: worn planes, not a blob
        v.co=Vector((sq.x*dims[0]/2,sq.y*dims[1]/2,sq.z*dims[2]/2*squash))*(1+rough*n)
    if flat_bottom:
        for v in bm.verts:v.co.z=max(v.co.z,-dims[2]/2*.82)
    if flat_top is not None:
        zt=dims[2]/2*flat_top
        for v in bm.verts:   # squash only what faces up: compressing the sides too pleats their rough shoulders into thin stacked layers
            w=min(1,max(0,(dz[v]-.35)/.3));w=w*w*(3-2*w)
            if v.co.z>zt:v.co.z-=(v.co.z-zt)*.88*w
    for k in range(chips):
        a=rng.uniform(0,math.tau);el=rng.uniform(.2,.8);nrm=Vector((math.cos(a)*math.cos(el),math.sin(a)*math.cos(el),math.sin(el)))
        lim=max(v.co.dot(nrm) for v in bm.verts)*rng.uniform(.80,.9)
        for v in bm.verts:
            dd=v.co.dot(nrm)
            if dd>lim:v.co-=nrm*(dd-lim)*.72
    for k in range(fractures):   # near-vertical broken faces round the sides
        a=rng.uniform(0,math.tau);nrm=Vector((math.cos(a),math.sin(a),rng.uniform(-.15,.25))).normalized()
        lim=max(v.co.dot(nrm) for v in bm.verts)*rng.uniform(.86,.94)
        for v in bm.verts:
            dd=v.co.dot(nrm)
            if dd>lim:v.co-=nrm*(dd-lim)*.85
    sc_=min(dims)
    for k in range(cracks):   # thin cracks: V grooves where a random plane meets the surface
        nrm=Vector((rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-.4,.4))).normalized();d0=rng.uniform(-.3,.3)*max(dims)/2
        w=.018*sc_/.4;depth=.014*sc_/.4
        for v in bm.verts:
            t=abs(v.co.dot(nrm)-d0+.004*mnoise.noise(v.co*9))
            if t<w:v.co-=v.co.normalized()*depth*(1-t/w)**1.5
    if split:
        nrm=Vector(split).normalized()
        for v in bm.verts:
            dd=v.co.dot(nrm)
            if dd>0:v.co-=nrm*dd*.94-nrm*.012*mnoise.noise(v.co*8)
    unfold(bm,ref)
    for v in bm.verts:v.co.rotate(Matrix.Rotation(rot,3,'Z'))
    o=finish(name,bm,mat,grp,.5);defold(o,6)
    for p_ in o.data.polygons:p_.use_smooth=True
    o.data.transform(Matrix.Translation(center));return o

def ferns(prefix,centres,M,grp,rng,fronds=(5,8),L=(.22,.38)):
    """small ferns: arching fronds"""
    for k,c in enumerate(centres):
        nf=rng.integers(*fronds);a0=rng.uniform(0,math.tau)
        for f in range(nf):
            a=a0+f*math.tau/nf+rng.uniform(-.25,.25)*math.tau/nf;ln=rng.uniform(*L);d=Vector((math.cos(a)*.75,math.sin(a)*.75,.62)).normalized()   # fronds fanned evenly: two at nearly the same angle lay on each other
            base=Vector(c)+Vector((math.cos(a),math.sin(a),0))*.012+Vector((0,0,.004*f))   # fronds start apart: sharing one base point they lay on each other
            leaf(f'{prefix}{k}_{f}',base,d,Vector((-math.sin(a),math.cos(a),0)),ln,ln*.36,M['herb_green' if f%2 else 'herb_sage'],grp,curl=.55,seg=6)

def tufts(prefix,centres,M,grp,rng,blades=(7,12),h=(.12,.24),spread=.06):
    """grass tufts: a few curved blades fanning out of each centre"""
    for k,c in enumerate(centres):
        n=rng.integers(*blades)
        for b in range(n):
            a=k*2.4+b*math.tau/n+(rng.uniform(0,math.tau)/math.tau-.5)*.5*math.tau/n;tilt=rng.uniform(.15,.55);L=rng.uniform(*h)   # fanned evenly: blades at nearly one angle lay on each other
            d=Vector((math.cos(a)*tilt,math.sin(a)*tilt,1)).normalized();base=Vector(c)+Vector((math.cos(a),math.sin(a),0))*rng.uniform(0,spread)
            leaf(f'{prefix}{k}_{b}',base,d,Vector((-math.sin(a),math.cos(a),0)),L,rng.uniform(.012,.02),M['herb_green' if b%3 else 'herb_olive'],grp,curl=rng.uniform(.15,.45),seg=4)

def sag(o,fn):
    """move vertices by fn(co) -> Vector offset"""
    for v in o.data.vertices:v.co+=fn(v.co)

def RK09(M):
    """觀景石凳 · one long rough granite slab worn into a shallow seat dip, on two rough tapered stone supports with shims; grass at the feet"""
    meta={'moss_low':.35,'soil':.10,'top':5,'res':{'Stone':2048,'Detail_Grass':512,'Detail_Pebbles':512},'moss':{'Stone':.30},'lichen':{'Stone':.9}}
    rng=np.random.default_rng(909)
    seat=rock('RK09_Seat',(1.95,.52,.19),(0,0,.495),M['granite'],'Stone',seed=91,sub=6,rough=.06,flat_top=.55,chips=4,boxy=9,cracks=4,fractures=3)
    # a seat worn smooth in the middle: up to 1.8 cm dip on the top face
    sag(seat,lambda c:Vector((0,0,-.035*max(0,1-(c.x/.8)**2)*(.2+.8*min(1,max(0,(c.z-.50)/.05))))))   # weight eases in over the top 5 cm (a step folded the rim)
    defold(seat,8)
    for sx,yaw,seed in ((-1,.05,92),(1,-.07,93)):
        s_=rock(f'RK09_Support{sx}',(.44,.48,.42),(sx*.64,0,.195),M['granite'],'Stone',seed=seed,sub=5,rough=.10,flat_top=.75,chips=5,rot=yaw,boxy=7,cracks=3,fractures=4)
        sag(s_,lambda c,sx=sx:Vector(((c.x-sx*.64)*-.26*max(0,c.z/.41),c.y*-.24*max(0,c.z/.41),0)))   # clearly wider at the foot
        rock(f'RK09_Shim{sx}',(.17,.11,.05),(sx*.52,.16*sx,.395),M['granite'],'Stone',seed=seed+5,sub=2,rough=.2)
    for k in range(14):
        sx=1 if k%2 else -1;sz=rng.uniform(.04,.11)
        rock(f'RK09_Pebble{k}',(sz,sz*.8,sz*.5),(sx*rng.uniform(.4,.9),rng.uniform(-.25,.25),.0),M['granite'],'Detail_Pebbles',seed=940+k,sub=2,rough=.25)
    tufts('RK09_Tuft',[(-.88,-.22,0),(-.86,.12,0),(-.42,.24,0),(-.45,-.25,0),(.40,-.25,0),(.44,.24,0),(.88,.20,0),(.86,-.18,0)],M,'Detail_Grass',rng,spread=.05,h=(.12,.26))
    meta['collision']=[{'type':'box','size':[1.98,.54,.59],'center':[0,0,.295]}]
    meta['walkable']={'seat_height_m':.55,'note':'sit point on the seat centre'}
    return meta

def WM08(variant):
    dims={'A':(1.0,.84,.40),'B':(.92,.74,.36),'C':(.96,.92,.38)}[variant];seed={'A':81,'B':82,'C':83}[variant]
    def build(M):
        """踏石 · water-worn creek stepping stone with a nearly flat walkable top, half sunk in the bed; wet dark lower half"""
        rng=np.random.default_rng(seed)
        meta={'moss_low':.0,'wet':dims[2]*.55,'worn_top':True,'res':{'Stone':2048,'Detail_Pebbles':256},'moss':{'Stone':.12},'lichen':{'Stone':.7}}
        rock(f'WM08{variant}_Stone',dims,(0,0,dims[2]/2*.82),M['granite'],'Stone',seed=seed,sub=6,rough=.10,flat_top=.62,chips=3,boxy=3.8,fractures=7,cracks=5)
        for k in range(7):   # pale creek pebbles half-buried round the foot: removable detail
            a=rng.uniform(0,math.tau);r=np.array(dims[:2])/2*rng.uniform(1.0,1.15);sz=rng.uniform(.05,.09)
            rock(f'WM08{variant}_Pebble{k}',(sz,sz*.8,sz*.4),(math.cos(a)*r[0],math.sin(a)*r[1],-.006),M['granite'],'Detail_Pebbles',seed=seed*10+k,sub=2,rough=.12,rot=a)
        top=dims[2]*(.82/2+.55/2)
        meta['collision']=[{'type':'cylinder','radius':round(min(dims[:2])/2*.95,3),'height':round(top,3),'center':[0,0,round(top/2,3)]}]
        meta['walkable']={'top_height_m':round(top,3),'note':'nearly flat top, sink ~0.12 m into the creek bed when placed'}
        return meta
    return build

def WM10(variant):
    spec={'A':((.46,.38,.30),101,dict(rough=.16,chips=1)),'B':((1.12,.90,.66),102,dict(rough=.18,chips=2)),
          'C':((2.8,2.0,1.36),103,dict(rough=.20,chips=3,split=(1,-.35,.15))),'D':((2.9,1.05,.62),104,dict(rough=.16,chips=2,flat_top=.7,squash=.95))}[variant]
    dims,seed,kw=spec
    def build(M):
        """溪石 · creek boulder (A small cobble, B medium, C large split boulder, D long low slab) half buried in gravel"""
        rng=np.random.default_rng(seed)
        meta={'moss_low':.0,'wet':dims[2]*.35,'res':{'Stone':2048 if dims[0]>1 else 1024,'Detail_Gravel':512,'Detail_Ferns':512},'moss':{'Stone':.55}}
        rock(f'WM10{variant}_Stone',dims,(0,0,dims[2]/2*.82),M['granite'],'Stone',seed=seed,sub=6,**kw)
        if variant in 'BCD':   # gravel the boulder is bedded in, and small ferns where it meets the bank
            n=int(8+dims[0]*6)
            for k in range(n):
                a=rng.uniform(0,math.tau);r=np.array(dims[:2])/2*rng.uniform(.95,1.15);sz=rng.uniform(.05,.14)
                rock(f'WM10{variant}_Gravel{k}',(sz,sz*.8,sz*.5),(math.cos(a)*r[0],math.sin(a)*r[1],sz*.18),M['granite'],'Detail_Gravel',seed=seed*20+k,sub=2,rough=.25,rot=a)
        if variant in 'CD':
            fc=[(dims[0]*.42,-dims[1]*.38,0),(-dims[0]*.45,dims[1]*.3,0),(dims[0]*.1,dims[1]*.47,0)]
            ferns(f'WM10{variant}_Fern',fc,M,'Detail_Ferns',rng)
        h=dims[2]*.82
        if variant=='A':meta['collision']=[{'type':'cylinder','radius':.19,'height':round(h,3),'center':[0,0,round(h/2,3)]}]
        else:meta['collision']=[{'type':'box','size':[round(dims[0]*.86,3),round(dims[1]*.82,3),round(h,3)],'center':[0,0,round(h/2,3)]}]
        meta['note']='bed it ~15 % of its height into the gravel when placed'
        return meta
    return build

def RK12(variant):
    seed={'A':121,'B':122,'C':123,'D':124}[variant];length={'A':2.0,'B':1.6,'C':1.8,'D':1.2}[variant]
    def build(M):
        """路緣碎石 · a loose low edge of half-buried fieldstones of mixed sizes along a dirt road, grass and weeds between"""
        rng=np.random.default_rng(seed)
        meta={'moss_low':.4,'soil':.08,'res':{'Stone':1024,'Detail_Grass':512},'moss':{'Stone':.35}}
        x=-length/2;k=0
        while x<length/2-.05:
            w=rng.uniform(.14,.38) if rng.random()>.25 else rng.uniform(.07,.12);h=min(.28,w*rng.uniform(.45,.75))
            y=rng.normal(0,.06)+(.05*math.sin(x*2.1+seed))
            rock(f'RK12{variant}_Stone{k}',(w,w*rng.uniform(.7,1.0),h),(x+w/2,y,h/2*.7),M['granite'],'Stone',seed=seed*30+k,sub=3,rough=.22,chips=1,rot=rng.uniform(0,math.tau))
            if rng.random()<.6:tufts(f'RK12{variant}_T{k}_',[(x+w+.02,y+rng.normal(0,.08),0)],M,'Detail_Grass',rng,blades=(5,9),h=(.10,.22),spread=.04)
            x+=w*rng.uniform(.7,1.05);k+=1
        meta['note']='roadside dressing, no collision; set along both edges of the dirt road'
        return meta
    return build


def shrine(M,P,k=1.0,steps=True,fresh=True,glow=True,base=True):
    """roadside earth-god shrine kit at scale k: plinth (+steps), stone niche (back slab, side posts, lintel), timber beam with
    bracket blocks, small hip roof of blue-grey roll tiles with upturned corners and a ridge with curled ends, faceless seated
    stone figure, bronze tripod burner. Returns key heights."""
    S,Rf,T='Stone','Roof','Timber';rnd=random.Random(int(k*1000))
    z0=0
    if base:
        PX,PY,PH=.92*k,.62*k,.46*k
        box(f'{P}_PlinthCore',(2*PX-.12*k,2*PY-.12*k,PH-.02*k),(0,.12*k,(PH-.02*k)/2),M['plinth'],S,bev=0)
        for course,(zc,hh) in enumerate(((0,.27*k),(.27*k,PH-.27*k))):   # dressed course stones round the edge
            for side in range(4):
                horiz=side%2==0;half=PX if horiz else PY;sgn=-1 if side<2 else 1;x=-half+(rnd.uniform(0,.2*k) if course else 0)
                while x<half-.02:
                    ln=min(rnd.uniform(.40,.62)*k,half-x);c=x+ln/2
                    cen=(c,.12*k+sgn*(PY-.1*k),zc+hh/2) if horiz else (sgn*(PX-.1*k),.12*k+c,zc+hh/2)
                    sz=(ln-.01,.2*k,hh-.008) if horiz else (.2*k,ln-.01,hh-.008)
                    box(f'{P}_Course{course}{side}{x:.2f}',sz,cen,M['plinth'],S,bev=.018*k,cuts=2,jit=.005*k,seed=rnd.randint(0,9999),scale=.7)
                    x+=ln
        if steps:
            for i,(h,dy) in enumerate(((PH*2/3,.26),(PH/3,.50))):
                box(f'{P}_Step{i}',(.95*k,.26*k,h-.01),(0,.12*k-PY-(dy-.13)*k,(h-.01)/2),M['plinth'],S,bev=.02*k,cuts=2,jit=.004*k,seed=50+i,scale=.7)
        z0=PH
    # niche body
    BW,BD,BH=1.30*k,.95*k,1.20*k;yb=.12*k
    def coursed(name,length,thick,height,origin,along,rows=4,avoid=()):
        # a wall laid in courses of dressed blocks; odd rows start with a short block so the joints are offset
        z=origin[2];h=height/rows
        for r in range(rows):
            x=-length/2;first=True
            while x<length/2-.01:
                ln=(rnd.uniform(.12,.2) if (r%2 and first) else rnd.uniform(.28,.48))*k;ln=min(ln,length/2-x)
                if any(abs(x+ln-a_)<.008 for a_ in avoid):ln+=.016   # no joint on a pillar face plane
                ln=min(ln,length/2-x);c=x+ln/2;first=False
                sz=(ln-.006,thick,h-.006) if along.x else (thick,ln-.006,h-.006)
                box(f'{name}{r}_{x:.2f}',sz,(origin[0]+along.x*c,origin[1]+along.y*c,z+h/2),M['granite'],S,bev=.014*k,cuts=1,jit=.004*k,seed=rnd.randint(0,9999),scale=.6)
                x+=ln
            z+=h
    coursed(f'{P}_Back',BW-.444*k,.20*k,BH,(0,yb+BD/2-.10*k,z0),Vector((1,0,0)),5)   # butts between the side walls (running into them overlapped their coplanar courses)
    for sx in (-1,1):
        coursed(f'{P}_Side{sx}',BD,.22*k,BH,(sx*(BW/2-.11*k),yb,z0),Vector((0,1,0)),5,avoid=(-BD/2+.16*k+.012,-BD/2+.19*k,-BD/2+.185*k))   # pillar shaft, base and capital back faces
    # shelf, sill, lintel and pillar bases meet the wall courses on shared planes: their beds/tops are moved 6-12 mm off those planes
    # (the sill bed sits 8 mm below the pillar-base bed: the two overlap in plan and must not share that plane either)
    # so the stone detail displacement (about +-4 mm) cannot leave coplanar overlapping faces
    box(f'{P}_Shelf',(BW-.40*k,BD-.25*k,.10*k),(0,yb+.05*k,z0+.05*k+.012),M['granite'],S,bev=.015*k,cuts=1,seed=64)
    box(f'{P}_Lintel',(BW+.20*k,.30*k,.22*k+.012),(0,yb-BD/2+.12*k,z0+BH-.11*k+.006),M['granite'],S,bev=.025*k,cuts=3,jit=.006*k,seed=65)
    box(f'{P}_Sill',(BW+.10*k,.34*k,.08*k+.020),(0,yb-BD/2+.12*k,z0+.04*k-.010),M['granite'],S,bev=.015*k,cuts=2,seed=66)
    zt=z0+BH
    for sx in (-1,1):   # dressed front pillars standing proud of the side walls, with a base block and a capital (the shaft is 12 mm
        # deeper than square so its back face cannot land on a side-wall joint plane)
        px_,py_=sx*(BW/2-.06*k),yb-BD/2+.06*k
        box(f'{P}_PillarBase{sx}',(.26*k,.26*k,.12*k+.012),(px_,py_,z0+.06*k-.006),M['granite'],S,bev=.02*k,cuts=2,jit=.004*k,seed=81+sx,scale=.6)
        box(f'{P}_Pillar{sx}',(.20*k,.20*k+.012,BH-.30*k),(px_,py_+.006,z0+.12*k+(BH-.30*k)/2),M['granite'],S,bev=.018*k,cuts=4,jit=.005*k,seed=83+sx,scale=.6)
        box(f'{P}_PillarCap{sx}',(.25*k,.25*k,.10*k),(px_,py_,zt-.13*k),M['granite'],S,bev=.02*k,cuts=2,jit=.004*k,seed=85+sx,scale=.6)
    beam(f'{P}_BeamF',(-BW/2-.18*k,yb-BD/2+.05*k,zt+.06*k),(BW/2+.18*k,yb-BD/2+.05*k,zt+.06*k),.12*k,.12*k,M['wood'],T)
    beam(f'{P}_BeamB',(-BW/2-.18*k,yb+BD/2-.05*k,zt+.06*k),(BW/2+.18*k,yb+BD/2-.05*k,zt+.06*k),.12*k,.12*k,M['wood'],T)
    for x in (-BW/2,0,BW/2):
        for y in (yb-BD/2+.05*k,yb+BD/2-.05*k):
            box(f'{P}_Dou{x:.2f}{y:.2f}',(.13*k,.13*k,.07*k),(x,y,zt+.155*k),M['wood'],T,bev=.008*k)
            box(f'{P}_Gong{x:.2f}{y:.2f}',(.30*k,.07*k,.05*k),(x,y,zt+.14*k),M['wood'],T,bev=.008*k)   # bracket arm across the block
            for gx in (-.12,.12):box(f'{P}_GongCap{x:.2f}{y:.2f}{gx}',(.07*k,.08*k,.05*k),(x+gx*k,y,zt+.185*k),M['wood'],T,bev=.006*k)
    box(f'{P}_WallPlate',(BW+.30*k,BD+.10*k,.10*k),(0,yb,zt+.22*k),M['oldwood'],T,bev=.012*k)
    for i,x in enumerate(np.linspace(-BW/2-.10*k,BW/2+.10*k,11)):   # rafter tails projecting under the front and back eaves
        for sy in (-1,1):beam(f'{P}_Rafter{i}{sy}',(x,yb+sy*(BD/2-.02*k),zt+.19*k),(x,yb+sy*(.66*k-.06*k),zt+.13*k),.045*k,.05*k,M['oldwood'],T)   # tails stay under the eave
    for i,y in enumerate(np.linspace(-BD/2+.05*k,BD/2-.05*k,7)):   # and under the side eaves
        for sx in (-1,1):beam(f'{P}_RafterS{i}{sx}',(sx*(BW/2+.12*k),yb+y,zt+.19*k),(sx*(1.15*k-.06*k),yb+y,zt+.13*k),.045*k,.05*k,M['oldwood'],T)
    # roof
    HW,HD,ZE,ZR=1.15*k,.66*k,zt+.22*k,zt+.66*k;PIT=.12*k
    def roll(c):
        t=(c/PIT)%1;return .03*k*math.sqrt(max(0,1-((t-.5)/.22)**2))+.006*k*math.cos(math.tau*t)
    def bump(x,y,dx,dy):
        e=min(dx,dy);return roll(x if dy<=dx else y)*min(1,e/(.03*k))
    o,zf=hip_surface(f'{P}_Roof',HW,HD,ZE,ZR,1.7,.30*k,M['tile'],Rf,step=.016*k,thick=.07*k,bump=bump)
    o.data.transform(Matrix.Translation((0,yb,0)))
    zr=ZR
    box(f'{P}_Ridge',(2*(HW-HD)+.30*k,.12*k,.11*k),(0,yb,zr+.04*k),M['tile'],Rf,bev=.015*k,cuts=2,scale=.4)
    for sx in (-1,1):
        x0=sx*(HW-HD+.16*k);curl=[(x0,yb,zr),(x0+sx*.05*k,yb,zr+.16*k),(x0+sx*.01*k,yb,zr+.24*k),(x0-sx*.06*k,yb,zr+.25*k),(x0-sx*.09*k,yb,zr+.20*k)]
        tube(f'{P}_RidgeEnd{sx}',curl,.05*k,M['tile'],Rf,10,.3,radii=[.07*k,.065*k,.05*k,.04*k,.03*k])
    # faceless seated stone figure on the shelf
    fz=z0+.10*k;fy=yb+.08*k
    rock(f'{P}_FigureLegs',(.40*k,.26*k,.13*k),(0,fy-.02*k,fz+.055*k),M['granite'],S,seed=71,sub=4,rough=.04,boxy=2.8)
    rock(f'{P}_FigureTorso',(.26*k,.18*k,.34*k),(0,fy+.02*k,fz+.24*k),M['granite'],S,seed=72,sub=4,rough=.04,boxy=2.6,flat_bottom=False)
    rock(f'{P}_FigureHands',(.13*k,.08*k,.06*k),(0,fy-.09*k,fz+.15*k),M['granite'],S,seed=73,sub=3,rough=.04,flat_bottom=False)
    rock(f'{P}_FigureHead',(.13*k,.12*k,.15*k),(0,fy+.01*k,fz+.47*k),M['granite'],S,seed=74,sub=4,rough=.03,flat_bottom=False)
    rock(f'{P}_FigureHood',(.16*k,.14*k,.08*k),(0,fy+.03*k,fz+.53*k),M['granite'],S,seed=75,sub=3,rough=.04,flat_bottom=False)
    # bronze tripod burner on the sill
    by=yb-BD/2+.12*k;bz=z0+.08*k
    lathe(f'{P}_Burner',[(0,0),(.07*k,.0),(.10*k,.04*k),(.11*k,.09*k),(.10*k,.12*k),(.115*k,.13*k),(.11*k,.14*k),(.09*k,.13*k),(.0,.11*k)],M['bronze'],'Bronze',seg=28,center=(0,by,bz+.04*k))
    for i in range(3):
        a=i*math.tau/3+math.pi/2
        tube(f'{P}_BurnerLeg{i}',[(.07*k*math.cos(a),by+.07*k*math.sin(a),bz+.05*k),(.085*k*math.cos(a),by+.085*k*math.sin(a),bz)],.012*k,M['bronze'],'Bronze',6,.2)
    for sx in (-1,1):
        tube(f'{P}_BurnerEar{sx}',[(sx*.10*k,by,bz+.17*k),(sx*.12*k,by,bz+.21*k),(sx*.09*k,by,bz+.22*k)],.009*k,M['bronze'],'Bronze',6,.2)
    if fresh:
        for i,(dx,colr) in enumerate(((-.30,'fruit_orange'),(.30,'fruit_red'))):
            lathe(f'{P}_Plate{i}',[(0,0),(.08*k,0),(.10*k,.02*k),(0,.02*k)],M['granite'],'Detail_Offerings',seg=20,center=(dx*k,by,bz))
            for j in range(3):
                a=j*math.tau/3
                lathe(f'{P}_Fruit{i}{j}',[(0,0),(.03*k,.008*k),(.038*k,.035*k),(.03*k,.06*k),(0,.068*k)],M[colr],'Detail_Offerings',seg=14,center=(dx*k+.032*k*math.cos(a),by+.032*k*math.sin(a),bz+.02*k))
    for i in range(5 if fresh else 3):   # incense sticks in the burner (old ones burnt short)
        a=i*math.tau/5;L=(.24 if fresh else .09)*k
        tube(f'{P}_Incense{i}',[(.025*k*math.cos(a),by+.025*k*math.sin(a),bz+.12*k),(.035*k*math.cos(a),by+.035*k*math.sin(a),bz+.12*k+L)],.004*k,M['incense'],'Detail_Incense',5,.1)
    if glow:   # oil-lamp dish beside the figure; the flame is the separate emissive mesh
        gx,gy,gz=.30*k,yb-.02*k,z0+.10*k
        lathe(f'{P}_LampDish',[(0,0),(.035*k,0),(.05*k,.02*k),(.045*k,.025*k),(0,.012*k)],M['clay'],'Bronze',seg=18,center=(gx,gy,gz))
        lathe(f'{P}_Flame',[(0,0),(.018*k,.009*k),(.024*k,.038*k),(.014*k,.075*k),(0,.105*k)],M['flame'],'Glow',seg=12,center=(gx,gy,gz+.011*k))   # base 1 mm into the oil at the dish centre (z .012): it hovered 6 mm
    return {'z0':z0,'zt':zt,'zr':zr,'yb':yb,'BW':BW,'BD':BD}

def RK06(M):
    """土地祠 · well-kept roadside earth-god shrine on a coursed plinth with two steps, stone niche, small tiled hip roof with
    upturned corners, faceless figure, bronze burner, fresh fruit and incense, a little oil lamp glowing in the niche"""
    meta={'moss_low':.35,'soil':.05,'res':{'Stone':2048,'Roof':1024,'Timber':512,'Bronze':512,'Glow':256,'Detail_Offerings':512,'Detail_Incense':256,'Detail_Grass':512},
          'moss':{'Stone':.22,'Roof':.25},'lichen':{'Stone':.3}}
    shrine(M,'RK06',1.0)
    rng=np.random.default_rng(606)
    tufts('RK06_Tuft',[(-.9,.7,0),(.92,.6,0),(-.95,-.3,0),(.9,-.5,0),(.55,-.82,0)],M,'Detail_Grass',rng,spread=.03,h=(.10,.2))
    meta['collision']=[{'type':'box','size':[1.84,1.24,.46],'center':[0,.12,.23]},{'type':'box','size':[.95,.50,.31],'center':[0,-.75,.155]},   # plinth and the two steps as built
                       {'type':'box','size':[1.3,.95,1.2],'center':[0,.12,1.1]}]
    meta['note']='Glow group = the oil-lamp flame in the niche; drive its emission strength 0..1 (0 = unlit, paper-yellow)'
    return meta

def SC01(M):
    """倒下的土地公小廟 · a small shrine toppled onto its side, half sunk in a soil mound: tilted niche with its tiled cap, the worn
    faceless figure still inside, cracked and missing tiles scattered, burnt-down incense, a small fresh offering of wild fruit"""
    meta={'moss_low':.6,'soil':.25,'res':{'Stone':2048,'Roof':1024,'Timber':512,'Bronze':512,'Detail_Offerings':256,'Detail_Incense':256,'Detail_Tiles':512,'Detail_Ferns':512},
          'moss':{'Stone':.75,'Roof':.6,'Timber':.2},'lichen':{'Stone':.8}}
    start=len(parts);k=.56
    shrine(M,'SC01',k,steps=False,fresh=False,glow=False,base=False)
    tilt=Matrix.Rotation(math.radians(-21),4,'Y')@Matrix.Rotation(math.radians(6),4,'X')
    for o in parts[start:]:o.data.transform(Matrix.Translation((.05,0,.0))@tilt)
    rng=np.random.default_rng(101)
    rock('SC01_Mound',(.92,.92,.56),(-.36,.05,.0),M['soil'],'Stone',seed=11,sub=4,rough=.28,boxy=2.0)
    rock('SC01_Mound2',(.5,.6,.30),(.30,.25,.0),M['soil'],'Stone',seed=12,sub=3,rough=.3,boxy=2.0)
    for i in range(6):   # stones bedded in the mound
        a=i*math.tau/6;sz=rng.uniform(.12,.22)
        rock(f'SC01_Bedded{i}',(sz,sz*.85,sz*.7),(-.36+math.cos(a)*.36,.05+math.sin(a)*.34,.12+.08*rng.random()),M['granite'],'Stone',seed=140+i,sub=2,rough=.25)
    for i in range(7):
        sz=rng.uniform(.10,.22);rock(f'SC01_Rubble{i}',(sz,sz*.8,sz*.6),(rng.uniform(-.6,.55),rng.uniform(-.48,.48),.04),M['granite'],'Stone',seed=120+i,sub=2,rough=.25)
    for i in range(6):   # fallen roof tiles
        a=rng.uniform(0,math.tau);r=rng.uniform(.45,.75)
        box(f'SC01_Tile{i}',(.13,.07,.012),(math.cos(a)*r,math.sin(a)*r,.02),M['tile'],'Detail_Tiles',bev=.004,cuts=1,rot=Matrix.Rotation(a,4,'Z')@Matrix.Rotation(rng.uniform(-.4,.4),4,'X'))
    for j in range(3):   # a small fresh offering of wild fruit, set by someone who still visits
        a=j*math.tau/3
        lathe(f'SC01_WildFruit{j}',[(0,0),(.025,.006),(.032,.03),(.025,.05),(0,.056)],M['fruit_red'],'Detail_Offerings',seg=14,center=(.25+.04*math.cos(a),-.55+.04*math.sin(a),.0))
    ferns('SC01_Fern',[(-.62,.35,.05),(.45,.42,0),(-.4,-.48,.05),(-.7,-.15,0),(.05,.5,.1),(.5,-.35,0)],M,'Detail_Ferns',rng,L=(.18,.32))
    tufts('SC01_Tuft',[(-.15,-.5,0),(.62,.1,0),(-.65,.55,0),(.2,.45,.05)],M,'Detail_Ferns',rng,spread=.04,h=(.10,.2))
    meta['collision']=[{'type':'box','size':[1.3,1.1,.75],'center':[-.1,0,.37]}]
    return meta


def arrow_board(name,x0,x1,z,h,thick,mat,grp,point=1,y=0.0,seed=1):
    """blank arrow board in the XZ plane, made of two weathered planks with a thin gap: the square end is at the tail, the point at
    the head (point=+1 points to +x, -1 to -x). Returns the upper plank."""
    tip=.16*h/.2;g=.004;L,Rr=min(x0,x1),max(x0,x1);out=None
    for half,(za,zb) in enumerate(((z-h/2,z-g),(z+g,z+h/2))):
        w=lambda zz:tip*abs(zz-z)/(h/2)   # inset of the point's slanted edge at height zz
        if point>0:poly=[(L,za),(Rr-w(za),za),(Rr-w(zb),zb),(L,zb)]
        else:poly=[(L+w(za),za),(Rr,za),(Rr,zb),(L+w(zb),zb)]
        if half==0:poly=poly[::1]
        o=prism(f'{name}P{half}',poly,thick,M_['oldwood'],grp,bev=.005,scale=.35)
        jitter(o,.004,seed*3+half,freq=10)
        o.data.transform(Matrix.Translation((0,y,0)));out=o
    return out

def RK01(variant):
    def build(M):
        """路牌 · weathered cedar post with blank arrow boards (A: two boards pointing different ways; B: one long board on a strut),
        hemp lashings, iron nail heads, a small stone pile at the foot, moss on the shaded side. Boards are blank: text is overlaid in game."""
        global M_;M_=M
        rng=np.random.default_rng(11 if variant=='A' else 12)
        meta={'moss_low':.5,'soil':.08,'res':{'Wood':1024,'Stone':1024,'Detail_Vine':256,'Detail_Stones':512},'moss':{'Wood':.25,'Stone':.12},'lichen':{'Wood':.45,'Stone':.35}}
        H=2.45 if variant=='A' else 2.25;lean=0 if variant=='A' else .03
        top=Vector((lean,0,H))
        tube(f'RK01{variant}_Post',[(0,0,0),(lean*.5,0,H*.5),top],.10,M['oldwood'],'Wood',16,.4,radii=[.115,.105,.095])
        cap=lathe(f'RK01{variant}_PostTop',[(0,0),(.096,0),(.092,.05),(.07,.06),(.075,.10),(.04,.085),(.03,.12),(0,.09)],M['oldwood'],'Wood',seg=7,center=tuple(top))
        jitter(cap,.012,77,freq=14)
        boards=[(2.06,-1,(-.57,.42)),(1.72,1,(-.40,.57))] if variant=='A' else [(1.90,1,(-.34,.57))]
        for i,(z,pt,ln) in enumerate(boards):
            yb=-.13;x0,x1=ln
            arrow_board(f'RK01{variant}_Board{i}',x0,x1,z,.27 if variant=='A' else .30,.045,M,'Wood',point=pt,y=yb,seed=20+i)
            for nx in (-.07,.07):   # nail heads into the post
                n_=lathe(f'RK01{variant}_Nail{i}{nx}',[(0,0),(.009,0),(.008,.006),(0,.007)],M['iron'],'Wood',seg=8)
                n_.data.transform(Matrix.Translation((nx,yb-.023,z))@Matrix.Rotation(math.radians(90),4,'X'))   # head faces the front (-Y)
            lashing(f'RK01{variant}_Lash{i}',(0,0,z+.17),(0,0,1),.108,4,M['hemp'],'Wood',cord=.011)
        # diagonal strut under the lowest board
        zl=boards[-1][0];pt=boards[-1][1]
        beam(f'RK01{variant}_Strut',(pt*.06,-.09,zl-.48),(pt*.36,-.11,zl-.14),.05,.045,M['oldwood'],'Wood',up=(0,1,0))
        lashing(f'RK01{variant}_LashLow',(0,0,zl-.46),(0,0,1),.11,3,M['hemp'],'Wood',cord=.011)
        # stone pile at the foot
        n=9 if variant=='A' else 7
        for k in range(n):
            a=k*math.tau/n+rng.uniform(-.3,.3);r=rng.uniform(.16,.27);sz=rng.uniform(.15,.25)   # kept within the 0.4 m depth of the limit
            rock(f'RK01{variant}_Pile{k}',(sz,sz*.6,sz*.72),(math.cos(a)*r,math.sin(a)*r*.28,.0),M['granite'],'Stone',seed=300+k+(50 if variant=='B' else 0),sub=4,rough=.12,rot=rng.uniform(-.3,.3),boxy=3.4,chips=2,fractures=4)
        for k in range(3):   # a second layer leaning on the post
            a=k*math.tau/3+.5;sz=rng.uniform(.15,.21)
            rock(f'RK01{variant}_PileTop{k}',(sz,sz*.6,sz*.7),(math.cos(a)*.15,math.sin(a)*.06,.12),M['granite'],'Stone',seed=330+k+(50 if variant=='B' else 0),sub=4,rough=.12,rot=rng.uniform(-.3,.3),boxy=3.4,fractures=3)
        for k in range(5):
            a=rng.uniform(0,math.tau);r=rng.uniform(.25,.38);sz=rng.uniform(.04,.08)
            rock(f'RK01{variant}_Pebble{k}',(sz,sz*.8,sz*.5),(math.cos(a)*r,math.sin(a)*r*.35,0),M['granite'],'Detail_Stones',seed=360+k,sub=2,rough=.3)
        for k in range(9):   # small creeper on the shaded (back) side of the post
            z=.15+k*.11;a=math.pi/2+math.sin(k*1.3)*.6
            # vine leaf base follows the leaning post and sits just inside its bark
            leaf(f'RK01{variant}_Vine{k}',(lean*z/H+math.cos(a)*.10,math.sin(a)*.10,z),(math.cos(a)*.6,math.sin(a)*.6,.5),(-math.sin(a),math.cos(a),0),.06,.04,M['herb_green'],'Detail_Vine',curl=.3,seg=4)
        meta['collision']=[{'type':'cylinder','radius':.12,'height':H,'center':[0,0,H/2]}]
        meta['note']='arrow boards are blank; overlay the place names in game. A2_RoadSign uses A, A3_WestSign uses B'
        return meta
    return build

def straw_mat(M):
    return M['straw']

def straw_shell(name,r_top,z_top,r_bot,z_bot,mat,grp,rng,teeth=240,tooth=(.03,.12),flare=.04,seg_v=3,twist=0.0):
    """one shingle of thatch: a cone shell from (r_top,z_top) down to (r_bot,z_bot) whose hem is cut into fine comb teeth that flare
    outward, so the edge reads as individual straw ends. One UV island (cylindrical), so it bakes cleanly."""
    bm=bmesh.new();n=teeth*2;rows=[]
    for j in range(seg_v+1):
        t=j/seg_v;rows.append([bm.verts.new(((r_top+(r_bot-r_top)*t)*math.cos(math.tau*i/n+twist*t),(r_top+(r_bot-r_top)*t)*math.sin(math.tau*i/n+twist*t),
                                              z_top+(z_bot-z_top)*t+.006*math.sin(math.tau*13*i/n+j*1.7))) for i in range(n)])   # smooth waviness: a per-vertex zigzag
        # 1.7 mm apart at the top ring folded the solidified back shell onto itself
    for j in range(seg_v):
        for i in range(n):k=(i+1)%n;bm.faces.new((rows[j][i],rows[j][k],rows[j+1][k],rows[j+1][i]))
    last=rows[-1]
    for i in range(0,n,2):   # one tooth per pair of hem vertices: a thin straw tip hanging below and flaring out
        k=(i+2)%n;mid=(i+1)%n;L=rng.uniform(*tooth);a=math.tau*(i+1)/n+twist
        rr=r_bot+flare*L/tooth[1]*rng.uniform(.5,1.2);tip=bm.verts.new((rr*math.cos(a+rng.uniform(-.01,.01)),rr*math.sin(a+rng.uniform(-.01,.01)),z_bot-L))
        bm.faces.new((last[i],last[mid],tip));bm.faces.new((last[mid],last[k],tip))
    for f in bm.faces:f.smooth=True
    o=finish(name,bm,mat,grp,.4,uv=cyl_uv(1));o['uvkeep']=1;solidify_uv(o,.008,-1,.4);return o

def straw_fringe(name,x0,x1,y,z,sy,mat,grp,rng,hang=.08,teeth=180,tooth=(.04,.14),out=.04,droop=-.3):
    """a straight band of straw along x at (y, z) hanging outward (sy = ±1 toward ±y), its lower edge cut into fine comb teeth"""
    bm=bmesh.new();n=teeth*2;top=[];bot=[]
    for i in range(n+1):
        x=x0+(x1-x0)*i/n;top.append(bm.verts.new((x,y,z)));bot.append(bm.verts.new((x,y+sy*out,z-hang+.006*math.sin(i*1.3))))
    for i in range(n):bm.faces.new((top[i],top[i+1],bot[i+1],bot[i]))
    for i in range(0,n,2):
        L=rng.uniform(*tooth);m=bot[i+1].co;tip=bm.verts.new((m.x+rng.uniform(-.006,.006),m.y+sy*L*(1+droop)*.5,m.z-L))
        bm.faces.new((bot[i],bot[i+1],tip));bm.faces.new((bot[i+1],bot[i+2],tip))
    for f in bm.faces:f.smooth=True
    o=finish(name,bm,mat,grp,.4,uv=(lambda p:p.x,lambda p:p.z));o['uvkeep']=1;solidify_uv(o,.008,0,.4);return o

def straw_rope(name,rr,z,mat,grp,rng,knots=4,wave=.015):
    """two-ply twisted straw rope round the stack, with knots and short hanging tassels"""
    for ply in (0,1):
        pts=[]
        for a in np.linspace(0,math.tau,181):
            ph=a*38+ply*math.pi;r_=rr+.011*math.cos(ph);pts.append((r_*math.cos(a),r_*math.sin(a),z+.011*math.sin(ph)+wave*math.sin(a*3)))
        tube(f'{name}Ply{ply}',pts,.013,mat,grp,8,.2,caps=False)
    for k in range(knots):
        a=k*math.tau/knots+rng.uniform(-.3,.3);c=Vector(((rr+.012)*math.cos(a),(rr+.012)*math.sin(a),z+wave*math.sin(a*3)))
        rock(f'{name}Knot{k}',(.05,.045,.045),tuple(c),mat,grp,seed=900+k,sub=2,rough=.15,flat_bottom=False)
        for t in range(6):   # tassel of loose ends hanging from the knot
            d=Vector((math.cos(a)*.15+rng.uniform(-.08,.08),math.sin(a)*.15+rng.uniform(-.08,.08),-1))
            b_=a+(t-2.5)*.4   # each end turned on its own: six from one point with one normal lay on each other
            leaf(f'{name}Tassel{k}{t}',c+Vector((math.cos(t*1.05)*.004,math.sin(t*1.05)*.004,-.01)),d,(-math.sin(b_),math.cos(b_),0),rng.uniform(.12,.24),.014,mat,grp,curl=.05,seg=3)

def RK10(variant):
    def build(M):
        """草垛 · round rice-straw stack around a central pole, built up of overlapping straw shingles whose ends hang in fine fringes,
        an overhanging straw cap with a shaggy eave, a tied top knot, two-ply straw ropes with knots and tassels, a pulled-out side,
        scattered straw at the foot (A: neat banded stack; B: shaggy, slumped, more layers, minTier high)"""
        rng=np.random.default_rng(101 if variant=='A' else 102)
        meta={'moss_low':.0,'soil':.06,'res':{'Straw':4096,'Cap':2048,'Wood':512,'Rope':1024,'Detail_Straw':512},'moss':{}}
        R=1.0 if variant=='A' else 1.08;Hb=1.55 if variant=='A' else 1.45
        if variant=='A':
            prof=[(R*.90,0),(R*.98,.25),(R*1.02,.7),(R*.98,1.15),(R*.88,Hb),(R*.55,Hb+.25),(R*.22,Hb+.45),(0,Hb+.52)]
        else:
            prof=[(R*1.02,0),(R*1.06,.18),(R*.98,.6),(R*.85,1.0),(R*.62,Hb),(R*.32,Hb+.32),(0,Hb+.42)]
        rz=lambda z:float(np.interp(z,[p[1] for p in prof],[p[0] for p in prof]))
        lathe(f'RK10{variant}_Body',prof,M['straw'],'Straw',seg=72,cyl=True)
        # shingles from the bottom up, each one overlapping the one below
        step=.13 if variant=='A' else .11;z=.30;i=0
        while z<Hb-.05:
            hang=step*1.6;rt=rz(z)+.004;rb=rz(z-hang)+.03+.006*i%2
            straw_shell(f'RK10{variant}_Shingle{i}',rt,z,rb,z-hang,M['straw'],'Straw',rng,teeth=260,tooth=(.03,.10) if variant=='A' else (.04,.16),
                        flare=.03 if variant=='A' else .06,twist=rng.uniform(-.05,.05))
            z+=step;i+=1
        straw_shell(f'RK10{variant}_Foot',rz(.12)+.01,.12,rz(.0)+.06,.0,M['straw'],'Straw',rng,teeth=260,tooth=(.0,.03),flare=.08)
        # overhanging cap: two shaggy layers from the top knot out past the shoulder
        zc=prof[-1][1]
        for k,(rt,zt,rb,zb,tl) in enumerate(((.16,zc+.02,rz(Hb-.1)+.22,Hb-.15,(.10,.24)),(.14,zc+.06,rz(Hb+.05)+.12,Hb+.02,(.06,.16)))):
            straw_shell(f'RK10{variant}_Cap{k}',rt,zt,rb,zb,M['straw'],'Cap',rng,teeth=300,tooth=tl,flare=.10,seg_v=5,twist=.08*(k+1))
        lathe(f'RK10{variant}_TopKnot',[(0,zc-.02),(.13,zc),(.15,zc+.08),(.10,zc+.17),(.05,zc+.20),(0,zc+.21)],M['straw'],'Cap',seg=28)
        for t in range(18):   # splayed straw ends above the tie
            a=t*math.tau/18+rng.uniform(-.1,.1)
            leaf(f'RK10{variant}_KnotEnd{t}',(.08*math.cos(a),.08*math.sin(a),zc+.17),(math.cos(a)*.7,math.sin(a)*.7,.6),(-math.sin(a),math.cos(a),0),rng.uniform(.09,.16),.02,M['straw'],'Cap',curl=-.3,seg=3)
        for zz in (zc+.04,zc+.12):lashing(f'RK10{variant}_CapTie{zz:.2f}',(0,0,zz),(0,0,1),.145,2,M['hemp'],'Rope',cord=.012)
        tube(f'RK10{variant}_Pole',[(0,0,zc-.4),(0,0,zc+.50)],.045,M['oldwood'],'Wood',12,.3,radii=[.05,.04])
        # ropes: A has two neat bands, B one slack band
        for k,zb in enumerate((.32,1.02) if variant=='A' else (.62,)):
            straw_rope(f'RK10{variant}_Rope{k}',rz(zb)+.045,zb,M['hemp'],'Rope',rng,knots=4 if variant=='A' else 3,wave=.015 if variant=='A' else .05)
        # a bundle pulled out of one side
        a0=-.6;n=9 if variant=='A' else 16
        for k in range(n):
            a=a0+k*.05;base=Vector((rz(.9)*math.cos(a),rz(.9)*math.sin(a),.9+.03*k))
            leaf(f'RK10{variant}_Pulled{k}',base,(math.cos(a)*.8,math.sin(a)*.8,-.6),(-math.sin(a),math.cos(a),0),rng.uniform(.35,.55),.03,M['straw'],'Straw',curl=.2,seg=4)
        # scattered straw and two dropped sheaves on the ground (removable)
        for k in range(90):
            a=rng.uniform(0,math.tau);r=rng.uniform(R*.92,R*1.3);d=rng.uniform(0,math.tau)
            leaf(f'RK10{variant}_Loose{k}',(r*math.cos(a),r*math.sin(a),.004+.0015*(k%8)),(math.cos(d),math.sin(d),.03),(0,0,1),rng.uniform(.10,.30),.010,M['straw'],'Detail_Straw',curl=.0,seg=3)
        for k,a in enumerate((2.2,4.1)):
            c=Vector(((R+.25)*math.cos(a),(R+.25)*math.sin(a),.048))   # tie (r .046) rests on the ground
            for t in range(10):
                d=Vector((math.cos(a+1.57),math.sin(a+1.57),0))*(1 if t%2 else -1)+Vector((rng.uniform(-.2,.2),rng.uniform(-.2,.2),.02))
                ph=t*math.tau/10;rad=Vector((math.cos(a),math.sin(a),0))*math.cos(ph)+Vector((0,0,1))*math.sin(ph)   # straws round the inside of the tie,
                # each facing out (ten flat ones at the centre lay on each other and touched nothing)
                sh_=leaf(f'RK10{variant}_Sheaf{k}{t}',tuple(c+rad*.043),d,tuple(rad),rng.uniform(.18,.26),.02,M['straw'],'Detail_Straw',curl=.02,seg=3);sh_['nosettle']=1
            lashing(f'RK10{variant}_SheafTie{k}',tuple(c),(math.cos(a+1.57),math.sin(a+1.57),0),.04,2,M['hemp'],'Detail_Straw',cord=.006)
        meta['collision']=[{'type':'cylinder','radius':round(R*1.03,3),'height':round(Hb+.5,3),'center':[0,0,round((Hb+.5)/2,3)]}]
        return meta
    return build

def chip(o,n,seed,depth=(.86,.94),side_bias=.0):
    """planar breaks on an existing mesh: n random planes shave off whatever sticks out past them (rough-hewn, broken faces)"""
    rng=random.Random(seed);V=o.data.vertices;c=sum((v.co for v in V),Vector())/len(V)
    for k in range(n):
        a=rng.uniform(0,math.tau);el=rng.uniform(-.9,.9)*(1-side_bias);nrm=Vector((math.cos(a)*math.cos(el),math.sin(a)*math.cos(el),math.sin(el)))
        lim=max((v.co-c).dot(nrm) for v in V)*rng.uniform(*depth)
        for v in V:
            dd=(v.co-c).dot(nrm)
            if dd>lim:v.co-=nrm*(dd-lim)*.9

def TY06(M):
    """練功器材 · a squat stone lock with a wooden grip set into it, and a stone barbell (two round stones on a thick ash bar),
    grips polished by hands, chipped edges, moss at the base; two separate pieces"""
    meta={'moss_low':.5,'soil':.06,'res':{'Lock':2048,'Barbell':2048,'Bar':1024,'Detail_Grass':1024},'moss':{'Lock':.35,'Barbell':.3,'Bar':0},'lichen':{'Lock':.6,'Barbell':.6},'pieces':{}}
    # stone lock: a squat block with a carved arch handle on top
    lx,ly=-.45,.12
    blk=rock('TY06_LockBlock',(.36,.24,.25),(lx,ly,.12*.82),M['granite'],'Lock',seed=61,sub=5,rough=.07,flat_top=.8,chips=5,boxy=4.5)
    sag(blk,lambda c:Vector(((c.x-lx)*-.30*max(0,c.z/.25),(c.y-ly)*-.30*max(0,c.z/.25),0)))   # squat, wider at the foot
    pts=[(lx-.115+.23*t,ly,.17+.15*math.sin(math.pi*t)**.7) for t in np.linspace(0,1,17)]
    tube('TY06_LockHandle',pts,.036,M['oldwood'],'Bar',12,.3,radii=[.042]+[.036]*15+[.042])   # hand-polished wooden grip set into the stone
    meta['pieces']['Lock']={'centre':[lx,ly],'collision':{'type':'box','size':[.34,.22,.33]}}
    # barbell: bar resting on two stone wheels
    bx,by=.15,-.12;L=1.18;rw=.19
    for sx in (-1,1):
        cx=bx+sx*(L/2-.08)
        w_=lathe(f'TY06_Wheel{sx}',[(0,-.08),(.06,-.08),(.12,-.08),(.17,-.078),(.19,-.06),(.196,-.02),(.196,.02),(.19,.06),(.17,.078),(.12,.08),(.06,.08),(0,.08)],M['granite'],'Barbell',seg=64)
        chip(w_,9,62+sx,depth=(.88,.95));jitter(w_,.006,62+sx,freq=7)   # rough-hewn disc with broken facets round the rim
        w_.data.transform(Matrix.Rotation(math.radians(90),4,'Y'));w_.data.transform(Matrix.Translation((cx,by,rw)))
        lathe(f'TY06_Collar{sx}',[(0,-.03),(.045,-.03),(.05,0),(.045,.03),(0,.03)],M['oldwood'],'Bar',seg=16)
        parts[-1].data.transform(Matrix.Rotation(math.radians(90),4,'Y'));parts[-1].data.transform(Matrix.Translation((cx-sx*.1,by,rw)))
        lashing(f'TY06_Wrap{sx}',(bx+sx*.18,by,rw),(1,0,0),.032,4,M['hemp'],'Bar',cord=.008)
    tube('TY06_Bar',[(bx-L/2+.015,by,rw),(bx+L/2-.015,by,rw)],.032,M['wood'],'Bar',16,.3)   # ends stop inside the wheels (flush caps z-fought the wheel faces)
    meta['pieces']['Barbell']={'centre':[bx,by],'collision':{'type':'box','size':[L,.4,.4]}}
    rng=np.random.default_rng(66)
    tufts('TY06_Tuft',[(lx-.17,ly-.12,0),(lx+.19,ly+.10,0),(bx-.62,by+.17,0),(bx+.55,by-.18,0),(bx+.1,by+.2,0)],M,'Detail_Grass',rng,spread=.03,h=(.08,.16))
    meta['collision']=[{'type':'box','size':[.34,.22,.33],'center':[lx,ly,.165]},{'type':'box','size':[L,.4,.4],'center':[bx,by,.2]}]
    return meta

def lotus_pad(name,c,r,lift,cup,mat,grp,notch=0.0,tilt=None,seed=1):
    """round lotus leaf: dense radial grid cupped upward around a navel dimple, raised radial veins, a rim that waves in several
    frequencies and curls up at places (notch>0 gives a water-lily style cut toward the stem)"""
    rnd=random.Random(seed);bm=bmesh.new();rings=12;seg=72;V=[[bm.verts.new((0,0,-.004*r))]]
    ph=[rnd.uniform(0,math.tau) for _ in range(4)]
    for i in range(1,rings+1):
        rr=r*i/rings*(1+.04*math.sin(i+seed));row=[]
        for s_ in range(seg):
            a=math.tau*s_/seg+.0001
            if notch and abs(math.atan2(math.sin(a),math.cos(a)))<notch/2 and i>1:a=math.copysign(notch/2,math.atan2(math.sin(a),math.cos(a)))
            t=rr/r;wave=(.05*math.sin(a*5+ph[0])+.035*math.sin(a*9+ph[1])+.02*math.sin(a*17+ph[2]))*r*t**3
            curl=.06*r*max(0,math.sin(a*2+ph[3]))*t**6
            vein=.0035*r*(1-abs(math.cos(a*11)))**4*t*(1-t)*4
            z=cup*t**1.6-.01*r*math.exp(-(t/.12)**2)+wave+curl+vein
            row.append(bm.verts.new((rr*math.cos(a),rr*math.sin(a),z)))
        V.append(row)
    for s_ in range(seg):bm.faces.new((V[0][0],V[1][s_],V[1][(s_+1)%seg]))
    for i in range(1,rings):
        for s_ in range(seg):t=(s_+1)%seg;bm.faces.new((V[i][s_],V[i+1][s_],V[i+1][t],V[i][t]))
    for f in bm.faces:f.smooth=True
    o=finish(name,bm,mat,grp,.3)
    m=o.modifiers.new('t','SOLIDIFY');m.thickness=.003;m.offset=0;apply(o,m)
    if tilt:o.data.transform(tilt)
    o.data.transform(Matrix.Translation((c[0],c[1],lift)));return o

def young_leaf(name,base,h,mat,grp,seed=1):
    """a new lotus leaf still rolled into a slim scroll on its stalk"""
    rnd=random.Random(seed);lean=Vector((rnd.uniform(-.03,.03),rnd.uniform(-.03,.03),0))
    tube(f'{name}Stalk',[base,Vector(base)+lean*.5+Vector((0,0,h*.6)),Vector(base)+lean+Vector((0,0,h*.8))],.004,M_['herb_olive'],grp,6,.1)
    lathe(f'{name}Roll',[(0,0),(.010,.01),(.014,.05),(.010,h*.25),(.004,h*.32),(0,h*.34)],mat,grp,seg=12,center=tuple(Vector(base)+lean+Vector((0,0,h*.78))))

def TY03(stage):
    def build(M):
        """淨水蓮 · four growth stages in shallow water: floating leaves, upright round leaves, a closed pale bud on a slim stem,
        a full open pale white-and-jade flower whose heart glows faintly (separate Glow mesh)"""
        rng=np.random.default_rng(30+stage)
        meta={'moss_low':0,'soil':0,'top':5,'res':{'Leaf':1024,'Flower':1024,'Glow':256,'Detail_Leaf':512},'moss':{}}
        H={1:.15,2:.35,3:.55,4:.65}[stage]
        # floating pads on every stage (they stay as the plant grows)
        for k in range(3 if stage==1 else 2):
            a=k*2.2+.4;r=.10+.06*k
            lotus_pad(f'TY03{stage}_Float{k}',(math.cos(a)*r*1.2,math.sin(a)*r*1.2),rng.uniform(.06,.10) if stage>1 else rng.uniform(.08,.12),.0045,.004,M['herb_green'],'Leaf' if stage==1 else 'Detail_Leaf',seed=k+stage*10,tilt=Matrix.Rotation(a,4,'Z'))
        global M_;M_=M
        if stage==1:
            for k in range(3):   # first leaves lifting off the water on short stalks
                a=k*2.1+1.3;h=rng.uniform(.06,.12);top=Vector((math.cos(a)*.07*(k+1),math.sin(a)*.07*(k+1),h))
                tube(f'TY031_Stalk{k}',[(0,0,0),(top.x*.4,top.y*.4,h*.6),tuple(top)],.004,M['herb_olive'],'Leaf',6,.1)
                lotus_pad(f'TY031_Up{k}',(top.x,top.y),rng.uniform(.06,.085),top.z,.018,M['herb_green'],'Leaf',seed=70+k,tilt=Matrix.Rotation(rng.uniform(-.35,.35),4,'X')@Matrix.Rotation(a,4,'Z'))
            young_leaf('TY031_Young',(.02,-.02,0),.14,M['herb_green'],'Leaf',seed=3)
        if stage>=2:   # upright cupped leaves on curved stems, of different sizes
            nl={2:2,3:3,4:3}[stage]
            for k in range(nl):
                a=k*2.3+.9;h=H*(.65 if stage==2 else .55)*(1-.18*k)+(.08 if stage==2 else 0);r=(.11 if stage==2 else .13)*(1-.15*k)
                top=Vector((math.cos(a)*.10*(k+1),math.sin(a)*.10*(k+1),h))
                tube(f'TY03{stage}_Stem{k}',[(0,0,0),(top.x*.3,top.y*.3,h*.5),tuple(top)],.006,M['herb_olive'],'Leaf',6,.1)
                lotus_pad(f'TY03{stage}_Leaf{k}',(top.x,top.y),r,top.z,r*.35,M['herb_green'],'Leaf',seed=40+k,tilt=Matrix.Rotation(rng.uniform(-.3,.3),4,'X')@Matrix.Rotation(a,4,'Z'))
        if stage==3:   # slim stem with a closed pale bud
            tube('TY033_BudStem',[(0,0,0),(.01,.0,H*.5),(0,0,H-.08)],.007,M['herb_olive'],'Leaf',8,.1)
            lathe('TY033_Bud',[(0,0),(.022,.01),(.035,.035),(.034,.06),(.02,.085),(0,.105)],M['petal'],'Flower',seg=20,center=(0,0,H-.09))
        if stage==4:
            zf=H-.10
            tube('TY034_FlowerStem',[(0,0,0),(.015,0,zf*.5),(0,0,zf)],.008,M['herb_olive'],'Leaf',8,.1)
            for ring,(n,L,W,el,rot) in enumerate(((8,.095,.05,.95,0),(8,.085,.045,.55,math.pi/8),(6,.06,.035,.25,0))):
                for k in range(n):
                    a=k*math.tau/n+rot;d=Vector((math.cos(a)*math.cos(el),math.sin(a)*math.cos(el),math.sin(el)))
                    leaf(f'TY034_Petal{ring}{k}',(math.cos(a)*.015,math.sin(a)*.015,zf),tuple(d),(-math.sin(a),math.cos(a),0),L,W,M['petal'],'Flower',curl=-.25,seg=5)
            lathe('TY034_Heart',[(0,0),(.022,.0),(.026,.015),(.018,.03),(0,.03)],M['lotus_glow'],'Glow',seg=16,center=(0,0,zf+.005))
            for k in range(14):   # stamens
                a=k*math.tau/14;tube(f'TY034_Stamen{k}',[(math.cos(a)*.02,math.sin(a)*.02,zf+.01),(math.cos(a)*.032,math.sin(a)*.032,zf+.035)],.0018,M['flower_gold'],'Flower',4,.1)
            meta['note']='Glow = the seed-pod heart; emission 0..1 for the faint inner light'
        meta['note']=meta.get('note','')+f' · stage {stage} of 4, plant at water level z = 0 (TY01 flooded state)'
        return meta
    return build


def hide(name,c,w,h,mat,grp,seed=1,holes=0,sway=.04,face=(0,-1,0)):
    """hanging hide / cloth: a grid sheet with a ragged hem, slight sag and optional torn holes"""
    rnd=random.Random(seed);bm=bmesh.new();nx,nz=36,44;V={}
    fwd=Vector(face).normalized();side=Vector((0,0,1)).cross(fwd).normalized()
    hole_c=[(rnd.uniform(.2,.8),rnd.uniform(.25,.75),rnd.uniform(.06,.12)) for _ in range(holes)]
    for i in range(nx+1):
        for j in range(nz+1):
            u,v=i/nx,j/nz
            if any(math.hypot(u-a,(v-b)*h/w)<r*(1+.35*math.sin(5*math.atan2(v-b,u-a)+seed)+.2*math.sin(11*math.atan2(v-b,u-a)+a*40)) for a,b,r in hole_c):continue
            hem=(.08*math.sin(u*17+seed)+.06*math.sin(u*31))*h*max(0,1-v/.35)   # ragged hem eased over the lower third: moving only the last row folded it over the rows above
            p=Vector(c)+side*(u-.5)*w+Vector((0,0,-(1-v)*h+hem))+fwd*(sway*math.sin(math.pi*u)*(1-v)+.01*math.sin(u*9+v*7))
            V[i,j]=bm.verts.new(p)
    for i in range(nx):
        for j in range(nz):
            q=[V.get((i,j)),V.get((i+1,j)),V.get((i+1,j+1)),V.get((i,j+1))]
            if all(q):bm.faces.new(q)
    o=finish(name,bm,mat,grp,.5)
    m=o.modifiers.new('t','SOLIDIFY');m.thickness=.006;m.offset=0;apply(o,m);return o

def log(name,a,b,r,mat,grp,sides=14,cap=True):
    o=tube(name,[a,b],r,mat,grp,sides,.4,radii=[r,r*.94]);return o

def SC04(M):
    """獵人工具棚 · forest-edge hunter's tool shed: dry-stone footing, round timber posts, lean-to bark-and-thatch roof held down by
    poles, plank walls open at the front, a patched corner, moss on the north (back) side; inside: hanging hides, traps, rope coils,
    a chopping block with an axe, stacked firewood"""
    meta={'moss_low':.5,'soil':.10,'res':{'Timber':2048,'Roof':2048,'Shakes':4096,'Stone':2048,'Firewood':1024,'Detail_Hang':1024,'Detail_Axe':512,'Detail_Chips':256},
          'moss':{'Timber':.12,'Roof':.35,'Shakes':.45,'Stone':.2},'lichen':{'Stone':.6,'Timber':.3,'Shakes':.5}}
    T,R,S='Timber','Roof','Stone';rng=np.random.default_rng(404);rnd=random.Random(404)
    W,D=2.8,2.1;ZE,ZR=2.02,2.48   # footprint inside the posts; eave and ridge heights of the gable thatch roof (ridge along x)
    # dry-stone footing along back and sides, a low stone kerb across the open front
    for (x0,y0,x1,y1) in ((-W/2-.15,D/2,W/2+.15,D/2),(-W/2,-D/2,-W/2,D/2),(W/2,-D/2,W/2,D/2),(-W/2,-D/2,W/2,-D/2)):
        L_=math.hypot(x1-x0,y1-y0);hor=abs(x1-x0)>abs(y1-y0);front=y0==-D/2 and y1==-D/2
        for row in range(1 if front else 3):
            pos=-rnd.uniform(0,.18)
            while pos<L_-.08:
                ln=rnd.uniform(.20,.40);c=min(pos+ln/2,L_-.06);h=rnd.uniform(.11,.15);dp=rnd.uniform(.22,.30)
                dims=(ln-.025,dp,h) if hor else (dp,ln-.025,h);px,py=x0+(x1-x0)*c/L_,y0+(y1-y0)*c/L_
                rock(f'SC04_Footing{x0:.1f}{y0:.1f}{row}_{pos:.2f}',dims,(px+rnd.uniform(-.015,.015),py+rnd.uniform(-.015,.015),.065+row*.125),M['granite'],S,
                     seed=rnd.randint(0,9999),sub=3,rough=.07,boxy=5,chips=2,rot=rnd.uniform(-.05,.05))
                pos+=ln
    # posts: corners at eave height, a front middle post, ridge posts in the gable ends
    posts=[(-W/2,-D/2,ZE),(0,-D/2,ZE),(W/2,-D/2,ZE),(-W/2,D/2,ZE),(W/2,D/2,ZE),(-W/2,0,ZR),(W/2,0,ZR)]
    for i,(x,y,z) in enumerate(posts):log(f'SC04_Post{i}',(x,y,.18),(x+rnd.uniform(-.02,.02),y,z+.04),.085,M['oldwood'],T)
    for sy in (-1,1):log(f'SC04_Plate{sy}',(-W/2-.32,sy*D/2,ZE+.05),(W/2+.32,sy*D/2,ZE+.05),.075,M['oldwood'],T)
    log('SC04_Ridge',(-W/2-.40,0,ZR+.06),(W/2+.40,0,ZR+.06),.08,M['oldwood'],T)
    for x in np.linspace(-W/2-.1,W/2+.1,6):   # rafter pairs from the ridge past the eaves
        for sy in (-1,1):log(f'SC04_Rafter{x:.2f}{sy}',(x,0,ZR+.12),(x,sy*(D/2+.45),ZE-.10),.05,M['oldwood'],T,10)
    for i,(x,y,z) in enumerate(posts):lashing(f'SC04_PostLash{i}',(x,y,z-.02),(0,0,1),.085,3,M['hemp'],T,cord=.01)
    # plank walls on back and both gable sides (vertical boards, small gaps, one missing on the right)
    def gable(y):return ZE+(ZR-ZE)*(1-abs(y)/(D/2))
    def planks(x0,y0,x1,y1,tag):
        L_=math.hypot(x1-x0,y1-y0);n=int(L_/.18);d=Vector((x1-x0,y1-y0,0)).normalized()
        for k in range(n):
            if tag=='R' and k==4:continue
            t=(k+.5)/n;cx,cy=x0+(x1-x0)*t,y0+(y1-y0)*t;zt=(gable(cy) if tag!='B' else ZE)-.04+rnd.uniform(-.03,.02)
            w=L_/n-.007;box(f'SC04_Plank{tag}{k}',(w if abs(d.x)>.5 else .03,w if abs(d.y)>.5 else .03,zt-.36),(cx,cy,.36+(zt-.36)/2),M['oldwood'],T,bev=.005,cuts=2,jit=.004,seed=rnd.randint(0,9999),scale=.5)
    planks(-W/2,D/2+.04,W/2,D/2+.04,'B')
    planks(-W/2-.04,-D/2+.30,-W/2-.04,D/2,'L')
    planks(W/2+.04,-D/2+.30,W/2+.04,D/2,'R')
    for z in (.55,1.45):
        log(f'SC04_RailB{z}',(-W/2,D/2-.03,z),(W/2,D/2-.03,z),.035,M['oldwood'],T,8)
        log(f'SC04_RailL{z}',(-W/2+.03,-D/2+.2,z),(-W/2+.03,D/2,z),.035,M['oldwood'],T,8)
        log(f'SC04_RailR{z}',(W/2-.03,-D/2+.2,z),(W/2-.03,D/2,z),.035,M['oldwood'],T,8)
    # roof: two thick thatch slopes over bark, ragged eaves, a tied thatch ridge roll, hold-down poles, a patched corner
    X0,X1,HY=-W/2-.34,W/2+.34,D/2+.38;TH=.20
    def roofz(y):return ZR+.16-(ZR-ZE)*abs(y)/(D/2)
    for sy in (-1,1):
        bm=bmesh.new();nx,ny=40,16;V=[]
        for j in range(ny+1):
            row=[]
            for i in range(nx+1):
                x=X0+(X1-X0)*i/nx;y=sy*HY*j/ny
                eave=j==ny;side=i in (0,nx)
                z=roofz(y)+.03*mnoise.noise(Vector((x*1.6,y*1.6,0)))+.015*math.sin(x*11+j)
                if eave:z-=.04+.05*abs(mnoise.noise(Vector((x*7,sy*3,0))));y+=sy*.04*mnoise.noise(Vector((x*5,0,1)))
                if side:x+=(-1 if i==0 else 1)*.03*mnoise.noise(Vector((y*6,0,2)))
                row.append(bm.verts.new((x,y,z)))
            V.append(row)
        for j in range(ny):
            for i in range(nx):bm.faces.new((V[j][i],V[j][i+1],V[j+1][i+1],V[j+1][i]) if sy>0 else (V[j][i],V[j+1][i],V[j+1][i+1],V[j][i+1]))
        o=finish(f'SC04_Thatch{sy}',bm,M['thatch'],R,.6);m=o.modifiers.new('t','SOLIDIFY');m.thickness=TH;m.offset=-1;apply(o,m)
        for k,(dy,dz,tl) in enumerate(((-.02,-.02,(.05,.16)),(-.10,.03,(.04,.12)))):   # ragged straw ends hanging out under the shakes
            straw_fringe(f'SC04_Eave{sy}{k}',X0+.02,X1-.02,sy*(HY+dy),roofz(sy*HY)+dz,sy,M['thatch'],R,rng,hang=.07,teeth=220,tooth=tl,out=.05)
        ang=math.atan((ZR-ZE)/(D/2))   # bark shakes laid in overlapping courses from the eave up to the ridge
        for j in range(9):
            y=sy*(HY-.20-(HY-.30)*j/8);x=X0+.03-rnd.uniform(0,.18)
            while x<X1-.12:
                w=min(rnd.uniform(.20,.36),X1-.03-x);ln=rnd.uniform(.32,.40);x+=w
                if rnd.random()<.05:continue   # a missing shake shows the thatch beneath
                rot=Matrix.Rotation(-sy*ang+rnd.uniform(-.04,.04),4,'X')@Matrix.Rotation(rnd.uniform(-.05,.05),4,'Z')
                newer=sy<0 and .45<x-w/2<1.55 and -1.25<y<-.45   # the patched corner: a few newer, paler shakes
                box(f'SC04_Shake{sy}{j}_{x:.2f}',(w-.012,ln,.022),(x-w/2,y,roofz(y)+.03+.012*(j%2)),M['wood' if newer else 'oldwood'],'Shakes',bev=.004,cuts=2,jit=.006,seed=rnd.randint(0,9999),rot=rot,scale=.4)
        for x in (X0+.5,X1-.5):   # hold-down poles on each slope
            log(f'SC04_HoldPole{sy}{x:.1f}',(x,sy*.05,roofz(0)+.06),(x+rnd.uniform(-.05,.05),sy*(HY-.12),roofz(sy*(HY-.12))+.05),.04,M['oldwood'],T,8)
    tube('SC04_RidgeRoll',[(X0+.05,0,roofz(0)+.04),(X1-.05,0,roofz(0)+.04)],.11,M['thatch'],R,14,.4)
    for x in np.linspace(X0+.2,X1-.2,7):lashing(f'SC04_RidgeTie{x:.2f}',(x,0,roofz(0)+.04),(1,0,0),.11,2,M['hemp'],R,cord=.012)
    for i in range(3):   # bark sheets peeking out under the front eave
        box(f'SC04_Bark{i}',(.6,.10,.025),(-1.0+i*.95,-HY+.06,roofz(-HY)-TH-.01),M['oldwood'],R,bev=.008,cuts=2,jit=.008,seed=70+i)
    # inside: chopping block with an axe, stacked firewood, hanging hides, traps, rope coils, wood chips
    lathe('SC04_Block',[(0,0),(.24,0),(.25,.05),(.23,.40),(.22,.44),(0,.45)],M['oldwood'],'Firewood',seg=24,center=(-.55,-.45,0))
    ax=Vector((-.55,-.45,.45))
    tube('SC04_AxeHaft',[ax+Vector((.0,0,.02)),ax+Vector((.22,-.05,.42))],.018,M['wood'],'Detail_Axe',8,.2)
    box('SC04_AxeHead',(.15,.03,.10),tuple(ax+Vector((-.02,0,.03))),M['iron'],'Detail_Axe',bev=.004,rot=Matrix.Rotation(-.45,4,'Y'))
    for row in range(4):   # firewood stacked against the right wall
        for k in range(9-row):
            y=-D/2+.55+k*.19+row*.09;z=.10+row*.17
            log(f'SC04_Wood{row}{k}',(W/2-.85+rnd.uniform(-.03,.03),y,z),(W/2-.12,y+rnd.uniform(-.02,.02),z),.085+rnd.uniform(-.01,.01),M['oldwood'],'Firewood',10)
    for i,x in enumerate((-1.25,-.85,-.45,.05)):   # hides hanging from the back rail
        hide(f'SC04_Hide{i}',(x,D/2-.12,1.70),rnd.uniform(.35,.5),rnd.uniform(.7,.95),M['hide'],'Detail_Hang',seed=i+1,sway=.03,face=(0,-1,0))
    for i,(x,z) in enumerate(((.55,1.65),(.85,1.55))):   # box traps of sticks
        cx,cy=x,D/2-.18
        for a in range(4):
            for b in range(2):
                p0=(cx-.12+.24*(a%2)+(.017 if a%2==0 else -.017)*b,cy-.09+.18*(a//2),z-.28);tube(   # the two sticks of a corner side by side (they were one on the other)
                    f'SC04_Trap{i}{a}{b}',[p0,(p0[0],p0[1],z)],.008,M['oldwood'],'Detail_Hang',5,.1)
        for zz in (z-.28,z-.14,z):
            tube(f'SC04_TrapRing{i}{zz:.2f}',[(cx-.12,cy-.09,zz),(cx+.12,cy-.09,zz),(cx+.12,cy+.09,zz),(cx-.12,cy+.09,zz),(cx-.12,cy-.09,zz)],.007,M['oldwood'],'Detail_Hang',5,.1,caps=False)
    for i,(x,y,z,r) in enumerate(((-W/2+.1,-.2,1.5,.16),(-W/2+.1,.35,1.35,.13),(1.25,D/2-.1,1.3,.15))):   # rope coils on pegs
        for t in range(4):
            rt=r*(1+.04*t);ox,oy=(t*.021,0) if x<0 else (0,-t*.021)   # turns lie side by side along the peg (they were the same loop lifted 12 mm, in one plane)
            pts=[(x+ox+(0 if x<0 else math.cos(a)*rt),y+oy+(math.cos(a)*rt if x<0 else 0),z+math.sin(a)*rt+t*.004) for a in np.linspace(0,math.tau,25)]
            tube(f'SC04_Coil{i}{t}',pts,.011,M['hemp'],'Detail_Hang',6,.1,caps=False)
    for k in range(18):
        a=rnd.uniform(0,math.tau);r=rnd.uniform(.3,.6)
        box(f'SC04_Chip{k}',(rnd.uniform(.04,.08),.025,.008),(-.55+math.cos(a)*r,-.45+math.sin(a)*r,.004),M['wood'],'Detail_Chips',bev=0,rot=Matrix.Rotation(a,4,'Z'))
    meta['collision']=[{'type':'box','size':[W+.3,.25,ZE],'center':[0,D/2+.04,ZE/2]},{'type':'box','size':[.25,D,ZE],'center':[-W/2-.04,0,ZE/2]},
                       {'type':'box','size':[.25,D,ZE],'center':[W/2+.04,0,ZE/2]},{'type':'cylinder','radius':.1,'height':ZE,'center':[0,-D/2,ZE/2]},
                       {'type':'cylinder','radius':.1,'height':ZE,'center':[-W/2,-D/2,ZE/2]},{'type':'cylinder','radius':.1,'height':ZE,'center':[W/2,-D/2,ZE/2]},
                       {'type':'cylinder','radius':.26,'height':.45,'center':[-.55,-.45,.225]},{'type':'box','size':[.75,1.7,.75],'center':[W/2-.48,-D/2+1.3,.375]}]
    meta['walkable']={'note':'open front between the posts (two 1.5 m bays); floor is the ground inside the footing'}
    return meta

def SC03(M):
    """倒塌的歇腳亭 · collapsed rest pavilion: worn stone plinth with one step, one post still standing at 3.2 m with a bird's nest
    and a wild vine, a broken stump, the blue-grey tiled hip roof caved in and sliding to one side with a corner on the ground, a fallen
    beam, a broken bench, scattered tiles, grass through the plinth. Walkable; only the post and the tile heap block."""
    meta={'moss_low':.45,'soil':.08,'res':{'Stone':2048,'Timber':2048,'Roof':2048,'Detail_Tiles':1024,'Detail_Vine':512,'Detail_Nest':256,'Detail_Grass':512},
          'moss':{'Stone':.5,'Roof':.55,'Timber':.1}}
    S,T,R='Stone','Timber','Roof';rnd=random.Random(303);rng=np.random.default_rng(303)
    PX=1.62;PH=.32
    box('SC03_PlinthCore',(2*PX-.2,2*PX-.2,PH-.02),(0,0,(PH-.02)/2),M['plinth'],S,bev=0)
    for side in range(4):
        horiz=side%2==0;sgn=-1 if side<2 else 1;x=-PX
        while x<PX-.02:
            ln=min(rnd.uniform(.45,.7),PX-x);c=x+ln/2
            cen=(c,sgn*(PX-.12),PH/2) if horiz else (sgn*(PX-.12),c,PH/2);sz=(ln-.012,.24,PH-.01) if horiz else (.24,ln-.012,PH-.01)
            box(f'SC03_Kerb{side}{x:.2f}',sz,cen,M['plinth'],S,bev=.02,cuts=2,jit=.006,seed=rnd.randint(0,9999),scale=.7);x+=ln
    for i in range(6):
        for j in range(6):
            if rnd.random()<.12:continue   # a few flags missing
            w=2*(PX-.24)/6;box(f'SC03_Flag{i}{j}',(w-.014,w-.014,.05),(-(PX-.24)+w*(i+.5),-(PX-.24)+w*(j+.5),PH-.015+rnd.uniform(-.01,.008)),M['plinth'],S,bev=.012,cuts=1,jit=.003,seed=i*7+j,scale=.7)
    box('SC03_Step',(1.3,.34,.16),(0,-PX-.15,.08),M['plinth'],S,bev=.02,cuts=2,jit=.005,seed=99,scale=.7)
    # standing post (back-left) and a broken stump (back-right); drum bases at all four corners
    P0=1.25
    for sx in (-1,1):
        for sy in (-1,1):lathe(f'SC03_Base{sx}{sy}',[(.15,0),(.17,.03),(.17,.08),(.14,.11),(0,.11)],M['granite'],S,seg=24,center=(sx*P0,sy*P0,PH))
    log('SC03_Post',(-P0,P0,PH+.1),(-P0+.02,P0,3.18),.10,M['oldwood'],T,16)
    log('SC03_Post2',(-P0,-P0,PH+.1),(-P0+.22,-P0+.04,2.62),.095,M['oldwood'],T,16)   # leaning, still standing
    o=log('SC03_Stump',(P0,P0,PH+.1),(P0,P0,1.05),.10,M['oldwood'],T,16)
    for k in range(6):   # splintered top of the stump
        a=k*math.tau/6;tube(f'SC03_Splinter{k}',[(P0+math.cos(a)*.06,P0+math.sin(a)*.06,1.02),(P0+math.cos(a)*.07,P0+math.sin(a)*.07,1.12+rnd.uniform(0,.12))],.018,M['oldwood'],T,5,.1,radii=[.02,.004])
    # roof: a hip roof slab tilted and slid toward +x/-y; its low corner rests on the plinth
    HW,HD,ZE,ZR=1.9,1.9,0,.95;PIT=.16
    def roll(c):
        t=(c/PIT)%1;return .04*math.sqrt(max(0,1-((t-.5)/.22)**2))+.008*math.cos(math.tau*t)
    def bump(x,y,dx,dy):
        e=min(dx,dy);return roll(x if dy<=dx else y)*min(1,e/.04)
    start=len(parts)
    o,zf=hip_surface('SC03_Roof',HW,HD,ZE,ZR,1.5,.32,M['tile'],R,step=.03,thick=.09,bump=bump,region=(-HW,HW*.55,-HD,HD*.7))
    box('SC03_RoofRidge',(.3,.16,.16),(0,0,ZR+.06),M['tile'],R,bev=.02,cuts=1)
    # rafters follow the underside of the tile slab and sit 6 mm into it (straight ones under the concave roof hung 3-5 cm below)
    from mathutils.bvhtree import BVHTree
    rb=BVHTree.FromPolygons([v.co.copy() for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons])
    def under(x,y):
        h=rb.ray_cast(Vector((x,y,-5.0)),Vector((0,0,1)));return h[0].z if h[0] is not None else zf(x,y,min(HW-abs(x),HD-abs(y)))-.09
    for x in np.linspace(-HW+.2,HW*.5,6):
        ys=np.linspace(-HD+.2,HD*.6,7);tube(f'SC03_Rafter{x:.2f}',[(x,y,under(x,y)-.035+.006) for y in ys],.035,M['oldwood'],T,8,.4,radii=[.035]*7)
    tilt=Matrix.Rotation(math.radians(38),4,'Y')@Matrix.Rotation(math.radians(-8),4,'X')
    for o in parts[start:]:o.data.transform(tilt)
    zmin=min(v.co.z for o in parts[start:] for v in o.data.vertices)
    for o in parts[start:]:o.data.transform(Matrix.Translation((.15,-.12,PH+.02-zmin)))
    # fallen beam leaning from the standing post down to the plinth, a broken bench
    log('SC03_FallenBeam',(-P0+.1,P0-.1,2.55),(1.35,-1.1,PH+.06),.09,M['oldwood'],T,12)
    for sx in (-1,1):box(f'SC03_BenchLeg{sx}',(.08,.30,.38),(-.75+sx*.55,1.05,PH+.19),M['oldwood'],T,bev=.01,cuts=2,jit=.004,seed=50+sx)
    box('SC03_BenchSeat',(1.35,.32,.06),(-.85,1.05,PH+.36),M['planks'],T,bev=.01,cuts=4,jit=.008,seed=55,rot=Matrix.Rotation(math.radians(-9),4,'Y'))
    # scattered tiles, vine on the post, nest on top, grass through the plinth joints
    for k in range(26):
        a=rnd.uniform(-.9,1.4);r=rnd.uniform(.5,1.8);x,y=math.cos(a)*r+.2,-math.sin(a)*r*.8
        if abs(x)>PX+.2 or abs(y)>PX+.4:continue
        box(f'SC03_Tile{k}',(.22,.14,.016),(x,y,(PH if abs(x)<PX and abs(y)<PX else 0)+.012),M['tile'],'Detail_Tiles',bev=.004,cuts=2,rot=Matrix.Rotation(rnd.uniform(0,math.tau),4,'Z')@Matrix.Rotation(rnd.uniform(-.25,.25),4,'X'))
    for k in range(26):
        z=PH+.15+k*.1;a=k*.9;t=(z-PH-.1)/(3.18-PH-.1);ax=-P0+.02*t;rr=.10*(1-.06*t)-.006   # leaf bases on the tapered, leaning post (they stood 0.5-2.8 cm off it)
        leaf(f'SC03_Vine{k}',(ax+math.cos(a)*rr,P0+math.sin(a)*rr,z),(math.cos(a)*.7,math.sin(a)*.7,.4),(-math.sin(a),math.cos(a),0),rnd.uniform(.07,.11),.06,M['herb_green'],'Detail_Vine',curl=.35,seg=4)
    for k in range(16):   # nest of twigs on the post top, each rooted inside the post head (they hovered 1 cm off it)
        a=k*math.tau/16;tube(f'SC03_Nest{k}',[(-P0+.02+math.cos(a)*.085,P0+math.sin(a)*.085,3.15),(-P0+.02+math.cos(a+1.2)*.13,P0+math.sin(a+1.2)*.13,3.22)],.006,M['oldwood'],'Detail_Nest',4,.1)
    tufts('SC03_Tuft',[(rnd.uniform(-1.3,1.3),rnd.uniform(-1.3,1.3),PH) for _ in range(9)]+[(-1.7,.5,0),(1.7,-.8,0),(.4,1.75,0)],M,'Detail_Grass',rng,spread=.05,h=(.12,.26))
    meta['collision']=[{'type':'cylinder','radius':.13,'height':3.2,'center':[-P0,P0,1.6]},{'type':'cylinder','radius':.13,'height':2.6,'center':[-P0+.11,-P0+.02,1.3]},{'type':'cylinder','radius':.13,'height':1.1,'center':[P0,P0,.55]},
                       {'type':'box','size':[1.7,1.35,.9],'center':[.7,-.5,.45],'yaw':-12}]   # the leaning roof's low end and tile heap
    meta['walkable']={'note':'plinth top 0.32 m; walk in over the front step; the roof heap and the post block, everything else is open'}
    return meta

def SC02(M):
    """熄掉的獵人營地 · abandoned hunter's camp: cold fire pit of blackened stones in ash, a log stool, a pole drying frame with a torn
    hide, a rusty pot on a tripod, a broken snare, weeds through the ashes, rain-rotted rope, fallen maple leaves"""
    meta={'moss_low':.4,'soil':.08,'res':{'Stone':2048,'Ash':1024,'Timber':1024,'Iron':512,'Hide':1024,'Detail_Leaves':512,'Detail_Grass':512,'Detail_Snare':256},
          'moss':{'Stone':.35,'Timber':.15,'Ash':0}}
    S,T='Stone','Timber';rnd=random.Random(202);rng=np.random.default_rng(202)
    fx,fy=-.35,-.35
    rock('SC02_Ash',(.82,.76,.045),(fx,fy,.0),M['charcoal'],'Ash',seed=21,sub=4,rough=.35,flat_top=.3,boxy=1.6)
    for k in range(11):   # ring of blackened stones
        a=k*math.tau/11;sz=rnd.uniform(.16,.24)
        rock(f'SC02_Ring{k}',(sz,sz*.85,sz*.7),(fx+math.cos(a)*.52,fy+math.sin(a)*.48,.0),M['granite'] if k%3 else M['charcoal'],S,seed=220+k,sub=3,rough=.18,rot=a)
    for k in range(5):   # charred sticks in the ash, fanned and stacked 6 mm apart (two at one angle lay on each other)
        a=rnd.uniform(0,math.tau)*.2+k*math.tau/5;log(f'SC02_Char{k}',(fx+math.cos(a)*.3,fy+math.sin(a)*.3,.05+.006*k),(fx-math.cos(a)*.1,fy-math.sin(a)*.1,.08+.006*k),.025,M['charcoal'],'Ash',8)
    lathe('SC02_Stool',[(0,0),(.2,0),(.21,.04),(.19,.38),(.18,.42),(0,.43)],M['oldwood'],T,seg=22,center=(.55,-.75,0))
    # drying frame: two forked uprights and a crossbar, torn hide hanging, lashings
    for sx in (-1,1):
        log(f'SC02_Upright{sx}',(sx*.85+.2,.75,0),(sx*.85+.2+sx*.03,.75,1.19),.04,M['oldwood'],T,10)   # top stands clear of the crossbar (was flush with its top)
        for k in (-1,1):tube(f'SC02_Fork{sx}{k}',[(sx*.85+.2,.75,1.05),(sx*.85+.2+k*.07,.75,1.18)],.018,M['oldwood'],T,6,.1)
    log('SC02_Crossbar',(-.75,.75,1.10),(1.15,.75,1.12),.032,M['oldwood'],T,10)
    hide('SC02_Hide',(.2,.73,1.10),1.05,.78,M['hide'],'Hide',seed=7,holes=0,sway=.05,face=(0,-1,0))
    for sx in (-1,1):lashing(f'SC02_Lash{sx}',(sx*.85+.2,.75,1.08),(0,0,1),.04,3,M['hemp'],T,cord=.008)
    # tripod with a rusty pot over the cold pit
    for k in range(3):
        a=k*math.tau/3+.3;log(f'SC02_Tripod{k}',(fx+math.cos(a)*.62,fy+math.sin(a)*.6,0),(fx,fy,1.05),.025,M['oldwood'],T,8)
    tube('SC02_PotChain',[(fx,fy,1.02),(fx,fy,.62)],.006,M['iron'],'Iron',5,.1)
    lathe('SC02_Pot',[(0,0),(.10,.0),(.15,.05),(.16,.13),(.14,.2),(.15,.21),(.13,.22),(.12,.2),(0,.06)],M['iron'],'Iron',seg=28,center=(fx,fy,.36))
    tube('SC02_PotHandle',[(fx-.15,fy,.57),(fx,fy,.64),(fx+.15,fy,.57)],.006,M['iron'],'Iron',6,.1)
    # broken snare: bent sapling stick and a rope loop, rotted rope lying on the ground
    tube('SC02_SnareStick',[(1.1,-.2,0),(1.05,-.15,.35),(.85,-.2,.48)],.016,M['oldwood'],'Detail_Snare',6,.1)
    tube('SC02_SnareLoop',[(.85+.08*math.cos(a),-.2+.08*math.sin(a),.02) for a in np.linspace(0,math.tau,17)],.006,M['hemp'],'Detail_Snare',5,.1,caps=False)
    tube('SC02_RottenRope',[(-1.2,.2,.01),(-1.0,.0,.012),(-.95,-.25,.01),(-1.1,-.5,.012)],.01,M['hemp'],'Detail_Snare',6,.1)
    for k in range(22):   # fallen maple leaves
        a=rnd.uniform(0,math.tau);r=rnd.uniform(.2,1.35);d=rnd.uniform(0,math.tau)
        leaf(f'SC02_Leaf{k}',(math.cos(a)*r,math.sin(a)*r,.01),(math.cos(d),math.sin(d),.05),(0,0,1),rnd.uniform(.10,.15),.09,M['leaf_fallen'],'Detail_Leaves',curl=.15,seg=4)
    tufts('SC02_Tuft',[(fx+.1,fy-.1,.03),(fx-.2,fy+.15,.03),(.9,.4,0),(-1.1,.6,0),(1.2,-.9,0),(-.9,-1.0,0)],M,'Detail_Grass',rng,spread=.04,h=(.10,.24))
    meta['collision']=[{'type':'cylinder','radius':.22,'height':.43,'center':[.55,-.75,.215]},{'type':'box','size':[1.95,.2,1.2],'center':[.2,.75,.6]}]
    return meta

def wheel(P,cx,cy,cz,R,M,grp,spokes=12,seed=1):
    """cart wheel around the X axis: felloes with an iron tyre, hub with an iron band, turned spokes"""
    rot=Matrix.Rotation(math.radians(90),4,'Y')
    rim=lathe(f'{P}_Felloe',[(R-.07,-.045),(R-.012,-.045),(R-.012,.045),(R-.07,.045)],M['oldwood'],grp,seg=48);rim.data.transform(rot)
    tyre=lathe(f'{P}_Tyre',[(R-.014,-.04),(R,-.04),(R,.04),(R-.014,.04)],M['iron'],grp,seg=48);tyre.data.transform(rot)
    hub=lathe(f'{P}_Hub',[(0,-.13),(.055,-.13),(.075,-.08),(.085,0),(.075,.08),(.055,.13),(0,.13)],M['wood'],grp,seg=24);hub.data.transform(rot)
    for z in (-.09,.09):
        b=lathe(f'{P}_HubBand{z}',[(.08,z-.012),(.088,z-.012),(.088,z+.012),(.08,z+.012)],M['iron'],grp,seg=24);b.data.transform(rot)
    objs=[rim,tyre,hub]+parts[-2:]
    for k in range(spokes):
        a=k*math.tau/spokes;d=Vector((0,math.cos(a),math.sin(a)))
        s=tube(f'{P}_Spoke{k}',[d*.07,d*(R-.06)],.02,M['wood'],grp,8,.2,radii=[.024,.017]);objs.append(s)
    for o in objs:o.data.transform(Matrix.Translation((cx,cy,cz)))

def sack(name,c,dims,mat,grp,seed=1,tied=True):
    o=rock(name,dims,c,mat,grp,seed=seed,sub=4,rough=.12,boxy=2.6,flat_bottom=True)
    if tied:   # gathered neck and tie
        top=Vector(c)+Vector((dims[0]*.35,0,dims[2]*.42))
        lathe(f'{name}Neck',[(0,0),(.045,.0),(.03,.05),(.05,.10),(0,.11)],mat,grp,seg=12,center=tuple(top))
        lashing(f'{name}Tie',tuple(top+Vector((0,0,.035))),(0,0,1),.03,2,M_['hemp'],grp,cord=.006)
    return o

def RK05(M):
    """載貨板車 · two-wheeled elm goods cart resting on its prop: shafts running into the bed rails, stake-and-board sides with a
    mended rail, iron-bound wheels with dried mud (each wheel its own mesh with its origin on the axle), loaded with hemp sacks and
    bamboo baskets tied down with rope"""
    global M_;M_=M
    meta={'moss_low':.0,'soil':.32,'res':{'Timber':2048,'WheelL':1024,'WheelR':1024,'Load':2048,'Detail_Rope':512,'Detail_Cloth':512},
          'moss':{'Timber':.05},'pivots':{}}
    T='Timber';rnd=random.Random(505);start=len(parts)
    R=.56;AX=.03;CZ=R;BW=1.12;BL=1.9;bz=CZ+.10   # wheel radius, axle x position, bed width/length, bed underside height
    # shafts = side rails extended forward, sloping down to a prop at the front
    for sx in (-1,1):
        log(f'RK05_Shaft{sx}',(sx*BW/2,BL/2,bz),(sx*.32,-1.55,.62),.045,M['oldwood'],T,10)
    for y in np.linspace(-BL/2+.1,BL/2-.1,5):log(f'RK05_Cross{y:.2f}',(-BW/2,y,bz),(BW/2,y,bz),.035,M['oldwood'],T,8)
    for k in range(9):   # bed planks
        x=-BW/2+.06+k*(BW-.12)/8;box(f'RK05_Bed{k}',((BW-.12)/8.4,BL,.035),(x,0,bz+.05),M['planks'],T,bev=.004,cuts=3,jit=.003,seed=k,scale=.5)
    for sx in (-1,1):   # stakes and side boards
        for y in np.linspace(-BL/2+.08,BL/2-.08,5):box(f'RK05_Stake{sx}{y:.2f}',(.05,.05,.42),(sx*(BW/2+.02),y,bz+.25),M['oldwood'],T,bev=.006,cuts=2,jit=.003,seed=int(y*50))
        for z in (bz+.18,bz+.36):box(f'RK05_Side{sx}{z:.2f}',(.03,BL,.13),(sx*(BW/2+.05),0,z),M['planks'],T,bev=.004,cuts=4,jit=.004,seed=int(z*100)+sx)
    box('RK05_Mend',(.035,.38,.15),(BW/2+.075,.25,bz+.36),M['wood'],T,bev=.004,cuts=1,seed=9)   # newer board nailed over a break
    for z in (bz+.12,bz+.30):lashing(f'RK05_MendLash{z:.2f}',(BW/2+.07,.25,z),(0,1,0),.02,3,M['hemp'],T,cord=.007)
    for sy in (-1,1):box(f'RK05_End{sy}',(BW,.03,.30),(0,sy*(BL/2+.03),bz+.20),M['planks'],T,bev=.004,cuts=3,jit=.004,seed=40+sy)
    log('RK05_Axle',(-BW/2-.20,AX,CZ),(BW/2+.20,AX,CZ),.04,M['wood'],T,10)
    log('RK05_Prop',(0,-1.45,.0),(0,-1.47,.64),.035,M['oldwood'],T,8)
    for sx,g in ((-1,'WheelL'),(1,'WheelR')):
        wheel(f'RK05_{g}',sx*(BW/2+.12),AX,CZ,R,M,g,seed=sx)
        meta['pivots'][g]=(sx*(BW/2+.12),AX,CZ)
    # load: hemp sacks, two bamboo baskets, rope over the top, a grey cloth
    sk=[(-.25,-.55,.34,.30),(.26,-.5,.36,.28),(-.2,-.05,.34,.30),(.28,.05,.32,.27),(0,.5,.36,.30),(-.05,-.3,.34,.26)]
    for i,(x,y,w,h) in enumerate(sk):
        sack(f'RK05_Sack{i}',(x,y,bz+.07+h/2+(.22 if i==5 else 0)),(w*1.05,w*.8,h),M['linen'],'Load',seed=i+1)
    for i,(x,y) in enumerate(((.22,.55),(-.30,.62))):
        prof=[(0,0),(.15,0),(.19,.04),(.22,.24),(.23,.32),(.215,.33),(.205,.25),(.17,.05),(0,.04)]
        lathe(f'RK05_Basket{i}',prof,M['weave'],'Load',seg=40,cyl=True,center=(x,y,bz+.07))
        tube(f'RK05_BasketRim{i}',[(x+.23*math.cos(a),y+.23*math.sin(a),bz+.40) for a in np.linspace(0,math.tau,33)],.012,M['bamboo_old'],'Load',6,.2,caps=False)
    for k,y in enumerate((-.45,.1,.6)):   # ropes thrown over the load and tied to the stakes
        pts=[(-BW/2-.03,y,bz+.36)]+[(x,y+.02*math.sin(x*6),bz+.68+.06*math.cos(x*2.5)) for x in np.linspace(-.42,.42,7)]+[(BW/2+.03,y,bz+.36)]
        rope(f'RK05_Rope{k}',pts,.012,M['hemp'],'Detail_Rope')
    hide('RK05_Cloth',(.3,-.8,bz+.62),.45,.35,M['linen'],'Detail_Cloth',seed=5,sway=.06,face=(1,-.4,0))
    turn=Matrix.Rotation(math.radians(90),4,'Z')   # length along x (the 3.2 m side of the limit), shafts toward +x
    for o in parts[start:]:o.data.transform(turn)
    meta['pivots']={g:tuple(turn@Vector(v)) for g,v in meta['pivots'].items()}
    meta['collision']=[{'type':'box','size':[BL+.1,BW+.42,1.0],'center':[0,0,.5]},{'type':'box','size':[1.1,.8,.6],'center':[1.0,0,.3]}]   # shafts and prop, up to the shaft tips
    meta['note']='WheelL / WheelR origins are on the axle (y axis); spin them about local Y when the cart moves'
    return meta

# ITEMS_END
PROPS={'RK09':RK09,'RK06':RK06,'SC01':SC01,'TY06':TY06,'SC04':SC04,'SC03':SC03,'SC02':SC02,'RK05':RK05}
PROPS.update({f'RK01{v}':RK01(v) for v in 'AB'});PROPS.update({f'RK10{v}':RK10(v) for v in 'AB'});PROPS.update({f'TY03{'ABCD'[i-1]}':TY03(i) for i in (1,2,3,4)})
PROPS.update({f'WM08{v}':WM08(v) for v in 'ABC'});PROPS.update({f'WM10{v}':WM10(v) for v in 'ABCD'});PROPS.update({f'RK12{v}':RK12(v) for v in 'ABCD'})

# ---------------- collision ----------------
def collision(pid,meta,dims):
    """static collider meshes joined into <ID>_Collision from meta['collision'] primitives (item frame, before recentring)"""
    prims=[]
    for c in meta.get('collision',[]):
        p=dict(c);p['center']=[round(p['center'][i]+float(meta['offset'][i]),3) for i in range(3)]
        if 'size' in p:p['size']=[round(v,3) for v in p['size']]
        prims.append(p)
    if not prims:return None,[]
    objs=[]
    for p in prims:
        if p['type']=='box':
            bm=box_bm(p['size'],(0,0,0))
            if p.get('yaw'):bmesh.ops.rotate(bm,verts=bm.verts,matrix=Matrix.Rotation(math.radians(p['yaw']),3,'Z'))
            bmesh.ops.translate(bm,verts=bm.verts,vec=Vector(p['center']))
        else:
            bm=bmesh.new();bmesh.ops.create_cone(bm,cap_ends=True,segments=12,radius1=p['radius'],radius2=p['radius'],depth=p['height'])
            bmesh.ops.translate(bm,verts=bm.verts,vec=Vector(p['center']))
        me=bpy.data.meshes.new('col');bm.to_mesh(me);bm.free();o=bpy.data.objects.new('col',me);bpy.context.scene.collection.objects.link(o);objs.append(o)
    c=join(objs,f'{pid}_Collision');c.data.name=c.name;c.hide_render=True;c.display_type='WIRE'
    return c,prims
MOSS={'Stone':.55,'Roof':.45,'Timber':.06,'Wood':.06,'Thatch':.12,'Detail':.1}


# ---------------- high-detail pass (user, 2026-11-03: "面數可以高很多很多，為了極致的美感") ----------------
HD={'granite':(.022,.0065,'stone'),'plinth':(.024,.005,'stone'),'bluestone':(.022,.006,'stone'),'soil':(.03,.012,'stone'),
    'oldwood':(.018,.0022,'wood'),'wood':(.02,.0018,'wood'),'planks':(.02,.002,'wood'),'tile':(.02,.0025,'stone'),'straw':(.025,.010,'straw')}
def fold_safe_displace(me,co0,nr0,disp):
    """move vertices along their snapshotted normals; where that turns a face over (small bevel faces at sharp corners, crack
    grooves) the displacement of its vertices is halved, up to four times, then dropped, so the surface never folds onto itself"""
    nf=len(me.polygons);nl=len(me.loops);ls=np.empty(nf,np.int64);lt=np.empty(nf,np.int64);lv=np.empty(nl,np.int64)
    me.polygons.foreach_get('loop_start',ls);me.polygons.foreach_get('loop_total',lt);me.loops.foreach_get('vertex_index',lv)
    face=np.repeat(np.arange(nf),lt);nxt=np.arange(nl)+1;ends=ls+lt-1;nxt[ends]=ls   # Newell normals, vectorised over loops
    fv=np.split(lv,ls[1:])
    def fnorm(co):
        out=np.zeros((nf,3));np.add.at(out,face,np.cross(co[lv],co[lv[nxt]]));return out
    n0=fnorm(co0);d=disp.copy()
    for it in range(5):
        co=co0+nr0*d[:,None];n1=fnorm(co)
        l0=np.linalg.norm(n0,axis=1)+1e-20;l1=np.linalg.norm(n1,axis=1)+1e-20
        bad=np.where((n0*n1).sum(1)/(l0*l1)<.25)[0]
        if not len(bad):break
        vs=np.unique(np.concatenate([fv[i] for i in bad]));d[vs]*=.5 if it<4 else 0
    co=co0+nr0*d[:,None];me.vertices.foreach_set('co',co.ravel());me.update()
    return d

def self_overlaps(bm,eps=.001,isl=None,pairs=False):
    """same test as the asset QA's z-fighting check, within one part: non-adjacent triangles facing the same way within eps
    whose areas overlap (a pleat of the surface lying on itself). Returns the BMesh faces involved."""
    from mathutils.bvhtree import BVHTree
    tri=bm.calc_loop_triangles();V=[v.co.copy() for v in bm.verts];T=[tuple(l.vert.index for l in t) for t in tri];F=[t[0].face for t in tri]
    N=[(V[b]-V[a]).cross(V[c]-V[a]) for a,b,c in T];N=[n.normalized() if n.length>1e-15 else n for n in N]
    bvh=BVHTree.FromPolygons(V,T,epsilon=0.0);hit=set()
    def inside(p,a,b,c,n):return all((v-u).cross(p-u).dot(n)>=-1e-9 for u,v in ((a,b),(b,c),(c,a)))
    for i,t in enumerate(T):
        if N[i].length<.5:continue
        A,B,C=(V[j] for j in t);c=(A+B+C)/3
        for p in (c,c.lerp(A,.6),c.lerp(B,.6),c.lerp(C,.6)):
            for _,_,j,_ in bvh.find_nearest_range(p,eps):
                if j is None or j==i or set(T[i])&set(T[j]) or N[i].dot(N[j])<.999:continue
                if isl is not None and isl[T[i][0]]!=isl[T[j][0]]:continue
                a2,b2,c2=(V[x] for x in T[j]);q=p-N[j]*N[j].dot(p-a2)
                if inside(q,a2,b2,c2,N[j]):hit.add((F[i],F[j]) if pairs else F[i]);pairs or hit.add(F[j])
    return hit

def unpleat(me,co0,nr0,disp,iters=6):
    """pull the detail displacement back where it folds the surface onto itself: vertices of overlapping facets and their
    neighbours keep half their displacement per round, none after four rounds (the undisplaced subdivided surface is clean)"""
    d=disp.copy();n0=None
    for it in range(iters):
        bm=bmesh.new();bm.from_mesh(me);bmesh.ops.triangulate(bm,faces=bm.faces[:]);bm.verts.ensure_lookup_table()
        hit=self_overlaps(bm);n=len(hit)
        if n0 is None:n0=n
        if not hit:bm.free();break
        vs={v.index for f in hit for v in f.verts};vs|={w.index for i in list(vs) for e in bm.verts[i].link_edges for w in e.verts};bm.free()
        vs=np.fromiter(vs,int);d[vs]*=.5 if it<3 else 0
        co=co0+nr0*d[:,None];me.vertices.foreach_set('co',co.ravel());me.update()
    return n0,n

def defold(o,iters=8):
    """relax pleats left by subdivision + displacement until the part has no self-overlapping facets"""
    # triangulated first, the same way the export does: a quad that is clean as one face can still fold once it is split, and the
    # check on the quads reported 0 left while the exported triangles kept 27 overlapping pairs (RK09 seat)
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.triangulate(bm,faces=bm.faces[:]);bm.verts.ensure_lookup_table();n0=None
    for it in range(iters):
        hit=self_overlaps(bm)
        if n0 is None:n0=len(hit)
        if not hit:break
        vs={v for f in hit for v in f.verts};vs|={w for v in list(vs) for e in v.link_edges for w in e.verts}
        bmesh.ops.smooth_vert(bm,verts=list(vs),factor=.6,use_axis_x=True,use_axis_y=True,use_axis_z=True)
    bm.to_mesh(o.data);bm.free();o.data.update();return n0,len(hit)

def hd_pass(objs):
    """subdivide each eligible part to a target edge length, then displace along the normal: ridged noise for stone (cracks and
    facets), long anisotropic grain for timber, combed streaks for straw. Thin parts and Detail_* groups are left alone."""
    for o in objs:
        if o.get('grp','').startswith('Detail') or not o.data.materials:continue
        key=o.data.materials[0].name.replace('src_','')
        if key not in HD:continue
        edge,amp,kind=HD[key]
        dims=o.dimensions
        if min(dims)<.03:continue
        me=o.data;el=[(me.vertices[e.vertices[0]].co-me.vertices[e.vertices[1]].co).length for e in me.edges]
        if not el:continue
        avg=sum(el)/len(el);lv=0
        while avg/(2**lv)>edge and lv<4:lv+=1
        if lv:
            m=o.modifiers.new('hd','SUBSURF');m.subdivision_type='SIMPLE';m.levels=lv;m.render_levels=lv;apply(o,m)
        me=o.data;me.update()
        seed=Vector((hash(o.name)%97,hash(o.name)%89,hash(o.name)%83))
        # normals and positions snapshotted first (reading v.normal of a half-moved mesh re-derives it and folds the surface)
        nv=len(me.vertices);co0=np.empty(nv*3);me.vertices.foreach_get('co',co0);nr0=np.empty(nv*3);me.vertices.foreach_get('normal',nr0)
        co0=co0.reshape(nv,3);nr0=nr0.reshape(nv,3);disp=np.zeros(nv)
        for v in me.vertices:
            q=v.co*1.0+seed
            if kind=='stone':
                n=(1-abs(mnoise.noise(q*7)))**3*.6+mnoise.noise(q*18)*.25+mnoise.noise(q*45)*.1-.25
            elif kind=='wood':
                d=Vector((q.x*.15,q.y*9,q.z*9)) if dims.x>max(dims.y,dims.z) else (Vector((q.x*9,q.y*.15,q.z*9)) if dims.y>dims.z else Vector((q.x*9,q.y*9,q.z*.15)))
                n=mnoise.noise(d)*.7+(1-abs(mnoise.noise(d*3)))**6*-.9
            else:
                n=mnoise.noise(Vector((q.x*22,q.y*22,q.z*2)))*.8+mnoise.noise(q*40)*.2
            disp[v.index]=amp*n
        disp=fold_safe_displace(me,co0,nr0,disp)
        print('UNPLEAT',o.name,*unpleat(me,co0,nr0,disp))   # every size: the >300k parts were skipped before and kept their pleats
        print('DEFOLD',o.name,*defold(o,24))

# ---------------- bake / LOD / export ----------------
def gpu(sc):
    try:
        pr=bpy.context.preferences.addons['cycles'].preferences
        for t in ('OPTIX','CUDA'):
            try:pr.compute_device_type=t
            except TypeError:continue
            pr.get_devices();ds=[d for d in pr.devices if d.type==t]
            if ds:
                for d in pr.devices:d.use=d.type==t
                sc.cycles.device='GPU';return t
    except Exception as e:print('GPU unavailable',e)
    sc.cycles.device='CPU';return 'CPU'
SETTLE={'Detail_Grass','Detail_Ferns','Detail_Tiles','Detail_Leaves','Detail_Offerings','Detail_Straw'}
def settle(objs):
    """loose ground dressing (grass and fern blades, fallen tiles, leaves, fruit) was placed at hand-picked heights; drop every
    piece whose lowest point hangs in the air onto the surface below it (a stone, the mound, or the ground at z 0), 2 mm in"""
    from mathutils.bvhtree import BVHTree
    sol=[o for o in objs if not o.get('grp','').startswith('Detail')];V=[];T=[]
    for o in sol:
        b=len(V);V+=[o.matrix_world@v.co for v in o.data.vertices];T+=[[b+i for i in p.vertices] for p in o.data.polygons]
    bvh=BVHTree.FromPolygons(V,T) if T else None;up=Vector((0,0,1));moved=0
    for o in objs:
        if o.get('grp') not in SETTLE or o.get('nosettle'):continue
        n=len(o.data.vertices);co=np.empty(n*3);o.data.vertices.foreach_get('co',co);co=co.reshape(n,3);p=Vector(co[co[:,2].argmin()])
        if p.z<=.002:continue
        if bvh:
            near=bvh.find_nearest(p)
            if near[0] is not None and near[3]<.003:continue   # already resting on something
            hu=bvh.ray_cast(p,up)
            if hu[0] is not None and hu[1].dot(up)>0 and o.get('grp') in ('Detail_Grass','Detail_Ferns'):continue   # a blade base inside a stone grows out of it (a tile or straw does not)
            hd=bvh.ray_cast(p,-up);tz=max(0.0,hd[0].z) if hd[0] is not None else 0.0
        else:tz=0.0
        co[:,2]-=p.z-tz+(.002 if tz>0 else 0);o.data.vertices.foreach_set('co',co.ravel());o.data.update();moved+=1
    print('SETTLE moved',moved)

def seat(objs,tol=.002,reach=.06,sink=.001,passes=2):
    """the detail pass (noise, chips, fold-safe pull-back) eats a few mm off surfaces that pieces rested on: stacked logs, a hub
    cap on its wheel, a footing stone on the ground, a hide on its peg, a straw pulled out of the stack. Every loose island that
    touches nothing within 2 mm but has the ground or another part within 6 cm is moved straight at that nearest point until it
    sinks 1 mm in (onto the ground: to z 0). Glow meshes (lamp flames, the lotus heart) are placed by hand and left alone."""
    from mathutils.bvhtree import BVHTree
    def isl(me):
        n=len(me.vertices);e=np.empty(len(me.edges)*2,int);me.edges.foreach_get('vertices',e);par=list(range(n))
        def f(i):
            while par[i]!=i:par[i]=par[par[i]];i=par[i]
            return i
        for x,y in e.reshape(-1,2):
            a,b=f(int(x)),f(int(y))
            if a!=b:par[a]=b
        return np.array([f(i) for i in range(n)])
    total=0
    for ps in range(passes):
        D=[]
        for o in objs:
            me=o.data;n=len(me.vertices);co=np.empty(n*3);me.vertices.foreach_get('co',co);co=co.reshape(n,3)
            polys=[list(p.vertices) for p in me.polygons];il=isl(me);fil=np.array([il[p[0]] for p in polys]) if polys else np.zeros(0,int)
            D.append(dict(o=o,co=co,polys=polys,il=il,fil=fil,bvh=BVHTree.FromPolygons([Vector(c) for c in co],polys) if polys else None,
                          lo=co.min(0) if n else np.zeros(3),hi=co.max(0) if n else np.zeros(3)))
        moved=0
        for d in D:
            if 'Glow' in d['o'].get('grp','') or d['bvh'] is None:continue
            roots=np.unique(d['il']);mv={}
            for r in roots:
                vi=np.nonzero(d['il']==r)[0];P=d['co'][vi];lo,hi=P.min(0),P.max(0)
                if lo[2]<=tol:continue
                near=[e for e in D if e is not d and e['bvh'] is not None and (e['lo']-reach<=hi).all() and (lo<=e['hi']+reach).all()]
                smp=P[::max(1,len(P)//300)];hit=False
                for e in near:
                    if any(e['bvh'].find_nearest(Vector(p),tol)[0] is not None for p in smp):hit=True;break
                if not hit and len(roots)>1:
                    hit=any(d['fil'][h[2]]!=r for p in smp for h in d['bvh'].find_nearest_range(Vector(p),tol))
                if hit:continue
                best=(lo[2],Vector((0,0,-lo[2])))   # the ground
                cand=[(e['bvh'],None) for e in near]
                if len(roots)>1:
                    rest=[q for q,fr in zip(d['polys'],d['fil']) if fr!=r]
                    if rest:cand.append((BVHTree.FromPolygons([Vector(c) for c in d['co']],rest),None))
                for b,_ in cand:
                    for p in smp:
                        h=b.find_nearest(Vector(p),min(best[0],reach))
                        if h[0] is not None and h[3]<best[0]:best=(h[3],(h[0]-Vector(p)))
                g,v=best
                if g>=reach or g<=tol:continue
                if v.length<1e-9:continue
                mv[r]=v.normalized()*(g+(0 if v.z<0 and abs(v.z+lo[2])<1e-9 else sink))
            if mv:
                co=d['co']
                for r,v in mv.items():co[d['il']==r]+=np.array(v[:])
                d['o'].data.vertices.foreach_set('co',co.ravel());d['o'].data.update();moved+=len(mv)
        print('SEAT pass',ps,'moved',moved);total+=moved
        if not moved:break
    return total

def run(pid):
    rid=REFID(pid);sel_txt=(REF/rid/'prompt.txt').read_text(encoding='utf-8')
    assert '選用：' in sel_txt and (REF/rid/f'{rid}_option1.png').stat().st_size>10000,f'{pid}: pick a saved AI three-view before modelling'
    bpy.ops.wm.read_factory_settings(use_empty=True);parts.clear();GLOW.clear()
    sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.render.engine='CYCLES';dev=gpu(sc);sc.cycles.samples=16;sc.render.bake.margin=12
    M=make_sources();meta=PROPS[pid](M);hd_pass(list(parts));RESOF=lambda g:max(1024,meta.get('res',{}).get(g,2048 if not g.startswith('Detail') else 1024))   # small atlases lose most of their area to island margins
    def sel(*obs):
        bpy.ops.object.select_all(action='DESELECT')
        for o in obs:o.select_set(True)
        bpy.context.view_layer.objects.active=obs[0]
    # ground line = source z 0: whatever is buried below it (half-buried stones, a sunk ash pit) is cut away there, so the exported
    # bottom (z 0) is the ground and grass/leaves/gravel laid at z 0 rest on it instead of hovering by the buried depth. The cut
    # is left open: those faces would sit under the terrain, and capping them makes neighbouring stones' beds coplanar at z 0.
    for o in parts:
        if min(v.co.z for v in o.data.vertices)<-1e-5:
            bm_=bmesh.new();bm_.from_mesh(o.data)
            bmesh.ops.bisect_plane(bm_,geom=bm_.verts[:]+bm_.edges[:]+bm_.faces[:],plane_co=(0,0,0),plane_no=(0,0,1),clear_inner=True,dist=.0004)
            bmesh.ops.dissolve_degenerate(bm_,edges=bm_.edges[:],dist=.0004)   # slivers where the cut grazes a vertex
            bmesh.ops.delete(bm_,geom=[v for v in bm_.verts if not v.link_faces],context='VERTS')
            bm_.to_mesh(o.data);bm_.free();o.data.update()
    parts[:]=[o for o in parts if len(o.data.polygons)]
    settle(parts);seat(parts)
    pts=np.array([(o.matrix_world@v.co)[:] for o in parts for v in o.data.vertices]);lo,hi=pts.min(0),pts.max(0)
    lim=LIMITS[pid];fit=min(1.0,*[lim[i]/max(1e-6,hi[i]-lo[i])*.985 for i in range(3)])
    if fit<1:   # noise, gravel and tufts pushed it past the size limit: scale the whole item (and its collision / pivots) to fit
        c0=Vector(((lo[0]+hi[0])/2,(lo[1]+hi[1])/2,lo[2]));S_=Matrix.Translation(c0)@Matrix.Scale(fit,4)@Matrix.Translation(-c0)
        for o in parts:o.data.transform(S_)
        for c in meta.get('collision',[]):
            c['center']=list(S_@Vector(c['center']))
            for k in ('size',):
                if k in c:c[k]=[v*fit for v in c[k]]
            for k in ('radius','height'):
                if k in c:c[k]*=fit
        meta['pivots']={g:list(S_@Vector(v)) for g,v in meta.get('pivots',{}).items()}
        meta['fit_scale']=round(fit,4);lo=np.array(S_@Vector(lo));hi=np.array(S_@Vector(hi))
    off=Vector((-(lo[0]+hi[0])/2,-(lo[1]+hi[1])/2,-lo[2]))
    for o in parts:o.data.transform(Matrix.Translation(off))
    meta['offset']=np.array(off[:])
    srcparts=list(parts);groups={}
    for o in srcparts:groups.setdefault(o['grp'],[]).append(o)
    G={}
    for g,objs in groups.items():
        cp=[]
        for o in objs:
            d=o.copy();d.data=o.data.copy();sc.collection.objects.link(d);cp.append(d)
            a_=d.data.attributes.get('uvkeep_f') or d.data.attributes.new('uvkeep_f','INT','FACE')
            a_.data.foreach_set('value',[1 if o.get('uvkeep') else 0]*len(d.data.polygons))
        sel(*cp);bpy.ops.object.join();o=bpy.context.object;o.name=o.data.name=f'{pid}_{g}_LOD0'
        bm=bmesh.new();bm.from_mesh(o.data)
        # sub-0.15 mm slivers (shell rims, ground cuts) would get zero-area bake UVs, and where three of them met an edge they left
        # non-manifold wedges with flipped winding: collapse them before and after triangulating, then drop any face still without area
        bmesh.ops.dissolve_degenerate(bm,edges=bm.edges[:],dist=1.5e-4)
        bmesh.ops.triangulate(bm,faces=bm.faces[:]);bmesh.ops.dissolve_degenerate(bm,edges=bm.edges[:],dist=1.5e-4)
        bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3])
        z_=[f for f in bm.faces if f.calc_area()<1e-10]
        if z_:bmesh.ops.delete(bm,geom=z_,context='FACES_ONLY')
        # a wedge facet under 1 mm2 folded onto a rim (same directed edge used twice) is dropped; the hole it leaves has no visible size
        from collections import defaultdict as _dd
        bm.verts.index_update();de=_dd(list)
        for f in bm.faces:
            for l in f.loops:de[(l.vert.index,l.link_loop_next.vert.index)].append(f)
        w_={min(fs,key=lambda f:f.calc_area()) for fs in de.values() if len(fs)>1}
        w_=[f for f in w_ if f.calc_area()<1e-6]
        if w_:bmesh.ops.delete(bm,geom=w_,context='FACES_ONLY')
        if True:   # the sliver collapse and the join can still leave a few pleats: relax them on the exported
            # triangles, within one connected piece only (flush faces of two separate pieces are a layout matter, not a pleat)
            bm.verts.index_update();bm.verts.ensure_lookup_table();par=list(range(len(bm.verts)))
            def fd_(i):
                while par[i]!=i:par[i]=par[par[i]];i=par[i]
                return i
            for e in bm.edges:
                x_,y_=fd_(e.verts[0].index),fd_(e.verts[1].index)
                if x_!=y_:par[x_]=y_
            il=[fd_(i) for i in range(len(bm.verts))];n0_=None
            for it_ in range(12):
                hit=self_overlaps(bm,isl=il)
                if n0_ is None:n0_=len(hit)
                if not hit:break
                vs={v for f in hit for v in f.verts};vs|={w for v in list(vs) for e in v.link_edges for w in e.verts}
                bmesh.ops.smooth_vert(bm,verts=list(vs),factor=.6,use_axis_x=True,use_axis_y=True,use_axis_z=True)
            print('GROUP_DEFOLD',pid,g,n0_,len(hit))
            # two separate pieces lying on each other with overlapping coplanar faces (a figure's hand on the mound, a block end on a
            # pillar face): the smaller piece's faces there are pushed 1.8 mm out along their normal so one surface clearly wins
            sz_={}
            for i_ in il:sz_[i_]=sz_.get(i_,0)+1
            cross=None;pushed=0
            for rd_ in range(8):   # a push can land a face on a third piece: repeat on what is left
                pf=set();bm.normal_update()
                for fa,fb in self_overlaps(bm,pairs=True):
                    ia,ib=il[fa.verts[0].index],il[fb.verts[0].index]
                    if ia!=ib:pf.add(fa if (sz_[ia],ia)<=(sz_[ib],ib) else fb)
                    else:pf.add(fa if fa.calc_area()<=fb.calc_area() else fb)   # a pleat the relax could not undo: lift its smaller face
                if cross is None:cross=pf
                if not pf:break
                mv={v for f in pf for v in f.verts};nr_={v:v.normal.copy() for v in mv}
                for v in mv:v.co+=nr_[v]*.0018   # past the 1 mm z-fight eps, inside the 2 mm contact tolerance
                pushed+=len(mv)
            print('GROUP_PUSH_LEFT',pid,g,len(pf))
            print('GROUP_PUSH',pid,g,len(cross),pushed)
        for rw_ in range(3):   # the relax and the push can fold a new sub-5 mm2 wedge onto a rim: drop those again
            bm.verts.index_update();de=_dd(list)
            for f in bm.faces:
                for l in f.loops:de[(l.vert.index,l.link_loop_next.vert.index)].append(f)
            w_=[f for f in {min(fs,key=lambda f:f.calc_area()) for fs in de.values() if len(fs)>1} if f.calc_area()<5e-6]
            if not w_:break
            bmesh.ops.delete(bm,geom=w_,context='FACES_ONLY')
        print('GROUP_WEDGE_LEFT',pid,g,len(w_))
        bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(o.data);bm.free()
        keep=any(x.get('uvkeep') for x in objs)
        for u in [u for u in o.data.uv_layers if u.name!='Tiled']:o.data.uv_layers.remove(u)
        bu=o.data.uv_layers.new(name='Bake');o.data.uv_layers.active=bu;sel(o)
        if keep:   # copy the continuous tiled UVs, then only pack them
            for d_,s_ in zip(bu.data,o.data.uv_layers['Tiled'].data):d_.uv=s_.uv
        res=RESOF(g);mg=6/res
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
        if not keep:bpy.ops.uv.smart_project(angle_limit=math.radians(55),island_margin=mg,area_weight=0,scale_to_bounds=False)
        else:
            bpy.ops.object.mode_set(mode='OBJECT');kv=[0]*len(o.data.polygons);o.data.attributes['uvkeep_f'].data.foreach_get('value',kv)
            for v_ in o.data.vertices:v_.select=False
            for e_ in o.data.edges:e_.select=False
            for p_,k_ in zip(o.data.polygons,kv):
                p_.select=not k_
                if not k_:
                    for vi in p_.vertices:o.data.vertices[vi].select=True
            bpy.ops.object.mode_set(mode='EDIT')
            if not all(kv):bpy.ops.uv.smart_project(angle_limit=math.radians(55),island_margin=mg,area_weight=0,scale_to_bounds=False)
            bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.pack_islands(margin=mg,rotate=True,shape_method='AABB' if keep else 'CONCAVE')   # comb-edged straw islands: exact shapes take ages
        bpy.ops.object.mode_set(mode='OBJECT');G[g]=o
    if os.environ.get('WA_GEOM'):   # geometry/UV check only: save the joined LOD0 groups, skip baking and export
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.environ['WA_GEOM'],f'{pid}_geom.blend'));print('WORLD_A_GEOM',pid);return
    for o in sc.objects:o.hide_render=o not in G.values()
    tex={}
    for g,o in G.items():
        RES=RESOF(g);mats=list(o.data.materials)
        def target(name,data=False):
            im=bpy.data.images.new(name,RES,RES,alpha=False,float_buffer=data)
            for m in mats:
                nt=m.node_tree;t=nt.nodes.get('BAKE_TARGET') or nt.nodes.new('ShaderNodeTexImage');t.name='BAKE_TARGET';t.image=im;nt.nodes.active=t
            return im
        def bake(name,type,data=False,**kw):
            im=target(name,data);sel(o);bpy.ops.object.bake(type=type,**kw);a=np.array(im.pixels[:],dtype=np.float32).reshape(RES,RES,4);bpy.data.images.remove(im);return a
        def emit(fn):
            saved=[]
            for m in mats:
                nt=m.node_tree;out=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL');old=out.inputs['Surface'].links[0].from_socket
                em=nt.nodes.new('ShaderNodeEmission');fn(nt,m,em);nt.links.new(em.outputs[0],out.inputs['Surface']);saved.append((nt,out,old,em))
            return saved
        def restore(s):
            for nt,out,old,em in s:nt.links.new(old,out.inputs['Surface']);nt.nodes.remove(em)
        alb=bake('alb','DIFFUSE',pass_filter={'COLOR'});sc.cycles.samples=96;ao=bake('ao','AO',True)[...,0];sc.cycles.samples=16
        rough=bake('rough','ROUGHNESS',True)[...,0];nrm=bake('nrm','NORMAL',True,normal_space='TANGENT');onrm=bake('onrm','NORMAL',True,normal_space='OBJECT')[...,:3]*2-1
        s=emit(lambda nt,m,em:em.inputs['Color'].__setattr__('default_value',(GLOW.get(m.name,(0,0))[0],)*3+(1,)));met=bake('met','EMIT',True)[...,0];restore(s)
        s=emit(lambda nt,m,em:em.inputs['Color'].__setattr__('default_value',(GLOW.get(m.name,(0,0))[1],)*3+(1,)));glow=bake('glow','EMIT',True)[...,0];restore(s)
        def edges(nt,m,em):
            gg=nt.nodes.new('ShaderNodeNewGeometry');nt.links.new(gg.outputs['Pointiness'],em.inputs['Color'])
        s=emit(edges);pt=bake('edge','EMIT',True)[...,0];restore(s);edge=np.clip((pt-.52)/.07,0,1);cav=np.clip((.485-pt)/.05,0,1)
        s=emit(lambda nt,m,em:nt.links.new(nt.nodes.new('ShaderNodeNewGeometry').outputs['Position'],em.inputs['Color']));pos=bake('pos','EMIT',True)[...,:3];restore(s)
        filled=np.abs(pos).sum(2)>1e-7;px,py,pz=pos[...,0],pos[...,1],pos[...,2];H=hi[2]-lo[2]
        # painterly finish: cool blue-violet shade in occlusion, warm light on top, worn warm edges
        cool=np.array([.30,.32,.46]);col=alb[...,:3]*(.42+.58*ao[...,None])+(1-ao[...,None])*cool*.12
        col=col*(1-.45*cav[...,None])+cav[...,None]*np.array([.10,.09,.07])*.45
        col=col*(1+.08*np.clip(pz/H,0,1)[...,None]*np.array([1.0,.85,.6]))
        wear=np.clip(edge,0,1)[...,None]*(met[...,None]<.1)*(glow[...,None]<.5);col=np.clip(col*(1+.35*wear)+wear*np.array([.06,.05,.03]),0,1)
        # soot inside lamp chambers
        for (cx,cy,cz,hw_,hh_) in meta.get('soot',[]):
            q=pos-meta['offset'];inside=filled&(np.abs(q[...,0]-cx)<hw_)&(np.abs(q[...,1]-cy)<hw_)&(np.abs(q[...,2]-cz)<hh_)
            k=np.clip((q[...,2]-cz+hh_*.2)/(hh_*1.2),0,1)*inside*(1-.6*(glow>.5))*(1-np.clip(np.abs(q[...,0])+np.abs(q[...,1])-hw_*1.6,0,1))
            col=col*(1-.75*k[...,None])+np.array([.05,.045,.04])*.75*k[...,None]
        # moss on up-facing joints near the ground (and on roof ridges / tile channels)
        mn=np.clip((onrm[...,2]-.35)/.5,0,1)
        n1=np.sin(px*7.3+np.sin(py*5.1+pz*2.3)*1.7)*np.sin(py*6.7+np.sin(pz*4.3+px*2.1)*1.9);n2=np.sin(px*23.1+np.sin(py*19.7)*1.3)*np.sin(pz*21.3+py*13.9)
        noise=np.clip(.5+.42*n1+.18*n2,0,1)
        amt=meta.get('moss',{}).get(g,MOSS.get(g.split('_')[0],0))
        if amt:
            low=np.clip(1-pz/.5,0,1)*meta.get('moss_low',0)
            highm=np.clip((pz-(meta.get('top',H)*.80))/(H*.25),0,1)*.6 if g in ('Stone','Roof') else 0
            ridge=(np.clip((pz-3.7)/.4,0,1)+np.clip((1-ao)*2-.6,0,1)*.5) if g=='Roof' else 0
            creep=np.clip(1-pz/.30,0,1)*meta.get('moss_low',0)*.9+cav*.5
            m=np.clip((mn*(low+highm+ridge+.15)+creep)*amt*2*np.clip((noise-.38)*3.5,0,1),0,1)*filled*(glow<.5)
            mcol=np.array([.27,.36,.13])*(1-m[...,None]*.0)+np.array([.10,.10,.04])*noise[...,None]
            for (cx,cy,cz,rr) in meta.get('nomoss',[]):   # keep the carved mark faint: dirt, not bright moss
                q=pos-meta['offset'];m=m*(1-(np.sqrt((q[...,0]-cx)**2+(q[...,1]-cy)**2+(q[...,2]-cz)**2)<rr)*np.clip(cav*3,0,1))
            col=col*(1-m[...,None])+mcol*m[...,None];rough=np.clip(rough+.15*m,0,1)
        la=meta.get('lichen',{}).get(g,0)
        if la:
            patch=vfbm3(px,py,pz,2.5,3,seed=3)                       # where growth clusters (tens of cm)
            spots=vfbm3(px,py,pz,28,3,seed=7)                         # lichen rosettes (a few cm), irregular
            grain=vfbm3(px,py,pz,90,2,seed=11)
            tint=vfbm3(px,py,pz,1.2,2,seed=5)[...,None]
            col=col*(np.array([.94,.96,1.01])*(1-tint)+np.array([1.05,1.0,.90])*tint)
            mosp=np.clip((patch-.47)*5,0,1)*np.clip((grain-.28)*3,0,1)*la*filled*(glow<.5)
            lich=np.clip((spots-.54)*9,0,1)*np.clip((patch-.30)*3,0,1)*np.clip((grain-.22)*4,0,1)*la*filled*(glow<.5)
            col=col*(1-mosp[...,None])+(np.array([.30,.37,.15])+np.array([.10,.09,.02])*noise[...,None])*mosp[...,None]
            col=col*(1-lich[...,None]*.85)+np.array([.66,.70,.58])*lich[...,None]*.85
            col=np.clip(col,0,1);rough=np.clip(rough+.12*mosp,0,1)
        # roof: a repaired corner with newer, cleaner tiles
        if g=='Roof' and meta.get('newtiles'):
            q=pos-meta['offset'];k=filled&(q[...,0]>1.98)&(q[...,0]<2.75)&(q[...,1]<-1.75)&(onrm[...,2]>.15)
            col=np.where(k[...,None],alb[...,:3]*.25*(.55+.45*ao[...,None])+np.array([.33,.42,.50])*(.45+.55*ao[...,None])*.75,col);rough=np.where(k,.55,rough)
        # soil and water stains low on everything that stands on the ground
        if meta.get('soil'):
            s_=np.clip((meta['soil']-pz)/meta['soil'],0,1)*filled*(met<.5);col=col*(1-.45*s_[...,None])+np.array([.26,.20,.14])*.45*s_[...,None]
        if meta.get('wet') and not g.startswith('Detail'):   # creek stones: darker, glossier wet band below the waterline (not the loose pebbles)
            w_=np.clip((meta['wet']-pz)/(meta['wet']*.35),0,1)*filled*(met<.5);col=col*(1-.38*w_[...,None])+np.array([.05,.07,.08])*.2*w_[...,None];rough=np.clip(rough-.35*w_,.15,1)
        if meta.get('worn_top'):   # stepping stones: the walkable top is polished pale by footsteps
            t_=np.clip((onrm[...,2]-.85)/.12,0,1)*np.clip((pz-H*.75)/(H*.2),0,1)*filled;col=np.clip(col*(1+.16*t_[...,None])+np.array([.03,.03,.02])*t_[...,None],0,1);rough=np.clip(rough-.15*t_,0,1)
        if g=='Vat':   # unglazed clay foot below a dripping glaze line, water stains under the rim
            q=pos-meta['offset'];vx,vy=meta['vat'];ang=np.arctan2(q[...,1]-vy,q[...,0]-vx);line=.24+.035*np.sin(ang*7)+.05*np.clip(np.sin(ang*13),0,1)**6
            outer=filled&(np.hypot(q[...,0]-vx,q[...,1]-vy)>.27)&(glow<.5)
            raw=outer&(q[...,2]<line);col=np.where(raw[...,None],np.array([.46,.30,.20])*(.75+.25*ao[...,None]),col);rough=np.where(raw,.92,rough)
            ln=.72-.22*np.clip(np.sin(ang*3.3+1)*np.sin(ang*1.7),0,1);st=outer&(q[...,2]>ln)&(q[...,2]<.735)&(np.sin(ang*9+np.sin(ang*4)*2.5)>.55);col=np.where(st[...,None],col*.86+np.array([.42,.40,.34])*.06,col)
        if g=='Hoe':
            q=pos-meta['offset'];b=np.array(meta['hoe_blade']);d=np.linalg.norm(q-b,axis=2);k=filled&(met>.1)&(d<.20)&(q[...,2]<.12)
            col=np.where(k[...,None],col*.4+np.array([.32,.25,.17])*.6,col);rough=np.where(k,.95,rough)
        def save(name,rgba,data=False):
            im=bpy.data.images.new(name,RES,RES,alpha=True)
            if data:im.colorspace_settings.name='Non-Color'
            im.pixels.foreach_set(np.ascontiguousarray(rgba,dtype=np.float32).ravel());im.filepath_raw=str(TEX/f'{name}.png');im.file_format='PNG';im.save();return im
        one=np.ones((RES,RES),np.float32);key=f'{pid}_{g}'
        T={'alb':save(f'{key}_Albedo',np.dstack([np.clip(col,0,1),one])),'nrm':save(f'{key}_Normal',nrm,True),
           'orm':save(f'{key}_ORM',np.dstack([ao,rough,met,one]),True)}
        save(f'{key}_MaskURP',np.dstack([met,ao,0*one,1-rough]),True)
        if glow.max()>.5:   # lamp paper / embers: emission colour = warm light through the paper albedo
            em=np.clip(alb[...,:3]*np.array([1.25,.95,.62])*(glow[...,None]>.5),0,1);T['emi']=save(f'{key}_Emission',np.dstack([em,one]))
        tex[g]=T
    # final materials, LODs, root, lamp driver
    root=bpy.data.objects.new(f'{pid}_GroundOrigin',None);sc.collection.objects.link(root)
    if meta.get('lamp'):root['glow_level']=0 if pid=='TY04' else 1
    lods=[]
    # LOD1 is the phone close-up (quality-tiers-v1 4.1): at most 100k tris per item, LOD2 25k, never above 50 % / 15 %; shared by
    # water-filling on sqrt(group tris) so ropes and small parts are not crushed into spikes (same rule as relod_world_a.py)
    n0={g:sum(len(p.vertices)-2 for p in o.data.polygons) for g,o in G.items()}
    def share(budget,cap):
        if sum(cap*v for v in n0.values())<=budget:return {k:cap*v for k,v in n0.items()}
        lo_,hi_=0.0,max(math.sqrt(v)*cap for v in n0.values())+1
        for _ in range(60):
            lam=(lo_+hi_)/2
            if sum(min(cap*v,lam*math.sqrt(v)) for v in n0.values())>budget:hi_=lam
            else:lo_=lam
        return {k:min(cap*v,lo_*math.sqrt(v)) for k,v in n0.items()}
    alloc={1:share(100_000,.5),2:share(25_000,.15)}
    for g,o in G.items():
        T=tex[g];fm=bpy.data.materials.new(f'{pid}_{g}');fm.use_nodes=True;nt=fm.node_tree;bs=nt.nodes['Principled BSDF']
        def tn(im):t=nt.nodes.new('ShaderNodeTexImage');t.image=im;return t
        nt.links.new(tn(T['alb']).outputs['Color'],bs.inputs['Base Color'])
        nmn=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tn(T['nrm']).outputs['Color'],nmn.inputs['Color']);nt.links.new(nmn.outputs['Normal'],bs.inputs['Normal'])
        sp=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tn(T['orm']).outputs['Color'],sp.inputs['Color']);nt.links.new(sp.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sp.outputs['Blue'],bs.inputs['Metallic'])
        if 'emi' in T:
            nt.links.new(tn(T['emi']).outputs['Color'],bs.inputs['Emission Color'])
            if pid in ('G01','TY04'):   # lamp state on the root: G01 0 = unlit / 1 = lit; TY04 glow_level 0..4
                fc=bs.inputs['Emission Strength'].driver_add('default_value');dr=fc.driver;dr.type='SCRIPTED';v=dr.variables.new();v.name='lv'
                v.targets[0].id=root;v.targets[0].data_path='["glow_level"]'
                dr.expression='1.2*lv' if pid=='G01' else '0.2333*lv+0.1167*lv*lv'
            else:bs.inputs['Emission Strength'].default_value=1.0
        group=[o]
        for L in (1,2):
            ratio=min(1.0,alloc[L][g]/max(1,n0[g]))
            d=o.copy();d.data=o.data.copy();sc.collection.objects.link(d);d.name=d.data.name=f'{pid}_{g}_LOD{L}'
            m=d.modifiers.new('d','DECIMATE');m.ratio=ratio;m.use_collapse_triangulate=True;sel(d);bpy.ops.object.modifier_apply(modifier='d');group.append(d)
        for d in group:
            uvs=d.data.uv_layers;uvs.remove(uvs['Tiled']);uvs['Bake'].name='UVMap';d.data.materials.clear();d.data.materials.append(fm);d.hide_render=not d.name.endswith('LOD0');d.parent=root
        if g.startswith('Detail_'):   # removable detail: Detail_<Name>_LOD0/1/2 (quality-tiers-v1 §4)
            for L,d in enumerate(group):d.name=d.data.name=f'{g}_LOD{L}'
        pv=meta.get('pivots',{}).get(g)
        if pv:   # moving part (cart wheel): origin on its axle so the engine can spin it
            P=Vector(pv)+Vector(meta['offset'])
            for d in group:d.data.transform(Matrix.Translation(-P));d.location=P
        lods.append(group)
    pts=np.array([(gr[0].location+v.co)[:] for gr in lods for v in gr[0].data.vertices]);lo,hi=pts.min(0),pts.max(0);dims=hi-lo   # pivoted parts (wheels) sit at their location
    col,prims=collision(pid,meta,dims)
    if col:col.parent=root
    if meta.get('light'):
        ls=bpy.data.objects.new(f'{pid}_LightSocket',None);sc.collection.objects.link(ls);ls.location=Vector(meta['light'])+Vector(meta['offset']);ls.parent=root
    lim=LIMITS[pid];fits=bool(all(dims[i]<=lim[i]+1e-6 for i in range(3)))
    src=bpy.data.collections.new(f'{pid}_SourceParts');sc.collection.children.link(src)
    for o in srcparts:
        for c in list(o.users_collection):c.objects.unlink(o)
        src.objects.link(o);o.hide_render=True;o.hide_set(True)
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE/f'{pid}.blend'),compress=True)
    if 'glow_level' in root:root['glow_level']=4 if pid=='TY04' else 1;bpy.context.view_layer.update()   # export carries the emissive texture at full strength
    extra=[o for o in sc.objects if o.name.endswith('LightSocket')]
    sel(root,*[d for gr in lods for d in gr],*([col] if col else []),*extra);bpy.ops.export_scene.fbx(filepath=str(OUT/f'{pid}.fbx'),use_selection=True,object_types={'MESH','EMPTY'},global_scale=1.0,apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_ALL',bake_space_transform=True,axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='FACE',
        use_tspace=False,add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE',embed_textures=False)
    tri=lambda o:sum(len(p.vertices)-2 for p in o.data.polygons)
    info={'id':pid,'device':dev,'dimensions_xyz_m':[round(float(x),3) for x in dims],'size_limit_m':lim,'fits_limit':fits,
          'groups':{g:{'material':f'{pid}_{g}','texture_px':RESOF(g),'triangles':[tri(d) for d in gr],'emission':'emi' in tex[g]} for g,gr in zip(G,lods)},
          'triangles_total':[sum(tri(gr[i]) for gr in lods) for i in range(3)],'source_parts':len(srcparts),
          'reference':f'art/references/{REFID(pid)}/prompt.txt','origin':'footprint centre, bottom z = 0, front = -Y (Blender) / +Z glTF',
          'textures':'per group: Albedo / Normal / MaskURP (R metal, G AO, A smoothness) / ORM (glTF) [+ Emission]','collision':{'mesh':f'{pid}_Collision','primitives':prims} if col else None,
          'minTier':TIER[pid],'detailObjects':sorted(g for g in G if g.startswith('Detail_')),
          'pivots':{g:[round(v+float(meta['offset'][i]),3) for i,v in enumerate(pv)] for g,pv in meta.get('pivots',{}).items()}}
    for k in ('crescent','states','pieces','walkable','note','fit_scale'):
        if k in meta:info[k]=meta[k]
    for v in info.get('pieces',{}).values():   # piece centres in the exported (recentred) frame, same as the collision
        if 'centre' in v:v['centre']=[round(v['centre'][i]+float(meta['offset'][i]),3) for i in range(2)]
    if meta.get('light'):info['light_socket']=[round(float(v),3) for v in Vector(meta['light'])+Vector(meta['offset'])]
    print('WORLD_A_DONE',json.dumps(info,ensure_ascii=False));return info
ids=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else list(PROPS)
infos=[run(i) for i in ids]
mf=OUT/'model_info.json';old=json.loads(mf.read_text(encoding='utf-8')) if mf.exists() else {}
old.update({i['id']:i for i in infos});mf.write_text(json.dumps(old,ensure_ascii=False,indent=1),encoding='utf-8')
