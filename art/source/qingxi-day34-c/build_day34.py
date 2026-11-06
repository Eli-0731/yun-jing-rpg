"""承天 · 第 3、4 天的模型（C 包）— Eli-0731, Blender 4.5.3 LTS.
UP01 斷流石壩、UP02 溫石 ×3、UP03 水位刻痕石樁、UP04 畫了水路的平石、UP05 引氣課擺設（蒲團 ×2、矮几、小香爐）、UP06 柳知微的提燈。
Each item is modelled only after its AI three-view candidates are saved and one is picked in
art/references/qingxi-day34-c/<ID>/prompt.txt (AGENTS.md order).
Pipeline (same as the day 1-2 package): named parts with painterly tiled source materials, tagged into bake groups → each group joined,
unique UV, Cycles bake (diffuse colour, AO with the whole asset visible, roughness, tangent normal, object normal, metal, glow mask,
edge pointiness, position) → numpy finish (cool AO shade, warm worn edges, moss, soil, per-item paint and state maps)
→ one material per group with Albedo / Normal / MaskURP / ORM (+ Emission, Albedo_Warm, WarmthMask) → LOD1 ≈ 50 %, LOD2 ≈ 15 %
→ collision meshes (box / cylinder / convex hulls of named parts) → .blend, FBX (all LODs + collision + sockets), GLB (LOD0).
Origin: footprint centre, bottom at z = 0, Blender -Y is the front. No ground plate.
blender -b --factory-startup -P build_day34.py -- UP03 [UP04 ...]
"""
import bpy,bmesh,json,math,sys,random
from pathlib import Path
from mathutils import Vector,Matrix
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];PKG='qingxi-day34-c'
REF=ROOT/'art/references'/PKG;TEX=ROOT/'art/textures'/PKG;OUT=ROOT/'art/exports'/PKG
for p in (TEX,OUT):p.mkdir(parents=True,exist_ok=True)

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
    S['moss']=(lerp((.22,.24,.09),(.50,.49,.17),fbm(8,3)),fbm(16,3),3.0,.95,0,0)
    S['soil']=(lerp((.28,.21,.14),(.45,.35,.24),fbm(8,3)),fbm(24,3),2.4,.95,0,0)
    S['water']=(lerp((.06,.16,.16),(.12,.26,.25),soft),fbm(6,2)*.2,.3,.05,0,0)
    S['charcoal']=(lerp((.05,.05,.05),(.20,.13,.10),fbm(20,2)),fbm(20,2),2,.9,0,0)
    S['ember']=(lerp((.55,.18,.06),(.85,.40,.12),fbm(20,2)),fbm(20,2),1,.9,0,1)
    for k,(c0,c1) in {'herb_green':((.20,.32,.12),(.38,.52,.22)),'herb_sage':((.36,.42,.30),(.56,.62,.46)),'herb_dry':((.40,.34,.18),(.62,.54,.30)),
                      'herb_olive':((.30,.32,.14),(.48,.50,.24)),'flower_violet':((.36,.30,.48),(.54,.46,.66)),'flower_gold':((.62,.46,.14),(.82,.66,.26)),
                      'leaf_fallen':((.42,.28,.14),(.66,.46,.22))}.items():
        S[k]=(lerp(c0,c1,np.clip(.6*fbm(6,2)+.4*(.5+.5*np.sin(X*math.tau*3)),0,1)),fbm(20,2),1,.85,0,0)
    # day 3-4 additions: creek stone, a paler replacement block, wet silt, silver dead wood and bark, water weed, fern, gravel,
    # straw braid, old elm, patinated bronze, incense ash, moon-white lantern paper
    S['creekstone']=(lerp((.31,.28,.24),(.60,.54,.45),np.clip(big*.75+.3*blot+.12*st-.05,0,1))*(1-.08*lich[...,None])+lich[...,None]*np.array([.08,.09,.05]),big+.4*fbm(18,2)+.4*lich,2.6,.86,0,0)
    S['granite']=(lerp((.31,.29,.26),(.55,.52,.46),np.clip(big*.8+.25*blot+.15*st-.05,0,1))*(1-.10*lich[...,None])+lich[...,None]*np.array([.06,.08,.02]),big+.5*fbm(24,2)+.6*lich,3.2,.88,0,0)
    S['granite_new']=(lerp((.56,.53,.48),(.74,.71,.65),np.clip(big*.7+.2*st,0,1)),big+.4*fbm(24,2),2.6,.82,0,0)
    S['granite_b']=(lerp((.30,.30,.30),(.55,.54,.52),np.clip(big*.8+.25*blot+.15*st-.05,0,1))*(1-.10*lich[...,None])+lich[...,None]*np.array([.06,.08,.02]),big+.5*fbm(24,2)+.6*lich,3.2,.88,0,0)
    S['granite_c']=(lerp((.38,.34,.28),(.64,.57,.47),np.clip(big*.8+.25*blot+.15*st-.05,0,1))*(1-.10*lich[...,None])+lich[...,None]*np.array([.06,.08,.02]),big+.5*fbm(24,2)+.6*lich,3.2,.88,0,0)
    S['mortar']=(lerp((.13,.12,.10),(.25,.23,.19),fbm(8,3)),fbm(20,3),2.0,.95,0,0)
    S['silt']=(lerp((.22,.18,.13),(.40,.33,.24),np.clip(fbm(5,3)*.8+.25*strokes(6,2),0,1)),fbm(18,3),2.0,.55,0,0)
    S['deadwood']=(lerp((.24,.19,.14),(.46,.38,.29),np.clip(t*1.1-.05,0,1))*(1-.25*cr[...,None]),.8*grain+1.6*cr,2.8,.82,0,0)
    S['bark']=(lerp((.18,.15,.12),(.36,.30,.23),np.clip(.6*fbm(6,3,aniso=5)+.4*cr,0,1)),fbm(14,3,aniso=5)+cr,3.4,.92,0,0)
    S['weed']=(lerp((.12,.20,.10),(.26,.36,.16),np.clip(.6*fbm(6,2)+.4*(.5+.5*np.sin(Y*math.tau*6)),0,1)),fbm(20,2),.8,.45,0,0)
    S['fern']=(lerp((.20,.34,.12),(.42,.56,.22),np.clip(.6*fbm(6,2)+.4*(.5+.5*np.sin(X*math.tau*3)),0,1)),fbm(20,2),1,.8,0,0)
    S['grass']=(lerp((.30,.40,.14),(.56,.62,.26),np.clip(.6*fbm(6,2)+.4*Y,0,1)),fbm(20,2),1,.85,0,0)
    S['gravel']=(lerp((.30,.29,.27),(.62,.59,.54),fbm(10,3)),fbm(30,3),2,.85,0,0)
    S['straw']=(lerp((.52,.42,.22),(.78,.66,.38),np.clip(tw*.55+.45*fbm(5,3),0,1)),tw,1.4,.9,0,0)
    S['straw_old']=(lerp((.33,.27,.17),(.52,.44,.30),np.clip(tw*.55+.45*fbm(5,3),0,1))*(1-.12*np.clip((fbm(3,2)-.5)*3,0,1))[...,None],tw,1.4,.92,0,0)
    S['elm']=(lerp((.22,.16,.12),(.42,.32,.23),np.clip(t*1.05,0,1)),.5*grain+1.0*cr+.3*st,2.2,.72,0,0)
    S['bronze']=(lerp((.20,.30,.24),(.38,.46,.34),np.clip(fbm(5,3)*1.1-.05,0,1))+np.array([.10,.06,.0])*np.clip((fbm(3,2)-.55)*3,0,1)[...,None],fbm(16,3),1.4,.62,.55,0)
    S['ash']=(lerp((.20,.19,.18),(.36,.35,.33),fbm(16,3)),fbm(30,2),1,.95,0,0)
    S['moonpaper']=(lerp((.80,.77,.68),(.92,.89,.80),fbm(4,3))*(1-.12*np.clip((fbm(10,2)-.6)*4,0,1)-.06*np.clip((fbm(40,2,aniso=4)-.55)*4,0,1))[...,None],fbm(30,2)+.4*(.5+.5*np.sin(Y*math.tau*10)),.5,.9,0,1)
    S['cloth']=(lerp((.30,.30,.32),(.46,.46,.48),soft)*(1-.06*(np.sin(X*700)>.6))[...,None],.5*np.sin(X*600)+.5*np.sin(Y*600),.7,.95,0,0)
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
LOOSE={'UP01':('Debris','Plants'),**{k:('Gravel','Plants') for k in ('UP02_01','UP02_02','UP02_03','UP03')},'UP04':('Gravel','Plants','Charcoal')}
def settle(pid,link_=.003,touch=.001,embed=.003):
    """#64 review: loose pieces (debris, weed, tufts, gravel) must rest on something. Pieces of the loose groups that come
    within link_ of each other form a cluster; a cluster is supported when one of its pieces comes within touch of the
    ground or of a fixed part (weir, gate, stone). Every unsupported cluster is moved, in rounds of growing reach, onto
    its nearest support (the ground, a fixed part, or an already supported cluster) and sunk embed into it; onto the
    ground it only comes down to touch, since sinking it would make it the lowest point and lift the whole prop off its pivot.
    Same contact rule as tools/art/qa_contact_parts.py. Returns {piece name: move in mm} for the log."""
    from mathutils.bvhtree import BVHTree
    loose=LOOSE.get(pid,())
    L=[o for o in parts if o['grp'] in loose];Fx=[o for o in parts if o['grp'] not in loose and not o.get('nobounds')]
    if not L:return {}
    def wv(o):mw=o.matrix_world;return [mw@v.co for v in o.data.vertices]
    VS=[wv(o) for o in L];ground=min(min(v.z for v in wv(o)) for o in Fx)
    def bvh(objs):
        V=[];F=[];own=[]
        for k,o in enumerate(objs):
            b=len(V);V+=wv(o)
            for p in o.data.polygons:F.append([b+i for i in p.vertices]);own.append(k)
        return BVHTree.FromPolygons(V,F),own
    allo=L+Fx;tree,own=bvh(allo);n=len(L);par=list(range(n));sup=[False]*n
    def fd(x):
        while par[x]!=x:par[x]=par[par[x]];x=par[x]
        return x
    for k in range(n):
        if min(v.z for v in VS[k])-ground<=touch:sup[k]=True
        for v in VS[k]:
            for (co,nn,fi,d) in tree.find_nearest_range(v,link_):
                j=own[fi]
                if j==k:continue
                if j>=n:
                    if d<=touch:sup[k]=True
                else:par[fd(k)]=fd(j)
    cl={};[cl.setdefault(fd(k),[]).append(k) for k in range(n)]
    ok={r for r,ks in cl.items() if any(sup[k] for k in ks)};moves={};reach=.004
    while len(ok)<len(cl):
        st,sown=bvh(Fx+[L[k] for r in ok for k in cl[r]])
        for r,ks in cl.items():
            if r in ok:continue
            best=(min(min(v.z for v in VS[k]) for k in ks)-ground,None,None)   # straight down onto the ground
            for k in ks:
                for v in VS[k]:
                    hit=st.find_nearest(v,reach)
                    if hit[0] is not None and hit[3]<best[0]:best=(hit[3],v,hit[0])
            if best[0]>reach:continue
            mv=Vector((0,0,-best[0])) if best[1] is None else (best[2]-best[1])+(best[2]-best[1]).normalized()*embed
            for k in ks:
                L[k].data.transform(Matrix.Translation(L[k].matrix_world.inverted().to_3x3()@mv));VS[k]=wv(L[k]);moves[L[k].name]=round(mv.length*1000,1)
            ok.add(r)
        reach*=2
        if reach>4:break
    return moves
def _sat(A,B,n):   # in-plane overlap depth of two coplanar triangles (separating axes), 0 when they only touch
    u_=(A[1]-A[0]).normalized();w_=n.cross(u_);P=[Vector((p.dot(u_),p.dot(w_))) for p in A];Q=[Vector((p.dot(u_),p.dot(w_))) for p in B];pen=1e9
    for poly in (P,Q):
        for t in range(3):
            e_=poly[(t+1)%3]-poly[t];ax=Vector((-e_.y,e_.x))
            if ax.length<1e-12:return 0
            ax.normalize();pa=[p.dot(ax) for p in P];pb=[p.dot(ax) for p in Q];pen=min(pen,min(max(pa),max(pb))-max(min(pa),min(pb)))
    return max(pen,0)
def unfold(bm,passes=4):
    """#64 follow-up: two neighbouring triangles (sharing a corner) that face opposite ways and lie on top of each other in one
    plane are a fold: a strip 1-2.5 mm high flipped over on a capstone joint, a sliver turned back by the decimation. The QA
    used to see them only where a UV seam split the shared corner. The shortest edge of the smaller triangle is collapsed, which
    takes the flipped sliver out and leaves the surface closed (no hole). Returns the number of edges collapsed."""
    key=lambda v:(round(v.co.x/1e-5),round(v.co.y/1e-5),round(v.co.z/1e-5));done=0;cos_=math.cos(math.radians(3))   # a margin over the QA's 1.5 degrees / 0.5 mm / 1 mm
    for _ in range(passes):
        # neighbours are found through corners at one position, not a BVH self-overlap: Blender's self-overlap skips
        # triangles that share a vertex, which is exactly what a fold is (the first version of this found nothing)
        bm.faces.ensure_lookup_table();bm.normal_update();at={};edges=set()
        for f in bm.faces:
            for v in f.verts:at.setdefault(key(v),[]).append(f)
        seen=set()
        for fs in at.values():
            for x in range(len(fs)):
                for y in range(x+1,len(fs)):
                    a,b=fs[x],fs[y]
                    if a is b or len(a.verts)!=3 or len(b.verts)!=3:continue
                    k=(min(a.index,b.index),max(a.index,b.index))
                    if k in seen:continue
                    seen.add(k)
                    if a.normal.length<1e-9 or b.normal.length<1e-9 or a.normal.dot(b.normal)>-cos_:continue
                    A=[v.co for v in a.verts];B=[v.co for v in b.verts]
                    if max(abs((p-A[0]).dot(a.normal)) for p in B)>.001 or _sat(A,B,a.normal)<.0008:continue
                    f=a if a.calc_area()<=b.calc_area() else b;edges.add(min(f.edges,key=lambda e:e.calc_length()))
        if not edges:break
        bmesh.ops.collapse(bm,edges=list(edges));done+=len(edges)
        bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3])
    return done
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
def finish(name,bm,mat,grp,scale=.4,uv=None):
    """tiled UV: box projection on principal axes, or uv=(u,v) callables of a world point for cylinders"""
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces);lay=bm.loops.layers.uv.get('Tiled') or bm.loops.layers.uv.new('Tiled')
    if uv:
        for f in bm.faces:
            us=[uv[0](l.vert.co) for l in f.loops];m=max(us)-min(us)
            if len(uv)>2 and m>uv[2]/2:us=[u+uv[2] if u<0 else u for u in us]
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
def cyl_uv(r):return (lambda p:math.atan2(p.y,p.x)*r,lambda p:p.z,math.tau*r)   # third value: the u period, to unwrap faces on the seam
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
    su=[0.]
    for a_,b_ in zip(pts,pts[1:]):su.append(su[-1]+(b_-a_).length)
    lay=bm.loops.layers.uv.new('Strip');flag=bm.faces.layers.int.new('strip');circ=math.tau*max(radii or [r]);Lmax=max(10*circ,.05)
    for i,(a,b) in enumerate(zip(rings,rings[1:])):
        for k in range(sides):
            f=bm.faces.new((a[k],a[(k+1)%sides],b[(k+1)%sides],b[k]));f[flag]=1
            sg=int(su[i]/Lmax);u0=sg*Lmax   # long tubes are cut into pieces of at most ~10 circumferences so they pack
            for l,(uu,vv) in zip(f.loops,((su[i],k),(su[i],k+1),(su[i+1],k+1),(su[i+1],k))):l[lay].uv=(uu-u0,vv/sides*circ+sg*circ*1.5)
    if caps:   # caps keep the smart-project UV (a small island of their own); folding them onto the end ring gave zero-area UV faces
        for ring,rev in ((rings[0],True),(rings[-1],False)):bm.faces.new(list(reversed(ring)) if rev else ring)
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
def apply(o,m):
    bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.modifier_apply(modifier=m.name);o.select_set(False)
def subdiv(o,cuts):
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.subdivide_edges(bm,edges=bm.edges,cuts=cuts,use_grid_fill=True);bm.to_mesh(o.data);bm.free()
def jitter(o,amt,seed=1,freq=6):
    """displace along the normals of the undisplaced mesh: read all normals first (Blender 4 recomputes
    vertex normals from the half-moved mesh if they are read inside the loop, which folds the surface)"""
    r=random.Random(seed);ph=[r.uniform(0,9) for _ in range(6)];me=o.data;me.update();n=len(me.vertices)
    co=np.empty(n*3);me.vertices.foreach_get('co',co);co=co.reshape(n,3);nr=np.empty(n*3);me.vertices.foreach_get('normal',nr);nr=nr.reshape(n,3)
    x,y,z=co[:,0],co[:,1],co[:,2]
    d=amt*(np.sin(x*freq+ph[0])*np.sin(y*freq*1.3+ph[1])+.6*np.sin(z*freq*.8+ph[2])*np.sin((x+y)*freq*2.1+ph[3]))
    me.vertices.foreach_set('co',(co+nr*d[:,None]).ravel());me.update()
