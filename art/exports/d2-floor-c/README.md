| 項目 | 內容 |
|---|---|
| 誰做的 | C（Eli-0731） |
| 工作包 | docs/execution/2026-11-15/C-300h-D2-small-life.md，C 批；標準照 docs/execution/2026-11-15/00-300h-共同標準.md |
| ID | DP14 細枯枝（八種）、DP15 中斷枝（六種）、DP16 樹皮片（六種）、DP17 小石與碎石（八種）、DP18 松果與落果（三種）、DP19 落葉堆（三種）、DP20 細根網（六種）、DP21 小朽樹樁（四種）、DP22 水窪落葉與枝（一組），共 45 件，都是 v001 |
| 分支／PR | art/c-1115-d2-floor-smalls ／ 開 PR 後補 |
| 版本 | v001 |
| 狀態 | Exported ／ Imported（Unity 6000.3.28f1 獨立匯入檢查）／ Visually Verified（Blender 審圖、和 D2 設定圖並排）／ In-game Verified：未驗（沒放進正式場景） |
| 素材來源 | 樹皮：Poly Haven `bark_brown_02`（CC0，2k），共同標準第五節指定，和 d2-roots-b／d2-logs-b 同一套；掃描圖不進版本庫，放在環境變數 `DR_TEX` 指的資料夾（預設 `D:/yun-jing-cache/polyhaven-bark/`），建模時取它的明暗與高度，重新上成 D2 的灰褐色。其餘原創，貼圖在建模腳本裡畫；三視圖參考在 `art/references/DP14/`–`DP22/` |
| 實際工時 | 2026-11-23（台灣時間），約 7 小時：三視圖 192 張與自評（DP20 三種重畫一次）、套件建立、45 件建模、灰模每組兩到三輪、上貼圖、QA、審圖、Unity 檢查 |

# D2 地上的小東西（d2-floor-c）

11/15 的 300 小時包 C 批：D2 古樹神木地上的小石、細枝、樹皮片、松果、落葉、細根、小樹樁（設定圖 V2–V6）。靜態擺設；擺進世界由核心組做，這裡不改主場景、不改區塊 JSON。使用者 2026-11-22 決定不等樣品審查，整批先做完。

**共同做法**
- 先生成三視圖（每種 4 張）、自評選一張（分數和取捨在 `art/references/<ID>/prompt.txt`），再做灰模（`art/previews/d2-floor-c/<ID>/clay/`），最後上貼圖。
- 原點：底部中心，z = 0 在地面；埋進土裡的部分往下延伸（小石埋 25–40%，枝條埋半徑的 40%、至少 3.5 mm，樹皮片最低邊 4 mm，樹樁腳 6 cm），擺在不平的地上不會浮空（共同標準第四節）。DP22 的 z = 0 是水窪水面。Blender −Y 是正面（FBX／Unity 是 −Z）。
- 一件一個材質、一套 1024 貼圖（Albedo／Normal／ORM／MaskURP），雙面。沒有 `Detail_*`。`minTier` 都是 `standard`。LOD1 約 50%、LOD2 約 15%。
- 石材：核心組的 SS01 半埋踏石還沒在 main 上，石頭照 D2 設定圖 V6 的中灰自己畫；DS07 擺好之後可以再對一次顏色。
- 建模流程和 `art/source/d2-mushrooms-c/build_dp.py`（DP01–DP05，在 art/c-1115-d2-mushrooms 分支，還沒進 main）相同，複製成 `build_floor.py`，共用零件在 `floor_base.py`；工具（`creekside-life-c/wl_kit.py`）用 main 上的。亂數種子固定，重建結果一樣。
- 重建：`blender -b --factory-startup -P art/source/d2-floor-c/build_floor.py -- DP17_01 [...] [--clay]`；審圖：`BL=<blender> sh art/source/d2-floor-c/render_reviews.sh`；總表與 D2 並排：`D2=<放 D2 V1–V6.png 的資料夾> sh art/source/d2-floor-c/make_sheets.sh`；Unity：`UNITY=<Unity.exe 6000.3.28f1> sh art/source/d2-floor-c/unity/run_unity_check.sh`。

### DP14_01 細枯枝・短枝（TwigShort，v001）

