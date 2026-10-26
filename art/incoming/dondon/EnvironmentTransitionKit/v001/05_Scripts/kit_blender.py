"""Shared Blender helpers for the Environment Transition Kit - NOT YET RUN (used from PHASE 2 modelling onwards).

Safety: every script calls start_session() first.  It refuses to run inside a Blender session that
has a file open, never calls read_factory_settings(), and every write goes through kit_path(),
which refuses paths outside Environment_Transition_Kit/.
"""
import math, os, random
from pathlib import Path
import bpy
from mathutils import Vector, noise
import kit_spec as K

SCRIPTS = Path(__file__).resolve().parent
KIT_DIR = SCRIPTS.parent
TEX_DIR = KIT_DIR / '03_Textures'


# ---- safety ------------------------------------------------------------------------------------
def kit_path(*parts):
    p = (KIT_DIR.joinpath(*parts)).resolve()
    root = str(KIT_DIR.resolve())
    if not (str(p) == root or str(p).startswith(root + os.sep)):
        raise RuntimeError('Refusing to write outside the kit: %s' % p)
    return p


def new_output(*parts):
    """Path for a new deliverable; refuses to overwrite (versioning instead of overwriting)."""
    p = kit_path(*parts)
    if p.exists():
        raise SystemExit('EXISTS (not overwritten, use a new version): %s' % p)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def start_session():
    if bpy.data.filepath:
        raise SystemExit('Refusing to run: this Blender session already has a file open (%s). Use a fresh background instance.' % bpy.data.filepath)
    for ob in list(bpy.data.objects):          # startup-file Cube/Camera/Light only
        bpy.data.objects.remove(ob, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.cameras, bpy.data.lights, bpy.data.materials):
        for d in list(coll):
            if d.users == 0: coll.remove(d)
    for c in list(bpy.data.collections):                 # empty startup 'Collection'
        if not c.all_objects and not c.children: bpy.data.collections.remove(c)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'; scene.unit_settings.scale_length = 1.0
    print('SESSION filepath=%r blender=%s kit=%s' % (bpy.data.filepath, bpy.app.version_string, KIT_DIR), flush=True)
    return scene


def open_kit_file(path):
    p = kit_path(path) if not isinstance(path, Path) else path.resolve()
    kit_path(p)
    if bpy.data.filepath:
        raise SystemExit('Refusing to open over another open file.')
    bpy.ops.wm.open_mainfile(filepath=str(p))
    assert Path(bpy.data.filepath).resolve() == p
    print('OPENED kit file', p, flush=True)


# ---- node helpers --------------------------------------------------------------------------------
def sock(socks, ident):
    for s in socks:
        if s.identifier == ident: return s
    raise KeyError(ident)


