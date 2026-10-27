"""Showcase and seam close-ups (PHASE 5-6): the kit assembled into a small river crossing.

  blender -b --python-exit-code 1 --python 05_Scripts/render_showcase.py -- [--name showcase_v01] [--samples 64] [--preview]

Links the three kit .blend files read-only and places module collections at connector-derived transforms:
near road A05-A06-A03-A04 -> bridgehead C01-C05, C07, C08 -> D02 timber bridge (01_Blender/timber_bridge_v01.blend) over the river -> the same
bridgehead rotated 180 degrees on the far bank -> A11-A03-A04-A10.  Bank chains start and end on the C02 bank
connectors of both bridgeheads.  Ground, riverbed, river stones, water, diorama sides and grass tufts on the ground
are showcase props, not kit deliverables.  Writes 04_Previews/Showcase/<name>_<view>.png, <name>_labels.json
(2D label anchors for annotate_showcase.py) and <name>_scene.blend (links the kit files).  --preview renders
small, noisy test frames to _work/showcase_preview/ instead.  Never overwrites.
"""
import sys, math, json, random
from pathlib import Path
import bpy
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit_spec as K
import kit_blender as KB

FAR = Matrix.Translation((14.0, 0.0, 0.0)) @ Matrix.Rotation(math.pi, 4, 'Z')     # far bridgehead frame
Y_EDGE = 16.0                                                                      # diorama half width (3 bank modules + C02)
GROUND_Z = -0.03                                                                   # showcase ground just under every land surface
BRIDGEHEAD = ('C01', 'C02', 'C03', 'C04', 'C05', 'C07', 'C08')


def cli():
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    def get(k, d=None): return a[a.index(k) + 1] if k in a else d
    return get('--name', 'showcase_v01'), int(get('--samples', '64')), '--preview' in a


def rz(deg):
    return Matrix.Rotation(math.radians(deg), 4, 'Z')


def exit_m(code):
    tf = K.exit_transform(K.BY_CODE[code])
    if tf is None: return None
    (x, y, z), hd = tf
    return Matrix.Translation((x, y, z)) @ rz(hd)


class Kit:
    """Read-only links to the module collections of the three kit files."""

    def __init__(self, scene):
        self.scene = scene; self.coll = {}; self.slot = {}; self.placed = []
        for f in K.GROUP_FILES.values():
            with bpy.data.libraries.load(str(KB.kit_path('01_Blender/%s_v01.blend' % f)), link=True) as (src, dst):
                dst.collections = [c for c in src.collections if c.startswith('SM_')]
            for c in dst.collections:
                root = next(o for o in c.objects if o.type == 'EMPTY' and o.name == c.name)
                self.coll[c.name] = c; self.slot[c.name] = Vector(root.location)
        with bpy.data.libraries.load(str(KB.kit_path('01_Blender/timber_bridge_v01.blend')), link=True) as (src, dst):   # D02, the extra timber bridge
            dst.collections = ['SM_Bridge_Timber_A']
        self.bridge = dst.collections[0]

    def place_bridge(self, T):
        e = bpy.data.objects.new('SHOW_D02_TimberBridge', None); e.instance_type = 'COLLECTION'; e.instance_collection = self.bridge
        e.matrix_world = T; self.scene.collection.objects.link(e)

    def place(self, code, T, tag):
        mid = K.BY_CODE[code]['id']
        e = bpy.data.objects.new('SHOW_%s_%s' % (code, tag), None); e.instance_type = 'COLLECTION'; e.instance_collection = self.coll[mid]
        e.matrix_world = T @ Matrix.Translation(-self.slot[mid]); self.scene.collection.objects.link(e)
        self.placed.append((code, T.copy(), tag))

    def forward(self, codes, T, tag):
        for c in codes:
            self.place(c, T, tag); m = exit_m(c)
            if m is not None: T = T @ m
        return T

    def backward(self, codes, T, tag):
        """codes nearest-first: each module's exit lands on the entry of the one placed before it."""
        for c in codes:
            T = T @ exit_m(c).inverted(); self.place(c, T, tag)
        return T


