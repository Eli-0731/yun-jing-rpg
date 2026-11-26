# D2 根與木（B 包 11/15）共用：掃描樹皮推進幾何的管子、樹皮材質。
# 樹皮做法與核心組 art/source/core-d2-v1/godtree/godtree_base.py 相同（同一組掃描圖、同樣的 TILE／AMP），
# 這樣根拱、根牆和神木擺在一起是同一種樹皮。差別：斷面座標用平行移動（拱頂不會翻面）、
# 路徑每個控制點自帶半徑與扁度、苔有厚度。
#
# 掃描貼圖不放進 repo：Poly Haven bark_brown_02、jolcham_oak_bark_01（CC0），2k，
# 放在環境變數 DR_TEX 指的資料夾（預設 D:/yun-jing-cache/polyhaven-bark/）。
import bpy, bmesh, math, os, numpy as np
from mathutils import Vector, noise

TEX = os.environ.get('DR_TEX', 'D:/yun-jing-cache/polyhaven-bark/')
SET = 'bark_brown_02'
TILE = 2.6      # 一張掃描圖蓋多大 (m)，和神木一致
CFG = dict(step=0.10, amp=0.16, numin=40, moss=0.085)

_IMG = {}


def img(n, cs='Non-Color', set_=None):
    set_ = set_ or SET
    key = (set_, n)
    if key not in _IMG or _IMG[key].name not in bpy.data.images:
        for ext in ('png', 'jpg'):
            p = TEX + f'{set_}_{n}_2k.{ext}'
            if os.path.exists(p):
                i = bpy.data.images.load(p, check_existing=True)
                i.colorspace_settings.name = cs
                _IMG[key] = i
                break
        else:
            raise FileNotFoundError(TEX + f'{set_}_{n}_2k')
    return _IMG[key]


_DP = None


def _disp():
    global _DP
    if _DP is None:
        d = img('disp')
        w, h = d.size
        a = np.empty(w * h * d.channels, dtype=np.float32)
        d.pixels.foreach_get(a)
        _DP = a.reshape(h, w, -1)[:, :, 0].copy()
    return _DP


def sdisp_row(u, v):
    """u: numpy array, v: scalar。雙線性取掃描凹凸。"""
    dp = _disp()
    h, w = dp.shape
    x = (u % 1.0) * w
    y = (v % 1.0) * h
    x0 = np.floor(x).astype(np.int64) % w
    x1 = (x0 + 1) % w
    fx = x - np.floor(x)
    y0 = int(y) % h
    y1 = (y0 + 1) % h
    fy = y - int(y)
    return (dp[y0, x0] * (1 - fx) + dp[y0, x1] * fx) * (1 - fy) + (dp[y1, x0] * (1 - fx) + dp[y1, x1] * fx) * fy


def fb(p, s, o=4):
    return noise.fractal(Vector(p) * s, 1.0, 2.0, o, noise_basis='PERLIN_ORIGINAL')


def _cr(p0, p1, p2, p3, t):
    return .5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)


def resample(pts, step):
    """pts: [(x, y, z, r, flat)]，回傳等距的 [(Vector, r, flat, s)] 與總長。"""
    P = [np.array(p, dtype=np.float64) for p in pts]
    n = len(P)
    spl = []
    for i in range(n - 1):
        a, b, c, d = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, n - 1)]
        for k in range(24):
            spl.append(_cr(a, b, c, d, k / 24))
    spl.append(P[-1])
    spl = np.array(spl)
    seg = np.linalg.norm(np.diff(spl[:, :3], axis=0), axis=1)
    L = np.concatenate([[0], np.cumsum(seg)])
    tot = float(L[-1])
    nv = max(2, int(tot / step))
    out = []
    for k in range(nv + 1):
        s = tot * k / nv
        j = min(int(np.searchsorted(L, s, side='right')) - 1, len(L) - 2)
        f = (s - L[j]) / max(L[j + 1] - L[j], 1e-9)
        q = spl[j] * (1 - f) + spl[j + 1] * f
        out.append((Vector(q[:3]), max(float(q[3]), .012), max(float(q[4]), .3), s))
    return out, tot


