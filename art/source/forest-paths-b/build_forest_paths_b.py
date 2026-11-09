"""forest-paths-b v001 (work pack B 11/08): FP01-FP05 forest path kit (straight, curves, slope, root crossing, log steps).

Run one asset per process:
  blender --background --factory-startup --python art/source/forest-paths-b/build_forest_paths_b.py -- FP01_PathStraight --force
  ... -- FP01_PathStraight --preview <dir>     procedural look only, no bake or export
An asset whose validation.json exists is skipped unless --force is given.

ti_core / ti_mats / mk_mats / cr_mats / cr_parts / fr_parts / fr_mats / ti_pipeline / qa_* / backface_check / ruler_views / pair_sheets
are copied from art/source/village-houses-b (branch art/b-1107-vl-houses-lod); only the kit name in ruler_views, pair_sheets,
qa_uv_overlap and backface_check differs. The pipeline below is the forest-roots-b one with two changes for a path kit:
  - the walking surface ('Ground' group) is not decimated: its LOD1 / LOD2 drop whole rows of the grid (every 2nd / all but every
    10th), keeping every column and both end rows, so the end sections are the same at every LOD and any LOD meets any LOD;
  - the end rows get the kit section's exact normals (custom split normals), so two pieces shade the same across a joint.
Writes:
  art/source/forest-paths-b/blend/<ID>_v001.blend
  art/exports/forest-paths-b/<ID>/<ID>_v001.fbx, .glb, Textures/, model_info.json, validation.json
  art/previews/forest-paths-b/<ID>/turnaround/ (ten views + views.json), hero, LOD sheets
"""
import bpy, bmesh, sys, json, math, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np
from mathutils import Vector, Matrix
import ti_core, ti_mats, ti_pipeline as pl
import fp_path, fp_parts
from ti_core import S

KIT = 'forest-paths-b'
ART = HERE.parents[1]
VER = 'v001'
LOD_TARGET = {1: .50, 2: .15}
LOD_DROPS = {1: (2, 99), 2: (1, 2, 99)}

ASSETS = {}
fp_path.register(ASSETS)


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
        lods[lv] = {}; share = LOD_TARGET[lv]
        if 'Ground' in S['lod0']:                  # the walking surface first: it only drops whole rows
            g0 = tris(S['lod0']['Ground'].data); o = ground_lod(S['lod0']['Ground'], lv); lods[lv]['Ground'] = o
            report.setdefault('Ground', {'LOD0': g0})[f'LOD{lv}'] = g1 = tris(o.data)
            if g1 > g0 * (LOD_TARGET[lv] + .03):     # a grid that has to keep many rows (FP05's steps): the other parts take the difference
                rest = sum(tris(x.data) for k_, x in S['lod0'].items() if k_ != 'Ground')
                share = min(share, (LOD_TARGET[lv] * (g0 + rest) - g1) / max(rest, 1))
        for gname, src in S['lod0'].items():
            if gname == 'Ground': continue
            n0 = tris(src.data); want = n0 * share
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
    for lv in (0, 1, 2):
        if 'Ground' in lods[lv]: seam_normals(lods[lv]['Ground'])
    return report


GROUND_KEEP = {1: 2, 2: 10}     # LOD1 keeps every 2nd row of the walking-surface grid, LOD2 every 10th (0.5 m); end rows always


def ground_lod(src, lv):
    """Walking-surface LOD by dropping whole grid rows (dissolve the across edges of a row and the skirt edges under it): every
    column and both end rows stay, so the end section is the same at every LOD; corner UVs are kept."""
    me = src.data.copy(); bm = bmesh.new(); bm.from_mesh(me)
    lay = bm.verts.layers.float_vector.get('pth'); ni = S['slab']['ni']; ds = S['slab']['L'] / ni; k = GROUND_KEEP[lv]
    row = lambda v: int(round(v[lay].x / ds))      # (a tall end's grid lies past the end rows: never dropped)
    keep = set(S['slab'].get('keep', ()))
    drop = [e for e in bm.edges if row(e.verts[0]) == row(e.verts[1]) and 0 < row(e.verts[0]) < ni and row(e.verts[0]) % k and row(e.verts[0]) not in keep]
    bmesh.ops.dissolve_edges(bm, edges=drop, use_verts=True, use_face_split=False)
    bad = [f for f in bm.faces if len(f.verts) > 4]          # rows stay quads; the end caps were triangulated with LOD0
    bm.to_mesh(me); bm.free(); me.update()
    assert not bad, ('ground_lod left n-gons', len(bad))
    o = src.copy(); o.data = me; S['lodcol'].objects.link(o)
    o.name = src.name.replace('_LOD0', f'_LOD{lv}'); me.name = o.name
    S.setdefault('ground_rows', {})[f'LOD{lv}'] = len({row_ for row_ in range(ni + 1) if row_ % k == 0 or row_ == ni or row_ in keep})
    return o


