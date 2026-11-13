"""生成橫向可平鋪的雲海、雲帶與薄霧 RGBA 貼圖。"""
from __future__ import annotations
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

W, H = 2048, 512
OUT = Path(__file__).resolve().parents[2] / "exports" / "sky-and-distance-v1" / "CL"
SKY_PREVIEW = Path(__file__).resolve().parents[2] / "exports" / "sky-and-distance-v1" / "SK" / "SK01_sky-preview.png"
OUT.mkdir(parents=True, exist_ok=True)


def smooth(a: float, b: float, v: np.ndarray) -> np.ndarray:
    t = np.clip((v - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def noise(seed: int, nx: int, ny: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    cells = rng.integers(0, 256, (ny, nx), dtype=np.uint8)
    tiled = np.tile(cells, (1, 3))
    image = Image.fromarray(tiled, "L").resize((W * 3, H), Image.Resampling.BICUBIC)
    return np.asarray(image.crop((W, 0, W * 2, H)), dtype=np.float32) / 255.0


def layers(seed: int) -> tuple[np.ndarray, np.ndarray]:
    broad = noise(seed, 7, 4)
    medium = noise(seed + 1, 21, 9)
    small = noise(seed + 2, 57, 22)
    mixed = 0.55 * broad + 0.32 * medium + 0.13 * small
    return broad, mixed


def cloud(name: str, seed: int) -> Image.Image:
    broad, mixed = layers(seed)
    x = np.arange(W, dtype=np.float32)[None, :]
    y = np.arange(H, dtype=np.float32)[:, None]
    wav = 25*np.sin(2*np.pi*3*x/W + seed) + 12*np.sin(2*np.pi*7*x/W + seed/3)
    if name == "CL01":
        upper = 184 + wav + 33*(broad[150:151, :] - 0.5)
        envelope = smooth(upper - 36, upper + 100, y) * (1 - smooth(455, 511, y))
        body = 0.55 + 0.45*smooth(0.28, 0.70, mixed)
        alpha = 225 * envelope * body
        base = np.array((202, 213, 219), dtype=np.float32)
    elif name == "CL02":
        center = 235 + wav
        width = 68 + 24*broad[230:231, :]
        envelope = np.exp(-0.5*((y-center)/width)**2)
        filament = np.exp(-0.5*((y-(center+95))/33)**2)*0.24
        alpha = 158 * (envelope + filament) * (0.28 + 0.72*smooth(0.28,0.70,mixed))
        alpha *= smooth(18, 72, y) * (1 - smooth(445, 511, y))
        base = np.array((207, 218, 225), dtype=np.float32)
    else:
        center = 312 + 0.6*wav
        envelope = np.exp(-0.5*((y-center)/154)**2)
        alpha = 90 * envelope * (0.42 + 0.58*mixed)
        alpha *= smooth(0, 82, y) * (1 - smooth(420, 511, y))
        base = np.array((192, 207, 216), dtype=np.float32)
    shade = (mixed - 0.5) * 30
    rgba = np.empty((H, W, 4), dtype=np.uint8)
    rgba[:, :, :3] = np.uint8(np.clip(base[None,None,:] + shade[:,:,None], 0, 255))
    rgba[:, :, 3] = np.uint8(np.clip(alpha, 0, 255))
    rgba[:, -1, :] = rgba[:, 0, :]
    rgba[0, :, 3] = 0
    rgba[-1, :, 3] = 0
    im = Image.fromarray(rgba, "RGBA")
    im.save(OUT / f"{name}.png", optimize=True)
    preview(name, im)
    seam_check(name, im)
    return im


def preview(name: str, layer: Image.Image) -> None:
    with Image.open(SKY_PREVIEW) as sk:
        base = sk.convert("RGBA")
    if base.size != (1920, 1080):
        base = base.resize((1920, 1080), Image.Resampling.LANCZOS)
    band = layer.resize((1920, 480), Image.Resampling.LANCZOS)
    top = {"CL01": 475, "CL02": 350, "CL03": 520}[name]
    base.alpha_composite(band, (0, top))
    base.convert("RGB").save(OUT / f"{name}_sky-preview.png", optimize=True)


def seam_check(name: str, layer: Image.Image) -> None:
    bg = Image.new("RGBA", (W, 780), (169,184,196,255))
    bg.alpha_composite(layer, (0, 16))
    draw = ImageDraw.Draw(bg)
    arr = np.asarray(layer)
    for q, seam in enumerate((512,1024,1536,2048)):
        draw.line((seam % W,0,seam % W,12),fill=(140,84,85,255),width=2)
        ix = np.array([(seam-128+j)%W for j in range(256)])
        crop = Image.fromarray(arr[180:276,ix,:], "RGBA").resize((512,252),Image.Resampling.NEAREST)
        bg.alpha_composite(crop,(q*512,528))
        draw.line((q*512+256,528,q*512+256,779),fill=(140,84,85,255),width=2)
    bg.convert("RGB").save(OUT / f"{name}_seam-check.png", optimize=True)


def main() -> None:
    for name, seed in (("CL01",2101),("CL02",2102),("CL03",2103)):
        im = cloud(name, seed)
        a = np.asarray(im,dtype=np.int16)
        print(name, im.size, im.mode, "首尾最大色差",np.abs(a[:,0,:]-a[:,-1,:]).max(),
              "最高透明度",a[:,:,3].max())


if __name__ == "__main__":
    main()
