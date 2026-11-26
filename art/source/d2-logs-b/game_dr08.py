# DR08 長滿蕈和苔的朽木（三種）的遊戲用模型：低模 → 拆 UV → 烘焙 → 植物 → LOD1／LOD2 → 碰撞 → FBX／GLB。
# 整套沿用 game_dr06.py（再往下是 D2 根與木的 game_dr02.py），和 game_dr05.py 一樣只換：
#   - 高模腳本換成 build_dr08.py，物件／集合名前綴 DR08_；
#   - 「藏起來的面」：外殼、內壁、洞口斷面彼此不算擋住（從洞口、頂上的洞看得到內壁）；
#   - 樹皮遮罩：DR08 自己那份樹皮材質（DR08_Bark）也算樹皮；
#   - 低模清掉 EndMoss（朽木靠斷口的苔，已烘進貼圖）；
#   - 方塊褐腐（高模 RotBlocks）只在高模：烘到樹幹那組低模上（法線、顏色、AO）；
#   - 白色菌絲（高模 Mycel，半透明的扇形薄片）：烘焙時不算（Cycles 烘焙不管透明，整片會烘成白的），
#     另外烘一張菌絲遮罩（薄片的 Alpha 當發光），再照遮罩把灰白疊進底色。
#   - 撕裂斷口的木刺（Splinter1）和翻卷的朽木片一樣太薄烘不準，改指到圖集最下面一條的淺灰褐木色漸層。
# 用法（背景）：blender -b --python game_dr08.py -- A 24（B、C 同）
import os, sys

_HERE8 = 'D:/yun-jing-d2-logs/art/source/d2-logs-b'
_src6 = _HERE8 + '/game_dr06.py'
UV_WEIGHT = {'Brackets': .02, 'Slab': .02, 'Cubes': .02, 'Debris': .55, 'Inner': .65, 'Soil': .70}     # UV 邊長倍數（面積是平方）
_txt6 = open(_src6, encoding='utf-8').read()
for _a, _b in (("('ring', 'Peel', 'MudMoss')", "('ring', 'Peel', 'MudMoss', 'EndMoss')"),
               ("m.name.startswith('DR06_Bark')", "m.name.startswith(('DR06_Bark', 'DR05_Bark', 'DR08_Bark'))"),
               ("'DR06_LowG", "'DR08_LowG"), ("f'DR06_LowG", "f'DR08_LowG"),
               ("o.name.startswith('DR06_LowG')", "o.name.startswith('DR08_LowG')"),
               ("uvo[sl, 0] = a0 + (a1 - a0) * (.08 + .84 * su[vi[sl]])",      # 每根木刺（低模 24 個頂點）尖端深淺不同
                "uvo[sl, 0] = a0 + (a1 - a0) * np.clip(.08 + .84 * su[vi[sl]] * (.45 + .55 * ((vi[sl] // 24 * .618034) % 1.0)), 0, .92)"),
               ("    allm = _join([_dup(o) for o in parts], 'DR06_UVPack')",       # 排 UV 前：之後會改指到色條的件（層狀菌、木條）不占空間，碎塊、內壁、土縮小，像素讓給外殼
                "    for o in parts:\n        f_ = next((v for k, v in UV_WEIGHT.items() if k in o.name), 1.0)\n        if f_ != 1.0:\n            d_ = o.data.uv_layers['UVMap'].data\n            u_ = np.empty(len(d_) * 2, np.float32)\n            d_.foreach_get('uv', u_)\n            u_ = u_.reshape(-1, 2)\n            c_ = u_.mean(0)\n            d_.foreach_set('uv', ((u_ - c_) * f_ + c_).ravel())\n            print('uv weight', o.name, f_)\n    allm = _join([_dup(o) for o in parts], 'DR06_UVPack')"),
               ("        elif 'Litter' in n:\n            grp = 'Litter'",                  # 毛苔叢指到苔色葉片格
                "        elif 'MossClump' in n:\n            grp = 'Moss'\n        elif 'Litter' in n:\n            grp = 'Litter'"),
               ("        o.data.uv_layers['UVMap'].data.foreach_set('uv', uvo.ravel())\n        for an in ('Shard', 'ShardU'):",
                "        uvo = _cube_uv(o, _brk_uv(o, uvo, n), n)\n        o.data.uv_layers['UVMap'].data.foreach_set('uv', uvo.ravel())\n        for an in ('Shard', 'ShardU', 'BrkU', 'BrkV', 'CubeU', 'CubeV', 'CubeT'):")):
    assert _a in _txt6 or _b in _txt6, _a
    _txt6 = _txt6.replace(_a, _b)
