| 項目 | 內容 |
|---|---|
| 誰做的 | C（Eli-0731） |
| 工作包 | docs/execution/2026-11-15/C-300h-D2-small-life.md，B 批；標準照 docs/execution/2026-11-15/00-300h-共同標準.md |
| ID | DP06 苔團（六種，v002）；DP07 苔被片（六種）、DP08 小蕨（三種）、DP09 林下地被（四種）、DP10 垂藤（四種）、DP11 莎草（三種）、DP12 枯小灌叢（三種）、DP13 地衣片（四種），都是 v001 |
| 分支／PR | art/c-1115-d2-moss-plants ／ 開 PR 後補 |
| 版本 | DP06 是 v002（v001 的母稿、模型及貼圖保留）；DP07 起是 v001。 |
| 狀態 | Exported ／ Unity 6000.3.28f1 匯入結果見驗證紀錄／ Blender 並排審圖完成 ／ 正式 D2 場景驗收待驗 |
| 素材來源 | 原創；三視圖參考在 `art/references/DP06/`–`DP13/`；貼圖全部在建模腳本裡畫，沒有外部素材 |
| 實際工時 | DP06 v001：2026-11-19（台灣時間），約 3 小時。DP07–DP13 v001：2026-11-22 至 11-23，約 6 小時：三視圖 108 張與自評、建模、灰模每組兩到三輪、上貼圖一到兩輪、QA、審圖、Unity 檢查 |

# D2 古樹神木的苔與小植物（d2-moss-c）

11/15 的 300 小時包 B 批：D2 古樹神木地上的苔與小植物（設定圖 V2、V3、V5、V6）。DP06–DP13 都已做（使用者 2026-11-22 決定不等樣品審查，整批先做完）。靜態擺設；擺進世界由核心組做，這裡不改主場景、不改區塊 JSON。

**共同做法**
- 先生成三視圖（每種 4 張）、自評選一張（分數和取捨在 `art/references/DP06/prompt.txt`），再做灰模（`art/previews/d2-moss-c/<ID>/clay/`），最後上貼圖。
- 苔團是真的幾何：不規則帶瓣的外形（邊緣有細的鋸齒）、幾個大瓣、上面許多小苔球凸起；頂面用平均分布的點做 Delaunay 三角化，沒有中心放射的扇形面。一撮撮的苔尖畫在貼圖和法線上。沒有用卡片。
- 原點：底部中心，z = 0 在地面；苔的邊緣正好落在 z = 0，底下一圈土裙往地下 1.5 cm（DP06_06 的小叢 1 cm）（共同標準第四節），擺在不平的地上不會浮空。DP06_05 石頂苔帽例外：z = 0 是下垂邊緣的最低處，底下是空的，扣在石頭上。Blender −Y 是正面（FBX／Unity 是 −Z）。
- 一件一個材質、一套 1024 貼圖（Albedo／Normal／ORM／MaskURP），雙面。沒有 `Detail_*`。`minTier` 都是 `standard`。
- LOD：LOD1 約 50%、LOD2 約 15%（共同標準第四節）。
- 顏色照 D2：暗橄欖綠，朝天的苔尖帶一點暗黃綠，苔撮之間是暗縫；不是亮綠。三視圖本身比 D2 亮、偏黃，顏色不照三視圖。
- 建模流程和 `art/source/d2-mushrooms-c/build_dp.py`（DP01）相同（來源貼圖 → 一張 UV 圖集 → Cycles 烘焙），因為那個套件還沒進 main，所以把流程複製成 `build_moss.py`，工具（`creekside-life-c/wl_kit.py`）用 main 上的。亂數種子固定，重建結果一樣。
- 重建：`blender -b --factory-startup -P art/source/d2-moss-c/build_moss.py -- DP06_01 [DP06_02 ...] [--clay]`；審圖、QA、D2 對圖用的渲染：`BL=<blender> sh art/source/d2-moss-c/render_reviews.sh`；審圖總表和 D2 並排圖：`D2=<放 D2 V1–V6.png 的資料夾> sh art/source/d2-moss-c/make_sheets.sh`；Unity：`UNITY=<Unity.exe 6000.3.28f1> sh art/source/d2-moss-c/unity/run_unity_check.sh`。


