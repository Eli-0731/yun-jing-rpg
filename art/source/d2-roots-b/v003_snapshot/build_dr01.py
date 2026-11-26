# DR01 南入口大根拱（高模）：三股粗根絞成拱，淨跨 8 m、淨高 5 m；兩腳散成根，往外爬 12–15 m 鑽進土裡。
# 正面 -Y（從南邊看），路沿 Y 軸穿過拱洞；原點在拱洞正下方地面，z = 0 是地面，鑽土的部分在 z < 0。
# 在 Blender 裡：exec(open(此檔).read()); build(quick=True)
import bpy, math, random, sys, os, importlib, bisect
from mathutils import Vector, noise

HERE = os.path.dirname(os.path.abspath(globals().get('__file__', 'D:/yun-jing-d2-roots/art/source/d2-roots-b/build_dr01.py')))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import dr_core
importlib.reload(dr_core)
from dr_core import tube, fb, bark_material, CFG

AX, AZ, CZ = 5.70, 4.95, 2.0     # 拱中心線：橢圓半寬、半高、圓心高
AX_L = 5.84                       # 左半邊的半寬：左腿比較粗，中心線往外移一點，洞才不會變窄
A0 = 0.38                         # 兩腳落地時橢圓角（水平線下多少弧度）→ 拱腳往內收，洞是馬蹄形
THICK = [.86, .55, .69]           # 三股的半徑：粗細不一，絞起來像一根扭轉的粗幹（核心組 11/16 第二、三版也是這個方向）
WOFF = [.38, .69, .55]            # 各股中心離拱中心線多遠：粗的靠中間，三股的外緣大致齊
TURNS = .55                       # 每條根的三股從腳到交叉點互絞幾圈（v003：兩條根各自絞）
PH0 = 2.86                        # 絞的起始角：最粗那股在兩隻腳都落在正面（V2 看得到它的根頸）
LEG = (.38, .20)                  # 拱腿比拱頂粗多少（左腿、右腿）：設定圖左腿、左肩明顯比右邊粗壯
FLARE, HB = 2.2, .15              # 根頸：拱腿最下面 15%（約 3 m 以下）順著落地的方向往外撇，畫一個弧落地，不是直直插到地上
PATH_HALF = 1.5                   # 路寬 2.2 m，兩邊各留一點；地面根不進這個範圍


# v003：交叉尖拱。兩條巨根各自從一隻腳拱起來，在路中央上方約 7.3 m 交叉；交叉之後根梢越過對方，
# 左根搭在右肩外側（南面）往下垂，右根搭在左肩背面（北面）往下垂，像兩隻手交握。拱洞是尖的，不是圓環。
# 每條根的路徑是 (x, z) 控制點的 Catmull-Rom 曲線；u = 0 腳、u = 1 交叉點、u > 1 是越過去的根梢。
ROOTS = (
    ((-6.1, 0.0), (-6.2, 1.7), (-5.5, 3.5), (-4.2, 5.2), (-2.0, 6.45), (0.0, 7.35),
     (1.7, 7.95), (3.1, 8.0), (4.3, 7.4), (5.25, 6.2), (6.05, 4.8), (6.6, 3.5)),
    ((6.0, 0.0), (6.05, 1.8), (5.4, 3.6), (4.1, 5.25), (2.0, 6.45), (0.0, 7.35),
     (-1.6, 7.85), (-2.9, 7.85), (-4.1, 7.25), (-5.1, 6.1), (-5.95, 4.8), (-6.55, 3.6)),
)
SEG = .2                          # 每段控制點佔多少 u：u = 1 在第 5 個點（交叉點）
UMAX = SEG * (len(ROOTS[0]) - 1)  # 根梢末端的 u
YSIDE = (-.55, .55)               # 交叉處左根在南（前）、右根在北（後）
RSC = (1.0, .86)                  # 右根比左根細


def _cr(P, u):
    n = len(P) - 1
    x = max(0.0, min(n - 1e-6, u / SEG))
    i = int(x)
    f = x - i
    p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, n)]
    return tuple(.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * f + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * f * f
                       + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * f ** 3) for j in range(2))


