"""Qingxi upstream investigation kit (waterhead A, 2026-10-29). Run in a background Blender 5.2:

  blender -b --python-exit-code 1 --python build_waterhead.py [-- A01_straight_01 A02_side_crack_01 ...] [--no-render] [--quick]
  blender -b --python-exit-code 1 --python build_waterhead.py -- --master

Each asset or shape variant: editable procedural parts built from its saved AI front/side/back view in
art/references/qingxi-waterhead-a/, baked to one atlas (BaseColor, ORM, Normal), LOD1/LOD2, GLB (LOD0, WebP)
+ FBX (LOD0-2), <key>_model_info.json and review renders. Water surfaces stay a separate unbaked, translucent
node (<key>_Clear) together with the vertex-coloured grass clumps. Original procedural modelling only; no third-party meshes.
"""
import sys
import json
import math
import random
import time
from pathlib import Path

import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector, noise

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import geomlib as Y  # noqa: E402
import kitlib as Q  # noqa: E402

REF = ROOT.parents[2] / 'art/references/qingxi-waterhead-a'
EXPORT, PREV = Q.EXPORTS, Q.PREVIEWS
ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
RENDER = '--no-render' not in ARGV

# River module interface (shared by every A01 segment, A04 and later A08): metres above the tile base.
TOP = 1.15        # bank top = surrounding ground; place tile origins at -TOP so banks meet ground 0
BED = 0.25        # channel bed centre
WATER = 0.30      # today's low water surface: a thin flow in the centre groove only
OLD_HI = 0.86     # yesterday's water line: the pale dry band runs from just above WATER up to here
HALF_W = 1.2      # channel half-width at the bed (2.4 m), same at both ends of every segment
TILE_HW = 3.5     # tile half-width across the stream (7 m)


# ====================================================================== materials
def add_moss(m, amount=0.7, up=(0.35, 0.8), color=(0.035, 0.065, 0.012), cover=(0.32, 0.55)):
    """Moss on upward-facing surfaces, broken up by noise (kept in the bake channels)."""
    nt = m.node_tree
    alb = next(n for n in nt.nodes if n.type == 'REROUTE' and n.name == 'CH_albedo')
    src = alb.inputs[0].links[0].from_socket
    nz = Q.sep(nt, Q.N(nt, 'ShaderNodeNewGeometry').outputs['Normal'])[2]
    co = Q.coords(nt, (1, 1, 1))
    mask = Q.math_(nt, 'MULTIPLY', Q.smooth(nt, nz, *up), Q.smooth(nt, Q.noise(nt, co, 2.2, 6, 0.6), *cover))
    tint = Q.mix(nt, Q.noise(nt, co, 9.0, 3), color, (color[0] * 1.6, color[1] * 1.45, color[2] * 1.3))
    Q.L(nt, Q.mix(nt, Q.math_(nt, 'MULTIPLY', mask, amount), src, tint), alb.inputs[0])
    rr = next(n for n in nt.nodes if n.type == 'REROUTE' and n.name == 'CH_rough')
    Q.L(nt, Q.mixf(nt, mask, rr.inputs[0].links[0].from_socket, 0.95), rr.inputs[0])
    return m


def water_bands(m, z_off=0.0, wet_top=WATER + 0.1, old_lo=WATER + 0.16, old_hi=OLD_HI, strength=1.0, dry=((0.125, 0.115, 0.095), (0.09, 0.083, 0.07))):
    """Shared water-history bands on any river-side surface, by height above the tile base (part-local z + z_off):
    dark wet below today's water line, a pale dried silt band up to the old high-water line, a thin dark tide
    mark at that line. Every A01 segment, rock and marker stone shows the same two levels."""
    nt = m.node_tree
    alb = next(n for n in nt.nodes if n.type == 'REROUTE' and n.name == 'CH_albedo')
    rr = next(n for n in nt.nodes if n.type == 'REROUTE' and n.name == 'CH_rough')
    src, rsrc = alb.inputs[0].links[0].from_socket, rr.inputs[0].links[0].from_socket
    co = Q.coords(nt, (1, 1, 1), offset_by_seed=False)
    z = Q.math_(nt, 'ADD', Q.attr(nt, 'qa_wz', 'fac'), z_off)
    zj = Q.math_(nt, 'ADD', z, Q.math_(nt, 'MULTIPLY', Q.noise(nt, co, 3.0, 3), 0.05))          # ragged lines
    wet = Q.math_(nt, 'SUBTRACT', 1.0, Q.smooth(nt, zj, wet_top - 0.03, wet_top + 0.03))
    drym = Q.math_(nt, 'MULTIPLY', Q.smooth(nt, zj, old_lo - 0.04, old_lo + 0.04),
                  Q.math_(nt, 'SUBTRACT', 1.0, Q.smooth(nt, zj, old_hi - 0.02, old_hi + 0.02)))
    tide = Q.math_(nt, 'MULTIPLY', Q.smooth(nt, zj, old_hi - 0.035, old_hi), Q.math_(nt, 'SUBTRACT', 1.0, Q.smooth(nt, zj, old_hi + 0.01, old_hi + 0.04)))
    streak = Q.smooth(nt, Q.noise(nt, Q.coords(nt, (6.0, 6.0, 0.6), offset_by_seed=False), 4.0, 3), 0.45, 0.7)
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', drym, min(1.0, 0.32 * strength)), src, Q.mix(nt, streak, *dry))
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', tide, min(1.0, 0.9 * strength)), col, (0.03, 0.026, 0.02))
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', wet, min(1.0, 0.8 * strength)), col, Q.mix(nt, streak, (0.022, 0.024, 0.02), (0.04, 0.042, 0.035)))
    Q.L(nt, col, alb.inputs[0])
    Q.L(nt, Q.mixf(nt, Q.math_(nt, 'MULTIPLY', wet, strength), Q.mixf(nt, drym, rsrc, 0.97), 0.48), rr.inputs[0])
    return m


def m_riverbank(name='Riverbank'):
    """One material for a whole river tile, chosen by height and slope: dry ochre meadow on the bank tops,
    warm soil with stone outcrops on the banks, wet gravel in the channel; then the shared water bands."""
    m, nt, b = Q.new_mat(name)
    co = Q.coords(nt, (1, 1, 1), offset_by_seed=False)
    z = Q.attr(nt, 'qa_wz', 'fac')
    nz = Q.sep(nt, Q.N(nt, 'ShaderNodeNewGeometry').outputs['Normal'])[2]
    n1, n2 = Q.noise(nt, co, 1.4, 5, 0.6), Q.noise(nt, co, 16.0, 4, 0.6)
    soil = Q.mix(nt, Q.smooth(nt, n1, 0.3, 0.7), (0.045, 0.034, 0.023), (0.09, 0.068, 0.046))
    stone = Q.mix(nt, Q.smooth(nt, Q.noise(nt, co, 3.0, 6, 0.65), 0.3, 0.75), (0.10, 0.095, 0.085), (0.24, 0.225, 0.20))
    steep = Q.math_(nt, 'MULTIPLY', Q.math_(nt, 'SUBTRACT', 1.0, Q.smooth(nt, nz, 0.45, 0.8)), Q.smooth(nt, n1, 0.35, 0.55))
    col = Q.mix(nt, steep, soil, stone)
    # meadow on flat ground near the bank top: dry ochre with a few green patches
    meadow = Q.math_(nt, 'MULTIPLY', Q.smooth(nt, nz, 0.8, 0.95), Q.smooth(nt, z, TOP - 0.25, TOP - 0.08))
    grass = Q.mix(nt, Q.smooth(nt, Q.noise(nt, co, 1.1, 4), 0.35, 0.7), (0.11, 0.09, 0.045), (0.19, 0.155, 0.075))
    grass = Q.mix(nt, Q.math_(nt, 'MULTIPLY', Q.smooth(nt, Q.noise(nt, co, 0.7, 3), 0.55, 0.7), 0.85), grass, (0.055, 0.075, 0.025))
    blades = Q.smooth(nt, Q.noise(nt, co, 80.0, 2, 0.5), 0.45, 0.72)
    grass = Q.mix(nt, Q.math_(nt, 'MULTIPLY', blades, 0.35), grass, (0.36, 0.30, 0.15))
    col = Q.mix(nt, meadow, col, grass)
    # gravel in the channel: rounded pebbles with dark gaps
    vo = Q.voronoi(nt, co, 9.0, 'F1', 'Color')
    peb = Q.mix(nt, Q.sep(nt, vo)[0], (0.07, 0.066, 0.058), (0.19, 0.18, 0.16))
    gap = Q.smooth(nt, Q.voronoi(nt, co, 9.0, 'DISTANCE_TO_EDGE'), 0.0, 0.06)
    peb = Q.mix(nt, Q.math_(nt, 'SUBTRACT', 1.0, gap), peb, (0.04, 0.035, 0.03))
    bed = Q.math_(nt, 'SUBTRACT', 1.0, Q.smooth(nt, z, WATER + 0.02, WATER + 0.16))
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', bed, Q.smooth(nt, nz, 0.5, 0.8)), col, peb)
    cav, edge = Q.edge_cavity(nt, 0.08, 0.01)
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', Q.smooth(nt, cav, 0.1, 0.6), 0.55), col, (0.02, 0.018, 0.014))
    rough = Q.mixf(nt, n2, 0.82, 0.95)
    hgt = Q.math_(nt, 'ADD', Q.math_(nt, 'MULTIPLY', n2, 0.5), Q.math_(nt, 'MULTIPLY', Q.math_(nt, 'MULTIPLY', gap, bed), 0.8))
    Q.finish(m, nt, b, col, rough, 0.0, hgt, 0.006, 0.9)
    return water_bands(m)


