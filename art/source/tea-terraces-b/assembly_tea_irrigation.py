"""2026-11-07 pack: 40 x 40 m tea-field sample with TE04 (baskets, drying trays) and TE05 (lookout pavilion), and RI03 beside WM02 in one scene.

  blender --background --factory-startup --python art/source/tea-terraces-b/assembly_tea_irrigation.py -- [--render]

Writes art/exports/tea-terraces-b/assembly-20261107/farm-assembly.json and wheel-compare.json. With --render it also saves
blend/assembly_tea_irrigation_v001.blend and the previews in art/previews/tea-terraces-b/assembly-20261107/.
The earlier 9-row sample (assembly_tea_terraces_b.py, exports/.../assembly/) is left as it is.

Layout (Blender axes, metres; Unity = (x, z, y)):
  rows 0-7 of the earlier sample (same pieces, stairs, paths and bushes); row 8 is replaced by a flat lookout at the top of the slope,
  y 14 .. 20 at z 8 (row 7 soil height). The lookout ground is a placeholder plane, not part of the kit.
  TE05 stands on the lookout at (5, 17.3, 8), steps facing -Y down the slope; three TE04 trays dry on the lookout beside it;
  TE04 baskets stand on the row paths and the lookout. Every basket and tray is dropped onto what is under it (ray cast on the LOD0 meshes).
Wheel scene: one channel along Y; RI03 axle at z 4.0, WM02 (creek-repair-b) axle at z 2.0 nine metres in front, the bank at z 0, water at z -0.15.
None of this is an official placement in the game scene.
"""
import bpy, sys, json, math
from pathlib import Path
from mathutils import Matrix, Vector
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import assembly_tea_terraces_b as base

ART = HERE.parents[1]; KIT = 'tea-terraces-b'; VER = 'v001'
OUT = ART / 'exports' / KIT / 'assembly-20261107'
PREV = ART / 'previews' / KIT / 'assembly-20261107'
ROWS = 8
Z_TOP = 8.                      # row 7 soil, the lookout ground
LOOK_Y = (14., 20.)
PAV = (5., 17.3)
TRAYS = [(-2.0, 15.9, 6.), (-.4, 16.6, -12.), (-2.3, 17.3, 3.)]
BASKETS = [(-3.7, 16.4, 20.), (-4.8, None, 1, 140.), (-7.3, None, 3, -30.), (2.6, None, 5, 75.)]    # (x, y | None -> beside the path of row k, row, rot)
WHEELS = {'RI03_GreatWheel': ('tea-terraces-b', (0., 0., 4.)), 'WM02_WaterWheel': ('creek-repair-b', (-.1, -9., 2.))}
CHANNEL_X = (-.86, .57)          # RI03's tubes swing out to x -0.83 on the -X side; its footing slabs start at x 0.58


def fbx_path(kit, aid):
    f = ART / 'exports' / kit / aid / 'model_info.json'
    v = json.loads(f.read_text(encoding='utf-8')).get('version', VER) if f.exists() else VER
    return ART / 'exports' / kit / aid / f'{aid}_{v}.fbx', f'{aid}/{aid}_{v}.fbx'


def layout():
    P = [e for e in base.layout() if e.get('row', 0) < ROWS]
    def add(aid, x, y, z, rot=0., note=None, snap=False):
        e = {'id': aid, 'fbx': fbx_path(KIT, aid)[1], 'position_m': [round(x, 4), round(y, 4), round(z, 4)], 'rotation_z_deg': round(rot, 2), 'mirror_x': False}
        if note: e['note'] = note
        if snap: e['snap'] = 'z from a ray cast onto the LOD0 meshes below'
        P.append(e)
    add('TE05_Pavilion', PAV[0], PAV[1], Z_TOP, note='lookout pavilion; steps face -Y down the slope')
    for x, y, r in TRAYS: add('TE04_Tray', x, y, Z_TOP, r, note='drying tray on the lookout', snap=True)
    for b in BASKETS:
        if b[1] is not None: add('TE04_Basket', b[0], b[1], Z_TOP, b[2], note='on the lookout beside the trays', snap=True)
        else:
            x, _, k, r = b
            add('TE04_Basket', x, base.front(k) + base.PATH_D + .55, k + 1., r, note=f'set down at the uphill edge of the row {k} path', snap=True)
    return P


