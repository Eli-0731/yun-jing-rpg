"""CR15 bank walk, drawn: the collision plan and the section under the walk line, the capsule where it first touches and where it rides highest.

uv run --with matplotlib python walk_figure.py <collision.json> <trace.json> <collision_after.json> <trace_after.json> <out.png>
collision.json: top-surface faces of CR15_DitchCross_Collision as [[x, y, z], ...] per face (qa dump); trace.json: FieldWalk's walk-trace-*.json.
The collision is symmetric in x and in y, so its Blender plan is drawn in Unity's x/z as it is.
"""
import json, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, Rectangle, Wedge
from matplotlib import font_manager

for f in ('C:/Windows/Fonts/msjh.ttc', 'C:/Windows/Fonts/msyh.ttc'):
    try:
        font_manager.fontManager.addfont(f); plt.rcParams['font.family'] = font_manager.FontProperties(fname=f).get_name(); plt.rcParams['axes.unicode_minus'] = False; break
    except Exception: pass


def tops(faces):
    out = []
    for f in faces:
        zs = [p[2] for p in f]
        if max(zs) - min(zs) < .2 and min(zs) > .001 or (len(f) >= 3 and all(z > .001 for z in zs)): out.append(f)
    return out


def inside(px, py, poly):
    c = False; n = len(poly)
    for i in range(n):
        x1, y1 = poly[i][0], poly[i][1]; x2, y2 = poly[(i + 1) % n][0], poly[(i + 1) % n][1]
        if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1 + 1e-12) + x1: c = not c
    return c


def height(faces, x, y):
    h = 0.
    for f in faces:
        if inside(x, y, f): h = max(h, sum(p[2] for p in f) / len(f))
    return h


def panel(ax_plan, ax_sec, faces, tr, title):
    top = tops(faces); R = tr['radius']; H = tr['height']
    for f in top:
        z = sum(p[2] for p in f) / len(f)
        ax_plan.add_patch(Polygon([(p[0], p[1]) for p in f], closed=True, fc=plt.cm.copper(.25 + z * 1.3), ec='#3a2a1a', lw=.4))
    path = tr['trace']; xs = [p[0] for p in path]; zs = [p[2] for p in path]; ys = [p[1] for p in path]
    ax_plan.plot(xs, zs, '-', color='#1f6fd1', lw=1.6, label='膠囊中心實際路線')
    (fx, fz), (tx, tz) = tr['from'], tr['to']
    ax_plan.plot([fx, tx], [fz, tz], '--', color='#888', lw=1, label='預定路線 x = %.1f m' % fx)
    t = tr['first_touch']; hi = max(range(len(path)), key=lambda i: path[i][1]); end = len(path) - 1
    if t and t != 'none':
        c = t['capsule']; ax_plan.add_patch(Circle((c[0], c[2]), R, fill=False, ec='#d12f1f', lw=1.5))
        ax_plan.plot(t['point'][0], t['point'][2], 'x', color='#d12f1f', ms=11, mew=2.5, label='第一次撞擊點 (%.2f, %.2f, %.2f)' % tuple(t['point']))
    if path[hi][1] > .12:
        ax_plan.add_patch(Circle((path[hi][0], path[hi][2]), R, fill=False, ec='#e09a00', lw=1.5, ls='--'))
        ax_plan.plot(path[hi][0], path[hi][2], 'o', color='#e09a00', ms=6, label='腳最高處 %.3f m（第 %d 步）' % (path[hi][1], hi))
    ax_plan.add_patch(Circle((path[end][0], path[end][2]), R, fill=False, ec='#2a9d3a', lw=1.5))
    ax_plan.plot(path[end][0], path[end][2], 's', color='#2a9d3a', ms=5, label='400 步後停在 (%.2f, %.2f)' % (path[end][0], path[end][2]))
    ax_plan.set_xlim(-1.6, 1.8); ax_plan.set_ylim(-1.6, 1.8); ax_plan.set_aspect('equal'); ax_plan.grid(alpha=.25)
    ax_plan.set_title(title + '：平面（Unity x／z，m）', fontsize=11); ax_plan.legend(fontsize=7.5, loc='upper left')
    # section: the collision under the planned line and under the line the capsule actually took at its highest
    zz = [-1.6 + i * .005 for i in range(int(3.4 / .005))]
    ax_sec.fill_between(zz, [height(top, fx, z) for z in zz], color='#8a5a2b', alpha=.75, label='碰撞剖面，x = %.2f（預定）' % fx)
    if path[hi][1] > .12 and abs(path[hi][0] - fx) > .05:
        hx = path[hi][0]; ex = hx - (1 if hx > 0 else -1) * R * .97; ax_sec.plot(zz, [height(top, ex, z) for z in zz], color='#e09a00', lw=1.2, label='碰撞剖面，x = %.2f（膠囊靠模型那側邊緣，爬上處）' % ex)
    ax_sec.plot(zs, ys, color='#1f6fd1', lw=1.4, label='腳底高度')
    def capsule(z0, y0, col, ls):
        ax_sec.add_patch(Rectangle((z0 - R, y0 + R), 2 * R, H - 2 * R, fill=False, ec=col, lw=1.2, ls=ls))
        ax_sec.add_patch(Wedge((z0, y0 + R), R, 180, 360, fill=False, ec=col, lw=1.2, ls=ls))
    if t and t != 'none': capsule(t['capsule'][2], t['capsule'][1], '#d12f1f', '-'); ax_sec.plot(t['point'][2], t['point'][1], 'x', color='#d12f1f', ms=10, mew=2.5)
    if path[hi][1] > .12: capsule(path[hi][2], path[hi][1], '#e09a00', '--')
    ax_sec.axhline(.3, color='#999', lw=.8, ls=':'); ax_sec.text(-1.55, .31, 'stepOffset 0.3 m', fontsize=7, color='#666')
    ax_sec.set_xlim(-1.6, 1.8); ax_sec.set_ylim(0, 1.0); ax_sec.set_aspect('equal'); ax_sec.grid(alpha=.25)
    ax_sec.set_title('剖面（沿行走方向 z，高度 y，m）', fontsize=10); ax_sec.legend(fontsize=7, loc='upper right')


a, b, c, d, out = sys.argv[1:6]
fig, ax = plt.subplots(2, 2, figsize=(15, 12), gridspec_kw=dict(height_ratios=[3.4, 1.4]))
for k, (cf, tf, name) in enumerate(((a, b, '改前'), (c, d, '改後'))):
    tr = json.load(open(tf, encoding='utf-8'))
    panel(ax[0][k], ax[1][k], json.load(open(cf)), tr, name)
fig.suptitle('CR15_DitchCross 走動測試 x = 0.6 m：CharacterController 半徑 %.1f、高 %.2f、stepOffset %.1f、skin %.2f' % (tr['radius'], tr['height'], tr['stepOffset'], tr['skin']), fontsize=13)
fig.tight_layout(); fig.savefig(out, dpi=110)
