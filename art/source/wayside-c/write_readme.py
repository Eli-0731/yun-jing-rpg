"""Writes art/exports/wayside-c/README.md from model_info.json (labeling-v1 §5 header, then per-item numbers), after
art/source/yard-props-c/write_readme.py.   python art/source/wayside-c/write_readme.py   (from the repo root)"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'art/exports/wayside-c'
info=json.loads((E/'model_info.json').read_text(encoding='utf-8'))
DESC={
 'WS01_01':('路邊野花叢（黃）','一叢細莖從基部分枝，基部 12 片葉；22 根細莖上互生有深鋸齒的窄葉，往上變小；每根莖頂分出三、四枝花梗，開黃色小菊（13 片舌狀花瓣圍著金黃的圓頂花心，花瓣高低錯開、不在同一面），也有花苞和開過只剩褐色花托的。每片葉子和花瓣都是單獨一片，沒有葉片卡。低處葉子的路塵、部分葉子偏黃畫在貼圖上。腳下一小片乾土和兩顆小石是 Detail_Base。','cand-1（91，黃花）'),
 'WS01_02':('路邊野花叢（紫，夏枯草）','14 根直立的方莖，卵形葉對生、每對轉 90°；莖頂一串短花穗（綠紫色的苞片），四圈紫色唇形小花伸出來，幾串開過變成褐色；基部 10 片葉攤在地上。每片葉子和小花都是單獨一片，沒有葉片卡。低處葉子的路塵畫在貼圖上。腳下一小片乾土和兩顆小石是 Detail_Base。','cand-3（91，紫花）'),
 'WS02_01':('乾草叢（高，乾芒草）','一叢約 1.1 m 高的乾芒草：70 片有中摺的長葉從密的基部拱出去，草黃到淺褐，裡面低處幾片還綠；六根細稈高出葉子，每根頂上 16 條絲狀小穗往外彎垂成羽毛狀的花穗。每片葉子都是單獨一片，沒有葉片卡；葉尖的下垂量有限制，不會穿進地面。腳下一小片乾土和四顆小石是 Detail_Base。','cand-4（91，高）'),
 'WS02_02':('乾草叢（矮，枯草團）','低低一團約 0.25 m 高的枯草：90 片細葉往外拱、彎折、糾在一起，每四片有一片折斷：一小截立著，折斷的部分倒下來、尖端落到地上；裡面幾片還帶綠。每片葉子都是單獨一片，沒有葉片卡。腳下一小片乾土和三顆小石是 Detail_Base。','cand-1（91，矮）'),
 'WS03':('路邊碎石堆','修路剩下的一小堆劈開的花崗岩：24 塊從頭大到拳頭大、有稜角的石頭，大的先放、小的一塊塊往下落，停在地面或已經放好的石頭上（不穿插、不浮空），每塊轉到沒有面和鄰居貼平為止（GC06 的做法）。腳邊散落的 70 粒碎石子是 Detail_Gravel，石縫裡 8 叢小草是 Detail_Weeds。朝上面的灰塵、低處的青苔和泥、幾處新的淺色斷口畫在貼圖上，小坑在法線圖裡。','cand-2（91）'),
 'WS04_01':('疊石小塔（三塊）','三塊扁圓的河石由大到小疊起來，每塊往下落到下面那塊上，轉到接觸面不貼平；有一點偏、有一點歪，但每塊的重心都在下面那塊上。石頭有暖褐有偏灰，頂面灰塵、低處青苔畫在貼圖上。腳邊四叢小草是 Detail_Weeds。','cand-4（91）'),
 'WS04_02':('疊石小塔（五塊）','和 WS04_01 同樣的做法，五塊石頭，往同一邊歪得比較多。','cand-4（91）'),
 'WS05_01':('稻草堆','一堆低低、歪一邊的打過穀的稻草，做法和 VG04 草垛相同：實心的芯外面罩四層草披，每層的下緣參差做在形狀上、各自歪一點、比下面那層往外幾公分（不會共面），每層下緣伸出一根根草稈（毛邊是做出來的，不是透明卡），頂上丟著一團亂草。插出來的 30 根散草稈是 Detail_Stalks。金黃和淋過雨的灰白稻草、近地面的潮濕畫在貼圖上。整堆在深度方向壓成 0.85 的橢圓。','cand-1（91）'),
 'WS05_02':('稻束（三束）','三束立著曬的稻草排成一排：每束 64 根稻草從腳下一圈經過綁緊的腰部到頂，每根在束裡的位置（腳、腰、頂的半徑）成比例，所以不會互相交叉；腰上兩圈草繩；頂上的穗頭往外垂。腳下比較暗、部分稻草灰白，畫在貼圖上。A6 稻田也可以一束束沿田埂擺。','cand-1（91）'),
 'WS06':('柴捆','兩捆柴一捆躺在另一捆的凹處：28 根和 25 根粗細不同的樹枝在圓形截面裡排緊，彼此只差 0.4 mm（不穿插、也不會一根懸在中間），每捆整體微彎、每根長短不同，粗的約五分之一是三角形截面的劈柴；捆的兩端伸出分叉的細枝；每捆兩道三股扭成的草繩勒進外圈的枝條，留一小段繩頭。淺色的鋸口和年輪（也在法線圖裡）、灰白和褐色混雜的樹皮、一點地衣畫在貼圖上。地上 6 根散落的細枝是 Detail_Twigs。','cand-4（91）')}
rows=[]
for k in sorted(info):
    d=info[k];l=d['lods'];name,desc,ref=DESC[k];rid=k.split('_')[0]
    tex=', '.join(sorted({f'{w}×{h}' for w,h in l['LOD0']['textures_px'].values()}))
    det=', '.join(d['detailObjects']) if d['detailObjects'] else '無'
    col=d['collision'];colt=(f"`{col['mesh']}`：一個盒子 {' × '.join(str(x) for x in col['primitives'][0]['size_xyz_m'])} m（只在 FBX 和 .blend 裡，不顯示）" if isinstance(col,dict) else '模型裡沒有')
    rows.append(f"### {k} {name}（{d['name']}，{d['version']}）\n\n{desc}\n\n"
      f"| 項目 | 數字 |\n|---|---|\n| 三視圖 | `art/references/{rid}/`，選用 {ref} |\n"
      f"| 尺寸（寬 × 深 × 高） | {d['dimensions_xyz_m'][0]} × {d['dimensions_xyz_m'][1]} × {d['dimensions_xyz_m'][2]} m（上限 {' × '.join(str(x) for x in d['size_limit_xyz_m'])} m） |\n"
      f"| 三角面 LOD0 / LOD1 / LOD2 | {l['LOD0']['triangles']:,} / {l['LOD1']['triangles']:,} / {l['LOD2']['triangles']:,}（不含 Detail_：{l['LOD0']['triangles_without_detail']:,} / {l['LOD1']['triangles_without_detail']:,} / {l['LOD2']['triangles_without_detail']:,}） |\n"
      f"| 物件數（每個 LOD） | {l['LOD0']['objects']}（本體 1 + {det}） |\n"
      f"| 材質數 | 1（`{d['material']}`，全部共用） |\n| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，{tex} |\n"
      f"| minTier | {d['minTier']} |\n| 碰撞 | {colt} |\n"
      f"| 檔案 | `{d['files']['fbx']}`（LOD0–2）、`{d['files']['glb']}`（LOD0）、`{d['files']['blend']}` |\n")
head="""| 項目 | 內容 |
|---|---|
| 誰做的 | C（Eli-0731） |
| 工作包 | docs/execution/2026-11-14/C-120h-yards-undergrowth-and-wayside.md，C 批 |
| ID | WS01–WS06（10 個模型：WS01、WS02、WS04、WS05 各兩種） |
| 分支／PR | art/c-1114-ws01-06-wayside ／ 開 PR 後補 |
| 版本 | v001（檔名帶 `_v001`；之後改版另存 v002，不覆寫） |
| 狀態 | Exported ／ Imported（Unity 6000.3.28f1 獨立匯入檢查）／ Visually Verified（Blender 與 Unity 審圖）／ In-game Verified：未驗（沒放進正式場景） |
| 素材來源 | 原創；三視圖參考在 `art/references/WS01/`–`art/references/WS06/` |
| 實際工時 | 見下方「實際工時」 |

