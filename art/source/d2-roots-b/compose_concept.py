# 「設定圖裡同一個東西 vs 成品」並排圖：設定圖裁切（範圍見 vs_concept.py 的 CROPS）＋ vs_concept.py 渲染的 <物件>_LOD0_<設定圖>cam.png。
# 設定圖不在版本庫（核心組的 D2 設定圖 V2、V3、V5）：放在環境變數 D2_CONCEPT 指的資料夾（預設 D:/yun-jing-cache/dr04-codex，V2 在 dr01-codex）。
# 用法：uv run --no-project --with pillow python art/source/d2-roots-b/compose_concept.py DR04_H [DR03_X ...]
import os, re, sys, ast
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
src = open(os.path.join(HERE, 'vs_concept.py'), encoding='utf-8').read()
CAMS = ast.literal_eval(re.search(r'CAMS = (\{.*?\n\})', src, re.S).group(1))
CROPS = ast.literal_eval(re.search(r'CROPS = (\{.*?\})\n', src, re.S).group(1))
CDIR = os.environ.get('D2_CONCEPT', 'D:/yun-jing-cache/dr04-codex')
H = 720
try:
    FONT = ImageFont.truetype('C:/Windows/Fonts/msjh.ttc', 26)
except OSError:
    FONT = ImageFont.load_default()


def tile(im):
    return im.resize((round(im.width * H / im.height), H), Image.LANCZOS)


def compose(job):
    asset, V = CAMS[job][0], CAMS[job][1]
    cv, box = CROPS.get(job) or CROPS[job.split('_')[0]]
    concept = Image.open(os.path.join(CDIR, cv + '.png')).convert('RGB').crop(box)
    pre = os.path.join(ROOT, 'art', 'previews', 'd2-roots-b', asset)
    render = Image.open(os.path.join(pre, f'{asset}_LOD0_{V}cam.png')).convert('RGB')
    tiles = [(tile(concept), f'設定圖 {cv}（局部）'), (tile(render), f'成品 {asset} LOD0：鏡位照 {cv} 估、陰天漫射光')]
    W = sum(t[0].width for t in tiles) + 12 * (len(tiles) + 1)
    canvas = Image.new('RGB', (W, H + 60), (18, 18, 18))
    d = ImageDraw.Draw(canvas)
    x = 12
    for im, label in tiles:
        canvas.paste(im, (x, 12))
        d.text((x + 4, H + 20), label, fill=(235, 235, 235), font=FONT)
        x += im.width + 12
    out = os.path.join(pre, f'{asset}_vs_concept_{cv}.jpg')
    canvas.save(out, quality=90)
    print(out, canvas.size)


if __name__ == '__main__':
    for j in sys.argv[1:]:
        compose(j)
