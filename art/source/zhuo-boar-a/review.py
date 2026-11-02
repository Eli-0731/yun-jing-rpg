"""Review sheets for BR01 and BR02, with EEVEE and a Poly Haven HDRI (CC0, not in the repo: YJ_HDRI overrides the path).

  blender -b --python-exit-code 1 --python art/source/zhuo-boar-a/review.py -- boar|pine [quick]

The preview material does what the Unity shader does (YunJing/QingxiZhuoBoar): the base map, the mask, _Zhuo / _Scar, vertex colour.
"""
import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitlib as K
from kitlib import L, N, math_, mix, smooth

args = sys.argv[sys.argv.index('--') + 1:]
WHAT = args[0]
QUICK = 'quick' in args
HDRI = Path(os.environ.get('YJ_HDRI', Path.home() / '.cache/yunjing/hdri/kloofendal_48d_partly_cloudy_puresky_2k.hdr'))
RES = 700 if QUICK else 1280


def lighting(sun_yaw=-140, sun_pitch=24):
    s = bpy.context.scene
    s.render.engine = 'BLENDER_EEVEE'
    s.eevee.taa_render_samples = 24 if QUICK else 64
    if hasattr(s.eevee, 'use_raytracing'): s.eevee.use_raytracing = True
    w = bpy.data.worlds.new('Review'); s.world = w; w.use_nodes = True; nt = w.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = N(nt, 'ShaderNodeOutputWorld'); bg = N(nt, 'ShaderNodeBackground'); env = N(nt, 'ShaderNodeTexEnvironment')
    env.image = bpy.data.images.load(str(HDRI)); L(nt, env.outputs[0], bg.inputs['Color']); bg.inputs['Strength'].default_value = .5
    L(nt, bg.outputs[0], out.inputs['Surface'])
    sd = bpy.data.lights.new('Sun', 'SUN'); sd.energy = 3.2; sd.color = (1, .82, .62); sd.angle = math.radians(4)
    so = bpy.data.objects.new('Sun', sd); s.collection.objects.link(so)
    so.rotation_euler = (math.radians(90 - sun_pitch), 0, math.radians(sun_yaw))
    s.view_settings.view_transform = 'AgX'; s.view_settings.look = 'AgX - Medium High Contrast'
    gm = bpy.data.materials.new('Ground'); gm.use_nodes = True; b = gm.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (.34, .36, .27, 1); b.inputs['Roughness'].default_value = 1
    bpy.ops.mesh.primitive_plane_add(size=60); g = bpy.context.active_object; g.name = 'ReviewGround'; g.data.materials.append(gm)
    return s


def person(x, y=0):
    """The 1.75 m figure."""
    m = bpy.data.materials.new('Figure'); m.use_nodes = True
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.32, .36, .5, 1)
    objs = []
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=.17, depth=1.46, location=(x, y, .73)); objs.append(bpy.context.active_object)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, radius=.145, location=(x, y, 1.605)); objs.append(bpy.context.active_object)
    for o in objs: o.data.materials.append(m); o.name = 'Figure'
    return objs


