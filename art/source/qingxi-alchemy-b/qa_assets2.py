"""Batch 2 builders: B07 fuel box, B08 drying basket, B09 filter frame, B10 medicine bottle, B11 recipe stand, B12 chimney."""
import math, random
import bmesh
from mathutils import Vector, Matrix
import qa_lib as Q
from qa_assets import asset

TAU = math.tau


def log(name, r, length, loc, rot, bark, split, end, sector=360, segs=12):
    """Split firewood along local Z: bark on the arc, split face on the cut planes, end grain on the caps."""
    n = max(4, int(segs * sector / 360))
    arc = [(r * math.cos(math.radians(sector) * i / n - math.radians(sector) / 2), r * math.sin(math.radians(sector) * i / n - math.radians(sector) / 2))
           for i in range(n + (0 if sector >= 360 else 1))]
    out = arc if sector >= 360 else [(0.0, 0.0)] + arc
    o = Q.prism(name, out, length, bark, axis='Z', sharp=50)
    me = o.data; me.materials.append(split); me.materials.append(end)
    for p in me.polygons:
        if abs(p.normal.z) > 0.9: p.material_index = 2
        elif sector < 360 and any(math.hypot(*me.vertices[i].co.xy) < 1e-5 for i in p.vertices): p.material_index = 1
    Q.jitter(o, r * 0.04, seed=hash(name) % 997)
    o.location = loc; o.rotation_euler = rot
    return o


# ============================================================================ B07 wooden fuel box
@asset('B07', 'WoodenFuelBox', res=1024, budget=5200, size=(0.68, 0.42, 0.46),
       collision={'type': 'box', 'size': [0.68, 0.42, 0.46], 'center': [0, 0, 0.23], 'note': 'fuel refill point; no paid speed-up'})
