# 來源：核心組 art/source/core-d2-v1/ground/plants.py（art/core-1114-d2-altar-terrace，2026-11-16），原樣複製，
# 讓 DR 系列的蕨、心形葉和 D2 林下範本長得一樣。只加了這兩行說明。
# D2 林下植物（核心組範本）：大蕨叢、心形葉植物、單片落葉——都是一片片立體葉，不用葉片卡
#   由 floor_tile.py exec；需要 bpy, math, random(R), Vector, np
import bpy, math, random
import numpy as np
from mathutils import Vector, Matrix


def _leaf_material(name, base_dark, base_light, vein, gloss=.45):
    """葉片材質：UV（u 沿葉長 0–1、v 橫向 0–1）畫中脈、側脈、葉緣變暗、隨機深淺；頂點色 Tint 乘上去。"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    b = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    tc = N.new('ShaderNodeTexCoord')
    sp = N.new('ShaderNodeSeparateXYZ')
    L.new(tc.outputs['UV'], sp.inputs[0])
    # 中脈：|v-0.5| 小
    mid = N.new('ShaderNodeMath'); mid.operation = 'SUBTRACT'; mid.inputs[1].default_value = .5
    L.new(sp.outputs['Y'], mid.inputs[0])
    ab = N.new('ShaderNodeMath'); ab.operation = 'ABSOLUTE'
    L.new(mid.outputs[0], ab.inputs[0])
    midr = N.new('ShaderNodeMapRange'); midr.inputs['From Min'].default_value = 0; midr.inputs['From Max'].default_value = .045
    midr.inputs['To Min'].default_value = 1; midr.inputs['To Max'].default_value = 0
    L.new(ab.outputs[0], midr.inputs['Value'])
    # 側脈：沿 u 加上 |v-.5| 的斜線週期
    sv = N.new('ShaderNodeMath'); sv.operation = 'MULTIPLY_ADD'; sv.inputs[1].default_value = .9
    L.new(ab.outputs[0], sv.inputs[0]); L.new(sp.outputs['X'], sv.inputs[2])
    wv = N.new('ShaderNodeMath'); wv.operation = 'MULTIPLY'; wv.inputs[1].default_value = 7 * 2 * math.pi
    L.new(sv.outputs[0], wv.inputs[0])
    sn = N.new('ShaderNodeMath'); sn.operation = 'SINE'
    L.new(wv.outputs[0], sn.inputs[0])
    svr = N.new('ShaderNodeMapRange'); svr.inputs['From Min'].default_value = .82; svr.inputs['From Max'].default_value = 1
    L.new(sn.outputs[0], svr.inputs['Value'])
    # 葉緣變暗：|v-.5| 大
    edg = N.new('ShaderNodeMapRange'); edg.inputs['From Min'].default_value = .3; edg.inputs['From Max'].default_value = .5
    L.new(ab.outputs[0], edg.inputs['Value'])
    # 斑駁
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 9; nz.inputs['Detail'].default_value = 6
    L.new(tc.outputs['UV'], nz.inputs['Vector'])
    base = N.new('ShaderNodeMixRGB'); base.inputs[1].default_value = base_dark; base.inputs[2].default_value = base_light
    L.new(nz.outputs['Fac'], base.inputs[0])
    vm = N.new('ShaderNodeMath'); vm.operation = 'MAXIMUM'
    L.new(midr.outputs[0], vm.inputs[0]); L.new(svr.outputs[0], vm.inputs[1])
    vmix = N.new('ShaderNodeMixRGB'); vmix.inputs[2].default_value = vein
    vf = N.new('ShaderNodeMath'); vf.operation = 'MULTIPLY'; vf.inputs[1].default_value = .55
    L.new(vm.outputs[0], vf.inputs[0])
    L.new(vf.outputs[0], vmix.inputs[0]); L.new(base.outputs[0], vmix.inputs[1])
    emix = N.new('ShaderNodeMixRGB'); emix.blend_type = 'MULTIPLY'; emix.inputs[2].default_value = (.55, .5, .45, 1)
    L.new(edg.outputs[0], emix.inputs[0]); L.new(vmix.outputs[0], emix.inputs[1])
    vc = N.new('ShaderNodeVertexColor'); vc.layer_name = 'Tint'
    tint = N.new('ShaderNodeMixRGB'); tint.blend_type = 'MULTIPLY'; tint.inputs[0].default_value = 1
    L.new(emix.outputs[0], tint.inputs[1]); L.new(vc.outputs[0], tint.inputs[2])
    L.new(tint.outputs[0], b.inputs['Base Color'])
    bp = N.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = .5; bp.inputs['Distance'].default_value = .002
    inv = N.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1
    L.new(vm.outputs[0], inv.inputs[1]); L.new(inv.outputs[0], bp.inputs['Height'])
    L.new(bp.outputs[0], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = gloss
    try:
        b.inputs['Subsurface Weight'].default_value = .08
    except Exception:
        pass
    out = next(n for n in N if n.type == 'OUTPUT_MATERIAL')
    tr = N.new('ShaderNodeBsdfTranslucent')
    L.new(tint.outputs[0], tr.inputs['Color'])
    mx = N.new('ShaderNodeMixShader'); mx.inputs['Fac'].default_value = .15
    L.new(b.outputs[0], mx.inputs[1]); L.new(tr.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs['Surface'])
    return m


class LeafBuf:
    """累積葉片：每片是一個 (NU×NV) 小網格，帶 UV 與 Tint。"""
    def __init__(self):
        self.V, self.F, self.UV, self.C = [], [], [], []

    def leaf(self, origin, along, side, up, L, W, shape, fold=.3, curl=0.0, droop=0.0, tint=(1, 1, 1), nu=7, nv=4, twist=0.0):
        """shape(u)->半寬比例；fold 沿中脈對折；curl 葉緣捲；droop 葉尖下垂；twist 沿長度扭轉。"""
        base = len(self.V)
        for i in range(nu + 1):
            u = i / nu
            hw = W * shape(u)
            for j in range(nv + 1):
                v = j / nv
                s = (v - .5) * 2
                x = s * hw
                z = abs(s) * hw * fold + (s * s) * hw * curl - droop * u * u * L
                ang = twist * u
                xr = x * math.cos(ang) - z * math.sin(ang)
                zr = x * math.sin(ang) + z * math.cos(ang)
                p = origin + along * (u * L) + side * xr + up * zr
                self.V.append(tuple(p))
                self.UV.append((u, v))
                self.C.append((tint[0], tint[1], tint[2], 1))
        for i in range(nu):
            for j in range(nv):
                a = base + i * (nv + 1) + j
                self.F.append((a, a + 1, a + nv + 2, a + nv + 1))

    def build(self, name, mat):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.V, [], self.F)
        uv = me.uv_layers.new(name='UVMap')
        idx = np.empty(len(me.loops), np.int32)
        me.loops.foreach_get('vertex_index', idx)
        uvs = np.array(self.UV, np.float32)[idx]
        uv.data.foreach_set('uv', uvs.ravel())
        ca = me.color_attributes.new('Tint', 'FLOAT_COLOR', 'POINT')
        ca.data.foreach_set('color', np.array(self.C, np.float32).ravel())
        for p in me.polygons:
            p.use_smooth = True
        me.materials.append(mat)
        o = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(o)
        return o


def _frame(d):
    d = d.normalized()
    up = Vector((0, 0, 1))
    side = d.cross(up)
    if side.length < 1e-4:
        side = Vector((1, 0, 0))
    side.normalize()
    nrm = side.cross(d).normalized()
    return d, side, nrm


# ---------------- 大蕨叢：8–14 片羽狀複葉，葉軸拱起垂下，羽片由基部往梢變短 ----------------
def fern(name, pos, R, size=1.0, mat=None, stem_mat=None):
    buf = LeafBuf()
    stems = []
    nf = R.randint(12, 18)
    for f in range(nf):
        az = 2 * math.pi * f / nf + R.uniform(-.25, .25)
        Lf = size * R.uniform(.55, 1.0)
        rise = R.uniform(.55, .9)
        pts = []
        n = 14
        for k in range(n + 1):
            t = k / n
            hz = math.sin(t * math.pi * .6) * rise * Lf * .85 - t ** 2.2 * Lf * .5
            r = t * Lf * .95
            pts.append(Vector((pos.x + math.cos(az) * r, pos.y + math.sin(az) * r, pos.z + hz)))
        stems.append(pts)
        npin = R.randint(34, 44)
        for k in range(2, npin):
            t = k / npin
            i = min(n - 1, int(t * n))
            p = pts[i].lerp(pts[i + 1], t * n - i)
            d = (pts[i + 1] - pts[i]).normalized()
            d, side, nrm = _frame(d)
            plen = Lf * .16 * (1 - t) ** .6 * (.45 + .55 * min(1, t * 5))
            for sgn in (-1, 1):
                pd = (side * sgn * .85 + d * .55 - nrm * .12).normalized()
                pd, ps, pn = _frame(pd)
                g = R.uniform(.85, 1.1)
                buf.leaf(p, pd, ps, pn, plen, plen * .13,
                         shape=lambda u: math.sin(math.pi * min(1, u * 1.05)) ** .6 * (1 + .25 * math.sin(u * 40)),
                         fold=.35, curl=-.15, droop=.18, tint=(g * .9, g, g * .85), nu=8, nv=2)
    o = buf.build(name, mat)
    # 葉軸
    allv, allf = [], []
    for pts in stems:
        b0 = len(allv)
        for k, p in enumerate(pts):
            d = (pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)]).normalized()
            _, s, nn = _frame(d)
            r = .006 * size * (1 - .7 * k / len(pts))
            for j in range(4):
                a = j * math.pi / 2
                allv.append(tuple(p + (s * math.cos(a) + nn * math.sin(a)) * r))
        for k in range(len(pts) - 1):
            for j in range(4):
                a = b0 + k * 4 + j
                allf.append((a, b0 + k * 4 + (j + 1) % 4, b0 + (k + 1) * 4 + (j + 1) % 4, b0 + (k + 1) * 4 + j))
    sm = bpy.data.meshes.new(name + '_stem')
    sm.from_pydata(allv, [], allf)
    so = bpy.data.objects.new(name + '_stem', sm)
    bpy.context.scene.collection.objects.link(so)
    if stem_mat:
        sm.materials.append(stem_mat)
    return o, so


# ---------------- 心形葉植物：長柄、心形葉片微杯、葉面略亮（濕） ----------------
def heart_plant(name, pos, R, size=1.0, mat=None, stem_mat=None):
    buf = LeafBuf()
    sv, sf = [], []
    nl = R.randint(7, 12)
    for k in range(nl):
        az = 2 * math.pi * k / nl + R.uniform(-.3, .3)
        h = size * R.uniform(.12, .32)
        reach = size * R.uniform(.08, .22)
        tip = pos + Vector((math.cos(az) * reach, math.sin(az) * reach, h))
        Lf = size * R.uniform(.10, .16)
        d = Vector((math.cos(az), math.sin(az), R.uniform(-.35, -.05)))
        d, side, nrm = _frame(d)
        g = R.uniform(.85, 1.1)
        # 心形：u=0 在葉柄端，兩片圓耳最寬處在 u≈.25，尖端收尖
        buf.leaf(tip - d * Lf * .12, d, side, nrm, Lf, Lf * .55,
                 shape=lambda u: (.55 + .45 * math.sin(math.pi * min(1, u / .5))) * (1 - u) ** .8 * (1 - .5 * max(0, .06 - u) / .06),
                 fold=.1, curl=.15, droop=.2, tint=(g, g, g), nu=10, nv=6, twist=R.uniform(-.3, .3))
        # 葉柄：從地面彎到葉基
        b0 = len(sv)
        n = 6
        for i in range(n + 1):
            t = i / n
            q = pos.lerp(tip, t) + Vector((0, 0, math.sin(t * math.pi) * h * .25))
            for j in range(3):
                a = j * 2 * math.pi / 3
                sv.append(tuple(q + Vector((math.cos(a), math.sin(a), 0)) * .003 * size))
        for i in range(n):
            for j in range(3):
                a = b0 + i * 3 + j
                sf.append((a, b0 + i * 3 + (j + 1) % 3, b0 + (i + 1) * 3 + (j + 1) % 3, b0 + (i + 1) * 3 + j))
    o = buf.build(name, mat)
    if stem_mat:
        sm = bpy.data.meshes.new(name + '_stem')
        sm.from_pydata(sv, [], sf)
        sm.materials.append(stem_mat)
        so = bpy.data.objects.new(name + '_stem', sm)
        bpy.context.scene.collection.objects.link(so)
    return o

# ---------------- 單片落葉（地上）：薄、有葉脈、捲邊，顏色乾濕不一 ----------------
def litter(name, R, count, place, mat):
    buf = LeafBuf()
    PAL = ((.30, .18, .08), (.40, .25, .11), (.22, .16, .10), (.34, .30, .16), (.17, .13, .09), (.45, .31, .14), (.20, .22, .12))
    n = 0
    for i in range(count * 3):
        q = place()
        if q is None:
            continue
        p, z = q
        L = R.uniform(.05, .09)
        W = L * R.uniform(.32, .45)
        a = R.uniform(0, 2 * math.pi)
        d = Vector((math.cos(a), math.sin(a), R.uniform(-.08, .08)))
        d, side, nrm = _frame(d)
        start = Vector((p[0], p[1], z + .003)) - d * L * .5
        c = PAL[R.randrange(len(PAL))]
        buf.leaf(start, d, side, nrm, L, W,
                 shape=lambda u: math.sin(math.pi * u) ** .8 * (1 - .2 * u),
                 fold=R.uniform(.05, .3), curl=R.uniform(-.1, .45), droop=R.uniform(-.06, .06), tint=c, nu=6, nv=4,
                 twist=R.uniform(-.25, .25))
        n += 1
        if n >= count:
            break
    return buf.build(name, mat), n


# ---------------- 苔叢：在苔丘表面長滿一根根短苔（毛茸茸），不是光滑的丘 ----------------
def moss_tufts(name, mounds, R, mat, fbfn, density=5200):
    buf = LeafBuf()
    for (i, cx, cy, rx, ry, hgt, z0) in mounds:
        n = int(density * rx * ry * 4)
        for k in range(n):
            a = R.uniform(0, 2 * math.pi)
            rr = math.sqrt(R.random()) * .98
            px, py = math.cos(a) * rr, math.sin(a) * rr
            pz = math.sqrt(max(0.0, 1 - rr * rr))
            nn = fbfn((px * 2 + i, py * 2, pz * 2), 1, 2)
            r = 1 + .18 * nn
            tuft = .5 + .5 * fbfn((px * 14 + i, py * 14, 0), 1, 2)
            p = Vector((cx + px * rx * r, cy + py * ry * r, z0 + (pz ** .7) * hgt * (1 + .25 * nn) + pz * .018 * tuft))
            nrm = Vector((px / rx, py / ry, pz / max(hgt, .02) * .35 + .6)).normalized()
            d = (nrm + Vector((R.uniform(-.5, .5), R.uniform(-.5, .5), R.uniform(0, .3)))).normalized()
            d, side, up = _frame(d)
            L = R.uniform(.012, .03) * (.6 + .8 * tuft)
            g = R.uniform(.7, 1.15)
            buf.leaf(p - d * .003, d, side, up, L, L * .2, shape=lambda u: (1 - u) ** .6, fold=.3, droop=R.uniform(0, .5),
                     tint=(g * R.uniform(.85, 1.1), g, g * .8), nu=2, nv=1)
    return buf.build(name, mat)


# ---------------- 蕈：一叢 3–12 朵，傘面有弧度與中央深色，菌褶淺，柄微彎 ----------------
def mushrooms(name, pos, R, count, size, mat, cap=(.30, .17, .08), ground=None):
    V, F, C = [], [], []
    seg = 14
    for m in range(count):
        a = R.uniform(0, 2 * math.pi)
        d = R.uniform(0, .09) * size * math.sqrt(count)
        bx, by = pos.x + math.cos(a) * d, pos.y + math.sin(a) * d
        bz = (ground(bx, by) if ground else pos.z) - .004
        h = size * R.uniform(.045, .11)
        sr = size * R.uniform(.006, .011)
        cr = size * R.uniform(.022, .055)
        ch = cr * R.uniform(.45, .8)
        lx, ly = R.uniform(-.35, .35), R.uniform(-.35, .35)
        k = R.uniform(.75, 1.15)
        capc = (cap[0] * k, cap[1] * k, cap[2] * k, 1)
        capd = (capc[0] * .55, capc[1] * .5, capc[2] * .5, 1)
        gill = (.55, .46, .34, 1)
        stem = (.62, .56, .46, 1)
        stemb = (.25, .19, .13, 1)
        prof = [(sr * 1.5, 0, stemb), (sr * 1.05, h * .25, stem), (sr * .85, h * .9, stem),
                (cr * .55, h * .93, gill), (cr * .98, h * 1.0 + ch * .05, gill), (cr, h + ch * .12, capc)]
        for j in range(1, 7):
            t = j / 6
            ang = t * math.pi / 2
            prof.append((cr * math.cos(ang) ** .9, h + ch * .12 + ch * math.sin(ang) ** .9, capc if t < .65 else capd))
        base = len(V)
        for (r, z, c) in prof:
            ox, oy = lx * z * (z / max(h, 1e-4)) * .6, ly * z * (z / max(h, 1e-4)) * .6
            wob = 1 + .06 * math.sin(m * 3 + z * 90)
            for s in range(seg):
                th = 2 * math.pi * s / seg
                rr = r * wob * (1 + .05 * math.sin(th * 3 + m))
                V.append((bx + ox + math.cos(th) * rr, by + oy + math.sin(th) * rr, bz + z))
                C.append(c)
        for i in range(len(prof) - 1):
            for s in range(seg):
                a0 = base + i * seg + s
                a1 = base + i * seg + (s + 1) % seg
                F.append((a0, a1, a1 + seg, a0 + seg))
    me = bpy.data.meshes.new(name)
    me.from_pydata(V, [], F)
    ca = me.color_attributes.new('Tint', 'FLOAT_COLOR', 'POINT')
    ca.data.foreach_set('color', np.array(C, np.float32).ravel())
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def mushroom_material():
    m = bpy.data.materials.new('UG_Mushroom')
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    b = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    vc = N.new('ShaderNodeVertexColor'); vc.layer_name = 'Tint'
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 60; nz.inputs['Detail'].default_value = 5
    rp = N.new('ShaderNodeMapRange'); rp.inputs['To Min'].default_value = .7; rp.inputs['To Max'].default_value = 1.1
    L.new(nz.outputs['Fac'], rp.inputs['Value'])
    mx = N.new('ShaderNodeMixRGB'); mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1
    L.new(vc.outputs[0], mx.inputs[1]); L.new(rp.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = .42
    try:
        b.inputs['Subsurface Weight'].default_value = .15
    except Exception:
        pass
    return m


# ---------------- 林下小白花：細莖、五瓣、基部幾片小葉 ----------------
def white_flowers(name, pos, R, count, petal_mat, leaf_mat, ground=None):
    pb, lb = LeafBuf(), LeafBuf()
    for f in range(count):
        a = R.uniform(0, 2 * math.pi)
        d = R.uniform(0, .16)
        x, y = pos.x + math.cos(a) * d, pos.y + math.sin(a) * d
        z = ground(x, y) if ground else pos.z
        h = R.uniform(.06, .13)
        top = Vector((x + R.uniform(-.02, .02), y + R.uniform(-.02, .02), z + h))
        tilt = Vector((R.uniform(-.3, .3), R.uniform(-.3, .3), 1)).normalized()
        e1 = tilt.cross(Vector((1, 0, 0))).normalized()
        e2 = tilt.cross(e1).normalized()
        for k in range(5):
            th = 2 * math.pi * k / 5 + f
            pd = (e1 * math.cos(th) + e2 * math.sin(th) + tilt * .25).normalized()
            pd, ps, pn = _frame(pd)
            Lp = R.uniform(.013, .019)
            pb.leaf(top, pd, ps, tilt, Lp, Lp * .42, shape=lambda u: math.sin(math.pi * (u * .9 + .1)) ** .7, fold=.15, curl=.1,
                    droop=-.1, tint=(1, 1, 1), nu=5, nv=3)
        # 莖（當成很窄的葉）
        sd = (top - Vector((x, y, z)))
        Ls = sd.length
        sd, ss, sn = _frame(sd)
        lb.leaf(Vector((x, y, z)), sd, ss, sn, Ls, .0018, shape=lambda u: 1.0, fold=0, tint=(.8, .9, .7), nu=3, nv=1)
        for k in range(R.randint(2, 4)):
            th = R.uniform(0, 2 * math.pi)
            ld = Vector((math.cos(th), math.sin(th), R.uniform(.1, .5)))
            ld, ls, ln = _frame(ld)
            Ll = R.uniform(.03, .05)
            lb.leaf(Vector((x, y, z + .005)), ld, ls, ln, Ll, Ll * .3, shape=lambda u: math.sin(math.pi * u) ** .8, fold=.2,
                    droop=.3, tint=(1, 1, 1), nu=5, nv=2)
    return pb.build(name + '_petals', petal_mat), lb.build(name + '_leaves', leaf_mat)