0.2 m、1 cm 粗的短枝，一根小側枝，粗端纖維斷口。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP14/`，選用 A cand-1（90） |
| 尺寸（寬 × 深 × 高） | 0.222 × 0.041 × 0.01 m（高度含埋進土裡的部分） |
| 三角面 LOD0 / LOD1 / LOD2 | 228 / 114 / 34（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP14_01_TwigShort`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP14_01_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP14_01_v001.glb`（LOD0）、`art/source/d2-floor-c/DP14_01_v001.blend` |

### DP14_02 細枯枝・分叉（TwigForked，v001）

0.35 m 的細枝，靠一端分一個叉，兩端都是碎裂斷口。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP14/`，選用 B cand-2（90） |
| 尺寸（寬 × 深 × 高） | 0.391 × 0.038 × 0.014 m（高度含埋進土裡的部分） |
| 三角面 LOD0 / LOD1 / LOD2 | 312 / 156 / 46（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP14_02_TwigForked`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP14_02_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP14_02_v001.glb`（LOD0）、`art/source/d2-floor-c/DP14_02_v001.blend` |

### DP14_03 細枯枝・微彎（TwigCurved，v001）

0.5 m、微彎，兩根短側枝。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP14/`，選用 C cand-2（90） |
| 尺寸（寬 × 深 × 高） | 0.526 × 0.106 × 0.019 m（高度含埋進土裡的部分） |
| 三角面 LOD0 / LOD1 / LOD2 | 392 / 196 / 58（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP14_03_TwigCurved`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP14_03_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP14_03_v001.glb`（LOD0）、`art/source/d2-floor-c/DP14_03_v001.blend` |

### DP14_04 細枯枝・S 形苔枝（TwigSMossy，v001）

0.7 m 的 S 形枝，朝上那面一塊苔，兩端碎裂。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP14/`，選用 D cand-4（91） |
| 尺寸（寬 × 深 × 高） | 0.743 × 0.127 × 0.027 m（高度含埋進土裡的部分） |
| 三角面 LOD0 / LOD1 / LOD2 | 434 / 216 / 65（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP14_04_TwigSMossy`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP14_04_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP14_04_v001.glb`（LOD0）、`art/source/d2-floor-c/DP14_04_v001.blend` |

### DP14_05 細枯枝・剝皮（TwigPeeled，v001）

0.9 m，三根側枝，幾處剝皮露出淺色木頭。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP14/`，選用 E cand-1（90） |
| 尺寸（寬 × 深 × 高） | 0.974 × 0.133 × 0.026 m（高度含埋進土裡的部分） |
| 三角面 LOD0 / LOD1 / LOD2 | 662 / 330 / 98（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP14_05_TwigPeeled`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP14_05_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP14_05_v001.glb`（LOD0）、`art/source/d2-floor-c/DP14_05_v001.blend` |

### DP14_06 細枯枝・兩折歪枝（TwigCrooked，v001）

1.1 m，兩處彎折，有兩個舊枝節。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP14/`，選用 F cand-2（90） |
| 尺寸（寬 × 深 × 高） | 1.124 × 0.222 × 0.03 m（高度含埋進土裡的部分） |
| 三角面 LOD0 / LOD1 / LOD2 | 432 / 216 / 64（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP14_06_TwigCrooked`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP14_06_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP14_06_v001.glb`（LOD0）、`art/source/d2-floor-c/DP14_06_v001.blend` |

### DP14_07 細枯枝・直枝（TwigStraightFork，v001）

1.3 m 的直枝，細端分叉，粗端纖維斷口，一點苔。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP14/`，選用 G cand-2（90） |
| 尺寸（寬 × 深 × 高） | 1.38 × 0.085 × 0.034 m（高度含埋進土裡的部分） |
| 三角面 LOD0 / LOD1 / LOD2 | 865 / 431 / 128（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP14_07_TwigStraightFork`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP14_07_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP14_07_v001.glb`（LOD0）、`art/source/d2-floor-c/DP14_07_v001.blend` |

### DP14_08 細枯枝・長枝（TwigLong，v001）

1.5 m，沿途六根小側枝，兩端碎裂。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP14/`，選用 H cand-3（91） |
| 尺寸（寬 × 深 × 高） | 1.574 × 0.128 × 0.039 m（高度含埋進土裡的部分） |
| 三角面 LOD0 / LOD1 / LOD2 | 882 / 440 / 132（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP14_08_TwigLong`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP14_08_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP14_08_v001.glb`（LOD0）、`art/source/d2-floor-c/DP14_08_v001.blend` |

