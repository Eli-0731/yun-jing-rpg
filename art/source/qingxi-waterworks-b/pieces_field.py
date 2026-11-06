"""地形件：F01 灌溉田地（依使用者提供的「灌溉田地｜三視圖」建模）。

接口沿用石槽套件：入口在原點、水流朝 +Y；田地另一端的出水口 out 在 (0, L)。
田埂、田畦、溝底都是封閉土塊；水面一律是獨立網格，預覽不顯示。
參考圖為 AI 概念圖，俯視與側視比例互相矛盾，尺寸以俯視為準，其餘寫在 notes 標「推定設計」。
"""
import math

import bmesh
from mathutils import Vector, noise

from kit_lib import CLEAR_W, FLOOR_T, OUTER_W, TOTAL_H, WATER_Z, channel, floor_run, line, wall_run
from pieces_b2 import _wood_tint

W, L = 6.0, 4.0                     # 外框（x 寬 × y 長），出入口落在 25 cm 拼接格
HALF_O = OUTER_W / 2
HALF_C = CLEAR_W / 2
SLOT = 0.04                         # 沉板槽寬（堰板厚 3 cm）
WEIR_H = 0.22                       # 堰板高：預設堰頂 0.28 時板底沉入槽內 4 cm
STEM = 0.34                         # 螺桿長（堰板全降時仍穿出手輪）
PLANKS = 4                          # 出水口疊板片數
CREST_FULL = 0.30                   # 疊板卡滿（預設）：田面保水上限
BUND_IN = 0.63                      # 田埂外緣到內側溝底邊的水平距離
BED_TOP = 0.34                      # 田畦頂（水面 0.28 以上 6 cm）
FURROW = 0.26                       # 畦間水溝底寬（畦：溝約 2.4：1，對照俯視圖）
N_BEDS = 5

# 田埂截面（d：由外緣向內的水平距離，z：高度），凸多邊形，頂面略拱
BUND_PROFILE = [(0.0, 0.0), (0.12, 0.25), (0.25, 0.395), (0.40, 0.412), (0.55, 0.395),
                (BUND_IN, 0.10), (BUND_IN + 0.03, 0.0)]


def _smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def mound(b, part, mat, x0, x1, y0, y1, z0, top_fn, nx, ny, inset=0.0, round_r=0.0, cluster=False, tint=None, **kw):
    """底面為矩形、頂面為格點高度場的封閉土塊；側面由底緣斜收到頂緣（inset）。

    底面用中心扇形三角面封口，避免長條 n-gon 三角化出零面積三角形。round_r > 0 時平面轉角收成圓角；
    cluster=True 時格線往邊緣加密（餘弦分布），畦肩的圓弧才有足夠段數。
    """
    def rounded(x, y, ax0, ax1, ay0, ay1):
        if round_r <= 0:
            return x, y
        cx = min(max(x, ax0 + round_r), ax1 - round_r)
        cy = min(max(y, ay0 + round_r), ay1 - round_r)
        dx, dy = x - cx, y - cy
        d = math.hypot(dx, dy)
        if d <= round_r or d < 1e-9:
            return x, y
        return cx + dx / d * round_r, cy + dy / d * round_r

    bm = bmesh.new()
    top = {}
    for j in range(ny + 1):
        for i in range(nx + 1):
            u, v = i / nx, j / ny
            if cluster:
                u, v = 0.5 - 0.5 * math.cos(math.pi * u), 0.5 - 0.5 * math.cos(math.pi * v)
            x = x0 + inset + (x1 - x0 - 2 * inset) * u
            y = y0 + inset + (y1 - y0 - 2 * inset) * v
            x, y = rounded(x, y, x0 + inset, x1 - inset, y0 + inset, y1 - inset)
            top[i, j] = bm.verts.new((x, y, top_fn(x, y, u, v)))
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((top[i, j], top[i + 1, j], top[i + 1, j + 1], top[i, j + 1]))
    ring = [(i, 0) for i in range(nx)] + [(nx, j) for j in range(ny)] + \
           [(i, ny) for i in range(nx, 0, -1)] + [(0, j) for j in range(ny, 0, -1)]
    bot = []
    for i, j in ring:
        u, v = i / nx, j / ny
        if cluster:
            u, v = 0.5 - 0.5 * math.cos(math.pi * u), 0.5 - 0.5 * math.cos(math.pi * v)
        x, y = rounded(x0 + (x1 - x0) * u, y0 + (y1 - y0) * v, x0, x1, y0, y1)
        bot.append(bm.verts.new((x, y, z0)))
    m = len(ring)
    for k in range(m):
        a, c = ring[k], ring[(k + 1) % m]
        bm.faces.new((bot[k], bot[(k + 1) % m], top[c], top[a]))
    ctr = bm.verts.new(((x0 + x1) / 2, (y0 + y1) / 2, z0))
    for k in range(m):
        bm.faces.new((bot[(k + 1) % m], bot[k], ctr))
    b._merge(part, mat, bm, tint or (1, 1, 1), **kw)


