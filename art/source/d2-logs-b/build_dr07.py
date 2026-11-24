# DR07 巨樹樁（高模）：巨樹很久以前折斷後留下的樹樁（不是鋸的），兩種：
#   A：徑 2.5 m，矮邊約 1.35 m、最高的斷刺約 2.0 m；B：徑 3.5 m，矮邊約 1.6 m、最高的斷刺約 3.0 m。
#   頂上：參差的斷口，一邊（折斷時的鉸點那側）有幾根高高的撕裂木齒，另一邊低、朽爛；斷面一圈圈年輪層、翻卷的朽木片、細長木刺。
#   中心：朽空成一個深碗（殼厚 0.3–0.4 m），底下積了雨水（暗色水面、浮著落葉）；內壁是朽爛的橘褐纖維木。
#   基部：根頸往外張（約 1.6–1.8 倍樹幹徑），6–8 條板根扭著鑽進土裡，根間幾條細根、土和小石塊。
#   外面：深灰褐長稜老樹皮（稍微扭轉），一塊剝皮露出灰白風化木；上面的苔、地衣，腳邊蕨、蕈，一側層狀菌。
# 樹幹沿 +Z 直立；正面 -Y；z = 0 是地面；樹幹中心在原點。
# 沿用 DR05／DR06 的材質與零件（exec build_dr05.py，它再 exec build_dr06.py）；材質另存 DR07_ 副本，
# 把物件座標轉 90°（DR05／06 的纖維沿 X，樹樁的纖維要沿 Z）。
# 用法（背景，不要加 --factory-startup）：
#   blender -b --python build_dr07.py -- A quick|full <輸出資料夾> [鏡位,鏡位] [nodress] [存檔.blend]
import bpy, bmesh, math, random, sys, os
import numpy as np
from mathutils import Vector

_HERE7 = os.path.dirname(os.path.abspath(globals().get('__file__', 'D:/yun-jing-d2-logs/art/source/d2-logs-b/build_dr07.py')))
_p5 = os.path.join(_HERE7, 'build_dr05.py')
_nm7 = globals().get('__name__')
globals()['__name__'] = 'build_dr05_lib'            # 不要跑 DR05 的主程式
exec(compile(open(_p5, encoding='utf-8').read(), _p5, 'exec'), globals())
globals()['__name__'] = _nm7
__file__ = os.path.join(_HERE7, 'build_dr07.py')

# R 樹幹半徑、H (矮邊, 最高斷刺)、W 殼厚、hinge 鉸點那側的方位角（世界 XY，0 = +X）、pool 水面高、lean 傾斜
# teeth：斷刺（方位角相對 hinge, 角寬 rad, 高出矮邊比例 0–1）
VARIANTS = {
    'A': dict(name='StumpA', R=1.25, H=(1.35, 2.0), W=.38, seed=71, hinge=2.25, pool=.70, lean=(.025, -.015),
              nroots=9, teeth=((0.0, .30, 1.0), (.58, .17, .52), (-.52, .16, .42), (2.6, .15, .18)),
              fungi=((.42, -.6, 4), (.30, 2.9, 3))),
    'B': dict(name='StumpB', R=1.75, H=(1.62, 3.0), W=.50, seed=89, hinge=-.65, pool=.70, lean=(-.02, .03),
              nroots=11, teeth=((0.0, .26, 1.0), (.46, .19, .68), (-.48, .21, .52), (1.25, .14, .26), (-1.55, .12, .20), (2.9, .16, .15)),
              fungi=((.30, 1.0, 5), (.40, 1.6, 4), (.25, -2.3, 3))),
}
VAR = VARIANTS['A']
PRE = 'DR07'


def set_variant(v):
    global VAR
    VAR = VARIANTS[v]
    VAR['id'] = v
    VAR['L'] = VAR['H'][1]          # DR05／06 的函式用 L 當「長度」：樹樁就是最高點
    return VAR


# ---------------- 材質（DR07 副本，物件座標轉 90°） ----------------
def _reorient(m, normals=False):
    """物件座標（還有 normals=True 時的幾何法線）先繞 Y 轉 90°：(x, y, z) → (z, y, −x)，原本沿 X 拉長的纖維就沿 Z。"""
    N, Lk = m.node_tree.nodes, m.node_tree.links
    srcs = [n.outputs['Object'] for n in N if n.type == 'TEX_COORD']
    if normals:
        srcs += [n.outputs['Normal'] for n in N if n.type == 'NEW_GEOMETRY']
    for out in srcs:
        links = list(out.links)
        if not links:
            continue
        vr = N.new('ShaderNodeVectorRotate')
        vr.rotation_type = 'Y_AXIS'
        vr.inputs['Angle'].default_value = math.pi / 2
        Lk.new(out, vr.inputs['Vector'])
        for l in links:
            to = l.to_socket
            Lk.remove(l)
            Lk.new(vr.outputs['Vector'], to)


def bark7_material():
    m = bpy.data.materials.get('DR07_Bark')
    if m:
        return m
    m = bark5_material().copy()
    m.name = 'DR07_Bark'
    _reorient(m, normals=False)          # 地衣「朝上」要用世界法線，不轉
    for n in m.node_tree.nodes:          # 第二輪：直立的樹幹整面都是「側面」，躺著的 DR05／06 調的地衣斑在這裡太多、太白（像白漆）
        if n.type == 'VALTORGB':
            e = n.color_ramp.elements
            if abs(e[0].position - .60) < 1e-3 and abs(e[1].position - .64) < 1e-3:
                e[0].position, e[1].position = .665, .705
            elif abs(e[0].position - .15) < 1e-3 and abs(e[1].position - .55) < 1e-3 and abs(e[0].color[0] - .35) < 1e-3:
                e[0].color = (.55, .55, .55, 1)            # 第四輪：裂溝別壓那麼黑（從上往下看整片是黑的）
        elif n.type == 'MIX_RGB' and n.blend_type == 'MIX' and abs(n.inputs[2].default_value[0] - .31) < 1e-3:
            n.inputs[2].default_value = (.15, .17, .15, 1)          # 第四輪：只比樹皮亮一點（線性 .25 在暗樹皮上還是一塊塊白斑）
        elif n.type == 'HUE_SAT':
            n.inputs['Value'].default_value = 2.8          # 第三、四輪：從上往下看（參考圖鏡位）樹皮幾乎是黑的；參考圖是淺灰褐
        if n.type == 'VALTORGB' and abs(n.color_ramp.elements[-1].color[0] - .56) < 1e-3 and abs(n.color_ramp.elements[0].color[0] - .36) < 1e-3:
            n.color_ramp.elements[0].color = (.10, .115, .105, 1)      # DR05 的一朵朵地衣：樹樁的根朝上，一朵朵太白（像白漆），壓暗
            n.color_ramp.elements[-1].color = (.17, .19, .175, 1)
    return m


