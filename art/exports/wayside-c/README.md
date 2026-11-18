| 項目 | 內容 |
|---|---|
| 誰做的 | C（Eli-0731） |
| 工作包 | docs/execution/2026-11-14/C-120h-yards-undergrowth-and-wayside.md，C 批 |
| ID | WS01–WS06（10 個模型：WS01、WS02、WS04、WS05 各兩種） |
| 分支／PR | art/c-1114-ws01-06-wayside ／ 開 PR 後補 |
| 版本 | v001（檔名帶 `_v001`；之後改版另存 v002，不覆寫） |
| 狀態 | Exported ／ Imported（Unity 6000.3.28f1 獨立匯入檢查）／ Visually Verified（Blender 與 Unity 審圖）／ In-game Verified：未驗（沒放進正式場景） |
| 素材來源 | 原創；三視圖參考在 `art/references/WS01/`–`art/references/WS06/` |
| 實際工時 | 見下方「實際工時」 |

# 路邊小物 WS01–WS06

11/14 的 120 小時包 C 批：A2 村外官道路邊的小東西（A2 沒有設定圖，照區塊規劃 `docs/execution/blocks/A2-A3-block-plan.md` 寫物件句）；WS05 也給 A6 稻田用。靜態擺設，沒有玩法或動畫；擺進世界由核心組做，這裡不改主場景、不改區塊 JSON。

**共同做法**
- 先生成三視圖（每件 4 張，WS01、WS02 兩種各 4 張）、自評選一張（分數和取捨在各自的 `prompt.txt`），再做灰模（`art/previews/wayside-c/<ID>/clay/`），最後上貼圖。三視圖底下畫的石板地座都不做。
- 原點在腳印中心、底部 z = 0，Blender −Y 是正面（FBX／Unity 是 −Z）。不附地面底板（草和花腳下的薄土片是 Detail_）。
- 一件一個材質、一套 1024 貼圖（Albedo／Normal／ORM／MaskURP）；可有可無的小東西放 `Detail_*`（標準畫質關掉）。`minTier` 都是 `standard`。LOD1 約 50%、LOD2 約 15%。
- **沒有透明卡**：花瓣、葉片、草葉、稻草的毛邊都是做出來的形狀。薄的葉片和花瓣在 Unity 裡用雙面材質（檢查腳本有設）。
- **碰撞**：WS05_01 稻草堆、WS06 柴捆在 FBX 裡附一個盒子 `<ID>_Collision`（不顯示）；其餘可以跨過或穿過，模型裡沒有。
- 建模流程和 yard-props-c 相同（共用工具、來源貼圖和零件），`build_ws.py` 只換套件名、表格和物件檔；石頭的堆法照 ground-cover-c 的 GC06。
- 重建：`blender -b --factory-startup -P art/source/wayside-c/build_ws.py -- WS03 [--clay]`；審圖與 QA：`BL=<blender> sh art/source/wayside-c/render_reviews.sh`（並排：`CMP=1 … render_reviews.sh -`）；審圖表：`sh art/source/wayside-c/make_sheets.sh`；路邊擺設：`BL=<blender> sh art/source/wayside-c/render_road.sh`；Unity：`UNITY=<Unity.exe 6000.3.28f1> sh art/source/wayside-c/unity/run_unity_check.sh`。

### WS01_01 路邊野花叢（黃）（WildflowersYellow，v001）

