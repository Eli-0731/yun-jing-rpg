# DR07 巨樹樁的遊戲用模型：低模 → 拆 UV → 烘焙 → 植物 → LOD1／LOD2 → 碰撞 → FBX／GLB。
# 整套沿用 game_dr06.py（再往下是 D2 根與木的 game_dr02.py），和 game_dr05.py 一樣只換：
#   - 高模腳本換成 build_dr07.py，物件／集合名前綴 DR07_；
#   - 「藏起來的面」：外殼、內壁、斷面彼此不算擋住（內壁在外殼「裡面」，但從上面看得到）；
#   - 樹皮遮罩：DR07 自己那份樹皮材質（DR07_Bark）也算樹皮；
#   - 低模清掉 EndMoss（朽木靠斷口的苔，已烘進貼圖）；
#   - 本體不含水面（build_dr07.WATER = False）：水面由 water_dr07.py 另存，Unity 套 YunJing/CreekFlowWater 靜水。
# 用法（背景）：blender -b --python game_dr07.py -- A 24（B 同）
import os, sys

_HERE7 = 'D:/yun-jing-d2-logs/art/source/d2-logs-b'
_src6 = _HERE7 + '/game_dr06.py'
_txt6 = open(_src6, encoding='utf-8').read()
for _a, _b in (("('ring', 'Peel', 'MudMoss')", "('ring', 'Peel', 'MudMoss', 'EndMoss')"),
               ("m.name.startswith('DR06_Bark')", "m.name.startswith(('DR06_Bark', 'DR05_Bark', 'DR07_Bark'))"),
               ("'DR06_LowG", "'DR07_LowG"), ("f'DR06_LowG", "f'DR07_LowG"),
               ("o.name.startswith('DR06_LowG')", "o.name.startswith('DR07_LowG')"),
               ("uvo[sl, 0] = a0 + (a1 - a0) * (.08 + .84 * su[vi[sl]])",      # 每片木片（36–42 個頂點）尖端深淺不同
                "uvo[sl, 0] = a0 + (a1 - a0) * np.clip(.08 + .84 * su[vi[sl]] * (.45 + .55 * ((vi[sl] // 36 * .618034) % 1.0)), 0, .92)")):
    assert _a in _txt6 or _b in _txt6, _a
    _txt6 = _txt6.replace(_a, _b)
_nm = globals().get('__name__')
globals()['__name__'] = 'game_dr06_lib'             # 不要跑 DR06 的主程式
exec(compile(_txt6, _src6, 'exec'), globals())
globals()['__name__'] = _nm

NAMES = {'A': 'DR07_GiantStump_A', 'B': 'DR07_GiantStump_B'}
DET = 'Detail_DR07_Plants'
SHELL = ('Trunk', 'Inner', 'Rim0')
LOWRES = (.12, 8, 64, 1.0)                      # 低模：每 0.12 m 一環、最多 64 邊（斷口的木板只有 0.4–0.8 m 寬，28 邊時是一兩個平面）
SHARD_C = ((.20, .115, .055), (.56, .38, .21))      # 斷口的木刺、翻卷的朽木片：根部深褐 → 尖端淺橘褐（同 DR05 第四輪）


def configure(v):
    global VARIANT, ASSET, EXP, TEX, WORKTEX
    VARIANT = v
    ASSET = NAMES[v]
    EXP = f'{ROOT}/art/exports/d2-logs-b/{ASSET}'
    TEX = EXP + '/Textures'
    WORKTEX = os.environ.get('DR_WORK7', 'D:/yun-jing-cache/dr07-work/') + f'bake_{v}'


def _build():
    global B
    if B is None:
        p = HERE6 + '/build_dr07.py'
        B = {'__file__': p, '__name__': 'build_dr07'}
        exec(compile(open(p, encoding='utf-8').read(), p, 'exec'), B)
        B['WATER'] = False                          # 本體不含水面：水面另存 <件名>_water_v001.fbx（water_dr07.py），有水／沒水兩種狀態
    B['set_variant'](VARIANT)
    return B


def _cn(kind):
    return f"DR07_{_build()['VAR']['name']}_{kind}"


def _hidden_verts(objs, margin=.03, zcut=-.5):
    """外殼、內壁、斷面兩兩之間不互相判斷（從上面看得到內壁）；其他件照 DR06。"""
    from mathutils.bvhtree import BVHTree
    from mathutils import Vector
    import numpy as np
    base = lambda o: o.name.split('_', 1)[1] if o.name.startswith(('L_', 'C_', 'F_')) else o.name
    shell = [base(o) in SHELL for o in objs]
    dirs = [Vector(d) for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
    data = []
    for o in objs:
        co = np.array([v.co[:] for v in o.data.vertices])
        t = BVHTree.FromPolygons([Vector(c) for c in co], [tuple(p.vertices) for p in o.data.polygons])
        data.append((co, t, co.min(0), co.max(0)))
    out = []
    for i, o in enumerate(objs):
        co, _, lo_i, hi_i = data[i]
        hide = co[:, 2] < zcut
        for j, (cj, tj, lo, hi) in enumerate(data):
            if j == i or (shell[i] and shell[j]) or (lo_i > hi).any() or (hi_i < lo).any():
                continue
            for vi in np.nonzero(~hide & (co >= lo).all(1) & (co <= hi).all(1))[0]:
                q = Vector(co[vi])
                loc, nrm, idx, dist = tj.find_nearest(q)
                if loc is not None and dist > margin and (q - loc).dot(nrm) < 0 and all(tj.ray_cast(q, d, 50)[0] is not None for d in dirs):
                    hide[vi] = True
        out.append(hide)
    return out


if __name__ == '__main__' and '--' in sys.argv:
    a = sys.argv[sys.argv.index('--') + 1:]
    if 'redetail' in a:
        configure(a[0])
        p = Vector(bpy.context.scene.get('dr_pivot', (0.0, 0.0, 0.0)))
        bpy.data.objects[f'{ASSET}_LOD0'].data.transform(Matrix.Translation(p))
        bpy.data.objects.remove(bpy.data.objects[f'{DET}_LOD0'], do_unlink=True)
        bpy.context.scene['dr_pivot'] = [0.0, 0.0, 0.0]
        make_detail()
        refinish(a[0])
    elif 'retex' in a:
        configure(a[0])
        finish_textures()
        refinish(a[0])
    elif 'refinish' in a:
        refinish(a[0])
    else:
        run_all(a[0] if a else 'A', int(a[1]) if len(a) > 1 else 24)
