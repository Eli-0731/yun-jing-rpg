"""地形件：S01 溪流（依使用者提供的溪流三視圖建模）。

參考圖只有水體：S 形水面、邊緣細碎波浪、表面漣漪與白色水花，側視為薄片。
使用者指示這次 demo 不必照 S 形，因此中線改為直段（只保留極輕微的擺動），寬度、岸線波浪、水花與薄片厚度照參考圖。
本件就是水面本身（封閉薄透鏡體，中央厚 6 cm、邊緣收為 0），不含河床；
原點在上游端中線、z = 0 為平均水面，水流朝 +Y。UV：U 橫越水面、V 沿流向（公尺 × 0.6），引擎可捲動 V 做流動。
SOCKET_kit_B01：B01 舊水路基座的原點應放的位置（入水口伸入水面 10 cm，基座地面 = 水面 − 0.28 m）。
"""
import math

import bmesh
from mathutils import Vector, noise

from kit_lib import WATER_Z

PX = 12.0 / 1125.0                  # 參考俯視圖 1125 px ≈ 12 m
# 俯視圖中線取樣（像素，x 向右＝下游、y 向下）；轉換：本件 y = (px − 40)·PX、x = (py − 172)·PX
# demo 版：直段中線（兩端對齊 x = 0，中段僅 ±6 cm 自然擺動）；寬度約 1.8 m，中段略寬
CENTER_PX = [(40, 172), (321, 167), (603, 177), (884, 168), (1165, 172)]
WIDTH_PX = [(40, 165), (400, 172), (760, 178), (1165, 165)]   # 各處水面寬（像素）
THICK = 0.06                        # 中央厚度
STEP = 0.08                         # 沿流向取樣間距
COLS = 18                           # 橫向分段
UV_K = 0.6


def _catmull(pts, n):
    out = []
    p = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = (Vector(q) for q in p[i - 1:i + 3])
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t))
    out.append(Vector(pts[-1]))
    return out


def _interp(table, x):
    for (x0, y0), (x1, y1) in zip(table, table[1:]):
        if x <= x1:
            t = (x - x0) / (x1 - x0)
            t = t * t * (3 - 2 * t)
            return y0 + (y1 - y0) * t
    return table[-1][1]


def stations():
    """沿中線等距取站：(點, 單位切線, 左法線, 弧長, 左半寬, 右半寬)。"""
    raw = _catmull([((py - 172) * PX, (px - 40) * PX) for px, py in CENTER_PX], 24)
    dense, s = [raw[0]], [0.0]
    for q in raw[1:]:
        s.append(s[-1] + (q - dense[-1]).length)
        dense.append(q)
    total = s[-1]
    out = []
    n = int(total / STEP)
    j = 0
    for k in range(n + 1):
        st = total * k / n
        while j < len(s) - 2 and s[j + 1] < st:
            j += 1
        t = (st - s[j]) / max(s[j + 1] - s[j], 1e-9)
        p = dense[j].lerp(dense[j + 1], t)
        tan = (dense[j + 1] - dense[j]).normalized()
        nl = Vector((-tan.y, tan.x))
        w = _interp(WIDTH_PX, 40 + st / PX) * PX
        # 岸線細碎波浪：低頻起伏＋高頻扇貝，兩岸各自不同
        wl = w / 2 + noise.noise(Vector((st * 0.45, 1.3, 0))) * 0.10 + noise.noise(Vector((st * 2.6, 4.1, 0))) * 0.035
        wr = w / 2 + noise.noise(Vector((st * 0.45, 7.7, 0))) * 0.10 + noise.noise(Vector((st * 2.6, 9.2, 0))) * 0.035
        if k in (0, n):                                    # 兩端截面平直（與下一段溪流拼接）
            wl = wr = w / 2
        out.append((p, tan, nl, st, wl, wr))
    return out


