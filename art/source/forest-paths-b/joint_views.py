"""Two copies of a path piece end to end, the second one's Socket_Path_W on the first one's Socket_Path_E: close views of the joint
at every LOD (baked materials), and LOD0 next to LOD2 across the joint. Reads the saved asset .blend, writes previews only.

blender --background --factory-startup art/source/forest-paths-b/blend/<ID>_<ver>.blend --python joint_views.py -- <ID> <repo>/art
Writes art/previews/forest-paths-b/<ID>/joint_<name>.png
"""
import bpy, math, sys
from pathlib import Path
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index('--') + 1:]
AID, ART = argv[0], Path(argv[1])
KIT = 'forest-paths-b'
OUT = ART / 'previews' / KIT / AID
for img in bpy.data.images:
    if img.source == 'FILE' and img.filepath:
        p = ART / 'exports' / KIT / AID / 'Textures' / Path(bpy.path.abspath(img.filepath)).name
        if p.exists(): img.filepath = str(p); img.reload()
root = bpy.data.objects[AID]
sw, se = bpy.data.objects['Socket_Path_W'].matrix_world, bpy.data.objects['Socket_Path_E'].matrix_world
M = se @ Matrix.Rotation(math.pi, 4, 'Z') @ sw.inverted()
meshes = {o.name: o for o in root.children if o.type == 'MESH' and '_Collision' not in o.name}
scene = bpy.context.scene
for o in scene.objects: o.hide_render = True
coll = bpy.data.collections.new('joint_copies'); scene.collection.children.link(coll)
copies = {}
for n, o in meshes.items():
    c = o.copy(); c.data = o.data; c.matrix_world = M @ o.matrix_world; coll.objects.link(c); copies[n] = c
scene.render.engine = 'CYCLES'; scene.cycles.samples = 64; scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = 1400, 900
scene.view_settings.view_transform = 'AgX'
world = scene.world or bpy.data.worlds.new('w'); scene.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.32, .34, .38, 1); world.node_tree.nodes['Background'].inputs[1].default_value = 1.4
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); scene.collection.objects.link(sun)
sun.data.energy = 4.5; sun.rotation_euler = (math.radians(50), 0, math.radians(35))
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); scene.collection.objects.link(cam); scene.camera = cam
J = se.translation
FWD = (se.to_3x3() @ Vector((0, 1, 0))).normalized(); LFT = Vector((0, 0, 1)).cross(FWD).normalized()   # along the path at the joint
rel = lambda v: FWD * v[0] + LFT * v[1] + Vector((0, 0, v[2]))


def shot(name, show_a, show_b, eye, target, lens=40):
    for o in list(meshes.values()) + list(copies.values()): o.hide_render = True
    for n in show_a: meshes[n].hide_render = False
    for n in show_b: copies[n].hide_render = False
    cam.data.lens = lens; cam.location = J + rel(eye)
    cam.rotation_euler = ((J + rel(target)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(OUT / f'joint_{name}.png'); bpy.ops.render.render(write_still=True)
    print('JOINT_VIEW', name, flush=True)


def lod(lv): return [n for n in meshes if n.endswith(f'_LOD{lv}')]


for lv in (0, 1, 2):        # standing on the path 1.6 m up, looking along it across the joint
    shot(f'lod{lv}_eye', lod(lv), lod(lv), (-1.9, -.35, 1.6), (.6, 0, 0))
shot('lod0_top', lod(0), lod(0), (0, -.02, 1.5), (0, 0, 0), lens=30)
shot('lod0_next_to_lod2', lod(0), lod(2), (-1.4, -1.2, 1.2), (.3, 0, .05))
