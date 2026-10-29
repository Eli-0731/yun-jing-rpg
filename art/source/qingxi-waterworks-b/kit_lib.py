"""青溪水工 B 套件：程序化建模共用工具（Blender 5.2，1 單位 = 1 m）。

座標約定（Blender，Z 向上）：
- 每件的「入口」接口在原點，水流朝 +Y；正視圖由 -Y 看入口。
- 接口與水道中心線都落在 0.25 m 格點上，方向只有 ±X／±Y。
- 標準斷面：外寬 0.60、淨寬 0.40、總高 0.40、底厚 0.10、淨深 0.30；
  運作水面基準 z = 0.28（水深 18 cm），接口面平齊、不外凸。
"""
import json
import math
import os
import random

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector, noise
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SET = "qingxi-waterworks-b"
TEX_DIR = os.path.join(HERE, "textures")
EXPORT_DIR = os.path.join(ROOT, "art", "exports", SET)
PREVIEW_DIR = os.path.join(ROOT, "art", "previews", SET)

GRID = 0.25
OUTER_W = 0.60
CLEAR_W = 0.40
WALL_T = 0.10
TOTAL_H = 0.40
FLOOR_T = 0.10
WATER_Z = 0.28
AUTHOR = "蘇奕安 Josh（joshsu54@gmail.com），Claude Code 協作建模"


# ---------------------------------------------------------------- textures

def _fbm(n, beta, seed, aniso=(1.0, 1.0)):
    rng = np.random.default_rng(seed)
    white = rng.standard_normal((n, n))
    fy = np.fft.fftfreq(n)[:, None] * aniso[1]
    fx = np.fft.fftfreq(n)[None, :] * aniso[0]
    f = np.sqrt(fx * fx + fy * fy)
    f[0, 0] = 1.0
    spec = np.fft.fft2(white) / f ** beta
    spec[0, 0] = 0
    out = np.real(np.fft.ifft2(spec))
    out -= out.min()
    return out / max(out.max(), 1e-9)


def _voronoi(n, count, seed):
    """可平鋪 Voronoi：回傳 (F2-F1 距離, 所屬格 id)。"""
    rng = np.random.default_rng(seed)
    pts = rng.random((count, 2)) * n
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    f1 = np.full((n, n), 1e9, np.float32)
    f2 = np.full((n, n), 1e9, np.float32)
    ids = np.zeros((n, n), np.int32)
    for k, (px, py) in enumerate(pts):
        dx = np.abs(xx - px)
        dx = np.minimum(dx, n - dx)
        dy = np.abs(yy - py)
        dy = np.minimum(dy, n - dy)
        d = np.sqrt(dx * dx + dy * dy)
        closer = d < f1
        f2 = np.where(closer, f1, np.minimum(f2, d))
        ids = np.where(closer, k, ids)
        f1 = np.minimum(f1, d)
    return f2 - f1, ids


def _normal_from_height(h, strength):
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * strength
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * strength
    nz = np.ones_like(h)
    ln = np.sqrt(gx * gx + gy * gy + 1)
    # 影像 y 由上而下，切線空間 +Y 朝上 → gy 取正
    return np.stack([(-gx / ln) * 0.5 + 0.5, (gy / ln) * 0.5 + 0.5, nz / ln * 0.5 + 0.5], -1)


def _srgb(c):
    return np.array(c, dtype=np.float64) / 255.0


def _save_png(name, rgb, color=True):
    os.makedirs(TEX_DIR, exist_ok=True)
    path = os.path.join(TEX_DIR, name + ".png")
    n = rgb.shape[0]
    img = bpy.data.images.get(name) or bpy.data.images.new(name, n, n, alpha=False)
    if img.size[0] != n:
        img.scale(n, n)
    rgba = np.ones((n, n, 4), dtype=np.float32)
    rgba[..., :3] = np.clip(rgb[::-1], 0, 1)  # Blender 影像由下而上
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    img.filepath = path
    if not color:
        img.colorspace_settings.name = "Non-Color"
    return img


