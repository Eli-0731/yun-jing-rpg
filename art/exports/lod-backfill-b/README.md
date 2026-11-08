# 承天｜2026-11-07 工作包：LOD 補件（舊素材補 LOD1／LOD2 與 Detail_*）

| 項目 | 內容 |
|---|---|
| 誰做的 | B（joshsu54） |
| 工作包 | docs/execution/2026-11-07/B-104h-tea-wheel-and-mountain-way.md（LOD 補齊；檔案在 `feature/qingxi-creek-chapter` 分支）；規則照 docs/standards/quality-tiers-v1.md 第 4 節 |
| ID | qingxi-alchemy-b B01–B12（15 件，含加熱／空瓶等狀態）、creek-repair-b-props A04／C03／C04／C06／C07、Dondon StarterHouse、Blacksmith、TownLayout 的客棧（TownInn），共 23 件 |
| 分支／PR | art/b-1107-vl-houses-lod ／ 未開（排在 FR 那張之後；同時只開一張待審 PR）；和 VL01–03（`art/exports/village-houses-b/`）同一張 PR |
| 版本 | 全部 v001（新資料夾 `lod-backfill-b/`；來源檔一個都沒改，原本的 LOD 也還在原處） |
| 狀態 | Exported ／ Imported（Unity 編輯器批次檢查）／ Visually Verified；In-game Verified：未驗 |
| 素材來源 | 改自既有素材，只加 LOD：qingxi-alchemy-b v001（B）、creek-repair-b-props（B）、Dondon StarterHouse v004／Blacksmith v001／TownLayout v004（Dondon）。LOD0 就是原本的幾何，沒有重做 |
| 實際工時 | 2026-11-08 23:05 起，到 11-09 00:20（台灣時間），約 1 小時 15 分；和 VL01–03 收尾同時進行 |

**沒有改主場景、沒有改區塊 JSON、沒有宣稱已正式落位。** 新東西只做在 Unity 用的模型裡，沒有新增網頁版（PWA）頁面。來源檔只讀不寫；客棧從 TownLayout v004 取出，原點改到腳印中心、底部 0（位移 −16.2, 22.2, 1.12 m 寫在 `recentre_offset_m`），TownLayout 本身沒動。

## 做了什麼

每件輸出一個 `<ID>_LOD_v001.fbx`（加 `.blend`、`model_info.json`），裡面 6 個物件：
- `<ID>_LOD0／LOD1／LOD2`：本體。LOD0 和來源幾何一模一樣，只把零件合成一個物件。
- `<ID>_Detail_Small_LOD0／LOD1／LOD2`：小零件（瓶子、繩結、門前小物、碎石等），低畫質可以整個關掉，關掉後外形不變。沒有小零件的件（B03、B10 空瓶、C07、A04）就沒有這個物件。

LOD1 約 50%、LOD2 約 15%：先把平面上多餘的線溶掉（材質、UV、銳邊不動），再減面到目標數。審圖時發現有些件 LOD2 壞掉，改用下面的做法（`jobs.json` 每件都記著用了哪些，model_info 的 `lod_method` 也有）：

| 做法 | 用在 | 為什麼 |
|---|---|---|
| 逐零件 | B06、B07、B08、B10 ×2、B12、C03、A04、客棧 | 整件一起減面時，小零件（瓶塞、蓋子、桶緣、河岸表皮）會先被壓壞或破洞；改成每個零件照同一比例各自減 |
| LOD2 每件至少 30%／50% | B06、B08、C03（30%）、B10 ×2（50%） | 雙層桶壁、罐口、瓶塞這種圓殼低於這個比例就合不起來，會變成尖刺或楔形 |
| 保邊 | B06、B07、B08、B10 ×2、B12、C03 | 開口邊和硬轉角（桶緣、蓋緣、板端）減面時不移動 |
| 重算法線 | B12 | 沿用 LOD0 的自訂法線時石塊變黑 |
| 開口表皮留在本體 | A04 | A04 的河岸表皮是蓋在土堆上的開口薄片，原本被當成小零件，關掉 Detail 會露出破洞；現在一律留在本體，所以 A04 沒有可關的小零件 |
| 大而簡單的零件不減 | 逐零件的那幾件 | 面數 ≤ 64、卻佔整件 25% 以上長度的零件（水面條、木板）一減就變大三角形 |

**代價（照實寫）**：上面那幾件的 LOD2 高於 15%（22–50%），B07、B12、C03 的 LOD1 也高於 50%（56–60%）；這幾件 LOD0 本來就只有 1,000–9,000 面，客棧是 11,038 面。

## 全批數量（物件、材質、貼圖）

每件每級 LOD 是 1–2 個物件（本體＋Detail_Small）。貼圖照來源原樣帶過來，沒有重烘。

