# 把成品渲染和設定圖並排：uv run --no-project --with pillow python compose_review.py 輸出.jpg 左圖 左標 右圖 右標 [...]
import sys
from PIL import Image, ImageDraw, ImageFont
out, rest = sys.argv[1], sys.argv[2:]
H = 720
tiles = []
for i in range(0, len(rest), 2):
    im = Image.open(rest[i]).convert('RGB')
    im = im.resize((round(im.width * H / im.height), H), Image.LANCZOS)
    tiles.append((im, rest[i + 1]))
W = sum(t[0].width for t in tiles) + 12 * (len(tiles) + 1)
canvas = Image.new('RGB', (W, H + 64), (18, 18, 18))
try:
    font = ImageFont.truetype('C:/Windows/Fonts/msjh.ttc', 28)
except OSError:
    font = ImageFont.load_default()
d = ImageDraw.Draw(canvas)
x = 12
for im, label in tiles:
    canvas.paste(im, (x, 12))
    d.text((x + 4, H + 20), label, fill=(235, 235, 235), font=font)
    x += im.width + 12
canvas.save(out, quality=90)
print(out, canvas.size)
