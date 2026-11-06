"""Batch 1 builders: B03 mortar, B04 sorting trays, B05 drawer cabinet, B06 water jar."""
import math
from mathutils import Vector, Matrix
import qa_lib as Q
from qa_assets import asset

TAU = math.tau


# ============================================================================ B03 stone mortar and pestle
@asset('B03', 'StoneMortar', res=512, budget=2500, size=(0.32, 0.32, 0.25),
       collision={'type': 'cylinder', 'radius': 0.16, 'height': 0.17, 'center': [0, 0, 0.085], 'note': 'table prop; interaction: grind (material pre-processing)'})
def b03(state='default'):
    st = Q.m_stone('B03_Granite', light=(0.20, 0.196, 0.19), dark=(0.125, 0.122, 0.118), scale=0.9, speck=1.6, chisel=5.0)
    powder = Q.m_simple('B03_HerbPowder', (0.20, 0.23, 0.10), (0.30, 0.30, 0.14), rough=0.95, nscale=60, bump=0.0008)
    P = []
    prof = [(0, 0), (0.085, 0), (0.092, 0.004), (0.094, 0.026), (0.088, 0.032), (0.098, 0.037), (0.124, 0.060), (0.141, 0.094), (0.149, 0.124),
            (0.150, 0.140), (0.157, 0.143), (0.159, 0.161), (0.155, 0.168), (0.141, 0.170), (0.129, 0.168), (0.124, 0.160), (0.121, 0.130),
            (0.110, 0.092), (0.082, 0.064), (0.042, 0.054), (0, 0.052)]
    bowl = Q.lathe('Mortar_Bowl', prof, st, segs=40, sharp=40)
    notch = Q.cyl('Cut_Spout', 0.021, 0.08, (0, -0.15, 0.181), st, segs=20, rot=(math.pi / 2, 0, 0))
    Q.boolean(bowl, notch); Q.apply_mods(bowl); Q.weld(bowl); Q.jitter(bowl, 0.0006, 3); P.append(bowl)
    pw = Q.lathe('Mortar_Powder', [(0, 0.062), (0.05, 0.0585), (0.072, 0.064), (0.076, 0.066), (0, 0.066)], powder, segs=24)
    Q.jitter(pw, 0.0012, 5); P.append(pw)
    pest = Q.lathe('Pestle', [(0, 0), (0.015, 0.002), (0.025, 0.011), (0.0295, 0.028), (0.028, 0.046), (0.0235, 0.066), (0.0195, 0.095), (0.0168, 0.14),
                              (0.0158, 0.19), (0.0165, 0.222), (0.0178, 0.238), (0.0172, 0.250), (0.012, 0.258), (0, 0.260)], st, segs=24)
    pest.location = (-0.040, 0.0, 0.058); pest.rotation_euler = (0, math.radians(57), 0); Q.tag_node([pest], 'Pestle'); P.append(pest)
    Q.finalize_parts(P, 303)
    return P, dict(states={'default': 'pestle resting in the bowl over a small heap of ground herb'}, sockets={'grind_point': [0, 0, 0.07]})


# ============================================================================ B04 two-tier bamboo sorting trays
@asset('B04', 'BambooSortingTrays', res=1024, budget=8000, size=(0.62, 0.48, 0.68),
       collision={'type': 'box', 'size': [0.62, 0.48, 0.68], 'center': [0, 0, 0.34], 'note': 'upper tray = jade-tagged property, lower tray = amber-tagged property'})
