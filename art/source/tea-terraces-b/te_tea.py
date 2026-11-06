"""TE02 pruned tea bushes: woody frame (baked atlas) + leaf cards (shared alpha-clipped leaf atlas) + vertex-colour wind weights.

Leaf atlas (TE02_Shared/Textures/TE02_LeafCards_*.png, 2048, four 1024 cells), rendered here from real leaf geometry:
  cell 0 (left top)     old dense foliage, dark glossy leaves, a few yellowed ones
  cell 1 (right top)    the plucking table: mature leaves with upright young shoots (a bud and two pale yellow-green leaves)
  cell 2 (left bottom)  mixed side foliage
  cell 3 (right bottom) left half: a side sprig; right half: an opaque leaf mass for the crown core
Cards carry outward 'spherical' normals (attribute leaf_n, applied after the LODs) so the crown shades as one soft mass.
Vertex colour 'Wind' (exported as the FBX colour layer): R wind weight 0 at the root -> 1 at the outer leaves, G per-card phase, B height 0..1.
"""
import bpy, bmesh, math, random
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix, noise
from ti_core import S, mesh, surface, socket
import ti_mats as tm
import cr_mats as cm
from cr_parts import rope, log, rbox

LEAF_DIR = Path(__file__).resolve().parents[2] / 'exports' / 'tea-terraces-b' / 'TE02_Shared' / 'v002' / 'Textures'   # v001 atlas stays in TE02_Shared/Textures
BOUND = .146   # half the 0.3 m cell, less a margin
CELLS = {0: (0., .5, .5, 1.), 1: (.5, .5, 1., 1.), 2: (0., 0., .5, .5), 3: (.5, 0., .75, .5), 4: (.775, .025, .975, .475)}   # u0, v0, u1, v1; 4 = opaque core mass


