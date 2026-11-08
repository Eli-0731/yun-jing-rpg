"""LOD backfill for B's older assets (11/07 work pack, LOD 補齊).

LOD0 keeps the source geometry exactly (modifiers applied, as the source FBX already exported it); this script only
  1. joins the parts into one body object and one Detail_Small object (small parts you can switch off),
  2. adds LOD1 (about 50 %) and LOD2 (about 15 %) made from LOD0,
  3. writes FBX + model_info.json (triangles, objects, materials, texture sizes, minTier, detailObjects) into a new folder.
The source files are only read, never written.

usage:
  blender --background --factory-startup --python lod_backfill.py -- <job.json> <ID> <out_root>
job.json: {"<ID>": {"src": "...blend|fbx", "root": "<object name or null>", "detail_max_m": 0.3, "min_tier": "standard",
                    "keep": ["name prefixes never treated as detail"], "detail": ["name prefixes always detail"],
                    "recentre": true, "split_loose": false, "note": "..."}}
"""
import bpy, bmesh, json, math, os, sys, shutil
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
JOB, AID, OUT = argv[0], argv[1], argv[2]
cfg = json.load(open(JOB, encoding='utf-8'))[AID]
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
src = os.path.join(REPO, cfg['src']) if not os.path.isabs(cfg['src']) else cfg['src']
out_dir = os.path.join(OUT, AID); os.makedirs(out_dir, exist_ok=True)


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def descendants(o):
    out = [o]
    for c in o.children: out += descendants(c)
    return out


# ------------------------------------------------------------------ load the source (read only)
bpy.ops.wm.read_factory_settings(use_empty=True)
if src.lower().endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=src)
else:
    bpy.ops.import_scene.fbx(filepath=src)
scene = bpy.context.scene
root = bpy.data.objects.get(cfg['root']) if cfg.get('root') else None
pool = [o for o in (descendants(root) if root else scene.objects) if o.type == 'MESH' and not o.hide_render and o.visible_get()]
skip = tuple(cfg.get('skip', ()))
def not_exported(o):        # Dondon files keep studio floors / concept boards in collections like 90_Studio_Not_Exported, 80_Concept_References
    return any(k in c.name for c in o.users_collection for k in ('Not_Exported', 'Studio', 'Concept'))
pool = [o for o in pool if not o.name.startswith(skip) and not not_exported(o)]
DETAIL_COLL = tuple(cfg.get('detail_collections', ()))
detail_names = {o.name for o in pool if any(c.name.startswith(DETAIL_COLL) for c in o.users_collection)} if DETAIL_COLL else set()
if cfg.get('only_lod0'):                      # source already has LOD objects: LOD0 is the source
    pool = [o for o in pool if 'LOD1' not in o.name and 'LOD2' not in o.name]
if not pool: raise SystemExit('no meshes under root')

# evaluated copies in world space (modifiers applied, exactly what the source FBX exported)
dg = bpy.context.evaluated_depsgraph_get()
work = bpy.data.collections.new('LODWORK'); scene.collection.children.link(work)
parts = []
src_tris = 0
for o in pool:
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    me.transform(o.matrix_world)
    if not len(me.polygons): bpy.data.meshes.remove(me); continue
    n = bpy.data.objects.new(o.name, me); n['src'] = o.name; work.objects.link(n); parts.append(n); src_tris += tris(n)
for o in list(bpy.data.objects):                 # drop the source objects so the new LOD names stay exact (no .001 suffix)
    if work not in o.users_collection: bpy.data.objects.remove(o)
for c in list(scene.collection.children):
    if c != work: scene.collection.children.unlink(c)
bpy.context.view_layer.update()
for o in list(scene.collection.objects): scene.collection.objects.unlink(o)

# optional: split single merged objects into loose parts so small pieces can become Detail
if cfg.get('split_loose'):
    for o in list(parts):
        bpy.context.view_layer.objects.active = o
        for x in bpy.context.view_layer.objects: x.select_set(x == o)
        bpy.ops.mesh.separate(type='LOOSE')
    parts = [o for o in work.objects if o.type == 'MESH']

# recentre: bottom centre of the footprint at the origin (front stays -Y); offset recorded
lo = Vector((min(min((v.co[i] for v in o.data.vertices)) for o in parts) for i in range(3)))
hi = Vector((max(max((v.co[i] for v in o.data.vertices)) for o in parts) for i in range(3)))
offset = Vector((0, 0, 0))
if cfg.get('recentre', True):
    offset = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    for o in parts: o.data.transform(__import__('mathutils').Matrix.Translation(-offset))
size = hi - lo

# ------------------------------------------------------------------ detail split
dmax = cfg.get('detail_max_m', .3); keep = tuple(cfg.get('keep', ())); force = tuple(cfg.get('detail', ()))
def open_shell(o):         # surface patches (bank skins, moss sheets) have open borders and fill holes in the body: never detail
    cnt = {}
    for p in o.data.polygons:
        for k in p.edge_keys: cnt[k] = cnt.get(k, 0) + 1
    return any(v == 1 for v in cnt.values())