一叢細莖從基部分枝，基部 12 片葉；22 根細莖上互生有深鋸齒的窄葉，往上變小；每根莖頂分出三、四枝花梗，開黃色小菊（13 片舌狀花瓣圍著金黃的圓頂花心，花瓣高低錯開、不在同一面），也有花苞和開過只剩褐色花托的。每片葉子和花瓣都是單獨一片，沒有葉片卡。低處葉子的路塵、部分葉子偏黃畫在貼圖上。腳下一小片乾土和兩顆小石是 Detail_Base。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/WS01/`，選用 cand-1（91，黃花） |
| 尺寸（寬 × 深 × 高） | 0.703 × 0.698 × 0.515 m（上限 0.75 × 0.75 × 0.65 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 16,236 / 8,116 / 2,433（不含 Detail_：15,586 / 7,792 / 2,337） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_Base） |
| 材質數 | 1（`M_WS01_01_WildflowersYellow`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 模型裡沒有 |
| 檔案 | `art/exports/wayside-c/WS01_01_v001.fbx`（LOD0–2）、`art/exports/wayside-c/WS01_01_v001.glb`（LOD0）、`art/source/wayside-c/WS01_01_v001.blend` |

### WS01_02 路邊野花叢（紫，夏枯草）（WildflowersPurple，v001）

14 根直立的方莖，卵形葉對生、每對轉 90°；莖頂一串短花穗（綠紫色的苞片），四圈紫色唇形小花伸出來，幾串開過變成褐色；基部 10 片葉攤在地上。每片葉子和小花都是單獨一片，沒有葉片卡。低處葉子的路塵畫在貼圖上。腳下一小片乾土和兩顆小石是 Detail_Base。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/WS01/`，選用 cand-3（91，紫花） |
| 尺寸（寬 × 深 × 高） | 0.479 × 0.43 × 0.376 m（上限 0.7 × 0.7 × 0.55 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 7,562 / 3,780 / 1,131（不含 Detail_：6,912 / 3,456 / 1,035） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_Base） |
| 材質數 | 1（`M_WS01_02_WildflowersPurple`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 模型裡沒有 |
| 檔案 | `art/exports/wayside-c/WS01_02_v001.fbx`（LOD0–2）、`art/exports/wayside-c/WS01_02_v001.glb`（LOD0）、`art/source/wayside-c/WS01_02_v001.blend` |

### WS02_01 乾草叢（高，乾芒草）（DryGrassTall，v001）

一叢約 1.1 m 高的乾芒草：70 片有中摺的長葉從密的基部拱出去，草黃到淺褐，裡面低處幾片還綠；六根細稈高出葉子，每根頂上 16 條絲狀小穗往外彎垂成羽毛狀的花穗。每片葉子都是單獨一片，沒有葉片卡；葉尖的下垂量有限制，不會穿進地面。腳下一小片乾土和四顆小石是 Detail_Base。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/WS02/`，選用 cand-4（91，高） |
| 尺寸（寬 × 深 × 高） | 1.274 × 1.3 × 1.124 m（上限 1.3 × 1.3 × 1.35 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 6,378 / 3,187 / 954（不含 Detail_：5,568 / 2,783 / 834） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_Base） |
| 材質數 | 1（`M_WS02_01_DryGrassTall`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 模型裡沒有 |
| 檔案 | `art/exports/wayside-c/WS02_01_v001.fbx`（LOD0–2）、`art/exports/wayside-c/WS02_01_v001.glb`（LOD0）、`art/source/wayside-c/WS02_01_v001.blend` |

### WS02_02 乾草叢（矮，枯草團）（DryGrassLow，v001）

低低一團約 0.25 m 高的枯草：90 片細葉往外拱、彎折、糾在一起，每四片有一片折斷：一小截立著，折斷的部分倒下來、尖端落到地上；裡面幾片還帶綠。每片葉子都是單獨一片，沒有葉片卡。腳下一小片乾土和三顆小石是 Detail_Base。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/WS02/`，選用 cand-1（91，矮） |
| 尺寸（寬 × 深 × 高） | 0.689 × 0.692 × 0.277 m（上限 0.85 × 0.85 × 0.42 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 3,786 / 1,891 / 566（不含 Detail_：3,056 / 1,527 / 458） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_Base） |
| 材質數 | 1（`M_WS02_02_DryGrassLow`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 模型裡沒有 |
| 檔案 | `art/exports/wayside-c/WS02_02_v001.fbx`（LOD0–2）、`art/exports/wayside-c/WS02_02_v001.glb`（LOD0）、`art/source/wayside-c/WS02_02_v001.blend` |