def box(name,size,center,mat,grp,bev=.01,segs=2,scale=.4,cuts=0,jit=0,seed=1,rot=None):
    o=finish(name,box_bm(size),mat,grp,scale)
    if cuts:subdiv(o,cuts)
    if bev:bevel(o,bev,segs)
    if jit:jitter(o,jit,seed,freq=4/max(size))
    if rot:o.data.transform(rot)
    o.data.transform(Matrix.Translation(center));return o
def beam(name,a,b,w,h,mat,grp,bev=.008,up=(0,0,1),scale=.5):
    """rectangular member from a to b (w across, h along `up`)"""
    a,b=Vector(a),Vector(b);t=(b-a);L=t.length;t.normalize();up=Vector(up);s=t.cross(up).normalized();u=s.cross(t)
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
    for i,c in enumerate(cutters):
        keep=o.data.copy();n0=len(o.data.polygons);vol0=o.dimensions.x*o.dimensions.y*o.dimensions.z;ok=False
        for solver in ('EXACT','FAST'):   # EXACT, hole tolerant; fall back to FAST if it returns nothing or collapses the mesh
            m=o.modifiers.new('carve','BOOLEAN');m.operation='DIFFERENCE';m.object=c;m.solver=solver
            if solver=='EXACT':m.use_hole_tolerant=True
            apply(o,m);o.data.update()
            if len(o.data.polygons)>.3*n0 and o.dimensions.x*o.dimensions.y*o.dimensions.z>.5*vol0:ok=True;break
            old=o.data;o.data=keep.copy();bpy.data.meshes.remove(old)
        if not ok:print(f'carve: {o.name} cutter {i} skipped (it would have collapsed the mesh)')
        bpy.data.meshes.remove(keep);bpy.data.objects.remove(c)
        assert len(o.data.polygons)>0,f'{o.name}: boolean {i} emptied the mesh'
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

# ---------------- shared shapes ----------------
def boulder(name,size,center,mat,grp,seed,sub=4,flat=.35,jit=.06,rot=0):
    """water-worn stone: ellipsoid with a flattened (sunk) bottom, two octaves of soft lumps"""
    bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=sub,radius=.5)
    r=random.Random(seed);k=[r.uniform(-.12,.12) for _ in range(4)]
    for v in bm.verts:
        x,y,z=v.co;z2=max(z,-.5+flat*.5)   # flattened underside: half sunk into the gravel
        v.co=Vector((x*size[0]*(1+k[0]*z),y*size[1]*(1+k[1]*x),z2*size[2]*(1+k[2]*y)))
    o=finish(name,bm,mat,grp,.5);m=min(size)
    jitter(o,jit*m,seed,1.6/m);jitter(o,jit*.35*m,seed+7,4.2/m)
    o.data.transform(Matrix.Rotation(rot,4,'Z'))
    lo=min(v.co.z for v in o.data.vertices);o.data.transform(Matrix.Translation(Vector(center)-Vector((0,0,lo))));return o
def rock(name,size,center,mat,grp,seed,cuts=16,flat=.3,round_=.03,lumps=.04,ncracks=2,top_bias=.5,rot=0,vox=90,target=None,segs=2,frac=(.78,.93)):
    """fractured granite: an ellipsoid cut by cleavage planes (flat facets, steep sides, sloped tops), a flat bed,
    softened edges (bevel + voxel remesh), broad uneven planes and grain, and a few long cracks pressed in"""
    r=random.Random(seed);sx,sy,sz=size;m=min(size)
    bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=3,radius=.5)
    for v in bm.verts:v.co=Vector((v.co.x*sx,v.co.y*sy,v.co.z*sz))
    def cut(nv,frac):
        nv=Vector(nv).normalized();d=max(v.co.dot(nv) for v in bm.verts)*frac
        bmesh.ops.bisect_plane(bm,geom=bm.verts[:]+bm.edges[:]+bm.faces[:],plane_co=nv*d,plane_no=nv,clear_outer=True)
        ed=[e for e in bm.edges if len(e.link_faces)<2]
        if ed:bmesh.ops.holes_fill(bm,edges=ed,sides=0)
    for i in range(cuts):
        a=r.uniform(0,math.tau);el=r.uniform(-.15,.9) if r.random()<top_bias else r.uniform(-.2,.35);c=math.cos(math.asin(el))
        cut((math.cos(a)*c,math.sin(a)*c,el),r.uniform(*frac))
    cut((0,0,-1),1-flat)
    me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free();o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o)
    bv=o.modifiers.new('b','BEVEL');bv.width=m*round_;bv.segments=segs;bv.limit_method='ANGLE'
    rm=o.modifiers.new('r','REMESH');rm.mode='VOXEL';rm.voxel_size=m/vox
    bpy.context.view_layer.objects.active=o
    for md in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=md.name)
    me=o.data;n=len(me.vertices);co=np.empty(n*3);me.vertices.foreach_get('co',co);co=co.reshape(n,3)
    nr=np.empty(n*3);me.vertices.foreach_get('normal',nr);nr=nr.reshape(n,3);zb=co[:,2].min();bed=co[:,2]<zb+m*.01
    vn=lambda f,s,oc=3:vnoise3(co[:,None,:].astype(np.float32),f,s,oc)[:,0]
    d=lumps*m*(vn(1.6/m,seed)-.5)*2+.012*m*(vn(9/m,seed+1)-.5)*2;d[bed]=0
    co=co+nr*d[:,None];co[:,2]=np.maximum(co[:,2],zb);me.vertices.foreach_set('co',co.ravel());me.update()
    o.data.transform(Matrix.Rotation(rot,4,'Z'));bpy.context.scene.collection.objects.unlink(o)
    bm=bmesh.new();bm.from_mesh(o.data);bpy.data.objects.remove(o);o=finish(name,bm,mat,grp,.5)
    for k in range(ncracks):   # long meandering cracks from the upper part down the side
        co=np.array([v.co[:] for v in o.data.vertices]);top=co[np.argmax(co@np.array([r.uniform(-1,1),r.uniform(-1,1),1.5]))]
        pts=surface_walk(o,top,(r.uniform(-1,1),r.uniform(-1,1),-.6),m*r.uniform(.5,1.0),m*.02,seed+k,.45);groove(o,pts,m*.014,m*.012)
    if target and len(o.data.polygons)>target:
        dm=o.modifiers.new('d','DECIMATE');dm.ratio=target/len(o.data.polygons);bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier='d')
    lo=min(v.co.z for v in o.data.vertices);o.data.transform(Matrix.Translation(Vector(center)-Vector((0,0,lo))));return o
def moss_pad(name,o,mat,grp,seed,cover=.45,thick=.012,up=.45,zmin=.35,freq=4,zmax=1.01):
    """cushions of moss lying on the up-facing part of a stone: the selected faces copied, lifted along their normals
    by a lumpy thickness that tapers to zero at the patch edge, so the pad melts into the stone"""
    bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();m=min(o.dimensions);zs=[v.co.z for v in bm.verts];z0,z1=min(zs),max(zs)
    C=np.array([f.calc_center_median()[:] for f in bm.faces],np.float32)
    nz=np.array([f.normal.z for f in bm.faces]);nse=vnoise3(C[:,None,:],freq/m,seed,3)[:,0]
    keep=(nz>up)&(nse>1-cover)&(C[:,2]>z0+(z1-z0)*zmin)&(C[:,2]<z0+(z1-z0)*zmax)
    bmesh.ops.delete(bm,geom=[f for f,k in zip(bm.faces,keep) if not k],context='FACES')
    loose=[v for v in bm.verts if not v.link_faces]
    if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
    if len(bm.faces)<8:bm.free();return None
    ring={v:0 for v in bm.verts if v.is_boundary};front=list(ring)
    for k in range(1,6):   # distance from the patch edge in edge rings
        nxt=[]
        for v in front:
            for e in v.link_edges:
                w=e.other_vert(v)
                if w not in ring:ring[w]=k;nxt.append(w)
        front=nxt
    P=np.array([v.co[:] for v in bm.verts],np.float32);hi=vnoise3(P[:,None,:],freq*6/m,seed+1,2)[:,0]
    for v,h in zip(bm.verts,hi):
        t=min(ring.get(v,6),6)/6;v.co=v.co+v.normal*thick*(t**.7)*(.45+.8*h)
    return finish(name,bm,mat,grp,.15)
def vcell(P,cell,seed):
    """Voronoi cells of baked positions: (F1 distance in cell units, per-cell hash) — angular colour patches, lichen"""
    Q=P/cell;I=np.floor(Q).astype(np.int64);b1=np.full(Q.shape[:-1],9.,np.float32);hid=np.zeros(Q.shape[:-1],np.int64)
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            for dz in (-1,0,1):
                C=I+np.array([dx,dy,dz]);h=(C[...,0]*73856093)^(C[...,1]*19349663)^(C[...,2]*83492791)^(seed*2654435761);h=(h^(h>>13))*1274126177
                fp=np.stack([((h>>s)&1023)/1023. for s in (0,10,20)],-1);dd=np.linalg.norm(Q-(C+.15+.7*fp),axis=-1).astype(np.float32)
                k=dd<b1;b1=np.where(k,dd,b1);hid=np.where(k,h,hid)
    return b1,hid
def surface_walk(o,start,direction,length,step,seed,wobble=.5):
    """a crack: walk across the surface of `o` from start, wobbling, snapped to the surface each step"""
    from mathutils.bvhtree import BVHTree
    bpy.context.view_layer.update();bvh=BVHTree.FromObject(o,bpy.context.evaluated_depsgraph_get());r=random.Random(seed)
    p=bvh.find_nearest(Vector(start))[0];d=Vector(direction).normalized();pts=[p.copy()]
    for i in range(int(length/step)):
        n=bvh.find_nearest(p)[1];d=(d-n*d.dot(n)).normalized();side=n.cross(d)
        d=(d+side*r.uniform(-wobble,wobble)).normalized();p=bvh.find_nearest(p+d*step)[0];pts.append(p.copy())
    return pts
def groove(o,pts,w,depth):
    """press a polyline into the mesh along vertex normals (a hairline crack)"""
    P=np.array([p[:] for p in pts]);me=o.data;me.update();n=len(me.vertices)
    co=np.empty(n*3);me.vertices.foreach_get('co',co);co=co.reshape(n,3);nr=np.empty(n*3);me.vertices.foreach_get('normal',nr);nr=nr.reshape(n,3)
    d=np.full(n,1e9)
    for a,b in zip(P,P[1:]):
        ab=b-a;t=np.clip((co-a)@ab/max(ab@ab,1e-12),0,1);d=np.minimum(d,np.linalg.norm(co-(a+t[:,None]*ab),axis=1))
    k=np.clip(1-d/w,0,1)**1.5;co=co-nr*(depth*k)[:,None];me.vertices.foreach_set('co',co.ravel());me.update()
def tuft(name,base,M,grp,seed,n=9,h=.18,mat='grass'):
    r=random.Random(seed)
    for i in range(n):
        a=r.uniform(0,math.tau);lean=r.uniform(.15,.55);d=(math.cos(a)*lean,math.sin(a)*lean,1)
        leaf(f'{name}_{i}',Vector(base)+Vector((r.uniform(-.015,.015),r.uniform(-.015,.015),0)),d,(-math.sin(a),math.cos(a),0),h*r.uniform(.6,1.1),.012,M[mat],grp,curl=.35,seg=5)
def fern(name,base,M,grp,seed,n=6,L=.32,up=(0,0,1),mat='fern'):
    """fronds: a curved midrib with paired leaflets shrinking to the tip"""
    r=random.Random(seed);up=Vector(up).normalized();u=up.orthogonal().normalized();v=up.cross(u)
    for i in range(n):
        a=math.tau*i/n+r.uniform(-.3,.3);out=(u*math.cos(a)+v*math.sin(a));LL=L*r.uniform(.7,1.05);pts=[]
        for k in range(7):
            t=k/6;pts.append(Vector(base)+out*LL*t*.95+up*LL*.55*math.sin(t*2.3))
        tube(f'{name}_rib{i}',pts,.0025,M[mat],grp,4,.1)
        for k in range(1,12):
            t=k/12;seg=min(5,int(t*6));p=pts[seg].lerp(pts[seg+1],t*6-seg);d=(pts[seg+1]-pts[seg]).normalized();s=d.cross(up).normalized()
            for sgn in (-1,1):leaf(f'{name}_l{i}_{k}{sgn}',p,(s*sgn+d*.35).normalized(),up,LL*.22*(1-t*.75),.016*(1-t*.6),M[mat],grp,curl=.12,seg=4)
def pebbles(pfx,M,grp,seed,centre,r0,r1,n,size=(.03,.07),mat='gravel',avoid=None):
    r=random.Random(seed)
    for i in range(n):
        a=r.uniform(0,math.tau);rr=r.uniform(r0,r1);c=(centre[0]+rr*math.cos(a),centre[1]+rr*math.sin(a),0)
        if avoid and avoid(c):continue
        s=r.uniform(*size);boulder(f'{pfx}{i:03d}',(s*r.uniform(1,1.6),s,s*r.uniform(.5,.8)),c,M[mat],grp,seed*100+i,sub=2 if s<.045 else 3,jit=.1,rot=r.uniform(0,6))

# ---------------- UP01 斷流石壩 ----------------
UP01_SAG=.8
def up01_bend(x):   # plan curve: the weir arches upstream (+Y); flat over the sluice frame so the gate slides straight
    a=max(0,abs(x)-1.3)/4.9;return UP01_SAG*(1-min(a,1.3)**2)
