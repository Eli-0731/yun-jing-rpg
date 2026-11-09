| 項目 | 內容 |
|---|---|
| 誰做的 | C（Eli-0731） |
| 工作包 | docs/execution/2026-11-05/C-48h-a3-creekside-life.md（併入 docs/execution/2026-11-07/C-128h-creekside-and-village-life.md 第一部分） |
| ID | WL01–WL05（#88）、FI01–FI05 |
| 分支／PR | WL：art/c-1107-wl-washing-props ／ #88；FI：art/c-1107-fi-fishing-props ／ 開 PR 後補 |
| 版本 | v001（檔名帶 `_v001`；之後改版另存 v002，不覆寫） |
| 狀態 | Exported ／ Imported（Unity 6000.0.82f1 獨立匯入檢查）／ Visually Verified（Blender 與 Unity 審圖）／ In-game Verified：未驗（沒放進正式場景） |
| 素材來源 | 原創；三視圖參考在 `art/references/WL01/`–`WL05/`、`art/references/FI01/`–`FI05/` |

# A3 西溪洗衣小物 WL01–WL05、釣具 FI01–FI05

工作包第一段（WL，洗衣埠頭旁）和第二段（FI，釣魚台岸邊）：讓 A3 西溪看起來有人日常使用的十件小道具。靜態擺設，沒有玩法、碰撞或動畫；釣竿和網是收起的，不做可操作物或魚。

**共同做法**
- 先生成三視圖（每件至少 4 張）、自評選一張（分數和取捨在各自的 `prompt.txt`），再做灰模（`art/previews/creekside-life-c/<ID>/clay/`），最後上貼圖。
- 原點在腳印中心、底部 z = 0，Blender −Y 是正面（FBX／Unity 是 −Z）。不附地面底板，五件分開，可各自擺放。
- 一件一個材質、一套 1024 貼圖（11/07 小道具規則）；可有可無的小東西放 `Detail_*` 子物件（標準畫質關掉）。本體的環境遮蔽在烘焙時不含 Detail_，關掉後不會留下繩子或木釘的陰影。
- LOD1 約 50%、LOD2 約 15%，LOD0 不減面。`minTier` 都是 `high`（畫質分級第 4 節：增加豐富度的路邊擺設，不擋路、不參與玩法），所以沒有碰撞。
- 重建：`blender -b --factory-startup -P art/source/creekside-life-c/build_wl.py -- WL01 [--clay]`；審圖與 QA：`BL=<blender> sh art/source/creekside-life-c/render_reviews.sh`；Unity：`UNITY=<Unity.exe> sh art/source/creekside-life-c/unity/run_unity_check.sh`。

### FI01 細竹釣竿（收起）（FishingPole，v001）

長 2.2 m 的竹竿平放：一截磨亮的木握把套，竹竿一節節變細、竹節微凸，竿尖最後 35 cm 側彎；上段一塊裂竹夾板用麻繩交叉綁住（修補）；釣線從竿尖經兩個繩圈沿竿身拉到握把上方一根小木棒線架，繞成一捆（收起，沒有鉤和餌）。擺放時可整件轉成斜靠。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/FI01/`，選用 cand-2（92） |
| 尺寸（寬 × 深 × 高） | 2.2 × 0.153 × 0.055 m（上限 2.2 × 0.2 × 0.2 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 7,480 / 3,740 / 1,122（不含 Detail_：4,680 / 2,340 / 702） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_Line） |
| 材質數 | 1（`M_FI01_FishingPole`，本體和 Detail_ 共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | high |
| 檔案 | `art/exports/creekside-life-c/FI01_v001.fbx`（LOD0–2）、`art/exports/creekside-life-c/FI01_v001.glb`（LOD0）、`art/source/creekside-life-c/FI01_v001.blend` |

### FI02 木線輪與麻線（LineSpool，v001）

照參考圖直立做好再側躺（0.28 × 0.28 × 0.12 m）：兩片立柱外側磨出指凹，上下兩根橫木，中間一根木軸繞滿麻線（兩層不整齊的線圈加幾道交叉），軸的一端是較新、較淺的換過的木栓；線頭繞在上橫木打結。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/FI02/`，選用 cand-1（92） |
| 尺寸（寬 × 深 × 高） | 0.28 × 0.268 × 0.118 m（上限 0.28 × 0.28 × 0.12 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 5,358 / 2,678 / 1,380（不含 Detail_：5,130 / 2,564 / 1,346） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_LooseEnd） |
| 材質數 | 1（`M_FI02_LineSpool`，本體和 Detail_ 共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | high |
| 檔案 | `art/exports/creekside-life-c/FI02_v001.fbx`（LOD0–2）、`art/exports/creekside-life-c/FI02_v001.glb`（LOD0）、`art/source/creekside-life-c/FI02_v001.blend` |

