"""VH roof (work pack 2026-11-09 B-112h, batch A): the VL pan-and-roll tile roof on a span and pitch of the house's own.

vl_roof builds the StarterHouse v004 roof only (its curve, depths and tile counts are module constants). VH houses have other spans and
a steeper pitch, so configure() rebinds those constants on vl_roof before any tile is laid, and the board, barge, rafter, ridge and
eave-cap parts below take the span from the config instead of the StarterHouse numbers. The tile geometry, the eight baked tile cells
and the shared 1024 tile texture (VL_Shared/Textures/VL_RoofTiles_*) are vl_roof's own and are not rebuilt: every VH roof reads the
same texture as VL01-05.

Roof curve (same form as StarterHouse's): z(x, t) = Z0 + RISE (1 - t)^1.35 + LIFT_EAVE t^8 + LIFT_END (|x| / XH)^8, t = 0 at the ridge,
1 at the eave; the ridge line runs along x at y = 0, the front slope reaches y = -DEPTH[-1], the back slope y = +DEPTH[1].
One build runs one house per Blender process, so rebinding the module constants affects nothing else.
"""
import math
import numpy as np
from mathutils import Vector
import vl_roof as RF
from ti_core import S, cyl

CFG = {}


def configure(z0, rise, depth_front, depth_back, xh, lift_eave=.15, lift_end=.2, courses=12):
    """Rebind vl_roof's curve and tile layout to this house. xh = half the tiled width (pan centres run -xh .. +xh)."""
    n_pan = int(round(2 * xh / RF.PITCH)) + 1
    x0 = -(n_pan - 1) * RF.PITCH / 2
    CFG.update(z0=z0, rise=rise, depth={-1: depth_front, 1: depth_back}, xh=xh, x0=x0, n_pan=n_pan, lift_eave=lift_eave, lift_end=lift_end)
    def roof_z(x, t):
        return z0 + rise * max(0., 1 - t) ** 1.35 + lift_eave * t ** 8 + lift_end * (abs(x) / xh) ** 8
    RF.roof_z = roof_z
    RF.DEPTH = dict(CFG['depth'])
    RF.PAN_X0 = x0
    RF.N_PAN = n_pan
    RF.N_ROLL = n_pan + 1
    assert courses == RF.N_COURSE, 'course_t() keeps vl_roof\'s 12 courses as its default argument'
    CFG['roof_z'] = roof_z
    S['roof_cfg'] = {k: v for k, v in CFG.items() if k != 'roof_z'}
    return roof_z


def z(x, t): return CFG['roof_z'](x, t)
def t_of(y): return abs(y) / CFG['depth'][-1 if y < 0 else 1]
def under(x, y): return z(x, t_of(y)) + RF.UNDER_TOP - RF.UNDER_T        # underside of the roof boards above (x, y)


def underlay(P, side, cut=lambda side, x, t: False, nx=None):
    D = CFG['depth'][side]; X = abs(CFG['x0']) + .10; nx = nx or int(round(2 * X / .4)); nt = 24
    xs = lambda i: -X + 2 * X * i / nx
    ts = lambda j: j / nt * (1 + .002 / D)          # boards end 2 mm past the eave line, inside the eave caps (D + .004 +- .008)
    top = lambda i, j: (xs(i), side * ts(j) * D, z(xs(i), ts(j)) + RF.UNDER_TOP)
    bot = lambda i, j: (xs(i), side * ts(j) * D, z(xs(i), ts(j)) + RF.UNDER_TOP - RF.UNDER_T)
    keep = lambda i, j: not cut(side, (xs(i) + xs(i + 1)) / 2, (ts(j) + ts(j + 1)) / 2)
    return RF.slab_grid(f'Roof_Boards_{side}', nx, nt, top, bot, keep, P['timber'], group='Wood', grain='x')


def barge_boards(P):
    for sx in (-1, 1):
        x = sx * (abs(CFG['x0']) + .15)
        for side in (-1, 1):
            D = CFG['depth'][side]
            pts = [(x, side * t * D, z(x, t) + RF.UNDER_TOP - .005) for t in np.linspace(0., .985, 17)]
            RF.sweep_box(f'Barge_Board_{sx}_{side}', pts, .045, .19, P['timber'], up=(0, 0, 1), group='Wood', grain='y')


def eave_rafters(P, spacing=.5, reach=.8):
    X = abs(CFG['x0']) - .2; n = int(2 * X / spacing) + 1
    for side in (-1, 1):
        D = CFG['depth'][side]
        for i in range(n):
            x = -X + i * 2 * X / (n - 1)
            t0 = (D - reach) / D
            pts = [(x, side * t * D, z(x, t) + RF.UNDER_TOP - RF.UNDER_T + .01) for t in np.linspace(t0, 1.0, 5)]
            RF.sweep_box(f'Eave_Rafter_{side}_{i}', pts, .08, .1, P['timber'], bevel=False, group='Wood', grain='y', uvw=.6)


def ridge(P):
    """Stacked ridge body with a round cap tile; the ends sweep up into short curled ends (restrained, a village house)."""
    x1 = abs(CFG['x0']) + .05; xs = np.linspace(-x1, x1, 41)
    zr = lambda x: z(x, 0.)
    body = [(x, 0., zr(x) + .19) for x in xs]
    RF.sweep_box('Ridge_Body', body, .3, .22, P['tile'], up=(0, 0, 1), grain='x', group='Stone')
    V, F = [], []; seg = 8
    for x in xs:
        for q in range(seg + 1):
            a = math.pi * q / seg
            V.append((x, .085 * math.cos(a), zr(x) + .19 + .075 * math.sin(a)))
    for k in range(len(xs) - 1):
        for q in range(seg):
            a = k * (seg + 1) + q
            F.append((a, a + seg + 1, a + seg + 2, a + 1))
    from ti_core import mesh
    mesh('Ridge_Cap', V, F, P['tile'], smooth=True, grain='x', solid=.012, group='Stone')
    for sx in (-1, 1):
        x = sx * x1
        # the curled end: a short block rising from the ridge end, its tip turned outwards (village houses keep it low)
        pts = [(x - sx * .3, 0., zr(x) + .19), (x - sx * .08, 0., zr(x) + .2), (x + sx * .05, 0., zr(x) + .26), (x + sx * .1, 0., zr(x) + .33)]
        RF.sweep_box(f'Ridge_Curl_{sx}', pts, .22, .16, P['tile'], grain='x', group='Stone')
        cyl('Ridge_End_Cap', (x - sx * .02, 0., zr(x) + .19), .095, .02, P['tile'], axis='x', verts=14, group='Stone')


def eave_caps(P, side):
    D = CFG['depth'][side]
    for i in range(RF.N_ROLL):
        x = RF.roll_x(i)
        y = side * (D + .004); zz = z(x, 1.) + RF.ROLL_BASE + RF.LIFT + .02
        cyl('Eave_Cap', (x, y, zz), .056, .016, P['tile'], axis='y', verts=8, bevel=0., detail=1, group='Stone')


def build(P, cell=None, hole=lambda side, x, k: False):
    for side in (-1, 1):
        RF.tiles(P, side, hole=hole, cell=cell)
        underlay(P, side)
        eave_caps(P, side)
    ridge(P); barge_boards(P); eave_rafters(P)
