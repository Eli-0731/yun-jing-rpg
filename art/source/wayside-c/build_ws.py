"""承天 · C 路邊小物 WS01–WS06（wayside-c）— Eli-0731, Blender 4.5.3 LTS.
Work pack: docs/execution/2026-11-14/C-120h-yards-undergrowth-and-wayside.md, batch C (A2 村外官道; docs/execution/blocks/A2-A3-block-plan.md; WS05 also A6 稻田).
WS01 路邊野花叢（黃、紫）、WS02 乾草叢（高、矮）、WS03 路邊碎石堆、WS04 疊石小塔（三塊、五塊）、WS05 稻草堆與稻束、WS06 柴捆.
Each item is modelled only after its three-view candidates are saved and one is picked in art/references/<ID>/prompt.txt.
The pipeline is the one of yard-props-c (build_yp.py, after yard-roadside-c/build_vg.py): the same tiled sources (with the YP ones),
part helpers and bake / split / LOD / export code; only the package name, the item table and the item files change.
Kinds of one ID are separate models (<ID>_01, <ID>_02), so each can be placed alone.
blender -b --factory-startup -P build_ws.py -- WS03 [WS04_01 ...] [--clay]
"""
import sys
from pathlib import Path
_VG=Path(__file__).resolve().parents[1]/'yard-roadside-c'/'build_vg.py';_YP=Path(__file__).resolve().parents[1]/'yard-props-c'
_t=_VG.read_text(encoding='utf-8');_a=_t.index('# ---------------- items');_b=_t.index('# ---------------- bake')
exec(compile(_t[:_a].replace("PKG='yard-roadside-c'","PKG='wayside-c'"),str(_VG),'exec'))   # imports, kit, tiled sources (HERE is this folder: __file__ is ours)
_make_sources_vg=make_sources
def make_sources():
    """the shared sources, then the YP ones (own seeds after all the others: the shared ones keep their textures)"""
    S=_make_sources_vg();E={}
    for _f in sorted(_YP.glob('yp_sources*.py'))+sorted(HERE.glob('ws_sources*.py')):exec(open(_f,encoding='utf-8').read(),globals(),{'E':E})
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
 'WS01_01':('WildflowersYellow',(.75,.75,.65),'standard'),'WS01_02':('WildflowersPurple',(.70,.70,.55),'standard'),
 'WS02_01':('DryGrassTall',(1.3,1.3,1.35),'standard'),'WS02_02':('DryGrassLow',(.85,.85,.42),'standard'),
 'WS03':('RoadsideStonePile',(1.4,1.1,.45),'standard'),
 'WS04_01':('CairnThree',(.45,.45,.45),'standard'),'WS04_02':('CairnFive',(.50,.50,.65),'standard'),
 'WS05_01':('StrawHeap',(1.9,1.6,.95),'standard'),'WS05_02':('RiceSheaves',(1.2,.8,1.0),'standard'),
 'WS06':('FirewoodBundles',(1.3,.95,.60),'standard'),
}
IDS=tuple(TABLE);TARGET={k:('x',None) for k in IDS};LIMIT={k:v[1] for k,v in TABLE.items()};NAME={k:v[0] for k,v in TABLE.items()};MIN_TIER={k:v[2] for k,v in TABLE.items()}
for _f in [CK/'wl_items.py']+sorted(CK.glob('fi_items*.py')):exec(open(_f,encoding='utf-8').read())   # part helpers (_sheet, _cane, _lathe, _ring, _plate …)
for _f in sorted((ROOT/'art/source/village-life-c').glob('lv_items*.py')):exec(open(_f,encoding='utf-8').read())   # LV part helpers (_hoop2, _staves …)
exec(open(ROOT/'art/source/ground-cover-c/gc_items.py',encoding='utf-8').read())   # _blob, _shard (stones)
for _f in sorted(_VG.parent.glob('vg_items*.py')):exec(open(_f,encoding='utf-8').read())   # VG part helpers (_bar, _beam, _turned, _rrect …)
PROPS.clear()   # only the YP items below
for _f in sorted(_YP.glob('yp_items*.py')):exec(open(_f,encoding='utf-8').read())   # YP part helpers (_fb, _vn, _sack, _slab …)
PROPS.clear()
for _f in sorted(HERE.glob('ws_items*.py')):exec(open(_f,encoding='utf-8').read())

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
