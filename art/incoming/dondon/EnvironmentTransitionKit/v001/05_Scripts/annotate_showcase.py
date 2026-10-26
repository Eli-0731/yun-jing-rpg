"""Draw Chinese labels and seam markers on the showcase renders (Python 3 + Pillow, no Blender).

  python3 05_Scripts/annotate_showcase.py [--name showcase_v01] [--dir 04_Previews/Showcase] [--qa 06_Reports/qa/final_all29.json]

Reads <name>_labels.json written by render_showcase.py and the connector QA JSON, then writes
<name>_<view>_labels.png next to each render.  Seam close-ups show where the joint is and the error that
validate_connectors.py measured for that joint.  The original renders are not modified.  Never overwrites.
"""
import sys, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

KIT = Path(__file__).resolve().parents[1]
FONT = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
TITLES = {
    'hero': '環境收邊模組：拼裝示範（道路 → 橋頭 → 木橋 → 對岸；兩岸接河岸模組）',
    'bridgehead': '橋頭近景：C01 坡道接 D02 木橋，C05 石基、C08 沖刷帶、C02 接河岸',
    'river': '沿河望去：兩岸河岸模組＋橋頭，測試水位 -0.80 m',
    'stream': '溪水近景：清澈見底，越深越偏青綠；河床卵石與波光是展示道具',
    'top': '頂視圖：模組位置與名稱',
    'seam_road': '接縫特寫：A03 左彎 15° 接 A04 右彎 15°',
    'seam_bank': '接縫特寫：C02 橋頭岸坡接 B07 石砌護岸',
    'seam_deck': '接縫特寫：C01 坡道頂端接 D02 木橋橋面（+0.15 m）',
}
NOTE = '地面、河床、溪石、水面與側邊土層是展示用道具，不是交付模組；D02 木造梁橋是 29 件之外新增的獨立資產。'


def cli():
    a = sys.argv[1:]
    def get(k, d=None): return a[a.index(k) + 1] if k in a else d
    return get('--name', 'showcase_v01'), KIT / get('--dir', '04_Previews/Showcase'), KIT / get('--qa', '06_Reports/qa/final_all29.json')


def seam_errors(qa):
    R = json.loads(qa.read_text())
    step = next(s for c in R['chains'] for s in c['steps'] if s['a'] == 'A03' and s['b'] == 'A04')
    def con(mid, name): return next(c for c in R['modules'][mid]['connectors'] if c['connector'] == name)
    bank = max(con('SM_Bridgehead_BankTransition_A', 'ExitConnector')['max_position_error_m'], con('SM_Riverbank_RockReinforced_A', 'EntryConnector')['max_position_error_m'])
    deck = next(p for p in R['pairs'] if p['pair'].startswith('C01 exit on TEST_BridgeDeck'))['max_position_error_m']
    log = json.loads((KIT / '04_Previews/Individual/D02_SM_Bridge_Timber_A/validation.json').read_text())['geometry']
    deck = max(deck, abs(log['entry_top_in_bridgehead_frame_z_m'] - log['c01_exit_z_m']))
    return {'seam_road': ('兩段直接相接，實測頂點誤差 %.4f mm（目標 ≤ 1 mm）' % (step['max_position_error_m'] * 1000)),
            'seam_bank': ('兩側都是標準河岸斷面，實測頂點誤差 %.4f mm（目標 ≤ 1 mm）' % (bank * 1000)),
            'seam_deck': ('坡道頂端與木橋橋面高度差 %.4f mm（目標 ≤ 1 mm）' % (deck * 1000))}


def font(size):
    return ImageFont.truetype(FONT, size)


def box_of(d, xy, text, f, pad=8):
    l, t, r, b = d.textbbox(xy, text, font=f)
    return (l - pad, t - pad, r + pad, b + pad)