def b07(state='default'):
    wd = Q.m_wood('B07_OldPine', a=(0.075, 0.045, 0.026), b_=(0.15, 0.095, 0.055), axis='X', ring=4.0, wear=0.7)
    wdv = Q.m_wood('B07_OldPineV', a=(0.075, 0.045, 0.026), b_=(0.15, 0.095, 0.055), axis='Z', ring=4.0, wear=0.7)
    wdy = Q.m_wood('B07_OldPineY', a=(0.075, 0.045, 0.026), b_=(0.15, 0.095, 0.055), axis='Y', ring=4.0, wear=0.7)
    iron = Q.m_iron('B07_Iron', rust=0.55)
    bark = Q.m_bark('B07_Bark'); split = Q.m_wood('B07_Split', a=(0.30, 0.20, 0.11), b_=(0.45, 0.32, 0.18), axis='Z', ring=6, wear=0.2)
    end = Q.m_endgrain('B07_EndGrain')
    P = []
    W, D = 0.68, 0.42; z0 = 0.04; px, py = W / 2 - 0.025, D / 2 - 0.025
    ztop_f, ztop_b = 0.275, 0.43
    for sx in (-1, 1):
        for sy in (-1, 1):
            P.append(Q.box(f'Post_{sx}{sy}', (0.05, 0.05, 0.42), (sx * px, sy * py, z0 + 0.21), wdv, bevel=0.006, bseg=2))
            P.append(Q.box(f'Foot_{sx}{sy}', (0.085, 0.07, 0.04), (sx * 0.25, sy * 0.13, 0.02), wd, bevel=0.006))
    for i in range(3):
        P.append(Q.box(f'FrontPlank{i}', (W - 0.09, 0.022, 0.074), (0, -D / 2 + 0.02, z0 + 0.04 + i * 0.076), wd, bevel=0.004))
    for i in range(5):
        P.append(Q.box(f'BackPlank{i}', (W - 0.09, 0.022, 0.074), (0, D / 2 - 0.02, z0 + 0.04 + i * 0.076), wd, bevel=0.004))
    y0, y1 = -D / 2 + 0.04, D / 2 - 0.04
    slope = lambda y: ztop_f + (y - y0) / (y1 - y0) * (ztop_b - ztop_f)
    for sx in (-1, 1):
        for i in range(5):
            zb, zt = z0 + 0.004 + i * 0.076, z0 + 0.004 + i * 0.076 + 0.074
            if zb >= slope(y1) - 0.01: continue
            if zt <= slope(y0): pts = [(y0, zb), (y1, zb), (y1, zt), (y0, zt)]
            else:
                ys = y0 + (zt - ztop_f) / (ztop_b - ztop_f) * (y1 - y0)
                if zb < slope(y0): pts = [(y0, zb), (y1, zb), (y1, min(zt, slope(y1)))] + ([(ys, zt)] if ys < y1 else []) + [(y0, slope(y0))]
                else:
                    yb = y0 + (zb - ztop_f) / (ztop_b - ztop_f) * (y1 - y0)
                    pts = [(yb, zb), (y1, zb), (y1, min(zt, slope(y1)))] + ([(ys, zt)] if ys < y1 else [])
            pl = Q.prism(f'SidePlank{sx}{i}', pts, 0.022, wdy, axis='X', center=sx * (W / 2 - 0.02))
            Q.add_bevel(pl, 0.004, 1, 40); P.append(pl)
        hole = Q.prism(f'Cut_Grip{sx}', [(0.045 * math.cos(t) + 0.04, 0.016 * math.sin(t) + 0.335) for t in [TAU * k / 16 for k in range(16)]], 0.08, wdy, axis='X', center=sx * (W / 2 - 0.02))
        for o in [o for o in P if o.name.startswith(f'SidePlank{sx}')]:
            Q.boolean(o, hole)
    P.append(Q.box('Bottom', (W - 0.06, D - 0.06, 0.016), (0, 0, z0 + 0.008), wd, bevel=0.0))
    # iron corner plates with rivets
    for sx in (-1, 1):
        for sy in (-1, 1):
            for zc in ((z0 + 0.05, ztop_f - 0.035) if sy < 0 else (z0 + 0.05, ztop_b - 0.04)):
                P.append(Q.box(f'IronF_{sx}{sy}{zc:.2f}', (0.085, 0.004, 0.05), (sx * (W / 2 - 0.035), sy * (D / 2 + 0.002), zc), iron, bevel=0.0015, bseg=1))
                P.append(Q.box(f'IronS_{sx}{sy}{zc:.2f}', (0.004, 0.07, 0.05), (sx * (W / 2 + 0.002), sy * (D / 2 - 0.03), zc), iron, bevel=0.0015, bseg=1))
                for k in (-1, 1):
                    P.append(Q.cyl(f'Rivet_{sx}{sy}{zc:.2f}{k}', 0.0055, 0.004, (sx * (W / 2 - 0.035) + k * 0.025, sy * (D / 2 + 0.004), zc), iron, segs=8, bevel=0.0015, bseg=1, rot=(math.pi / 2, 0, 0)))
    # firewood
    rnd = random.Random(7); L = D - 0.10
    spots = [(-0.21, 0.105, 0.05), (-0.105, 0.10, 0.048), (0.0, 0.105, 0.05), (0.105, 0.10, 0.047), (0.21, 0.104, 0.049),
             (-0.16, 0.19, 0.045), (-0.05, 0.195, 0.05), (0.06, 0.19, 0.046), (0.17, 0.192, 0.048), (-0.20, 0.275, 0.044), (-0.10, 0.27, 0.045), (0.0, 0.272, 0.047), (0.10, 0.275, 0.05), (0.205, 0.27, 0.045),
             (-0.15, 0.352, 0.044), (-0.05, 0.356, 0.046), (0.055, 0.352, 0.045), (0.155, 0.35, 0.043)]
    for i, (x, z, r) in enumerate(spots):
        sector = 360 if i % 3 == 0 else (180 if i % 3 == 1 else 110)
        P.append(log(f'Log{i}', r, L - rnd.uniform(0, 0.04), (x, rnd.uniform(-0.01, 0.01), z), (math.pi / 2, rnd.uniform(-0.05, 0.05), rnd.uniform(0, TAU) * 0 + rnd.uniform(-0.8, 0.8)),
                     bark, split, end, sector=sector))
    Q.finalize_parts(P, 707)
    return P, dict(states={'default': 'full of split firewood'}, sockets={'take_point': [0, -0.25, 0.30]})


# ============================================================================ B08 ventilated drying basket
@asset('B08', 'VentilatedDryingBasket', res=2048, budget=9000, size=(0.74, 0.64, 0.21),
       collision={'type': 'cylinder', 'radius': 0.32, 'height': 0.16, 'center': [0, 0, 0.08], 'note': 'open-weave floor and wall use alpha clip'})
