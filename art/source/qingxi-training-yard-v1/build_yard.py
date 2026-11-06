"""Qingxi public training yard v1 (rebuild at alchemy-kit quality). Run in a background Blender:

  blender -b --python-exit-code 1 --python build_yard.py [-- training-shelter qi-striking-post ...] [--no-render]
  blender -b --python-exit-code 1 --python build_yard.py -- --master        (assemble the master .blend)

Per asset: builds editable procedural parts from the saved AI three-views in
art/references/qingxi-training-yard-v1/, bakes them into one atlas material (BaseColor, ORM, Normal)
with kitlib (adapted from the alchemy workshop pipeline), makes LOD1/LOD2, exports GLB (LOD0) and
FBX (LOD0-2), writes <asset>_model_info.json and renders review images.
All geometry is original procedural modelling; no third-party meshes are used.
"""
import sys
import json
import math
import random
import time
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import yardlib as Y  # noqa: E402
import kitlib as Q  # noqa: E402

PROJECT = ROOT.parents[2]
REF = PROJECT / 'art/references/qingxi-training-yard-v1'
TEX = ROOT / 'textures'
TEX.mkdir(exist_ok=True)
EXPORT = Q.EXPORTS
PREV = Q.PREVIEWS
IDS = ['training-shelter', 'qi-striking-post', 'agility-post', 'weapon-rack',
       'engraved-training-stone', 'training-banner']
# The AI three-views must exist before any modelling happens.
for asset in IDS:
    assert (REF / f'{asset}-three-view.png').is_file(), f'missing three-view: {asset}'
ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
RENDER = '--no-render' not in ARGV

N = 512
yy, xx = np.mgrid[0:N, 0:N].astype(np.float32) / N


# ====================================================================== pattern images (motifs only)
def save_image(name, arr, data=False):
    h, w = arr.shape[:2]
    rgba = np.ones((h, w, 4), np.float32)
    rgba[..., :3] = arr[..., None] if arr.ndim == 2 else arr
    im = bpy.data.images.new(name, width=w, height=h, alpha=False)
    im.colorspace_settings.name = 'Non-Color' if data else 'sRGB'
    im.pixels.foreach_set(rgba.ravel())
    im.filepath_raw = str(TEX / f'{name}.png')
    im.file_format = 'PNG'
    im.save()
    im.pack()
    return im


def tex_stone(seed, base, dark, moss=0.0):
    big = Y.noise(N, 2.0, seed)
    mid = Y.noise(N, 1.4, seed + 1)
    pits = Y.smoothstep(0.72, 0.9, Y.noise(N, 0.8, seed + 2))
    veins = 1 - Y.smoothstep(0.0, 0.025, np.abs(Y.noise(N, 2.2, seed + 3) - 0.5))
    rgb = Y.mix(dark, base, big * 0.6 + mid * 0.4)
    rgb = rgb * (1 - pits[..., None] * 0.35) * (1 - veins[..., None] * 0.25)
    if moss:
        mask = Y.smoothstep(0.62, 0.8, Y.noise(N, 2.0, seed + 4)) * moss
        rgb = Y.mix(rgb, (0.20, 0.26, 0.11), mask)
    height = big * 0.5 + mid * 0.5 - pits * 0.6 - veins * 0.3
    return rgb, height, 0.86 - mid * 0.1



def tex_banner(seed):
    """Banner print in 0..1 UV space: green field, ochre borders, concentric rings."""
    h, w = 1024, 512
    v, u = np.mgrid[0:h, 0:w].astype(np.float32)
    u /= w
    v /= h  # v = 0 bottom, 1 top
    weave = (np.sin(u * 300 * np.pi) * np.sin(v * 600 * np.pi)) * 0.5 + 0.5
    blot = np.kron(Y.noise(512, 2.0, seed), np.ones((2, 1)))[:h, :w]
    green = np.array((0.09, 0.27, 0.22))
    ochre = np.array((0.62, 0.43, 0.15))
    rgb = green * (0.8 + 0.2 * weave[..., None]) * (0.85 + 0.3 * blot[..., None])
    border = (u < 0.085) | (u > 0.915) | (v > 0.955)
    rgb[border] = ochre * (0.8 + 0.25 * blot[border][..., None])
    cx, cy = 0.5, 0.64
    d = np.sqrt(((u - cx) * 0.5) ** 2 + ((v - cy) * 1.0) ** 2) / 0.5  # aspect corrected
    rings = ((d < 0.16) | ((d > 0.26) & (d < 0.32)) | ((d > 0.40) & (d < 0.46))) & ~border
    rgb[rings] = (np.array((0.78, 0.66, 0.42)) * (0.85 + 0.2 * blot[rings][..., None]))
    fade = Y.smoothstep(0.25, 0.0, v)  # sun-faded, dirtier hem
    rgb = rgb * (1 - fade[..., None] * 0.25)
    height = weave * 0.3 + rings * 0.2
    return np.clip(rgb, 0, 1), height, 0.88


def tex_spiral(seed):
    n = 256
    v, u = np.mgrid[0:n, 0:n].astype(np.float32) / n
    x, y = u - 0.5, v - 0.5
    r = np.sqrt(x * x + y * y) + 1e-6
    a = np.arctan2(y, x)
    spiral = np.abs(((r * 22 - a / np.pi) % 2) - 1)
    groove = (1 - Y.smoothstep(0.15, 0.35, spiral)) * (r < 0.40) * (r > 0.04)
    rim = 1 - Y.smoothstep(0.0, 0.02, np.abs(r - 0.45))
    cloud = Y.noise(n, 2.0, seed)
    rgb = Y.mix((0.12, 0.38, 0.33), (0.36, 0.62, 0.54), cloud)
    rgb = rgb * (1 - groove[..., None] * 0.55) * (1 - rim[..., None] * 0.3)
    return rgb, -groove - rim * 0.5, 0.25 + groove * 0.2


def tex_plaque(seed):
    """Lacquered plaque inset with an abstract gilt sword-and-ring emblem (no text)."""
    h, w = 256, 512
    v, u = np.mgrid[0:h, 0:w].astype(np.float32)
    u, v = u / w, v / h
    lac = Y.noise(256, 2.0, seed)[:h, :]
    lac = np.kron(lac, np.ones((1, 2)))[:, :w]
    rgb = Y.mix((0.06, 0.05, 0.04), (0.14, 0.10, 0.07), lac)
    x, y = (u - 0.5) * 2.4, (v - 0.5)
    r = np.sqrt(x * x + y * y)
    gold = (np.abs(r - 0.30) < 0.025) | ((np.abs(y) < 0.018) & (np.abs(x) < 0.85)) | \
        ((np.abs(x) < 0.02) & (np.abs(y) < 0.36)) | ((np.abs(x) < 0.12) & (np.abs(y + 0.14) < 0.02))
    frame = (u < 0.03) | (u > 0.97) | (v < 0.06) | (v > 0.94)
    rgb[gold | frame] = (0.70, 0.52, 0.22)
    return rgb, (gold | frame).astype(np.float32) * 0.5, np.where(gold | frame, 0.35, 0.45)


# ---------------------------------------------------------------- materials

# ====================================================================== materials
def local_uv(nt, axes, scale, offset):
    """UV from the part-local coordinates kitlib stores in qa_lc (survives joining and re-unwrapping)."""
    p = Q.sep(nt, Q.attr(nt, 'qa_lc'))
    cv = Q.N(nt, 'ShaderNodeCombineXYZ')
    for i, (ax, s, o) in enumerate(zip(axes, scale, offset)):
        Q.L(nt, Q.math_(nt, 'ADD', Q.math_(nt, 'MULTIPLY', p[ax], s), o), cv.inputs[i])
    return cv.outputs[0]


def m_image(name, maker, axes, scale, offset, bump=0.0008, extra_rough=None):
    """Albedo, roughness and height straight from an authored pattern (banner print, plaque)."""
    rgb, height, rough = maker
    alb = save_image(f'P_{name}_Color', rgb)
    hgt = save_image(f'P_{name}_Height', (height - height.min()) / (np.ptp(height) or 1), True)
    m, nt, b = Q.new_mat(name)
    uv = local_uv(nt, axes, scale, offset)
    ti = Q.N(nt, 'ShaderNodeTexImage', image=alb, extension='EXTEND')
    Q.L(nt, uv, ti.inputs['Vector'])
    th = Q.N(nt, 'ShaderNodeTexImage', image=hgt, extension='EXTEND')
    Q.L(nt, uv, th.inputs['Vector'])
    r = float(np.mean(rough)) if extra_rough is None else extra_rough
    return Q.finish(m, nt, b, ti.outputs['Color'], r, 0.0, th.outputs['Color'], bump, 0.8)


