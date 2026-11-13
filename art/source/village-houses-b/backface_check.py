"""Unity culls back faces and Blender's previews do not, so a flipped surface only shows up in the engine.
Renders the LOD0 meshes with front faces green and back faces red from eight directions and reports the red share.

blender --background --factory-startup <blend> --python art/source/creek-repair-b/backface_check.py -- <ID> <out_dir>
"""
import bpy, math, sys
from pathlib import Path
from mathutils import Vector

aid, out = sys.argv[sys.argv.index('--') + 1:][:2]
out = Path(out).resolve(); out.mkdir(parents=True, exist_ok=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = 1; sc.cycles.use_denoising = False; sc.cycles.max_bounces = 0
sc.render.resolution_x = sc.render.resolution_y = 360; sc.view_settings.view_transform = 'Standard'
sc.render.image_settings.file_format = 'PNG'
sc.world = bpy.data.worlds.new('None'); sc.world.use_nodes = False; sc.world.color = (0, 0, 0)

m = bpy.data.materials.new('Sides'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
geo = nt.nodes.new('ShaderNodeNewGeometry'); mix = nt.nodes.new('ShaderNodeMixRGB'); em = nt.nodes.new('ShaderNodeEmission'); o_ = nt.nodes.new('ShaderNodeOutputMaterial')
mix.inputs[1].default_value = (0, 1, 0, 1); mix.inputs[2].default_value = (1, 0, 0, 1)
nt.links.new(geo.outputs['Backfacing'], mix.inputs[0]); nt.links.new(mix.outputs[0], em.inputs[0]); nt.links.new(em.outputs[0], o_.inputs[0])

meshes = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.split('.')[0].endswith('_LOD0') and '_Leaves_' not in o.name]   # FR03 vine cards are two-sided (culling off) on purpose
for o in bpy.data.objects:
    if o.type == 'MESH' and o not in meshes: o.hide_render = True
for c in bpy.data.collections: c.hide_render = False
for o in meshes:
    o.hide_render = False; o.data.materials.clear(); o.data.materials.append(m)
bpy.context.view_layer.update()
pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
lo = Vector(min(p[i] for p in pts) for i in range(3)); hi = Vector(max(p[i] for p in pts) for i in range(3))
mid = (lo + hi) / 2; R = (hi - lo).length / 2 + .05
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = R * 2; cam.data.clip_end = R * 8

worst = []
for k in range(8):
    a = k / 8 * math.tau; el = .35 if k % 2 == 0 else -.1
    d = Vector((math.cos(a), math.sin(a), el)).normalized()
    cam.location = mid + d * R * 3; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    p = out / f'{aid}_{k}.png'; sc.render.filepath = str(p); bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(str(p)); px = img.pixels[:]
    red = sum(1 for i in range(0, len(px), 4) if px[i] > .5 and px[i + 1] < .5); green = sum(1 for i in range(0, len(px), 4) if px[i + 1] > .5 and px[i] < .5)
    worst.append((round(red / max(1, red + green), 4), k)); bpy.data.images.remove(img)
    if worst[-1][0] < .002: p.unlink()
print('BACKFACE', aid, 'max_red_share', max(worst)[0], 'view', max(worst)[1], flush=True)
