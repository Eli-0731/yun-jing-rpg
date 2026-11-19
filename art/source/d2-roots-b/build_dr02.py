# DR02 板根牆模組（高模）：神木的板根延伸出去的樣子，一頭粗（立起來的板根，頂上一道脊）、一頭細鑽進土裡，
# 好幾件首尾相接圍成弧。三種：A 高拱（中段離地拱起約 4 m，底下留約 1 m 的暗縫）、B 低伏（貼地蛇行 1.5–2 m 高）、
# C 分岔（粗頭往前分成 Y 字兩條，各自鑽進土裡）。側面有慢慢扭轉的粗稜（貼著主根繞的副根）。
# 根沿 +X 走：粗頭在 -X、細頭在 +X；正面 -Y；原點在底部中心，z = 0 是地面，鑽土的部分在 z < 0。
# 在 Blender 裡：b = 載入此檔; b['set_variant']('A'); b['build'](quick=True)
import bpy, math, random, sys, os, importlib
from mathutils import Vector, noise

HERE = os.path.dirname(os.path.abspath(globals().get('__file__', 'D:/yun-jing-d2-roots/art/source/d2-roots-b/build_dr02.py')))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import dr_core
importlib.reload(dr_core)
from dr_core import tube, fb, bark_material, CFG

PATH_HALF = -100.0          # 沒有路：植物、地面根不用避開什麼

# 主根的控制點：(沿長度 s m, 前後 y m, 中心高 z m, 半寬 r m, 扁度 fl)。高度 ≈ z + r × fl，底 ≈ z − r × fl。
# 頭尾兩點在土裡（從土裡冒出來、再鑽回土裡）。
VARIANTS = {
    'A': dict(name='HighArch', L=13.0, seed=11, turns=.55, plants=1.0,
              spine=((-2.0, .00, -1.20, 1.20, 1.30), (-.2, .00, .55, 1.25, 1.45), (1.8, -.10, 1.45, 1.08, 1.60),
                     (3.8, -.30, 2.15, .85, 1.60), (5.6, -.15, 2.05, .72, 1.55), (7.6, .20, 1.30, .58, 1.45),
                     (9.6, .35, .60, .46, 1.30), (11.4, .20, .20, .32, 1.15), (13.0, .10, -.50, .16, 1.0)),
              strands=14, peel=3, lift_gap=True),
    'B': dict(name='LowCrawl', L=12.0, seed=23, turns=.40, plants=.8, sides=9,     # 低伏：最高約一人高，中段再鼓起一個小包
              spine=((-1.8, .00, -1.00, 1.00, 1.25), (.2, .05, .40, 1.00, 1.30), (2.3, .40, .28, .78, 1.30),
                     (4.2, .50, -.05, .64, 1.25), (6.1, .05, .58, .62, 1.25), (8.0, -.45, .15, .48, 1.20),
                     (9.8, -.40, -.04, .38, 1.15), (11.3, -.05, -.10, .27, 1.05), (12.6, .20, -.45, .14, 1.0)),
              strands=12, peel=3, lift_gap=False),
    'C': dict(name='Fork', L=12.0, seed=37, turns=.45, plants=.9,
              spine=((-1.8, .00, -1.10, 1.05, 1.30), (.2, .00, .45, 1.00, 1.45), (2.4, .10, .80, .84, 1.55),
                     (3.9, .10, .85, .76, 1.50), (5.0, .05, .70, .66, 1.40), (5.6, .00, .45, .52, 1.2)),
              branches=(  # 從主根 s≈3.6 分出去：(往前後偏 y 的方向 ±1, 控制點 [(s, dy, z, r, fl)])；前枝拱起來跨在後枝上方
                  (-1, ((3.6, -.15, 1.00, .56, 1.40), (5.2, -.95, 1.55, .46, 1.35), (7.0, -2.05, 1.80, .40, 1.30),
                        (8.8, -3.00, 1.40, .33, 1.20), (10.4, -3.60, .55, .25, 1.10), (11.6, -3.90, -.45, .14, 1.0))),
                  (1, ((3.6, .30, .75, .54, 1.40), (5.3, 1.10, .42, .48, 1.35), (7.0, 2.00, .22, .40, 1.30),
                       (8.6, 2.80, .12, .32, 1.18), (9.9, 3.30, -.02, .24, 1.08), (10.9, 3.60, -.45, .14, 1.0)))),
              strands=16, peel=2, lift_gap=False),
}
VAR = None
SP = None           # 主根控制點（世界座標）
X0 = 0.0