**v002**
- 多瓣中丘加深瓣與瓣之間的凹谷。從連續苔面抬出小撮鈍頭幾何，減掉底層不需要的面數；修飾舊版粗塊狀的凹凸與苔尖色。早期的尖端在並排圖上呈現刺狀，已改成較低的鈍頭。
- 使用既有候選及選圖；v002 的貼圖在 `art/textures/d2-moss-c/v002/`。
### DP06_01 苔團・小圓墊（MossCushionSmall，v002）

一團低圓的苔墊（約 0.25 × 0.25 m、高約 0.10 m），表面一團團小苔球，邊緣散出細苔鬚。放地上、根旁、石頭腳下。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP06/`，選用 A cand-3（90） |
| 尺寸（寬 × 深 × 高） | 0.248 × 0.247 × 0.102 m（高度含地下的土裙） |
| 三角面 LOD0 / LOD1 / LOD2 | 2,968 / 1,484 / 445（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP06_01_MossCushionSmall`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP06_01_v002.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP06_01_v002.glb`（LOD0）、`art/source/d2-moss-c/DP06_01_v002.blend` |

### DP06_02 苔團・多瓣中丘（MossMoundLobed，v002）

三、四個大小不同的圓瓣併成一丘（約 0.42 × 0.41 m、高約 0.18 m），瓣間有凹縫。像 V6 石邊那團。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP06/`，選用 B cand-1（91） |
| 尺寸（寬 × 深 × 高） | 0.423 × 0.41 × 0.185 m（高度含地下的土裙） |
| 三角面 LOD0 / LOD1 / LOD2 | 3,674 / 1,837 / 551（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP06_02_MossMoundLobed`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP06_02_v002.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP06_02_v002.glb`（LOD0）、`art/source/d2-moss-c/DP06_02_v002.blend` |

### DP06_03 苔團・大片低鋪（MossPatchSpreading，v002）

一大片低平的苔（約 0.80 × 0.65 m、只高約 0.12 m），有幾處緩丘，外形不規則帶瓣。鋪在林床、根和根之間。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP06/`，選用 C cand-3（90） |
| 尺寸（寬 × 深 × 高） | 0.805 × 0.652 × 0.116 m（高度含地下的土裙） |
| 三角面 LOD0 / LOD1 / LOD2 | 3,832 / 1,915 / 574（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP06_03_MossPatchSpreading`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP06_03_v002.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP06_03_v002.glb`（LOD0）、`art/source/d2-moss-c/DP06_03_v002.blend` |

### DP06_04 苔團・沿根腳長條（MossRootFootStrip，v002）

一串緩丘排成微彎的長條（約 0.60 × 0.22 m），兩端收尖，貼著任一段根的根腳放。根不在模型裡（根是 Josh 的 DR 系列）。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP06/`，選用 D cand-1（91） |
| 尺寸（寬 × 深 × 高） | 0.602 × 0.215 × 0.146 m（高度含地下的土裙） |
| 三角面 LOD0 / LOD1 / LOD2 | 3,452 / 1,726 / 517（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP06_04_MossRootFootStrip`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP06_04_v002.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP06_04_v002.glb`（LOD0）、`art/source/d2-moss-c/DP06_04_v002.blend` |

### DP06_05 苔團・石頂苔帽（MossBoulderCap，v002）

一頂圓的苔帽（約 0.47 × 0.40 m、高約 0.17 m），邊緣往下垂，底下是空的，整合時扣在任一顆石頭頂上（像 V3、V6 石頭頂的苔）。z = 0 是下垂邊緣的最低處，沒有土裙。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP06/`，選用 E cand-1（91） |
| 尺寸（寬 × 深 × 高） | 0.473 × 0.403 × 0.162 m（高度含地下的土裙） |
| 三角面 LOD0 / LOD1 / LOD2 | 3,720 / 1,860 / 558（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP06_05_MossBoulderCap`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP06_05_v002.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP06_05_v002.glb`（LOD0）、`art/source/d2-moss-c/DP06_05_v002.blend` |

### DP06_06 苔團・碎散小叢（MossTuftsScattered，v002）

一叢大的加六叢小的，各自分開，散在約 0.49 × 0.38 m 內。每叢都有自己的土裙。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP06/`，選用 F cand-4（90） |
| 尺寸（寬 × 深 × 高） | 0.486 × 0.385 × 0.109 m（高度含地下的土裙） |
| 三角面 LOD0 / LOD1 / LOD2 | 3,540 / 1,769 / 530（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP06_06_MossTuftsScattered`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP06_06_v002.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP06_06_v002.glb`（LOD0）、`art/source/d2-moss-c/DP06_06_v002.blend` |