# ---- showcase props (not deliverables) ---------------------------------------------------------------
def show_pbr(name, layer):
    m = bpy.data.materials.new(name); m.use_nodes = True; nb = KB.NB(m); p = nb.n['Principled BSDF']
    col, rough, nrm = KB._texset(nb, layer)
    nb.link(col, p.inputs['Base Color'])
    sep = nb.node('ShaderNodeSeparateColor'); nb.link(rough, sep.inputs['Color']); nb.link(sep.outputs['Red'], p.inputs['Roughness'])
    nm = nb.node('ShaderNodeNormalMap', uv_map='UVMap'); nb.link(nrm, nm.inputs['Color']); nb.link(nm.outputs['Normal'], p.inputs['Normal'])
    return m


BED_DEPTH = 0.55     # extra depth of the showcase channel below the bank toe (-1.00) at mid-river


def bed_z(x, y):
    """Showcase stream bed between the two bank toes (x 5..9): 0 at the toes, deepest in the middle."""
    from mathutils import noise as mnoise
    t = min(1.0, max(0.0, (x - 5.0) / 4.0))
    return K.BANK_TOE_Z - BED_DEPTH * math.sin(math.pi * t) ** 1.3 * (1.0 + 0.12 * mnoise.noise(Vector((x * 0.4, y * 0.35, 3.1))))


def riverbed_material():
    """Pebble bed (T_PathGravel) with sun caustics: two Voronoi edge webs brighten the bed under the water."""
    m = bpy.data.materials.new('SHOW_Riverbed'); m.use_nodes = True; nb = KB.NB(m); p = nb.n['Principled BSDF']
    col, rough, nrm = KB._texset(nb, 'PathGravel')
    tc = nb.node('ShaderNodeTexCoord'); web = None
    warp = nb.node('ShaderNodeTexNoise'); warp.inputs['Scale'].default_value = 1.6; warp.inputs['Detail'].default_value = 2.0
    nb.link(tc.outputs['Object'], warp.inputs['Vector'])
    for sc, off in ((6.5, 0.0), (9.5, 7.7)):
        mp = nb.node('ShaderNodeMapping'); mp.inputs['Location'].default_value = (off, off * 0.5, 0.0); mp.inputs['Scale'].default_value = (1.0, 0.75, 1.0)
        wv = nb.node('ShaderNodeVectorMath', operation='MULTIPLY_ADD'); nb.link(warp.outputs['Color'], wv.inputs[0])
        wv.inputs[1].default_value = (0.12, 0.12, 0.12); nb.link(tc.outputs['Object'], wv.inputs[2]); nb.link(wv.outputs['Vector'], mp.inputs['Vector'])
        v = nb.node('ShaderNodeTexVoronoi'); v.feature = 'DISTANCE_TO_EDGE'; v.inputs['Scale'].default_value = sc; nb.link(mp.outputs['Vector'], v.inputs['Vector'])
        c = nb.maprange(v.outputs['Distance'], 0.0, 0.03, 1.0, 0.0, smooth=True)
        web = c if web is None else nb.math('MAXIMUM', web, nb.math('MULTIPLY', c, 0.6))
    patch = nb.node('ShaderNodeTexNoise'); patch.inputs['Scale'].default_value = 0.9; nb.link(tc.outputs['Object'], patch.inputs['Vector'])
    web = nb.math('MULTIPLY', web, nb.maprange(patch.outputs['Fac'], 0.4, 0.65))          # patchy, not a uniform net
    lit = nb.mix_rgb(nb.math('MULTIPLY', web, 0.28), col, (0.92, 0.90, 0.80))
    nb.link(lit, p.inputs['Base Color'])
    sep = nb.node('ShaderNodeSeparateColor'); nb.link(rough, sep.inputs['Color']); nb.link(sep.outputs['Red'], p.inputs['Roughness'])
    nm = nb.node('ShaderNodeNormalMap', uv_map='UVMap'); nb.link(nrm, nm.inputs['Color']); nb.link(nm.outputs['Normal'], p.inputs['Normal'])
    return m


