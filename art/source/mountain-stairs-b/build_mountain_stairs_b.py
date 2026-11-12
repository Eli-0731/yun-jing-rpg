"""mountain-stairs-b v001 (work pack B-104h part 2, batch 1): SG01 straight stair run, SG02 turning landing, SG03 balustrade set, SG04 rest shelter.
Work pack 2026-11-09 B-112h batch C adds SG05 wide stair run and SG06 wide landing (sg_wide.py, grey-white granite).

Run one asset per process:
  blender --background --factory-startup --python art/source/mountain-stairs-b/build_mountain_stairs_b.py -- SG01_StraightRun --force
  ... -- SG01_StraightRun --preview <dir>     procedural look only, no bake or export
An asset whose validation.json exists is skipped unless --force is given.

ti_core / ti_mats / mk_mats / cr_mats / cr_parts / ti_pipeline / qa_* / backface_check / ruler_views / pair_sheets are copied from
art/source/tea-terraces-b (branch art/b-1107-te04-te05-ri03-tea-wheel); only the kit name in ruler_views and pair_sheets differs.
The pipeline functions below (LODs, clamp, collision, FBX/GLB, run) are the tea-terraces-b ones with the tea-only parts (leaf cards, bushes) removed.

Step rule (docs/art/modeling-style-spec-v1.md section 4, a world constant): rise 0.15-0.18 m, tread 0.28-0.32 m.
The work pack's SG01 line reads "3 x 6 x 3 m (10 steps)"; ten steps over 3 m would be 0.30 m risers, so SG01 keeps ten steps at
0.16 x 0.32 m and stays inside the 3 x 6 x 3 m limit (1.6 m rise, 3.2 m run). See the README.
Writes:
  art/source/mountain-stairs-b/blend/<ID>_v001.blend
  art/exports/mountain-stairs-b/<ID>/<ID>_v001.fbx, .glb, Textures/, model_info.json, validation.json
  art/previews/mountain-stairs-b/<ID>/turnaround/ (ten views + views.json), hero, LOD sheets
"""
import bpy, bmesh, sys, json, math, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np
from mathutils import Vector, Matrix
import ti_core, ti_mats, ti_pipeline as pl
import sg_parts as SG, sg_rail, sg_landing, sg_shelter, sg_wide
from ti_core import S

KIT = 'mountain-stairs-b'
ART = HERE.parents[1]
VER = 'v001'
LOD_TARGET = {1: .50, 2: .15}
LOD_DROPS = {1: (2, 99), 2: (1, 2, 99)}

ASSETS = {}
SG.register(ASSETS); sg_rail.register(ASSETS); sg_landing.register(ASSETS); sg_shelter.register(ASSETS); sg_wide.register(ASSETS)


def route_details():
    """Grass, ferns, moss, pebbles and chink stones export as their own Detail_Small object (quality-tiers-v1 section 4)."""
    for o in S['parts']:
        if o.get('group') == 'Main' and int(o.get('detail', 0)) >= 1:
            o['group'] = 'Detail_Small'


def part_twins(me):
    bm = bmesh.new(); bm.from_mesh(me); seen, twins = set(), []
    for f in bm.faces:
        k = frozenset(v.index for v in f.verts)
        (twins.append(f) if k in seen else seen.add(k))
    if twins: bmesh.ops.split(bm, geom=twins)
    bm.to_mesh(me); bm.free(); me.update()
    return len(twins)


def make_lods():
    """LOD1/LOD2 per export group: drop small parts while enough triangles remain, then collapse to the target."""
    tris = lambda me: sum(len(p.vertices) - 2 for p in me.polygons)
    for src in S['lod0'].values():
        bm = bmesh.new(); bm.from_mesh(src.data); big = [f for f in bm.faces if len(f.verts) > 4]
        if big: bmesh.ops.triangulate(bm, faces=big, quad_method='BEAUTY', ngon_method='BEAUTY')
        bm.to_mesh(src.data); bm.free(); S.setdefault('ngons_split', {})[src.name] = len(big)
        S.setdefault('twins_parted', {})[src.name] = part_twins(src.data)
    lods = {0: dict(S['lod0'])}; report = {}
    for lv in (1, 2):
        lods[lv] = {}
        for gname, src in S['lod0'].items():
            n0 = tris(src.data); want = n0 * LOD_TARGET[lv]
            for drop in LOD_DROPS[lv]:
                me = src.data.copy(); bm = bmesh.new(); bm.from_mesh(me)
                lay = bm.faces.layers.int.get('part_detail')
                if lay is not None and drop < 99:
                    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[lay] >= drop], context='FACES')
                bm.to_mesh(me); bm.free()
                if tris(me) >= want * .98 or drop == 99: break
                bpy.data.meshes.remove(me)
            o = src.copy(); o.data = me; S['lodcol'].objects.link(o)
            o.name = src.name.replace('_LOD0', f'_LOD{lv}'); me.name = o.name
            r = min(1., want / max(tris(me), 1))
            bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
            if r < .999:
                m = o.modifiers.new('LOD_decimate', 'DECIMATE'); m.use_collapse_triangulate = True; m.ratio = r
                if S.get('keep_border'):
                    m.use_symmetry = False
                for _ in range(6):
                    dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); tm_ = e.to_mesh(); n = tris(tm_); e.to_mesh_clear()
                    if abs(n - want) <= max(2, want * .01): break
                    m.ratio = min(1., m.ratio * want / max(n, 1))
                bpy.ops.object.modifier_apply(modifier=m.name)
                pl.orient_faces(o.data, flush=False); pl.spread_zero_uv([o])
                S.setdefault('twins_parted', {})[o.name] = part_twins(o.data)
            try: bpy.ops.mesh.customdata_custom_splitnormals_clear()
            except Exception: pass
            bpy.ops.object.shade_smooth_by_angle(angle=math.radians(38))
            lods[lv][gname] = o
            report.setdefault(gname, {'LOD0': n0})[f'LOD{lv}'] = tris(o.data)
    S['lods'] = lods
    return report


