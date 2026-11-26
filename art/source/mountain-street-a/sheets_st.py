"""Review sheets for ST01-ST06 (system Python + PIL), same layout as the MC01 / TX04 / MC02 sheets:
  ST_<ID>_ref_vs_model.jpg   picked AI three-view | model three-quarter (material) | clay | wireframe
  ST_<ID>_LOD0_vs_LOD1.jpg   same camera, details on

    python art/source/mountain-street-a/sheets_st.py ST01 ST02 ...
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]; PRE = ROOT / 'art/previews/mountain-street-a'; REF = ROOT / 'art/references'
try: FONT = ImageFont.truetype('C:/Windows/Fonts/msjh.ttc', 28)
except Exception: FONT = ImageFont.load_default()

def row(paths, labels, h=640, name='out.jpg'):
    ims = []
    for p in paths:
        im = Image.open(p).convert('RGB'); ims.append(im.resize((int(im.width * h / im.height), h)))
    W = sum(i.width for i in ims) + 12 * (len(ims) - 1); s = Image.new('RGB', (W, h + 48), (236, 234, 230)); x = 0; d = ImageDraw.Draw(s)
    for im, lb in zip(ims, labels):
        s.paste(im, (x, 48)); d.text((x + 10, 8), lb, fill=(40, 40, 40), font=FONT); x += im.width + 12
    s.save(PRE / name, quality=88); print('wrote', name)

def picked(mid):
    ref = mid.split('_')[0]; t = (REF / ref / 'prompt.txt').read_text(encoding='utf-8'); return ref, REF / ref / t.split('選用：')[1].split()[0]

for mid in sys.argv[1:]:
    ref, img = picked(mid)
    row([img, PRE / f'ST_{mid}_three_quarter.png', PRE / f'ST_{mid}_clay_three_quarter.png', PRE / f'ST_{mid}_wire_three_quarter.png'],
        [f'{ref} 選用的 AI 三視圖', '模型（材質）', '灰模（同光同角度）', '線框'], name=f'ST_{mid}_ref_vs_model.jpg')
    row([PRE / f'ST_{mid}_three_quarter.png', PRE / f'ST_{mid}_LOD1_three_quarter.png'], ['LOD0', 'LOD1（同機位）'], name=f'ST_{mid}_LOD0_vs_LOD1.jpg')
