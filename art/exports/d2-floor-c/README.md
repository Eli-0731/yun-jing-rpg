| 項目 | 內容 |
|---|---|
| 誰做的 | C（Eli-0731） |
| 工作包 | docs/execution/2026-11-15/C-300h-D2-small-life.md，C 批；標準照 docs/execution/2026-11-15/00-300h-共同標準.md |
| ID | 已做：DP17 小石與碎石（八種）、DP18 松果與落果（三種）、DP19 落葉堆（三種），都是 v001。DP14 細枯枝、DP15 中斷枝、DP16 樹皮片、DP20 細根網、DP21 小朽樹樁、DP22 水窪落葉要用共同標準第五節的 `bark_brown_02` 掃描樹皮，等下載許可後再做 |
| 分支／PR | art/c-1115-d2-floor-smalls ／ 開 PR 後補 |
| 版本 | v001 |
| 狀態 | Exported ／ Imported（Unity 6000.3.28f1 獨立匯入檢查）／ Visually Verified（Blender 審圖、和 D2 設定圖並排）／ In-game Verified：未驗（沒放進正式場景） |
| 素材來源 | 原創；三視圖參考在 `art/references/DP14/`–`DP22/`；貼圖全部在建模腳本裡畫，沒有外部素材 |
| 實際工時 | 2026-11-23（台灣時間），約 4 小時：三視圖 192 張與自評（DP20 三種重畫一次）、套件建立、DP17–DP19 建模、灰模每組兩到三輪、上貼圖兩輪、QA、審圖、Unity 檢查 |

# D2 地上的小東西（d2-floor-c）

11/15 的 300 小時包 C 批：D2 古樹神木地上的小石、細枝、樹皮片、松果、落葉、細根、小樹樁（設定圖 V2–V6）。靜態擺設；擺進世界由核心組做，這裡不改主場景、不改區塊 JSON。使用者 2026-11-22 決定不等樣品審查，整批先做完。

**共同做法**
- 先生成三視圖（每種 4 張）、自評選一張（分數和取捨在 `art/references/<ID>/prompt.txt`），再做灰模（`art/previews/d2-floor-c/<ID>/clay/`），最後上貼圖。
- 原點：底部中心，z = 0 在地面；埋進土裡的部分往下延伸（小石埋 25–40%），擺在不平的地上不會浮空（共同標準第四節）。Blender −Y 是正面（FBX／Unity 是 −Z）。
- 一件一個材質、一套 1024 貼圖（Albedo／Normal／ORM／MaskURP），雙面。沒有 `Detail_*`。`minTier` 都是 `standard`。LOD1 約 50%、LOD2 約 15%。
- 石材：核心組的 SS01 半埋踏石還沒在 main 上，石頭照 D2 設定圖 V6 的中灰自己畫；DS07 擺好之後可以再對一次顏色。
- 建模流程和 `art/source/d2-mushrooms-c/build_dp.py`（DP01–DP05，在 art/c-1115-d2-mushrooms 分支，還沒進 main）相同，複製成 `build_floor.py`，共用零件在 `floor_base.py`；工具（`creekside-life-c/wl_kit.py`）用 main 上的。亂數種子固定，重建結果一樣。
- 重建：`blender -b --factory-startup -P art/source/d2-floor-c/build_floor.py -- DP17_01 [...] [--clay]`；審圖：`BL=<blender> sh art/source/d2-floor-c/render_reviews.sh`；總表與 D2 並排：`D2=<放 D2 V1–V6.png 的資料夾> sh art/source/d2-floor-c/make_sheets.sh`；Unity：`UNITY=<Unity.exe 6000.3.28f1> sh art/source/d2-floor-c/unity/run_unity_check.sh`。

### DP17_01 小石・圓小石（PebbleRound，v001）

一顆 6 cm 的圓小石，半埋。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP17/`，選用 A cand-4（90） |
| 尺寸（寬 × 深 × 高） | 0.055 × 0.052 × 0.04 m（高度含地下的苔墊） |
| 三角面 LOD0 / LOD1 / LOD2 | 320 / 160 / 48（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP17_01_PebbleRound`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP17_01_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP17_01_v001.glb`（LOD0）、`art/source/d2-floor-c/DP17_01_v001.blend` |

### DP17_02 小石・角石一小群（PebbleCluster，v001）

五顆 3–11 cm 的角石，中間一顆高而尖，半埋。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP17/`，選用 B cand-3（90） |
| 尺寸（寬 × 深 × 高） | 0.152 × 0.121 × 0.1 m（高度含地下的苔墊） |
| 三角面 LOD0 / LOD1 / LOD2 | 640 / 320 / 96（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP17_02_PebbleCluster`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP17_02_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP17_02_v001.glb`（LOD0）、`art/source/d2-floor-c/DP17_02_v001.blend` |

