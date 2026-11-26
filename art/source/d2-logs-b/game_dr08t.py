# DR08 長滿蕈和苔的朽木（三種）的遊戲用模型，第二版做法：手繪平鋪貼圖＋頂點權重分層（不烘焙圖集）。
# 為什麼換：第一版一件一張 2048 烘焙圖集，專案匯入規則壓成 1024 後每公尺只剩約 150 px，苔、腐木全糊；程序化雜訊貼圖也做不出設定圖的手繪感。
#   - 本體：材質 M_DR08_Layered（Unity：YunJing/D2LayeredWood），六層 1024 手繪平鋪貼圖（樹皮、苔、褐腐木、撕裂纖維、樹洞內壁、土），
#     UV0 是公尺（樹幹沿長＝u，貼圖的木紋左右向），頂點色 RGBA＝苔、腐木、纖維、內壁的權重，UV1＝(土的權重, AO)；
#     大香菇（立在地上、斜靠樹幹，build_dr08.big_mush8）是本體的第二個材質槽 M_DR08_Plants（菌傘照 BrkA／BrkR 貼手繪菌蓋圖）。
#   - Detail_DR08_Plants：手繪植物卡（蕨、小褐蕈、發光小蕈、小苗、落葉、垂苔），M_DR08_Plants（雙面、alpha 裁切）。
#   - 兩個材質三件共用（A、B、C 同一組貼圖），貼圖在 art/exports/d2-logs-b/DR08_Shared/Textures（tex_dr08.py 做的）。
#   - LOD1／LOD2 不減面：用較粗的低模參數重建，再照同樣的規則上權重（UV、權重不會被減面拉壞）；植物卡取一部分。
# 用法（背景）：blender -b --python game_dr08t.py -- B
import os, sys, json, math, re, time, traceback, random

_HERE8 = 'D:/yun-jing-d2-logs/art/source/d2-logs-b'
_p8 = _HERE8 + '/game_dr08.py'
_nm8 = globals().get('__name__')
globals()['__name__'] = 'game_dr08_lib'
exec(compile(open(_p8, encoding='utf-8').read(), _p8, 'exec'), globals())
globals()['__name__'] = _nm8

TEXD = f'{ROOT}/art/exports/d2-logs-b/DR08_Shared/Textures'
TILES = {'Bark': 1.0, 'Moss': 2.0, 'Rot': 2.0, 'Fibre': 1.0, 'Inner': 1.0, 'Soil': 1.0}     # 每公尺重複幾次（1024 px → 1024／2048 px/m）
LAYER_MAT, PLANT_MAT = 'M_DR08_Layered', 'M_DR08_Plants'
LODRES = {0: (.10, 12, 36, 1.2, 0), 1: (.17, 10, 24, 1.0, 1), 2: (.34, 8, 12, 1.0, 2)}
PLANT_KEEP = {0: 1.0, 1: .65, 2: .12}
RECTS = None


def rects():
    global RECTS
    if RECTS is None:
        RECTS = json.load(open(f'{TEXD}/DR08_Plants_rects.json'))['rects']
    return RECTS


def _np(o, name, dom_n, dt=np.float32, w=1):
    a = np.empty(dom_n * w, dt)
    o.data.attributes[name].data.foreach_get('value' if w == 1 else 'color', a)
    return a.reshape(-1, w) if w > 1 else a


def _loops(o):
    me = o.data
    vi = np.empty(len(me.loops), np.int32)
    me.loops.foreach_get('vertex_index', vi)
    ls = np.empty(len(me.polygons), np.int32)
    me.polygons.foreach_get('loop_start', ls)
    lt = np.empty(len(me.polygons), np.int32)
    me.polygons.foreach_get('loop_total', lt)
    fo = np.repeat(np.arange(len(me.polygons)), lt)
    return vi, fo, ls, lt


def _co(o):
    a = np.empty(len(o.data.vertices) * 3, np.float32)
    o.data.vertices.foreach_get('co', a)
    return a.reshape(-1, 3) @ np.array(o.matrix_world)[:3, :3].T + np.array(o.matrix_world)[:3, 3]


def _fnormal(o):
    a = np.empty(len(o.data.polygons) * 3, np.float32)
    o.data.polygons.foreach_get('normal', a)
    return a.reshape(-1, 3)


