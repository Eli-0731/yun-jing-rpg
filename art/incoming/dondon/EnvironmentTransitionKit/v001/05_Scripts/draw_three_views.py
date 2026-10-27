"""Design three-view drawings (top / front / right side) for all 29 modules, straight from kit_spec.py.

Pure Python 3 + Pillow; no Blender, no modelling.  These are design drawings computed from the same
section functions the modelling scripts will use - not renders.  Small details (pebbles, grass cards)
are only shown as annotated zones.

Outputs (refuses to overwrite existing files):
  00_References/ThreeViews/<code>_<id>_3view.png        one sheet per module
  00_References/REF_A_Road_Edge_Sheet.png              numbered overview sheets
  00_References/REF_B_Riverbank_Sheet.png
  00_References/REF_C_Bridgehead_Sheet.png
  00_References/REF_D_Orthographic_Construction.png    representative three-views
  00_References/REF_E_Connector_Engineering.png        connector sections and geometry
Usage: python3 draw_three_views.py [--only A01,B03]
"""
import math, os, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit_spec as K

KIT = Path(__file__).resolve().parents[1]
OUT = KIT / '00_References'
SS = 2   # supersampling

FONT_CANDIDATES = ['/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', '/System/Library/Fonts/PingFang.ttc',
                   '/System/Library/Fonts/STHeiti Medium.ttc', '/Library/Fonts/Arial Unicode.ttf']
_fonts = {}


def font(size):
    if size not in _fonts:
        for p in FONT_CANDIDATES:
            if os.path.exists(p):
                _fonts[size] = ImageFont.truetype(p, size * SS); break
        else:
            _fonts[size] = ImageFont.load_default()
    return _fonts[size]


INK = (38, 44, 46); FAINT = (150, 156, 152); GRID = (120, 126, 122); BG = (244, 245, 241)
ENTRY = (34, 139, 87); EXIT = (196, 57, 43); SEAM = (222, 140, 30); WATER = (52, 120, 170); DECK = (110, 90, 160)
COL = {'dry': (178, 152, 119), 'gravel': (200, 186, 160), 'grass': (126, 152, 88), 'wet': (104, 86, 68), 'moss': (92, 126, 66)}


class Canvas:
    def __init__(self, w, h, bg=BG):
        self.w, self.h = w, h; self.im = Image.new('RGB', (w * SS, h * SS), bg); self.d = ImageDraw.Draw(self.im); self.clip = None

    def _p(self, p): return (p[0] * SS, p[1] * SS)

    def inside(self, p):
        c = self.clip
        return c is None or (c[0] - 0.5 <= p[0] <= c[2] + 0.5 and c[1] - 0.5 <= p[1] <= c[3] + 0.5)

    def _clipseg(self, a, b):
        if self.clip is None: return a, b
        x0, y0, x1, y1 = self.clip; t0, t1 = 0.0, 1.0; dx, dy = b[0] - a[0], b[1] - a[1]
        for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
            if p == 0:
                if q < 0: return None
            else:
                t = q / p
                if p < 0: t0 = max(t0, t)
                else: t1 = min(t1, t)
        if t0 > t1: return None
        return (a[0] + dx * t0, a[1] + dy * t0), (a[0] + dx * t1, a[1] + dy * t1)

    def line(self, pts, fill=INK, width=1.0, dash=None):
        if len(pts) < 2: return
        wd = max(1, int(round(width * SS)))
        if not dash and all(self.inside(p) for p in pts):
            self.d.line([self._p(p) for p in pts], fill=fill, width=wd, joint='curve'); return
        segs = []
        if not dash:
            segs = list(zip(pts, pts[1:]))
        else:
            on, off = dash; draw = True; left = on
            for a, b in zip(pts, pts[1:]):
                seg = math.dist(a, b); t = 0.0
                while seg > 0 and t < seg - 1e-9:
                    step = min(left, seg - t)
                    if draw:
                        segs.append(((a[0] + (b[0] - a[0]) * t / seg, a[1] + (b[1] - a[1]) * t / seg),
                                     (a[0] + (b[0] - a[0]) * (t + step) / seg, a[1] + (b[1] - a[1]) * (t + step) / seg)))
                    t += step; left -= step
                    if left <= 1e-9: draw = not draw; left = on if draw else off
        for a, b in segs:
            c = self._clipseg(a, b)
            if c: self.d.line([self._p(c[0]), self._p(c[1])], fill=fill, width=wd)

    def poly(self, pts, fill, outline=None, width=1.0):
        if not all(self.inside(p) for p in pts): return
        self.d.polygon([self._p(p) for p in pts], fill=fill, outline=outline, width=max(1, int(round(width * SS))) if outline else 0)

    def rect(self, box, fill=None, outline=INK, width=1.0):
        x0, x1 = sorted((box[0], box[2])); y0, y1 = sorted((box[1], box[3]))
        if self.clip:
            c = self.clip; x0, y0, x1, y1 = max(x0, c[0]), max(y0, c[1]), min(x1, c[2]), min(y1, c[3])
            if x0 >= x1 or y0 >= y1: return
        self.d.rectangle([x0 * SS, y0 * SS, x1 * SS, y1 * SS], fill=fill, outline=outline, width=max(1, int(round(width * SS))))

    def circle(self, c, r, fill=None, outline=INK, width=1.0):
        if not self.inside(c): return
        x, y = c
        self.d.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], fill=fill, outline=outline, width=max(1, int(round(width * SS))))

    def text(self, xy, s, size=14, fill=INK, anchor='la', halo=False):
        if not self.inside(xy): return
        kw = dict(stroke_width=3 * SS, stroke_fill=BG) if halo else {}
        self.d.text(self._p(xy), s, font=font(size), fill=fill, anchor=anchor, **kw)

    def text_w(self, s, size):
        return self.d.textlength(s, font=font(size)) / SS

    def wrap(self, xy, s, size, width_px, fill=INK, leading=1.45):
        x, y = xy; line = ''
        for ch in s:
            if self.text_w(line + ch, size) > width_px:
                self.text((x, y), line, size, fill); y += size * leading; line = ch.lstrip()
            else:
                line += ch
        if line: self.text((x, y), line, size, fill); y += size * leading
        return y

    def arrow(self, p, q, fill=INK, width=2.0, head=11.0):
        self.line([p, q], fill, width)
        ang = math.atan2(q[1] - p[1], q[0] - p[0])
        a = (q[0] - head * math.cos(ang - 0.42), q[1] - head * math.sin(ang - 0.42))
        b = (q[0] - head * math.cos(ang + 0.42), q[1] - head * math.sin(ang + 0.42))
        self.poly([q, a, b], fill)

    def save(self, path, size=None):
        path = Path(path)
        if path.exists(): raise SystemExit('EXISTS (not overwritten): %s' % path)
        path.parent.mkdir(parents=True, exist_ok=True)
        im = self.im.resize(size or (self.w, self.h), Image.LANCZOS); im.save(path, optimize=True); return im


class View:
    """Maps world (h, w) to canvas pixels with equal scale; w is vertically exaggerated by vex."""

    def __init__(self, cv, box, hc, wc, s, vex=1.0):
        self.cv, self.box, self.hc, self.wc, self.s, self.vex = cv, box, hc, wc, s, vex
        self.cx = (box[0] + box[2]) / 2; self.cy = (box[1] + box[3]) / 2

    def P(self, h, w):
        return (self.cx + (h - self.hc) * self.s, self.cy - (w - self.wc) * self.s * self.vex)


# ---- geometry evaluation ------------------------------------------------------------------------
def parts_of(mod):
    if mod['kind'] == 'c_base': return []
    if mod['kind'] == 'c_grid': return [K.Surface(mod, i) for i in range(len(mod['parts']))]
    return [K.Surface(mod)]


def fine(lst, n_per):
    out = []
    for a, b in zip(lst, lst[1:]):
        for k in range(n_per): out.append(a + (b - a) * k / n_per)
    out.append(lst[-1]); return out


def normal(sf, u, v, h=1e-4):
    x0, y0 = sf.xy(u - h, v); x1, y1 = sf.xy(u + h, v); du = (x1 - x0, y1 - y0, sf.z(u + h, v) - sf.z(u - h, v))
    x0, y0 = sf.xy(u, v - h); x1, y1 = sf.xy(u, v + h); dv = (x1 - x0, y1 - y0, sf.z(u, v + h) - sf.z(u, v - h))
    n = (du[1] * dv[2] - du[2] * dv[1], du[2] * dv[0] - du[0] * dv[2], du[0] * dv[1] - du[1] * dv[0])
    L = math.sqrt(sum(c * c for c in n)) or 1.0
    return tuple(c / L for c in n)


