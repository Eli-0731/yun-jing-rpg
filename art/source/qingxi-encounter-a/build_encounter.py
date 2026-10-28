"""Qingxi forest encounter kit (A, 2026-10-29). Run in a background Blender 5.2:

  blender -b --python-exit-code 1 --python build_encounter.py [-- A01 A02 ...] [--no-render] [--quick]
  blender -b --python-exit-code 1 --python build_encounter.py -- --master

Each asset: editable procedural parts built from the saved AI front/side/back views in
art/references/qingxi-encounter-a/, baked to one atlas (BaseColor, ORM, Normal), LOD1/LOD2,
GLB (LOD0, WebP textures) + FBX (LOD0-2), <ID>_model_info.json and review renders.
Original procedural modelling only; no third-party meshes.
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

REF = ROOT.parents[2] / 'art/references/qingxi-encounter-a'
EXPORT, PREV = Q.EXPORTS, Q.PREVIEWS
ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
RENDER = '--no-render' not in ARGV
DATUM = 0.6   # terrain tiles: the walkable "ground level" edge sits 0.6 m above the tile origin


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


def m_grass(name='MeadowTop', lush=1.0):
    """Short meadow from above: two greens, clover clumps, bare soil scuffs, darker hollows."""
    m, nt, b = Q.new_mat(name)
    co = Q.coords(nt, (1, 1, 1))
    n1, n2 = Q.noise(nt, co, 1.6, 5, 0.6), Q.noise(nt, co, 14.0, 4, 0.6)
    col = Q.mix(nt, Q.smooth(nt, n1, 0.3, 0.7), (0.040, 0.062, 0.016), (0.090, 0.115, 0.030))
    blades = Q.smooth(nt, Q.noise(nt, co, 90.0, 2, 0.5), 0.45, 0.7)
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', blades, 0.35), col, (0.13, 0.15, 0.05))
    clover = Q.smooth(nt, Q.voronoi(nt, co, 7.0, 'F1'), 0.12, 0.05)
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', clover, 0.6 * lush), col, (0.05, 0.10, 0.03))
    soil = Q.smooth(nt, Q.noise(nt, co, 0.9, 4, 0.6, 0.5), 0.62, 0.7)
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', soil, 0.85), col, (0.11, 0.075, 0.045))
    cav, edge = Q.edge_cavity(nt, 0.05, 0.006)
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', Q.smooth(nt, cav, 0.1, 0.6), 0.5), col, (0.02, 0.025, 0.01))
    return Q.finish(m, nt, b, col, 0.92, 0.0, Q.math_(nt, 'ADD', n2, blades), 0.003, 0.8)


def m_litter(name='LeafLitter'):
    m, nt, b = Q.new_mat(name)
    co = Q.coords(nt, (1, 1, 1))
    leaf = Q.voronoi(nt, co, 26.0, 'F1', 'Color')
    t = Q.sep(nt, leaf)
    col = Q.mix(nt, t[0], (0.055, 0.032, 0.016), (0.15, 0.085, 0.03))
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', Q.smooth(nt, t[1], 0.6, 0.9), 0.6), col, (0.07, 0.08, 0.025))
    gaps = Q.smooth(nt, Q.voronoi(nt, co, 26.0, 'DISTANCE_TO_EDGE'), 0.0, 0.03)
    col = Q.mix(nt, Q.math_(nt, 'SUBTRACT', 1.0, gaps), col, (0.03, 0.02, 0.012))
    return Q.finish(m, nt, b, col, 0.9, 0.0, gaps, 0.002, 0.7)


def m_soil(name='Soil'):
    return Q.m_simple(name, (0.055, 0.036, 0.022), (0.10, 0.068, 0.04), rough=0.95, nscale=18.0, bump=0.002,
                      cav_col=(0.02, 0.013, 0.008))


def make_materials():
    g = {}
    g['GRASS'] = m_grass()
    g['LITTER'] = m_litter()
    g['SOIL'] = m_soil()
    g['SIDE'] = add_moss(Q.m_stone('CutStone', light=(0.17, 0.15, 0.12), dark=(0.07, 0.062, 0.052), scale=1.3, chisel=1.5), 0.6, (0.3, 0.8))
    g['ROCK'] = add_moss(Q.m_stone('MossGranite', light=(0.13, 0.126, 0.115), dark=(0.055, 0.054, 0.05), scale=1.1, speck=1.5, chisel=1.6), 1.0, (0.05, 0.5))
    g['STRATA_G'] = add_moss(Q.m_stone('StrataGrey', light=(0.22, 0.20, 0.165), dark=(0.10, 0.092, 0.078), scale=1.4, chisel=2.5), 0.5, (0.55, 0.9))
    g['STRATA_O'] = add_moss(Q.m_stone('StrataOchre', light=(0.32, 0.20, 0.08), dark=(0.15, 0.095, 0.045), scale=1.4, chisel=2.5), 0.4, (0.55, 0.9))
    g['BARK'] = add_moss(Q.m_bark('OldBark'), 0.9, (0.3, 0.75))
    g['DEADWOOD'] = add_moss(Q.m_wood('Deadwood', (0.10, 0.085, 0.065), (0.22, 0.19, 0.15), axis='X', ring=2.0, wear=0.3, rough=0.85), 0.6)
    g['ENDGRAIN'] = Q.m_endgrain('StumpTop', (0.20, 0.15, 0.10), (0.33, 0.26, 0.18))
    g['FUNGUS'] = Q.m_simple('ShelfFungus', (0.20, 0.13, 0.07), (0.42, 0.33, 0.20), rough=0.7, nscale=20.0,
                             edge_col=(0.55, 0.47, 0.34))
    g['FERN'] = Q.m_simple('Fern', (0.03, 0.07, 0.015), (0.08, 0.15, 0.03), rough=0.7, nscale=6.0, edge_col=(0.12, 0.2, 0.05))
    g['BLADE'] = Q.m_simple('GrassBlade', (0.05, 0.08, 0.02), (0.12, 0.15, 0.045), rough=0.85, nscale=12.0)
    g['HOLE'] = Q.m_simple('BurrowDark', (0.012, 0.009, 0.006), (0.03, 0.02, 0.012), rough=1.0)
    globals().update(g)


# ====================================================================== shape helpers
def coll():
    return Q.ACTIVE['coll']


def boulder(name, radii, loc, mat, seed=1, subd=4, rough=0.16, rot=0.0, squash_top=0.0, cleave=3, box=2.0):
    """Noise-displaced rounded stone; anything below ground is flattened onto it (seated, not floating)."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subd, radius=1.0)
    off = Vector((seed * 1.37, seed * 2.11, seed * 0.73))
    for v in bm.verts:
        d = v.co.normalized()
        if box != 2.0:   # superellipsoid: higher exponent -> rounded box (stone slabs)
            d = d / (abs(d.x) ** box + abs(d.y) ** box + abs(d.z) ** box) ** (1 / box)
        k = 1 + rough * noise.fractal(d * 1.4 + off, 0.55, 2.0, 5) + 0.05 * noise.noise(d * 6 + off)
        p = Vector((d.x * radii[0] * k, d.y * radii[1] * k, d.z * radii[2] * k))
        if squash_top and p.z > 0:
            p.z *= 1 - squash_top
        for ci in range(cleave):   # flat fracture faces
            nrm = Vector((math.sin(seed * 3.1 + ci * 2.4), math.cos(seed * 1.7 + ci * 1.3), 0.6 * math.sin(seed + ci))).normalized()
            lim = 0.78 * (radii[0] * abs(nrm.x) + radii[1] * abs(nrm.y) + radii[2] * abs(nrm.z))
            dd = p.dot(nrm)
            if dd > lim:
                p -= nrm * (dd - lim) * 0.85
        c, s = math.cos(rot), math.sin(rot)
        p = Vector((p.x * c - p.y * s, p.x * s + p.y * c, p.z))
        p.z = max(p.z, -loc[2])
        v.co = p
    o = Q._obj(name, bm, mat, sharp=60)
    o.location = loc
    return o


