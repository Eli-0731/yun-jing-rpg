"""將 imagegen 鳥、蝶的透明圖整理成同規格 1024 方形貼圖。"""
from argparse import ArgumentParser
from pathlib import Path
import numpy as np
from PIL import Image

parser = ArgumentParser()
for name in ('bird_spread', 'bird_folded', 'butterfly_ivory', 'butterfly_ochre'):
    parser.add_argument(f'--{name.replace("_", "-")}', type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[3] / 'art/exports/life-v1'
inputs = {
    'LF01/LF01_Spread.png': args.bird_spread,
    'LF01/LF01_Folded.png': args.bird_folded,
    'LF02/LF02_Ivory.png': args.butterfly_ivory,
    'LF02/LF02_Ochre.png': args.butterfly_ochre,
}

for dest, source in inputs.items():
    image = Image.open(source).convert('RGBA')
    alpha = np.asarray(image.getchannel('A'))
    ys, xs = np.where(alpha > 12)
    assert len(xs), source
    margin = round(max(xs.max()-xs.min(), ys.max()-ys.min()) * .035)
    bounds = (max(0, int(xs.min())-margin), max(0, int(ys.min())-margin),
              min(image.width, int(xs.max())+margin+1), min(image.height, int(ys.max())+margin+1))
    crop = image.crop(bounds)
    scale = min(944 / crop.width, 944 / crop.height)
    size = (round(crop.width * scale), round(crop.height * scale))
    crop = crop.resize(size, Image.Resampling.LANCZOS)
    canvas = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
    canvas.alpha_composite(crop, ((1024-size[0])//2, (1024-size[1])//2))
    target = root / dest
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target, optimize=True)
    print(target, size, canvas.getchannel('A').getextrema())
