# DR08 大香菇穿插檢查（遊戲 blend 的 LOD0 本體）：第二槽（植物材質）的面 = 大香菇。
# 分成一塊塊（菌傘是封閉的一塊、菌柄是一塊），檢查：
#   1. 香菇的點有沒有卡進本體其他件（樹幹、斷口、木條、碎塊、土堆）超過 1 cm（菌柄根部埋進地面 / 土堆以下不算）
#   2. 菌柄有沒有穿過別朵的菌傘、菌傘之間有沒有疊進去（自己那頂菌傘不算）
#   blender -b art/source/d2-logs-b/blend/DR08_RottenLog_A_v001.blend --python art/source/d2-logs-b/clip_dr08.py -- A
import bpy, bmesh, sys, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree

v = sys.argv[sys.argv.index('--') + 1]
for lv in (0, 1, 2):
    o = bpy.data.objects[f'DR08_RottenLog_{v}_LOD{lv}']
    mw = o.matrix_world
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.transform(mw)
    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    mush = [f for f in bm.faces if f.material_index == 1]
    rest = [f for f in bm.faces if f.material_index != 1]
    rtree = BVHTree.FromPolygons([vv.co.copy() for vv in bm.verts], [[vv.index for vv in f.verts] for f in rest])
    gtree = BVHTree.FromPolygons([vv.co.copy() for vv in bm.verts], [[vv.index for vv in f.verts] for f in rest if f.normal.z > .3])
    # 一塊塊
    seen, islands = set(), []
    adj = {}
    for f in mush:
        for e in f.edges:
            for g in e.link_faces:
                if g.material_index == 1 and g is not f:
                    adj.setdefault(f.index, set()).add(g.index)
    for f in mush:
        if f.index in seen:
            continue
        st, isl = [f.index], []
        seen.add(f.index)
        while st:
            k = st.pop()
            isl.append(k)
            for g in adj.get(k, ()):
                if g not in seen:
                    seen.add(g)
                    st.append(g)
        islands.append(isl)
    info = []
    for isl in islands:
        vs = sorted({vv.index for k in isl for vv in bm.faces[k].verts})
        closed = all(e.is_manifold for k in isl for e in bm.faces[k].edges)
        tree = BVHTree.FromPolygons([vv.co.copy() for vv in bm.verts], [[vv.index for vv in bm.faces[k].verts] for k in isl])
        info.append(dict(vs=vs, closed=closed, tree=tree, top=max(vs, key=lambda i: bm.verts[i].co.z)))
    def _odd(tree, p, d):
        k, q = 0, p.copy()
        for _ in range(40):
            h = tree.ray_cast(q, d, 10)
            if h[0] is None:
                break
            k += 1
            q = h[0] + d * 1e-4
        return k % 2 == 1

    bad_body = 0
    for it in info:
        for i in it['vs']:
            p = bm.verts[i].co
            loc, n, _, d = rtree.find_nearest(p)
            if loc is None or (p - loc).dot(n) > -.01:
                continue
            if d > .06 and not all(_odd(rtree, p, Vector(dd).normalized()) for dd in ((0, 0, 1), (1, .13, .07), (-.11, 1, .05))):
                continue                                    # 離最近的面很遠、三個方向打出去都是偶數次：在外面（最近的面剛好是背對的底面）
            g = gtree.ray_cast(p + Vector((0, 0, 2)), Vector((0, 0, -1)), 3)
            if g[0] is not None and p.z < g[0].z + .01 and not it['closed']:
                continue                                    # 菌柄根部埋在地面／土堆裡
            if p.z < .01:
                continue
            bad_body += 1
    caps = [it for it in info if it['closed']]
    stems = [it for it in info if not it['closed']]

    def inside(cap, p):                                 # 封閉菌傘：往三個方向打，穿過面數都是奇數才算在裡面（不靠法線方向）
        loc, n, _, dist = cap['tree'].find_nearest(p)
        if loc is None or dist < .003:
            return False
        return all(_odd(cap['tree'], p, Vector(d).normalized()) for d in ((0, 0, 1), (1, .13, .07), (-.11, 1, .05)))
    bad_mm = 0
    for st in stems:
        top = bm.verts[st['top']].co
        own = [c for c in caps if inside(c, top)]
        for c in caps:
            if c in own:
                continue
            bad_mm += sum(1 for i in st['vs'] if inside(c, bm.verts[i].co))
    for a in range(len(caps)):
        for b in range(len(caps)):
            if a != b:
                bad_mm += sum(1 for i in caps[a]['vs'] if inside(caps[b], bm.verts[i].co))
    print('CLIP', v, f'LOD{lv}', json.dumps(dict(caps=len(caps), stems=len(stems), into_body_over_1cm=bad_body, mushroom_vs_mushroom=bad_mm)))
    bm.free()
