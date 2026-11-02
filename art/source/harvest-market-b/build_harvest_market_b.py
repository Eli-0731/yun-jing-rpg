"""harvest-market-b v001: MK01 steelyard, MK02 harvest sieve + three herb grades, MK03 price board + coins,
MK04 back basket (work pack 02-B, 2026-11-02).

Run one asset per process:
  blender --background --factory-startup --python art/source/harvest-market-b/build_harvest_market_b.py -- MK01_Steelyard
  ... -- MK01_Steelyard --preview <dir>     quick procedural look, no bake or export
An asset whose validation.json exists is skipped unless --force is given.

Shared helpers ti_core / ti_mats / ti_pipeline are copied from art/source/tea-brewing-b (ti_pipeline: socket names
matched case-insensitively, so the work pack's Socket_Back counts). LOD1/LOD2 land on about 50% / 15% of LOD0.
Each export group is its own object with its own pivot (pan on its hang ring, counterweight on its slide ring,
herbs on their root tips, tag on its hole); one baked atlas per asset.
Writes:
  art/source/harvest-market-b/blend/<ID>_v001.blend
  art/exports/harvest-market-b/<ID>/<ID>_v001.fbx, Textures/, model_info.json, validation.json
  art/previews/harvest-market-b/<ID>/turnaround/ (ten views + views.json), hero, LOD sheet, state renders
"""
import bpy, bmesh, sys, json, math, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np
from mathutils import Vector, Matrix
import ti_core, ti_mats, ti_pipeline as pl, mk_assets as A
from ti_core import S

KIT = 'harvest-market-b'
ART = HERE.parents[1]
VER = 'v001'
LOD_TARGET = {1: .50, 2: .15}
LOD_DROPS = {1: (2, 3, 99), 2: (1, 2, 3, 99)}

ASSETS = {
    'MK01_Steelyard': dict(zh='桿秤', slot='Market_HerbalStall / Socket_Scale', tex=2048, build=A.mk01_steelyard,
        limit=(.8, .3, .6), pivots={'Pan': 'SOCKET_pan', 'Weight': 'SOCKET_weight_rest'}, states=['weight 0–0.5 m on local X'],
        note='秤砣（_Weight）是獨立物件，沿秤桿局部 X 軸 0–0.5 m 滑動（SOCKET_weight_rest → SOCKET_weight_max）；秤盤（_Pan）三條麻繩掛在秤桿下的銅環，pivot 在掛環；SOCKET_hook 是整把秤掛到攤子 Socket_Scale 的點'),
    'MK02_HarvestSieve': dict(zh='收成竹篩＋三級草藥捆', slot='TY_Field01 田邊（分揀）', tex=4096, build=A.mk02_harvest_set,
        limit=None, pivots='bottom', keep_pivot=('Litter',), states=['_Glow 0–1（上品葉尖發光）', 'Litter 可隱藏'],
        note='竹篩（Main；篩底的落葉與土屑是獨立的 Litter，原點與 Main 相同，可隱藏）、三種草藥捆（BundleTop/Mid/Low）、三種單株（PlantTop/Mid/Low，拖曳用）各自是獨立物件，pivot 在各自底部中心；上品的葉子在 Glow 材質槽，發光強度 = Unity _Glow（0–1）'),
    'MK03_PriceBoard': dict(zh='價目木牌＋錢串', slot='Market_HerbalStall 攤前', tex=2048, build=A.mk03_market_set,
        limit=None, pivots={'PlateDemand': 'SOCKET_plate_demand', 'CoinString': 'bottom', 'LooseCoins': 'bottom', 'Purse': 'bottom'},
        regroup={'Purse_': 'Purse'}, states=['Plate_Demand 可替換'],
        note='木牌牌面空白（UI 疊字）；Plate_Demand 是可替換小木片，掛在 SOCKET_plate_demand 的木釘上，正面 SOCKET_demand_icon 貼今天收的圖示；錢串（10 枚）、散錢 3 枚、錢袋各自獨立，出售結束落在 SOCKET_coins_drop'),
    'MK04_BackBasket': dict(zh='背簍', slot='角色背上（Socket_Back）', tex=4096, build=A.mk04_back_basket,
        limit=(.45, .35, .6), pivots={'Fill': 'Socket_Back'}, origin_socket='Socket_Back', uv_weight={'Fill': .2}, states=['empty', 'full (Fill on)'],
        note='原點在背部貼身那一面的中間（Socket_Back，同一點），核心組把 Socket_Back 掛到角色背上；裝滿是另一個子網格 _Fill（三捆草藥露出口外），整個開關'),
}


