"""批次 2：B04-V02、B07–B12 與修補石／支架變體的形體定義。

非水槽件（B07–B12）原點為底面中心、正面朝 -Y；支架（B10 家族）原點在地面，
SOCKET_trough 是 1 m 直槽入口原點應放的位置（支架落在槽身中段）。
三視圖為 AI 概念圖，無法量測或互相矛盾處在 notes 寫明「推定設計」。
"""
import math

import bmesh
from mathutils import Vector, noise

from kit_lib import CLEAR_W, FLOOR_T, OUTER_W, TOTAL_H, clamp_band, join, line, wall_run

HALF_O = OUTER_W / 2
HALF_C = CLEAR_W / 2
WOOD = (1, 1, 1)


# ------------------------------------------------------------------ 共用小工具

def _wood_tint(b, lo=0.9, hi=1.05):
    return (b.rng.uniform(lo, hi),) * 3


def tube(b, part, mat, pts, r, segs=8, tint=WOOD, r_fn=None):
    """沿折線掃出的封閉圓管（繩、握把、弧形撐桿）。r_fn(i) 可逐點改半徑。"""
    pts = [Vector(p) for p in pts]
    n = len(pts)
    bm = bmesh.new()
    rings, prev = [], None
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        if prev is None:
            a = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
            nv = t.cross(a).normalized()
        else:
            nv = (prev - t * prev.dot(t)).normalized()
        prev = nv
        bv = t.cross(nv)
        rr = r_fn(i) if r_fn else r
        rings.append([bm.verts.new(p + (nv * math.cos(2 * math.pi * k / segs) +
                                        bv * math.sin(2 * math.pi * k / segs)) * rr) for k in range(segs)])
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(segs):
            bm.faces.new((r0[k], r0[(k + 1) % segs], r1[(k + 1) % segs], r1[k]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    b._merge(part, mat, bm, tint, bevel=0.0, jitter=0.0)


def prism_xz(b, part, mat, poly, y0, y1, tint=None, **kw):
    """x-z 平面多邊形沿 y 擠出（側面輪廓明確的石板、木楔、箭頭）。"""
    bm = bmesh.new()
    a = [bm.verts.new((x, y0, z)) for x, z in poly]
    c = [bm.verts.new((x, y1, z)) for x, z in poly]
    bm.faces.new(a)
    bm.faces.new(c[::-1])
    m = len(poly)
    for i in range(m):
        bm.faces.new((a[i], c[i], c[(i + 1) % m], a[(i + 1) % m]))
    b._merge(part, mat, bm, tint or (b.stone_tint() if mat.startswith("ww_stone") else WOOD), **kw)


def prism_yz(b, part, mat, poly, x0, x1, tint=None, **kw):
    """y-z 平面多邊形沿 x 擠出（側視輪廓的碑石）。"""
    bm = bmesh.new()
    a = [bm.verts.new((x0, y, z)) for y, z in poly]
    c = [bm.verts.new((x1, y, z)) for y, z in poly]
    bm.faces.new(a)
    bm.faces.new(c[::-1])
    m = len(poly)
    for i in range(m):
        bm.faces.new((a[i], c[i], c[(i + 1) % m], a[(i + 1) % m]))
    b._merge(part, mat, bm, tint or (b.stone_tint() if mat.startswith("ww_stone") else WOOD), **kw)


def revolve(b, part, mat, center, a0, a1, prof, step_deg=6.0, tint=None, **kw):
    """r-z 截面（封閉多邊形）繞 center 從角度 a0 轉到 a1（弧度）。圓腹石缽、弧形青銅帶。"""
    n = max(2, int(math.degrees(abs(a1 - a0)) / step_deg) + 1)
    bm = bmesh.new()
    rings = []
    for i in range(n):
        a = a0 + (a1 - a0) * i / (n - 1)
        ca, sa = math.cos(a), math.sin(a)
        rings.append([bm.verts.new((center[0] + r * ca, center[1] + r * sa, z)) for r, z in prof])
    m = len(prof)
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(m):
            bm.faces.new((r0[k], r0[(k + 1) % m], r1[(k + 1) % m], r1[k]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    b._merge(part, mat, bm, tint or (b.stone_tint() if mat.startswith("ww_stone") else WOOD), **kw)


def cone(b, part, mat, center, r_bot, r_top, depth, segs=4, rot_z=math.pi / 4, tint=WOOD):
    """尖樁頭、柱頂尖：create_cone，segs=4 即方錐。center 為中點。"""
    from mathutils import Matrix
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r_bot, radius2=r_top, depth=depth)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(center) @ Matrix.Rotation(rot_z, 4, "Z"), verts=bm.verts)
    b._merge(part, mat, bm, tint, bevel=0.0, jitter=0.0)


def rock(b, part, center, size, tint=None):
    """不規則碎石（手推車貨物）：細分 1 次的二十面體加低頻起伏，不走砌石圓角流程。"""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    seed = Vector((b.rng.uniform(0, 40), b.rng.uniform(0, 40), b.rng.uniform(0, 40)))
    for v in bm.verts:
        d = 1.0 + 0.22 * noise.noise(v.co * 1.6 + seed) + 0.08 * noise.noise(v.co * 4.0 + seed)
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2])) * d * 0.5
        # 底面壓平，石頭能平放在車床上
        v.co.z = max(v.co.z, -size[2] * 0.32)
        v.co += Vector(center)
    b._merge(part, "ww_stone", bm, tint or b.stone_tint(0.95), bevel=0.0, jitter=0.0)


def strap_box(b, part, center, size, rot=0.0):
    b.box(part, "ww_bronze", center, size, rot=rot, tint=WOOD, bevel=0.002, jitter=0)


def rivet(b, part, center, axis, r=0.007, depth=0.006):
    b.cylinder(part, "ww_bronze", center, r, depth, axis=axis, segs=8)


def beam_between(b, part, mat, p0, p1, w, h, tint=WOOD, bevel=0.005):
    """兩點間的方木（斜撐、握把）：截面 w（水平）× h，沿 p0→p1。"""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    L = d.length
    yaw = math.atan2(-d.x, d.y)
    pitch = math.atan2(d.z, math.hypot(d.x, d.y))
    from mathutils import Euler, Matrix
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    m = (Matrix.Translation((p0 + p1) / 2) @ Euler((0, 0, yaw)).to_matrix().to_4x4()
         @ Euler((pitch, 0, 0)).to_matrix().to_4x4() @ Matrix.Diagonal((w, L, h, 1)))
    bmesh.ops.transform(bm, matrix=m, verts=bm.verts)
    b._merge(part, mat, bm, tint, bevel=bevel, jitter=0.0)


# ------------------------------------------------------------------ B04-V02