def set_variant(v):
    global VAR, SP, X0
    VAR = dict(VARIANTS[v], key=v)
    pts = VAR['roots'][0] if 'roots' in VAR else VAR['spine']     # roots：好幾條各自獨立的根（DR03 交叉件），植物、量測沿第一條
    if 'branches' in VAR:      # 分岔件：中心線接前面那條分枝，植物、量測都沿這一條
        pts = tuple(p for p in pts if p[0] < VAR.get('fork_s', 3.6)) + VAR['branches'][0][1]
    ss = [p[0] for p in pts]
    X0 = VAR['x0'] if 'x0' in VAR else -(min(ss) + max(ss)) / 2         # 頭尾都在土裡：讓整條根的中點落在原點
    SP = [(Vector((X0 + s, y, z)), r, fl) for s, y, z, r, fl in pts]


def _cr(p0, p1, p2, p3, t):
    return .5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)


def spine_at(t):
    """t 0..1 沿主根（粗頭→細頭），回傳 (中心, 半寬, 扁度)。"""
    n = len(SP) - 1
    f = max(0.0, min(.99999, t)) * n
    i = int(f)
    u = f - i
    g = lambda k: SP[max(0, min(n, k))]
    a, b, c, d = g(i - 1), g(i), g(i + 1), g(i + 2)
    p = _cr(a[0], b[0], c[0], d[0], u)
    r = b[1] + (c[1] - b[1]) * u
    fl = b[2] + (c[2] - b[2]) * u
    return p, r, fl


def centre(t):
    return spine_at(t)[0]


def frame(t):
    d = (centre(min(1, t + .01)) - centre(max(0, t - .01))).normalized()
    side = Vector((0, 1, 0))
    side = (side - d * side.dot(d)).normalized()
    nrm = d.cross(side).normalized()
    if nrm.z < 0:
        nrm = -nrm
    return d, side, nrm


def ground_run(p0, ang, length, r0, R, wig=1.0, dive=.9, n=10, lift=0.0, taper=1.05):
    """從 p0 沿地面往 ang 方向爬 length 公尺、越來越細、最後鑽進土裡（和 DR01 同一個做法，這裡沒有路要避）。"""
    out = []
    ph = R.uniform(0, 6.3)
    for i in range(1, n + 1):
        f = i / n
        w = (math.sin(f * 5.0 + ph) + .45 * math.sin(f * 11.0 + ph * 2)) * wig * (.25 + f) * (1 - .4 * f)
        x = p0.x + math.cos(ang) * length * f - math.sin(ang) * w
        y = p0.y + math.sin(ang) * length * f + math.cos(ang) * w
        r = r0 * (1 - f) ** taper * (1 - .25 * f) + .05
        hump = max(0.0, fb((x * .3, y * .3, ph), 1.0, 2)) * r * 1.2
        z = r * .38 + hump + lift * (1 - f) ** 2
        if f > .72:
            z -= dive * ((f - .72) / .28) ** 1.6
        out.append((x, y, z, r, 1.0 + .35 * (1 - f) ** 2))
    return out


def top_moss(p, nrm):
    """朝上的面長苔（板根頂上的脊一整條是苔），越高越多；側面下半和貼地處少。"""
    h = max(0.0, min(1.0, (p.z - .3) / 2.2))
    return .08 + .38 * max(0.0, nrm.z) ** 1.3 + .14 * h


set_variant('A')


LICHEN = (.56, .61)     # 地衣斑的雜訊門檻（DR01／神木是 .60–.65）：設定圖根脊上的灰白地衣斑比神木多