def preview_material(key, name='M_Preview'):
    """Base map, mask, vertex colour, with a value node per state."""
    tdir = K.EXPORTS / key / 'textures'
    img = lambda n, cs: (lambda i: (setattr(i.colorspace_settings, 'name', cs), i)[1])(bpy.data.images.load(str(tdir / f'T_{key}_{n}.png'), check_existing=True))
    m, nt, b = K.new_mat(name)
    bc = N(nt, 'ShaderNodeTexImage', image=img('BaseColor', 'sRGB'))
    mk = N(nt, 'ShaderNodeTexImage', image=img('Mask', 'Non-Color'))
    orm = N(nt, 'ShaderNodeTexImage', image=img('ORM', 'Non-Color'))
    nm = N(nt, 'ShaderNodeTexImage', image=img('Normal', 'Non-Color'))
    nmap = N(nt, 'ShaderNodeNormalMap'); L(nt, nm.outputs['Color'], nmap.inputs['Color']); L(nt, nmap.outputs['Normal'], b.inputs['Normal'])
    sp = N(nt, 'ShaderNodeSeparateColor'); L(nt, mk.outputs['Color'], sp.inputs['Color'])
    so = N(nt, 'ShaderNodeSeparateColor'); L(nt, orm.outputs['Color'], so.inputs['Color'])
    L(nt, so.outputs['Green'], b.inputs['Roughness'])
    z = N(nt, 'ShaderNodeValue'); z.name = '_Zhuo'; z.outputs[0].default_value = 1
    sc = N(nt, 'ShaderNodeValue'); sc.name = '_Scar'; sc.outputs[0].default_value = 0
    lo = math_(nt, 'SUBTRACT', 1.0, z.outputs[0])
    vein = smooth(nt, sp.outputs['Red'], lo, math_(nt, 'ADD', lo, .5))
    vein = math_(nt, 'MULTIPLY', vein, smooth(nt, z.outputs[0], 0, .002))
    vein = math_(nt, 'MULTIPLY', vein, smooth(nt, sp.outputs['Red'], .015, .025))
    deep = mix(nt, math_(nt, 'MULTIPLY', sp.outputs['Red'], 1.4, True), (.2, .055, .36), (.085, .022, .185))
    c = mix(nt, math_(nt, 'MULTIPLY', vein, .92), bc.outputs['Color'], deep)
    L(nt, deep, b.inputs['Emission Color']); L(nt, math_(nt, 'MULTIPLY', vein, .16), b.inputs['Emission Strength'])
    c = mix(nt, math_(nt, 'MULTIPLY', sp.outputs['Green'], z.outputs[0]), c, (.36, .05, .05))
    c = mix(nt, math_(nt, 'MULTIPLY', smooth(nt, sp.outputs['Blue'], .15, .6), sc.outputs[0]), c, (.5, .33, .16))
    va = N(nt, 'ShaderNodeVertexColor', layer_name='Col')
    mul = N(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY', clamp_factor=True); mul.inputs[0].default_value = 1
    L(nt, c, mul.inputs[6]); L(nt, va.outputs['Color'], mul.inputs[7])
    L(nt, mul.outputs[2], b.inputs['Base Color'])
    fur_path = tdir / f'T_{key}_Fur.png'
    if fur_path.exists():
        uv2 = N(nt, 'ShaderNodeUVMap', uv_map='UV2')
        fur = N(nt, 'ShaderNodeTexImage', image=img('Fur', 'Non-Color'))
        L(nt, uv2.outputs['UV'], fur.inputs['Vector'])
        L(nt, math_(nt, 'GREATER_THAN', fur.outputs['Alpha'], .5), b.inputs['Alpha'])
        tone = N(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY', clamp_factor=True); tone.inputs[0].default_value = 1
        L(nt, mul.outputs[2], tone.inputs[6]); L(nt, fur.outputs['Color'], tone.inputs[7])
        L(nt, tone.outputs[2], b.inputs['Base Color'])
        m.surface_render_method = 'DITHERED'
    return m


def cam_view(target, yaw, pitch, dist, lens=70):
    s = bpy.context.scene
    cam = s.camera or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    if not s.camera: s.collection.objects.link(cam); s.camera = cam
    cam.data.lens = lens; cam.data.clip_end = 300
    y, p = math.radians(yaw), math.radians(pitch)
    d = Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p)))
    cam.location = Vector(target) + d * dist
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()


def shot(path, w=None, h=None):
    s = bpy.context.scene
    s.render.resolution_x, s.render.resolution_y = w or RES, h or int(RES * .68)
    s.render.resolution_percentage = 100
    s.render.film_transparent = False
    s.render.filepath = str(path)
    s.render.image_settings.file_format = 'PNG'
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)
    print('SHOT', path, flush=True)


