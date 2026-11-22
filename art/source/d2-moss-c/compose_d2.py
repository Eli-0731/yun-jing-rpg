from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
import sys

d2, render_dir, output = map(Path, sys.argv[1:4])
tag = sys.argv[4]
reference_by_variant = {
    "DP10_01": ("V2", (0,0,700,600), "V2 根上垂下的細藤"),
    "DP10_02": ("V2", (0,0,700,600), "V2 根上垂下的細藤"),
    "DP10_03": ("V3", (0,0,700,600), "V3 垂藤"),
    "DP10_04": ("V2", (0,0,700,600), "V2 根上垂下的細藤"),
    "DP12_01": ("V4", (0,300,700,700), "V4 枯灌"),
    "DP12_02": ("V4", (0,300,700,700), "V4 枯灌"),
    "DP12_03": ("V4", (0,300,700,700), "V4 枯灌"),
    "DP08_01": ("V6", (1100,0,1820,420), "V6 右上的蕨"),
    "DP08_02": ("V6", (1100,0,1820,420), "V6 右上的蕨"),
    "DP08_03": ("V6", (0,600,600,1024), "V6 左下的蕨"),
    "DP09_01": ("V6", (1320,700,1820,1024), "V6 右下林下地被"),
    "DP09_02": ("V6", (1320,700,1820,1024), "V6 右下林下地被"),
    "DP09_03": ("V6", (1320,700,1820,1024), "V6 右下林下地被"),
    "DP09_04": ("V6", (1320,700,1820,1024), "V6 右下林下地被"),
    "DP11_01": ("V5", (1300,620,1820,1024), "V5 右下林下"),
    "DP11_02": ("V5", (1300,620,1820,1024), "V5 右下林下"),
    "DP11_03": ("V3", (0,600,700,1024), "V3 左下林下"),
    "DP07_01": ("V3", (1050,820,1400,1000), "V3 石上的苔"),
    "DP07_02": ("V3", (1050,820,1400,1000), "V3 石上的苔"),
    "DP07_03": ("V6", (1153,576,1517,728), "V6 倒木上的苔"),
    "DP07_04": ("V3", (1050,820,1400,1000), "V3 石上的苔"),
    "DP07_05": ("V3", (1050,820,1400,1000), "V3 石上的苔"),
    "DP07_06": ("V3", (1050,820,1400,1000), "V3 石上的苔"),
    "DP13_01": ("V6", (1500,330,1820,520), "V6 倒木上的地衣"),
    "DP13_02": ("V6", (1500,330,1820,520), "V6 倒木上的地衣"),
    "DP13_03": ("V6", (1500,330,1820,520), "V6 倒木上的地衣"),
    "DP13_04": ("V6", (1500,330,1820,520), "V6 倒木上的地衣"),
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
draw.text((pad,11),f"{tag}  D2 設定圖對照",font=font,fill=(234,234,229))
source=Image.open(d2 / f"{view}.png").convert("RGB").crop(box)
crouch=render_dir / f"{tag}-d2-crouch.png"
if (render_dir / f"{tag}-d2-crouch-v001.png").exists():   # a revised item: setting view, first version, current version (same camera)
    panels=((source,label),(Image.open(render_dir / f"{tag}-d2-crouch-v001.png"),"v001 原樣品"),(Image.open(crouch),"v002 修訂樣品"))
    note="v001 與 v002 使用同一相機、燈光與地景。左側為設定圖裁切，正式場景的鏡位尚待核對。"
else:   # a first version: setting view, eye height 1.6 m, crouched 0.6 m
    panels=((source,label),(Image.open(render_dir / f"{tag}-d2-eye.png"),"成品・眼高 1.6 m"),(Image.open(crouch),"成品・蹲低 0.6 m"))
    note="成品在 D2 的光下（陰天、薄霧、濕褐土）；貼在石頭、根、樹皮上的件在審圖裡是單獨擺在地上。左側為設定圖裁切，正式場景的鏡位尚待核對。"
for i,(im,label_i) in enumerate(panels):
    thumb=ImageOps.contain(im.convert("RGB"),(width,height),Image.Resampling.LANCZOS)
    x=pad+(width+pad)*i
    sheet.paste(thumb, (x+(width-thumb.width)//2,47+(height-thumb.height)//2))
    draw.text((x,55+height),label_i,font=small_font,fill=(228,229,220))
draw.text((pad,92+height),note,font=small_font,fill=(170,181,169))
sheet.save(output, quality=92)