### DP15_01 中斷枝・一叉（BranchForkA，v001）

1.6 m、7 cm 粗，一根翹起的叉枝，斷口長木刺，細端幾根小枝。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP15/`，選用 A cand-1（90） |
| 尺寸（寬 × 深 × 高） | 1.9 × 0.431 × 0.271 m（高度含埋進土裡的部分） |
| 三角面 LOD0 / LOD1 / LOD2 | 928 / 464 / 138（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP15_01_BranchForkA`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP15_01_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP15_01_v001.glb`（LOD0）、`art/source/d2-floor-c/DP15_01_v001.blend` |

### DP15_02 中斷枝・彎曲雙叉（BranchCurvedTwoFork，v001）

2 m，彎曲、兩個叉（一個翹起），碎斷口，苔斑。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP15/`，選用 B cand-3（91） |
| 尺寸（寬 × 深 × 高） | 2.267 × 0.814 × 0.241 m（高度含埋進土裡的部分） |
| 三角面 LOD0 / LOD1 / LOD2 | 1,470 / 734 / 220（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP15_02_BranchCurvedTwoFork`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP15_02_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP15_02_v001.glb`（LOD0）、`art/source/d2-floor-c/DP15_02_v001.blend` |

### DP15_03 中斷枝・長側枝（BranchLongSide，v001）

2.2 m 的直枝，一根 1 m 的長側枝。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP15/`，選用 C cand-1（91） |
| 尺寸（寬 × 深 × 高） | 2.5 × 0.573 × 0.189 m（高度含埋進土裡的部分） |
| 三角面 LOD0 / LOD1 / LOD2 | 1,076 / 538 / 160（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP15_03_BranchLongSide`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP15_03_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP15_03_v001.glb`（LOD0）、`art/source/d2-floor-c/DP15_03_v001.blend` |

### DP15_04 中斷枝・Y 形（BranchYFork，v001）

2.5 m，中間 Y 形分岔，兩個細端都是小枝。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP15/`，選用 D cand-1（91） |
| 尺寸（寬 × 深 × 高） | 2.8 × 0.93 × 0.291 m（高度含埋進土裡的部分） |
| 三角面 LOD0 / LOD1 / LOD2 | 1,332 / 666 / 198（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP15_04_BranchYFork`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP15_04_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP15_04_v001.glb`（LOD0）、`art/source/d2-floor-c/DP15_04_v001.blend` |

### DP15_05 中斷枝・剝皮（BranchPeeled，v001）

2.8 m、微彎，幾處剝皮露淺色木頭，翹起的小枝。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP15/`，選用 E cand-1（90） |
| 尺寸（寬 × 深 × 高） | 3.1 × 0.473 × 0.201 m（高度含埋進土裡的部分） |
| 三角面 LOD0 / LOD1 / LOD2 | 1,182 / 590 / 176（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP15_05_BranchPeeled`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP15_05_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP15_05_v001.glb`（LOD0）、`art/source/d2-floor-c/DP15_05_v001.blend` |

### DP15_06 中斷枝・苔（BranchMossy，v001）

3 m、11 cm 粗，兩根側枝，朝上那面長苔，斷口長木刺。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP15/`，選用 F cand-1（91） |
| 尺寸（寬 × 深 × 高） | 3.3 × 0.584 × 0.26 m（高度含埋進土裡的部分） |
| 三角面 LOD0 / LOD1 / LOD2 | 1,928 / 964 / 289（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP15_06_BranchMossy`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP15_06_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP15_06_v001.glb`（LOD0）、`art/source/d2-floor-c/DP15_06_v001.blend` |

### DP16_01 樹皮片・半管（BarkHalfTube，v001）

0.15 m 捲成半管的樹皮，外面灰褐粗糙、裡面淺黃褐。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP16/`，選用 A cand-1（90） |
| 尺寸（寬 × 深 × 高） | 0.14 × 0.082 × 0.035 m（高度含埋進土裡的部分） |
| 三角面 LOD0 / LOD1 / LOD2 | 304 / 152 / 44（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP16_01_BarkHalfTube`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP16_01_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP16_01_v001.glb`（LOD0）、`art/source/d2-floor-c/DP16_01_v001.blend` |

### DP16_02 樹皮片・厚平（BarkFlatThick，v001）

0.25 m 的厚樹皮，微凹，外面有裂溝。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP16/`，選用 B cand-1（90） |
| 尺寸（寬 × 深 × 高） | 0.238 × 0.14 × 0.027 m（高度含埋進土裡的部分） |
| 三角面 LOD0 / LOD1 / LOD2 | 524 / 262 / 78（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP16_02_BarkFlatThick`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP16_02_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP16_02_v001.glb`（LOD0）、`art/source/d2-floor-c/DP16_02_v001.blend` |

