# DR06 倒伏巨木的遊戲用模型：低模 → 拆 UV → 烘焙 → 植物 → LOD1／LOD2 → 碰撞 → FBX／GLB。
# 沿用 D2 根與木的 game_dr02.py（補邊、貼圖輸出、遊戲材質、藏起來的面怎麼刪、烘焙怎麼分組），換掉只能處理「管子」的部分：
#   - 低模裡除了管子（樹幹、根、斷枝），還有泥丘、石頭、坑、斷口木刺、層狀菌這些不是管子的件。
#     管子照 DR02：沿長度每 SEG 公尺切一個長方形 UV 島（圍一圈 × 沿長度，公尺）；其他件用 Smart UV，再縮放成同樣的「每公尺幾格」。
#     全部併成一個物件用 Blender 的 Pack Islands 排進一張圖（不旋轉：樹皮島的方向一致，共用的樹皮細節法線才能沿 UV0 重複），
#     排完再照 part 編號拆回一件一件，後面刪藏起來的面、烘焙分組、LOD 都照 DR02。
#   - 細根鬚、遊戲植物（蕨、闊葉、小樹苗、蕈、落葉）併成 Detail_DR06_Plants，顏色畫在圖集最下面那一條。
# 用法（背景）：blender -b --python game_dr06.py -- B
import bpy, bmesh, math, os, json, re, sys, importlib, time, traceback
import numpy as np
from mathutils import Vector, Matrix

_R2 = 'D:/yun-jing-d2-logs/art/source/d2-roots-b'
_src = _R2 + '/game_dr02.py'
exec(compile(open(_src, encoding='utf-8').read(), _src, 'exec'), globals())

HERE = _R2                                      # dr_pivot.py 在這
HERE6 = 'D:/yun-jing-d2-logs/art/source/d2-logs-b'
ROOT = 'D:/yun-jing-d2-logs'
VER = 'v001'
SIZE = 2048
STRIP = 128 / 2048                              # 最下面一條：葉子、蕈、細枝、根鬚的顏色
SEG = 4.0                                       # 管子沿長度每 4 m 切一個 UV 島
LOWRES = (.25, 8, 28, 1.0)                      # 低模：每 0.25 m 一環；細根 8 邊，樹幹照周長加到 28 邊
COLRES = (1.0, 8, 8, 1.0)                       # 碰撞殼：每 1 m 一環、8 邊
SETS = 'A'
NAMES = {'A': 'DR06_FallenTrunk_A', 'B': 'DR06_FallenTrunk_B'}
DET = 'Detail_DR06_Plants'
LEAF = {'Ferns': (0.0, .18, (.13, .21, .095), (.27, .37, .18)),
        'Leaves': (.18, .32, (.18, .27, .145), (.34, .43, .26)),
        'Sapling': (.32, .44, (.30, .35, .13), (.60, .62, .28)),        # 參考圖：黃綠的闊葉
        'Litter0': (.44, .54, (.30, .17, .08), (.62, .38, .17)),        # 參考圖：橘褐落葉
        'Litter1': (.54, .64, (.24, .16, .09), (.50, .34, .18)),
        'Litter2': (.64, .74, (.33, .24, .11), (.64, .49, .25))}
LEAF_X = 1.0
# 平塗色塊（sRGB）：蕈的五種顏色、細枝、根鬚
MUSH = [(.53, .48, .40), (.81, .78, .70), (.77, .70, .60), (.58, .44, .30), (.42, .29, .19)]       # 柄基、柄、菌褶、傘、傘頂深色（拿來比對高模蕈的頂點色）
MUSH_PAINT = [(.44, .37, .28), (.72, .66, .56), (.68, .60, .49), (.56, .46, .35), (.38, .29, .20)]   # 實際畫進圖集的顏色：參考圖的蕈是淡褐、柄淺褐，不是橘傘白柄
FLAT = {'Mush': (.74, .88), 'Twig': (.88, .92), 'Hair': (.92, .95), 'Shard': (.95, 1.0)}
SHARD_C = ((.36, .29, .21), (.80, .73, .61))      # 木刺：根部（貼著斷面、暗）→ 尖端（風化、淺）
TWIG_C, HAIR_C = (.30, .25, .20), (.24, .19, .15)
COL_MIN_R = .25                                 # 碰撞殼：斷枝基部半徑 > 0.25 R × 1.3 才算
VARIANT = ASSET = EXP = TEX = WORKTEX = None
B = None


def configure(v):
    global VARIANT, ASSET, EXP, TEX, WORKTEX
    VARIANT = v
    ASSET = NAMES[v]
    EXP = f'{ROOT}/art/exports/d2-logs-b/{ASSET}'
    TEX = EXP + '/Textures'
    WORKTEX = os.environ.get('DR_WORK6', 'D:/yun-jing-cache/dr06-work/') + f'bake_{v}'     # 烘焙中間檔，不進版本庫


def _build():
    global B
    if B is None:
        p = HERE6 + '/build_dr06.py'
        B = {'__file__': p, '__name__': 'build_dr06'}
        exec(compile(open(p, encoding='utf-8').read(), p, 'exec'), B)
    B['set_variant'](VARIANT)
    return B


def _cn(kind):
    return f"DR06_{_build()['VAR']['name']}_{kind}"


def _edit(o, fn):
    _select([o], o)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    try:
        fn()
    finally:
        bpy.ops.object.mode_set(mode='OBJECT')