def wheel_doc():
    pieces = []
    for aid, (kit, pos) in WHEELS.items():
        info = json.loads((ART / 'exports' / kit / aid / 'model_info.json').read_text(encoding='utf-8'))
        lo_z = pos[2] - info['dimensions_m'][2] / 2
        pieces.append({'id': aid, 'kit': kit, 'fbx': fbx_path(kit, aid)[1], 'axle_position_m': list(pos), 'dimensions_m': info['dimensions_m'],
                       'lowest_point_z_m': round(lo_z, 3), 'dips_below_bank_m': round(-lo_z, 3), 'lod_totals': info.get('lod_totals'), 'slot': info.get('slot')})
    a, b = pieces
    return {'name': 'RI03 beside WM02, same scene', 'units': 'meters', 'bank_z_m': 0., 'water_z_m': -.15, 'channel_x_m': list(CHANNEL_X),
            'figure_height_m': 1.75, 'diameter_ratio': round(a['dimensions_m'][2] / b['dimensions_m'][2], 3), 'pieces': pieces,
            'note': 'one channel along Y; both wheels turn about Blender X. Placement for comparison only, not a game-scene placement.'}


def write():
    P = layout(); OUT.mkdir(parents=True, exist_ok=True)
    counts = {}
    for e in P: counts[e['id']] = counts.get(e['id'], 0) + 1
    doc = {'name': 'tea-irrigation 2026-11-07: 40 x 40 m tea-field sample with TE04 / TE05', 'version': VER, 'units': 'meters',
           'axes': 'Blender: x right, y back (+Y uphill), z up. Unity with bakeAxisConversion: (x, z, y); rotation_z_deg becomes a rotation about Unity -Y',
           'extent_m': {'x': [-20, 20], 'y': [-20, 20], 'z': [0, Z_TOP + 5]}, 'rows': ROWS,
           'row_rule': 'as the earlier sample: row k front edge y = -18 + 4k, piece origin z = k, soil z = k + 1',
           'placeholders': ['flat strip y -20 .. -18 at z 0', f'flat lookout y {LOOK_Y[0]} .. {LOOK_Y[1]} at z {Z_TOP}'],
           'counts': counts, 'not_included': 'bends; no official placement in the game scene', 'pieces': P}
    return doc


def save(doc, name):
    path = OUT / name; path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding='utf-8')
    print('ASSEMBLY_JSON', path, len(doc['pieces']), flush=True)


# ------------------------------------------------------------------ Blender scene
def import_lod0(path, lib):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(path))
    new = [o for o in bpy.data.objects if o not in before]
    keep = [o for o in new if o.type == 'MESH' and o.name.split('.')[0].endswith('_LOD0')]
    for o in new:
        for c in list(o.users_collection): c.objects.unlink(o)
    for o in keep:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw; lib.objects.link(o)
    return keep


def plane(name, coll, x0, x1, y0, y1, z, rgb, rough=.9):
    me = bpy.data.meshes.new(name); me.from_pydata([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], [], [(0, 1, 2, 3)])
    o = bpy.data.objects.new(name, me); coll.objects.link(o)
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Roughness'].default_value = rough; me.materials.append(m)
    return o