### DP16_03 樹皮片・扭轉條（BarkStripTwisted，v001）

0.35 m、5 cm 寬的樹皮條，扭轉、兩端翹起。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP16/`，選用 C cand-1（90） |
| 尺寸（寬 × 深 × 高） | 0.342 × 0.053 × 0.063 m（高度含埋進土裡的部分） |
| 三角面 LOD0 / LOD1 / LOD2 | 472 / 236 / 70（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP16_03_BarkStripTwisted`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP16_03_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP16_03_v001.glb`（LOD0）、`art/source/d2-floor-c/DP16_03_v001.blend` |

### DP16_04 樹皮片・碎屑（BarkFlakes，v001）

五片碎樹皮疊在一起，兩片翻面露出淺色內面。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP16/`，選用 D cand-1（90） |
| 尺寸（寬 × 深 × 高） | 0.191 × 0.15 × 0.019 m（高度含埋進土裡的部分） |
| 三角面 LOD0 / LOD1 / LOD2 | 960 / 480 / 144（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP16_04_BarkFlakes`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP16_04_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP16_04_v001.glb`（LOD0）、`art/source/d2-floor-c/DP16_04_v001.blend` |

### DP16_05 樹皮片・彎厚塊（BarkChunkCurved，v001）

0.3 m 強烈彎曲的厚樹皮塊，深裂溝，一點苔。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP16/`，選用 E cand-1（90） |
| 尺寸（寬 × 深 × 高） | 0.29 × 0.19 × 0.074 m（高度含埋進土裡的部分） |
| 三角面 LOD0 / LOD1 / LOD2 | 1,002 / 501 / 150（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP16_05_BarkChunkCurved`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP16_05_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP16_05_v001.glb`（LOD0）、`art/source/d2-floor-c/DP16_05_v001.blend` |

### DP16_06 樹皮片・捲邊大片（BarkSheetRolled，v001）

0.4 × 0.24 m 的大片樹皮，一邊捲起來。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP16/`，選用 F cand-1（90） |
| 尺寸（寬 × 深 × 高） | 0.384 × 0.222 × 0.059 m（高度含埋進土裡的部分） |
| 三角面 LOD0 / LOD1 / LOD2 | 1,016 / 508 / 152（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP16_06_BarkSheetRolled`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP16_06_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP16_06_v001.glb`（LOD0）、`art/source/d2-floor-c/DP16_06_v001.blend` |

### DP17_01 小石・圓小石（PebbleRound，v001）

一顆 6 cm 的圓小石，半埋。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP17/`，選用 A cand-4（90） |
| 尺寸（寬 × 深 × 高） | 0.055 × 0.052 × 0.04 m（高度含埋進土裡的部分） |
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
| 尺寸（寬 × 深 × 高） | 0.152 × 0.121 × 0.1 m（高度含埋進土裡的部分） |
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
| 尺寸（寬 × 深 × 高） | 0.15 × 0.108 × 0.06 m（高度含埋進土裡的部分） |
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
| 尺寸（寬 × 深 × 高） | 0.19 × 0.164 × 0.14 m（高度含埋進土裡的部分） |
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
| 尺寸（寬 × 深 × 高） | 0.178 × 0.1 × 0.247 m（高度含埋進土裡的部分） |
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
| 尺寸（寬 × 深 × 高） | 0.28 × 0.164 × 0.16 m（高度含埋進土裡的部分） |
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
| 尺寸（寬 × 深 × 高） | 0.298 × 0.257 × 0.24 m（高度含埋進土裡的部分） |
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
| 尺寸（寬 × 深 × 高） | 0.388 × 0.318 × 0.26 m（高度含埋進土裡的部分） |
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
| 尺寸（寬 × 深 × 高） | 0.181 × 0.099 × 0.054 m（高度含埋進土裡的部分） |
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
| 尺寸（寬 × 深 × 高） | 0.118 × 0.132 × 0.03 m（高度含埋進土裡的部分） |
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
| 尺寸（寬 × 深 × 高） | 0.175 × 0.16 × 0.029 m（高度含埋進土裡的部分） |
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
| 尺寸（寬 × 深 × 高） | 0.383 × 0.348 × 0.09 m（高度含埋進土裡的部分） |
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
| 尺寸（寬 × 深 × 高） | 0.605 × 0.569 × 0.126 m（高度含埋進土裡的部分） |
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
| 尺寸（寬 × 深 × 高） | 0.914 × 0.344 × 0.13 m（高度含埋進土裡的部分） |
| 三角面 LOD0 / LOD1 / LOD2 | 3,040 / 1,520 / 456（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP19_03_LeafDrift`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP19_03_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP19_03_v001.glb`（LOD0）、`art/source/d2-floor-c/DP19_03_v001.blend` |

### DP20_01 細根網・交錯（RootNetCrossing，v001）

約 1 m，六條 1–3 cm 的細根交錯，時進時出地半埋，三個根尖露出地面。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP20/`，選用 A cand-1（90） |
| 尺寸（寬 × 深 × 高） | 0.959 × 0.521 × 0.058 m（高度含埋進土裡的部分） |
| 三角面 LOD0 / LOD1 / LOD2 | 1,336 / 668 / 200（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP20_01_RootNetCrossing`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP20_01_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP20_01_v001.glb`（LOD0）、`art/source/d2-floor-c/DP20_01_v001.blend` |

