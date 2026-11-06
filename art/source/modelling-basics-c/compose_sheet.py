"""Put review renders on one labelled sheet.
  python compose_sheet.py <out.jpg> "<title>" <cols> <image>=<label> [<image>=<label> ...]"""
import sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
out,title,cols=Path(sys.argv[1]),sys.argv[2],int(sys.argv[3]);items=[a.split('=',1) for a in sys.argv[4:]]
def font(sz):
    for f in ('C:/Windows/Fonts/msjh.ttc','C:/Windows/Fonts/msyh.ttc','/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'):
        try:return ImageFont.truetype(f,sz)
        except OSError:pass
    return ImageFont.load_default()
ims=[(Image.open(p).convert('RGB'),l) for p,l in items];tw=640;th=int(tw*ims[0][0].size[1]/ims[0][0].size[0]);lab=40;rows=(len(ims)+cols-1)//cols
sheet=Image.new('RGB',(cols*(tw+6),56+rows*(th+lab+6)),(250,250,248));d=ImageDraw.Draw(sheet);d.text((10,10),title,fill=(20,20,20),font=font(30))
for i,(im,l) in enumerate(ims):
    x,y=(i%cols)*(tw+6),56+(i//cols)*(th+lab+6);sheet.paste(im.resize((tw,th),Image.LANCZOS),(x,y+lab));d.text((x+6,y+6),l,fill=(40,40,40),font=font(22))
out.parent.mkdir(parents=True,exist_ok=True);sheet.save(out,quality=88);print('sheet',out)
