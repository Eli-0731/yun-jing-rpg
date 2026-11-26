# DR01 根拱上長的東西：拱頂與拱肩的短苔叢（有厚度）、蕨，拱底垂下來的小葉藤，根腳縫裡的蕨和心形葉。
# 由 build_dr01.py 的 dress() 呼叫。植物做法沿用核心組 D2 林下範本（core_plants.py）：一片片立體葉，不用葉片卡。
import bpy, math, random, importlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def dress(objs, centre, frame, fb, path_half, quick=True, seed=5, coll_name='DR01_High', prefix='DR01_P_', lite=False, amount=1.0):
    """lite=True：遊戲模型用的數量（蕨和葉叢少一點）。amount：數量再乘幾倍（v004 後拱 0.5）。"""
    n_foot_fern = int(round((6 if lite else 7) * amount))
    n_foot_heart = int(round((6 if lite else 7) * amount))
    import core_plants
    if not lite:
        importlib.reload(core_plants)      # lite 時呼叫端已換上降面數的 LeafBuf，不重載
    LeafBuf = core_plants.LeafBuf
    from core_plants import _leaf_material, _frame, fern, heart_plant
    # 心形葉：葉基寬、葉尖收尖（設定圖拱頂正面和根腳的小闊葉）
    HEART = lambda u: math.sin(math.pi * min(1.0, u * .8 + .2)) ** .6 * (1 - .55 * u ** 2.2)
    # 地上長的那種：和核心組林下範本 heart_plant 同一個葉形（兩片圓耳、尖端收尖）
    CORE_HEART = lambda u: (.55 + .45 * math.sin(math.pi * min(1, u / .5))) * (1 - u) ** .8 * (1 - .5 * max(0, .06 - u) / .06)
    R = random.Random(seed)
    coll = bpy.data.collections[coll_name]
    for o in list(coll.objects):
        if o.name.startswith(prefix):
            bpy.data.objects.remove(o, do_unlink=True)
    import numpy as np
    V, F, FM = [], [], []
    for o in objs:
        b = len(V)
        me = o.data
        V.extend(v.co.copy() for v in me.vertices)
        F.extend(tuple(b + i for i in p.vertices) for p in me.polygons)
        ca = me.color_attributes.get('Mask')
        if ca is None:                     # 已經清掉遮罩的遊戲模型：當作到處都可以長
            FM.extend([1.0] * len(me.polygons))
            continue
        col = np.empty(len(me.loops) * 4, np.float32)
        ca.data.foreach_get('color', col)
        red = col.reshape(-1, 4)[:, 0]
        ls = np.empty(len(me.polygons), np.int32)
        me.polygons.foreach_get('loop_start', ls)
        FM.extend(red[ls].tolist())          # 每個面的苔量（取第一個角）
    bvh = BVHTree.FromPolygons(V, F)

    def mat(name, *a, **k):
        return bpy.data.materials.get(name) or _leaf_material(name, *a, **k)

    fern_mat = mat('D2_Fern', (.050, .090, .040, 1), (.11, .17, .075, 1), (.16, .22, .11, 1), gloss=.55)
    heart_mat = mat('D2_HeartLeafPale', (.060, .105, .050, 1), (.135, .20, .10, 1), (.22, .29, .16, 1), gloss=.4)   # 設定圖的闊葉是偏灰的淺綠；太白在引擎裡會跳出來，壓一點
    moss_mat = mat('D2_MossTuft', (.040, .058, .014, 1), (.10, .125, .032, 1), (.12, .15, .045, 1), gloss=.8)
    stem_mat = bpy.data.materials.get('D2_Stem')
    if stem_mat is None:
        stem_mat = bpy.data.materials.new('D2_Stem')
        stem_mat.use_nodes = True
        next(n for n in stem_mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Base Color'].default_value = (.05, .06, .025, 1)
    groups = {'MossTufts': [], 'Ferns': [], 'Leaves': [], 'Stems': []}

    def keep(o, group):
        for c in list(o.users_collection):
            c.objects.unlink(o)
        coll.objects.link(o)
        groups[group].append(o)

    def hit_from(t, ang, lat):
        """從拱外某個方向往中心線打，回傳表面點、法線。ang：0 是拱外正上方，±pi/2 正前／正後，pi 是拱底。"""
        c = centre(t)
        d, side, nrm = frame(t)
        out = (nrm * math.cos(ang) + side * math.sin(ang)).normalized()
        h = bvh.ray_cast(c + out * 5 + d * lat, -out, 6)
        return (h[0], h[1], FM[h[2]]) if h[0] is not None else None

    # ---- 短苔叢：一根根小苔葉，長在拱頂、拱肩朝上朝外的面 ----
    mb = LeafBuf()
    n = 0
    want = 0          # 苔改成做在樹皮幾何和材質上的苔墊（團粒凹凸），不用一根根苔葉：近看像草，不像苔
    for i in range(want * 6):
        h = hit_from(R.uniform(.06, .94), R.gauss(0, .9), R.uniform(-.3, .3))
        if h is None:
            continue
        p, nr, moss = h
        if moss < .55:
            continue                              # 只長在有苔的地方
        dd = (nr + Vector((R.uniform(-.5, .5), R.uniform(-.5, .5), .35))).normalized()
        dd, s2, u2 = _frame(dd)
        L = R.uniform(.035, .08)
        g = R.uniform(.8, 1.2)
        mb.leaf(p - dd * .01, dd, s2, u2, L, L * .24, shape=lambda u: (1 - u) ** .6, fold=.3, droop=R.uniform(0, .5),
                tint=(g, g, g * .8), nu=2, nv=1)
        n += 1
        if n >= want:
            break
    # 地面根上的苔也長苔葉（從正上方往下找）
    n = 0
    want2 = want // 2
    for i in range(want2 * 10):
        h = bvh.ray_cast(Vector((R.uniform(-19, 19), R.uniform(-14, 12), 9)), Vector((0, 0, -1)), 12)
        if h[0] is None or h[0].z > 2.6 or FM[h[2]] < .55:
            continue
        p, nr = h[0], h[1]
        dd = (nr + Vector((R.uniform(-.5, .5), R.uniform(-.5, .5), .35))).normalized()
        dd, s2, u2 = _frame(dd)
        L = R.uniform(.035, .08)
        g = R.uniform(.8, 1.2)
        mb.leaf(p - dd * .01, dd, s2, u2, L, L * .24, shape=lambda u: (1 - u) ** .6, fold=.3, droop=R.uniform(0, .5),
                tint=(g, g, g * .8), nu=2, nv=1)
        n += 1
        if n >= want2:
            break
    if mb.V:
        keep(mb.build(prefix + 'MossTufts', moss_mat), 'MossTufts')

    # ---- 蕨：拱頂、拱肩上面長幾叢（設定圖的拱頂主要是苔，植物是一叢一叢的，不是沿著拱頂排一整排）----
    k = 0
    for tc, want in ((.29, 2), (.46, 2), (.57, 1), (.74, 2)):
        want = int(round(want * amount))
        if want <= 0:
            continue
        made = 0
        for i in range(40):
            h = hit_from(tc + R.uniform(-.03, .03), R.gauss(0, .45), R.uniform(-.2, .2))
            if h is None or h[1].z < .55:
                continue
            o, so = fern(f'{prefix}Fern{k}', h[0] - Vector((0, 0, .04)), R, R.uniform(.5, .9), fern_mat, stem_mat)
            keep(o, 'Ferns')
            keep(so, 'Stems')
            k += 1
            made += 1
            if made >= want:
                break

    def clump(buf, pos, nr, size, hang=True):
        """一小叢心形葉：幾根細葉柄從同一處伸出來。hang=True 是貼著樹皮長的（葉片在柄端往下垂、葉面朝外）；
        hang=False 是地上長的（長柄把葉片撐起來、葉面朝上，和核心組林下範本的心形葉同一個葉形）。
        葉柄和葉片在同一個網格裡，遊戲模型不會只剩葉片浮在半空。"""
        nr = nr.normalized()
        t0 = nr.cross(Vector((0, 0, 1)))
        if t0.length < .1:
            t0 = nr.cross(Vector((1, 0, 0)))
        t0.normalize()
        t1 = nr.cross(t0)
        n = R.randint(5, 8) if hang else R.randint(7, 11)
        for k in range(n):
            az = R.uniform(0, 2 * math.pi) if hang else 2 * math.pi * k / n + R.uniform(-.3, .3)
            rad = t0 * math.cos(az) + t1 * math.sin(az)
            if hang:
                pd = (nr * R.uniform(.5, 1.0) + rad * R.uniform(.4, 1.0) + Vector((0, 0, R.uniform(0, .5)))).normalized()
                Lp = size * R.uniform(.10, .26)
                ld = (pd * .35 + Vector((0, 0, -1)) * R.uniform(.35, .9) + rad * .35).normalized()
            else:
                pd = (nr * R.uniform(.9, 1.7) + rad * R.uniform(.4, 1.0)).normalized()
                Lp = size * R.uniform(.16, .36)
                ld = (rad + nr * R.uniform(-.35, -.05)).normalized()
            a, s2, u2 = _frame(pd)
            buf.leaf(pos, a, s2, u2, Lp, .006 if hang else .008, shape=lambda u: 1.0, fold=0, tint=(.6, .7, .5), nu=1, nv=1)      # 葉柄
            ls = ld.cross(nr)
            if ls.length < .1:
                ls = ld.cross(t0)
            ls.normalize()
            ln = ls.cross(ld).normalized()
            if ln.dot(nr) < 0:
                ls, ln = -ls, -ln
            g = R.uniform(.82, 1.15)
            if hang:
                L = size * R.uniform(.15, .27)
                buf.leaf(pos + pd * Lp, ld, ls, ln, L, L * .40, shape=HEART, fold=.18, curl=.08, droop=R.uniform(.05, .3),
                         tint=(g, g, g * .96), nu=6, nv=4, twist=R.uniform(-.3, .3))
            else:
                L = size * R.uniform(.11, .17)
                buf.leaf(pos + pd * Lp - ld * (L * .12), ld, ls, ln, L, L * .55, shape=CORE_HEART, fold=.1, curl=.15, droop=.2,
                         tint=(g, g, g * .96), nu=8, nv=4, twist=R.uniform(-.3, .3))

    # ---- 垂藤：從拱底和拱頂前後緣垂下，沿藤排小葉 ----
    vb = LeafBuf()
    # 幾處各垂兩三條（設定圖：拱洞左上、右上各幾條細藤），不是整排門簾。角度：負的是朝南那一面，pi 是拱底
    for tc, ac, want in ((.36, -1.9, 3), (.42, -2.3, 3), (.47, math.pi, 1), (.61, -1.9, 3), (.67, -2.4, 2), (.52, 2.0, 2), (.33, 2.2, 2)):
        want = int(round(want * amount))
        if want <= 0:
            continue
        made = 0
        for i in range(40):
            h = hit_from(tc + R.uniform(-.02, .02), ac + R.uniform(-.2, .2), R.uniform(-.2, .2))
            if h is None or h[0].z < 2.6:
                continue
            p0 = h[0] + h[1] * .03
            L = min(R.uniform(.7, 2.3), p0.z - 2.6)
            if L < .5:
                continue
            nseg = int(L / .13)
            sway = R.uniform(-.25, .25)
            for j in range(nseg):
                q = p0 + Vector((sway * (j / nseg) ** 2, math.sin(j * .5 + i) * .05, -L * j / nseg))
                dq, sq, uq = _frame(Vector((0.05, 0, -1)))
                vb.leaf(q, dq, sq, uq, .15, .008, shape=lambda u: 1.0, fold=0, tint=(.6, .7, .5), nu=1, nv=1)
                if j > 0 and R.random() < .7:
                    a = R.uniform(0, 6.3)                # 一節一片、左右亂數，不排成整齊的兩排
                    ld = Vector((math.cos(a), math.sin(a), -.5))
                    ld, ls, ln = _frame(ld)
                    Ll = R.uniform(.10, .17) * (1 - .3 * j / nseg)
                    g = R.uniform(.85, 1.1)
                    vb.leaf(q, ld, ls, ln, Ll, Ll * .42, shape=HEART,
                            fold=.15, droop=.3, tint=(g, g, g * .96), nu=5, nv=3)
            made += 1
            if made >= want:
                break
    # 心形葉：一處長幾小叢。前四處照設定圖擺（拱頂正面偏左、左腿上段、右腿中段、拱頂偏右），其餘亂數（南面北面都有）
    spots = [(.40, -1.15, 5), (.21, -1.0, 3), (.86, -1.2, 3), (.63, -1.0, 2)]
    for i in range(5):
        spots.append((R.uniform(.2, .8), R.choice([-1, 1, 1]) * R.uniform(.6, 1.5), R.randint(1, 2)))
    for tc, ac, want in spots:
        want = int(round(want * amount))
        if want <= 0:
            continue
        made = 0
        for i in range(40):
            h = hit_from(tc + R.uniform(-.02, .02), ac + R.uniform(-.4, .4), R.uniform(-.15, .15))
            if h is None or (h[2] < .15 and i < 20):
                continue                              # 先找有苔的地方長
            clump(vb, h[0], h[1], R.uniform(1.0, 1.5))
            made += 1
            if made >= want:
                break

    # ---- 根腳：根和根之間的縫裡長蕨和心形葉（貼著根，不是另外鋪地被）----
    kf = kh = 0
    for foot in (0, 1):
        cf = centre(0.0 if foot == 0 else 1.0)
        base = math.pi if foot == 0 else 0.0
        tries = nf = nh = 0
        while (nf < n_foot_fern or nh < n_foot_heart) and tries < 600:
            tries += 1
            a = base + R.uniform(-1.6, 1.6)
            dist = R.uniform(1.2, 7.5)
            x, y = cf.x + math.cos(a) * dist, cf.y + math.sin(a) * dist
            if abs(x) < path_half + .3:
                continue
            h = bvh.ray_cast(Vector((x, y, 9)), Vector((0, 0, -1)), 12)
            if h[0] is not None and h[0].z > .25:
                continue                      # 根上面不放，放在根旁邊
            if bvh.find_nearest(Vector((x, y, .1)), 1.1)[0] is None:
                continue                      # 要貼著根
            pos = Vector((x, y, -.02))
            if nf < n_foot_fern and (nh >= n_foot_heart or R.random() < .5):
                o, so = fern(f'{prefix}FootFern{kf}', pos, R, R.uniform(1.1, 1.8), fern_mat, stem_mat)
                keep(o, 'Ferns')
                keep(so, 'Stems')
                nf += 1
                kf += 1
            elif nh < n_foot_heart:
                clump(vb, pos, Vector((0, 0, 1)), R.uniform(1.6, 2.6), hang=False)
                nh += 1
                kh += 1
    if vb.V:
        keep(vb.build(prefix + 'Vines', heart_mat), 'Leaves')
    out = []
    for g, lst in groups.items():
        if not lst:
            continue
        if len(lst) > 1:
            with bpy.context.temp_override(active_object=lst[0], object=lst[0], selected_editable_objects=lst, selected_objects=lst):
                bpy.ops.object.join()
        lst[0].name = prefix + g
        out.append(lst[0])
    print('plants', [(o.name, len(o.data.polygons)) for o in out])
    return out
