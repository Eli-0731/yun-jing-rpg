# DR04 根間的樹洞（高模）：沿用 build_dr02.py 的整套根做法（內芯＋一股股扭絞的根＋苔），控制點換成「兩條板根夾一個洞」。
#   兩條板根（左右各一，像 DR02 的板根，高 2 m 左右的立板）從後面（神木那邊，+Y）往前（-Y）斜下去鑽進土裡，相距約 2.4 m；
#   兩條板根之間、靠後面的地方是一個黑洞口：寬約 1.5 m、高約 1.5 m，往裡約 1.4 m。
#   洞頂是一條拱起來的根唇（從左板根內側拱到右板根內側），根唇後面是蓋住洞頂的根、再後面是封住的心材牆（背面靠在神木或根牆上）。
#   洞裡：朽木纖維一條條從洞頂垂下、貼著洞壁；洞底後面堆著一堆朽掉的心材（偏紅褐、鬆軟）。洞口前、洞裡地上有落葉（在 game_dr04 的植物裡）。
#   （設定圖 V5 最左邊板根之間的黑洞；Codex 三視圖 art/references/DR04/v001/DR04-threeview.png）
# 正面 -Y（看進洞口），原點在洞口正下方的地面（洞口最前緣），z = 0 是地面。
# 在 Blender 裡：b = 載入此檔; b['set_variant']('H'); b['build'](quick=True)
import os

_HERE = os.path.dirname(os.path.abspath(globals().get('__file__', 'D:/yun-jing-d2-roots/art/source/d2-roots-b/build_dr04.py')))
_src = os.path.join(_HERE, 'build_dr02.py')
exec(compile(open(_src, encoding='utf-8').read(), _src, 'exec'), globals())

# 控制點 (x, y, z, 半寬, 扁度)：roots 模式、x0 = 0，所以就是世界座標。半寬是和根的走向垂直、水平方向的半寬；扁度 >1 是立起來的板。
# 照 Codex 三視圖：洞口本身是一道粗根拱（根從拱頂沿兩側流下來、在地面攤開），後面再一道更高的拱當洞頂，
# 最後面是封住的心材牆（往神木那邊升高到約 2.3 m）；兩側各一條板根從後面高處斜下來、往前往外攤開鑽進土裡。


def _arch(y, top, leg, r, fl, lean=.0, n=9, splay=.30, p=.80):
    """一道根拱：兩腳在 x = ±leg 鑽進土裡，拱頂中心高 top；lean：拱頂往後（+Y）偏多少；
    splay：拱腳貼地時再往外攤多少（設定圖的根從拱頂流下來、到地面往外攤開，不是直直插進土裡）。"""
    out = []
    for k in range(n):
        a = math.pi * k / (n - 1)                     # 0 → pi：右腳 → 左腳
        c, s_ = math.cos(a), math.sin(a)
        x = leg * c * (1 + .06 * s_) + math.copysign(splay * (1 - s_) ** 3, c)
        z = -.18 + (top + .18) * s_ ** p         # p 越小拱越圓、兩側越直（洞口上半不會收成尖拱）
        out.append((x, y + lean * s_ - .06 * (1 - s_), z, r * (1 + .10 * (1 - s_)), fl))
    return tuple(out[::-1])


