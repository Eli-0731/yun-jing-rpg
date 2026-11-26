# DR08 長滿蕈和苔的朽木（三種）：量尺寸（長、寬、高、陷進土裡多深、擋不擋人）、剝皮比例、FBX 回匯、十視圖、LOD 比較、model_info.json／validation.json。
# 和 report_dr05.py 同一套寫法。在做完 game_dr08 的 Blender 裡（或背景）：
#   blender -b art/source/d2-logs-b/blend/DR08_RottenLog_A_v001.blend --python art/source/d2-logs-b/report_dr08.py -- A
import bpy, math, os, sys, json, hashlib
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = 'D:/yun-jing-d2-logs/art/source/d2-roots-b'
HERE6 = 'D:/yun-jing-d2-logs/art/source/d2-logs-b'
ROOT = 'D:/yun-jing-d2-logs'
VER = 'v001'
ASSETS = {'A': 'DR08_RottenLog_A', 'B': 'DR08_RottenLog_B', 'C': 'DR08_RottenLog_C'}
DET = 'Detail_DR08_Plants'
NAME_ZH = {'A': '長滿蕈和苔的朽木 A：短截（長 2 m、徑約 0.6 m）', 'B': '長滿蕈和苔的朽木 B：中段裂開（長 3.5 m、徑約 0.7 m）',
           'C': '長滿蕈和苔的朽木 C：長條、一頭朽空（長 5 m、徑約 0.8 m）'}
SPEC = {'A': dict(L=2.0, D=.90), 'B': dict(L=3.5, D=1.0), 'C': dict(L=5.0, D=1.10)}          # 工作包長 2–5 m；粗細照參考圖人形尺（1.75 m）估：樹幹高約人的一半
SLOT = 'D2 古樹空地四周的林地（工作包：三種共 6 處擺放；長 2–5 m）'
VIEWS = [('01_front', (0, -1, .06)), ('02_right', (1, 0, .06)), ('03_rear', (0, 1, .06)), ('04_left', (-1, 0, .06)),
         ('05_front_right', (1, -1, .45)), ('06_rear_right', (1, 1, .45)), ('07_rear_left', (-1, 1, .45)),
         ('08_front_left', (-1, -1, .45)), ('09_top', (0, -.001, 1)), ('10_high_front', (0, -1, 1))]
NOTE = {
    'A': '一截 2 m 長的短朽木，扁扁地趴在地上、半陷進土裡，兩頭斷口碎、塌，中段頂上塌陷一個洞。',
    'B': '3.5 m 長的朽木，中段頂上裂開、塌下去，一頭是撕裂的斷口、一根根長短不齊的淺灰褐木刺往外伸。',
    'C': '5 m 長的朽木，長長一條低低地陷在土裡，一頭朽空（看得到裡面），頂上兩個塌掉的洞。',
}


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


def bvh_of(o, wood_only=False):
    """wood_only：不含第二槽（立在地上的大香菇），量樹幹本身的頂高、外寬用。"""
    return BVHTree.FromPolygons([o.matrix_world @ v.co for v in o.data.vertices],
                                [tuple(p.vertices) for p in o.data.polygons if not (wood_only and p.material_index == 1)])


def _odd(tree, p, d):
    k, q = 0, p.copy()
    for _ in range(60):
        h = tree.ray_cast(q, d, 20)
        if h[0] is None:
            break
        k += 1
        q = h[0] + d * 1e-4
    return k % 2 == 1


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
        if d < -.02 and (q - loc).length > .06 and not all(_odd(t, q, Vector(dd).normalized()) for dd in ((0, 0, 1), (1, .13, .07), (-.11, 1, .05))):
            continue                                    # 最近的面剛好背對、三個方向打出去都是偶數次：其實在外面
        in2 += d < -.02
        in5 += d < -.05
    return dict(vertices_checked=n, inside_body_over_2cm=in2, inside_body_over_5cm=in5)


