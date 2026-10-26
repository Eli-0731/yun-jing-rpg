"""Environment Transition Kit v01 - single source of truth (pure Python 3, no bpy).

Coordinates: metres, Z up, module forward +X, lateral Y (+Y = left of travel), ground datum Z = 0.
Road and bank modules: pivot = entry connector (0, 0, 0).  Bridgehead modules C01-C05, C07, C08 share
one bridgehead frame whose origin is the C01 road entry, so placing them on one transform assembles
the bridgehead.  C06 has its own frame (pivot below its high edge).

Every connector boundary is produced from the canonical section functions and sample lattices below.
Modules that share a connector type therefore share the exact same boundary vertex sequence; natural
variation (noise, rills, potholes, details) is only applied inside a window that is zero on boundaries.
"""
import math

KIT = 'Environment_Transition_Kit'
KIT_VERSION = 'v01'

# ---- global standards --------------------------------------------------------------------------
ROAD_HALF = 1.5          # road surface Y = -1.50 .. +1.50
EDGE_W = 0.75            # edge band each side
ROAD_OUTER = ROAD_HALF + EDGE_W
VERGE_H = 0.04           # low walkable verge hump inside the edge band
SEG_L = 4.0              # main straight length
HALF_SEG_L = 2.0         # spare half length (generator parameter; not one of the 29 modules)
BANK_LAND_W = 1.0        # bank module: land strip behind the bank line
BANK_WATER_W = 2.0       # bank module: slope from the bank line to the toe
BANK_TOE_Z = -1.0        # toe under the test water level
WATER_Z = -0.8           # kit test water level (not a claim about the main world)
DECK_Z = 0.15            # test bridge deck top
DECK_HALF = 1.5          # test bridge deck half width (3.00 m)
DECK_BOTTOM = -0.05      # test deck is 0.20 m thick
RAMP_L = 2.0             # road -> deck ramp length
BANK_LINE_X = 3.0        # bridgehead frame: bank line (crest)
BASE_FACE_X = 3.25       # bridgehead frame: stone base front face
BH_RIVER_X = 5.0         # bridgehead frame: river-side edge (toe)
BH_BANK_A = 4.0          # bridgehead frame: |Y| of the two bank connectors
TOL = 0.001              # connector tolerance (1 mm)
UV_TILE_M = 2.0          # metres per texture repeat (UV unit)
CURVE_ARC = 4.0          # road curve centreline arc length
CORNER_ARC = 4.0         # bank corner arc length along the bank line
CORNER_R = CORNER_ARC / (math.pi / 2)


def S(t):
    """smoothstep clamped to 0..1 (zero slope at both ends)."""
    t = min(1.0, max(0.0, t))
    return t * t * (3.0 - 2.0 * t)


def steps(a, b, step):
    n = int(round((b - a) / step))
    return [a + step * i for i in range(n + 1)]


# ---- sample lattices (identical on both sides of every connector) ------------------------------
EDGE_NEG = steps(-ROAD_OUTER, -ROAD_HALF, 0.125)
EDGE_POS = steps(ROAD_HALF, ROAD_OUTER, 0.125)
CORE_V = steps(-ROAD_HALF, ROAD_HALF, 0.25)
ROAD_V = EDGE_NEG + CORE_V[1:-1] + EDGE_POS          # 25 samples across the full road section
BANK_V = steps(-BANK_WATER_W, BANK_LAND_W, 0.125)    # 25 samples: water toe .. land edge
S_STEP = 0.25


# ---- canonical sections ------------------------------------------------------------------------
def verge(a):
    if a <= ROAD_HALF or a >= ROAD_OUTER:
        return 0.0
    return VERGE_H * math.sin(math.pi * (a - ROAD_HALF) / EDGE_W) ** 2


def road_z(v):
    return verge(abs(v))


def bank_z(v):
    """v = lateral distance from the bank line, positive towards land."""
    return 0.0 if v >= 0 else BANK_TOE_Z * S(-v / BANK_WATER_W)


def waterline_v():
    lo, hi = -BANK_WATER_W, 0.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if bank_z(mid) < WATER_Z: lo = mid
        else: hi = mid
    return (lo + hi) / 2


# Layer mask channels (vertex colour "Mask"): R = WetSoil, G = Grass, B = PathGravel, A = Moss.
# Base layer is DrySoil.  Canonical masks are used on connectors so textures also match.
def road_mask(v):
    a = abs(v)
    return (0.0, 0.9 * S((a - 1.6) / 0.5), 0.45 * math.exp(-((a - 0.75) / 0.35) ** 2), 0.0)


def grass_path_mask(v):
    a = abs(v)
    return (0.0, 0.92 - 0.3 * math.exp(-(a / 0.55) ** 2), 0.0, 0.0)


def gravel_path_mask(v):
    a = abs(v)
    return (0.0, 0.9 * S((a - 1.75) / 0.45), 1.0 - S((a - 1.45) / 0.4), 0.0)