def build_riverbed():
    xs = [5.0 + 4.0 * i / 40 for i in range(41)]; ys = [-Y_EDGE + 2 * Y_EDGE * j / 64 for j in range(65)]
    verts = [(x, y, bed_z(x, y)) for x in xs for y in ys]; ny = len(ys)
    faces = [(i * ny + j, (i + 1) * ny + j, (i + 1) * ny + j + 1, i * ny + j + 1) for i in range(len(xs) - 1) for j in range(ny - 1)]
    me = bpy.data.meshes.new('SHOW_Riverbed'); me.from_pydata(verts, [], faces); me.update(); me.shade_smooth()
    uv = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co; uv.data[li].uv = (co.x / K.UV_TILE_M, co.y / K.UV_TILE_M)
    me.materials.append(riverbed_material()); ob = bpy.data.objects.new('SHOW_Riverbed', me); bpy.context.scene.collection.objects.link(ob)
    stones = KB.Parts(); rng = random.Random(23)
    for _ in range(110):
        x = rng.uniform(5.1, 8.9); y = rng.uniform(-Y_EDGE + 0.4, Y_EDGE - 0.4)
        big = rng.random() < 0.12; r = rng.uniform(0.28, 0.45) if big else rng.uniform(0.07, 0.2)
        z = bed_z(x, y)
        KB.chunk(stones, rng, (x, y, z - r * 0.18), (r * rng.uniform(1.1, 1.5), r, r * rng.uniform(0.55, 0.75)), (0, 0, 1), rng.uniform(0, math.tau),
                 mat=0, roundness=(0.72, 0.92), rough=0.12, tilt=0.25, dome=0.15, facets=(0, 1))
    stones.build('SHOW_RiverStones', [KB.pbr_material('Rock')], bpy.context.scene.collection, None, sharp_angle=55.0)
    return ob


def water_material():
    """Shallow stream: refractive surface with flow-stretched ripples (T_Water_Normal), tinted water volume
    (deeper = greener and darker) and a thin foam line where the water is shallower than about 5 cm."""
    m = bpy.data.materials.new('SHOW_Water'); m.use_nodes = True; nb = KB.NB(m); p = nb.n['Principled BSDF']; out = nb.n['Material Output']
    p.inputs['Base Color'].default_value = (1.0, 1.0, 1.0, 1.0); p.inputs['Roughness'].default_value = 0.025
    p.inputs['IOR'].default_value = 1.333; p.inputs['Transmission Weight'].default_value = 1.0
    uvn = nb.node('ShaderNodeUVMap', uv_map='UVMap'); cols = []
    for sc, loc in (((1.0, 1.0, 1.0), (0.0, 0.0, 0.0)), ((2.3, 1.7, 1.0), (0.31, 0.57, 0.0))):
        mp = nb.node('ShaderNodeMapping'); mp.inputs['Scale'].default_value = sc; mp.inputs['Location'].default_value = loc; nb.link(uvn.outputs['UV'], mp.inputs['Vector'])
        t = nb.node('ShaderNodeTexImage'); t.image = KB.tex_image('T_Water_Normal.png', True); nb.link(mp.outputs['Vector'], t.inputs['Vector']); cols.append(t.outputs['Color'])
    nm = nb.node('ShaderNodeNormalMap', uv_map='UVMap'); nm.inputs['Strength'].default_value = 0.35
    nb.link(nb.mix_rgb(0.5, cols[0], cols[1]), nm.inputs['Color']); nb.link(nm.outputs['Normal'], p.inputs['Normal'])
    depth = nb.node('ShaderNodeAttribute', attribute_type='GEOMETRY', attribute_name='Depth')
    fn = nb.node('ShaderNodeTexNoise'); fn.inputs['Scale'].default_value = 9.0; fn.inputs['Detail'].default_value = 3.0
    fmp = nb.node('ShaderNodeMapping'); fmp.inputs['Scale'].default_value = (3.0, 0.8, 1.0); nb.link(uvn.outputs['UV'], fmp.inputs['Vector']); nb.link(fmp.outputs['Vector'], fn.inputs['Vector'])
    foam = nb.math('MULTIPLY', nb.maprange(depth.outputs['Fac'], 0.0, 0.035, 0.6, 0.0, smooth=True), nb.maprange(fn.outputs['Fac'], 0.5, 0.68))
    nb.link(nb.mix_rgb(foam, (1.0, 1.0, 1.0), (0.62, 0.65, 0.62)), p.inputs['Base Color'])      # foam folded into one BSDF (closure limit)
    nb.link(nb.math('SUBTRACT', 1.0, foam), p.inputs['Transmission Weight']); nb.link(nb.mix_f(foam, 0.025, 0.7), p.inputs['Roughness'])
    nb.link(p.outputs['BSDF'], out.inputs['Surface'])
    ab = nb.node('ShaderNodeVolumeAbsorption'); ab.inputs['Color'].default_value = (0.52, 0.86, 0.80, 1.0); ab.inputs['Density'].default_value = 1.4
    scat = nb.node('ShaderNodeVolumeScatter'); scat.inputs['Color'].default_value = (0.70, 0.90, 0.85, 1.0); scat.inputs['Density'].default_value = 0.05
    add = nb.node('ShaderNodeAddShader'); nb.link(ab.outputs['Volume'], add.inputs[0]); nb.link(scat.outputs['Volume'], add.inputs[1]); nb.link(add.outputs['Shader'], out.inputs['Volume'])
    return m


