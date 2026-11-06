"""承天 · 基礎建模練習（C 包 modelling-basics-c）— Eli-0731, Blender 4.5.3 LTS.
BM01 舊木箱 ×3：BM01_01 0.5 m、BM01_02 0.8 m（綁麻繩）、BM01_03 1.1 m（正面換過一塊板）。
BM02 拴繩矮木樁 ×2：BM02_01 0.8 m、BM02_02 1.1 m。BM03 粗陶罐 ×3：BM03_01 矮胖 0.3 m、BM03_02 細長 0.5 m、BM03_03 大口 0.8 m。
BM04 山路塊石 ×4：BM04_01 1.5 m（附碰撞）、BM04_02 1.0 m、BM04_03 0.7 m、BM04_04 0.4 m。
BM05 石桌和石凳：BM05_01 圓石桌（高 0.75 m、桌面 Ø1 m）、BM05_02 鼓凳、BM05_03 方凳（高 0.45 m），都附碰撞。
BM07 舊石碑：BM07_01 1.1 × 0.5 × 2.3 m，碑面磨平、右半一長條被鑿掉，附碰撞。
BM06 舊石缸和花台：BM06_01／02 瓜稜石缸 0.8 m（02 有鐵扣補釘）、BM06_03 灌木花台、BM06_04 草花台 1.2 m，前後一塊雲紋浮雕，都附碰撞。
Each item is modelled only after its AI three-view candidates are saved and one is picked in art/references/<ID>/prompt.txt
(AGENTS.md order). Look: round 1 was semi-realistic (user's choice, 2026-11-02); the #67 review asked to return to the style
guide's fixed paragraph 5.2 + negative 5.3 and to match C07 (the old warm-dark joinery in the game), so round 2 keeps the sizes and
structure and repaints the wood: large soft colour patches, varied board widths and tones, local edge wear, no all-over noise.
Pipeline (as the day 3-4 package): named parts with tiled source materials, tagged into bake groups → each group joined, unique UV,
Cycles bake (diffuse colour, AO, roughness, tangent normal, object normal, metal, edge pointiness, position) → numpy finish
(cool AO shade, worn pale edges, moss and soil at the foot, knot holes) → one material per group with Albedo / Normal / MaskURP / ORM
→ LOD1 ≈ 50 %, LOD2 ≈ 15 % → collision box → .blend, FBX (all LODs + collision), GLB (LOD0).
Quality tiers (docs/standards/quality-tiers-v1.md §4): groups named Detail_* (nail heads, rope, grass at the foot) are separate
meshes <ID>_Detail_*_LOD<n> the standard tier switches off; model_info.json lists them under detailObjects with minTier.
Origin: footprint centre, bottom at z = 0, Blender -Y is the front. No ground plate.
blender -b --factory-startup -P build_basics.py -- BM01_01 [BM01_02 ...]
"""
import bpy,bmesh,json,math,sys,random
import mathutils.noise as mnoise
sys.path.insert(0,str(__import__('pathlib').Path(__file__).resolve().parent));import meshfix   # shared #69 clean-up (meshfix.py)
from pathlib import Path
from mathutils import Vector,Matrix
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];PKG='modelling-basics-c'
REF=ROOT/'art/references';TEX=ROOT/'art/textures'/PKG;OUT=ROOT/'art/exports'/PKG
for p in (TEX,OUT):p.mkdir(parents=True,exist_ok=True)

# ---------------- tiled source textures (1024², tileable, 0.5 m per tile) ----------------
R=1024;TILE=.5;rng=np.random.default_rng(2611)
def tile_noise(cx,cy):
    g=rng.random((cy,cx));x=np.linspace(0,cx,R,endpoint=False);y=np.linspace(0,cy,R,endpoint=False)
    xi=x.astype(int);yi=y.astype(int);fx=x-xi;fy=y-yi;fx=fx*fx*(3-2*fx);fy=fy*fy*(3-2*fy)
    a=g[np.ix_(yi%cy,xi%cx)];b=g[np.ix_(yi%cy,(xi+1)%cx)];c=g[np.ix_((yi+1)%cy,xi%cx)];d=g[np.ix_((yi+1)%cy,(xi+1)%cx)]
    fx=fx[None,:];fy=fy[:,None];return (a*(1-fx)+b*fx)*(1-fy)+(c*(1-fx)+d*fx)*fy
def fbm(c0,oct=4,aniso=1):
    """aniso > 1 stretches the noise along Y (the board length in the box projection)"""
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
GLOW={}
def board(dark,light,grey,bleach,crack_amt,seed_shift=0.):
    """old timber in the style guide's hand-painted look (5.2, round 2 after the #67 review): large soft colour gradients
    along the board, a handful of long darker grain strokes and a few pale ones, one or two knots, sun-greyed areas and a
    few open checks. No fine all-over stripes or noise in the colour: the fibre lives only in the normal map.
    Returns (albedo, height)."""
    knot=np.clip((fbm(3,2)-.78)*6,0,1)**1.5;warp=1.6*fbm(2,3,aniso=6)+.9*knot
    broad=fbm(3,3,aniso=8)   # big soft patches stretched along the board
    rings=.5+.5*np.sin(math.tau*(X*3+warp+seed_shift))
    dark_st=np.maximum(np.clip((fbm(24,2,aniso=8)-.70)*5,0,1),.7*np.clip((rings-.9)*8,0,1))   # thin brush strokes ~1 × 10 cm, not blobs (aniso ≤ c0/2, or the noise has one cell along the board and turns into full-length stripes)
    pale_st=np.clip((fbm(10,2,aniso=4)-.70)*4,0,1)*(1-dark_st)
    fib=fbm(128,2,aniso=64);cr=np.clip((fbm(24,2,aniso=30)-.80)*8,0,1)*crack_amt
    slash=np.clip((fbm(40,2,aniso=8)-.80)*9,0,1)*np.clip((fbm(3,2)-.35)*3,0,1)   # sparse lens-shaped dark slashes (painted checks), as on C07
    t=np.clip(.5+1.1*(broad-.5)+.10*(rings-.5)-.3*knot,0,1)
    col=lerp(dark,light,t);g=np.clip((fbm(2,2)-.45)*2.5,0,1)*bleach;col=col*(1-g[...,None])+np.asarray(grey)[None,None,:]*g[...,None]
    col=col*(1-.42*dark_st[...,None])*(1-.55*cr[...,None])*(1-.6*slash[...,None])*(1-.12*knot[...,None])+.10*pale_st[...,None]*np.asarray(light)[None,None,:]
    return col,.25*dark_st+.30*fib+1.4*cr+.8*slash+.25*broad+.4*knot
def log_wood():
    """long-weathered debarked log (C2): warm golden-brown, the surface split into fibrous ribbons by many thin dark checks
    of uneven length (iso-lines of noise stretched along the grain, gated so they start and stop), pale fibre tops,
    darker water streaks, a few sun-bleached grey patches. Returns (albedo, height); the checks are grooves."""
    checks=np.zeros((R,R));cr=random.Random(5150);band=np.arange(-6,7)
    for k in range(170):   # nearly straight splits along the grain, tapering at both ends, wrapping round the tile
        L=int(R*cr.choice((cr.uniform(.08,.25),cr.uniform(.25,.7))));y0=cr.randrange(R);x0=cr.uniform(0,R);w=cr.uniform(.7,2.2)*(1.4 if L>R*.3 else 1)
        a1,f1,a2,f2=cr.uniform(1,4),cr.uniform(1,3),cr.uniform(.3,1),cr.uniform(6,14);ys=np.arange(L);u=ys/L
        xs=x0+a1*np.sin(u*f1*math.pi+k)+a2*np.sin(u*f2*math.pi)+cr.uniform(-4,4)*u
        ww=w*np.clip(np.sin(u*math.pi)*1.6,.15,1)[:,None];xi=np.floor(xs).astype(int)[:,None]+band[None,:]
        v=np.clip(1-np.abs(xi-xs[:,None])/ww,0,1)*cr.uniform(.6,1);rows=((y0+ys)%R)[:,None].repeat(len(band),1)
        np.maximum.at(checks,(rows,xi%R),v)
    fib=fbm(160,2,aniso=60);fib=np.clip((fib-.5)*2.2+.5,0,1);streak=fbm(6,3,aniso=12);blot=fbm(10,3)
    t=np.clip(.5+.7*(streak-.5)+.6*(fib-.5)+.3*(blot-.5),0,1)
    col=lerp((.36,.24,.13),(.76,.57,.35),t)
    grey=np.clip((fbm(4,3)-.55)*3,0,1)*.45+np.clip((fbm(24,2)-.68)*5,0,1)*.35   # broad sun-greyed areas, small pale lichen blots
    col=col*(1-grey[...,None])+np.array([.66,.63,.55])[None,None,:]*grey[...,None]
    water=np.clip((fbm(9,2,aniso=10)-.6)*3,0,1)   # darker runs down the grain
    col=col*(1-.25*water[...,None])*(1-.85*checks[...,None])*(.86+.28*fib)[...,None]
    return col,-1.4*checks+.9*fib+.25*streak-.1*water
def make_sources():
    S={}
    # three board stocks (mid, dark, sun-greyed) and darker battens, after C07 the repair toolbox (old warm-dark joinery, albedo
    # mean #4c3724): sources sit a step lighter than that, the AO / grime finish brings them down. The renewed board is
    # fresher pine, paler and warmer, still not grey-white.
    S['crate']=(*board((.34,.22,.13),(.56,.38,.23),(.46,.40,.33),.30,1.0),1.6,.86,0,0)
    S['crate_b']=(*board((.26,.16,.09),(.43,.28,.17),(.38,.33,.28),.20,1.0,.4),1.6,.86,0,0)
    S['crate_c']=(*board((.40,.30,.21),(.60,.47,.34),(.55,.50,.44),.55,.8,.7),1.6,.88,0,0)
    S['batten']=(*board((.25,.15,.085),(.40,.26,.15),(.36,.31,.26),.20,.8,.3),1.6,.86,0,0)
    S['newboard']=(*board((.55,.40,.25),(.72,.56,.38),(.66,.60,.52),.15,.3,.6),1.4,.8,0,0)
    global rng
    main_rng,rng=rng,np.random.default_rng(2612)   # stocks for BM02 onward draw from their own generator: the crates keep #67's noise exactly, and changing one family's stock no longer shifts the others
    S['log']=(*log_wood(),2.4,.9,0,0)   # debarked round log (BM02)
    S['weed']=(lerp((.20,.32,.12),(.40,.52,.22),np.clip(.6*fbm(6,2)+.4*X,0,1)),fbm(20,2),1,.8,0,0)   # darker broad-leaf weeds, guide grass root end
    big=fbm(3,4);lich=np.clip((fbm(40,2)-.72)*5,0,1)   # guide rock swatch #8a8478 → #b8b0a0, a few lichen dots
    S['stone']=(lerp((.36,.34,.30),(.68,.65,.58),np.clip(big*1.1-.05+.15*fbm(16,2),0,1))*(1-.08*lich[...,None])+lich[...,None]*np.array([.05,.07,.02]),big+.5*fbm(24,2)+.4*lich,2.4,.88,0,0)
    gs=np.clip((fbm(180,1)-.62)*6,0,1);gl=np.clip((fbm(150,1)-.64)*6,0,1);mot=fbm(5,3)   # dark and pale grog, broad firing mottle
    ash=np.clip((fbm(7,3)-.5)*2.5,0,1)   # greyish firing and dust patches, so the body is not one even orange
    S['clay']=(lerp((.38,.28,.21),(.55,.42,.33),np.clip(.4+.6*(mot-.5)+.3*(fbm(30,2)-.5),0,1))*(1-.2*gs[...,None])*(1-.3*ash[...,None])+ash[...,None]*np.array([.52,.48,.43])*.3+gl[...,None]*np.array([.06,.05,.04]),
               .35*fbm(60,2)+.3*gs-.25*gl+.3*fbm(14,2),1.6,.92,0,0)
    gd=np.clip((fbm(200,1)-.6)*5,0,1);gw=np.clip((fbm(170,1)-.66)*6,0,1)   # dark and pale mineral grains
    S['rock']=(lerp((.36,.33,.29),(.66,.61,.53),np.clip(.5+.8*(fbm(5,4)-.5)+.3*(fbm(40,2)-.5),0,1))*(1-.16*gd[...,None])+gw[...,None]*np.array([.05,.045,.04])
               +np.clip((fbm(3,3)-.55)*2,0,1)[...,None]*np.array([.05,.02,-.01]),.5*fbm(90,2)+.4*fbm(24,3)+.3*gd-.2*gw,2.0,.86,0,0)   # a faint warm iron tint in patches
    gk=np.clip((fbm(220,1)-.58)*5,0,1);gp=np.clip((fbm(190,1)-.64)*6,0,1)
    wz=np.clip((fbm(3,4)-.45)*2.2,0,1)   # broad warm weathering
    S['granite']=(lerp((.40,.36,.31),(.66,.60,.51),np.clip(.5+.9*(fbm(4,4)-.5)+.25*(fbm(30,2)-.5),0,1))*(1-.14*gk[...,None])+gp[...,None]*np.array([.04,.035,.03])
                  +wz[...,None]*np.array([.05,.025,0])-np.clip((fbm(8,3,aniso=6)-.6)*2,0,1)[...,None]*np.array([.08,.08,.07]),
                  .4*fbm(120,2)+.3*fbm(24,3)+.3*gk-.2*gp,1.8,.82,0,0)
    S['soil']=(lerp((.17,.12,.08),(.32,.24,.16),np.clip(fbm(10,3)+.3*(fbm(60,2)-.5),0,1))+np.clip((fbm(90,1)-.7)*5,0,1)[...,None]*np.array([.12,.11,.09]),fbm(60,2)+.5*fbm(12,2),2.0,.95,0,0)
    S['leaf']=(lerp((.26,.40,.14),(.60,.66,.26),np.clip(.6*fbm(5,2)+.4*Y,0,1)),fbm(30,2),1,.6,0,0)   # sunlit yellow-green, guide foliage
    S['twig']=(lerp((.22,.16,.11),(.40,.31,.22),fbm(12,3)),fbm(40,2,aniso=8),1.5,.85,0,0)
    S['darkgranite']=(lerp((.25,.24,.22),(.45,.43,.39),np.clip(.5+.8*(fbm(4,4)-.5)+.25*(fbm(30,2)-.5),0,1))*(1-.18*gk[...,None])+gp[...,None]*np.array([.06,.06,.055]),
                      .4*fbm(120,2)+.3*fbm(24,3)+.3*gk-.2*gp,1.8,.8,0,0)
    S['needle']=(lerp((.36,.20,.10),(.58,.38,.20),fbm(8,2)),fbm(40,2),1,.85,0,0)   # dry pine needles, rust brown
    rng=main_rng
    S['iron']=(lerp((.13,.11,.10),(.36,.20,.11),np.clip((fbm(6,4)-.35)*1.8,0,1)),fbm(18,3),2.4,.8,.25,0)
    tw=.5+.5*np.sin(math.tau*((X+Y)*16));fib=fbm(30,2,aniso=6)
    S['hemp']=(lerp((.36,.29,.19),(.62,.51,.34),np.clip(tw*.55+.3*fbm(4,3)+.15*fib,0,1)),tw+.4*fib,1.4,.92,0,0)
    S['grass']=(lerp((.24,.42,.16),(.62,.76,.36),np.clip(.6*fbm(6,2)+.4*Y,0,1)),fbm(20,2),1,.85,0,0)   # guide grass #3e6a2a → #6fa443 → #b8d468
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
parts=[];uvr=random.Random(77)
def link(o,grp):bpy.context.scene.collection.objects.link(o);o['grp']=grp;parts.append(o);return o
def separate_coplanar(bm,lift=.001):
    """two separate pieces (weed strands, grass blades, stacked stones) with triangles lying in one plane z-fight:
    lift the smaller piece 1 mm along its own face normal. Same test as tools/art/qa_lod0_basic.py."""
    from mathutils.bvhtree import BVHTree
    bm.faces.ensure_lookup_table();bm.verts.ensure_lookup_table();bm.normal_update()
    isl=[-1]*len(bm.verts);n=0
    for v in bm.verts:   # connected pieces
        if isl[v.index]>=0:continue
        st=[v];isl[v.index]=n
        while st:
            w=st.pop()
            for e in w.link_edges:
                u=e.other_vert(w)
                if isl[u.index]<0:isl[u.index]=n;st.append(u)
        n+=1
    size=[0]*n
    for v in bm.verts:size[isl[v.index]]+=1
    tree=BVHTree.FromBMesh(bm,epsilon=.0005);moved=set()
    for i,j in tree.overlap(tree):
        if i>=j:continue
        a,b=bm.faces[i],bm.faces[j];ia,ib=isl[a.verts[0].index],isl[b.verts[0].index]
        if ia==ib or ia in moved or ib in moved or abs(a.normal.dot(b.normal))<math.cos(math.radians(1.5)):continue
        if max(abs((v.co-a.verts[0].co).dot(a.normal)) for v in b.verts)>.0005:continue
        u_=(a.verts[1].co-a.verts[0].co).normalized();w_=a.normal.cross(u_)
        P=[Vector((v.co.dot(u_),v.co.dot(w_))) for v in a.verts];Q=[Vector((v.co.dot(u_),v.co.dot(w_))) for v in b.verts];pen=1e9
        for poly in (P,Q):   # in-plane overlap deeper than 1 mm (separating axes), not just touching edges
            for t in range(3):
                e_=poly[(t+1)%3]-poly[t];ax=Vector((-e_.y,e_.x))
                if ax.length<1e-12:pen=0;break
                ax.normalize();pa=[p.dot(ax) for p in P];pb=[p.dot(ax) for p in Q];pen=min(pen,min(max(pa),max(pb))-max(min(pa),min(pb)))
        if pen<.001:continue
        f,k=(a,ia) if size[ia]<=size[ib] else (b,ib);d=f.normal*lift;moved.add(k)
        for v in bm.verts:
            if isl[v.index]==k:v.co+=d
    return len(moved)
