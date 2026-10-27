"""Procedural builders for the alchemy workshop kit. Each builder(state) creates its parts in the active
collection and returns (parts, info). info carries the asset metadata used by build.py / validation."""
import math
from mathutils import Vector
import qa_lib as Q

TAU = math.tau
ASSETS = {}


def asset(aid, name, states=('default',), res=1024, budget=6000, size=None, collision=None):
    def deco(fn):
        ASSETS[aid] = dict(id=aid, name=name, states=states, res=res, budget=budget, size=size, collision=collision, build=fn)
        return fn
    return deco


# ============================================================================ B01 bronze furnace
RIM_TOP = 0.785          # furnace rim top (lid seat)
RIM_IN = 0.210           # rim inner radius
LID_SEAT_Z = RIM_TOP + 0.001 - 0.040   # lid origin when seated (lid flange underside is at lid z = 0.040)

FURNACE_OUT = [(0, 0.14), (0.10, 0.14), (0.165, 0.152), (0.215, 0.172), (0.262, 0.205), (0.300, 0.245), (0.330, 0.292),
               (0.348, 0.345), (0.355, 0.40), (0.350, 0.455), (0.336, 0.505), (0.316, 0.548),
               (0.300, 0.574), (0.306, 0.578), (0.306, 0.590), (0.296, 0.594),                     # lower band moulding
               (0.282, 0.612), (0.268, 0.632), (0.258, 0.652),
               (0.262, 0.656), (0.262, 0.668), (0.252, 0.672),                                     # upper band moulding
               (0.240, 0.690), (0.233, 0.708), (0.232, 0.722),
               (0.252, 0.726), (0.262, 0.734), (0.264, 0.746), (0.262, 0.766), (0.256, 0.776),    # rim lip
               (0.246, 0.782), (0.236, 0.785), (0.218, 0.785), (0.212, 0.782),
               (RIM_IN, 0.774), (RIM_IN, 0.740), (0.205, 0.712), (0.232, 0.66), (0.268, 0.60),     # inner wall
               (0.290, 0.54), (0.284, 0.50), (0.24, 0.475), (0.14, 0.462), (0, 0.458)]


@asset('B01', 'BronzeFurnace', states=('cold', 'heating'), res=1024, budget=15000, size=(0.86, 0.80, 0.92),
       collision={'type': 'capsule', 'radius': 0.38, 'height': 0.80, 'center': [0, 0, 0.42], 'note': 'player blocker; interaction trigger 1.1 m in front of the mouth'})
