"""TX04 lime-plaster wall texture (review on PR #90: the trim-sheet plaster read as vertical planks on the long academy walls).

One 1024 x 1024 tile = 4 m x 4 m (256 px/m, the trim sheet's density). U runs along the wall and tiles; V = height, the top row
is the top of the wall (build_tx04.wallmat anchors every wall's top edge there), so rain streaks hang from under the coping /
lintel. Irregular on purpose: blotchy tone at three scales, a few repair patches, flaked spots showing the grey under-coat,
and rain streaks of random length, width, strength and slant (never all the same direction).

    python art/source/tx04-branch-court/gen_wall_tex.py   -> art/textures/tx04-branch-court/T_TX04_Wall_{Albedo,Normal}.png
"""
import math
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]
OUT = ROOT / 'art/textures/tx04-branch-court'; OUT.mkdir(parents=True, exist_ok=True)
N = 1024; PXM = 256; rng = np.random.default_rng(9004)

def vnoise(cells_x, cells_y):
    """tileable (in X and Y) value noise, smoothstep-interpolated"""
    g = rng.random((cells_y, cells_x)); x = np.arange(N) * cells_x / N; y = np.arange(N) * cells_y / N
    xi = x.astype(int); yi = y.astype(int); fx = x - xi; fy = y - yi; fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy)
    a = g[np.ix_(yi % cells_y, xi % cells_x)]; b = g[np.ix_(yi % cells_y, (xi + 1) % cells_x)]
    c = g[np.ix_((yi + 1) % cells_y, xi % cells_x)]; d = g[np.ix_((yi + 1) % cells_y, (xi + 1) % cells_x)]
    fx = fx[None, :]; fy = fy[:, None]; return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy

def fbm(c, octaves=4, gain=.5):
    v = 0; amp = 1; tot = 0
    for o in range(octaves): v = v + amp * vnoise(c * 2 ** o, c * 2 ** o); tot += amp; amp *= gain
    return v / tot

def warp_fbm(c, octaves=4, amt=.08):
    """domain-warped fbm: breaks the grid look so blotches have ragged, non-repeating edges"""
    base = fbm(c, octaves); wx = (fbm(3, 2) - .5) * amt * N; wy = (fbm(3, 2) - .5) * amt * N
    yy, xx = np.mgrid[0:N, 0:N]; return base[((yy + wy).astype(int)) % N, ((xx + wx).astype(int)) % N]

# base tone: the trim sheet's plaster mean, so TX04 walls sit next to MC01 plaster without a jump
trim = np.asarray(Image.open(ROOT / 'art/textures/mountain-street-houses-a/T_MountainStreet_Albedo.png').convert('RGB'), np.float32) / 255
band = trim[2048 - 1536 + 8:2048 - 1280 - 8]   # plaster strip (V 1280-1536 from the bottom), padding skipped
base = band.reshape(-1, 3).mean(0); print('trim plaster mean', np.round(base * 255).astype(int))

Y = (np.arange(N) / N)[:, None]   # 0 = wall top, 1 = 4 m below it
blot = warp_fbm(2, 4, .12); mid = warp_fbm(6, 3, .06); fine = fbm(40, 2)
tone = 1 + .10 * (blot - .5) * 2 + .05 * (mid - .5) * 2 + .02 * (fine - .5) * 2
alb = np.ones((N, N, 3), np.float32) * base[None, None, :] * tone[..., None]
hgt = .5 * mid + .25 * fine

# repair patches: fresher, slightly cooler lime with ragged outlines
edge = warp_fbm(10, 3, .1)
for _ in range(5):
    cx, cy = rng.uniform(0, N), rng.uniform(.05, .9) * N; rx, ry = rng.uniform(.15, .45) * PXM, rng.uniform(.12, .35) * PXM
    yy, xx = np.mgrid[0:N, 0:N]; dx = (xx - cx + N / 2) % N - N / 2; dy = yy - cy
    r = np.sqrt((dx / rx) ** 2 + (dy / ry) ** 2) + 1.1 * (edge - .5) * 2   # strongly ragged outline, not an ellipse
    m = np.clip((1 - r) * 3, 0, 1) * rng.uniform(.4, 1.0)
    alb = alb * (1 - m[..., None]) + (alb * np.array([1.03, 1.035, 1.04]))[...] * m[..., None]; hgt = hgt + .12 * m

# flaked spots: the grey-brown under-coat shows through, a little recessed
under = np.array([.52, .49, .44])
flake = np.clip((warp_fbm(9, 3, .05) - .70) * 7, 0, 1) * np.clip((fbm(2, 2) - .45) * 3, 0, 1)
alb = alb * (1 - .85 * flake[..., None]) + under[None, None, :] * .85 * flake[..., None]; hgt = hgt - .6 * flake

# rain streaks from the top edge: random x, length 0.25-1.6 m, width 1.5-14 cm, strength, slant -10..+10 deg, wobble
streak = np.zeros((N, N), np.float32); yy, xx = np.mgrid[0:N, 0:N]
clusters = rng.uniform(0, N, 6)   # streaks gather where water runs off (joints, ends), not evenly like a comb
for _ in range(24):
    x0 = (rng.choice(clusters) + rng.normal(0, .25 * PXM)) % N if rng.random() < .7 else rng.uniform(0, N)
    L = rng.uniform(.2, 1.7) * PXM; s = rng.uniform(.2, .9)
    w = rng.uniform(.015, .05) * PXM if rng.random() < .6 else rng.uniform(.1, .3) * PXM   # thin runs and broad faint stains
    if w > .09 * PXM: s *= .5
    slant = math.tan(math.radians(rng.uniform(-10, 10))); wob = rng.uniform(2, 10); ph = rng.uniform(0, math.tau)
    y0 = (rng.uniform(0, .03) if rng.random() < .6 else rng.uniform(.05, .35)) * N   # under the coping, or from a crack lower down
    t = (yy - y0) / L; cxs = x0 + slant * (yy - y0) + wob * np.sin(yy / rng.uniform(40, 120) + ph)
    dx = (xx - cxs + N / 2) % N - N / 2
    wt = w * (1 - .6 * np.clip(t, 0, 1))   # narrows downwards
    prof = np.exp(-(dx / np.maximum(wt, 1)) ** 2 * 2) * np.clip(t * 12, 0, 1) * np.clip(1 - t, 0, 1) ** 1.6
    streak = np.maximum(streak, s * prof * (t >= 0))
streak = streak * (.6 + .4 * fine)
grime = np.array([.40, .38, .33])
alb = alb * (1 - .30 * streak[..., None]) + grime[None, None, :] * .30 * streak[..., None] * .4
# a soft overall darkening near the top (drip zone) and a faint damp band lower down
alb = alb * (1 - .03 * np.exp(-Y / .04) * (.5 + blot))[..., None] * (1 - .04 * np.clip((Y - .45) * 3, 0, 1) * blot)[..., None]
hgt = hgt + .1 * streak

alb = np.clip(alb, 0, 1)
Image.fromarray((alb * 255 + .5).astype(np.uint8)).save(OUT / 'T_TX04_Wall_Albedo.png')
s = 1.6; dx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) * s; dy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) * s
n = np.dstack([-dx, dy, np.ones_like(hgt)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
Image.fromarray(((n * .5 + .5) * 255 + .5).astype(np.uint8)).save(OUT / 'T_TX04_Wall_Normal.png')
print('wrote', OUT / 'T_TX04_Wall_Albedo.png', 'mean', np.round(alb.reshape(-1, 3).mean(0) * 255).astype(int))