class NB:
    """Tiny node-tree builder."""

    def __init__(self, mat):
        self.nt = mat.node_tree; self.n = self.nt.nodes; self.l = self.nt.links

    def node(self, kind, **props):
        nd = self.n.new(kind)
        for k, v in props.items(): setattr(nd, k, v)
        return nd

    def link(self, a, b): self.l.new(a, b)

    def val(self, x):
        nd = self.node('ShaderNodeValue'); nd.outputs[0].default_value = x; return nd.outputs[0]

    def math(self, op, a, b=None, c=None, clamp=False):
        nd = self.node('ShaderNodeMath', operation=op, use_clamp=clamp)
        for i, x in enumerate((a, b, c)):
            if x is None: continue
            if isinstance(x, (int, float)): nd.inputs[i].default_value = x
            else: self.link(x, nd.inputs[i])
        return nd.outputs[0]

    def maprange(self, x, a, b, c=0.0, d=1.0, smooth=False):
        nd = self.node('ShaderNodeMapRange'); nd.interpolation_type = 'SMOOTHSTEP' if smooth else 'LINEAR'; nd.clamp = True
        self.link(x, nd.inputs['Value']); nd.inputs['From Min'].default_value = a; nd.inputs['From Max'].default_value = b
        nd.inputs['To Min'].default_value = c; nd.inputs['To Max'].default_value = d
        return nd.outputs['Result']

    def mix_rgb(self, fac, a, b):
        nd = self.node('ShaderNodeMix'); nd.data_type = 'RGBA'
        for s, x in ((sock(nd.inputs, 'Factor_Float'), fac), (sock(nd.inputs, 'A_Color'), a), (sock(nd.inputs, 'B_Color'), b)):
            if isinstance(x, (int, float)): s.default_value = x
            elif isinstance(x, tuple): s.default_value = (*x[:3], 1.0)
            else: self.link(x, s)
        return sock(nd.outputs, 'Result_Color')

    def mix_f(self, fac, a, b):
        nd = self.node('ShaderNodeMix'); nd.data_type = 'FLOAT'
        for s, x in ((sock(nd.inputs, 'Factor_Float'), fac), (sock(nd.inputs, 'A_Float'), a), (sock(nd.inputs, 'B_Float'), b)):
            if isinstance(x, (int, float)): s.default_value = x
            else: self.link(x, s)
        return sock(nd.outputs, 'Result_Float')

    def ramp(self, fac, stops):
        nd = self.node('ShaderNodeValToRGB'); cr = nd.color_ramp
        cr.elements[0].position = stops[0][0]; cr.elements[0].color = (*stops[0][1], 1)
        cr.elements[1].position = stops[-1][0]; cr.elements[1].color = (*stops[-1][1], 1)
        for pos, col in stops[1:-1]:
            e = cr.elements.new(pos); e.color = (*col, 1)
        self.link(fac, nd.inputs['Fac']); return nd.outputs['Color']

    def torus(self, ru=1.0, rv=1.0, offset=(0.0, 0.0)):
        """4D torus coordinates of the UV square: any texture sampled with them tiles seamlessly."""
        tc = self.node('ShaderNodeTexCoord'); sep = self.node('ShaderNodeSeparateXYZ'); self.link(tc.outputs['UV'], sep.inputs['Vector'])
        a = self.math('MULTIPLY', self.math('ADD', sep.outputs['X'], offset[0]), 2 * math.pi)
        b = self.math('MULTIPLY', self.math('ADD', sep.outputs['Y'], offset[1]), 2 * math.pi)
        comb = self.node('ShaderNodeCombineXYZ')
        self.link(self.math('MULTIPLY', self.math('COSINE', a), ru), comb.inputs['X'])
        self.link(self.math('MULTIPLY', self.math('SINE', a), ru), comb.inputs['Y'])
        self.link(self.math('MULTIPLY', self.math('COSINE', b), rv), comb.inputs['Z'])
        return comb.outputs['Vector'], self.math('MULTIPLY', self.math('SINE', b), rv)

    def noise4(self, tor, scale, detail=6.0, rough=0.55, distortion=0.0):
        nd = self.node('ShaderNodeTexNoise'); nd.noise_dimensions = '4D'
        self.link(tor[0], nd.inputs['Vector']); self.link(tor[1], nd.inputs['W'])
        nd.inputs['Scale'].default_value = scale; nd.inputs['Detail'].default_value = detail
        nd.inputs['Roughness'].default_value = rough; nd.inputs['Distortion'].default_value = distortion
        return nd.outputs['Fac'], nd.outputs['Color']

    def voronoi4(self, tor, scale, feature='F1', randomness=1.0):
        nd = self.node('ShaderNodeTexVoronoi'); nd.voronoi_dimensions = '4D'; nd.feature = feature
        self.link(tor[0], nd.inputs['Vector']); self.link(tor[1], nd.inputs['W'])
        nd.inputs['Scale'].default_value = scale; nd.inputs['Randomness'].default_value = randomness
        return nd


# ---- materials -----------------------------------------------------------------------------------
LAYERS = ['DrySoil', 'WetSoil', 'Grass', 'Moss', 'Rock', 'PathGravel']
MASK_ORDER = [('PathGravel', 2), ('WetSoil', 0), ('Grass', 1), ('Moss', 3)]   # (layer, mask channel)
# Blend of each layer over the layers below it: v = mask + amp * (wR*R + wG*G + wB*B) of T_BlendNoise, then smoothstep(lo, hi, v).
# R = 10 cm, G = 30 cm, B = 4 cm noise.  Wet soil fades softly; grass, moss and gravel get crisper, irregular edges.
BLEND = {'PathGravel': ((0.5, 0.0, 0.5), 0.70, 0.78, 0.92), 'WetSoil': ((0.4, 0.6, 0.0), 0.55, 0.55, 0.97),
         'Grass': ((0.5, 0.2, 0.3), 0.70, 0.78, 0.92), 'Moss': ((0.6, 0.0, 0.4), 0.70, 0.80, 0.95)}