VARIANTS.update({
    'H': dict(name='Hollow', L=4.0, seed=67, turns=.34, plants=1.0, sides=0, branch_sides=0, head_roots=False, x0=0.0, flare=0.0,
              rho=(.26, .36), dk=(.78, .92), moss_add=.35, hollow=True,
              roots=(
                  # 0 洞口的根拱：內緣寬約 1.5 m、高約 1.5 m
                  _arch(.22, 1.86, 1.30, .43, 1.0, lean=.05, splay=.20, p=.60),
                  # 1 後面那道拱：更高、更寬，當洞頂（兩道拱之間的頂是兩道拱的股絞在一起）
                  _arch(.95, 2.10, 1.55, .48, 1.0, lean=.10, splay=.25, p=.65),
                  # 2 心材牆：封住背面，往神木那邊升高（背面靠在神木或根牆上）
                  # （兩端往下鑽進土裡，不然從側面看是兩個懸空的斷面）
                  ((-2.05, 1.90, -.30, .36, 1.6), (-1.55, 1.97, .70, .52, 2.0), (-.75, 2.02, 1.15, .58, 2.0), (.20, 2.05, 1.18, .58, 2.0),
                   (1.10, 2.00, 1.05, .56, 2.0), (1.65, 1.94, .62, .50, 2.0), (2.10, 1.88, -.30, .34, 1.6)),
                  # 3 左板根：從後面高處沿洞的左側斜下來，往前往外攤開鑽進土裡（起點埋在心材牆裡，背面才不會露出斷頭）
                  ((-1.05, 2.18, 1.10, .40, 2.0), (-1.69, 1.10, .95, .40, 1.9), (-1.86, .10, .55, .36, 1.7), (-2.19, -.75, .22, .28, 1.5), (-2.59, -1.45, -.30, .15, 1.15)),
                  # 4 右板根：比左邊短一點、更往外撇
                  ((1.05, 2.18, 1.02, .38, 2.0), (1.76, 1.05, .85, .38, 1.85), (2.02, .15, .45, .33, 1.6), (2.44, -.55, .15, .25, 1.4), (2.84, -1.10, -.30, .14, 1.1)),
              ),
              strands=34, peel=0, lift_gap=False),
})

_top_moss0 = top_moss


def top_moss(p, nrm):
    """頂上一整片厚苔（moss_add 0 就和 DR02 一樣）。洞裡（洞頂以下、洞口後面）不長苔。"""
    m = _top_moss0(p, nrm) + VAR.get('moss_add', 0.0) * max(0.0, nrm.z) ** 1.5
    if VAR.get('hollow') and abs(p.x) < 1.15 and .15 < p.y < 1.75 and p.z < 1.65 and nrm.z < .5:
        m -= 1.0
    return m


_build_roots = build


def build(quick=True, seed=None, name='DR02_High', low=None, only_big=0.0):
    objs = _build_roots(quick=quick, seed=seed, name=name, low=low, only_big=only_big)
    if VAR.get('hollow') and not only_big:
        objs += _hollow(name, objs)
    return objs