def bund_half(b, side, seed):
    """半圈田埂：從入口缺口沿外框繞到出水口缺口（side=-1 左半、+1 右半）。"""
    xe = side * HALF_O
    corners = [(xe, 0.0), (side * W / 2, 0.0), (side * W / 2, L), (xe, L)]
    # 沿路徑取站點；轉角用斜接法線（兩邊法線相加），讓截面在角上保持等寬
    stations = []
    for k in range(3):
        p0, p1 = Vector(corners[k]), Vector(corners[k + 1])
        seg = p1 - p0
        n_in = Vector((-seg.y, seg.x)).normalized() * side
        steps = max(2, int(seg.length / 0.22))
        for s in range(steps + (1 if k == 2 else 0)):
            t = s / steps
            p = p0 + seg * t
            n = n_in
            if s == 0 and k > 0:
                n = n_in + prev_n
            stations.append((p, n, k))
        prev_n = n_in
    sd = Vector((seed, seed * 1.7, 0.0))
    bm = bmesh.new()
    rings = []
    total = len(stations)
    for idx, (p, n, k) in enumerate(stations):
        end = min(idx, total - 1 - idx)                 # 兩端接石槽口，起伏收斂
        amp = _smooth(end / 3.0)
        q = Vector((p.x * 1.3, p.y * 1.3, 0.0)) + sd
        dz = (noise.noise(q) * 0.016 + noise.noise(q * 3.1) * 0.006) * amp
        bulge = noise.noise(q * 0.6 + Vector((7.0, 3.0, 0.0))) * 0.015 * amp
        ring = []
        for d, z in BUND_PROFILE:
            dd = d
            if 0.0 < d < BUND_IN and z > 0.05:
                dd = max(0.02, d - bulge * (1 - abs(d - 0.3) / 0.3))   # 外坡、頂面略鼓出或內凹
            zz = z + dz * (z / 0.41) if z > 0.0 else z
            ring.append(bm.verts.new((p.x + n.x * dd, p.y + n.y * dd, zz)))
        rings.append(ring)
    m = len(BUND_PROFILE)
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(m):
            bm.faces.new((r0[i], r0[(i + 1) % m], r1[(i + 1) % m], r1[i]))
    bm.faces.new(rings[0])
    bm.faces.new(rings[-1][::-1])
    b._merge("body", "ww_field_soil", bm, (1.0, 1.0, 1.0), bevel=0.012, jitter=0.004)


def pebble(b, center, size, tint=None):
    """小碎石：細分 1 次的二十面體（80 面），底部壓平。"""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    seed = Vector((b.rng.uniform(0, 40), b.rng.uniform(0, 40), b.rng.uniform(0, 40)))
    for v in bm.verts:
        d = 1.0 + 0.2 * noise.noise(v.co * 1.7 + seed)
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2])) * d * 0.5
        v.co.z = max(v.co.z, -size[2] * 0.25)
        v.co += Vector(center)
    b._merge("body", "ww_stone", bm, tint or b.stone_tint(0.9), bevel=0.0, jitter=0.0)


