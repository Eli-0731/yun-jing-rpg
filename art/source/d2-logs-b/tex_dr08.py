# DR08 長滿蕈和苔的朽木：手繪平鋪貼圖的後製（Codex 依 D2 設定圖 V6 畫的原圖在 tex_src_dr08/，提示詞 prompt.txt）。
#   1. 六張表面貼圖（苔、樹皮、褐腐木、撕裂纖維、樹洞內壁、土）：Codex 畫的四邊接不起來 → 先左右、再上下各做一次
#      「捲半圈 + 中間帶狀遮罩」的無縫處理（遮罩加一點雜訊，交界不是一條直線），縮成 1024；
#      法線由明暗推高度（扣掉大範圍模糊，只留中小起伏），用 FFT 做循環的模糊、np.roll 做循環的斜率，邊上也接得起來。
#   2. 植物圖集 DR08_Plants（2048，RGBA，alpha 裁切）：左半層狀菌蓋、右半 Codex 的植物圖（蕨、小蕈、發光小蕈、小苗、落葉、垂苔）。
#      洋紅底去背、去掉葉緣的洋紅邊、透明處往外補色（縮圖時不會滲出洋紅），每一件的框寫進 DR08_Plants_rects.json。
# 用法：uv run --no-project --offline --with pillow --with numpy python tex_dr08.py
import json, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'tex_src_dr08')
OUT = os.path.join(HERE, '..', '..', 'exports', 'd2-logs-b', 'DR08_Shared', 'Textures')
N = 1024
# 每層：原圖、色調（乘、飽和度）、法線強度、說明
LAYERS = {
    'Bark':  ('tex_bark.png',  1.00, 1.00, 5.0),
    'Moss':  ('tex_moss.png',  .78,  .80,  4.0),     # Codex 的苔偏黃亮，設定圖 V6 是深橄欖
    'Rot':   ('tex_rot.png',   .92,  .95,  6.0),
    'Fibre': ('tex_fibre.png', .95,  .95,  5.0),
    'Inner': ('tex_inner.png', .85,  .95,  5.0),
    'Soil':  ('tex_soil.png',  .90,  .90,  3.5),
}


def load(name):
    return np.asarray(Image.open(os.path.join(SRC, name)).convert('RGB'), np.float64) / 255.0


def save(a, name, mode='RGB'):
    os.makedirs(OUT, exist_ok=True)
    im = Image.fromarray(np.clip(np.round(a * 255), 0, 255).astype(np.uint8), mode)
    im.save(os.path.join(OUT, name), optimize=True)
    print('saved', name, im.size)


def fft_blur(a, sigma):
    """循環（邊接邊）的高斯模糊；a 是 (H, W) 或 (H, W, C)。"""
    h, w = a.shape[:2]
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    g = np.exp(-2 * (np.pi * sigma) ** 2 * (fx * fx + fy * fy))
    if a.ndim == 2:
        return np.real(np.fft.ifft2(np.fft.fft2(a) * g))
    return np.stack([np.real(np.fft.ifft2(np.fft.fft2(a[..., c]) * g)) for c in range(a.shape[2])], -1)


def seam_pass(img, axis, rs):
    """沿 axis 做一次無縫：捲半圈的那張在兩邊、原圖在中間，中間帶狀遮罩加雜訊。"""
    n = img.shape[axis]
    rolled = np.roll(img, n // 2, axis=axis)
    x = (np.arange(n) + .5) / n
    d = np.abs(x - .5)                                   # 離中線（原圖的中間）多遠：0..0.5
    other = img.shape[1 - axis]
    noise = fft_blur(rs.randn(n, other) if axis == 0 else rs.randn(other, n), 18)
    noise = noise / (np.abs(noise).max() + 1e-9) * .06
    dd = (d[:, None] if axis == 0 else d[None, :]) + noise
    w = np.clip((.40 - dd) / .12, 0, 1)                  # 中間 0.56 寬是原圖（中線＝捲過那張的接縫，完全蓋掉）、兩邊 0.1 是捲過的那張
    w = w * w * (3 - 2 * w)
    return img * w[..., None] + rolled * (1 - w[..., None])


def make_seamless(img, seed):
    rs = np.random.RandomState(seed)
    img = seam_pass(img, 1, rs)
    img = seam_pass(img, 0, rs)
    return img


def resize(a, n, mode='RGB'):
    im = Image.fromarray(np.clip(np.round(a * 255), 0, 255).astype(np.uint8), mode)
    return np.asarray(im.resize((n, n), Image.LANCZOS), np.float64) / 255.0


def tone(a, mul, sat):
    g = (a * np.array((.30, .59, .11))).sum(-1, keepdims=True)
    return np.clip((g + (a - g) * sat) * mul, 0, 1)


def normal_from(a, strength):
    lum = (a ** 2.2 * np.array((.30, .59, .11))).sum(-1)
    h = lum - fft_blur(lum, 40)                          # 只留中小起伏（大範圍的明暗是畫上去的光影，不是高低）
    h = h - .5 * (h - fft_blur(h, 1.2))                  # 最細的雜點壓一半
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * .5
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * .5
    nx, ny = -gx * strength * 8, gy * strength * 8       # 圖片列往下＝UV 的 v 往下：綠色反向（OpenGL 法線，Unity 用的）
    nz = np.ones_like(nx)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / ln, ny / ln, nz / ln], -1) * .5 + .5