def boar():
    key = 'BR01_ZhuoBoar'
    bpy.ops.wm.open_mainfile(filepath=str(K.HERE / 'blend' / f'{key}_v001.blend'))
    s = lighting()
    obj = bpy.data.objects[key]
    pm = preview_material(key)
    for name in (key, key + '_LOD1', key + '_LOD2'):
        o = bpy.data.objects[name]; o.data.materials[0] = pm
    bpy.data.objects[key + '_LOD1'].hide_render = True
    bpy.data.objects[key + '_LOD2'].hide_render = True
    arm = bpy.data.objects['RIG_BR01_ZhuoBoar']
    set_zhuo = lambda v: setattr(pm.node_tree.nodes['_Zhuo'].outputs[0], 'default_value', v)
    out = K.PREVIEWS / key
    t = (0, 0, .52)
    arm.data.pose_position = 'REST'
    fig = person(0, 1.6)
    if QUICK:
        cam_view((.75, 0, .62), 90, 8, 5.2, 60); shot(out / 'quick_side.png')
        for o in fig: o.hide_render = True
        cam_view(t, 40, 10, 3.2); shot(out / 'quick_34.png')
        cam_view((0, -.3, .6), 0, 6, 2.6); shot(out / 'quick_front.png')
        set_zhuo(0); cam_view(t, 40, 10, 3.2); shot(out / 'quick_clean.png'); set_zhuo(1)
        return
    for name, yaw, pitch in (('front', 0, 6), ('side', 90, 6), ('back', 180, 6), ('three_quarter', 40, 12)):
        cam_view((.45 if name in ('front', 'back') else .35, 0, .72), yaw, pitch, 5.0, 60)
        shot(out / f'{name}.png')
    for o in fig: o.hide_render = True
    set_zhuo(1); cam_view(t, 40, 10, 3.1); shot(out / 'zhuo_1.png')
    set_zhuo(.5); shot(out / 'zhuo_0.5.png')
    set_zhuo(0); shot(out / 'zhuo_0.png')
    set_zhuo(1)
    cam_view((0, -.55, .5), 25, 8, 1.5); shot(out / 'head.png')
    cam_view((.05, -.2, .8), 120, 28, 1.9); shot(out / 'bristles.png')
    # The animation contact sheet: three moments of each clip.
    arm.data.pose_position = 'POSE'
    for clip, frames in (('Idle', (1, 17, 41)), ('Paw', (6, 15, 23)), ('Charge', (1, 6, 12)), ('Daze', (12, 32, 60)), ('Cleanse', (5, 30, 56)), ('Flee', (1, 8, 15))):
        arm.animation_data.action = bpy.data.actions[clip]
        for f in frames:
            s.frame_set(f); cam_view((0, 0, .5), 72, 8, 3.5, 60); shot(out / 'anim' / f'{clip}_{f:02d}.png', 720, 480)
    # LOD silhouettes side by side.
    arm.data.pose_position = 'REST'
    for lvl in (0, 1, 2):
        name = key if lvl == 0 else f'{key}_LOD{lvl}'
        for other in (key, key + '_LOD1', key + '_LOD2'): bpy.data.objects[other].hide_render = other != name
        cam_view(t, 70, 8, 3.2); shot(out / 'lod' / f'LOD{lvl}.png', 720, 480)


def import_any(path):
    before = set(bpy.data.objects)
    if str(path).endswith('.glb'): bpy.ops.import_scene.gltf(filepath=str(path))
    else: bpy.ops.import_scene.fbx(filepath=str(path))
    return [o for o in bpy.data.objects if o not in before]


def move_roots(objs, by):
    for o in objs:
        if o.parent is None: o.location = Vector(o.location) + Vector(by)


def boar_lineup():
    """Beside the rabbit v003 and the 1.75 m figure."""
    key = 'BR01_ZhuoBoar'
    bpy.ops.wm.open_mainfile(filepath=str(K.HERE / 'blend' / f'{key}_v001.blend'))
    lighting()
    pm = preview_material(key)
    for name in (key, key + '_LOD1', key + '_LOD2'): bpy.data.objects[name].data.materials[0] = pm
    bpy.data.objects[key + '_LOD1'].hide_render = bpy.data.objects[key + '_LOD2'].hide_render = True
    bpy.data.objects['RIG_BR01_ZhuoBoar'].data.pose_position = 'REST'
    rabbit = import_any(K.REPO / 'art/exports/qingxi-mountain-rabbit-v003/QingxiMountainRabbit_v003.glb')
    move_roots(rabbit, (0, 1.1, 0))
    person(0, -1.25)
    cam_view((0, .0, .78), 90, 7, 5.2, 55); shot(K.PREVIEWS / key / 'lineup_rabbit_figure.png')