def b08(state='default'):
    bam = Q.m_bamboo('B08_Bamboo', a=(0.26, 0.18, 0.08), b_=(0.40, 0.29, 0.13), axis='Z')
    bamx = Q.m_bamboo('B08_BambooHoop', a=(0.26, 0.18, 0.08), b_=(0.40, 0.29, 0.13), axis='X')
    floor_m = Q.m_weave('B08_FloorWeave', pitch=0.016, open_=0.36, a=(0.24, 0.16, 0.07), b_=(0.40, 0.29, 0.13), mode='flat')
    wall_m = Q.m_weave('B08_WallWeave', pitch=0.016, open_=0.36, a=(0.24, 0.16, 0.07), b_=(0.40, 0.29, 0.13), mode='wall', radius=0.29)
    cord = Q.m_cord('B08_SageCord')
    P = []
    P.append(Q.cyl('Floor', 0.274, 0.004, (0, 0, 0.056), floor_m, segs=48))
    ring = [(0.272, 0.054), (0.313, 0.152), (0.310, 0.153), (0.269, 0.055), (0.272, 0.054)]
    P.append(Q.lathe('Wall', ring, wall_m, segs=64, sharp=60))
    P.append(Q.torus('RimOuter', 0.316, 0.011, (0, 0, 0.156), bamx, 56, 8))
    P.append(Q.torus('RimInner', 0.302, 0.009, (0, 0, 0.152), bamx, 48, 6))
    P.append(Q.torus('BaseBand', 0.275, 0.0085, (0, 0, 0.058), bamx, 48, 6))
    phi = math.atan2(0.041, 0.098); L = math.hypot(0.041, 0.098) + 0.01
    for k in range(8):
        th = TAU * k / 8 + TAU / 16
        rr, zz = 0.296, 0.104
        rib = Q.box(f'Rib{k}', (0.006, 0.017, L), (rr * math.cos(th), rr * math.sin(th), zz), bam, bevel=0.002, bseg=1, rot=(0, phi, th))
        P.append(rib)
        for j, (R_, z_) in enumerate(((0.318, 0.156), (0.277, 0.058))):
            for w in (-1, 0, 1):
                t = th + w * 0.024
                P.append(Q.torus(f'Bind{k}{j}{w}', 0.0145 if j == 0 else 0.012, 0.0024, (R_ * math.cos(t), R_ * math.sin(t), z_), cord, 8, 4, rot=(math.pi / 2, 0, t)))
    for sx in (-1, 1):
        pts = [Vector((sx * 0.312, -0.065, 0.158)), Vector((sx * 0.340, -0.055, 0.188)), Vector((sx * 0.356, 0, 0.202)), Vector((sx * 0.340, 0.055, 0.188)), Vector((sx * 0.312, 0.065, 0.158))]
        P.append(Q.tube(f'Handle{sx}', pts, 0.0085, bamx, segs=10, res=8))
        for yy in (-0.06, 0.06):
            for w in (-1, 0, 1):
                P.append(Q.torus(f'HandleBind{sx}{yy}{w}', 0.0135, 0.0022, (sx * 0.316, yy + w * 0.005, 0.161), cord, 8, 4, rot=(math.pi / 2, 0, 0)))
    for k in range(4):
        th = TAU * k / 4 + TAU / 8
        P.append(Q.pole(f'Foot{k}', (0.19 * math.cos(th), 0.19 * math.sin(th), 0.0), (0.19 * math.cos(th), 0.19 * math.sin(th), 0.054), 0.017, bam, segs=12, node_every=0.5))
        P.append(Q.torus(f'FootBind{k}', 0.0185, 0.0022, (0.19 * math.cos(th), 0.19 * math.sin(th), 0.046), cord, 14, 5))
    Q.finalize_parts(P, 808)
    return P, dict(states={'default': 'empty; open weave lets air through (alpha clip)'}, sockets={'herb_surface': [0, 0, 0.062]})


# ============================================================================ B09 cloth filtration frame
@asset('B09', 'ClothFilterFrame', res=1024, budget=7000, size=(0.60, 0.42, 0.92),
       collision={'type': 'box', 'size': [0.56, 0.42, 0.92], 'center': [0, 0, 0.46], 'note': 'coarse batch poured into the cloth, refined liquid collects in the bowl'})