def tuft(name, x, y, z, h=0.22, n=6, seed=0, mat=None):
    """A few solid grass blades (no alpha cards): both windings so they read from any side."""
    rnd = random.Random(seed)
    verts, faces = [], []
    for i in range(n):
        a = rnd.uniform(0, math.tau)
        w = rnd.uniform(0.012, 0.022)
        hh = h * rnd.uniform(0.6, 1.15)
        lean = rnd.uniform(0.15, 0.45)
        bx, by = math.cos(a) * 0.03, math.sin(a) * 0.03
        tx, ty = bx + math.cos(a) * hh * lean, by + math.sin(a) * hh * lean
        px, py = -math.sin(a) * w, math.cos(a) * w
        k = len(verts)
        verts += [(bx - px, by - py, 0), (bx + px, by + py, 0), (tx, ty, hh)]
        faces += [(k, k + 1, k + 2), (k, k + 2, k + 1)]
    o = Y.make_mesh(name, verts, faces, None, [mat or BLADE], coll=coll())
    o.location = (x, y, z)
    return o


def fern(name, x, y, z, size=0.5, fronds=6, seed=0):
    """Low-poly fern clump: curved spines with paired leaflets."""
    rnd = random.Random(seed)
    verts, faces = [], []
    for f in range(fronds):
        a = f / fronds * math.tau + rnd.uniform(-0.3, 0.3)
        L = size * rnd.uniform(0.75, 1.15)
        d = Vector((math.cos(a), math.sin(a), 0))
        side = Vector((-d.y, d.x, 0))
        steps = 12
        for i in range(steps):
            t0, t1 = i / steps, (i + 1) / steps
            p0 = d * L * t0 + Vector((0, 0, L * 0.55 * math.sin(math.pi * t0 * 0.75)))
            p1 = d * L * t1 + Vector((0, 0, L * 0.55 * math.sin(math.pi * t1 * 0.75)))
            wid = L * 0.13 * math.sin(math.pi * min(1.0, 0.25 + t0)) + 0.008
            for sgn in (-1, 1):
                tip = p0 * 0.35 + p1 * 0.65 + side * sgn * wid + d * wid * 0.5 - Vector((0, 0, wid * 0.35))
                k = len(verts)
                verts += [tuple(p0), tuple(p0 * 0.5 + p1 * 0.5), tuple(tip)]
                faces += [(k, k + 1, k + 2), (k, k + 2, k + 1)]
    o = Y.make_mesh(name, verts, faces, None, [FERN], coll=coll())
    o.location = (x, y, z)
    return o


