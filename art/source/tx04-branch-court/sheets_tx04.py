"""Review sheets for TX04 (system Python + PIL), same layout as the MC01 sheets:
  TX04_<ID>_ref_vs_model.jpg   picked AI three-view | model three-quarter (material) | clay | wireframe
  TX04_<ID>_LOD0_vs_LOD1.jpg   Detail_* off, same camera
  TX04_sample_gate_walls_sheet.jpg   the gate with wall segments: material | clay (same angle) | front | 1.7 m eye height

    python art/source/tx04-branch-court/sheets_tx04.py GATE WALL_ST
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]; PRE = ROOT / 'art/previews/tx04-branch-court'; REF = ROOT / 'art/references'
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
    rid = 'TX04-' + mid.replace('_', '-'); t = (REF / rid / 'prompt.txt').read_text(encoding='utf-8')
    return REF / rid / t.split('選用：')[1].split()[0]

for mid in sys.argv[1:]:
    row([picked(mid), PRE / f'TX04_{mid}_three_quarter.png', PRE / f'TX04_{mid}_clay_three_quarter.png', PRE / f'TX04_{mid}_wire_three_quarter.png'],
        [f'TX04-{mid.replace("_", "-")} 選用的 AI 三視圖', '模型（材質）', '灰模（同光同角度）', '線框'], name=f'TX04_{mid}_ref_vs_model.jpg')
    row([PRE / f'TX04_{mid}_nodetail_three_quarter.png', PRE / f'TX04_{mid}_nodetail_LOD1_three_quarter.png'],
        ['LOD0', 'LOD1（同機位）'], name=f'TX04_{mid}_LOD0_vs_LOD1.jpg')
S = 'TX04_sample_gate_walls_'
row([PRE / f'{S}three_quarter.png', PRE / f'{S}three_quarter_clay.png', PRE / f'{S}front.png', PRE / f'{S}eye_1p7m.png'],
    ['樣品：院門＋兩側直牆（材質）', '灰模（同光同角度）', '正面', '1.7 m 人眼'], name='TX04_sample_gate_walls_sheet.jpg')
A = 'TX04_academy_'
if (PRE / f'{A}aerial.png').exists():
    row([PRE / f'{A}aerial.png', PRE / f'{A}aerial_clay.png'], ['分院組裝（材質）', '灰模（同光同角度）'], h=720, name='TX04_academy_sheet_a.jpg')
    row([PRE / f'{A}front.png', PRE / f'{A}courtyard_eye_1p7m.png'], ['正面', '院內 1.7 m 人眼'], h=720, name='TX04_academy_sheet_b.jpg')