def bank_mask(v):
    z = bank_z(v)
    return (S((-0.5 - z) / 0.3), 0.9 * S((v - 0.1) / 0.5), 0.0, 0.0)


def lerp4(m0, m1, t):
    return tuple(a + (b - a) * t for a, b in zip(m0, m1))


# ---- module paths ------------------------------------------------------------------------------
class Path:
    """Centreline (road) or bank line (bank): point(s, v) = c(s) + v * left_normal(s)."""

    def __init__(self, length, turn_deg=0.0, direction=0):
        self.L = length; self.turn = math.radians(turn_deg) * direction
        self.R = abs(length / self.turn) if self.turn else None

    def heading(self, s):
        return self.turn * s / self.L if self.turn else 0.0

    def centre(self, s):
        if not self.turn:
            return (s, 0.0)
        k = 1 if self.turn > 0 else -1; R = self.R; t = s / R
        return (R * math.sin(t), k * R * (1 - math.cos(t)))

    def point(self, s, v):
        cx, cy = self.centre(s); h = self.heading(s)
        return (cx - v * math.sin(h), cy + v * math.cos(h))


# ---- bridgehead height field and masks (frame F) -----------------------------------------------
def c_side(a):
    return 1.0 if a <= ROAD_OUTER else 1.0 - S((a - ROAD_OUTER) / 0.75)


def c_H(X, Y):
    a = abs(Y)
    if X <= RAMP_L:
        r = DECK_Z * S(X / RAMP_L)
        if a <= ROAD_HALF: return r
        if a <= ROAD_OUTER: return r + verge(a)
        return r * c_side(a)
    e = verge(a) * (1.0 - S((X - RAMP_L) / 0.5))
    plat = (DECK_Z * c_side(a) + e) * (1.0 - S((X - 2.4) / 0.9))
    P = bank_z(BANK_LINE_X - X)
    scour = -0.3 * (1.0 - S((a - 1.5) / 1.5)) * S((X - 3.0) / 0.5) * (1.0 - S((X - 4.2) / 0.8))
    return P + plat + scour


def c_mask(X, Y):
    a = abs(Y)
    grass_a = 0.9 * S((a - 1.6) / 0.5)
    track = 0.45 * math.exp(-((a - 0.75) / 0.35) ** 2)
    landing = 0.8 * S((min(X, RAMP_L) - 0.8) / 1.2) * (1.0 - S((a - 1.4) / 0.4))
    gravel_a = max(track, landing)
    if X <= RAMP_L:
        return (0.0, grass_a, gravel_a, 0.0)
    H = c_H(X, Y)
    grass = grass_a * S(((BANK_LINE_X - X) - 0.1) / 0.5)
    wet = S((-0.5 - H) / 0.3)
    gravel = gravel_a * (1.0 - S((X - RAMP_L) / 0.6)) + 0.8 * (1.0 - S((a - 1.6) / 1.0)) * S((X - 3.1) / 0.3)
    return (wet, grass, min(1.0, gravel), 0.0)


def c_uv(X, Y):
    """Approach zone uses road-style UVs; bank band uses bank-style UVs that continue the B modules."""
    if X <= RAMP_L:
        return (X / UV_TILE_M, Y / UV_TILE_M)
    return ((Y + BH_BANK_A) / UV_TILE_M, (BANK_LINE_X - X) / UV_TILE_M)


def c06_z(X, Y):
    return DECK_Z * (1.0 - S(X / 1.5))


# ---- module table --------------------------------------------------------------------------------
def M(code, mid, group, name, purpose, kind, **kw):
    d = dict(code=code, id=mid, group=group, name_zh=name, purpose=purpose, kind=kind)
    d.update(kw); return d


