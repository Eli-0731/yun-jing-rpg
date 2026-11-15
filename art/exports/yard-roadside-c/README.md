| 項目 | 內容 |
|---|---|
| 誰做的 | C（Eli-0731） |
| 工作包 | docs/execution/2026-11-11/C-36h-yard-and-roadside-props.md |
| ID | VG01–VG04（VG04 是兩種：VG04_01、VG04_02） |
| 分支／PR | 批 A（VG01–VG04）：art/c-1111-vg-yard-props；批 B（VG05–VG08）：art/c-1111-vg-roadside-props ／ 開 PR 後補（一次一張，等前一張結案） |
| 版本 | v001（檔名帶 `_v001`；之後改版另存 v002，不覆寫） |
| 狀態 | Exported ／ Imported（Unity 6000.3.28f1 獨立匯入檢查）／ Visually Verified（Blender 與 Unity 審圖）／ In-game Verified：未驗（沒放進正式場景） |
| 素材來源 | 原創；三視圖參考在 `art/references/VG01/`–`art/references/VG08/` |

# 院子和路邊的東西 VG01–VG04

11/11 的 36 小時包：青溪村院子裡和路邊比較大件的東西，遠遠就看得到。靜態擺設，沒有玩法或動畫；擺進世界由核心組做，這裡不改主場景、不改區塊 JSON。

**共同做法**
- 先生成三視圖（每件 4 張）、自評選一張（分數和取捨在各自的 `prompt.txt`），再做灰模（`art/previews/yard-roadside-c/<ID>/clay/`），最後上貼圖。
- 原點在腳印中心、底部 z = 0，Blender −Y 是正面（FBX／Unity 是 −Z）。不附地面底板。
- 一件一個材質、一套 1024 貼圖；可有可無的小東西放 `Detail_*`（標準畫質關掉）。`minTier` 都是 `standard`（工作包第 3.5 點）。
- LOD1 約 50%、LOD2 約 15%，LOD0 不減面。
- **alpha clip（VG02 藤葉和花、VG03 下襬毛邊、VG04 草邊）**：面片的圖畫在圖集頂端的一條裡（Albedo 的 alpha），材質用 alpha clip 0.5、雙面；Unity 匯入 Albedo 時打開「Mip Maps Preserve Coverage」（檢查腳本有設並有檢查）。灰模圖上這些面片是沒裁的方片。
- **碰撞**：工作包要簡單碰撞的（VG01、VG05、VG07、VG08）在 FBX 裡附一個盒子 `<ID>_Collision`（不顯示）；其餘模型裡沒有碰撞。
- 建模流程和 village-life-c、creekside-life-c 相同，共用那裡的工具和來源貼圖；這裡放 VG 自己的物件（`vg_items.py`）和建模腳本（`build_vg.py`）。
- 重建：`blender -b --factory-startup -P art/source/yard-roadside-c/build_vg.py -- VG01 [--clay]`；審圖與 QA：`BL=<blender> sh art/source/yard-roadside-c/render_reviews.sh`；Unity：`UNITY=<Unity.exe 6000.3.28f1> sh art/source/yard-roadside-c/unity/run_unity_check.sh`。

### VG01 菜畦一組（三條土壟：青菜、蘿蔔、蔥）（VegetableBeds，v001）

