"""Annotate the top-down layout render with station ids, roles, approach points and a 1 m scale bar (Pillow).

  uv run --no-project --with pillow python art/source/qingxi-alchemy-b/layout_sketch.py

Reads tools/qingxi-alchemy-b/data/layout.json and art/previews/qingxi-alchemy-b/layout/layout_top_raw.png,
writes art/previews/qingxi-alchemy-b/layout/layout_sketch.png.
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[3]
L = json.loads((REPO / 'tools/qingxi-alchemy-b/data/layout.json').read_text(encoding='utf-8'))
LAY = REPO / 'art/previews/qingxi-alchemy-b/layout'
img = Image.open(LAY / 'layout_top_raw.png').convert('RGB'); d = ImageDraw.Draw(img)
o = L['topOrtho']; k = o['px'] / o['scale']; c = o['px'] / 2


def px(x, y):
    return c + (x - o['center'][0]) * k, c - (y - o['center'][1]) * k


def font(size):
    for f in ('msjh.ttc', 'msjhbd.ttc', 'arial.ttf'):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()


F, FS = font(26), font(19)
for s in L['stations']:
    sx, sy = px(*s['position'][:2]); ax, ay = px(*s['approach'][:2])
    d.line([(sx, sy), (ax, ay)], fill=(63, 111, 98), width=3)
    d.ellipse([ax - 9, ay - 9, ax + 9, ay + 9], fill=(63, 111, 98), outline='white', width=2)
    r = s['interactRadius'] * k
    d.ellipse([ax - r, ay - r, ax + r, ay + r], outline=(63, 111, 98), width=1)
    tag = f"{s['id']} {s['label']}"
    tw = d.textlength(tag, font=F); tx, ty = ax - tw / 2, ay + 14
    d.rounded_rectangle([tx - 6, ty - 2, tx + tw + 6, ty + 32], 6, fill=(250, 247, 238))
    d.text((tx, ty), tag, fill=(35, 33, 29), font=F)
ex, ey = px(*L['entrance'][:2])
d.text((ex + 24, ey - 12), '1.70 m 比例人／入口', fill=(122, 59, 34), font=FS)
fs, fe = px(*L['flueElbow']['start'][:2]), px(*L['flueElbow']['end'][:2])
d.text(((fs[0] + fe[0]) / 2 - 60, fs[1] - 40), '煙道彎管（佈局用）', fill=(80, 70, 60), font=FS)
x0, y0 = 60, o['px'] - 70
d.rectangle([x0, y0, x0 + k, y0 + 10], fill=(35, 33, 29)); d.text((x0, y0 - 30), '1 m', fill=(35, 33, 29), font=FS)
d.text((60, 40), '溪畔煉製小工坊 · 佈局俯視（北＝上，入口在南）', fill=(35, 33, 29), font=font(34))
d.text((60, 86), '圓點＝互動接近點，細圈＝互動半徑 0.9 m；棚架、長凳、彎管、比例人為佈局佔位', fill=(90, 85, 78), font=FS)
img.save(LAY / 'layout_sketch.png'); print('sketch', LAY / 'layout_sketch.png')