### DP20_02 細根網・扇形（RootNetFan，v001）

從一條 5 cm 的根往外扇開的細根網。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP20/`，選用 B cand-7（90，重畫） |
| 尺寸（寬 × 深 × 高） | 1.175 × 1.049 × 0.079 m（高度含埋進土裡的部分） |
| 三角面 LOD0 / LOD1 / LOD2 | 3,406 / 1,702 / 509（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP20_02_RootNetFan`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP20_02_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP20_02_v001.glb`（LOD0）、`art/source/d2-floor-c/DP20_02_v001.blend` |

### DP20_03 細根網・根結（RootKnot，v001）

七條細根打結成一團，有的拱起跨過別的根，縫裡有苔墊。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP20/`，選用 C cand-1（90） |
| 尺寸（寬 × 深 × 高） | 1.279 × 1.388 × 0.12 m（高度含埋進土裡的部分） |
| 三角面 LOD0 / LOD1 / LOD2 | 2,064 / 1,032 / 308（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP20_03_RootKnot`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP20_03_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP20_03_v001.glb`（LOD0）、`art/source/d2-floor-c/DP20_03_v001.blend` |

### DP20_04 細根網・三股平行（RootsParallel，v001）

1.5 m，三條細根平躺、互相纏繞。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP20/`，選用 D cand-5（90，重畫） |
| 尺寸（寬 × 深 × 高） | 1.551 × 0.155 × 0.071 m（高度含埋進土裡的部分） |
| 三角面 LOD0 / LOD1 / LOD2 | 1,256 / 627 / 188（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP20_04_RootsParallel`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP20_04_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP20_04_v001.glb`（LOD0）、`art/source/d2-floor-c/DP20_04_v001.blend` |

### DP20_05 細根網・分岔（RootNetBranching，v001）

一條根一再分岔成更細的根。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP20/`，選用 E cand-8（90，重畫） |
| 尺寸（寬 × 深 × 高） | 1.162 × 1.146 × 0.087 m（高度含埋進土裡的部分） |
| 三角面 LOD0 / LOD1 / LOD2 | 1,572 / 785 / 234（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP20_05_RootNetBranching`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP20_05_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP20_05_v001.glb`（LOD0）、`art/source/d2-floor-c/DP20_05_v001.blend` |

### DP20_06 細根網・寬網卡石（RootNetWideStones，v001）