_nm = globals().get('__name__')
globals()['__name__'] = 'game_dr06_lib'             # 不要跑 DR06 的主程式
exec(compile(_txt6, _src6, 'exec'), globals())
globals()['__name__'] = _nm

NAMES = {'A': 'DR08_RottenLog_A', 'B': 'DR08_RottenLog_B', 'C': 'DR08_RottenLog_C'}
LEAF['Leaves'] = (.18, .26) + tuple(LEAF['Leaves'][2:])         # 闊葉那格讓一半給毛苔叢
LEAF['Sapling'] = LEAF['Sapling'][:2] + ((.16, .24, .08), (.36, .46, .20))   # 小苗：引擎裡 .60 的黃綠像螢光
LEAF['Moss'] = (.26, .32, (.11, .14, .035), (.29, .33, .09))   # 苔：深橄欖 → 橄欖綠（sRGB；第一版 .42 的黃綠在 Unity 裡太亮）
MUSH.extend([(.73, .90, .81), (.57, .67, .60)])                 # 發光小蕈：傘、傘頂（比對高模頂點色，sRGB）
MUSH_PAINT.extend([(.72, .95, .80), (.52, .74, .62)])           # 引擎裡沒有發光貼圖：畫成淡青綠
FLAT['Brk'] = (.88, .95)                            # 層狀菌的環帶色條（DR08 沒有小苗細枝、根鬚，借用那兩塊）
BRK_PAL = ((.028, .012, .005), (.10, .036, .011), (.19, .10, .040), (.050, .021, .007), (.15, .072, .022))   # 線性，同 build_dr08 的層狀菌
BRK_CREAM, BRK_UNDER = (.22, .16, .088), (.18, .13, .072)


def _brk_uv(o, uvo, n):
    """層狀菌：烘焙時相鄰菌蓋互相擋、低模只有 4 圈，烘出來是一團灰褐。改指到圖集最下面一條的環帶色條：
    U 照頂點的 BrkU（上面根→邊、圓唇、下面），V 每片菌各取一列（每列環帶相位不同）。"""
    bk = o.data.attributes.get('BrkU')
    if bk is None:
        return uvo
    bu = np.empty(len(o.data.vertices), np.float32)
    bk.data.foreach_get('value', bu)
    bv = np.empty(len(o.data.vertices), np.float32)
    o.data.attributes['BrkV'].data.foreach_get('value', bv)
    vi = np.empty(n, np.int32)
    o.data.loops.foreach_get('vertex_index', vi)
    a0, a1 = FLAT['Brk']
    uvo[:, 0] = a0 + (a1 - a0) * (.02 + .96 * bu[vi])
    uvo[:, 1] = STRIP * (.06 + .88 * bv[vi])
    print('brackets -> band strip', o.name, n, 'loops')
    return uvo
def _cube_uv(o, uvo, n):
    """方塊褐腐：每個面指到圖集右邊那欄（x 1−STRIP..1、STRIP 以上）的一格磚格（CubeT 第幾格、CubeU／CubeV 面上的位置）。"""
    ct_a = o.data.attributes.get('CubeT')
    if ct_a is None:
        return uvo
    ct = np.empty(len(o.data.polygons), np.int32)
    ct_a.data.foreach_get('value', ct)
    cu = np.empty(n, np.float32)
    o.data.attributes['CubeU'].data.foreach_get('value', cu)
    cv = np.empty(n, np.float32)
    o.data.attributes['CubeV'].data.foreach_get('value', cv)
    ls = np.empty(len(o.data.polygons), np.int32)
    o.data.polygons.foreach_get('loop_start', ls)
    lt = np.empty(len(o.data.polygons), np.int32)
    o.data.polygons.foreach_get('loop_total', lt)
    tl = np.repeat(ct, lt)
    T = CUBE_T / SIZE
    m_ = 1.5 / SIZE
    uvo[:, 0] = (1 - STRIP) + m_ + cu * (T - 2 * m_)
    uvo[:, 1] = STRIP + tl * T + m_ + cv * (T - 2 * m_)
    print('cubes -> tile column', o.name, n, 'loops')
    return uvo