def colour(mask, z, n, faint=False):
    wet, grass, gravel, moss = mask
    c = list(COL['dry'])
    for key, f in (('gravel', gravel), ('wet', wet), ('grass', grass), ('moss', moss)):
        f = max(0.0, min(1.0, (f - 0.35) / 0.4)); c = [a + (b - a) * f for a, b in zip(c, COL[key])]
    L = (-0.45, 0.55, 0.70); ln = math.sqrt(sum(x * x for x in L)); d = sum(a * b / ln for a, b in zip(n, L))
    shade = 0.78 + 0.32 * d
    c = [x * shade for x in c]
    if z < K.WATER_Z:
        t = min(0.55, 0.3 + (K.WATER_Z - z) * 0.8); c = [a + (b - a) * t for a, b in zip(c, (122, 168, 190))]
    if faint:
        c = [a + (b - a) * 0.62 for a, b in zip(c, BG)]
    return tuple(int(max(0, min(255, x))) for x in c)


def bounds_of(mod, n_per=2):
    xs, ys, zs = [], [], []
    for sf in parts_of(mod):
        for u in fine(sf.us, n_per):
            for v in fine(sf.vs, n_per):
                x, y = sf.xy(u, v); xs.append(x); ys.append(y); zs.append(sf.z(u, v))
    if mod['kind'] == 'c_base':
        xs += [K.RAMP_L, K.BASE_FACE_X]; ys += [-K.DECK_HALF, K.DECK_HALF]; zs += [-0.55, K.DECK_BOTTOM]
    return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))


def draw_surface_plan(view, sf, faint=False, n_per=4, lattice=True, contours=None):
    cv = view.cv; us = fine(sf.us, n_per); vs = fine(sf.vs, n_per)
    for i in range(len(us) - 1):
        for j in range(len(vs) - 1):
            u0, u1, v0, v1 = us[i], us[i + 1], vs[j], vs[j + 1]; uc, vc = (u0 + u1) / 2, (v0 + v1) / 2
            col = colour(sf.mask(uc, vc), sf.z(uc, vc), normal(sf, uc, vc), faint)
            pts = [view.P(*sf.xy(u, v)) for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1))]
            cv.poly(pts, col, outline=col, width=0.6)
    if contours and not faint:
        grid = [[sf.z(u, v) for v in vs] for u in us]
        for level, colr, width, dash in contours:
            for i in range(len(us) - 1):
                for j in range(len(vs) - 1):
                    seg = march(us[i], us[i + 1], vs[j], vs[j + 1], grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1], level)
                    for (ua, va), (ub, vb) in seg:
                        cv.line([view.P(*sf.xy(ua, va)), view.P(*sf.xy(ub, vb))], colr, width, dash)
    if lattice and not faint:
        for u in sf.us: cv.line([view.P(*sf.xy(u, v)) for v in fine(sf.vs, 2)], (255, 255, 255), 0.5)
        for v in sf.vs: cv.line([view.P(*sf.xy(u, v)) for u in fine(sf.us, 2)], (255, 255, 255), 0.5)
    edge = [(u, sf.vs[0]) for u in fine(sf.us, 2)] + [(sf.us[-1], v) for v in fine(sf.vs, 2)] + \
           [(u, sf.vs[-1]) for u in fine(sf.us, 2)[::-1]] + [(sf.us[0], v) for v in fine(sf.vs, 2)[::-1]]
    cv.line([view.P(*sf.xy(u, v)) for u, v in edge], FAINT if faint else INK, 0.8 if faint else 1.6)


def march(u0, u1, v0, v1, a, b, c, d, lv):
    """Marching squares on one cell: corners a(u0,v0) b(u1,v0) c(u1,v1) d(u0,v1)."""
    pts = []
    def edge(p, q, zp, zq):
        t = (lv - zp) / (zq - zp); return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
    corners = [((u0, v0), a), ((u1, v0), b), ((u1, v1), c), ((u0, v1), d)]
    for k in range(4):
        (p, zp), (q, zq) = corners[k], corners[(k + 1) % 4]
        if (zp - lv) * (zq - lv) < 0: pts.append(edge(p, q, zp, zq))
    if len(pts) == 2: return [(pts[0], pts[1])]
    if len(pts) == 4:
        centre = (a + b + c + d) / 4
        return [(pts[0], pts[1]), (pts[2], pts[3])] if (centre - lv) * (a - lv) < 0 else [(pts[0], pts[3]), (pts[1], pts[2])]
    return []


# ---- annotations ------------------------------------------------------------------------------------
def dim(cv, p, q, off, text, size=13, colr=INK):
    """Dimension line between canvas points p, q offset perpendicular by off pixels."""
    dx, dy = q[0] - p[0], q[1] - p[1]; L = math.hypot(dx, dy) or 1.0; nx, ny = -dy / L * off, dx / L * off
    a = (p[0] + nx, p[1] + ny); b = (q[0] + nx, q[1] + ny)
    cv.line([p, (a[0] + nx * 0.15, a[1] + ny * 0.15)], colr, 0.7); cv.line([q, (b[0] + nx * 0.15, b[1] + ny * 0.15)], colr, 0.7)
    cv.arrow(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), a, colr, 1.0, 8); cv.arrow(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), b, colr, 1.0, 8)
    m = ((a[0] + b[0]) / 2 + nx * 0.35, (a[1] + b[1]) / 2 + ny * 0.35)
    cv.text(m, text, size, colr, 'mm')


def connector_arrows(view, mod, cons):
    cv = view.cv
    for c in cons:
        if c['role'] not in ('entry', 'exit'): continue
        vx = [p[0] for p in c['vertices']]; vy = [p[1] for p in c['vertices']]
        x, y = (min(vx) + max(vx)) / 2, (min(vy) + max(vy)) / 2; h = math.radians(c['heading_deg'])
        colr = ENTRY if c['role'] == 'entry' else EXIT
        if mod['kind'] in ('c_grid', 'c_base') and mod['id'] not in ('SM_Bridgehead_RoadTransition_A', 'SM_Bridgehead_BankTransition_A'):
            continue
        p0 = view.P(x - 0.55 * math.cos(h), y - 0.55 * math.sin(h)) if c['role'] == 'entry' else view.P(x, y)
        p1 = view.P(x, y) if c['role'] == 'entry' else view.P(x + 0.55 * math.cos(h), y + 0.55 * math.sin(h))
        cv.arrow(p0, p1, colr, 3.0, 14)
        lab = ('入口 ' if c['role'] == 'entry' else '出口 ') + c['type']
        tp = view.P(x + (0.62 if c['role'] == 'exit' else -0.62) * math.cos(h) - 0.25 * math.sin(h), y + (0.62 if c['role'] == 'exit' else -0.62) * math.sin(h) + 0.25 * math.cos(h))
        cv.text(tp, lab, 12, colr, 'mm', halo=True)
    for c in cons:   # highlight boundary vertex sequences
        colr = ENTRY if c['role'] == 'entry' else EXIT if c['role'] == 'exit' else SEAM
        pts = [view.P(p[0], p[1]) for p in c['vertices']]
        if len(pts) > 1 and c['type'] not in ('BRIDGE_SEAT',):
            cv.line(pts, colr, 3.2 if c['role'] != 'seam' else 2.2)
        for p in pts: cv.circle(p, 2.0, fill=colr, outline=colr)


def axes(cv, origin, labels=('+X', '+Y'), size=48):
    x, y = origin
    cv.arrow((x, y), (x + size, y), INK, 1.6, 9); cv.text((x + size + 6, y), labels[0], 13, INK, 'lm')
    cv.arrow((x, y), (x, y - size), INK, 1.6, 9); cv.text((x, y - size - 8), labels[1], 13, INK, 'mb')


# ---- per-module sheet -------------------------------------------------------------------------------
W, H = 2600, 1660
TOP_BOX = (50, 120, 1350, 900); SIDE_BOX = (50, 965, 1350, 1600); FRONT_BOX = (1420, 965, 2550, 1600); INFO_BOX = (1420, 120, 2550, 900)
C_CONTEXT = ['SM_Bridgehead_RoadTransition_A', 'SM_Bridgehead_BankTransition_A', 'SM_Bridgehead_SideTrim_L_A', 'SM_Bridgehead_SideTrim_R_A',
             'SM_Bridgehead_CornerCap_A', 'SM_Bridgehead_WaterEdge_A']
