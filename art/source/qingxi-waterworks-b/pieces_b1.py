"""批次 1：B01–B06 與 B02／B03 家族變體的形體定義。

每個函式接收 kit_lib.Builder，建立幾何、接口與水路；尺寸依
art/references/qingxi-waterworks-b/ 的三視圖，AI 圖無法量測或互相矛盾處
在 SPEC 的 notes 中寫明「推定設計」。
"""
import math

from kit_lib import (CLEAR_W, course_breaks, FLOOR_T, OUTER_W, TOTAL_H, WALL_T, WATER_Z, arc, channel, clamp_band,
                     cumlen, floor_run, join, line, offset_pts, sample, subpath, wall_run)

HALF_O = OUTER_W / 2
HALF_C = CLEAR_W / 2


def _stake_and_strap(b, s_pos, path, side, z_strap=0.25, stake_h=0.40, proud=0.0):
    """端柱外側的直立舊杉木樁，青銅帶繞過木樁兩側扣回石面（B02 右視圖）。proud：端柱外凸量。"""
    HALF_O = OUTER_W / 2 + proud
    p, d = sample(path, s_pos)
    sgn = 1 if side == "L" else -1
    nx, ny = -d[1] * sgn, d[0] * sgn
    rot = math.atan2(d[1], d[0])
    t_wood = 0.035
    off = HALF_O + t_wood / 2 + 0.001
    b.box("body", "ww_wood", (p[0] + nx * off, p[1] + ny * off, stake_h / 2 + 0.005), (0.055, t_wood, stake_h - 0.01),
          rot=rot, tint=(b.rng.uniform(0.92, 1.04),) * 3, bevel=0.005, jitter=0.0015)
    # 青銅帶：正面一片跨過木樁，兩側翼片貼回石面
    face = HALF_O + t_wood + 0.006
    b.box("body", "ww_bronze", (p[0] + nx * face, p[1] + ny * face, z_strap), (0.075, 0.009, 0.034), rot=rot,
          tint=(1, 1, 1), bevel=0.002, jitter=0)
    for k in (-1, 1):
        cx = p[0] + d[0] * k * 0.042 + nx * (HALF_O + 0.022)
        cy = p[1] + d[1] * k * 0.042 + ny * (HALF_O + 0.022)
        b.box("body", "ww_bronze", (cx, cy, z_strap), (0.009, 0.044, 0.034), rot=rot, tint=(1, 1, 1),
              bevel=0.002, jitter=0)
        b.box("body", "ww_bronze", (p[0] + d[0] * k * 0.052 + nx * (HALF_O + 0.004),
                                    p[1] + d[1] * k * 0.052 + ny * (HALF_O + 0.004), z_strap),
              (0.026, 0.008, 0.034), rot=rot, tint=(1, 1, 1), bevel=0.002, jitter=0)
        b.cylinder("body", "ww_bronze", (p[0] + d[0] * k * 0.054 + nx * (HALF_O + 0.01),
                                         p[1] + d[1] * k * 0.054 + ny * (HALF_O + 0.01), z_strap),
                   0.0075, 0.008, axis="X" if abs(nx) > 0.5 else "Y", segs=10)
    b.cylinder("body", "ww_bronze", (p[0] + nx * (face + 0.006), p[1] + ny * (face + 0.006), z_strap),
               0.0085, 0.008, axis="X" if abs(nx) > 0.5 else "Y", segs=10)


def _bookend_wall(b, path, side, end_len=0.10, proud=0.0, cap=0.0, wear=0.0, mid_courses=1,
                  mid_height=None, mid_drop=0.016, post_courses=1):
    """B02 式牆：兩端 10 cm 端柱維持標準 40 cm，中段長石略低（參考圖端柱突起的台階）。"""
    L = cumlen(path)[-1]
    if side == "L":
        a, c = HALF_C, HALF_O
        ap, cp = HALF_C, HALF_O + proud
    else:
        a, c = -HALF_O, -HALF_C
        ap, cp = -HALF_O - proud, -HALF_C
    for s0, s1 in ((0.0, end_len), (L - end_len, L)):
        st = subpath(path, s0, s1)
        zz = (0.0, TOTAL_H + cap) if post_courses == 1 else (0.0, 0.19, TOTAL_H + cap)
        for z0, z1 in zip(zz, zz[1:]):
            b.strip_prism("body", "ww_stone", offset_pts(st, ap), offset_pts(st, cp), z0, z1,
                          tint=b.stone_tint(0.97), bevel=0.016, wear=wear)
    zs = [0.0, TOTAL_H - mid_drop] if mid_courses == 1 else [0.0, 0.2, TOTAL_H - mid_drop]
    for k in range(len(zs) - 1):
        # v002：中段依層錯縫切成 24–40 cm 的石塊（第一輪 #51 的切石尺度），不再是一整條長石
        cuts = course_breaks(L - 2 * end_len, b.rng, 0.24, 0.40, offset=(b.rng.uniform(0.12, 0.2) if k % 2 else 0.0))
        for c0, c1 in zip(cuts, cuts[1:]):
            mid = subpath(path, end_len + c0, end_len + c1, step=0.05)
            top = zs[k + 1]
            if mid_height is not None and k == len(zs) - 2:
                ss = [end_len + c0 + (c1 - c0) * i / (len(mid) - 1) for i in range(len(mid))]
                top = [min(zs[k + 1], mid_height(s)) for s in ss]
            b.strip_prism("body", "ww_stone", offset_pts(mid, a), offset_pts(mid, c), zs[k], top,
                          tint=b.stone_tint(1.0), bevel=0.02, wear=wear)


# ------------------------------------------------------------------ B02 家族

def B02(b):
    """完整短直槽 100 × 60 × 40 cm（v002 參考：端石＋中段整石，端部木樁與銅帶）。"""
    b.props.update(moss=0.6)
    path = line((0, 0), (0, 1.0))
    b.port("in", (0, 0), (0, -1), "in")
    b.port("out", (0, 1.0), (0, 1), "out")
    floor_run(b, path, lo=0.46, hi=0.54)
    _bookend_wall(b, path, "L", proud=0.015, post_courses=2, mid_courses=2)
    _bookend_wall(b, path, "R", proud=0.015, post_courses=2, mid_courses=2)
    for s in (0.068, 0.932):
        _stake_and_strap(b, s, path, "L", proud=0.015)
        _stake_and_strap(b, s, path, "R", proud=0.015)
    b.flow("main", path, frm="in", to="out")
    return dict(name="完整短直槽", family="B02", variant="B02", length=1.0,
                ref="B02_three_view_dry_v002.png",
                notes=["端柱上下兩塊疊砌、向外凸 1.5 cm（參考圖正視）；接口內緣仍為標準 40 cm 淨寬。",
                       "接口面平齊；參考圖的 20 mm 墊片凹座未建成幾何，墊片可作獨立件。"])


def _std_ports(b, path, out_dir, out_kind="out"):
    p1, d1 = sample(path, cumlen(path)[-1])
    b.port("in", path[0], (0, -1), "in")
    b.port("out", p1, out_dir, out_kind)


def _extrude_xz(b, prof, y0, y1, part="body", mat="ww_stone"):
    """x-z 截面沿 y 擠出（內圓角、導角條）。"""
    import bmesh as _bm
    bm = _bm.new()
    a = [bm.verts.new((x, y0, z)) for x, z in prof]
    c = [bm.verts.new((x, y1, z)) for x, z in prof]
    bm.faces.new(a)
    bm.faces.new(c[::-1])
    n = len(prof)
    for i in range(n):
        bm.faces.new((a[i], c[i], c[(i + 1) % n], a[(i + 1) % n]))
    b._merge(part, mat, bm, b.stone_tint(0.97), bevel=0.0, jitter=0.0)