def b04(state='default'):
    bam = Q.m_bamboo('B04_Bamboo', a=(0.19, 0.13, 0.05), b_=(0.29, 0.20, 0.09), axis='Z'); bam2 = Q.m_bamboo('B04_BambooStrip', a=(0.18, 0.12, 0.048), b_=(0.27, 0.19, 0.08), axis='X')
    weave = Q.m_weave('B04_TrayWeave', pitch=0.014, a=(0.22, 0.15, 0.06), b_=(0.36, 0.26, 0.11))
    br = Q.m_bronze('B04_BronzeCaps', patina=0.6, polish=0.6); cord = Q.m_cord('B04_Rattan', (0.36, 0.25, 0.11), (0.48, 0.35, 0.16))
    jade = Q.m_celadon('B04_JadeTag', g1=(0.16, 0.27, 0.23), g2=(0.24, 0.36, 0.30)); amber = Q.m_bronze('B04_AmberTag', patina=0.05, polish=0.9)
    P = []
    X, Y, H = 0.285, 0.205, 0.665
    for sx in (-1, 1):
        for sy in (-1, 1):
            P.append(Q.pole(f'Post_{sx}{sy}', (sx * X, sy * Y, 0.05), (sx * X, sy * Y, H - 0.03), 0.021, bam, segs=12, node_every=0.2))
            P.append(Q.box(f'PostFoot_{sx}{sy}', (0.056, 0.056, 0.055), (sx * X, sy * Y, 0.0275), br, bevel=0.006, bseg=2))
            P.append(Q.box(f'PostCap_{sx}{sy}', (0.052, 0.052, 0.036), (sx * X, sy * Y, H - 0.018), br, bevel=0.007, bseg=2))
    for sy in (-1, 1):
        P.append(Q.pole(f'StretchX_{sy}', (-X, sy * Y, 0.11), (X, sy * Y, 0.11), 0.012, bam, segs=10, node_every=0.25))
    for sx in (-1, 1):
        P.append(Q.pole(f'StretchY_{sx}', (sx * X, -Y, 0.11), (sx * X, Y, 0.11), 0.012, bam, segs=10, node_every=0.25))
    tilt = math.radians(9)

    def tray(tag, zc, plate_mat):
        objs = []
        W, D, h = 0.53, 0.38, 0.05
        objs.append(Q.box(f'Tray{tag}_Floor', (W - 0.02, D - 0.02, 0.006), (0, 0, 0.004), weave, bevel=0.0))
        for sy in (-1, 1):
            objs.append(Q.box(f'Tray{tag}_RimX{sy}', (W, 0.016, h), (0, sy * (D / 2 - 0.008), h / 2), bam2, bevel=0.005, bseg=2))
            objs.append(Q.box(f'Tray{tag}_WallX{sy}', (W - 0.03, 0.004, h - 0.012), (0, sy * (D / 2 - 0.018), h / 2), weave, bevel=0.0))
        for sx in (-1, 1):
            objs.append(Q.box(f'Tray{tag}_RimY{sx}', (0.016, D, h), (sx * (W / 2 - 0.008), 0, h / 2), bam2, bevel=0.005, bseg=2))
            objs.append(Q.box(f'Tray{tag}_WallY{sx}', (0.004, D - 0.03, h - 0.012), (sx * (W / 2 - 0.018), 0, h / 2), weave, bevel=0.0))
        for sx in (-1, 1):
            for sy in (-1, 1):
                for k in range(3):
                    objs.append(Q.torus(f'Tray{tag}_Lash{sx}{sy}{k}', 0.011, 0.0028, (sx * (W / 2 - 0.008), sy * (D / 2 - 0.03 - k * 0.007), h - 0.012),
                                        cord, 12, 5, rot=(0, math.pi / 2, 0)))
        objs.append(Q.box(f'Tray{tag}_Tag', (0.10, 0.006, 0.036), (0, -D / 2 - 0.006, h * 0.15), plate_mat, bevel=0.002))
        for sx in (-1, 1):
            objs.append(Q.torus(f'Tray{tag}_TagRing{sx}', 0.006, 0.0014, (sx * 0.035, -D / 2 - 0.005, h * 0.15 + 0.022), amber, 10, 4, rot=(0, math.pi / 2, 0)))
        M = Matrix.Translation(Vector((0, 0, zc))) @ Matrix.Rotation(-tilt, 4, 'X')
        for o in objs: o.matrix_basis = M @ o.matrix_basis
        for sx in (-1, 1):
            a = M @ Vector((sx * 0.272, -Y - 0.01, -0.012)); b = M @ Vector((sx * 0.272, Y + 0.01, -0.012))
            objs.append(Q.pole(f'Tray{tag}_Rail{sx}', a, b, 0.011, bam, segs=10, node_every=0.3))
        return objs
    P += tray('Up', 0.47, jade)
    P += tray('Low', 0.215, amber)
    for sx in (-1, 1):
        P.append(Q.pole(f'Brace_{sx}', (sx * X, Y, 0.13), (sx * X, 0.02, 0.43), 0.009, bam, segs=8, node_every=0.4))
    Q.finalize_parts(P, 404)
    return P, dict(states={'default': 'both trays empty; upper tag jade, lower tag amber'}, sockets={'tray_upper': [0, 0, 0.50], 'tray_lower': [0, 0, 0.245]})


