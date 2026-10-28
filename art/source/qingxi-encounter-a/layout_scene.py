"""Scene layout renders for the A kit (run after build_encounter.py and its --master step):

  blender -b art/source/qingxi-encounter-a/Qingxi_Encounter_A.blend --python-exit-code 1 --python art/source/qingxi-encounter-a/layout_scene.py

Places the baked game meshes as tools/qingxi-encounter-a/app.mjs does (three.js (x, y, z) -> Blender (x, -z, y)),
adds a 1.7 m figure and renders: overview, plan, eye height from the trail, and the terrain tile seams.
"""
import math
from pathlib import Path

import bpy
import bmesh
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parents[2] / 'art/previews/qingxi-encounter-a/layout'
OUT.mkdir(parents=True, exist_ok=True)
LAYOUT = [  # (key, three x, three y, three z, three rot.y) -- mirrors LAYOUT in app.mjs
    ('A02_HollowTile', 0, -0.6, 0, math.pi), ('A01_SlopeTile', -2, -0.6, 5, math.pi), ('A01_SlopeTile', 2, -0.6, 5, math.pi),
    ('A01_SlopeTile', 5, -0.6, 1, math.pi / 2), ('A04_MossBoulderCover', -2.6, 0, -3.2, 0.3), ('A05_LayeredRockCover', 3.4, 0, -1.2, -1.2),
    ('A03_FallenLog', 3.6, 0, -5.2, -0.45), ('A06_RootStump', -3.0, 0, -6.4, 0.6),
    ('A07_RabbitTrailTile', 0, -0.15, -5.0, 0), ('A08_BrokenBambooFence', -2.4, 0, -8.6, 0), ('A08_BrokenBambooFence', 2.4, 0, -8.6, math.pi),
    ('A11_WarningClothRack', 1.75, 0, -8.15, math.pi), ('A10_WatchPlatform', -6.2, 0, -7.5, math.pi / 2), ('A09_StoneShelter', 0, 0, -11, 0),
    ('A12_VineDummy', 3.4, 0, -10.6, -math.pi / 2),
]
sc = bpy.data.scenes.new('Layout')
for key, x, y, z, rot in LAYOUT:
    e = bpy.data.objects.new(f'place_{key}', None)
    e.instance_type = 'COLLECTION'
    e.instance_collection = bpy.data.collections[f'{key}__game']
    e.location = (x, -z, y)
    e.rotation_euler = (0, 0, rot)
    sc.collection.objects.link(e)


def mat(name, rgb, rough=0.95):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1)
    b.inputs['Roughness'].default_value = rough
    return m


def plane(name, verts, m, z=0.0):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(x, y, z) for x, y in verts], [], [tuple(range(len(verts)))])
    me.materials.append(m)
    o = bpy.data.objects.new(name, me)
    sc.collection.objects.link(o)
    return o


plane('meadow', [(-40, -40), (40, -40), (40, 40), (-40, 40)], mat('Meadow', (0.045, 0.06, 0.02)), -0.002)
plane('trail', [(-0.6, 3.0), (0.6, 3.0), (0.9, 14), (-0.3, 14)], mat('Trail', (0.10, 0.07, 0.042)), 0.003)
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.24, radius2=0.2, depth=1.45)
bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, 0.725))
bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=0.13, matrix=Matrix.Translation((0, 0, 1.57)))
me = bpy.data.meshes.new('Figure')
bm.to_mesh(me)
me.materials.append(mat('Figure', (0.20, 0.30, 0.26), 0.7))
fig = bpy.data.objects.new('Figure_1p7m', me)
fig.location = (0.4, 6.4, 0)
sc.collection.objects.link(fig)

w = bpy.data.worlds.new('Sky')
sc.world = w
sky = w.node_tree.nodes.new('ShaderNodeTexSky')
for a, v in (('sun_elevation', math.radians(35)), ('sun_rotation', math.radians(140))):
    if hasattr(sky, a):
        setattr(sky, a, v)
w.node_tree.links.new(sky.outputs['Color'], w.node_tree.nodes['Background'].inputs['Color'])
w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.35
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN'))
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(55), 0, math.radians(140))
sc.collection.objects.link(sun)
sc.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences
for kind in ('OPTIX', 'CUDA'):
    try:
        prefs.compute_device_type = kind
        prefs.get_devices()
        if any(d.type == kind for d in prefs.devices):
            break
    except TypeError:
        continue
for d in prefs.devices:
    d.use = d.type != 'CPU'
sc.cycles.device = 'GPU'
sc.cycles.samples = 96
sc.cycles.use_denoising = True
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Base Contrast'
sc.render.resolution_x, sc.render.resolution_y = 1600, 900

SHOTS = {
    'overview': ((-12, 18, 10), (0.0, 4.0, 0.3), 26, None),
    'safe_side': ((5.5, 15.5, 3.2), (-0.5, 9.0, 1.0), 26, None),
    'plan_top': ((-0.5, 4.5, 30), (-0.5, 4.5, 0), None, 28),
    'eye_height_trail': ((0.3, 8.5, 1.7), (0, -0.5, 0.6), 24, None),
    'tile_seams': ((-5.5, -1.0, 3.2), (0, -4.5, 0.2), 32, None),
}
for name, (loc, target, lens, ortho) in SHOTS.items():
    cam = bpy.data.objects.new(f'cam_{name}', bpy.data.cameras.new(name))
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    if ortho:
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = ortho
    else:
        cam.data.lens = lens
    sc.collection.objects.link(cam)
    sc.camera = cam
    sc.render.filepath = str(OUT / f'{name}.png')
    bpy.ops.render.render(write_still=True, scene=sc.name)
    print('RENDER', name, flush=True)