| ID | 尺寸（m） | LOD0／LOD1／LOD2 三角面 | LOD2 比例 | 關掉 Detail 的 LOD0 | Detail 零件數 | 材質 | 貼圖（px） | minTier | 做法 |
|---|---|---|---|---|---|---|---|---|---|
| StarterHouse | 9.05 × 8.19 × 5.61 | 105,928／52,964／15,888 | 15% | 83,020 | 117 | 16 | 無（純色材質） | standard | 整體 |
| Blacksmith | 7.43 × 5.72 × 5.36 | 86,854／43,426／13,026 | 15% | 72,106 | 115 | 21 | 無（純色材質） | standard | 整體 |
| TownInn | 14.38 × 14.79 × 10.41 | 51,152／25,258／11,038 | 22% | 48,400 | 10 | 15 | 無（純色材質） | standard | 逐零件 |
| B01_BronzeFurnace_cold | 0.74 × 0.77 × 0.89 | 14,912／7,454／2,236 | 15% | 14,000 | 12 | 1 | 1024 ×3 | standard | 整體 |
| B01_BronzeFurnace_heating | 0.74 × 0.77 × 0.89 | 14,912／7,454／2,236 | 15% | 14,000 | 12 | 1 | 1024 ×4 | standard | 整體 |
| B02_FurnaceLid | 0.54 × 0.54 × 0.28 | 6,216／3,108／930 | 15% | 5,768 | 5 | 1 | 1024 ×3 | standard | 整體 |
| B02_FurnaceLid_heating | 0.54 × 0.54 × 0.28 | 6,216／3,108／930 | 15% | 5,768 | 5 | 1 | 1024 ×4 | standard | 整體 |
| B03_StoneMortar | 0.34 × 0.32 × 0.21 | 2,276／1,138／340 | 15% | 2,276 | 0 | 1 | 512 ×3 | standard | 整體 |
| B04_BambooSortingTrays | 0.63 × 0.47 × 0.67 | 7,824／3,912／1,184 | 15% | 4,624 | 28 | 1 | 1024 ×3 | standard | 整體 |
| B05_HerbDrawerCabinet | 0.76 × 0.48 × 0.94 | 7,000／3,500／1,049 | 15% | 6,448 | 18 | 1 | 1024 ×3 | standard | 整體 |
| B06_CeramicWaterJar | 0.55 × 0.47 × 0.55 | 4,544／2,292／1,292 | 28% | 4,312 | 6 | 1 | 1024 ×3 | standard | 逐零件，LOD2 每件至少 30%，保邊 |
| B07_WoodenFuelBox | 0.69 × 0.43 × 0.46 | 5,068／3,036／1,842 | 36% | 3,596 | 16 | 1 | 1024 ×3 | standard | 逐零件，保邊 |
| B08_VentilatedDryingBasket | 0.73 × 0.65 × 0.21 | 8,956／4,468／2,734 | 31% | 5,100 | 64 | 1 | 2048 ×3 | standard | 逐零件，LOD2 每件至少 30%，保邊 |
| B09_ClothFilterFrame | 0.62 × 0.42 × 0.93 | 6,996／3,498／1,048 | 15% | 6,188 | 17 | 1 | 1024 ×3 | standard | 整體 |
| B10_WaxSealedBottle_empty | 0.11 × 0.08 × 0.11 | 1,036／522／522 | 50% | 1,036 | 0 | 2 | 512 ×3 | standard | 逐零件，LOD2 每件至少 50%，保邊 |
| B10_WaxSealedBottle_filled | 0.07 × 0.08 × 0.12 | 2,612／1,308／1,172 | 45% | 2,236 | 14 | 3 | 512 ×3 | standard | 逐零件，LOD2 每件至少 50%，保邊 |
| B11_BambooRecipeStand | 0.57 × 0.36 × 0.45 | 4,064／2,032／608 | 15% | 3,128 | 6 | 1 | 1024 ×3 | standard | 整體 |
| B12_WorkshopChimney | 0.76 × 0.74 × 1.95 | 6,144／3,471／1,757 | 29% | 3,892 | 20 | 1 | 1024 ×3 | standard | 逐零件，保邊，重算法線 |
| C03 | 0.67 × 0.32 × 0.56 | 3,172／1,896／1,400 | 44% | 3,028 | 4 | 5 | 128 ×3 | standard | 逐零件，LOD2 每件至少 30%，保邊 |
| C04 | 1.26 × 0.06 × 0.31 | 2,424／1,204／362 | 15% | 504 | 5 | 3 | 128 ×3 | standard | 整體 |
| C06 | 0.46 × 0.22 × 0.85 | 1,256／628／186 | 15% | 1,124 | 3 | 5 | 128 ×4 | standard | 整體 |
| C07 | 0.49 × 0.28 × 0.33 | 2,420／1,210／362 | 15% | 2,420 | 0 | 4 | 128 ×3 | standard | 整體 |
| A04_SiltBar | 2.47 × 2.97 × 0.70 | 4,066／2,052／739 | 18% | 4,066 | 0 | 2 | 1024 ×3 | standard | 逐零件，開口表皮留在本體 |
- 「關掉 Detail 的 LOD0」是只留本體時的三角面；「Detail 零件數」是被分到 Detail_Small 的零件個數（以零件外框小於 min(門檻, 整件 12%) 判斷，門檻：房子 0.35 m、煉丹 B 件 0.04–0.05 m、瓶子 0.015 m、C 件 0.08 m、A04 0.15 m；StarterHouse 另把 `07_Porch_Props` 整組算 Detail）。
- 材質數照來源：Dondon 三間房子用純色材質（沒有貼圖），B 件一件一張圖集，C 件 128 px 小圖。
- 房子三間的 LOD0 帶著來源原本就有的零面積三角面（StarterHouse 48、Blacksmith 64、客棧 64），LOD0 不改所以留著；Unity 匯入時會自動丟掉（StarterHouse 實際少 36 面），已記在 model_info 的 `lod0_zero_area_triangles`。