# ------------------------------------------------------------------ leaf atlas
def _leaf_mat(name):
    """Colour from per-leaf attributes: 'tone' (0 old dark .. 1 young yellow-green), 'cuv' leaf space (u across, v base->tip)."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    g = tm.G(m)
    tone = g.attr('tone', 'Fac'); C = g.attr('cuv'); cs = g.node('ShaderNodeSeparateXYZ'); g.link(C, cs.inputs[0])
    u, v = cs.outputs['X'], cs.outputs['Y']
    old = g.ramp(v, [(.0, (.022, .05, .024)), (.6, (.04, .085, .034)), (1., (.05, .1, .036))])
    mid = g.ramp(v, [(.0, (.05, .1, .03)), (.6, (.1, .17, .045)), (1., (.14, .21, .05))])
    young = g.ramp(v, [(.0, (.14, .21, .045)), (.7, (.27, .35, .075)), (1., (.35, .4, .1))])
    col = g.mix(g.maprange(tone, .0, .5), old, mid); col = g.mix(g.maprange(tone, .55, .95), col, young)
    yellowed = g.attr('yellow', 'Fac'); col = g.mix(yellowed, col, (.3, .26, .07))
    vein = g.maprange(g.math('ABSOLUTE', g.math('SUBTRACT', u, .5)), .035, .0)
    col = g.mix(g.math('MULTIPLY', vein, .45), col, (.3, .36, .12))
    rim = g.maprange(g.math('ABSOLUTE', g.math('SUBTRACT', u, .5)), .4, .5)
    col = g.mix(g.math('MULTIPLY', rim, .35), col, (.16, .22, .08))
    side = g.geo('Backfacing'); col = g.mix(g.math('MULTIPLY', side, .6), col, (.06, .12, .1))   # teal undersides
    ao = g.node('ShaderNodeAmbientOcclusion', only_local=True, samples=16); ao.inputs['Distance'].default_value = .05
    shade = g.ramp(ao.outputs['AO'], [(0, (.32, .34, .36)), (1, (1, 1, 1))])
    g.link(col, ao.inputs['Color'])
    col = g.mul(1., col, shade)
    em = g.node('ShaderNodeEmission'); g.link(col, em.inputs['Color'])
    out = g.node('ShaderNodeOutputMaterial'); g.link(em.outputs[0], out.inputs['Surface'])
    return m


def _normal_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); g = tm.G(m)
    n = g.geo('Normal'); back = g.geo('Backfacing')
    flip = g.vmath('SCALE', n); nd = flip.node; nd.inputs['Scale'].default_value = -1
    sel = g.node('ShaderNodeMix', data_type='VECTOR', clamp_factor=True); g._in(sel.inputs['Factor'], back)
    g.link(n, tm._ident(sel.inputs, 'A_Vector')); g.link(flip, tm._ident(sel.inputs, 'B_Vector'))
    c = g.vmath('ADD', g.vmath('MULTIPLY', tm._ident(sel.outputs, 'Result_Vector'), (.5, .5, .5)), (.5, .5, .5))
    em = g.node('ShaderNodeEmission'); g.link(c, em.inputs['Color'])
    out = g.node('ShaderNodeOutputMaterial'); g.link(em.outputs[0], out.inputs['Surface'])
    return m


def _leaf(verts, faces, attrs, base, direction, L, W, tone, yellow, cup=.18, curl=.08, R=None):
    """One tea leaf: elliptic, pointed tip, serrated rim, cupped along the midrib, tip curling down."""
    d = Vector(direction).normalized(); up = Vector((0, 0, 1))
    side = d.cross(up)
    if side.length < 1e-4: side = Vector((1, 0, 0))
    side.normalize(); nrm = side.cross(d).normalized()
    if nrm.z < 0: nrm = -nrm
    nu, nv = 4, 9; k0 = len(verts)
    tip = base + d * L
    if max(abs(base.x), abs(base.y), abs(tip.x), abs(tip.y)) + W > BOUND: return False
    for j in range(nv + 1):
        v = j / nv
        w = W * math.sin(math.pi * min(v, .999) ** .85) ** .9 * (1 - .25 * v)
        for i in range(nu + 1):
            u = i / nu; x = (u - .5) * 2
            ser = .06 * W * (math.sin(v * 48) > .2) * (abs(x) > .95)
            p = base + d * (L * v) + side * (x * (w + ser)) + nrm * (cup * W * x * x - curl * L * v * v)
            verts.append(tuple(p)); attrs['cuv'].append((u, v, 0)); attrs['tone'].append(tone); attrs['yellow'].append(yellow)
    for j in range(nv):
        for i in range(nu):
            a = k0 + j * (nu + 1) + i
            faces.append((a, a + 1, a + nu + 2, a + nu + 1))
    return True


def _sprig_mesh(name, kind, R):
    """Leaves seen from above for one atlas cell, inside a 0.3 m square centred on the origin."""
    verts, faces = [], []; attrs = {'cuv': [], 'tone': [], 'yellow': []}
    stems = []
    def twig(start, ang, n, tone_lo, tone_hi, L0, young_tip, length):
        p = Vector(start); d = Vector((math.cos(ang), math.sin(ang), .15)); pts = [p.copy()]
        for k in range(n):
            t = k / max(1, n - 1)
            step = length / n; d = (d + Vector((R.uniform(-.25, .25), R.uniform(-.25, .25), .02))).normalized(); q = p + d * step
            if max(abs(q.x), abs(q.y)) > BOUND - .01: break
            p = q; pts.append(p.copy())
            for sgn in (-1, 1):
                if R.random() < .03: continue   # v002: almost every node carries its pair of leaves (was 12% skipped)
                a = math.atan2(d.y, d.x) + sgn * R.uniform(.55, 1.05)
                L = L0 * R.uniform(.8, 1.15) * (1 - .25 * t); tone = R.uniform(tone_lo, tone_hi) + .2 * t * (tone_hi - tone_lo)
                _leaf(verts, faces, attrs, p, (math.cos(a), math.sin(a), R.uniform(.05, .35)), L, L * .36, min(1., tone), 1. if R.random() < .015 else 0., R=R)   # v002: fewer yellowed leaves (was 4%), the denser cells showed them as noise
        if len(pts) > 1: stems.append(pts)
        if young_tip:
            # the shoot: a furled bud and two pale leaves standing up
            for k, (a, s) in enumerate(((0, .5), (1.2, .9), (-1.1, .8))):
                ang2 = math.atan2(d.y, d.x) + a
                L = .035 * s + .015; _leaf(verts, faces, attrs, p + d * .005, (math.cos(ang2) * .6, math.sin(ang2) * .6, .8 if k == 0 else .35), L, L * (.22 if k == 0 else .33), 1., 0., cup=.4)
    # v002: more and smaller leaves per cell, spread to the cell corners, so a card reads as a closed clump of foliage
    if kind == 0:      # old dense
        for k in range(22): twig((R.uniform(-.125, .125), R.uniform(-.125, .125), R.uniform(0, .03)), R.uniform(0, 6.3), 5, .0, .35, .06, False, .19)
    elif kind == 1:    # plucking table with shoots
        for k in range(18): twig((R.uniform(-.12, .12), R.uniform(-.12, .12), 0), R.uniform(0, 6.3), 4, .12, .5, .058, False, .15)
        for k in range(8): twig((R.uniform(-.1, .1), R.uniform(-.1, .1), .04), R.uniform(0, 6.3), 2, .6, .9, .05, True, .06)
    elif kind == 2:    # mixed side
        for k in range(20): twig((R.uniform(-.125, .125), R.uniform(-.125, .125), R.uniform(0, .03)), R.uniform(0, 6.3), 5, .05, .5, .058, R.random() < .2, .19)
    else:              # side sprig: a main branch and two side branches, fanning up the cell
        twig((0, -.13, 0), math.pi / 2, 8, .15, .6, .056, True, .25)
        twig((-.05, -.11, 0), math.pi / 2 + .45, 6, .15, .55, .052, False, .2)
        twig((.05, -.11, 0), math.pi / 2 - .45, 6, .15, .55, .052, False, .2)
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    for nm, vals in attrs.items():
        if nm == 'cuv':
            at = me.attributes.new(nm, 'FLOAT_VECTOR', 'POINT'); at.data.foreach_set('vector', [c for v in vals for c in v])
        else:
            at = me.attributes.new(nm, 'FLOAT', 'POINT'); at.data.foreach_set('value', vals)
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me)
    st = []
    for pts in stems:
        cu = bpy.data.curves.new(name + '_stem', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = .0024; cu.bevel_resolution = 1
        sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
        for q, pt in zip(sp.points, pts): q.co = (*pt, 1)
        so = bpy.data.objects.new(name + '_stem', cu); st.append(so)
    return o, st


def leaf_atlas(tex_dir, size=2048):
    """Render the four cells top-down (orthographic, transparent film) into BaseColor+alpha and a tangent-space normal map, then pad the colours past the alpha edge."""
    tex_dir.mkdir(parents=True, exist_ok=True)
    out_c = tex_dir / 'TE02_LeafCards_BaseColor.png'; out_n = tex_dir / 'TE02_LeafCards_Normal.png'
    if out_c.exists() and out_n.exists(): return out_c, out_n
    scene = bpy.context.scene   # background mode has no window to switch scenes in: borrow the current one and put it back
    keep = dict(engine=scene.render.engine, ft=scene.render.film_transparent, vt=scene.view_settings.view_transform, rx=scene.render.resolution_x, ry=scene.render.resolution_y, fs=scene.render.filter_size, cam=scene.camera)
    scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = 16; scene.cycles.use_denoising = False
    scene.render.film_transparent = True; scene.view_settings.view_transform = 'Standard'; scene.render.resolution_x = scene.render.resolution_y = size // 2
    scene.render.image_settings.file_format = 'PNG'; scene.render.image_settings.color_mode = 'RGBA'; scene.render.filter_size = .8
    cam = bpy.data.objects.new('LeafCam', bpy.data.cameras.new('LeafCam')); scene.collection.objects.link(cam); scene.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = .3; cam.location = (0, 0, 1); cam.rotation_euler = (0, 0, 0)
    lm, nm_ = _leaf_mat('LeafAtlas_Colour'), _normal_mat('LeafAtlas_Normal')
    stem_m = bpy.data.materials.new('LeafAtlas_Stem'); stem_m.use_nodes = True
    sn = stem_m.node_tree.nodes; sn.clear(); e = sn.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (.07, .045, .02, 1); o_ = sn.new('ShaderNodeOutputMaterial'); stem_m.node_tree.links.new(e.outputs[0], o_.inputs[0])
    stem_n = _normal_mat('LeafAtlas_StemN')
    R = random.Random(2002)
    cells = {}
    import tempfile
    tmp = Path(tempfile.gettempdir()) / 'te02_cells'; tmp.mkdir(exist_ok=True)
    for kind in range(4):
        o, st = _sprig_mesh(f'Sprig_{kind}', kind, R); scene.collection.objects.link(o)
        for s_ in st: scene.collection.objects.link(s_)
        for pas, m, sm in (('c', lm, stem_m), ('n', nm_, stem_n)):
            o.data.materials.clear(); o.data.materials.append(m)
            for s_ in st: s_.data.materials.clear(); s_.data.materials.append(sm)
            scene.render.filepath = str(tmp / f'{kind}_{pas}.png'); bpy.ops.render.render(write_still=True)
            im = bpy.data.images.load(scene.render.filepath); cells[(kind, pas)] = np.array(im.pixels[:], np.float32).reshape(size // 2, size // 2, 4); bpy.data.images.remove(im)
        bpy.data.objects.remove(o); [bpy.data.objects.remove(s_) for s_ in st]
    h = size // 2
    col = np.zeros((size, size, 4), np.float32); nrm = np.zeros((size, size, 4), np.float32); nrm[..., :] = (.5, .5, 1, 1)
    place = {0: (h, 0), 1: (h, h), 2: (0, 0), 3: (0, h)}     # (row0, col0) in numpy rows from the bottom (Blender pixels start bottom-left)
    for kind, (r0, c0) in place.items():
        c = cells[(kind, 'c')]; n = cells[(kind, 'n')]
        if kind == 3:     # left half of the cell: the sprig, squeezed; right half: an opaque mass made from the dense cell
            sprig = c[:, ::2]; sn_ = n[:, ::2]
            col[r0:r0 + h, c0:c0 + h // 2] = sprig; nrm[r0:r0 + h, c0:c0 + h // 2] = np.where(sprig[..., 3:4] > .5, sn_, nrm[r0:r0 + h, c0:c0 + h // 2])
            dense = cells[(0, 'c')][:, ::2].copy(); dn = cells[(0, 'n')][:, ::2]
            under = np.array([.03, .065, .028, 1.], np.float32)
            a = dense[..., 3:4]; dense = dense * a + under * (1 - a); dense[..., 3] = 1
            col[r0:r0 + h, c0 + h // 2:c0 + h] = dense; nrm[r0:r0 + h, c0 + h // 2:c0 + h] = np.where(a > .5, dn, (.5, .5, 1, 1))
        else:
            col[r0:r0 + h, c0:c0 + h] = c; nrm[r0:r0 + h, c0:c0 + h] = np.where(c[..., 3:4] > .5, n, (.5, .5, 1, 1))
    # alpha test at 0.5: push the colours outward so mip levels do not bleed the background in
    a = col[..., 3] > .5; rgb = col[..., :3].copy(); filled = a.copy()
    for _ in range(24):
        acc = np.zeros_like(rgb); cnt = np.zeros(a.shape, np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sh = np.roll(np.roll(filled, dy, 0), dx, 1); acc += np.roll(np.roll(rgb, dy, 0), dx, 1) * sh[..., None]; cnt += sh
        grow = (~filled) & (cnt > 0); rgb[grow] = acc[grow] / cnt[grow][:, None]; filled |= grow
    rgb[~filled] = (.05, .09, .035)
    col[..., :3] = rgb; col[..., 3] = a.astype(np.float32)
    # the normal render is world space seen from +Z, which for a card lying in XY is its tangent space; leave linear
    def save(arr, path, srgb):
        im = bpy.data.images.new(path.stem, size, size, alpha=True, float_buffer=False)
        im.colorspace_settings.name = 'sRGB' if srgb else 'Non-Color'
        im.pixels.foreach_set(arr.ravel()); im.filepath_raw = str(path); im.file_format = 'PNG'; im.save()
        return im
    save(col, out_c, True); save(nrm, out_n, False)
    scene.render.engine = keep['engine']; scene.render.film_transparent = keep['ft']; scene.view_settings.view_transform = keep['vt']
    scene.render.resolution_x, scene.render.resolution_y, scene.render.filter_size, scene.camera = keep['rx'], keep['ry'], keep['fs'], keep['cam']
    bpy.data.objects.remove(cam)
    for m in (lm, nm_, stem_m, stem_n): bpy.data.materials.remove(m)
    return out_c, out_n


def leaf_material(tex_c, tex_n):
    m = bpy.data.materials.new('TE02_LeafCards'); m.use_nodes = True; nt = m.node_tree
    bs = nt.nodes['Principled BSDF']
    ic = nt.nodes.new('ShaderNodeTexImage'); ic.image = bpy.data.images.load(str(tex_c), check_existing=True)
    inn = nt.nodes.new('ShaderNodeTexImage'); inn.image = bpy.data.images.load(str(tex_n), check_existing=True); inn.image.colorspace_settings.name = 'Non-Color'
    nmap = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(inn.outputs['Color'], nmap.inputs['Color']); nt.links.new(nmap.outputs[0], bs.inputs['Normal'])
    nt.links.new(ic.outputs['Color'], bs.inputs['Base Color'])
    rnd = nt.nodes.new('ShaderNodeMath'); rnd.operation = 'ROUND'; nt.links.new(ic.outputs['Alpha'], rnd.inputs[0]); nt.links.new(rnd.outputs[0], bs.inputs['Alpha'])
    bs.inputs['Roughness'].default_value = .7; bs.inputs['Specular IOR Level'].default_value = .16
    bs.inputs['Subsurface Weight'].default_value = .0
    try: m.blend_method = 'CLIP'
    except Exception: pass
    try: m.surface_render_method = 'DITHERED'
    except Exception: pass
    m.use_backface_culling = False
    # identity nodes so the bake pass can treat it like the others if ever routed (own_uv keeps it out of the atlas)
    tm.MAT_INFO[m.name] = {'slot': 'LeafCards', 'own_uv': True}
    return m


# ------------------------------------------------------------------ the bush
def palette():
    P = {}
    P['bark'] = cm.wood('Tea_Bark', (.07, .055, .04), (.23, .19, .14), ground_h=.15, grey=.6, moss=True, moss_amt=.5)
    P['soil'] = __import__('te_terrace').tread_soil('Bush_Soil')
    P['litter'] = cm.weed_leaf('Leaf_Litter', (.06, .045, .02), (.14, .09, .035), (.2, .15, .06))
    P['stone'] = cm.stone('Base_Pebble', light=(.29, .265, .225), dark=(.12, .108, .088), moss=.4)
    c, n = leaf_atlas(LEAF_DIR); P['leaves'] = leaf_material(c, n)
    return P


class Crown:
    """Pruned crown: a flat plucking table on top, rounded shoulders, an open underside showing the stems."""
    def __init__(self, H, rx, ry, z_under, shoulder, seed, skew=(0., 0.), lobes=.06):
        self.H, self.rx, self.ry, self.zu, self.sh, self.seed, self.skew, self.lobes = H, rx, ry, z_under, shoulder, seed, skew, lobes

    def radius(self, a, z):
        """Plan radius at angle a and height z (0 at the underside edge, widening to the shoulder, then rounding into the table)."""
        n = 1 + self.lobes * noise.noise(Vector((math.cos(a) * 1.6 + self.seed, math.sin(a) * 1.6, z * 2))) + .4 * self.lobes * math.sin(3 * a + self.seed)
        base = 1 / math.sqrt((math.cos(a) / self.rx) ** 2 + (math.sin(a) / self.ry) ** 2)
        t = (z - self.zu) / max(self.H - self.zu, .01)
        if t < 0: return 0.
        prof = (.62 + .38 * math.sin(min(1., t / .55) * math.pi / 2)) if t < .55 else 1.
        top = self.H - self.sh
        if z > top:
            k = (z - top) / self.sh; prof *= math.sqrt(max(0., 1 - k * k)) * .45 + .55 * (1 - k ** 3)
        return base * n * prof

    def centre(self, z):
        t = (z - self.zu) / max(self.H - self.zu, .01)
        return Vector((self.skew[0] * t, self.skew[1] * t, z))

    def point(self, a, z):
        r = self.radius(a, z); c = self.centre(z)
        return Vector((c.x + r * math.cos(a), c.y + r * math.sin(a), z))

    def normal(self, a, z):
        e = .02
        p0 = self.point(a, z); pa = self.point(a + e, z); pz = self.point(a, min(z + e, self.H))
        n = (pa - p0).cross(pz - p0)
        if n.length < 1e-6 or z > self.H - .02: return Vector((0, 0, 1))
        n.normalize()
        if n.dot(Vector((math.cos(a), math.sin(a), 0))) < 0: n = -n
        return n


def card(verts, faces, uvs, cols, nrms, masks, c, n, size, cell, R, roll=None, lift=.0, flat=False, wind=1., phase=0., H=1., mask=1, bend=.15):
    """A leaf card: a quad split once along its length so it can bow (3 verts wide x 2 long), facing roughly along n."""
    n = Vector(n).normalized()
    t = n.cross(Vector((0, 0, 1)) if abs(n.z) < .95 else Vector((1, 0, 0))).normalized(); b = n.cross(t)
    rr = R.uniform(0, math.tau) if roll is None else roll
    t, b = t * math.cos(rr) + b * math.sin(rr), -t * math.sin(rr) + b * math.cos(rr)
    u0, v0, u1, v1 = CELLS[cell]
    k = len(verts); half = size / 2
    for j, y in enumerate((-1, 0, 1)):
        for i, x in enumerate((-1, 0, 1)):
            p = Vector(c) + t * (x * half) + b * (y * half) + n * (-bend * size * (x * x + y * y) * .5 + lift)
            verts.append(tuple(p)); uvs.append((u0 + (u1 - u0) * (x + 1) / 2, v0 + (v1 - v0) * (y + 1) / 2))
            rad = (Vector(p) - Vector((0, 0, H * .45)))
            cols.append((min(1., wind * (.55 + .45 * min(1., rad.length / .6))), phase, max(0., min(1., p[2] / max(H, .01))), 1.))
            nrms.append(None)
    for j in range(2):
        for i in range(2):
            a = k + j * 3 + i; faces.append((a, a + 1, a + 4, a + 3)); masks.append(mask)


def tea_bush(P, cfg):
    """cfg: H, rx, ry, z_under, shoulder, skew, stems, seed, cards, lobes."""
    cfg['leaf_mat'] = P['leaves']
    R = random.Random(cfg['seed']); H = cfg['H']
    C = Crown(H, cfg['rx'], cfg['ry'], cfg['z_under'], cfg['shoulder'], cfg['seed'] * .37, cfg.get('skew', (0, 0)), cfg.get('lobes', .06))
    # soil mound and litter at the root
    def mound(u, v):
        a = u * math.tau; r = .3 * v * (1 + .12 * noise.noise(Vector((math.cos(a) * 2, math.sin(a) * 2, cfg['seed']))))
        return (r * math.cos(a) * 1.15, r * math.sin(a), .07 * (1 - v * v) ** 1.4)
    surface('Root_Mound', 20, 5, mound, P['soil'], closed_u=True, grain='z')
    for k in range(7):
        a = R.uniform(0, 6.3); r = R.uniform(.12, .3); sz = R.uniform(.03, .06)
        rbox('Root_Pebble', (r * math.cos(a), r * math.sin(a), .01 + sz * .1), (sz, sz * .8, sz * .5), P['stone'], r=sz * .3, amp=sz * .1, seed=k, div=sz * .45, rot=(0, 0, a), detail=2)
    # woody frame: stems from a gnarled crown base, splitting twice, ending under the leaf shell
    stems = []
    def inside(p):
        # above the crown underside a branch may not reach past 80 % of the crown radius, so no bare tips poke through the foliage
        # below the underside the allowed radius widens linearly from the root, so stems lean out evenly and never fold back
        zu = cfg['z_under'] + .02
        c = C.centre(max(p.z, zu)); dv = Vector((p.x - c.x, p.y - c.y, 0)); r = dv.length; a = math.atan2(dv.y, dv.x)
        if p.z >= zu: lim = .8 * C.radius(a, p.z)
        else: lim = .07 + (.8 * C.radius(a, zu) - .07) * max(0., p.z) / zu
        return p if r <= lim or r < 1e-6 else Vector((c.x, c.y, p.z)) + dv * (lim / r)
    def grow(p, d, r, depth, length):
        pts = [p.copy()]; rads = [r]
        steps = 5
        for k in range(steps):
            d = (d + Vector((R.uniform(-.18, .18), R.uniform(-.18, .18), R.uniform(0, .12)))).normalized()
            q = inside(p + d * (length / steps))
            if (q - p).length > 1e-4: d = (q - p).normalized()
            p = q; pts.append(p.copy()); rads.append(r * (1 - .35 * (k + 1) / steps))
        stems.append((pts, rads, depth))
        if depth < 2 and p.z < H - .2:
            for s in range(R.choice((2, 2, 3))):
                a = math.atan2(d.y, d.x) + R.uniform(-.9, .9); spread = R.uniform(.35, .7)
                nd = Vector((math.cos(a) * spread, math.sin(a) * spread, 1)).normalized()
                grow(p, nd, rads[-1] * .78, depth + 1, length * R.uniform(.62, .8))
    n = cfg['stems']
    for k in range(3):
        a = k / 3 * math.tau + R.uniform(-.4, .4)
        rope('Stump', [(math.cos(a) * .05, math.sin(a) * .05, -.01), (math.cos(a) * .03, math.sin(a) * .03, .06), (math.cos(a) * .045, math.sin(a) * .045, .12)], R.uniform(.04, .05), P['bark'], ply=2, tw=40., seg=10, amp=.14, grain='z', detail=0)
    for k in range(n):
        a = k / n * math.tau + R.uniform(-.3, .3); sp = R.uniform(.8, 1.2)
        grow(Vector((math.cos(a) * .05, math.sin(a) * .05, .09)), Vector((math.cos(a) * sp, math.sin(a) * sp, 1)).normalized(), R.uniform(.024, .033), 0, (cfg['z_under'] + .08) * R.uniform(.75, .95))
    for i, (pts, rads, depth) in enumerate(stems):
        pts = [Vector((p.x, p.y, min(p.z, H - .12))) for p in pts]
        rope('Stem', [tuple(p) for p in pts], rads[0], P['bark'], ply=1, tw=0., seg=9 if depth == 0 else 7, amp=.08, radius_fn=lambda t, r0=rads[0], r1=rads[-1]: (1 - t) + t * r1 / r0, grain='z', detail=0 if depth < 2 else 1)
    # leaf cards on the crown shell; inner layer, core mass, plucking table
    verts, faces, uvs, cols, nrms, masks = [], [], [], [], [], []
    def shell_points(count, inset, zlo, zhi, seed):
        Rs = random.Random(seed); out = []
        for _ in range(count * 30):
            if len(out) >= count: break
            a = Rs.uniform(0, math.tau); z = Rs.uniform(zlo, zhi)
            p = C.point(a, z); r = C.radius(a, z)
            if r < .05: continue
            p = C.centre(z) + (p - C.centre(z)) * (1 - inset / max(r, .05))
            if all((p - q).length > cfg['spacing'] * (1 - inset * .6) for q, _, _ in out): out.append((p, a, z))
        return out
    top_z = H - cfg['shoulder']
    shoot_ranges = []
    for lod_mask, scale, count_k, seed in ((1, 1., 1., 11), (2, 1.4, .48, 12), (4, 1.9, .2, 13)):
        sink = .03 + (scale - 1) * .1   # larger far-LOD cards sit deeper so they keep inside the LOD0 silhouette
        sp = cfg['spacing']; cfg['spacing'] = sp * math.sqrt(1 / count_k)
        # outer shell: sides and shoulders
        # v003: down to the skirt edge (was +.11); the larger LOD1/LOD2 cards start higher so their lower edge stays above the ground
        for p, a, z in shell_points(int(cfg['cards'] * count_k), sink, cfg['z_under'] + .05 + (scale - 1) * .22, top_z + cfg['shoulder'] * .7, seed):
            nrm = C.normal(a, z); up = (z - cfg['z_under']) / (H - cfg['z_under'])
            cell = 2 if up > .45 else 0
            if R.random() < .25: cell = 3
            card(verts, faces, uvs, cols, nrms, masks, p, (nrm + Vector((0, 0, .35))).normalized(), R.uniform(.21, .28) * scale, cell, R, wind=1., phase=R.random(), H=H, mask=lod_mask)   # v003: larger, more overlap (was .19-.25)
        # plucking table: cards lying nearly flat on top, shoots up
        for p, a, z in shell_points(int(cfg['top_cards'] * count_k), .02, top_z + cfg['shoulder'] * .55, H - .005, seed + 50):
            card(verts, faces, uvs, cols, nrms, masks, p, (Vector((R.uniform(-.25, .25), R.uniform(-.25, .25), 1))).normalized(), R.uniform(.19, .25) * scale, 1, R, wind=1., phase=R.random(), H=H, mask=lod_mask, bend=.1)
        # inner layer: darker old foliage so the crown never reads hollow
        for p, a, z in shell_points(int(cfg['cards'] * .6 * count_k), .12, cfg['z_under'] + .08 + (scale - 1) * .22, top_z, seed + 90):   # v002: fuller inner layer (was .35, inset .16)
            card(verts, faces, uvs, cols, nrms, masks, p, (C.normal(a, z) + Vector((0, 0, .2))).normalized(), R.uniform(.24, .3) * scale, 0, R, wind=.7, phase=R.random(), H=H, mask=lod_mask)
        if lod_mask == 1:
            # young shoots: smaller sprig cards leaning back about 50 deg so the table reads tufted from eye level without a dark upright fringe from behind
            s0 = len(verts)
            for p, a, z in shell_points(int(cfg['top_cards'] * .4), .0, H - .05, H - .005, seed + 70):
                b = a + R.uniform(-1, 1)
                card(verts, faces, uvs, cols, nrms, masks, p + Vector((0, 0, .03)), (math.cos(b) * .75, math.sin(b) * .75, R.uniform(.55, .8)), R.uniform(.14, .18), 3, R,
                     roll=R.uniform(-.25, .25), wind=1., phase=R.random(), H=H, mask=3, bend=.05)
            shoot_ranges.append((s0, len(verts)))
        cfg['spacing'] = sp
    # outward normals for every card vertex: from a point low in the crown, flattened so the table faces up
    cz = cfg['z_under'] + (H - cfg['z_under']) * .3
    leaf_n = []
    in_shoot = set(i for a0, a1 in shoot_ranges for i in range(a0, a1))
    for i, p in enumerate(verts):
        q = Vector(p) - Vector((0, 0, cz)); q.x /= cfg['rx']; q.y /= cfg['ry']; q.z /= (H - cz) * .8
        q = q.normalized()
        if i in in_shoot: q = (q * .35 + Vector((0, 0, 1))).normalized()   # shoots shade like the table they stand on, from either side
        leaf_n.append(tuple(q))
    o = mesh('Leaf_Cards', verts, faces, cfg['leaf_mat'], grain='z', detail=0, group='Leaves')
    me = o.data
    uv = me.uv_layers[0]
    for poly in me.polygons:
        for li in poly.loop_indices: uv.data[li].uv = uvs[me.loops[li].vertex_index]
    ca = me.color_attributes.new('Wind', 'FLOAT_COLOR', 'POINT'); ca.data.foreach_set('color', [c for v in cols for c in v])
    at = me.attributes.new('leaf_n', 'FLOAT_VECTOR', 'POINT'); at.data.foreach_set('vector', [c for v in leaf_n for c in v])
    lm = me.attributes.new('lod_mask', 'INT', 'FACE'); lm.data.foreach_set('value', masks)
    # crown core: a lumpy closed mass just inside the inner layer, mapped onto the opaque cell
    u0, v0, u1, v1 = CELLS[4]
    def core(u, v):
        a = u * math.tau; z = cfg['z_under'] + .1 + (top_z - cfg['z_under'] - .05) * v
        r = C.radius(a, z) * .62; c = C.centre(z)
        return (c.x + r * math.cos(a), c.y + r * math.sin(a), z)
    co = surface('Crown_Core', 14, 4, core, cfg['leaf_mat'], uvfn=lambda u, v: (u0 + (u1 - u0) * u, v0 + (v1 - v0) * v), closed_u=False, grain='z', group='Leaves')
    cme = co.data
    ca = cme.color_attributes.new('Wind', 'FLOAT_COLOR', 'POINT'); ca.data.foreach_set('color', [c for vv in cme.vertices for c in (.35, .5, vv.co.z / H, 1.)])
    nn = []
    for vv in cme.vertices:
        q = vv.co - Vector((0, 0, cz)); q.x /= cfg['rx']; q.y /= cfg['ry']; q.z /= (H - cz); nn.append(tuple(q.normalized()))
    at = cme.attributes.new('leaf_n', 'FLOAT_VECTOR', 'POINT'); at.data.foreach_set('vector', [c for v in nn for c in v])
    lm = cme.attributes.new('lod_mask', 'INT', 'FACE'); lm.data.foreach_set('value', [7] * len(cme.polygons))
    # stems: wind 0 at the root rising to 0.4 under the crown
    for o2 in S['parts']:
        if o2.type == 'MESH' and o2.get('group', 'Main') == 'Main' and not o2.data.color_attributes:
            me2 = o2.data; mw = o2.matrix_world
            ca = me2.color_attributes.new('Wind', 'FLOAT_COLOR', 'POINT')
            ca.data.foreach_set('color', [c for vv in me2.vertices for c in (min(.4, max(0., (mw @ vv.co).z / H * .5)), 0., (mw @ vv.co).z / H, 1.)])
    fit(cfg)
    # collision: an octagonal prism around the crown below shoulder height, so a character brushes the bush instead of walking through it
    r0 = cfg['collide_r']; hc = cfg['H'] * .75; vs = []
    for z in (0., hc):
        for k in range(8): a = k / 8 * math.tau + math.pi / 8; vs.append((r0 * math.cos(a), r0 * math.sin(a), z))
    fs = [tuple(range(7, -1, -1)), tuple(range(8, 16))] + [(k, (k + 1) % 8, 8 + (k + 1) % 8, 8 + k) for k in range(8)]
    S['collision_mesh'] = (vs, fs)
    S['bush'] = cfg


def fit(cfg):
    """Scale the finished bush about its root so the widest plan extent is exactly cfg['W'] and the top is cfg['H']."""
    import ti_pipeline as pl
    bpy.context.view_layer.update()
    # LOD0 content only: the larger LOD1/LOD2 cards are not what the size refers to
    pts = []
    for o in S['parts']:
        if o.type != 'MESH': continue
        me = o.data; mw = o.matrix_world
        if o.name.startswith('Leaf_Cards'):
            m = me.attributes['lod_mask'].data
            ids = {v for f in me.polygons if m[f.index].value & 1 for v in f.vertices}
        else: ids = range(len(me.vertices))
        pts += [mw @ me.vertices[i].co for i in ids]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))); hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    w = max(hi.x - lo.x, hi.y - lo.y); sx = cfg['W'] / w; sz = cfg['H'] / hi.z
    cx, cy = (hi.x + lo.x) / 2, (hi.y + lo.y) / 2
    M = Matrix.Diagonal((sx, sx, sz, 1.)) @ Matrix.Translation((-cx, -cy, 0))
    for o in S['parts']: o.matrix_world = M @ o.matrix_world
    bpy.context.view_layer.update()
    S['fit_scale'] = (round(sx, 4), round(sz, 4))


TE02 = {
    # v003 (lush): skirt lowered (z_under .30/.25/.40 -> .14/.12/.20) so the foliage reaches near the ground and hides most of the stems,
    # cards x1.35 (top x1.2) and spacing x0.9 against v002 (322/117/.061, 308/109/.061, 350/91/.064), lumpier outline (lobes +.03).
    # v002 had cards x1.4 / spacing x0.85 against v001 (230/90/.072, 220/84/.072, 250/70/.075).
    'TE02_Round': dict(W=1.2, collide_r=.42, H=.9, rx=.6, ry=.56, z_under=.14, shoulder=.17, skew=(0, 0), stems=8, seed=21, cards=435, top_cards=140, spacing=.055, lobes=.08),
    'TE02_Wide': dict(W=1.2, collide_r=.42, H=.8, rx=.6, ry=.47, z_under=.12, shoulder=.14, skew=(.06, -.02), stems=8, seed=22, cards=416, top_cards=131, spacing=.055, lobes=.12),
    'TE02_Tall': dict(W=1.2, collide_r=.42, H=1.1, rx=.56, ry=.53, z_under=.2, shoulder=.22, skew=(-.03, .02), stems=7, seed=23, cards=472, top_cards=109, spacing=.058, lobes=.13),
}
