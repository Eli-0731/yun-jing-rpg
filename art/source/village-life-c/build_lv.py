"""承天 · C 村裡生活小物 LV01–LV06（village-life-c）— Eli-0731, Blender 4.5.3 LTS.
Work pack: docs/execution/2026-11-07/C-128h-creekside-and-village-life.md, part 2 (LV01–LV12, this file LV01–LV06 first).
LV01 竹編雞籠、LV02 竹掃帚與木畚箕、LV03 靠牆的竹梯、LV04 竹編吊籃、LV05 醃菜甕三個、LV06 劈柴木墩與柴刀.
Each item is modelled only after its three-view candidates are saved and one is picked in art/references/<ID>/prompt.txt.
Same pipeline as creekside-life-c (its kit and part helpers are loaded from there, not copied): named parts with tiled
source materials → one UV atlas (1024², one material) → Cycles bake → numpy finish → body + Detail_* → LOD1/LOD2 → .blend, FBX, GLB.
Origin: footprint centre, bottom at z = 0, Blender -Y is the front. No ground plate.
blender -b --factory-startup -P build_lv.py -- LV01 [LV02 ...] [--clay]
"""
import bpy,bmesh,json,math,sys,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'creekside-life-c'))
import wl_kit as K
from wl_kit import fbm,lerp,board,finish,tube,rope,box_bm,box,bevel,subdiv,jitter,join,apply,separate_coplanar,parts,link
from mathutils import Vector,Matrix
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];PKG='village-life-c';CK=ROOT/'art/source/creekside-life-c'   # CK: the shared kit and part helpers
REF=ROOT/'art/references';TEX=ROOT/'art/textures'/PKG;OUT=ROOT/'art/exports'/PKG
sys.path.insert(0,str(ROOT/'art/source/modelling-basics-c'));import meshfix
for p in (TEX,OUT):p.mkdir(parents=True,exist_ok=True)
X=np.arange(K.R)[None,:]/K.R;Y=np.arange(K.R)[:,None]/K.R
RES=1024;VERSION='v001'

# ---------------- tiled source textures ----------------
def linen(base,dark,seed,slub=.5,warp_pitch=90):   # 90 thread pairs per 0.5 m tile: finer aliased into moiré in the 1024 bake
    """coarse plain-weave linen: a faint over-under weave in the normal map, slubs (thicker threads) as soft streaks,
    large soft colour patches; colour kept calm, the weave lives mostly in the height"""
    K.rng=np.random.default_rng(seed)
    wx=.5+.5*np.sin(math.tau*X*warp_pitch);wy=.5+.5*np.sin(math.tau*Y*warp_pitch)
    chk=np.sign(np.sin(math.pi*X*warp_pitch))*np.sign(np.sin(math.pi*Y*warp_pitch))
    weave=np.where(chk>0,wx,wy)
    sl=np.clip((fbm(40,2,aniso=20)-.62)*4,0,1)*slub;sl2=np.clip((fbm(40,2,aniso=20).T-.66)*4,0,1)*slub*.6   # warp slubs along V, weft slubs along U
    broad=fbm(3,3)
    t=np.clip(.5+.9*(broad-.5),0,1)
    col=lerp(dark,base,t)*(1-.025*weave[...,None])*(1+.08*sl[...,None])
    return col,.6*weave+.5*sl+.3*sl2+.2*broad