# 路邊小物 WS01–WS06

11/14 的 120 小時包 C 批：A2 村外官道路邊的小東西（A2 沒有設定圖，照區塊規劃 `docs/execution/blocks/A2-A3-block-plan.md` 寫物件句）；WS05 也給 A6 稻田用。靜態擺設，沒有玩法或動畫；擺進世界由核心組做，這裡不改主場景、不改區塊 JSON。

**共同做法**
- 先生成三視圖（每件 4 張，WS01、WS02 兩種各 4 張）、自評選一張（分數和取捨在各自的 `prompt.txt`），再做灰模（`art/previews/wayside-c/<ID>/clay/`），最後上貼圖。三視圖底下畫的石板地座都不做。
- 原點在腳印中心、底部 z = 0，Blender −Y 是正面（FBX／Unity 是 −Z）。不附地面底板（草和花腳下的薄土片是 Detail_）。
- 一件一個材質、一套 1024 貼圖（Albedo／Normal／ORM／MaskURP）；可有可無的小東西放 `Detail_*`（標準畫質關掉）。`minTier` 都是 `standard`。LOD1 約 50%、LOD2 約 15%。
- **沒有透明卡**：花瓣、葉片、草葉、稻草的毛邊都是做出來的形狀。薄的葉片和花瓣在 Unity 裡用雙面材質（檢查腳本有設）。
- **碰撞**：WS05_01 稻草堆、WS06 柴捆在 FBX 裡附一個盒子 `<ID>_Collision`（不顯示）；其餘可以跨過或穿過，模型裡沒有。
- 建模流程和 yard-props-c 相同（共用工具、來源貼圖和零件），`build_ws.py` 只換套件名、表格和物件檔；石頭的堆法照 ground-cover-c 的 GC06。
- 重建：`blender -b --factory-startup -P art/source/wayside-c/build_ws.py -- WS03 [--clay]`；審圖與 QA：`BL=<blender> sh art/source/wayside-c/render_reviews.sh`（並排：`CMP=1 … render_reviews.sh -`）；審圖表：`sh art/source/wayside-c/make_sheets.sh`；路邊擺設：`BL=<blender> sh art/source/wayside-c/render_road.sh`；Unity：`UNITY=<Unity.exe 6000.3.28f1> sh art/source/wayside-c/unity/run_unity_check.sh`。

"""
tail=(ROOT/'art/source/wayside-c/readme_tail.md').read_text(encoding='utf-8')
(E/'README.md').write_text(head+'\n'.join(rows)+tail,encoding='utf-8');print('README written',len(rows),'items')
