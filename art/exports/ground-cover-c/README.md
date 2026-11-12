| 項目 | 內容 |
|---|---|
| 誰做的 | C（Eli-0731） |
| 工作包 | docs/execution/2026-11-07/C-128h-creekside-and-village-life.md 第二部分 B（GC01–GC06） |
| ID | GC01–GC06 |
| 分支／PR | art/c-1112-gc01-06-ground-cover ／ 開 PR 後補（一次一張，等前一張結案） |
| 版本 | v001（檔名帶 `_v001`；之後改版另存 v002，不覆寫） |
| 狀態 | Exported ／ Imported（Unity 6000.3.28f1 獨立匯入檢查）／ Visually Verified（Blender 與 Unity 審圖）／ In-game Verified：未驗（沒放進正式場景） |
| 素材來源 | 原創；三視圖參考在 `art/references/GC01/`–`art/references/GC06/` |

# 地上小石與野菇 GC01–GC06

工作包第二部分 B：溪邊、山路、古林地面用的小石頭和野菇，讓地面不只是平的。靜態擺設，沒有玩法或動畫；擺進世界由核心組做。

**共同做法**
- 先生成三視圖（每件 4 張，GC03 重生一次共 8 張）、自評選一張（分數和取捨在各自的 `prompt.txt`），再做灰模（`art/previews/ground-cover-c/<ID>/clay/`），最後上貼圖。
- **GC01–GC03 每顆石頭都能單獨拿出來擺**（工作包「不要焊成一塊」）：每顆是自己的物件，掛在自己的空節點 `<ID>_S<n>` 下，節點在那顆石頭的底部中心，LOD0／1／2 都在它下面（Unity 會在每顆上各建一個 LODGroup）。整組的原點 `<ID>_GroundOrigin` 在排開時的腳印中心。
- 原點在腳印中心、底部 z = 0，Blender −Y 是正面（FBX／Unity 是 −Z）。不附地面底板。
- 一件一個材質、一套 1024 貼圖；可有可無的小東西放 `Detail_*`（標準畫質關掉）。
- LOD1 約 50%、LOD2 約 15%，LOD0 不減面。`minTier`：GC01–GC05 是 `high`（增加豐富度的地面雜物），GC06 是 `standard`（石堆會擋路，場景要用 `body_dimensions` 加一個盒碰撞）。
- 建模流程和 village-life-c、creekside-life-c 相同，共用那裡的工具和來源貼圖；這裡只放 GC 自己的物件（`gc_items.py`）和建模腳本（`build_gc.py`）。
- 重建：`blender -b --factory-startup -P art/source/ground-cover-c/build_gc.py -- GC01 [--clay]`；審圖與 QA：`BL=<blender> sh art/source/ground-cover-c/render_reviews.sh`；Unity：`UNITY=<Unity.exe 6000.3.28f1> sh art/source/ground-cover-c/unity/run_unity_check.sh`。

### GC01 溪邊圓石散件一組（5 顆不同形）（CreekPebbles，v001）

練「被水沖圓的石頭：圓但不完美、底部埋土」。五顆形狀各不同：大而圓胖、扁長、高的蛋形、矮扁、小圓。每顆從一個球用幾個大的起伏和凹陷推出不對稱的外形，再磨出兩到四個平一點的面，底面較平（躺過河床）。暖灰和藍灰兩種石色，淺色石英脈、下半濕而較暗、一條藻線、凹處和腳邊的泥沙、淡淡的層理都畫在貼圖上。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/GC01/`，選用 cand-2（93） |
| 尺寸（寬 × 深 × 高） | 1.658 × 0.32 × 0.26 m（上限 1.8 × 0.5 × 0.4 m，整組排開） |
| 每顆尺寸 | S1 0.399 × 0.32 × 0.26；S2 0.316 × 0.205 × 0.14；S3 0.199 × 0.17 × 0.2；S4 0.212 × 0.159 × 0.1；S5 0.119 × 0.109 × 0.09 m |
| 三角面 LOD0 / LOD1 / LOD2 | 6,400 / 3,200 / 960（不含 Detail_：6,400 / 3,200 / 960） |
| 物件數（每個 LOD） | 5（本體 5 顆，每顆一個物件（`GC01_S1`…，原點在各自底部中心、各自一個 LOD 組） + 無） |
| 材質數 | 1（`M_GC01_CreekPebbles`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | high |
| 檔案 | `art/exports/ground-cover-c/GC01_v001.fbx`（LOD0–2）、`art/exports/ground-cover-c/GC01_v001.glb`（LOD0）、`art/source/ground-cover-c/GC01_v001.blend` |

### GC02 山路碎石散件一組（5 顆不同形）（PathRubble，v001）

練「有稜角的碎石，和 GC01 一眼分得出」。每顆是一堆散點的凸包：大大小小平的斷面、銳利的稜（4 mm 倒角，小石頭按比例縮小），面上一點低起伏，不是機器切的平面；底面切平。朝上最大的兩個斷面畫成較淺的新斷面，石縫裡的灰塵、舊面上的地衣、淡淡的層理在貼圖上。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/GC02/`，選用 cand-3（92） |
| 尺寸（寬 × 深 × 高） | 1.361 × 0.255 × 0.212 m（上限 1.4 × 0.4 × 0.3 m，整組排開） |
| 每顆尺寸 | S1 0.288 × 0.255 × 0.158；S2 0.217 × 0.134 × 0.141；S3 0.115 × 0.092 × 0.212；S4 0.207 × 0.151 × 0.071；S5 0.118 × 0.099 × 0.071 m |
| 三角面 LOD0 / LOD1 / LOD2 | 2,926 / 1,460 / 434（不含 Detail_：2,926 / 1,460 / 434） |
| 物件數（每個 LOD） | 5（本體 5 顆，每顆一個物件（`GC02_S1`…，原點在各自底部中心、各自一個 LOD 組） + 無） |
| 材質數 | 1（`M_GC02_PathRubble`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | high |
| 檔案 | `art/exports/ground-cover-c/GC02_v001.fbx`（LOD0–2）、`art/exports/ground-cover-c/GC02_v001.glb`（LOD0）、`art/source/ground-cover-c/GC02_v001.blend` |