### WS03 路邊碎石堆（RoadsideStonePile，v001）

修路剩下的一小堆劈開的花崗岩：24 塊從頭大到拳頭大、有稜角的石頭，大的先放、小的一塊塊往下落，停在地面或已經放好的石頭上（不穿插、不浮空），每塊轉到沒有面和鄰居貼平為止（GC06 的做法）。腳邊散落的 70 粒碎石子是 Detail_Gravel，石縫裡 8 叢小草是 Detail_Weeds。朝上面的灰塵、低處的青苔和泥、幾處新的淺色斷口畫在貼圖上，小坑在法線圖裡。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/WS03/`，選用 cand-2（91） |
| 尺寸（寬 × 深 × 高） | 1.004 × 0.806 × 0.326 m（上限 1.4 × 1.1 × 0.45 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 10,882 / 5,440 / 1,630（不含 Detail_：9,268 / 4,634 / 1,390） |
| 物件數（每個 LOD） | 3（本體 1 + Detail_Gravel, Detail_Weeds） |
| 材質數 | 1（`M_WS03_RoadsideStonePile`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 模型裡沒有 |
| 檔案 | `art/exports/wayside-c/WS03_v001.fbx`（LOD0–2）、`art/exports/wayside-c/WS03_v001.glb`（LOD0）、`art/source/wayside-c/WS03_v001.blend` |

### WS04_01 疊石小塔（三塊）（CairnThree，v001）

三塊扁圓的河石由大到小疊起來，每塊往下落到下面那塊上，轉到接觸面不貼平；有一點偏、有一點歪，但每塊的重心都在下面那塊上。石頭有暖褐有偏灰，頂面灰塵、低處青苔畫在貼圖上。腳邊四叢小草是 Detail_Weeds。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/WS04/`，選用 cand-4（91） |
| 尺寸（寬 × 深 × 高） | 0.438 × 0.382 × 0.322 m（上限 0.45 × 0.45 × 0.45 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 4,144 / 2,072 / 621（不含 Detail_：3,840 / 1,920 / 576） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_Weeds） |
| 材質數 | 1（`M_WS04_01_CairnThree`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 模型裡沒有 |
| 檔案 | `art/exports/wayside-c/WS04_01_v001.fbx`（LOD0–2）、`art/exports/wayside-c/WS04_01_v001.glb`（LOD0）、`art/source/wayside-c/WS04_01_v001.blend` |

### WS04_02 疊石小塔（五塊）（CairnFive，v001）

和 WS04_01 同樣的做法，五塊石頭，往同一邊歪得比較多。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/WS04/`，選用 cand-4（91） |
| 尺寸（寬 × 深 × 高） | 0.382 × 0.389 × 0.499 m（上限 0.5 × 0.5 × 0.65 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 6,608 / 3,304 / 991（不含 Detail_：6,400 / 3,200 / 960） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_Weeds） |
| 材質數 | 1（`M_WS04_02_CairnFive`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 模型裡沒有 |
| 檔案 | `art/exports/wayside-c/WS04_02_v001.fbx`（LOD0–2）、`art/exports/wayside-c/WS04_02_v001.glb`（LOD0）、`art/source/wayside-c/WS04_02_v001.blend` |

### WS05_01 稻草堆（StrawHeap，v001）

一堆低低、歪一邊的打過穀的稻草，做法和 VG04 草垛相同：實心的芯外面罩四層草披，每層的下緣參差做在形狀上、各自歪一點、比下面那層往外幾公分（不會共面），每層下緣伸出一根根草稈（毛邊是做出來的，不是透明卡），頂上丟著一團亂草。插出來的 30 根散草稈是 Detail_Stalks。金黃和淋過雨的灰白稻草、近地面的潮濕畫在貼圖上。整堆在深度方向壓成 0.85 的橢圓。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/WS05/`，選用 cand-1（91） |
| 尺寸（寬 × 深 × 高） | 1.748 × 1.6 × 0.653 m（上限 1.9 × 1.6 × 0.95 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 4,288 / 2,144 / 641（不含 Detail_：3,868 / 1,934 / 579） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_Stalks） |
| 材質數 | 1（`M_WS05_01_StrawHeap`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | `WS05_01_Collision`：一個盒子 1.063 × 0.869 × 0.435 m（只在 FBX 和 .blend 裡，不顯示） |
| 檔案 | `art/exports/wayside-c/WS05_01_v001.fbx`（LOD0–2）、`art/exports/wayside-c/WS05_01_v001.glb`（LOD0）、`art/source/wayside-c/WS05_01_v001.blend` |