def _surface(x, y, edge):
    """水面起伏：大波 ±1 cm＋細漣漪 ±0.5 cm；靠岸 edge→0 時收平。"""
    q = Vector((x * 0.9, y * 0.9, 0.0))
    r = Vector((x * 4.5, y * 3.0, 2.0))
    return (noise.noise(q) * 0.010 + noise.noise(r) * 0.005) * edge


def S01(b):
    """溪流（demo 直段）：水面 12 m（沿 +Y），寬約 1.8 m，薄透鏡體。"""
    sts = stations()
    bm = bmesh.new()
    top, bot = [], []
    for p, tan, nl, st, wl, wr in sts:
        rt, rb = [], []
        for c in range(COLS + 1):
            u = c / COLS
            o = wl - (wl + wr) * u                         # 左正右負的橫向偏移
            half = wl if o >= 0 else wr
            e = 1.0 - min(1.0, abs(o) / max(half, 1e-6)) ** 4    # 中央 1、岸邊 0
            x, y = p.x + nl.x * o, p.y + nl.y * o
            zt = _surface(x, y, e ** 0.5)
            v = bm.verts.new((x, y, zt))
            rt.append(v)
            if c in (0, COLS):
                rb.append(v)                               # 岸線上下共用頂點，邊緣收為 0 厚
            else:
                rb.append(bm.verts.new((x, y, zt * 0.3 - THICK * e)))
        top.append(rt)
        bot.append(rb)
    for a, c in zip(range(len(sts) - 1), range(1, len(sts))):
        for k in range(COLS):
            bm.faces.new((top[a][k], top[a][k + 1], top[c][k + 1], top[c][k]))
            if 0 < k < COLS - 1:
                bm.faces.new((bot[a][k], bot[c][k], bot[c][k + 1], bot[a][k + 1]))
            elif k == 0:
                bm.faces.new((bot[a][0], bot[c][1], bot[a][1]))
                bm.faces.new((bot[a][0], bot[c][0], bot[c][1]))
            else:
                bm.faces.new((bot[a][k], bot[c][k], bot[a][k + 1]))
                bm.faces.new((bot[c][k], bot[c][k + 1], bot[a][k + 1]))
    for idx, flip in ((0, False), (len(sts) - 1, True)):   # 端面：截面中心扇形
        p = sts[idx][0]
        ctr = bm.verts.new((p.x, p.y, -THICK * 0.45))
        ring = top[idx] + bot[idx][-2:0:-1]
        for k in range(len(ring)):
            f = (ring[k], ring[(k + 1) % len(ring)], ctr)
            bm.faces.new(f[::-1] if not flip else f)

    # 逐點明暗：岸邊淺亮、中央深；外彎側（離中線較遠的一側）略亮帶白（水花多）
    def shade_fn(co, normal, mat=None):
        best = min(sts, key=lambda q: (q[0].x - co.x) ** 2 + (q[0].y - co.y) ** 2)
        p, tan, nl, st, wl, wr = best
        o = (co.x - p.x) * nl.x + (co.y - p.y) * nl.y
        e = min(1.0, abs(o) / max(wl if o >= 0 else wr, 1e-6))
        k = 0.82 + 0.26 * e ** 2
        return (k * 0.97, k, k)

    def uv_fn(co):
        best = min(sts, key=lambda q: (q[0].x - co.x) ** 2 + (q[0].y - co.y) ** 2)
        p, tan, nl, st, wl, wr = best
        o = (co.x - p.x) * nl.x + (co.y - p.y) * nl.y
        a = (co.x - p.x) * tan.x + (co.y - p.y) * tan.y
        return (o * UV_K, (st + a) * UV_K)

    b.props.update(shade_fn=shade_fn, uv_fn=uv_fn)
    b._merge("body", "ww_stream", bm, (1.0, 1.0, 1.0), bevel=0.0, jitter=0.0)

    # B01 取水掛點：右岸（+X 側）溪段中點，B01 入水口朝向水面
    k = len(sts) // 2
    p, tan, nl, st, wl, wr = sts[k]
    edge = p - nl * wr
    org = edge + nl * 0.10 - nl * 1.8                       # 入水口（B01 本地 y = −1.8）伸入水面 10 cm
    theta = math.atan2(nl.x, -nl.y)
    b.socket("kit_B01", (round(org.x, 4), round(org.y, 4), -WATER_Z), (0.0, 0.0, round(theta, 5)))

    prof = [[round(q[0].x, 4), round(q[0].y, 4), round(q[2].x, 4), round(q[2].y, 4), round(q[4], 4), round(q[5], 4)]
            for q in sts[::3]] + [[round(sts[-1][0].x, 4), round(sts[-1][0].y, 4), round(sts[-1][2].x, 4),
                                   round(sts[-1][2].y, 4), round(sts[-1][4], 4), round(sts[-1][5], 4)]]
    total = sts[-1][3]
    return dict(name="溪流", family="S01", variant="S01", ref="S01_stream_three_view_v001.jpg",
                extra=dict(is_water=True, length_m=round(total, 3), profile=prof,
                           profile_fields=["x", "y", "left_nx", "left_ny", "half_w_left", "half_w_right"],
                           intake_station_m=round(st, 3)),
                states=dict(flow=dict(uv_scroll_axis="V", uv_per_m=UV_K, note="V 沿流向，捲動 V 即為水流動畫")),
                collision="水面不碰撞；需要時以觸發體判定入水",
                notes=["依使用者提供的溪流三視圖建模：參考圖只有水體，本件即水面（封閉薄透鏡體），不含河床與河岸。",
                       f"使用者指示 demo 不必照 S 形：中線改為直段（中段 ±6 cm 擺動），全長 {total:.2f} m、寬約 1.8 m"
                       "（寬度依俯視圖量測換算，推定）。",
                       "側視、正視只見薄片：中央厚 6 cm、岸線收為 0；表面大波 ±1 cm、細漣漪 ±0.5 cm。",
                       "白色水花、光網、漣漪法線在 ww_stream 貼圖；深淺用頂點色（中央深、岸邊淺）。",
                       "兩端截面平直、與水流方向垂直，可接下一段溪流；與石槽套件的銜接透過 SOCKET_kit_B01（B01 取水口）。",
                       "本件是水，依套件規則「預覽不顯示水」不適用於本件，預覽直接呈現水面。"])