def make_sources():
    S={}
    K.rng=np.random.default_rng(3101)
    # old cedar (style spec §2 old wood #5A3A22 / #7A5234 / #3B2617, sun-greyed #6E6458): sources a step lighter, the AO finish brings them down
    S['cedar']=(*board((.33,.21,.12),(.55,.37,.22),(.47,.42,.36),.30,.8),1.6,.80,0,0)
    S['cedar_b']=(*board((.28,.18,.10),(.47,.31,.18),(.42,.38,.33),.25,.8,.4),1.6,.80,0,0)
    S['cedar_new']=(*board((.43,.30,.18),(.60,.45,.29),(.55,.50,.43),.15,.3,.6),1.4,.75,0,0)   # the repaired slat: a little fresher and paler, not new-white
    S['cedar_rib']=(*board((.38,.25,.15),(.56,.39,.25),(.50,.45,.38),.20,.15,.3),1.2,.72,0,0)   # rib stock: softer grain, few checks (narrow ribs turned stripy with the board stock)
    S['endgrain']=(*endgrain(),1.8,.85,0,0)
    S['linen']=(*linen((.78,.72,.60),(.62,.56,.45),3102),.55,.92,0,0)          # undyed natural linen (weave kept faint in the normal: at 1.2 it read as sacking)
    S['linen_b']=(*linen((.74,.70,.62),(.58,.55,.48),3103),.55,.92,0,0)        # faded, greyer
    S['linen_blue']=(*linen((.42,.50,.58),(.30,.37,.45),3104),.55,.92,0,0)     # muted indigo, washed out
    S['iron']=(lerp((.16,.13,.11),(.36,.22,.13),np.clip((fbm(6,4)-.35)*1.8,0,1)),fbm(18,3),2.0,.8,0,0)   # old rusty iron staples
    K.rng=np.random.default_rng(3105)
    tw=.5+.5*np.sin(math.tau*((X+Y)*16));fib=fbm(30,2,aniso=6)
    S['hemp']=(lerp((.36,.29,.19),(.62,.51,.34),np.clip(tw*.55+.3*fbm(4,3)+.15*fib,0,1)),tw+.4*fib,1.4,.92,0,0)
    gk=np.clip((fbm(220,1)-.58)*5,0,1);gp=np.clip((fbm(190,1)-.64)*6,0,1);wz=np.clip((fbm(3,4)-.45)*2.2,0,1)
    S['stone']=(lerp((.39,.38,.35),(.62,.60,.55),np.clip(.5+.9*(fbm(4,4)-.5)+.25*(fbm(30,2)-.5),0,1))*(1-.06*gk[...,None])+gp[...,None]*np.array([.02,.018,.015])   # warm grey (#8a8478 → #b8b0a0 guide rock), grains kept faint: stronger read as spots on a small dish
                +wz[...,None]*np.array([.04,.02,0]),.4*fbm(120,2)+.3*fbm(24,3)+.3*gk-.2*gp,.9,.84,0,0)   # warm-grey fieldstone, as BM05/BM06
    pores=np.clip((fbm(160,1)-.6)*5,0,1)
    S['ash']=(lerp((.47,.46,.44),(.66,.65,.62),np.clip(.5+.8*(fbm(5,3)-.5),0,1))*(1-.12*pores[...,None]),.5*fbm(60,2)-.3*pores,.8,.95,0,0)   # pressed lye-ash cake, matte grey
    # FI sources (added after the WL ones, each with its own seed, so WL01–WL05 keep their exact textures)
    K.rng=np.random.default_rng(3201)
    st=np.clip((fbm(30,2,aniso=30)-.5)*2+.5,0,1);bl=fbm(4,3,aniso=8)   # fibres along the cane (V), broad soft colour along it
    spots=np.clip((fbm(18,2)-.72)*5,0,1)
    S['bamboo']=(lerp((.48,.40,.24),(.74,.64,.40),np.clip(.5+.8*(bl-.5)+.12*(st-.5),0,1))*(1-.25*spots[...,None]),.5*st+.3*bl,1.0,.55,0,0)   # old cane: straw-gold, darker water spots, glossy skin
    S['bamboo_split']=(lerp((.56,.46,.29),(.78,.68,.47),np.clip(.5+.6*(bl-.5)+.35*(st-.5),0,1)),1.2*st,1.4,.75,0,0)   # split cane: inner fibres show, matte
    K.rng=np.random.default_rng(3202)
    S['floatwood']=(*board((.42,.33,.22),(.62,.51,.36),(.55,.51,.45),.30,.35,.5),1.2,.82,0,0)   # light timber (paulownia-like), a little paler than cedar; at first it read as wax
    K.rng=np.random.default_rng(3203)
    tw2=.5+.5*np.sin(math.tau*((X+Y)*28))
    S['net']=(lerp((.40,.33,.22),(.58,.48,.32),np.clip(tw2*.5+.4*fbm(4,3),0,1)),tw2,1.0,.92,0,0)   # thin hemp net cord, a little darker than the rope
    S['cord_dark']=(lerp((.18,.15,.12),(.32,.26,.19),np.clip(tw2*.5+.4*fbm(5,3),0,1)),tw2,1.0,.9,0,0)   # dark tarred cord (binding)
    K.rng=np.random.default_rng(3204)   # #93 review round: bank mud where FI03's handle is pushed in (own seed: the other sources keep their textures)
    S['mud']=(lerp((.20,.16,.11),(.36,.30,.22),np.clip(.5+.9*(fbm(5,3)-.5)+.2*(fbm(40,2)-.5),0,1)),.6*fbm(30,3)+.3*fbm(90,2),1.2,.70,0,0)
    # LV sources (after all creekside ones, own seeds: the shared ones keep their textures)
    K.rng=np.random.default_rng(3301)
    stw=np.clip((fbm(40,2,aniso=30)-.5)*2+.5,0,1)
    S['straw']=(lerp((.55,.43,.20),(.82,.68,.38),np.clip(.5+.7*(fbm(4,3,aniso=6)-.5)+.25*(stw-.5),0,1)),.8*stw,1.0,.85,0,0)   # dry rice straw, golden
    S['feather']=(lerp((.72,.70,.66),(.92,.90,.86),np.clip(fbm(3,3),0,1)),.3*fbm(60,2),.5,.8,0,0)   # a stray hen feather, off-white
    S['bamboo_old']=(lerp((.44,.36,.21),(.66,.56,.34),np.clip(.5+.7*(fbm(4,3,aniso=8)-.5)+.2*(stw-.5),0,1))*(1-.10*np.clip((fbm(6,3)-.55)*4,0,1)[...,None]),.6*stw+.2*fbm(20,2),1.2,.72,0,0)   # weathered split bamboo strip, matte
    K.rng=np.random.default_rng(3302)
    tw3=np.clip((fbm(50,2,aniso=40)-.5)*2+.5,0,1)
    S['twig']=(lerp((.26,.17,.10),(.48,.34,.20),np.clip(.5+.6*(fbm(5,3,aniso=10)-.5)+.3*(tw3-.5),0,1)),.9*tw3,1.3,.88,0,0)   # dried brown broom twigs (own seed, after the others)
    K.rng=np.random.default_rng(3303)   # LV04: a woven basket skin (the weave lives in the texture), dried leaves, dried chillies
    su=np.floor(X*24);sv=np.floor(Y*24);ov=((su+sv)%2)[...,None]*np.ones((1,1,1))
    fu=np.abs(((X*24)%1)-.5)*2;fv=np.abs(((Y*24)%1)-.5)*2   # 0 in the middle of a strip, 1 at its edge
    hgt=np.where(((su+sv)%2)>0,1-fu**3,1-fv**3)*.8+np.where(((su+sv)%2)>0,.3,0)
    tint=np.where(((su+sv)%2)>0,np.sin(su*12.9898+3)*.5+.5,np.sin(sv*78.233+1)*.5+.5)
    gap=np.clip((np.where(((su+sv)%2)>0,fu,fv)-.82)*6,0,1)
    S['weave']=(lerp((.40,.32,.19),(.66,.55,.34),np.clip(.45+.35*(tint-.5)+.3*(fbm(5,3)-.5),0,1))*(1-.45*gap[...,None]),hgt+.2*fbm(40,2),1.6,.8,0,0)
    S['leaf_dry']=(lerp((.46,.44,.20),(.72,.68,.40),np.clip(.5+.8*(fbm(6,3)-.5),0,1))*(1-.25*np.clip((fbm(30,2)-.6)*4,0,1)[...,None]),.4*fbm(25,3),.9,.8,0,0)
    S['chilli']=(lerp((.42,.06,.04),(.66,.15,.08),np.clip(.5+.8*(fbm(5,3)-.5),0,1)),.3*fbm(20,2),.6,.55,0,0)
    K.rng=np.random.default_rng(3304)   # LV05: dark brown glaze (soft sheen) and unglazed clay
    S['glaze']=(lerp((.20,.10,.08),(.40,.22,.15),np.clip(.5+.8*(fbm(4,3)-.5)+.15*(fbm(20,2)-.5),0,1))*(1+.10*(fbm(3,2)-.5))[...,None]*np.array([1,.95,1.05]),.15*fbm(30,2),.4,.42,0,0)
    S['clay']=(lerp((.52,.38,.26),(.72,.56,.40),np.clip(.5+.8*(fbm(5,3)-.5),0,1))*(1-.12*np.clip((fbm(40,2)-.6)*4,0,1)[...,None]),.4*fbm(60,2)+.3*fbm(12,3),1.0,.9,0,0)
    K.rng=np.random.default_rng(3305)   # LV06: bark and pale weathered stump wood
    vf=np.clip((fbm(60,2,aniso=50)-.5)*2+.5,0,1);vc=np.clip((fbm(25,2,aniso=40)-.62)*5,0,1)
    S['bark']=(lerp((.22,.16,.11),(.42,.32,.24),np.clip(.5+.6*(fbm(5,3)-.5)+.35*(vf-.5),0,1))*(1-.35*vc[...,None]),1.2*vf-.8*vc,2.0,.92,0,0)
    S['stumpwood']=(lerp((.50,.42,.34),(.74,.66,.56),np.clip(.5+.7*(fbm(4,3,aniso=6)-.5)+.2*(vf-.5),0,1))*(1-.40*vc[...,None]),.6*vf-1.0*vc,1.6,.85,0,0)
    K.rng=np.random.default_rng(3306)   # LV07: dried gourd shell, tan with darker freckles
    gs=np.clip((fbm(10,3)-.6)*3,0,1)*.6+np.clip((fbm(40,2)-.7)*3,0,1)*.4   # soft blotches, a few small freckles
    S['gourd']=(lerp((.55,.38,.19),(.78,.60,.33),np.clip(.5+.7*(fbm(3,3)-.5),0,1))*(1-.16*gs[...,None]),.15*fbm(20,2)-.1*gs,.5,.62,0,0)
    S['cloth_dark']=(*linen((.24,.26,.32),(.15,.16,.21),3308),.6,.92,0,0)   # LV10: dark indigo cloth of the sandal and clog thongs
    K.rng=np.random.default_rng(3309)   # LV11: fine grey whetstone, and the water in its bowl
    S['whet']=(lerp((.29,.30,.31),(.47,.47,.46),np.clip(.5+.7*(fbm(4,3)-.5)+.12*(fbm(50,2)-.5),0,1))*(1-.10*np.clip((fbm(12,2,aniso=5)-.62)*4,0,1))[...,None],.25*fbm(40,2),.6,.7,0,0)
    S['water']=(lerp((.17,.30,.30),(.30,.46,.43),np.clip(.5+.6*(fbm(3,2)-.5),0,1)),.05*fbm(8,2),.2,.08,0,0)
    K.rng=np.random.default_rng(3310)   # LV12: clean cream eggshell, very faint speckle
    S['egg']=(lerp((.80,.68,.50),(.90,.80,.64),np.clip(.5+.5*(fbm(3,2)-.5),0,1))*(1-.05*np.clip((fbm(60,2)-.65)*4,0,1))[...,None],.05*fbm(30,2),.2,.5,0,0)
    K.rng=np.random.default_rng(3307)   # LV08: the rain cape's old straw and palm fibre, golden going grey-green, strong strands along V
    cf=np.clip((fbm(70,2,aniso=60)-.5)*2.2+.5,0,1);cg=np.clip(.5+.9*(fbm(4,3,aniso=4)-.5),0,1)
    S['cape']=(lerp((.40,.38,.22),(.76,.62,.34),np.clip(.30+.50*cg+.55*(cf-.5),0,1))*(1-.22*np.clip((fbm(8,3,aniso=8)-.55)*3,0,1))[...,None]*(1-.25*np.clip((.35-cf)*3,0,1))[...,None],1.8*cf,2.2,.9,0,0)   # dark gaps between the strands
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
def endgrain():
    """cedar end grain: growth rings round an off-centre pith, a few radial checks (WL02 practice point)"""
    K.rng=np.random.default_rng(3106)
    cx,cy=.43,.52;dx=X-cx;dy=Y-cy;r=np.sqrt(dx*dx+dy*dy);a=np.arctan2(dy,dx)
    wob=.012*fbm(4,3);rings=.5+.5*np.sin(math.tau*(r+wob)*38)
    late=np.clip((rings-.82)*6,0,1)
    checks=np.zeros_like(r)
    for ang,w,L in ((.6,.010,.32),(2.3,.008,.26),(4.1,.012,.38),(5.3,.006,.2)):
        d=np.abs(((a-ang+math.pi)%math.tau)-math.pi)*r;checks=np.maximum(checks,np.clip(1-d/w,0,1)*np.clip(1-r/L,0,1)*np.clip(r/.03,0,1))
    t=np.clip(.55+.5*(fbm(3,3)-.5)-.2*np.clip(r*1.6,0,1),0,1)
    col=lerp((.40,.27,.16),(.66,.50,.33),t)*(1-.22*late[...,None])*(1-.75*checks[...,None])
    return col,.18*late-1.2*checks+.2*fbm(60,2)   # rings mostly in colour, the checks cut in