MODULES = [
    M('A01', 'SM_RoadEdge_Straight_L_A', 'A', '直線左路緣', '4 m 左側收邊帶（+Y），路面 3 m 由測試路芯或其他道路模組提供；泥土與草地自然過渡。', 'road_strip', side=1, length=4.0),
    M('A02', 'SM_RoadEdge_Straight_R_A', 'A', '直線右路緣', '4 m 右側收邊帶（-Y），與 A01 配對。', 'road_strip', side=-1, length=4.0),
    M('A03', 'SM_RoadEdge_Curve_L_A', 'A', '左彎 15°', '整段 3 m 路面＋兩側收邊，中心線弧長 4 m、左轉 15°，出口位姿依圓弧計算。', 'road_full', length=CURVE_ARC, turn=15, direction=1),
    M('A04', 'SM_RoadEdge_Curve_R_A', 'A', '右彎 15°', '右轉 15°，直接生成（非鏡射），法線與 UV 正確。', 'road_full', length=CURVE_ARC, turn=15, direction=-1),
    M('A05', 'SM_RoadEdge_WideCurve_L_A', 'A', '左彎 30°', '左轉 30°，路面與收邊沿同一圓弧，不扭曲。', 'road_full', length=CURVE_ARC, turn=30, direction=1),
    M('A06', 'SM_RoadEdge_WideCurve_R_A', 'A', '右彎 30°', '右轉 30°。', 'road_full', length=CURVE_ARC, turn=30, direction=-1),
    M('A07', 'SM_RoadEdge_Slope_A', 'A', '小坡銜接', '4 m 上坡，出口比入口高 0.20 m；smoothstep 坡形，兩端坡度為 0，最大坡度 7.5%。', 'road_full', length=4.0, rise=0.2),
    M('A08', 'SM_RoadEdge_GrassTransition_A', 'A', '泥路轉草地', '泥土路面沿行進方向漸變為草地小徑；貼圖遮罩混合＋稀疏可關閉草片。', 'road_full', length=4.0, variant='grass'),
    M('A09', 'SM_RoadEdge_StoneTransition_A', 'A', '泥路轉碎石', '泥土路面漸變為細碎石路，少量碎石細節；不形成石牆。', 'road_full', length=4.0, variant='gravel'),
    M('A10', 'SM_RoadEdge_End_A', 'A', '道路終端', '道路自然收尾（半圓收口），只有入口接頭。', 'road_end', length=4.0),
    M('A11', 'SM_RoadEdge_Damaged_A', 'A', '破損路段', '內側坑洞、缺角與裂紋，入口出口仍為標準斷面。', 'road_full', length=4.0, variant='damaged'),
    M('B01', 'SM_Riverbank_Straight_A', 'B', '河岸直段 A', '4 m 土坡河岸，岸上 0 m、示意水位 -0.8 m、水下坡腳 -1.0 m；稀疏植被。', 'bank', length=4.0),
    M('B02', 'SM_Riverbank_Straight_B', 'B', '河岸直段 B', '與 B01 同接頭，多風化小石、苔蘚與不同侵蝕紋。', 'bank', length=4.0, variant='stones'),
    M('B03', 'SM_Riverbank_InnerCorner_A', 'B', '河岸內凹轉角', '陸地內凹（水灣）90° 轉角：沿岸線行進時向水側右轉，岸線弧長 4 m。', 'bank', length=CORNER_ARC, turn=90, direction=-1),
    M('B04', 'SM_Riverbank_OuterCorner_A', 'B', '河岸外凸轉角', '陸地外凸（岬角）90° 轉角：向陸側左轉，岸線弧長 4 m。', 'bank', length=CORNER_ARC, turn=90, direction=1),
    M('B05', 'SM_Riverbank_Slope_A', 'B', '緩坡入水', '中段改為寬緩入水坡道（約 19°），兩端回到標準斷面；水面只在測試場景顯示。', 'bank', length=4.0, variant='gentle'),
    M('B06', 'SM_Riverbank_Steep_A', 'B', '陡岸露岩', '中段為陡土岸與面向水側的露岩。', 'bank', length=4.0, variant='steep'),
    M('B07', 'SM_Riverbank_RockReinforced_A', 'B', '砌石護岸', '岸坡上排列護岸石塊，石塊不越過兩端接頭面。', 'bank', length=4.0, variant='riprap'),
    M('B08', 'SM_Riverbank_GrassHeavy_A', 'B', '草根濕岸', '草量多、岸頂有草皮懸邊；草片為可關閉子物件。', 'bank', length=4.0, variant='grassy'),
    M('B09', 'SM_Riverbank_Eroded_A', 'B', '沖刷崩岸', '坡面三道沖刷細溝與坡腳崩土，端面高程不變。', 'bank', length=4.0, variant='eroded'),
    M('B10', 'SM_Riverbank_End_A', 'B', '河岸終端', '岸高差在 4 m 內平順消失到地面，只有入口接頭。', 'bank_end', length=4.0),
    M('C01', 'SM_Bridgehead_RoadTransition_A', 'C', '道路轉橋面', '道路 0 m 以 2 m smoothstep 緩坡升到測試橋面 +0.15 m，最大坡度 11%，無台階。', 'c_grid', parts=[('Terrain', 'approach', (0.0, RAMP_L, 0.25), (-ROAD_OUTER, ROAD_OUTER, None))]),
    M('C02', 'SM_Bridgehead_BankTransition_A', 'C', '橋頭兩側岸坡', '橋頭兩側陸地到河岸土坡的過渡（左右兩片），外端接 B 類標準河岸斷面。', 'c_grid', parts=[('Terrain', 'bank', (RAMP_L, BH_RIVER_X, 0.125), (ROAD_OUTER, BH_BANK_A, 0.125)), ('Terrain', 'bank', (RAMP_L, BH_RIVER_X, 0.125), (-BH_BANK_A, -ROAD_OUTER, 0.125))]),
    M('C03', 'SM_Bridgehead_SideTrim_L_A', 'C', '橋頭左側收口', '左側（+Y）泥土草坡與散石，貼著 C01 外緣由坡道高度降回地面，避開通行區。', 'c_grid', parts=[('Terrain', 'approach', (0.0, RAMP_L, 0.25), (ROAD_OUTER, 3.0, 0.125))]),
    M('C04', 'SM_Bridgehead_SideTrim_R_A', 'C', '橋頭右側收口', '右側（-Y）對應收口，與 C03 成對。', 'c_grid', parts=[('Terrain', 'approach', (0.0, RAMP_L, 0.25), (-3.0, -ROAD_OUTER, 0.125))]),
    M('C05', 'SM_Bridgehead_Base_A', 'C', '橋頭石基', '橋頭下方簡潔石基（頂面 -0.05 m 承托 0.20 m 厚的測試橋面），不含橋梁主跨。', 'c_base'),
    M('C06', 'SM_Bridgehead_SlopeFix_A', 'C', '接地短坡', '1.5 m 短坡，把 +0.15 m 橋面高度平順降到地面 0 m；可單獨用於簡易橋端或高差修飾。', 'c06'),
    M('C07', 'SM_Bridgehead_CornerCap_A', 'C', '橋頭角隅封邊', '石基兩側角隅的地形與封邊石，消除土坡與石基之間的三角縫（左右兩片）。', 'c_grid', parts=[('Terrain', 'bank', (RAMP_L, BASE_FACE_X, 0.125), (ROAD_HALF, ROAD_OUTER, 0.125)), ('Terrain', 'bank', (RAMP_L, BASE_FACE_X, 0.125), (-ROAD_OUTER, -ROAD_HALF, 0.125))]),
    M('C08', 'SM_Bridgehead_WaterEdge_A', 'C', '橋頭近水沖刷帶', '石基前方到河床的濕泥碎石沖刷帶，河側邊緣與 B 類坡腳同為 -1.0 m。', 'c_grid', parts=[('Terrain', 'bank', (BASE_FACE_X, BH_RIVER_X, 0.125), (-ROAD_OUTER, ROAD_OUTER, 0.125))]),
]
BY_ID = {m['id']: m for m in MODULES}
BY_CODE = {m['code']: m for m in MODULES}
GROUP_FILES = {'A': 'road_edge_modules', 'B': 'riverbank_modules', 'C': 'bridgehead_modules'}
GROUP_EXPORT_DIR = {'A': 'RoadEdge', 'B': 'Riverbank', 'C': 'Bridgehead'}
TRI_BUDGET = {'A': (300, 2000), 'B': (300, 2000), 'C': (800, 4000)}
TRI_BUDGET_MODULE = {'B07': (800, 4000)}   # rock-reinforced bank is a revetment (護岸): the brief's 800-4000 range


