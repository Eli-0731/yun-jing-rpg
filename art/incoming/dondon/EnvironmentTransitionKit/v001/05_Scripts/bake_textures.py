"""Bake the kit's seamless 1024 px PBR textures (Base Color, Roughness, Normal) in a fresh Blender session.

  blender -b --python-exit-code 1 --python 05_Scripts/bake_textures.py

Each material is designed as procedural nodes sampled on 4D torus coordinates of the UV square, so the
baked images tile without seams.  1 texture repeat = 2 m (kit_spec.UV_TILE_M).  Outputs 03_Textures/
T_<Layer>_BaseColor.png (sRGB), _Roughness.png and _Normal.png (Non-Color, OpenGL tangent space)
plus T_BlendNoise.png, T_Water_Normal.png (stream ripples) and the log-bridge sets Bark, Wood (adzed top) and EndGrain
(sawn end, centred on the UV square, the only set that does not tile).  Existing textures are never overwritten.
"""
import sys
from pathlib import Path
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit_blender as KB

RES = 1024


def F(nb, op, a, b=None):
    return nb.math(op, a, b)


def st(nb, x, lo=0.36, hi=0.64):
    """Stretch a noise output (which clusters around 0.5) to the full 0..1 range."""
    return nb.maprange(x, lo, hi)


def cells(nb, t, scale, feature='F1'):
    """Voronoi cells: (distance socket, random 0..1 per cell)."""
    vor = nb.voronoi4(t, scale, feature)
    if feature == 'DISTANCE_TO_EDGE':
        return vor.outputs['Distance'], None
    sep = nb.node('ShaderNodeSeparateColor'); nb.link(vor.outputs['Color'], sep.inputs['Color'])
    return vor.outputs['Distance'], sep.outputs['Red']


def cell_rnd2(nb, t, scale):
    """Two independent per-cell random values of the F1 cells at this scale."""
    vor = nb.voronoi4(t, scale, 'F1'); sep = nb.node('ShaderNodeSeparateColor'); nb.link(vor.outputs['Color'], sep.inputs['Color'])
    return vor.outputs['Distance'], sep.outputs['Red'], sep.outputs['Green']


def pebbles(nb, t, scale, r0, r1, tones, density=1.0, wobble=None, rim=0.45):
    """Loose pebbles lying in soil: coverage, tone, dome height and a contact-shadow ring.

    Scale is in torus units: one 2 m tile is 2*pi units around, so a cell is about 0.32 m / scale."""
    dist, rnd, rnd2 = cell_rnd2(nb, t, scale)
    if wobble is not None: dist = F(nb, 'ADD', dist, F(nb, 'MULTIPLY', F(nb, 'SUBTRACT', wobble, 0.5), 0.35))
    present = nb.maprange(rnd2, density - 0.02, density, 1.0, 0.0)               # drop whole pebbles
    rr = F(nb, 'ADD', r1, F(nb, 'MULTIPLY', rnd, 0.06))
    m = F(nb, 'MULTIPLY', nb.maprange(F(nb, 'SUBTRACT', dist, rr), r0 - r1, 0.0, 1.0, 0.0, smooth=True), present)
    dome = F(nb, 'MULTIPLY', present, F(nb, 'POWER', nb.maprange(F(nb, 'SUBTRACT', dist, rr), -0.22, 0.0, 1.0, 0.0), 0.5))
    tone = nb.mix_rgb(F(nb, 'MULTIPLY', F(nb, 'SUBTRACT', 1.0, dome), rim), nb.ramp(rnd, tones), (0.030, 0.027, 0.023))   # darker rims
    ring = F(nb, 'MULTIPLY', present, nb.maprange(F(nb, 'SUBTRACT', dist, rr), 0.0, 0.12, 1.0, 0.0, smooth=True))
    return m, tone, dome, ring