練「重複排列但每棵略不同；土壟的起伏」。三條壟是同一塊土：壟頂圓、壟間是踩實的淺溝，四周參差地斜到地面，輪廓是圓角、邊緣略有進出，不做圍欄和石牆。每種菜是一個做法（葉數、大小、仰角、朝向是參數），沿壟排成兩行、每棵的參數各自隨機，不是一棵棵手擺：青菜 12 棵（一圈寬葉加淺色菜梗）、蘿蔔 12 棵（露出土面的白肩加羽狀裂葉）、蔥 18 叢（直立的細管葉，少數葉尖折下）。溝和邊緣的土較乾較淺、壟頂較濕較深，畫在貼圖上。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/VG01/`，選用 cand-3（92） |
| 尺寸（寬 × 深 × 高） | 2.859 × 1.941 × 0.336 m（上限 3 × 2 × 0.4 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 17,054 / 8,527 / 2,558（不含 Detail_：16,294 / 8,147 / 2,444） |
| 物件數（每個 LOD） | 3（本體 1 + Detail_Stones, Detail_Weeds） |
| 材質數 | 1（`M_VG01_VegetableBeds`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | `VG01_Collision`：一個盒子 2.6 × 1.7 × 0.17 m（只在 FBX 和 .blend 裡，不顯示） |
| 檔案 | `art/exports/yard-roadside-c/VG01_v001.fbx`（LOD0–2）、`art/exports/yard-roadside-c/VG01_v001.glb`（LOD0）、`art/source/yard-roadside-c/VG01_v001.blend` |

### VG02 瓜架（竹架上爬著葫蘆藤，吊三顆葫蘆）（GourdTrellis，v001）

練「細竹竿的綁接；藤和葉用帶透明貼圖的面片」。四根立柱插在地上，頂上兩根長樑、兩根橫樑、五根細椽、三根細竹條，每根柱一根斜撐、兩端各兩根橫檔；竹竿都有凸起的竹節，每個交叉點用繩在兩條對角線上各繞一圈（沒有釘子）。藤是實體的細管，沿兩根柱盤上去、在頂上蜿蜒；三顆葫蘆（大、中、小）是實體，各用一段藤柄吊在椽下。葉（三種）和四朵黃花是面片，畫在圖集頂端 22% 的一條裡，alpha clip。柱腳的潮濕和青苔在貼圖上。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/VG02/`，選用 cand-4（93） |
| 尺寸（寬 × 深 × 高） | 2.165 × 1.447 × 2.016 m（上限 2.4 × 1.6 × 2.1 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 18,116 / 9,058 / 2,716（不含 Detail_：18,116 / 9,058 / 2,716） |
| 物件數（每個 LOD） | 1（本體 1 + 無） |
| 材質數 | 1（`M_VG02_GourdTrellis`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 模型裡沒有 |
| 檔案 | `art/exports/yard-roadside-c/VG02_v001.fbx`（LOD0–2）、`art/exports/yard-roadside-c/VG02_v001.glb`（LOD0）、`art/source/yard-roadside-c/VG02_v001.blend` |

### VG03 晾衣竿（兩根叉竿、一根橫竿、晾著兩件布衣）（ClothesPole，v001）

練「布掛著往下垂的形狀」。兩根略彎的原木柱插在地上，頂端分成兩叉，竹竿架在叉口、用繩綁住。上衣是衣身和兩隻袖子各一片搭在竿上（袖子穿在竿上張開的樣子），褲子是兩條褲管對折搭在竿上、前面垂下。布有 4.5 mm 厚，垂下的直褶越往下襬越深、下襬有起伏、兩側略低，都做在形狀上；布壓在竹竿頂上。下襬的毛邊和線頭是 alpha clip 面片（圖集頂端 10%）。領條、兩塊補丁和下襬的髒污畫在貼圖上。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/VG03/`，選用 cand-4（93） |
| 尺寸（寬 × 深 × 高） | 2.54 × 0.297 × 1.832 m（上限 2.6 × 0.6 × 1.9 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 7,264 / 3,632 / 1,088（不含 Detail_：7,264 / 3,632 / 1,088） |
| 物件數（每個 LOD） | 1（本體 1 + 無） |
| 材質數 | 1（`M_VG03_ClothesPole`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 模型裡沒有 |
| 檔案 | `art/exports/yard-roadside-c/VG03_v001.fbx`（LOD0–2）、`art/exports/yard-roadside-c/VG03_v001.glb`（LOD0）、`art/source/yard-roadside-c/VG03_v001.blend` |

### VG04_01 草垛（圓頂、完整）（Haystack，v001）

練「大塊的軟輪廓；邊緣要毛，不要像一顆光滑的饅頭」。略歪的圓頂：一個實心的芯外面披六層稻草，每層略歪、高低不齊，下緣的參差做在形狀上，上緣塞進上一層底下；每層下緣掛一圈散開的草絲（alpha clip 面片，圖集頂端 12%）。頂上一頂小草帽綁在中心木桿上，木桿露出一截。下層較灰較濕、頂部較亮，畫在貼圖上。伸出來的零星草稈是 Detail_。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/VG04/`，選用 cand-3（91） |
| 尺寸（寬 × 深 × 高） | 2.028 × 2.09 × 2.336 m（上限 2.2 × 2.2 × 2.4 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 4,398 / 2,199 / 658（不含 Detail_：3,894 / 1,947 / 584） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_Stalks） |
| 材質數 | 1（`M_VG04_01_Haystack`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 模型裡沒有 |
| 檔案 | `art/exports/yard-roadside-c/VG04_01_v001.fbx`（LOD0–2）、`art/exports/yard-roadside-c/VG04_01_v001.glb`（LOD0）、`art/source/yard-roadside-c/VG04_01_v001.blend` |