def figure(coll, at):
    import bmesh
    m = bpy.data.materials.new('Figure'); m.use_nodes = True; m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.46, .48, .5, 1)
    parts = []
    def solid(name, build):
        me = bpy.data.meshes.new(name); bm = bmesh.new(); build(bm); bm.to_mesh(me); bm.free()
        for p in me.polygons: p.use_smooth = True
        o = bpy.data.objects.new(name, me); me.materials.append(m); coll.objects.link(o); o.matrix_world = Matrix.Translation(at); parts.append(o)
    def cyl(name, r1, r2, z0, z1, x=0.):
        solid(name, lambda bm: bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=r1, radius2=r2, depth=z1 - z0, matrix=Matrix.Translation((x, 0, (z0 + z1) / 2))))
    for s in (-1, 1):
        cyl('Leg', .075, .065, 0, .86, s * .095); cyl('Arm', .05, .042, .80, 1.42, s * .25)
    cyl('Body', .19, .17, .82, 1.46); cyl('Neck', .05, .05, 1.44, 1.53)
    solid('Head', lambda bm: bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=16, radius=.11, matrix=Matrix.Translation((0, 0, 1.64))))
    return parts


def outdoor_light(scene, coll):
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); coll.objects.link(sun)
    sun.data.energy = 3.2; sun.data.angle = math.radians(2.5); sun.rotation_euler = (math.radians(52), 0, math.radians(-38))
    scene.world = bpy.data.worlds.new('Sky'); scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes['Background']; bg.inputs[0].default_value = (.42, .5, .58, 1); bg.inputs[1].default_value = .8
    scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.use_denoising = True
    scene.render.image_settings.file_format = 'PNG'; scene.view_settings.view_transform = 'AgX'


def shoot(scene, name, eye, tgt, lens, samples=64, res=(1600, 1000)):
    cam = scene.camera
    if cam is None:
        cam = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera')); scene.collection.objects.link(cam); scene.camera = cam
    cam.data.lens = lens; cam.data.clip_end = 300; cam.location = eye
    cam.rotation_euler = (Vector(tgt) - Vector(eye)).to_track_quat('-Z', 'Y').to_euler()
    scene.render.resolution_x, scene.render.resolution_y = res; scene.render.resolution_percentage = 100
    scene.cycles.samples = samples; scene.render.filepath = str(PREV / f'{name}.png'); bpy.ops.render.render(write_still=True)


def place(doc, coll, src, kit=KIT, key='position_m'):
    out = []
    for e in doc['pieces']:
        if e['id'] not in src: src[e['id']] = import_lod0(fbx_path(e.get('kit', kit), e['id'])[0], LIB)
        M = Matrix.Translation(e[key]) @ Matrix.Rotation(math.radians(e.get('rotation_z_deg', 0.)), 4, 'Z') @ Matrix.Diagonal((-1. if e.get('mirror_x') else 1., 1., 1., 1.))
        objs = []
        for o in src[e['id']]:
            d = o.copy(); d.matrix_world = M @ o.matrix_world; coll.objects.link(d); objs.append(d)
        out.append((e, objs))
    return out


def snap(placed, ground):
    """Drop each snapped piece so the highest ground under its footprint (centre and four corners) meets its base."""
    dg = bpy.context.evaluated_depsgraph_get(); scene = bpy.context.scene
    hide = {o: o.hide_get() for o in scene.objects}
    for e, objs in placed:
        if not e.get('snap'): continue
        for o in objs: o.hide_set(True)          # never hit itself
        from ti_pipeline import eval_bounds
        lo, hi = eval_bounds(objs)
        x, y = e['position_m'][:2]; best = None
        for dx, dy in ((0, 0), (lo.x - x, lo.y - y), (hi.x - x, lo.y - y), (lo.x - x, hi.y - y), (hi.x - x, hi.y - y)):
            p = Vector((x + dx * .8, y + dy * .8, e['position_m'][2] + 3.))
            ok, loc, *_ = scene.ray_cast(dg, p, Vector((0, 0, -1)), distance=8.)
            if ok and (best is None or loc.z > best): best = loc.z
        for o in objs: o.hide_set(False)
        if best is None: continue
        dz = best - e['position_m'][2]
        for o in objs: o.matrix_world = Matrix.Translation((0, 0, dz)) @ o.matrix_world
        e['position_m'][2] = round(best, 4)
        dg = bpy.context.evaluated_depsgraph_get()
    for o, h in hide.items(): o.hide_set(h)