def build_water(scene, x0=4.2, x1=9.8, z=K.WATER_Z, bottom=-1.75):
    """Closed water body under the test water level.  Depth to the terrain below each surface vertex is found by
    casting rays at the real module geometry and stored as the 'Depth' attribute (drives the foam line)."""
    import bmesh
    dg = bpy.context.evaluated_depsgraph_get(); bpy.context.view_layer.update()
    xs = [x0 + (x1 - x0) * i / 70 for i in range(71)]; ys = [-Y_EDGE + 0.004 + (2 * Y_EDGE - 0.008) * j / 80 for j in range(81)]
    def depth_at(x, y):
        o = Vector((x, y, -0.5))
        for _ in range(10):
            hit, loc, nrm, idx, ob, mtx = scene.ray_cast(dg, o, Vector((0.0, 0.0, -1.0)), distance=3.0)
            if not hit: return 0.3
            nm = ob.name if ob else ''
            if 'Terrain' in nm or 'Masonry' in nm or nm.startswith(('SHOW_Riverbed', 'SHOW_RiverStones')): return max(0.0, z - loc.z)
            o = loc + Vector((0.0, 0.0, -1e-3))
        return 0.3
    bm = bmesh.new(); dl = bm.verts.layers.float.new('Depth'); top = {}; bot = {}
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            v = bm.verts.new((x, y, z)); v[dl] = depth_at(x, y); top[i, j] = v
            if i in (0, len(xs) - 1) or j in (0, len(ys) - 1): b = bm.verts.new((x, y, bottom)); b[dl] = 1.0; bot[i, j] = b
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1): bm.faces.new((top[i, j], top[i + 1, j], top[i + 1, j + 1], top[i, j + 1]))
    ring = [(i, 0) for i in range(len(xs))] + [(len(xs) - 1, j) for j in range(1, len(ys))] + [(i, len(ys) - 1) for i in range(len(xs) - 2, -1, -1)] + [(0, j) for j in range(len(ys) - 2, 0, -1)]
    for a, b in zip(ring, ring[1:] + ring[:1]): bm.faces.new((top[a], bot[a], bot[b], top[b]))
    bm.faces.new([bot[k] for k in reversed(ring)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new('SHOW_Water_-0.80'); bm.to_mesh(me); bm.free()
    uv = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co; uv.data[li].uv = (co.x / K.UV_TILE_M, co.y / K.UV_TILE_M)
    me.materials.append(water_material()); ob = bpy.data.objects.new('SHOW_Water_-0.80', me); scene.collection.objects.link(ob)
    return ob


def sky(scene, strength=0.8):
    """Gradient sky (pale horizon, blue zenith) seen in reflections; camera rays see a plain light backdrop."""
    nt = scene.world.node_tree; bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Generated'], sep.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -0.05; mr.inputs['From Max'].default_value = 0.85; nt.links.new(sep.outputs['Z'], mr.inputs['Value'])
    rp = nt.nodes.new('ShaderNodeValToRGB'); cr = rp.color_ramp
    cr.elements[0].color = (0.56, 0.63, 0.70, 1.0); cr.elements[1].color = (0.22, 0.36, 0.62, 1.0); e = cr.elements.new(0.3); e.color = (0.40, 0.52, 0.70, 1.0)
    nt.links.new(mr.outputs['Result'], rp.inputs['Fac'])
    lp = nt.nodes.new('ShaderNodeLightPath'); mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'     # camera sees a plain backdrop
    nt.links.new(lp.outputs['Is Camera Ray'], KB.sock(mx.inputs, 'Factor_Float')); nt.links.new(rp.outputs['Color'], KB.sock(mx.inputs, 'A_Color'))
    KB.sock(mx.inputs, 'B_Color').default_value = (0.74, 0.76, 0.78, 1.0); nt.links.new(KB.sock(mx.outputs, 'Result_Color'), bg.inputs['Color'])
    bg.inputs['Strength'].default_value = strength


def grid_plane(name, x0, x1, y0, y1, z, mat, step=1.0):
    nx = max(1, round((x1 - x0) / step)); ny = max(1, round((y1 - y0) / step))
    xs = [x0 + (x1 - x0) * i / nx for i in range(nx + 1)]; ys = [y0 + (y1 - y0) * j / ny for j in range(ny + 1)]
    verts = [(x, y, z) for x in xs for y in ys]
    faces = [(i * (ny + 1) + j, (i + 1) * (ny + 1) + j, (i + 1) * (ny + 1) + j + 1, i * (ny + 1) + j + 1) for i in range(nx) for j in range(ny)]
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    uv = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co; uv.data[li].uv = (co.x / K.UV_TILE_M, co.y / K.UV_TILE_M)
    me.materials.append(mat); ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); return ob


def skirt(name, profile, bottom, mat, axis):
    """Vertical diorama side under a top profile [(s, z)], s along x (axis 'y=c') or y (axis 'x=c')."""
    kind, c = axis; verts = []
    for s, z in profile:
        p = (s, c) if kind == 'y' else (c, s)
        verts += [(p[0], p[1], z), (p[0], p[1], bottom)]
    faces = [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) for i in range(len(profile) - 1)]
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update(); me.materials.append(mat)
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); return ob


