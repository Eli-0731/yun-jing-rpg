"""Lay out 00_References/REF_F_Materials.png from the material previews and texture maps (Python 3 + Pillow).

  python3 05_Scripts/make_ref_f.py

Needs 04_Previews/Materials/*.png from render_material_sheet.py and 03_Textures/.  Never overwrites.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

KIT = Path(__file__).resolve().parents[1]
OUT = KIT / '00_References' / 'REF_F_Materials.png'
FONT = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
INFO = {
    'DrySoil': ('乾土（路面、陸地底層）', 'TerrainBlend 底層；道路與岸頂'),
    'WetSoil': ('濕土（近水、河床）', 'Mask R；水位附近與坡腳'),
    'Grass': ('草地（路肩、岸頂）', 'Mask G；草皮卡片另用 M_GrassCard'),
    'Moss': ('苔（陰濕坡面、石面）', 'Mask A；也用在大石頂面'),
    'Rock': ('石（散石、護岸石、石基）', '石塊、砌石、沖刷大石'),
    'PathGravel': ('碎石路面', 'Mask B；A09、C06 與路面碎石帶'),
}


def main():
    if OUT.exists(): raise SystemExit('EXISTS (not overwritten): %s' % OUT)
    f_title = ImageFont.truetype(FONT, 40); f_h = ImageFont.truetype(FONT, 26); f = ImageFont.truetype(FONT, 20); f_s = ImageFont.truetype(FONT, 17)
    cw, tile, thumb = 400, 360, 112
    W = 40 + cw * 6 + 40; H = 2200
    im = Image.new('RGB', (W, H), (246, 244, 239)); d = ImageDraw.Draw(im)
    d.text((40, 28), 'REF_F｜共用 PBR 材質（1 張貼圖平鋪＝2 m × 2 m，1024×1024，可無縫重複）', font=f_title, fill=(30, 30, 30))
    d.text((40, 84), '上排：材質實際渲染（一個平鋪單位）。下排：Base Color／Roughness／Normal 貼圖。檔案在 03_Textures/T_<名稱>_<類型>.png。', font=f, fill=(70, 70, 70))
    for i, layer in enumerate(['DrySoil', 'WetSoil', 'Grass', 'Moss', 'Rock', 'PathGravel']):
        x = 40 + i * cw; y = 130
        im.paste(Image.open(KIT / '04_Previews' / 'Materials' / ('M_%s.png' % layer)).convert('RGB').resize((tile, tile)), (x, y))
        zh, use = INFO[layer]
        d.text((x, y + tile + 12), 'M_' + layer, font=f_h, fill=(20, 20, 20)); d.text((x, y + tile + 48), zh, font=f, fill=(50, 50, 50))
        d.text((x, y + tile + 76), use, font=f_s, fill=(90, 90, 90))
        for k, kind in enumerate(('BaseColor', 'Roughness', 'Normal')):
            t = Image.open(KIT / '03_Textures' / ('T_%s_%s.png' % (layer, kind))).convert('RGB').resize((thumb, thumb))
            im.paste(t, (x + k * (thumb + 8), y + tile + 108)); d.text((x + k * (thumb + 8), y + tile + 108 + thumb + 4), kind, font=f_s, fill=(90, 90, 90))
    y = 130 + tile + 108 + thumb + 50
    d.text((40, y), 'M_TerrainBlend（地表混合）：乾土為底，頂點色 Mask 的四個通道各疊一層；由左到右 Mask 從 0 漸變到 1，邊界由 T_BlendNoise 打散。', font=f_h, fill=(20, 20, 20))
    demo = Image.open(KIT / '04_Previews' / 'Materials' / 'M_TerrainBlend_demo.png').convert('RGB')
    dw = W - 80 - 260; dh = int(demo.size[1] * dw / demo.size[0]); im.paste(demo.resize((dw, dh)), (40 + 260, y + 50))
    for r, txt in enumerate(['R＝濕土 WetSoil', 'G＝草 Grass', 'B＝碎石 PathGravel', 'A＝苔 Moss']):
        d.text((40, y + 50 + dh * (r + 0.5) / 4 - 12), txt, font=f, fill=(30, 30, 30))
    d.text((40 + 260, y + 58 + dh), 'Mask = 0', font=f_s, fill=(90, 90, 90)); d.text((W - 40 - 90, y + 58 + dh), 'Mask = 1', font=f_s, fill=(90, 90, 90))
    im = im.crop((0, 0, W, y + 100 + dh))
    OUT.parent.mkdir(parents=True, exist_ok=True); im.save(OUT); print('WROTE', OUT.relative_to(KIT), im.size)


if __name__ == '__main__':
    main()