def _sm(a, e0, e1):
    t = np.clip((a - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def _noise(co, s, k=0.0):
    """便宜的平滑雜訊（幾個不同方向的 sin 疊起來），-1..1。"""
    x, y, z = co[:, 0] * s, co[:, 1] * s, co[:, 2] * s
    n = (np.sin(x * 1.7 + y * .9 + k) + np.sin(y * 2.3 - z * 1.3 + 1.7 * k + 2) + np.sin(z * 1.9 + x * 1.1 - k + 4)
         + .5 * np.sin(x * 3.7 - y * 2.9 + z * 1.3 + 2 * k))
    return n / 3.5


# ---------------------------------------------------------------- UV（公尺）
def uv_tube(o, ring_r):
    """管子（外殼、內壁）：u＝沿長公尺，v＝繞一圈（周長取整數公尺，各層的重複次數都是 1／2 的倍數，接縫接得起來）。"""
    me = o.data
    pa = np.empty(len(me.loops) * 2, np.float32)
    me.uv_layers['Param'].data.foreach_get('uv', pa)
    pa = pa.reshape(-1, 2).astype(np.float64)
    vi, fo, ls, lt = _loops(o)
    C = max(1.0, round(2 * math.pi * float(np.mean(ring_r))))
    ring = _np(o, 'ring', len(me.polygons), np.int32)
    uv = np.zeros((len(me.loops), 2))
    a = pa[:, 0].copy()
    for f in range(len(me.polygons)):                     # 繞回來那一圈：同一面裡 a 跨過 0／1 的往上補 1
        sl = slice(ls[f], ls[f] + lt[f])
        if a[sl].max() - a[sl].min() > .5:
            a[sl] = np.where(a[sl] < .5, a[sl] + 1, a[sl])
    uv[:, 0] = pa[:, 1]
    uv[:, 1] = a * C
    fnx = np.abs(_fnormal(o)[:, 0])
    caps = np.nonzero((ring < 0) | (fnx > .55))[0]
    if len(caps):
        co = _co(o)
        fn = _fnormal(o)
        for f in caps:
            uv[ls[f]:ls[f] + lt[f]] = _plane_uv(co[vi[ls[f]:ls[f] + lt[f]]], fn[f])
    return uv


def _plane_uv(p, n):
    n = n / (np.linalg.norm(n) + 1e-9)
    a = np.cross(n, (0, 0, 1)) if abs(n[2]) < .9 else np.cross(n, (1, 0, 0))
    a /= np.linalg.norm(a) + 1e-9
    b = np.cross(n, a)
    return np.stack([p @ a, p @ b], -1)


def uv_box(o, xbias=1.0):
    """其他件：每個面照法線最大的軸投影（公尺）；側面的 u 都順著樹幹（x），木紋方向一致。
    洞口斷面（Rim、Lip）是斜的一圈：xbias 讓偏向端面的面都用端面投影，不會被沿長方向的投影拉成一條條。"""
    vi, fo, ls, lt = _loops(o)
    co = _co(o)
    fn = np.abs(_fnormal(o)) * np.array([xbias, 1.0, 1.0])
    ax = np.argmax(fn, 1)[fo]
    p = co[vi]
    uv = np.where((ax == 2)[:, None], p[:, [0, 1]], np.where((ax == 1)[:, None], p[:, [0, 2]], p[:, [1, 2]]))
    return uv


def uv_rim(o):
    """洞口斷面（一圈圈年輪台階）：繞洞口一圈展開。u＝繞一圈的角度×周長（取整數公尺，接縫接得起來），
    v＝從外圈往內的距離＋往洞裡退的深度：端面、台階的側面都有正常比例，木紋繞著洞口一圈圈走（像年輪），不會被軸向投影拉成條紋。"""
    vi, fo, ls, lt = _loops(o)
    co = _co(o)
    fn = _fnormal(o)
    ar = np.array([p.area for p in o.data.polygons])
    ad = (fn * ar[:, None]).sum(0)
    ad /= np.linalg.norm(ad) + 1e-9
    c = co.mean(0)
    d = co - c
    dep = d @ ad
    rad = d - dep[:, None] * ad
    r = np.linalg.norm(rad, axis=1)
    e1 = np.cross(ad, (0, 0, 1))
    if np.linalg.norm(e1) < 1e-3:
        e1 = np.cross(ad, (0, 1, 0))
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(ad, e1)
    t = (np.arctan2(rad @ e2, rad @ e1) / (2 * math.pi)) % 1.0
    C = max(1.0, round(2 * math.pi * float(np.median(r))))
    a = t[vi].copy()
    for f in range(len(o.data.polygons)):
        sl = slice(ls[f], ls[f] + lt[f])
        if a[sl].max() - a[sl].min() > .5:
            a[sl] = np.where(a[sl] < .5, a[sl] + 1, a[sl])
    v = -(r + dep)
    nV = len(co)
    rows = 15                                               # build_dr05.rim 低模：16 列 × M 點，照列排（外圈 → 內圈）
    if nV % (rows + 1) == 0:                                # v 改成沿每一條（外圈到內圈）量的表面距離：台階的側面、坑坑疤疤都不會壓扁
        M = nV // (rows + 1)
        g = co.reshape(rows + 1, M, 3)
        seg = np.linalg.norm(np.diff(g, axis=0), axis=2)
        v = np.concatenate([np.zeros((1, M)), np.cumsum(seg, axis=0)], 0).ravel()
    return np.stack([a * C, v[vi]], -1)


def uv_fungus(o):
    """層狀菌：BrkA（扇形角度）、BrkR（從根到邊 0..1，邊、下面在奶油色圓唇）→ 手繪菌蓋圖（直邊在下＝貼樹幹那邊）。"""
    r = next(q for q in rects() if q['cat'] == 'fungus')['uv']
    vi, _, _, _ = _loops(o)
    A = _np(o, 'BrkA', len(o.data.vertices))[vi]
    Rr0 = _np(o, 'BrkR', len(o.data.vertices))[vi]
    Rr = np.where(Rr0 < 0, np.clip(-Rr0, 0, .955), .24 + .64 * np.clip(Rr0, 0, 1))      # 負值（菌傘下面、菌柄）取靠上中央的奶油色；菌傘頂跳過根部纖維（不然中心像印章），外緣停在 0.88（圖上的波浪透明邊 alpha 裁切後會缺一口口）
    t = np.clip(A, .03 * math.pi, .97 * math.pi)
    cx = .5 * (r[0] + r[2])
    hw, hh = .5 * (r[2] - r[0]) * .96, (r[3] - r[1]) * .96
    return np.stack([cx + np.cos(t) * Rr * hw, r[1] + .01 * (r[3] - r[1]) + np.sin(t) * Rr * hh], -1)


# ---------------------------------------------------------------- 權重
def weights(o, kind):
    """回傳每個角的 (苔, 腐木, 纖維, 內壁, 土)。"""
    me = o.data
    vi, fo, ls, lt = _loops(o)
    co = _co(o)
    pc = co[vi]
    fn = _fnormal(o)[fo]
    n = len(me.loops)
    W = np.zeros((n, 5))
    em = _np(o, 'EndMoss', len(me.vertices))[vi] if me.attributes.get('EndMoss') else np.zeros(n)
    gz = _sm(-pc[:, 2], -.12, .02)                          # 貼地（z 0.12 m 以下）漸漸變成土
    if kind == 'Trunk':
        mk = np.empty(n * 4, np.float32)
        me.color_attributes['Mask'].data.foreach_get('color', mk)
        mo = mk.reshape(-1, 4)[:, 0]
        pe = _np(o, 'Peel', len(me.vertices))[vi]
        moss = _sm(mo, .0, .16)
        # 參考圖：苔從頂上一舌舌垂到側面（不是只蓋頂上）；側面朝上、朝外的面一片片長苔，越低越少
        side = _sm(fn[:, 2], -.40, .10) * _sm(_noise(pc * np.array((1.6, 1.6, .45)), 2.4, 7.0), -.28, .08) * _sm(pc[:, 2], .05, .25)
        moss = np.maximum(moss, side)
        rot = _sm(pe, .35, .70) * (1 - moss)
        W[:, 0] = moss
        W[:, 1] = rot
        W[:, 4] = gz * .85 * (1 - moss * .6)
    elif kind == 'Inner':
        W[:, 3] = 1
        W[:, 1] = .45 * _sm(_noise(pc, 3.0, 1.0), .1, .6)       # 內壁一片片褐腐
        W[:, 0] = np.clip(em * 1.5, 0, 1)
        W[:, 4] = .7 * _sm(fn[:, 2], .55, .9) * _sm(_noise(pc, 4.0, 3.0), -.2, .4)   # 洞底：土、碎屑
    elif kind in ('Rim', 'Lip'):
        W[:, 3] = .45                                            # 斷面以褐腐（裂成小塊的紅褐木）為主，內壁纖維只在一些地方
        W[:, 1] = .55 + .35 * _sm(_noise(pc, 5.0, 2.0), -.2, .5)
        W[:, 0] = np.clip(em * 1.5, 0, 1)
    elif kind == 'Slab':
        W[:, 2] = 1
    elif kind == 'Debris':
        W[:, 1] = 1
        W[:, 2] = .35 * _sm(_noise(pc, 6.0, 4.0), .2, .6)
        W[:, 4] = gz * .3
    elif kind == 'Soil':
        W[:, 4] = 1
        W[:, 0] = .8 * _sm(_noise(pc, 2.5, 5.0), .25, .6) * _sm(fn[:, 2], .3, .8)
        W[:, 1] = .5 * _sm(_noise(pc, 5.0, 6.0), .3, .7)        # 腐木粉
    s = W.sum(1, keepdims=True)
    W = np.where(s > 1, W / np.maximum(s, 1e-6), W)
    return W


def vertex_ao(objs, rays=12, dist=.32):
    """每個頂點往法線半球打 rays 條射線（全部件一起當遮擋）＋貼地變暗，回傳每件每個角的 AO（1＝不遮）。"""
    from mathutils.bvhtree import BVHTree
    V, F = [], []
    for o in objs:
        off = len(V)
        V += [Vector(p) for p in _co(o)]
        F += [tuple(off + i for i in p.vertices) for p in o.data.polygons]
    tree = BVHTree.FromPolygons(V, F)
    rs = np.random.RandomState(3)
    dirs = rs.randn(rays, 3)
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    out = []
    for o in objs:
        co = _co(o)
        vn = np.empty(len(o.data.vertices) * 3, np.float32)
        o.data.vertices.foreach_get('normal', vn)
        vn = vn.reshape(-1, 3) @ np.array(o.matrix_world)[:3, :3].T
        vn /= np.linalg.norm(vn, axis=1, keepdims=True) + 1e-9
        ao = np.ones(len(co))
        for i in range(len(co)):
            nrm = vn[i]
            hit = 0
            for d in dirs:
                if d @ nrm < 0:
                    d = -d
                dd = Vector(d * .85 + nrm * .15).normalized()
                if tree.ray_cast(Vector(co[i] + nrm * .006), dd, dist)[0] is not None:
                    hit += 1
            ao[i] = 1 - .70 * hit / rays
        ao *= .55 + .45 * _sm(co[:, 2], -.02, .20)          # 貼地的一圈暗（接地感）
        vi, _, _, _ = _loops(o)
        out.append(ao[vi])
    return out


def kind_of(name):
    b = re.sub(r'^[LF]_', '', name)
    b = re.sub(r'\.\d{3}$', '', b)
    for k in ('Trunk', 'Inner', 'Rim', 'Lip', 'Slab', 'Brackets', 'Debris', 'Soil', 'Cubes', 'Mycel'):
        if b.startswith(k):
            return k
    return 'Debris'


def layer_parts(lv):
    """建 LOD lv 的本體件，上 UV、權重、AO、材質；回傳件（還沒合併）。"""
    b = _build()
    objs = b['build'](VARIANT, quick=False, low=LODRES[lv], pre='L_')
    parts = []
    for o in objs:
        k = kind_of(o.name.split('_', 1)[1])
        if k in ('Cubes', 'Mycel') or o.name.split('_', 1)[1].startswith('Hair'):
            bpy.data.objects.remove(o, do_unlink=True)
            continue
        if lv == 2 and k == 'Rim':                         # 洞口斷面（build_dr05.rim，DR05 共用）各級都是 16 列：LOD2 在這裡減面，不動 DR05
            md = o.modifiers.new('lod2', 'DECIMATE')
            md.ratio = .35
            dg = bpy.context.evaluated_depsgraph_get()
            m2 = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
            o.modifiers.clear()
            old = o.data
            o.data = m2
            bpy.data.meshes.remove(old)
        me = o.data
        if k == 'Brackets':
            uv = uv_fungus(o)
        elif 'ring_r' in o and me.uv_layers.get('Param'):
            uv = uv_tube(o, list(o['ring_r']))
        elif k == 'Slab' and me.attributes.get('SlU'):
            vi_ = _loops(o)[0]
            uv = np.stack([_np(o, 'SlU', len(me.vertices))[vi_], _np(o, 'SlV', len(me.vertices))[vi_]], -1)
        else:
            uv = uv_rim(o) if k == 'Rim' else uv_box(o)
        W = np.zeros((len(me.loops), 5)) if k == 'Brackets' else weights(o, k)
        while me.uv_layers:
            me.uv_layers.remove(me.uv_layers[0])
        me.uv_layers.new(name='UVMap').data.foreach_set('uv', uv.astype(np.float32).ravel())
        for ca in list(me.color_attributes):
            me.color_attributes.remove(ca)
        ca = me.color_attributes.new('Layers', 'FLOAT_COLOR', 'CORNER')         # 權重先存成角屬性：刪面時跟著網格走
        ca.data.foreach_set('color', W[:, :4].astype(np.float32).ravel())
        me.color_attributes.active_color = ca
        me.attributes.new('_soil', 'FLOAT', 'CORNER').data.foreach_set('value', W[:, 4].astype(np.float32))
        me.materials.clear()
        me.materials.append(plant_material() if k == 'Brackets' else layer_material())
        for an in [a.name for a in me.attributes if a.name in ('ring', 'Peel', 'MudMoss', 'EndMoss', 'Shard', 'ShardU', 'BrkU', 'BrkV', 'BrkA', 'BrkR', 'Tint', 'CubeU', 'CubeV', 'CubeT', 'SlU', 'SlV')]:
            me.attributes.remove(me.attributes[an])
        for kk in ('ring_r', 'ring_s'):
            if kk in o:
                del o[kk]
        o['_kind'] = k
        parts.append(o)
    # 刪藏起來的面（外殼、內壁、洞口斷面互不算擋：DR08 的 _hidden_verts）
    hidden = _hidden_verts(parts)
    parts, gone = _delete_hidden(parts, hidden)
    print('LOD', lv, 'hidden tris removed', gone)
    parts = [o for o in parts if len(o.data.polygons)]
    print('LOD', lv, 'PARTS', {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in parts})
    aos = vertex_ao(parts) if lv < 2 else [np.ones(len(o.data.loops)) for o in parts]
    for o, ao in zip(parts, aos):
        me = o.data
        soil = np.empty(len(me.loops), np.float32)
        me.attributes['_soil'].data.foreach_get('value', soil)
        me.attributes.remove(me.attributes['_soil'])
        if o['_kind'] == 'Brackets':
            ao = np.ones(len(me.loops))
        me.uv_layers.new(name='Extra').data.foreach_set('uv', np.stack([soil, ao], -1).astype(np.float32).ravel())
        del o['_kind']
    return parts


def layer_material():
    """Blender 裡的預覽材質（Unity 用 YunJing/D2LayeredWood）：六層照權重依序疊（預覽，不做高度混合）。"""
    m = bpy.data.materials.get(LAYER_MAT)
    if m:
        return m
    m = bpy.data.materials.new(LAYER_MAT)
    m.use_nodes = True
    N, Lk = m.node_tree.nodes, m.node_tree.links
    bs = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    uv = N.new('ShaderNodeUVMap')
    uv.uv_map = 'UVMap'
    at = N.new('ShaderNodeVertexColor')
    at.layer_name = 'Layers'
    sp = N.new('ShaderNodeSeparateColor')
    Lk.new(at.outputs['Color'], sp.inputs[0])
    ex = N.new('ShaderNodeUVMap')
    ex.uv_map = 'Extra'
    se = N.new('ShaderNodeSeparateXYZ')
    Lk.new(ex.outputs['UV'], se.inputs[0])

    def tex(nm, normal=False):
        mp = N.new('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (TILES[nm], TILES[nm], 1)
        Lk.new(uv.outputs['UV'], mp.inputs['Vector'])
        t = N.new('ShaderNodeTexImage')
        t.image = bpy.data.images.load(f'{TEXD}/DR08_{nm}_{"Normal" if normal else "Albedo"}.png', check_existing=True)
        if normal:
            t.image.colorspace_settings.name = 'Non-Color'
        Lk.new(mp.outputs[0], t.inputs['Vector'])
        return t.outputs['Color']
    order = [('Moss', sp.outputs[0]), ('Rot', sp.outputs[1]), ('Fibre', sp.outputs[2]), ('Inner', at.outputs['Alpha']), ('Soil', se.outputs[0])]
    col, nrm = tex('Bark'), tex('Bark', True)
    for nm, w in order:
        sh = N.new('ShaderNodeMath')                       # 權重變陡一點（Unity 是高度混合，交界比線性的窄）
        sh.operation = 'MULTIPLY_ADD'
        sh.inputs[1].default_value = 1.6
        sh.inputs[2].default_value = -.3
        sh.use_clamp = True
        Lk.new(w, sh.inputs[0])
        for kind in ('c', 'n'):
            mx = N.new('ShaderNodeMix')
            mx.data_type = 'RGBA'
            Lk.new(sh.outputs[0], mx.inputs[0])
            Lk.new(col if kind == 'c' else nrm, mx.inputs[6])
            Lk.new(tex(nm, kind == 'n'), mx.inputs[7])
            if kind == 'c':
                col = mx.outputs[2]
            else:
                nrm = mx.outputs[2]
    ao = N.new('ShaderNodeMath')
    ao.operation = 'MULTIPLY_ADD'
    ao.inputs[1].default_value = .5
    ao.inputs[2].default_value = .5
    Lk.new(se.outputs[1], ao.inputs[0])
    mu = N.new('ShaderNodeMix')
    mu.data_type = 'RGBA'
    mu.blend_type = 'MULTIPLY'
    mu.inputs[0].default_value = 1.0
    Lk.new(col, mu.inputs[6])
    Lk.new(ao.outputs[0], mu.inputs[7])
    Lk.new(mu.outputs[2], bs.inputs['Base Color'])
    nm_ = N.new('ShaderNodeNormalMap')
    nm_.uv_map = 'UVMap'
    Lk.new(nrm, nm_.inputs['Color'])
    Lk.new(nm_.outputs['Normal'], bs.inputs['Normal'])
    bs.inputs['Roughness'].default_value = .90
    m['unity'] = {'shader': 'YunJing/D2LayeredWood', 'textures': 'DR08_Shared/Textures/DR08_{Bark,Moss,Rot,Fibre,Inner,Soil}_{Albedo,Normal}.png',
                  'tiles_per_m': TILES, 'vertex_colour': 'RGBA = moss, rot, fibre, inner', 'uv1': 'x = soil, y = AO'}
    return m


def plant_material():
    m = bpy.data.materials.get(PLANT_MAT)
    if m:
        return m
    m = bpy.data.materials.new(PLANT_MAT)
    m.use_nodes = True
    N, Lk = m.node_tree.nodes, m.node_tree.links
    bs = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    t = N.new('ShaderNodeTexImage')
    t.image = bpy.data.images.load(f'{TEXD}/DR08_Plants_Albedo.png', check_existing=True)
    Lk.new(t.outputs['Color'], bs.inputs['Base Color'])
    Lk.new(t.outputs['Alpha'], bs.inputs['Alpha'])
    bs.inputs['Roughness'].default_value = .85
    m.use_backface_culling = False
    try:
        m.surface_render_method = 'DITHERED'
    except Exception:
        pass
    m['unity'] = {'shader': 'Universal Render Pipeline/Lit', 'render_face': 'Both', 'alpha_clip': .5, 'textures': 'DR08_Shared/Textures/DR08_Plants_Albedo.png'}
    return m


# ---------------------------------------------------------------- 植物卡
class Cards:
    def __init__(self):
        self.V, self.F, self.UV, self.tag = [], [], [], []

    def card(self, base, up, side, w, h, rect, bend=0.0, nrm=None, segs=3, tag=0, flip=False):
        """底邊中心 base、往 up 長 h、寬 w；bend：尖端往 nrm 方向彎（公尺）。rect：圖集 [u0, v0, u1, v1]（v 往上）。"""
        up, side = Vector(up).normalized(), Vector(side).normalized()
        nrm = Vector(nrm).normalized() if nrm is not None else up.cross(side)
        u0, v0, u1, v1 = rect
        if flip:
            u0, u1 = u1, u0
        o = len(self.V)
        for j in range(segs + 1):
            t = j / segs
            c = Vector(base) + up * (h * t) + nrm * (bend * t * t)
            for i, s in enumerate((-.5, .5)):
                self.V.append(tuple(c + side * (w * s)))
                self.UV.append((u0 + (u1 - u0) * (s + .5), v0 + (v1 - v0) * t))
        for j in range(segs):
            a = o + 2 * j
            self.F.append((a, a + 1, a + 3, a + 2))
            self.tag.append(tag)

    def obj(self, name, keep=1.0, seed=0):
        """keep：留幾成卡（LOD1／2）；同一 tag 的卡一起留或一起丟。"""
        rs = random.Random(seed)
        tags = sorted(set(self.tag))
        kept = {t for t in tags if rs.random() < keep or t < 0}
        F = [f for f, t in zip(self.F, self.tag) if t in kept]
        used = sorted({i for f in F for i in f})
        mp = {v: k for k, v in enumerate(used)}
        me = bpy.data.meshes.new(name)
        me.from_pydata([self.V[i] for i in used], [], [tuple(mp[i] for i in f) for f in F])
        uvl = me.uv_layers.new(name='UVMap')
        for lp in me.loops:
            uvl.data[lp.index].uv = self.UV[used[lp.vertex_index]]
        me.materials.append(plant_material())
        o = bpy.data.objects.new(name, me)
        _coll(_cn('Game')).objects.link(o)
        return o


def make_cards(body):
    """沿低模本體表面撒植物卡：頂上苔上的蕨叢、小苗，兩側苔邊往下垂的苔，側面、腳邊的小褐蕈，洞口裡的發光小蕈，地上落葉、腳邊蕨。"""
    from mathutils.bvhtree import BVHTree
    b = _build()
    V = b['VAR']
    L = V['L']
    co = _co(body)
    tree = BVHTree.FromPolygons([Vector(p) for p in co], [tuple(p.vertices) for p in body.data.polygons])
    lay = np.empty(len(body.data.loops) * 4, np.float32)
    body.data.color_attributes['Layers'].data.foreach_get('color', lay)
    lay = lay.reshape(-1, 4)
    vi, fo, ls, lt = _loops(body)
    fmoss = np.bincount(fo, lay[:, 0], len(body.data.polygons)) / np.maximum(lt, 1)
    mi = np.empty(len(body.data.polygons), np.int32)
    body.data.polygons.foreach_get('material_index', mi)
    R = random.Random(V['seed'] + 71)
    rc = {}
    for q in rects():
        rc.setdefault(q['cat'], []).append(q['uv'])
    C = Cards()
    tag = [0]

    def nt():
        tag[0] += 1
        return tag[0]
    ax = lambda x: Vector((x, b['axis_y'](V, x), b['axis_z'](V, x)))

    def hit_side(x, th):
        o_ = ax(x)
        d = Vector((0, math.cos(th), math.sin(th))).normalized()
        h = tree.ray_cast(o_ + d * 3 * V['R'], -d, 6 * V['R'])
        if h[0] is None or mi[h[2]] != 0:
            return None
        return h

    def aspect(r):
        return (r[2] - r[0]) / max(r[3] - r[1], 1e-6)
    # 1. 頂上苔上的蕨叢、小苗
    nf, tries = 0, 0
    while nf < int(1.6 * L) and tries < 400:
        tries += 1
        x = R.uniform(.12, .88) * L
        h = hit_side(x, R.uniform(.35, .65) * math.pi)
        if h is None or h[1].z < .45 or fmoss[h[2]] < .5:
            continue
        nf += 1
        p, n = h[0], h[1]
        t0 = nt()
        for k in range(R.randint(4, 6)):
            r = R.choice(rc['fern'])
            a = R.uniform(0, 2 * math.pi)
            out = Vector((math.cos(a), math.sin(a), 0))
            tilt = R.uniform(.35, .75)
            up = (n * math.cos(tilt) + out * math.sin(tilt)).normalized()
            side = up.cross(out).normalized() if up.cross(out).length > .1 else Vector((1, 0, 0))
            hh = R.uniform(.30, .48)
            C.card(p - n * .02, up, side, hh * aspect(r), hh, r, bend=-hh * .25, nrm=Vector((0, 0, 1)), tag=t0, flip=R.random() < .5)
    for k in range(R.randint(2, 4)):                       # 小苗（參考圖頂上幾株明顯的小苗）
        for _ in range(60):
            x = R.uniform(.25, .75) * L
            h = hit_side(x, R.uniform(.4, .6) * math.pi)
            if h is not None and h[1].z > .6:
                break
        else:
            continue
        r = R.choice(rc['sapling'])
        hh = R.uniform(.28, .42)
        t0 = nt()
        a = R.uniform(0, math.pi)
        for j in range(2):
            s = Vector((math.cos(a + j * math.pi / 2), math.sin(a + j * math.pi / 2), 0))
            C.card(h[0] - Vector((0, 0, .02)), (0, 0, 1), s, hh * aspect(r), hh, r, tag=t0)
    # 2. 兩側苔邊往下垂的苔（苔面朝外、往下掛）
    nd, tries = 0, 0
    while nd < int(4.5 * L) and tries < 800:
        tries += 1
        x = R.uniform(.08, .92) * L
        th = R.choice((1, -1)) * R.uniform(.05, .35) * math.pi + (0 if R.random() < .5 else math.pi)
        h = hit_side(x, th)
        if h is None or abs(h[1].z) > .55 or fmoss[h[2]] < .45:
            continue
        nd += 1
        r = R.choice(rc['mossdrape'])
        n = Vector((h[1].x, h[1].y, 0)).normalized()
        side = Vector((0, 0, 1)).cross(n).normalized()
        hh = R.uniform(.16, .30)
        top = h[0] + n * .015 + Vector((0, 0, hh * .25))
        C.card(top + Vector((0, 0, -hh)), (0, 0, 1), side, hh * aspect(r), hh, r, bend=-.05, nrm=n, tag=nt(), flip=R.random() < .5)
    # 3. 小褐蕈：側面（半腰以下）、苔邊、腳邊
    nm_, tries = 0, 0
    while nm_ < int(4.5 * L) and tries < 800:
        tries += 1
        x = R.uniform(.08, .92) * L
        th = R.uniform(-.35, .35) * math.pi + (0 if R.random() < .5 else math.pi)
        h = hit_side(x, th)
        if h is None or h[1].z < -.25 or h[0].z < .03:
            continue
        nm_ += 1
        r = R.choice(rc['mush'])
        hh = R.uniform(.09, .15)
        up = (Vector((0, 0, 1)) * .8 + h[1] * .2).normalized()
        t0 = nt()
        a = math.atan2(h[1].y, h[1].x)
        for j in range(2):
            s = Vector((math.cos(a + math.pi / 2 + j * math.pi / 2), math.sin(a + math.pi / 2 + j * math.pi / 2), 0))
            C.card(h[0] - up * .012, up, s, hh * aspect(r), hh, r, tag=t0, segs=1)
    # 3b. 腳邊土堆上一叢叢小褐蕈（參考圖樹幹腳下一路都有）
    for k in range(int(1.3 * L)):
        x = R.uniform(.06, .94) * L
        sd = R.choice((-1, 1))
        y = b['axis_y'](V, x) + sd * b['out_r'](V, x) * R.uniform(1.05, 1.40)
        hg = tree.ray_cast(Vector((x, y, 2.0)), Vector((0, 0, -1)), 3)
        if hg[0] is not None and (hg[0].z > .20 or mi[hg[2]] != 0):         # 打到大香菇（第二槽）不放
            continue
        p = hg[0].copy() if hg[0] is not None else Vector((x, y, 0.0))
        t0 = nt()
        for c_ in range(R.randint(1, 3)):
            q = p + Vector((R.uniform(-.06, .06), R.uniform(-.06, .06), 0))
            r = R.choice(rc['mush'])
            hh = R.uniform(.10, .17)
            a = R.uniform(0, math.pi)
            for j in range(2):
                s_ = Vector((math.cos(a + j * math.pi / 2), math.sin(a + j * math.pi / 2), 0))
                C.card(q - Vector((0, 0, .015)), (0, 0, 1), s_, hh * aspect(r), hh, r, tag=t0, segs=1)
    # 3c. 原本長在樹幹側面的層狀菌叢（V['fungi']）改到地上：那個位置的腳邊一大叢蕈；兩頭洞口外的地上也各一叢
    spots = []
    for f, ang, cnt in V['fungi']:
        sd = -1 if ang > 0 else 1                                  # 正角＝-Y 側（正面）
        spots.append((f * L, sd, 3, 1.35, 1.65))                  # 11/24 那裡改成立在地上的大香菇（本體第二槽）：外面再陪兩三朵小的
    for e, x in ((0, -.02 * L), (1, 1.02 * L)):
        spots.append((x, R.choice((-1, 1)), 5, .20, .55))
    for xc, sd, cnt, r0, r1 in spots:
        xx = min(max(xc, 0), L)
        t0 = nt()
        for c_ in range(cnt):
            x = xc + R.uniform(-.22, .22)
            y = b['axis_y'](V, xx) + sd * b['out_r'](V, xx) * R.uniform(r0, r1)
            hg = tree.ray_cast(Vector((x, y, 2.0)), Vector((0, 0, -1)), 3)
            if hg[0] is not None and (hg[0].z > .22 or mi[hg[2]] != 0):
                continue
            q = hg[0].copy() if hg[0] is not None else Vector((x, y, 0.0))
            r = R.choice(rc['mush'])
            hh = R.uniform(.14, .26)
            a = R.uniform(0, math.pi)
            for j in range(2):
                s_ = Vector((math.cos(a + j * math.pi / 2), math.sin(a + j * math.pi / 2), 0))
                C.card(q - Vector((0, 0, .015)), (0, 0, 1), s_, hh * aspect(r), hh, r, tag=t0, segs=1)
    # 4. 發光小蕈：兩頭洞口裡（內壁的地板上）
    for e, x in ((0, .10 * L), (1, .90 * L)):
        o_ = ax(x) + Vector((0, 0, .1))
        for k in range(2):
            h = tree.ray_cast(o_ + Vector((R.uniform(-.05, .05), R.uniform(-.12, .12), 0)), Vector((0, 0, -1)), V['R'] * 2)
            if h[0] is None or h[1].z < .5 or mi[h[2]] != 0:
                continue
            r = R.choice(rc['glow'])
            hh = R.uniform(.07, .11)
            t0 = nt()
            for j in range(2):
                a = R.uniform(0, math.pi) + j * math.pi / 2
                C.card(h[0] - Vector((0, 0, .01)), (0, 0, 1), (math.cos(a), math.sin(a), 0), hh * aspect(r), hh, r, tag=t0, segs=1)
    # 5. 地上：腳邊的蕨、落葉
    for k in range(int(2.6 * L)):                           # 參考圖腳邊一路都是蕨
        x = R.uniform(.05, .95) * L
        sd = R.choice((-1, 1))
        y = b['axis_y'](V, x) + sd * (b['out_r'](V, x) * R.uniform(1.0, 1.25) + R.uniform(.02, .25))
        p = Vector((x, y, 0.0))
        hg = tree.ray_cast(p + Vector((0, 0, 2)), Vector((0, 0, -1)), 3)
        if hg[0] is not None:                                   # 打到腳邊土堆：長在土堆上；打到樹幹（太高）就不放
            if hg[0].z > .22 or mi[hg[2]] != 0:
                continue
            p = hg[0].copy()
        t0 = nt()
        for j in range(R.randint(3, 5)):
            r = R.choice(rc['fern'])
            a = math.atan2(sd, 0) + R.uniform(-1.3, 1.3)
            out = Vector((math.cos(a), math.sin(a), 0))
            tilt = R.uniform(.45, .9)
            up = (Vector((0, 0, 1)) * math.cos(tilt) + out * math.sin(tilt)).normalized()
            side = up.cross(out).normalized()
            hh = R.uniform(.32, .50)
            C.card(p - Vector((0, 0, .02)), up, side, hh * aspect(r), hh, r, bend=-hh * .3, nrm=Vector((0, 0, 1)), tag=t0, flip=R.random() < .5)
    nl, tries = 0, 0
    while nl < int(16 * L) and tries < 2000:
        tries += 1
        x = R.uniform(-.05, 1.05) * L
        sd = R.choice((-1, 1))
        y = b['axis_y'](V, min(max(x, 0), L)) + sd * (b['out_r'](V, min(max(x, 0), L)) * R.uniform(.85, 1.6) + R.uniform(0, .5))
        p = Vector((x, y, 0.0))
        hh = tree.ray_cast(p + Vector((0, 0, 2)), Vector((0, 0, -1)), 3)
        z = .006 + R.uniform(0, .006)
        if hh[0] is not None:
            if (hh[0].z > .10 and fmoss[hh[2]] < .3) or mi[hh[2]] != 0:
                continue
            p, z = hh[0], .006
            nrm = hh[1]
        else:
            nrm = Vector((0, 0, 1))
        nl += 1
        r = R.choice(rc['leaf'])
        s = R.uniform(.07, .12)
        a = R.uniform(0, 2 * math.pi)
        fwd = Vector((math.cos(a), math.sin(a), 0))
        fwd = (fwd - nrm * fwd.dot(nrm)).normalized()
        side = nrm.cross(fwd).normalized()
        C.card(p + nrm * z - fwd * s * .5, fwd, side, s * aspect(r), s, r, bend=.01, nrm=nrm, tag=nt(), segs=1)
    # 11/24 使用者：「不要卡進去」→ 一組卡（一叢蕨、一片垂苔、一叢小蕈）只要有一點埋進本體超過 3 cm 就整組拿掉
    def _odd(p, d):
        k, q = 0, p.copy()
        for _ in range(60):
            h = tree.ray_cast(q, d, 20)
            if h[0] is None:
                break
            k += 1
            q = h[0] + d * 1e-4
        return k % 2 == 1
    # 埋進去的點推回表面（垂苔、蕨葉順著樹幹彎過去，不整組丟掉）；推不回來（很深）的那一組才丟
    moved, bad = 0, set()
    for _ in range(3):
        deep = {}
        for i, c in enumerate(C.V):
            q = Vector(c)
            loc, nr, _, dist = tree.find_nearest(q, 1.0)
            if loc is None or (q - loc).dot(nr) > -.02:
                continue
            if dist > .06 and not all(_odd(q, Vector(dd).normalized()) for dd in ((0, 0, 1), (1, .13, .07), (-.11, 1, .05))):
                continue
            deep[i] = (loc, nr, dist)
        if not deep:
            break
        for i, (loc, nr, dist) in deep.items():
            if dist > .15:
                continue
            C.V[i] = tuple(loc + nr * .006)
            moved += 1
    for i, c in enumerate(C.V):
        q = Vector(c)
        loc, nr, _, dist = tree.find_nearest(q, 1.0)
        if loc is not None and (q - loc).dot(nr) < -.03 and (dist <= .06 or all(_odd(q, Vector(dd).normalized()) for dd in ((0, 0, 1), (1, .13, .07), (-.11, 1, .05)))):
            bad.update(t for f, t in zip(C.F, C.tag) if i in f)
    keep = [k for k, t in enumerate(C.tag) if t not in bad]
    C.F, C.tag = [C.F[k] for k in keep], [C.tag[k] for k in keep]
    print('plant cards', len(C.F), 'quads in', tag[0], 'groups; pushed out', moved, 'verts; dropped', len(bad), 'groups')
    return C


# ---------------------------------------------------------------- 一次跑完
def _clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.context.view_layer.update()


def _select(objs, active):
    for o in bpy.context.view_layer.objects:
        if o is not None:
            o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active


def _tri(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def _triangulate(o):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    dead = [f for f in bm.faces if f.calc_area() < 1e-9]
    if dead:
        bmesh.ops.delete(bm, geom=dead, context='FACES')
    bm.to_mesh(o.data)
    bm.free()


def export_t(lods, col, root):
    allm = [o for lst in lods.values() for o in lst] + [col]
    bpy.context.view_layer.update()
    os.makedirs(EXP, exist_ok=True)
    col.hide_render = False
    _select(allm + [root], root)
    bpy.ops.export_scene.fbx(filepath=f'{EXP}/{ASSET}_{VER}.fbx', use_selection=True, object_types={'MESH', 'EMPTY'},
                             apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', bake_space_transform=True,
                             axis_forward='-Z', axis_up='Y', mesh_smooth_type='FACE', use_mesh_modifiers=True, colors_type='LINEAR',
                             add_leaf_bones=False, bake_anim=False, path_mode='STRIP', embed_textures=False)
    try:
        _select(lods[0] + [root], root)
        bpy.ops.export_scene.gltf(filepath=f'{EXP}/{ASSET}_{VER}.glb', use_selection=True, export_format='GLB', export_yup=True)
    except Exception as e:
        print('glb', e)
    col.hide_render = True
    info = {lv: {o.name: _tri(o) for o in lst} for lv, lst in lods.items()}
    info['collision'] = _tri(col)
    print(json.dumps(info, indent=1))
    return info


def run_t(variant):
    configure(variant)
    log = WORKTEX + '_run_t.log'
    os.makedirs(os.path.dirname(log), exist_ok=True)
    t = time.time()

    def Lg(m):
        open(log, 'a', encoding='utf-8').write(f'{round(time.time() - t)}s {m}\n')
        print('RUN', m)
    open(log, 'w').write('')
    try:
        _clear()
        b = _build()
        hi = b['build'](variant, quick=False)
        Lg('high %d objects' % len(hi))
        b['dress'](b['VAR'], quick=False)
        os.makedirs(HERE6 + '/blend', exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=f'{HERE6}/blend/{ASSET}_high_{VER}.blend', copy=True)
        Lg('high saved')
        _clear()                                           # 高模已存檔；低模、植物卡只用 B 裡算好的資料（方塊表、菌位置等），不打高模
        g = _coll(_cn('Game'))
        lods = {}
        bodies = {}
        for lv in (0, 1, 2):
            parts = layer_parts(lv)
            body = _join(parts, f'{ASSET}_LOD{lv}')
            for c in list(body.users_collection):
                c.objects.unlink(body)
            g.objects.link(body)
            _triangulate(body)
            bodies[lv] = body
            Lg(f'LOD{lv} body {_tri(body)} tris')
        cards = make_cards(bodies[0])
        for lv in (0, 1, 2):
            d = cards.obj(f'{DET}_LOD{lv}', PLANT_KEEP[lv], seed=lv)
            _triangulate(d)
            lods[lv] = [bodies[lv], d]
            Lg(f'LOD{lv} detail {_tri(d)} tris')
        cobjs = b['build'](variant, quick=False, low=COLRES, col=True, pre='C_')
        for o in cobjs:
            o.data.materials.clear()
        col = _join(cobjs, f'{ASSET}_Collision')
        for c in list(col.users_collection):
            c.objects.unlink(col)
        g.objects.link(col)
        for ca in list(col.data.color_attributes):
            col.data.color_attributes.remove(ca)
        while col.data.uv_layers:
            col.data.uv_layers.remove(col.data.uv_layers[0])
        col.hide_render = True
        col.display_type = 'WIRE'
        root = bpy.data.objects.new(ASSET, None)
        g.objects.link(root)
        for o in [o for lst in lods.values() for o in lst] + [col]:
            o.data.name = o.name
            o.parent = root
        _load('dr_pivot.py')['to_bottom_centre'](root, bodies[0])
        Lg('finish ' + json.dumps(export_t(lods, col, root)))
        for c in bpy.data.collections:
            if c.name.endswith('_Game'):
                c.hide_render = c.hide_viewport = False
        bpy.ops.wm.save_as_mainfile(filepath=f'{HERE6}/blend/{ASSET}_{VER}.blend', copy=True)
        Lg('DONE')
    except Exception:
        Lg('ERROR ' + traceback.format_exc())


if __name__ == '__main__' and '--' in sys.argv:
    a = sys.argv[sys.argv.index('--') + 1:]
    run_t(a[0] if a else 'B')
