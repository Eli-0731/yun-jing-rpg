"""Material sheets from the baked textures and renders (Pillow, no Blender).

  uv run --no-project --with pillow python art/source/qingxi-alchemy-b/sheets.py

Writes art/previews/qingxi-alchemy-b/<ID>/<state>/material_sheet.png for every exported asset state.
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
EX = REPO / 'art/exports/qingxi-alchemy-b'
PV = REPO / 'art/previews/qingxi-alchemy-b'
BG, FG, SUB = (236, 234, 229), (38, 36, 33), (110, 106, 100)


def font(size):
    for f in ('msjh.ttc', 'arial.ttf', 'DejaVuSans.ttf'):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()


def tile(img, size):
    im = img.convert('RGB'); im.thumbnail((size, size)); t = Image.new('RGB', (size, size), BG)
    t.paste(im, ((size - im.width) // 2, (size - im.height) // 2)); return t


def sheet(mi_path):
    mi = json.loads(mi_path.read_text(encoding='utf-8')); v = mi['validation']; key = mi['key']
    tdir = mi_path.parent / 'textures'; pdir = PV / mi['id'] / mi['state']
    maps = []
    bc = tdir / f'T_{key}_BaseColor.png'
    if bc.exists():
        maps.append(('BaseColor (sRGB)', Image.open(bc)))
    orm = tdir / f'T_{key}_ORM.png'
    if orm.exists():
        r, g, b = Image.open(orm).convert('RGB').split()
        maps += [('ORM.R  AO', r), ('ORM.G  Roughness', g), ('ORM.B  Metallic', b)]
    for nm, lab in (('Normal', 'Normal (tangent, OpenGL +Y)'), ('Emissive', 'Emissive (sRGB)')):
        p = tdir / f'T_{key}_{nm}.png'
        if p.exists():
            maps.append((lab, Image.open(p)))
    renders = [(lab, pdir / f) for lab, f in (('neutral 3/4', 'neutral_02_front_right.png'), ('close-up front', 'close_front.png'),
                                                ('close-up side', 'close_side.png'), ('stylized 3/4', 'stylized_02_three_quarter.png'))]
    renders = [(lab, Image.open(p)) for lab, p in renders if p.exists()]
    T, pad, W = 300, 24, 4 * 300 + 5 * 24
    rows = [renders[i:i + 4] for i in range(0, len(renders), 4)] + [maps[i:i + 4] for i in range(0, len(maps), 4)]
    H = 150 + len(rows) * (T + 46) + 40
    out = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(out)
    d.text((pad, 22), f"{mi['id']}  {mi['name']}" + ('' if mi['state'] == 'default' else f"  [{mi['state']}]"), fill=FG, font=font(34))
    alpha = ' | alpha clip' if v.get('alphaClip') else ''
    d.text((pad, 70), f"LOD tris {v['trianglesLOD']}  budget {v['budgetLOD0']}  | {v['textureResolution']} px  | materials {', '.join(v['materials'])}{alpha}",
           fill=SUB, font=font(18))
    d.text((pad, 98), f"size {mi['dimensions_m']} m  | origin base centre, front -Y  | baked from procedural Cycles source", fill=SUB, font=font(18))
    y = 140
    for row in rows:
        for i, (lab, img) in enumerate(row):
            x = pad + i * (T + pad); out.paste(tile(img, T), (x, y)); d.text((x, y + T + 8), lab, fill=FG, font=font(17))
        y += T + 46
    path = pdir / 'material_sheet.png'; path.parent.mkdir(parents=True, exist_ok=True); out.save(path); return path


if __name__ == '__main__':
    n = 0
    for mi in sorted(EX.glob('B*/v001/*_model_info.json')):
        print(sheet(mi).relative_to(REPO)); n += 1
    print(n, 'sheets')