# ============================================================================ B05 three-tier herb drawer cabinet
@asset('B05', 'HerbDrawerCabinet', res=1024, budget=7000, size=(0.76, 0.48, 0.92),
       collision={'type': 'box', 'size': [0.76, 0.48, 0.92], 'center': [0, 0, 0.46], 'note': 'drawers are separate nodes Drawer1-3 that slide along -Y by up to 0.28 m'})
def b05(state='default'):
    wd = Q.m_wood('B05_Walnut', axis='X'); wdv = Q.m_wood('B05_WalnutV', axis='Z'); wdy = Q.m_wood('B05_WalnutY', axis='Y')
    br = Q.m_bronze('B05_Bronze', patina=0.55, polish=0.7)
    por = Q.m_simple('B05_Porcelain', (0.70, 0.71, 0.66), (0.78, 0.79, 0.74), rough=0.25, nscale=12, cav_col=(0.4, 0.42, 0.38))
    P = []
    W, D, H = 0.72, 0.44, 0.84; px, py = W / 2 - 0.0225, D / 2 - 0.0225
    for sx in (-1, 1):
        for sy in (-1, 1):
            P.append(Q.box(f'Post_{sx}{sy}', (0.045, 0.045, H), (sx * px, sy * py, H / 2), wdv, bevel=0.004))
    P.append(Q.box('Top', (W + 0.04, D + 0.04, 0.034), (0, 0, H + 0.017), wd, bevel=0.006, bseg=3))
    P.append(Q.box('Gallery', (W - 0.04, 0.016, 0.042), (0, D / 2 - 0.006, H + 0.055), wd, bevel=0.004))
    for sx in (-1, 1):
        P.append(Q.box(f'GalleryPost{sx}', (0.024, 0.022, 0.07), (sx * (W / 2 - 0.02), D / 2 - 0.006, H + 0.068), wdv, bevel=0.008, bseg=3))
    for sx in (-1, 1):
        P.append(Q.box(f'SidePanel{sx}', (0.012, D - 0.06, H - 0.16), (sx * (W / 2 - 0.016), 0, 0.08 + (H - 0.16) / 2 + 0.02), wdv, bevel=0.002))
        for z in (0.10, H - 0.03):
            P.append(Q.box(f'SideRail{sx}{z:.2f}', (0.03, D - 0.05, 0.04), (sx * (W / 2 - 0.022), 0, z), wdy, bevel=0.004))
    ap = [(-0.30, 0.0), (0.30, 0.0), (0.30, 0.03), (0.27, 0.03), (0.25, 0.015), (-0.25, 0.015), (-0.27, 0.03), (-0.30, 0.03)]
    P.append(Q.prism('ApronFront', [(x, z + 0.055) for x, z in ap], 0.018, wd, axis='Y', center=-D / 2 + 0.012))
    for i in range(3):
        P.append(Q.box(f'BackBoard{i}', (0.215, 0.012, H - 0.03), (-0.22 + i * 0.22, D / 2 - 0.012, (H - 0.03) / 2 + 0.03), wdv, bevel=0.002))
    for z in (0.30, 0.62):
        P.append(Q.box(f'BackBatten{z}', (W - 0.07, 0.016, 0.05), (0, D / 2 + 0.002, z), wd, bevel=0.004))
    rails = [0.08, 0.33, 0.58, H - 0.02]
    for z in rails:
        P.append(Q.box(f'FrontRail{z:.2f}', (W - 0.08, 0.03, 0.022), (0, -D / 2 + 0.017, z), wd, bevel=0.003))
    for i in range(3):
        z0, z1 = rails[i] + 0.011, rails[i + 1] - 0.011; zc = (z0 + z1) / 2; h = z1 - z0 - 0.004; w = W - 0.095
        D_ = [Q.box(f'Drawer{i + 1}_Front', (w, 0.022, h), (0, -D / 2 + 0.013, zc), wd, bevel=0.003, bseg=2)]
        for sx in (-1, 1):
            D_.append(Q.box(f'Drawer{i + 1}_Side{sx}', (0.012, D - 0.07, h - 0.02), (sx * (w / 2 - 0.01), 0.0, zc - 0.005), wdy, bevel=0.0015))
        D_.append(Q.box(f'Drawer{i + 1}_Back', (w - 0.03, 0.012, h - 0.02), (0, D / 2 - 0.04, zc - 0.005), wd, bevel=0.0015))
        D_.append(Q.box(f'Drawer{i + 1}_Bottom', (w - 0.03, D - 0.07, 0.008), (0, 0, z0 + 0.01), wd, bevel=0.0))
        fy = -D / 2 + 0.0015; bw, bh, t = w - 0.03, h - 0.03, 0.009
        for nm, sz, loc in (('T', (bw, 0.003, t), (0, fy, zc + bh / 2)), ('B', (bw, 0.003, t), (0, fy, zc - bh / 2)),
                            ('L', (t, 0.003, bh), (-bw / 2, fy, zc)), ('R', (t, 0.003, bh), (bw / 2, fy, zc))):
            D_.append(Q.box(f'Drawer{i + 1}_Frame{nm}', sz, loc, br, bevel=0.001, bseg=1))
        for sx in (-1, 1):
            for sz in (-1, 1):
                D_.append(Q.box(f'Drawer{i + 1}_Corner{sx}{sz}', (0.032, 0.004, 0.032), (sx * (bw / 2 - 0.01), fy - 0.0005, zc + sz * (bh / 2 - 0.01)), br, bevel=0.0015, bseg=1))
        D_.append(Q.cyl(f'Drawer{i + 1}_PullPlate', 0.03, 0.004, (-0.03, fy - 0.002, zc + 0.012), br, segs=20, bevel=0.0015, rot=(math.pi / 2, 0, 0)))
        D_.append(Q.tube(f'Drawer{i + 1}_Bail', [Vector((-0.072, fy - 0.006, zc + 0.016)), Vector((-0.066, fy - 0.014, zc - 0.014)), Vector((-0.03, fy - 0.016, zc - 0.026)),
                                                  Vector((0.006, fy - 0.014, zc - 0.014)), Vector((0.012, fy - 0.006, zc + 0.016))], 0.0042, br, segs=8, res=6))
        D_.append(Q.box(f'Drawer{i + 1}_LabelFrame', (0.082, 0.005, 0.05), (0.13, fy - 0.001, zc), br, bevel=0.002, bseg=1))
        D_.append(Q.box(f'Drawer{i + 1}_Label', (0.068, 0.006, 0.036), (0.13, fy - 0.002, zc), por, bevel=0.0015, bseg=1))
        Q.tag_node(D_, f'Drawer{i + 1}'); P += D_
    Q.finalize_parts(P, 505)
    return P, dict(states={'default': 'all drawers closed; label colour/ink for identified vs unidentified is set by the game'},
                   sockets={'top_surface': [0, 0, H + 0.034], 'drawer_slide_axis': [0, -1, 0], 'drawer_slide_max': 0.28})


