"""外觀改版對照板：第一輪 #51、第二輪 #52（r2 首版）、本版 v002 的同件渲染並排。

用法：uv run --no-project --with pillow python art/source/qingxi-waterworks-b/compare_rounds.py <r1圖> <r2圖> <v002圖> <輸出> <標題>
r1／r2 圖由 git 取出（pr/51 的 neutral_threequarter.png、ff6bcd4 的 <件號>_hero.png），本腳本只負責排版。
"""
import sys

from PIL import Image, ImageDraw, ImageFont

FONT = "C:/Windows/Fonts/msjh.ttc"


def main():
    r1, r2, v2, out, title = sys.argv[1:6]
    W = 700
    imgs = []
    for p, crop in ((r1, (0.05, 0.22, 0.95, 0.85)), (r2, (0.2, 0.25, 0.8, 0.78)), (v2, (0.2, 0.25, 0.8, 0.78))):
        im = Image.open(p).convert("RGB")
        w, h = im.size
        im = im.crop((int(w * crop[0]), int(h * crop[1]), int(w * crop[2]), int(h * crop[3])))
        imgs.append(im.resize((W, int(W * im.size[1] / im.size[0]))))
    H = max(i.size[1] for i in imgs)
    f = ImageFont.truetype(FONT, 28)
    fs = ImageFont.truetype(FONT, 22)
    sheet = Image.new("RGB", (W * 3, H + 110), (246, 242, 232))
    d = ImageDraw.Draw(sheet)
    d.text((16, 10), title, fill=(30, 30, 30), font=f)
    for k, (im, lab) in enumerate(zip(imgs, ("第一輪 #51", "第二輪 #52（r2 首版）", "本版 v002（外觀拉回）"))):
        sheet.paste(im, (k * W, 100))
        d.text((k * W + 16, 60), lab, fill=(60, 60, 60), font=fs)
    sheet.save(out)


if __name__ == "__main__":
    main()
