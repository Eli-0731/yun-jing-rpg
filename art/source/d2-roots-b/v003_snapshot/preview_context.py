# DR01 對照圖用的陪襯：遠處的神木替身、霧、泥土路和踏石、前景的蕨和苔石。
# 只給「和設定圖 V2 同鏡位」的對照圖用，讓人看得出拱洞有沒有框住神木；不是交付物件，不匯出、不進遊戲。
# 用法（先跑過 preview_dr.setup()）：exec(open('preview_context.py').read()); context()
import bpy, math, random, os, sys
from mathutils import Vector, noise

HERE = 'D:/yun-jing-d2-roots/art/source/d2-roots-b'
if HERE not in sys.path:
    sys.path.insert(0, HERE)
PREVIEW = 'DR_Preview'
TREE_Y = 58.0          # 神木替身離拱 58 m（實際場景的位置以核心組的 D2 場景為準）


def context(seed=3, fog=.0035):
    import dr_core, core_plants
    R = random.Random(seed)
    noise.seed_set(seed)
    coll = bpy.data.collections[PREVIEW]
    for o in list(coll.objects):
        if o.name.startswith('DR_Ctx_'):
            bpy.data.objects.remove(o, do_unlink=True)
    keep = dict(dr_core.CFG)
    dr_core.CFG.update(step=.45, numin=28, numax=72, amp=.16, moss=.085)
    mat = dr_core.bark_material()
    try:
        made = []
        made.append(dr_core.tube('DR_Ctx_Trunk', [(0, TREE_Y, -2, 12.0, 1), (0, TREE_Y, 5, 9.6, 1), (.4, TREE_Y, 18, 8.2, 1), (0, TREE_Y, 40, 7.4, 1),
                                                  (-.5, TREE_Y, 75, 6.6, 1)], seed=1, rib=.30, twist=.05, collection=coll))
        n = 13
        for k in range(n):                      # 板根：從樹幹十幾公尺高流到地面，往四周散開
            a = 2 * math.pi * k / n + R.uniform(-.18, .18)
            c, s = math.cos(a), math.sin(a)
            reach = R.uniform(26, 38)
            h0 = R.uniform(11, 17)
            pts = []
            for f, z, r, fl in ((.13, h0, 2.4, 1.7), (.26, h0 * .52, 2.3, 1.9), (.45, h0 * .2, 1.8, 1.6), (.68, .9, 1.1, 1.3), (.88, .25, .55, 1.1), (1.0, -.7, .15, 1.0)):
                w = math.sin(f * 4 + k) * 1.6 * f
                pts.append((c * reach * f - s * w, TREE_Y + s * reach * f + c * w, z, r, fl))
            made.append(dr_core.tube(f'DR_Ctx_Buttress{k}', pts, seed=40 + k, rib=.26, twist=.08, collection=coll))
        for o in made:
            o.data.materials.append(mat)
            for p in o.data.polygons:
                p.use_smooth = True
    finally:
        dr_core.CFG.clear()
        dr_core.CFG.update(keep)
    # 前景：路兩邊的蕨
    fern_mat = bpy.data.materials.get('D2_Fern') or core_plants._leaf_material('D2_Fern', (.050, .090, .040, 1), (.11, .17, .075, 1), (.16, .22, .11, 1), gloss=.55)
    stem = bpy.data.materials.get('D2_Stem')
    k = 0
    for i in range(400):
        x, y = R.uniform(-13, 13), R.uniform(-13.5, -2.5)
        if abs(x) < 2.0 + max(0, (-y - 9)) * .25 or k >= 30:
            continue
        o, so = core_plants.fern(f'DR_Ctx_Fern{k}', Vector((x, y, -.03)), R, R.uniform(1.0, 2.1), fern_mat, stem)
        for q in (o, so):
            if q is None:
                continue
            for c in list(q.users_collection):
                c.objects.unlink(q)
            coll.objects.link(q)
            q.name = f'DR_Ctx_{q.name}' if not q.name.startswith('DR_Ctx_') else q.name
        k += 1
    for x, y, sz in ((-2.7, -11.6, 2.3), (-3.6, -10.1, 2.0), (-2.3, -9.0, 1.5), (3.1, -11.9, 2.2), (2.5, -9.6, 1.4), (-5.2, -8.2, 2.1), (5.6, -9.4, 1.8)):
        o, so = core_plants.fern(f'DR_Ctx_Fern{k}', Vector((x, y, -.03)), R, sz, fern_mat, stem)
        for q in (o, so):
            if q is None:
                continue
            for c in list(q.users_collection):
                c.objects.unlink(q)
            coll.objects.link(q)
            q.name = f'DR_Ctx_{q.name}' if not q.name.startswith('DR_Ctx_') else q.name
        k += 1
    # 泥土路（寬約 2.2 m，沿 Y 穿過拱洞）和踏石
    pm = bpy.data.materials.get('DR_Ctx_Path') or bpy.data.materials.new('DR_Ctx_Path')
    pm.use_nodes = True
    pb = next(q for q in pm.node_tree.nodes if q.type == 'BSDF_PRINCIPLED')
    pb.inputs['Base Color'].default_value = (.085, .066, .050, 1)
    pb.inputs['Roughness'].default_value = .8
    vs_, fs_ = [], []
    n = 60
    for i in range(n + 1):
        y = -18 + 60 * i / n
        cx = .35 * math.sin(y * .21) + .2 * math.sin(y * .47 + 1)
        w = 1.1 + .25 * math.sin(y * .33 + 2)
        vs_ += [(cx - w, y, .012), (cx + w, y, .012)]
        if i:
            b0 = 2 * (i - 1)
            fs_.append((b0, b0 + 1, b0 + 3, b0 + 2))
    me = bpy.data.meshes.new('DR_Ctx_Path')
    me.from_pydata(vs_, [], fs_)
    po = bpy.data.objects.new('DR_Ctx_Path', me)
    po.data.materials.append(pm)
    coll.objects.link(po)
    # 苔石
    sm = bpy.data.materials.get('DR_Ctx_Stone') or bpy.data.materials.new('DR_Ctx_Stone')
    sm.use_nodes = True
    N, Lk = sm.node_tree.nodes, sm.node_tree.links
    b = next(q for q in N if q.type == 'BSDF_PRINCIPLED')
    if not any(q.type == 'TEX_NOISE' for q in N):
        geo = N.new('ShaderNodeNewGeometry')
        sx = N.new('ShaderNodeSeparateXYZ')
        Lk.new(geo.outputs['Normal'], sx.inputs[0])
        nz = N.new('ShaderNodeTexNoise')
        nz.inputs['Scale'].default_value = 3.0
        nz.inputs['Detail'].default_value = 8
        ad = N.new('ShaderNodeMath')
        ad.operation = 'ADD'
        Lk.new(sx.outputs['Z'], ad.inputs[0])
        Lk.new(nz.outputs[0], ad.inputs[1])
        rp = N.new('ShaderNodeValToRGB')
        rp.color_ramp.elements[0].position, rp.color_ramp.elements[1].position = .95, 1.25
        rp.color_ramp.elements[0].color = (.085, .09, .095, 1)
        rp.color_ramp.elements[1].color = (.045, .065, .022, 1)
        Lk.new(ad.outputs[0], rp.inputs[0])
        Lk.new(rp.outputs[0], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = .7
    pm2 = bpy.data.materials.get('DR_Ctx_StepStone') or bpy.data.materials.new('DR_Ctx_StepStone')      # 踏石：灰石，不長滿苔
    pm2.use_nodes = True
    sb = next(q for q in pm2.node_tree.nodes if q.type == 'BSDF_PRINCIPLED')
    sb.inputs['Base Color'].default_value = (.12, .12, .115, 1)
    sb.inputs['Roughness'].default_value = .6
    stones = [(11.5, -9.5, 1.5, .7), (9.0, -12.5, 1.1, .7), (-11.0, -11.5, 1.3, .7), (4.7, -8.3, 1.15, .7), (3.6, -10.9, .8, .7), (-2.2, -12.2, .55, .6),
              (.25, -12.4, .42, .2), (-.35, -10.6, .38, .2), (.3, -8.7, .45, .2), (-.2, -6.6, .36, .2), (.35, -4.3, .42, .2), (-.1, -1.6, .4, .2), (.2, 1.5, .38, .2)]
    for i, (x, y, r, flat) in enumerate(stones):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=r, location=(x, y, r * (.28 if flat > .5 else .04)))
        o = bpy.context.object
        o.name = f'DR_Ctx_Stone{i}'
        o.scale = (1.0, R.uniform(.8, 1.15), R.uniform(.62, .78) * flat / .7)
        for v in o.data.vertices:
            p = v.co
            v.co = p * (1 + .16 * noise.noise(p * (1.1 / r) + Vector((i * 7, 0, 0))) + .05 * noise.noise(p * (4 / r)))
        for p in o.data.polygons:
            p.use_smooth = True
        o.data.materials.append(sm if flat > .5 else pm2)
        for c in list(o.users_collection):
            c.objects.unlink(o)
        coll.objects.link(o)
    f = bpy.data.objects.get('DR_Fog')
    if f:
        vs = next(q for q in f.data.materials[0].node_tree.nodes if q.type == 'VOLUME_SCATTER')
        vs.inputs['Density'].default_value = fog
    h = bpy.data.objects.get('DR_Human_1p75m')
    if h:
        h.location = (1.4, .5, .875)
    print('context objects', len([o for o in coll.objects if o.name.startswith('DR_Ctx_')]))