def make_textures(n=512):
    """生成可平鋪貼圖（固定亂數種子，重跑結果相同）。"""
    imgs = {}
    # 舊石（對照三視圖）：鎚鑿卵面——密集小隆起只做柔和明暗與法線浮雕，不畫深色裂線；
    # 石塊之間的縫由幾何圓角＋頂點色產生。石材貼圖用 2 倍解析度。
    ns = n * 2
    edge, ids = _voronoi(ns, 220, 15)
    rng = np.random.default_rng(16)
    cell_k = rng.uniform(0.95, 1.05, ids.max() + 1)[ids]
    dome = np.clip(edge / 24.0, 0, 1) ** 0.85
    dome_c = np.clip(edge / 40.0, 0, 1)                 # 顏色用更寬的過渡
    mott = _fbm(ns, 2.0, 11)
    mid = _fbm(ns, 1.2, 12)
    grain = _fbm(ns, 0.2, 13)
    speck = _fbm(ns, 0.0, 14)
    base = _srgb((150, 143, 130))
    rgb = np.empty((ns, ns, 3))
    warm = (mott - 0.5) * 0.07
    rgb[..., 0] = base[0] * (1 + warm)
    rgb[..., 1] = base[1]
    rgb[..., 2] = base[2] * (1 - warm)
    k = cell_k * (0.93 + 0.07 * dome_c) * (0.90 + 0.14 * mott) * (0.96 + 0.06 * grain)
    k = k * np.where(speck > 0.88, 0.8, 1.0)
    rgb *= k[..., None]
    imgs["ww_stone"] = _save_png("ww_stone", rgb)
    patch = _fbm(ns, 1.7, 17)
    crev = (1 - dome) ** 2
    mossy = np.clip((patch - 0.55) * 2.5, 0, 1) * (0.35 + 0.65 * crev) + np.clip((mid - 0.72) * 2.5, 0, 1) * 0.2
    mossy = np.clip(mossy, 0, 0.85)[..., None]
    moss_col = _srgb((90, 104, 62)) * (0.8 + 0.3 * grain[..., None])
    imgs["ww_stone_moss"] = _save_png("ww_stone_moss", rgb * (1 - mossy) + moss_col * mossy)
    height = dome * 0.75 + mid * 0.15 + grain * 0.10
    for _ in range(6):  # 放寬卵面交界，避免出現細黑裂線
        height = (height + np.roll(height, 1, 0) + np.roll(height, -1, 0) + np.roll(height, 1, 1)
                  + np.roll(height, -1, 1)) / 5
    imgs["ww_stone_n"] = _save_png("ww_stone_n", _normal_from_height(height, 1.5), color=False)

    # 舊杉木：沿 U 方向的木紋
    g1 = _fbm(n, 1.4, 21, aniso=(0.08, 1.0))
    g2 = _fbm(n, 0.7, 22, aniso=(0.15, 1.0))
    knots = _fbm(n, 2.0, 23)
    wood_a = _srgb((116, 88, 64))
    wood_b = _srgb((84, 64, 48))
    tt = np.clip(g1 * 0.7 + g2 * 0.3, 0, 1)[..., None]
    rgb = wood_a * (1 - tt) + wood_b * tt
    rgb *= (0.92 + 0.12 * knots[..., None])
    imgs["ww_wood"] = _save_png("ww_wood", rgb)

    # 舊青銅：褐銅底＋綠鏽斑
    pat = _fbm(n, 1.5, 31)
    fine = _fbm(n, 0.5, 32)
    bronze = _srgb((158, 110, 64))
    verd = _srgb((88, 128, 108))
    m = np.clip((pat - 0.68) * 3, 0, 0.6)[..., None]
    rgb = bronze * (1 - m) + verd * m
    rgb *= (0.85 + 0.25 * fine[..., None])
    imgs["ww_bronze"] = _save_png("ww_bronze", rgb)

    # 濕土：褐土＋小卵石點
    s1 = _fbm(n, 1.2, 41)
    s2 = _fbm(n, 0.3, 42)
    soil_a = _srgb((92, 74, 56))
    soil_b = _srgb((58, 48, 38))
    peb = np.clip((s2 - 0.78) * 8, 0, 1)[..., None]
    rgb = soil_a * (1 - s1[..., None]) + soil_b * s1[..., None]
    rgb = rgb * (1 - peb) + _srgb((150, 142, 128)) * peb
    imgs["ww_soil"] = _save_png("ww_soil", rgb)

    # 田土（F01）：暖橙褐乾土、碎礫顆粒與土塊起伏，對照灌溉田地三視圖
    edge_f, ids_f = _voronoi(n, 900, 51)
    rng = np.random.default_rng(52)
    grain_k = rng.uniform(0.80, 1.15, ids_f.max() + 1)[ids_f]
    clod = _fbm(n, 1.6, 53)
    fine_f = _fbm(n, 0.2, 54)
    peb_e, peb_id = _voronoi(n, 2600, 57)                 # 碎礫：小圓點（Voronoi 細胞中心）
    peb_on = np.random.default_rng(58).random(peb_id.max() + 1)[peb_id] > 0.88
    gravel = np.clip((_fbm(n, 0.1, 55) - 0.80) * 7, 0, 1) * 0.6 + np.clip((peb_e - 1.5) / 3.0, 0, 1) * peb_on * 0.75
    dark = np.clip((_fbm(n, 0.1, 56) - 0.84) * 7, 0, 1)
    soil_a = _srgb((136, 100, 72))
    soil_b = _srgb((98, 72, 52))
    tt = np.clip(clod * 0.75 + fine_f * 0.25, 0, 1)[..., None]
    rgb = soil_a * (1 - tt) + soil_b * tt
    rgb *= (0.94 + 0.08 * grain_k[..., None])
    rgb = rgb * (1 - gravel[..., None]) + _srgb((150, 132, 110)) * gravel[..., None]
    rgb = rgb * (1 - 0.55 * dark[..., None])
    imgs["ww_field_soil"] = _save_png("ww_field_soil", rgb)
    hf = clod * 0.5 + gravel * 0.6 - dark * 0.4 + fine_f * 0.25 + np.clip(edge_f / 5.0, 0, 1) * 0.08
    imgs["ww_field_soil_n"] = _save_png("ww_field_soil_n", _normal_from_height(hf, 2.2), color=False)

    # 溪水（S01）：青綠水色＋光網（Voronoi 細線）＋沿 V（流向）拉長的白色水花；法線為細碎漣漪
    # 光網：兩層 ridged 雜訊（|2f−1| 取谷線）相乘，得到彎曲、不規則的水底光紋
    r1 = 1.0 - np.abs(2 * _fbm(n, 1.5, 61) - 1)
    r2 = 1.0 - np.abs(2 * _fbm(n, 1.3, 67) - 1)
    caust = np.clip(r1 ** 10 + r2 ** 10, 0, 1) * (0.5 + 0.5 * _fbm(n, 1.6, 66))
    swirl = _fbm(n, 1.4, 62)
    foam_a = _fbm(n, 1.0, 63, aniso=(1.0, 0.18))          # V 方向拉長
    foam_b = _fbm(n, 0.3, 64, aniso=(1.0, 0.35))
    foam = np.clip((foam_a * 0.75 + foam_b * 0.25 - 0.60) * 4.0, 0, 1) * np.clip((foam_b - 0.30) * 3, 0, 1)
    deep = _srgb((52, 132, 136))
    shallow = _srgb((92, 176, 168))
    tt = np.clip(swirl * 1.2 - 0.1, 0, 1)[..., None]
    rgb = deep * (1 - tt) + shallow * tt
    rgb = rgb + (_srgb((196, 236, 226)) - rgb) * (caust[..., None] * 0.45)
    rgb = rgb + (_srgb((240, 248, 244)) - rgb) * foam[..., None]
    imgs["ww_stream"] = _save_png("ww_stream", rgb)
    rip = _fbm(n, 1.1, 65, aniso=(1.0, 0.6)) * 0.7 + foam * 0.3
    imgs["ww_stream_n"] = _save_png("ww_stream_n", _normal_from_height(rip, 2.0), color=False)

    # 河床（S02）：灰褐沙礫，密集小卵石（Voronoi 細胞）＋細沙顆粒
    rb_e, rb_id = _voronoi(n, 1800, 71)
    rng = np.random.default_rng(72)
    stone_k = rng.uniform(0.75, 1.25, rb_id.max() + 1)[rb_id]
    is_peb = rng.random(rb_id.max() + 1)[rb_id] > 0.55
    sand_m = _fbm(n, 1.3, 73)
    sand_f = _fbm(n, 0.1, 74)
    sand = _srgb((168, 148, 118)) * (0.88 + 0.18 * sand_m[..., None]) * (0.94 + 0.1 * sand_f[..., None])
    peb_mask = (np.clip((rb_e - 1.0) / 2.5, 0, 1) * is_peb)[..., None]
    peb_col = _srgb((146, 138, 124)) * stone_k[..., None]
    rgb = sand * (1 - peb_mask) + peb_col * peb_mask
    rgb *= (1 - 0.25 * np.clip(1.0 - rb_e / 1.5, 0, 1) * is_peb)[..., None]      # 卵石邊緣陰影
    imgs["ww_riverbed"] = _save_png("ww_riverbed", rgb)
    hb = np.clip(rb_e / 4.0, 0, 1) ** 0.7 * is_peb * 0.8 + sand_f * 0.2
    imgs["ww_riverbed_n"] = _save_png("ww_riverbed_n", _normal_from_height(hb, 2.4), color=False)
    return imgs


