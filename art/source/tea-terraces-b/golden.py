"""Presentation lighting for tea-terraces-b, following the reference art direction:
low warm morning sun with a soft warm rim, blue-violet shadows (never black), a pale sky, thin white mist in the distance.

Used by showcase_tea_terraces_b.py and beauty_views.py. Render only: nothing here touches the exported models.
"""
import bpy, math, random
from mathutils import Vector, Matrix


def _mat(name, rgb, rough=.9):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Roughness'].default_value = rough
    return m


def setup(scene, sun_azimuth_deg=-35., sun_elev_deg=17., fog=.0035, strength=1.0, samples=96, res=(1920, 1080), fog_centre=(0., 0., 0.), fog_size=(700., 700., 140.), sky=.85):
    """Cycles, a warm sun from the front-left, a sky that is pale and warm at the horizon and soft blue overhead, and a thin world fog."""
    scene.render.engine = 'CYCLES'
    try: scene.cycles.device = 'GPU'
    except Exception: pass
    scene.cycles.samples = samples; scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = res; scene.render.film_transparent = False
    scene.view_settings.view_transform = 'AgX'
    try: scene.view_settings.look = 'AgX - Medium High Contrast'
    except Exception: scene.view_settings.look = 'None'
    scene.view_settings.exposure = .35
    for o in [o for o in scene.objects if o.type == 'LIGHT']: bpy.data.objects.remove(o, do_unlink=True)
    sun = bpy.data.objects.new('Golden_Sun', bpy.data.lights.new('Golden_Sun', 'SUN')); scene.collection.objects.link(sun)
    sun.data.energy = 4.2 * strength; sun.data.color = (1., .80, .58); sun.data.angle = math.radians(2.5)
    az, el = math.radians(sun_azimuth_deg), math.radians(sun_elev_deg)
    to_sun = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    sun.rotation_euler = (-to_sun).to_track_quat('-Z', 'Y').to_euler()
    rim = bpy.data.objects.new('Rim_Fill', bpy.data.lights.new('Rim_Fill', 'SUN')); scene.collection.objects.link(rim)
    rim.data.energy = .55 * strength; rim.data.color = (.72, .74, 1.); rim.data.angle = math.radians(20)
    rim.rotation_euler = (Vector((-to_sun.x, -to_sun.y, -.6))).to_track_quat('-Z', 'Y').to_euler()   # cool light from the opposite side lifts the shadows to blue-violet
    w = bpy.data.worlds.new('Golden_Sky'); w.use_nodes = True; nt = w.node_tree; nodes = nt.nodes; links = nt.links
    bg = nodes['Background']; bg.inputs['Strength'].default_value = sky * strength
    tc = nodes.new('ShaderNodeTexCoord'); sep = nodes.new('ShaderNodeSeparateXYZ'); links.new(tc.outputs['Generated'], sep.inputs[0])
    ramp = nodes.new('ShaderNodeValToRGB'); links.new(sep.outputs['Z'], ramp.inputs[0])
    cr = ramp.color_ramp; cr.elements[0].position = .5; cr.elements[0].color = (.98, .86, .70, 1); cr.elements[1].position = .78; cr.elements[1].color = (.47, .58, .78, 1)
    links.new(ramp.outputs[0], bg.inputs['Color'])
    scene.world = w
    if fog > 0:
        # a bounded fog box, not a world volume: in Cycles a world volume is infinitely deep, so the sun (at infinity) never gets through and the frame goes black
        cx, cy, cz = fog_centre; sx, sy, sz = fog_size
        bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, cz + sz / 2 - 20)); box = bpy.context.object; box.name = 'Fog_Volume'; box.scale = (sx, sy, sz)
        fm = bpy.data.materials.new('Fog_Volume'); fm.use_nodes = True; fn = fm.node_tree.nodes; fn.remove(fn['Principled BSDF'])
        vs = fn.new('ShaderNodeVolumeScatter'); vs.inputs['Density'].default_value = fog; vs.inputs['Color'].default_value = (.86, .89, .97, 1); vs.inputs['Anisotropy'].default_value = .35
        fm.node_tree.links.new(vs.outputs[0], fn['Material Output'].inputs['Volume']); box.data.materials.append(fm)
        box.visible_shadow = False   # the mist should not cast a shadow block over the scene
    return sun


def distant_hills(scene, centre=(0, 0, 0), radius=140., seed=3, count=7, height=(25, 55), col=(.30, .36, .42)):
    """Soft blue-green ridgelines far behind the subject: low-poly displaced cones, only seen through the mist."""
    R = random.Random(seed); m = _mat('Distant_Hill', col, .95); out = []
    for k in range(count):
        a = math.radians(R.uniform(35, 145)); r = radius * R.uniform(.85, 1.25)
        h = R.uniform(*height); base = h * R.uniform(1.8, 2.6)
        bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=base, radius2=base * .08, depth=h, location=(centre[0] + r * math.cos(a), centre[1] + r * math.sin(a), centre[2] + h / 2 - 4))
        o = bpy.context.object; o.name = 'Distant_Hill'; o.data.materials.append(m)
        o.scale = (1., R.uniform(.5, .8), 1.); o.rotation_euler = (0, 0, R.uniform(0, 3.14))
        d = o.modifiers.new('Lumps', 'DISPLACE'); t = bpy.data.textures.new('HillNoise', 'CLOUDS'); t.noise_scale = base * .35; d.texture = t; d.strength = h * .25
        sub = o.modifiers.new('Sub', 'SUBSURF'); sub.levels = 2; sub.render_levels = 2; o.modifiers.move(1, 0)
        out.append(o)
    return out


def ground_plane(scene, z=0., size=600., col=(.13, .11, .075)):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, z)); g = bpy.context.object; g.name = 'Presentation_Ground'
    g.data.materials.append(_mat('Presentation_Ground', col, .95)); return g


def camera(scene, eye, target, lens=35):
    cam = scene.camera
    if cam is None:
        cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); scene.collection.objects.link(cam); scene.camera = cam
    cam.data.lens = lens; cam.data.clip_end = 2000; cam.location = eye
    cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat('-Z', 'Y').to_euler()
    return cam


def shot(scene, path, eye, target, lens=35, samples=None):
    camera(scene, eye, target, lens)
    if samples: scene.cycles.samples = samples
    scene.render.filepath = str(path); bpy.ops.render.render(write_still=True)
    print('GOLDEN_SHOT', path, flush=True)