def shape(o, b, V):
    """（建模座標：x = 0 到 L、樹幹沿 +X）每 0.25 m：從上往下打量頂高，軸心高處從兩側橫打量外寬；
    橫著走過去擋不擋（0.15／0.30／0.45 m 高；人物跨得過的台階約 0.3–0.45 m）。頂高、外寬只量木頭（不含大香菇），擋不擋含全部。"""
    t = bvh_of(o, wood_only=True)
    tf = bvh_of(o)
    L = V['L']
    rows = []
    for i in range(1, int(L / .25)):
        x = i * .25
        ay, az = b['axis_y'](V, x), b['axis_z'](V, x)
        tops = [t.ray_cast(Vector((x, ay + dy, 20)), Vector((0, 0, -1)), 25)[0] for dy in (-.1, 0, .1)]
        top = max((h.z for h in tops if h is not None), default=None)
        l_ = t.ray_cast(Vector((x, ay - 15, max(az, .08))), Vector((0, 1, 0)), 30)[0]
        r_ = t.ray_cast(Vector((x, ay + 15, max(az, .08))), Vector((0, -1, 0)), 30)[0]
        w = (r_.y - l_.y) if (l_ and r_) else 0.0
        rows.append((x, round(top, 3) if top is not None else None, round(w, 3)))
    mids = [r for r in rows if .15 * L < r[0] < .85 * L and r[2] > 0]
    blocked = []
    for i in range(int(L / .25)):
        x = .125 + i * .25
        blocked.append([tf.ray_cast(Vector((x, -15, z)), Vector((0, 1, 0)), 30)[0] is not None for z in (.15, .30, .45)])
    tz = [r[1] for r in mids if r[1] is not None]
    return dict(top_z_m_every_0p25m=[r[1] for r in rows], outer_width_m_every_0p25m=[r[2] for r in rows],
                outer_width_mid_m=round(sum(r[2] for r in mids) / max(1, len(mids)), 3),
                top_z_mid_m=dict(min=min(tz), max=max(tz), mean=round(sum(tz) / len(tz), 3)) if tz else None,
                blocked_fraction_at_0p15_0p30_0p45m=[round(sum(r[k] for r in blocked) / len(blocked), 3) for k in range(3)])


def peel_fraction():
    """高模外殼側面（不含朝上 0.62 以上那片苔）剝掉樹皮的面積比例。"""
    o = bpy.data.objects.get('Trunk')
    if o is None or 'Peel' not in o.data.attributes:
        return None
    pe = np.empty(len(o.data.vertices), np.float32)
    o.data.attributes['Peel'].data.foreach_get('value', pe)
    a = p_ = 0.0
    for f in o.data.polygons:
        if f.normal.z > .62:
            continue
        a += f.area
        if pe[list(f.vertices)].mean() > .5:
            p_ += f.area
    return round(p_ / max(a, 1e-9), 3)


