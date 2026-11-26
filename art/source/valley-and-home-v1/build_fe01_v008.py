"""FE01 三段重做：沿用 Josh 零件與材質函式，保留既有接口和橋面高度。"""
from pathlib import Path
import sys, math, json, random
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'art/source/village-houses-b'))
import ti_core as core
import ti_pipeline as pipe
import cr_parts as parts
import cr_mats as mats
import vl_mats
import numpy as np

VERSION='v008'
ASSET='FE01'
VARIANTS=('Straight','Corner','End')

def eli_bake_layers(S,out,size=1024):
    """照 Eli build_wl 的清單補 AO、物件法線、邊緣 Pointiness、位置與 URP 組圖。"""
    sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU'
    sc.render.bake.margin=8;sc.render.bake.use_clear=True
    objs=list(S['lod0'].values())
    for o in S['parts']:o.hide_render=True
    mats_used={m for o in objs for m in o.data.materials}
    tex=out/'Textures';tex.mkdir(parents=True,exist_ok=True)
    def bake(label,typ,objects,samples=16,source=None,normal_space=None):
        sc.cycles.samples=samples
        im=bpy.data.images.new(label,width=size,height=size,alpha=True,float_buffer=True)
        im.colorspace_settings.name='Non-Color'
        state=[]
        for m in mats_used:
            nt=m.node_tree
            target=nt.nodes.new('ShaderNodeTexImage');target.name='ELI_BAKE_TARGET';target.image=im;nt.nodes.active=target
            output=nt.nodes.get('OUTPUT')
            old=[(link.from_socket,link.to_socket) for link in output.inputs['Surface'].links]
            nodes=[]
            if source:
                geo=nt.nodes.new('ShaderNodeNewGeometry');nodes.append(geo)
                em=nt.nodes.new('ShaderNodeEmission');nodes.append(em)
                if source=='Pointiness': value=geo.outputs['Pointiness']
                else:
                    mul=nt.nodes.new('ShaderNodeVectorMath');mul.operation='SCALE';mul.inputs[3].default_value=.25
                    nt.links.new(geo.outputs['Position'],mul.inputs[0]);nodes.append(mul)
                    add=nt.nodes.new('ShaderNodeVectorMath');add.operation='ADD';add.inputs[1].default_value=(.5,.5,.5)
                    nt.links.new(mul.outputs[0],add.inputs[0]);nodes.append(add)
                    value=add.outputs[0]
                nt.links.new(value,em.inputs['Color']);nt.links.new(em.outputs[0],output.inputs['Surface'])
            state.append((nt,target,old,nodes,output))
        bpy.ops.object.select_all(action='DESELECT')
        for o in objects:o.hide_render=False;o.select_set(True)
        bpy.context.view_layer.objects.active=objects[0]
        kw={'type':typ}
        if normal_space:kw['normal_space']=normal_space
        bpy.ops.object.bake(**kw)
        for nt,target,old,nodes,output in state:
            nt.nodes.remove(target)
            for n in nodes:nt.nodes.remove(n)
            for frm,to in old:nt.links.new(frm,to)
        for o in objects:o.hide_render=True
        path=tex/f'{S["asset"]}_{label}.png'
        im.filepath_raw=str(path);im.file_format='PNG';im.save()
        arr=np.empty(size*size*4,np.float32);im.pixels.foreach_get(arr)
        bpy.data.images.remove(im)
        print('ELI_BAKED',label,flush=True)
        return arr.reshape(size,size,4)
    main=[o for o in objs if 'Detail' not in o.name]
    detail=[o for o in objs if 'Detail' in o.name]
    ao=bake('AO_Main','AO',main,96)
    if detail:
        aod=bake('AO_Detail','AO',detail,96)
        ao=np.where(aod[...,3:4]>.01,aod,ao)
    bake('ObjectNormal','NORMAL',objs,16,normal_space='OBJECT')
    edge=bake('Pointiness','EMIT',objs,8,source='Pointiness')
    pos=bake('Position','EMIT',objs,8,source='Position')
    def pixels(path):
        im=bpy.data.images.load(str(path),check_existing=False)
        a=np.empty(size*size*4,np.float32);im.pixels.foreach_get(a);bpy.data.images.remove(im)
        return a.reshape(size,size,4)
    base=pixels(S['tex']['BaseColor']);rough=pixels(S['tex']['Roughness']);metal=pixels(S['tex']['Metallic'])
    # 冷 AO、縫污與磨亮邊；位置圖保留供日後依高度調濕痕。
    shade=np.clip(.70+.30*ao[...,0:1],.66,1)
    worn=np.clip((edge[...,0:1]-.52)*.09,0,.035)
    base[...,:3]=np.clip(base[...,:3]*shade*np.array([.97,.985,1.0])+worn,0,1)
    def write(label,arr,color=False):
        im=bpy.data.images.new(label,width=size,height=size,alpha=True,float_buffer=True)
        im.colorspace_settings.name='sRGB' if color else 'Non-Color'
        im.pixels.foreach_set(np.clip(arr,0,1).ravel())
        path=tex/f'{S["asset"]}_{label}.png';im.filepath_raw=str(path);im.file_format='PNG';im.save()
        bpy.data.images.remove(im)
        return path
    # 匯出材質讀同一個 BaseColor 路徑，所以先以 Eli 的合成結果覆蓋。
    write('BaseColor',base,True)
    for im in bpy.data.images:
        if im.filepath and Path(bpy.path.abspath(im.filepath)).resolve()==(tex/f'{S["asset"]}_BaseColor.png').resolve():
            im.reload()
    orm=np.zeros_like(base);orm[...,0]=ao[...,0];orm[...,1]=rough[...,0];orm[...,2]=metal[...,0];orm[...,3]=1
    write('ORM',orm)
    mask=np.zeros_like(base);mask[...,0]=metal[...,0];mask[...,1]=ao[...,0];mask[...,2]=1;mask[...,3]=1-rough[...,0]
    write('MaskURP',mask)
    S['tex']['BaseColor']=tex/f'{S["asset"]}_BaseColor.png'
    return {'AO':True,'ObjectNormal':True,'Pointiness':True,'Position':True,'ORM':True,'MaskURP':True}

