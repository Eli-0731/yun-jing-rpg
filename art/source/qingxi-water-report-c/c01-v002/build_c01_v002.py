"""C01 village council table v002 — Eli-0731, Blender 4.5.3 LTS.
Rebuilds C01 against the saved AI three-view (art/references/qingxi-water-report-c/C01-three-view.png).
v001 (build.py, C01.glb) is left untouched.
blender -b --factory-startup -P build_c01_v002.py
"""
import bpy,bmesh,math,json,random
from pathlib import Path
from mathutils import Vector,Matrix
import numpy as np

ROOT=Path(__file__).resolve().parents[4]
REF=ROOT/'art/references/qingxi-water-report-c/C01-three-view.png'
SRC=Path(__file__).resolve().parent
TEX=ROOT/'art/textures/qingxi-water-report-c/c01-v002'
OUT=ROOT/'art/exports/qingxi-water-report-c/c01-v002'
assert REF.stat().st_size>10000,'three-view must exist before modeling'
for p in [TEX,OUT]:p.mkdir(parents=True,exist_ok=True)
rng=np.random.default_rng(1029);random.seed(1029)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.unit_settings.system='METRIC'

# ---------- textures: tileable, 512 px per 0.5 m (1024 px/m) ----------
R=512
def tile_noise(cx,cy,res=R):
    g=rng.random((cy,cx));x=np.linspace(0,cx,res,endpoint=False);y=np.linspace(0,cy,res,endpoint=False)
    xi=x.astype(int);yi=y.astype(int);fx=x-xi;fy=y-yi;fx=fx*fx*(3-2*fx);fy=fy*fy*(3-2*fy)
    a=g[np.ix_(yi%cy,xi%cx)];b=g[np.ix_(yi%cy,(xi+1)%cx)];c=g[np.ix_((yi+1)%cy,xi%cx)];d=g[np.ix_((yi+1)%cy,(xi+1)%cx)]
    fx=fx[None,:];fy=fy[:,None];return (a*(1-fx)+b*fx)*(1-fy)+(c*(1-fx)+d*fx)*fy
def fbm(c0,oct=4,aniso=1):
    v=0;amp=.5;tot=0
    for o in range(oct):v=v+amp*tile_noise(c0*2**o,max(1,int(c0*2**o/aniso)));tot+=amp;amp*=.5
    return v/tot
def lerp(a,b,t):return np.asarray(a)[None,None,:]*(1-t[...,None])+np.asarray(b)[None,None,:]*t[...,None]
def save(name,rgb):
    im=bpy.data.images.new(name,R,R);a=np.ones((R,R,4),np.float32);a[...,:3]=np.clip(rgb,0,1);im.pixels.foreach_set(a.ravel())
    p=TEX/f'{name}.png';im.filepath_raw=str(p);im.file_format='PNG';im.save();return im
X=np.arange(R)[None,:]/R
# wood: grain runs along V (image rows = Y). warped stripes + long streaks + sparse dark checks
warp=fbm(2,2);streak=fbm(24,3,aniso=8);grain=.5+.5*np.sin(math.tau*(X*11+warp*.45))
grain=grain**3;cracks=np.clip((fbm(40,2,aniso=12)-.68)*7,0,1)
t=np.clip(.58-.16*grain+.22*(streak-.5)-.30*cracks,0,1)
WOODTEX=save('C01_wood_albedo',lerp((.27,.19,.13),(.55,.42,.30),t))
pat=np.clip((fbm(6,4)-.60)*3,0,.7)
BRONZETEX=save('C01_bronze_albedo',lerp((.50,.40,.24),(.34,.40,.33),pat)*(.90+.18*fbm(32,2))[...,None])
STONETEX=save('C01_stone_albedo',lerp((.36,.36,.34),(.60,.58,.53),fbm(8,5)))
INLAYTEX=save('C01_inlay_albedo',lerp((.13,.13,.11),(.27,.26,.21),fbm(10,4)))
twist=.5+.5*np.sin(math.tau*((X+np.arange(R)[:,None]/R)*16))
HEMPTEX=save('C01_hemp_albedo',lerp((.30,.22,.14),(.52,.42,.28),np.clip(twist*.7+.3*fbm(32,2),0,1)))