def dr02_bark():
    """DR01 同一套樹皮材質（掃描樹皮、裂溝壓暗、苔），只把凸起處的地衣斑放多一點。
    已經有就沿用（遊戲流程會呼叫好幾次 build，刪掉重建會讓先建好的高模掉材質、烘成全白），每次都把門檻設成 LICHEN。"""
    m = bark_material('D2RootBark_DR02')
    for n in m.node_tree.nodes:
        if n.type != 'VALTORGB' or not n.inputs[0].is_linked:
            continue
        src = n.inputs[0].links[0].from_node
        e = n.color_ramp.elements
        if src.type == 'TEX_NOISE' and abs(src.inputs['Scale'].default_value - 5.0) < 1e-3:      # 地衣斑那個 5 公尺尺度的雜訊（苔的雜訊是 6）
            e[0].position, e[1].position = LICHEN
            return m
    raise RuntimeError('lichen ramp not found in D2RootBark_DR02')


def build(quick=True, seed=None, name='DR02_High', low=None, only_big=0.0):
    """low=(step, numin, numax[, nuk])：同一份路徑做不帶樹皮凹凸的低模；only_big：只做半徑大於這個值的根（碰撞用）。"""
    CFG.update(step=.12 if quick else .05, numin=28 if quick else 48, numax=520, amp=.16, moss=.085, nuk=.8, crest=.40)
    if low:
        CFG.update(step=low[0], numin=low[1], numax=low[2], amp=0.0, moss=0.0, nuk=low[3] if len(low) > 3 else .8)
    seed = VAR['seed'] if seed is None else seed
    pre = name.replace('_High', '') + '_'
    noise.seed_set(seed)
    R = random.Random(seed)
    coll = bpy.data.collections.get(name)
    if coll:
        for o in list(coll.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    else:
        coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(coll)
    mat = dr02_bark()
    objs = []

    def tb(nm, pts, **kw):
        if only_big and max(p[3] for p in pts) < only_big:
            return None
        o = tube(pre + nm, pts, collection=coll, **kw)
        o.data.materials.append(mat)
        objs.append(o)
        return o

    def pts_of(sp):
        return [(X0 + s, y, z, r, fl) for s, y, z, r, fl in sp]

    def _tan(along, t):
        return (along(min(1, t + .01))[0] - along(max(0, t - .01))[0]).normalized()

    def _sn(d):
        side = Vector((0, 1, 0))
        side = (side - d * side.dot(d)).normalized()
        nrm = d.cross(side).normalized()
        if nrm.z < 0:
            nrm = -nrm
        return side, nrm

    branches = VAR.get('branches', ())
    trunk = [p for p in VAR.get('spine', ()) if not branches or p[0] < VAR.get('fork_s', 3.6)]
    lines = [spine_at]                 # 每股根沿哪一條中心線走（分岔件：前一半走前分枝、後一半走後分枝）
    if branches:
        lines = [lambda t, sp=sp: _along(pts_of(trunk + list(sp)), t) for sg, sp in branches]
    if 'roots' in VAR:
        lines = [lambda t, sp=sp: _along(pts_of(sp), t) for sp in VAR['roots']]

    # ---- 內芯：一塊立起來的板根把整束根撐起來、填住根和根之間的縫（設定圖斷面是底寬頂尖的帳篷形）----
    for li, along in enumerate(lines):
        pts = []
        for i in range(31):
            t = i / 30
            c, r, fl = along(t)
            th = next((j / 200 for j in range(201) if along(j / 200)[0].z > along(j / 200)[1] * along(j / 200)[2] * .35), .1)
            u = VAR.get('flare', 1.0) * max(0.0, min(1.0, (th * 1.25 - t) / max(th * 1.25, 1e-3)))
            pts.append((c.x, c.y, c.z - r * fl * (.06 + .25 * u), r * .76 * (1 - .10 * u), fl * .98))
        tb(f'Core{li}', pts, seed=3 + li * 5.1, rib=.26, twist=.05, moss_bias=top_moss)

    # ---- 一股股絞在一起的根：繞著中心線慢慢扭轉（大多同一個方向，幾股反著繞、壓在別股上面），
    #      頂上收窄成脊；有幾股半路離開這一束，往旁邊爬下去鑽進土裡 ----
    N = VAR['strands']
    turns = VAR['turns']
    # 粗頭鑽出土的那一段：各股往兩側攤開、貼地抓進土裡（設定圖端視是底寬頂尖、一條條肋骨落地的帳篷形，不是一塊切面）
    t_head = []
    for along in lines:
        th = next((i / 200 for i in range(201) if along(i / 200)[0].z > along(i / 200)[1] * along(i / 200)[2] * .35), .1)
        t_head.append(max(th, .02))
    peel = set(R.sample(range(N), VAR['peel']))
    for k in range(N):
        along = lines[k % len(lines)]
        th = t_head[k % len(lines)]
        ph0 = 2 * math.pi * k / N + R.uniform(-.25, .25)
        dk = R.uniform(*VAR.get('dk', (.84, 1.0)))
        rho = R.uniform(*VAR.get('rho', (.20, .34)))
        tw = turns * (1 if k % 4 else -.65) * R.uniform(.85, 1.15)
        t_end = 1.0                            # 尾端跟著中心線一起鑽進土裡，不留切口
        peeled = False
        if k in peel:                          # 只從貼地的那一段離開這一束（拱起來的地方離開會像拐杖）
            for _ in range(40):
                te = R.uniform(.40, .90)
                c, r, fl = along(te)
                if c.z - r * fl * .9 < .05 and math.sin(ph0 + te * 2 * math.pi * tw) < -.2:
                    t_end, peeled = te, True   # 這一股在那裡要正好繞到下半邊
                    break                      # 找不到這種地方就不離開（不能用最後一次亂數的位置）
        pts = []
        n = 44
        for i in range(n + 1):
            t = t_end * i / n
            c, r, fl = along(t)
            d = _tan(along, t)
            side, nrm = _sn(d)
            ph = ph0 + t * 2 * math.pi * tw
            cv, sv = math.cos(ph), math.sin(ph)
            wd = 1 - .38 * max(0.0, sv) ** 1.3              # 上半邊收窄：帳篷形
            u = VAR.get('flare', 1.0) * max(0.0, min(1.0, (th * 1.25 - t) / (th * 1.25)))   # 0：束已離地；1：粗頭最末端（flare 0：不攤開）
            fan = 1 + .75 * u ** .8                          # 往兩側攤開（太開會露出股與股之間的縫，像一捆圓木）
            q = c + side * (cv * r * dk * wd * fan) + nrm * (sv * r * fl * dk * .90 * (1 - .25 * u))
            rr = r * rho * (1 + .15 * math.sin(t * 17 + k * 1.3)) * (1 + .35 * u)
            pts.append((q.x, q.y, q.z, max(rr, .05), 1.0 + .12 * cv * cv))
        if peeled:
            q = Vector(pts[-1][:3])
            c = along(t_end)[0]
            sgn = 1 if (q - c).dot(side) >= 0 else -1
            rr = pts[-1][3]
            out = side * sgn
            land = Vector((q.x + out.x * 1.1 + d.x * .8, q.y + out.y * 1.1 + d.y * .8, rr * .5))
            pts.append(((q.x + land.x) / 2, (q.y + land.y) / 2, max(rr * .6, (q.z + land.z) / 2 + .1), rr, 1.1))
            pts.append((land.x, land.y, land.z + .08, rr, 1.25))
            ang = math.atan2(out.y + d.y * .6, out.x + d.x * .6)
            pts += ground_run(land, ang, R.uniform(2.0, 3.6), rr, R, wig=R.uniform(.5, 1.1), lift=.05, taper=1.15, n=8)
        tb(f'Strand{k}', pts, seed=30 + k * 3.9, rib=.18, twist=.10, moss_bias=top_moss)

    # ---- 粗頭：兩三條粗根從束裡往兩側斜後方離開、鑽進土裡（像從神木那邊延伸過來的根頸）----
    c0, r0, fl0 = spine_at(.10)
    for j, (sg, back, rr, rise) in enumerate(((-1, .7, .40, .35), (1, .9, .36, .30), (1, 1.4, .26, .05)) if VAR.get('head_roots', True) else ()):
        p_top = c0 + Vector((.2 + .5 * j, sg * r0 * .80, -r0 * fl0 * .25 + rise))
        pts = [(p_top.x + .9, p_top.y - sg * .1, p_top.z + .2, rr * .7, 1.0), (p_top.x, p_top.y, p_top.z, rr, 1.25)]
        land = Vector((p_top.x - back * .9, p_top.y + sg * back * .8, rr * .5))
        pts.append((land.x, land.y, land.z + .15, rr * 1.05, 1.3))
        ang = math.atan2(sg * .8, -1.0 + R.uniform(-.2, .2))
        pts += ground_run(land, ang, R.uniform(1.4, 2.4), rr, R, wig=R.uniform(.4, .8), dive=1.0, lift=.05, taper=1.2, n=6)
        tb(f'Head{j}', pts, seed=50 + j * 2.3, rib=.24, twist=.12)

    # ---- 側邊小根：從主根貼地的那一段，往兩側斜後方爬 2–4 m 鑽進土裡（抓住地面，不是放在地上的一根木頭）----
    m = 0
    for li, along in enumerate(lines):
        n_side = VAR.get('sides', 5) if li == 0 else VAR.get('branch_sides', 3)
        for i in range(n_side):
            t = R.uniform(.22, .88) if li == 0 else R.uniform(.35, .85)
            c, r, fl = along(t)
            bottom = c.z - r * fl
            if bottom > .20:
                continue              # 只從貼地的那段長（拱起來的那段長出來會像斜撐的支架；A 的暗縫要留著）
            sg = 1 if (i + li) % 2 == 0 else -1
            d = _tan(along, t)
            side = _sn(d)[0]
            st = c + side * (sg * r * .8)
            st.z = max(.18, min(c.z, bottom + r * fl * .6))
            rr = R.uniform(.14, .26) * (r / .7) ** .5
            ang = math.atan2(side.y * sg, side.x * sg) + R.uniform(.2, .6) * (1 if R.random() < .7 else -1)
            pts = [(st.x - d.x * .3, st.y - d.y * .3, st.z + .1, rr * .8, 1.0), (st.x, st.y, st.z, rr, 1.1)]
            pts += ground_run(st, ang, R.uniform(1.8, 3.6), rr, R, wig=R.uniform(.5, 1.1), lift=.05, taper=1.15)
            tb(f'Side{m}', pts, seed=70 + m * 1.9, rib=.2, twist=.12)
            m += 1

    # ---- A：拱起處底下垂兩三條細根（暗縫裡有東西，但人走不進去）----
    if VAR['lift_gap'] and False:            # 試過：垂下來的細根像木樁，先不做
        for j, t in enumerate((.36, .47, .58)):
            c, r, fl = spine_at(t + R.uniform(-.03, .03))
            top = c.z - r * fl * .7
            sg = R.choice((-1, 1))
            pts = [(c.x, c.y + sg * r * .4, top + .2, .09, 1.0)]
            reach = R.uniform(.55, 1.0)
            for f in (.3, .6, 1.0):
                pts.append((c.x + .25 * f * sg, c.y + sg * (r * .4 + .2 * f), max(top - (top + .1) * reach * f, -.2), .09 * (1 + .4 * f) if reach > .9 else .09 * (1 - .6 * f) + .01, 1.0))
            tb(f'Hang{j}', pts, seed=90 + j, rib=.15, twist=.2)

    tris = sum(len(o.data.polygons) * 2 for o in objs)
    print('DR02', VAR['key'], 'objects', len(objs), 'tris', tris)
    return objs


def _along(pts, t):
    """一串 (x,y,z,r,fl) 控制點上 t 處的 (中心, 半寬, 扁度)。"""
    n = len(pts) - 1
    f = max(0.0, min(.99999, t)) * n
    i = int(f)
    u = f - i
    g = lambda k: pts[max(0, min(n, k))]
    a, b, c, d = g(i - 1), g(i), g(i + 1), g(i + 2)
    p = _cr(Vector(a[:3]), Vector(b[:3]), Vector(c[:3]), Vector(d[:3]), u)
    return p, b[3] + (c[3] - b[3]) * u, b[4] + (c[4] - b[4]) * u


def dress(objs, quick=True, seed=5):
    import dr01_dress
    importlib.reload(dr01_dress)
    return dr01_dress.dress(objs, centre, frame, fb, PATH_HALF, quick=quick, seed=seed, coll_name='DR02_High', prefix='DR02_P_', amount=VAR['plants'], avoid=True)