def rot7_material():
    m = bpy.data.materials.get('DR07_Rot')
    if m:
        return m
    m = rot_material().copy()
    m.name = 'DR07_Rot'
    _reorient(m, normals=True)           # 斷面（法線沿軸）纖維溝淡掉：軸現在是 Z
    # 第六輪：DR05 的白色菌絲在直立的內壁上像一塊白漆，壓成暗灰褐、少一點
    for n in m.node_tree.nodes:
        if n.type == 'MIX_RGB' and tuple(round(c, 2) for c in n.inputs[2].default_value[:3]) == (.62, .60, .55):
            n.inputs[2].default_value = (.30, .26, .20, 1)
            fr = n.inputs[0].links[0].from_node if n.inputs[0].links else None
            if fr is not None and fr.type == 'VALTORGB':
                fr.color_ramp.elements[0].position, fr.color_ramp.elements[1].position = .70, .76
    rot7_extras(m)
    return m


def rot7_extras(m):
    """第二輪（以下節點用原本的物件座標、世界法線，不轉）：
    - 內壁往下越深越暗（參考圖洞裡靠水面是深紅褐、上緣才是亮橘褐）；
    - 縱向拉長的朽洞（Voronoi 沿 Z 拉長，洞裡暗）：參考圖內壁一條條、一窩窩朽空的纖維，不是一面平的木板；
    - 朝上的斷面（|n.z| 大）一圈圈年輪：淺灰褐、細的深色環，環照雜訊扭一點。"""
    N, Lk = m.node_tree.nodes, m.node_tree.links
    b = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    mx = b.inputs['Base Color'].links[0].from_node          # 最後一個「苔」的 Mix：苔留在最上層
    lk = mx.inputs[1].links[0]
    src = lk.from_socket
    Lk.remove(lk)
    tc = N.new('ShaderNodeTexCoord')
    sep = N.new('ShaderNodeSeparateXYZ')
    Lk.new(tc.outputs['Object'], sep.inputs[0])
    geo = N.new('ShaderNodeNewGeometry')
    gz = N.new('ShaderNodeSeparateXYZ')
    Lk.new(geo.outputs['Normal'], gz.inputs[0])
    anz = N.new('ShaderNodeMath')
    anz.operation = 'ABSOLUTE'
    Lk.new(gz.outputs['Z'], anz.inputs[0])
    pool = VAR['pool']
    dep = _ramp(N, pool - .05, pool + 1.1, (.36, .24, .17, 1), (1.0, .82, .64, 1))      # 第三輪：內壁偏紅褐（參考圖），往下越暗
    Lk.new(sep.outputs['Z'], dep.inputs[0])
    mp = N.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (3.6, 3.6, .75)          # 一格約 28 cm 寬、1.3 m 高：洞是縱向的長縫
    Lk.new(tc.outputs['Object'], mp.inputs['Vector'])
    pv = N.new('ShaderNodeTexVoronoi')
    pv.inputs['Randomness'].default_value = 1.0
    Lk.new(mp.outputs[0], pv.inputs['Vector'])
    pg = N.new('ShaderNodeTexNoise')                      # 只有一部分的格子是洞：成片出現
    pg.inputs['Scale'].default_value = 2.2
    pg.inputs['Detail'].default_value = 3
    Lk.new(tc.outputs['Object'], pg.inputs['Vector'])
    pgr = _ramp(N, .42, .60, (0, 0, 0, 1), (1, 1, 1, 1))
    Lk.new(pg.outputs['Fac'], pgr.inputs[0])
    hole = _ramp(N, .06, .26, (1, 1, 1, 1), (0, 0, 0, 1))          # 1 = 洞裡
    Lk.new(pv.outputs['Distance'], hole.inputs[0])
    wall = _ramp(N, .45, .80, (1, 1, 1, 1), (0, 0, 0, 1))          # 只在內壁（直立面），朝上的斷面不挖
    Lk.new(anz.outputs[0], wall.inputs[0])
    hm = N.new('ShaderNodeMath')
    hm.operation = 'MULTIPLY'
    Lk.new(hole.outputs[0], hm.inputs[0])
    Lk.new(pgr.outputs[0], hm.inputs[1])
    hm2 = N.new('ShaderNodeMath')
    hm2.operation = 'MULTIPLY'
    Lk.new(hm.outputs[0], hm2.inputs[0])
    Lk.new(wall.outputs[0], hm2.inputs[1])
    hc = N.new('ShaderNodeMixRGB')
    hc.blend_type = 'MULTIPLY'
    Lk.new(hm2.outputs[0], hc.inputs[0])
    hc.inputs[2].default_value = (.42, .24, .14, 1)               # 洞裡深紅褐
    Lk.new(src, hc.inputs[1])
    dm = N.new('ShaderNodeMixRGB')
    dm.blend_type = 'MULTIPLY'
    dm.inputs[0].default_value = 1.0
    Lk.new(hc.outputs[0], dm.inputs[1])
    Lk.new(dep.outputs[0], dm.inputs[2])
    # 年輪：離軸心的距離（XY）× 每公尺 26 圈，雜訊扭一點
    ln_ = N.new('ShaderNodeVectorMath')
    ln_.operation = 'LENGTH'
    cxy = N.new('ShaderNodeCombineXYZ')
    Lk.new(sep.outputs['X'], cxy.inputs['X'])
    Lk.new(sep.outputs['Y'], cxy.inputs['Y'])
    Lk.new(cxy.outputs[0], ln_.inputs[0])
    rn = N.new('ShaderNodeTexNoise')
    rn.inputs['Scale'].default_value = 1.3
    rn.inputs['Detail'].default_value = 2
    Lk.new(tc.outputs['Object'], rn.inputs['Vector'])
    ra = N.new('ShaderNodeMath')
    ra.operation = 'MULTIPLY_ADD'
    ra.inputs[1].default_value = 26.0
    Lk.new(ln_.outputs['Value'], ra.inputs[0])
    rn2 = N.new('ShaderNodeMath')
    rn2.operation = 'MULTIPLY'
    rn2.inputs[1].default_value = 3.0
    Lk.new(rn.outputs['Fac'], rn2.inputs[0])
    Lk.new(rn2.outputs[0], ra.inputs[2])
    fr = N.new('ShaderNodeMath')
    fr.operation = 'FRACT'
    Lk.new(ra.outputs[0], fr.inputs[0])
    rr = N.new('ShaderNodeValToRGB')
    e = rr.color_ramp.elements
    e[0].position, e[0].color = .0, (.11, .075, .045, 1)          # 線性色：深色環
    e[1].position, e[1].color = .25, (.34, .25, .16, 1)          # 淺灰褐（sRGB 約 .62/.54/.44）
    e3 = rr.color_ramp.elements.new(.80)
    e3.color = (.28, .20, .125, 1)
    Lk.new(fr.outputs[0], rr.inputs[0])
    rb = _streak(N, Lk, (2.0, 2.0, 2.0), 4)                      # 大片的深淺
    rbr = _ramp(N, .35, .70, (.72, .70, .68, 1), (1.05, 1.02, 1.0, 1))
    Lk.new(rb.outputs['Fac'], rbr.inputs[0])
    rcol = N.new('ShaderNodeMixRGB')
    rcol.blend_type = 'MULTIPLY'
    rcol.inputs[0].default_value = 1.0
    Lk.new(rr.outputs[0], rcol.inputs[1])
    Lk.new(rbr.outputs[0], rcol.inputs[2])
    up = _ramp(N, .30, .55, (0, 0, 0, 1), (1, 1, 1, 1))      # 第六輪：斷口的台階面比較斜，以前 .55–.82 年輪畫不上去
    Lk.new(anz.outputs[0], up.inputs[0])
    # 第五輪：年輪只畫在上面的斷面。B 的洞底上方有一圈緩坡（板根包進來），之前也被畫上淺色年輪，像一圈耙過的沙
    hi = _ramp(N, pool + .35, pool + .55, (0, 0, 0, 1), (1, 1, 1, 1))
    Lk.new(sep.outputs['Z'], hi.inputs[0])
    upm = N.new('ShaderNodeMath')
    upm.operation = 'MULTIPLY'
    Lk.new(up.outputs[0], upm.inputs[0])
    Lk.new(hi.outputs[0], upm.inputs[1])
    fin = N.new('ShaderNodeMixRGB')
    Lk.new(upm.outputs[0], fin.inputs[0])
    Lk.new(dm.outputs[0], fin.inputs[1])
    Lk.new(rcol.outputs[0], fin.inputs[2])
    Lk.new(fin.outputs[0], mx.inputs[1])
    # 凹凸：洞往裡陷
    bp0 = b.inputs['Normal'].links[0].from_node
    hh = N.new('ShaderNodeMath')
    hh.operation = 'MULTIPLY'
    hh.inputs[1].default_value = -1.0
    Lk.new(hm2.outputs[0], hh.inputs[0])
    bp = N.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = .8
    bp.inputs['Distance'].default_value = .03
    Lk.new(hh.outputs[0], bp.inputs['Height'])
    Lk.new(bp0.outputs[0], bp.inputs['Normal'])
    Lk.new(bp.outputs[0], b.inputs['Normal'])


