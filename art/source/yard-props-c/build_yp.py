"""承天 · C 院子小物 YP01–YP13（yard-props-c）— Eli-0731, Blender 4.5.3 LTS.
Work pack: docs/execution/2026-11-14/C-120h-yards-undergrowth-and-wayside.md, batch A (A1 青溪村 yards; setting image A1 V6, YP13 on V5).
YP01 菜圃（三種作物）、YP02 晾衣繩與衣物、YP03 木水桶與木杓、YP04 石臼與木杵、YP05 木長凳（長、短）、YP06 草蓆（攤平、捲起）與曬穀竹匾、
YP07 盆栽香草（三種）、YP08 牆上掛串（竹篩、辣椒、玉米、蒜）、YP09 木箱（一般、帶蓋米箱）、YP10 獨輪車、YP11 扁擔與兩個水桶、YP12 大水缸、YP13 溪邊水草與小花.
Each item is modelled only after its three-view candidates are saved and one is picked in art/references/<ID>/prompt.txt.
The pipeline is the one of yard-roadside-c (build_vg.py): this file reuses its tiled sources and its bake / split / LOD / export code as they are,
and only swaps the package name, the item table and the item files. Kinds of one ID are separate models (<ID>_01, <ID>_02 …), so each can be placed alone.
blender -b --factory-startup -P build_yp.py -- YP03 [YP04 ...] [--clay]
"""
import sys
from pathlib import Path
_VG=Path(__file__).resolve().parents[1]/'yard-roadside-c'/'build_vg.py'
_t=_VG.read_text(encoding='utf-8');_a=_t.index('# ---------------- items');_b=_t.index('# ---------------- bake')
exec(compile(_t[:_a].replace("PKG='yard-roadside-c'","PKG='yard-props-c'"),str(_VG),'exec'))   # imports, kit, tiled sources (HERE is this folder: __file__ is ours)
_make_sources_vg=make_sources
def make_sources():
    """the shared sources, then the YP ones (own seeds after all the others: the shared ones keep their textures)"""
    S=_make_sources_vg();E={}
    for _f in sorted(HERE.glob('yp_sources*.py')):exec(open(_f,encoding='utf-8').read(),globals(),{'E':E})
    for k,(alb,h,s,r,m,glow) in E.items():
        mat=bpy.data.materials.new('src_'+k);mat.use_nodes=True;nt=mat.node_tree;bs=nt.nodes['Principled BSDF']
        bs.inputs['Roughness'].default_value=r;bs.inputs['Metallic'].default_value=m
        uvn=nt.nodes.new('ShaderNodeUVMap');uvn.uv_map='Tiled'
        ta=nt.nodes.new('ShaderNodeTexImage');ta.image=K.img('alb_'+k,alb);nt.links.new(uvn.outputs['UV'],ta.inputs['Vector']);nt.links.new(ta.outputs['Color'],bs.inputs['Base Color'])
        tn=nt.nodes.new('ShaderNodeTexImage');tn.image=K.nmap('nrm_'+k,h,s);nt.links.new(uvn.outputs['UV'],tn.inputs['Vector'])
        nm=nt.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.8;nt.links.new(tn.outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
        S[k]=mat
    return S

# ---------------- items (filled per item after its three-view is picked) ----------------
PROPS={}
# id: (name, size limit w × d × h in m, minTier)
TABLE={
 'YP02':('WashingLine',(2.7,.5,2.1),'standard'),
 'YP03':('WaterBucketLadle',(.50,.50,.50),'standard'),
 'YP04':('StoneMortarPestle',(.60,.60,.75),'standard'),
 'YP05_01':('BenchLong',(1.6,.40,.50),'standard'),'YP05_02':('BenchShort',(.70,.40,.50),'standard'),
 'YP06_01':('RushMatFlat',(1.95,1.05,.12),'standard'),'YP06_02':('RushMatRolled',(1.0,.30,.26),'standard'),'YP06_03':('DryingTrayRice',(.90,.90,.14),'standard'),
 'YP07_01':('PotScallion',(.60,.60,.62),'standard'),'YP07_02':('TubBroadHerb',(.60,.60,.62),'standard'),'YP07_03':('PotFloweringHerb',(.60,.60,.62),'standard'),
 'YP08':('WallHangings',(1.75,.50,1.2),'standard'),
 'YP09_01':('CrateOpen',(.72,.45,.40),'standard'),'YP09_02':('RiceChest',(.68,.56,.60),'standard'),
 'YP10':('Wheelbarrow',(1.85,.80,1.0),'standard'),
 'YP11':('CarryingPoleBuckets',(1.8,.5,.6),'standard'),'YP12':('WaterVat',(.85,.85,.98),'standard'),
}
IDS=tuple(TABLE);TARGET={k:('x',None) for k in IDS};LIMIT={k:v[1] for k,v in TABLE.items()};NAME={k:v[0] for k,v in TABLE.items()};MIN_TIER={k:v[2] for k,v in TABLE.items()}
for _f in [CK/'wl_items.py']+sorted(CK.glob('fi_items*.py')):exec(open(_f,encoding='utf-8').read())   # part helpers (_sheet, _cane, _lathe, _ring, _plate …)
for _f in sorted((ROOT/'art/source/village-life-c').glob('lv_items*.py')):exec(open(_f,encoding='utf-8').read())   # LV part helpers (_hoop2, _staves …)
exec(open(ROOT/'art/source/ground-cover-c/gc_items.py',encoding='utf-8').read())   # _blob, _shard (stones)
for _f in sorted(_VG.parent.glob('vg_items*.py')):exec(open(_f,encoding='utf-8').read())   # VG part helpers (_bar, _beam, _turned, _rrect …)
PROPS.clear()   # only the YP items below
for _f in sorted(HERE.glob('yp_items*.py')):exec(open(_f,encoding='utf-8').read())

def _relief(nrm,pos,filled,h,k=1.):
    """a painted height field (metres, on the baked position map) added to the baked tangent normal map: cracks, checks,
    chisel facets, flaked glaze. The slope is taken along U and V from neighbouring texels of the same island."""
    h=np.asarray(h,np.float32);m=float(np.median(np.linalg.norm(pos[:,1:]-pos[:,:-1],axis=2)[filled[:,1:]&filled[:,:-1]]))
    def grad(ax):
        d=np.linalg.norm(np.roll(pos,-1,ax)-np.roll(pos,1,ax),axis=2);ok=np.roll(filled,-1,ax)&np.roll(filled,1,ax)&filled&(d<6*m)&(d>1e-9)
        return np.clip(np.where(ok,(np.roll(h,-1,ax)-np.roll(h,1,ax))/np.maximum(d,1e-9),0)*k,-1.2,1.2)
    n=nrm[...,:3]*2-1;n[...,0]-=grad(1);n[...,1]-=grad(0);n/=np.maximum(np.linalg.norm(n,axis=2,keepdims=True),1e-6)
    out=nrm.copy();out[...,:3]=n*.5+.5;return out
_tail=_t[_b:];_hook="    if meta.get('paint'):col,rough=meta['paint'](col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta)\n"
assert _hook in _tail
_tail=_tail.replace(_hook,_hook+"    if meta.get('relief'):nrm=_relief(nrm,pos,filled,meta['relief'](),meta.get('relief_k',1.))   # YP: painted relief into the normal map\n")
exec(compile(_tail,str(_VG),'exec'))   # bake / split / LOD / export, and the command line