def overlay_mask(m, mask_arr, name, axes, scale, offset, color, depth=0.6, rough=None):
    """Inlay a mask (engraved rings, spiral groove) onto an existing kitlib material."""
    nt = m.node_tree
    img = save_image(f'P_{name}_Mask', mask_arr.astype(np.float32), True)
    ti = Q.N(nt, 'ShaderNodeTexImage', image=img, extension='EXTEND')
    Q.L(nt, local_uv(nt, axes, scale, offset), ti.inputs['Vector'])
    mask = ti.outputs['Color']
    alb = next(n for n in nt.nodes if n.type == 'REROUTE' and n.name == 'CH_albedo')
    src = alb.inputs[0].links[0].from_socket
    Q.L(nt, Q.mix(nt, mask, src, color), alb.inputs[0])
    bump = next(n for n in nt.nodes if n.type == 'BUMP')
    h = bump.inputs['Height'].links[0].from_socket
    Q.L(nt, Q.math_(nt, 'SUBTRACT', h, Q.math_(nt, 'MULTIPLY', mask, depth)), bump.inputs['Height'])
    bump.inputs['Distance'].default_value = max(bump.inputs['Distance'].default_value, 0.003)
    if rough is not None:
        rr = next(n for n in nt.nodes if n.type == 'REROUTE' and n.name == 'CH_rough')
        Q.L(nt, Q.mixf(nt, mask, rr.inputs[0].links[0].from_socket, rough), rr.inputs[0])
    return m


WOOD_A, WOOD_B = (0.046, 0.026, 0.014), (0.115, 0.068, 0.036)
DARK_A, DARK_B = (0.026, 0.015, 0.008), (0.066, 0.038, 0.020)


def m_oldwood(name, a, b_, axis='Z', grey=(0.17, 0.15, 0.13), wear=0.6, rough=0.74):
    """Outdoor timber: long grain streaks, cracks running with the grain, sun-greyed upward faces and
    lighter worn edges. Same channel layout as kitlib materials so it bakes into the atlas."""
    m, nt, b = Q.new_mat(name)
    sc = {'X': (0.6, 11.0, 11.0), 'Y': (11.0, 0.6, 11.0), 'Z': (11.0, 11.0, 0.6)}[axis]
    co = Q.coords(nt, sc)
    streak = Q.noise(nt, co, 3.0, 8, 0.65, 0.6)
    fib = Q.noise(nt, Q.coords(nt, tuple(s * 6 for s in sc)), 4.0, 3, 0.6)
    wv = Q.N(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='X' if axis != 'X' else 'Y')
    Q.L(nt, co, wv.inputs['Vector'])
    wv.inputs['Scale'].default_value = 1.4
    wv.inputs['Distortion'].default_value = 5.0
    wv.inputs['Detail'].default_value = 4.0
    g = Q.math_(nt, 'ADD', Q.math_(nt, 'MULTIPLY', wv.outputs['Fac'], 0.45), Q.math_(nt, 'MULTIPLY', streak, 0.55))
    col = Q.mix(nt, Q.smooth(nt, g, 0.25, 0.85), a, b_)
    crack = Q.math_(nt, 'SUBTRACT', 1.0, Q.smooth(nt, Q.voronoi(nt, Q.coords(nt, tuple(s * 0.5 for s in sc)), 2.2,
                                                                 'DISTANCE_TO_EDGE'), 0.0, 0.035))
    crack = Q.math_(nt, 'MULTIPLY', crack, Q.smooth(nt, Q.noise(nt, co, 1.2, 2), 0.45, 0.65))
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', crack, 0.85), col, (a[0] * 0.35, a[1] * 0.35, a[2] * 0.35))
    up = Q.sep(nt, Q.N(nt, 'ShaderNodeNewGeometry').outputs['Normal'])[2]
    sun = Q.math_(nt, 'MULTIPLY', Q.smooth(nt, up, 0.2, 0.9), Q.smooth(nt, Q.noise(nt, co, 0.8, 3), 0.35, 0.7))
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', sun, 0.55), col, grey)
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', Q.attr(nt, 'qa_seed', 'fac'), 0.25), col, (b_[0] * 1.2, b_[1] * 1.05, b_[2] * 0.9))
    cav, edge = Q.edge_cavity(nt, 0.03, 0.006)
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', Q.smooth(nt, cav, 0.1, 0.7), 0.7), col, (0.018, 0.011, 0.006))
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', Q.smooth(nt, Q.math_(nt, 'ADD', edge, Q.math_(nt, 'MULTIPLY', fib, 0.35)), 0.5, 0.9),
                            wear), col, (b_[0] * 1.9, b_[1] * 1.8, b_[2] * 1.7))
    hgt = Q.math_(nt, 'SUBTRACT', Q.math_(nt, 'ADD', Q.math_(nt, 'MULTIPLY', wv.outputs['Fac'], 0.35),
                                         Q.math_(nt, 'MULTIPLY', fib, 0.4)), Q.math_(nt, 'MULTIPLY', crack, 1.2))
    return Q.finish(m, nt, b, col, Q.mixf(nt, edge, rough, rough - 0.14), 0.0, hgt, 0.002, 0.9)


def m_tile(name, pitch=0.30):
    """Grey-blue fired clay tiles: an overlap joint every `pitch` metres down the slope (part-local Y),
    lichen and rain streaks on the lower ends, darker joints so roll tiles read as individual pieces."""
    m, nt, b = Q.new_mat(name)
    co = Q.coords(nt, (1, 1, 1))
    p = Q.sep(nt, Q.attr(nt, 'qa_lc'))
    yy_ = Q.math_(nt, 'ABSOLUTE', p[1])
    ph = Q.math_(nt, 'FRACT', Q.math_(nt, 'DIVIDE', yy_, pitch))
    joint = Q.math_(nt, 'MULTIPLY', Q.smooth(nt, ph, 0.80, 0.97), Q.math_(nt, 'SUBTRACT', 1.0, Q.smooth(nt, ph, 0.97, 1.0)))
    n = Q.noise(nt, co, 6.0, 5, 0.6)
    col = Q.mix(nt, Q.smooth(nt, n, 0.3, 0.75), (0.028, 0.034, 0.040), (0.058, 0.066, 0.074))
    tint = Q.smooth(nt, Q.noise(nt, co, 1.1, 2), 0.5, 0.8)
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', tint, 0.5), col, (0.070, 0.062, 0.050))
    lichen = Q.math_(nt, 'MULTIPLY', Q.smooth(nt, Q.noise(nt, co, 9.0, 4), 0.62, 0.72), Q.smooth(nt, ph, 0.4, 0.9))
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', lichen, 0.6), col, (0.11, 0.115, 0.085))
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', joint, 0.8), col, (0.010, 0.011, 0.012))
    cav, edge = Q.edge_cavity(nt, 0.04, 0.006)
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', Q.smooth(nt, cav, 0.1, 0.6), 0.7), col, (0.008, 0.009, 0.010))
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', Q.smooth(nt, edge, 0.4, 0.8), 0.4), col, (0.11, 0.12, 0.125))
    hgt = Q.math_(nt, 'SUBTRACT', Q.math_(nt, 'MULTIPLY', n, 0.3), Q.math_(nt, 'MULTIPLY', joint, 1.0))
    return Q.finish(m, nt, b, col, Q.mixf(nt, lichen, 0.5, 0.85), 0.0, hgt, 0.004, 1.0)


