"""承天 · C 林下植物 SH01–SH02、SP01、UG01–UG06（undergrowth-c）— Eli-0731, Blender 4.5.3 LTS.
Work pack: docs/execution/2026-11-14/C-120h-yards-undergrowth-and-wayside.md, batch B (D2 林下; setting views D2 V2, V3, V6),
and docs/execution/2026-11-14/樹木重做-v2-分工.md with its guide tree-method/天空島世界樹建模歷程與精修方法.md:
leaves one by one along the twigs (five-vertex leaves: four outline points and a raised midrib), no leaf cards, no leaf atlas,
three orders of branches, height colour and canopy occlusion in the vertex colour, a wind weight in the second UV.
Each item is modelled only after its three-view candidates are saved and one is picked in art/references/<ID>/prompt.txt.
The pipeline is the one of yard-props-c / yard-roadside-c (build_vg.py: tiled sources → one atlas → Cycles bake → body + Detail_* → LOD),
with three changes for plants, switched on per item through meta:
  meta['ground0']   the origin stays where the item put it (the stem base on the ground, z = 0); stems run on below the ground
  meta['foliage']   LOD1 / LOD2: the leaves are thinned (every 4th / 12th leaf kept, each enlarged about its stalk) instead of
                    decimated, the wood is decimated on its own (the guide: LOD1 a quarter of the leaves, each larger)
  meta['vcol']      vertex colour COLOR_0 (RGB height / inside-outside colour, A canopy occlusion) and UV2 'Wind'
                    (u: wind weight, 0 at the stem base … 1 at the leaf tips; v: phase) on every LOD
Parts mark their faces with the int face attribute 'leaf' (leaf number, 0 = wood) and their leaf stalk vertex with 'lbase' = 1.
blender -b --factory-startup -P build_ug.py -- SH01 [--clay]
"""
import sys
from pathlib import Path
_VG=Path(__file__).resolve().parents[1]/'yard-roadside-c'/'build_vg.py';_YP=Path(__file__).resolve().parents[1]/'yard-props-c'
_t=_VG.read_text(encoding='utf-8');_a=_t.index('# ---------------- items');_b=_t.index('# ---------------- bake')
exec(compile(_t[:_a].replace("PKG='yard-roadside-c'","PKG='undergrowth-c'"),str(_VG),'exec'))
_make_sources_vg=make_sources
def make_sources():
    """the shared sources, then the YP ones, then the UG ones (each set after the others: the earlier ones keep their textures)"""
    S=_make_sources_vg();E={}
    for _f in sorted(_YP.glob('yp_sources*.py'))+sorted(HERE.glob('ug_sources*.py')):exec(open(_f,encoding='utf-8').read(),globals(),{'E':E})
    for k,(alb,h,s,r,m,glow) in E.items():
        mat=bpy.data.materials.new('src_'+k);mat.use_nodes=True;nt=mat.node_tree;bs=nt.nodes['Principled BSDF']
        bs.inputs['Roughness'].default_value=r;bs.inputs['Metallic'].default_value=m
        uvn=nt.nodes.new('ShaderNodeUVMap');uvn.uv_map='Tiled'
        ta=nt.nodes.new('ShaderNodeTexImage');ta.image=K.img('alb_'+k,alb);nt.links.new(uvn.outputs['UV'],ta.inputs['Vector']);nt.links.new(ta.outputs['Color'],bs.inputs['Base Color'])
        tn=nt.nodes.new('ShaderNodeTexImage');tn.image=K.nmap('nrm_'+k,h,s);nt.links.new(uvn.outputs['UV'],tn.inputs['Vector'])
        nm=nt.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.8;nt.links.new(tn.outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
        S[k]=mat
    return S

PROPS={}
# id: (name, size limit w × d × h in m (h counts the stems under the ground too), minTier)
TABLE={
 'SH01':('UnderstoryShrubBroadleaf',(2.2,2.2,2.4),'standard'),
 'UG01':('WaistHighFernClump',(2.0,2.0,1.4),'standard'),
 'UG02':('HeartLeafForestPlant',(1.2,1.2,.9),'standard'),
 'UG03':('StrapLeafForestPlant',(1.2,1.2,.75),'standard'),
 'UG04':('WhiteWildflowerClump',(.6,.6,.4),'standard'),
 'UG05_01':('FallenLeafHeapSmall',(.6,.6,.15),'standard'),
 'UG05_02':('FallenLeafHeapMedium',(1.2,1.2,.25),'standard'),
 'UG05_03':('FallenLeafHeapLarge',(1.8,1.8,.32),'standard'),
 'UG06_01':('RootVineStraight',(1.2,.5,.4),'standard'),
 'UG06_02':('RootVineWinding',(1.6,.6,.6),'standard'),
 'UG06_03':('RootVineWrapping',(1.4,.8,.7),'standard'),
 'UG06_04':('RootVineDownToGround',(1.6,.7,.6),'standard'),
}
IDS=tuple(TABLE);TARGET={k:('x',None) for k in IDS};TARGET['SH01']=('z',1.93)   # 1.75 m above the ground + the stems under it
LIMIT={k:v[1] for k,v in TABLE.items()};NAME={k:v[0] for k,v in TABLE.items()};MIN_TIER={k:v[2] for k,v in TABLE.items()}
CK=ROOT/'art/source/creekside-life-c'
for _f in [CK/'wl_items.py']+sorted(CK.glob('fi_items*.py')):exec(open(_f,encoding='utf-8').read())
for _f in sorted((ROOT/'art/source/village-life-c').glob('lv_items*.py')):exec(open(_f,encoding='utf-8').read())
exec(open(ROOT/'art/source/ground-cover-c/gc_items.py',encoding='utf-8').read())
for _f in sorted(_VG.parent.glob('vg_items*.py')):exec(open(_f,encoding='utf-8').read())
for _f in sorted(_YP.glob('yp_items*.py')):exec(open(_f,encoding='utf-8').read())   # YP part helpers (_fb, _vn noise …)
PROPS.clear()
for _f in sorted(HERE.glob('ug_items*.py')):exec(open(_f,encoding='utf-8').read())

def foliage_lod(e,L,meta):
    """LOD L of a plant body: wood decimated alone; leaves thinned to every n-th one, each kept leaf scaled about its stalk"""
    keep,grow,wood_ratio=meta['foliage'][L-1]
    me=e.data;nf=len(me.polygons);lf=np.zeros(nf,np.int32);me.attributes['leaf'].data.foreach_get('value',lf)
    W=e.copy();W.data=me.copy();bpy.context.scene.collection.objects.link(W)
    bm=bmesh.new();bm.from_mesh(W.data);la=bm.faces.layers.int['leaf'];bmesh.ops.delete(bm,geom=[f for f in bm.faces if f[la]!=0],context='FACES');bm.to_mesh(W.data);bm.free()
    m=W.modifiers.new('d','DECIMATE');m.ratio=wood_ratio;m.use_collapse_triangulate=True;sel(W);bpy.ops.object.modifier_apply(modifier='d')
    bm=bmesh.new();bm.from_mesh(me);la=bm.faces.layers.int['leaf'];lb=bm.verts.layers.float['lbase']
    bmesh.ops.delete(bm,geom=[f for f in bm.faces if f[la]==0 or (f[la]*2654435761%4294967296)%keep!=0],context='FACES')
    vs={}
    for f in bm.faces:
        for v in f.verts:vs.setdefault(f[la],set()).add(v)
    for k,vv in vs.items():
        b=[v for v in vv if v[lb]>.5];c=b[0].co.copy() if b else sum((v.co for v in vv),Vector())/len(vv)
        for v in vv:v.co=c+(v.co-c)*grow
    bm.to_mesh(me);bm.free()
    sel(e,W);bpy.context.view_layer.objects.active=e;bpy.ops.object.join();return bpy.context.object

def plant_attrs(lods,meta):
    """COLOR_0 and UV2 'Wind' on every Body LOD (leaf colour from meta['vcol'](pos, is_leaf, H) → (r, g, b, occlusion))"""
    H=meta['height']
    for L,o in enumerate(lods['Body']):
        me=o.data;n=len(me.loops);vi=np.zeros(n,np.int32);me.loops.foreach_get('vertex_index',vi)
        co=np.zeros(len(me.vertices)*3);me.vertices.foreach_get('co',co);co=co.reshape(-1,3)[vi]
        fl=np.zeros(len(me.polygons),np.int32)
        if 'leaf' in me.attributes:me.attributes['leaf'].data.foreach_get('value',fl)
        ls=np.zeros(len(me.polygons),np.int32);lt=np.zeros(len(me.polygons),np.int32);me.polygons.foreach_get('loop_start',ls);me.polygons.foreach_get('loop_total',lt)
        leafl=np.repeat(fl,lt);isleaf=leafl>0
        rgba=meta['vcol'](co,isleaf,H)
        ca=me.color_attributes.new('Col','BYTE_COLOR','CORNER');ca.data.foreach_set('color',np.clip(rgba,0,1).astype(np.float32).ravel())
        me.color_attributes.active_color=ca;me.color_attributes.render_color_index=0
        r=np.hypot(co[:,0],co[:,1]);hz=np.clip(co[:,2]/H,0,1)
        w=np.where(isleaf,np.clip(.55+.45*hz,0,1),np.clip(hz**1.4*.6+np.clip(r/1.2,0,1)*.25,0,.85))   # stems stiff at the base, the leaves move most
        ph=np.where(isleaf,(leafl*0.6180339)%1.,np.clip(np.arctan2(co[:,1],co[:,0])/math.tau+.5,0,1))
        uv=me.uv_layers.new(name='Wind');uv.data.foreach_set('uv',np.dstack([w,ph]).astype(np.float32).ravel())
        me.uv_layers.active=me.uv_layers['UVMap']
        for a in ('leaf','lbase'):
            if a in me.attributes:me.attributes.remove(me.attributes[a])

_tail=_t[_b:]
def _sub(a,b):
    global _tail
    assert _tail.count(a)==1,a;_tail=_tail.replace(a,b)
_sub("off=Vector((-(lo[0]+hi[0])/2,-(lo[1]+hi[1])/2,-lo[2]))","off=Vector((0,0,0)) if meta.get('ground0') else Vector((-(lo[0]+hi[0])/2,-(lo[1]+hi[1])/2,-lo[2]))")
_sub("meta['offset']=np.array(off[:]);meta['height']=float(hi[2]-lo[2])","meta['offset']=np.array(off[:]);meta['height']=float(hi[2]-(0. if meta.get('ground0') else lo[2]))")
_sub("            else:\n                m=e.modifiers.new('d','DECIMATE');m.ratio=ratio;m.use_collapse_triangulate=True;sel(e);bpy.ops.object.modifier_apply(modifier='d');e.hide_render=True;grp.append(e)",
     "            elif meta.get('foliage') and name=='Body':\n                e=foliage_lod(e,L,meta);e.name=e.data.name=f'{pid}_{name}_LOD{L}';e.parent=root;e.hide_render=True;grp.append(e)\n"
     "            else:\n                m=e.modifiers.new('d','DECIMATE');m.ratio=ratio;m.use_collapse_triangulate=True;sel(e);bpy.ops.object.modifier_apply(modifier='d');e.hide_render=True;grp.append(e)")
_sub("    col_obj=None;col_info=None\n","    if meta.get('vcol'):plant_attrs(lods,meta)\n    for g_ in lods.values():\n        for d_ in g_:\n            for a_ in ('leaf','lbase'):\n                if a_ in d_.data.attributes:d_.data.attributes.remove(d_.data.attributes[a_])\n    col_obj=None;col_info=None\n")
_sub("use_selection=True,export_format='GLB',export_apply=True)","use_selection=True,export_format='GLB',export_apply=True,export_vertex_color='ACTIVE')")
_sub("'origin':'footprint centre, bottom z = 0, front = -Y (Blender) / -Z (FBX, Unity)',","'origin':meta.get('origin_note','footprint centre, bottom z = 0, front = -Y (Blender) / -Z (FBX, Unity)'),")
exec(compile(_tail,str(_VG),'exec'))
