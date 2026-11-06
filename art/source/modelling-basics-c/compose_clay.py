"""Grey-model review sheet (work pack §1.3, silhouette first): for every item folder <previews>/BMxx/clay, one row per id with
<id>-clay-front / -side / -threequarter → <previews>/BMxx/clay/BMxx-clay.png.   python compose_clay.py <previews dir>"""
import sys
from pathlib import Path
from PIL import Image,ImageDraw
for d in sorted(Path(sys.argv[1]).glob('BM*/clay')):
    ids=sorted({p.name.split('-clay-')[0] for p in d.glob('*-clay-*.png')});rows=[]
    for i in ids:
        ims=[Image.open(d/f'{i}-clay-{v}.png').convert('RGB') for v in ('front','side','threequarter')]
        row=Image.new('RGB',(sum(m.width for m in ims)+12*(len(ims)-1),ims[0].height),(30,30,30));x=0
        for m in ims:row.paste(m,(x,0));x+=m.width+12
        ImageDraw.Draw(row).text((14,10),f'{i} grey model: front / side / three-quarter  --  rendered AFTER modelling from the final export (no clay pass came first; #69)',fill=(255,255,255));rows.append(row)
    sheet=Image.new('RGB',(rows[0].width,sum(r.height for r in rows)+12*(len(rows)-1)),(30,30,30));y=0
    for r in rows:sheet.paste(r,(0,y));y+=r.height+12
    sheet.save(d/f'{d.parent.name}-clay.png');print('CLAY_SHEET',d/f'{d.parent.name}-clay.png')