def make_materials():
    """(Re)create every material after a scene reset; exposes them as module globals."""
    g = {}
    for axis in 'XYZ':
        g['WOOD_' + axis] = m_oldwood('WeatheredElm_' + axis, WOOD_A, WOOD_B, axis)
        g['DARK_' + axis] = m_oldwood('DarkTimber_' + axis, DARK_A, DARK_B, axis, grey=(0.10, 0.09, 0.08), wear=0.45,
                                      rough=0.68)
    g['WOOD'], g['DARK'] = g['WOOD_Z'], g['DARK_Z']
    g['STONE'] = Q.m_stone('Limestone', light=(0.25, 0.244, 0.226), dark=(0.14, 0.136, 0.128), chisel=0.8)
    g['ROCK'] = Q.m_stone('FieldRock', light=(0.17, 0.168, 0.158), dark=(0.085, 0.084, 0.08), scale=1.6, speck=1.4, chisel=2.0)
    g['TILE'] = m_tile('BlueClayTile')
    g['ROPE'] = Q.m_cord('HempRope', (0.26, 0.18, 0.085), (0.46, 0.34, 0.17))
    g['DROPE'] = Q.m_cord('DarkCord', (0.025, 0.022, 0.018), (0.07, 0.058, 0.045))
    g['LEATHER'] = Q.m_simple('WornLeather', (0.085, 0.045, 0.022), (0.17, 0.10, 0.048), rough=0.52, nscale=14.0,
                              bump=0.0012, cav_col=(0.03, 0.016, 0.008), edge_col=(0.26, 0.16, 0.08))
    g['RED'] = Q.m_cloth('RedWrap', base=(0.30, 0.045, 0.03), stain=(0.15, 0.04, 0.025), pitch=0.0025)
    g['IRON'] = Q.m_iron('BlackIron', 0.45)
    g['JADE'] = Q.m_simple('Jade', (0.025, 0.14, 0.11), (0.09, 0.30, 0.23), rough=0.22, nscale=3.0,
                           edge_col=(0.20, 0.42, 0.34))
    g['GREEN'] = Q.m_cloth('JadeCloth', base=(0.022, 0.10, 0.075), stain=(0.015, 0.05, 0.035), pitch=0.002)
    g['IVORY'] = Q.m_simple('Ivory', (0.36, 0.32, 0.23), (0.45, 0.40, 0.30), rough=0.38, cav_col=(0.30, 0.26, 0.18))
    # Pattern materials sample authored images through part-local coordinates.
    spiral = tex_spiral(61)[1]
    g['SPIRAL'] = overlay_mask(Q.m_simple('JadeSpiral', (0.03, 0.17, 0.13), (0.10, 0.33, 0.26), rough=0.2, nscale=3.0,
                                          edge_col=(0.24, 0.46, 0.38)),
                               np.clip(-spiral, 0, 1), 'Spiral', (0, 1, 2), (1 / 0.18, 1 / 0.18, 0), (0.5, 0.5, 0),
                               (0.02, 0.07, 0.055), 0.8, 0.45)
    g['BANNER'] = m_image('BannerPrint', tex_banner(67), (0, 2, 1), (1 / 0.70, 1 / 1.40, 0), (0.5, -(2.295 - 1.40) / 1.40, 0))
    g['PLAQUE'] = m_image('LacquerPlaque', tex_plaque(79), (0, 2, 1), (1 / 0.96, 1 / 0.36, 0), (0.5, 0.5, 0), 0.0006, 0.4)
    g['MOTIF'] = overlay_mask(Q.m_stone('EngravedTop', light=(0.23, 0.225, 0.21), dark=(0.13, 0.127, 0.12), chisel=0.5),
                              tex_motif_mask(), 'Motif', (0, 1, 2), (1 / 1.8, 1 / 1.5, 0), (0.5, 0.5, 0),
                              (0.03, 0.17, 0.15), 1.0, 0.45)
    globals().update(g)
    return g


def tex_motif_mask():
    """Engraved ring / four-petal / diamond mask for the 1.8 x 1.5 m training stone (1 = groove)."""
    n = 1024
    v, u = np.mgrid[0:n, 0:n].astype(np.float32) / n
    x, y = (u - 0.5) * 1.8, (v - 0.5) * 1.5
    r = np.sqrt(x ** 2 + y ** 2)
    a = np.arctan2(y, x)
    groove = np.zeros_like(r)
    for rr in (0.27, 0.40, 0.58):
        groove = np.maximum(groove, 1 - Y.smoothstep(0.006, 0.014, np.abs(r - rr)))
    petal_r = 0.15 * np.abs(np.cos(2 * a)) ** 0.6
    groove = np.maximum(groove, (1 - Y.smoothstep(0.006, 0.014, np.abs(r - petal_r))) * (r < 0.17))
    for k in range(4):
        ang = k * np.pi / 2
        dx, dy = x - 0.58 * np.cos(ang), y - 0.58 * np.sin(ang)
        rx = dx * np.cos(ang) + dy * np.sin(ang)
        ry = -dx * np.sin(ang) + dy * np.cos(ang)
        dia = np.abs(rx) / 0.07 + np.abs(ry) / 0.035
        groove = np.maximum(groove, 1 - Y.smoothstep(0.85, 1.0, np.abs(dia - 0.8) + 0.8))
    return np.maximum(groove, 1 - Y.smoothstep(0.01, 0.022, r))


def new_collection(name):
    return Q.ACTIVE['coll']


def assign_grain(objs):
    """Point wood grain along each part's longest local axis."""
    for o in objs:
        if o.type != 'MESH':
            continue
        dims = [max(v.co[i] for v in o.data.vertices) - min(v.co[i] for v in o.data.vertices) for i in range(3)]
        axis = 'XYZ'[int(np.argmax(dims))]
        for i, m in enumerate(o.data.materials):
            if m and m.name.split('_')[0] in ('WeatheredElm', 'DarkTimber'):
                o.data.materials[i] = globals()[('WOOD_' if m.name.startswith('Weathered') else 'DARK_') + axis]


