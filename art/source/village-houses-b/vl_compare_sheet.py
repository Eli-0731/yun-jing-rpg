"""Joins the four vl_compare.py panels (StarterHouse v004, VL01, VL02, VL03) into one labelled sheet.
uv run --with pillow python vl_compare_sheet.py <panel dir> <out.png>"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

src, out = Path(sys.argv[1]), Path(sys.argv[2])
LABELS = [('StarterHouse v004（原版，未改）', 'Dondon 原檔，外框基準'),
          ('VL01 久無人住的空屋', '門窗釘木板、缺瓦三處、剝落見土磚、落葉雜草'),
          ('VL02 剛有人住的空屋', '新窗紙、前廊掃淨、掃帚、窗台花盆、換新瓦'),
          ('VL03 半塌的空屋', '右山牆端屋頂塌、右牆倒成瓦礫、小樹穿出')]
panels = sorted(src.glob('VL_four_houses_raw_[0-3]_*.png'))
assert len(panels) == 4, panels
ims = [Image.open(p).convert('RGB') for p in panels]
w, h = ims[0].size; head = 120
sheet = Image.new('RGB', (w * 4, h + head), (46, 50, 54))
font = lambda size: ImageFont.truetype('C:/Windows/Fonts/msjh.ttc', size)
d = ImageDraw.Draw(sheet)
for i, (im, (title, sub)) in enumerate(zip(ims, LABELS)):
    sheet.paste(im, (i * w, head))
    d.text((i * w + 30, 22), title, fill=(236, 232, 222), font=font(40))
    d.text((i * w + 30, 74), sub, fill=(180, 182, 178), font=font(26))
    if i: d.line([(i * w, 0), (i * w, h + head)], fill=(30, 33, 36), width=3)
sheet.save(out, optimize=True); print('SHEET', out, sheet.size)
