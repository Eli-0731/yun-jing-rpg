# DR07 「成品 vs 參考圖」並排圖用的成品渲染：鏡位照 art/references/DR07/v001/DR07-threequarter.png（Codex 依 D2 設定圖 V1、V4 畫的四分之三視圖）估。
# 參考圖沒有相機資料，鏡位是對著畫面估的（從高處斜看、看得到洞裡的積水、高的斷口在後方），不是量出來的。
# 用法（Blender 背景模式，開遊戲 blend）：
#   blender -b art/source/d2-logs-b/blend/DR07_GiantStump_A_v001.blend --python art/source/d2-logs-b/vs_dr07.py -- A
# 輸出 art/previews/d2-logs-b/<物件>/<物件>_LOD0_refcam.png；再用 compose_dr07.py 和參考圖並排。
import bpy, sys, os, math

HERE = os.path.dirname(os.path.abspath(__file__)).replace('\\', '/')
R2 = HERE + '/../d2-roots-b'
ROOT = os.path.abspath(HERE + '/../../..').replace('\\', '/')
ASSETS = {'A': 'DR07_GiantStump_A', 'B': 'DR07_GiantStump_B'}
# 以樁半徑 R 為單位：站在斷口高處（hinge）的對面、往右偏 25°，離樁 5.2R、高 3.4R，看得到洞裡的水、高的斷口在後面（參考圖兩個樁都是這樣）
CAM = dict(dist=5.2, side=.44, up=3.4, lens=32, res=(1536, 1024))


def _load(p):
    g = {'__file__': p, '__name__': os.path.basename(p)[:-3]}
    exec(compile(open(p, encoding='utf-8').read(), p, 'exec'), g)
    return g


def run(v, samples=64):
    asset = ASSETS[v]
    b = _load(HERE + '/build_dr07.py')
    V = b['set_variant'](v)
    R, hg = V['R'], V['hinge']
    pv = _load(R2 + '/preview_dr.py')
    dp = _load(R2 + '/dr_pivot.py')
    dp['frame'](asset, True)
    pv['setup'](samples=samples, fog=True)
    hm = bpy.data.objects.get('DR_Human_1p75m')
    if hm:
        hm.hide_render = True
    a = hg + math.pi + CAM['side']
    frm = (math.cos(a) * CAM['dist'] * R, math.sin(a) * CAM['dist'] * R, CAM['up'] * R)
    at = (0.0, 0.0, V['H'][0] * .45)
    # 有水（本體＋植物＋水面）、沒水（本體＋植物）各一張
    for tag, keep in (('', {f'{asset}_LOD0', 'Detail_DR07_Plants_LOD0', f'{asset}_water_LOD0'}),
                      ('_dry', {f'{asset}_LOD0', 'Detail_DR07_Plants_LOD0'})):
        for o in bpy.data.objects:
            if o.type == 'MESH' and not o.name.startswith('DR_'):
                o.hide_render = o.name not in keep
        out = f'{ROOT}/art/previews/d2-logs-b/{asset}/{asset}_LOD0_refcam{tag}.png'
        os.makedirs(os.path.dirname(out), exist_ok=True)
        pv['shot'](out, frm, at, CAM['lens'], res=CAM['res'])
    dp['frame'](asset, False)
    print('VS_DONE', out)


if __name__ == '__main__':
    a = sys.argv[sys.argv.index('--') + 1:]
    run(a[0], int(a[1]) if len(a) > 1 else 64)