# ---------------- items (filled per item after its three-view is picked) ----------------
PROPS={}
TARGET={k:('x',None) for k in ('LV01','LV02','LV03','LV04','LV05','LV06','LV07','LV08','LV09','LV10','LV11','LV12')}   # None: built at true size, only held to the limit
LIMIT={'LV01':(.8,.8,.6),'LV02':(1.4,.4,.3),'LV03':(.5,.1,2.4),'LV04':(.5,.5,.8),'LV05':(.9,.5,.6),'LV06':(.6,.6,.6),
       'LV07':(.4,.2,.5),'LV08':(.8,.4,1.6),'LV09':(.4,.4,1.2),'LV10':(.4,.3,.1),'LV11':(.8,.3,.5),'LV12':(.35,.35,.25)}   # work pack part 2 table A, w × d × h
NAME={'LV01':'ChickenCoop','LV02':'BroomDustpan','LV03':'BambooLadder','LV04':'HangingBasket','LV05':'PickleJars','LV06':'ChoppingBlock',
      'LV07':'GourdLadle','LV08':'RainHatCapeRack','LV09':'BirdcagePole','LV10':'StrawSandalsClogs','LV11':'WhetstoneBench','LV12':'StrawEggBasket'}
MIN_TIER={k:'high' for k in TARGET}   # quality-tiers §4: roadside props that add richness; nothing to play with or stop the player
for _f in [CK/'wl_items.py']+sorted(CK.glob('fi_items*.py')):exec(open(_f,encoding='utf-8').read())   # part helpers (_sheet, _cane, _lathe, _ring, _plate …)
PROPS.clear()   # only the LV items below
for _f in sorted(HERE.glob('lv_items*.py')):exec(open(_f,encoding='utf-8').read())