def tube(name, pts, seed, rib=.22, twist=.12, nu=None, collection=None, moss_bias=0.0, cap_end=True):
    """把一條路徑做成帶掃描樹皮凹凸的根。pts: [(x, y, z, 半徑, 扁度)]，扁度 >1 是立起來的板根。
    頂點色 Mask：R 苔、G 掃描高度（低＝裂溝）、B 粗稜溝。UV 層 'UV' 是每 TILE 公尺重複的樹皮 UV。"""
    step, amp = CFG['step'], CFG['amp']
    rings, tot = resample(pts, step)
    nv = len(rings) - 1
    rmax = max(r * max(1.0, fl) for _, r, fl, _ in rings)
    if nu is None:
        nu = int(min(CFG.get('numax', 520), max(CFG['numin'], 2 * math.pi * rmax / step * CFG.get('nuk', .8))))
    rep = max(1, round(2 * math.pi * max(r for _, r, _, _ in rings) * .8 / TILE))
    th = np.arange(nu) * (2 * math.pi / nu)
    cs, sn = np.cos(th), np.sin(th)
    uu = np.arange(nu) / nu * rep
    # 平行移動座標：拱頂、鑽地處不會突然翻轉
    tans = []
    for k in range(nv + 1):
        a = rings[min(k + 1, nv)][0] - rings[max(k - 1, 0)][0]
        tans.append(a.normalized())
    side = tans[0].cross(Vector((0, 0, 1)))
    if side.length < 1e-3:
        side = tans[0].cross(Vector((1, 0, 0)))
    side.normalize()
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UV')
    uvp = bm.loops.layers.uv.new('Param')        # (繞一圈 0–1, 沿長度公尺)：給烘焙用的 UV 拆島
    col = bm.loops.layers.color.new('Mask')
    fring = bm.faces.layers.int.new('ring')
    V, M = [], []
    for k, (c, r, fl, s) in enumerate(rings):
        a = tans[k]
        side = (side - a * side.dot(a)).normalized()
        up = side.cross(a).normalized()
        if k == 0:
            # 讓 up 盡量朝上，苔才長在上面
            if up.z < 0:
                side, up = -side, -up
        tw = s * twist + seed
        v = s / TILE
        d = sdisp_row(uu, v) - .5
        crest = CFG.get('crest', .40) * max(0.0, min(1.0, (fl - 1.12) / .4))      # 板根（扁度 > 1.12）：上半邊收窄成一道脊
        row, rm = [], []
        for i in range(nu):
            ct, st = cs[i], sn[i]
            r1 = fb((math.cos(th[i] + tw) * 2.0, math.sin(th[i] + tw) * 2.0, s * .10 + seed), 1.0, 3)
            r2 = abs(fb((math.cos(th[i] + tw * 1.4) * 4.5, math.sin(th[i] + tw * 1.4) * 4.5, s * .22 + seed * 3), 1.0, 2))
            lump = fb((c.x * .35, c.y * .35 + th[i] * .3, c.z * .35 + seed), 1.0, 2)
            rr = r * (1 + (rib * r1 - rib * .8 * r2) / fl ** 1.5 + .08 * lump)
            di = float(d[i])
            rr += di * amp * min(1.0, r / .4 + .3)
            wd = 1 - crest * max(0.0, st) ** 1.3 if crest else 1.0      # 底下寬、頂上窄，不是立起來的橢圓
            d3 = side * (ct * rr * wd) + up * (st * rr * fl)
            p = c + d3
            nrm = (side * (ct * fl) + up * st).normalized()
            mo = nrm.z * .55 + fb(p, .45, 3) * .65 + fb(p, 2.5, 3) * .30 - di * .5 - r2 * .25 + (moss_bias(p, nrm) if callable(moss_bias) else moss_bias)
            mo = max(0.0, min(1.0, (mo - .44) / .20))
            mo = mo * mo * (3 - 2 * mo)
            if mo > 0 and CFG['moss'] > 0:
                # 苔有厚度：一塊一塊鼓起來，表面有小起伏
                # 苔墊：一團一團鼓起來（15–30 cm 的團塊），邊緣薄、中間厚
                p = p + nrm * (mo * CFG['moss'] * (.55 + .45 * abs(fb(p, 5.0, 3)) * 2 + .25 * fb(p, 14.0, 2)))
            row.append(bm.verts.new(p))
            rm.append((mo, max(0.0, min(1.0, di * 2 + .5)), max(0.0, min(1.0, r2)), 1.0))
        V.append(row)
        M.append(rm)
    for k in range(nv):
        v0, v1 = rings[k][3] / TILE, rings[k + 1][3] / TILE
        for i in range(nu):
            i2 = (i + 1) % nu
            f = bm.faces.new((V[k][i], V[k][i2], V[k + 1][i2], V[k + 1][i]))
            u0 = uu[i]
            u1 = rep if i2 == 0 else uu[i2]
            lp = f.loops
            f[fring] = k
            lp[0][uvp].uv = (i / nu, rings[k][3])
            lp[1][uvp].uv = ((i + 1) / nu, rings[k][3])
            lp[2][uvp].uv = ((i + 1) / nu, rings[k + 1][3])
            lp[3][uvp].uv = (i / nu, rings[k + 1][3])
            lp[0][uvl].uv = (u0, v0)
            lp[1][uvl].uv = (u1, v0)
            lp[2][uvl].uv = (u1, v1)
            lp[3][uvl].uv = (u0, v1)
            lp[0][col] = M[k][i]
            lp[1][col] = M[k][i2]
            lp[2][col] = M[k + 1][i2]
            lp[3][col] = M[k + 1][i]
            f.smooth = True
    if cap_end:
        for row, rm, flip in ((V[0], M[0], True), (V[-1], M[-1], False)):
            f = bm.faces.new(row[::-1] if flip else row)
            f[fring] = -1
            for lp in f.loops:
                lp[uvl].uv = (0, 0)
                lp[uvp].uv = (0, 0)
                lp[col] = (0, .2, 0, 1)
    bmesh.ops.reverse_faces(bm, faces=bm.faces[:])      # 面法線朝外
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob['ring_r'] = [r * (1 + fl) / 2 for _, r, fl, _ in rings]
    ob['ring_s'] = [s for _, _, _, s in rings]
    (collection or bpy.context.scene.collection).objects.link(ob)
    return ob