def b09(state='default'):
    wd = Q.m_wood('B09_Wood', axis='X'); wdv = Q.m_wood('B09_WoodV', axis='Z'); wdy = Q.m_wood('B09_WoodY', axis='Y')
    br = Q.m_bronze('B09_Bronze', patina=0.6, polish=0.6)
    cloth = Q.m_cloth('B09_Linen', base=(0.43, 0.39, 0.31), stain=(0.25, 0.16, 0.07), stain_axis_z=(0.47, 0.63))
    cel = Q.m_celadon('B09_Bowl', g1=(0.10, 0.15, 0.12), g2=(0.18, 0.23, 0.19), glaze_rough=0.28)
    liq = Q.m_simple('B09_Filtrate', (0.16, 0.10, 0.03), (0.22, 0.14, 0.04), rough=0.08, nscale=3)
    cord = Q.m_cord('B09_Cord', (0.55, 0.50, 0.40), (0.68, 0.63, 0.52))
    P = []
    for sx in (-1, 1):
        P.append(Q.box(f'Skid{sx}', (0.07, 0.42, 0.06), (sx * 0.22, 0, 0.03), wdy, bevel=0.008, bseg=2))
        P.append(Q.box(f'Post{sx}', (0.045, 0.045, 0.85), (sx * 0.22, 0, 0.06 + 0.425), wdv, bevel=0.005, bseg=2))
        P.append(Q.box(f'PostCap{sx}', (0.054, 0.054, 0.024), (sx * 0.22, 0, 0.91 + 0.012), br, bevel=0.005))
        for sy in (-1, 1):
            a = Vector((sx * 0.22, sy * 0.17, 0.06)); b = Vector((sx * 0.22, sy * 0.022, 0.31)); d = b - a; mid = (a + b) / 2
            br_ = Q.box(f'Brace{sx}{sy}', (0.034, 0.03, d.length), mid, wdv, bevel=0.004)
            br_.rotation_euler = (math.atan2(-d.y, d.z), 0, 0); P.append(br_)
            P.append(Q.box(f'Collar{sx}{sy}', (0.05, 0.006, 0.05), (sx * 0.22, sy * 0.0255, 0.632), br, bevel=0.002))
    for sy in (-1, 1):
        P.append(Q.box(f'Bearer{sy}', (0.50, 0.05, 0.045), (0, sy * 0.12, 0.06 + 0.0225), wd, bevel=0.005))
    P.append(Q.box('BaseBoard', (0.40, 0.34, 0.024), (0, 0, 0.105 + 0.012), wd, bevel=0.004))
    P.append(Q.rod('TopRod', (-0.275, 0, 0.875), (0.275, 0, 0.875), 0.016, wd, segs=14, bevel=0.003))
    for sx in (-1, 1):
        P.append(Q.lathe(f'RodKnob{sx}', [(0, -0.022), (0.016, -0.019), (0.022, -0.006), (0.022, 0.006), (0.016, 0.019), (0, 0.022)], wd, segs=16))
        P[-1].location = (sx * 0.29, 0, 0.875)
    # square cloth frame (rails along X pass the posts' faces; short rails along Y)
    zf = 0.62
    for sy in (-1, 1):
        P.append(Q.box(f'FrameX{sy}', (0.47, 0.022, 0.022), (0, sy * 0.145, zf), wd, bevel=0.003))
    for sx in (-1, 1):
        P.append(Q.box(f'FrameY{sx}', (0.022, 0.312, 0.022), (sx * 0.197, 0, zf), wdy, bevel=0.003))
        for sy in (-1, 1):
            P.append(Q.cyl(f'FrameStud{sx}{sy}', 0.008, 0.006, (sx * 0.197, sy * 0.145, zf + 0.012), br, segs=10, bevel=0.002))
    # linen cone: hangs from the inner edge of the frame to a tied tip above the bowl
    a, b, ztop, tip = 0.183, 0.131, zf + 0.009, Vector((0, 0, 0.345))
    U, V = 44, 12
    def perim(u):
        t = u * 4.0; k = int(t) % 4; f = t - int(t)
        c = [(-a, -b), (a, -b), (a, b), (-a, b)]
        p0, p1 = c[k], c[(k + 1) % 4]
        return Vector((p0[0] + (p1[0] - p0[0]) * f, p0[1] + (p1[1] - p0[1]) * f, 0))
    bm = bmesh.new(); grid = []
    for j in range(V + 1):
        v = j / V; row = []
        for i in range(U):
            p = perim(i / U); rad = Vector((p.x, p.y, 0)); sag = math.sin(math.pi * v) * 0.028 * (1 - v * 0.4)
            q = p * (1 - v) ** 0.85 + rad.normalized() * sag * (0.6 + 0.4 * math.sin(i / U * TAU * 4 + 1.3))
            z = ztop - (ztop - tip.z) * v ** 1.15
            row.append(bm.verts.new((q.x, q.y, z)))
        grid.append(row)
    for j in range(V):
        for i in range(U):
            bm.faces.new((grid[j][i], grid[j][(i + 1) % U], grid[j + 1][(i + 1) % U], grid[j + 1][i]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    cone = Q._obj('FilterCloth', bm, cloth, sharp=80)
    so = cone.modifiers.new('Solid', 'SOLIDIFY'); so.thickness = 0.0025
    P.append(cone)
    for sx in (-1, 1):
        for sy in (-1, 1):
            P.append(Q.lathe(f'CornerKnot{sx}{sy}', [(0, -0.009), (0.008, -0.006), (0.009, 0.0), (0.008, 0.006), (0, 0.009)], cord, segs=10))
            P[-1].location = (sx * 0.192, sy * 0.140, zf + 0.016)
            P.append(Q.tube(f'Tie{sx}{sy}', [Vector((sx * 0.192, sy * 0.140, zf + 0.02)), Vector((sx * 0.15, sy * 0.06, 0.78)), Vector((sx * 0.11, 0, 0.862))], 0.0028, cord, segs=6, res=6))
    P.append(Q.lathe('TipKnot', [(0, 0.322), (0.010, 0.326), (0.013, 0.336), (0.010, 0.347), (0, 0.352)], cord, segs=12))
    # bowl with filtrate
    bowl = [(0, 0.129), (0.05, 0.129), (0.055, 0.135), (0.062, 0.136), (0.098, 0.16), (0.122, 0.192), (0.128, 0.207), (0.124, 0.209), (0.116, 0.200),
            (0.092, 0.168), (0.05, 0.146), (0, 0.143)]
    P.append(Q.lathe('Bowl', bowl, cel, segs=40))
    P.append(Q.lathe('Filtrate', [(0, 0.172), (0.104, 0.172), (0, 0.1721)], liq, segs=32))
    Q.finalize_parts(P, 909)
    return P, dict(states={'default': 'cloth stained toward the tip; refined filtrate in the bowl'}, sockets={'pour_point': [0, 0, 0.66], 'collect_point': [0, 0, 0.18]})


# ============================================================================ B10 wax-sealed medicine bottle
GLASS = [(0, 0), (0.030, 0), (0.0355, 0.002), (0.0375, 0.008), (0.0375, 0.066), (0.0355, 0.075), (0.028, 0.083), (0.018, 0.089), (0.0125, 0.092),
         (0.0118, 0.100), (0.0138, 0.102), (0.0142, 0.107), (0.0125, 0.109), (0.0098, 0.108), (0.0095, 0.100), (0.0098, 0.092), (0.016, 0.087),
         (0.026, 0.081), (0.0335, 0.073), (0.0352, 0.066), (0.0352, 0.009), (0.032, 0.0045), (0, 0.004)]
SQUARE = lambda r: 2.0 + 2.6 * max(0.0, min(1.0, (r - 0.015) / 0.012))


@asset('B10', 'WaxSealedBottle', states=('filled', 'empty'), res=512, budget=3200, size=(0.075, 0.075, 0.12),
       collision={'type': 'box', 'size': [0.075, 0.075, 0.115], 'center': [0, 0, 0.058], 'note': 'finished product container; empty bottle has its cork as node Cork'})
def b10(state='filled'):
    glass = Q.m_glass('B10_Glass', color=(0.05, 0.085, 0.075), alpha=0.32, rough=0.03)
    liquid = Q.m_glass('B10_Tonic', color=(0.40, 0.11, 0.008), alpha=1.0, rough=0.15)
    lb = liquid.node_tree.nodes['Principled BSDF']  # faint inner glow keeps the tonic amber behind the tinted glass
    lb.inputs['Emission Color'].default_value = (0.9, 0.38, 0.05, 1); lb.inputs['Emission Strength'].default_value = 0.12
    cork = Q.m_simple('B10_Cork', (0.33, 0.22, 0.12), (0.47, 0.33, 0.18), rough=0.85, nscale=90, bump=0.0004, cav_col=(0.15, 0.09, 0.05))
    wax = Q.m_simple('B10_Wax', (0.30, 0.018, 0.012), (0.46, 0.04, 0.025), rough=0.32, nscale=20, edge_col=(0.6, 0.12, 0.08))
    paper = Q.m_simple('B10_Label', (0.56, 0.50, 0.38), (0.66, 0.60, 0.47), rough=0.92, nscale=40, edge_col=(0.40, 0.33, 0.22))
    twine = Q.m_cord('B10_Twine', (0.40, 0.31, 0.17), (0.55, 0.44, 0.26))
    P = [Q.superlathe('Bottle_Glass', GLASS[:15], glass, segs=32, n_of_r=SQUARE)]  # single shell: one blended layer over the tonic
    lab = Q.box('Bottle_Label', (0.042, 0.0006, 0.030), (0, -0.0379, 0.040), paper, bevel=0.0); P.append(lab)
    c = Q.lathe('Cork', [(0, 0.0), (0.0090, 0.0), (0.0092, 0.012), (0.0118, 0.015), (0.0120, 0.019), (0.0105, 0.0205), (0, 0.021)], cork, segs=16)
    if state == 'filled':
        P.append(Q.superlathe('Tonic', [(0, 0.0048), (0.0312, 0.0048), (0.0346, 0.008), (0.0346, 0.062), (0, 0.062)], liquid, segs=32, n_of_r=SQUARE))
        c.location = (0, 0, 0.096); P.append(c)
        w = Q.lathe('Wax_Cap', [(0, 0.1195), (0.009, 0.119), (0.0142, 0.1155), (0.0158, 0.109), (0.0156, 0.1035), (0.0149, 0.1012), (0.0143, 0.1012),
                                (0.0148, 0.104), (0.0149, 0.109), (0.0134, 0.1145), (0.009, 0.1172), (0, 0.1176)], wax, segs=24)
        rnd = random.Random(10)
        for v in w.data.vertices:
            if v.co.z < 0.1045:
                th = math.atan2(v.co.y, v.co.x); v.co.z -= 0.0035 * max(0, math.sin(th * 3 + 0.7)) ** 3 + rnd.uniform(0, 0.0006)
        P.append(w)
        for k, th in enumerate((0.6, 2.4, 4.3)):
            a = Vector((0.0149 * math.cos(th), 0.0149 * math.sin(th), 0.102)); b = Vector((0.0132 * math.cos(th), 0.0132 * math.sin(th), 0.0955 - k * 0.0012))
            P.append(Q.tube(f'Wax_Drip{k}', [a, (a + b) / 2 + Vector((0.0004 * math.cos(th), 0.0004 * math.sin(th), 0)), b], 0.0016, wax, segs=8, res=4, taper=[1.0, 0.9, 0.55]))
        P.append(Q.torus('Twine_Wrap', 0.0131, 0.0011, (0, 0, 0.0945), twine, 24, 6))
        P.append(Q.lathe('Twine_Knot', [(0, -0.0024), (0.002, -0.0018), (0.0026, 0), (0.002, 0.0018), (0, 0.0024)], twine, segs=8))
        P[-1].location = (0.0095, -0.0098, 0.0945)
        for k, (dx, dy) in enumerate(((0.012, -0.022), (0.004, -0.026))):
            P.append(Q.tube(f'Twine_Tail{k}', [Vector((0.0098, -0.0102, 0.0942)), Vector((0.0098 + dx * 0.5, -0.0102 + dy * 0.4, 0.0885)), Vector((0.0098 + dx, -0.0102 + dy * 0.85, 0.077))], 0.0009, twine, segs=6, res=5))
    else:
        c.location = (0.052, -0.004, 0.0118); c.rotation_euler = (0, math.pi / 2, 0.35)
        Q.tag_node([c], 'Cork'); P.append(c)
    Q.finalize_parts(P, 1010)
    return P, dict(states={'filled': 'corked, wax-sealed, twine tied, tonic 80 percent', 'empty': 'open and dry, cork lying beside it'},
                   sockets={'grip': [0, 0, 0.05]})


# ============================================================================ B11 bamboo recipe stand
@asset('B11', 'BambooRecipeStand', res=1024, budget=4200, size=(0.58, 0.36, 0.47),
       collision={'type': 'box', 'size': [0.58, 0.36, 0.47], 'center': [0, 0, 0.235], 'note': 'in-world recipe entry; sits on the B05 cabinet top'})
def b11(state='default'):
    wd = Q.m_wood('B11_Walnut', axis='Z'); wdx = Q.m_wood('B11_WalnutX', axis='X'); wdy = Q.m_wood('B11_WalnutY', axis='Y')
    slips = Q.m_slips('B11_Slips'); cord = Q.m_cord('B11_Cord', (0.10, 0.06, 0.03), (0.19, 0.12, 0.06))
    br = Q.m_bronze('B11_Bronze', patina=0.65, polish=0.6)
    ink = Q.m_celadon('B11_InkPot', g1=(0.10, 0.16, 0.13), g2=(0.18, 0.24, 0.20), glaze_rough=0.25)
    P = []
    th_f = math.atan2(0.19, 0.42); th_b = math.atan2(0.07, 0.38)
    for sx in (-1, 1):
        x = sx * 0.255
        P.append(Q.box(f'Runner{sx}', (0.042, 0.36, 0.034), (x, 0.0, 0.017), wdy, bevel=0.012, bseg=3))
        f = Q.box(f'FrontLeg{sx}', (0.036, 0.03, 0.462), (x, -0.025, 0.24), wd, bevel=0.005, bseg=2); f.rotation_euler = (-th_f, 0, 0); P.append(f)
        b = Q.box(f'BackLeg{sx}', (0.034, 0.028, 0.388), (x, 0.115, 0.222), wd, bevel=0.005, bseg=2); b.rotation_euler = (th_b, 0, 0); P.append(b)
        P.append(Q.cyl(f'Knob{sx}', 0.021, 0.014, (sx * 0.279, 0.062, 0.430), br, segs=18, bevel=0.004, rot=(0, math.pi / 2, 0)))
        P.append(Q.cyl(f'KnobLow{sx}', 0.015, 0.012, (sx * 0.278, -0.065, 0.16), br, segs=16, bevel=0.003, rot=(0, math.pi / 2, 0)))
    P.append(Q.box('BackRail', (0.47, 0.026, 0.03), (0, 0.128, 0.14), wdx, bevel=0.004))
    P.append(Q.box('Ledge', (0.50, 0.072, 0.016), (0, -0.104, 0.10), wdx, bevel=0.004))
    P.append(Q.box('LedgeLip', (0.50, 0.012, 0.03), (0, -0.138, 0.112), wdx, bevel=0.003))
    u = Vector((0, math.sin(th_f), math.cos(th_f))); n = Vector((0, -math.cos(th_f), math.sin(th_f)))
    c = Vector((0, -0.12, 0.03)) + Vector((0, 0.19, 0.42)) * 0.585 + n * 0.022
    for i in range(17):
        x = -0.22 + i * 0.0275
        s = Q.box(f'Slip{i}', (0.025, 0.006, 0.33), c + Vector((x, 0, 0)), slips, bevel=0.0015, bseg=1); s.rotation_euler = (-th_f, 0, 0); P.append(s)
    for k, off in enumerate((0.168, -0.168)):
        bar = Q.box(f'SlipBar{k}', (0.50, 0.026, 0.024), c + u * off + n * 0.002, wdx, bevel=0.005); bar.rotation_euler = (-th_f, 0, 0); P.append(bar)
    for k, off in enumerate((0.105, -0.105)):
        p = c + u * off + n * 0.0045
        P.append(Q.rod(f'Lash{k}', p + Vector((-0.243, 0, 0)), p + Vector((0.243, 0, 0)), 0.0034, cord, segs=8))
        for sx in (-1, 1):
            P.append(Q.cyl(f'LashCap{k}{sx}', 0.007, 0.01, p + Vector((sx * 0.245, 0, 0)), br, segs=12, bevel=0.002, rot=(0, math.pi / 2, 0)))
    pot = Q.lathe('InkPot', [(0, 0), (0.020, 0), (0.027, 0.008), (0.030, 0.017), (0.027, 0.026), (0.016, 0.031), (0.009, 0.033), (0.009, 0.036),
                             (0.013, 0.037), (0.013, 0.040), (0.004, 0.044), (0, 0.045)], ink, segs=24)
    pot.location = (0.17, -0.102, 0.108); P.append(pot)
    Q.finalize_parts(P, 1111)
    return P, dict(states={'default': 'seventeen slips with brushed herb sprigs (no readable text)'}, sockets={'read_focus': [0, -0.02, 0.29]})


# ============================================================================ B12 short workshop chimney
@asset('B12', 'WorkshopChimney', res=1024, budget=6500, size=(0.80, 0.78, 1.92),
       collision={'type': 'box', 'size': [0.74, 0.74, 1.92], 'center': [0, 0, 0.96], 'note': 'flue inlet socket on +X at z 0.98'})
def b12(state='default'):
    st = Q.m_stone('B12_Limestone', light=(0.20, 0.186, 0.162), dark=(0.13, 0.122, 0.106), scale=1.0, speck=0.5, soot=0.7, soot_z=(0.95, 1.6), chisel=3.0)
    mortar = Q.m_simple('B12_Mortar', (0.12, 0.11, 0.10), (0.17, 0.16, 0.14), rough=0.95, nscale=30)
    iron = Q.m_iron('B12_Iron', rust=0.5); br = Q.m_bronze('B12_Bronze', patina=0.6, polish=0.6)
    roof = Q.m_bronze('B12_RoofPatina', patina=1.0, polish=0.45)
    sootm = Q.m_bronze('B12_Flue', patina=0.1, polish=0.2, soot=0.9)
    P = []; rnd = random.Random(12); gap = 0.006
    def course(z0, h, half, axis, split, tag):
        for side in (-1, 1):
            if axis == 'X':
                x0, x1 = (-half, split) if side < 0 else (split, half); sx, sy = x1 - x0 - gap, 2 * half - gap; cx, cy = (x0 + x1) / 2, 0
            else:
                y0, y1 = (-half, split) if side < 0 else (split, half); sx, sy = 2 * half - gap, y1 - y0 - gap; cx, cy = 0, (y0 + y1) / 2
            o = Q.box(f'Block_{tag}{side}', (sx, sy, h - gap), (cx, cy, z0 + h / 2), st, bevel=0.014, bseg=1)
            Q.apply_mods(o); Q.jitter(o, 0.0025, seed=rnd.randint(0, 999)); P.append(o)
    course(0.0, 0.13, 0.37, 'X', 0.05, 'P0'); course(0.13, 0.13, 0.35, 'Y', -0.06, 'P1')
    P.append(Q.box('Core_Plinth', (0.69, 0.69, 0.25), (0, 0, 0.125), mortar, bevel=0))
    z = 0.26
    for i, h in enumerate((0.22, 0.20, 0.23, 0.21, 0.22, 0.14)):
        course(z, h, 0.27, 'X' if i % 2 == 0 else 'Y', (0.07, -0.09, 0.05, -0.06, 0.09, -0.04)[i], f'S{i}'); z += h
    P.append(Q.box('Core_Shaft', (0.53, 0.53, z - 0.26), (0, 0, (z + 0.26) / 2), mortar, bevel=0))
    P.append(Q.box('CapSlab', (0.64, 0.64, 0.065), (0, 0, z + 0.0325), st, bevel=0.012, bseg=2))
    P.append(Q.box('CapSlab2', (0.58, 0.58, 0.04), (0, 0, z + 0.085), st, bevel=0.01, bseg=2))
    zt = z + 0.105
    flue = Q.lathe('FlueStack', [(0.11, zt - 0.01), (0.12, zt - 0.01), (0.12, zt + 0.16), (0.10, zt + 0.16), (0.10, zt - 0.2), (0.11, zt - 0.2)], sootm, segs=24)
    P.append(flue)
    for sx in (-1, 1):
        for sy in (-1, 1):
            P.append(Q.box(f'CapPost{sx}{sy}', (0.045, 0.045, 0.13), (sx * 0.215, sy * 0.215, zt + 0.065), br, bevel=0.005))
    for k, (sz, loc) in enumerate((((0.50, 0.035, 0.03), (0, -0.215, zt + 0.145)), ((0.50, 0.035, 0.03), (0, 0.215, zt + 0.145)),
                                   ((0.035, 0.50, 0.03), (-0.215, 0, zt + 0.145)), ((0.035, 0.50, 0.03), (0.215, 0, zt + 0.145)))):
        P.append(Q.box(f'CapFrame{k}', sz, loc, br, bevel=0.004))
    zr = zt + 0.16; cr = 0.36 * math.sqrt(2)
    rf = Q.lathe('Roof', [(0, zr), (cr * 0.93, zr), (cr * 1.02, zr + 0.016), (cr * 0.99, zr + 0.028), (cr * 0.72, zr + 0.07), (cr * 0.36, zr + 0.13),
                          (0.11, zr + 0.158), (0.11, zr + 0.172), (0.07, zr + 0.18), (0.075, zr + 0.192), (0, zr + 0.2)], roof, segs=4, a0=math.pi / 4, sharp=20)
    P.append(rf)
    for k in range(4):
        th = math.pi / 4 + k * math.pi / 2; d = Vector((math.cos(th), math.sin(th), 0))
        P.append(Q.tube(f'RoofHip{k}', [d * cr * 0.99 + Vector((0, 0, zr + 0.034)), d * cr * 0.55 + Vector((0, 0, zr + 0.106)), d * 0.12 + Vector((0, 0, zr + 0.162))], 0.011, roof, segs=8, res=6))
    # iron band, cleanout door (front), flue inlet (+X)
    zb = 0.43
    for k, (sz, loc) in enumerate((((0.565, 0.009, 0.05), (0, -0.2775, zb)), ((0.565, 0.009, 0.05), (0, 0.2775, zb)),
                                   ((0.009, 0.565, 0.05), (-0.2775, 0, zb)), ((0.009, 0.565, 0.05), (0.2775, 0, zb)))):
        P.append(Q.box(f'Band{k}', sz, loc, iron, bevel=0.002, bseg=1))
    for sx in (-1, 1):
        for sy in (-1, 1):
            P.append(Q.box(f'BandCorner{sx}{sy}', (0.045, 0.045, 0.064), (sx * 0.262, sy * 0.262, zb), iron, bevel=0.004))
    for k in range(4):
        x = -0.18 + k * 0.12
        P.append(Q.cyl(f'BandRivet{k}', 0.008, 0.008, (x, -0.283, zb), iron, segs=8, bevel=0.002, rot=(math.pi / 2, 0, 0)))
    P.append(Q.box('Door_Frame', (0.20, 0.014, 0.18), (0, -0.278, 0.60), br, bevel=0.005))
    P.append(Q.box('Door_Panel', (0.15, 0.010, 0.13), (0, -0.288, 0.60), br, bevel=0.006))
    for sz in (-1, 1):
        P.append(Q.cyl(f'Door_Hinge{sz}', 0.008, 0.035, (0.083, -0.292, 0.60 + sz * 0.045), br, segs=10, bevel=0.002))
    P.append(Q.torus('Door_Ring', 0.018, 0.0035, (-0.045, -0.296, 0.585), br, 16, 6, rot=(math.pi / 2, 0, 0)))
    P.append(Q.cyl('Door_RingBoss', 0.009, 0.008, (-0.045, -0.292, 0.602), br, segs=10, rot=(math.pi / 2, 0, 0)))
    zi = 0.98
    P.append(Q.box('Inlet_Plate', (0.012, 0.17, 0.17), (0.279, 0, zi), br, bevel=0.004))
    inlet = Q.lathe('Inlet_Pipe', [(0.066, 0.0), (0.066, 0.085), (0.078, 0.09), (0.078, 0.11), (0.058, 0.11), (0.058, -0.02), (0.066, -0.02)], sootm, segs=24)
    inlet.location = (0.285, 0, zi); inlet.rotation_euler = (0, math.pi / 2, 0); P.append(inlet)
    for sy in (-1, 1):
        for sz in (-1, 1):
            P.append(Q.cyl(f'Inlet_Bolt{sy}{sz}', 0.007, 0.008, (0.287, sy * 0.065, zi + sz * 0.065), iron, segs=8, bevel=0.002, rot=(0, math.pi / 2, 0)))
    Q.finalize_parts(P, 1212)
    return P, dict(states={'default': 'soot darkens the upper courses'}, sockets={'flue_inlet': [0.39, 0, zi], 'smoke_outlet': [0, 0, zt + 0.08]})
