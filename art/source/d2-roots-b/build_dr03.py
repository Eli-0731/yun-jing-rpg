# DR03 根牆收頭與交叉件（高模）：沿用 build_dr02.py 的整套根做法（內芯＋一股股扭絞的根＋側根＋苔），只換控制點。
#   E 收頭（RootEnd）：根牆在路邊斷開的地方，DR02 粗頭不能是一面陡的切面。收頭件從牆的粗頭底下鑽出來，
#     約 2 m 高，往外彎下去分成八根粗細不一的根指，向前、向兩側攤開（約 6 m 寬）鑽進土裡，根指之間有暗縫
#     （設定圖 V5 左邊那種根腳；Codex 三視圖 art/references/DR03/v001/DR03-end-threeview.png）。
#     Socket_Wall 對到 DR02 的 Socket_Head（位置、方向都對齊），收頭就往牆的反方向攤出去。
#   X 交叉件（RootCross）：兩條根約 55° 交叉，下面一條貼地（約 0.9 m 高），上面一條細一點，拱起來壓在它上面，
#     四個端都鑽進土裡；上面那條頂上有幾條細根蜿蜒、兩條細根橫著箍住它往下抓進土裡
#     （設定圖 V1 外圈、V5 右邊；Codex 三視圖 DR03-cross-threeview.png）。Socket_Joint 對到 DR02 的接頭（下面那條順著牆）。
# 根沿 +X 走、正面 -Y、原點在底部中心，z = 0 是地面。
# 在 Blender 裡：b = 載入此檔; b['set_variant']('E'); b['build'](quick=True)
import os

_HERE = os.path.dirname(os.path.abspath(globals().get('__file__', 'D:/yun-jing-d2-roots/art/source/d2-roots-b/build_dr03.py')))
_src = os.path.join(_HERE, 'build_dr02.py')
exec(compile(open(_src, encoding='utf-8').read(), _src, 'exec'), globals())

# 控制點 (沿長度 s m, 前後 y m, 中心高 z m, 半寬 r m, 扁度 fl)，和 DR02 一樣。
_C = .574, .819          # 交叉件上面那條根的方向（和 X 軸夾 55°）


def _over(u, z, r, fl, w=0.0):
    """上面那條根上 u 公尺處（w：往側邊彎多少，平面上不是一條直線）。"""
    return (u * _C[0] - w * _C[1], u * _C[1] + w * _C[0], z, r, fl)


def _finger(th, L, r0, wig, seed):
    """收頭的一根根指：從分叉處（s = 1.2，還在約 1.5 m 高）往 th 度方向彎下去，L 公尺後鑽進土裡；平面上微微彎。
    側面是一道往下凹的長坡（設定圖：從牆邊 2 m 高一路斜到地面，根指在半腰才分開），不是在牆邊就塌到地面。"""
    out = []
    for f, z, rf in ((.0, .80, 1.0), (.15, .62, .92), (.33, .42, .80), (.55, .22, .66), (.78, .08, .50), (1.0, -.42, .30)):
        d = .25 + (L - .25) * f
        a = math.radians(th * (1 - .30 * f))          # 兩側的根指越往外越往前彎（設定圖俯視不是放射狀的星形）
        c, s_ = math.cos(a), math.sin(a)
        w = wig * math.sin(f * 3.4 + seed) * f
        out.append((1.2 + d * c - w * s_, d * s_ + w * c, z, max(r0 * rf, .11), 1.40 - .25 * f))
    return tuple(out)


_FINGERS = ((0, 4.9, .52, .30), (-22, 4.5, .48, -.25), (21, 4.3, .47, .28), (-46, 3.9, .43, .22),
            (44, 3.8, .44, -.24), (-70, 3.2, .36, -.18), (68, 3.3, .37, .20), (-9, 3.1, .32, -.30))