# ---------------------------------------------------------------- materials

MAT_SPECS = {
    "ww_stone": dict(rough=0.88, spec=0.15, metal=0.0),
    "ww_wood": dict(rough=0.80, spec=0.12, metal=0.0),
    "ww_bronze": dict(rough=0.32, spec=0.5, metal=0.65),
    "ww_stone_moss": dict(rough=0.92, spec=0.12, metal=0.0),
    "ww_soil": dict(rough=0.95, spec=0.08, metal=0.0),
    "ww_gasket": dict(rough=0.9, spec=0.1, metal=0.0, color=(0.10, 0.085, 0.07)),
    "ww_seal": dict(rough=0.95, spec=0.08, metal=0.0, color=(0.40, 0.20, 0.12)),
    "ww_cloth": dict(rough=0.85, spec=0.1, metal=0.0, color=(0.56, 0.12, 0.07)),
    "ww_rope": dict(rough=0.95, spec=0.08, metal=0.0, color=(0.20, 0.14, 0.075)),
    "ww_iron": dict(rough=0.55, spec=0.4, metal=0.7, color=(0.30, 0.30, 0.29)),
    "ww_field_soil": dict(rough=0.95, spec=0.08, metal=0.0),
    "ww_riverbed": dict(rough=0.92, spec=0.1, metal=0.0),
    "ww_stream": dict(rough=0.06, spec=0.5, metal=0.0, alpha=0.9),
    "ww_grass": dict(rough=0.9, spec=0.1, metal=0.0, color=(0.15, 0.25, 0.07)),
    "ww_water": dict(rough=0.08, spec=0.5, metal=0.0, color=(0.16, 0.36, 0.38), alpha=0.62),
    # 田面積水（water_polys）：同色，另立材質名，Unity 端給慢速、無主流向的水面參數
    "ww_water_still": dict(rough=0.08, spec=0.5, metal=0.0, color=(0.16, 0.36, 0.38), alpha=0.62),
}


def rgba_socket(sockets, name):
    """ShaderNodeMix 有同名的 float／vector／color 插槽，需取 RGBA 那個。"""
    return next(x for x in sockets if x.name == name and x.type == "RGBA")


def get_material(name, imgs):
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    spec = MAT_SPECS[name]
    mat = bpy.data.materials.new(name)
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = spec["rough"]
    bsdf.inputs["Specular IOR Level"].default_value = spec["spec"]
    bsdf.inputs["Metallic"].default_value = spec["metal"]
    if name in imgs:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = imgs[name]
        vc = nt.nodes.new("ShaderNodeVertexColor")
        vc.layer_name = "Col"
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        nt.links.new(tex.outputs["Color"], rgba_socket(mix.inputs, "A"))
        nt.links.new(vc.outputs["Color"], rgba_socket(mix.inputs, "B"))
        nt.links.new(rgba_socket(mix.outputs, "Result"), bsdf.inputs["Base Color"])
        nkey = "ww_stone_n" if name.startswith("ww_stone") else name + "_n"
        if nkey in imgs:
            nimg = nt.nodes.new("ShaderNodeTexImage")
            nimg.image = imgs[nkey]
            nimg.image.colorspace_settings.name = "Non-Color"
            nmap = nt.nodes.new("ShaderNodeNormalMap")
            nmap.inputs["Strength"].default_value = 0.75
            nt.links.new(nimg.outputs["Color"], nmap.inputs["Color"])
            nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    else:
        c = spec["color"]
        bsdf.inputs["Base Color"].default_value = (c[0], c[1], c[2], 1)
    if "alpha" in spec:
        bsdf.inputs["Alpha"].default_value = spec["alpha"]
        mat.surface_render_method = "BLENDED"
    return mat


# ---------------------------------------------------------------- 2D paths

def line(p0, p1, step=0.05):
    p0, p1 = np.array(p0, float), np.array(p1, float)
    n = max(1, int(math.ceil(np.linalg.norm(p1 - p0) / step)))
    return [tuple(p0 + (p1 - p0) * i / n) for i in range(n + 1)]