def UP01(M):
    """old low granite weir, arched upstream: dressed courses on the steep downstream face, pitched rubble on the upstream slope,
    coping slabs (walkable crest 0.9 m), a stone sluice frame with a timber windlass, a plank gate (own pivot, lifts 1.2 m),
    the sluice choked by silt, broken logs, dead branches and water weed (Debris layer), bank boulders tying into the rocks."""
    W='Weir';Gt='Gate';D='Debris';P='Plants';r=random.Random(301)
    meta={'moss_low':.6,'moss_h':.9,'moss_top':.35,'moss_cav':.6,'soil':.15,'moss_scale':.6,'collisions':{},'notes':{}}
    CREST=2.2;SILL=.25;HW=6.2;OPEN=.7;PIL=(.7,1.2);PY=(.2,.7);GY=.45
    yd=lambda z:-.95+.25*z/2.2          # downstream face (batter)
    yu=lambda z:1.9-1.2*z/2.2           # upstream slope
    # core: one slice per metre so the collision follows the arch
    xs=[-HW,-5.2,-4.2,-3.2,-2.2,-1.2,-OPEN];xs=xs+[-x for x in reversed(xs)]
    k=0
    for a,b in zip(xs,xs[1:]):
        if a>=-OPEN-1e-6 and b<=OPEN+1e-6:continue
        sec=[(yd(0)+.06,0),(yu(0)-.04,0),(yu(2.18)-.04,2.18),(yd(2.18)+.06,2.18)]
        bm=bmesh.new();solid_prism(bm,[(a,y,z) for y,z in sec],(b-a,0,0));o=finish(f'UP01_Core{k:02d}',bm,M['mortar'],W,.6);subdiv(o,2);jitter(o,.01,k,3);k+=1
    bm=bmesh.new();solid_prism(bm,[(-OPEN,y,z) for y,z in [(yd(0)+.06,0),(yu(0)-.04,0),(yu(SILL)-.04,SILL),(yd(SILL)+.06,SILL)]],(2*OPEN,0,0));o=finish('UP01_Sill',bm,M['granite'],W,.5);subdiv(o,2);jitter(o,.006,3,4)
    # downstream face: dressed courses, staggered joints
    z=0;row=0;blocks=[]
    while z<2.0:
        h=min(r.uniform(.28,.38),2.04-z);x=-HW+r.uniform(0,.35)*(row%2)
        while x<HW-.05:
            L=r.uniform(.45,.85);x1=min(x+L,HW)
            if not (x1>-OPEN-.28 and x<OPEN+.28):   # the outlet and its jambs
                c=((x+x1)/2,yd(z+h/2)+.15-r.uniform(0,.02),z+h/2)
                o=box(f'UP01_Face{row}_{len(blocks)}',(x1-x-.045,.30,h-.045),(0,0,0),M[r.choice(('granite','granite_b','granite_c'))],W,bev=.045,cuts=2,jit=.013,seed=len(blocks),scale=.5,rot=Matrix.Rotation(-math.atan2(.25,2.2),4,'X'))
                o.data.transform(Matrix.Translation(c));blocks.append((o,c))
            x=x1
        z+=h;row+=1
    new=r.choice([o for o,c in blocks if .6<c[2]<1.6 and abs(c[0])>2])   # one later replacement block, paler
    new.data.materials[0]=M['granite_new'];new.name='UP01_FaceNew'
    for sx in (-1,1):   # outlet jambs: tall dressed stones on both sides of the outlet
        for j,(z0,z1) in enumerate(((0,SILL+.7),(SILL+.7,1.4),(1.4,2.02))):
            box(f'UP01_Jamb{sx}{j}',(.30,.42,z1-z0-.02),(sx*(OPEN+.14),yd((z0+z1)/2)+.2,(z0+z1)/2),M['granite'],W,bev=.03,cuts=2,jit=.005,seed=60+j+sx)
    # upstream slope: pitched rubble
    zz=.06;row=0;ang=math.atan2(1.2,2.2)   # first row starts a little up so its tilted corner stays above the bed
    while zz<2.0:
        h=.42;x=-HW+.2*(row%2);rot=Matrix.Rotation(ang,4,'X')
        while x<HW-.05:
            L=r.uniform(.35,.6);x1=min(x+L,HW)
            if x1<-PIL[1] or x>PIL[1]:
                zc=zz+h/2;c=((x+x1)/2,yu(zc)-.12,zc)
                o=box(f'UP01_Pitch{row}_{int((x+7)*10)}',(x1-x-.04,.28,h/math.cos(ang)-.05),(0,0,0),M[r.choice(('granite','granite_b','granite_b'))],W,bev=.035,cuts=2,jit=.01,seed=row*31+int(x*10),scale=.5,rot=rot)
                o.data.transform(Matrix.Translation(c))
            x=x1
        zz+=h*.95;row+=1
    # coping: downstream walk row everywhere; upstream row except at the frame; one long slab bridges the outlet
    for (y0,y1),skip in (((-.73,PY[0]),OPEN+.18),((PY[0],.73),PIL[1])):
        x=-HW
        while x<HW-.05:
            L=r.uniform(.7,1.1);x1=min(x+L,HW)
            if x<-skip<x1:x1=-skip
            if x<skip and x1>-skip:x=skip;continue
            box(f'UP01_Coping{int((x+7)*10)}_{int(y0*10)}',(x1-x-.03,y1-y0-.02,.18),((x+x1)/2,(y0+y1)/2,CREST-.09+.005),M[r.choice(('granite','granite_b','granite_c'))],W,bev=.03,cuts=2,jit=.004,seed=int(x*10)+3)
            x=x1
    box('UP01_Bridge',(2*OPEN+.36,PY[0]+.73-.02,.2),(0,(-.73+PY[0])/2,CREST-.1+.005),M['granite'],W,bev=.03,cuts=3,jit=.003,seed=88)
    # sluice frame: stacked dressed stones with a gate groove on the inner face, cap stones, rope-worn notches
    for sx in (-1,1):
        z=SILL
        for h,j in ((.9,0),(.85,1),(.55,2),(.45,3)):
            o=box(f'UP01_Pillar{sx}{j}',(PIL[1]-PIL[0]-.01,PY[1]-PY[0]-.01,h-.015),(sx*(PIL[0]+PIL[1])/2,(PY[0]+PY[1])/2,z+h/2),M['granite'],W,bev=.025,cuts=2,jit=.004,seed=70+j+sx)
            carve(o,[cutter(box_bm((.12,.13,h+.1),(sx*PIL[0],GY,z+h/2)))]);z+=h
        o=box(f'UP01_PillarCap{sx}',(.58,.58,.1),(sx*(PIL[0]+PIL[1])/2,(PY[0]+PY[1])/2,z+.05),M['granite'],W,bev=.02,cuts=2,jit=.003,seed=80+sx)
        cs=[]
        for dx in (.06,.13):   # rope-worn grooves on the inner top edge of the cap
            bm=bmesh.new();bmesh.ops.create_cone(bm,cap_ends=True,segments=12,radius1=.012,radius2=.012,depth=.7)
            bmesh.ops.rotate(bm,verts=bm.verts,cent=(0,0,0),matrix=Matrix.Rotation(math.pi/2,3,'X'));bmesh.ops.translate(bm,verts=bm.verts,vec=(sx*(PIL[0]+dx),GY,z+.1));cs.append(cutter(bm))
        carve(o,cs)
    zt=SILL+.9+.85+.55+.45+.1   # 3.10: cap top = frame top
    beam('UP01_Beam',(-1.38,GY,zt+.08),(1.38,GY,zt+.08),.18,.16,M['oldwood'],W,bev=.012)
    for sx in (-1,1):
        box(f'UP01_DrumPost{sx}',(.13,.24,.2),(sx*.66,GY+.06,zt+.16+.10),M['oldwood'],W,bev=.012,cuts=2,jit=.003,seed=97+sx)
        for sy in (-1,1):box(f'UP01_BoltPlate{sx}{sy}',(.006,.07,.07),(sx*(.66+.068),GY+.06+sy*.06,zt+.27),M['iron'],W,bev=.002)
        for dz in (-.06,.06):lathe(f'UP01_Bolt{sx}{dz}',[(0,0),(.012,0),(.012,.008),(0,.01)],M['iron'],W,seg=8,center=(sx*(.66+.07),GY+.06,zt+.27+dz*.7))
    lathe('UP01_Drum',[(0,-.62),(.075,-.62),(.085,-.58),(.075,-.54),(.075,.54),(.085,.58),(.075,.62),(0,.62)],M['oldwood'],W,seg=24,cyl=True)
    dr=parts[-1];dr.data.transform(Matrix.Rotation(math.pi/2,4,'Y'));dr.data.transform(Matrix.Translation((0,GY+.06,zt+.27)))
    tube('UP01_Crank',[(.62,GY+.06,zt+.27),(.80,GY+.06,zt+.27),(.80,GY+.06,zt+.12),(.88,GY+.06,zt+.12)],.016,M['iron'],W,8)
    lashing('UP01_RopeCoil',(0,GY+.06,zt+.27),(1,0,0),.075,11,M['hemp'],W,cord=.011)
    for sx in (-1,1):lathe(f'UP01_DrumBand{sx}',[(.079,-.02),(.084,-.02),(.084,.02),(.079,.02)],M['iron'],W,seg=24);o=parts[-1];o.data.transform(Matrix.Rotation(math.pi/2,4,'Y'));o.data.transform(Matrix.Translation((sx*.5,GY+.06,zt+.27)))
    # gate (own pivot at the frame top): five planks, three battens, iron straps, a lifting ring
    GZ=(SILL,1.85);gw=2*OPEN+.08
    for i in range(5):
        x0=-gw/2+gw*i/5;box(f'UP01_Plank{i}',(gw/5-.008,.06,GZ[1]-GZ[0]-r.uniform(0,.03)),(x0+gw/10,GY,(GZ[0]+GZ[1])/2),M['oldwood'],Gt,bev=.006,cuts=2,jit=.002,seed=90+i,scale=.4)
    for j,zz_ in enumerate((.42,1.05,1.65)):
        box(f'UP01_Batten{j}',(gw-.14,.05,.12),(0,GY-.055,zz_),M['oldwood'],Gt,bev=.008,cuts=1,seed=95+j)
        box(f'UP01_Strap{j}',(gw-.3,.012,.05),(0,GY-.086,zz_),M['iron'],Gt,bev=.003)
        for i_ in range(7):box(f'UP01_Rivet{j}_{i_}',(.018,.012,.018),(-(gw-.36)/2+(gw-.36)*i_/6,GY-.095,zz_),M['iron'],Gt,bev=.004)
    tube('UP01_Ring',[(0,GY+.02,GZ[1]-.02)]+[(.03*math.sin(a),GY+.02,GZ[1]+.03-.03*math.cos(a)) for a in np.linspace(0,math.tau,17)][1:],.008,M['iron'],Gt,6,.1)
    rope('UP01_Rope',[(0,GY+.12,zt+.25),(0,GY+.11,zt-.1),(0,GY+.03,GZ[1]+.05)],.010,M['hemp'],W)
    # debris in the sluice mouth: silt banks both sides of the gate, jammed logs, dead branches, a clump of water weed
    boulder('UP01_SiltDownA',(1.5,1.2,1.1),(0,-.2,0),M['silt'],D,311,sub=4,flat=.9,jit=.05)
    boulder('UP01_SiltDownB',(1.2,.8,.55),(.1,yd(.2)+.25,0),M['silt'],D,312,sub=4,flat=.9,jit=.05)
    boulder('UP01_SiltUp',(1.45,1.2,1.75),(0,GY+.8,0),M['silt'],D,313,sub=4,flat=.9,jit=.04)
    def log(name,a,b,r0,seed,mat='deadwood'):
        r_=random.Random(seed);a,b=Vector(a),Vector(b);pts=[a.lerp(b,t)+Vector((0,0,r_.uniform(-.02,.02))) for t in np.linspace(0,1,9)]
        o=tube(name,pts,r0,M[mat],D,14,.3,radii=[r0*r_.uniform(.85,1.1) for _ in pts]);jitter(o,r0*.08,seed,40);return o
    log('UP01_Log0',(-.66,yd(.3)+.25,.30),(.55,yd(1.3)+.9,1.32),.11,401)
    log('UP01_Log1',(-.85,yd(.9)+.42,.86),(.82,yd(.9)+.36,.92),.09,402,'bark')
    log('UP01_Log2',(-.45,GY+1.1,.5),(.6,GY+.17,2.0),.10,403,'bark')   # foot buried in the upstream silt, top leaning on the pillar's inner face (it floated before)
    log('UP01_Log4',(.6,yd(.4)+.3,.45),(-.5,yd(1.5)+.75,1.55),.075,405,'bark')
    log('UP01_Log3',(.68,yd(.2)+.1,.18),(-.2,yd(.2)-.55,.12),.07,404)
    for i in range(28):   # dead branches with a fork, poking out of the jam
        a=Vector((r.uniform(-.6,.6),yd(.8)+r.uniform(.15,1.1),r.uniform(.35,1.75)));d=Vector((r.uniform(-1,1),r.uniform(-1,-.2),r.uniform(-.2,.6))).normalized();L=r.uniform(.5,1.0)
        b=a+d*L;tube(f'UP01_Branch{i}',[a,a.lerp(b,.5)+Vector((0,0,.03)),b],r.uniform(.012,.022),M['deadwood'],D,6,.2,radii=[.02,.015,.007])
        f=a.lerp(b,.55);tube(f'UP01_Twig{i}',[f,f+(d+Vector((r.uniform(-.8,.8),0,.5))).normalized()*L*.35],.008,M['deadwood'],D,5,.1,radii=[.009,.004])
    for i in range(40):   # water weed draped over the cross log, hanging in strands
        x=r.uniform(-.5,.55);base=Vector((x,yd(.9)+.36-.08,.98))
        leaf(f'UP01_Weed{i}',base,(r.uniform(-.2,.2),-.25,-1),(0,-1,0),r.uniform(.25,.5),r.uniform(.025,.045),M['weed'],D,curl=-.3,seg=7)
    # bank boulders: the weir ends run into the rock of both banks; a few fallen stones at the foot
    for sx in (-1,1):
        for j,(dx,dy,s) in enumerate(((.15,-.45,(1.45,1.25,1.9)),(.3,.55,(1.3,1.55,2.45)),(.45,-.75,(.85,.75,.7)),(.2,1.25,(1.2,.95,1.5)))):
            rock(f'UP01_Bank{sx}{j}',s,(sx*(HW+dx-.33),dy,0),M['granite'],W,500+j+sx*10,cuts=18,flat=.25,round_=.035,lumps=.05,ncracks=3,rot=j*.9,vox=55,target=5000)
    for j in range(12):   # fallen face blocks: squared stones with broken arrises, some tilted
        x=r.choice((-1,1))*r.uniform(1.4,5.6);sz=(r.uniform(.38,.6),r.uniform(.28,.4),r.uniform(.2,.32))
        rock(f'UP01_Fallen{j}',sz,(x,yd(0)-r.uniform(.12,.28),0),M[r.choice(('granite','granite_b'))],W,600+j,cuts=8,frac=(.9,.97),flat=.15,round_=.04,lumps=.02,ncracks=1,rot=r.uniform(-.5,.5),vox=35,target=900)
    for j in range(80):   # rubble and cobbles heaped along the downstream foot (round three: denser, as in the reference; kept inside the 4 m depth)
        x=r.uniform(-6.2,6.2)
        if abs(x)<1.25:continue
        sz=r.uniform(.08,.26);rock(f'UP01_Rubble{j}',(sz*r.uniform(1,1.5),sz,sz*r.uniform(.5,.8)),(x,yd(0)-r.uniform(.0,.18),0),M[r.choice(('granite','granite_b','creekstone'))],W,640+j,cuts=7,flat=.3,round_=.08,ncracks=0,rot=r.uniform(0,3),vox=18,target=220)
    for j in range(16):   # larger talus stones heaped against the foot, as in the reference (round three)
        x=r.choice((-1,1))*r.uniform(1.5,5.8);sz=(r.uniform(.4,.6),r.uniform(.28,.36),r.uniform(.25,.4))
        rock(f'UP01_Talus{j}',sz,(x,yd(0)+.05-r.uniform(0,.1),0),M[r.choice(('granite','granite_b','creekstone'))],W,760+j,cuts=9,flat=.25,round_=.06,lumps=.03,ncracks=1,rot=r.uniform(0,3),vox=30,target=900)
    # ferns in the joints of the downstream face, grass on the bank rocks and the crest
    for j in range(20):
        x=r.choice((-1,1))*r.uniform(1.4,5.8);z=r.uniform(.15,1.95);fern(f'UP01_Fern{j}',(x,yd(z)-.02,z),M,P,700+j,n=5,L=r.uniform(.18,.34),up=(0,-.7,.7))
    for j in range(14):   # grass tufts in the face joints
        x=r.choice((-1,1))*r.uniform(1.4,5.8);z=r.uniform(.2,1.9);tuft(f'UP01_JointTuft{j}',(x,yd(z)-.03,z),M,P,760+j,n=6,h=.13)
    for j in range(22):
        x=r.choice((-1,1))*r.uniform(5.4,6.4);tuft(f'UP01_Tuft{j}',(x,r.uniform(-.9,1.2),0),M,P,800+j,n=8,h=.22)
    for j in range(26):   # ferns and grass among the rubble at the downstream foot
        x=r.choice((-1,1))*r.uniform(1.4,6.0);c=(x,yd(0)-r.uniform(.05,.2),0)
        if j%2:fern(f'UP01_FootFern{j}',c,M,P,900+j,n=6,L=r.uniform(.2,.32))
        else:tuft(f'UP01_FootTuft{j}',c,M,P,940+j,n=9,h=r.uniform(.14,.24))
    for j in range(5):
        x=r.choice((-1,1))*r.uniform(1.5,5.5);tuft(f'UP01_CrestTuft{j}',(x,r.uniform(.25,.65),CREST),M,P,850+j,n=6,h=.14)
    for j in range(9):   # ivy hanging over the coping down the downstream face
        x=r.choice((-1,1))*r.uniform(1.3,5.6);L=r.uniform(.6,1.6)
        for v_ in range(r.randint(2,4)):
            xx=x+r.uniform(-.25,.25);pts=[Vector((xx,yd(CREST)-.04,CREST+.01))]
            for t in np.linspace(.1,1,8):z_=CREST-L*r.uniform(.8,1)*t;pts.append(Vector((xx+.05*math.sin(t*7+v_),yd(z_)-.025,z_)))
            tube(f'UP01_Vine{j}_{v_}',pts,.004,M['bark'],P,5,.1)
            for k_,p_ in enumerate(pts[1:]):
                for sgn in (-1,1):leaf(f'UP01_Ivy{j}_{v_}_{k_}{sgn}',p_,(sgn*.8,-.5,-.3),(0,-1,.2),r.uniform(.05,.08),r.uniform(.035,.05),M['fern'],P,curl=.15,seg=4)
    # bend everything into the arch
    for o in parts:
        for v in o.data.vertices:v.co.y+=up01_bend(v.co.x)
    meta['pivots']={Gt:('UP01_Gate',(0,GY+UP01_SAG,zt))}
    hull=lambda *p:{'type':'hull','parts':list(p)}
    meta['collisions']={'Collision':[hull(f'UP01_Core{i:02d}') for i in range(k)]+[hull('UP01_Sill'),hull('UP01_Bridge'),hull('UP01_Beam'),hull('UP01_Drum')]
                                    +[hull(f'UP01_Pillar{sx}') for sx in (-1,1)]+[hull(f'UP01_PillarCap{sx}') for sx in (-1,1)]+[hull(f'UP01_Jamb{sx}') for sx in (-1,1)]
                                    +[hull(o.name) for o in parts if o.name.startswith('UP01_Coping')]+[hull(f'UP01_Bank{sx}{j}') for sx in (-1,1) for j in range(4)],
                        'Collision_Debris':[hull('UP01_SiltDownA'),hull('UP01_SiltDownB'),hull('UP01_SiltUp')]+[hull(f'UP01_Log{i}') for i in range(5)],
                        'Collision_Gate':[hull('UP01_Plank'),hull('UP01_Batten')]}
    meta['collision_parent']={'Collision_Gate':Gt}
    meta['heights']={'downstream_bed_z':0,'sill_z':SILL,'crest_walk_z':round(CREST+.005,3),'crest_walk_width_m':.92,'waterline_upstream_z':1.8,
                     'gate_closed_z':list(GZ),'gate_lift_m':1.2,'gate_open_z':[round(GZ[0]+1.2,3),round(GZ[1]+1.2,3)],'frame_top_z':round(zt,3),'upstream_face_below_waterline_m':1.8}
    meta['states']={'blocked':'Debris + Collision_Debris visible, gate down (default)','cleared':'hide UP01_Debris_* and UP01_Collision_Debris',
                    'open':'move UP01_Gate_LOD0/1/2 and UP01_Collision_Gate (all four have their origin at the frame top, see pivots) up 1.2 m'}
    meta['notes']={'front':'-Y (Blender) = downstream face, where the player walks up the dry creek','water':'not modelled; still pool upstream at waterline_upstream_z',
                   'rope':'the windlass rope is static (part of Weir); when the gate lifts it can be hidden or scaled by the scene'}
    return meta