def _cove(b, radius, y0, y1):
    """槽底與牆的內圓角（四分之一圓填角條），左右各一。"""
    for sgn in (1, -1):
        prof = [(sgn * (HALF_C - radius + radius * math.cos(t)), FLOOR_T + radius - radius * math.sin(t))
                 for t in [i * math.pi / 2 / 7 for i in range(8)]]
        prof += [(sgn * HALF_C, FLOOR_T)]
        _extrude_xz(b, prof, y0, y1)


def B02_V02(b):
    """磨損階梯牆直槽：三層砌石；頂層只留兩端 12 cm 端石，接斜削過渡石降到中段 27 cm 的磨損凹口；
    中層外面在中段內退 2 cm 成小台階；右牆（+X）約 3/4 處一道裂縫以直立銅片補釘。"""
    b.props.update(moss=1.0)
    path = line((0, 0), (0, 1.0))
    _std_ports(b, path, (0, 1))
    floor_run(b, path, lo=0.28, hi=0.4, split_width=True)
    z = (0.0, 0.13, 0.27, TOTAL_H)
    for side, (a, c), sh in (("L", (HALF_C, HALF_O), 0.0), ("R", (-HALF_O, -HALF_C), 0.02)):
        out_sgn = 1 if side == "L" else -1          # 外側偏移方向（offset 正值 = -X）

        def seg(s0, s1, z0, z1, inset=0.0, tint=1.0, wear=0.1):
            st = subpath(path, s0, s1)
            oc = c - out_sgn * inset if side == "L" else c
            oa = a if side == "L" else a + inset
            b.strip_prism("body", "ww_stone", offset_pts(st, oa), offset_pts(st, oc), z0, z1,
                          tint=b.stone_tint(tint), wear=wear)
        for s0, s1 in zip(*(lambda cs: (cs, cs[1:]))(course_breaks(1.0, b.rng, 0.18, 0.3))):
            seg(s0, s1, z[0], z[1], tint=0.95)
        cuts = course_breaks(1.0, b.rng, 0.2, 0.32, offset=0.12)
        for s0, s1 in zip(cuts, cuts[1:]):
            mid = 0.25 + sh < (s0 + s1) / 2 < 0.75 - sh
            seg(s0, s1, z[1], z[2], inset=0.02 if mid else 0.0)
        e0, e1 = 0.12 + sh, 0.26 + sh
        seg(0.0, e0, z[2], z[3], tint=0.98)
        seg(1.0 - e0 - sh, 1.0, z[2], z[3], tint=0.98)
        seg(e0, e1, z[2], [z[3], z[2] + 0.05], tint=1.02, wear=0.0)
        seg(1.0 - e1 - sh, 1.0 - e0 - sh, z[2], [z[2] + 0.05, z[3]], tint=1.02, wear=0.0)
    # 右牆裂縫與直立銅片
    crack = [(0.80, 0.03), (0.83, 0.09), (0.81, 0.15), (0.845, 0.21), (0.825, 0.26)]
    for (y0, z0), (y1, z1) in zip(crack, crack[1:]):
        ln = math.hypot(y1 - y0, z1 - z0)
        b.obox("body", "ww_gasket", (HALF_O + 0.001, (y0 + y1) / 2, (z0 + z1) / 2), (0.006, 0.006, ln),
               (math.atan2(-(y1 - y0), z1 - z0), 0, 0), bevel=0.0, jitter=0)
    b.box("body", "ww_bronze", (HALF_O + 0.006, 0.825, 0.17), (0.012, 0.05, 0.26), tint=(1, 1, 1), bevel=0.002,
          jitter=0)
    for zz in (0.07, 0.17, 0.27):
        b.cylinder("body", "ww_bronze", (HALF_O + 0.013, 0.825, zz), 0.009, 0.008, axis="X", segs=10)
    b.flow("main", path, frm="in", to="out")
    return dict(name="磨損階梯牆直槽", family="B02", variant="B02-V02", length=1.0,
                ref="B02_V02_three_view_dry_v002.png",
                notes=["三層砌石 13／14／13 cm；中段牆頂 0.27 m，略低於運作水面 0.28 m，玩法中作為溢流／滲漏風險。",
                       "右牆 y ≈ 0.82 m 裂縫以直立銅片補釘（參考圖右視）。"])


def B02_V03(b):
    """半埋基腳直槽：U 形內圓角；中段 60 cm 外側三階退台（84／76／68 cm），兩端 20 cm 過渡回 60 cm；
    基腳另向下埋入地面 20 cm。"""
    b.props.update(moss=0.9)
    path = line((0, 0), (0, 1.0))
    _std_ports(b, path, (0, 1))
    floor_run(b, path, lo=0.3, hi=0.4)
    wall_run(b, path, HALF_C, HALF_O, courses=2, lo=0.24, hi=0.4)
    wall_run(b, path, -HALF_O, -HALF_C, courses=2, lo=0.24, hi=0.4)
    _cove(b, 0.06, 0.0, 1.0)
    # 埋地基腳：z -0.20..0，平面為中段 84 cm、兩端收到 60 cm 的六角形
    # 兩端內縮 3 cm，讓回填土包住基腳截面（單獨展示時不露出地下石面）
    foot = [(-HALF_O, 0.03), (-0.42, 0.2), (-0.42, 0.8), (-HALF_O, 0.97),
            (HALF_O, 0.97), (0.42, 0.8), (0.42, 0.2), (HALF_O, 0.03)]
    b.poly_prism_z("body", "ww_stone", foot, -0.20, [0.0] * len(foot), tint=b.stone_tint(0.88), bevel=0.012)
    # 外側退台：每階分 2–3 塊，側視呈三層階梯
    steps = ((0.00, 0.10, 0.42, 0.20, [0.2, 0.5, 0.8]),
             (0.10, 0.18, 0.38, 0.28, [0.28, 0.5, 0.72]),
             (0.18, 0.26, 0.34, 0.36, [0.36, 0.64]))
    for z0, z1, xo, y0, cuts in steps:
        for sgn in (1, -1):
            # 底階兩端的斜過渡段
            if z0 == 0.0:
                for ya, yb in ((0.0, 0.2), (1.0, 0.8)):
                    tri = [(sgn * (HALF_O - 0.001), ya), (sgn * (HALF_O - 0.001), yb), (sgn * xo, yb)]
                    b.poly_prism_z("body", "ww_stone", tri, z0, [z1] * 3, tint=b.stone_tint(0.94), bevel=0.01)
            for ya, yb in zip(cuts, cuts[1:]):
                cx = sgn * (HALF_O + xo) / 2
                b.box("body", "ww_stone", (cx, (ya + yb) / 2, (z0 + z1) / 2),
                      (xo - HALF_O + 0.002, yb - ya - 0.004, z1 - z0), tint=b.stone_tint(0.94), bevel=0.012)
    # 回填土：只蓋住地下基腳與底階根部
    soil, tops = [], []
    for side in (-1, 1):
        ys_s = [i / 14 for i in range(15)] if side > 0 else [1 - i / 14 for i in range(15)]
        for y in ys_s:
            w = 0.47 + 0.025 * math.sin(y * 9 + side) + 0.015 * math.sin(y * 23)
            soil.append((side * w, y))
            tops.append(0.005 + 0.03 * (0.5 + 0.5 * math.sin(y * 13 + side * 2)))
    b.poly_prism_z("soil", "ww_soil", soil, -0.21, tops, tint=(1, 1, 1), bevel=0.0, jitter=0.0)
    # 外緣土坡：再寬 6 cm、低 9 cm，讓土丘邊緣呈斜坡而非直壁
    skirt = [(x * 1.13, y) for x, y in soil]
    b.poly_prism_z("soil", "ww_soil", skirt, -0.21, [t - 0.09 for t in tops], tint=(0.9, 0.9, 0.9), bevel=0.0,
                   jitter=0.0)
    for s in (0.06, 0.32, 0.68, 0.94):
        clamp_band(b, (0, s), (0, 1), drop=0.12, width=0.045)
    b.flow("main", path, frm="in", to="out")
    return dict(name="半埋基腳直槽", family="B02", variant="B02-V03", length=1.0,
                ref="B02_V03_three_view_dry_v002.png",
                notes=["中段外側三階退台 84／76／68 cm，高 10／8／8 cm；兩端 20 cm 斜過渡回標準 60 cm。",
                       "基腳底在 z = -0.20（參考圖土深 20 cm）；擺放時需挖入地面，接口仍以 z = 0 為槽底。",
                       "回填土為獨立 soil 部件，可在場景中改用地形。"],
                collision="槽身同 B02；基腳在地下不需碰撞")


