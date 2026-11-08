"""Joins the five lod_compare.py panels of each asset into one before/after sheet with Chinese labels.
usage: python lod_compare_sheet.py <previews_root> [ID ...]   (needs Pillow; writes <ID>/<ID>_LOD_compare.png)"""
import glob, json, os, sys
from PIL import Image, ImageDraw, ImageFont
root = sys.argv[1]
ids = sys.argv[2:] or sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
info_root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(root))), 'exports', 'lod-backfill-b')
try: font = ImageFont.truetype('C:/Windows/Fonts/msjh.ttc', 30); small = ImageFont.truetype('C:/Windows/Fonts/msjh.ttc', 24)
except OSError: font = small = ImageFont.load_default()
LABEL = ['LOD0（原樣）', 'LOD1', 'LOD2', 'LOD0 關掉 Detail_*', 'LOD1 關掉 Detail_*']
for aid in ids:
    fs = sorted(glob.glob(os.path.join(root, aid, f'{aid}_[1-5]_*_material.png')))
    if len(fs) != 5: print('SKIP', aid, len(fs)); continue
    ims = [Image.open(f).convert('RGB') for f in fs]
    w, h = ims[0].size
    info = json.load(open(os.path.join(info_root, aid, 'model_info.json'), encoding='utf-8'))
    b = info['budget_per_lod']
    tri = [b['LOD0']['triangles'], b['LOD1']['triangles'], b['LOD2']['triangles'], b['LOD0']['triangles_without_detail'], b['LOD1']['triangles_without_detail']]
    sheet = Image.new('RGB', (w * 5, h + 110), (38, 38, 38)); dr = ImageDraw.Draw(sheet)
    for i, im in enumerate(ims):
        sheet.paste(im, (i * w, 110))
        dr.text((i * w + 16, 14), LABEL[i], fill=(240, 240, 240), font=font)
        dr.text((i * w + 16, 60), f'{tri[i]:,} 三角面', fill=(200, 200, 160), font=small)
    out = os.path.join(root, aid, f'{aid}_LOD_compare.png'); sheet.save(out); print('SHEET', out)