def finish(name,bm,mat,grp,scale=TILE,keep_uv=False):
    """tiled UV: box projection on the part's principal axes, the long axis along V (the grain runs along the board);
    every part starts at a random place in the tile so neighbouring boards do not repeat the same grain.
    keep_uv: the caller already wrote the 'Tiled' layer (log posts: unrolled cylinder, grain along the length)"""
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces);lay=bm.loops.layers.uv.get('Tiled') or bm.loops.layers.uv.new('Tiled')
    pts=np.array([v.co[:] for v in bm.verts]);c=pts.mean(0);du,dv=uvr.random(),uvr.random()
    try:_,_,vt=np.linalg.svd(pts-c,full_matrices=False);A,S1,S2=[Vector(v) for v in vt]
    except Exception:A,S1,S2=Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))
    for f in ([] if keep_uv else bm.faces):
        n=f.normal;k=int(np.argmax([abs(n.dot(A)),abs(n.dot(S1)),abs(n.dot(S2))]))
        for l in f.loops:
            p=l.vert.co-Vector(c);u,v={0:(p.dot(S1),p.dot(S2)),1:(p.dot(S2),p.dot(A)),2:(p.dot(S1),p.dot(A))}[k];l[lay].uv=(u/scale+du,v/scale+dv)
    me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free();o=bpy.data.objects.new(name,me);me.materials.append(mat)
    return link(o,grp)
def tube(name,pts,r,mat,grp,sides=8,scale=.3,caps=True,up=None):
    """up: the first corner of every ring points this way (a 3-sided needle lying down, rolled so no face is flat against the stone)"""
    pts=[Vector(p) for p in pts];bm=bmesh.new();rings=[];prev=Vector(up) if up is not None else None
    for i,p in enumerate(pts):
        t=(pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]).normalized()
        u=(prev-t*prev.dot(t)).normalized() if prev is not None else t.orthogonal().normalized();prev=u;v=t.cross(u)
        rings.append([bm.verts.new(p+(u*math.cos(math.tau*k/sides)+v*math.sin(math.tau*k/sides))*r) for k in range(sides)])
    su=[0.]
    for a_,b_ in zip(pts,pts[1:]):su.append(su[-1]+(b_-a_).length)
    lay=bm.loops.layers.uv.new('Strip');flag=bm.faces.layers.int.new('strip');circ=math.tau*r;Lmax=max(10*circ,.05)
    for i,(a,b) in enumerate(zip(rings,rings[1:])):
        for k in range(sides):
            f=bm.faces.new((a[k],a[(k+1)%sides],b[(k+1)%sides],b[k]));f[flag]=1
            sg=int(su[i]/Lmax);u0=sg*Lmax   # long tubes are cut into pieces of at most ~10 circumferences so they pack
            for l,(uu,vv) in zip(f.loops,((su[i],k),(su[i],k+1),(su[i+1],k+1),(su[i+1],k))):l[lay].uv=(uu-u0,vv/sides*circ+sg*circ*1.5)
    if caps:   # caps keep the smart-project UV (folding them onto the strip's end ring gave zero-area UV faces in the #67 QA)
        for ring,rev in ((rings[0],True),(rings[-1],False)):bm.faces.new(list(reversed(ring)) if rev else ring)
    for f in bm.faces:f.smooth=True
    return finish(name,bm,mat,grp,scale)
def rope(name,pts,r,mat,grp,plies=3,sides=5,twist_pitch=None):
    """laid rope: `plies` strands twisted round the path (one turn per ~7 diameters)"""
    P=[Vector(p) for p in pts];L=sum((b-a).length for a,b in zip(P,P[1:]));turns=L/(twist_pitch or r*14);dense=[]
    for a,b in zip(P,P[1:]):
        n=max(2,int((b-a).length/(r*1.0)))
        for i in range(n):dense.append(a+(b-a)*(i/n))
    dense.append(P[-1]);res=[];prev=None;frames=[]
    for i,p in enumerate(dense):   # parallel-transported frame, so the strands do not flip at the corners
        t=(dense[min(i+1,len(dense)-1)]-dense[max(i-1,0)]).normalized()
        u=(prev-t*prev.dot(t)).normalized() if prev is not None else t.orthogonal().normalized();prev=u;frames.append((u,t.cross(u)))
    for k in range(plies):
        path=[];s=0
        for i,p in enumerate(dense):
            if i:s+=(p-dense[i-1]).length
            u,v=frames[i];ang=math.tau*k/plies+s/L*turns*math.tau;path.append(p+(u*math.cos(ang)+v*math.sin(ang))*r*.55)
        res.append(tube(f'{name}_ply{k+1}',path,r*.52,mat,grp,sides,.1))
    return res
def box_bm(size,center=(0,0,0)):
    bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
    for v in bm.verts:v.co=Vector([center[i]+v.co[i]*size[i] for i in range(3)])
    return bm
def apply(o,m):
    bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.modifier_apply(modifier=m.name);o.select_set(False)
def bevel(o,w,segs=2,angle=35):
    m=o.modifiers.new('wear','BEVEL');m.width=w;m.segments=segs;m.limit_method='ANGLE';m.angle_limit=math.radians(angle);m.use_clamp_overlap=True
    apply(o,m)
def subdiv(o,cuts):
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.subdivide_edges(bm,edges=bm.edges,cuts=cuts,use_grid_fill=True);bm.to_mesh(o.data);bm.free()
def jitter(o,amt,seed=1,freq=6):
    """displace along the normals of the undisplaced mesh (normals read first: Blender 4 recomputes them from the half-moved mesh)"""
    r=random.Random(seed);ph=[r.uniform(0,9) for _ in range(6)];me=o.data;me.update();n=len(me.vertices)
    co=np.empty(n*3);me.vertices.foreach_get('co',co);co=co.reshape(n,3);nr=np.empty(n*3);me.vertices.foreach_get('normal',nr);nr=nr.reshape(n,3)
    x,y,z=co[:,0],co[:,1],co[:,2]
    d=amt*(np.sin(x*freq+ph[0])*np.sin(y*freq*1.3+ph[1])+.6*np.sin(z*freq*.8+ph[2])*np.sin((x+y)*freq*2.1+ph[3]))
    me.vertices.foreach_set('co',(co+nr*d[:,None]).ravel());me.update()
def box(name,size,center,mat,grp,bev=.004,segs=2,cuts=0,jit=0,seed=1,rot=None):
    o=finish(name,box_bm(size),mat,grp)
    if cuts:subdiv(o,cuts)
    if bev:bevel(o,bev,segs)
    if jit:jitter(o,jit,seed,freq=4/max(size))
    if rot:o.data.transform(rot)
    o.data.transform(Matrix.Translation(center));return o
def join(objs,name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0];bpy.ops.object.join();o=bpy.context.object;o.name=name;return o
def leaf(name,base,direction,normal,L,W,mat,grp,curl=.25,seg=5):
    """grass blade: lens-shaped strip with a slight fold along the midrib"""
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
def tuft(name,base,M,grp,seed,n=9,h=.08,spread=(1,1)):
    r=random.Random(seed)
    for i in range(n):
        a=r.uniform(0,math.tau);lean=r.uniform(.15,.55);d=(math.cos(a)*lean*spread[0],math.sin(a)*lean*spread[1],1)
        leaf(f'{name}_{i}',Vector(base)+Vector((r.uniform(-.012,.012),r.uniform(-.006,.006),0)),d,(-math.sin(a),math.cos(a),0),h*r.uniform(.55,1.1),.008,M['grass'],grp,curl=.35,seg=5)
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
def round_loop(corners,rad,n=5,closed=True):
    """polyline through `corners` with each corner rounded by an arc of radius `rad` (rope going round a box edge)"""
    C=[Vector(c) for c in corners];out=[];m=len(C)
    for i in (range(m) if closed else range(1,m-1)):
        p,a,b=C[i],C[i-1],C[(i+1)%m];da=(a-p).normalized();db=(b-p).normalized();ang=math.acos(max(-1,min(1,da.dot(db))))
        if ang>math.pi-1e-3:out.append(p);continue
        d=rad/math.tan(ang/2);p0=p+da*d;p1=p+db*d;c=p+(da+db).normalized()*(rad/math.sin(ang/2))
        for k in range(n+1):
            t=k/n;q=(p0-c).lerp(p1-c,t).normalized()*rad;out.append(c+q)
    if closed:out.append(out[0])
    else:out=[C[0]]+out+[C[-1]]
    return out

# ---------------- BM01 old wooden crates ----------------
def crate(pid,M,W,D,H,rows,seed,t=.02,bw=.07,bt=.02,lid_n=3,replaced=(),knots=(),rope_tie=False,grass=()):
    """board crate: front/back boards run the full width between the side battens, side boards butt in between them,
    vertical battens on all four faces stand proud of the boards and of the lid by a few mm, lid boards across the width,
    a hidden bottom board. W × D × H are the outside sizes over the battens.
    replaced = [(face, row)] boards renewed in the middle span (paler, two nails each side on the old ends);
    knots = [(face, x, z, r)] knot holes painted into the finish; rope_tie: girth + vertical loop with a knot and a hanging bight"""
    r=random.Random(seed);emb=.003;W_=W-2*bt+2*emb;D_=D-2*bt+2*emb;Hw=H-t;gap=.0045;meta={'moss_low':.8,'moss_h':.10,'moss_top':.0,'moss_cav':.35,'soil':.07,'wear':0}
    nails=[]
    # board widths with a rhythm (#67 review: the even rows read as machine-cut slats): one wide, one narrow, the rest in between
    base=[1.35,.72,1.0,1.15,.85][:rows];r.shuffle(base);hs=[h*r.uniform(.95,1.05) for h in base];k=(Hw-(rows-1)*gap)/sum(hs);hs=[h*k for h in hs]
    zr=[];z=0
    for h in hs:zr.append((z,z+h));z+=h+gap
    ins=.03+.02*W;xb=W_/2-ins-bw/2;yb=D_/2-.025-bw/2   # batten centre lines on the long and short faces
    def tilt(ax):return Matrix.Rotation(r.uniform(-.006,.006),4,ax)
    last=[None]
    def stock():   # tone rhythm: mostly mid boards with dark and sun-greyed ones mixed in, rarely two of the same in a row
        k=r.choices(('crate','crate_b','crate_c'),(.45,.33,.22))[0]
        if k==last[0] and r.random()<.75:k=r.choices(('crate','crate_b','crate_c'),(.45,.33,.22))[0]
        last[0]=k;return M[k]
    for face,sy in (('Front',-1),('Back',1)):
        y=sy*(D_/2-t/2)
        for i,(z0,z1) in enumerate(zr):
            cz=(z0+z1)/2+r.uniform(-.002,.002);hh=z1-z0
            if (face,i) in replaced:   # old board ends stay under the battens; the renewed middle runs between two short cuts
                xa=xb-bw/2-.07*W;old=stock()   # both ends are what is left of one board
                for s in (-1,1):
                    box(f'{pid}_{face}Board{i}_old{s:+d}',(W_/2-xa,t,hh),(s*(xa+W_/2)/2,y,cz),old,'Wood',bev=.004,cuts=2,jit=.0012,seed=seed+i*7+s)
                    for dz in (-hh*.26,hh*.26):nails.append(((s*(xa+.025),y+sy*(t/2+.001),cz+dz),'y'))
                box(f'{pid}_{face}Board{i}_new',(2*xa-.006,t+.002,hh-.002),(0,y+sy*.001,cz),M['newboard'],'Wood',bev=.0022,cuts=3,jit=.0008,seed=seed+i*11)
                for s in (-1,1):
                    for dz in (-hh*.26,hh*.26):nails.append(((s*(xa-.03),y+sy*(t/2+.0035),cz+dz),'y'))   # the renewed board stands 2 mm proud: the nail sits 0.5 mm into it
            else:
                box(f'{pid}_{face}Board{i}',(W_,t,hh),(0,y,cz),stock(),'Wood',bev=.0065,cuts=3,jit=.0018,seed=seed+i*13+(sy>0),rot=tilt('Y'))
    for face,sx in (('Left',-1),('Right',1)):
        x=sx*(W_/2-t/2)
        for i,(z0,z1) in enumerate(zr):
            cz=(z0+z1)/2;hh=z1-z0
            if (face,i) in replaced:mat=M['newboard']
            else:mat=stock()
            box(f'{pid}_{face}Board{i}',(t,D_-2*t-.002,hh),(x,0,cz),mat,'Wood',bev=.0065,cuts=2,jit=.0015,seed=seed+i*17+(sx>0),rot=tilt('X'))
    # lid boards across the width, a hidden bottom board
    ws=[r.uniform(.9,1.1) for _ in range(lid_n)];k=(D_-(lid_n-1)*gap)/sum(ws);ws=[w*k for w in ws];y=-D_/2
    for i,w in enumerate(ws):
        box(f'{pid}_Lid{i}',(W_,w,t),(0,y+w/2,H-t/2-emb+r.uniform(-.0005,.0005)),stock(),'Wood',bev=.0065,cuts=3,jit=.0018,seed=seed+i*19,rot=tilt('X'))
        for s in (-1,1):nails.append(((s*(W_/2-t/2),y+w/2+r.uniform(-.01,.01),H-emb+.001),'z'))
        y+=w+gap
    box(f'{pid}_Bottom',(W_-2*t-.004,D_-2*t-.004,t),(0,0,t/2+.002),stock(),'Wood',bev=.003)
    # battens: proud of the boards (bt) and of the lid (+6 mm), one nail per board row; they sit emb deep in the boards they cover, so
    # their contact faces are not coplanar with the board faces (the #67 QA found z-fighting pairs there)
    top=H+.006
    for sy in (-1,1):
        for s in (-1,1):
            box(f'{pid}_Batten{"FB"[sy>0]}{s:+d}',(bw,bt,top),(s*xb,sy*(D_/2+bt/2-emb),top/2),M['batten'],'Wood',bev=.008,cuts=3,jit=.0018,seed=seed+s*3+sy*5,rot=tilt('Y'))
            for z0,z1 in zr:nails.append(((s*xb+r.uniform(-.006,.006),sy*(D_/2+bt-emb-.0003),(z0+z1)/2+r.uniform(-.008,.008)),'y'))
    for sx in (-1,1):
        for s in (-1,1):
            box(f'{pid}_Batten{"LR"[sx>0]}{s:+d}',(bt,bw*.85,top),(sx*(W_/2+bt/2-emb),s*yb,top/2),M['batten'],'Wood',bev=.008,cuts=3,jit=.0018,seed=seed+s*7+sx*9,rot=tilt('X'))
            for z0,z1 in zr:nails.append(((sx*(W_/2+bt-emb-.0003),s*yb+r.uniform(-.005,.005),(z0+z1)/2+r.uniform(-.008,.008)),'x'))
    # hand-forged nail heads: small square domes, a few bent or missing
    for i,(p,ax) in enumerate(nails):
        if r.random()<.07:continue
        sz=r.uniform(.009,.012);dims={'x':(.004,sz,sz),'y':(sz,.004,sz),'z':(sz,sz,.004)}[ax]
        box(f'{pid}_Nail{i}',dims,p,M['iron'],'Detail_Nails',bev=.0014,segs=1,rot=Matrix.Rotation(r.uniform(-.4,.4),4,{'x':'X','y':'Y','z':'Z'}[ax]))
    if rope_tie:
        rr=.0085;zg=H*.66;xv=W*.29;o=rr*1.1   # girth loop round the battens; vertical loop over the lid at x = +0.29 W
        g=[(-W/2-o,-D/2-o,zg),(W/2+o,-D/2-o,zg),(W/2+o,D/2+o,zg+.01),(-W/2-o,D/2+o,zg+.006)]
        rope(f'{pid}_RopeGirth',round_loop(g,.025),rr,M['hemp'],'Detail_Rope')
        v=[(xv,-D/2-o*2.2,.012),(xv,-D/2-o*2.2,H+o),(xv+.012,D/2+o,H+o),(xv+.012,D/2+o,.012)]
        rope(f'{pid}_RopeCross',round_loop(v,.03,closed=False),rr,M['hemp'],'Detail_Rope')
        # the knot where the two meet on the front: two tight turns, then a hanging bight and a short frayed tail
        c=Vector((xv,-D/2-o*3.3,zg));turns=[c+Vector((.019*math.cos(a),-.006*math.sin(a*2),.017*math.sin(a))) for a in np.linspace(0,math.tau*1.75,40)]
        rope(f'{pid}_Knot',turns,rr*.95,M['hemp'],'Detail_Rope')
        yb_=-D/2-o*3.6
        bight=[(xv+.012,yb_,zg-.015),(xv+.022,yb_-.004,zg-.09),(xv+.03,yb_-.006,zg-.17),(xv+.05,yb_-.004,zg-.2),(xv+.062,yb_,zg-.17),(xv+.056,yb_+.002,zg-.09),(xv+.03,yb_+.002,zg-.02)]
        rope(f'{pid}_Bight',bight,rr*.9,M['hemp'],'Detail_Rope')
        rope(f'{pid}_Tail',[(xv-.01,yb_,zg-.015),(xv-.016,yb_-.003,zg-.07),(xv-.012,yb_-.005,zg-.125)],rr*.9,M['hemp'],'Detail_Rope')
        for j in range(5):   # frayed end
            a=j/5*math.tau;tube(f'{pid}_Fray{j}',[(xv-.012,yb_-.005,zg-.122),(xv-.012+.008*math.cos(a),yb_-.005+.005*math.sin(a),zg-.15)],.0016,M['hemp'],'Detail_Rope',4,.1)
    for j,(x,y,n,h) in enumerate(grass):tuft(f'{pid}_Grass{j}',(x,y,0),M,'Detail_Grass',seed+j*31,n=n,h=h,spread=(1,.35))
    meta['knots']=list(knots);meta['zrows']=zr;meta['dims']=(W,D,H)
    meta['collisions']={'Collision':[{'type':'box','size':(W,D,H),'center':(0,0,H/2)}]}
    meta['notes']={'build':f'{rows} board rows per face, {lid_n} lid boards, battens proud of the boards by {bt} m and of the lid by 6 mm',
                   'detail':'Detail_Nails (nail heads), '+('Detail_Rope (girth and cross rope, knot, hanging bight), ' if rope_tie else '')+'Detail_Grass (tufts at the foot) are separate meshes; the standard tier hides them'}
    return meta
def BM01_01(M):return crate('BM01_01',M,.50,.34,.28,3,101,t=.018,bw=.055,bt=.016,lid_n=3,replaced=[('Back',1)],
                            grass=[(-.2,-.17,6,.06),(.21,.165,5,.05)])
