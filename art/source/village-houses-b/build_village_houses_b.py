"""village-houses-b v001 (work pack B-104h part 2, batch 3): VL01 long-empty house, VL02 just-moved-into house, VL03 half-collapsed
house, all three on the Dondon StarterHouse v004 outline.

Run one asset per process:
  blender --background --factory-startup --python art/source/village-houses-b/build_village_houses_b.py -- VL01_LongEmptyHouse --force
  ... -- VL01_LongEmptyHouse --preview <dir>     procedural look only, no bake or export
An asset whose validation.json exists is skipped unless --force is given.

ti_core / ti_mats / mk_mats / cr_mats / cr_parts / fr_parts / fr_mats / ti_pipeline / qa_* / backface_check / ruler_views / pair_sheets
are copied from art/source/forest-roots-b. Changes: ti_core.finish takes a per-part texel weight (uvw); ti_pipeline keeps a per-face
'uvw' through the join, scales UV islands by it, and can pack and bake one atlas per group set (objs / prefix).
A house is three materials on one object per LOD: Main atlas (plaster, brick, stone, ridge), Wood atlas (frame, doors, windows,
boards, roof boards) and the shared roof-tile texture (VL_Shared, own UVs; tiles built per LOD, not decimated). Small growth and
leaves stay a separate Detail_Small object.
Writes:
  art/source/village-houses-b/blend/<ID>_v001.blend
  art/exports/village-houses-b/<ID>/<ID>_v001.fbx, .glb, Textures/, model_info.json, validation.json
  art/previews/village-houses-b/<ID>/turnaround/ (ten views + views.json), hero, LOD sheets
"""
import bpy, bmesh, sys, json, math, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np
from mathutils import Vector, Matrix
import ti_core, ti_mats, ti_pipeline as pl
import vl_house, vl_roof
from ti_core import S

KIT = 'village-houses-b'
ART = HERE.parents[1]
VER = 'v001'
LOD_TARGET = {1: .50, 2: .15}
LOD_DROPS = {1: (2, 99), 2: (1, 2, 99)}

ASSETS = {}
vl_house.register(ASSETS)


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
    objs = [o for g in S['lods'].values() for o in g.values()] + collision_objs()
    for o in objs:
        me = o.data; co = np.zeros(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
        w = co + np.array(o.location, np.float32)
        c = w.copy(); c[:, 0] = np.clip(c[:, 0], lo_b[0], hi_b[0]); c[:, 1] = np.clip(c[:, 1], lo_b[1], hi_b[1]); c[:, 2] = np.maximum(c[:, 2], lo_b[2])
        moved = max(moved, float(np.abs(c - w).max()))
        me.vertices.foreach_set('co', (c - np.array(o.location, np.float32)).ravel()); me.update()
    S['clamped_m'] = round(moved, 5)
    assert moved < cfg.get('clamp_max', .02), ('clamp moved a vertex too far', moved)   # TE03: buried stone bottoms are flattened onto z = 0


def roof_lods(src, tex_dir):
    """Roof tiles: built per LOD (lod_mask bit 0/1/2), not decimated; the shared tile texture is copied into this piece's Textures."""
    import shutil
    tex_dir.mkdir(parents=True, exist_ok=True)
    for f in vl_roof.TILE_DIR.glob('VL_RoofTiles_*.png'): shutil.copy2(f, tex_dir / f.name)
    rep = {}; orig = src.data
    for lv in (0, 1, 2):
        me = orig.copy(); bm = bmesh.new(); bm.from_mesh(me); lay = bm.faces.layers.int.get('lod_mask')
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if not (f[lay] >> lv) & 1], context='FACES')
        bm.to_mesh(me); bm.free()
        for nm in ('lod_mask', 'uvw'):
            if nm in me.attributes: me.attributes.remove(me.attributes[nm])
        o = src.copy() if lv else src; o.data = me
        if lv: S['lodcol'].objects.link(o)
        o.name = f"{S['asset']}_Roof_LOD{lv}"; me.name = o.name
        S['lods'][lv]['Roof'] = o
        rep[f'LOD{lv}'] = sum(len(p.vertices) - 2 for p in me.polygons)
    S['lod0']['Roof'] = S['lods'][0]['Roof']
    return rep