def arc(center, r, a0, a1, step=0.04):
    n = max(2, int(math.ceil(abs(a1 - a0) * max(r, 0.05) / step)))
    return [(center[0] + r * math.cos(a0 + (a1 - a0) * i / n),
             center[1] + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def join(*paths):
    out = list(paths[0])
    for p in paths[1:]:
        out += list(p[1:]) if np.allclose(out[-1], p[0]) else list(p)
    return out


def cumlen(path):
    s = [0.0]
    for a, b in zip(path, path[1:]):
        s.append(s[-1] + math.dist(a, b))
    return s


def sample(path, s_target):
    """回傳弧長 s 處的位置與切線。"""
    s = cumlen(path)
    s_target = min(max(s_target, 0.0), s[-1])
    for i in range(len(path) - 1):
        if s[i + 1] >= s_target - 1e-9:
            seg = s[i + 1] - s[i]
            t = 0 if seg < 1e-12 else (s_target - s[i]) / seg
            a, b = np.array(path[i]), np.array(path[i + 1])
            d = b - a
            d = d / max(np.linalg.norm(d), 1e-12)
            return tuple(a + (b - a) * t), (d[0], d[1])
    a, b = np.array(path[-2]), np.array(path[-1])
    d = (b - a) / max(np.linalg.norm(b - a), 1e-12)
    return tuple(b), (d[0], d[1])


def subpath(path, s0, s1, step=0.04):
    """取弧長 s0–s1 的站點；直線段只留轉折點，避免多餘的細長面妨礙倒角。"""
    n = max(1, int(math.ceil((s1 - s0) / step)))
    pts = [sample(path, s0 + (s1 - s0) * i / n) for i in range(n + 1)]
    keep = [pts[0]]
    for i in range(1, len(pts) - 1):
        d0, d1 = keep[-1][1], pts[i + 1][1]
        if abs(d0[0] * d1[1] - d0[1] * d1[0]) > 1e-4 or d0[0] * d1[0] + d0[1] * d1[1] < 0:
            keep.append(pts[i])
    keep.append(pts[-1])
    return keep


def offset_pts(stations, off):
    """stations: [(p, tangent)]，左側為正（面向 +tangent 時的左）。"""
    out = []
    for p, d in stations:
        nx, ny = -d[1], d[0]
        out.append((p[0] + nx * off, p[1] + ny * off))
    return out


# ---------------------------------------------------------------- builder

class Builder:
    """收集一件模型的幾何：每個「石塊」是獨立封閉網格，最後依材質合併。"""

    def __init__(self, piece_id, seed=None):
        self.id = piece_id
        self.rng = random.Random(seed if seed is not None else piece_id)
        self.parts = {}          # 部件名稱 -> {材質 -> bmesh}
        self.ports = []
        self.flows = []          # 水流路徑：dict(path, z0, z1, width, name)
        self.water_polys = []    # 靜水面多邊形：dict(poly, z, name)
        self.sockets = []        # 額外掛點：dict(name, pos, rot)
        self.props = {}
        self.port_planes = []    # (point2d, normal2d)：接口面，避免抖動與青苔

    # --- 低階：把一個封閉 bmesh 合併進部件
    def _merge(self, part, mat, bm_block, tint, wear=0.0, bevel=0.01, jitter=0.004):
        stone = mat == "ww_stone" and bevel > 0
        groove = None
        if stone:
            # 石塊：圓角放大到約 22% 最小邊（上限 2.6 cm），相鄰石塊的圓角自然形成凹縫
            bmesh.ops.recalc_face_normals(bm_block, faces=bm_block.faces)
            bm_block.normal_update()
            xs = [v.co.x for v in bm_block.verts]
            ys = [v.co.y for v in bm_block.verts]
            zs = [v.co.z for v in bm_block.verts]
            thick = min(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
            if self.props.get("thin_min"):
                thick = min(thick, self.props["thin_min"])
            # 牆石（指定圓角 ≥ 1 cm）放大圓角；底板等指定小圓角者只略放大，避免鋪面像階梯
            bevel = max(bevel, min(0.026, 0.22 * thick)) if bevel >= 0.01 else max(bevel, 0.009)
            # 崩角候選：原始角點（不在接口面、不在底面），方向取相鄰面法線平均
            corners = []
            for v in bm_block.verts:
                fs = v.link_faces
                sharp = sum(1 for e in v.link_edges
                            if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(30))
                if len(fs) < 3 or sharp < 3:      # 只取三條銳邊交會的真角點（弧牆分段點不算）
                    continue
                if self._on_port(v.co, tol=0.012) or v.co.z < min(zs) + 0.002:
                    continue
                n = Vector((0, 0, 0))
                for f in fs:
                    n += f.normal
                if n.length < 1e-6:
                    continue
                corners.append((v.co.copy(), n.normalized()))
            self.rng.shuffle(corners)
            n_chip = self.rng.choice((0, 1, 1, 2, 2)) if thick > 0.06 else self.rng.choice((0, 0, 1))
            chips = []
            for c, n in corners[:n_chip]:
                tilt = Vector((self.rng.uniform(-0.35, 0.35), self.rng.uniform(-0.35, 0.35),
                               self.rng.uniform(-0.2, 0.35)))
                chips.append((c, (n + tilt).normalized(), self.rng.uniform(0.012, 0.022) + 0.6 * min(0.026, 0.22 * thick)))
            ref = bm_block.copy()
            bmesh.ops.triangulate(ref, faces=ref.faces)
            ref.normal_update()
            tree = BVHTree.FromBMesh(ref)
        if bevel > 0:
            edges = [e for e in bm_block.edges
                     if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(30)]
            if edges:
                segs = 3 if stone else (3 if bevel >= 0.012 else (2 if bevel >= 0.006 else 1))
                bmesh.ops.bevel(bm_block, geom=edges, offset=bevel, segments=segs,
                                affect="EDGES", profile=0.6 if stone else 0.5, clamp_overlap=True)
        if stone:
            bm_block.normal_update()
            groove = []
            for v in bm_block.verts:
                hit = tree.find_nearest(v.co)
                dev = 0.0 if hit[1] is None else v.normal.angle(hit[1], 0.0)
                groove.append(min(1.0, dev / math.radians(50)))
            # 手鑿邊：圓角區沿法線做低頻起伏（底面與接口面不動），石塊輪廓不再像機切
            seed = Vector((self.rng.uniform(0, 50), self.rng.uniform(0, 50), self.rng.uniform(0, 50)))
            moves = []
            for v, e in zip(bm_block.verts, groove):
                if e < 0.05 or self._near_port(v.co, 0.03) or (v.co.z < 0.002 and v.normal.z < -0.3):
                    continue
                q = v.co * 11.0 + seed
                d = noise.noise(q) * 0.7 + noise.noise(q * 2.7) * 0.3
                moves.append((v, v.normal * (d * 0.006 * min(1.0, e * 2.0))))
            for v, mv in moves:
                v.co += mv
            # 崩角：以斜平面削掉角點，形成平整斷面（接口面附近不削）
            chipped = [0.0] * len(groove)
            verts = list(bm_block.verts)
            for c, n, dep in chips:
                pt = c - n * dep
                hit = [(i, (v.co - pt).dot(n)) for i, v in enumerate(verts)
                       if (v.co - pt).dot(n) > 0 and (v.co - c).length < 3.0 * dep]
                # 削到超過兩成頂點（小石塊）或碰到接口附近就放棄，避免摺疊與越界
                if len(hit) > 0.2 * len(verts) or any(self._near_port(verts[i].co, 0.03) for i, _ in hit):
                    continue
                for i, sd in hit:
                    verts[i].co -= n * sd
                    chipped[i] = 1.0
                    groove[i] *= 0.3
            ref.free()
        if jitter > 0 or wear > 0:
            for v in bm_block.verts:
                if self._on_port(v.co):
                    continue
                j = jitter + wear * 0.02
                v.co += Vector((self.rng.uniform(-j, j), self.rng.uniform(-j, j),
                                self.rng.uniform(-j, j) * 0.6))
        bmesh.ops.recalc_face_normals(bm_block, faces=bm_block.faces)
        bm_block.normal_update()
        vol = sum(f.calc_center_median().dot(f.normal) * f.calc_area() for f in bm_block.faces)
        if vol < 0:                                   # 重算偶爾整塊判反（崩角後），以有號體積校正為朝外
            bmesh.ops.reverse_faces(bm_block, faces=bm_block.faces)
        if mat == "ww_stone" and bm_block.verts:
            zmin = min(v.co.z for v in bm_block.verts)
            if zmin < 0.06 and self.rng.random() < 0.4 * self.props.get("moss", 1.0):
                mat = "ww_stone_moss"
        target = self.parts.setdefault(part, {}).setdefault(mat, bmesh.new())
        col = target.loops.layers.color.get("Col") or target.loops.layers.color.new("Col")
        tmp = bpy.data.meshes.new("_tmp")
        bm_block.to_mesh(tmp)
        bm_block.free()
        before = set(target.faces)
        nv0 = len(target.verts)
        target.from_mesh(tmp)
        target.verts.index_update()
        bpy.data.meshes.remove(tmp)
        col = target.loops.layers.color.get("Col")
        for f in target.faces:
            if f in before:
                continue
            f.material_index = 0
            for lp in f.loops:
                e = groove[lp.vert.index - nv0] if groove else 0.0
                r, g, bb = self._shade(lp.vert.co, f.normal, tint, mat, e)
                k = 1.0 - 0.42 * e ** 1.3                      # 凹縫壓暗（頂點色，引擎內同樣有效）
                if groove and chipped[lp.vert.index - nv0]:
                    k *= 1.07                                  # 崩口新鮮斷面略亮
                lp[col] = (r * k, g * k, bb * k, 1.0)

    def _on_port(self, co, tol=0.012):
        for p, n in self.port_planes:
            if abs((co.x - p[0]) * n[0] + (co.y - p[1]) * n[1]) < tol:
                return True
        return False

    def _near_port(self, co, dist=0.06):
        for p, n in self.port_planes:
            if abs((co.x - p[0]) * n[0] + (co.y - p[1]) * n[1]) < dist:
                return True
        return False

    def _shade(self, co, normal, tint, mat, crev=0.0):
        r, g, b = tint
        fn = self.props.get("shade_fn")
        if fn is not None:                         # 件自訂逐點明暗（S01 溪水深淺）
            k = fn(co, normal, mat)
            return (r * k[0], g * k[1], b * k[2])
        if mat not in ("ww_stone", "ww_stone_moss"):
            wl = self.props.get("wet_line")
            if mat in ("ww_soil", "ww_field_soil") and wl:
                # 田土濕線：水面以下壓暗，往上 5 cm 漸回乾土色
                t = max(0.0, min(1.0, (co.z - wl) / 0.05))
                k = 0.80 + 0.20 * t * t * (3 - 2 * t)
                return (r * k, g * k * 0.98, b * k * 0.95)
            return (r, g, b)
        # 青苔：低處、朝上面與陰濕處，接合面附近收斂
        n = noise.noise(Vector((co.x * 5.1 + 3.3, co.y * 5.1 - 1.7, co.z * 7.0)))
        n2 = noise.noise(Vector((co.x * 17.0, co.y * 17.0, co.z * 17.0)))
        low = max(0.0, 1.0 - (co.z + 0.05) / 0.35)
        up = max(0.0, normal.z) * 0.6
        m = max(0.0, n * 0.8 + n2 * 0.15 + low * 0.35 + up * 0.15 - 0.55) * 1.2
        if self._near_port(co):
            m *= 0.15
        # 縫苔：凹縫裡、偏低處與朝上的縫更容易長
        mask = noise.noise(Vector((co.x * 9.0 - 5.1, co.y * 9.0 + 2.2, co.z * 9.0)))
        m += crev ** 1.5 * max(0.0, mask + 0.35) * (0.5 + 0.5 * low + 0.3 * up)
        if self._near_port(co):
            m *= 0.4
        m = min(m, 0.6) * self.props.get("moss", 1.0)
        moss = (0.50, 0.64, 0.32)
        return (r * (1 - m) + moss[0] * m, g * (1 - m) + moss[1] * m, b * (1 - m) + moss[2] * m)

    def stone_tint(self, base=1.0):
        k = base * self.rng.uniform(0.86, 1.08)
        w = self.rng.uniform(-0.03, 0.03)
        return (k * (1 + w), k, k * (1 - w))

    # --- 基本體
    def strip_prism(self, part, mat, inner, outer, z0, z1, tint=None, **kw):
        """inner/outer：等長 2D 折線；z0/z1 可為常數或與點數相同的串列。"""
        bm = bmesh.new()
        n = len(inner)
        z0s = z0 if isinstance(z0, (list, tuple)) else [z0] * n
        z1s = z1 if isinstance(z1, (list, tuple)) else [z1] * n
        ring = []
        for i in range(n):
            a, b = inner[i], outer[i]
            ring.append([bm.verts.new((a[0], a[1], z0s[i])), bm.verts.new((b[0], b[1], z0s[i])),
                         bm.verts.new((b[0], b[1], z1s[i])), bm.verts.new((a[0], a[1], z1s[i]))])
        for i in range(n - 1):
            r0, r1 = ring[i], ring[i + 1]
            for k in range(4):
                bm.faces.new((r0[k], r0[(k + 1) % 4], r1[(k + 1) % 4], r1[k]))
        bm.faces.new(ring[0][::-1])
        bm.faces.new(ring[-1])
        self._merge(part, mat, bm, tint or self.stone_tint(), **kw)

    def poly_prism(self, part, mat, poly, z0, z1, tint=None, **kw):
        bm = bmesh.new()
        bot = [bm.verts.new((x, y, z0)) for x, y in poly]
        top = [bm.verts.new((x, y, z1)) for x, y in poly]
        area = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                   for i in range(len(poly)))
        if area < 0:
            bot, top = bot[::-1], top[::-1]
        bm.faces.new(bot[::-1])
        bm.faces.new(top)
        m = len(bot)
        for i in range(m):
            bm.faces.new((bot[i], bot[(i + 1) % m], top[(i + 1) % m], top[i]))
        self._merge(part, mat, bm, tint or self.stone_tint(), **kw)

    def poly_prism_z(self, part, mat, poly, z0, tops, tint=None, **kw):
        """底面平、頂面各頂點高度不同（斜撐、坡面、楔形石）。"""
        bm = bmesh.new()
        area = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                   for i in range(len(poly)))
        if area < 0:
            poly, tops = poly[::-1], tops[::-1]
        bot = [bm.verts.new((x, y, z0)) for x, y in poly]
        top = [bm.verts.new((x, y, t)) for (x, y), t in zip(poly, tops)]
        bm.faces.new(bot[::-1])
        f = bm.faces.new(top)
        m = len(bot)
        for i in range(m):
            bm.faces.new((bot[i], bot[(i + 1) % m], top[(i + 1) % m], top[i]))
        bmesh.ops.triangulate(bm, faces=[f])
        self._merge(part, mat, bm, tint or self.stone_tint(), **kw)

    def box(self, part, mat, center, size, rot=0.0, tint=None, **kw):
        cx, cy, cz = center
        sx, sy, sz = (s / 2 for s in size)
        c, s = math.cos(rot), math.sin(rot)
        poly = [(cx + x * c - y * s, cy + x * s + y * c)
                for x, y in ((-sx, -sy), (sx, -sy), (sx, sy), (-sx, sy))]
        self.poly_prism(part, mat, poly, cz - sz, cz + sz, tint=tint, **kw)

    def obox(self, part, mat, center, size, euler, tint=None, **kw):
        """任意角度的方塊（斜撐、木楔）。euler 為弧度 (x, y, z)。"""
        from mathutils import Euler
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        m = Matrix.Translation(center) @ Euler(euler).to_matrix().to_4x4() @ Matrix.Diagonal((*size, 1))
        bmesh.ops.transform(bm, matrix=m, verts=bm.verts)
        self._merge(part, mat, bm, tint or (1, 1, 1), **kw)

    def cylinder(self, part, mat, center, radius, depth, axis="Z", segs=12, tint=None, **kw):
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=radius, radius2=radius,
                              depth=depth)
        rot = {"Z": Matrix.Identity(4), "X": Matrix.Rotation(math.pi / 2, 4, "Y"),
               "Y": Matrix.Rotation(math.pi / 2, 4, "X")}[axis]
        bmesh.ops.transform(bm, matrix=Matrix.Translation(center) @ rot, verts=bm.verts)
        kw.setdefault("bevel", 0.0)
        kw.setdefault("jitter", 0.0)
        self._merge(part, mat, bm, tint or (1, 1, 1), **kw)

    def ring(self, part, mat, center, r_in, r_out, depth, axis="X", segs=24, tint=None, **kw):
        bm = bmesh.new()
        rings = []
        for k in range(segs):
            a = 2 * math.pi * k / segs
            ca, sa = math.cos(a), math.sin(a)
            rings.append([bm.verts.new((r * ca, r * sa, z)) for r, z in
                          ((r_in, -depth / 2), (r_out, -depth / 2), (r_out, depth / 2), (r_in, depth / 2))])
        for k in range(segs):
            r0, r1 = rings[k], rings[(k + 1) % segs]
            for q in range(4):
                bm.faces.new((r0[q], r1[q], r1[(q + 1) % 4], r0[(q + 1) % 4]))
        rot = {"Z": Matrix.Identity(4), "X": Matrix.Rotation(math.pi / 2, 4, "Y"),
               "Y": Matrix.Rotation(math.pi / 2, 4, "X")}[axis]
        bmesh.ops.transform(bm, matrix=Matrix.Translation(center) @ rot, verts=bm.verts)
        kw.setdefault("bevel", 0.0)
        kw.setdefault("jitter", 0.0)
        self._merge(part, mat, bm, tint or (1, 1, 1), **kw)

    # --- 接口與水
    def port(self, name, pos, direction, kind):
        """direction：水流離開本件的方向（入口則為進入方向的反向，即朝外）。"""
        self.ports.append(dict(name=name, pos=[round(pos[0], 4), round(pos[1], 4), 0.0],
                               dir=[int(round(direction[0])), int(round(direction[1]))], kind=kind))
        self.port_planes.append(((pos[0], pos[1]), direction))

    def flow(self, name, path, z0=WATER_Z, z1=None, width=CLEAR_W - 0.01, frm="in", to=None):
        self.flows.append(dict(name=name, path=[list(map(lambda v: round(v, 4), p)) for p in path],
                               z0=z0, z1=z0 if z1 is None else z1, width=width, frm=frm, to=to))

    def socket(self, name, pos, rot=(0, 0, 0)):
        self.sockets.append(dict(name=name, pos=list(pos), rot=list(rot)))


