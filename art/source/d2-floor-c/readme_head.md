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

