# DR08 長滿蕈和苔的朽木 A／B／C — v002 遊戲模型（直接建遊戲網格，不烘焙；材質、貼圖沿用 DR08_Shared 的兩個材質）。
# 為什麼重做（審圖意見，同角度對照參考圖像度約 55–60%）：
#   v001 外形像一塊方磚（上緣平、底邊一條直線）、兩頭只是收圓、苔只是貼圖上的綠點、香菇是地上長的有柄菇、底下乾淨像放在地上。
# v002 做法：
#   - 樹幹：圓剖面的管；上緣照參考圖隆起／塌陷（塌陷只壓頂上，側面不動，所以是一道凹槽，露出紅褐的褐腐木）；底部陷進土裡。
#   - 兩頭：C 左端是空心洞口（外殼＋內壁兩層、洞口斷面一圈圈年輪往裡退成台階，裡面越深越暗）；B 右端是一大束撕裂、往上翹的木纖維；
#     其餘是參差的碎斷口（斷面凹凸、褐腐色）。
#   - 苔毯：另一層有厚度（4–8 cm）的網格蓋在頂上，邊緣參差、一舌舌往兩側垂下，邊緣塞進樹皮底下；兩側再掛垂苔卡。
#   - 層孔菌：無柄、半圓托盤狀，一叢 3–5 片疊在樹幹側面（植物圖集的層孔菌圖）。有柄小褐蕈只留幾叢在地上。
#   - 底部過渡：一圈落葉土（爬上樹幹側面蓋掉底線）、碎木塊、剝落的樹皮片、蕨、落葉；A、B 正面下方有一個朽空的凹洞，裡面有發光小蕈。
# 本體：M_DR08_Layered_v002（v001 材質複製、苔換亮黃綠 DR08_Moss_v002_Albedo；Unity：YunJing/D2LayeredWood）。UV0 公尺；頂點色 RGBA＝苔、褐腐、纖維、內壁；UV1＝(土, AO)。
# Detail_DR08_Plants：層孔菌、蕨、小苗、垂苔、小褐蕈、發光小蕈、落葉，M_DR08_Plants（雙面、alpha 裁切）。
# 用法（背景）：blender -b --python art/source/d2-logs-b/game_dr08v2.py -- C
import bpy, bmesh, sys, os, json, math, random, time, traceback
import numpy as np
from mathutils import Vector, Matrix, noise
from mathutils.bvhtree import BVHTree

ROOT = 'D:/yun-jing-d2-logs'
HERE = ROOT + '/art/source/d2-logs-b'
ROOTS = ROOT + '/art/source/d2-roots-b'
VER = 'v002'
NAMES = {v: f'DR08_RottenLog_{v}' for v in 'ABC'}
DET = 'Detail_DR08_Plants'

# L 長、R 半徑、sink 陷進土裡（半徑比例）、bend 左右彎
# prof：(位置, 半徑增減, 寬) 隆起／變細；collapse：(位置, 頂上塌下去的深度（半徑比例）, 寬)
# ends：兩頭 crumb 碎斷口／torn 撕裂纖維束／hollow 空心洞口
# cavity：(位置, 半長 m, 深 m)：正面下方朽空的凹洞；brackets：(位置, -1 正面／+1 背面, 片數)
VARIANTS = {
    'A': dict(L=2.2, R=.40, sink=.20, bend=.04, seed=801, moss_t=.13, mound=.24, margin=.32,
              prof=((.24, .20, .20), (.52, -.08, .18), (.78, .17, .19)),
              collapse=((.52, .48, .19),),
              ends=('crumb', 'crumb'), cavity=((.70, .36, .38),),
              brackets=((.22, -1, 4), (.40, -1, 3), (.74, -1, 2), (.40, 1, 2)), saplings=2, ferns=11, mush=2),
    'B': dict(L=3.7, R=.48, sink=.18, bend=.06, seed=802, moss_t=.14, mound=.27, margin=.38,
              prof=((.20, .16, .17), (.55, -.08, .14), (.88, .10, .10)),
              collapse=((.56, .52, .13), (.33, .18, .06)),
              ends=('crumb', 'torn'), cavity=((.36, .42, .38),),
              brackets=((.15, -1, 4), (.27, -1, 3), (.78, -1, 4), (.62, 1, 3)), saplings=3, ferns=15, mush=2, gaps=.7),
    'C': dict(L=5.0, R=.62, sink=.14, bend=.08, seed=803, moss_t=.15, mound=.30, margin=.42,
              prof=((.10, .08, .14), (.55, -.10, .16), (.82, .08, .14)),
              collapse=((.55, .48, .14), (.36, .20, .07)),
              ends=('hollow', 'crumb'), cavity=(), delta=1.45,
              brackets=((.20, -1, 4), (.34, -1, 3), (.66, -1, 4), (.80, -1, 3), (.48, 1, 3)), saplings=4, ferns=18, mush=3, gaps=.5),
}
LODRES = {0: dict(ns=40, dx=.07, bl=.06, mg=.09, deb=1.0), 1: dict(ns=24, dx=.13, bl=.11, mg=.16, deb=.55), 2: dict(ns=12, dx=.30, bl=.26, mg=.34, deb=.22)}
PLANT_KEEP = {0: 1.0, 1: .55, 2: .15}
DELTA = .80          # 兩頭參差斷口：最後 0.45 m 內照角度往內縮
WALL = .15           # 空心洞口的殼厚（參考圖 C 洞口約 1 m、殼約 15 cm）
HOLLOW_D = 1.7       # 空心往裡多深
V = None


# ---------------------------------------------------------------- 小工具
def U(R, a, b):
    return a + (b - a) * R.random()


