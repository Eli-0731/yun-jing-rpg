"""Preview renders for MC01 modules: appends the *_LOD0 objects (or LODn / clay) from MC01_<ID>.blend and renders
front / side / back / three-quarter views with a 1.75 m figure, or a stacked assembly.

    blender -b --factory-startup -P render_mc01.py -- --out <dir> [--lod 0] [--clay] [--samples 48] [--wire] SB01 SF01 ...
    blender -b --factory-startup -P render_mc01.py -- --out <dir> --stack SB01,SF01,RF01 [--name shop]
"""
import bpy, math, sys
from pathlib import Path
from mathutils import Vector

HERE = Path(__file__).resolve().parent
args = sys.argv[sys.argv.index('--') + 1:]
def opt(k, d=None):
    if k in args: i = args.index(k); v = args[i + 1]; del args[i:i + 2]; return v
    return d
def flag(k):
    if k in args: args.remove(k); return True
    return False
OUT = Path(opt('--out')); LOD = int(opt('--lod', '0')); SAMPLES = int(opt('--samples', '48')); STACK = opt('--stack'); NAME = opt('--name', 'stack')
CLAY = flag('--clay'); WIRE = flag('--wire'); NODETAIL = flag('--nodetail'); HEIGHTS = {'SB': 2.0, 'SF': 3.0, 'HM': 3.0}
OUT.mkdir(parents=True, exist_ok=True)

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True
    try:
        pr = bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type = 'OPTIX'; pr.get_devices()
        for d in pr.devices: d.use = True
        sc.cycles.device = 'GPU'
    except Exception: pass
    sc.render.resolution_x, sc.render.resolution_y = 1600, 1200; sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (.62, .64, .68, 1); bg.inputs['Strength'].default_value = .55
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sun.data.energy = 3.6; sun.data.color = (1, .88, .70); sun.data.angle = .08
    sun.rotation_euler = (math.radians(58), 0, math.radians(-38)); sc.collection.objects.link(sun)
    fill = bpy.data.objects.new('fill', bpy.data.lights.new('fill', 'SUN')); fill.data.energy = .7; fill.data.color = (.70, .76, 1.0)
    fill.rotation_euler = (math.radians(65), 0, math.radians(150)); sc.collection.objects.link(fill)
    g = bpy.data.meshes.new('ground'); g.from_pydata([(-40, -40, 0), (40, -40, 0), (40, 40, 0), (-40, 40, 0)], [], [(0, 1, 2, 3)])
    go = bpy.data.objects.new('ground', g); m = bpy.data.materials.new('ground'); m.use_nodes = True
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.46, .45, .42, 1); g.materials.append(m); sc.collection.objects.link(go)

def append(mid, offset=(0, 0, 0)):
    path = HERE / f'MC01_{mid}.blend'; suf = f'_LOD{LOD}'
    with bpy.data.libraries.load(str(path)) as (src, dst): dst.objects = [n for n in src.objects if n.endswith(suf) and not (NODETAIL and n.startswith('Detail_'))]
    objs = []
    for o in dst.objects:
        bpy.context.scene.collection.objects.link(o); o.location = Vector(offset); objs.append(o)
    if CLAY:
        cm = bpy.data.materials.get('clay') or bpy.data.materials.new('clay'); cm.use_nodes = True
        cm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.72, .70, .66, 1); cm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .8
        for o in objs: o.data.materials.clear(); o.data.materials.append(cm)
    if WIRE:
        cm = bpy.data.materials.get('clay') or bpy.data.materials.new('clay'); cm.use_nodes = True
        cm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.78, .76, .72, 1)
        wm = bpy.data.materials.new('wire'); wm.use_nodes = True; wm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.05, .06, .08, 1)
        for o in objs:
            o.data.materials.clear(); o.data.materials.append(cm); o.data.materials.append(wm)
            m = o.modifiers.new('w', 'WIREFRAME'); m.thickness = .006; m.use_replace = False; m.material_offset = 1
    return objs

def figure(x, y):
    """1.75 m scale figure: grey capsule body + head"""
    bpy.ops.mesh.primitive_cylinder_add(radius=.18, depth=1.45, location=(x, y, .725)); b = bpy.context.object
    bpy.ops.mesh.primitive_uv_sphere_add(radius=.13, location=(x, y, 1.62)); h = bpy.context.object
    m = bpy.data.materials.new('fig'); m.use_nodes = True; m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.35, .38, .42, 1)
    for o in (b, h): o.data.materials.append(m)

def bounds(objs):
    mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
    for o in objs:
        for c in o.bound_box: w = o.matrix_world @ Vector(c); mn = Vector(map(min, mn, w)); mx = Vector(map(max, mx, w))
    return mn, mx

def shoot(objs, name, views):
    sc = bpy.context.scene; mn, mx = bounds(objs); ctr = (mn + mx) / 2; size = max(mx - mn)
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    for v in views:
        if v == 'three_quarter':
            cam.data.type = 'PERSP'; cam.data.lens = 40; d = size * 2.1
            cam.location = ctr + Vector((-.62, -.78, .42)).normalized() * d
        else:
            cam.data.type = 'ORTHO'; cam.data.ortho_scale = size * 1.25
            dirv = {'front': Vector((0, -1, .0)), 'side': Vector((1, 0, 0)), 'back': Vector((0, 1, 0)), 'top': Vector((0, -.001, 1))}[v]
            cam.location = ctr + dirv * size * 3
        cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = str(OUT / f'{name}_{v}.png'); bpy.ops.render.render(write_still=True); print('wrote', sc.render.filepath, flush=True)

if STACK:
    reset(); objs = []; z = 0
    for mid in STACK.split(','):
        objs += append(mid, (0, 0, z)); z += HEIGHTS.get(mid[:2], 0)
    figure(1.3, -3.2); shoot(objs, NAME, ['three_quarter', 'front', 'side'])
else:
    for mid in args:
        reset(); objs = append(mid); figure(mid and (bounds(objs)[1].x + .5), -1.0)
        tag = f'MC01_{mid}' + ('_clay' if CLAY else '') + ('_wire' if WIRE else '') + ('_nodetail' if NODETAIL else '') + (f'_LOD{LOD}' if LOD else '')
        shoot(objs, tag, ['three_quarter', 'front', 'side', 'back'] if not (CLAY or WIRE or NODETAIL or LOD) else ['three_quarter'])