def B04_V02(b):
    """圓缽分流三通：前方入口短槽、左右出口，中央圓腹石缽、後側封閉的弧牆。

    外框 150 × 115 cm（參考 140 × 110）；出口 x = ±0.75、y = 0.75 對齊 25 cm 拼接格（推定）。
    """
    b.props.update(moss=0.9)
    yc, R = 0.75, 0.30                                  # 缽心與缽內淨半徑
    b.port("in", (0, 0), (0, -1), "in")
    b.port("out_left", (-0.75, yc), (-1, 0), "out")
    b.port("out_right", (0.75, yc), (1, 0), "out")
    a_f = math.asin(HALF_C / R)                         # 入口側牆 x=±0.2 與內圓交點
    a_b = math.acos(math.sqrt(R * R - HALF_C * HALF_C) / R)

    def arcpts(a0, a1, n=6):
        return [(R * math.cos(a0 + (a1 - a0) * i / n), yc + R * math.sin(a0 + (a1 - a0) * i / n))
                for i in range(n + 1)]

    # 底板：入口短槽、兩出口臂、中央缽底（含前角圓弧）
    b.box("body", "ww_stone", (0, (yc - R * math.cos(a_f) + 0.0) / 2 - 0.0, FLOOR_T / 2),
          (CLEAR_W, yc - R * math.cos(a_f), FLOOR_T), tint=b.stone_tint(0.97), bevel=0.006)
    y_in = yc - R * math.cos(a_f)                       # 入口槽底與缽底分界（y ≈ 0.526）
    for sg in (1, -1):
        b.box("body", "ww_stone", (sg * 0.575, yc, FLOOR_T / 2), (0.35, CLEAR_W, FLOOR_T),
              tint=b.stone_tint(0.97), bevel=0.006)
    bowl = [(-HALF_C, y_in), (HALF_C, y_in)]
    bowl += arcpts(-math.pi / 2 + a_f, -a_b)[1:]
    bowl += [(0.4, yc - HALF_C), (0.4, yc + HALF_C)]
    bowl += arcpts(a_b, math.pi - a_b, 16)
    bowl += [(-0.4, yc + HALF_C), (-0.4, yc - HALF_C)]
    bowl += arcpts(math.pi + a_b, 1.5 * math.pi - a_f)[:-1]
    b.poly_prism("body", "ww_stone", bowl, 0.0, FLOOR_T, tint=b.stone_tint(0.95), bevel=0.006)

    # 入口側牆（兩層錯縫）
    for sg in (1, -1):
        wall_run(b, line((0, 0), (0, y_in - 0.08)), sg * HALF_C, sg * HALF_O, courses=2, lo=0.18, hi=0.3)
        # 前角塊：入口牆、出口前牆交會處，內側沿缽圓弧
        corner = [(sg * HALF_C, y_in - 0.08), (sg * 0.4, y_in - 0.08), (sg * 0.4, yc - HALF_C)]
        corner += [(sg * x, y) for x, y in arcpts(-a_b, -math.pi / 2 + a_f, 4)]
        corner = corner if sg > 0 else corner[::-1]
        b.poly_prism("body", "ww_stone", corner, 0.0, TOTAL_H, tint=b.stone_tint(0.94), bevel=0.016)
        # 出口臂前牆、後牆
        wall_run(b, line((sg * 0.4, yc - 0.25), (sg * 0.75, yc - 0.25)), 0.05, -0.05, courses=2,
                 lo=0.16, hi=0.22)
        wall_run(b, line((sg * 0.26, yc + 0.25), (sg * 0.75, yc + 0.25)), 0.05, -0.05, courses=2,
                 lo=0.18, hi=0.26)

    # 圓腹缽牆：內面垂直 r=0.30，外面中段鼓出、頂緣內收
    def r_out(z):
        return R + 0.10 + 0.065 * math.sin(math.pi * z / 0.44) - 0.075 * (z / TOTAL_H) ** 3

    for z0, z1 in ((0.0, 0.2), (0.2, TOTAL_H)):
        zs = [z0 + (z1 - z0) * k / 5 for k in range(6)]
        prof = [(R, z0)] + [(r_out(z), z) for z in zs] + [(R, z1)]
        cuts = [a_b, a_b + (math.pi - 2 * a_b) * 0.36, a_b + (math.pi - 2 * a_b) * 0.64, math.pi - a_b] \
            if z0 == 0 else [a_b, math.pi / 2 - 0.05, math.pi - a_b]
        for a0, a1 in zip(cuts, cuts[1:]):
            revolve(b, "body", "ww_stone", (0, yc), a0, a1, prof, step_deg=5, tint=b.stone_tint(), bevel=0.014)
    # 缽上的青銅帶：兩道縱帶跨過頂緣，一道水平腰帶
    for a in (math.radians(66), math.radians(114)):
        zs = [0.03 + (TOTAL_H - 0.03) * k / 8 for k in range(9)]
        prof = [(r_out(z) + 0.008, z) for z in zs] + [(r_out(TOTAL_H) + 0.008, TOTAL_H + 0.008),
                                                    (R - 0.004, TOTAL_H + 0.008), (R - 0.004, TOTAL_H - 0.03),
                                                    (R + 0.001, TOTAL_H - 0.03)]
        prof += [(r_out(z) - 0.002, z) for z in zs[::-1]]
        revolve(b, "body", "ww_bronze", (0, yc), a - 0.032, a + 0.032, prof, step_deg=2, tint=WOOD, bevel=0.0,
                jitter=0)
        for z in (0.12, 0.30):
            rr = r_out(z) + 0.012
            rivet(b, "body", (rr * math.cos(a), yc + rr * math.sin(a), z), "X", r=0.011, depth=0.01)
    zb = 0.16
    prof = [(r_out(zb - 0.02) - 0.002, zb - 0.02), (r_out(zb - 0.02) + 0.008, zb - 0.02),
            (r_out(zb + 0.02) + 0.008, zb + 0.02), (r_out(zb + 0.02) - 0.002, zb + 0.02)]
    revolve(b, "body", "ww_bronze", (0, yc), a_b + 0.12, math.pi - a_b - 0.12, prof, step_deg=4, tint=WOOD,
            bevel=0.0, jitter=0)
    for sg in (1, -1):
        clamp_band(b, (sg * 0.62, yc), (1, 0), drop=0.22)
    clamp_band(b, (0, 0.18), (0, 1), drop=0.22)
    b.flow("to_left", join(line((0, 0), (0, yc)), line((0, yc), (-0.75, yc))), frm="in", to="out_left")
    b.flow("to_right", join(line((0, 0), (0, yc)), line((0, yc), (0.75, yc))), frm="in", to="out_right")
    return dict(name="圓缽分流三通", family="B04", variant="B04-V02", ref="B04_V02_three_view_dry_v002.png",
                notes=["出口在 x = ±0.75（外寬 150 cm，參考 140 cm），為對齊 25 cm 拼接格的推定設計。",
                       "缽內淨半徑 30 cm、底板與三個接口同高；後側弧牆封閉。缽牆外側中段鼓出約 5 cm、頂緣內收成圓腹。",
                       "與 B04 的差別：中央圓缽取代直角橫槽與分水尖，水流在缽內轉向，三個接口仍為標準 U 形。"])