def terrain_tile(name, sx, sy, height, top_mat_of=None, nx=48, ny=48, rocks=10, seed=1):
    """Top grid (height(x,y) -> z) + four stony skirts down to z=0 + base. top_mat_of(x,y,z) -> 0 grass / 1 litter / 2 soil."""
    hx, hy = sx / 2, sy / 2
    verts, faces, fmat = [], [], []
    for j in range(ny + 1):
        for i in range(nx + 1):
            x, y = -hx + sx * i / nx, -hy + sy * j / ny
            verts.append((x, y, height(x, y)))
    w = nx + 1
    for j in range(ny):
        for i in range(nx):
            a = j * w + i
            faces.append((a, a + 1, a + w + 1, a + w))
            cx = sum(verts[k][0] for k in faces[-1]) / 4
            cy = sum(verts[k][1] for k in faces[-1]) / 4
            cz = sum(verts[k][2] for k in faces[-1]) / 4
            fmat.append(top_mat_of(cx, cy, cz) if top_mat_of else 0)
    # skirt: walk the border, drop rows to the base with a little strata bulge
    border = [j * 0 + i for i in range(nx + 1)] + [j * w + nx for j in range(1, ny + 1)] + \
             [ny * w + i for i in range(nx - 1, -1, -1)] + [j * w for j in range(ny - 1, 0, -1)]
    rows = 6
    ring_start = []
    rnd = random.Random(seed)
    for r in range(1, rows + 1):
        ring_start.append(len(verts))
        f = r / rows
        for bi in border:
            x, y, z = verts[bi]
            out = Vector((x / hx if abs(abs(x) - hx) < 1e-6 else 0, y / hy if abs(abs(y) - hy) < 1e-6 else 0, 0))
            out = out.normalized() if out.length else out
            bulge = 0.035 * math.sin(f * 17 + x * 3 + y * 2.3) + 0.02 * noise.noise(Vector((x, y, f * 4)) * 2.2)
            verts.append((x + out.x * bulge * (r < rows), y + out.y * bulge * (r < rows), z * (1 - f)))
    prev = border
    for r in range(rows):
        cur = list(range(ring_start[r], ring_start[r] + len(border)))
        for k in range(len(border)):
            a, b = prev[k], prev[(k + 1) % len(border)]
            c, d = cur[(k + 1) % len(border)], cur[k]
            faces.append((a, d, c, b))
            fmat.append(3)
        prev = cur
    # bottom cap
    faces.append(tuple(prev[::-1]) if False else tuple(prev))
    fmat.append(3)
    o = Y.make_mesh(name + '_body', verts, faces, None, [GRASS, LITTER, SOIL, SIDE], fmat, coll(), smooth_angle=50)
    Y.recalc_normals(o)
    # embedded stones peeking out of the cut sides
    for k in range(rocks):
        edge = rnd.randrange(4)
        t = rnd.uniform(-0.85, 0.85)
        x, y = [(t * hx, -hy), (hx, t * hy), (t * hx, hy), (-hx, t * hy)][edge]
        z = rnd.uniform(0.12, height(x, y) * 0.6)
        r = rnd.uniform(0.16, 0.32)
        inward = Vector((0 if edge in (0, 2) else (-1 if edge == 1 else 1), (1 if edge == 0 else -1) if edge in (0, 2) else 0, 0))
        boulder(f'{name}_siderock_{k}', (r, r * 0.9, r * 0.75), (x + inward.x * r * 0.45, y + inward.y * r * 0.45, z), ROCK,
                seed=seed * 31 + k, subd=3, rough=0.25)
    return o