WATER = True          # 高模預覽放水面；遊戲流程（game_dr07）關掉：本體不含水，水面另存 <件名>_water_v001.fbx（water_dr07.py）


def water_material(name='DR07_Water'):
    """積水的 Blender 預覽材質。樹洞裡的雨水泡過朽木，是茶褐色、清的：看得到 14 cm 底下的泥和落葉，越斜看越像鏡子，
    映出內壁和天空；表面幾乎不動，只有很細的波。
    Cycles 單面透射（IOR 1.333、粗糙度 .02），透射色 = 茶色（一層水就染一次色）；凹凸是兩層很淡的雜訊。
    遊戲裡用使用者的 YunJing/CreekFlowWater 靜水模式，加了 _StillColour 茶褐、_AlphaMid 降低（見 D2LogsVerify.cs 的 WaterMat）。
    第一版是近乎黑色的鏡面，第二版照 CreekFlowWater 的灰綠不透明 .74 → 一塊淺藍圓板（使用者：「水太假了」「什麼鬼」）。"""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    N, Lk = m.node_tree.nodes, m.node_tree.links
    for n in list(N):
        N.remove(n)
    out = N.new('ShaderNodeOutputMaterial')
    b = N.new('ShaderNodeBsdfPrincipled')
    Lk.new(b.outputs['BSDF'], out.inputs['Surface'])
    b.inputs['Base Color'].default_value = (.50, .36, .20, 1)        # 透射染色：茶褐
    b.inputs['Roughness'].default_value = .02
    b.inputs['IOR'].default_value = 1.333
    for k in ('Transmission Weight', 'Transmission'):
        if k in b.inputs:
            b.inputs[k].default_value = 1.0
            break
    tc = N.new('ShaderNodeTexCoord')
    n1 = N.new('ShaderNodeTexNoise')
    n1.inputs['Scale'].default_value = 6.0
    n1.inputs['Detail'].default_value = 2
    n2 = N.new('ShaderNodeTexNoise')
    n2.inputs['Scale'].default_value = 40.0
    n2.inputs['Detail'].default_value = 1
    for n in (n1, n2):
        Lk.new(tc.outputs['Object'], n.inputs['Vector'])
    mx = N.new('ShaderNodeMath')
    mx.operation = 'MULTIPLY_ADD'
    mx.inputs[1].default_value = .25
    Lk.new(n2.outputs['Fac'], mx.inputs[0])
    Lk.new(n1.outputs['Fac'], mx.inputs[2])
    bp = N.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = .025
    bp.inputs['Distance'].default_value = .01
    Lk.new(mx.outputs['Value'], bp.inputs['Height'])
    Lk.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


# ---------------- 形狀 ----------------
def axis_xy(V, z):
    return V['lean'][0] * z, V['lean'][1] * z


def out_r(V, z):
    H1 = V['H'][1]
    return V['R'] * (1 + .30 * math.exp(-max(z, 0.0) / .42)) * (1 - .03 * max(z, 0.0) / H1)


def in_r(V, z):
    return (V['R'] - V['W']) * (1 + .035 * math.sin(z * 2.3 + V['seed']))


def _adist(a, b):
    return abs((a - b + math.pi) % (2 * math.pi) - math.pi)


def top_h(V, phi, inner=False):
    """世界方位角 phi 處斷口頂的高度。鉸點那側高、有幾根斷刺；另一側低、朽爛。內壁比外殼低（心材朽得深）、斷刺短。"""
    H0, H1 = V['H']
    s = V['seed']
    d0 = _adist(phi, V['hinge'])
    v = H0 + .22 * (H1 - H0) * (.5 + .5 * math.cos(d0))
    v += .07 * fb((math.cos(phi) * 1.6, math.sin(phi) * 1.6, s), 1.0, 3) + .025 * fb((math.cos(phi) * 9, math.sin(phi) * 9, s + 4), 1.0, 2)
    vb = v
    for rel, wk, hk in V['teeth']:
        # 斷裂的木板：寬、頂上斜、邊緣鋸齒（不是一根根圓錐，第一版看起來像王冠）
        dd = (phi - V['hinge'] - rel + math.pi) % (2 * math.pi) - math.pi
        dt = abs(dd)
        if dt < wk:
            slab = _sm((wk - dt) / (.45 * wk))
            slope = 1 - .30 * (dd / wk) * (1 if rel >= 0 else -1)
            jag = 1 + .16 * fb((math.cos(phi) * 16, math.sin(phi) * 16, s + rel), 1.0, 2) + .10 * fb((math.cos(phi) * 45, math.sin(phi) * 45, s), 1.0, 1)
            v += (H1 - H0) * .82 * hk * slab * slope * jag
    if inner:
        # 第六輪：參考圖頂上是一圈寬、平的年輪台。以前內壁頂比外殼低 10–26 cm、往裡斜，從上面看斷面只剩一條窄帶
        v = vb - .035 - .06 * abs(fb((math.cos(phi) * 2.2, math.sin(phi) * 2.2, s + 7), 1.0, 2)) + (v - vb) * .40
    return v


def trunk_pts(V):
    H1 = V['H'][1]
    zs = [-.55, -.25, 0.0, .12, .28, .48, .75, 1.05] + list(np.linspace(1.4, H1 + .08, max(3, int((H1 + .08 - 1.4) / .45) + 1)))
    pts = []
    for z in zs:
        x, y = axis_xy(V, z)
        pts.append((x, y, z, out_r(V, z), 1.0))
    return pts


