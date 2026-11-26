# DR06 倒伏巨木：量尺寸（長、徑、根盤寬高、陷進土裡多深、擋不擋人）、FBX 回匯檢查、十視圖、LOD 比較、model_info.json／validation.json。
# 和 D2 根與木的 report_dr02.py 同一套寫法。在做完 game_dr06 的 Blender 裡（或背景）：blender -b <DR06_..._v001.blend> --python report_dr06.py -- B
import bpy, math, os, sys, json, hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = 'D:/yun-jing-d2-logs/art/source/d2-roots-b'
HERE6 = 'D:/yun-jing-d2-logs/art/source/d2-logs-b'
ROOT = 'D:/yun-jing-d2-logs'
VER = 'v001'
ASSETS = {'A': 'DR06_FallenTrunk_A', 'B': 'DR06_FallenTrunk_B'}
DET = 'Detail_DR06_Plants'
NAME_ZH = {'A': '倒伏巨木・短（長 10 m、徑 1.4 m）', 'B': '倒伏巨木・長（長 16 m、徑 2 m）'}
SPEC = {'A': dict(L=10.0, D=1.4, plate=3.5), 'B': dict(L=16.0, D=2.0, plate=4.5)}
SLOT = 'D2 古樹空地四周的林地（工作包：4 件，兩種長度混用、可旋轉鏡像）'
VIEWS = [('01_front', (0, -1, .06)), ('02_right', (1, 0, .06)), ('03_rear', (0, 1, .06)), ('04_left', (-1, 0, .06)),
         ('05_front_right', (1, -1, .45)), ('06_rear_right', (1, 1, .45)), ('07_rear_left', (-1, 1, .45)),
         ('08_front_left', (-1, -1, .45)), ('09_top', (0, -.001, 1)), ('10_high_front', (0, -1, 1))]


def _load(p):
    g = {'__file__': p, '__name__': os.path.basename(p)[:-3]}
    exec(compile(open(p, encoding='utf-8').read(), p, 'exec'), g)
    return g