def tex_image(name, non_color):
    path = TEX_DIR / name
    img = bpy.data.images.get(name) or bpy.data.images.load(str(path), check_existing=True)
    img.colorspace_settings.name = 'Non-Color' if non_color else 'sRGB'
    return img


def _texset(nb, layer, uv_offset=(0.0, 0.0)):
    uvn = nb.node('ShaderNodeUVMap', uv_map='UVMap')
    src = uvn.outputs['UV']
    if uv_offset != (0.0, 0.0):
        mp = nb.node('ShaderNodeMapping'); mp.inputs['Location'].default_value = (*uv_offset, 0.0)
        nb.link(src, mp.inputs['Vector']); src = mp.outputs['Vector']
    out = []
    for kind, non_color in (('BaseColor', False), ('Roughness', True), ('Normal', True)):
        t = nb.node('ShaderNodeTexImage'); t.image = tex_image('T_%s_%s.png' % (layer, kind), non_color)
        nb.link(src, t.inputs['Vector']); out.append(t.outputs['Color'])
    return out


def pbr_material(layer):
    name = 'M_' + layer
    if name in bpy.data.materials: return bpy.data.materials[name]
    m = bpy.data.materials.new(name); m.use_nodes = True; nb = NB(m); p = nb.n['Principled BSDF']
    col, rough, nrm = _texset(nb, layer)
    nb.link(col, p.inputs['Base Color'])
    sep = nb.node('ShaderNodeSeparateColor'); nb.link(rough, sep.inputs['Color']); nb.link(sep.outputs['Red'], p.inputs['Roughness'])
    nm = nb.node('ShaderNodeNormalMap', uv_map='UVMap'); nb.link(nrm, nm.inputs['Color']); nb.link(nm.outputs['Normal'], p.inputs['Normal'])
    m.diffuse_color = (*SWATCH[layer], 1.0)
    m['kit_material'] = layer
    return m


def terrain_material():
    """M_TerrainBlend: DrySoil base, vertex colour Mask selects PathGravel/WetSoil/Grass/Moss."""
    name = 'M_TerrainBlend'
    if name in bpy.data.materials: return bpy.data.materials[name]
    m = bpy.data.materials.new(name); m.use_nodes = True; nb = NB(m); p = nb.n['Principled BSDF']
    attr = nb.node('ShaderNodeAttribute', attribute_type='GEOMETRY', attribute_name='Mask')
    sep = nb.node('ShaderNodeSeparateColor'); nb.link(attr.outputs['Color'], sep.inputs['Color'])
    chan = [sep.outputs['Red'], sep.outputs['Green'], sep.outputs['Blue'], attr.outputs['Alpha']]
    col, rough, nrm = _texset(nb, 'DrySoil')
    uvn = nb.node('ShaderNodeUVMap', uv_map='UVMap')
    for i, (layer, ch) in enumerate(MASK_ORDER):
        lc, lr, ln = _texset(nb, layer)
        mp = nb.node('ShaderNodeMapping'); mp.inputs['Location'].default_value = (0.37 * (i + 1), 0.61 * (i + 1), 0.0)
        nb.link(uvn.outputs['UV'], mp.inputs['Vector'])
        bt = nb.node('ShaderNodeTexImage'); bt.image = tex_image('T_BlendNoise.png', True); nb.link(mp.outputs['Vector'], bt.inputs['Vector'])
        h = sock(bt.outputs, 'Color')
        hsep = nb.node('ShaderNodeSeparateColor'); nb.link(h, hsep.inputs['Color'])
        (wr, wg, wb), amp, lo, hi = BLEND[layer]
        n = nb.math('ADD', nb.math('MULTIPLY', hsep.outputs['Red'], wr), nb.math('ADD', nb.math('MULTIPLY', hsep.outputs['Green'], wg), nb.math('MULTIPLY', hsep.outputs['Blue'], wb)))
        v = nb.math('MULTIPLY_ADD', n, amp, chan[ch])                            # mask + amp * noise
        f = nb.maprange(v, lo, hi, smooth=True)
        col = nb.mix_rgb(f, col, lc); rough = nb.mix_rgb(f, rough, lr); nrm = nb.mix_rgb(f, nrm, ln)
    nb.link(col, p.inputs['Base Color'])
    rs = nb.node('ShaderNodeSeparateColor'); nb.link(rough, rs.inputs['Color']); nb.link(rs.outputs['Red'], p.inputs['Roughness'])
    nm = nb.node('ShaderNodeNormalMap', uv_map='UVMap'); nb.link(nrm, nm.inputs['Color']); nb.link(nm.outputs['Normal'], p.inputs['Normal'])
    m.diffuse_color = (*SWATCH['DrySoil'], 1.0)
    m['kit_material'] = 'TerrainBlend: base DrySoil; Mask R=WetSoil G=Grass B=PathGravel A=Moss'
    return m