# ---------------------------------------------------------------- 低模 + UV
def _tube_uv(o):
    """管子：沿長度每 SEG 公尺一個長方形島（u = 圍一圈的公尺數、v = 沿長度公尺）；封口面用平面投影各自一個小島。
    TileUV = dr_core 的每 2.6 m 重複的樹皮 UV。"""
    rr, ss = list(o['ring_r']), list(o['ring_s'])
    me = o.data
    bm = bmesh.new()
    bm.from_mesh(me)
    up = bm.loops.layers.uv['Param']
    ut = bm.loops.layers.uv['UV']
    ua = bm.loops.layers.uv.new('Atlas')
    fr = bm.faces.layers.int['ring']
    nseg = max(1, int(math.ceil(ss[-1] / SEG)))
    per = max(1, int(math.ceil((len(ss) - 1) / nseg)))
    for f in bm.faces:
        k = f[fr]
        if k < 0:
            n = f.normal
            a = n.cross(Vector((0, 0, 1)) if abs(n.z) < .9 else Vector((1, 0, 0))).normalized()
            b = n.cross(a)
            c = f.calc_center_median()
            for lp in f.loops:
                d = lp.vert.co - c
                lp[ua].uv = (500 + d.dot(a), 500 + d.dot(b))
            continue
        si = min(k // per, nseg - 1)
        k0, k1 = si * per, min((si + 1) * per, len(ss) - 1)
        w = 2 * math.pi * float(np.mean(rr[k0:k1 + 1]))
        for lp in f.loops:
            a, s = lp[up].uv
            lp[ua].uv = (si * 60.0 + a * w, s - ss[k0])
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


def _smart_uv(o):
    """不是管子的件：Smart UV，再整體縮放成公尺（UV 面積 = 3D 面積）。"""
    me = o.data
    while me.uv_layers:
        me.uv_layers.remove(me.uv_layers[0])
    me.uv_layers.new(name='UVMap')
    _edit(o, lambda: bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.0, scale_to_bounds=False))
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv['UVMap']
    a3 = sum(f.calc_area() for f in bm.faces)
    au = 0.0
    for f in bm.faces:
        p = [lp[uv].uv for lp in f.loops]
        for i in range(1, len(p) - 1):
            au += abs((p[i] - p[0]).cross(p[i + 1] - p[0])) * .5
    k = math.sqrt(a3 / max(au, 1e-9))
    for f in bm.faces:
        for lp in f.loops:
            lp[uv].uv = lp[uv].uv * k + Vector((300.0, 0.0))
    bm.to_mesh(me)
    bm.free()
    me.uv_layers.new(name='TileUV').data.foreach_set('uv', np.array([d.uv[:] for d in me.uv_layers['UVMap'].data], np.float32).ravel())


