"""Review sheets for MC02 (system Python + PIL), same layout as the MC01 / TX04 sheets:
  MC02_<ID>_ref_vs_model.jpg   picked AI three-view | model three-quarter (material) | clay | wireframe
  MC02_<ID>_LOD0_vs_LOD1.jpg   same camera
  MC02_<ID>_with_boardwalk_sheet.jpg   with CliffBoardwalk at both ends: material | clay | joint close-up | on the deck at 1.7 m

    python art/source/mc02-rope-bridge/sheets_mc02.py B24 B12
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]; PRE = ROOT / 'art/previews/mc02-rope-bridge'; REF = ROOT / 'art/references'
try: FONT = ImageFont.truetype('C:/Windows/Fonts/msjh.ttc', 28)
except Exception: FONT = ImageFont.load_default()
RID = {'B24': 'MC02-24M', 'B12': 'MC02-12M'}

def row(paths, labels, h=640, name='out.jpg'):
    ims = []
    for p in paths:
        im = Image.open(p).convert('RGB'); ims.append(im.resize((int(im.width * h / im.height), h)))
    W = sum(i.width for i in ims) + 12 * (len(ims) - 1); s = Image.new('RGB', (W, h + 48), (236, 234, 230)); x = 0; d = ImageDraw.Draw(s)
    for im, lb in zip(ims, labels):
        s.paste(im, (x, 48)); d.text((x + 10, 8), lb, fill=(40, 40, 40), font=FONT); x += im.width + 12
    s.save(PRE / name, quality=88); print('wrote', name)

def picked(mid):
    t = (REF / RID[mid] / 'prompt.txt').read_text(encoding='utf-8'); return REF / RID[mid] / t.split('選用：')[1].split()[0]

for mid in sys.argv[1:]:
    row([picked(mid), PRE / f'MC02_{mid}_three_quarter.png', PRE / f'MC02_{mid}_clay_three_quarter.png', PRE / f'MC02_{mid}_wire_three_quarter.png'],
        [f'{RID[mid]} 選用的 AI 三視圖', '模型（材質）', '灰模（同光同角度）', '線框'], name=f'MC02_{mid}_ref_vs_model.jpg')
    row([PRE / f'MC02_{mid}_nodetail_three_quarter.png', PRE / f'MC02_{mid}_nodetail_LOD1_three_quarter.png'], ['LOD0', 'LOD1（同機位）'], name=f'MC02_{mid}_LOD0_vs_LOD1.jpg')
    S = f'MC02_{mid}_with_boardwalk_'
    row([PRE / f'{S}three_quarter.png', PRE / f'{S}three_quarter_clay.png', PRE / f'{S}joint_A_closeup.png', PRE / f'{S}deck_eye_1p7m.png'],
        ['兩端接既有峭壁棧道（材質）', '灰模（同光同角度）', 'A 端接口特寫', '橋面 1.7 m 人眼'], name=f'{S}sheet.jpg')