VARIANTS.update({
    'E': dict(name='RootEnd', L=6.5, seed=41, turns=.35, plants=.9, sides=0, head_roots=False, fork_s=1.2,
              # 粗頭（s < 0）從土裡鑽出來、藏在 DR02 粗頭底下；s = 0 是牆的粗頭露出土的地方（Socket_Wall），頂高約 2 m
              spine=((-1.9, .00, -.25, 1.00, 1.30), (-.7, .00, .55, 1.02, 1.38), (.3, .00, .66, .98, 1.36), (1.0, .00, .74, .88, 1.32)),
              branches=tuple((1 if th >= 0 else -1, _finger(th, L, r0, w, k)) for k, (th, L, r0, w) in enumerate(_FINGERS)),
              strands=24, peel=0, lift_gap=False, branch_sides=0),
    # v001 第二輪：從人眼高看像一堆棍子 → 根股收緊成兩條完整的圓木（rho／dk）、側根各剩一條、苔加厚（moss_add），
    #   纏根加粗加多、兩條根都長蕨和葉叢（dress／dress_game）
    'X': dict(name='RootCross', L=7.2, seed=53, turns=.40, plants=.8, sides=1, branch_sides=1, head_roots=False, x0=0.0,
              wraps=True, flare=0.0, rho=(.27, .38), dk=(.76, .90), moss_add=.30,
              roots=(
                  # 下面那條：順著 X 貼地，交叉處頂高約 0.9 m；兩端用緩坡鑽進土裡（陡坡從端頭看像一截切斷的木樁）
                  ((-3.9, .20, -.40, .13, 1.0), (-3.0, .12, -.05, .28, 1.10), (-2.0, .06, .12, .44, 1.18), (-.8, -.04, .22, .58, 1.22),
                   (.7, .00, .20, .58, 1.22), (1.9, .10, .12, .45, 1.18), (2.9, .06, -.04, .30, 1.10), (3.8, .00, -.40, .13, 1.0)),
                  # 上面那條：55° 斜過去，側面是圓拱，壓在下面那條上（底面陷進它的苔約 10 cm），平面上略成 S 形，
                  # 離開交叉處漸漸貼回地面，兩端緩緩鑽進土裡
                  (_over(-4.0, -.40, .12, 1.0, -.40), _over(-3.1, -.04, .25, 1.08, -.15), _over(-2.2, .28, .33, 1.12, .10),
                   _over(-1.25, .82, .40, 1.15, .16), _over(-.35, 1.32, .43, 1.15, .06), _over(.5, 1.28, .42, 1.15, -.06),
                   _over(1.4, .80, .39, 1.15, -.14), _over(2.3, .27, .33, 1.10, -.06), _over(3.2, -.03, .24, 1.08, .14),
                   _over(4.0, -.40, .12, 1.0, .38))),
              strands=20, peel=0, lift_gap=False),
})

_top_moss0 = top_moss


def top_moss(p, nrm):
    """交叉件：設定圖兩條根頂上是一整片厚苔（DR02 的苔只在脊上一條）。moss_add 0 就和 DR02 一樣。"""
    return _top_moss0(p, nrm) + VAR.get('moss_add', 0.0) * max(0.0, nrm.z) ** 1.5

_build_roots = build


def build(quick=True, seed=None, name='DR02_High', low=None, only_big=0.0):
    objs = _build_roots(quick=quick, seed=seed, name=name, low=low, only_big=only_big)
    if VAR.get('wraps') and not only_big:
        objs += _wraps(name, objs)
    return objs


def _wraps(name, objs):
    """交叉件：兩條根頂上蜿蜒的細根（只走上半邊，不穿進另一條），和幾條橫著箍住根、兩頭往下抓進土裡的細根。
    設定圖：上面那條根頂上纏著三四條明顯的細根，下面那條也有，有的從一條根爬到另一條。"""
    R = random.Random(VAR['seed'] + 7)
    coll = bpy.data.collections[name]
    mat = dr02_bark()
    pre = name.replace('_High', '') + '_'
    out = []

    def line(li):
        pts = [(X0 + s, y, z, r, fl) for s, y, z, r, fl in VAR['roots'][li]]
        return lambda t: _along(pts, t)

    def frame_at(along, t):
        d = (along(min(1, t + .01))[0] - along(max(0, t - .01))[0]).normalized()
        side = Vector((-d.y, d.x, 0)).normalized()
        up = d.cross(side).normalized()
        if up.z < 0:
            up = -up
        return d, side, up

    def add(nm, pts, rib=.12):
        st = CFG['step']
        if st > .2:                      # 低模：纏根繞得急，0.30 m 一環會折成方角（像釘書針），這裡加密成一半
            CFG['step'] = st / 2
        try:
            o = tube(pre + nm, pts, collection=coll, seed=R.uniform(0, 50), rib=rib, twist=.2)
        finally:
            CFG['step'] = st
        o.data.materials.append(mat)
        out.append(o)

    # 頂上蜿蜒的細根：從一端的地面爬上來，沿著頂上左右擺，再從另一端下去
    #   (哪條根, t0, t1, 相位, 半徑, 擺幅°)；下面那條根避開交叉處（t .40–.60 被上面那條蓋住）
    for j, (li, t0, t1, ph, rr, sw) in enumerate((
            (1, .10, .82, .4, .14, 62), (1, .28, .95, 2.3, .12, 58), (1, .04, .56, 4.1, .11, 66), (1, .42, .90, 5.6, .10, 55),
            (1, .18, .70, 1.2, .085, 70), (0, .06, .38, 3.0, .12, 55), (0, .63, .95, .9, .11, 60), (0, .14, .36, 5.0, .08, 68))):
        along = line(li)
        pts = []
        n = 34

        def surf(t, a, rad):
            c, r, fl = along(t)
            d, side, up = frame_at(along, t)
            q = c + side * (math.cos(a) * r) + up * (math.sin(a) * r * fl)
            return (q.x, q.y, max(q.z, -.14), rad, 1.0)
        # 只在上半邊擺；擺動頻率按長度算（每公尺約 1.5 rad）：短的纏根用固定頻率會急轉，低模上折成 Z 字
        fq = 12.0 * (t1 - t0)
        angs = [math.radians(90 + sw * math.sin(i / n * fq + ph)) for i in range(n + 1)]
        for i in range(n + 1):
            pts.append(surf(t0 + (t1 - t0) * i / n, angs[i], rr * (1 - .35 * abs(2 * i / n - 1))))
        # 兩頭貼著根的側面滑下去鑽進土裡（不離開根面：離開的尾巴從人眼高看像勾子、像一堆柴）
        for k in (0, -1):
            a0 = angs[k]
            a_t = math.radians(-30) if math.cos(a0) >= 0 else math.radians(210)
            tk, dt = (t0, -.035) if k == 0 else (t1, .035)
            rad = pts[k][3]
            tail = [surf(min(1, max(0, tk + dt * f)), a0 + (a_t - a0) * f, rad * (1 - .3 * f)) for f in (.3, .6, .85, 1.0)]
            pts = (tail[::-1] + pts) if k == 0 else (pts + tail)
        add(f'Wrap{j}', pts)
    # 橫著箍住的細根：繞過根頂、從另一邊下去
    for j, (li, t, rr) in enumerate(((1, .26, .12), (1, .74, .11), (0, .22, .10), (0, .80, .10))):
        along = line(li)
        c, r, fl = along(t)
        d, side, up = frame_at(along, t)
        pts = []
        for i in range(21):              # 從根腳的土裡（-35°）繞過頂上到另一側的土裡（215°），一路貼著根面
            a = math.radians(-35 + 250 * i / 20)
            q = c + side * (math.cos(a) * r * 1.04) + up * (math.sin(a) * r * fl * 1.04) + d * (.12 * math.sin(i / 20 * math.pi))
            e = min(i, 20 - i)
            pts.append((q.x, q.y, max(q.z, -.14), rr * (.75 + .25 * min(1, e / 4)), 1.0))
        add(f'Strap{j}', pts, rib=.1)
    return out


