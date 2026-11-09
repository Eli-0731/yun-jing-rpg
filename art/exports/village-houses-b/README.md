# 承天｜2026-11-07 工作包第二部分：VL01–03 空屋變體

| 項目 | 內容 |
|---|---|
| 誰做的 | B（joshsu54） |
| 工作包 | docs/execution/2026-11-07/B-104h-tea-wheel-and-mountain-way.md（第二部分 VL01–03；檔案在 `feature/qingxi-creek-chapter` 分支） |
| ID | VL01 久無人住的空屋、VL02 剛有人住的空屋、VL03 半塌的空屋 |
| 分支／PR | art/b-1107-vl-houses-lod ／ 本分支的 PR（#83 山城石階、FR 古林巨根還在待審時開出，使用者決定先開）；和 LOD 補件（`art/exports/lod-backfill-b/`）同一張 PR |
| 版本 | 全部 v001（首次交付，沒有舊版） |
| 狀態 | Exported ／ Imported（Unity 編輯器批次檢查）／ Visually Verified；In-game Verified：未驗 |
| 預定位置 | 青溪村空屋（`A1_QingxiVillage_EmptyHouse`），由核心組落位 |
| 素材來源 | 外框、尺寸、原點照 Dondon `art/incoming/dondon/StarterHouse/v004`（原檔未改，只讀）；牆面、瓦、門窗、破損與擺設是原創（Blender 程序化建模）；三視圖參考由 Codex image_gen 生成，只當外形參考 |
| 實際工時 | 2026-11-08 18:20 起，到 11-09 00:15 收尾（台灣時間），約 6 小時；其中 23:05 以後和 LOD 補件同時進行 |

**沒有改主場景、沒有改區塊 JSON、沒有宣稱已正式落位。** 新東西只做在 Unity 用的模型裡，沒有新增網頁版（PWA）頁面。Dondon 的 StarterHouse 原檔沒有改，三間都另存新檔。

## 進度

| ID | 名稱 | Exported | Imported（Unity 編輯器） | Visually Verified | In-game Verified |
|---|---|---|---|---|---|
| VL01_LongEmptyHouse | 久無人住的空屋 | 是 | 是 | 是 | 否 |
| VL02_MovedInHouse | 剛有人住的空屋 | 是 | 是 | 是 | 否 |
| VL03_HalfCollapsedHouse | 半塌的空屋 | 是 | 是 | 是 | 否 |

四屋並排圖（StarterHouse 原版＋VL01–03，同一盞光、同一個鏡頭）：`art/previews/village-houses-b/VL_StarterHouse_VL01_VL02_VL03_compare.png`。

**未驗**：
- 手機效能：沒有量測，不寫 FPS。
- 真人用鍵鼠走：Unity 的行走是在編輯器裡用 CharacterController.Move 推一個 1.75 m 膠囊，不是進遊戲跑。
- 放進青溪村正式地形後的落位、地面高低差、和旁邊房子的距離。
- 屋內：三間的門都是關的（VL01 釘死），屋內沒有做家具，也沒有室內碰撞以外的東西；VL03 從缺口看得到空屋內，但人進不去。
- `minTier` 只寫在 model_info 裡，遊戲的畫質分級沒有實測。

## 全批數量（物件、材質、貼圖）

每件每級 LOD 都是 2 個物件：本體 `<ID>_LOD0/1/2`＋`<ID>_Detail_Small_LOD0/1/2`（落葉、雜草、苔、門前小物，低畫質可以整個關掉）；另有 1 個隱藏的碰撞網格 `<ID>_Collision`，以及 3 個接口空物件（Socket_Door、Socket_Porch、Socket_Path）。

| ID | 尺寸（m） | LOD0／LOD1／LOD2 三角面 | 其中 Detail_Small | 材質 | 碰撞三角面 | 貼圖（px） |
|---|---|---|---|---|---|---|
| VL01_LongEmptyHouse | 8.983 × 8.198 × 5.552 | 76,060／38,030／10,584 | 13,876／6,938／2,080 | 4 | 164 | 2048 ×15 ＋ 共用 1024 ×4 |
| VL02_MovedInHouse | 8.983 × 8.189 × 5.552 | 63,186／31,592／8,769 | 1,726／862／257 | 4 | 164 | 2048 ×15 ＋ 共用 1024 ×4 |
| VL03_HalfCollapsedHouse | 9.277 × 8.191 × 5.552 | 72,884／36,437／10,303 | 11,450／5,725／1,717 | 4 | 176 | 2048 ×15 ＋ 共用 1024 ×4 |

**材質**（每件 4 個，URP Lit）
- `_Main`：灰泥牆、窗紙、雜項；`_Stone`：石基、台階、土磚、瓦礫；`_Wood`：柱、樑、門窗、木板、前廊。三張 2048 圖集，各 5 張貼圖：`_BaseColor`、`_Normal`、`_MetallicSmoothness`、`_Roughness`、`_Metallic`。Unity 材質只引用前三張；`_Roughness` 和 `_Metallic` 是給其他引擎與 GLB 用的。
- `_RoofTiles`：三間共用一套 1024 瓦片貼圖（`VL_Shared/Textures/VL_RoofTiles_*`，4 張），瓦片用自己的格子 UV，貼圖重複。

**LOD**：LOD1 約 50%、LOD2 約 15%（實際 13.9–14.1%），先丟 Detail 再減面。Detail_Small 在每一級都是獨立物件，關掉後房子外形不變。

**minTier**：三間都是 standard（會擋人的建築，所有畫質都看得到）。