def overlaps(a, b):
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def draw_labels(im, items, scale):
    d = ImageDraw.Draw(im, 'RGBA'); f = font(int(23 * scale)); W, H = im.size; taken = []
    offsets = [(0, -1), (1, -1), (-1, -1), (1, 0), (-1, 0), (0, 1), (1, 1), (-1, 1)]
    for it in sorted(items, key=lambda i: i['xy'][1]):
        ax, ay = it['xy'][0] * W, it['xy'][1] * H; placed = None
        for rad in (70, 110, 150, 200):
            for ox, oy in offsets:
                tx, ty = ax + ox * rad * scale, ay + oy * rad * 0.7 * scale
                tw = d.textlength(it['text'], font=f)
                x0 = tx - tw / 2 if ox == 0 else (tx if ox > 0 else tx - tw)
                bx = box_of(d, (x0, ty - 12 * scale), it['text'], f)
                if bx[0] < 4 or bx[1] < 60 * scale or bx[2] > W - 4 or bx[3] > H - 50 * scale: continue
                if any(overlaps(bx, o) for o in taken): continue
                placed = (bx, (x0, ty - 12 * scale)); break
            if placed: break
        if not placed: continue
        bx, txy = placed; taken.append(bx)
        cx, cy = (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2
        d.line([(ax, ay), (cx, cy)], fill=(255, 255, 255, 230), width=max(2, int(2 * scale)))
        r = 5 * scale; d.ellipse([ax - r, ay - r, ax + r, ay + r], fill=(255, 214, 64, 255), outline=(40, 30, 10, 255), width=2)
        d.rounded_rectangle(bx, radius=int(8 * scale), fill=(255, 255, 255, 228), outline=(60, 60, 60, 200), width=1)
        d.text(txy, it['text'], font=f, fill=(25, 25, 25, 255))


def dashed(d, a, b, fill, width, dash=18, gap=10):
    (x0, y0), (x1, y1) = a, b; L = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5; t = 0.0
    while t < L:
        t1 = min(L, t + dash)
        d.line([(x0 + (x1 - x0) * t / L, y0 + (y1 - y0) * t / L), (x0 + (x1 - x0) * t1 / L, y0 + (y1 - y0) * t1 / L)], fill=fill, width=width)
        t = t1 + gap


def draw_seam(im, seam, text, scale):
    d = ImageDraw.Draw(im, 'RGBA'); W, H = im.size
    a = (seam[0][0] * W, seam[0][1] * H); b = (seam[1][0] * W, seam[1][1] * H)
    dashed(d, a, b, (255, 214, 64, 255), max(3, int(4 * scale)))
    f = font(int(25 * scale)); txt = '黃色虛線＝接縫位置｜' + text
    bx = box_of(d, (24 * scale, H - 100 * scale), txt, f, 10)
    d.rounded_rectangle(bx, radius=int(8 * scale), fill=(255, 255, 255, 235)); d.text((24 * scale, H - 100 * scale), txt, font=f, fill=(20, 20, 20, 255))


def header(im, title, scale):
    d = ImageDraw.Draw(im, 'RGBA'); W, H = im.size
    d.rectangle([0, 0, W, 54 * scale], fill=(20, 24, 28, 215)); d.text((20 * scale, 11 * scale), title, font=font(int(28 * scale)), fill=(255, 255, 255, 255))
    d.rectangle([0, H - 40 * scale, W, H], fill=(20, 24, 28, 190)); d.text((20 * scale, H - 33 * scale), NOTE, font=font(int(19 * scale)), fill=(235, 235, 235, 255))


def main():
    name, folder, qa = cli()
    labels = json.loads((folder / ('%s_labels.json' % name)).read_text())
    errs = seam_errors(qa)
    for view, rec in labels.items():
        src = folder / rec['file']; out = folder / ('%s_%s_labels.png' % (name, view))
        if out.exists(): raise SystemExit('EXISTS (not overwritten): %s' % out)
        im = Image.open(src).convert('RGB'); scale = im.size[0] / 1920
        header(im, TITLES.get(view, view), scale)
        if rec.get('items'): draw_labels(im, rec['items'], scale)
        if rec.get('seam'): draw_seam(im, rec['seam'], errs[view], scale)
        im.save(out); print('WROTE', out.relative_to(KIT))


if __name__ == '__main__':
    main()