def seam_normals(o):
    """Hard edges by angle (38 deg, as the other LODs), then the top-surface corners on both end rows take the exact normal of
    the kit section there (relief is zero at the ends), so the shading on either side of a joint is the same."""
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    try: bpy.ops.mesh.customdata_custom_splitnormals_clear()
    except Exception: pass
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(38))
    me = o.data; pth = me.attributes['pth'].data; L = S['slab']['L']; F = S['relief'].F
    cn = [Vector(c.vector) for c in me.corner_normals]; n_set = 0
    for p in me.polygons:
        if p.normal.z < .3: continue
        for li in p.loop_indices:
            vi = me.loops[li].vertex_index; s, t, h = pth[vi].vector
            if h <= 0. or not (s < 1e-4 or s > L - 1e-4): continue
            up = Vector((0, 0, 1)); lf = F.left(s)
            cn[li] = (up - lf * fp_parts.section_slope(t)).normalized(); n_set += 1
    me.normals_split_custom_set([tuple(c) for c in cn]); me.update()
    S.setdefault('seam_normals_set', {})[o.name] = n_set


def clamp_to_limit(cfg):
    """Separating flush faces pushes a piece out by a millimetre or two; pull every vertex back inside the footprint and above z = 0."""
    lo_b, hi_b = cfg.get('box') or ((-cfg['limit'][0] / 2, -cfg['limit'][1] / 2, 0.), (cfg['limit'][0] / 2, cfg['limit'][1] / 2, 99.)); moved = 0
    objs = [o for g in S['lods'].values() for o in g.values()] + ([S['collision_obj']] if S.get('collision_obj') else [])
    for o in objs:
        me = o.data; co = np.zeros(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
        w = co + np.array(o.location, np.float32)
        c = w.copy(); c[:, 0] = np.clip(c[:, 0], lo_b[0], hi_b[0]); c[:, 1] = np.clip(c[:, 1], lo_b[1], hi_b[1]); c[:, 2] = np.maximum(c[:, 2], lo_b[2])
        moved = max(moved, float(np.abs(c - w).max()))
        me.vertices.foreach_set('co', (c - np.array(o.location, np.float32)).ravel()); me.update()
    S['clamped_m'] = round(moved, 5)
    assert moved < cfg.get('clamp_max', .02), ('clamp moved a vertex too far', moved)   # TE03: buried stone bottoms are flattened onto z = 0


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
    if cfg.get('box'):
        (bx0, by0, bz0), (bx1, by1, bz1) = cfg['box']
        for o in S['parts']:
            a, b = pl.eval_bounds([o])
            over = max(bx0 - a.x, a.x - 1e9, b.x - bx1, by0 - a.y, b.y - by1, b.z - bz1, bz0 - a.z)
            if over > .003: print('PREVIEW_OUTSIDE', o.name, round(over, 3), [round(v, 2) for v in a], [round(v, 2) for v in b], flush=True)
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
    pl.uv_atlas(cfg.get('uv_weight'), cfg['tex'], shape=cfg.get('uv_shape', 'CONCAVE'), pad_px=cfg.get('uv_pad', 2.5)); pl.spread_zero_uv()
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
        'name_zh': cfg['zh'], 'slot': cfg.get('slot', 'D1_ForestEdge_to_D2_ElderTree'), 'note': cfg['note'],
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
        'modeling_method': f'procedural mesh construction (art/source/{KIT}/); procedural shaders (fp_mats.py, cr_mats.py, fr_mats.py) baked to one {cfg["tex"]} atlas; walking surface LODs by dropping grid rows (end rows kept)',
        'ground_rows_per_lod': {'LOD0': S['slab']['ni'] + 1, **S.get('ground_rows', {})} if S.get('slab') else None,
        'seam_normals_set': S.get('seam_normals_set'), 'leaves_laid': S.get('leaves_laid'),
        'reference': f"art/references/{cfg['ref'].split('/')[0]}/ (AI three-view {cfg['ref']}; proportions from the work pack's written sizes, not measured from the image)",
        'unity_import_verified': 'not yet: Unity check not run (project editor 6000.0.82f1 is not installed here)',
    }
    (exp / 'model_info.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
    val = {'asset': aid, 'checks': checks, 'all_pass': all(c['pass'] for c in checks), 'seconds': round(time.time() - t0),
           'not_checked': ['Unity import and walking (not run)', 'in-engine lighting', 'mobile frame rate (not measured)']}
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




# ------------------------------------------------------------------ FP checks
from fp_checks import *   # noqa: F401,F403  path_checks, _bvh


def spec_checks(aid, check):
    kind = ASSETS[aid]['kind']
    fn = globals().get(f'{kind}_checks')
    return fn(aid, check, ASSETS[aid]) if fn else {}


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    force = '--force' in argv; ids = [a for a in argv if a in ASSETS] or list(ASSETS)
    if '--preview' in argv:
        out = Path(argv[argv.index('--preview') + 1])
        for aid in ids: preview(aid, out)
    else:
        for aid in ids: run(aid, force)
