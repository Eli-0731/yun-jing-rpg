# DR07 巨樹樁的積水：照使用者青溪水工 B 的做法（CR06／F01 的 <件名>_water），水面是另一個模型，本體 FBX 不含水。
#   - DR07_GiantStump_<A|B>_water_v001.fbx（＋ .glb，LOD0）：<件名>_water_LOD0／1／2，原點和本體相同（底部中心），沒有貼圖；
#   - UV 以公尺計（u、v 都是公尺，水面中心是 0），給 YunJing/CreekFlowWater 的靜水模式（_Still = 1，同 F01 田裡積水的 Field_StillWater）；
#   - 水面邊緣推進內壁 4 cm（藏起水線的接縫），高度 = 建模參數 pool（A、B 都是 0.70 m）。
# 兩種狀態：有水 = 本體 ＋ 水面；沒水 = 只放本體（樹洞底是一層泥、落葉，牆腳長苔）。
# 水面上的浮葉（第六輪）也在這個模型裡（第二個材質槽，用本體圖集），所以沒水時不會有葉子浮在半空。
# 用法（開遊戲 blend；game_dr07.py 之後、report_dr07.py 之前）：
#   blender -b art/source/d2-logs-b/blend/DR07_GiantStump_A_v001.blend --python art/source/d2-logs-b/water_dr07.py -- A
import bpy, sys, os, math, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__)).replace('\\', '/')
ROOT = os.path.abspath(HERE + '/../../..').replace('\\', '/')
ASSETS = {'A': 'DR07_GiantStump_A', 'B': 'DR07_GiantStump_B'}
VER = 'v001'
LODS = ((64, (.5, 1.0)), (32, (1.0,)), (16, (1.0,)))        # （邊數, 每圈半徑比例）：LOD0 兩圈 64 邊，LOD1 32 邊、LOD2 16 邊扇形
TUCK = .04                                                  # 邊緣推進內壁


def _load(p):
    g = {'__file__': p, '__name__': os.path.basename(p)[:-3]}
    exec(compile(open(p, encoding='utf-8').read(), p, 'exec'), g)
    return g


