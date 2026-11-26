"""把 imagegen 透明石峰原圖整理成 2048 方形 RGBA 遊戲貼圖。"""
from argparse import ArgumentParser
from pathlib import Path
from PIL import Image

parser = ArgumentParser()
parser.add_argument('--mm01', type=Path, required=True)
parser.add_argument('--mm02', type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[3]
for key, source in (('MM01', args.mm01), ('MM02', args.mm02)):
    image = Image.open(source).convert('RGBA')
    assert image.getchannel('A').getextrema() == (0, 255), f'{key} 缺少透明度'
    image = image.resize((2048, 2048), Image.Resampling.LANCZOS)
    target = root / 'art/exports/midground-v1' / key / f'{key}_Albedo.png'
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, optimize=True)
    print(key, target, image.size, image.mode)
