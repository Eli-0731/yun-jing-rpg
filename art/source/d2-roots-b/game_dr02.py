# DR02 板根牆模組的遊戲用模型（由 game_dr01.py 改寫，流程相同）：同一份路徑做低模 → 拆 UV → 把高模烘焙到低模 → 遊戲用植物 →
# LOD1／LOD2 → 碰撞殼 → FBX／GLB。三種（A 高拱、B 低伏、C 分岔）各自一件：configure('A'); run_all()。
# 一件約 12 m，一組 2048 貼圖（Albedo／Normal／ORM／MaskURP）就有 DR01 四組的紋素密度；Detail_DR02_Plants 另一個雙面材質。
import bpy, bmesh, math, os, sys, json, importlib, random
import numpy as np
from mathutils import Vector

HERE = 'D:/yun-jing-d2-roots/art/source/d2-roots-b'
if HERE not in sys.path:
    sys.path.insert(0, HERE)
ROOT = os.path.abspath(HERE + '/../../..').replace('\\', '/')
VER = 'v001'
SIZE = 2048
STRIP = 96 / 2048           # 圖集最下面一條留給葉子（蕨羽片、心形葉）
DET = 'Detail_DR02_Plants'   # 可關掉的小植物（畫質標準檔不顯示），照 quality-tiers-v1 命名 Detail_*
SEG = 6.0                   # 每條根沿長度每 6 m 切一個 UV 島
LOWRES = (.30, 8, 20, 1.0)   # 低模取樣：沿長度每 0.30 m 一環；細根 8 邊，粗根照周長加到最多 20 邊（空地外圈要擺約 14 件，面數壓低）
SETS = 'A'                  # 一組貼圖
OVERLAP = 2.5               # 首尾相接時重疊的長度（見 finish 的接口）
VARIANT = ASSET = EXP = TEX = WORKTEX = None


def configure(v):
    """切換到 A／B／C 其中一件：輸出資料夾、烘焙中間檔都分開。"""
    global VARIANT, ASSET, EXP, TEX, WORKTEX
    VARIANT = v
    ASSET = f'DR02_RootWall_{v}'
    EXP = f'{ROOT}/art/exports/d2-roots-b/{ASSET}'
    TEX = EXP + '/Textures'
    WORKTEX = os.environ.get('DR_WORK2', 'D:/yun-jing-cache/dr02-work/') + f'bake_{v}'     # 烘焙中間檔，不進版本庫


def _build():
    b = _load('build_dr02.py')
    b['set_variant'](VARIANT)
    return b


def _load(n):
    p = f'{HERE}/{n}'
    g = {'__file__': p, '__name__': n[:-3]}
    exec(compile(open(p, encoding='utf-8').read(), p, 'exec'), g)
    return g


def _select(objs, active):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active


def _join(objs, name):
    _select(objs, objs[0])
    with bpy.context.temp_override(active_object=objs[0], object=objs[0], selected_objects=objs, selected_editable_objects=objs):
        bpy.ops.object.join()
    objs[0].name = name
    objs[0].data.name = name
    return objs[0]


