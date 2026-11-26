# DR07 巨樹樁：量尺寸（樹幹徑、斷口高低、根頸張開多寬、樹洞內徑、水面多深、殼厚、剝皮比例、擋不擋人）、FBX 回匯檢查、十視圖、
# LOD 比較、model_info.json／validation.json。和 report_dr05.py 同一套寫法。
# 在做完 game_dr07 的 Blender 裡（或背景）：blender -b <DR07_GiantStump_A_v001.blend> --python report_dr07.py -- A
import bpy, math, os, sys, json, hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = 'D:/yun-jing-d2-logs/art/source/d2-roots-b'
HERE6 = 'D:/yun-jing-d2-logs/art/source/d2-logs-b'
ROOT = 'D:/yun-jing-d2-logs'
VER = 'v001'
ASSETS = {'A': 'DR07_GiantStump_A', 'B': 'DR07_GiantStump_B'}
DET = 'Detail_DR07_Plants'
NAME_ZH = {'A': '巨樹樁 A（徑 2.5 m，矮邊 1.35 m、斷刺最高 2 m）', 'B': '巨樹樁 B（徑 3.5 m，矮邊 1.6 m、斷刺最高 3 m）'}
SPEC = {'A': dict(D=2.5, H=(1.2, 3.0)), 'B': dict(D=3.5, H=(1.2, 3.0))}
SLOT = 'D2 古樹空地四周的林地（工作包：兩種共擺 4 個）'
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


def shape(o, b, V, col=False):
    """（建模座標：樹幹沿 +Z、軸心在原點附近）
    樹幹徑：1.0 m 高處從四個方向往軸心打，兩兩相減；斷口頂：每 10° 在殼壁中間（內外半徑的平均）從上往下打；
    根頸：0.05 m 高處從 16 個方向往軸心打，最外的距離 × 2；樹洞：在矮邊下 0.3 m 從軸心往外打 8 個方向；水面：軸心往下打；
    殼厚 = 外半徑 − 內半徑（1.0 m 高）；人橫穿（0.3／1.0 m 高、三條線）擋不擋。"""
    t = bvh_of(o)
    H0, H1 = V['H']
    cx, cy = b['axis_xy'](V, 1.0)
    c1 = Vector((cx, cy, 1.0))
    outer = {}
    for nm, d in (('x', Vector((1, 0, 0))), ('y', Vector((0, 1, 0)))):
        p = t.ray_cast(c1 + d * 12, -d, 24)[0]
        q = t.ray_cast(c1 - d * 12, d, 24)[0]
        outer[nm] = round((p - q).length, 3) if (p and q) else None
    tops = []
    for k in range(36):
        a = math.radians(k * 10)
        z = H1 + 2
        rm = (b['out_r'](V, H0) + b['in_r'](V, H0)) / 2
        cx_, cy_ = b['axis_xy'](V, H0)
        h = t.ray_cast(Vector((cx_ + math.cos(a) * rm, cy_ + math.sin(a) * rm, z)), Vector((0, 0, -1)), z + 2)[0]
        tops.append(round(h.z, 3) if h else None)
    cx0, cy0 = b['axis_xy'](V, 0.0)
    spread = []
    for k in range(16):
        a = 2 * math.pi * k / 16
        d = Vector((math.cos(a), math.sin(a), 0))
        st = Vector((cx0, cy0, .05)) + d * 12
        h = t.ray_cast(st, -d, 12)[0]
        if h:
            spread.append((h - Vector((cx0, cy0, .05))).length)
    zi = H0 - .30
    cxi, cyi = b['axis_xy'](V, zi)
    ci = Vector((cxi, cyi, zi))
    inner = []
    walls = []
    for k in range(8):
        a = 2 * math.pi * k / 8
        d = Vector((math.cos(a), math.sin(a), 0))
        h = t.ray_cast(ci, d, 6)[0]
        if h:
            inner.append((h - ci).length)
        hi_ = t.ray_cast(c1, d, 6)[0]
        ho = t.ray_cast(c1 + d * 12, -d, 12)[0]
        if hi_ and ho:
            walls.append(round((ho - c1).length - (hi_ - c1).length, 3))
    pool = t.ray_cast(Vector((cx, cy, H0 - .05)), Vector((0, 0, -1)), 4)[0]
    blocked = []
    for off in (-.5, 0.0, .5):
        y = cy0 + off * V['R']
        blocked.append([t.ray_cast(Vector((-12, y, z)), Vector((1, 0, 0)), 24)[0] is not None for z in (.3, 1.0)])
    vt = [x for x in tops if x is not None]
    return dict(trunk_diameter_at_1m_xy_m=outer,
                trunk_diameter_at_1m_m=round(sum(v for v in outer.values() if v) / max(1, sum(1 for v in outer.values() if v)), 3),
                rim_top_z_every_10deg=tops, rim_low_m=min(vt) if vt else None, rim_high_m=max(vt) if vt else None,
                root_collar_spread_diameter_m=round(2 * max(spread), 3) if spread else None,
                hollow_inner_diameter_m=round(2 * sum(inner) / len(inner), 3) if inner else None,
                pool_or_floor_z_m=round(pool.z, 3) if pool else None,
                wall_thickness_at_1m_m=dict(min=min(walls), max=max(walls), mean=round(sum(walls) / len(walls), 3)) if walls else None,
                blocked_at_0p3_1p0m_three_lines=blocked)