# ---------------------------------------------------------------- trough kit

def course_breaks(length, rng, lo=0.22, hi=0.48, offset=0.0):
    """沿長度切石塊的位置（含頭尾），offset 讓上下層錯縫。"""
    cuts = [0.0]
    s = offset if offset > 0.05 else 0.0
    if s > 0:
        cuts.append(s)
    while True:
        s += rng.uniform(lo, hi)
        if s >= length - lo * 0.6:
            break
        cuts.append(s)
    cuts.append(length)
    return cuts


def wall_run(b, path, off_in, off_out, z0=0.0, z1=TOTAL_H, courses=2, part="body",
             height_fn=None, wear=0.0, lo=0.22, hi=0.48, tint_k=1.0, bevel=0.01):
    """沿 path 的一道牆：off_in/off_out 為相對中心線的左右偏移。

    height_fn(s) 可改變牆頂高度（磨損缺口、坡度），但接口兩端保持標準高度。
    """
    L = cumlen(path)[-1]
    zs = [z0 + (z1 - z0) * k / courses for k in range(courses + 1)]
    for c in range(courses):
        cuts = course_breaks(L, b.rng, lo, hi, offset=(b.rng.uniform(0.1, 0.2) if c % 2 else 0.0))
        for s0, s1 in zip(cuts, cuts[1:]):
            st = subpath(path, s0, s1)
            inner, outer = offset_pts(st, off_in), offset_pts(st, off_out)
            if height_fn is None:
                top = zs[c + 1]
                bot = zs[c]
                b.strip_prism(part, "ww_stone", inner, outer, bot, top,
                              tint=b.stone_tint(tint_k), wear=wear, bevel=bevel)
            else:
                ss = [s0 + (s1 - s0) * i / (len(st) - 1) for i in range(len(st))]
                tops = [min(zs[c + 1], height_fn(s)) for s in ss]
                bots = [zs[c]] * len(st)
                if max(tops) - zs[c] < 0.03:
                    continue
                tops = [max(t, zs[c] + 0.03) for t in tops]
                b.strip_prism(part, "ww_stone", inner, outer, bots, tops,
                              tint=b.stone_tint(tint_k), wear=wear, bevel=bevel)


