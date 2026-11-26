# DR05 空心倒木的遊戲用模型：低模 → 拆 UV → 烘焙 → 植物 → LOD1／LOD2 → 碰撞 → FBX／GLB。
# 整套沿用 game_dr06.py（再往下是 D2 根與木的 game_dr02.py），只換：
#   - 高模腳本換成 build_dr05.py，物件／集合名前綴 DR05_；
#   - 「藏起來的面」：外殼、內壁、洞口斷面彼此不算擋住（內壁在外殼「裡面」，但從隧道裡看得到）；
#   - 樹皮遮罩：DR05 自己那份樹皮材質（DR05_Bark）也算樹皮；
#   - 低模清掉 EndMoss（朽木靠洞口的苔，已烘進貼圖）。
# 用法（背景）：blender -b --python game_dr05.py -- A 24
import os, sys

_HERE5 = 'D:/yun-jing-d2-logs/art/source/d2-logs-b'
_src6 = _HERE5 + '/game_dr06.py'
_txt6 = open(_src6, encoding='utf-8').read()
for _a, _b in (("('ring', 'Peel', 'MudMoss')", "('ring', 'Peel', 'MudMoss', 'EndMoss')"),
               ("m.name.startswith('DR06_Bark')", "m.name.startswith(('DR06_Bark', 'DR05_Bark'))"),
               ("'DR06_LowG", "'DR05_LowG"), ("f'DR06_LowG", "f'DR05_LowG"),
               ("o.name.startswith('DR06_LowG')", "o.name.startswith('DR05_LowG')"),
               ("uvo[sl, 0] = a0 + (a1 - a0) * (.08 + .84 * su[vi[sl]])",      # 每片木片（42 個頂點）尖端深淺不同，不然一圈同一個色
                "uvo[sl, 0] = a0 + (a1 - a0) * np.clip(.08 + .84 * su[vi[sl]] * (.45 + .55 * ((vi[sl] // 42 * .618034) % 1.0)), 0, .92)")):
    _txt6 = _txt6.replace(_a, _b)
_nm = globals().get('__name__')
globals()['__name__'] = 'game_dr06_lib'             # 不要跑 DR06 的主程式
exec(compile(_txt6, _src6, 'exec'), globals())
globals()['__name__'] = _nm

NAMES = {'A': 'DR05_HollowLog'}
DET = 'Detail_DR05_Plants'
SHELL = ('Trunk', 'Inner', 'Rim0', 'Rim1', 'Lip0', 'Lip1')
LOWRES = (.15, 8, 44, 1.0)                      # 低模比 DR06 密：兩頭參差、塌掉的洞口和頂上的洞，每 0.25 m 一環、28 邊會變成幾片大平面（像紙箱角）
SHARD_C = ((.20, .115, .055), (.56, .38, .21))      # 洞口的纖維舌片：根部深褐 → 尖端淺橘褐（第四輪：跟內壁朽木同色，深褐厚片近看像碎樹皮塊）


def configure(v):
    global VARIANT, ASSET, EXP, TEX, WORKTEX
    VARIANT = v
    ASSET = NAMES[v]
    EXP = f'{ROOT}/art/exports/d2-logs-b/{ASSET}'
    TEX = EXP + '/Textures'
    WORKTEX = os.environ.get('DR_WORK5', 'D:/yun-jing-cache/dr05-work/') + f'bake_{v}'


def _build():
    global B
    if B is None:
        p = HERE6 + '/build_dr05.py'
        B = {'__file__': p, '__name__': 'build_dr05'}
        exec(compile(open(p, encoding='utf-8').read(), p, 'exec'), B)
    B['set_variant'](VARIANT)
    return B


def _cn(kind):
    return f"DR05_{_build()['VAR']['name']}_{kind}"


_hidden_verts6 = _hidden_verts


def _hidden_verts(objs, margin=.03, zcut=-.5):
    """外殼、內壁、洞口斷面兩兩之間不互相判斷（隧道裡看得到內壁）；其他件照 DR06。"""
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