def peel_fraction():
    o = bpy.data.objects.get('Trunk')
    if o is None or 'Peel' not in o.data.attributes:
        return None
    import numpy as np
    pe = np.empty(len(o.data.vertices), np.float32)
    o.data.attributes['Peel'].data.foreach_get('value', pe)
    a = p_ = 0.0
    for f in o.data.polygons:
        if f.center.z < .45 or abs(f.normal.z) > .6:
            continue
        a += f.area
        if pe[list(f.vertices)].mean() > .5:
            p_ += f.area
    return round(p_ / max(a, 1e-9), 3)


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
        if c.name.startswith('DR07_'):
            c.hide_render = False
            for o in c.objects:
                o.hide_render = o.hide_viewport = o.name not in names


def water_check(asset, b, V, P, body):
    """水面模型（water_dr07.py）：在不在樹洞裡、高度對不對、邊緣有沒有藏進內壁、比洞底高多少；FBX 回匯外框。"""
    ws = [bpy.data.objects.get(f'{asset}_water_LOD{i}') for i in range(3)]
    if not all(ws):
        return None
    info = json.loads(bpy.context.scene.get('dr07_water', '{}'))
    w0 = ws[0]
    wv = {i for p in w0.data.polygons if p.material_index == 0 for i in p.vertices}      # 只看水面（第二個材質槽是浮葉）
    co = [w0.matrix_world @ w0.data.vertices[i].co for i in wv]
    ax, ay = b['axis_xy'](V, V['pool'])
    c = Vector((ax, ay, V['pool']))
    zs = [q.z for q in co]
    rr = [math.hypot(q.x - c.x, q.y - c.y) for q in co]
    # 水邊：在水面高度（上方 2 mm）往外打到內壁，水邊要比打到的距離遠（藏進牆裡、沒有縫），但不能穿出外殼
    t = bvh_of(body)
    hidden, inside_shell, n = 0, 0, 0
    for k in range(32):
        a = 2 * math.pi * k / 32
        d = Vector((math.cos(a), math.sin(a), 0))
        h = t.ray_cast(c + Vector((0, 0, .002)), d, 6)[0]
        far = max((q - c).dot(d) for q in co)
        n += 1
        if h is not None and far > (h - c - Vector((0, 0, .002))).length:
            hidden += 1
        if far < b['out_r'](V, V['pool']) * .95:
            inside_shell += 1
    floor = t.ray_cast(c + Vector((0, 0, .5)), Vector((0, 0, -1)), 3)
    fl = None
    if floor[0] is not None:
        # 往下打先打到本體的洞底（水面不在本體裡）
        fl = floor[0].z
    rep = dict(model=info, z_m=round(sum(zs) / len(zs), 3), flat=max(zs) - min(zs) < 1e-4, radius_max_m=round(max(rr), 3),
               edge_hidden_in_wall_dirs=f'{hidden}/{n}', edge_inside_outer_shell_dirs=f'{inside_shell}/{n}',
               floor_z_under_centre_m=round(fl, 3) if fl is not None else None,
               depth_over_floor_m=round(V['pool'] - fl, 3) if fl is not None else None,
               tris={f'LOD{i}': tri(o) for i, o in enumerate(ws)})
    rep['ok'] = rep['flat'] and abs(rep['z_m'] - V['pool']) < .005 and hidden == n and inside_shell == n and (rep['depth_over_floor_m'] or 0) > .05
    return rep