# ------------------------------------------------------------------ B07 修補石家族

def _saddle_top(x):
    """B07 頂緣鞍形下凹：中段 26 cm 平滑下凹 2.8 cm。"""
    t = min(1.0, abs(x) / 0.13)
    return 0.20 - 0.028 * (0.5 + 0.5 * math.cos(math.pi * t))


def B07(b):
    """修補石鞍 45 × 8 × 20 cm：石板背面嵌黏土纖維墊圈，兩道青銅扣帶跨頂緣、下端銅環＋木楔。"""
    b.props.update(moss=0.7)
    y_f, y_b = -0.04, 0.02                               # 石板前後面（背面接觸受損槽壁）
    poly = [(-0.213, 0.0), (0.213, 0.0), (0.225, 0.012), (0.225, 0.185), (0.205, 0.2)]
    poly += [(x, _saddle_top(x)) for x in [0.16 - 0.32 * i / 12 for i in range(13)]]
    poly += [(-0.205, 0.2), (-0.225, 0.185), (-0.225, 0.012)]
    prism_xz(b, "body", "ww_stone", poly, y_f, y_b, tint=b.stone_tint(0.98), bevel=0.012)
    # 正面下段凸起一層（參考圖下半截的台階線）
    prism_xz(b, "body", "ww_stone", [(-0.2, 0.018), (0.2, 0.018), (0.2, 0.108), (-0.2, 0.108)],
             y_f - 0.012, y_f + 0.008, tint=b.stone_tint(0.95), bevel=0.01)
    # 背面黏土墊圈（框形，內縮 2 cm）
    for cx, cz, sx, sz in ((0, 0.03, 0.39, 0.02), (0, 0.16, 0.39, 0.02), (-0.185, 0.095, 0.02, 0.15),
                           (0.185, 0.095, 0.02, 0.15)):
        b.box("body", "ww_seal", (cx, y_b + 0.005, cz), (sx, 0.012, sz), tint=WOOD, bevel=0.002, jitter=0.0005)
    for sg in (1, -1):
        x = sg * 0.135
        zt = _saddle_top(x)
        strap_box(b, "body", (x, (y_f + y_b) / 2 - 0.004, zt + 0.004), (0.045, y_b - y_f + 0.03, 0.008))
        strap_box(b, "body", (x, y_f - 0.016, (zt + 0.1) / 2), (0.045, 0.008, zt - 0.1))
        strap_box(b, "body", (x, y_b + 0.015, zt - 0.03), (0.045, 0.008, 0.06))
        b.ring("body", "ww_bronze", (x, y_f - 0.026, 0.085), 0.017, 0.026, 0.009, axis="Y", segs=16)
        b.box("body", "ww_wood", (x, y_f - 0.028, 0.045), (0.034, 0.018, 0.06), tint=_wood_tint(b), bevel=0.003,
              jitter=0)
        for z in (0.13, zt - 0.02):
            rivet(b, "body", (x, y_f - 0.022, z), "Y")
    b.socket("contact", (0, y_b + 0.011, 0.1))
    return dict(name="修補石鞍", family="B07", variant="B07", ref="B07_three_view_dry_v002.png",
                notes=["背面（+Y）為接觸面，SOCKET_contact 在墊圈面中心；放在破損槽壁外側，頂緣鞍形對準牆頂。",
                       "實際裂縫大小未知（參考圖 A FIT: VERIFY），玩法以「修補位置」吸附，不做幾何密合。"],
                collision="單一盒 45 × 9 × 20 cm")


def B07_V02(b):
    """轉角 L 形修補鍵：長臂 35、短臂 25、厚 8、高 20 cm；內側兩面黏土墊圈，青銅夾＋杉木楔。"""
    b.props.update(moss=0.8)
    xa, xb, ya, yb, t = -0.175, 0.175, -0.125, 0.125, 0.08
    L = [(xa, ya), (xb, ya), (xb, yb), (xb - t, yb), (xb - t, ya + t), (xa, ya + t)]
    b.poly_prism("body", "ww_stone", L, 0.0, 0.2, tint=b.stone_tint(0.98), bevel=0.014)
    # 內側墊圈（朝 +Y 的長臂內面、朝 -X 的短臂內面）
    b.box("body", "ww_seal", ((xa + xb - t) / 2 - 0.005, ya + t + 0.005, 0.1), (xb - t - xa - 0.03, 0.012, 0.16),
          tint=WOOD, bevel=0.002, jitter=0.0005)
    b.box("body", "ww_seal", (xb - t - 0.005, (ya + t + yb) / 2 + 0.004, 0.1), (0.012, yb - ya - t - 0.025, 0.16),
          tint=WOOD, bevel=0.002, jitter=0.0005)
    # 長臂正面：直條跨頂＋水平帶
    x = -0.12
    strap_box(b, "body", (x, ya - 0.005, 0.12), (0.035, 0.008, 0.16))
    strap_box(b, "body", (x, ya + t / 2, 0.204), (0.035, t + 0.02, 0.008))
    strap_box(b, "body", (-0.06, ya - 0.009, 0.115), (0.15, 0.008, 0.032))
    for xx in (-0.135, -0.105, 0.0):
        rivet(b, "body", (xx, ya - 0.014, 0.115), "Y")
    # 短臂外側：彎折青銅夾＋斜插杉木楔
    strap_box(b, "body", (xb + 0.005, -0.02, 0.1), (0.008, 0.11, 0.032))
    strap_box(b, "body", (xb - t / 2, -0.074, 0.1), (t + 0.01, 0.008, 0.032))
    rivet(b, "body", (xb + 0.01, 0.015, 0.1), "X")
    b.obox("body", "ww_wood", (xb + 0.022, -0.075, 0.095), (0.022, 0.04, 0.2), (0.0, math.radians(-14), 0.0),
           tint=_wood_tint(b), bevel=0.004, jitter=0.0)
    b.socket("contact", (xb - t - 0.011, ya + t + 0.011, 0.1))
    return dict(name="轉角L形修補鍵", family="B07", variant="B07-V02", ref="B07_V02_three_view_dry_v002.png",
                notes=["長臂朝 -Y、短臂朝 +X，貼補槽體外轉角；兩個內側面為墊圈接觸面。",
                       "實際缺角大小未知（A FIT: VERIFY），玩法以轉角位置吸附。"],
                collision="兩個盒（長臂、短臂）")