# ====================================================================== 1 SHELTER
def build_shelter():
    C = new_collection('training-shelter')
    PH = 0.30                       # plinth height
    PW, PD = 6.4, 4.8               # plinth footprint
    CX, CY = 2.55, 1.75             # column grid
    ZR, DROP, LIFT = 3.80, 0.72, 0.46
    XE = 3.35                       # gable overhang half-width

    def corner(x):
        return min(max((abs(x) - 1.25) / (XE - 1.25), 0.0), 1.0)

    def eave_y(x):
        return 2.75 + 0.20 * corner(x) ** 2

    def roof_z(x, s):
        over = max(s - 1.0, 0.0)  # rafters run slightly past the eave line
        s = min(s, 1.0)
        return ZR - DROP * (1 - (1 - s) ** 1.4) + LIFT * corner(x) ** 2.5 * s ** 3 - over * 0.4

    # ---- plinth: core, curb course and floor slabs
    core = Y.block('plinth_core', (PW - 0.1, PD - 0.1, PH - 0.05), (0, 0, (PH - 0.05) / 2), C, [STONE], 0.02)
    k = 0
    for side in (-1, 1):
        x = -PW / 2
        while x < PW / 2 - 1e-3:
            seg = min(1.15 + random.uniform(-0.15, 0.2), PW / 2 - x)
            Y.block(f'curb_{k}', (seg - 0.012, 0.36, 0.08), (x + seg / 2, side * (PD / 2 - 0.18), PH - 0.04), C, [STONE], 0.015)
            x += seg
            k += 1
        y = -PD / 2 + 0.36
        while y < PD / 2 - 0.37:
            seg = min(1.1 + random.uniform(-0.1, 0.15), PD / 2 - 0.36 - y)
            Y.block(f'curb_{k}', (0.36, seg - 0.012, 0.08), (side * (PW / 2 - 0.18), y + seg / 2, PH - 0.04), C, [STONE], 0.015)
            y += seg
            k += 1
    nx, ny = 7, 5
    sx, sy = (PW - 0.72) / nx, (PD - 0.72) / ny
    for i in range(nx):
        for j in range(ny):
            off = (j % 2) * 0.5 * sx if i < nx - 1 else 0
            Y.block(f'slab_{i}_{j}', (sx - 0.014, sy - 0.014, 0.05 + random.uniform(-0.004, 0.004)),
                    (-PW / 2 + 0.36 + sx * (i + 0.5), -PD / 2 + 0.36 + sy * (j + 0.5), PH - 0.025), C, [STONE], 0.012)
    # ---- front steps (3.4 m) with cheek stones
    for n, (top, y0) in enumerate(((0.20, -PD / 2 - 0.30), (0.10, -PD / 2 - 0.60))):
        Y.block(f'step_{n}', (3.4, 0.31, top), (0, y0 + 0.155, top / 2), C, [STONE], 0.018)
    for side in (-1, 1):
        cheek = Y.prism(f'step_cheek_{side}', [(-PD / 2 - 0.66, 0), (-PD / 2, 0), (-PD / 2, PH), (-PD / 2 - 0.08, PH),
                                               (-PD / 2 - 0.66, 0.08)], 0.24, C, [STONE], plane='YZ', offset=side * 1.82)
        Y.bevel(cheek, 0.015)

    # ---- columns on carved drum bases
    col_top = roof_z(0, 1.95 / 2.75) - 0.21 - 0.08 - 0.27
    for ix in (-1, 1):
        for iy in (-1, 1):
            x, y = ix * CX, iy * CY
            base = Y.lathe(f'col_base_{ix}{iy}', [(0.31, 0), (0.31, 0.06), (0.29, 0.08), (0.30, 0.13), (0.29, 0.18),
                                                  (0.25, 0.23), (0.21, 0.27), (0.20, 0.29)], 20, C, [STONE], smooth_angle=35)
            Y.place(base, (x, y, PH))
            col = Y.lathe(f'column_{ix}{iy}', [(0.175, 0), (0.172, 0.6), (0.165, 1.2), (0.155, col_top - PH - 0.32)],
                          18, C, [WOOD], vscale=1.0)
            Y.place(col, (x, y, PH + 0.29))
    # ---- beams: lintel (e fang), lower tie, plate
    zb = col_top - 0.14
    for iy in (-1, 1):
        Y.beam_between(f'lintel_fb_{iy}', (-CX - 0.25, iy * CY, zb), (CX + 0.25, iy * CY, zb), 0.17, 0.28, C, [WOOD])
        Y.beam_between(f'tie_fb_{iy}', (-CX, iy * CY, zb - 0.36), (CX, iy * CY, zb - 0.36), 0.13, 0.14, C, [WOOD])
        for x in (-1.3, 0.0, 1.3):  # short struts between lintel and tie
            Y.block(f'strut_{iy}_{x}', (0.12, 0.10, 0.22), (x, iy * CY, zb - 0.22), C, [DARK], 0.01)
    for ix in (-1, 1):
        Y.beam_between(f'lintel_side_{ix}', (ix * CX, -CY - 0.25, zb), (ix * CX, CY + 0.25, zb), 0.17, 0.28, C, [WOOD])
        Y.beam_between(f'tie_side_{ix}', (ix * CX, -CY, zb - 0.36), (ix * CX, CY, zb - 0.36), 0.13, 0.14, C, [WOOD])
    zp = col_top + 0.035
    for iy in (-1, 1):
        Y.beam_between(f'plate_fb_{iy}', (-CX - 0.32, iy * CY, zp), (CX + 0.32, iy * CY, zp), 0.24, 0.07, C, [DARK])
    for ix in (-1, 1):
        Y.beam_between(f'plate_side_{ix}', (ix * CX, -CY - 0.32, zp), (ix * CX, CY + 0.32, zp), 0.24, 0.07, C, [DARK])

    # ---- que ti brackets: scalloped profile under the tie beam, inner side of each column
    zt = zb - 0.43
    prof = [(0.0, 0.0), (0.78, 0.0), (0.72, -0.07), (0.58, -0.08), (0.50, -0.15), (0.36, -0.16),
            (0.28, -0.25), (0.16, -0.27), (0.10, -0.36), (0.0, -0.40)]
    for ix in (-1, 1):
        for iy in (-1, 1):
            p = [(ix * -1 * px, pz) for px, pz in prof]
            if ix > 0:
                p = p[::-1]
            br = Y.prism(f'queti_x_{ix}{iy}', [(ix * CX + a, zt + b) for a, b in p], 0.07, C, [DARK],
                         plane='XZ', offset=iy * CY)
            Y.bevel(br, 0.008, 1)
            q = [(iy * -1 * px, pz) for px, pz in prof]
            if iy > 0:
                q = q[::-1]
            br = Y.prism(f'queti_y_{ix}{iy}', [(iy * CY + a, zt + b) for a, b in q], 0.07, C, [DARK],
                         plane='YZ', offset=ix * CX)
            Y.bevel(br, 0.008, 1)

    # ---- dou-gong clusters on the plate
    zd = zp + 0.035
    eave_purlin_z = roof_z(0, 1.95 / 2.75) - 0.21
    sites = [(x, iy * CY, 'fb') for iy in (-1, 1) for x in (-CX, -1.7, -0.85, 0.0, 0.85, 1.7, CX)] + \
            [(ix * CX, y, 'side') for ix in (-1, 1) for y in (-0.9, 0.0, 0.9)]
    for n, (x, y, kind) in enumerate(sites):
        Y.block(f'dou_{n}', (0.22, 0.22, 0.11), (x, y, zd + 0.055), C, [DARK], 0.01, taper=0.22)
        along = (0.70, 0.09, 0.09) if kind == 'fb' else (0.09, 0.70, 0.09)
        Y.block(f'gong_{n}', along, (x, y, zd + 0.155), C, [WOOD], 0.012)
        for t in (-0.3, 0.3):
            dx, dy = (t, 0) if kind == 'fb' else (0, t)
            Y.block(f'sheng_{n}_{t}', (0.13, 0.13, 0.07), (x + dx, y + dy, zd + 0.235), C, [DARK], 0.008, taper=0.2)
        if kind == 'fb':  # projecting arm carries the eave purlin
            sgn = 1 if y > 0 else -1
            Y.beam_between(f'ang_{n}', (x, y - sgn * 0.12, zd + 0.17), (x, sgn * 2.02, eave_purlin_z - 0.02), 0.09, 0.10, C, [WOOD])
            Y.block(f'dou_top_{n}', (0.15, 0.15, 0.07), (x, sgn * 1.95, eave_purlin_z - 0.11), C, [DARK], 0.008, taper=0.2)

    # ---- trusses and purlins
    mid_s = 0.98 / 2.75
    z_mid = roof_z(0, mid_s) - 0.21
    z_ridge = roof_z(0, 0) - 0.21
    for x in (-CX, 0.0, CX):
        Y.beam_between(f'tie_beam_{x}', (x, -CY - 0.12, zd + 0.08), (x, CY + 0.12, zd + 0.08), 0.16, 0.2, C, [WOOD])
        for sy in (-1, 1):
            Y.block(f'gua_{x}_{sy}', (0.13, 0.13, z_mid - zd - 0.18), (x, sy * 0.98, (z_mid + zd + 0.18) / 2), C, [WOOD], 0.01)
        Y.beam_between(f'beam3_{x}', (x, -1.10, z_mid - 0.1), (x, 1.10, z_mid - 0.1), 0.14, 0.16, C, [WOOD])
        Y.block(f'king_{x}', (0.12, 0.12, z_ridge - z_mid), (x, 0, (z_ridge + z_mid) / 2 - 0.05), C, [WOOD], 0.01)
        for sy in (-1, 1):  # cha shou braces
            Y.beam_between(f'brace_{x}_{sy}', (x, sy * 0.9, z_mid - 0.02), (x, sy * 0.08, z_ridge - 0.1), 0.06, 0.08, C, [DARK], 0.006)
    for y, z in ((0.0, z_ridge), (0.98, z_mid), (-0.98, z_mid), (1.95, eave_purlin_z), (-1.95, eave_purlin_z)):
        p = Y.tube(f'purlin_{y}', [(-XE + 0.25, y, z), (XE - 0.25, y, z)], 0.085, 12, C, [WOOD])

    # ---- roof: corrugated pan sheet (solidified) + roll-tile tubes + eave caps
    pitch = 0.235
    ncol = int((2 * XE) / pitch)
    xs = [-XE + pitch * (i + 0.5) for i in range(ncol)]
    for sgn in (-1, 1):
        def pan(u, v, sgn=sgn):
            x = -XE + 2 * XE * u
            s = v
            trough = 0.035 * (1 - math.cos(2 * math.pi * ((x + XE) / pitch))) * 0.5
            return (x, sgn * s * eave_y(x), roof_z(x, s) - 0.03 - trough)
        sheet = Y.grid_surface(f'roof_pan_{sgn}', pan, ncol * 4, 18, C, [TILE], uscale=2 * XE, vscale=2.9,
                               smooth_angle=80, flip=sgn < 0)
        sol = sheet.modifiers.new('Board', 'SOLIDIFY')
        sol.thickness = 0.07
        sol.offset = -1
        sol.material_offset = 0
        for i, x in enumerate(xs):
            pts = [(x, sgn * s * eave_y(x), roof_z(x, s) - 0.005) for s in np.linspace(0.015, 1.0, 16)]
            Y.tube(f'roll_{sgn}_{i}', pts, 0.06, 6, C, [TILE], caps=False, arc=(math.pi, 2 * math.pi), vscale=1.0,
                   smooth_angle=80)
            end = Vector(pts[-1])
            dirv = (end - Vector(pts[-2])).normalized()
            cap = Y.tube(f'wadang_{sgn}_{i}', [tuple(end - dirv * 0.01), tuple(end + dirv * 0.03)], 0.068, 10, C, [TILE])
        # rafters under the eave, visible from below
        for i, x in enumerate(xs[1::2]):
            pts = [(x, sgn * s * eave_y(x), roof_z(x, s) - 0.14) for s in np.linspace(0.3, 1.02, 6)]
            Y.tube(f'rafter_{sgn}_{i}', pts, 0.036, 8, C, [DARK])
    # ---- main ridge with curled ends, gable ridges and barge boards
    Y.block('ridge_body', (2 * XE + 0.1, 0.24, 0.20), (0, 0, ZR + 0.06), C, [TILE], 0.03)
    Y.tube('ridge_roll', [(-XE + 0.02, 0, ZR + 0.17), (XE - 0.02, 0, ZR + 0.17)], 0.075, 10, C, [TILE])
    for sx in (-1, 1):
        curl = [(sx * (XE + 0.05 + 0.10 * math.sin(t)), 0, ZR + 0.12 + 0.10 * (1 - math.cos(t)) + 0.05 * t)
                for t in np.linspace(0, 3.6, 18)]
        Y.tube(f'ridge_curl_{sx}', curl, lambda t: 0.085 * (1 - 0.55 * t), 10, C, [TILE])
        for sgn in (-1, 1):
            edge = [(sx * (XE - 0.06), sgn * s * eave_y(sx * XE), roof_z(sx * XE, s) + 0.06) for s in np.linspace(0.03, 1.0, 16)]
            Y.tube(f'gable_ridge_{sx}_{sgn}', edge, 0.08, 10, C, [TILE])
            board = Y.grid_surface(f'barge_{sx}_{sgn}', lambda u, v, sx=sx, sgn=sgn: (
                sx * (XE - 0.12), sgn * u * eave_y(sx * XE), roof_z(sx * XE, u) - 0.06 - 0.22 * v), 16, 1, C, [DARK],
                uscale=2.8, vscale=0.25, flip=(sx * sgn) < 0)
            s2 = board.modifiers.new('Thick', 'SOLIDIFY')
            s2.thickness = 0.05
        # hanging-fish board at the gable peak
        fish = Y.prism(f'xuanyu_{sx}', [(-0.10, ZR - 0.25), (0.10, ZR - 0.25), (0.14, ZR - 0.45), (0.0, ZR - 0.62),
                                       (-0.14, ZR - 0.45)], 0.04, C, [DARK], plane='YZ', offset=sx * (XE - 0.12))
        Y.bevel(fish, 0.008, 1)

    # ---- hanging jade knots on the two front columns, and the emblem plaque
    for ix in (-1, 1):
        x, y = ix * CX, -CY - 0.19
        z0 = zt - 0.05
        knot = [(x + 0.06 * math.cos(t), y, z0 - 0.18 + 0.06 * math.sin(t) * 1.3) for t in np.linspace(0, 2 * math.pi, 20)]
        Y.tube(f'jade_ring_{ix}', knot, 0.016, 8, C, [JADE])
        Y.tube(f'jade_cord_{ix}', [(x, y, z0), (x, y, z0 - 0.10)], 0.007, 6, C, [GREEN])
        Y.lathe(f'jade_bead_{ix}', [(0.0, -0.05), (0.035, -0.03), (0.035, 0.03), (0.0, 0.05)], 12, C, [JADE]).location = (x, y, z0 - 0.32)
        tassel = Y.lathe(f'tassel_{ix}', [(0.012, 0.0), (0.03, -0.06), (0.045, -0.36), (0.0, -0.40)], 12, C, [GREEN])
        tassel.location = (x, y, z0 - 0.36)
    frame = Y.block('plaque_frame', (1.10, 0.06, 0.46), (0, -CY - 0.14, zb + 0.02), C, [DARK], 0.015)
    frame.rotation_euler = (math.radians(-8), 0, 0)
    inset = Y.grid_surface('plaque_face', lambda u, v: (-0.48 + 0.96 * u, 0, -0.18 + 0.36 * v), 1, 1, C, [PLAQUE])
    inset.location = (0, -CY - 0.175, zb + 0.02)
    inset.rotation_euler = (math.radians(-8), 0, 0)
    return C