def grass_card_material():
    name = 'M_GrassCard'
    if name in bpy.data.materials: return bpy.data.materials[name]
    m = bpy.data.materials.new(name); m.use_nodes = True; nb = NB(m); p = nb.n['Principled BSDF']
    t = nb.node('ShaderNodeTexImage'); t.image = tex_image('T_GrassCard_BaseColor.png', False)
    uvn = nb.node('ShaderNodeUVMap', uv_map='UVMap'); nb.link(uvn.outputs['UV'], t.inputs['Vector'])
    dim = nb.node('ShaderNodeMix'); dim.data_type = 'RGBA'; dim.blend_type = 'MULTIPLY'
    sock(dim.inputs, 'Factor_Float').default_value = 1.0; sock(dim.inputs, 'B_Color').default_value = (0.72, 0.74, 0.62, 1.0)
    nb.link(t.outputs['Color'], sock(dim.inputs, 'A_Color')); nb.link(sock(dim.outputs, 'Result_Color'), p.inputs['Base Color'])
    nb.link(t.outputs['Alpha'], p.inputs['Alpha'])
    p.inputs['Roughness'].default_value = 0.85
    try: m.surface_render_method = 'DITHERED'
    except AttributeError: pass
    m.diffuse_color = (*SWATCH['Grass'], 1.0); m['kit_material'] = 'GrassCard (alpha cutout)'
    return m


def flat_material(name, color, rough=0.8):
    if name in bpy.data.materials: return bpy.data.materials[name]
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*color, 1.0); p.inputs['Roughness'].default_value = rough
    m.diffuse_color = (*color, 1.0)
    return m


def test_material(name='M_TEST_Only', color=(0.35, 0.36, 0.38)):
    m = flat_material(name, color, 0.6); m['test_only'] = True; return m


def blockout_material():
    """Blockout preview: flat layer colours selected by the same Mask attribute (no textures)."""
    name = 'M_Blockout_Layers'
    if name in bpy.data.materials: return bpy.data.materials[name]
    m = bpy.data.materials.new(name); m.use_nodes = True; nb = NB(m); p = nb.n['Principled BSDF']
    attr = nb.node('ShaderNodeAttribute', attribute_type='GEOMETRY', attribute_name='Mask')
    sep = nb.node('ShaderNodeSeparateColor'); nb.link(attr.outputs['Color'], sep.inputs['Color'])
    chan = [sep.outputs['Red'], sep.outputs['Green'], sep.outputs['Blue'], attr.outputs['Alpha']]
    col = (0.30, 0.24, 0.17)
    for layer, ch in MASK_ORDER:
        f = nb.maprange(chan[ch], 0.35, 0.75, smooth=True)
        c = {'PathGravel': (0.40, 0.36, 0.30), 'WetSoil': (0.13, 0.10, 0.075), 'Grass': (0.16, 0.24, 0.09), 'Moss': (0.10, 0.20, 0.07)}[layer]
        col = nb.mix_rgb(f, col, c)
    nb.link(col, p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.85
    m.diffuse_color = (0.30, 0.24, 0.17, 1.0); m['kit_material'] = 'Blockout preview (flat layer colours)'
    return m


def lattice_multi(name, surfs, zfun_of, maskfun_of, coll, parent, mats, ku=1, kv=1, h=1e-4):
    """One mesh from several lattice parts (e.g. the left and right pieces of C02).

    zfun_of(sf) / maskfun_of(sf) return the (u, v) -> value functions of a part.  Normals are the
    analytic normals of the height function, written as custom normals so seams shade identically.
    """
    verts, normals, masks, uvs, faces = [], [], [], [], []
    for sf in surfs:
        zf, mf = zfun_of(sf), maskfun_of(sf)
        us = subsample(sf.us, ku); vs = subsample(sf.vs, kv); nu, nv = len(us), len(vs); base = len(verts)
        def P(u, v):
            x, y = sf.xy(u, v); return Vector((x, y, zf(u, v)))
        for u in us:
            for v in vs:
                verts.append(P(u, v)); masks.append(mf(u, v)); uvs.append(sf.uv(u, v))
                n = (P(u + h, v) - P(u - h, v)).cross(P(u, v + h) - P(u, v - h))
                normals.append(n.normalized() if n.length > 0 else Vector((0, 0, 1)))
        for i in range(nu - 1):
            for j in range(nv - 1):
                a = base + i * nv + j; faces.append((a, a + nv, a + nv + 1, a + 1))
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(p) for p in verts], [], faces); me.update()
    uvl = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices:
            uvl.data[li].uv = uvs[me.loops[li].vertex_index]
    ca = me.color_attributes.new('Mask', 'FLOAT_COLOR', 'POINT')
    for d, mk in zip(ca.data, masks): d.color = tuple(min(1.0, max(0.0, c)) for c in mk)
    me.color_attributes.active_color = ca
    for m in mats: me.materials.append(m)
    me.shade_smooth()
    me.normals_split_custom_set_from_vertices([tuple(n) for n in normals])
    return link_obj(name, me, coll, parent)