def export_materials_multi(cfg):
    """Baked materials per atlas (M_<ID>_Main, M_<ID>_Wood) and the roof-tile material (M_<ID>_RoofTiles, own UVs)."""
    a = S['asset']; mats = {}
    atlas_of = {g: name for name, groups in cfg['atlases'].items() for g in groups}
    def load(p, color):
        im = bpy.data.images.load(str(p), check_existing=True); im.colorspace_settings.name = 'sRGB' if color else 'Non-Color'; return im
    def baked(name):
        if name in mats: return mats[name]
        tex = S['tex_sets'][a if name == 'Main' else f'{a}_{name}']
        m = bpy.data.materials.new(f'M_{a}_{name}'); m.use_nodes = True; nt = m.node_tree; bs = nt.nodes['Principled BSDF']
        def t(im, sock):
            n = nt.nodes.new('ShaderNodeTexImage'); n.image = im; nt.links.new(n.outputs['Color'], sock); return n
        t(load(tex['BaseColor'], True), bs.inputs['Base Color']); t(load(tex['Roughness'], False), bs.inputs['Roughness']); t(load(tex['Metallic'], False), bs.inputs['Metallic'])
        nm = nt.nodes.new('ShaderNodeNormalMap'); t(load(tex['Normal'], False), nm.inputs['Color']); nt.links.new(nm.outputs[0], bs.inputs['Normal'])
        bs.inputs['Specular IOR Level'].default_value = .35
        m['unity'] = {'shader': 'Universal Render Pipeline/Lit', 'BaseColor': tex['BaseColor'].name, 'Normal': tex['Normal'].name, 'MetallicSmoothness': tex['MetallicSmoothness'].name}
        mats[name] = m; return m
    roofm = None
    for lv, groups in S['lods'].items():
        for g, o in groups.items():
            me = o.data
            if g == 'Roof':
                m = me.materials[0]
                if not m.name.startswith('M_'):
                    m.name = f'M_{a}_RoofTiles'
                    m['unity'] = {'shader': 'Universal Render Pipeline/Lit', 'BaseColor': 'VL_RoofTiles_BaseColor.png', 'Normal': 'VL_RoofTiles_Normal.png',
                                  'MetallicSmoothness': 'VL_RoofTiles_MetallicSmoothness.png', 'uv': 'own (tile cells)'}
                roofm = m; continue
            me.materials.clear(); me.materials.append(baked(atlas_of[g]))
            me.polygons.foreach_set('material_index', [0] * len(me.polygons)); me.update()
    if roofm: mats['RoofTiles'] = roofm
    return mats


def merge_per_lod():
    """Main, Stone, Wood and Roof of one LOD become one object (four material slots); Detail_Small stays apart (quality tiers)."""
    a = S['asset']
    for lv, groups in S['lods'].items():
        parts = [groups[g] for g in ('Main', 'Stone', 'Wood', 'Roof') if g in groups]
        bpy.ops.object.select_all(action='DESELECT')
        for o in parts: o.select_set(True)
        bpy.context.view_layer.objects.active = parts[0]
        bpy.ops.object.join()
        j = bpy.context.view_layer.objects.active; j.name = f'{a}_LOD{lv}'; j.data.name = j.name
        S['lods'][lv] = {'Main': j, **{g: o for g, o in groups.items() if g not in ('Main', 'Stone', 'Wood', 'Roof')}}
    S['lod0'] = dict(S['lods'][0])


def make_collision(aid):
    extra = S.get('collision_mesh')
    if not extra: return None
    me = bpy.data.meshes.new(aid + '_Collision'); me.from_pydata(extra[0], [], extra[1]); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(aid + '_Collision', me); S['lodcol'].objects.link(o); o.hide_render = True
    S['collision_obj'] = o
    det = S.get('detail_collision_mesh')   # VL04/VL05: boxes for the props in Detail_Small, switched off with it
    if det:
        md = bpy.data.meshes.new(aid + '_Detail_Collision'); md.from_pydata(det[0], [], det[1]); md.update()
        bm = bmesh.new(); bm.from_mesh(md); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(md); bm.free()
        od = bpy.data.objects.new(aid + '_Detail_Collision', md); S['lodcol'].objects.link(od); od.hide_render = True
        S['detail_collision_obj'] = od
    return o


def collision_objs():
    return [o for o in (S.get('collision_obj'), S.get('detail_collision_obj')) if o]


