# DR08 長滿蕈和苔的朽木（高模），三種：
#   A 短截 2 m（徑 0.6 m）：兩頭斷、碎，中段頂上塌陷一塊，半陷進土裡；
#   B 3.5 m（徑 0.7 m）：一頭撕裂的斷口，中段頂上裂開、塌下去，看得到裡面一塊塊碎掉的褐腐木；
#   C 5 m（徑 0.8 m）：長長一條低低地陷在土裡，一頭朽空，鬆脫的樹皮板翹起、掛著。
# 工作包重點：「一碰會碎的感覺；層狀菌、苔、白色菌絲」。
#   - 褐腐：露出的木頭被縱橫的深裂縫切成一塊塊方塊（像木炭），深紅褐、軟、碎；旁邊地上一堆碎屑、木粉；
#   - 樹皮大半掉了，剩下的是一片片鬆的灰褐樹皮板；
#   - 側面一層層疊起來的層狀菌（奶油、黃褐、鏽褐的環帶，淺色邊）；一叢叢小褐蕈；
#   - 白色菌絲：裂縫裡、剝皮的木頭上一絲絲、一片片扇形的白；
#   - 頂上一層厚的深橄欖綠苔、苔墊，淺灰綠地衣，幾株蕨、小苗，落葉。
# 樹幹沿 +X：x = 0 到 L；正面 -Y；z = 0 是地面。原點之後由 dr_pivot.py 移到底部中心。
# 沿用 DR05 空心倒木（再往下是 DR06）：外殼＋內壁兩條管、參差的斷口、洞口斷面、頂上挖洞，只換尺寸、形狀函式、材質。
# 用法（背景，不要加 --factory-startup）：
#   blender -b --python build_dr08.py -- A quick <輸出資料夾> [鏡位,鏡位] [存檔.blend]
import bpy, bmesh, math, random, sys, os
import numpy as np
from mathutils import Vector

_HERE8 = os.path.dirname(os.path.abspath(globals().get('__file__', 'D:/yun-jing-d2-logs/art/source/d2-logs-b/build_dr08.py')))
_p5 = os.path.join(_HERE8, 'build_dr05.py')
_nm8 = globals().get('__name__')
globals()['__name__'] = 'build_dr05_lib'            # 不要跑 DR05 的主程式
exec(compile(open(_p5, encoding='utf-8').read(), _p5, 'exec'), globals())
MOSS_C = ((.013, .020, .006, 1), (.085, .092, .024, 1))      # 斷口邊的苔：同外殼的深橄欖（DR06 的黃綠在斷口邊是一條平塗的帶子）
globals()['__name__'] = _nm8
__file__ = os.path.join(_HERE8, 'build_dr08.py')

# L 長、R 外半徑、W 殼厚（中心朽空的心材）、sink 陷進土裡、bend 左右彎、sag 中段往下塌
# holes：頂上塌掉／裂開的洞（沿長比例, 角度（π/2 正上）, 沿長半軸 m, 繞圈半軸 m, 種子）
# fungi：(沿長比例, 繞軸角（0 正上，正值往 -Y）, 片數)：一叢疊成幾層
# ends：兩頭斷口的樣子（0：碎、塌；1：撕裂的長纖維）
VARIANTS = {
    'A': dict(name='Chunk', L=2.4, R=.46, W=.17, sink=.08, seed=181, bend=.05, sag=.05, ends=(0, 0),
              prof=((.50, -.36, .17), (.13, .10, .12), (.86, .10, .12)),      # 參考圖 A：中段塌成馬鞍、兩頭鼓起
              holes=((.52, math.pi / 2 + .15, .52, .30, 0),),                  # 中段頂上塌掉一大塊：側面看是馬鞍形（參考圖 A）
              fungi=((.28, 1.40, 5), (.74, 1.35, 3), (.55, -1.40, 4))),
    'B': dict(name='Split', L=3.9, R=.50, W=.17, sink=.09, seed=193, bend=.08, sag=.09, ends=(0, 1),
              prof=((.22, .14, .16), (.58, -.32, .13), (.88, .06, .10)),       # 參考圖 B：左段鼓、中段凹、撕裂端再翹起
              holes=((.48, math.pi / 2 - .10, .72, .28, 0), (.20, math.pi / 2 + .45, .20, .13, 1)),
              fungi=((.22, 1.40, 5), (.74, 1.35, 4), (.50, -1.40, 5))),
    'C': dict(name='Long', L=5.2, R=.55, W=.16, sink=.10, seed=211, bend=.11, sag=.06, ends=(2, 0),
              prof=((.15, .18, .16), (.55, -.38, .15), (.83, .08, .10)),       # 參考圖 C：洞口那頭高、中段凹、右段再鼓         # 參考圖 C：左端圓的朽空大洞口、右端碎
              holes=((.36, math.pi / 2 + .30, .38, .20, 0), (.74, math.pi / 2 - .25, .28, .17, 1)),
              fungi=((.16, -1.42, 6), (.47, 1.38, 5), (.62, -1.35, 4), (.86, 1.40, 4))),
}
VAR = VARIANTS['A']
PRE = 'DR08'
DELTA = .55                       # 兩頭參差的斷口：最後 0.55 m 內照角度壓縮
FL = .80                          # 扁度：朽軟了塌下來，斷面寬比高多（參考圖三種都是扁扁地趴在地上）
HOLES = VAR['holes']


def set_variant(v):
    global VAR, HOLES
    VAR = VARIANTS[v]
    VAR['id'] = v
    HOLES = VAR['holes']
    return VAR


# ---------------- 形狀 ----------------
def flx(V, x):
    """這個位置的斷面扁度（高／寬）：FL 乘上每種自己的起伏（prof：位置、增減、寬）。"""
    t = max(0.0, min(1.0, x / V['L']))
    return FL * (1.0 + sum(a * math.exp(-((t - tc) / w) ** 2) for tc, a, w in V.get('prof', ())))


def out_r(V, x):
    t = max(0.0, min(1.0, x / V['L']))
    return V['R'] * (1.0 + .35 * max(0.0, 1.0 - flx(V, x) / FL)) * (1.02 - .06 * t + .07 * math.sin(t * math.pi * (1.4 + .3 * V['L'] / 5) + V['seed'] * .3) + .025 * math.sin(t * 17.0 + V['seed']))


def axis_z(V, x):
    t = max(0.0, min(1.0, x / V['L']))
    return out_r(V, x) * flx(V, x) * .95 - V['sink'] - V['sag'] * math.sin(math.pi * t)      # 朽軟了，中段往下垂


def in_r(V, x):
    """中心朽空的心材：殼厚 W 上下起伏。"""
    t = max(0.0, min(1.0, x / V['L']))
    return out_r(V, x) - V['W'] * (1 + .20 * math.sin(t * 7.0 + 2.0) + .10 * math.sin(t * 19.0))


def flare(V, x, k):
    """朽木的斷口不往外張（DR05 的喇叭口拿掉），只有最後一點點鬆開。"""
    d = min(x, V['L'] - x)
    return 1 + .04 * _sm(1 - d / .25)


def end_cut(V, th, end, inner=False):
    """斷口在角度 th 往內縮多少公尺。ends[end] 0：碎、塌（上半邊缺一大塊）；1：撕裂（長短不齊的木條）。"""
    s = V['seed'] + 11 * end
    R_ = V['R']
    kind = V['ends'][end]
    c = R_ * (.15 + .45 * abs(fb((math.cos(th) * 1.7, math.sin(th) * 1.7, s), 1.0, 3))) + .02 * fb((math.cos(th) * 5, math.sin(th) * 5, s + 3), 1.0, 2)
    if kind == 0:
        d = (th - math.pi * (.55 if end else .40) + math.pi) % (2 * math.pi) - math.pi
        c += R_ * 1.05 * _sm(1 - abs(d) / 1.10) * (1 + .3 * fb((th * 3, s, 0), 1.0, 2))     # 上半邊碎掉一大塊
    elif kind == 2:
        c = R_ * (.06 + .16 * abs(fb((math.cos(th) * 2.5, math.sin(th) * 2.5, s), 1.0, 3)))  # 圓的朽空洞口：一圈還在、邊緣參差
        if inner:
            c += .10 + R_ * .35 * abs(fb((math.cos(th) * 2.3, math.sin(th) * 2.3, s + 7), 1.0, 2))   # 內壁往裡退，看得到一圈圈殼
        return max(0.0, min(DELTA - .06, c))
    else:
        c += R_ * .55 * abs(fb((math.cos(th) * 9, math.sin(th) * 9, s + 5), 1.0, 1))          # 撕裂：一條條長短不齊
    if inner:
        c += .03 + R_ * .25 * abs(fb((math.cos(th) * 2.3, math.sin(th) * 2.3, s + 7), 1.0, 2))
    return max(0.0, min(DELTA - .06, c))


def shell_pts(V, inner=False):
    pts = []
    n = max(9, int(V['L'] / .18) + 1)
    for x in np.linspace(0.0, V['L'], n):
        x = float(x)
        if inner:
            pts.append((x, axis_y(V, x) + .01, axis_z(V, x) + .02, in_r(V, x) * flare(V, x, 0), flx(V, x) + .03))
        else:
            pts.append((x, axis_y(V, x), axis_z(V, x), out_r(V, x) * flare(V, x, 0), flx(V, x)))
    return pts


def _param(V, p, inner):
    x = p[0]
    ay = axis_y(V, x) + (.01 if inner else 0.0)
    az = axis_z(V, x) + (.02 if inner else 0.0)
    return x, math.atan2(p[2] - az, p[1] - ay), math.hypot(p[1] - ay, p[2] - az)


def trunk_moss8(p, n):
    """頂上一層厚苔（參考圖整條頂上都蓋著），兩側一團團、一舌舌往下垂。"""
    blot = fb((p.x * 3.0, p.y * 3.5, p.z * 3.5 + 5.0), 1.0, 3)
    tongue = max(0.0, fb((p.x * 4.5, 3.1 if p.y > 0 else 7.3, 0), 1.0, 3)) * 2.2       # 一舌舌往下垂（沿長 10–25 cm 一條）
    side = max(0.0, min(1.0, (n.z + .55) / .6))
    clump = max(0.0, fb((p.x * 2.4, p.y * 2.8, p.z * 2.8 + 9.0), 1.0, 2))                      # 一團團隆起的苔墊（20–40 cm 一團）
    rag = fb((p.x * 9.0, p.y * 9.0, p.z * 9.0 + 3.0), 1.0, 2)                                   # 邊緣碎、中間有破洞（一整張連著像一層皮）
    return .40 * max(0.0, n.z) - .02 + .28 * blot + .22 * tongue * side + .9 * clump * max(0.0, n.z + .2) + .45 * rag      # 頂上一塊塊，側面露出木頭（整片包住像一張綠布）


# ---------------- 材質 ----------------
def cubic_rot(N, Lk, tc, scale=(11.0, 15.0, 15.0), seed=0.0):
    """褐腐的方塊裂紋：物件座標沿長拉開的 Chebychev Voronoi（方格狀的格子），回傳 (裂縫深度 0..1, 每塊亂數 0..1)。"""
    mp = N.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = scale
    mp.inputs['Location'].default_value = (seed, seed * .7, 0)
    Lk.new(tc.outputs['Object'], mp.inputs['Vector'])
    wn = N.new('ShaderNodeTexNoise')                 # 格線稍微歪，不是方格紙
    wn.inputs['Scale'].default_value = 1.2
    wn.inputs['Detail'].default_value = 2
    Lk.new(mp.outputs[0], wn.inputs['Vector'])
    wm = N.new('ShaderNodeVectorMath')
    wm.operation = 'MULTIPLY_ADD'
    wm.inputs[1].default_value = (.35, .35, .35)
    Lk.new(wn.outputs['Color'], wm.inputs[0])
    Lk.new(mp.outputs[0], wm.inputs[2])
    ve = N.new('ShaderNodeTexVoronoi')
    ve.feature = 'DISTANCE_TO_EDGE'
    ve.distance = 'CHEBYCHEV'
    ve.inputs['Randomness'].default_value = .55
    Lk.new(wm.outputs[0], ve.inputs['Vector'])
    vf = N.new('ShaderNodeTexVoronoi')
    vf.distance = 'CHEBYCHEV'
    vf.inputs['Randomness'].default_value = .55
    Lk.new(wm.outputs[0], vf.inputs['Vector'])
    crack = _ramp(N, .0, .045, (1, 1, 1, 1), (0, 0, 0, 1))         # 1 = 裂縫裡（細：真的方塊已經是幾何，這裡只是小裂）
    Lk.new(ve.outputs['Distance'], crack.inputs[0])
    return crack, vf


