from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
import sys

d2, render_dir, output = map(Path, sys.argv[1:4])
tag = sys.argv[4]
reference_by_variant = {
    "DP01_01": ("V4", (137,607,258,698), "V4 細長褐蕈"),
    "DP01_02": ("V6", (546,500,743,637), "V6 坑邊褐蕈"),
    "DP01_03": ("V2", (425,667,607,774), "V2 根腳一排"),
    "DP01_04": ("V5", (1426,667,1608,789), "V5 根上褐蕈"),
    "DP06_01": ("V6", (1180,880,1440,1024), "V6 近景苔團"),
    "DP06_02": ("V6", (1100,610,1460,760), "V6 石邊苔團"),
    "DP06_03": ("V6", (1180,880,1440,1024), "V6 近景苔團"),
    "DP06_04": ("V2", (260,830,600,1000), "V2 林下近景"),
    "DP06_05": ("V3", (1050,820,1400,1000), "V3 石上的苔"),
    "DP06_06": ("V6", (1180,880,1440,1024), "V6 近景苔團"),
}
view, box, label = reference_by_variant[tag]
font = ImageFont.truetype(r"C:\Windows\Fonts\msjh.ttc", 24)
small_font = ImageFont.truetype(r"C:\Windows\Fonts\msjh.ttc", 20)
width, height, pad = 480, 360, 14
sheet = Image.new("RGB", (3*width+4*pad, height+126), (23,25,24))
draw = ImageDraw.Draw(sheet)
draw.text((pad,11),f"{tag}  D2 設定圖與版本對照",font=font,fill=(234,234,229))
source=Image.open(d2 / f"{view}.png").convert("RGB").crop(box)
before=Image.open(render_dir / f"{tag}-d2-crouch-v001.png").convert("RGB")
after=Image.open(render_dir / f"{tag}-d2-crouch.png").convert("RGB")
for i,(im,label_i) in enumerate(((source,label),(before,"v001 原樣品"),(after,"v002 修訂樣品"))):
    thumb=ImageOps.contain(im,(width,height),Image.Resampling.LANCZOS)
    x=pad+(width+pad)*i
    sheet.paste(thumb, (x+(width-thumb.width)//2,47+(height-thumb.height)//2))
    draw.text((x,55+height),label_i,font=small_font,fill=(228,229,220))
draw.text((pad,92+height),"v001 與 v002 使用同一相機、燈光與地景。左側為設定圖裁切，正式場景的鏡位尚待核對。",font=small_font,fill=(170,181,169))
sheet.save(output, quality=92)
