"""FR03 hanging vine curtains (work pack B-104h part 2): 2 x 0.2 x 3 m, two kinds: Dense and Sparse.

Three-view FR03 candidates 01 (dense) and 02 (sparse). A curtain of vine strands hangs from a short twisted runner of old vine
stems. The strands are alpha-clipped cards (two-sided): each strand is a ribbon of 1 m segments mapped onto a vine-strip cell of a
shared atlas; the last segment uses a tip cell. The atlas is rendered here from real leaf geometry (heart-shaped leaves on
petioles, alternating along a wavy stem), the strip cells periodic top to bottom so segments join without a seam.

Atlas (FR03_Shared/Textures/FR03_VineCards_*.png, 2048, four cells 0.25 m x 1 m at 2048 px/m):
  cell 0  dense strip (two stems wound together, leaves every 6 cm)    cell 2  dense tip (leaves shrink, a tendril curls)
  cell 1  sparse strip (one stem, leaves every 11 cm, gaps)            cell 3  sparse tip
Vertex colour 'Wind' (the FBX colour layer): R 0 at the hang line -> 1 at the tips, G per-strand phase, B 1 at the top -> 0 at the
bottom. minTier high; no collision (it never blocks a walk; switching it off changes nothing for walking).
Origin: centre of the hang line (top). Everything hangs below z = 0; ground_z -3 m for the review views.
"""
import bpy, math, random
import numpy as np
from pathlib import Path
from mathutils import Vector, noise
from ti_core import S, mesh, socket
import ti_mats as tm
import fr_parts as FP

VINE_DIR = Path(__file__).resolve().parents[2] / 'exports' / 'forest-roots-b' / 'FR03_Shared' / 'Textures'
CELL_W, CELL_H = .25, 1.
CELLS = {0: (0., 0., .25, 1.), 1: (.25, 0., .5, 1.), 2: (.5, 0., .75, 1.), 3: (.75, 0., 1., 1.)}
HALF_X, HALF_Y = 1., .1
TOP_Z = -.035
SC_MAX = .97                       # the longest strand: 3 segments of 0.97 m -> lowest point TOP_Z - 2.91 m


# ------------------------------------------------------------------ atlas: leaves and stems rendered top-down
def _leaf_mat(name):
    """'tone' 0 old dark .. 1 young; 'bronze' a few old leaves turning; 'cuv' leaf space (u across, v base -> tip)."""
    m = bpy.data.materials.new(name); m.use_nodes = True; m.node_tree.nodes.clear(); g = tm.G(m)
    tone = g.attr('tone', 'Fac'); C = g.attr('cuv'); cs = g.node('ShaderNodeSeparateXYZ'); g.link(C, cs.inputs[0])
    u, v = cs.outputs['X'], cs.outputs['Y']
    old = g.ramp(v, [(.0, (.018, .042, .02)), (.6, (.032, .07, .03)), (1., (.04, .082, .032))])
    mid = g.ramp(v, [(.0, (.04, .085, .03)), (.6, (.075, .14, .042)), (1., (.1, .17, .05))])
    young = g.ramp(v, [(.0, (.1, .17, .05)), (.7, (.2, .28, .07)), (1., (.26, .32, .09))])
    col = g.mix(g.maprange(tone, .0, .5), old, mid); col = g.mix(g.maprange(tone, .6, .95), col, young)
    col = g.mix(g.math('MULTIPLY', g.attr('bronze', 'Fac'), .7), col, (.075, .055, .022))
    au = g.math('ABSOLUTE', g.math('SUBTRACT', u, .5))
    vein = g.maprange(au, .03, .0)
    col = g.mix(g.math('MULTIPLY', vein, .4), col, (.2, .27, .1))
    side_v = g.maprange(g.math('ABSOLUTE', g.math('SINE', g.math('ADD', g.math('MULTIPLY', v, 22.), g.math('MULTIPLY', au, 30.)))), .93, 1.)
    col = g.mix(g.math('MULTIPLY', side_v, .25), col, (.13, .2, .07))
    rim = g.maprange(au, .42, .5)
    col = g.mix(g.math('MULTIPLY', rim, .3), col, (.1, .15, .06))
    ao = g.node('ShaderNodeAmbientOcclusion', only_local=True, samples=16); ao.inputs['Distance'].default_value = .04
    g.link(col, ao.inputs['Color'])
    col = g.mul(1., col, g.ramp(ao.outputs['AO'], [(0, (.3, .32, .33)), (1, (1, 1, 1))]))
    em = g.node('ShaderNodeEmission'); g.link(col, em.inputs['Color'])
    out = g.node('ShaderNodeOutputMaterial'); g.link(em.outputs[0], out.inputs['Surface'])
    return m


