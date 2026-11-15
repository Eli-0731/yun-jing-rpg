
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