def smoothstep(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def edge_fade(x, y, hx, hy, m=0.5):
    """1 inside, 0 on the tile border: keeps borders flat so neighbouring tiles meet without seams."""
    return smoothstep(0, m, hx - abs(x)) * smoothstep(0, m, hy - abs(y))


def scatter(height, hx, hy, n, seed, avoid=None, ferns=0, name='tuft'):
    rnd = random.Random(seed)
    k = 0
    for i in range(n * 5):
        if k >= n:
            break
        x, y = rnd.uniform(-hx + 0.15, hx - 0.15), rnd.uniform(-hy + 0.15, hy - 0.15)
        if avoid and avoid(x, y):
            continue
        tuft(f'{name}_{k}', x, y, max(0.0, height(x, y) - 0.01), h=rnd.uniform(0.14, 0.26), seed=seed + i)
        k += 1
    for i in range(ferns):
        for _ in range(30):
            x, y = rnd.uniform(-hx + 0.3, hx - 0.3), rnd.uniform(-hy + 0.3, hy - 0.3)
            if not avoid or not avoid(x, y):
                break
        fern(f'{name}_fern_{i}', x, y, max(0.0, height(x, y) - 0.02), size=rnd.uniform(0.45, 0.75), fronds=8, seed=seed * 7 + i)


# ====================================================================== A01 slope tile
def build_A01():
    def h(x, y):
        rise = 0.6 * smoothstep(-1.5, 1.5, y)
        return DATUM + rise + 0.035 * noise.noise(Vector((x, y, 0.3)) * 1.3) * edge_fade(x, y, 2, 2)
    def mat_of(x, y, z):
        return 2 if noise.noise(Vector((x * 0.9, y * 0.9, 5.0))) > 0.42 else 0
    terrain_tile('A01', 4.0, 4.0, h, mat_of, 44, 44, rocks=9, seed=1)
    scatter(h, 2.0, 2.0, 85, 11, ferns=4, name='A01_tuft')
    for k, (x, y) in enumerate(((-1.1, 0.9), (0.9, -0.4), (1.4, 1.3))):
        boulder(f'A01_stone_{k}', (0.24, 0.2, 0.14), (x, y, h(x, y) - 0.05), ROCK, seed=40 + k, subd=3)


# ====================================================================== A02 hollow tile (burrow + exit ramp)
def build_A02():
    def h(x, y):
        r = math.hypot(x, y * 1.05)
        d = 0.52 * max(0.0, 1 - (r / 2.25) ** 2) ** 1.1           # bowl
        ch = smoothstep(1.3, 0.45, abs(x)) * smoothstep(-0.5, -2.2, y)   # front exit channel: wide, gentle
        d = max(d, ch * 0.52 * smoothstep(-3.0, -0.6, y) * 0.85)
        rim = 0.07 * smoothstep(1.9, 2.35, r) * smoothstep(2.95, 2.45, r) * (y > -1.2)
        return DATUM - d + rim + 0.02 * noise.noise(Vector((x, y, 1.7)) * 1.6) * edge_fade(x, y, 3, 3)
    def mat_of(x, y, z):
        return 1 if z < DATUM - 0.12 else (2 if abs(x) < 1.0 and y < -1.2 and z < DATUM - 0.02 else 0)
    terrain_tile('A02', 6.0, 6.0, h, mat_of, 60, 60, rocks=14, seed=2)
    # burrow: a dark tunnel mouth in the back inner slope, a lip of dug soil in front of it
    bx, by = 0.0, 1.75
    bz = h(bx, by)
    mouth = Y.lathe('A02_burrow_mouth', [(0.0, -0.40), (0.14, -0.36), (0.24, -0.14), (0.27, 0.0)], 22, coll(), [HOLE],
                    cap_top=False, smooth_angle=60)
    mouth.rotation_euler = (math.radians(-68), 0, 0)
    mouth.location = (bx, by - 0.05, bz + 0.08)
    lip = boulder('A02_burrow_lip', (0.42, 0.22, 0.09), (bx, by - 0.42, h(bx, by - 0.42) - 0.02), SOIL, seed=7, subd=3, rough=0.3)
    arch = Y.tube('A02_burrow_arch', [(bx + 0.33 * math.cos(t), by + 0.02, bz + 0.1 + 0.26 * math.sin(t)) for t in np.linspace(0.1, math.pi - 0.1, 9)],
                  0.07, 8, coll(), [SOIL])
    for k in range(3):
        boulder(f'A02_burrow_stone_{k}', (0.12, 0.1, 0.08), (bx - 0.4 + 0.4 * k, by + 0.12, h(bx - 0.4 + 0.4 * k, by + 0.12) + 0.02), ROCK, seed=80 + k, subd=3)
    for k, ang in enumerate((0.3, 1.2, 2.6, 4.1, 5.2)):   # roots creeping over the rim and into the soil
        r0 = 2.45
        pts = []
        for t in np.linspace(0, 1, 10):
            rr = r0 - 0.7 * t
            x, y = math.cos(ang + 0.25 * t) * rr, math.sin(ang + 0.25 * t) * rr
            pts.append((x, y, h(x, y) + 0.04 * math.sin(math.pi * t) - 0.02 * t))
        Y.tube(f'A02_root_{k}', pts, lambda t: 0.05 * (1 - 0.75 * t), 7, coll(), [BARK])
    avoid = lambda x, y: math.hypot(x, y) < 1.9 or (abs(x) < 1.2 and y < -1.0)
    scatter(h, 3.0, 3.0, 110, 22, avoid=avoid, ferns=12, name='A02_tuft')


# ====================================================================== A03 fallen log
def build_A03():
    rest = boulder('A03_rest_stone', (0.42, 0.34, 0.30), (0.35, 0.0, 0.18), ROCK, seed=3, rough=0.2)
    def axis(t):  # t 0 root end (-x) .. 1 broken top (+x)
        x = -2.42 + 4.82 * t
        z = 0.30 + 0.135 * t + 0.13 * math.sin(math.pi * min(t / 0.6, 1))  # sags onto the rest stone
        return (x, 0.04 * math.sin(t * 5), z)
    pts = [axis(t) for t in np.linspace(0, 1, 26)]
    def rad(t):
        flare = 1 + 0.55 * smoothstep(0.12, 0.0, t)   # the base swells where it tore out of the ground
        return (0.30 - 0.06 * t) * flare * (1 + 0.04 * math.sin(t * 37) + 0.03 * math.sin(t * 91))
    log = Y.tube('A03_trunk', pts, rad, 20, coll(), [BARK], caps=False, smooth_angle=60)
    # root plate: an upturned, roughly round disc of soil and stones standing at the -x end, roots pulled out of it
    plate = boulder('A03_rootplate', (0.36, 0.86, 0.72), (-2.50, 0.0, 0.72), SOIL, seed=5, subd=4, rough=0.14, box=2.3, cleave=0)
    rnd = random.Random(31)
    # roots torn out with the plate: thick, curving out over its rim and hanging down to the soil (no spikes)
    for k in range(11):
        a = k / 11 * math.tau + rnd.uniform(-0.15, 0.15)
        rr = rnd.uniform(0.55, 0.8)
        p0 = Vector((-2.66, math.cos(a) * rr * 0.85, 0.72 + math.sin(a) * rr * 0.7))
        out = Vector((-rnd.uniform(0.18, 0.32), math.cos(a) * rnd.uniform(0.2, 0.35), 0.0))
        pts_r = [p0 + out * f + Vector((0, 0, -0.55 * f * f * (p0.z + 0.1))) for f in np.linspace(0, 1, 7)]
        r0 = rnd.uniform(0.045, 0.085)
        Y.tube(f'A03_root_{k}', [(q.x, q.y, max(q.z, 0.0)) for q in pts_r], lambda t, r0=r0: r0 * (1 - 0.6 * t) + 0.012, 8, coll(), [DEADWOOD])
    for k in range(5):
        boulder(f'A03_plate_stone_{k}', (0.13, 0.11, 0.1), (-2.80, -0.55 + 0.27 * k, 0.45 + 0.5 * ((k * 37) % 3) / 2), ROCK, seed=60 + k, subd=3)
    # broken top: a ragged rim with a few long splinters along the trunk axis, recessed dark core
    end = Vector(pts[-1])
    for k in range(7):
        a = k / 7 * math.tau + rnd.uniform(-0.2, 0.2)
        base = end + Vector((-0.06, math.cos(a) * 0.19, math.sin(a) * 0.19))
        ln = rnd.uniform(0.08, 0.38) if k % 3 else rnd.uniform(0.35, 0.55)
        tip = base + Vector((ln, math.cos(a) * 0.02, math.sin(a) * 0.02))
        Y.tube(f'A03_splinter_{k}', [tuple(base), tuple(base.lerp(tip, 0.5)), tuple(tip)], lambda t: 0.085 * (1 - t) ** 1.3 + 0.004, 5, coll(), [DEADWOOD])
    core = Y.lathe('A03_core', [(0.0, -0.02), (0.22, -0.02), (0.23, 0.0)], 18, coll(), [ENDGRAIN])
    core.rotation_euler = (0, math.radians(90), 0)
    core.location = end - Vector((0.04, 0, 0))
    # branch stubs and shelf fungus
    for k, (t, ang) in enumerate(((0.22, 1.2), (0.48, 1.9), (0.7, 1.4), (0.36, -2.0))):
        p = Vector(axis(t))
        d = Vector((0.2, math.cos(ang), math.sin(ang))).normalized()
        Y.tube(f'A03_stub_{k}', [tuple(p + d * 0.2), tuple(p + d * 0.42), tuple(p + d * 0.6)], lambda tt: 0.085 * (1 - 0.55 * tt), 8, coll(), [DEADWOOD])
    for k, (t, ang) in enumerate(((0.12, -0.6), (0.17, -0.3), (0.2, -0.75), (0.82, 2.6))):
        p = Vector(axis(t))
        shelf = Y.lathe(f'A03_fungus_{k}', [(0.0, 0.0), (0.15, 0.0), (0.16, 0.025), (0.11, 0.045), (0.0, 0.05)], 14, coll(), [FUNGUS])
        shelf.scale = (1.0, 0.6, 1.0)
        shelf.location = p + Vector((0, math.cos(ang) * 0.27, math.sin(ang) * 0.27))
    scatter(lambda x, y: 0.0, 2.6, 0.9, 30, 33, avoid=lambda x, y: abs(y) < 0.4, ferns=4, name='A03_tuft')


# ====================================================================== A04 mossy boulder cover
def build_A04():
    boulder('A04_main', (0.62, 0.52, 0.72), (-0.22, 0.08, 0.66), ROCK, seed=11, rough=0.14)
    boulder('A04_second', (0.42, 0.38, 0.44), (0.52, -0.12, 0.38), ROCK, seed=12, rough=0.16)
    boulder('A04_small', (0.24, 0.22, 0.2), (-0.62, -0.42, 0.17), ROCK, seed=13, rough=0.2)
    for k in range(5):
        boulder(f'A04_pebble_{k}', (0.06, 0.05, 0.04), (-0.7 + 0.35 * k, -0.62 + 0.08 * (k % 2), 0.02), ROCK, seed=70 + k, subd=2)
    for k, (x, y) in enumerate(((-0.75, 0.0), (0.1, -0.5), (0.85, 0.3), (-0.2, 0.62))):
        fern(f'A04_fern_{k}', x, y, 0.0, size=0.45, seed=90 + k)
    scatter(lambda x, y: 0.0, 0.95, 0.7, 14, 44, avoid=lambda x, y: math.hypot(x + 0.2, y) < 0.55, name='A04_tuft')


# ====================================================================== A05 layered standing rock
LAYERS_Z = [0.0, 0.34, 0.62, 0.86, 0.99, 1.29, 1.55, 1.85, 2.08]


def m_strata(name='LayeredStone'):
    """One material for the monolith: beds alternate warm grey / ochre by height, joints darken."""
    m, nt, b = Q.new_mat(name)
    co = Q.coords(nt, (1.3, 1.3, 1.3))
    z = Q.sep(nt, Q.world_pos(nt))[2]
    n1, n2 = Q.noise(nt, co, 2.4, 6, 0.6, 0.3), Q.noise(nt, co, 16.0, 4, 0.6)
    wav = Q.math_(nt, 'SINE', Q.math_(nt, 'MULTIPLY', Q.math_(nt, 'ADD', z, Q.math_(nt, 'MULTIPLY', n1, 0.12)), 11.5))
    grey = Q.mix(nt, Q.smooth(nt, n1, 0.3, 0.75), (0.10, 0.092, 0.078), (0.22, 0.20, 0.168))
    ochre = Q.mix(nt, Q.smooth(nt, n1, 0.3, 0.75), (0.13, 0.095, 0.055), (0.27, 0.19, 0.10))
    col = Q.mix(nt, Q.smooth(nt, wav, 0.1, 0.6), grey, ochre)
    fine = Q.math_(nt, 'SINE', Q.math_(nt, 'MULTIPLY', z, 70.0))
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', Q.smooth(nt, fine, 0.7, 1.0), 0.25), col, (0.06, 0.05, 0.04))
    cav, edge = Q.edge_cavity(nt, 0.05, 0.008)
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', Q.smooth(nt, cav, 0.1, 0.6), 0.75), col, (0.025, 0.022, 0.018))
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', Q.smooth(nt, edge, 0.3, 0.8), 0.35), col, (0.32, 0.29, 0.24))
    lichen = Q.smooth(nt, Q.voronoi(nt, co, 9.0, 'F1'), 0.09, 0.03)
    col = Q.mix(nt, Q.math_(nt, 'MULTIPLY', lichen, 0.45), col, (0.36, 0.38, 0.30))
    m = Q.finish(m, nt, b, col, Q.mixf(nt, n2, 0.82, 0.92), 0.0, Q.math_(nt, 'ADD', n2, Q.math_(nt, 'MULTIPLY', fine, 0.2)), 0.003, 0.9)
    return add_moss(m, 0.55, (0.6, 0.95))


def build_A05():
    """Monolith: subdivided rounded box, beds stepped and grooved at LAYERS_Z, a projecting ledge."""
    mat = m_strata()
    W, D, H = 2.3, 0.82, 2.1
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=13, use_grid_fill=True)
    rnd = random.Random(5)
    shifts = [(rnd.uniform(-0.09, 0.09), rnd.uniform(-0.07, 0.07)) for _ in LAYERS_Z]
    joints = [[rnd.uniform(-0.8, 0.8) for _ in range(rnd.randint(1, 2))] for _ in LAYERS_Z]
    for v in bm.verts:
        c = v.co.copy()                      # cube coords in [-1, 1]
        z = (c.z + 1) / 2 * H
        top = H - 0.25 * (c.x + 1) / 2       # the top falls away to one side, like the reference
        z = min(z, top) if c.z > 0.9 else z * (top / H)
        bed = max(i for i, lz in enumerate(LAYERS_Z) if lz <= z + 1e-6)
        sx, sy = shifts[bed]
        joint = min(abs(z - lz) for lz in LAYERS_Z[1:])
        groove = 0.06 * max(0.0, 1 - joint / 0.06)
        groove += max([0.05 * max(0.0, 1 - abs(c.x - jx) / 0.05) for jx in joints[bed]] + [0.0])   # vertical joints
        taper = 1 - 0.12 * (z / H) ** 1.5
        q = Vector((c.x * 2.1, c.y * 2.1, z * 1.7)) + Vector((3.1, 0.7, 1.9))
        rnd_n = noise.fractal(q, 0.6, 2.2, 5) + 0.6 * noise.noise(q * 0.4)
        sx_ = W / 2 * taper * (1 - 0.06 * (c.y ** 8)) + sx
        sy_ = D / 2 * taper * (1 - 0.06 * (c.x ** 8))
        p = Vector((c.x * sx_, c.y * sy_ + sy, z))
        side = Vector((c.x, c.y, 0))
        if side.length > 1e-6 and abs(c.z) < 0.999:
            side.normalize()
            p -= side * (groove - 0.05 * rnd_n)
        v.co = p
    o = Q._obj('A05_monolith', bm, mat, sharp=50)
    ledge = boulder('A05_ledge', (1.30, 0.6, 0.1), (-0.05, -0.12, 0.93), mat, seed=104, subd=4, rough=0.12, box=5.0, cleave=2)
    for k in range(6):
        boulder(f'A05_fallen_{k}', (0.18, 0.12, 0.05), (-0.95 + 0.38 * k, -0.62 - 0.06 * (k % 2), 0.03), mat, seed=120 + k,
                subd=2, rough=0.3, box=4.0)
    scatter(lambda x, y: 0.0, 1.3, 0.65, 22, 55, avoid=lambda x, y: abs(x) < 1.18 and abs(y) < 0.45, ferns=3, name='A05_tuft')