SWATCH = {'DrySoil': (0.155, 0.125, 0.092), 'WetSoil': (0.07, 0.054, 0.038), 'Grass': (0.09, 0.125, 0.045),
          'Moss': (0.06, 0.11, 0.035), 'Rock': (0.16, 0.17, 0.17), 'PathGravel': (0.19, 0.165, 0.13),
          'Bark': (0.10, 0.085, 0.07), 'Wood': (0.22, 0.18, 0.13), 'EndGrain': (0.30, 0.23, 0.15), 'Timber': (0.22, 0.14, 0.08)}   # D01 / D02 bridges


# ---- mesh helpers --------------------------------------------------------------------------------
def subsample(lst, k):
    out = lst[::k]
    if out[-1] != lst[-1]: out.append(lst[-1])
    return out


def link_obj(name, data, coll, parent=None):
    ob = bpy.data.objects.new(name, data); coll.objects.link(ob)
    if parent is not None: ob.parent = parent
    return ob


def lattice_object(name, sf, zfun, maskfun, coll, parent, mats, ku=1, kv=1, h=1e-4):
    """Grid surface on the module lattice: UVs, Mask colours and analytic custom normals."""
    us = subsample(sf.us, ku); vs = subsample(sf.vs, kv); nu, nv = len(us), len(vs)
    verts = []; normals = []; masks = []; uvs = []
    def P(u, v):
        x, y = sf.xy(u, v); return Vector((x, y, zfun(u, v)))
    for u in us:
        for v in vs:
            verts.append(P(u, v)); masks.append(maskfun(u, v)); uvs.append(sf.uv(u, v))
            du = (P(u + h, v) - P(u - h, v)); dv = (P(u, v + h) - P(u, v - h))
            n = du.cross(dv); normals.append(n.normalized() if n.length > 0 else Vector((0, 0, 1)))
    faces = []
    for i in range(nu - 1):
        for j in range(nv - 1):
            a = i * nv + j; faces.append((a, a + nv, a + nv + 1, a + 1))
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(p) for p in verts], [], faces); me.update()
    uvl = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices:
            uvl.data[li].uv = uvs[me.loops[li].vertex_index]
    ca = me.color_attributes.new('Mask', 'FLOAT_COLOR', 'POINT')
    for d, mk in zip(ca.data, masks): d.color = tuple(min(1.0, max(0.0, c)) for c in mk)
    for m in mats: me.materials.append(m)
    me.shade_smooth()
    me.normals_split_custom_set_from_vertices([tuple(n) for n in normals])
    return link_obj(name, me, coll, parent)


def box_uv(me, scale=0.5):
    """Box projection UVs (metres * scale) for rocks and masonry."""
    uvl = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        n = poly.normal; ax = max(range(3), key=lambda i: abs(n[i]))
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            a, b = [(co.y, co.z), (co.x, co.z), (co.x, co.y)][ax]
            uvl.data[li].uv = (a * scale, b * scale)


