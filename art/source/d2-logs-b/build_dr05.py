# DR05 空心倒木（高模）：一截老樹幹（長 8 m、外徑 2 m）躺在地上、稍微陷進土裡，心材整條朽空，像一條隧道，人可以彎腰鑽過去。
#   殼：外面一半樹皮剝落（露出灰褐風化木、長裂縫），另一半是深灰褐長稜老樹皮；幾片大樹皮翹起來、一片掉在地上。
#   裡面：朽爛的淺橘褐木頭，沿長度一絲一絲的纖維；地上有朽木碎塊、落葉；靠洞口長一點苔；幾塊白色菌絲。
#   兩頭：斷折、朽爛的參差洞口（不是鋸的），+X 那頭上半邊塌掉一大塊。
#   頂上：苔、地衣、蕨、蕈；兩側層狀菌。
# 樹幹沿 +X：x = 0 到 L；正面 -Y；z = 0 是地面。原點之後由 dr_pivot.py 移到底部中心。
# 沿用 DR06 的樹皮、剝皮、層狀菌、植物（exec build_dr06.py），只換掉樹幹形狀、根盤、斷口這些 DR06 自己的件。
# 用法（背景，不要加 --factory-startup）：
#   blender -b --python build_dr05.py -- A quick <輸出資料夾> [鏡位,鏡位] [存檔.blend]
import bpy, bmesh, math, random, sys, os
import numpy as np
from mathutils import Vector

_HERE5 = os.path.dirname(os.path.abspath(globals().get('__file__', 'D:/yun-jing-d2-logs/art/source/d2-logs-b/build_dr05.py')))
_p6 = os.path.join(_HERE5, 'build_dr06.py')
_nm = globals().get('__name__')
globals()['__name__'] = 'build_dr06_lib'            # 不要跑 DR06 的主程式
exec(compile(open(_p6, encoding='utf-8').read(), _p6, 'exec'), globals())
globals()['__name__'] = _nm
__file__ = os.path.join(_HERE5, 'build_dr05.py')

# L 長、R 外半徑、W 殼厚、sink 陷進土裡、bend 左右彎
# fungi：(沿長比例, 繞軸角（0 正上，正值往 -Y）, 片數)
VARIANTS = {
    'A': dict(name='Hollow', L=8.0, R=1.06, W=.27, sink=.17, seed=53, bend=.10,
              fungi=((.30, -1.50, 4), (.58, 1.50, 5), (.80, -1.35, 3))),
}
VAR = VARIANTS['A']
PRE = 'DR05'
from dr_core import TILE
DELTA = 1.6                       # 兩頭參差的洞口：最後 1.6 m 內照角度壓縮


def set_variant(v):
    global VAR
    VAR = VARIANTS[v]
    VAR['id'] = v
    return VAR


# ---------------- 材質 ----------------
def bark5_material():
    """DR06 樹皮的副本：剝皮處的裂縫拉得更長（DR05 剝掉一半，DR06 那種短的裂縫大片看起來像石板路）。"""
    m = bpy.data.materials.get('DR05_Bark')
    if m:
        return m
    m = bark_material().copy()
    m.name = 'DR05_Bark'
    N, Lk = m.node_tree.nodes, m.node_tree.links
    for n in list(N):
        if n.type == 'MAPPING' and abs(n.inputs['Scale'].default_value[0] - .7) < 1e-3 and abs(n.inputs['Scale'].default_value[1] - 9.0) < 1e-3:
            n.inputs['Scale'].default_value = (.05, 13.0, 13.0)
    # 剝皮露木的裂縫：Voronoi 的邊換成拉長雜訊的等高線（|雜訊 − .5|）。Voronoi 的細長格子被洞口喇叭那段斜面斜切，會切成一格一格的石板
    for vo in [n for n in N if n.type == 'TEX_VORONOI' and n.feature == 'DISTANCE_TO_EDGE']:
        src = vo.inputs['Vector'].links[0].from_socket if vo.inputs['Vector'].links else None
        gn = N.new('ShaderNodeTexNoise')
        gn.inputs['Scale'].default_value = 1.0
        gn.inputs['Detail'].default_value = 3
        gn.inputs['Roughness'].default_value = .5
        if src:
            Lk.new(src, gn.inputs['Vector'])
        g1 = N.new('ShaderNodeMath')
        g1.operation = 'SUBTRACT'
        g1.inputs[1].default_value = .5
        Lk.new(gn.outputs['Fac'], g1.inputs[0])
        ab = N.new('ShaderNodeMath')
        ab.operation = 'ABSOLUTE'
        Lk.new(g1.outputs[0], ab.inputs[0])
        sc = N.new('ShaderNodeMath')
        sc.operation = 'MULTIPLY'
        sc.inputs[1].default_value = 2.2                   # 溝寬照原本 Voronoi 邊的門檻
        Lk.new(ab.outputs[0], sc.inputs[0])
        for l in list(vo.outputs['Distance'].links):
            Lk.new(sc.outputs[0], l.to_socket)
        N.remove(vo)
    lichen_rosettes(N, Lk, next(n for n in N if n.type == 'BSDF_PRINCIPLED'))
    return m


def lichen_rosettes(N, Lk, b):
    """一朵朵 8–18 cm 的葉狀地衣（參考圖頂上苔間、樹皮上淺灰藍綠的花形斑）：
    Voronoi 每格中心一朵，邊緣加高頻雜訊成一瓣瓣；只挑兩成的格子、成群出現、朝上的面才有；中心暗、外圈淺。"""
    tc = N.new('ShaderNodeTexCoord')
    vo = N.new('ShaderNodeTexVoronoi')
    vo.inputs['Scale'].default_value = 4.5
    vo.inputs['Randomness'].default_value = .9
    Lk.new(tc.outputs['Object'], vo.inputs['Vector'])
    lob = N.new('ShaderNodeTexNoise')
    lob.inputs['Scale'].default_value = 48.0
    lob.inputs['Detail'].default_value = 2
    Lk.new(tc.outputs['Object'], lob.inputs['Vector'])
    lm = N.new('ShaderNodeMath')
    lm.operation = 'MULTIPLY_ADD'
    lm.inputs[1].default_value = .16
    Lk.new(lob.outputs['Fac'], lm.inputs[0])
    Lk.new(vo.outputs['Distance'], lm.inputs[2])
    # 每格大小不同：格子亂數 G 放大半徑
    sp = N.new('ShaderNodeSeparateColor')
    Lk.new(vo.outputs['Color'], sp.inputs[0])
    rad = N.new('ShaderNodeMath')
    rad.operation = 'MULTIPLY_ADD'
    rad.inputs[1].default_value = .14
    rad.inputs[2].default_value = .30          # 加回瓣緣雜訊的平均 .08
    Lk.new(sp.outputs[1], rad.inputs[0])
    dd = N.new('ShaderNodeMath')
    dd.operation = 'SUBTRACT'
    Lk.new(lm.outputs[0], dd.inputs[0])
    Lk.new(rad.outputs[0], dd.inputs[1])
    inside = _ramp(N, -.03, .0, (.85, .85, .85, 1), (0, 0, 0, 1))      # 邊緣軟、半透（太實像噴漆）
    Lk.new(dd.outputs[0], inside.inputs[0])
    pick = _ramp(N, .30, .315, (1, 1, 1, 1), (0, 0, 0, 1))          # 只挑三成的格子
    Lk.new(sp.outputs[0], pick.inputs[0])
    grp = N.new('ShaderNodeTexNoise')                               # 成群：大尺度雜訊高的地方
    grp.inputs['Scale'].default_value = .9
    grp.inputs['Detail'].default_value = 2
    Lk.new(tc.outputs['Object'], grp.inputs['Vector'])
    gr = _ramp(N, .40, .50, (0, 0, 0, 1), (1, 1, 1, 1))
    Lk.new(grp.outputs['Fac'], gr.inputs[0])
    geo = N.new('ShaderNodeNewGeometry')
    sz = N.new('ShaderNodeSeparateXYZ')
    Lk.new(geo.outputs['Normal'], sz.inputs[0])
    up = _ramp(N, .35, .65, (0, 0, 0, 1), (1, 1, 1, 1))              # 只長在朝上的面
    Lk.new(sz.outputs['Z'], up.inputs[0])
    pa = N.new('ShaderNodeAttribute')                               # 剝皮露木上不長（長在樹皮和苔上）
    pa.attribute_name = 'Peel'
    np_ = _ramp(N, .25, .55, (1, 1, 1, 1), (0, 0, 0, 1))
    Lk.new(pa.outputs['Fac'], np_.inputs[0])
    msk = None
    for r_ in (inside, pick, gr, up, np_):
        if msk is None:
            msk = r_.outputs[0]
            continue
        mm = N.new('ShaderNodeMath')
        mm.operation = 'MULTIPLY'
        Lk.new(msk, mm.inputs[0])
        Lk.new(r_.outputs[0], mm.inputs[1])
        msk = mm.outputs[0]
    col = _ramp(N, .0, .9, (.36, .41, .38, 1), (.56, .61, .58, 1))       # 中心暗、外圈淺的灰藍綠（DR06 教訓：太亮像點上去的白點）
    rr = N.new('ShaderNodeMath')
    rr.operation = 'DIVIDE'
    Lk.new(lm.outputs[0], rr.inputs[0])
    Lk.new(rad.outputs[0], rr.inputs[1])
    Lk.new(rr.outputs[0], col.inputs[0])
    lk = next(l for l in b.inputs['Base Color'].links)
    src = lk.from_socket
    Lk.remove(lk)
    mx = N.new('ShaderNodeMixRGB')
    Lk.new(msk, mx.inputs[0])
    Lk.new(src, mx.inputs[1])
    Lk.new(col.outputs[0], mx.inputs[2])
    Lk.new(mx.outputs[0], b.inputs['Base Color'])