LIB = None


def main(render):
    global LIB
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    LIB = bpy.data.collections.new('Library'); scene.collection.children.link(LIB); LIB.hide_render = True; LIB.hide_viewport = True
    src = {}
    # ---- tea field
    field = bpy.data.collections.new('TeaField'); scene.collection.children.link(field)
    doc = write()
    placed = place(doc, field, src)
    plane('Placeholder_Strip', field, -22, 22, -20, -18, 0., (.12, .09, .055))
    plane('Placeholder_Lookout', field, -20, 20, LOOK_Y[0], LOOK_Y[1], Z_TOP, (.16, .13, .08))
    snap(placed, field)
    save(doc, 'farm-assembly.json')
    # ---- wheels, 60 m off to the side so the two scenes never share a frame
    wheels = bpy.data.collections.new('WheelCompare'); scene.collection.children.link(wheels)
    wd = wheel_doc(); OFF = Vector((70., 0., 0.))
    for p in wd['pieces']: p['scene_offset_m'] = list(OFF)
    wdoc = {'pieces': [dict(p, position_m=list(Vector(p['axle_position_m']) + OFF)) for p in wd['pieces']]}
    wplaced = place(wdoc, wheels, src)
    x0, x1 = CHANNEL_X
    for name, a, b in (('Bank_W', -12., x0), ('Bank_E', x1, 12.)):
        plane(name, wheels, OFF.x + a, OFF.x + b, -16., 9., 0., (.15, .14, .09))
    plane('Channel_Floor', wheels, OFF.x + x0, OFF.x + x1, -16., 9., -.6, (.06, .055, .04))
    plane('Channel_Water', wheels, OFF.x + x0, OFF.x + x1, -16., 9., -.15, (.03, .055, .06), rough=.08)
    figure(wheels, OFF + Vector((2.2, -4.4, 0.)))
    save(wd, 'wheel-compare.json')
    print('PLACED', len(placed), 'wheels', len(wplaced), flush=True)
    if not render: return
    (HERE / 'blend').mkdir(exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE / 'blend' / f'assembly_tea_irrigation_{VER}.blend'))
    PREV.mkdir(parents=True, exist_ok=True)
    sun_coll = bpy.data.collections.new('Light'); scene.collection.children.link(sun_coll)
    outdoor_light(scene, sun_coll)
    wheels.hide_render = True
    shoot(scene, 'field_aerial', (34., -40., 34.), (0., 0., 3.), 30)
    shoot(scene, 'field_lookout_from_row7', (-9., 11.2, 9.6), (5., 17.3, 9.3), 24)
    shoot(scene, 'field_trays_and_pavilion', (-5.5, 13.6, 10.2), (-.5, 17., 8.2), 32)
    shoot(scene, 'field_from_pavilion', (5., 16.6, 9.75), (-4., -6., 4.), 24)
    shoot(scene, 'field_basket_on_path', (-9.5, base.front(3) + .6, 4 + 1.5), (-7.3, base.front(3) + base.PATH_D + .55, 4.2), 30)
    wheels.hide_render = False; field.hide_render = True
    shoot(scene, 'wheels_side_by_side', tuple(OFF + Vector((19., -4.5, 3.2))), tuple(OFF + Vector((0., -4.3, 2.2))), 30)
    shoot(scene, 'wheels_three_quarter', tuple(OFF + Vector((14., -20., 6.))), tuple(OFF + Vector((0., -3.5, 2.))), 30)
    print('ASSEMBLY_RENDERED', PREV, flush=True)


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    main('--render' in argv)