def material(name,im,rough,metal=0.):
    m=bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes['Principled BSDF']
    bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
    tx=m.node_tree.nodes.new('ShaderNodeTexImage');tx.image=im;m.node_tree.links.new(tx.outputs['Color'],bs.inputs['Base Color'])
    return m
WOOD=material('C01_Wood',WOODTEX,.72);BRONZE=material('C01_AgedBronze',BRONZETEX,.50,.30)
STONE=material('C01_Stone',STONETEX,.86);INLAY=material('C01_InlayRecess',INLAYTEX,.70);HEMP=material('C01_Hemp',HEMPTEX,.92)

# ---------- helpers ----------
parts=[]
def obj_from_bm(name,bm,mat,basis,origin=Vector(),uvoff=(0,0)):
    """basis=(A,S1,S2): grain/V runs along A. 0.5 m = one texture tile."""
    A,S1,S2=[Vector(v).normalized() for v in basis];uv=bm.loops.layers.uv.verify()
    for f in bm.faces:
        n=f.normal;c=[abs(n.dot(A)),abs(n.dot(S1)),abs(n.dot(S2))];k=c.index(max(c))
        for l in f.loops:
            p=l.vert.co-origin;u,v={0:(p.dot(S1),p.dot(S2)),1:(p.dot(S2),p.dot(A)),2:(p.dot(S1),p.dot(A))}[k]
            l[uv].uv=(u/.5+uvoff[0],v/.5+uvoff[1])
    me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free();o=bpy.data.objects.new(name,me);sc.collection.objects.link(o);me.materials.append(mat)
    for poly in me.polygons:poly.use_smooth=False
    parts.append(o);return o
def bevel(o,width,segs=2,angle=35):
    m=o.modifiers.new('worn_edges','BEVEL');m.width=width;m.segments=segs;m.limit_method='ANGLE';m.angle_limit=math.radians(angle);m.harden_normals=False
    bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.modifier_apply(modifier=m.name);o.select_set(False)
def prism(outline,z0,z1):
    """outline: list of (x,y) CCW; returns closed bmesh prism."""
    bm=bmesh.new();lo=[bm.verts.new((x,y,z0)) for x,y in outline];hi=[bm.verts.new((x,y,z1)) for x,y in outline]
    bm.faces.new(list(reversed(lo)));bm.faces.new(hi);n=len(outline)
    for i in range(n):bm.faces.new((lo[i],lo[(i+1)%n],hi[(i+1)%n],hi[i]))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces);return bm
def rounded_rect(w,h,r,seg=2):
    pts=[]
    for cx,cy,a0 in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
        for i in range(seg+1):a=math.radians(a0+90*i/seg);pts.append((cx+r*math.cos(a),cy+r*math.sin(a)))
    return pts
