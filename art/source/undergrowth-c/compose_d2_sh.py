"""D2 look-match sheet for SH02 and SP01 (11/15 standard §4): the nearest crops of the D2 concepts (top) above the
render_d2match.py shots (bottom: eye height 1.6 m and crouch 0.6 m, same overcast light, mist and wet soil). Eli-0731.
   python art/source/undergrowth-c/compose_d2_sh.py <D2 concept dir with V*.png> <previews dir> <out.jpg>
The concepts show no shrub or sapling up close: the crops are the nearest small woody plants (V5 right edge, V3 / V6 background).
Crop boxes are fractions of each concept's width and height."""
import sys
from PIL import Image, ImageDraw, ImageFont
d2, pv, out = sys.argv[1:4]
F = ImageFont.truetype(r'C:\Windows\Fonts\msjh.ttc', 22)
TOP = [('V5', (.86, .55, 1., .98), 'V5 右下：林緣小灌木'), ('V3', (.80, .02, 1., .45), 'V3 右後：林間小樹'), ('V5', (.74, .02, .96, .62), 'V5 右後：林間小樹')]
H = 380
def fit(im): return im.resize((int(im.width * H / im.height), H), Image.LANCZOS)
def crop(v, b):
    im = Image.open(f'{d2}/{v}.png').convert('RGB'); w, h = im.size
    return im.crop((int(b[0] * w), int(b[1] * h), int(b[2] * w), int(b[3] * h)))
top = [(fit(crop(v, b)), t) for v, b, t in TOP]
bot = []
for pid in ('SH02', 'SP01'):
    for shot, t in (('eye', '眼高 1.6 m'), ('crouch', '蹲低 0.6 m')):
        r = Image.open(f'{pv}/{pid}/d2/{pid}-d2-{shot}.png').convert('RGB'); w, h = r.size
        bot.append((fit(r.crop((int(w * .22), int(h * .08), int(w * .78), int(h * .86)))), f'{pid} {t}'))
W = max(sum(i.width for i, _ in top), sum(i.width for i, _ in bot)) + 10 * 5
sheet = Image.new('RGB', (W, 2 * H + 140), (24, 24, 24)); dr = ImageDraw.Draw(sheet)
dr.text((10, 8), 'D2 設定圖（上） vs SH02、SP01 成品（下）：陰天、薄霧、濕褐土，同光', fill=(230, 230, 230), font=F)
for items, y in ((top, 40), (bot, H + 96)):
    x = 10
    for im, t in items:
        sheet.paste(im, (x, y)); dr.text((x + 6, y + H + 4), t, fill=(220, 220, 220), font=F); x += im.width + 10
sheet.save(out, quality=90); print(sheet.size)
