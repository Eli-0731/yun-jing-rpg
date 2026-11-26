# DR01：量尺寸、FBX 回匯檢查、十視圖、LOD 比較、model_info.json／validation.json。
# 在做完 game_dr01 的 Blender 裡：exec(open('report_dr01.py').read()); report()
import bpy, math, os, json, hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = 'D:/yun-jing-d2-roots/art/source/d2-roots-b'
ROOT = os.path.abspath(HERE + '/../../..').replace('\\', '/')
ASSET, VER = 'DR01_RootArch', 'v003'
EXP = f'{ROOT}/art/exports/d2-roots-b/{ASSET}'
PRE = f'{ROOT}/art/previews/d2-roots-b/{ASSET}'
VIEWS = [('01_front', (0, -1, .06)), ('02_right', (1, 0, .06)), ('03_rear', (0, 1, .06)), ('04_left', (-1, 0, .06)),
         ('05_front_right', (1, -1, .45)), ('06_rear_right', (1, 1, .45)), ('07_rear_left', (-1, 1, .45)),
         ('08_front_left', (-1, -1, .45)), ('09_top', (0, -.001, 1)), ('10_high_front', (0, -1, 1))]


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


def clearance(o):
    """拱洞淨高、淨跨（拱身前後約 3 m 厚，取這個厚度裡最低／最窄的地方）；路上有沒有東西擋。"""
    b = bvh_of(o)
    ys = (-1.5, -1, -.5, 0, .5, 1, 1.5)
    heights = {}
    for x in (-4, -3, -2, -1, 0, 1, 2, 3, 4):
        hs = [b.ray_cast(Vector((x, y, .05)), Vector((0, 0, 1)), 30)[3] for y in ys]
        hs = [h for h in hs if h is not None]
        heights[str(x)] = round(min(hs) + .05, 3) if hs else None
    spans = {}
    for z in (.3, 1.0, 2.0, 3.0, 4.0):
        l = [h for h in (b.ray_cast(Vector((0, y, z)), Vector((-1, 0, 0)), 30)[3] for y in ys) if h is not None]
        r = [h for h in (b.ray_cast(Vector((0, y, z)), Vector((1, 0, 0)), 30)[3] for y in ys) if h is not None]
        spans[str(z)] = round(min(l) + min(r), 3) if l and r else None
    # 路（寬 2.2 m，沿 Y 從 -16 到 16）上方 2.2 m 內有沒有幾何
    blocked = 0
    for i in range(65):
        y = -16 + i * .5
        for x in (-1.1, -.55, 0, .55, 1.1):
            if b.ray_cast(Vector((x, y, .02)), Vector((0, 0, 1)), 2.2)[0] is not None:
                blocked += 1
    hv = [heights[k] for k in ('-2', '-1', '0', '1', '2')]
    sv = [spans[k] for k in ('0.3', '1.0', '2.0', '3.0')]
    return dict(clear_height_m_at_x=heights, clear_span_m_at_z=spans, path_2p2m_blocked_samples=blocked,
                clear_height_min_over_central_4m=min(hv), clear_span_min_ground_to_3m=min(sv),
                meets_pack_8m_x_5m=bool(min(hv) >= 5.0 and min(sv) >= 8.0 and blocked == 0))


def foot_spread(o):
    """兩腳的根離拱腳落地點最遠多遠（工作包：往外散 12–15 m）。"""
    bd = _load('build_dr01.py')
    out = {}
    for nm, t, sg in (('west', 0.0, -1), ('east', 1.0, 1)):
        c = bd['centre'](t)
        d = 0.0
        for v in o.data.vertices:
            p = o.matrix_world @ v.co
            if p.x * sg > abs(c.x) and p.z < 1.5:
                d = max(d, math.hypot(p.x - c.x, p.y - c.y))
        out[nm] = round(d, 2)
    return out


