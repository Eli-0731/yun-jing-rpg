"""Compose 'AI three-view (top) vs Blender model orthographic render (bottom)' sheets.

  python compose_sheets.py   (host Python with Pillow; run after build_yard.py has rendered ortho_*.png)
"""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
REF = PROJECT / 'art/references/qingxi-training-yard-v1'
OUT = PROJECT / 'art/previews/qingxi-training-yard-v1'
IDS = ['training-shelter', 'qi-striking-post', 'agility-post', 'weapon-rack',
       'engraved-training-stone', 'training-banner']
W = 1800

for name in IDS:
    ref = Image.open(REF / f'{name}-three-view.png').convert('RGB')
    ref = ref.resize((W, int(ref.height * W / ref.width)))
    tile = W // 3
    row = Image.new('RGB', (W, tile + 40), (243, 240, 232))
    draw = ImageDraw.Draw(row)
    for i, view in enumerate(('front', 'side', 'top')):
        im = Image.open(OUT / name / f'ortho_{view}.png').convert('RGBA').resize((tile, tile))
        row.paste(im, (i * tile, 40), im)
        draw.text((i * tile + 12, 10), f'Blender model - {view.upper()} (orthographic)', fill=(40, 40, 40))
    sheet = Image.new('RGB', (W, ref.height + row.height + 36), (243, 240, 232))
    sheet.paste(ref, (0, 0))
    ImageDraw.Draw(sheet).text((12, ref.height + 10), 'Above: saved AI three-view reference. Below: built model.', fill=(90, 60, 30))
    sheet.paste(row, (0, ref.height + 36))
    sheet.save(OUT / name / 'ref-vs-model.png', optimize=True)
    print('SHEET', name)