def key_magenta(a):
    """洋紅底去背：alpha、去洋紅邊。a：(H, W, 3) 0..1。"""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mag = np.minimum(r, b) - g                           # 洋紅程度
    alpha = np.clip((.55 - mag) / .30, 0, 1)
    sp = np.clip(np.minimum(r, b) - g * .90, 0, None)    # 去洋紅：紅、藍都比綠（略打折）高的部分扣掉（葉緣、垂苔原本一圈粉紅）
    out = a.copy()
    out[..., 0] -= sp
    out[..., 2] -= sp
    return np.clip(out, 0, 1), alpha


def bleed(rgb, alpha, it=24):
    """透明處往外補色（縮圖時不會滲出底色）。"""
    rgb = rgb.copy()
    known = alpha > .5
    for _ in range(it):
        acc = np.zeros_like(rgb)
        cnt = np.zeros(alpha.shape)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            k = np.roll(known, (dy, dx), (0, 1))
            acc += np.roll(rgb, (dy, dx), (0, 1)) * k[..., None]
            cnt += k
        new = (~known) & (cnt > 0)
        rgb[new] = acc[new] / cnt[new][:, None]
        known = known | new
    return rgb


def components(mask, step=4):
    """粗格上找連通塊，回傳每塊的框（原圖像素）。"""
    m = mask[::step, ::step]
    lab = np.zeros(m.shape, np.int32)
    boxes = []
    for y0, x0 in zip(*np.nonzero(m)):
        if lab[y0, x0]:
            continue
        k = len(boxes) + 1
        st = [(y0, x0)]
        lab[y0, x0] = k
        ys, xs = [], []
        while st:
            y, x = st.pop()
            ys.append(y)
            xs.append(x)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < m.shape[0] and 0 <= xx < m.shape[1] and m[yy, xx] and not lab[yy, xx]:
                        lab[yy, xx] = k
                        st.append((yy, xx))
        if len(ys) * step * step > 900:
            boxes.append((min(xs) * step, min(ys) * step, (max(xs) + 1) * step, (max(ys) + 1) * step))
    return boxes


def largest(mask):
    """只留最大的連通塊（8 鄰接），回傳 0/1 浮點遮罩；邊上外擴 2 px 保住半透明的邊。"""
    lab = np.zeros(mask.shape, np.int32)
    best, bk = 0, 0
    k = 0
    for y0, x0 in zip(*np.nonzero(mask)):
        if lab[y0, x0]:
            continue
        k += 1
        st, n = [(y0, x0)], 0
        lab[y0, x0] = k
        while st:
            y, x = st.pop()
            n += 1
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < mask.shape[0] and 0 <= xx < mask.shape[1] and mask[yy, xx] and not lab[yy, xx]:
                        lab[yy, xx] = k
                        st.append((yy, xx))
        if n > best:
            best, bk = n, k
    keep = lab == bk
    for _ in range(2):
        keep = keep | np.roll(keep, 1, 0) | np.roll(keep, -1, 0) | np.roll(keep, 1, 1) | np.roll(keep, -1, 1)
    return keep.astype(np.float64)