def is_detail(o):
    nm = o.get('src', o.name)
    if nm in detail_names or (force and nm.startswith(force)): return True
    if keep and nm.startswith(keep): return False
    if cfg.get('detail_closed_only') and open_shell(o): return False
    xs = [v.co for v in o.data.vertices]
    d = Vector((max(v[i] for v in xs) - min(v[i] for v in xs) for i in range(3)))
    return max(d) < min(dmax, cfg.get('detail_rel', .12) * max(size))   # small against the asset as well as in metres
detail = [o for o in parts if is_detail(o)]
body = [o for o in parts if o not in detail]


def join(objs, name):
    if not objs: return None
    for x in bpy.context.view_layer.objects: x.select_set(False)
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1: bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active; o.name = name; o.data.name = name
    assert o.name == name, (o.name, name)
    return o


main0 = join(body, f'{AID}_LOD0')
det0 = join(detail, f'{AID}_Detail_Small_LOD0')


def add_decimate(x, ratio):
    """Collapse decimate; with protect_borders the open borders and hard creases (rims, lid edges, stave ends) are kept out of the
    'free' vertex group, which the collapse treats as costly to move, so round rims and patch edges stay where they are."""
    m = x.modifiers.new('dec', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = ratio; m.use_collapse_triangulate = True
    if not cfg.get('protect_borders') or tris(x) < cfg.get('protect_min_tris', 0): return m   # tiny patches may move
    bm = bmesh.new(); bm.from_mesh(x.data); bm.edges.ensure_lookup_table()
    crease = math.radians(cfg.get('protect_crease_deg', 55))
    keep = set()
    for e in bm.edges:
        if len(e.link_faces) != 2 or e.calc_face_angle(0) > crease: keep.update(v.index for v in e.verts)
    bm.free()
    g = x.vertex_groups.new(name='decim_free')
    g.add([i for i in range(len(x.data.vertices)) if i not in keep], 1., 'REPLACE')
    m.vertex_group = 'decim_free'; m.vertex_group_factor = cfg.get('protect_factor', 50.)
    return m


def make_lod(o0, name, ratio, planar_deg):
    """LOD from LOD0: planar dissolve of flat detail first (keeps silhouettes), then collapse to the ratio; material, UV and sharp
    borders are kept as limits so walls, roofs and trims stay readable."""
    if o0 is None: return None
    o = o0.copy(); o.data = o0.data.copy(); o.name = name; o.data.name = name; work.objects.link(o)
    assert o.name == name, (o.name, name)
    target = max(12, int(tris(o0) * ratio))
    bm = bmesh.new(); bm.from_mesh(o.data)
    if cfg.get('weld', True): bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=.0001)   # stacked blocks (B12 stones) must not weld into their wall
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(planar_deg), use_dissolve_boundaries=False, verts=bm.verts, edges=bm.edges,
                             delimit={'MATERIAL', 'SEAM', 'SHARP', 'UV'})
    bm.to_mesh(o.data); bm.free()
    bmesh_tri = tris(o)
    if bmesh_tri > target and cfg.get('lod_per_island'):
        # one collapse over the joined mesh spends the budget by absolute error, so small parts (corks, lids, rims, bank
        # patches) collapse first and deform or open holes; here every loose part keeps the same share, with a small floor
        floor = cfg.get('island_floor', 16)
        bpy.context.view_layer.objects.active = o
        for x in bpy.context.view_layer.objects: x.select_set(x == o)
        bpy.ops.mesh.separate(type='LOOSE')
        isl = [x for x in bpy.context.selected_objects]
        for x in isl:
            share = max(target / bmesh_tri, cfg.get("island_min_ratio", 0) if ratio < .5 else 0)   # LOD2 floor share for round shells
            t = tris(x); tg = max(min(t, floor), int(t * share))
            xs = [v.co for v in x.data.vertices]
            big = max(max(v[i] for v in xs) - min(v[i] for v in xs) for i in range(3)) > .25 * max(size)
            if big and t <= 64: continue          # large simple sheets (water, boards) carry the outline: one collapse makes a spike
            if t > tg: add_decimate(x, tg / t)
        for x in bpy.context.view_layer.objects: x.select_set(x in isl)
        bpy.context.view_layer.objects.active = isl[0]
        bpy.ops.object.convert(target='MESH')
        bpy.ops.object.join()
        o = bpy.context.view_layer.objects.active; o.name = name; o.data.name = name
        assert o.name == name, (o.name, name)
    elif bmesh_tri > target:
        add_decimate(o, target / bmesh_tri)
        bpy.context.view_layer.objects.active = o
        for x in bpy.context.view_layer.objects: x.select_set(x == o)
        bpy.ops.object.modifier_apply(modifier='dec')
    for g in list(o.vertex_groups):
        if g.name == 'decim_free': o.vertex_groups.remove(g)
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=.0001)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(o.data); bm.free()
    # collapsed curved parts (tiles, posts, jars) get hard facets that read as dark stripes: smooth by angle, keep marked sharp edges
    bpy.context.view_layer.objects.active = o
    for x in bpy.context.view_layer.objects: x.select_set(x == o)
    if o.data.has_custom_normals and cfg.get('recompute_normals'):   # B12: LOD0's custom normals no longer fit the reduced faces (stones went dark)
        bpy.ops.mesh.customdata_custom_splitnormals_clear()
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35), keep_sharp_edges=True)
    return o


