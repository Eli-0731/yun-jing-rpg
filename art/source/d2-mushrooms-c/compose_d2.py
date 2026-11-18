"""Side-by-side sheet for the 11/15 standard: D2 concept crops (top) vs render_d2match.py shots (bottom).
   python art/source/undergrowth-c/compose_d2.py <D2 concept dir with V*.png> <render dir> <out.jpg> <ID>
Crop boxes are in the concepts' own pixels (1820x1024): the brown mushrooms of V6, V5, V2, V4. Eli-0731."""
import sys
from PIL import Image, ImageDraw, ImageFont
d2, rd, out, tag = sys.argv[1:5]
F = ImageFont.truetype(r'C:\Windows\Fonts\msjh.ttc', 22)
crops = [('V6', (546,500,743,637), 'V6 坑邊褐蕈'), ('V5', (1426,667,1608,789), 'V5 根上褐蕈'),
         ('V2', (425,667,607,774), 'V2 根腳一排'), ('V4', (137,607,258,698), 'V4 細長褐蕈')]   # the brown mushrooms of the D2 views
H = 420
def fit(im): return im.resize((int(im.width*H/im.height), H), Image.LANCZOS)
top = [(fit(Image.open(f'{d2}/{v}.png').convert('RGB').crop(b)), t) for v,b,t in crops]
eye = Image.open(f'{rd}/{tag}-d2-eye.png').convert('RGB').crop((240,120,1040,840))
cr = Image.open(f'{rd}/{tag}-d2-crouch.png').convert('RGB').crop((200,60,1080,900))
bot = [(fit(eye), f'{tag} 0.3 m 高、約 0.45 m 外'), (fit(cr), f'{tag} 蹲低 0.12 m（同 V6 近景）')]
W = max(sum(i.width for i,_ in top), sum(i.width for i,_ in bot)) + 10*5
sheet = Image.new('RGB', (W, 2*H + 3*40 + 20), (24,24,24)); dr = ImageDraw.Draw(sheet)
dr.text((10,8), 'D2 設定圖（上） vs 成品渲染（下）：陰天、薄霧、濕褐土，同光', fill=(230,230,230), font=F)
for row,(items,y) in enumerate(((top,40),(bot,H+80))):
    x=10
    for im,t in items:
        sheet.paste(im,(x,y)); dr.text((x+6,y+H+4), t, fill=(220,220,220), font=F); x+=im.width+10
sheet.save(out, quality=90); print(sheet.size)
