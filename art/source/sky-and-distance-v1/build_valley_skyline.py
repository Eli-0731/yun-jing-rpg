"""將兩段不透明山景合成四片可閉合的 4096×1024 遠景貼圖。"""
from __future__ import annotations
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

W, H, SEG_W = 4096, 1024, 2560
FOG = np.array((169, 184, 196), dtype=np.float32)
SRC = Path(__file__).resolve().parent / "SK"
OUT = Path(__file__).resolve().parents[2] / "exports" / "sky-and-distance-v1" / "SK"
OUT.mkdir(parents=True, exist_ok=True)


def smooth(a: float, b: float, v: np.ndarray) -> np.ndarray:
    t = np.clip((v - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def segment(name: str, offset: int) -> np.ndarray:
    image = Image.open(SRC / name).convert("RGB").resize((SEG_W, 853), Image.Resampling.LANCZOS)
    src = np.asarray(image, dtype=np.float32)
    base = np.broadcast_to(FOG, (H, SEG_W, 3)).copy()
    end = min(H, offset + 853)
    base[offset:end] = src[:end-offset]
    y = np.arange(H, dtype=np.float32)
    top_weight = smooth(offset, offset + 110, y)
    # 下緣完全回到霧色，供天空弧面底部自然融入場景。
    foot_weight = 1 - smooth(880, H - 1, y)
    weight = (top_weight * foot_weight)[:, None, None]
    return base * weight + FOG * (1 - weight)


def make_ring(name: str, offset: int) -> Image.Image:
    first = segment(f"{name}-a.png", offset)
    second = segment(f"{name}-b.png", offset)
    x = np.arange(W)
    a_index = np.clip((x + 256) % W, 0, SEG_W - 1)
    b_index = np.clip(np.where(x < 256, x + 2304, x - 1792), 0, SEG_W - 1)
    wa = np.zeros(W, dtype=np.float32)
    wa[:256] = 0.5 + 0.5 * smooth(0, 256, x[:256])
    wa[256:1792] = 1
    wa[1792:2304] = 1 - smooth(1792, 2304, x[1792:2304])
    wa[3840:] = 0.5 * smooth(3840, 4096, x[3840:])
    result = first[:, a_index, :] * wa[None, :, None] + second[:, b_index, :] * (1 - wa[None, :, None])
    result[0, :, :] = FOG
    result[-1, :, :] = FOG
    result[:, -1, :] = result[:, 0, :]
    img = Image.fromarray(np.uint8(np.clip(result, 0, 255)), "RGB")
    img.save(OUT / f"{name}.png", optimize=True)
    for q in range(4):
        img.crop((q * 1024, 0, (q + 1) * 1024, H)).save(OUT / f"{name}_q{q}.png", optimize=True)
    preview(name, img)
    seams(name, img)
    return img


def preview(name: str, img: Image.Image) -> None:
    # 以完整天空畫布示範一個觀看方向，不冒稱 Unity 截圖。
    canvas = Image.new("RGB", (1920, 1080), tuple(FOG.astype(int)))
    band = img.resize((1920, 550), Image.Resampling.LANCZOS)
    canvas.paste(band, (0, 530))
    canvas.save(OUT / f"{name}_sky-preview.png", optimize=True)


def seams(name: str, img: Image.Image) -> None:
    # 上半為四個 90° 象限相接；下半放大三個象限接點及首尾閉合處。
    canvas = Image.new("RGB", (W, 1280), (226, 230, 232))
    canvas.paste(img, (0, 24))
    draw = ImageDraw.Draw(canvas)
    arr = np.asarray(img)
    for q, x in enumerate((1024, 2048, 3072, 4096)):
        draw.line((x % W, 0, x % W, 20), fill=(132, 91, 89), width=2)
        ix = np.array([(x - 256 + j) % W for j in range(512)])
        detail = Image.fromarray(arr[440:568, ix, :]).resize((1024, 232), Image.Resampling.NEAREST)
        canvas.paste(detail, (q * 1024, 1048))
        draw.line((q * 1024 + 512, 1048, q * 1024 + 512, 1279), fill=(132, 91, 89), width=2)
    canvas.save(OUT / f"{name}_seam-check.png", optimize=True)


def main() -> None:
    for name, offset in (("SK01", 110), ("SK02", 160), ("SK03", 210)):
        img = make_ring(name, offset)
        a = np.asarray(img, dtype=np.int16)
        diff = np.abs(a[:, 0, :] - a[:, -1, :])
        print(f"{name}: {img.width}x{img.height}, 首尾最大色差 {diff.max()}, 平均 {diff.mean():.3f}")


if __name__ == "__main__":
    main()
