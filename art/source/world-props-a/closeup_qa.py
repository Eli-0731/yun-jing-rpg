"""Close-up evidence for asset-QA findings on an exported world prop (Johnnnny0823, 11/05 review round).
Imports the exported FBX (LOD0 only), puts a neutral ground plane at z = 0 and renders one close-up per point of interest: shaded
(left) and wireframe of the same view (right), so a reviewer can see whether a loose piece rests on the ground or on another
part, and what the topology at a flagged spot looks like.
blender -b --factory-startup -P closeup_qa.py -- --fbx <ID>.fbx --out <png> --pts "x,y,z,label[,azimuth_deg];..." [--dist 0.45] [--samples 48] [--hide Roof,Shakes]
Points are in the exported frame (Blender Z up, metres), as printed by the QA scripts.
"""
import bpy, math, sys, argparse
from mathutils import Vector
a = argparse.ArgumentParser()
a.add_argument('--fbx'); a.add_argument('--out'); a.add_argument('--pts'); a.add_argument('--dist', type=float, default=.45)
a.add_argument('--samples', type=int, default=48); a.add_argument('--res', default='640x480')
a.add_argument('--hide', default='', help='comma-separated name fragments left out of the render (a roof that shades the spot)')
args = a.parse_args(sys.argv[sys.argv.index('--') + 1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = args.samples; sc.cycles.use_denoising = True
try:
    pr = bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type = 'OPTIX'; pr.get_devices()
    for d in pr.devices: d.use = d.type == 'OPTIX'
    sc.cycles.device = 'GPU'
except Exception: sc.cycles.device = 'CPU'
w, h = map(int, args.res.split('x')); sc.render.resolution_x = w; sc.render.resolution_y = h; sc.view_settings.view_transform = 'AgX'
bpy.ops.import_scene.fbx(filepath=args.fbx)
for o in sc.objects:
    if o.type == 'MESH' and (not o.name.endswith('_LOD0') or 'Collision' in o.name or any(s and s in o.name for s in args.hide.split(','))):
        o.hide_render = True
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0)); g = bpy.context.object
gm = bpy.data.materials.new('ground'); gm.use_nodes = True; gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.36, .34, .30, 1)
g.data.materials.append(gm)
world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True; world.node_tree.nodes['Background'].inputs['Strength'].default_value = .35
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 3.2
sun.rotation_euler = (math.radians(50), 0, math.radians(35))
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 50
fill = bpy.data.objects.new('fill', bpy.data.lights.new('fill', 'POINT')); sc.collection.objects.link(fill); fill.parent = cam
fill.data.energy = 60 * args.dist ** 2; fill.data.shadow_soft_size = .1   # camera fill, so spots under eaves or in a crevice still read
pts = [p.split(',') for p in args.pts.split(';') if p]
import tempfile, os
tmp = tempfile.mkdtemp(); shots = []
for i, p in enumerate(pts):
    tgt = Vector(tuple(float(x) for x in p[:3])); label = p[3] if len(p) > 3 else str(i)
    az = math.radians(float(p[4])) if len(p) > 4 else math.atan2(-.75, .55)   # optional 5th field: view azimuth in degrees
    eye = tgt + Vector((math.cos(az) * .93, math.sin(az) * .93, .45)).normalized() * args.dist
    cam.location = eye; cam.rotation_euler = (tgt - eye).to_track_quat('-Z', 'Y').to_euler()
    for wire in (False, True):
        for o in sc.objects:
            if o.type == 'MESH' and not o.hide_render:
                m = next((md for md in o.modifiers if md.type == 'WIREFRAME'), None)
                if wire and o is not g and not m: m = o.modifiers.new('wf', 'WIREFRAME'); m.thickness = .0006; m.use_replace = False
                if m: m.show_render = wire
        f = os.path.join(tmp, f'{i}_{int(wire)}.png'); sc.render.filepath = f; bpy.ops.render.render(write_still=True); shots.append((label, f))
# contact sheet: one row per point, shaded | wireframe, label strip on top
import numpy as np
rows = []
for i in range(len(pts)):
    ims = []
    for wire in (0, 1):
        im = bpy.data.images.load(os.path.join(tmp, f'{i}_{wire}.png')); a_ = np.array(im.pixels[:]).reshape(h, w, 4)[::-1, :, :3]; ims.append(a_)
    rows.append(np.concatenate(ims, 1))
sheet = np.concatenate(rows, 0)
H, W = sheet.shape[:2]; out = bpy.data.images.new('sheet', W, H)
out.pixels.foreach_set(np.dstack([sheet[::-1], np.ones((H, W))]).astype(np.float32).ravel()); out.filepath_raw = args.out; out.file_format = 'PNG'; out.save()
print('CLOSEUP', args.out, [p[3] if len(p) > 3 else '' for p in pts])