# ---------------- UP02 溫石 ×3 ----------------
WARM_AMBER=np.array([1.0,.58,.22])
def warm_stone(pid,M,size,seed,comps,crack_starts,plants):
    S='Stone';P='Plants';r=random.Random(seed);meta={'moss_low':.25,'moss_h':.3,'moss_top':.2,'moss_cav':.25,'soil':.06,'cracks':[],'moss_col':(.30,.33,.17),'wear':.35}
    o=rock(f'{pid}_Main',size,(0,0,0),M['creekstone'],S,seed,cuts=7,flat=.4,round_=.22,segs=5,frac=(.86,.95),lumps=.035,ncracks=0,target=12000)
    for k,(st,d,L) in enumerate(crack_starts):
        pts=surface_walk(o,st,d,L,.012,seed+k,.35);meta['cracks'].append([p[:] for p in pts])
    for j,(sz,c) in enumerate(comps):rock(f'{pid}_Comp{j}',sz,c,M['creekstone'],S,seed+20+j,cuts=6,flat=.45,round_=.22,segs=4,frac=(.86,.95),ncracks=0,rot=r.uniform(0,3),vox=45,target=2000)
    moss_pad(f'{pid}_MossPad',o,M['moss'],S,seed+5,cover=.55,thick=min(size)*.03,up=.35,zmin=.3)
    R0=max(size[0],size[1])/2;lim=LIMITS[pid]
    inside=lambda c:abs(c[0])>lim[0]/2-.05 or abs(c[1])>lim[1]/2-.05
    pebbles(f'{pid}_Gravel',M,'Gravel',seed+40,(0,0),R0*.6,R0*1.2,int(125*R0/.4),avoid=inside)
    for j,(c,kind) in enumerate(plants):
        if kind=='fern':fern(f'{pid}_Fern{j}',c,M,P,seed+60+j,n=6,L=.11)
        else:tuft(f'{pid}_Tuft{j}',c,M,P,seed+70+j,n=8,h=.14)
    for j in range(22):   # grass and small ferns tucked against the foot of the stone all round
        a=math.tau*j/22+r.uniform(-.15,.15);c=(size[0]/2*.86*math.cos(a),size[1]/2*.86*math.sin(a),0)   # just under the stone's bulge, so they stay inside the size limit
        if abs(c[0])>lim[0]/2-.09 or abs(c[1])>lim[1]/2-.09:continue
        if j%2==0:fern(f'{pid}_RingFern{j}',c,M,P,seed+80+j,n=6,L=.14)
        else:tuft(f'{pid}_RingTuft{j}',c,M,P,seed+90+j,n=9,h=r.uniform(.09,.16))
    meta['sockets']={'Socket_Steam':(0,0,max(v.co.z for v in o.data.vertices)+.01)}
    meta['collisions']={'Collision':[{'type':'hull','parts':[f'{pid}_Main'],'simplify':8}]} if size[0]>=.7 else {}
    meta['state']={'prop':'warmth','param':'_Warmth','default':0,'export':0,'range':[0,1],'emit_expr':'0.12*s*s'}
    meta['notes']={'warmth':'_Warmth 0 = ordinary creek stone; 1 = faint amber in the hairline cracks and a small ring of dried, yellowed moss. '
                   'Base colour = lerp(Albedo, Albedo_Warm, _Warmth); Emission = Emission map x (0.12 * _Warmth^2). WarmthMask: R crack, G dried ring.'}
    return meta
def UP02_01(M):
    """溫石・大 · long rounded stone (0.8 m), two hairline cracks, a small companion stone and a fern"""
    return warm_stone('UP02_01',M,(.70,.52,.70),2101,[((.2,.17,.13),(.33,-.14,0)),((.14,.12,.09),(-.36,.17,0))],
                      [((-.25,-.2,.25),(1,.3,-.4),.5),((.12,.1,.48),(.2,-1,-.6),.3)],[((-.33,.2,0),'fern'),((.37,.08,0),'tuft')])
def UP02_02(M):
    """溫石・中 · taller egg-shaped stone with one crack running over the top"""
    return warm_stone('UP02_02',M,(.50,.42,.62),2202,[((.18,.15,.12),(.25,-.15,0))],
                      [((-.05,-.2,.4),(.1,1,-.1),.55)],[((-.29,.15,0),'fern'),((.24,.2,0),'tuft')])
def UP02_03(M):
    """溫石・小 · low flat stone, a short forked crack, two pebbles beside it"""
    return warm_stone('UP02_03',M,(.42,.34,.2),2303,[((.12,.1,.08),(.21,.09,0)),((.09,.08,.06),(-.2,-.1,0))],
                      [((-.12,0,.2),(1,.2,0),.28),((.02,.02,.2),(.2,-1,-.2),.14)],[((.05,.19,0),'tuft')])
def warm_paint(meta):
    def paint(g,col,rough,q,onrm,ao,cav,edge,m,filled,glow,noise,RES):
        ex={};one=np.ones(col.shape[:2],np.float32)
        P_=q.astype(np.float32);ring=np.clip(1-np.hypot(q[...,0],q[...,1])/.5,0,1)*np.clip(1-q[...,2]/.35,0,1)*filled
        if g=='Stone':
            v1=vnoise3(P_,3,21,3);v2=vnoise3(P_,11,22,2)   # tonal patches: cooler blue-grey and warmer ochre areas on the stone
            col=col*(.82+.3*v1[...,None])*(1+np.array([.05,.0,-.06])*(v2[...,None]-.5)*2)
            d=np.min([seg_dist(P_,c) for c in meta['cracks']],axis=0)
            crack=np.clip(1-d/.006,0,1)*filled;halo=np.clip(1-d/.03,0,1)*filled
            col=col*(1-.5*crack[...,None])+np.array([.10,.08,.06])*.5*crack[...,None]
            dry=np.clip(m*2.5+.55*np.clip(1-q[...,2]/.16,0,1)*np.clip((vnoise3(P_,14,23,2)-.3)*2.5,0,1),0,1)*ring
            warm=col*(1-.8*dry[...,None])+np.array([.60,.50,.22])*(.65+.35*noise[...,None])*.8*dry[...,None]
            warm=warm*(1-.2*crack[...,None])+np.array([.50,.36,.22])*.2*crack[...,None]+np.array([.015,.008,0])*halo[...,None]
            ex['Albedo_Warm']=np.dstack([np.clip(warm,0,1),one]);ex['WarmthMask']=np.dstack([np.maximum(crack,.25*halo),dry,0*one,one])
            ex['Emission']=np.dstack([np.clip(WARM_AMBER*(.8*crack+.08*halo)[...,None],0,1),one])
        elif g=='Plants':   # the tufts inside the ring dry and yellow too
            ex['Albedo_Warm']=np.dstack([np.clip(col*(1-.5*ring[...,None])+np.array([.56,.48,.22])*.5*ring[...,None],0,1),one])
            ex['WarmthMask']=np.dstack([0*one,ring,0*one,one])
        return col,rough,ex
    return paint

# ---------------- UP03 水位刻痕石樁 ----------------
UP03_LINES=[]
def UP03(M):
    """square granite post, 7 carved level lines of different depths with a dot each, a small wave sign by the top line,
    chipped top corner, a dark old waterline stain high up, lichen; moss grows inside the grooves"""
    S='Stone';P='Plants';r=random.Random(303);meta={'moss_low':.8,'moss_h':.3,'moss_top':.5,'moss_cav':.2,'soil':.08,'wear':.5}
    w,d,h=.34,.29,1.33
    o=box('UP03_Post',(w,d,h),(0,0,h/2),M['granite'],S,bev=.012,cuts=4,scale=.5)
    rm=o.modifiers.new('r','REMESH');rm.mode='VOXEL';rm.voxel_size=.008;apply(o,rm)   # even, dense surface for the spalls
    me=o.data;nv=len(me.vertices);co=np.empty(nv*3);me.vertices.foreach_get('co',co);co=co.reshape(nv,3)
    def spall(p0,nrm,rad):   # flat-faced spall: everything near p0 beyond the plane (p0, nrm) is pressed onto it
        nrm=np.array(nrm,float);nrm/=np.linalg.norm(nrm);sd=(co-np.array(p0))@nrm;fall=np.clip((rad-np.linalg.norm(co-np.array(p0),axis=1))/(rad*.45),0,1)
        co[:]-=nrm*(np.clip(sd,0,None)*fall**.7)[:,None]   # full cut in the middle, fading out towards the rim (no step)
    for k in range(9):   # crown: broken facets round the top, deeper at the front-left
        t=math.tau*k/9+r.uniform(-.2,.2);ex,ey=math.cos(t),math.sin(t);big=1.5 if (ex<0 and ey<0) else 1
        dep=r.uniform(.012,.028)*big;p0=(w/2*ex*.95,d/2*ey*.95,h-dep);spall(p0,(ex*r.uniform(.5,1.2),ey*r.uniform(.5,1.2),1),.11*big)
    for k,(z0,z1) in enumerate(((.30,.45),(.43,.70),(.71,.89),(.93,1.03))):   # the long broken front-left arris, four spall groups of 2-4 facets
        for j in range(r.randint(4,7)):
            zc=r.uniform(z0,z1);dep=r.uniform(.012,.03);p0=(-w/2+dep,-d/2+dep,zc)
            spall(p0,(-1+r.uniform(-.4,.4),-1+r.uniform(-.4,.4),r.uniform(-.7,.7)),r.uniform(.05,.09))
    for k in range(4):   # small spalls at the foot
        t=math.tau*k/4+.7+r.uniform(-.3,.3);dep=r.uniform(.008,.02);p0=(w/2*math.cos(t)*.92,d/2*math.sin(t)*.92,.03);spall(p0,(math.cos(t),math.sin(t),-.6),.07)
    co[:,2]=np.maximum(co[:,2],0);me.vertices.foreach_set('co',co.ravel());me.update()
    jitter(o,.0025,32,22);jitter(o,.0012,33,70)
    cs=[]
    lines=[];zz=.40
    for i,(L,dep,gap) in enumerate(((.17,.004,.12),(.21,.007,.11),(.15,.0035,.13),(.23,.008,.11),(.19,.005,.12),(.22,.009,.13),(.16,.0045,.12),(.2,.006,.11))):
        x0=-w/2+.045;cs.append(cutter(box_bm((L,.04+dep*2,.011),(x0+L/2,-d/2-.02+dep,zz))));lines.append((x0,x0+L,zz,2*dep))
        bm=bmesh.new();bmesh.ops.create_cone(bm,cap_ends=True,segments=14,radius1=.009,radius2=.009,depth=.05);bmesh.ops.rotate(bm,verts=bm.verts,cent=(0,0,0),matrix=Matrix.Rotation(math.pi/2,3,'X'))
        bmesh.ops.translate(bm,verts=bm.verts,vec=(x0+L+.03,-d/2-.025+.007,zz));cs.append(cutter(bm))
        if i<7:zz+=gap
    top=lines[-1];wx=top[0]+.01;wz=top[2]+.026   # small wave sign: two short s-curves just above the top line
    for k in range(2):
        pts=[(wx+.05*t,-d/2,wz+k*.018+.006*math.sin(t*math.tau*1.5)) for t in np.linspace(0,1,14)]
        bm=bmesh.new();vs=[]
        for (x,y,z) in pts:vs.append((bm.verts.new((x,y-.02,z-.0025)),bm.verts.new((x,y-.02,z+.0025)),bm.verts.new((x,y+.007,z+.0025)),bm.verts.new((x,y+.007,z-.0025))))
        for a,b in zip(vs,vs[1:]):
            for i in range(4):bm.faces.new((a[i],a[(i+1)%4],b[(i+1)%4],b[i]))
        bm.faces.new(vs[0][::-1]);bm.faces.new(vs[-1]);cs.append(cutter(bm))
    carve(o,cs);bpy.context.view_layer.update()
    for k,(st,dv,L_,wd) in enumerate((((-w/2+.03,-d/2,1.0),(.2,0,-1),.75,.006),((w/2,-.05,.94),(0,.6,.5),.3,.004),((w/2,.08,.72),(0,-.5,-1),.5,.004),
                                       ((-.05,d/2,.85),(-.3,0,-1),.8,.006),((.06,d/2,.6),(.6,0,-.7),.18,.003),((-.08,-d/2,.33),(.6,0,-.6),.14,.0025),((0,0,h),(1,.3,0),.2,.004))):
        groove(o,surface_walk(o,st,dv,L_,.012,370+k,.35),wd*1.8,wd*.9)   # crack systems on every face, wider on the broken arris
    for j in range(7):   # angular foot stones and gravel kept inside the 0.5 x 0.4 footprint
        a=math.tau*j/7+r.uniform(-.3,.3);c=(.18*math.cos(a),.135*math.sin(a),0);rock(f'UP03_Foot{j}',(r.uniform(.07,.1),r.uniform(.055,.07),r.uniform(.05,.08)),c,M['granite'],S,330+j,cuts=10,round_=.04,ncracks=0,rot=a,vox=40,target=1500)
    pebbles('UP03_Gravel',M,'Gravel',340,(0,0),.19,.24,30,size=(.02,.04),avoid=lambda c:abs(c[0])>.22 or abs(c[1])>.17)
    for j,c in enumerate(((-.195,.08,0),(.195,.1,0),(-.19,-.1,0),(.2,-.06,0),(.02,.165,0),(-.08,-.12,0),(.1,-.12,0))):tuft(f'UP03_Tuft{j}',c,M,P,360+j,n=8,h=.085)   # tuft size as before, so the 0.5 x 0.4 footprint holds
    UP03_LINES[:]=lines;meta['collisions']={'Collision':[{'type':'box','size':(w,d,h),'center':(0,0,h/2)}]}
    meta['notes']={'marks':f'8 level lines (lowest at {lines[0][2]:.2f} m, highest at {lines[-1][2]:.2f} m), a dot beside each, a small wave sign by the top line; no letters, no numbers',
                   'stain':'old high-water stain band about 0.80-0.96 m'}
    return meta
def up03_paint(g,col,rough,q,onrm,ao,cav,edge,m,filled,glow,noise,RES):
    if g!='Stone':return col,rough,{}
    z=q[...,2];post=filled&(np.abs(q[...,0])<.19)&(np.abs(q[...,1])<.165)&(z>.1)
    n1=vnoise3(q,9,1);n2=vnoise3(q,38,2);v1=vnoise3(q,3,5,3)
    col=col*(.84+.3*v1[...,None])*(1+np.array([.05,.0,-.06])*(n1[...,None]-.5)*2)   # tonal patches
    col=np.clip(col*np.array([1.16,1.10,1.03]),0,1)   # warm grey granite, as in the v2 sheet (round three: was too orange)
    lum=col.mean(-1,keepdims=True);col=col*.55+lum*np.array([1.0,.97,.9])*.45;col=np.clip(col-np.clip(lum-.6,0,None)*.7,0,1)   # toward warm grey; tone down the big pale palette spots
    edge_=.88+.025*(n1-.5)*2;band=np.clip(1-np.abs(z-edge_)/.085,0,1)**.45*post*(.75+.25*n2)
    drip=np.clip((vnoise3(q*np.array([1,1,.12]),40,7,2)-.55)*4,0,1)*np.clip((edge_-z)/.03,0,1)*np.clip(1-(edge_-z)/.35,0,1)   # streaks running down from the old waterline
    under=np.clip((edge_-z)/.45,0,1)*post*.25*(.6+.4*n1)+.5*drip*post;band=np.clip(band*1.1,0,1)
    col=col*(1-.85*band[...,None]-under[...,None]*.6)+np.array([.16,.12,.08])*(.85*band+.6*under)[...,None]
    gr=np.zeros_like(z)
    for x0,x1,zc,dep in UP03_LINES:
        gr=np.maximum(gr,((q[...,0]>x0-.004)&(q[...,0]<x1+.004)&(np.abs(z-zc)<.008)&(q[...,1]>-.145-.004)&(q[...,1]<-.145+dep+.004)).astype(np.float32))
    gr=gr*post*np.clip((n2-.25)*2.2,0,1);mc=np.array([.24,.29,.13])
    col=col*(1-.7*gr[...,None])+mc*.7*gr[...,None]
    lich=np.clip((vnoise3(q,38,3,2)-.68)*8,0,1)*np.clip((vnoise3(q,5,4,1)-.3)*3,0,1)*post*(z>.2)   # small rosettes, not blobs
    col=col*(1-.55*lich[...,None])+np.array([.80,.80,.70])*.55*lich[...,None]
    return col,rough,{}