# ============================================================================ B06 ceramic water jar
JAR = [(0, 0), (0.150, 0), (0.156, 0.005), (0.154, 0.030), (0.148, 0.034), (0.162, 0.044), (0.198, 0.095), (0.224, 0.170), (0.234, 0.245),
       (0.228, 0.315), (0.207, 0.375), (0.176, 0.418), (0.152, 0.440), (0.143, 0.455), (0.145, 0.474), (0.158, 0.480), (0.163, 0.490),
       (0.159, 0.499), (0.146, 0.502), (0.136, 0.496), (0.131, 0.472), (0.150, 0.420), (0.200, 0.330), (0.208, 0.200), (0.160, 0.070), (0.08, 0.045), (0, 0.042)]


@asset('B06', 'CeramicWaterJar', res=1024, budget=5000, size=(0.56, 0.52, 0.55),
       collision={'type': 'cylinder', 'radius': 0.24, 'height': 0.52, 'center': [0, 0, 0.26], 'note': 'lid is node Lid; water level socket for the water resource'})
def b06(state='default'):
    cel = Q.m_celadon('B06_Celadon', glaze_z=0.205, drip=0.075, incise=(0.405, 0.006, 14.0, 0.0032), clay=(0.20, 0.18, 0.155), g1=(0.095, 0.14, 0.11), g2=(0.17, 0.22, 0.18), glaze_rough=0.3)
    wd = Q.m_wood('B06_LidWood', a=(0.09, 0.05, 0.028), b_=(0.18, 0.10, 0.055), axis='X', wear=0.5)
    water = Q.m_simple('B06_Water', (0.03, 0.06, 0.055), (0.05, 0.09, 0.08), rough=0.05, nscale=3)
    P = []
    jar = Q.lathe('Jar_Body', JAR, cel, segs=56, sharp=40)
    for v in jar.data.vertices:                                       # pinch a pour spout at the front of the lip
        if v.co.z > 0.462:
            th = math.atan2(v.co.y, v.co.x); d = (th + math.pi / 2 + math.pi) % TAU - math.pi
            k = math.exp(-(d / 0.30) ** 2) * (v.co.z - 0.462) / 0.04
            s = 1 + 0.16 * k; v.co.x *= s; v.co.y *= s; v.co.z -= 0.006 * k
    P.append(jar)
    for sx in (-1, 1):
        pts = [Vector((sx * 0.192, 0, 0.410)), Vector((sx * 0.236, 0, 0.428)), Vector((sx * 0.262, 0, 0.398)), Vector((sx * 0.250, 0, 0.362)), Vector((sx * 0.214, 0, 0.352))]
        P.append(Q.tube(f'Jar_Lug{sx}', pts, 0.0135, cel, segs=10, res=8))
    P.append(Q.lathe('Jar_Water', [(0, 0.432), (0.168, 0.432), (0, 0.4321)], water, segs=40))
    lid = [Q.cyl('Lid_Disc', 0.172, 0.026, (0, 0, 0.503 + 0.013), wd, segs=40, bevel=0.005, bseg=2),
           Q.box('Lid_Handle', (0.13, 0.026, 0.024), (0, 0, 0.503 + 0.026 + 0.012), wd, bevel=0.007, bseg=3)]
    for sx in (-1, 1):
        lid.append(Q.box(f'Lid_Key{sx}', (0.03, 0.04, 0.004), (sx * 0.15, 0, 0.503 + 0.026), wd, bevel=0.001))
    Q.tag_node(lid, 'Lid'); P += lid
    Q.finalize_parts(P, 606)
    return P, dict(states={'default': 'lid on; water surface at z 0.432'}, sockets={'water_surface': [0, 0, 0.432], 'lid_rest_z': 0.503})