def tri_budget(mod):
    return TRI_BUDGET_MODULE.get(mod['code'], TRI_BUDGET[mod['group']])


# ---- per-module surface description ------------------------------------------------------------
def _win_s(s, L, d=0.6):
    return S(min(s, L - s) / d)


class Surface:
    """Lattice surface of one module part.  All boundary behaviour is defined here."""

    def __init__(self, mod, part_index=0):
        self.mod = mod; k = mod['kind']; self.kind = k
        if k in ('road_strip', 'road_full', 'road_end', 'bank', 'bank_end'):
            self.path = Path(mod.get('length', 4.0), mod.get('turn', 0.0), mod.get('direction', 0))
            self.L = self.path.L
            n = int(round(self.L / S_STEP))
            self.us = [self.L * i / n for i in range(n + 1)]
            if k == 'road_strip':
                self.vs = EDGE_POS if mod['side'] > 0 else EDGE_NEG
            elif k.startswith('road'):
                self.vs = ROAD_V
            else:
                self.vs = BANK_V
        elif k == 'c06':
            self.us = steps(0.0, 1.5, 0.125); self.vs = steps(-DECK_HALF, DECK_HALF, 0.25)
        elif k == 'c_grid':
            name, zone, (x0, x1, xs), (y0, y1, ys) = mod['parts'][part_index]
            self.zone = zone; self.us = steps(x0, x1, xs)
            self.vs = ROAD_V if ys is None else steps(y0, y1, ys)
            self.rect = (x0, x1, y0, y1)
        else:
            raise ValueError(k)

    # position in module space
    def xy(self, u, v):
        if self.kind in ('c_grid', 'c06'):
            return (u, v)
        return self.path.point(u, v)

    def z(self, u, v):
        m = self.mod; k = self.kind
        if k == 'c_grid': return c_H(u, v)
        if k == 'c06': return c06_z(u, v)
        if k == 'road_strip': return road_z(v)
        if k == 'road_full':
            z = road_z(v) + m.get('rise', 0.0) * S(u / self.L)
            if m.get('variant') == 'damaged':
                z = road_z(v) * (1.0 - chips(u, v)) - potholes(u, v)
            return z
        if k == 'road_end':
            return road_z(end_distance(u, v))
        if k == 'bank':
            base = bank_z(v); var = m.get('variant'); w = S(u / 1.0) * S((self.L - u) / 1.0)
            if var == 'gentle': return base + (gentle_z(v) - base) * w
            if var == 'steep': return base + (steep_z(v) - base) * w
            if var == 'eroded': return base + rills(u, v)
            return base
        if k == 'bank_end':
            return bank_z(v) * (1.0 - S(u / self.L))
        raise ValueError(k)

    def mask(self, u, v):
        m = self.mod; k = self.kind; var = m.get('variant')
        if k == 'c_grid': return c_mask(u, v)
        if k == 'c06': return (0.0, 0.25, 0.8 * (1 - S(u / 1.5)), 0.0)
        if k in ('road_strip', 'road_full'):
            if var == 'grass': return lerp4(road_mask(v), grass_path_mask(v), S(u / self.L))
            if var == 'gravel': return lerp4(road_mask(v), gravel_path_mask(v), S(u / self.L))
            return road_mask(v)
        if k == 'road_end':
            d = end_distance(u, v); return road_mask(d)
        if k == 'bank':
            return bank_mask_z(v, self.z(u, v))
        if k == 'bank_end':
            return bank_mask_z(v, self.z(u, v))

    def uv(self, u, v):
        if self.kind == 'c_grid': return c_uv(u, v)
        return (u / UV_TILE_M, v / UV_TILE_M)

    def window(self, u, v):
        """Weight for decorative variation: exactly 0 on every boundary of the part."""
        k = self.kind
        if k == 'road_strip':
            a = abs(v); return _win_s(u, self.L) * S((a - ROAD_HALF) / 0.2) * S((ROAD_OUTER - a) / 0.25)
        if k == 'road_full':
            return _win_s(u, self.L) * S((ROAD_OUTER - abs(v)) / 0.35)
        if k == 'road_end':
            return S(u / 0.6) * S((self.L - u) / 0.35) * S((ROAD_OUTER - abs(v)) / 0.35)
        if k == 'bank':
            return _win_s(u, self.L) * S((BANK_LAND_W - v) / 0.3) * S((v + BANK_WATER_W) / 0.3)
        if k == 'bank_end':
            return S(u / 0.6) * S((self.L - u) / 0.3) * S((BANK_LAND_W - v) / 0.3) * S((v + BANK_WATER_W) / 0.3)
        if k == 'c06':
            return S(u / 0.3) * S((1.5 - u) / 0.3) * S((DECK_HALF - abs(v)) / 0.3)
        x0, x1, y0, y1 = self.rect
        return S((u - x0) / 0.3) * S((x1 - u) / 0.3) * S((v - y0) / 0.3) * S((y1 - v) / 0.3)

    def walkable(self, u, v):
        k = self.kind
        if k in ('road_strip', 'road_full', 'road_end'): return abs(v) <= ROAD_HALF + 0.05
        if k == 'c_grid': return self.zone == 'approach' and abs(v) <= ROAD_HALF + 0.05
        return k == 'c06'