def inner_pts(V):
    H1 = V['H'][1]
    zf = V['pool'] - .18
    ri = in_r(V, zf + .6)
    pts = []
    for z, r in ((zf - .03, .10), (zf + .05, ri * .48), (zf + .22, ri * .82), (zf + .50, ri * .97)):
        x, y = axis_xy(V, z)
        pts.append((x, y, z, r, 1.0))
    for z in np.linspace(zf + .85, H1 + .08, max(3, int((H1 + .08 - zf - .85) / .4) + 1)):
        z = float(z)
        x, y = axis_xy(V, z)
        pts.append((x, y, z, in_r(V, z), 1.0))
    return pts


def ragged_top(V, ob, pts, inner=False):
    """最上面一段照方位角壓縮：管子頂端那圈落在 top_h(phi) 上。"""
    rings, nu, co = ring_info(ob, pts)
    zt = rings[-1][0].z
    z0 = V['H'][0] - (.55 if not inner else .9)
    for j in range(len(co)):
        z = co[j][2]
        if z <= z0:
            continue
        cx, cy = axis_xy(V, z)
        phi = math.atan2(co[j][1] - cy, co[j][0] - cx)
        ztop = top_h(V, phi, inner)
        co[j][2] = z0 + (z - z0) * (ztop - z0) / (zt - z0)
    ob.data.vertices.foreach_set('co', co.ravel())
    ob.data.update()
    return rings, nu, co


def top_ring(V, co, nu):
    """管子最上面那圈，照方位角重新排：從 hinge − π/2 開始逆時針（DR05 的洞口函式把「上半邊」當成 t≈0.25，就落在鉸點那側）。"""
    ring = [Vector(p) for p in co[-nu:]]
    c = sum(ring, Vector()) / len(ring)
    a0 = V['hinge'] - math.pi / 2
    ring.sort(key=lambda p: (math.atan2(p.y - c.y, p.x - c.x) - a0) % (2 * math.pi))
    return ring


def inner_fibres7(V, inner):
    """內壁一條條縱向的纖維束、溝（參考圖內壁是撕開的纖維，不是平的）：沿徑向推進推出，沿 Z 拉長的雜訊；水面以下不動。"""
    s = V['seed']
    for v in inner.data.vertices:
        z = v.co.z
        if z < V['pool'] + .05:
            continue
        cx, cy = axis_xy(V, z)
        d = Vector((v.co.x - cx, v.co.y - cy, 0))
        rr = d.length
        if rr < 1e-6:
            continue
        phi = math.atan2(d.y, d.x)
        cs, sn = math.cos(phi), math.sin(phi)
        a = .045 * fb((cs * 7, sn * 7, z * .35 + s), 1.0, 3) + .025 * fb((cs * 19, sn * 19, z * .9 + s + 3), 1.0, 2)
        a *= _sm((z - V['pool'] - .05) / .3)
        v.co = Vector((cx, cy, z)) + d * ((rr + a) / rr)
    inner.data.update()


def clear_inner7(V, trunk, inner, gap=.06):
    """內壁不能穿出外殼：從軸心水平打到外殼，離外殼不到 gap 的內壁頂點往軸心推回來。"""
    from mathutils.bvhtree import BVHTree
    me = trunk.data
    t = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
    n = 0
    for v in inner.data.vertices:
        cx, cy = axis_xy(V, v.co.z)
        c = Vector((cx, cy, v.co.z))
        d = v.co - c
        d.z = 0.0
        rr = d.length
        if rr < 1e-6:
            continue
        h = t.ray_cast(c, d / rr, 6)[0]
        if h is not None and (h - c).length < rr + gap:
            v.co = c + d * (((h - c).length - gap) / rr)
            n += 1
    inner.data.update()
    print('inner pushed in', n, 'of', len(inner.data.vertices))


def peel7(V, ob, pts, seed):
    """一兩大片剝皮（沿 Z 拉長）：壓回 0.93 r 的木頭面，點屬性 Peel。苔厚處、根頸以下不剝。"""
    rings, nu, co = ring_info(ob, pts)
    mo = vert_moss(ob.data)
    w = np.zeros(len(co))
    ph0 = V['hinge'] + math.pi * .62
    for k, (c, r, fl, s) in enumerate(rings):
        cc = np.array(c)
        for i in range(nu):
            j = k * nu + i
            z = co[j][2]
            if z < .45:
                continue
            d = co[j] - cc
            d[2] = 0
            rr = np.linalg.norm(d)
            if rr < 1e-6:
                continue
            dn = d / rr
            phi = math.atan2(dn[1], dn[0])
            pn = fb((math.cos(phi) * 1.4, math.sin(phi) * 1.4, z * .28 + seed), 1.0, 3) + .22 * fb(co[j] * 1.5, 1.0, 2)
            pn += .65 * (1 - _adist(phi, ph0) / 1.5)          # 一大片在鉸點對面偏一側
            pn += .75 * max(0.0, 1 - _adist(phi, V['hinge'] + .10) / .30) * _sm((z - V['H'][0] + 1.0) / .5)    # 最高的斷刺那條
            ww = _sm((pn - .34) / .08) * (1 - _sm((mo[j] - .15) / .25)) * _sm((z - .45) / .25)
            if ww <= 0:
                continue
            w[j] = ww
            co[j] = cc + dn * (rr * (1 - ww) + r * .93 * ww) + np.array((0, 0, co[j][2] - cc[2]))
    me = ob.data
    me.vertices.foreach_set('co', co.ravel())
    me.attributes.new('Peel', 'FLOAT', 'POINT').data.foreach_set('value', w.astype(np.float32))
    me.update()
    print('peel verts', int((w > .5).sum()), 'of', len(w))
    return w


def stump_moss(V):
    H0 = V['H'][0]

    def f(p, n):
        hi = _sm((p.z - (H0 - .75)) / .55)                      # 靠斷口上緣長一圈苔
        pat = fb((p.x * .7, p.y * .7, p.z * .35 + 3.0), 1.0, 3)
        collar = _sm((.75 - p.z) / .45)                         # 根頸一圈
        return .06 + .30 * hi * (.6 + pat) + .38 * max(0.0, n.z) + .26 * collar * (.5 + pat)
    return f