# ------------------------------------------------------------------ S02 河床與河岸

BED_EXT = 0.35                      # 河床延伸到水邊外 35 cm
BANK_D = [(0.15, -0.30), (0.15, -0.04), (0.35, 0.05), (0.60, 0.20), (0.85, 0.31), (1.15, 0.33), (1.45, 0.14),
          (1.80, -0.28), (1.80, -0.30)]  # 河岸截面（d：由水邊往外的距離，z：相對水面）
BASE_Z = -0.30                      # 底面（＝石槽地面 −0.28 再下 2 cm）
NOTCH = 0.78                        # 取水缺口：B01 寬 1.4 m，左右各留 8 cm
BANK_TINT = (0.86, 0.82, 0.78)      # 河岸土色比田土灰一些（對照參考圖）


def _bed_z(o, half, x, y):
    t = abs(o) / max(half, 1e-6)
    n = noise.noise(Vector((x * 3.0, y * 3.0, 5.0))) * 0.008
    if t <= 1.0:
        return -0.065 + 0.06 * t * t + n
    return -0.005 + (abs(o) - half) / BED_EXT * 0.035 + n


def _bank_z(d, z, st, side):
    """河岸截面高度加起伏：坡頂 ±3 cm、坡面輕微鼓凹（底部兩點不動）。"""
    if z <= -0.27:
        return z
    q = Vector((st * 0.7, side * 3.3, d))
    amp = 0.03 if d >= 0.8 else 0.018
    return z + noise.noise(q) * amp + noise.noise(q * 3.1) * amp * 0.35


