"""承天 · 基礎建模練習（C 包 modelling-basics-c）— Eli-0731, Blender 4.5.3 LTS.
BM01 舊木箱 ×3：BM01_01 0.5 m、BM01_02 0.8 m（綁麻繩）、BM01_03 1.1 m（正面換過一塊板）。
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
def finish(name,bm,mat,grp,scale=TILE):
    """tiled UV: box projection on the part's principal axes, the long axis along V (the grain runs along the board);
    every part starts at a random place in the tile so neighbouring boards do not repeat the same grain"""
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces);lay=bm.loops.layers.uv.get('Tiled') or bm.loops.layers.uv.new('Tiled')
    pts=np.array([v.co[:] for v in bm.verts]);c=pts.mean(0);du,dv=uvr.random(),uvr.random()
    try:_,_,vt=np.linalg.svd(pts-c,full_matrices=False);A,S1,S2=[Vector(v) for v in vt]
    except Exception:A,S1,S2=Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))
    for f in bm.faces:
        n=f.normal;k=int(np.argmax([abs(n.dot(A)),abs(n.dot(S1)),abs(n.dot(S2))]))
        for l in f.loops:
            p=l.vert.co-Vector(c);u,v={0:(p.dot(S1),p.dot(S2)),1:(p.dot(S2),p.dot(A)),2:(p.dot(S1),p.dot(A))}[k];l[lay].uv=(u/scale+du,v/scale+dv)
    me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free();o=bpy.data.objects.new(name,me);me.materials.append(mat)
    return link(o,grp)
def tube(name,pts,r,mat,grp,sides=8,scale=.3,caps=True):
    pts=[Vector(p) for p in pts];bm=bmesh.new();rings=[];prev=None
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

PROPS={'BM01_01':BM01_01,'BM01_02':BM01_02,'BM01_03':BM01_03}
REFDIR={'BM01_01':'BM01','BM01_02':'BM01','BM01_03':'BM01'}
MIN_TIER={'BM01_01':'standard','BM01_02':'standard','BM01_03':'standard'}
WIDTH={'BM01_01':.5,'BM01_02':.8,'BM01_03':1.1}   # work pack: 0.5 / 0.8 / 1.1 m wide
GROUP_RES={'BM01_01':{'Wood':1024,'Detail_Nails':256,'Detail_Grass':256},
           'BM01_02':{'Wood':2048,'Detail_Nails':256,'Detail_Rope':1024,'Detail_Grass':256},
           'BM01_03':{'Wood':2048,'Detail_Nails':512,'Detail_Grass':256}}
MOSS={k:{'Wood':.35} for k in PROPS}   # a little moss at the foot only (C07 has none)
PAINT={k:crate_paint for k in PROPS}

# ---------------- collision ----------------
def collision(pid,meta):
    off=Vector(meta['offset']);out=[];info={}
    for suffix,plist in meta.get('collisions',{}).items():
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
        bmesh.ops.triangulate(bm,faces=bm.faces[:]);separate_coplanar(bm);bm.to_mesh(o.data);bm.free()
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
        rough=bake('rough','ROUGHNESS',True)[...,0];nrm=bake('nrm','NORMAL',True,normal_space='TANGENT');onrm=bake('onrm','NORMAL',True,normal_space='OBJECT')[...,:3]*2-1
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
    info={'id':pid,'device':dev,'dimensions_xyz_m':[round(float(x),3) for x in dims],'body_dimensions_xyz_m':[round(float(x),3) for x in bdims],'target_width_m':WIDTH[pid],
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