def rot8_material():
    """褐腐朽木（內壁、斷口、裂開處）：深紅褐的方塊、縫裡黑，縫裡和一片片扇形的白色菌絲；靠斷口的苔沿用 DR05 的 EndMoss。"""
    m = bpy.data.materials.get('DR08_Rot')
    if m:
        return m
    m = bpy.data.materials.new('DR08_Rot')
    m.use_nodes = True
    N, Lk = m.node_tree.nodes, m.node_tree.links
    b = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    tc = N.new('ShaderNodeTexCoord')
    crack, vf = cubic_rot(N, Lk, tc)
    # 每塊深淺不同（褐腐：深紅褐 → 偏橘褐）
    blk = _ramp(N, .0, 1.0, (.050, .018, .008, 1), (.165, .062, .025, 1))       # 鏽紅褐（參考圖細節）：灰褐的平塊配深縫像砌石牆     # 土褐（第一版深紅褐在引擎裡像巧克力、磚）     # 深紅褐（參考圖；太陽下 .17 已經是橘紅磚色）
    bn = N.new('ShaderNodeTexNoise')                       # 深淺：一片片受潮（不照格子）
    bn.inputs['Scale'].default_value = 9.0
    bn.inputs['Detail'].default_value = 4
    Lk.new(tc.outputs['Object'], bn.inputs['Vector'])
    Lk.new(bn.outputs['Fac'], blk.inputs[0])
    bc = N.new('ShaderNodeMixRGB')
    bc.blend_type = 'MULTIPLY'
    bc.inputs[0].default_value = 1.0
    Lk.new(blk.outputs[0], bc.inputs[1])
    Lk.new(vf.outputs['Color'], bc.inputs[2])
    bcr = N.new('ShaderNodeMixRGB')                        # 塊色（Voronoi 亂色乘回來會太花：只混一點）
    bcr.inputs[0].default_value = 0.0
    Lk.new(blk.outputs[0], bcr.inputs[1])
    Lk.new(bc.outputs[0], bcr.inputs[2])
    fib = _streak(N, Lk, (.9, 34.0, 34.0), 6)               # 沿長的細纖維
    fr = _ramp(N, .30, .75, (.52, .48, .45, 1), (1.18, 1.10, 1.02, 1))       # 纖維深淺拉開（看得出是木頭）
    Lk.new(fib.outputs['Fac'], fr.inputs[0])
    c1 = N.new('ShaderNodeMixRGB')
    c1.blend_type = 'MULTIPLY'
    c1.inputs[0].default_value = 1.0
    Lk.new(bcr.outputs[0], c1.inputs[1])
    Lk.new(fr.outputs[0], c1.inputs[2])
    cdk = N.new('ShaderNodeMixRGB')                        # 縫裡暗
    Lk.new(crack.outputs[0], cdk.inputs[0])
    Lk.new(c1.outputs[0], cdk.inputs[1])
    cdk.inputs[2].default_value = (.035, .017, .009, 1)
    cdk.inputs[0].default_value = 0.0
    pore = N.new('ShaderNodeTexVoronoi')                   # 細孔（參考圖方塊上一點點小洞）
    pore.inputs['Scale'].default_value = 150.0
    Lk.new(tc.outputs['Object'], pore.inputs['Vector'])
    pr_ = _ramp(N, .04, .14, (1, 1, 1, 1), (0, 0, 0, 1))
    Lk.new(pore.outputs['Distance'], pr_.inputs[0])
    cpm = N.new('ShaderNodeMath')
    cpm.operation = 'MAXIMUM'
    cpm.inputs[0].default_value = 0.0                      # 格子裂紋不壓暗（方塊上一格格像龜殼）；縫裡的菌絲還是用它
    cpw = N.new('ShaderNodeMath')
    cpw.operation = 'MULTIPLY'
    cpw.inputs[1].default_value = .40                     # 細孔淡淡的（.85 是滿滿的黑點，像海綿蛋糕）
    pcl = N.new('ShaderNodeTexNoise')                      # 細孔成片：有的地方多、有的沒有
    pcl.inputs['Scale'].default_value = 5.0
    pcl.inputs['Detail'].default_value = 2
    Lk.new(tc.outputs['Object'], pcl.inputs['Vector'])
    pcr = _ramp(N, .45, .62, (0, 0, 0, 1), (1, 1, 1, 1))
    Lk.new(pcl.outputs['Fac'], pcr.inputs[0])
    pcm = N.new('ShaderNodeMath')
    pcm.operation = 'MULTIPLY'
    Lk.new(pr_.outputs[0], pcm.inputs[0])
    Lk.new(pcr.outputs[0], pcm.inputs[1])
    Lk.new(pcm.outputs[0], cpw.inputs[0])
    Lk.new(cpw.outputs[0], cpm.inputs[1])
    cpk = N.new('ShaderNodeMath')
    cpk.operation = 'MULTIPLY'
    cpk.inputs[1].default_value = 1.0                      # 方塊上的小裂只壓暗一點（太黑像一格格蛇皮）
    Lk.new(cpm.outputs[0], cpk.inputs[0])
    Lk.new(cpk.outputs[0], cdk.inputs[0])
    # 白色菌絲：(1) 縫裡一段段的白；(2) 一片片扇形（Voronoi 格子裡放射的細絲，邊緣散開）
    myn = N.new('ShaderNodeTexNoise')
    myn.inputs['Scale'].default_value = 2.6
    myn.inputs['Detail'].default_value = 4
    Lk.new(tc.outputs['Object'], myn.inputs['Vector'])
    myz = _ramp(N, .52, .62, (0, 0, 0, 1), (1, 1, 1, 1))     # 哪幾段縫裡有菌絲
    Lk.new(myn.outputs['Fac'], myz.inputs[0])
    myc = N.new('ShaderNodeMath')
    myc.operation = 'MULTIPLY'
    Lk.new(crack.outputs[0], myc.inputs[0])
    myc.inputs[1].default_value = 0.0                      # 縫裡不畫白線（方塊上變成一格格白網）；菌絲用 mycel_fans 的薄片
    fan_mp = N.new('ShaderNodeMapping')
    fan_mp.inputs['Scale'].default_value = (3.2, 4.5, 4.5)
    Lk.new(tc.outputs['Object'], fan_mp.inputs['Vector'])
    fv = N.new('ShaderNodeTexVoronoi')                     # 每格一個扇子：離格心越遠越淡
    fv.inputs['Randomness'].default_value = .9
    Lk.new(fan_mp.outputs[0], fv.inputs['Vector'])
    fsel = _ramp(N, .90, .95, (0, 0, 0, 1), (.6, .6, .6, 1))   # 一成不到的格子有一點淡淡的菌絲（主要的在 mycel_fans）
    Lk.new(fv.outputs['Color'], fsel.inputs[0])
    frad = _ramp(N, .05, .42, (1, 1, 1, 1), (0, 0, 0, 1))
    Lk.new(fv.outputs['Distance'], frad.inputs[0])
    fst = _streak(N, Lk, (40.0, 40.0, 40.0), 3)             # 細絲
    fsr = _ramp(N, .35, .65, (.35, .35, .35, 1), (1, 1, 1, 1))
    Lk.new(fst.outputs['Fac'], fsr.inputs[0])
    fa = N.new('ShaderNodeMath')
    fa.operation = 'MULTIPLY'
    Lk.new(fsel.outputs[0], fa.inputs[0])
    Lk.new(frad.outputs[0], fa.inputs[1])
    fb_ = N.new('ShaderNodeMath')
    fb_.operation = 'MULTIPLY'
    Lk.new(fa.outputs[0], fb_.inputs[0])
    Lk.new(fsr.outputs[0], fb_.inputs[1])
    mys = N.new('ShaderNodeMath')
    mys.operation = 'MAXIMUM'
    Lk.new(myc.outputs[0], mys.inputs[0])
    Lk.new(fb_.outputs[0], mys.inputs[1])
    myk = N.new('ShaderNodeMixRGB')
    Lk.new(mys.outputs[0], myk.inputs[0])
    Lk.new(cdk.outputs[0], myk.inputs[1])
    myk.inputs[2].default_value = (.62, .60, .54, 1)       # 線性色：sRGB 約 .81／.80／.76，灰白不是純白
    # 靠斷口的苔（DR05 的 EndMoss）
    at = N.new('ShaderNodeAttribute')
    at.attribute_name = 'EndMoss'
    nm = N.new('ShaderNodeTexNoise')
    nm.inputs['Scale'].default_value = 7
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
    bta = N.new('ShaderNodeAttribute')                     # 方塊每塊深淺（RotBlocks 的 BlkTone；別的件沒有＝0＝不變）
    bta.attribute_name = 'BlkTone'
    bt1 = N.new('ShaderNodeMath')
    bt1.operation = 'ADD'
    bt1.inputs[1].default_value = 1.0
    Lk.new(bta.outputs['Fac'], bt1.inputs[0])
    btm = N.new('ShaderNodeMixRGB')
    btm.blend_type = 'MULTIPLY'
    btm.inputs[0].default_value = 1.0
    Lk.new(myk.outputs[0], btm.inputs[1])
    Lk.new(bt1.outputs[0], btm.inputs[2])
    Lk.new(btm.outputs[0], mx.inputs[1])
    Lk.new(mc.outputs[0], mx.inputs[2])
    Lk.new(mx.outputs[0], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = .93
    # 凹凸：每塊中間鼓、縫深；菌絲稍微浮起
    hb = N.new('ShaderNodeMath')
    hb.operation = 'MULTIPLY_ADD'
    hb.inputs[1].default_value = -.012                    # 小方格裂紋只留一點（-.05 在方塊頂上是一層細裂的釉）
    Lk.new(crack.outputs[0], hb.inputs[0])
    hb.inputs[2].default_value = 0.0
    hm = N.new('ShaderNodeMath')
    hm.operation = 'MULTIPLY_ADD'
    hm.inputs[1].default_value = .25
    Lk.new(mys.outputs[0], hm.inputs[0])
    Lk.new(hb.outputs[0], hm.inputs[2])
    hf = N.new('ShaderNodeMath')
    hf.operation = 'MULTIPLY_ADD'
    hf.inputs[1].default_value = .55
    Lk.new(fib.outputs['Fac'], hf.inputs[0])
    Lk.new(hm.outputs[0], hf.inputs[2])
    hpo = N.new('ShaderNodeMath')                          # 細孔凹下去
    hpo.operation = 'MULTIPLY_ADD'
    hpo.inputs[1].default_value = -.45
    Lk.new(pcm.outputs[0], hpo.inputs[0])
    Lk.new(hf.outputs[0], hpo.inputs[2])
    bp = N.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 1.0
    bp.inputs['Distance'].default_value = .012
    Lk.new(hpo.outputs[0], bp.inputs['Height'])
    Lk.new(bp.outputs[0], b.inputs['Normal'])
    return m


def bark8_material():
    """外殼：剩下的樹皮（DR05 樹皮的副本）＋剝掉的地方換成褐腐方塊（Peel 屬性），用 Mix Shader 接。"""
    m = bpy.data.materials.get('DR08_Bark')
    if m:
        return m
    m = bark5_material().copy()
    m.name = 'DR08_Bark'
    N, Lk = m.node_tree.nodes, m.node_tree.links
    for n in N:                                            # 地衣：DR05 是 1 m 粗的樹，這裡 0.6–0.8 m：花小一半、顏色暗一點（太亮像貼紙）
        if n.type == 'TEX_VORONOI' and abs(n.inputs['Scale'].default_value - 4.5) < 1e-3:
            n.inputs['Scale'].default_value = 8.0
        if n.type == 'VALTORGB' and abs(n.color_ramp.elements[0].color[0] - .36) < 1e-3:
            n.color_ramp.elements[0].color = (.11, .15, .11, 1)          # 灰綠（太亮在太陽下像一塊白紙）
            n.color_ramp.elements[-1].color = (.22, .28, .22, 1)
        if n.type == 'VALTORGB' and abs(n.color_ramp.elements[0].position - .30) < 1e-3 and abs(n.color_ramp.elements[1].position - .315) < 1e-3:
            n.color_ramp.elements[0].position, n.color_ramp.elements[1].position = .16, .175      # 只挑一成半的格子
    # 苔的團粒（Voronoi 55）、苔色雜訊（Noise 6）原本沒接座標＝用 Generated（物件外框 0–1）：
    # 細長的倒木沿長被壓扁 5–10 倍，苔上是一條條橫的波紋。改接物件座標（公尺）。
    tco = N.new('ShaderNodeTexCoord')
    for n in N:
        if n.type in ('TEX_VORONOI', 'TEX_NOISE') and not n.inputs['Vector'].links:
            Lk.new(tco.outputs['Object'], n.inputs['Vector'])
        if n.type == 'TEX_VORONOI' and abs(n.inputs['Scale'].default_value - 55.0) < 1e-3:
            n.inputs['Scale'].default_value = 150.0             # 1 cm 的苔粒（55 在細樹幹上像一顆顆石頭）
        if n.type == 'VALTORGB' and abs(n.color_ramp.elements[0].color[0] - .046) < 1e-3 and abs(n.color_ramp.elements[1].color[0] - .165) < 1e-3:
            n.color_ramp.elements[0].color = (.013, .020, .006, 1)          # 苔：深橄欖到橄欖綠（.15 的黃綠在引擎裡像塑膠布）
            n.color_ramp.elements[1].color = (.085, .092, .024, 1)
            n.color_ramp.elements[0].position, n.color_ramp.elements[1].position = .30, .70
        if n.type == 'BUMP' and abs(n.inputs['Distance'].default_value - .02) < 1e-4:
            n.inputs['Distance'].default_value = .005
            n.inputs['Strength'].default_value = .75
        if n.type == 'VALTORGB' and abs(n.color_ramp.elements[-1].color[0] - .45) < 1e-3 and abs(n.color_ramp.elements[-1].position - .45) < 1e-3:
            n.color_ramp.elements[-1].color = (.55, .60, .50, 1)     # 苔粒之間的縫
    # 地衣只長在樹皮上，不長在苔上（苔上一塊塊半透明的灰藍像水漬）
    lcol = next(n for n in N if n.type == 'VALTORGB' and abs(n.color_ramp.elements[0].color[0] - .11) < 1e-3)
    lmx = next(l.to_node for l in lcol.outputs[0].links if l.to_node.type == 'MIX_RGB')
    if lmx.inputs[0].links:
        msk_src = lmx.inputs[0].links[0].from_socket
        sepm = next(n for n in N if n.type == 'SEPARATE_COLOR' and n.inputs[0].links and n.inputs[0].links[0].from_node.type == 'VERTEX_COLOR')
        mrm = next(l.to_node for l in sepm.outputs[0].links if l.to_node.type == 'VALTORGB')
        nm_ = N.new('ShaderNodeMath')
        nm_.operation = 'SUBTRACT'
        nm_.inputs[0].default_value = 1.0
        Lk.new(mrm.outputs[0], nm_.inputs[1])
        mm_ = N.new('ShaderNodeMath')
        mm_.operation = 'MULTIPLY'
        Lk.new(msk_src, mm_.inputs[0])
        Lk.new(nm_.outputs[0], mm_.inputs[1])
        Lk.new(mm_.outputs[0], lmx.inputs[0])
        if lmx.inputs[1].links:
            tint = N.new('ShaderNodeMixRGB')
            tint.blend_type = 'MULTIPLY'
            tint.inputs[2].default_value = (.74, .52, .36, 1)          # 灰褐 → 暗暖褐（參考圖樹皮是暖褐的纖維；淺米色一層層在左端像頁岩）
            tf = N.new('ShaderNodeMath')
            tf.operation = 'MULTIPLY'
            tf.inputs[1].default_value = 1.0
            Lk.new(nm_.outputs[0], tf.inputs[0])
            Lk.new(tf.outputs[0], tint.inputs[0])
            Lk.new(lmx.inputs[1].links[0].from_socket, tint.inputs[1])
            Lk.new(tint.outputs[0], lmx.inputs[1])
    # 苔上不要透出樹皮掃描的法線（細樹幹上看起來是一條條沿長的大波浪）：法線強度乘 (1 − 苔遮罩)
    nmap = next(n for n in N if n.type == 'NORMAL_MAP')
    sepc = next(n for n in N if n.type == 'SEPARATE_COLOR' and n.inputs[0].links and n.inputs[0].links[0].from_node.type == 'VERTEX_COLOR')
    mrr = next(l.to_node for l in sepc.outputs[0].links if l.to_node.type == 'VALTORGB')
    inv = N.new('ShaderNodeMath')
    inv.operation = 'MULTIPLY_ADD'
    inv.inputs[1].default_value = -1.4
    inv.inputs[2].default_value = 1.5
    Lk.new(mrr.outputs[0], inv.inputs[0])
    Lk.new(inv.outputs[0], nmap.inputs['Strength'])
    mramp = next(n for n in N if n.type == 'VALTORGB' and abs(n.color_ramp.elements[0].color[0] - .013) < 1e-4
                 and abs(n.color_ramp.elements[1].color[0] - .085) < 1e-4)
    cv = N.new('ShaderNodeTexNoise')
    cv.inputs['Scale'].default_value = 14.0
    cv.inputs['Detail'].default_value = 3
    cv.inputs['Roughness'].default_value = .55
    cvw = N.new('ShaderNodeTexNoise')                      # 苔墊邊緣不是直線
    cvw.inputs['Scale'].default_value = 9.0
    cvw.inputs['Detail'].default_value = 2
    Lk.new(tco.outputs['Object'], cvw.inputs['Vector'])
    cvm = N.new('ShaderNodeVectorMath')
    cvm.operation = 'MULTIPLY_ADD'
    cvm.inputs[1].default_value = (.05, .05, .05)
    Lk.new(cvw.outputs['Color'], cvm.inputs[0])
    Lk.new(tco.outputs['Object'], cvm.inputs[2])
    Lk.new(cvm.outputs[0], cv.inputs['Vector'])
    ce = _ramp(N, .36, .62, (.42, .45, .38, 1), (1, 1, 1, 1))
    Lk.new(cv.outputs['Fac'], ce.inputs[0])
    cn = N.new('ShaderNodeTexNoise')                       # 有的苔墊黃一點、有的暗一點
    cn.inputs['Scale'].default_value = 6.0
    cn.inputs['Detail'].default_value = 2
    Lk.new(tco.outputs['Object'], cn.inputs['Vector'])
    cnr = _ramp(N, .30, .70, (.66, .70, .58, 1), (1.22, 1.18, .95, 1))
    Lk.new(cn.outputs['Fac'], cnr.inputs[0])
    cm1 = N.new('ShaderNodeMixRGB')
    cm1.blend_type = 'MULTIPLY'
    cm1.inputs[0].default_value = 1.0
    Lk.new(ce.outputs[0], cm1.inputs[1])
    Lk.new(cnr.outputs[0], cm1.inputs[2])
    cm2 = N.new('ShaderNodeMixRGB')
    cm2.blend_type = 'MULTIPLY'
    cm2.inputs[0].default_value = 1.0
    tg = [l.to_socket for l in mramp.outputs[0].links]
    for l in list(mramp.outputs[0].links):
        Lk.remove(l)
    Lk.new(mramp.outputs[0], cm2.inputs[1])
    Lk.new(cm1.outputs[0], cm2.inputs[2])
    for so in tg:
        Lk.new(cm2.outputs[0], so)
    bsdf = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    cbp = N.new('ShaderNodeBump')                          # 苔墊的凹凸（只在苔上）
    cbp.inputs['Distance'].default_value = .014
    cbs = N.new('ShaderNodeMath')
    cbs.operation = 'MULTIPLY'
    cbs.inputs[1].default_value = .9
    Lk.new(mrr.outputs[0], cbs.inputs[0])
    Lk.new(cbs.outputs[0], cbp.inputs['Strength'])
    Lk.new(cv.outputs['Fac'], cbp.inputs['Height'])
    if bsdf.inputs['Normal'].links:
        Lk.new(bsdf.inputs['Normal'].links[0].from_socket, cbp.inputs['Normal'])
    Lk.new(cbp.outputs[0], bsdf.inputs['Normal'])
    print('moss cushions: relinked', len(tg))
    out = next(n for n in N if n.type == 'OUTPUT_MATERIAL')
    bark_sh = out.inputs['Surface'].links[0].from_socket
    rot = rot8_material()
    # 把褐腐材質的節點搬一份進來：直接複製節點樹太麻煩，改成群組
    grp = bpy.data.node_groups.get('DR08_RotGroup')
    if grp is None:
        grp = bpy.data.node_groups.new('DR08_RotGroup', 'ShaderNodeTree')
        grp.interface.new_socket('Shader', in_out='OUTPUT', socket_type='NodeSocketShader')
        gN, gL = grp.nodes, grp.links
        mp_ = {}
        for n in rot.node_tree.nodes:
            if n.type == 'OUTPUT_MATERIAL':
                continue
            c = gN.new(n.bl_idname)
            for attr in ('feature', 'distance', 'operation', 'blend_type', 'attribute_name', 'data_type', 'interpolation_type'):
                if hasattr(n, attr):
                    try:
                        setattr(c, attr, getattr(n, attr))
                    except (AttributeError, TypeError):
                        pass
            if n.type == 'VALTORGB':
                el = c.color_ramp.elements
                src = n.color_ramp.elements
                while len(el) < len(src):
                    el.new(.5)
                for e, s in zip(el, src):
                    e.position, e.color = s.position, s.color[:]
            for i, s in enumerate(n.inputs):
                if hasattr(s, 'default_value') and i < len(c.inputs):
                    try:
                        c.inputs[i].default_value = s.default_value
                    except (AttributeError, TypeError, ValueError):
                        pass
            mp_[n.name] = c
        for l in rot.node_tree.links:
            if l.to_node.type == 'OUTPUT_MATERIAL':
                continue
            a = mp_[l.from_node.name].outputs[list(l.from_node.outputs).index(l.from_socket)]
            bb = mp_[l.to_node.name].inputs[list(l.to_node.inputs).index(l.to_socket)]
            gL.new(a, bb)
        go = gN.new('NodeGroupOutput')
        bs = next(c for n, c in mp_.items() if c.type == 'BSDF_PRINCIPLED')
        gL.new(bs.outputs['BSDF'], go.inputs[0])
    gn = N.new('ShaderNodeGroup')
    gn.node_tree = grp
    pa = N.new('ShaderNodeAttribute')
    pa.attribute_name = 'Peel'
    pr = _ramp(N, .45, .60, (0, 0, 0, 1), (1, 1, 1, 1))
    Lk.new(pa.outputs['Fac'], pr.inputs[0])
    ms = N.new('ShaderNodeMixShader')
    Lk.new(pr.outputs[0], ms.inputs[0])
    Lk.new(bark_sh, ms.inputs[1])
    dk = N.new('ShaderNodeBsdfPrincipled')                 # 方塊底下的木頭面（縫、掉了的洞）：暗紅褐
    dk.inputs['Base Color'].default_value = (.030, .012, .006, 1)
    dk.inputs['Roughness'].default_value = .95
    mdk = N.new('ShaderNodeMixShader')
    mdk.inputs[0].default_value = .88                    # 方塊縫底幾乎黑（.60 時是一條條平的褐色＝水泥縫）
    Lk.new(gn.outputs[0], mdk.inputs[1])
    Lk.new(dk.outputs[0], mdk.inputs[2])
    Lk.new(mdk.outputs[0], ms.inputs[2])
    Lk.new(ms.outputs[0], out.inputs['Surface'])
    return m


# ---------------- 件 ----------------
DL = 0                                                     # 遊戲模型 LOD 級（0／1／2）：菌、木條、碎屑跟著減


def debris8(V, coll, R, mat, n, sub=1):
    """地上的碎屑：兩側、兩頭、裂開處底下，一塊塊小方塊（褐腐碎成方塊）和壓扁的木粉堆。"""
    bm = bmesh.new()
    L, Rt = V['L'], V['R']
    for k in range(n):
        u = R.random()
        if u < .45:                                        # 兩頭
            x = R.choice((R.uniform(-.25, .12), R.uniform(L - .12, L + .30)))
            y = axis_y(V, min(max(x, 0), L)) + R.gauss(0, Rt * .8)
        else:                                              # 兩側
            x = R.uniform(.05, .95) * L
            sg = R.choice((-1, 1))
            y = axis_y(V, x) + sg * (out_r(V, x) * .85 + abs(R.gauss(0, Rt * .45)))
        s = R.uniform(.016, .042) * (1.4 if R.random() < .12 else 1.0)
        tmp = bmesh.new()
        kind_ = R.random()
        if kind_ < .45:                                    # 剝落的木片／樹皮片：扁、邊緣不規則（第七輪是小方塊，像積木，團隊規則不准）
            bmesh.ops.create_icosphere(tmp, subdivisions=1 + sub, radius=1.0)
            sx, sy, sz = R.uniform(1.3, 2.1), R.uniform(.8, 1.2), R.uniform(.22, .34)
        elif kind_ < .82:                                  # 崩下來的褐腐木塊（參考圖腳邊一堆紅褐碎塊）：圓鈍、不規則，不是方塊
            s *= R.uniform(1.5, 2.2)
            bmesh.ops.create_icosphere(tmp, subdivisions=1 + max(sub, 1 if (DL <= 1 and s > .05) else 0), radius=1.0)     # 大塊的多一級細分，近看不會一面面
            sx, sy, sz = R.uniform(1.0, 1.5), R.uniform(.8, 1.1), R.uniform(.55, .80)
        else:                                              # 木粉堆
            bmesh.ops.create_icosphere(tmp, subdivisions=1 + sub, radius=1.0)
            sx, sy, sz = R.uniform(1.6, 2.6), R.uniform(1.2, 2.0), R.uniform(.25, .4)
        rz = R.uniform(0, math.pi)
        rx, ry = R.uniform(-.4, .4), R.uniform(-.4, .4)
        from mathutils import Euler
        rot = Euler((rx, ry, rz)).to_matrix()
        for v in tmp.verts:
            d = v.co.copy()
            q = d * (1 + .24 * fb(d * 2.3 + Vector((k, 0, 0)), 1.0, 2))
            q = Vector((q.x * s * sx, q.y * s * sy, q.z * s * sz))
            v.co = rot @ q + Vector((x, y, s * sz * .55 - .01))
        me_ = bpy.data.meshes.new('tmp')
        tmp.to_mesh(me_)
        tmp.free()
        bm.from_mesh(me_)
        bpy.data.meshes.remove(me_)
    me = bpy.data.meshes.new('DR08_Debris')
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:                                  # 平滑著色：崩落木塊是圓鈍的，不是多面體
        p.use_smooth = True
    at = me.attributes.new('EndMoss', 'FLOAT', 'POINT')
    at.data.foreach_set('value', np.zeros(len(me.vertices), np.float32))
    me.materials.append(mat)
    return _obj('Debris', me, coll)


def bracket_material():
    """層狀菌：頂點色 Tint × 細雜訊；不要次表面散射（共用的小蕈材質有，整片泛白），粗糙一點、像乾的木質菌。"""
    m = bpy.data.materials.get('DR08_Bracket')
    if m:
        return m
    m = core_plants.mushroom_material()
    m.name = 'DR08_Bracket'
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Roughness'].default_value = .62
    try:
        b.inputs['Subsurface Weight'].default_value = 0.0
    except Exception:
        pass
    return m


BRACKETS = False                  # 11/23 使用者：「菇不要再黏在木頭上了」→ 樹幹側面不長層狀菌，改成腳邊、洞口的蕈叢（V['fungi'] 位置照用）
BR_ANCH = []                      # 層狀菌長出來的點（點, 半徑）：方塊褐腐不長在菌底下


def brackets8(V, coll, R, rings, mat, lowpoly=False, trunk=None):
    """層狀菌（參考圖細節圖中間那格）：一叢 6–8 片，從樹幹側面長出來、兩欄錯開像瓦片一層層疊（上面的蓋住下面的後半），
    最低一片離地至少 9 cm。每片是厚的扇形菌蓋：根部厚 2–3 cm、往外收薄、邊緣一圈圓的厚唇（不是零厚度的紙片）；
    平面像腎形、有兩三個淺裂瓣，邊緣上下波浪；上面一圈圈細的環紋起伏，深褐／鏽褐／黃褐環帶、最外一圈奶油色；下面淺黃褐。
    菌蓋一律水平長（向地性），根部埋進樹幹 1.5 cm。"""
    from mathutils.bvhtree import BVHTree
    BR_ANCH.clear()
    tb = None
    if trunk is not None:
        mw = trunk.matrix_world
        tb = BVHTree.FromPolygons([mw @ v.co for v in trunk.data.vertices], [tuple(p.vertices) for p in trunk.data.polygons])
    V_, F_, C_, BU, BV, BA, BR = [], [], [], [], [], [], []
    na, nr = ((14, 4), (10, 3), (5, 1))[DL] if lowpoly else (28, 15)
    pal = ((.028, .012, .005), (.10, .036, .011), (.19, .10, .040), (.050, .021, .007), (.15, .072, .022))
    cream, under = (.22, .16, .088), (.18, .13, .072)
    Rw = V['R']
    for ci, (f, ang, cnt) in enumerate(V['fungi']):
        s0 = f * V['L']
        ydir = 1.0 if ang > 0 else -1.0                      # 正角往 -Y 側長（從 -Y 外面往 +Y 打到樹幹）
        n = max(3, cnt)                                      # 一叢 3–5 片（多了就疊成一根柱子）
        side_l = R.choice((-1, 1))
        shelves = []
        for q in range(n):
            col_ = q % 2
            lvl = q // 2
            u = (lvl + .5 * col_ + R.uniform(-.12, .12)) / max(1, (n - 1) / 2)
            w = Rw * R.uniform(.74, .92) * (1.0 - .30 * u) * (.75 if q == n - 1 else 1.0)      # 參考圖的層狀菌一片比人的手臂還寬
            sx = s0 + side_l * (col_ - .5) * Rw * .50 + side_l * (u - .5) * Rw * .55 + R.uniform(-.05, .05) * Rw      # 沿樹幹錯開，不是一欄往上疊
            shelves.append(dict(u=u, w=w, sx=sx, dep=w * R.uniform(.72, .88), th=w * R.uniform(.13, .17),
                                lip=w * R.uniform(.045, .060), droop=R.uniform(.25, .55), yaw=R.uniform(-.22, .22),
                                ph=R.uniform(0, 6.28), nl=R.choice((2, 3, 3, 4)), nw=R.uniform(5.0, 8.0),
                                nb=R.uniform(10.0, 13.0), wa=R.uniform(.035, .060), cs=R.random()))
        # 這一叢在樹幹側面能放的高度：地面上 9 cm 到頂上往下 5 cm
        zt = axis_z(V, s0) + out_r(V, s0) * flx(V, s0) * .80
        if tb is not None:
            h = tb.ray_cast(Vector((s0, axis_y(V, s0), 3.0)), Vector((0, 0, -1)), 5)
            if h[0] is not None:
                zt = h[0].z
        z0 = max(.09, axis_z(V, s0) - .10 * Rw)              # 從軸心高度（樹幹最寬處）往上長：肚子下面樹幹往內收，菌長在那裡會懸空
        z1 = max(z0 + .10, min(zt - .06, z0 + Rw * .78))                  # 擠成一叢（不是一片片散到頂上）
        for sh in shelves:
            z = z0 + (z1 - z0) * min(1.0, max(0.0, sh['u'])) * .92
            o = Vector((sh['sx'], axis_y(V, sh['sx']) - ydir * 3.0, z))
            if tb is not None:
                hit = tb.ray_cast(o, Vector((0, ydir, 0)), 6)
                if hit[0] is None:
                    continue
                P, nrm = hit[0], hit[1]
            else:
                c, nrm, _, r = surf(rings, sh['sx'], ang)
                P = c + nrm * r * .90
            out = Vector((nrm.x, nrm.y, 0))
            if out.length < .3:
                continue
            out.normalize()
            hz = Vector((0, 0, 1))
            along = hz.cross(out).normalized()
            cy, sy = math.cos(sh['yaw']), math.sin(sh['yaw'])
            along, out = along * cy + out * sy, out * cy - along * sy
            P = P - out * .015
            BR_ANCH.append((P.copy(), sh['w'] * .55 + .02))
            w, dep, th, lip = sh['w'], sh['dep'], sh['th'], sh['lip']
            # 剖面：上面從根到邊（rho 0→1），圓唇，下面從邊回到根
            prof = [(i / nr, 'T') for i in range(nr + 1)] + [(1.0 + lip * .9 / dep, 'E')] + [(i / nr, 'B') for i in range(nr, -1, -1)]
            base = len(V_)
            shelf_v = R.random()
            for (rho, kind) in prof:
                for j in range(na + 1):
                    t = -.08 * math.pi + 1.16 * math.pi * j / na
                    lob = 1 + .10 * math.sin(sh['nl'] * t + sh['ph']) + .04 * math.sin(11 * t + sh['ph'] * 2)
                    ext = min(1.0, max(0.0, math.sin(t) + .25))         # 兩側根部收回到樹幹上
                    x = math.cos(t) * w * .5 * (.55 + .45 * min(rho, 1.0)) * lob      # 根部是一條寬的附著線（原本 rho = 0 縮成一點，看起來是靠在樹幹上）
                    y = (math.sin(t) * rho * lob) * dep * ext - .010 * (1 - min(rho, 1.0))
                    rc = min(rho, 1.0)
                    wave = sh['wa'] * w * rc ** 3 * math.sin(sh['nw'] * t + sh['ph'])
                    sag = -sh['droop'] * th * rc ** 2
                    if kind == 'T':
                        zz = lip * .5 + th * (1 - rho ** 1.7) * .85 + .11 * th * math.sin(rho * sh['nb'] * math.pi * 2) * rho
                    elif kind == 'B':
                        zz = -lip * .5 - th * .30 * (1 - rho) ** 2
                    else:
                        zz = 0.0
                    Pv = P + along * x + out * y + hz * (zz + sag + wave)
                    if tb is not None and rc < .45:                    # 根部那一圈沿著 out 貼到樹幹表面（樹幹是彎的，直線根部兩端會離開樹幹）
                        hh_ = tb.ray_cast(Pv + out * .30, -out, .9)
                        if hh_[0] is not None:
                            wgt = (1 - rc / .45) ** 1.5
                            Pv = Pv + out * (((hh_[0] - Pv).dot(out) - .012) * wgt)
                    V_.append(tuple(Pv))
                    BU.append(.78 * rho if kind == 'T' else (.84 if kind == 'E' else .90 + .10 * (1 - rho)))
                    BV.append(shelf_v)
                    BA.append(t if kind != 'B' else .5 * math.pi + .12 * (t - .5 * math.pi))   # 菌蓋圖（扇形）的角度、半徑：遊戲模型照這個貼手繪菌蓋；下面一律取邊緣的奶油色（照角度取會拉成條紋）
                    BR.append(rho * lob if kind == 'T' else (1.0 if kind == 'E' else .955))
                    if kind == 'T' and rho < .93:
                        bi = rho * sh['nb'] + .35 * math.sin(3 * t + sh['ph']) + sh['cs'] * 5
                        k0 = int(math.floor(bi)) % len(pal)
                        fr = bi - math.floor(bi)
                        c0, c1 = pal[k0], pal[(k0 + 1) % len(pal)]
                        m_ = max(0.0, (fr - .80) / .20)
                        cc = [c0[i_] + (c1[i_] - c0[i_]) * m_ for i_ in range(3)]
                        dk = .65 + .35 * min(1.0, rho / .35)              # 根部暗
                        cc = (cc[0] * dk, cc[1] * dk, cc[2] * dk, 1)
                    elif kind == 'B':
                        dk = .70 + .30 * rho
                        cc = (under[0] * dk, under[1] * dk, under[2] * dk, 1)
                    else:
                        cc = (*cream, 1)
                    C_.append(cc)
            row = na + 1
            for i in range(len(prof) - 1):
                for j in range(na):
                    a0 = base + i * row + j
                    F_.append((a0, a0 + 1, a0 + row + 1, a0 + row))          # 上表面法線朝上（反了的話引擎背面剔除後只看到下面那層）
    me = bpy.data.meshes.new('DR08_Brackets')
    me.from_pydata(V_, [], F_)
    ca = me.color_attributes.new('Tint', 'FLOAT_COLOR', 'POINT')
    ca.data.foreach_set('color', np.array(C_, np.float32).ravel())
    me.attributes.new('BrkU', 'FLOAT', 'POINT').data.foreach_set('value', np.array(BU, np.float32))      # 遊戲模型：指到圖集的環帶色條
    me.attributes.new('BrkV', 'FLOAT', 'POINT').data.foreach_set('value', np.array(BV, np.float32))
    me.attributes.new('BrkA', 'FLOAT', 'POINT').data.foreach_set('value', np.array(BA, np.float32))
    me.attributes.new('BrkR', 'FLOAT', 'POINT').data.foreach_set('value', np.array(BR, np.float32))
    for p in me.polygons:
        p.use_smooth = True
    me.validate()
    me.materials.append(mat)
    print('BRACKETS', len(BR_ANCH), 'shelves')
    return _obj('Brackets', me, coll)



def big_mush8(V, coll, R, mat, trunk, soil=None, lowpoly=False, solids=()):
    """參考圖（三分之二視角前排左那根、細節圖中間）的大香菇：每一朵都是自己從地上長出來的菌柄＋一頂波浪大菌傘，
    菌傘後緣只是「靠」在樹幹側面（留 5 mm，不插進木頭、不從樹皮長出來）。菌柄從地上斜斜往樹幹靠、中段往外微彎；
    一叢 3–5 朵沿樹幹排開、高低錯落，低的大、高的小。菌傘上面照手繪菌蓋圖（中心深褐、一圈圈環紋、外緣奶油色），
    下面、菌柄是奶油色。屬性 BrkA／BrkR 跟原本的層狀菌一樣，遊戲模型照現成規則貼圖。"""
    from mathutils.bvhtree import BVHTree
    VV, FF = [], []                                         # 樹幹＋斷口、木條、碎塊、土堆：菌傘、菌柄都不能卡進去
    for o in [trunk] + [o for o in solids if o is not trunk and o.type == 'MESH' and len(o.data.polygons)]:
        mw = o.matrix_world
        b0 = len(VV)
        VV += [mw @ v.co for v in o.data.vertices]
        FF += [tuple(b0 + i for i in p.vertices) for p in o.data.polygons]
    tb = BVHTree.FromPolygons(VV, FF)
    mw = trunk.matrix_world
    tt = BVHTree.FromPolygons([mw @ v.co for v in trunk.data.vertices], [tuple(p.vertices) for p in trunk.data.polygons])
    PLACED = []                                             # 已放的香菇：('cap', 中心, U, 半徑, 厚) / ('stem', 點, 半徑)
    sb = None
    if soil is not None:
        sw = soil.matrix_world
        sb = BVHTree.FromPolygons([sw @ v.co for v in soil.data.vertices], [tuple(p.vertices) for p in soil.data.polygons])
    na, nrT, nrB, ns, nseg = ((40, 4, 2, 8, 5), (20, 2, 1, 6, 4), (10, 1, 1, 4, 2))[DL] if lowpoly else (48, 9, 5, 14, 10)
    pal = ((.028, .012, .005), (.10, .036, .011), (.19, .10, .040), (.050, .021, .007), (.15, .072, .022))
    cream, under = (.22, .16, .088), (.18, .13, .072)
    Z = Vector((0, 0, 1))
    Rw, L = V['R'], V['L']
    V_, F_, C_, BA, BR, FREF = [], [], [], [], [], []
    gap = .005

    def sdist(p):
        loc, nrm, idx, d = tb.find_nearest(p)
        return 9.0 if loc is None else (p - loc).dot(nrm)

    def ground(x, y, ztop):
        z = 0.0
        if sb is not None:
            h = sb.ray_cast(Vector((x, y, ztop)), Vector((0, 0, -1)), ztop + 1)
            if h[0] is not None:
                z = max(z, h[0].z)
        return z

    nmush = 0
    for ci, (f, ang, cnt) in enumerate(V['fungi']):
        s0 = f * L
        sd = -1.0 if ang > 0 else 1.0                       # 正角＝-Y 側（正面）
        n = min(5, max(4, cnt + 1))                         # 一叢 4–6 朵疊在一起（參考圖：一層層疊、高低錯落，不是一朵朵分開站）
        z_lo = .10
        z_hi = max(z_lo + .18, axis_z(V, s0) + .15 * Rw)       # 菌柄短、菌傘大（參考圖），不是細長竹竿
        order = list(range(n))
        R.shuffle(order)
        shrooms = []
        for q in range(n):
            u = (order[q] + R.uniform(-.15, .15)) / max(1, n - 1)
            u = min(1.0, max(0.0, u))
            rc = Rw * (.42 if order[q] == 0 else R.uniform(.26, .34)) * (1.0 - .22 * u)
            sx = s0 + (q - (n - 1) / 2) * Rw * .24 + R.uniform(-.04, .04)
            shrooms.append((rc, sx, z_lo + rc * .30 + (z_hi - z_lo) * u, u))
        if lowpoly and DL == 2:
            shrooms = sorted(shrooms, key=lambda s: -s[0])[:1]
        for rc, sx0, zc, u in shrooms:
            for cand in (0.0, .4, -.4, .8, -.8, 1.2, -1.2):          # 碰到同叢別朵：沿樹幹挪開再試，都不行就不放
                sx = min(max(sx0 + cand * rc * 1.6, .12 * L), .88 * L)
                h = tt.ray_cast(Vector((sx, axis_y(V, sx) + sd * 3.0, zc)), Vector((0, -sd, 0)), 6)
                if h[0] is None:
                    continue
                P, nrm = h[0], h[1]
                out = Vector((nrm.x, nrm.y, 0))
                out = out.normalized() if out.length > .3 else Vector((0, sd, 0))
                if abs(out.y) < .75:                         # 打到樹幹尾端收口：菌傘會朝外飄出去、離樹幹很遠
                    continue
                tilt = R.uniform(.16, .36)                       # 菌傘往外仰（後緣靠在樹幹上），再往左右歪一點
                roll = R.uniform(-.18, .18)
                al = Z.cross(out).normalized()
                U = (Z * math.cos(tilt) + out * math.sin(tilt)).normalized()
                U = (U * math.cos(roll) + al * math.sin(roll)).normalized()
                e1 = U.cross(out).normalized()
                e2 = e1.cross(U).normalized()                    # 大致朝外
                th = rc * R.uniform(.28, .34)                    # 圓頂高一點（不是平桌面）
                lip = rc * .07
                droop = R.uniform(.70, .95)                      # 外圈往下垂成傘
                nl, ph, ph2 = R.choice((3, 4, 5)), R.uniform(0, 6.28), R.uniform(0, 6.28)
                nw, wa = R.choice((3, 4, 5)), R.uniform(.12, .17)     # 邊緣大波浪（參考圖菌傘像荷葉邊，不是平的圓盤）
                nb, cs = R.uniform(9.0, 12.0), R.random()
                rs = rc * R.uniform(.13, .16)

                def rad(t):                                  # 圓順的幾個大瓣（不是一段段折角）
                    return rc * (1 + .07 * math.sin(nl * t + ph) + .015 * math.sin((nl + 2) * t + ph2))

                def wav(t):
                    return wa * rc * math.sin(nw * t + ph)

                prof = [(i / nrT, 'T') for i in range(nrT + 1)] + [(1.0 + lip * .8 / rc, 'E')] + [(1.0 - .75 * i / nrB, 'B') for i in range(nrB + 1)] + [(0.0, 'B')]
                loc = []
                for rho, kind in prof:
                    ring = []
                    for j in range(na):
                        t = 2 * math.pi * j / na
                        rr = min(rho, 1.0)
                        r_ = rho * rad(t)
                        if kind == 'T':
                            z = lip * .5 + th * (1 - rr ** 2) * .9 + .06 * th * math.sin(rr * nb * math.pi) * rr
                        elif kind == 'B':
                            z = -lip * .5 + th * .22 * (1 - rr)
                        else:
                            z = 0.0
                        z += wav(t) * rr ** 3 - droop * th * rr ** 2
                        ring.append((r_ * math.cos(t), r_ * math.sin(t), z, t, rho, kind))
                    loc.append(ring)
                C = P + out * (rc * .55)
                worst = 9.0
                for it in range(14):                             # 推到菌傘每一點都在樹幹外面 5 mm（只靠著，不插進去）
                    worst = 9.0
                    for ring in loc:                      # 菌傘上下每一點
                        for (lx, ly, lz, *_r) in ring:
                            worst = min(worst, sdist(C + e1 * lx + e2 * ly + U * lz))
                    if worst >= gap:
                        break
                    C = C + out * (gap - worst + .002)
                if worst > gap + .03:                            # 第一次就沒碰到：往樹幹靠回去
                    C = C - out * (worst - gap)
                worst = min(sdist(C + e1 * lx + e2 * ly + U * lz) for ring in loc for (lx, ly, lz, *_r) in ring)
                if worst < gap - .002 or worst > .04:            # 推不出來（卡進去）或靠不到樹幹（離太遠、不是靠著）：換位置
                    continue
                # 菌柄：地上 → 菌傘下面中心，往樹幹斜靠、中段往外彎
                T_ = C + U * (th * .22 - lip * .5 - .01)
                dout = R.uniform(.01, .04) + rc * .08               # 11/24 使用者「根也太斜了」：菌柄幾乎直立，只微微往樹幹靠
                jx = R.uniform(-.03, .03)
                B = Vector((T_.x, T_.y, 0)) + out * dout
                for it in range(10):
                    B = Vector((T_.x + jx, T_.y, 0)) + out * dout
                    hz = tt.ray_cast(Vector((B.x, B.y, 3.0)), Vector((0, 0, -1)), 4)
                    if hz[0] is None or hz[0].z < .03:
                        break
                    dout += .03
                gz = ground(B.x, B.y, T_.z)
                B.z = gz - .03
                bow = R.uniform(.015, .035)
                M = (B + T_) * .5 + out * bow
                for it in range(8):                              # 菌柄也不能插進樹幹
                    worst = 9.0
                    for k in range(nseg + 1):
                        s = k / nseg
                        c = B * (1 - s) ** 2 + M * 2 * s * (1 - s) + T_ * s * s
                        if c.z > gz + .02 and s < .85:
                            worst = min(worst, sdist(c) - rs * 1.2)
                    if worst >= gap:
                        break
                    B = B + out * (gap - worst + .01)
                    M = M + out * (gap - worst + .01)
                    gz = ground(B.x, B.y, T_.z)
                    B.z = gz - .03
                # 跟同一叢已放的香菇互相不能穿：新菌柄不穿過舊菌傘、新菌傘不壓到舊菌柄、菌傘之間不疊進去
                stem_pts = []
                for k in range(nseg + 1):
                    s_ = k / nseg
                    stem_pts.append(B * (1 - s_) ** 2 + M * 2 * s_ * (1 - s_) + T_ * s_ * s_)

                def in_cap(q, Cq, Uq, rq, tq, pad):
                    d = q - Cq
                    hgt = d.dot(Uq)
                    rr_ = (d - Uq * hgt).length
                    return rr_ < rq * 1.12 + pad and -tq - pad < hgt < tq * 1.3 + pad
                clash = False
                for it_ in PLACED:
                    if it_[0] == 'cap':
                        _, Cq, Uq, rq, tq = it_
                        if any(in_cap(q, Cq, Uq, rq, tq, rs + .01) for q in stem_pts[1:]):
                            clash = True
                        if (C - Cq).length < (rc + rq) * 1.05 and abs((C - Cq).dot(Z)) < (th + tq) * 1.4 + .06:
                            clash = True
                    else:
                        _, q, rq = it_
                        if in_cap(q, C, U, rc, th, rq + .01):
                            clash = True
                if clash:
                    continue
                for q in stem_pts:
                    PLACED.append(('stem', q.copy(), rs * 1.3))
                PLACED.append(('cap', C.copy(), U.copy(), rc, th))
                # 菌傘（頂上、下面中心各一點）
                ridx = []
                for ring in loc:
                    ids = []
                    for j, (lx, ly, lz, t, rho, kind) in enumerate(ring):
                        if rho == 0.0 and j > 0:
                            ids.append(ids[0])
                            continue
                        ids.append(len(V_))
                        V_.append(tuple(C + e1 * lx + e2 * ly + U * lz))
                        a_ = t if t <= math.pi else 2 * math.pi - t
                        BA.append(a_ if kind != 'B' else .5 * math.pi + .12 * (a_ - .5 * math.pi))
                        BR.append(min(rho, 1.0) * .97 if kind == 'T' else (1.0 if kind == 'E' else -.955))      # 負值＝菌傘下面、菌柄：遊戲模型直接取奶油色那圈
                        if kind == 'T' and rho < .93:
                            bi = rho * nb + .35 * math.sin(3 * t + ph) + cs * 5
                            k0 = int(math.floor(bi)) % len(pal)
                            fr = bi - math.floor(bi)
                            c0, c1 = pal[k0], pal[(k0 + 1) % len(pal)]
                            m_ = max(0.0, (fr - .80) / .20)
                            cc = [c0[i_] + (c1[i_] - c0[i_]) * m_ for i_ in range(3)]
                            dk = .65 + .35 * min(1.0, rho / .35)
                            C_.append((cc[0] * dk, cc[1] * dk, cc[2] * dk, 1))
                        elif kind == 'B':
                            C_.append((*under, 1))
                        else:
                            C_.append((*cream, 1))
                    ridx.append(ids)
                for i in range(len(loc) - 1):
                    A_, B_ = ridx[i], ridx[i + 1]
                    for j in range(na):
                        j1 = (j + 1) % na
                        if A_[0] == A_[1]:
                            F_.append((A_[0], B_[j1], B_[j]))
                        elif B_[0] == B_[1]:
                            F_.append((A_[j], A_[j1], B_[0]))
                        else:
                            F_.append((A_[j], A_[j1], B_[j1], B_[j]))
                        FREF.append(('c', C.copy(), U.copy()))
                sbase = len(V_)
                for k in range(nseg + 1):
                    s = k / nseg
                    c = B * (1 - s) ** 2 + M * 2 * s * (1 - s) + T_ * s * s
                    tg = (2 * (1 - s) * (M - B) + 2 * s * (T_ - M)).normalized()
                    a1 = tg.cross(out)
                    a1 = a1.normalized() if a1.length > 1e-4 else e1
                    a2 = tg.cross(a1).normalized()
                    r_ = rs * (1.0 + .55 * max(0.0, 1 - s / .20) ** 2 - .12 * s + .45 * max(0.0, (s - .80) / .20) ** 2)   # 根部膨大、頂上往菌傘張開（不是一根竹籤）
                    for j in range(ns):
                        t = 2 * math.pi * j / ns
                        wob = 1 + .06 * math.sin(3 * t + ph + s * 4)
                        V_.append(tuple(c + (a1 * math.cos(t) + a2 * math.sin(t)) * r_ * wob))
                        BA.append(.5 * math.pi + .25 * math.cos(t))
                        BR.append(-(.86 + .095 * min(1.0, s / .55)))      # 菌柄根部沾土偏黃褐、往上淡成奶油色（不是一根白棍）
                        C_.append((cream[0] * (.75 + .25 * s), cream[1] * (.75 + .25 * s), cream[2] * (.75 + .25 * s), 1))
                for k in range(nseg):
                    sm = (k + .5) / nseg
                    cA = B * (1 - sm) ** 2 + M * 2 * sm * (1 - sm) + T_ * sm * sm
                    for j in range(ns):
                        a0, a1 = sbase + k * ns + j, sbase + k * ns + (j + 1) % ns
                        F_.append((a0, a1, a1 + ns, a0 + ns))
                        FREF.append(('s', cA.copy(), None))
                nmush += 1
                break
    me = bpy.data.meshes.new('DR08_BigMush')
    me.from_pydata(V_, [], F_)
    me.validate()
    flips = []
    for p, (kind, ref, U) in zip(me.polygons, FREF):
        d = p.center - ref
        if kind == 'c':
            d = d + U * (d.dot(U) * 2.0)               # 扁圓盤：上面朝上、下面朝下、邊朝外
        if p.normal.dot(d) < 0:
            flips.append(p.index)
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    for i in flips:
        bm.faces[i].normal_flip()
    bm.to_mesh(me)
    bm.free()
    ca = me.color_attributes.new('Tint', 'FLOAT_COLOR', 'POINT')
    ca.data.foreach_set('color', np.array(C_, np.float32).ravel())
    me.attributes.new('BrkA', 'FLOAT', 'POINT').data.foreach_set('value', np.array(BA, np.float32))
    me.attributes.new('BrkR', 'FLOAT', 'POINT').data.foreach_set('value', np.array(BR, np.float32))
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    print('BIGMUSH', nmush, 'mushrooms', len(F_), 'faces')
    return _obj('BracketsMush', me, coll)


BLK_LIST = []                     # 高模方塊（底中心、轉向、長、寬、高）：低模照這份做


def rot_blocks_low(V, coll, mat):
    """遊戲模型用的方塊褐腐：照高模那份每塊做一個沒倒角的方塊（12 面；貼著樹幹那面會被刪），烘焙對到高模的 RotBlocks。"""
    bm = bmesh.new()
    proto = bmesh.new()
    bmesh.ops.create_cube(proto, size=1.0)
    pv = [v.co.copy() for v in proto.verts]
    pf = [[v.index for v in f.verts] for f in proto.faces]
    proto.free()
    for base, M, sa, st, hh in BLK_LIST:
        vs = [bm.verts.new(base + M @ Vector((p_.x * sa * .96, p_.y * st * .96, p_.z * hh))) for p_ in pv]
        for f in pf:
            bm.faces.new([vs[i] for i in f])
    me = bpy.data.meshes.new('DR08_RotBlocksLow')
    bm.to_mesh(me)
    bm.free()
    me.attributes.new('EndMoss', 'FLOAT', 'POINT').data.foreach_set('value', np.zeros(len(me.vertices), np.float32))
    me.materials.append(mat)
    print('ROT_BLOCKS_LOW', len(BLK_LIST))
    return _obj('RotBlocks', me, coll)


def rot_blocks(V, coll, trunk, mat, R, cell=.075, lowpoly=False):
    """一碰會碎的方塊褐腐（參考圖側面整片是一塊塊方塊）：在剝掉樹皮的地方（Peel 屬性 > .55），
    沿長 x、繞圈弧長排成格子，每格一塊稍微歪的小方塊，從壓下去的木頭面凸出 2–4 cm；少幾塊（掉了）、幾塊往外翹（快掉了）。
    方塊邊倒一點角。高模烘進法線、顏色；遊戲模型不帶這些方塊。"""
    from mathutils.bvhtree import BVHTree
    from mathutils import Matrix
    me_t = trunk.data
    mw = trunk.matrix_world
    wv = [mw @ v.co for v in me_t.vertices]
    tb = BVHTree.FromPolygons(wv, [tuple(p.vertices) for p in me_t.polygons])
    pe = np.empty(len(me_t.vertices), np.float32)
    me_t.attributes['Peel'].data.foreach_get('value', pe)
    polys = me_t.polygons
    bm = bmesh.new()
    proto = bmesh.new()
    bmesh.ops.create_cube(proto, size=1.0)
    if not lowpoly:
        bmesh.ops.bevel(proto, geom=proto.edges[:] + proto.verts[:], offset=.12, segments=1, affect='EDGES', profile=.5)
    pv = [v.co.copy() for v in proto.verts]
    pf = [[v.index for v in f.verts] for f in proto.faces]
    proto.free()
    L = V['L']
    cell = cell * max(1.0, V['R'] / .40)                  # 1 m 粗的朽木一塊約 8–10 cm（參考圖），不是滿牆小磚
    nb = 0
    tl = bm.faces.layers.float.new('BlkTone')            # 每塊深淺（材質乘上去）：受潮、曬乾不一
    sc = max(1.0, V['R'] / .40)
    cx_ = cell * 1.10                                    # 接近方塊（褐腐＝方塊狀；扁長的一排排在引擎裡像亂石砌牆）
    dth0 = cell * .90 / out_r(V, L * .5)
    # 縱縫（順木紋）：一圈圈寬窄不一、沿長彎彎的；橫縫：先排一組全域的位置，每一圈只用六成 → 有的連過好幾圈、有的斷掉
    # （第五輪整齊格子在引擎裡像編織；第七輪一版每圈各切各的，錯縫變成砌磚牆）
    edges = [R.random() * dth0]
    while edges[-1] < edges[0] + 2 * math.pi - dth0 * .6:
        edges.append(edges[-1] + dth0 * R.uniform(.60, 1.50))
    edges[-1] = edges[0] + 2 * math.pi
    ne = len(edges) - 1
    wph = [R.uniform(0, 50) for _ in range(ne)]
    wph.append(wph[0])

    def th_e(k, x):
        return edges[k] + dth0 * .45 * fb(Vector((x * 2.0, wph[k], 1.3)), 1.0, 2)
    cuts = []
    xc = -R.uniform(0, cx_)
    while xc < L + cx_:
        cuts.append(xc)
        xc += cx_ * R.uniform(.50, .95)

    def S(x, th):
        o = Vector((x, axis_y(V, x), axis_z(V, x)))
        d = Vector((0, math.cos(th), math.sin(th) * flx(V, x))).normalized()
        return tb.ray_cast(o, d, 3 * out_r(V, x))
    M_ = 6
    for it in range(ne):
        xs = [(cuts[0], 0.0)]
        for c in cuts[1:]:
            if R.random() < .60 or c - xs[-1][0] > cx_ * 1.9:
                xs.append((c + R.uniform(-.06, .06) * cx_, R.uniform(-.20, .20) * cx_))     # 橫縫的位置、斜度
        for j in range(len(xs) - 1):
            (xa, sa_), (xb, sb_) = xs[j], xs[j + 1]
            xm = .5 * (xa + xb)
            if xm < .03 or xm > L - .03:
                continue
            gone = fb(Vector((xm * 1.6, edges[it] * 1.1, V['seed'] * .1)), 1.0, 2)
            if R.random() < .14 or gone > .22:                 # 掉了的格子：零星幾格＋成片崩掉露出底下更爛的木頭（崩多一點：整片完整的格子像砌石牆）
                continue
            thm = .5 * (th_e(it, xm) + th_e(it + 1, xm))
            hc = S(xm, thm)
            if hc[0] is None or hc[0].z < .025:
                continue
            pk = max(pe[i] for i in polys[hc[2]].vertices)
            if pk < .55 or any((hc[0] - bp).length < br for bp, br in BR_ANCH):      # 層狀菌底下不長方塊
                continue
            cor = [(xa - sa_ * .5, th_e(it, xa)), (xb - sb_ * .5, th_e(it, xb)), (xb + sb_ * .5, th_e(it + 1, xb)), (xa + sa_ * .5, th_e(it + 1, xa))]
            cxp = sum(c[0] for c in cor) / 4
            ctp = sum(c[1] for c in cor) / 4
            kx, kt = R.uniform(.78, .90), R.uniform(.78, .90)               # 縫 1–2.5 cm（引擎每公尺約 100 像素：1 cm 的縫看不到）
            cor = [(cxp + (c[0] - cxp) * kx + R.uniform(-.04, .04) * cx_, ctp + (c[1] - ctp) * kt + R.uniform(-.04, .04) * dth0) for c in cor]
            us, vs_ = [(0.0, 1.0)], [(0.0, 1.0)]
            if R.random() < .30:                                              # 再裂一刀（打斷一排排的縫）
                c_, g_ = R.uniform(.35, .65), R.uniform(.03, .06)
                us = [(0.0, c_ - g_), (c_ + g_, 1.0)]
            if R.random() < .22:
                c_, g_ = R.uniform(.35, .65), R.uniform(.03, .06)
                vs_ = [(0.0, c_ - g_), (c_ + g_, 1.0)]
            tone0 = R.uniform(-.40, .15)
            for (ua, ub) in us:
              for (va, vb) in vs_:
                lift = R.uniform(.004, .012) * sc                                 # 塊面高低差小：整片木頭裂開，不是一顆顆積木（邊緣要高過縫底的暗片）
                dome = R.uniform(.008, .022) * sc
                tilt = R.uniform(.010, .022) * sc * R.choice((-1, 1)) if R.random() < .06 else 0.0      # 少數幾塊翹起（快掉了）
                tone = tone0 + R.uniform(-.06, .06)
                if not rot_piece(bm, tl, S, cor, ua, ub, va, vb, lift, dome, tilt, tone, sc, M_, it, j, hc):
                    continue
                nb += 1
    me = bpy.data.meshes.new('DR08_RotBlocks')
    bm.to_mesh(me)
    bm.free()
    me.attributes.new('EndMoss', 'FLOAT', 'POINT').data.foreach_set('value', np.zeros(len(me.vertices), np.float32))
    me.materials.append(mat)
    print('ROT_BLOCKS', nb)
    return _obj('RotBlocks', me, coll)


def rot_piece(bm, tl, S, cor, ua, ub, va, vb, lift, dome, tilt, tone, sc, M_, it, j, hc):
    """一塊褐腐裂塊：四角（x, θ）圍出的四邊形裡 (ua..ub, va..vb) 那一塊，貼著樹幹表面，頂面微鼓，往下埋 3.5 cm。"""
    if True:
        if True:
            grid = []
            for iu in range(M_ + 1):
                u = ua + (ub - ua) * iu / M_
                row = []
                for iv in range(M_ + 1):
                    v = va + (vb - va) * iv / M_
                    if iu in (0, M_) or iv in (0, M_):                          # 邊緣崩碎：外圈的點在面上亂移（直邊＝磚）
                        u += .10 * (ub - ua) * fb(Vector((u * 7 + it * .37, v * 7 + j * .53, 4.1)), 1.0, 2)
                        v += .10 * (vb - va) * fb(Vector((u * 7 + 1.3, v * 7 + it * .11, 9.2)), 1.0, 2)
                    px = (1 - u) * (1 - v) * cor[0][0] + u * (1 - v) * cor[1][0] + u * v * cor[2][0] + (1 - u) * v * cor[3][0]
                    pt = (1 - u) * (1 - v) * cor[0][1] + u * (1 - v) * cor[1][1] + u * v * cor[2][1] + (1 - u) * v * cor[3][1]
                    u_, v_ = iu / M_, iv / M_
                    h = S(px, pt)
                    if h[0] is None:
                        break
                    nn = h[1].normalized()
                    e_ = max(abs(2 * u_ - 1), abs(2 * v_ - 1))
                    z = lift + dome * (1 - e_ ** 2.5) + tilt * (u_ - .5) + .005 * sc * fb(h[0] * 30 + Vector((it, j, 0)), 1.0, 1)
                    if e_ > .5:                                                     # 邊角往下崩（一塊塊高低不齊的缺角）
                        z -= .012 * sc * (e_ - .5) / .5 * (.6 + fb(h[0] * 14 + Vector((j, it, 3)), 1.0, 2))
                    row.append((h[0] + nn * z, h[0] - nn * .035 * sc))
                if len(row) < M_ + 1:
                    break
                grid.append(row)
            if len(grid) < M_ + 1:
                return False
            sk = []                                                            # 縫底的暗片：比這塊大一圈、貼著樹幹面，縫裡烘出來是深褐
            for (u_, v_) in ((ua - .10, va - .10), (ub + .10, va - .10), (ub + .10, vb + .10), (ua - .10, vb + .10)):
                px = (1 - u_) * (1 - v_) * cor[0][0] + u_ * (1 - v_) * cor[1][0] + u_ * v_ * cor[2][0] + (1 - u_) * v_ * cor[3][0]
                pt = (1 - u_) * (1 - v_) * cor[0][1] + u_ * (1 - v_) * cor[1][1] + u_ * v_ * cor[2][1] + (1 - u_) * v_ * cor[3][1]
                h = S(px, pt)
                if h[0] is None:
                    sk = None
                    break
                sk.append(bm.verts.new(h[0] + h[1].normalized() * .002 * sc))
            if sk:
                fs_ = bm.faces.new(sk)
                fs_[tl] = -.60 - .30 * abs(fb(hc[0] * 3.0, 1.0, 1))         # 縫底深淺不一（一樣黑像水泥縫）
                fs_.normal_update()
                if fs_.normal.dot(hc[1]) < 0:
                    fs_.normal_flip()
            top = [[bm.verts.new(q[0]) for q in row] for row in grid]
            bot = [[bm.verts.new(q[1]) for q in row] for row in grid]
            fl, ft = [], []
            for iu in range(M_):
                for iv in range(M_):
                    f = bm.faces.new((top[iu][iv], top[iu + 1][iv], top[iu + 1][iv + 1], top[iu][iv + 1]))
                    f.smooth = True
                    ft.append(f)
            ring = [(i, 0) for i in range(M_)] + [(M_, i) for i in range(M_)] + [(M_ - i, M_) for i in range(M_)] + [(0, M_ - i) for i in range(M_)]
            for k in range(len(ring)):
                (u1, v1), (u2, v2) = ring[k], ring[(k + 1) % len(ring)]
                fl.append(bm.faces.new((top[u1][v1], bot[u1][v1], bot[u2][v2], top[u2][v2])))
            fl += ft
            for f in fl:
                f[tl] = tone
            bmesh.ops.recalc_face_normals(bm, faces=fl)
            ft[len(ft) // 2].normal_update()
            if ft[len(ft) // 2].normal.dot(hc[1]) < 0:
                bmesh.ops.reverse_faces(bm, faces=fl)
            BLK_LIST.append((hc[0].copy(), None, 0.0, 0.0, 0.0))
            return True


def mycel_material():
    """白色菌絲網：扇形薄片的 UV（u 0–1 繞扇子、v 0–1 從中心往外），放射的細絲＋一圈圈橫絲＋稀疏的地方透明。
    顏色灰白（線性 .50），細絲之間透明（Alpha），所以底下的方塊看得到。"""
    m = bpy.data.materials.get('DR08_Mycel')
    if m:
        return m
    m = bpy.data.materials.new('DR08_Mycel')
    m.use_nodes = True
    N, Lk = m.node_tree.nodes, m.node_tree.links
    b = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = (.50, .49, .45, 1)
    b.inputs['Roughness'].default_value = .75
    uv = N.new('ShaderNodeUVMap')
    uv.uv_map = 'UVMap'
    sp = N.new('ShaderNodeSeparateXYZ')
    Lk.new(uv.outputs[0], sp.inputs[0])
    wn = N.new('ShaderNodeTexNoise')                       # 絲有點彎
    wn.inputs['Scale'].default_value = 6.0
    wn.inputs['Detail'].default_value = 3
    Lk.new(uv.outputs[0], wn.inputs['Vector'])
    uu = N.new('ShaderNodeMath')
    uu.operation = 'MULTIPLY_ADD'
    uu.inputs[1].default_value = .09
    Lk.new(wn.outputs['Fac'], uu.inputs[0])
    Lk.new(sp.outputs['X'], uu.inputs[2])

    def lines(src, freq, width):
        mm = N.new('ShaderNodeMath')
        mm.operation = 'MULTIPLY'
        mm.inputs[1].default_value = freq
        Lk.new(src, mm.inputs[0])
        fr = N.new('ShaderNodeMath')
        fr.operation = 'PINGPONG'
        fr.inputs[1].default_value = .5
        Lk.new(mm.outputs[0], fr.inputs[0])
        r = _ramp(N, .0, width, (1, 1, 1, 1), (0, 0, 0, 1))
        Lk.new(fr.outputs[0], r.inputs[0])
        return r
    wn.inputs['Scale'].default_value = 3.5
    rad = lines(uu.outputs[0], 75.0, .10)                  # 放射的絲
    rv = N.new('ShaderNodeTexNoise')                       # 一束束：有的地方絲密、有的地方空
    rv.inputs['Scale'].default_value = 14.0
    rv.inputs['Detail'].default_value = 2
    Lk.new(uv.outputs[0], rv.inputs['Vector'])
    rvr = _ramp(N, .38, .62, (.15, .15, .15, 1), (1, 1, 1, 1))
    Lk.new(rv.outputs['Fac'], rvr.inputs[0])
    rad2 = N.new('ShaderNodeMath')
    rad2.operation = 'MULTIPLY'
    Lk.new(rad.outputs[0], rad2.inputs[0])
    Lk.new(rvr.outputs[0], rad2.inputs[1])
    rings = lines(sp.outputs['Y'], 6.0, .03)               # 一圈圈的橫絲
    rn = N.new('ShaderNodeTexNoise')                       # 橫絲斷斷續續
    rn.inputs['Scale'].default_value = 9.0
    Lk.new(uv.outputs[0], rn.inputs['Vector'])
    rnr = _ramp(N, .55, .62, (0, 0, 0, 1), (.7, .7, .7, 1))
    Lk.new(rn.outputs['Fac'], rnr.inputs[0])
    rk = N.new('ShaderNodeMath')
    rk.operation = 'MULTIPLY'
    Lk.new(rings.outputs[0], rk.inputs[0])
    Lk.new(rnr.outputs[0], rk.inputs[1])
    a1 = N.new('ShaderNodeMath')
    a1.operation = 'MAXIMUM'
    Lk.new(rad2.outputs[0], a1.inputs[0])
    Lk.new(rk.outputs[0], a1.inputs[1])
    fade = _ramp(N, .55, 1.0, (1, 1, 1, 1), (0, 0, 0, 1))  # 外緣散掉
    Lk.new(sp.outputs['Y'], fade.inputs[0])
    cen = _ramp(N, .0, .18, (.6, .6, .6, 1), (0, 0, 0, 1))  # 中心一團密的
    Lk.new(sp.outputs['Y'], cen.inputs[0])
    cl = N.new('ShaderNodeTexNoise')                       # 棉絮一樣的一團團（不是魚網）
    cl.inputs['Scale'].default_value = 7.0
    cl.inputs['Detail'].default_value = 6
    cl.inputs['Roughness'].default_value = .62
    Lk.new(uv.outputs[0], cl.inputs['Vector'])
    clr = _ramp(N, .44, .70, (0, 0, 0, 1), (.85, .85, .85, 1))
    Lk.new(cl.outputs['Fac'], clr.inputs[0])
    sm = N.new('ShaderNodeMath')                           # 絲只是讓棉絮有一條條放射的紋
    sm.operation = 'MULTIPLY_ADD'
    sm.inputs[1].default_value = .55
    sm.inputs[2].default_value = .45
    Lk.new(a1.outputs[0], sm.inputs[0])
    cm2 = N.new('ShaderNodeMath')
    cm2.operation = 'MULTIPLY'
    Lk.new(clr.outputs[0], cm2.inputs[0])
    Lk.new(sm.outputs[0], cm2.inputs[1])
    a2 = N.new('ShaderNodeMath')
    a2.operation = 'ADD'
    Lk.new(cm2.outputs[0], a2.inputs[0])
    Lk.new(cen.outputs[0], a2.inputs[1])
    a3 = N.new('ShaderNodeMath')
    a3.operation = 'MULTIPLY'
    a3.use_clamp = True
    Lk.new(a2.outputs[0], a3.inputs[0])
    Lk.new(fade.outputs[0], a3.inputs[1])
    Lk.new(a3.outputs[0], b.inputs['Alpha'])
    try:
        m.blend_method = 'HASHED'
    except Exception:
        pass
    return m


def mycel_fans(V, coll, trunk, R, n=None, blocks=None):
    """白色菌絲（參考圖近景：方塊之間一片片扇形、蛛網一樣的白絲）：每片是一張扇形薄片（12×7 格），
    每個點從外面往樹幹軸心打、貼到最外層（方塊頂或樹幹）再浮 4 mm，方塊之間的縫就像網一樣跨過去。網紋在 DR08_Mycel 材質。
    每片 10–24 cm，只長在剝皮露出方塊的地方、不長在朝下的面。"""
    from mathutils.bvhtree import BVHTree
    me_t = trunk.data
    wv = [trunk.matrix_world @ v.co for v in me_t.vertices]
    tb = BVHTree.FromPolygons(wv, [tuple(p.vertices) for p in me_t.polygons])
    sv, sf = list(wv), [tuple(p.vertices) for p in me_t.polygons]
    if blocks is not None:
        o_ = len(sv)
        sv += [blocks.matrix_world @ v.co for v in blocks.data.vertices]
        sf += [tuple(i + o_ for i in p.vertices) for p in blocks.data.polygons]
    sb = BVHTree.FromPolygons(sv, sf)

    def drape(q):
        ax = Vector((q.x, axis_y(V, q.x), axis_z(V, q.x)))
        d_ = q - ax
        d_.x = 0.0
        if d_.length < 1e-6:
            return q
        d_.normalize()
        h = sb.ray_cast(ax + d_ * 3 * V['R'], -d_, 3 * V['R'])
        return (h[0] + d_ * .004) if h[0] is not None else q
    pe = np.empty(len(me_t.vertices), np.float32)
    me_t.attributes['Peel'].data.foreach_get('value', pe)
    n = n or int(2 + 2.2 * V['L'])
    VV, FF, UU = [], [], []
    made = 0
    NA, NR = 12, 7
    for tries in range(n * 30):
        if made >= n:
            break
        x = R.uniform(.08, .92) * V['L']
        th = R.uniform(-1.1, 1.1) + (0 if R.random() < .5 else math.pi)
        o = Vector((x, axis_y(V, x), axis_z(V, x)))
        d = Vector((0, math.cos(th), math.sin(th) * flx(V, x))).normalized()
        hit = tb.ray_cast(o, d, 3 * V['R'])
        if hit[0] is None or hit[0].z < .06 or hit[1].z < -.3:
            continue
        if max(pe[i] for i in me_t.polygons[hit[2]].vertices) < .6:
            continue
        nrm = hit[1].normalized()
        a = Vector((1, 0, 0))
        a = (a - nrm * a.dot(nrm)).normalized()
        t = nrm.cross(a)
        c0 = hit[0]
        rad = R.uniform(.10, .24)
        dir0 = R.uniform(0, 2 * math.pi)
        spread = R.uniform(1.2, 2.4)
        base = len(VV)
        for i in range(NR + 1):
            v_ = i / NR
            for j in range(NA + 1):
                u_ = j / NA
                an = dir0 + spread * (u_ - .5)
                rr = rad * v_ * (1 + .12 * math.sin(an * 5 + made))
                q = c0 + (a * math.cos(an) + t * math.sin(an)) * rr
                VV.append(tuple(drape(q)))
                UU.append((u_ * spread / 1.8, v_))
        row = NA + 1
        for i in range(NR):
            for j in range(NA):
                a0 = base + i * row + j
                FF.append((a0, a0 + 1, a0 + row + 1, a0 + row))
        made += 1
    me = bpy.data.meshes.new('DR08_Mycel')
    me.from_pydata(VV, [], FF)
    uvl = me.uv_layers.new(name='UVMap')
    for lp in me.loops:
        uvl.data[lp.index].uv = UU[lp.vertex_index]
    me.attributes.new('EndMoss', 'FLOAT', 'POINT').data.foreach_set('value', np.zeros(len(me.vertices), np.float32))
    for p_ in me.polygons:
        p_.use_smooth = True
    me.materials.append(mycel_material())
    print('MYCEL_FANS', made)
    return _obj('Mycel', me, coll)


def splinter_material():
    """撕裂斷口的木刺：曬白的灰褐木頭，沿長細紋。"""
    m = bpy.data.materials.get('DR08_Splinter')
    if m:
        return m
    m = bpy.data.materials.new('DR08_Splinter')
    m.use_nodes = True
    N, Lk = m.node_tree.nodes, m.node_tree.links
    b = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    fib = _streak(N, Lk, (.8, 40.0, 40.0), 6)
    cr = _ramp(N, .25, .80, (.050, .034, .021, 1), (.15, .105, .066, 1))     # 暖褐（第一版 .21 在太陽下是米色，像紙）
    Lk.new(fib.outputs['Fac'], cr.inputs[0])
    Lk.new(cr.outputs[0], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = .9
    bp = N.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = .6
    bp.inputs['Distance'].default_value = .004
    Lk.new(fib.outputs['Fac'], bp.inputs['Height'])
    Lk.new(bp.outputs[0], b.inputs['Normal'])
    return m


def splinters(V, coll, R, e, outer_ring, inner_ring, axis_dir, mat, n=18, lowpoly=False):
    """撕裂的斷口（參考圖 B 的一頭）：一根根長短不齊、往外伸的淺色木刺，上半邊長、下半邊短；扁的楔形，末端尖、會分岔一點。"""
    ad = Vector(axis_dir).normalized()
    no = len(outer_ring)
    c = sum((Vector(p) for p in outer_ring), Vector()) / no
    bm = bmesh.new()
    sul = bm.verts.layers.float.new('ShardU')
    shl = bm.faces.layers.int.new('Shard')                 # 遊戲模型：太薄烘不準，改指到圖集最下面一條的木色漸層
    nseg = 3 if lowpoly else 5
    for q in range(n):
        th = R.gauss(math.pi / 2, .6) if R.random() < .85 else R.uniform(0.0, math.pi)      # 細刺夾在木條之間，多在上半圈
        t = (th / (2 * math.pi)) % 1.0
        i0 = int(t * no) % no
        po = Vector(outer_ring[i0])
        ni = len(inner_ring)
        pi = Vector(inner_ring[int(t * ni) % ni])
        base = po.lerp(pi, R.uniform(.05, .85)) - ad * R.uniform(.10, .20)
        rad = base - c
        rad -= ad * rad.dot(ad)
        if rad.length < 1e-6:
            continue
        rad.normalize()
        tan = ad.cross(rad).normalized()
        top = max(0.0, math.sin(th))
        ks = max(1.0, V['R'] / .36)
        ln = (R.uniform(.12, .32) + R.uniform(.05, .40) * top * R.random()) * ks * 1.15
        wd = R.uniform(.010, .030)                          # 細長纖維條，不是獠牙
        tk = R.uniform(.005, .011)
        pitch = R.uniform(.05, .30) * (1 if R.random() < .7 else -1)
        d = (ad * math.cos(pitch) + rad * math.sin(pitch)).normalized()
        sag = R.uniform(-.04, .02)
        rows = []
        for s_ in range(nseg + 1):
            u = s_ / nseg
            p = base + d * (ln * u) + Vector((0, 0, sag * u * u)) + tan * (.015 * math.sin(u * 5 + q))
            ww = wd * (1 - u) ** .8 + .002
            tt = tk * (1 - .7 * u) + .0015
            nr = d.cross(tan).normalized()
            ring = []
            for sx, sy in ((-1, 0), (-.5, 1), (.5, 1), (1, 0), (.5, -1), (-.5, -1)):
                vv = bm.verts.new(p + tan * ww * sx + nr * tt * sy)
                vv[sul] = u
                ring.append(vv)
            rows.append(ring)
        for s_ in range(nseg):
            for k in range(6):
                bm.faces.new((rows[s_][k], rows[s_][(k + 1) % 6], rows[s_ + 1][(k + 1) % 6], rows[s_ + 1][k]))[shl] = 1
        bm.faces.new(rows[0])[shl] = 1
        bm.faces.new(rows[-1])[shl] = 1
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(f'Splinter{e}')
    bm.to_mesh(me)
    bm.free()
    me.attributes.new('EndMoss', 'FLOAT', 'POINT').data.foreach_set('value', np.zeros(len(me.vertices), np.float32))
    for p in me.polygons:
        p.use_smooth = False
    me.materials.append(mat)
    return _obj(f'Splinter{e}', me, coll)


def slabs8(V, coll, R, e, outer_ring, inner_ring, axis_dir, mat, n=11, lowpoly=False):
    """撕裂端的寬木條（參考圖 B）：樹殼沿木紋撕成一條條，寬 7–14 cm、長 0.4–0.9 m，上半圈排開、順著樹幹往上翹（上面的翹得多、長），
    斷面跟著樹殼微彎、一路扭一點，尖端每一縷長短不齊（撕開的纖維）。第一版是 90 根往四面放射的細刺，看起來像刺蝟。"""
    ad = Vector(axis_dir).normalized()
    no, ni = len(outer_ring), len(inner_ring)
    c = sum((Vector(p) for p in outer_ring), Vector()) / no
    bm = bmesh.new()
    sul = bm.verts.layers.float.new('ShardU')
    slu = bm.verts.layers.float.new('SlU')                 # 平鋪貼圖用：沿木條公尺、橫過木條公尺（木紋順著木條，不再照軸向投影成鋸齒）
    slv = bm.verts.layers.float.new('SlV')
    shl = bm.faces.layers.int.new('Shard')                 # 遊戲模型同木刺：指到圖集最下面的木色漸層（根暗、尖淺）
    nl, nw = ((4, 3), (3, 2), (2, 1))[DL] if lowpoly else (10, 6)
    if lowpoly and DL == 2:
        n = max(6, n // 2)
    ks = max(1.0, V['R'] / .36)
    for q in range(n):
        lay = q % 2                                                                     # 外層（樹殼）、內層（裡面的木頭）交錯，疊成一整束
        th = math.pi * (.26 + .48 * (q + R.uniform(-.45, .45)) / max(1, n - 1))           # 集中在上半圈（擺得寬會變成一把扇子）
        t = (th / (2 * math.pi)) % 1.0
        po, pi = Vector(outer_ring[int(t * no) % no]), Vector(inner_ring[int(t * ni) % ni])
        base = po.lerp(pi, .20 + .45 * lay + R.uniform(-.08, .08)) - ad * R.uniform(.20, .34)     # 根埋進樹殼裡：看起來是樹殼本身撕開
        rad = base - c
        rad -= ad * rad.dot(ad)
        if rad.length < 1e-6:
            continue
        rad.normalize()
        top = max(0.0, math.sin(th))
        side_w = math.exp(-((th - math.pi * .62) / (math.pi * .20)) ** 2)            # 長木條集中在一側（樹從那邊撕開），其他的短（長短一樣、平均排開＝端面看像王冠）
        ln = R.uniform(.40, .60) * ks * (.22 + .98 * side_w) * R.uniform(.85, 1.15) * (1 - .22 * lay)
        wd = R.uniform(.05, .11) * ks
        tk = R.uniform(.024, .042) * ks                                    # 2.4–4.2 cm 厚：側面看得到木頭的厚度（1–2 cm 像紙）
        pitch = .02 + R.uniform(.08, .22) * top ** 3 * side_w             # 只有撕開那側頂上幾條往上翹，其他順著樹幹（兩側也翹，端面看像一圈尖刺王冠）
        d = (ad * math.cos(pitch) + Vector((0, 0, math.sin(pitch))) + rad * .03 + ad.cross(Vector((0, 0, 1))) * R.uniform(-.03, .03)).normalized()
        nr = (rad - d * rad.dot(d)).normalized()
        tan = d.cross(nr).normalized()
        tw = R.uniform(-.35, .35)
        curl = R.uniform(.02, .08) * top ** 2
        jag = [1.0 - R.uniform(0.0, .28) * (1.0 if j % 2 else .5) for j in range(nw + 1)]
        grid = []
        for i in range(nl + 1):
            u = i / nl
            rt, rb = [], []
            for j in range(nw + 1):
                v = j / nw * 2 - 1
                uj = u * jag[j]
                w = wd * (1 - .55 * uj ** 1.6)                                       # 尾端還有寬度：撕開的參差平頭，不是尖刺
                a_ = tw * uj
                tdir = tan * math.cos(a_) + nr * math.sin(a_)
                ndir = nr * math.cos(a_) - tan * math.sin(a_)
                bulge = .14 * wd * (1 - v * v) + .0025 * math.sin(v * 9 + q)          # 斷面跟著樹殼微彎、上面一條條纖維溝
                pp = base + d * (ln * uj) + ndir * (bulge + curl * ln * uj * uj) + tdir * (v * w * .5)
                th_ = tk * (1 - .7 * uj) + .002
                a = bm.verts.new(pp + ndir * th_ * .5)
                b = bm.verts.new(pp - ndir * th_ * .5)
                a[sul] = b[sul] = uj
                a[slu] = b[slu] = ln * uj + q * .53
                a[slv], b[slv] = v * w * .5 + q * .29, v * w * .5 + q * .29 + th_ * .7
                rt.append(a)
                rb.append(b)
            grid.append((rt, rb))
        F = []
        for i in range(nl):
            (t0, b0), (t1, b1) = grid[i], grid[i + 1]
            for j in range(nw):
                F.append((t0[j], t0[j + 1], t1[j + 1], t1[j]))
                F.append((b0[j], b1[j], b1[j + 1], b0[j + 1]))
            F.append((t0[0], t1[0], b1[0], b0[0]))
            F.append((t0[nw], b0[nw], b1[nw], t1[nw]))
        (t0, b0), (tl, bl) = grid[0], grid[-1]
        for j in range(nw):
            F.append((t0[j], b0[j], b0[j + 1], t0[j + 1]))
            F.append((tl[j], tl[j + 1], bl[j + 1], bl[j]))
        for f in F:
            bm.faces.new(f)[shl] = 1
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(f'Slab{e}')
    bm.to_mesh(me)
    bm.free()
    me.attributes.new('EndMoss', 'FLOAT', 'POINT').data.foreach_set('value', np.zeros(len(me.vertices), np.float32))
    for pg in me.polygons:
        pg.use_smooth = True
    me.materials.append(mat)
    print('SLABS', e, n, len(me.polygons))
    return _obj(f'Slab{e}', me, coll)


def soil8_material():
    """腳邊土堆：DR06 泥的副本，但乾的（DR06 的泥是濕的，朝天的土堆整片反光成米色）。"""
    m = bpy.data.materials.get('DR08_Soil')
    if m:
        return m
    m = mud_material().copy()
    m.name = 'DR08_Soil'
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    for nm_, v in (('Roughness', .93), ('Specular IOR Level', .15), ('Coat Weight', 0.0)):
        sk = b.inputs.get(nm_)
        if sk is None:
            continue
        for l in list(sk.links):
            m.node_tree.links.remove(l)
        sk.default_value = v
    for n in m.node_tree.nodes:                     # 土色壓暗（參考圖腳邊是深褐土，DR06 的中褐在太陽下像沙）
        if n.type == 'VALTORGB' and abs(n.color_ramp.elements[0].color[0] - .040) < 1e-3:
            n.color_ramp.elements[0].color = (.022, .013, .008, 1)
            n.color_ramp.elements[-1].color = (.070, .042, .024, 1)
    return m


def soil_berm(V, coll, mat, seed, lowpoly=False):
    """腳邊的土堆（參考圖三種腳邊都堆著一圈褐土）：兩側各一條，內緣埋在樹幹壁裡，
    高 6–17 cm、寬 0.3–0.45 m，往外降到地面下 3 cm；兩頭收掉（洞口、斷口前面不堆）。"""
    L = V['L']
    dx, ns = (.15, 5) if lowpoly else (.04, 12)
    nx = max(4, int(L * .9 / dx))
    vs, fs = [], []
    for side in (-1, 1):
        b0 = len(vs)
        for i in range(nx + 1):
            t = .05 + .90 * i / nx
            x = t * L
            taper = _sm(min(1.0, min(t - .05, .95 - t) / .12))
            ay, r = axis_y(V, x), out_r(V, x)
            w = (.30 + .15 * fb((x * .9, side * 3.0, seed * .1), 1.0, 2)) * (.4 + .6 * taper)
            hgt = (.11 + .06 * fb((x * 1.7, side * 5.0, seed * .1 + 2), 1.0, 2)) * taper
            for j in range(ns + 1):
                u = j / ns
                y = ay + side * (r * .80 + (r * .20 + w) * u)
                lump = 0.0 if lowpoly else .022 * fb((x * 6.0, y * 6.0, seed * .1 + 4), 1.0, 2)
                z = (hgt + lump) * (1 - u) ** 1.6 - .03 * u * u
                vs.append((x, y, z))
        row = ns + 1
        for i in range(nx):
            for j in range(ns):
                a = b0 + i * row + j
                fs.append((a, a + row, a + row + 1, a + 1) if side > 0 else (a, a + 1, a + row + 1, a + row))
    me = bpy.data.meshes.new('DR08_Soil')
    me.from_pydata(vs, [], fs)
    for pg in me.polygons:
        pg.use_smooth = True
    me.attributes.new('EndMoss', 'FLOAT', 'POINT').data.foreach_set('value', np.zeros(len(me.vertices), np.float32))
    me.materials.append(mat)
    print('SOIL', 'low' if lowpoly else 'high', len(me.polygons))
    return _obj('Soil', me, coll)



# ---------------- v002 參考圖：方塊褐腐做成真的幾何（高低模同一份），貼圖是畫好的方塊磚格 ----------------
CUBE_LIST = []                    # 每顆：(8 個頂點, [(面的 4 個頂點索引, 4 個 (u, v), 磚格號)])
CUBE_T, CUBE_N = 128, 8           # 磚格 128 px、8 格（0–3 端面／頂面：一點點孔；4–7 側面：順纖維的紋）
CUBE_DIR = os.environ.get('DR_CUBE_TILES', 'D:/yun-jing-cache/dr08-work/cube_tiles')


def _sines(rs, u, v, n, fq0, fq1, amp=1.0):
    out = np.zeros(np.broadcast(u, v).shape)
    for _ in range(n):
        a = rs.uniform(0, 2 * math.pi)
        f = rs.uniform(fq0, fq1)
        out += np.sin((u * math.cos(a) + v * math.sin(a)) * f * 2 * math.pi + rs.uniform(0, 6.3))
    return out * amp / max(1, n) ** .5


def cube_tiles():
    """畫 8 格方塊褐腐的磚格（sRGB 底色、法線、AO），寫成 128×1024 的 PNG；同一份給高模預覽和遊戲圖集。
    參考圖 v002 細節：鏽紅褐、一點點小孔、側面順纖維的紋、邊角崩掉變暗。"""
    T, NT = CUBE_T, CUBE_N
    rs = np.random.RandomState(31)
    v, u = np.mgrid[0:T, 0:T].astype(np.float64)
    u, v = (u + .5) / T, (v + .5) / T
    alb = np.zeros((NT * T, T, 3))
    hgt = np.zeros((NT * T, T))
    ao = np.ones((NT * T, T))
    for k in range(NT):
        side = k >= NT // 2
        base = np.array((.300, .158, .090)) * (.70, 1.02, .84, .95, .76, 1.0, .88, .92)[k] * np.array((1.0, rs.uniform(.94, 1.08), rs.uniform(.90, 1.12)))
        lf = _sines(rs, u, v, 6, .8, 2.6, .22)                    # 大片斑駁：有的淺黃褐、有的深
        h = .15 * lf
        col = np.ones((T, T)) * (1 + lf)
        tan = np.clip(lf * 3.0, 0, 1)[..., None] * np.array((.045, .040, .028))[None, None, :]
        if side:                                                   # 側面：沿 u 的纖維
            fib = np.zeros((T, T))
            for _ in range(14):
                fq, ph = rs.uniform(10, 40), rs.uniform(0, 6.3)
                fib += np.sin(v * fq * 2 * math.pi + ph + .8 * np.sin(u * rs.uniform(1, 4) * 2 * math.pi + ph))
            fib /= 14 ** .5
            seg = np.clip(_sines(rs, u * 4.0, v * .6, 5, 1.0, 3.0, 1.6), 0, 1)     # 纖維一段有一段沒有
            fib *= seg
            col *= 1 + .12 * fib
            h += .20 * fib
        else:                                                      # 端面：細小的龜裂
            gr = rs.uniform(-1, 1, (T, T))
            col *= 1 + .07 * gr
            h += .10 * gr
        npore = 20 if not side else 22
        ccx, ccy = rs.uniform(.2, .8, 3), rs.uniform(.2, .8, 3)
        for _ in range(npore):                                     # 小孔：繞幾個中心成片（側面的拉長）
            k_ = rs.randint(3)
            cx = np.clip(ccx[k_] + rs.normal(0, .16), .06, .94)
            cy = np.clip(ccy[k_] + rs.normal(0, .16), .06, .94)
            rx = rs.uniform(.8, 3.2) / T * (2.0 if side else 1.0)
            ry = rs.uniform(.8, 3.2) / T
            m = ((u - cx) / rx) ** 2 + ((v - cy) / ry) ** 2 < 1
            col[m] *= rs.uniform(.55, .75)
            h[m] -= .6
        for ax in (0, 1):                                          # 面上偶爾一條裂縫，從邊裂進來、沒裂到底（褐腐一層套一層地裂）
            if rs.rand() < .55:
                c0 = rs.uniform(.30, .70)
                w_ = rs.uniform(1.0, 2.0) / T
                q_ = (u if ax == 0 else v) + .05 * _sines(rs, u, v, 3, 1.5, 4.0, 1.0)
                al = v if ax == 0 else u
                st = rs.rand() < .5
                reach = rs.uniform(.35, .80)
                ext = np.clip((reach - (al if st else 1 - al)) / .15, 0, 1)
                g = np.clip(1 - np.abs(q_ - c0) / w_, 0, 1) * ext
                col *= 1 - .50 * g
                h -= .8 * g
        d = np.minimum(np.minimum(u, 1 - u), np.minimum(v, 1 - v)) * T      # 離邊幾 px
        chip = d + 6.0 * np.clip(_sines(rs, u, v, 7, 3.0, 10.0, 1.6), 0, None) - 2.0 * np.clip(-_sines(rs, u, v, 5, 6.0, 14.0, 1.0), 0, None)
        bev = np.clip(chip / 10.0, 0, 1)
        h += .9 * bev
        notch = np.clip(1 - chip / 4.0, 0, 1) * (chip < d)              # 缺角（碎掉的地方）
        col *= (1 + .10 * (1 - bev)) * (1 - .40 * notch)
        alb_k = base[None, None, :] * col[..., None] + tan
        if k in (1, 6):                                            # 白色菌絲扇（只兩格：三格時每顆都一樣，像蓋章）（參考圖：方塊上一片片扇形白絲）：從一邊散開的細絲＋根部一團白霧
            ox, oy = (rs.uniform(.1, .9), rs.choice((0.0, 1.0))) if rs.rand() < .5 else (rs.choice((0.0, 1.0)), rs.uniform(.1, .9))
            dir0 = math.atan2(.5 - oy, .5 - ox)
            wm = np.zeros((T, T))
            for _ in range(22):
                an = dir0 + rs.uniform(-.9, .9)
                ln_ = rs.uniform(.35, .95)
                cv_ = rs.uniform(-1.2, 1.2)
                for st in np.linspace(0, 1, 90):
                    a2 = an + cv_ * st * .5
                    px_ = ox + math.cos(a2) * ln_ * st
                    py_ = oy + math.sin(a2) * ln_ * st
                    dd = ((u - px_) ** 2 + (v - py_) ** 2) * T * T
                    wm = np.maximum(wm, np.exp(-dd / .9) * (1 - .6 * st))
            haze = np.exp(-((u - ox) ** 2 + (v - oy) ** 2) / .05) * .55
            wm = np.clip(np.maximum(wm, haze), 0, 1) * .65
            alb_k = alb_k * (1 - wm[..., None]) + np.array((.80, .78, .72))[None, None, :] * wm[..., None]
            h += .3 * wm
        alb[k * T:(k + 1) * T] = alb_k
        hgt[k * T:(k + 1) * T] = h
        ao[k * T:(k + 1) * T] = (.80 + .20 * bev) * (1 - .35 * notch)
    gy, gx = np.gradient(hgt)
    s = 7.0
    nx, ny = -gx * s, -gy * s
    for k in range(1, NT):                                         # 磚格交界不要算斜率
        nx[k * T - 1:k * T + 1] = 0
        ny[k * T - 1:k * T + 1] = 0
    nz = np.ones_like(nx)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    nrm = np.stack([nx / ln, ny / ln, nz / ln], -1) * .5 + .5
    os.makedirs(CUBE_DIR, exist_ok=True)
    out = {}
    for nm, arr, color in (('albedo', np.clip(alb, 0, 1), True), ('normal', nrm, False), ('ao', np.repeat(ao[..., None], 3, -1), False)):
        a4 = np.concatenate([arr, np.ones(arr.shape[:2] + (1,))], -1)
        p = f'{CUBE_DIR}/cube_{nm}.png'
        im = bpy.data.images.new('tmp_cube', T, NT * T, alpha=True)
        im.colorspace_settings.name = 'sRGB' if color else 'Non-Color'
        im.pixels.foreach_set(a4.astype(np.float32).ravel())
        im.filepath_raw = p
        im.file_format = 'PNG'
        im.save()
        bpy.data.images.remove(im)
        out[nm] = p
    print('CUBE_TILES', CUBE_DIR)
    return out


def cube_material():
    """高模預覽用：同一張磚格圖（UV 由 CubeU／CubeV／CubeT 組出來）。"""
    m = bpy.data.materials.get('DR08_Cube')
    if m:
        return m
    paths = cube_tiles()
    m = bpy.data.materials.new('DR08_Cube')
    m.use_nodes = True
    N, Lk = m.node_tree.nodes, m.node_tree.links
    b = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    uv = N.new('ShaderNodeUVMap')
    uv.uv_map = 'CubeTile'
    ta = N.new('ShaderNodeTexImage')
    ta.image = bpy.data.images.load(paths['albedo'], check_existing=True)
    ta.interpolation = 'Closest' if False else 'Linear'
    Lk.new(uv.outputs['UV'], ta.inputs['Vector'])
    tn = N.new('ShaderNodeTexImage')
    tn.image = bpy.data.images.load(paths['normal'], check_existing=True)
    tn.image.colorspace_settings.name = 'Non-Color'
    Lk.new(uv.outputs['UV'], tn.inputs['Vector'])
    to = N.new('ShaderNodeTexImage')
    to.image = bpy.data.images.load(paths['ao'], check_existing=True)
    to.image.colorspace_settings.name = 'Non-Color'
    Lk.new(uv.outputs['UV'], to.inputs['Vector'])
    mu = N.new('ShaderNodeMixRGB')
    mu.blend_type = 'MULTIPLY'
    mu.inputs[0].default_value = 1.0
    Lk.new(ta.outputs['Color'], mu.inputs[1])
    Lk.new(to.outputs['Color'], mu.inputs[2])
    Lk.new(mu.outputs[0], b.inputs['Base Color'])
    nm = N.new('ShaderNodeNormalMap')
    nm.uv_map = 'CubeTile'
    Lk.new(tn.outputs['Color'], nm.inputs['Color'])
    Lk.new(nm.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = .92
    return m


def cubes8_layout(V, trunk, R, cell=.10):
    """方塊褐腐（參考圖 v002）：剝皮處一顆顆凸出 3–11 cm、一階階的鏽紅褐方塊（邊長約 10–14 cm），塊間深縫，
    成片掉了露出暗的洞；腳邊撒一些掉下來的方塊。只在高模算一次，低模照 CUBE_LIST 做同一份。"""
    from mathutils.bvhtree import BVHTree
    from mathutils import Matrix
    CUBE_LIST.clear()
    me_t = trunk.data
    wv = [trunk.matrix_world @ v.co for v in me_t.vertices]
    tb = BVHTree.FromPolygons(wv, [tuple(p.vertices) for p in me_t.polygons])
    pe = np.empty(len(me_t.vertices), np.float32)
    me_t.attributes['Peel'].data.foreach_get('value', pe)
    polys = me_t.polygons
    L = V['L']
    sc = max(1.0, V['R'] / .40)
    cell = cell * sc
    cx_ = cell * 1.05
    dth0 = cell / out_r(V, L * .5)
    edges = [R.random() * dth0]
    while edges[-1] < edges[0] + 2 * math.pi - dth0 * .6:
        edges.append(edges[-1] + dth0 * R.uniform(.75, 1.30))
    edges[-1] = edges[0] + 2 * math.pi
    ne = len(edges) - 1
    wph = [R.uniform(0, 50) for _ in range(ne)]
    wph.append(wph[0])

    def th_e(k, x):
        return edges[k] + dth0 * .25 * fb(Vector((x * 2.0, wph[k], 1.3)), 1.0, 2)
    cuts = []
    xc = -R.uniform(0, cx_)
    while xc < L + cx_:
        cuts.append(xc)
        xc += cx_ * R.uniform(.62, .98)

    def S(x, th):
        o = Vector((x, axis_y(V, x), axis_z(V, x)))
        d = Vector((0, math.cos(th), math.sin(th) * flx(V, x))).normalized()
        return tb.ray_cast(o, d, 3 * out_r(V, x))

    def add_cube(bot, top, tiles_top, tile_side, tile_end, axis):
        """bot/top：各 4 點（同一圈的順序）。axis：沿長方向（判斷側面是順纖維還是端面）。"""
        P = list(bot) + list(top)
        cen = sum(P, Vector()) / 8
        faces = [((4, 5, 6, 7), tiles_top)]
        for i in range(4):
            j = (i + 1) % 4
            ed = (P[j] - P[i]).normalized()
            t_ = tile_side if abs(ed.dot(axis)) > .7 else tile_end
            faces.append(((i, j, 4 + j, 4 + i), t_))
        out = []
        hgt = max((P[4 + i] - P[i]).length for i in range(4))
        for fi, (idx, t_) in enumerate(faces):
            q = [P[i] for i in idx]
            uvs = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
            nrm = (q[1] - q[0]).cross(q[3] - q[0])
            fc = sum(q, Vector()) / 4
            if nrm.dot(fc - cen) < 0:
                idx = tuple(reversed(idx))
                uvs = list(reversed(uvs))
                nrm = -nrm
            nrm = nrm.normalized()
            if fi != 0:                                                     # 側面：平的四邊形（中心點在引擎裡是三角切面）
                out.append((idx, uvs, t_))
                continue
            ins, bul = R.uniform(.16, .26), R.uniform(.05, .11) * hgt       # 頂面倒角：內圈往內縮、往上抬，邊是斜的（磨圓、崩掉的邊）
            ii = []
            for a_ in range(4):
                ii.append(len(P))
                P.append(q[a_] + (fc - q[a_]) * ins * R.uniform(.8, 1.2) + nrm * bul)
            ui = [(u_ + (.5 - u_) * ins, v_ + (.5 - v_) * ins) for u_, v_ in uvs]
            out.append((tuple(ii), ui, t_))
            for a_ in range(4):
                b_ = (a_ + 1) % 4
                out.append(((idx[a_], idx[b_], ii[b_], ii[a_]), [uvs[a_], uvs[b_], ui[b_], ui[a_]], t_))
        CUBE_LIST.append(([p.copy() for p in P], out))

    for it in range(ne):
        xs = [(cuts[0], 0.0)]
        for c in cuts[1:]:
            if R.random() < .92 or c - xs[-1][0] > cx_ * 1.25:
                xs.append((c + R.uniform(-.05, .05) * cx_, R.uniform(-.15, .15) * cx_))
        for j in range(len(xs) - 1):
            (xa, sa_), (xb, sb_) = xs[j], xs[j + 1]
            xm = .5 * (xa + xb)
            if xm < .05 or xm > L - .05:
                continue
            gone = fb(Vector((xm * 1.6, edges[it] * 1.1, V['seed'] * .1)), 1.0, 2)
            if R.random() < .14 or gone > .24:                      # 掉了：露出暗的洞
                continue
            thm = .5 * (th_e(it, xm) + th_e(it + 1, xm))
            hc = S(xm, thm)
            if hc[0] is None or hc[0].z < .03 or hc[1].z < -.55 or hc[1].z > .62:      # 朝下的不做（埋進土）；朝上的是苔，不做（苔上孤零零冒出方塊）
                continue
            if max(pe[i] for i in polys[hc[2]].vertices) < .55 or any((hc[0] - bp).length < br for bp, br in BR_ANCH):
                continue
            cor = [(xa - sa_ * .5, th_e(it, xa)), (xb - sb_ * .5, th_e(it, xb)), (xb + sb_ * .5, th_e(it + 1, xb)), (xa + sa_ * .5, th_e(it + 1, xa))]
            cxp = sum(c[0] for c in cor) / 4
            ctp = sum(c[1] for c in cor) / 4
            kx, kt = R.uniform(.86, .93), R.uniform(.86, .93)
            cor = [(cxp + (c[0] - cxp) * kx + R.uniform(-.05, .05) * cx_, ctp + (c[1] - ctp) * kt + R.uniform(-.05, .05) * dth0) for c in cor]
            hs = [S(px, pt) for px, pt in cor]
            if any(h[0] is None for h in hs):
                continue
            lev = int(3 * max(0.0, min(.999, .5 + 1.4 * fb(Vector((xm * 1.3, thm * .9, 7.0 + V['seed'] * .1)), 1.0, 2))))
            lev = max(0, min(3, lev + R.choice((-1, 0, 0, 1, 1))))
            hh = (.030 + .036 * lev + R.uniform(0, .022)) * sc                 # 一階階：4、8、12 cm 三層，再加一點（參考圖是一根根凸出的短柱）
            tilt = [R.uniform(-.012, .012) * sc for _ in range(4)]
            nn = hc[1].normalized()
            bot = [h[0] - nn * .060 * sc for h in hs]
            top0 = [h[0] + nn * (hh + t_) for h, t_ in zip(hs, tilt)]
            tc = sum(top0, Vector()) / 4
            top = [p + (tc - p) * R.uniform(0.0, .22) - nn * hh * R.uniform(0, .30) for p in top0]      # 頂角崩掉、往下塌
            add_cube(bot, top, R.randrange(0, CUBE_N // 2), CUBE_N // 2 + R.randrange(0, CUBE_N // 2), R.randrange(0, CUBE_N // 2), Vector((1, 0, 0)))
    nin = len(CUBE_LIST)
    for k in range(int(3 * L)):                                   # 腳邊掉下來的方塊
        x = R.uniform(.12, .88) * L
        sd = R.choice((-1, 1))
        y = axis_y(V, x) + sd * (out_r(V, x) * R.uniform(.95, 1.25) + R.uniform(.03, .35))
        s_ = R.uniform(.035, .075) * sc
        rot = Matrix.Rotation(R.uniform(0, 2 * math.pi), 3, 'Z') @ Matrix.Rotation(R.uniform(-.35, .35), 3, 'X')
        q = [Vector((-1, -1, 0)), Vector((1, -1, 0)), Vector((1, 1, 0)), Vector((-1, 1, 0))]
        z0 = .015 + .02 * R.random()
        bot = [Vector((x, y, -.02)) + rot @ Vector((p.x * s_ * .5, p.y * s_ * .5 * R.uniform(.8, 1.2), 0)) for p in q]
        top = [Vector((x, y, -.02)) + rot @ Vector((p.x * s_ * .45, p.y * s_ * .45, s_ * R.uniform(.7, 1.0) + z0)) for p in q]
        add_cube(bot, top, R.randrange(0, CUBE_N // 2), CUBE_N // 2 + R.randrange(0, CUBE_N // 2), R.randrange(0, CUBE_N // 2), rot @ Vector((1, 0, 0)))
    print('CUBES', nin, 'on log +', len(CUBE_LIST) - nin, 'on ground')


def cubes8_mesh(coll, lowpoly=False):
    """照 CUBE_LIST 做方塊網格（高低模同一份）。角屬性 CubeU／CubeV、面屬性 CubeT：遊戲模型照這個指到圖集右邊那欄的磚格；
    高模另做一個 UV 'CubeTile' 給預覽材質。"""
    vs, fs, cu, cv, ct = [], [], [], [], []
    for P, faces in CUBE_LIST:
        o_ = len(vs)
        vs += [tuple(p) for p in P]
        for idx, uvs, t_ in faces:
            fs.append(tuple(o_ + i for i in idx))
            cu += [a for a, b in uvs]
            cv += [b for a, b in uvs]
            ct.append(t_)
    me = bpy.data.meshes.new('DR08_Cubes')
    me.from_pydata(vs, [], fs)
    me.attributes.new('CubeU', 'FLOAT', 'CORNER').data.foreach_set('value', np.array(cu, np.float32))
    me.attributes.new('CubeV', 'FLOAT', 'CORNER').data.foreach_set('value', np.array(cv, np.float32))
    me.attributes.new('CubeT', 'INT', 'FACE').data.foreach_set('value', np.array(ct, np.int32))
    me.attributes.new('EndMoss', 'FLOAT', 'POINT').data.foreach_set('value', np.zeros(len(me.vertices), np.float32))
    if not lowpoly:
        uvl = me.uv_layers.new(name='CubeTile')
        m_ = 1.5 / CUBE_T
        tt = np.repeat(np.array(ct, np.float64), [len(f) for f in fs])
        uu = np.array(cu) * (1 - 2 * m_) + m_
        vv = (tt + np.array(cv) * (1 - 2 * m_) + m_) / CUBE_N
        uvl.data.foreach_set('uv', np.stack([uu, vv], -1).astype(np.float32).ravel())
        me.materials.append(cube_material())
    else:
        me.materials.append(rot8_material())
    print('CUBES_MESH', 'low' if lowpoly else 'high', len(fs), 'faces')
    return _obj('Cubes', me, coll)


def build(variant='A', quick=True, low=None, col=False, pre=''):
    """low=(step, numin, numax, nuk[, LOD 級])：同一份路徑做不帶樹皮凹凸的低模；col=True：只做碰撞殼。"""
    global DL
    DL = low[4] if low and len(low) > 4 else 0
    V = set_variant(variant)
    CFG.update(step=.05 if quick else .025, numin=28 if quick else 44, numax=360, amp=.025, moss=.036, nuk=.8, crest=.40)      # 掃描凹凸淺（細樹幹上一條條大波浪），苔厚一點、一團團
    if low:
        CFG.update(step=low[0], numin=low[1], numax=low[2], amp=0.0, moss=.030, nuk=low[3])      # 低模也帶苔墊的起伏（輪廓一團團），略低於高模
    seed = V['seed']
    noise.seed_set(seed)
    R = random.Random(seed)
    coll = _coll(f"{PRE}_{V['name']}_{'Col' if col else ('Low' if low else 'High')}")
    if col:
        col_shell(V, coll, sides=10, step=.5)
        return _finish_names(coll, pre)
    mat = bark8_material()
    rmat = rot8_material()
    objs = []
    tp = shell_pts(V)
    trunk = tube('Trunk', tp, seed, rib=.08, twist=.20, collection=coll, moss_bias=trunk_moss8, cap_end=False)
    trunk.data.materials.append(mat)
    objs.append(trunk)
    peel5(trunk, tp, seed, frac_thr=-.16)                  # 樹皮掉了一大半（低模也壓：方塊坐在壓下去的木頭面上，高低模一致）
    if not low:
        bark_plates(V, trunk, tp, seed)
    rings_o, nu_o, co_o = ragged_ends(V, trunk, tp)
    amp0, moss0 = CFG['amp'], CFG['moss']
    CFG.update(amp=amp0 * .5, moss=0.0)
    ip = shell_pts(V, inner=True)
    inner = tube('Inner', ip, seed + 5, rib=.10, twist=.06, collection=coll, moss_bias=-1.0, cap_end=False)
    CFG.update(amp=amp0, moss=moss0)
    rings_i, nu_i, co_i = ragged_ends(V, inner, ip, inner=True)
    clear_inner(V, trunk, inner, gap=.03)
    co_i = np.array([v.co[:] for v in inner.data.vertices])
    end_moss(V, inner, rings_i, nu_i, co_i)
    flip(inner)
    inner.data.materials.append(rmat)
    objs.append(inner)
    for e, k_o, k_i, ad in ((0, 0, 0, -1), (1, len(rings_o) - 1, len(rings_i) - 1, 1)):
        ta = rings_o[min(k_o + 1, len(rings_o) - 1)][0] - rings_o[max(k_o - 1, 0)][0]
        o = rim(V, coll, f'Rim{e}', end_ring(co_o, nu_o, k_o), end_ring(co_i, nu_i, k_i), ta.normalized() * ad, rmat, seed + e, rows=5, lowpoly=bool(low))
        objs.append(o)
        if V['ends'][e] == 1:
            objs.append(slabs8(V, coll, random.Random(seed + 60 + e), e, end_ring(co_o, nu_o, k_o), end_ring(co_i, nu_i, k_i),
                               ta.normalized() * ad, splinter_material(), n=22, lowpoly=bool(low)))
    objs += punch_holes(V, coll, trunk, inner, rmat, lowpoly=bool(low))
    rings, _ = resample(tp, CFG['step'])
    if BRACKETS:
        objs.append(brackets8(V, coll, random.Random(seed + 4), rings, bracket_material(), lowpoly=bool(low), trunk=trunk))
    else:
        BR_ANCH.clear()
    if not low:
        cubes8_layout(V, trunk, random.Random(seed + 7))
    cb = cubes8_mesh(coll, lowpoly=bool(low))              # 方塊褐腐：真的幾何（參考圖 v002），高低模同一份
    objs.append(cb)
    if not low:
        objs.append(mycel_fans(V, coll, trunk, random.Random(seed + 8), blocks=cb))
    objs.append(debris8(V, coll, R, rmat, int(26 * V['L'] * (1.8, .95, .10)[DL]), sub=0 if low else 1))
    objs.append(soil_berm(V, coll, soil8_material(), seed, lowpoly=bool(low)))
    if not BRACKETS:                                       # 11/24 使用者看參考圖：大香菇是自己從地上長出來、有菌柄，只是靠著樹幹
        objs.append(big_mush8(V, coll, random.Random(seed + 4), bracket_material(), trunk, soil=objs[-1], lowpoly=bool(low),
                              solids=[o for o in objs if o is not inner]))
    print('BUILD', V['id'], 'low' if low else 'high', len(coll.objects), 'objects')
    return _finish_names(coll, pre)


_dress5 = dress


def moss_clumps8(name, mounds, R, mat, per=90):
    """參考圖的苔是一叢叢毛茸茸、往下掛的厚苔：每個苔墊上 per 根 3.5–7.5 cm 的粗苔絲，
    中間往上、邊緣往外往下垂。遊戲模型也帶（指到圖集的苔色葉片格）。"""
    buf = core_plants.LeafBuf()
    for (i, cx, cy, rx, ry, hgt, z0) in mounds:
        for k in range(per):
            a = R.uniform(0, 2 * math.pi)
            rr = math.sqrt(R.random())
            px, py = math.cos(a) * rr, math.sin(a) * rr
            pz = math.sqrt(max(0.0, 1 - rr * rr))
            p = Vector((cx + px * rx * .9, cy + py * ry * .9, z0 + pz * hgt * 1.4))
            d = Vector((px * 1.2 + R.uniform(-.3, .3), py * 1.2 + R.uniform(-.3, .3), .9 * pz - .45 * rr + R.uniform(-.2, .3))).normalized()
            d, side, up = core_plants._frame(d)
            L = R.uniform(.030, .060)
            g = R.uniform(.75, 1.15)
            buf.leaf(p - d * .01, d, side, up, L, L * R.uniform(.14, .22), shape=lambda u: (1 - u) ** .4, fold=.2,
                     droop=R.uniform(.4, .9), tint=(g * R.uniform(.9, 1.1), g, g * .75), nu=2, nv=1)
    return buf.build(name, mat)


def seedling8(name, pos, R, height, leaf_mat, stem_mat):
    """朽木頂上的小苗（參考圖）：一根細莖 18–30 cm，上半段對生 2–3 對卵形葉，頂上一對小的。"""
    buf = core_plants.LeafBuf()
    lean = Vector((R.uniform(-.2, .2), R.uniform(-.2, .2), 1)).normalized()
    stem = []
    for i in range(7):
        u = i / 6
        p = pos + lean * height * u + Vector((.04 * math.sin(u * 4 + height * 9), .04 * math.cos(u * 3), 0)) * height
        stem.append((p, .0030 + .0025 * (1 - u)))
    npair = R.choice((2, 3, 3))
    az0 = R.uniform(0, 2 * math.pi)
    for k in range(npair + 1):
        top = k == npair
        at = stem[min(6, int(round((.45 + .55 * k / npair) * 6)))][0]
        for s_ in (0, 1):
            az = az0 + k * math.pi / 2 + s_ * math.pi
            dd = Vector((math.cos(az), math.sin(az), R.uniform(.35, .7) if top else R.uniform(-.05, .30))).normalized()
            dd, side, nrm = core_plants._frame(dd)
            ro = R.uniform(-.4, .4)
            side, nrm = side * math.cos(ro) + nrm * math.sin(ro), -side * math.sin(ro) + nrm * math.cos(ro)
            L = height * R.uniform(.30, .38) * (.6 if top else 1.0)
            g = R.uniform(.9, 1.1)
            buf.leaf(at - dd * .004, dd, side, nrm, L, L * R.uniform(.48, .58),
                     shape=lambda u: math.sin(math.pi * min(1.0, u * 1.08)) ** .75 * (1 - .25 * u), fold=R.uniform(.2, .35),
                     curl=R.uniform(0, .15), droop=R.uniform(.1, .3), tint=(g, g, g * .9), nu=6, nv=4)
    return buf.build(name, leaf_mat), _twigs(name + '_Stem', [stem], stem_mat)


def dress(V, quick=True, seed=None, game=False, surf=('Trunk',)):
    """DR08 的植物、落葉（尺寸照 2–5 m 的朽木縮）：頂上整條厚苔叢＋淺灰綠地衣不在這裡（在材質），
    頂上 1–3 株小蕨、小苗；側面一叢叢小褐蕈；腳邊 2–4 株蕨、闊葉草；落葉少、只在腳邊 0.5 m 內。"""
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

    def hit(x, y, z0=6.0):
        ok, loc, nrm, _, ob, _ = sc.ray_cast(dg, Vector((x, y, z0)), Vector((0, 0, -1)))
        return (loc, nrm, ob.name) if ok else None

    def on_log(x, y, nz=.72):
        h = hit(x, y)
        if h and h[2] in surf and h[1].z > nz:
            return h
        return None

    def half_w(x):
        return out_r(V, x) * .98

    def gz(x, y):
        h = hit(x, y)
        return max(0.0, h[0].z) if h and (h[2] in surf or h[2].startswith('Soil')) else 0.0

    def keep(o):
        for c in list(o.users_collection):
            c.objects.unlink(o)
        coll.objects.link(o)
        return o

    out = []
    mounds = []
    for i in range(int(L * 7)):
        x = R.uniform(.04, .96) * L
        h = on_log(x, axis_y(V, x) + R.gauss(0, .35 * Rt), .55)
        if h:
            mounds.append((i, h[0].x, h[0].y, R.uniform(.40, .80) * Rt, R.uniform(.28, .50) * Rt, R.uniform(.025, .05), h[0].z - .02))
    if mounds and not game:
        out.append(keep(core_plants.moss_tufts('DR08_MossTufts', mounds, R, moss_mat, fb, density=6000 if quick else 12000)))
    if mounds:
        mc = [m_ for m_ in mounds if .35 < m_[1] < L - .35]          # 兩頭斷口、洞口邊上不長（遊戲模型裡一團黃綠掛在洞口很突兀）
        out.append(keep(moss_clumps8('DR08_MossClump', mc, random.Random(seed + 55), moss_mat, per=55 if game else 300)))
    nf = 0
    for i in range(40):
        if nf >= max(1, int(L * .6)):
            break
        x = R.uniform(.10, .85) * L
        h = on_log(x, axis_y(V, x) + R.gauss(0, .2 * Rt), .8)
        if not h:
            continue
        o, so = core_plants.fern(f'DR08_TopFern{nf}', h[0] - Vector((0, 0, .02)), R, R.uniform(.55, .80) * Rt, fern_mat, stem_mat)
        out += [keep(o), keep(so)]
        nf += 1
    # 頂上的小苗：自己的亂數（高模、遊戲模型長在同一處、同一個樣子）
    sap_mat = mat('DR06_SaplingLeafV2', (.10, .13, .030, 1), (.30, .34, .085, 1), (.38, .40, .14, 1), gloss=.45)
    twig_mat = bpy.data.materials.get('DR06_Twig')
    if twig_mat is None:
        twig_mat = bpy.data.materials.new('DR06_Twig')
        twig_mat.use_nodes = True
        next(n for n in twig_mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Base Color'].default_value = (.07, .05, .035, 1)
    RS = random.Random(seed + 77)
    ns = 0
    for i in range(80):
        if ns >= max(2, int(L * .8)):
            break
        x = RS.uniform(.08, .92) * L
        h = on_log(x, axis_y(V, x) + RS.gauss(0, .18 * Rt), .8)
        if not h:
            continue
        lo, so = seedling8(f'DR08_Sapling{ns}', h[0] - Vector((0, 0, .02)), RS, RS.uniform(.28, .42), sap_mat, twig_mat)
        out += [keep(lo), keep(so)]
        ns += 1
    nm = 0
    for i in range(60):
        if nm >= max(2, int(L * .8)):
            break
        x = R.uniform(.08, .92) * L
        sg = R.choice((-1, 1))
        h = hit(x, axis_y(V, x) + sg * half_w(x) * R.uniform(.55, .85))
        if h and h[2] in surf and h[1].z > .2:
            out.append(keep(core_plants.mushrooms(f'DR08_LogMush{nm}', h[0] - Vector((0, 0, .01)), R, R.randint(4, 8), 1.4 * Rt, mush_mat, cap=MUSH_CAP)))
            nm += 1
    for k in range(max(2, int(L * 1.0))):
        x = R.uniform(.05, .95) * L
        sg = R.choice((-1, 1))
        y = axis_y(V, x) + sg * (half_w(x) + R.uniform(.02, .12))
        out.append(keep(core_plants.mushrooms(f'DR08_FootMush{k}', Vector((x, y, 0)), R, R.randint(4, 9), 1.6 * Rt, mush_mat, cap=MUSH_CAP, ground=gz)))
    glow = bpy.data.materials.get('DR08_GlowMush')
    if glow is None:
        glow = core_plants.mushroom_material().copy()
        glow.name = 'DR08_GlowMush'
        gb = next(n for n in glow.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        gb.inputs['Emission Color'].default_value = (.30, .85, .55, 1)
        gb.inputs['Emission Strength'].default_value = 1.5
    RG = random.Random(seed + 91)
    for e in (0, 1):
        if V['ends'][e] not in (0, 2):
            continue
        for tries in range(12):
            x = (.30 + RG.uniform(0, .25)) if e == 0 else (L - .30 - RG.uniform(0, .25))
            h = hit(x, axis_y(V, x) + RG.uniform(-.08, .08), axis_z(V, x))
            if h and (h[2] in surf or h[2].startswith(('Inner', 'Rim'))) and h[1].z > .5:
                out.append(keep(core_plants.mushrooms(f'DR08_GlowMush{e}', h[0] - Vector((0, 0, .01)), RG, RG.randint(5, 8), 1.2 * Rt, glow,
                                                      cap=(.50, .80, .62))))
                break
    for k in range(max(3, int(L * 1.3))):
        x = R.uniform(.05, .95) * L
        sg = -1 if k % 2 == 0 else 1
        y = axis_y(V, x) + sg * (half_w(x) + R.uniform(.12, .30))
        o, so = core_plants.fern(f'DR08_FootFern{k}', Vector((x, y, gz(x, y) - .02)), R, R.uniform(.9, 1.2) * Rt, fern_mat, stem_mat)
        out += [keep(o), keep(so)]
    for k in range(max(1, int(L * .5))):
        x = R.uniform(.1, .9) * L
        sg = R.choice((-1, 1))
        y = axis_y(V, x) + sg * (half_w(x) + R.uniform(.05, .3))
        o = core_plants.heart_plant(f'DR08_Heart{k}', Vector((x, y, gz(x, y) - .01)), R, R.uniform(.55, .8) * Rt, heart_mat, stem_mat)
        out.append(keep(o))
        so = bpy.data.objects.get(f'DR08_Heart{k}_stem')
        if so:
            out.append(keep(so))

    def place():
        x = R.uniform(-.12, 1.08) * L
        sg = R.choice((-1, 1))
        y = axis_y(V, min(max(x, 0), L)) + sg * (half_w(min(max(x, 0), L)) + abs(R.gauss(0, .25)) + .02)
        h = hit(x, y, 6.0)
        z = h[0].z if h else 0.0
        if z > .25 or (h and ('Brackets' in h[2] or 'Mycel' in h[2])):      # 不要落在層狀菌、菌絲上（一片片插在菌叢裡）
            return None
        if z > .04 and any((Vector((x, y, 0)) - Vector((bp.x, bp.y, 0))).length < br * 2.2 for bp, br in BR_ANCH):
            return None
        return (x, y), z
    lo, n = litter('DR08_Litter', R, int(L * 28), place, litter_mat)
    out.append(keep(lo))
    print('DRESS', len(out), 'plant objects, litter', n)
    return coll


def _views(V):
    L = V['L']
    cx = L * .5
    zc = axis_z(V, L)
    fs = next((f * L for f, ang, c in V['fungi'] if ang > 0), cx)        # 最近 -Y 側那叢層狀菌
    return {
        'tq': ((L + 2.6, -3.4, 1.7), (L * .55, 0, .3), 30),
        'side': ((cx, -L * .9 - 2.2, .9), (cx, 0, .3), 30),
        'top': ((cx, -.01, L * 1.3 + 2.5), (cx, 0, 0), 30),
        'back': ((cx * .9, L * .9 + 2.2, 1.3), (cx, 0, .3), 30),
        'end': ((L + 2.4, axis_y(V, L) - .3, .75), (L, axis_y(V, L), zc), 32),
        'endA': ((-2.4, .3, .75), (0, 0, axis_z(V, 0)), 32),
        'hole': ((L * .5 + .6, 1.6, 2.0), (L * .5, 0, .35), 30),
        'fungi': ((L * .4, -1.9, .7), (L * .4, 0, .25), 30),
        'leftc': ((-.5, -1.9, 1.1), (.55, 0, .35), 40),
        'midc': ((L * .68, -1.7, .9), (L * .68, 0, .35), 40),
        'brk': ((fs + .30, axis_y(V, fs) - V['R'] - .95, .25 + V['R'] * .5), (fs, axis_y(V, fs) - V['R'] * .7, V['R'] * .35), 40),
    }


if __name__ == '__main__' and '--' in sys.argv:
    args = sys.argv[sys.argv.index('--') + 1:]
    var = args[0] if args else 'A'
    quick = (args[1] if len(args) > 1 else 'quick') == 'quick'
    outdir = args[2] if len(args) > 2 else 'D:/yun-jing-cache/dr08-work'
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
        hum.location = (-1.1, 1.4, .875)                   # 樹幹後面一頭，量尺看得到又不擋
    want = args[3].split(',') if len(args) > 3 else list(_views(VAR))
    for k in want:
        loc, tgt, lens = _views(VAR)[k]
        preview_dr.shot(os.path.join(outdir, f"DR08_{var}_{k}.png"), loc, tgt, lens, (1280, 720))
    for a_ in args[4:]:
        if a_.endswith('.blend'):
            bpy.ops.wm.save_as_mainfile(filepath=a_)
