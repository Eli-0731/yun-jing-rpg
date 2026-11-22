from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
import sys

d2, render_dir, output = map(Path, sys.argv[1:4])
tag = sys.argv[4]
reference_by_variant = {
    "DP18_01": ("V6", (520,880,860,1015), "V6 路面散落物"),
    "DP18_02": ("V6", (520,880,860,1015), "V6 路面散落物"),
    "DP18_03": ("V6", (520,880,860,1015), "V6 路面散落物"),
    "DP19_01": ("V6", (900,780,1300,900), "V6 落葉"),
    "DP19_02": ("V6", (900,780,1300,900), "V6 落葉"),
    "DP19_03": ("V2", (300,830,800,1020), "V2 林下落葉"),
    "DP17_01": ("V6", (520,880,860,1015), "V6 路中的小石"),
    "DP17_02": ("V6", (520,880,860,1015), "V6 路中的小石"),
    "DP17_03": ("V6", (520,880,860,1015), "V6 路中的小石"),
    "DP17_04": ("V6", (1220,600,1520,760), "V6 石邊的苔石"),
    "DP17_05": ("V6", (520,880,860,1015), "V6 路中的小石"),
    "DP17_06": ("V6", (520,880,860,1015), "V6 路中的小石"),
    "DP17_07": ("V6", (1220,600,1520,760), "V6 石邊的苔石"),
    "DP17_08": ("V6", (1220,600,1520,760), "V6 石邊的苔石"),
}
view, box, label = reference_by_variant[tag]
font = ImageFont.truetype(r"C:\Windows\Fonts\msjh.ttc", 24)
small_font = ImageFont.truetype(r"C:\Windows\Fonts\msjh.ttc", 20)
width, height, pad = 480, 360, 14
sheet = Image.new("RGB", (3*width+4*pad, height+126), (23,25,24))
draw = ImageDraw.Draw(sheet)
draw.text((pad,11),f"{tag}  D2 設定圖對照",font=font,fill=(234,234,229))
source=Image.open(d2 / f"{view}.png").convert("RGB").crop(box)
crouch=render_dir / f"{tag}-d2-crouch.png"
if (render_dir / f"{tag}-d2-crouch-v001.png").exists():   # a revised item: setting view, first version, current version (same camera)
    panels=((source,label),(Image.open(render_dir / f"{tag}-d2-crouch-v001.png"),"v001 原樣品"),(Image.open(crouch),"v002 修訂樣品"))
    note="v001 與 v002 使用同一相機、燈光與地景。左側為設定圖裁切，正式場景的鏡位尚待核對。"
else:   # a first version: setting view, eye height 1.6 m, crouched 0.6 m
    panels=((source,label),(Image.open(render_dir / f"{tag}-d2-eye.png"),"成品・眼高 1.6 m"),(Image.open(crouch),"成品・蹲低 0.6 m"))
    note="成品在 D2 的光下（陰天、薄霧、濕褐土）。左側為設定圖裁切，正式場景的鏡位尚待核對。"
for i,(im,label_i) in enumerate(panels):
    thumb=ImageOps.contain(im.convert("RGB"),(width,height),Image.Resampling.LANCZOS)
    x=pad+(width+pad)*i
    sheet.paste(thumb, (x+(width-thumb.width)//2,47+(height-thumb.height)//2))
    draw.text((x,55+height),label_i,font=small_font,fill=(228,229,220))
draw.text((pad,92+height),note,font=small_font,fill=(170,181,169))
sheet.save(output, quality=92)