### DP07_01 苔被片・石頂苔帽（MossSheetBoulderCap，v001）

一層薄苔像帽子蓋在圓石頂（宿主半徑約 0.55 m），2–4 cm 厚，有低墊，邊緣細鬚往下垂。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP07/`，選用 A cand-1（90） |
| 尺寸（寬 × 深 × 高） | 0.893 × 0.733 × 0.283 m（抬高到最低點在 z = 0；宿主貼合點見 model_info） |
| 三角面 LOD0 / LOD1 / LOD2 | 3,064 / 1,532 / 459（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP07_01_MossSheetBoulderCap`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP07_01_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP07_01_v001.glb`（LOD0）、`art/source/d2-moss-c/DP07_01_v001.blend` |

### DP07_02 苔被片・平石苔片（MossSheetFlat，v001）

平石面上一片 1–3 cm 的薄苔，幾個低墊、破邊。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP07/`，選用 B cand-1（90） |
| 尺寸（寬 × 深 × 高） | 0.567 × 0.499 × 0.042 m（抬高到最低點在 z = 0；宿主貼合點見 model_info） |
| 三角面 LOD0 / LOD1 / LOD2 | 2,726 / 1,362 / 408（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP07_02_MossSheetFlat`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP07_02_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP07_02_v001.glb`（LOD0）、`art/source/d2-moss-c/DP07_02_v001.blend` |

### DP07_03 苔被片・根頂苔條（MossSheetRootTop，v001）

沿著根頂（半徑約 0.12 m）的一條 1 m 長苔，往兩側垂一點。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP07/`，選用 C cand-1（90） |
| 尺寸（寬 × 深 × 高） | 1.078 × 0.219 × 0.096 m（抬高到最低點在 z = 0；宿主貼合點見 model_info） |
| 三角面 LOD0 / LOD1 / LOD2 | 3,148 / 1,574 / 471（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP07_03_MossSheetRootTop`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP07_03_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP07_03_v001.glb`（LOD0）、`art/source/d2-moss-c/DP07_03_v001.blend` |

### DP07_04 苔被片・石側垂苔（MossSheetStoneSide，v001）

貼在石頭直面上的一片薄苔，下緣是長短不一的苔舌往下垂。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP07/`，選用 D cand-2（91） |
| 尺寸（寬 × 深 × 高） | 0.636 × 0.03 × 0.516 m（抬高到最低點在 z = 0；宿主貼合點見 model_info） |
| 三角面 LOD0 / LOD1 / LOD2 | 2,792 / 1,396 / 418（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP07_04_MossSheetStoneSide`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP07_04_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP07_04_v001.glb`（LOD0）、`art/source/d2-moss-c/DP07_04_v001.blend` |

### DP07_05 苔被片・小苔斑（MossSheetSmall，v001）

微彎石面上的一小片不規則薄苔。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP07/`，選用 E cand-1（90） |
| 尺寸（寬 × 深 × 高） | 0.376 × 0.229 × 0.048 m（抬高到最低點在 z = 0；宿主貼合點見 model_info） |
| 三角面 LOD0 / LOD1 / LOD2 | 1,848 / 924 / 277（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP07_05_MossSheetSmall`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP07_05_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP07_05_v001.glb`（LOD0）、`art/source/d2-moss-c/DP07_05_v001.blend` |

### DP07_06 苔被片・包角苔（MossSheetBlockEdge，v001）

從方石頂面包過邊角往正面垂的一片薄苔。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP07/`，選用 F cand-2（91） |
| 尺寸（寬 × 深 × 高） | 0.494 × 0.256 × 0.304 m（抬高到最低點在 z = 0；宿主貼合點見 model_info） |
| 三角面 LOD0 / LOD1 / LOD2 | 2,810 / 1,405 / 421（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP07_06_MossSheetBlockEdge`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP07_06_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP07_06_v001.glb`（LOD0）、`art/source/d2-moss-c/DP07_06_v001.blend` |

### DP08_01 小蕨・鐵線蕨型（FernMaidenhair，v001）

