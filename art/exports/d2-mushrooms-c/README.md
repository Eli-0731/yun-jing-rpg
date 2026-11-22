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
### DP01_01 褐色蕈叢・細長五朵（BrownMushroomsTall，v002）

五朵高低不同的細長褐蕈從一團苔墊長出，往外分開（最高的傘頂 17 cm、傘寬 9 cm，最小的傘寬 4 cm）。像 V4、V5 根邊那種細長柄的褐蕈。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP01/`，選用 A cand-1（91） |
| 尺寸（寬 × 深 × 高） | 0.168 × 0.141 × 0.172 m（高度含地下的苔墊） |
| 三角面 LOD0 / LOD1 / LOD2 | 2,980 / 1,489 / 447（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP01_01_BrownMushroomsTall`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-mushrooms-c/DP01_01_v002.fbx`（LOD0–2）、`art/exports/d2-mushrooms-c/DP01_01_v002.glb`（LOD0）、`art/source/d2-mushrooms-c/DP01_01_v002.blend` |

### DP01_02 褐色蕈叢・粗壯三朵（BrownMushroomsStout，v002）

一朵大的成熟褐蕈（傘寬 11 cm、柄粗 2.5 cm、高 12 cm）和兩朵小的（傘寬 6 cm、4 cm）。像 V6 坑邊那叢。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP01/`，選用 B cand-1（91） |
| 尺寸（寬 × 深 × 高） | 0.214 × 0.152 × 0.136 m（高度含地下的苔墊） |
| 三角面 LOD0 / LOD1 / LOD2 | 1,998 / 999 / 298（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP01_02_BrownMushroomsStout`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-mushrooms-c/DP01_02_v002.fbx`（LOD0–2）、`art/exports/d2-mushrooms-c/DP01_02_v002.glb`（LOD0）、`art/source/d2-mushrooms-c/DP01_02_v002.blend` |

### DP01_03 褐色蕈叢・沿根腳一列（BrownMushroomsRootRow，v002）

十朵排成一條微彎的線（長 0.5 m），兩端是小圓鈕，往中間越來越大、傘張開。擺在任一段根的根腳，像 V2 根腳那排。根不在模型裡（根是 Josh 的 DR 系列），模型只有沿根腳的一條窄苔帶。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP01/`，選用 C cand-1（90） |
| 尺寸（寬 × 深 × 高） | 0.572 × 0.082 × 0.113 m（高度含地下的苔墊） |
| 三角面 LOD0 / LOD1 / LOD2 | 3,802 / 1,900 / 570（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP01_03_BrownMushroomsRootRow`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-mushrooms-c/DP01_03_v002.fbx`（LOD0–2）、`art/exports/d2-mushrooms-c/DP01_03_v002.glb`（LOD0）、`art/source/d2-mushrooms-c/DP01_03_v002.blend` |

### DP01_04 褐色蕈叢・簇生一叢（BrownMushroomsTuft，v002）

十二朵從同一個基部長出，柄往外彎，有半開的幼菇和張開的傘，長在一塊半埋的朽木片上，木片頂上一小片苔。從十幾朵減成十二朵是為了 LOD0 ≤ 4,000 面。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP01/`，選用 D cand-1（91） |
| 尺寸（寬 × 深 × 高） | 0.18 × 0.165 × 0.136 m（高度含地下的苔墊） |
| 三角面 LOD0 / LOD1 / LOD2 | 3,672 / 1,836 / 549（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP01_04_BrownMushroomsTuft`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-mushrooms-c/DP01_04_v002.fbx`（LOD0–2）、`art/exports/d2-mushrooms-c/DP01_04_v002.glb`（LOD0）、`art/source/d2-mushrooms-c/DP01_04_v002.blend` |

## v002 技術驗證

- 所有變體的 LOD0 在 4,000 三角面內，維持單材質和 1024 貼圖。逐 LOD 統計見 model_info。
- 嚴格／寬鬆 QA 每件均 0／0，接觸檢查最大間隙 0.9 mm。報告在 `art/previews/d2-mushrooms-c/qa/`。
- Unity 6000.3.28f1 獨立匯入驗證 64 項 PASS、0 項 FAIL，報告在 `art/previews/d2-mushrooms-c/unity/report.txt`。

## v001 視覺檢查紀錄（DP01）

灰模三輪、上貼圖後兩輪，每輪看同樣的角度，先修最嚴重的：
1. 灰模第一輪：傘太扁，像一片片圓餅 → 改成有厚度的傘；DP01_04 的柄擠成一束、傘疊在一起、木片是方盒 → 柄往外彎、木片改成不規則的片；DP01_03 太小太細 → 傘和柄放大。
2. 灰模第二、三輪：DP01_04 的幼菇脹成球、四朵大的都在同一邊 → 幼菇縮小、大的分到四個方向。
3. 上貼圖第一輪（和 D2 並排）：傘是尖的斗笠形，D2 是寬的扁平微凸 → 改成低圓頂加中間小隆起；傘上白斑太多太大 → 減成幾點小斑；苔墊太亮太綠、太高 → 改暗橄欖綠、壓低。
4. 上貼圖第二輪：傘緣看得出多邊形 → DP01_01、DP01_02 的傘段數加多（面數還在 4,000 內）；柄像淺色塑膠 → 改成灰褐、加深色纖維紋；DP01_04 的木片像一塊亮橘色木板 → 改成暗、濕、有剝落的朽木。

**v001 自評：和 D2 設定圖並排約 65–70% 像，還沒到 85–90%。** 傘的顏色、形狀、淺色傘緣、細長柄和成叢的樣子對得上；差的是：
- 設定圖的蕈長在根、苔、蕨、落葉中間，單件放在空地上看比較「乾淨」；整合時和根、苔、蕨擺在一起才是設定圖的樣子（DP05 的擺放示範會做這件事）。
- 小傘（DP01_03 兩端、DP01_04）段數少，近看傘緣有稜角；DP01_04 的朽木片還是低面數的稜面。
- 菌褶從上往下看不到，只有蹲低的鏡位看得到（D2 V6 也是蹲低才看得到）。

## v001 已知問題與未驗

- 工作包寫「擺幾處 64」，這裡只交四種模型，擺放由核心組做。
- DP01_03 沒有根本體，擺的時候要貼著任一段根的根腳放。
- 正式場景擺放、手機上的效果都未驗；不寫幀率。

## v002 視覺對照與驗收

- `art/previews/d2-mushrooms-c/<ID>/d2/<ID>-d2-compare.jpg` 並排設定圖裁切、v001、v002。兩版模型在同一個 Blender 相機、照明和地景比較；根、土、石和葉是本機審圖用的陪襯。
- 成熟傘增加不同頻率的環向起伏與小缺口，傘頂加內圈改善中央尖折。大傘降低隆起、放寬傘肩。重做傘緣的淺色分布和褶縫的深淺，調整細長款最小一朵的位置以減少交疊。
- 正式 D2 場景的對圖鏡位、構圖、場景材質與光照仍待核對，90% 美術驗收尚未確認。
- 本輪觀察：大傘的褶縫在低視角已能辨識，V6 近景的菌褶仍更密、更淺，柄和傘緣也有更自然的濕潤反光。