# ====================================================================== 2 QI STRIKING POST
def build_qi_post():
    C = new_collection('qi-striking-post')
    for n, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        st = Y.block(f'base_stone_{n}', (0.35, 0.35, 0.26 + 0.02 * (n % 2)), (sx * 0.185, sy * 0.185, 0.13 + 0.01 * (n % 2)), C, [ROCK], 0.03)
        st.data.vertices[4 + n].co.z -= 0.025  # chipped top corners, one per block
    for n, ang in enumerate((0, 90, 180, 270)):
        a = math.radians(ang)
        w = Y.block(f'wedge_{n}', (0.07, 0.10, 0.26), (0.0, 0.0, 0.13), C, [DARK], 0.008)
        w.location = (0.34 * math.sin(a), -0.34 * math.cos(a), 0.13)
        w.rotation_euler = (0, 0, a)
    plate = Y.prism('wedge_spike', [(-0.025, 0.08), (0.025, 0.08), (0.0, 0.0)], 0.01, C, [IRON], plane='XZ', offset=-0.396)
    plate.location.z = 0.10
    post = Y.lathe('post_body', [(0.18, 0.02), (0.18, 1.55), (0.165, 1.60), (0.13, 1.635), (0.0, 1.645)], 8, C, [WOOD],
                   smooth_angle=30, start=math.pi / 8)
    post['node'] = 'body'
    for b, zc in enumerate((0.60, 0.88, 1.16)):
        coil = Y.helix(0.205, zc - 0.095, zc + 0.095, 8.5, 22, phase=b)
        Y.tube(f'rope_band_{b + 1}', coil, 0.021, 7, C, [ROPE], node=f'rope_band_{b + 1}')
        for sx in (-1, 1):
            Y.block(f'clamp_{b}_{sx}', (0.035, 0.06, 0.25), (sx * 0.226, 0, zc), C, [DARK], 0.006,
                    node=f'rope_band_{b + 1}')
    disc = Y.lathe('jade_disc', [(0.0, 0.0), (0.078, 0.0), (0.082, 0.012), (0.074, 0.026), (0.0, 0.028)], 24, C, [SPIRAL],
                   smooth_angle=40, node='jade_disc')
    me = disc.data  # planar UV so the spiral texture faces the player
    for loop in me.loops:
        co = me.vertices[loop.vertex_index].co
        me.uv_layers.active.data[loop.index].uv = (0.5 + co.x / 0.18, 0.5 + co.y / 0.18)
    disc.rotation_euler = (math.radians(90), 0, 0)
    disc.location = (0, -0.172, 1.44)
    for i, z in enumerate((1.33, 1.295, 1.26)):
        s = Y.lathe(f'stud_{i}', [(0.0, 0.0), (0.014, 0.0), (0.012, 0.012), (0.0, 0.016)], 10, C, [IRON])
        s.rotation_euler = (math.radians(90), 0, 0)
        s.location = (0, -0.17, z)
    return C