十條細黑柄往外拱，分出側柄，每根側柄一扇小圓扇形小葉。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP08/`，選用 A cand-3（90） |
| 尺寸（寬 × 深 × 高） | 0.396 × 0.367 × 0.247 m（高度含地下的土裙） |
| 三角面 LOD0 / LOD1 / LOD2 | 2,676 / 1,338 / 401（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP08_01_FernMaidenhair`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP08_01_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP08_01_v001.glb`（LOD0）、`art/source/d2-moss-c/DP08_01_v001.blend` |

### DP08_02 小蕨・細裂蕨（FernLacy，v001）

六片往外拱的葉，左右錯開的齒緣羽片，中間一個捲曲的幼葉。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP08/`，選用 B cand-1（91） |
| 尺寸（寬 × 深 × 高） | 0.391 × 0.406 × 0.194 m（高度含地下的土裙） |
| 三角面 LOD0 / LOD1 / LOD2 | 3,724 / 1,862 / 558（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP08_02_FernLacy`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP08_02_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP08_02_v001.glb`（LOD0）、`art/source/d2-moss-c/DP08_02_v001.blend` |

### DP08_03 小蕨・梯子蕨（FernLadder，v001）

十片直立窄葉成瓶狀一叢，兩排短圓小葉像梯子。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP08/`，選用 C cand-1（90） |
| 尺寸（寬 × 深 × 高） | 0.202 × 0.189 × 0.408 m（高度含地下的土裙） |
| 三角面 LOD0 / LOD1 / LOD2 | 3,788 / 1,893 / 568（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP08_03_FernLadder`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP08_03_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP08_03_v001.glb`（LOD0）、`art/source/d2-moss-c/DP08_03_v001.blend` |

### DP09_01 林下地被・酢漿草（GroundWoodSorrel，v001）

二十八根細紅褐柄，每根三片微摺的心形小葉，成一團低矮的葉堆。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP09/`，選用 A cand-1（90） |
| 尺寸（寬 × 深 × 高） | 0.259 × 0.245 × 0.085 m（高度含地下的土裙） |
| 三角面 LOD0 / LOD1 / LOD2 | 1,452 / 726 / 217（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP09_01_GroundWoodSorrel`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP09_01_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP09_01_v001.glb`（LOD0）、`art/source/d2-moss-c/DP09_01_v001.blend` |

### DP09_02 林下地被・幼苗（GroundSeedlings，v001）

五株紅褐細莖的幼苗，兩到四片橢圓葉。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP09/`，選用 B cand-1（91） |
| 尺寸（寬 × 深 × 高） | 0.282 × 0.148 × 0.191 m（高度含地下的土裙） |
| 三角面 LOD0 / LOD1 / LOD2 | 488 / 244 / 73（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP09_02_GroundSeedlings`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP09_02_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP09_02_v001.glb`（LOD0）、`art/source/d2-moss-c/DP09_02_v001.blend` |

### DP09_03 林下地被・圓葉（GroundRoundLeaves，v001）

一片匍匐的銅錢形圓葉，貼地。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP09/`，選用 C cand-1（90） |
| 尺寸（寬 × 深 × 高） | 0.344 × 0.241 × 0.061 m（高度含地下的土裙） |
| 三角面 LOD0 / LOD1 / LOD2 | 1,876 / 938 / 280（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP09_03_GroundRoundLeaves`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP09_03_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP09_03_v001.glb`（LOD0）、`art/source/d2-moss-c/DP09_03_v001.blend` |

### DP09_04 林下地被・混合（GroundMixed，v001）

心形葉、兩株小蕨和幾片圓葉混在一起的低矮地被。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP09/`，選用 D cand-2（90） |
| 尺寸（寬 × 深 × 高） | 0.338 × 0.288 × 0.117 m（高度含地下的土裙） |
| 三角面 LOD0 / LOD1 / LOD2 | 1,964 / 982 / 294（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP09_04_GroundMixed`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP09_04_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP09_04_v001.glb`（LOD0）、`art/source/d2-moss-c/DP09_04_v001.blend` |

### DP10_01 垂藤・單條（VineSingle，v001）

一條 0.6 m 細藤，成對的橢圓小葉，幾條捲鬚。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP10/`，選用 A cand-1（90） |
| 尺寸（寬 × 深 × 高） | 0.103 × 0.074 × 0.6 m（抬高到最低點在 z = 0；宿主貼合點見 model_info） |
| 三角面 LOD0 / LOD1 / LOD2 | 854 / 426 / 128（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP10_01_VineSingle`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP10_01_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP10_01_v001.glb`（LOD0）、`art/source/d2-moss-c/DP10_01_v001.blend` |

