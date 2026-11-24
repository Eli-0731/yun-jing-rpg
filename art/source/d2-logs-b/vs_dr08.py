# DR08「成品 vs 參考圖」並排圖用的成品渲染：鏡位照 art/references/DR08/v001/DR08-threeview.png 左欄（側視、人形尺在左）估。
# 參考圖沒有相機資料，鏡位是對著畫面估的（從正面 -Y 平視、樹幹佔畫面寬度），不是量出來的。
# 用法（Blender 背景模式，開遊戲 blend）：
#   blender -b art/source/d2-logs-b/blend/DR08_RottenLog_A_v001.blend --python art/source/d2-logs-b/vs_dr08.py -- A
# 輸出 art/previews/d2-logs-b/<物件>/<物件>_LOD0_refcam.png；再用 compose_dr08.py 和參考圖並排。
import bpy, sys, os

HERE = os.path.dirname(os.path.abspath(__file__)).replace('\\', '/')
R2 = HERE + '/../d2-roots-b'
ROOT = os.path.abspath(HERE + '/../../..').replace('\\', '/')
ASSETS = {'A': 'DR08_RottenLog_A', 'B': 'DR08_RottenLog_B', 'C': 'DR08_RottenLog_C'}


def _load(p):
    g = {'__file__': p, '__name__': os.path.basename(p)[:-3]}
    exec(compile(open(p, encoding='utf-8').read(), p, 'exec'), g)
    return g


def run(v, samples=64):
    asset = ASSETS[v]
    b = _load(HERE + '/build_dr08.py')
    V = b['set_variant'](v)
    L = V['L']
    pv = _load(R2 + '/preview_dr.py')
    dp = _load(R2 + '/dr_pivot.py')
    dp['frame'](asset, True)
    pv['setup'](samples=samples, fog=False)
    hm = bpy.data.objects.get('DR_Human_1p75m')
    if hm:
        hm.location = (-1.0, .4, .875)             # 參考圖人形尺站在樹幹左邊
    keep = {f'{asset}_LOD0', 'Detail_DR08_Plants_LOD0'}
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name not in keep and not o.name.startswith('DR_'):
            o.hide_render = True
    cx = (L - 1.0) * .5
    w = L + 1.8
    ver = os.environ.get('DR8VER', 'v001')                 # v002 以後的對照圖放在 <物件>/<版本>/，不蓋掉 v001
    out = f'{ROOT}/art/previews/d2-logs-b/{asset}/' + ('' if ver == 'v001' else ver + '/') + f'{asset}_LOD0_refcam.png'
    os.makedirs(os.path.dirname(out), exist_ok=True)
    pv['shot'](out, (cx, -w * 1.75, .75), (cx, 0, .55), 50, res=(1536, 640))
    dp['frame'](asset, False)
    print('VS_DONE', out)


if __name__ == '__main__':
    a = sys.argv[sys.argv.index('--') + 1:]
    run(a[0], int(a[1]) if len(a) > 1 else 64)