def floor_run(b, path, half=CLEAR_W / 2, z0=0.0, z1=FLOOR_T, part="body", lo=0.3, hi=0.55,
              split_width=False, z_fn=None):
    L = cumlen(path)[-1]
    cuts = course_breaks(L, b.rng, lo, hi)
    for s0, s1 in zip(cuts, cuts[1:]):
        st = subpath(path, s0, s1)
        tops = z1 if z_fn is None else [z_fn(s0 + (s1 - s0) * i / (len(st) - 1)) for i in range(len(st))]
        if split_width:
            for a, c in ((-half, 0.0), (0.0, half)):
                b.strip_prism(part, "ww_stone", offset_pts(st, a), offset_pts(st, c), z0, tops,
                              tint=b.stone_tint(0.97), bevel=0.006)
        else:
            b.strip_prism(part, "ww_stone", offset_pts(st, -half), offset_pts(st, half), z0, tops,
                          tint=b.stone_tint(0.97), bevel=0.006)


def channel(b, path, walls=("L", "R"), **kw):
    """標準 U 形石槽：底板＋左右牆。"""
    floor_run(b, path, split_width=kw.pop("split_floor", False), z_fn=kw.pop("floor_fn", None))
    h_l = kw.pop("height_l", None)
    h_r = kw.pop("height_r", None)
    if "L" in walls:
        wall_run(b, path, CLEAR_W / 2, OUTER_W / 2, height_fn=h_l, **kw)
    if "R" in walls:
        wall_run(b, path, -OUTER_W / 2, -CLEAR_W / 2, height_fn=h_r, **kw)