VEX = {'A': [20, 10, 5, 4, 3, 2, 1], 'B': [1], 'C': [4, 3, 2, 1.5, 1]}


def elevation_view(cv, box, h0, h1, z0, z1, group):
    """Independent elevation scale: fill the width, then the largest allowed vertical exaggeration that fits."""
    s = (box[2] - box[0] - 120) / (h1 - h0)
    vex = 1.0
    for cand in VEX[group]:
        if (z1 - z0) * cand * s <= (box[3] - box[1]) - 150: vex = cand; break
    else:
        s = ((box[3] - box[1]) - 150) / (z1 - z0)
    return View(cv, box, (h0 + h1) / 2, (z0 + z1) / 2 - 0.02 * (z1 - z0), s, vex)


def view_setup(mod):
    x0, x1, y0, y1, z0, z1 = bounds_of(mod)
    if mod['group'] == 'C' and mod['kind'] != 'c06':
        x0, x1, y0, y1 = min(x0, -0.3), max(x1, x0 + 2.5), min(y0, -1.0), max(y1, 1.0)
    m = 0.85
    px0, px1, py0, py1 = x0 - m, x1 + m, y0 - m, y1 + m
    zr = [z0, z1, 0.0]
    if mod['group'] in ('B', 'C') and z0 < -0.3: zr.append(K.WATER_Z)
    if mod['group'] == 'C' and mod['kind'] != 'c06': zr.append(K.DECK_Z); zr.append(K.DECK_BOTTOM)
    ez0, ez1 = min(zr) - 0.06, max(zr) + 0.08
    s = min((TOP_BOX[2] - TOP_BOX[0]) / (px1 - px0), (TOP_BOX[3] - TOP_BOX[1]) / (py1 - py0))
    return (px0, px1, py0, py1), (x0 - 0.3, x1 + 0.3, y0 - 0.3, y1 + 0.3, ez0, ez1), s


def section_lines(mod):
    """Front-view sections and side-view profiles as (label, colour, dash, [(u, v)...])."""
    k = mod['kind']; sf = parts_of(mod)[0]
    front, side = [], []
    L = sf.us[-1]
    front.append(('入口斷面 (u=0)', ENTRY, None, [(sf.us[0], v) for v in fine(sf.vs, 4)]))
    turned = bool(mod.get('turn'))
    if k in ('road_strip', 'road_full', 'bank', 'c06') and not turned:
        front.append(('出口斷面 (u=%.2f)' % L, EXIT, (7, 5), [(L, v) for v in fine(sf.vs, 4)]))
    var = mod.get('variant')
    if var in ('gentle', 'steep', 'eroded', 'damaged', 'stones', 'riprap', 'grassy') or k in ('road_end', 'bank_end'):
        um = {'gentle': 2.0, 'steep': 2.0, 'eroded': 2.1, 'damaged': 1.15}.get(var, 2.0)
        if k in ('road_end',): um = 3.0
        front.append(('中段斷面 (u=%.2f)' % um, (90, 90, 200), (3, 4), [(um, v) for v in fine(sf.vs, 4)]))
    if k.startswith('road'):
        if k == 'road_strip':
            sg = mod['side']; vs = [(1.5 * sg, '路緣 v=%+.2f' % (1.5 * sg), INK), (1.875 * sg, '收邊帶中線 v=%+.3f' % (1.875 * sg), (150, 110, 50)), (2.25 * sg, '外緣 v=%+.2f' % (2.25 * sg), FAINT)]
        else:
            vs = [(0.0, '中心線 v=0', INK), (0.75, '輪跡 v=+0.75', (120, 120, 120)), (1.875, '左收邊帶中線 v=+1.875', (150, 110, 50))]
    elif k.startswith('bank'):
        vs = [(1.0, '陸地外緣 v=+1.00', (90, 120, 70)), (0.0, '岸線 v=0', INK), (-1.0, '坡中 v=-1.00', (150, 110, 50)), (-2.0, '坡腳 v=-2.00', WATER)]
    else:
        vs = [(0.0, '中心線 y=0', INK), (1.5, '邊 y=+1.50', (150, 110, 50))]
    for v, lab, colr in vs:
        side.append((lab, colr, None, [(u, v) for u in fine(sf.us, 4)]))
    return front, side


def draw_profiles(view, sf, curves, mode, width=2.2):
    cv = view.cv
    for lab, colr, dash, uvs in curves:
        pts = []
        for u, v in uvs:
            x, y = sf.xy(u, v); z = sf.z(u, v)
            pts.append(view.P(-y, z) if mode == 'front' else view.P(x, z))
        cv.line(pts, colr, width, dash)


def ref_lines(view, mod, h0, h1):
    cv = view.cv; out = [(0.0, '地面 Z=0', FAINT, (6, 4))]
    if mod['group'] in ('B', 'C'): out.append((K.WATER_Z, '示意水位 -0.80', WATER, (10, 6)))
    if mod['group'] == 'C': out.append((K.DECK_Z, '測試橋面 +0.15', DECK, (10, 6)))
    for z, lab, colr, dash in out:
        a = view.P(h0, z); b = view.P(h1, z); cv.line([a, b], colr, 1.0, dash); cv.text((b[0] - 4, b[1] - 4), lab, 12, colr, 'rb', halo=True)