def rot_material():
    """朽木心材：深紅褐、鬆軟，沿長度方向一條條纖維紋；越往洞裡越暗（洞裡的暗主要靠烘焙的 AO 和這個底色）。"""
    m = bpy.data.materials.get('D2RotWood')
    if m:
        return m
    m = bpy.data.materials.new('D2RotWood')
    m.use_nodes = True
    N, Lk = m.node_tree.nodes, m.node_tree.links
    b = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    tc = N.new('ShaderNodeTexCoord')
    mp = N.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (14.0, 14.0, 1.6)       # 纖維順著 z（垂下來、貼著洞壁往下）
    Lk.new(tc.outputs['Object'], mp.inputs['Vector'])
    fib = N.new('ShaderNodeTexNoise')
    fib.inputs['Scale'].default_value = 3.0
    fib.inputs['Detail'].default_value = 8.0
    Lk.new(mp.outputs['Vector'], fib.inputs['Vector'])
    blot = N.new('ShaderNodeTexNoise')
    blot.inputs['Scale'].default_value = 2.2
    blot.inputs['Detail'].default_value = 3.0
    Lk.new(tc.outputs['Object'], blot.inputs['Vector'])
    r1 = N.new('ShaderNodeValToRGB')
    e = r1.color_ramp.elements
    e[0].position, e[0].color = .35, (.018, .010, .006, 1)
    e[1].position, e[1].color = .70, (.230, .105, .045, 1)
    Lk.new(fib.outputs['Fac'], r1.inputs['Fac'])
    r2 = N.new('ShaderNodeValToRGB')
    e = r2.color_ramp.elements
    e[0].position, e[0].color = .40, (.45, .45, .45, 1)
    e[1].position, e[1].color = .62, (1, 1, 1, 1)
    Lk.new(blot.outputs['Fac'], r2.inputs['Fac'])
    mx = N.new('ShaderNodeMixRGB')
    mx.blend_type = 'MULTIPLY'
    mx.inputs[0].default_value = 1.0
    Lk.new(r1.outputs['Color'], mx.inputs[1])
    Lk.new(r2.outputs['Color'], mx.inputs[2])
    Lk.new(mx.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = .92
    return m


def _hollow(name, objs):
    """洞裡的東西：洞底後面一堆朽掉的心材、貼著後壁的朽木板、從兩道拱的內緣垂下來的朽木纖維（一圈參差的流蘇）。都用 D2RotWood。
    位置用射線找：纖維從拱的內面往下垂、後壁的朽木板貼著心材牆的前面。物件名有 Rot：game_dr04 烘焙時放在同一組。"""
    from mathutils.bvhtree import BVHTree
    R = random.Random(VAR['seed'] + 13)
    coll = bpy.data.collections[name]
    mat = rot_material()
    pre = name.replace('_High', '') + '_'
    V, F = [], []
    for o in objs:
        b0 = len(V)
        V.extend(o.matrix_world @ v.co for v in o.data.vertices)
        F.extend(tuple(b0 + i for i in p.vertices) for p in o.data.polygons)
    bvh = BVHTree.FromPolygons(V, F)
    out = []
    # 位置只在做高模時用射線算一次、存在場景裡；低模（沒有樹皮凹凸，表面差幾公分）沿用同一份，烘焙時高低模才對得上
    import json
    key = f'dr04_hollow_{VAR["seed"]}'
    sc = bpy.context.scene
    is_low = CFG['amp'] == 0.0
    plan = json.loads(sc[key]) if (is_low and key in sc) else None
    rec = []

    def add(nm, pts, rib=.14, twist=.15, sd=None):
        sd = R.uniform(0, 50) if sd is None else sd
        rec.append((nm, [list(p) for p in pts], rib, twist, sd))
        o = tube(pre + 'Rot' + nm, pts, collection=coll, seed=sd, rib=rib, twist=twist)
        o.data.materials.append(mat)
        out.append(o)

    if plan is not None:
        for nm, pts, rib, twist, sd in plan:
            add(nm, [tuple(p) for p in pts], rib, twist, sd)
        return out

    def up_hit(x, y, z0=.2):
        h = bvh.ray_cast(Vector((x, y, z0)), Vector((0, 0, 1)), 3.0)
        return h[0]

    def back_hit(x, z):
        h = bvh.ray_cast(Vector((x, .3, z)), Vector((0, 1, 0)), 3.0)
        return h[0]

    # 洞底後面一堆朽心材（鬆軟、塌成一坨），貼著後壁
    yb = (back_hit(0.0, .3) or Vector((0, 1.45, .3))).y
    add('Heap', [(-.95, yb - .10, -.05, .22, .9), (-.48, yb - .18, .14, .34, .85), (.10, yb - .20, .18, .36, .85), (.60, yb - .15, .10, .30, .9), (1.00, yb - .08, -.06, .20, .9)], rib=.25)
    add('Heap2', [(-.50, yb - .55, -.06, .13, .9), (-.15, yb - .48, .05, .19, .8), (.28, yb - .50, .04, .17, .8), (.58, yb - .58, -.07, .12, .9)], rib=.25)
    # 後壁的朽木板：從洞頂一路貼著心材牆前面往下，下端埋進那堆朽心材
    for j in range(8):
        x = -.80 + 1.60 * j / 7 + R.uniform(-.05, .05)
        pts = []
        for z in (1.35, 1.05, .75, .45, .15):
            h = back_hit(x, z)
            if h is None:
                continue
            pts.append((h.x, h.y - .03, z, .065 * (1 - .2 * abs(z - .7)), 1.7))
        if len(pts) >= 3:
            add(f'Wall{j}', pts, rib=.30, twist=.05)
    # 兩側內壁的朽木條：貼著兩道拱的拱腳內面，從地面往上到拱的內面（洞口一進去兩側就是紅褐色的朽心材，不是外面的樹皮）
    def side_hit(y, z, sg):
        h = bvh.ray_cast(Vector((0, y, z)), Vector((sg, 0, 0)), 1.9)
        return h[0]
    for sg in (-1, 1):
        for j, y in enumerate((.02, .26, .50, .74, .98, 1.22)):
            y += R.uniform(-.05, .05)
            pts = []
            for z in (.05, .35, .65, .95, 1.20):
                h = side_hit(y, z, sg)
                if h is None:
                    continue
                pts.append((h.x - sg * .025, h.y, z, .055 + .015 * R.random(), 1.0))
            if len(pts) >= 3:
                add(f'Side{"LR"[sg > 0]}{j}', pts, rib=.30, twist=.05)
    # 拱內緣垂下來的纖維：一圈參差的流蘇，前面那道拱（洞口）密、後面那道少；長短不一，下端收尖
    k = 0
    for j in range(80):
        front = j < 58
        y = R.uniform(.05, .45) if front else R.uniform(.75, 1.20)
        x = R.uniform(-1.15, 1.15)
        h = up_hit(x, y)
        if h is None or h.z > 2.1 or h.z < .55:
            continue
        top = h.z + .04
        L = R.uniform(.15, .60) * (1.0 if abs(x) < .6 else .7)
        L = min(L, top - .25)
        if L < .08:
            continue
        rr = R.uniform(.014, .030)
        sw = R.uniform(-.04, .04)
        n = 5
        pts = [(x + sw * (i / n) ** 2, y + R.uniform(-.01, .01), top - L * i / n, max(rr * (1 - .8 * i / n), .006), 1.0) for i in range(n + 1)]
        add(f'Fib{k:02d}', pts, rib=.05, twist=.3)
        k += 1
    if not is_low:
        sc[key] = json.dumps(rec)
    return out


def dress(objs, quick=True, seed=5):
    """高模植物：沿兩條板根長（板根頂上的蕨、心形葉叢，根腳的小蕨）。洞口的落葉在遊戲植物裡做。"""
    import dr01_dress
    importlib.reload(dr01_dress)
    out = []
    for li, pre in ((3, 'DR02_P_'), (4, 'DR02_Q_')):          # 沿兩側的板根長（不是沿洞口的拱，不然根腳的蕨會擋住洞口）
        c1, f1 = _line(li)
        out += dr01_dress.dress(objs, c1, f1, fb, PATH_HALF, quick=quick, seed=seed + 11 * li, coll_name='DR02_High', prefix=pre,
                                amount=VAR['plants'], avoid=True, **_FOOT)
    out += litter([o for o in objs if o.name in bpy.data.objects], seed, 'DR02_High', 'DR02_P_')
    return out


_FOOT = dict(foot=.45, foot_size=.55, foot_along=True, heart=.45)
PATH_HALF = 1.1        # 根腳的蕨、心形葉不放在 |x| < 1.4 m：洞口前面留給落葉（dr01_dress 用 path_half 避開路）
BACK_Y = 2.55        # 背面（心材牆後緣）大約在 y = 2.55：Socket_Back 放這裡


def dress_game(low, mod, seed):
    """遊戲植物（game_dr02.make_detail 呼叫）：兩條板根各長一次（DR02_LP_／DR02_LQ_），再加洞口和洞裡的落葉（DR02_LP_Litter0–2）。"""
    import core_plants
    cfg = getattr(core_plants.LeafBuf, 'cfg', None)
    if cfg is not None:
        cfg['fern_keep'] = 3                  # 兩條板根都長，根腳小蕨很多：蕨羽片三片留一片（和 DR03 一樣）
    try:
        return _dress_game(low, mod, seed)
    finally:
        if cfg is not None:
            cfg.pop('fern_keep', None)


def _dress_game(low, mod, seed):
    out = []
    for li, pre in ((3, 'DR02_LP_'), (4, 'DR02_LQ_')):
        c1, f1 = _line(li)
        out += mod.dress([low], c1, f1, fb, PATH_HALF, quick=True, seed=seed + 11 * li, coll_name='DR02_Game', prefix=pre, lite=True,
                         amount=VAR['plants'], avoid=True, **_FOOT)
    out += litter([low], seed, 'DR02_Game', 'DR02_LP_')
    return out


def litter(objs, seed, coll_name, prefix, n=280):
    """落葉：洞口前面一片（越靠洞口越密）、洞裡地上一些、兩條板根腳邊零星幾片；三種褐色各一個物件（遊戲圖集上各一條）。
    葉子平貼地面（略翹），不放進根裡、不疊在根上面。"""
    import core_plants
    from mathutils.bvhtree import BVHTree
    R = random.Random(seed + 101)
    V, F = [], []
    for o in objs:
        b0 = len(V)
        V.extend(o.matrix_world @ v.co for v in o.data.vertices)
        F.extend(tuple(b0 + i for i in p.vertices) for p in o.data.polygons)
    bvh = BVHTree.FromPolygons(V, F)
    coll = bpy.data.collections[coll_name]
    for o in list(coll.objects):
        if o.name.startswith(prefix + 'Litter'):
            bpy.data.objects.remove(o, do_unlink=True)
    bufs = [core_plants.LeafBuf() for _ in range(3)]

    def free(p):
        """p 在地面上、不在根裡面，正上方 0.25 m 內沒有根（洞裡例外：洞頂在 1.3 m 以上）。"""
        loc, nrm, _, d = bvh.find_nearest(p, 3.0)
        if loc is not None and ((p - loc).dot(nrm) < .02 or d < .03):
            return False
        h = bvh.ray_cast(p + Vector((0, 0, .01)), Vector((0, 0, 1)), 1.2)
        return h[0] is None or h[0].z > 1.2
    made = 0
    for i in range(n * 6):
        if made >= n:
            break
        k = R.random()
        if k < .55:            # 洞口前面：扇形，靠洞口密
            x = R.gauss(0, .65)
            y = .45 - abs(R.gauss(0, .75))
        elif k < .80:          # 洞裡
            x = R.uniform(-.85, .85)
            y = R.uniform(.45, 1.45)
        else:                  # 板根腳邊
            sg = R.choice((-1, 1))
            y = R.uniform(-1.6, 1.4)
            x = sg * (2.0 + .25 * max(0.0, -y) + R.uniform(-.15, .35))
        p = Vector((x, y, .004))
        if not free(p):
            continue
        L = R.uniform(.09, .16)
        a = R.uniform(0, 2 * math.pi)
        d = Vector((math.cos(a), math.sin(a), R.uniform(-.05, .12)))
        d, side, nrm = core_plants._frame(d)
        g = R.uniform(.8, 1.15)
        bufs[R.randrange(3)].leaf(p - d * L * .5, d, side, nrm, L, L * R.uniform(.34, .46),
                                  shape=lambda u: math.sin(math.pi * u) ** .8 * (1 - .2 * u), fold=R.uniform(.05, .3),
                                  curl=R.uniform(-.1, .4), droop=R.uniform(-.05, .05), tint=(g, g, g), nu=6, nv=4, twist=R.uniform(-.3, .3))
        made += 1
    mat = bpy.data.materials.get('D2_LitterLeaf') or core_plants._leaf_material('D2_LitterLeaf', (.10, .06, .03, 1), (.30, .19, .08, 1), (.36, .25, .12, 1), gloss=.3)
    out = []
    for j, buf in enumerate(bufs):
        if not buf.V:
            continue
        o = buf.build(f'{prefix}Litter{j}', mat)
        for c in list(o.users_collection):
            c.objects.unlink(o)
        coll.objects.link(o)
        out.append(o)
    print('litter leaves', made)
    return out


def _line(li):
    pts = [(X0 + s, y, z, r, fl) for s, y, z, r, fl in VAR['roots'][li]]

    def c1(t):
        return _along(pts, t)[0]

    def f1(t):
        d = (c1(min(1, t + .01)) - c1(max(0, t - .01))).normalized()
        side = Vector((-d.y, d.x, 0)).normalized()
        nrm = d.cross(side).normalized()
        if nrm.z < 0:
            nrm = -nrm
        return d, side, nrm
    return c1, f1


set_variant('H')
