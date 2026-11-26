"""把山城原畫整理成遠景透明卡，並輸出天空及四象限擺位預覽。"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'art/source/sky-and-distance-v1/MC-S-source.png'
OUT = ROOT / 'art/exports/sky-and-distance-v1/MC'
OUT.mkdir(parents=True, exist_ok=True)
FOG = np.array([169, 184, 196], dtype=np.float32)

def smoothstep(a, b, x):
    t = np.clip((x-a)/(b-a), 0, 1)
    return t*t*(3-2*t)

source = Image.open(SOURCE).convert('RGBA').resize((2048, 1024), Image.Resampling.LANCZOS)
a = np.asarray(source, dtype=np.float32).copy()
y, x = np.mgrid[:1024, :2048]
# 觀景亭屬近景；卡片只保留遠處山城。
matte = smoothstep(680, 1010, x) * (1-smoothstep(1940, 2048, x))
matte *= (1-smoothstep(900, 1024, y))
matte *= smoothstep(0, 55, y)
alpha = Image.fromarray(np.uint8(a[:,:,3]), 'L').filter(ImageFilter.MinFilter(5)).filter(ImageFilter.GaussianBlur(2))
a[:,:,3] = np.asarray(alpha, dtype=np.float32) * matte * 0.88
# 輕微降低飽和度與對比，使屋頂退入山霧。
value = a[:,:,:3]
gray = value.mean(axis=2, keepdims=True)
value = gray + (value-gray)*0.72
value = value*0.84 + FOG*0.16
a[:,:,:3] = np.clip(value, 0, 255)
card = Image.fromarray(np.uint8(np.clip(a, 0, 255)), 'RGBA')
card.save(OUT / 'MC-S.png', optimize=True)

sky = Image.open(ROOT / 'art/exports/sky-and-distance-v1/SK/SK03_sky-preview.png').convert('RGBA')
# 檢視 A4 朝東北的遠景比例：山城約佔畫面寬度一半。
def paste_card(canvas, size, xy):
    layer = card.resize(size, Image.Resampling.LANCZOS)
    canvas.alpha_composite(layer, xy)

preview = sky.copy()
paste_card(preview, (980, 490), (790, 430))
preview.convert('RGB').save(OUT / 'MC-S_sky-preview.png', optimize=True)

# 四片天空弧面排列檢查；山城是單片遠景卡，本身不需左右平鋪。
ring = Image.open(ROOT / 'art/exports/sky-and-distance-v1/SK/SK03.png').convert('RGBA')
paste_card(ring, (1120, 560), (2460, 300))
check = Image.new('RGB', (2048, 640), '#a9b8c4')
check.paste(ring.convert('RGB').resize((2048, 512), Image.Resampling.LANCZOS), (0, 64))
draw = ImageDraw.Draw(check)
for i in range(1, 4):
    xx = i*512
    draw.line((xx, 64, xx, 576), fill='#597080', width=2)
check.save(OUT / 'MC-S_four-panel-check.png', optimize=True)
print('MC-S', card.size, 'alpha', card.getchannel('A').getextrema())