def loft(name,a,b,sec_a,sec_b,mat,rings=5,wobble=0.,side=None,caps=True):
    """Hand-hewn member from a to b with rounded-rect sections (w,h,r) tapering; one face looks along `side`."""
    a,b=Vector(a),Vector(b);A=(b-a).normalized();S=Vector(side or (0,0,1));S=(S-A*S.dot(A)).normalized();T=A.cross(S)
    bm=bmesh.new();loops=[]
    for i in range(rings):
        t=i/(rings-1);w=sec_a[0]+(sec_b[0]-sec_a[0])*t;h=sec_a[1]+(sec_b[1]-sec_a[1])*t
        off=(T*random.uniform(-1,1)+S*random.uniform(-1,1))*wobble*math.sin(math.pi*t);c=a+(b-a)*t+off
        loops.append([bm.verts.new(c+S*x+T*y) for x,y in rounded_rect(w,h,sec_a[2])])
    n=len(loops[0])
    for r0,r1 in zip(loops,loops[1:]):
        for i in range(n):bm.faces.new((r0[i],r0[(i+1)%n],r1[(i+1)%n],r1[i]))
    if caps:bm.faces.new(list(reversed(loops[0])));bm.faces.new(loops[-1])
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces);return obj_from_bm(name,bm,mat,(A,S,T),a)
def torus(name,center,axis,R0,r,mat,seg=14,mseg=4):
    bm=bmesh.new();ax=Vector(axis).normalized();u=ax.orthogonal().normalized();v=ax.cross(u);rows=[]
    for i in range(seg):
        a=math.tau*i/seg;d=u*math.cos(a)+v*math.sin(a);rows.append([bm.verts.new(Vector(center)+d*(R0+r*math.cos(math.tau*j/mseg+math.pi/4))+ax*r*math.sin(math.tau*j/mseg+math.pi/4)) for j in range(mseg)])
    for i in range(seg):
        for j in range(mseg):bm.faces.new((rows[i][j],rows[(i+1)%seg][j],rows[(i+1)%seg][(j+1)%mseg],rows[i][(j+1)%mseg]))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces);return obj_from_bm(name,bm,mat,(u.cross(ax),ax,u),Vector(center))
def disk(name,center,r,z0,z1,mat,seg=24,inner=0.):
    if inner:
        bm=bmesh.new();o=[];i_=[]
        for z in (z0,z1):
            o.append([bm.verts.new((center[0]+r*math.cos(math.tau*k/seg),center[1]+r*math.sin(math.tau*k/seg),z)) for k in range(seg)])
            i_.append([bm.verts.new((center[0]+inner*math.cos(math.tau*k/seg),center[1]+inner*math.sin(math.tau*k/seg),z)) for k in range(seg)])
        for k in range(seg):
            k1=(k+1)%seg
            bm.faces.new((o[1][k],i_[1][k],i_[1][k1],o[1][k1]));bm.faces.new((o[0][k],o[0][k1],i_[0][k1],i_[0][k]))
            bm.faces.new((o[0][k],o[1][k],o[1][k1],o[0][k1]));bm.faces.new((i_[0][k],i_[0][k1],i_[1][k1],i_[1][k]))
        bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    else:bm=prism([(center[0]+r*math.cos(math.tau*k/seg),center[1]+r*math.sin(math.tau*k/seg)) for k in range(seg)],z0,z1)
    return obj_from_bm(name,bm,mat,((0,1,0),(1,0,0),(0,0,1)),Vector((*center,0)))
def emblem(name,outline,center,z0,z1,mat):
    cx,cy=center;bm=prism([(cx+x,cy+y) for x,y in outline],z0,z1)
    bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>4])
    return obj_from_bm(name,bm,mat,((0,1,0),(1,0,0),(0,0,1)),Vector((cx,cy,0)))

TOP0,TOP1=.562,.618   # 56 mm thick top; medallions rise to ~0.625 → overall 0.63 m like v001/plan
# ---------- primary: six radial wedges (seams at 30°+60°k, as in the reference top view) ----------
for k in range(6):
    a0=math.radians(30+60*k);a1=a0+math.radians(60);gap=.0009
    def edge(a,r,sgn):  # offset seam sides by half the gap
        d=Vector((math.cos(a),math.sin(a)));nrm=Vector((-d.y,d.x))*sgn;return tuple(d*r+nrm*gap)
    out=[edge(a0,.118,1)]+[(r*math.cos(a),r*math.sin(a)) for i in range(11) for a in [a0+(a1-a0)*(.02+.96*i/10)] for r in [.550+random.uniform(-.003,.003)]]+[edge(a1,.118,-1)]
    inner=[(.118*math.cos(a0+(a1-a0)*i/4),.118*math.sin(a0+(a1-a0)*i/4)) for i in (3,2,1)]
    dz=random.uniform(-.0015,.0015);bm=prism(out+inner,TOP0,TOP1+dz)
    mid=(a0+a1)/2;Ar=Vector((math.cos(mid),math.sin(mid),0));o=obj_from_bm(f'Top_Wedge_{k+1}',bm,WOOD,(Ar,Vector((0,0,1)).cross(Ar),(0,0,1)),uvoff=(k*.37,k*.21))
    bevel(o,.0065,2)
