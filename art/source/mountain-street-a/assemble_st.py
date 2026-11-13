"""Render the ST 20 m street sample from art/exports/mountain-street-a/st-street-assembly.json (LOD0, Cycles): MC01 street
houses with ST01-ST06, a cliff edge beyond the railing, 1.75 m figures. Views: overview, street at 1.7 m eye height, the
railing side (lantern post, bench, railing), the stair with the cascade, the shop fronts with banners and the lantern string.
--clay for the grey model.

    blender -b --factory-startup -P art/source/mountain-street-a/assemble_st.py -- [--clay] [--samples 64]
"""
import bpy, json, math, sys
from pathlib import Path
from mathutils import Vector, Matrix

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; PKG = 'mountain-street-a'
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
CLAY = '--clay' in args; SAMPLES = int(args[args.index('--samples') + 1]) if '--samples' in args else 64
OUT = ROOT / 'art/previews' / PKG / 'assembly'; OUT.mkdir(parents=True, exist_ok=True)
asm = json.loads((ROOT / 'art/exports' / PKG / 'st-street-assembly.json').read_text(encoding='utf-8'))

bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True
try:
    pr = bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type = 'OPTIX'; pr.get_devices()
    for d in pr.devices: d.use = True
    sc.cycles.device = 'GPU'
except Exception: pass
sc.render.resolution_x, sc.render.resolution_y = 1600, 1000; sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; bg = w.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (.66, .69, .74, 1); bg.inputs['Strength'].default_value = .6
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sun.data.energy = 3.4; sun.data.color = (1, .88, .70); sun.data.angle = .08
sun.rotation_euler = (math.radians(50), 0, math.radians(-30)); sc.collection.objects.link(sun)
fill = bpy.data.objects.new('fill', bpy.data.lights.new('fill', 'SUN')); fill.data.energy = .7; fill.data.color = (.70, .76, 1.0)
fill.rotation_euler = (math.radians(65), 0, math.radians(150)); sc.collection.objects.link(fill)
def mat(nm, col, rough=.9):
    m = bpy.data.materials.new(nm); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough; return m
def slab(nm, verts, m):
    me = bpy.data.meshes.new(nm); me.from_pydata(verts, [], [(0, 1, 2, 3)]); o = bpy.data.objects.new(nm, me); me.materials.append(m); sc.collection.objects.link(o); return o
ye = asm['street']['cliff_edge_y']
slab('street', [(-40, ye, 0), (40, ye, 0), (40, 40, 0), (-40, 40, 0)], mat('street', (.46, .45, .42)))
slab('cliff', [(-40, ye, 0), (40, ye, 0), (40, ye, -30), (-40, ye, -30)], mat('cliff', (.40, .40, .38)))
slab('valley', [(-80, ye - 80, -30), (80, ye - 80, -30), (80, ye, -30), (-80, ye, -30)], mat('valley', (.55, .62, .60)))
clay = mat('clay', (.72, .70, .66), .8)

cache = {}
def module(pid):
    if pid not in cache:
        pre = pid.split('-')[0]; mid = (pid[5:] if pre == 'MC01' else pid).replace('-', '_')
        path = ROOT / 'art/source' / ('mountain-street-houses-a' if pre == 'MC01' else PKG) / (f'MC01_{mid}.blend' if pre == 'MC01' else f'ST_{mid}.blend')
        with bpy.data.libraries.load(str(path)) as (src, dst): dst.objects = [n for n in src.objects if n.endswith('_LOD0')]
        cache[pid] = list(dst.objects)
        if CLAY:
            for o in cache[pid]: o.data.materials.clear(); o.data.materials.append(clay)
    return cache[pid]

def figure(p):
    bpy.ops.mesh.primitive_cylinder_add(radius=.18, depth=1.45, location=(p[0], p[1], p[2] + .725)); b = bpy.context.object
    bpy.ops.mesh.primitive_uv_sphere_add(radius=.13, location=(p[0], p[1], p[2] + 1.62)); h = bpy.context.object
    fm = bpy.data.materials.get('fig') or mat('fig', (.35, .38, .42))
    for o in (b, h): o.data.materials.append(fm)

for p in asm['parts']:
    for src in module(p['id']):
        o = src.copy(); sc.collection.objects.link(o)
        o.matrix_world = Matrix.Translation(Vector(p['pos'])) @ Matrix.Rotation(math.radians(p['rotZ']), 4, 'Z')
for objs in cache.values():
    for o in objs:
        if o.name in sc.collection.objects: sc.collection.objects.unlink(o)
for f in ((-6.2, -2.6, 0), (1.0, -3.4, 0), (-2.2, -4.7, 0), (7.2, 1.3, .9), (3.2, -1.2, 0)): figure(f)

cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
def shot(name, loc, look, lens=35):
    cam.data.lens = lens; cam.location = Vector(loc); cam.rotation_euler = (Vector(look) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = str(OUT / f'{name}{"_clay" if CLAY else ""}.png'); bpy.ops.render.render(write_still=True); print('wrote', sc.render.filepath, flush=True)

shot('st_street_overview', (-14.0, -22.0, 13.0), (0.5, 0.0, 2.2), 30)
shot('st_street_eye_1p7m', (-11.5, -3.6, 1.7), (2.0, -1.0, 2.6), 24)
shot('st_railing_side', (-6.5, -1.2, 1.9), (-2.5, -5.2, .7), 30)
shot('st_stair_cascade', (13.8, -4.6, 2.6), (9.4, 1.6, 1.3), 30)
shot('st_shopfronts', (-5.0, -7.2, 3.6), (-4.6, 0.0, 4.4), 28)
