"""製作山城遠景卡、天空合成與四片並排接縫檢查。"""
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np
import shutil

root = Path("art/exports/sky-and-distance-v1/MC")
root.mkdir(parents=True, exist_ok=True)
source = Path(r"C:\Users\User\.codex\generated_images\01a1cfe8-2f6c-7ef1-88d9-e284b3e72faa\exec-00b01013-2db7-4a43-b8fe-15e078ac2bf1.png")
shutil.copy2(source, root / "MC-S-source.png")
im = Image.open(source).convert("RGB").resize((2048, 1024), Image.Resampling.LANCZOS)
a = np.clip(np.asarray(im, dtype=np.int16) + np.array([8, 11, -4], dtype=np.int16), 0, 255).astype(np.uint8)
y, x = np.mgrid[0:1024, 0:2048]
fade = np.minimum.reduce([
    np.clip(x / 150.0, 0, 1),
    np.clip((2047 - x) / 150.0, 0, 1),
    np.clip((y - 230) / 105.0, 0, 1),
    np.clip((1023 - y) / 240.0, 0, 1)
])
rgba = Image.fromarray(np.dstack((a, np.rint(fade * 255).astype(np.uint8))), "RGBA")
rgba.save(root / "MC-S.png")

sky = Image.new("RGB", (1920, 1080), "#A9B8C4")
skyline = Image.open("art/exports/sky-and-distance-v1/SK/SK05.png").convert("RGB").resize((1920, 480), Image.Resampling.LANCZOS)
sky.paste(skyline, (0, 600))
card = rgba.resize((1440, 720), Image.Resampling.LANCZOS)
sky.paste(card, (240, 260), card)
sky.save(root / "MC-S_sky-preview.png")

sheet = Image.new("RGB", (2048, 512), "#A9B8C4")
small = rgba.resize((512, 256), Image.Resampling.LANCZOS)
for i in range(4):
    sheet.paste(small, (i * 512, 128), small)
sheet.save(root / "MC-S_seam-check.png")
print("MC-S", rgba.size, rgba.mode, "邊緣 alpha", int(np.asarray(rgba)[:,0,3].max()), int(np.asarray(rgba)[:,-1,3].max()))

