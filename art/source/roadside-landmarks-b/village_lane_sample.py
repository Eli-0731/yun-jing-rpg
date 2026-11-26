"""VH check (work pack B-112h): VH01-03, VL01-05 and RS01-02 laid out as one 30 m village lane, with 1.75 m figures and a ruler.

A review layout only: it imports the exported GLBs (LOD0 kept, LOD1/LOD2 and collision left out), places each house with its
front (-Y in its own file) facing the lane, and renders a plan, a high 3/4 view, two 1.7 m eye-height views down the lane
and an elevation of each side. The houses themselves are not changed and no game scene or block JSON is touched.

Lane: x 0..31 m, 4.5 m wide (y -2.25..2.25), paved. North side VH01, VH03, VL01, VL02; south side VH02, VL03, VL04;
the inn RS01 closes the west end; the blacksmith and material shop stand at the east end either side of the lane's
mouth, and VL05 faces back down the lane from across a 4 m cross street.

blender --background --factory-startup --python village_lane_sample.py -- <houses art root> <out dir>
"""
import bpy, bmesh, json, math, sys
from pathlib import Path
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT = Path(argv[0]), Path(argv[1])
OUT.mkdir(parents=True, exist_ok=True)
HUMAN, LANE_W, LANE_L, GAP = 1.75, 4.5, 31., .3
scene = bpy.context.scene
for o in list(scene.objects): bpy.data.objects.remove(o, do_unlink=True)

KITS = {'VH': 'village-houses-b', 'VL': 'village-houses-b', 'RS': 'village-reskin-b'}
NAMES = {'VH01': 'VH01_TwoStoreyHouse', 'VH02': 'VH02_LCourtyardHouse', 'VH03': 'VH03_NarrowCottage', 'VL01': 'VL01_LongEmptyHouse',
         'VL02': 'VL02_MovedInHouse', 'VL03': 'VL03_HalfCollapsedHouse', 'VL04': 'VL04_DiligentFamilyHouse', 'VL05': 'VL05_ElderlyCoupleHouse',
         'RS01': 'RS01_TownInn', 'RS02a': 'RS02_Blacksmith', 'RS02b': 'RS02_MaterialShop'}


def load(key):
    aid = NAMES[key]; d = SRC / 'exports' / KITS[key[:2]] / aid
    info = json.loads((d / 'model_info.json').read_text(encoding='utf-8'))
    glb = d / f"{aid}_{info.get('version', 'v001')}.glb"
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(glb))
    new = [o for o in bpy.data.objects if o not in before]
    keep = []
    for o in new:
        n = o.name.upper()
        if o.type == 'MESH' and ('_LOD1' in n or '_LOD2' in n or n.startswith('UCX') or 'COLLISION' in n or n.startswith('SOCKET')):
            bpy.data.objects.remove(o, do_unlink=True)
        elif o.type == 'MESH': keep.append(o)
    # one root empty per house so it can be placed as a whole
    root = bpy.data.objects.new(f'Place_{key}', None); scene.collection.objects.link(root)
    for o in keep:
        mw = o.matrix_world.copy(); o.parent = root; o.matrix_world = mw
    for o in [o for o in bpy.data.objects if o in set(new) and o.name in bpy.data.objects and o.type != 'MESH']:
        if not o.children: bpy.data.objects.remove(o, do_unlink=True)
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in keep:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c); lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in keep)
    return root, lo, hi, info, tris


placed = []


def place(key, yaw, anchor):
    """yaw: 0 front faces -Y, pi front faces +Y, pi/2 front faces +X, -pi/2 front faces -X. anchor: function (lo, hi rotated) -> offset."""
    root, lo, hi, info, tris = load(key)
    R = Matrix.Rotation(yaw, 4, 'Z')
    pts = [R @ Vector((x, y, 0)) for x in (lo.x, hi.x) for y in (lo.y, hi.y)]
    rlo = Vector((min(p.x for p in pts), min(p.y for p in pts), lo.z)); rhi = Vector((max(p.x for p in pts), max(p.y for p in pts), hi.z))
    off = anchor(rlo, rhi)
    root.matrix_world = Matrix.Translation(off) @ R
    box = (rlo + off, rhi + off)
    placed.append({'key': key, 'asset': NAMES[key], 'version': info.get('version', 'v001'), 'yaw_deg': round(math.degrees(yaw)),
                   'min_m': [round(v, 2) for v in box[0]], 'max_m': [round(v, 2) for v in box[1]],
                   'size_m': [round(v, 2) for v in (box[1] - box[0])], 'lod0_tris': tris})
    return box


