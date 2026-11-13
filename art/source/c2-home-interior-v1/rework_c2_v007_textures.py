"""C2 v007：只修屋瓦與室內灰牆的色彩／剝落分布。"""
from pathlib import Path
import shutil

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[3]
old = ROOT / 'art/exports/c2-home-interior-v1/v006/Textures'
new = ROOT / 'art/exports/c2-home-interior-v1/v007/Textures'
new.mkdir(parents=True, exist_ok=True)
for texture in old.glob('*.png'):
    shutil.copy2(texture, new / texture.name)

tile = np.asarray(Image.open(old / 'C2_VL_tile_BaseColor.png').convert('RGBA')).copy()
rgb = tile[:, :, :3].astype(np.float32)
variation = rgb.mean(axis=2, keepdims=True) - rgb.mean()
tile[:, :, :3] = np.clip(np.array([58, 64, 72]) + variation * 0.77, 0, 255).astype(np.uint8)
Image.fromarray(tile).save(new / 'C2_VL_tile_BaseColor.png')

source = np.asarray(Image.open(old / 'C2_TI_plaster_BaseColor.png').convert('RGBA'))
h, w = source.shape[:2]
yy, xx = np.mgrid[:h, :w]
rgb = source[:, :, :3].astype(np.float32)
brightness = rgb.mean(axis=2)
detail = np.clip((brightness - 148) * 0.36, -14, 11)
grain = (np.sin(xx * .071 + yy * .041) + np.sin(xx * .019 - yy * .083)) * 1.8
base = np.stack([151 + detail + grain, 151 + detail + grain, 145 + detail + grain], axis=-1)
# 原貼圖的磚色只留在牆腳和一處背陰角落，避免全牆反覆露磚。
brick = (rgb[:, :, 0] - rgb[:, :, 2] > 37) & (rgb[:, :, 0] - rgb[:, :, 1] > 13)
bottom = yy > 427 + 21 * np.sin(xx * .021) + 9 * np.sin(xx * .079)
corner = (xx < 62 + 9 * np.sin(yy * .053)) & (yy > 303) & (yy < 441)
keep = brick & (bottom | corner)
aged_brick = rgb * .57 + np.array([108, 105, 100]) * .43
out = np.concatenate([np.where(keep[:, :, None], aged_brick, base), source[:, :, 3:4]], axis=2)
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(new / 'C2_TI_plaster_BaseColor.png')
print('C2 v007 材質已輸出', new)