### DP10_02 垂藤・兩條（VineTwinTwist，v001）

兩條約 1.5 m 的細藤，心形和橢圓小葉。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP10/`，選用 B cand-1（91） |
| 尺寸（寬 × 深 × 高） | 0.172 × 0.102 × 1.506 m（抬高到最低點在 z = 0；宿主貼合點見 model_info） |
| 三角面 LOD0 / LOD1 / LOD2 | 1,602 / 801 / 240（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP10_02_VineTwinTwist`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP10_02_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP10_02_v001.glb`（LOD0）、`art/source/d2-moss-c/DP10_02_v001.blend` |

### DP10_03 垂藤・長藤（VineLongCoil，v001）

一條 3 m 長藤，下端在地上捲一圈。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP10/`，選用 C cand-1（90） |
| 尺寸（寬 × 深 × 高） | 0.27 × 0.24 × 3.014 m（抬高到最低點在 z = 0；宿主貼合點見 model_info） |
| 三角面 LOD0 / LOD1 / LOD2 | 2,404 / 1,202 / 360（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP10_03_VineLongCoil`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP10_03_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP10_03_v001.glb`（LOD0）、`art/source/d2-moss-c/DP10_03_v001.blend` |

### DP10_04 垂藤・藤簾（VineCurtain，v001）

一條沿邊緣橫走的藤垂下五條 0.65–1.2 m 細藤。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP10/`，選用 D cand-1（91） |
| 尺寸（寬 × 深 × 高） | 0.638 × 0.077 × 1.207 m（抬高到最低點在 z = 0；宿主貼合點見 model_info） |
| 三角面 LOD0 / LOD1 / LOD2 | 2,420 / 1,210 / 363（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP10_04_VineCurtain`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP10_04_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP10_04_v001.glb`（LOD0）、`art/source/d2-moss-c/DP10_04_v001.blend` |

### DP11_01 莎草・小叢（SedgeTuft，v001）

八十片窄長深綠葉往外拱，幾片葉尖枯黃。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP11/`，選用 A cand-1（90） |
| 尺寸（寬 × 深 × 高） | 0.369 × 0.319 × 0.223 m（高度含地下的土裙） |
| 三角面 LOD0 / LOD1 / LOD2 | 2,028 / 1,014 / 304（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP11_01_SedgeTuft`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP11_01_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP11_01_v001.glb`（LOD0）、`art/source/d2-moss-c/DP11_01_v001.blend` |

### DP11_02 莎草・大叢（SedgeFountain，v001）

九十二片長葉像噴泉往外垂到地，基部有枯葉。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP11/`，選用 B cand-1（90） |
| 尺寸（寬 × 深 × 高） | 0.637 × 0.706 × 0.269 m（高度含地下的土裙） |
| 三角面 LOD0 / LOD1 / LOD2 | 2,316 / 1,157 / 347（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP11_02_SedgeFountain`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP11_02_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP11_02_v001.glb`（LOD0）、`art/source/d2-moss-c/DP11_02_v001.blend` |

### DP11_03 莎草・穗（SedgeSeedSpikes，v001）

直立細葉叢，五根細莖頂著褐色小穗。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP11/`，選用 C cand-2（91） |
| 尺寸（寬 × 深 × 高） | 0.293 × 0.285 × 0.477 m（高度含地下的土裙） |
| 三角面 LOD0 / LOD1 / LOD2 | 2,096 / 1,047 / 314（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP11_03_SedgeSeedSpikes`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP11_03_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP11_03_v001.glb`（LOD0）、`art/source/d2-moss-c/DP11_03_v001.blend` |

### DP12_01 枯小灌叢・小（DeadShrubSmall，v001）