# north side: fronts face -Y, front line on y = +LANE_W/2
x = 0.
for k in ('VH01', 'VH03', 'VL01', 'VL02'):
    b = place(k, 0., lambda lo, hi, x=x: Vector((x - lo.x, LANE_W / 2 - lo.y, 0)))
    x = b[1].x + GAP
north_end = x - GAP
# south side: turned round, fronts face +Y, front line on y = -LANE_W/2
x = 0.
for k in ('VH02', 'VL03', 'VL04'):
    b = place(k, math.pi, lambda lo, hi, x=x: Vector((x - lo.x, -LANE_W / 2 - hi.y, 0)))
    x = b[1].x + GAP
south_end = x - GAP
lane_end = max(north_end, south_end)
# west end: the inn faces down the lane (+X) across its head
inn = place('RS01', math.pi / 2, lambda lo, hi: Vector((-GAP - hi.x, -(lo.y + hi.y) / 2 - 1.5, 0)))
# east end: blacksmith (south) and material shop (north) face back up the lane (-X), the lane's mouth open between them;
# beyond them a 4 m cross street, and VL05 across it facing back down the lane
CROSS = lane_end + 2.5
a = place('RS02a', -math.pi / 2, lambda lo, hi: Vector((CROSS - lo.x, -LANE_W / 2 - .2 - hi.y, 0)))
b = place('RS02b', -math.pi / 2, lambda lo, hi: Vector((CROSS - lo.x, LANE_W / 2 + .2 - lo.y, 0)))
east_x = max(a[1].x, b[1].x) + 4.
place('VL05', -math.pi / 2, lambda lo, hi: Vector((east_x - lo.x, -(lo.y + hi.y) / 2, 0)))


def mat(name, rgb, rough=.8, emit=0.):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Roughness'].default_value = rough
    if emit: b.inputs['Emission Color'].default_value = (*rgb, 1); b.inputs['Emission Strength'].default_value = emit
    return m


def solid(name, build, m):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); build(bm); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); scene.collection.objects.link(o); me.materials.append(m); return o


grey, ink, chalk = mat('Figure', (.3, .31, .33)), mat('Ruler', (.85, .70, .38), .5), mat('Chalk', (.9, .86, .74), .6)


def figure(pos, yaw=0.):
    parts = []
    def cyl(name, r1, r2, z0, z1, x=0.):
        def b(bm):
            bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=r1, radius2=r2, depth=z1 - z0, matrix=Matrix.Translation((x, 0, (z0 + z1) / 2)))
        parts.append(solid(name, b, grey))
    for s in (-1, 1):
        cyl('Fig_Leg', .075, .065, 0, .86, s * .095); cyl('Fig_Arm', .05, .042, .80, 1.42, s * .25)
    cyl('Fig_Body', .19, .17, .82, 1.46); cyl('Fig_Neck', .05, .05, 1.44, 1.53)
    parts.append(solid('Fig_Head', lambda bm: bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=.11, matrix=Matrix.Translation((0, 0, HUMAN - .11))), grey))
    for o in parts: o.matrix_world = Matrix.Translation(pos) @ Matrix.Rotation(yaw, 4, 'Z')
    return parts


def ruler(pos, yaw=0.):
    parts = []
    def box(name, sx, sz, z, x=0.):
        def b(bm): bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation((x, 0, z)) @ Matrix.Diagonal((sx, .02, sz, 1)))
        parts.append(solid(name, b, ink))
    box('Ruler_Bar', .025, HUMAN, HUMAN / 2)
    for i in range(8):
        z = i * .25 if i < 7 else HUMAN
        box('Ruler_Tick', .09 if i % 2 == 0 or i == 7 else .055, .012, z, .03)
    for o in parts: o.matrix_world = Matrix.Translation(pos) @ Matrix.Rotation(yaw, 4, 'Z')
    return parts


# figures along the lane, a ruler at its head, and 5 m chalk marks on the paving (0..30 m)
FIGS = [(1.2, -.9, 0.), (6., .6, math.pi), (11.5, -.4, .4), (17., .9, math.pi), (22.5, -.7, 0.), (28.5, .3, math.pi)]
for x, y, yaw in FIGS: figure(Vector((x, y, 0)), yaw + math.pi / 2)
ruler(Vector((.6, .4, 0)), math.pi / 2)
lane = solid('Lane', lambda bm: bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation((LANE_L / 2, 0, -.01)) @ Matrix.Diagonal((LANE_L + 4, LANE_W, .02, 1))), mat('LanePaving', (.2, .19, .17), .9))
for i in range(7):
    solid('Mark', lambda bm, i=i: bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation((i * 5., -LANE_W / 2 + .25, .002)) @ Matrix.Diagonal((.06, .5, .004, 1))), chalk)