class Parts:
    """Accumulates loose pieces (rocks, cards) into one object per category."""

    def __init__(self):
        self.v = []; self.f = []; self.m = []; self.uv = []; self.sm = []

    def add(self, verts, faces, mat=0, uvs=None, smooth=None):
        o = len(self.v); self.v += [tuple(p) for p in verts]
        for k, face in enumerate(faces):
            self.f.append(tuple(o + i for i in face)); self.m.append(mat); self.sm.append(smooth)
            self.uv.append(uvs[k] if uvs else None)

    def build(self, name, mats, coll, parent, smooth=False, uv_mode='box', sharp_angle=None):
        """sharp_angle (degrees): shade smooth but keep edges sharper than this crisp (natural stones)."""
        if not self.f: return None
        me = bpy.data.meshes.new(name); me.from_pydata(self.v, [], self.f); me.update()
        for mt in mats: me.materials.append(mt)
        for poly, mi, fs in zip(me.polygons, self.m, self.sm): poly.material_index = mi; poly.use_smooth = smooth if fs is None else fs
        if sharp_angle is not None:
            for poly in me.polygons: poly.use_smooth = True
            me.set_sharp_from_angle(angle=math.radians(sharp_angle))
        if uv_mode == 'box': box_uv(me)
        else:
            uvl = me.uv_layers.new(name='UVMap')
            for poly, fuv in zip(me.polygons, self.uv):
                for k, li in enumerate(poly.loop_indices): uvl.data[li].uv = fuv[k]
        return link_obj(name, me, coll, parent)


def rock(parts, rng, loc, size, yaw=None, tilt=(0.0, 0.0), subdiv=1, flatten=0.45, moss_mat=None, base_mat=0, normal_up=None, moss_cut=0.25, facets=0):
    """Low-poly displaced icosphere (Blender subdivisions: 1 = icosahedron, 20 triangles; 2 = 80 triangles)."""
    import bmesh
    from mathutils import Euler, Matrix
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
    o = rng.uniform(0, 100)
    for v in bm.verts:
        d = 1 + 0.26 * noise.noise(v.co * 1.3 + Vector((o, o, o))) + 0.07 * noise.noise(v.co * 3.7 + Vector((-o, o, o)))
        v.co *= d; v.co.z = max(v.co.z, -flatten)
    planes = fracture_planes(rng, facets) if facets else []
    for v in bm.verts: v.co = cleave(v.co, planes)
    rot = Euler((tilt[0], tilt[1], rng.uniform(0, math.tau) if yaw is None else yaw)).to_matrix()
    if normal_up is not None:
        rot = Vector((0, 0, 1)).rotation_difference(Vector(normal_up)).to_matrix() @ rot
    verts = [rot @ Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2])) + Vector(loc) for v in bm.verts]
    faces = [tuple(v.index for v in f.verts) for f in bm.faces]; bm.free()
    o = len(parts.v); parts.v += [tuple(p) for p in verts]
    for f in faces:
        pts = [verts[i] for i in f]; n = (pts[1] - pts[0]).cross(pts[2] - pts[0])
        top = n.length > 0 and n.normalized().z > 0.7 and moss_mat is not None and noise.noise(pts[0] * 2.1) > moss_cut
        parts.f.append(tuple(o + i for i in f)); parts.m.append(moss_mat if top else base_mat); parts.uv.append(None); parts.sm.append(True)


def pebble(parts, rng, loc, r, mat=0):
    n = 5; h = r * rng.uniform(0.35, 0.6); a0 = rng.uniform(0, math.tau)
    ring = [(loc[0] + r * rng.uniform(0.7, 1.1) * math.cos(a0 + i * math.tau / n), loc[1] + r * rng.uniform(0.7, 1.1) * math.sin(a0 + i * math.tau / n), loc[2] + h * 0.3) for i in range(n)]
    parts.add(ring + [(loc[0], loc[1], loc[2] + h), (loc[0], loc[1], loc[2] - h * 0.4)],
              [(i, (i + 1) % n, n) for i in range(n)] + [((i + 1) % n, i, n + 1) for i in range(n)], mat)


def grass_card(parts, rng, loc, size=1.0, mat=0, lean=None):
    """Two crossed quads (4 triangles) using the alpha grass texture."""
    w = rng.uniform(0.32, 0.5) * size; hgt = rng.uniform(0.22, 0.38) * size; a0 = rng.uniform(0, math.pi)
    lx, ly = lean if lean else (rng.uniform(-0.04, 0.04), rng.uniform(-0.04, 0.04))
    for k in range(2):
        a = a0 + k * math.pi / 2; dx, dy = math.cos(a) * w / 2, math.sin(a) * w / 2
        x, y, z = loc
        quad = [(x - dx, y - dy, z - 0.02), (x + dx, y + dy, z - 0.02), (x + dx + lx, y + dy + ly, z + hgt), (x - dx + lx, y - dy + ly, z + hgt)]
        parts.add(quad, [(0, 1, 2, 3)], mat, uvs=[[(0, 0), (1, 0), (1, 1), (0, 1)]])