def bank_mask_z(v, z):
    return (S((-0.5 - z) / 0.3), 0.9 * S((v - 0.1) / 0.5), 0.0, 0.0)


def gentle_z(v):
    return 0.0 if v >= 0.9 else BANK_TOE_Z * S((0.9 - v) / 2.9)


def steep_z(v):
    return 0.0 if v >= -0.1 else BANK_TOE_Z * S(-(v + 0.1) / 0.9)


RILLS = [(1.0, 0.24, 0.12), (2.1, 0.3, 0.14), (3.05, 0.22, 0.10)]   # (s, half width, depth)


def rills(s, v):
    dz = 0.0
    for sc, hw, depth in RILLS:
        lat = S(1.0 - abs(s - sc) / hw)
        down = S((0.15 - v) / 0.4) * (1.0 - S((-1.35 - v) / 0.3))
        fan = S(1.0 - abs(s - sc) / (hw * 2.2)) * S((-1.25 - v) / 0.25) * (1.0 - S((-1.85 - v) / 0.12))
        dz += -depth * lat * down + 0.06 * fan
    return dz


POTHOLES = [(1.15, 0.45, 0.38, 0.05), (2.35, -0.65, 0.32, 0.04), (3.05, 0.85, 0.26, 0.035)]   # (s, v, radius, depth)
CHIPS = [(1.8, 1.95, 0.55), (2.9, -1.9, 0.5)]


def potholes(s, v):
    return sum(d * S(1.0 - math.hypot(s - ps, v - pv) / r) for ps, pv, r, d in POTHOLES)


def chips(s, v):
    return min(1.0, sum(S(1.0 - math.hypot(s - cs, v - cv) / r) for cs, cv, r in CHIPS))


END_CAP_S = 1.75


def end_distance(s, v):
    return abs(v) if s <= END_CAP_S else math.hypot(s - END_CAP_S, v)