# bowtie keys across each seam near the rim
for k in range(6):
    a=math.radians(30+60*k);d=Vector((math.cos(a),math.sin(a)));t=Vector((-d.y,d.x));c=d*.47
    bt=[(-.018,-.010),(-.018,.010),(0,.005),(.018,.010),(.018,-.010),(0,-.005)]
    o=emblem(f'Bowtie_Key_{k+1}',[tuple(t*x+d*y) for x,y in bt],tuple(c),TOP1-.004,TOP1+.0015,WOOD)
# underside radial battens; leg tops seat into them
LEG_ANG=[90,210,330];legs=[]
for i,ang in enumerate(LEG_ANG):
    d=Vector((math.cos(math.radians(ang)),math.sin(math.radians(ang)),0))
    loft(f'Under_Batten_{i+1}',d*.10+Vector((0,0,TOP0-.018)),d*.47+Vector((0,0,TOP0-.018)),(.040,.050,.008),(.040,.050,.008),WOOD,rings=2,side=(0,0,1))
# ---------- centre medallion ----------
disk('Center_Ring_Outer',(0,0),.116,TOP0+.01,TOP1+.007,BRONZE,40,inner=.084)
disk('Center_Disc',(0,0),.085,TOP0+.01,TOP1+.002,BRONZE,32)
disk('Center_Ring_Inner',(0,0),.080,TOP1+.002,TOP1+.0045,BRONZE,32,inner=.072)
# ---------- choice inlays: drop (west), mallet (east), sprout (front/south) ----------
def drop():return [(.011*math.sin(t)*abs(math.sin(t/2))**.9*1.9,.018*math.cos(t)-.002) for t in [math.tau*i/22 for i in range(22)]][::-1]
def mallet():return [(-.022,.006),(-.022,.020),(.022,.020),(.022,.006),(.006,.006),(.006,-.022),(-.006,-.022),(-.006,.006)][::-1]
def leaf(cx,cy,ang,L=.022,W=.009):
    ca,sa=math.cos(ang),math.sin(ang);pts=[]
    for i in range(12):
        t=i/11;pts.append((t*L,W*math.sin(math.pi*t)))
    for i in range(10,0,-1):
        t=i/11;pts.append((t*L,-W*math.sin(math.pi*t)*.6))
    return [(cx+x*ca-y*sa,cy+x*sa+y*ca) for x,y in pts]
INLAYS={'Water':(180,[drop()]),'Repair':(0,[mallet()]),'Sprout':(270,[[(-.0028,-.022),(.0028,-.022),(.0028,.004),(-.0028,.004)],leaf(.001,0,math.radians(35)),leaf(-.001,0,math.radians(145))])}
for nm,(ang,shapes) in INLAYS.items():
    c=(.34*math.cos(math.radians(ang)),.34*math.sin(math.radians(ang)))
    disk(f'Inlay_{nm}_Ring',c,.064,TOP1-.004,TOP1+.0055,BRONZE,32,inner=.050)
    disk(f'Inlay_{nm}_Recess',c,.051,TOP1-.004,TOP1+.0015,INLAY,24)
    for j,s in enumerate(shapes):emblem(f'Inlay_{nm}_Symbol_{j+1}',[(x*1.25,y*1.25) for x,y in s],c,TOP1+.001,TOP1+.0045,BRONZE)