def tuft(b, center, r=0.06, blades=5, h=0.07):
    """草叢：數片細長四面體草葉，自中心向外傾。"""
    cx, cy, cz = center
    for k in range(blades):
        a = 2 * math.pi * k / blades + b.rng.uniform(-0.4, 0.4)
        lean = b.rng.uniform(0.3, 0.8) * r
        hh = h * b.rng.uniform(0.7, 1.25)
        bx, by = cx + math.cos(a) * r * 0.25, cy + math.sin(a) * r * 0.25
        w = 0.012
        bm = bmesh.new()
        p = [bm.verts.new((bx + math.cos(a + 1.57) * w, by + math.sin(a + 1.57) * w, cz - 0.01)),
             bm.verts.new((bx - math.cos(a + 1.57) * w, by - math.sin(a + 1.57) * w, cz - 0.01)),
             bm.verts.new((bx - math.cos(a) * w * 0.8, by - math.sin(a) * w * 0.8, cz - 0.01)),
             bm.verts.new((bx + math.cos(a) * lean, by + math.sin(a) * lean, cz + hh))]
        for f in ((0, 1, 2), (0, 3, 1), (1, 3, 2), (2, 3, 0)):
            bm.faces.new([p[i] for i in f])
        g = b.rng.uniform(0.8, 1.15)
        b._merge("body", "ww_grass", bm, (g, g, g), bevel=0.0, jitter=0.0)