def _normal_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; m.node_tree.nodes.clear(); g = tm.G(m)
    # Cycles already turns a back face's shading normal towards the camera: no second flip here (that turned 72 % of the
    # leaves inside out in the first atlas); vine_atlas also flips any texel still pointing away.
    n = g.geo('Normal')
    c = g.vmath('ADD', g.vmath('MULTIPLY', n, (.5, .5, .5)), (.5, .5, .5))
    em = g.node('ShaderNodeEmission'); g.link(c, em.inputs['Color'])
    out = g.node('ShaderNodeOutputMaterial'); g.link(em.outputs[0], out.inputs['Surface'])
    return m


def _leaf(verts, faces, A, base, d, L, tone, bronze, tilt):
    """A heart-shaped vine leaf: two rounded lobes at the base, pointed tip, cupped, tip curling back. d: the blade direction in XY."""
    d = Vector((d[0], d[1], 0)).normalized(); side = Vector((-d.y, d.x, 0)); up = Vector((0, 0, 1))
    nu, nv = 4, 8; k0 = len(verts); W = L * .42
    for j in range(nv + 1):
        v = j / nv
        w = W * (math.sin(math.pi * min(.999, v) ** .62) * (1.08 - .3 * v) + .25 * max(0., .22 - v) / .22)   # lobes at the base
        back = -.012 * L * max(0., .22 - v) / .22                                                            # lobes reach back past the petiole
        for i in range(nu + 1):
            u = i / nu; x = (u - .5) * 2
            p = base + d * (L * v + back * x * x) + side * (x * w) + up * (L * (.22 * x * x - .12 * v * v + tilt * v))
            verts.append(tuple(p)); A['cuv'].append((u, v, 0.)); A['tone'].append(tone); A['bronze'].append(bronze)
    for j in range(nv):
        for i in range(nu):
            a = k0 + j * (nu + 1) + i
            faces.append((a, a + 1, a + nu + 2, a + nu + 1))


def _stem_x(y, ph, amp, per):
    return amp * math.sin(math.tau * y / per + ph)