# ---------------- UP04 畫了水路的平石 ----------------
def UP04(M):
    """flat-topped creek slab (about 1.36 x 0.96 x 0.31) with lichen on the sides; the charcoal drawing is its own decal sheet; a charcoal stick on the edge"""
    S='Stone';Dr='Drawing';C='Charcoal';P='Plants';r=random.Random(404);meta={'moss_low':.7,'moss_h':.25,'moss_top':.05,'moss_cav':.25,'soil':.07,'decals':{}}
    a,b,h=.62,.44,.29;n=72;bm=bmesh.new();rings=[];meta['wear']=.5
    prof=[(0,0),(0,.4),(0,.8),(.03,.9),(.10,.965),(.28,1.0),(.55,1.0),(.75,.975),(.88,.93),(.95,.87),(.985,.80),(1.0,.70),(1.0,.5),(1.0,.25),(1.0,0)]   # (z, radius) fractions: rounded top edge, flared foot, closed by rings to the centre
    for zf,rf in prof:
        if rf==0:rings.append([bm.verts.new((0,0,h*zf))]*n);continue
        ring=[]
        for i in range(n):
            t=math.tau*i/n;e=1+.06*math.sin(3*t+.7)+.04*math.sin(5*t+2.1);ring.append(bm.verts.new((a*rf*e*math.cos(t),b*rf*e*math.sin(t),h*zf)))
        rings.append(ring)
    for A,B in zip(rings,rings[1:]):
        for i in range(n):
            q_=[A[i],A[(i+1)%n],B[(i+1)%n],B[i]];q_=[v for k_,v in enumerate(q_) if v not in q_[:k_]]
            bm.faces.new(q_)
    o=finish('UP04_Slab',bm,M['creekstone'],S,.5);subdiv(o,2)
    me=o.data;me.update();nv=len(me.vertices)   # sides lumpy, top only gently undulating (it is drawn on); normals read before moving
    co=np.empty(nv*3);me.vertices.foreach_get('co',co);co=co.reshape(nv,3);nr=np.empty(nv*3);me.vertices.foreach_get('normal',nr);nr=nr.reshape(nv,3)
    x,y,z=co[:,0],co[:,1],co[:,2];zf=z/h;k=np.where(zf<.9,.028*(1-zf),.002)*(nr[:,2]>-.5)
    side=np.clip((.9-zf)/.15,0,1)*(nr[:,2]>-.5);P_=co[:,None,:].astype(np.float32)
    led=np.clip((((z+.03*np.sin(x*3.1+y*2.3)+.02*np.sin(x*7.7-y*5.3))/.075)%1-.75)*6,0,1)*.012*np.clip(vnoise3(P_,4,403,2)[:,0]*2-.3,0,1)   # bedding planes: each layer steps back a little at its base
    lump=(vnoise3(P_,2.2,401,3)[:,0]-.5)*.05+(vnoise3(P_,9,402,2)[:,0]-.5)*.012
    co=co+nr*(k*(np.sin(x*7+1)*np.sin(y*9+.5)+.6*np.sin(x*19+y*15+z*20)+.35*np.sin(x*41-y*37))+side*(lump-led))[:,None]
    co[:,2]=np.maximum(co[:,2],0);me.vertices.foreach_set('co',co.ravel());me.update()
    for k_,(st,d_,L_) in enumerate((((.5,-.3,.2),(0,0,-1),.25),((-.55,.15,.2),(0,0,-1),.22),((.1,.42,.2),(0,0,-1),.2),((-.2,-.44,.2),(0,0,-1),.24),((.62,.1,.15),(0,0,-1),.16))):
        groove(o,surface_walk(o,st,d_,L_,.01,410+k_,.35),.008,.006)   # cracks down the sides
    for k_,(st,d_,L_) in enumerate((((-.45,-.25,.3),(1,.35,0),.5),((.2,.3,.3),(.4,-1,0),.3),((-.1,-.05,.3),(-1,.6,0),.35))):
        groove(o,surface_walk(o,st,d_,L_,.01,420+k_,.3),.0035,.002)   # hairlines across the top, under the drawing
    top=max(v.co.z for v in o.data.vertices);bpy.context.view_layer.update()
    # decal sheet: a grid laid on the top surface, 3 mm above it
    from mathutils.bvhtree import BVHTree
    bvh=BVHTree.FromObject(o,bpy.context.evaluated_depsgraph_get());dw,dh=1.04,.70;nx,ny=52,36;bm=bmesh.new();V=[]
    for j in range(ny+1):
        row=[]
        for i in range(nx+1):
            x=-dw/2+dw*i/nx;y=-dh/2+dh*j/ny;hit=bvh.ray_cast(Vector((x,y,top+.2)),Vector((0,0,-1)))
            row.append(bm.verts.new((x,y,(hit[0].z if hit[0] else top)+.003)))
        V.append(row)
    for j in range(ny):
        for i in range(nx):bm.faces.new((V[j][i],V[j][i+1],V[j+1][i+1],V[j+1][i]))
    lay=bm.loops.layers.uv.new('Tiled')
    for f in bm.faces:
        for l in f.loops:x,y=l.vert.co.x,l.vert.co.y;l[lay].uv=((x+dw/2)/dw,(y+dh/2)/dh)
    me=bpy.data.meshes.new('UP04_Drawing');bm.to_mesh(me);bm.free();d=bpy.data.objects.new('UP04_Drawing',me);me.materials.append(M['charcoal']);link(d,Dr)
    meta['decals'][Dr]=lambda RES:drawing_rgba(RES,dw,dh)
    # charcoal stick on the right edge
    p0=Vector((.40,.12,0));p1=p0+Vector((.10,-.025,0))
    for p in (p0,p1):hit=bvh.ray_cast(p+Vector((0,0,1)),Vector((0,0,-1)));p.z=(hit[0].z if hit[0] else top)+.011
    st_=tube('UP04_Charcoal',[p0,p0.lerp(p1,.5),p1],.011,M['charcoal'],C,8,.05,radii=[.011,.012,.010]);jitter(st_,.0015,41,120)
    pebbles('UP04_Gravel',M,'Gravel',450,(0,0),.62,.70,40,size=(.025,.05),avoid=lambda c:abs(c[0])>.66 or abs(c[1])>.46)
    for j in range(22):   # grass and a few ferns tucked against the foot all round
        t=math.tau*j/22+r.uniform(-.1,.1);e=1+.06*math.sin(3*t+.7)+.04*math.sin(5*t+2.1);c=(a*1.04*e*math.cos(t),b*1.04*e*math.sin(t),0)
        if abs(c[0])>.66 or abs(c[1])>.46:continue
        if j%5==0:fern(f'UP04_Fern{j}',c,M,P,480+j,n=5,L=.09)
        else:tuft(f'UP04_Tuft{j}',c,M,P,470+j,n=11,h=r.uniform(.12,.2))
    meta['collisions']={'Collision':[{'type':'hull','parts':['UP04_Slab'],'simplify':6}]}
    meta['states']={'drawing':'UP04_Drawing is a separate alpha-blended decal sheet (UV 0-1 over 1.04 x 0.70 m); swap its Albedo for later days. Delivered: half drawn.'}
    meta['notes']={'charcoal':'UP04_Charcoal is its own mesh (0.10 m stick) and can be removed'}
    return meta
def drawing_rgba(RES,dw,dh):
    """child's charcoal map of the creek: a winding double-line creek, branching channels with arrows, small circles,
    a circle-in-circle mechanism; two right-hand channels only half drawn. No letters, no numbers.
    Drawn in metres on the sheet (x 0..dw, y 0..dh), rasterised segment by segment (Blender's Python has no PIL)."""
    S=RES;a=np.zeros((S,S),np.float32);r=random.Random(44);px=dw/S;py=dh/S
    def seg(p,q,w):
        x0,x1=sorted((p[0],q[0]));y0,y1=sorted((p[1],q[1]));i0=max(0,int((x0-w)/px));i1=min(S,int((x1+w)/px)+2);j0=max(0,int((y0-w)/py));j1=min(S,int((y1+w)/py)+2)
        if i0>=i1 or j0>=j1:return
        X_=(np.arange(i0,i1)+.5)*px;Y_=(np.arange(j0,j1)+.5)*py;XX,YY=np.meshgrid(X_,Y_);d=np.array(q)-np.array(p)
        t=np.clip(((XX-p[0])*d[0]+(YY-p[1])*d[1])/max(d@d,1e-12),0,1);dist=np.hypot(XX-p[0]-t*d[0],YY-p[1]-t*d[1])
        a[j0:j1,i0:i1]=np.maximum(a[j0:j1,i0:i1],np.clip((w-dist)/(w*.45),0,1))
    def line(pts,w,amp=.003):
        pts=[(x*dw+r.uniform(-amp,amp),y*dh+r.uniform(-amp,amp)) for x,y in pts]
        for p,q in zip(pts,pts[1:]):seg(p,q,1.5*w*r.uniform(.8,1.1))   # round three: bolder charcoal, reads from standing height as in the reference
    def circle(cx,cy,R,w):line([(cx+R*math.cos(t)/dw,cy+R*math.sin(t)/dh) for t in np.linspace(0,math.tau,28)],w,.0015)
    creek=[(.03+.94*t,.52+.16*math.sin(t*math.tau*1.25+.4)+.05*math.sin(t*math.tau*3.1)) for t in np.linspace(0,1,60)]
    for off in (-.035,.035):line([(x,y+off) for x,y in creek],.0062)
    for k in range(3):line([(x,y+(k-1)*.012) for x,y in creek[5+k*4:50-k*3]],.0014)   # flow strokes inside the creek
    def branch(i0,dx,dy,n,done=1.0):
        x,y=creek[i0];pts=[(x,y+.035*math.copysign(1,dy))]
        for k in range(1,n+1):pts.append((pts[-1][0]+dx/n+r.uniform(-.01,.01),pts[-1][1]+dy/n+r.uniform(-.012,.012)))
        m=max(2,int(len(pts)*done));line(pts[:m],.0042)
        if done>=1:   # arrow head
            (x0,y0),(x1,y1)=pts[-2],pts[-1];ang=math.atan2((y1-y0)*dh,(x1-x0)*dw)
            for s in (-1,1):a2=ang+math.pi+s*.5;line([(x1,y1),(x1+.035*math.cos(a2)/dw,y1+.035*math.sin(a2)/dh)],.003)
        return pts[m-1]
    ends=[branch(10,.10,.26,6),branch(22,.05,-.30,6),branch(34,.16,.22,7),branch(16,-.06,-.28,6),branch(28,.08,.30,6)]
    def fork(x,y,dx,dy,lev):   # root-like forks off a channel end
        if lev==0:return
        for s_ in (-1,1):
            nx_,ny_=x+dx*.5+s_*dy*.25,y+dy*.5-s_*dx*.25;line([(x,y),((x+nx_)/2+r.uniform(-.008,.008),(y+ny_)/2+r.uniform(-.008,.008)),(nx_,ny_)],.0022);fork(nx_,ny_,dx*.6,dy*.6,lev-1)
    for (x,y),(dx,dy) in zip(ends,((.05,.10),(.03,-.12),(.07,.09),(-.04,-.1),(.05,.1))):fork(x,y,dx,dy,3)
    for k in range(12):   # flow arrows beside the creek
        i=3+k*4;(x0,y0),(x1,y1)=creek[i],creek[i+2];off=.075*(1 if k%2 else -1);ang=math.atan2((y1-y0)*dh,(x1-x0)*dw)
        p0=(x0,y0+off);p1=(x0+.05*math.cos(ang)/dw,y0+off+.05*math.sin(ang)/dh);line([p0,p1],.0024)
        for s_ in (-1,1):a2=ang+math.pi+s_*.55;line([p1,(p1[0]+.018*math.cos(a2)/dw,p1[1]+.018*math.sin(a2)/dh)],.0024)
    for (x0,y0),(x1,y1) in (((.30,.15),(.45,.24)),((.55,.85),(.40,.80)),((.08,.30),(.20,.38))):   # dashed guide lines
        for t0 in np.arange(0,1,.16):line([(x0+(x1-x0)*t0,y0+(y1-y0)*t0),(x0+(x1-x0)*(t0+.09),y0+(y1-y0)*(t0+.09))],.0022)
    for (cx_,cy_,R_) in ((.30,.15,.03),(.88,.80,.028),(.12,.82,.022)):   # concentric circles with a dot
        circle(cx_,cy_,R_,.0026);circle(cx_,cy_,R_*.45,.0022);circle(cx_,cy_,.003,.003)
    branch(44,.12,-.24,6,done=.5);branch(53,.10,.28,6,done=.4)   # the half-drawn channels
    for (x,y) in ends[:2]:circle(x,y+.03*math.copysign(1,y-.5),.022,.003)
    circle(.72,.22,.05,.003);circle(.72,.22,.022,.0026)   # the circle-in-circle "machine"
    for k in range(14):   # little circles along the creek, like stepping stones
        x,y=creek[4+k*4];circle(x,y+r.choice((-1,1))*.09,r.uniform(.008,.014),.0022)
    g=np.random.default_rng(7).random(a.shape).astype(np.float32);a=a*np.clip(.55+.6*g,0,1)   # grainy charcoal on rough stone
    return np.dstack([.07+0*a,.065+0*a,.06+0*a,np.clip(a*.92,0,1)])

# ---------------- UP05 引氣課擺設 ----------------
def cushion(pid,M,mat,h,squash,seed,R=.25):
    """coiled straw braid: a spiral on top, stacked rings on the side, binding cords; the old one flatter with frayed straws"""
    C='Cushion';r=random.Random(seed);meta={'soil':0,'moss_low':0}
    br=.0105;hb=h-1.9*br   # body under the top coil; the coil's top is at h
    prof=[(0,0),(R-.03,0),(R,.02),(R+.005,hb*.5),(R-.01,hb*.9),(R-.05,hb),(0,hb)]
    lathe(f'{pid}_Body',prof,M[mat],C,seg=64,cyl=True)
    rows=max(2,round(hb/(2*br)))
    for k in range(rows):
        z=br+k*(hb-br)/max(1,rows-1);rr=R+.002-(.012 if k==rows-1 else 0)
        rope(f'{pid}_Side{k}',[(rr*math.cos(a),rr*math.sin(a),z) for a in np.linspace(0,math.tau,73)],br,M[mat],C,plies=3,sides=5)
    turns=11;pts=[];n=turns*48
    for i in range(n+1):
        t=i/n;rad=.02+(R-.05)*t;a=math.tau*turns*t;zt=h-br-(1-t)**2*squash*.012
        pts.append((rad*math.cos(a),rad*math.sin(a),zt))
    rope(f'{pid}_Top',pts,br*.95,M[mat],C,plies=3,sides=5)
    for k in range(6):   # twisted binding cords over the side coils, a knot at mid height
        a=math.tau*k/6+.3;rr=R+.012
        rope(f'{pid}_Bind{k}',[((rr-.006)*math.cos(a),(rr-.006)*math.sin(a),.002)]+[(rr*math.cos(a),rr*math.sin(a),z) for z in np.linspace(.012,hb-.004,5)]+[((rr-.012)*math.cos(a),(rr-.012)*math.sin(a),hb+.008)],.0032,M[mat],C,plies=2,sides=4)
        lathe(f'{pid}_Knot{k}',[(0,-.006),(.0062,-.004),(.0068,0),(.0062,.004),(0,.006)],M[mat],C,seg=8,center=(rr*math.cos(a),rr*math.sin(a),hb*.5))
    for k in range(16):   # radial ties stitched over the top spiral
        a=math.tau*k/16;tube(f'{pid}_Spoke{k}',[(.02*math.cos(a),.02*math.sin(a),h-.002),((R-.04)*math.cos(a),(R-.04)*math.sin(a),h-.003-squash*.004)],.0018,M[mat],C,4,.05)
    for i in range(64 if squash else 20):   # frayed straws sticking out of the rim (round three: the new one frays a little too, as in the reference)
        a=r.uniform(0,math.tau);z=r.uniform(.01,hb);p=Vector(((R+.005)*math.cos(a),(R+.005)*math.sin(a),z));d=Vector((math.cos(a+r.uniform(-.8,.8)),math.sin(a+r.uniform(-.8,.8)),r.uniform(-.3,.4))).normalized()
        tube(f'{pid}_Straw{i}',[p,p+d*r.uniform(.012,.03 if squash else .02)],.0012,M[mat],C,4,.05)
    if squash:   # grey cloth band patched over a broken side coil, a few running stitches
        a0=r.uniform(0,math.tau);bm=bmesh.new();G=[]
        for i in range(9):
            a=a0+(i/8-.5)*.34;row=[]
            for z in np.linspace(-.008,hb+.012,6):
                rr=R+.0115+.002*math.sin(i*1.7+z*90);zz=min(z,hb);rr=rr if z<=hb else R-.01;row.append(bm.verts.new((rr*math.cos(a),rr*math.sin(a),max(zz,.0)+(z-hb if z>hb else 0)*0+(.012 if z>hb else 0))))
            G.append(row)
        for i in range(8):
            for j in range(5):bm.faces.new((G[i][j],G[i+1][j],G[i+1][j+1],G[i][j+1]))
        finish(f'{pid}_Patch',bm,M['cloth'],C,.1)
        for k in range(7):
            a=a0+(k/6-.5)*.32;z=.012 if k%2 else hb-.006;rr=R+.013;tube(f'{pid}_Stitch{k}',[(rr*math.cos(a-.012),rr*math.sin(a-.012),z),(rr*math.cos(a+.012),rr*math.sin(a+.012),z+.004)],.0009,M['hemp'],C,4,.05)
    meta['collisions']={};meta['notes']={'collision':'none (walk over), per work pack','copies':'the scene duplicates 5-6 cushions'}
    return meta
def UP05_CushionNew(M):
    """蒲團・新 · plump coiled straw, Ø0.55 × 0.12"""
    return cushion('UP05_CushionNew',M,'straw',.115,0,501)
def UP05_CushionOld(M):
    """蒲團・舊 · flattened, darker straw, frayed edge"""
    return cushion('UP05_CushionOld',M,'straw_old',.085,1,502,R=.235)