### GC03 半埋在土裡的扁石一組（4 顆）（HalfBuriedFlatStones，v001）

練「石頭和地面接觸的地方：一圈土、草」。每顆只做露出地面的圓拱頂（一顆大石的上 38%），底部平、z = 0，擺放時直接放在地面上；交界一圈壓實的土墊（貼著石頭最厚約 2 cm、往外 4–7 cm 漸薄、外緣參差），沿著土墊一圈短草（每叢草葉平均分方向）。石頭和它的土墊、草算同一個物件。裂縫、肩上的苔、和地面交界的土線畫在貼圖上。第一輪四張三視圖都只畫一顆，重生四張選 cand-6。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/GC03/`，選用 cand-6（93） |
| 尺寸（寬 × 深 × 高） | 2.35 × 0.535 × 0.153 m（上限 2.6 × 0.75 × 0.3 m，整組排開） |
| 每顆尺寸 | S1 0.68 × 0.514 × 0.152；S2 0.531 × 0.491 × 0.122；S3 0.458 × 0.42 × 0.107；S4 0.42 × 0.354 × 0.092 m |
| 三角面 LOD0 / LOD1 / LOD2 | 10,012 / 5,004 / 1,500（不含 Detail_：10,012 / 5,004 / 1,500） |
| 物件數（每個 LOD） | 4（本體 4 顆，每顆一個物件（`GC03_S1`…，原點在各自底部中心、各自一個 LOD 組） + 無） |
| 材質數 | 1（`M_GC03_HalfBuriedFlatStones`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | high |
| 檔案 | `art/exports/ground-cover-c/GC03_v001.fbx`（LOD0–2）、`art/exports/ground-cover-c/GC03_v001.glb`（LOD0）、`art/source/ground-cover-c/GC03_v001.blend` |

### GC04 地上的小野菇一叢（普通、不發光）（WildMushroomCluster，v001）

練「菇傘和菇柄、大小不一」。七朵普通菇，高 1.2–12.5 cm：一朵大的、三朵中的、三朵小的；菇柄略彎、根部粗、沾土，菇傘是有厚度的殼，下面是一個淺錐面的菇褶（放射紋畫在貼圖上），兩朵菇傘邊緣破了一塊；長在一小片低土堆上，十三片落葉一片疊一片（每片和下面那片隔 3 mm，不在同一個面上，Detail_）。顏色淺褐到褐，不發光。照工作包高度 0.15 m，比 cand-1 矮。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/GC04/`，選用 cand-1（92） |
| 尺寸（寬 × 深 × 高） | 0.286 × 0.277 × 0.124 m（上限 0.3 × 0.3 × 0.15 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 10,150 / 5,074 / 1,522（不含 Detail_：8,990 / 4,494 / 1,348） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_Leaves） |
| 材質數 | 1（`M_GC04_WildMushroomCluster`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | high |
| 檔案 | `art/exports/ground-cover-c/GC04_v001.fbx`（LOD0–2）、`art/exports/ground-cover-c/GC04_v001.glb`（LOD0）、`art/source/ground-cover-c/GC04_v001.blend` |

### GC05 長在倒木上的層狀菇（BracketFungusLog，v001）