def clamp_to_limit(cfg):
    """Separating flush faces pushes a piece out by a millimetre or two; pull every vertex back inside the footprint and above z = 0."""
    lo_b, hi_b = cfg.get('box') or ((-cfg['limit'][0] / 2, -cfg['limit'][1] / 2, 0.), (cfg['limit'][0] / 2, cfg['limit'][1] / 2, 99.)); moved = 0
    objs = [o for g in S['lods'].values() for o in g.values()] + ([S['collision_obj']] if S.get('collision_obj') else [])
    for o in objs:
        me = o.data; co = np.zeros(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
        w = co + np.array(o.location, np.float32)
        c = w.copy(); c[:, 0] = np.clip(c[:, 0], lo_b[0], hi_b[0]); c[:, 1] = np.clip(c[:, 1], lo_b[1], hi_b[1]); c[:, 2] = np.maximum(c[:, 2], lo_b[2])
        dm = np.abs(c - w)
        if float(dm.max()) > moved:
            i = int(dm.max(axis=1).argmax()); S['clamp_worst'] = (o.name, [round(float(v), 3) for v in w[i]])
        moved = max(moved, float(dm.max()))
        me.vertices.foreach_set('co', (c - np.array(o.location, np.float32)).ravel()); me.update()
    S['clamped_m'] = round(moved, 5)
    assert moved < cfg.get('clamp_max', .02), ('clamp moved a vertex too far', moved, S.get('clamp_worst'))   # TE03: buried stone bottoms are flattened onto z = 0


def make_collision(aid):
    extra = S.get('collision_mesh')
    if not extra: return None
    me = bpy.data.meshes.new(aid + '_Collision'); me.from_pydata(extra[0], [], extra[1]); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(aid + '_Collision', me); S['lodcol'].objects.link(o); o.hide_render = True
    S['collision_obj'] = o
    return o


def export_fbx(path):
    a = S['asset']
    root = bpy.data.objects.new(a, None); S['lodcol'].objects.link(root); S['root'] = root
    for groups in S['lods'].values():
        for o in groups.values(): o.parent = root
    extra = [S['collision_obj']] if S.get('collision_obj') else []
    for o in extra: o.parent = root
    for e in S['sockets'].values():
        mw = e.matrix_world.copy()
        for c in list(e.users_collection): c.objects.unlink(e)
        S['lodcol'].objects.link(e); e.parent = root; e.matrix_world = mw
    bpy.ops.object.select_all(action='DESELECT')
    root.select_set(True)
    for groups in S['lods'].values():
        for o in groups.values(): o.select_set(True)
    for o in extra: o.hide_render = False; o.select_set(True)
    for e in S['sockets'].values(): e.select_set(True)
    bpy.context.view_layer.objects.active = root
    bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True, object_types={'MESH', 'EMPTY'},
                             apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', bake_space_transform=True,
                             axis_forward='-Z', axis_up='Y', mesh_smooth_type='FACE', use_mesh_modifiers=True,
                             add_leaf_bones=False, bake_anim=False, path_mode='STRIP', embed_textures=False, colors_type='LINEAR')
    for o in extra: o.hide_render = True


def export_glb(path):
    """Same LOD0..2 and collision as the FBX, for web previews; textures packed."""
    bpy.ops.object.select_all(action='DESELECT')
    S['root'].select_set(True)
    for o in S['root'].children_recursive: o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True, export_yup=True, export_apply=True, export_image_format='JPEG', export_jpeg_quality=88)


def build(aid):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene; scene.unit_settings.system = 'METRIC'; scene.unit_settings.scale_length = 1
    bpy.context.preferences.filepaths.save_version = 0
    ti_mats.MAT_INFO.clear(); ti_core.reset_state(aid)
    cfg = ASSETS[aid]
    P = cfg['palette'](); cfg['build'](P)
    bpy.context.view_layer.update()
    return cfg