約 0.3 m 的細乾枝叢，掛幾片捲曲枯葉。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP12/`，選用 A cand-1（90） |
| 尺寸（寬 × 深 × 高） | 0.276 × 0.332 × 0.28 m（高度含地下的土裙） |
| 三角面 LOD0 / LOD1 / LOD2 | 3,984 / 1,992 / 672（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP12_01_DeadShrubSmall`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP12_01_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP12_01_v001.glb`（LOD0）、`art/source/d2-moss-c/DP12_01_v001.blend` |

### DP12_02 枯小灌叢・中（DeadShrubMedium，v001）

約 0.5 m 的細乾枝叢、斷枝頭、十來片紅褐枯葉。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP12/`，選用 B cand-1（91） |
| 尺寸（寬 × 深 × 高） | 0.47 × 0.464 × 0.486 m（高度含地下的土裙） |
| 三角面 LOD0 / LOD1 / LOD2 | 3,306 / 1,734 / 536（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP12_02_DeadShrubMedium`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP12_02_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP12_02_v001.glb`（LOD0）、`art/source/d2-moss-c/DP12_02_v001.blend` |

### DP12_03 枯小灌叢・大（DeadShrubLarge，v001）

約 0.7 m 的乾枝叢，微微往一邊斜，幾簇枯葉。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP12/`，選用 C cand-1（90） |
| 尺寸（寬 × 深 × 高） | 0.663 × 0.732 × 0.658 m（高度含地下的土裙） |
| 三角面 LOD0 / LOD1 / LOD2 | 2,334 / 1,172 / 456（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP12_03_DeadShrubLarge`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP12_03_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP12_03_v001.glb`（LOD0）、`art/source/d2-moss-c/DP12_03_v001.blend` |

### DP13_01 地衣片・殼狀（LichenCrust，v001）

一片 0.25 m 的灰綠殼狀地衣，2–4 mm 厚，貼在石面上。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP13/`，選用 A cand-1（90） |
| 尺寸（寬 × 深 × 高） | 0.267 × 0.25 × 0.018 m（抬高到最低點在 z = 0；宿主貼合點見 model_info） |
| 三角面 LOD0 / LOD1 / LOD2 | 1,650 / 824 / 247（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP13_01_LichenCrust`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP13_01_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP13_01_v001.glb`（LOD0）、`art/source/d2-moss-c/DP13_01_v001.blend` |

### DP13_02 地衣片・葉狀（LichenFoliose，v001）

五朵灰綠葉狀地衣，瓣邊微捲。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP13/`，選用 B cand-3（90） |
| 尺寸（寬 × 深 × 高） | 0.204 × 0.184 × 0.018 m（抬高到最低點在 z = 0；宿主貼合點見 model_info） |
| 三角面 LOD0 / LOD1 / LOD2 | 3,178 / 1,589 / 476（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP13_02_LichenFoliose`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP13_02_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP13_02_v001.glb`（LOD0）、`art/source/d2-moss-c/DP13_02_v001.blend` |

### DP13_03 地衣片・杯狀（LichenCups，v001）

淺鼠尾草綠鱗片墊上長著二十幾個 1–2 cm 的小喇叭杯。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP13/`，選用 C cand-2（91） |
| 尺寸（寬 × 深 × 高） | 0.177 × 0.156 × 0.028 m（抬高到最低點在 z = 0；宿主貼合點見 model_info） |
| 三角面 LOD0 / LOD1 / LOD2 | 2,884 / 1,442 / 432（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP13_03_LichenCups`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP13_03_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP13_03_v001.glb`（LOD0）、`art/source/d2-moss-c/DP13_03_v001.blend` |

### DP13_04 地衣片・樹皮地衣條（LichenBarkStrip，v001）