### WS05_02 稻束（三束）（RiceSheaves，v001）

三束立著曬的稻草排成一排：每束 64 根稻草從腳下一圈經過綁緊的腰部到頂，每根在束裡的位置（腳、腰、頂的半徑）成比例，所以不會互相交叉；腰上兩圈草繩；頂上的穗頭往外垂。腳下比較暗、部分稻草灰白，畫在貼圖上。A6 稻田也可以一束束沿田埂擺。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/WS05/`，選用 cand-1（91） |
| 尺寸（寬 × 深 × 高） | 1.18 × 0.479 × 0.959 m（上限 1.2 × 0.8 × 1.0 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 9,988 / 4,994 / 1,498（不含 Detail_：9,988 / 4,994 / 1,498） |
| 物件數（每個 LOD） | 1（本體 1 + 無） |
| 材質數 | 1（`M_WS05_02_RiceSheaves`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 模型裡沒有 |
| 檔案 | `art/exports/wayside-c/WS05_02_v001.fbx`（LOD0–2）、`art/exports/wayside-c/WS05_02_v001.glb`（LOD0）、`art/source/wayside-c/WS05_02_v001.blend` |

### WS06 柴捆（FirewoodBundles，v001）

兩捆柴一捆躺在另一捆的凹處：28 根和 25 根粗細不同的樹枝在圓形截面裡排緊，彼此只差 0.4 mm（不穿插、也不會一根懸在中間），每捆整體微彎、每根長短不同，粗的約五分之一是三角形截面的劈柴；捆的兩端伸出分叉的細枝；每捆兩道三股扭成的草繩勒進外圈的枝條，留一小段繩頭。淺色的鋸口和年輪（也在法線圖裡）、灰白和褐色混雜的樹皮、一點地衣畫在貼圖上。地上 6 根散落的細枝是 Detail_Twigs。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/WS06/`，選用 cand-4（91） |
| 尺寸（寬 × 深 × 高） | 1.209 × 0.757 × 0.55 m（上限 1.3 × 0.95 × 0.6 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 12,996 / 6,498 / 1,948（不含 Detail_：12,780 / 6,390 / 1,916） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_Twigs） |
| 材質數 | 1（`M_WS06_FirewoodBundles`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | `WS06_Collision`：一個盒子 0.98 × 0.26 × 0.47 m（只在 FBX 和 .blend 裡，不顯示） |
| 檔案 | `art/exports/wayside-c/WS06_v001.fbx`（LOD0–2）、`art/exports/wayside-c/WS06_v001.glb`（LOD0）、`art/source/wayside-c/WS06_v001.blend` |

## 驗證