def block(parts, center, size, yaw=0.0, rng=None, jitter=0.012, mat=0, tilt=None):
    x, y, z = center; a, b, c = size[0] / 2, size[1] / 2, size[2] / 2
    j = (lambda: rng.uniform(-jitter, jitter)) if rng else (lambda: 0.0)
    corners = [(-a, -b, -c), (a, -b, -c), (a, b, -c), (-a, b, -c), (-a + j(), -b + j(), c + j()), (a + j(), -b + j(), c + j()), (a + j(), b + j(), c + j()), (-a + j(), b + j(), c + j())]
    cs, sn = math.cos(yaw), math.sin(yaw); pts = []
    for px, py, pz in corners:
        v = Vector((px * cs - py * sn, px * sn + py * cs, pz))
        if tilt is not None: v = Vector((0, 0, 1)).rotation_difference(Vector(tilt)).to_matrix() @ v
        pts.append((x + v.x, y + v.y, z + v.z))
    parts.add(pts, [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], mat, smooth=False)


def dressed_stone(parts, rng, center, size, bevel=0.03, wobble=0.006, mat=0, moss_mat=None):
    """Cut stone block with chamfered edges (bmesh bevel, 1 segment = 44 triangles), flat shaded.

    Vertices are displaced by smooth noise (not per-vertex random) so the chamfers stay coherent;
    the displacement never pushes a face outside the nominal box, so seats and front faces keep their planes."""
    import bmesh
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    bmesh.ops.bevel(bm, geom=bm.verts[:] + bm.edges[:], offset=bevel, segments=1, affect='EDGES', profile=0.5)
    o = Vector([rng.uniform(0, 100) for _ in range(3)]); half = Vector(size) / 2
    for v in bm.verts:
        d = noise.noise_vector(v.co * 4.0 + o) * wobble
        v.co = Vector([max(-half[i], min(half[i], v.co[i] + d[i])) for i in range(3)])
    verts = [v.co + Vector(center) for v in bm.verts]
    faces = [tuple(v.index for v in f.verts) for f in bm.faces]; bm.free()
    base = len(parts.v); parts.v += [tuple(p) for p in verts]
    for f in faces:
        pts = [verts[i] for i in f]; n = (pts[1] - pts[0]).cross(pts[2] - pts[0])
        top = moss_mat is not None and n.length > 0 and n.normalized().z > 0.45 and noise.noise(pts[0] * 3.1 + o) > 0.15
        parts.f.append(tuple(base + i for i in f)); parts.m.append(moss_mat if top else mat); parts.uv.append(None); parts.sm.append(False)


def decimated_copy(name, src, ratio, coll, parent):
    """Real reduced LOD: evaluate a Decimate (collapse) modifier on a temporary object and keep the result."""
    tmp = link_obj(name + '__tmp', src.data, coll, parent)
    mod = tmp.modifiers.new('KIT_Decimate', 'DECIMATE'); mod.ratio = ratio; mod.use_collapse_triangulate = True
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(tmp); me.name = name
    return link_obj(name, me, coll, parent)


def cleave(co, planes):
    """Project a vertex onto every fracture plane it lies beyond: flat broken faces with crisp edges."""
    for n, d in planes:
        t = co.dot(n) - d
        if t > 0: co = co - n * t
    return co


def fracture_planes(rng, count):
    out = []
    for _ in range(count):
        a = rng.uniform(0, math.tau); z = rng.uniform(-0.25, 0.85); r = math.sqrt(max(0.0, 1 - z * z))
        out.append((Vector((r * math.cos(a), r * math.sin(a), z)), rng.uniform(0.62, 0.86)))
    return out


