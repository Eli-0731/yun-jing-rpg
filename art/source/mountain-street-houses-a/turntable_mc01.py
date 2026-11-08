"""Turntable review videos for the three MC01 demo buildings in b-street-assembly.json (LOD0, EEVEE, 1280x720, 24 fps, H.264).
Camera rig after the turntable skill of kevinbadi/blender-skills: an empty at the building centre, a tracked camera parented
to it, the empty spins 360 degrees with linear keys so the loop is seamless. Runs headless (no Blender MCP add-on needed).
A 1.75 m figure stands at the front-left corner.

    blender -b --factory-startup -P art/source/mountain-street-houses-a/turntable_mc01.py -- A-shophouse [frames]
    -> art/previews/mountain-street-houses-a/turntable/MC01_<building>_turntable.mp4
"""
import bpy, json, math, sys
from pathlib import Path
from mathutils import Vector, Matrix

a = sys.argv[sys.argv.index('--') + 1:]; NAME = a[0]; FR = int(a[1]) if len(a) > 1 else 144
SRC = Path(__file__).resolve().parent; ROOT = SRC.parents[2]
OUTD = ROOT / 'art/previews/mountain-street-houses-a/turntable'; OUTD.mkdir(parents=True, exist_ok=True); OUT = str(OUTD / f'MC01_{NAME}_turntable.mp4')
asm = json.loads((ROOT / 'art/exports/mountain-street-houses-a/b-street-assembly.json').read_text(encoding='utf-8'))
bd = next(b for b in asm['buildings'] if b['name'] == NAME)

bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'; sc.eevee.taa_render_samples = 32
sc.render.resolution_x, sc.render.resolution_y = 1280, 720; sc.render.fps = 24; sc.frame_start, sc.frame_end = 1, FR
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; bg = w.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (.62, .64, .68, 1); bg.inputs['Strength'].default_value = .6
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sun.data.energy = 3.4; sun.data.color = (1, .88, .70); sun.data.angle = .1
sun.rotation_euler = (math.radians(52), 0, math.radians(-38)); sc.collection.objects.link(sun)
fill = bpy.data.objects.new('fill', bpy.data.lights.new('fill', 'SUN')); fill.data.energy = .8; fill.data.color = (.70, .76, 1.0)
fill.rotation_euler = (math.radians(65), 0, math.radians(150)); sc.collection.objects.link(fill)
g = bpy.data.meshes.new('ground'); g.from_pydata([(-60, -60, 0), (60, -60, 0), (60, 60, 0), (-60, 60, 0)], [], [(0, 1, 2, 3)])
go = bpy.data.objects.new('ground', g); m = bpy.data.materials.new('ground'); m.use_nodes = True
m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.46, .45, .42, 1); g.materials.append(m); sc.collection.objects.link(go)

cache = {}; objs = []
for p in bd['parts']:
    if p['id'] not in cache:
        with bpy.data.libraries.load(str(SRC / f"MC01_{p['id']}.blend")) as (src, dst): dst.objects = [n for n in src.objects if n.endswith('_LOD0')]
        cache[p['id']] = list(dst.objects)
    for s in cache[p['id']]:
        o = s.copy(); sc.collection.objects.link(o)
        o.matrix_world = Matrix.Translation(Vector(p['pos'])) @ Matrix.Rotation(math.radians(p['rotZ']), 4, 'Z'); objs.append(o)
mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
for o in objs:
    for c in o.bound_box: v = o.matrix_world @ Vector(c); mn = Vector(map(min, mn, v)); mx = Vector(map(max, mx, v))
ctr = (mn + mx) / 2; size = (mx - mn).length
bpy.ops.mesh.primitive_cylinder_add(radius=.18, depth=1.45, location=(mn.x - .6, mn.y - 1.0, .725)); fig = bpy.context.object
bpy.ops.mesh.primitive_uv_sphere_add(radius=.13, location=(mn.x - .6, mn.y - 1.0, 1.62)); head = bpy.context.object
fm = bpy.data.materials.new('fig'); fm.use_nodes = True; fm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.35, .38, .42, 1)
for o in (fig, head): o.data.materials.append(fm)

target = bpy.data.objects.new('TurntableTarget', None); sc.collection.objects.link(target); target.location = ctr
cam = bpy.data.objects.new('TurntableCamera', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 24; cam.parent = target; cam.location = Vector((0, -size * 1.75, size * .42))
tr = cam.constraints.new('TRACK_TO'); tr.target = target; tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'
target.rotation_euler = (0, 0, 0); target.keyframe_insert('rotation_euler', index=2, frame=1)
target.rotation_euler = (0, 0, math.tau); target.keyframe_insert('rotation_euler', index=2, frame=FR + 1)
for fc in target.animation_data.action.layers[0].strips[0].channelbag(target.animation_data.action.slots[0]).fcurves if hasattr(target.animation_data.action, 'layers') else target.animation_data.action.fcurves:
    for k in fc.keyframe_points: k.interpolation = 'LINEAR'
sc.render.image_settings.media_type = 'VIDEO'; sc.render.image_settings.file_format = 'FFMPEG'; sc.render.ffmpeg.format = 'MPEG4'; sc.render.ffmpeg.codec = 'H264'
sc.render.ffmpeg.constant_rate_factor = 'HIGH'; sc.render.filepath = OUT
bpy.ops.render.render(animation=True); print('wrote', OUT, flush=True)
