# 「成品 vs 設定圖裡同一個東西」的並排圖用的成品渲染：鏡位照 D2 設定圖（V3、V5）裡那一段根的方向和高度估的，光用 preview_dr 的陰天漫射光＋霧。
# 設定圖是手繪場景、沒有相機資料，鏡位是對著畫面估的（相機高度、看過去的方向、物件在畫面裡的位置），不是量出來的。
# 用法（Blender 背景模式，開新版遊戲 blend）：
#   blender -b art/source/d2-roots-b/blend/DR04_RootHollow_v002.blend --python art/source/d2-roots-b/vs_concept.py -- DR04_H
# 輸出 art/previews/d2-roots-b/<物件>/<物件>_LOD0_<設定圖>cam.png；再用 compose_review.py 和設定圖裁切並排（裁切範圍見 CROPS）。
# 鏡位用舊原點的座標（和 report 的審圖鏡位一樣），拍的時候根物件搬回舊原點（dr_pivot.frame）。
import bpy, sys, os

HERE = 'D:/yun-jing-d2-roots/art/source/d2-roots-b'
ROOT = os.path.abspath(HERE + '/../../..').replace('\\', '/')
# 代號：(物件名, 設定圖, 相機位置, 看的點, 焦距 mm, 解析度)
CAMS = {
    # V3 祭壇後面那幾條順著地面往右爬的長根：從空地這邊側看、略高於人眼，約 20 m 遠
    'DR02_A': ('DR02_RootWall_A', 'V3', (1.0, -18.0, 2.4), (0.3, 0.0, 1.3), 30, (1536, 524)),
    'DR02_B': ('DR02_RootWall_B', 'V3', (1.0, -18.0, 2.4), (0.3, 0.0, 1.3), 30, (1536, 524)),
    'DR02_C': ('DR02_RootWall_C', 'V3', (1.0, -18.0, 2.4), (0.3, 0.0, 1.3), 30, (1536, 524)),
    # V5 左半：從神木斜下來、在路邊分成根指鑽進土裡；站在路上、人眼高，從根指那一側斜看
    'DR03_E': ('DR03_RootEnd', 'V5', (1.2, -5.2, 1.8), (-.4, .6, .7), 22, (1536, 1010)),
    # V5 右下：一條根拱起來壓過另一條；人眼高、離約 4–5 m、往下看
    'DR03_X': ('DR03_RootCross', 'V5', (1.9, -3.3, 2.1), (-.3, .5, .35), 22, (1536, 1038)),
    # V5 最左邊：板根之間的黑洞口，近看、人眼略低、從右前方
    'DR04_H': ('DR04_RootHollow', 'V5', (1.9, -2.3, 1.55), (.3, .9, .65), 22, (1536, 1256)),
}
# 設定圖裁切（原圖像素：左、上、右、下），compose 時用
CROPS = {'DR02': ('V3', (750, 307, 1501, 563)), 'DR03_E': ('V5', (364, 303, 1132, 808)),
         'DR03_X': ('V5', (889, 525, 1577, 990)), 'DR04_H': ('V5', (0, 303, 667, 849))}


def _load(n):
    p = f'{HERE}/{n}'
    g = {'__file__': p, '__name__': n[:-3]}
    exec(compile(open(p, encoding='utf-8').read(), p, 'exec'), g)
    return g


def run(job, samples=64):
    asset, V, loc, tgt, lens, res = CAMS[job]
    pv = _load('preview_dr.py')
    dp = _load('dr_pivot.py')
    dp['frame'](asset, True)
    pv['setup'](samples=samples, fog=True)
    hm = bpy.data.objects.get('DR_Human_1p75m')
    if hm:
        hm.hide_render = True              # 設定圖裡沒有人形尺；比例看十方位和審圖
    det = next(o.name[:-5] for o in bpy.data.objects[asset].children if o.name.startswith('Detail_') and o.name.endswith('_LOD0'))
    keep = {f'{asset}_LOD0', f'{det}_LOD0'}
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name not in keep and not o.name.startswith('DR_'):
            o.hide_render = True
    out = f'{ROOT}/art/previews/d2-roots-b/{asset}/{asset}_LOD0_{V}cam.png'
    pv['shot'](out, loc, tgt, lens, res=res)
    dp['frame'](asset, False)
    print('VS_DONE', out)


if __name__ == '__main__':
    run(sys.argv[sys.argv.index('--') + 1])