- QA（`tools/art/qa_lod0_basic.py` 嚴格與寬鬆、`tools/art/qa_contact_glb.py`）：10 個模型嚴格、寬鬆都是 0 項。接觸檢查最大 4.2 mm（WS06 上面那捆中間一根柴，被外圈擋住看不到），其次 WS01_01 3.0 mm、WS02_02 2.9 mm，其餘 1 mm 以內。結果在 `art/previews/wayside-c/qa/`。
- 寬鬆 QA 的重疊在花、草、柴捆、稻草堆上用亂數種子挑掉（`WS_SEED`：WS01_01 9102、WS01_02 9155、WS02_02 9254、WS05_01 9505、WS06 9604，其餘用預設值），都寫在原始碼裡，重建一樣。
- Unity 6000.3.28f1 獨立匯入：`art/previews/wayside-c/unity/report.txt`（10 個模型 144 項全過）。檢查內容：匯入尺寸和 model_info 差 2 cm 內、在上限內、底部在地面、每個 LOD 的三角面和物件數、一個材質、貼圖 1024、`minTier = standard`、Detail_ 關掉後本體還在、WS05_01 和 WS06 各有一個碰撞盒而其餘沒有、花和草的材質是雙面。
- 每件的審圖在 `art/previews/wayside-c/<ID>/`：灰模（`clay/`）、四個方向加 1.75 m 人形尺、近看、線框、LOD0／LOD1／LOD2（不含 Detail_）；`<ID>-sheet.jpg` 把選用的三視圖和這些排在同一張。
- 同光同角度並排（含 1.75 m 人形尺，灰模和成品各一張）：`art/previews/wayside-c/compare/`。WS01、WS02 對 C 的溪邊水草和小花 YP13；WS03、WS04 對 C 的落石堆 GC06 和醃菜甕 LV05；WS05 對 C 的草垛 VG04_01；WS06 對 C 的扁擔水桶 YP11；`WS-all` 是 10 個模型加 LV05。
- 路邊擺設（工作包「全包檢查」）：`compare/WS-road-eye-cam.png`（站在路上、眼高 1.6 m 往前看）和 `WS-road-top-cam.png`（俯視配置）。路是 B 的林間土路直段 FP01_PathStraight 接兩段（12 m）。Unity 裡同樣的擺設（沒有路）：`unity/WS-road-eye.png`。

## 實際工時

台灣時間：2026-11-18 14:40–17:55，約 3 小時 15 分（工作包估 16 小時）。內容：讀 A2 區塊規劃、8 組三視圖（32 張）、10 個模型、QA 和種子挑選、審圖、並排、路邊擺設、Unity 檢查、README。等三視圖生成和渲染的時間沒有扣掉。

## 已知問題與未驗

- 正式場景擺放、手機上的效果都未驗。
- A2 沒有設定圖，路邊擺設圖只是配置和比例的檢查；路用的是 B 的林間土路（FP01），不是 A2 規劃裡的石板官道，地面是平的單色。
- 三視圖底下都畫了一塊石板地座，全部沒有做（和其他道具一樣不附地面底板）。
- WS02_01 乾芒草寬 1.27 m，比三視圖寫的 0.9 m 寬：外圈的葉子拱得比較開。花穗是一條條細的小穗，近看比三視圖的羽毛狀花穗稀。
- WS05_01 稻草堆：試過用一根根稻草稈鋪滿，QA 的共面檢查過不了，改成和 VG04 草垛一樣的「草披＋下緣伸出的草稈」，所以看起來比三視圖整齊、層次分明，不像一堆亂草；寬 1.75 m，比三視圖的 1.4 m 大。頂上那團亂草是一塊不規則的塊體。
- WS05_02 稻束一束 64 根稻草，比三視圖稀，看得到裡面。
- WS06：柴捆的中間一根和鄰居差 4.2 mm（接觸檢查最大值），從外面看不到。枝條是直的、整捆一起微彎，沒有彎曲的枝。
- WS03 碎石堆的石頭是凸包加稜，近看面數低、稜角明顯。
- 重跑路邊擺設和並排前，要先 `git lfs pull` B 的 FP01_PathStraight GLB。