# ====================================================================== A06 stump with roots that enter the soil
def build_A06():
    Y.lathe('A06_stump', [(0.60, 0.0), (0.52, 0.06), (0.45, 0.16), (0.41, 0.30), (0.40, 0.44)], 28, coll(), [BARK], cap_top=False,
            smooth_angle=55)
    Y.lathe('A06_top', [(0.0, 0.43), (0.40, 0.43), (0.405, 0.45)], 28, coll(), [ENDGRAIN])
    boulder('A06_soil', (1.3, 1.1, 0.13), (0, 0, 0.0), LITTER, seed=8, subd=4, rough=0.2)
    rnd = random.Random(6)

    def root(name, a, reach, r0, z0, start_r):
        pts = []
        for t in np.linspace(0, 1, 14):
            r = start_r + reach * t
            wob = 0.18 * math.sin(t * 5 + a * 3)
            x, y = math.cos(a + wob * t) * r, math.sin(a + wob * t) * r * 0.85
            mound = 0.13 * max(0.0, 1 - (x / 1.3) ** 2 - (y / 1.1) ** 2)
            z = z0 * (1 - t) ** 1.3 + mound * 0.7 * t - 0.12 * max(0.0, t - 0.55)   # dives under the mound surface
            pts.append((x, y, z))
        o = Y.tube(name, pts, lambda t: r0 * (1 - 0.8 * t) + 0.012, 9, coll(), [BARK])
        o.scale = (1.0, 1.0, 1.0)
        for v in o.data.vertices:   # roots are wider than tall
            v.co.z = v.co.z * 0.7 + 0.0
        return pts

    for k in range(9):
        a = k / 9 * math.tau + rnd.uniform(-0.18, 0.18)
        # buttress roots start high on the stump wall and flare out, so the stump widens into them like the reference
        pts = root(f'A06_root_{k}', a, rnd.uniform(0.6, 1.0), rnd.uniform(0.16, 0.21), 0.40, 0.30)
        if k % 2 == 0:   # a smaller side root branching off
            mid = pts[5]
            root(f'A06_subroot_{k}', a + rnd.choice((-0.5, 0.5)), 0.45, 0.05, mid[2] + 0.02, math.hypot(mid[0], mid[1]))
    for k in range(6):
        a = k * 1.1 + 0.4
        fern(f'A06_fern_{k}', math.cos(a) * 1.05, math.sin(a) * 0.9, 0.02, size=0.42, fronds=7, seed=130 + k)
    scatter(lambda x, y: 0.03, 1.25, 1.05, 22, 66, avoid=lambda x, y: math.hypot(x, y) < 0.7, name='A06_tuft')