def make_lods():
    """LOD1/LOD2 per export group: drop small parts while enough triangles remain, then collapse to the target."""
    tris = lambda me: sum(len(p.vertices) - 2 for p in me.polygons)
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
                for _ in range(6):
                    dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); tm_ = e.to_mesh(); n = tris(tm_); e.to_mesh_clear()
                    if abs(n - want) <= max(2, want * .01): break
                    m.ratio = min(1., m.ratio * want / max(n, 1))
                bpy.ops.object.modifier_apply(modifier=m.name)
            try: bpy.ops.mesh.customdata_custom_splitnormals_clear()
            except Exception: pass
            bpy.ops.object.shade_smooth_by_angle(angle=math.radians(38))
            lods[lv][gname] = o
            report.setdefault(gname, {'LOD0': n0})[f'LOD{lv}'] = tris(o.data)
    S['lods'] = lods
    return report


def regroup(cfg):
    for prefix, group in (cfg.get('regroup') or {}).items():
        for o in S['parts']:
            if o.name.startswith(prefix): o['group'] = group


def move_origin(cfg):
    """MK04: the whole model's origin sits on the back-contact face (Socket_Back), not the bottom centre.
    Runs after the bake: the procedural materials read world Z (ground grime, moss), so the model has to stand
    on the ground while they are evaluated."""
    sk = cfg.get('origin_socket')
    if not sk: return
    p = S['sockets'][sk].matrix_world.translation.copy()
    shift = Matrix.Translation(-p)
    for o in list(S['lod0'].values()) + list(S['sockets'].values()):
        if o.parent is None: o.matrix_world = shift @ o.matrix_world
    bpy.context.view_layer.update()


def set_pivots(cfg):
    """Give each export group its own origin (socket point or bottom centre). Mesh data moves, world stays."""
    piv = cfg['pivots']
    for gname, o in S['lod0'].items():
        want = piv if isinstance(piv, str) else (piv or {}).get(gname)
        if gname == 'Main' or gname in cfg.get('keep_pivot', ()) or not want: continue   # keep_pivot: shares Main's origin
        if want == 'bottom':
            lo, hi = pl.eval_bounds([o]); p = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
        else:
            p = S['sockets'][want].matrix_world.translation.copy()
        o.data.transform(Matrix.Translation(-p)); o.location = p
    bpy.context.view_layer.update()