def BM01_02(M):return crate('BM01_02',M,.80,.48,.38,4,202,t=.02,bw=.065,bt=.018,lid_n=4,knots=[('Back',-.05,.20,.013)],rope_tie=True,
                            grass=[(-.36,-.235,8,.07),(.30,-.235,5,.05),(.37,.23,6,.06)])
def BM01_03(M):return crate('BM01_03',M,1.10,.58,.52,4,303,t=.024,bw=.08,bt=.022,lid_n=4,replaced=[('Front',2)],
                            knots=[('Back',.02,.30,.016),('Left',.05,.18,.011)],grass=[(-.50,-.285,9,.09),(.42,-.285,6,.07),(-.47,.285,7,.08),(.5,.28,5,.06)])
# ---------------- BM02 rope-hitching posts ----------------
def angd(a,b):return (a-b+math.pi)%math.tau-math.pi
def stone(name,c,size,M,grp,seed):
    bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=2,radius=.5)
    for v in bm.verts:
        k=1+.18*math.sin(v.co.x*7+seed)*math.sin(v.co.y*6+seed*.7)+.1*math.sin(v.co.z*9+seed*1.3)
        v.co=Vector((v.co.x*size[0]*k,v.co.y*size[1]*k,max(v.co.z,-.18)*size[2]*k))+Vector(c)
    for f in bm.faces:f.smooth=True
    return finish(name,bm,M['stone'],grp,.3)
