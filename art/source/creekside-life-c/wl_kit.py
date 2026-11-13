"""承天 · C 西溪生活小物（creekside-life-c）共用工具 — Eli-0731, Blender 4.5.3 LTS.
Tiled source-texture painting (numpy, 1024², 0.5 m per tile), mesh helpers (box, tube, rope, bevel, jitter) and the
coplanar clean-up, carried over from art/source/modelling-basics-c/build_basics.py (BM01–BM07, merged in #67/#69)
so the WL / FI props are built and finished the same way as C's earlier basics."""
import bpy,bmesh,math,random
import numpy as np
from mathutils import Vector,Matrix
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

# ---------------- geometry helpers ----------------
parts=[];uvr=random.Random(77)
def link(o,grp):bpy.context.scene.collection.objects.link(o);o["grp"]=grp;parts.append(o);return o
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
