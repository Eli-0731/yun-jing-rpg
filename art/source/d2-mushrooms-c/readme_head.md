| 項目 | 內容 |
|---|---|
| 誰做的 | C（Eli-0731） |
| 工作包 | docs/execution/2026-11-15/C-300h-D2-small-life.md，A 批；標準照 docs/execution/2026-11-15/00-300h-共同標準.md |
| ID | DP01（A 批樣品，四種：DP01_01–DP01_04；DP02–DP05 等樣品審過再做） |
| 分支／PR | art/c-1115-d2-mushrooms ／ 開 PR 後補 |
| 版本 | v002。v001 的母稿、模型及貼圖保留。 |
| 狀態 | Exported ／ Unity 6000.3.28f1 匯入結果見驗證紀錄／ Blender 並排審圖完成 ／ 正式 D2 場景驗收待驗 |
| 素材來源 | 原創；三視圖參考在 `art/references/DP01/`；貼圖全部在建模腳本裡畫，沒有外部素材 |
| 實際工時（v001） | 2026-11-19 03:45–04:35（台灣時間），約 50 分鐘：讀標準、三視圖、建模腳本、灰模三輪、上貼圖、視覺修正兩輪、QA、審圖、Unity 檢查 |

# D2 古樹神木的蕈（d2-mushrooms-c）

11/15 的 300 小時包 A 批：D2 古樹神木地上的小蕈（設定圖 V2、V4、V5、V6）。DP01 褐色蕈叢先交樣品，審過再做 DP02 白色小蕈、DP03 層狀菌、DP04 苔上小菇、DP05 擺放示範。靜態擺設；擺進世界由核心組做，這裡不改主場景、不改區塊 JSON。

**共同做法**
- 先生成三視圖（每種 4 張）、自評選一張（分數和取捨在 `art/references/DP01/prompt.txt`），再做灰模（`art/previews/d2-mushrooms-c/<ID>/clay/`），最後上貼圖。
- 傘、菌褶、柄都是真的幾何：傘是扁平微凸、中間微微隆起的低圓頂，傘緣略往下捲；傘下菌褶在網格上做成一圈起伏，細的褶線畫在貼圖上；柄有粗細、腳下微微膨大、略彎。沒有用卡片。
- 原點：底部中心，z = 0 在地面；苔墊（DP01_04 是朽木片）往地下延伸 1.2–1.7 cm，邊緣正好落在 z = 0（共同標準第四節，照 CO01 的做法），擺在不平的地上不會浮空。Blender −Y 是正面（FBX／Unity 是 −Z）。
- 一件一個材質、一套 1024 貼圖（Albedo／Normal／ORM／MaskURP），雙面（傘面和菌褶是兩片開放的面）。沒有 `Detail_*`。`minTier` 都是 `standard`。
- LOD：LOD1 約 50%、LOD2 約 15%（共同標準第四節）。
- 顏色照 D2：傘淡黃褐、中間深一點、傘緣淺奶油色、幾點淺色小斑；菌褶奶油色；柄灰褐帶深色纖維紋；苔是暗橄欖綠，不是亮綠。
- 建模流程和 yard-roadside-c 的 `build_vg.py` 相同（來源貼圖 → 一張 UV 圖集 → Cycles 烘焙），因為那個套件還沒進 main，所以把流程複製成 `build_dp.py`，工具（`creekside-life-c/wl_kit.py`）用 main 上的。亂數種子固定，重建結果一樣。
- 重建：`blender -b --factory-startup -P art/source/d2-mushrooms-c/build_dp.py -- DP01_01 [DP01_02 ...] [--clay]`；審圖、QA、D2 對圖用的渲染：`BL=<blender> sh art/source/d2-mushrooms-c/render_reviews.sh`；審圖總表和 D2 並排圖：`D2=<放 D2 V1–V6.png 的資料夾> sh art/source/d2-mushrooms-c/make_sheets.sh`；Unity：`UNITY=<Unity.exe 6000.3.28f1> sh art/source/d2-mushrooms-c/unity/run_unity_check.sh`。


**v002**
- 成熟傘增加不同頻率的環向起伏與小缺口，傘頂加內圈改善中央尖折。大傘降低隆起、放寬傘肩。重做傘緣的淺色分布和褶縫的深淺，調整細長款最小一朵的位置以減少交疊。
- 使用既有候選及選圖；v002 的貼圖在 `art/textures/d2-mushrooms-c/v002/`。