def B07_V03(b):
    """階梯底板修補塞：底 40 × 30 × 5 cm＋中間退台＋上台 25 × 20 × 3 cm；前後兩組燕尾木鍵＋青銅夾。"""
    b.props.update(moss=0.5)
    b.box("body", "ww_stone", (0, 0, 0.025), (0.40, 0.30, 0.05), tint=b.stone_tint(0.96), bevel=0.01)
    b.box("body", "ww_stone", (0, 0, 0.056), (0.33, 0.245, 0.014), tint=b.stone_tint(1.0), bevel=0.004)
    b.box("body", "ww_stone", (0, 0, 0.078), (0.25, 0.20, 0.03), tint=b.stone_tint(1.02), bevel=0.008)
    for fy in (-1, 1):
        y = fy * 0.15
        for sg in (1, -1):
            x = sg * 0.12
            key = [(x - 0.016, 0.004), (x + 0.016, 0.004), (x + 0.011, 0.044), (x - 0.011, 0.044)]
            prism_xz(b, "body", "ww_wood", key, y - fy * 0.012, y + fy * 0.003, tint=_wood_tint(b), bevel=0.0015,
                     jitter=0)
            for dx in (-1, 1):
                strap_box(b, "body", (x + dx * 0.026, y + fy * 0.002, 0.024), (0.012, 0.006, 0.034))
                rivet(b, "body", (x + dx * 0.026, y + fy * 0.006, 0.024), "Y", r=0.0045, depth=0.004)
    return dict(name="階梯底板修補塞", family="B07", variant="B07-V03", ref="B07_V03_three_view_dry_v002.png",
                notes=["裝在槽底破洞，上台頂面與槽底齊平（上台 3 cm 嵌入洞口）；實際洞口大小未知（A FIT: VERIFY）。",
                       "參考圖仰視的燕尾鍵槽只做到側面可見的木鍵與銅夾，底面未挖槽（推定簡化）。"],
                collision="底座盒 40 × 30 × 5 cm")


# ------------------------------------------------------------------ B08 清淤篩

def B08(b):
    """可操作河床清淤篩：杉木框 60 × 45 × 12 cm、10 mm 青銅網格，110 cm 長柄（斜靠地面）。"""
    b.props.update(moss=0.0)
    W, D, H, t = 0.60, 0.45, 0.12, 0.025
    for fy in (-1, 1):
        b.box("body", "ww_wood", (0, fy * (D / 2 - t / 2), H / 2), (W, t, H), tint=_wood_tint(b), bevel=0.004)
    for sg in (1, -1):
        b.box("body", "ww_wood", (sg * (W / 2 - t / 2), 0, H / 2), (t, D - 2 * t, H), tint=_wood_tint(b),
              bevel=0.004)
    for fy in (-0.1, 0.1):
        b.box("body", "ww_wood", (0, fy, 0.022), (W - 2 * t, 0.03, 0.02), tint=_wood_tint(b, 0.8, 0.9),
              bevel=0.002)
    pitch, wire = 0.0125, 0.0025
    nx = int((W - 2 * t) / pitch)
    ny = int((D - 2 * t) / pitch)
    for i in range(nx + 1):
        x = -(W / 2 - t) + i * (W - 2 * t) / nx
        b.box("body", "ww_bronze", (x, 0, 0.0335), (wire, D - 2 * t + 0.004, wire), tint=WOOD, bevel=0.0, jitter=0)
    for j in range(ny + 1):
        y = -(D / 2 - t) + j * (D - 2 * t) / ny
        b.box("body", "ww_bronze", (0, y, 0.0335 + wire), (W - 2 * t + 0.004, wire, wire), tint=WOOD, bevel=0.0,
              jitter=0)
    # 四角青銅包角
    for sg in (1, -1):
        for fy in (-1, 1):
            cx, cy = sg * W / 2, fy * D / 2
            strap_box(b, "body", (cx + sg * 0.002, cy - fy * 0.03, H / 2), (0.005, 0.06, H + 0.004))
            strap_box(b, "body", (cx - sg * 0.03, cy + fy * 0.002, H / 2), (0.06, 0.005, H + 0.004))
            rivet(b, "body", (cx + sg * 0.006, cy - fy * 0.032, H / 2), "X")
            rivet(b, "body", (cx - sg * 0.032, cy + fy * 0.006, H / 2), "Y")
    # 長柄：自後框中央斜升到 110 cm 外、離地約 61 cm
    p0 = Vector((0, D / 2 + 0.005, 0.075))
    d = Vector((0, 1.10, 0.53)).normalized()
    L = 1.22
    b.box("body", "ww_wood", (0, D / 2 + 0.012, 0.07), (0.075, 0.03, 0.08), tint=_wood_tint(b), bevel=0.004)
    tube(b, "body", "ww_wood", [p0 + d * (L * k / 8) for k in range(9)], 0.02, segs=10)
    tube(b, "body", "ww_bronze", [p0 + d * 0.01, p0 + d * 0.075], 0.026, segs=12)
    tube(b, "body", "ww_rope", [p0 + d * (L - 0.16 + 0.03 * k) for k in range(6)], 0.0235, segs=10)
    b.cylinder("body", "ww_wood", tuple(p0 + d * (L + 0.004)), 0.019, 0.01, axis="Y", segs=10)
    joint = p0 + d * 0.13
    for sg in (1, -1):
        beam_between(b, "body", "ww_wood", (sg * 0.25, D / 2 + 0.006, 0.09), tuple(joint + Vector((sg * 0.012, 0, 0))),
                     0.022, 0.022, tint=_wood_tint(b))
    tube(b, "body", "ww_bronze", [joint - d * 0.03, joint + d * 0.03], 0.025, segs=12)
    return dict(name="河床清淤篩", family="B08", variant="B08", ref="B08_three_view_dry_v002.png",
                notes=["靜置姿勢：籃底平放地面、柄末端離地約 61 cm（參考圖右視）；握持姿勢由角色動畫決定。",
                       "網格 10 mm 淨開口、2.5 mm 青銅線；籃底泥污未建模，留給貼圖或頂點色。"],
                collision="籃盒 60 × 45 × 12 cm＋柄膠囊 Ø4 cm")


# ------------------------------------------------------------------ B09 流速指示浮標

