"""Side-by-side sheet for the 11/15 standard: D2 concept crops (top) vs render_d2match.py shots (bottom).
   python art/source/d2-moss-c/compose_d2.py <D2 concept dir with V*.png> <render dir> <out.jpg> <ID>
Crop boxes are in the concepts' own pixels (V6 1820x1024, V3 1536x1024): the moss cushions of V6 and the moss on the V3 boulder. Eli-0731."""
import sys
from PIL import Image, ImageDraw, ImageFont
d2, rd, out, tag = sys.argv[1:5]
F = ImageFont.truetype(r'C:\Windows\Fonts\msjh.ttc', 22)
crops = [('V6', (1100,610,1460,760), 'V6 石邊苔團'), ('V6', (1180,880,1440,1024), 'V6 近景苔團'),
         ('V3', (1050,820,1400,1000), 'V3 石上的苔')]   # the moss of the D2 views
H = 420
def fit(im): return im.resize((int(im.width*H/im.height), H), Image.LANCZOS)
top = [(fit(Image.open(f'{d2}/{v}.png').convert('RGB').crop(b)), t) for v,b,t in crops]
eye = Image.open(f'{rd}/{tag}-d2-eye.png').convert('RGB').crop((240,120,1040,840))
cr = Image.open(f'{rd}/{tag}-d2-crouch.png').convert('RGB').crop((200,60,1080,900))
bot = [(fit(eye), f'{tag} 0.3 m 高（小件鏡位）'), (fit(cr), f'{tag} 蹲低 0.12 m（同 V6 近景）')]
W = max(sum(i.width for i,_ in top), sum(i.width for i,_ in bot)) + 10*5
sheet = Image.new('RGB', (W, 2*H + 3*40 + 20), (24,24,24)); dr = ImageDraw.Draw(sheet)
dr.text((10,8), 'D2 設定圖（上） vs 成品渲染（下）：陰天、薄霧、濕褐土，同光', fill=(230,230,230), font=F)
for row,(items,y) in enumerate(((top,40),(bot,H+80))):
    x=10
    for im,t in items:
        sheet.paste(im,(x,y)); dr.text((x+6,y+H+4), t, fill=(220,220,220), font=F); x+=im.width+10
sheet.save(out, quality=90); print(sheet.size)