# ====================================================================== 3 AGILITY / BLOCKING POST
def build_agility_post():
    C = new_collection('agility-post')
    for n, ang in enumerate((45, -45)):
        h = 0.14 + 0.006 * n  # second timber slightly taller so crossing tops never coplanar
        b = Y.block(f'foot_{n}', (1.15, 0.17, h + 0.03), (0, 0, (h + 0.03) / 2), C, [WOOD], 0.018)
        b.rotation_euler = (0, 0, math.radians(ang))
    for n in range(4):
        a = math.radians(45 + 90 * n)
        Y.block(f'foot_wedge_{n}', (0.08, 0.08, 0.08), (0.22 * math.cos(a), 0.22 * math.sin(a), 0.21), C, [DARK], 0.008)
    Y.lathe('post_body', [(0.142, 0.16), (0.139, 0.80), (0.134, 1.50)], 20, C, [WOOD], node='body')
    Y.lathe('pad_cap', [(0.0, 1.49), (0.146, 1.49), (0.158, 1.515), (0.160, 1.60), (0.15, 1.645), (0.10, 1.665), (0.0, 1.67)],
            20, C, [LEATHER], smooth_angle=60)
    Y.tube('cap_cord', Y.helix(0.145, 1.44, 1.488, 4.0, 24), 0.010, 6, C, [DROPE])
    arms = {'arm_left': (math.radians(210), 1.12, 0.0), 'arm_right': (math.radians(330), 1.12, 0.0),  # front is -Y
            'arm_low': (math.radians(270), 0.56, math.radians(-22))}
    for name, (yaw, z, tilt) in arms.items():
        # each arm is its own node pivoting on the post axis (origin at the post centre)
        d = Vector((math.cos(yaw) * math.cos(tilt), math.sin(yaw) * math.cos(tilt), math.sin(tilt)))
        start, end = d * 0.12, d * 0.48
        parts = [Y.tube(f'{name}_shaft', [tuple(start), tuple(end)], 0.046, 12, C, [WOOD], node=name)]
        pad_axis = [tuple(end - d * 0.03), tuple(end + d * 0.03), tuple(end + d * 0.10), tuple(end + d * 0.16), tuple(end + d * 0.185)]
        parts.append(Y.tube(f'{name}_pad', pad_axis, lambda t: 0.058 + 0.026 * math.sin(math.pi * min(t * 1.08, 1)) ** 0.6, 16, C,
                            [LEATHER], node=name))
        if name == 'arm_left':
            wrap_pts = [tuple(d * t) for t in np.linspace(0.30, 0.45, 2)]
            parts.append(Y.tube(f'{name}_wrap', wrap_pts, 0.053, 14, C, [RED], node=name))
        mort = Y.block(f'{name}_mortise', (0.10, 0.07, 0.14), tuple(d * 0.145), C, [DARK], 0.008, node=name)
        mort.rotation_euler = (0, -tilt, yaw)
        for ob in parts + [mort]:
            ob.location = Vector(ob.location) + Vector((0, 0, z))
    for n, (a, z) in enumerate(((0.4, 1.32), (2.7, 1.30), (1.6, 0.92), (4.7, 0.75), (5.5, 1.0))):
        Y.block(f'peg_{n}', (0.05, 0.035, 0.06), (0.148 * math.cos(a), 0.148 * math.sin(a), z), C, [DARK], 0.006).rotation_euler = (0, 0, a)
    return C


# ====================================================================== 4 WEAPON RACK
def build_weapon_rack():
    C = new_collection('weapon-rack')
    for sx in (-1, 1):
        x = sx * 0.80
        foot = Y.prism(f'foot_{sx}', [(-0.325, 0.0), (0.325, 0.0), (0.325, 0.05), (0.20, 0.09), (0.09, 0.17),
                                      (-0.09, 0.17), (-0.20, 0.09), (-0.325, 0.05)], 0.16, C, [WOOD], plane='YZ', offset=x)
        Y.bevel(foot, 0.012)
        Y.block(f'upright_{sx}', (0.12, 0.12, 1.50), (x, 0, 0.15 + 0.75), C, [WOOD], 0.012)
        for z in (0.24, 1.50):
            Y.block(f'band_{sx}_{z}', (0.135, 0.135, 0.05), (x, 0, z), C, [IRON], 0.004)
            for fy in (-1, 1):
                Y.lathe(f'rivet_{sx}_{z}_{fy}', [(0, 0), (0.009, 0), (0.007, 0.007), (0, 0.009)], 8, C, [IRON]).location = (x, fy * 0.068, z)
    for z in (0.78, 1.36):
        pts = [(-0.80, z - 0.07), (0.80, z - 0.07), (0.80, z + 0.07)]
        top = []
        for i in range(6):
            cx = 0.80 - 0.23 - i * 0.228
            top += [(cx + 0.07 + 0.012, z + 0.07)] + [(cx + 0.065 * math.cos(t), z + 0.07 - 0.065 * math.sin(t))
                                                       for t in np.linspace(0.0, math.pi, 7)] + [(cx - 0.07 - 0.012, z + 0.07)]
        pts += top + [(-0.80, z + 0.07)]
        beam = Y.prism(f'rail_{z}', pts, 0.10, C, [WOOD], plane='XZ', offset=0.0)
        Y.bevel(beam, 0.008, 1, 30)
        for sx in (-1, 1):
            peg = Y.tube(f'dowel_{z}_{sx}', [(sx * 0.70, 0, z), (sx * 0.95, 0, z)], 0.028, 10, C, [DARK])
            Y.lathe(f'pin_{z}_{sx}', [(0, 0), (0.03, 0), (0.026, 0.02), (0, 0.025)], 10, C, [DARK]).location = (sx * 0.80, -0.065, z)
    return C


# ====================================================================== 5 ENGRAVED TRAINING STONE
def build_stone():
    C = new_collection('engraved-training-stone')
    nt, nr = 96, 12
    rng = np.random.default_rng(5)
    harm = [(k, rng.uniform(0.006, 0.03) / k ** 0.3, rng.uniform(0, 6.28)) for k in range(2, 9)]

    def rim(t):
        r = 1 + sum(a * math.cos(k * t + p) for k, a, p in harm)
        notch = -0.10 * math.exp(-((t - 2.55) / 0.12) ** 2)  # the chipped corner in the top view
        return 0.9 * (r + notch), 0.75 * (r + notch)

    verts, faces, uvs, fmat = [], [], [], []
    # top disc: polar rings (index ring*nt + i), centre vertex last
    for j in range(1, nr + 1):
        f = j / nr
        for i in range(nt):
            t = 2 * math.pi * i / nt
            ax, ay = rim(t)
            x, y = ax * math.cos(t) * f * 0.97, ay * math.sin(t) * f * 0.97
            z = 0.26 + 0.018 * (1 - f * f) + 0.004 * math.sin(7 * t + j)
            verts.append((x, y, z))
    centre = len(verts)
    verts.append((0, 0, 0.278))
    for i in range(nt):
        faces.append((centre, i, (i + 1) % nt))
    for j in range(nr - 1):
        for i in range(nt):
            a, b = j * nt + i, j * nt + (i + 1) % nt
            faces.append((a, a + nt, b + nt, b))
    top_faces = len(faces)
    # skirt: rough rocky edge down to the ground
    skirt_rows = [(1.0, 0.0), (1.02, -0.035), (1.05, -0.09), (1.07, -0.16), (1.06, -0.255)]
    first = len(verts)
    for k, (scale, dz) in enumerate(skirt_rows[1:]):
        for i in range(nt):
            t = 2 * math.pi * i / nt
            ax, ay = rim(t)
            bump = 1 + 0.03 * math.sin(11 * t + k * 1.7) + 0.02 * math.sin(23 * t + k) + 0.018 * rng.standard_normal()
            last_row = k == len(skirt_rows) - 2
            z = 0.0 if last_row else 0.255 + dz + 0.012 * rng.standard_normal()
            verts.append((ax * math.cos(t) * scale * bump, ay * math.sin(t) * scale * bump, z))
    rings = [(nr - 1) * nt] + [first + k * nt for k in range(len(skirt_rows) - 1)]
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(nt):
            a, b = r0 + i, r0 + (i + 1) % nt
            faces.append((a, b, r1 + (i + 1) % nt, r1 + i))
    bottom = len(verts)
    verts.append((0, 0, 0.0))
    last = rings[-1]
    for i in range(nt):
        faces.append((bottom, last + (i + 1) % nt, last + i))
    corner_uvs = []
    for fi, f in enumerate(faces):
        if fi < top_faces or all(verts[v][2] == 0.0 for v in f):  # top motif or flat underside
            corner_uvs.append([(verts[v][0] / 1.8 + 0.5, verts[v][1] / 1.5 + 0.5) for v in f])
            fmat.append(0 if fi < top_faces else 1)
        else:
            row = []
            for v in f:
                x, y, z = verts[v]
                row.append(((math.atan2(y, x) / (2 * math.pi) + 0.5) * 5.2, z * 1.5))
            corner_uvs.append(row)
            fmat.append(1)
    ob = Y.make_mesh('stone_body', verts, faces, corner_uvs, [MOTIF, ROCK], fmat, C, smooth_angle=55)
    Y.recalc_normals(ob)
    return C