def rpath(sd, u):
    x, z = _cr(ROOTS[sd], u)
    k = max(0.0, min(1.0, (u - .4) / .6))
    y = YSIDE[sd] * k * k * (3 - 2 * k) + .12 * math.sin(u * 3.1 + sd * 1.7) - .08
    return Vector((x, y, z))


def rframe(sd, u):
    d = (rpath(sd, u + .01) - rpath(sd, u - .01)).normalized()
    side = Vector((0, 1, 0))
    side = (side - d * side.dot(d)).normalized()
    nrm = d.cross(side).normalized()      # 指向拱外
    if nrm.dot(rpath(sd, u) - Vector((0, 0, 2.5))) < 0:
        nrm = -nrm
    return d, side, nrm


def _su(t):
    return (0, 2 * t) if t < .5 else (1, 2 * (1 - t))


def centre(t):
    """t 0..1：左腳 → 交叉點（t = .5）→ 右腳。t < .5 是左根，t > .5 是右根（各自到交叉點為止）。"""
    return rpath(*_su(max(0.0, min(1.0, t))))


def frame(t):
    sd, u = _su(max(0.0, min(1.0, t)))
    d, side, nrm = rframe(sd, u)
    return (d if sd == 0 else -d), side, nrm


def foot_flare(t, dirs, amount):
    """拱腿靠近腳的那一段往落地方向撇出去（平方緩入）。dirs = (左腳方向, 右腳方向)。"""
    v = Vector((0, 0, 0))
    if t < HB:
        v += dirs[0] * (amount * (1 - t / HB) ** 2)
    if t > 1 - HB:
        v += dirs[1] * (amount * (1 - (1 - t) / HB) ** 2)
    return v


def leg_scale(t):
    """拱腿比拱頂粗：拱頂 1.0；左肩約 1.16、左腳約 1.34；右肩約 1.08、右腳約 1.18。"""
    t = max(0.0, min(1.0, t))
    return 1 + LEG[0 if t < .5 else 1] * (1 - math.sin(math.pi * t)) ** .7


def tipk(u, end=None):
    """根梢越往末端越細：交叉點以前 1.0，末端約 0.3。end：這一股提早在哪裡結束（嵌回樹皮）。"""
    end = UMAX if end is None else end
    if u <= 1.0:
        return 1.0
    f = (u - 1.0) / (end - 1.0)
    return max(.10, 1 - .62 * f - .26 * f ** 4)          # 最後一小段收尖，末端不是平切口


def strand_offset_r(sd, k, u, dirs=None, end=None):
    """第 sd 條根的第 k 股，在 u 處離根中心線的位置與半徑。"""
    c = rpath(sd, u)
    d, side, nrm = rframe(sd, u)
    t = u / 2 if sd == 0 else 1 - u / 2
    ph = k * 2 * math.pi / 3 + PH0 + sd * 1.3 + u * 2 * math.pi * TURNS
    e = u / 2
    g = leg_scale(t) if u <= 1 else 1.0
    tk = tipk(u, end)
    w = WOFF[k] * g * max(.25, tk) + .30 * max(0.0, 1 - e / .16) ** 1.5
    p = c + side * math.cos(ph) * w * 1.05 + nrm * math.sin(ph) * w * .85
    fo = max(0.0, 1 - e / .20) ** 2
    p += Vector((-1 if sd == 0 else 1, 0, 0)) * fo * (.9 * max(0.0, math.sin(ph))) + side * math.cos(ph) * fo * .7
    r = THICK[k] * RSC[sd] * g * tk * (1 + .10 * math.sin(u * 8.5 + k * 2.1)) * (1 - .16 * max(0.0, 1 - e / .14) ** 1.2)
    if dirs and u <= 1.0:                       # 根頸往外撇只在拱腳；越過交叉點的根梢不套
        p = p + foot_flare(t, dirs, FLARE)
    return p, r, ph


def strand_offset(k, t, dirs=None):
    """第 k 股在 t 處（拱腳附近用）離中心線的位置與半徑。"""
    sd, u = _su(t)
    return strand_offset_r(sd, k, u, dirs)


