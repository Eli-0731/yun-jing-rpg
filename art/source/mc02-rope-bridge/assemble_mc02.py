"""MC02 assembly preview: each bridge with an existing CliffBoardwalk v001 (art/incoming/dondon, unchanged) at both ends, placed by
its connectors (deck +1.2 m, along Y), so the joints show the two ends at the boardwalk deck height. LOD0, Cycles, material and
clay, with a 1.75 m figure standing on the boardwalk and one on the deck mid span.

    blender -b --factory-startup -P art/source/mc02-rope-bridge/assemble_mc02.py -- [--clay] B24 B12
"""
import bpy, math, sys, json
from pathlib import Path
from mathutils import Vector, Matrix
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; OUT = ROOT / 'art/previews/mc02-rope-bridge'; OUT.mkdir(parents=True, exist_ok=True)
BW = ROOT / 'art/incoming/dondon/CliffBoardwalk/v001'
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
CLAY = '--clay' in args; mids = [a for a in args if not a.startswith('--')]
conn = json.loads((BW / 'model_info.json').read_text(encoding='utf-8'))['connectors']   # entry (x, -3, 1.2), exit (x, +3, 1.2)

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 64; sc.cycles.use_denoising = True
    try:
        pr = bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type = 'OPTIX'; pr.get_devices()
        for d in pr.devices: d.use = True
        sc.cycles.device = 'GPU'
    except Exception: pass
    sc.render.resolution_x, sc.render.resolution_y = 1800, 1000; sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; bg = w.node_tree.nodes['Background']; bg.inputs['Color'].default_value = (.62, .64, .68, 1); bg.inputs['Strength'].default_value = .55
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sun.data.energy = 3.6; sun.data.color = (1, .88, .70); sun.data.angle = .08
    sun.rotation_euler = (math.radians(50), 0, math.radians(-60)); sc.collection.objects.link(sun)
    fill = bpy.data.objects.new('fill', bpy.data.lights.new('fill', 'SUN')); fill.data.energy = .7; fill.data.color = (.70, .76, 1.0); fill.rotation_euler = (math.radians(65), 0, math.radians(150)); sc.collection.objects.link(fill)
    g = bpy.data.meshes.new('ground'); z = -1.2 - 2.5; g.from_pydata([(-60, -60, z), (60, -60, z), (60, 60, z), (-60, 60, z)], [], [(0, 1, 2, 3)])
    go = bpy.data.objects.new('ground', g); m = bpy.data.materials.new('ground'); m.use_nodes = True; m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.46, .45, .42, 1); g.materials.append(m); sc.collection.objects.link(go)
    return sc

def clay_all(objs):
    cm = bpy.data.materials.get('clay') or bpy.data.materials.new('clay'); cm.use_nodes = True; cm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.72, .70, .66, 1)
    for o in objs:
        if o.type == 'MESH': o.data.materials.clear(); o.data.materials.append(cm)

def figure(x, y, z):
    bpy.ops.mesh.primitive_cylinder_add(radius=.18, depth=1.45, location=(x, y, z + .725)); b = bpy.context.object
    bpy.ops.mesh.primitive_uv_sphere_add(radius=.13, location=(x, y, z + 1.62)); h = bpy.context.object
    m = bpy.data.materials.new('fig'); m.use_nodes = True; m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.35, .38, .42, 1)
    for o in (b, h): o.data.materials.append(m)

for mid in mids:
    sc = reset(); L = {'B24': 24.0, 'B12': 12.0}[mid]
    with bpy.data.libraries.load(str(HERE / f'MC02_{mid}.blend')) as (src, dst): dst.objects = [n for n in src.objects if n.endswith('_LOD0')]
    objs = list(dst.objects)
    for o in objs: sc.collection.objects.link(o)
    # boardwalks: exit connector on end A (y = 0), entry connector on end B (y = L); both at the bridge's z = 0
    for name, at in (('A', Vector((0, 0, 0)) - Vector(conn['exit'])), ('B', Vector((0, L, 0)) - Vector(conn['entry']))):
        before = set(bpy.data.objects); bpy.ops.import_scene.fbx(filepath=str(BW / 'CliffBoardwalk_v001.fbx'))
        new = [o for o in bpy.data.objects if o not in before]
        for o in new:
            if o.parent is None: o.location = o.location + at
        objs += [o for o in new if o.type == 'MESH']
    if CLAY: clay_all(objs)
    figure(-.95, -1.6, 0); figure(.3, L / 2, -1.5)   # first figure stands beside the eye-height camera
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    span = L + 12
    for name, loc, at, lens in (('three_quarter', (-span * .55, L / 2 - span * .32, span * .22), (0, L / 2, -.8), 35),
                                ('side', (-span * 1.05, L / 2, -.3), (0, L / 2, -.3), 35),
                                ('joint_A_closeup', (-3.2, -2.4, 1.6), (0, .8, 0), 30),
                                ('deck_eye_1p7m', (0, -3.5, 1.7), (0, L * .6, -.6), 30)):
        cam.location = loc; cam.data.lens = lens; cam.rotation_euler = (Vector(at) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = str(OUT / f'MC02_{mid}_with_boardwalk_{name}{"_clay" if CLAY else ""}.png'); bpy.ops.render.render(write_still=True); print('wrote', sc.render.filepath, flush=True)