# ====================================================================== pipeline
ASSETS = {
    'A01': dict(name='SlopeTile', build=build_A01, res=1024, budget=12000, double=True,
                collision=dict(type='heightfield', note='use the top surface as walkable mesh collider; sides are cliffs; datum 0.6 m (place origin at -0.6 so the flat edge meets ground 0)')),
    'A02': dict(name='HollowTile', build=build_A02, res=2048, budget=21000, double=True,
                collision=dict(type='mesh', note='walkable bowl; burrow mouth is a non-walkable trigger (rabbit spawn) at local (0, 1.75); exit ramp on -Y')),
    'A03': dict(name='FallenLog', build=build_A03, res=1024, budget=9000, double=False,
                collision=dict(type='capsule', radius=0.3, from_=[-2.3, 0, 0.3], to=[2.4, 0, 0.43], note='climb-over point at x 0.35 (top 0.72 m); walk-around past the root end (-x)')),
    'A04': dict(name='MossBoulderCover', build=build_A04, res=1024, budget=8000, double=True,
                collision=dict(type='spheres', items=[[-0.22, 0.08, 0.66, 0.62], [0.52, -0.12, 0.38, 0.42]], note='blocks rabbit sight line; crouch cover 1.4 m')),
    'A05': dict(name='LayeredRockCover', build=build_A05, res=1024, budget=8000, double=True,
                collision=dict(type='box', size=[2.3, 0.85, 2.1], center=[0, 0, 1.05], note='tall side cover; ledge at 0.8 m is decorative')),
    'A06': dict(name='RootStump', build=build_A06, res=1024, budget=8000, double=True,
                collision=dict(type='cylinder', radius=0.5, height=0.45, center=[0, 0, 0.225], note='roots are step-over (< 0.3 m): no collider, slow-walk zone r 1.2 m')),
}