# ====================================================================== 6 TRAINING BANNER
def build_banner():
    C = new_collection('training-banner')
    Y.block('base_stone', (0.55, 0.55, 0.25), (0, 0, 0.125), C, [ROCK], 0.035)
    Y.lathe('socket', [(0.075, 0.25), (0.075, 0.40), (0.062, 0.43), (0.05, 0.44)], 8, C, [IRON], smooth_angle=30,
            start=math.pi / 8)
    for n in range(4):
        a = math.radians(45 + 90 * n)
        br = Y.prism(f'socket_fin_{n}', [(0.06, 0.25), (0.17, 0.25), (0.06, 0.36)], 0.025, C, [IRON], plane='XZ')
        br.rotation_euler = (0, 0, a)
    Y.lathe('pole', [(0.040, 0.262), (0.038, 1.5), (0.034, 2.55)], 12, C, [WOOD])
    Y.lathe('finial', [(0.0, 2.54), (0.03, 2.55), (0.05, 2.58), (0.058, 2.61), (0.05, 2.645), (0.0, 2.66)], 14, C, [IVORY])
    for z0, z1 in ((0.50, 0.60), (2.40, 2.48)):
        Y.tube(f'pole_wrap_{z0}', Y.helix(0.046, z0, z1, 6, 18), 0.012, 6, C, [ROPE])
    zc = 2.33
    Y.tube('crossbar', [(-0.42, 0, zc), (0.42, 0, zc)], 0.03, 10, C, [WOOD])
    for sx in (-1, 1):
        pts = [(sx * 0.36 + 0.035 * math.sin(t), 0.035 * math.cos(t), zc + 0.004 * t) for t in np.linspace(0, 8 * math.pi, 50)]
        Y.tube(f'bar_wrap_{sx}', pts, 0.010, 6, C, [ROPE])
        Y.tube(f'tassel_cord_{sx}', [(sx * 0.38, 0, zc - 0.02), (sx * 0.385, -0.01, zc - 0.18), (sx * 0.39, 0, zc - 0.26)], 0.008, 6, C, [ROPE])
        Y.lathe(f'tassel_knot_{sx}', [(0, -0.03), (0.022, -0.015), (0.022, 0.012), (0, 0.025)], 10, C, [ROPE]).location = (sx * 0.39, 0, zc - 0.28)
    for t in (-1, 1):
        lash = [(0.045 * math.cos(a), 0.045 * math.sin(a), zc + t * 0.03 * math.cos(a) + 0.02 * math.sin(2 * a))
                for a in np.linspace(0, 2 * math.pi, 24)]
        Y.tube(f'lash_{t}', lash, 0.010, 6, C, [ROPE])
    # cloth: 0.70 x 1.40 m with gentle ripple and a ragged hem; its own node for wind sway
    nu, nv = 14, 28
    rng = np.random.default_rng(9)
    hem = rng.uniform(0.0, 0.06, nu + 1)
    hem[::3] += 0.035

    def cloth(u, v):
        x = -0.35 + 0.70 * u
        drop = 1.40 + (hem[int(round(u * nu))] if v < 1e-6 else 0)
        z = (zc - 0.035) - (1 - v) * drop
        y = -0.045 + 0.022 * math.sin(u * 7.0 + (1 - v) * 3.0) * (1 - v) + 0.012 * math.sin(u * 15) * (1 - v) ** 2
        return (x, y, z)

    Y.grid_surface('banner_cloth', cloth, nu, nv, C, [BANNER], uscale=1.0, vscale=1.0, smooth_angle=80, node='banner_cloth')
    for sx in (-0.22, 0.22):  # hanging loops over the bar
        loop = [(sx, 0.045 * math.cos(a) - 0.0, zc + 0.045 * math.sin(a) - 0.0) for a in np.linspace(-math.pi / 2 + 0.15, math.pi * 1.5 - 0.15, 16)]
        Y.tube(f'loop_{sx}', loop, 0.012, 4, C, [GREEN], caps=False)
    return C



# ====================================================================== pipeline
ASSETS = {
    'training-shelter': dict(build=lambda: build_shelter(), res=2048, budget=65000, size=(6.8, 5.9, 4.1),
                             collision=dict(type='compound', note='plinth box 6.4x4.8x0.30 + front steps; four column '
                                            'capsules r0.2 at (+-2.55, +-1.75); roof not walkable')),
    'qi-striking-post': dict(build=lambda: build_qi_post(), res=1024, budget=10500, size=(0.78, 0.79, 1.65),
                             collision=dict(type='box', size=[0.62, 0.62, 1.65], center=[0, 0, 0.825])),
    'agility-post': dict(build=lambda: build_agility_post(), res=1024, budget=6000, size=(1.2, 1.2, 1.67),
                         collision=dict(type='capsule', radius=0.16, height=1.67, center=[0, 0, 0.835],
                                        note='arms are separate nodes; add small capsules when they animate')),
    'weapon-rack': dict(build=lambda: build_weapon_rack(), res=1024, budget=5000, size=(1.9, 0.65, 1.65),
                        collision=dict(type='box', size=[1.8, 0.4, 1.65], center=[0, 0, 0.825])),
    'engraved-training-stone': dict(build=lambda: build_stone(), res=1024, budget=4000, size=(1.9, 1.6, 0.29),
                                    collision=dict(type='box', size=[1.8, 1.5, 0.28], center=[0, 0, 0.14],
                                                   note='walkable top; step height 0.28 m')),
    'training-banner': dict(build=lambda: build_banner(), res=1024, budget=8000, size=(0.85, 0.55, 2.66),
                            collision=dict(type='box', size=[0.55, 0.55, 0.30], center=[0, 0, 0.15],
                                           note='pole capsule r0.05 above the base; cloth has no collision')),
}
# Pivots for animated nodes (Blender coordinates). The demo rotates/sways these.
PIVOTS = {'arm_left': (0, 0, 1.12), 'arm_right': (0, 0, 1.12), 'arm_low': (0, 0, 0.56),
          'banner_cloth': (0, 0, 2.33), 'jade_disc': (0, -0.172, 1.44)}


