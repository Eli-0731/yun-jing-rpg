# DR02 拼接檢查（只為了看接起來的樣子，不交付）：三件都跑完 game_dr02 以後，在開著的 Blender 裡 exec 這個檔再 start()。
# A、B、C、B 四件首尾相接排成空地外圈（半徑 26 m）的一段弧，出三張圖到 art/previews/d2-roots-b/DR02_pack/；
# low_points(2.5) 量接縫處牆頂最低多高（重疊 2.5 m 就是 game_dr02 的 OVERLAP：下一件的 Socket_Head 對到這件的 Socket_Tail）。
import bpy, math, os, time, traceback
from mathutils import Vector, Matrix
D = 'D:/yun-jing-d2-roots/art/source/d2-roots-b/'
W = D.replace('art/source/d2-roots-b/', 'art/previews/d2-roots-b/DR02_pack/')
LOG = os.environ.get('DR_WORK2', 'D:/yun-jing-cache/dr02-work/') + 'pack_run.log'     # 紀錄不進版本庫
R = 26.0          # 空地半徑（外圈約 14 件）


def load(n):
    g = {'__file__': D + n, '__name__': n[:-3]}
    exec(compile(open(D + n, encoding='utf-8').read(), D + n, 'exec'), g)
    return g


def ends(v):
    b = load('build_dr02.py')
    b['set_variant'](v)
    ts = [i / 400 for i in range(401)]
    f = b['spine_at']
    if b['VAR'].get('branches'):      # 分岔件：主幹＋前枝（接口和 game_dr02 一樣放在這條線上）
        trunk = [p for p in b['VAR']['spine'] if p[0] < 3.6]
        pts = [(b['X0'] + s, y, z, r, fl) for s, y, z, r, fl in trunk + list(b['VAR']['branches'][0][1])]
        f = lambda t: b['_along'](pts, t)
    up = [t for t in ts if (lambda c, r, fl: c.z + r * fl * .5 > .1)(*f(t))]    # 頂面還露在土上的那一段
    h, t = f(up[0])[0], f(up[-1])[0]
    return Vector((h.x, h.y, 0)), Vector((t.x, t.y, 0))


def grab(v, tag):
    path = f'{D}blend/DR02_RootWall_{v}_v001.blend'
    want = [f'DR02_RootWall_{v}_LOD0', 'Detail_DR02_Plants_LOD0']
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n in want]
    lib = bpy.data.libraries.get(os.path.basename(path)) or next((l for l in bpy.data.libraries if os.path.normcase(bpy.path.abspath(l.filepath)) == os.path.normcase(path)), None)
    if lib:                    # 附加完就放掉來源檔，不然之後 game_dr02 存同一個 .blend 會失敗（Cannot overwrite used library）
        bpy.data.libraries.remove(lib)
    coll = bpy.data.collections.get('DR02_Pack') or bpy.data.collections.new('DR02_Pack')
    if coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)
    out = []
    for o in dst.objects:
        o.name = f'PACK_{tag}_{o.name}'
        coll.objects.link(o)
        o.parent = None
        out.append(o)
    return out