**交付位置**
- FBX、GLB、貼圖、model_info.json、validation.json、qa：`art/exports/village-houses-b/<ID>/`；共用瓦片貼圖在 `VL_Shared/`。
- 預覽圖：`art/previews/village-houses-b/<ID>/`：十方位（`turnaround/`）、線框、LOD 對照、LOD0／LOD1 關掉 Detail 的對照、人形尺四向（灰模與材質各一）、灰模 vs 材質配對圖、主視覺。
- 可編輯 .blend：`art/source/village-houses-b/blend/<ID>_v001.blend`。
- 生成腳本：`vl_house.py`（三間共用的房子、破損與擺設）、`vl_roof.py`（瓦頂）、`vl_mats.py`（材質）、`vl_checks.py`（量測）；`build_village_houses_b.py` 負責建模、匯出和驗證；並排圖 `vl_compare.py`＋`vl_compare_sheet.py`。
- Unity 檢查：`apps/game/Assets/YunJing/Editor/VillageHousesModelCheck.cs`，輸出到 `artifacts/village-houses-unity/`（報告與 URP 截圖，本機，不提交）。

## 各件說明

三間的牆線、石基（0.54 m）、前廊（深 1.08 m）、三級 0.18 m 石階、屋簷下緣（3.345 m，前廊上淨高 2.805 m）、屋脊（5.271 m）和原點都和 StarterHouse v004 一樣，可以直接換進同一個位置。validation.json 逐項量過：牆面外緣 ±2.61／±3.61 m、台階頂 0.18／0.359／0.539 m。

### VL01 久無人住的空屋（三視圖 VL01 candidate-04）
- 門和五扇窗用舊木板釘成 X 再加一道橫板，釘頭下有鏽水痕；木板後面的窗紙破洞。
- 前坡兩處、後坡一處缺瓦，缺口看得到掛瓦條和一根椽子。
- 屋脊和簷口長草、瓦面長苔；灰泥一塊塊剝落，露出土磚。
- 前廊、門檻和台階上堆著落葉。

### VL02 剛有人住的空屋（三視圖 VL02 candidate-02）
- 新糊的白窗紙；前廊掃乾淨，掃起的落葉推到台階旁；門邊靠一支掃帚；右窗台一盆粉紅小花。
- 前坡兩處、後坡一處換了幾片顏色較淺的新瓦；舊灰泥上有較新的補灰。
- 玩家第一天分到的就是這種。

### VL03 半塌的空屋（三視圖 VL03 candidate-01）
- 右山牆一端的屋頂塌陷（後坡整片、前坡靠屋脊的上半），斷椽外露，兩根垂進屋內。
- 右牆往外倒成一堆土磚和碎瓦，只剩前角一段和低矮的牆根，從缺口看得到空屋內。
- 一棵小樹從屋內長出、穿過缺口；木頭發黑受潮，瓦和瓦礫長苔，瓦礫上長草。
- 碰撞：牆線照原屋封住（缺口處也擋），瓦礫堆另有一個斜面碰撞，人不會走進屋內，也不會卡在瓦礫裡。

## Unity 實測（編輯器批次檢查，失敗 0 項，59 項通過）

- 三間匯入後尺寸和 model_info 一致（誤差 0.0 mm），LODGroup 三級都有東西，四個材質槽都從 FBX 的槽名對上，沒有缺貼圖或錯誤 shader。
- 人在 x −0.6／0／0.6 三條線上走上三級台階到前廊（腳高 0.560 m），停在關著的門前。
- 從屋外推向後牆、左牆、右牆，人都停在牆外。
- VL03：在三條線上從屋外走上瓦礫堆，停在倒塌那面牆原本的牆線外（腳最高 0.824 m），再走下來回到地面。
- Unity 6000.0.85f1；只是編輯器批次檢查，沒有放進主場景，也沒有進遊戲。

## QA（匯出後的 FBX 重新匯入）

| ID | 同向共面 @1 mm | 浮空零件（> 1 cm） | 退化面 | 零面積 UV | UV 重疊（texel） | 背面紅色比例 | FBX 尺寸誤差 |
|---|---|---|---|---|---|---|---|
| VL01_LongEmptyHouse | 0 | 0／1,464 件 | 0 | 0 | 114 | 0.0086 | 0.04 mm |
| VL02_MovedInHouse | 0 | 0／635 件 | 0 | 0 | 120 | 0.0073 | 0.04 mm |
| VL03_HalfCollapsedHouse | 0 | 0／1,271 件 | 0 | 0 | 122 | 0.0081 | 0.04 mm |

- `two_sides`（薄片兩面）來自窗紙、草葉、苔片、樹葉，屬於預期。
- UV 重疊是三張圖集合計約 800 萬 texel 中的 114–122 個，最大一塊 2 texel，看不出來；瓦片貼圖刻意重複，不算。
- VL03 的可編輯 .blend 裡，倒塌牆角還有 4 個同向共面的細長面（在 x 3.46–3.54 m、y 2.4–2.6 m 斷口處），匯出的 FBX 在 1 mm 量測下為 0。

### 審圖後修改（照實記錄）
- 屋頂的草和苔原本落在 LOD1／LOD2 的屋頂副本上，LOD0 看起來浮起來；改成擺設只落在 LOD0 看得到的表面，並略過隱藏的碰撞網格。
- 屋簷草原本整叢一起移動，坡下那幾根葉子懸空；改成每根葉子各自落到瓦面。
- 落葉疊在落葉上時會互相閃爍、或角落懸空；改成每片葉子傾斜 2–5°、由下往上落、疊在別片上留 1.5 mm，並以「任一角先碰到」決定落點。
- 瓦面苔片貼到瓦上時原本被壓平；改成保留各叢原本的隆起，疊在一起的苔叢錯開 1.2 mm。