# ---------- legs: chunky, square with chamfer, splayed, hand-hewn ----------
FOOT_R,TOPR=.455,.355;FOOT_Z=.065
for i,ang in enumerate(LEG_ANG):
    d=Vector((math.cos(math.radians(ang)),math.sin(math.radians(ang)),0))
    a=d*FOOT_R+Vector((0,0,FOOT_Z));b=d*TOPR+Vector((0,0,TOP0-.04))
    legs.append((a,b,d));loft(f'Leg_{i+1}',a,b,(.064,.064,.013),(.074,.074,.013),WOOD,rings=6,wobble=.003,side=d)
    A=(b-a).normalized()
    for j in range(4):torus(f'Leg_{i+1}_Rope_{j+1}',a+(b-a)*(.80+.035*j),A,.046,.0062,HEMP,seg=10)
    # bronze strap below the lashing, on the outward face
    p=a+(b-a)*.74;loft(f'Leg_{i+1}_Bronze_Strap',p-A*.022+d*.036,p+A*.022+d*.036,(.004,.030,.0015),(.004,.030,.0015),BRONZE,rings=2,side=d)
    # river-stone foot
    bm=bmesh.new();bmesh.ops.create_uvsphere(bm,u_segments=14,v_segments=7,radius=1)
    for v in bm.verts:
        n=v.co.normalized();j=1+.10*math.sin(n.x*7+i)+.07*math.sin(n.y*9+2*i)+.05*math.sin(n.z*11)
        v.co=Vector((n.x*.078*j,n.y*.072*j,n.z*.060*j))
        if v.co.z<-.018:v.co.z=-.018
    bmesh.ops.translate(bm,verts=bm.verts,vec=Vector((a.x,a.y,.018)))
    for f in bm.faces:f.smooth=True
    o=obj_from_bm(f'Leg_{i+1}_Stone_Foot',bm,STONE,((0,1,0),(1,0,0),(0,0,1)),Vector((a.x,a.y,0)))
    for poly in o.data.polygons:poly.use_smooth=True
# ---------- triangular stretchers with lashed ends ----------
SZ=.19
def on_leg(i,z):a,b,_=legs[i];t=(z-a.z)/(b.z-a.z);return a+(b-a)*t
for i in range(3):
    p,q=on_leg(i,SZ),on_leg((i+1)%3,SZ);A=(q-p).normalized()
    loft(f'Stretcher_{i+1}',p+A*.028,q-A*.028,(.034,.030,.009),(.034,.030,.009),WOOD,rings=4,wobble=.002,side=(0,0,1))
    for e,sgn in [(p,1),(q,-1)]:
        for j in range(2):torus(f'Stretcher_{i+1}_Lash_{"ab"[sgn<0]}{j+1}',e+A*sgn*(.058+.013*j),A,.024,.0055,HEMP,seg=8)
parts_lod0=list(parts)

# ---------- organise source scene ----------
src=bpy.data.collections.new('C01_v002_Parts');sc.collection.children.link(src)
root=bpy.data.objects.new('C01_CouncilTable_v002_GroundOrigin',None);sc.collection.objects.link(root)
for o in parts:
    for c in list(o.users_collection):c.objects.unlink(o)
    src.objects.link(o);o.parent=root
# ---------- export meshes: joined LOD0, decimated LOD1/LOD2, simple collider ----------
exp=bpy.data.collections.new('C01_v002_Export');sc.collection.children.link(exp)
def joined(name,objs):
    cp=[]
    for o in objs:
        d=o.copy();d.data=o.data.copy();d.parent=None;d.matrix_world=o.matrix_world.copy();exp.objects.link(d);cp.append(d)
    bpy.ops.object.select_all(action='DESELECT')
    for d in cp:d.select_set(True)
    bpy.context.view_layer.objects.active=cp[0];bpy.ops.object.join();j=bpy.context.object;j.name=name;j.data.name=name
    bm=bmesh.new();bm.from_mesh(j.data);bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-5);bm.to_mesh(j.data);bm.free();return j