def packed(nb, t, scale, gap0, gap1, tones):
    """Stones packed edge to edge (gravel): coverage, tone, height, per-cell random."""
    edge = nb.voronoi4(t, scale, 'DISTANCE_TO_EDGE').outputs['Distance']
    _, rnd, rnd2 = cell_rnd2(nb, t, scale)
    cover = nb.maprange(edge, gap0, gap1, 0.0, 1.0, smooth=True)
    dome = F(nb, 'POWER', nb.maprange(edge, gap0, 0.34, 0.0, 1.0), 0.5)
    tone = nb.mix_rgb(F(nb, 'MULTIPLY', F(nb, 'SUBTRACT', 1.0, dome), 0.5), nb.ramp(rnd, tones), (0.028, 0.025, 0.021))
    h = F(nb, 'MULTIPLY', dome, nb.maprange(rnd2, 0.0, 1.0, 0.55, 1.0))
    return cover, tone, h, rnd2


def speckle(nb, t, scale):
    _, rnd = cells(nb, t, scale); return rnd


def over(nb, col, fac, colour, k=1.0):
    return nb.mix_rgb(fac if k == 1.0 else F(nb, 'MULTIPLY', fac, k), col, colour)


def H(nb, *terms):
    """Weighted height sum: H(nb, (socket, weight), ...)."""
    out = None
    for sock_, w in terms:
        v = F(nb, 'MULTIPLY', sock_, w)
        out = v if out is None else F(nb, 'ADD', out, v)
    return out


def drysoil(nb):
    """Packed dry earth of a country road: dusty patches, embedded pebbles, grit, crumbs and hairline cracks."""
    t = nb.torus()
    macro = st(nb, nb.noise4(t, 0.9, 4, 0.5)[0]); meso = st(nb, nb.noise4(t, 3.0, 5, 0.55)[0]); wob = nb.noise4(t, 10.0, 3, 0.5)[0]
    col = nb.ramp(macro, [(0.0, (0.092, 0.071, 0.051)), (0.5, (0.150, 0.118, 0.086)), (1.0, (0.205, 0.170, 0.128))])
    col = over(nb, col, nb.maprange(meso, 0.62, 0.95, smooth=True), (0.240, 0.206, 0.160), 0.55)        # dusty
    col = over(nb, col, nb.maprange(meso, 0.05, 0.35, 1.0, 0.0, smooth=True), (0.080, 0.061, 0.044), 0.45)  # compacted
    sp = speckle(nb, t, 55.0)
    col = over(nb, col, nb.maprange(sp, 0.78, 1.0), (0.270, 0.235, 0.190), 0.7)
    col = over(nb, col, nb.maprange(sp, 0.18, 0.0), (0.055, 0.043, 0.032), 0.6)
    crumb = cells(nb, t, 11.0, 'DISTANCE_TO_EDGE')[0]
    crumb_l = F(nb, 'MULTIPLY', nb.maprange(crumb, 0.0, 0.05, 1.0, 0.0), nb.maprange(meso, 0.3, 0.7))
    col = over(nb, col, crumb_l, (0.070, 0.054, 0.040), 0.35)
    g_m, g_tone, g_dome, g_ring = pebbles(nb, t, 15.0, 0.14, 0.22, [(0.0, (0.095, 0.088, 0.078)), (0.5, (0.190, 0.172, 0.145)), (1.0, (0.290, 0.268, 0.230))], 0.55, wob)
    p_m, p_tone, p_dome, p_ring = pebbles(nb, t, 4.6, 0.20, 0.25, [(0.0, (0.075, 0.070, 0.062)), (0.35, (0.125, 0.115, 0.100)), (0.7, (0.175, 0.155, 0.125)), (1.0, (0.215, 0.200, 0.175))], 0.55, wob, rim=0.15)
    col = over(nb, col, g_ring, (0.065, 0.050, 0.037), 0.35); col = over(nb, col, g_m, g_tone)
    col = over(nb, col, p_ring, (0.055, 0.043, 0.032), 0.22); col = over(nb, col, p_m, p_tone)
    cdist = cells(nb, t, 1.3, 'DISTANCE_TO_EDGE')[0]; cg = nb.noise4(t, 1.8, 3, 0.5)[0]
    crack = F(nb, 'MULTIPLY', nb.maprange(cdist, 0.0, 0.007, 1.0, 0.0), nb.maprange(cg, 0.52, 0.62))
    col = over(nb, col, crack, (0.045, 0.035, 0.026), 0.85)
    rough = F(nb, 'SUBTRACT', nb.maprange(meso, 0.0, 1.0, 0.86, 0.95), F(nb, 'MULTIPLY', p_m, 0.14))
    h = F(nb, 'SUBTRACT', H(nb, (macro, 0.25), (meso, 0.25), (p_dome, 0.9), (g_dome, 0.35), (sp, 0.05)), H(nb, (crumb_l, 0.12), (crack, 0.4)))
    return col, rough, h, 1.0


