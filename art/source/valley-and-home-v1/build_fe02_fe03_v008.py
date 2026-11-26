"""FE02 舊船與 FE03 渡口小棚重做：沿用既有接口，加入 Josh 零件與 Eli 烘焙層。"""
from pathlib import Path
import sys, math, json
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'art/source/village-houses-b'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import ti_core as core
import ti_pipeline as pipe
import cr_parts as parts
import cr_mats as mats
import vl_mats
from build_fe01_v008 import eli_bake_layers

def relink_textures():
    texture_root=ROOT/'art/textures/valley-and-home-v1'
    for image in bpy.data.images:
        if image.source!='FILE':continue
        current=Path(bpy.path.abspath(image.filepath)) if image.filepath else Path('')
        if current.is_file() and image.has_data:continue
        filename=Path(image.filepath).name
        matches=list(texture_root.rglob(filename))
        if not matches:raise FileNotFoundError(f'{image.name}: {filename}')
        image.filepath=str(matches[0]);image.reload();image.pack()


def gray_save(path):
    old={o:(tuple(o.data.materials),[p.material_index for p in o.data.polygons])
         for o in bpy.data.objects if o.type=='MESH'}
    gray=bpy.data.materials.new('ReviewClay');gray.diffuse_color=(.46,.47,.48,1)
    for o in old:o.data.materials.clear();o.data.materials.append(gray)
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    for o,(mlist,indices) in old.items():
        o.data.materials.clear()
        for m in mlist:o.data.materials.append(m)
        for p,index in zip(o.data.polygons,indices):p.material_index=index


def warp_hull(o):
    for v in o.data.vertices:
        y=abs(v.co.y)/3.0
        influence=max(0,min(1,(v.co.z+.22)/.42))
        v.co.z+=.18*y*y*influence
        v.co.x*=(1-.34*max(0,(abs(v.co.y)-2.35)/.65))*(1+.035*math.sin(v.co.y*1.25))
    o.data.update()