def section_profile(x_min, x_max):
    """Top edge of the diorama at y = +-Y_EDGE: ground, canonical bank sections, riverbed, far bank, ground."""
    near = [(K.BANK_LINE_X - v, K.bank_z(v)) for v in reversed(K.BANK_V)]          # x 2 -> 5
    far_line = 14.0 - K.BANK_LINE_X
    far = [(far_line + v, K.bank_z(v)) for v in K.BANK_V]                           # x 9 -> 12
    bed = [(5.0 + 4.0 * i / 40, bed_z(5.0 + 4.0 * i / 40, Y_EDGE)) for i in range(1, 40)]
    return [(x_min, GROUND_Z), (near[0][0], GROUND_Z)] + near + bed + far + [(far[-1][0], GROUND_Z), (x_max, GROUND_Z)]


def road_samples(kit):
    pts = []
    for code, T, tag in kit.placed:
        mod = K.BY_CODE[code]
        if mod['group'] != 'A': continue
        sf = K.Surface(mod)
        for i in range(41):
            s = sf.L * i / 40; x, y = sf.path.point(s, 0.0); pts.append(T @ Vector((x, y, 0.0)))
    return pts


def build_props(kit, near_start, far_x):
    M = {'grass': show_pbr('SHOW_Ground_Grass', 'Grass'), 
         'side': KB.flat_material('SHOW_DioramaSide', (0.055, 0.042, 0.032), 0.95),
         'card': KB.grass_card_material()}
    x_min = near_start.translation.x; x_max = far_x
    grid_plane('SHOW_Ground_Near', x_min, 2.0, -Y_EDGE, Y_EDGE, GROUND_Z, M['grass'])
    grid_plane('SHOW_Ground_Far', 12.0, x_max, -Y_EDGE, Y_EDGE, GROUND_Z, M['grass'])
    for sgn in (1, -1):   # under the land strip of C02 and the banks (bank land is above GROUND_Z up to x = 2.9)
        y0, y1 = sorted((sgn * 3.0, sgn * Y_EDGE))
        grid_plane('SHOW_Ground_NearBankLand_%+d' % sgn, 2.0, 2.9, y0, y1, GROUND_Z, M['grass'])
        grid_plane('SHOW_Ground_FarBankLand_%+d' % sgn, 11.1, 12.0, y0, y1, GROUND_Z, M['grass'])
    build_riverbed()
    kit.place_bridge(Matrix.Translation((K.RAMP_L, 0.0, K.DECK_Z)))  # D02 timber bridge from C01 exit to the far C01 exit, seated on both C05
    prof = section_profile(x_min, x_max)
    for sgn in (1, -1):
        skirt('SHOW_Side_Y%+d' % sgn, prof, -1.6, M['side'], ('y', sgn * Y_EDGE))
    y0 = near_start.translation.y
    road = [(y0 + v, K.road_z(v)) for v in K.ROAD_V]
    skirt('SHOW_Side_Xmin', [(-Y_EDGE, GROUND_Z), (y0 - K.ROAD_OUTER, GROUND_Z)] + road + [(y0 + K.ROAD_OUTER, GROUND_Z), (Y_EDGE, GROUND_Z)], -1.6, M['side'], ('x', x_min))
    skirt('SHOW_Side_Xmax', [(-Y_EDGE, GROUND_Z), (Y_EDGE, GROUND_Z)], -1.6, M['side'], ('x', x_max))
    # grass tufts on the showcase ground, kept off the road corridor and the bridgehead footprints
    pts = road_samples(kit); kd = KDTree(len(pts))
    for i, p in enumerate(pts): kd.insert(Vector((p.x, p.y, 0.0)), i)
    kd.balance()
    rng = random.Random(11); cards = KB.Parts(); n = 0
    for _ in range(9000):
        if n >= 2600: break
        x = rng.uniform(x_min + 0.3, x_max - 0.3); y = rng.uniform(-Y_EDGE + 0.3, Y_EDGE - 0.3)
        if not (x < 1.8 or x > 12.2): continue
        if kd.find(Vector((x, y, 0.0)))[2] < 2.6: continue
        if (-0.3 < x < 2.0 or 12.0 < x < 14.3) and abs(y) < 3.3: continue
        KB.grass_card(cards, rng, (x, y, GROUND_Z), rng.uniform(0.7, 1.3)); n += 1
    cards.build('SHOW_GroundGrass', [M['card']], bpy.context.scene.collection, None, uv_mode='given')
    return x_min, x_max