練「一片片半圓疊上去的層次」。每片菇是一個半圓的厚片：貼著樹皮最厚、往外變薄，上面微拱、邊緣略垂，後緣埋進樹皮 1 cm；左邊一叢五片、右邊一叢三片，上小下大往上疊，片和片之間留空。倒木是一段 0.38 m 的圓木（工作包深 0.2 m，所以斷面比較高瘦），兩端斷面碎爛、往中間凹，頂上一層苔和幾株小草（Detail_）。菇片的同心色帶、背面一條剝掉樹皮的爛木、腳邊濕痕畫在貼圖上。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/GC05/`，選用 cand-4（93） |
| 尺寸（寬 × 深 × 高） | 0.4 × 0.181 × 0.237 m（上限 0.4 × 0.2 × 0.3 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 4,492 / 2,246 / 673（不含 Detail_：4,092 / 2,046 / 613） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_Plants） |
| 材質數 | 1（`M_GC05_BracketFungusLog`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | high |
| 檔案 | `art/exports/ground-cover-c/GC05_v001.fbx`（LOD0–2）、`art/exports/ground-cover-c/GC05_v001.glb`（LOD0）、`art/source/ground-cover-c/GC05_v001.blend` |

### GC06 小落石堆（RockfallPile，v001）

練「很多石頭堆在一起不穿插、不懸空」。24 顆石頭（20 顆有稜角、4 顆圓的）從大到小一顆顆放：每顆從上面往下放，用射線找出剛好碰到地面或下面石頭的高度（往下從它的頂點、往上從下面石頭的頂點），所以不穿插也不懸空；如果只靠一個離重心太遠的點撐著，就往外滑一點重放，直到落進石頭之間的凹處或地面；擺好後再檢查有沒有面和鄰石貼成同一個平面，有就轉個角度重放。堆底一片低土，腳邊 60 顆碎石用同樣的方法放（Detail_），下層石頭之間幾叢草（Detail_）；頂上石頭的新斷面畫淺色。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/GC06/`，選用 cand-4（93） |
| 尺寸（寬 × 深 × 高） | 1.148 × 0.942 × 0.478 m（上限 1.2 × 1.0 × 0.6 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 14,242 / 7,120 / 2,134（不含 Detail_：13,064 / 6,532 / 1,958） |
| 物件數（每個 LOD） | 3（本體 1 + Detail_Grass, Detail_Gravel） |
| 材質數 | 1（`M_GC06_RockfallPile`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 檔案 | `art/exports/ground-cover-c/GC06_v001.fbx`（LOD0–2）、`art/exports/ground-cover-c/GC06_v001.glb`（LOD0）、`art/source/ground-cover-c/GC06_v001.blend` |

## 驗證

- QA（`tools/art/qa_lod0_basic.py` 嚴格與寬鬆、`tools/art/qa_contact_glb.py`）：六件嚴格、寬鬆都是 0 項，結果在 `art/previews/ground-cover-c/qa/`。
- Unity 6000.3.28f1 獨立匯入：`art/previews/ground-cover-c/unity/report.txt`；`GC-stones-alone.png` 是從 GC01、GC02、GC03 各拿一顆出來單獨擺的樣子。
- 同光同角度並排（含 1.75 m 人形尺，灰模和成品各一張）：`art/previews/ground-cover-c/compare/`。GC01–GC03 對既有的苔石 A04、層岩 A05；GC04、GC05 對 C 的蕨 BM09_02 和落葉貼片 BM10_02；GC06 對 B 的石堆 CR03；`GC-set` 是六件放在一起。

**和既有模型的三個共同點**
1. 石頭有層次：大塊柔和的深淺、濕和乾的分界、淡淡的層理和少量筆觸，和 A04、A05、CR03 一樣是暖灰石色。
2. 地面交界都有東西：GC01 腳邊的泥沙、GC03 的土墊和草、GC04 的土和落葉、GC06 的土和碎石，和 BM10 的地面貼片同一種土色。
3. 磨損有位置：GC02、GC06 朝上的新斷面較淺、舊面有地衣；GC01 下半濕暗；GC05 的爛木在斷面和剝皮處。

## 已知問題與未驗

- 正式場景擺放、手機上的效果都未驗。
- GC03 只做地面以上的部分，放在斜坡上時底部會露出縫，需要稍微壓進地面。
- GC04 照工作包高度 0.15 m，菇比三視圖矮胖；菇傘是平滑的殼，三視圖裡的波浪邊沒有做。
- GC05：工作包深度 0.2 m，倒木的斷面高瘦；菇片的同心色帶在貼圖上，遠看不明顯。
- GC06：石堆高 0.48 m，比上限 0.6 m 矮；擺放規則是幾何近似（不是物理模擬），石頭都有碰到下面，但不保證每顆在真實重力下都穩。