def B02_V04(b):
    """鍵槽短接頭（50 cm）：大圓角 U 槽；兩端 15 cm 端石（3 層）外貼木板與銅帶，
    中段 20 cm 鍵塊外面內退 1 cm、兩側青銅直條；底角小木楔。"""
    b.props.update(moss=0.7)
    L = 0.5
    k0, k1 = 0.15, 0.35                       # 鍵塊範圍
    path = line((0, 0), (0, L))
    _std_ports(b, path, (0, 1))
    floor_run(b, path, lo=0.5, hi=0.5)
    for side in ("L", "R"):
        sg = 1 if side == "L" else -1         # offset 正值 = -X
        a, c = (HALF_C, HALF_O) if side == "L" else (-HALF_O, -HALF_C)
        for s0, s1 in ((0.0, k0), (k1, L)):
            st = [((0, s0), (0, 1)), ((0, s1), (0, 1))]
            for z0, z1 in ((0.0, 0.12), (0.12, 0.28), (0.28, TOTAL_H)):
                b.strip_prism("body", "ww_stone", offset_pts(st, a), offset_pts(st, c), z0, z1,
                              tint=b.stone_tint(), bevel=0.016)
        st = [((0, k0), (0, 1)), ((0, k1), (0, 1))]
        ka, kc = (a, c - 0.01) if side == "L" else (a + 0.01, c)
        b.strip_prism("body", "ww_stone", offset_pts(st, ka), offset_pts(st, kc), 0.0, TOTAL_H - 0.01,
                      tint=b.stone_tint(1.04), bevel=0.016)
        xo = -sg * HALF_O                     # 外面 x
        out = -sg                             # 外法線 x 分量
        for y in (k0 + 0.008, k1 - 0.008):
            b.box("body", "ww_bronze", (xo + out * 0.0, y, 0.2), (0.012, 0.022, 0.37), tint=(1, 1, 1),
                  bevel=0.002, jitter=0)
            for z in (0.06, 0.2, 0.34):
                b.cylinder("body", "ww_bronze", (xo + out * 0.008, y, z), 0.007, 0.006, axis="X", segs=8)
        for y in (0.07, L - 0.07):
            b.box("body", "ww_wood", (xo + out * 0.016, y, 0.2), (0.03, 0.06, 0.37), tint=(1, 1, 1),
                  bevel=0.004, jitter=0.0008)
            for z in (0.1, 0.3):
                b.box("body", "ww_bronze", (xo + out * 0.034, y, z), (0.008, 0.075, 0.03), tint=(1, 1, 1),
                      bevel=0.002, jitter=0)
                b.cylinder("body", "ww_bronze", (xo + out * 0.04, y, z), 0.0075, 0.006, axis="X", segs=8)
            # 底角小木楔：斜 45° 塞在端石外側底緣
            b.obox("body", "ww_wood", (xo + out * 0.03, y + (0.045 if y < 0.25 else -0.045), 0.045),
                   (0.025, 0.035, 0.11), (0, out * math.radians(45), 0), tint=(0.9, 0.9, 0.9), bevel=0.004,
                   jitter=0.0)
    _cove(b, 0.1, 0.0, L)
    for s in (0.07, L - 0.07):
        clamp_band(b, (0, s), (0, 1), drop=0.10, width=0.05)
    b.flow("main", path, frm="in", to="out")
    return dict(name="鍵槽短接頭", family="B02", variant="B02-V04", length=L,
                ref="B02_V04_three_view_dry_v002.png",
                notes=["長度 0.50 m（推定設計：參考圖 40 cm，為對齊 0.25 m 拼接格調整；端石 15 cm、鍵塊 20 cm）。",
                       "用途：接舊渠斷口或補短缺口；鍵塊外面內退 1 cm、兩側青銅直條示意鍵槽。"])


def B02_V05(b):
    """終止放流坡：標準入口 20 cm 後，牆身降低、槽底外擴成 80 cm 寬放流石坡，前緣弧形收邊。"""
    b.props.update(moss=0.9)
    b.port("in", (0, 0), (0, -1), "in")
    b.port("discharge", (0, 0.8), (0, 1), "discharge")
    floor_run(b, line((0, 0), (0, 0.2)), lo=0.2, hi=0.2)
    for sg in (1, -1):
        a, c = (HALF_C, HALF_O) if sg > 0 else (-HALF_O, -HALF_C)
        st = [((0, 0.0), (0, 1)), ((0, 0.2), (0, 1))]
        b.strip_prism("body", "ww_stone", offset_pts(st, a), offset_pts(st, c), 0.0, TOTAL_H,
                      tint=b.stone_tint(0.96), bevel=0.016)
        # 入口柱：外側水平箍＋直條，鉚釘
        b.box("body", "ww_bronze", (sg * (HALF_O + 0.006), 0.1, 0.31), (0.012, 0.19, 0.04), tint=(1, 1, 1),
              bevel=0.002, jitter=0)
        b.box("body", "ww_bronze", (sg * (HALF_O + 0.006), 0.1, 0.18), (0.012, 0.035, 0.22), tint=(1, 1, 1),
              bevel=0.002, jitter=0)
        for z in (0.10, 0.22, 0.31):
            b.cylinder("body", "ww_bronze", (sg * (HALF_O + 0.013), 0.1, z), 0.009, 0.008, axis="X", segs=10)
    half = lambda y: HALF_C + 0.15 * (y - 0.2) / 0.6      # 前緣外寬 90 cm
    zt = lambda y: FLOOR_T - 0.05 * (y - 0.2) / 0.6
    # 鋪石：6 排 × 3 塊，逐排略降
    ys = [0.2 + 0.1 * i for i in range(7)]
    for y0, y1 in zip(ys, ys[1:]):
        for j in range(3):
            f0, f1 = -1 + 2 * j / 3, -1 + 2 * (j + 1) / 3
            poly = [(f0 * half(y0), y0), (f1 * half(y0), y0), (f1 * half(y1), y1), (f0 * half(y1), y1)]
            b.poly_prism_z("body", "ww_stone", poly, 0.0, [zt(y0)] * 2 + [zt(y1)] * 2,
                           tint=b.stone_tint(0.96), bevel=0.008)
    # 側牆：4 段退階，每段頂面微斜、段間落差 3 cm
    tops = ((0.20, 0.35, 0.33, 0.27), (0.35, 0.50, 0.24, 0.19), (0.50, 0.65, 0.16, 0.12), (0.65, 0.80, 0.10, 0.07))
    for y0, y1, h0, h1 in tops:
        for sg in (1, -1):
            poly = [(sg * half(y0), y0), (sg * (half(y0) + WALL_T), y0), (sg * (half(y1) + WALL_T), y1),
                    (sg * half(y1), y1)]
            if sg < 0:
                poly = poly[::-1]
            b.poly_prism_z("body", "ww_stone", poly, 0.0, [h0, h0, h1, h1] if sg > 0 else [h1, h1, h0, h0],
                           tint=b.stone_tint(0.98), bevel=0.012)
    edge = arc((0, -0.1), 0.9, math.radians(62), math.radians(118), step=0.07)
    for i in range(len(edge) - 1):
        (x0, y0), (x1, y1) = edge[i], edge[i + 1]
        poly = [(x0, y0 - 0.04), (x1, y1 - 0.04), (x1, y1 + 0.04), (x0, y0 + 0.04)]
        b.poly_prism("body", "ww_stone", poly, 0.0, 0.06, tint=b.stone_tint(0.94), bevel=0.008)
    b.flow("main", line((0, 0), (0, 0.8)), z0=WATER_Z, z1=0.09, frm="in", to="discharge")
    return dict(name="終止放流坡", family="B02", variant="B02-V05", length=0.8,
                ref="B02_V05_three_view_dry_v002.png",
                notes=["終止件：只有入口；水由前緣弧形放流口散出到溪道或田埂水溝。"])