### DP17_03 小石・扁平石（StoneFlatMossy，v001）

一顆 15 cm 的扁石，頂上一塊薄苔。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP17/`，選用 C cand-2（90） |
| 尺寸（寬 × 深 × 高） | 0.15 × 0.108 × 0.06 m（高度含地下的苔墊） |
| 三角面 LOD0 / LOD1 / LOD2 | 1,623 / 810 / 242（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP17_03_StoneFlatMossy`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP17_03_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP17_03_v001.glb`（LOD0）、`art/source/d2-floor-c/DP17_03_v001.blend` |

### DP17_04 小石・圓苔石（StoneRoundMossy，v001）

一顆 19 cm 的圓石，頂上和一側有苔。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP17/`，選用 D cand-1（90） |
| 尺寸（寬 × 深 × 高） | 0.19 × 0.164 × 0.14 m（高度含地下的苔墊） |
| 三角面 LOD0 / LOD1 / LOD2 | 1,569 / 784 / 235（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP17_04_StoneRoundMossy`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP17_04_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP17_04_v001.glb`（LOD0）、`art/source/d2-floor-c/DP17_04_v001.blend` |

### DP17_05 小石・楔形角石（StoneAngular，v001）

一顆 25 cm 高、往上收尖的角石，有裂面。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP17/`，選用 E cand-1（90） |
| 尺寸（寬 × 深 × 高） | 0.178 × 0.1 × 0.247 m（高度含地下的苔墊） |
| 三角面 LOD0 / LOD1 / LOD2 | 1,280 / 640 / 192（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP17_05_StoneAngular`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP17_05_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP17_05_v001.glb`（LOD0）、`art/source/d2-floor-c/DP17_05_v001.blend` |

### DP17_06 小石・兩顆一對（StonePair，v001）

一大一小兩顆石頭靠在一起，縫裡長苔。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP17/`，選用 F cand-1（90） |
| 尺寸（寬 × 深 × 高） | 0.28 × 0.164 × 0.16 m（高度含地下的苔墊） |
| 三角面 LOD0 / LOD1 / LOD2 | 2,849 / 1,423 / 426（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP17_06_StonePair`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP17_06_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP17_06_v001.glb`（LOD0）、`art/source/d2-floor-c/DP17_06_v001.blend` |

### DP17_07 小石・苔帽圓石（StoneMossCap，v001）

一顆 30 cm 的圓石，頂上一塊苔帽。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP17/`，選用 G cand-2（90） |
| 尺寸（寬 × 深 × 高） | 0.298 × 0.257 × 0.24 m（高度含地下的苔墊） |
| 三角面 LOD0 / LOD1 / LOD2 | 1,627 / 813 / 243（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP17_07_StoneMossCap`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP17_07_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP17_07_v001.glb`（LOD0）、`art/source/d2-floor-c/DP17_07_v001.blend` |

### DP17_08 小石・大石（StoneLarge，v001）

一顆 39 cm 的大石，一面平，頂上有苔。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP17/`，選用 H cand-1（90） |
| 尺寸（寬 × 深 × 高） | 0.388 × 0.318 × 0.26 m（高度含地下的苔墊） |
| 三角面 LOD0 / LOD1 / LOD2 | 1,370 / 685 / 205（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP17_08_StoneLarge`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP17_08_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP17_08_v001.glb`（LOD0）、`art/source/d2-floor-c/DP17_08_v001.blend` |

### DP18_01 松果與落果・松果（PineConesThree，v001）

三顆 6–9 cm 張開的松果躺在地上，鱗片一片片做出來。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP18/`，選用 A cand-3（90） |
| 尺寸（寬 × 深 × 高） | 0.181 × 0.099 × 0.054 m（高度含地下的苔墊） |
| 三角面 LOD0 / LOD1 / LOD2 | 2,544 / 1,272 / 381（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP18_01_PineConesThree`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP18_01_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP18_01_v001.glb`（LOD0）、`art/source/d2-floor-c/DP18_01_v001.blend` |

### DP18_02 松果與落果・堅果（NutsAndAcorns，v001）

八顆小堅果和帶殼斗的種子，兩片乾葉。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP18/`，選用 B cand-3（90） |
| 尺寸（寬 × 深 × 高） | 0.118 × 0.132 × 0.03 m（高度含地下的苔墊） |
| 三角面 LOD0 / LOD1 / LOD2 | 960 / 480 / 144（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP18_02_NutsAndAcorns`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP18_02_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP18_02_v001.glb`（LOD0）、`art/source/d2-floor-c/DP18_02_v001.blend` |