ground = solid('Ground', lambda bm: bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=70, matrix=Matrix.Translation((LANE_L / 2 + 6, 0, -.025))), mat('Ground', (.17, .18, .14), .95))

font = None
for fp in ('C:/Windows/Fonts/msjh.ttc', 'C:/Windows/Fonts/msyh.ttc'):
    try: font = bpy.data.fonts.load(fp); break
    except Exception: pass
for i in range(7):
    cu = bpy.data.curves.new('MarkLabel', 'FONT'); cu.body = f'{i * 5} m'; cu.size = .45; cu.align_x = 'CENTER'
    if font: cu.font = font
    t = bpy.data.objects.new('MarkLabel', cu); scene.collection.objects.link(t); cu.materials.append(chalk)
    t.location = (i * 5., -LANE_W / 2 + .9, .004)

sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); scene.collection.objects.link(sun); sun.data.energy = 3.2; sun.data.angle = math.radians(2)
sun.rotation_euler = (math.radians(48), 0, math.radians(32))
w = bpy.data.worlds.new('Sky'); w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (.55, .62, .7, 1)
w.node_tree.nodes['Background'].inputs[1].default_value = .9
scene.world = w
cam_d = bpy.data.cameras.new('Cam'); cam = bpy.data.objects.new('Cam', cam_d); scene.collection.objects.link(cam); scene.camera = cam
scene.render.engine = 'BLENDER_EEVEE'; scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
scene.view_settings.view_transform = 'AgX'
try: scene.eevee.use_shadows = True
except Exception: pass

lo = Vector((min(p['min_m'][0] for p in placed), min(p['min_m'][1] for p in placed), 0)); hi = Vector((max(p['max_m'][0] for p in placed), max(p['max_m'][1] for p in placed), max(p['max_m'][2] for p in placed)))
mid = (lo + hi) / 2
written = []


def shot(name, loc, target, lens=None, ortho=None, clip=.1):
    cam.location = loc; cam_d.clip_start = clip
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    if ortho: cam_d.type = 'ORTHO'; cam_d.ortho_scale = ortho
    else: cam_d.type = 'PERSP'; cam_d.lens = lens or 24
    cam_d.clip_end = 400
    p = OUT / f'{name}.png'; scene.render.filepath = str(p); bpy.ops.render.render(write_still=True); written.append(p.name)


shot('01_plan', (mid.x, mid.y, 80), (mid.x, mid.y + .001, 0), ortho=max(hi.x - lo.x, (hi.y - lo.y) * 1.78) * 1.05)
shot('02_high_three_quarter', (mid.x - 26, mid.y - 34, 30), (mid.x, mid.y, 2), lens=30)
shot('03_eye_1p7_west_to_east', (1.2, -.6, 1.7), (30, .2, 1.9), lens=22)
shot('04_eye_1p7_east_to_west', (lane_end + 1., .5, 1.7), (-5, -.2, 2.2), lens=22)
# elevations: an orthographic camera standing in the lane, so the far side's fronts show and the near side is behind it
shot('05_north_side_elevation', (LANE_L / 2, -1.5, 3.6), (LANE_L / 2, 10, 3.6), ortho=34)
shot('06_south_side_elevation', (LANE_L / 2, 1.5, 3.6), (LANE_L / 2, -10, 3.6), ortho=34)

(OUT / 'village_lane_sample.json').write_text(json.dumps({
    'check': 'VH-檢查 村子樣張', 'source': str(SRC).replace('\\', '/'),
    'lane': {'length_m': LANE_L, 'width_m': LANE_W, 'north_side_end_m': round(north_end, 2), 'south_side_end_m': round(south_end, 2), 'gap_between_houses_m': GAP},
    'figure_height_m': HUMAN, 'figures': len(FIGS), 'eye_height_views_m': 1.7, 'houses': placed,
    'layout_size_m': [round(v, 2) for v in (hi - lo)], 'renders': written,
    'note': 'review layout only, LOD0 meshes from the exported GLBs; houses unchanged; not a game scene'}, ensure_ascii=False, indent=2), encoding='utf-8')
print('LANE', [(p['key'], p['size_m']) for p in placed], round(north_end, 2), round(south_end, 2), written)