沿樹幹（半徑約 0.3 m）往上的一條地衣，殼狀帶小葉瓣。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP13/`，選用 D cand-1（90） |
| 尺寸（寬 × 深 × 高） | 0.12 × 0.014 × 0.463 m（抬高到最低點在 z = 0；宿主貼合點見 model_info） |
| 三角面 LOD0 / LOD1 / LOD2 | 1,670 / 835 / 250（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP13_04_LichenBarkStrip`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP13_04_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP13_04_v001.glb`（LOD0）、`art/source/d2-moss-c/DP13_04_v001.blend` |

## v002 技術驗證

- 所有變體的 LOD0 在 4,000 三角面內，維持單材質和 1024 貼圖。逐 LOD 統計見 model_info。
- 嚴格／寬鬆 QA 每件均 0／0，接觸檢查最大間隙 0 mm。報告在 `art/previews/d2-moss-c/qa/`。
- Unity 6000.3.28f1 獨立匯入驗證 96 項 PASS、0 項 FAIL，報告在 `art/previews/d2-moss-c/unity/report.txt`。

## v001 視覺檢查紀錄（DP06）

灰模兩輪、上貼圖六輪，每輪看同樣的角度，先修最嚴重的：
1. 灰模第一輪：01、05 側面幾乎垂直像鼓 → 改成圓頂、底邊外擴；小苔球疊加成尖刺 → 取最高值不相加；02 的大瓣看不出來 → 加大瓣、降低瓣間的底。
2. 灰模第二輪：02 的瓣變成尖峰 → 瓣改成圓頂、半徑加大。
3. 上貼圖第一輪（和 D2 並排）：太暗太褐，像土堆 → 調成橄欖綠；表面一片平滑斑紋 → 苔撮做成一團團、團間是暗縫；邊緣苔鬚是深褐尖刺 → 改苔色、加多、變短。
4. 第二、三輪：黃綠跟著低頻雜訊走成大塊迷彩 → 只依朝天的面上色、保留貼圖的苔撮紋；苔鬚還是像一圈刺，而且貼在苔面上造成共面 → 拿掉苔鬚，改成外形邊緣的細鋸齒。
5. 第四、五輪：陡坡上的頂視 UV 拉成直條紋 → 陡坡改用繞著苔團的投影；頂上出現從中心放射的皺褶（極座標網格在中心擠成扇形） → 頂面改成平均分布的點做 Delaunay 三角化。
6. 第六輪（和 D2 並排）：整體比 D2 暗一截 → 苔的顏色和苔尖的黃綠調亮。

**v001 自評：和 D2 設定圖並排約 60% 像，還沒到 85–90%。** 顏色（橄欖綠帶黃綠苔尖）、圓墊和多瓣的形狀、貼地不浮空對得上；差的是：
- D2 的苔是一根根細絲立起來的苔撮，輪廓毛茸茸的；成品的苔撮只在貼圖和法線上，近看是一粒粒的斑點，輪廓偏圓滑。要更像需要真的細絲幾何或透明卡片，但工作包要求不用卡片，面數也有 4,000 的上限，這一點要審查時決定。
- 單件放在空地上看比較「乾淨」，設定圖裡的苔是長在石頭、根和落葉中間的。
- 三視圖本身比 D2 亮、偏黃；顏色照 D2，所以成品和三視圖的顏色不同。

## v001 已知問題與未驗

- 工作包寫「擺幾處 48」，這裡只交六種模型，擺放由核心組做。
- DP06_04 沒有根本體，擺的時候貼著任一段根的根腳放；DP06_05 要扣在一顆石頭上，石頭頂的弧度和苔帽底不一定完全貼合。
- 正式場景擺放、手機上的效果都未驗；不寫幀率。

## v002 視覺對照與驗收

- `art/previews/d2-moss-c/<ID>/d2/<ID>-d2-compare.jpg` 並排設定圖裁切、v001、v002。兩版模型在同一個 Blender 相機、照明和地景比較；根、土、石和葉是本機審圖用的陪襯。
- 多瓣中丘加深瓣與瓣之間的凹谷。從連續苔面抬出小撮鈍頭幾何，減掉底層不需要的面數；修飾舊版粗塊狀的凹凸與苔尖色。早期的尖端在並排圖上呈現刺狀，已改成較低的鈍頭。
- 正式 D2 場景的對圖鏡位、構圖、場景材質與光照仍待核對，90% 美術驗收尚未確認。
- 本輪觀察：鈍頭苔撮讓局部輪廓更碎，V6 的細密直立纖維和層疊邊緣仍有差距，近景仍偏厚塊。

## DP07–DP13 v001（B 批其餘七種）

**共同做法（和 DP06 不同的地方）**
- DP07 苔被片、DP13 地衣片是貼在宿主表面的薄殼：石頂（半徑約 0.55 m 的圓石）、平石、根頂（半徑 0.12 m）、石側直面、方石邊角、樹幹（半徑 0.3 m）。宿主不在模型裡，薄片沿著宿主表面長，邊緣落在宿主上，一圈裙邊往宿主裡收 4–6 mm，所以擺在差不多形狀的石頭或根上不會浮空。為了審圖和 Unity 檢查，掛在宿主上的件整件抬高到最低點在 z = 0；宿主上的貼合點座標寫在 model_info 的 origin。
- DP08–DP11 每一片葉、小葉、草葉都是真的幾何，沒有卡片；每片葉子各自轉一點角度，避免相鄰的葉片平行重疊。底下一小片土盤往地下 1 cm。
- DP10 垂藤掛在根或石頭的邊緣上（邊緣不在模型裡），同樣抬高到最低點在 z = 0、掛點記在 origin；DP10_04 五條藤從一條沿邊緣橫走的藤垂下，五條連成一件。
- DP10、DP12 的最細枝梢和捲鬚放在 `Fine` 這組，LOD2 拿掉（遠看看不到）。不這樣做時，上千根細枝減不了面，LOD2 停在 24–56%。

**驗證**
- QA 嚴格：27 種都是 0。接觸檢查最大 9.1 mm（DP12_02 的枯葉掛在枝梢下，本來就懸空）；其他在 4 mm 內。
- QA 寬鬆：DP07、DP09_01–03、DP10_02、DP10_04、DP13 是 0。其餘有少量「兩片葉、兩根草葉或兩根細枝在 1 mm 內幾乎平行地交錯」：DP08_01 4、DP08_02 35、DP08_03 5、DP09_04 1、DP10_01 1、DP10_03 5、DP11_01 15、DP11_02 2、DP11_03 18、DP12_01 25、DP12_02 19、DP12_03 3（對）。這是密集葉叢裡分開的葉片交錯，不是同一片面重疊；再減就得把葉子拉開、葉叢變稀，這裡保留，留給審查決定。
- Unity 6000.3.28f1：DP06–DP13 一起跑，528 項 PASS、0 項 FAIL。第一次跑 DP11_02 有幾片下垂的草葉穿到地下 4.5 cm，已把草葉限制在地面以上後重跑。
- 面數：每件 LOD0 ≤ 4,000，LOD1 約 50%、LOD2 約 15%（model_info 有逐件數字）。

**視覺檢查紀錄**
1. DP07 灰模：掛在宿主下方的部分被審圖台的地面吃掉 → 整件抬高；邊緣的鋸齒像三角形 → 改成細碎的鬚邊；石側和邊角的垂苔是三四條粗腳 → 改成很多條長短不一的細舌，再改鈍（尖的看起來像刺）。
2. DP13 上貼圖：殼狀地衣太白 → 改成 D2 V6 那種暗灰綠；DP13_02 面數 4,960 → 每朵的邊緣點數減少。
3. DP08、DP09、DP11 灰模：每一種都比三視圖稀很多 → 葉片、小葉、草葉加密；DP08_03 超過 4,000 面 → 葉片段數減少；DP09_03 的 LOD2 是 23% → 葉片多切幾段、柄改一段。上貼圖後寬鬆 QA 抓到大量葉片平行重疊、DP08_01 有小葉沒接到柄（21.5 mm）→ 每片葉子隨機轉角、小葉從柄上長出、扇形小葉平均分開、細裂蕨的羽片左右錯開半格。
4. DP10 灰模：葉子是水平的，正面看只看到葉緣 → 葉面朝外、往兩側伸；長藤太直 → 加大擺動。DP12：枝太粗、細枝太少 → 枝變細、多分一層。

**自評（和 D2 設定圖並排）**
- DP07 苔被片約 55%：顏色和薄薄貼著的樣子對得上；單獨擺在地上審圖時看不出貼的是什麼，要整合到石頭和根上才看得出來。
- DP08 小蕨約 45–50%：DP08_02 細裂蕨的羽片太寬太暗，像掌狀葉，V6 的蕨是細密的羽葉；DP08_01、DP08_03 比較接近三視圖。
- DP09 林下地被約 55%：形狀和高度對；V6 的葉子更亮、有葉脈光澤。
- DP10 垂藤約 60%：細莖、成對小葉、長短不一對得上。
- DP11 莎草約 60%：暗綠細長、往外拱；草葉比 V5 的少一點。
- DP12 枯小灌叢約 60%：細枝和少量枯葉對得上；最細的枝梢比三視圖少。
- DP13 地衣片約 45%：殼狀地衣和樹皮地衣條還可以；葉狀地衣（DP13_02）太亮、太像一塊塊色片，V6 的地衣是細碎的灰綠斑。

**已知問題與未驗**
- 工作包的「擺幾處」由核心組擺；DP07、DP10、DP13 要貼到差不多形狀的宿主上，宿主的半徑寫在 model_info。
- 正式場景擺放、手機上的效果都未驗；不寫幀率。