def add_fe02():
    src=ROOT/'art/source/valley-and-home-v1/FE02/FE02-ferry-pack-v007.blend'
    out=ROOT/'art/exports/valley-and-home-v1/FE02/v008';out.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(src))
    relink_textures()
    for lod in (0,1,2):
        bpy.data.objects.remove(bpy.data.objects[f'SM_FE02_Canopy_LOD{lod}'],do_unlink=True)
    for name in ('SM_FE02_FerryHull_LOD0','SM_FE02_FerryHull_LOD1','SM_FE02_FerryHull_LOD2','Detail_FE02_HullPatches_LOD0'):
        warp_hull(bpy.data.objects[name])
    core.reset_state('SM_FE02_Rework')
    oldwood=mats.wood('FE02_WornGunwale',dark=vl_mats.WOOD[2],light=vl_mats.WOOD[1],wet_z=.18,moss=True,grey=.7,holes=.9,polish=.12)
    repair=mats.wood('FE02_RepairPatch',dark=vl_mats.WOOD[1],light=vl_mats.WOOD[0],wet_z=.1,moss=True,grey=.55,holes=.8)
    fabric=mats.canvas('FE02_OldCloth',base=(.38,.35,.29),stain=(.15,.13,.10),faded=.7,dirt=.9)
    woven=mats.canvas('FE02_WovenMat',base=(.32,.285,.18),stain=(.14,.115,.07),faded=.5,dirt=.7)
    bamboo=mats.culm('FE02_BambooRibs',green=(.12,.13,.075),straw=(.26,.21,.11))
    rope=mats.canvas('FE02_HempLashing',base=(.18,.15,.09),stain=(.065,.05,.025),faded=.6,dirt=.8)
    # 船舷兩側沿舊船首尾起伏，不使用直方條。
    for sign in (-1,1):
        pts=[]
        for i in range(17):
            y=-3+6*i/16
            width=.86-.47*(abs(y)/3)**2
            pts.append((sign*(width+.015),y,.31+.18*(abs(y)/3)**2+.015*math.sin(y*1.8)))
        parts.log(f'Gunwale_{sign}',pts,.038,oldwood,seg=10,lump=.09,seed=14+sign,group='Main',detail=0)
        for j,y in enumerate((-1.75,.68,1.8)):
            if sign<0 and j==0:continue
            width=.86-.47*(abs(y)/3)**2
            x=sign*(width+.022)
            parts.rbox(f'RepairPatch_{sign}_{j}',(x,y,.00),(.028,.34,.26),repair,
                       r=.006,amp=.004,chips=4,hew=2,seed=10+j,div=.08,
                       rot=(0,0,sign*.035),group='Main',detail=0)
    # 竹編篷重新編排；竹篾縱橫交錯，一側覆以破舊布。
    def arch(x):return .945-.36*(x/.78)**2
    def weave(u,v):
        x=-.78+u*1.56;y=.225+v*2.52
        return(x,y,arch(x))
    parts.sheet('BambooWeave_Mat',28,22,weave,woven,solid=.006,group='Canopy',detail=0)
    for x in (-.78,-.55,-.32,-.1,.1,.32,.55,.78):
        pts=[(x,.225+j*2.52/12,arch(x)+.012) for j in range(13)]
        parts.log(f'Long_BambooSlat_{x}',pts,.011,bamboo,seg=6,step=.10,lump=.035,group='Canopy',detail=0)
    for y in (.25,.75,1.25,1.75,2.25,2.70):
        pts=[(-.78+j*1.56/10,y,arch(-.78+j*1.56/10)+.033) for j in range(11)]
        parts.log(f'Cross_BambooRib_{y}',pts,.018,bamboo,seg=7,step=.09,lump=.04,group='Canopy',detail=0)
    for x in (-.72,.72):
        for y in (.27,2.68):
            parts.log(f'CanopyPost_{x}_{y}',[(x,y,.28),(x,y,.58)],.025,bamboo,
                      seg=8,step=.07,lump=.04,group='Canopy',detail=0)
    def cloth(u,v):
        x=-.68+u*.82;y=.88+v*1.55
        z=.945-.36*(x/.78)**2-.013+.018*math.sin(v*math.pi*4+u*2)
        return (x,y,z)
    parts.sheet('OldCloth_Canopy',18,26,cloth,fabric,solid=.006,
                keep=lambda u,v: not (v>.83 and u<.15 and (int(u*18)+int(v*26))%3==0),
                group='Canopy',detail=0)
    for y in (1.0,2.15):
        parts.rope(f'Canopy_Tie_{y}',[(-.70,y,.59),(-.78,y,.51),(-.85,y,.47)],.008,rope,
                   ply=3,tw=85,seg=6,group='Canopy',detail=1)
    gray_save(out/'FE02_v008_gray.blend')
    return out