**minTier**：23 件都是 standard（煉丹工作台、修水物件、房子都是會擋人或要互動的東西，所有畫質都看得到；只有 Detail_Small 在低畫質關掉）。

## 前後對照圖

每件一張 `art/previews/lod-backfill-b/<ID>/<ID>_LOD_compare.png`，五格同一個鏡頭、同一盞光：LOD0（原樣）、LOD1、LOD2、LOD0 關掉 Detail_*、LOD1 關掉 Detail_*，上面標三角面數。單格原圖也在同一個資料夾。Unity 裡的對照（LOD0／LOD1／LOD2／LOD1 關掉 Detail 四個並排）在 `artifacts/lod-backfill-unity/`（本機，不提交）。

審圖結果：23 件的 LOD1 和 LOD0 看起來幾乎一樣，關掉 Detail 後外形不變。LOD2 看得出減面，但沒有破洞、尖刺或變形。

## 已知問題

- **StarterHouse 的 LOD2 瓦頂**：近看時瓦溝變淺，瓦片之間露出底下的木板條，瓦面有深淺斑塊（Blacksmith 的 LOD2 瓦面也有較輕的斑塊）。試過逐零件減面（更糟，整片木板露出來）和保邊（沒有變化）。這一級只在遠距使用，遠處看不出來，但沒有在遊戲裡實測切換距離。
- **客棧的 LOD1 關掉 Detail**：屋頂幾排瓦面顏色略淺，近看看得出來。
- A04 原本就有 LOD0/1/2（在 `creek-repair-b-props/A04_SiltBar/`），這裡重做的 LOD1／LOD2 是新的一套；遊戲要用哪一套由核心組決定。煉丹 B 件原本的 LOD2 約 22%，這裡改成約 15%（有例外的見上表），原檔也還在。

## Unity 實測（編輯器批次檢查，失敗 0 項，180 項通過）

每件檢查：`_LOD0/1/2` 三個本體都在；匯入尺寸和 model_info 一致（誤差 < 2 mm）；三角面和物件數每級都和 model_info 一樣（LOD0 允許少掉來源的零面積三角面）；只留本體時的三角面也一樣；Detail_Small 在三級都是獨立物件；LODGroup 三級都有東西；沒有缺貼圖或錯誤 shader。每件一張四級並排截圖。Unity 6000.0.85f1；只是編輯器批次檢查，沒有放進主場景，也沒有進遊戲。

## 交付位置

- FBX、可編輯 .blend、model_info.json、來源帶來的貼圖（`.fbm/`）：`art/exports/lod-backfill-b/<ID>/`。
- 前後對照圖：`art/previews/lod-backfill-b/<ID>/`。
- 腳本：`art/source/lod-backfill-b/`
  - `make_jobs.py` 產生 `jobs.json`（每件的來源、門檻、做法）。
  - `lod_backfill.py` 做 LOD 與匯出。
  - `lod_compare.py`、`lod_compare_sheet.py` 畫對照圖。
  - `run_all.sh` 全部重跑：`bash art/source/lod-backfill-b/run_all.sh [ID ...]`。
- Unity 檢查：`apps/game/Assets/YunJing/Editor/LodBackfillModelCheck.cs`，輸出到 `artifacts/lod-backfill-unity/`。

## 未驗

- 手機效能：沒有量測，不寫 FPS。
- LODGroup 的切換距離：檢查裡用的是 0.1／0.035／0.006 的螢幕高度比例，只是為了驗證三級都在，不是正式數值。
- 遊戲裡實際切換 LOD 時的跳動感、Detail_Small 在畫質選單裡關掉的效果。
- 原本已經擺在場景裡的這些物件換成新 FBX 後的位置（客棧的原點換過，見上面的位移）。
