"""Review sheets for the MC01 sample (system Python + PIL):
  MC01_<ID>_ref_vs_model.jpg   picked AI three-view | model three-quarter (material) | clay | wireframe
  MC01_<ID>_LOD0_vs_LOD1.jpg   Detail_* off, same camera
  MC01_sample_shop_sheet.jpg   assembled shop: material | clay (same angle) + front + side

    python art/source/mountain-street-houses-a/sheets_mc01.py SB01 SF01 RF01
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]; PRE = ROOT / 'art/previews/mountain-street-houses-a'; REF = ROOT / 'art/references'
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
    t = (REF / f'MC01-{mid}' / 'prompt.txt').read_text(encoding='utf-8')
    fn = t.split('選用：')[1].split()[0]; return REF / f'MC01-{mid}' / fn

for mid in sys.argv[1:]:
    row([picked(mid), PRE / f'MC01_{mid}_three_quarter.png', PRE / f'MC01_{mid}_clay_three_quarter.png', PRE / f'MC01_{mid}_wire_three_quarter.png'],
        [f'MC01-{mid} 選用的 AI 三視圖', '模型（材質）', '灰模（同光同角度）', '線框'], name=f'MC01_{mid}_ref_vs_model.jpg')
    row([PRE / f'MC01_{mid}_nodetail_three_quarter.png', PRE / f'MC01_{mid}_nodetail_LOD1_three_quarter.png'],
        ['LOD0（關 Detail_*）', 'LOD1（關 Detail_*，同機位）'], name=f'MC01_{mid}_LOD0_vs_LOD1.jpg')
row([PRE / 'MC01_sample_shop_three_quarter.png', PRE / 'MC01_sample_shop_clay_three_quarter.png', PRE / 'MC01_sample_shop_front.png', PRE / 'MC01_sample_shop_side.png'],
    ['樣品組裝 SB01＋SF01＋RF01（材質）', '灰模（同光同角度）', '正面', '側面'], name='MC01_sample_shop_sheet.jpg')
