"""Before / after sheets for the third review round on PR #80 (system Python + PIL). Same camera, light and render settings on
both sides: the "before" images are the renders committed in a971440f (Blender previews and Unity shots), the "after" images
are the current ones. Output: art/previews/mountain-street-houses-a/compare-v1/*.jpg

    python art/source/mountain-street-houses-a/compare_mc01.py <before_dir>
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]; PRE = ROOT / 'art/previews/mountain-street-houses-a'; OUT = PRE / 'compare-v1'; OUT.mkdir(exist_ok=True)
BEFORE = Path(sys.argv[1])
try: FONT = ImageFont.truetype('C:/Windows/Fonts/msjh.ttc', 30)
except Exception: FONT = ImageFont.load_default()

def pair(before, after, name, title, h=720):
    a, b = Image.open(before).convert('RGB'), Image.open(after).convert('RGB')
    a = a.resize((int(a.width * h / a.height), h)); b = b.resize((int(b.width * h / b.height), h))
    s = Image.new('RGB', (a.width + b.width + 12, h + 52), (236, 234, 230)); d = ImageDraw.Draw(s)
    s.paste(a, (0, 52)); s.paste(b, (a.width + 12, 52))
    d.text((10, 10), f'{title}｜修改前（a971440f）', fill=(40, 40, 40), font=FONT); d.text((a.width + 22, 10), '修改後（第三輪審查）', fill=(40, 40, 40), font=FONT)
    s.save(OUT / name, quality=88); print('wrote', name)

pair(BEFORE / 'unity-street-eye-1p7m.png', PRE / 'unity/assembly/street-eye-1p7m.png', 'unity_street_eye_1p7m.jpg', 'Unity 1.7 m 人眼（貼圖 1024）')
pair(BEFORE / 'street_eye_1p7m.png', PRE / 'assembly/street_eye_1p7m.png', 'blender_street_eye_1p7m.jpg', 'Blender 1.7 m 人眼')
for b in ('A-shophouse', 'B-corner', 'C-terrace-row'):
    pair(BEFORE / f'{b}-threequarter.png', PRE / f'unity/assembly/{b}-threequarter.png', f'unity_{b}.jpg', f'Unity {b}')
for m in ('SF01', 'SF02', 'SF03', 'HM01', 'HM02', 'HM03', 'DT01', 'DT03'):
    pair(BEFORE / f'MC01_{m}_three_quarter.png', PRE / f'MC01_{m}_three_quarter.png', f'MC01_{m}.jpg', f'MC01-{m}')