def plants():
    S = 2048
    atlas = np.zeros((S, S, 3))
    alpha = np.zeros((S, S))
    rects = []
    # 左半：層狀菌蓋（直邊在下＝長在樹幹上的那邊）
    f = load('tex_fungus.png')
    frgb, fa = key_magenta(f)
    ys, xs = np.nonzero(fa > .5)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    crop = np.concatenate([frgb[y0:y1, x0:x1], fa[y0:y1, x0:x1, None]], -1)
    h, w = crop.shape[:2]
    sc = min((S // 2 - 24) / w, (S // 2 - 24) / h)
    im = Image.fromarray(np.round(crop * 255).astype(np.uint8), 'RGBA').resize((int(w * sc), int(h * sc)), Image.LANCZOS)
    c = np.asarray(im, np.float64) / 255.0
    c[..., :3] = tone(c[..., :3], .80, .78)                 # Unity 打光下原圖的橘色、奶油邊太亮太艷（像塑膠），壓暗、降飽和
    ox, oy = 12, 12
    atlas[oy:oy + c.shape[0], ox:ox + c.shape[1]] = c[..., :3]
    alpha[oy:oy + c.shape[0], ox:ox + c.shape[1]] = c[..., 3]
    rects.append({'cat': 'fungus', 'px': [ox, oy, ox + c.shape[1], oy + c.shape[0]]})
    # 右半：植物圖
    p = load('sheet_plants.png')
    prgb, pa = key_magenta(p)
    boxes = components(pa > .5)
    # 照 Codex 排的列分類：上→下 蕨、褐小蕈、發光小蕈＋小苗、落葉、垂苔
    boxes.sort(key=lambda b: (b[1] + b[3]) / 2)
    rows = []
    for b in boxes:
        cy = (b[1] + b[3]) / 2
        if rows and abs(cy - rows[-1][0]) < p.shape[0] * .07:
            rows[-1][1].append(b)
            rows[-1][0] = np.mean([(q[1] + q[3]) / 2 for q in rows[-1][1]])
        else:
            rows.append([cy, [b]])
    cats = ['fern', 'mush', 'row3', 'leaf', 'mossdrape']
    print('plant rows', [len(r[1]) for r in rows])
    items = []
    for ri, (cy, bs) in enumerate(rows):
        bs.sort(key=lambda b: b[0])
        for b in bs:
            cat = cats[ri] if ri < len(cats) else 'other'
            if cat == 'row3':                            # 第三列：左邊兩叢發光小蕈、右邊兩株小苗（看顏色：發光的偏青）
                reg = prgb[b[1]:b[3], b[0]:b[2]][pa[b[1]:b[3], b[0]:b[2]] > .5]
                cat = 'glow' if reg[:, 2].mean() > reg[:, 1].mean() * .80 else 'sapling'          # 發光小蕈偏青（藍接近綠），小苗藍很低
            m = 6
            x0, y0 = max(0, b[0] - m), max(0, b[1] - m)
            x1, y1 = min(p.shape[1], b[2] + m), min(p.shape[0], b[3] + m)
            ca = pa[y0:y1, x0:x1] * largest(pa[y0:y1, x0:x1] > .05)          # 框裡夾到的隔壁碎片拿掉
            items.append((cat, np.concatenate([prgb[y0:y1, x0:x1], ca[..., None]], -1)))
    # 逐件排進右半（x 1024–2048 全高）＋左下（x 0–1024、y 1024–2048）：一列列往下排，放得下就盡量放大
    regions = [(S // 2, 0, S, S), (0, S // 2, S // 2, S)]
    items.sort(key=lambda it: -it[1].shape[0])

    def pack(k):
        out, ri, x, y, rowh = [], 0, regions[0][0], regions[0][1], 0
        for cat, c in items:
            w, h = int(c.shape[1] * k), int(c.shape[0] * k)
            while True:
                rx0, ry0, rx1, ry1 = regions[ri]
                if x + w > rx1:
                    x, y, rowh = rx0, y + rowh + 8, 0
                if y + h <= ry1 and x + w <= rx1:
                    break
                ri += 1
                if ri >= len(regions):
                    return None
                x, y, rowh = regions[ri][0], regions[ri][1], 0
            out.append((cat, c, x, y, w, h))
            x += w + 8
            rowh = max(rowh, h)
        return out
    k = 4.0
    while pack(k) is None:
        k *= .95
    print('plant scale', round(k, 2))
    for cat, c, x, y, w, h in pack(k):
        im = Image.fromarray(np.round(c * 255).astype(np.uint8), 'RGBA').resize((w, h), Image.LANCZOS)
        cc = np.asarray(im, np.float64) / 255.0
        atlas[y:y + h, x:x + w] = cc[..., :3]
        alpha[y:y + h, x:x + w] = cc[..., 3]
        rects.append({'cat': cat, 'px': [x, y, x + w, y + h]})
    rgb = bleed(atlas, alpha)
    rgba = np.concatenate([rgb, alpha[..., None]], -1)
    save(rgba, 'DR08_Plants_Albedo.png', 'RGBA')
    for r in rects:                                      # 像素框 → UV（v 往上）
        x0, y0, x1, y1 = r['px']
        r['uv'] = [x0 / S, 1 - y1 / S, x1 / S, 1 - y0 / S]
    json.dump({'size': S, 'rects': rects}, open(os.path.join(OUT, 'DR08_Plants_rects.json'), 'w'), indent=1)
    print('rects', {c: sum(1 for r in rects if r['cat'] == c) for c in set(r['cat'] for r in rects)})


def surfaces():
    for i, (nm, (fn, mul, sat, ns)) in enumerate(LAYERS.items()):
        a = load(fn)
        a = make_seamless(a, 11 + i)
        a = resize(a, N)
        a = tone(a, mul, sat)
        save(a, f'DR08_{nm}_Albedo.png')
        save(normal_from(a, ns), f'DR08_{nm}_Normal.png')
        # 2×2 平鋪檢查圖（不交付）
        t = np.tile(a[::2, ::2], (2, 2, 1))
        os.makedirs(os.path.join(HERE, '..', '..', '..', '..', 'yun-jing-cache', 'dr08-work'), exist_ok=True)
        Image.fromarray(np.round(t * 255).astype(np.uint8)).save(f'D:/yun-jing-cache/dr08-work/tile_{nm}.jpg', quality=88)


if __name__ == '__main__':
    if 'plants' not in sys.argv:
        surfaces()
    plants()
