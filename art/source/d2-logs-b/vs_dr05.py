# DR05 「成品 vs 參考圖」並排圖用的成品渲染：鏡位照 art/references/DR05/v001/DR05-threequarter.png（Codex 依 D2 設定圖 V1、V4 畫的四分之三視圖）估。
# 參考圖沒有相機資料，鏡位是對著畫面估的（樹幹佔畫面寬度、地平線高度、近端洞口露出多少），不是量出來的。
# 用法（Blender 背景模式，開遊戲 blend）：
#   blender -b art/source/d2-logs-b/blend/DR05_HollowLog_v001.blend --python art/source/d2-logs-b/vs_dr05.py -- A
# 輸出 art/previews/d2-logs-b/<物件>/<物件>_LOD0_refcam.png；再用 compose_dr05.py 和參考圖並排。
import bpy, sys, os

HERE = os.path.dirname(os.path.abspath(__file__)).replace('\\', '/')
R2 = HERE + '/../d2-roots-b'
ROOT = os.path.abspath(HERE + '/../../..').replace('\\', '/')
ASSETS = {'A': 'DR05_HollowLog'}
# 建模座標（x = 0 那頭洞口完整、x = L 那頭上半塌掉）；以長 L 為單位估：站在 x = 0 洞口的左前方、比人眼高一點，看得到近端洞口裡面，樹幹往右後方退（參考圖近端洞口在左、塌掉的那頭在右後）
CAM = dict(frm=(-.62, -.42, 2.4), at=(.30, .02, .85), lens=30, res=(1536, 1024))


def _load(p):
    g = {'__file__': p, '__name__': os.path.basename(p)[:-3]}
    exec(compile(open(p, encoding='utf-8').read(), p, 'exec'), g)
    return g


def run(v, samples=64):
    asset = ASSETS[v]
    b = _load(HERE + '/build_dr05.py')
    V = b['set_variant'](v)
    L = V['L']
    pv = _load(R2 + '/preview_dr.py')
    dp = _load(R2 + '/dr_pivot.py')
    dp['frame'](asset, True)
    pv['setup'](samples=samples, fog=True)
    hm = bpy.data.objects.get('DR_Human_1p75m')
    if hm:
        hm.hide_render = True
    keep = {f'{asset}_LOD0', 'Detail_DR05_Plants_LOD0'}
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
