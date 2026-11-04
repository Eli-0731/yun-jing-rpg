"""Work pack comparison renders, each at true scale with a 1.75 m stand-in:

  CR05 beside RK04 tea stall   (art/exports/tea-brewing-b/RK04_TeaStall/v001)
  CR09 A and B beside B05      (art/exports/qingxi-waterworks-b/B05)
  CR12 beside the NoticeBoard  (art/incoming/dondon/NoticeBoard/v002, placed in town as NoticeBoard_SettlementExit)
  WM01 and WM09 beside H01     (art/exports/qingxi-world-ruins-b/H01_StoneTimberHouse)
  WM07 and WM05 beside the riverbank module (art/exports/qingxi-riverbank-v2)
  CR03 beside B11 cart, CR04 beside C07 toolbox, CR06 and CR08 beside B02/B03, CR07 beside CR05
  WM02 and WM04 beside WM01, CR10 and CR11 beside CR12 (the pieces they will stand next to in game)

Reads the v001 .blend files (LOD0 meshes, baked textures) and the reference exports read-only; writes only
art/previews/creek-repair-b/<ID>/compare_<ID>.png.

blender --background --factory-startup --python art/source/creek-repair-b/compare_views.py -- [CR05 CR09 CR12]
"""
import bpy, bmesh, math, sys
from pathlib import Path
from mathutils import Vector, Matrix

ART = Path(__file__).resolve().parents[2]
KIT = 'creek-repair-b'
HUMAN = 1.75


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 64; sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
    sc.view_settings.view_transform = 'AgX'; sc.view_settings.exposure = -.3
    w = bpy.data.worlds.new('Sky'); w.use_nodes = True; bg = w.node_tree.nodes['Background']
    bg.inputs[0].default_value = (.5, .55, .58, 1); bg.inputs[1].default_value = .75; sc.world = w
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sc.collection.objects.link(sun)
    sun.data.energy = 3.0; sun.data.angle = math.radians(5); sun.rotation_euler = (math.radians(52), 0, math.radians(-32))
    me = bpy.data.meshes.new('Ground'); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=30); bm.to_mesh(me); bm.free()
    g = bpy.data.objects.new('Ground', me); sc.collection.objects.link(g)
    m = bpy.data.materials.new('Ground'); m.use_nodes = True; m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.24, .22, .19, 1)
    me.materials.append(m)
    return sc


def ours(aid, at):
    with bpy.data.libraries.load(str(ART / 'source' / KIT / 'blend' / f'{aid}_v001.blend'), link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n.endswith('_LOD0') or n == aid]
    objs = [o for o in dst.objects if o is not None]
    for o in objs:
        bpy.context.scene.collection.objects.link(o); o.hide_render = False
    for img in bpy.data.images:
        if img.source == 'FILE' and img.filepath:
            p = ART / 'exports' / KIT / aid / 'Textures' / Path(bpy.path.abspath(img.filepath)).name
            if p.exists(): img.filepath = str(p); img.reload()
    root = next(o for o in objs if o.name == aid)
    root.matrix_world = Matrix.Translation(at) @ root.matrix_world
    bpy.context.view_layer.update()


def theirs(path, at, base=None, lod0_only=True):
    before = set(bpy.data.objects)
    if path.suffix == '.glb': bpy.ops.import_scene.gltf(filepath=str(path))
    else: bpy.ops.import_scene.fbx(filepath=str(path))
    new = set(bpy.data.objects) - before
    if lod0_only:
        for o in list(new):
            if o.name.split('.')[0].endswith(('_LOD1', '_LOD2')) or '_Collision' in o.name:
                new.discard(o); bpy.data.objects.remove(o, do_unlink=True)
    for o in new:
        if o.parent is None: o.matrix_world = Matrix.Translation(at) @ o.matrix_world
        if base and o.type == 'MESH':
            m = bpy.data.materials.new('Base'); m.use_nodes = True
            t = m.node_tree.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(str(base))
            m.node_tree.links.new(t.outputs[0], m.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
            o.data.materials.clear(); o.data.materials.append(m)
    bpy.context.view_layer.update()


def figure(at):
    m = bpy.data.materials.new('Figure'); m.use_nodes = True; m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.5, .5, .52, 1)
    def part(fn):
        me = bpy.data.meshes.new('Figure175'); bm = bmesh.new(); fn(bm); bm.to_mesh(me); bm.free()
        for p in me.polygons: p.use_smooth = True
        o = bpy.data.objects.new('Figure175', me); bpy.context.scene.collection.objects.link(o); me.materials.append(m); o.location = at
    for s in (-1, 1):
        part(lambda bm, s=s: bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=.075, radius2=.065, depth=.86, matrix=Matrix.Translation((s * .095, 0, .43))))
        part(lambda bm, s=s: bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=.05, radius2=.042, depth=.62, matrix=Matrix.Translation((s * .25, 0, 1.11))))
    part(lambda bm: bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=.19, radius2=.17, depth=.64, matrix=Matrix.Translation((0, 0, 1.14))))
    part(lambda bm: bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=16, radius=.11, matrix=Matrix.Translation((0, 0, HUMAN - .11))))