CUBE_T, CUBE_N = 128, 8
DET = 'Detail_DR08_Plants'
SHELL = ('Trunk', 'Inner', 'Rim0', 'Rim1', 'Lip0', 'Lip1')
LOWRES = (.10, 12, 36, 1.2)                     # 低模：每 0.10 m 一環、最多 36 邊（0.6–0.8 m 粗、扁的斷面，太少邊兩側變成平板）
COLRES = (.5, 8, 10, 1.0)
SHARD_C = ((.16, .11, .075), (.40, .32, .23))      # 撕裂端木條：根部暗褐 → 尖端暖灰褐（.50 在 Unity 太陽下是米色、像紙）
MUSH_PAINT[1:5] = [(.58, .50, .40), (.54, .45, .35), (.48, .36, .25), (.33, .24, .16)]   # 小蕈：柄、褶、傘壓暗（引擎裡 .72 的柄像白塑膠圖釘）
MYCEL_C = np.array((.80, .79, .74))                 # 菌絲疊進底色的灰白（sRGB）


def configure(v):
    global VARIANT, ASSET, EXP, TEX, WORKTEX
    VARIANT = v
    ASSET = NAMES[v]
    EXP = f'{ROOT}/art/exports/d2-logs-b/{ASSET}'
    TEX = EXP + '/Textures'
    WORKTEX = os.environ.get('DR_WORK8', 'D:/yun-jing-cache/dr08-work/') + f'bake_{v}'


def _build():
    global B
    if B is None:
        p = HERE6 + '/build_dr08.py'
        B = {'__file__': p, '__name__': 'build_dr08'}
        exec(compile(open(p, encoding='utf-8').read(), p, 'exec'), B)
    B['set_variant'](VARIANT)
    return B


def _cn(kind):
    return f"DR08_{_build()['VAR']['name']}_{kind}"


_finish8 = finish_textures