def chunk(parts, rng, loc, size, normal_up=(0, 0, 1), yaw=0.0, mat=0, moss_mat=None, moss_cut=0.3, roundness=(0.3, 0.55), rough=0.16, tilt=0.0, dome=0.0,
          facets=(2, 4), cuts=1):
    """Blocky natural stone: once-subdivided cube pulled towards a sphere and roughened (48 triangles).

    roundness: range of the pull towards a sphere; rough: noise displacement (two octaves); facets: range
    of random fracture planes; cuts: 1 = 48 triangles, 2 = 108; tilt: max random tilt (radians)
    about a horizontal axis, so laid stones do not all lie parallel to the slope like paving; dome: extra
    rise of the upper face centre (in half-heights) so stones read as boulders rather than slabs."""
    import bmesh
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=2.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    o = rng.uniform(0, 100); k = rng.uniform(*roundness); planes = fracture_planes(rng, rng.randint(*facets))
    for v in bm.verts:
        sph = v.co.normalized() * 1.2; v.co = v.co.lerp(sph, k)
        v.co *= 1 + rough * (noise.noise(v.co * 1.6 + Vector((o, o, o))) + 0.45 * noise.noise(v.co * 3.7 + Vector((-o, o, 0.5 * o))))
        v.co = cleave(v.co, planes)
        if v.co.z > 0: v.co.z += dome * max(0.0, 1.0 - 0.5 * (v.co.x ** 2 + v.co.y ** 2))
        v.co.z = max(v.co.z, -0.75)
    from mathutils import Matrix
    ax = rng.uniform(0, math.tau)
    rot = (Vector((0, 0, 1)).rotation_difference(Vector(normal_up)).to_matrix() @ Matrix.Rotation(yaw, 3, 'Z')
           @ Matrix.Rotation(rng.uniform(-tilt, tilt), 3, Vector((math.cos(ax), math.sin(ax), 0.0))))
    verts = [rot @ Vector((v.co.x * size[0] / 2, v.co.y * size[1] / 2, v.co.z * size[2] / 2)) + Vector(loc) for v in bm.verts]
    faces = [tuple(v.index for v in f.verts) for f in bm.faces]; bm.free()
    base = len(parts.v); parts.v += [tuple(p) for p in verts]
    for f in faces:
        pts = [verts[i] for i in f]; n = (pts[1] - pts[0]).cross(pts[2] - pts[0])
        top = moss_mat is not None and n.length > 0 and n.normalized().dot(Vector(normal_up)) > 0.8 and noise.noise(pts[0] * 2.3) > moss_cut
        parts.f.append(tuple(base + i for i in f)); parts.m.append(moss_mat if top else mat); parts.uv.append(None); parts.sm.append(False)


# ---- lighting / rendering ------------------------------------------------------------------------
def studio(scene, coll, samples=32, transparent=True, exposure=0.0):
    sun = bpy.data.lights.new('KIT_Sun', 'SUN'); sun.energy = 3.2; sun.angle = math.radians(6)
    so = bpy.data.objects.new('KIT_Sun', sun); coll.objects.link(so); so.rotation_euler = (math.radians(48), math.radians(-8), math.radians(-35))
    fill = bpy.data.lights.new('KIT_Fill', 'SUN'); fill.energy = 0.6; fill.angle = math.radians(25)
    fo = bpy.data.objects.new('KIT_Fill', fill); coll.objects.link(fo); fo.rotation_euler = (math.radians(65), 0, math.radians(150))
    w = bpy.data.worlds.new('KIT_Sky'); w.use_nodes = True; bg = w.node_tree.nodes['Background']
    bg.inputs[0].default_value = (0.55, 0.60, 0.66, 1.0); bg.inputs[1].default_value = 0.55; scene.world = w
    scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = samples; scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 6; scene.cycles.diffuse_bounces = 3; scene.cycles.glossy_bounces = 3; scene.cycles.transparent_max_bounces = 12
    scene.render.film_transparent = transparent
    scene.render.resolution_x = 1024; scene.render.resolution_y = 1024; scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'; scene.render.image_settings.color_mode = 'RGBA' if transparent else 'RGB'
    scene.view_settings.view_transform = 'AgX'; scene.view_settings.look = 'AgX - Medium High Contrast'; scene.view_settings.exposure = exposure


def look_at(cam, target, direction, dist):
    cam.location = Vector(target) + Vector(direction).normalized() * dist
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()


VIEWS = [('01_front', (0, -1, 0)), ('02_right', (1, 0, 0)), ('03_rear', (0, 1, 0)), ('04_left', (-1, 0, 0)), ('05_front_right', (1, -1, 0.6)),
         ('06_rear_right', (1, 1, 0.6)), ('07_rear_left', (-1, 1, 0.6)), ('08_front_left', (-1, -1, 0.6)), ('09_top', (0, 0, 1)), ('10_high_front', (0, -1, 1))]