### FI03 竹圈抄網（LandingNet，v001）

平放：一根彎竹圍成水滴形竹圈，兩端沿握把兩側用深色繩綁住，竹圈上幾處小綁繩；網兜塌在竹圈下面的地上（所以總高只有 4 cm），網線一條條建出、略歪扭、交叉處有網結，一處用深色線補過；握把纏舊布；網的遠端還濕。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/FI03/`，選用 cand-2（92） |
| 尺寸（寬 × 深 × 高） | 1.3 × 0.442 × 0.043 m（上限 1.3 × 0.45 × 0.06 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 9,464 / 4,732 / 1,418（不含 Detail_：9,408 / 4,704 / 1,410） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_Repair） |
| 材質數 | 1（`M_FI03_LandingNet`，本體和 Detail_ 共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | high |
| 檔案 | `art/exports/creekside-life-c/FI03_v001.fbx`（LOD0–2）、`art/exports/creekside-life-c/FI03_v001.glb`（LOD0）、`art/source/creekside-life-c/FI03_v001.blend` |

### FI04 長錐形竹魚筌（FishTrap，v001）

側躺並傾斜到口部和尾端都著地：22 條劈竹從粗竹圈口部收向尾端、尾端束緊綁繩，三道竹箍和三道麻繩，竹條間留空看得出是空心；口內一個短的倒漏斗（魚進得去出不來，這是和背簍最大的差別）；側面一塊補編片；著地那一側濕暗帶綠。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/FI04/`，選用 cand-3（93） |
| 尺寸（寬 × 深 × 高） | 0.892 × 0.38 × 0.38 m（上限 0.9 × 0.38 × 0.38 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 10,016 / 5,008 / 1,514（不含 Detail_：9,876 / 4,938 / 1,480） |
| 物件數（每個 LOD） | 3（本體 1 + Detail_Fray, Detail_Patch） |
| 材質數 | 1（`M_FI04_FishTrap`，本體和 Detail_ 共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | high |
| 檔案 | `art/exports/creekside-life-c/FI04_v001.fbx`（LOD0–2）、`art/exports/creekside-life-c/FI04_v001.glb`（LOD0）、`art/source/creekside-life-c/FI04_v001.blend` |

### FI05 三顆木浮子與繩（Floats，v001）

三種不同形狀的輕木浮子：紡錘形（約 0.2 m，頂端木栓，兩道淡紅色浮標漆圈）、鼓形（約 0.12 m，中心穿孔走繩，一端缺角）、蛋形（約 0.08 m，頸部刻槽綁繩）；一條鬆麻線穿過鼓形浮子把三顆連起，中間一個手打的結和一段起毛的繩尾，下半部水漬。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/FI05/`，選用 整組 cand-1（91）；單顆 a-4、b-3、c-2（各 92） |
| 尺寸（寬 × 深 × 高） | 0.437 × 0.3 × 0.074 m（上限 0.5 × 0.3 × 0.2 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 2,792 / 1,396 / 418（不含 Detail_：2,764 / 1,382 / 414） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_Tail） |
| 材質數 | 1（`M_FI05_Floats`，本體和 Detail_ 共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | high |
| 檔案 | `art/exports/creekside-life-c/FI05_v001.fbx`（LOD0–2）、`art/exports/creekside-life-c/FI05_v001.glb`（LOD0）、`art/source/creekside-life-c/FI05_v001.blend` |

### WL01 老木洗衣板（WashBoard，v001）

左右兩條側框夾住搓洗板；上方一塊磨出淺凹的平面，下方 12 條圓肋，中段一條斷掉的肋換成較新的平板、兩端麻繩綁住；上端橫木有提手孔，下端擋木；背面三條橫檔。平放、肋朝上。下緣（擋木那端）濕暗，角落少量苔。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/WL01/`，選用 cand-4（93） |
| 尺寸（寬 × 深 × 高） | 0.697 × 0.4 × 0.078 m（上限 0.7 × 0.4 × 0.12 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 7,816 / 3,908 / 1,172（不含 Detail_：6,000 / 3,000 / 900） |
| 物件數（每個 LOD） | 3（本體 1 + Detail_Lashing, Detail_Pegs） |
| 材質數 | 1（`M_WL01_WashBoard`，本體和 Detail_ 共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | high |
| 檔案 | `art/exports/creekside-life-c/WL01_v001.fbx`（LOD0–2）、`art/exports/creekside-life-c/WL01_v001.glb`（LOD0）、`art/source/creekside-life-c/WL01_v001.blend` |

