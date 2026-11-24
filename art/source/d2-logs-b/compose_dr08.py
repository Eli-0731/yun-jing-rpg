# DR08「參考圖 vs 成品」並排圖：art/references/DR08/v001/DR08-threeview.png 左欄那一列（側視）＋ vs_dr08.py 渲染的 <物件>_LOD0_refcam.png。
# 用法：uv run --no-project --with pillow python art/source/d2-logs-b/compose_dr08.py A B C
import os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
ASSETS = {'A': 'DR08_RottenLog_A', 'B': 'DR08_RottenLog_B', 'C': 'DR08_RottenLog_C'}
ROW = {'A': (0, 70, 760, 330), 'B': (0, 360, 760, 630), 'C': (0, 660, 830, 940)}      # 參考圖（1536×1024）左欄三列：側視＋人形尺
H = 420
try:
    FONT = ImageFont.truetype('C:/Windows/Fonts/msjh.ttc', 24)
except OSError:
    FONT = ImageFont.load_default()


def tile(im):
    return im.resize((round(im.width * H / im.height), H), Image.LANCZOS)


def compose(v):
    asset = ASSETS[v]
    ref = Image.open(os.path.join(ROOT, 'art', 'references', 'DR08', 'v001', 'DR08-threeview.png')).convert('RGB').crop(ROW[v])
    ver = os.environ.get('DR8VER', 'v001')                 # v002 以後：讀寫 <物件>/<版本>/
    pre = os.path.join(ROOT, 'art', 'previews', 'd2-logs-b', asset, *([] if ver == 'v001' else [ver]))
    render = Image.open(os.path.join(pre, f'{asset}_LOD0_refcam.png')).convert('RGB')
    tiles = [(tile(ref), f'參考圖：DR08 三視圖左欄（{v}）'),
             (tile(render), f'成品 {asset} {ver} LOD0（遊戲模型）：正面平視，鏡位照參考圖估')]
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
