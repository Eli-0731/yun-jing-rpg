"""Quality-tier review sheet: for each id, <id>-LOD0-nodetail-threequarter.png beside <id>-LOD1-nodetail-threequarter.png,
one row per id → <dir>/lod0-vs-lod1-nodetail.png.   python compose_lod.py <dir> <id> [<id> ...]"""
import sys
from pathlib import Path
from PIL import Image,ImageDraw
d=Path(sys.argv[1]);ids=sys.argv[2:];rows=[]
for i in ids:
    a,b=(Image.open(d/f'{i}-LOD{L}-nodetail-threequarter.png').convert('RGB') for L in (0,1))
    row=Image.new('RGB',(a.width+b.width+12,a.height),(30,30,30));row.paste(a,(0,0));row.paste(b,(a.width+12,0))
    dr=ImageDraw.Draw(row);dr.text((14,10),f'{i} LOD0',fill=(255,255,255));dr.text((a.width+26,10),f'{i} LOD1 (Detail_* off)',fill=(255,255,255));rows.append(row)
sheet=Image.new('RGB',(rows[0].width,sum(r.height for r in rows)+12*(len(rows)-1)),(30,30,30));y=0
for r in rows:sheet.paste(r,(0,y));y+=r.height+12
sheet.save(d/'lod0-vs-lod1-nodetail.png');print('LOD_SHEET',d/'lod0-vs-lod1-nodetail.png')
