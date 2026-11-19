"""承天 · C D2 古樹神木的苔與小植物 DP06–DP13（d2-moss-c）— Eli-0731, Blender 4.5.3 LTS.
Work pack: docs/execution/2026-11-15/C-300h-D2-small-life.md batch B, with 00-300h-共同標準.md (D2 setting views V2, V3, V5, V6).
Each item is modelled only after its three-view candidates are saved and one is picked in art/references/<ID>/prompt.txt.
Pipeline: the one of art/source/d2-mushrooms-c/build_dp.py (DP01; itself from yard-roadside-c/build_vg.py): named parts with tiled
source materials → one UV atlas (1024², one material) → Cycles bake → numpy finish → body + Detail_* → LOD1/LOD2.
That package is not on main yet, so the pipeline is copied here; the kit (creekside-life-c/wl_kit.py) and meshfix come from main.
  · origin: footprint centre, z = 0 on the ground; the moss rim lands on z = 0 and a soil skirt runs on below it (standard §四),
    so a clump never floats on uneven ground;
  · the sources are D2 moss (cushion tufts, older brown moss, loose strands) and wet soil, own seeds;
  · moss tops keep a flat top-down 'Tiled' UV so the tufts in the texture never stretch down the sides of a hump.
blender -b --factory-startup -P build_moss.py -- DP06_01 [DP06_02 ...] [--clay]
"""
import bpy,bmesh,json,math,sys,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'creekside-life-c'))
import wl_kit as K
from wl_kit import fbm,lerp,board,finish,tube,rope,box_bm,box,bevel,subdiv,jitter,join,apply,separate_coplanar,parts,link,leaf,tuft
from mathutils import Vector,Matrix
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];PKG='d2-moss-c';CK=ROOT/'art/source/creekside-life-c'   # CK: the shared kit and part helpers
REF=ROOT/'art/references';TEX=ROOT/'art/textures'/PKG;OUT=ROOT/'art/exports'/PKG
sys.path.insert(0,str(ROOT/'art/source/modelling-basics-c'));import meshfix
for p in (TEX,OUT):p.mkdir(parents=True,exist_ok=True)
X=np.arange(K.R)[None,:]/K.R;Y=np.arange(K.R)[:,None]/K.R
RES=1024;VERSION='v001'