def build_asset(aid):
    t0 = time.time()
    a = ASSETS[aid]
    key = f"{aid}_{a['name']}"
    assert (REF / f'{aid}_three_view.png').is_file(), f'{aid}: save and review the AI three-view before modelling'
    Q.reset()
    random.seed(29)
    src = Q.coll('10_Procedural_Source')
    Q.ACTIVE['coll'] = src
    make_materials()
    a['build']()
    parts = [o for o in src.objects if o.type == 'MESH']
    for o in parts:   # anything that dips below the ground plane is pressed onto it: it reads as entering the soil
        mw, inv = o.matrix_world, o.matrix_world.inverted()
        for v in o.data.vertices:
            w = mw @ v.co
            if w.z < 0.0:
                w.z = 0.0
                v.co = inv @ w
    Q.finalize_parts(parts, seed=sum(map(ord, aid)))
    bpy.context.view_layer.update()
    game = Q.coll('00_Game_Export')
    Q.ACTIVE['coll'] = game
    G, _ = Q.game_mesh(key, parts, game)
    tdir = EXPORT / 'textures'
    imgs, alpha = Q.bake_asset(G, key, tdir, a['res'])
    gm = Q.game_material(key, imgs, alpha)
    gm.use_backface_culling = not a['double']   # blades and fern leaflets are thin
    G.data.materials.clear()
    G.data.materials.append(gm)
    G.name = f'{key}_LOD0'
    lods = Q.make_lods(G, gcoll=game)
    for l, nm in zip(lods, ('LOD1', 'LOD2')):
        l.name = f'{key}_{nm}'
    nodes = Q.split_nodes(G, key)
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
    blend = ROOT / 'blend' / f'{key}_v1.blend'
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
        'asset': aid, 'key': key, 'dimensions_m': dims, 'bbox_min': [round(x, 4) for x in mn], 'bbox_max': [round(x, 4) for x in mx],
        'trianglesLOD': tris, 'budgetLOD0': a['budget'], 'withinBudget': tris[0] <= a['budget'],
        'materials': [m.name for m in G.data.materials], 'textureResolution': a['res'], 'doubleSided': a['double'],
        'nodes': [o.name for o in nodes], 'originAtBase': abs(mn[2]) < 0.003, 'meshHealth': health,
        'glbRoundTrip': {'triangles': rt_tris, 'trianglesMatch': rt_tris == tris[0],
                         'bboxMatch': all(abs(p - q) < 0.002 for p, q in zip(rmn + rmx, mn + mx)), 'materials': rmats},
        'files': {p.name: {'bytes': p.stat().st_size, 'sha256': Q.sha(p)} for p in (glb, fbx)},
        'reference': f'art/references/qingxi-encounter-a/{aid}_three_view.png',
        'notChecked': ['Unity import', 'in-game lighting', 'mobile performance', 'LOD screen-size thresholds'],
    }
    info = dict(id=aid, name=a['name'], key=key, units='metre', forward='-Y (Blender) / +Z (glTF)', origin='base centre',
                datum_m=DATUM if aid in ('A01', 'A02') else 0.0, dimensions_m=dims, triangles=tris[0], lod_triangles=tris,
                collision=a['collision'], author='Johnnnny0823 (commission, direction) / Claude Code (procedural modelling, bake, validation)',
                validation=v)
    (EXPORT / f'{key}_model_info.json').write_text(json.dumps(info, indent=1, ensure_ascii=False), encoding='utf-8')
    print(f'[{key}] tris {tris} dims {dims} health {health} roundtrip {rt_tris} {time.time() - t0:.0f}s', flush=True)
    if RENDER:
        previews(key, nodes)
    return v