# ------------------------------------------------------------------ B03 家族

def _bronze_ear(b, p, n, z=0.26):
    """青銅箍上的環耳（參考圖 B03 細節 2），在水道外側。"""
    rot = math.atan2(n[1], n[0])
    b.box("body", "ww_bronze", (p[0] + n[0] * 0.006, p[1] + n[1] * 0.006, z), (0.012, 0.05, 0.05),
          rot=rot, tint=(1, 1, 1), bevel=0.002, jitter=0)
    axis = "Y" if abs(n[0]) > 0.5 else "X"
    b.ring("body", "ww_bronze", (p[0] + n[0] * 0.016, p[1] + n[1] * 0.016, z - 0.032), 0.016, 0.024, 0.008,
           axis=axis, segs=16)


def B03(b):
    """直角彎槽（右轉）：入口在前、出口在右；外側方角兩層砌石，內側一塊小圓角整石轉角，底面連續。

    出口中心 (0.75, 0.75)：外框 105 × 105 cm，對應參考圖 100 × 100 cm 並落在 25 cm 拼接格。
    """
    b.props.update(moss=0.8)
    R = 0.75
    yo = R + HALF_C                              # 出口臂外側內緣 y = 0.95
    yi = R - HALF_C                              # 出口臂內側內緣 y = 0.55
    b.port("in", (0, 0), (0, -1), "in")
    b.port("out", (R, R), (1, 0), "out")
    # 底板：入口段、轉角段、出口段兩塊
    for x0, x1, y0, y1 in ((-HALF_C, HALF_C, 0.0, 0.45), (-HALF_C, HALF_C, 0.45, yo),
                           (HALF_C, 0.475, yi, yo), (0.475, R, yi, yo)):
        b.box("body", "ww_stone", ((x0 + x1) / 2, (y0 + y1) / 2, FLOOR_T / 2), (x1 - x0, y1 - y0, FLOOR_T),
              tint=b.stone_tint(0.97), bevel=0.006)
    # 外側方角：左牆＋後牆
    wall_run(b, line((-0.25, 0.0), (-0.25, yo)), 0.05, -0.05, courses=2, lo=0.3, hi=0.45)
    wall_run(b, line((-HALF_O, yo + 0.05), (R, yo + 0.05)), 0.05, -0.05, courses=2, lo=0.3, hi=0.45)
    # 內側：入口臂內牆、整石轉角（水側小圓角 r 8 cm）、出口臂內牆
    for z0, z1 in ((0.0, 0.2), (0.2, TOTAL_H)):
        b.box("body", "ww_stone", (0.25, 0.175, (z0 + z1) / 2), (0.1, 0.35, z1 - z0), tint=b.stone_tint(),
              bevel=0.016)
        b.box("body", "ww_stone", (0.6125, yi - 0.05, (z0 + z1) / 2), (0.275, 0.1, z1 - z0),
              tint=b.stone_tint(), bevel=0.016)
    rc = (HALF_C + 0.08, yi - 0.08)
    corner = [(0.3, 0.35), (HALF_C, 0.35)] + arc(rc, 0.08, math.pi, math.pi / 2, step=0.02) +              [(0.475, yi), (0.475, yi - 0.1), (0.3, yi - 0.1)]
    b.poly_prism("body", "ww_stone", corner, 0.0, TOTAL_H, tint=b.stone_tint(1.03), bevel=0.016)
    clamp_band(b, (0, 0.08), (0, 1), drop=0.3)
    clamp_band(b, (R - 0.08, R), (1, 0), drop=0.3)
    for p, n in (((-HALF_O, 0.16), (-1, 0)), ((HALF_O, 0.16), (1, 0)),
                 ((R - 0.16, yo + 0.1), (0, 1)), ((R - 0.16, yi - 0.1), (0, -1))):
        _bronze_ear(b, p, n)
    b.flow("main", join(line((0, 0), (0, R)), line((0, R), (R, R))), frm="in", to="out")
    return dict(name="直角彎槽（右）", family="B03", variant="B03", turn="right", radius=R,
                ref="B03_three_view_dry_v002.png",
                notes=["出口在 (0.75, 0.75)：外框 105 × 105 cm（參考圖 100 × 100 cm，為 25 cm 拼接格取 0.75）。",
                       "內側轉角為一塊整石，水側圓角 r = 8 cm；底面連續無階。"])


def B03_V02(b):
    """右轉寬弧彎：中心半徑 1.0 m，內外牆皆為弧形石塊，外側木樁＋青銅帶沿弧箍緊。"""
    b.props.update(moss=0.7)
    b.port("in", (0, 0), (0, -1), "in")
    b.port("out", (1.0, 1.0), (1, 0), "out")
    center = (1.0, 0.0)
    path = arc(center, 1.0, math.pi, math.pi / 2, step=0.03)
    floor_run(b, path, lo=0.3, hi=0.45)
    wall_run(b, path, HALF_C, HALF_O, courses=2, lo=0.24, hi=0.36)
    wall_run(b, path, -HALF_O, -HALF_C, courses=2, lo=0.22, hi=0.34)
    L = cumlen(path)[-1]
    st = subpath(path, 0.06, L - 0.06, step=0.05)
    b.strip_prism("body", "ww_bronze", offset_pts(st, HALF_O + 0.001), offset_pts(st, HALF_O + 0.012),
                  0.22, 0.255, tint=(1, 1, 1), bevel=0.002, jitter=0)
    for s in (0.12, L / 2, L - 0.12):
        p, d = sample(path, s)
        n = (-d[1], d[0])
        rot = math.atan2(d[1], d[0])
        b.box("body", "ww_wood", (p[0] + n[0] * (HALF_O + 0.032), p[1] + n[1] * (HALF_O + 0.032), 0.2),
              (0.06, 0.04, 0.4), rot=rot, tint=(1, 1, 1), bevel=0.005, jitter=0.001)
    b.flow("main", path, frm="in", to="out")
    return dict(name="寬弧彎槽（右）", family="B03", variant="B03-V02", turn="right", radius=1.0,
                ref="B03_V02_three_view_dry_v002.png",
                notes=["中心半徑 1.0 m：內牆面 0.8、外牆面 1.2（參考圖內 60／外 120 cm，配合拼接格放大 20 cm）。"])