def log_post(pid,M,H,rx,ry,seed,rope_dir=0.,knot=None,stub=None,ncracks=10,stones=11,weeds=3,tufts=4):
    """weathered round log post: slightly oval and lumpy, a little flare at the soil, long open checks down the grain,
    a head above a groove worn by rope (deeper on the side the rope pulls, rope_dir), a rounded sawn top with radial
    checks, one knot scar, one branch stub; stones, weeds and grass tufts round the foot are Detail_ parts.
    knot = (angle, z, radius); stub = (angle, z)"""
    r=random.Random(seed);NS=128;zg=H-.15;ph=[r.uniform(0,6) for _ in range(8)]
    # long open checks plus a few short ones; widths in radians (≥ one of the 128 columns, or a check shades as a dashed line), depths in m
    cr=[(r.uniform(0,math.tau),r.uniform(.02,.3),r.uniform(H*.5,H+.01),r.uniform(.010,.02),r.uniform(.05,.075)) for _ in range(ncracks//2)]
    cr+=[(r.uniform(0,math.tau),z0,z0+r.uniform(.12,.3),r.uniform(.005,.01),r.uniform(.045,.06)) for z0 in [r.uniform(.05,H-.3) for _ in range(ncracks-ncracks//2)]]
    def ell(t):return rx*ry/math.sqrt((ry*math.cos(t))**2+(rx*math.sin(t))**2)
    def rad(z,t):
        e=ell(t);n=1+.04*math.sin(3*t+ph[0])*math.sin(z*3+ph[1])+.02*math.sin(5*t+ph[2]+z*2)+.01*math.sin(11*t+ph[3]+z*7)
        n+=(.006*math.sin(t*23+ph[6]+2.5*math.sin(z*2.3))+.004*math.sin(t*41+ph[7]+1.5*math.sin(z*3.1)))*(.5+.5*math.sin(t*7+z*4))   # uneven fibre ribbons along the grain
        flare=1+.05*max(0.,1-z/.12);head=1+.02*min(1.,max(0.,(z-zg-.015)/.02))
        # worn by rope: deep on the pulled side, almost nothing on the far side; the band wanders a little
        g=(.007+.014*max(0.,math.cos(t-rope_dir))**1.5*(.75+.5*math.sin(3*t+ph[4])))*math.exp(-((z-zg-.005*math.sin(2*t+ph[5]))/(.011+.004*math.sin(t+ph[7])))**2)
        c=sum(d*math.exp(-(angd(t,tc)/w)**2)*min(1.,(z-z0)/.08,(z1-z)/.08) for tc,z0,z1,d,w in cr if z0<z<z1)
        out=e*n*flare*head-g-c
        if knot:
            ka,kz,kr=knot;dd=math.hypot(e*angd(t,ka),z-kz)
            out+=.018*math.exp(-(dd/(1.7*kr))**2)+.008*min(1.,max(0.,(kr-dd)/.006))-.007*math.exp(-((dd-kr)/.006)**2)   # wood swelled round it, a flat face, a dark rim groove
        if stub:
            sa,sz=stub;dd=math.hypot(e*angd(t,sa),z-sz);out+=.022*math.exp(-(dd/.022)**2)
        rr=.02*(1+.5*math.sin(5*t+ph[1])*math.sin(3*t+ph[3]))   # rounded, unevenly chipped top edge
        if z>H-rr:out-=rr-math.sqrt(max(0.,rr*rr-(z-(H-rr))**2))
        return out
    zs=list(np.arange(0,H-.02,.008))+[H-.02,H-.014,H-.009,H-.005,H-.002,H]
    bm=bmesh.new();lay=bm.loops.layers.uv.new('Tiled');rings=[]
    for z in zs:rings.append([bm.verts.new((rad(z,math.tau*i/NS)*math.cos(math.tau*i/NS),rad(z,math.tau*i/NS)*math.sin(math.tau*i/NS),z)) for i in range(NS)])
    circ=max(1,round(math.tau*(rx+ry)/2/TILE))*TILE;du=r.random()   # a whole number of tiles round the log, so the grain meets itself at the UV seam
    for a,b,za,zb in zip(rings,rings[1:],zs,zs[1:]):
        for i in range(NS):
            j=(i+1)%NS;f=bm.faces.new((a[i],a[j],b[j],b[i]))
            for l,(uu,vv) in zip(f.loops,((i,za),(i+1,za),(i+1,zb),(i,zb))):l[lay].uv=(uu/NS*circ/TILE+du,vv/TILE)
    # sawn top: low dome with radial checks
    chk=[r.uniform(0,math.tau) for _ in range(3)];prev=rings[-1]
    for fr in (.86,.68,.5,.32,.15):
        ring=[]
        for i in range(NS):
            t=math.tau*i/NS;d=sum(.009*math.exp(-(angd(t,c)/.05)**2) for c in chk)*min(1.,fr/.3)
            rr_=rad(H,t)*fr;ring.append(bm.verts.new((rr_*math.cos(t),rr_*math.sin(t),H+.006*(1-fr*fr)-d)))
        for i in range(NS):
            j=(i+1)%NS;f=bm.faces.new((prev[i],prev[j],ring[j],ring[i]))
            for l in f.loops:l[lay].uv=(l.vert.co.x/TILE+.3,l.vert.co.y/TILE+.6)
        prev=ring
    cv=bm.verts.new((0,0,H+.006))
    for i in range(NS):
        f=bm.faces.new((prev[i],prev[(i+1)%NS],cv))
        for l in f.loops:l[lay].uv=(l.vert.co.x/TILE+.3,l.vert.co.y/TILE+.6)
    cb=bm.verts.new((0,0,0))
    for i in range(NS):   # hidden bottom cap, so the mesh is closed
        f=bm.faces.new((rings[0][(i+1)%NS],rings[0][i],cb))
        for l in f.loops:l[lay].uv=(l.vert.co.x/TILE,l.vert.co.y/TILE)
    for f in bm.faces:f.smooth=True
    finish(f'{pid}_Log',bm,M['log'],'Wood',keep_uv=True)
    # foot: half-sunk stones, a few weeds and grass tufts (Detail_)
    R0=max(rx,ry)
    for k in range(stones):
        a=math.tau*k/stones+r.uniform(-.25,.25);sz=r.uniform(.07,.11) if k%4==0 else r.uniform(.035,.07);d=R0+sz*.35+r.uniform(0,.04)
        stone(f'{pid}_Stone{k}',(d*math.cos(a),d*math.sin(a),sz*.04),(sz*r.uniform(1,1.35),sz,sz*r.uniform(.6,.8)),M,'Detail_Stones',seed+k)
    for k in range(weeds):
        a=r.uniform(0,math.tau);base=Vector(((R0+.02)*math.cos(a),(R0+.02)*math.sin(a),0))
        for j in range(6):   # a small rosette of broad leaves
            b=a+math.tau*j/6+r.uniform(-.3,.3);d=(math.cos(b)*.7,math.sin(b)*.7,1)
            leaf(f'{pid}_Weed{k}_{j}',base,d,(-math.sin(b),math.cos(b),0),r.uniform(.06,.11),.026,M['weed'],'Detail_Grass',curl=.3,seg=5)
    for k in range(tufts):
        a=r.uniform(0,math.tau);tuft(f'{pid}_Tuft{k}',((R0+.015)*math.cos(a),(R0+.015)*math.sin(a),0),M,'Detail_Grass',seed+40+k,n=7,h=r.uniform(.07,.12))
    meta={'moss_low':1.0,'moss_h':.32,'moss_top':.05,'moss_cav':.6,'soil':.06,'wear':.6,'post':{'H':H,'zg':zg,'knot':knot,'chk':chk}}
    meta['collisions']={}
    meta['notes']={'build':f'round log {2*rx:.2f} x {2*ry:.2f} m, rope groove {H-zg:.2f} m below the top (deeper towards the pull), {ncracks} long checks, knot scar, branch stub, rounded sawn top with radial checks',
                   'collision':'none: the work pack marks BM02 minTier high (a dressing prop the standard tier does not show), and the quality tiers keep collision the same on every tier, so it must not block the way',
                   'detail':'Detail_Stones (stones round the foot), Detail_Grass (weeds and tufts) are separate meshes; the standard tier hides them'}
    return meta
def BM02_01(M):return log_post('BM02_01',M,.80,.095,.08,401,rope_dir=-math.pi/2,knot=(math.pi*.85,.36,.045),stub=(math.pi*.05,.5))
def BM02_02(M):return log_post('BM02_02',M,1.10,.10,.088,402,rope_dir=-math.pi/2,knot=(-math.pi*.45,.58,.05),stub=(math.pi*.5,.72),ncracks=8,stones=13,weeds=4,tufts=5)
def post_paint(g,col,rough,q,onrm,ao,cav,edge,m,filled,glow,noise,RES,meta=None):
    """end grain on the sawn top (growth rings, dark pith, radial checks), the knot scar, the rope-polished groove"""
    if g=='Detail_Stones':   # each stone a little different: darker, browner or greyer, damp low down
        x,y,z=q[...,0],q[...,1],q[...,2];v=np.sin(x*37+np.sin(y*29)*2)*np.sin(y*41+x*13)
        col=col*(.8+.25*v[...,None])*np.array([1,.98,.95])+(v<-.3)[...,None]*np.array([.03,.02,0]);col=col*(1-.2*np.clip(.02-z,0,.02)[...,None]/.02)
        return np.clip(col,0,1),rough,{}
    if g!='Wood':return col,rough,{}
    P=meta['post'];H,zg=P['H'],P['zg'];x,y,z=q[...,0],q[...,1],q[...,2];rr=np.sqrt(x*x+y*y);t=np.arctan2(y,x)
    top=(onrm[...,2]>.6)&(z>H-.03)&filled
    rings=.5+.5*np.sin(rr*math.tau*150+np.sin(t*3)*2.5+np.sin(t*7+rr*40)*1.2);pith=np.clip(1-rr/.012,0,1)
    chk=np.zeros_like(rr)
    for c in P['chk']:chk=np.maximum(chk,np.clip(1-np.abs(np.angle(np.exp(1j*(t-c))))/.03,0,1)*np.clip(rr/.03,0,1))
    endg=np.array([.52,.44,.36])*(.88+.12*rings)[...,None]*(1-.4*pith[...,None])*(1-.6*chk[...,None])
    col=np.where(top[...,None],col*.35+endg*.65,col)
    side=(np.abs(onrm[...,2])<.6)&filled
    if P['knot']:
        ka,kz,kr=P['knot'];da=rr*np.angle(np.exp(1j*(t-ka)));dz=z-kz;dd=np.sqrt(da*da+dz*dz)/kr;phi=np.arctan2(dz,da)
        face=np.clip((1-dd)*8,0,1)*side;rim=np.exp(-((dd-1)/.12)**2)*side
        kring=.5+.5*np.sin(dd*math.tau*4.5+.6*np.sin(phi*3));krad=np.clip(1-np.abs(np.sin(phi*2.5+1))/.08,0,1)*np.clip(dd*2-.3,0,1)   # growth rings, two radial checks
        kcol=np.array([.46,.30,.17])*(.75+.25*kring)[...,None]*(1-.6*krad[...,None])*(1-.45*np.clip(1-dd/.25,0,1)[...,None])
        col=col*(1-face[...,None])+kcol*face[...,None];col=col*(1-.65*rim[...,None])
        bend=np.clip(1.6-dd/1.6,0,1)*(dd>1)*side*(.5+.5*np.sin(dd*math.tau*2.2))   # grain lines bending round the knot
        col=col*(1-.3*bend[...,None])
    # moss in streaks up the checks (C2): narrow bands round the log, thinning out with height
    mst=np.clip((np.sin(t*9+np.sin(z*5+t*3)*1.2)*.5+.5)*(np.sin(t*23+z*2)*.5+.5)-.3,0,1)*2.8*np.clip(1-z/(.45*H),0,1)**1.3*side
    mst*=np.clip((noise*.7+.3*np.sin(z*60+t*11)*.5+.15-.25)*3,0,1)
    mcol=np.array([.40,.46,.18])*(.8+.3*noise[...,None])
    col=col*(1-.8*mst[...,None])+mcol*.8*mst[...,None];rough=np.clip(rough+.1*mst,0,1)
    gv=np.exp(-((z-zg)/.014)**2)*filled*(np.abs(onrm[...,2])<.9);col=col*(1-.12*gv[...,None]);rough=np.clip(rough-.25*gv,0,1)   # rope-polished
    return col,rough,{}
def crate_paint(g,col,rough,q,onrm,ao,cav,edge,m,filled,glow,noise,RES,meta=None):
    """knot holes: a dark oval with a soft darker rim; grime streaks down from the lid joints"""
    if g!='Wood':return col,rough,{}
    W,D,H=meta['dims'];x,y,z=q[...,0],q[...,1],q[...,2]
    for face,kx,kz,kr in meta['knots']:
        if face in ('Front','Back'):sgn=-1 if face=='Front' else 1;on=(y*sgn>D/2-.06)&(np.abs(onrm[...,1]*sgn-1)<.4);u=x-kx
        else:sgn=-1 if face=='Left' else 1;on=(x*sgn>W/2-.06)&(np.abs(onrm[...,0]*sgn-1)<.4);u=y-kx
        d=np.sqrt((u/1.4)**2+(z-kz)**2)/kr;hole=np.clip((1-d)*3,0,1)*on;rim=np.clip((1.6-d)*2,0,1)*on*(1-hole)   # dark hole, a soft darker rim
        col=col*(1-.8*hole[...,None])*(1-.18*rim[...,None])+np.array([.05,.035,.025])*.8*hole[...,None];rough=np.clip(rough+.08*hole,0,1)
    # #67 review (style guide 5.2): large colour patches and local wear instead of even slats; nothing over the whole box
    def lf(f,o):   # smooth low-frequency field in object space (0..1), a few soft blobs per box
        return .5+.5*np.sin(x*f*1.3+o+np.sin(z*f*1.7+o*2)*1.4)*np.sin(z*f*1.1+y*f*.9+o*3+np.sin(x*f*.8)*1.2)
    side=(np.abs(onrm[...,2])<.4)&filled;top=(onrm[...,2]>.6)&filled
    # damp darkening from the foot, uneven along the box (C07's dark lower band)
    streaks=np.clip(.5+.5*np.sin(x*57+y*49+np.sin(x*11.3+y*9.7)*2.6)+.25*(lf(21,5.5)-.5),0,1)   # grime rising in vertical streaks
    damp=np.clip(1-z/(H*(.30+.25*streaks)),0,1)**1.2*(.55+.45*lf(9,1.7))*filled;col=col*(1-.38*damp[...,None])+np.array([.10,.07,.045])*.25*damp[...,None]
    # a few big darker and sun-greyed patches across neighbouring boards
    dk=np.clip((lf(6,4.1)-.62)*3.5,0,1)*side;col=col*(1-.22*dk[...,None])
    sun=np.clip((lf(5,.9)-.6)*3,0,1)*np.clip(z/H,0,1)*filled+.35*top*np.clip((lf(4,2.3)-.35)*2,0,1)
    grey=np.array([.47,.42,.36]);col=col*(1-.30*sun[...,None])+grey*.30*sun[...,None]
    # rain grime: irregular darker runs down from the lid joints, not a regular comb
    runs=np.clip((np.sin(x*23+np.sin(x*7.3+y*5.1)*3.1+y*19)*.5+.5-.55)*3,0,1)*np.clip((lf(13,6.2)-.35)*2.5,0,1)
    run=np.clip((z-(H-.16))/.14,0,1)*runs*side;col=col*(1-.20*run[...,None])
    # worn edges only where hands and knocks reach: the lid rim, the top of the battens, the corners; warm pale wood, not white
    reach=np.clip((z-H*.55)/(H*.45),0,1)*.8+np.clip((np.abs(x)-(W/2-.07))/.05,0,1)*.6+np.clip((np.abs(y)-(D/2-.06))/.05,0,1)*.4
    # every board edge carries a soft painted highlight (the hand-painted look of the v2 reference), the worn spots a stronger one
    hl=np.clip(edge*1.6,0,1)*filled*(.6+.4*lf(11,7.7));col=col*(1-.22*hl[...,None])+np.array([.60,.45,.30])*.22*hl[...,None]
    wear=np.clip(edge*2.0,0,1)*np.clip(reach,0,1)*np.clip((lf(17,3.3)-.25)*2.5,0,1)*filled
    col=col*(1-.7*wear[...,None])+np.array([.64,.49,.33])*.7*wear[...,None];rough=np.clip(rough-.10*wear,0,1)
    return col,rough,{}

# ---------------- BM03 clay storage jars ----------------
def catmull(pts,step):
    """Catmull-Rom through the (r, z) control points, resampled about every `step` m along the curve"""
    P=[np.array(p,float) for p in pts];P=[2*P[0]-P[1]]+P+[2*P[-1]-P[-2]];dense=[]
    for i in range(1,len(P)-2):
        p0,p1,p2,p3=P[i-1],P[i],P[i+1],P[i+2];n=max(2,int(np.linalg.norm(p2-p1)/step*1.3))
        for k in range(n):
            u=k/n;dense.append(.5*(2*p1+(-p0+p2)*u+(2*p0-5*p1+4*p2-p3)*u*u+(-p0+3*p1-3*p2+p3)*u**3))
    dense.append(P[-2]);d=np.array(dense);L=np.r_[0,np.cumsum(np.linalg.norm(np.diff(d,axis=0),axis=1))]
    m=max(3,int(L[-1]/step));t=np.linspace(0,L[-1],m)
    return np.c_[np.interp(t,L,d[:,0]),np.interp(t,L,d[:,1])]
def glaze_mask(t,z,G):
    """1 where the dark glaze covers the outside: above a wavering line, plus runs hanging below it with a bead at the end.
    Shared by the mesh (a slight glaze thickness) and the paint, so the raised runs and the painted ones match."""
    t=np.asarray(t,float);z=np.asarray(z,float);ph=G['ph']
    zb=G['z']+G['wave']*(np.sin(3*t+ph[0])*.6+np.sin(7*t+ph[1])*.4)
    low=zb.copy();bead=np.zeros_like(z)
    for ta,w,L in G['drips']:
        a=np.abs(np.angle(np.exp(1j*(t-ta))))/w;inside=np.clip(1-a*a,0,1)
        bot=zb-L*np.sqrt(inside);low=np.minimum(low,np.where(a<1,bot,zb))
        bead=np.maximum(bead,np.exp(-(a/.9)**2-((z-(zb-L+.004))/.008)**2)*(a<1.2))
    return np.clip((z-low)/.004+.5,0,1),bead
def shard(name,c,size,rot,M,grp,seed):
    """a broken piece of the rim lying on the ground: an irregular curved plate with thickness"""
    r=random.Random(seed);n=8;bm=bmesh.new();top=[];bot=[]
    for i in range(n):
        a=math.tau*i/n+r.uniform(-.25,.25);k=r.uniform(.6,1.1);x,y=math.cos(a)*size[0]*k,math.sin(a)*size[1]*k
        zc=-.35*(x*x)/max(size[0],1e-3)   # curved like the jar wall
        top.append(bm.verts.new((x,y,zc+size[2])));bot.append(bm.verts.new((x,y,zc)))
    bm.faces.new(top);bm.faces.new(list(reversed(bot)))
    for i in range(n):j=(i+1)%n;bm.faces.new((bot[i],bot[j],top[j],top[i]))
    M_=Matrix.Translation(Vector(c))@Matrix.Rotation(rot[2],4,'Z')@Matrix.Rotation(rot[0],4,'X')
    for v in bm.verts:v.co=M_@v.co
    return finish(name,bm,M['clay'],grp,.2)
def jar(pid,M,H,prof,wall,seed,glaze_z,ndrips,chips,shards,NS=96,step=.006):
    """thrown storage jar: one lathe profile (outer wall from the foot, a rolled lip, the inner wall down to a floor), a little
    out of round and leaning, gentle throwing undulations, glaze thickness and runs raised a hair; chipped rim (chips = (angle,
    width rad, depth m)); the broken-off pieces lie at the foot as Detail_Shards. prof = outer (r, z) control points, foot to rim."""
    r=random.Random(seed);ph=[r.uniform(0,6) for _ in range(8)]
    prof=list(prof[:-1])+[(prof[-1][0],prof[-1][1]-wall*.75)]   # the rolled lip rises wall*0.75 above the profile's end: the top lands at H
    out=catmull(prof,step);T=np.gradient(out,axis=0);T/=np.linalg.norm(T,axis=1)[:,None];N=np.c_[T[:,1],-T[:,0]]
    inn=(out-wall*N)[::-1];inn=inn[inn[:,1]>wall*1.2];inn=inn[::2]   # inner wall, coarser, down to the floor
    top_o,top_i=out[-1],inn[0];c=(top_o+top_i)/2;lip=[]
    for k in range(1,8):   # rolled lip, a little fuller than the wall
        a=math.pi*k/8;lip.append(c+np.array([math.cos(a)*wall*.62,math.sin(a)*wall*.75]))
    rf=prof[0][0]
    pro=[np.array((0.,0.)),np.array((rf-.012,0.)),np.array((rf-.004,.002))]+list(out)+lip+list(inn)+[np.array((inn[-1][0]*.5,wall)),np.array((0.,wall))]
    pro=np.array(pro);seg=np.r_[0,np.cumsum(np.linalg.norm(np.diff(pro,axis=0),axis=1))]
    nout=3+len(out)
    Rm=max(p[0] for p in prof);drips=[(r.uniform(0,math.tau),r.uniform(.004,.012)/Rm,r.choice((r.uniform(.01,.04),r.uniform(.04,.12)))*H/.5) for _ in range(ndrips)]
    G={'z':glaze_z,'wave':.02*H/.5,'ph':ph[4:7],'drips':drips,
       'streaks':[(r.uniform(0,math.tau),r.uniform(.006,.025)/Rm,r.uniform(glaze_z-.02,H*.92),r.uniform(.04,.25)*H/.5,r.choice((0,0,1,2))) for _ in range(int(ndrips*1.4))]}
    bm=bmesh.new();lay=bm.loops.layers.uv.new('Tiled');nu=max(1,round(math.tau*max(p[0] for p in prof)/TILE*1.5))
    rings=[];poles=[]
    for k,(rr0,z0) in enumerate(pro):
        if rr0<1e-6:poles.append(k);rings.append(bm.verts.new((0,0,z0)));continue
        ts=np.arange(NS)*math.tau/NS;rr=np.full(NS,rr0);z=np.full(NS,z0)
        f=z0/H;rr=rr*(1+.012*np.sin(ts+ph[0])*f+.006*np.sin(2*ts+ph[1]))+.0007*np.sin(z0*math.tau/.04+ph[2])*(k<nout)*(z0>.02)
        if 3<=k<nout:   # glaze thickness and its runs, on the outside only
            gm,bd=glaze_mask(ts,z,G);rr=rr+.0009*gm+.0022*bd
        for ca,cw,cd in chips:   # chipped rim: the lip and both walls cut down, unevenly
            a=np.abs(np.angle(np.exp(1j*(ts-ca))))/cw;depth=cd*np.clip(1-a**1.6,0,1)*(.8+.2*np.sin(ts*53+ca))
            # #69 review: clamping z to the cut line flattened several lip rings into one plane (same-facing coplanar faces at the
            # rim). The band from 2.5 x depth below the top is now pushed down smoothly instead: still lower by depth at the top,
            # but every ring keeps its order (slope 1/3 at least), so nothing folds or stacks.
            w=np.clip((z-(H-2.5*depth))/np.maximum(1.5*depth,1e-6),0,1);z=np.where(a<1,z-depth*w,z)
        x=rr*np.cos(ts)+.004*f*f;y=rr*np.sin(ts)
        rings.append([bm.verts.new((x[i],y[i],z[i])) for i in range(NS)])
    def uv(i,k):return (i/NS*nu+.13,seg[k]/TILE)
    for k in range(len(pro)-1):
        a,b=rings[k],rings[k+1]
        for i in range(NS):
            j=(i+1)%NS
            if k in poles:f=bm.faces.new((a,b[j],b[i]));ls=((i+.5,k),(i+1,k+1),(i,k+1))
            elif k+1 in poles:f=bm.faces.new((a[i],a[j],b));ls=((i,k),(i+1,k),(i+.5,k+1))
            else:f=bm.faces.new((a[i],a[j],b[j],b[i]));ls=((i,k),(i+1,k),(i+1,k+1),(i,k+1))
            for l,(ii,kk) in zip(f.loops,ls):l[lay].uv=uv(ii,kk)
    for f in bm.faces:f.smooth=True
    bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-5)
    finish(f'{pid}_Jar',bm,M['clay'],'Jar',keep_uv=True)
    R0=max(p[0] for p in prof)
    for k,(ca,sz) in enumerate(shards):
        d=R0*.9+sz*1.5+r.uniform(0,.03);a=ca+r.uniform(-.4,.4)
        shard(f'{pid}_Shard{k}',(d*math.cos(a),d*math.sin(a),.002),(sz,sz*.7,wall*.9),(r.uniform(-.15,.15),0,r.uniform(0,math.tau)),M,'Detail_Shards',seed+k)
    meta={'moss_low':.5,'moss_h':.07,'moss_top':0,'moss_cav':.2,'soil':.025,'wear':.7,'jar':{'H':H,'G':G,'chips':chips,'wall':wall}}
    meta['collisions']={}
    meta['notes']={'build':f'thrown jar {H:.2f} m tall, wall {wall*1000:.0f} mm, hollow to a floor, dark glaze from {glaze_z:.2f} m up with {ndrips} runs, {len(chips)} rim chip(s)',
                   'collision':'none: the work pack marks BM03 minTier high (a dressing prop the standard tier does not show), and the quality tiers keep collision the same on every tier, so it must not block the way',
                   'detail':'Detail_Shards (the broken-off rim pieces at the foot) are separate meshes; the standard tier hides them'}
    return meta
# outer profiles from C2 (width : height squat 1.26, slender 0.53, wide-mouth 0.66), heights from the work pack
def BM03_01(M):return jar('BM03_01',M,.30,[(.118,0),(.15,.03),(.185,.10),(.188,.13),(.17,.20),(.13,.25),(.095,.272),(.088,.285),(.096,.30)],.011,501,.115,22,
                          [(math.pi*.62,.16,.022)],[(math.pi*.62,.04)])
def BM03_02(M):return jar('BM03_02',M,.50,[(.078,0),(.088,.07),(.106,.20),(.126,.32),(.13,.36),(.12,.42),(.085,.465),(.064,.48),(.066,.49),(.076,.50)],.012,502,.29,26,
                          [(math.pi*.35,.14,.02),(-math.pi*.3,.09,.012)],[(math.pi*.35,.045),(-math.pi*.3,.03)])
def BM03_03(M):return jar('BM03_03',M,.80,[(.168,0),(.19,.08),(.235,.25),(.262,.44),(.262,.52),(.24,.62),(.20,.69),(.183,.725),(.19,.76),(.222,.79),(.235,.80)],.016,503,.48,34,
                          [(math.pi*.55,.22,.035),(-math.pi*.6,.12,.02)],[(math.pi*.55,.06),(math.pi*.45,.045),(-math.pi*.6,.04)],NS=112,step=.009)
# ---------------- BM04 mountain path stones ----------------
def vor3(P,seed):
    """3-D cellular noise: distances f1, f2 to the two nearest jittered feature points (P in cell units, any leading shape).
    f2 - f1 is small along cell borders: the fracture network, shared by the mesh grooves and the painted crack lines."""
    c=np.floor(P);f1=np.full(P.shape[:-1],9.);f2=f1.copy()
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            for dz in (-1,0,1):
                cc=c+np.array([dx,dy,dz]);j=[]
                for k in (np.array([127.1,311.7,74.7]),np.array([269.5,183.3,246.1]),np.array([113.5,271.9,124.6])):
                    h=np.sin(cc@k+seed)*43758.5453;j.append(h-np.floor(h))
                d=np.linalg.norm(P-(cc+np.stack(j,-1)*.8+.1),axis=-1)
                f2=np.where(d<f1,f1,np.minimum(f2,d));f1=np.minimum(f1,d)
    return f1,f2
def crack_space(P):
    """cells taller than wide, so the fractures run mostly up and down the faces, as in the reference"""
    return P*np.array([1.,1.,.5])
def crack_gate(P,seed):
    """which borders of the cell network are open fractures: about a third, in long runs"""
    x,y,z=P[...,0],P[...,1],P[...,2]
    return np.clip((np.sin(x*2.3+seed+np.sin(y*1.7+z*1.3)*1.5)*np.sin(y*2.1+z*.9+seed*.3)+.15)*3,0,1)
def hull_block(bm,centre,ax,planes,npts,g,r):
    """angular block: hull of a few points on an ellipsoid, clamped by planes, so it has big flat faces"""
    ax=np.asarray(ax);pl=[]
    for el,d in planes:
        a=r.uniform(0,math.tau);n=np.array([math.cos(a)*math.cos(el),math.sin(a)*math.cos(el),math.sin(el)]);pl.append((n,d))
    vs=[]
    for u in g.normal(size=(npts,3)):
        u/=np.linalg.norm(u);p=u*r.uniform(.9,1.05)
        for n,d in pl:
            h=p.dot(n)-d
            if h>0:p=p-n*h
        vs.append(bm.verts.new(p*ax+np.asarray(centre)))
    bmesh.ops.convex_hull(bm,input=vs)
def rock(pid,M,L,W,Hh,seed,blocks,cell=.4,crack=1.,tris=8000):
    """weathered block (C4 sheet): one or more angular hulls with big flat faces (blocks = [(centre, axes, n planes)]), merged by a
    voxel remesh and only lightly smoothed, so the edges round off but the faces stay flat (not a cube, not a bun); broad shallow
    dents, fracture grooves along a cellular network; cut flat at the soil line (half buried: the part below is not modelled),
    scaled to the work-pack size, decimated to the budget."""
    r=random.Random(seed);g=np.random.default_rng(seed);bm=bmesh.new()
    for c,ax,npl in blocks:
        planes=[(r.choice((r.uniform(-.15,.3),r.uniform(.6,1.3))),r.uniform(.55,.8)) for _ in range(npl)]
        hull_block(bm,c,ax,planes,r.randint(16,26),g,r)
    me=bpy.data.meshes.new('rk');bm.to_mesh(me);bm.free();o=bpy.data.objects.new('rk',me);bpy.context.scene.collection.objects.link(o)
    ext=np.ptp(np.array([v.co[:] for v in me.vertices]),axis=0);S_=float(max(ext[0],ext[1]))   # the hulls live in unit space; sizes below are relative
    m=o.modifiers.new('rm','REMESH');m.mode='VOXEL';m.voxel_size=S_/120;apply(o,m)
    m=o.modifiers.new('sm','SMOOTH');m.factor=.5;m.iterations=3;apply(o,m)
    me=o.data;me.update();n=len(me.vertices);co=np.empty(n*3);me.vertices.foreach_get('co',co);co=co.reshape(-1,3)
    nr=np.empty(n*3);me.vertices.foreach_get('normal',nr);nr=nr.reshape(-1,3)
    dent=np.array([mnoise.fractal(Vector(v/S_*2.2+seed*.37),1.,2.,3) for v in co])*.012*S_
    Pc=crack_space(co/(cell*S_));f1,f2=vor3(Pc,seed);gate=crack_gate(Pc,seed)
    groove=np.exp(-((f2-f1)/.07)**2)*gate*.009*S_*crack
    co=co+nr*(dent-groove)[:,None];me.vertices.foreach_set('co',co.ravel());me.update()
    bm=bmesh.new();bm.from_mesh(me);bpy.data.objects.remove(o);bpy.data.meshes.remove(me)
    res=bmesh.ops.bisect_plane(bm,geom=bm.verts[:]+bm.edges[:]+bm.faces[:],plane_co=(0,0,0),plane_no=(0,0,1),clear_inner=True)
    bmesh.ops.holes_fill(bm,edges=[e for e in res['geom_cut'] if isinstance(e,bmesh.types.BMEdge)],sides=0)
    pts=np.array([v.co[:] for v in bm.verts]);lo,hi=pts.min(0),pts.max(0);sc_=np.array([L,W,Hh])/(hi-lo);cx=(lo+hi)/2
    for v in bm.verts:v.co=Vector(((v.co.x-cx[0])*sc_[0],(v.co.y-cx[1])*sc_[1],v.co.z*sc_[2]))
    bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>4])
    for f in bm.faces:f.smooth=True
    me=bpy.data.meshes.new('rk2');bm.to_mesh(me);bm.free();o=bpy.data.objects.new('rk2',me);bpy.context.scene.collection.objects.link(o)
    nt=sum(len(p_.vertices)-2 for p_ in me.polygons)
    if nt>tris:m=o.modifiers.new('dc','DECIMATE');m.ratio=tris/nt;m.use_collapse_triangulate=True;apply(o,m)
    bm=bmesh.new();bm.from_mesh(o.data);bpy.data.objects.remove(o)
    # lichen rosettes: centres on open, upward faces (stored for the paint), mesh coordinates after scaling
    V=[(v.co.copy(),v.normal.copy()) for v in bm.verts];cand=[c for c,nn in V if nn.z>.25 and c.z>Hh*.25]
    lich=[(tuple(c),r.uniform(.012,.04)*(L/1.5)**.5) for c in r.sample(cand,min(len(cand),int(110*L+15)))]
    return finish(f'{pid}_Stone',bm,M['rock'],'Stone'),{'cell':cell*S_,'seed':seed,'sc':sc_.tolist(),'cx':cx.tolist(),'lich':lich}
def path_stone(pid,M,L,W,Hh,seed,tufts,collide=False,**kw):
    o,rk=rock(pid,M,L,W,Hh,seed,**kw);r=random.Random(seed+9)
    vs=[o.matrix_world@v.co for v in o.data.vertices if v.co.z<.02]
    for k,(a,n,h) in enumerate(tufts):   # grass tufts where the stone meets the soil
        p=max(vs,key=lambda v:math.cos(math.atan2(v.y,v.x)-a)*math.hypot(v.x,v.y))
        tuft(f'{pid}_Tuft{k}',(p.x*1.04,p.y*1.04,0),M,'Detail_Grass',seed+40+k,n=n,h=h)
    meta={'moss_low':.8,'moss_h':.12*Hh/.5+.04,'moss_top':.04,'moss_cav':.6,'soil':.05,'wear':.6,'rock':dict(rk,H=Hh)}
    pts=np.array([v.co[:] for v in o.data.vertices]);lo,hi=pts.min(0),pts.max(0)
    meta['collisions']={'Collision':'hull'} if collide else {}
    meta['notes']={'build':f'weathered block {L:.2f} x {W:.2f} m, {Hh:.2f} m above the soil; the buried part is not modelled (cut flat at the ground, hidden cap)',
                   'collision':'convex hull of the stone (simplified), the work pack asks for it on the largest stone only' if collide else 'none: the work pack puts _Collision on the largest stone only; the smaller ones are kerb dressing a player steps round',
                   'detail':'Detail_Grass (tufts at the base) is a separate mesh; the standard tier hides it'}
    return meta
def rock_paint(g,col,rough,q,onrm,ao,cav,edge,m,filled,glow,noise,RES,meta=None):
    """dark fracture lines along the same cellular network as the mesh grooves (plus finer ones), yellow-green lichen rosettes on the
    open upper faces, darker rain streaks down the sides, a damp darker foot"""
    if g!='Stone':return col,rough,{}
    R_=meta['rock'];H=R_['H'];x,y,z=q[...,0],q[...,1],q[...,2];sc_=np.array(R_['sc']);cx=np.array(R_['cx'])
    P0=np.stack([x/sc_[0]+cx[0],y/sc_[1]+cx[1],z/sc_[2]],-1)   # back to the unscaled space the grooves were cut in
    Pc=crack_space(P0/R_['cell']);f1,f2=vor3(Pc,R_['seed']);e1=f2-f1;g1=crack_gate(Pc,R_['seed'])
    f3,f4=vor3(Pc*2.7+7.3,R_['seed']+5);e2=f4-f3;g2=crack_gate(Pc*2.7+3.1,R_['seed']+2)
    w1=.02+.015*np.sin(Pc[...,2]*3+Pc[...,0]*2)   # the main fractures vary in width along their length
    cr=np.maximum(np.clip(1-e1/w1,0,1)*g1,np.clip(1-e2/.025,0,1)*g2*.6)*filled
    col=col*(1-.62*cr[...,None]);rough=np.clip(rough+.05*cr,0,1)
    lich=np.zeros_like(z)
    for c,rad in R_['lich']:   # rosettes with a lobed rim and a paler centre
        dx=x-c[0];dy=y-c[1];dz=z-c[2];d=np.sqrt(dx*dx+dy*dy+dz*dz)
        ang=np.arctan2(dz,dx+dy);lobe=rad*(1+.25*np.sin(ang*7+c[0]*31)+.15*np.sin(ang*13+c[1]*17))
        lich=np.maximum(lich,np.clip((lobe-d)/(rad*.25),0,1)*(.7+.3*np.clip(d/lobe,0,1)))
    clump=np.clip((np.sin(x*4.3+np.sin(y*3.1+z*2.7)*1.8)*np.sin(y*3.9+z*4.7+1)+.2)*2.5,0,1)   # lichen gathers in a few patches
    lich=lich*clump*filled*np.clip((onrm[...,2]+.2)/.5,0,1)*(1-cr)
    lc=np.array([.58,.55,.26])*(.75+.45*noise[...,None]);col=col*(1-.75*lich[...,None])+lc*.75*lich[...,None]
    side=np.clip(1-np.abs(onrm[...,2])/.6,0,1)*filled;st=np.clip(np.sin(x*23+y*29+np.sin(z*3)*.5)*.5+.5-.55,0,1)*2*side*np.clip((z-.05)/(H*.5),0,1)
    col=col*(1-.15*st[...,None]);dmp=np.clip(1-z/.12,0,1)*filled;col=col*(1-.15*dmp[...,None])
    return np.clip(col,0,1),rough,{}
# ---------------- BM05 stone table and stools ----------------
def prof_path(parts,step):
    """profile from pieces: ('L', points) straight runs (crisp mouldings), ('C', points) Catmull-Rom curves; resampled ~step"""
    out=[]
    for kind,pts in parts:
        if kind=='C':seg=catmull(pts,step)
        else:
            seg=[]
            for a,b in zip(pts,pts[1:]):
                n=max(1,int(math.dist(a,b)/step));seg+=[(a[0]+(b[0]-a[0])*i/n,a[1]+(b[1]-a[1])*i/n) for i in range(n)]
            seg.append(pts[-1]);seg=np.array(seg)
        for q in seg:
            if not out or math.dist(out[-1],q)>1e-4:out.append((float(q[0]),float(q[1])))
    return out
def lathe(name,pro,M,grp,seed,NS=96,disp=.003,chips=(),nu=2,tris=None):
    """solid of revolution from a profile that starts and ends on the axis; a little out of round, weathered by noise along
    the normals, chips cut out of the edges: chips = (angle, width rad, z0, z1, r cut)"""
    r=random.Random(seed);pro=np.array(pro);seg=np.r_[0,np.cumsum(np.linalg.norm(np.diff(pro,axis=0),axis=1))]
    T=np.gradient(pro,axis=0);T/=np.maximum(np.linalg.norm(T,axis=1),1e-9)[:,None];N=np.c_[T[:,1],-T[:,0]]
    bm=bmesh.new();lay=bm.loops.layers.uv.new('Tiled');rings=[];poles=[];ph=[r.uniform(0,6) for _ in range(4)]
    Rmax=pro[:,0].max()
    for k,(rr0,z0) in enumerate(pro):
        if rr0<1e-6:poles.append(k);rings.append(bm.verts.new((0,0,z0)));continue
        row=[]
        for i in range(NS):
            t=math.tau*i/NS;rr=rr0*(1+.006*math.sin(t+ph[0])+.004*math.sin(3*t+ph[1]));z=z0
            q=Vector((rr*math.cos(t),rr*math.sin(t),z))*4+Vector((seed,0,0))
            d=disp*(mnoise.fractal(q,1.,2.,3)+.4*mnoise.noise(q*5));rr+=d*N[k][0];z+=d*N[k][1]
            for ca,cw,_,ztop,cut in chips:   # broken arris: everything outside a slanting plane through the edge is gone
                a=abs(angd(t,ca))/cw
                if a<1:
                    f=cut*(1-a*a)*(.8+.2*math.sin(t*37+ca));n_=np.array([1.5,1.])/math.hypot(1.5,1);A=np.array([Rmax-f,ztop])
                    h=(np.array([rr,z])-A)@n_
                    if h>0:rr,z=np.array([rr,z])-n_*h
            row.append(bm.verts.new((rr*math.cos(t),rr*math.sin(t),z)))
        rings.append(row)
    for k in range(len(pro)-1):
        a,b=rings[k],rings[k+1]
        for i in range(NS):
            j=(i+1)%NS
            if k in poles:f=bm.faces.new((a,b[j],b[i]));ls=((i+.5,k),(i+1,k+1),(i,k+1))
            elif k+1 in poles:f=bm.faces.new((a[i],a[j],b));ls=((i,k),(i+1,k),(i+.5,k+1))
            else:f=bm.faces.new((a[i],a[j],b[j],b[i]));ls=((i,k),(i+1,k),(i+1,k+1),(i,k+1))
            flat=all(abs(N[kk][1])>.9 for _,kk in ls)   # seat / table top and the base: planar UV, no pinch at the pole
            for l,(ii,kk) in zip(f.loops,ls):l[lay].uv=(l.vert.co.x/TILE+.37,l.vert.co.y/TILE+.11) if flat else (ii/NS*nu+.21,seg[kk]/TILE)
    for f in bm.faces:f.smooth=True
    o=finish(name,bm,M['granite'],grp,keep_uv=True);nt=sum(len(p_.vertices)-2 for p_ in o.data.polygons)
    if tris and nt>tris:m=o.modifiers.new('dc','DECIMATE');m.ratio=tris/nt;m.use_collapse_triangulate=True;apply(o,m)   # flat runs need few rings
    return o
def stone_block(name,W,D,H,M,grp,seed,taper=.97,chip=None,tris=4500):
    """square stool: a slightly tapering block, voxel-remeshed and smoothed so the arrises are rounded by wear, noise-weathered;
    chip = (corner x sign, y sign, size) cut off the top corner on a slanting plane"""
    bm=box_bm((W,D,H),(0,0,H/2))
    for v in bm.verts:
        if v.co.z>H/2:v.co.x*=taper;v.co.y*=taper
    me=bpy.data.meshes.new('blk');bm.to_mesh(me);bm.free();o=bpy.data.objects.new('blk',me);bpy.context.scene.collection.objects.link(o)
    m=o.modifiers.new('rm','REMESH');m.mode='VOXEL';m.voxel_size=.006;apply(o,m);m=o.modifiers.new('sm','SMOOTH');m.factor=.5;m.iterations=6;apply(o,m)
    me=o.data;me.update();n=len(me.vertices);co=np.empty(n*3);me.vertices.foreach_get('co',co);co=co.reshape(-1,3);nr=np.empty(n*3);me.vertices.foreach_get('normal',nr);nr=nr.reshape(-1,3)
    d=np.array([mnoise.fractal(Vector(v*4+seed),1.,2.,3)*.003+mnoise.noise(Vector(v*20))*.001 for v in co]);co=co+nr*d[:,None]
    if chip:
        sx,sy,c=chip;nn=np.array([sx,sy,1.3]);nn/=np.linalg.norm(nn);p0=np.array([sx*W/2*taper,sy*D/2*taper,H])-nn*c
        h=(co-p0)@nn;co=np.where((h>0)[:,None],co-nn*h[:,None]*(1+.15*np.sin(co[:,0]*90)*np.sin(co[:,1]*80))[:,None],co)
    co[:,2]=np.maximum(co[:,2],0);me.vertices.foreach_set('co',co.ravel());me.update()
    nt=sum(len(p_.vertices)-2 for p_ in me.polygons)
    if nt>tris:m=o.modifiers.new('dc','DECIMATE');m.ratio=tris/nt;m.use_collapse_triangulate=True;apply(o,m)
    bm=bmesh.new();bm.from_mesh(o.data);bpy.data.objects.remove(o)
    for f in bm.faces:f.smooth=True
    return finish(name,bm,M['granite'],grp)
def garden_piece(pid,M,o,H,seed,tufts,cracks):
    """common: grass tufts at the foot (Detail_Grass), lichen centres low on the sides, crack polylines for the paint, hull collision"""
    r=random.Random(seed+9);vs=[o.matrix_world@v.co for v in o.data.vertices if v.co.z<.02]
    for k,(a,n,h) in enumerate(tufts):
        p=max(vs,key=lambda v:math.cos(math.atan2(v.y,v.x)-a)*math.hypot(v.x,v.y))
        tuft(f'{pid}_Tuft{k}',(p.x*1.03,p.y*1.03,0),M,'Detail_Grass',seed+40+k,n=n,h=h)
    side=[v.co.copy() for v in o.data.vertices if abs(v.normal.z)<.6 and v.co.z<H*.5]
    lich=[]
    for c in r.sample(side,min(len(side),9)):   # a few colonies, each a cluster of patches of mixed size, denser low down
        for _ in range(r.randint(4,9)):
            q_=r.choice(side);cc=c+(q_-c)*r.uniform(0,.12)
            if cc.z<H*.5:lich.append((tuple(cc),r.uniform(.006,.02)*(1.3-cc.z/H)))
    meta={'moss_low':1.0,'moss_h':.13,'moss_top':0,'moss_cav':.7,'soil':.03,'wear':.8,'garden':{'H':H,'lich':lich,'cracks':cracks}}
    meta['collisions']={'Collision':'hull'}
    return meta
def BM05_01(M):
    """round table: a 1 m slab on an hourglass pedestal with a moulded foot (C1)"""
    pro=prof_path([('L',[(0,0),(.25,0),(.255,.012),(.255,.055),(.245,.065),(.235,.075)]),
                   ('C',[(.235,.075),(.215,.12),(.185,.2),(.15,.32),(.135,.42),(.142,.5),(.17,.58),(.2,.635)]),
                   ('L',[(.2,.635),(.21,.645),(.47,.655),(.494,.665),(.5,.68),(.5,.73),(.494,.744),(.48,.75),(0,.75)])],.006)
    o=lathe('BM05_01_Table',pro,M,'Stone',701,NS=96,tris=12000,chips=[(-math.pi*.15,.16,0,.75,.05),(math.pi*.7,.08,0,.75,.025)])
    m=garden_piece('BM05_01',M,o,.75,701,[(-math.pi*.55,10,.1),(math.pi*.3,8,.09)],[(math.pi*.55,.08,.5,.01)])
    m['notes']={'build':'round table: slab Ø1.0 m x 0.095 m with rounded arris and two chips, hourglass pedestal on a moulded foot, height 0.75 m',
                'collision':'simplified convex hull: it blocks the way (the space under the slab is not walkable anyway)','detail':'Detail_Grass (tufts at the foot); the standard tier hides it'}
    return m
def BM05_02(M):
    """drum stool: a barrel of stone, slightly rounded rims, a worn dished seat"""
    pro=prof_path([('L',[(0,0),(.158,0),(.166,.01)]),('C',[(.166,.01),(.18,.08),(.19,.2),(.187,.3),(.176,.39),(.166,.43)]),
                   ('L',[(.166,.43),(.158,.443),(.14,.449),(.07,.447),(0,.446)])],.005)
    o=lathe('BM05_02_Drum',pro,M,'Stone',702,NS=80,tris=6000,chips=[(math.pi*.25,.13,0,.446,.022)])
    m=garden_piece('BM05_02',M,o,.45,702,[(math.pi*.8,7,.08)],[(-math.pi*.4,.05,.3,.012)])
    m['notes']={'build':'drum stool Ø0.38 m x 0.45 m, rounded rims, one chip on the seat edge','collision':'simplified convex hull','detail':'Detail_Grass (tufts at the foot)'}
    return m
def BM05_03(M):
    o=stone_block('BM05_03_Block',.37,.37,.45,M,'Stone',703,chip=(1,-1,.05))
    m=garden_piece('BM05_03',M,o,.45,703,[(-math.pi*.8,7,.08)],[(None,(-.12,-.186,.05),(.06,-.186,.32),.012)])
    m['notes']={'build':'square stool 0.37 x 0.37 x 0.45 m, a slight taper, worn rounded arrises, the front-right top corner broken off','collision':'simplified convex hull','detail':'Detail_Grass (tufts at the foot)'}
    return m
# ---------------- BM06 old stone basins and planters ----------------
def cloud_relief(u,v,W,spiral=True):
    """simple auspicious-cloud panel (no letters): three curled lobes with incised spirals and two trailing tails; u, v in metres
    from the panel centre, W the panel width. Returns raised height 0..1 (numpy, works on arrays)."""
    k=W/.5;h=np.zeros_like(u);g=np.zeros_like(u)
    for cu,cv,R,turn in ((-.12,.0,.055,1),(0,.02,.07,-1),(.12,0,.055,1)):
        cu*=k;cv*=k;R*=k;du=u-cu;dv=v-cv;d=np.sqrt(du*du+dv*dv);a=np.arctan2(dv,du)
        h=np.maximum(h,np.clip((R-d)/(.006*k),0,1))
        sp=np.abs(((d/R*2.6-turn*a/math.pi)%1)-.5)   # spiral groove: radius growing with the angle
        g=np.maximum(g,np.clip(1-sp/.11,0,1)*(d<R*.92)*(d>R*.12))
    for sgn in (-1,1):   # tails: tapering bands flowing out to each side
        x=(u*sgn-.17*k)/(.17*k);band=np.clip(1-np.abs(v+.035*k+.02*k*x*x)/(.018*k*(1-np.clip(x,0,1)*.8)),0,1)*(x>-.3)*(x<1)
        h=np.maximum(h,np.clip(band*3,0,1))
    return np.clip(h-.55*g*h*spiral,0,1)
def basin(pid,M,seed,clamp=False,chips=((0.,.12,0,.45,.03),)):
    """lobed (melon-ribbed) stone basin, 0.8 m wide: foot ring, bellied body with 8 lobes, thick rolled rim, hollow with water;
    a recessed panel with a cloud relief at the front and the back; chipped rim"""
    r=random.Random(seed);ph=[r.uniform(0,6) for _ in range(4)]
    out=prof_path([('L',[(0,0),(.33,0),(.336,.01),(.336,.045),(.322,.056)]),('C',[(.322,.056),(.35,.10),(.39,.2),(.398,.27),(.388,.34),(.372,.40),(.374,.418)]),
                   ('L',[(.374,.418),(.392,.428),(.4,.44),(.394,.449),(.38,.452),(.35,.452),(.344,.446)]),('C',[(.344,.446),(.345,.38),(.33,.25),(.27,.13),(.15,.095)]),('L',[(.15,.095),(0,.09)])],.004)
    pro=np.array(out);nout=next(i for i,(rr,zz) in enumerate(out) if zz>=.418);NS=288;Rmax=pro[:,0].max()
    bm=bmesh.new();lay=bm.loops.layers.uv.new('Tiled');rings=[];poles=[];seg=np.r_[0,np.cumsum(np.linalg.norm(np.diff(pro,axis=0),axis=1))]
    ts=np.arange(NS)*math.tau/NS
    for k,(rr0,z0) in enumerate(pro):
        if rr0<1e-6:poles.append(k);rings.append(bm.verts.new((0,0,z0)));continue
        rr=np.full(NS,rr0);z=np.full(NS,z0)
        if k<nout and .06<z0<.41:   # lobes, flattened into a panel at the front and back
            env=math.sin(math.pi*(z0-.06)/.35)**.7;pan=np.zeros(NS)
            for tc in (-math.pi/2,math.pi/2):
                a=np.abs(np.angle(np.exp(1j*(ts-tc))));pan=np.maximum(pan,np.clip((.5-a)/.08,0,1)*np.clip(min(z0-.15,.36-z0)/.02,0,1))
            rr=rr*(1+.045*np.cos(8*(ts-math.pi/16))*env*(1-pan))
            for tc in (-math.pi/2,math.pi/2):   # inside the panel: recessed field, raised cloud
                u=rr0*np.angle(np.exp(1j*(ts-tc)))*np.sign(math.cos(tc) or 1)*(-1 if tc>0 else 1);v=np.full(NS,z0-.255)
                inside=(np.abs(u)<.19)&(abs(z0-.255)<.085)
                rr=rr-.006*inside+.013*cloud_relief(u,v,.36,spiral=False)*inside   # the curved wall is too coarse for the incised spirals: plain lobes
        rr=rr*(1+.005*np.sin(ts+ph[0]))
        for ca,cw,_,ztop,cut in chips:
            a=np.abs(np.angle(np.exp(1j*(ts-ca))))/cw;f=cut*np.clip(1-a*a,0,1)*(.8+.2*np.sin(ts*37+ca));n_=np.array([1.5,1.])/math.hypot(1.5,1)
            h=(rr-(Rmax-f))*n_[0]+(z-ztop)*n_[1];cutm=(h>0)&(a<1);rr=np.where(cutm,rr-n_[0]*h,rr);z=np.where(cutm,z-n_[1]*h,z)
        rings.append([bm.verts.new((rr[i]*math.cos(ts[i]),rr[i]*math.sin(ts[i]),z[i])) for i in range(NS)])
    for k in range(len(pro)-1):
        a,b=rings[k],rings[k+1]
        for i in range(NS):
            j=(i+1)%NS
            if k in poles:f=bm.faces.new((a,b[j],b[i]));ls=((i+.5,k),(i+1,k+1),(i,k+1))
            elif k+1 in poles:f=bm.faces.new((a[i],a[j],b));ls=((i,k),(i+1,k),(i+.5,k+1))
            else:f=bm.faces.new((a[i],a[j],b[j],b[i]));ls=((i,k),(i+1,k),(i+1,k+1),(i,k+1))
            for l,(ii,kk) in zip(f.loops,ls):l[lay].uv=(ii/NS*5+.21,seg[kk]/TILE)
    for f in bm.faces:f.smooth=True
    sx=.4/max(max(abs(v.co.x),abs(v.co.y)) for v in bm.verts)
    for v in bm.verts:v.co.x*=sx;v.co.y*=sx   # the lobes bulge past the profile: bring the width back to 0.80 m
    o=finish(f'{pid}_Basin',bm,M['granite'],'Stone',keep_uv=True);nt=len(o.data.polygons)*2
    hi=o.copy();hi.data=o.data.copy();hi.name=f'{pid}_HiRes';bpy.context.scene.collection.objects.link(hi);hi.hide_render=True   # relief source for the normal bake
    m=o.modifiers.new('dc','DECIMATE');m.ratio=min(1,16000/nt);m.use_collapse_triangulate=True;apply(o,m)
    wb=bmesh.new();bmesh.ops.create_circle(wb,cap_ends=True,radius=.343,segments=64)   # water surface
    for v in wb.verts:v.co.z=.372
    finish(f'{pid}_Water',wb,M['granite'],'Water')
    if clamp:   # an old repair: two iron staples across a crack below the rim
        from mathutils.bvhtree import BVHTree
        sb_=bmesh.new();sb_.from_mesh(o.data);sb_.transform(o.matrix_world);tree=BVHTree.FromBMesh(sb_);sb_.free()
        for dt in (-.06,.06):
            t=math.pi*.15+dt;bb=box_bm((.012,.06,.008));me=bpy.data.meshes.new('st');bb.to_mesh(me);bb.free();ob=bpy.data.objects.new('st',me)
            u=Vector((math.cos(t),math.sin(t),0));hit=tree.ray_cast(u*.6+Vector((0,0,.39)),-u)[0]   # #69: on the lobe's surface (a fixed .385 m left it 12 mm off)
            rs=(hit.to_2d().length if hit else .385)+.006-.003   # half the staple's thickness out, 3 mm into the stone
            ob.matrix_world=Matrix.Translation((rs*math.cos(t),rs*math.sin(t),.39))@Matrix.Rotation(t,4,'Z');bpy.context.scene.collection.objects.link(ob);bpy.context.view_layer.update()
            bb=bmesh.new();bb.from_mesh(me);bb.transform(ob.matrix_world);bpy.data.objects.remove(ob);finish(f'{pid}_Staple{dt:+.2f}',bb,M['iron'],'Detail_Iron',.1)
    meta=garden_piece(pid,M,o,.45,seed,[(math.pi*.75,9,.1),(-math.pi*.2,7,.08)],[(math.pi*.15,.06,.38,.012)] if clamp else [(math.pi*1.2,.05,.3,.012)])
    meta['hires']={'Stone':hi};meta['garden']['waterline']=.37;meta['garden']['panels']=[('lathe',-math.pi/2),('lathe',math.pi/2)]
    meta['notes']={'build':'lobed basin 0.80 m wide, 0.45 m tall: foot ring, 8 lobes, rolled rim, hollow with a water surface; recessed panels with a cloud relief front and back; chipped rim'+(', two iron staples across a crack (Detail_Iron)' if clamp else ''),
                   'collision':'simplified convex hull of the stone','detail':'Detail_Grass (tufts at the foot)'+(', Detail_Iron (staples)' if clamp else '')}
    return meta
def shrub(pid,M,c,H,spread,seed,grp):
    """small leafy shrub: a few stems fanning out of the soil, twigs, clusters of leaves at the ends"""
    r=random.Random(seed);c=Vector(c);tips=[]
    for k in range(8):
        a=math.tau*k/8+r.uniform(-.3,.3);L=r.uniform(.6,1)*H;lean=r.uniform(.3,.7)
        c0=c+Vector((math.cos(a),math.sin(a),0))*.028   # #69: the stems rise from a small ring, not one point, so their bottom segments do not share faces
        pts=[c0+Vector((math.cos(a)*lean*spread*(i/5)**1.3*L/H,math.sin(a)*lean*spread*(i/5)**1.3*L/H,L*i/5)) for i in range(6)]
        tube(f'{pid}_Stem{k}',pts,.009,M['twig'],grp,sides=5,scale=.1);tips+=pts[3:]
        for b_ in range(2):   # side branches
            s0=pts[r.randint(2,3)];bb=a+r.choice((-1,1))*r.uniform(.5,1.1);bl=r.uniform(.12,.22)
            bp=[s0+Vector((math.cos(bb)*bl*i/3,math.sin(bb)*bl*i/3,bl*.6*i/3)) for i in range(4)];tube(f'{pid}_Br{k}_{b_}',bp,.005,M['twig'],grp,sides=4,scale=.1);tips+=bp[1:]
    for k in range(len(tips)):
        for j in range(r.randint(7,11)):   # leaf clusters round every branch end
            q=tips[k]+Vector((r.uniform(-.08,.08),r.uniform(-.08,.08),r.uniform(-.04,.07)))*.08   # #69 review: the leaf grows from the branch end (was up to 8 cm away, floating)
            b=r.uniform(0,math.tau);d=(math.cos(b)*.8,math.sin(b)*.8,r.uniform(.1,.6))
            leaf(f'{pid}_Leaf{k}_{j}',q,d,(-math.sin(b),math.cos(b),.3),r.uniform(.04,.065),.026,M['leaf'],grp,curl=.2,seg=2)
def planter(pid,M,seed,plant):
    """low stone planter 1.2 x 0.8 x 0.42 m: corner posts standing proud, wall slabs between them lifted off the ground (the corners
    are the feet), soil inside; a recessed panel with a cloud relief on both long faces; chipped corner; a shrub or grass (Detail_Plant)"""
    r=random.Random(seed);W,D,H=1.2,.8,.42;P=.13;T=.075;bm=bmesh.new()
    def add(size,c):
        b=box_bm(size,c);me=bpy.data.meshes.new('t');b.to_mesh(me);b.free();bm.from_mesh(me);bpy.data.meshes.remove(me)
    for sx in (-1,1):
        for sy in (-1,1):add((P,P,H),(sx*(W/2-P/2),sy*(D/2-P/2),H/2))
    for sy in (-1,1):add((W-2*P+.02,T,H-.06-.02),(0,sy*(D/2-T/2-.01),.06+(H-.08)/2))
    for sx in (-1,1):add((T,D-2*P+.02,H-.06-.02),(sx*(W/2-T/2-.01),0,.06+(H-.08)/2))
    add((W-2*P+.02,D-2*P+.02,.06),(0,0,.20))   # floor under the soil
    me=bpy.data.meshes.new('pl');bm.to_mesh(me);bm.free();o=bpy.data.objects.new('pl',me);bpy.context.scene.collection.objects.link(o)
    m=o.modifiers.new('rm','REMESH');m.mode='VOXEL';m.voxel_size=.0055;apply(o,m);m=o.modifiers.new('sm','SMOOTH');m.factor=.5;m.iterations=5;apply(o,m)
    me=o.data;me.update();n=len(me.vertices);co=np.empty(n*3);me.vertices.foreach_get('co',co);co=co.reshape(-1,3);nr=np.empty(n*3);me.vertices.foreach_get('normal',nr);nr=nr.reshape(-1,3)
    d=np.array([mnoise.fractal(Vector(v*3+seed),1.,2.,3)*.003+mnoise.noise(Vector(v*18))*.0012 for v in co])
    for sy in (-1,1):   # relief panels on the outer long faces
        on=(nr[:,1]*sy>.7)&(co[:,1]*sy>D/2-.02);u=co[:,0]*(-sy);v=co[:,2]-.24
        inside=on&(np.abs(u)<.36)&(np.abs(v)<.095);d+=(-.004+.008*cloud_relief(u,v,.62))*inside
    co=co+nr*d[:,None]
    nn=np.array([1,-1,1.3]);nn/=np.linalg.norm(nn);p0=np.array([W/2,-D/2,H])-nn*.05;h=(co-p0)@nn;co=np.where((h>0)[:,None],co-nn*h[:,None],co)   # broken corner
    co[:,2]=np.maximum(co[:,2],0);me.vertices.foreach_set('co',co.ravel());me.update()
    bm=bmesh.new();bm.from_mesh(o.data);bpy.data.objects.remove(o)
    for f in bm.faces:f.smooth=True
    o=finish(f'{pid}_Planter',bm,M['granite'],'Stone')
    hi=o.copy();hi.data=o.data.copy();hi.name=f'{pid}_HiRes';bpy.context.scene.collection.objects.link(hi);hi.hide_render=True   # relief source for the normal bake
    m=o.modifiers.new('dc','DECIMATE');m.ratio=min(1,14000/(len(o.data.polygons)*2));m.use_collapse_triangulate=True;apply(o,m)
    sb=bmesh.new();bmesh.ops.create_grid(sb,x_segments=24,y_segments=16,size=.5)
    for v in sb.verts:v.co.x*=(W-2*T-.02);v.co.y*=(D-2*T-.02);v.co.z=.37+.012*mnoise.noise(Vector((v.co.x*6,v.co.y*6,seed)))
    so=finish(f'{pid}_Soil',sb,M['soil'],'Stone',.5)
    from mathutils.bvhtree import BVHTree
    sb_=bmesh.new();sb_.from_mesh(so.data);sb_.transform(so.matrix_world);tree=BVHTree.FromBMesh(sb_);sb_.free()
    def soil(x,y):   # #69: plants stand in the soil surface (a flat .37 left grass up to 7 mm above it), 4 mm deep
        h=tree.ray_cast(Vector((x,y,.6)),Vector((0,0,-1)))[0];return (h.z if h else .37)-.004
    if plant=='shrub':shrub(pid,M,(-.05,.02,soil(-.05,.02)),.5,.75,seed,'Detail_Plant')
    else:
        for k in range(26):
            x_,y_=r.uniform(-.48,.48),r.uniform(-.26,.26);tuft(f'{pid}_Grass{k}',(x_,y_,soil(x_,y_)),M,'Detail_Plant',seed+100+k,n=9,h=r.uniform(.16,.32))
    meta=garden_piece(pid,M,o,H,seed,[(-math.pi*.4,8,.1),(math.pi*.6,7,.09)],[(None,(-.5,-.401,.05),(-.42,-.401,.3),.01)])
    meta['hires']={'Stone':hi};meta['garden']['waterline']=None;meta['collisions']={'Collision':'hull_stone'}
    meta['notes']={'build':f'planter {W} x {D} x {H} m: corner posts, wall slabs lifted off the ground between the corner feet, soil inside, cloud relief panels on both long faces, one corner broken; '+('a small shrub' if plant=='shrub' else 'grass')+' in Detail_Plant',
                   'collision':'simplified convex hull of the stone and soil (the plant is left out)','detail':'Detail_Plant (the shrub or grass), Detail_Grass (tufts at the foot); the standard tier shows an earth-filled planter'}
    return meta
def BM06_01(M):return basin('BM06_01',M,801)
def BM06_02(M):return basin('BM06_02',M,802,clamp=True,chips=((math.pi*.9,.1,0,.45,.028),(-math.pi*.15,.06,0,.45,.015)))
def BM06_03(M):return planter('BM06_03',M,803,'shrub')
def BM06_04(M):return planter('BM06_04',M,804,'grass')
# ---------------- BM07 old stele ----------------
def BM07_01(M):
    """standing stele on a low base (C1): a slab with a round-shouldered top, rough-hewn arrises, the faces worn smooth past reading;
    a long vertical strip right of centre chiselled away (recessed, rough, paler); pine needles and a few leaves on the base"""
    pid='BM07_01';r=random.Random(901);W,D,H=1.1,.5,2.3;bh=.3;sw,sd=.88,.3;rad=.3
    out=[]   # stele outline in x-z: straight sides, rounded shoulders
    for i in range(25):
        a=math.pi/2*i/24;out.append((sw/2-rad+rad*math.cos(a),H-rad+rad*math.sin(a)))
    for i in range(25):
        a=math.pi/2+math.pi/2*i/24;out.append((-(sw/2-rad)+rad*math.cos(a),H-rad+rad*math.sin(a)))
    out=[(sw/2,bh-.05)]+out+[(-sw/2,bh-.05)]
    bm=bmesh.new();fv=[bm.verts.new((x,-sd/2,z)) for x,z in out];f=bm.faces.new(fv)
    ext=bmesh.ops.extrude_face_region(bm,geom=[f]);bmesh.ops.translate(bm,vec=(0,sd,0),verts=[e for e in ext['geom'] if isinstance(e,bmesh.types.BMVert)])
    b=box_bm((W,D,bh),(0,0,bh/2));me=bpy.data.meshes.new('b');b.to_mesh(me);b.free();bm.from_mesh(me);bpy.data.meshes.remove(me)
    me=bpy.data.meshes.new('st');bm.to_mesh(me);bm.free();o=bpy.data.objects.new('st',me);bpy.context.scene.collection.objects.link(o)
    m=o.modifiers.new('rm','REMESH');m.mode='VOXEL';m.voxel_size=.0075;apply(o,m);m=o.modifiers.new('sm','SMOOTH');m.factor=.5;m.iterations=4;apply(o,m)
    me=o.data;me.update();n=len(me.vertices);co=np.empty(n*3);me.vertices.foreach_get('co',co);co=co.reshape(-1,3);nr=np.empty(n*3);me.vertices.foreach_get('normal',nr);nr=nr.reshape(-1,3)
    big=np.array([mnoise.fractal(Vector(v*2.2+9),1.,2.,4) for v in co]);fine=np.array([mnoise.noise(Vector(v*14)) for v in co])
    # rough-hewn arrises and sides, smoother broad faces
    flatface=(np.abs(nr[:,1])>.85)&(co[:,2]>bh+.02);d=np.where(flatface,.004*big+.0012*fine,.012*big+.004*fine)
    # the chiselled strip: right of centre on the front, recessed with ragged edges and pitted chisel marks
    sx0,sx1=.06,.30;edge=np.array([.028*mnoise.noise(Vector((v[0]*.5,v[2]*4,3)))+.01*mnoise.noise(Vector((0,v[2]*17,8))) for v in co])
    strip=(nr[:,1]<-.7)&(co[:,1]<-sd/2+.03)&(co[:,0]>sx0+edge)&(co[:,0]<sx1-edge)&(co[:,2]>bh+.06)&(co[:,2]<H-.18)
    chis=np.array([mnoise.noise(Vector((v[0]*45,v[2]*30,1)))+.5*mnoise.noise(Vector((v[0]*90,v[2]*70,5))) for v in co])
    d=d-strip*(.011+.004*chis)
    co=co+nr*d[:,None];co[:,2]=np.maximum(co[:,2],0);me.vertices.foreach_set('co',co.ravel());me.update()
    bm=bmesh.new();bm.from_mesh(me);bpy.data.objects.remove(o)
    for f in bm.faces:f.smooth=True
    o=finish(f'{pid}_Stele',bm,M['darkgranite'],'Stone')
    hi=o.copy();hi.data=o.data.copy();hi.name=f'{pid}_HiRes';bpy.context.scene.collection.objects.link(hi);hi.hide_render=True
    m=o.modifiers.new('dc','DECIMATE');m.ratio=min(1,12000/(len(o.data.polygons)*2));m.use_collapse_triangulate=True;apply(o,m)
    # litter on the base top: pine needles in drifts against the stele, a few dead leaves
    from mathutils.bvhtree import BVHTree
    sb_=bmesh.new();sb_.from_mesh(o.data);sb_.transform(o.matrix_world);tree=BVHTree.FromBMesh(sb_);sb_.free()
    def on_top(x,y,lift):   # #69: on the stone under it (needles were 2-8 mm up in the air, dead leaves 4 mm)
        h=tree.ray_cast(Vector((x,y,bh+.3)),Vector((0,0,-1)))[0];return (h.z if h else bh)+lift
    for k in range(260):
        side=r.choice((-1,1));x=r.uniform(-W/2+.05,W/2-.05);y=side*r.uniform(sd/2+.01,D/2-.02)*(1 if r.random()<.8 else r.uniform(.3,1))
        if abs(y)<sd/2 and abs(x)<sw/2:continue
        a=r.uniform(0,math.tau);L=r.uniform(.03,.055);c=Vector((x,y,bh+.002+r.uniform(0,.006)));c.z=on_top(x,y,.001)   # lowest edge on the stone
        tube(f'{pid}_Needle{k}',[c-Vector((math.cos(a),math.sin(a),0))*L/2,c+Vector((math.cos(a),math.sin(a),r.uniform(-.1,.1)))*L/2],.0012,M['needle'],'Detail_Litter',sides=3,scale=.05,caps=False,up=(-math.sin(a)*.5,math.cos(a)*.5,.866))   # rolled 30 degrees: no face flat on top or underneath
    for k in range(9):
        x=r.uniform(-W/2+.08,W/2-.08);y=r.choice((-1,1))*r.uniform(sd/2+.03,D/2-.04);b_=r.uniform(0,math.tau)
        leaf(f'{pid}_DeadLeaf{k}',Vector((x,y,on_top(x,y,-.0005))),(math.cos(b_),math.sin(b_),.3),(0,0,1),r.uniform(.05,.08),.035,M['needle'],'Detail_Litter',curl=-.1,seg=3)   # a dry leaf resting on its stalk end, tip curled up (lying flat it shared the stone's plane)
    side=[v.co.copy() for v in o.data.vertices if abs(v.normal.z)<.6]
    lich=[]
    for c in r.sample(side,12):
        for _ in range(r.randint(3,7)):
            q_=r.choice(side);cc=c+(q_-c)*r.uniform(0,.08);lich.append((tuple(cc),r.uniform(.012,.035)))
    meta={'moss_low':.55,'moss_h':.36,'moss_top':.15,'moss_cav':.6,'soil':.04,'wear':.5,'hires':{'Stone':hi},
          'stele':{'H':H,'bh':bh,'sd':sd,'strip':(sx0,sx1),'lich':lich}}
    meta['collisions']={'Collision':'hull_stone'}
    meta['notes']={'build':'stele 0.88 x 0.30 x 2.0 m with a round-shouldered top on a 1.1 x 0.5 x 0.3 m base; faces worn smooth (no letters), arrises rough-hewn; a chiselled strip right of centre on the front, recessed ~12 mm, its marks baked from the dense mesh',
                   'collision':'simplified convex hull of the stone','detail':'Detail_Litter (pine needles and dead leaves on the base); the standard tier hides it'}
    return meta
def stele_paint(g,col,rough,q,onrm,ao,cav,edge,m,filled,glow,noise,RES,meta=None):
    """paler fresh-cut strip, dark rain runs from the crown, lichen rosettes, a diagonal crack on the back"""
    if g!='Stone':return col,rough,{}
    S_=meta['stele'];x,y,z=q[...,0],q[...,1],q[...,2];H=S_['H'];sx0,sx1=S_['strip']
    st=filled*(onrm[...,1]<-.6)*(y<-S_['sd']/2+.03)*np.clip((x-sx0)/.02,0,1)*np.clip((sx1-x)/.02,0,1)*np.clip((z-S_['bh']-.06)/.03,0,1)*np.clip((H-.18-z)/.03,0,1)
    st=st*(.8+.2*noise)
    col=col*(1-.75*st[...,None])+np.array([.66,.62,.54])*(.85+.25*noise[...,None])*.75*st[...,None];rough=np.clip(rough+.08*st,0,1)
    runs=np.clip(np.sin(x*31+np.sin(z*2)*.6)*.5+.5-.55,0,1)*2.2*np.clip((z-S_['bh'])/(H-S_['bh']),0,1)*(np.abs(onrm[...,2])<.5)*(1-st)
    col=col*(1-.25*runs[...,None])
    a=np.array([-.35,S_['sd']/2+.001,.7]);b=np.array([.4,S_['sd']/2+.001,1.25]);P=np.stack([x,y,z],-1);ab=b-a;u=np.clip(((P-a)@ab)/(ab@ab),0,1)
    dd=np.linalg.norm(P-(a+u[...,None]*ab+np.stack([0*u,0*u,np.sin(u*37)*.008],-1)),axis=-1);cr=np.clip(1-dd/.0035,0,1)*(onrm[...,1]>.6)*filled
    col=col*(1-.6*cr[...,None])
    lich=np.zeros_like(z)
    for c,rad in S_['lich']:
        d=np.sqrt((x-c[0])**2+(y-c[1])**2+(z-c[2])**2);lich=np.maximum(lich,np.clip((rad-d)/(rad*.3),0,1))
    crown=filled*np.clip((z-(H-.32))/.1,0,1)*np.clip((onrm[...,2]+.1)/.4,0,1)*np.clip((noise*.7+.3*np.sin(x*37+z*29)-.35)*4,0,1)   # moss cap on the crown
    col=col*(1-.85*crown[...,None])+np.array([.30,.36,.14])*(.8+.4*noise[...,None])*.85*crown[...,None];rough=np.clip(rough+.1*crown,0,1)
    lich=lich*filled*np.clip((noise-.15)*3,0,1)*(1-st)
    col=col*(1-.7*lich[...,None])+np.array([.62,.64,.52])*.7*lich[...,None]
    return np.clip(col,0,1),rough,{}
def garden_paint(g,col,rough,q,onrm,ao,cav,edge,m,filled,glow,noise,RES,meta=None):
    """a hand-polished, paler seat / table top; one or two thin cracks; pale grey-green lichen rosettes low on the sides; damp foot"""
    if g=='Water':   # still dark water with a few floating leaves
        x,y=q[...,0],q[...,1];lv=np.clip((np.sin(x*61+np.sin(y*37)*2)*np.sin(y*57+x*13)-.75)*8,0,1)
        col=np.array([.07,.09,.06])*(1+.3*noise[...,None])*(1-lv[...,None])+np.array([.35,.42,.15])*lv[...,None];return col,.06+.6*lv,{'flat':filled*1.}
    if g!='Stone':return col,rough,{}
    G_=meta['garden'];H=G_['H'];x,y,z=q[...,0],q[...,1],q[...,2];t=np.arctan2(y,x)
    if G_.get('waterline'):   # tide marks on the inside and overflow stains down the outside
        wl=G_['waterline'];rad=np.sqrt(x*x+y*y);inner=(onrm[...,0]*x+onrm[...,1]*y)<0
        mark=sum(np.exp(-((z-(wl+dz))/.0035)**2)*a_ for dz,a_ in ((.012,.5),(.028,.35),(.05,.25)))*inner
        runs=np.clip(np.sin(t*13+np.sin(z*20)*.4)*.5+.5-.6,0,1)*2.5*(~inner)*np.clip((z-.1)/.3,0,1)
        col=col*(1-.35*np.clip(mark,0,1)[...,None])*(1-.22*runs[...,None])
    top=np.clip((onrm[...,2]-.75)/.2,0,1)*np.clip((z-H*.8)/(H*.1),0,1)*filled
    col=col*(1+.10*top[...,None])+np.array([.02,.015,.01])*top[...,None];rough=np.clip(rough-.18*top,0,1)
    cr=np.zeros_like(z)
    for c in G_['cracks']:
        if c[0] is None:   # a straight-ish crack between two points on a flat face
            _,a,b,w=c;a=np.array(a);b=np.array(b);P=np.stack([x,y,z],-1);ab=b-a;u=np.clip(((P-a)@ab)/(ab@ab),0,1)
            dd=np.linalg.norm(P-(a+u[...,None]*ab+np.stack([np.sin(u*40)*.004,0*u,np.sin(u*23)*.006],-1)),axis=-1)
            cr=np.maximum(cr,np.clip(1-dd/(w*.25),0,1)*np.clip(np.sin(u*math.pi)*3,0,1))
        else:   # a crack running up the round body from the foot
            ta,w,z1,_=c;rr=np.sqrt(x*x+y*y);da=rr*np.angle(np.exp(1j*(t-ta-.08*np.sin(z*30))))
            cr=np.maximum(cr,np.clip(1-np.abs(da)/.0025,0,1)*(z<z1)*np.clip((z1-z)/.05,0,1)*(np.abs(onrm[...,2])<.7))
    col=col*(1-.6*cr[...,None]*filled[...,None])
    lich=np.zeros_like(z)
    for c,rad in G_['lich']:
        d=np.sqrt((x-c[0])**2+(y-c[1])**2+(z-c[2])**2);ang=np.arctan2(z-c[2],x-c[0]+y-c[1]);lobe=rad*(1+.1*np.sin(ang*5+c[0]*40)+.06*np.sin(ang*11+c[1]*30))
        ring=np.clip((lobe-d)/(rad*.3),0,1);lich=np.maximum(lich,ring*(.75+.25*np.clip(d/lobe,0,1)))
    lich=lich*filled*(np.abs(onrm[...,2])<.8)*np.clip((noise-.15)*3,0,1)   # ragged, broken colonies
    col=col*(1-.7*lich[...,None])+np.array([.66,.68,.56])*(.85+.25*noise[...,None])*.7*lich[...,None]
    return np.clip(col,0,1),rough,{}
def jar_paint(g,col,rough,q,onrm,ao,cav,edge,m,filled,glow,noise,RES,meta=None):
    """dark glaze on the upper body (brown-black, olive and teal runs, thinner and browner at its edge), glazed inside the
    mouth, the worn rim and the chip faces bare clay, dust settled on the shoulder, pale lime crust in patches on the clay"""
    J=meta['jar'];H,G=J['H'],J['G'];x,y,z=q[...,0],q[...,1],q[...,2];rr=np.sqrt(x*x+y*y)+1e-6;t=np.arctan2(y,x)
    shade=(.5+.5*ao)[...,None]
    if g=='Detail_Shards':   # the outside of the broken rim faces up: glazed, the edges bare clay
        gm=((onrm[...,2]>.5)&filled).astype(float)
        col=col*(1-gm[...,None])+(np.array([.08,.06,.045])+np.array([.10,.11,.05])*noise[...,None]*.5)*shade*gm[...,None];return col,rough*(1-gm)+.35*gm,{'flat':gm*.75}
    if g!='Jar':return col,rough,{}
    radial=(onrm[...,0]*x+onrm[...,1]*y)/rr;inner=(radial<-.2)&filled&(z>J['wall']*1.5);outer=filled&~inner
    rimtop=filled&(onrm[...,2]>.6)&(z>H-J['wall']*.9)
    chipf=np.zeros_like(z)
    for ca,cw,cd in J['chips']:
        a=np.abs(np.angle(np.exp(1j*(t-ca))))/cw;dep=cd*np.clip(1-a**1.6,0,1);chipf=np.maximum(chipf,(a<1.05)*(z>H-dep-.005)*(dep>.002))
    gm,bd=glaze_mask(t,z,G);gm=gm*outer
    gm=np.maximum(gm,inner*np.clip((z-(H-.06*H/.5))/.01,0,1));gm=gm*(1-rimtop)*(1-chipf)
    edgeband=np.clip(1-(z-(G['z']-.03))/.06,0,1)   # the glaze thins out and browns towards its lower edge and in the runs
    # streaks running down: olive and teal where the glaze pooled, warm brown where it ran thin
    s1=np.zeros_like(z);s2=np.zeros_like(z);s3=np.zeros_like(z)
    for ta,w,z1,L,kind in G['streaks']:   # each run: widest at its top, wandering a little, fading out as it goes down
        a=np.abs(np.angle(np.exp(1j*(t-ta-.15*w*np.sin(z*40+ta)))))/(w*np.clip((z-(z1-L))/L,.25,1))
        v=np.exp(-a*a)*np.clip((z1-z)/.01,0,1)*np.clip((z-(z1-L))/(L*.6),0,1)
        if kind==0:s1=np.maximum(s1,v)
        elif kind==1:s2=np.maximum(s2,v)
        else:s3=np.maximum(s3,v)
    s1=s1*(.6+.4*noise)
    mott=np.clip(np.sin(x*47+np.sin(y*31+z*23)*2)*np.sin(y*41+z*29)*.5+.5,0,1)
    gcol=np.array([.075,.055,.04])[None,None,:]*(.8+.5*mott[...,None])
    gcol=gcol*(1-s1[...,None]*.85)+np.array([.25,.26,.13])*(.7+.6*noise[...,None])*s1[...,None]*.85
    gcol=gcol*(1-s2[...,None]*.6)+np.array([.16,.22,.21])*s2[...,None]*.6
    gcol=gcol*(1-s3[...,None]*.6)+np.array([.30,.18,.10])*s3[...,None]*.6
    gcol=gcol+np.array([.06,.035,.02])*bd[...,None]
    gcol=gcol*(1-edgeband[...,None]*.6)+np.array([.30,.17,.09])*edgeband[...,None]*.6
    col=col*(1-gm[...,None])+gcol*shade*gm[...,None];rough=rough*(1-gm)+(.32+.1*mott)*gm
    rb=(rimtop&(chipf==0)).astype(float)*np.clip((noise-.12)*4,0,1)   # thin brown glaze on the lip, rubbed through in places
    col=col*(1-rb[...,None]*.7)+np.array([.26,.15,.08])*shade*rb[...,None]*.7;rough=rough*(1-rb)+.45*rb
    col=np.where((chipf>0)[...,None]&filled[...,None],col*1.12+np.array([.03,.025,.02]),col)   # fresh breaks: bare clay, a step paler
    col=col*np.where(gm[...,None]>0,1,(.85+.3*noise[...,None]))   # darker and lighter patches on the bare clay
    mn=np.clip((onrm[...,2]-.3)/.5,0,1)*outer;dust=mn*np.clip((noise-.25)*2,0,1)*np.clip((z-H*.35)/(H*.2),0,1)
    col=col*(1-.55*dust[...,None])+np.array([.66,.60,.50])*.55*dust[...,None];rough=np.clip(rough+.4*dust,0,1)
    crust=np.clip((noise*.7+.3*mott-.62)*4,0,1)*outer*(1-gm)*np.clip(1-z/(G['z']+.02),0,1)
    col=col*(1-.5*crust[...,None])+np.array([.62,.58,.50])*.5*crust[...,None]
    return np.clip(col,0,1),rough,{'flat':gm*.75}   # glaze fills the grog pits: most of the clay relief goes under it

# sizes from the work pack (0.4-1.5 m, the largest 1.5 m long and 0.9 m tall); shapes from the chosen three-view
def BM04_01(M):return path_stone('BM04_01',M,1.5,.95,.9,601,[(-math.pi*.6,14,.18),(math.pi*.15,10,.15),(math.pi*.8,9,.14)],collide=True,tris=10000,
                                  blocks=[((-.15,0,.05),(.78,.5,.8),5),((.32,-.02,.02),(.5,.44,.68),4),((.7,.1,-.08),(.28,.3,.42),3)])
def BM04_02(M):return path_stone('BM04_02',M,1.0,.7,.55,602,[(-math.pi*.3,12,.15),(math.pi*.7,9,.12)],tris=7000,
                                  blocks=[((0,0,0),(.55,.4,.62),5),((.32,.1,-.15),(.22,.22,.3),3)])
def BM04_03(M):return path_stone('BM04_03',M,.7,.55,.42,603,[(math.pi*.4,10,.12),(-math.pi*.7,7,.1)],tris=5000,blocks=[((0,0,0),(.5,.42,.55),6)])
def BM04_04(M):return path_stone('BM04_04',M,.4,.34,.2,604,[(-math.pi*.5,7,.09)],tris=2800,crack=.7,blocks=[((0,0,0),(.5,.45,.4),4)])

PROPS={'BM01_01':BM01_01,'BM01_02':BM01_02,'BM01_03':BM01_03,'BM02_01':BM02_01,'BM02_02':BM02_02,'BM03_01':BM03_01,'BM03_02':BM03_02,'BM03_03':BM03_03,'BM04_01':BM04_01,'BM04_02':BM04_02,'BM04_03':BM04_03,'BM04_04':BM04_04,'BM05_01':BM05_01,'BM05_02':BM05_02,'BM05_03':BM05_03,'BM06_01':BM06_01,'BM06_02':BM06_02,'BM06_03':BM06_03,'BM06_04':BM06_04,'BM07_01':BM07_01}
REFDIR={k:k[:4] for k in PROPS}
MIN_TIER={'BM01_01':'standard','BM01_02':'standard','BM01_03':'standard','BM02_01':'high','BM02_02':'high','BM03_01':'high','BM03_02':'high','BM03_03':'high','BM04_01':'standard','BM04_02':'standard','BM04_03':'standard','BM04_04':'standard','BM05_01':'standard','BM05_02':'standard','BM05_03':'standard','BM06_01':'standard','BM06_02':'standard','BM06_03':'standard','BM06_04':'standard','BM07_01':'standard'}   # work pack §2
TARGET={'BM01_01':('x',.5),'BM01_02':('x',.8),'BM01_03':('x',1.1),'BM02_01':('z',.8),'BM02_02':('z',1.1),'BM03_01':('z',.3),'BM03_02':('z',.5),'BM03_03':('z',.8),'BM04_01':('x',1.5),'BM04_02':('x',1.0),'BM04_03':('x',.7),'BM04_04':('x',.4),'BM05_01':('z',.75),'BM05_02':('z',.45),'BM05_03':('z',.45),'BM06_01':('x',.8),'BM06_02':('x',.8),'BM06_03':('x',1.2),'BM06_04':('x',1.2),'BM07_01':('z',2.3)}   # work pack §2: crates by width, posts by height
GROUP_RES={'BM02_01':{'Wood':2048,'Detail_Stones':512,'Detail_Grass':256},'BM02_02':{'Wood':2048,'Detail_Stones':512,'Detail_Grass':256},
           'BM03_01':{'Jar':1024,'Detail_Shards':256},'BM03_02':{'Jar':1024,'Detail_Shards':256},'BM03_03':{'Jar':2048,'Detail_Shards':256},
           'BM04_01':{'Stone':2048,'Detail_Grass':256},'BM04_02':{'Stone':2048,'Detail_Grass':256},'BM04_03':{'Stone':1024,'Detail_Grass':256},'BM04_04':{'Stone':1024,'Detail_Grass':256},
           'BM05_01':{'Stone':2048,'Detail_Grass':256},'BM05_02':{'Stone':1024,'Detail_Grass':256},'BM05_03':{'Stone':1024,'Detail_Grass':256},
           'BM06_01':{'Stone':2048,'Water':256,'Detail_Grass':256},'BM06_02':{'Stone':2048,'Water':256,'Detail_Grass':256,'Detail_Iron':256},
           'BM06_03':{'Stone':2048,'Detail_Plant':1024,'Detail_Grass':256},'BM06_04':{'Stone':2048,'Detail_Plant':1024,'Detail_Grass':256},
           'BM07_01':{'Stone':2048,'Detail_Litter':512},
           'BM01_01':{'Wood':1024,'Detail_Nails':256,'Detail_Grass':256},
           'BM01_02':{'Wood':2048,'Detail_Nails':256,'Detail_Rope':1024,'Detail_Grass':256},
           'BM01_03':{'Wood':2048,'Detail_Nails':512,'Detail_Grass':256}}
MOSS={k:{'BM01':{'Wood':.35},'BM02':{'Wood':.3,'Detail_Stones':.12},'BM03':{'Jar':.25},'BM04':{'Stone':.35},'BM05':{'Stone':.45},'BM06':{'Stone':.4},'BM07':{'Stone':.55}}[k[:4]] for k in PROPS}
PAINT={k:{'BM01':crate_paint,'BM02':post_paint,'BM03':jar_paint,'BM04':rock_paint,'BM05':garden_paint,'BM06':garden_paint,'BM07':stele_paint}[k[:4]] for k in PROPS}

# ---------------- collision ----------------
def collision(pid,meta):
    off=Vector(meta['offset']);out=[];info={}
    for suffix,plist in meta.get('collisions',{}).items():
        if plist in ('hull','hull_stone'):   # convex hull of the body (Detail_ left out), cut down to a few hundred triangles
            bm=bmesh.new()
            for o in parts:
                if not o['grp'].startswith('Detail_') and (plist=='hull' or o['grp']=='Stone'):
                    for v in o.data.vertices:bm.verts.new(o.matrix_world@v.co)
            bmesh.ops.convex_hull(bm,input=bm.verts[:]);bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
            me=bpy.data.meshes.new(f'{pid}_{suffix}');bm.to_mesh(me);bm.free();c=bpy.data.objects.new(f'{pid}_{suffix}',me);bpy.context.scene.collection.objects.link(c)
            nt=len(me.polygons)
            if nt>300:md=c.modifiers.new('d','DECIMATE');md.ratio=300/nt;apply(c,md)
            c.hide_render=True;c.display_type='WIRE';out.append(c)
            lo=np.array([min((c.matrix_world@v.co)[i] for v in c.data.vertices) for i in range(3)]);hi=np.array([max((c.matrix_world@v.co)[i] for v in c.data.vertices) for i in range(3)])
            info[f'{pid}_{suffix}']={'primitives':[{'type':'convex_hull','triangles':sum(len(p_.vertices)-2 for p_ in c.data.polygons)}],'bounds_min':[round(float(v),3) for v in lo],'bounds_max':[round(float(v),3) for v in hi]}
            continue
        objs=[];prims=[]
        for p in plist:
            c=[round(p['center'][i]+off[i],3) for i in range(3)];bm=box_bm(p['size'],c);prims.append({'type':'box','size':[round(v,3) for v in p['size']],'center':c})
            me=bpy.data.meshes.new('col');bm.to_mesh(me);bm.free();o=bpy.data.objects.new('col',me);bpy.context.scene.collection.objects.link(o);objs.append(o)
        c=join(objs,f'{pid}_{suffix}');c.data.name=c.name;c.hide_render=True;c.display_type='WIRE';out.append(c)
        lo=np.array([min((c.matrix_world@v.co)[i] for v in c.data.vertices) for i in range(3)]);hi=np.array([max((c.matrix_world@v.co)[i] for v in c.data.vertices) for i in range(3)])
        info[f'{pid}_{suffix}']={'primitives':prims,'bounds_min':[round(float(v),3) for v in lo],'bounds_max':[round(float(v),3) for v in hi]}
    return out,info

# ---------------- bake / LOD / export ----------------
def run(pid):
    sel_txt=(REF/REFDIR.get(pid,pid)/'prompt.txt').read_text(encoding='utf-8')
    assert '選用：' in sel_txt,f'{pid}: pick a saved AI three-view before modelling'
    bpy.ops.wm.read_factory_settings(use_empty=True);parts.clear();GLOW.clear()
    sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.render.engine='CYCLES';dev=gpu(sc);sc.cycles.samples=16;sc.render.bake.margin=6;sc.render.bake.margin_type='EXTEND'
    M=make_sources();meta=PROPS[pid](M)
    def sel(*obs):
        bpy.ops.object.select_all(action='DESELECT')
        for o in obs:o.select_set(True)
        bpy.context.view_layer.objects.active=obs[0]
    # origin from the body alone: grass leaning out and nail heads must not shift the footprint centre or lift the base
    pts=np.array([(o.matrix_world@v.co)[:] for o in parts if not o['grp'].startswith('Detail_') for v in o.data.vertices]);lo,hi=pts.min(0),pts.max(0)
    off=Vector((-(lo[0]+hi[0])/2,-(lo[1]+hi[1])/2,-lo[2]))
    for o in parts:o.data.transform(Matrix.Translation(off))
    for h in meta.get('hires',{}).values():h.data.transform(Matrix.Translation(off))
    meta['offset']=np.array(off[:])
    srcparts=list(parts);groups={}
    for o in srcparts:groups.setdefault(o['grp'],[]).append(o)
    G={}
    for g,objs in groups.items():
        cp=[]
        for o in objs:d=o.copy();d.data=o.data.copy();sc.collection.objects.link(d);cp.append(d)
        sel(*cp);bpy.ops.object.join();o=bpy.context.object;o.name=o.data.name=f'{pid}_{g}_LOD0'
        bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.triangulate(bm,faces=bm.faces)
        # #67 QA: sub-millimetre slivers bake to zero-area UV (collapse them); separate pieces with triangles in one plane z-fight (lift the smaller 1 mm)
        bmesh.ops.dissolve_degenerate(bm,dist=.0008,edges=list({e for f in bm.faces if f.calc_area()<4e-7 for e in f.edges}))
        bmesh.ops.triangulate(bm,faces=bm.faces[:]);separate_coplanar(bm)
        if g.startswith('Detail_') and not pid.startswith('BM01'):   # #69 review (BM01 stays as merged from #67): hidden ground bottoms
            meshfix.drop_ground_bottoms(bm);meta.setdefault('separated',{})[g]=list(meshfix.separate_overlaps(bm,mode='tilt',big=14))+list(meshfix.separate_overlaps(bm))   # and same-facing coplanar pieces; only leaves and grass blades turn (a branch turned about its root swung away from its leaf cluster)
        bm.to_mesh(o.data);bm.free()
        for u in [u for u in o.data.uv_layers if u.name not in ('Tiled','Strip')]:o.data.uv_layers.remove(u)
        bu=o.data.uv_layers.new(name='Bake');o.data.uv_layers.active=bu;sel(o)
        res=GROUP_RES[pid][g];mg=16/res   # island gap 16 px > bake bleed 6 px
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(55),island_margin=mg,area_weight=0,scale_to_bounds=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        me=o.data;sa=me.attributes.get('strip')
        if sa and 'Strip' in me.uv_layers:   # rope strands: one island per tube, not one per face
            nl=len(me.loops);nf=len(me.polygons);fl=np.zeros(nf,np.int32);sa.data.foreach_get('value',fl)
            lt=np.zeros(nf,np.int64);me.polygons.foreach_get('loop_total',lt)
            lf=np.repeat(fl,lt).astype(bool);su=np.zeros(nl*2);me.uv_layers['Strip'].data.foreach_get('uv',su);bk=np.zeros(nl*2);me.uv_layers['Bake'].data.foreach_get('uv',bk)
            su=su.reshape(nl,2);bk=bk.reshape(nl,2);bk[lf]=su[lf]*.05;me.uv_layers['Bake'].data.foreach_set('uv',bk.ravel())
        if 'Strip' in me.uv_layers:me.uv_layers.remove(me.uv_layers['Strip'])
        if sa:me.attributes.remove(sa)
        me.uv_layers.active=me.uv_layers['Bake'];bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.select_all(action='SELECT')
        bpy.ops.uv.average_islands_scale();bpy.ops.uv.pack_islands(margin=mg,rotate=True)
        bpy.ops.object.mode_set(mode='OBJECT');G[g]=o
    for o in sc.objects:o.hide_render=o not in G.values()
    tex={};padmask=[None]
    def pad(a):
        f=padmask[0]
        if f is None or f.shape!=a.shape[:2] or f.all():return a
        a=a.copy();f=f.copy();a[~f]=0
        for _ in range(24):
            acc=np.zeros_like(a);cnt=np.zeros(f.shape,np.float32)
            for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):acc+=np.roll(np.roll(a*f[...,None],dy,0),dx,1);cnt+=np.roll(np.roll(f,dy,0),dx,1)
            new=(~f)&(cnt>0);a[new]=acc[new]/cnt[new][:,None];f=f|new
            if f.all():break
        a[~f]=a[f].mean(0);return a
    def save(name,rgba,RES,data=False):
        rgba=pad(np.asarray(rgba,dtype=np.float32));im=bpy.data.images.new(name,RES,RES,alpha=True)
        if data:im.colorspace_settings.name='Non-Color'
        im.pixels.foreach_set(np.ascontiguousarray(rgba,dtype=np.float32).ravel());im.filepath_raw=str(TEX/f'{name}.png');im.file_format='PNG';im.save();return im
    for g,o in G.items():
        RES=GROUP_RES[pid][g];key=f'{pid}_{g}';one=np.ones((RES,RES),np.float32);padmask[0]=None;mats=list(o.data.materials)
        for d in G.values():   # the body bakes without the Detail_ meshes: the standard tier hides them, so no rope or nail shadow may stay in its AO
            d.hide_render=not g.startswith('Detail_') and d.name.startswith(f'{pid}_Detail_')
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
        rough=bake('rough','ROUGHNESS',True)[...,0]
        hr=meta.get('hires',{}).get(g)
        if hr:   # carved relief lives on the dense mesh: bake its normals onto this decimated one
            hr.hide_render=False;im=target('nrm',True);sel(o);hr.select_set(True);bpy.context.view_layer.objects.active=o
            bpy.ops.object.bake(type='NORMAL',normal_space='TANGENT',use_selected_to_active=True,cage_extrusion=.008,max_ray_distance=.03)
            nrm=np.array(im.pixels[:],dtype=np.float32).reshape(RES,RES,4);bpy.data.images.remove(im);hr.hide_render=True
        else:nrm=bake('nrm','NORMAL',True,normal_space='TANGENT')
        onrm=bake('onrm','NORMAL',True,normal_space='OBJECT')[...,:3]*2-1
        s=emit(lambda nt,m,em:em.inputs['Color'].__setattr__('default_value',(GLOW.get(m.name,(0,0))[0],)*3+(1,)));met=bake('met','EMIT',True)[...,0];restore(s)
        def edges(nt,m,em):
            gg=nt.nodes.new('ShaderNodeNewGeometry');nt.links.new(gg.outputs['Pointiness'],em.inputs['Color'])
        s=emit(edges);pt=bake('edge','EMIT',True)[...,0];restore(s);edge=np.clip((pt-.52)/.07,0,1);cav=np.clip((.485-pt)/.05,0,1)
        s=emit(lambda nt,m,em:nt.links.new(nt.nodes.new('ShaderNodeNewGeometry').outputs['Position'],em.inputs['Color']));pos=bake('pos','EMIT',True)[...,:3];restore(s)
        filled=np.abs(pos).sum(2)>1e-7;padmask[0]=filled;q=pos-meta['offset'];px,py,pz=pos[...,0],pos[...,1],pos[...,2];glow=np.zeros_like(pz)
        # finish: cool shade in occlusion, grime in the board joints, a little warmth on top, worn pale edges (weathered, not painted)
        cool=np.array([.30,.32,.42]);col=alb[...,:3]*(.45+.55*ao[...,None])+(1-ao[...,None])*cool*.08
        col=col*(1-.5*cav[...,None])+cav[...,None]*np.array([.08,.07,.05])*.5
        col=col*(1+.05*np.clip(pz/max(hi[2]-lo[2],.3),0,1)[...,None]*np.array([1.0,.88,.7]))
        wear=np.clip(edge,0,1)[...,None]*(met[...,None]<.1)*meta.get('wear',1);col=np.clip(col*(1+.10*wear)+wear*np.array([.03,.03,.03]),0,1)
        mn=np.clip((onrm[...,2]-.35)/.5,0,1)
        n1=np.sin(px*9.3+np.sin(py*7.1+pz*3.3)*1.7)*np.sin(py*8.7+np.sin(pz*6.3+px*2.1)*1.9);n2=np.sin(px*31.1+np.sin(py*27.7)*1.3)*np.sin(pz*29.3+py*17.9)
        noise=np.clip(.5+.42*n1+.18*n2,0,1);m=np.zeros_like(pz);amt=MOSS.get(pid,{}).get(g,0)
        if amt:   # moss creeping up from the soil line, thickest in the joints and corners
            ml=meta.get('moss_low',0);mh=meta.get('moss_h',.5)
            low=np.clip(1-pz/mh,0,1)*ml;creep=np.clip(1-pz/(mh*.6),0,1)*ml*.9+cav*meta.get('moss_cav',.5)*np.clip(1-pz/(mh*1.6),0,1)
            n3=.5+.5*np.sin(px*83.1+np.sin(pz*61.7)*2.1)*np.sin(pz*77.3+py*59.9+np.sin(px*47.3)*1.7)   # small clumps, so it is not an airbrushed band
            m=np.clip((mn*(low+meta.get('moss_top',.15))+creep)*amt*2*np.clip((noise*.6+n3*.4-.45)*5,0,1),0,1)*filled
            mcol=np.array((.24,.38,.15))+np.array([.10,.14,.06])*noise[...,None]   # guide grass swatch, root end #3e6a2a
            col=col*(1-m[...,None])+mcol*m[...,None];rough=np.clip(rough+.12*m,0,1)
        if meta.get('soil'):
            s_=np.clip((meta['soil']-pz)/meta['soil'],0,1)**1.4*filled*(met<.5)*(.6+.4*noise);col=col*(1-.5*s_[...,None])+np.array([.24,.19,.13])*.5*s_[...,None]
        extra={}
        if pid in PAINT:col,rough,extra=PAINT[pid](g,col,rough,q,onrm,ao,cav,edge,m,filled,glow,noise,RES,meta)
        if 'flat' in extra:f_=extra['flat'][...,None];nrm=nrm.copy();nrm[...,:3]=nrm[...,:3]*(1-f_)+np.array([.5,.5,1.])*f_   # toward the mesh normal
        T={'alb':save(f'{key}_Albedo',np.dstack([np.clip(col,0,1),one]),RES),'nrm':save(f'{key}_Normal',nrm,RES,True),
           'orm':save(f'{key}_ORM',np.dstack([ao,rough,met,one]),RES,True)}
        save(f'{key}_MaskURP',np.dstack([met,ao,0*one,1-rough]),RES,True);tex[g]=T
    root=bpy.data.objects.new(f'{pid}_GroundOrigin',None);sc.collection.objects.link(root)
    lods=[]
    for g,o in G.items():
        T=tex[g];fm=bpy.data.materials.new(f'{pid}_{g}');fm.use_nodes=True;nt=fm.node_tree;bs=nt.nodes['Principled BSDF']
        def tn(im):t=nt.nodes.new('ShaderNodeTexImage');t.image=im;return t
        nt.links.new(tn(T['alb']).outputs['Color'],bs.inputs['Base Color'])
        nmn=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tn(T['nrm']).outputs['Color'],nmn.inputs['Color']);nt.links.new(nmn.outputs['Normal'],bs.inputs['Normal'])
        sp=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tn(T['orm']).outputs['Color'],sp.inputs['Color']);nt.links.new(sp.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sp.outputs['Blue'],bs.inputs['Metallic'])
        group=[o]
        for L,ratio in ((1,.5),(2,.15)):
            d=o.copy();d.data=o.data.copy();sc.collection.objects.link(d);d.name=d.data.name=f'{pid}_{g}_LOD{L}'
            m=d.modifiers.new('d','DECIMATE');m.ratio=ratio;m.use_collapse_triangulate=True;sel(d);bpy.ops.object.modifier_apply(modifier='d');group.append(d)
        for d in group:
            uvs=d.data.uv_layers
            if 'Tiled' in uvs:uvs.remove(uvs['Tiled'])
            uvs['Bake'].name='UVMap';d.data.materials.clear();d.data.materials.append(fm);d.hide_render=not d.name.endswith('LOD0');d.parent=root
        lods.append(group)
    bpy.context.view_layer.update();pts=np.array([(gr[0].matrix_world@v.co)[:] for gr in lods for v in gr[0].data.vertices]);lo,hi=pts.min(0),pts.max(0);dims=hi-lo
    bp=np.array([(gr[0].matrix_world@v.co)[:] for g,gr in zip(G,lods) if not g.startswith('Detail_') for v in gr[0].data.vertices]);bdims=bp.max(0)-bp.min(0)
    cols,colinfo=collision(pid,meta)
    for c in cols:c.parent=root
    src=bpy.data.collections.new(f'{pid}_SourceParts');sc.collection.children.link(src)
    for o in srcparts:
        for c in list(o.users_collection):c.objects.unlink(o)
        src.objects.link(o);o.hide_render=True;o.hide_set(True)
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE/f'{pid}.blend'),compress=True)
    sel(root,*[gr[0] for gr in lods]);bpy.ops.export_scene.gltf(filepath=str(OUT/f'{pid}.glb'),use_selection=True,export_format='GLB',export_apply=True)
    sel(root,*[d for gr in lods for d in gr],*cols);bpy.ops.export_scene.fbx(filepath=str(OUT/f'{pid}.fbx'),use_selection=True,object_types={'MESH','EMPTY'},global_scale=1.0,apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_ALL',bake_space_transform=True,axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='FACE',
        use_tspace=True,add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE',embed_textures=False)
    tri=lambda o:sum(len(p.vertices)-2 for p in o.data.polygons)
    detail=[g for g in G if g.startswith('Detail_')]
    info={'id':pid,'device':dev,'dimensions_xyz_m':[round(float(x),3) for x in dims],'body_dimensions_xyz_m':[round(float(x),3) for x in bdims],'target_axis':TARGET[pid][0],'target_m':TARGET[pid][1],
          'minTier':MIN_TIER[pid],'detailObjects':detail,'detailMeshes':[f'{pid}_{g}_LOD{L}' for g in detail for L in range(3)],
          'groups':{g:{'material':f'{pid}_{g}','texture_px':GROUP_RES[pid][g],'triangles':[tri(d) for d in gr],'maps':sorted(tex[g])} for g,gr in zip(G,lods)},
          'triangles_total':[sum(tri(gr[i]) for gr in lods) for i in range(3)],
          'triangles_without_detail':[sum(tri(gr[i]) for g,gr in zip(G,lods) if not g.startswith('Detail_')) for i in range(3)],'source_parts':len(srcparts),
          'reference':f'art/references/{REFDIR.get(pid,pid)}/prompt.txt','origin':'footprint centre, bottom z = 0, front = -Y (Blender) / -Z (FBX, Unity)',
          'textures':'per group: Albedo / Normal / MaskURP (R metal, G AO, A smoothness) / ORM (glTF)','collision':colinfo}
    if 'notes' in meta:info['notes']=meta['notes']
    print('BASICS_DONE',json.dumps(info,ensure_ascii=False));return info
ids=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else list(PROPS)
infos=[run(i) for i in ids]
mf=OUT/'model_info.json';old=json.loads(mf.read_text(encoding='utf-8')) if mf.exists() else {}
old.update({i['id']:i for i in infos});mf.write_text(json.dumps(dict(sorted(old.items())),ensure_ascii=False,indent=1),encoding='utf-8')