def roots(V, coll, R, mat):
    """根頸：nroots 條板根（扁度 1.4–1.9，立起來的板）從樹幹裡面長出，往外、往下扭著鑽進土裡；根間幾條細根。"""
    Rt = V['R']
    objs = []
    n = V['nroots']
    base = V['seed'] * .7
    for k in range(n):
        phi = base + 2 * math.pi * k / n + R.uniform(-.22, .22)
        sc = R.uniform(.72, 1.18)
        wob = R.uniform(-.38, .38)                                   # 第六輪：扭得多
        pts = []
        prof = ((.90, 1.0, .10, 1.0), (1.05, .68, .19, 1.4), (1.30, .35, .20, 1.8), (1.58, .14, .15, 1.6),      # 起點埋在殼壁裡（太裡面會穿進樹洞）
                (1.85, .00, .10, 1.3), (2.12 + .3 * (sc - 1), -.24, .065, 1.1), (2.32 + .35 * (sc - 1), -.60, .04, 1.0))
        for q, (rd, z, rr, fl) in enumerate(prof):
            a = phi + wob * (q / 6) ** 1.3 + .12 * math.sin(q * 1.7 + k) * (q / 6) + .05 * fb((k, q, base), 1.0, 2)      # 第六輪：蜿蜒
            rad = Rt * (rd if q < 2 else 1 + (rd - 1) * sc)
            zz = z * (1 if q < 3 else 1) + (.06 * R.uniform(-1, 1) if q > 2 else 0.0)
            cx, cy = axis_xy(V, max(zz, 0.0))
            pts.append((cx + math.cos(a) * rad, cy + math.sin(a) * rad, zz * (1 + .25 * (sc - 1)), Rt * rr * (.85 + .3 * sc) * (6.5 / n) ** .5, fl))      # 第六輪：根多了就細一點
        o = tube(f'Root{k}', pts, V['seed'] + 40 + k, rib=.20, twist=.22, collection=coll, moss_bias=.26)      # 第二輪：根的上面長苔；第六輪再加
        o.data.materials.append(mat)
        objs.append(o)
    # 根間的細根：貼地蜿蜒、半埋
    for k in range(n + 2):
        phi = base + 2 * math.pi * (k + .5) / n + R.uniform(-.3, .3)
        r0 = Rt * R.uniform(1.05, 1.25)
        pts = []
        for q in range(6):
            u = q / 5
            a = phi + .25 * math.sin(u * 3 + k) * u
            rad = r0 + Rt * (.25 + 1.0 * u) * R.uniform(.9, 1.1)
            cx, cy = axis_xy(V, 0.0)
            pts.append((cx + math.cos(a) * rad, cy + math.sin(a) * rad, .04 * (1 - u) - .16 * u, Rt * (.07 * (1 - .5 * u) + .012), 1.0))      # 半埋：只露上半
        o = tube(f'Rootlet{k}', pts, V['seed'] + 80 + k, rib=.15, twist=.3, collection=coll, moss_bias=.08)
        o.data.materials.append(mat)
        objs.append(o)
    return objs


def ground7(V, coll, lowpoly=False):
    """根間的土丘：根頸周圍隆起一點、往外收到地面以下，邊緣塞進地裡。"""
    Rt = V['R']
    nr, na = (10, 40) if lowpoly else (36, 160)
    vs, fs, mm = [], [], []
    r0, r1 = Rt * .80, Rt * 2.55
    for i in range(nr + 1):
        u = i / nr
        rad = r0 + (r1 - r0) * u
        for j in range(na):
            a = 2 * math.pi * j / na
            cx, cy = axis_xy(V, 0.0)
            x, y = cx + math.cos(a) * rad, cy + math.sin(a) * rad
            z = .16 * (1 - u) ** 1.6 + .035 * fb((x * 1.1, y * 1.1, 2.0), 1.0, 3) + .012 * fb((x * 5, y * 5, 1.0), 1.0, 2) - .06 * u ** 3
            vs.append((x, y, z))
            mm.append(max(0.0, .05 + .25 * fb((x * .6, y * .6, 3.0), 1.0, 2)))
    for i in range(nr):
        for j in range(na):
            a, b_ = i * na + j, i * na + (j + 1) % na
            fs.append((a, b_, b_ + na, a + na))
    me = bpy.data.meshes.new('Ground')
    me.from_pydata(vs, [], fs)
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.normal_update()
    if sum(f.normal.z for f in bm.faces) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    me.attributes.new('MudMoss', 'FLOAT', 'POINT').data.foreach_set('value', np.array(mm, np.float32))
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mud_material())
    return _obj('Ground', me, coll)


def pebbles(V, coll, R, n, sub=2):
    """根間的小石塊。"""
    Rt = V['R']
    bm = bmesh.new()
    for k in range(n):
        a = R.uniform(0, 2 * math.pi)
        rad = Rt * R.uniform(1.25, 2.1)
        cx, cy = axis_xy(V, 0.0)
        c = Vector((cx + math.cos(a) * rad, cy + math.sin(a) * rad, .0))
        s = R.uniform(.06, .17)
        tmp = bmesh.new()
        bmesh.ops.create_icosphere(tmp, subdivisions=sub, radius=1.0)
        for v in tmp.verts:
            d = v.co.copy()
            q = d * (1 + .28 * fb(d * 1.6 + Vector((k, 3, 0)), 1.0, 2))
            v.co = c + Vector((q.x * s * 1.2, q.y * s, q.z * s * .55 + s * .12))
        me_t = bpy.data.meshes.new('t')
        tmp.to_mesh(me_t)
        tmp.free()
        bm.from_mesh(me_t)
        bpy.data.meshes.remove(me_t)
    me = bpy.data.meshes.new('Stones')
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(stone_material())
    return _obj('Stones', me, coll)


def water7(V, coll, inner, lowpoly=False):
    """積水：水面一片圓盤，邊緣比內壁大一點（藏進殼裡）。"""
    z = V['pool']
    cx, cy = axis_xy(V, z)
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    t = BVHTree.FromObject(inner, dg)
    na = 24 if lowpoly else 96
    vs = [(cx, cy, z)]
    for j in range(na):
        a = 2 * math.pi * j / na
        d = Vector((math.cos(a), math.sin(a), 0))
        h = t.ray_cast(Vector((cx, cy, z)), d, 4)[0]
        rr = (h - Vector((cx, cy, z))).length + .05 if h else in_r(V, z)
        vs.append((cx + d.x * rr, cy + d.y * rr, z))
    fs = [(0, 1 + j, 1 + (j + 1) % na) for j in range(na)]
    me = bpy.data.meshes.new('Water')
    me.from_pydata(vs, [], fs)
    me.update()
    me.materials.append(water_material())
    return _obj('Water', me, coll)


def floor_z7(V, x, y):
    """樹洞底的泥地高度：水面下 0.10 m，靠內壁積高一點（碎屑堆在牆腳），中間微凹，照雜訊起伏幾公分。"""
    cx, cy = axis_xy(V, V['pool'])
    r = math.hypot(x - cx, y - cy) / max(.3, in_r(V, V['pool']) * .62)
    return (V['pool'] - .10 - .035 + .05 * min(1.0, r) ** 2
            + .022 * fb((x * 2.2, y * 2.2, V['seed'] + 13), 1.0, 3) + .008 * fb((x * 9, y * 9, V['seed']), 1.0, 2))