### DP18_03 松果與落果・野果（WildFruits，v001）

五顆 2–3 cm 的暗紅褐野果，一顆裂開露出淺色果肉，兩片乾葉。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP18/`，選用 C cand-1（90） |
| 尺寸（寬 × 深 × 高） | 0.175 × 0.16 × 0.029 m（高度含地下的苔墊） |
| 三角面 LOD0 / LOD1 / LOD2 | 752 / 376 / 112（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP18_03_WildFruits`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP18_03_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP18_03_v001.glb`（LOD0）、`art/source/d2-floor-c/DP18_03_v001.blend` |

### DP19_01 落葉堆・小（LeafPileSmall，v001）

0.39 m 的一小堆落葉，一百二十片葉子一片片疊起來。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP19/`，選用 A cand-2（90） |
| 尺寸（寬 × 深 × 高） | 0.383 × 0.348 × 0.09 m（高度含地下的苔墊） |
| 三角面 LOD0 / LOD1 / LOD2 | 2,080 / 1,040 / 312（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP19_01_LeafPileSmall`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP19_01_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP19_01_v001.glb`（LOD0）、`art/source/d2-floor-c/DP19_01_v001.blend` |

### DP19_02 落葉堆・中（LeafPileMedium，v001）

0.6 m 的落葉堆，上層乾紅褐、黃褐，下層暗濕褐。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP19/`，選用 B cand-2（90） |
| 尺寸（寬 × 深 × 高） | 0.605 × 0.569 × 0.126 m（高度含地下的苔墊） |
| 三角面 LOD0 / LOD1 / LOD2 | 2,920 / 1,460 / 438（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP19_02_LeafPileMedium`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP19_02_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP19_02_v001.glb`（LOD0）、`art/source/d2-floor-c/DP19_02_v001.blend` |

### DP19_03 落葉堆・長條（LeafDrift，v001）

0.9 m 長、沿邊緣堆起的一長條落葉。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP19/`，選用 C cand-2（90） |
| 尺寸（寬 × 深 × 高） | 0.914 × 0.344 × 0.13 m（高度含地下的苔墊） |
| 三角面 LOD0 / LOD1 / LOD2 | 3,040 / 1,520 / 456（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP19_03_LeafDrift`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP19_03_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP19_03_v001.glb`（LOD0）、`art/source/d2-floor-c/DP19_03_v001.blend` |

## 驗證（DP17–DP19）

- QA 嚴格：14 件都是 0。寬鬆：DP17、DP18_02、DP18_03 是 0；DP18_01 松果鱗片交錯 8 對，DP19 落葉堆 12–19 對（一片片分開的葉子疊在一起時，有些在 1 mm 內幾乎平行；再拉開葉堆就會變稀）。接觸：DP17、DP18 在 3 mm 內；DP19 落葉堆最大 10.4 mm（最上層幾片葉子架在別的葉子上，留一點縫）。
- Unity 6000.3.28f1 獨立匯入：224 項 PASS、0 項 FAIL（`art/previews/d2-floor-c/unity/report.txt`）。埋進土裡的檢查改成「往地下 0.3–12 cm」，因為小石埋得比苔墊深。
- 面數：每件 LOD0 ≤ 4,000（逐件在 model_info）。

## 視覺檢查紀錄

1. DP17 灰模：石頭像麵團 → 每顆加平面切面，切面用平面著色、稜邊清楚；楔形角石像方磚 → 往上收窄、略斜。上貼圖第一輪：面數只有 320–445（Blender 球體細分 3 只有 320 面，我算錯了）→ 改細分 4 重建；和 D2 並排偏藍、黑斑多 → 改成暖的中灰、細碎色塊；苔像地毯蓋滿頂 → 改成一塊塊，再把苔的邊緣順過（照三角面選會變成階梯）。
2. DP18 灰模：松果鱗片是一堆亂刺 → 鱗片朝尖端斜出、一排排疊起來。
3. DP19：葉片尖角太多 → 少用分裂葉；上層葉子浮空 15 mm → 每層葉子落在下一層上、底下的核心加高，落葉長條的核心移到最高的那一側。

**自評（和 D2 設定圖並排）**
- DP17 小石約 60%：形狀和半埋的樣子對得上；V6 的石頭有更細的筆觸和亮邊，近看比成品細緻。
- DP18 松果落果約 65%：松果和堅果的形狀、顏色對得上；V6 裡這麼小的東西看不清，主要對三視圖。
- DP19 落葉堆約 60%：乾濕兩色、一片片的葉子對得上；葉形比較單純（橢圓為主）。

**已知問題與未驗**
- 工作包的「擺幾處」由核心組擺。
- 正式場景擺放、手機上的效果都未驗；不寫幀率。