def geom(variant):
    core.reset_state('SM_FE01_'+variant)
    S=core.S
    old=mats.wood('FE01_OldWetWood',dark=vl_mats.WOOD[2],light=vl_mats.WOOD[1],
                  wet_z=.20,moss=True,grey=.42,holes=.5,polish=.10)
    deck=mats.wood('FE01_DeckGrain',dark=vl_mats.WOOD[0],light=vl_mats.WOOD[1],
                   wet_z=.31,moss=True,grey=.58,holes=.7,polish=.20)
    bark=mats.wood('FE01_BarkRemnants',dark=(.043,.026,.014),light=(.16,.095,.04),
                   wet_z=.12,moss=True,grey=.26,holes=.8)
    iron=vl_mats.iron('FE01_IronNails')
    rope_mat=mats.canvas('FE01_Rope',base=(.20,.16,.095),stain=(.075,.05,.025),faded=.6,dirt=.8)
    rng=random.Random(variant)
    for i in range(13):
        y=-1.5+(i+.5)*3/13
        width=1.49+rng.uniform(-.035,.045)
        thick=.047+rng.uniform(-.008,.010)
        span=.213+rng.uniform(-.015,.012)
        crown=rng.uniform(-.012,.018)
        def warp(q, crown=crown, width=width):
            q.z+=crown*(1-(q.x/(width*.5))**2)
        parts.rbox(f'Deck_Plank_{i:02}',(rng.uniform(-.008,.008),y,.422),(width,span,thick),old if i in (4,10) else deck,
                   r=.006,amp=.004,freq=9,chips=3,hew=2,seed=i,div=.12,
                   rot=(rng.uniform(-.012,.012),rng.uniform(-.01,.01),rng.uniform(-.006,.006)),
                   warp=warp,flat='z',group='Main',detail=0,grain='x')
        # 短而不規則的暗裂及鏽釘，跟木板分開，低畫質先隱藏。
        if i not in (0,12):
            for j in range(1):
                xx=rng.uniform(-.43,.42)
                parts.rbox(f'Crack_{i}_{j}',(xx,y+rng.uniform(-.025,.025),.477),
                           (rng.uniform(.16,.37),.008,.002),bark,r=.001,div=.13,
                           rot=(0,0,rng.uniform(-.17,.17)),group='Main',detail=1)
        for x in (-.62,.62):
            parts.rbox(f'Detail_Nail_{i}_{x}',(x,y,.454),(.014,.014,.005),iron,
                       r=.002,div=.05,group='Detail_Small',detail=2)
    for x in (-.69,.69):
        parts.rbox(f'Long_Sill_{x}',(x,0,.292),(.14,2.99,.17),old,
                   r=.018,amp=.007,chips=3,hew=2,seed=8,div=.20,group='Main',detail=0)
    for y in (-1.39,1.39):
        parts.rbox(f'Cross_Sill_{y}',(0,y,.294),(1.54,.15,.16),old,
                   r=.015,amp=.006,chips=3,hew=2,seed=11,div=.18,group='Main',detail=0)
    for x in (-.68,.68):
        for y in (-1.42,1.42):
            pile=parts.log(f'Pile_{x}_{y}',[(x,y,-1),(x+rng.uniform(-.025,.025),y,.32),(x,y,1.16)],
                           .105,old,seg=14,lump=.10,seed=int((x+2)*10+(y+2)*4),group='Main',detail=0)
            # 樹皮殘留改做樁面局部材料，避免薄片與樁身近共面。
            pile.data.materials.append(bark)
            for face in pile.data.polygons:
                c=face.center
                if -.86<c.z<-.12 and math.sin(c.z*19+c.y*22+x*7)>-.08:
                    face.material_index=1
            parts.lash(f'Detail_PileLash_{x}_{y}',(x,y,.36),(0,0,1),.112,.09,.008,rope_mat,
                       turns=2.8,step=.018,seg=7,group='Detail_Small',detail=1)
    for x in (-.68,.68):
        # 轉角在右側留渡口；盡頭在遠端補一條橫欄。
        runs=[(-1.41,1.41)]
        if variant=='Corner' and x>0: runs=[(-1.41,-.56),(.56,1.41)]
        for j,(a,b) in enumerate(runs):
            parts.log(f'Handrail_{x}_{j}',[(x,a,1.06),(x+rng.uniform(-.012,.012),(a+b)*.5,1.08),(x,b,1.05)],
                      .083,old,seg=12,lump=.07,seed=j+7,group='Main',detail=0)
            for y in (a,b):
                parts.lash(f'Detail_RailLash_{x}_{j}_{y}',(x,y,1.06),(0,1,0),.084,.08,.006,rope_mat,
                           turns=2.2,step=.018,seg=6,group='Detail_Small',detail=1)
    if variant=='Corner':
        for y in (-.56,.56):
            parts.log(f'Opening_Post_{y}',[(.68,y,.43),(.68,y,1.15)],.09,old,
                      seg=12,lump=.07,seed=52+int(y*10),group='Main',detail=0)
            parts.lash(f'Detail_OpeningLash_{y}',(.68,y,1.03),(0,0,1),.095,.07,.006,rope_mat,
                       turns=2.0,step=.018,seg=6,group='Detail_Small',detail=1)
    if variant=='End':
        parts.log('End_Handrail',[(-.68,1.41,1.05),(0,1.41,1.08),(.68,1.41,1.05)],
                  .083,old,seg=12,lump=.07,seed=44,group='Main',detail=0)
    for x in (-.68,.68):
        for y in (-1.42,1.42):
            parts.between(f'Diagonal_Brace_{x}_{y}',(x,y,.20),(x*.7,y*.70,.47),.10,.08,old,
                          r=.007,amp=.004,chips=2,hew=1,seed=16,div=.10,group='Main',detail=0)
    return S

