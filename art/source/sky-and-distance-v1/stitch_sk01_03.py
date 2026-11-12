"""從兩張不透明 AI 山景拼成四片 90° 弧面的週期貼圖。"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

SRC = Path(__file__).resolve().parent
OUT = SRC.parents[1] / "exports" / "sky-and-distance-v1" / "SK"
OUT.mkdir(parents=True, exist_ok=True)
W, H = 4096, 1024
TOP = np.array([143, 162, 177], dtype=np.float32)
FOG = np.array([169, 184, 196], dtype=np.float32)
sky = TOP[None, :] + (FOG - TOP)[None, :] * np.linspace(0, 1, H)[:, None] ** 0.85
sky = np.repeat(sky[:, None, :], W, axis=1)


def panel(path):
    img = Image.open(path).convert("RGB")
    # 上下增補同色天空與霧，再縮為 2048×1024，避免把原 3:1 山體拉高。
    top = np.asarray(img)[0, :, :].mean(axis=0).astype(np.uint8)
    bottom = np.asarray(img)[-1, :, :].mean(axis=0).astype(np.uint8)
    padded = Image.new("RGB", (img.width, 1086))
    padded.paste(Image.new("RGB", (img.width, 181), tuple(top)), (0, 0))
    padded.paste(img, (0, 181))
    padded.paste(Image.new("RGB", (img.width, 181), tuple(bottom)), (0, 905))
    arr = np.asarray(padded.resize((2048, H), Image.Resampling.LANCZOS)).astype(np.float32)
    # 兩半來源的天空與霧統一色基，避免整片色塊不連續。
    tint_top = TOP - np.median(arr[:100], axis=(0, 1))
    tint_bottom = FOG - np.median(arr[-100:], axis=(0, 1))
    t = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    arr += tint_top[None, None, :] * (1 - t) + tint_bottom[None, None, :] * t
    return np.clip(arr, 0, 255)


def make(id):
    a = panel(SRC / f"{id}-source-a.png")
    b = panel(SRC / f"{id}-source-b.png")
    rgb = np.concatenate([a, b], axis=1)
    # 左右端與中央交接逐漸融入同一天空／霧層，避免雙影硬接。
    x = np.arange(W, dtype=np.float32)
    dist = np.minimum.reduce((x, W - 1 - x, np.abs(x - 2048)))
    fade = np.clip(dist / 100, 0, 1)
    fade = fade * fade * (3 - 2 * fade)
    rgb = rgb * fade[None, :, None] + sky * (1 - fade[None, :, None])
    yy = np.arange(H, dtype=np.float32)
    vf = np.clip(yy / 180, 0, 1) * np.clip((H - 1 - yy) / 170, 0, 1)
    vf = vf * vf * (3 - 2 * vf)
    rgb = rgb * vf[:, None, None] + sky * (1 - vf[:, None, None])
    rgb = np.uint8(np.clip(rgb, 0, 255))
    rgb[:, -1] = rgb[:, 0]
    Image.fromarray(rgb, "RGB").save(OUT / f"{id}_ai-mountains.png", optimize=True)

    # 天空預覽：增加天空高度，確認上緣不成一條線。
    preview = Image.new("RGB", (2048, 768), tuple(TOP.astype(int)))
    preview.paste(Image.fromarray(rgb).resize((2048, 512), Image.Resampling.LANCZOS), (0, 256))
    preview.save(OUT / f"{id}_ai-preview-on-sky.png", optimize=True)

    check = Image.fromarray(rgb.copy(), "RGB")
    draw = ImageDraw.Draw(check)
    for seam in (1024, 2048, 3072):
        draw.line((seam, 0, seam, H - 1), fill=(190, 83, 84), width=2)
    check.save(OUT / f"{id}_ai-four-panel-seams.png", optimize=True)
    wrap = np.concatenate([rgb[:, -256:], rgb[:, :256]], axis=1)
    Image.fromarray(wrap, "RGB").save(OUT / f"{id}_ai-wrap-seam.png", optimize=True)
    print(id, rgb.shape, "首尾像素最大差", np.abs(rgb[:, 0].astype(int) - rgb[:, -1].astype(int)).max())


for id in ("SK01", "SK02", "SK03"):
    make(id)
