"""DP05 review sheet: the V6 log (setting view crop) beside the placement demo renders.
python art/source/d2-mushrooms-c/compose_dp05.py <folder with D2 V6.png>   (from the repo root, after place_dp05.py)"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
d2=Path(sys.argv[1]);P=Path('art/previews/d2-mushrooms-c/DP05')
font=ImageFont.truetype(r"C:\Windows\Fonts\msjh.ttc",24);small=ImageFont.truetype(r"C:\Windows\Fonts\msjh.ttc",19)
panels=[(Image.open(d2/'V6.png').convert('RGB').crop((849,379,1820,789)),'V6 長苔的倒木（右側）'),
        (Image.open(P/'DP05-overview.png'),'擺放示範・全景（DR06_FallenTrunk_A 的一段）'),
        (Image.open(P/'DP05-threequarter.png'),'斜看：側面的層狀菌、根腳的褐蕈'),
        (Image.open(P/'DP05-top.png'),'倒木頂上：簇生褐蕈、白蕈、小菇、苔枝'),
        (Image.open(P/'DP05-crouch.png'),'蹲低 0.3 m：根腳的白蕈、朽木段'),
        (Image.open(P/'DP05-plan.png'),'俯視：擺放位置')]
W,H,pad=620,388,14;sheet=Image.new('RGB',(3*W+4*pad,2*(H+40)+60),(23,25,24));dr=ImageDraw.Draw(sheet)
dr.text((pad,12),'DP05 蕈叢擺放示範（DP01–DP04 在一段倒木上；座標在 art/exports/d2-mushrooms-c/DP05_placement.json）',font=font,fill=(234,234,229))
for i,(im,lab) in enumerate(panels):
    t=ImageOps.contain(im.convert('RGB'),(W,H));x=pad+(W+pad)*(i%3);y=52+(H+40)*(i//3)
    sheet.paste(t,(x+(W-t.width)//2,y+(H-t.height)//2));dr.text((x,y+H+6),lab,font=small,fill=(228,229,220))
out=P/'DP05-sheet.jpg';sheet.save(out,quality=90);print('sheet',out)