def sm(x, e0, e1):
    t = np.clip((np.asarray(x, float) - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def nz(x, y=0.0, z=0.0):
    return noise.noise(Vector((x, y, z)))


def _exec(path, name):
    g = {'__name__': name, '__file__': path}
    exec(compile(open(path, encoding='utf-8').read(), path, 'exec'), g)
    return g


_LIB = None


def lib8():
    """DR08 的兩個材質（M_DR08_Layered、M_DR08_Plants）和植物圖集分格。"""
    global _LIB
    if _LIB is None:
        _LIB = _exec(HERE + '/game_dr08t.py', 'dr08t_lib')
    return _LIB


def layer_mat_v2():
    """M_DR08_Layered_v002：複製 v001 材質，把苔、纖維、樹皮的顏色圖換成 v002（苔較亮黃綠、纖維淡米色、樹皮暖紅褐）。v001 材質不動。"""
    nm = 'M_DR08_Layered_v002'
    m = bpy.data.materials.get(nm)
    if m:
        return m
    m = lib8()['layer_material']().copy()
    m.name = nm
    for n in m.node_tree.nodes:
        for k in ('Moss', 'Fibre', 'Bark'):
            if n.type == 'TEX_IMAGE' and n.image and n.image.name.startswith(f'DR08_{k}_Albedo'):
                path = n.image.filepath.replace(f'DR08_{k}_Albedo', f'DR08_{k}_v002_Albedo')
                n.image = bpy.data.images.load(path, check_existing=True)
    return m


# ---------------------------------------------------------------- 形狀
def gsum(t, lst):
    return sum(a * math.exp(-((t - tc) / w) ** 2) for tc, a, w in lst)


def R_at(x):
    t = x / V['L']
    return V['R'] * (1 + gsum(t, V['prof'])) * (1 + .035 * math.sin(t * 9.0 + V['seed']))


def yc(x):
    return V['bend'] * math.sin(math.pi * x / V['L'])


def zc(x):
    return V['R'] * (1 - V['sink']) + .25 * (R_at(x) - V['R'])


def collapse(x):
    return gsum(x / V['L'], V['collapse'])


def cav(x, th):
    """正面下方朽空凹洞的深度（公尺）和權重。"""
    d, g = 0.0, 0.0
    for tc, hl, dep in V['cavity']:
        xc = tc * V['L']
        da = ((th - (math.pi + .12)) + math.pi) % (2 * math.pi) - math.pi
        gg = math.exp(-((x - xc) / hl) ** 4) * math.exp(-(da / .50) ** 4)
        gg *= 1 + .25 * nz(x * 4, th * 2, 7.7)
        if gg > g:
            g, d = gg, dep * gg
    return d, min(1.0, g)


def rad(x, th):
    r = R_at(x)
    s = math.sin(th)
    sd = V['seed']
    r *= 1 - collapse(x) * max(0.0, s) ** 1.6
    for e in (0, 1):                                       # 碎斷口那頭上半圈收小：側看是圓坡，不是方角
        if V['ends'][e] == 'crumb':
            de = x if e == 0 else V['L'] - x
            r *= 1 - .42 * max(0.0, s) ** 1.3 * (1 - float(sm(de, 0, .95)))
    r *= 1 + .06 * nz(x * 1.3, math.cos(th) * 1.2, s * 1.2 + sd) + .06 * nz(x * 4.5, math.cos(th) * 3, s * 3 + sd) + .035 * nz(x * 11, math.cos(th) * 8, s * 8 + sd)
    cl = collapse(x) * max(0.0, s + .3)
    r *= 1 + cl * (.22 * nz(x * 7, math.cos(th) * 6, s * 6 + sd + 13) + .12 * nz(x * 15, math.cos(th) * 12, s * 12 + sd + 3))   # 塌陷槽裡是碎爛的褐腐塊，不是光滑樹皮
    r -= cav(x, th)[0]
    return r


def pt(x, th, r=None):
    r = rad(x, th) if r is None else r
    return np.array((x, yc(x) + r * math.cos(th), zc(x) + r * math.sin(th)))


def cut(e, th):
    """第 e 頭（0：x=0，1：x=L）的斷口在角度 th 往內縮幾公尺。"""
    kind = V['ends'][e]
    R_ = V['R']
    s = V['seed'] + 17 * e
    c, sn = math.cos(th), math.sin(th)
    if kind == 'hollow':
        v = R_ * (.03 + .10 * abs(nz(c * 2.4, sn * 2.4, s)))
        v += R_ * .25 * max(0.0, sn) ** 3 * (.5 + abs(nz(c * 3, sn * 3, s + 4)))   # 頂上那圈殼缺一點
        v += R_ * 1.55 * (.5 - .5 * c) ** 1.3                                            # 斜切：正面（−Y）退得多，洞口朝正面偏，平視看得到洞
    elif kind == 'torn':
        v = R_ * (.06 + .45 * abs(nz(c * 7, sn * 7, s + 2)) + .20 * (1 - sn) * .5)
    else:
        v = R_ * (.10 + .60 * abs(nz(c * 2.2, sn * 2.2, s)) + .15 * abs(nz(c * 8, sn * 8, s + 3)))
        v += R_ * .55 * max(0.0, sn) ** 1.5 * (.6 + .6 * abs(nz(c * 1.5, s, 1)))          # 上半邊碎掉多一些
    return min(v, dl(e) - .04)


def dl(e):
    """第 e 頭斷口的壓縮長度：空心洞口斜切很深，要比較長（C 用 delta）。"""
    return V.get('delta', DELTA) if V['ends'][e] == 'hollow' else DELTA


def xmap(x, th, extra=(0.0, 0.0)):
    """兩頭最後 DELTA 內照斷口形狀往內壓縮。"""
    L = V['L']
    d0, d1 = dl(0), dl(1)
    if x < d0:
        c = cut(0, th) + extra[0]
        return c + x * (d0 - c) / d0
    if x > L - d1:
        c = cut(1, th) + extra[1]
        return L - c - (L - x) * (d1 - c) / d1
    return x


def moss_t(x, th):
    """苔毯的厚度（0＝沒有苔毯）和遮罩 m（>0 在苔毯裡）。"""
    L = V['L']
    sd = V['seed']
    side = 1 if math.cos(th) > 0 else -1
    span = 1.05 + .45 * nz(x * 1.1, sd, 2.0) - 1.3 * collapse(x)
    span -= V.get('gaps', 0) * max(0.0, nz(x * 1.4, sd + 31, 0.5) + .1) * 2.2          # 苔斷成一段段，中間露樹皮
    span += 2.2 * max(0.0, nz(x * 2.8, side * 3.1, sd + 5.0) + .05) ** 1.1 + .30 * abs(nz(x * 9, side, sd + 2))         # 一舌舌往下垂
    a = abs(((th - math.pi / 2) + math.pi) % (2 * math.pi) - math.pi)
    m = span - a
    lo = cut(0, math.pi / 2) + .03 if V['ends'][0] != 'hollow' else .02
    hi = L - cut(1, math.pi / 2) - .03
    mx = min((x - lo) * 4.0, (hi - x) * 4.0)
    m = min(m, mx)
    if m <= 0:
        return 0.0, m
    clump = .5 + .5 * nz(x * 1.8, math.cos(th) * 1.8, math.sin(th) * 1.8 + sd + 9) + .22 * nz(x * 4.2, math.cos(th) * 4.2, math.sin(th) * 4.2 + sd + 4) + .14 * nz(x * 9, math.cos(th) * 9, math.sin(th) * 9 + sd + 6)   # 低頻圓團＋小簇，不要高頻尖峰
    return V['moss_t'] * float(.35 + .65 * sm(m, 0, .25)) * max(.25, .40 + 1.1 * clump) * max(.2, 1 - 2.2 * collapse(x)) * float(sm(mx, 0, .22)), m          # 兩頭收薄到 0（不留開口的厚邊）         # 一團團隆起的苔墊（頂線不平）


# ---------------------------------------------------------------- 網格
class MB:
    """頂點、面（每個角的 UV）、每個頂點的權重（苔、褐腐、纖維、內壁、土）、面的種類。"""

    def __init__(self):
        self.V, self.F, self.UV, self.W, self.fk = [], [], [], [], []

    def v(self, p, w=(0, 0, 0, 0, 0)):
        self.V.append(tuple(float(a) for a in p))
        self.W.append(tuple(float(a) for a in w))
        return len(self.V) - 1

    def f(self, idx, uvs, kind=0):
        self.F.append(tuple(idx))
        self.UV.append([tuple(map(float, u)) for u in uvs])
        self.fk.append(kind)


def trunk_w(x, th, p):
    """樹幹表面的權重：塌陷槽、側面一塊塊褐腐；凹洞＝內壁；腳下＝土。"""
    sd = V['seed']
    s = math.sin(th)
    rot = 1.6 * collapse(x) * max(0.0, s) ** .8
    rot += float(sm(nz(x * 1.7, math.cos(th) * 1.4, s * 1.4 + sd + 3) + .12, 0, .30)) * float(sm(.75 - s, 0, .6))
    inner = cav(x, th)[1]
    inner = float(sm(inner, .25, .6))
    soil = float(sm(.16 - p[2], 0, .16)) * .8
    moss = .5 * float(sm(nz(x * 3, math.cos(th) * 3, s * 3 + sd) - .1, 0, .3)) * float(sm(s, -.1, .4))
    return (moss, min(1.0, rot), 0.0, inner, soil)


def ring_list(lv):
    L = V['L']
    dx = LODRES[lv]['dx']
    n = max(4, int(math.ceil(L / dx)))
    xs = list(np.linspace(0, L, n + 1))
    # 兩頭斷口附近多加幾圈（參差斷口要有點可以壓）
    extra = [d for d in (.04, .10, .18, .28) if d < DELTA and dx > .06]
    xs += extra + [L - d for d in extra]
    return sorted(set(round(float(x), 4) for x in xs))


def trunk(mb, lv):
    ns = LODRES[lv]['ns']
    xs = ring_list(lv)
    ths = [3 * math.pi / 2 + 2 * math.pi * j / ns for j in range(ns)]      # 接縫在正下方（埋在土裡）
    rings = []
    for x in xs:
        ring = []
        for j, th in enumerate(ths):
            xm = xmap(x, th)
            p = pt(xm, th)
            ring.append(mb.v(p, trunk_w(xm, th, p)))
        rings.append(ring)
    Rm = V['R']
    for i in range(len(xs) - 1):
        a, b = rings[i], rings[i + 1]
        for j in range(ns):
            j1 = (j + 1) % ns
            va, vb = Rm * 2 * math.pi * j / ns, Rm * 2 * math.pi * (j + 1) / ns
            ua = [mb.V[a[j]][0], mb.V[a[j1]][0], mb.V[b[j1]][0], mb.V[b[j]][0]]
            mb.f((a[j], a[j1], b[j1], b[j]), [(ua[0], va), (ua[1], vb), (ua[2], vb), (ua[3], va)], 0)      # 面朝外
    for e in (0, 1):
        ring = rings[0] if e == 0 else rings[-1]
        kind = V['ends'][e]
        if kind == 'hollow':
            hollow_end(mb, lv, e, ring, ths)
        else:
            broken_cap(mb, lv, e, ring, ths, kind)
            if kind == 'torn':
                splinters(mb, lv, e)
    return rings, xs, ths


def broken_cap(mb, lv, e, ring, ths, kind):
    """碎斷口／撕裂斷口：從外圈往中心收，斷面凹凸（不是一個平面、也不是收圓）。"""
    sg = -1 if e == 0 else 1
    P = np.array([mb.V[i] for i in ring])
    xe = P[:, 0].mean()
    c = np.array((xe + sg * V['R'] * .05, P[:, 1].mean(), P[:, 2].mean() + V['R'] * .05))
    fr = (.74, .48, .22) if lv < 2 else (.45,)
    sd = V['seed'] + 31 * e
    w = (0, .2, .8, 0, 0) if kind == 'torn' else (0, .75, .3, 0, 0)
    prev = ring
    for k, f in enumerate(fr):
        cur = []
        for j, i0 in enumerate(ring):
            q = c + (P[j] - c) * f
            q[0] = P[j][0] * f + c[0] * (1 - f) + sg * V['R'] * .09 * nz(q[1] * 4, q[2] * 4, sd + k)
            cur.append(mb.v(q, w))
        _strip(mb, prev, cur, e, kind=2)
        prev = cur
    cv = mb.v(c + np.array((sg * V['R'] * .04 * nz(sd, 1, 1), 0, 0)), w)
    n = len(prev)
    for j in range(n):
        j1 = (j + 1) % n
        tri = (prev[j1], prev[j], cv) if e == 0 else (prev[j], prev[j1], cv)
        mb.f(tri, [_puv(mb, t) for t in tri], 2)


def _puv(mb, i):
    p = mb.V[i]
    return (p[1], p[2])


def _strip(mb, a, b, e, kind):
    n = len(a)
    for j in range(n):
        j1 = (j + 1) % n
        q = (a[j1], a[j], b[j], b[j1]) if e == 0 else (a[j], a[j1], b[j1], b[j])
        mb.f(q, [_puv(mb, t) for t in q], kind)


def hollow_end(mb, lv, e, ring, ths):
    """空心洞口：外殼斷面一圈圈年輪往裡退成台階、內壁往裡越深越暗、最裡面收口。"""
    sg = -1 if e == 0 else 1
    L = V['L']
    ns = len(ths)
    steps = ((.0, .0), (.32, .0), (.32, .025), (.62, .025), (.62, .05), (1.0, .05)) if lv < 2 else ((0, 0), (1.0, .04))
    rim_w = (0, .45, .55, 0, 0)
    outer = [np.array(mb.V[i]) for i in ring]
    prev = ring
    inner_first = None
    for k, (q, dxs) in enumerate(steps[1:], 1):
        cur = []
        for j, th in enumerate(ths):
            po = outer[j]
            x = po[0] - sg * (dxs + .01 * nz(j * .7, k, V['seed']))
            ro = rad(x, th)
            r = ro - WALL * q
            p = np.array((x, yc(x) + r * math.cos(th), zc(x) + r * math.sin(th)))
            cur.append(mb.v(p, rim_w if q < 1 else (0, .2, 0, .8, 0)))
        # 年輪：UV 繞圈＝u，木紋（纖維貼圖的條紋）就變成一圈圈
        for j in range(ns):
            j1 = (j + 1) % ns
            qd = (prev[j], prev[j1], cur[j1], cur[j]) if e == 1 else (prev[j1], prev[j], cur[j], cur[j1])
            mb.f(qd, [_ruv(mb, t) for t in qd], 2)
        prev = cur
        inner_first = cur
    # 內壁：從洞口往裡 HOLLOW_D
    x0 = np.mean([mb.V[i][0] for i in inner_first])
    nseg = max(3, int(HOLLOW_D / LODRES[lv]['dx'] * .6))
    last = inner_first
    for k in range(1, nseg + 1):
        f = k / nseg
        cur = []
        for j, th in enumerate(ths):
            p0 = np.array(mb.V[inner_first[j]])
            x = p0[0] - sg * HOLLOW_D * f
            r = max(.25 * R_at(x), rad(x, th) - WALL * (1 + .5 * f)) * (1 - .25 * f ** 2)
            r *= 1 + .05 * nz(x * 3, th, V['seed'] + 2)
            p = np.array((x, yc(x) + r * math.cos(th), zc(x) + .02 + r * math.sin(th)))
            cur.append(mb.v(p, (0, .15, 0, 1.0, 0)))
        Rm = V['R']
        for j in range(ns):
            j1 = (j + 1) % ns
            qd = (last[j], last[j1], cur[j1], cur[j]) if e == 1 else (last[j1], last[j], cur[j], cur[j1])
            mb.f(qd, [(mb.V[t][0], Rm * 2 * math.pi * ((j + (1 if t in (last[j1], cur[j1]) else 0)) / ns)) for t in qd], 3)
        last = cur
    xe = np.mean([mb.V[i][0] for i in last]) - sg * .25
    cv = mb.v((xe, yc(xe), zc(xe) + .02), (0, .2, 0, 1.0, 0))
    for j in range(ns):
        j1 = (j + 1) % ns
        tri = (last[j], last[j1], cv) if e == 1 else (last[j1], last[j], cv)
        mb.f(tri, [_puv(mb, t) for t in tri], 3)


def _ruv(mb, i):
    p = mb.V[i]
    x = p[0]
    dy, dz = p[1] - yc(x), p[2] - zc(x)
    a = math.atan2(dz, dy)
    r = math.hypot(dy, dz)
    return (a * r, r + x * .3)


def splinters(mb, lv, e):
    """撕裂端：一大束長短不一、往上翹的木纖維（扁長條、尖端收尖，根部埋進斷口）。"""
    if lv == 2:
        n = 7
    else:
        n = 30 if lv == 0 else 16
    R = random.Random(V['seed'] + 77)
    sg = -1 if e == 0 else 1
    L = V['L']
    xe = 0.0 if e == 0 else L
    for k in range(n):
        th = U(R, .55, math.pi - .55) if R.random() < .85 else U(R, math.pi + .4, 2 * math.pi - .4)
        rr = V['R'] * U(R, .30, .92)
        if math.sin(th) < -.3:
            rr *= .7
        x0 = xe - sg * (cut(e, th) + U(R, .05, .20))
        base = np.array((x0, yc(x0) + rr * math.cos(th), zc(x0) + rr * math.sin(th)))
        up = U(R, .30, .72) * (1.0 if math.sin(th) > .2 else .45)      # 一片片厚木條往上翹（參考圖 B 右端像一道往上的斜坡）
        yaw = U(R, -.15, .15) + .15 * math.cos(th) * -sg
        d = np.array((sg * math.cos(up) * math.cos(yaw), math.sin(yaw) * math.cos(up), math.sin(up)))
        d /= np.linalg.norm(d)
        ln = U(R, .25, .75) + (.45 if math.sin(th) > .3 else 0) * R.random() ** 2
        ln *= V['R'] / .48
        w = U(R, .08, .20) * V['R'] / .48
        tk = U(R, .03, .06)
        side = np.cross(d, (0, 0, 1.0))
        side /= np.linalg.norm(side) + 1e-9
        rd = np.cross(side, d)
        tw = U(R, .5, .9) * R.choice((-1, 1))                     # 寬面轉向側面（不然平視只看到木條的窄邊）
        side, rd = side * math.cos(tw) + rd * math.sin(tw), -side * math.sin(tw) + rd * math.cos(tw)
        segs = 4 if lv == 0 else 2
        rings = []
        for s_ in range(segs + 1):
            t = s_ / segs
            p = base + d * ln * t + rd * (ln * .12 * t * t)                   # 往上彎一點
            ww, tt = w * (1 - .45 * t ** 1.3) * .5, tk * (1 - .6 * t) * .5
            rings.append([mb.v(p + side * a * ww + rd * b * tt, (0, 0, 1.0, 0, 0)) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
        tip = mb.v(base + d * ln * 1.05 + rd * ln * .13, (0, 0, 1.0, 0, 0))
        for s_ in range(segs):
            a, b = rings[s_], rings[s_ + 1]
            for j in range(4):
                j1 = (j + 1) % 4
                mb.f((b[j], b[j1], a[j1], a[j]), [(ln * (s_ + 1) / segs, j * w * .5), (ln * (s_ + 1) / segs, (j + 1) * w * .5), (ln * s_ / segs, (j + 1) * w * .5), (ln * s_ / segs, j * w * .5)], 2)
        a = rings[-1]
        for j in range(4):
            j1 = (j + 1) % 4
            mb.f((a[j1], a[j], tip), [(ln, (j + 1) * w * .5), (ln, j * w * .5), (ln * 1.15, (j + .5) * w * .5)], 2)


def blanket(mb, lv):
    """有厚度的苔毯：照 moss_t 的遮罩在頂上鋪一層，邊緣塞進樹皮底下；一舌舌往兩側垂。"""
    L = V['L']
    st = LODRES[lv]['bl']
    nx = int(L / st) + 1
    xs = np.linspace(0.02, L - .02, nx)
    nth = int(4.6 * V['R'] / st) + 1
    ths = np.linspace(math.pi / 2 - 2.3, math.pi / 2 + 2.3, nth)
    grid = {}
    T = np.zeros((nx, nth))
    M = np.zeros((nx, nth))
    for i, x in enumerate(xs):
        for j, th in enumerate(ths):
            T[i, j], M[i, j] = moss_t(x, th)
    for i in range(nx - 1):
        for j in range(nth - 1):
            q = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            if max(M[a, b] for a, b in q) <= 0:
                continue
            ids = []
            for a, b in q:
                if (a, b) not in grid:
                    x, th = float(xs[a]), float(ths[b])
                    xm = xmap(x, th)
                    r = rad(xm, th) + T[a, b] - (.008 if M[a, b] <= .02 else 0)
                    grid[(a, b)] = mb.v(pt(xm, th, r), (1.0, 0, 0, 0, 0))
                ids.append(grid[(a, b)])
            Rm = V['R']
            ids, q = ids[::-1], q[::-1]                            # 面朝外
            mb.f(ids, [(float(xs[a]), float(ths[b]) * Rm) for a, b in q], 4)
    skirt(mb, xs, ths, M, grid)


def skirt(mb, xs, ths, M, grid):
    """苔毯兩側的下緣：從邊上的頂點往下、略往外垂一段（長短不齊），苔毯看起來是蓋上去、垂下來的。"""
    sd = V['seed']
    Rm = V['R']
    nx, nth = M.shape
    for side in (0, 1):
        edge = []
        for i in range(nx):
            js = [j for j in range(nth) if (i, j) in grid]
            if not js:
                edge.append(None)
                continue
            j = min(js) if side == 0 else max(js)
            th = float(ths[j])
            if math.sin(th) > .55:                             # 只有側面往下垂，頂上的邊不垂
                edge.append(None)
                continue
            out = np.array((0.0, math.cos(th), 0.0))
            h = Rm * (.10 + .22 * max(0.0, nz(xs[i] * 3.2, side * 5.0, sd + 21) + .35))
            top = np.array(mb.V[grid[(i, j)]])
            bot = top + out * .025 + np.array((0, 0, -h))
            edge.append((grid[(i, j)], mb.v(bot, (1.0, 0, 0, 0, 0)), h, th))
        for i in range(nx - 1):
            a, b = edge[i], edge[i + 1]
            if a is None or b is None:
                continue
            ids = [a[0], b[0], b[1], a[1]]
            if side == 1:
                ids = ids[::-1]
            u0, u1 = float(xs[i]), float(xs[i + 1])
            uv = [(u0, a[3] * Rm), (u1, b[3] * Rm), (u1, b[3] * Rm - b[2]), (u0, a[3] * Rm - a[2])]
            mb.f(ids, uv[::-1] if side == 1 else uv, 4)


def mound_h(x, y):
    """落葉土的高度：貼著樹幹最高（爬上側面蓋掉底線），往外降到地面下。"""
    L = V['L']
    xc = min(max(x, 0.0), L)
    dy = abs(y - yc(xc)) - R_at(xc) * .98
    dx = max(-x, x - L, 0.0)
    d = math.hypot(dx, max(dy, 0.0)) if (dx > 0 or dy > 0) else max(dy, -x, x - L)
    mg = V['margin'] * (1 + .35 * nz(x * .9, y * .9, V['seed'] + 13))
    f = float(sm(mg - d, 0, mg)) ** 1.15
    n = .70 + .30 * nz(x * 2.3, y * 2.3, 5.1)
    return V['mound'] * f * n - .025


def mound(mb, lv):
    L = V['L']
    sp = LODRES[lv]['mg']
    mg = V['margin'] * 1.4
    lo = np.array((-mg, -V['R'] * 1.1 - mg))
    hi = np.array((L + mg, V['R'] * 1.1 + mg + V['bend']))
    nx, ny = int((hi[0] - lo[0]) / sp) + 1, int((hi[1] - lo[1]) / sp) + 1
    hs = np.zeros((nx, ny))
    under = np.zeros((nx, ny), bool)
    for ix in range(nx):
        for iy in range(ny):
            x, y = lo[0] + ix * sp, lo[1] + iy * sp
            hs[ix, iy] = mound_h(x, y)
            xc = min(max(x, 0.0), L)
            under[ix, iy] = .25 < x < L - .25 and abs(y - yc(xc)) < R_at(xc) * .72       # 壓在樹幹正下方、看不到
    grid = {}
    for ix in range(nx - 1):
        for iy in range(ny - 1):
            q = [(ix, iy), (ix + 1, iy), (ix + 1, iy + 1), (ix, iy + 1)]
            if max(hs[a, b] for a, b in q) < -.006 or all(under[a, b] for a, b in q):
                continue
            ids = []
            for a, b in q:
                if (a, b) not in grid:
                    x, y = lo[0] + a * sp, lo[1] + b * sp
                    h = max(hs[a, b], -.025)
                    mo = .7 * float(sm(nz(x * 1.8, y * 1.8, 3.3) + .05, 0, .3))
                    ro = .45 * float(sm(nz(x * 3.1, y * 3.1, 8.8), .1, .45))
                    grid[(a, b)] = mb.v((x, y, h), (mo, ro, 0, 0, 1.0))
                ids.append(grid[(a, b)])
            mb.f(ids, [(lo[0] + a * sp, lo[1] + b * sp) for a, b in q], 1)


def lump(mb, c, size, R, sub, w):
    """一塊碎掉的朽木塊／土塊：壓扁、扭一下的多面體（不是方塊）。"""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    sx, sy, sz = size * U(R, .8, 1.3), size * U(R, .6, 1.0), size * U(R, .40, .70)
    rot = Matrix.Rotation(U(R, 0, 6.3), 3, 'Z') @ Matrix.Rotation(U(R, -.4, .4), 3, 'X')
    off = R.random() * 50
    ids = {}
    for v in bm.verts:
        p = v.co
        k = 1 + .28 * nz(p.x * 1.7 + off, p.y * 1.7, p.z * 1.7)
        q = rot @ Vector((p.x * sx * k, p.y * sy * k, p.z * sz * k))
        ids[v.index] = mb.v((c[0] + q.x, c[1] + q.y, c[2] + q.z), w)
    for f in bm.faces:
        idx = [ids[v.index] for v in f.verts]
        n = f.normal
        uvs = []
        for i in idx:
            p = mb.V[i]
            if abs(n.z) > .6:
                uvs.append((p[0], p[1]))
            elif abs(n.x) > abs(n.y):
                uvs.append((p[1], p[2]))
            else:
                uvs.append((p[0], p[2]))
        mb.f(idx, uvs, 5)
    bm.free()


def debris_plan():
    """碎木塊、樹皮片的位置（各級 LOD 共用同一份，再照比例抽）。"""
    R = random.Random(V['seed'] + 5)
    L = V['L']
    out = []
    n = int(L * 24)
    for k in range(n * 4):
        if len(out) >= n:
            break
        x = U(R, -.25, L + .25)
        side = R.choice((-1, 1)) if R.random() < .8 else (1 if R.random() < .3 else -1)
        xc = min(max(x, 0.0), L)
        y = yc(xc) + side * R_at(xc) * U(R, .92, 1.45)
        if x < 0 or x > L:
            y = yc(xc) + U(R, -.8, .8) * R_at(xc)
            if (x < 0 and V['ends'][0] == 'hollow'):
                y = yc(xc) + side * R_at(xc) * U(R, .6, 1.1)
        size = U(R, .05, .16) * (V['R'] / .48)
        z = mound_h(x, y) + size * U(R, .05, .25)
        kind = 'lump' if R.random() < .8 else 'flake'
        if any(abs(x - tc * L) < hl * 1.1 and y < yc(xc) for tc, hl, dep in V['cavity']):
            continue                                                 # 凹洞前面留空（正面看得到洞）
        out.append(dict(c=(x, y, z), size=size, kind=kind, seed=R.randint(0, 10 ** 6), tag=R.random()))
    return out


def flake(mb, d):
    """地上一片剝落、微捲的樹皮。"""
    R = random.Random(d['seed'])
    w, l = d['size'] * U(R, 1.1, 1.7), d['size'] * U(R, 1.8, 2.8)
    a = U(R, 0, 6.3)
    ca, sa = math.cos(a), math.sin(a)
    c = d['c']
    ids = []
    nu, nv = 4, 2
    for i in range(nu + 1):
        row = []
        for j in range(nv + 1):
            u, v = (i / nu - .5) * l, (j / nv - .5) * w
            z = .012 + .25 * w * (2 * j / nv - 1) ** 2 + .02 * math.sin(i / nu * math.pi)
            row.append(mb.v((c[0] + u * ca - v * sa, c[1] + u * sa + v * ca, c[2] - d['size'] * .2 + z), (0, .25, 0, 0, 0)))
        ids.append(row)
    for i in range(nu):
        for j in range(nv):
            q = (ids[i][j], ids[i + 1][j], ids[i + 1][j + 1], ids[i][j + 1])
            mb.f(q, [((i) / nu * l, j / nv * w), ((i + 1) / nu * l, j / nv * w), ((i + 1) / nu * l, (j + 1) / nv * w), (i / nu * l, (j + 1) / nv * w)], 5)


def plates_plan():
    """側面一片片鬆脫、微微翹起的灰褐樹皮板（參考圖苔毯底下、褐腐之間那些灰色鱗片狀的板）。"""
    R = random.Random(V['seed'] + 41)
    L = V['L']
    out = []
    n = int(L * 3.2)
    for k in range(n * 6):
        if len(out) >= n:
            break
        side = -1 if R.random() < .7 else 1
        x = U(R, .35, L - .35)
        th = (math.pi + U(R, -.55, .20)) if side < 0 else U(R, -.20, .55)
        if moss_t(x, th)[0] > .005 or cav(x, th)[1] > .1:
            continue
        hx, ha = U(R, .16, .34), U(R, .16, .30)
        if any(abs(x - q['x']) < (hx + q['hx']) * .8 and abs(th - q['th']) < (ha + q['ha']) * .8 for q in out):
            continue
        out.append(dict(x=x, th=th, hx=hx, ha=ha, seed=R.randint(0, 10 ** 6)))
    return out


def bark_plates(mb, lv):
    if lv == 2:
        return
    nu, nv = (6, 4) if lv == 0 else (3, 2)
    for q in PLATES:
        sd = q['seed'] % 1000
        ids = []
        for i in range(nu + 1):
            row = []
            for j in range(nv + 1):
                a, b = 2 * i / nu - 1, 2 * j / nv - 1
                k = 1 + .25 * nz(a * 1.3, b * 1.3, sd)                  # 邊緣不規則
                x, th = q['x'] + a * q['hx'] * k, q['th'] + b * q['ha'] * k
                e = max(abs(a), abs(b)) ** 2
                xm = xmap(x, th)
                r = rad(xm, th) + .010 + .028 * e * (.6 + .4 * nz(a * 2, b * 2, sd + 3))     # 邊緣往外翹
                row.append(mb.v(pt(xm, th, r), (0, .08, 0, 0, 0)))
            ids.append(row)
        Rm = V['R']
        for i in range(nu):
            for j in range(nv):
                f = (ids[i][j], ids[i][j + 1], ids[i + 1][j + 1], ids[i + 1][j])
                mb.f(f, [(mb.V[t][0] * 1.3, (q['th'] + (2 * (jj) / nv - 1) * q['ha']) * Rm * 1.3) for t, jj in zip(f, (j, j + 1, j + 1, j))], 6)


def body(lv):
    mb = MB()
    trunk(mb, lv)
    blanket(mb, lv)
    bark_plates(mb, lv)
    mound(mb, lv)
    keep = LODRES[lv]['deb']
    for d in DEBRIS:
        if d['tag'] > keep:
            continue
        R = random.Random(d['seed'])
        if d['kind'] == 'lump':
            rw = U(R, .55, 1.0)
            lump(mb, d['c'], d['size'], R, 1 if lv < 2 else 0, (0, rw, 0, 0, .2))
        elif lv < 2:
            flake(mb, d)
    o = to_object(mb, f'{NAMES[V["v"]]}_LOD{lv}')
    gone = hide_faces(o, mb)
    print('LOD', lv, 'hidden faces removed', gone)
    finish(o, mb, lv)
    return o


def to_object(mb, name):
    me = bpy.data.meshes.new(name)
    me.from_pydata(mb.V, [], mb.F)
    me.validate(clean_customdata=False)
    uv = np.array([u for f in mb.UV for u in f], np.float32)
    me.uv_layers.new(name='UVMap').data.foreach_set('uv', uv.ravel())
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(layer_mat_v2())
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def hide_faces(o, mb):
    """看不到的面刪掉：埋在土下的樹幹、被苔毯蓋住的樹皮、壓在落葉土下的樹幹底。"""
    me = o.data
    co = np.array(mb.V)
    hid = np.zeros(len(co), bool)
    for i, p in enumerate(co):
        if p[2] < -.03:
            hid[i] = True
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    dead = []
    for f in bm.faces:
        k = mb.fk[f.index]
        if k == 0:
            vs = [v.index for v in f.verts]
            if all(hid[i] for i in vs):
                dead.append(f)
                continue
            ok = True
            for i in vs:
                p = co[i]
                x = p[0]
                th = math.atan2(p[2] - zc(x), p[1] - yc(x))
                t, _ = moss_t(x, th)
                if t < .014 and p[2] > mound_h(x, p[1]) + .01:
                    ok = False
                    break
            if ok:
                dead.append(f)
    bmesh.ops.delete(bm, geom=dead, context='FACES_ONLY')
    loose = [v for v in bm.verts if not v.link_faces]
    keep = np.ones(len(co), bool)
    for v in loose:
        keep[v.index] = False
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bm.to_mesh(me)
    bm.free()
    mb.W = [w for w, k in zip(mb.W, keep) if k]
    return len(dead)


def _loops(me):
    vi = np.empty(len(me.loops), np.int32)
    me.loops.foreach_get('vertex_index', vi)
    return vi


def vertex_ao(o, rays=12, dist=.35):
    me = o.data
    n = len(me.vertices)
    co = np.empty(n * 3, np.float32)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    vn = np.empty(n * 3, np.float32)
    me.vertices.foreach_get('normal', vn)
    vn = vn.reshape(-1, 3)
    tree = BVHTree.FromPolygons([Vector(p) for p in co], [tuple(p.vertices) for p in me.polygons])
    rs = np.random.RandomState(3)
    dirs = rs.randn(rays, 3)
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    ao = np.ones(n)
    for i in range(n):
        nn = vn[i]
        hit = 0.0
        for d in dirs:
            if d @ nn < 0:
                d = -d
            dd = Vector(d * .85 + nn * .15).normalized()
            if tree.ray_cast(Vector(co[i] + nn * .004), dd, dist)[0] is not None:
                hit += 1
            elif co[i][2] + dd.z * dist < -.01:
                hit += .5
        ao[i] = 1 - .70 * hit / rays
    return ao


def finish(o, mb, lv):
    me = o.data
    W = np.array(mb.W)
    s = W[:, :4].sum(1, keepdims=True)
    W[:, :4] = np.where(s > 1, W[:, :4] / np.maximum(s, 1e-6), W[:, :4])
    ao = vertex_ao(o) if lv < 2 else np.ones(len(W))
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    ao = ao * (.60 + .40 * sm(co[:, 2], -.02, .18))
    ao = np.where(W[:, 2] > .7, np.maximum(ao, .82), ao)
    ao = np.where(W[:, 0] > .95, np.maximum(ao, .85), ao)          # 苔毯：一團團的苔互相遮，整片會暗成橄欖色          # 撕裂的木條彼此靠得近，AO 會整片黑掉
    ao = ao * (1 - .85 * W[:, 3])                                  # 凹洞、空心內壁：壓暗，平視看得出是洞
    vi = _loops(me)
    ca = me.color_attributes.new('Layers', 'FLOAT_COLOR', 'CORNER')
    ca.data.foreach_set('color', W[vi, :4].astype(np.float32).ravel())
    me.color_attributes.active_color = ca
    me.uv_layers.new(name='Extra').data.foreach_set('uv', np.stack([W[vi, 4], ao[vi]], -1).astype(np.float32).ravel())
    me.uv_layers.active_index = 0
    for l in me.uv_layers:
        l.active_render = l.name == 'UVMap'


# ---------------------------------------------------------------- 植物卡（層孔菌、蕨、小苗、垂苔、小褐蕈、發光小蕈、落葉）
class Cards:
    def __init__(self):
        self.V, self.F, self.UV, self.tag = [], [], [], []

    def mesh(self, verts, faces, uvs, tag):
        o = len(self.V)
        self.V += [tuple(map(float, p)) for p in verts]
        self.UV += [tuple(map(float, u)) for u in uvs]
        for f in faces:
            self.F.append(tuple(o + i for i in f))
            self.tag.append(tag)

    def quad(self, pts, uvs, tag):
        self.mesh(pts, [(0, 1, 2, 3)], uvs, tag)

    def upright(self, base, h, w, rect, yaw, tag, lean=(0, 0, 0), cross=True):
        u0, v0, u1, v1 = rect
        base = Vector(base)
        up = (Vector((0, 0, 1)) + Vector(lean)).normalized()
        for k in range(2 if cross else 1):
            a = yaw + k * math.pi / 2
            side = Vector((math.cos(a), math.sin(a), 0))
            self.quad([base - side * w / 2, base + side * w / 2, base + side * w / 2 + up * h, base - side * w / 2 + up * h],
                      [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], tag)

    def flat(self, p, n, yaw, w, h, rect, tag, curl=.012):
        n = Vector(n).normalized()
        a = (Matrix.Rotation(yaw, 3, n) @ n.orthogonal().normalized()).normalized()
        b = n.cross(a)
        u0, v0, u1, v1 = rect
        p = Vector(p)
        verts, uvs = [], []
        for k, (c, l) in enumerate(zip([p - a * h * .5, p, p + a * h * .5], [curl, 0, curl * 1.4])):
            for sgn in (-.5, .5):
                verts.append(c + n * l + b * (w * sgn) + n * (abs(sgn) * curl * .6))
                uvs.append((u0 + (u1 - u0) * (sgn + .5), v0 + (v1 - v0) * k / 2))
        self.mesh(verts, [(0, 1, 3, 2), (2, 3, 5, 4)], uvs, tag)

    def obj(self, name, keep, seed):
        rs = random.Random(seed)
        tags = sorted(set(self.tag))
        kept = {t for t in tags if t < 0 or rs.random() < keep}
        F = [f for f, t in zip(self.F, self.tag) if t in kept]
        used = sorted({i for f in F for i in f})
        mp = {v: k for k, v in enumerate(used)}
        me = bpy.data.meshes.new(name)
        me.from_pydata([self.V[i] for i in used], [], [tuple(mp[i] for i in f) for f in F])
        uvl = me.uv_layers.new(name='UVMap')
        for lp in me.loops:
            uvl.data[lp.index].uv = self.UV[used[lp.vertex_index]]
        me.materials.append(lib8()['plant_material']())
        o = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(o)
        return o


def surf_front(x, z, side):
    """樹幹側面（side −1 正面、+1 背面）在高度 z 的那一點和朝外方向。"""
    r = R_at(x)
    s = max(-.95, min(.95, (z - zc(x)) / r))
    th = (math.pi - math.asin(s)) if side < 0 else math.asin(s)
    for _ in range(3):
        rr = rad(x, th)
        s = max(-.95, min(.95, (z - zc(x)) / rr))
        th = (math.pi - math.asin(s)) if side < 0 else math.asin(s)
    return pt(x, th), np.array((0, math.cos(th), 0)) / max(abs(math.cos(th)), 1e-3)


def bracket_shelf(C, base, out, w, D, th, rect, lv, seed):
    """一片層孔菌：半圓托盤，貼樹幹那邊埋進去，邊緣微波、略往上翹；上面照圖集的環帶，下面淺奶油色。"""
    R = random.Random(seed)
    up = np.array((0, 0, 1.0))
    X = np.cross(up, out)
    X /= np.linalg.norm(X)
    nphi = (10, 6, 4)[lv]
    nrho = (4, 3, 2)[lv]
    rise, droop = 0.0, D * U(R, .28, .42)
    tilt = U(R, -.10, .10)
    u0, v0, u1, v1 = rect
    verts, uvs, faces = [], [], []
    rhos = [.12 + .88 * k / nrho for k in range(nrho + 1)]
    ph = R.random() * 6
    top, bot = [], []
    for k, rho in enumerate(rhos):
        rt, rb = [], []
        for j in range(nphi + 1):
            phi = math.pi * j / nphi
            wav = 1 + .07 * math.sin(phi * 6 + ph) * rho
            loc = X * (rho * w * .5 * math.cos(phi) * wav) + out * (rho * D * math.sin(phi) * wav)
            loc = loc + up * (tilt * rho * D * math.cos(phi))
            ht = th * (1 - rho) ** .8 * .75 + rise * rho - droop * rho ** 1.6 + .004
            hb = th * (1 - rho) ** .8 * .45 + .006
            rt.append(len(verts))
            verts.append(base + loc + up * ht)
            uvs.append((u0 + (u1 - u0) * (.5 + .40 * rho * math.cos(phi)), v0 + (v1 - v0) * (.05 + .90 * rho * math.sin(phi))))
            rb.append(len(verts))
            verts.append(base + loc - up * (hb + droop * rho ** 1.6 * .85))      # 底面跟著往下垂（邊緣上下面合在一起）
            uvs.append((u0 + (u1 - u0) * .5, v0 + (v1 - v0) * .965))
        top.append(rt)
        bot.append(rb)
    for k in range(nrho):
        for j in range(nphi):
            faces.append((top[k][j + 1], top[k + 1][j + 1], top[k + 1][j], top[k][j]))
            faces.append((bot[k][j], bot[k + 1][j], bot[k + 1][j + 1], bot[k][j + 1]))
    for j in range(nphi):                                          # 邊緣一圈（薄）
        faces.append((top[-1][j + 1], bot[-1][j + 1], bot[-1][j], top[-1][j]))
    C.mesh(verts, faces, uvs, -1)


def plants(body0, lv):
    """植物卡。擺放全用同一個亂數序列（各級 LOD 擺在同一個地方），只有層孔菌的段數跟著 LOD 變。"""
    R = random.Random(V['seed'] + 7)
    rects = lib8()['rects']()
    cat = lambda c: [r['uv'] for r in rects if r['cat'] == c]
    leaves, mush, fern, drape, sap, glow, fung = cat('leaf'), cat('mush'), cat('fern'), cat('mossdrape'), cat('sapling'), cat('glow'), cat('fungus')[0]
    me = body0.data
    co = [v.co.copy() for v in me.vertices]
    tree = BVHTree.FromPolygons(co, [tuple(p.vertices) for p in me.polygons])
    C = Cards()
    L = V['L']
    tag = 0
    cnt = dict(brackets=0, ferns=0, saplings=0, drape=0, mush=0, glow=0, leaves=0)
    # 層孔菌：一叢 3–5 片，從上往下疊（上面的較大、較往外）
    for tc, side, nt in V['brackets']:
        x0 = tc * L
        z0 = zc(x0) + R_at(x0) * U(R, .05, .30)
        for k in range(nt):
            x = x0 + U(R, -.20, .20) + (k % 2) * U(R, .04, .16)
            z = z0 - k * U(R, .07, .17) * (V['R'] / .48)
            p, out = surf_front(x, z, side)
            sc = (1 - .13 * k) * U(R, .75, 1.15) * (max(V['R'], .46) / .48)
            w = U(R, .36, .52) * sc
            D = w * U(R, .55, .72)
            base = p - out * .04
            bracket_shelf(C, base, out, w, D, U(R, .07, .09) * sc, fung, lv, R.randint(0, 10 ** 6))
            cnt['brackets'] += 1

    def ground_hit(x, y):
        h = tree.ray_cast(Vector((x, y, 3)), Vector((0, 0, -1)), 6)
        return h

    # 蕨：腳邊前後、兩頭；頂上一兩株
    for k in range(V['ferns']):
        x = U(R, -.15, L + .15)
        side = -1 if k % 3 else 1
        xc = min(max(x, 0.0), L)
        y = yc(xc) + side * R_at(xc) * U(R, 1.12, 1.55)
        if side < 0 and any(abs(x - tc * L) < hl * 1.1 for tc, hl, dep in V['cavity']):
            continue
        h = ground_hit(x, y)
        if h[0] is None or h[0].z > .42:
            continue
        C.upright(h[0] - Vector((0, 0, .02)), U(R, .30, .48) * (V['R'] / .48) ** .5, U(R, .40, .58), R.choice(fern), U(R, 0, math.pi), tag,
                  lean=(0, side * U(R, .2, .45), 0))
        tag += 1
        cnt['ferns'] += 1
    # 頂上的小苗、蕨
    for k in range(V['saplings'] + 1):
        x = U(R, .12, .88) * L
        h = tree.ray_cast(Vector((x, yc(x) + U(R, -.2, .2) * V['R'], 4)), Vector((0, 0, -1)), 8)
        if h[0] is None or h[1].z < .6:
            continue
        if k == V['saplings']:
            C.upright(h[0] - Vector((0, 0, .02)), U(R, .28, .38), U(R, .36, .46), R.choice(fern), U(R, 0, math.pi), tag)
        else:
            C.upright(h[0] - Vector((0, 0, .015)), U(R, .28, .42), U(R, .24, .34), R.choice(sap), U(R, 0, math.pi), tag)
            cnt['saplings'] += 1
        tag += 1
    # 垂苔：苔毯兩側的下緣往下掛
    st = .32
    for x in np.arange(.25, L - .2, st):
        for side in (-1, 1):
            if R.random() < .35:
                continue
            xx = float(x) + U(R, -.08, .08)
            th0 = math.pi / 2 + (math.pi / 2) * (1 if side < 0 else -1) * .0
            best = None
            for th in np.linspace(math.pi / 2, math.pi / 2 - side * 1.7, 30):
                t, m = moss_t(xx, th)
                if m > 0:
                    best = th
            if best is None or abs(best - math.pi / 2) < .6:
                continue
            p = pt(xmap(xx, best), best, rad(xmap(xx, best), best) + .01)
            outd = np.array((0, math.cos(best), 0))
            outd /= np.linalg.norm(outd) + 1e-9
            hh = U(R, .16, .30) * (V['R'] / .48)
            ww = U(R, .26, .40)
            rc = R.choice(drape)
            top_ = Vector(p + outd * .012 + np.array((0, 0, .02)))
            dn = Vector((0, 0, -1)) + Vector(outd * .18)
            ax = Vector((1, 0, 0))
            u0, v0, u1, v1 = rc
            C.quad([top_ - ax * ww / 2, top_ + ax * ww / 2, top_ + ax * ww / 2 + dn * hh, top_ - ax * ww / 2 + dn * hh],
                   [(u0, v1), (u1, v1), (u1, v0), (u0, v0)], tag)
            tag += 1
            cnt['drape'] += 1
    # 小褐蕈：腳邊幾叢
    for k in range(V['mush']):
        x = U(R, .15, .85) * L
        y = yc(x) - R_at(x) * U(R, 1.00, 1.15)
        h = ground_hit(x, y)
        if h[0] is None or h[0].z > .42:
            continue
        C.upright(h[0] - Vector((0, 0, .01)), U(R, .09, .14), U(R, .10, .15), R.choice(mush), U(R, 0, math.pi), tag)
        tag += 1
        cnt['mush'] += 1
    # 發光小蕈：凹洞底、洞口裡
    spots = [(tc * L, None) for tc, hl, dep in V['cavity']]
    if V['ends'][0] == 'hollow':
        spots.append((.35, 'hollow'))
    for x, kind in spots:
        for k in range(3):
            xx = x + U(R, -.14, .14)
            if kind == 'hollow':
                p = Vector((xx, yc(xx) + U(R, -.12, .12), zc(xx) - R_at(xx) * .55))
                h = tree.ray_cast(p + Vector((0, 0, .25)), Vector((0, 0, -1)), 1.0)
            else:
                yy = yc(xx) - R_at(xx) * .80
                h = tree.ray_cast(Vector((xx, yy - .6, zc(xx) - .05)), Vector((0, 1, 0)), 1.5)
                if h[0] is not None:
                    h = tree.ray_cast(h[0] + Vector((0, -.07, .05)), Vector((0, 0, -1)), .6)
            if h[0] is None or h[1].z < .5:
                continue
            C.upright(h[0] - Vector((0, 0, .008)), U(R, .20, .28), U(R, .20, .28), R.choice(glow), U(R, 0, math.pi), tag)
            tag += 1
            cnt['glow'] += 1
    # 落葉：落葉土上、苔毯邊
    nl = int(L * 14)
    for k in range(nl * 3):
        if cnt['leaves'] >= nl:
            break
        x = U(R, -.4, L + .4)
        y = U(R, -1, 1) * (V['R'] + V['margin'])
        h = ground_hit(x, y)
        if h[0] is None or h[1].z < .5:
            continue
        if h[0].z > .30 and R.random() < .7:
            continue
        n = (h[1] + Vector((U(R, -.25, .25), U(R, -.25, .25), 0))).normalized()
        rc = R.choice(leaves)
        asp = (rc[2] - rc[0]) / max(rc[3] - rc[1], 1e-6)
        hh = U(R, .075, .12)
        C.flat(h[0] + n * .008, n, U(R, 0, 6.3), hh * asp, hh, rc, tag)
        tag += 1
        cnt['leaves'] += 1
    print('PLANTS', lv, cnt)
    return C


# ---------------------------------------------------------------- 碰撞、匯出
def collision():
    mb = MB()
    L = V['L']
    xs = np.linspace(.05, L - .05, max(3, int(L / .5) + 1))
    ns = 10
    rings = []
    for x in xs:
        x = float(x)
        r = R_at(x) * .93
        rings.append([mb.v((x, yc(x) + r * math.cos(2 * math.pi * j / ns), zc(x) + r * math.sin(2 * math.pi * j / ns))) for j in range(ns)])
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        for j in range(ns):
            j1 = (j + 1) % ns
            mb.f((a[j], b[j], b[j1], a[j1]), [(0, 0)] * 4)
    for e, ring in ((0, rings[0]), (1, rings[-1])):
        c = mb.v(np.mean([mb.V[i] for i in ring], 0))
        for j in range(ns):
            j1 = (j + 1) % ns
            mb.f((ring[j1], ring[j], c) if e == 0 else (ring[j], ring[j1], c), [(0, 0)] * 3)
    me = bpy.data.meshes.new(f'{NAMES[V["v"]]}_Collision')
    me.from_pydata(mb.V, [], mb.F)
    o = bpy.data.objects.new(me.name, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def _tri(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def _triangulate(o):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    dead = [f for f in bm.faces if f.calc_area() < 1e-10]
    if dead:
        bmesh.ops.delete(bm, geom=dead, context='FACES')
    bm.to_mesh(o.data)
    bm.free()


def _select(objs, active):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active


DEBRIS = []
PLATES = []


def run(v):
    global V, DEBRIS, PLATES
    t0 = time.time()
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    V = dict(VARIANTS[v], v=v)
    DEBRIS = debris_plan()
    PLATES = plates_plan()
    asset = NAMES[v]
    lods, bodies = {}, {}
    for lv in (0, 1, 2):
        b = body(lv)
        _triangulate(b)
        bodies[lv] = b
        print('LOD', lv, 'body', _tri(b), round(time.time() - t0), 's')
    for lv in (0, 1, 2):
        C = plants(bodies[0], lv)
        d = C.obj(f'{DET}_LOD{lv}', PLANT_KEEP[lv], lv)
        _triangulate(d)
        lods[lv] = [bodies[lv], d]
        print('LOD', lv, 'detail', _tri(d))
    col = collision()
    _triangulate(col)
    col.display_type = 'WIRE'
    root = bpy.data.objects.new(asset, None)
    bpy.context.scene.collection.objects.link(root)
    for o in [o for lst in lods.values() for o in lst] + [col]:
        o.data.name = o.name
        o.parent = root
    piv = _exec(ROOTS + '/dr_pivot.py', 'dr_pivot')
    c = piv['to_bottom_centre'](root, bodies[0])
    exp = f'{ROOT}/art/exports/d2-logs-b/{asset}'
    os.makedirs(exp, exist_ok=True)
    allm = [o for lst in lods.values() for o in lst] + [col]
    _select(allm + [root], root)
    bpy.ops.export_scene.fbx(filepath=f'{exp}/{asset}_{VER}.fbx', use_selection=True, object_types={'MESH', 'EMPTY'},
                             apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', bake_space_transform=True,
                             axis_forward='-Z', axis_up='Y', mesh_smooth_type='FACE', use_mesh_modifiers=True, colors_type='LINEAR',
                             add_leaf_bones=False, bake_anim=False, path_mode='STRIP', embed_textures=False)
    try:
        _select(lods[0] + [root], root)
        bpy.ops.export_scene.gltf(filepath=f'{exp}/{asset}_{VER}.glb', use_selection=True, export_format='GLB', export_yup=True)
    except Exception as e:
        print('glb', e)
    col.hide_render = True
    info = {lv: {o.name: _tri(o) for o in lst} for lv, lst in lods.items()}
    info['collision'] = _tri(col)
    bpy.context.view_layer.update()
    mn = np.min([np.array(o.matrix_world @ Vector(b)) for o in lods[0] for b in o.bound_box], 0)
    mx = np.max([np.array(o.matrix_world @ Vector(b)) for o in lods[0] for b in o.bound_box], 0)
    mi = dict(asset=asset, version=VER, variant=v, spec=dict(L=V['L'], R=V['R']), tris=info, bounds_min_m=np.round(mn, 3).tolist(),
              bounds_max_m=np.round(mx, 3).tolist(), dimensions_m=np.round(mx - mn, 3).tolist(), build_origin_m=list(c),
              materials=['M_DR08_Layered_v002', 'M_DR08_Plants'], textures='DR08_Shared/Textures（1024 分層貼圖 12 張＋苔、纖維、樹皮 v002 顏色圖 3 張、植物圖集 2048）')
    json.dump(mi, open(f'{exp}/model_info_{VER}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('TRIS', json.dumps(info))
    print('DIMS', mi['dimensions_m'], mi['bounds_min_m'])
    os.makedirs(HERE + '/blend', exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=f'{HERE}/blend/{asset}_{VER}.blend', copy=True)
    print('GAME_DONE', asset, round(time.time() - t0), 's')


if __name__ == '__main__' and '--' in sys.argv:
    a = sys.argv[sys.argv.index('--') + 1:]
    try:
        run(a[0] if a else 'C')
    except Exception:
        traceback.print_exc()
        sys.exit(1)