def _loft(b, part, mat, rows, tint=(1, 1, 1), **kw):
    """rows：每站一圈 3D 點（同點數、同順序的封閉截面）；端面以截面中心扇形封口。"""
    bm = bmesh.new()
    rings = [[bm.verts.new(p) for p in r] for r in rows]
    m = len(rows[0])
    for a, c in zip(rings, rings[1:]):
        for i in range(m):
            bm.faces.new((a[i], a[(i + 1) % m], c[(i + 1) % m], c[i]))
    for ring, flip in ((rings[0], True), (rings[-1], False)):
        ctr = bm.verts.new(sum((v.co for v in ring), Vector()) / m)
        for i in range(m):
            f = (ring[i], ring[(i + 1) % m], ctr)
            bm.faces.new(f[::-1] if flip else f)
    b._merge(part, mat, bm, tint, **kw)


def S02(b):
    """河床與河岸（demo 直段，與 S01 同原點、同中線、同岸線）。右岸在 B01 取水掛點留缺口。"""
    sts = stations()[::2]
    k_in = len(stations()) // 2
    s_in = stations()[k_in][3]

    # 逐點明暗：坡頂草皮染綠（斑塊）、坡面土層條紋、水面下河床與石頭偏濕暗
    def shade_fn(co, normal, mat=None):
        if mat == "ww_field_soil":
            g = max(0.0, min(1.0, (co.z - 0.20) / 0.08)) * (1.0 if normal.z > 0.45 else 0.35)
            g *= 0.6 + 0.4 * max(0.0, noise.noise(Vector((co.x * 2.2, co.y * 2.2, 1.0))) + 0.5)
            layer = 0.9 if math.sin(co.z * 38 + noise.noise(co * 2.0) * 2) > 0.65 else 1.0
            r, gg, bb = 1 - 0.45 * g, 1 - 0.05 * g, 1 - 0.58 * g
            return (r * layer, gg * layer, bb * layer)
        if mat in ("ww_riverbed", "ww_stone", "ww_stone_moss"):
            wet = 0.9 if co.z < -0.002 else 1.0
            return (wet, wet, wet * 1.02)
        return (1.0, 1.0, 1.0)

    b.props.update(shade_fn=shade_fn)

    def notch_f(st):                                     # 0：缺口內、1：正常
        return max(0.0, min(1.0, (abs(st - s_in) - NOTCH) / 0.12))

    # 河床：橫向 18 點，右緣在缺口處縮回 B01 背牆內側
    rows = []
    for p, tan, nl, st, wl, wr in sts:
        f = notch_f(st)
        r_ext = (wr - 0.12) * (1 - f) + (wr + BED_EXT) * f
        top = []
        for i in range(18):
            o = (wl + BED_EXT) - (wl + BED_EXT + r_ext) * i / 17
            x, y = p.x + nl.x * o, p.y + nl.y * o
            top.append(Vector((x, y, _bed_z(o, wl if o >= 0 else wr, x, y))))
        bot = [Vector((q.x, q.y, BASE_Z)) for q in (top[-1], top[0])]
        rows.append(top + bot)
    _loft(b, "body", "ww_riverbed", rows, bevel=0.0, jitter=0.0)

    # 河岸：左岸一整段；右岸在取水缺口前後分兩段
    def bank_rows(side, seg):
        out = []
        for p, tan, nl, st, wl, wr in seg:
            half = wl if side > 0 else wr
            ring = []
            for d, z in BANK_D:
                o = side * (half + d)
                ring.append(Vector((p.x + nl.x * o, p.y + nl.y * o, _bank_z(d, z, st, side))))
            out.append(ring if side > 0 else ring[::-1])
        return out

    _loft(b, "body", "ww_field_soil", bank_rows(1, sts), tint=BANK_TINT, bevel=0.0, jitter=0.003)
    up = [q for q in sts if q[3] <= s_in - NOTCH]
    dn = [q for q in sts if q[3] >= s_in + NOTCH]
    for seg in (up, dn):
        _loft(b, "body", "ww_field_soil", bank_rows(-1, seg), tint=BANK_TINT, bevel=0.0, jitter=0.003)

    def surf_z(o, st_q):
        p, tan, nl, st, wl, wr = st_q
        side = 1 if o >= 0 else -1
        half = wl if o >= 0 else wr
        d = abs(o) - half
        x, y = p.x + nl.x * o, p.y + nl.y * o
        zb = _bed_z(o, half, x, y)
        if d < 0.15:
            return zb
        for (d0, z0), (d1, z1) in zip(BANK_D[1:], BANK_D[2:]):
            if d0 <= d <= d1:
                t = (d - d0) / (d1 - d0)
                zk = _bank_z(d0, z0, st, side) * (1 - t) + _bank_z(d1, z1, st, side) * t
                return max(zb, zk)
        return zb

    def in_notch(o, st):
        return o < 0 and abs(st - s_in) < NOTCH + 0.12

    # 碎石帶：兩岸水邊內外；大圓石散在河床
    from pieces_field import pebble, tuft
    for _ in range(90):
        q = b.rng.choice(sts[2:-2])
        side = b.rng.choice((1, -1))
        half = q[4] if side > 0 else q[5]
        o = side * (half + b.rng.uniform(-0.18, 0.32))
        if in_notch(o, q[3]):
            continue
        s = b.rng.uniform(0.03, 0.085)
        c = q[0] + q[2] * o
        pebble(b, (c.x, c.y, surf_z(o, q) + s * 0.08), (s * 1.25, s, s * 0.65), tint=b.stone_tint(0.92))
    for _ in range(7):
        q = b.rng.choice(sts[4:-4])
        o = b.rng.uniform(-0.75, 0.75) * (q[4] if b.rng.random() < 0.5 else q[5])
        if in_notch(o, q[3]):
            continue
        s = b.rng.uniform(0.15, 0.27)
        c = q[0] + q[2] * o
        pebble(b, (c.x, c.y, surf_z(o, q) + s * 0.12), (s * 1.15, s, s * 0.7), tint=b.stone_tint(0.98))
    # 草叢：坡頂一排、坡肩垂草
    for q in sts[1:-1]:
        for side in (1, -1):
            if b.rng.random() > 0.55:
                continue
            half = q[4] if side > 0 else q[5]
            d = b.rng.uniform(0.78, 1.32)
            o = side * (half + d)
            if in_notch(o, q[3]):
                continue
            c = q[0] + q[2] * o
            tuft(b, (c.x, c.y, surf_z(o, q) - 0.01), r=b.rng.uniform(0.06, 0.11), blades=5,
                 h=b.rng.uniform(0.08, 0.15))

    return dict(name="河床與河岸", family="S02", variant="S02", ref="S02_riverbed_banks_three_view_v001.jpg",
                preview_ground=BASE_Z,
                extra=dict(pairs_with="S01", intake_notch_station_m=round(s_in, 3), notch_half_len_m=NOTCH),
                collision="河床為地面碰撞；河岸坡面與坡頂需碰撞（尚未製作）",
                notes=["依使用者提供的「河床與河岸｜三視圖」建模；參考圖為 S 形，但 S01 溪流已依使用者指示做成 demo 直段，"
                       "河床與河岸沿用 S01 的中線與岸線（同原點），兩件疊放即對齊。",
                       "河床：水邊以內為淺碟形（中央低於水面 6.5 cm），往外 35 cm 收到岸腳；材質 ww_riverbed（沙礫）。",
                       "河岸：坡頂高出水面約 0.33 m，外側緩坡降到 −0.28 m（＝石槽、田地所在地面），坡頂草皮與草叢、坡面土層條紋。",
                       f"右岸在 SOCKET_kit_B01（S01）處留 {NOTCH * 2:.2f} m 取水缺口，河床右緣縮到 B01 背牆內側，B01 可直接坐進去。",
                       "水邊碎石帶與河床大圓石依參考圖散佈（程序化、固定亂數種子）。"])
