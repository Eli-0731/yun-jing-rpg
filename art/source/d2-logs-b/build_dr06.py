# DR06 倒伏巨木（高模）：一棵老樹連根倒下，躺在地上、稍微陷進土裡。兩種長度：A 長 10 m、徑 1.4 m；B 長 16 m、徑 2 m。
#   一頭：整個根盤從地裡翻起來，立成一座泥丘（A 約 3.5 m、B 約 4.5 m 寬）：粗根從樹幹基部包過泥丘往外伸、末端斷成淺色木刺，
#         根之間夾著深褐泥土，朝外那面（原本的根底）泥裡卡著灰石頭、垂著細根鬚；根盤前面（原本樹站的地方）一圈翻起的土和淺坑。
#   另一頭：樹幹斷折，斷口一大束長長的淺色木刺、撕裂的纖維，外面一圈樹皮。
#   樹幹：深灰褐、扭轉長稜和深溝的老樹皮，幾大片樹皮剝落露出灰褐風化木；一根往上翹的長斷枝、一兩個短枝樁。
#   頂上：厚厚一層深橄欖綠苔、灰白地衣；兩側層狀菌。植物（dress）：頂上的蕨、小樹苗、苔叢、蕈，腳邊的大蕨、闊葉草、蕈、落葉。
# 樹幹沿 +X：根盤在 x ≈ 0，斷口在 x = L；正面 -Y。z = 0 是地面。原點之後由 dr_pivot.py 移到底部中心。
# 樹皮、苔、地衣沿用 D2 根與木的同一套（../d2-roots-b/dr_core.py）。參考：art/references/DR06/v001/。
# 用法（背景，不要加 --factory-startup：會關掉擴充套件、清掉它們的 Python 套件）：
#   blender -b --python build_dr06.py -- B quick <輸出資料夾> [鏡位,鏡位] [存檔.blend]
import bpy, bmesh, math, random, sys, os, importlib, re
import numpy as np
from mathutils import Vector, noise

