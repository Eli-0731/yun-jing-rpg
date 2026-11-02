"""Work pack 02-B comparison renders: each MK asset beside the things it lives with, at true scale.

  compare_MK01: steelyard hung on HerbalStall v002 Socket_Scale, 1.75 m stand-in keeper behind the counter
  compare_MK02: sieve, bundles and plants beside Market_DryingRack (dondon v001) and the alchemy B04 sorting trays
  compare_MK03: price board leaning on the stall, coin string / purse on the counter, MK01 hung above

Reads the v001 .blend files (LOD0 meshes, baked textures) and the reference models read-only; writes only
art/previews/harvest-market-b/<ID>/compare_<ID>.png.

blender --background --factory-startup --python art/source/harvest-market-b/compare_views.py -- [MK01 MK02 MK03]
"""
import bpy, bmesh, math, sys
from pathlib import Path
from mathutils import Vector, Matrix

ART = Path(__file__).resolve().parents[2]
KIT = 'harvest-market-b'
STALL = ART / 'incoming/dondon/HerbalStall/v002/HerbalStall_v002.blend'
RACK = ART / 'incoming/dondon/DryingRack/v001/DryingRack_v001.blend'
TRAYS = ART / 'exports/qingxi-alchemy-b/B04_BambooSortingTrays/v001/B04_BambooSortingTrays.glb'
SOCKET_SCALE = Vector((.45, -.649, 2.005))
HUMAN = 1.75


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 48; sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
    sc.view_settings.view_transform = 'AgX'
    w = bpy.data.worlds.new('Sky'); w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (.5, .55, .58, 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = .6; sc.world = w
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sc.collection.objects.link(sun)
    sun.data.energy = 3.2; sun.data.angle = math.radians(4); sun.rotation_euler = (math.radians(50), 0, math.radians(-35))
    me = bpy.data.meshes.new('Ground'); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=20); bm.to_mesh(me); bm.free()
    g = bpy.data.objects.new('Ground', me); sc.collection.objects.link(g)
    m = bpy.data.materials.new('Ground'); m.use_nodes = True; m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.24, .22, .19, 1)
    me.materials.append(m)
    return sc


def append_all(path, keep=lambda o: True):
    """Every object of another .blend (meshes and empties), parented as saved."""
    with bpy.data.libraries.load(str(path), link=False) as (src, dst):
        dst.objects = list(src.objects)
    objs = [o for o in dst.objects if o is not None and keep(o)]
    for o in objs:
        if o.type not in ('MESH', 'EMPTY'): continue
        bpy.context.scene.collection.objects.link(o)
    bpy.context.view_layer.update()
    return [o for o in objs if o.type in ('MESH', 'EMPTY')]


def asset(aid):
    """LOD0 meshes and sockets of one MK asset, textures relinked to the export folder."""
    objs = append_all(ART / 'source' / KIT / 'blend' / f'{aid}_v001.blend',
                      keep=lambda o: o.name.endswith('_LOD0') or o.name.lower().startswith('socket') or o.name == aid)
    for img in bpy.data.images:
        if img.source == 'FILE' and img.filepath:
            p = ART / 'exports' / KIT / aid / 'Textures' / Path(bpy.path.abspath(img.filepath)).name
            if p.exists(): img.filepath = str(p); img.reload()
    root = next(o for o in objs if o.name == aid)
    return root, {o.name: o for o in objs}


def figure(at, name='Keeper175'):
    """Plain 1.75 m stand-in (no face): it is a scale reference, not a character."""
    m = bpy.data.materials.new('Figure'); m.use_nodes = True; m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.5, .5, .52, 1)
    def part(bm_fn):
        me = bpy.data.meshes.new(name); bm = bmesh.new(); bm_fn(bm); bm.to_mesh(me); bm.free()
        for p in me.polygons: p.use_smooth = True
        o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); me.materials.append(m)
        o.location = at
    for s in (-1, 1):
        part(lambda bm, s=s: bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=.075, radius2=.065, depth=.86, matrix=Matrix.Translation((s * .095, 0, .43))))
        part(lambda bm, s=s: bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=.05, radius2=.042, depth=.62, matrix=Matrix.Translation((s * .25, 0, 1.11))))
    part(lambda bm: bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=.19, radius2=.17, depth=.64, matrix=Matrix.Translation((0, 0, 1.14))))
    part(lambda bm: bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=16, radius=.11, matrix=Matrix.Translation((0, 0, HUMAN - .11))))


def camera(target, direction, dist, lens=35):
    sc = bpy.context.scene
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.lens = lens; d = Vector(direction).normalized()
    cam.location = Vector(target) + d * dist; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()


def hang_mk01(at_socket):
    root, objs = asset('MK01_Steelyard')
    bpy.context.view_layer.update()   # appended objects have no evaluated world matrix until the layer updates
    hook = objs['SOCKET_hook'].matrix_world.translation.copy()
    root.matrix_world = Matrix.Translation(at_socket - hook) @ root.matrix_world
    return root


def render(aid, name):
    out = ART / 'previews' / KIT / aid; out.mkdir(parents=True, exist_ok=True)
    sc = bpy.context.scene; sc.render.filepath = str(out / name); bpy.ops.render.render(write_still=True)
    print('COMPARE', aid, out / name, flush=True)


def mk01():
    reset(); append_all(STALL); hang_mk01(SOCKET_SCALE); figure(Vector((-.25, .25, 0)))
    camera((.15, -.5, 1.55), (.35, -1, .18), 4.2, lens=40)
    render('MK01_Steelyard', 'compare_MK01_stall_keeper.png')


def mk02():
    reset()
    root, _ = asset('MK02_HarvestSieve')
    rack = append_all(RACK)
    for o in rack:
        if o.parent is None: o.matrix_world = Matrix.Translation((-1.45, .35, 0)) @ o.matrix_world
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=str(TRAYS))
    for o in set(bpy.data.objects) - before:
        if o.parent is None: o.matrix_world = Matrix.Translation((1.15, .25, 0)) @ o.matrix_world
    figure(Vector((2.05, .55, 0)))
    camera((.25, 0, .55), (.2, -1, .42), 4.6, lens=40)
    render('MK02_HarvestSieve', 'compare_MK02_rack_alchemy.png')


def mk03():
    reset(); append_all(STALL); hang_mk01(SOCKET_SCALE)
    root, objs = asset('MK03_PriceBoard')
    # board leans against the stall's left stone foot, coins and purse go on the counter top (z 1.077)
    board = [o for n, o in objs.items() if n == 'MK03_PriceBoard_LOD0' or n.startswith('MK03_PriceBoard_PlateDemand')]
    table = [o for n, o in objs.items() if any(k in n for k in ('CoinString', 'LooseCoins', 'Purse'))]
    for o in board: o.matrix_world = Matrix.Translation((-2.0, -.55, 0)) @ Matrix.Rotation(math.radians(-8), 4, 'X') @ Matrix.Rotation(math.radians(15), 4, 'Z') @ o.matrix_world
    for o in table: o.matrix_world = Matrix.Translation((.05, -.5, 1.077)) @ o.matrix_world   # front strip of the counter, clear of the trays
    figure(Vector((-.25, .25, 0)))
    camera((-.6, -.5, 1.0), (.1, -1, .2), 4.6, lens=38)
    render('MK03_PriceBoard', 'compare_MK03_scale_stall.png')


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for key, fn in (('MK01', mk01), ('MK02', mk02), ('MK03', mk03)):
        if not argv or key in argv: fn()
