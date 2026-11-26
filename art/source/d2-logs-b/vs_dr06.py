# DR06 「成品 vs 參考圖」並排圖用的成品渲染：鏡位照 art/references/DR06/v001/DR06-threequarter.png（Codex 依 D2 設定圖 V1、V4、V5 畫的四分之三視圖）估。
# 參考圖沒有相機資料，鏡位是對著畫面估的（樹幹佔畫面寬度、地平線高度、根盤朝外那面露出多少），不是量出來的。
# 用法（Blender 背景模式，開遊戲 blend）：
#   blender -b art/source/d2-logs-b/blend/DR06_FallenTrunk_B_v001.blend --python art/source/d2-logs-b/vs_dr06.py -- B
# 輸出 art/previews/d2-logs-b/<物件>/<物件>_LOD0_refcam.png；再用 compose_dr06.py 和參考圖並排。
import bpy, sys, os

HERE = os.path.dirname(os.path.abspath(__file__)).replace('\\', '/')
R2 = HERE + '/../d2-roots-b'
ROOT = os.path.abspath(HERE + '/../../..').replace('\\', '/')
ASSETS = {'A': 'DR06_FallenTrunk_A', 'B': 'DR06_FallenTrunk_B'}
# 建模座標（根盤 x = 0、斷口 x = L）；以樹幹長 L 為單位估：站在根盤那頭的左前方、比人眼高一點，樹幹斜斜往右後方退（參考圖根盤在左前、斷口在右邊較小）
CAM = dict(frm=(-.14, -1.02, 4.2), at=(.49, 0, 1.0), lens=30, res=(1536, 1024))


def _load(p):
    g = {'__file__': p, '__name__': os.path.basename(p)[:-3]}
    exec(compile(open(p, encoding='utf-8').read(), p, 'exec'), g)
    return g


def run(v, samples=64):
    asset = ASSETS[v]
    b = _load(HERE + '/build_dr06.py')
    V = b['set_variant'](v)
    L = V['L']
    pv = _load(R2 + '/preview_dr.py')
    dp = _load(R2 + '/dr_pivot.py')
    dp['frame'](asset, True)
    pv['setup'](samples=samples, fog=True)
    hm = bpy.data.objects.get('DR_Human_1p75m')
    if hm:
        hm.hide_render = True
    keep = {f'{asset}_LOD0', 'Detail_DR06_Plants_LOD0'}
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name not in keep and not o.name.startswith('DR_'):
            o.hide_render = True
    f, t = CAM['frm'], CAM['at']
    out = f'{ROOT}/art/previews/d2-logs-b/{asset}/{asset}_LOD0_refcam.png'
    os.makedirs(os.path.dirname(out), exist_ok=True)
    pv['shot'](out, (f[0] * L, f[1] * L, f[2]), (t[0] * L, t[1] * L, t[2]), CAM['lens'], res=CAM['res'])
    dp['frame'](asset, False)
    print('VS_DONE', out)


if __name__ == '__main__':
    a = sys.argv[sys.argv.index('--') + 1:]
    run(a[0], int(a[1]) if len(a) > 1 else 64)