def ground_run(p0, ang, length, r0, R, wig=1.0, dive=.9, n=10, lift=0.0, taper=1.05):
    """從 p0 沿地面往 ang 方向爬 length 公尺、越來越細、最後鑽進土裡。回傳 [(x,y,z,r,flat)]（不含 p0）。
    靠近路的時候順著路邊轉向（設定圖：拱腳內側的根沿著路邊爬，路面是空的）；萬一還是進了路（|x| < PATH_HALF）就提早鑽下去。"""
    out = []
    ph = R.uniform(0, 6.3)
    stop = None
    own = 1.0 if p0.x >= 0 else -1.0                  # 這條根在路的哪一邊
    lo, m = PATH_HALF + .35, PATH_HALF + 2.35           # 離路中心 m 以內開始轉，最近只到 lo
    sy = math.copysign(1.0, math.sin(ang)) if abs(math.sin(ang)) > .2 else -1.0      # 轉向南或北；本來就橫著走的朝南
    for i in range(1, n + 1):
        f = i / n
        w = (math.sin(f * 5.0 + ph) + .45 * math.sin(f * 11.0 + ph * 2)) * wig * (.25 + f) * (1 - .4 * f)
        x = p0.x + math.cos(ang) * length * f - math.sin(ang) * w
        y = p0.y + math.sin(ang) * length * f + math.cos(ang) * w
        d = own * x
        if d < m:
            push = (m - lo) * (math.exp((d - m) / (m - lo)) - 1) - (d - m)      # 越靠近路推得越多，m 處是 0
            k = min(1.0, f / .3)                      # 根頭那一段不動，才不會和它長出來的地方脫開
            x += own * push * k
            y += sy * push * .9 * k
        if abs(x) < PATH_HALF and stop is None:
            stop = i
        r = r0 * (1 - f) ** taper * (1 - .25 * f) + .05
        hump = max(0.0, fb((x * .3, y * .3, ph), 1.0, 2)) * r * 1.2
        z = r * .38 + hump + lift * (1 - f) ** 2
        if f > .72:
            z -= dive * ((f - .72) / .28) ** 1.6
        out.append((x, y, z, r, 1.0 + .35 * (1 - f) ** 2))
    if stop is not None:
        out = out[:max(stop, 2)]
        x, y, z, r, fl = out[-1]
        out[-1] = (x + (PATH_HALF - abs(x)) * (1 if x > 0 else -1), y, -.5, .05, 1.0)
        if len(out) > 1:
            x, y, z, r, fl = out[-2]
            out[-2] = (x, y, z * .4, r * .6, 1.0)
    return out


_CT = [centre(.13 + .75 * i / 150) for i in range(151)]      # 拱身中心線（這一段 x 單調遞增）
_CX = [c.x for c in _CT]
_CZ = [c.z for c in _CT]


def crown_z(x):
    """拱身中心線在 x 這個位置的高度。"""
    i = bisect.bisect_right(_CX, x)
    if i <= 0:
        return _CZ[0]
    if i >= len(_CX):
        return _CZ[-1]
    return _CZ[i - 1] + (_CZ[i] - _CZ[i - 1]) * (x - _CX[i - 1]) / max(_CX[i] - _CX[i - 1], 1e-6)


def crown_moss(p, nrm):
    """拱身越高苔越多。朝上的面長滿；拱頂、拱肩正面和背面的上半邊（中心線以上）也披著一層，下緣參差、一條一條往下掛
    （設定圖：從南邊平視，拱頂看得到的那一面上半是苔）；下半邊和拱底只有零星幾塊，樹皮看得到。"""
    h = max(0.0, min(1.0, (p.z - 2.6) / 2.6))
    h = h * h * (3 - 2 * h)
    h2 = max(0.0, min(1.0, (p.z - 3.8) / 1.6))
    top = max(0.0, min(1.0, (p.z - crown_z(p.x) + .25) / .8))
    top = top * top * (3 - 2 * top) * h2
    drip = fb((p.x * 1.4, p.y * 1.4, p.z * .22), 1.0, 2)
    return .06 + h * (.14 + .22 * max(0.0, nrm.z)) + top * (.40 + .16 * drip)


