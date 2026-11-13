"""Render the three MC01 demo buildings from art/exports/mountain-street-houses-a/b-street-assembly.json (LOD0, Cycles),
one three-quarter and one front view per building plus a street overview, with 1.75 m figures; --clay for the grey model.

    blender -b --factory-startup -P assemble_mc01.py -- [--clay] [--samples 64]
"""
import bpy, json, math, sys
from pathlib import Path
from mathutils import Vector, Matrix

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; PKG = 'mountain-street-houses-a'
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
CLAY = '--clay' in args; SAMPLES = int(args[args.index('--samples') + 1]) if '--samples' in args else 64
OUT = ROOT / 'art/previews' / PKG / 'assembly'; OUT.mkdir(parents=True, exist_ok=True)
asm = json.loads((ROOT / 'art/exports' / PKG / 'b-street-assembly.json').read_text(encoding='utf-8'))

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
sun.rotation_euler = (math.radians(52), 0, math.radians(-38)); sc.collection.objects.link(sun)
fill = bpy.data.objects.new('fill', bpy.data.lights.new('fill', 'SUN')); fill.data.energy = .7; fill.data.color = (.70, .76, 1.0)
fill.rotation_euler = (math.radians(65), 0, math.radians(150)); sc.collection.objects.link(fill)
g = bpy.data.meshes.new('ground'); g.from_pydata([(-60, -60, 0), (60, -60, 0), (60, 60, 0), (-60, 60, 0)], [], [(0, 1, 2, 3)])
go = bpy.data.objects.new('ground', g); m = bpy.data.materials.new('ground'); m.use_nodes = True
m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.46, .45, .42, 1); g.materials.append(m); sc.collection.objects.link(go)
clay = bpy.data.materials.new('clay'); clay.use_nodes = True
clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.72, .70, .66, 1); clay.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .8

cache = {}
def module(mid):
    if mid not in cache:
        with bpy.data.libraries.load(str(HERE / f'MC01_{mid}.blend')) as (src, dst): dst.objects = [n for n in src.objects if n.endswith('_LOD0')]
        cache[mid] = list(dst.objects)
        if CLAY:
            for o in cache[mid]: o.data.materials.clear(); o.data.materials.append(clay)
    return cache[mid]

def figure(p):
    bpy.ops.mesh.primitive_cylinder_add(radius=.18, depth=1.45, location=(p[0], p[1], p[2] + .725)); b = bpy.context.object
    bpy.ops.mesh.primitive_uv_sphere_add(radius=.13, location=(p[0], p[1], p[2] + 1.62)); h = bpy.context.object
    fm = bpy.data.materials.get('fig') or bpy.data.materials.new('fig'); fm.use_nodes = True; fm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.35, .38, .42, 1)
    for o in (b, h): o.data.materials.append(fm)

groups = {}
for bd in asm['buildings']:
    objs = []
    for p in bd['parts']:
        for src in module(p['id']):
            o = src.copy(); sc.collection.objects.link(o)   # linked duplicate: shares the mesh
            o.matrix_world = Matrix.Translation(Vector(p['pos'])) @ Matrix.Rotation(math.radians(p['rotZ']), 4, 'Z'); objs.append(o)
    groups[bd['name']] = objs
for o in [o for objs in cache.values() for o in objs]:
    if o.name in sc.collection.objects: sc.collection.objects.unlink(o)
figure((-6.3, -6.0, 0)); figure((-8.4, -1.2, 2.0)); figure((2.6, -2.4, 2.0)); figure((10.4, -3.3, 0))

def bounds(objs):
    mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
    for o in objs:
        for c in o.bound_box: wv = o.matrix_world @ Vector(c); mn = Vector(map(min, mn, wv)); mx = Vector(map(max, mx, wv))
    return mn, mx

cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
def shoot(name, objs, dirv, lens=40, k=1.9):
    mn, mx = bounds(objs); ctr = (mn + mx) / 2; size = max(mx - mn)
    cam.data.lens = lens; cam.location = ctr + Vector(dirv).normalized() * size * k
    cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = str(OUT / f'{name}{"_clay" if CLAY else ""}.png'); bpy.ops.render.render(write_still=True); print('wrote', sc.render.filepath, flush=True)

for name, objs in groups.items():
    shoot(f'{name}_three_quarter', objs, (-.62, -.78, .38))
    shoot(f'{name}_front', objs, (0, -1, .12))
allo = [o for objs in groups.values() for o in objs]
shoot('street_overview', allo, (-.45, -.85, .45), lens=35, k=1.15)
cam.data.lens = 24; cam.location = Vector((-4.0, -12.0, 1.7)); cam.rotation_euler = (Vector((1.5, 0, 4.2)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.filepath = str(OUT / f'street_eye_1p7m{"_clay" if CLAY else ""}.png'); bpy.ops.render.render(write_still=True); print('wrote', sc.render.filepath, flush=True)