# ---------------- bake / split / LOD / export ----------------
def sel(*obs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:o.select_set(True)
    bpy.context.view_layer.objects.active=obs[0]
def run(pid):
    sel_txt=(REF/pid/'prompt.txt').read_text(encoding='utf-8')
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
    off=Vector((-(lo[0]+hi[0])/2,-(lo[1]+hi[1])/2,-lo[2]))
    for o in parts:o.data.transform(o.matrix_world);o.matrix_world=Matrix.Identity(4);o.data.transform(Matrix.Translation(off))
    meta['offset']=np.array(off[:]);meta['height']=float(hi[2]-lo[2])
    if CLAY:   # grey model first (work pack §5: pick a three-view, then the grey model): bare geometry, no bake, for the clay review
        cd=ROOT/'art/previews'/PKG/pid/'clay';cd.mkdir(parents=True,exist_ok=True);sel(*parts)
        bpy.ops.export_scene.gltf(filepath=str(cd/f'{pid}-clay.glb'),use_selection=True,export_format='GLB',export_apply=True,export_materials='NONE')
        d=hi-lo;print('WL_CLAY',pid,[round(float(x),3) for x in d]);return {'id':pid,'clay':True}
    srcparts=list(parts);groups=sorted({o['grp'] for o in srcparts},key=lambda g:(g.startswith('Detail_'),g))
    cp=[]
    for o in srcparts:
        d=o.copy();d.data=o.data.copy();sc.collection.objects.link(d)
        a=d.data.attributes.new('gid','INT','FACE');a.data.foreach_set('value',[groups.index(o['grp'])]*len(d.data.polygons));cp.append(d)
    sel(*cp);bpy.ops.object.join();A=bpy.context.object;A.name=A.data.name=f'{pid}_All'
    if 'strip' in A.data.attributes:A.data.attributes.remove(A.data.attributes['strip'])   # tube() rope-strip flag, not needed here
    bm=bmesh.new();bm.from_mesh(A.data);bmesh.ops.triangulate(bm,faces=bm.faces)
    bmesh.ops.dissolve_degenerate(bm,dist=.0005,edges=list({e for f in bm.faces if f.calc_area()<2.5e-7 for e in f.edges}))
    bmesh.ops.triangulate(bm,faces=bm.faces[:]);meta['coplanar_lifted']=separate_coplanar(bm)
    bm.to_mesh(A.data);bm.free()
    for u in [u for u in A.data.uv_layers if u.name!='Tiled']:A.data.uv_layers.remove(u)
    bu=A.data.uv_layers.new(name='Bake');A.data.uv_layers.active=bu;sel(A);mg=16/RES
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(meta.get('uv_angle',55)),island_margin=mg,area_weight=0,scale_to_bounds=False)
    bpy.ops.uv.select_all(action='SELECT');bpy.ops.uv.average_islands_scale();bpy.ops.uv.pack_islands(margin=mg,rotate=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    card=meta.get('card');V0=1-card['strip'] if card else 1.
    if card:   # LOD2 card (FI03 net bag): the baked parts are squeezed below v = V0, the strip above holds the painted net with alpha
        bu=A.data.uv_layers['Bake'];uv=np.empty(len(bu.data)*2,np.float32);bu.data.foreach_get('uv',uv);uv[1::2]*=V0-mg;bu.data.foreach_set('uv',uv)   # re-fetch: edit mode invalidated the old layer pointer
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
        r0=int(V0*RES);h=RES-r0;crgb,ca=card['pattern'](RES,h);filled=filled.copy();filled[r0:]=True;padmask[0]=filled
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
    if 'Tiled' in uvs:uvs.remove(uvs['Tiled'])
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
            cd_=card if (card and L==2 and name=='Body') else None
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
        lods[name]=grp
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
    sel(root,*[d for g in lods.values() for d in g]);bpy.ops.export_scene.fbx(filepath=str(OUT/f'{stem}.fbx'),use_selection=True,object_types={'MESH','EMPTY'},global_scale=1.0,apply_unit_scale=True,
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
          'reference':f'art/references/{pid}/prompt.txt','origin':'footprint centre, bottom z = 0, front = -Y (Blender) / -Z (FBX, Unity)',
          'collision':meta.get('collision','none: a small prop on the ground the player walks round; add a box from body_dimensions if the scene needs one')}
    if 'notes' in meta:info['notes']=meta['notes']
    print('WL_DONE',json.dumps(info,ensure_ascii=False));return info
ids=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else list(PROPS)
CLAY='--clay' in ids;ids=[i for i in ids if i!='--clay']
infos=[run(i) for i in ids]
if CLAY:sys.exit(0)
mf=OUT/'model_info.json';old=json.loads(mf.read_text(encoding='utf-8')) if mf.exists() else {}
old.update({i['id']:i for i in infos});mf.write_text(json.dumps(dict(sorted(old.items())),ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