# ---- cameras and labels ----------------------------------------------------------------------------
LABELS = [('A05', 'near'), ('A06', 'near'), ('A03', 'near'), ('A04', 'near'), ('C01', 'near'), ('C03', 'near'), ('C05', 'near'), ('C08', 'near'),
          ('C02', 'near'), ('C07', 'near'), ('B07', 'near'), ('B08', 'near'), ('B02', 'near'), ('B09', 'near'), ('B06', 'near'), ('B05', 'near'),
          ('A11', 'far'), ('A10', 'far'), ('C01', 'far')]
C_ANCHOR = {'C01': (1.0, 0.0, 0.08), 'C02': (3.6, 3.1, -0.4), 'C03': (1.0, 2.6, 0.02), 'C05': (3.25, -0.8, -0.3), 'C07': (2.6, 1.9, 0.0),
            'C08': (4.3, -1.2, -0.75)}


def anchor_of(code, T):
    """Label anchor on a placed module: road centre, mid-slope of a bank, or a chosen point of a bridgehead piece."""
    mod = K.BY_CODE[code]
    if code in C_ANCHOR: return T @ Vector(C_ANCHOR[code])
    sf = K.Surface(mod)
    if mod['group'] == 'B':
        x, y = sf.path.point(sf.L * 0.5, -0.9); return T @ Vector((x, y, -0.45))
    x, y = sf.path.point(sf.L * 0.5, 0.0); return T @ Vector((x, y, 0.02))