def clamp_band(b, p, d, z_top=TOTAL_H, part="body", width=0.05, drop=0.16, side="both",
               rivets=True):
    """跨在牆頂的青銅箍：沿切線 d 位於 p 點，包住左右牆外側。"""
    nx, ny = -d[1], d[0]
    rot = math.atan2(d[1], d[0])
    for sgn in ((1, -1) if side == "both" else ((1,) if side == "L" else (-1,))):
        cx = p[0] + nx * sgn * (OUTER_W / 2 - WALL_T / 2)
        cy = p[1] + ny * sgn * (OUTER_W / 2 - WALL_T / 2)
        b.box(part, "ww_bronze", (cx, cy, z_top + 0.006), (width, WALL_T + 0.02, 0.012), rot=rot,
              tint=(1, 1, 1), bevel=0.002, jitter=0)
        ox = p[0] + nx * sgn * (OUTER_W / 2 + 0.006)
        oy = p[1] + ny * sgn * (OUTER_W / 2 + 0.006)
        b.box(part, "ww_bronze", (ox, oy, z_top - drop / 2 + 0.006), (width, 0.012, drop + 0.012), rot=rot,
              tint=(1, 1, 1), bevel=0.002, jitter=0)
        if rivets:
            for dz in (0.035, drop - 0.03):
                rx = p[0] + nx * sgn * (OUTER_W / 2 + 0.014)
                ry = p[1] + ny * sgn * (OUTER_W / 2 + 0.014)
                b.cylinder(part, "ww_bronze", Vector((rx, ry, z_top - dz)), 0.009, 0.012,
                           axis="X" if abs(nx) > 0.5 else "Y", segs=8)


# ---------------------------------------------------------------- objects

def build_objects(b, collection):
    """把 Builder 內容轉成 Blender 物件，回傳 {部件: 物件}。"""
    objs = {}
    for part, mats in b.parts.items():
        merged = bmesh.new()
        col = merged.loops.layers.color.new("Col")
        mat_names = list(mats.keys())
        for mi, m in enumerate(mat_names):
            src = mats[m]
            tmp = bpy.data.meshes.new("_t")
            src.to_mesh(tmp)
            src.free()
            before = set(merged.faces)
            merged.from_mesh(tmp)
            bpy.data.meshes.remove(tmp)
            for f in merged.faces:
                if f not in before:
                    f.material_index = mi
        mesh = bpy.data.meshes.new(f"{b.id}_{part}")
        merged.to_mesh(mesh)
        merged.free()
        box_uv(mesh, fn=b.props.get("uv_fn"))
        imgs = {k: bpy.data.images.get(k) for k in ("ww_stone", "ww_stone_moss", "ww_stone_n", "ww_wood",
                                                    "ww_bronze", "ww_soil", "ww_field_soil",
                                                    "ww_field_soil_n", "ww_stream", "ww_stream_n",
                                                    "ww_riverbed", "ww_riverbed_n")}
        for m in mat_names:
            mesh.materials.append(get_material(m, {k: v for k, v in imgs.items() if v}))
        mesh.color_attributes.active_color_name = "Col"
        mesh.shade_smooth()
        mesh.set_sharp_from_angle(angle=math.radians(38))
        name = b.id if part == "body" else f"{b.id}_{part}"
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)
        objs[part] = obj
    return objs


def box_uv(mesh, scale=2.4, fn=None):
    uv = mesh.uv_layers.new(name="UVMap")
    if fn is not None:                             # 件自訂 UV（S01：U 橫越水面、V 沿流向，可捲動做流動）
        per_v = [fn(v.co) for v in mesh.vertices]
        for li, lp in enumerate(mesh.loops):
            uv.data[li].uv = per_v[lp.vertex_index]
        return
    for poly in mesh.polygons:
        n = poly.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for li in poly.loop_indices:
            co = mesh.vertices[mesh.loops[li].vertex_index].co
            if ax == 2:
                u, v = co.x, co.y
            elif ax == 0:
                u, v = co.y, co.z
            else:
                u, v = co.x, co.z
            uv.data[li].uv = (u * scale, v * scale)


def water_objects(b, collection):
    """水面為獨立網格：沿流路的帶狀面，UV 的 U 橫跨 0–1、V 為沿流向距離（m，往下游遞增，Unity 流動著色器依此捲動）；
    靜水面（water_polys）UV = 平面 x、y（m），材質 ww_water_still。"""
    objs = []
    mat = get_material("ww_water", {})
    for i, fl in enumerate(b.flows):
        path = [tuple(p) for p in fl["path"]]
        s = cumlen(path)
        L = s[-1]
        st = subpath(path, 0, L, step=0.05)
        bm = bmesh.new()
        uvl = bm.loops.layers.uv.new("UVMap")
        lift = 0.002 * i
        prev = None
        for k, (p, d) in enumerate(st):
            t = k / (len(st) - 1)
            z = fl["z0"] + (fl["z1"] - fl["z0"]) * t + lift
            l = offset_pts([(p, d)], fl["width"] / 2)[0]
            r = offset_pts([(p, d)], -fl["width"] / 2)[0]
            cur = (bm.verts.new((r[0], r[1], z)), bm.verts.new((l[0], l[1], z)), t * L)
            if prev:
                f = bm.faces.new((prev[0], cur[0], cur[1], prev[1]))
                for lp, uvv in zip(f.loops, ((0, prev[2]), (0, cur[2]), (1, cur[2]), (1, prev[2]))):
                    lp[uvl].uv = uvv
            prev = cur
        mesh = bpy.data.meshes.new(f"WATER_{b.id}_{fl['name']}")
        bm.to_mesh(mesh)
        bm.free()
        mesh.materials.append(mat)
        obj = bpy.data.objects.new(f"WATER_{b.id}_{fl['name']}", mesh)
        obj["flow_to"] = fl["to"] or ""
        collection.objects.link(obj)
        objs.append(obj)
    for wp in b.water_polys:
        bm = bmesh.new()
        vs = [bm.verts.new((x, y, wp["z"])) for x, y in wp["poly"]]
        bm.faces.new(vs)
        uvl = bm.loops.layers.uv.new("UVMap")
        for f in bm.faces:
            for lp in f.loops:
                lp[uvl].uv = (lp.vert.co.x, lp.vert.co.y)
        mesh = bpy.data.meshes.new(f"WATER_{b.id}_{wp['name']}")
        bm.to_mesh(mesh)
        bm.free()
        mesh.materials.append(get_material("ww_water_still", {}))
        obj = bpy.data.objects.new(f"WATER_{b.id}_{wp['name']}", mesh)
        collection.objects.link(obj)
        objs.append(obj)
    return objs


