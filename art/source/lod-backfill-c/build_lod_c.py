"""C's old sets: add LOD1 / LOD2 (and a Detail_Small group) without touching LOD0 — work pack 2026-11-07 part 2 C.
Same deliverable shape as B's art/exports/lod-backfill-b: one <ID>_LOD_v001.fbx (+ .blend) per item holding
<ID>_LOD0/1/2 (the body) and <ID>_Detail_Small_LOD0/1/2 (small parts that standard quality may switch off).
LOD0 is the source geometry as it is, only joined; LOD1 ~50 %, LOD2 ~15 %, decimated part by part.

  blender -b --factory-startup -P art/source/lod-backfill-c/build_lod_c.py -- <source.glb|fbx> [...]   (from the repo root)
The source files are only read. Output: art/exports/lod-backfill-c/<ID>/ and model_info.json there."""
import bpy,bmesh,sys,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(bpy.path.abspath('//')) if bpy.data.filepath else Path.cwd();OUT=ROOT/'art/exports/lod-backfill-c'
args=sys.argv[sys.argv.index('--')+1:]
RATIO={1:.5,2:.15};FLOOR={1:.5,2:.30}   # a part never goes below this share of its own faces
KEEP_TRIS=24   # parts this small are not decimated at all
TINY=.05   # LOD2 leaves out parts shorter than 5 % of the item's diagonal (pegs, nails, knots: not seen at LOD2 distance)
def tris(o):return sum(len(p.vertices)-2 for p in o.data.polygons)
def bbox(objs):
    lo=Vector((1e9,)*3);hi=Vector((-1e9,)*3)
    for o in objs:
        for v in o.data.vertices:
            w=o.matrix_world@v.co;lo=Vector(map(min,lo,w));hi=Vector(map(max,hi,w))
    return lo,hi
def sel(*obs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:o.select_set(True)
    bpy.context.view_layer.objects.active=obs[0]
def join(objs,name):
    objs=[o for o in objs if o.data.polygons]
    if not objs:return None
    if len(objs)>1:sel(*objs);bpy.ops.object.join()
    o=objs[0];o.name=o.data.name=name;return o
def open_edges(me):
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=bm.verts[:],dist=1e-5);n=sum(1 for e in bm.edges if e.is_boundary or len(e.link_faces)>2);bm.free();return n
def size(me):
    if not me.vertices:return Vector((0,0,0))
    co=[v.co for v in me.vertices];return Vector((max(c.x for c in co)-min(c.x for c in co),max(c.y for c in co)-min(c.y for c in co),max(c.z for c in co)-min(c.z for c in co)))
def decimate(o,L):
    """limited dissolve, then collapse towards the LOD's ratio; a try is undone when it opens the mesh (more open or
    non-manifold edges than the part had) or shrinks it by more than 2 % on any side — then a gentler ratio is tried,
    and a part that cannot be reduced safely stays whole (the low-poly staves and cloth wraps of #35 opened up)"""
    t0=tris(o)
    if t0<=KEEP_TRIS:return
    src=o.data.copy();bm=bmesh.new();bm.from_mesh(src);bmesh.ops.remove_doubles(bm,verts=bm.verts[:],dist=1e-5);bm.to_mesh(src);bm.free()   # the GLB splits vertices at UV seams: weld them (UVs stay per corner) or collapse tears the seams open
    src.set_sharp_from_angle(angle=math.radians(15));e0=open_edges(src);s0=size(src)
    for share in ((.5,.75) if L==1 else (.30,.40,.50,.75))+(None,):   # gentler steps; LOD2's steps never pass LOD1's
        if share is None or share>=.95:o.data=src;return
        o.data=src.copy()
        m=o.modifiers.new('dis','DECIMATE');m.decimate_type='DISSOLVE';m.angle_limit=math.radians(1.0);m.delimit={'MATERIAL','SEAM','SHARP','UV'}
        sel(o);bpy.ops.object.modifier_apply(modifier='dis')
        t1=tris(o);target=t0*share
        if t1>target:
            m=o.modifiers.new('d','DECIMATE');m.ratio=target/t1;m.use_collapse_triangulate=True
            sel(o);bpy.ops.object.modifier_apply(modifier='d')
        o.data.set_sharp_from_angle(angle=math.radians(15))   # hard edges again on the reduced mesh: its new folds shade as facets, not as dark smooth wedges
        s1=size(o.data)
        if open_edges(o.data)<=e0 and all(s1[i]>=s0[i]*.98-1e-4 for i in range(3)):return
