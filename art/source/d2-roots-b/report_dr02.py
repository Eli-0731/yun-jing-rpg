# DR02 板根牆模組：量尺寸、拱下暗縫、FBX 回匯檢查、十視圖、LOD 比較、model_info.json／validation.json。
# 在做完 game_dr02 的 Blender 裡：r = 載入此檔; r['report']('A')
import bpy, math, os, json, hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = 'D:/yun-jing-d2-roots/art/source/d2-roots-b'
ROOT = os.path.abspath(HERE + '/../../..').replace('\\', '/')
VER = 'v001'
NAME_ZH = {'A': '板根牆・高拱', 'B': '板根牆・低伏', 'C': '板根牆・分岔'}
NOTE = {
    'A': '中段離地拱起，底下留一道約 1 m 高的暗縫（人走不進去），再往細頭鑽回土裡。',
    'B': '貼著地面蛇行，1.5–2 m 高，一路有小根往兩側爬下去抓住地面。',
    'C': '粗頭往前分成 Y 字兩條：一條拱起來越過另一條，另一條貼地，各自鑽進土裡。',
}
VIEWS = [('01_front', (0, -1, .06)), ('02_right', (1, 0, .06)), ('03_rear', (0, 1, .06)), ('04_left', (-1, 0, .06)),
         ('05_front_right', (1, -1, .45)), ('06_rear_right', (1, 1, .45)), ('07_rear_left', (-1, 1, .45)),
         ('08_front_left', (-1, -1, .45)), ('09_top', (0, -.001, 1)), ('10_high_front', (0, -1, 1))]
SHOTS = {
    'front': ((0.0, -17.0, 1.6), (0.0, 0.0, 1.4), 30),
    'tq': ((-11.0, -12.0, 3.2), (0.5, 0.0, 1.3), 28),
    'end': ((-16.0, -1.0, 1.6), (0.0, 0.0, 1.5), 35),
    'eye': ((-3.0, -6.5, 1.65), (1.5, 0.5, 1.3), 22),
    'back': ((2.0, 16.0, 2.2), (0.0, 0.0, 1.4), 30),
    'bark': ((-1.5, -3.4, 1.6), (-2.5, -.3, 1.6), 50),
}


# 下面這幾個 DR03（report_dr03.py）會換掉
ASSET_FMT = 'DR02_RootWall_{v}'
BUILD = 'build_dr02.py'
DET_NAME = 'Detail_DR02_Plants'
COL_BIG = .32               # 和 game_dr02.COL_BIG 一樣（只寫進 model_info 的說明）
SLOT = 'D2 空地外圈一圈，約 14 件首尾相接圍成弧（A／B／C 混用、可鏡像）'
NOTE_HEAD = ('神木的板根延伸出去的樣子：一頭粗（從土裡斜著冒出來，最高）、一頭細鑽進土裡。整條是一塊立起來的內芯板根加上八到十二股'
             '慢慢扭轉的根絞成一束，斷面底寬頂尖；有幾股半路離開這一束，往旁邊爬下去鑽進土裡。')
FRONT_TXT = '-Y (Blender)；根沿 +X 走，粗頭在 -X、細頭在 +X'
ORIGIN_TXT = '整條根（含頭尾鑽土的部分）中點正下方的地面；z = 0 是地面，鑽土的部分在 z < 0'
TURN_DIST = 30


def _load(n):
    p = f'{HERE}/{n}'
    g = {'__file__': p, '__name__': n[:-3]}
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
    """植物有沒有穿進根裡：地面以上的植物頂點，離根本體最近的表面、在表面內側超過 2 cm／5 cm 的有幾個。"""
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
    return dict(vertices_checked=n, inside_root_over_2cm=in2, inside_root_over_5cm=in5)