2 × 1 m，八條細根交錯，四顆小石卡在根間。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP20/`，選用 F cand-1（90） |
| 尺寸（寬 × 深 × 高） | 1.912 × 0.991 × 0.081 m（高度含埋進土裡的部分） |
| 三角面 LOD0 / LOD1 / LOD2 | 3,988 / 1,994 / 598（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP20_06_RootNetWideStones`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP20_06_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP20_06_v001.glb`（LOD0）、`art/source/d2-floor-c/DP20_06_v001.blend` |

### DP21_01 小朽樹樁・小（StumpSmall，v001）

0.3 m 高的小樹樁，空心、參差斷口、側面苔、四條根入土。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP21/`，選用 A cand-1（90） |
| 尺寸（寬 × 深 × 高） | 0.645 × 0.605 × 0.343 m（高度含埋進土裡的部分） |
| 三角面 LOD0 / LOD1 / LOD2 | 1,219 / 609 / 182（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP21_01_StumpSmall`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有；樹樁需要時在場景加一個圓柱 |
| 檔案 | `art/exports/d2-floor-c/DP21_01_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP21_01_v001.glb`（LOD0）、`art/source/d2-floor-c/DP21_01_v001.blend` |

### DP21_02 小朽樹樁・破邊（StumpBrokenSide，v001）

0.5 m，一邊破掉露出淺色朽空的內壁。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP21/`，選用 B cand-1（90） |
| 尺寸（寬 × 深 × 高） | 1.038 × 1.05 × 0.5 m（高度含埋進土裡的部分） |
| 三角面 LOD0 / LOD1 / LOD2 | 1,666 / 832 / 249（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP21_02_StumpBrokenSide`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有；樹樁需要時在場景加一個圓柱 |
| 檔案 | `art/exports/d2-floor-c/DP21_02_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP21_02_v001.glb`（LOD0）、`art/source/d2-floor-c/DP21_02_v001.blend` |

### DP21_03 小朽樹樁・高木刺（StumpSplinter，v001）

一側一根高高的碎木刺，到 0.72 m；空心，下半有苔。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP21/`，選用 C cand-1（90） |
| 尺寸（寬 × 深 × 高） | 1.266 × 1.208 × 0.653 m（高度含埋進土裡的部分） |
| 三角面 LOD0 / LOD1 / LOD2 | 1,787 / 893 / 268（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP21_03_StumpSplinter`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有；樹樁需要時在場景加一個圓柱 |
| 檔案 | `art/exports/d2-floor-c/DP21_03_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP21_03_v001.glb`（LOD0）、`art/source/d2-floor-c/DP21_03_v001.blend` |

### DP21_04 小朽樹樁・裂兩半（StumpSplit，v001）

1 m 高的寬樹樁，兩道深缺口裂成兩半，厚苔，六條根。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP21/`，選用 D cand-1（90） |
| 尺寸（寬 × 深 × 高） | 1.79 × 1.571 × 1.081 m（高度含埋進土裡的部分） |
| 三角面 LOD0 / LOD1 / LOD2 | 2,163 / 1,080 / 324（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP21_04_StumpSplit`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有；樹樁需要時在場景加一個圓柱 |
| 檔案 | `art/exports/d2-floor-c/DP21_04_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP21_04_v001.glb`（LOD0）、`art/source/d2-floor-c/DP21_04_v001.blend` |

### DP22_01 水窪落葉與枝（PuddleLeavesTwigs，v001）

十八片濕暗的落葉和三根細枝，放進 DS03 水窪；原點在水面，有的葉子半沉。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP22/`，選用 A cand-1（90） |
| 尺寸（寬 × 深 × 高） | 0.476 × 0.422 × 0.06 m（高度從水面下的葉子算起） |
| 三角面 LOD0 / LOD1 / LOD2 | 1,178 / 588 / 176（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP22_01_PuddleLeavesTwigs`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-floor-c/DP22_01_v001.fbx`（LOD0–2）、`art/exports/d2-floor-c/DP22_01_v001.glb`（LOD0）、`art/source/d2-floor-c/DP22_01_v001.blend` |

## 驗證

- QA 嚴格：45 件都是 0。
- DP14–DP16、DP20–DP22（31 件）寬鬆：多數是 0；DP14_04、DP16_05、DP20_02、DP21_01 各 1 項（側枝、苔或根和主體交接處有 1–6 對三角面幾乎平行）。接觸：枝條、樹皮片、細根在 1 mm 內；DP16_04 碎樹皮最大 3.5 mm，DP21 樹樁的苔與根最大 7.0 mm，DP22 浮在水面的葉子最大 5.0 mm。
- DP17–DP19 寬鬆：寬鬆：DP17、DP18_02、DP18_03 是 0；DP18_01 松果鱗片交錯 8 對，DP19 落葉堆 12–19 對（一片片分開的葉子疊在一起時，有些在 1 mm 內幾乎平行；再拉開葉堆就會變稀）。接觸：DP17、DP18 在 3 mm 內；DP19 落葉堆最大 10.4 mm（最上層幾片葉子架在別的葉子上，留一點縫）。
- Unity 6000.3.28f1 獨立匯入：720 項 PASS、0 項 FAIL（`art/previews/d2-floor-c/unity/report.txt`）。埋進土裡的檢查改成「往地下 0.3–12 cm」，因為小石埋得比苔墊深。
- 面數：每件 LOD0 ≤ 4,000（逐件在 model_info）。

