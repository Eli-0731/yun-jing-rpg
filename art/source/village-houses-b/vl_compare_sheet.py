"""Joins the vl_compare.py panels (StarterHouse v004, VL01, VL02, VL03; with --five also VL04, VL05) into one labelled sheet,
three panels to a row when there are six.
uv run --with pillow python vl_compare_sheet.py <panel dir> <out.png> [<panel file stem> --five]"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

src, out = Path(sys.argv[1]), Path(sys.argv[2])
LABELS = [('StarterHouse v004（原版，未改）', 'Dondon 原檔，外框基準'),
          ('VL01 久無人住的空屋', '門窗釘木板、缺瓦三處、剝落見土磚、落葉雜草'),
          ('VL02 剛有人住的空屋', '新窗紙、前廊掃淨、掃帚、窗台花盆、換新瓦'),
          ('VL03 半塌的空屋', '右山牆端屋頂塌、右牆倒成瓦礫、小樹穿出')]
five = '--five' in sys.argv
stem = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith('--') else 'VL_four_houses_raw'
if five:
    LABELS += [('VL04 勤快人家', '晾衣竹架、整齊柴堆、窗台曬乾菜、門口草鞋'),
               ('VL05 老人家', '小竹椅、簷下乾玉米、窗紙補過、老松盆景、石基長苔')]
n = len(LABELS)
panels = sorted(src.glob(f'{stem}_[0-{n - 1}]_*.png'))
assert len(panels) == n, panels
ims = [Image.open(p).convert('RGB') for p in panels]
w, h = ims[0].size; head = 120
cols = 3 if n == 6 else n; rows = (n + cols - 1) // cols
sheet = Image.new('RGB', (w * cols, (h + head) * rows), (46, 50, 54))
font = lambda size: ImageFont.truetype('C:/Windows/Fonts/msjh.ttc', size)
d = ImageDraw.Draw(sheet)
for i, (im, (title, sub)) in enumerate(zip(ims, LABELS)):
    x, y = (i % cols) * w, (i // cols) * (h + head)
    sheet.paste(im, (x, y + head))
    d.text((x + 30, y + 22), title, fill=(236, 232, 222), font=font(40))
    d.text((x + 30, y + 74), sub, fill=(180, 182, 178), font=font(26))
    if i % cols: d.line([(x, y), (x, y + h + head)], fill=(30, 33, 36), width=3)
    if i // cols: d.line([(x, y), (x + w, y)], fill=(30, 33, 36), width=3)
sheet.save(out, optimize=True); print('SHEET', out, sheet.size)