def previews(key, nodes):
    out = PREV / key
    Q.gpu(bpy.context.scene, 48)
    Q.studio('stylized')
    Q.camera_fit(nodes, 35, 18)
    Q.render(out / 'three_quarter.png', 1024, 64)
    Q.camera_fit(nodes, 0, 10, margin=0.75)
    Q.render(out / 'close_front.png', 1024, 64)
    Q.camera_fit(nodes, 90, 12, margin=0.75)
    Q.render(out / 'close_side.png', 1024, 64)
    if '--quick' in ARGV:
        return
    # 1.7 m stand-in beside the asset for scale
    mn, mx = Q.bbox(nodes)
    fig_m = Q.m_simple('ScaleFigure', (0.20, 0.27, 0.24), (0.22, 0.29, 0.26), rough=0.8)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.24, radius2=0.2, depth=1.45)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, 0.725))
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=0.13, matrix=Matrix.Translation((0, 0, 1.57)))
    fig = Q._obj('QA_ScaleFigure', bm, fig_m)
    fig.location = (mx[0] + 0.55, (mn[1] + mx[1]) / 2, 0)
    Q.camera_fit(nodes + [fig], 25, 12)
    Q.render(out / 'scale_1p7m.png', 1024, 48)
    bpy.data.objects.remove(fig)
    Q.camera_fit(nodes, 180, 14)
    Q.render(out / 'back.png', 768, 48)
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
    # orthographic front / side / back for the reference comparison sheet
    s = bpy.context.scene
    g = bpy.data.objects.get('QA_Ground')
    if g:
        g.hide_render = True
    s.render.film_transparent = True
    mn, mx = Q.bbox(nodes)
    c = Vector([(mn[i] + mx[i]) / 2 for i in range(3)])
    span = max(mx[i] - mn[i] for i in range(3)) * 1.1
    cam = s.camera
    for view, d in (('front', (0, -1, 0)), ('side', (1, 0, 0)), ('back', (0, 1, 0))):
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = span
        cam.location = c + Vector(d) * 30
        cam.rotation_euler = (-Vector(d)).to_track_quat('-Z', 'Y').to_euler()
        Q.render(out / f'ortho_{view}.png', 900, 48)
    s.render.film_transparent = False
    cam.data.type = 'PERSP'


def assemble_master():
    Q.reset()
    for aid, a in ASSETS.items():
        key = f"{aid}_{a['name']}"
        blend = ROOT / 'blend' / f'{key}_v1.blend'
        if not blend.exists():
            continue
        for cname, label in (('10_Procedural_Source', 'source'), ('00_Game_Export', 'game')):
            before = set(bpy.data.collections)
            bpy.ops.wm.append(filepath=str(blend / 'Collection' / cname), directory=str(blend / 'Collection') + '/', filename=cname)
            for c in [c for c in bpy.data.collections if c not in before and c.name.startswith(cname)]:
                c.name = f'{key}__{label}'
                if label == 'source':
                    c.hide_render = True
                    c.hide_viewport = True
    bpy.context.scene['author'] = 'Johnnnny0823 (commission) / Claude Code (modelling)'
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'Qingxi_Encounter_A.blend'), compress=True, relative_remap=True)
    print('MASTER_SAVED', flush=True)


if '--master' in ARGV:
    assemble_master()
else:
    todo = [a for a in ARGV if not a.startswith('--')] or list(ASSETS)
    report = {aid: build_asset(aid) for aid in todo}
    print('DONE', json.dumps({k: [v['trianglesLOD'], v['glbRoundTrip']['trianglesMatch'], v['withinBudget']] for k, v in report.items()}), flush=True)