def B03_V03(b):
    """左轉斜角扶壁彎：入口在前、出口在左；外角切斜面並加實心斜扶壁，接口兩側夾木板。"""
    b.props.update(moss=0.9)
    b.port("in", (0, 0), (0, -1), "in")
    b.port("out", (-0.5, 0.5), (-1, 0), "out")
    center = (-0.5, 0.0)
    inner = arc(center, 0.3, math.pi / 2, 0.0)
    floor_poly = [(HALF_C, 0.0), (HALF_C, 0.42), (0.08, 0.7), (-0.5, 0.7)] + inner
    b.poly_prism("body", "ww_stone", floor_poly, 0.0, FLOOR_T, tint=b.stone_tint(0.97), bevel=0.006)
    wall_run(b, line((0.25, 0.0), (0.25, 0.4)), 0.05, -0.05, courses=2, lo=0.18, hi=0.26)
    wall_run(b, line((0.25, 0.4), (0.04, 0.75), step=0.5), 0.05, -0.05, courses=2, lo=0.2, hi=0.3)
    wall_run(b, line((0.04, 0.75), (-0.5, 0.75)), 0.05, -0.05, courses=2, lo=0.2, hi=0.3)
    st = subpath(arc(center, 0.25, 0.0, math.pi / 2), 0, 0.25 * math.pi / 2)
    b.strip_prism("body", "ww_stone", offset_pts(st, -0.05), offset_pts(st, 0.05), 0.0, TOTAL_H,
                  tint=b.stone_tint(), bevel=0.016)
    dx, dy = 0.04 - 0.25, 0.75 - 0.4
    ln = math.hypot(dx, dy)
    ux, uy = dy / ln, -dx / ln     # 斜牆外法線（指向外側）
    a0 = (0.25 + ux * 0.05, 0.4 + uy * 0.05)
    a1 = (0.04 + ux * 0.05, 0.75 + uy * 0.05)
    poly = [a0, (a0[0] + ux * 0.26, a0[1] + uy * 0.26), (a1[0] + ux * 0.26, a1[1] + uy * 0.26), a1]
    b.poly_prism_z("body", "ww_stone", poly, 0.0, [0.36, 0.06, 0.06, 0.36], tint=b.stone_tint(0.94), bevel=0.014)
    # 對角扶壁肋：從斜牆中點向外角伸出，頂面由 0.40 斜降到 0.06
    mx, my = (a0[0] + a1[0]) / 2, (a0[1] + a1[1]) / 2
    tx, ty = -uy, ux
    rib = [(mx - tx * 0.06, my - ty * 0.06), (mx - tx * 0.06 + ux * 0.36, my - ty * 0.06 + uy * 0.36),
           (mx + tx * 0.06 + ux * 0.36, my + ty * 0.06 + uy * 0.36), (mx + tx * 0.06, my + ty * 0.06)]
    b.poly_prism_z("body", "ww_stone", rib, 0.0, [0.40, 0.06, 0.06, 0.40], tint=b.stone_tint(0.9), bevel=0.014)
    for x in (HALF_O + 0.018, -HALF_O - 0.018):
        b.box("body", "ww_wood", (x, 0.1, 0.2), (0.035, 0.16, 0.4), tint=(1, 1, 1), bevel=0.005, jitter=0.001)
        for z in (0.07, 0.31):
            b.box("body", "ww_bronze", (x + math.copysign(0.004, x), 0.1, z), (0.04, 0.17, 0.035), tint=(1, 1, 1),
                  bevel=0.002, jitter=0)
            b.cylinder("body", "ww_bronze", (x + math.copysign(0.025, x), 0.1, z), 0.008, 0.008, axis="X", segs=10)
    for y in (0.5 + HALF_O + 0.018, 0.5 - HALF_O - 0.018):
        b.box("body", "ww_wood", (-0.4, y, 0.2), (0.16, 0.035, 0.4), tint=(1, 1, 1), bevel=0.005, jitter=0.001)
        for z in (0.07, 0.31):
            b.box("body", "ww_bronze", (-0.4, y + math.copysign(0.004, y - 0.5), z), (0.17, 0.04, 0.035),
                  tint=(1, 1, 1), bevel=0.002, jitter=0)
            b.cylinder("body", "ww_bronze", (-0.4, y + math.copysign(0.025, y - 0.5), z), 0.008, 0.008, axis="Y",
                       segs=10)
    clamp_band(b, (0, 0.1), (0, 1), drop=0.2)
    clamp_band(b, (-0.4, 0.5), (-1, 0), drop=0.2)
    b.flow("main", arc(center, 0.5, 0.0, math.pi / 2), frm="in", to="out")
    return dict(name="斜角扶壁彎槽（左）", family="B03", variant="B03-V03", turn="left", radius=0.5,
                ref="B03_V03_three_view_dry_v002.png",
                notes=["中心半徑 0.5 m；外角改斜牆並加扶壁，與 B03 方角外緣不同。"])


def B03_V04(b):
    """左轉掃弧階台彎：中心半徑 0.75 m，外弧牆外有 12 cm 階台與斜撐，底部一圈基座石。"""
    b.props.update(moss=0.8)
    b.port("in", (0, 0), (0, -1), "in")
    b.port("out", (-0.75, 0.75), (-1, 0), "out")
    center = (-0.75, 0.0)
    path = arc(center, 0.75, 0.0, math.pi / 2, step=0.03)
    floor_run(b, path, lo=0.3, hi=0.42)
    wall_run(b, path, -HALF_O, -HALF_C, courses=2, lo=0.22, hi=0.34)
    wall_run(b, path, HALF_C, HALF_O, courses=2, lo=0.2, hi=0.3)
    L = cumlen(path)[-1]
    st = subpath(path, 0.12, L - 0.12, step=0.05)
    b.strip_prism("body", "ww_stone", offset_pts(st, -HALF_O - 0.12), offset_pts(st, -HALF_O + 0.001),
                  0.25, 0.30, tint=b.stone_tint(0.95), bevel=0.01)
    st2 = subpath(path, 0.0, L, step=0.05)
    b.strip_prism("body", "ww_stone", offset_pts(st2, -HALF_O - 0.07), offset_pts(st2, -HALF_O + 0.001),
                  0.0, 0.07, tint=b.stone_tint(0.9), bevel=0.01)
    for s in [0.22 + (L - 0.44) * k / 3 for k in range(4)]:
        p, d = sample(path, s)
        n = (d[1], -d[0])
        a = (p[0] + n[0] * HALF_O, p[1] + n[1] * HALF_O)
        c = (p[0] + n[0] * (HALF_O + 0.1), p[1] + n[1] * (HALF_O + 0.1))
        poly = [(a[0] - d[0] * 0.025, a[1] - d[1] * 0.025), (c[0] - d[0] * 0.025, c[1] - d[1] * 0.025),
                (c[0] + d[0] * 0.025, c[1] + d[1] * 0.025), (a[0] + d[0] * 0.025, a[1] + d[1] * 0.025)]
        b.poly_prism_z("body", "ww_stone", poly, 0.07, [0.25, 0.25, 0.25, 0.25], tint=b.stone_tint(0.92),
                       bevel=0.006)
    for s in (0.06, L - 0.06):
        p, d = sample(path, s)
        clamp_band(b, p, d, drop=0.2)
    b.flow("main", path, frm="in", to="out")
    return dict(name="掃弧階台彎槽（左）", family="B03", variant="B03-V04", turn="left", radius=0.75,
                ref="B03_V04_three_view_dry_v002.png",
                notes=["中心半徑 0.75 m（內牆面 0.55、外牆面 0.95），外加 12 cm 階台；與 B03-V03 弧度不同。"])