_FOOT = dict(foot=.7, foot_size=.55, foot_along=True, heart=.4)      # 交叉件根腳：設定圖是貼著根側的小蕨，不是一叢叢比根還高的大蕨


def _over_line():
    """上面那條根的中心線、座標架（給植物沿第二條根長）。"""
    pts = [(X0 + s, y, z, r, fl) for s, y, z, r, fl in VAR['roots'][1]]

    def c1(t):
        return _along(pts, t)[0]

    def f1(t):
        d = (c1(min(1, t + .01)) - c1(max(0, t - .01))).normalized()
        side = Vector((-d.y, d.x, 0)).normalized()
        nrm = d.cross(side).normalized()
        if nrm.z < 0:
            nrm = -nrm
        return d, side, nrm
    return c1, f1


def dress(objs, quick=True, seed=5):
    """高模植物：交叉件兩條根各長一次（第二條用 DR02_Q_），其他件和 DR02 一樣。"""
    import dr01_dress
    importlib.reload(dr01_dress)
    kw = _FOOT if 'roots' in VAR else {}
    out = dr01_dress.dress(objs, centre, frame, fb, PATH_HALF, quick=quick, seed=seed, coll_name='DR02_High', prefix='DR02_P_', amount=VAR['plants'], avoid=True, **kw)
    if 'roots' in VAR:
        c1, f1 = _over_line()
        out += dr01_dress.dress(objs, c1, f1, fb, PATH_HALF, quick=quick, seed=seed + 11, coll_name='DR02_High', prefix='DR02_Q_', amount=VAR['plants'], avoid=True, **_FOOT)
    return out


def dress_game(low, mod, seed):
    """遊戲植物（game_dr02.make_detail 呼叫）：同上，用遊戲低模、DR02_LP_／DR02_LQ_。
    交叉件的蕨羽片三片留一片（Lite.cfg fern_keep；兩條根都長，數量是 DR02 的兩倍）。"""
    import core_plants
    cfg = getattr(core_plants.LeafBuf, 'cfg', None)
    if cfg is not None and 'roots' in VAR:
        cfg['fern_keep'] = 3
    try:
        return _dress_game(low, mod, seed)
    finally:
        if cfg is not None:
            cfg.pop('fern_keep', None)


def _dress_game(low, mod, seed):
    kw = _FOOT if 'roots' in VAR else {}
    out = mod.dress([low], centre, frame, fb, PATH_HALF, quick=True, seed=seed, coll_name='DR02_Game', prefix='DR02_LP_', lite=True, amount=VAR['plants'], avoid=True, **kw)
    if 'roots' in VAR:
        c1, f1 = _over_line()
        out += mod.dress([low], c1, f1, fb, PATH_HALF, quick=True, seed=seed + 11, coll_name='DR02_Game', prefix='DR02_LQ_', lite=True, amount=VAR['plants'], avoid=True, **_FOOT)
    return out


set_variant('E')