def _coll(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


# ---------------------------------------------------------------- 低模 + UV
def make_low():
    b = _build()
    for nm in ('DR02_Low', 'DR02_Game', 'DR02_LowFull'):
        c = bpy.data.collections.get(nm)
        if c:
            for o in list(c.objects):
                bpy.data.objects.remove(o, do_unlink=True)
    objs = b['build'](quick=False, name='DR02_Low', low=LOWRES)
    hidden = _hidden_verts(objs)        # 哪些頂點藏在別的根裡或土裡。先不刪：LOD1／LOD2 要用完整的管子各自減面
    # 每條根切成一段段長方形 UV 島
    rects = []
    for oi, o in enumerate(objs):
        rr, ss = list(o['ring_r']), list(o['ring_s'])
        ring = [d.value for d in o.data.attributes['ring'].data]
        live = {ring[p.index] for p in o.data.polygons if not all(hidden[oi][v] for v in p.vertices)}
        nseg = max(1, int(math.ceil(ss[-1] / SEG)))
        per = int(math.ceil((len(ss) - 1) / nseg))
        for si in range(nseg):
            k0, k1 = si * per, min((si + 1) * per, len(ss) - 1)
            if k0 >= k1:
                continue
            if not any(k0 <= k < k1 for k in live):
                continue                      # 這一段整個藏在別的根裡或土裡：不佔圖集
            w = 2 * math.pi * float(np.mean(rr[k0:k1 + 1]))
            rects.append(dict(o=oi, k0=k0, k1=k1, w=max(w, .12), h=ss[k1] - ss[k0], s0=ss[k0]))
    pad = 6.0 / SIZE

    # 整條根分到四組貼圖裡的一組（照面積平均分；A 組最下面一條留給葉子）。四組同一個比例，共用的細節貼圖才能用同一個 Tiling
    area = {}
    for r in rects:
        area[r['o']] = area.get(r['o'], 0.0) + r['w'] * r['h']
    cap = [1 - STRIP if i == 0 else 1.0 for i in range(len(SETS))]
    load = [0.0] * len(SETS)
    aset = {}
    for oi in sorted(area, key=lambda k: -area[k]):
        i = min(range(len(SETS)), key=lambda k: load[k] / cap[k])
        aset[oi] = i
        load[i] += area[oi]
    for r in rects:
        r['a'] = aset[r['o']]

    def pack(f):
        for ai in range(len(SETS)):
            order = sorted((r for r in rects if r['a'] == ai), key=lambda r: -r['h'])
            x, y, rowh = pad, (STRIP if ai == 0 else 0.0) + pad, 0.0
            for r in order:
                w, h = r['w'] * f, r['h'] * f
                if x + w + pad > 1:
                    x, y, rowh = pad, y + rowh + pad, 0.0
                if y + h + pad > 1:
                    return False
                r['x'], r['y'], r['f'] = x, y, f
                x += w + pad
                rowh = max(rowh, h)
        return True
    lo, hi = 1e-4, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if pack(mid):
            lo = mid
        else:
            hi = mid
    pack(lo)
    print('atlas scale', round(lo * SIZE, 1), 'px per metre,', len(rects), 'islands; bark area per set (m2)', [round(v, 1) for v in load])
    bmats = [m for m, _ in _bake_mats()]
    bpy.context.scene['dr02_uv_per_m'] = lo
    by = {}
    for r in rects:
        by.setdefault(r['o'], []).append(r)
    for oi, o in enumerate(objs):
        me = o.data
        bm = bmesh.new()
        bm.from_mesh(me)
        up = bm.loops.layers.uv['Param']
        ut = bm.loops.layers.uv['UV']
        ua = bm.loops.layers.uv.new('Atlas')
        fr = bm.faces.layers.int['ring']
        segs = by.get(oi, [])
        for f in bm.faces:
            k = f[fr]
            r = next((q for q in segs if q['k0'] <= k < q['k1']), None)
            if r is None and segs and k >= 0:
                # 這一段整個藏起來、沒有自己的 UV 島：借最近那一段的邊緣（LOD1／LOD2 減面後萬一露出一角，顏色還是樹皮）
                r = min(segs, key=lambda q: min(abs(k - q['k0']), abs(k - q['k1'])))
            for lp in f.loops:
                if r is None:
                    lp[ua].uv = (pad * .5, STRIP + pad * .5)
                else:
                    a, s = lp[up].uv
                    lp[ua].uv = (r['x'] + a * r['w'] * r['f'], r['y'] + min(max(s - r['s0'], 0.0), r['h']) * r['f'])
        # UV0 = 圖集、UV1 = 每 2.6 m 重複的樹皮 UV（給 Detail Normal）
        for f in bm.faces:
            for lp in f.loops:
                t = lp[ut].uv.copy()
                lp[ut].uv = lp[ua].uv
                lp[up].uv = t
        bm.loops.layers.uv.remove(ua)
        bm.to_mesh(me)
        bm.free()
        me.uv_layers['UV'].name = 'UVMap'
        me.uv_layers['Param'].name = 'TileUV'
        for p in me.polygons:
            p.use_smooth = True
        me.materials.clear()
        for m in bmats:
            me.materials.append(m)
        me.polygons.foreach_set('material_index', [aset.get(oi, 0)] * len(me.polygons))      # 材質 A–D = 這條根烘到哪一組貼圖
    for o in objs:
        for k in ('ring_r', 'ring_s'):
            if k in o:
                del o[k]
    # 留一份完整的管子（已經有 UV 和材質編號）給 LOD1／LOD2：各自減面之後再刪藏起來的面，根和根的交界才不會露出破洞
    full = _coll('DR02_LowFull')
    for o in objs:
        c = o.copy()
        c.data = o.data.copy()
        c.name = c.data.name = o.name.replace('DR02_Low_', 'DR02_Full_')
        for cc in list(c.users_collection):
            cc.objects.unlink(c)
        full.objects.link(c)
    full.hide_render = full.hide_viewport = True
    objs, gone = _delete_hidden(objs, hidden)
    bpy.context.scene['dr02_hidden_tris_removed'] = gone
    groups = _colour(objs)
    outs = []
    for gi, idx in enumerate(groups):
        srcs = [objs[i].name.replace('DR02_Low_', 'DR02_') for i in idx]
        go = _join([objs[i] for i in idx], f'DR02_LowG{gi:02d}') if len(idx) > 1 else objs[idx[0]]
        go.name = go.data.name = f'DR02_LowG{gi:02d}'
        go['srcs'] = srcs
        outs.append(go)
    print('bake groups', len(outs), [len(g) for g in groups], 'bark tris', sum(len(p.vertices) - 2 for o in outs for p in o.data.polygons))
    return outs


def _hidden_verts(objs, margin=.03, zcut=-.5):
    """每個物件一個布林陣列：這個頂點鑽在別條根裡面超過 margin，或在地面以下 zcut 公尺。
    根和根是互相穿過去的（三股主根、根座、嵌在上面的小根），穿進去的部分永遠看不到，留著只是白佔面數和貼圖。
    判斷用的是完整（封閉）的管子，所以外面看得到的那一層不會被算進去。"""
    from mathutils.bvhtree import BVHTree
    data = []
    for o in objs:
        co = np.array([v.co[:] for v in o.data.vertices])
        t = BVHTree.FromPolygons([Vector(c) for c in co], [tuple(p.vertices) for p in o.data.polygons])
        data.append((co, t, co.min(0), co.max(0)))
    out = []
    for i, o in enumerate(objs):
        co, _, lo_i, hi_i = data[i]
        hide = co[:, 2] < zcut
        for j, (cj, tj, lo, hi) in enumerate(data):
            if j == i or (lo_i > hi).any() or (hi_i < lo).any():
                continue
            for vi in np.nonzero(~hide & (co >= lo).all(1) & (co <= hi).all(1))[0]:
                q = Vector(co[vi])
                loc, nrm, idx, dist = tj.find_nearest(q)
                if loc is not None and dist > margin and (q - loc).dot(nrm) < 0:
                    hide[vi] = True
        out.append(hide)
    return out


def _delete_hidden(objs, hidden):
    """刪掉每個頂點都藏起來的面。回傳（還有面的物件, 刪掉幾個三角面）。"""
    before = after = 0
    keep = []
    for o, hide in zip(objs, hidden):
        bm = bmesh.new()
        bm.from_mesh(o.data)
        before += sum(len(f.verts) - 2 for f in bm.faces)
        dead = [f for f in bm.faces if all(hide[v.index] for v in f.verts)]
        if dead:
            bmesh.ops.delete(bm, geom=dead, context='FACES')
        after += sum(len(f.verts) - 2 for f in bm.faces)
        n = len(bm.faces)
        bm.to_mesh(o.data)
        bm.free()
        if n:
            keep.append(o)
        else:
            bpy.data.objects.remove(o, do_unlink=True)
    print('hidden tris removed', before - after, 'of', before, '; objects', len(keep), 'of', len(objs))
    return keep, before - after


def _cull_hidden(objs, margin=.03, zcut=-.5):
    return _delete_hidden(objs, _hidden_verts(objs, margin, zcut))


def _colour(objs, near=.75):
    """把根分組：同一組裡任兩條根的表面相距都超過 near。靠在一起的根若一起烘焙，射線會打到隔壁那條的樹皮。"""
    from mathutils.kdtree import KDTree
    P, T, B = [], [], []
    for o in objs:
        pts = [o.matrix_world @ v.co for v in o.data.vertices]
        kd = KDTree(len(pts))
        for i, q in enumerate(pts):
            kd.insert(q, i)
        kd.balance()
        a = np.array(pts)
        P.append(pts)
        T.append(kd)
        B.append((a.min(0) - near, a.max(0) + near))
    n = len(objs)
    adj = [set() for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if (B[i][0] > B[j][1]).any() or (B[j][0] > B[i][1]).any():
                continue
            a, b = (i, j) if len(P[i]) <= len(P[j]) else (j, i)
            if any(T[b].find(q)[2] < near for q in P[a][::2]):
                adj[i].add(j)
                adj[j].add(i)
    col = {}
    for i in sorted(range(n), key=lambda k: -len(adj[k])):
        used = {col[j] for j in adj[i] if j in col}
        col[i] = next(c for c in range(n) if c not in used)
    return [[i for i in range(n) if col[i] == c] for c in range(max(col.values()) + 1)]


def join_low():
    """烘焙完：各組合併成 LOD0。"""
    lows = sorted([o for o in bpy.data.collections['DR02_Low'].objects if o.name.startswith('DR02_LowG')], key=lambda o: o.name)
    for o in lows:
        o.hide_render = o.hide_viewport = False
        if 'srcs' in o:
            del o['srcs']
    old = bpy.data.objects.get(f'{ASSET}_LOD0')
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    low = _join(lows, f'{ASSET}_LOD0')
    low.data.uv_layers.active = low.data.uv_layers['UVMap']
    low.data.uv_layers['UVMap'].active_render = True
    g = _coll('DR02_Game')
    for c in list(low.users_collection):
        c.objects.unlink(low)
    g.objects.link(low)
    print('LOD0 bark tris', sum(len(p.vertices) - 2 for p in low.data.polygons))
    return low


# ---------------------------------------------------------------- 烘焙
def _image(name, color):
    im = bpy.data.images.get(name)
    if im:
        bpy.data.images.remove(im)
    im = bpy.data.images.new(name, SIZE, SIZE, alpha=True, float_buffer=False)      # alpha = 烘到的範圍，補邊用
    im.colorspace_settings.name = 'sRGB' if color else 'Non-Color'
    im.pixels.foreach_set(np.zeros(SIZE * SIZE * 4, np.float32))                    # 全透明起頭；烘焙時不清圖（一張圖要分好幾次烘）
    return im


def _bake_mats():
    """烘焙用的四個材質，各指向一張圖：低模每個面的材質決定它烘到哪一組。"""
    out = []
    for S in SETS:
        m = bpy.data.materials.get(f'DR02_BakeTarget_{S}') or bpy.data.materials.new(f'DR02_BakeTarget_{S}')
        m.use_nodes = True
        N = m.node_tree.nodes
        tn = next((n for n in N if n.type == 'TEX_IMAGE'), None) or N.new('ShaderNodeTexImage')
        N.active = tn
        out.append((m, tn))
    return out


def bake(samples=24, log=None, kinds=None):
    """每組低模只對「自己那幾條根」的高模烘焙；AO 另外讓全部高模和地面都在場，根和根之間的暗角才會有。
    低模每個面的材質（A–D）決定它寫到哪一張圖，一次烘焙同時寫四張。"""
    os.makedirs(WORKTEX, exist_ok=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    for nm in ('DR02_Low', 'DR02_High'):          # 集合本身若被關掉渲染，裡面的物件就不能烘焙
        c = bpy.data.collections.get(nm)
        if c:
            c.hide_render = c.hide_viewport = False
    lows = sorted([o for o in bpy.data.collections['DR02_Low'].objects if o.name.startswith('DR02_LowG')], key=lambda o: o.name)
    highs = {o.name: o for o in bpy.data.collections['DR02_High'].objects if not o.name.startswith(('DR02_P_', 'DR02_Q_'))}
    bm_ = _bake_mats()
    for o in lows:
        assert len(o.data.materials) == len(SETS), o.name
        for i, (m, _) in enumerate(bm_):
            o.data.materials[i] = m
    for o in bpy.context.view_layer.objects:
        o.hide_render = True
    for o in list(highs.values()) + lows:
        o.hide_viewport = False
        o.hide_set(False)
    ground = bpy.data.objects.get('DR_Ground')
    out = {}
    for kind, btype, color, kw in (('BaseColor', 'DIFFUSE', True, dict(pass_filter={'COLOR'})), ('Roughness', 'ROUGHNESS', False, {}),
                                   ('Normal', 'NORMAL', False, dict(normal_space='TANGENT')), ('AO', 'AO', False, {})):
        if kinds and kind not in kinds:        # 只重烘其中幾張（例如只改了顏色）
            continue
        ims = []
        for S, (m, tn) in zip(SETS, bm_):
            tn.image = _image(f'{ASSET}_{S}_{kind}', color)
            ims.append(tn.image)
        sc.cycles.samples = samples * 2 if kind == 'AO' else (max(8, samples // 2) if kind == 'BaseColor' else 8)
        if ground:
            ground.hide_render = kind != 'AO'
        for gi, low in enumerate(lows):
            src = [highs[n] for n in low['srcs']]
            for o in highs.values():
                o.hide_render = kind != 'AO'
            for o in src:
                o.hide_render = False
            for o in lows:
                o.hide_render = o is not low
            _select(src + [low], low)
            bpy.ops.object.bake(type=btype, use_selected_to_active=True, cage_extrusion=.30, max_ray_distance=.75, margin=1,
                                margin_type='EXTEND', use_clear=False, **kw)
        for S, im in zip(SETS, ims):
            im.filepath_raw = f'{WORKTEX}/{ASSET}_{S}_{kind}.png'
            im.file_format = 'PNG'
            im.save()
            out[S, kind] = im.filepath_raw
        print('baked', kind)
        if log:
            log('baked ' + kind)
    for o in bpy.context.view_layer.objects:
        o.hide_render = False
    return out


def _dilate(a, n=10, fill=None):
    """UV 島外面補邊：沒烘到的像素（alpha 0）往外抄鄰近像素 n 圈；還是空的填 fill。"""
    rgb = a[..., :3].copy()
    m = a[..., 3] > .5
    for _ in range(n):
        acc = np.zeros_like(rgb)
        cnt = np.zeros(m.shape, np.float32)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            mm = np.roll(m, (dy, dx), (0, 1))
            acc += np.roll(rgb, (dy, dx), (0, 1)) * mm[..., None]
            cnt += mm
        new = (~m) & (cnt > 0)
        rgb[new] = acc[new] / cnt[new][:, None]
        m = m | new
    if fill is not None:
        rgb[~m] = fill
    a[..., :3] = rgb
    a[..., 3] = 1
    return a


def _px(path):
    im = bpy.data.images.load(path, check_existing=False)
    a = np.empty(im.size[0] * im.size[1] * 4, np.float32)
    im.pixels.foreach_get(a)
    return im, a.reshape(im.size[1], im.size[0], 4)


def _save(arr, path, color):
    h, w = arr.shape[:2]
    im = bpy.data.images.new('tmp_save', w, h, alpha=True)
    im.colorspace_settings.name = 'sRGB' if color else 'Non-Color'
    im.pixels.foreach_set(arr.astype(np.float32).ravel())
    im.filepath_raw = path
    im.file_format = 'PNG'
    im.save()
    bpy.data.images.remove(im)


LEAF = {'Ferns': (0.0, .25, (.13, .21, .095), (.27, .37, .18)), 'Leaves': (.25, .5, (.18, .27, .145), (.34, .43, .26))}   # x0, x1, 暗、亮 (sRGB)


def finish_textures():
    """補邊；A 組最下面一條畫上葉子（u 沿葉長、v 橫向：中脈亮、葉緣暗）；每組輸出 Albedo／Normal／ORM／MaskURP 四張。"""
    os.makedirs(TEX, exist_ok=True)
    for f in os.listdir(TEX):
        os.remove(f'{TEX}/{f}')
    h0 = int(STRIP * SIZE)
    half = int(.5 * SIZE)
    for S in SETS:
        leaf = S == SETS[0]
        W = lambda k: f'{WORKTEX}/{ASSET}_{S}_{k}.png'
        im, base = _px(W('BaseColor'))
        cov = base[..., 3] > .5
        base = _dilate(base, fill=base[cov][:, :3].mean(0))
        if leaf:
            for nm, (x0, x1, dark, light) in LEAF.items():
                a, b = int(x0 * SIZE), int(x1 * SIZE)
                u = np.linspace(0, 1, b - a)[None, :]
                v = np.linspace(0, 1, h0)[:, None]
                mid = np.clip(1 - np.abs(v - .5) / .06, 0, 1)
                edge = np.clip((np.abs(v - .5) - .3) / .2, 0, 1)
                veins = (np.sin((u * 9 + np.abs(v - .5) * 1.2) * 2 * math.pi) > .86) * .5
                t = np.clip(.45 + .25 * u + .5 * np.maximum(mid, veins) - .45 * edge, 0, 1)
                for c in range(3):
                    base[:h0, a:b, c] = (dark[c] + (light[c] - dark[c]) * t)
        moss = np.clip((base[..., 1] - (base[..., 0] + base[..., 2]) / 2 - .015) / .05, 0, 1)
        if leaf:
            moss[:h0, :half] = 0                  # 葉子那一條不是苔，不壓暗
        base[..., :3] *= (1 - .12 * moss)[..., None]      # 苔壓暗（引擎裡亮面的苔會偏螢光）；平均值對齊核心組神木 GT01 的苔
        grey = base[..., :3].mean(-1, keepdims=True)
        base[..., :3] += (grey - base[..., :3]) * (.25 * moss)[..., None]
        base[..., 3] = 1 - .65 * moss             # alpha：樹皮細節遮罩（URP Lit 的 Detail Mask 讀 alpha）。苔上留 35% 細節紋，近看不會是一塊平的綠
        if leaf:
            base[:h0, :half, 3] = 0               # 葉子那一條不疊樹皮紋
        _save(base, f'{TEX}/{ASSET}_{S}_Albedo.png', True)
        bpy.data.images.remove(im)
        im, nrm = _px(W('Normal'))
        nrm = _dilate(nrm, fill=(.5, .5, 1.0))
        if leaf:
            nrm[:h0, :half, :3] = (.5, .5, 1.0)
        _save(nrm, f'{TEX}/{ASSET}_{S}_Normal.png', False)
        bpy.data.images.remove(im)
        im, rgh = _px(W('Roughness'))
        rgh = _dilate(rgh, fill=.8)
        if leaf:
            rgh[:h0, :half, :3] = .82             # 葉面不要亮：引擎裡平滑的葉子會反射天空，整片發白
        bpy.data.images.remove(im)
        im, ao = _px(W('AO'))
        ao = _dilate(ao, fill=1.0)
        ao[..., :3] = np.maximum(ao[..., :3], .30)      # 低模鑽進隔壁根裡面的地方烘出來全黑，露出一點就是黑斑；設下限
        if leaf:
            ao[:h0, :half, :3] = 1
        bpy.data.images.remove(im)
        orm = np.ones_like(rgh)                       # R AO、G roughness、B metal
        orm[..., 0], orm[..., 1], orm[..., 2] = ao[..., 0], rgh[..., 0], 0
        _save(orm, f'{TEX}/{ASSET}_{S}_ORM.png', False)
        msk = np.zeros_like(rgh)                      # R metal、G AO、A smoothness（URP Lit）
        msk[..., 1] = ao[..., 0]
        msk[..., 3] = 1 - rgh[..., 0]
        _save(msk, f'{TEX}/{ASSET}_{S}_MaskURP.png', False)


def shared_detail():
    """D2 根與木共用的樹皮細節法線（Poly Haven bark_brown_02，CC0，縮成 1024）。"""
    d = f'{ROOT}/art/exports/d2-roots-b/Shared'
    os.makedirs(d, exist_ok=True)
    p = f'{d}/D2Bark_Detail_Normal.png'
    if not os.path.exists(p):
        src = os.environ.get('DR_TEX', 'D:/yun-jing-cache/polyhaven-bark/') + 'bark_brown_02_nor_gl_2k.png'
        im = bpy.data.images.load(src, check_existing=False)
        im.scale(1024, 1024)
        im.filepath_raw = p
        im.file_format = 'PNG'
        im.save()
        bpy.data.images.remove(im)
    pa = f'{d}/D2Bark_Detail_Albedo.png'
    if not os.path.exists(pa):
        # 灰階疊色（URP Lit Detail Base Map，x2 相乘）：平均 0.5 sRGB = 不改變底色，只加樹皮的明暗條紋
        src = os.environ.get('DR_TEX', 'D:/yun-jing-cache/polyhaven-bark/') + 'bark_brown_02_diff_2k.png'
        im = bpy.data.images.load(src, check_existing=False)
        im.scale(1024, 1024)
        a = np.empty(1024 * 1024 * 4, np.float32)
        im.pixels.foreach_get(a)
        a = a.reshape(1024, 1024, 4)
        lum = a[..., 0] * .3 + a[..., 1] * .5 + a[..., 2] * .2
        g = np.clip(.5 + (lum - lum.mean()) / (lum.std() + 1e-6) * .09, .2, .8)      # 對比壓低：專案匯入規則的 crunch 壓縮會把高對比細節壓成直條
        out = np.dstack([g, g, g, np.ones_like(g)])
        bpy.data.images.remove(im)
        _save(out, pa, True)
    return p


def game_material(S, name=None):
    name = name or f'M_{ASSET}_{S}'
    m = bpy.data.materials.get(name)
    if m:
        bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')

    def t(kind, color):
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = bpy.data.images.load(f'{TEX}/{ASSET}_{S}_{kind}.png', check_existing=False)
        n.image.colorspace_settings.name = 'sRGB' if color else 'Non-Color'
        return n
    # 近看的樹皮細節：共用的掃描樹皮法線，沿 UV0 重複（所有 UV 島同比例、同方向，所以可以直接用 URP Lit 的 Detail Normal）
    f = bpy.context.scene.get('dr02_uv_per_m', 46.0 / SIZE)
    tile = 1.0 / (f * 2.6)
    dpath = shared_detail()
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (tile, tile, 1)
    nt.links.new(tc.outputs['UV'], mp.inputs['Vector'])
    alb = t('Albedo', True)
    alb.image.alpha_mode = 'CHANNEL_PACKED'
    orm = t('ORM', False)
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(orm.outputs[0], sep.inputs[0])
    mix = nt.nodes.new('ShaderNodeMix')           # AO 乘進底色（預覽用 40%；Unity 裡走 Occlusion）
    mix.data_type = 'RGBA'
    mix.blend_type = 'MULTIPLY'
    mix.inputs['Factor'].default_value = .4
    da = nt.nodes.new('ShaderNodeTexImage')        # 樹皮細節疊色（和細節法線同一組重複 UV）
    da.image = bpy.data.images.load(dpath.replace('_Normal', '_Albedo'), check_existing=True)
    nt.links.new(mp.outputs[0], da.inputs['Vector'])
    dbl = nt.nodes.new('ShaderNodeVectorMath')
    dbl.operation = 'SCALE'
    dbl.inputs['Scale'].default_value = 4.59          # Unity 線性空間的 x2：0.5 sRGB 的灰 ≈ 1
    nt.links.new(da.outputs[0], dbl.inputs[0])
    dmix = nt.nodes.new('ShaderNodeMix')
    dmix.data_type = 'RGBA'
    dmix.blend_type = 'MULTIPLY'
    nt.links.new(alb.outputs['Alpha'], dmix.inputs['Factor'])
    nt.links.new(alb.outputs[0], dmix.inputs['A'])
    nt.links.new(dbl.outputs[0], dmix.inputs['B'])
    nt.links.new(dmix.outputs['Result'], mix.inputs['A'])
    nt.links.new(sep.outputs[0], mix.inputs['B'])
    nt.links.new(mix.outputs['Result'], bs.inputs['Base Color'])
    nt.links.new(sep.outputs[1], bs.inputs['Roughness'])
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(t('Normal', False).outputs[0], nm.inputs['Color'])
    dt = nt.nodes.new('ShaderNodeTexImage')
    dt.image = bpy.data.images.load(dpath, check_existing=True)
    dt.image.colorspace_settings.name = 'Non-Color'
    nt.links.new(mp.outputs[0], dt.inputs['Vector'])
    dn = nt.nodes.new('ShaderNodeNormalMap')
    dn.inputs['Strength'].default_value = 1.0
    nt.links.new(dt.outputs[0], dn.inputs['Color'])
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    add = nt.nodes.new('ShaderNodeVectorMath')
    add.operation = 'ADD'
    sub = nt.nodes.new('ShaderNodeVectorMath')
    sub.operation = 'SUBTRACT'
    nrmz = nt.nodes.new('ShaderNodeVectorMath')
    nrmz.operation = 'NORMALIZE'
    nt.links.new(nm.outputs[0], add.inputs[0])
    nt.links.new(dn.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], sub.inputs[0])
    nt.links.new(geo.outputs['Normal'], sub.inputs[1])
    nt.links.new(sub.outputs[0], nrmz.inputs[0])
    nt.links.new(nrmz.outputs[0], bs.inputs['Normal'])
    m['unity_detail_tiling'] = tile
    m['unity'] = {'shader': 'Universal Render Pipeline/Lit', 'detail': 'D2Bark_Detail_Normal + D2Bark_Detail_Albedo on UV0, mask = Albedo alpha'}
    return m


# ---------------------------------------------------------------- 遊戲用植物（Detail_Small）
def make_detail(seed=5):
    import core_plants, dr01_dress
    importlib.reload(core_plants)
    importlib.reload(dr01_dress)
    for nm in list(bpy.data.objects.keys()):
        if nm.startswith(('DR02_LP_', 'DR02_LQ_', f'{ASSET}_Detail_Small', DET)):
            bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    b = _build()
    Base = core_plants.LeafBuf

    class Lite(Base):
        cfg = dict(every=1, widen=1.0, maxnu=4, maxnv=2)

        def __init__(self):
            super().__init__()
            self.n = 0

        def leaf(self, origin, along, side, up, L, W, shape, fold=.3, curl=0.0, droop=0.0, tint=(1, 1, 1), nu=7, nv=4, twist=0.0):
            c = Lite.cfg
            self.n += 1
            if nu >= 8 and nv == 2:          # 蕨的羽片：隔一片留一片、加寬、降面數；拱頂上的（離人最近也有四五公尺）三片留一片
                far = origin.z > 3.0
                if self.n % (3 if far else c.get('fern_keep', 2)):     # fern_keep：DR03 交叉件根腳小蕨很多，三片留一片
                    return
                W, nu, nv = W * (2.7 if far else 1.9), 2, 1
            elif nu == 1:                     # 藤的細莖
                pass
            else:
                nu, nv = min(nu, c['maxnu']), min(nv, c['maxnv'])
            super().leaf(origin, along, side, up, L, W, shape, fold, curl, droop, tint, nu, nv, twist)
    core_plants.LeafBuf = Lite
    try:
        low = bpy.data.objects[f'{ASSET}_LOD0']
        g = _coll('DR02_Game')
        outs = []
        if 'dress_game' in b:            # DR03 交叉件：兩條根各長一次（第二條用 DR02_LQ_）
            outs += b['dress_game'](low, dr01_dress, seed)
        else:
            outs += dr01_dress.dress([low], b['centre'], b['frame'], b['fb'], b['PATH_HALF'], quick=True, seed=seed,
                                     coll_name='DR02_Game', prefix='DR02_LP_', lite=True, amount=b['VAR']['plants'], avoid=True)
    finally:
        core_plants.LeafBuf = Base
    keep = []
    for o in outs:
        grp = o.name.replace('DR02_LP_', '').replace('DR02_LQ_', '')
        if grp not in LEAF:
            bpy.data.objects.remove(o, do_unlink=True)        # 細莖不進遊戲模型
            continue
        x0, x1 = LEAF[grp][0], LEAF[grp][1]
        uv = o.data.uv_layers[0]
        a = np.empty(len(o.data.loops) * 2, np.float32)
        uv.data.foreach_get('uv', a)
        a = a.reshape(-1, 2)
        a[:, 0] = x0 + (x1 - x0) * (.03 + .94 * np.clip(a[:, 0], 0, 1))
        a[:, 1] = STRIP * (.06 + .88 * np.clip(a[:, 1], 0, 1))
        uv.data.foreach_set('uv', a.ravel())
        uv.name = 'UVMap'
        t = o.data.uv_layers.new(name='TileUV')
        t.data.foreach_set('uv', a.ravel())
        for ca in list(o.data.color_attributes):
            o.data.color_attributes.remove(ca)
        keep.append(o)
    d = _join(keep, f'{DET}_LOD0') if len(keep) > 1 else keep[0]
    d.name = d.data.name = f'{DET}_LOD0'
    # 葉尖收成一點的地方會留下零面積三角面，引擎匯入時會丟掉；這裡先清掉，面數才和引擎裡一致
    bm = bmesh.new()
    bm.from_mesh(d.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-5)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(d.data)
    bm.free()
    print('detail tris', sum(len(p.vertices) - 2 for p in d.data.polygons))
    return d


# ---------------------------------------------------------------- LOD、碰撞、接口、匯出
def finish():
    b = _build()
    g = _coll('DR02_Game')
    old = bpy.data.materials.get(f'M_{ASSET}_Main')
    if old:
        bpy.data.materials.remove(old)
    mats = [game_material(S) for S in SETS]
    low = bpy.data.objects[f'{ASSET}_LOD0']
    det = bpy.data.objects[f'{DET}_LOD0']
    assert len(low.data.materials) == len(SETS)
    for i, m in enumerate(mats):                  # 本體：四個材質槽 A–D（面的材質編號在 make_low 就定好了）
        low.data.materials[i] = m
    leafm = game_material(SETS[0], f'M_{ASSET}_Leaf')      # 小植物：A 組貼圖（葉子畫在 A 組圖集最下面一條），另一個材質，引擎裡開雙面
    leafm.use_backface_culling = False
    leafm['unity'] = {'shader': 'Universal Render Pipeline/Lit', 'render_face': 'Both', 'textures': f'{ASSET}_A_*'}
    det.data.materials.clear()
    det.data.materials.append(leafm)
    det.data.polygons.foreach_set('material_index', [0] * len(det.data.polygons))
    for o in (low, det):
        for ca in list(o.data.color_attributes):
            o.data.color_attributes.remove(ca)
    for nm in list(bpy.data.objects.keys()):
        if nm.startswith((ASSET, DET)) and ('_LOD1' in nm or '_LOD2' in nm or nm.endswith('_Collision') or nm == ASSET) or nm.startswith(('Socket_', 'DR02_LodTmp')):
            bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
    lods = {0: [low, det]}

    def decimated(src, ratio, name):
        o = src.copy()
        o.data = src.data.copy()
        for c in list(o.users_collection):
            c.objects.unlink(o)
        g.objects.link(o)
        o.name = o.data.name = name
        m = o.modifiers.new('LOD_decimate', 'DECIMATE')
        m.ratio = ratio
        m.use_collapse_triangulate = True
        _select([o], o)
        with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o], selected_editable_objects=[o]):
            bpy.ops.object.modifier_apply(modifier=m.name)
        return o
    fulls = sorted(bpy.data.collections['DR02_LowFull'].objects, key=lambda o: o.name)
    for lv, ratio in ((1, .5), (2, .15)):
        # 樹皮：每條根各自減面（還是封閉的管子）→ 刪掉藏在別的根裡的面 → 併成一個物件
        cps, _ = _cull_hidden([decimated(src, ratio, f'DR02_LodTmp{lv}_{i:03d}') for i, src in enumerate(fulls)])
        bark = _join(cps, f'{ASSET}_LOD{lv}') if len(cps) > 1 else cps[0]
        bark.name = bark.data.name = f'{ASSET}_LOD{lv}'
        for i, m in enumerate(mats):
            bark.data.materials[i] = m
        lods[lv] = [bark, decimated(det, ratio, f'{DET}_LOD{lv}')]
    for lst in lods.values():
        for o in lst:
            for ca in list(o.data.color_attributes):
                o.data.color_attributes.remove(ca)
            at = o.data.attributes.get('ring')
            if at:
                o.data.attributes.remove(at)
    # 碰撞殼：只留粗的根（半徑 > 0.32 m，也就是直徑 0.64 m 以上、人跨不過去的），6 邊、每 1.2 m 一環
    cobjs = b['build'](quick=False, name='DR02_Col', low=(1.2, 6, 6), only_big=.32)
    col = _join(cobjs, f'{ASSET}_Collision')
    for c in list(col.users_collection):
        c.objects.unlink(col)
    g.objects.link(col)
    col.data.materials.clear()
    for ca in list(col.data.color_attributes):
        col.data.color_attributes.remove(ca)
    while col.data.uv_layers:
        col.data.uv_layers.remove(col.data.uv_layers[0])
    col.hide_render = True
    col.display_type = 'WIRE'
    cc = bpy.data.collections.get('DR02_Col')
    if cc:
        bpy.data.collections.remove(cc)
    root = bpy.data.objects.new(ASSET, None)
    g.objects.link(root)
    socks = []
    for nm, loc, rz in sockets(b):
        e = bpy.data.objects.new(nm, None)
        e.empty_display_size = .5
        e.location = loc
        e.rotation_euler = (0, 0, math.radians(rz))
        g.objects.link(e)
        e.parent = root
        socks.append(e)
    allm = [o for lst in lods.values() for o in lst] + [col]
    for o in allm:
        o.data.name = o.name
    for o in allm:
        o.parent = root
    return _export(lods, col, socks, root)


def sockets(b):
    """回傳 [(名稱, (x, y, z), 方向角度)]。"""
    # 接口：Socket_Head 在粗頭頂面露出土的地方；Socket_Tail 在細頭頂面鑽進土的地方再往回 2.5 m（OVERLAP）。
    # 兩個接口的 +X 都是這段根往細頭走的方向。下一件的 Socket_Head 直接對到這件的 Socket_Tail（位置、方向都對齊），
    # 細頭最後 2.5 m 就和下一件的粗頭並在一起，接縫處的牆不會塌下去（量過：重疊 1.2 m 時接縫最低 0.58 m，2.5 m 時 0.8 m）
    ts = [i / 800 for i in range(801)]
    up = [t for t in ts if (lambda c, r, fl: c.z + r * fl * .5 > .1)(*b['spine_at'](t))]
    th, tt = up[0], up[-1]
    acc, t_tail = 0.0, tt
    for k in range(ts.index(tt), 0, -1):
        acc += (b['spine_at'](ts[k])[0] - b['spine_at'](ts[k - 1])[0]).xy.length
        if acc >= OVERLAP:
            t_tail = ts[k - 1]
            break

    def heading(t):
        d = b['spine_at'](min(1, t + .01))[0] - b['spine_at'](max(0, t - .01))[0]
        return math.degrees(math.atan2(d.y, d.x))
    ph, pt = b['spine_at'](th)[0], b['spine_at'](t_tail)[0]
    return [('Socket_Head', (ph.x, ph.y, 0), heading(th)), ('Socket_Tail', (pt.x, pt.y, 0), heading(t_tail))]


def _export(lods, col, socks, root):
    allm = [o for lst in lods.values() for o in lst] + [col]
    bpy.context.view_layer.update()
    os.makedirs(EXP, exist_ok=True)
    col.hide_render = False
    _select(allm + socks + [root], root)
    fbx = f'{EXP}/{ASSET}_{VER}.fbx'
    bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, object_types={'MESH', 'EMPTY'},
                             apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', bake_space_transform=True,
                             axis_forward='-Z', axis_up='Y', mesh_smooth_type='FACE', use_mesh_modifiers=True,
                             add_leaf_bones=False, bake_anim=False, path_mode='STRIP', embed_textures=False)
    try:
        _select(lods[0] + [root], root)
        bpy.ops.export_scene.gltf(filepath=f'{EXP}/{ASSET}_{VER}.glb', use_selection=True, export_format='GLB', export_yup=True)
    except Exception as e:
        print('glb', e)
    col.hide_render = True
    tri = lambda o: sum(len(p.vertices) - 2 for p in o.data.polygons)
    info = {lv: {o.name: tri(o) for o in lst} for lv, lst in lods.items()}
    info['collision'] = tri(col)
    print(json.dumps(info, indent=1))
    return info


# ---------------------------------------------------------------- 一次跑完（在 Blender 裡用 timer 啟動，進度寫到紀錄檔）
def run_all(samples=24, rebuild_high=True, kinds=None, rebuild_low=True):
    import traceback, time
    log = WORKTEX + '_run.log'
    t = time.time()

    def L(m):
        open(log, 'a', encoding='utf-8').write(f'{round(time.time() - t)}s {m}\n')
    open(log, 'w').write('')
    try:
        if rebuild_high:
            b = _build()
            objs = b['build'](quick=False)
            b['dress'](objs, quick=False)
            L('high %d objects' % len(objs))
            os.makedirs(HERE + '/blend', exist_ok=True)
            bpy.ops.wm.save_as_mainfile(filepath=f'{HERE}/blend/{ASSET}_high_{VER}.blend', copy=True)
        if rebuild_low:
            L('low groups %d' % len(make_low()))
        bake(samples, log=L, kinds=kinds)
        L('bake')
        finish_textures()
        L('textures')
        join_low()
        make_detail()
        L('detail')
        L('finish ' + json.dumps(finish()))
        bpy.ops.wm.save_as_mainfile(filepath=f'{HERE}/blend/{ASSET}_{VER}.blend', copy=True)
        L('DONE')
    except Exception:
        L('ERROR ' + traceback.format_exc())