def floor7(V, coll, inner, lowpoly=False):
    """樹洞底：一層積了朽木屑、落葉的泥（使用者要「有水」「沒水」兩種：沒水時看得到這層；有水時隔著半透明水面看得到一點）。
    邊緣推進內壁 5 cm（藏起接縫）。點屬性 MudMoss：靠牆腳一圈斷斷續續的苔（水乾了以後牆腳長苔）。"""
    from mathutils.bvhtree import BVHTree
    z0 = V['pool'] - .10
    cx, cy = axis_xy(V, z0)
    t = BVHTree.FromObject(inner, bpy.context.evaluated_depsgraph_get())
    na, nr = (24, 3) if lowpoly else (96, 8)
    edge = []
    for j in range(na):
        a = 2 * math.pi * j / na
        d = Vector((math.cos(a), math.sin(a), 0))
        h = t.ray_cast(Vector((cx, cy, z0 + .02)), d, 4)[0]
        edge.append(((h - Vector((cx, cy, z0))).length if h else in_r(V, z0) * .7) + .05)
    vs, mm = [], []
    vs.append((cx, cy, floor_z7(V, cx, cy)))
    mm.append(0.0)
    for k in range(1, nr + 1):
        u = k / nr
        for j in range(na):
            a = 2 * math.pi * j / na
            x, y = cx + math.cos(a) * edge[j] * u, cy + math.sin(a) * edge[j] * u
            vs.append((x, y, floor_z7(V, x, y) + (.03 * _sm((u - .85) / .15))))
            mm.append(_sm((u - .70) / .25) * _sm((fb((math.cos(a) * 2.6, math.sin(a) * 2.6, V['seed'] + 21), 1.0, 2) + .10) / .25))
    fs = [(0, 1 + j, 1 + (j + 1) % na) for j in range(na)]
    for k in range(nr - 1):
        b0, b1 = 1 + k * na, 1 + (k + 1) * na
        for j in range(na):
            j2 = (j + 1) % na
            fs.append((b0 + j, b1 + j, b1 + j2, b0 + j2))
    me = bpy.data.meshes.new('Floor')
    me.from_pydata(vs, [], fs)
    me.update()
    me.attributes.new('MudMoss', 'FLOAT', 'POINT').data.foreach_set('value', np.array(mm, np.float32))
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mud_material())
    VAR['floor_r'] = sum(edge) / len(edge) - .05
    return _obj('Floor', me, coll)


def inner_moss7(V, inner):
    """內壁靠斷口那段長一點苔（點屬性 EndMoss）。"""
    co = np.array([v.co[:] for v in inner.data.vertices])
    w = np.zeros(len(co), np.float32)
    for j, p in enumerate(co):
        cx, cy = axis_xy(V, p[2])
        phi = math.atan2(p[1] - cy, p[0] - cx)
        d = top_h(V, phi, True) - p[2]
        pat = _sm((fb((math.cos(phi) * 3.0, math.sin(phi) * 3.0, p[2] * .8 + V['seed']), 1.0, 2) + .05) / .25)
        w[j] = max(0.0, 1 - d / .55) ** 1.5 * .55 * pat                  # 第二輪：一團團（第一輪沿上緣一條綠線）
    inner.data.attributes.new('EndMoss', 'FLOAT', 'POINT').data.foreach_set('value', w)


