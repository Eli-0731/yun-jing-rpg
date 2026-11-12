"""Writes art/exports/ground-cover-c/README.md from model_info.json (labeling-v1 §5 header, then per-item numbers).
python art/source/ground-cover-c/write_readme.py   (from the repo root)"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'art/exports/ground-cover-c'
info=json.loads((E/'model_info.json').read_text(encoding='utf-8'))
DESC={'GC01':('溪邊圓石散件一組（5 顆不同形）','練「被水沖圓的石頭：圓但不完美、底部埋土」。五顆形狀各不同：大而圓胖、扁長、高的蛋形、矮扁、小圓。每顆從一個球用幾個大的起伏和凹陷推出不對稱的外形，再磨出兩到四個平一點的面，底面較平（躺過河床）。暖灰和藍灰兩種石色，淺色石英脈、下半濕而較暗、一條藻線、凹處和腳邊的泥沙、淡淡的層理都畫在貼圖上。','cand-2（93）'),
      'GC02':('山路碎石散件一組（5 顆不同形）','練「有稜角的碎石，和 GC01 一眼分得出」。每顆是一堆散點的凸包：大大小小平的斷面、銳利的稜（4 mm 倒角，小石頭按比例縮小），面上一點低起伏，不是機器切的平面；底面切平。朝上最大的兩個斷面畫成較淺的新斷面，石縫裡的灰塵、舊面上的地衣、淡淡的層理在貼圖上。','cand-3（92）'),
      'GC03':('半埋在土裡的扁石一組（4 顆）','練「石頭和地面接觸的地方：一圈土、草」。每顆只做露出地面的圓拱頂（一顆大石的上 38%），底部平、z = 0，擺放時直接放在地面上；交界一圈壓實的土墊（貼著石頭最厚約 2 cm、往外 4–7 cm 漸薄、外緣參差），沿著土墊一圈短草（每叢草葉平均分方向）。石頭和它的土墊、草算同一個物件。裂縫、肩上的苔、和地面交界的土線畫在貼圖上。第一輪四張三視圖都只畫一顆，重生四張選 cand-6。','cand-6（93）'),
      'GC04':('地上的小野菇一叢（普通、不發光）','練「菇傘和菇柄、大小不一」。七朵普通菇，高 1.2–12.5 cm：一朵大的、三朵中的、三朵小的；菇柄略彎、根部粗、沾土，菇傘是有厚度的殼，下面是一個淺錐面的菇褶（放射紋畫在貼圖上），兩朵菇傘邊緣破了一塊；長在一小片低土堆上，十三片落葉一片疊一片（每片和下面那片隔 3 mm，不在同一個面上，Detail_）。顏色淺褐到褐，不發光。照工作包高度 0.15 m，比 cand-1 矮。','cand-1（92）'),
      'GC05':('長在倒木上的層狀菇','練「一片片半圓疊上去的層次」。每片菇是一個半圓的厚片：貼著樹皮最厚、往外變薄，上面微拱、邊緣略垂，後緣埋進樹皮 1 cm；左邊一叢五片、右邊一叢三片，上小下大往上疊，片和片之間留空。倒木是一段 0.38 m 的圓木（工作包深 0.2 m，所以斷面比較高瘦），兩端斷面碎爛、往中間凹，頂上一層苔和幾株小草（Detail_）。菇片的同心色帶、背面一條剝掉樹皮的爛木、腳邊濕痕畫在貼圖上。','cand-4（93）'),
      'GC06':('小落石堆','練「很多石頭堆在一起不穿插、不懸空」。24 顆石頭（20 顆有稜角、4 顆圓的）從大到小一顆顆放：每顆從上面往下放，用射線找出剛好碰到地面或下面石頭的高度（往下從它的頂點、往上從下面石頭的頂點），所以不穿插也不懸空；如果只靠一個離重心太遠的點撐著，就往外滑一點重放，直到落進石頭之間的凹處或地面；擺好後再檢查有沒有面和鄰石貼成同一個平面，有就轉個角度重放。堆底一片低土，腳邊 60 顆碎石用同樣的方法放（Detail_），下層石頭之間幾叢草（Detail_）；頂上石頭的新斷面畫淺色。','cand-4（93）'),
      'GC07':('枯枝散件一組（6 根不同形）','練「細長形狀的彎曲和分叉，每根能單獨擺」（11/08 工作包）。六根長 0.3–1.2 m，主枝是一條沿彎曲路徑漸細的管（粗的一端貼地，往細端彎、尾段折一下），細枝從主枝表面長出、多半貼著地面往側邊伸、只微微往上，七成再分一叉；兩端斷口的淺色木頭、剝落的樹皮、地衣都在貼圖上。六根都往同一邊彎，彼此不碰。每根是單獨物件、各自一個 FBX，原點在各自底部中心。','cand-1（93）'),
      'GC08':('松果與橡實散件一組（8 顆）','練「很小的東西要看得清楚輪廓」（11/08 工作包）。四顆松果（12、9、7、5 cm）各有 56–84 片鱗，沿 137.5° 的螺旋排在芯上，每片是窄根、寬身、厚鈍尖的舌形，下面的往外平張、越往上越往上收，每片稍微扭一點，輪廓靠鱗尖撐出來；四顆橡實是平滑的殼加一頂有粗紋的殼斗和短柄，一顆沒有殼斗、側躺。底部沾土在貼圖上。每顆是單獨物件、各自一個 FBX。','cand-3（93）')}
rows=[]
for k in sorted(info):
    d=info[k];l=d['lods'];name,desc,ref=DESC[k]
    tex=', '.join(sorted({f'{w}×{h}' for w,h in l['LOD0']['textures_px'].values()}))
    det=', '.join(d['detailObjects']) if d['detailObjects'] else '無'
    pcs=d.get('pieces',{})
    body=f"本體 {len(pcs)} 件，每件一個物件（`{k}_S1_LOD0`…，原點在各自底部中心）" if len(pcs)>1 else '本體 1'
    rows.append(f"### {k} {name}（{d['name']}，{d['version']}）\n\n{desc}\n\n"
      f"| 項目 | 數字 |\n|---|---|\n| 三視圖 | `art/references/{k}/`，選用 {ref} |\n"
      f"| 尺寸（寬 × 深 × 高） | {d['dimensions_xyz_m'][0]} × {d['dimensions_xyz_m'][1]} × {d['dimensions_xyz_m'][2]} m（上限 {' × '.join(str(x) for x in d['size_limit_xyz_m'])} m{'，整組排開' if len(pcs)>1 else ''}） |\n"
      +(f"| 每件尺寸 | {'；'.join(f'{n} {v[0]} × {v[1]} × {v[2]}' for n,v in pcs.items())} m |\n" if len(pcs)>1 else '')+
      f"| 三角面 LOD0 / LOD1 / LOD2 | {l['LOD0']['triangles']:,} / {l['LOD1']['triangles']:,} / {l['LOD2']['triangles']:,}（不含 Detail_：{l['LOD0']['triangles_without_detail']:,} / {l['LOD1']['triangles_without_detail']:,} / {l['LOD2']['triangles_without_detail']:,}） |\n"
      f"| 物件數（每個 LOD） | {l['LOD0']['objects']}（{body} + {det}） |\n"
      f"| 材質數 | 1（`{d['material']}`，全部共用） |\n| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，{tex} |\n"
      f"| minTier | {d['minTier']} |\n| 檔案 | `{d['files']['fbx']}`（LOD0–2）、`{d['files']['glb']}`（LOD0）、`{d['files']['blend']}`{"；單件 FBX `"+k+"_S1_v001.fbx`–`"+k+"_S"+str(len(pcs))+"_v001.fbx`（每件含 LOD0–2）" if d.get("stone_files") else ""} |\n")
head="""| 項目 | 內容 |
|---|---|
| 誰做的 | C（Eli-0731） |
| 工作包 | docs/execution/2026-11-07/C-128h-creekside-and-village-life.md 第二部分 B（GC01–GC06）；docs/execution/2026-11-08/C-40h-more-village-life.md 表 B（GC07–GC08） |
| ID | GC01–GC08 |
| 分支／PR | GC01–GC06：art/c-1112-gc01-06-ground-cover；GC07–GC08：art/c-1108-gc07-gc08-ground-bits ／ 開 PR 後補（一次一張，等前一張結案） |
| 版本 | v001（檔名帶 `_v001`；之後改版另存 v002，不覆寫） |
| 狀態 | Exported ／ Imported（Unity 6000.3.28f1 獨立匯入檢查）／ Visually Verified（Blender 與 Unity 審圖）／ In-game Verified：未驗（沒放進正式場景） |
| 素材來源 | 原創；三視圖參考在 `art/references/GC01/`–`art/references/GC08/` |