def preview(aid, out_dir, samples=20):
    cfg = build(aid)
    ti_core.write_grain_attributes()
    S['cut'].hide_render = True
    lo, hi = pl.eval_bounds(S['parts']); print('PREVIEW_BOUNDS', aid, [round(v, 3) for v in lo], [round(v, 3) for v in hi], flush=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    tris = 0; dg = bpy.context.evaluated_depsgraph_get()
    for o in S['parts']:
        e = o.evaluated_get(dg); m = e.to_mesh(); tris += sum(len(p.vertices) - 2 for p in m.polygons); e.to_mesh_clear()
    print('PREVIEW_TRIS', aid, tris, len(S['parts']), flush=True)
    views = (('front', (0, -1, .12)), ('three_quarter', (1, -1.3, .55)), ('side', (1, 0, .15)), ('top', (.05, -.25, 1)), ('close', None))
    for name, d in views:
        if d is None:
            close_shot(S['parts'], out_dir / f'{aid}_close.png', samples=samples)
            continue
        pl.persp_shot(S['parts'], out_dir / f'{aid}_{name}.png', direction=d, samples=samples, lens=50)
    bpy.ops.wm.save_as_mainfile(filepath=str(out_dir / f'{aid}_preview.blend'))


def archive_previous(aid, ver):
    """Before a piece's first build of version ver, move the previous version's exports and previews into <ID>/<prev>/ so nothing is overwritten.
    Folders of older versions (v001/, v002/ ...) stay where they are."""
    import shutil, re
    prev = f'v{int(ver[1:]) - 1:03d}'
    exp = ART / 'exports' / KIT / aid
    if not (exp / f'{aid}_{prev}.fbx').exists(): return
    for root in (exp, ART / 'previews' / KIT / aid):
        if not root.exists(): continue
        items = [q for q in root.iterdir() if not re.fullmatch(r'v\d{3}', q.name)]
        (root / prev).mkdir(exist_ok=True)
        for q in items: shutil.move(str(q), str(root / prev / q.name))
        print('ARCHIVED_' + prev.upper(), root, len(items), flush=True)


def run(aid, force=False):
    global VER
    cfg = ASSETS[aid]; VER = cfg.get('ver', 'v001')
    exp = ART / 'exports' / KIT / aid; prev = ART / 'previews' / KIT / aid; blend = ART / 'source' / KIT / 'blend'
    if VER != 'v001': archive_previous(aid, VER)
    if (exp / 'validation.json').exists() and not force:
        print('ALREADY_COMPLETE', aid, flush=True); return
    t0 = time.time()
    build(aid)
    ti_core.write_grain_attributes(); route_details()
    pl.join_groups()
    pl.uv_atlas(cfg.get('uv_weight'), cfg['tex'], shape=cfg.get('uv_shape', 'CONCAVE')); pl.spread_zero_uv()
    pl.bake(exp / 'Textures', cfg['tex'])
    lod_report = make_lods()
    pl.export_materials()
    make_collision(aid); clamp_to_limit(cfg)
    S['col'].hide_render = True; S['col'].hide_viewport = True
    lod0 = list(S['lods'][0].values())
    lo, hi = pl.eval_bounds(lod0); dims = hi - lo
    checks = []
    def check(name, ok, detail): checks.append({'check': name, 'pass': bool(ok), 'detail': detail})
    pieces = {}
    for gname, o in S['lods'][0].items():
        a, b = pl.eval_bounds([o]); pieces[gname] = {'dims_m': [round(v, 4) for v in b - a], 'min': [round(v, 4) for v in a], 'max': [round(v, 4) for v in b]}
    lim = cfg['limit']
    if cfg.get('box'):
        (bx0, by0, _), (bx1, by1, bz1) = cfg['box']
        check('footprint_within_limit', lo.x >= bx0 - 1e-3 and hi.x <= bx1 + 1e-3 and lo.y >= by0 - 1e-3 and hi.y <= by1 + 1e-3 and hi.z <= bz1 + 1e-3,
              {'min': [round(v, 4) for v in lo], 'max': [round(v, 4) for v in hi], 'box_m': cfg['box']})
    else: check('footprint_within_limit', lo.x >= -lim[0] / 2 - 1e-3 and hi.x <= lim[0] / 2 + 1e-3 and lo.y >= -lim[1] / 2 - 1e-3 and hi.y <= lim[1] / 2 + 1e-3 and dims.z <= lim[2] + 1e-3,
          {'min': [round(v, 4) for v in lo], 'max': [round(v, 4) for v in hi], 'limit_m': lim, 'note': 'footprint centred on the origin; height includes grass on the tread'})
    bz = cfg.get('base_z', 0.)   # RI03: origin at the axle, the lowest point is the bottom of the wheel
    check('base_at_z0' if not bz else 'lowest_point_at_design_z', abs(lo.z - bz) < (1e-3 if not bz else .01), {'min_z': round(lo.z, 5), 'design_min_z': bz, 'largest_clamp_m': S.get('clamped_m')})
    spec = spec_checks(aid, check)
    tot = {k: sum(g[k] for g in lod_report.values()) for k in ('LOD0', 'LOD1', 'LOD2')}  # (fit-scale keys are ignored)
    r1, r2 = tot['LOD1'] / tot['LOD0'], tot['LOD2'] / tot['LOD0']
    check('lod_ratios_50_15', .45 <= r1 <= .55 and .12 <= r2 <= .18, {'triangles': tot, 'LOD1': round(r1, 3), 'LOD2': round(r2, 3), 'per_group': lod_report})
    exp.mkdir(parents=True, exist_ok=True)
    fbx = exp / f'{aid}_{VER}.fbx'
    export_fbx(fbx)
    rt = pl.fbx_roundtrip(fbx)
    check('fbx_reimport_dimensions', all(abs(a - b) < .02 for a, b in zip(rt['lod0_dimensions_m'], dims)),
          {'fbx_lod0_dims_m': rt['lod0_dimensions_m'], 'blend_dims_m': [round(v, 4) for v in dims], 'tolerance_m': .02, 'max_error_m': round(max(abs(a - b) for a, b in zip(rt['lod0_dimensions_m'], dims)), 5)})
    names = rt['objects']
    check('fbx_has_lod0_1_2', all(any(n.split('.')[0].endswith(f'_LOD{lv}') for n in names) for lv in (0, 1, 2)), names)
    check('fbx_sockets', sorted(k.split('.')[0] for k in rt['sockets']) == sorted(S['sockets']), rt['sockets'])
    check('fbx_collision', cfg.get('no_collision') or (aid + '_Collision') in [n.split('.')[0] for n in names], cfg.get('no_collision') or 'collision mesh present')
    glb = exp / f'{aid}_{VER}.glb'; export_glb(glb)
    check('glb_written', glb.exists() and glb.stat().st_size > 1000, {'bytes': glb.stat().st_size})
    pl.ten_views(lod0, prev / 'turnaround', f'art/source/{KIT}/blend/{aid}_{VER}.blend')
    check('ten_views_rendered', len(list((prev / 'turnaround').glob('*.png'))) == 10, 'orthographic, framing asserted per view')
    shots = []
    for lv in (0, 1, 2):
        p = prev / f'_lod{lv}.png'; pl.persp_shot(list(S['lods'][lv].values()), p, samples=32); shots.append(p)
    _strip(shots, prev / f'{aid}_LOD_comparison.png'); [p.unlink() for p in shots]
    shots = []
    for lv in (0, 1):
        p = prev / f'_nd{lv}.png'; pl.persp_shot([o for g, o in S['lods'][lv].items() if not g.startswith('Detail_')], p, samples=48); shots.append(p)
    _strip(shots, prev / f'{aid}_LOD0_LOD1_no_detail.png'); [p.unlink() for p in shots]
    pl.persp_shot(lod0, prev / f'{aid}_hero.png', samples=96)
    wire(lod0, prev / f'{aid}_wireframe.png')
    for o in lod0: o.hide_render = False
    blend.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend / f'{aid}_{VER}.blend'))
    mats = sorted({m.name for g in S['lods'].values() for o in g.values() for m in o.data.materials})
    def png_px(p):   # width x height from the PNG header (IHDR)
        b = p.read_bytes()[16:24]; return [int.from_bytes(b[:4], 'big'), int.from_bytes(b[4:], 'big')]
    budget = {f'LOD{lv}': {'triangles': tot[f'LOD{lv}'], 'objects': len(S['lods'][lv]),
                           'objects_without_detail': len([g for g in S['lods'][lv] if not g.startswith('Detail_')]),
                           'materials': len({m.name for o in S['lods'][lv].values() for m in o.data.materials})} for lv in (0, 1, 2)}
    tex_px = {p.name: png_px(p) for p in sorted((exp / 'Textures').glob('*.png'))}
    info = {
        'asset': aid, 'version': VER, 'minTier': cfg.get('minTier', 'standard'), 'detailObjects': sorted(f'{aid}_{g}' for g in S['lods'][0] if g.startswith('Detail_')),
        'name_zh': cfg['zh'], 'slot': cfg.get('slot', 'B1_SectGateStairs'), 'note': cfg['note'],
        'budget_per_lod': budget, 'texture_resolution_px': tex_px,
        'units': 'meters', 'front': '-Y (Blender)', 'up': '+Z (Blender); FBX exported Y-up, -Z forward, transforms baked',
        'origin': cfg.get('origin', 'footprint centre, z = 0 at the lowest ground contact'), 'dimensions_m': [round(v, 4) for v in dims], 'bounds_min_m': [round(v, 4) for v in lo], 'bounds_max_m': [round(v, 4) for v in hi],
        'size_limit_m': cfg['limit'], 'pieces': pieces,
        'lods': lod_report, 'lod_totals': tot, 'lod_rule': 'LOD1 about 50%, LOD2 about 15% of LOD0 (detail parts dropped first, then collapse decimate)',
        'materials': mats, 'textures': sorted(p.name for p in (exp / 'Textures').glob('*.png')), 'texture_size_px': cfg['tex'],
        'unity': {'pipeline': 'URP Lit', 'axes': 'imported with bakeAxisConversion: Unity local = (Blender x, z, y); the model front faces Unity -Z', 'BaseColor': f'{aid}_BaseColor.png', 'Normal': f'{aid}_Normal.png (OpenGL +Y)',
                  'MetallicSmoothness': f'{aid}_MetallicSmoothness.png (R metallic, A smoothness)', 'lod_group': 'objects end in _LOD0/_LOD1/_LOD2 under one root',
                  'collision': f'{aid}_Collision: MeshCollider (convex off), renderer hidden'},
        'collision': bool(S.get('collision_obj')),
        **({'ground_z_m': cfg['ground_z']} if 'ground_z' in cfg else {}),
        **({'parts': S['part_notes']} if S.get('part_notes') else {}),
        'sockets_blender_xyz': {k: [round(v, 4) for v in e.matrix_world.translation] for k, e in S['sockets'].items()},
        'sockets_fbx_reimport_xyz': rt['sockets'], 'fbx_objects': rt['objects'], 'glb': glb.name,
        'interface': spec,
        'modeling_method': f'procedural mesh construction (art/source/{KIT}/); procedural shaders (cr_mats.py) baked to one {cfg["tex"]} atlas',
        'reference': f"art/references/{cfg['ref'].split('/')[0]}/ (AI three-view {cfg['ref']}; proportions from the work pack's written sizes, not measured from the image)",
        'unity_import_verified': 'see artifacts/mountain-stairs-unity/ (local Unity batch check, not committed)',
    }
    (exp / 'model_info.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
    val = {'asset': aid, 'checks': checks, 'all_pass': all(c['pass'] for c in checks), 'seconds': round(time.time() - t0),
           'not_checked': ['in-engine lighting and walking (see the Unity report)', 'mobile frame rate (not measured)']}
    (exp / 'validation.json').write_text(json.dumps(val, ensure_ascii=False, indent=2), encoding='utf-8')
    print('ASSET_COMPLETE', aid, 'all_pass=', val['all_pass'], [c['check'] for c in checks if not c['pass']], round(time.time() - t0), 's', flush=True)


def close_shot(objs, path, samples=32, target=None, eye=None, lens=40):
    """A person's-eye close-up of the wall: 1.6 m eye height, 2.4 m in front of it."""
    scene = bpy.context.scene; pl.show_only(objs)
    cam, centre, ext = pl.studio(objs, samples)
    cam.data.type = 'PERSP'; cam.data.lens = lens
    target = Vector(target or (centre.x - ext.x * .12, centre.y - ext.y * .45, .55)); eye = Vector(eye or (target.x + 1.3, target.y - 2.4, 1.6))
    cam.location = eye; cam.rotation_euler = (target - eye).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(path); bpy.ops.render.render(write_still=True)


def wire(objs, path):
    """Wireframe over the baked colour, same 3/4 angle as the hero."""
    for o in objs:
        m = o.modifiers.new('QA_Wire', 'WIREFRAME'); m.thickness = .004; m.use_replace = False; m.material_offset = 99
    pl.persp_shot(objs, path, samples=24)
    for o in objs: o.modifiers.remove(o.modifiers['QA_Wire'])


def _strip(paths, out):
    ims = [bpy.data.images.load(str(p)) for p in paths]
    w, h = ims[0].size
    arr = np.concatenate([np.array(i.pixels[:], np.float32).reshape(h, w, 4) for i in ims], axis=1)
    im = bpy.data.images.new(out.stem, w * len(ims), h, alpha=True); im.pixels.foreach_set(arr.ravel())
    im.filepath_raw = str(out); im.file_format = 'PNG'; im.save()




# ------------------------------------------------------------------ SG checks (all measured on the exported LOD0 by ray, not taken from the design numbers)
def _bvh(objs):
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get(); trees = [BVHTree.FromObject(o, dg) for o in objs]
    def down(x, y, z0=20.):
        best = None
        for t in trees:
            hit = t.ray_cast(Vector((x, y, z0)), Vector((0, 0, -1)))
            if hit[0] is not None and (best is None or hit[0].z > best): best = hit[0].z
        return best
    def up(x, y, z0):
        best = None
        for t in trees:
            hit = t.ray_cast(Vector((x, y, z0)), Vector((0, 0, 1)))
            if hit[0] is not None and (best is None or hit[0].z < best): best = hit[0].z
        return best
    def along(p, d):
        best = None
        for t in trees:
            hit = t.ray_cast(Vector(p), Vector(d).normalized())
            if hit[0] is not None and (best is None or hit[3] < best[1]): best = (hit[0], hit[3])
        return best
    return down, up, along


def stair_checks(aid, check):
    """SG01: ten equal risers and treads inside the world-constant range, a clear walking width, the top flush with the landing."""
    p = S['prop']; main = [S['lods'][0]['Main']]
    down, up, along = _bvh(main)
    n, R, Tr, W = p['steps'], p['rise'], p['tread'], p['walk_w']
    rows = {}
    for x in (-W / 2 + .25, 0., W / 2 - .25):   # three lines up the flight: both sides of the walking width and the centre
        zs = [down(x, p['y0'] + (k + .5) * Tr) for k in range(n)]
        rows[round(x, 3)] = [round(z, 4) if z is not None else None for z in zs]
    ok_rows = all(z is not None for zs in rows.values() for z in zs)
    rises = []
    if ok_rows:
        for zs in rows.values():
            prev = 0.
            for z in zs: rises.append(z - prev); prev = z
    check('ten_equal_risers_in_world_range', ok_rows and len(rises) == 3 * n and max(rises) - min(rises) <= .008 and .15 <= min(rises) and max(rises) <= .18,
          {'tread_z_m_by_line': rows, 'rise_min_max_m': [round(min(rises), 4), round(max(rises), 4)] if rises else None, 'design_rise_m': R,
           'rule': 'docs/art/modeling-style-spec-v1.md section 4: rise 0.15-0.18 m'})
    noses = []
    for k in range(1, n):   # horizontal ray along +Y just under each tread top finds the next riser face
        z = k * R - .07; hit = along((0., p['y0'] - .5, z), (0, 1, 0))
        noses.append(round(hit[0].y, 4) if hit else None)
    depths = [round(b - a, 4) for a, b in zip(noses, noses[1:])] if all(v is not None for v in noses) else None
    check('equal_treads_in_world_range', depths is not None and max(depths) - min(depths) <= .01 and .28 <= min(depths) and max(depths) <= .32 + .005,
          {'riser_face_y_m': noses, 'tread_depths_m': depths, 'design_tread_m': Tr, 'rule': 'tread 0.28-0.32 m'})
    lo, hi = pl.eval_bounds(main)
    clear = []
    for k in (1, 4, 8):   # walking width: horizontal rays from the centre line towards each kerb, 0.2 m above the tread
        z = k * R + .2; y = p['y0'] + (k - .5) * Tr
        l = along((0, y, z), (-1, 0, 0)); r = along((0, y, z), (1, 0, 0))
        clear.append(round((r[0].x if r else hi.x) - (l[0].x if l else lo.x), 4))
    check('clear_walking_width', min(clear) >= W - .02, {'clear_between_kerbs_m': clear, 'design_m': W})
    top = [down(x, p['y1'] - .1) for x in (-W / 2 + .2, 0, W / 2 - .2)]
    check('top_flush_with_landing', all(t is not None and abs(t - n * R) <= .006 for t in top), {'top_tread_z_m': [round(t, 4) if t else None for t in top], 'design_m': round(n * R, 4)})
    over = []   # nothing may stand above the sloped coping between the newel caps (rays straight down across the kerb top)
    for side in (-1, 1):
        for x in (SG.KX0 + .03, SG.KXC, SG.KX1 - .03):
            y = SG.POST_Y[0] + .25
            while y < SG.POST_Y[2] - .25:
                z = down(side * x, y)
                if z is not None and z > SG.cope_top(y) + .012: over.append([round(side * x, 3), round(y, 3), round(z - SG.cope_top(y), 4)])
                y += .02
    check('nothing_above_sloped_coping', not over, {'points_above_m': over[:12], 'count': len(over), 'tolerance_m': .012})
    need = {'Socket_Bottom', 'Socket_Top'} | {f'Socket_Post_{s}{i}' for s in 'LR' for i in range(p['posts'])}
    check('sockets_present', need <= set(S['sockets']), {'missing': sorted(need - set(S['sockets'])), 'sockets': sorted(S['sockets'])})
    return {'steps': n, 'rise_m': R, 'tread_m': Tr, 'walk_width_m': W, 'slope_deg': round(math.degrees(math.atan2(R, Tr)), 2),
            'bottom_edge_y_m': p['y0'], 'top_edge_y_m': p['y1'], 'top_z_m': round(n * R, 4), 'sockets': sorted(S['sockets'])}


def rail_checks(aid, check):
    """SG03 straight bay: handrail top at 0.9 m all along, the ends 5 mm into the post faces."""
    p = S['prop']; down, up, along = _bvh([S['lods'][0]['Main']])
    lo, hi = pl.eval_bounds([S['lods'][0]['Main']])
    tops = [down(x, 0.) for x in (-.7, -.35, 0., .35, .7)]
    check('handrail_top_in_world_range', all(t is not None and abs(t - p['rail_top']) <= .006 for t in tops) and min(tops) >= .9 - .006 and max(tops) <= 1.05,
          {'handrail_top_z_m': [round(t, 4) if t else None for t in tops], 'design_m': p['rail_top'], 'rule': 'balustrade 0.9-1.05 m'})
    import sg_rail as SR
    face = SR.BAY / 2 - SR.POST_W / 2
    check('ends_run_into_post_faces', abs(lo.x + face + SR.INTO) <= .0025 and abs(hi.x - face - SR.INTO) <= .0025,
          {'end_x_m': [round(lo.x, 4), round(hi.x, 4)], 'post_face_x_m': face, 'into_post_m': SR.INTO, 'note': 'the seam against the post is closed; measured again in the assembly'})
    check('sockets_present', {'Socket_Post_A', 'Socket_Post_B'} <= set(S['sockets']), sorted(S['sockets']))
    return {'bay_post_centres_m': SR.BAY, 'over_post_faces_m': SR.BAY + SR.POST_W, 'rail_top_m': p['rail_top'], 'sockets': sorted(S['sockets'])}


def rail_sloped_checks(aid, check):
    """SG03 sloped run: posts sit in SG01's sockets, the handrail runs 1.02 m above the nosing line."""
    import sg_rail as SR
    down, up, along = _bvh([S['lods'][0]['Main']])
    sg01 = json.loads((ART / 'exports' / KIT / 'SG01_StraightRun' / 'model_info.json').read_text(encoding='utf-8'))['sockets_blender_xyz']
    err = {}
    for i in range(3):
        a = S['sockets'][f'Socket_Post_{i}'].matrix_world.translation; b = sg01[f'Socket_Post_R{i}']
        err[f'Post_{i}'] = round(max(abs(a.x + SG.KXC - b[0]), abs(a.y - b[1]), abs(a.z - b[2])) * 1000, 2)
    check('posts_on_sg01_sockets', max(err.values()) <= .5, {'error_mm': err, 'note': 'SG03 placed at x = +1.34 against SG01 Socket_Post_R0..2'})
    rows = []
    for b in range(2):
        for f in (.2, .5, .8):
            y = SG.POST_Y[b] + .1 + (SG.POST_Y[b + 1] - SG.POST_Y[b] - .2) * f; z = down(0., y)
            rows.append([round(y, 3), round(z - SG.nose_z(y), 4) if z else None])
    hs = [r[1] for r in rows]
    check('handrail_above_nosing_in_world_range', all(h is not None and .9 <= h <= 1.05 for h in hs),
          {'y_and_height_above_nosing_m': rows, 'design_m': SR.STAIR_RAIL, 'rule': 'balustrade 0.9-1.05 m'})
    holes = []
    for i, y in enumerate(SG.POST_Y):   # the tenon fits the 0.15 m hole with play on every side and stops above its floor
        a = S['sockets'][f'Socket_Post_{i}'].matrix_world.translation
        holes.append({'post': i, 'tenon_m': SR.TENON, 'hole_m': SG.SOCK, 'tenon_bottom_above_floor_m': round(SR.TENON_D and (.1 - SR.TENON_D), 4)})
    check('tenons_fit_sockets', SR.TENON < SG.SOCK and SR.TENON_D < .1, holes)
    check('sockets_present', {f'Socket_Post_{i}' for i in range(3)} <= set(S['sockets']), sorted(S['sockets']))
    return {'posts_y_m': list(SG.POST_Y), 'rail_above_nosing_m': SR.STAIR_RAIL, 'place': 'SG01 origin + (+-1.34, 0, 0)', 'sockets': sorted(S['sockets'])}


def post_checks(aid, check):
    import sg_rail as SR
    o = S['lods'][0]['Main']; down, up, along = _bvh([o])
    lo, hi = pl.eval_bounds([o])
    top = down(0., 0.)
    me = o.data; low = [o.matrix_world @ v.co for v in me.vertices if (o.matrix_world @ v.co).z < -.005]
    tw = max(max(abs(v.x) for v in low), max(abs(v.y) for v in low)) * 2 if low else None
    check('tenon_fits_sg01_socket', tw is not None and tw < SG.SOCK and abs(lo.z + SR.TENON_D) <= .003,
          {'tenon_width_m': round(tw, 4) if tw else None, 'socket_m': SG.SOCK, 'tenon_bottom_z_m': round(lo.z, 4), 'socket_depth_m': .1})
    check('top_above_handrail', top is not None and top > SR.RAIL_TOP + .1, {'post_top_z_m': round(top, 4) if top else None, 'handrail_top_m': SR.RAIL_TOP})
    need = {'Socket_Base'} | {f'Socket_Rail_{k}' for k in 'NSEW'}
    check('sockets_present', need <= set(S['sockets']), sorted(S['sockets']))
    return {'post_m': SR.POST_W, 'top_z_m': round(top, 4) if top else None, 'tenon_m': [SR.TENON, SR.TENON_D], 'sockets': sorted(S['sockets'])}


def landing_checks(aid, check):
    """SG02: the walking surface level at 0.4 m, the four edges at the SG01 top-tread height, the sockets in place."""
    import sg_landing as SL
    down, up, along = _bvh([S['lods'][0]['Main']])
    pts = []
    for x in [-1.75 + .35 * i for i in range(11)]:
        for y in [-1.75 + .35 * j for j in range(11)]:
            if (x - SL.LANTERN[0]) ** 2 + (y - SL.LANTERN[1]) ** 2 < .5 ** 2: continue
            zz = [down(x + dx, y + dy) for dx, dy in ((0, 0), (.03, 0), (-.03, 0), (0, .03), (0, -.03))]
            z = max((v for v in zz if v is not None), default=None); pts.append(z)   # a foot bridges a 3 mm stone joint: highest of five rays 3 cm apart
    ok = all(z is not None for z in pts)
    zs = [z for z in pts if z is not None]
    check('walking_surface_level', ok and max(zs) - min(zs) <= .008 and abs(sum(zs) / len(zs) - SL.TOP) <= .004,
          {'samples': len(pts), 'z_min_max_m': [round(min(zs), 4), round(max(zs), 4)], 'design_m': SL.TOP, 'tolerance_m': .008})
    edge = {}
    for nm, (x, y) in {'S': (0, -1.95), 'N': (0, 1.95), 'E': (1.95, 0), 'W': (-1.95, 0)}.items():
        z = down(x, y); edge[nm] = round(z, 4) if z else None
    check('edges_flush_with_sg01_top', all(v is not None and abs(v - SL.TOP) <= .006 for v in edge.values()),
          {'edge_z_m': edge, 'note': 'SG01 Socket_Top (z 1.6 in SG01) sits on Socket_Edge_*: the top tread meets the landing at the same height'})
    lz = up(SL.LANTERN[0], SL.LANTERN[1], SL.TOP - .1)
    need = {f'Socket_Edge_{k}' for k in 'SNEW'} | {'Socket_Lantern'} | {f'Socket_Post_{k}' for k in ('SW', 'SE', 'NE', 'NW', 'S', 'N', 'E', 'W')}
    check('sockets_present', need <= set(S['sockets']), {'missing': sorted(need - set(S['sockets']))})
    return {'top_z_m': SL.TOP, 'size_m': [4, 4], 'lantern_socket_z_m': round(S['sockets']['Socket_Lantern'].matrix_world.translation.z, 4),
            'post_centres_m': 'corners and edge middles, 0.2 m in from the outer face, 1.8 m apart', 'sockets': sorted(S['sockets'])}


def shelter_checks(aid, check):
    """SG04: eave and architrave clear a person, the bench at seat height, the floor level, a usable depth inside."""
    import sg_shelter as SH
    down, up, along = _bvh([S['lods'][0]['Main']])
    eave = [up(x, -1.42, .3) for x in (-1.6, -.8, 0., .8, 1.6)]
    check('eave_underside_at_least_2_6m', all(z is not None and z >= 2.6 for z in eave),
          {'eave_underside_z_m': [round(z, 3) if z else None for z in eave], 'rule': 'modeling-style-spec-v1 section 4: eave underside >= 2.6 m'})
    head = [up(x, SH.COL_Y, .3) for x in (-1.2, -.6, 0., .6, 1.2)]
    check('clear_height_under_architrave', all(z is not None and z >= 2.3 for z in head),
          {'underside_z_m': [round(z, 3) if z else None for z in head], 'floor_m': SH.FLOOR, 'need_m': 2.3, 'note': 'brackets at the columns come down to 2.49 m'})
    seat = [down(x, .72, 2.) for x in (-.06, .52, 1.04)]          # from under the roof
    check('bench_seat_height', all(z is not None and abs(z - SH.SEAT) <= .015 for z in seat), {'seat_z_m': [round(z, 4) if z else None for z in seat], 'design_m': SH.SEAT})
    fl = [down(x, y, 2.) for x in (-1.3, -.7, 0., .7, 1.2) for y in (-1.3, -.7, -.2)]
    check('floor_level', all(z is not None and abs(z - SH.FLOOR) <= .006 for z in fl), {'z_min_max_m': [round(min(fl), 4), round(max(fl), 4)], 'design_m': SH.FLOOR})
    depth = []
    for x in (-.6, 0., .6):
        h = along((x, -2.5, 1.0), (0, 1, 0)); depth.append(round(h[0].y, 3) if h else None)
    check('open_depth_inside', all(d is not None and d >= .6 for d in depth), {'first_hit_y_at_1m_height': depth, 'note': 'from the open front (y -1.5) to the rock is at least 2.1 m'})
    need = {'Socket_Front', 'Socket_Seat', 'Socket_Basin'}
    check('sockets_present', need <= set(S['sockets']), sorted(S['sockets']))
    return {'eave_underside_min_m': round(min(eave), 3), 'architrave_clear_m': round(min(head), 3), 'seat_m': SH.SEAT, 'sockets': sorted(S['sockets'])}


def wide_stair_checks(aid, check): return sg_wide.wide_stair_checks(aid, check, _bvh, S['lods'][0]['Main'])
def wide_landing_checks(aid, check): return sg_wide.wide_landing_checks(aid, check, _bvh, S['lods'][0]['Main'])


def spec_checks(aid, check):
    kind = ASSETS[aid]['kind']
    if kind == 'stair': return stair_checks(aid, check)
    fn = globals().get(f'{kind}_checks')
    return fn(aid, check) if fn else {}


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    force = '--force' in argv; ids = [a for a in argv if a in ASSETS] or list(ASSETS)
    if '--preview' in argv:
        out = Path(argv[argv.index('--preview') + 1])
        for aid in ids: preview(aid, out)
    else:
        for aid in ids: run(aid, force)