# ---------------- tiled source textures (D2 smalls, own seeds) ----------------
def make_sources():
    S={}
    K.rng=np.random.default_rng(5601)   # D2 cushion moss: clumps of tufts 1–2 cm with dark gaps between, fine tips inside; olive, yellow-green on the tufts
    cl=fbm(60,1);cl2=fbm(110,1)
    clump=np.clip((np.maximum(cl,cl2*.92)-.40)*3.2,0,1)   # rounded clumps 5–9 mm; 0 in the dark gaps
    tu=np.clip((fbm(260,1)-.40)*2.6,0,1);big=fbm(6,3);dk=np.clip((fbm(7,3)-.60)*3,0,1)
    t=np.clip(.32+.62*clump*(.65+.35*tu)+.25*(big-.5),0,1)
    col=lerp((.045,.052,.018),(.27,.29,.085),t)   # D2 V6 side by side: lighter olive than v1 of this script*(1-.30*dk[...,None])+dk[...,None]*np.array([.03,.028,.012])
    S['moss']=(col,1.6*clump+.5*tu+.3*big,3.6,.95,0,0)
    K.rng=np.random.default_rng(5602)   # older brown-olive moss for the lower flanks
    cl=fbm(30,1);clump=np.clip((cl-.38)*2.6,0,1);tu=np.clip((fbm(140,1)-.42)*2.4,0,1)
    t=np.clip(.25+.7*clump*(.7+.3*tu)+.25*(fbm(8,3)-.5),0,1)
    S['moss_old']=(lerp((.035,.033,.015),(.19,.18,.07),t),1.4*clump+.4*tu,3.2,.95,0,0)
    K.rng=np.random.default_rng(5605)   # wet dark forest soil with a few crumbs
    clod=np.clip((fbm(26,3)-.5)*2.4+.5,0,1);peb=np.clip((fbm(90,2)-.72)*5,0,1)
    S['soil']=(lerp((.07,.055,.04),(.18,.13,.09),np.clip(.5+.9*(fbm(4,3)-.5)+.35*(clod-.5),0,1))*(1+.3*peb[...,None]),.9*clod+.4*fbm(70,2)+.4*peb,1.6,.78,0,0)
    out={}
    for k,(alb,h,s,r,m,glow) in S.items():
        mat=bpy.data.materials.new('src_'+k);mat.use_nodes=True;nt=mat.node_tree;bs=nt.nodes['Principled BSDF']
        bs.inputs['Roughness'].default_value=r;bs.inputs['Metallic'].default_value=m
        uvn=nt.nodes.new('ShaderNodeUVMap');uvn.uv_map='Tiled'
        ta=nt.nodes.new('ShaderNodeTexImage');ta.image=K.img('alb_'+k,alb);nt.links.new(uvn.outputs['UV'],ta.inputs['Vector']);nt.links.new(ta.outputs['Color'],bs.inputs['Base Color'])
        tn=nt.nodes.new('ShaderNodeTexImage');tn.image=K.nmap('nrm_'+k,h,s);nt.links.new(uvn.outputs['UV'],tn.inputs['Vector'])
        nm=nt.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.8;nt.links.new(tn.outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
        out[k]=mat
    return out

# ---------------- items (filled per item after its three-view is picked) ----------------
PROPS={}
# id: (name, size limit w × d × h in m (h counts the pad under the ground too), minTier)
TABLE={
 'DP06_01':('MossCushionSmall',(.32,.32,.14),'standard'),
 'DP06_02':('MossMoundLobed',(.55,.48,.22),'standard'),
 'DP06_03':('MossPatchSpreading',(.85,.68,.14),'standard'),
 'DP06_04':('MossRootFootStrip',(.68,.30,.16),'standard'),
 'DP06_05':('MossBoulderCap',(.52,.52,.20),'standard'),
 'DP06_06':('MossTuftsScattered',(.58,.48,.12),'standard'),
}
IDS=tuple(TABLE);TARGET={k:('x',None) for k in IDS}
LIMIT={k:v[1] for k,v in TABLE.items()};NAME={k:v[0] for k,v in TABLE.items()};MIN_TIER={k:v[2] for k,v in TABLE.items()}
for _f in sorted(HERE.glob('moss_items*.py')):exec(open(_f,encoding='utf-8').read())

# ---------------- bake / split / LOD / export ----------------
def sel(*obs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:o.select_set(True)
    bpy.context.view_layer.objects.active=obs[0]
def run(pid):
    rid=pid.split('_')[0];sel_txt=(REF/rid/'prompt.txt').read_text(encoding='utf-8')
    assert '選用：' in sel_txt,f'{pid}: pick a saved three-view before modelling'
    bpy.ops.wm.read_factory_settings(use_empty=True);parts.clear();K.uvr.seed(77)
    sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.render.engine='CYCLES';dev=K.gpu(sc);sc.cycles.samples=16;sc.render.bake.margin=8;sc.render.bake.margin_type='EXTEND'
    M=make_sources();meta=PROPS[pid](M)
    pts=np.array([(o.matrix_world@v.co)[:] for o in parts if not o['grp'].startswith('Detail_') for v in o.data.vertices]);lo,hi=pts.min(0),pts.max(0)
    allp=np.array([(o.matrix_world@v.co)[:] for o in parts for v in o.data.vertices]);alo,ahi=allp.min(0),allp.max(0)   # the limit holds for everything, Detail_ included
    ax,tm=TARGET[pid];k='xyz'.index(ax);f=min([tm/(hi[k]-lo[k]) if tm else 1.]+[LIMIT[pid][i]/(ahi[i]-alo[i]) for i in range(3)])
    print('WL_EXT',pid,'body',[round(float(x),4) for x in hi-lo],'all',[round(float(x),4) for x in ahi-alo],'scale',round(float(f),4))   # edge jitter and bevels move the size by a few mm: scale to the work pack's length, never past its limit
    for o in parts:o.data.transform(o.matrix_world);o.matrix_world=Matrix.Identity(4);o.data.transform(Matrix.Scale(f,4))
    pts=np.array([v.co[:] for o in parts if not o['grp'].startswith('Detail_') for v in o.data.vertices]);lo,hi=pts.min(0),pts.max(0);meta['scale_to_target']=round(float(f),4)
    off=Vector((0,0,0))   # ground origin: the item is built round (0, 0) with z = 0 on the ground
    for o in parts:o.data.transform(o.matrix_world);o.matrix_world=Matrix.Identity(4);o.data.transform(Matrix.Translation(off))
    meta['offset']=np.array(off[:]);meta['height']=float(hi[2])
    if CLAY:   # grey model first (work pack §5: pick a three-view, then the grey model): bare geometry, no bake, for the clay review
        cd=ROOT/'art/previews'/PKG/pid/'clay';cd.mkdir(parents=True,exist_ok=True);sel(*parts)
        bpy.ops.export_scene.gltf(filepath=str(cd/f'{pid}-clay.glb'),use_selection=True,export_format='GLB',export_apply=True,export_materials='NONE')
        d=hi-lo;print('WL_CLAY',pid,[round(float(x),3) for x in d]);return {'id':pid,'clay':True}
    srcparts=list(parts);groups=sorted({o['grp'] for o in srcparts},key=lambda g:(g.startswith('Detail_'),g))
    cp=[]
    for o in srcparts:
        d=o.copy();d.data=o.data.copy();sc.collection.objects.link(d)
        a=d.data.attributes.new('gid','INT','FACE');a.data.foreach_set('value',[groups.index(o['grp'])]*len(d.data.polygons))
        c_=d.data.attributes.new('iscard','INT','FACE');c_.data.foreach_set('value',[1 if o.get('card') else 0]*len(d.data.polygons));cp.append(d)
    sel(*cp);bpy.ops.object.join();A=bpy.context.object;A.name=A.data.name=f'{pid}_All'
    if 'strip' in A.data.attributes:A.data.attributes.remove(A.data.attributes['strip'])   # tube() rope-strip flag, not needed here
    bm=bmesh.new();bm.from_mesh(A.data);bmesh.ops.triangulate(bm,faces=bm.faces)
    bmesh.ops.dissolve_degenerate(bm,dist=.0005,edges=list({e for f in bm.faces if f.calc_area()<2.5e-7 for e in f.edges}))
    bmesh.ops.triangulate(bm,faces=bm.faces[:]);meta['coplanar_lifted']=separate_coplanar(bm)
    bm.to_mesh(A.data);bm.free()
    for u in [u for u in A.data.uv_layers if u.name not in ('Tiled','CardUV')]:A.data.uv_layers.remove(u)
    bu=A.data.uv_layers.new(name='Bake');A.data.uv_layers.active=bu;sel(A);mg=16/RES
    fc_=np.zeros(len(A.data.polygons),np.int32);A.data.attributes['iscard'].data.foreach_get('value',fc_)
    A.data.polygons.foreach_set('hide',fc_.astype(bool));A.data.update()   # card faces take no room in the baked part of the atlas: they are unwrapped into the strip
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(meta.get('uv_angle',55)),island_margin=mg,area_weight=0,scale_to_bounds=False)
    bpy.ops.uv.select_all(action='SELECT');bpy.ops.uv.average_islands_scale();bpy.ops.uv.pack_islands(margin=mg,rotate=True)
    bpy.ops.mesh.reveal();bpy.ops.object.mode_set(mode='OBJECT')
    card=meta.get('card');V0=1-card['strip'] if card else 1.
    if card:   # LOD2 card (FI03 net bag): the baked parts are squeezed below v = V0, the strip above holds the painted net with alpha
        bu=A.data.uv_layers['Bake'];uv=np.empty(len(bu.data)*2,np.float32);bu.data.foreach_get('uv',uv);uv[1::2]*=V0-mg   # re-fetch: edit mode invalidated the old layer pointer
        if 'CardUV' in A.data.uv_layers and 'iscard' in A.data.attributes:   # card faces keep their own UVs, mapped into the strip
            cu=np.empty(len(bu.data)*2,np.float32);A.data.uv_layers['CardUV'].data.foreach_get('uv',cu)
            fc=np.zeros(len(A.data.polygons),np.int32);A.data.attributes['iscard'].data.foreach_get('value',fc)
            ls=np.zeros(len(A.data.polygons),np.int32);lt=np.zeros(len(A.data.polygons),np.int32);A.data.polygons.foreach_get('loop_start',ls);A.data.polygons.foreach_get('loop_total',lt)
            lm=np.repeat(fc,lt).astype(bool);uv[0::2][lm]=cu[0::2][lm];uv[1::2][lm]=V0+cu[1::2][lm]*(1-V0)
        bu.data.foreach_set('uv',uv)
    for o in sc.objects:o.hide_render=o is not A
    mats=list(A.data.materials);one=np.ones((RES,RES),np.float32);padmask=[None]
    def pad(a):
        f=padmask[0]
        if f is None or f.all():return a
        a=a.copy();f=f.copy();a[~f]=0
        for _ in range(24):
            acc=np.zeros_like(a);cnt=np.zeros(f.shape,np.float32)
            for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):acc+=np.roll(np.roll(a*f[...,None],dy,0),dx,1);cnt+=np.roll(np.roll(f,dy,0),dx,1)
            new=(~f)&(cnt>0);a[new]=acc[new]/cnt[new][:,None];f=f|new
            if f.all():break
        a[~f]=a[f].mean(0);return a
    def save(name,rgba,data=False):
        rgba=pad(np.asarray(rgba,dtype=np.float32));im=bpy.data.images.new(name,RES,RES,alpha=True)
        if data:im.colorspace_settings.name='Non-Color'
        im.pixels.foreach_set(np.ascontiguousarray(rgba,dtype=np.float32).ravel());im.filepath_raw=str(TEX/f'{name}.png');im.file_format='PNG';im.save();return im
    def target(name,data=False):
        im=bpy.data.images.new(name,RES,RES,alpha=False,float_buffer=data)
        for m in mats:
            nt=m.node_tree;t=nt.nodes.get('BAKE_TARGET') or nt.nodes.new('ShaderNodeTexImage');t.name='BAKE_TARGET';t.image=im;nt.nodes.active=t
        return im
    def bake(name,type,data=False,obj=None,**kw):
        im=target(name,data);sel(obj or A);bpy.ops.object.bake(type=type,**kw);a=np.array(im.pixels[:],dtype=np.float32).reshape(RES,RES,4);bpy.data.images.remove(im);return a
    def emit(fn):
        saved=[]
        for m in mats:
            nt=m.node_tree;out=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL');old=out.inputs['Surface'].links[0].from_socket
            em=nt.nodes.new('ShaderNodeEmission');fn(nt,m,em);nt.links.new(em.outputs[0],out.inputs['Surface']);saved.append((nt,out,old,em))
        return saved
    def restore(s):
        for nt,out,old,em in s:nt.links.new(old,out.inputs['Surface']);nt.nodes.remove(em)
    alb=bake('alb','DIFFUSE',pass_filter={'COLOR'});sc.cycles.samples=96;ao=bake('ao','AO',True)[...,0]
    det_ids=[i for i,g in enumerate(groups) if g.startswith('Detail_')]
    if det_ids:   # the body's AO is baked without the Detail_ pieces: the standard tier hides them, so no cord or peg shadow may stay on the body
        B=A.copy();B.data=A.data.copy();sc.collection.objects.link(B);bm=bmesh.new();bm.from_mesh(B.data);la=bm.faces.layers.int['gid']
        bmesh.ops.delete(bm,geom=[f for f in bm.faces if f[la] in det_ids],context='FACES');bm.to_mesh(B.data);bm.free()
        A.hide_render=True;B.hide_render=False;aob=bake('aob','AO',True,obj=B)[...,0]
        sc.cycles.samples=1;s=emit(lambda nt,m,em:em.inputs['Color'].__setattr__('default_value',(1,1,1,1)));cov=bake('cov','EMIT',True,obj=B)[...,0]>.5;restore(s)
        A.hide_render=False;bpy.data.objects.remove(B);ao=np.where(cov,aob,ao)
    sc.cycles.samples=16
    rough=bake('rough','ROUGHNESS',True)[...,0];nrm=bake('nrm','NORMAL',True,normal_space='TANGENT')
    onrm=bake('onrm','NORMAL',True,normal_space='OBJECT')[...,:3]*2-1
    s=emit(lambda nt,m,em:nt.links.new(nt.nodes.new('ShaderNodeNewGeometry').outputs['Pointiness'],em.inputs['Color']));pt=bake('edge','EMIT',True)[...,0];restore(s)
    edge=np.clip((pt-.52)/.07,0,1);cav=np.clip((.485-pt)/.05,0,1)
    s=emit(lambda nt,m,em:nt.links.new(nt.nodes.new('ShaderNodeNewGeometry').outputs['Position'],em.inputs['Color']));pos=bake('pos','EMIT',True)[...,:3];restore(s)
    s=emit(lambda nt,m,em:em.inputs['Color'].__setattr__('default_value',(*([float(m.get('mid',0))]*3),1)));mid=bake('mid','EMIT',True)[...,0];restore(s)
    filled=np.abs(pos).sum(2)>1e-7;padmask[0]=filled;px,py,pz=pos[...,0],pos[...,1],pos[...,2];H=max(meta['height'],.05)
    # finish: cool shade in occlusion, grime in the crevices, a little warmth on top, local pale wear on edges
    k_=meta.get('ao_k',.5)   # how much AO goes into the colour (the engine applies the AO map as well); WL04 lower: the 5 cm gap between its piles went near black
    cool=np.array([.30,.32,.42]);col=alb[...,:3]*(1-k_+k_*ao[...,None])+(1-ao[...,None])*cool*.07
    col=col*(1-.4*cav[...,None]*meta.get('grime',1))+cav[...,None]*np.array([.08,.07,.05])*.4*meta.get('grime',1)
    col=col*(1+.05*np.clip(pz/H,0,1)[...,None]*np.array([1.0,.9,.75]))
    n1=np.sin(px*23.3+np.sin(py*17.1+pz*13.3)*1.7)*np.sin(py*21.7+np.sin(pz*16.3+px*12.1)*1.9);n2=np.sin(px*71.1+np.sin(py*57.7)*1.3)*np.sin(pz*69.3+py*47.9)
    noise=np.clip(.5+.42*n1+.18*n2,0,1)
    wear=edge*np.clip((noise-.35)*2.5,0,1)*meta.get('wear',1);col=np.clip(col*(1+.12*wear[...,None])+wear[...,None]*.025,0,1)
    if meta.get('damp'):   # darker, cooler damp lower edge with a soft irregular tide line, smoother where wet
        dh=meta['damp']*(1+.35*(noise-.5));dm=np.clip((dh-pz)/(.35*meta['damp']),0,1)*filled
        col=col*(1-.30*dm[...,None])*(1-.05*dm[...,None]*np.array([1,0,-.6]));rough=np.clip(rough-.12*dm,0,1)
    if meta.get('paint'):col,rough=meta['paint'](col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta)
    alpha=one.copy()
    if card:   # paint the card strip: net colour and alpha (cord and knots opaque, holes clear), flat normal
        r0=int(V0*RES);h=RES-r0;crgb,ca=card['pattern'](RES,h)[:2];filled=filled.copy();filled[r0:]=True;padmask[0]=filled
        col=col.copy();col[r0:]=crgb;alpha[r0:]=ca;ao=ao.copy();ao[r0:]=.85;rough=rough.copy();rough[r0:]=.9
        nrm=nrm.copy();nrm[r0:]=(.5,.5,1,1)
    T={'alb':save(f'{pid}_Albedo',np.dstack([np.clip(col,0,1),alpha])),'nrm':save(f'{pid}_Normal',nrm,True),'orm':save(f'{pid}_ORM',np.dstack([ao,rough,0*one,one]),True)}
    save(f'{pid}_MaskURP',np.dstack([0*one,ao,0*one,1-rough]),True)
    fm=bpy.data.materials.new(f'M_{pid}_{NAME[pid]}');fm.use_nodes=True;nt=fm.node_tree;bs=nt.nodes['Principled BSDF'];fm.use_backface_culling=False
    def tn(im):t=nt.nodes.new('ShaderNodeTexImage');t.image=im;return t
    ta_=tn(T['alb']);nt.links.new(ta_.outputs['Color'],bs.inputs['Base Color'])
    if card and card.get('alpha',True):   # alpha clip (glTF: alphaMode MASK, cutoff 0.5, read from the Round node)
        rn=nt.nodes.new('ShaderNodeMath');rn.operation='ROUND';nt.links.new(ta_.outputs['Alpha'],rn.inputs[0]);nt.links.new(rn.outputs[0],bs.inputs['Alpha'])
    nmn=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tn(T['nrm']).outputs['Color'],nmn.inputs['Color']);nt.links.new(nmn.outputs['Normal'],bs.inputs['Normal'])
    sp=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tn(T['orm']).outputs['Color'],sp.inputs['Color']);nt.links.new(sp.outputs['Green'],bs.inputs['Roughness'])
    bs.inputs['Metallic'].default_value=0;bs.inputs['Specular IOR Level'].default_value=.35
    # split the atlas mesh back: body (every group not called Detail_*) and one object per Detail_ group, all on M_<ID>
    uvs=A.data.uv_layers
    for n_ in ('Tiled','CardUV'):
        if n_ in uvs:uvs.remove(uvs[n_])
    uvs['Bake'].name='UVMap';A.data.materials.clear();A.data.materials.append(fm)
    gid=np.zeros(len(A.data.polygons),np.int32);A.data.attributes['gid'].data.foreach_get('value',gid)
    pieces={'Body':[i for i,g in enumerate(groups) if not g.startswith('Detail_')]}
    for i,g in enumerate(groups):
        if g.startswith('Detail_'):pieces[g]=[i]
    root=bpy.data.objects.new(f'{pid}_GroundOrigin',None);sc.collection.objects.link(root);lods={}
    for name,ids in pieces.items():
        d=A.copy();d.data=A.data.copy();sc.collection.objects.link(d);d.name=d.data.name=f'{pid}_{name}_LOD0'
        bm=bmesh.new();bm.from_mesh(d.data);la=bm.faces.layers.int['gid']
        bmesh.ops.delete(bm,geom=[f for f in bm.faces if f[la] not in ids],context='FACES');bm.to_mesh(d.data);bm.free()
        d.parent=root;grp=[d]
        for L,ratio in ((1,.5),(2,.15)):
            e=d.copy();e.data=d.data.copy();sc.collection.objects.link(e);e.name=e.data.name=f'{pid}_{name}_LOD{L}'
            cd_=card if (card and L==2 and name=='Body' and card.get('verts')) else None
            if cd_:   # LOD2 body: the modelled net (FI03) or line coil (FI02) is dropped for a low stand-in painted in the atlas strip
                drop=[groups.index(g) for g in cd_['drop']];bm=bmesh.new();bm.from_mesh(e.data);la=bm.faces.layers.int['gid']
                bmesh.ops.delete(bm,geom=[f_ for f_ in bm.faces if f_[la] in drop],context='FACES');bm.to_mesh(e.data);bm.free();ratio=cd_.get('ratio',ratio)
            lr=meta.get('lod_ratios') if name=='Body' else None
            if lr:   # per-group ratios (FI02: decimated as one, the thin cut boards lost their thickness at LOD2 while the many line turns kept theirs)
                sub=[]
                for gi,gn in enumerate(groups):
                    if gn.startswith('Detail_'):continue
                    o_=e.copy();o_.data=e.data.copy();sc.collection.objects.link(o_);bm=bmesh.new();bm.from_mesh(o_.data);la=bm.faces.layers.int['gid']
                    bmesh.ops.delete(bm,geom=[f_ for f_ in bm.faces if f_[la]!=gi],context='FACES');bm.to_mesh(o_.data);bm.free()
                    if not o_.data.polygons:bpy.data.objects.remove(o_);continue
                    m=o_.modifiers.new('d','DECIMATE');m.ratio=lr.get(gn,(ratio,ratio))[L-1];m.use_collapse_triangulate=True;sel(o_);bpy.ops.object.modifier_apply(modifier='d');sub.append(o_)
                nm_=e.name;bpy.data.objects.remove(e);sel(*sub);bpy.ops.object.join();e=bpy.context.object;e.name=e.data.name=nm_;e.parent=root;e.hide_render=True;grp.append(e)
            else:
                m=e.modifiers.new('d','DECIMATE');m.ratio=ratio;m.use_collapse_triangulate=True;sel(e);bpy.ops.object.modifier_apply(modifier='d');e.hide_render=True;grp.append(e)
            if cd_:
                bm=bmesh.new();bm.from_mesh(e.data);ul=bm.loops.layers.uv['UVMap'];vs=[bm.verts.new(Vector(v)*f+off) for v in cd_['verts']]
                for fc,fu in zip(cd_['faces'],cd_['uvs']):
                    nf=bm.faces.new([vs[i] for i in fc]);nf.smooth=True
                    for l,(u_,v_) in zip(nf.loops,fu):l[ul].uv=(u_,V0+v_*(1-V0))
                bm.to_mesh(e.data);bm.free()
        for g in grp:
            if 'gid' in g.data.attributes:g.data.attributes.remove(g.data.attributes['gid'])
            if 'iscard' in g.data.attributes:g.data.attributes.remove(g.data.attributes['iscard'])
        lods[name]=grp
    col_obj=None;col_info=None
    if meta.get('collision_box'):   # work pack §3.5: a simple collider for the pieces a player would walk into: one box, <ID>_Collision, FBX and .blend only
        size,cen=meta['collision_box'];size=[s*f for s in size];cen=Vector(cen)*f+off
        col_obj=bpy.data.objects.new(f'{pid}_Collision',bpy.data.meshes.new(f'{pid}_Collision'));bmc=box_bm(size,cen);bmc.to_mesh(col_obj.data);bmc.free()
        sc.collection.objects.link(col_obj);col_obj.parent=root;col_obj.hide_render=True;col_obj.display_type='WIRE'
        col_info={'mesh':col_obj.name,'primitives':[{'type':'box','size_xyz_m':[round(float(s),3) for s in size],'center_xyz_m':[round(float(c),3) for c in cen]}],'note':meta.get('collision','')}
    src=bpy.data.collections.new(f'{pid}_SourceParts');sc.collection.children.link(src)
    for o in srcparts+[A]:
        for c in list(o.users_collection):c.objects.unlink(o)
        src.objects.link(o);o.hide_render=True;o.hide_set(True)
    bpy.context.view_layer.update()
    allp=np.array([(g[0].matrix_world@v.co)[:] for g in lods.values() for v in g[0].data.vertices]);dims=allp.max(0)-allp.min(0)
    bp=np.array([(v.co)[:] for v in lods['Body'][0].data.vertices]);bdims=bp.max(0)-bp.min(0)
    stem=f'{pid}_{VERSION}'
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE/f'{stem}.blend'),compress=True)
    sel(root,*[g[0] for g in lods.values()]);bpy.ops.export_scene.gltf(filepath=str(OUT/f'{stem}.glb'),use_selection=True,export_format='GLB',export_apply=True)
    sel(root,*[d for g in lods.values() for d in g],*([col_obj] if col_obj else []));bpy.ops.export_scene.fbx(filepath=str(OUT/f'{stem}.fbx'),use_selection=True,object_types={'MESH','EMPTY'},global_scale=1.0,apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_ALL',bake_space_transform=True,axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='FACE',
        use_tspace=True,add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE',embed_textures=False)
    tri=lambda o:sum(len(p.vertices)-2 for p in o.data.polygons)
    detail=[g for g in pieces if g.startswith('Detail_')]
    texinfo={f'{pid}_{k}.png':[RES,RES] for k in ('Albedo','Normal','ORM','MaskURP')}
    per_lod={}
    for L in range(3):
        per_lod[f'LOD{L}']={'triangles':sum(tri(g[L]) for g in lods.values()),'triangles_without_detail':tri(lods['Body'][L]),
                            'objects':len(lods),'objects_without_detail':1,'materials':1,'textures_px':texinfo}
    info={'id':pid,'name':NAME[pid],'version':VERSION,'files':{'fbx':f'art/exports/{PKG}/{stem}.fbx','glb':f'art/exports/{PKG}/{stem}.glb','blend':f'art/source/{PKG}/{stem}.blend'},
          'bake_device':dev,'dimensions_xyz_m':[round(float(x),3) for x in dims],'body_dimensions_xyz_m':[round(float(x),3) for x in bdims],
          'size_limit_xyz_m':list(LIMIT[pid]),'within_limit':bool(all(dims[i]<=LIMIT[pid][i]+1e-4 for i in range(3))),
          'minTier':MIN_TIER[pid],'detailObjects':detail,'detailMeshes':[f'{pid}_{g}_LOD{L}' for g in detail for L in range(3)],
          'lods':per_lod,'objects':{n:[d.name for d in g] for n,g in lods.items()},'material':fm.name,
          'textures':'one set: Albedo (sRGB) / Normal (OpenGL, +Y) / ORM (R AO, G roughness, B metal) / MaskURP (R metal, G AO, A smoothness)',
          'source_parts':len(srcparts),'coplanar_lifted':meta['coplanar_lifted'],
          'reference':f'art/references/{rid}/prompt.txt','origin':'footprint centre, z = 0 on the ground (the soil skirt runs on below it), front = -Y (Blender) / -Z (FBX, Unity)',
          'collision':col_info or meta.get('collision','none in the model; add a box from body_dimensions if the scene needs one')}
    if 'notes' in meta:info['notes']=meta['notes']
    print('WL_DONE',json.dumps(info,ensure_ascii=False));return info
ids=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else list(PROPS)
CLAY='--clay' in ids;ids=[i for i in ids if i!='--clay']
infos=[run(i) for i in ids]
if CLAY:sys.exit(0)
mf=OUT/'model_info.json';old=json.loads(mf.read_text(encoding='utf-8')) if mf.exists() else {}
old.update({i['id']:i for i in infos});mf.write_text(json.dumps(dict(sorted(old.items())),ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