def b01(state='cold'):
    heat = 1.0 if state == 'heating' else 0.0
    br = Q.m_bronze('B01_Bronze', patina=0.65, polish=0.65, band=(0.623, 0.026, 0.009, 12.0), seams=True, smudge=((0, -0.33, 0.50), (0.16, 0.12, 0.09)))
    br2 = Q.m_bronze('B01_BronzeFittings', patina=0.35, polish=0.8)
    soot = Q.m_bronze('B01_BronzeSooty', patina=0.2, polish=0.3, soot=0.85)
    ref = Q.m_refractory('B01_Firebox', heat=heat * 0.55, floor_z=0.20)
    stone = Q.m_stone('B01_PadStone', light=(0.30, 0.29, 0.27), dark=(0.19, 0.185, 0.175), scale=1.5)
    coal = Q.m_coal('B01_Coal', heat=heat * 0.7)
    iron = Q.m_iron('B01_Grate', rust=0.4)
    P = []
    body = Q.lathe('Furnace_Body', FURNACE_OUT, br, segs=52, sharp=34)
    # inner crucible wall darker: separate soot shell just inside the rim is overkill; the rim interior uses AO darkening.
    # fire mouth: arched cave carved into the belly, lined with refractory brick
    cave = Q.prism('Cut_Mouth', Q.arch_outline(0.27, 0.195, 0.335, 14), 0.60, ref, axis='Y', center=-0.20)
    Q.boolean(body, cave); Q.apply_mods(body); P.append(body)
    # conforming cast frame: a 16 mm shell over the belly, cut to the frame outline (arch band + vented side plates)
    up = [(r + 0.017, z) for r, z in FURNACE_OUT[2:12]]
    ring = up + [(r - 0.004, z) for r, z in reversed(FURNACE_OUT[2:12])] + [up[0]]
    shell = Q.lathe('Furnace_MouthFrame', ring, br2, segs=96, sharp=30)
    t0 = math.acos(0.148 / 0.17)
    arc = [(0.17 * math.cos(math.pi - t0 - i * (math.pi - 2 * t0) / 16), 0.335 + 0.17 * math.sin(math.pi - t0 - i * (math.pi - 2 * t0) / 16)) for i in range(17)]
    outline = [(-0.245, 0.185), (-0.245, 0.405), (-0.232, 0.418)] + arc + [(0.232, 0.418), (0.245, 0.405), (0.245, 0.185), (0.232, 0.170), (-0.232, 0.170)]
    plate = Q.prism('Cut_PlateOutline', outline, 0.6, br2, axis='Y', center=-0.25)
    Q.boolean(shell, plate, 'INTERSECT'); Q.apply_mods(shell)
    hole = Q.prism('Cut_PlateHole', Q.arch_outline(0.276, 0.193, 0.335, 14), 0.6, ref, axis='Y', center=-0.25)
    Q.boolean(shell, hole); Q.apply_mods(shell)
    for sx in (-1, 1):
        for i in range(3):
            x = sx * (0.189 + i * 0.019)
            for tgt in (shell, body):
                slot = Q.box(f'Cut_Slot{sx}{i}{tgt.name[-4:]}', (0.0085, 0.30, 0.12), (x, -0.40, 0.30), ref, bevel=0)
                Q.boolean(tgt, slot); Q.apply_mods(tgt)
    Q.weld(shell); P.append(shell)
    # short sill lip and grate
    for i in range(6):
        x = -0.10 + i * 0.04
        P.append(Q.cyl(f'Grate_{i}', 0.0075, 0.30, (x, -0.13, 0.212), iron, segs=8, rot=(math.pi / 2, 0, 0)))
    P.append(Q.box('Grate_Rail', (0.25, 0.012, 0.016), (0, -0.25, 0.205), iron, bevel=0.003))
    # coal bed
    import random
    rnd = random.Random(11)
    for i in range(15):
        x = rnd.uniform(-0.10, 0.10); y = rnd.uniform(-0.24, 0.02); s = rnd.uniform(0.018, 0.034)
        P.append(Q.rock(f'Coal_{i}', (s, s * 0.9, s * 0.7), (x, y, 0.225 + s * 0.4 + rnd.uniform(0, 0.012)), coal, seed=40 + i, subd=1, rough=0.5))
    # cast legs (4, diagonals) on stone pads
    leg_ol = [(0.300, 0.31), (0.338, 0.30), (0.362, 0.265), (0.372, 0.22), (0.368, 0.17), (0.356, 0.125), (0.352, 0.09), (0.362, 0.06), (0.392, 0.045),
              (0.404, 0.034), (0.318, 0.034), (0.322, 0.05), (0.316, 0.075), (0.310, 0.11), (0.312, 0.15), (0.306, 0.19), (0.290, 0.23), (0.270, 0.26), (0.262, 0.29)]
    for k, ang in enumerate((-142, -38, 38, 142)):
        a = math.radians(ang)
        leg = Q.prism(f'Furnace_Leg{k}', [(u, z) for u, z in leg_ol], 0.054, br, axis='Y')
        Q.add_bevel(leg, 0.012, 3, 25)
        # rotate the leg plane so its u axis points along the diagonal
        leg.rotation_euler = (0, 0, a)
        P.append(leg)
        cx, cy = 0.362 * math.cos(a), 0.362 * math.sin(a)
        boss = Q.cyl(f'Furnace_LegBoss{k}', 0.02, 0.016, (0.338 * math.cos(a), 0.338 * math.sin(a), 0.288), br2, segs=16, bevel=0.004,
                     rot=(math.pi / 2, 0, a + math.pi / 2))
        P.append(boss)
        pad = Q.cyl(f'Furnace_Pad{k}', 0.062, 0.036, (cx, cy, 0.018), stone, segs=20, bevel=0.008, bseg=3)
        Q.jitter(pad, 0.002, seed=k)
        for v in pad.data.vertices: v.co.z = max(v.co.z, -0.018)   # keep the pad soles flat on z = 0
        P.append(pad)
    # ring handles at +/-X
    for sx in (-1, 1):
        x = sx * 0.322
        P.append(Q.cyl(f'Handle_Boss{sx}', 0.042, 0.03, (sx * 0.300, 0, 0.535), br2, segs=24, bevel=0.006, rot=(0, math.pi / 2, 0)))
        P.append(Q.torus(f'Handle_Lug{sx}', 0.026, 0.008, (sx * 0.334, 0, 0.537), br2, 20, 8, rot=(math.pi / 2, 0, 0)))
        P.append(Q.torus(f'Handle_Ring{sx}', 0.068, 0.0125, (sx * 0.338, 0, 0.47), br2, 30, 9, rot=(math.radians(90), 0, math.pi / 2 + sx * math.radians(12))))
    # flue pipe at the back
    pipe = Q.lathe('Flue_Pipe', [(0, 0.55), (0.054, 0.55), (0.054, 0.852), (0.064, 0.858), (0.066, 0.878), (0.062, 0.892), (0.044, 0.892), (0.044, 0.80), (0, 0.80)], soot, segs=32)
    pipe.location = (0, 0.335, 0); P.append(pipe)
    P.append(Q.torus('Flue_Strap', 0.059, 0.008, (0, 0.335, 0.70), br2, 32, 8))
    strap = Q.box('Flue_StrapPlate', (0.085, 0.09, 0.06), (0, 0.27, 0.70), br2, bevel=0.008, bseg=3); P.append(strap)
    P.append(Q.cyl('Flue_Collar', 0.068, 0.03, (0, 0.335, 0.62), br2, segs=32, bevel=0.006))
    Q.finalize_parts(P, 101)
    info = dict(states={'cold': 'firebox dark, coal grey', 'heating': 'coal and lining glow (emissive map)'},
                sockets={'lid_seat': [0, 0, LID_SEAT_Z], 'flue_outlet': [0, 0.335, 0.892], 'mouth_center': [0, -0.31, 0.30]},
                rim={'top_z': RIM_TOP, 'inner_r': RIM_IN})
    return P, info