def F01(b):
    """灌溉田地：田埂圍成 6 × 4 m 外框，入口石槽口在 y=0 中央，出水口在 y=4 中央。

    進水沿上緣橫溝向左右分流，經 6 道畦間水溝流到下緣集水溝，再由出水口離開；5 條田畦高出水面 6 cm。
    """
    b.props.update(moss=0.7, wet_line=WATER_Z - 0.01)
    b.port("in", (0, 0), (0, -1), "in")
    b.port("out", (0, L), (0, 1), "out")
    inner_x = W / 2 - BUND_IN                            # 2.37
    y_head0, y_head1 = BUND_IN, BUND_IN + 0.40           # 上緣分水橫溝
    y_drain1 = L - BUND_IN
    y_drain0 = y_drain1 - 0.40                           # 下緣集水溝

    # 石槽口：穿過田埂的標準 U 形短槽（外寬 60、淨寬 40、高 40），與套件直接相接
    channel(b, line((0, 0), (0, BUND_IN)), courses=2, lo=0.2, hi=0.34)
    # 出水石槽口：兩側牆照標準，底板在堰板處留 4 cm 沉板槽，槽下是埋地石匣（堰板降下時沉入）
    wy = y_drain1 + 0.30                                # 堰板中心線（石槽口中段）
    for off_in, off_out in ((HALF_C, HALF_O), (-HALF_O, -HALF_C)):
        wall_run(b, line((0, y_drain1), (0, L)), off_in, off_out, courses=2, lo=0.2, hi=0.34)
    floor_run(b, line((0, y_drain1), (0, wy - SLOT / 2)), lo=0.12, hi=0.2)
    floor_run(b, line((0, wy + SLOT / 2), (0, L)), lo=0.12, hi=0.2)
    pit_z = FLOOR_T - WEIR_H - 0.03                     # 石匣底（堰板全降時板頂齊溝底）
    for sy in (-1, 1):
        b.box("body", "ww_stone", (0, wy + sy * (SLOT / 2 + 0.03), (pit_z + FLOOR_T) / 2 - 0.05),
              (0.48, 0.06, FLOOR_T - pit_z - 0.10 + 0.0), tint=b.stone_tint(0.85), bevel=0.006)
    for sx in (-1, 1):
        b.box("body", "ww_stone", (sx * 0.22, wy, (pit_z + 0.0) / 2), (0.04, SLOT, -pit_z),
              tint=b.stone_tint(0.85), bevel=0.004)
    b.box("body", "ww_stone", (0, wy, pit_z - 0.02), (0.48, SLOT + 0.12, 0.04), tint=b.stone_tint(0.85), bevel=0.006)

    # 田埂（左右兩半，夾住兩個石槽口）
    bund_half(b, -1, 3.1)
    bund_half(b, 1, 11.7)

    # 溝底：整片濕土，頂面 z = FLOOR_T 附近微起伏（與石槽底板同高）
    def floor_fn(x, y, u, v):
        if abs(x) < 0.25 and (y < y_head0 + 0.06 or y > y_drain1 - 0.06):
            return FLOOR_T                               # 石槽口銜接處保持平整
        q = Vector((x * 2.3, y * 2.3, 0.5))
        return FLOOR_T + noise.noise(q) * 0.006
    mound(b, "body", "ww_field_soil", -inner_x - 0.06, inner_x + 0.06, y_head0, y_drain1, 0.0,
          floor_fn, 20, 10, tint=(0.95, 0.95, 0.95), bevel=0.0, jitter=0.0)

    # 田畦：底寬 bed_w、兩側斜收 7 cm，頂面中央微拱、土塊起伏
    bed_w = (2 * inner_x - (N_BEDS + 1) * FURROW) / N_BEDS
    by0, by1 = y_head1 + 0.02, y_drain0 - 0.02
    beds = []
    for i in range(N_BEDS):
        x0 = -inner_x + FURROW + i * (bed_w + FURROW)
        x1 = x0 + bed_w
        beds.append((x0, x1))
        sd = Vector((i * 5.3, i * 2.1, 0.0))

        def top_fn(x, y, u, v, sd=sd, x0=x0, x1=x1):
            # 整條田畦是一張高度場：邊緣貼溝底，往內 14 cm 以圓肩升到畦頂（夯土墩，不是方塊）
            de = min(x - x0, x1 - x, y - by0, by1 - y)
            t = max(0.0, min(1.0, de / 0.14))
            rise = math.sin(t * math.pi / 2) ** 0.8
            crown = 0.012 * (1 - (2 * u - 1) ** 2)
            q = Vector((x * 7.0, y * 7.0, 0.0)) + sd
            bump = (noise.noise(q) * 0.009 + noise.noise(q * 2.9) * 0.005) * t
            return FLOOR_T + 0.012 + (BED_TOP - FLOOR_T - 0.012 + crown) * rise + bump

        k = b.rng.uniform(0.92, 1.0)
        mound(b, "body", "ww_field_soil", x0, x1, by0, by1, FLOOR_T - 0.02, top_fn, 12, 26, round_r=0.10,
              cluster=True, tint=(k, k, k), bevel=0.0, jitter=0.004)
        b.socket(f"bed_{i + 1}", ((x0 + x1) / 2, (by0 + by1) / 2, BED_TOP + 0.01))

    # 溝口護石：畦溝兩端、貼畦角的低矮深色石（參考圖畦頭的小石），頂面低於畦頂
    edges = sorted({round(x, 4) for x0, x1 in beds for x in (x0, x1)} | {-inner_x, inner_x})
    for x in edges:
        for y in (by0 + 0.02, by1 - 0.02):
            s = b.rng.uniform(0.10, 0.13)
            pebble(b, (x, y, FLOOR_T + s * 0.28), (s * 1.1, s * 1.3, s * 1.05), tint=b.stone_tint(0.62))

    # 碎石：田埂外坡腳與頂面零星散落
    for _ in range(14):
        side = b.rng.choice(("x", "y"))
        if side == "x":
            x = b.rng.choice((-1, 1)) * (W / 2 - b.rng.uniform(0.07, 0.14))
            y = b.rng.uniform(0.4, L - 0.4)
        else:
            x = b.rng.uniform(0.7, W / 2 - 0.3) * b.rng.choice((-1, 1))
            y = b.rng.choice((b.rng.uniform(0.07, 0.14), L - b.rng.uniform(0.07, 0.14)))
        s = b.rng.uniform(0.04, 0.09)
        pebble(b, (x, y, s * 0.12), (s * 1.2, s, s * 0.7))
    for _ in range(6):
        x = b.rng.choice((-1, 1)) * (W / 2 - b.rng.uniform(0.32, 0.45))
        y = b.rng.uniform(0.8, L - 0.8)
        s = b.rng.uniform(0.035, 0.06)
        pebble(b, (x, y, 0.40), (s * 1.2, s, s * 0.6))

    # 草叢：田埂四角與外坡零星（參考圖的綠色苔草）
    spots = [(-2.78, 0.24), (-2.62, 0.18), (2.76, 0.24), (2.66, 3.8), (-2.74, 3.76), (2.8, 1.6), (-2.8, 2.3),
             (-1.6, 3.82), (1.2, 0.18), (2.8, 2.9), (-2.8, 1.1), (0.9, 3.82), (-1.9, 0.18), (2.0, 3.82)]
    for x, y in spots:
        for _ in range(b.rng.choice((2, 3, 3, 4))):
            px = x + b.rng.uniform(-0.08, 0.08)
            py = y + b.rng.uniform(-0.06, 0.06)
            d = min(W / 2 - abs(px), py, L - py)          # 離外緣距離 → 外坡高度
            z = max(0.0, min(0.40, d / 0.25 * 0.395)) - 0.005
            tuft(b, (px, py, z), r=b.rng.uniform(0.06, 0.10), blades=6, h=b.rng.uniform(0.08, 0.13))

    # 出水口疊板閘：一疊木板沿兩側木導槽上下移動，平時升到頂（堰頂 0.30）卡滿擋水；
    # 放水時轉手輪把整疊降進沉板槽，板頂＝溢流高度，可停在 0.10–0.30 m 任一高度。
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.box("body", "ww_wood", (sx * 0.1825, wy + sy * 0.03, 0.26), (0.035, 0.025, 0.32),
                  tint=_wood_tint(b), bevel=0.004, jitter=0.0)
        b.box("body", "ww_bronze", (sx * 0.1825, wy, 0.425), (0.042, 0.088, 0.012), bevel=0.002, jitter=0.0)
        for z in (0.16, 0.34):                          # 導槽固定銅片
            b.box("body", "ww_bronze", (sx * 0.199, wy, z), (0.006, 0.09, 0.03), bevel=0.0, jitter=0.0)
    # 牆頂橫梁（跨在兩側牆頂）＋青銅螺母座
    b.box("body", "ww_wood", (0, wy, TOTAL_H + 0.03), (0.70, 0.09, 0.06), tint=_wood_tint(b), bevel=0.008,
          jitter=0.0)
    for sx in (-1, 1):
        b.box("body", "ww_bronze", (sx * 0.30, wy, TOTAL_H + 0.03), (0.035, 0.096, 0.066), bevel=0.002, jitter=0.0)
    b.cylinder("body", "ww_bronze", (0, wy, TOTAL_H + 0.075), 0.032, 0.03, segs=16)
    # 疊板＋螺桿（部件 weir，建模位置＝堰頂 0.28；使用時預設升到 0.30 卡滿）
    # 依使用者要求：出水口平時由一疊橫木板卡滿擋水，要放水時再把整疊木板降進沉板槽，水從板頂溢流。
    zb = WATER_Z - WEIR_H
    gap = 0.004                                            # 板縫
    ph = (WEIR_H - (PLANKS - 1) * gap) / PLANKS
    for k in range(PLANKS):
        z0 = zb + k * (ph + gap)
        t = _wood_tint(b, 0.9 + 0.05 * (k % 2), 1.06)
        b.box("weir", "ww_wood", (b.rng.uniform(-0.002, 0.002), wy, z0 + ph / 2), (0.39, 0.032, ph), tint=t,
              bevel=0.005, jitter=0.0015)
    for sx in (-1, 1):                                     # 兩端鐵包角，把整疊木板串成一組
        b.box("weir", "ww_iron", (sx * 0.183, wy, zb + WEIR_H / 2), (0.022, 0.036, WEIR_H - 0.01),
              bevel=0.0015, jitter=0.0)
    for sx in (-1, 1):                                     # 頂板提環
        b.ring("weir", "ww_iron", (sx * 0.09, wy, WATER_Z + 0.012), 0.012, 0.017, 0.006, axis="Y", segs=12)
    b.box("weir", "ww_bronze", (0, wy, WATER_Z + 0.012), (0.07, 0.036, 0.024), bevel=0.002, jitter=0.0)  # 螺桿接座
    b.cylinder("weir", "ww_bronze", (0, wy, WATER_Z + 0.024 + STEM / 2), 0.011, STEM, segs=10)
    for k in range(int(STEM / 0.025)):                    # 螺紋（細環）
        b.cylinder("weir", "ww_bronze", (0, wy, WATER_Z + 0.04 + k * 0.025), 0.014, 0.006, segs=10)
    # 手輪（部件 weir_wheel，坐在螺母上，升降時原地旋轉）
    hz = TOTAL_H + 0.11
    b.ring("weir_wheel", "ww_bronze", (0, wy, hz), 0.075, 0.09, 0.016, axis="Z", segs=28)
    b.cylinder("weir_wheel", "ww_bronze", (0, wy, hz), 0.026, 0.03, segs=14)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        b.obox("weir_wheel", "ww_bronze", (0.05 * math.cos(a), wy + 0.05 * math.sin(a), hz), (0.06, 0.012, 0.01),
               (0, 0, a), tint=(1, 1, 1), bevel=0.0, jitter=0.0)
    b.cylinder("weir_wheel", "ww_wood", (0.083, wy, hz + 0.035), 0.01, 0.06, segs=8)        # 搖把

    # 水面（獨立網格，預覽隱藏）：入口流路、出口溢流，田內依水口板狀態三選一
    b.flow("inlet", line((0, 0), (0, y_head0 - 0.01)), frm="in", to="field")
    b.flow("outlet", line((0, wy + 0.016), (0, L)), frm="weir", to="out")
    pool = [(-inner_x - 0.04, y_head0 - 0.02), (inner_x + 0.04, y_head0 - 0.02), (inner_x + 0.04, y_drain1 + 0.02),
            (0.195, y_drain1 + 0.02), (0.195, wy - 0.016), (-0.195, wy - 0.016), (-0.195, y_drain1 + 0.02),
            (-inner_x - 0.04, y_drain1 + 0.02)]
    for name, z in (("field", WATER_Z), ("field_low", FLOOR_T + 0.025)):
        b.water_polys.append(dict(name=name, z=z, poly=pool))
    return dict(name="灌溉田地", family="F01", variant="F01", ref="F01_irrigated_field_three_view_v001.png",
                preview_ground=0.0,
                states=dict(
                    control="weir", crest_z_default=CREST_FULL, crest_z_min=FLOOR_T, crest_z_max=0.30,
                    weir_offset_z="crest_z - 0.28（部件 weir 沿 Z 平移；-0.18 全降、+0.02 最高）",
                    wheel=dict(part="weir_wheel", axis="Z", pitch_m_per_turn=0.025,
                               deg_per_cm=round(360 / 2.5, 1)),
                    water=dict(field="WATER_F01_field 的 z 設為 crest_z；crest_z < 0.125 時改顯示 WATER_F01_field_low",
                               inlet="WATER_F01_inlet 有進水時顯示",
                               outlet="WATER_F01_outlet 只在疊板降下（crest_z < 0.30）且田內有水時顯示"),
                    presets=dict(full=CREST_FULL, half=0.19, drain=FLOOR_T),
                    holding="crest_z = 0.30（疊板卡滿）時出水口不出水；降下才溢流",
                    dry=dict(water=[], desc="未通水：水面全部隱藏（預覽用）")),
                collision="田埂、田畦各自盒狀或凸包碰撞；溝底為地面；水面不碰撞（尚未製作）",
                notes=["依使用者提供的「灌溉田地｜三視圖」建模。參考圖含水；依套件規則，模型預覽一律不顯示水面，"
                       "水面另存 F01_water.glb。",
                       f"外框 {W:.0f} × {L:.0f} m：俯視圖寬長比約 1.5，側視圖反而畫得比正視長，兩者矛盾，以俯視為準（推定設計）。",
                       "出入口為標準 U 形石槽口（外寬 60、淨寬 40、高 40、底板 10 cm），可直接和 B 系列石槽相接。",
                       f"田埂頂高 0.40 m、頂寬約 0.30 m；溝底 z = 0.10 與石槽底板同高；田畦頂 {BED_TOP} m，"
                       f"水面 {WATER_Z} m；畦寬 {bed_w:.2f} m、畦間溝寬 {FURROW} m（推定）。",
                       "參考圖的水流方向（上緣分流 → 6 道畦溝 → 下緣集水 → 出水口）以溝的配置表現，"
                       "水面為靜水，未做流動動畫。",
                       "每條田畦中心有 SOCKET_bed_1…5（田畦頂），供種植或互動掛點使用。",
                       "參考圖的出水口是全開的，水會一直流掉；依使用者要求改為疊板閘：4 片橫木板（鐵包角串成一組）"
                       "平時升到頂卡滿擋水（堰頂 0.30），要放水時降下沉入溝底沉板槽（埋地石匣到 z = -0.15），"
                       "板頂 0.10–0.30 m 連續可調；牆頂橫梁上的手輪 weir_wheel 轉一圈升降 2.5 cm（推定）。"])