# ---- connectors ----------------------------------------------------------------------------------
CONNECTOR_TYPES = {
    'ROAD_3M': 'Full road section: 3.00 m surface (Y=±1.50, Z=0) plus 0.75 m edge band each side with a 0.04 m verge hump; 25 vertices at Y = -2.25..-1.50 step 0.125, -1.25..1.25 step 0.25, 1.50..2.25 step 0.125.',
    'ROAD_EDGE_L': 'Left edge band only: Y = +1.50..+2.25 step 0.125 (7 vertices).  Joins ROAD_3M edges and TEST_RoadCore_3m.',
    'ROAD_EDGE_R': 'Right edge band only: Y = -2.25..-1.50 step 0.125 (7 vertices).',
    'BANK_0_TO_MINUS_0P8': 'Bank section across the bank line: land +1.00 m at Z=0, crest at 0, smoothstep slope through the test water level -0.80 to the toe -1.00 at 2.00 m on the water side; 25 vertices step 0.125.  Land is on the left of the travel direction.',
    'BRIDGE_3M': 'Test deck seat: 3.00 m wide, Z=+0.15, 13 vertices Y=-1.50..1.50 step 0.25.',
    'GROUND_3M': 'Flat ground line Z=0, 3.00 m wide.',
    'GROUND_EDGE': 'Open edge resting on flat ground Z=0.',
    'BRIDGEHEAD_FIELD': 'Internal seam of the bridgehead set; both sides sample the same height field c_H on the same lattice.',
    'BRIDGE_SEAT': 'Top face of the stone base, Z=-0.05, under the 0.20 m test deck.',
    'RIVERBED_EDGE': 'River-side open edge at the toe depth (Z=-1.00 at the bank connectors).',
}


def _seq(surface, u, vs=None):
    return [(*surface.xy(u, v), surface.z(u, v)) for v in (vs or surface.vs)]


def _seq_v(surface, v, us=None):
    return [(*surface.xy(u, v), surface.z(u, v)) for u in (us or surface.us)]