def fbx_roundtrip(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    bpy.context.view_layer.update()
    m0 = [o for o in new if o.type == 'MESH' and o.name.split('.')[0] == f'{ASSET}_LOD0']
    lo, hi = bounds(m0)
    rep = dict(objects=sorted(o.name.split('.')[0] for o in new), lod0_dimensions_m=[round(hi[i] - lo[i], 4) for i in range(3)],
               sockets={o.name.split('.')[0]: [round(v, 4) for v in o.matrix_world.translation] for o in new if o.name.startswith('Socket_')},
               uv_layers=[u.name for u in m0[0].data.uv_layers] if m0 else [], materials=sorted({s.material.name.split('.')[0] for o in new if o.type == 'MESH' for s in o.material_slots if s.material}))
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    return rep


def show(names):
    for cn in ('DR01_High', 'DR01_Game', 'DR01_Low'):
        c = bpy.data.collections.get(cn)
        if c:
            c.hide_render = False
            for o in c.objects:
                o.hide_render = o.hide_viewport = o.name not in names


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def report(render=True, samples=48):
    os.makedirs(PRE + '/turnaround', exist_ok=True)
    pv = _load('preview_dr.py')
    G = lambda n: bpy.data.objects[n]
    lods = {lv: [G(f'{ASSET}_LOD{lv}'), G(f'Detail_DR01_Plants_LOD{lv}')] for lv in (0, 1, 2)}
    col = G(f'{ASSET}_Collision')
    lo, hi = bounds([lods[0][0]])
    dlo, dhi = bounds([lods[0][1]])
    val = dict(asset=ASSET, version=VER, blender=bpy.app.version_string)
    val['bounds_main'] = dict(min=lo, max=hi, dims=[round(hi[i] - lo[i], 4) for i in range(3)])
    val['bounds_detail'] = dict(min=dlo, max=dhi)
    val['opening_lod0'] = clearance(lods[0][0])
    val['opening_collision'] = clearance(col)
    val['foot_root_spread_m'] = foot_spread(lods[0][0])
    val['buried_depth_m'] = round(-lo[2], 3)
    val['tris'] = {f'LOD{lv}': {o.name: tri(o) for o in lst} for lv, lst in lods.items()}
    val['tris']['collision'] = tri(col)
    val['lod_ratio'] = {f'LOD{lv}': round(sum(tri(o) for o in lods[lv]) / sum(tri(o) for o in lods[0]), 3) for lv in (1, 2)}
    fbx = f'{EXP}/{ASSET}_{VER}.fbx'
    val['fbx_roundtrip'] = fbx_roundtrip(fbx)
    val['fbx_dims_match'] = all(abs(a - b) < .01 for a, b in zip(sorted(val['fbx_roundtrip']['lod0_dimensions_m']), sorted(val['bounds_main']['dims'])))
    tex = {}
    for f in sorted(os.listdir(EXP + '/Textures')):
        im = bpy.data.images.load(f'{EXP}/Textures/{f}', check_existing=False)
        tex[f] = list(im.size)
        bpy.data.images.remove(im)
    sh = f'{ROOT}/art/exports/d2-roots-b/Shared/D2Bark_Detail_Normal.png'
    im = bpy.data.images.load(sh, check_existing=False)
    shared = {'Shared/D2Bark_Detail_Normal.png': list(im.size)}
    bpy.data.images.remove(im)
    im = bpy.data.images.load(sh.replace('_Normal', '_Albedo'), check_existing=False)
    shared['Shared/D2Bark_Detail_Albedo.png'] = list(im.size)
    bpy.data.images.remove(im)
    val['textures_px'] = tex
    val['checks_not_in_this_file'] = ['Unity 匯入與引擎內外觀：另見 art/previews/d2-roots-b/DR01_RootArch/unity/report.txt',
                                      '放進 D2 場景後的同鏡位截圖（場景由核心組擺）', '實機效能、FPS']
    json.dump(val, open(f'{EXP}/validation.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    mats = [bpy.data.materials[f'M_{ASSET}_{S}'] for S in ('A', 'B', 'C', 'D', 'Leaf')]
    mat = mats[0]
    info = {
        'asset': ASSET, 'version': VER, 'minTier': 'standard', 'detailObjects': ['Detail_DR01_Plants'],
        'name_zh': '南入口大根拱', 'slot': 'D2_AncientTree_SouthEntrance (10,167)，拱朝南北',
        'note': 'v003 交叉尖拱：兩條巨根各自從一隻腳拱起，在路中央上方約 7.3 m 交叉，根梢越過對方搭在對面拱肩上（左根在南面、右根在北面）；'
                '每條根是三股粗細不一的根互絞，左根比右根粗；兩腳各有實心根座、一條條板根和扇形散根，'
                '朝外的大板根從拱腿半腰掃到地面，尾端鑽進土裡。樹皮：Poly Haven bark_brown_02 掃描凹凸推進高模幾何再烘焙。'
                '苔是鼓起來的苔墊（做在高模幾何和材質上），拱頂正面背面的上半邊披著一層。'
                'Detail_DR01_Plants：拱頂的蕨、心形葉小叢、垂藤，根腳的蕨和心形葉。',
        'budget_per_lod': {f'LOD{lv}': dict(triangles=sum(tri(o) for o in lst), objects=2, objects_without_detail=1, materials=len(mats)) for lv, lst in lods.items()},
        'texture_resolution_px': {**tex, **shared},
        'units': 'meters', 'front': '-Y (Blender)，從南邊看；路沿 Y 穿過拱洞',
        'up': '+Z (Blender); FBX exported Y-up, -Z forward, transforms baked',
        'origin': '拱洞正下方地面；z = 0 是地面，根尾鑽土的部分在 z < 0',
        'dimensions_m': val['bounds_main']['dims'], 'bounds_min_m': lo, 'bounds_max_m': hi,
        'opening': val['opening_lod0'], 'foot_root_spread_m': val['foot_root_spread_m'],
        'lods': val['tris'], 'lod_rule': 'LOD0 不刪細節；LOD1 collapse 50%；LOD2 collapse 15%',
        'materials': [m.name for m in mats], 'objects_per_lod': 2,
        'material_note': '本體一個物件、四個材質槽（A–D 四組貼圖，各 2048）；Detail_DR01_Plants 一個材質 M_DR01_RootArch_Leaf（用 A 組貼圖，雙面）。四組 UV 同比例，細節貼圖 Tiling 相同',
        'uv': {'UV0': 'UVMap：烘焙圖集（四組），所有 UV 島同比例（%.1f px/m）、同方向' % (bpy.context.scene.get('dr01_uv_per_m', 0) * 2048),
               'UV1': 'TileUV：每 2.6 m 重複的樹皮 UV'},
        'unity': {'shader': 'Universal Render Pipeline/Lit', 'detail_normal': 'Shared/D2Bark_Detail_Normal.png', 'detail_albedo': 'Shared/D2Bark_Detail_Albedo.png', 'detail_mask': '各組 Albedo.png 的 alpha（1 = 樹皮，0 = 苔和葉）',
                  'detail_tiling_on_uv0': round(mat.get('unity_detail_tiling', 0), 2), 'mask_map': '各組 MaskURP.png（R metal、G AO、A smoothness）'},
        'collision': f'{ASSET}_Collision: MeshCollider (convex off), renderer hidden；只含半徑 0.32 m 以上的根',
        'sockets_blender_xyz': {o.name: [round(v, 3) for v in o.matrix_world.translation] for o in bpy.data.objects if o.name.startswith('Socket_')},
        'external_assets': [{'name': 'bark_brown_02', 'source': 'https://polyhaven.com/a/bark_brown_02', 'license': 'CC0'}],
        'files_sha256': {f: sha(f'{EXP}/{f}') for f in sorted(os.listdir(EXP)) if f.endswith(('.fbx', '.glb'))},
    }
    json.dump(info, open(f'{EXP}/model_info.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    if render:
        pv['setup'](samples=samples, fog=False)
        show({o.name for o in lods[0]})
        vj = []
        for nm, d in VIEWS:
            dv = Vector(d).normalized()
            dist = 52 if nm != '09_top' else 60
            loc = Vector((0, 0, 2.6)) + dv * dist
            pv['shot'](f'{PRE}/turnaround/{nm}.png', tuple(loc), (0, 0, 2.6), 50, res=(1024, 1024))
            vj.append(dict(name=nm, direction=list(d), camera=[round(v, 3) for v in loc], lens_mm=50, file=f'turnaround/{nm}.png', mesh='LOD0'))
        json.dump(dict(asset=ASSET, version=VER, views=vj, note='遊戲模型 LOD0＋Detail_DR01_Plants，烘焙貼圖；白柱是 1.75 m 人形尺'),
                  open(f'{PRE}/turnaround/views.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
        pv['setup'](samples=samples)
        for lv in (0, 1, 2):
            show({o.name for o in lods[lv]})
            loc, tgt, lens = pv['VIEWS']['V2']
            pv['shot'](f'{PRE}/{ASSET}_LOD{lv}_V2cam.png', loc, tgt, lens, res=(1536, 864))
        show({lods[1][0].name})
        loc, tgt, lens = pv['VIEWS']['V2']
        pv['shot'](f'{PRE}/{ASSET}_LOD1_nodetail_V2cam.png', loc, tgt, lens, res=(1536, 864))
        show({o.name for o in lods[0]})
        for n in ('tq', 'back', 'bark', 'footL'):
            loc, tgt, lens = pv['VIEWS'][n]
            pv['shot'](f'{PRE}/{ASSET}_LOD0_{n}.png', loc, tgt, lens, res=(1536, 864))
        # 對照設定圖 V2 用：加上陪襯（神木替身、霧、前景的蕨和苔石，都不是交付物件），看拱洞有沒有框住神木
        _load('preview_context.py')['context']()
        loc, tgt, lens = pv['VIEWS']['V2']
        pv['shot'](f'{PRE}/{ASSET}_LOD0_V2cam_context.png', loc, tgt, lens, res=(1536, 864))
        loc, tgt, lens = pv['VIEWS']['V2core']          # 核心組 root_arch.py 的 V2 鏡位（往上抬、3:2）
        pv['shot'](f'{PRE}/{ASSET}_LOD0_V2core_context.png', loc, tgt, lens, res=(1536, 1024))
    print(json.dumps({k: val[k] for k in ('bounds_main', 'opening_lod0', 'foot_root_spread_m', 'buried_depth_m', 'tris', 'lod_ratio', 'fbx_dims_match')}, indent=1))
    print(val['fbx_roundtrip'])
    return val