# 地上小石、野菇與林地小件 GC01–GC08

工作包第二部分 B：溪邊、山路、古林地面用的小石頭和野菇，讓地面不只是平的。靜態擺設，沒有玩法或動畫；擺進世界由核心組做。

**共同做法**
- 先生成三視圖（每件 4 張，GC03 重生一次共 8 張）、自評選一張（分數和取捨在各自的 `prompt.txt`），再做灰模（`art/previews/ground-cover-c/<ID>/clay/`），最後上貼圖。
- **GC01–GC03、GC07、GC08 每一件都能單獨拿出來擺**（工作包「不要焊成一塊」）：每件是自己的物件 `<ID>_S<n>_LOD0`（LOD1、LOD2 是 `_LOD1`、`_LOD2`），原點在那一件的底部中心，直接掛在整組的根 `<ID>_GroundOrigin` 下（根在排開時的腳印中心）。另外每件各匯出一個自己的 FBX `<ID>_S<n>_v001.fbx`（含 LOD0–2），要單獨擺時直接拖那個檔案。
- 原點在腳印中心、底部 z = 0，Blender −Y 是正面（FBX／Unity 是 −Z）。不附地面底板。
- 一件一個材質、一套 1024 貼圖；可有可無的小東西放 `Detail_*`（標準畫質關掉）。
- LOD1 約 50%、LOD2 約 15%，LOD0 不減面。`minTier`：GC01–GC05、GC07、GC08 是 `high`（增加豐富度的地面雜物），GC06 是 `standard`（石堆會擋路，場景要用 `body_dimensions` 加一個盒碰撞）。
- 建模流程和 village-life-c、creekside-life-c 相同，共用那裡的工具和來源貼圖；這裡只放 GC 自己的物件（`gc_items.py`）和建模腳本（`build_gc.py`）。
- 重建：`blender -b --factory-startup -P art/source/ground-cover-c/build_gc.py -- GC01 [--clay]`；審圖與 QA：`BL=<blender> sh art/source/ground-cover-c/render_reviews.sh`；Unity：`UNITY=<Unity.exe 6000.3.28f1> sh art/source/ground-cover-c/unity/run_unity_check.sh`。