def add_fe03():
    src=ROOT/'art/source/valley-and-home-v1/FE03/FE03-ferry-shed-pack-v007.blend'
    out=ROOT/'art/exports/valley-and-home-v1/FE03/v008';out.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(src))
    relink_textures()
    core.reset_state('SM_FE03_Rework')
    wood=mats.wood('FE03_WornWood',dark=vl_mats.WOOD[2],light=vl_mats.WOOD[1],wet_z=.15,moss=True,grey=.65,holes=.9)
    cloth=mats.canvas('FE03_OldRag',base=(.22,.205,.165),stain=(.07,.065,.05),faded=.7,dirt=.9)
    rope=mats.canvas('FE03_OldRope',base=(.16,.14,.10),stain=(.065,.05,.03),faded=.65,dirt=.9)
    # 舊箱、補板、繩圈與掛布，讓渡口可見日常使用痕跡。
    parts.rbox('CargoChest_Body',(-.65,-.32,.30),(.58,.43,.50),wood,
               r=.015,amp=.009,chips=5,hew=2,seed=41,div=.14,group='Main',detail=0)
    parts.rbox('CargoChest_Lid',(-.65,-.32,.57),(.63,.47,.05),wood,
               r=.007,amp=.004,chips=3,hew=2,seed=42,div=.11,group='Main',detail=0)
    for j in range(3):
        y=-.48+j*.15
        parts.rbox(f'Chest_RepairedSlat_{j}',(-.65,y,.585),(.54,.046,.012),wood,
                   r=.003,amp=.003,chips=2,hew=1,seed=j+44,div=.10,group='Detail_Small',detail=1)
    def rag(u,v):
        x=-1.15+.34*u;y=.24+.025*math.sin(u*6+v*5)
        z=1.50-.72*v+.03*math.sin(u*8+v*9)
        return(x,y,z)
    parts.sheet('Hanging_OldRag',13,20,rag,cloth,solid=.004,
                keep=lambda u,v: not(v>.84 and u>.68 and (int(u*13)+int(v*20))%2==0),
                group='Main',detail=0)
    parts.log('Leaning_Oar',[(.82,-.64,.08),(.94,.02,.50),(1.03,.63,1.08)],.042,wood,
              seg=10,lump=.06,seed=55,group='Main',detail=0)
    gray_save(out/'FE03_v008_gray.blend')
    return out


def finalize(code,out):
    S=core.S
    for o in bpy.data.objects:
        if o.type=='MESH' and o not in S['parts']:o.hide_render=True
    core.write_grain_attributes()
    pipe.join_groups()
    pipe.uv_atlas(size=512,objs=list(S['lod0'].values()))
    pipe.spread_zero_uv(list(S['lod0'].values()))
    pipe.bake(out/'Textures',512)
    eli_bake_layers(S,out,size=512)
    pipe.make_lods();pipe.export_materials()
    for o in S['parts']:o.hide_render=True;o.hide_viewport=True
    for o in bpy.data.objects:
        if o.type=='MESH' and '_LOD' in o.name:
            o.hide_render=not o.name.endswith('_LOD0')
    source=ROOT/f'art/source/valley-and-home-v1/{code}/{code.lower()}-rework-pack-v008.blend'
    source.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(source))
    export=[o for o in bpy.data.objects if o.type=='MESH' and ('_LOD' in o.name or '_Collision' in o.name)]
    bpy.ops.object.select_all(action='DESELECT')
    for o in export:o.select_set(True)
    bpy.context.view_layer.objects.active=export[0]
    bpy.ops.export_scene.fbx(filepath=str(out/f'{code}_rework.fbx'),use_selection=True,axis_forward='-Z',axis_up='Y',use_triangles=True,add_leaf_bones=False,bake_anim=False)
    bpy.ops.export_scene.gltf(filepath=str(out/f'{code}_rework.glb'),export_format='GLB',use_selection=True)
    info={'id':code,'version':'v008','source':str(source.relative_to(ROOT)).replace('\\','/'),
          'reference':f'art/references/valley-and-home-v1/{code}/',
          'method':'既有模型接口保留；Josh cr_parts/cr_mats/vl_mats 零件與材質；Eli AO、粗糙度、物件法線、Pointiness、位置圖烘焙',
          'lods':{o.name:sum(len(p.vertices)-2 for p in o.data.polygons) for o in export if '_LOD' in o.name},
          'materials':{o.name:len(o.data.materials) for o in export if '_LOD0' in o.name},
          'texture_resolution':512,'unity_import':'未驗證'}
    (out/'model_info.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf8')
    print('DONE',code,info['lods'],flush=True)

if __name__=='__main__':
    which=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['FE02','FE03']
    for code in which:
        if code=='FE02':out=add_fe02()
        elif code=='FE03':out=add_fe03()
        else:raise ValueError(code)
        finalize(code,out)
