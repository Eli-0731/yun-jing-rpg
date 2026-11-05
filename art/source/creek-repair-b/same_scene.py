"""Each PR's models beside the existing kits in one scene, one light, one camera, with a 1.75 m stand-in: a clay render and a
material render from the same place. Reads the v001 .blend files and the other kits read-only; writes art/previews/creek-repair-b/_qa/.

blender --background --factory-startup --python art/source/creek-repair-b/same_scene.py -- [site a3 stalls]
"""
import bpy, sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
import compare_views as C

ART = C.ART
W = ART / 'exports/qingxi-waterworks-b'
H01 = ART / 'exports/qingxi-world-ruins-b/H01_StoneTimberHouse/H01_StoneTimberHouse_v001.glb'
RK04 = ART / 'exports/tea-brewing-b/RK04_TeaStall/v001'
MK03 = ART / 'exports/harvest-market-b/MK03_PriceBoard'


def ours(aid, x, y=0, z=0):
    C.ours(aid, Vector((x, y, z)))
    for o in bpy.data.objects:   # only the fullest stage of a pile stands; water is not in this pack
        if o.name.startswith(aid) and ('Stage_Low' in o.name or 'Stage_Mid' in o.name or '_water_' in o.name.lower()): o.hide_render = True


def both(name, target, direction, dist, lens=40):
    C.shoot('_qa', f'samescene_{name}_material.png', target, direction, dist, lens)
    clay = bpy.data.materials.new('Clay'); clay.use_nodes = True
    clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.42, .42, .42, 1)
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name != 'Ground' and not o.name.startswith('Figure175'):
            o.data.materials.clear(); o.data.materials.append(clay)
    C.shoot('_qa', f'samescene_{name}_gray.png', target, direction, dist, lens)


def site():
    C.reset()
    C.theirs(H01, Vector((-9.5, 3.5, 0)))
    ours('CR05_WorkShelter', -2.6, -.5); ours('CR03_StonePile', 1.2, -1.2); ours('CR03_TimberRack', 4.0, -1.0); ours('CR03_MudHeap', 7.0, -1.0)
    ours('CR06_Straight', -1.5, -4.2); ours('CR09_A_RopeGate', -.1, -4.2); ours('CR08_Straight', 1.2, -4.2)
    C.theirs(W / 'B02-V02/B02-V02.glb', Vector((2.7, -4.2, 0))); C.theirs(W / 'B05/B05.glb', Vector((4.1, -4.2, 0)))
    C.theirs(ART / 'exports/qingxi-water-report-c/C07.glb', Vector((5.6, -4.2, 0)))
    C.figure(Vector((-4.2, -4.6, 0)))
    both('site', (-.6, 0, 1.4), (.08, -1, .3), 23.)


def a3():
    C.reset()
    C.theirs(H01, Vector((-13.5, 2, 0)))
    ours('WM01_MillHouse', -3.6, 1); ours('WM02_WaterWheel', 1.1, -1.2, 2.301); ours('WM04_Millstones', 3.6, -3.4)
    ours('WM09_BambooPavilion', 6.6, 1.5); ours('WM05_WashSteps', -4, -6.); ours('WM07_StoneBridge', 13, 0)
    C.theirs(W / 'B02-V02/B02-V02.glb', Vector((1.2, -6.5, 0))); C.theirs(W / 'B05/B05.glb', Vector((2.8, -6.5, 0)))
    C.figure(Vector((-.2, -8., 0)))
    both('a3', (2.5, 0, 2.3), (.08, -1, .28), 39.)


def stalls():
    C.reset()
    C.theirs(RK04 / 'RK04_TeaStall_v001.fbx', Vector((-5.4, 0, 0)), RK04 / 'Textures/RK04_TeaStall_BaseColor.png')
    ours('CR10_CharmStall', -1.3, 0); ours('CR11_NoodleStall', 3.0, 0); ours('CR12_RankingBoard', 7.4, 0)
    C.theirs(MK03 / 'MK03_PriceBoard_v001.fbx', Vector((10.3, 0, 0)), MK03 / 'Textures/MK03_PriceBoard_BaseColor.png')
    C.figure(Vector((.9, -2.6, 0)))
    both('stalls', (2, 0, 1.25), (.05, -1, .22), 21.)


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for key, fn in (('site', site), ('a3', a3), ('stalls', stalls)):
        if not argv or key in argv: fn()