info={}
mi=OUT/'model_info.json'
if mi.exists():info=json.loads(mi.read_text(encoding='utf-8'))
for src in args:
    src=Path(src);pid=src.stem;bpy.ops.wm.read_factory_settings(use_empty=True)
    (bpy.ops.import_scene.fbx if src.suffix=='.fbx' else bpy.ops.import_scene.gltf)(filepath=str(src))
    parts=[o for o in bpy.context.scene.objects if o.type=='MESH']
    for o in list(bpy.context.scene.objects):   # bake the hierarchy into the meshes, drop empties
        if o.type=='MESH':
            mw=o.matrix_world.copy();o.parent=None;o.matrix_world=mw
    sel(*parts);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    for o in [o for o in bpy.context.scene.objects if o.type!='MESH']:bpy.data.objects.remove(o)
    lo,hi=bbox(parts);diag=(hi-lo).length;src_tris=sum(tris(o) for o in parts);src_dims=[round(x,4) for x in (hi-lo)]
    # small parts: short (under 7 % of the item's diagonal and 9 cm) and few faces — cords, pegs, nails, tags
    small=[o for o in parts if (lambda a,b:(b-a).length)(*bbox([o]))<min(.09,.07*diag) and tris(o)<.08*src_tris]
    body=[o for o in parts if o not in small]
    groups={'':body,'Detail_Small_':small};out={}
    for g,objs in groups.items():
        if not objs:continue
        for L in (2,1,0):
            cp=[]
            for o in objs:
                if L==2 and g=='' and (lambda a,b:(b-a).length)(*bbox([o]))<TINY*diag:continue   # tiny parts drop out of LOD2
                c=o.copy();c.data=o.data.copy();bpy.context.scene.collection.objects.link(c);cp.append(c)
                if L:decimate(c,L)
            out[(g,L)]=join(cp,f'{pid}_{g}LOD{L}')
        for o in objs:bpy.data.objects.remove(o)
    d=OUT/pid;d.mkdir(parents=True,exist_ok=True)
    lods={}
    for L in (0,1,2):
        ob=[out[k] for k in out if k[1]==L and out[k]];mats={m.name for o in ob for m in o.data.materials if m}
        tex={}
        for m in {m for o in ob for m in o.data.materials if m and m.use_nodes}:
            for n in m.node_tree.nodes:
                if n.type=='TEX_IMAGE' and n.image:tex[n.image.name]=list(n.image.size)
        lods[f'LOD{L}']={'triangles':sum(tris(o) for o in ob),'triangles_without_detail':tris(out[('',L)]) if out.get(('',L)) else 0,'objects':len(ob),'materials':len(mats),'textures_px':tex}
    lo2,hi2=bbox([out[k] for k in out if k[1]==0 and out[k]])
    stem=f'{pid}_LOD_v001';fbx=d/f'{stem}.fbx';blend=d/f'{stem}.blend';td=d/'Textures';td.mkdir(exist_ok=True)
    for m in {m for o in bpy.context.scene.objects if o.type=='MESH' for m in o.data.materials if m and m.use_nodes}:   # the GLB's images have no names: written out under unique names
        for i,n in enumerate([n for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]):   # (embedded in the FBX they collided and C04's sage cloth came back as hemp)
            im=n.image;nm=f'{pid}_{m.name}_{i}'.replace(' ','_')
            if im.get('lodc_saved'):continue
            im.name=nm;im.filepath_raw=str(td/f'{nm}.png');im.file_format='PNG';im.save();im['lodc_saved']=1
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Z',axis_up='Y',mesh_smooth_type='FACE',path_mode='RELATIVE',embed_textures=False,bake_anim=False)
    bpy.ops.export_scene.gltf(filepath=str(d/f'{stem}.glb'),use_selection=True,export_format='GLB',export_apply=True)   # same LODs as GLB, the format the set was delivered in
    bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
    info[pid]={'id':pid,'version':'v001','source':src.as_posix(),'source_untouched':True,'dimensions_xyz_m':[round(x,3) for x in (hi2-lo2)],'source_dimensions_xyz_m':src_dims,
               'source_triangles':src_tris,'lod0_equals_source':lods['LOD0']['triangles']==src_tris,'lods':lods,
               'lod2_share':round(lods['LOD2']['triangles']/max(1,lods['LOD0']['triangles']),3),'detail_parts':len(small),'minTier':'standard',
               'lod_method':f'per part: limited dissolve (1°, keeps material / UV / sharp edges), then collapse to 50 % / 15 % but never below {int(FLOOR[2]*100)} % of the part at LOD2; parts of ≤ {KEEP_TRIS} faces kept whole; LOD2 leaves out parts shorter than {int(TINY*100)} % of the item diagonal',
               'files':{'fbx':fbx.relative_to(ROOT).as_posix(),'glb':(d/f'{stem}.glb').relative_to(ROOT).as_posix(),'blend':blend.relative_to(ROOT).as_posix(),'textures':td.relative_to(ROOT).as_posix()}}
    print('LODC',pid,[lods[f'LOD{L}']['triangles'] for L in range(3)],'detail',len(small),'lod0==src',info[pid]['lod0_equals_source'])
mi.parent.mkdir(parents=True,exist_ok=True);mi.write_text(json.dumps(info,ensure_ascii=False,indent=1),encoding='utf-8')