def run(aid, force=False):
    cfg = ASSETS[aid]
    exp = ART / 'exports' / KIT / aid; prev = ART / 'previews' / KIT / aid; blend = ART / 'source' / KIT / 'blend'
    if (exp / 'validation.json').exists() and not force:
        print('ALREADY_COMPLETE', aid, flush=True); return
    t0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene; scene.unit_settings.system = 'METRIC'; scene.unit_settings.scale_length = 1
    bpy.context.preferences.filepaths.save_version = 0
    ti_mats.MAT_INFO.clear(); ti_core.reset_state(aid)
    P = A.palette(); cfg['build'](P); regroup(cfg)
    pl.normalise()
    pl.join_groups(); set_pivots(cfg); pl.uv_atlas(cfg.get('uv_weight'))
    pl.bake(exp / 'Textures', cfg['tex'])
    move_origin(cfg)
    lod_report = make_lods(); pl.export_materials()
    S['col'].hide_render = True; S['col'].hide_viewport = True
    lod0 = list(S['lods'][0].values())
    lo, hi = pl.eval_bounds(lod0); dims = hi - lo
    checks = []
    def check(name, ok, detail): checks.append({'check': name, 'pass': bool(ok), 'detail': detail})
    pieces = {}
    for gname, o in S['lods'][0].items():
        a, b = pl.eval_bounds([o]); pieces[gname] = {'dims_m': [round(v, 4) for v in b - a], 'pivot': [round(v, 4) for v in o.location],
                                                      'min_z_local': round(a.z - o.location.z, 4)}
    if cfg.get('origin_socket'):
        sk = S['sockets'][cfg['origin_socket']].matrix_world.translation
        check('origin_on_back_contact_face', sk.length < 1e-4 and abs(hi.y) < .06, {'socket': [round(v, 4) for v in sk], 'max_y': round(hi.y, 4),
              'note': 'work pack 2.4: origin at the middle of the face against the back'})
    else:
        check('origin_bottom_centre', abs(lo.z) < 1e-4 and abs((lo.x + hi.x) / 2) < 1e-3 and abs((lo.y + hi.y) / 2) < 1e-3,
              {'min': [round(v, 4) for v in lo], 'max': [round(v, 4) for v in hi]})
    if cfg['limit']:
        check('within_size_limit', all(d <= l + 1e-4 for d, l in zip(dims, cfg['limit'])), {'dims_m': [round(v, 4) for v in dims], 'limit_m': cfg['limit']})
    spec_checks(aid, check, pieces, dims)
    tot = {k: sum(g[k] for g in lod_report.values()) for k in ('LOD0', 'LOD1', 'LOD2')}
    r1, r2 = tot['LOD1'] / tot['LOD0'], tot['LOD2'] / tot['LOD0']
    check('lod_ratios_50_15', .45 <= r1 <= .55 and .12 <= r2 <= .18, {'triangles': tot, 'LOD1': round(r1, 3), 'LOD2': round(r2, 3), 'per_group': lod_report})
    exp.mkdir(parents=True, exist_ok=True)
    fbx = exp / f'{aid}_{VER}.fbx'
    pl.export_fbx(fbx)
    rt = pl.fbx_roundtrip(fbx)
    check('fbx_reimport_dimensions', all(abs(a - b) < 2e-3 for a, b in zip(rt['lod0_dimensions_m'], dims)),
          {'fbx_lod0_dims_m': rt['lod0_dimensions_m'], 'blend_dims_m': [round(v, 4) for v in dims]})
    names = rt['objects']
    check('fbx_has_lod0_1_2', all(any(n.split('.')[0].endswith(f'_LOD{lv}') for n in names) for lv in (0, 1, 2)), names)
    check('fbx_sockets', sorted(k.split('.')[0] for k in rt['sockets']) == sorted(S['sockets']), rt['sockets'])
    pl.ten_views(lod0, prev / 'turnaround', f'art/source/{KIT}/blend/{aid}_{VER}.blend')
    check('ten_views_rendered', len(list((prev / 'turnaround').glob('*.png'))) == 10, 'orthographic, framing asserted per view')
    shots = []
    for lv in (0, 1, 2):
        p = prev / f'_lod{lv}.png'; pl.persp_shot(list(S['lods'][lv].values()), p, samples=32); shots.append(p)
    _strip(shots, prev / f'{aid}_LOD_comparison.png'); [p.unlink() for p in shots]
    pl.persp_shot(lod0, prev / f'{aid}_hero.png', samples=96)
    states = state_renders(aid, prev, lod0)
    blend.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend / f'{aid}_{VER}.blend'))
    mats = sorted({m.name for g in S['lods'].values() for o in g.values() for m in o.data.materials})
    info = {
        'asset': aid, 'version': VER, 'name_zh': cfg['zh'], 'slot': cfg['slot'], 'note': cfg['note'],
        'units': 'meters', 'front': '-Y (Blender)', 'up': '+Z (Blender); FBX exported Y-up, -Z forward, transforms baked',
        'origin': 'back-contact face centre (Socket_Back)' if cfg.get('origin_socket') else 'bottom centre',
        'dimensions_m': [round(v, 4) for v in dims], 'size_limit_m': cfg['limit'], 'pieces': pieces,
        'lods': lod_report, 'lod_totals': tot, 'lod_rule': 'LOD1 about 50%, LOD2 about 15% of LOD0 (small parts dropped first, then collapse decimate)',
        'materials': mats, 'textures': sorted(p.name for p in (exp / 'Textures').glob('*.png')), 'texture_size_px': cfg['tex'],
        'unity': {'pipeline': 'URP Lit', 'BaseColor': f'{aid}_BaseColor.png', 'Normal': f'{aid}_Normal.png (OpenGL +Y)',
                  'MetallicSmoothness': f'{aid}_MetallicSmoothness.png (R metallic, A smoothness)',
                  'Emission': f'{aid}_Emission.png' if 'Emission' in S['tex'] else None,
                  'lod_group': 'objects end in _LOD0/_LOD1/_LOD2 under one root, so Unity builds a LODGroup on import'},
        'collision': False, 'collision_note': 'hand-held / tabletop / worn props: nothing here blocks the player (00-overview 2: only blocking pieces get _Collision)',
        'sockets_blender_xyz': {k: [round(v, 4) for v in e.matrix_world.translation] for k, e in S['sockets'].items()},
        'sockets_fbx_reimport_xyz': rt['sockets'], 'states': cfg['states'], 'state_renders': states, 'fbx_objects': rt['objects'],
        'modeling_method': f'procedural mesh construction (art/source/{KIT}/mk_assets.py, mk_herbs.py); procedural shaders (mk_mats.py) baked to a UV atlas',
        'reference': f'art/references/{aid[:4]}/v002/selected.png (AI three-view, not measured)',
        'unity_import_verified': False,
    }
    (exp / 'model_info.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
    val = {'asset': aid, 'checks': checks, 'all_pass': all(c['pass'] for c in checks), 'seconds': round(time.time() - t0),
           'not_checked': ['in-engine lighting (see the Unity report)']}
    (exp / 'validation.json').write_text(json.dumps(val, ensure_ascii=False, indent=2), encoding='utf-8')
    print('ASSET_COMPLETE', aid, 'all_pass=', val['all_pass'], round(time.time() - t0), 's', flush=True)


def spec_checks(aid, check, pieces, dims):
    d = lambda g: pieces[g]['dims_m']
    if aid == 'MK01_Steelyard':
        beam = [o for o in S['parts'] if o.name == 'Beam'][0]
        a, b = pl.eval_bounds([beam]); L = b.x - a.x
        check('beam_length_max_0.7', L <= .7 + 1e-4, {'beam_m': round(L, 4)})
        check('pan_diameter_max_0.25', max(d('Pan')[0], d('Pan')[1]) <= .25 + 1e-4, {'pan_dims_m': d('Pan')})
        check('hung_height_max_0.6', dims.z <= .6 + 1e-4, {'height_m': round(dims.z, 4)})
        s0, s1 = S['sockets']['SOCKET_weight_rest'].matrix_world.translation, S['sockets']['SOCKET_weight_max'].matrix_world.translation
        check('weight_slides_0_to_0.5_on_beam', abs((s1 - s0).x - .5) < 1e-4 and s1.x <= b.x, {'rest_x': round(s0.x, 4), 'max_x': round(s1.x, 4), 'beam_end_x': round(b.x, 4)})
    if aid == 'MK02_HarvestSieve':
        m = d('Main')
        check('sieve_0.6_by_0.08', max(m[0], m[1]) <= .6 + 1e-4 and m[2] <= .08 + 1e-4, {'sieve_dims_m': m})
        for g in ('BundleTop', 'BundleMid', 'BundleLow'):
            check(f'{g}_about_0.35_long', .32 <= d(g)[2] <= .38, {'dims_m': d(g)})
        for g in ('PlantTop', 'PlantMid', 'PlantLow'):
            check(f'{g}_about_0.3_long', .27 <= d(g)[2] <= .33, {'dims_m': d(g)})
        own = [g for g in pieces if g != 'Main' and g not in ASSETS[aid].get('keep_pivot', ())]
        check('pivots_at_bottom_centre', all(abs(pieces[g]['min_z_local']) < 1e-3 for g in own), {g: pieces[g]['min_z_local'] for g in own})
        check('litter_shares_main_origin', all(pieces[g]['pivot'] == pieces['Main']['pivot'] for g in ASSETS[aid].get('keep_pivot', ())),
              {g: pieces[g]['pivot'] for g in ('Main',) + tuple(ASSETS[aid].get('keep_pivot', ()))})
    if aid == 'MK03_PriceBoard':
        m = d('Main')
        check('board_0.5_0.04_0.7', m[0] <= .5 + 1e-3 and m[1] <= .05 and m[2] <= .7 + 1e-4, {'board_dims_m': m, 'note': 'depth includes nail heads and the tag peg'})
        check('coin_string_about_0.12', .11 <= d('CoinString')[0] <= .125, {'dims_m': d('CoinString')})
        check('purse_about_0.15', .13 <= d('Purse')[2] <= .155, {'dims_m': d('Purse')})
    if aid == 'MK04_BackBasket':
        check('fill_is_separate_object', 'Fill' in pieces, list(pieces))


def state_renders(aid, prev, lod0):
    states = {}
    def emit(v):
        for m in bpy.data.materials:
            if m.node_tree and 'EMIT_STRENGTH' in m.node_tree.nodes: m.node_tree.nodes['EMIT_STRENGTH'].outputs[0].default_value = v
    if aid == 'MK01_Steelyard':
        w = S['lods'][0]['Weight']; x0 = w.location.x
        w.location.x = x0 + .5
        pl.persp_shot(lod0, prev / 'state_weight_max.png', direction=(0, -1, .2), samples=48); states['weight_max'] = 'state_weight_max.png'
        w.location.x = x0
    if aid == 'MK02_HarvestSieve':
        emit(1.0)
        pl.persp_shot(lod0, prev / 'state_glow_1.png', direction=(.3, -1, .45), samples=64); states['glow_1'] = 'state_glow_1.png'
        emit(0.0)
    if aid == 'MK04_BackBasket':
        f = S['lods'][0]['Fill']; f.hide_render = True
        pl.persp_shot([o for o in lod0 if o is not f], prev / 'state_empty.png', samples=64); states['empty'] = 'state_empty.png'
        f.hide_render = False; states['full'] = f'{aid}_hero.png'
    return states


def _strip(paths, out):
    ims = [bpy.data.images.load(str(p)) for p in paths]
    w, h = ims[0].size
    arr = np.concatenate([np.array(i.pixels[:], np.float32).reshape(h, w, 4) for i in ims], axis=1)
    im = bpy.data.images.new(out.stem, w * len(ims), h, alpha=True); im.pixels.foreach_set(arr.ravel())
    im.filepath_raw = str(out); im.file_format = 'PNG'; im.save()


def preview(aid, out_dir, samples=24):
    """Quick look before the bake: procedural materials, five perspective views."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ti_mats.MAT_INFO.clear(); ti_core.reset_state(aid)
    cfg = ASSETS[aid]; P = A.palette(); cfg['build'](P); regroup(cfg); pl.normalise()
    S['cut'].hide_render = True
    for m in bpy.data.materials:
        if m.node_tree and 'EMIT_STRENGTH' in m.node_tree.nodes: m.node_tree.nodes['EMIT_STRENGTH'].outputs[0].default_value = 1.0
    lo, hi = pl.eval_bounds(S['parts']); print('PREVIEW_DIMS', aid, [round(v, 3) for v in hi - lo], flush=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, d in (('front', (0, -1, .12)), ('side', (1, 0, .12)), ('back', (0, 1, .12)), ('three_quarter', (-1, -1.2, .5)), ('top', (.05, -.3, 1))):
        pl.persp_shot(S['parts'], out_dir / f'{aid}_{name}.png', direction=d, samples=samples, lens=70)


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    force = '--force' in argv; ids = [a for a in argv if a in ASSETS] or list(ASSETS)
    if '--preview' in argv:
        out = Path(argv[argv.index('--preview') + 1])
        for aid in ids: preview(aid, out)
    else:
        for aid in ids: run(aid, force)