def tri(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def bounds(objs):
    lo, hi = [1e9] * 3, [-1e9] * 3
    for o in objs:
        mw = o.matrix_world
        for v in o.data.vertices:
            p = mw @ v.co
            for i in range(3):
                lo[i] = min(lo[i], p[i])
                hi[i] = max(hi[i], p[i])
    return [round(v, 4) for v in lo], [round(v, 4) for v in hi]


def bvh_of(o):
    return BVHTree.FromPolygons([o.matrix_world @ v.co for v in o.data.vertices], [tuple(p.vertices) for p in o.data.polygons])


def plants_inside(plants, body):
    t = bvh_of(body)
    M = plants.matrix_world
    n = in2 = in5 = 0
    for v in plants.data.vertices:
        q = M @ v.co
        if q.z < .05:
            continue
        n += 1
        loc, nr, _, _ = t.find_nearest(q, 1.0)
        if loc is None:
            continue
        d = (q - loc).dot(nr)
        in2 += d < -.02
        in5 += d < -.05
    return dict(vertices_checked=n, inside_body_over_2cm=in2, inside_body_over_5cm=in5)


def shape(o, b, V):
    """（建模座標：根盤在 x ≈ 0、斷口在 x = L、樹幹沿 +X）
    樹幹：每 1 m 量一次頂高、左右寬（中心高處橫打）；根盤：x < 0.6 m 那一段的寬、高；陷進土裡多深；橫著穿過去擋不擋（0.3／1.0／1.7 m 高）。"""
    t = bvh_of(o)
    L = V['L']
    rows = []
    for i in range(1, int(L)):
        x = float(i)
        top = t.ray_cast(Vector((x, 0, 20)), Vector((0, 0, -1)), 25)[0]
        if top is None:
            continue
        zc = b['trunk_z'](V, x)
        l_ = t.ray_cast(Vector((x, -15, zc)), Vector((0, 1, 0)), 30)[0]
        r_ = t.ray_cast(Vector((x, 15, zc)), Vector((0, -1, 0)), 30)[0]
        w = (r_.y - l_.y) if (l_ and r_) else 0.0
        rows.append((x, round(top.z, 3), round(w, 3)))
    plate = [o.matrix_world @ v.co for v in o.data.vertices if (o.matrix_world @ v.co).x < .6 and (o.matrix_world @ v.co).z > -.05]
    blocked = []
    for i in range(int(L * 2)):
        x = .25 + i * .5
        blocked.append([t.ray_cast(Vector((x, -15, z)), Vector((0, 1, 0)), 30)[0] is not None for z in (.3, 1.0, 1.7)])
    # 樹幹基部抬起來的那段：底下的空隙有多高（從地面往上打）
    gaps = []
    for i in range(int(L * .4 / .25)):
        x = .5 + i * .25
        h, n_ = t.ray_cast(Vector((x, b['trunk_pts'](V)[0][1], .02)), Vector((0, 0, 1)), 10)[:2]
        # 只算打到樹幹底面（法線朝下）的：樹幹已經貼地、陷進土裡那段，起點在樹幹裡面，會打到頂面的內側，不是空隙
        gaps.append(round(h.z, 3) if h is not None and n_.z < 0 else None)
    mids = [r for r in rows if .3 * L < r[0] < .9 * L]
    return dict(trunk_top_z_m_every_1m=[r[1] for r in rows], trunk_width_m_every_1m=[r[2] for r in rows],
                trunk_diameter_mid_m=round(sum(r[2] for r in mids) / max(1, len(mids)), 3),
                plate_width_y_m=round(max(p.y for p in plate) - min(p.y for p in plate), 3),
                plate_height_m=round(max(p.z for p in plate), 3),
                gap_under_raised_base_m=[g for g in gaps if g is not None][:12],
                blocked_fraction_at_0p3_1p0_1p7m=[round(sum(r[k] for r in blocked) / len(blocked), 3) for k in range(3)])


def fbx_roundtrip(path, asset):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    bpy.context.view_layer.update()
    m0 = [o for o in new if o.type == 'MESH' and o.name.split('.')[0] == f'{asset}_LOD0']
    lo, hi = bounds(m0)
    rep = dict(objects=sorted(o.name.split('.')[0] for o in new), lod0_dimensions_m=[round(hi[i] - lo[i], 4) for i in range(3)],
               uv_layers=[u.name for u in m0[0].data.uv_layers] if m0 else [],
               materials=sorted({s.material.name.split('.')[0] for o in new if o.type == 'MESH' for s in o.material_slots if s.material}))
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    return rep


def show(names):
    for c in bpy.data.collections:
        if c.name.startswith('DR06_'):
            c.hide_render = False
            for o in c.objects:
                o.hide_render = o.hide_viewport = o.name not in names


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def report(v, render=True, samples=48):
    asset = ASSETS[v]
    EXP = f'{ROOT}/art/exports/d2-logs-b/{asset}'
    PRE = f'{ROOT}/art/previews/d2-logs-b/{asset}'
    os.makedirs(PRE + '/turnaround', exist_ok=True)
    b = _load(HERE6 + '/build_dr06.py')
    V = b['set_variant'](v)
    pv = _load(HERE + '/preview_dr.py')
    G = lambda n: bpy.data.objects[n]
    lods = {lv: [G(f'{asset}_LOD{lv}'), G(f'{DET}_LOD{lv}')] for lv in (0, 1, 2)}
    col = G(f'{asset}_Collision')
    dp = _load(HERE + '/dr_pivot.py')
    P = dp['pivot']()
    dp['frame'](asset, False)
    lo, hi = bounds([lods[0][0]])
    dlo, dhi = bounds([lods[0][1]])
    centre_xy = [round((lo[i] + hi[i]) / 2, 3) for i in (0, 1)]
    dp['frame'](asset, True)                  # 量形狀、拍審圖鏡位用建模座標
    val = dict(asset=asset, version=VER, blender=bpy.app.version_string)
    val['bounds_main'] = dict(min=lo, max=hi, dims=[round(hi[i] - lo[i], 4) for i in range(3)])
    val['origin_at_bottom_centre'] = dict(footprint_centre_xy_m=centre_xy, ok=all(abs(c) < .01 for c in centre_xy))
    val['build_origin_in_asset_m'] = [round(-P.x, 4), round(-P.y, 4), 0.0]
    val['bounds_detail'] = dict(min=dlo, max=dhi)
    val['shape_lod0'] = shape(lods[0][0], b, V)
    val['shape_collision'] = shape(col, b, V)
    sp = SPEC[v]
    s0 = val['shape_lod0']
    # 樹幹長：根頸（根盤在 x = 0）到斷口斷面中心（從 +X 沿樹幹中心高往 −X 打到的第一個面，木刺從旁邊過）
    tb = bvh_of(lods[0][0])
    zL = b['trunk_z'](V, V['L'] - .5)
    yL = b['trunk_pts'](V)[-1][1]
    snap = tb.ray_cast(Vector((V['L'] + 6, yL, zL)), Vector((-1, 0, 0)), 12)[0]
    trunk_len = round(snap.x, 3) if snap is not None else None
    val['spec_check'] = dict(spec=sp, trunk_length_root_collar_to_break_m=trunk_len, overall_bbox_x_m=val['bounds_main']['dims'][0],
                             trunk_diameter_mid_m=s0['trunk_diameter_mid_m'],
                             plate_width_m=s0['plate_width_y_m'], plate_height_m=s0['plate_height_m'],
                             length_ok=trunk_len is not None and abs(trunk_len - sp['L']) < .8,
                             diameter_ok=abs(s0['trunk_diameter_mid_m'] - sp['D']) < .25 * sp['D'],
                             plate_ok=abs(s0['plate_width_y_m'] - sp['plate']) < .25 * sp['plate'],
                             note='工作包的 10 m／16 m 是樹幹長（根頸到斷口）；外框 X 另含根盤往後伸的根和斷口往前伸的木刺。徑量的是樹幹中段（0.3–0.9 L）在中心高處的左右寬')
    val['plants_inside_body_lod0'] = plants_inside(lods[0][1], lods[0][0])
    val['buried_depth_m'] = round(-lo[2], 3)
    val['tris'] = {f'LOD{lv}': {o.name: tri(o) for o in lst} for lv, lst in lods.items()}
    val['tris']['collision'] = tri(col)
    val['lod_ratio'] = {f'LOD{lv}': round(sum(tri(o) for o in lods[lv]) / sum(tri(o) for o in lods[0]), 3) for lv in (1, 2)}
    fbx = f'{EXP}/{asset}_{VER}.fbx'
    val['fbx_roundtrip'] = fbx_roundtrip(fbx, asset)
    val['fbx_dims_match'] = all(abs(a - c) < .01 for a, c in zip(sorted(val['fbx_roundtrip']['lod0_dimensions_m']), sorted(val['bounds_main']['dims'])))
    tex = {}
    for f in sorted(os.listdir(EXP + '/Textures')):
        im = bpy.data.images.load(f'{EXP}/Textures/{f}', check_existing=False)
        tex[f] = list(im.size)
        bpy.data.images.remove(im)
    val['textures_px'] = tex
    upm = bpy.context.scene.get('dr02_uv_per_m', 0) * 2048
    val['texel_px_per_m'] = round(upm, 1)
    val['hidden_tris_removed_lod0'] = int(bpy.context.scene.get('dr06_hidden_tris_removed', 0))
    val['checks_not_in_this_file'] = [f'Unity 匯入與引擎內外觀：另見 art/previews/d2-logs-b/{asset}/unity/report.txt',
                                      '放進 D2 場景後的同鏡位截圖（場景由核心組擺）', '實機效能、FPS']
    json.dump(val, open(f'{EXP}/validation.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    mats = [bpy.data.materials[f'M_{asset}_{S}'] for S in ('A', 'Leaf')]
    sh = 'Shared/D2Bark_Detail_Normal.png'
    info = {
        'asset': asset, 'version': VER, 'minTier': 'standard', 'detailObjects': [DET],
        'name_zh': NAME_ZH[v], 'slot': SLOT,
        'note': ('一棵老樹連根倒下，躺在地上、陷進土裡約 0.14 R。一頭是翻起來立著的根盤：粗根從樹幹基部包過一座泥丘、往後捲過邊緣，'
                 '貼著朝外那面（原本的根底）往中心收；上半圈幾條斷根伸出去，末端斷成淺色木刺；泥裡卡著石頭、垂著細根鬚；根盤前面一圈翻起的土。'
                 '另一頭斷折，斷口一束長木刺。樹幹是扭轉長稜的老樹皮，側面幾大片剝皮露出風化木；一根往上翹的長斷枝、一兩個短枝樁、兩側層狀菌；'
                 f'頂上厚苔與地衣。樹皮：Poly Haven bark_brown_02 掃描凹凸推進高模幾何再烘焙。{DET}：頂上的蕨、小樹苗、蕈，腳邊的大蕨、闊葉草、蕈、落葉、根盤的細根鬚。'),
        'references': 'art/references/DR06/v001/（Codex 依 D2 設定圖 V1、V4、V5、V6 畫的三視圖、四分之三視圖、細節圖）',
        'budget_per_lod': {f'LOD{lv}': dict(triangles=sum(tri(o) for o in lst), objects=2, objects_without_detail=1, materials=len(mats)) for lv, lst in lods.items()},
        'texture_resolution_px': {**tex, sh: [1024, 1024], sh.replace('_Normal', '_Albedo'): [1024, 1024]},
        'units': 'meters', 'front': '-Y (Blender)：看樹幹的側面；根盤在 -X、斷口在 +X',
        'up': '+Z (Blender); FBX exported Y-up, -Z forward, transforms baked',
        'origin': '底部中心：LOD0 本體外框 XY 的中心正下方的地面；z = 0 是地面，陷進土裡的部分在 z < 0',
        'dimensions_m': val['bounds_main']['dims'], 'bounds_min_m': lo, 'bounds_max_m': hi,
        'shape': val['shape_lod0'], 'spec_check': val['spec_check'],
        'lods': val['tris'], 'lod_rule': 'LOD0 不刪細節；LOD1／LOD2：本體每件各自 collapse 再刪藏起來的面，植物整件 collapse；照實得比例修正，本體＋植物合計約為 LOD0 的 50%／15%；面積 0 的三角形匯出前刪掉',
        'materials': [m.name for m in mats], 'objects_per_lod': 2,
        'material_note': f'本體一個物件、一個材質 M_{asset}_A（一組貼圖 2048）；{DET} 一個材質 M_{asset}_Leaf（同一組貼圖，雙面；葉、蕈、細枝、根鬚畫在圖集最下面一條）',
        'uv': {'UV0': 'UVMap：烘焙圖集，所有 UV 島同比例（%.1f px/m）、不旋轉' % upm, 'UV1': 'TileUV：樹皮件是每 2.6 m 重複的樹皮 UV，其他件同 UV0'},
        'unity': {'shader': 'Universal Render Pipeline/Lit', 'detail_normal': sh, 'detail_albedo': sh.replace('_Normal', '_Albedo'),
                  'detail_mask': 'Albedo.png 的 alpha（1 = 樹皮，0 = 苔和葉）', 'detail_tiling_on_uv0': round(mats[0].get('unity_detail_tiling', 0), 2),
                  'mask_map': 'MaskURP.png（R metal、G AO、A smoothness）'},
        'collision': f'{asset}_Collision: MeshCollider (convex off), renderer hidden；樹幹（8 邊、每 1 m 一環、兩端封口）、粗的那根斷枝、根盤泥丘（16×10 的球）',
        'sockets_blender_xyz': {},
        'build_origin_m': val['build_origin_in_asset_m'],
        'build_origin_note': '建模座標（根盤在 x = 0、樹幹沿 +x、斷口在 x = L）的原點在本資產座標裡的位置；Unity 檢查把模型放在它的負值，審圖鏡位才對得上',
        'length_build_m': V['L'], 'plate_x_build_m': round(b['plate_geom'](V)['xp'], 3),
        'review_cams_build_xyz': [dict(name=k, **{'from': [round(c, 3) for c in f], 'at': [round(c, 3) for c in t]}, lens_mm=ln)
                                  for k, (f, t, ln) in b['_views'](V).items()],
        'external_assets': [{'name': 'bark_brown_02', 'source': 'https://polyhaven.com/a/bark_brown_02', 'license': 'CC0'}],
        'files_sha256': {f: sha(f'{EXP}/{f}') for f in sorted(os.listdir(EXP)) if f.endswith(('.fbx', '.glb'))},
    }
    json.dump(info, open(f'{EXP}/model_info.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    if render:
        L = V['L']
        pv['setup'](samples=samples, fog=False)
        hm = bpy.data.objects.get('DR_Human_1p75m')
        if hm:
            hm.location = (L * .45, -V['R'] * 2.2, .875)
        show({o.name for o in lods[0]})
        vj = []
        cz = V['RP'] * .5
        dist = L * 1.6 + 3
        for nm, d in VIEWS:
            dv = Vector(d).normalized()
            loc = P + Vector((0, 0, cz)) + dv * (dist if nm != '09_top' else dist + 4)
            pv['shot'](f'{PRE}/turnaround/{nm}.png', tuple(loc), tuple(P + Vector((0, 0, cz))), 50, res=(1024, 1024))
            vj.append(dict(name=nm, direction=list(d), camera=[round(c, 3) for c in loc - P], lens_mm=50, file=f'turnaround/{nm}.png', mesh='LOD0'))
        json.dump(dict(asset=asset, version=VER, views=vj, note=f'遊戲模型 LOD0＋{DET}，烘焙貼圖；白柱是 1.75 m 人形尺；相機座標以原點（底部中心）為準'),
                  open(f'{PRE}/turnaround/views.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
        pv['setup'](samples=samples)
        hm = bpy.data.objects.get('DR_Human_1p75m')
        if hm:
            hm.location = (L * .45, -V['R'] * 2.2, .875)
        vw = b['_views'](V)
        for lv in (0, 1, 2):
            show({o.name for o in lods[lv]})
            loc, tgt, lens = vw['side']
            pv['shot'](f'{PRE}/{asset}_LOD{lv}_side.png', loc, tgt, lens, res=(1536, 864))
        show({lods[1][0].name})
        loc, tgt, lens = vw['side']
        pv['shot'](f'{PRE}/{asset}_LOD1_nodetail_side.png', loc, tgt, lens, res=(1536, 864))
        show({o.name for o in lods[0]})
        for n in ('tq', 'plate', 'plateq', 'snap', 'back', 'sap'):
            loc, tgt, lens = vw[n]
            pv['shot'](f'{PRE}/{asset}_LOD0_{n}.png', loc, tgt, lens, res=(1536, 864))
    dp['frame'](asset, False)
    print(json.dumps({k: val[k] for k in ('bounds_main', 'origin_at_bottom_centre', 'shape_lod0', 'spec_check', 'buried_depth_m', 'tris', 'lod_ratio',
                                          'fbx_dims_match', 'texel_px_per_m', 'plants_inside_body_lod0')}, indent=1, ensure_ascii=False))
    print(val['fbx_roundtrip'])
    return val


if __name__ == '__main__' and '--' in sys.argv:
    a = sys.argv[sys.argv.index('--') + 1:]
    report(a[0] if a else 'B', render='norender' not in a)
    print('REPORT_DONE')