def spot_heights(view, mod):
    cv = view.cv; seen = set()
    for sf in parts_of(mod):
        pts = [(sf.us[0], sf.vs[0]), (sf.us[-1], sf.vs[0]), (sf.us[-1], sf.vs[-1]), (sf.us[0], sf.vs[-1]),
               (sf.us[len(sf.us) // 2], sf.vs[len(sf.vs) // 2])]
        if sf.kind in ('bank', 'bank_end'):
            uq = sf.us[int(len(sf.us) * 0.8)]
            pts += [(uq, 0.0), (uq, -1.0)]
        for u, v in pts:
            x, y = sf.xy(u, v); key = (round(x, 2), round(y, 2))
            if key in seen: continue
            seen.add(key); z = sf.z(u, v); p = view.P(x, y)
            cv.circle(p, 3.2, (255, 255, 255), INK, 1.0); cv.text((p[0] + 6, p[1] - 6), '%+.2f' % z, 12, (60, 60, 60), 'lb', halo=True)


def module_sheet(mod):
    cv = Canvas(W, H); cons = K.connectors(mod)
    (x0, x1, y0, y1), (bx0, bx1, by0, by1, z0, z1), s = view_setup(mod)
    top = View(cv, TOP_BOX, (x0 + x1) / 2, (y0 + y1) / 2, s)
    side = elevation_view(cv, SIDE_BOX, bx0, bx1, z0, z1, mod['group'])
    front = elevation_view(cv, FRONT_BOX, -by1, -by0, z0, z1, mod['group'])
    for box, title in ((TOP_BOX, '俯視圖 TOP（由上往下，+X 向右、+Y 向上）'), (SIDE_BOX, '右側視圖 SIDE（自 -Y 側看，X 向右）'),
                       (FRONT_BOX, '正視圖 FRONT（自入口沿 +X 看；圖左 = +Y）'), (INFO_BOX, '')):
        cv.rect(box, None, (200, 204, 198), 1.0)
        if title: cv.text((box[0] + 10, box[1] - 10), title, 15, INK, 'lb')
    # ---- top view (clipped to its box)
    cv.clip = TOP_BOX
    is_c = mod['group'] == 'C' and mod['kind'] != 'c06'
    if is_c:
        for cid in C_CONTEXT:
            if cid == mod['id']: continue
            for sf in parts_of(K.BY_ID[cid]): draw_surface_plan(top, sf, faint=True, n_per=2, lattice=False)
        if mod['id'] != 'SM_Bridgehead_Base_A':
            cv.poly([top.P(K.RAMP_L, -K.DECK_HALF), top.P(K.BASE_FACE_X, -K.DECK_HALF), top.P(K.BASE_FACE_X, K.DECK_HALF), top.P(K.RAMP_L, K.DECK_HALF)], (214, 212, 206), FAINT, 0.8)
    if mod['kind'] == 'road_strip':
        core = [top.P(0, -K.ROAD_HALF), top.P(4.0, -K.ROAD_HALF), top.P(4.0, K.ROAD_HALF), top.P(0, K.ROAD_HALF)]
        cv.poly(core, (226, 222, 214), FAINT, 1.0)
    for sf in parts_of(mod):
        draw_surface_plan(top, sf, contours=contour_levels(mod))
    if mod['kind'] == 'c_base':
        base_plan(top)
    if is_c:
        deck = [top.P(K.RAMP_L, -K.DECK_HALF), top.P(K.RAMP_L + 3.2, -K.DECK_HALF), top.P(K.RAMP_L + 3.2, K.DECK_HALF), top.P(K.RAMP_L, K.DECK_HALF)]
        cv.line(deck + [deck[0]], DECK, 1.6, (10, 6)); cv.text(top.P(K.RAMP_L + 2.0, -1.15), 'TEST_BridgeDeck_3m（測試用，不匯出）', 12, DECK, 'mm', halo=True)
    features(top, mod)
    connector_arrows(top, mod, cons)
    spot_heights(top, mod)
    plan_dims(top, mod)
    labels(top, mod)
    o = top.P(0.0, 0.0)
    if cv.inside(o):
        cv.line([(o[0] - 9, o[1]), (o[0] + 9, o[1])], INK, 1.4); cv.line([(o[0], o[1] - 9), (o[0], o[1] + 9)], INK, 1.4)
        cv.text((o[0] - 6, o[1] + 8), 'Pivot (0,0,0)', 12, INK, 'rt', halo=True)
    cv.clip = None
    axes(cv, (TOP_BOX[0] + 30, TOP_BOX[3] - 30))
    scale_bar(cv, top, (TOP_BOX[2] - 40 - 2 * top.s, TOP_BOX[3] - 28))
    # ---- side and front views
    for view, box, mode in ((side, SIDE_BOX, 'side'), (front, FRONT_BOX, 'front')):
        cv.clip = box
        if mod['kind'] == 'c_base':
            base_elevation(view, mode)
        else:
            fr, sd = section_lines(mod) if mod['kind'] != 'c_grid' else c_sections(mod)
            silhouette(view, mod, mode)
            for i, sf in enumerate(parts_of(mod)):
                curves = (fr if mode == 'front' else sd) if i == 0 else c_sections(mod, sf)[0 if mode == 'front' else 1]
                draw_profiles(view, sf, curves, mode)
        if is_c:
            if mode == 'side':
                a, b = view.P(K.RAMP_L, K.DECK_Z), view.P(K.RAMP_L + 3.2, K.DECK_BOTTOM)
            else:
                a, b = view.P(-K.DECK_HALF, K.DECK_Z), view.P(K.DECK_HALF, K.DECK_BOTTOM)
            cv.rect((a[0], a[1], b[0], b[1]), None, DECK, 1.0)
        ref_lines(view, mod, view.hc - (box[2] - box[0]) / 2 / view.s + 0.05, view.hc + (box[2] - box[0]) / 2 / view.s - 0.05)
        elevation_dims(view, mod, mode)
        cv.clip = None
        if mod['kind'] != 'c_base':
            legend(cv, (box[0] + 14, box[1] + 14), (fr if mode == 'front' else sd))
        cv.text((box[2] - 12, box[1] + 12), '水平 1 m = %.0f px；垂直比例 %s' % (view.s, ('×%g（放大）' % view.vex) if view.vex != 1 else '1:1（真實比例）'), 13,
                (150, 60, 40) if view.vex != 1 else INK, 'rt')
    cv.text((FRONT_BOX[0] + 14, FRONT_BOX[3] - 14), '左 L (+Y)', 13, INK, 'lb'); cv.text((FRONT_BOX[2] - 14, FRONT_BOX[3] - 14), '右 R (-Y)', 13, INK, 'rb')
    info_block(cv, mod, cons, top.s)
    cv.text((50, 40), '%s  %s' % (mod['code'], mod['id']), 30, INK, 'lm')
    cv.text((50, 82), '%s ｜ 設計三視圖（依 kit_spec.py 數值繪製，非渲染；尚未建模）' % mod['name_zh'], 18, (90, 96, 92), 'lm')
    cv.text((W - 50, 40), 'Environment Transition Kit %s' % K.KIT_VERSION, 16, (90, 96, 92), 'rm')
    return cv


def contour_levels(mod):
    g = mod['group']
    if g == 'A':
        lv = [((i * 0.02), (90, 70, 40), 0.7, None) for i in range(1, 16)] + [(-0.02, (90, 70, 40), 0.7, None), (-0.04, (90, 70, 40), 0.7, None)]
    elif g == 'B':
        lv = [(-0.1 * i, (70, 60, 50), 0.7, None) for i in range(1, 10) if abs(-0.1 * i - K.WATER_Z) > 1e-6]
        lv.append((K.WATER_Z, WATER, 1.8, None))
    else:
        lv = [(z, (70, 60, 50), 0.7, None) for z in (0.05, 0.10, -0.1, -0.2, -0.3, -0.4, -0.5, -0.6, -0.7, -0.9)]
        lv.append((K.WATER_Z, WATER, 1.8, None))
    return lv


def silhouette(view, mod, mode):
    for sf in parts_of(mod):
        pts = {}
        for u in fine(sf.us, 4):
            for v in fine(sf.vs, 4):
                x, y = sf.xy(u, v); z = sf.z(u, v)
                b = round((x if mode == 'side' else -y) / 0.04)
                pts[b] = max(pts.get(b, -9), z)
        view.cv.line([view.P(b * 0.04, z) for b, z in sorted(pts.items())], (175, 178, 172), 1.4, (2, 3))


def legend(cv, xy, curves):
    x, y = xy
    for lab, colr, dash, _ in curves:
        cv.line([(x, y + 8), (x + 34, y + 8)], colr, 2.2, dash); cv.text((x + 42, y + 8), lab, 12, INK, 'lm'); y += 22
    cv.line([(x, y + 8), (x + 34, y + 8)], (175, 178, 172), 1.4, (2, 3)); cv.text((x + 42, y + 8), '外輪廓（最高點投影）', 12, INK, 'lm')


def scale_bar(cv, view, xy):
    x, y = xy; L = view.s
    for i in range(2):
        cv.rect((x + i * L, y - 6, x + (i + 1) * L, y), INK if i % 2 == 0 else BG, INK, 0.8)
    cv.text((x, y - 10), '0', 11, INK, 'mb'); cv.text((x + L, y - 10), '1', 11, INK, 'mb'); cv.text((x + 2 * L, y - 10), '2 m', 11, INK, 'mb')


def labels(view, mod):
    cv = view.cv; k = mod['kind']
    if k.startswith('bank'):
        sf = parts_of(mod)[0]; um = sf.us[len(sf.us) // 2]
        cv.text(view.P(*sf.xy(um, 0.62)), '陸地 LAND（Z = 0）', 15, (40, 70, 30), 'mm', halo=True)
        cv.text(view.P(*sf.xy(um, -1.72)), '水側 WATER', 15, WATER, 'mm', halo=True)
        cv.text(view.P(*sf.xy(um * 0.6, 0.0)), '岸線 v=0', 11, INK, 'mm', halo=True)
    if k in ('road_full', 'road_end'):
        sf = parts_of(mod)[0]; cv.text(view.P(*sf.xy(sf.us[len(sf.us) // 2] * (0.6 if k == 'road_end' else 1), 0.0)), '路面 3.00 m', 13, INK, 'mm', halo=True)
    if k == 'road_strip':
        sf = parts_of(mod)[0]; cv.text(view.P(*sf.xy(2.0, mod['side'] * 0.9)), 'TEST_RoadCore_3m 路芯位置（測試用，不屬於本模組）', 12, (110, 116, 112), 'mm', halo=True)


def plan_dims(view, mod):
    cv = view.cv; k = mod['kind']; P = view.P
    if k in ('road_strip', 'road_full', 'road_end', 'bank', 'bank_end'):
        sf = parts_of(mod)[0]; L = sf.L; v_lo, v_hi = sf.vs[0], sf.vs[-1]
        if not mod.get('turn'):
            dim(cv, P(0, v_lo), P(L, v_lo), 34, '%.2f m' % L)
            o1 = -(0.62 * view.s + 70); o2 = o1 - 56
            dim(cv, P(L, v_hi), P(L, v_lo), o1, '%.2f m' % (v_hi - v_lo))
            if k in ('road_full', 'road_end'):
                dim(cv, P(L, K.ROAD_HALF), P(L, -K.ROAD_HALF), o2, '3.00 路面')
                dim(cv, P(L, K.ROAD_OUTER), P(L, K.ROAD_HALF), o2, '0.75')
            if k.startswith('bank'):
                dim(cv, P(L, 1.0), P(L, 0.0), o2, '1.00'); dim(cv, P(L, 0.0), P(L, -2.0), o2, '2.00')
        else:
            p = sf.path; R = p.R
            cx, cy = (0.0, R) if p.turn > 0 else (0.0, -R)
            if R < 4:
                ex, ey = p.centre(L)
                cv.line([P(cx, cy), P(0, 0)], FAINT, 0.8, (4, 4)); cv.line([P(cx, cy), P(ex, ey)], FAINT, 0.8, (4, 4))
                cv.circle(P(cx, cy), 3, FAINT, FAINT); cv.text(P(cx, cy), ' 圓心', 11, FAINT, 'lm', halo=True)
    elif k == 'c06':
        dim(cv, P(0, -1.5), P(1.5, -1.5), 34, '1.50 m'); dim(cv, P(0, 1.5), P(0, -1.5), 46, '3.00 m')
    elif k == 'c_grid':
        for sf in parts_of(mod):
            x0, x1, ya, yb = sf.rect
            edge = ya if ya < 0 else yb
            off = 0.62 * view.s + 40 if any(c['role'] in ('entry', 'exit') and abs(c['vertices'][0][1] - edge) < 1e-6 and abs(c['vertices'][-1][1] - edge) < 1e-6 for c in K.connectors(mod)) else 30
            dim(cv, P(x0, edge), P(x1, edge), off if ya < 0 else -off, '%.2f' % (x1 - x0), 12)
            dim(cv, P(x0, ya), P(x0, yb), -(0.55 * view.s + 60), '%.2f' % (yb - ya), 12)


def features(view, mod):
    cv = view.cv; P = view.P; var = mod.get('variant'); k = mod['kind']
    if not parts_of(mod): return
    sf = parts_of(mod)[0]
    def zone(u0, u1, v0, v1, colr, text, hatch=True):
        pts = [P(*sf.xy(u, v0)) for u in fine([u0, u1], 8)] + [P(*sf.xy(u1, v)) for v in fine([v0, v1], 6)] + \
              [P(*sf.xy(u, v1)) for u in fine([u1, u0], 8)] + [P(*sf.xy(u0, v)) for v in fine([v1, v0], 6)]
        cv.line(pts + [pts[0]], colr, 1.6, (6, 4))
        if hatch:
            for t in fine([0.0, 1.0], 10)[1:-1]:
                a = P(*sf.xy(u0 + (u1 - u0) * t, v0)); b = P(*sf.xy(u0 + (u1 - u0) * max(0, t - 0.15), v1)); cv.line([a, b], colr, 0.6)
        cv.text(P(*sf.xy(u0 + 0.08, v0 - 0.06)), text, 12, colr, 'lt', halo=True)
    if var == 'damaged':
        for s_, v, r, d in K.POTHOLES:
            c = P(s_, v); cv.circle(c, r * view.s, None, (150, 40, 30), 1.6); cv.text(c, '坑 -%d cm' % round(d * 100), 11, (150, 40, 30), 'mm', halo=True)
        for s_, v, r in K.CHIPS:
            c = P(s_, v); cv.circle(c, r * view.s, None, (150, 90, 30), 1.2); cv.text((c[0], c[1] - r * view.s - 4), '缺角（土埂破損）', 11, (150, 90, 30), 'mb', halo=True)
        zone(0.7, 3.4, -1.2, 1.2, (110, 60, 50), '裂紋貼片區（3 mm 細條）', hatch=False)
    if var == 'grass': cv.text(P(3.3, 0.0), '→ 出口為草地小徑 GRASS_PATH', 13, (40, 90, 30), 'mm', halo=True)
    if var == 'gravel': cv.text(P(3.3, 0.0), '→ 出口為碎石路 GRAVEL_PATH', 13, (110, 100, 80), 'mm', halo=True)
    if var == 'stones': zone(0.5, 3.5, -1.4, 0.4, (70, 76, 96), '風化小石＋苔蘚分布區')
    if var == 'steep': zone(0.9, 3.1, -1.05, -0.15, (70, 76, 96), '露岩帶（岩面朝水側）')
    if var == 'riprap':
        for row, (v0, v1) in enumerate(((-0.25, 0.1), (-0.75, -0.4), (-1.3, -0.95))):
            for i in range(9):
                u = 0.45 + i * 0.39 + (0.19 if row % 2 else 0)
                if u + 0.17 > 3.75: continue
                pts = [P(*sf.xy(uu, vv)) for uu, vv in ((u - 0.17, v0), (u + 0.17, v0), (u + 0.17, v1), (u - 0.17, v1))]
                cv.poly(pts, (150, 152, 150), INK, 0.8)
        cv.text(P(2.0, 0.42), '護岸石塊三排（離兩端接頭面 ≥ 0.28 m）', 12, INK, 'mm', halo=True)
    if var == 'grassy':
        zone(0.4, 3.6, -0.9, 0.95, (40, 90, 30), '密草層（DET_Grass，可關閉）', hatch=False)
        cv.line([P(u, 0.02) for u in fine([0.5, 3.5], 10)], (40, 90, 30), 3.0); cv.text(P(2.0, -0.14), '草皮懸邊 SodLip', 12, (40, 90, 30), 'mt', halo=True)
    if var == 'eroded':
        for sc, hw, d in K.RILLS:
            cv.line([P(sc, 0.15), P(sc, -1.35)], (120, 70, 40), 2.4); cv.text(P(sc, 0.3), '細溝 -%d cm' % round(d * 100), 11, (120, 70, 40), 'mb', halo=True)
            cv.circle(P(sc, -1.6), hw * 1.6 * view.s, None, (150, 110, 60), 1.0)
        cv.text(P(2.0, -1.95), '坡腳崩土扇 +6 cm', 11, (150, 110, 60), 'mt', halo=True)
    if k == 'bank_end': cv.text(P(3.3, -1.0), '高差在 4 m 內消失 →', 13, INK, 'mm', halo=True)
    if k == 'road_end': cv.text(P(*sf.xy(K.END_CAP_S, -0.3)), '收口圓心 (1.75, 0)', 11, INK, 'mt', halo=True)
    if mod['id'] == 'SM_Bridgehead_CornerCap_A':
        for sg in (1, -1):
            for i in range(5):
                x = K.RAMP_L + 0.05 + i * 0.24; cv.poly([P(x, sg * 1.5), P(x + 0.22, sg * 1.5), P(x + 0.22, sg * 1.7), P(x, sg * 1.7)], (150, 152, 150), INK, 0.8)
            cv.text(P(2.6, sg * 2.0), '封邊石', 11, INK, 'mm', halo=True)
    if mod['id'] == 'SM_Bridgehead_WaterEdge_A': cv.text(P(4.1, 0.0), '濕泥碎石沖刷帶', 13, (60, 50, 40), 'mm', halo=True)
    if mod['id'] in ('SM_Bridgehead_SideTrim_L_A', 'SM_Bridgehead_SideTrim_R_A'):
        sg = 1 if mod['id'].endswith('L_A') else -1; cv.text(P(1.0, sg * 2.62), '草坡＋散石', 12, (40, 90, 30), 'mm', halo=True)


def base_plan(view, label=True):
    cv = view.cv; P = view.P
    cv.poly([P(K.RAMP_L, -1.5), P(K.BASE_FACE_X, -1.5), P(K.BASE_FACE_X, 1.5), P(K.RAMP_L, 1.5)], (168, 170, 168), INK, 1.6)
    y = -1.5
    for w in (0.62, 0.55, 0.7, 0.48, 0.65):
        cv.line([P(K.RAMP_L, y + w), P(K.BASE_FACE_X, y + w)], INK, 0.8); y += w
    if label: cv.text(P(2.62, 0), '石基頂 Z = -0.05', 13, INK, 'mm', halo=True)


def base_elevation(view, mode):
    cv = view.cv
    if mode == 'side':
        h0, h1 = K.RAMP_L, K.BASE_FACE_X; ctx = [(x, K.c_H(x, 0.0)) for x in fine([K.BASE_FACE_X, K.BH_RIVER_X], 20)]
    else:
        h0, h1 = -1.5, 1.5; ctx = [(-y, K.c_H(K.BASE_FACE_X, y)) for y in fine([-2.25, 2.25], 30)]
    a = view.P(h0, K.DECK_BOTTOM); b = view.P(h1, -0.55); cv.rect((a[0], a[1], b[0], b[1]), (190, 192, 188), INK, 1.6)
    cv.line([view.P(h0, -0.30), view.P(h1, -0.30)], INK, 0.9)
    cv.line([view.P(h, z) for h, z in ctx], (150, 110, 50), 1.8, (6, 4))
    cv.text(view.P((h0 + h1) / 2, -0.62), '兩層砌石，頂 -0.05、底 -0.55', 12, INK, 'mt', halo=True)
    cv.text(view.P(ctx[len(ctx) // 2][0], ctx[len(ctx) // 2][1] - 0.04), '前方 C08 地形（虛線）', 11, (150, 110, 50), 'mt', halo=True)


def c_sections(mod, sf=None):
    sf = sf or parts_of(mod)[0]; x0, x1, y0, y1 = sf.rect
    ym = (y0 + y1) / 2; yo = y1 if y1 > 0 else y0
    fr = [('X = %.2f 斷面' % x0, ENTRY, None, [(x0, v) for v in fine(sf.vs, 4)]),
          ('X = %.2f 斷面' % x1, EXIT, (7, 5), [(x1, v) for v in fine(sf.vs, 4)])]
    sd = [('Y = %+.2f 縱斷面' % ym, INK, None, [(u, ym) for u in fine(sf.us, 4)]),
          ('Y = %+.2f 縱斷面' % yo, (150, 110, 50), (7, 5), [(u, yo) for u in fine(sf.us, 4)])]
    if mod['id'] == 'SM_Bridgehead_RoadTransition_A':
        sd = [('中心線 Y=0', INK, None, [(u, 0.0) for u in fine(sf.us, 4)]), ('收邊帶 Y=+1.875', (150, 110, 50), (7, 5), [(u, 1.875) for u in fine(sf.us, 4)])]
    return fr, sd


def elevation_dims(view, mod, mode):
    cv = view.cv; k = mod['kind']; P = view.P
    if mode == 'side':
        if k == 'road_full' and mod.get('rise'):
            dim(cv, P(4.0, 0.0), P(4.0, 0.2), -40, '+0.20（坡度最大 7.5%）')
        if mod['id'] == 'SM_Bridgehead_RoadTransition_A':
            dim(cv, P(2.0, 0.0), P(2.0, K.DECK_Z), -40, '+0.15'); dim(cv, P(0.0, 0.0), P(2.0, 0.0), 40, '2.00 m 緩坡（最大 11%）')
        if k == 'c06':
            dim(cv, P(0.0, 0.0), P(0.0, K.DECK_Z), 40, '+0.15'); dim(cv, P(0.0, 0.0), P(1.5, 0.0), 40, '1.50 m')
        if k in ('road_strip', 'road_full', 'road_end', 'bank', 'bank_end') and not mod.get('turn'):
            dim(cv, P(0.0, view.wc - 0.48 * (view.box[3] - view.box[1]) / (view.s * view.vex) + 0.02), P(mod.get('length', 4.0), view.wc - 0.48 * (view.box[3] - view.box[1]) / (view.s * view.vex) + 0.02), -20, '%.2f m' % mod.get('length', 4.0), 12)
        return
    if k.startswith('bank'):
        dim(cv, P(-1.0, 0.0), P(0.0, 0.0), -30, '1.00 陸地')
        dim(cv, P(0.0, K.BANK_TOE_Z), P(2.0, K.BANK_TOE_Z), 36, '2.00 坡')
        dim(cv, P(2.0, 0.0), P(2.0, K.BANK_TOE_Z), -46, '1.00')
    if k in ('road_strip', 'road_full', 'road_end'):
        if k != 'road_strip':
            dim(cv, P(-1.5, 0.0), P(1.5, 0.0), 44, '3.00 路面')
            dim(cv, P(-2.25, 0.0), P(-1.5, 0.0), 44, '0.75'); dim(cv, P(1.5, 0.0), P(2.25, 0.0), 44, '0.75')
            hh = -1.875
        else:
            sg = mod['side']; dim(cv, P(-1.5 * sg, 0.0), P(-2.25 * sg, 0.0), 44 * sg, '0.75 收邊帶'); hh = -1.875 * sg
        cv.text(P(hh, K.VERGE_H + 0.012), '土埂 4 cm', 11, (150, 110, 50), 'mb', halo=True)


def info_block(cv, mod, cons, s):
    x0, y0, x1, y1 = INFO_BOX; x = x0 + 22; y = y0 + 22
    cv.text((x, y), '%s　%s' % (mod['code'], mod['name_zh']), 24, INK, 'lt'); y += 44
    y = cv.wrap((x, y), '用途：' + mod['purpose'], 15, x1 - x0 - 44) + 6
    if mod.get('turn'):
        sf = parts_of(mod)[0]; p = sf.path; (ex, ey, ez), hd = K.exit_transform(mod)
        y = cv.wrap((x, y), '幾何：%s 弧長 %.2f m、半徑 R = %.3f m、轉角 %d°；出口位置 (%.3f, %.3f, %.3f)，出口朝向 %+.1f°。' % (
            '中心線' if mod['group'] == 'A' else '岸線', p.L, p.R, round(abs(math.degrees(p.turn))), ex, ey, ez, hd), 15, x1 - x0 - 44) + 6
    b = bounds_of(mod, 4)
    cv.text((x, y), '外形範圍（模組座標，細節前）  X %.2f～%.2f　Y %.2f～%.2f　Z %.2f～%.2f' % b, 14, INK, 'lt'); y += 26
    parts = parts_of(mod)
    if parts:
        tris = sum((len(p.us) - 1) * (len(p.vs) - 1) * 2 for p in parts)
        cv.text((x, y), '地表格點：%s　LOD0 地表約 %d 三角面（細節另計）　預算 %d–%d' % (' + '.join('%d×%d' % (len(p.us), len(p.vs)) for p in parts), tris, *K.tri_budget(mod)), 14, INK, 'lt'); y += 26
    else:
        cv.text((x, y), '石基：兩層砌石塊，預估 600–1,400 三角面', 14, INK, 'lt'); y += 26
    y += 6
    cv.text((x, y), '接頭（模組座標；誤差目標 ≤ 1 mm）', 16, INK, 'lt'); y += 28
    cols = [x, x + 200, x + 520, x + 790, x + 880]
    for c, t in zip(cols, ['名稱', '類型', '位置 (x, y, z)', '朝向', '頂點']): cv.text((c, y), t, 13, (90, 96, 92), 'lt')
    y += 22
    for c in cons:
        colr = ENTRY if c['role'] == 'entry' else EXIT if c['role'] == 'exit' else SEAM
        row = [c['name'], c['type'] + (' / ' + c['surface_variant'] if c.get('surface_variant') else ''), '(%.3f, %.3f, %.3f)' % tuple(c['location']), '%+.1f°' % c['heading_deg'], str(len(c['vertices']))]
        for cc, t in zip(cols, row): cv.text((cc, y), t, 12, colr if cc == cols[0] else INK, 'lt')
        y += 20
    y += 12
    notes = '圖例：綠＝入口接頭，紅＝出口接頭，橘＝內部接縫（圓點＝接頭頂點）；白細線＝實際網格格點；棕細線＝等高線（A 每 2 cm、B 每 10 cm、C 每 5–10 cm），藍粗線＝示意水位 -0.80 m；白圈數字＝該點高程 (m)。俯視著色依材質遮罩（乾土／碎石／草／濕土）與高程陰影。'
    y = cv.wrap((x, y), notes, 13, x1 - x0 - 44, (90, 96, 92))
    cv.wrap((x, y + 4), '俯視比例：1 m = %.0f px。小石、草片、苔蘚等細節在建模階段才加入，且不會改變接頭邊界。' % s, 13, x1 - x0 - 44, (90, 96, 92))


# ---- overview sheets --------------------------------------------------------------------------------
def overview(group, title, path, cols=4):
    mods = [m for m in K.MODULES if m['group'] == group]
    cell_w, cell_h = 620, 560; rows = math.ceil(len(mods) / cols)
    extra = 900 if group == 'C' else 0
    cv = Canvas(cols * cell_w + 60, rows * cell_h + 150 + extra)
    cv.text((30, 40), title, 30, INK, 'lm')
    cv.text((30, 84), '依 kit_spec.py 數值繪製的設計平面（非渲染，尚未建模）。綠箭頭＝入口、紅箭頭＝出口；格內標示 ID、外形尺寸、接頭類型。', 16, (90, 96, 92), 'lm')
    for i, mod in enumerate(mods):
        cx = 30 + (i % cols) * cell_w; cy = 120 + (i // cols) * cell_h
        cv.rect((cx, cy, cx + cell_w - 20, cy + cell_h - 20), (250, 250, 247), (205, 208, 202), 1.0)
        x0, x1, y0, y1, z0, z1 = bounds_of(mod)
        if mod['kind'] == 'c_base': x0, x1, y0, y1 = K.RAMP_L, K.BASE_FACE_X, -1.5, 1.5
        m = 0.75; box = (cx + 10, cy + 70, cx + cell_w - 30, cy + cell_h - 70)
        s = min((box[2] - box[0]) / (x1 - x0 + 2 * m), (box[3] - box[1]) / (y1 - y0 + 2 * m))
        v = View(cv, box, (x0 + x1) / 2, (y0 + y1) / 2, s)
        cv.clip = (cx + 2, cy + 60, cx + cell_w - 22, cy + cell_h - 64)
        for sf in parts_of(mod): draw_surface_plan(v, sf, n_per=2, contours=None)
        if mod['kind'] == 'c_base': base_plan(v)
        connector_arrows(v, mod, K.connectors(mod))
        cv.clip = None
        cv.text((cx + 14, cy + 18), '%s  %s' % (mod['code'], mod['name_zh']), 20, INK, 'lt')
        cv.text((cx + 14, cy + 46), mod['id'], 13, (90, 96, 92), 'lt')
        cons = K.connectors(mod); types = ' → '.join(dict.fromkeys(c['type'] for c in cons if c['role'] in ('entry', 'exit')))
        cv.text((cx + 14, cy + cell_h - 58), '外形 %.2f × %.2f m，Z %.2f～%.2f' % (x1 - x0, y1 - y0, z0, z1), 13, INK, 'lt')
        cv.text((cx + 14, cy + cell_h - 38), types, 12, (90, 96, 92), 'lt')
    if group == 'C':
        y0 = 120 + rows * cell_h + 10
        cv.text((30, y0 + 20), '組裝平面：C01–C05、C07、C08 共用橋頭座標系，同一變換即可組成橋頭；C02 兩端接 B 類河岸；C06 為獨立短坡。', 18, INK, 'lt')
        box = (40, y0 + 60, cols * cell_w + 20, y0 + extra - 20)
        s = min((box[2] - box[0]) / 13.0, (box[3] - box[1]) / 11.2)
        v = View(cv, box, 3.4, 0.0, s)
        for cid in C_CONTEXT:
            for sf in parts_of(K.BY_ID[cid]): draw_surface_plan(v, sf, n_per=2, lattice=False)
        base_plan(v)
        for ysign in (1, -1):   # neighbouring B modules in faint
            pts = []
            for (bx, by) in ((K.BANK_LINE_X - 1.0, ysign * 4.0), (K.BANK_LINE_X + 2.0, ysign * 4.0), (K.BANK_LINE_X + 2.0, ysign * 5.5), (K.BANK_LINE_X - 1.0, ysign * 5.5)):
                pts.append(v.P(bx, by))
            cv.poly(pts, (226, 228, 224), FAINT, 1.0); cv.text(v.P(K.BANK_LINE_X + 0.5, ysign * 4.75), 'B 類河岸（例：B01）', 14, FAINT, 'mm')
        cv.poly([v.P(-4.0, -2.25), v.P(0.0, -2.25), v.P(0.0, 2.25), v.P(-4.0, 2.25)], (226, 228, 224), FAINT, 1.0); cv.text(v.P(-2.0, 0.0), 'A 類道路（例：A01＋路芯＋A02）', 14, FAINT, 'mm')
        deck = [v.P(K.RAMP_L, -1.5), v.P(K.RAMP_L + 6.5, -1.5), v.P(K.RAMP_L + 6.5, 1.5), v.P(K.RAMP_L, 1.5)]
        cv.line(deck + [deck[0]], DECK, 2.0, (10, 6)); cv.text(v.P(K.RAMP_L + 5.2, 0.0), 'TEST_BridgeDeck_3m', 15, DECK, 'mm')
        for cid, (lx, ly) in {'C01': (1.0, 0.0), 'C02': (3.9, 3.1), 'C03': (1.0, 2.62), 'C04': (1.0, -2.62), 'C05': (2.62, 0.75), 'C07': (2.62, 1.87), 'C08': (4.3, -0.9)}.items():
            cv.text(v.P(lx, ly), cid, 16, INK, 'mm')
        cv.text(v.P(3.9, -3.1), 'C02', 16, INK, 'mm'); cv.text(v.P(2.62, -1.87), 'C07', 16, INK, 'mm')
        for c in K.connectors(K.BY_ID['SM_Bridgehead_BankTransition_A']) + K.connectors(K.BY_ID['SM_Bridgehead_RoadTransition_A']):
            if c['role'] in ('entry', 'exit'):
                colr = ENTRY if c['role'] == 'entry' else EXIT
                cv.line([v.P(p[0], p[1]) for p in c['vertices']], colr, 3.0)
        axes(cv, (box[0] + 30, box[3] - 30))
    return cv.save(path)


# ---- connector engineering sheet ----------------------------------------------------------------
def connector_sheet(path):
    cv = Canvas(3000, 2200)
    cv.text((40, 44), 'REF_E 接頭工程圖：標準斷面、出口位姿、組裝方向（數值來自 kit_spec.py）', 30, INK, 'lm')
    def panel(box, title):
        cv.rect(box, (250, 250, 247), (205, 208, 202), 1.0); cv.text((box[0] + 14, box[1] + 14), title, 18, INK, 'lt')
    # ROAD_3M section
    box = (40, 100, 1480, 620); panel(box, 'ROAD_3M 道路斷面（垂直 ×8）：路面 3.00 m＋兩側 0.75 m 收邊帶，25 個接頭頂點')
    v = View(cv, box, 0.0, 0.03, 290, 8)
    cv.line([v.P(-y, K.road_z(y)) for y in fine(K.ROAD_V, 6)], INK, 2.4)
    for y in K.ROAD_V: cv.circle(v.P(-y, K.road_z(y)), 4, ENTRY, ENTRY)
    dim(cv, v.P(-1.5, 0), v.P(1.5, 0), 60, '3.00 m 路面  Z = 0', 15); dim(cv, v.P(-2.25, 0), v.P(-1.5, 0), 60, '0.75', 15); dim(cv, v.P(1.5, 0), v.P(2.25, 0), 60, '0.75', 15)
    cv.text(v.P(1.875, 0.075), '左 +Y 收邊帶（A01 = ROAD_EDGE_L，7 點）', 14, INK, 'mb'); cv.text(v.P(-1.875, 0.075), '右 -Y 收邊帶（A02 = ROAD_EDGE_R，7 點）', 14, INK, 'mb')
    cv.text(v.P(0.0, 0.02), 'TEST_RoadCore_3m：13 點，間距 0.25（不匯出）', 14, FAINT, 'mb')
    dim(cv, v.P(-1.875, 0), v.P(-1.875, K.VERGE_H), -30, '4 cm', 13)
    # BANK section
    box = (1520, 100, 2960, 620); panel(box, 'BANK_0_TO_MINUS_0P8 河岸斷面（1:1）：陸地 1.00 m、岸線、坡腳 -1.00 m，25 個頂點')
    v = View(cv, box, 0.5, -0.45, 330, 1)
    cv.line([v.P(-y, K.bank_z(y)) for y in fine(K.BANK_V, 6)], INK, 2.4)
    for y in K.BANK_V: cv.circle(v.P(-y, K.bank_z(y)), 4, ENTRY, ENTRY)
    cv.line([v.P(-1.2, K.WATER_Z), v.P(2.2, K.WATER_Z)], WATER, 1.6, (10, 6)); cv.text(v.P(2.2, K.WATER_Z + 0.03), '示意水位 -0.80（距岸線 %.2f m）' % -K.waterline_v(), 14, WATER, 'rb')
    cv.text(v.P(-0.5, 0.06), '陸地 LAND +Y', 15, (40, 70, 30), 'mb'); cv.text(v.P(1.6, -0.45), '水側 WATER -Y', 15, WATER, 'mm')
    dim(cv, v.P(-1.0, 0), v.P(0.0, 0), -40, '1.00', 14); dim(cv, v.P(0.0, -1.0), v.P(2.0, -1.0), 40, '2.00', 14); dim(cv, v.P(2.0, 0.0), v.P(2.0, -1.0), -40, '1.00', 14)
    # Bridge ramp profile
    box = (40, 660, 1480, 1100); panel(box, 'BRIDGE_3M：C01 道路 0 → 測試橋面 +0.15（2.00 m smoothstep，垂直 ×6）；C06 短坡 +0.15 → 0（1.50 m）')
    v = View(cv, box, 3.1, 0.05, 200, 6)
    cv.line([v.P(x, K.c_H(x, 0.0)) for x in fine([0.0, 2.0], 60)], INK, 2.6)
    cv.rect((v.P(2.0, K.DECK_Z)[0], v.P(2.0, K.DECK_Z)[1], v.P(4.4, K.DECK_BOTTOM)[0], v.P(4.4, K.DECK_BOTTOM)[1]), None, DECK, 1.6)
    cv.text(v.P(3.2, 0.05), 'TEST_BridgeDeck_3m（厚 0.20）', 14, DECK, 'mm')
    cv.line([v.P(x + 4.6, K.c06_z(x, 0)) for x in fine([0.0, 1.5], 40)], (120, 100, 60), 2.4); cv.text(v.P(5.35, 0.12), 'C06（另一座標系）', 13, (120, 100, 60), 'mm')
    dim(cv, v.P(0, 0), v.P(2.0, 0), 40, '2.00 m', 14); dim(cv, v.P(2.0, 0), v.P(2.0, K.DECK_Z), -34, '+0.15', 14)
    cv.line([v.P(-0.2, 0), v.P(6.4, 0)], FAINT, 1.0, (6, 4))
    # Curve exits
    box = (1520, 660, 2960, 1480); panel(box, '彎道出口位姿（中心線弧長 4.00 m）與河岸轉角（岸線弧長 4.00 m）')
    v = View(cv, box, -1.05, 0.0, 120, 1)
    rows = []
    for mid, colr in (('SM_RoadEdge_Curve_L_A', (40, 120, 70)), ('SM_RoadEdge_Curve_R_A', (40, 120, 70)), ('SM_RoadEdge_WideCurve_L_A', (160, 80, 40)), ('SM_RoadEdge_WideCurve_R_A', (160, 80, 40)),
                       ('SM_Riverbank_InnerCorner_A', WATER), ('SM_Riverbank_OuterCorner_A', (90, 120, 70))):
        mod = K.BY_ID[mid]; sf = K.Surface(mod); p = sf.path
        cv.line([v.P(*p.centre(s)) for s in fine([0.0, p.L], 40)], colr, 2.4)
        (ex, ey, ez), hd = K.exit_transform(mod)
        cv.arrow(v.P(ex, ey), v.P(ex + 0.5 * math.cos(math.radians(hd)), ey + 0.5 * math.sin(math.radians(hd))), EXIT, 2.0, 10)
        rows.append((mod['code'], mod['name_zh'], ex, ey, hd, p.R))
    cv.line([v.P(0, 0), v.P(4.0, 0)], INK, 2.0, (8, 5)); cv.arrow(v.P(-0.6, 0), v.P(0, 0), ENTRY, 2.6, 12); cv.text(v.P(-0.65, 0.25), '入口 (0,0,0) +X', 14, ENTRY, 'rm')
    y = box[1] + 70
    for code, name, ex, ey, hd, R in rows:
        cv.text((box[0] + 24, y), '%s %s' % (code, name), 15, INK, 'lt')
        cv.text((box[0] + 24, y + 22), '出口 (%.3f, %.3f)  朝向 %+.1f°  R = %.3f m' % (ex, ey, hd, R), 14, (90, 96, 92), 'lt'); y += 56
    cv.wrap((box[0] + 24, y + 10), '直線段：入口 (0,0,0)，出口 (4,0,0)，朝向 0°。下一段模組的 Pivot 放在上一段的出口位姿。', 14, 660, INK)
    # bridgehead plan zones
    box = (40, 1140, 1480, 2160); panel(box, '橋頭座標系：C 類分區與接縫（組裝箭頭）')
    v = View(cv, box, 2.6, 0.0, 70, 1)
    for cid in C_CONTEXT:
        for sf in parts_of(K.BY_ID[cid]): draw_surface_plan(v, sf, n_per=2, lattice=False)
    base_plan(v, label=False)
    for cid, (lx, ly) in {'C01': (1.0, 0.0), 'C02': (3.9, 3.1), 'C03': (1.0, 2.62), 'C04': (1.0, -2.62), 'C05': (2.62, 0.75), 'C07': (2.62, 1.87), 'C08': (4.3, -0.9)}.items():
        cv.text(v.P(lx, ly), cid, 18, INK, 'mm', halo=True)
    cv.arrow(v.P(-1.6, 0), v.P(-0.05, 0), ENTRY, 3, 14); cv.text(v.P(-1.7, 0.35), 'ROAD_3M', 14, ENTRY, 'rm')
    cv.arrow(v.P(3.0, -7.0), v.P(3.0, -4.05), ENTRY, 3, 14); cv.text(v.P(3.2, -6.2), 'B 類出口 → C02 入口 (3, -4) 朝 +Y', 14, ENTRY, 'lm')
    cv.arrow(v.P(3.0, 4.05), v.P(3.0, 7.0), EXIT, 3, 14); cv.text(v.P(3.2, 6.2), 'C02 出口 (3, +4) → 下一段 B 類', 14, EXIT, 'lm')
    cv.arrow(v.P(5.2, 0), v.P(6.6, 0), DECK, 3, 14); cv.text(v.P(6.8, 0.0), 'BRIDGE_3M 出口 (2, 0, +0.15) → 測試橋面', 14, DECK, 'lm', halo=True)
    for xx, lab, yy, anc in ((K.BANK_LINE_X, '岸線 X=3.00', 4.75, 'rb'), (K.BASE_FACE_X, '石基前緣 X=3.25', 5.25, 'lb'), (K.BH_RIVER_X, '河側 X=5.00', 4.75, 'lb')):
        cv.line([v.P(xx, -4.6), v.P(xx, yy)], FAINT, 1.0, (6, 4)); cv.text(v.P(xx, yy + 0.05), lab, 12, (110, 116, 112), anc, halo=True)
    axes(cv, (box[0] + 30, box[3] - 30))
    # type table
    box = (1520, 1520, 2960, 2160); panel(box, '接頭類型')
    y = box[1] + 50
    for t, desc in K.CONNECTOR_TYPES.items():
        cv.text((box[0] + 20, y), t, 15, INK, 'lt'); y = cv.wrap((box[0] + 300, y), desc, 13, box[2] - box[0] - 330) + 6
    return cv.save(path)


def composite(paths, path, title):
    ims = [Image.open(p) for p in paths]; w = 2600; h = 1660; sc = 0.5
    sheet = Image.new('RGB', (int(w * sc) * 2 + 60, int(h * sc) * 2 + 140), BG); d = ImageDraw.Draw(sheet)
    d.text((30, 30), title, font=ImageFont.truetype(FONT_CANDIDATES[0], 30) if os.path.exists(FONT_CANDIDATES[0]) else None, fill=INK)
    for i, im in enumerate(ims):
        sheet.paste(im.resize((int(w * sc), int(h * sc)), Image.LANCZOS), (20 + (i % 2) * (int(w * sc) + 20), 100 + (i // 2) * (int(h * sc) + 20)))
    if Path(path).exists(): raise SystemExit('EXISTS (not overwritten): %s' % path)
    sheet.save(path, optimize=True)


def main():
    global OUT
    if '--out' in sys.argv:
        OUT = (KIT / sys.argv[sys.argv.index('--out') + 1]).resolve()
        assert str(OUT).startswith(str(KIT.resolve()) + os.sep), 'output must stay inside the kit'
    only = None
    if '--only' in sys.argv: only = set(sys.argv[sys.argv.index('--only') + 1].split(','))
    made = {}
    for mod in K.MODULES:
        if only and mod['code'] not in only: continue
        p = OUT / 'ThreeViews' / ('%s_%s_3view.png' % (mod['code'], mod['id']))
        module_sheet(mod).save(p); made[mod['code']] = p; print('SHEET', p.name, flush=True)
    if only: return
    overview('A', 'REF_A 道路不規則收邊 11 件（A01–A11）', OUT / 'REF_A_Road_Edge_Sheet.png')
    overview('B', 'REF_B 河岸自然收邊 10 件（B01–B10）', OUT / 'REF_B_Riverbank_Sheet.png')
    overview('C', 'REF_C 橋頭與地形交接收邊 8 件（C01–C08）', OUT / 'REF_C_Bridgehead_Sheet.png')
    composite([made[c] for c in ('A01', 'A03', 'B01', 'C01')], OUT / 'REF_D_Orthographic_Construction.png', 'REF_D 代表模組正投影施工圖：A01、A03、B01、C01（完整版見 ThreeViews/）')
    connector_sheet(OUT / 'REF_E_Connector_Engineering.png')
    print('DONE', flush=True)


if __name__ == '__main__':
    main()
