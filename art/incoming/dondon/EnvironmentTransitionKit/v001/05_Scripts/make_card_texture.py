"""Draw the alpha grass-card texture 03_Textures/T_GrassCard_BaseColor.png (Python 3 + Pillow).

Blades are tapered, slightly curved polygons rooted at the bottom edge; the background is fully
transparent so the card renders as an alpha cutout.  Deterministic (fixed seed).  Never overwrites.
"""
import math, random
from pathlib import Path
from PIL import Image, ImageDraw

KIT = Path(__file__).resolve().parents[1]
OUT = KIT / '03_Textures' / 'T_GrassCard_BaseColor.png'
S = 1024; FINAL = 512


def main():
    if OUT.exists(): raise SystemExit('EXISTS (not overwritten): %s' % OUT)
    rng = random.Random(7)
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i in range(70):
        x0 = rng.uniform(0.08, 0.92) * S; h = rng.uniform(0.45, 0.97) * S; w = rng.uniform(0.012, 0.03) * S
        lean = rng.uniform(-0.22, 0.22) * S; bend = rng.uniform(-0.08, 0.08) * S
        tone = rng.random(); dry = rng.random() < 0.18
        base = (40, 60, 24) if not dry else (92, 86, 48)
        tip = (82, 100, 42) if not dry else (130, 118, 72)
        col = tuple(int(b + (t - b) * (0.4 + 0.6 * tone)) for b, t in zip(base, tip))
        pts_l, pts_r = [], []
        for k in range(9):
            t = k / 8; y = S - t * h; x = x0 + lean * t * t + bend * math.sin(t * math.pi)
            ww = w * (1 - t) ** 0.9
            pts_l.append((x - ww, y)); pts_r.append((x + ww, y))
        d.polygon(pts_l + pts_r[::-1], fill=col + (255,))
        d.line([pts_l[0], pts_l[-1]], fill=tuple(int(c * 0.75) for c in col) + (255,), width=1)
    im = im.resize((FINAL, FINAL), Image.LANCZOS)
    OUT.parent.mkdir(parents=True, exist_ok=True); im.save(OUT)
    print('WROTE', OUT)


if __name__ == '__main__':
    main()