def bark_material(name='D2RootBark'):
    """掃描樹皮＋降飽和灰化＋裂溝壓暗＋凸起處地衣＋朝上處苔（和神木同一套）。"""
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, Lk = m.node_tree.nodes, m.node_tree.links
    b = next(n for n in N if n.type == 'BSDF_PRINCIPLED')

    def tx(n, cs='Non-Color'):
        t = N.new('ShaderNodeTexImage')
        t.image = img(n, cs)
        return t

    def ramp(p0, p1, c0=None, c1=None):
        r = N.new('ShaderNodeValToRGB')
        e = r.color_ramp.elements
        e[0].position, e[1].position = p0, p1
        if c0:
            e[0].color = c0
        if c1:
            e[1].color = c1
        return r

    def mix(kind='MIX', fac=None):
        x = N.new('ShaderNodeMixRGB')
        x.blend_type = kind
        if fac is not None:
            x.inputs[0].default_value = fac
        return x

    dif, nor, rgh, ao = tx('diff', 'sRGB'), tx('nor_gl'), tx('rough'), tx('ao')
    vc = N.new('ShaderNodeVertexColor')
    vc.layer_name = 'Mask'
    sep = N.new('ShaderNodeSeparateColor')
    Lk.new(vc.outputs['Color'], sep.inputs[0])
    hsv = N.new('ShaderNodeHueSaturation')
    hsv.inputs['Saturation'].default_value = .60
    hsv.inputs['Value'].default_value = 1.5
    Lk.new(dif.outputs[0], hsv.inputs['Color'])
    tint = mix('MULTIPLY', 1.0)
    tint.inputs[2].default_value = (1.0, .90, .84, 1)
    Lk.new(hsv.outputs[0], tint.inputs[1])
    aom = mix('MULTIPLY', .9)
    Lk.new(tint.outputs[0], aom.inputs[1])
    Lk.new(ao.outputs[0], aom.inputs[2])
    crev = ramp(.15, .55, (.35, .35, .35, 1), (1, 1, 1, 1))
    Lk.new(sep.outputs[1], crev.inputs[0])
    cm = mix('MULTIPLY', 1.0)
    Lk.new(aom.outputs[0], cm.inputs[1])
    Lk.new(crev.outputs[0], cm.inputs[2])
    nz = N.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 5.0
    nz.inputs['Detail'].default_value = 9
    nz.inputs['Roughness'].default_value = .62
    ltc = N.new('ShaderNodeTexCoord')
    Lk.new(ltc.outputs['Object'], nz.inputs['Vector'])      # 公尺：斑塊約 20–50 cm
    lr = ramp(.60, .65)
    Lk.new(nz.outputs[0], lr.inputs[0])
    lm = N.new('ShaderNodeMath')
    lm.operation = 'MULTIPLY'
    Lk.new(lr.outputs[0], lm.inputs[0])
    lg = ramp(.24, .56, (.40, .40, .40, 1), (.82, .82, .82, 1))        # 地衣只在凸起處，而且是半透的一層
    Lk.new(sep.outputs[1], lg.inputs[0])
    Lk.new(lg.outputs[0], lm.inputs[1])
    lmx = mix()
    lmx.inputs[2].default_value = (.36, .42, .40, 1)      # 灰藍白地衣斑
    Lk.new(lm.outputs[0], lmx.inputs[0])
    Lk.new(cm.outputs[0], lmx.inputs[1])
    mn = N.new('ShaderNodeTexVoronoi')            # 苔的小團粒（2–3 cm）
    mn.inputs['Scale'].default_value = 55
    mn.inputs['Randomness'].default_value = 1.0
    mn2 = N.new('ShaderNodeTexNoise')
    mn2.inputs['Scale'].default_value = 6
    mn2.inputs['Detail'].default_value = 6
    mc = ramp(.3, .7, (.027, .034, .011, 1), (.092, .102, .034, 1))
    Lk.new(mn2.outputs[0], mc.inputs[0])
    mcd = mix('MULTIPLY', .7)
    mdr = ramp(.0, .45, (1, 1, 1, 1), (.45, .5, .4, 1))      # 團粒之間的縫暗一點
    Lk.new(mn.outputs['Distance'], mdr.inputs[0])
    Lk.new(mc.outputs[0], mcd.inputs[1])
    Lk.new(mdr.outputs[0], mcd.inputs[2])
    mr = ramp(.40, .62)
    Lk.new(sep.outputs[0], mr.inputs[0])
    mx = mix()
    Lk.new(mr.outputs[0], mx.inputs[0])
    Lk.new(lmx.outputs[0], mx.inputs[1])
    Lk.new(mcd.outputs[0], mx.inputs[2])
    Lk.new(mx.outputs[0], b.inputs['Base Color'])
    nm = N.new('ShaderNodeNormalMap')
    nm.inputs['Strength'].default_value = 1.5
    Lk.new(nor.outputs[0], nm.inputs['Color'])
    bp = N.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 1.0
    bp.inputs['Distance'].default_value = .02
    bp.invert = True
    mb = N.new('ShaderNodeMath')
    mb.operation = 'MULTIPLY'
    Lk.new(mn.outputs['Distance'], mb.inputs[0])
    Lk.new(mr.outputs[0], mb.inputs[1])
    Lk.new(mb.outputs[0], bp.inputs['Height'])
    Lk.new(nm.outputs[0], bp.inputs['Normal'])
    Lk.new(bp.outputs[0], b.inputs['Normal'])
    rmx = mix()
    rmx.inputs[2].default_value = (.95, .95, .95, 1)
    Lk.new(mr.outputs[0], rmx.inputs[0])
    Lk.new(rgh.outputs[0], rmx.inputs[1])
    Lk.new(rmx.outputs[0], b.inputs['Roughness'])
    return m