def wetsoil(nb):
    """Dark river mud: silt streaks, glossy puddles, wet pebbles."""
    t = nb.torus()
    macro = st(nb, nb.noise4(t, 1.0, 4, 0.5)[0]); meso = st(nb, nb.noise4(t, 3.2, 5, 0.55)[0]); pud = st(nb, nb.noise4(t, 1.5, 4, 0.5)[0])
    wob = nb.noise4(t, 30.0, 2, 0.5)[0]
    col = nb.ramp(macro, [(0.0, (0.036, 0.028, 0.020)), (0.5, (0.060, 0.047, 0.034)), (1.0, (0.092, 0.074, 0.054))])
    col = over(nb, col, nb.maprange(meso, 0.65, 0.95, smooth=True), (0.115, 0.098, 0.076), 0.5)           # dried silt
    sp = speckle(nb, t, 50.0); col = over(nb, col, nb.maprange(sp, 0.8, 1.0), (0.130, 0.115, 0.095), 0.5)
    p_m, p_tone, p_dome, p_ring = pebbles(nb, t, 5.2, 0.16, 0.24, [(0.0, (0.050, 0.047, 0.042)), (0.5, (0.095, 0.088, 0.078)), (1.0, (0.150, 0.140, 0.122))], 0.45, wob)
    g_m, g_tone, g_dome, _ = pebbles(nb, t, 16.0, 0.14, 0.2, [(0.0, (0.055, 0.050, 0.044)), (1.0, (0.130, 0.120, 0.104))], 0.5, wob)
    col = over(nb, col, p_ring, (0.025, 0.020, 0.015), 0.5); col = over(nb, col, p_m, p_tone); col = over(nb, col, g_m, g_tone)
    puddle = nb.maprange(pud, 0.70, 0.80, smooth=True)
    col = over(nb, col, puddle, (0.030, 0.024, 0.018), 0.35)
    rough = nb.mix_f(puddle, F(nb, 'SUBTRACT', nb.maprange(meso, 0.0, 1.0, 0.52, 0.74), F(nb, 'MULTIPLY', p_m, 0.12)), 0.18)
    h = F(nb, 'MULTIPLY', H(nb, (macro, 0.2), (meso, 0.3), (p_dome, 0.8), (g_dome, 0.3)), F(nb, 'SUBTRACT', 1.0, F(nb, 'MULTIPLY', puddle, 0.9)))
    return col, rough, h, 0.9


def grass(nb):
    t = nb.torus()
    n1, _ = nb.noise4(t, 3.0, 6, 0.55); n2, _ = nb.noise4(t, 1.3, 4, 0.5); n3, _ = nb.noise4(t, 4.5, 4, 0.5); clump, _ = nb.noise4(t, 9.0, 4, 0.6)
    macro = st(nb, nb.noise4(t, 0.8, 3, 0.5)[0])
    s1 = speckle(nb, t, 70.0); s2 = speckle(nb, t, 150.0)
    blades = F(nb, 'ADD', F(nb, 'MULTIPLY', s1, 0.55), F(nb, 'MULTIPLY', s2, 0.45))
    col = nb.ramp(blades, [(0.0, (0.020, 0.036, 0.012)), (0.45, (0.058, 0.092, 0.030)), (0.80, (0.112, 0.148, 0.050)), (1.0, (0.165, 0.180, 0.070))])
    col = over(nb, col, nb.maprange(clump, 0.52, 0.70), (0.024, 0.042, 0.015), 0.55)
    col = over(nb, col, nb.maprange(macro, 0.6, 1.0), (0.120, 0.135, 0.052), 0.45)
    col = over(nb, col, nb.maprange(macro, 0.3, 0.0), (0.035, 0.055, 0.020), 0.4)
    dry = nb.maprange(n2, 0.60, 0.70, smooth=True); col = over(nb, col, F(nb, 'MULTIPLY', dry, blades), (0.190, 0.168, 0.090), 0.9)
    soil = nb.maprange(n3, 0.68, 0.78, smooth=True); col = over(nb, col, soil, (0.100, 0.080, 0.058), 0.65)
    rough = nb.maprange(blades, 0.0, 1.0, 0.9, 0.72)
    h = H(nb, (blades, 0.55), (clump, 0.3), (macro, 0.15))
    return col, rough, h, 0.9