def connectors(mod):
    """Connector list: role, type, transform (location + heading) and exact boundary vertices."""
    k = mod['kind']; out = []
    if k in ('road_strip', 'road_full', 'road_end', 'bank', 'bank_end'):
        sf = Surface(mod); p = sf.path; L = sf.L
        if k == 'road_strip': t = 'ROAD_EDGE_L' if mod['side'] > 0 else 'ROAD_EDGE_R'
        elif k.startswith('road'): t = 'ROAD_3M'
        else: t = 'BANK_0_TO_MINUS_0P8'
        out.append(dict(name='EntryConnector', role='entry', type=t, location=(0.0, 0.0, 0.0), heading_deg=0.0, vertices=_seq(sf, 0.0)))
        if k in ('road_end', 'bank_end'):
            return out
        ex, ey = p.centre(L); rise = mod.get('rise', 0.0)
        variant = {'grass': 'GRASS_PATH', 'gravel': 'GRAVEL_PATH'}.get(mod.get('variant'))
        out.append(dict(name='ExitConnector', role='exit', type=t, surface_variant=variant, location=(ex, ey, rise),
                        heading_deg=math.degrees(p.heading(L)), vertices=_seq(sf, L)))
        if k == 'road_strip':
            v = ROAD_HALF * mod['side']
            out.append(dict(name='CoreSeam', role='seam', type='ROAD_3M', partner='TEST_RoadCore_3m (or the surface of another road module)',
                            location=(0.0, v, 0.0), heading_deg=0.0, vertices=_seq_v(sf, v)))
        return out
    if k == 'c06':
        sf = Surface(mod)
        out.append(dict(name='EntryConnector', role='entry', type='BRIDGE_3M', location=(0.0, 0.0, DECK_Z), heading_deg=0.0, vertices=_seq(sf, 0.0)))
        out.append(dict(name='ExitConnector', role='exit', type='GROUND_3M', location=(1.5, 0.0, 0.0), heading_deg=0.0, vertices=_seq(sf, 1.5)))
        return out
    if k == 'c_base':
        out.append(dict(name='EntryConnector', role='entry', type='BRIDGE_SEAT', location=(RAMP_L, 0.0, DECK_BOTTOM), heading_deg=0.0,
                        vertices=[(RAMP_L, -DECK_HALF, DECK_BOTTOM), (RAMP_L, DECK_HALF, DECK_BOTTOM), (BASE_FACE_X, DECK_HALF, DECK_BOTTOM), (BASE_FACE_X, -DECK_HALF, DECK_BOTTOM)]))
        out.append(dict(name='ExitConnector', role='exit', type='BRIDGEHEAD_FIELD', partner='SM_Bridgehead_WaterEdge_A (front face contact)',
                        location=(BASE_FACE_X, 0.0, c_H(BASE_FACE_X, 0.0)), heading_deg=0.0,
                        vertices=[(BASE_FACE_X, y, c_H(BASE_FACE_X, y)) for y in steps(-DECK_HALF, DECK_HALF, 0.125)]))
        return out
    mid = mod['id']
    def surf(i): return Surface(mod, i)
    if mid == 'SM_Bridgehead_RoadTransition_A':
        sf = surf(0)
        out.append(dict(name='EntryConnector', role='entry', type='ROAD_3M', location=(0.0, 0.0, 0.0), heading_deg=0.0, vertices=_seq(sf, 0.0)))
        out.append(dict(name='ExitConnector', role='exit', type='BRIDGE_3M', location=(RAMP_L, 0.0, DECK_Z), heading_deg=0.0, vertices=_seq(sf, RAMP_L, CORE_V)))
        for side, partner in ((1, 'SM_Bridgehead_SideTrim_L_A'), (-1, 'SM_Bridgehead_SideTrim_R_A')):
            out.append(dict(name='SideSeam_' + ('L' if side > 0 else 'R'), role='seam', type='BRIDGEHEAD_FIELD', partner=partner,
                            location=(0.0, side * ROAD_OUTER, 0.0), heading_deg=0.0, vertices=_seq_v(sf, side * ROAD_OUTER)))
        edge = [v for v in ROAD_V if abs(v) >= ROAD_HALF]
        out.append(dict(name='CornerSeam', role='seam', type='BRIDGEHEAD_FIELD', partner='SM_Bridgehead_CornerCap_A',
                        location=(RAMP_L, 0.0, DECK_Z), heading_deg=0.0, vertices=_seq(sf, RAMP_L, edge)))
    elif mid == 'SM_Bridgehead_BankTransition_A':
        L, R = surf(0), surf(1)
        out.append(dict(name='EntryConnector', role='entry', type='BANK_0_TO_MINUS_0P8', location=(BANK_LINE_X, -BH_BANK_A, 0.0), heading_deg=90.0,
                        vertices=[(BANK_LINE_X - v, -BH_BANK_A, bank_z(v)) for v in BANK_V]))
        out.append(dict(name='ExitConnector', role='exit', type='BANK_0_TO_MINUS_0P8', location=(BANK_LINE_X, BH_BANK_A, 0.0), heading_deg=90.0,
                        vertices=[(BANK_LINE_X - v, BH_BANK_A, bank_z(v)) for v in BANK_V]))
        for sf, side in ((L, 1), (R, -1)):
            tag = 'L' if side > 0 else 'R'
            out.append(dict(name='TrimSeam_' + tag, role='seam', type='BRIDGEHEAD_FIELD', partner='SM_Bridgehead_SideTrim_%s_A' % tag, location=(RAMP_L, side * ROAD_OUTER, 0.0), heading_deg=0.0,
                            vertices=sorted((RAMP_L, side * y, c_H(RAMP_L, side * y)) for y in steps(ROAD_OUTER, 3.0, 0.125))))
            out.append(dict(name='InnerSeam_' + tag, role='seam', type='BRIDGEHEAD_FIELD', partner='SM_Bridgehead_CornerCap_A / SM_Bridgehead_WaterEdge_A',
                            location=(RAMP_L, side * ROAD_OUTER, 0.0), heading_deg=0.0, vertices=_seq_v(sf, side * ROAD_OUTER)))
    elif mid in ('SM_Bridgehead_SideTrim_L_A', 'SM_Bridgehead_SideTrim_R_A'):
        sf = surf(0); side = 1 if mid.endswith('L_A') else -1; ys = sf.vs
        out.append(dict(name='EntryConnector', role='entry', type='GROUND_EDGE', location=(0.0, side * 2.625, 0.0), heading_deg=0.0, vertices=_seq(sf, 0.0)))
        out.append(dict(name='ExitConnector', role='exit', type='BRIDGEHEAD_FIELD', partner='SM_Bridgehead_BankTransition_A', location=(RAMP_L, side * 2.625, 0.0), heading_deg=0.0, vertices=_seq(sf, RAMP_L)))
        out.append(dict(name='RoadSeam', role='seam', type='BRIDGEHEAD_FIELD', partner='SM_Bridgehead_RoadTransition_A', location=(0.0, side * ROAD_OUTER, 0.0), heading_deg=0.0,
                        vertices=_seq_v(sf, side * ROAD_OUTER)))
    elif mid == 'SM_Bridgehead_CornerCap_A':
        for i, side in ((0, 1), (1, -1)):
            sf = surf(i); tag = 'L' if side > 0 else 'R'
            out.append(dict(name=('EntryConnector' if side > 0 else 'EntryConnector_R'), role='entry', type='BRIDGEHEAD_FIELD', partner='SM_Bridgehead_RoadTransition_A',
                            location=(RAMP_L, side * 1.875, 0.0), heading_deg=0.0, vertices=_seq(sf, RAMP_L)))
            out.append(dict(name=('ExitConnector' if side > 0 else 'ExitConnector_R'), role='exit', type='BRIDGEHEAD_FIELD', partner='SM_Bridgehead_WaterEdge_A',
                            location=(BASE_FACE_X, side * 1.875, 0.0), heading_deg=0.0, vertices=_seq(sf, BASE_FACE_X)))
            out.append(dict(name='BankSeam_' + tag, role='seam', type='BRIDGEHEAD_FIELD', partner='SM_Bridgehead_BankTransition_A',
                            location=(RAMP_L, side * ROAD_OUTER, 0.0), heading_deg=0.0, vertices=_seq_v(sf, side * ROAD_OUTER)))
    elif mid == 'SM_Bridgehead_WaterEdge_A':
        sf = surf(0)
        out.append(dict(name='EntryConnector', role='entry', type='BRIDGEHEAD_FIELD', partner='SM_Bridgehead_Base_A / SM_Bridgehead_CornerCap_A',
                        location=(BASE_FACE_X, 0.0, c_H(BASE_FACE_X, 0.0)), heading_deg=0.0, vertices=_seq(sf, BASE_FACE_X)))
        out.append(dict(name='ExitConnector', role='exit', type='RIVERBED_EDGE', location=(BH_RIVER_X, 0.0, c_H(BH_RIVER_X, 0.0)), heading_deg=0.0, vertices=_seq(sf, BH_RIVER_X)))
        for side in (1, -1):
            out.append(dict(name='BankSeam_' + ('L' if side > 0 else 'R'), role='seam', type='BRIDGEHEAD_FIELD', partner='SM_Bridgehead_BankTransition_A',
                            location=(BASE_FACE_X, side * ROAD_OUTER, 0.0), heading_deg=0.0, vertices=_seq_v(sf, side * ROAD_OUTER)))
    return out