def run(order=("A", "B", "C", "B"), overlap=2.5, views=True):
    t0 = time.time()
    open(LOG, 'w').write('start\n')
    try:
        for o in list(bpy.data.objects):
            if o.name.startswith(('DR02', 'Detail_DR02', 'Socket_', 'PACK_')):
                bpy.data.objects.remove(o, do_unlink=True)
        ang = .55                    # 弧從這個角度開始（往 -ang 方向接）
        info = []
        for i, v in enumerate(order):
            h, t = ends(v)
            span = (t - h).length
            dang = (span - overlap) / R
            a0, a1 = ang, ang - dang     # 粗頭→細頭時正面（-Y）在右手邊，所以沿弧順時針排，正面就朝圓心
            P0 = Vector((R * math.cos(a0), R * math.sin(a0), 0))
            P1 = Vector((R * math.cos(a1), R * math.sin(a1), 0))
            # 本地：粗頭在 h、細頭在 t、正面 -Y。放到世界：h→P0、t 方向→P1，正面朝圓心
            loc_dir = (t - h).normalized()
            wd = (P1 - P0).normalized()
            rot = math.atan2(wd.y, wd.x) - math.atan2(loc_dir.y, loc_dir.x)
            M = Matrix.Translation(P0) @ Matrix.Rotation(rot, 4, 'Z') @ Matrix.Translation(-h)
            # 正面（-Y）要朝圓心：檢查，不對就沿弦翻 180°（鏡像不行，改成繞弦中點轉）
            front = (Matrix.Rotation(rot, 4, 'Z') @ Vector((0, -1, 0)))
            mid = (P0 + P1) / 2
            flip = front.dot(-mid) < 0     # 只檢查，不翻（翻了會上下顛倒）
            for o in grab(v, f'{i}{v}'):
                o.matrix_world = M @ o.matrix_world
            info.append((v, round(span, 2), flip))
            ang = a1
        open(LOG, 'a').write('placed %r\n' % (info,))
        if views:
            pv = load('preview_dr.py')
            pv['setup'](samples=32)
            h = bpy.data.objects.get('DR_Human_1p75m')
            mid_a = (.55 + ang) / 2
            C = Vector((R * math.cos(mid_a), R * math.sin(mid_a), 0))
            if h:
                h.location = C * .86 + Vector((0, 0, .875))
            shots = {
                'over': (Vector((0, 0, 0)) - C * .25 + Vector((0, 0, 13)), C * 1.0 + Vector((0, 0, .5)), 20),
                'eye': (C * .55 + Vector((0, 0, 1.65)), C * 1.0 + Vector((0, 0, 1.4)), 16),
                'top': (C * .95 + Vector((0, -.01, 55)), C * .95, 30),
            }
            for n, (loc, tgt, lens) in shots.items():
                pv['shot'](f'{W}DR02_pack_{n}.png', tuple(loc), tuple(tgt), lens, res=(1600, 800))
                open(LOG, 'a').write('shot %s %.0f s\n' % (n, time.time() - t0))
        open(LOG, 'a').write('DONE %.0f s\n' % (time.time() - t0))
    except Exception:
        open(LOG, 'a').write('ERROR\n' + traceback.format_exc())


def start(**kw):
    bpy.app.timers.register(lambda: run(**kw), first_interval=.5)


def low_points(overlap, skip_tail=5.0, skip_head=3.0):
    """接好以後沿弧量牆頂高度（每 0.25 m，橫跨 ±3 m 取最高），回傳弧長與最低三處（不含最前、最後一段）。"""
    from mathutils.bvhtree import BVHTree
    run(overlap=overlap, views=False)
    trees = []
    for o in bpy.data.objects:
        if o.name.startswith('PACK_') and '_LOD0' in o.name and 'Detail' not in o.name:
            M = o.matrix_world
            trees.append(BVHTree.FromPolygons([M @ v.co for v in o.data.vertices], [tuple(p.vertices) for p in o.data.polygons]))
    prof, a = [], .55
    while a > -2.6:
        best = 0.0
        for dr in [x * .25 for x in range(-12, 13)]:
            p = Vector(((R + dr) * math.cos(a), (R + dr) * math.sin(a), 20))
            for t in trees:
                h = t.ray_cast(p, Vector((0, 0, -1)), 25)
                if h[0] is not None:
                    best = max(best, h[0].z)
        prof.append(((.55 - a) * R, best))
        a -= .25 / R
    on = [p for p in prof if p[1] > 0]
    s0, s1 = on[0][0], on[-1][0]
    inner = [p for p in prof if s0 + skip_head < p[0] < s1 - skip_tail]
    return round(s1 - s0, 1), [(round(s, 1), round(h, 2)) for s, h in sorted(inner, key=lambda p: p[1])[:3]]
