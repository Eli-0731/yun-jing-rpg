"""以 55° 水平 FOV、1920×1080 預覽鳥 60 m 與蝶 3 m 的實際像素尺寸。"""
from pathlib import Path
from math import tan, radians
from PIL import Image

root = Path(__file__).resolve().parents[2]
out = root / 'exports/life-v1'
refs = root / 'references/keyart'
sky = root / 'exports/sky-and-distance-v1/SK/SK03_sky-preview.png'
width, height = 1920, 1080
fov = 55


def px(meters, distance):
    return round(width * meters / (2 * distance * tan(radians(fov / 2))))


def put(image, source, center, size):
    sprite = Image.open(source).convert('RGBA').resize((size, size), Image.Resampling.LANCZOS)
    image.alpha_composite(sprite, (center[0]-size//2, center[1]-size//2))


bird = Image.open(sky).convert('RGB').resize((width, height), Image.Resampling.LANCZOS).convert('RGBA')
bird_px = px(.50, 60)
for name, center in (('Spread', (770, 335)), ('Folded', (965, 305)),
                     ('Spread', (1065, 380)), ('Folded', (1195, 340))):
    put(bird, out / 'LF01' / f'LF01_{name}.png', center, bird_px)
bird.convert('RGB').save(out / 'LF01/LF01_game-size-60m.png')

field = Image.open(refs / 'KA06/chosen.png').convert('RGB').resize((width, height), Image.Resampling.LANCZOS).convert('RGBA')
butterfly_px = px(.12, 3)
for name, center in (('Ivory', (820, 610)), ('Ochre', (1110, 660))):
    put(field, out / 'LF02' / f'LF02_{name}.png', center, butterfly_px)
field.convert('RGB').save(out / 'LF02/LF02_game-size-3m.png')

for key, names in (('LF01', ('Spread', 'Folded')), ('LF02', ('Ivory', 'Ochre'))):
    sheet = Image.new('RGBA', (2048, 1024), (210, 217, 218, 255))
    for i, name in enumerate(names):
        part = Image.open(out / key / f'{key}_{name}.png').convert('RGBA')
        sheet.alpha_composite(part, (i * 1024, 0))
    sheet.convert('RGB').save(out / key / f'{key}_animation-preview.png')
print('距離預覽', '鳥 60 m', bird_px, '像素；蝶 3 m', butterfly_px, '像素')