# ------------------------------------------------------------------ B04

def B04(b):
    """分流三通：前方 45 cm 入口短槽接橫槽，左右出口，後牆封閉；後牆腳一座低矮三角分水尖。"""
    b.props.update(moss=0.8)
    yc = 0.75                                   # 橫槽中心線（出口接口）
    b.port("in", (0, 0), (0, -1), "in")
    b.port("out_left", (-0.5, yc), (-1, 0), "out")
    b.port("out_right", (0.5, yc), (1, 0), "out")
    y_in, y_bk = yc - HALF_C, yc + HALF_C       # 橫槽內淨 0.55..0.95
    floor_poly = [(-HALF_C, 0.0), (HALF_C, 0.0), (HALF_C, y_in), (0.5, y_in), (0.5, y_bk), (-0.5, y_bk),
                  (-0.5, y_in), (-HALF_C, y_in)]
    b.poly_prism("body", "ww_stone", floor_poly, 0.0, FLOOR_T, tint=b.stone_tint(0.97), bevel=0.006)
    wall_run(b, line((-0.5, y_bk + 0.05), (0.5, y_bk + 0.05)), 0.05, -0.05, courses=3, lo=0.22, hi=0.34)
    for sg in (1, -1):
        # 入口短槽側牆與橫槽前牆分兩塊，接縫在 x = ±0.30
        b.box("body", "ww_stone", (sg * 0.25, (y_in - 0.1) / 2, TOTAL_H / 2), (0.1, y_in - 0.1, TOTAL_H),
              tint=b.stone_tint(), bevel=0.016)
        b.box("body", "ww_stone", (sg * 0.25, y_in - 0.05, TOTAL_H / 2), (0.1, 0.1, TOTAL_H),
              tint=b.stone_tint(0.94), bevel=0.016)
        b.box("body", "ww_stone", (sg * 0.4, y_in - 0.05, TOTAL_H / 2), (0.2, 0.1, TOTAL_H),
              tint=b.stone_tint(), bevel=0.016)
    # 分水尖：貼後牆、低於水面的三角錐
    b.poly_prism_z("body", "ww_stone", [(-0.11, y_bk + 0.001), (0.11, y_bk + 0.001), (0.0, y_bk - 0.15)],
                   FLOOR_T - 0.001, [0.24, 0.24, 0.12], tint=b.stone_tint(1.04), bevel=0.008)
    # 木樁＋青銅箍：橫槽前牆兩根、後牆兩根、入口短槽兩根
    for sg in (1, -1):
        for y, face in ((y_in - 0.1, -1), (y_bk + 0.1, 1)):
            x = sg * 0.33
            b.box("body", "ww_wood", (x, y + face * 0.022, 0.2), (0.06, 0.04, 0.4), tint=(1, 1, 1),
                  bevel=0.005, jitter=0.001)
            for z in (0.12, 0.30):
                b.box("body", "ww_bronze", (x, y + face * 0.046, z), (0.075, 0.01, 0.03), tint=(1, 1, 1),
                      bevel=0.002, jitter=0)
                b.cylinder("body", "ww_bronze", (x, y + face * 0.053, z), 0.008, 0.008, axis="Y", segs=10)
        b.box("body", "ww_bronze", (sg * 0.4, y_in - 0.1 - 0.006, 0.24), (0.2, 0.012, 0.03), tint=(1, 1, 1),
              bevel=0.002, jitter=0)
        b.box("body", "ww_wood", (sg * (HALF_O + 0.022), 0.12, 0.2), (0.04, 0.06, 0.4), tint=(1, 1, 1),
              bevel=0.005, jitter=0.001)
        b.box("body", "ww_bronze", (sg * (HALF_O + 0.046), 0.12, 0.26), (0.01, 0.075, 0.03), tint=(1, 1, 1),
              bevel=0.002, jitter=0)
        clamp_band(b, (sg * 0.42, yc), (1, 0), drop=0.25)
    b.box("body", "ww_bronze", (0, y_bk + 0.1 + 0.006, 0.24), (0.96, 0.012, 0.03), tint=(1, 1, 1), bevel=0.002,
          jitter=0)
    b.flow("to_left", join(line((0, 0), (0, yc)), line((0, yc), (-0.5, yc))), frm="in", to="out_left")
    b.flow("to_right", join(line((0, 0), (0, yc)), line((0, yc), (0.5, yc))), frm="in", to="out_right")
    return dict(name="分流三通", family="B04", variant="B04", ref="B04_three_view_dry_v002.png",
                notes=["外框 100 × 105 cm；參考圖 120 × 100 cm。出口收在 x = ±0.5、y = 0.75 以對齊 25 cm 拼接格（推定設計）。",
                       "分水尖為貼後牆的低矮三角錐（頂 24 cm、尖端 12 cm），不擋視線。",
                       "左出口預設接村田、右出口接支流；分流比例由玩法規則決定。"])


# ------------------------------------------------------------------ B05 / B06

GATE_Y = 0.5
POST_IN, POST_OUT = 0.22, 0.37
AXLE_Z = 0.90