def export_fbx(path):
    a = S['asset']
    root = bpy.data.objects.new(a, None); S['lodcol'].objects.link(root); S['root'] = root
    for groups in S['lods'].values():
        for o in groups.values(): o.parent = root
    extra = collision_objs()
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
    for o in S['parts']:
        if o.name.startswith('Roof_Tiles') and not o.name.endswith('LOD0'): o.hide_render = True
    S['parts'] = [o for o in S['parts'] if not o.hide_render]
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
    roof = S['lod0'].pop('Roof', None)                  # tiles keep their own UVs and are built per LOD
    for name, groups in cfg['atlases'].items():
        objs = [S['lod0'][g] for g in groups if g in S['lod0']]
        pl.uv_atlas(cfg.get('uv_weight'), cfg['tex'], shape=cfg.get('uv_shape', 'CONCAVE'), objs=objs); pl.spread_zero_uv(objs)
        S['texel_density'] = {**S.get('texel_density', {}), name: texel_density(objs, cfg['tex'])}
        pl.bake(exp / 'Textures', cfg['tex'], objs=objs, prefix=aid if name == 'Main' else f'{aid}_{name}')
    lod_report = make_lods()
    if roof is not None: lod_report['Roof'] = roof_lods(roof, exp / 'Textures')
    export_materials_multi(cfg)
    merge_per_lod()
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
    if S.get('detail_collision_obj'):
        check('fbx_detail_collision', (aid + '_Detail_Collision') in [n.split('.')[0] for n in names], 'prop collision mesh present, apart from the house collision')
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
        'name_zh': cfg['zh'], 'slot': cfg.get('slot', 'A1_QingxiVillage_EmptyHouse'), 'note': cfg['note'],
        'budget_per_lod': budget, 'texture_resolution_px': tex_px,
        'units': 'meters', 'front': '-Y (Blender)', 'up': '+Z (Blender); FBX exported Y-up, -Z forward, transforms baked',
        'origin': cfg.get('origin', 'footprint centre, z = 0 at the lowest ground contact'), 'dimensions_m': [round(v, 4) for v in dims], 'bounds_min_m': [round(v, 4) for v in lo], 'bounds_max_m': [round(v, 4) for v in hi],
        'size_limit_m': cfg['limit'], 'pieces': pieces,
        'lods': lod_report, 'lod_totals': tot, 'lod_rule': 'LOD1 about 50%, LOD2 about 15% of LOD0 (detail parts dropped first, then collapse decimate)',
        'materials': mats, 'textures': sorted(p.name for p in (exp / 'Textures').glob('*.png')), 'texture_size_px': cfg['tex'],
        'unity': {'pipeline': 'URP Lit', 'axes': 'imported with bakeAxisConversion: Unity local = (Blender x, z, y); the model front faces Unity -Z',
                  'materials': {m.name: dict(m['unity']) for m in sorted({m for g in S['lods'].values() for o in g.values() for m in o.data.materials}, key=lambda m: m.name)},
                  'normal_maps': 'OpenGL +Y', 'MetallicSmoothness': 'R metallic, A smoothness', 'lod_group': 'objects end in _LOD0/_LOD1/_LOD2 under one root',
                  'collision': f'{aid}_Collision: MeshCollider (convex off), renderer hidden',
                  **({'detail_collision': f'{aid}_Detail_Collision: MeshCollider (convex off), renderer hidden; switch it off together with '
                      f'{aid}_Detail_Small_LOD0/1/2 (low quality), it only covers props inside Detail_Small'} if S.get('detail_collision_obj') else {})},
        **({'detail_collision_boxes': S.get('detail_boxes')} if S.get('detail_collision_obj') else {}),
        'collision': bool(S.get('collision_obj')),
        **({'ground_z_m': cfg['ground_z']} if 'ground_z' in cfg else {}),
        **({'parts': S['part_notes']} if S.get('part_notes') else {}),
        'sockets_blender_xyz': {k: [round(v, 4) for v in e.matrix_world.translation] for k, e in S['sockets'].items()},
        'sockets_fbx_reimport_xyz': rt['sockets'], 'fbx_objects': rt['objects'], 'glb': glb.name,
        'interface': spec,
        'modeling_method': f'procedural mesh construction (art/source/{KIT}/) on the StarterHouse v004 outline; procedural shaders baked to two {cfg["tex"]} atlases (Main, Wood); roof tiles on the shared 1024 tile-cell texture (VL_Shared)',
        'texel_density_px_per_m': S.get('texel_density'), 'hidden_faces_downweighted': S.get('occluded_faces'),
        'reference': f"art/references/{cfg['ref'].split('/')[0]}/ (AI three-view {cfg['ref']}; proportions from the work pack's written sizes, not measured from the image)",
        'unity_import_verified': 'see artifacts/village-houses-unity/ (local Unity batch check, not committed)',
        'based_on': 'art/incoming/dondon/StarterHouse/v004 (outline and sizes; the original files are not changed)',
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




# ------------------------------------------------------------------ FR checks
from vl_checks import *   # noqa: F401,F403  house_checks, texel_density


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
