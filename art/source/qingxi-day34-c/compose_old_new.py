"""Combine the round-two vs round-three renders into one sheet per model: material on top, grey model below,
round two (d8411eaa, the version reviewed in #64) on the left, round three on the right.
  python compose_old_new.py <raw dir> <out dir>
Reads <ID>-old-mat-threequarter.png, <ID>-new-mat-..., <ID>-old-clay-..., <ID>-new-clay-... from the raw dir."""
import sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
raw,out=Path(sys.argv[1]),Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
def font(sz):
    for f in ('C:/Windows/Fonts/msjh.ttc','C:/Windows/Fonts/msyh.ttc','/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'):
        try:return ImageFont.truetype(f,sz)
        except OSError:pass
    return ImageFont.load_default()
F=font(30)
ids=sorted({p.name.split('-old-mat')[0] for p in raw.glob('*-old-mat-threequarter.png')})
for k in ids:
    tiles=[[raw/f'{k}-{v}-{m}-threequarter.png' for v in ('old','new')] for m in ('mat','clay')]
    if not all(p.exists() for row in tiles for p in row):print('missing',k);continue
    ims=[[Image.open(p).convert('RGB') for p in row] for row in tiles];w,h=ims[0][0].size;s=.5
    tw,th=int(w*s),int(h*s);sheet=Image.new('RGB',(tw*2+6,th*2+6+84),(250,250,248));d=ImageDraw.Draw(sheet)
    d.text((10,6),f'{k}　同燈同機位',fill=(20,20,20),font=F);d.text((10,44),'左：第二輪 d8411eaa（#64 審查版）　右：第三輪　上：材質　下：灰模',fill=(60,60,60),font=font(24))
    for r,row in enumerate(ims):
        for c,im in enumerate(row):sheet.paste(im.resize((tw,th),Image.LANCZOS),(c*(tw+6),84+r*(th+6)))
    sheet.save(out/f'{k}-old-vs-new.jpg',quality=88);print('sheet',k)