## 視覺檢查紀錄

1. DP17 灰模：石頭像麵團 → 每顆加平面切面，切面用平面著色、稜邊清楚；楔形角石像方磚 → 往上收窄、略斜。上貼圖第一輪：面數只有 320–445（Blender 球體細分 3 只有 320 面，我算錯了）→ 改細分 4 重建；和 D2 並排偏藍、黑斑多 → 改成暖的中灰、細碎色塊；苔像地毯蓋滿頂 → 改成一塊塊，再把苔的邊緣順過（照三角面選會變成階梯）。
2. DP18 灰模：松果鱗片是一堆亂刺 → 鱗片朝尖端斜出、一排排疊起來。
3. DP19：葉片尖角太多 → 少用分裂葉；上層葉子浮空 15 mm → 每層葉子落在下一層上、底下的核心加高，落葉長條的核心移到最高的那一側。

4. DP14／DP15 灰模：枝條太光滑、粗細一致 → 加沿長度的粗細起伏和舊枝節；DP15 的側枝全躺平、側面看不出來 → 一根側枝和小枝翹起來，靠在主枝上。上貼圖後樹皮太暗（貼圖中位數 0.20，比石頭暗）→ 調亮到約 0.24。
5. DP16 灰模：撕裂端的參差比網格間距大，表面折回去和自己重疊（嚴格 QA 1 項）→ 參差限制在一格以內。
6. DP20 灰模：蓋在根上的土是一顆顆圓球 → 改成又寬又低的土堆；分岔根網只在末端分岔 → 從 15% 處就開始分、每次分兩到三條；根結是平的 → 根拱起來跨過別的根。
7. DP21 灰模：斷口的齒一高一低太規則 → 改成大段高低起伏再加單根木刺；破邊的缺口像一條縫 → 缺口加寬；根太短像尖刺 → 加長。樹樁原本因為根伸得遠被縮小（DP21_03 只剩 0.62 m）→ 放寬寬度限制，高度回到 0.65 m。

**自評（和 D2 設定圖並排）**
- DP17 小石約 60%：形狀和半埋的樣子對得上；V6 的石頭有更細的筆觸和亮邊，近看比成品細緻。
- DP18 松果落果約 65%：松果和堅果的形狀、顏色對得上；V6 裡這麼小的東西看不清，主要對三視圖。
- DP19 落葉堆約 60%：乾濕兩色、一片片的葉子對得上；葉形比較單純（橢圓為主）。
- DP14 細枯枝約 55%：長度、粗細、彎折和斷口照提示詞；三視圖的枝畫得比提示詞粗、樹皮塊更明顯，成品看起來細。
- DP15 中斷枝約 50%：分叉、翹起的側枝、長木刺斷口對得上；三視圖枝更粗、苔更多更亮。
- DP16 樹皮片約 55%：半管、捲邊、扭轉、翻面露淺色都有；三視圖的樹皮是一層層鱗片疊起來，成品只用貼圖和裂溝表現。
- DP20 細根網約 45%：時進時出地半埋、根尖露出、卡石頭對得上；三視圖的根網密得像一張墊子，成品稀很多（受 4,000 面限制，DP20_06 已到 3,988）。
- DP21 小朽樹樁約 45%：空心、參差斷口、破邊、高木刺、裂兩半、根入土都有；三視圖的朽木有很多孔洞和長條木纖維，成品內壁太平滑、顏色太亮；苔在成品上幾乎看不出來。
- DP22 水窪落葉約 50%：濕暗的葉子和細枝、有的半沉對得上；葉形比三視圖的楓葉單純。
- D2 對照圖：平躺的枝和根在 D2 的光下離鏡頭太遠、幾乎看不見，這組對照圖對 DP14、DP15、DP20 沒有參考價值，主要對三視圖。

**已知問題與未驗**
- 工作包的「擺幾處」由核心組擺。
- DP21 的苔幾乎沒長出來、內壁太亮，DP20 的密度不夠，是這批最弱的兩組，審查時優先看。
- 正式場景擺放、手機上的效果都未驗；不寫幀率。