# ============================================================================ B02 removable lid
LID_PROF = [(0, 0.028), (0.170, 0.026), (0.188, 0.018), (0.194, 0.004), (0.199, 0.0), (0.202, 0.0), (0.202, 0.040),
            (0.266, 0.040), (0.272, 0.044), (0.272, 0.058), (0.266, 0.063), (0.250, 0.064), (0.245, 0.070), (0.245, 0.082),
            (0.236, 0.087), (0.214, 0.096), (0.182, 0.110), (0.145, 0.121), (0.108, 0.129), (0.100, 0.134), (0.098, 0.141),
            (0.090, 0.145), (0.088, 0.152), (0.070, 0.158), (0.035, 0.162), (0, 0.163)]


@asset('B02', 'FurnaceLid', states=('default',), res=1024, budget=6500, size=(0.54, 0.54, 0.27),
       collision={'type': 'cylinder', 'radius': 0.27, 'height': 0.16, 'center': [0, 0, 0.08], 'note': 'pick-up / place target; seat on B01 socket lid_seat'})
def b02(state='default'):
    br = Q.m_bronze('B02_Bronze', patina=0.45, polish=0.7)
    br2 = Q.m_bronze('B02_Fittings', patina=0.3, polish=0.85)
    wood = Q.m_wood('B02_Grip', a=(0.025, 0.022, 0.02), b_=(0.06, 0.05, 0.045), axis='Z', ring=12, wear=0.3, rough=0.45)
    P = []
    lid = Q.lathe('Lid_Body', LID_PROF, br, segs=72, sharp=34)
    for i in range(6):
        a = TAU * i / 6 + math.pi / 6
        n = Q.box(f'Cut_Notch{i}', (0.06, 0.026, 0.020), (0.202 * math.cos(a), 0.202 * math.sin(a), 0.004), br, bevel=0, rot=(0, 0, a + math.pi / 2))
        Q.boolean(lid, n); Q.apply_mods(lid)
    P.append(lid)
    # bail handle: hinge lugs, bronze rod, dark wood grip with ferrules
    for sx in (-1, 1):
        lug = Q.box(f'Lid_Lug{sx}', (0.016, 0.034, 0.05), (sx * 0.172, 0, 0.128), br2, bevel=0.006, bseg=3)
        P.append(lug)
        P.append(Q.cyl(f'Lid_Pin{sx}', 0.011, 0.03, (sx * 0.172, 0, 0.142), br2, segs=16, bevel=0.003, rot=(0, math.pi / 2, 0)))
    pts = [(-0.172, 0, 0.142), (-0.172, 0, 0.19), (-0.15, 0, 0.236), (-0.10, 0, 0.255), (0.10, 0, 0.255), (0.15, 0, 0.236), (0.172, 0, 0.19), (0.172, 0, 0.142)]
    P.append(Q.tube('Lid_Bail', [Vector(p) for p in pts], 0.0085, br2, segs=12, res=10))
    P.append(Q.cyl('Lid_Grip', 0.020, 0.13, (0, 0, 0.255), wood, segs=20, bevel=0.006, bseg=3, rot=(0, math.pi / 2, 0)))
    for sx in (-1, 1):
        P.append(Q.cyl(f'Lid_Ferrule{sx}', 0.023, 0.014, (sx * 0.072, 0, 0.255), br2, segs=20, bevel=0.003, rot=(0, math.pi / 2, 0)))
    # vent spout at back-right
    a = math.radians(60); r = 0.165
    sp = Q.lathe('Lid_Vent', [(0, -0.01), (0.024, -0.01), (0.024, 0.045), (0.028, 0.05), (0.028, 0.062), (0.0, 0.064)], br2, segs=24)
    sp.location = (r * math.cos(a), r * math.sin(a), 0.112); sp.rotation_euler = (math.radians(-26), 0, a - math.pi / 2)
    P.append(sp)
    Q.finalize_parts(P, 202)
    info = dict(states={'closed': f'seated on B01 at z={LID_SEAT_Z:.3f}', 'open': 'lifted / set beside the furnace'},
                sockets={'grip': [0, 0, 0.255], 'seat_underside_z': 0.040})
    return P, info


import qa_assets1  # noqa: E402,F401  (registers B03-B06)
import qa_assets2  # noqa: E402,F401  (registers B07-B12)