def m_cutsoil(name='CutSoil'):
    """Tile cross-section (only seen at the open end of a run): layered soil, gravel and stone."""
    m, nt, b = Q.new_mat(name)
    co = Q.coords(nt, (1, 1, 1), offset_by_seed=False)
    z = Q.sep(nt, Q.attr(nt, 'qa_lc'))[2]
    layer = Q.N(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='Z')
    Q.L(nt, co, layer.inputs['Vector'])
    layer.inputs['Scale'].default_value = 2.2
    layer.inputs['Distortion'].default_value = 3.0
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', Q.smooth(nt, layer.outputs['Fac'], 0.3, 0.7), 0.5), (0.07, 0.05, 0.034), (0.12, 0.09, 0.062))
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', Q.smooth(nt, Q.voronoi(nt, co, 12.0), 0.0, 0.2), 0.5), col, (0.17, 0.16, 0.14))
    return Q.finish(m, nt, b, col, 0.95, 0.0, Q.noise(nt, co, 20.0, 3), 0.004, 0.8)


def m_water(name='LowWater'):
    """Unbaked translucent water (kept as its own node): low-saturation blue-green, slightly rough."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (0.05, 0.11, 0.105, 1)
    b.inputs['Roughness'].default_value = 0.08
    b.inputs['Alpha'].default_value = 0.42
    b.inputs['IOR'].default_value = 1.33
    m.surface_render_method = 'BLENDED'
    m.use_backface_culling = False
    m['qa_nobake'] = True
    return m


def m_grass_vc(name='GrassClump'):
    """Unbaked, shared by every clump: base colour from the per-vertex 'Col' attribute, both sides rendered."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    ca = nt.nodes.new('ShaderNodeVertexColor')
    ca.layer_name = 'Col'
    nt.links.new(ca.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.85
    m.use_backface_culling = False
    m['qa_nobake'] = True
    return m


def make_materials():
    g = {}
    g['BANK'] = m_riverbank()
    g['CUT'] = m_cutsoil()
    g['ROCK'] = water_bands(strength=0.55, m=add_moss(Q.m_stone('BankStone', light=(0.16, 0.15, 0.13), dark=(0.055, 0.052, 0.046), scale=1.2, chisel=1.8),
                                     0.55, (0.55, 0.9)))
    g['PEBBLE'] = water_bands(Q.m_stone('Pebble', light=(0.20, 0.19, 0.17), dark=(0.075, 0.072, 0.066), scale=2.5, speck=0.6, chisel=0.6))
    g['STRATA'] = water_bands(strength=0.6, m=add_moss(Q.m_stone('StrataFace', light=(0.27, 0.22, 0.16), dark=(0.11, 0.095, 0.075), scale=1.4, chisel=2.6),
                                       0.45, (0.55, 0.9)))
    g['ROOTWOOD'] = water_bands(Q.m_bark('ExposedRoot'))
    g['DRYGRASS'] = Q.m_simple('DryGrass', (0.22, 0.16, 0.06), (0.40, 0.31, 0.13), rough=0.85, nscale=14.0, cav_col=(0.09, 0.06, 0.025))
    g['GREENBLADE'] = Q.m_simple('GreenBlade', (0.05, 0.08, 0.02), (0.12, 0.15, 0.045), rough=0.85, nscale=12.0)
    g['WATERM'] = m_water()
    g['GRASSVC'] = m_grass_vc()
    g['SLUICE'] = add_moss(m_sluice_stone(), 0.5, (0.6, 0.95), cover=(0.45, 0.6))
    g['FSTONE'] = add_moss(Q.m_stone('FormationStone', light=(0.24, 0.225, 0.20), dark=(0.10, 0.095, 0.085), scale=1.3, chisel=1.4), 0.55, (0.55, 0.95))
    g['BRONZE'] = Q.m_simple('Verdigris', (0.07, 0.16, 0.12), (0.17, 0.29, 0.22), rough=0.7, metal=0.25, nscale=14.0, bump=0.0015,
                             cav_col=(0.035, 0.05, 0.035), edge_col=(0.16, 0.10, 0.05))
    g['SOILM'] = add_moss(Q.m_simple('HeapedSoil', (0.05, 0.036, 0.024), (0.10, 0.075, 0.05), rough=0.95, nscale=12.0, bump=0.003), 0.4, (0.6, 0.95))
    g['SILT'] = m_silt()
    g['CRACKMUD'] = m_crackmud()
    g['MARKER'] = water_bands(add_moss(Q.m_stone('MarkerStone', light=(0.17, 0.16, 0.14), dark=(0.065, 0.062, 0.055), scale=1.4, chisel=1.6), 0.85, (0.5, 0.95)),
                              wet_top=0.35, old_lo=0.38, old_hi=0.86, strength=1.4, dry=((0.30, 0.28, 0.24), (0.24, 0.225, 0.19)))
    g['MUD'] = Q.m_simple('WetMud', (0.035, 0.026, 0.018), (0.07, 0.05, 0.032), rough=0.3, nscale=10.0, bump=0.002)
    globals().update(g)


def m_sluice_stone(name='SluiceStone'):
    """Dressed warm-grey trough stone with a carved cloud band (part-local z 0.22-0.34) and silt at the base."""
    m, nt, b = Q.new_mat(name)
    co = Q.coords(nt, (1, 1, 1))
    lc = Q.sep(nt, Q.attr(nt, 'qa_lc'))
    n1, n2 = Q.noise(nt, co, 2.2, 6, 0.6), Q.noise(nt, co, 18.0, 4)
    col = Q.mix(nt, Q.smooth(nt, n1, 0.3, 0.75), (0.13, 0.12, 0.105), (0.27, 0.255, 0.225))
    wz = Q.attr(nt, 'qa_wz', 'fac')   # world height of each vertex (stored by build_A02)
    band = Q.math_(nt, 'MULTIPLY', Q.smooth(nt, wz, 0.21, 0.23), Q.math_(nt, 'SUBTRACT', 1.0, Q.smooth(nt, wz, 0.33, 0.35)))
    wave = Q.N(nt, 'ShaderNodeTexWave', wave_type='RINGS')
    Q.L(nt, Q.coords(nt, (1.0, 1.0, 1.0), offset_by_seed=False), wave.inputs['Vector'])
    wave.inputs['Scale'].default_value = 6.0
    wave.inputs['Distortion'].default_value = 6.0
    wave.inputs['Detail'].default_value = 1.0
    carve = Q.math_(nt, 'MULTIPLY', band, Q.smooth(nt, wave.outputs['Fac'], 0.55, 0.75))
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', carve, 0.5), col, (0.07, 0.065, 0.055))
    silt = Q.math_(nt, 'SUBTRACT', 1.0, Q.smooth(nt, Q.math_(nt, 'ADD', wz, Q.math_(nt, 'MULTIPLY', n1, 0.06)), 0.03, 0.14))
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', silt, 0.75), col, (0.11, 0.085, 0.055))
    cav, edge = Q.edge_cavity(nt, 0.035, 0.006)
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', Q.smooth(nt, cav, 0.1, 0.6), 0.6), col, (0.04, 0.036, 0.03))
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', Q.smooth(nt, edge, 0.3, 0.8), 0.35), col, (0.36, 0.34, 0.30))
    hgt = Q.math_(nt, 'SUBTRACT', Q.math_(nt, 'MULTIPLY', n2, 0.4), Q.math_(nt, 'MULTIPLY', carve, 1.2))
    return Q.finish(m, nt, b, col, Q.mixf(nt, n2, 0.78, 0.92), 0.0, hgt, 0.004, 0.9)


# ====================================================================== shape helpers
def coll():
    return Q.ACTIVE['coll']


def smoothstep(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def boulder(name, radii, loc, mat, seed=1, subd=3, rough=0.16, rot=0.0, squash_top=0.0, cleave=3, box=2.0, ground=0.0, tilt=(0.0, 0.0)):
    """Noise-displaced stone; anything below `ground` (world z) is flattened onto it (seated, not floating)."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subd, radius=1.0)
    off = Vector((seed * 1.37, seed * 2.11, seed * 0.73))
    rmat = Matrix.Rotation(tilt[0], 3, 'X') @ Matrix.Rotation(tilt[1], 3, 'Y')
    for v in bm.verts:
        d = v.co.normalized()
        if box != 2.0:
            d = d / (abs(d.x) ** box + abs(d.y) ** box + abs(d.z) ** box) ** (1 / box)
        k = 1 + rough * noise.fractal(d * 1.4 + off, 0.55, 2.0, 5) + 0.05 * noise.noise(d * 6 + off)
        p = Vector((d.x * radii[0] * k, d.y * radii[1] * k, d.z * radii[2] * k))
        if squash_top and p.z > 0:
            p.z *= 1 - squash_top
        for ci in range(cleave):
            nrm = Vector((math.sin(seed * 3.1 + ci * 2.4), math.cos(seed * 1.7 + ci * 1.3), 0.6 * math.sin(seed + ci))).normalized()
            lim = 0.78 * (radii[0] * abs(nrm.x) + radii[1] * abs(nrm.y) + radii[2] * abs(nrm.z))
            dd = p.dot(nrm)
            if dd > lim:
                p -= nrm * (dd - lim) * 0.85
        p = rmat @ p
        c, s = math.cos(rot), math.sin(rot)
        p = Vector((p.x * c - p.y * s, p.x * s + p.y * c, p.z))
        p.z = max(p.z, ground - loc[2])
        v.co = p
    o = Q._obj(name, bm, mat, sharp=60)
    o.location = loc
    return o


def tuft(name, x, y, z, h=0.22, n=6, seed=0, mat=None, droop=0.0):
    """Low-poly grass clump: single-sided blades (the material renders both sides), coloured per vertex (dark root,
    lighter tip, a little hue drift per clump) so every clump shares one small unbaked material."""
    rnd = random.Random(seed)
    green = mat is GREENBLADE
    base_c = (0.035, 0.05, 0.015) if green else (0.07, 0.05, 0.02)
    tip_c = (0.11, 0.15, 0.04) if green else rnd.choice(((0.42, 0.32, 0.13), (0.36, 0.27, 0.11), (0.30, 0.25, 0.12)))
    verts, faces, cols = [], [], []
    for i in range(n):
        a = rnd.uniform(0, math.tau)
        w = rnd.uniform(0.010, 0.02)
        hh = h * rnd.uniform(0.6, 1.15)
        lean = rnd.uniform(0.15, 0.45) + droop
        d = Vector((math.cos(a), math.sin(a), 0))
        side = Vector((-d.y, d.x, 0)) * w
        segs = 3 if droop else 1
        base = d * 0.03
        prev = [base - side, base + side]
        prev_t = 0.0
        for sgi in range(1, segs + 1):
            t = sgi / segs
            p = base + d * hh * lean * t + Vector((0, 0, hh * (t - droop * t * t * 1.2)))
            c0 = tuple(base_c[j] + (tip_c[j] - base_c[j]) * prev_t for j in range(3))
            c1 = tuple(base_c[j] + (tip_c[j] - base_c[j]) * t for j in range(3))
            k = len(verts)
            if sgi == segs:
                verts += [tuple(prev[0]), tuple(prev[1]), tuple(p)]
                faces.append((k, k + 1, k + 2))
                cols += [c0, c0, c1]
            else:
                cur = [p - side * (1 - t), p + side * (1 - t)]
                verts += [tuple(prev[0]), tuple(prev[1]), tuple(cur[1]), tuple(cur[0])]
                faces.append((k, k + 1, k + 2, k + 3))
                cols += [c0, c0, c1, c1]
                prev = cur
            prev_t = t
    o = Y.make_mesh(name, verts, faces, None, [GRASSVC], coll=coll())
    ca = o.data.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
    for i, c in enumerate(cols):
        ca.data[i].color = (*c, 1.0)
    o.location = (x, y, z)
    return o


# ====================================================================== A01 river module frame
class Course:
    """Centre line of a river module in tile coordinates: starts at the origin heading +Y (upstream), turns by
    `turn` radians (+ = left, towards -X) at constant curvature over length L. (u, s) -> (x, y): u along, s across
    (+ = right bank, looking upstream)."""

    def __init__(self, L, turn=0.0, closed=False):
        self.L, self.turn, self.k, self.closed = L, turn, turn / L, closed

    def w(self, u):
        """0 at an interface end, 1 inside. A closed (terminal) module has an interface only at u = 0."""
        return smoothstep(0.0, 0.9, u) * (1.0 if self.closed else smoothstep(0.0, 0.9, self.L - u))

    def frame(self, u):
        a = self.k * u
        if abs(self.k) < 1e-9:
            p = Vector((0.0, u, 0.0))
        else:
            p = Vector(((math.cos(a) - 1) / self.k, math.sin(a) / self.k, 0.0))
        return p, Vector((-math.sin(a), math.cos(a), 0.0)), Vector((math.cos(a), math.sin(a), 0.0))

    def at(self, u, s, z=0.0):
        p, _, r = self.frame(u)
        q = p + r * s
        return Vector((q.x, q.y, z))

    def out_port(self):
        p, d, _ = self.frame(self.L)
        return [round(p.x, 4), round(p.y, 4), round(math.degrees(self.turn), 3)]


def profile(s, hw_l=HALF_W, hw_r=HALF_W, slope_l=1.0, slope_r=1.0, top_l=TOP, top_r=TOP):
    """Channel cross-section height at lateral offset s. Ends of every module use the defaults (the interface)."""
    hw, slope, top = (hw_r, slope_r, top_r) if s >= 0 else (hw_l, slope_l, top_l)
    a = abs(s)
    top += (TOP - top) * smoothstep(TILE_HW - 1.1, TILE_HW - 0.25, a)   # a raised bank always comes back to ground level at the tile's side edge
    if a <= hw:
        return BED + 0.14 * (a / hw) ** 1.6
    t = smoothstep(0.0, slope, a - hw)
    return BED + 0.14 + (top - BED - 0.14) * (t ** 0.9)


def river_tile(name, course, shape, nu=44, ns=52, seed=1):
    """Top surface over (u, s) + side skirts down to z = 0 + base. shape(u, s, w) -> z, where w is 0 at both
    interface ends and 1 inside; within 0.9 m of each end the cross-section is the shared interface profile."""
    L = course.L
    rnd_off = Vector((seed * 3.3, seed * 1.7, 0))
    verts, faces, fmat = [], [], []
    for j in range(nu + 1):
        u = L * j / nu
        w = course.w(u)
        for i in range(ns + 1):
            s = -TILE_HW + 2 * TILE_HW * i / ns
            z = shape(u, s, w)
            # small undulation inside the tile only (edges along the stream stay at TOP so the tile meets flat ground)
            edge = smoothstep(0.0, 0.6, TILE_HW - abs(s))
            z += w * edge * 0.05 * noise.noise(Vector((u * 0.9, s * 0.9, 0)) + rnd_off)
            sl = (z - BED) / (TOP - BED)
            slope_w = smoothstep(0.12, 0.3, sl) * (1 - smoothstep(0.85, 0.98, sl))      # banks only: lumps, gullies, small terraces
            z += w * slope_w * (0.10 * noise.fractal(Vector((u * 1.3, s * 1.1, 3.0)) + rnd_off, 0.6, 2.0, 4)
                            + 0.04 * math.sin(z * 22.0 + noise.noise(Vector((u, s, 0)) * 2.0) * 3.0))
            verts.append(tuple(course.at(u, s, z)))
    W = ns + 1
    for j in range(nu):
        for i in range(ns):
            a = j * W + i
            faces.append((a, a + 1, a + W + 1, a + W))
            fmat.append(0)
    border = [i for i in range(ns + 1)] + [j * W + ns for j in range(1, nu + 1)] + \
             [nu * W + i for i in range(ns - 1, -1, -1)] + [j * W for j in range(nu - 1, 0, -1)]
    base = []
    for bi in border:
        x, y, _ = verts[bi]
        base.append(len(verts))
        verts.append((x, y, 0.0))
    nb = len(border)
    for k in range(nb):
        a, b = border[k], border[(k + 1) % nb]
        faces.append((a, base[k], base[(k + 1) % nb], b))
        fmat.append(1)
    # no bottom cap: never seen, and it would take atlas space
    o = Y.make_mesh(name, verts, faces, None, [BANK, CUT], fmat, coll(), smooth_angle=60)
    Y.recalc_normals(o)
    return o


def water_strip(name, course, shape, level, nu=40, u_max=None):
    """Water surface between the two points where the bed rises above `level` (per u); level(u) may vary."""
    verts, faces = [], []
    for j in range(nu + 1):
        u = (u_max or course.L) * j / nu
        w = course.w(u)
        lv = level(u, w)
        edges = []
        for side in (-1, 1):
            s = 0.0
            while abs(s) < TILE_HW - 0.2 and shape(u, s, w) < lv:
                s += side * 0.02
            edges.append(s + side * 0.03)   # tuck the edge just into the bank
        c = 0.5 * (edges[0] + edges[1])
        for s in (edges[0], c, edges[1]):
            verts.append(tuple(course.at(u, s, lv)))
    for j in range(nu):
        a = j * 3
        faces += [(a, a + 1, a + 4, a + 3), (a + 1, a + 2, a + 5, a + 4)]
    o = Y.make_mesh(name, verts, faces, None, [WATERM], coll=coll(), smooth_angle=80)
    return o


def bed_stones(name, course, shape, n, seed, lo=-1.6, hi=1.6, size=(0.07, 0.2), keep=None):
    """Pebbles and cobbles seated on the channel bed and lower banks."""
    rnd = random.Random(seed)
    k = 0
    for _ in range(n * 6):
        if k >= n:
            break
        u = rnd.uniform(0.25, course.L - 0.25)
        s = rnd.uniform(lo, hi)
        if keep and not keep(u, s):
            continue
        w = course.w(u)
        z = shape(u, s, w)
        r = rnd.uniform(*size) * (1.0 if rnd.random() < 0.8 else 1.6)
        p = course.at(u, s, z - r * 0.35)
        boulder(f'{name}_{k}', (r, r * rnd.uniform(0.7, 1.0), r * rnd.uniform(0.45, 0.7)), tuple(p), PEBBLE,
                seed=seed * 7 + k, subd=1 if r < 0.12 else 2, rough=0.12, rot=rnd.uniform(0, math.tau), ground=z - r * 0.4, cleave=1)
        k += 1


def bank_rocks(name, course, shape, spots, seed, mat=None):
    """Embedded boulders on the banks: spots = [(u, s, (rx, ry, rz)), ...]."""
    for k, (u, s, rad) in enumerate(spots):
        w = course.w(u)
        z = shape(u, s, w)
        _, d, _ = course.frame(u)
        rot = math.atan2(d.y, d.x) + random.Random(seed + k).uniform(-0.4, 0.4)
        boulder(f'{name}_{k}', rad, tuple(course.at(u, s, z - rad[2] * 0.3)), mat or ROCK, seed=seed + k, subd=3, rough=0.26,
                rot=rot, cleave=5, box=2.6, tilt=(random.Random(seed * 3 + k).uniform(-0.3, 0.3), 0.0))


def roots(name, course, shape, spots, seed):
    """Tree roots creeping over the bank lip and down into the soil (spots = [(u, s_lip, side), ...])."""
    rnd = random.Random(seed)
    for k, (u, s0, side) in enumerate(spots):
        pts = []
        for t in np.linspace(0, 1, 9):
            s = s0 - side * 0.9 * t
            uu = u + 0.25 * math.sin(t * 3 + k)
            w = course.w(uu)
            z = shape(uu, s, w) + 0.03 - 0.06 * t
            pts.append(tuple(course.at(uu, s, z)))
        Y.tube(f'{name}_{k}', pts, lambda t: 0.05 * (1 - 0.7 * t) + 0.01, 7, coll(), [ROOTWOOD], caps=False)


def top_grass(name, course, shape, n, seed, s_min=2.0, s_max=TILE_HW - 0.35):
    rnd = random.Random(seed)
    for k in range(n):
        u = rnd.uniform(0.2, course.L - 0.2)
        s = rnd.choice((-1, 1)) * rnd.uniform(s_min, s_max)
        w = course.w(u)
        p = course.at(u, s, shape(u, s, w) - 0.01)
        green = rnd.random() < 0.18
        tuft(f'{name}_{k}', p.x, p.y, p.z, h=rnd.uniform(0.22, 0.42), n=10, seed=seed + k,
             mat=GREENBLADE if green else DRYGRASS, droop=0.0 if green else rnd.uniform(0.15, 0.4))


def gentle(u, s, w, **kw):
    """Shape helper: the interface profile with inner-tile overrides faded in by w."""
    base = profile(s)
    if not kw:
        return base
    return base + w * (profile(s, **kw) - base)


def build_river(variant):
    rnd = random.Random(hash(variant) % 997)
    if variant == 'straight':
        course = Course(6.0)

        def shape(u, s, w):
            off = 0.25 * math.sin(math.pi * u / course.L) * w            # the low flow wanders a little
            return gentle(u, s - off, w, slope_l=1.1, slope_r=0.85)
        rocks = [(1.6, -1.9, (0.42, 0.35, 0.32)), (4.3, 2.1, (0.5, 0.42, 0.38)), (3.0, -2.4, (0.3, 0.28, 0.22)),
                 (5.1, -1.7, (0.28, 0.24, 0.2))]
        root = [(1.2, -2.3, -1), (3.6, 2.4, 1), (4.0, 2.2, 1)]
    elif variant == 'bend_left':
        course = Course(6.5, math.radians(25))

        def shape(u, s, w):   # inner (left) bank: wide gravel point bar; outer (right) bank steeper
            return gentle(u, s, w, hw_l=HALF_W + 0.7, slope_l=1.4, slope_r=0.6, hw_r=HALF_W - 0.15)
        rocks = [(3.2, 2.15, (0.75, 0.55, 0.7)), (1.4, 2.4, (0.4, 0.35, 0.3)), (5.0, 2.0, (0.35, 0.3, 0.3)),
                 (2.4, -2.9, (0.3, 0.26, 0.22))]
        root = [(4.2, 2.5, 1)]
    elif variant == 'bend_right':
        course = Course(6.5, math.radians(-40))

        def shape(u, s, w):   # outer (left) bank: tall undercut rock face; inner (right) bank: low sandy bar
            return gentle(u, s, w, hw_r=HALF_W + 0.6, slope_r=1.5, hw_l=HALF_W - 0.1, slope_l=0.35, top_l=TOP + 0.55)
        rocks = []
        root = [(2.2, -1.7, -1), (3.4, -1.75, -1), (4.4, -1.65, -1)]
    elif variant == 'narrow':
        course = Course(6.0)

        def shape(u, s, w):   # pinched to ~1.2 m between two rock outcrops in the middle
            pinch = math.exp(-((u - 3.0) / 0.9) ** 2)
            return gentle(u, s, w, hw_l=HALF_W - 0.62 * pinch, hw_r=HALF_W - 0.6 * pinch, slope_l=1.0 - 0.6 * pinch,
                          slope_r=1.0 - 0.6 * pinch)
        rocks = [(3.0, -1.35, (0.85, 0.75, 1.05)), (2.9, 1.4, (0.8, 0.85, 0.95)), (1.7, -1.9, (0.4, 0.35, 0.35)),
                 (4.3, 1.95, (0.45, 0.4, 0.4)), (3.5, -1.05, (0.35, 0.3, 0.45))]
        root = [(1.5, 2.3, 1)]
    elif variant == 'end_source':
        course = Course(4.0, closed=True)

        def shape(u, s, w):   # the bed climbs into a boulder jam; a shallow spring pool at its foot
            base = gentle(u, s, w)
            pool = math.exp(-((u - 1.5) / 0.55) ** 2) * max(0.0, 1 - abs(s) / 1.0)
            c = smoothstep(1.6, 3.7, u)
            return base - 0.07 * pool + (TOP + 0.05 - base) * c * smoothstep(0.0, 1.0, 3.4 - abs(s) + 1.0)
        rocks = [(2.5, -0.6, (0.55, 0.5, 0.6)), (2.6, 0.7, (0.5, 0.45, 0.5)), (3.2, -1.5, (0.7, 0.6, 0.75)), (3.3, 0.1, (0.85, 0.7, 0.95)),
                 (3.2, 1.6, (0.65, 0.6, 0.7)), (2.2, -1.75, (0.4, 0.35, 0.35)), (2.1, 1.8, (0.38, 0.34, 0.32)), (3.7, -0.8, (0.6, 0.5, 0.6)),
                 (3.7, 1.0, (0.55, 0.5, 0.55)), (2.9, -0.15, (0.3, 0.28, 0.3)), (1.9, -1.15, (0.24, 0.2, 0.2)), (1.95, 1.2, (0.22, 0.2, 0.18))]
        root = [(3.0, 2.3, 1), (3.4, -2.4, -1)]
    else:
        raise ValueError(variant)
    river_tile(f'A01_{variant}_bank', course, shape, seed=hash(variant) % 97)

    def level(u, w):
        if variant == 'narrow':   # water heaps up a little in the pinch
            return WATER + 0.05 * math.exp(-((u - 3.0) / 0.6) ** 2) * w
        if variant == 'end_source':   # the spring pool sits a little higher than the outflow
            return WATER + 0.02 * smoothstep(0.6, 1.4, u)
        return WATER
    water_strip(f'A01_{variant}_water', course, shape, level, u_max=2.15 if variant == 'end_source' else None)
    bank_rocks(f'A01_{variant}_rock', course, shape, rocks, seed=40 + len(variant))
    if variant == 'bend_right':   # the outer cliff is built from stacked, overhanging strata ledges
        k = 0
        for layer in range(5):
            u = 0.8 + rnd.uniform(0, 0.3)
            while u < course.L - 0.7:
                ln = rnd.uniform(0.7, 1.4)
                w = course.w(u)
                z = BED + 0.3 + layer * 0.26 + rnd.uniform(-0.04, 0.04)
                s_face = -HALF_W + 0.1 - 0.12 * layer
                while shape(u, s_face, w) < z and s_face > -TILE_HW + 0.5:   # walk into the bank until the slab meets it
                    s_face -= 0.05
                if z < shape(u, s_face, w) + 0.3 and w > 0.3:
                    boulder(f'A01_bend_right_strata_{k}', (ln / 2, 0.34 + 0.04 * layer, rnd.uniform(0.06, 0.12)),
                            tuple(course.at(u + ln / 2, s_face + rnd.uniform(-0.02, 0.16), z)), STRATA, seed=300 + k, subd=2,
                            rough=0.16, box=6.0, cleave=5, rot=course.k * (u + ln / 2) + math.pi / 2 + rnd.uniform(-0.08, 0.08),
                            tilt=(rnd.uniform(-0.06, 0.06), rnd.uniform(-0.05, 0.05)))
                    k += 1
                u += ln + rnd.uniform(0.02, 0.08)
    if variant == 'narrow':   # a sill of stones across the pinch: the water breaks white here
        for k in range(5):
            s = -0.5 + k * 0.25
            bed = shape(3.0, s, 1.0)
            boulder(f'A01_narrow_sill_{k}', (0.16, 0.13, 0.12), tuple(course.at(3.0 + 0.05 * (k % 2), s, bed + 0.03)), PEBBLE,
                    seed=500 + k, subd=2, rough=0.15, ground=bed)
    if variant == 'end_source':   # trickles seeping out between the boulders into the pool, ferns in the damp gaps
        for k, (u0, s0, z0) in enumerate(((3.05, -0.45, 1.05), (2.75, 0.4, 0.85))):
            pts = [tuple(course.at(u0 - 1.0 * t, s0 * (1 - 0.4 * t), z0 * (1 - t) + (WATER + 0.02) * t + 0.12 * math.sin(math.pi * t))) for t in np.linspace(0, 1, 8)]
            Y.tube(f'A01_end_source_trickle_{k}', pts, lambda t: 0.05 + 0.04 * t, 8, coll(), [WATERM], caps=False)
        for k in range(14):
            u = rnd.uniform(2.0, 3.8)
            s_ = rnd.uniform(-2.4, 2.4)
            p = course.at(u, s_, shape(u, s_, course.w(u)) - 0.02)
            tuft(f'A01_end_source_fern_{k}', p.x, p.y, p.z, h=rnd.uniform(0.25, 0.42), n=9, seed=700 + k, mat=GREENBLADE, droop=0.35)
    roots(f'A01_{variant}_root', course, shape, root, seed=60)
    # embedded stones all along both banks (half buried in the slope), then gravel and cobbles, then grass on the lip
    slope_spots = []
    for k in range(16):
        u = rnd.uniform(0.4, course.L - 0.4)
        side = rnd.choice((-1, 1))
        r = rnd.uniform(0.16, 0.38)
        slope_spots.append((u, side * rnd.uniform(1.35, 2.3), (r * 1.2, r, r * 0.8)))
    bank_rocks(f'A01_{variant}_slope', course, shape, slope_spots, seed=140 + len(variant))
    bed_stones(f'A01_{variant}_peb', course, shape, 32 if variant == 'end_source' else 70, seed=70 + len(variant), lo=-1.9, hi=1.9, size=(0.05, 0.12))
    bed_stones(f'A01_{variant}_cob', course, shape, 14, seed=170 + len(variant), lo=-1.4, hi=1.4, size=(0.14, 0.24))
    top_grass(f'A01_{variant}_lip', course, shape, 60, seed=90, s_min=2.0, s_max=2.7)
    top_grass(f'A01_{variant}_slopegrass', course, shape, 18, seed=290, s_min=1.6, s_max=2.1)
    top_grass(f'A01_{variant}_grass', course, shape, 24, seed=190, s_min=2.7)
    return course


# ====================================================================== A02 cracked ancient sluice trough
def trough_block(name, x0, x1, inner_w=0.42, wall_h=0.55, floor_z=0.13, z0=0.12, mats=None):
    """One U-section trough stone from x0 to x1 (along X), sitting on the footing at z0."""
    W2, I2 = 0.35, inner_w / 2
    poly = [(-W2, z0), (W2, z0), (W2, z0 + wall_h), (I2, z0 + wall_h), (I2, z0 + floor_z + 0.12),
            (I2 * 0.75, z0 + floor_z + 0.02), (0.0, z0 + floor_z), (-I2 * 0.75, z0 + floor_z + 0.02), (-I2, z0 + floor_z + 0.12),
            (-I2, z0 + wall_h), (-W2, z0 + wall_h)]
    # prism draws in the XZ plane and extrudes along Y; build along Y and rotate onto X
    o = Y.prism(name, poly, x1 - x0, coll(), mats or [SLUICE], plane='XZ')
    o.rotation_euler = (0, 0, math.radians(90))
    o.location = ((x0 + x1) / 2, 0, 0)
    Q.add_bevel(o, 0.012, 2)
    return o


def build_A02(variant):
    rnd = random.Random(2 if variant == 'side_crack' else 3)
    for k in range(13):                       # footing course of small dressed stones
        x = -1.5 + 0.115 + k * 0.23
        Y.block(f'A02_foot_{k}', (0.22, 0.8, 0.12), (x, 0.0, 0.06), coll(), [SLUICE], bev=0.015)
    blocks = [(-1.5, -0.5), (-0.5, 0.5), (0.5, 1.5)]
    parts = []
    for i, (x0, x1) in enumerate(blocks):
        if variant == 'end_break' and i == 2:
            continue
        parts.append(trough_block(f'A02_block_{i}', x0 + 0.004, x1 - 0.004))
    for sx in (-1, 1):                         # end posts
        Y.block(f'A02_post_{sx}', (0.16, 0.74, 0.62), (sx * 1.42, 0.0, 0.12 + 0.31), coll(), [SLUICE], bev=0.02)
    if variant == 'side_crack':
        mid = parts[1]
        cut = boulder('A02_chunk_cut', (0.14, 0.22, 0.17), (0.02, -0.36, 0.42), SLUICE, seed=21, subd=2, rough=0.3, ground=-9)
        Q.boolean(mid, cut)
        crack = Y.block('A02_crack_cut', (0.025, 0.5, 0.5), (0.05, -0.3, 0.42), coll(), [SLUICE], bev=0.0, rot=(0, math.radians(8), 0))
        Q.boolean(mid, crack)
        Q.apply_mods(mid)
        leak = (0.03, -0.37, 0.36)
    else:
        # the last stone cracked on a diagonal; its outer end and the end post tipped out over the edge (+X)
        inner = trough_block('A02_block_2_inner', 0.504, 1.5)
        outer = trough_block('A02_block_2_outer', 0.504, 1.5)
        for o, side in ((inner, 1), (outer, -1)):
            c = Y.block(f'{o.name}_cut', (1.2, 1.4, 1.6), (1.27 + side * 0.6, 0.0, 0.4), coll(), [SLUICE], bev=0.0,
                        rot=(0, math.radians(-14), 0))
            Q.boolean(o, c)
            Q.apply_mods(o)
        pivot = Vector((1.5, 0.0, 0.12))
        tip = Matrix.Translation(pivot + Vector((0.14, 0.0, -0.05))) @ Matrix.Rotation(math.radians(-24), 4, 'Y') @ Matrix.Translation(-pivot)
        outer.matrix_world = tip @ outer.matrix_world
        post = bpy.data.objects['A02_post_1']
        post.matrix_world = Matrix.Translation((0.38, 0.06, -0.12)) @ tip @ Matrix.Rotation(math.radians(-14), 4, 'Y') @ post.matrix_world
        for k in range(7):
            boulder(f'A02_frag_{k}', (rnd.uniform(0.05, 0.12),) * 2 + (0.05,), (1.45 + rnd.uniform(-0.2, 0.6), rnd.uniform(-0.55, 0.45), 0.03),
                    SLUICE, seed=40 + k, subd=1, rough=0.25, cleave=2)
        leak = (1.3, 0.0, 0.33)
    # low water inside (unbaked), the leak stream and a puddle with a dark wet stain on the ground
    xe = 1.34 if variant == 'side_crack' else 1.22
    Y.make_mesh('A02_water', [(-1.34, -0.2, 0.33), (xe, -0.2, 0.33), (xe, 0.2, 0.33), (-1.34, 0.2, 0.33)], [(0, 1, 2, 3)], None, [WATERM],
                coll=coll())
    if variant == 'side_crack':   # a thin stream out of the side crack, curving down to the ground
        pts = [(leak[0], leak[1] - 0.12 * math.sin(t * 1.3), leak[2] * (1 - t) + 0.02) for t in np.linspace(0, 1, 7)]
        pud = (leak[0] + 0.05, -0.75)
    else:                          # a wider sheet over the broken end
        pts = [(leak[0] + 0.28 * math.sin(t * 1.4), 0.0, leak[2] * (1 - t) + 0.02) for t in np.linspace(0, 1, 7)]
        pud = (1.75, 0.0)
    Y.tube('A02_leak', pts, lambda t: 0.018 + 0.016 * t, 6, coll(), [WATERM])
    puddle = boulder('A02_puddle', (0.45, 0.32, 0.02), (pud[0], pud[1], 0.0), MUD, seed=7, subd=3, rough=0.25, ground=0.0)
    puddle.scale.z = 0.6
    for k in range(9):                        # dry grass and silt along the footing
        tuft(f'A02_grass_{k}', rnd.uniform(-1.5, 1.5), rnd.choice((-0.45, 0.45)) + rnd.uniform(-0.06, 0.06), 0.0,
             h=rnd.uniform(0.12, 0.24), n=6, seed=200 + k, droop=0.3)


# ====================================================================== A03 half-buried formation base
def sector(name, r0, r1, a0, a1, z0, z1, mat, n=8, bev=0.015):
    """Annular sector stone (r0..r1, angles a0..a1) from z0 to z1."""
    outline = [(r1 * math.cos(a0 + (a1 - a0) * i / n), r1 * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
    if r0 > 0.01:
        outline += [(r0 * math.cos(a1 - (a1 - a0) * i / n), r0 * math.sin(a1 - (a1 - a0) * i / n)) for i in range(n + 1)]
    else:
        outline.append((0.0, 0.0))
    o = Y.prism(name, outline, z1 - z0, coll(), [mat], plane='XY', offset=(z0 + z1) / 2)
    if bev:
        Q.add_bevel(o, bev, 2)
    return o


def build_A03():
    rnd = random.Random(33)
    R, H = 0.9, 0.45
    gap = (math.radians(20), math.radians(115))           # the broken third of the ring
    for i in range(12):                                   # curb stones
        a0, a1 = i * math.tau / 12 + 0.006, (i + 1) * math.tau / 12 - 0.006
        broken = gap[0] < (a0 + a1) / 2 < gap[1]
        top = H - (rnd.uniform(0.12, 0.26) if broken else rnd.uniform(0.0, 0.02))
        sector(f'A03_curb_{i}', 0.62, R - (0.05 if broken else 0.0), a0, a1, 0.0, top, FSTONE)
    for i in range(6):                                    # top slabs; the carved rings run across them
        a0, a1 = i * math.tau / 6 + 0.004, (i + 1) * math.tau / 6 - 0.004
        broken = gap[0] < (a0 + a1) / 2 < gap[1]
        sector(f'A03_slab_{i}', 0.0, 0.615, a0, a1, 0.0, H - 0.02 - (0.09 if broken else 0.0), FSTONE, n=6)
    # bronze ring with trigram notches, missing over the gap
    arc = np.linspace(gap[1] + 0.05, gap[0] + math.tau - 0.05, 60)
    pts = [(0.76 * math.cos(a), 0.76 * math.sin(a), H + 0.004) for a in arc]
    ring = Y.tube('A03_bronze_ring', pts, 0.035, 4, coll(), [BRONZE], caps=True)
    ring.scale.z = 0.55
    for k, a in enumerate(np.linspace(gap[1] + 0.35, gap[0] + math.tau - 0.35, 8)):   # trigram marks: three bars, some broken
        for j in range(3):
            r = 0.725 + j * 0.035
            Y.block(f'A03_bar_{k}_{j}', (0.012, 0.11 if (k + j) % 3 else 0.045, 0.012), (r * math.cos(a), r * math.sin(a), H + 0.022), coll(),
                    [BRONZE], bev=0.002, rot=(0, 0, a))
    for k, (x, y, a) in enumerate(((0.95, -0.55, 0.4), (1.15, 0.2, 2.1))):            # loose fragments half in the soil
        fr = [(x + 0.18 * math.cos(a + t), y + 0.18 * math.sin(a + t), 0.02) for t in np.linspace(0, 0.9, 8)]
        Y.tube(f'A03_frag_{k}', fr, 0.035, 4, coll(), [BRONZE], caps=True).scale.z = 0.55
    # tilt and sink: the gap side drops into the soil
    axis = Vector((math.cos(1.2), math.sin(1.2), 0)).cross(Vector((0, 0, 1)))
    tilt = Matrix.Translation((0, 0, -0.1)) @ Matrix.Rotation(math.radians(9), 4, axis)
    for o in [o for o in coll().objects if o.name.startswith(('A03_curb', 'A03_slab', 'A03_bronze', 'A03_bar'))]:
        o.matrix_world = tilt @ o.matrix_world
    # soil heaped over the sunk side, rubble in the gap, dry grass
    for k in range(4):
        a = 1.2 + rnd.uniform(-0.6, 0.6)
        r = rnd.uniform(0.85, 1.05)
        boulder(f'A03_soil_{k}', (rnd.uniform(0.35, 0.5), rnd.uniform(0.25, 0.35), rnd.uniform(0.12, 0.2)), (r * math.cos(a), r * math.sin(a), 0.0),
                SOILM, seed=330 + k, subd=3, rough=0.3, rot=a)
    for k in range(6):
        a = rnd.uniform(*gap)
        boulder(f'A03_rubble_{k}', (rnd.uniform(0.06, 0.12),) * 2 + (0.06,), (0.8 * math.cos(a), 0.8 * math.sin(a), 0.18), FSTONE,
                seed=340 + k, subd=1, rough=0.3, cleave=3, ground=0.0)
    for k in range(16):
        a = rnd.uniform(0, math.tau)
        r = rnd.uniform(0.9, 1.15)
        tuft(f'A03_grass_{k}', r * math.cos(a), r * math.sin(a), 0.0, h=rnd.uniform(0.18, 0.32), n=9, seed=350 + k, droop=0.35)


# ====================================================================== A04 silt bar (blocking / cleared)
def m_silt(name='Silt'):
    m, nt, b = Q.new_mat(name)
    co = Q.coords(nt, (1, 1, 1), offset_by_seed=False)
    wz = Q.attr(nt, 'qa_wz', 'fac')
    n1 = Q.noise(nt, co, 3.0, 5, 0.6)
    col = Q.mix(nt, Q.smooth(nt, n1, 0.3, 0.75), (0.08, 0.066, 0.048), (0.16, 0.135, 0.10))
    peb = Q.smooth(nt, Q.voronoi(nt, co, 34.0), 0.0, 0.25)
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', Q.math_(nt, 'SUBTRACT', 1.0, peb), 0.55), col, (0.05, 0.048, 0.044))
    leaf = Q.smooth(nt, Q.noise(nt, co, 6.0, 3), 0.62, 0.7)
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', leaf, 0.8), col, Q.mix(nt, Q.noise(nt, co, 40.0, 2), (0.12, 0.06, 0.02), (0.22, 0.13, 0.05)))
    wet = Q.math_(nt, 'SUBTRACT', 1.0, Q.smooth(nt, wz, 0.06, 0.18))
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', wet, 0.75), col, (0.03, 0.026, 0.02))
    ripple = Q.N(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='Y')
    Q.L(nt, co, ripple.inputs['Vector'])
    ripple.inputs['Scale'].default_value = 7.0
    ripple.inputs['Distortion'].default_value = 4.0
    hgt = Q.math_(nt, 'ADD', Q.math_(nt, 'MULTIPLY', ripple.outputs['Fac'], 0.35), Q.math_(nt, 'MULTIPLY', Q.math_(nt, 'SUBTRACT', 1.0, peb), 0.6))
    return Q.finish(m, nt, b, col, Q.mixf(nt, wet, 0.9, 0.4), 0.0, hgt, 0.006, 1.0)


def mound_h(x, y, height=0.6, rx=1.25, ry=1.1, gap_x=0.75):
    return height * max(0.0, 1 - (x / rx) ** 2 - (y / ry) ** 2) ** 0.55 * (1 - 0.85 * smoothstep(gap_x - 0.15, gap_x + 0.25, x))


def silt_mound(name, height, rx, ry, gap_x=0.75, n=36, seed=4):
    """Polar heightfield mound on z=0 (it sits on the channel bed): an irregular, smooth outline; lower towards +x
    where the trickle gets past."""
    off = Vector((seed * 2.1, seed * 0.7, 0))
    na, nr = n * 2, n // 2
    verts, faces = [(0.0, 0.0, mound_h(0, 0, height, rx, ry, gap_x))], []
    for j in range(1, nr + 1):
        t = j / nr
        for i in range(na):
            a = math.tau * i / na
            wob = 1 + 0.12 * noise.noise(Vector((math.cos(a), math.sin(a), 0)) * 1.7 + off)   # wavy outline
            x, y = rx * t * wob * math.cos(a), ry * t * wob * math.sin(a)
            h = mound_h(x / wob, y / wob, height, rx, ry, gap_x) if j < nr else 0.0
            h *= 1 + 0.3 * noise.fractal(Vector((x, y, 0)) * 2.2 + off, 0.6, 2.0, 5)
            h += 0.02 * math.sin(y * 9 + x * 2) * min(1.0, h * 6)
            verts.append((x, y, max(0.0, h)))
    for i in range(na):
        faces.append((0, 1 + i, 1 + (i + 1) % na))
    for j in range(nr - 1):
        r0, r1 = 1 + j * na, 1 + (j + 1) * na
        for i in range(na):
            i2 = (i + 1) % na
            faces.append((r0 + i, r1 + i, r1 + i2, r0 + i2))
    o = Y.make_mesh(name, verts, faces, None, [SILT], coll=coll(), smooth_angle=70)
    Y.recalc_normals(o)
    return o


def build_A04(cleared=False):
    rnd = random.Random(44)
    if not cleared:
        silt_mound('A04_silt', 0.6, 1.25, 1.1)
        Y.tube('A04_branch', [(-1.1, 0.35, 0.42), (-0.4, 0.25, 0.55), (0.3, 0.05, 0.5), (0.9, -0.2, 0.26)], lambda t: 0.05 * (1 - 0.5 * t), 8,
               coll(), [ROOTWOOD], caps=True)
        for k in range(18):           # twigs caught in the silt
            a = rnd.uniform(0, math.pi)
            x, y = rnd.uniform(-0.9, 0.6), rnd.uniform(-0.6, 0.7)
            z = mound_h(x, y)
            L = rnd.uniform(0.25, 0.6)
            Y.tube(f'A04_twig_{k}', [(x - math.cos(a) * L / 2, y - math.sin(a) * L / 2, z), (x, y, z + 0.04),
                                     (x + math.cos(a) * L / 2, y + math.sin(a) * L / 2, z - 0.02)], rnd.uniform(0.008, 0.016), 5, coll(), [ROOTWOOD],
                   caps=True)
        for k in range(44):
            x, y = rnd.uniform(-1.15, 0.85), rnd.uniform(-1.0, 1.0)
            r = rnd.uniform(0.04, 0.13)
            boulder(f'A04_peb_{k}', (r, r * 0.8, r * 0.55), (x, y, max(0.0, mound_h(x, y) - r * 0.3)), PEBBLE, seed=440 + k, subd=1, rough=0.15, ground=0.0)
        # water pooled upstream (+Y) and the trickle past the low side
        pond = [(1.05 * math.cos(a) * (1 + 0.08 * math.sin(3 * a)), 1.15 + 0.62 * math.sin(a), 0.36) for a in np.linspace(0, math.tau, 28, endpoint=False)]
        Y.make_mesh('A04_pond', pond, [tuple(range(len(pond)))], None, [WATERM], coll=coll())   # rounded pool behind the bar
        Y.tube('A04_trickle', [(0.98, 0.9, 0.3), (1.0, 0.2, 0.17), (0.96, -0.5, 0.1), (0.9, -1.2, 0.06)], lambda t: 0.06 - 0.02 * t, 6, coll(), [WATERM],
               caps=False).scale.z = 0.35
    else:
        for k, sx in enumerate((-1, 1)):   # silt raked to the edges, low remnants
            o = silt_mound(f'A04_remnant_{k}', 0.1, 0.35, 1.0, gap_x=9, n=16, seed=8 + k)
            o.location = (sx * 1.05, 0.0, 0.0)
        for k in range(8):
            x = rnd.choice((-1, 1)) * rnd.uniform(1.0, 1.25)
            y = rnd.uniform(-0.9, 0.9)
            a = rnd.uniform(0, math.pi)
            Y.tube(f'A04_twig_{k}', [(x - math.cos(a) * 0.2, y - math.sin(a) * 0.2, 0.06), (x + math.cos(a) * 0.2, y + math.sin(a) * 0.2, 0.05)],
                   0.012, 5, coll(), [ROOTWOOD], caps=True)
        for k in range(10):
            x, y = rnd.uniform(-0.8, 0.8), rnd.uniform(-1.0, 1.0)
            r = rnd.uniform(0.05, 0.1)
            boulder(f'A04_peb_{k}', (r, r * 0.8, r * 0.5), (x, y, 0.0), PEBBLE, seed=460 + k, subd=1, rough=0.15, ground=0.0)
        Y.make_mesh('A04_flow', [(-0.9, -1.1, 0.1), (0.9, -1.1, 0.1), (0.9, 1.1, 0.1), (-0.9, 1.1, 0.1)], [(0, 1, 2, 3)], None, [WATERM], coll=coll())


def build_A04_cleared():
    build_A04(cleared=True)


# ====================================================================== A05 withered sedge clump
def m_crackmud(name='CrackedMud'):
    m, nt, b = Q.new_mat(name)
    co = Q.coords(nt, (1, 1, 1))
    cr = Q.smooth(nt, Q.voronoi(nt, co, 9.0, 'DISTANCE_TO_EDGE'), 0.0, 0.025)
    col = Q.mix(nt, Q.smooth(nt, Q.noise(nt, co, 4.0, 4), 0.3, 0.7), (0.12, 0.095, 0.065), (0.21, 0.17, 0.12))
    col = Q.mix(nt, Q.math_(nt, 'SUBTRACT', 1.0, cr), col, (0.03, 0.022, 0.015))
    return Q.finish(m, nt, b, col, 0.93, 0.0, cr, 0.01, 1.0)


def sedge(name, n, seed, h=(0.45, 0.85)):
    """Ribbon leaves: green base, ochre to brown tips, the upper half folding over; some tips broken off."""
    rnd = random.Random(seed)
    verts, faces, cols = [], [], []
    for i in range(n):
        a = rnd.uniform(0, math.tau)
        L = rnd.uniform(*h)
        wid = rnd.uniform(0.018, 0.034)
        out = rnd.uniform(0.3, 1.0)
        fold = rnd.uniform(0.3, 0.6)
        segs = 7 if rnd.random() > 0.25 else 5           # a quarter of the tips are broken off
        d = Vector((math.cos(a), math.sin(a), 0))
        side = Vector((-d.y, d.x, 0))
        twist = rnd.uniform(-0.6, 0.6)
        p = d * rnd.uniform(0.0, 0.08)
        dirv = (d * out + Vector((0, 0, 1))).normalized()
        tip_c = rnd.choice(((0.30, 0.20, 0.07), (0.38, 0.27, 0.10), (0.24, 0.15, 0.06)))
        prev = None
        for sgi in range(segs + 1):
            t = sgi / 7
            if t > fold:          # past the fold the leaf droops down and outwards
                dirv = (dirv + Vector((0, 0, -0.42)) + d * 0.12).normalized()
            ww = wid * (1 - 0.85 * t ** 1.6)
            sv = (side * math.cos(twist * t) + Vector((0, 0, 0.3)) * math.sin(twist * t)).normalized() * ww
            g = min(1.0, t * 2.2)
            c = tuple((0.05, 0.075, 0.025)[j] * (1 - g) + (0.30, 0.24, 0.10)[j] * g * (1 - t) + tip_c[j] * t for j in range(3))
            k = len(verts)
            verts += [tuple(p - sv), tuple(p + sv)]
            cols += [c, c]
            if prev is not None:
                faces.append((prev, prev + 1, k + 1, k))
            prev = k
            p = p + dirv * (L / 7)
    o = Y.make_mesh(name, verts, faces, None, [GRASSVC], coll=coll())
    ca = o.data.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
    for i, c in enumerate(cols):
        ca.data[i].color = (*c, 1.0)
    return o


def build_A05():
    rnd = random.Random(55)
    boulder('A05_mud', (0.5, 0.42, 0.06), (0.0, 0.0, 0.0), CRACKMUD, seed=5, subd=4, rough=0.25, ground=0.0)
    sedge('A05_leaves', 110, 505)
    for k in range(10):           # dry runners and roots over the cracked mud
        a = rnd.uniform(0, math.tau)
        pts = [(math.cos(a) * r, math.sin(a) * r, 0.045 - 0.02 * r) for r in np.linspace(0.06, rnd.uniform(0.3, 0.48), 6)]
        Y.tube(f'A05_root_{k}', pts, lambda t: 0.007 * (1 - 0.6 * t), 4, coll(), [ROOTWOOD], caps=False)


# ====================================================================== A06 wet mossy marker stone
def build_A06():
    rnd = random.Random(66)
    boulder('A06_stone', (0.5, 0.42, 0.62), (0.0, 0.0, 0.58), MARKER, seed=6, subd=5, rough=0.14, box=2.25, cleave=4, squash_top=0.08)
    for k in range(9):
        a = rnd.uniform(0, math.tau)
        r = rnd.uniform(0.55, 0.85)
        rr = rnd.uniform(0.05, 0.13)
        boulder(f'A06_peb_{k}', (rr, rr * 0.85, rr * 0.6), (r * math.cos(a), r * math.sin(a), 0.0), PEBBLE, seed=600 + k, subd=2, rough=0.18, ground=0.0)
    for k in range(6):
        a = rnd.uniform(0, math.tau)
        tuft(f'A06_grass_{k}', 0.55 * math.cos(a), 0.5 * math.sin(a), 0.0, h=rnd.uniform(0.2, 0.34), n=8, seed=610 + k, droop=0.3)


# ====================================================================== pipeline
def ref(name):
    return f'{name}_three_view.png'


ASSETS = {
    'A01_straight_01': dict(build=lambda: build_river('straight'), ref=ref('A01_straight'), res=2048, budget=20000, double=True,
                            family='A01', variant='straight', collision=dict(type='heightfield', note='banks and channel walkable; datum: bank top 1.15 m above origin')),
    'A01_bend_left_01': dict(build=lambda: build_river('bend_left'), ref=ref('A01_bend_left'), res=2048, budget=20000, double=True,
                             family='A01', variant='bend_left 25 deg', collision=dict(type='heightfield', note='inner gravel bar is the easy way down to the water')),
    'A01_bend_right_01': dict(build=lambda: build_river('bend_right'), ref=ref('A01_bend_right'), res=2048, budget=21000,   # strata ledges are individual slabs
                              double=True,
                              family='A01', variant='bend_right 40 deg', collision=dict(type='heightfield', note='outer cliff (left bank) 1.7 m: not climbable; walk the inner bar')),
    'A01_narrow_01': dict(build=lambda: build_river('narrow'), ref=ref('A01_narrow'), res=2048, budget=20000, double=True,
                          family='A01', variant='narrowing pinch', collision=dict(type='heightfield', note='pinch rocks are blockers; the sill can be stepped over')),
    'A01_end_source_01': dict(build=lambda: build_river('end_source'), ref=ref('A01_end_source'), res=2048, budget=22000, double=True,   # budget: twelve jam boulders
                              family='A01', variant='terminal: spring and boulder jam (closes a run upstream)',
                              collision=dict(type='heightfield', note='interface only at the downstream end; the boulder jam is a blocker')),
    'A02_side_crack_01': dict(build=lambda: build_A02('side_crack'), ref=ref('A02_side_crack'), res=1024, budget=9000, double=True,
                              family='A02', variant='side crack', collision=dict(type='box', size=[3.0, 0.8, 0.67], center=[0, 0, 0.335], note='clue cracked_sluice: look at the -Y face')),
    'A02_end_break_01': dict(build=lambda: build_A02('end_break'), ref=ref('A02_end_break'), res=1024, budget=9000, double=True,
                             family='A02', variant='broken end joint', collision=dict(type='box', size=[3.0, 0.8, 0.67], center=[0, 0, 0.335], note='clue cracked_sluice: the tipped end at +X')),
    'A03_FormationBase': dict(build=build_A03, ref=ref('A03'), res=1024, budget=9000, double=True, family='A03', variant='single',
                              collision=dict(type='cylinder', radius=0.9, height=0.45, center=[0, 0, 0.22], note='tilted 9 deg, sunk 0.1 m on the gap side; step-on not intended')),
    'A04_SiltBar': dict(build=build_A04, ref=ref('A04'), res=1024, budget=9000, double=True, family='A04', variant='mound 01 (blocking)',
                        collision=dict(type='mesh', note='place on the channel bed (origin z = bed); clue silt_buildup; pond water is part of the Clear node')),
    'A04_SiltBar_cleared': dict(build=build_A04_cleared, ref=ref('A04'), res=1024, budget=4000, double=True, family='A04', variant='cleared state',
                                collision=dict(type='none', note='walkable remnant; swap in when the silt is cleared')),
    'A05_WitheredSedge_01': dict(build=build_A05, ref=ref('A05'), res=512, budget=3500, double=True, family='A05', variant='clump 01',
                                 collision=dict(type='none', note='non-blocking plant; vertex-coloured leaves in the Clear node')),
    'A06_MarkerStone': dict(build=build_A06, ref=ref('A06'), res=1024, budget=7000, double=True, family='A06', variant='single',
                            collision=dict(type='capsule', radius=0.45, height=1.2, center=[0, 0, 0.6], note='water lines at 0.35 m (today) and 0.86 m (old)')),
}


def build_asset(aid):
    t0 = time.time()
    a = ASSETS[aid]
    key = aid
    assert (REF / a['ref']).is_file(), f'{aid}: save and review the AI three-view before modelling'
    Q.reset()
    random.seed(29)
    src = Q.coll('10_Procedural_Source')
    Q.ACTIVE['coll'] = src
    make_materials()
    course = a['build']()
    parts = [o for o in src.objects if o.type == 'MESH' and not o.get('qa_cutter')]
    bpy.context.view_layer.update()
    for o in parts:   # anything that dips below the base is pressed onto it
        mw, inv = o.matrix_world, o.matrix_world.inverted()
        for v in o.data.vertices:
            w = mw @ v.co
            if w.z < 0.0:
                w.z = 0.0
                v.co = inv @ w
    Q.finalize_parts(parts, seed=sum(map(ord, aid)))
    for o in parts:   # world height per vertex, for materials that must line up across parts (carved band, silt)
        me, mw = o.data, o.matrix_world
        at = me.attributes.get('qa_wz') or me.attributes.new('qa_wz', 'FLOAT', 'POINT')
        at.data.foreach_set('value', [(mw @ v.co).z for v in me.vertices])
    bpy.context.view_layer.update()
    game = Q.coll('00_Game_Export')
    Q.ACTIVE['coll'] = game
    G, K = Q.game_mesh(key, parts, game)
    tdir = EXPORT / 'textures'
    imgs, alpha = Q.bake_asset(G, key, tdir, a['res'])
    gm = Q.game_material(key, imgs, alpha)
    gm.use_backface_culling = not a['double']
    G.data.materials.clear()
    G.data.materials.append(gm)
    G.name = f'{key}_LOD0'
    lods = Q.make_lods(G, gcoll=game)
    for l, nm in zip(lods, ('LOD1', 'LOD2')):
        l.name = f'{key}_{nm}'
    nodes = Q.split_nodes(G, key)
    if K:
        K.name = f'{key}_Clear'   # unbaked: translucent water + vertex-coloured grass clumps
        nodes.append(K)
    src.hide_render = True
    src.hide_viewport = True
    for l in lods:
        l.hide_render = True
    glb, fbx = EXPORT / f'{key}.glb', EXPORT / f'{key}.fbx'
    Q.export(nodes, glb, fbx, nodes + lods)
    Q.select_only(nodes, nodes[0])
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format='GLB', use_selection=True, export_apply=True,
                              export_yup=True, export_image_format='WEBP', export_image_quality=88,
                              export_materials='EXPORT', export_extras=False)
    for l in lods:
        l.hide_set(True)
    blend = ROOT / 'blend' / f'{key}.blend'
    blend.parent.mkdir(exist_ok=True)
    for img in bpy.data.images:
        if img.filepath_raw and img.filepath_raw.startswith(str(tdir)):
            img.filepath = img.filepath_raw
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), compress=True, relative_remap=True)
    bpy.ops.file.make_paths_relative()
    bpy.ops.wm.save_mainfile(compress=True)
    solid = [o for o in nodes if o is not K]
    mn, mx = Q.bbox(nodes)
    dims = [round(mx[i] - mn[i], 4) for i in range(3)]
    tris = [sum(Q.tri_count(o) for o in nodes)] + [Q.tri_count(o) for o in lods]
    hs = [Q.mesh_health(o) for o in solid]
    health = {k: sum(h[k] for h in hs) for k in hs[0]}
    rt_tris, rmn, rmx, rmats = Q.glb_roundtrip(glb)
    v = {
        'asset': aid, 'dimensions_m': dims, 'bbox_min': [round(x, 4) for x in mn], 'bbox_max': [round(x, 4) for x in mx],
        'trianglesLOD': tris, 'budgetLOD0': a['budget'], 'withinBudget': tris[0] <= a['budget'],
        'materials': sorted({m.name for o in nodes for m in o.data.materials if m}), 'textureResolution': a['res'],
        'nodes': [o.name for o in nodes], 'originAtBase': abs(mn[2]) < 0.003, 'meshHealth': health,
        'glbRoundTrip': {'triangles': rt_tris, 'trianglesMatch': rt_tris == tris[0],
                         'bboxMatch': all(abs(p - q) < 0.002 for p, q in zip(rmn + rmx, mn + mx)), 'materials': rmats},
        'files': {p.name: {'bytes': p.stat().st_size, 'sha256': Q.sha(p)} for p in (glb, fbx)},
        'reference': f"art/references/qingxi-waterhead-a/{a['ref']}",
        'notChecked': ['Unity import', 'in-game lighting', 'mobile performance', 'LOD screen-size thresholds'],
    }
    info = dict(id=a['family'], variant=a['variant'], key=key, units='metre', forward='-Y (Blender) / +Z (glTF)', origin='base centre',
                dimensions_m=dims, triangles=tris[0], lod_triangles=tris, collision=a['collision'],
                author='Johnnnny0823', validation=v)
    if isinstance(course, Course):
        info['river_interface'] = dict(
            origin='downstream port: channel centre at the tile base; upstream is +Y (Blender) / -Z (glTF)',
            channel_width_m=2 * HALF_W, tile_width_m=2 * TILE_HW, bank_top_m=TOP, bed_m=BED, water_m=WATER, old_high_water_m=OLD_HI,
            length_m=course.L, out_port_blender_xy_deg=None if course.closed else course.out_port(), terminal=course.closed,
            place='set the origin at y = -bank_top so banks meet ground 0; chain the next module at out_port')
    (EXPORT / f'{key}_model_info.json').write_text(json.dumps(info, indent=1, ensure_ascii=False), encoding='utf-8')
    print(f'[{key}] tris {tris} dims {dims} health {health} roundtrip {rt_tris} {time.time() - t0:.0f}s', flush=True)
    if RENDER:
        previews(key, nodes)
    return v


def previews(key, nodes):
    out = PREV / key
    Q.gpu(bpy.context.scene, 48)
    Q.studio('stylized')
    Q.camera_fit(nodes, 35, 24)
    Q.render(out / 'three_quarter.png', 1024, 64)
    Q.camera_fit(nodes, 0, 14, margin=0.8)
    Q.render(out / 'close_front.png', 1024, 64)
    Q.camera_fit(nodes, 90, 16, margin=0.8)
    Q.render(out / 'close_side.png', 1024, 64)
    if '--quick' in ARGV:
        return
    mn, mx = Q.bbox(nodes)
    fig_m = Q.m_simple('ScaleFigure', (0.20, 0.27, 0.24), (0.22, 0.29, 0.26), rough=0.8)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.24, radius2=0.2, depth=1.45)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, 0.725))
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=0.13, matrix=Matrix.Translation((0, 0, 1.57)))
    fig = Q._obj('QA_ScaleFigure', bm, fig_m)
    fig.location = (mx[0] + 0.55, (mn[1] + mx[1]) / 2, 0)
    if key.startswith('A01'):
        fig.location = (2.6, 1.5, TOP)   # standing on the right bank
    Q.camera_fit(nodes + [fig], 25, 14)
    Q.render(out / 'scale_1p7m.png', 1024, 48)
    bpy.data.objects.remove(fig)
    Q.camera_fit(nodes, 180, 18)
    Q.render(out / 'back.png', 768, 48)
    wm, nt, b = Q.new_mat('QA_Wire')
    w = Q.N(nt, 'ShaderNodeWireframe', use_pixel_size=True)
    w.inputs['Size'].default_value = 1.0
    Q.L(nt, Q.mix(nt, w.outputs['Fac'], (0.72, 0.72, 0.70), (0.05, 0.05, 0.06)), b.inputs['Base Color'])
    keep = [list(o.data.materials) for o in nodes]
    for o in nodes:
        for i in range(len(o.data.materials)):
            o.data.materials[i] = wm
    Q.camera_fit(nodes, 35, 24)
    Q.render(out / 'wireframe.png', 1024, 24)
    for o, ms in zip(nodes, keep):
        for i, m in enumerate(ms):
            o.data.materials[i] = m
    s = bpy.context.scene
    g = bpy.data.objects.get('QA_Ground')
    if g:
        g.hide_render = True
    s.render.film_transparent = True
    mn, mx = Q.bbox(nodes)
    c = Vector([(mn[i] + mx[i]) / 2 for i in range(3)])
    span = max(mx[i] - mn[i] for i in range(3)) * 1.1
    cam = s.camera
    for view, d in (('front', (0, -1, 0)), ('side', (1, 0, 0)), ('back', (0, 1, 0)), ('top', (0, 0, 1))):
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = span
        cam.location = c + Vector(d) * 30
        cam.rotation_euler = (-Vector(d)).to_track_quat('-Z', 'Y').to_euler()
        Q.render(out / f'ortho_{view}.png', 900, 48)
    s.render.film_transparent = False
    cam.data.type = 'PERSP'


def assemble_master():
    Q.reset()
    for aid in ASSETS:
        blend = ROOT / 'blend' / f'{aid}.blend'
        if not blend.exists():
            continue
        for cname, label in (('10_Procedural_Source', 'source'), ('00_Game_Export', 'game')):
            before = set(bpy.data.collections)
            bpy.ops.wm.append(filepath=str(blend / 'Collection' / cname), directory=str(blend / 'Collection') + '/', filename=cname)
            for c in [c for c in bpy.data.collections if c not in before and c.name.startswith(cname)]:
                c.name = f'{aid}__{label}'
                if label == 'source':
                    c.hide_render = True
                    c.hide_viewport = True
    bpy.context.scene['author'] = 'Johnnnny0823'
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'Qingxi_Waterhead_A.blend'), compress=True, relative_remap=True)
    print('MASTER_SAVED', flush=True)


if '--master' in ARGV:
    assemble_master()
else:
    todo = [a for a in ARGV if not a.startswith('--')] or list(ASSETS)
    report = {aid: build_asset(aid) for aid in todo}
    print('DONE', json.dumps({k: [v['trianglesLOD'], v['glbRoundTrip']['trianglesMatch'], v['withinBudget']] for k, v in report.items()}), flush=True)