def moss(nb):
    t = nb.torus()
    d1, _ = cells(nb, t, 26.0, 'SMOOTH_F1'); n1, _ = nb.noise4(t, 5.0, 5, 0.55); s1 = speckle(nb, t, 120.0)
    cushion = nb.maprange(d1, 0.0, 0.55, 1.0, 0.0, smooth=True)
    fuzz = F(nb, 'ADD', F(nb, 'MULTIPLY', cushion, 0.65), F(nb, 'MULTIPLY', s1, 0.35))
    col = nb.ramp(fuzz, [(0.10, (0.022, 0.040, 0.014)), (0.55, (0.058, 0.100, 0.030)), (0.90, (0.105, 0.150, 0.048)), (1.0, (0.140, 0.172, 0.058))])
    col = over(nb, col, nb.maprange(n1, 0.58, 0.75), (0.125, 0.140, 0.052), 0.4)
    rough = nb.maprange(n1, 0.3, 0.7, 0.86, 0.96)
    h = H(nb, (cushion, 0.6), (s1, 0.4))
    return col, rough, h, 0.8


def rock(nb):
    """Warm grey stone: mottling, mineral grains, pale lichen and fine cracks."""
    t = nb.torus()
    macro = st(nb, nb.noise4(t, 1.1, 6, 0.6, distortion=0.4)[0], 0.34, 0.66); meso = st(nb, nb.noise4(t, 4.0, 6, 0.6)[0]); fine = nb.noise4(t, 14.0, 4, 0.6)[0]
    col = nb.ramp(macro, [(0.0, (0.052, 0.050, 0.047)), (0.35, (0.100, 0.096, 0.088)), (0.7, (0.150, 0.141, 0.126)), (1.0, (0.200, 0.190, 0.172))])
    hue = st(nb, nb.noise4(t, 0.7, 3, 0.5)[0], 0.38, 0.62)                       # stone-sized warm / cool patches
    col = over(nb, col, nb.maprange(hue, 0.62, 1.0, smooth=True), (0.140, 0.112, 0.082), 0.45)
    col = over(nb, col, nb.maprange(hue, 0.38, 0.0, smooth=True), (0.088, 0.098, 0.106), 0.45)
    col = over(nb, col, nb.maprange(meso, 0.28, 0.0, smooth=True), (0.062, 0.060, 0.055), 0.6)
    col = over(nb, col, nb.maprange(meso, 0.75, 1.0, smooth=True), (0.205, 0.196, 0.178), 0.4)
    sp = speckle(nb, t, 42.0)
    col = over(nb, col, nb.maprange(sp, 0.86, 1.0), (0.245, 0.238, 0.220), 0.6)
    col = over(nb, col, nb.maprange(sp, 0.10, 0.0), (0.040, 0.039, 0.036), 0.6)
    lich_n = st(nb, nb.noise4(t, 2.6, 4, 0.6)[0]); spots = cells(nb, t, 20.0, 'F1')[0]
    lichen = F(nb, 'MULTIPLY', nb.maprange(lich_n, 0.74, 0.84, smooth=True), nb.maprange(spots, 0.25, 0.55, 1.0, 0.35))
    col = over(nb, col, lichen, (0.180, 0.182, 0.125), 0.7)
    cdist = cells(nb, t, 1.6, 'DISTANCE_TO_EDGE')[0]; gate = nb.noise4(t, 1.6, 3, 0.5)[0]
    crack = F(nb, 'MULTIPLY', nb.maprange(cdist, 0.0, 0.009, 1.0, 0.0), nb.maprange(gate, 0.48, 0.60))
    col = over(nb, col, crack, (0.030, 0.029, 0.027), 0.9)
    rough = F(nb, 'ADD', nb.maprange(macro, 0.0, 1.0, 0.70, 0.86), F(nb, 'MULTIPLY', lichen, 0.08))
    h = F(nb, 'SUBTRACT', H(nb, (macro, 0.45), (meso, 0.3), (fine, 0.12), (sp, 0.04)), F(nb, 'MULTIPLY', crack, 0.5))
    return col, rough, h, 1.0