lod0=joined('C01_CouncilTable_LOD0',parts_lod0)
small=[o for o in parts_lod0 if any(k in o.name for k in ('Rope','Lash','Bowtie','Strap','Symbol','Inner','Batten'))]
lod1=joined('C01_CouncilTable_LOD1',[o for o in parts_lod0 if o not in small or 'Symbol' in o.name or 'Rope_1' in o.name or 'Rope_3' in o.name])
m=lod1.modifiers.new('d','DECIMATE');m.ratio=.55;bpy.context.view_layer.objects.active=lod1;bpy.ops.object.modifier_apply(modifier='d')
lod2=joined('C01_CouncilTable_LOD2',[o for o in parts_lod0 if o not in small and 'Inlay' not in o.name])
m=lod2.modifiers.new('d','DECIMATE');m.ratio=.18;bpy.context.view_layer.objects.active=lod2;bpy.ops.object.modifier_apply(modifier='d')
bm=bmesh.new();bmesh.ops.create_cone(bm,cap_ends=True,segments=12,radius1=.555,radius2=.555,depth=TOP1-0.0)
bmesh.ops.translate(bm,verts=bm.verts,vec=Vector((0,0,(TOP1)/2)));col=bpy.data.meshes.new('C01_CouncilTable_Collider');bm.to_mesh(col);bm.free()
colo=bpy.data.objects.new('C01_CouncilTable_Collider',col);exp.objects.link(colo)
for o in (lod0,lod1,lod2,colo):o.parent=None
def tris(o):return sum(len(p.vertices)-2 for p in o.data.polygons)
stats={o.name:{'triangles':tris(o),'vertices':len(o.data.vertices),'materials':len(o.data.materials)} for o in (lod0,lod1,lod2,colo)}
pts=[lod0.matrix_world@v.co for v in lod0.data.vertices];dims=[max(p[i] for p in pts)-min(p[i] for p in pts) for i in range(3)]
# manifold / open-edge check per source part (closed pieces expected)
bad={}
for o in parts_lod0:
    bm=bmesh.new();bm.from_mesh(o.data);open_e=sum(1 for e in bm.edges if not e.is_manifold);bm.free()
    if open_e:bad[o.name]=open_e
bpy.ops.wm.save_as_mainfile(filepath=str(SRC/'C01_CouncilTable_v002.blend'))
bpy.ops.object.select_all(action='DESELECT');lod0.select_set(True);bpy.context.view_layer.objects.active=lod0
bpy.ops.export_scene.gltf(filepath=str(OUT/'C01_CouncilTable_v002.glb'),use_selection=True,export_format='GLB',export_apply=True)
for o in (lod0,lod1,lod2,colo):o.select_set(True)
bpy.ops.export_scene.fbx(filepath=str(OUT/'C01_CouncilTable_v002.fbx'),use_selection=True,object_types={'MESH'},global_scale=1.0,apply_unit_scale=True,
    apply_scale_options='FBX_SCALE_ALL',bake_space_transform=True,axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='FACE',
    use_tspace=True,add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE',embed_textures=False)
report={'asset':'C01_CouncilTable_v002','authors':'Eli-0731','reference':str(REF.relative_to(ROOT)).replace('\\','/'),
 'dimensions_xyz_m':[round(x,4) for x in dims],'source_parts':len(parts_lod0),'stats':stats,'open_edge_parts':bad,
 'textures':{p.name:'512x512' for p in TEX.glob('*.png')},'materials':[m.name for m in lod0.data.materials]}
(OUT/'C01_CouncilTable_v002-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=1),encoding='utf-8')
print('C01V2',json.dumps(report,ensure_ascii=False))