def outline(body, c, z, n=128):
    """從水面中心水平往外打到本體 LOD0（內壁），每個方向的距離。"""
    bpy.context.view_layer.update()
    t = BVHTree.FromPolygons([body.matrix_world @ v.co for v in body.data.vertices], [tuple(p.vertices) for p in body.data.polygons])
    out = []
    for j in range(n):
        a = 2 * math.pi * j / n
        h = t.ray_cast(Vector((c.x, c.y, z)), Vector((math.cos(a), math.sin(a), 0)), 6)[0]
        out.append((h - Vector((c.x, c.y, z))).length if h else None)
    good = [d for d in out if d]
    fill = sorted(good)[len(good) // 2]
    return [d if d else fill for d in out]


def float_leaves(det, c, z, dist, n=14, seed=7):
    """浮葉：從 Detail_DR07_Plants_LOD0 裡挑洞底的落葉（一片一個連通塊），複製 n 片浮到水面上（攤平、轉個方向、換位置）。
    留著圖集 UV（同 M_<件名>_Leaf 那組貼圖），水面 FBX 第二個材質槽。回傳 [(頂點, 面, UV)]，一片一組。"""
    import bmesh, random
    R = random.Random(seed)
    bm = bmesh.new()
    bm.from_mesh(det.data)
    bm.transform(det.matrix_world)
    bm.faces.ensure_lookup_table()
    uvl = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.active
    rmin = min(dist) * .85
    seen, cand = set(), []
    for f0 in bm.faces:
        if f0.index in seen:
            continue
        isl, st = [], [f0]
        seen.add(f0.index)
        while st:
            f = st.pop()
            isl.append(f)
            for e in f.edges:
                for g in e.link_faces:
                    if g.index not in seen:
                        seen.add(g.index)
                        st.append(g)
        vs = {v for f in isl for v in f.verts}
        if len(isl) > 80:
            continue
        if all(math.hypot(v.co.x - c.x, v.co.y - c.y) < rmin and z - .35 < v.co.z < z for v in vs):
            cand.append(isl)
    R.shuffle(cand)
    out = []
    n0 = len(dist)
    for isl in cand[:n]:
        vs = sorted({v for f in isl for v in f.verts}, key=lambda v: v.index)
        cen = sum((v.co for v in vs), Vector()) / len(vs)
        zmin = min(v.co.z for v in vs)
        a = R.uniform(0, 2 * math.pi)
        ca, sa = math.cos(a), math.sin(a)
        b_ = R.uniform(0, 2 * math.pi)
        rr = dist[int(round(b_ / (2 * math.pi) * n0)) % n0] * R.uniform(.15, .78)
        nx, ny = c.x + math.cos(b_) * rr, c.y + math.sin(b_) * rr
        idx = {v.index: k for k, v in enumerate(vs)}
        co = []
        for v in vs:
            dx, dy = v.co.x - cen.x, v.co.y - cen.y
            co.append((nx + dx * ca - dy * sa, ny + dx * sa + dy * ca, z + .004 + (v.co.z - zmin) * .3))   # 浮著：攤平，葉緣略翹
        fs, uvs = [], []
        for f in isl:
            fs.append([idx[l.vert.index] for l in f.loops])
            uvs.append([tuple(l[uvl].uv) for l in f.loops])
        out.append((co, fs, uvs))
    bm.free()
    print('FLOAT_LEAVES', len(cand), 'on the floor,', len(out), 'floated')
    return out


def make(v):
    asset = ASSETS[v]
    EXP = f'{ROOT}/art/exports/d2-logs-b/{asset}'
    b = _load(HERE + '/build_dr07.py')
    V = b['set_variant'](v)
    P = Vector(bpy.context.scene.get('dr_pivot', (0.0, 0.0, 0.0)))
    root = bpy.data.objects[asset]
    root.location = (0, 0, 0)
    bpy.context.view_layer.update()
    body = bpy.data.objects[f'{asset}_LOD0']
    z = V['pool']
    ax, ay = b['axis_xy'](V, z)
    c = Vector((ax - P.x, ay - P.y, z))                       # 資產座標（底部中心原點）
    dist = outline(body, c, z)
    n0 = len(dist)
    for o in [o for o in bpy.data.objects if o.name.startswith(f'{asset}_water')]:
        bpy.data.objects.remove(o, do_unlink=True)
    for me in [me for me in bpy.data.meshes if me.name.startswith(f'{asset}_water') and me.users == 0]:
        bpy.data.meshes.remove(me)                            # 重跑時舊網格還在，新的會被改名成 .001
    coll = bpy.data.collections.get(f'DR07_{V["name"]}_Water') or bpy.data.collections.new(f'DR07_{V["name"]}_Water')
    if coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)
    mat = b['water_material'](f'M_{asset}_Water')
    det = bpy.data.objects.get('Detail_DR07_Plants_LOD0')
    leaves = float_leaves(det, c, z, dist) if det else []
    lmat = det.data.materials[0] if det and det.data.materials else None
    wroot = bpy.data.objects.new(f'{asset}_water', None)
    coll.objects.link(wroot)
    objs = []
    for lv, (na, rings) in enumerate(LODS):
        vs, uvs = [(c.x, c.y, z)], [(0.0, 0.0)]
        fuv = None
        for u in rings:
            for j in range(na):
                a = 2 * math.pi * j / na
                d = dist[int(round(j * n0 / na)) % n0] + TUCK
                x, y = c.x + math.cos(a) * d * u, c.y + math.sin(a) * d * u
                vs.append((x, y, z))
                uvs.append((x - c.x, y - c.y))                 # 公尺
        fs = [(0, 1 + j, 1 + (j + 1) % na) for j in range(na)]
        for k in range(len(rings) - 1):
            b0, b1 = 1 + k * na, 1 + (k + 1) * na
            for j in range(na):
                j2 = (j + 1) % na
                fs.append((b0 + j, b1 + j, b1 + j2, b0 + j2))
        nw = len(fs)
        lf = [] if lv == 2 or lmat is None else leaves[:len(leaves) if lv == 0 else len(leaves) // 2]   # 浮葉：LOD0 全部、LOD1 一半、LOD2 不放
        fuv = []
        for co, lfs, luv in lf:
            base = len(vs)
            vs += co
            fs += [[base + i for i in f] for f in lfs]
            fuv += luv
        me = bpy.data.meshes.new(f'{asset}_water_LOD{lv}')
        me.from_pydata(vs, [], fs)
        me.update()
        uv = me.uv_layers.new(name='UVMap')
        for p in me.polygons:
            for k, li in enumerate(p.loop_indices):
                if p.index < nw:
                    uv.data[li].uv = uvs[me.loops[li].vertex_index]
                else:
                    uv.data[li].uv = fuv[p.index - nw][k]
        me.materials.append(mat)
        if lf:
            me.materials.append(lmat)
            for p in me.polygons:
                p.material_index = 0 if p.index < nw else 1
        for p in me.polygons:
            p.use_smooth = True
        o = bpy.data.objects.new(f'{asset}_water_LOD{lv}', me)
        assert o.name == f'{asset}_water_LOD{lv}', o.name
        coll.objects.link(o)
        o.parent = wroot
        objs.append(o)
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs + [wroot]:
        o.select_set(True)
    bpy.context.view_layer.objects.active = wroot
    fbx = f'{EXP}/{asset}_water_{VER}.fbx'
    bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, object_types={'MESH', 'EMPTY'},
                             apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', bake_space_transform=True,
                             axis_forward='-Z', axis_up='Y', mesh_smooth_type='FACE', use_mesh_modifiers=True,
                             add_leaf_bones=False, bake_anim=False, path_mode='STRIP', embed_textures=False)
    bpy.ops.object.select_all(action='DESELECT')
    for o in (objs[0], wroot):
        o.select_set(True)
    try:
        bpy.ops.export_scene.gltf(filepath=f'{EXP}/{asset}_water_{VER}.glb', use_selection=True, export_format='GLB', export_yup=True)
    except Exception as e:
        print('glb', e)
    # 留在 blend 裡、跟著本體走（審圖時 dr_pivot.frame 搬本體，水面一起搬）
    for o in objs:
        mw = o.matrix_world.copy()
        o.parent = root
        o.matrix_world = mw
    bpy.data.objects.remove(wroot, do_unlink=True)
    tri = lambda o: sum(len(p.vertices) - 2 for p in o.data.polygons)
    r = [d + TUCK for d in dist]
    info = dict(file=os.path.basename(fbx), objects=[o.name for o in objs], triangles={f'LOD{i}': tri(o) for i, o in enumerate(objs)},
                origin='same as the body FBX (bottom centre)', z_m=round(z, 3), centre_xy_m=[round(c.x, 3), round(c.y, 3)],
                radius_m=dict(min=round(min(r), 3), max=round(max(r), 3), mean=round(sum(r) / len(r), 3)), edge_tucked_into_wall_m=TUCK,
                uv='u, v in metres from the water centre (standing water: CreekFlowWater _Still = 1 reads uv as metres on both axes)',
                textures='water: none; floating leaves (2nd material slot): the stump atlas, same material as Detail_ plants',
                floating_leaves={f'LOD{i}': len(o.data.materials) > 1 and sum(1 for p in o.data.polygons if p.material_index == 1) for i, o in enumerate(objs)},
                collision='none (the stump collision closes the hollow on top)')
    bpy.context.scene['dr07_water'] = json.dumps(info)
    bpy.ops.wm.save_mainfile()
    print('WATER_DONE', json.dumps(info, ensure_ascii=False))
    return info


if __name__ == '__main__' and '--' in sys.argv:
    make(sys.argv[sys.argv.index('--') + 1])