def socket_empties(b, collection, parent):
    out = []
    for p in b.ports:
        e = bpy.data.objects.new(f"SOCKET_{p['name']}", None)
        e.empty_display_type = "SINGLE_ARROW"
        e.empty_display_size = 0.2
        e.location = (p["pos"][0], p["pos"][1], WATER_Z)
        # 箭頭（局部 Z）指向接口朝外方向
        e.rotation_euler = Vector((p["dir"][0], p["dir"][1], 0)).to_track_quat("Z", "Y").to_euler()
        e["kind"] = p["kind"]
        e.parent = parent
        collection.objects.link(e)
        out.append(e)
    for s in b.sockets:
        e = bpy.data.objects.new(f"SOCKET_{s['name']}", None)
        e.empty_display_type = "ARROWS"
        e.empty_display_size = 0.12
        e.location = s["pos"]
        e.rotation_euler = s["rot"]
        e.parent = parent
        collection.objects.link(e)
        out.append(e)
    return out


def footprint_cells(objs, cell=GRID):
    """以 0.25 m 格估計占地（三角形投影覆蓋格心），供玩法碰撞用。"""
    tris = []
    for o in objs:
        me = o.data
        me.calc_loop_triangles()
        mw = o.matrix_world
        vs = [mw @ v.co for v in me.vertices]
        for t in me.loop_triangles:
            a, b_, c = (vs[i] for i in t.vertices)
            if max(a.z, b_.z, c.z) < 0.0:
                continue
            tris.append(((a.x, a.y), (b_.x, b_.y), (c.x, c.y)))
    if not tris:
        return []
    xs = [p[0] for t in tris for p in t]
    ys = [p[1] for t in tris for p in t]
    cells = set()
    i0, i1 = math.floor(min(xs) / cell), math.ceil(max(xs) / cell)
    j0, j1 = math.floor(min(ys) / cell), math.ceil(max(ys) / cell)

    def inside(px, py, t):
        (x1, y1), (x2, y2), (x3, y3) = t
        d1 = (px - x2) * (y1 - y2) - (x1 - x2) * (py - y2)
        d2 = (px - x3) * (y2 - y3) - (x2 - x3) * (py - y3)
        d3 = (px - x1) * (y3 - y1) - (x3 - x1) * (py - y1)
        neg = d1 < 0 or d2 < 0 or d3 < 0
        pos = d1 > 0 or d2 > 0 or d3 > 0
        return not (neg and pos)

    for i in range(i0, i1):
        for j in range(j0, j1):
            px, py = (i + 0.5) * cell, (j + 0.5) * cell
            for t in tris:
                if min(p[0] for p in t) > px or max(p[0] for p in t) < px:
                    continue
                if min(p[1] for p in t) > py or max(p[1] for p in t) < py:
                    continue
                if inside(px, py, t):
                    cells.add((i, j))
                    break
    return sorted([list(c) for c in cells])


def mesh_stats(objs):
    tris = verts = 0
    mats = set()
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for o in objs:
        me = o.data
        me.calc_loop_triangles()
        tris += len(me.loop_triangles)
        verts += len(me.vertices)
        mats |= {m.name for m in me.materials if m}
        for v in me.vertices:
            co = o.matrix_world @ v.co
            lo = Vector(map(min, lo, co))
            hi = Vector(map(max, hi, co))
    return dict(tris=tris, verts=verts, materials=sorted(mats),
                bbox_min=[round(x, 4) for x in lo], bbox_max=[round(x, 4) for x in hi],
                size=[round(h - l, 4) for h, l in zip(hi, lo)])


def qa_mesh(obj):
    """封閉性、退化面、法線、浮件（各島的最低點需接地或落在其他島上）。"""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)
    nonmanifold = sum(1 for e in bm.edges if not e.is_manifold)
    degenerate = sum(1 for f in bm.faces if f.calc_area() < 1e-8)
    # 島
    islands = []
    seen = set()
    for f in bm.faces:
        if f.index in seen:
            continue
        stack = [f]
        isl = []
        seen.add(f.index)
        while stack:
            cur = stack.pop()
            isl.append(cur)
            for e in cur.edges:
                for g in e.link_faces:
                    if g.index not in seen:
                        seen.add(g.index)
                        stack.append(g)
        islands.append(isl)
    boxes = []
    inward = 0
    for isl in islands:
        vs = {v for f in isl for v in f.verts}
        lo = Vector((min(v.co.x for v in vs), min(v.co.y for v in vs), min(v.co.z for v in vs)))
        hi = Vector((max(v.co.x for v in vs), max(v.co.y for v in vs), max(v.co.z for v in vs)))
        boxes.append((lo, hi))
        # 符號體積 < 0 表示法線朝內
        vol = sum(f.calc_center_median().dot(f.normal) * f.calc_area() for f in isl) / 3
        if vol < 0:
            inward += 1
    ground = min(bx[0].z for bx in boxes) if boxes else 0
    floating = 0
    for i, (lo, hi) in enumerate(boxes):
        if lo.z <= max(ground, 0.0) + 0.012:
            continue
        supported = False
        for j, (lo2, hi2) in enumerate(boxes):
            if i == j:
                continue
            if lo2.x - 0.02 <= hi.x and hi2.x + 0.02 >= lo.x and lo2.y - 0.02 <= hi.y and hi2.y + 0.02 >= lo.y \
                    and lo2.z - 0.02 <= lo.z <= hi2.z + 0.025:
                supported = True
                break
        if not supported:
            floating += 1
    bm.free()
    return dict(islands=len(islands), nonmanifold_edges=nonmanifold, degenerate_faces=degenerate,
                inward_islands=inward, floating_islands=floating)


def ensure_dirs(*paths):
    for p in paths:
        os.makedirs(p, exist_ok=True)


def write_json(path, data):
    ensure_dirs(os.path.dirname(path))
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