def water_roundtrip(path, asset):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    bpy.context.view_layer.update()
    m0 = [o for o in new if o.type == 'MESH' and o.name.split('.')[0] == f'{asset}_water_LOD0']
    lo, hi = bounds(m0)
    rep = dict(objects=sorted(o.name.split('.')[0] for o in new), lod0_min_m=lo, lod0_max_m=hi,
               uv_layers=[u.name for u in m0[0].data.uv_layers] if m0 else [])
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    return rep


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def report(v, render=True, samples=48):
    asset = ASSETS[v]
    EXP = f'{ROOT}/art/exports/d2-logs-b/{asset}'
    PRE = f'{ROOT}/art/previews/d2-logs-b/{asset}'
    os.makedirs(PRE + '/turnaround', exist_ok=True)
    b = _load(HERE6 + '/build_dr07.py')
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
    val['shape_collision'] = shape(col, b, V, col=True)
    sp = SPEC[v]
    s0 = val['shape_lod0']
    D = s0['trunk_diameter_at_1m_m']
    val['spec_check'] = dict(spec=sp, trunk_diameter_at_1m_m=D, rim_low_m=s0['rim_low_m'], rim_high_m=s0['rim_high_m'],
                             root_collar_spread_ratio=round(s0['root_collar_spread_diameter_m'] / D, 2) if D else None,
                             diameter_ok=abs(D - sp['D']) < .15 * sp['D'],
                             height_ok=(s0['rim_low_m'] or 0) >= sp['H'][0] and (s0['rim_high_m'] or 9) <= sp['H'][1] + .1,
                             hollow_deep_enough_for_water=s0['pool_or_floor_z_m'] is not None and V['pool'] < (s0['rim_low_m'] or 0) - .4 and s0['pool_or_floor_z_m'] < V['pool'] - .05,
                             note='工作包：徑 2.5／3.5 m、高 1.2–3 m；斷口參差、中心朽空積水、根頸張開抓地。'
                                  '樹幹徑量 1.0 m 高處（根頸往上已收回）X、Y 兩向平均；高度量殼壁中間每 10° 從上往下打到的斷口頂（最低＝矮邊、最高＝斷刺）；'
                                  '根頸張開量 0.05 m 高處最外的板根到軸心距離 × 2')
    val['peel_fraction_side_high'] = peel_fraction()
    val['plants_inside_body_lod0'] = plants_inside(lods[0][1], lods[0][0])
    val['buried_depth_m'] = round(-lo[2], 3)
    val['tris'] = {f'LOD{lv}': {o.name: tri(o) for o in lst} for lv, lst in lods.items()}
    val['tris']['collision'] = tri(col)
    val['lod_ratio'] = {f'LOD{lv}': round(sum(tri(o) for o in lods[lv]) / sum(tri(o) for o in lods[0]), 3) for lv in (1, 2)}
    val['water'] = water_check(asset, b, V, P, lods[0][0])
    wf = f'{EXP}/{asset}_water_{VER}.fbx'
    if os.path.exists(wf):
        val['water_fbx_roundtrip'] = water_roundtrip(wf, asset)
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
    cx, cy = b['axis_xy'](V, 0.0)
    val['stump_build'] = dict(axis_x=round(cx, 3), axis_y=round(cy, 3), rim_low=s0['rim_low_m'], pool_z=V['pool'], radius=V['R'])
    val['checks_not_in_this_file'] = [f'Unity 匯入與引擎內外觀：另見 art/previews/d2-logs-b/{asset}/unity/report.txt',
                                      '放進 D2 場景後的同鏡位截圖（場景由核心組擺）', '實機效能、FPS']
    json.dump(val, open(f'{EXP}/validation.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    mats = [bpy.data.materials[f'M_{asset}_{S}'] for S in ('A', 'Leaf')]
    sh = 'Shared/D2Bark_Detail_Normal.png'
    info = {
        'asset': asset, 'version': VER, 'minTier': 'standard', 'detailObjects': [DET],
        'name_zh': NAME_ZH[v], 'slot': SLOT,
        'note': ('巨樹很久以前折斷後留下的樹樁（不是鋸的）：頂上參差的斷口，鉸點那側幾片高高撕裂的木板、細長木刺，另一側低、朽爛；'
                 '斷面一圈圈年輪層、翻卷的朽木片。中心朽空成一個深碗，碗底一層泥、落葉，牆腳長苔；內壁是朽爛的紅褐纖維木，縱向纖維溝、朽洞。'
                 '積水是另一個模型（<件名>_water_v001.fbx）：有水＝本體＋水面，沒水＝只放本體。'
                 '根頸往外張，板根扭著鑽進土裡，根間細根、土和小石塊。外面深灰褐長稜老樹皮，一片剝皮露出灰白風化木；斷口上緣和板根上長苔、地衣，一側層狀菌。'
                 '樹皮：Poly Haven bark_brown_02 掃描凹凸推進高模幾何再烘焙。'
                 f'{DET}：斷口上的小蕨，腳邊的蕨、闊葉草、蕈，根上的蕈，地上和樹洞底的落葉。'),
        'references': 'art/references/DR07/v001/（Codex 依 D2 設定圖 V1、V4（另參考 V5、V6）畫的三視圖、四分之三視圖、細節圖）',
        'budget_per_lod': {f'LOD{lv}': dict(triangles=sum(tri(o) for o in lst), objects=2, objects_without_detail=1, materials=len(mats)) for lv, lst in lods.items()},
        'texture_resolution_px': {**tex, sh: [1024, 1024], sh.replace('_Normal', '_Albedo'): [1024, 1024]},
        'units': 'meters', 'front': '-Y (Blender)；斷口最高的木板朝 hinge 方位角（stump_build 之外另記在 hinge_azimuth_deg）',
        'hinge_azimuth_deg': round(math.degrees(V['hinge']), 1),
        'up': '+Z (Blender); FBX exported Y-up, -Z forward, transforms baked',
        'origin': '底部中心：LOD0 本體外框 XY 的中心正下方的地面；z = 0 是地面，鑽進土裡的根在 z < 0',
        'stump_build': val['stump_build'], 'peel_fraction_side': val['peel_fraction_side_high'],
        'dimensions_m': val['bounds_main']['dims'], 'bounds_min_m': lo, 'bounds_max_m': hi,
        'shape': val['shape_lod0'], 'spec_check': val['spec_check'],
        'lods': val['tris'], 'lod_rule': 'LOD0 不刪細節；LOD1／LOD2：本體每件各自 collapse 再刪藏起來的面，植物整件 collapse；照實得比例修正，本體＋植物合計約為 LOD0 的 50%／15%；面積 0 的三角形匯出前刪掉',
        'materials': [m.name for m in mats], 'objects_per_lod': 2,
        'material_note': f'本體一個物件、一個材質 M_{asset}_A（一組貼圖 2048）；{DET} 一個材質 M_{asset}_Leaf（同一組貼圖，雙面）。'
                         f'水面另一個 FBX、一個材質 M_{asset}_Water（沒有貼圖；Unity 換成 YunJing/CreekFlowWater）',
        'water': dict(**(val['water'] or {}).get('model', {}),
                      unity_shader='YunJing/CreekFlowWater（apps/game/Assets/YunJing/Runtime/CreekRepair/CreekFlowWater.shader，使用者青溪水工 B 的水）：'
                                   '靜水模式 _Still = 1、_Speed 0.03（同 CreekRepairSceneBuilder 的 Field_StillWater），樹洞水另設 _StillColour 茶褐 (0.05, 0.036, 0.02)、_AlphaMid／_AlphaBank 0.6，'
                                   '看得到洞底的泥和落葉；_StillColour 是這次在著色器加的可調值，預設等於原本田裡積水的灰綠，F01 不變；隨 _Time 慢慢起伏，不用腳本',
                      blender_preview='Blender 審圖用 M_<件名>_Water：Cycles 單面透射（IOR 1.333、粗糙度 0.02），透射染茶褐、兩層很淡的小波，看得到底下的泥和落葉、斜看映出內壁'),
        'states': {'wet': f'有水：本體 {asset}_{VER}.fbx ＋ 水面 {asset}_water_{VER}.fbx（同一個位置、同一個旋轉）',
                   'dry': f'沒水：只放本體 {asset}_{VER}.fbx（樹洞底是泥、落葉，牆腳長苔；水面那個 FBX 不放）'},
        'uv': {'UV0': 'UVMap：烘焙圖集，所有 UV 島同比例（%.1f px/m）、不旋轉' % upm, 'UV1': 'TileUV：樹皮件是每 2.6 m 重複的樹皮 UV，其他件同 UV0'},
        'unity': {'shader': 'Universal Render Pipeline/Lit', 'detail_normal': sh, 'detail_albedo': sh.replace('_Normal', '_Albedo'),
                  'detail_mask': 'Albedo.png 的 alpha（1 = 樹皮，0 = 苔和葉）', 'detail_tiling_on_uv0': round(mats[0].get('unity_detail_tiling', 0), 2),
                  'mask_map': 'MaskURP.png（R metal、G AO、A smoothness）'},
        'collision': f'{asset}_Collision: MeshCollider (convex off), renderer hidden；樹幹一個實心 12 邊柱（到矮邊 0.92 高，頂上封平，人掉不進樹洞）＋根頸一圈 0.38 m 高的矮台',
        'sockets_blender_xyz': {},
        'build_origin_m': val['build_origin_in_asset_m'],
        'build_origin_note': '建模座標（樹幹軸心在原點附近、沿 +Z）的原點在本資產座標裡的位置；Unity 檢查把模型放在它的負值，審圖鏡位才對得上',
        'length_build_m': V['H'][1],
        'ruler_build_xy': [round(V['R'] * 2.4, 3), round(-V['R'] * 1.2, 3)],
        'review_cams_build_xyz': [dict(name=k, **{'from': [round(c, 3) for c in f], 'at': [round(c, 3) for c in t]}, lens_mm=ln)
                                  for k, (f, t, ln) in b['_views'](V).items()],
        'external_assets': [{'name': 'bark_brown_02', 'source': 'https://polyhaven.com/a/bark_brown_02', 'license': 'CC0'}],
        'files_sha256': {f: sha(f'{EXP}/{f}') for f in sorted(os.listdir(EXP)) if f.endswith(('.fbx', '.glb'))},
    }
    json.dump(info, open(f'{EXP}/model_info.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    if render:
        pv['setup'](samples=samples, fog=False)
        hm = bpy.data.objects.get('DR_Human_1p75m')
        if hm:
            hm.location = (V['R'] * 2.4, -V['R'] * 1.2, .875)
        W = {f'{asset}_water_LOD{i}': f'{asset}_water_LOD{i}' for i in range(3)}
        wet = lambda lv: {o.name for o in lods[lv]} | ({f'{asset}_water_LOD{lv}'} if bpy.data.objects.get(f'{asset}_water_LOD{lv}') else set())
        cz = V['H'][1] * .45
        dist = V['R'] * 5.5 + 3
        for sub, names, label in (('turnaround', wet(0), '有水（本體＋水面）'), ('turnaround_dry', {o.name for o in lods[0]}, '沒水（只有本體）')):
            os.makedirs(f'{PRE}/{sub}', exist_ok=True)
            show(names)
            vj = []
            for nm, d in VIEWS:
                dv = Vector(d).normalized()
                loc = Vector((0, 0, cz)) + dv * (dist if nm != '09_top' else dist + 2)
                pv['shot'](f'{PRE}/{sub}/{nm}.png', tuple(loc), (0, 0, cz), 50, res=(1024, 1024))
                vj.append(dict(name=nm, direction=list(d), camera=[round(c, 3) for c in loc - P], lens_mm=50, file=f'{sub}/{nm}.png', mesh='LOD0'))
            json.dump(dict(asset=asset, version=VER, state=label, views=vj,
                           note=f'遊戲模型 LOD0＋{DET}，烘焙貼圖；{label}；水面在 Blender 是預覽材質（遊戲裡是 CreekFlowWater）；白柱是 1.75 m 人形尺；相機座標以原點（底部中心）為準'),
                      open(f'{PRE}/{sub}/views.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
        pv['setup'](samples=samples)
        hm = bpy.data.objects.get('DR_Human_1p75m')
        if hm:
            hm.location = (V['R'] * 2.4, -V['R'] * 1.2, .875)
        vw = b['_views'](V)
        for lv in (0, 1, 2):
            show(wet(lv))
            loc, tgt, lens = vw['front']
            pv['shot'](f'{PRE}/{asset}_LOD{lv}_front.png', loc, tgt, lens, res=(1536, 864))
        show({lods[1][0].name})
        loc, tgt, lens = vw['front']
        pv['shot'](f'{PRE}/{asset}_LOD1_nodetail_front.png', loc, tgt, lens, res=(1536, 864))
        show(wet(0))
        for n in ('tq', 'hinge', 'into', 'roots', 'rim', 'back'):
            loc, tgt, lens = vw[n]
            pv['shot'](f'{PRE}/{asset}_LOD0_{n}.png', loc, tgt, lens, res=(1536, 864))
        show({o.name for o in lods[0]})
        for n in ('tq', 'into', 'rim'):
            loc, tgt, lens = vw[n]
            pv['shot'](f'{PRE}/{asset}_LOD0_{n}_dry.png', loc, tgt, lens, res=(1536, 864))
    dp['frame'](asset, False)
    print(json.dumps({k: val[k] for k in ('bounds_main', 'origin_at_bottom_centre', 'spec_check', 'buried_depth_m', 'tris', 'lod_ratio',
                                          'fbx_dims_match', 'texel_px_per_m', 'plants_inside_body_lod0', 'peel_fraction_side_high')}, indent=1, ensure_ascii=False))
    print(json.dumps(val['shape_lod0'], ensure_ascii=False))
    print(val['fbx_roundtrip'])
    return val


if __name__ == '__main__' and '--' in sys.argv:
    a = sys.argv[sys.argv.index('--') + 1:]
    report(a[0] if a else 'A', render='norender' not in a)
    print('REPORT_DONE')
