"""D2 look-match sheet for UG01–UG06 (11/15 standard §4): for each item the closest crop of the D2 concepts (top) above its
render_d2match.py crouch shot (bottom, 0.6 m camera like V6, same overcast light, mist and wet soil). Eli-0731.
   python art/source/undergrowth-c/compose_d2_ug.py <D2 concept dir with V*.png> <previews dir> <out.jpg>
Crop boxes are in the concepts' own pixels (1820x1024)."""
import sys
from PIL import Image, ImageDraw, ImageFont
d2, pv, out = sys.argv[1:4]
F = ImageFont.truetype(r'C:\Windows\Fonts\msjh.ttc', 22)
ITEMS = [('UG01', 'V2', (0, 560, 470, 1024), 'V2 左下：大蕨'), ('UG02', 'V2', (0, 720, 300, 1024), 'V2 左下：心形大葉'),
         ('UG03', 'V6', (1430, 420, 1820, 700), 'V6 右：長舌葉'), ('UG04', 'V6', (1340, 760, 1820, 1024), 'V6 右下：白花'),
         ('UG05_02', 'V2', (560, 820, 1060, 1024), 'V2 路上：落葉'), ('UG06_02', 'V6', (880, 430, 1250, 760), 'V6 中：根上小藤')]
H = 330
def fit(im): return im.resize((int(im.width * H / im.height), H), Image.LANCZOS)
cols = []
for pid, v, box, t in ITEMS:
    ref = fit(Image.open(f'{d2}/{v}.png').convert('RGB').crop(box))
    r = Image.open(f'{pv}/{pid}/d2/{pid}-d2-crouch.png').convert('RGB')
    w, h = r.size; r = fit(r.crop((int(w * .12), int(h * .08), int(w * .88), int(h * .80))))
    cols.append((pid, ref, r, t))
W = sum(max(a.width, b.width) for _, a, b, _ in cols) + 10 * (len(cols) + 1)
sheet = Image.new('RGB', (W, 2 * H + 140), (24, 24, 24)); dr = ImageDraw.Draw(sheet)
dr.text((10, 8), 'D2 設定圖（上） vs UG 成品（下，蹲低 0.6 m，陰天、薄霧、濕褐土同光）', fill=(230, 230, 230), font=F)
x = 10
for pid, a, b, t in cols:
    cw = max(a.width, b.width)
    sheet.paste(a, (x + (cw - a.width) // 2, 40)); dr.text((x + 4, 40 + H + 2), t, fill=(220, 220, 220), font=F)
    sheet.paste(b, (x + (cw - b.width) // 2, H + 76)); dr.text((x + 4, 2 * H + 78), pid, fill=(220, 220, 220), font=F)
    x += cw + 10
sheet.save(out, quality=90); print(sheet.size)