def run(variant):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
    S=geom(variant)
    out=ROOT/f'art/exports/valley-and-home-v1/FE01/{variant}/{VERSION}'
    src=ROOT/f'art/source/valley-and-home-v1/FE01/FE01-{variant.lower()}-pack-{VERSION}.blend'
    out.mkdir(parents=True,exist_ok=True);src.parent.mkdir(parents=True,exist_ok=True)
    # 灰模先交：幾何與材質的檢查彼此獨立。
    original={o:tuple(o.data.materials) for o in S['parts']}
    clay=bpy.data.materials.new('FE01_Clay');clay.diffuse_color=(.48,.48,.48,1)
    for o in original:o.data.materials.clear();o.data.materials.append(clay)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/f'FE01_{variant}_gray.blend'))
    for o,materials in original.items():
        o.data.materials.clear()
        for m in materials:o.data.materials.append(m)
    core.write_grain_attributes()
    pipe.join_groups()
    pipe.uv_atlas(size=1024,objs=list(S['lod0'].values()))
    pipe.spread_zero_uv(list(S['lod0'].values()))
    pipe.bake(out/'Textures',1024)
    bake_report=eli_bake_layers(S,out)
    pipe.make_lods()
    pipe.export_materials()
    for o in S['parts']:o.hide_render=True;o.hide_viewport=True
    bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,.38))
    col=bpy.context.object;col.name=f'SM_FE01_{variant}_Collision';col.dimensions=(1.50,2.98,.14)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    col.hide_render=True
    allmeshes=[o for groups in S['lods'].values() for o in groups.values()]
    for o in allmeshes:
        o.hide_render=not o.name.endswith('_LOD0')
        o.hide_viewport=False
    bpy.ops.wm.save_as_mainfile(filepath=str(src))
    bpy.ops.object.select_all(action='DESELECT')
    for o in allmeshes+[col]:o.select_set(True)
    bpy.context.view_layer.objects.active=allmeshes[0]
    bpy.ops.export_scene.fbx(filepath=str(out/f'FE01_{variant}.fbx'),use_selection=True,
        axis_forward='-Z',axis_up='Y',use_triangles=True,add_leaf_bones=False,bake_anim=False)
    bpy.ops.export_scene.gltf(filepath=str(out/f'FE01_{variant}.glb'),export_format='GLB',use_selection=True)
    tri={o.name:sum(len(p.vertices)-2 for p in o.data.polygons) for o in allmeshes}
    info={'id':'FE01','variant':variant,'version':VERSION,'dimensions_m':[1.6,3.0,2.16],
          'deck_top_z_m':.45,'pile_bottom_z_m':-1.0,'triangles':tri,
          'method':'Josh cr_parts 的 rbox/log/lash/tuft；cr_mats 與 vl_mats 程式材質；ti_pipeline 的圖集、烘焙及細節優先 LOD',
          'eli_bake_layers':bake_report,
          'reference':f'art/references/valley-and-home-v1/FE01-{variant}/',
          'unity_import':'未驗證'}
    (out/'model_info.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
    print('FE01_DONE',variant,tri,flush=True)

if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    for variant in (args if args else VARIANTS):
        assert variant in VARIANTS
        run(variant)