### WL02 洗衣木槌（BeatingPaddle，v001）

厚實的槌頭往前端加厚，前端平面是端面木紋（年輪圍著面下方的髓心，有放射狀細裂）；肩部收成圓頸，頸上纏 6 圈麻繩；握柄兩段手指凹，頂端扁圓並穿孔掛繩。平放，傾斜 1.8° 讓槌頭前端和柄尾都著地。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/WL02/`，選用 cand-3（92） |
| 尺寸（寬 × 深 × 高） | 0.45 × 0.14 × 0.068 m（上限 0.45 × 0.15 × 0.12 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 4,102 / 2,050 / 614（不含 Detail_：3,710 / 1,854 / 556） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_Cord） |
| 材質數 | 1（`M_WL02_BeatingPaddle`，本體和 Detail_ 共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | high |
| 檔案 | `art/exports/creekside-life-c/WL02_v001.fbx`（LOD0–2）、`art/exports/creekside-life-c/WL02_v001.glb`（LOD0）、`art/source/creekside-life-c/WL02_v001.blend` |

### WL03 捲起的粗布（RolledLinen，v001）

一條對折的粗麻布（厚 1.8 cm）捲 4 圈，被自身重量壓成扁橢圓，兩端各圈略錯開、端面看得到一層層的布；外層布邊翹起一點；一道鬆麻繩繞一圈、打結、兩條繩尾垂下。一端下半部濕暗。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/WL03/`，選用 cand-3（92） |
| 尺寸（寬 × 深 × 高） | 0.568 × 0.3 × 0.196 m（上限 0.65 × 0.3 × 0.25 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 7,544 / 3,772 / 1,164（不含 Detail_：7,240 / 3,620 / 1,086） |
| 物件數（每個 LOD） | 3（本體 1 + Detail_CordEnds, Detail_Fray） |
| 材質數 | 1（`M_WL03_RolledLinen`，本體和 Detail_ 共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | high |
| 檔案 | `art/exports/creekside-life-c/WL03_v001.fbx`（LOD0–2）、`art/exports/creekside-life-c/WL03_v001.glb`（LOD0）、`art/source/creekside-life-c/WL03_v001.blend` |

### WL04 折好的濕布兩疊（FoldedLinen，v001）

第二版（#88 審查）。兩疊分開、相隔約 5 cm：左疊 10 層（只有一層暗藍布），右疊 8 層、頂上一塊補丁。每層是薄布，露出 1.3–1.8 cm：前側是圓弧折痕，後側是參差的布邊（只有上面變薄），每層錯開 0.5–2 cm、四角略垂；左疊頂層一角翻折垂下。濕布色：疊頂 #B8AE9A、往下漸暗到 #8E8676，粗糙度 0.78 → 0.66，加幾塊較濕的暗斑和淡水痕。第一版對照在 `art/previews/creekside-life-c/compare-v1/WL04.jpg`。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/WL04/`，選用 cand-12（92，第三輪） |
| 尺寸（寬 × 深 × 高） | 0.6 × 0.454 × 0.162 m（上限 0.6 × 0.5 × 0.25 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 8,356 / 4,178 / 1,252（不含 Detail_：8,208 / 4,104 / 1,230） |
| 物件數（每個 LOD） | 3（本體 1 + Detail_Flap, Detail_Patch） |
| 材質數 | 1（`M_WL04_FoldedLinen`，本體和 Detail_ 共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | high |
| 檔案 | `art/exports/creekside-life-c/WL04_v001.fbx`（LOD0–2）、`art/exports/creekside-life-c/WL04_v001.glb`（LOD0）、`art/source/creekside-life-c/WL04_v001.blend` |

### WL05 石製皂灰小盤與灰餅（AshDish，v001）