def shoot(aid, name, target, direction, dist, lens=40):
    sc = bpy.context.scene
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.lens = lens; d = Vector(direction).normalized()
    cam.location = Vector(target) + d * dist; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    out = ART / 'previews' / KIT / aid; out.mkdir(parents=True, exist_ok=True)
    sc.render.filepath = str(out / name); bpy.ops.render.render(write_still=True)
    print('COMPARE', aid, out / name, flush=True)


def cr05():
    reset(); ours('CR05_WorkShelter', Vector((-2.2, 0, 0)))
    r = ART / 'exports/tea-brewing-b/RK04_TeaStall/v001'
    theirs(r / 'RK04_TeaStall_v001.fbx', Vector((2.1, 0, 0)), r / 'Textures/RK04_TeaStall_BaseColor.png')
    figure(Vector((.15, -1.3, 0)))
    shoot('CR05_WorkShelter', 'compare_CR05_RK04.png', (0, 0, 1.25), (.05, -1, .22), 9.2)


def cr10():
    reset(); ours('CR10_CharmStall', Vector((-2.2, 0, 0)))
    r = ART / 'exports/tea-brewing-b/RK04_TeaStall/v001'
    theirs(r / 'RK04_TeaStall_v001.fbx', Vector((2.1, 0, 0)), r / 'Textures/RK04_TeaStall_BaseColor.png')
    figure(Vector((.15, -1.3, 0)))
    shoot('CR10_CharmStall', 'compare_CR10_RK04.png', (0, 0, 1.25), (.05, -1, .22), 9.2)


def cr09():
    reset(); ours('CR09_A_RopeGate', Vector((-.75, 0, 0))); ours('CR09_B_TenonGate', Vector((.3, 0, 0)))
    theirs(ART / 'exports/qingxi-waterworks-b/B05/B05.glb', Vector((1.3, 0, 0)))
    figure(Vector((-1.75, .1, 0)))
    shoot('CR09_A_RopeGate', 'compare_CR09_B05.png', (-.1, 0, .72), (.12, -1, .28), 4.6)


def cr12():
    reset(); ours('CR12_RankingBoard', Vector((-.9, 0, 0)))
    theirs(ART / 'incoming/dondon/NoticeBoard/v002/NoticeBoard_v002.fbx', Vector((2., 0, 0)))
    figure(Vector((.95, -.6, 0)))
    shoot('CR12_RankingBoard', 'compare_CR12_NoticeBoard.png', (.35, 0, 1.3), (.06, -1, .16), 7.4)


def wm_house():
    h = ART / 'exports/qingxi-world-ruins-b/H01_StoneTimberHouse/H01_StoneTimberHouse_v001.glb'
    reset(); ours('WM01_MillHouse', Vector((-4.6, 0, 0))); theirs(h, Vector((4.6, 0, 0)))
    figure(Vector((0, -3.2, 0)))
    shoot('WM01_MillHouse', 'compare_WM01_H01.png', (0, 0, 2.6), (.05, -1, .22), 17.)
    reset(); ours('WM09_BambooPavilion', Vector((-3.4, 0, 0))); theirs(h, Vector((3.8, 0, 0)))
    figure(Vector((-.9, -2.4, 0)))
    shoot('WM09_BambooPavilion', 'compare_WM09_H01.png', (0, 0, 2.3), (.05, -1, .22), 14.)