def B05(b):
    """木製手動閘板（側邊操作）：1 m 直槽中段，兩側階梯石墩上立 12 cm 方木柱，閘板 44×40×5 cm 嵌在柱槽內。

    右柱內側有隨閘板升降的青銅齒條；右柱外側為 B06 閘輪座。
    狀態：closed（閘板底 = 槽底 0.10 m）／open（上提 0.32 m）。閘板與齒條為獨立部件 gate。
    """
    b.props.update(moss=0.8)
    path = line((0, 0), (0, 1.0))
    _std_ports(b, path, (0, 1))
    floor_run(b, path, lo=0.3, hi=0.4)
    for side in ("L", "R"):
        a_, c_ = (HALF_C, HALF_O) if side == "L" else (-HALF_O, -HALF_C)
        for s0, s1, h in ((0.0, 0.36, TOTAL_H), (0.36, 0.64, TOTAL_H + 0.04), (0.64, 1.0, TOTAL_H)):
            st = [((0, s0), (0, 1)), ((0, s1), (0, 1))]
            b.strip_prism("body", "ww_stone", offset_pts(st, a_), offset_pts(st, c_), 0.0, h,
                          tint=b.stone_tint(), bevel=0.016)
    for sg in (1, -1):
        b.box("body", "ww_stone", (sg * 0.42, GATE_Y, 0.16), (0.24, 0.38, 0.32), tint=b.stone_tint(0.95), bevel=0.02)
        b.box("body", "ww_stone", (sg * 0.3, GATE_Y, 0.38), (0.2, 0.26, 0.12), tint=b.stone_tint(0.98), bevel=0.016)
        cx = sg * (POST_IN + POST_OUT) / 2
        b.box("body", "ww_wood", (cx, GATE_Y, 0.44 + 0.53), (0.15, 0.15, 1.06), tint=(1, 1, 1), bevel=0.008,
              jitter=0.001)
        b.box("body", "ww_wood", (cx, GATE_Y, 1.515), (0.18, 0.18, 0.03), tint=(0.9, 0.9, 0.9), bevel=0.006,
              jitter=0.0)
        b.box("body", "ww_wood", (cx, GATE_Y, 1.545), (0.14, 0.14, 0.03), tint=(0.9, 0.9, 0.9), bevel=0.006,
              jitter=0.0)
        b.box("body", "ww_bronze", (cx, GATE_Y, 0.49), (0.16, 0.16, 0.08), tint=(1, 1, 1), bevel=0.004, jitter=0)
        for z in (0.80, 1.30):
            b.box("body", "ww_bronze", (cx, GATE_Y, z), (0.158, 0.158, 0.03), tint=(1, 1, 1), bevel=0.003, jitter=0)
        for fy in (-1, 1):
            b.box("body", "ww_bronze", (cx, GATE_Y + fy * 0.079, 0.66), (0.035, 0.008, 0.26), tint=(1, 1, 1),
                  bevel=0.002, jitter=0)
            for z in (0.56, 0.66, 0.76):
                b.cylinder("body", "ww_bronze", (cx, GATE_Y + fy * 0.084, z), 0.007, 0.006, axis="Y", segs=8)
        for dy in (-0.04, 0.04):
            b.box("body", "ww_wood", (sg * 0.195, GATE_Y + dy, 0.26), (0.01, 0.025, 0.32), tint=(0.85, 0.85, 0.85),
                  bevel=0.002, jitter=0)
    b.box("body", "ww_bronze", (POST_OUT + 0.006, GATE_Y, AXLE_Z), (0.012, 0.1, 0.12), tint=(1, 1, 1), bevel=0.003,
          jitter=0)
    for dz in (-0.045, 0.045):
        b.cylinder("body", "ww_bronze", (POST_OUT + 0.014, GATE_Y, AXLE_Z + dz), 0.008, 0.008, axis="X", segs=8)
    b.cylinder("body", "ww_bronze", (POST_OUT + 0.016, GATE_Y, AXLE_Z), 0.028, 0.012, axis="X", segs=16)
    b.socket("wheel_mount", (POST_OUT + 0.022, GATE_Y, AXLE_Z))
    for k in range(3):
        z0 = FLOOR_T + 0.4 * k / 3
        b.box("gate", "ww_wood", (0, GATE_Y, z0 + 0.4 / 6), (0.44, 0.05, 0.4 / 3 - 0.004),
              tint=(b.rng.uniform(0.92, 1.05),) * 3, bevel=0.004, jitter=0.0008)
    # 閘板青銅：只在兩側邊緣各一道直條＋上下角片（參考圖面板細節），木板面保持外露
    for fy in (-1, 1):
        y = GATE_Y + fy * 0.028
        for x in (-0.19, 0.19):
            b.box("gate", "ww_bronze", (x, y, FLOOR_T + 0.2), (0.03, 0.006, 0.38), tint=(1, 1, 1), bevel=0.0015,
                  jitter=0)
            for z in (0.15, 0.25, 0.35, 0.45):
                b.cylinder("gate", "ww_bronze", (x, y + fy * 0.004, z), 0.006, 0.005, axis="Y", segs=8)
            for z in (FLOOR_T + 0.03, FLOOR_T + 0.37):
                b.box("gate", "ww_bronze", (x * 0.86, y, z), (0.06, 0.005, 0.035), tint=(1, 1, 1), bevel=0.0015,
                      jitter=0)
    rack_x, rack_y = 0.205, GATE_Y - 0.045
    b.box("gate", "ww_bronze", (rack_x, rack_y, FLOOR_T + 0.52), (0.022, 0.02, 1.0), tint=(1, 1, 1),
          bevel=0.002, jitter=0)
    b.box("gate", "ww_bronze", (rack_x, GATE_Y - 0.03, FLOOR_T + 0.2), (0.022, 0.012, 0.06), tint=(1, 1, 1),
          bevel=0.0015, jitter=0)
    for k in range(26):
        b.box("gate", "ww_bronze", (rack_x, rack_y + 0.014, FLOOR_T + 0.08 + k * 0.036), (0.02, 0.01, 0.014),
              tint=(1, 1, 1), bevel=0.0, jitter=0)
    b.flow("upstream", line((0, 0), (0, GATE_Y - 0.03)), frm="in", to="gate")
    b.flow("downstream", line((0, GATE_Y + 0.03), (0, 1.0)), frm="gate", to="out")
    return dict(name="木製手動閘板", family="B05", variant="B05", length=1.0,
                ref="B05_three_view_dry_v003_side_operation.png",
                states=dict(closed=dict(gate_offset_z=0.0), open=dict(gate_offset_z=0.32)),
                notes=["從入口看操作者站右岸（+X）；閘輪座在右柱外側 x = 0.392、z = 0.90（B06 對準點）。",
                       "齒條在右柱內側 x = 0.205；B06 小齒輪直徑 7 cm 由軸穿過右柱與之嚙合（推定設計，未做機構模擬）。",
                       "框架外寬 0.74 m、柱寬 15 cm、柱頂 1.56 m（參考圖 80／150 cm）。"],
                collision="槽身盒＋兩柱盒；閘板 closed 時擋水")


def B06(b):
    """青銅水位閘輪：Ø50 cm 四輻輪，輪面平行水道（YZ），軸沿 X；外側 18 cm 木握把，軸端 Ø7 cm 小齒輪。

    原點 = B05 右柱外側閘輪座中心；輪在 +X 18 cm，小齒輪在 -X 15 cm（穿過柱體）。整組為 wheel 部件，繞 X 軸轉。
    """
    import bmesh as _bm
    from mathutils import Matrix as _M
    b.props.update(moss=0.0)
    b.cylinder("body", "ww_bronze", (0.012, 0, 0), 0.045, 0.024, axis="X", segs=20)
    wx = 0.18
    b.ring("wheel", "ww_bronze", (wx, 0, 0), 0.205, 0.25, 0.035, axis="X", segs=40)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        r0, r1 = 0.035, 0.212
        cy, cz = math.cos(a) * (r0 + r1) / 2, math.sin(a) * (r0 + r1) / 2
        bm = _bm.new()
        _bm.ops.create_cube(bm, size=1.0)
        _bm.ops.transform(bm, matrix=_M.Translation((wx, cy, cz)) @ _M.Rotation(a, 4, "X")
                          @ _M.Diagonal((0.022, r1 - r0, 0.03, 1)), verts=bm.verts)
        b._merge("wheel", "ww_bronze", bm, (1, 1, 1), bevel=0.003, jitter=0.0)
    b.cylinder("wheel", "ww_bronze", (wx, 0, 0), 0.045, 0.05, axis="X", segs=20)
    b.cylinder("wheel", "ww_bronze", (wx + 0.03, 0, 0), 0.022, 0.02, axis="X", segs=16)
    b.cylinder("wheel", "ww_bronze", (wx + 0.03, 0.0, 0.18), 0.012, 0.04, axis="X", segs=10)
    b.cylinder("wheel", "ww_wood", (wx + 0.105, 0.0, 0.18), 0.02, 0.11, axis="X", segs=14)
    b.cylinder("wheel", "ww_bronze", (wx + 0.165, 0.0, 0.18), 0.024, 0.012, axis="X", segs=14)
    b.cylinder("wheel", "ww_bronze", (wx / 2 - 0.08, 0, 0), 0.014, 0.35, axis="X", segs=12)
    b.cylinder("wheel", "ww_bronze", (-0.15, 0, 0), 0.028, 0.03, axis="X", segs=16)
    for k in range(10):
        a = k * 2 * math.pi / 10
        b.box("wheel", "ww_bronze", (-0.15, math.cos(a) * 0.032, math.sin(a) * 0.032), (0.03, 0.012, 0.012),
              tint=(1, 1, 1), bevel=0.0, jitter=0)
    return dict(name="青銅水位閘輪", family="B06", variant="B06", ref="B06_three_view_dry_v003_side_operation.png",
                states=dict(rotate_axis="X", deg_per_open=round(360 * 0.32 / (math.pi * 0.07), 1)),
                notes=["掛在 B05 的 SOCKET_wheel_mount；轉 1 圈閘板升降約 22 cm（小齒輪 Ø7 cm）。",
                       "輪心高 0.90 m、輪緣 0.65–1.15 m，對 1.75 m 角色為腰到胸高。"],
                collision="輪盤圓柱 Ø0.5 × 0.05 m；不擋路")