def make_low():
    b = _build()
    for kind in ('Low', 'LowFull', 'Game', 'HairLow'):
        c = bpy.data.collections.get(_cn(kind))
        if c:
            for o in list(c.objects):
                bpy.data.objects.remove(o, do_unlink=True)
    objs = b['build'](VARIANT, quick=False, low=LOWRES, pre='L_')
    hairs = [o for o in objs if o.name.startswith('L_Hair')]
    hc = _coll(_cn('HairLow'))
    for o in hairs:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        hc.objects.link(o)
    hc.hide_render = hc.hide_viewport = True
    parts = [o for o in objs if o not in hairs]
    for o in parts:
        if 'ring_r' in o:
            _tube_uv(o)
        else:
            _smart_uv(o)
        o.data.materials.clear()
        for ca in list(o.data.color_attributes):
            o.data.color_attributes.remove(ca)
        for an in ('ring', 'Peel', 'MudMoss'):
            at = o.data.attributes.get(an)
            if at:
                o.data.attributes.remove(at)
    # 全部併起來排 UV，再照 part 拆回去
    names = [o.name for o in parts]
    for i, o in enumerate(parts):
        at = o.data.attributes.new('part', 'INT', 'FACE')
        at.data.foreach_set('value', np.full(len(o.data.polygons), i, np.int32))
    allm = _join([_dup(o) for o in parts], 'DR06_UVPack')
    sc = bpy.context.scene
    sc.tool_settings.use_uv_select_sync = True
    allm.data.uv_layers.active = allm.data.uv_layers['UVMap']

    def pack():
        bpy.ops.uv.pack_islands(udim_source='CLOSEST_UDIM', rotate=False, scale=True, merge_overlap=False,
                                margin_method='FRACTION', margin=.0035, shape_method='CONCAVE')
    _edit(allm, pack)
    uvA = np.empty(len(allm.data.loops) * 2, np.float32)
    allm.data.uv_layers['UVMap'].data.foreach_get('uv', uvA)
    uvA = uvA.reshape(-1, 2)
    uvA[:, 0] = uvA[:, 0] * (1 - STRIP)
    uvA[:, 1] = STRIP + uvA[:, 1] * (1 - STRIP)
    part = np.empty(len(allm.data.polygons), np.int32)
    allm.data.attributes['part'].data.foreach_get('value', part)
    ls = np.empty(len(allm.data.polygons), np.int32)
    allm.data.polygons.foreach_get('loop_start', ls)
    lt = np.empty(len(allm.data.polygons), np.int32)
    allm.data.polygons.foreach_get('loop_total', lt)
    # 每件的面在併起來的網格裡是依序排的（join 照物件順序接上去），所以照 part 依序取回 UV
    off = 0
    for i, o in enumerate(parts):
        n = len(o.data.loops)
        fsel = np.nonzero(part == i)[0]
        idx = np.concatenate([np.arange(ls[f], ls[f] + lt[f]) for f in fsel])
        assert len(idx) == n, (o.name, len(idx), n)
        uvo = uvA[idx].copy()
        sh = o.data.attributes.get('Shard')
        if sh is not None:
            # 木刺（1–2 cm 厚、一束擠在一起）烘出來的法線會打到隔壁那根，引擎裡整根發黑：改指到最下面一條的淺木色漸層（根部暗、尖端淺，法線平）
            fs = np.empty(len(o.data.polygons), np.int32)
            sh.data.foreach_get('value', fs)
            su = np.empty(len(o.data.vertices), np.float32)
            o.data.attributes['ShardU'].data.foreach_get('value', su)
            vi = np.empty(n, np.int32)
            o.data.loops.foreach_get('vertex_index', vi)
            ols = np.empty(len(o.data.polygons), np.int32)
            o.data.polygons.foreach_get('loop_start', ols)
            olt = np.empty(len(o.data.polygons), np.int32)
            o.data.polygons.foreach_get('loop_total', olt)
            sl = np.concatenate([np.arange(ols[f], ols[f] + olt[f]) for f in np.nonzero(fs)[0]] or [np.zeros(0, np.int64)])
            a0, a1 = FLAT['Shard']
            uvo[sl, 0] = a0 + (a1 - a0) * (.08 + .84 * su[vi[sl]])
            # 橫向：每個面的兩條長邊分別對到色條的不同高度（中間內插），色條上畫了沿長度的纖維紋，木片近看才有一絲一絲
            fsh = np.nonzero(fs)[0]
            jj = np.concatenate([np.arange(olt[f]) for f in fsh] or [np.zeros(0, np.int64)])
            fo = np.concatenate([np.full(olt[f], f) for f in fsh] or [np.zeros(0, np.int64)])
            y0 = .06 + .58 * ((fo * .618034) % 1.0)
            uvo[sl, 1] = STRIP * (y0 + .30 * ((jj == 1) | (jj == 2)))
        o.data.uv_layers['UVMap'].data.foreach_set('uv', uvo.ravel())
        for an in ('Shard', 'ShardU'):
            if o.data.attributes.get(an):
                o.data.attributes.remove(o.data.attributes[an])
    # 每公尺幾格（樹皮細節法線的重複次數照這個算）
    t = bpy.data.objects[names[0]]
    me = t.data
    l0 = me.loops[me.polygons[len(me.polygons) // 2].loop_start]
    p0 = me.polygons[len(me.polygons) // 2]
    v0, v1 = me.vertices[p0.vertices[0]].co, me.vertices[p0.vertices[1]].co
    u0 = Vector(me.uv_layers['UVMap'].data[p0.loop_start].uv)
    u1 = Vector(me.uv_layers['UVMap'].data[p0.loop_start + 1].uv)
    upm = (u1 - u0).length / max((v1 - v0).length, 1e-6)
    sc['dr02_uv_per_m'] = upm
    print('atlas', round(upm * SIZE, 1), 'px per metre')
    bpy.data.objects.remove(allm, do_unlink=True)
    for o in parts:
        o.data.attributes.remove(o.data.attributes['part'])
        for k in ('ring_r', 'ring_s'):
            if k in o:
                del o[k]
        o.data.materials.append(_bake_mats()[0][0])
        o.data.uv_layers['UVMap'].active = True
        o.data.uv_layers['UVMap'].active_render = True
    hidden = _hidden_verts(parts)
    full = _coll(_cn('LowFull'))
    for o in parts:
        c = _dup(o)
        c.name = c.data.name = o.name.replace('L_', 'F_', 1)
        for cc in list(c.users_collection):
            cc.objects.unlink(c)
        full.objects.link(c)
    full.hide_render = full.hide_viewport = True
    parts, gone = _delete_hidden(parts, hidden)
    sc['dr06_hidden_tris_removed'] = gone
    groups = _colour(parts, near=.45)
    outs = []
    for gi, idx in enumerate(groups):
        srcs = [parts[i].name[2:] for i in idx]
        go = _join([parts[i] for i in idx], f'DR06_LowG{gi:02d}') if len(idx) > 1 else parts[idx[0]]
        go.name = go.data.name = f'DR06_LowG{gi:02d}'
        go['srcs'] = srcs
        outs.append(go)
    print('bake groups', len(outs), [len(g) for g in groups], 'tris', sum(len(p.vertices) - 2 for o in outs for p in o.data.polygons))
    return outs


def _dup(o):
    c = o.copy()
    c.data = o.data.copy()
    for cc in o.users_collection:
        cc.objects.link(c)
    return c


# ---------------------------------------------------------------- 烘焙
def _mask_emission(objs):
    """烘「樹皮遮罩」用：高模的樹皮發白光（剝皮露木的地方 Peel = 1 → 黑），泥、石、斷口木頭、菌全黑。回傳還原用的函式。"""
    undo = []
    for m in {s.material for o in objs for s in o.material_slots if s.material}:
        nt = m.node_tree
        bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if bsdf is None:
            continue
        ec, es = bsdf.inputs['Emission Color'], bsdf.inputs['Emission Strength']
        old = (tuple(ec.default_value), es.default_value, [l.from_socket for l in ec.links])
        new_nodes = []
        es.default_value = 1.0
        if m.name.startswith('DR06_Bark'):
            at = nt.nodes.new('ShaderNodeAttribute')
            at.attribute_name = 'Peel'
            inv = nt.nodes.new('ShaderNodeMath')
            inv.operation = 'SUBTRACT'
            inv.inputs[0].default_value = 1.0
            nt.links.new(at.outputs['Fac'], inv.inputs[1])
            nt.links.new(inv.outputs[0], ec)
            new_nodes = [at, inv]
        else:
            for l in list(ec.links):
                nt.links.remove(l)
            ec.default_value = (0, 0, 0, 1)

        def restore(nt=nt, ec=ec, es=es, old=old, new_nodes=new_nodes):
            for l in list(ec.links):
                nt.links.remove(l)
            for n in new_nodes:
                nt.nodes.remove(n)
            ec.default_value, es.default_value = old[0], old[1]
            for s in old[2]:
                nt.links.new(s, ec)
        undo.append(restore)
    return undo


def bake(samples=24, log=None, kinds=None):
    os.makedirs(WORKTEX, exist_ok=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    try:
        pr = bpy.context.preferences.addons['cycles'].preferences
        for kd in ('OPTIX', 'CUDA'):
            try:
                pr.compute_device_type = kd
                break
            except TypeError:
                pass
        pr.get_devices()
        for d in pr.devices:
            d.use = True
        sc.cycles.device = 'GPU'
    except Exception as e:
        print('gpu', e)
    hi_c, lo_c = bpy.data.collections[_cn('High')], bpy.data.collections[_cn('Low')]
    for c in (hi_c, lo_c):
        c.hide_render = c.hide_viewport = False
    lows = sorted([o for o in lo_c.objects if o.name.startswith('DR06_LowG')], key=lambda o: o.name)
    highs = {o.name: o for o in hi_c.objects if not o.name.startswith('Hair')}
    bm_ = _bake_mats()
    for o in lows:
        o.data.materials[0] = bm_[0][0]
    for o in bpy.context.view_layer.objects:
        o.hide_render = True
    for o in list(highs.values()) + lows:
        o.hide_viewport = False
        o.hide_set(False)
    ground = bpy.data.objects.get('DR06_BakeGround')
    if ground is None:
        me = bpy.data.meshes.new('DR06_BakeGround')
        s_ = 60
        me.from_pydata([(-s_, -s_, 0), (s_, -s_, 0), (s_, s_, 0), (-s_, s_, 0)], [], [(0, 1, 2, 3)])
        ground = bpy.data.objects.new('DR06_BakeGround', me)
        sc.collection.objects.link(ground)
    out = {}
    undo = []
    for kind, btype, color, kw in (('BaseColor', 'DIFFUSE', True, dict(pass_filter={'COLOR'})), ('Roughness', 'ROUGHNESS', False, {}),
                                   ('Normal', 'NORMAL', False, dict(normal_space='TANGENT')), ('AO', 'AO', False, {}),
                                   ('BarkMask', 'EMIT', False, {})):
        if kinds and kind not in kinds:
            continue
        if kind == 'BarkMask':
            undo = _mask_emission(highs.values())
        m, tn = bm_[0]
        tn.image = _image(f'{ASSET}_A_{kind}', color)
        sc.cycles.samples = samples * 2 if kind == 'AO' else (max(8, samples // 2) if kind == 'BaseColor' else 8)
        ground.hide_render = kind != 'AO'
        for low in lows:
            src = [highs[n] for n in low['srcs'] if n in highs]
            for o in highs.values():
                o.hide_render = kind != 'AO'
            for o in src:
                o.hide_render = False
            for o in lows:
                o.hide_render = o is not low
            _select(src + [low], low)
            bpy.ops.object.bake(type=btype, use_selected_to_active=True, cage_extrusion=.30, max_ray_distance=.75, margin=1,
                                margin_type='EXTEND', use_clear=False, **kw)
        im = tn.image
        im.filepath_raw = f'{WORKTEX}/{ASSET}_A_{kind}.png'
        im.file_format = 'PNG'
        im.save()
        out[kind] = im.filepath_raw
        print('baked', kind)
        if log:
            log('baked ' + kind)
    for f in undo:
        f()
    for o in bpy.context.view_layer.objects:
        o.hide_render = False
    ground.hide_render = True
    return out


def _hidden_verts(objs, margin=.03, zcut=-.5):
    """同 DR02（頂點鑽在別件裡面超過 margin，或在地面以下 zcut），多一道確認：往 ±x、±y、±z 六個方向打都會打到那一件才算在裡面。
    DR06 的斷枝是開口的管子（根部埋在樹幹裡、沒封口），只看最近點和法線，開口外面的樹幹頂點會被當成在斷枝裡面而刪掉，樹幹上開一個洞。"""
    from mathutils.bvhtree import BVHTree
    dirs = [Vector(d) for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
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
                if loc is not None and dist > margin and (q - loc).dot(nrm) < 0 and all(tj.ray_cast(q, d, 50)[0] is not None for d in dirs):
                    hide[vi] = True
        out.append(hide)
    return out


_finish_textures0 = finish_textures
# DR02 的貼圖後處理會把苔壓暗 12%、去飽和 25%（對齊核心組神木 GT01）。DR06 照參考圖要亮的橄欖黃綠苔，
# 改成壓暗 5%、去飽和 8%：從 game_dr02.py 原文取出這個函式、只換這兩個數字再定義一次（DR02 原檔不動）。
_src_ft = open(_src, encoding='utf-8').read()
_i0 = _src_ft.index('def finish_textures():')
_i1 = _src_ft.index(chr(10) + 'def ', _i0 + 10)
_ft = _src_ft[_i0:_i1]
for _a, _b in (('(1 - .12 * moss)', '(1 - .05 * moss)'), ('(.25 * moss)', '(.08 * moss)')):
    assert _ft.count(_a) == 1, _a
    _ft = _ft.replace(_a, _b)
exec(compile(_ft, _src, 'exec'), globals())
_finish_textures0 = finish_textures
_game_material0 = game_material


def game_material(S, name=None):
    """DR02 的預覽材質，細節法線也照 Albedo alpha 遮（URP Lit 的 Detail Mask 同時遮細節底色和細節法線）；
    DR02 全是樹皮所以沒差，DR06 的泥、石、坑、斷口木頭不能有樹皮紋。"""
    m = _game_material0(S, name) if name else _game_material0(S)
    nt = m.node_tree
    fp = lambda n: os.path.basename(n.image.filepath) if n.image else ''
    alb = next(n for n in nt.nodes if n.type == 'TEX_IMAGE' and fp(n).endswith('_Albedo.png') and 'D2Bark' not in fp(n))
    dn = [n for n in nt.nodes if n.type == 'NORMAL_MAP' and n.inputs['Color'].links
          and 'D2Bark' in fp(n.inputs['Color'].links[0].from_node)]
    for d in dn:
        geo = nt.nodes.new('ShaderNodeNewGeometry')
        mx = nt.nodes.new('ShaderNodeMix')
        mx.data_type = 'VECTOR'
        out_links = [l.to_socket for l in d.outputs[0].links]
        nt.links.new(alb.outputs['Alpha'], mx.inputs[0])
        nt.links.new(geo.outputs['Normal'], mx.inputs[4])
        nt.links.new(d.outputs[0], mx.inputs[5])
        for s in out_links:
            nt.links.new(mx.outputs[1], s)
    return m


def finish_textures():
    """照 DR02 補邊、畫葉子那一條、輸出四張圖；再在那一條畫上蕈、細枝、根鬚的平塗色塊。"""
    _finish_textures0()
    h0 = int(STRIP * SIZE)
    p = f'{TEX}/{ASSET}_A_Albedo.png'
    im, base = _px(p)
    bpy.data.images.remove(im)
    a, b = int(FLAT['Mush'][0] * SIZE), int(FLAT['Mush'][1] * SIZE)
    w = (b - a) / len(MUSH)
    for j, c in enumerate(MUSH_PAINT):
        base[:h0, int(a + j * w):int(a + (j + 1) * w), :3] = c
    for nm, c in (('Twig', TWIG_C), ('Hair', HAIR_C)):
        a, b = int(FLAT[nm][0] * SIZE), int(FLAT[nm][1] * SIZE)
        base[:h0, a:b, :3] = c
    a, b = int(FLAT['Shard'][0] * SIZE), int(FLAT['Shard'][1] * SIZE)
    t = np.clip((np.linspace(0, 1, b - a) - .08) / .84, 0, 1)[None, :, None] ** .8
    c0, c1 = np.array(SHARD_C[0]), np.array(SHARD_C[1])
    base[:h0, a:b, :3] = c0 + (c1 - c0) * t
    # 纖維紋：沿長度（x）拉長的深淺條紋＋幾條暗縫（y 方向是木片寬度）
    rs = np.random.RandomState(6)
    yy = np.arange(h0)[:, None] / h0
    xx = np.linspace(0, 1, b - a)[None, :]
    fib = np.zeros((h0, b - a))
    for k in range(10):
        fq, ph = rs.uniform(8, 40), rs.uniform(0, 6.3)
        fib += np.sin(yy * fq * 2 * np.pi + ph + xx * rs.uniform(-1.5, 1.5)) / 10
    crack = (np.abs(np.sin(yy * 23 * 2 * np.pi + xx * 2.0)) < .08) * .35
    base[:h0, a:b, :3] *= np.clip(1 + .22 * fib - crack, .45, 1.3)[..., None]
    a = int(FLAT['Mush'][0] * SIZE)
    base[:h0, a:, 3] = 0
    # 樹皮細節只疊在樹皮上：泥、石、坑、斷口木頭、剝皮露木、層菌的 alpha 歸零（BarkMask 從高模烘來：樹皮 1、其他 0）
    mp = f'{WORKTEX}/{ASSET}_A_BarkMask.png'
    if os.path.exists(mp):
        im, bm = _px(mp)
        bpy.data.images.remove(im)
        bm = _dilate(bm, fill=1.0)
        k = np.clip((bm[..., 0] - .25) / .5, 0, 1)
        k[:h0] = 1
        base[..., 3] *= k
    _save(base, p, True)
    # 法線：射線打到高模薄邊（斷枝口的唇、木刺）背面時，切線空間法線的 Z 會小於 0 → 引擎裡一圈黑。Z < 0.35 的往平的拉、再正規化
    p = f'{TEX}/{ASSET}_A_Normal.png'
    im, nrm = _px(p)
    bpy.data.images.remove(im)
    v = nrm[..., :3] * 2 - 1
    w = np.clip((.35 - v[..., 2]) / .25, 0, 1)[..., None]
    v = v * (1 - w) + np.array([0, 0, 1.0]) * w
    v /= np.linalg.norm(v, axis=-1, keepdims=True) + 1e-6
    nrm[..., :3] = v * .5 + .5
    print('normal fix: %.2f%% pixels pulled flat' % (100 * float((w > 0).mean())))
    _save(nrm, p, False)


def _flat_uv(o, region, idx_of_loop):
    """把物件每個角的 UV 指到色塊 region 裡第 idx 格的中心。"""
    a, b = FLAT[region]
    n = len(MUSH) if region == 'Mush' else 1
    w = (b - a) / n
    uv = o.data.uv_layers[0] if o.data.uv_layers else o.data.uv_layers.new(name='UVMap')
    arr = np.empty(len(o.data.loops) * 2, np.float32).reshape(-1, 2)
    for li in range(len(o.data.loops)):
        j = idx_of_loop(li)
        arr[li] = (a + (j + .5) * w, STRIP * .5)
    uv.data.foreach_set('uv', arr.ravel())


def join_low():
    lo_c = bpy.data.collections[_cn('Low')]
    lows = sorted([o for o in lo_c.objects if o.name.startswith('DR06_LowG')], key=lambda o: o.name)
    for o in lows:
        o.hide_render = o.hide_viewport = False
        if 'srcs' in o:
            del o['srcs']
    old = bpy.data.objects.get(f'{ASSET}_LOD0')
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    low = _join(lows, f'{ASSET}_LOD0')
    low.data.uv_layers.active = low.data.uv_layers['UVMap']
    low.data.uv_layers['UVMap'].active_render = True
    g = _coll(_cn('Game'))
    for c in list(low.users_collection):
        c.objects.unlink(low)
    g.objects.link(low)
    print('LOD0 body tris', sum(len(p.vertices) - 2 for p in low.data.polygons))
    return low


# ---------------------------------------------------------------- 遊戲用植物（Detail_DR06_Plants）
def make_detail():
    import core_plants
    b = _build()
    for nm in list(bpy.data.objects.keys()):
        if nm.startswith((DET, 'DR06_G_')):
            bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
    Base = core_plants.LeafBuf

    class Lite(Base):
        def __init__(self):
            super().__init__()
            self.n = 0

        def leaf(self, origin, along, side, up, L, W, shape, fold=.3, curl=0.0, droop=0.0, tint=(1, 1, 1), nu=7, nv=4, twist=0.0):
            self.n += 1
            if nu >= 8 and nv == 2:          # 蕨的羽片：隔一片留一片、加寬、降面數
                if self.n % 2:
                    return
                W, nu, nv = W * 1.9, 2, 1
            else:
                nu, nv = min(nu, 4), min(nv, 2)
            super().leaf(origin, along, side, up, L, W, shape, fold, curl, droop, tint, nu, nv, twist)
    core_plants.LeafBuf = Lite
    hi_c = bpy.data.collections.get(_cn('High'))
    if hi_c:
        hi_c.hide_viewport = True                # 植物要長在低模表面上：射線只打低模
    low = bpy.data.objects[f'{ASSET}_LOD0']
    try:
        coll = b['dress'](b['VAR'], quick=True, game=True, surf=(low.name,))
    finally:
        core_plants.LeafBuf = Base
        if hi_c:
            hi_c.hide_viewport = False
    keep = []
    for o in list(coll.objects):
        n = re.sub(r'\.\d{3}$', '', o.name)      # 高模裡已有同名植物時新物件會帶 .001
        grp = None
        if n.endswith('_stem'):
            bpy.data.objects.remove(o, do_unlink=True)          # 蕨、闊葉的細莖不進遊戲模型
            continue
        if 'Fern' in n:
            grp = 'Ferns'
        elif 'Heart' in n:
            grp = 'Leaves'
        elif 'Sapling' in n and n.endswith('_Stem'):
            _flat_uv(o, 'Twig', lambda li: 0)
        elif 'Sapling' in n:
            grp = 'Sapling'
        elif 'Litter' in n:
            grp = 'Litter'
        elif 'Mush' in n:
            tint = o.data.color_attributes['Tint']
            cols = np.empty(len(o.data.vertices) * 4, np.float32)
            tint.data.foreach_get('color', cols)
            cols = cols.reshape(-1, 4)[:, :3] ** (1 / 2.2)
            pal = np.array(MUSH)
            vi = np.empty(len(o.data.loops), np.int32)
            o.data.loops.foreach_get('vertex_index', vi)
            near = np.argmin(((cols[:, None, :] - pal[None]) ** 2).sum(-1), 1)
            _flat_uv(o, 'Mush', lambda li: int(near[vi[li]]))
        else:
            bpy.data.objects.remove(o, do_unlink=True)          # 苔叢（樹皮上的苔已經烘進去）
            continue
        if grp:
            uv = o.data.uv_layers[0]
            a = np.empty(len(o.data.loops) * 2, np.float32)
            uv.data.foreach_get('uv', a)
            a = a.reshape(-1, 2)
            if grp == 'Litter':
                # 落葉：每片整片對到三條褐色裡的一條（照面的順序輪流）
                nl = len(o.data.loops)
                band = (np.arange(nl) // (4 * 24)) % 3
                x0 = np.array([LEAF[f'Litter{k}'][0] for k in range(3)])[band]
                x1 = np.array([LEAF[f'Litter{k}'][1] for k in range(3)])[band]
            else:
                x0, x1 = LEAF[grp][0], LEAF[grp][1]
            a[:, 0] = x0 + (x1 - x0) * (.03 + .94 * np.clip(a[:, 0], 0, 1))
            a[:, 1] = STRIP * (.06 + .88 * np.clip(a[:, 1], 0, 1))
            uv.data.foreach_set('uv', a.ravel())
        keep.append(o)
    # 根鬚
    for h in bpy.data.collections[_cn('HairLow')].objects:
        c = h.copy()
        c.data = h.data.copy()
        coll.objects.link(c)
        while c.data.uv_layers:
            c.data.uv_layers.remove(c.data.uv_layers[0])
        c.data.uv_layers.new(name='UVMap')
        _flat_uv(c, 'Hair', lambda li: 0)
        keep.append(c)
    for o in keep:
        o.data.uv_layers[0].name = 'UVMap'
        while len(o.data.uv_layers) > 1:
            o.data.uv_layers.remove(o.data.uv_layers[1])
        o.data.uv_layers.new(name='TileUV').data.foreach_set('uv', np.array([d.uv[:] for d in o.data.uv_layers['UVMap'].data], np.float32).ravel())
        for ca in list(o.data.color_attributes):
            o.data.color_attributes.remove(ca)
        for an in [a.name for a in o.data.attributes if a.name in ('ring',)]:
            o.data.attributes.remove(o.data.attributes[an])
        o.data.materials.clear()
        for k in ('ring_r', 'ring_s'):
            if k in o:
                del o[k]
    d = _join(keep, f'{DET}_LOD0')
    bm = bmesh.new()
    bm.from_mesh(d.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-5)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    # 整片埋在本體裡的植物面刪掉（樹幹壓在地上那段底下的落葉、伸進樹皮的蕨柄）：三個角都在本體表面內 2 cm 以上
    from mathutils.bvhtree import BVHTree
    lb = bmesh.new()
    lb.from_mesh(low.data)
    lb.transform(low.matrix_world)
    tree = BVHTree.FromBMesh(lb)
    lb.free()
    M = d.matrix_world
    inside = set()
    for v in bm.verts:
        q = M @ v.co
        loc, nr, _, _ = tree.find_nearest(q, 1.0)
        if loc is not None and (q - loc).dot(nr) < -.02:
            inside.add(v)
    dead = [f for f in bm.faces if all(v in inside for v in f.verts)]
    print('detail faces inside the body removed', len(dead), 'of', len(bm.faces))
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    bm.to_mesh(d.data)
    bm.free()
    g = _coll(_cn('Game'))
    for c in list(d.users_collection):
        c.objects.unlink(d)
    g.objects.link(d)
    bpy.data.collections.remove(coll)
    print('detail tris', sum(len(p.vertices) - 2 for p in d.data.polygons))
    return d


# ---------------------------------------------------------------- LOD、碰撞、匯出
def finish():
    b = _build()
    g = _coll(_cn('Game'))
    mat = game_material('A')
    low = bpy.data.objects[f'{ASSET}_LOD0']
    det = bpy.data.objects[f'{DET}_LOD0']
    low.data.materials.clear()
    low.data.materials.append(mat)
    low.data.polygons.foreach_set('material_index', [0] * len(low.data.polygons))
    leafm = game_material('A', f'M_{ASSET}_Leaf')
    leafm.use_backface_culling = False
    leafm['unity'] = {'shader': 'Universal Render Pipeline/Lit', 'render_face': 'Both', 'textures': f'{ASSET}_A_*'}
    det.data.materials.clear()
    det.data.materials.append(leafm)
    for nm in list(bpy.data.objects.keys()):
        if nm.startswith((ASSET, DET)) and ('_LOD1' in nm or '_LOD2' in nm or nm.endswith('_Collision') or nm == ASSET) or nm.startswith('DR06_LodTmp'):
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
    fulls = sorted(bpy.data.collections[_cn('LowFull')].objects, key=lambda o: o.name)
    ntri = lambda o: sum(len(p.vertices) - 2 for p in o.data.polygons)
    t_low, t_det = ntri(low), ntri(det)
    t0 = t_low + t_det
    # 本體和植物合計要落在 LOD0 的 50%、15%（和 DR01–04 一樣）。decimate 後再刪藏起來的面，實得比例和設定的不同：先試一次、照實得比例修正一次。
    for lv, tgt in ((1, .5), (2, .15)):
        r = tgt
        for it in range(3):
            cps, _ = _cull_hidden([decimated(src, r, f'DR06_LodTmp{lv}_{i:03d}') for i, src in enumerate(fulls)])
            body = _join(cps, f'{ASSET}_LOD{lv}') if len(cps) > 1 else cps[0]
            got = ntri(body) / t_low
            if abs(got - tgt) < .012 or it == 2:
                break
            bpy.data.objects.remove(body, do_unlink=True)
            r *= tgt / got
        body.name = body.data.name = f'{ASSET}_LOD{lv}'
        body.data.materials.clear()
        body.data.materials.append(mat)
        body.data.polygons.foreach_set('material_index', [0] * len(body.data.polygons))
        want = max(.05, (tgt * t0 - ntri(body)) / t_det)
        rd = want
        for it in range(3):
            dl = decimated(det, min(1.0, rd), f'{DET}_LOD{lv}')
            got = ntri(dl) / t_det
            if abs(got - want) < .012 or it == 2:
                break
            bpy.data.objects.remove(dl, do_unlink=True)
            rd *= want / max(got, 1e-3)
        dl.name = dl.data.name = f'{DET}_LOD{lv}'
        lods[lv] = [body, dl]
        print(f'LOD{lv} body {ntri(body)} ({ntri(body) / t_low:.3f}) detail {ntri(dl)} ({ntri(dl) / t_det:.3f}) total {(ntri(body) + ntri(dl)) / t0:.3f}')
    for lst in lods.values():
        for o in lst:
            for ca in list(o.data.color_attributes):
                o.data.color_attributes.remove(ca)
            # 面積 0 的三角形（減面後葉片上常有）Unity 匯入時會丟掉，面數就對不上 model_info：先刪
            bm = bmesh.new()
            bm.from_mesh(o.data)
            bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
            dead = [f for f in bm.faces if f.calc_area() < 1e-9]
            if dead:
                bmesh.ops.delete(bm, geom=dead, context='FACES')
            bm.to_mesh(o.data)
            bm.free()
            print('degenerate tris removed', o.name, len(dead))
    # 碰撞殼：樹幹（8 邊、每 1 m 一環，兩端封口）、粗的那根斷枝、根盤泥丘（16×10 的球）
    cobjs = b['build'](VARIANT, quick=False, low=COLRES, col=True, pre='C_')
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
    for an in [a.name for a in col.data.attributes if a.name in ('ring', 'MudMoss')]:
        col.data.attributes.remove(col.data.attributes[an])
    for k in ('ring_r', 'ring_s'):
        if k in col:
            del col[k]
    col.hide_render = True
    col.display_type = 'WIRE'
    cc = bpy.data.collections.get(_cn('Col'))
    if cc:
        bpy.data.collections.remove(cc)
    root = bpy.data.objects.new(ASSET, None)
    g.objects.link(root)
    allm = [o for lst in lods.values() for o in lst] + [col]
    for o in allm:
        o.data.name = o.name
        o.parent = root
    _load('dr_pivot.py')['to_bottom_centre'](root, low)
    return _export(lods, col, [], root)


def run_all(variant, samples=24):
    configure(variant)
    log = WORKTEX + '_run.log'
    os.makedirs(os.path.dirname(log), exist_ok=True)
    t = time.time()

    def L(m):
        open(log, 'a', encoding='utf-8').write(f'{round(time.time() - t)}s {m}\n')
        print('RUN', m)
    open(log, 'w').write('')
    try:
        for o in list(bpy.data.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        b = _build()
        hi = b['build'](variant, quick=False)
        L('high %d objects' % len(hi))
        b['dress'](b['VAR'], quick=False)
        L('high plants')
        os.makedirs(HERE6 + '/blend', exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=f'{HERE6}/blend/{ASSET}_high_{VER}.blend', copy=True)
        L('low groups %d' % len(make_low()))
        bake(samples, log=L)
        finish_textures()
        L('textures')
        join_low()
        make_detail()
        L('detail')
        L('finish ' + json.dumps(finish()))
        bpy.ops.wm.save_as_mainfile(filepath=f'{HERE6}/blend/{ASSET}_{VER}.blend', copy=True)
        L('DONE')
    except Exception:
        L('ERROR ' + traceback.format_exc())


def refinish(variant):
    """只重做 LOD、碰撞、匯出（開已存的遊戲 blend 跑）：blender -b blend/DR06_..._v001.blend --python game_dr06.py -- A refinish"""
    configure(variant)
    # 上一次 finish() 已經把 LOD0（本體、植物）平移到底部中心；先搬回建模座標，不然這次量到的平移量是 0，LOD1/2、碰撞殼（從建模座標重做）會和 LOD0 錯開
    p = Vector(bpy.context.scene.get('dr_pivot', (0.0, 0.0, 0.0)))
    for n in (f'{ASSET}_LOD0', f'{DET}_LOD0'):
        bpy.data.objects[n].data.transform(Matrix.Translation(p))
    print('RUN finish ' + json.dumps(finish()))
    bpy.ops.wm.save_mainfile()


if __name__ == '__main__' and '--' in sys.argv:
    a = sys.argv[sys.argv.index('--') + 1:]
    if 'redetail' in a:                    # 只重長植物（Detail_）＋ LOD／碰撞／匯出；先把 LOD0 搬回建模座標
        configure(a[0])
        p = Vector(bpy.context.scene.get('dr_pivot', (0.0, 0.0, 0.0)))
        bpy.data.objects[f'{ASSET}_LOD0'].data.transform(Matrix.Translation(p))
        bpy.data.objects.remove(bpy.data.objects[f'{DET}_LOD0'], do_unlink=True)
        bpy.context.scene['dr_pivot'] = [0.0, 0.0, 0.0]
        make_detail()
        refinish(a[0])
    elif 'retex' in a:                     # 只重做貼圖後處理（用 WORKTEX 裡已烘好的圖）＋ LOD／碰撞／匯出
        configure(a[0])
        finish_textures()
        refinish(a[0])
    elif 'refinish' in a:
        refinish(a[0])
    else:
        run_all(a[0] if a else 'B', int(a[1]) if len(a) > 1 else 24)