def exit_transform(mod):
    for c in connectors(mod):
        if c['role'] == 'exit' and c['name'] == 'ExitConnector':
            return c['location'], c['heading_deg']
    return None


# ---- assembly pairs checked by validate_connectors.py ----------------------------------------
# (module, connector) must coincide with (module, connector) after placing the second module on the
# first module's exit transform.  Bridgehead seams compare both sides in the shared frame.
CHAIN_TESTS = [
    ('straight x3', ['SM_RoadEdge_Straight_L_A', 'SM_RoadEdge_Straight_L_A', 'SM_RoadEdge_Straight_L_A']),
    ('curves L15 R15 L30 R30', ['SM_RoadEdge_Curve_L_A', 'SM_RoadEdge_Curve_R_A', 'SM_RoadEdge_WideCurve_L_A', 'SM_RoadEdge_WideCurve_R_A']),
    ('road variants', ['SM_RoadEdge_Slope_A', 'SM_RoadEdge_Damaged_A', 'SM_RoadEdge_StoneTransition_A']),
    ('road into end', ['SM_RoadEdge_Curve_L_A', 'SM_RoadEdge_End_A']),
    ('bank chain', ['SM_Riverbank_Straight_A', 'SM_Riverbank_InnerCorner_A', 'SM_Riverbank_Straight_B', 'SM_Riverbank_OuterCorner_A', 'SM_Riverbank_Slope_A',
                    'SM_Riverbank_Steep_A', 'SM_Riverbank_RockReinforced_A', 'SM_Riverbank_GrassHeavy_A', 'SM_Riverbank_Eroded_A', 'SM_Riverbank_End_A']),
    ('road into bridgehead', ['SM_RoadEdge_Damaged_A', 'SM_Bridgehead_RoadTransition_A']),
    ('transition exits (geometry)', ['SM_RoadEdge_GrassTransition_A', 'SM_RoadEdge_WideCurve_L_A']),
]
FIELD_SEAMS = [  # (module A, connector A, module B, connector B)
    ('SM_Bridgehead_RoadTransition_A', 'SideSeam_L', 'SM_Bridgehead_SideTrim_L_A', 'RoadSeam'),
    ('SM_Bridgehead_RoadTransition_A', 'SideSeam_R', 'SM_Bridgehead_SideTrim_R_A', 'RoadSeam'),
    ('SM_Bridgehead_SideTrim_L_A', 'ExitConnector', 'SM_Bridgehead_BankTransition_A', 'TrimSeam_L'),
    ('SM_Bridgehead_SideTrim_R_A', 'ExitConnector', 'SM_Bridgehead_BankTransition_A', 'TrimSeam_R'),
    ('SM_Bridgehead_RoadTransition_A', 'CornerSeam', 'SM_Bridgehead_CornerCap_A', 'EntryConnector+EntryConnector_R'),
    ('SM_Bridgehead_CornerCap_A', 'BankSeam_L', 'SM_Bridgehead_BankTransition_A', 'InnerSeam_L[:11]'),
    ('SM_Bridgehead_CornerCap_A', 'BankSeam_R', 'SM_Bridgehead_BankTransition_A', 'InnerSeam_R[:11]'),
    ('SM_Bridgehead_WaterEdge_A', 'BankSeam_L', 'SM_Bridgehead_BankTransition_A', 'InnerSeam_L[10:]'),
    ('SM_Bridgehead_WaterEdge_A', 'BankSeam_R', 'SM_Bridgehead_BankTransition_A', 'InnerSeam_R[10:]'),
    ('SM_Bridgehead_CornerCap_A', 'ExitConnector', 'SM_Bridgehead_WaterEdge_A', 'EntryConnector[30:]'),
    ('SM_Bridgehead_CornerCap_A', 'ExitConnector_R', 'SM_Bridgehead_WaterEdge_A', 'EntryConnector[:7]'),
]


if __name__ == '__main__':
    import json
    print(len(MODULES), 'modules;', 'waterline v =', round(waterline_v(), 4))
    for m in MODULES:
        cs = connectors(m)
        print(m['code'], m['id'], [(c['name'], c['type'], len(c['vertices'])) for c in cs])