HERE = os.path.dirname(os.path.abspath(globals().get('__file__', 'D:/yun-jing-d2-logs/art/source/d2-logs-b/build_dr06.py')))
ROOTS = os.path.join(os.path.dirname(HERE), 'd2-roots-b')
for _p in (ROOTS, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import dr_core, core_plants
importlib.reload(dr_core)
from dr_core import tube, fb, CFG, resample

# L 長度、R 樹幹半徑、RP 根盤半徑（含伸出去的斷根）
# stubs：(沿長比例, 繞軸角（0 正上，正值往 -Y）, 長 m, 枝徑/樹幹半徑, 往 +X 傾角)
# fungi：(沿長比例, 繞軸角, 片數)
VARIANTS = {
    'A': dict(name='Short', L=10.0, R=.70, RP=1.75, seed=61, nroots=21,
              stubs=((.50, .45, 1.05, .36, .70), (.77, -1.25, .65, .22, .30)),
              fungi=((.30, -1.45, 4), (.62, 1.55, 3)), bend=.18),
    'B': dict(name='Long', L=16.0, R=1.00, RP=2.25, seed=73, nroots=27,
              stubs=((.44, .50, 1.50, .34, .72), (.73, -1.20, 1.0, .21, .35), (.24, 1.45, .55, .17, .20)),
              fungi=((.20, -1.50, 5), (.50, 1.45, 4), (.66, -1.55, 4)), bend=.25),
}
VAR = VARIANTS['B']
# 苔色（線性）：參考圖的苔是亮的橄欖黃綠，比 A 批（對齊神木 GT01）亮、黃
MOSS_C = ((.046, .050, .013, 1), (.165, .160, .044, 1))


def set_variant(v):
    global VAR
    VAR = VARIANTS[v]
    VAR['id'] = v
    return VAR


def _coll(name):
    c = bpy.data.collections.get(name)
    if c:
        for o in list(c.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    else:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


def _obj(name, me, coll):
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    return o


def _sm(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


# ---------------- 材質 ----------------
def _streak(N, Lk, scale=(1.4, 24.0, 24.0), detail=8):
    """沿 X（樹幹方向）拉長的雜訊＝木纖維條紋。"""
    tc = N.new('ShaderNodeTexCoord')
    mp = N.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = scale
    Lk.new(tc.outputs['Object'], mp.inputs['Vector'])
    nz = N.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 1.0
    nz.inputs['Detail'].default_value = detail
    nz.inputs['Roughness'].default_value = .68
    Lk.new(mp.outputs[0], nz.inputs['Vector'])
    return nz


def _ramp(N, p0, p1, c0, c1):
    r = N.new('ShaderNodeValToRGB')
    e = r.color_ramp.elements
    e[0].position, e[1].position = p0, p1
    e[0].color, e[1].color = c0, c1
    return r


def wood_material():
    """斷口木刺：淺黃褐、沿纖維的條紋，縫裡暗。"""
    m = bpy.data.materials.get('DR06_Wood')
    if m:
        return m
    m = bpy.data.materials.new('DR06_Wood')
    m.use_nodes = True
    N, Lk = m.node_tree.nodes, m.node_tree.links
    b = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    nz = _streak(N, Lk)
    cr = _ramp(N, .30, .72, (.13, .095, .060, 1), (.42, .33, .22, 1))
    Lk.new(nz.outputs['Fac'], cr.inputs[0])
    nz2 = _streak(N, Lk, (.25, 3.0, 3.0), 4)              # 大片的深淺（風化、受潮）
    cr2 = _ramp(N, .35, .70, (.62, .60, .58, 1), (1.0, .97, .92, 1))
    Lk.new(nz2.outputs['Fac'], cr2.inputs[0])
    mx = N.new('ShaderNodeMixRGB')
    mx.blend_type = 'MULTIPLY'
    mx.inputs[0].default_value = 1.0
    Lk.new(cr.outputs[0], mx.inputs[1])
    Lk.new(cr2.outputs[0], mx.inputs[2])
    Lk.new(mx.outputs[0], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = .86
    bp = N.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = .7
    bp.inputs['Distance'].default_value = .012
    Lk.new(nz.outputs['Fac'], bp.inputs['Height'])
    Lk.new(bp.outputs[0], b.inputs['Normal'])
    return m


def bark_material():
    """D2 樹皮（同一套）＋剝皮處（點屬性 Peel）換成灰褐風化木。"""
    m = bpy.data.materials.get('DR06_Bark')
    if m:
        return m
    m = dr_core.bark_material('D2RootBark').copy()
    m.name = 'DR06_Bark'
    N, Lk = m.node_tree.nodes, m.node_tree.links
    b = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    # v001 第二輪（使用者要求「修一下」）：照參考圖，樹皮亮一點、灰褐；苔是亮的橄欖黃綠；灰白地衣斑多一點、亮一點。
    # 只改 DR06 自己這份副本，A 批共用的 D2RootBark 不動。
    for n in N:
        if n.type == 'HUE_SAT':
            n.inputs['Value'].default_value = 1.80
            n.inputs['Saturation'].default_value = .55
        elif n.type == 'VALTORGB':
            e = n.color_ramp.elements
            if abs(e[0].color[0] - .027) < 1e-3 and abs(e[1].color[0] - .092) < 1e-3:       # 苔色：深淺拉開，不是一片草皮
                e[0].color, e[1].color = MOSS_C
                e[0].position, e[1].position = .25, .78
            elif abs(e[0].position - .60) < 1e-3 and abs(e[1].position - .65) < 1e-3:      # 地衣斑的範圍
                e[0].position, e[1].position = .600, .640          # 邊緣軟一點：半透的一層，不是貼上去的白漆
            elif abs(e[0].position - .40) < 1e-3 and abs(e[1].position - .62) < 1e-3:      # 苔遮罩：邊緣收得利一點
                e[0].position, e[1].position = .36, .54
        elif n.type == 'TEX_NOISE' and abs(n.inputs['Scale'].default_value - 5.0) < 1e-3:
            n.inputs['Scale'].default_value = 3.6               # 地衣斑：參考圖是一朵一朵 10–30 cm 的灰綠白斑，不是小點
            n.inputs['Roughness'].default_value = .55
        elif n.type == 'MIX_RGB' and n.blend_type == 'MIX' and abs(n.inputs[2].default_value[0] - .36) < 1e-3:
            n.inputs[2].default_value = (.31, .35, .32, 1)              # 地衣：灰綠（太亮在深色根上像點上去的白點）
    at = N.new('ShaderNodeAttribute')
    at.attribute_name = 'Peel'
    pr = _ramp(N, .25, .75, (0, 0, 0, 1), (1, 1, 1, 1))
    Lk.new(at.outputs['Fac'], pr.inputs[0])
    nz = _streak(N, Lk)
    cr0 = _ramp(N, .30, .72, (.13, .10, .068, 1), (.36, .29, .205, 1))          # 風化木：參考圖是淺灰褐
    Lk.new(nz.outputs['Fac'], cr0.inputs[0])
    # 風化木上沿纖維的裂縫（拉長的 Voronoi 邊）＋大片受潮的深淺：不然剝皮處是一塊平平的淺色
    tcv = N.new('ShaderNodeTexCoord')
    mpv = N.new('ShaderNodeMapping')
    mpv.inputs['Scale'].default_value = (.7, 9.0, 9.0)
    Lk.new(tcv.outputs['Object'], mpv.inputs['Vector'])
    vo = N.new('ShaderNodeTexVoronoi')
    vo.feature = 'DISTANCE_TO_EDGE'
    vo.inputs['Scale'].default_value = 1.0
    Lk.new(mpv.outputs[0], vo.inputs['Vector'])
    crk = _ramp(N, .0, .06, (.30, .27, .24, 1), (1, 1, 1, 1))
    Lk.new(vo.outputs['Distance'], crk.inputs[0])
    nz2 = _streak(N, Lk, (.35, 2.5, 2.5), 4)
    blot = _ramp(N, .35, .70, (.76, .75, .73, 1), (1.0, .98, .95, 1))
    Lk.new(nz2.outputs['Fac'], blot.inputs[0])
    m1 = N.new('ShaderNodeMixRGB')
    m1.blend_type = 'MULTIPLY'
    m1.inputs[0].default_value = 1.0
    Lk.new(cr0.outputs[0], m1.inputs[1])
    Lk.new(crk.outputs[0], m1.inputs[2])
    cr = N.new('ShaderNodeMixRGB')
    cr.blend_type = 'MULTIPLY'
    cr.inputs[0].default_value = 1.0
    Lk.new(m1.outputs[0], cr.inputs[1])
    Lk.new(blot.outputs[0], cr.inputs[2])
    hgt = N.new('ShaderNodeMath')
    hgt.operation = 'ADD'
    Lk.new(nz.outputs['Fac'], hgt.inputs[0])
    crh = N.new('ShaderNodeMapRange')
    crh.inputs['From Max'].default_value = .06
    crh.inputs['To Min'].default_value = -.8
    crh.inputs['To Max'].default_value = 0.0
    Lk.new(vo.outputs['Distance'], crh.inputs['Value'])
    Lk.new(crh.outputs[0], hgt.inputs[1])
    for inp, kind in (('Base Color', 'RGBA'), ('Normal', 'VECTOR'), ('Roughness', 'FLOAT')):
        lk = next(l for l in b.inputs[inp].links)
        src = lk.from_socket
        Lk.remove(lk)
        mx = N.new('ShaderNodeMix')
        mx.data_type = kind
        A, B_, R_ = {'RGBA': (6, 7, 2), 'VECTOR': (4, 5, 1), 'FLOAT': (2, 3, 0)}[kind]
        Lk.new(pr.outputs[0], mx.inputs[0])
        Lk.new(src, mx.inputs[A])
        if kind == 'RGBA':
            Lk.new(cr.outputs[0], mx.inputs[B_])
        elif kind == 'VECTOR':
            bp = N.new('ShaderNodeBump')
            bp.inputs['Strength'].default_value = .8
            bp.inputs['Distance'].default_value = .012
            Lk.new(hgt.outputs[0], bp.inputs['Height'])
            Lk.new(bp.outputs[0], mx.inputs[B_])
        else:
            mx.inputs[B_].default_value = .85
        Lk.new(mx.outputs[R_], b.inputs[inp])
    return m


def mud_material():
    """根盤上的泥：深褐、濕、團塊；點屬性 MudMoss：原本的地面（根盤朝樹幹那面、上緣）長苔。"""
    m = bpy.data.materials.get('DR06_Mud')
    if m:
        return m
    m = bpy.data.materials.new('DR06_Mud')
    m.use_nodes = True
    N, Lk = m.node_tree.nodes, m.node_tree.links
    b = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    tc = N.new('ShaderNodeTexCoord')
    nz = N.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 3.0
    nz.inputs['Detail'].default_value = 10
    nz.inputs['Roughness'].default_value = .62
    Lk.new(tc.outputs['Object'], nz.inputs['Vector'])
    vo = N.new('ShaderNodeTexVoronoi')            # 土團、碎石粒
    vo.inputs['Scale'].default_value = 14
    Lk.new(tc.outputs['Object'], vo.inputs['Vector'])
    cr0 = _ramp(N, .30, .72, (.040, .027, .016, 1), (.125, .080, .045, 1))      # 中褐土色（參考圖朝外那面整片褐土）     # 參考圖的泥是中褐色，不是黑
    Lk.new(nz.outputs['Fac'], cr0.inputs[0])
    vc_ = _ramp(N, .0, .10, (.55, .50, .46, 1), (1, 1, 1, 1))                     # 土團之間的縫暗一點
    Lk.new(vo.outputs['Distance'], vc_.inputs[0])
    cr = N.new('ShaderNodeMixRGB')
    cr.blend_type = 'MULTIPLY'
    cr.inputs[0].default_value = 1.0
    Lk.new(cr0.outputs[0], cr.inputs[1])
    Lk.new(vc_.outputs[0], cr.inputs[2])
    at = N.new('ShaderNodeAttribute')
    at.attribute_name = 'MudMoss'
    mr = _ramp(N, .35, .65, (0, 0, 0, 1), (1, 1, 1, 1))
    Lk.new(at.outputs['Fac'], mr.inputs[0])
    nm = N.new('ShaderNodeTexNoise')
    nm.inputs['Scale'].default_value = 7
    nm.inputs['Detail'].default_value = 6
    Lk.new(tc.outputs['Object'], nm.inputs['Vector'])
    mc0 = _ramp(N, .25, .78, *MOSS_C)       # 和樹皮上的苔同色
    Lk.new(nm.outputs['Fac'], mc0.inputs[0])
    mvo = N.new('ShaderNodeTexVoronoi')            # 苔的小團粒（2–3 cm），團粒之間的縫暗一點：不然是一塊光滑的黃綠
    mvo.inputs['Scale'].default_value = 55
    Lk.new(tc.outputs['Object'], mvo.inputs['Vector'])
    mdr = _ramp(N, .0, .45, (1, 1, 1, 1), (.45, .5, .4, 1))
    Lk.new(mvo.outputs['Distance'], mdr.inputs[0])
    mc = N.new('ShaderNodeMixRGB')
    mc.blend_type = 'MULTIPLY'
    mc.inputs[0].default_value = .7
    Lk.new(mc0.outputs[0], mc.inputs[1])
    Lk.new(mdr.outputs[0], mc.inputs[2])
    mx = N.new('ShaderNodeMixRGB')
    Lk.new(mr.outputs[0], mx.inputs[0])
    Lk.new(cr.outputs[0], mx.inputs[1])
    Lk.new(mc.outputs[0], mx.inputs[2])
    Lk.new(mx.outputs[0], b.inputs['Base Color'])
    rg = _ramp(N, .2, .8, (.45, .45, .45, 1), (.85, .85, .85, 1))
    Lk.new(nz.outputs['Fac'], rg.inputs[0])
    Lk.new(rg.outputs[0], b.inputs['Roughness'])
    hm = N.new('ShaderNodeMath')
    hm.operation = 'ADD'
    Lk.new(nz.outputs['Fac'], hm.inputs[0])
    vm = N.new('ShaderNodeMath')
    vm.operation = 'MULTIPLY'
    vm.inputs[1].default_value = -.35
    Lk.new(vo.outputs['Distance'], vm.inputs[0])
    Lk.new(vm.outputs[0], hm.inputs[1])
    bp = N.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = .8
    bp.inputs['Distance'].default_value = .03
    Lk.new(hm.outputs[0], bp.inputs['Height'])
    Lk.new(bp.outputs[0], b.inputs['Normal'])
    return m


def stone_material():
    m = bpy.data.materials.get('DR06_Stone')
    if m:
        return m
    m = bpy.data.materials.new('DR06_Stone')
    m.use_nodes = True
    N, Lk = m.node_tree.nodes, m.node_tree.links
    b = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    tc = N.new('ShaderNodeTexCoord')
    nz = N.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 6
    nz.inputs['Detail'].default_value = 10
    Lk.new(tc.outputs['Object'], nz.inputs['Vector'])
    cr = _ramp(N, .3, .75, (.060, .056, .050, 1), (.150, .142, .128, 1))       # 參考圖：中灰的石頭
    Lk.new(nz.outputs['Fac'], cr.inputs[0])
    Lk.new(cr.outputs[0], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = .78
    bp = N.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = .5
    Lk.new(nz.outputs['Fac'], bp.inputs['Height'])
    Lk.new(bp.outputs[0], b.inputs['Normal'])
    return m


# ---------------- 樹幹 ----------------
def trunk_z(V, x):
    """樹幹中心高：基部稍微抬起（根盤撐著），往斷口那頭躺平、陷進土裡約 0.14 R。"""
    L, R = V['L'], V['R']
    r = trunk_r(V, x)
    rest = r * .96 - .14 * R
    u = _sm(max(0.0, x) / (.32 * L))
    return (R * 1.30) * (1 - u) + rest * u


def trunk_r(V, x):
    L, R = V['L'], V['R']
    t = max(0.0, x) / L
    return R * (1 + .38 * math.exp(-max(0.0, x) / (.04 * L + .45))) * (1 - .15 * t)


def trunk_moss(p, n):
    """樹幹的苔：頂上一整層厚苔（比 A 批多），另外沿樹幹某幾段往兩側垂下來一舌一舌（參考圖苔從頂上流下側面）。"""
    tongue = max(0.0, fb((p.x * .9, 3.1 if p.y > 0 else 7.3, 0), 1.0, 3)) * 1.6
    side = max(0.0, min(1.0, (n.z + .45) / .5))
    return .40 * max(0.0, n.z) + .14 + .30 * tongue * side


def trunk_pts(V):
    L, R = V['L'], V['R']
    pts = []
    xs = [-.6, -.2, .25, .7, 1.3, 2.1, 3.0] + list(np.linspace(4.0, L, max(4, int(L / 1.6))))
    for x in xs:
        t = max(0.0, x) / L
        y = V['bend'] * R * math.sin(t * 2.6 + V['seed'] * .37) * t
        pts.append((x, y, trunk_z(V, x), trunk_r(V, x), .96))
    return pts


def ring_info(ob, pts):
    rings, _ = resample(pts, CFG['step'])
    me = ob.data
    nr = len(rings)
    nu = len(me.vertices) // nr
    assert nu * nr == len(me.vertices), (nu, nr, len(me.vertices))
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get('co', co)
    return rings, nu, co.reshape(-1, 3)


def vert_moss(me):
    """Mask 的 R（苔）平均到點上。"""
    ca = me.color_attributes['Mask']
    n = len(me.loops)
    col = np.empty(n * 4, np.float32)
    ca.data.foreach_get('color', col)
    col = col.reshape(-1, 4)
    vi = np.empty(n, np.int32)
    me.loops.foreach_get('vertex_index', vi)
    acc = np.zeros(len(me.vertices))
    cnt = np.zeros(len(me.vertices))
    np.add.at(acc, vi, col[:, 0])
    np.add.at(cnt, vi, 1)
    return acc / np.maximum(cnt, 1)


def peel(ob, pts, seed, s0, s1):
    """樹皮剝落：側面幾大片沿樹幹拉長的，表面壓回平滑的木頭圓柱（半徑 0.93 r），點屬性 Peel = 1。"""
    rings, nu, co = ring_info(ob, pts)
    mo = vert_moss(ob.data)
    w = np.zeros(len(co))
    for k, (c, r, fl, s) in enumerate(rings):
        if not (s0 < s < s1):
            continue
        cc = np.array(c)
        for i in range(nu):
            j = k * nu + i
            d = co[j] - cc
            rr = np.linalg.norm(d)
            if rr < 1e-6:
                continue
            dn = d / rr
            if dn[2] > .55:            # 頂上是苔，不剝
                continue
            pn = fb((co[j][0] * .11 + seed, co[j][1] * .55, co[j][2] * .55), 1.0, 3) + .22 * fb(co[j] * 1.6, 1.0, 2)
            ww = _sm((pn - .37) / .07) * (1 - _sm((mo[j] - .05) / .2))
            if ww <= 0:
                continue
            w[j] = ww
            co[j] = cc + dn * (rr * (1 - ww) + r * .925 * ww)
    me = ob.data
    me.vertices.foreach_set('co', co.ravel())
    at = me.attributes.new('Peel', 'FLOAT', 'POINT')
    at.data.foreach_set('value', w.astype(np.float32))
    me.update()
    print('peel verts', int((w > .5).sum()), 'of', len(w))


def snap_cap(name, ob, pts, R, seed, coll, reach=1.0, nspk=11, sub=4, shards=4, top=1.0, splay=.22, shard_w=1.0, slen=(.35, 1.25)):
    """斷口：用管子最後一圈的頂點當外緣，往內一圈樹皮、裡面是參差的木頭（往 +軸 伸出木刺），外加一束長木刺。"""
    rings, nu, co = ring_info(ob, pts)
    Rn = random.Random(seed)
    rim0 = co[-nu:]
    c = np.array(rings[-1][0])
    a = np.array(rings[-1][0] - rings[max(0, len(rings) - 4)][0])
    a /= np.linalg.norm(a)
    z = np.array((0, 0, 1.0))
    upv = z - a * z.dot(a)
    if np.linalg.norm(upv) < 1e-3:
        upv = np.array((0, 1.0, 0))
    upv /= np.linalg.norm(upv)
    sdv = np.cross(a, upv)
    M = nu * sub
    rim = np.array([rim0[i // sub] * (1 - (i % sub) / sub) + rim0[(i // sub + 1) % nu] * ((i % sub) / sub) for i in range(M)])
    rel = rim - c
    ax = rel @ a
    e = rel - np.outer(ax, a)
    th = np.arctan2(e @ upv, e @ sdv)              # π/2 = 正上方
    spk = []
    for k in range(nspk):
        tk = Rn.gauss(math.pi / 2, 1.2) if Rn.random() < .6 else Rn.uniform(-math.pi, math.pi)
        lk = reach * R * Rn.uniform(.12, .70) * (1 + .9 * max(0.0, math.sin(tk))) * top
        spk.append((tk, Rn.uniform(.05, .17), Rn.uniform(.30, .88), lk))
    lev = [1.0, .95, .90, .83, .75, .66, .57, .48, .39, .30, .21, .12, .05]

    def h(t, rho):
        if rho >= .95:
            return 0.0
        v = reach * R * (.06 + .14 * max(0.0, math.sin(t)) * top)
        for tk, wk, rk, lk in spk:
            dt = abs((t - tk + math.pi) % (2 * math.pi) - math.pi)
            if dt < wk:
                v += lk * (1 - dt / wk) ** 1.4 * max(0.0, 1 - abs(rho - rk) / .40) ** 1.2
        v += .06 * R * reach * fb((math.cos(t) * 9, math.sin(t) * 9, rho * 4 + seed), 1.0, 3)
        v += .03 * R * fb((math.cos(t) * 34, math.sin(t) * 34, rho * 9), 1.0, 2)
        v -= .05 * R * (1 - rho) ** 2
        return v * _sm((.95 - rho) / .10)

    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UV')
    col = bm.loops.layers.color.new('Mask')
    grid = []
    for rho in lev:
        row = []
        for j in range(M):
            if rho == 1.0:
                p = rim[j]
            elif rho == .95:
                p = c + e[j] * .935 + a * (ax[j] - .015 * R)
            else:
                p = c + e[j] * rho + a * (ax[j] * rho + h(th[j], rho))
            row.append(bm.verts.new(p))
        grid.append(row)
    cv = bm.verts.new(c + a * h(math.pi / 2, .0))
    for li in range(len(lev) - 1):
        for j in range(M):
            j2 = (j + 1) % M
            f = bm.faces.new((grid[li][j], grid[li][j2], grid[li + 1][j2], grid[li + 1][j]))
            f.material_index = 0 if li == 0 else 1
    for j in range(M):
        f = bm.faces.new((grid[-1][j], grid[-1][(j + 1) % M], cv))
        f.material_index = 1
    bm.normal_update()
    f0 = next(f for f in bm.faces if len(f.verts) == 3)
    if f0.normal.dot(Vector(a)) < 0:                # 斷面朝 +a
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    # 一束長木刺：從斷面各處往外伸，上半邊多、長；扁、扭、尖，稍微往外散
    # Shard（面）／ShardU（點，0 根部 → 1 尖端）：遊戲模型的木刺太細烘不準，改用圖集最下面一條的淺木色漸層
    shl = bm.faces.layers.int.new('Shard')
    sul = bm.verts.layers.float.new('ShardU')
    for s_ in range(shards):
        t = Rn.gauss(math.pi / 2, .95) if Rn.random() < .65 else Rn.uniform(-math.pi, math.pi)
        rho = Rn.uniform(.25, .92)
        dirr = sdv * math.cos(t) + upv * math.sin(t)
        base = c + dirr * rho * R * .93 + a * h(t, rho) * .45
        ln = min(reach * R * Rn.uniform(*slen) * (1 + .5 * max(0.0, math.sin(t))) * top, 1.7 * R * reach)
        wd = R * Rn.uniform(.03, .075) * shard_w
        tk = R * Rn.uniform(.012, .03)
        dv = a + dirr * Rn.uniform(.0, splay) * rho + upv * Rn.uniform(-.04, .08)
        dv /= np.linalg.norm(dv)
        tan1 = np.cross(dv, dirr)
        tan1 /= np.linalg.norm(tan1)
        nrm2 = np.cross(tan1, dv)
        sag = Rn.uniform(-.05, .10)
        rows = []
        for q in range(7):
            u = q / 6
            cc = base + dv * ln * u - nrm2 * (sag * ln * u * u)
            ww, tt = wd * (1 - u) ** .7, tk * (1 - u) ** .6 + .002
            tw = Rn.uniform(.2, .8) * u
            t1 = tan1 * math.cos(tw) + nrm2 * math.sin(tw)
            t2 = -tan1 * math.sin(tw) + nrm2 * math.cos(tw)
            rows.append([bm.verts.new(cc + t1 * ww * sx + t2 * tt * sy) for sx, sy in ((1, 0), (0, 1), (-1, 0), (0, -1))])
            for vv in rows[-1]:
                vv[sul] = u
        for q in range(6):
            for k in range(4):
                f = bm.faces.new((rows[q][k], rows[q][(k + 1) % 4], rows[q + 1][(k + 1) % 4], rows[q + 1][k]))
                f.material_index = 1
                f[shl] = 1
    for f in bm.faces:
        f.smooth = f.material_index == 0
        for lp in f.loops:
            p = lp.vert.co
            lp[uvl].uv = (float(np.dot(p, sdv)) / dr_core.TILE, float(np.dot(p, upv)) / dr_core.TILE)
            lp[col] = (0.0, .45, .3, 1.0)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(bark_material())
    me.materials.append(wood_material())
    return _obj(name, me, coll)


# ---------------- 根盤 ----------------
def plate_geom(V):
    RP = V['RP']
    k = RP / 2.25
    return dict(k=k, xp=-.20 * k, zc=RP * .78, Re=RP * .86, Tm=.56 * k, Tp=.72 * k)      # 根盤是一片厚圓盤（厚度約半徑的四成），不是一顆蛋


def dome_d(V, x):
    """泥丘在 x 處（沿 X 切）的半徑：朝 +X 那面是圓頂，朝 -X 那面（原本的根底）平一點。"""
    g = plate_geom(V)
    q = (g['xp'] - x) / g['Tm'] if x <= g['xp'] else (x - g['xp']) / g['Tp']
    return g['Re'] * math.sqrt(max(0.0, 1 - min(1.0, q) ** 2))


def face_prof(q):
    """朝外那面（原本的根底）的剖面：q 是離中心的比例（1＝外緣）。中間凹進去、外圈一道唇，再繞回邊緣。"""
    if q < .8:
        return .45 + .55 * _sm(q / .8)
    return math.sqrt(max(0.0, 1 - ((q - .8) / .2) ** 2))


def mud_pt(V, d, seed):
    """單位方向 d → 泥丘表面上的點（和網格解析度無關：石頭、根鬚、低模都用同一個函式）。"""
    g = plate_geom(V)
    d = Vector(d).normalized()
    lob = 1 + .12 * fb(d * 1.7 + Vector((seed, 0, 0)), 1.0, 3) + .06 * fb(d * 5.0, 1.0, 2)
    Re = g['Re'] * lob
    if d.x < 0:
        xx = -g['Tm'] * face_prof(math.sqrt(max(0.0, 1 - d.x * d.x))) * (1 + .25 * fb(d * 2.6 + Vector((0, seed, 0)), 1.0, 3))
    else:
        xx = g['Tp'] * d.x * (1 + .15 * fb(d * 2.6, 1.0, 3))
    p = Vector((g['xp'] + xx, d.y * Re, g['zc'] + d.z * Re))
    p += d * (.06 * g['k'] * fb(p * 3.0, 1.0, 3) + .030 * g['k'] * fb(p * 8.0, 1.0, 2) + .012 * g['k'] * fb(p * 19.0, 1.0, 2))
    if p.z < -.40:
        p.z = -.40 + (p.z + .40) * .1
    return p


def face_x(V, y, z, seed):
    """朝外那面（-X）在 (y, z) 處泥面實際的 x：反求 mud_pt 的方向（含泥面起伏），和網格解析度無關，高模低模一樣。"""
    g = plate_geom(V)
    d = Vector((-.8, y / g['Re'], (z - g['zc']) / g['Re']))
    for _ in range(8):
        q = Vector((0, d.y, d.z))
        if q.length > .985:
            q *= .985 / q.length
        d = Vector((-math.sqrt(max(.0003, 1 - q.length_squared)), q.y, q.z))
        p = mud_pt(V, d, seed)
        d.y += (y - p.y) / g['Re']
        d.z += (z - p.z) / g['Re']
    q = Vector((0, d.y, d.z))
    if q.length > .985:
        q *= .985 / q.length
    return mud_pt(V, Vector((-math.sqrt(max(.0003, 1 - q.length_squared)), q.y, q.z)), seed).x


def mud_nrm(V, d, seed, e=.02):
    d = Vector(d).normalized()
    a = d.cross(Vector((0, 0, 1)) if abs(d.z) < .9 else Vector((0, 1, 0))).normalized()
    b = d.cross(a).normalized()
    n = (mud_pt(V, d + a * e, seed) - mud_pt(V, d - a * e, seed)).cross(mud_pt(V, d + b * e, seed) - mud_pt(V, d - b * e, seed)).normalized()
    g = plate_geom(V)
    if n.dot(mud_pt(V, d, seed) - Vector((g['xp'], 0, g['zc']))) < 0:
        n = -n
    return n


def face_dir(R, xlo, xhi):
    """朝外那面（-X）上隨機一個方向：d.x 在 (-xhi, -xlo) 之間。"""
    dx = -R.uniform(xlo, xhi)
    a = R.uniform(0, 2 * math.pi)
    q = math.sqrt(1 - dx * dx)
    return Vector((dx, q * math.cos(a), q * math.sin(a)))


def mud_plate(V, coll, seed, res=(80, 48)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=res[0], v_segments=res[1], radius=1.0)
    mm = []
    for v in bm.verts:
        d = v.co.copy()
        p = mud_pt(V, d, seed)
        v.co = p
        m_ = max(0.0, d.x) * 1.4 + max(0.0, d.z - .45) * 1.8 + .45 * fb(p * 2.0, 1.0, 3) - .45       # 根盤頂上、朝樹幹那面長苔（參考圖那裡整片苔＋根）
        m_ = max(0.0, min(1.0, m_))
        mm.append(m_)
        if res[0] > 60 and d.x < -.05:          # 高模：朝外那面（原本的根底）是一塊塊土團、碎土，不是光滑的泥
            v.co = v.co + d * (.045 * plate_geom(V)['k'] * (abs(fb(p * 4.5, 1.0, 3)) * 1.6 - .3 + .5 * fb(p * 13.0, 1.0, 2)) * min(1.0, -d.x * 3))
        if res[0] > 60 and m_ > 0:              # 高模：苔的地方鼓成一團一團的苔墊（10–20 cm 的團塊），烘進法線，不是一塊光滑的漆
            v.co = p + d * (m_ * .035 * (.5 + .9 * abs(fb(p * 9.0, 1.0, 3)) + .4 * fb(p * 22.0, 1.0, 2)))
    me = bpy.data.meshes.new('DR06_Mud')
    bm.to_mesh(me)
    bm.free()
    at = me.attributes.new('MudMoss', 'FLOAT', 'POINT')
    at.data.foreach_set('value', np.array(mm, np.float32))
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mud_material())
    return _obj('Mud', me, coll)


def stones(V, coll, R, n, seed, sub=3):
    g = plate_geom(V)
    out_bm = bmesh.new()
    for i in range(n):
        for _ in range(50):
            d = face_dir(R, .5, .95)
            P = mud_pt(V, d, seed)
            if P.z > .15:
                break
        N = mud_nrm(V, d, seed)
        s = g['k'] * R.uniform(.10, .30)
        b2 = bmesh.new()
        bmesh.ops.create_icosphere(b2, subdivisions=sub, radius=1.0)
        sc = Vector((R.uniform(.7, 1.0), R.uniform(.8, 1.2), R.uniform(.55, .85)))
        off = Vector((R.uniform(-9, 9), R.uniform(-9, 9), R.uniform(-9, 9)))
        for q in b2.verts:
            d2 = q.co.copy()
            rr = 1 + .22 * fb(d2 * 1.3 + off, 1.0, 2) + .05 * fb(d2 * 5 + off, 1.0, 2)
            pp = Vector((d2.x * sc.x, d2.y * sc.y, d2.z * sc.z)) * rr
            for pl in (Vector((.6, .3, .74)), Vector((-.5, .7, -.5))):       # 幾個切面：石頭不是圓球
                pl.normalize()
                dd = pp.dot(pl)
                if dd > .62:
                    pp -= pl * (dd - .62) * .85
            q.co = P - N * (.40 * s) + pp * s
        me2 = bpy.data.meshes.new('tmp')
        b2.to_mesh(me2)
        b2.free()
        out_bm.from_mesh(me2)
        bpy.data.meshes.remove(me2)
    me3 = bpy.data.meshes.new('DR06_Stones')
    out_bm.to_mesh(me3)
    out_bm.free()
    for p in me3.polygons:
        p.use_smooth = True
    me3.materials.append(stone_material())
    return _obj('Stones', me3, coll)


def pit(V, coll, R, nr=16, na=72):
    """根盤前面的淺坑：地形沒辦法往下挖，所以做成「一圈翻起來的土＋中間濕黑的低處」，外緣沉到地面下。"""
    g = plate_geom(V)
    RP = V['RP']
    cx, ax_, ay = g['xp'] - g['Tm'] - RP * .42, RP * .52, RP * .82
    bm = bmesh.new()
    rows = []
    for i in range(nr + 1):
        rho = 1.3 * i / nr
        row = []
        for j in range(na):
            t = 2 * math.pi * j / na
            wob = 1 + .10 * fb((math.cos(t) * 1.5, math.sin(t) * 1.5, 7.7), 1.0, 2)
            x, y = cx + math.cos(t) * ax_ * rho * wob, math.sin(t) * ay * rho * wob
            near = max(0.0, 1 - abs(x - g['xp']) / RP)                    # 靠根盤那邊的土翻得高
            rim = (.20 + .30 * near) * g['k'] * math.exp(-((rho - .95) / .17) ** 2) * (1 + .7 * fb((x * 1.3, y * 1.3, 3.3), 1.0, 3))
            z = .012 + rim + .035 * fb((x * 2.5, y * 2.5, 1.1), 1.0, 3) - .12 * _sm((rho - 1.08) / .2)
            row.append(bm.verts.new((x, y, z)))
        rows.append(row)
    cv = bm.verts.new((cx, 0, .012))
    for i in range(nr):
        for j in range(na):
            j2 = (j + 1) % na
            bm.faces.new((rows[i][j], rows[i][j2], rows[i + 1][j2], rows[i + 1][j]))
    for j in range(na):
        bm.faces.new((cv, rows[0][(j + 1) % na], rows[0][j]))
    bm.normal_update()
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
        f.smooth = True
    me = bpy.data.meshes.new('DR06_Pit')
    bm.to_mesh(me)
    bm.free()
    mm = []
    for v in me.vertices:
        rho = math.hypot((v.co.x - cx) / ax_, v.co.y / ay)
        mm.append(max(0.0, min(1.0, (rho - 1.05) * 3 + .4 * fb(v.co * 2, 1.0, 2))))
    at = me.attributes.new('MudMoss', 'FLOAT', 'POINT')
    at.data.foreach_set('value', np.array(mm, np.float32))
    me.materials.append(mud_material())
    return _obj('Pit', me, coll)


def twine(pts, R, rc, period):
    """一條細根沿著 pts 那條根螺旋纏繞（每 period 公尺繞一圈），從粗根中段開始、末段離開。回傳 tube 用的點。"""
    rings, tot = resample(pts, .08)
    if tot < period * .8:
        return None
    s0, s1 = tot * R.uniform(.05, .25), tot * R.uniform(.70, .92)
    th0 = R.uniform(0, 2 * math.pi)
    sg = R.choice((-1, 1))
    out = []
    for k, (c, r, fl, s) in enumerate(rings):
        if not (s0 <= s <= s1):
            continue
        a = (rings[min(k + 1, len(rings) - 1)][0] - rings[max(k - 1, 0)][0]).normalized()
        p1 = a.cross(Vector((0, 0, 1)))
        if p1.length < 1e-3:
            p1 = a.cross(Vector((0, 1, 0)))
        p1.normalize()
        p2 = a.cross(p1).normalized()
        th = th0 + sg * 2 * math.pi * (s - s0) / period
        f = (s - s0) / max(s1 - s0, 1e-3)
        rr = rc * (1 - .5 * f)
        off = (r + rr * .7) * (1 + .5 * _sm((f - .8) / .2))          # 最後一段鬆開、離開粗根
        q = c + (p1 * math.cos(th) + p2 * math.sin(th)) * off
        out.append((q.x, q.y, q.z, rr, 1.0))
    out = out[::2]
    if len(out) < 4 or min(p[2] for p in out) < -.1:
        return None
    return out


def plate_roots(V, coll, R, mat, objs):
    """根盤的粗根：從樹幹基部沿樹幹表面出來，包過泥丘的圓頂，越過邊緣往外、往後（-X）伸出去，末端斷成木刺。
    下面那一圈（埋在土裡）不做；另外幾條貼地的根從泥丘腳往兩側爬、鑽進土裡。一半的粗根分一條副根。"""
    g = plate_geom(V)
    Rt, k_ = V['R'], g['k']
    n = V['nroots']
    caps = []
    tz = lambda x: Vector((x, 0, trunk_z(V, x)))
    for k in range(n):
        ph = -.35 * math.pi + 1.70 * math.pi * k / (n - 1) + R.uniform(-.13, .13)       # 右下 → 上 → 左下（間距不等，不會像梳過的一排）
        dr = Vector((0, math.cos(ph), math.sin(ph)))
        pr = Vector((0, -math.sin(ph), math.cos(ph)))
        r0 = Rt * (R.uniform(.20, .36) if k % 2 == 0 else .07 + .16 * R.random() ** 1.6)
        sw = (R.uniform(-.40, .40), R.uniform(-.55, .55))          # 兩個控制點往旁邊擺：相鄰的根會交叉、壓在彼此上面
        spike = k % 3 != 2 and math.sin(ph) > -.25             # 兩條裡一條斷刺朝外伸（參考圖根盤一圈放射狀的斷根），其餘往後捲過邊緣、貼在朝外那面的唇上
        tipd = g['Re'] * (R.uniform(1.15, 1.55) * (1 - .24 * math.cos(ph) ** 2) if spike else R.uniform(.82, .98))      # 朝兩側水平伸的斷根短一點：根盤寬度守在工作包範圍
        lift = (R.uniform(-.10, .12) + .12 * max(0.0, math.sin(ph)) * g['k']) if spike else 0.0          # 頂上的斷根不要直直翹上天（看起來假）
        cz = Vector((0, 0, g['zc']))
        x2 = g['xp'] + .50 * g['Tp']
        x3 = g['xp'] + .05
        x4 = g['xp'] - g['Tm'] * R.uniform(.0, .45) - .10 - .55 * k_ * max(0.0, math.sin(ph)) ** 2 if spike else g['xp'] - g['Tm'] * 1.0 - .30 * r0          # 頂上的斷根往外（-X）斜，不要一根根直立
        P = [
            (tz(1.5 * k_) + dr * trunk_r(V, 1.5 * k_) * .50, r0),
            (tz(.55 * k_) + dr * trunk_r(V, .55 * k_) * 1.0, r0 * .95),
            (Vector((x2, 0, 0)) + cz + dr * (dome_d(V, x2) + .12 * r0), r0 * .80),
            (Vector((x3 if spike else g['xp'] - .35 * g['Tm'], 0, 0)) + cz + dr * (g['Re'] * (1.0 if spike else 1.04) + .15 * r0 + .25 * abs(sw[0])) + pr * sw[0] * g['k'], r0 * .62),
            (Vector((x4, 0, 0)) + cz + dr * tipd + pr * sw[1] * g['k'] + Vector((0, 0, lift)), r0 * (.40 if spike else .50)),          # 斷根末端收細（粗的平頭會像一排木樁），淺色木刺靠斷口那束長刺
        ]
        if not spike:
            # 捲過邊緣後沿著朝外那面往中心收（原本的根底：根從中心放射出去），末端鑽進泥裡
            dc = g['Re'] * R.uniform(.22, .40)
            P.append((Vector((g['xp'] - g['Tm'] * face_prof(dc / g['Re']) + .25 * r0 * .3, 0, 0)) + cz + dr * dc + pr * .2 * math.sin(k), r0 * .30))
        if min(p.z for p, _ in P[2:]) < -.2:
            continue
        pts = [(p.x, p.y, p.z, r, 1.0) for p, r in P]
        o = tube(f'PlateRoot{k:02d}', pts, V['seed'] + k, rib=.20, twist=.10, collection=coll, moss_bias=-.05, cap_end=not spike)
        o.data.materials.append(mat)
        objs.append(o)
        if r0 > .18 * Rt and R.random() < .4:          # 細根繞著粗根纏上去
            tw = twine(pts[1:], R, r0 * R.uniform(.18, .26), R.uniform(.9, 1.5) * k_)
            if tw:
                o3 = tube(f'PlateRoot{k:02d}t', tw, V['seed'] + 90 + k, rib=.12, twist=.06, collection=coll, moss_bias=-.15, cap_end=True)
                o3.data.materials.append(mat)
                objs.append(o3)
        if spike:
            caps.append((o, pts))
        if R.random() < .75:
            sg = R.choice((-1, 1))
            q0 = P[2][0] * .5 + P[3][0] * .5
            dr2 = (dr + pr * sg * R.uniform(.45, .8)).normalized()
            r1 = r0 * .48
            q1 = Vector((x3 - .05, 0, 0)) + cz + dr2 * (g['Re'] * 1.0 + .3 * r1)
            if spike:
                q2 = Vector((x4 + .1, 0, 0)) + cz + dr2 * g['Re'] * R.uniform(1.12, 1.30) + Vector((0, 0, R.uniform(-.1, .2)))
                seq = ((q0, r1), (q1, r1 * .8), (q2, r1 * .40))
            else:              # 副根也捲過邊緣、貼著朝外那面往中心收
                q2 = Vector((g['xp'] - g['Tm'] * 1.0 - .3 * r1, 0, 0)) + cz + dr2 * g['Re'] * .92
                dc = g['Re'] * R.uniform(.40, .65)
                q3 = Vector((g['xp'] - g['Tm'] * face_prof(dc / g['Re']) + .1 * r1, 0, 0)) + cz + dr2 * dc
                seq = ((q0, r1), (q1, r1 * .8), (q2, r1 * .6), (q3, r1 * .35))
            pts2 = [(q.x, q.y, q.z, r, 1.0) for q, r in seq]
            if min(p[2] for p in pts2) > -.2:
                o2 = tube(f'PlateRoot{k:02d}b', pts2, V['seed'] + 50 + k, rib=.16, twist=.08, collection=coll, moss_bias=-.15, cap_end=not spike)
                o2.data.materials.append(mat)
                objs.append(o2)
                if spike:
                    caps.append((o2, pts2))
    # 貼地爬的根：從泥丘腳往兩側、往後爬，鑽進土裡（封平就好，埋在土裡）
    for k, sg in enumerate((-1, 1, -1, 1)):
        y0 = sg * g['Re'] * R.uniform(.45, .75)
        back = k >= 2
        x0 = g['xp'] + (.0 if back else .5 * g['Tp'])
        pts = [(x0 + .2, y0 * .7, .45 * k_, Rt * .20, 1.0),
               (x0 - (.6 if back else .1) * k_, y0 * 1.35, .18 * k_, Rt * .16, 1.0),
               (x0 - (1.3 if back else .3) * k_, y0 * 1.9, -.05, Rt * .11, 1.0),
               (x0 - (1.8 if back else .4) * k_, y0 * 2.2, -.35, Rt * .07, 1.0)]
        o = tube(f'GroundRoot{k}', pts, V['seed'] + 70 + k, rib=.16, twist=.08, collection=coll, moss_bias=-.05, cap_end=True)
        o.data.materials.append(mat)
        objs.append(o)
    return caps


def sinkers(V, coll, R, mat, objs):
    """朝外那面（原本的根底）：參考圖整面是一團根，不是光滑的泥面。
    - 面根：從中心附近往外放射到邊緣、半埋在泥裡，一半分出一條副根；
    - 斷根刺：從面上各處往外（-X、往四周）戳出來的斷根，末端斷成淺色木刺（參考圖根盤一圈放射狀的尖刺）；
    - 下扎根：往下、往外斷掉的幾截。"""
    g = plate_geom(V)
    caps = []
    big = V['id'] == 'B'
    fx = lambda d: g['xp'] - g['Tm'] * face_prof(min(1.0, d / g['Re']))
    # 面根：從中心附近出發、一路左右彎著往外爬到邊緣（隨機走，會互相交錯、壓在別條上面），粗細差很大；
    # 粗的一路分出副根；三分之一的粗根有一條細根繞著它螺旋纏上去（參考圖的根是互相纏繞的一團，不是一條條平行放射）
    cz = Vector((0, 0, g['zc']))
    stepl = .17 * g['k']

    def walk(a0, d0, r, depth, tag, seed_):
        Rw = random.Random(seed_)
        pos = Vector((0, math.cos(a0) * d0, math.sin(a0) * d0))
        head = a0 + Rw.uniform(-.5, .5)
        lift0 = Rw.uniform(-.15, .40)          # 多半半埋：朝外那面看到的是褐土，根是嵌在土裡的          # 根中心離泥面：0 是半埋、1 是整條浮在面上；各條不同，交錯時一條壓一條
        pts, s_ = [], 0.0
        for i in range(40):
            d = pos.length
            if d > g['Re'] * Rw.uniform(.93, 1.0):
                break
            rad = math.atan2(pos.z, pos.y)
            # 往外為主、隨機轉彎（拉回往外的力量弱一點，才會彎來彎去交錯）
            dh = (rad - head + math.pi) % (2 * math.pi) - math.pi
            head += .30 * dh + Rw.gauss(0, .42)
            f = min(1.0, d / g['Re'])
            rr = r * (1 - .55 * f)
            lift = rr * lift0 + .04 * g['k'] * (1 + math.sin(s_ * 2.3 + seed_))
            pts.append((face_x(V, pos.y, g['zc'] + pos.z, V['seed']) - lift, pos.y, g['zc'] + pos.z, rr, 1.0))       # 朝外是 -X
            pos = pos + Vector((0, math.cos(head), math.sin(head))) * stepl
            s_ += stepl
        if len(pts) < 3 or min(p[2] for p in pts) < -.05:
            return None
        x, y, z, rr, fl = pts[-1]
        pts[-1] = (x + rr * 1.5 + .05 * g['k'], y, z, rr * .8, fl)          # 末端鑽進泥裡（+X 是往泥裡）
        o = tube(tag, pts, seed_, rib=.16, twist=.08, collection=coll, moss_bias=-1, cap_end=True)
        o.data.materials.append(mat)
        objs.append(o)
        if depth == 0:
            nb = Rw.randint(1, 3) if r > .08 * g['k'] else Rw.randint(0, 1)
            for bi in range(nb):
                j = Rw.randint(1, max(1, len(pts) - 3))
                q = pts[j]
                a2 = math.atan2(q[2] - g['zc'], q[1]) + Rw.choice((-1, 1)) * Rw.uniform(.25, .7)
                walk(a2, math.hypot(q[1], q[2] - g['zc']), q[3] * Rw.uniform(.40, .65), 1, f'{tag}b{bi}', seed_ + 31 * (bi + 1))
            if r > .10 * g['k'] and Rw.random() < .45:
                tw = twine(pts, Rw, r * Rw.uniform(.22, .32), Rw.uniform(.7, 1.3) * g['k'])
                if tw:
                    o2 = tube(f'{tag}t', tw, seed_ + 7, rib=.12, twist=.06, collection=coll, moss_bias=-1, cap_end=True)
                    o2.data.materials.append(mat)
                    objs.append(o2)
        return o

    nf = 11 if big else 9
    for k in range(nf):
        a = 2 * math.pi * k / nf + R.uniform(-.25, .25)
        u = R.random()
        r = g['k'] * (.045 + .17 * u * u)                       # 大多細、少數很粗
        walk(a, g['Re'] * R.uniform(.03, .22), r, 0, f'FaceRoot{k:02d}', V['seed'] + 140 + 13 * k)
    # 斷根刺：從面上往外戳
    ns = 15 if big else 11
    for k in range(ns):
        for _ in range(30):
            a = R.uniform(-.35 * math.pi, 1.35 * math.pi)            # 下面那圈埋在土裡的不要
            d = g['Re'] * R.uniform(.25, .90)
            y, z = math.cos(a) * d, g['zc'] + math.sin(a) * d
            if z > .35:
                break
        r = g['k'] * (.06 + .12 * R.random() ** 1.5)
        x0 = fx(d) + .25 * r
        out_ = Vector((0, math.cos(a), math.sin(a)))
        dv = (Vector((-1, 0, 0)) * R.uniform(.5, 1.0) + out_ * R.uniform(.5, 1.1) + Vector((0, 0, R.uniform(-.15, .35)))).normalized()
        ln = g['k'] * R.uniform(.55, 1.3)          # 參考圖根盤一圈長長的斷根刺
        side = dv.cross(Vector((0, 0, 1)))
        if side.length < 1e-3:
            side = Vector((0, 1, 0))
        side.normalize()
        p0 = Vector((x0 + .30 * r, y, z))
        pts = [(p0.x, p0.y, p0.z, r, 1.0)]
        bend = R.uniform(.10, .22) * R.choice((-1, 1))
        for u in (.25, .5, .75, 1.0):
            q = p0 + dv * ln * u + side * (bend * ln * math.sin(u * 2.6 + k)) + Vector((0, 0, -.12 * ln * u * u))
            pts.append((q.x, q.y, q.z, r * (1 - .35 * u ** .8), 1.0))
        if min(p[2] for p in pts) < .05:
            continue
        o = tube(f'FaceSpike{k:02d}', pts, V['seed'] + 230 + k, rib=.14, twist=.08, collection=coll, moss_bias=-1, cap_end=False)
        o.data.materials.append(mat)
        objs.append(o)
        caps.append((o, pts))
    for k in range(5 if big else 4):
        a = R.uniform(-.2, math.pi + .2)
        d = g['Re'] * R.uniform(.20, .60)
        y, z = math.cos(a) * d, g['zc'] + math.sin(a) * d * .8
        r = g['k'] * R.uniform(.11, .17)
        x0 = fx(d) + .3
        ln = g['k'] * R.uniform(.22, .45)
        dv = Vector((-1, R.uniform(-.4, .4), -.55)).normalized()
        pts = [(x0, y, z, r, 1.0)] + [(x0 + dv.x * (g['Tm'] * .3 + .3 + ln * u), y + dv.y * ln * u, z + dv.z * ln * u - .08 * u * u, r * (1 - .3 * u), 1.0) for u in (.5, 1.0)]
        o = tube(f'Sinker{k}', pts, V['seed'] + 120 + k, rib=.14, twist=.06, collection=coll, moss_bias=-1, cap_end=False)
        o.data.materials.append(mat)
        objs.append(o)
        caps.append((o, pts))
    return caps


def dome_roots(V, coll, R, mat, objs):
    """泥丘頂上、朝樹幹那面（原本的地面那側）：粗根之間再爬一層細根，從樹幹基部出來、貼著泥面往外彎，
    末端鑽進泥裡；位置用和泥丘同一個函式算（mud_pt），高模低模一樣，不會浮起來或埋進去。"""
    g = plate_geom(V)
    Rt, k_ = V['R'], g['k']
    seed = V['seed']
    n = 10 if V['id'] == 'B' else 8
    for k in range(n):
        ph = -.15 * math.pi + 1.30 * math.pi * (k + R.uniform(-.4, .4)) / n
        r = Rt * (.035 + .07 * R.random() ** 1.5)
        lift = R.uniform(-.30, .10)          # 半埋在泥和苔裡，只露出背脊：不要像提籃的把手架在泥丘上
        wob, wph = R.uniform(.08, .20), R.uniform(0, 6.3)
        x0 = R.uniform(.35, .55)
        pts = []
        dr = Vector((0, math.cos(ph), math.sin(ph)))
        p0 = Vector((1.1 * k_, 0, trunk_z(V, 1.1 * k_))) + dr * trunk_r(V, 1.1 * k_) * .7
        pts.append((p0.x, p0.y, p0.z, r * 1.2, 1.0))
        m = 7
        for j in range(m):
            u = j / (m - 1)
            dx = x0 + (-.15 - x0) * u                    # 從朝樹幹那面（d.x > 0）爬到頂上、快到邊緣
            a = ph + wob * math.sin(u * 5 + wph)
            q = math.sqrt(max(0.0, 1 - dx * dx))
            d = Vector((dx, q * math.cos(a), q * math.sin(a)))
            P = mud_pt(V, d, seed)
            rr = r * (1 - .5 * u)
            P = P + mud_nrm(V, d, seed) * rr * (lift if j < m - 1 else -1.2)        # 最後一點鑽進泥裡
            pts.append((P.x, P.y, P.z, rr, 1.0))
        if min(p[2] for p in pts) < .1:
            continue
        o = tube(f'DomeRoot{k:02d}', pts, V['seed'] + 500 + k, rib=.14, twist=.08, collection=coll, moss_bias=-.10, cap_end=True)
        o.data.materials.append(mat)
        objs.append(o)


def root_hairs(V, coll, R, mat, n, seed, nu=6):
    """細根鬚：從泥丘外緣和朝外那面垂下來，有點彎。"""
    g = plate_geom(V)
    hs = []
    for i in range(n):
        for _ in range(50):
            d = face_dir(R, .25, .97)
            P = mud_pt(V, d, seed)
            if .15 < P.z < g['zc'] + g['Re'] * .8:
                break
        p = P + mud_nrm(V, d, seed) * .03
        ln = g['k'] * R.uniform(.25, 1.0)
        dx = R.uniform(-.25, -.05)
        wy = R.uniform(-.15, .15)
        # 細根鬚：先貼著泥面往外一小段，再垂下來，一路小幅左右擺（不是一根直棍）；末段往回勾一點
        amp, ph, fq = R.uniform(.03, .07) * g['k'], R.uniform(0, 6.3), R.uniform(2.5, 4.5)
        pts = []
        for j in range(7):
            u = j / 6
            sag = u ** 1.4
            pts.append((p.x + dx * (.9 * u - .3 * u * u) + amp * math.sin(fq * u * 3.1 + ph) * .6,
                        p.y + wy * u + amp * math.cos(fq * u * 2.7 + ph),
                        p.z - ln * sag, .020 * (1 - .78 * u) + .003, 1.0))
        o = tube(f'Hair{i:02d}', pts, V['seed'] + 200 + i, rib=0, twist=0, nu=nu, collection=coll, moss_bias=-1, cap_end=True)
        o.data.materials.append(mat)
        hs.append(o)
    return hs


# ---------------- 枝樁、層狀菌 ----------------
def surf(rings, s, ang):
    """樹幹在 s（公尺）、繞軸角 ang（0＝正上方，正值往 -Y 側）處的中心、外法線、軸向、半徑。"""
    ss = [q[3] for q in rings]
    k = min(range(len(rings)), key=lambda i: abs(ss[i] - s))
    c, r = rings[k][0], rings[k][1]
    a = (rings[min(k + 1, len(rings) - 1)][0] - rings[max(k - 1, 0)][0]).normalized()
    up = Vector((0, 0, 1))
    up = (up - a * up.dot(a)).normalized()
    sd = a.cross(up).normalized()
    n = (up * math.cos(ang) + sd * math.sin(ang)).normalized()
    return c, n, a, r


def stubs(V, coll, R, mat, objs, rings, caps):
    """斷枝：一根往上、往斷口方向翹的長斷枝，一兩個短枝樁。"""
    for i, (f, ang, ln, rf, pitch) in enumerate(V['stubs']):
        c, n, a, r = surf(rings, f * V['L'], ang)
        br = V['R'] * rf
        d = (n * math.cos(pitch) + a * math.sin(pitch)).normalized()
        st = c + n * r * .35
        Lt = r * .65 + ln
        side = d.cross(Vector((0, 0, 1)))
        # 斷枝要像從樹幹長出來、斷掉的一截（參考圖）：不是一根同樣粗的管子插在樹幹上。
        # 出樹皮那裡一圈枝領（粗、和樹幹接在一起），往上收細，末段斷成參差木刺；長度只有樹幹直徑上下
        sx = r * .65 / max(.3, n.dot(d))           # 從起點（樹幹裡）到出樹皮的距離
        prof = ((0.0, 1.95), (sx * .85, 1.80), (sx + .35 * br, 1.30), (sx + .45 * ln, 1.0), (sx + .80 * ln, .86), (sx + ln, .80))
        pts = []
        for s_, k_ in prof:
            u = s_ / (sx + ln)
            p = st + d * s_ + side * (.05 * (sx + ln) * math.sin(u * 3.0 + i)) + Vector((0, 0, -.03 * (sx + ln) * u * u))
            pts.append((p.x, p.y, p.z, br * k_, 1.0))
        o = tube(f'Stub{i}', pts, V['seed'] + 300 + i, rib=.18, twist=.10, collection=coll,
                 moss_bias=lambda p, nn: .60 * max(0.0, nn.z) + .34, cap_end=False)          # 斷枝和樹幹一樣蓋著苔（參考圖）：朝上那面整片、側面一塊一塊，和樹幹頂連成一片
        o.data.materials.append(mat)
        objs.append(o)
        caps.append((o, pts))


def brackets(V, coll, R, rings, mat):
    """層狀菌：一叢 3–6 片半圓形菌蓋疊在側面，上面一圈圈褐色、邊緣淺色，下面奶油色。"""
    V_, F_, C_ = [], [], []
    for (f, ang, cnt) in V['fungi']:
        s0 = f * V['L']
        for q in range(cnt):
            s = s0 + R.uniform(-.35, .35) * V['R']
            an = ang + R.uniform(-.30, .20)
            c, n, a, r = surf(rings, s, an)
            w = V['R'] * R.uniform(.12, .24)
            dep = w * R.uniform(.55, .75)
            th = w * R.uniform(.16, .24)
            p0 = c + n * r * .93
            hz = Vector((0, 0, 1))
            out = (n - hz * n.dot(hz)).normalized()
            along = hz.cross(out).normalized()
            base = len(V_)
            na, nrad = 14, 6
            for top in (1, 0):
                for i in range(nrad + 1):
                    rho = i / nrad
                    for j in range(na + 1):
                        t = math.pi * j / na
                        x = math.cos(t) * w * rho * (1 + .08 * math.sin(t * 5 + q))
                        y = math.sin(t) * dep * rho
                        zz = (th * (1 - rho ** 2) ** .6 * .9 if top else -th * .25 * (1 - rho ** 2)) - .25 * th * rho * rho
                        P = p0 + along * x + out * y + hz * zz
                        V_.append(tuple(P))
                        band = .5 + .5 * math.sin(rho * 14)
                        if top:
                            cc = (.17 + .10 * rho + .04 * band, .11 + .08 * rho + .03 * band, .06 + .05 * rho, 1) if rho < .86 else (.55, .50, .40, 1)
                        else:
                            cc = (.62, .56, .45, 1)
                        C_.append(cc)
            row = na + 1
            for tp in range(2):
                off = base + tp * (nrad + 1) * row
                for i in range(nrad):
                    for j in range(na):
                        a0 = off + i * row + j
                        quad = (a0, a0 + 1, a0 + row + 1, a0 + row)
                        F_.append(quad if tp == 0 else quad[::-1])
    me = bpy.data.meshes.new('DR06_Brackets')
    me.from_pydata(V_, [], F_)
    ca = me.color_attributes.new('Tint', 'FLOAT_COLOR', 'POINT')
    ca.data.foreach_set('color', np.array(C_, np.float32).ravel())
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    return _obj('Brackets', me, coll)


# ---------------- 組起來 ----------------
LOW_SKIP = ('Hair',)


def build(variant='B', quick=True, low=None, col=False, pre=''):
    """low=(step, numin, numax, nuk)：同一份路徑做不帶樹皮凹凸的低模（不剝皮、泥丘和坑少一點面）；
    col=True：只做碰撞用的粗件（樹幹、粗的斷枝、泥丘）；pre：物件名前綴（低模 'L_'、碰撞 'C_'），對得回高模的同名物件。"""
    V = set_variant(variant)
    CFG.update(step=.12 if quick else .05, numin=28 if quick else 48, numax=520, amp=.21, moss=.095, nuk=.8, crest=.40)      # 樹皮板和裂溝比 A 批深（參考圖的老樹皮稜溝很深）
    if low:
        CFG.update(step=low[0], numin=low[1], numax=low[2], amp=0.0, moss=0.0, nuk=low[3])
    seed = V['seed']
    noise.seed_set(seed)
    R = random.Random(seed)
    coll = _coll(f"DR06_{V['name']}_{'Col' if col else ('Low' if low else 'High')}")
    mat = bark_material()
    objs = []
    tp = trunk_pts(V)
    trunk = tube('Trunk', tp, seed, rib=.26, twist=.12, collection=coll,
                 moss_bias=trunk_moss, cap_end=bool(col))
    trunk.data.materials.append(mat)
    objs.append(trunk)
    if not low:
        peel(trunk, tp, seed, 2.2, V['L'] - .9)
    rings, _ = resample(tp, CFG['step'])
    caps = [(trunk, tp, 1.7, 48, 40 if V['id'] == 'B' else 30, (.30, .95))]          # 主幹斷口：一大束長木刺往外散（參考圖的斷口比樹幹還寬）
    sc = []
    stubs(V, coll, R, mat, objs, rings, sc)
    if col:
        for o, p in sc:
            if p[2][3] < .25 * V['R'] * 1.3:          # 出樹皮處的半徑（第 3 個控制點，1.3 倍枝徑）
                bpy.data.objects.remove(o, do_unlink=True)
        mud_plate(V, coll, seed, (16, 10))
        return _finish_names(coll, pre)
    caps += [(o, p, 1.5 if i == 0 else .9, 16 if i == 0 else 14, 10 if i == 0 else 3, (.35, 1.25)) for i, (o, p) in enumerate(sc)]      # 大斷枝頂端：一束參差的長木刺（參考圖）
    caps += [(o, p, 1.9, 12, 9, (.6, 1.9)) for o, p in plate_roots(V, coll, R, mat, objs)]          # 根的斷口木刺長一點（相對根徑）：參考圖淺色尖端很顯眼          # 斷根末端：一束淺色木刺（參考圖根盤一圈淺色尖端）
    caps += [(o, p, 1.8, 11, 8, (.6, 1.8)) for o, p in sinkers(V, coll, R, mat, objs)]
    dome_roots(V, coll, R, mat, objs)
    mud_plate(V, coll, seed, (36, 22) if low else (180, 110))
    stones(V, coll, R, 9 if V['id'] == 'B' else 7, seed, 2 if low else 3)
    root_hairs(V, coll, R, mat, 230 if V['id'] == 'B' else 170, seed, 4 if low else 6)
    pit(V, coll, R, *((6, 28) if low else (16, 72)))
    for i, (o, p, reach, nsp, sh, sl) in enumerate(caps):
        snap_cap(f'Snap_{o.name}', o, p, p[-1][3], seed + 400 + i, coll, reach=reach, nspk=nsp, shards=sh,
                 top=1.0 if o is trunk else .8, sub=2 if low else 4,
                 splay=.40 if o is trunk else .34, shard_w=3.0 if o is trunk else 1.9, slen=sl)
    brackets(V, coll, R, rings, core_plants.mushroom_material())
    print('BUILD', V['id'], 'low' if low else 'high', len(coll.objects), 'objects')
    return _finish_names(coll, pre)


def _finish_names(coll, pre):
    """低模、碰撞：物件名加前綴、去掉 Blender 自動加的 .001（高模同名物件已經佔了名字）。"""
    obs = list(coll.objects)
    if pre:
        for o in obs:
            o.name = pre + re.sub(r'\.\d{3}', '', o.name)
            o.data.name = o.name
    return obs


# ---------------- 植物 ----------------
def _twigs(name, paths, mat, sides=6):
    """細枝幹：paths = [[(Vector, 半徑), ...], ...]，每條做成一根 6 邊形的管子。"""
    Vs, Fs = [], []
    for path in paths:
        base = len(Vs)
        n = len(path)
        for i, (p, r) in enumerate(path):
            d = (path[min(i + 1, n - 1)][0] - path[max(i - 1, 0)][0]).normalized()
            sd = d.cross(Vector((0, 0, 1)))
            if sd.length < 1e-3:
                sd = d.cross(Vector((1, 0, 0)))
            sd.normalize()
            up = sd.cross(d).normalized()
            for k in range(sides):
                a = 2 * math.pi * k / sides
                Vs.append(tuple(p + (sd * math.cos(a) + up * math.sin(a)) * r))
        for i in range(n - 1):
            for k in range(sides):
                a0 = base + i * sides + k
                a1 = base + i * sides + (k + 1) % sides
                Fs.append((a0, a1, a1 + sides, a0 + sides))
        Fs.append(tuple(base + (n - 1) * sides + k for k in range(sides)))
    me = bpy.data.meshes.new(name)
    me.from_pydata(Vs, [], Fs)
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def sapling(name, pos, R, height, leaf_mat, stem_mat):
    """小樹苗：一根微彎的主莖、4–6 根側枝，枝上互生卵形葉，頂上一簇。"""
    buf = core_plants.LeafBuf()
    lean = Vector((R.uniform(-.12, .12), R.uniform(-.12, .12), 1)).normalized()
    stem = []
    for i in range(9):
        u = i / 8
        p = pos + lean * height * u + Vector((.03 * math.sin(u * 5 + height * 7), .03 * math.cos(u * 4), 0)) * height
        stem.append((p, height * .018 * (1 - .8 * u) + .003))
    paths = [stem]

    def leafs(at, d, k, L0):
        for j in range(k):
            a = (j % 2 * 2 - 1) * R.uniform(.7, 1.2)
            dd = (d * math.cos(a) + d.cross(Vector((0, 0, 1))).normalized() * math.sin(a) + Vector((0, 0, R.uniform(-.35, .40)))).normalized()
            dd, side, nrm = core_plants._frame(dd)
            ro = R.uniform(-1.0, 1.0)              # 葉面繞葉軸轉：葉子不全是水平的，樹冠才不會一層一層像平台
            side, nrm = side * math.cos(ro) + nrm * math.sin(ro), -side * math.sin(ro) + nrm * math.cos(ro)
            L = L0 * R.uniform(.8, 1.15)
            g = R.uniform(.85, 1.15)
            buf.leaf(at(j / max(1, k - 1)) - dd * .005, dd, side, nrm, L, L * R.uniform(.48, .58),
                     shape=lambda u: math.sin(math.pi * min(1.0, u * 1.08)) ** .75 * (1 - .25 * u), fold=R.uniform(.15, .35),
                     curl=R.uniform(-.05, .2), droop=R.uniform(.05, .25), tint=(g * R.uniform(.95, 1.1), g, g * .85), nu=6, nv=4)

    nb = R.randint(10, 12)
    for b in range(nb):
        u = .22 + .66 * b / max(1, nb - 1) + R.uniform(-.04, .04)          # 側枝從低處就開始長：一團圓的小樹冠，不是光桿頂上幾層
        i = min(7, int(u * 8))
        p0 = stem[i][0]
        az = b * 2.4 + R.uniform(-.3, .3)
        d = Vector((math.cos(az), math.sin(az), .10 + .75 * u + R.uniform(-.1, .1))).normalized()       # 下面的枝平展、上面的往上：外輪廓是圓的
        L = height * R.uniform(.30, .42) * (.55 + 1.6 * u * (1 - u) + .25 * (1 - u))      # 中段最長、上下短
        pts = [(p0 + d * L * t + Vector((0, 0, -.12 * L * t * t)), stem[i][1] * .55 * (1 - .7 * t) + .002) for t in (0, .5, 1.0)]
        paths.append(pts)
        tip = pts[-1][0]
        leafs(lambda t, p0=p0, tip=tip: p0.lerp(tip, .15 + .85 * t), d, R.randint(7, 10), height * R.uniform(.15, .19))
        # 每根側枝再分出兩根小枝，樹冠才會是一團、不是一根莖掛葉子
        for s in (-1, 1):
            q0 = p0.lerp(tip, R.uniform(.40, .65))
            ds = (d + d.cross(Vector((0, 0, 1))).normalized() * s * R.uniform(.6, 1.0) + Vector((0, 0, R.uniform(.1, .4)))).normalized()
            Ls = L * R.uniform(.45, .65)
            sp = [(q0 + ds * Ls * t + Vector((0, 0, -.10 * Ls * t * t)), stem[i][1] * .30 * (1 - .7 * t) + .0015) for t in (0, .5, 1.0)]
            paths.append(sp)
            stip = sp[-1][0]
            leafs(lambda t, q0=q0, stip=stip: q0.lerp(stip, .2 + .8 * t), ds, R.randint(4, 6), height * R.uniform(.13, .16))
    top = stem[-1][0]
    leafs(lambda t: top, lean, 7, height * .12)
    lo = buf.build(name, leaf_mat)
    so = _twigs(name + '_Stem', paths, stem_mat)
    return lo, so


MUSH_CAP = (.24, .16, .09)          # 蕈傘（線性）：參考圖是淡褐，不是橘


def litter(name, R, count, place, mat):
    """落葉：和 core_plants.litter 同一套做法，但葉子大一點（7–13 cm）、橘褐，遠一點也看得出是一片葉子。"""
    buf = core_plants.LeafBuf()
    PAL = ((.42, .22, .07), (.50, .30, .10), (.30, .17, .08), (.40, .32, .13), (.25, .14, .07), (.55, .33, .11), (.33, .26, .12))
    n = 0
    for i in range(count * 3):
        q = place()
        if q is None:
            continue
        p, z = q
        L = R.uniform(.07, .13)
        W = L * R.uniform(.40, .55)
        a = R.uniform(0, 2 * math.pi)
        d = Vector((math.cos(a), math.sin(a), R.uniform(-.08, .08)))
        d, side, nrm = core_plants._frame(d)
        start = Vector((p[0], p[1], z + .004)) - d * L * .5
        c = PAL[R.randrange(len(PAL))]
        buf.leaf(start, d, side, nrm, L, W,
                 shape=lambda u: math.sin(math.pi * u) ** .7 * (1 - .15 * u),
                 fold=R.uniform(.05, .25), curl=R.uniform(-.1, .35), droop=R.uniform(-.05, .05), tint=c, nu=6, nv=4,
                 twist=R.uniform(-.25, .25))
        n += 1
        if n >= count:
            break
    return buf.build(name, mat), n


def dress(V, quick=True, seed=None, game=False, surf=('Trunk',)):
    """頂上（苔上）的蕨、小樹苗、苔叢、蕈；腳邊地上的大蕨、闊葉草、蕈、落葉。
    game=True：遊戲用（不做苔叢，樹皮上的苔已經烘進貼圖）；surf：射線打到哪些物件算「樹幹頂上」（遊戲用是 LOD0）。"""
    seed = V['seed'] + 900 if seed is None else seed
    R = random.Random(seed)
    L, Rt = V['L'], V['R']
    coll = _coll(f"DR06_{V['name']}_{'GamePlants' if game else 'Plants'}")
    lm = core_plants._leaf_material
    mat = lambda n, *a, **k: bpy.data.materials.get(n) or lm(n, *a, **k)
    fern_mat = mat('D2_Fern', (.050, .090, .040, 1), (.11, .17, .075, 1), (.16, .22, .11, 1), gloss=.55)
    heart_mat = mat('D2_HeartLeafPale', (.060, .105, .050, 1), (.135, .20, .10, 1), (.22, .29, .16, 1), gloss=.4)
    moss_mat = mat('D2_MossTuft', (.040, .058, .014, 1), (.10, .125, .032, 1), (.12, .15, .045, 1), gloss=.8)
    sap_mat = mat('DR06_SaplingLeafV2', (.10, .13, .030, 1), (.30, .34, .085, 1), (.38, .40, .14, 1), gloss=.45)       # 參考圖：黃綠的闊葉
    litter_mat = mat('DR06_LitterLeaf', (.15, .07, .022, 1), (.42, .22, .07, 1), (.48, .30, .11, 1), gloss=.3)       # 參考圖：橘褐落葉
    stem_mat = bpy.data.materials.get('D2_Stem')
    if stem_mat is None:
        stem_mat = bpy.data.materials.new('D2_Stem')
        stem_mat.use_nodes = True
        next(n for n in stem_mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Base Color'].default_value = (.05, .06, .025, 1)
    twig_mat = bpy.data.materials.get('DR06_Twig')
    if twig_mat is None:
        twig_mat = bpy.data.materials.new('DR06_Twig')
        twig_mat.use_nodes = True
        next(n for n in twig_mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Base Color'].default_value = (.07, .05, .035, 1)
    mush_mat = bpy.data.materials.get('UG_Mushroom') or core_plants.mushroom_material()
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()

    def hit(x, y, z0=14.0):
        ok, loc, nrm, _, ob, _ = sc.ray_cast(dg, Vector((x, y, z0)), Vector((0, 0, -1)))
        return (loc, nrm, ob.name) if ok else None

    def on_log(x, y, nz=.72):
        h = hit(x, y)
        if h and h[2] in surf and h[1].z > nz:
            return h
        return None

    def axis_y(x):
        t = max(0.0, x) / L
        return V['bend'] * Rt * math.sin(t * 2.6 + V['seed'] * .37) * t

    def half_w(x):
        r, zc = trunk_r(V, x), trunk_z(V, x)
        return math.sqrt(max(0.0, r * r - zc * zc)) if zc < r else 0.0

    def keep(o):
        for c in list(o.users_collection):
            c.objects.unlink(o)
        coll.objects.link(o)
        return o

    out = []
    sz = Rt / 1.0
    big = V['id'] == 'B'
    # 頂上：苔叢
    mounds = []
    for i in range(int(L * .8)):
        x = R.uniform(.12, .95) * L
        h = on_log(x, axis_y(x) + R.gauss(0, .18 * Rt), .8)
        if h:
            mounds.append((i, h[0].x, h[0].y, R.uniform(.22, .45) * sz, R.uniform(.14, .26) * sz, R.uniform(.03, .07), h[0].z - .03))
    if mounds and not game:
        out.append(keep(core_plants.moss_tufts('DR06_MossTufts', mounds, R, moss_mat, fb, density=2600 if quick else 5200)))
    # 頂上：蕨
    nf = 0
    for i in range(40):
        if nf >= (6 if big else 4):
            break
        x = R.uniform(.12, .92) * L
        h = on_log(x, axis_y(x) + R.gauss(0, .22 * Rt), .8)
        if not h:
            continue
        o, so = core_plants.fern(f'DR06_TopFern{nf}', h[0] - Vector((0, 0, .03)), R, R.uniform(.70, 1.0) * sz, fern_mat, stem_mat)
        out += [keep(o), keep(so)]
        nf += 1
    # 頂上：小樹苗
    # 小樹苗用自己的亂數（高模、遊戲模型長在同一處、同一個樣子）；射線從樹幹頂上一點點往下打，上面翹過去的斷枝不會擋到
    for k, f in enumerate((.56, .86) if big else (.62,)):
        RS = random.Random(seed + 77 + k)
        for i in range(40):
            x = (f + RS.uniform(-.04, .04)) * L
            y = axis_y(x) + RS.gauss(0, .12 * Rt)
            h = hit(x, y, trunk_z(V, x) + trunk_r(V, x) + .35)
            if h and h[2] in surf and h[1].z > .8:
                lo, so = sapling(f'DR06_Sapling{k}', h[0] - Vector((0, 0, .04)), RS, RS.uniform(1.15, 1.45) * (1 if k == 0 else .8) * (1 if big else .85), sap_mat, twig_mat)
                out += [keep(lo), keep(so)]
                break
    # 蕈：頂上兩三叢、腳邊地上幾叢
    nm = 0
    for i in range(30):
        if nm >= 3:
            break
        x = R.uniform(.2, .9) * L
        h = on_log(x, axis_y(x) + R.gauss(0, .30 * Rt), .6)
        if h:
            out.append(keep(core_plants.mushrooms(f'DR06_LogMush{nm}', h[0] - Vector((0, 0, .02)), R, R.randint(5, 9), 2.3 * sz, mush_mat, cap=MUSH_CAP)))
            nm += 1
    for k in range(6 if big else 4):
        x = R.uniform(.12, .9) * L
        sg = R.choice((-1, 1))
        y = axis_y(x) + sg * (half_w(x) + R.uniform(.06, .25))
        out.append(keep(core_plants.mushrooms(f'DR06_FootMush{k}', Vector((x, y, 0)), R, R.randint(4, 10), 2.6 * sz, mush_mat, cap=MUSH_CAP)))
    # 腳邊：大蕨、闊葉草
    for k in range(6 if big else 4):
        x = R.uniform(.08, .85) * L
        sg = -1 if k % 2 == 0 else 1
        y = axis_y(x) + sg * (half_w(x) + R.uniform(.35, .7))
        o, so = core_plants.fern(f'DR06_FootFern{k}', Vector((x, y, -.02)), R, R.uniform(1.0, 1.35) * sz, fern_mat, stem_mat)
        out += [keep(o), keep(so)]
    for k in range(5 if big else 3):
        x = R.uniform(.1, .9) * L
        sg = R.choice((-1, 1))
        y = axis_y(x) + sg * (half_w(x) + R.uniform(.2, .6))
        o = core_plants.heart_plant(f'DR06_Heart{k}', Vector((x, y, -.01)), R, R.uniform(.7, 1.0) * sz, heart_mat, stem_mat)
        out.append(keep(o))
        so = bpy.data.objects.get(f'DR06_Heart{k}_stem')
        if so:
            out.append(keep(so))
    # 落葉：沿著樹幹兩側、根盤前的坑邊
    g = plate_geom(V)

    def place():
        if R.random() < .8:
            x = R.uniform(-.2, 1.0) * L
            sg = R.choice((-1, 1))
            y = axis_y(x) + sg * (half_w(x) + abs(R.gauss(0, .55)) + .03)
        else:
            x = g['xp'] - g['Tm'] - V['RP'] * R.uniform(.0, 1.0)
            y = R.gauss(0, V['RP'] * .6)
        h = hit(x, y, 6.0)
        z = h[0].z if h else 0.0
        if z > .5:
            return None
        return (x, y), z
    lo, n = litter('DR06_Litter', R, int((1100 if big else 750) * (.6 if quick else 1.0)), place, litter_mat)
    out.append(keep(lo))
    print('DRESS', len(out), 'plant objects, litter', n)
    return coll


def _views(V):
    L, RP = V['L'], V['RP']
    g = plate_geom(V)
    cx = L * .45
    sf = .56 if V['id'] == 'B' else .62          # 小樹苗在樹幹上的位置（dress 裡的 f）
    return {
        'tq': ((L * .22, -L * .85, 1.7), (L * .42, 0, 1.4), 24),
        'side': ((cx, -L * 1.25 - 4, 1.7), (cx, 0, 1.3), 30),
        'plate': ((-RP * 3.2 - 2.5, -RP * 1.8, 1.8), (g['xp'], 0, RP * .70), 30),
        'plateq': ((RP * 1.6, -RP * 3.2, 2.2), (0, 0, RP * .75), 26),
        'snap': ((L + 3.8, -3.6, 1.8), (L - .3, 0, .9), 30),
        'top': ((cx, -.01, L * 1.5 + 6), (cx, 0, 0), 30),
        'sap': ((L * sf + 1.6, 3.8, 3.1), (L * sf, 0, 2.2), 35),         # 從背面看：前面那根往上翹的斷枝不擋

        'back': ((cx * .9, L * .9 + 3, 2.4), (cx, 0, 1.0), 28),
    }


if __name__ == '__main__' and '--' in sys.argv:
    args = sys.argv[sys.argv.index('--') + 1:]
    var = args[0] if args else 'B'
    quick = (args[1] if len(args) > 1 else 'quick') == 'quick'
    outdir = args[2] if len(args) > 2 else 'D:/yun-jing-cache/dr06-work'
    os.makedirs(outdir, exist_ok=True)
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    build(var, quick)
    if 'nodress' not in args:
        dress(VAR, quick)
    import preview_dr
    preview_dr.setup(samples=24 if quick else 64, fog=False)
    hum = bpy.data.objects.get('DR_Human_1p75m')
    if hum:
        hum.location = (VAR['L'] * .45, -VAR['R'] * 2.2, .875)
    want = args[3].split(',') if len(args) > 3 else list(_views(VAR))
    for k in want:
        loc, tgt, lens = _views(VAR)[k]
        preview_dr.shot(os.path.join(outdir, f"DR06_{var}_{k}.png"), loc, tgt, lens, (1280, 720))
    if len(args) > 4:
        bpy.ops.wm.save_as_mainfile(filepath=args[4])