def wm_river():
    r = ART / 'exports/qingxi-riverbank-v2/qingxi-riverbank-v2.glb'
    reset(); ours('WM07_StoneBridge', Vector((-3.5, 0, 0))); theirs(r, Vector((3.5, 0, 0)))
    figure(Vector((-1, -3.5, 0)))
    shoot('WM07_StoneBridge', 'compare_WM07_Riverbank.png', (0, 0, 1.9), (.5, -1, .28), 17.)
    reset(); ours('WM05_WashSteps', Vector((-3.6, 0, 0))); theirs(r, Vector((3.6, 0, 0)))
    figure(Vector((-.2, -2.4, 0)))
    shoot('WM05_WashSteps', 'compare_WM05_Riverbank.png', (0, 0, 1.), (.1, -1, .3), 14.)


def site():
    w = ART / 'exports/qingxi-waterworks-b'
    reset(); ours('CR03_StonePile', Vector((-2.9, 0, 0))); ours('CR03_TimberRack', Vector((-.1, 0, 0))); ours('CR03_MudHeap', Vector((2.5, 0, 0)))
    theirs(w / 'B11/B11.glb', Vector((4.9, 0, 0))); figure(Vector((-1.4, -1.3, 0)))
    shoot('CR03_StonePile', 'compare_CR03_B11.png', (1., 0, .7), (.06, -1, .28), 10.5)
    reset(); ours('CR04_Tools', Vector((-.6, 0, 0))); theirs(ART / 'exports/qingxi-water-report-c/C07.glb', Vector((1.2, 0, 0))); figure(Vector((-1.9, 0, 0)))
    shoot('CR04_Tools', 'compare_CR04_C07.png', (-.2, 0, .8), (.06, -1, .3), 5.2)
    reset(); ours('CR06_Straight', Vector((-1.5, 0, 0))); ours('CR06_Bend', Vector((.2, 0, 0))); theirs(w / 'B02/B02.glb', Vector((-3., 0, 0))); theirs(w / 'B03/B03.glb', Vector((3.1, 0, 0))); figure(Vector((1.9, 1.6, 0)))
    shoot('CR06_Straight', 'compare_CR06_B02_B03.png', (0, .8, .5), (.06, -1, .55), 8.5)
    reset(); ours('CR08_Straight', Vector((-1.5, 0, 0))); ours('CR08_Bend', Vector((.2, 0, 0))); ours('CR08_Trestle_080', Vector((3.6, 0, 0))); ours('CR08_Trestle_150', Vector((5., 0, 0))); ours('CR08_Trestle_250', Vector((6.7, 0, 0))); theirs(w / 'B02/B02.glb', Vector((-3., 0, 0))); figure(Vector((-3.2, 1.6, 0)))
    shoot('CR08_Straight', 'compare_CR08_B02.png', (1.8, .4, 1.), (.04, -1, .3), 13.)
    reset(); ours('CR07_Celebration', Vector((-2.4, 0, 0))); ours('CR05_WorkShelter', Vector((3.2, 0, 0))); figure(Vector((.5, -1.4, 0)))
    shoot('CR07_Celebration', 'compare_CR07_CR05.png', (.5, 0, 1.2), (.05, -1, .22), 12.5)


def wm_town():
    reset(); ours('WM02_WaterWheel', Vector((5.2, 0, 2.3))); ours('WM01_MillHouse', Vector((0, 0, 0))); figure(Vector((-4.8, -3.2, 0)))
    shoot('WM02_WaterWheel', 'compare_WM02_WM01.png', (1, 0, 2.6), (.12, -1, .2), 17.)
    reset(); ours('WM04_Millstones', Vector((-5.4, -2., 0))); ours('WM01_MillHouse', Vector((0, 0, 0))); figure(Vector((-7., -2., 0)))
    shoot('WM04_Millstones', 'compare_WM04_WM01.png', (-1.5, 0, 2.4), (.08, -1, .2), 16.)
    reset(); ours('CR10_CharmStall', Vector((-3.2, 0, 0))); ours('CR12_RankingBoard', Vector((.8, 0, 0))); ours('CR11_NoodleStall', Vector((5., 0, 0))); figure(Vector((-.9, -1.5, 0)))
    shoot('CR10_CharmStall', 'compare_CR10_CR11_CR12.png', (.9, 0, 1.25), (.05, -1, .2), 13.5)


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for key, fn in (('CR05', cr05), ('CR10', cr10), ('CR09', cr09), ('CR12', cr12), ('WM_HOUSE', wm_house), ('WM_RIVER', wm_river), ('SITE', site), ('WM_TOWN', wm_town)):
        if not argv or key in argv: fn()