def rim_moss7(V, ob, rows):
    """斷面的苔：外緣一圈（不是只有「上半邊」）、照雜訊斷斷續續。"""
    me = ob.data
    nv = len(me.vertices)
    M = nv // (rows + 1)
    em = np.zeros(nv, np.float32)
    for vi, v in enumerate(me.vertices):
        u = (vi // M) / rows
        cx, cy = axis_xy(V, v.co.z)
        phi = math.atan2(v.co.y - cy, v.co.x - cx)
        pat = _sm((fb((math.cos(phi) * 2.2, math.sin(phi) * 2.2, V['seed'] + 5), 1.0, 2)
                   + .6 * fb((math.cos(phi) * 7, math.sin(phi) * 7, v.co.z * 2 + V['seed']), 1.0, 2) + .05) / .25)
        low = 1 - _sm((v.co.z - V['H'][0] - .15) / .3)           # 高的斷刺上不長
        em[vi] = .03 + .95 * pat * low * max(0.0, 1 - u / .45)     # 第二輪：靠外緣（樹皮那邊）一團團
    me.attributes['EndMoss'].data.foreach_set('value', em)


def splinters(V, coll, R, mat, outer_ring, inner_ring, n, lowpoly=False):
    """斷口上一根根撕裂的細長木刺（朝上、稍微往外散），鉸點那側多、長。Shard／ShardU 同 DR05 的木片（遊戲模型指到圖集色條）。"""
    bm = bmesh.new()
    shl = bm.faces.layers.int.new('Shard')
    sul = bm.verts.layers.float.new('ShardU')
    sec = ((-1, 0), (-.6, 1), (.6, 1), (1, 0), (.6, -1), (-.6, -1))
    ns = len(sec)
    no, ni = len(outer_ring), len(inner_ring)
    nseg = 5
    for q in range(n):
        t = (R.gauss(.25, .14) if R.random() < .75 else R.random()) % 1.0
        po = outer_ring[int(t * no) % no]
        pi = inner_ring[int(t * ni) % ni]
        u0 = R.uniform(.15, .80)
        base = po.lerp(pi, u0) - Vector((0, 0, R.uniform(.03, .08)))
        cx, cy = axis_xy(V, base.z)
        rad = Vector((base.x - cx, base.y - cy, 0)).normalized()
        tan = Vector((0, 0, 1)).cross(rad).normalized()
        near = max(0.0, 1 - _adist(math.atan2(rad.y, rad.x), V['hinge']) / 1.2)
        ln = R.uniform(.07, .20) * (1 + 1.0 * near) * (V['R'] / 1.25) ** .5      # 第二輪：短一點
        wd = R.uniform(.04, .10)                        # 扁的木條（太細像一根根刺）
        tk = R.uniform(.006, .011)
        lean = R.uniform(-.10, .30)
        rows = []
        p = base.copy()
        for s_ in range(nseg + 1):
            u = s_ / nseg
            d = (Vector((0, 0, 1)) + rad * (lean * (.4 + u)) + tan * R.uniform(-.06, .06)).normalized()
            if s_:
                p = p + d * (ln / nseg)
            nr = d.cross(tan).normalized()
            ww = wd * (1 - .85 * u ** 1.1) + .0015
            tt = tk * (1 - .6 * u) + .0015
            ring = []
            for sx, sy in sec:
                vv = bm.verts.new(p + tan * ww * sx + nr * tt * sy)
                vv[sul] = u
                ring.append(vv)
            rows.append(ring)
        for s_ in range(nseg):
            for k in range(ns):
                f = bm.faces.new((rows[s_][k], rows[s_][(k + 1) % ns], rows[s_ + 1][(k + 1) % ns], rows[s_ + 1][k]))
                f[shl] = 1
        for rr_ in (rows[0], rows[-1]):
            f = bm.faces.new(rr_)
            f[shl] = 1
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new('Splinters')
    bm.to_mesh(me)
    bm.free()
    me.attributes.new('EndMoss', 'FLOAT', 'POINT').data.foreach_set('value', np.zeros(len(me.vertices), np.float32))
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    return _obj('Splinters', me, coll)


def col_shell7(V, coll, sides=12):
    """碰撞：樹幹一個實心柱（到矮邊 0.92 高，頂上封平，掉不進樹洞）＋根頸一圈矮台（人可以踩上去）。"""
    Rt = V['R']
    vs, fs = [], []

    def ring(z, r):
        cx, cy = axis_xy(V, max(z, 0.0))
        return [(cx + math.cos(2 * math.pi * i / sides) * r, cy + math.sin(2 * math.pi * i / sides) * r, z) for i in range(sides)]

    def prism(r0, z0, r1, z1):
        b = len(vs)
        vs.extend(ring(z0, r0) + ring(z1, r1))
        for i in range(sides):
            i2 = (i + 1) % sides
            fs.append((b + i, b + i2, b + sides + i2, b + sides + i))
        fs.append(tuple(b + i for i in range(sides))[::-1])
        fs.append(tuple(b + sides + i for i in range(sides)))
    prism(out_r(V, .3) * .97, -.15, out_r(V, V['H'][0]) * .97, V['H'][0] * .92)
    prism(Rt * 1.55, -.15, Rt * 1.10, .38)
    me = bpy.data.meshes.new('Collision')
    me.from_pydata(vs, [], fs)
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    return _obj('Shell', me, coll)


def build(variant='A', quick=True, low=None, col=False, pre=''):
    """low=(step, numin, numax, nuk)：同一份路徑做不帶樹皮凹凸的低模；col=True：只做碰撞殼。"""
    V = set_variant(variant)
    CFG.update(step=.12 if quick else .05, numin=28 if quick else 48, numax=520, amp=.21, moss=.095, nuk=.8, crest=.40)
    if low:
        CFG.update(step=low[0], numin=low[1], numax=low[2], amp=0.0, moss=0.0, nuk=low[3])
    seed = V['seed']
    noise.seed_set(seed)
    R = random.Random(seed)
    coll = _coll(f"{PRE}_{V['name']}_{'Col' if col else ('Low' if low else 'High')}")
    if col:
        col_shell7(V, coll)
        return _finish_names(coll, pre)
    mat = bark7_material()
    rmat = rot7_material()
    objs = []
    tp = trunk_pts(V)
    trunk = tube('Trunk', tp, seed, rib=.24, twist=.22, collection=coll, moss_bias=stump_moss(V), cap_end=False)
    trunk.data.materials.append(mat)
    objs.append(trunk)
    if not low:
        peel7(V, trunk, tp, seed)
    else:
        trunk.data.attributes.new('Peel', 'FLOAT', 'POINT')
    rings_o, nu_o, co_o = ragged_top(V, trunk, tp)
    amp0, moss0 = CFG['amp'], CFG['moss']
    CFG.update(amp=amp0 * .5, moss=0.0)
    ip = inner_pts(V)
    inner = tube('Inner', ip, seed + 5, rib=.12, twist=.06, collection=coll, moss_bias=-1.0, cap_end=False)
    CFG.update(amp=amp0, moss=moss0)
    rings_i, nu_i, co_i = ragged_top(V, inner, ip, inner=True)
    if not low:
        inner_fibres7(V, inner)
    clear_inner7(V, trunk, inner)
    co_i = np.array([v.co[:] for v in inner.data.vertices])
    inner_moss7(V, inner)
    flip(inner)
    inner.data.materials.append(rmat)
    objs.append(inner)
    ro, ri = top_ring(V, co_o, nu_o), top_ring(V, co_i, nu_i)
    up = Vector((0, 0, 1))
    rm = rim(V, coll, 'Rim0', ro, ri, up, rmat, seed, lowpoly=bool(low))
    rim_moss7(V, rm, 15 if low else 22)
    objs.append(rm)
    objs.append(rim_flakes(V, coll, random.Random(seed + 30), rmat, 0, ro, ri, up,
                           n=(54 if not low else 40), lowpoly=False, trunk=trunk, n_sh=(26 if not low else 20)))
    objs.append(splinters(V, coll, random.Random(seed + 31), rmat, ro, ri, 18 if not low else 14))
    objs += roots(V, coll, random.Random(seed + 2), mat)
    objs.append(floor7(V, coll, inner, lowpoly=bool(low)))
    if WATER:
        objs.append(water7(V, coll, inner, lowpoly=bool(low)))
    objs.append(ground7(V, coll, lowpoly=bool(low)))
    objs.append(pebbles(V, coll, random.Random(seed + 6), 14, sub=1 if low else 2))
    print('BUILD', V['id'], 'low' if low else 'high', len(coll.objects), 'objects')
    return _finish_names(coll, pre)


def _views(V):
    H0, H1 = V['H']
    Rt = V['R']
    hx, hy = math.cos(V['hinge']), math.sin(V['hinge'])
    k = Rt / 1.25
    return {
        'tq': ((-6.0 * k, -7.4 * k, 1.7), (0, 0, H0 * .65), 30),
        'front': ((0, -9.5 * k, 1.5), (0, 0, H1 * .45), 30),
        'back': ((0, 9.5 * k, 1.8), (0, 0, H1 * .45), 30),
        'side': ((9.5 * k, 0, 1.5), (0, 0, H1 * .45), 30),
        'hinge': ((hx * 7.5 * k, hy * 7.5 * k, 1.7), (0, 0, H1 * .5), 30),
        'top': ((0, -.01, H1 + 9 * k), (0, 0, 0), 30),
        'into': ((-hx * 1.6 * k, -hy * 1.6 * k, H1 + 1.6 * k), (hx * .2, hy * .2, V['pool']), 26),
        'roots': ((-2.6 * k, -3.6 * k, .9), (0, -.6 * k, .3), 28),
        'rim': ((-hx * 2.4 * k, -hy * 2.4 * k, H1 + .4), (hx * .4 * k, hy * .4 * k, H0 + .2), 30),
    }


def _surf7(rings, s, ang):
    """給 DR06 的 brackets 用：樹樁直立，s 是高度、ang 是世界方位角；從軸心水平打到樹幹表面。"""
    V = VAR
    cx, cy = axis_xy(V, s)
    c = Vector((cx, cy, s))
    n = Vector((math.cos(ang), math.sin(ang), 0))
    r = out_r(V, s)
    t = bpy.data.objects.get('Trunk')
    if t is not None:
        from mathutils.bvhtree import BVHTree
        bv = _surf7.cache.get(t.name)
        if bv is None:
            bv = BVHTree.FromPolygons([v.co.copy() for v in t.data.vertices], [tuple(p.vertices) for p in t.data.polygons])
            _surf7.cache[t.name] = bv
        h = bv.ray_cast(c, n, 6)[0]
        if h is not None:
            r = (h - c).length
    return c, n, Vector((0, 0, 1)), r


_surf7.cache = {}


def dress(V, quick=True, seed=None, game=False, surf=('Trunk',)):
    """斷口和板根上的苔叢、斷口低處一叢小蕨；腳邊的蕨、闊葉草、蕈；根上的蕈；側面層狀菌；地上和水面上的落葉。"""
    seed = V['seed'] + 900 if seed is None else seed
    R = random.Random(seed)
    Rt, H0, H1 = V['R'], V['H'][0], V['H'][1]
    k = Rt / 1.25
    coll = _coll(f"{PRE}_{V['name']}_{'GamePlants' if game else 'Plants'}")
    lm = core_plants._leaf_material
    mat = lambda n, *a, **kw: bpy.data.materials.get(n) or lm(n, *a, **kw)
    fern_mat = mat('D2_Fern', (.050, .090, .040, 1), (.11, .17, .075, 1), (.16, .22, .11, 1), gloss=.55)
    heart_mat = mat('D2_HeartLeafPale', (.060, .105, .050, 1), (.135, .20, .10, 1), (.22, .29, .16, 1), gloss=.4)
    moss_mat = mat('D2_MossTuft', (.040, .058, .014, 1), (.10, .125, .032, 1), (.12, .15, .045, 1), gloss=.8)
    litter_mat = mat('DR06_LitterLeaf', (.15, .07, .022, 1), (.42, .22, .07, 1), (.48, .30, .11, 1), gloss=.3)
    stem_mat = bpy.data.materials.get('D2_Stem')
    if stem_mat is None:
        stem_mat = bpy.data.materials.new('D2_Stem')
        stem_mat.use_nodes = True
        next(n for n in stem_mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Base Color'].default_value = (.05, .06, .025, 1)
    mush_mat = bpy.data.materials.get('UG_Mushroom') or core_plants.mushroom_material()
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()

    def base(nm):
        return nm.split('_', 1)[1] if nm.startswith(('L_', 'C_', 'F_')) else nm

    def cat(loc, nm):
        """打到的是哪一種面。高模照物件名；遊戲模型（全部併成一件）照位置判斷。"""
        nm = base(nm)
        if not game:
            return nm
        cx, cy = axis_xy(V, max(loc.z, 0.0))
        rr = math.hypot(loc.x - cx, loc.y - cy)
        if loc.z > H0 - .40 and rr < out_r(V, loc.z) * 1.03:
            return 'Rim0'
        if rr > Rt * 1.25 and loc.z < .10:
            return 'Ground'
        if rr < in_r(V, loc.z) * 1.02 and loc.z < V['pool'] + .25:
            return 'Floor'
        return 'Root'

    def hit(x, y, z0=H1 + 2.0):
        ok, loc, nrm, _, ob, _ = sc.ray_cast(dg, Vector((x, y, z0)), Vector((0, 0, -1)))
        return (loc, nrm, cat(loc, ob.name)) if ok else None

    def keep(o):
        for c in list(o.users_collection):
            c.objects.unlink(o)
        coll.objects.link(o)
        return o

    def polar(r0, r1):
        a = R.uniform(0, 2 * math.pi)
        rr = Rt * R.uniform(r0, r1)
        cx, cy = axis_xy(V, 0.0)
        return cx + math.cos(a) * rr, cy + math.sin(a) * rr, a

    out = []
    mounds = []
    for i in range(int(90 * k)):
        x, y, a = polar(.70, 2.0)
        h = hit(x, y)
        if not h or h[1].z < .7:
            continue
        nm = h[2]
        if nm.startswith('Rim') and h[0].z < H0 + .25 or nm.startswith('Root') and R.random() < .55:
            mounds.append((i, h[0].x, h[0].y, R.uniform(.10, .24) * k, R.uniform(.08, .16) * k, R.uniform(.02, .05), h[0].z - .02))
    if mounds and not game:
        out.append(keep(core_plants.moss_tufts('DR07_MossTufts', mounds, R, moss_mat, fb, density=2600 if quick else 5200)))
    # 斷口低處一兩叢小蕨（參考圖斷口上長苔和小植物）
    nf = 0
    for i in range(60):
        if nf >= 2:
            break
        x, y, a = polar(.78, .98)
        if _adist(a, V['hinge']) < 1.6:
            continue
        h = hit(x, y)
        if h and h[2].startswith(('Rim', 'Trunk')) and h[1].z > .6:
            o, so = core_plants.fern(f'DR07_TopFern{nf}', h[0] - Vector((0, 0, .03)), R, R.uniform(.45, .65) * k, fern_mat, stem_mat)
            out += [keep(o), keep(so)]
            nf += 1
    # 腳邊：根和根之間的地上
    nf = 0
    for i in range(80):
        if nf >= 5:
            break
        x, y, a = polar(1.35, 2.5)
        h = hit(x, y)
        if h and h[2] in ('Ground',) and h[1].z > .8:
            o, so = core_plants.fern(f'DR07_FootFern{nf}', h[0] - Vector((0, 0, .02)), R, R.uniform(.85, 1.25) * k, fern_mat, stem_mat)
            out += [keep(o), keep(so)]
            nf += 1
    nh = 0
    for i in range(60):
        if nh >= 3:
            break
        x, y, a = polar(1.5, 2.6)
        h = hit(x, y)
        if h and h[2] == 'Ground':
            o = core_plants.heart_plant(f'DR07_Heart{nh}', h[0] - Vector((0, 0, .01)), R, R.uniform(.65, .95) * k, heart_mat, stem_mat)
            out.append(keep(o))
            so = bpy.data.objects.get(f'DR07_Heart{nh}_stem')
            if so:
                out.append(keep(so))
            nh += 1
    nm_ = 0
    for i in range(120):
        if nm_ >= 6:
            break
        x, y, a = polar(1.0, 2.3)
        h = hit(x, y)
        if not h or h[1].z < .55:
            continue
        on_root = h[2].startswith('Root')
        if (on_root and nm_ < 2) or (h[2] == 'Ground' and nm_ >= 2):
            out.append(keep(core_plants.mushrooms(f'DR07_Mush{nm_}', h[0] - Vector((0, 0, .015)), R, R.randint(4, 9), 2.2 * k, mush_mat, cap=MUSH_CAP)))
            nm_ += 1
    # 側面層狀菌（DR06 的 brackets，位置改用樹樁的直立座標）
    g = globals()
    old = g.get('surf')
    g['surf'] = _surf7
    _surf7.cache.clear()
    try:
        out.append(keep(brackets(V, coll, random.Random(seed + 4), [], core_plants.mushroom_material())))
    finally:
        g['surf'] = old
    fr = V.get('floor_r', in_r(V, V['pool']) * .7)

    def place():
        if R.random() < .09:                                     # 樹洞底泥地上的落葉（沒水時看得到；有水時沉在水底。不再浮在水面上：水面另存一個模型）
            cx, cy = axis_xy(V, V['pool'])
            a = R.uniform(0, 2 * math.pi)
            rr = fr * R.uniform(0, 1) ** .5 * .92
            x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
            return (x, y), floor_z7(V, x, y) + .004
        x, y, a = polar(1.05, 3.3)
        h = hit(x, y)
        if h and h[2] in ('Ground', 'Stones') or h and h[2].startswith('Rootlet'):
            return (x, y), h[0].z
        if h is None or h[0].z < .02:
            return (x, y), 0.0
        return None
    lo, n = litter('DR07_Litter', R, int(520 * k * (.6 if quick else 1.0)), place, litter_mat)
    out.append(keep(lo))
    print('DRESS', len(out), 'plant objects, litter', n)
    return coll


if __name__ == '__main__' and '--' in sys.argv:
    args = sys.argv[sys.argv.index('--') + 1:]
    var = args[0] if args else 'A'
    quick = (args[1] if len(args) > 1 else 'quick') == 'quick'
    outdir = args[2] if len(args) > 2 else 'D:/yun-jing-cache/dr07-work'
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
        hum.location = (VAR['R'] * 2.4, -VAR['R'] * 1.2, .875)
    want = args[3].split(',') if len(args) > 3 else list(_views(VAR))
    for k in want:
        loc, tgt, lens = _views(VAR)[k]
        preview_dr.shot(os.path.join(outdir, f"DR07_{var}_{k}.png"), loc, tgt, lens, (1280, 720))
    for a_ in args[4:]:
        if a_.endswith('.blend'):
            bpy.ops.wm.save_as_mainfile(filepath=a_)