def build_asset(aid):
    t0 = time.time()
    a = ASSETS[aid]
    Q.reset()
    random.seed(1027)
    src = Q.coll('10_Procedural_Source')
    Q.ACTIVE['coll'] = src
    make_materials()
    a['build']()
    parts = [o for o in src.objects if o.type == 'MESH']
    assign_grain(parts)
    for o in parts:
        if o.get('node', 'body') != 'body':
            o['qa_node'] = o['node']
    Q.finalize_parts(parts, seed=sum(map(ord, aid)))
    bpy.context.view_layer.update()
    game = Q.coll('00_Game_Export')
    Q.ACTIVE['coll'] = game
    G, _ = Q.game_mesh(aid, parts, game)
    tdir = EXPORT / 'textures'
    imgs, alpha = Q.bake_asset(G, aid, tdir, a['res'])
    gm = Q.game_material(aid, imgs, alpha)
    gm.use_backface_culling = aid != 'training-banner'  # only the banner cloth is seen from both sides
    G.data.materials.clear()
    G.data.materials.append(gm)
    G.name = f'{aid}_LOD0'
    lods = Q.make_lods(G, gcoll=game)
    for l, nm in zip(lods, ('LOD1', 'LOD2')):
        l.name = f'{aid}_{nm}'
    nodes = Q.split_nodes(G, aid)
    for o in nodes:  # put animated nodes' origins on their real pivot
        for key, piv in PIVOTS.items():
            if f'_{key}_' in o.name:
                bpy.context.scene.cursor.location = piv
                Q.select_only([o], o)
                bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.context.scene.cursor.location = (0, 0, 0)
    src.hide_render = True
    src.hide_viewport = True
    for l in lods:
        l.hide_render = True
    glb, fbx = EXPORT / f'{aid}.glb', EXPORT / f'{aid}.fbx'
    Q.export(nodes, glb, fbx, nodes + lods)
    # The PWA loads the GLB on phones: re-export it with WebP textures (EXT_texture_webp, about 1/5 the size).
    # The FBX keeps the PNG atlases in textures/ for Unity.
    Q.select_only(nodes, nodes[0])
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format='GLB', use_selection=True, export_apply=True,
                              export_yup=True, export_image_format='WEBP', export_image_quality=88,
                              export_materials='EXPORT', export_extras=False)
    for l in lods:
        l.hide_set(True)
    blend = ROOT / 'blend' / f'{aid}_v1.blend'
    blend.parent.mkdir(exist_ok=True)
    for img in bpy.data.images:
        if img.filepath_raw and img.filepath_raw.startswith(str(tdir)):
            img.filepath = img.filepath_raw
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), compress=True, relative_remap=True)
    bpy.ops.file.make_paths_relative()
    bpy.ops.wm.save_mainfile(compress=True)
    mn, mx = Q.bbox(nodes)
    dims = [round(mx[i] - mn[i], 4) for i in range(3)]
    tris = [sum(Q.tri_count(o) for o in nodes)] + [Q.tri_count(o) for o in lods]
    hs = [Q.mesh_health(o) for o in nodes]
    health = {k: sum(h[k] for h in hs) for k in hs[0]}
    rt_tris, rmn, rmx, rmats = Q.glb_roundtrip(glb)
    v = {
        'asset': aid, 'dimensions_m': dims, 'bbox_min': [round(x, 4) for x in mn], 'bbox_max': [round(x, 4) for x in mx],
        'trianglesLOD': tris, 'budgetLOD0': a['budget'], 'withinBudget': tris[0] <= a['budget'],
        'materials': [m.name for m in G.data.materials], 'textureResolution': a['res'],
        'nodes': [o.name for o in nodes], 'originAtBase': abs(mn[2]) < 0.003, 'meshHealth': health,
        'glbRoundTrip': {'triangles': rt_tris, 'trianglesMatch': rt_tris == tris[0],
                         'bboxMatch': all(abs(p - q) < 0.002 for p, q in zip(rmn + rmx, mn + mx)), 'materials': rmats},
        'files': {p.name: {'bytes': p.stat().st_size, 'sha256': Q.sha(p)} for p in (glb, fbx)},
        'reference': f'art/references/qingxi-training-yard-v1/{aid}-three-view.png',
        'notChecked': ['Unity import', 'in-game lighting', 'mobile performance', 'LOD screen-size thresholds'],
    }
    info = dict(id=aid, units='metre', forward='-Y (Blender) / +Z (glTF)', origin='base centre', dimensions_m=dims,
                triangles=tris[0], lod_triangles=tris, collision=a['collision'],
                pivots={k: p for k, p in PIVOTS.items() if any(f'_{k}_' in o.name for o in nodes)},
                author='Johnnnny0823 (commission, direction) / Claude Code (procedural modelling, bake, validation)',
                validation=v)
    (EXPORT / f'{aid}_model_info.json').write_text(json.dumps(info, indent=1, ensure_ascii=False), encoding='utf-8')
    print(f'[{aid}] tris {tris} dims {dims} health {health} roundtrip {rt_tris} {time.time() - t0:.0f}s', flush=True)
    if RENDER:
        previews(aid, nodes)
    return v


def previews(aid, nodes):
    out = PREV / aid
    Q.gpu(bpy.context.scene, 48)
    if '--quick' in ARGV:  # iteration only: one stylized and one close view
        Q.studio('stylized')
        Q.camera_fit(nodes, 35, 16)
        Q.render(out / 'stylized_three_quarter.png', 900, 48)
        Q.camera_fit(nodes, 12, 10, margin=0.55)
        Q.render(out / 'close_front.png', 900, 48)
        return
    Q.studio('neutral')
    for nm, yaw, pitch in (('01_front', 0, 8), ('02_front_right', 45, 14), ('03_right', 90, 8), ('05_back', 180, 8),
                           ('10_high_front', 0, 38)):
        Q.camera_fit(nodes, yaw, pitch)
        Q.render(out / f'neutral_{nm}.png', 768, 40)
    for nm, yaw, pitch, mg in (('close_front', 12, 10, 0.55), ('close_side', 80, 14, 0.55)):
        Q.camera_fit(nodes, yaw, pitch, margin=mg)
        Q.render(out / f'{nm}.png', 1024, 64)
    wm, nt, b = Q.new_mat('QA_Wire')
    w = Q.N(nt, 'ShaderNodeWireframe', use_pixel_size=True)
    w.inputs['Size'].default_value = 1.0
    Q.L(nt, Q.mix(nt, w.outputs['Fac'], (0.72, 0.72, 0.70), (0.05, 0.05, 0.06)), b.inputs['Base Color'])
    keep = [list(o.data.materials) for o in nodes]
    for o in nodes:
        for i in range(len(o.data.materials)):
            o.data.materials[i] = wm
    Q.camera_fit(nodes, 35, 18)
    Q.render(out / 'wireframe.png', 1024, 24)
    for o, ms in zip(nodes, keep):
        for i, m in enumerate(ms):
            o.data.materials[i] = m
    # orthographic views for the reference comparison sheet (transparent background)
    s = bpy.context.scene
    g = bpy.data.objects.get('QA_Ground')
    if g:
        g.hide_render = True
    s.render.film_transparent = True
    mn, mx = Q.bbox(nodes)
    c = Vector([(mn[i] + mx[i]) / 2 for i in range(3)])
    span = max(mx[i] - mn[i] for i in range(3)) * 1.1
    for view, d in (('front', (0, -1, 0)), ('side', (1, 0, 0)), ('top', (0, 0.0001, 1))):
        cam = s.camera
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = span
        cam.location = c + Vector(d) * 30
        cam.rotation_euler = (-Vector(d)).to_track_quat('-Z', 'Y').to_euler()
        Q.render(out / f'ortho_{view}.png', 900, 48)
    s.render.film_transparent = False
    cam.data.type = 'PERSP'
    for o in list(bpy.data.objects):
        if o.name.startswith('QA_') and o.type in ('LIGHT', 'MESH'):
            bpy.data.objects.remove(o)
    Q.studio('stylized')
    Q.camera_fit(nodes, 35, 16)
    Q.render(out / 'stylized_three_quarter.png', 1024, 64)


def assemble_master():
    """One editable master file: each asset's procedural source and baked game mesh as collections,
    plus a YardPreview scene that instances the game meshes at the demo layout."""
    Q.reset()
    s = bpy.context.scene
    s.name = 'Assets'
    for aid in IDS:
        blend = ROOT / 'blend' / f'{aid}_v1.blend'
        for cname, label in (('10_Procedural_Source', 'source'), ('00_Game_Export', 'game')):
            before = set(bpy.data.collections)
            bpy.ops.wm.append(filepath=str(blend / 'Collection' / cname), directory=str(blend / 'Collection') + '/',
                              filename=cname, link=False)
            new = [c for c in bpy.data.collections if c not in before and c.name.startswith(cname)]
            for c in new:
                c.name = f'{aid}__{label}'
                if label == 'source':
                    c.hide_render = True
                    c.hide_viewport = True
    yard = bpy.data.scenes.new('YardPreview')
    for item in json.loads((ROOT / 'placement.json').read_text(encoding='utf-8')):
        e = bpy.data.objects.new(f"place_{item['id']}", None)
        e.instance_type = 'COLLECTION'
        e.instance_collection = bpy.data.collections[f"{item['id']}__game"]
        e.location = (item['x'], item['y'], item['z'])
        e.rotation_euler = (0, 0, math.radians(item.get('yaw', 0)))
        yard.collection.objects.link(e)
    s['author'] = 'Johnnnny0823 (commission) / Claude Code (modelling)'
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'Qingxi_Training_Yard_v1.blend'), compress=True, relative_remap=True)
    print('MASTER_SAVED', flush=True)


if '--master' in ARGV:
    assemble_master()
else:
    todo = [a for a in ARGV if not a.startswith('--')] or IDS
    report = {aid: build_asset(aid) for aid in todo}
    print('DONE', json.dumps({k: [v['trianglesLOD'], v['glbRoundTrip']['trianglesMatch'], v['withinBudget']]
                              for k, v in report.items()}), flush=True)