"""
tail="""
## 驗證

- QA（`tools/art/qa_lod0_basic.py` 嚴格與寬鬆、`tools/art/qa_contact_glb.py`）：八件嚴格、寬鬆都是 0 項，結果在 `art/previews/ground-cover-c/qa/`。
- Unity 6000.3.28f1 獨立匯入：`art/previews/ground-cover-c/unity/report.txt`；`GC-stones-alone.png` 是從 GC01、GC02、GC03、GC07、GC08 各拿一件出來、用它自己的 FBX 單獨擺的樣子。
- 同光同角度並排（含 1.75 m 人形尺，灰模和成品各一張）：`art/previews/ground-cover-c/compare/`。GC01–GC03 對既有的苔石 A04、層岩 A05；GC04、GC05 對 C 的蕨 BM09_02 和落葉貼片 BM10_02；GC06 對 B 的石堆 CR03；`GC-set` 是 GC01–GC06 放在一起；GC07、GC08 對 GC05 倒木和 C 的落葉 BM10_02。

**和既有模型的三個共同點**
1. 石頭有層次：大塊柔和的深淺、濕和乾的分界、淡淡的層理和少量筆觸，和 A04、A05、CR03 一樣是暖灰石色。
2. 地面交界都有東西：GC01 腳邊的泥沙、GC03 的土墊和草、GC04 的土和落葉、GC06 的土和碎石，和 BM10 的地面貼片同一種土色。
3. 磨損有位置：GC02、GC06 朝上的新斷面較淺、舊面有地衣；GC01 下半濕暗；GC05 的爛木在斷面和剝皮處；GC07 的淺色斷口在兩端、地衣在朝上那面；GC08 的沾土只在底部。

## 已知問題與未驗

- 正式場景擺放、手機上的效果都未驗。
- GC03 只做地面以上的部分，放在斜坡上時底部會露出縫，需要稍微壓進地面。
- GC04 照工作包高度 0.15 m，菇比三視圖矮胖；菇傘是平滑的殼，三視圖裡的波浪邊沒有做。
- GC05：工作包深度 0.2 m，倒木的斷面高瘦；菇片的同心色帶在貼圖上，遠看不明顯。
- GC07：枯枝的斷口、樹皮剝落是貼圖，斷口沒有做出參差的木纖維。
- GC08：松果鱗片是有厚度的小方塊收成舌形，近看邊緣是直的。
- GC06：石堆高 0.48 m，比上限 0.6 m 矮；擺放規則是幾何近似（不是物理模擬），石頭都有碰到下面，但不保證每顆在真實重力下都穩。
"""
(E/'README.md').write_text(head+'\n'.join(rows)+tail,encoding='utf-8');print('README written',len(rows),'items')
