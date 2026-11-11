"""Grey | material side-by-side sheets from ruler_views.py output (same camera, same light, 1.75 m figure in both halves).

Writes art/previews/village-houses-b/<ID>/compare_<view>_grey_material.png for every ruler_<view>_grey.png / _material.png pair.
Needs Pillow:  uv run --with pillow python art/source/village-houses-b/pair_sheets.py <ID> [<ID> ...] [--kit <kit>]   (default village-houses-b)
"""
import sys
from pathlib import Path
from PIL import Image

args = sys.argv[1:]
kit = args[args.index('--kit') + 1] if '--kit' in args else 'village-houses-b'
ids = [a for i, a in enumerate(args) if a != '--kit' and (i == 0 or args[i - 1] != '--kit')]
PREV = Path(__file__).resolve().parents[2] / 'previews' / kit
for aid in ids:
    d = PREV / aid
    for grey in sorted(d.glob('ruler_*_grey.png')):
        mat = grey.with_name(grey.name.replace('_grey.png', '_material.png'))
        if not mat.exists(): continue
        a, b = Image.open(grey).convert('RGB'), Image.open(mat).convert('RGB')
        sheet = Image.new('RGB', (a.width + b.width + 8, max(a.height, b.height)), (30, 31, 33))
        sheet.paste(a, (0, 0)); sheet.paste(b, (a.width + 8, 0))
        out = d / grey.name.replace('ruler_', 'compare_').replace('_grey.png', '_grey_material.png')
        sheet.save(out); print(out.name)