def pathgravel(nb):
    """Packed path gravel: angular stones of mixed tones over dark grit, thinner where the path is worn."""
    t = nb.torus()
    worn = nb.maprange(st(nb, nb.noise4(t, 1.1, 3, 0.5)[0]), 0.55, 0.85, smooth=True); n1 = st(nb, nb.noise4(t, 3.0, 5, 0.55)[0])
    col = nb.ramp(n1, [(0.0, (0.070, 0.056, 0.042)), (1.0, (0.125, 0.102, 0.076))])
    sp = speckle(nb, t, 60.0); col = over(nb, col, nb.maprange(sp, 0.75, 1.0), (0.190, 0.170, 0.140), 0.6)
    tones = [(0.0, (0.090, 0.085, 0.077)), (0.25, (0.150, 0.140, 0.126)), (0.5, (0.205, 0.190, 0.165)), (0.72, (0.180, 0.142, 0.100)), (0.86, (0.240, 0.228, 0.205)), (1.0, (0.120, 0.112, 0.104))]
    c1, t1, h1, r1 = packed(nb, t, 7.5, 0.06, 0.11, tones)
    keep1 = nb.maprange(F(nb, 'SUBTRACT', r1, F(nb, 'SUBTRACT', 0.80, F(nb, 'MULTIPLY', worn, 0.5))), 0.0, 0.03, 1.0, 0.0)
    c1 = F(nb, 'MULTIPLY', c1, keep1)
    c2, t2, h2, r2 = packed(nb, t, 3.2, 0.08, 0.14, tones)
    keep2 = nb.maprange(r2, 0.15, 0.18, 1.0, 0.0); c2 = F(nb, 'MULTIPLY', c2, keep2)
    col = over(nb, col, c1, t1); col = over(nb, col, c2, t2)
    col = over(nb, col, worn, (0.200, 0.172, 0.135), 0.22)                                                  # dust in the worn track
    rough = F(nb, 'SUBTRACT', 0.92, F(nb, 'ADD', F(nb, 'MULTIPLY', c1, 0.12), F(nb, 'MULTIPLY', c2, 0.14)))
    h = H(nb, (F(nb, 'MULTIPLY', c1, h1), 0.6), (F(nb, 'MULTIPLY', c2, h2), 1.0), (n1, 0.12))
    return col, rough, h, 1.0


def water(nb):
    """Ripple normal for a slow stream: ripples stretched along V (the flow direction of a UV laid along the river)."""
    t1 = nb.torus(ru=2.6, rv=0.8); t2 = nb.torus(ru=3.2, rv=1.1, offset=(0.37, 0.21))
    h = H(nb, (nb.noise4(t1, 2.2, 4, 0.55)[0], 0.7), (nb.noise4(t2, 6.0, 3, 0.5)[0], 0.3))
    return None, None, h, 0.6