lods = {'LOD0': [main0, det0]}
lods['LOD1'] = [make_lod(main0, f'{AID}_LOD1', .5, 1.), make_lod(det0, f'{AID}_Detail_Small_LOD1', .5, 1.)]
lods['LOD2'] = [make_lod(main0, f'{AID}_LOD2', .15, 4.), make_lod(det0, f'{AID}_Detail_Small_LOD2', .15, 4.)]
for o in (main0, det0):
    if o is None: continue
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.to_mesh(o.data); bm.free()   # same tris, explicit

root_e = bpy.data.objects.new(f'{AID}_ROOT', None); work.objects.link(root_e)
for lv in lods.values():
    for o in lv:
        if o: o.parent = root_e

# ------------------------------------------------------------------ export + info
objs = [o for lv in lods.values() for o in lv if o]
for x in bpy.context.view_layer.objects: x.select_set(x in objs or x == root_e)
fbx = os.path.join(out_dir, f'{AID}_LOD_v001.fbx')
bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS',
                         axis_forward='-Z', axis_up='Y', mesh_smooth_type='FACE', use_mesh_modifiers=True, add_leaf_bones=False,
                         path_mode='COPY', embed_textures=False, bake_anim=False, object_types={'EMPTY', 'MESH'})
blend = os.path.join(out_dir, f'{AID}_LOD_v001.blend')
bpy.ops.wm.save_as_mainfile(filepath=blend, copy=True)

mats = sorted({s.material.name for o in objs for s in o.material_slots if s.material})
imgs = {}
for m in bpy.data.materials:
    if m.name in mats and m.use_nodes:
        for n in m.node_tree.nodes:
            if n.type == 'TEX_IMAGE' and n.image: imgs[n.image.name] = list(n.image.size)
info = {
    'asset': AID, 'version': 'v001', 'source': cfg['src'], 'source_root': cfg.get('root'),
    'source_unchanged': True, 'note': cfg.get('note', ''),
    'lod0_rule': 'LOD0 = source geometry unchanged (modifiers applied, world transforms baked, recentred only)',
    'recentre_offset_m': [round(v, 4) for v in offset], 'dimensions_m': [round(v, 4) for v in size],
    'source_triangles': src_tris,
    # zero-area triangles already in the source LOD0 (kept, LOD0 is not edited); Unity drops them on import
    'lod0_zero_area_triangles': sum(sum(1 for p in o.data.polygons if p.area < 1e-10) for o in lods['LOD0'] if o),
    'budget_per_lod': {k: {'triangles': sum(tris(o) for o in v if o), 'triangles_without_detail': tris(v[0]),
                           'objects': sum(1 for o in v if o), 'objects_without_detail': 1,
                           'materials': len({s.material.name for o in v if o for s in o.material_slots if s.material})} for k, v in lods.items()},
    'detail_parts': len(detail), 'body_parts': len(body), 'detail_rule': f"part bounding box under min({dmax} m, {cfg.get('detail_rel', .12)} x asset size) (plus listed names / collections)",
    'minTier': cfg.get('min_tier', 'standard'), 'detailObjects': [f'{AID}_Detail_Small'] if det0 else [],
    'materials': mats, 'texture_resolution_px': imgs,
    'lod_rule': 'LOD1 about 50 %, LOD2 about 15 % of LOD0: limited dissolve of flat faces (material/UV/sharp kept), then collapse',
    'lod_method': {k: cfg[k] for k in ('lod_per_island', 'island_floor', 'island_min_ratio', 'protect_borders', 'protect_min_tris',
                                       'protect_crease_deg', 'recompute_normals', 'detail_closed_only', 'split_loose', 'only_lod0') if k in cfg},
    'fbx': os.path.basename(fbx), 'units': 'meters', 'front': '-Y (Blender)',
}
json.dump(info, open(os.path.join(out_dir, 'model_info.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('LODINFO', AID, json.dumps(info['budget_per_lod']), 'detail', len(detail), 'body', len(body), 'mats', len(mats), 'imgs', len(imgs), flush=True)