# ------------------------------------------------------------------ B01

def B01(b):
    """舊水路方形基座（公共工程起點）：140 × 140 × 40 cm 石框，內淨 120 × 120，前後 U 形短接口。

    原點 = 前方出口接口（水流 +Y 離開）；後方接口為溪邊進水 intake。
    """
    b.props.update(moss=0.9)
    b.port("out", (0, 0), (0, 1), "out")
    b.port("intake", (0, -1.8), (0, -1), "intake")
    y_front, y_back = -0.2, -1.6
    # 底板 3 × 3 石板＋前後短接口底板
    for i in range(3):
        for j in range(3):
            x0 = -0.6 + 0.4 * i
            y0 = y_back + 0.1 + 0.4 * j
            b.box("body", "ww_stone", (x0 + 0.2, y0 + 0.2, FLOOR_T / 2), (0.4, 0.4, FLOOR_T),
                  tint=b.stone_tint(0.97), bevel=0.006)
    for y0, y1 in ((-0.2, 0.0), (-1.8, -1.6)):
        b.box("body", "ww_stone", (0, (y0 + y1) / 2, FLOOR_T / 2), (CLEAR_W, 0.2, FLOOR_T),
              tint=b.stone_tint(0.97), bevel=0.006)
        b.box("body", "ww_stone", (0, (y0 + y1) / 2 + (0.05 if y0 < -1 else -0.05), FLOOR_T / 2),
              (CLEAR_W, 0.1, FLOOR_T), tint=b.stone_tint(0.97), bevel=0.006) if False else None
    # 前後牆（中央留 40 cm 開口）、左右牆、四角石
    for yc in (y_front - 0.05, y_back + 0.05):
        wall_run(b, line((-0.6, yc), (-HALF_C, yc)), 0.05, -0.05, courses=2, lo=0.2, hi=0.4)
        wall_run(b, line((HALF_C, yc), (0.6, yc)), 0.05, -0.05, courses=2, lo=0.2, hi=0.4)
    for xc in (-0.65, 0.65):
        wall_run(b, line((xc, y_back + 0.1), (xc, y_front - 0.1)), 0.05, -0.05, courses=2, lo=0.24, hi=0.4)
    for xc in (-0.65, 0.65):
        for yc in (y_front - 0.05, y_back + 0.05):
            b.box("body", "ww_stone", (xc, yc, TOTAL_H / 2), (0.1, 0.1, TOTAL_H), tint=b.stone_tint(0.93),
                  bevel=0.014)
    # 短接口側牆
    for y0, y1 in ((-0.2, 0.0), (-1.8, -1.6)):
        for sg in (1, -1):
            b.box("body", "ww_stone", (sg * 0.25, (y0 + y1) / 2, TOTAL_H / 2), (0.1, 0.2, TOTAL_H),
                  tint=b.stone_tint(0.97), bevel=0.014)
    # 青銅：四角 L 形包角、開口兩側直條
    for xc in (-0.7, 0.7):
        for yc in (y_front, y_back):
            sx = 1 if xc > 0 else -1
            sy = 1 if yc > -1 else -1
            b.box("body", "ww_bronze", (xc + sx * 0.005, yc - sy * 0.06, 0.2), (0.01, 0.06, 0.36), tint=(1, 1, 1),
                  bevel=0.002, jitter=0)
            b.box("body", "ww_bronze", (xc - sx * 0.06, yc + sy * 0.005, 0.2), (0.06, 0.01, 0.36), tint=(1, 1, 1),
                  bevel=0.002, jitter=0)
    for yc in (y_front, y_back):
        sy = 1 if yc > -1 else -1
        for sg in (1, -1):
            b.box("body", "ww_bronze", (sg * 0.36, yc + sy * 0.005, 0.2), (0.04, 0.01, 0.38), tint=(1, 1, 1),
                  bevel=0.002, jitter=0)
            for z in (0.08, 0.32):
                b.cylinder("body", "ww_bronze", (sg * 0.36, yc + sy * 0.012, z), 0.009, 0.01, axis="Y", segs=10)
    for xc in (-0.7, 0.7):
        sx = 1 if xc > 0 else -1
        for yc in (-0.6, -1.2):
            b.box("body", "ww_bronze", (xc + sx * 0.005, yc, 0.2), (0.01, 0.045, 0.38), tint=(1, 1, 1),
                  bevel=0.002, jitter=0)
    # 外圍底座線腳（外凸 2 cm、高 4 cm），開口處斷開
    for y0, y1, xs in ((y_back - 0.02, y_back + 0.08, ((-0.72, -0.2), (0.2, 0.72))),
                       (y_front - 0.08, y_front + 0.02, ((-0.72, -0.3), (0.3, 0.72)))):
        for xa, xb in xs:
            b.box("body", "ww_stone", ((xa + xb) / 2, (y0 + y1) / 2, 0.02), (xb - xa, y1 - y0, 0.04),
                  tint=b.stone_tint(0.86), bevel=0.008)
    for sx in (-1, 1):
        b.box("body", "ww_stone", (sx * 0.67, (y_front + y_back) / 2, 0.02), (0.1, 1.24, 0.04),
              tint=b.stone_tint(0.86), bevel=0.008)
    # 加高石：四角與開口兩端各疊一塊
    caps = [(sx * 0.65, yc, 0.13) for sx in (-1, 1) for yc in (y_front - 0.05, y_back + 0.05)]
    caps += [(sx * 0.25, yc, 0.11) for sx in (-1, 1) for yc in (y_front - 0.05, y_back + 0.05)]
    for x, y, w in caps:
        b.box("body", "ww_stone", (x, y, TOTAL_H + 0.025), (w, w, 0.05), tint=b.stone_tint(0.95), bevel=0.012)
    # 轉角水平青銅箍（z = 0.30）
    for xc in (-0.7, 0.7):
        for yc in (y_front, y_back):
            sx = 1 if xc > 0 else -1
            sy = 1 if yc > -1 else -1
            b.box("body", "ww_bronze", (xc + sx * 0.006, yc - sy * 0.08, 0.30), (0.012, 0.16, 0.035),
                  tint=(1, 1, 1), bevel=0.002, jitter=0)
            b.box("body", "ww_bronze", (xc - sx * 0.08, yc + sy * 0.006, 0.30), (0.16, 0.012, 0.035),
                  tint=(1, 1, 1), bevel=0.002, jitter=0)
            b.cylinder("body", "ww_bronze", (xc + sx * 0.013, yc - sy * 0.12, 0.30), 0.01, 0.01, axis="X", segs=10)
            b.cylinder("body", "ww_bronze", (xc - sx * 0.12, yc + sy * 0.013, 0.30), 0.01, 0.01, axis="Y", segs=10)
    b.water_polys.append(dict(name="basin", poly=[(-0.595, -1.495), (0.595, -1.495), (0.595, -0.305),
                                                  (-0.595, -0.305)], z=WATER_Z))
    b.flow("outlet", line((0, -0.3), (0, 0.0)), frm="basin", to="out")
    b.flow("intake", line((0, -1.8), (0, -1.5)), frm="intake", to="basin")
    return dict(name="舊水路方形基座", family="B01", variant="B01", ref="B01_three_view_dry_v002.png",
                notes=["整體 140 × 180 cm（含前後各 20 cm 短接口）；內淨 120 × 120 cm、底高 10 cm。",
                       "公共工程起點：後方 intake 接溪邊取水口，前方出口接 B02–B05；不是私人靈田床。"])