def bark(nb):
    """Weathered bark: plates split by long fissures running along V (the log axis), grey weathering, pale lichen."""
    t = nb.torus(); tv = nb.torus(ru=5.0, rv=0.45)
    edge = cells(nb, tv, 1.5, 'DISTANCE_TO_EDGE')[0]; _, prnd = cells(nb, tv, 1.5)
    fiss = nb.maprange(edge, 0.0, 0.05, 1.0, 0.0, smooth=True)
    macro = st(nb, nb.noise4(t, 1.2, 4, 0.5)[0]); fine = nb.noise4(tv, 9.0, 4, 0.6)[0]
    col = nb.ramp(prnd, [(0.0, (0.070, 0.058, 0.047)), (0.5, (0.110, 0.092, 0.074)), (1.0, (0.148, 0.128, 0.106))])
    col = over(nb, col, nb.maprange(macro, 0.6, 1.0, smooth=True), (0.170, 0.163, 0.148), 0.4)
    col = over(nb, col, nb.maprange(fine, 0.62, 0.75), (0.060, 0.050, 0.040), 0.35)
    streak = nb.noise4(nb.torus(ru=12.0, rv=0.6), 6.0, 4, 0.6)[0]                      # fine vertical striation inside the plates
    col = over(nb, col, nb.maprange(streak, 0.55, 0.75), (0.050, 0.042, 0.034), 0.45)
    col = over(nb, col, fiss, (0.028, 0.022, 0.017), 0.75)
    lich = F(nb, 'MULTIPLY', nb.maprange(st(nb, nb.noise4(t, 1.6, 5, 0.65)[0]), 0.84, 0.94, smooth=True), F(nb, 'SUBTRACT', 1.0, fiss))
    col = over(nb, col, lich, (0.170, 0.178, 0.135), 0.35)
    rough = F(nb, 'ADD', 0.8, F(nb, 'MULTIPLY', fiss, 0.15))
    h = H(nb, (F(nb, 'SUBTRACT', 1.0, fiss), 0.8), (fine, 0.25), (streak, 0.2), (macro, 0.1))
    return col, rough, h, 1.0


def wood(nb):
    """Adzed, weathered top of the log: grain along U (the log axis), shallow adze scallops, fine checks."""
    t = nb.torus(); tg = nb.torus(ru=0.45, rv=6.0)
    g = st(nb, nb.noise4(tg, 3.0, 6, 0.6, distortion=0.3)[0])
    col = nb.ramp(g, [(0.0, (0.150, 0.112, 0.078)), (0.5, (0.215, 0.168, 0.122)), (1.0, (0.285, 0.235, 0.180))])
    col = over(nb, col, nb.maprange(st(nb, nb.noise4(t, 1.0, 3, 0.5)[0]), 0.45, 1.0), (0.290, 0.280, 0.255), 0.55)   # silver weathering
    uvn = nb.node('ShaderNodeTexCoord'); sep = nb.node('ShaderNodeSeparateXYZ'); nb.link(uvn.outputs['UV'], sep.inputs['Vector'])
    wob = nb.noise4(t, 4.0, 2, 0.5)[0]
    sc = F(nb, 'SINE', F(nb, 'MULTIPLY', F(nb, 'ADD', sep.outputs['X'], F(nb, 'MULTIPLY', wob, 0.02)), 2 * 3.14159265 * 22))   # 22 scallops per tile: tiles
    scallop = nb.maprange(sc, -1.0, 1.0)
    chk = cells(nb, tg, 5.0, 'DISTANCE_TO_EDGE')[0]
    crack = F(nb, 'MULTIPLY', nb.maprange(chk, 0.0, 0.012, 1.0, 0.0), nb.maprange(nb.noise4(t, 2.0, 2, 0.5)[0], 0.55, 0.65))
    col = over(nb, col, crack, (0.050, 0.038, 0.028), 0.85)
    col = over(nb, col, F(nb, 'MULTIPLY', scallop, 0.25), (0.120, 0.095, 0.070))
    rough = nb.maprange(g, 0.0, 1.0, 0.72, 0.86)
    h = F(nb, 'SUBTRACT', H(nb, (g, 0.3), (scallop, 0.45)), F(nb, 'MULTIPLY', crack, 0.5))
    return col, rough, h, 0.8