def finish_textures():
    """DR06 的收尾（葉、蕈、木刺色條）之後，在 Brk 那塊畫層狀菌的環帶：
    x 0–.78 上面（根部暗、深褐／鏽褐／黃褐環帶，每列相位不同），.78–.88 奶油色圓唇，.88–1 下面淺黃褐（細孔雜點）。"""
    _finish8()
    h0 = int(STRIP * SIZE)
    p = f'{TEX}/{ASSET}_A_Albedo.png'
    im, base = _px(p)
    bpy.data.images.remove(im)
    a, b = int(FLAT['Brk'][0] * SIZE), int(FLAT['Brk'][1] * SIZE)
    W = b - a
    u = (np.arange(W) + .5) / W
    u = (u - .02) / .96
    y = (np.arange(h0) + .5) / h0
    v = np.clip((y - .06) / .88, 0, 1)
    rs = np.random.RandomState(8)
    pal = np.array(BRK_PAL) ** (1 / 2.2)
    cream = np.array(BRK_CREAM) ** (1 / 2.2)
    under = np.array(BRK_UNDER) ** (1 / 2.2)
    out = np.zeros((h0, W, 3))
    for j in range(h0):
        nb = 10.0 + 3.0 * ((v[j] * 7.31) % 1.0)
        ph = v[j] * 17.0
        rho = np.clip(u / .78, 0, 1)
        bi = rho * nb + ph + .15 * np.sin(np.arange(W) * .9 + j)
        k0 = np.floor(bi).astype(int) % len(pal)
        fr = bi - np.floor(bi)
        c0, c1 = pal[k0], pal[(k0 + 1) % len(pal)]
        m = np.clip((fr - .80) / .20, 0, 1)[:, None]
        col = c0 + (c1 - c0) * m
        col *= (.65 + .35 * np.clip(rho / .35, 0, 1))[:, None]
        top = u < .76
        rim = (u >= .76) & (u < .88)
        bot = u >= .88
        out[j, top] = col[top]
        out[j, rim] = cream
        out[j, bot] = under * (.8 + .2 * rs.rand(bot.sum(), 1))
    base[:h0, a:b, :3] = out
    # 細節遮罩：腐木、土（褐色、不是樹皮的地方）也疊半強度的共用木紋細節（匯入 1024 後每公尺只剩 60–110 像素，沒細節近看是一片糊的）
    body = base[h0:]
    rgb = body[..., :3]
    brown = (rgb[..., 0] > rgb[..., 1] * 1.12) & (rgb[..., 1] >= rgb[..., 2] * .9) & (body[..., 3] < .5)
    body[..., 3] = np.where(brown, .55, body[..., 3])
    print('detail mask on rot/soil: %.1f%% of body' % (100 * float(brown.mean())))
    # 方塊磚格貼到右邊那欄（底色、法線、AO→ORM／MaskURP）
    cdir = _build()['CUBE_DIR']
    if not os.path.exists(f'{cdir}/cube_albedo.png'):
        _build()['cube_tiles']()
    x0 = SIZE - h0
    hh = CUBE_T * CUBE_N
    im, ca = _px(f'{cdir}/cube_albedo.png')
    bpy.data.images.remove(im)
    base[h0:h0 + hh, x0:, :3] = ca[..., :3]
    base[h0:h0 + hh, x0:, 3] = 0
    _save(base, p, True)
    pn = f'{TEX}/{ASSET}_A_Normal.png'
    im, nr = _px(pn)
    bpy.data.images.remove(im)
    im, cn = _px(f'{cdir}/cube_normal.png')
    bpy.data.images.remove(im)
    nr[h0:h0 + hh, x0:, :3] = cn[..., :3]
    _save(nr, pn, False)
    im, cao = _px(f'{cdir}/cube_ao.png')
    bpy.data.images.remove(im)
    for k_, ch in (('ORM', 0), ('MaskURP', 1)):
        pk = f'{TEX}/{ASSET}_A_{k_}.png'
        im, ar = _px(pk)
        bpy.data.images.remove(im)
        ar[h0:h0 + hh, x0:, ch] = cao[..., 0]
        if k_ == 'ORM':
            ar[h0:h0 + hh, x0:, 1] = .92
        else:
            ar[h0:h0 + hh, x0:, 3] = .08
        _save(ar, pk, False)
    print('cube tiles pasted', x0, h0, hh)
    print('brk strip painted', a, b, h0)
    # 木條的法線：色條那塊原本是平的（引擎裡一片片光滑的板子）：沿長的纖維溝，V（木條寬度方向）上起伏
    p = f'{TEX}/{ASSET}_A_Normal.png'
    im, nrm = _px(p)
    bpy.data.images.remove(im)
    a, b = int(FLAT['Shard'][0] * SIZE), int(FLAT['Shard'][1] * SIZE)
    rs = np.random.RandomState(9)
    yy = np.arange(h0)[:, None] / h0
    xx = np.linspace(0, 1, b - a)[None, :]
    g = np.zeros((h0, b - a))
    for k in range(8):
        fq, ph = rs.uniform(10, 45), rs.uniform(0, 6.3)
        g += np.cos(yy * fq * 2 * np.pi + ph + xx * rs.uniform(-1.5, 1.5)) * fq / 45.0 / 8
    ny = np.clip(g * 2.2, -.55, .55)
    v = np.stack([np.zeros_like(ny), ny, np.sqrt(1 - ny * ny)], -1)
    nrm[:h0, a:b, :3] = v * .5 + .5
    _save(nrm, p, False)
    print('shard strip normal grooves', a, b)


_make_low6 = make_low


def make_low():
    outs = _make_low6()
    for go in outs:
        s = list(go['srcs'])
        if 'Trunk' in s and 'RotBlocks' not in s:
            go['srcs'] = s + ['RotBlocks']           # 方塊褐腐只在高模：烘到樹幹那組
            print('bake group', go.name, 'srcs', go['srcs'])
    return outs


_bake6 = bake


def bake(samples=24, log=None, kinds=None):
    out = _bake6(samples, log, kinds)
    if not kinds or 'BaseColor' in kinds:
        mycel_into_basecolor(log)
    return out