def shape(o, b):
    """地面以上的長度、最高點、主根各處的高度；根底下的空隙（A 的暗縫）有多高、人鑽不鑽得過去；橫著穿過這面牆會不會被擋。"""
    t = bvh_of(o)
    above = [o.matrix_world @ v.co for v in o.data.vertices if (o.matrix_world @ v.co).z > .05]
    xs = [p.x for p in above]
    gaps, tops, walls = [], [], []
    for i in range(121):
        tt = .02 + .96 * i / 120
        c = b['centre'](tt)
        if c.z < .2:
            continue
        down = t.ray_cast(Vector((c.x, c.y, 20)), Vector((0, 0, -1)), 25)
        tops.append(round(down[0].z, 3) if down[0] is not None else 0.0)
    # 根底下的空隙：沿主根每 0.25 m，從 0.05 m 起每 5 cm 往 +Y 橫打一條，最低一條被擋到的高度就是那裡看得穿的縫高
    # （根是一束扭股，股與股之間有縫，往上打的射線會從縫鑽進束裡，量出來的是假的；橫打才是人走過去會碰到的）
    for i in range(int((max(xs) - min(xs)) / .25)):
        x = min(xs) + .125 + i * .25
        top = t.ray_cast(Vector((x, 0, 20)), Vector((0, 0, -1)), 25)[0]
        if top is None and t.ray_cast(Vector((x, -15, .6)), Vector((0, 1, 0)), 30)[0] is None:
            continue
        g = 0.0
        while g < 4.0 and t.ray_cast(Vector((x, -15, .05 + g)), Vector((0, 1, 0)), 30)[0] is None:
            g += .05
        if g < 4.0:     # 上面有根蓋住才算縫；整條都沒擋到的是根的盡頭外面
            gaps.append(round(g + .05 if g else 0.0, 3))
    # 橫著穿過牆：沿主根每 0.5 m，在 0.3／1.0／1.7 m 高往 +Y 打，有沒有被擋（暗縫處 0.3 m 那條會穿過去）
    for i in range(int((max(xs) - min(xs)) / .5)):
        x = min(xs) + .25 + i * .5
        row = []
        for z in (.3, 1.0, 1.7):
            row.append(t.ray_cast(Vector((x, -15, z)), Vector((0, 1, 0)), 30)[0] is not None)
        walls.append((round(x, 2), row))
    return dict(length_above_ground_m=round(max(xs) - min(xs), 3), height_max_m=round(max(p.z for p in above), 3),
                gap_under_root_max_m=max(gaps) if gaps else 0.0, top_along_spine_m=[tops[k] for k in range(0, len(tops), 10)],
                walkable_under_1p75m=bool(sum(g >= 1.75 for g in gaps) >= 3),     # 至少 0.75 m 寬都有 1.75 m 高的縫才鑽得過
                blocked_at_1m_fraction=round(sum(r[1] for _, r in walls) / max(1, len(walls)), 3),
                blocked_at_1p7m_fraction=round(sum(r[2] for _, r in walls) / max(1, len(walls)), 3))


def fbx_roundtrip(path, asset):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    bpy.context.view_layer.update()
    m0 = [o for o in new if o.type == 'MESH' and o.name.split('.')[0] == f'{asset}_LOD0']
    lo, hi = bounds(m0)
    rep = dict(objects=sorted(o.name.split('.')[0] for o in new), lod0_dimensions_m=[round(hi[i] - lo[i], 4) for i in range(3)],
               sockets={o.name.split('.')[0]: [round(v, 4) for v in o.matrix_world.translation] for o in new if o.name.startswith('Socket_')},
               uv_layers=[u.name for u in m0[0].data.uv_layers] if m0 else [], materials=sorted({s.material.name.split('.')[0] for o in new if o.type == 'MESH' for s in o.material_slots if s.material}))
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    return rep


