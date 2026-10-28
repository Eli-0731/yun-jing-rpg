"""Assembled-yard renders from the master file (run after build_yard.py and build_yard.py -- --master):

  blender -b art/source/qingxi-training-yard-v1/Qingxi_Training_Yard_v1.blend --python-exit-code 1 \
          --python art/source/qingxi-training-yard-v1/review_yard.py

Renders the YardPreview scene (baked game meshes at the demo layout) under a physical sky, including
1.7 m eye-height views from the village approach, the steps and under the roof.
"""
import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parents[2] / 'art/previews/qingxi-training-yard-v1'
scene = bpy.data.scenes['YardPreview']
bpy.context.window_manager.windows[0].scene = scene if bpy.context.window_manager.windows else None


def gpu(sc, samples):
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
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True


gpu(scene, 128)
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Base Contrast'
world = bpy.data.worlds.new('YardSky')
scene.world = world
nt = world.node_tree
sky = nt.nodes.new('ShaderNodeTexSky')
for attr, val in (('sun_elevation', math.radians(28)), ('sun_rotation', math.radians(-38)), ('altitude', 300.0)):
    if hasattr(sky, attr):
        setattr(sky, attr, val)
nt.links.new(sky.outputs['Color'], nt.nodes['Background'].inputs['Color'])
nt.nodes['Background'].inputs['Strength'].default_value = 0.35
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN'))
sun.data.energy = 3.2
sun.data.angle = math.radians(1.5)
sun.data.color = (1.0, 0.92, 0.80)
sun.rotation_euler = (math.radians(62), 0, math.radians(142))
scene.collection.objects.link(sun)

gm = bpy.data.materials.new('PreviewMeadow')
b = gm.node_tree.nodes['Principled BSDF']
noise = gm.node_tree.nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 0.35
ramp = gm.node_tree.nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].color = (0.035, 0.05, 0.018, 1)
ramp.color_ramp.elements[1].color = (0.10, 0.12, 0.04, 1)
gm.node_tree.links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
gm.node_tree.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
b.inputs['Roughness'].default_value = 1.0
pm = bpy.data.materials.new('PreviewPath')
pb = pm.node_tree.nodes['Principled BSDF']
pb.inputs['Base Color'].default_value = (0.16, 0.115, 0.07, 1)
pb.inputs['Roughness'].default_value = 1.0


def plane(name, verts, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], [tuple(range(len(verts)))])
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    return ob


plane('meadow', [(-150, -150, -0.002), (150, -150, -0.002), (150, 150, -0.002), (-150, 150, -0.002)], gm)
plane('path', [(-1.6, -3.0, 0.002), (1.6, -3.0, 0.002), (2.0, -22, 0.002), (-1.2, -22, 0.002)], pm)

SHOTS = {
    'eye-height-village-approach': ((0.6, -14.5, 1.70), (0.0, 0.0, 1.9), 24),
    'eye-height-steps': ((0.2, -5.4, 1.70), (0.0, 1.0, 1.75), 22),
    'eye-height-under-shelter': ((0.3, -1.3, 0.30 + 1.70), (-1.9, 1.0, 1.1), 22),
    'eye-height-stone-and-banner': ((-1.9, -6.6, 1.70), (-3.8, -0.4, 0.8), 26),
    'yard-overview': ((-11.0, -14.0, 7.0), (0.0, -0.4, 1.4), 30),
}
for name, (loc, target, lens) in SHOTS.items():
    cam = bpy.data.objects.new(f'cam_{name}', bpy.data.cameras.new(name))
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens
    cam.data.sensor_width = 36
    scene.collection.objects.link(cam)
    scene.camera = cam
    scene.render.filepath = str(OUT / f'{name}.png')
    bpy.ops.render.render(write_still=True, scene=scene.name)
    print('RENDER', name, flush=True)