一整塊暖灰田石鑿出的橢圓淺盤，外壁外斜、盤緣高低不一且一側磨低，凹槽約 5 cm；中間一塊壓實的灰餅（略高出盤緣，頂面乾裂）；凹槽裡一圈濕痕和灰屑痕；前壁一道舊裂縫用兩根鐵扣補住。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/WL05/`，選用 cand-4（92） |
| 尺寸（寬 × 深 × 高） | 0.38 × 0.268 × 0.105 m（上限 0.38 × 0.28 × 0.12 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 2,460 / 1,230 / 366（不含 Detail_：2,272 / 1,136 / 340） |
| 物件數（每個 LOD） | 3（本體 1 + Detail_Crumbs, Detail_Staples） |
| 材質數 | 1（`M_WL05_AshDish`，本體和 Detail_ 共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | high |
| 檔案 | `art/exports/creekside-life-c/WL05_v001.fbx`（LOD0–2）、`art/exports/creekside-life-c/WL05_v001.glb`（LOD0）、`art/source/creekside-life-c/WL05_v001.blend` |

## 驗證

- QA（`tools/art/qa_lod0_basic.py` 嚴格與寬鬆、`tools/art/qa_contact_glb.py`）：結果在 `art/previews/creekside-life-c/qa/`。
- Unity 6000.0.82f1 獨立匯入：`art/previews/creekside-life-c/unity/report.txt`，布（WL03、WL04）用雙面材質並加低角度截圖。
- 同光同角度並排（含 1.75 m 人形尺，灰模和成品各一張）：`art/previews/creekside-life-c/compare/`，總表 `compare-sheet.jpg`。WL01／02 對舊木器（C 木箱 BM01_01、B 柴堆 R03），WL03／04 對既有布件（C 舊蒲團 UP05、B 草蓆 TI06），WL05 對 BM05_03 方凳、BM06_01 石缸。

FI01–FI05 對水工竹繩件：FI01、FI03、FI04 和 B 的河床清淤篩 B08、流速指示浮標 B09 同場（`FI-vs-waterworks`），FI02、FI05 對 B09（`FI02-FI05-vs-float`），FI04 對 B 的背簍 MK04（`FI04-vs-basket`，看得出不是背簍）。

**和既有模型的三個共同點**（工作包第 7 節）
1. 材料一看就認得、帶使用痕跡：舊木有木紋、乾裂和被手磨亮的邊（同 BM01 木箱、R03 柴堆）；石是同一套暖灰田石、邊被磨圓（同 BM05、BM06）；布是低飽和的本色麻布，沒有花紋和字。
2. 同一組底色：舊木落在風格規格第 2 節的暖褐（#5A3A22–#7A5234），石在暖灰，布只有一塊褪色暗藍；大塊柔和的深淺，只有少量筆觸。
3. 磨損有位置：濕暗和苔只在接地、泡水的那一側（洗衣板擋木端、布疊下層、捲布一端、石盤凹槽一圈），凸出的邊緣和手握的地方較亮、較滑，和 BM 系列地面接觸處的做法相同。

## 已知問題與未驗

- 正式場景擺放、手機上的效果都未驗。
- `A3_WashProps` 格位：工作包第 3 節的中心 (-95.2, -14) 落在 `A3_WashSteps`（WM05）範圍內；核心組在 #88 決定改到 (-95.2, -17.6)（石階北端外側），接入時由核心組處理，本 PR 不改 `tools/qingxi-terrain/blocks/A3.json`。
- WL01 參考圖比例約 2.1 : 1，照工作包 0.70 × 0.40 m 做；圓肋上的木紋近看偏碎。
- WL03 審查建議（加分項，這輪未做）：底色再壓暗一點、加幾塊髒污。
- FI01 照工作包做成平放；「收納可斜靠」由擺放時整件旋轉處理。
- FI03 的網線很細，LOD2（15%）只剩竹圈和握把的輪廓、網線大多消失。
- FI05 單顆浮子的三視圖：工作包要求每個不同輪廓都要有四張以上候選，所以三種浮子另各生成 4 張，只改物件描述，細節在 `art/references/FI05/prompt.txt`。
- WL03 為了把垂下的繩尾放進 0.3 m 深的上限，整件縮到長 0.57 m（上限 0.65 m）。
- WL04 前兩輪（cand-1–8）照工作包原文生成都只畫一疊，第三輪只改物件描述（固定段 5.2、5.3 不動）才畫出兩疊，細節在 `art/references/WL04/prompt.txt`。