def UP05_Table(M):
    """矮几 · old elm, 0.8 x 0.45 x 0.30: breadboard-end top, square legs, aprons with small spandrels, stretchers;
    a hand-worn shiny corner, a water ring, ash spilled near where the burner stands"""
    T='Table';meta={'soil':0,'moss_low':0,'wear':1.4}
    W,D,H,t=.8,.45,.30,.042
    for j,(y0,y1) in enumerate(((-D/2+.005,-.065),(-.062,.078),(.081,D/2-.005))):   # three boards, hairline seams between them
        box(f'UP05_Top{j}',(W-.07,y1-y0,t),(0,(y0+y1)/2,H-t/2),M['elm'],T,bev=.004,cuts=2,scale=.4)
    for sx in (-1,1):box(f'UP05_End{sx}',(.035,D,t+.004),(sx*(W/2-.0175),0,H-t/2-.002),M['elm'],T,bev=.006,scale=.4)
    for sx in (-1,1):
        for sy in (-1,1):
            box(f'UP05_Leg{sx}{sy}',(.044,.044,H-t),(sx*(W/2-.06),sy*(D/2-.045),(H-t)/2),M['elm'],T,bev=.004,scale=.3)
            for k,(zt,ht) in enumerate(((H-t-.018,.022),(H-t-.046,.016))):   # apron tenons coming through the leg face, wedge-proud
                box(f'UP05_Tenon{sx}{sy}{k}',(.014,.006,ht),(sx*(W/2-.06),sy*(D/2-.045+.0245),zt),M['elm'],T,bev=.0015,scale=.1)
            box(f'UP05_Peg{sx}{sy}',(.007,.007,.007),(sx*(W/2-.06+.024),sy*(D/2-.045),H-t-.03),M['elm'],T,bev=.001,scale=.1)
        box(f'UP05_SideApron{sx}',(.022,D-.12,.05),(sx*(W/2-.06),0,H-t-.025),M['elm'],T,bev=.003,scale=.3)
        box(f'UP05_Stretcher{sx}',(.02,D-.11,.022),(sx*(W/2-.06),0,.07),M['elm'],T,bev=.003,scale=.3)
    for sy in (-1,1):
        box(f'UP05_Apron{sy}',(W-.16,.02,.055),(0,sy*(D/2-.045),H-t-.0275),M['elm'],T,bev=.003,scale=.4)
        for sx in (-1,1):   # small cloud-curve spandrel under the apron, next to each leg
            poly=[(0,0),(.075,0),(.075,-.012),(.05,-.012),(.05,-.026),(.028,-.026),(.028,-.04),(.012,-.04),(0,-.052)]   # stepped bracket
            o=prism(f'UP05_Spandrel{sx}{sy}',[(sx*(W/2-.078)-sx*u,z) for u,z in poly],.016,M['elm'],T,bev=.002,scale=.2)
            o.data.transform(Matrix.Translation((0,sy*(D/2-.045),H-t-.055)))
    meta['collisions']={'Collision':[{'type':'box','size':(W,D,H),'center':(0,0,H/2)}]}
    meta['notes']={'surface_z':H,'burner_spot':[0.035,0.06,H],'worn_corner':'left-front, where the teacher\'s hand rests'}
    return meta
def up05_table_paint(g,col,rough,q,onrm,ao,cav,edge,m,filled,glow,noise,RES):
    col=col*np.array([.9,.76,.64]);top=filled&(onrm[...,2]>.8)&(q[...,2]>.29)   # warmer red-brown elm, as in the v2 sheet
    corner=np.clip(1-np.hypot(q[...,0]-(-.34),q[...,1]-(-.17))/.11,0,1)*filled*(q[...,2]>.24)   # left-front corner, where a hand rests
    col=col*(1+.35*corner[...,None])+np.array([.07,.045,.02])*corner[...,None];rough=np.clip(rough-.45*corner,.2,1)
    rr=np.hypot(q[...,0]-.22,q[...,1]-(-.06));ring=np.clip(1-np.abs(rr-.035)/.004,0,1)*top*.7
    col=col*(1-.35*ring[...,None])+np.array([.18,.12,.08])*.35*ring[...,None]
    ad=np.hypot((q[...,0]-.13)*.8,q[...,1]-.035);ash=np.clip((.06-ad)/.035,0,1)*top*np.clip((noise-.4)*2.2,0,1)*np.clip((vnoise3(q,70,11,2)-.3)*3,0,1)   # speckled spill (a sin x sin mask printed a checkerboard)
    col=col*(1-.6*ash[...,None])+np.array([.52,.51,.48])*.6*ash[...,None];rough=np.clip(rough+.3*ash,0,1)
    return col,rough,{}
def UP05_Burner(M):
    """小香爐 · patinated bronze, three legs, two upright loop ears, ash inside; Socket_Smoke over the ash; Ø0.15 x 0.12"""
    B='Burner';meta={'soil':0,'moss_low':0,'wear':1.2}
    # squat belly, a raised band at the shoulder, a short neck and a flared lip (outer profile, then back down the inside)
    prof=[(0,.026),(.038,.026),(.056,.032),(.068,.045),(.0715,.058),(.069,.068),(.0705,.070),(.0705,.077),(.066,.079),(.060,.083),(.059,.090),(.064,.097),(.067,.0995),
          (.064,.1015),(.058,.099),(.054,.090),(.056,.08),(.058,.066),(.054,.05),(.040,.040),(0,.038)]
    lathe('UP05_Bowl',prof,M['bronze'],B,seg=72)
    for k in range(8):   # low-relief square-spiral plaques round the belly: a raised frame and an inner block
        a=math.tau*k/8+math.pi/8
        for j,(w,hh,dep) in enumerate(((.022,.016,.0018),(.010,.006,.0028))):
            o=box(f'UP05_Plaque{k}_{j}',(dep*2,w,hh),(0,0,0),M['bronze'],B,bev=.0008,scale=.05);o.data.transform(Matrix.Translation((.0695,0,.060)));o.data.transform(Matrix.Rotation(a,4,'Z'))
    lathe('UP05_Ash',[(0,.084),(.0545,.084),(.0545,.0865),(.04,.0885),(.02,.0895),(0,.0898)],M['ash'],B,seg=48)
    for k,(x,y,hh) in enumerate(((.012,.006,.016),(-.008,.014,.010),(.004,-.016,.007))):   # burnt-down incense stubs in the ash
        tube(f'UP05_Stub{k}',[(x,y,.087),(x+.001,y,.087+hh)],.0016,M['clay'],B,6,.02)
    for k in range(3):
        a=math.tau*k/3+math.pi/2;c=Vector((.047*math.cos(a),.047*math.sin(a),0))   # short splayed legs
        tube(f'UP05_Leg{k}',[c*1.12+Vector((0,0,0)),c*1.06+Vector((0,0,.012)),c*.98+Vector((0,0,.026)),c*.9+Vector((0,0,.036))],.008,M['bronze'],B,12,.05,radii=[.0075,.0085,.0095,.010])
    for sx in (-1,1):   # upright square ears on the rim: two posts and a flat top bar, open in the middle
        for dy in (-.0095,.0095):box(f'UP05_EarPost{sx}{dy>0}',(.008,.005,.016),(sx*.061,dy,.1065),M['bronze'],B,bev=.0012,scale=.05)
        box(f'UP05_EarTop{sx}',(.009,.024,.005),(sx*.061,0,.1155),M['bronze'],B,bev=.0012,scale=.05)
    meta['sockets']={'Socket_Smoke':(0,0,.095)};meta['collisions']={};meta['notes']={'collision':'none (small prop)'}
    return meta
def up05_burner_paint(g,col,rough,q,onrm,ao,cav,edge,m,filled,glow,noise,RES):
    """patina: pale verdigris settles in the hollows, worn warm bronze shows on the raised band, the lip and the ears"""
    bronze=filled&~((np.hypot(q[...,0],q[...,1])<.0555)&(q[...,2]>.083)&(onrm[...,2]>.5))
    verd=np.clip((1-ao)*2.2+cav*.8,0,1)*bronze*np.clip(noise*1.4,.3,1)
    col=col*(1-.55*verd[...,None])+np.array([.38,.52,.42])*.55*verd[...,None]
    worn=np.clip(edge*1.4+np.clip((q[...,2]-.096)/.006,0,1)*.6,0,1)*bronze
    col=col*(1-.4*worn[...,None])+np.array([.55,.40,.22])*.4*worn[...,None];rough=np.clip(rough-.25*worn+.15*verd,0,1)
    return col,rough,{}

# ---------------- UP06 柳知微的提燈 ----------------
def UP06(M):
    """slender moon-white paper lantern (0.30 m) hanging from the bent tip of a bamboo pole (0.9 m) with a cloth-wrapped grip.
    Load path as in the v2 reference: lashing at the pole tip → short double loop → small iron ring → four rope legs →
    wooden collar with a low domed lid → six split-bamboo ribs (three nodes each, lashed top and bottom) → bamboo hoop
    → wooden base on three short feet. Paper bulges a little between the ribs; a mended patch pinned on the front-left;
    faint soot under the lid; _Lit drives the paper glow"""
    F='Frame';L='Lamp';meta={'soil':0,'moss_low':0,'wear':1.0};r=random.Random(606)
    tip=Vector((.115,0,.875));pole=[Vector((0,0,0)),Vector((0,0,.3)),Vector((.004,0,.6)),Vector((.03,0,.79)),Vector((.075,0,.86)),tip]
    tube('UP06_Pole',pole,.012,M['bamboo_old'],F,12,.15,radii=[.0105,.0102,.0098,.0094,.009,.0086])
    lathe('UP06_PoleEnd',[(0,-.0005),(.0086,-.0005),(.0086,.002),(.0062,.002),(.0062,.0005),(0,.0005)],M['bamboo_old'],F,seg=16,center=(0,0,0))
    for z in (.06,.40,.55,.68):   # natural nodes: a raised band with a slight neck either side
        lathe(f'UP06_Node{z}',[(.0,-.004),(.0099,-.004),(.0094,-.0025),(.0108,0),(.0094,.0025),(.0099,.004),(0,.004)],M['bamboo_old'],F,seg=16,center=(float(np.interp(z,[p.z for p in pole],[p.x for p in pole])),0,z))
    for k in range(14):lashing(f'UP06_Grip{k}',(0,0,.155+k*.0115),(r.uniform(-.06,.06),r.uniform(-.06,.06),1),.0108-.0006*(4<k<10),1,M['cloth'],F,cord=.0032)
    for z in (.148,.322):lashing(f'UP06_GripTie{z}',(0,0,z),(0,0,1),.0135,2,M['hemp'],F,cord=.0016)
    tube('UP06_GripTail',[(.013,0,.33),(.016,-.003,.318),(.018,-.006,.302)],.0025,M['cloth'],F,5,.05)
    # hanging: lashing round the bent tip, a short double loop down to the iron ring
    d=(tip-pole[-2]).normalized();lashing('UP06_TipLash',tip-d*.022,d,.0088,6,M['hemp'],F,cord=.0014)
    cx=tip.x;zb=tip.z-.40;zr=zb+.366
    tube('UP06_Ring',[(cx+.0065*math.sin(a),0,zr+.0065*math.cos(a)) for a in np.linspace(0,math.tau,25)],.0015,M['iron'],F,6,.05,caps=False)
    for sy in (-1,1):rope(f'UP06_Loop{sy}',[(tip.x-d.x*.022+sy*.002,sy*.003,tip.z-.012),(cx+sy*.002,sy*.002,zr+.02),(cx,0,zr+.006)],.0014,M['hemp'],F)
    # lantern body
    z0=zb+.036;prof=[(.047,.036),(.060,.065),(.071,.110),(.075,.155),(.071,.215),(.059,.252),(.043,.277)]
    def R(z):
        zz=[p[1] for p in prof];rr=[p[0] for p in prof];return float(np.interp(z-zb,zz,rr))
    bm=bmesh.new();seg=72;rows=40;zs=np.linspace(zb+.033,zb+.280,rows);grid=[]
    for z in zs:
        grid.append([bm.verts.new((cx+R(z)*(1+.016*math.sin(3*math.tau*i/seg)**2*min(1,(z-zs[0])/.03,(zs[-1]-z)/.03))*math.cos(math.tau*i/seg),
                                    R(z)*(1+.016*math.sin(3*math.tau*i/seg)**2*min(1,(z-zs[0])/.03,(zs[-1]-z)/.03))*math.sin(math.tau*i/seg),z)) for i in range(seg)])
    for a,b in zip(grid,grid[1:]):
        for i in range(seg):j=(i+1)%seg;bm.faces.new((a[i],a[j],b[j],b[i]))
    for f in bm.faces:f.smooth=True
    pap=finish('UP06_Paper',bm,M['moonpaper'],L,.05,uv=(lambda p:math.atan2(p.y,p.x-cx)*.075,lambda p:p.z,math.tau*.075))
    jitter(pap,.0006,61,140)   # soft crumple of mulberry paper, not a lathe-smooth shell
    for k in range(6):   # split-bamboo ribs at 0°, 60° … with three low nodes each, lashed into the lid slots and to the hoop
        a=math.tau*k/6;zz=np.linspace(zb+.036,zb+.276,25);nodes=[r.uniform(.075,.095),r.uniform(.15,.17),r.uniform(.225,.24)]
        rad=[.0019+.0007*max(0,1-abs(z-zb-nz)/.004) for z in zz for nz in [min(nodes,key=lambda n:abs(z-zb-n))]]
        pts=[(cx+(R(z)+.0021)*math.cos(a),(R(z)+.0021)*math.sin(a),z) for z in zz];tube(f'UP06_Rib{k}',pts,.0019,M['bamboo'],F,5,.05,radii=rad)
        for zt in (zb+.042,zb+.270):
            c=Vector((cx+(R(zt)+.0021)*math.cos(a),(R(zt)+.0021)*math.sin(a),zt));lashing(f'UP06_RibTie{k}_{zt:.3f}',c,(0,0,1),.0024,2,M['hemp'],F,cord=.0007)
    tube('UP06_Hoop',[(cx+.0495*math.cos(t),.0495*math.sin(t),zb+.034) for t in np.linspace(0,math.tau,49)],.0028,M['bamboo'],F,6,.05,caps=False)
    # base: turned block on three short feet with notches between them
    lathe('UP06_Base',[(0,zb+.008),(.044,zb+.008),(.050,zb+.012),(.052,zb+.024),(.049,zb+.031),(0,zb+.031)],M['elm'],F,seg=36,center=(cx,0,0))
    for k in range(3):
        a=math.tau*k/3+.5;box(f'UP06_Foot{k}',(.022,.016,.0085),(cx+.036*math.cos(a),.036*math.sin(a),zb+.0045),M['elm'],F,bev=.002,rot=Matrix.Rotation(a,4,'Z'))
    # lid: wooden collar with stepped edges + low domed disc; four rope legs from the ring to holes at front/back/left/right
    lathe('UP06_Collar',[(.039,zb+.276),(.045,zb+.276),(.045,zb+.278),(.044,zb+.279),(.044,zb+.291),(.045,zb+.292),(.045,zb+.294),(.039,zb+.294)],M['elm'],F,seg=36,center=(cx,0,0))
    lathe('UP06_Lid',[(0,zb+.292),(.0425,zb+.292),(.0425,zb+.2955),(.03,zb+.298),(.012,zb+.2998),(0,zb+.300)],M['elm'],F,seg=36,center=(cx,0,0))
    for k in range(4):
        a=math.tau*k/4;h=Vector((cx+.041*math.cos(a),.041*math.sin(a),zb+.290))
        rope(f'UP06_Leg{k}',[(cx+.002*math.cos(a),.002*math.sin(a),zr-.006),h+Vector((0,0,.004)),h],.0011,M['hemp'],F)
        box(f'UP06_LegKnot{k}',(.006,.006,.005),h+Vector((.0035*math.cos(a),.0035*math.sin(a),-.004)),M['hemp'],F,bev=.002,rot=Matrix.Rotation(a,4,'Z'))
    # mended patch on the front-left: a thin, ragged sheet a hair outside the paper, held by three short bamboo pins
    pa,pz=-2.0,zb+.115;bm=bmesh.new();PG=[]
    for i in range(7):
        row=[]
        for j in range(7):
            u=(i/6-.5)*.5;w=(j/6-.5)*.042;rag=.004*math.sin(i*2.1+j*1.3)
            z=pz+w+rag*(j in (0,6));aa=pa+u+.03*(i in (0,6))*math.sin(j*1.7);rr=R(z)*(1+.016*math.sin(3*aa)**2)+.0009
            row.append(bm.verts.new((cx+rr*math.cos(aa),rr*math.sin(aa),z)))
        PG.append(row)
    for i in range(6):
        for j in range(6):
            if (i,j) in ((0,0),(5,5),(0,5)):continue
            bm.faces.new((PG[i][j],PG[i+1][j],PG[i+1][j+1],PG[i][j+1]))
    for f in bm.faces:f.smooth=True
    finish('UP06_Patch',bm,M['moonpaper'],L,.05)
    for k,(da,dz) in enumerate(((-.21,.012),(.2,-.004),(-.02,-.02))):
        aa=pa+da;z=pz+dz;rr=R(z)*(1+.016*math.sin(3*aa)**2)+.0022;c=Vector((cx+rr*math.cos(aa),rr*math.sin(aa),z));t=Vector((-math.sin(aa),math.cos(aa),.6)).normalized()
        tube(f'UP06_Pin{k}',[c-t*.006,c+t*.006],.0011,M['bamboo_old'],F,5,.05)
    meta['sockets']={'Socket_Hand':(0,0,.24),'UP06_LightSocket':(cx,0,zb+.155)}
    meta['state']={'prop':'lit','param':'_Lit','default':0,'export':1,'range':[0,1],'emit_expr':'2.0*s'}
    meta['collisions']={};meta['notes']={'hold':'Socket_Hand is the grip centre on the cloth wrap; the pole stands upright in the file, the hand socket sets the carrying angle',
                                          'mend':'a pinned paper patch on the front-left of the shade; faint soot under the lid'}
    meta['lantern_z']=zb
    return meta