def _hull(b, part, mat, y0, y1, L=0.25, W=0.12, D=0.10, z_top=0.125, scale=1.0, n=10, tint=WOOD):
    """船形浮體：沿 y 取半橢圓截面，兩端收尖，頂面封閉（參考圖頂視有蓋板）。"""
    bm = bmesh.new()
    rings = []
    ys = [y0 + (y1 - y0) * i / 10 for i in range(11)]
    for y in ys:
        tt = min(0.985, abs(2 * y / L))
        w = W / 2 * (1 - tt ** 2) ** 0.55 * scale
        d = D * (1 - 0.8 * tt ** 2.2) * scale
        zt = z_top + 0.02 * tt ** 3 + (scale - 1) * 0.01
        ring = [bm.verts.new((w * math.cos(math.pi * k / n), y, zt - d * math.sin(math.pi * k / n)))
                for k in range(n + 1)]
        rings.append(ring)
    m = n + 1
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(m):
            bm.faces.new((r0[k], r0[(k + 1) % m], r1[(k + 1) % m], r1[k]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    b._merge(part, mat, bm, tint, bevel=0.0, jitter=0.0)


def B09(b):
    """流速指示浮標：25 × 12 × 10 cm 杉木船形浮體、青銅壓重龍骨、20 cm 桅杆紅三角旗，60 cm 繩繫木樁（乾燥展示：鬆繩）。"""
    b.props.update(moss=0.0)
    _hull(b, "body", "ww_wood", -0.125, 0.125, tint=_wood_tint(b, 0.95, 1.05))
    for y in (-0.06, 0.06):
        _hull(b, "body", "ww_bronze", y - 0.008, y + 0.008, scale=1.04)
    b.cylinder("body", "ww_bronze", (0, 0, 0.016), 0.028, 0.032, axis="Z", segs=16)
    b.cylinder("body", "ww_bronze", (0, 0, 0.003), 0.024, 0.006, axis="Z", segs=16)
    # 桅杆、銅套、頂珠
    b.cylinder("body", "ww_wood", (0, 0.0, 0.235), 0.011, 0.22, axis="Z", segs=12)
    b.cylinder("body", "ww_bronze", (0, 0.0, 0.14), 0.016, 0.035, axis="Z", segs=12)
    b.cylinder("body", "ww_bronze", (0, 0.0, 0.352), 0.013, 0.014, axis="Z", segs=12)
    cone(b, "body", "ww_bronze", (0, 0.0, 0.367), 0.012, 0.003, 0.016, segs=10, tint=WOOD)
    # 紅三角旗（鬆繩姿勢：自然下垂、帶波紋）
    bm = bmesh.new()
    rows = []
    for i in range(13):
        s = i / 12
        cz = 0.335 - 0.15 * s
        cy = 0.012 + 0.02 * s
        cx = 0.012 + 0.012 * math.sin(3.2 * math.pi * s)
        half = 0.022 * (1 - s) + 0.003
        rows.append([bm.verts.new((cx + dx, cy + dy, cz + dz)) for dx, dy, dz in
                     ((-0.0015, -half, half * 0.4), (0.0015, -half, half * 0.4),
                      (0.0015, half, -half * 0.4), (-0.0015, half, -half * 0.4))])
    for r0, r1 in zip(rows, rows[1:]):
        for k in range(4):
            bm.faces.new((r0[k], r0[(k + 1) % 4], r1[(k + 1) % 4], r1[k]))
    bm.faces.new(rows[0][::-1])
    bm.faces.new(rows[-1])
    b._merge("body", "ww_cloth", bm, WOOD, bevel=0.0, jitter=0.0)
    # 船頭銅環、繩、木樁
    b.ring("body", "ww_bronze", (0, -0.135, 0.125), 0.008, 0.013, 0.004, axis="X", segs=14)
    sy, sz = -0.72, 0.17
    pts = []
    for k in range(17):
        t = k / 16
        y = -0.147 + (sy + 0.03 + 0.147) * t
        z = 0.125 + (sz - 0.125) * t - 0.1 * math.sin(math.pi * t) + 0.004 * math.sin(9 * t)
        pts.append((0.004 * math.sin(5 * t), y, max(z, 0.007)))
    tube(b, "body", "ww_rope", pts, 0.006, segs=6)
    b.cylinder("body", "ww_wood", (0, sy, 0.02), 0.022, 0.36, axis="Z", segs=10, tint=_wood_tint(b, 0.8, 0.9))
    cone(b, "body", "ww_wood", (0, sy, -0.18), 0.003, 0.022, 0.04, segs=10, tint=(0.8, 0.8, 0.8))
    for k, z in enumerate((0.15, 0.165, 0.18)):
        b.ring("body", "ww_rope", (0, sy, z), 0.021, 0.029, 0.011, axis="Z", segs=14)
    b.ring("body", "ww_bronze", (0, sy + 0.032, 0.17), 0.009, 0.014, 0.005, axis="X", segs=14)
    return dict(name="流速指示浮標", preview_ground=0.0, family="B09", variant="B09", ref="B09_three_view_dry_v002.png",
                states=dict(slack=dict(rope="sag"), taut=dict(rope="straight", float_offset_y=0.0)),
                notes=["乾燥展示：龍骨著地、繩鬆垂、旗下垂；木樁在 -Y 上游 0.72 m，地下 20 cm。",
                       "緊繩姿勢（旗向後飄、浮體被拉向下游）由引擎內切換，母稿只做鬆繩版本。",
                       "參考圖 18 cm 是原水深標註，不是牆高；浮標不參與拼接。"],
                collision="浮體盒 25 × 12 × 12 cm；繩與旗不碰撞")


# ------------------------------------------------------------------ B10 支架家族

def _band(b, part, center, size):
    """包住方木的青銅箍：比木料略大的薄盒。"""
    b.box(part, "ww_bronze", center, size, tint=WOOD, bevel=0.002, jitter=0)


def B10(b):
    """石槽支架（B 型排架）：兩根 12 × 12 cm 木柱入土 30 cm、中心距 80 cm，頂梁 100 × 16 × 16 cm、梁頂離地 50 cm。

    梁沿水流方向（+Y），槽身直接坐在梁上；SOCKET_trough = 1 m 直槽入口原點。
    """
    b.props.update(moss=0.0)
    top = 0.50
    b.box("body", "ww_wood", (0, 0, top - 0.08), (0.16, 1.0, 0.16), tint=_wood_tint(b), bevel=0.008)
    for fy in (-1, 1):
        y = fy * 0.40
        b.box("body", "ww_wood", (0, y, (top - 0.18) / 2 + 0.0), (0.12, 0.12, top + 0.18), tint=_wood_tint(b),
              bevel=0.006)
        cone(b, "body", "ww_wood", (0, y, -0.24), 0.006, 0.085, 0.12, tint=_wood_tint(b, 0.8, 0.9))
        beam_between(b, "body", "ww_wood", (0, y - fy * 0.06, 0.10), (0, fy * 0.13, top - 0.16), 0.07, 0.06,
                     tint=_wood_tint(b))
        _band(b, "body", (0, y, top - 0.19), (0.128, 0.128, 0.035))
        _band(b, "body", (0, y, 0.05), (0.128, 0.128, 0.035))
        _band(b, "body", (0, y, top + 0.004), (0.17, 0.05, 0.008))
        for sg in (1, -1):
            _band(b, "body", (sg * 0.084, y, top - 0.06), (0.008, 0.05, 0.12))
            rivet(b, "body", (sg * 0.09, y, top - 0.06), "X", r=0.009, depth=0.008)
        _band(b, "body", (0, fy * 0.47, top - 0.08), (0.168, 0.035, 0.168))
    b.socket("trough", (0, -0.5, top))
    return dict(name="石槽支架（排架）", preview_ground=0.0, family="B10", variant="B10", ref="B10_three_view_dry_v002.png",
                notes=["地面 z = 0；木柱尖頭入土 30 cm（z = -0.30）。梁頂 z = 0.50 與槽底貼合，無空隙。",
                       "參考圖正視即槽身長向，本件對應 Unity／Blender 的右視；18 cm 為原水深標註，不是牆高。"],
                collision="梁盒＋兩柱盒；入土部分不碰撞")


def B10_V02(b):
    """低矮楔固枕木支架：100 × 24 × 16 cm 橫枕木頂離地 30 cm，兩塊石墩承托，四根 8 cm 木樁＋楔片夾住枕木兩端。

    枕木橫跨水流（沿 X），槽身縱向坐在枕木中央；SOCKET_trough = 1 m 直槽入口原點。
    """
    b.props.update(moss=0.8)
    top = 0.30
    b.box("body", "ww_wood", (0, 0, top - 0.08), (1.0, 0.24, 0.16), tint=_wood_tint(b), bevel=0.008)
    for sg in (1, -1):
        b.box("body", "ww_stone", (sg * 0.30, 0, 0.0), (0.18, 0.24, 0.28), tint=b.stone_tint(0.95), bevel=0.016)
        for fy in (-1, 1):
            x, y = sg * 0.46, fy * 0.155
            b.box("body", "ww_wood", (x, y, 0.06), (0.08, 0.08, 0.68), tint=_wood_tint(b), bevel=0.005)
            cone(b, "body", "ww_wood", (x, y, 0.42), 0.057, 0.004, 0.04, tint=_wood_tint(b))
            cone(b, "body", "ww_wood", (x, y, -0.3), 0.004, 0.057, 0.04, tint=_wood_tint(b, 0.8, 0.9))
            b.obox("body", "ww_wood", (x + sg * 0.065, y, 0.23), (0.11, 0.022, 0.05), (0, sg * math.radians(6), 0),
                   tint=_wood_tint(b, 0.85, 0.95), bevel=0.003, jitter=0)
            _band(b, "body", (x + sg * 0.043, y, 0.23), (0.008, 0.07, 0.11))
            _band(b, "body", (x, y + fy * 0.043, 0.24), (0.075, 0.008, 0.13))
            rivet(b, "body", (x, y + fy * 0.048, 0.24), "Y", r=0.01)
            _band(b, "body", (x, y, 0.385), (0.086, 0.086, 0.03))
            for dz in (-0.035, 0.035):
                rivet(b, "body", (x + sg * 0.048, y, 0.23 + dz), "X", r=0.008)
        _band(b, "body", (sg * 0.47, 0, top - 0.08), (0.04, 0.25, 0.165))
    b.socket("trough", (0, -0.5, top))
    return dict(name="低矮楔固枕木支架", preview_ground=0.0, family="B10", variant="B10-V02", ref="B10_V02_three_view_original_dry.png",
                notes=["支承頂 z = 0.30（manifest 審核選 30 cm；原圖 25／30／46 cm 標註互相矛盾）。",
                       "木樁在 x = ±0.46，槽外寬 60 cm 落在兩組木樁之間，不與槽壁衝突；石墩入土 14 cm、木樁入土 30 cm。"],
                collision="枕木盒＋兩石墩盒")


def B10_V03(b):
    """高四樁棧架：平面 100 × 80 cm，四根 12 cm 木樁入土 40 cm、樁頭與頂梁齊平於離地 80 cm，端框 X 形斜撐。"""
    b.props.update(moss=0.0)
    top = 0.80
    xs, ys = 0.34, 0.44
    for sg in (1, -1):
        b.box("body", "ww_wood", (sg * xs, 0, top - 0.07), (0.12, 1.0, 0.14), tint=_wood_tint(b), bevel=0.007)
    for fy in (-1, 1):
        b.box("body", "ww_wood", (0, fy * ys, top - 0.07), (0.82, 0.12, 0.14), tint=_wood_tint(b), bevel=0.007)
        for d in (1, -1):
            beam_between(b, "body", "ww_wood", (-d * (xs - 0.06), fy * (ys + 0.075), 0.08),
                         (d * (xs - 0.06), fy * (ys + 0.075), top - 0.16), 0.06, 0.03, tint=_wood_tint(b))
        rivet(b, "body", (0, fy * (ys + 0.093), 0.37), "Y", r=0.012, depth=0.01)
    for sg in (1, -1):
        for fy in (-1, 1):
            x, y = sg * xs, fy * ys
            b.box("body", "ww_wood", (x, y, (top - 0.40) / 2), (0.12, 0.12, top + 0.40), tint=_wood_tint(b),
                  bevel=0.006)
            beam_between(b, "body", "ww_wood", (x - sg * 0.075, y - fy * 0.06, 0.42),
                         (x - sg * 0.075, fy * 0.2, top - 0.14), 0.03, 0.06, tint=_wood_tint(b))
            for z in (0.04, 0.50):
                _band(b, "body", (x, y, z), (0.128, 0.128, 0.035))
            _band(b, "body", (x + sg * 0.064, y, top - 0.07), (0.008, 0.07, 0.11))
            _band(b, "body", (x, y + fy * 0.064, top - 0.07), (0.07, 0.008, 0.11))
            rivet(b, "body", (x + sg * 0.07, y, top - 0.07), "X", r=0.009)
            b.cylinder("body", "ww_wood", (x, y + fy * 0.064, top - 0.03), 0.012, 0.02, axis="Y", segs=8,
                       tint=(0.8, 0.8, 0.8))
    b.socket("trough", (0, -0.5, top))
    return dict(name="高四樁棧架", preview_ground=0.0, family="B10", variant="B10-V03", ref="B10_V03_three_view_dry_v002.png",
                notes=["地上 80 cm、入土 40 cm（總樁長 120 cm，依 manifest 修正參考圖的 120 cm 地上標註）。",
                       "樁頭與四根頂梁頂面齊平於 z = 0.80，槽底直接坐上，無空隙。"],
                collision="頂框盒＋四樁盒")


# ------------------------------------------------------------------ B11 手推車

def _wheel(b, part, x):
    y0, z0 = -0.30, 0.30
    b.ring(part, "ww_wood", (x, y0, z0), 0.245, 0.282, 0.045, axis="X", segs=36, tint=_wood_tint(b))
    b.ring(part, "ww_bronze", (x, y0, z0), 0.279, 0.30, 0.05, axis="X", segs=36)
    for k in range(10):
        a = 2 * math.pi * k / 10
        b.obox(part, "ww_wood", (x, y0 + math.cos(a) * 0.155, z0 + math.sin(a) * 0.155), (0.024, 0.2, 0.03),
               (a, 0, 0), tint=_wood_tint(b), bevel=0.003, jitter=0)
        rivet(b, part, (x + math.copysign(0.026, x), y0 + math.cos(a + 0.31) * 0.289, z0 + math.sin(a + 0.31) * 0.289),
              "X", r=0.007, depth=0.006)
    b.cylinder(part, "ww_wood", (x, y0, z0), 0.06, 0.11, axis="X", segs=16, tint=_wood_tint(b))
    b.ring(part, "ww_bronze", (x + math.copysign(0.03, x), y0, z0), 0.056, 0.07, 0.03, axis="X", segs=20)
    b.cylinder(part, "ww_bronze", (x + math.copysign(0.065, x), y0, z0), 0.03, 0.03, axis="X", segs=14)


def B11(b):
    """古樸兩輪手推車：車床 120 × 75 cm、全長 180、全寬 85（輪外更寬）、握把高 95 cm、Ø60 cm 木輪包銅箍。

    車頭（-Y）有兩支駐車腳；貨物（石塊、木料、鏟、木槌、綁繩）為獨立部件 cargo，可隱藏。
    """
    b.props.update(moss=0.0)
    yf, yb = -0.9, 0.3                                   # 車床前後
    for sg in (1, -1):
        b.box("body", "ww_wood", (sg * 0.40, (yf + yb) / 2, 0.40), (0.07, yb - yf + 0.04, 0.08), tint=_wood_tint(b),
              bevel=0.006)
        _wheel(b, "body", sg * 0.47)
        b.box("body", "ww_wood", (sg * 0.40, -0.30, 0.33), (0.08, 0.11, 0.08), tint=_wood_tint(b), bevel=0.005)
        beam_between(b, "body", "ww_wood", (sg * 0.38, yb - 0.12, 0.42), (sg * 0.37, 0.90, 0.93), 0.05, 0.05,
                     tint=_wood_tint(b))
        d = Vector((0, 0.90 - (yb - 0.12), 0.93 - 0.42)).normalized()
        end = Vector((sg * 0.37, 0.90, 0.93))
        tube(b, "body", "ww_rope", [end - d * (0.16 - 0.025 * k) for k in range(6)], 0.031, segs=10)
        beam_between(b, "body", "ww_wood", (sg * 0.36, yf + 0.12, 0.37), (sg * 0.37, yf + 0.10, 0.03), 0.055, 0.055,
                     tint=_wood_tint(b))
        b.box("body", "ww_bronze", (sg * 0.37, yf + 0.10, 0.017), (0.08, 0.08, 0.034), tint=WOOD, bevel=0.004,
              jitter=0)
        # 側欄：三根立柱＋兩道橫欄
        for y in (yf + 0.02, -0.3, yb - 0.02):
            b.box("body", "ww_wood", (sg * 0.395, y, 0.565), (0.045, 0.045, 0.19), tint=_wood_tint(b), bevel=0.004)
            _band(b, "body", (sg * 0.395, y, 0.48), (0.05, 0.05, 0.03))
        for z in (0.53, 0.625):
            b.box("body", "ww_wood", (sg * 0.395, (yf + yb) / 2, z), (0.03, yb - yf, 0.045), tint=_wood_tint(b),
                  bevel=0.004)
        for y in (yf + 0.02, yb - 0.02):
            strap_box(b, "body", (sg * 0.42, y, 0.58), (0.006, 0.07, 0.12))
    b.cylinder("body", "ww_bronze", (0, -0.30, 0.30), 0.025, 0.86, axis="X", segs=12)
    for y in (yf + 0.06, -0.3, yb - 0.08):
        b.box("body", "ww_wood", (0, y, 0.40), (0.84, 0.06, 0.07), tint=_wood_tint(b, 0.85, 0.95), bevel=0.004)
    for i in range(5):
        x = -0.30 + i * 0.15
        b.box("body", "ww_wood", (x, (yf + yb) / 2, 0.452), (0.146, yb - yf, 0.03), tint=_wood_tint(b), bevel=0.003,
              jitter=0.001)
    for y in (yf, yb):
        for z in (0.53, 0.625):
            b.box("body", "ww_wood", (0, y, z), (0.79, 0.03, 0.045), tint=_wood_tint(b), bevel=0.004)
    # 貨物
    for x, y, s in ((-0.2, -0.66, (0.30, 0.26, 0.26)), (0.16, -0.55, (0.28, 0.30, 0.28)),
                    (-0.13, -0.16, (0.32, 0.27, 0.27)), (0.2, 0.06, (0.26, 0.24, 0.24))):
        rock(b, "cargo", (x, y, 0.467 + s[2] * 0.32), s)
    for x, z, yaw in ((-0.02, 0.60, 0.12), (0.12, 0.70, -0.18)):
        beam_between(b, "cargo", "ww_wood", (x - 0.3 * math.sin(yaw), -0.62, z), (x + 0.3 * math.sin(yaw), 0.1, z),
                     0.09, 0.09, tint=_wood_tint(b, 0.8, 0.95))
    # 鏟：柄自後方斜放在木料上，鏟面落在前方石塊上
    s0, s1 = Vector((-0.05, 0.2, 0.78)), Vector((0.2, -0.52, 0.74))
    beam_between(b, "cargo", "ww_wood", tuple(s0), tuple(s1), 0.028, 0.028)
    dsh = (s1 - s0).normalized()
    beam_between(b, "cargo", "ww_iron", tuple(s1 - dsh * 0.02), tuple(s1 + dsh * 0.17), 0.13, 0.008, bevel=0.003)
    beam_between(b, "cargo", "ww_wood", (-0.25, -0.2, 0.74), (-0.05, -0.65, 0.69), 0.026, 0.026)
    b.cylinder("cargo", "ww_wood", (-0.27, -0.16, 0.745), 0.042, 0.13, axis="X", segs=14, tint=(0.8, 0.8, 0.8))
    for y in (-0.55, -0.05):
        pts = [(0.40 * math.cos(math.pi * k / 12), y, 0.62 + 0.2 * math.sin(math.pi * k / 12)) for k in range(13)]
        tube(b, "cargo", "ww_rope", pts, 0.008, segs=6)
    return dict(name="兩輪手推車", family="B11", variant="B11", ref="B11_three_view_original_dry.png",
                notes=["輪心在車床前端後方 60 cm（參考圖右視量取），駐車腳在車頭，握把末端高 0.93 m。",
                       "輪外寬約 1.08 m（參考圖 85 cm 為車框寬，木輪在框外）。cargo 部件可單獨隱藏。"],
                collision="車床盒＋兩輪圓柱＋握把膠囊")


# ------------------------------------------------------------------ B12 完工紀錄碑座

def _inlay(b, pts, y, part="body", w=0.013):
    """面板上的深色刻線（箭頭桿）：沿 x-z 折線的薄條。"""
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, z1 - z0)
        a = math.atan2(z1 - z0, x1 - x0)
        b.obox(part, "ww_gasket", ((x0 + x1) / 2, y, (z0 + z1) / 2), (L + w * 0.6, 0.004, w), (0, -a, 0),
               tint=WOOD, bevel=0.0, jitter=0)


def _arrow_head(b, x, z, a, y, part="body"):
    s = 0.028
    pts = [(x + math.cos(a) * s, z + math.sin(a) * s),
           (x + math.cos(a + 2.5) * s * 0.75, z + math.sin(a + 2.5) * s * 0.75),
           (x + math.cos(a - 2.5) * s * 0.75, z + math.sin(a - 2.5) * s * 0.75)]
    prism_xz(b, part, "ww_gasket", pts, y - 0.002, y + 0.002, tint=WOOD, bevel=0.0, jitter=0)


def B12(b):
    """公共水工完工紀錄碑座：80 × 60 × 25 cm 石座、背後 18 cm 厚石碑，前方木框掛三格方案板（三條路線的箭頭、方孔與木栓）。

    木栓 peg_1–3 為獨立部件：插入代表該方案已完工。
    """
    b.props.update(moss=0.8)
    for x0, x1 in ((-0.4, -0.12), (-0.12, 0.14), (0.14, 0.4)):
        b.box("body", "ww_stone", ((x0 + x1) / 2, 0, 0.125), (x1 - x0, 0.60, 0.25), tint=b.stone_tint(0.96),
              bevel=0.02)
    prism_yz(b, "body", "ww_stone", [(-0.07, 0.25), (0.11, 0.25), (0.11, 0.94), (0.04, 1.03), (-0.07, 1.03)],
             -0.28, 0.28, tint=b.stone_tint(1.0), bevel=0.02)
    yp = -0.165
    for sg in (1, -1):
        x = sg * 0.32
        b.box("body", "ww_stone", (x, yp, 0.285), (0.14, 0.14, 0.07), tint=b.stone_tint(0.93), bevel=0.014)
        b.box("body", "ww_wood", (x, yp, 0.71), (0.09, 0.09, 0.78), tint=_wood_tint(b), bevel=0.006)
        for z in (0.36, 1.02):
            _band(b, "body", (x, yp, z), (0.096, 0.096, 0.035))
        strap_box(b, "body", (x, yp - 0.048, 1.06), (0.1, 0.006, 0.1))
        rivet(b, "body", (x, yp - 0.053, 1.06), "Y", r=0.01)
    b.box("body", "ww_wood", (0, yp, 1.06), (0.84, 0.08, 0.08), tint=_wood_tint(b), bevel=0.006)
    # 方案板
    yf = yp - 0.045 - 0.016
    b.box("body", "ww_wood", (0, yf, 0.70), (0.60, 0.032, 0.56), tint=_wood_tint(b, 0.95, 1.05), bevel=0.004)
    yface = yf - 0.016
    for cx, cz, sx, sz in ((0, 0.975, 0.6, 0.016), (0, 0.425, 0.6, 0.016), (-0.292, 0.70, 0.016, 0.56),
                           (0.292, 0.70, 0.016, 0.56)):
        strap_box(b, "body", (cx, yface - 0.002, cz), (sx, 0.005, sz))
    for sx in (1, -1):
        for sz in (1, -1):
            strap_box(b, "body", (sx * 0.265, yface - 0.004, 0.70 + sz * 0.255), (0.05, 0.005, 0.05))
            rivet(b, "body", (sx * 0.265, yface - 0.008, 0.70 + sz * 0.255), "Y", r=0.008)
    rows = (0.88, 0.70, 0.52)
    for z in (0.79, 0.61):
        _inlay(b, [(-0.27, z), (0.27, z)], yface - 0.001, w=0.006)
    _inlay(b, [(0.07, 0.435), (0.07, 0.965)], yface - 0.001, w=0.006)
    yi = yface - 0.002
    # 1 直通村田：直箭頭
    _inlay(b, [(-0.23, rows[0]), (0.0, rows[0])], yi)
    _arrow_head(b, 0.012, rows[0], 0.0, yi)
    # 2 繞過育幼區：彎曲繞行
    curve = [(-0.23 + 0.23 * k / 10, rows[1] - 0.03 + 0.06 * (3 * (k / 10) ** 2 - 2 * (k / 10) ** 3))
             for k in range(11)]
    _inlay(b, curve, yi)
    _arrow_head(b, 0.012, rows[1] + 0.03, 0.0, yi)
    # 3 先清淤再暫時導流：分岔
    for sgn in (1, -1):
        br = [(-0.23 + 0.23 * k / 10, rows[2] + sgn * 0.035 * (3 * (k / 10) ** 2 - 2 * (k / 10) ** 3) * (k > 3))
              for k in range(11)]
        _inlay(b, br, yi)
        _arrow_head(b, 0.012, rows[2] + sgn * 0.035, 0.0, yi)
    for k, z in enumerate(rows):
        for cx, cz, sx, sz in ((0.13, z + 0.024, 0.056, 0.008), (0.13, z - 0.024, 0.056, 0.008),
                               (0.106, z, 0.008, 0.04), (0.154, z, 0.008, 0.04)):
            strap_box(b, "body", (cx, yface - 0.002, cz), (sx, 0.006, sz))
        b.box("body", "ww_gasket", (0.13, yface - 0.001, z), (0.04, 0.003, 0.04), tint=WOOD, bevel=0.0, jitter=0)
        b.cylinder(f"peg_{k + 1}", "ww_wood", (0.215, yface - 0.022, z), 0.012, 0.045, axis="Y", segs=12,
                   tint=(0.85, 0.7, 0.55))
        b.cylinder(f"peg_{k + 1}", "ww_bronze", (0.215, yface - 0.046, z), 0.014, 0.006, axis="Y", segs=12)
    strap_box(b, "body", (0, 0.113, 0.85), (0.44, 0.006, 0.03))
    for sg in (1, -1):
        b.cylinder("body", "ww_bronze", (sg * 0.19, 0.12, 0.85), 0.016, 0.012, axis="Y", segs=14)
    return dict(name="完工紀錄碑座", family="B12", variant="B12", ref="B12_three_view_original_dry.png",
                states=dict(pegs=dict(peg_1="直通村田", peg_2="繞過育幼區", peg_3="先清淤再暫時導流")),
                notes=["三格箭頭對應三條路線方案：直箭頭＝直通村田、彎箭頭＝繞過育幼區、分岔＝先清淤再暫時導流（推定對應）。",
                       "木栓 peg_1–3 是獨立部件，完工時顯示；方孔為銅框淺槽。"],
                collision="石座盒＋碑石盒")