def pine(var):
    key = f'BR02_YoungPine_{var}'
    bpy.ops.wm.open_mainfile(filepath=str(K.HERE / 'blend' / f'{key}_v001.blend'))
    lighting()
    pm = preview_material(key)
    for name in (key, key + '_LOD1', key + '_LOD2'):
        bpy.data.objects[name].data.materials[0] = pm
    bpy.data.objects[key + '_LOD1'].hide_render = bpy.data.objects[key + '_LOD2'].hide_render = True
    out = K.PREVIEWS / key
    fig = person(2.0)
    if QUICK:
        cam_view((.8, 0, 2.5), 0, 5, 15, 60); shot(out / 'quick_front.png')
        for o in fig: o.hide_render = True
        cam_view((0, 0, .8), 30, 8, 3.2, 60); pm.node_tree.nodes['_Scar'].outputs[0].default_value = 1; shot(out / 'quick_scar.png')
        return
    for name, yaw, pitch in (('front', 0, 5), ('side', 90, 5), ('back', 180, 5), ('three_quarter', 40, 14)):
        cam_view((.8, 0, 2.5), yaw, pitch, 11.5, 60); shot(out / f'{name}.png', 1000, 1000)
    for o in fig: o.hide_render = True
    cam_view((0, 0, 7), 0, 89, 7.5, 60); shot(out / 'top.png', 1000, 1000)
    cam_view((0, 0, .8), 30, 8, 3.2, 60); shot(out / 'trunk.png', 1000, 800)
    pm.node_tree.nodes['_Scar'].outputs[0].default_value = 1; shot(out / 'trunk_scar.png', 1000, 800)
    pm.node_tree.nodes['_Scar'].outputs[0].default_value = 0
    for lvl in (0, 1, 2):
        name = key if lvl == 0 else f'{key}_LOD{lvl}'
        for other in (key, key + '_LOD1', key + '_LOD2'): bpy.data.objects[other].hide_render = other != name
        cam_view((0, 0, 2.5), 30, 6, 10, 60); shot(out / 'lod' / f'LOD{lvl}.png', 720, 720)


def pine_lineup():
    """Both pines with the existing CommonPine and the A01 upstream reach."""
    bpy.ops.wm.open_mainfile(filepath=str(K.HERE / 'blend' / 'BR02_YoungPine_A_v001.blend'))
    lighting()
    pm = preview_material('BR02_YoungPine_A')
    a = bpy.data.objects['BR02_YoungPine_A']; a.data.materials[0] = pm
    a.location = (-.5, -2.5, 0)
    for n in ('_LOD1', '_LOD2'): bpy.data.objects['BR02_YoungPine_A' + n].hide_render = True
    with bpy.data.libraries.load(str(K.HERE / 'blend' / 'BR02_YoungPine_B_v001.blend')) as (src, dst): dst.objects = ['BR02_YoungPine_B']
    b = dst.objects[0]; bpy.context.scene.collection.objects.link(b); b.location = (.8, 2.8, 0)
    b.data.materials[0] = preview_material('BR02_YoungPine_B', 'M_PreviewB')
    common = import_any(K.REPO / 'art/incoming/dondon/CommonPine/v001/CommonPine_v001.fbx')
    move_roots(common, (-1.2, 8.2, 0))
    river = import_any(K.REPO / 'art/exports/qingxi-waterhead-a/A01_straight_01.glb')
    move_roots(river, (6.5, -1, 0))
    person(.6, -.1)
    cam_view((1.5, 2.6, 2.6), 58, 13, 21, 55); shot(K.PREVIEWS / 'lineup_pines_common_a01.png', 1400, 900)


if WHAT == 'boar':
    boar()
elif WHAT == 'boar_lineup':
    boar_lineup()
elif WHAT == 'pine':
    pine(args[1])
elif WHAT == 'pine_lineup':
    pine_lineup()