def up06_paint(g,col,rough,q,onrm,ao,cav,edge,m,filled,glow,noise,RES):
    if g!='Lamp':return col,rough,{}
    z=q[...,2];zb=.475;a=np.arctan2(q[...,1],q[...,0]-.115)
    soot=np.clip((z-(zb+.215))/.06,0,1)*filled*(.55+.45*noise)*(.7+.3*np.sin(a*3+1.3));col=col*(1-.45*soot[...,None])+np.array([.25,.22,.20])*.45*soot[...,None]
    seam=filled&(np.abs(a-1.5708)<.012);col=np.where(seam[...,None],col*.9,col)   # overlap seam at the back
    em=np.clip(col*np.array([1.12,1.0,.86])*(1-.85*soot[...,None]),0,1)   # warm white, never orange; soot stays dark
    return col,rough,{'Emission':np.dstack([em,np.ones(col.shape[:2],np.float32)])}

PROPS={'UP01':UP01,'UP02_01':UP02_01,'UP02_02':UP02_02,'UP02_03':UP02_03,'UP03':UP03,'UP04':UP04,
       'UP05_CushionNew':UP05_CushionNew,'UP05_CushionOld':UP05_CushionOld,'UP05_Table':UP05_Table,'UP05_Burner':UP05_Burner,'UP06':UP06}
REFDIR={'UP02_01':'UP02','UP02_02':'UP02','UP02_03':'UP02','UP05_CushionNew':'UP05','UP05_CushionOld':'UP05','UP05_Table':'UP05','UP05_Burner':'UP05'}
SLOTS={'UP01':'D3_Weir','UP02_01':'D3_WarmStone_01','UP02_02':'D3_WarmStone_02','UP02_03':'D3_WarmStone_03','UP03':'D3_WaterMark','UP04':'D3_DrawingStone',
       'UP05_CushionNew':'LT_QiLesson','UP05_CushionOld':'LT_QiLesson','UP05_Table':'LT_QiLesson','UP05_Burner':'LT_QiLesson','UP06':'Socket_Hand (Liu Zhiwei)'}
LIMITS={'UP01':(14,4,3.5),'UP02_01':(.9,.7,.6),'UP02_02':(.9,.7,.6),'UP02_03':(.9,.7,.6),'UP03':(.5,.4,1.4),'UP04':(1.4,1.0,.35),
        'UP05_CushionNew':(.55,.55,.12),'UP05_CushionOld':(.55,.55,.12),'UP05_Table':(.8,.45,.3),'UP05_Burner':(.15,.15,.12),'UP06':(.3,.3,.9)}
EXACT_MARGIN={('UP04','Charcoal')}   # groups packed with an exact 16 px margin (see the pack step)
GROUP_RES={'UP01':{'Weir':4096,'Gate':1024,'Debris':2048,'Plants':1024},
           **{k:{'Stone':2048,'Gravel':512,'Plants':512} for k in ('UP02_01','UP02_02','UP02_03')},'UP03':{'Stone':2048,'Gravel':512,'Plants':512},
           'UP04':{'Stone':2048,'Gravel':512,'Drawing':2048,'Charcoal':256,'Plants':512},
           'UP05_CushionNew':{'Cushion':1024},'UP05_CushionOld':{'Cushion':1024},'UP05_Table':{'Table':2048},'UP05_Burner':{'Burner':1024},'UP06':{'Frame':1024,'Lamp':1024}}
MOSS={'UP01':{'Weir':.42,'Debris':.06},**{k:{'Stone':.5} for k in ('UP02_01','UP02_02','UP02_03')},'UP03':{'Stone':.45},'UP04':{'Stone':.6}}
MOTTLE={'UP01':{'Weir':.09},**{k:{'Stone':.035,'Gravel':.03} for k in ('UP02_01','UP02_02','UP02_03')},'UP03':{'Stone':.035},'UP04':{'Stone':.045}}   # patch size m
LICHEN={'UP01':{'Weir':(.10,.3)},**{k:{'Stone':(.035,.4)} for k in ('UP02_01','UP02_02','UP02_03')},'UP03':{'Stone':(.09,.45)},'UP04':{'Stone':(.07,.5)}}   # (cell m, share of cells)
def up01_paint(g,col,rough,q,onrm,ao,cav,edge,m,filled,glow,noise,RES):
    if g not in ('Weir','Debris'):return col,rough,{}
    z=q[...,2];P_=q.astype(np.float32)
    streak=np.clip((vnoise3(P_*np.array([1,1,.12],np.float32),5,11,2)-.55)*3,0,1)*np.clip((2.2-z)/1.2,0,1)*np.clip(z/.3,0,1)*filled*(np.abs(onrm[...,2])<.6)
    wet=np.clip((.35-z)/.35,0,1)*filled*(.6+.4*vnoise3(P_,4,12,2))
    col=col*(1-.30*streak[...,None]-.25*wet[...,None])+np.array([.10,.10,.08])*(.30*streak+.25*wet)[...,None];rough=np.clip(rough-.25*wet,0,1)
    if g=='Weir':
        top=np.clip((onrm[...,2]-.6)/.3,0,1)*filled*np.clip((vnoise3(P_,3,13,3)-.42)*3.5,0,1)*np.clip((z-1.9)/.2,0,1)
        joint=np.clip(cav*1.5,0,1)*filled*np.clip((vnoise3(P_,6,14,2)-.4)*3,0,1)*(z<2.3)
        mm=np.clip(top*.85+joint*.7,0,1);mc=np.array([.26,.33,.13])+np.array([.08,.08,.03])*noise[...,None]
        col=col*(1-mm[...,None])+mc*mm[...,None];rough=np.clip(rough+.1*mm,0,1)
    return col,rough,{}
PAINT={'UP01':up01_paint,'UP03':up03_paint,'UP05_Table':up05_table_paint,'UP05_Burner':up05_burner_paint,'UP06':up06_paint}
def _with_paint(pid,fn):
    def go(M):
        meta=fn(M);meta['paint']=warm_paint(meta) if pid.startswith('UP02') else PAINT.get(pid)
        return meta
    return go
PROPS={k:_with_paint(k,v) for k,v in PROPS.items()}

# ---------------- collision ----------------
def collision(pid,meta,lod0):
    """meta['collisions'] = {mesh suffix: [primitive...]}; box/cylinder primitives, or hull = convex hull of named source parts.
    Each list becomes one static mesh <ID>_<suffix> (e.g. UP01_Collision, UP01_Collision_Debris)."""
    off=Vector(meta['offset']);out=[];info={}
    for suffix,plist in meta.get('collisions',{}).items():
        objs=[];prims=[]
        for p in plist:
            if p['type']=='box':
                c=[round(p['center'][i]+off[i],3) for i in range(3)];bm=box_bm(p['size'],c);prims.append({'type':'box','size':[round(v,3) for v in p['size']],'center':c})
            elif p['type']=='cylinder':
                c=[round(p['center'][i]+off[i],3) for i in range(3)];bm=bmesh.new();bmesh.ops.create_cone(bm,cap_ends=True,segments=12,radius1=p['radius'],radius2=p['radius'],depth=p['height'])
                bmesh.ops.translate(bm,verts=bm.verts,vec=Vector(c));prims.append({'type':'cylinder','radius':p['radius'],'height':p['height'],'center':c})
            else:   # hull of the source parts whose names start with one of p['parts']
                pts=[(o.matrix_world@v.co) for o in parts if any(o.name.startswith(s) for s in p['parts']) for v in o.data.vertices]
                bm=bmesh.new();vs=[bm.verts.new(v) for v in pts];r=bmesh.ops.convex_hull(bm,input=vs)
                bmesh.ops.delete(bm,geom=list({g for g in r['geom_interior']+r['geom_unused'] if isinstance(g,bmesh.types.BMVert)}),context='VERTS')
                bmesh.ops.dissolve_limit(bm,angle_limit=math.radians(p.get('simplify',6)),verts=bm.verts,edges=bm.edges);bmesh.ops.triangulate(bm,faces=bm.faces)
                bmesh.ops.recalc_face_normals(bm,faces=bm.faces)   # outward: Unity mesh colliders only hit front faces
                prims.append({'type':'hull','parts':p['parts'],'triangles':len(bm.faces)})
            me=bpy.data.meshes.new('col');bm.to_mesh(me);bm.free();o=bpy.data.objects.new('col',me);bpy.context.scene.collection.objects.link(o);objs.append(o)
        c=join(objs,f'{pid}_{suffix}');c.data.name=c.name;c.hide_render=True;c.display_type='WIRE';out.append(c)
        lo=np.array([min((c.matrix_world@v.co)[i] for v in c.data.vertices) for i in range(3)]);hi=np.array([max((c.matrix_world@v.co)[i] for v in c.data.vertices) for i in range(3)])
        info[f'{pid}_{suffix}']={'primitives':prims,'bounds_min':[round(float(v),3) for v in lo],'bounds_max':[round(float(v),3) for v in hi]}
    return out,info

# ---------------- bake / LOD / export ----------------
def seg_dist(P,pts):
    """distance from baked positions P (H,W,3) to a 3D polyline"""
    d=np.full(P.shape[:2],1e9,np.float32)
    for a,b in zip(pts,pts[1:]):
        a=np.array(a,np.float32);b=np.array(b,np.float32);ab=b-a;t=np.clip(((P-a)@ab)/max(ab@ab,1e-12),0,1);d=np.minimum(d,np.linalg.norm(P-(a+t[...,None]*ab),axis=2))
    return d
def vnoise3(P,freq,seed=0,octaves=3):
    """smooth 3D value noise of baked positions (H,W,3) → 0..1, for lichen, stains and patches that must not look gridded"""
    out=np.zeros(P.shape[:2],np.float32);amp=1;tot=0
    for o in range(octaves):
        Q=P*freq*(2**o)+seed*17.3+o*3.1;I=np.floor(Q).astype(np.int64);F=Q-I;F=F*F*(3-2*F)
        def h(dx,dy,dz):
            n=(I[...,0]+dx)*73856093^(I[...,1]+dy)*19349663^(I[...,2]+dz)*83492791^(seed*2654435761+o)
            n=(n^(n>>13))*1274126177;return ((n^(n>>16))&0xffff).astype(np.float32)/65535
        x0=h(0,0,0)*(1-F[...,0])+h(1,0,0)*F[...,0];x1=h(0,1,0)*(1-F[...,0])+h(1,1,0)*F[...,0]
        x2=h(0,0,1)*(1-F[...,0])+h(1,0,1)*F[...,0];x3=h(0,1,1)*(1-F[...,0])+h(1,1,1)*F[...,0]
        y0=x0*(1-F[...,1])+x1*F[...,1];y1=x2*(1-F[...,1])+x3*F[...,1];out+=amp*(y0*(1-F[...,2])+y1*F[...,2]);tot+=amp;amp*=.5
    return out/tot
def lichen(P,cell,seed,cover):
    """crustose lichen rosettes on baked positions: one lobed disc per Voronoi cell (a share `cover` of the cells),
    pale cream / grey-green with a few rust-orange ones, darker rim → (mask 0..1, colour HxWx3)"""
    H,W,_=P.shape;mask=np.zeros((H,W),np.float32);colr=np.zeros((H,W,3),np.float32)
    pal=np.array([[.80,.79,.64],[.70,.72,.52],[.74,.74,.70],[.80,.56,.26]],np.float32)
    for y0 in range(0,H,512):
        Q=P[y0:y0+512]/cell;b1,hid=vcell(P[y0:y0+512],cell,seed)
        u=((hid>>30)&1023)/1023.;v=((hid>>40)&1023)/1023.;act=u<cover
        rad=.18+.3*v;lobe=.06*np.sin(np.arctan2(Q[...,1]-np.floor(Q[...,1]),Q[...,0]-np.floor(Q[...,0]))*7+v*20)
        Pc=P[y0:y0+512];clus=np.clip((vnoise3(Pc,.6/cell,seed+5,2)-.42)*5,0,1);rag=vnoise3(Pc,4/cell,seed+6,2)   # colonies, ragged edge
        r_=b1/(rad+lobe)*(.8+.4*rag);mk=np.clip((1-r_)*5,0,1)*act*clus*(.55+.45*np.clip((rag-.25)*3,0,1));rim=np.clip(1-np.abs(r_-.9)*8,0,1)*act*clus
        ci=np.where(v<.12,3,(u*3/max(cover,1e-3)).astype(np.int64)%3);c=pal[ci]*(1-.25*rim[...,None])
        mask[y0:y0+512]=mk;colr[y0:y0+512]=c
    return mask,colr
