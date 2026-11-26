# D2 根與木預覽場景：陰天漫射光、濕泥地、1.75 m 人形尺、和設定圖同鏡位的相機。只給預覽用，不是交付物件。
import bpy, math
from mathutils import Vector

PREVIEW = 'DR_Preview'


def setup(samples=64, fog=True):
    sc = bpy.context.scene
    coll = bpy.data.collections.get(PREVIEW)
    if coll:
        for o in list(coll.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    else:
        coll = bpy.data.collections.new(PREVIEW)
        sc.collection.children.link(coll)
    try:
        sc.render.engine = 'CYCLES'
    except TypeError as e:
        print(e)
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    try:
        pr = bpy.context.preferences.addons['cycles'].preferences
        for kind in ('OPTIX', 'CUDA'):
            try:
                pr.compute_device_type = kind
                break
            except TypeError:
                pass
        pr.get_devices()
        for d in pr.devices:
            d.use = True
        sc.cycles.device = 'GPU'
    except Exception as e:
        print('gpu', e)
    w = bpy.data.worlds.get('DR_World') or bpy.data.worlds.new('DR_World')
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs[0].default_value = (.50, .56, .62, 1)
    bg.inputs[1].default_value = 2.2
    sc.world = w
    try:
        sc.view_settings.view_transform = 'AgX'
    except TypeError as e:
        print(e)
    sun = bpy.data.objects.new('DR_Sun', bpy.data.lights.new('DR_Sun', 'SUN'))
    sun.data.energy = 2.2
    sun.data.angle = math.radians(45)
    sun.rotation_euler = (math.radians(50), 0, math.radians(-35))
    coll.objects.link(sun)
    me = bpy.data.meshes.new('DR_Ground')
    s = 120
    me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
    g = bpy.data.objects.new('DR_Ground', me)
    gm = bpy.data.materials.get('DR_Mud') or bpy.data.materials.new('DR_Mud')
    gm.use_nodes = True
    N, Lk = gm.node_tree.nodes, gm.node_tree.links
    b = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    if not any(n.type == 'TEX_NOISE' for n in N):
        nz = N.new('ShaderNodeTexNoise')
        nz.inputs['Scale'].default_value = .35
        nz.inputs['Detail'].default_value = 9
        r = N.new('ShaderNodeValToRGB')
        r.color_ramp.elements[0].position, r.color_ramp.elements[1].position = .35, .7
        r.color_ramp.elements[0].color = (.040, .030, .022, 1)
        r.color_ramp.elements[1].color = (.060, .062, .030, 1)
        Lk.new(nz.outputs[0], r.inputs[0])
        Lk.new(r.outputs[0], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = .75
    g.data.materials.append(gm)
    coll.objects.link(g)
    # 1.75 m 人形尺
    bpy.ops.mesh.primitive_cylinder_add(radius=.22, depth=1.75, location=(1.4, .5, .875))
    h = bpy.context.object
    h.name = 'DR_Human_1p75m'
    for c in list(h.users_collection):
        c.objects.unlink(h)
    coll.objects.link(h)
    hm = bpy.data.materials.get('DR_HumanMat') or bpy.data.materials.new('DR_HumanMat')
    hm.use_nodes = True
    next(n for n in hm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Base Color'].default_value = (.8, .8, .8, 1)
    h.data.materials.append(hm)
    if fog:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 20))
        f = bpy.context.object
        f.name = 'DR_Fog'
        f.scale = (240, 240, 60)
        for c in list(f.users_collection):
            c.objects.unlink(f)
        coll.objects.link(f)
        fm = bpy.data.materials.get('DR_FogMat') or bpy.data.materials.new('DR_FogMat')
        fm.use_nodes = True
        N, Lk = fm.node_tree.nodes, fm.node_tree.links
        for n in list(N):
            if n.type != 'OUTPUT_MATERIAL':
                N.remove(n)
        out = next(n for n in N if n.type == 'OUTPUT_MATERIAL')
        vs = N.new('ShaderNodeVolumeScatter')
        vs.inputs['Density'].default_value = .004
        vs.inputs['Color'].default_value = (.8, .85, .9, 1)
        Lk.new(vs.outputs[0], out.inputs['Volume'])
        f.data.materials.append(fm)
        f.display_type = 'WIRE'
    return coll


def shot(path, loc, tgt, lens=24, res=(1536, 864)):
    sc = bpy.context.scene
    cam = bpy.data.objects.get('DR_Cam')
    if cam is None:
        cam = bpy.data.objects.new('DR_Cam', bpy.data.cameras.new('DR_Cam'))
        (bpy.data.collections.get(PREVIEW) or sc.collection).objects.link(cam)
    cam.location = loc
    cam.data.lens = lens
    cam.data.clip_end = 500
    cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


VIEWS = {
    # 南入口第一眼。位置、焦段和核心組 root_arch.py 的 V2 相同；設定圖是平視（地平線在畫面正中、拱頂貼近上緣），
    # 所以對照設定圖用平視的 V2；V2core 是核心組原本的鏡位（往上抬 6.5 度，他們用 3:2 出圖）
    'V2': ((0.5, -15.0, 1.7), (0.0, 0.0, 1.7), 22),
    'V2core': ((0.5, -15.0, 1.7), (0.0, 0.0, 3.4), 22),
    'tq': ((-15.0, -15.0, 4.5), (0.0, 0.0, 2.6), 28),
    'back': ((1.0, 24.0, 2.5), (0.0, 0.0, 2.8), 35),         # 從祭壇方向回看（V4 的近一點版本）
    'top': ((0.0, -0.01, 46.0), (0.0, 0.0, 0.0), 35),
    'footL': ((-9.0, -7.5, 1.5), (-5.0, -0.5, 1.4), 35),
    'bark': ((-2.2, -3.2, 1.6), (-5.4, -0.9, 1.8), 50),          # 站在路邊、眼睛高度，看左腿（約 3.3 m 遠）
}