### VG04_02 草垛（一側被抽掉一角）（HaystackPulled，v001）

和 VG04_01 同樣的做法，另一個亂數；一側下半（高 1.2 m 以下、約 90° 寬）被抽走，凹口往裡收，露出五捆橫放的草把（每捆中間一道草繩），凹口前的地上一小堆散草和幾根草稈。四張三視圖都把「抽掉一角」畫成綁起來的門簾，這裡照工作包的文字做成凹口。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/VG04/`，選用 cand-3（91） |
| 尺寸（寬 × 深 × 高） | 2.152 × 1.967 × 2.348 m（上限 2.2 × 2.2 × 2.4 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 6,190 / 3,095 / 927（不含 Detail_：5,574 / 2,787 / 835） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_Stalks） |
| 材質數 | 1（`M_VG04_02_HaystackPulled`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 模型裡沒有 |
| 檔案 | `art/exports/yard-roadside-c/VG04_02_v001.fbx`（LOD0–2）、`art/exports/yard-roadside-c/VG04_02_v001.glb`（LOD0）、`art/source/yard-roadside-c/VG04_02_v001.blend` |

## 驗證

- QA（`tools/art/qa_lod0_basic.py` 嚴格與寬鬆、`tools/art/qa_contact_glb.py`）：VG01、VG02、VG03、VG04_01、VG04_02 嚴格、寬鬆都是 0 項；接觸檢查本體都是 0 mm，結果在 `art/previews/yard-roadside-c/qa/`。
- Unity 6000.3.28f1 獨立匯入：`art/previews/yard-roadside-c/unity/report.txt`（批 A 五個模型 81 項全過）。檢查內容：匯入尺寸和 model_info 差 2 cm 內、在工作包上限內、底部在地面、每個 LOD 的三角面和物件數、一個材質、貼圖 1024、`minTier = standard`、Detail_ 關掉後本體還在、VG01 有一個碰撞盒而其餘沒有、alpha clip 的三件 Albedo 有 alpha 且 Mip Maps Preserve Coverage 打開。
- 每件的審圖在 `art/previews/yard-roadside-c/<ID>/`：灰模（`clay/`）、四個方向加 1.75 m 人形尺、近看、線框、LOD0／LOD1／LOD2（不含 Detail_）。
- 同光同角度並排（含 1.75 m 人形尺，灰模和成品各一張）：`art/previews/yard-roadside-c/compare/`。VG01 對 C 的蕨 BM09_02、落葉貼片 BM10_02 和醃菜甕 LV05；VG02、VG03 對 C 的竹梯 LV03 和蓑衣架 LV08；VG04 對 B 的柴堆 R03 和 C 的稻草蛋籃 LV12；`VG-setA` 是批 A 五個放在一起加 LV05。Unity 裡的並排是 `unity/VG-set-*.png`。

## 已知問題與未驗

- 正式場景擺放、手機上的效果都未驗。
- VG01：菜葉是單面的薄片（材質雙面）；菜的種類只有三種做法，近看同一種的葉形相同、只有大小和角度不同。
- VG02：葉片是 2 × 2 格的面片，LOD2 減面後葉子變少；葫蘆的顏色是還在長的淺綠，不是曬乾的褐色。
- VG03：上衣是三片布搭在竿上拼成的（衣身、兩袖），不是一件縫好的衣服，從背面看得出來；領條和補丁是畫的。
- VG04：草披的稻草紋路是貼圖，草絲只有下緣那一圈是面片；VG04_02 的凹口照工作包文字做，和三視圖畫的門簾不同。VG04_02 有幾根地上的散草（Detail_）離地 2.7 mm。
- 灰模圖上 alpha clip 的面片是沒裁的方片（裁切在貼圖的 alpha）。
- VG05–VG08（批 B）還沒做。
