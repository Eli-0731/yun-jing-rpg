"""Compose 'AI three-view (top) vs model orthographic FRONT / SIDE / BACK (bottom)' sheets.

  python compose_sheets.py   (host Python with Pillow; run after build_encounter.py rendered ortho_*.png)
"""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
REF = PROJECT / 'art/references/qingxi-encounter-a'
OUT = PROJECT / 'art/previews/qingxi-encounter-a'
W = 1800

for folder in sorted(p for p in OUT.iterdir() if p.is_dir() and (p / 'ortho_front.png').exists()):
    ref = Image.open(REF / f'{folder.name[:3]}_three_view.png').convert('RGB')
    ref = ref.resize((W, int(ref.height * W / ref.width)))
    tile = W // 3
    row = Image.new('RGB', (W, tile + 40), (243, 240, 232))
    draw = ImageDraw.Draw(row)
    for i, view in enumerate(('front', 'side', 'back')):
        im = Image.open(folder / f'ortho_{view}.png').convert('RGBA').resize((tile, tile))
        row.paste(im, (i * tile, 40), im)
        draw.text((i * tile + 12, 10), f'Blender model - {view.upper()} (orthographic)', fill=(40, 40, 40))
    sheet = Image.new('RGB', (W, ref.height + row.height + 36), (243, 240, 232))
    sheet.paste(ref, (0, 0))
    ImageDraw.Draw(sheet).text((12, ref.height + 10), 'Above: saved AI three-view reference. Below: built model.', fill=(90, 60, 30))
    sheet.paste(row, (0, ref.height + 36))
    sheet.save(folder / 'ref-vs-model.png', optimize=True)
    print('SHEET', folder.name)