def rot_material():
    """朽木（內壁、洞口）：淺橘褐、沿長度一絲一絲的纖維、纖維間暗縫；點屬性 EndMoss 是靠洞口的苔；幾塊白色菌絲。"""
    m = bpy.data.materials.get('DR05_Rot')
    if m:
        return m
    m = bpy.data.materials.new('DR05_Rot')
    m.use_nodes = True
    N, Lk = m.node_tree.nodes, m.node_tree.links
    b = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    fib = _streak(N, Lk, (.9, 30.0, 30.0), 8)               # 細纖維
    c0 = _ramp(N, .28, .74, (.15, .072, .028, 1), (.52, .31, .14, 1))
    Lk.new(fib.outputs['Fac'], c0.inputs[0])
    tc = N.new('ShaderNodeTexCoord')
    mp = N.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (.05, 14.0, 14.0)          # 纖維束之間的溝：拉得很長的雜訊的等高線，一條條不橫斷（Voronoi 的邊在隧道裡斜看像石板）
    Lk.new(tc.outputs['Object'], mp.inputs['Vector'])
    gn = N.new('ShaderNodeTexNoise')
    gn.inputs['Scale'].default_value = 1.0
    gn.inputs['Detail'].default_value = 3
    gn.inputs['Roughness'].default_value = .5
    Lk.new(mp.outputs[0], gn.inputs['Vector'])
    g1 = N.new('ShaderNodeMath')
    g1.operation = 'SUBTRACT'
    g1.inputs[1].default_value = .5
    Lk.new(gn.outputs['Fac'], g1.inputs[0])
    vo = N.new('ShaderNodeMath')
    vo.operation = 'ABSOLUTE'
    Lk.new(g1.outputs[0], vo.inputs[0])
    gap = _ramp(N, .0, .05, (.66, .60, .54, 1), (1, 1, 1, 1))      # 第四輪：溝淡一點、寬一點（黑細線像等高線圖）
    Lk.new(vo.outputs[0], gap.inputs[0])
    geo = N.new('ShaderNodeNewGeometry')                    # 洞口斷面（法線沿 X）看到的是纖維的橫切：溝淡掉，不要一條條蟲紋
    sx = N.new('ShaderNodeSeparateXYZ')
    Lk.new(geo.outputs['Normal'], sx.inputs[0])
    ax_ = N.new('ShaderNodeMath')
    ax_.operation = 'ABSOLUTE'
    Lk.new(sx.outputs['X'], ax_.inputs[0])
    pw = N.new('ShaderNodeMath')                            # 斜面（洞口喇叭、斷面）稍微朝軸向就淡掉：|n.x|^0.35
    pw.operation = 'POWER'
    pw.inputs[1].default_value = .35
    Lk.new(ax_.outputs[0], pw.inputs[0])
    gk = N.new('ShaderNodeMixRGB')
    Lk.new(pw.outputs[0], gk.inputs[0])
    Lk.new(gap.outputs[0], gk.inputs[1])
    gk.inputs[2].default_value = (.88, .84, .80, 1)
    gap = gk
    big = _streak(N, Lk, (.3, 2.2, 2.2), 4)                 # 大片受潮深淺
    bl = _ramp(N, .35, .72, (.55, .52, .50, 1), (1.05, 1.0, .95, 1))
    Lk.new(big.outputs['Fac'], bl.inputs[0])
    m1 = N.new('ShaderNodeMixRGB')
    m1.blend_type = 'MULTIPLY'
    m1.inputs[0].default_value = 1.0
    Lk.new(c0.outputs[0], m1.inputs[1])
    Lk.new(gap.outputs[0], m1.inputs[2])
    m2 = N.new('ShaderNodeMixRGB')
    m2.blend_type = 'MULTIPLY'
    m2.inputs[0].default_value = 1.0
    Lk.new(m1.outputs[0], m2.inputs[1])
    Lk.new(bl.outputs[0], m2.inputs[2])
    # 白色菌絲：一片片低頻雜訊的高點
    my = N.new('ShaderNodeTexNoise')
    my.inputs['Scale'].default_value = 1.7
    my.inputs['Detail'].default_value = 6
    my.inputs['Roughness'].default_value = .62
    Lk.new(tc.outputs['Object'], my.inputs['Vector'])
    myr = _ramp(N, .66, .72, (0, 0, 0, 1), (1, 1, 1, 1))
    Lk.new(my.outputs['Fac'], myr.inputs[0])
    myc = N.new('ShaderNodeMixRGB')
    myc.inputs[2].default_value = (.62, .60, .55, 1)
    Lk.new(myr.outputs[0], myc.inputs[0])
    Lk.new(m2.outputs[0], myc.inputs[1])
    # 靠洞口的苔
    at = N.new('ShaderNodeAttribute')
    at.attribute_name = 'EndMoss'
    nm = N.new('ShaderNodeTexNoise')
    nm.inputs['Scale'].default_value = 6
    nm.inputs['Detail'].default_value = 6
    Lk.new(tc.outputs['Object'], nm.inputs['Vector'])
    ad = N.new('ShaderNodeMath')
    ad.operation = 'ADD'
    Lk.new(at.outputs['Fac'], ad.inputs[0])
    Lk.new(nm.outputs['Fac'], ad.inputs[1])
    mr = _ramp(N, .95, 1.15, (0, 0, 0, 1), (1, 1, 1, 1))
    Lk.new(ad.outputs[0], mr.inputs[0])
    mc = _ramp(N, .30, .75, *MOSS_C)
    Lk.new(nm.outputs['Fac'], mc.inputs[0])
    mx = N.new('ShaderNodeMixRGB')
    Lk.new(mr.outputs[0], mx.inputs[0])
    Lk.new(myc.outputs[0], mx.inputs[1])
    Lk.new(mc.outputs[0], mx.inputs[2])
    Lk.new(mx.outputs[0], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = .90
    hg = N.new('ShaderNodeMath')
    hg.operation = 'ADD'
    Lk.new(fib.outputs['Fac'], hg.inputs[0])
    vh = N.new('ShaderNodeMapRange')
    vh.inputs['From Max'].default_value = .05
    vh.inputs['To Min'].default_value = -.45           # 第四輪：溝寬一點、淺一點（細黑線像等高線圖）
    vh.inputs['To Max'].default_value = 0.0
    Lk.new(vo.outputs[0], vh.inputs['Value'])
    Lk.new(vh.outputs[0], hg.inputs[1])
    bp = N.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = .9
    bp.inputs['Distance'].default_value = .02
    Lk.new(hg.outputs[0], bp.inputs['Height'])
    Lk.new(bp.outputs[0], b.inputs['Normal'])
    return m


# ---------------- 形狀 ----------------
def axis_y(V, x):
    t = max(0.0, min(1.0, x / V['L']))
    return V['bend'] * V['R'] * math.sin(t * 2.4 + V['seed'] * .37) * t


def out_r(V, x):
    t = max(0.0, min(1.0, x / V['L']))
    return V['R'] * (1.04 - .10 * t + .03 * math.sin(t * 7.0 + 1.3))


def axis_z(V, x):
    return out_r(V, x) * .96 - V['sink']


def in_r(V, x):
    """朽空的內徑：殼厚 W 上下起伏（朽得不平均）。"""
    t = max(0.0, min(1.0, x / V['L']))
    return out_r(V, x) - V['W'] * (1 + .14 * math.sin(t * 9.0 + 2.0) + .08 * math.sin(t * 23.0))      # 起伏收小：隧道最窄處也要能彎腰鑽過（內高 > 1.1 m）


def flare(V, x, k):
    """洞口像喇叭往外張（參考圖兩頭的口比樹幹粗、殼一層層往外翻）：離端點 1.1 m 內半徑放大到 1 + k。"""
    d = min(x, V['L'] - x)
    return 1 + k * _sm(1 - d / 1.3) ** 1.3


def shell_pts(V, inner=False):
    pts = []
    for x in np.linspace(0.0, V['L'], 21):
        x = float(x)
        if inner:
            pts.append((x, axis_y(V, x) + .03, axis_z(V, x) + .05, in_r(V, x) * flare(V, x, .34), .97))      # 內孔稍微偏上（下面朽得少、積了碎屑）
        else:
            pts.append((x, axis_y(V, x), axis_z(V, x), out_r(V, x) * flare(V, x, .24), .96))
    return pts


def end_cut(V, th, end, inner=False):
    """洞口在角度 th（0＝側面 +side，π/2＝正上方）往內縮多少公尺。end 0：x = 0 那頭；1：x = L 那頭（上半邊塌掉一大塊）。"""
    s = V['seed'] + 11 * end
    c = .10 + .22 * abs(fb((math.cos(th) * 1.6, math.sin(th) * 1.6, s), 1.0, 3)) + .03 * fb((math.cos(th) * 4, math.sin(th) * 4, s + 3), 1.0, 2)
    if end == 1:
        d = (th - math.pi * .58 + math.pi) % (2 * math.pi) - math.pi
        c += 1.15 * _sm(1 - abs(d) / 1.05) * (1 + .25 * fb((th * 3, s, 0), 1.0, 2))    # 上半邊塌掉
    else:
        d = (th - math.pi * .30 + math.pi) % (2 * math.pi) - math.pi
        c += .35 * _sm(1 - abs(d) / .55)                # 一個大缺口
    if inner:
        c += .06 + .16 * abs(fb((math.cos(th) * 2.3, math.sin(th) * 2.3, s + 7), 1.0, 2))       # 朽爛的心材凹進去一點
    return max(0.0, min(DELTA - .15, c))


def ragged_ends(V, ob, pts, inner=False):
    """兩頭最後 DELTA 公尺照角度壓縮，洞口變成參差的斷口。管子的頂點是一環一環照順序排的。"""
    rings, nu, co = ring_info(ob, pts)
    tot = rings[-1][3]
    ss = np.array([q[3] for q in rings])
    tans = []
    for k in range(len(rings)):
        a = rings[min(k + 1, len(rings) - 1)][0] - rings[max(k - 1, 0)][0]
        tans.append(np.array(a.normalized()))
    cut = [[end_cut(V, 2 * math.pi * i / nu, e, inner) for i in range(nu)] for e in (0, 1)]
    for k, s in enumerate(ss):
        for i in range(nu):
            j = k * nu + i
            if s > tot - DELTA:
                c = cut[1][i]
                s0 = tot - DELTA
                ds = (s0 + (s - s0) * (DELTA - c) / DELTA) - s
                co[j] += tans[k] * ds
            if s < DELTA:
                c = cut[0][i]
                ds = (DELTA - (DELTA - s) * (DELTA - c) / DELTA) - s
                co[j] += tans[k] * ds
    me = ob.data
    me.vertices.foreach_set('co', co.ravel())
    me.update()
    return rings, nu, co


def end_moss(V, ob, rings, nu, co):
    """內壁靠洞口那一段（約 0.8 m）長苔：點屬性 EndMoss。"""
    ss = np.array([q[3] for q in rings])
    tot = ss[-1]
    w = np.zeros(len(co), np.float32)
    for k, s in enumerate(ss):
        d = min(s, tot - s)
        w[k * nu:(k + 1) * nu] = max(0.0, 1 - d / 1.0) ** 1.5 * .55
    at = ob.data.attributes.new('EndMoss', 'FLOAT', 'POINT')
    at.data.foreach_set('value', w)


def clear_inner(V, trunk, inner, gap=.06):
    """內壁不能穿出外殼：外殼樹皮深溝（約 0.2 r）和剝皮（退到 0.925 r）會讓殼變得很薄。
    從隧道軸心往每個內壁頂點的方向打到外殼，離外殼內面不到 gap 的頂點往軸心推回來。"""
    from mathutils.bvhtree import BVHTree
    me = trunk.data
    t = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
    n = 0
    for v in inner.data.vertices:
        x = v.co.x
        c = Vector((x, axis_y(V, x) + .03, axis_z(V, x) + .05))
        d = v.co - c
        d.x = 0.0
        rr = d.length
        if rr < 1e-6:
            continue
        h = t.ray_cast(c, d / rr, 4)[0]
        if h is not None and (h - c).length < rr + gap:
            v.co = c + d * (((h - c).length - gap) / rr) + Vector((v.co.x - c.x, 0, 0))
            n += 1
    inner.data.update()
    print('inner pushed in', n, 'of', len(inner.data.vertices))


def inner_rings(V, inner, amp=.08, period=.40):
    """內壁一圈圈的朽木層：沿離最近洞口的距離 s 做鋸齒（每 period 一圈），台階朝洞口（從洞口往裡看是一層層疊進去的鱗片），
    台階邊照角度加雜訊（一舌一舌、參差，不是一圈整齊的環）。平均為零，隧道淨空不變小；之後 clear_inner 再保殼厚。只做高模（烘進法線）。"""
    L = V['L']
    s0 = V['seed'] * .37
    for v in inner.data.vertices:
        x = v.co.x
        c = Vector((x, axis_y(V, x) + .03, axis_z(V, x) + .05))
        d = v.co - c
        d.x = 0.0
        rr = d.length
        if rr < 1e-6:
            continue
        th = math.atan2(d.z, d.y)
        cs, sn = math.cos(th), math.sin(th)
        s = min(x, L - x)
        n = .10 * fb((cs * 1.8, sn * 1.8, s * .35 + s0), 1.0, 2) + .06 * fb((cs * 6.5, sn * 6.5, s * .8 + s0), 1.0, 2)
        f = ((s + n) / period) % 1.0
        h = (1 - f) ** 2.2 - 1 / 3.2
        a = amp * (1 + .35 * fb((cs * 3, sn * 3, s * .5 + 9), 1.0, 2))
        v.co = c + d * ((rr - a * h) / rr) + Vector((v.co.x - c.x, 0, 0))
    inner.data.update()


def flip(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    bm.to_mesh(ob.data)
    bm.free()


def rim(V, coll, name, outer_ring, inner_ring, axis_dir, mat, seed, rows=7, lowpoly=False):
    """洞口的斷面：外圈（樹皮端）到內圈（朽木端）之間一圈朽爛的斷面，往外鼓一點、坑坑疤疤。
    outer_ring / inner_ring：兩圈頂點座標（照角度排、起點同一個角度），axis_dir：往洞外的方向。"""
    no, ni = len(outer_ring), len(inner_ring)
    M = max(no, ni) if not lowpoly else max(12, min(no, ni))

    def at(ring, t):
        n = len(ring)
        f = t * n
        i0 = int(f) % n
        return ring[i0] * (1 - (f - int(f))) + ring[(i0 + 1) % n] * (f - int(f))
    ad = Vector(axis_dir).normalized()
    rows = 22 if not lowpoly else 15          # 低模也要有年輪台階，不然輪廓上看不出一層層剝開
    NL = 5                                   # 年輪層：一圈圈往內退（參考圖洞口是一層層剝開的厚殼）

    def layers(u, th):
        return _layers(u, th) - u * _layers(1.0, th)        # 內外兩圈固定（接外殼、內壁），中間一層層鋸齒台階

    def _layers(u, th):
        rec = 0.0
        for k in range(NL):
            b = (k + .7) / (NL + .4) + .05 * fb((math.cos(th) * 3, math.sin(th) * 3, k * 5 + seed), 1.0, 2)
            stp = .04 + .06 * abs(fb((math.cos(th) * 4, math.sin(th) * 4, k * 7 + seed + 2), 1.0, 2)) * 2
            rec += stp * _sm((u - b) / .035)
        return rec
    vs, fs, em = [], [], []
    for r_ in range(rows + 1):
        u = r_ / rows
        for j in range(M):
            t = j / M
            th = 2 * math.pi * t
            po, pi = Vector(at(outer_ring, t)), Vector(at(inner_ring, t))
            p = po.lerp(pi, u)
            if 0 < r_ < rows and lowpoly:
                p = p - ad * layers(u, th)
            if 0 < r_ < rows and not lowpoly:
                lump = .03 * math.sin(math.pi * u) * (.4 + abs(fb((math.cos(th) * 6, math.sin(th) * 6, u * 3 + seed), 1.0, 3)) * 1.6)
                crumb = .02 * fb((math.cos(th) * 18, math.sin(th) * 18, u * 8 + seed), 1.0, 2)
                p = p + ad * (lump + crumb - layers(u, th))
            vs.append(tuple(p))
            top = max(0.0, (math.sin(th) - .15) / .85)                  # 上半邊：苔從外面長到洞口邊、蓋過外面一兩層
            em.append(.05 + .20 * u + 1.0 * top * max(0.0, 1 - u / .60))
    for r_ in range(rows):
        for j in range(M):
            a, b_ = r_ * M + j, r_ * M + (j + 1) % M
            fs.append((a, b_, b_ + M, a + M))
    me = bpy.data.meshes.new(name)
    me.from_pydata(vs, [], fs)
    me.update()
    # 法線朝洞外（+ad）
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.normal_update()
    if sum(f.normal.dot(ad) for f in bm.faces) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    at_ = me.attributes.new('EndMoss', 'FLOAT', 'POINT')
    at_.data.foreach_set('value', np.array(em, np.float32))
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    return _obj(name, me, coll)


def end_ring(co, nu, k, rings_up_first=True):
    return [Vector(co[k * nu + i]) for i in range(nu)]


def peel5(ob, pts, seed, frac_thr=-.06):
    """DR05 樹皮剝掉一半：和 DR06 peel 一樣（壓回 0.925 r 的木頭圓柱、點屬性 Peel），門檻低很多；頂上苔的地方不剝。"""
    rings, nu, co = ring_info(ob, pts)
    mo = vert_moss(ob.data)
    w = np.zeros(len(co))
    tot = rings[-1][3]
    for k, (c, r, fl, s) in enumerate(rings):
        cc = np.array(c)
        for i in range(nu):
            j = k * nu + i
            d = co[j] - cc
            rr = np.linalg.norm(d)
            if rr < 1e-6:
                continue
            dn = d / rr
            if dn[2] > .62:
                continue
            th_ = math.atan2(dn[2], dn[1])
            pn = fb((co[j][0] * .32 + seed, math.cos(th_) * 1.3, math.sin(th_) * 1.3), 1.0, 3) + .25 * fb(co[j] * 1.4, 1.0, 2)      # 兩側都有、一大片一大片（沿長 1–3 m）
            ww = _sm((pn - frac_thr) / .06) * (1 - _sm((mo[j] - .10) / .25))
            if ww <= 0:
                continue
            w[j] = ww
            co[j] = cc + dn * (rr * (1 - ww) + r * .925 * ww)
    me = ob.data
    me.vertices.foreach_set('co', co.ravel())
    at = me.attributes.new('Peel', 'FLOAT', 'POINT')
    at.data.foreach_set('value', w.astype(np.float32))
    me.update()
    print('peel verts', int((w > .5).sum()), 'of', len(w))
    return w


def bark_plates(V, ob, pts, seed):
    """瓦片狀的樹皮板（參考圖整條樹皮是一片片鱗狀的板，不只是長稜溝）：在（沿長 x, 繞圈弧長）上做 Voronoi 格子，
    格子沿長 0.42 m、繞圈 0.16 m；格子邊緣往內壓成裂縫，每片朝 +X 那端微微翹起（像瓦片）。剝皮處、苔厚處不做。"""
    from mathutils import noise as mn
    rings, nu, co = ring_info(ob, pts)
    mo = vert_moss(ob.data)
    pe = np.empty(len(co), np.float32)
    ob.data.attributes['Peel'].data.foreach_get('value', pe)
    for k, (c, r, fl, s) in enumerate(rings):
        cc = np.array(c)
        for i in range(nu):
            j = k * nu + i
            w = (1 - _sm((pe[j] - .2) / .4)) * (1 - _sm((mo[j] - .15) / .3))
            if w <= 0:
                continue
            d = co[j] - cc
            rr = np.linalg.norm(d)
            if rr < 1e-6:
                continue
            th_ = math.atan2(d[2], d[1])
            P = Vector((co[j][0] / .30 + seed, th_ * r / .13, 0.0))
            ds, ps = mn.voronoi(P)
            edge = ds[1] - ds[0]
            crack = 1 - _sm(edge / .25)
            lift = .025 * max(-1.0, min(1.0, (P.x - ps[0].x) * 2.0)) + .01
            co[j] = cc + d / rr * (rr + w * (lift - .06 * crack))
    ob.data.vertices.foreach_set('co', co.ravel())
    ob.data.update()


def debris(V, coll, R, mat, n, sub=2):
    """洞裡地上的朽木碎塊：壓扁的不規則團塊，沿長度拉長一點。"""
    bm = bmesh.new()
    for k in range(n):
        x = R.uniform(.5, V['L'] - .5)
        y = axis_y(V, x) + .03 + R.gauss(0, .22)
        zf = axis_z(V, x) + .05 - in_r(V, x) * math.sqrt(max(0.0, 1 - ((y - axis_y(V, x) - .03) / in_r(V, x)) ** 2)) * .97
        s = R.uniform(.05, .16)
        tmp = bmesh.new()
        bmesh.ops.create_icosphere(tmp, subdivisions=sub, radius=1.0)
        for v in tmp.verts:
            d = v.co.copy()
            q = d * (1 + .35 * fb(d * 1.8 + Vector((k, 0, 0)), 1.0, 2))
            v.co = Vector((q.x * s * R.uniform(1.4, 2.4), q.y * s, q.z * s * .55)) + Vector((x, y, zf + .06 + s * .18))      # 坐在洞裡的泥土地面上
        me_ = bpy.data.meshes.new('tmp')
        tmp.to_mesh(me_)
        tmp.free()
        bm.from_mesh(me_)
        bpy.data.meshes.remove(me_)
    me = bpy.data.meshes.new('DR05_Debris')
    bm.to_mesh(me)
    bm.free()
    at = me.attributes.new('EndMoss', 'FLOAT', 'POINT')
    at.data.foreach_set('value', np.zeros(len(me.vertices), np.float32))
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    return _obj('Debris', me, coll)


def slabs(V, coll, R, mat, rings, lowpoly=False):
    """翹起來的大片樹皮：從剝皮處邊緣翹出去的弧形板（外面樹皮、裡面淺色木頭），一片掉在地上。
    樹皮材質要頂點色 Mask（R 苔、G 凹凸高度、B 稜溝）和 UV 'UV'，這裡自己寫。"""
    out = []
    spec = ((.36, -1.15, 1.3, .62, .30), (.70, 1.25, 1.0, .52, .24), (.18, -1.45, .9, .55, .18))
    nu_, nv_ = (8, 6) if lowpoly else (22, 16)
    for q, (f, ang, ln, wid, curl) in enumerate(spec):
        s0 = f * V['L']
        c, n, a, r = surf(rings, s0, ang)
        up = Vector((0, 0, 1))
        up = (up - a * up.dot(a)).normalized()
        sd = a.cross(up).normalized()
        th_w = wid / r
        vs, fs, cols, uvs, pe = [], [], [], [], []
        T = .028
        for side_ in (0, 1):                 # 0 外面（樹皮）、1 裡面（木頭）
            for i in range(nu_ + 1):
                for j in range(nv_ + 1):
                    u, v = i / nu_, j / nv_
                    an = ang - th_w / 2 + th_w * u
                    lift = curl * u ** 1.8 * (1 + .3 * math.sin(v * 3 + q)) + .015
                    rr = r * .99 + lift + (-T if side_ else 0.0) + .006 * fb((u * 9, v * 9, q), 1.0, 2)
                    nn = (up * math.cos(an) + sd * math.sin(an))
                    p = c + a * (ln * (v - .5)) + nn * rr
                    p = p + a * (.08 * curl * u * math.sin(v * math.pi))
                    vs.append(tuple(p))
                    cols.append((0.0, .55, .35, 1.0))
                    uvs.append((u * wid / TILE, v * ln / TILE))
                    pe.append(float(side_))
        base1 = (nu_ + 1) * (nv_ + 1)
        for side_ in (0, 1):
            off = side_ * base1
            for i in range(nu_):
                for j in range(nv_):
                    a0 = off + i * (nv_ + 1) + j
                    quad = (a0, a0 + nv_ + 1, a0 + nv_ + 2, a0 + 1)
                    fs.append(quad if side_ == 0 else quad[::-1])
        # 四個邊：外面和裡面接起來
        idx = lambda s_, i, j: s_ * base1 + i * (nv_ + 1) + j
        for i in range(nu_):
            for j in (0, nv_):
                f_ = (idx(0, i, j), idx(0, i + 1, j), idx(1, i + 1, j), idx(1, i, j))
                fs.append(f_ if j == 0 else f_[::-1])
        for j in range(nv_):
            for i in (0, nu_):
                f_ = (idx(0, i, j), idx(1, i, j), idx(1, i, j + 1), idx(0, i, j + 1))
                fs.append(f_ if i == 0 else f_[::-1])
        if q == 2:                           # 第三片掉在地上：繞樹幹軸轉到樹皮面朝上，搬到樹幹腳邊（+Y 側）躺著
            from mathutils import Matrix
            rot = Matrix.Rotation(ang, 4, a)
            P = [rot @ (Vector(v_) - c) for v_ in vs]
            zmin = min(p_.z for p_ in P)
            cy = sum(p_.y for p_ in P) / len(P)
            off = Vector((0, axis_y(V, s0) + out_r(V, s0) * 1.0 + .45 - cy, .01 - zmin))
            vs = [tuple(p_ + Vector((c.x, 0, 0)) + off) for p_ in P]
        me = bpy.data.meshes.new(f'{PRE}_Slab{q}')
        me.from_pydata(vs, [], fs)
        me.update()
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.normal_update()
        bm.to_mesh(me)
        bm.free()
        ca = me.color_attributes.new('Mask', 'FLOAT_COLOR', 'CORNER')
        uvl = me.uv_layers.new(name='UV')
        vi = np.empty(len(me.loops), np.int32)
        me.loops.foreach_get('vertex_index', vi)
        ca.data.foreach_set('color', np.array(cols, np.float32)[vi].ravel())
        uvl.data.foreach_set('uv', np.array(uvs, np.float32)[vi].ravel())
        at = me.attributes.new('Peel', 'FLOAT', 'POINT')
        at.data.foreach_set('value', np.array(pe, np.float32))
        for p in me.polygons:
            p.use_smooth = True
        me.materials.append(mat)
        out.append(_obj(f'Slab{q}', me, coll))
    return out


def trunk_moss5(p, n):
    """DR05 的苔：頂上不是一整片地毯，是一團一團、一條一條（參考圖苔塊之間露出樹皮和地衣），兩側偶爾垂下一舌。"""
    blot = fb((p.x * .55, p.y * .9, p.z * .9 + 5.0), 1.0, 3)
    tongue = max(0.0, fb((p.x * .9, 3.1 if p.y > 0 else 7.3, 0), 1.0, 3)) * 1.3
    side = max(0.0, min(1.0, (n.z + .45) / .5))
    return .30 * max(0.0, n.z) + .05 + .32 * blot * max(0.0, n.z) + .24 * tongue * side


HOLES = ((.42, math.pi / 2 + .25, .46, .34, 0), (.66, math.pi / 2 - .35, .36, .27, 1))     # (沿長比例, 角度, 沿長半軸 m, 繞圈半軸 m, 種子)


def _hole_rho(V, h, x, th, r, inner):
    f, th0, ax, at, hs = h
    k = 1.12 if inner else 1.0
    dx = (x - f * V['L']) / (ax * k)
    dth = (th - th0 + math.pi) % (2 * math.pi) - math.pi
    dt = dth * r / (at * k)
    phi = math.atan2(dt, dx)
    edge = 1 + .20 * fb((math.cos(phi) * 1.7, math.sin(phi) * 1.7, hs * 7 + (3 if inner else 0)), 1.0, 3) + .13 * fb((math.cos(phi) * 6, math.sin(phi) * 6, hs + (5 if inner else 0)), 1.0, 3)   # 撕得參差
    return math.hypot(dx, dt) / edge, phi


def _param(V, p, inner):
    x = p[0]
    ay = axis_y(V, x) + (.03 if inner else 0.0)
    az = axis_z(V, x) + (.05 if inner else 0.0)
    return x, math.atan2(p[2] - az, p[1] - ay), math.hypot(p[1] - ay, p[2] - az)


def punch_holes(V, coll, trunk, inner, mat, lowpoly=False):
    """頂上中段兩個朽穿的洞（參考圖頂上有洞、看得到裡面）：外殼、內壁各挖掉一塊，中間補一圈參差的斷面（Lip）。
    要在照環排頂點的步驟（剝皮、洞口、苔）之後做：刪面之後頂點順序就亂了。"""
    loops = {}
    for ob, inn in ((trunk, False), (inner, True)):
        from mathutils.bvhtree import BVHTree
        me0 = ob.data
        surf_t = BVHTree.FromPolygons([v.co.copy() for v in me0.vertices], [tuple(p.vertices) for p in me0.polygons])   # 挖洞前的表面
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        kill = []
        for f in bm.faces:
            c = f.calc_center_median()
            x, th, r = _param(V, c, inn)
            if any(_hole_rho(V, h, x, th, r, inn)[0] < 1.0 for h in HOLES):
                kill.append(f)
        bmesh.ops.delete(bm, geom=kill, context='FACES')
        # 洞邊照四邊形一格格刪，邊是鋸齒的方格：把洞邊的頂點沿洞的徑向推到參差的橢圓上（rho = 1）
        for hi, h in enumerate(HOLES):
            f0, th0, ax, at, hs = h
            kk = 1.12 if inn else 1.0
            for v in {v for e in bm.edges if e.is_boundary for v in e.verts}:
                x, th, r = _param(V, v.co, inn)
                rho, phi = _hole_rho(V, h, x, th, r, inn)
                if not (1e-6 < rho < 1.6):
                    continue
                dx = (x - f0 * V['L']) / (ax * kk) / rho
                dt = ((th - th0 + math.pi) % (2 * math.pi) - math.pi) * r / (at * kk) / rho
                x2 = f0 * V['L'] + dx * ax * kk
                t2 = th0 + dt * at * kk / r
                c0 = Vector((x2, axis_y(V, x2) + (.03 if inn else 0.0), axis_z(V, x2) + (.05 if inn else 0.0)))
                dd = Vector((0.0, math.cos(t2), math.sin(t2)))
                hh = surf_t.ray_cast(c0, dd, 4)[0]                # 貼回新位置的實際表面（苔、樹皮稜高低差 10 cm 以上，留原本半徑會凸出一圈）
                v.co = hh if hh is not None else c0 + dd * r
        for hi, h in enumerate(HOLES):
            pts = []
            for e in bm.edges:
                if not e.is_boundary:
                    continue
                for v in e.verts:
                    x, th, r = _param(V, v.co, inn)
                    rho, phi = _hole_rho(V, h, x, th, r, inn)
                    if rho < 1.6:
                        pts.append((phi, v.co.copy()))
            pts = sorted({round(p[0], 6): p for p in pts}.values(), key=lambda q: q[0])
            loops[(hi, inn)] = pts
        bm.to_mesh(ob.data)
        bm.free()
        ob.data.update()
    out = []
    N = 28 if lowpoly else 72
    rows = 2 if lowpoly else 5
    for hi, h in enumerate(HOLES):
        po, pi_ = loops[(hi, False)], loops[(hi, True)]
        if len(po) < 6 or len(pi_) < 6:
            print('HOLE', hi, 'boundary too small', len(po), len(pi_))
            continue

        def ring_at(pts, phis):
            a = np.array([q[0] for q in pts])
            P = np.array([q[1][:] for q in pts])
            a2 = np.concatenate([a - 2 * math.pi, a, a + 2 * math.pi])
            P2 = np.concatenate([P, P, P])
            return np.stack([np.interp(phis, a2, P2[:, d]) for d in range(3)], 1)
        phis = np.linspace(-math.pi, math.pi, N, endpoint=False)
        Ro, Ri = ring_at(po, phis), ring_at(pi_, phis)
        ctr = Vector(((Ro.mean(0) + Ri.mean(0)) * .5))
        vs, fs, em = [], [], []
        for r_ in range(rows + 1):
            u = r_ / rows
            for j in range(N):
                p = Vector(Ro[j] * (1 - u) + Ri[j] * u)
                if 0 < r_ < rows:
                    d = ctr - p
                    d.z = 0.0
                    d = d.normalized() if d.length > 1e-6 else Vector((0, 0, 0))
                    ph = phis[j]
                    lump = .045 * math.sin(math.pi * u) * (.3 + 1.5 * abs(fb((math.cos(ph) * 5, math.sin(ph) * 5, u * 3 + hi * 9), 1.0, 3)))
                    p = p + d * lump + Vector((0, 0, -.02 * math.sin(math.pi * u)))
                    if r_ == 1:                          # 頂邊磨圓：第一圈往洞裡、往下收一點
                        p = p + d * .03 - Vector((0, 0, .02))
                vs.append(tuple(p))
                em.append(.95 * max(0.0, 1 - u / .45) + .12)          # 苔從洞邊往下長一段，蓋過斷面頂邊
        for r_ in range(rows):
            for j in range(N):
                a, b_ = r_ * N + j, r_ * N + (j + 1) % N
                fs.append((a, b_, b_ + N, a + N))
        me = bpy.data.meshes.new(f'Lip{hi}')
        me.from_pydata(vs, [], fs)
        me.update()
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.normal_update()
        s_ = 0.0
        for f in bm.faces:
            d = ctr - f.calc_center_median()
            d.z = 0.0
            s_ += f.normal.dot(d)
        if s_ < 0:                                   # 斷面朝洞的中心
            bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
        bm.to_mesh(me)
        bm.free()
        me.attributes.new('EndMoss', 'FLOAT', 'POINT').data.foreach_set('value', np.array(em, np.float32))
        for p in me.polygons:
            p.use_smooth = True
        me.materials.append(mat)
        out.append(_obj(f'Lip{hi}', me, coll))
        print('HOLE', hi, 'outer', len(po), 'inner', len(pi_))
    return out


def rim_flakes(V, coll, R, mat, e, outer_ring, inner_ring, axis_dir, n=70, lowpoly=False, trunk=None, n_sh=0):
    """洞口一層層往外翻、捲起來的朽木片（參考圖洞口邊緣參差、翹起來）：扁的長條，從斷面往洞外、往外圈翻，上半邊多、長。
    面屬性 Shard／點屬性 ShardU：遊戲模型改指到圖集最下面一條的橘褐漸層（太薄烘不準）。"""
    ad = Vector(axis_dir).normalized()
    no = len(outer_ring)
    c = sum((Vector(p) for p in outer_ring), Vector()) / no
    bm = bmesh.new()
    shl = bm.faces.layers.int.new('Shard')
    sul = bm.verts.layers.float.new('ShardU')
    nseg = 3 if lowpoly else 6
    sec = ((-1, 0), (-.6, 1), (.6, 1), (1, 0), (.6, -1), (-.6, -1))      # 扁的斷面：兩面寬、邊薄
    ns = len(sec)

    def emit(q, base, rad, ln, wd, tk, bend, cup, ang0=0.0):
        tan = ad.cross(rad).normalized()
        rows = []
        p = base.copy()
        for s_ in range(nseg + 1):
            u = s_ / nseg
            ang = ang0 + bend * u ** 1.2
            d = ad * math.cos(ang) + rad * math.sin(ang)
            if s_:
                p = p + d * (ln / nseg)
            nr = d.cross(tan).normalized()
            ww = wd * (1 - .70 * u ** 1.3) * (1 + .18 * math.sin(u * 9 + q)) + .0015      # 收窄但不收成尖（尖的一根根像刺）
            tt = tk * (1 - .5 * u) + .0015
            tw = R.uniform(-.2, .2) * u
            t1 = tan * math.cos(tw) + nr * math.sin(tw)
            t2 = -tan * math.sin(tw) + nr * math.cos(tw)
            ring = []
            for sx, sy in sec:
                vv = bm.verts.new(p + t1 * ww * sx + t2 * (tt * sy + cup * ww * sx * sx))
                vv[sul] = u
                ring.append(vv)
            rows.append(ring)
        for s_ in range(nseg):
            for k in range(ns):
                f = bm.faces.new((rows[s_][k], rows[s_][(k + 1) % ns], rows[s_ + 1][(k + 1) % ns], rows[s_ + 1][k]))
                f[shl] = 1
        for rr_ in (rows[0], rows[-1]):
            f = bm.faces.new(rr_)
            f[shl] = 1
    for q in range(n):
        th = R.gauss(math.pi / 2, .85) if R.random() < .8 else R.uniform(-.3, math.pi + .3)      # 上半邊多，貼地的下半邊不放
        t = (th / (2 * math.pi)) % 1.0
        f_ = t * no
        i0 = int(f_) % no
        w_ = f_ - int(f_)
        po = Vector(outer_ring[i0]).lerp(Vector(outer_ring[(i0 + 1) % no]), w_)
        ni = len(inner_ring)
        g_ = t * ni
        pi = Vector(inner_ring[int(g_) % ni]).lerp(Vector(inner_ring[(int(g_) + 1) % ni]), g_ - int(g_))
        u0 = R.uniform(.0, .55) ** 1.3
        base = po.lerp(pi, u0) - ad * R.uniform(.03, .07)
        rad = base - c
        rad -= ad * rad.dot(ad)
        rad = rad.normalized()
        tan = ad.cross(rad).normalized()
        top = max(0.0, math.sin(th))
        thin = R.random() < .25                                  # 四分之一是細纖維條
        ln = (R.uniform(.12, .24) if thin else R.uniform(.07, .19)) * (1 + .35 * top)
        wd = R.uniform(.014, .026) if thin else R.uniform(.035, .08) * (1 + .25 * top)
        tk = R.uniform(.004, .007)
        bend = R.uniform(2.1, 3.1) * (1.1 - .4 * u0)             # 往外翻、捲回貼著外面（第四輪試過只翻 1–2 弧度：一根根往外刺）            # 翻過去貼回外面（從正面看不會一根根往外刺）              # 總共往外圈翻多少（弧度）：靠外圈的翻到貼回樹皮
        cup = R.uniform(.0, .35)
        emit(q, base, rad, ln, wd, tk, bend, cup)
    # 洞口外面一圈鱗片：洞口外 0.6 m 內的樹皮上，一片片朝洞口方向、往外翹（參考圖洞口外緣一片片鱗狀木片疊得很密）
    if trunk is not None and n_sh:
        from mathutils.bvhtree import BVHTree
        me_t = trunk.data
        tb = BVHTree.FromPolygons([v.co.copy() for v in me_t.vertices], [tuple(p.vertices) for p in me_t.polygons])
        made = 0
        for q in range(n_sh * 3):
            if made >= n_sh:
                break
            th = R.gauss(math.pi / 2, 1.0) if R.random() < .75 else R.uniform(-.4, math.pi + .4)
            t = (th / (2 * math.pi)) % 1.0
            f_ = t * no
            i0 = int(f_) % no
            po = Vector(outer_ring[i0]).lerp(Vector(outer_ring[(i0 + 1) % no]), f_ - int(f_))
            dd = .04 + .56 * R.random() ** 1.6
            rad = po - c
            rad -= ad * rad.dot(ad)
            if rad.length < 1e-6:
                continue
            rad = rad.normalized()
            o_ = c + ad * ((po - c).dot(ad) - dd)          # 軸心上、比這個角度的洞口邊緣往裡 dd 公尺
            hit = tb.ray_cast(o_, rad, 4)[0]
            if hit is None or (hit - o_).length < .5:
                continue
            base = hit - rad * .012
            top = max(0.0, math.sin(th))
            emit(1000 + q, base, rad, R.uniform(.07, .15) * (1 + .3 * top), R.uniform(.04, .08), R.uniform(.004, .007),
                 R.uniform(.2, .6) * (1 - .5 * dd), R.uniform(.05, .25), ang0=R.uniform(.02, .10))     # 貼著樹皮、只翹一點，不要一塊塊立起來
            made += 1
        print('SHINGLES', e, made)
    bm.normal_update()
    me = bpy.data.meshes.new(f'Flake{e}')
    bm.to_mesh(me)
    bm.free()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    me.attributes.new('EndMoss', 'FLOAT', 'POINT').data.foreach_set('value', np.zeros(len(me.vertices), np.float32))
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    return _obj(f'Flake{e}', me, coll)


def floor_strip(V, coll, inner, lowpoly=False):
    """洞裡的地面：一條泥土＋碎屑的帶子（參考圖洞裡是土和落葉，不是光禿禿的朽木），兩邊塞進內壁裡。
    高度照內壁中線實際打到的地方往上 6–9 cm。"""
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    t = BVHTree.FromObject(inner, dg)
    L = V['L']
    nx, ny = (24, 4) if lowpoly else (110, 14)
    x0, x1 = .55, L - .55
    vs, fs, mm = [], [], []
    for i in range(nx + 1):
        x = x0 + (x1 - x0) * i / nx
        ay, az = axis_y(V, x) + .03, axis_z(V, x) + .05
        h = t.ray_cast(Vector((x, ay, az)), Vector((0, 0, -1)), 3)[0]
        zb = h.z if h else az - in_r(V, x) * .97
        hw = .52 * (.55 + .45 * _sm(min(x - x0, x1 - x) / .8))
        for j in range(ny + 1):
            v = j / ny * 2 - 1
            y = ay + hw * v
            z = zb + .065 + .028 * fb((x * 1.3, y * 1.3, 4.0), 1.0, 3) + .012 * fb((x * 6, y * 6, 1.0), 1.0, 2) - .05 * abs(v) ** 3
            vs.append((x, y, z))
            mm.append(.06 + .10 * max(0.0, fb((x * .8, y, 2.0), 1.0, 2)))
    for i in range(nx):
        for j in range(ny):
            a = i * (ny + 1) + j
            fs.append((a, a + ny + 1, a + ny + 2, a + 1))
    me = bpy.data.meshes.new('Floor')
    me.from_pydata(vs, [], fs)
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.normal_update()
    if sum(f.normal.z for f in bm.faces) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    me.attributes.new('MudMoss', 'FLOAT', 'POINT').data.foreach_set('value', np.array(mm, np.float32))
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mud_material())
    return _obj('Floor', me, coll)


def col_shell(V, coll, sides=12, step=1.0):
    """碰撞殼：一條厚壁管（外 0.98 r、內孔比實際內徑大 2 cm），兩頭用平均的洞口位置封成環。法線朝殼外（隧道裡朝軸心）。"""
    L = V['L']
    x0 = .30
    x1 = L - .45
    xs = list(np.linspace(x0, x1, max(2, int((x1 - x0) / step) + 1)))
    vs, fs = [], []
    for k, x in enumerate(xs):
        for side_, rad in ((0, out_r(V, x) * .98), (1, in_r(V, x) + .02)):
            for i in range(sides):
                th = 2 * math.pi * i / sides
                cz = axis_z(V, x) + (.05 if side_ else 0.0)
                cy = axis_y(V, x) + (.03 if side_ else 0.0)
                vs.append((x, cy + math.cos(th) * rad, cz + math.sin(th) * rad * .96))
    S = 2 * sides
    for k in range(len(xs) - 1):
        for i in range(sides):
            i2 = (i + 1) % sides
            o0, o1 = k * S + i, k * S + i2
            fs.append((o0, o0 + S, o1 + S, o1))                       # 外壁
            n0, n1 = k * S + sides + i, k * S + sides + i2
            fs.append((n0, n1, n1 + S, n0 + S))                       # 內壁
    for k, sg in ((0, -1), (len(xs) - 1, 1)):
        for i in range(sides):
            i2 = (i + 1) % sides
            o0, o1 = k * S + i, k * S + i2
            n0, n1 = k * S + sides + i, k * S + sides + i2
            fs.append((o0, o1, n1, n0) if sg < 0 else (o0, n0, n1, o1))
    me = bpy.data.meshes.new('Collision')
    me.from_pydata(vs, [], fs)
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    return _obj('Shell', me, coll)


def build(variant='A', quick=True, low=None, col=False, pre=''):
    """low=(step, numin, numax, nuk)：同一份路徑做不帶樹皮凹凸的低模；col=True：只做碰撞殼。"""
    V = set_variant(variant)
    CFG.update(step=.12 if quick else .05, numin=28 if quick else 48, numax=520, amp=.21, moss=.095, nuk=.8, crest=.40)
    if low:
        CFG.update(step=low[0], numin=low[1], numax=low[2], amp=0.0, moss=0.0, nuk=low[3])
    seed = V['seed']
    noise.seed_set(seed)
    R = random.Random(seed)
    coll = _coll(f"{PRE}_{V['name']}_{'Col' if col else ('Low' if low else 'High')}")
    if col:
        col_shell(V, coll)
        return _finish_names(coll, pre)
    mat = bark5_material()
    rmat = rot_material()
    objs = []
    tp = shell_pts(V)
    trunk = tube('Trunk', tp, seed, rib=.24, twist=.28, collection=coll, moss_bias=trunk_moss5, cap_end=False)   # 樹皮紋扭著轉（參考圖螺旋紋）
    trunk.data.materials.append(mat)
    objs.append(trunk)
    if not low:
        peel5(trunk, tp, seed)
        bark_plates(V, trunk, tp, seed)
    else:
        at = trunk.data.attributes.new('Peel', 'FLOAT', 'POINT')
    rings_o, nu_o, co_o = ragged_ends(V, trunk, tp)
    # 內壁：同一條路徑、小一號的管子，凹凸淺、不長苔，翻面朝軸心
    amp0, moss0 = CFG['amp'], CFG['moss']
    CFG.update(amp=amp0 * .5, moss=0.0)
    ip = shell_pts(V, inner=True)
    inner = tube('Inner', ip, seed + 5, rib=.12, twist=.06, collection=coll, moss_bias=-1.0, cap_end=False)     # 內壁一條條粗纖維
    CFG.update(amp=amp0, moss=moss0)
    rings_i, nu_i, co_i = ragged_ends(V, inner, ip, inner=True)
    if not low:
        inner_rings(V, inner)
    clear_inner(V, trunk, inner)
    co_i = np.array([v.co[:] for v in inner.data.vertices])
    end_moss(V, inner, rings_i, nu_i, co_i)
    flip(inner)
    inner.data.materials.append(rmat)
    objs.append(inner)
    # 洞口斷面：兩頭各一圈
    for e, k_o, k_i, ad in ((0, 0, 0, -1), (1, len(rings_o) - 1, len(rings_i) - 1, 1)):
        ta = rings_o[min(k_o + 1, len(rings_o) - 1)][0] - rings_o[max(k_o - 1, 0)][0]
        o = rim(V, coll, f'Rim{e}', end_ring(co_o, nu_o, k_o), end_ring(co_i, nu_i, k_i), ta.normalized() * ad, rmat, seed + e, lowpoly=bool(low))
        objs.append(o)
        objs.append(rim_flakes(V, coll, random.Random(seed + 30 + e), rmat, e, end_ring(co_o, nu_o, k_o), end_ring(co_i, nu_i, k_i),
                               ta.normalized() * ad, n=(80 if e else 64) if not low else (60 if e else 48), lowpoly=False,
                               trunk=trunk, n_sh=(50 if e else 56) if not low else (40 if e else 44)))      # 低模也用高模的段數：3 段的朽木片看起來像方塊
    objs += punch_holes(V, coll, trunk, inner, rmat, lowpoly=bool(low))
    objs.append(floor_strip(V, coll, inner, lowpoly=bool(low)))
    objs.append(debris(V, coll, R, rmat, 26 if not low else 26, sub=1 if low else 2))
    rings, _ = resample(tp, CFG['step'])
    # 翹起的大片樹皮（slabs）第一版看起來像貼上去的平板，先不放
    brackets(V, coll, random.Random(seed + 4), rings, core_plants.mushroom_material())
    print('BUILD', V['id'], 'low' if low else 'high', len(coll.objects), 'objects')
    return _finish_names(coll, pre)


# ---------------- 植物 ----------------
def dress(V, quick=True, seed=None, game=False, surf=('Trunk',)):
    """頂上（苔上）的苔叢、蕨、蕈；腳邊地上的大蕨、闊葉草、蕈、落葉；洞裡地上的落葉。"""
    seed = V['seed'] + 900 if seed is None else seed
    R = random.Random(seed)
    L, Rt = V['L'], V['R']
    coll = _coll(f"{PRE}_{V['name']}_{'GamePlants' if game else 'Plants'}")
    lm = core_plants._leaf_material
    mat = lambda n, *a, **k: bpy.data.materials.get(n) or lm(n, *a, **k)
    fern_mat = mat('D2_Fern', (.050, .090, .040, 1), (.11, .17, .075, 1), (.16, .22, .11, 1), gloss=.55)
    heart_mat = mat('D2_HeartLeafPale', (.060, .105, .050, 1), (.135, .20, .10, 1), (.22, .29, .16, 1), gloss=.4)
    moss_mat = mat('D2_MossTuft', (.040, .058, .014, 1), (.10, .125, .032, 1), (.12, .15, .045, 1), gloss=.8)
    litter_mat = mat('DR06_LitterLeaf', (.15, .07, .022, 1), (.42, .22, .07, 1), (.48, .30, .11, 1), gloss=.3)
    stem_mat = bpy.data.materials.get('D2_Stem')
    if stem_mat is None:
        stem_mat = bpy.data.materials.new('D2_Stem')
        stem_mat.use_nodes = True
        next(n for n in stem_mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Base Color'].default_value = (.05, .06, .025, 1)
    mush_mat = bpy.data.materials.get('UG_Mushroom') or core_plants.mushroom_material()
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()

    def hit(x, y, z0=6.0, d=(0, 0, -1)):
        ok, loc, nrm, _, ob, _ = sc.ray_cast(dg, Vector((x, y, z0)), Vector(d))
        return (loc, nrm, ob.name) if ok else None

    def on_log(x, y, nz=.72):
        h = hit(x, y)
        if h and h[2] in surf and h[1].z > nz:
            return h
        return None

    def half_w(x):
        r, zc = out_r(V, x), axis_z(V, x)
        return math.sqrt(max(0.0, r * r - zc * zc)) if zc < r else 0.0

    def keep(o):
        for c in list(o.users_collection):
            c.objects.unlink(o)
        coll.objects.link(o)
        return o

    out = []
    sz = Rt
    mounds = []
    for i in range(int(L * .9)):
        x = R.uniform(.10, .80) * L
        h = on_log(x, axis_y(V, x) + R.gauss(0, .18 * Rt), .8)
        if h:
            mounds.append((i, h[0].x, h[0].y, R.uniform(.22, .45) * sz, R.uniform(.14, .26) * sz, R.uniform(.03, .07), h[0].z - .03))
    if mounds and not game:
        out.append(keep(core_plants.moss_tufts('DR05_MossTufts', mounds, R, moss_mat, fb, density=2600 if quick else 5200)))
    nf = 0
    for i in range(40):
        if nf >= 4:
            break
        x = R.uniform(.10, .78) * L
        h = on_log(x, axis_y(V, x) + R.gauss(0, .22 * Rt), .8)
        if not h:
            continue
        o, so = core_plants.fern(f'DR05_TopFern{nf}', h[0] - Vector((0, 0, .03)), R, R.uniform(.70, 1.0) * sz, fern_mat, stem_mat)
        out += [keep(o), keep(so)]
        nf += 1
    nm = 0
    for i in range(30):
        if nm >= 2:
            break
        x = R.uniform(.2, .75) * L
        h = on_log(x, axis_y(V, x) + R.gauss(0, .30 * Rt), .6)
        if h:
            out.append(keep(core_plants.mushrooms(f'DR05_LogMush{nm}', h[0] - Vector((0, 0, .02)), R, R.randint(5, 9), 2.3 * sz, mush_mat, cap=MUSH_CAP)))
            nm += 1
    for k in range(4):
        x = R.uniform(.12, .9) * L
        sg = R.choice((-1, 1))
        y = axis_y(V, x) + sg * (half_w(x) + R.uniform(.06, .25))
        out.append(keep(core_plants.mushrooms(f'DR05_FootMush{k}', Vector((x, y, 0)), R, R.randint(4, 10), 2.6 * sz, mush_mat, cap=MUSH_CAP)))
    # 洞口裡面一叢小蕈（朽木上）
    x = L * .12
    h = hit(x, axis_y(V, x) + .15, axis_z(V, x))
    if h and h[2] not in ('Trunk',):
        out.append(keep(core_plants.mushrooms('DR05_InMush0', h[0] - Vector((0, 0, .01)), R, 6, 1.8 * sz, mush_mat, cap=MUSH_CAP)))
    for k in range(4):
        x = R.uniform(.08, .85) * L
        sg = -1 if k % 2 == 0 else 1
        y = axis_y(V, x) + sg * (half_w(x) + R.uniform(.35, .7))
        o, so = core_plants.fern(f'DR05_FootFern{k}', Vector((x, y, -.02)), R, R.uniform(1.0, 1.35) * sz, fern_mat, stem_mat)
        out += [keep(o), keep(so)]
    for k in range(3):
        x = R.uniform(.1, .9) * L
        sg = R.choice((-1, 1))
        y = axis_y(V, x) + sg * (half_w(x) + R.uniform(.2, .6))
        o = core_plants.heart_plant(f'DR05_Heart{k}', Vector((x, y, -.01)), R, R.uniform(.7, 1.0) * sz, heart_mat, stem_mat)
        out.append(keep(o))
        so = bpy.data.objects.get(f'DR05_Heart{k}_stem')
        if so:
            out.append(keep(so))

    def place():
        u = R.random()
        if u < .70:                          # 外面兩側
            x = R.uniform(-.6, 1.1) * L
            sg = R.choice((-1, 1))
            y = axis_y(V, x) + sg * (half_w(x) + abs(R.gauss(0, .55)) + .03)
            h = hit(x, y, 6.0)
            z = h[0].z if h else 0.0
            if z > .4:
                return None
        else:                                # 洞裡地上（從軸心往下打）
            x = R.uniform(.15, .95) * L
            y = axis_y(V, x) + R.gauss(0, .25)
            h = hit(x, y, axis_z(V, x) + .1)
            if not h or h[2] == 'Trunk':
                return None
            z = h[0].z
        return (x, y), z
    lo, n = litter('DR05_Litter', R, int(700 * (.6 if quick else 1.0)), place, litter_mat)
    out.append(keep(lo))
    print('DRESS', len(out), 'plant objects, litter', n)
    return coll


def _views(V):
    L = V['L']
    cx = L * .5
    zc = axis_z(V, L)
    return {
        'tq': ((L + 4.6, -6.2, 1.7), (L * .55, 0, .8), 26),
        'end': ((L + 5.5, axis_y(V, L) - .4, 1.05), (L, axis_y(V, L), zc), 32),
        'endA': ((-5.5, .5, 1.05), (0, 0, axis_z(V, 0)), 32),
        'inside': ((L - .25, axis_y(V, L - .25) + .05, .80), (0, axis_y(V, 0) + .05, .70), 16),
        'side': ((cx, -L * 1.25 - 3, 1.5), (cx, 0, .9), 30),
        'top': ((cx, -.01, L * 1.6 + 5), (cx, 0, 0), 30),
        'back': ((cx * .9, L * 1.0 + 3, 2.2), (cx, 0, .8), 28),
        'peel': ((L * .45, -3.6, 1.5), (L * .45, 0, .8), 30),
        'hole': ((L * .42 + 1.2, 2.8, 3.3), (L * .50, -.1, 1.7), 30),
    }


if __name__ == '__main__' and '--' in sys.argv:
    args = sys.argv[sys.argv.index('--') + 1:]
    var = args[0] if args else 'A'
    quick = (args[1] if len(args) > 1 else 'quick') == 'quick'
    outdir = args[2] if len(args) > 2 else 'D:/yun-jing-cache/dr05-work'
    os.makedirs(outdir, exist_ok=True)
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    build(var, quick)
    if 'nodress' not in args:
        dress(VAR, quick)
    import preview_dr
    preview_dr.setup(samples=24 if quick else 64, fog=False)
    hum = bpy.data.objects.get('DR_Human_1p75m')
    if hum:
        hum.location = (VAR['L'] * .5, -VAR['R'] * 2.0, .875)
    want = args[3].split(',') if len(args) > 3 else list(_views(VAR))
    for k in want:
        loc, tgt, lens = _views(VAR)[k]
        preview_dr.shot(os.path.join(outdir, f"DR05_{var}_{k}.png"), loc, tgt, lens, (1280, 720))
    for a_ in args[4:]:
        if a_.endswith('.blend'):                       # 第 5 個以後的參數：.blend 才存檔（nodress 之類的旗標不會被當成檔名）
            bpy.ops.wm.save_as_mainfile(filepath=a_)