def show(names):
    for cn in ('DR02_High', 'DR02_Game', 'DR02_Low'):
        c = bpy.data.collections.get(cn)
        if c:
            c.hide_render = False
            for o in c.objects:
                o.hide_render = o.hide_viewport = o.name not in names


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def report(v, render=True, samples=48):
    asset = ASSET_FMT.format(v=v)
    EXP = f'{ROOT}/art/exports/d2-roots-b/{asset}'
    PRE = f'{ROOT}/art/previews/d2-roots-b/{asset}'
    os.makedirs(PRE + '/turnaround', exist_ok=True)
    b = _load(BUILD)
    b['set_variant'](v)
    pv = _load('preview_dr.py')
    G = lambda n: bpy.data.objects[n]
    DET = DET_NAME
    lods = {lv: [G(f'{asset}_LOD{lv}'), G(f'{DET}_LOD{lv}')] for lv in (0, 1, 2)}
    col = G(f'{asset}_Collision')
    lo, hi = bounds([lods[0][0]])
    dlo, dhi = bounds([lods[0][1]])
    val = dict(asset=asset, version=VER, blender=bpy.app.version_string)
    val['bounds_main'] = dict(min=lo, max=hi, dims=[round(hi[i] - lo[i], 4) for i in range(3)])
    val['bounds_detail'] = dict(min=dlo, max=dhi)
    val['shape_lod0'] = shape(lods[0][0], b)
    val['shape_collision'] = shape(col, b)
    val['plants_inside_root_lod0'] = plants_inside(lods[0][1], lods[0][0])
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
    val['checks_not_in_this_file'] = [f'Unity 匯入與引擎內外觀：另見 art/previews/d2-roots-b/{asset}/unity/report.txt',
                                      '放進 D2 場景後的同鏡位截圖（場景由核心組擺）', '實機效能、FPS']
    json.dump(val, open(f'{EXP}/validation.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    mats = [bpy.data.materials[f'M_{asset}_{S}'] for S in ('A', 'Leaf')]
    mat = mats[0]
    sh = 'Shared/D2Bark_Detail_Normal.png'
    info = {
        'asset': asset, 'version': VER, 'minTier': 'standard', 'detailObjects': [DET],
        'name_zh': NAME_ZH[v], 'slot': SLOT,
        'note': NOTE_HEAD + NOTE[v] +
                f'樹皮：Poly Haven bark_brown_02 掃描凹凸推進高模幾何再烘焙；苔是鼓起來的苔墊。{DET}：根上的蕨、心形葉小叢，兩端的蕨和心形葉。',
        'budget_per_lod': {f'LOD{lv}': dict(triangles=sum(tri(o) for o in lst), objects=2, objects_without_detail=1, materials=len(mats)) for lv, lst in lods.items()},
        'texture_resolution_px': {**tex, sh: [1024, 1024], sh.replace('_Normal', '_Albedo'): [1024, 1024]},
        'units': 'meters', 'front': FRONT_TXT,
        'up': '+Z (Blender); FBX exported Y-up, -Z forward, transforms baked',
        'origin': ORIGIN_TXT,
        'dimensions_m': val['bounds_main']['dims'], 'bounds_min_m': lo, 'bounds_max_m': hi,
        'shape': val['shape_lod0'],
        'lods': val['tris'], 'lod_rule': 'LOD0 不刪細節；LOD1 collapse 50%；LOD2 collapse 15%',
        'materials': [m.name for m in mats], 'objects_per_lod': 2,
        'material_note': f'本體一個物件、一個材質 M_{asset}_A（一組貼圖 2048）；{DET} 一個材質 M_{asset}_Leaf（同一組貼圖，雙面）',
        'uv': {'UV0': 'UVMap：烘焙圖集，所有 UV 島同比例（%.1f px/m）、同方向' % upm, 'UV1': 'TileUV：每 2.6 m 重複的樹皮 UV'},
        'unity': {'shader': 'Universal Render Pipeline/Lit', 'detail_normal': sh, 'detail_albedo': sh.replace('_Normal', '_Albedo'),
                  'detail_mask': 'Albedo.png 的 alpha（1 = 樹皮，0 = 苔和葉）', 'detail_tiling_on_uv0': round(mat.get('unity_detail_tiling', 0), 2),
                  'mask_map': 'MaskURP.png（R metal、G AO、A smoothness）'},
        'collision': f'{asset}_Collision: MeshCollider (convex off), renderer hidden；只含內芯半徑 {COL_BIG:.2f} m 以上的根（內芯和粗股）',
        'sockets_blender_xyz': {o.name: [round(c, 3) for c in o.matrix_world.translation] for o in bpy.data.objects if o.name.startswith('Socket_')},
        'external_assets': [{'name': 'bark_brown_02', 'source': 'https://polyhaven.com/a/bark_brown_02', 'license': 'CC0'}],
        'files_sha256': {f: sha(f'{EXP}/{f}') for f in sorted(os.listdir(EXP)) if f.endswith(('.fbx', '.glb'))},
    }
    json.dump(info, open(f'{EXP}/model_info.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    if render:
        pv['setup'](samples=samples, fog=False)
        hm = bpy.data.objects.get('DR_Human_1p75m')
        if hm:
            hm.location = (-1.0, -3.0, .875)
        show({o.name for o in lods[0]})
        vj = []
        cz = 1.2
        for nm, d in VIEWS:
            dv = Vector(d).normalized()
            dist = TURN_DIST if nm != '09_top' else TURN_DIST + 4
            loc = Vector((0, 0, cz)) + dv * dist
            pv['shot'](f'{PRE}/turnaround/{nm}.png', tuple(loc), (0, 0, cz), 50, res=(1024, 1024))
            vj.append(dict(name=nm, direction=list(d), camera=[round(c, 3) for c in loc], lens_mm=50, file=f'turnaround/{nm}.png', mesh='LOD0'))
        json.dump(dict(asset=asset, version=VER, views=vj, note=f'遊戲模型 LOD0＋{DET}，烘焙貼圖；白柱是 1.75 m 人形尺'),
                  open(f'{PRE}/turnaround/views.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
        pv['setup'](samples=samples)
        hm = bpy.data.objects.get('DR_Human_1p75m')
        if hm:
            hm.location = (-1.0, -3.0, .875)
        for lv in (0, 1, 2):
            show({o.name for o in lods[lv]})
            loc, tgt, lens = SHOTS['front']
            pv['shot'](f'{PRE}/{asset}_LOD{lv}_front.png', loc, tgt, lens, res=(1536, 864))
        show({lods[1][0].name})
        loc, tgt, lens = SHOTS['front']
        pv['shot'](f'{PRE}/{asset}_LOD1_nodetail_front.png', loc, tgt, lens, res=(1536, 864))
        show({o.name for o in lods[0]})
        for n in ('tq', 'end', 'eye', 'back', 'bark'):
            loc, tgt, lens = SHOTS[n]
            pv['shot'](f'{PRE}/{asset}_LOD0_{n}.png', loc, tgt, lens, res=(1536, 864))
    print(json.dumps({k: val[k] for k in ('bounds_main', 'shape_lod0', 'shape_collision', 'buried_depth_m', 'tris', 'lod_ratio', 'fbx_dims_match', 'texel_px_per_m', 'plants_inside_root_lod0')}, indent=1))
    print(val['fbx_roundtrip'])
    return val