def endgrain(nb):
    """Sawn log end (not tiling; centred on the UV square): growth rings, darker sapwood rim, a few radial checks."""
    tc = nb.node('ShaderNodeTexCoord'); sep = nb.node('ShaderNodeSeparateXYZ'); nb.link(tc.outputs['UV'], sep.inputs['Vector'])
    x = F(nb, 'SUBTRACT', sep.outputs['X'], 0.5); y = F(nb, 'SUBTRACT', sep.outputs['Y'], 0.5)
    r = F(nb, 'SQRT', F(nb, 'ADD', F(nb, 'MULTIPLY', x, x), F(nb, 'MULTIPLY', y, y))); ang = nb.math('ARCTAN2', y, x)
    n = nb.node('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 5.0; nb.link(tc.outputs['UV'], n.inputs['Vector'])
    ring = nb.maprange(F(nb, 'SINE', F(nb, 'MULTIPLY', F(nb, 'ADD', r, F(nb, 'MULTIPLY', n.outputs['Fac'], 0.025)), 2 * 3.14159265 * 34)), -1.0, 1.0)
    col = nb.ramp(r, [(0.0, (0.300, 0.225, 0.145)), (0.30, (0.340, 0.262, 0.172)), (0.40, (0.285, 0.215, 0.140)), (0.45, (0.120, 0.095, 0.070))])
    col = nb.mix_rgb(F(nb, 'MULTIPLY', ring, 0.35), col, (0.170, 0.118, 0.072))
    rad = F(nb, 'ABSOLUTE', F(nb, 'SINE', F(nb, 'ADD', F(nb, 'MULTIPLY', ang, 2.5), F(nb, 'MULTIPLY', n.outputs['Fac'], 1.2))))
    check = F(nb, 'MULTIPLY', nb.maprange(rad, 0.0, 0.025, 1.0, 0.0), F(nb, 'MULTIPLY', nb.maprange(r, 0.08, 0.16), nb.maprange(r, 0.42, 0.30)))
    col = nb.mix_rgb(F(nb, 'MULTIPLY', check, 0.9), col, (0.045, 0.032, 0.020))
    rough = nb.maprange(ring, 0.0, 1.0, 0.72, 0.86)
    h = F(nb, 'SUBTRACT', F(nb, 'MULTIPLY', ring, 0.3), F(nb, 'MULTIPLY', check, 0.7))
    return col, rough, h, 0.7


def timber(nb):
    """Warm sawn timber for the D02 bridge (planks, beams, posts): grain along U, slight weathering, knots."""
    t = nb.torus(); tg = nb.torus(ru=0.45, rv=6.0)
    g = st(nb, nb.noise4(tg, 3.2, 6, 0.6, distortion=0.35)[0])
    col = nb.ramp(g, [(0.0, (0.140, 0.082, 0.044)), (0.5, (0.215, 0.135, 0.075)), (1.0, (0.300, 0.200, 0.115))])
    col = over(nb, col, nb.maprange(st(nb, nb.noise4(t, 0.9, 3, 0.5)[0]), 0.6, 1.0), (0.235, 0.205, 0.165), 0.3)    # light weathering
    knot_d, _ = cells(nb, nb.torus(ru=1.0, rv=1.6), 2.2); knot = nb.maprange(knot_d, 0.0, 0.07, 1.0, 0.0, smooth=True)
    col = over(nb, col, knot, (0.075, 0.042, 0.022), 0.8)
    chk = cells(nb, tg, 5.0, 'DISTANCE_TO_EDGE')[0]
    crack = F(nb, 'MULTIPLY', nb.maprange(chk, 0.0, 0.010, 1.0, 0.0), nb.maprange(nb.noise4(t, 2.0, 2, 0.5)[0], 0.58, 0.66))
    col = over(nb, col, crack, (0.045, 0.028, 0.016), 0.85)
    rough = nb.maprange(g, 0.0, 1.0, 0.62, 0.8)
    h = F(nb, 'SUBTRACT', H(nb, (g, 0.35), (knot, 0.25)), F(nb, 'MULTIPLY', crack, 0.5))
    return col, rough, h, 0.8


RECIPES = {'DrySoil': drysoil, 'WetSoil': wetsoil, 'Grass': grass, 'Moss': moss, 'Rock': rock, 'PathGravel': pathgravel, 'Water': water, 'Bark': bark, 'Wood': wood, 'EndGrain': endgrain, 'Timber': timber}


def bake_one(obj, mat, img, kind):
    nt = mat.node_tree
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img
    for n in nt.nodes: n.select = False
    tex.select = True; nt.nodes.active = tex
    if kind == 'NORMAL':
        bpy.ops.object.bake(type='NORMAL', normal_space='TANGENT', margin=0, use_clear=True)
    else:
        bpy.ops.object.bake(type='EMIT', margin=0, use_clear=True)
    nt.nodes.remove(tex)


def main():
    only = sys.argv[sys.argv.index('--only') + 1].split(',') if '--only' in sys.argv else None
    scene = KB.start_session()
    scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = 4
    out = {}
    for layer in list(RECIPES) + ['BlendNoise']:
        if only and layer not in only: continue
        kinds = ['BlendNoise'] if layer == 'BlendNoise' else ['Normal'] if layer == 'Water' else ['BaseColor', 'Roughness', 'Normal']
        for k in kinds:
            name = 'T_BlendNoise.png' if layer == 'BlendNoise' else 'T_%s_%s.png' % (layer, k)
            out[name] = KB.new_output('03_Textures/' + name)
    me = bpy.data.meshes.new('BakePlane'); me.from_pydata([(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)], [], [(0, 1, 2, 3)]); me.update()
    uv = me.uv_layers.new(name='UVMap')
    for li, c in zip(range(4), [(0, 0), (1, 0), (1, 1), (0, 1)]): uv.data[li].uv = c
    ob = bpy.data.objects.new('BakePlane', me); scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    for layer, recipe in list(RECIPES.items()) + [('BlendNoise', None)]:
        if only and layer not in only: continue
        m = bpy.data.materials.new('BAKE_' + layer); m.use_nodes = True; me.materials.clear(); me.materials.append(m)
        nb = KB.NB(m); out_node = nb.n['Material Output']; prin = nb.n['Principled BSDF']
        if recipe is None:
            tb = nb.torus(); comb = nb.node('ShaderNodeCombineColor')                 # R: 10 cm, G: 30 cm, B: 4 cm blend noise
            for ch, (sc, det) in zip(('Red', 'Green', 'Blue'), ((3.0, 6), (1.0, 4), (8.0, 3))):
                nb.link(nb.maprange(nb.noise4(tb, sc, det, 0.55)[0], 0.3, 0.7), comb.inputs[ch])
            passes = [('BlendNoise', comb.outputs['Color'], None)]
        else:
            col, rough, h, strength = recipe(nb)
            bump = nb.node('ShaderNodeBump'); bump.inputs['Strength'].default_value = strength; bump.inputs['Distance'].default_value = 0.012
            nb.link(h, bump.inputs['Height']); nb.link(bump.outputs['Normal'], prin.inputs['Normal'])
            passes = [('Normal', None, True)] if layer == 'Water' else [('BaseColor', col, False), ('Roughness', rough, True), ('Normal', None, True)]
        emit = nb.node('ShaderNodeEmission')
        for kind, sock_, non_color in passes:
            name = 'T_BlendNoise.png' if kind == 'BlendNoise' else 'T_%s_%s.png' % (layer, kind)
            img = bpy.data.images.new(name, RES, RES, alpha=False, float_buffer=False)
            img.colorspace_settings.name = 'sRGB' if kind == 'BaseColor' else 'Non-Color'
            if kind == 'Normal':
                nb.link(prin.outputs['BSDF'], out_node.inputs['Surface']); bake_one(ob, m, img, 'NORMAL')
            else:
                nb.link(sock_, emit.inputs['Color']); nb.link(emit.outputs['Emission'], out_node.inputs['Surface']); bake_one(ob, m, img, 'EMIT')
            img.filepath_raw = str(out[name]); img.file_format = 'PNG'; img.save()
            print('BAKED', name, flush=True)
    print('DONE', flush=True)


if __name__ == '__main__':
    main()
