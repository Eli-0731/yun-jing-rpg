# DR06「參考圖 vs 成品」並排圖：art/references/DR06/v001/DR06-threequarter.png ＋ vs_dr06.py 渲染的 <物件>_LOD0_refcam.png。
# 用法：uv run --no-project --with pillow python art/source/d2-logs-b/compose_dr06.py A B
import os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
ASSETS = {'A': 'DR06_FallenTrunk_A', 'B': 'DR06_FallenTrunk_B'}
H = 720
try:
    FONT = ImageFont.truetype('C:/Windows/Fonts/msjh.ttc', 26)
except OSError:
    FONT = ImageFont.load_default()


def tile(im):
    return im.resize((round(im.width * H / im.height), H), Image.LANCZOS)


def compose(v):
    asset = ASSETS[v]
    ref = Image.open(os.path.join(ROOT, 'art', 'references', 'DR06', 'v001', 'DR06-threequarter.png')).convert('RGB')
    pre = os.path.join(ROOT, 'art', 'previews', 'd2-logs-b', asset)
    render = Image.open(os.path.join(pre, f'{asset}_LOD0_refcam.png')).convert('RGB')
    tiles = [(tile(ref), '參考圖：Codex 依 D2 設定圖 V1、V4、V5 畫的四分之三視圖'),
             (tile(render), f'成品 {asset} LOD0（遊戲模型）：鏡位照參考圖估、陰天漫射光＋霧')]
    W = sum(t[0].width for t in tiles) + 12 * (len(tiles) + 1)
    canvas = Image.new('RGB', (W, H + 60), (18, 18, 18))
    d = ImageDraw.Draw(canvas)
    x = 12
    for im, label in tiles:
        canvas.paste(im, (x, 12))
        d.text((x + 4, H + 20), label, fill=(235, 235, 235), font=FONT)
        x += im.width + 12
    out = os.path.join(pre, f'{asset}_vs_reference.jpg')
    canvas.save(out, quality=90)
    print(out, canvas.size)


if __name__ == '__main__':
    for j in sys.argv[1:]:
        compose(j)