def _cell_geometry(kind):
    """Leaves and stems for one cell in the XY plane: x across (-0.125..0.125), y along the strand (1 = up, the hang side; 0 = down).
    Strip cells (0, 1) are periodic in y with period 1: leaf nodes near the bottom are placed again one period up, so whatever
    hangs over the bottom edge reappears at the top. Tip cells (2, 3) carry the same repeats (they continue the strip segment
    above) and end in a tip with smaller leaves and a curled tendril."""
    dense = kind in (0, 2); tip = kind >= 2
    verts, faces = [], []; A = {'cuv': [], 'tone': [], 'bronze': []}; stems = []
    step = .06 if dense else .11
    phs, amps, pers = ([0., 2.2], [.022, .03], [1., .5]) if dense else ([.7], [.022], [1.])
    def nodes(Rx, y0, y1, scale_fn=lambda y: 1.):
        out = []; y = y1 - Rx.uniform(0, step); sgn = 1
        while y > y0:
            st = Rx.randrange(len(phs))
            for _ in range(2 if dense and Rx.random() < .35 else 1):
                out.append(dict(y=y, st=st, sgn=sgn, ang=math.radians(Rx.uniform(25, 75)), L=Rx.uniform(.045, .07) * scale_fn(y),
                                pet=Rx.uniform(.012, .028), tone=min(1., Rx.uniform(0, .75) + (.25 if Rx.random() < .12 else 0)),
                                bronze=1. if Rx.random() < .03 else 0., tilt=Rx.uniform(-.1, .35)))
                sgn = -sgn
            y -= step * Rx.uniform(.75, 1.25)
        return out
    strip = nodes(random.Random(1000 + (0 if dense else 1)), 0., 1.)       # the strip's nodes, the same in its tip cell
    def put(n, dy):
        y = n['y'] + dy; st = n['st']; sx = _stem_x(y, phs[st], amps[st], pers[st])
        base = Vector((sx, y, .004 * st))
        d = (n['sgn'] * math.cos(n['ang']), -math.sin(n['ang']))
        pe = base + Vector((d[0], d[1], 0)) * n['pet']
        if max(abs(pe.x + d[0] * n['L'] * 1.05), abs(pe.x)) + n['L'] * .3 > CELL_W / 2 - .004: return
        stems.append([tuple(base), tuple(pe + Vector((0, 0, .002)))])
        _leaf(verts, faces, A, pe, d, n['L'], n['tone'], n['bronze'], n['tilt'])
    y_tip = .1
    for n in strip:
        if n['y'] < .2: put(n, 1.)                                           # repeats from one period up
    if not tip:
        for n in strip: put(n, 0.)
    else:
        for n in nodes(random.Random(2000 + (0 if dense else 1)), y_tip + .05, 1., lambda y: .55 + .45 * min(1., (y - y_tip) / .5)): put(n, 0.)
    for k in range(len(phs)):
        lo = (y_tip + .25 * k) if tip else -.05
        pts = [(_stem_x(y, phs[k], amps[k], pers[k]), y, .004 * k) for y in np.linspace(1.05, lo, 70)]
        if tip and k == 0:                                                   # a tendril curls off the end
            c = Vector(pts[-1]); r0 = .02
            for a in np.linspace(0, 1.6 * math.pi, 14)[1:]:
                r = r0 * (1 - .6 * a / (1.6 * math.pi)); pts.append((c.x + r * math.sin(a), c.y - r0 + r * math.cos(a), c.z))
        stems.append(pts)
    me = bpy.data.meshes.new(f'VineCell_{kind}'); me.from_pydata(verts, [], faces); me.update()
    for nm, vals in A.items():
        if nm == 'cuv':
            at = me.attributes.new(nm, 'FLOAT_VECTOR', 'POINT'); at.data.foreach_set('vector', [c for v in vals for c in v])
        else:
            at = me.attributes.new(nm, 'FLOAT', 'POINT'); at.data.foreach_set('value', vals)
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(f'VineCell_{kind}', me); st = []
    for pts in stems:
        cu = bpy.data.curves.new('VineStem', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = .0032 if len(pts) > 2 else .0016; cu.bevel_resolution = 1
        sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
        for q, pt in zip(sp.points, pts): q.co = (*pt, 1)
        st.append(bpy.data.objects.new('VineStem', cu))
    return o, st


def vine_atlas(size=2048):
    """Render the four cells top-down (orthographic, transparent film) into BaseColor+alpha and a tangent-space normal map; pad the
    colours past the alpha edge (alpha clip 0.5) so mip levels do not bleed the background in."""
    VINE_DIR.mkdir(parents=True, exist_ok=True)
    out_c = VINE_DIR / 'FR03_VineCards_BaseColor.png'; out_n = VINE_DIR / 'FR03_VineCards_Normal.png'
    if out_c.exists() and out_n.exists(): return out_c, out_n
    scene = bpy.context.scene
    keep = dict(engine=scene.render.engine, ft=scene.render.film_transparent, vt=scene.view_settings.view_transform, rx=scene.render.resolution_x,
                ry=scene.render.resolution_y, fs=scene.render.filter_size, cam=scene.camera)
    scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = 16; scene.cycles.use_denoising = False
    scene.render.film_transparent = True; scene.view_settings.view_transform = 'Standard'
    cw, ch = size // 4, size
    scene.render.resolution_x, scene.render.resolution_y = cw, ch; scene.render.filter_size = .8
    scene.render.image_settings.file_format = 'PNG'; scene.render.image_settings.color_mode = 'RGBA'
    cam = bpy.data.objects.new('VineCam', bpy.data.cameras.new('VineCam')); scene.collection.objects.link(cam); scene.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = CELL_H; cam.location = (0, CELL_H / 2, 1); cam.rotation_euler = (0, 0, 0)
    lm, nm_ = _leaf_mat('VineAtlas_Colour'), _normal_mat('VineAtlas_Normal')
    stem_m = bpy.data.materials.new('VineAtlas_Stem'); stem_m.use_nodes = True
    sn = stem_m.node_tree.nodes; sn.clear(); e = sn.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (.045, .04, .02, 1)
    o_ = sn.new('ShaderNodeOutputMaterial'); stem_m.node_tree.links.new(e.outputs[0], o_.inputs[0])
    stem_n = _normal_mat('VineAtlas_StemN')
    import tempfile
    tmp = Path(tempfile.gettempdir()) / 'fr03_cells'; tmp.mkdir(exist_ok=True)
    cells = {}
    for kind in range(4):
        o, st = _cell_geometry(kind); scene.collection.objects.link(o)
        for s_ in st: scene.collection.objects.link(s_)
        for pas, m, sm in (('c', lm, stem_m), ('n', nm_, stem_n)):
            o.data.materials.clear(); o.data.materials.append(m)
            for s_ in st: s_.data.materials.clear(); s_.data.materials.append(sm)
            scene.render.filepath = str(tmp / f'{kind}_{pas}.png'); bpy.ops.render.render(write_still=True)
            im = bpy.data.images.load(scene.render.filepath); cells[(kind, pas)] = np.array(im.pixels[:], np.float32).reshape(ch, cw, 4); bpy.data.images.remove(im)
        bpy.data.objects.remove(o); [bpy.data.objects.remove(s_) for s_ in st]
    col = np.zeros((size, size, 4), np.float32); nrm = np.zeros((size, size, 4), np.float32); nrm[..., :] = (.5, .5, 1, 1)
    for kind in range(4):
        c = cells[(kind, 'c')]; n = cells[(kind, 'n')]; c0 = kind * cw
        n = n.copy(); away = n[..., 2] < .5; n[away, :3] = 1. - n[away, :3]      # every texel's normal out of the card
        col[:, c0:c0 + cw] = c; nrm[:, c0:c0 + cw] = np.where(c[..., 3:4] > .5, n, (.5, .5, 1, 1))
    a = col[..., 3] > .5; rgb = col[..., :3].copy(); filled = a.copy()
    for _ in range(24):
        acc = np.zeros_like(rgb); cnt = np.zeros(a.shape, np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sh = np.roll(np.roll(filled, dy, 0), dx, 1); acc += np.roll(np.roll(rgb, dy, 0), dx, 1) * sh[..., None]; cnt += sh
        grow = (~filled) & (cnt > 0); rgb[grow] = acc[grow] / cnt[grow][:, None]; filled |= grow
    rgb[~filled] = (.03, .06, .025)
    col[..., :3] = rgb; col[..., 3] = a.astype(np.float32)
    def save(arr, path, srgb):
        im = bpy.data.images.new(path.stem, size, size, alpha=True, float_buffer=False)
        im.colorspace_settings.name = 'sRGB' if srgb else 'Non-Color'
        im.pixels.foreach_set(arr.ravel()); im.filepath_raw = str(path); im.file_format = 'PNG'; im.save()
    save(col, out_c, True); save(nrm, out_n, False)
    scene.render.engine = keep['engine']; scene.render.film_transparent = keep['ft']; scene.view_settings.view_transform = keep['vt']
    scene.render.resolution_x, scene.render.resolution_y, scene.render.filter_size, scene.camera = keep['rx'], keep['ry'], keep['fs'], keep['cam']
    bpy.data.objects.remove(cam)
    for m in (lm, nm_, stem_m, stem_n): bpy.data.materials.remove(m)
    return out_c, out_n


def vine_material(tex_c, tex_n):
    m = bpy.data.materials.new('FR03_VineCards'); m.use_nodes = True; nt = m.node_tree
    bs = nt.nodes['Principled BSDF']
    ic = nt.nodes.new('ShaderNodeTexImage'); ic.image = bpy.data.images.load(str(tex_c), check_existing=True)
    inn = nt.nodes.new('ShaderNodeTexImage'); inn.image = bpy.data.images.load(str(tex_n), check_existing=True); inn.image.colorspace_settings.name = 'Non-Color'
    nmap = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(inn.outputs['Color'], nmap.inputs['Color']); nt.links.new(nmap.outputs[0], bs.inputs['Normal'])
    nt.links.new(ic.outputs['Color'], bs.inputs['Base Color'])
    rnd = nt.nodes.new('ShaderNodeMath'); rnd.operation = 'ROUND'; nt.links.new(ic.outputs['Alpha'], rnd.inputs[0]); nt.links.new(rnd.outputs[0], bs.inputs['Alpha'])
    bs.inputs['Roughness'].default_value = .65; bs.inputs['Specular IOR Level'].default_value = .2
    try: m.blend_method = 'CLIP'
    except Exception: pass
    try: m.surface_render_method = 'DITHERED'
    except Exception: pass
    m.use_backface_culling = False
    tm.MAT_INFO[m.name] = {'slot': 'VineCards', 'own_uv': True}
    return m


def palette():
    P = FP.palette()
    c, n = vine_atlas(); P['vines'] = vine_material(c, n)
    return P


# ------------------------------------------------------------------ the curtain
def strands(kind):
    """(x, y, segments, scale, yaw, phase) per strand, seeded; LOD membership by index."""
    R = random.Random('FR03_' + kind); out = []
    if kind == 'Dense':
        n = 24
        for i in range(n):
            x = -.86 + 1.72 * (i + .5) / n + R.uniform(-.025, .025); segs = 3 if R.random() < .72 else 2
            out.append((x, -.05 + .1 * ((i * .618) % 1), segs, R.uniform(.84, SC_MAX), R.uniform(-.2, .2), R.random()))
    else:
        n = 11
        for i in range(n):
            x = -.84 + 1.68 * (i + .5) / n + R.uniform(-.06, .06); segs = R.choice((2, 2, 3, 3, 3))
            out.append((x, -.04 + .08 * ((i * .618) % 1), segs, R.uniform(.78, SC_MAX), R.uniform(-.2, .2), R.random()))
    m = n // 2; x, y, segs, sc, yaw, ph = out[m]; out[m] = (x, y, 3, SC_MAX, yaw * .3, ph)       # the longest strand sets the lowest point
    return out


def card_strand(V, F, UV, COL, MASK, x, y, segs, sc, yaw, ph, strip, tipc, mask, rows, widen=1., H=3.):
    """One strand: a ribbon of segs segments (each CELL_H * sc long) hanging from (x, y, TOP_Z) with a slow sway; the card faces -Y
    turned by yaw; three columns, the middle one bowed back a little so the card is not dead flat."""
    n = Vector((math.sin(yaw), -math.cos(yaw), 0.)); side = n.cross(Vector((0, 0, -1))).normalized()
    w = CELL_W * sc * widen; seg_len = CELL_H * sc; L = seg_len * segs
    def centre(s):                    # s metres down the strand
        t = s / L
        return Vector((x + .025 * math.sin(s * 2.1 + ph * 6.) * t, y * min(1., s / .3) + .012 * math.sin(s * 1.3 + ph * 4.) * t, TOP_Z - s))   # tops on the runner
    prev = None                       # segments share their joining row of vertices (one welded strip); UVs are per corner
    for k in range(segs):
        u0, v0, u1, v1 = CELLS[tipc if k == segs - 1 else strip]
        rows_idx = []
        for r in range(rows + 1):
            if r == 0 and prev is not None: rows_idx.append(prev); continue
            c = centre(seg_len * (k + r / rows)); idx = []
            for u in (0., .5, 1.):
                p = c + side * ((u - .5) * w) + n * (-.012 * w * (1 - (2 * u - 1) ** 2))
                V.append(tuple(p)); idx.append(len(V) - 1)
                COL.append((min(1., (TOP_Z - p[2]) / (H - .1)), ph, max(0., min(1., 1 + p[2] / H)), 1.))
            rows_idx.append(idx)
        vr = lambda rr: v1 - (v1 - v0) * rr / rows
        uu = lambda ii: u0 + (u1 - u0) * ii * .5
        for r in range(rows):
            for i in range(2):
                F.append((rows_idx[r][i], rows_idx[r + 1][i], rows_idx[r + 1][i + 1], rows_idx[r][i + 1])); MASK.append(mask)
                UV.append(((uu(i), vr(r)), (uu(i), vr(r + 1)), (uu(i + 1), vr(r + 1)), (uu(i + 1), vr(r))))
        prev = rows_idx[-1]


def runner(P, R):
    """The hang line: three old vine stems twisted round each other along X just under the origin, thinning to the ends."""
    for k in range(3):
        ph = k * math.tau / 3; pts, rad = [], []
        for i in range(29):
            x = -.97 + 1.94 * i / 28; a = ph + x * 5.5
            pts.append((x, .018 * math.cos(a) + .006 * noise.noise(Vector((x * 2, k, 0))), -.038 + .014 * math.sin(a)))
            rad.append(.011 + .006 * (1 - abs(x)) + .002 * k)
        FP.sweep('Vine_Runner', pts, rad, P['bark'][1], step=.03, fiss=.12, plates=4., nring=8, lump=.06, seed=R.randrange(999), ground=None, cap=True)


def fr03_curtain(P, kind):
    runner(P, random.Random('FR03_' + kind + '_runner'))
    strip, tipc = (0, 2) if kind == 'Dense' else (1, 3)
    V, F, UV, COL, MASK = [], [], [], [], []
    ss = strands(kind)
    for i, (x, y, segs, sc, yaw, ph) in enumerate(ss):
        card_strand(V, F, UV, COL, MASK, x, y, segs, sc, yaw, ph, strip, tipc, 1, 8)                             # LOD0: every strand
        if i % 2 == 0: card_strand(V, F, UV, COL, MASK, x, y, segs, sc, yaw, ph, strip, tipc, 2, 8, widen=1.25)   # LOD1: every other, wider
        if i % 3 == 1: card_strand(V, F, UV, COL, MASK, x, y, segs, sc, yaw, ph, strip, tipc, 4, 4, widen=1.5)    # LOD2: a third, wider, coarser
    o = mesh('Vine_Cards', V, F, P['vines'], grain='z', detail=0, group='Leaves')
    me = o.data; uv = me.uv_layers[0]
    for poly in me.polygons:
        for corner, li in enumerate(poly.loop_indices): uv.data[li].uv = UV[poly.index][corner]
    ca = me.color_attributes.new('Wind', 'FLOAT_COLOR', 'POINT'); ca.data.foreach_set('color', [c for v in COL for c in v])
    lm = me.attributes.new('lod_mask', 'INT', 'FACE'); lm.data.foreach_set('value', MASK)
    for o2 in S['parts']:            # the runner: wind 0 (it is the fixed hang line)
        if o2.type == 'MESH' and o2.get('group', 'Main') != 'Leaves' and not o2.data.color_attributes:
            c = o2.data.color_attributes.new('Wind', 'FLOAT_COLOR', 'POINT'); c.data.foreach_set('color', [0., .5, 1., 1.] * len(o2.data.vertices))
    socket('Socket_Hang', (0, 0, 0))
    S['vines'] = dict(kind=kind, strands=len(ss), strip_cell=strip, tip_cell=tipc, lowest_design_z=round(TOP_Z - 3 * SC_MAX, 4))
    S['prop'] = dict(kind='vines')


NOTE = {'Dense': ('垂藤幕・密（三視圖 FR03 candidate-01）：寬 2 m、厚 0.2 m、垂長最多 2.95 m。頂端是三條老藤絞成的掛線（原點在掛線中點，全部在 z = 0 以下），'
                  '24 條藤蔓並排垂下、前後錯開，長短參差（約 1.7–2.9 m）。藤蔓是雙面透明裁切卡片，貼圖由真實葉片幾何渲染（心形葉、葉柄、兩條藤互纏）。'),
        'Sparse': ('垂藤幕・疏（三視圖 FR03 candidate-02）：寬 2 m、厚 0.2 m、垂長最多 2.95 m。同樣三藤絞成的掛線，'
                   '11 條單股藤蔓、間隔大，看得到後面；葉片稀，約每 11 cm 一片。')}
COMMON = ('minTier high：低畫質整件不載入。沒有碰撞，關掉不影響行走。頂點色 Wind：R 從掛線 0 到藤尖 1，G 每條藤的相位，B 高度。'
          'LOD1 每兩條取一條、加寬 1.25 倍；LOD2 每三條取一條、加寬 1.5 倍、分段減半。接口：Socket_Hang（掛線中點）。'
          '審圖畫面把掛線放在離地 3 m（ground_z −3 m）。')


def register(ASSETS):
    for kind, zh, ref in (('Dense', '垂藤幕・密', 'FR03/candidate-01'), ('Sparse', '垂藤幕・疏', 'FR03/candidate-02')):
        ASSETS[f'FR03_VineCurtain_{kind}'] = dict(zh=zh, kind='vines', palette=palette, build=lambda P, k=kind: fr03_curtain(P, k), limit=(2., .2, 3.),
            tex=1024, ver='v001', box=((-HALF_X, -HALF_Y, -3.), (HALF_X, HALF_Y, 0.)), base_z=round(TOP_Z - 3 * SC_MAX, 4), ground_z=-3., ref=ref,
            slot='D1_ForestEdge_to_D2_ElderTree', minTier='high', clamp_max=.03, uv_shape='CONVEX', no_collision=True,
            origin='centre of the hang line (top); everything hangs below z = 0', note=NOTE[kind] + COMMON)