def high_counts():
    out = {}
    for n in ('Cubes', 'RotBlocks', 'Mycel', 'Brackets', 'Slab1', 'Debris', 'Soil'):
        o = bpy.data.objects.get(n)
        if o is not None:
            out[n] = dict(tris=tri(o))
    return out


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
        if c.name.startswith('DR08_'):
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
    b = _load(HERE6 + '/build_dr08.py')
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
    tb = bvh_of(lods[0][0])
    L = V['L']
    # 殼長：沿長度每 2 cm 從兩側水平打（離地 0.15、0.25 m，兩側共四條線），打到軸心 1.3 R 以內的就是樹幹殼；取第一個到最後一個的距離，平均。
    # （從兩頭水平打進去、或從上往下打，都會穿進朽空的中心、碎掉的頭、塌掉的中段，量出來太短。）
    xs = []
    for z in (.15, .25):
        for sg in (-1, 1):
            hit_x = []
            for i in range(int((L + 1.0) / .02)):
                x = -.5 + i * .02
                ay = b['axis_y'](V, min(max(x, 0), L))
                h = tb.ray_cast(Vector((x, ay + sg * 5.0, z)), Vector((0, -sg, 0)), 10)[0]
                if h is not None and abs(h.y - ay) < 1.3 * V['R']:
                    hit_x.append(x)
            if hit_x:
                xs.append(hit_x[-1] - hit_x[0])
    shell_len = round(sum(xs) / len(xs), 3) if xs else None
    dims = val['bounds_main']['dims']
    val['spec_check'] = dict(spec=sp, overall_bbox_x_m=dims[0], shell_length_mean_m=shell_len,
                             outer_width_mid_m=s0['outer_width_mid_m'], top_z_mid_m=s0['top_z_mid_m'],
                             length_ok=abs((shell_len or dims[0]) - sp['L']) < .2 * sp['L'] + .3,
                             in_pack_range_2_to_5m=1.8 <= (shell_len or dims[0]) <= 5.5,
                             width_ok=abs(s0['outer_width_mid_m'] - sp['D']) < .25 * sp['D'],
                             blocks_walker=s0['blocked_fraction_at_0p15_0p30_0p45m'][1] > .6,
                             note='工作包：長 2–5 m、三種。長量外框 X（含斷口的木刺、碎屑）；shell_length_mean 是沿長度從兩側水平打（離地 0.15、0.25 m）、打到軸心 1.3 R 內的頭尾距離（四條線平均），length_ok 用它比。'
                                  '外寬量中段（0.15–0.85 L）在軸心高處的左右寬（朽軟塌扁：寬比高大）。頂高是從上往下打到的最高處（含苔）。'
                                  'blocks_walker：0.30 m 高處橫打，六成以上的位置打得到算擋人（要跨過去或繞過去）')
    val['peel_fraction_side_high'] = peel_fraction()
    val['high_parts'] = high_counts()
    val['plants_inside_body_lod0'] = plants_inside(lods[0][1], lods[0][0])
    val['buried_depth_m'] = round(-lo[2], 3)
    val['tris'] = {f'LOD{lv}': {o.name: tri(o) for o in lst} for lv, lst in lods.items()}
    val['tris']['collision'] = tri(col)
    val['lod_ratio'] = {f'LOD{lv}': round(sum(tri(o) for o in lods[lv]) / sum(tri(o) for o in lods[0]), 3) for lv in (1, 2)}
    fbx = f'{EXP}/{asset}_{VER}.fbx'
    val['fbx_roundtrip'] = fbx_roundtrip(fbx, asset)
    val['fbx_dims_match'] = all(abs(a - c) < .01 for a, c in zip(sorted(val['fbx_roundtrip']['lod0_dimensions_m']), sorted(dims)))
    tex = {}
    SH = f'{ROOT}/art/exports/d2-logs-b/DR08_Shared/Textures'
    for f in sorted(os.listdir(SH)):
        if not f.endswith('.png'):
            continue
        im = bpy.data.images.load(f'{SH}/{f}', check_existing=False)
        tex['DR08_Shared/Textures/' + f] = list(im.size)
        bpy.data.images.remove(im)
    val['textures_px'] = tex
    TL = {'Bark': 1, 'Moss': 2, 'Rot': 2, 'Fibre': 1, 'Inner': 1, 'Soil': 1}
    val['texel_px_per_m'] = {k: 1024 * r for k, r in TL.items()}
    upm = 1024
    val['hidden_tris_removed_lod0'] = int(bpy.context.scene.get('dr06_hidden_tris_removed', 0))
    val['checks_not_in_this_file'] = [f'Unity 匯入與引擎內外觀：另見 art/previews/d2-logs-b/{asset}/unity/report.txt',
                                      '放進 D2 場景後的同鏡位截圖（場景由核心組擺）', '實機效能、FPS']
    json.dump(val, open(f'{EXP}/validation.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    mats = [bpy.data.materials[n] for n in ('M_DR08_Layered', 'M_DR08_Plants')]
    info = {
        'asset': asset, 'version': VER, 'minTier': 'standard', 'detailObjects': [DET],
        'name_zh': NAME_ZH[v], 'slot': SLOT,
        'note': (NOTE[v] + '朽軟了塌扁（斷面寬比高大）。樹皮大半掉了，剩一片片灰褐鱗狀老樹皮；露出的木頭是連成一片的褐腐（深紅褐、裂成小塊紋路，畫在貼圖裡，不是一顆顆方塊），'
                 '旁邊地上一片片剝落的木片、木粉。頂上整條厚苔，兩側往下垂；苔上、腳邊、洞口外一叢叢小褐蕈，洞裡發光小蕈；幾叢大香菇從地上長出菌柄、菌傘斜靠在樹幹側面（不長在木頭上）。'
                 '表面是六層手繪平鋪貼圖（樹皮、苔、褐腐木、撕裂纖維、樹洞內壁、土）用頂點權重混合，A／B／C 共用同一組貼圖和材質。'
                 f'{DET}：手繪植物卡（頂上的蕨、小苗、垂苔、小褐蕈、發光小蕈、腳邊的蕨、落葉）。'),
        'references': 'art/references/DR08/v001/（Codex 依 D2 設定圖 V5、V6 畫的三視圖、四分之三視圖、細節圖）；手繪平鋪貼圖原圖 art/source/d2-logs-b/tex_src_dr08/（Codex 畫）',
        'budget_per_lod': {f'LOD{lv}': dict(triangles=sum(tri(o) for o in lst), objects=2, objects_without_detail=1, materials=len(mats)) for lv, lst in lods.items()},
        'texture_resolution_px': tex,
        'units': 'meters', 'front': '-Y (Blender)：看樹幹的側面；樹幹沿 X',
        'up': '+Z (Blender); FBX exported Y-up, -Z forward, transforms baked',
        'origin': '底部中心：LOD0 本體外框 XY 的中心正下方的地面；z = 0 是地面，陷進土裡的部分在 z < 0',
        'peel_fraction_side': val['peel_fraction_side_high'],
        'dimensions_m': dims, 'bounds_min_m': lo, 'bounds_max_m': hi,
        'shape': val['shape_lod0'], 'spec_check': val['spec_check'],
        'lods': val['tris'], 'lod_rule': 'LOD 每級用同一份路徑重建（不是 decimate）：樹幹環距、每圈點數變粗，層狀菌、撕裂木條、碎屑跟著減；植物卡照組抽掉（LOD1 留約 45%、LOD2 約 12%）；本體＋植物合計約為 LOD0 的 50%／15%',
        'materials': [m.name for m in mats], 'objects_per_lod': 2,
        'material_note': 'A／B／C 共用兩個材質：本體 M_DR08_Layered（六層 1024 手繪平鋪貼圖＋法線）；Detail_DR08_Plants 用 M_DR08_Plants（2048 手繪植物圖集，alpha 裁切、雙面）。樹幹上不長層狀菌（11/23 使用者要求）；大香菇（立在地上、菌傘靠著樹幹）是本體第二槽 M_DR08_Plants，菌傘貼手繪菌蓋圖',
        'uv': {'UV0': 'UVMap：公尺（平鋪貼圖每層各自乘重複次數）；層狀菌、植物卡是植物圖集的 UV', 'UV1': 'Extra：x = 土的權重，y = 頂點 AO（1 = 不遮）',
               'vertex_color': 'RGBA = 苔、褐腐木、撕裂纖維、樹洞內壁的權重；樹皮 = 1 − 其他權重總和'},
        'unity': {'shader': 'YunJing/D2LayeredWood（apps/game/Assets/YunJing/Runtime/D2Logs/D2LayeredWood.shader）', 'textures': 'DR08_Shared/Textures/DR08_{Bark,Moss,Rot,Fibre,Inner,Soil}_{Albedo,Normal}.png',
                  'tiles_per_m': TL, 'plants': 'Universal Render Pipeline/Lit，DR08_Plants_Albedo.png，Alpha Clipping 0.5，Render Face Both'},
        'collision': f'{asset}_Collision: MeshCollider (convex off), renderer hidden；沿樹幹的厚壁管（10 邊、每 0.5 m 一環），要跨過去或繞過去',
        'sockets_blender_xyz': {},
        'build_origin_m': val['build_origin_in_asset_m'],
        'build_origin_note': '建模座標（樹幹沿 +x、x = 0 到 L）的原點在本資產座標裡的位置；Unity 檢查把模型放在它的負值，審圖鏡位才對得上',
        'length_build_m': V['L'],
        'ruler_build_xy': [-.9, .9],
        'review_cams_build_xyz': [dict(name=k, **{'from': [round(c, 3) for c in f], 'at': [round(c, 3) for c in t]}, lens_mm=ln)
                                  for k, (f, t, ln) in b['_views'](V).items()],
        'external_assets': [],
        'files_sha256': {f: sha(f'{EXP}/{f}') for f in sorted(os.listdir(EXP)) if f.endswith(('.fbx', '.glb'))},
    }
    json.dump(info, open(f'{EXP}/model_info.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    if render:
        pv['setup'](samples=samples, fog=False)
        hm = bpy.data.objects.get('DR_Human_1p75m')
        if hm:
            hm.location = (-.9, .9, .875)
        show({o.name for o in lods[0]})
        vj = []
        cz = .25
        dist = L * 1.5 + 2.2
        for nm, d in VIEWS:
            dv = Vector(d).normalized()
            loc = P + Vector((0, 0, cz)) + dv * (dist if nm != '09_top' else dist + 1)
            if hm:                                   # 人形尺站在鏡頭方向的旁邊（不擋樹幹）
                pp = Vector((-dv.y, dv.x, 0))
                pp = pp.normalized() if pp.length > 1e-3 else Vector((0, 1, 0))
                hm.location = P + pp * (L * .5 + 1.0) + Vector((0, 0, .875))
            pv['shot'](f'{PRE}/turnaround/{nm}.png', tuple(loc), tuple(P + Vector((0, 0, cz))), 50, res=(1024, 1024))
            vj.append(dict(name=nm, direction=list(d), camera=[round(c, 3) for c in loc - P], lens_mm=50, file=f'turnaround/{nm}.png', mesh='LOD0'))
        json.dump(dict(asset=asset, version=VER, views=vj, note=f'遊戲模型 LOD0＋{DET}，烘焙貼圖；白柱是 1.75 m 人形尺；相機座標以原點（底部中心）為準'),
                  open(f'{PRE}/turnaround/views.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
        pv['setup'](samples=samples)
        hm = bpy.data.objects.get('DR_Human_1p75m')
        if hm:
            hm.location = (-.9, .9, .875)
        vw = b['_views'](V)
        for lv in (0, 1, 2):
            show({o.name for o in lods[lv]})
            loc, tgt, lens = vw['side']
            pv['shot'](f'{PRE}/{asset}_LOD{lv}_side.png', loc, tgt, lens, res=(1536, 864))
        show({lods[1][0].name})
        loc, tgt, lens = vw['side']
        pv['shot'](f'{PRE}/{asset}_LOD1_nodetail_side.png', loc, tgt, lens, res=(1536, 864))
        show({o.name for o in lods[0]})
        for n in ('tq', 'end', 'endA', 'hole', 'fungi', 'brk', 'back'):
            loc, tgt, lens = vw[n]
            pv['shot'](f'{PRE}/{asset}_LOD0_{n}.png', loc, tgt, lens, res=(1536, 864))
    dp['frame'](asset, False)
    print(json.dumps({k: val[k] for k in ('bounds_main', 'origin_at_bottom_centre', 'spec_check', 'buried_depth_m', 'tris', 'lod_ratio',
                                          'fbx_dims_match', 'texel_px_per_m', 'plants_inside_body_lod0')}, indent=1, ensure_ascii=False))
    print(val['fbx_roundtrip'])
    return val


if __name__ == '__main__' and '--' in sys.argv:
    a = sys.argv[sys.argv.index('--') + 1:]
    report(a[0] if a else 'A', render='norender' not in a)
    print('REPORT_DONE')