def run(pid):
    sel_txt=(REF/REFDIR.get(pid,pid)/'prompt.txt').read_text(encoding='utf-8')
    assert '選用：' in sel_txt,f'{pid}: pick a saved AI three-view before modelling'
    bpy.ops.wm.read_factory_settings(use_empty=True);parts.clear();GLOW.clear()
    sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.render.engine='CYCLES';dev=gpu(sc);sc.cycles.samples=16;sc.render.bake.margin=6;sc.render.bake.margin_type='EXTEND'
    M=make_sources();meta=PROPS[pid](M)
    moved=settle(pid)
    if moved:print(f'SETTLE {pid}: {len(moved)} loose pieces moved onto their support, largest {max(moved.values())} mm',sorted(moved.items(),key=lambda x:-x[1])[:12]);meta['settled']=moved
    def sel(*obs):
        bpy.ops.object.select_all(action='DESELECT')
        for o in obs:o.select_set(True)
        bpy.context.view_layer.objects.active=obs[0]
    pts=np.array([(o.matrix_world@v.co)[:] for o in parts if not o.get('nobounds') for v in o.data.vertices]);lo,hi=pts.min(0),pts.max(0)
    off=Vector((-(lo[0]+hi[0])/2,-(lo[1]+hi[1])/2,-lo[2]))
    for o in parts:o.data.transform(Matrix.Translation(off))
    meta['offset']=np.array(off[:])
    srcparts=list(parts);groups={}
    for o in srcparts:groups.setdefault(o['grp'],[]).append(o)
    decals=meta.get('decals',{})
    G={}
    for g,objs in groups.items():
        cp=[]
        for o in objs:d=o.copy();d.data=o.data.copy();sc.collection.objects.link(d);cp.append(d)
        sel(*cp);bpy.ops.object.join();o=bpy.context.object;o.name=o.data.name=f'{pid}_{g}_LOD0'
        bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.triangulate(bm,faces=bm.faces)
        # faces lying on the ground and facing straight down are never seen, and where two parts stand side by side
        # their bottoms overlap in one plane (z-fighting in QA): drop them
        bm.normal_update();bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.normal.z<-.95 and max(v.co.z for v in f.verts)<.02],context='FACES')
        # sub-pixel crumbs left by remeshing (edges under 2 mm on triangles under 2 mm2) bake to zero-area UV: collapse them
        bmesh.ops.dissolve_degenerate(bm,dist=.002,edges=list({e for f in bm.faces if f.calc_area()<2e-6 for e in f.edges}))
        bmesh.ops.triangulate(bm,faces=bm.faces[:])
        sl={min(f.edges,key=lambda e:e.calc_length()) for f in bm.faces if f.calc_area()<1e-6 and min(e.calc_length() for e in f.edges)<.001}
        if sl:bmesh.ops.collapse(bm,edges=list(sl));bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3])   # #64 follow-up: slivers under 1 mm2 with a sub-mm side (two on the weir crest still had a zero-area UV)
        meta.setdefault('slivers',{})[g]=len(sl)
        meta.setdefault('unfolded',{})[g]=unfold(bm);print('@@UNFOLD',pid,g,meta['unfolded'][g],'slivers',meta['slivers'][g],len(bm.faces))   # #64 follow-up: folds the QA used to find only across UV seams
        for _ in range(6):   # #64 follow-up: one 1 mm lift left three weed strands still overlapping; repeat until none are
            if not separate_coplanar(bm):break
        bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')   # loose vertices: Unity and glTF drop them, but they widened model_info's size (UP05_CushionOld 0.531 vs 0.495)
        bm.to_mesh(o.data);bm.free()
        if g in decals:   # decal sheet keeps its own 0-1 UV ('Tiled'), no bake
            o.data.uv_layers['Tiled'].name='Bake';G[g]=o;continue
        for u in [u for u in o.data.uv_layers if u.name not in ('Tiled','Strip')]:o.data.uv_layers.remove(u)
        bu=o.data.uv_layers.new(name='Bake');o.data.uv_layers.active=bu;sel(o)
        res=GROUP_RES[pid][g];mg=16/res   # island gap 16 px > bake bleed 6 px, so no island paints over its neighbour
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(55),island_margin=mg,area_weight=0,scale_to_bounds=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        me=o.data;sa=me.attributes.get('strip')
        if sa and 'Strip' in me.uv_layers:   # tubes (rope plies, bamboo, cords): one island per tube, not one per face
            nl=len(me.loops);nf=len(me.polygons);fl=np.zeros(nf,np.int32);sa.data.foreach_get('value',fl)
            ls=np.zeros(nf,np.int64);me.polygons.foreach_get('loop_start',ls);lt=np.zeros(nf,np.int64);me.polygons.foreach_get('loop_total',lt)
            lf=np.repeat(fl,lt).astype(bool);su=np.zeros(nl*2);me.uv_layers['Strip'].data.foreach_get('uv',su);bk=np.zeros(nl*2);me.uv_layers['Bake'].data.foreach_get('uv',bk)
            su=su.reshape(nl,2);bk=bk.reshape(nl,2);bk[lf]=su[lf]*.05;me.uv_layers['Bake'].data.foreach_set('uv',bk.ravel())
        if 'Strip' in me.uv_layers:me.uv_layers.remove(me.uv_layers['Strip'])
        if sa:me.attributes.remove(sa)
        me.uv_layers.active=me.uv_layers['Bake'];bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.select_all(action='SELECT')
        bpy.ops.uv.average_islands_scale()
        # 'SCALED' margin shrinks with the island count; a group of only a few islands (the 3-island charcoal stick) came out 2 px apart: pack those at an exact fraction
        bpy.ops.uv.pack_islands(margin=mg,rotate=True,**({'margin_method':'FRACTION'} if (pid,g) in EXACT_MARGIN else {}))
        bpy.ops.object.mode_set(mode='OBJECT');G[g]=o
    # #64 follow-up: a loose piece (a grass blade the settle step laid on a stone) lying flat against another group's face
    # z-fights across the two objects; it moves 1 mm off that face, along the face's normal
    from mathutils.bvhtree import BVHTree
    for lg in [g for g in G if g in ('Plants','Debris','Gravel')]:
        for og in [g for g in G if g!=lg and g not in decals]:
            for _ in range(4):
                bl=bmesh.new();bl.from_mesh(G[lg].data);bo=bmesh.new();bo.from_mesh(G[og].data)
                for b_ in (bl,bo):b_.faces.ensure_lookup_table();b_.normal_update()
                tl=BVHTree.FromBMesh(bl,epsilon=.0005);to=BVHTree.FromBMesh(bo,epsilon=.0005);mv={}
                for i,j in tl.overlap(to):
                    a,b=bl.faces[i],bo.faces[j]
                    if abs(a.normal.dot(b.normal))<math.cos(math.radians(1.5)):continue
                    A=[v.co for v in a.verts];B=[v.co for v in b.verts]
                    if max(abs((p-B[0]).dot(b.normal)) for p in A)>.0005 or _sat(A,B,b.normal)<.001:continue
                    mv.setdefault(a.verts[0].index,b.normal.copy())
                if mv:
                    isl=[-1]*len(bl.verts);bl.verts.ensure_lookup_table()
                    for s0,nrm in mv.items():   # the whole connected piece moves
                        if isl[s0]>=0:continue
                        st=[bl.verts[s0]];isl[s0]=1;piece=[]
                        while st:
                            w=st.pop();piece.append(w)
                            for e in w.link_edges:
                                u=e.other_vert(w)
                                if isl[u.index]<0:isl[u.index]=1;st.append(u)
                        for w in piece:G[lg].data.vertices[w.index].co+=nrm*.001
                    G[lg].data.update();meta.setdefault('lifted_off',{}).setdefault(f'{lg} x {og}',0);meta['lifted_off'][f'{lg} x {og}']+=len(mv)
                bl.free();bo.free()
                if not mv:break
    for o in sc.objects:o.hide_render=o not in G.values() or o.name.split('_LOD')[0][len(pid)+1:] in decals
    tex={}
    padmask=[None]
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
        im.pixels.foreach_set(np.ascontiguousarray(rgba,dtype=np.float32).ravel());im.filepath_raw=str(TEX/f'{name}.png');im.file_format='PNG'
        for t_ in range(4):   # Windows sometimes refuses to overwrite a PNG another process just read ("Invalid argument"): drop the old file and retry
            try:
                (TEX/f'{name}.png').unlink(missing_ok=True);im.save();break
            except (RuntimeError,PermissionError):
                if t_==3:raise
                import time;time.sleep(2)
        return im
    for g,o in G.items():
        RES=GROUP_RES[pid][g];key=f'{pid}_{g}';one=np.ones((RES,RES),np.float32);padmask[0]=None
        if g in decals:   # painted directly: RGBA charcoal lines, alpha-blended
            rgba=decals[g](RES);T={'alb':save(f'{key}_Albedo',rgba,RES),'decal':True}
            T['nrm']=save(f'{key}_Normal',np.dstack([.5*one,.5*one,one,one]),RES,True);T['orm']=save(f'{key}_ORM',np.dstack([one,.95*one,0*one,one]),RES,True)
            save(f'{key}_MaskURP',np.dstack([0*one,one,0*one,.05*one]),RES,True);tex[g]=T;continue
        mats=list(o.data.materials)
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
        filled=np.abs(pos).sum(2)>1e-7;padmask[0]=filled;q=pos-meta['offset'];px,py,pz=pos[...,0],pos[...,1],pos[...,2];H=hi[2]-lo[2]
        # painterly finish: cool blue-violet shade in occlusion, warm light on top, worn warm edges
        cool=np.array([.30,.32,.46]);col=alb[...,:3]*(.42+.58*ao[...,None])+(1-ao[...,None])*cool*.12
        col=col*(1-.45*cav[...,None])+cav[...,None]*np.array([.10,.09,.07])*.45
        col=col*(1+.08*np.clip(pz/max(H,.3),0,1)[...,None]*np.array([1.0,.85,.6]))
        wear=np.clip(edge,0,1)[...,None]*(met[...,None]<.1)*(glow[...,None]<.5)*meta.get('wear',1);col=np.clip(col*(1+.35*wear)+wear*np.array([.06,.05,.03]),0,1)
        mc=MOTTLE.get(pid,{}).get(g)
        if mc:   # angular hand-painted colour patches: each Voronoi cell a little lighter/darker, bluer or more ochre
            for y0 in range(0,RES,512):
                _,hid=vcell(q[y0:y0+512].astype(np.float32),mc,sum(map(ord,pid))+3);u=((hid>>30)&1023)/1023.;v=((hid>>40)&1023)/1023.
                hue=np.where((v<.3)[...,None],np.array([.93,.97,1.07]),np.where((v>.72)[...,None],np.array([1.08,1.0,.84]),1.))
                col[y0:y0+512]=col[y0:y0+512]*(.94+.11*u)[...,None]*(1+(hue-1)*.45)
        # moss on up-facing surfaces and in joints (amount per group)
        mn=np.clip((onrm[...,2]-.35)/.5,0,1)
        n1=np.sin(px*7.3+np.sin(py*5.1+pz*2.3)*1.7)*np.sin(py*6.7+np.sin(pz*4.3+px*2.1)*1.9);n2=np.sin(px*23.1+np.sin(py*19.7)*1.3)*np.sin(pz*21.3+py*13.9)
        sc_=meta.get('moss_scale',1);n1=np.sin(px*7.3*sc_+np.sin(py*5.1*sc_+pz*2.3*sc_)*1.7)*np.sin(py*6.7*sc_+np.sin(pz*4.3*sc_+px*2.1*sc_)*1.9)
        noise=np.clip(.5+.42*n1+.18*n2,0,1);m=np.zeros_like(pz)
        amt=MOSS.get(pid,{}).get(g,0)
        if amt:
            ml=meta.get('moss_low',0);mh=meta.get('moss_h',.5)
            low=np.clip(1-pz/mh,0,1)*ml
            creep=np.clip(1-pz/(mh*.6),0,1)*ml*.9+cav*meta.get('moss_cav',.5)
            m=np.clip((mn*(low+meta.get('moss_top',.15))+creep)*amt*2*np.clip((noise-.38)*3.5,0,1),0,1)*filled*(glow<.5)
            mcol=np.array(meta.get('moss_col',(.27,.36,.13)))+np.array([.10,.10,.04])*noise[...,None]
            col=col*(1-m[...,None])+mcol*m[...,None];rough=np.clip(rough+.15*m,0,1)
        lc=LICHEN.get(pid,{}).get(g)
        if lc:   # lichen rosettes on the open, lit stone; not in cavities, under moss or on the bed
            lm,lcol=lichen(q.astype(np.float32),lc[0],sum(map(ord,pid)),lc[1]);sm,scol=lichen(q.astype(np.float32),lc[0]*.3,sum(map(ord,pid))+1,lc[1]*.7)   # big colonies + fine speckle
            k_=sm>lm;lcol=np.where(k_[...,None],scol,lcol);lm=np.maximum(lm,.8*sm);lm=lm*filled*(1-m)*(1-cav)*np.clip((onrm[...,2]+.6)/.6,0,1)*(glow<.5)
            col=col*(1-.85*lm[...,None])+lcol*(.85+.15*noise[...,None])*.85*lm[...,None];rough=np.clip(rough+.1*lm,0,1)
        if meta.get('soil'):
            s_=np.clip((meta['soil']-pz)/meta['soil'],0,1)*filled*(met<.5);col=col*(1-.45*s_[...,None])+np.array([.26,.20,.14])*.45*s_[...,None]
        extra={}
        if meta.get('paint'):col,rough,extra=meta['paint'](g,col,rough,q,onrm,ao,cav,edge,m,filled,glow,noise,RES)
        T={'alb':save(f'{key}_Albedo',np.dstack([np.clip(col,0,1),one]),RES),'nrm':save(f'{key}_Normal',nrm,RES,True),
           'orm':save(f'{key}_ORM',np.dstack([ao,rough,met,one]),RES,True)}
        save(f'{key}_MaskURP',np.dstack([met,ao,0*one,1-rough]),RES,True)
        for k,v in extra.items():   # extra state maps, e.g. Albedo_Warm / WarmthMask / Emission
            T[k]=save(f'{key}_{k}',v,RES,k not in ('Albedo_Warm','Emission'))
        if 'Emission' not in T and glow.max()>.5:   # lamp paper: emission colour = light through the paper albedo
            ec=np.array(meta.get('emit_tint',(1.25,.95,.62)));em=np.clip(alb[...,:3]*ec*(glow[...,None]>.5),0,1);T['Emission']=save(f'{key}_Emission',np.dstack([em,one]),RES)
        tex[g]=T
    # final materials, LODs, root, state drivers
    root=bpy.data.objects.new(f'{pid}_GroundOrigin',None);sc.collection.objects.link(root)
    st=meta.get('state')   # {'prop': 'lit'|'warmth', 'param': '_Lit'|'_Warmth', 'default': 0, 'export': 1}
    if st:root[st['prop']]=st['default']
    # a moving part (UP01 gate): its LOD meshes and collider sit directly under the root with their origin at the pivot.
    # No empty in between: the FBX exporter's baked axis conversion turns meshes parented to a non-root empty on their side.
    pivots={g:(name,Vector(p)+off) for g,(name,p) in meta.get('pivots',{}).items()};moving={}
    def drive(sock,expr):
        fc=sock.driver_add('default_value');dr=fc.driver;dr.type='SCRIPTED';v=dr.variables.new();v.name='s'
        v.targets[0].id=root;v.targets[0].data_path=f'["{st["prop"]}"]';dr.expression=expr
    lods=[]
    for g,o in G.items():
        T=tex[g];fm=bpy.data.materials.new(f'{pid}_{g}');fm.use_nodes=True;nt=fm.node_tree;bs=nt.nodes['Principled BSDF']
        def tn(im):t=nt.nodes.new('ShaderNodeTexImage');t.image=im;return t
        ta=tn(T['alb'])
        if 'Albedo_Warm' in T and st:
            mx=nt.nodes.new('ShaderNodeMix');mx.data_type='RGBA';nt.links.new(ta.outputs['Color'],mx.inputs[6]);nt.links.new(tn(T['Albedo_Warm']).outputs['Color'],mx.inputs[7])
            nt.links.new(mx.outputs[2],bs.inputs['Base Color']);drive(mx.inputs[0],'s')
        else:nt.links.new(ta.outputs['Color'],bs.inputs['Base Color'])
        if T.get('decal'):
            nt.links.new(ta.outputs['Alpha'],bs.inputs['Alpha']);fm.surface_render_method='BLENDED' if hasattr(fm,'surface_render_method') else None
        nmn=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tn(T['nrm']).outputs['Color'],nmn.inputs['Color']);nt.links.new(nmn.outputs['Normal'],bs.inputs['Normal'])
        sp=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tn(T['orm']).outputs['Color'],sp.inputs['Color']);nt.links.new(sp.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sp.outputs['Blue'],bs.inputs['Metallic'])
        if 'Emission' in T:
            nt.links.new(tn(T['Emission']).outputs['Color'],bs.inputs['Emission Color'])
            if st:drive(bs.inputs['Emission Strength'],st['emit_expr'])
            else:bs.inputs['Emission Strength'].default_value=1.0
        group=[o]
        for L,ratio in ((1,.5),(2,.15)):
            d=o.copy();d.data=o.data.copy();sc.collection.objects.link(d);d.name=d.data.name=f'{pid}_{g}_LOD{L}'
            m=d.modifiers.new('d','DECIMATE');m.ratio=ratio;m.use_collapse_triangulate=True;sel(d);bpy.ops.object.modifier_apply(modifier='d');group.append(d)
        for d in group:
            uvs=d.data.uv_layers
            if 'Tiled' in uvs:uvs.remove(uvs['Tiled'])
            uvs['Bake'].name='UVMap';d.data.materials.clear();d.data.materials.append(fm);d.hide_render=not d.name.endswith('LOD0')
            if g in pivots:d.data.transform(Matrix.Translation(-pivots[g][1]));d.location=pivots[g][1];moving.setdefault(g,[]).append(d.name)   # origin at the pivot
            d.parent=root
        lods.append(group)
    bpy.context.view_layer.update();pts=np.array([(gr[0].matrix_world@v.co)[:] for gr in lods for v in gr[0].data.vertices]);lo,hi=pts.min(0),pts.max(0);dims=hi-lo
    cols,colinfo=collision(pid,meta,[gr[0] for gr in lods])
    for c in cols:
        g=meta.get('collision_parent',{}).get(c.name[len(pid)+1:])
        if g in pivots:c.data.transform(Matrix.Translation(-pivots[g][1]));c.location=pivots[g][1];moving.setdefault(g,[]).append(c.name)
        c.parent=root
    socks={}
    for name,p in meta.get('sockets',{}).items():
        ls=bpy.data.objects.new(name,None);sc.collection.objects.link(ls);ls.location=Vector(p)+off;ls.parent=root;socks[name]=[round(float(v),3) for v in ls.location]
    lim=LIMITS[pid];fits=bool(all(dims[i]<=lim[i]+1e-6 for i in range(3)))
    src=bpy.data.collections.new(f'{pid}_SourceParts');sc.collection.children.link(src)
    for o in srcparts:
        for c in list(o.users_collection):c.objects.unlink(o)
        src.objects.link(o);o.hide_render=True;o.hide_set(True)
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE/f'{pid}.blend'),compress=True)
    if st:root[st['prop']]=st['export'];bpy.context.view_layer.update()   # export carries the state maps at full strength
    extra=[o for o in sc.objects if o.type=='EMPTY' and o is not root]
    sel(root,*[gr[0] for gr in lods],*extra);bpy.ops.export_scene.gltf(filepath=str(OUT/f'{pid}.glb'),use_selection=True,export_format='GLB',export_apply=True)
    sel(root,*[d for gr in lods for d in gr],*cols,*extra);bpy.ops.export_scene.fbx(filepath=str(OUT/f'{pid}.fbx'),use_selection=True,object_types={'MESH','EMPTY'},global_scale=1.0,apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_ALL',bake_space_transform=True,axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='FACE',
        use_tspace=True,add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE',embed_textures=False)
    tri=lambda o:sum(len(p.vertices)-2 for p in o.data.polygons)
    info={'id':pid,'slot':SLOTS[pid],'device':dev,'dimensions_xyz_m':[round(float(x),3) for x in dims],'size_limit_m':lim,'fits_limit':fits,
          'groups':{g:{'material':f'{pid}_{g}','texture_px':GROUP_RES[pid][g],'triangles':[tri(d) for d in gr],'maps':sorted(k for k in tex[g] if k not in ('decal',)),
                       **({'pivot':pivots[g][0]} if g in pivots else {})} for g,gr in zip(G,lods)},
          'triangles_total':[sum(tri(gr[i]) for gr in lods) for i in range(3)],'source_parts':len(srcparts),
          'reference':f'art/references/{PKG}/{REFDIR.get(pid,pid)}/prompt.txt','origin':'footprint centre, bottom z = 0, front = -Y (Blender) / -Z (FBX, Unity)',
          'textures':'per group: Albedo / Normal / MaskURP (R metal, G AO, A smoothness) / ORM (glTF) [+ Emission, state maps]','collision':colinfo,'sockets':socks}
    if pivots:info['pivots']={pivots[g][0]:{'position':[round(float(v),3) for v in pivots[g][1]],'objects':moving[g]} for g in pivots}
    if st:info['state']={k:v for k,v in st.items() if k!='emit_expr'}|{'emission_strength_blender':st['emit_expr'].replace('s',st['param'])}
    if 'heights' in meta:   # heights were written in the build frame; move them with the footprint recentring, like sockets and collision
        oz=float(meta['offset'][2]);meta['heights']={k:(([round(x+oz,3) for x in v] if isinstance(v,list) else round(v+oz,3)) if k.endswith('_z') else v) for k,v in meta['heights'].items()}
    for k in ('states','notes','heights'):
        if k in meta:info[k]=meta[k]
    print('DAY34_DONE',json.dumps(info,ensure_ascii=False));return info
ids=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [k for k in PROPS if k!='UP05_Burner']
if 'UP05_Burner' in ids and '--old-burner' not in sys.argv:   # round 3: the shipped burner is the Codex build (build_up05_burner.py)
    sys.exit('UP05_Burner now comes from build_up05_burner.py; pass --old-burner to rebuild the round-2 version')
ids=[i for i in ids if i!='--old-burner']
infos=[run(i) for i in ids]
mf=OUT/'model_info.json';old=json.loads(mf.read_text(encoding='utf-8')) if mf.exists() else {}
old.update({i['id']:i for i in infos});mf.write_text(json.dumps(dict(sorted(old.items())),ensure_ascii=False,indent=1),encoding='utf-8')