def build(quick=True, seed=11, name='DR01_High', low=None, only_big=0.0):
    """low=(step, numin, numax[, nuk])：同一份路徑做成不帶樹皮凹凸的低模（遊戲用、碰撞用）；nuk 越大粗根的斷面邊數越多。
    only_big：只做半徑大於這個值的根。"""
    CFG.update(step=.12 if quick else .05, numin=28 if quick else 48, numax=520, amp=.16, moss=.085, nuk=.8)
    if low:
        CFG.update(step=low[0], numin=low[1], numax=low[2], amp=0.0, moss=0.0, nuk=low[3] if len(low) > 3 else .8)
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
    mat = bark_material()
    objs = []
    runs = {0: [], 1: []}        # 每隻腳的地面根路徑，給岔根用

    def add(o):
        o.data.materials.append(mat)
        objs.append(o)

    def tube(nm, pts, **kw):
        if only_big and max(p[3] for p in pts) < only_big:
            return None
        return dr_core.tube(nm.replace('DR01_', pre), pts, **kw)

    def add(o):
        if o is None:
            return
        o.data.materials.append(mat)
        objs.append(o)

    # ---- 三股主根：左腳地面根 → 絞著上拱 → 右腳地面根（一條到底）----
    # 每隻腳三股各走一個方向：最靠前的朝正面斜出去（V2 裡朝鏡頭掃過來）、中間那股朝外、最靠後的朝背面
    foot_ang, foot_phi = {}, {}      # foot_phi：0 = 正外側，+ = 朝正面 (-Y)，− = 朝背面
    for foot, t_end in ((0, .045), (1, .955)):
        base = math.pi if foot == 0 else 0.0
        sgn = 1 if foot == 0 else -1
        for q in range(3):
            ph = strand_offset(q, t_end)[2]
            nat = math.atan2(-math.cos(ph), math.sin(ph))       # 這一股在拱腳斷面上的方位（±π 是朝拱洞裡）
            foot_phi[q, foot] = max(-1.62, min(1.62, nat * .62)) + R.uniform(-.08, .08)
            foot_ang[q, foot] = base + sgn * foot_phi[q, foot]
    # ---- 拱腳的實心根座：三股根往三個方向撇出去之後，中間是一整塊（像樹頭），不是三根柱子中間透空 ----
    for foot in (0, 1):
        pts = []
        for tt0, r, fl in ((.20, .50, 1.0), (.16, .66, 1.0), (.12, .82, .95), (.08, .92, .9), (.045, .96, .88), (.015, .96, .86)):
            c = centre(tt0 if foot == 0 else 1 - tt0)
            pts.append((c.x, c.y, c.z, r * THICK[0] / .86, fl))
        c = centre(0.0 if foot == 0 else 1.0)
        pts.append((c.x, c.y, -.9, .98 * THICK[0] / .86, .86))
        add(tube(f'DR01_Core{foot}', pts, seed=7 + foot * 3.3, rib=.26, twist=.10, collection=coll))
    ENDS = (UMAX, UMAX - .45, UMAX - .85)       # 三股在根梢各自結束：最粗那股到最末端，細的兩股提早嵌回去
    for sd in (0, 1):
        for k in range(3):
            dirs = [Vector((math.cos(foot_ang[k, f]), math.sin(foot_ang[k, f]), 0)) for f in (0, 1)]
            mid = []
            n = 40
            for i in range(n + 1):
                u = .09 + (ENDS[k] - .09) * i / n
                p, r, ph = strand_offset_r(sd, k, u, dirs, end=ENDS[k])
                e = u / 2
                mid.append((p.x, p.y, max(p.z, r * .45), r, 1.0 + .25 * max(0.0, 1 - e / .12)))
            endp = mid[0]
            ang = foot_ang[k, sd]
            L = R.uniform(8.0, 9.8)
            k1 = (endp[0] + math.cos(ang) * 1.0, endp[1] + math.sin(ang) * 1.0, max(endp[2] * .6, endp[3] * .75), endp[3] * .80, 1.2)
            p0 = Vector((endp[0] + math.cos(ang) * 2.7, endp[1] + math.sin(ang) * 2.7, endp[3] * .46))
            knee = (p0.x, p0.y, p0.z + .08, endp[3] * .58, 1.35)
            run = [k1, knee] + ground_run(p0, ang, L, endp[3] * .45, R, wig=R.uniform(1.2, 2.2), lift=.2, taper=1.3)
            runs[sd].append(run)
            add(tube(f'DR01_Strand{sd}{k}', run[::-1] + mid, seed=20 + k * 4.1 + sd * 13.7, rib=.26, twist=.10, collection=coll, moss_bias=crown_moss))

    # ---- 嵌在三股之間凹溝裡的小根（跟著主根一起絞），加上半埋在樹皮上斜著跨過去的中等根和細根 ----
    # 拱身讀起來是「三股粗根絞成的一根粗幹」，小根只是嵌在上面；不是十幾條一樣粗的根綁成一束
    G0 = PH0 + math.pi / 3                    # 主根之間的溝
    WRAPS = ((TURNS, .26, G0, 1.10), (TURNS, .22, G0 + 2.09, .92), (TURNS, .30, G0 + 4.19, 1.12),
             (-.45, .34, 2.2, 1.26), (1.6, .28, 4.6, 1.25),
             (TURNS * 1.12, .20, 1.4, 1.30), (.25, .18, .4, 1.32))
    for k, (turns, r_e, ph0, w0) in enumerate(WRAPS):
        w0 *= THICK[0] / .95                    # 跟著主根的粗細縮放，才會嵌在樹皮上而不是浮在外面
        def wp(t):
            c = centre(t)
            d, side, nrm = frame(t)
            ph = ph0 + t * 2 * math.pi * turns
            e = min(t, 1 - t)
            w = w0 * leg_scale(t) + .08 * math.sin(t * 11 + k) + .35 * max(0.0, 1 - e / .16) ** 1.5
            q = c + side * math.cos(ph) * w * 1.05 + nrm * math.sin(ph) * w * .85
            fo = max(0.0, 1 - e / .20) ** 2
            q += Vector((-1 if t < .5 else 1, 0, 0)) * fo * (.9 * max(0.0, math.sin(ph))) + side * math.cos(ph) * fo * .7
            return q, e
        wsd = k % 2                              # v003：每條小根只走一條大根，到交叉點前嵌回去
        angs = []
        for foot, t_end in ((0, .06), (1, .94)):
            q, e = wp(t_end)
            c = centre(0 if foot == 0 else 1)
            base = math.pi if foot == 0 else 0.0
            sgn = 1 if foot == 0 else -1
            angs.append(base - sgn * max(-1, min(1, (q.y - c.y) / .9)) * R.uniform(.9, 1.3) + R.uniform(-.15, .15))
        dirs = [Vector((math.cos(a), math.sin(a), 0)) for a in angs]
        mid = []
        n = 30
        ta, tb = (.06, .47) if wsd == 0 else (.53, .94)
        for i in range(n + 1):
            t = ta + (tb - ta) * i / n
            q, e = wp(t)
            q = q + foot_flare(t, dirs, FLARE * .8)
            fade = max(.25, min(1.0, (.5 - abs(t - .5)) / .10 + .25))       # 靠近交叉點變細、嵌進樹皮
            r = r_e * (1 + .12 * math.sin(t * 21 + k)) * (1 + .2 * max(0.0, 1 - e / .14)) * fade
            mid.append((q.x, q.y, max(q.z, r * .45), r, 1.0))
        if wsd == 1:
            mid = mid[::-1]
        endp = mid[0]
        run = ground_run(Vector(endp[:3]), angs[wsd], R.uniform(6.8, 9.2), endp[3] * .9, R, wig=R.uniform(1.0, 1.8), lift=.3)
        runs[wsd].append(run)
        pts = run[::-1] + mid
        add(tube(f'DR01_Wrap{k}', pts, seed=40 + k * 5.3, rib=.24, twist=.14, collection=coll, moss_bias=crown_moss))

    # ---- 根裙：一條條板根從拱腿流下來，各自朝自己要去的方向離開拱腿（正面的從正面出來、外側的從外側出來），
    #      落地後扇形散開。朝正面的幾條在 V2 裡是從兩腳朝鏡頭掃過來的大根 ----
    for foot in (0, 1):
        base = math.pi if foot == 0 else 0.0
        out = Vector((-1 if foot == 0 else 1, 0, 0))
        cf = centre(0.0 if foot == 0 else 1.0)
        sgn = 1 if foot == 0 else -1
        taken = sorted(foot_phi[q, foot] for q in range(3))
        edges = [-1.62] + taken + [1.62]
        gaps = sorted(((edges[i + 1] - edges[i], .5 * (edges[i] + edges[i + 1])) for i in range(4)), reverse=True)
        majors = [c for w, c in gaps[:3] if w > .55]
        fan = [(c + R.uniform(-.06, .06), True) for c in majors]
        for q in range(17):
            phi = -1.5 + 3.0 * q / 16
            if min(abs(phi - a) for a in taken + majors) > .13:
                fan.append((phi, False))
        for j, (da, major) in enumerate(sorted(fan)):
            ang = base + sgn * da + R.uniform(-.08, .08)
            hi = .04 + .13 * (1 - abs(da) / 1.6) * R.uniform(.45, 1.0)      # 小根：正外側的最高從 3 m 出頭流下來，一層一層疊在大根下面
            r0 = R.uniform(.17, .33) * (1.0 if abs(da) < 1.25 else .8)
            outward = major and abs(da) < .6
            if major:
                # 朝外的大根從拱腿半腰（約 4–4.6 m）就離開，一路斜掃到地面：正面看，拱腿外緣是一道往外甩的弧（設定圖兩隻腳都是）。
                # 朝正面的從腰以下（約 2–2.6 m）才出來，正面看得到整條拱腿；朝背面的從肩膀（3–4 m）掃下來
                hi = R.uniform(.225, .255) if outward else (R.uniform(.09, .12) if da > 0 else R.uniform(.15, .20))
                r0 = R.uniform(.36, .46)
            dirv = Vector((math.cos(ang), math.sin(ang), 0))                 # 這條根落地後要去的方向
            reach = (4.5 if outward else 4.0) if major else 2.1
            pts = []
            prof = ((0.0, .55, 1.0), (.3, .95, 1.4), (.62, 1.06, 1.5), (.9, 1.0, 1.35)) if major else ((0.0, .55, 1.0), (.3, .95, 1.3), (.62, 1.05, 1.35), (.9, 1.0, 1.2))
            for s, rk, fl in prof:      # 靠拱腿那段是立起來的板根
                tt = hi * (1 - s) + .015 * s
                tt = tt if foot == 0 else 1 - tt
                c = centre(tt)
                off = (.50 + 1.20 * min(1.0, s * 2.4)) * leg_scale(tt) + reach * s * s
                p = c + dirv * off
                pts.append((p.x, p.y, max(p.z * (1 - (.20 if outward else .28) * s), r0 * .5), r0 * rk, fl))      # 越往外越貼近地面，根底下不留大空洞
            dist = off + (R.uniform(.9, 1.8) if major else R.uniform(.5, 1.2))
            land = Vector((cf.x + dirv.x * dist, cf.y + dirv.y * dist, r0 * .5))
            pts.append((land.x, land.y, land.z + .10, r0, 1.3))
            L = (R.uniform(5.0, 7.0) if major else R.uniform(5.4, 8.8)) * (1.0 if abs(da) < 1.25 else .75)
            run = ground_run(land, ang + R.uniform(-.25, .25), L, r0 * .95, R, wig=R.uniform(.9, 2.0), dive=.8, lift=.10)
            runs[foot].append(run)
            add(tube(f'DR01_Foot{foot}_{j}', pts + run, seed=60 + foot * 10 + j * 1.7, rib=.24, twist=.12, collection=coll))

        # ---- 夾路根：從拱腳前後各一條，沿著路邊朝南（鏡頭）和朝北爬出去，V2 裡是把視線帶進拱洞的那兩條 ----
        for sg, r0, L in ((-1, R.uniform(.46, .56), R.uniform(9.5, 11.0)), (1, R.uniform(.32, .38), R.uniform(6.5, 8.0))):
            pts = []
            for tt0, lat, rk in ((.11, 1.15, .70), (.06, 1.55, .92), (.025, 2.1, 1.0)):
                tt = tt0 if foot == 0 else 1 - tt0
                c = centre(tt)
                d, side, nrm = frame(tt)
                q = c + side * (sg * lat) - nrm * .15
                pts.append((q.x, q.y, max(q.z, r0 * .5), r0 * rk, 1.1))
            land = Vector((cf.x - out.x * .2, cf.y + sg * 3.4, r0 * .5))
            pts.append((land.x, land.y, land.z + .08, r0, 1.25))
            ang = math.atan2(sg, -out.x * (R.uniform(.16, .26) if sg < 0 else R.uniform(.02, .10)))
            run = ground_run(land, ang, L, r0 * .95, R, wig=R.uniform(.7, 1.2), dive=.8, lift=.10, taper=1.2)
            runs[foot].append(run)
            add(tube(f'DR01_Flank{foot}_{"S" if sg < 0 else "N"}', pts + run, seed=150 + foot * 7 + sg, rib=.24, twist=.12, collection=coll))

        # ---- 岔根：從地面根中段岔出去，越岔越細 ----
        nb = 0
        for gen in range(2):
            src = list(runs[foot])
            for run in src:
                if len(run) < 5 or R.random() < (.25 if gen == 0 else .6):
                    continue
                i = R.randint(2, max(2, len(run) - 4))
                x, y, z, r, fl = run[i]
                if r < .12:
                    continue
                x2, y2 = run[i + 1][0], run[i + 1][1]
                a0 = math.atan2(y2 - y, x2 - x)
                a2 = a0 + R.choice([-1, 1]) * R.uniform(.4, .95)
                r0 = r * R.uniform(.5, .72)
                p0 = Vector((x, y, z - r * .25))
                room = 14.3 - math.hypot(abs(x) - abs(cf.x), y - cf.y)      # 根尾離拱腳不超過 15 m
                if room < 1.5:
                    continue
                sub = ground_run(p0, a2, min(room, R.uniform(2.5, 6.0) * (1 if gen == 0 else .7)), r0, R, wig=R.uniform(.5, 1.2), dive=.5, n=7)
                runs[foot].append(sub)
                add(tube(f'DR01_Fork{foot}_{nb}', [(p0.x, p0.y, p0.z, r0 * .9, 1.0)] + sub, seed=120 + foot * 30 + nb, rib=.2, twist=.18, collection=coll))
                nb += 1

    # ---- 貼著主根爬的細藤根 ----
    for j in range(3):
        ph0 = R.uniform(0, 6.3)
        t0, t1 = (R.uniform(.14, .22), .46) if j % 2 == 0 else (.54, R.uniform(.78, .86))
        r0 = R.uniform(.08, .13)
        pts = []
        for i in range(30):
            t = t0 + (t1 - t0) * i / 29
            c = centre(t)
            d, side, nrm = frame(t)
            ph = j * 2 * math.pi / 3 + PH0 + t * 2 * math.pi * TURNS + .5 * math.sin(t * 13 + ph0)
            w = (WOFF[j] + THICK[j] * .90) * leg_scale(t)
            p = c + side * math.cos(ph) * w * 1.05 + nrm * math.sin(ph) * w * .85
            pts.append((p.x, p.y, p.z, r0 * (1 - .35 * abs(2 * i / 29 - 1)), 1.0))
        add(tube(f'DR01_Liana{j}', pts, seed=90 + j, rib=.15, twist=.25, nu=None if low else (14 if quick else 20), collection=coll, moss_bias=-.1))
    tris = sum(len(o.data.polygons) * 2 for o in objs)
    print('DR01 high objects', len(objs), 'tris', tris)
    return objs


def dress(objs, quick=True, seed=5):
    import dr01_dress
    importlib.reload(dr01_dress)
    return dr01_dress.dress(objs, centre, frame, fb, PATH_HALF, quick=quick, seed=seed)
