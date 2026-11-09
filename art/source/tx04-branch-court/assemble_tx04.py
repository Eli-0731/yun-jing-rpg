"""TX04 assemblies (LOD0, Cycles), material and clay, with a 1.75 m figure.
default: the sample (gate with two straight wall segments each side). --academy: the whole branch academy on the 4 m grid -
gate in the front wall, corner walls, side walls, a rear doorway between two WALL_DO, the main hall at the back, the two side
wings facing the courtyard and six paving bays (STEPS is a terrace piece and is shown on its own).

    blender -b --factory-startup -P art/source/tx04-branch-court/assemble_tx04.py -- [--academy] [--clay]
"""
import bpy, math, sys
from pathlib import Path
from mathutils import Vector, Matrix
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; OUT = ROOT / 'art/previews/tx04-branch-court'; OUT.mkdir(parents=True, exist_ok=True)
SAMPLE = [('GATE', (0, 0, 0), 0), ('WALL_ST', (-4.15, .04, 0), 0), ('WALL_ST', (-8.15, .04, 0), 0), ('WALL_ST', (4.15, .04, 0), 180), ('WALL_ST', (8.15, .04, 0), 180)]
CLAY = '--clay' in sys.argv; ACAD = '--academy' in sys.argv
if ACAD:   # the layout lives in the export folder so Unity places the same thing
    import json
    PARTS = [(p['id'], tuple(p['pos']), p['rotZ']) for p in json.loads((ROOT / 'art/exports/tx04-branch-court/tx04-academy-assembly.json').read_text(encoding='utf-8'))['parts']]
if not ACAD: PARTS = SAMPLE
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
sun.rotation_euler = (math.radians(52), 0, math.radians(-38)); sc.collection.objects.link(sun)
fill = bpy.data.objects.new('fill', bpy.data.lights.new('fill', 'SUN')); fill.data.energy = .7; fill.data.color = (.70, .76, 1.0); fill.rotation_euler = (math.radians(65), 0, math.radians(150)); sc.collection.objects.link(fill)
g = bpy.data.meshes.new('ground'); g.from_pydata([(-60, -60, 0), (60, -60, 0), (60, 60, 0), (-60, 60, 0)], [], [(0, 1, 2, 3)])
go = bpy.data.objects.new('ground', g); m = bpy.data.materials.new('ground'); m.use_nodes = True; m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.46, .45, .42, 1); g.materials.append(m); sc.collection.objects.link(go)
clay = bpy.data.materials.new('clay'); clay.use_nodes = True; clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.72, .70, .66, 1)
cache = {}; objs = []
for mid, pos, rz in PARTS:
    if mid not in cache:
        with bpy.data.libraries.load(str(HERE / f'TX04_{mid}.blend')) as (src, dst): dst.objects = [n for n in src.objects if n.endswith('_LOD0')]
        cache[mid] = list(dst.objects)
        if CLAY:
            for o in cache[mid]: o.data.materials.clear(); o.data.materials.append(clay)
    for s in cache[mid]:
        o = s.copy(); sc.collection.objects.link(o); o.matrix_world = Matrix.Translation(Vector(pos)) @ Matrix.Rotation(math.radians(rz), 4, 'Z'); objs.append(o)
fx, fy = (1.6, -6.0) if ACAD else (-1.6, -2.6)
bpy.ops.mesh.primitive_cylinder_add(radius=.18, depth=1.45, location=(fx, fy, .725)); b = bpy.context.object
bpy.ops.mesh.primitive_uv_sphere_add(radius=.13, location=(fx, fy, 1.62)); h = bpy.context.object
fm = bpy.data.materials.new('fig'); fm.use_nodes = True; fm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.35, .38, .42, 1)
for o in (b, h): o.data.materials.append(fm)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
VIEWS = ((('aerial', (-24, -30, 21), (0, -1, 1.5), 35), ('front', (0, -40, 5.5), (0, 0, 4.0), 35), ('courtyard_eye_1p7m', (-1.2, -7.6, 1.7), (0, 4.5, 3.6), 24))
         if ACAD else (('three_quarter', (-9.5, -13.5, 6.0), (0, 0, 2.4), 35), ('front', (0, -17, 2.6), (0, 0, 2.6), 35), ('eye_1p7m', (-2.5, -9.0, 1.7), (0, 0, 3.0), 28)))
STEM = 'TX04_academy_' if ACAD else 'TX04_sample_gate_walls_'
for name, loc, at, lens in VIEWS:
    cam.location = loc; cam.data.lens = lens; cam.rotation_euler = (Vector(at) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = str(OUT / f'{STEM}{name}{"_clay" if CLAY else ""}.png'); bpy.ops.render.render(write_still=True); print('wrote', sc.render.filepath, flush=True)