def label_text(code, tag):
    m = K.BY_CODE[code]; t = '%s %s' % (code, m['name_zh'])
    return t + '（對岸，同模組轉 180°）' if tag == 'far' and code == 'C01' else t


def set_camera(cam, target, direction, dist, lens=None, ortho=None):
    if ortho:
        cam.data.type = 'ORTHO'; cam.data.ortho_scale = ortho
    else:
        cam.data.type = 'PERSP'; cam.data.lens = lens or 35
    KB.look_at(cam, target, direction, dist); cam.data.clip_end = 600


def main():
    name, samples, preview = cli()
    scene = KB.start_session()
    out_dir = '_work/showcase_preview' if preview else '04_Previews/Showcase'
    kit = Kit(scene)
    for frame, tag in ((Matrix.Identity(4), 'near'), (FAR, 'far')):
        for c in BRIDGEHEAD: kit.place(c, frame, tag)
    near_start = kit.backward(['A04', 'A03', 'A06', 'A05'], Matrix.Identity(4), 'near')
    kit.forward(['A11', 'A03', 'A04', 'A10'], Matrix.Translation((14.0, 0.0, 0.0)), 'far')
    bank_out = Matrix.Translation((K.BANK_LINE_X, K.BH_BANK_A, 0.0)) @ rz(90); bank_in = Matrix.Translation((K.BANK_LINE_X, -K.BH_BANK_A, 0.0)) @ rz(90)
    kit.forward(['B07', 'B08', 'B02'], bank_out, 'near'); kit.backward(['B09', 'B06', 'B05'], bank_in, 'near')
    kit.forward(['B08', 'B01', 'B06'], FAR @ bank_out, 'far'); kit.backward(['B05', 'B02', 'B07'], FAR @ bank_in, 'far')
    far_end = max((T @ Vector((K.BY_CODE[c].get('length', 4.0), 0, 0))).x for c, T, tag in kit.placed if tag == 'far' and K.BY_CODE[c]['group'] == 'A')
    x_min, x_max = build_props(kit, near_start, far_end + 2.5)
    print('LAYOUT', len(kit.placed), 'instances; near start', tuple(round(v, 3) for v in near_start.translation),
          'heading %.2f' % math.degrees(near_start.to_euler().z), 'x range', round(x_min, 2), round(x_max, 2), flush=True)
    stu = bpy.data.collections.new('SHOW_Studio'); scene.collection.children.link(stu)
    KB.studio(scene, stu, samples=8 if preview else samples, transparent=False)
    sky(scene); build_water(scene)
    bpy.data.objects['KIT_Fill'].visible_glossy = False     # the 25-degree fill light made a large white blob on the water
    scene.render.resolution_x, scene.render.resolution_y = (960, 540) if preview else (1920, 1080)
    cam = bpy.data.objects.new('SHOW_Camera', bpy.data.cameras.new('SHOW_Camera')); stu.objects.link(cam); scene.camera = cam
    cx = (x_min + x_max) / 2
    seam_road = next(T for c, T, tag in kit.placed if c == 'A04' and tag == 'near').translation          # A03 exit = A04 entry
    views = [
        ('hero', dict(target=(cx - 1.0, 0.5, -0.6), direction=(-0.62, -1.0, 0.72), dist=60.0, lens=35)),
        ('bridgehead', dict(target=(4.0, -0.3, -0.35), direction=(-0.50, -1.0, 0.52), dist=12.5, lens=35)),
        ('river', dict(target=(7.0, 2.0, -0.6), direction=(0.05, -1.0, 0.30), dist=17.0, lens=32)),
        ('stream', dict(target=(6.6, -7.0, -1.05), direction=(-0.55, -1.0, 0.95), dist=6.0, lens=35)),
        ('top', dict(target=(cx, 0.0, 0.0), direction=(0.0, 0.0, 1.0), dist=80.0, ortho=max(x_max - x_min, 2 * Y_EDGE * 16 / 9) * 1.04)),
        ('seam_road', dict(target=tuple(seam_road + Vector((0, 0, 0.05))), direction=(-0.35, -1.0, 0.55), dist=3.6, lens=35)),
        ('seam_bank', dict(target=(3.7, 4.0, -0.35), direction=(1.0, -0.15, 0.55), dist=4.2, lens=35)),
        ('seam_deck', dict(target=(2.0, 0.6, 0.1), direction=(-0.75, -1.0, 0.6), dist=3.4, lens=35)),
    ]
    seams = {'seam_road': [seam_road + Vector(p) for p in ((0, -2.25, 0.02), (0, 2.25, 0.02))],
             'seam_bank': [Vector((K.BANK_LINE_X - v, K.BH_BANK_A, K.bank_z(v))) for v in (1.0, -2.0)],
             'seam_deck': [Vector((K.RAMP_L, -1.5, K.DECK_Z)), Vector((K.RAMP_L, 1.5, K.DECK_Z))]}
    labels = {}
    for tag, kw in views:
        set_camera(cam, **kw); bpy.context.view_layer.update()
        p = KB.new_output('%s/%s_%s.png' % (out_dir, name, tag)); scene.render.filepath = str(p)
        bpy.ops.render.render(write_still=True, scene=scene.name)
        def to2d(w):
            c = world_to_camera_view(scene, cam, Vector(w)); return [c.x, 1.0 - c.y, c.z]
        rec = {'file': p.name, 'items': []}
        if tag in ('hero', 'bridgehead', 'top'):
            for code, where in LABELS:
                T = next((T for c, T, t in kit.placed if c == code and t == where), None)
                if T is None: continue
                q = to2d(anchor_of(code, T))
                if 0.02 < q[0] < 0.98 and 0.02 < q[1] < 0.98 and q[2] > 0: rec['items'].append({'text': label_text(code, where), 'xy': q[:2]})
            q = to2d((7.0, 0.0, K.DECK_Z))
            rec['items'].append({'text': 'D02 木造梁橋（新增）', 'xy': q[:2]})
            q = to2d((7.0, -9.0, K.WATER_Z))
            if 0 < q[0] < 1 and 0 < q[1] < 1: rec['items'].append({'text': '測試水位 -0.80 m', 'xy': q[:2]})
        if tag in seams:
            rec['seam'] = [to2d(w)[:2] for w in seams[tag]]
        labels[tag] = rec
        print('RENDERED', tag, flush=True)
    KB.new_output('%s/%s_labels.json' % (out_dir, name)).write_text(json.dumps(labels, ensure_ascii=False, indent=2))
    if not preview:
        bpy.ops.wm.save_as_mainfile(filepath=str(KB.new_output('%s/%s_scene.blend' % (out_dir, name))), relative_remap=True)
    print('DONE', flush=True)


if __name__ == '__main__':
    main()