def mycel_into_basecolor(log=None):
    """菌絲薄片另外烘一張遮罩（Alpha 當發光，其他高模都不算），照遮罩把灰白疊進烘好的底色。"""
    sc = bpy.context.scene
    hi_c, lo_c = bpy.data.collections[_cn('High')], bpy.data.collections[_cn('Low')]
    my = next((o for o in hi_c.objects if o.name.startswith('Mycel')), None)
    if my is None:
        print('no Mycel')
        return
    lows = sorted([o for o in lo_c.objects if o.name.startswith('DR08_LowG')], key=lambda o: o.name)
    src_m = my.data.materials[0]
    mm = src_m.copy()
    mm.name = 'DR08_MycelMask'
    N, Lk = mm.node_tree.nodes, mm.node_tree.links
    b = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    a_src = b.inputs['Alpha'].links[0].from_socket
    for l in list(b.inputs['Alpha'].links):
        Lk.remove(l)
    b.inputs['Alpha'].default_value = 1.0
    Lk.new(a_src, b.inputs['Emission Color'])
    b.inputs['Emission Strength'].default_value = 1.0
    b.inputs['Base Color'].default_value = (0, 0, 0, 1)
    my.data.materials[0] = mm
    bm_ = _bake_mats()
    m, tn = bm_[0]
    tn.image = _image(f'{ASSET}_A_MycelMask', False)
    sc.cycles.samples = 4
    for o in bpy.context.view_layer.objects:
        o.hide_render = True
    my.hide_render = False
    my.hide_viewport = False
    my.hide_set(False)
    for low in lows:
        low.hide_render = False
        low.hide_viewport = False
        low.hide_set(False)
        _select([my, low], low)
        bpy.ops.object.bake(type='EMIT', use_selected_to_active=True, cage_extrusion=.30, max_ray_distance=.75, margin=1,
                            margin_type='EXTEND', use_clear=False)
        low.hide_render = True
    im = tn.image
    im.filepath_raw = f'{WORKTEX}/{ASSET}_A_MycelMask.png'
    im.file_format = 'PNG'
    im.save()
    my.data.materials[0] = src_m
    bpy.data.materials.remove(mm)
    for o in bpy.context.view_layer.objects:
        o.hide_render = False
    gr = bpy.data.objects.get('DR06_BakeGround')
    if gr:
        gr.hide_render = True
    p = f'{WORKTEX}/{ASSET}_A_BaseColor.png'
    im1, base = _px(p)
    bpy.data.images.remove(im1)
    im2, mk = _px(im.filepath_raw)
    bpy.data.images.remove(im2)
    k = np.clip(mk[..., 0] * mk[..., 3], 0, 1)[..., None] * .92
    base[..., :3] = base[..., :3] * (1 - k) + MYCEL_C * k
    _save(base, p, True)
    msg = 'mycel mask: %.2f%% of the atlas' % (100 * float((k[..., 0] > .1).mean()))
    print(msg)
    if log:
        log(msg)


def _hidden_verts(objs, margin=.03, zcut=-.5):
    """外殼、內壁、洞口斷面兩兩之間不互相判斷（從洞口、頂上的洞看得到內壁）；其他件照 DR06。"""
    from mathutils.bvhtree import BVHTree
    from mathutils import Vector
    import numpy as np
    base = lambda o: o.name.split('_', 1)[1] if o.name.startswith(('L_', 'C_', 'F_')) else o.name
    shell = [base(o) in SHELL for o in objs]
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
            if j == i or (shell[i] and shell[j]) or (lo_i > hi).any() or (hi_i < lo).any():
                continue
            for vi in np.nonzero(~hide & (co >= lo).all(1) & (co <= hi).all(1))[0]:
                q = Vector(co[vi])
                loc, nrm, idx, dist = tj.find_nearest(q)
                if loc is not None and dist > margin and (q - loc).dot(nrm) < 0 and all(tj.ray_cast(q, d, 50)[0] is not None for d in dirs):
                    hide[vi] = True
        out.append(hide)
    return out


if __name__ == '__main__' and '--' in sys.argv:
    a = sys.argv[sys.argv.index('--') + 1:]
    if 'redetail' in a:
        configure(a[0])
        p = Vector(bpy.context.scene.get('dr_pivot', (0.0, 0.0, 0.0)))
        bpy.data.objects[f'{ASSET}_LOD0'].data.transform(Matrix.Translation(p))
        bpy.data.objects.remove(bpy.data.objects[f'{DET}_LOD0'], do_unlink=True)
        bpy.context.scene['dr_pivot'] = [0.0, 0.0, 0.0]
        make_detail()
        refinish(a[0])
    elif 'retex' in a:
        configure(a[0])
        finish_textures()
        refinish(a[0])
    elif 'refinish' in a:
        refinish(a[0])
    else:
        run_all(a[0] if a else 'A', int(a[1]) if len(a) > 1 else 24)
