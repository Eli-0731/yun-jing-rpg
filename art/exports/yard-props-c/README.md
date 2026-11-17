| 項目 | 內容 |
|---|---|
| 誰做的 | C（Eli-0731） |
| 工作包 | docs/execution/2026-11-14/C-120h-yards-undergrowth-and-wayside.md，A 批 |
| ID | YP01–YP13（23 個模型：YP01 是土加三種作物排 YP01_01–_04，YP05、YP09 各兩種，YP06、YP07 各三種，YP13 兩種） |
| 分支／PR | art/c-1114-yp01-13-yard-props ／ 開 PR 後補 |
| 版本 | v001（檔名帶 `_v001`；之後改版另存 v002，不覆寫） |
| 狀態 | Exported ／ Imported（Unity 6000.3.28f1 獨立匯入檢查）／ Visually Verified（Blender 與 Unity 審圖）／ In-game Verified：未驗（沒放進正式場景） |
| 素材來源 | 原創；三視圖參考在 `art/references/YP01/`–`art/references/YP13/` |
| 實際工時 | 見下方「實際工時」 |

# 院子小物 YP01–YP13

11/14 的 120 小時包 A 批：A1 青溪村院子裡的小東西，對著設定圖 V6（東南巷子、眼高 1.0 m）；YP13 給 A1 溪邊（V5）。靜態擺設，沒有玩法或動畫；擺進世界由核心組做，這裡不改主場景、不改區塊 JSON。

**共同做法**
- 先生成三視圖（每件 4 張，YP13 水草和小花各 4 張）、自評選一張（分數和取捨在各自的 `prompt.txt`），再做灰模（`art/previews/yard-props-c/<ID>/clay/`），最後上貼圖。
- 原點在腳印中心、底部 z = 0，Blender −Y 是正面（FBX／Unity 是 −Z）。不附地面底板（YP13 的薄土片是 Detail_）。
- 一件一個材質、一套 1024 貼圖（Albedo／Normal／ORM／MaskURP）；可有可無的小東西放 `Detail_*`（標準畫質關掉）。`minTier` 都是 `standard`。
- LOD1 約 50%、LOD2 約 15%，LOD0 不減面。
- **沒有透明卡**：菜葉、蔥、豆葉、香草、水草、花瓣、布的下襬都是做出來的形狀，不用 alpha clip。薄的葉片和花瓣在 Unity 裡用雙面材質（檢查腳本有設）。
- **細節做在形狀上，再畫在貼圖上**：大的缺角、裂開、補板、繩結是網格；小的裂紋、鑿痕、補丁縫線、編織紋畫在貼圖上，凹凸同時烘進法線圖。
- **碰撞**：會擋路的東西在 FBX 裡附一個盒子 `<ID>_Collision`（不顯示），見各件的表；草蓆攤平、作物排、掛串、扁擔水桶、水草和小花沒有。
- **YP01 菜圃可以換作物**：YP01_01 是土，YP01_02（白菜）、_03（蔥）、_04（豆苗竹架）各是一條壟長的一排，放在壟中線 x = −0.62、0、+0.62 m 上（原點在地面），任一種作物可以放任一條壟。
- 建模流程和 yard-roadside-c、village-life-c 相同，共用那裡的工具和來源貼圖；這裡放 YP 自己的物件（`yp_items*.py`）、來源貼圖補充（`yp_sources.py`）和建模腳本（`build_yp.py`）。
- 重建：`blender -b --factory-startup -P art/source/yard-props-c/build_yp.py -- YP10 [--clay]`；審圖與 QA：`BL=<blender> sh art/source/yard-props-c/render_reviews.sh`（並排：`CMP=1 … render_reviews.sh -`）；院子擺設：`BL=<blender> sh art/source/yard-props-c/render_yard.sh`；Unity：`UNITY=<Unity.exe 6000.3.28f1> sh art/source/yard-props-c/unity/run_unity_check.sh`。

### YP01_01 菜圃的土（三條空壟）（VegBedEarth，v001）

2 × 3 m 的一塊土，沿長邊三條圓頂的壟（中線在 x = −0.62、0、+0.62 m），壟溝踩實，四周參差地斜到地面。壟上沒有作物：作物是另外三個模型，可以任意放到任一條壟上。土塊、幾顆小石子、壟溝裡的腳印畫在貼圖上，凹凸也在法線圖裡。土邊 9 顆小石（Detail_Stones）、14 叢雜草（Detail_Weeds）。碰撞盒蓋整塊土。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/YP01/`，選用 cand-4（91） |
| 尺寸（寬 × 深 × 高） | 2.033 × 3.071 × 0.174 m（上限 2.1 × 3.1 × 0.25 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 9,830 / 4,914 / 1,474（不含 Detail_：8,830 / 4,414 / 1,324） |
| 物件數（每個 LOD） | 3（本體 1 + Detail_Stones, Detail_Weeds） |
| 材質數 | 1（`M_YP01_01_VegBedEarth`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | `YP01_01_Collision`：一個盒子 1.84 × 2.84 × 0.16 m（只在 FBX 和 .blend 裡，不顯示） |
| 檔案 | `art/exports/yard-props-c/YP01_01_v001.fbx`（LOD0–2）、`art/exports/yard-props-c/YP01_01_v001.glb`（LOD0）、`art/source/yard-props-c/YP01_01_v001.blend` |

### YP01_02 一排白菜（6 棵）（RowCabbage，v001）

放在 YP01_01 一條壟上的一排作物：原點在壟中線下的地面，自帶一條培高的土，蓋住原本的空壟。六棵包心白菜：淡色的菜心、五片包住菜心的內葉、七片攤開的外葉；每片葉子都是有厚白梗、邊緣起皺的碗形葉片，沒有葉片卡。內葉較淡，外葉有蟲咬和濺上的泥，畫在貼圖上。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/YP01/`，選用 cand-4（91） |
| 尺寸（寬 × 深 × 高） | 0.796 × 2.599 × 0.422 m（上限 0.95 × 2.8 × 0.55 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 8,050 / 4,025 / 1,206（不含 Detail_：8,050 / 4,025 / 1,206） |
| 物件數（每個 LOD） | 1（本體 1 + 無） |
| 材質數 | 1（`M_YP01_02_RowCabbage`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 模型裡沒有 |
| 檔案 | `art/exports/yard-props-c/YP01_02_v001.fbx`（LOD0–2）、`art/exports/yard-props-c/YP01_02_v001.glb`（LOD0）、`art/source/yard-props-c/YP01_02_v001.blend` |

### YP01_03 一排蔥（11 叢）（RowScallion，v001）

和 YP01_02 一樣放在壟上、自帶培土。十一叢蔥，每根葉子是從淡色葉鞘長出的五邊形細管，大約五根有一根折下來；沒有葉片卡。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/YP01/`，選用 cand-4（91） |
| 尺寸（寬 × 深 × 高） | 0.668 × 2.596 × 0.681 m（上限 0.95 × 2.8 × 0.75 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 7,762 / 3,880 / 1,164（不含 Detail_：7,762 / 3,880 / 1,164） |
| 物件數（每個 LOD） | 1（本體 1 + 無） |
| 材質數 | 1（`M_YP01_03_RowScallion`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 模型裡沒有 |
| 檔案 | `art/exports/yard-props-c/YP01_03_v001.fbx`（LOD0–2）、`art/exports/yard-props-c/YP01_03_v001.glb`（LOD0）、`art/source/yard-props-c/YP01_03_v001.blend` |

### YP01_04 一排豆苗和人字竹架（RowBeanFrame，v001）

和 YP01_02 一樣放在壟上、自帶培土。竹架：三對竹竿在壟上交叉綁住，交叉處放一根頂竿，兩側半高各一根橫竿。六條豆藤繞著竹竿往上爬（每條是繞竿的細管），三片小葉一組的葉子有短柄，幾條垂下的豆莢，每個藤尖有捲鬚；每片小葉都是單獨的葉片，沒有葉片卡。竹竿灰白、有乾裂和深色的竿腳，部分葉子偏黃，畫在貼圖上。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/YP01/`，選用 cand-4（91） |
| 尺寸（寬 × 深 × 高） | 0.725 × 2.594 × 1.465 m（上限 0.95 × 2.8 × 1.65 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 21,010 / 10,504 / 3,151（不含 Detail_：21,010 / 10,504 / 3,151） |
| 物件數（每個 LOD） | 1（本體 1 + 無） |
| 材質數 | 1（`M_YP01_04_RowBeanFrame`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 模型裡沒有 |
| 檔案 | `art/exports/yard-props-c/YP01_04_v001.fbx`（LOD0–2）、`art/exports/yard-props-c/YP01_04_v001.glb`（LOD0）、`art/source/yard-props-c/YP01_04_v001.blend` |

### YP02 晾衣繩和三件布（WashingLine，v001）

兩根竹竿插在地上，頂上一根橫竹用麻繩十字綁住（工作包寫兩根竹竿一條繩，橫竹是照三視圖加的）。麻繩在兩根竿上各繞三圈、留一段垂下的繩頭，中間下垂 17 cm。繩上搭著一件米白布衫（衣身和兩隻袖子）、一塊褪色藍布、一條藍條紋布巾：每件都是有厚度、搭在繩上的布片，摺痕往下襬變深，下襬高低不齊、有破口，都做在形狀上，沒有透明卡。布衫的前襟和四顆布扣、三塊補丁、布巾的條紋、曬白的地方、竿腳的濕綠、竹竿的乾裂畫在貼圖上。竿腳 8 顆小石（Detail_Stones）、10 叢草（Detail_Weeds）。碰撞盒只蓋左邊竹竿，右邊竹竿要在 +1.05 m 放一個同樣的盒子；繩子和布沒有碰撞。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/YP02/`，選用 cand-4（91） |
| 尺寸（寬 × 深 × 高） | 2.501 × 0.349 × 1.995 m（上限 2.7 × 0.5 × 2.1 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 9,824 / 4,912 / 1,472（不含 Detail_：8,544 / 4,272 / 1,280） |
| 物件數（每個 LOD） | 3（本體 1 + Detail_Stones, Detail_Weeds） |
| 材質數 | 1（`M_YP02_WashingLine`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | `YP02_Collision`：一個盒子 0.12 × 0.12 × 1.95 m（只在 FBX 和 .blend 裡，不顯示） |
| 檔案 | `art/exports/yard-props-c/YP02_v001.fbx`（LOD0–2）、`art/exports/yard-props-c/YP02_v001.glb`（LOD0）、`art/source/yard-props-c/YP02_v001.blend` |

### YP03 木水桶和木杓（WaterBucketLadle，v001）

十四片桶板（頂端高低不齊，有的缺角或磨短），兩道鐵箍各有十顆鉚釘（Detail_Rivets）和一個搭接口，桶底板嵌在桶板裡。相對的兩片桶板伸出桶口、鑽孔，麻繩提把穿過去在外側打結。桶裡的水面在桶口下 4 cm；木杓（車出來的杓頭、長柄）橫放在桶口上。一片桶板用小木板釘補。桶板的裂紋、桶口往下的裂縫、生鏽的鐵箍和鏽水痕、曬灰的地方、桶內的濕痕、桶腳的潮濕和青苔畫在貼圖上。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/YP03/`，選用 cand-4（92） |
| 尺寸（寬 × 深 × 高） | 0.488 × 0.357 × 0.471 m（上限 0.5 × 0.5 × 0.5 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 4,058 / 2,028 / 608（不含 Detail_：3,578 / 1,788 / 536） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_Rivets） |
| 材質數 | 1（`M_YP03_WaterBucketLadle`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 模型裡沒有 |
| 檔案 | `art/exports/yard-props-c/YP03_v001.fbx`（LOD0–2）、`art/exports/yard-props-c/YP03_v001.glb`（LOD0）、`art/source/yard-props-c/YP03_v001.blend` |

### YP04 石臼和木杵（StoneMortarPestle，v001）

一整塊鑿出來的石頭：外面是不平的鼓起和寬的鑿面（做在形狀上），腰略收、有一圈底座；臼口不平，有四處缺口；臼內深、圓、光滑；正面從臼口往下一道裂縫。木杵斜靠在臼裡：圓頭、握處繞四圈繩、頂上一個圓頭；臼裡一小堆穀子。三視圖上的石頭補片和鐵扒釘沒有做（裂開的石臼不會這樣補）。鑿點和小坑、裂縫往下的延續、雨水痕、淺色地衣、磨光的臼內、臼口的粉、腳邊的青苔和泥畫在貼圖上。碰撞盒只蓋石臼。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/YP04/`，選用 cand-3（91） |
| 尺寸（寬 × 深 × 高） | 0.494 × 0.436 × 0.708 m（上限 0.6 × 0.6 × 0.75 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 3,262 / 1,630 / 488（不含 Detail_：3,262 / 1,630 / 488） |
| 物件數（每個 LOD） | 1（本體 1 + 無） |
| 材質數 | 1（`M_YP04_StoneMortarPestle`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | `YP04_Collision`：一個盒子 0.43 × 0.43 × 0.45 m（只在 FBX 和 .blend 裡，不顯示） |
| 檔案 | `art/exports/yard-props-c/YP04_v001.fbx`（LOD0–2）、`art/exports/yard-props-c/YP04_v001.glb`（LOD0）、`art/source/yard-props-c/YP04_v001.blend` |

### YP05_01 木長凳（長）（BenchLong，v001）

一塊厚木板當凳面，中間微凹（做在形狀上）、邊不直；四隻腳往兩端和前後外撇，榫頭穿出凳面、鋸平後凸出 4 mm。兩端各一根短橫檔、前後各一根長橫檔，榫頭穿過凳腳、用楔子卡住（Detail_Keys）。凳面前緣釘了一塊補板，一端順紋裂開、繞了四圈繩。木紋裂、節疤、淺淺的錛痕、曬灰的地方、凳面中間坐得發亮、凳腳的泥和青苔畫在貼圖上。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/YP05/`，選用 cand-4（92） |
| 尺寸（寬 × 深 × 高） | 1.503 × 0.389 × 0.464 m（上限 1.6 × 0.4 × 0.5 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 2,016 / 1,008 / 300（不含 Detail_：1,624 / 812 / 242） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_Keys） |
| 材質數 | 1（`M_YP05_01_BenchLong`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | `YP05_01_Collision`：一個盒子 1.5 × 0.3 × 0.45 m（只在 FBX 和 .blend 裡，不顯示） |
| 檔案 | `art/exports/yard-props-c/YP05_01_v001.fbx`（LOD0–2）、`art/exports/yard-props-c/YP05_01_v001.glb`（LOD0）、`art/source/yard-props-c/YP05_01_v001.blend` |

### YP05_02 木長凳（短）（BenchShort，v001）

和 YP05_01 同樣的做法，短的一張：凳面一端繞了四圈繩，沒有補板。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/YP05/`，選用 cand-4（92） |
| 尺寸（寬 × 深 × 高） | 0.627 × 0.389 × 0.461 m（上限 0.7 × 0.4 × 0.5 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 1,908 / 954 / 284（不含 Detail_：1,556 / 778 / 232） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_Keys） |
| 材質數 | 1（`M_YP05_02_BenchShort`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | `YP05_02_Collision`：一個盒子 0.62 × 0.3 × 0.45 m（只在 FBX 和 .blend 裡，不顯示） |
| 檔案 | `art/exports/yard-props-c/YP05_02_v001.fbx`（LOD0–2）、`art/exports/yard-props-c/YP05_02_v001.glb`（LOD0）、`art/source/yard-props-c/YP05_02_v001.blend` |

### YP06_01 草蓆（攤平）（RushMatFlat，v001）

一張平鋪在地上的草蓆，厚 1 cm：低低的起伏、一道斜斜的皺、一角翹起都做在形狀上；四周 156 根散出來的草頭。一塊縫上去的布補丁，20 針縫線（Detail_Stitches）。編織紋在貼圖和法線圖上；一處破口和毛邊、灰白的舊色、髒污、邊緣一點青苔、中間被踩得發白畫在貼圖上。沒有碰撞（人會走過去）。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/YP06/`，選用 cand-4（92） |
| 尺寸（寬 × 深 × 高） | 1.8 × 0.952 × 0.03 m（上限 1.95 × 1.05 × 0.12 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 6,526 / 3,262 / 978（不含 Detail_：6,246 / 3,122 / 936） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_Stitches） |
| 材質數 | 1（`M_YP06_01_RushMatFlat`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 模型裡沒有 |
| 檔案 | `art/exports/yard-props-c/YP06_01_v001.fbx`（LOD0–2）、`art/exports/yard-props-c/YP06_01_v001.glb`（LOD0）、`art/source/yard-props-c/YP06_01_v001.blend` |

### YP06_02 草蓆（捲起）（RushMatRolled，v001）

同一張草蓆捲起來：一條 9 mm 厚的螺旋帶捲了四圈多（兩端看得到一圈圈），被自己的重量壓扁一點；兩端和鬆開的邊緣有草頭伸出。兩條草繩，各在上面打結、留兩段繩尾。灰白的舊色、髒污、底下的潮濕和青苔畫在貼圖上。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/YP06/`，選用 cand-4（92） |
| 尺寸（寬 × 深 × 高） | 0.958 × 0.207 × 0.2 m（上限 1.0 × 0.3 × 0.26 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 12,916 / 6,458 / 1,936（不含 Detail_：12,916 / 6,458 / 1,936） |
| 物件數（每個 LOD） | 1（本體 1 + 無） |
| 材質數 | 1（`M_YP06_02_RushMatRolled`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | `YP06_02_Collision`：一個盒子 0.86 × 0.18 × 0.17 m（只在 FBX 和 .blend 裡，不顯示） |
| 檔案 | `art/exports/yard-props-c/YP06_02_v001.fbx`（LOD0–2）、`art/exports/yard-props-c/YP06_02_v001.glb`（LOD0）、`art/source/yard-props-c/YP06_02_v001.blend` |

### YP06_03 曬穀竹匾（DryingTrayRice，v001）

一個淺的編織竹匾（編織紋在貼圖和法線圖上），邊是兩圈竹片箍、用藤皮綁了十六處（Detail_Lashings），底下兩根交叉的竹片。裡面薄薄一層稻穀，越往邊緣越薄；一粒粒穀子和耙過的淺溝在法線圖上，竹匾的灰白和一點青苔畫在貼圖上。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/YP06/`，選用 cand-4（92） |
| 尺寸（寬 × 深 × 高） | 0.843 × 0.841 × 0.09 m（上限 0.9 × 0.9 × 0.14 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 6,150 / 3,074 / 922（不含 Detail_：1,734 / 866 / 260） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_Lashings） |
| 材質數 | 1（`M_YP06_03_DryingTrayRice`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | `YP06_03_Collision`：一個盒子 0.8 × 0.8 × 0.08 m（只在 FBX 和 .blend 裡，不顯示） |
| 檔案 | `art/exports/yard-props-c/YP06_03_v001.fbx`（LOD0–2）、`art/exports/yard-props-c/YP06_03_v001.glb`（LOD0）、`art/source/yard-props-c/YP06_03_v001.blend` |

### YP07_01 陶盆蔥（PotScallion，v001）

手捏的厚陶盆（捲邊、不太圓、盆口一個缺口），盆裡的土堆高。六叢蔥，每根葉子是五邊形的細管，大約四根有一根折下來；沒有葉片卡。陶盆上的白色鹼花、小坑、手指捏痕、盆口往下的裂紋、潮濕的盆腳和青苔，最高的葉尖發黃，畫在貼圖上。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/YP07/`，選用 cand-4（91） |
| 尺寸（寬 × 深 × 高） | 0.344 × 0.304 × 0.5 m（上限 0.6 × 0.6 × 0.62 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 2,964 / 1,482 / 444（不含 Detail_：2,964 / 1,482 / 444） |
| 物件數（每個 LOD） | 1（本體 1 + 無） |
| 材質數 | 1（`M_YP07_01_PotScallion`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | `YP07_01_Collision`：一個盒子 0.28 × 0.28 × 0.2 m（只在 FBX 和 .blend 裡，不顯示） |
| 檔案 | `art/exports/yard-props-c/YP07_01_v001.fbx`（LOD0–2）、`art/exports/yard-props-c/YP07_01_v001.glb`（LOD0）、`art/source/yard-props-c/YP07_01_v001.blend` |

### YP07_02 木盆薄荷（TubBroadHerb，v001）

小的木桶盆：十二片桶板（頂端不齊、有缺角），兩圈竹片箍、箍頭用繩綁住，桶底板，盆裡的土堆高。十三根莖，葉子對生、每節轉 90°，每片是有鋸齒的碗形葉片（約 140 片），每根莖頂四片嫩葉；沒有葉片卡。桶板灰白有裂紋、盆腳潮濕有青苔、部分葉子偏黃，畫在貼圖上。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/YP07/`，選用 cand-4（91） |
| 尺寸（寬 × 深 × 高） | 0.408 × 0.4 × 0.446 m（上限 0.6 × 0.6 × 0.62 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 5,238 / 2,618 / 785（不含 Detail_：5,238 / 2,618 / 785） |
| 物件數（每個 LOD） | 1（本體 1 + 無） |
| 材質數 | 1（`M_YP07_02_TubBroadHerb`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | `YP07_02_Collision`：一個盒子 0.28 × 0.28 × 0.21 m（只在 FBX 和 .blend 裡，不顯示） |
| 檔案 | `art/exports/yard-props-c/YP07_02_v001.fbx`（LOD0–2）、`art/exports/yard-props-c/YP07_02_v001.glb`（LOD0）、`art/source/yard-props-c/YP07_02_v001.blend` |

### YP07_03 陶盆開花香草（PotFloweringHerb，v001）

手捏的厚陶盆，盆口破了一塊、另有一個小缺口，盆裡的土堆高。十四根細莖，小葉對生（140 片），每根莖頂一串七個淡紫色的小花苞；沒有葉片卡。鹼花、小坑、捏痕、從破口往下的裂紋、潮濕的盆腳和青苔畫在貼圖上。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/YP07/`，選用 cand-4（91） |
| 尺寸（寬 × 深 × 高） | 0.354 × 0.287 × 0.353 m（上限 0.6 × 0.6 × 0.62 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 6,148 / 3,074 / 922（不含 Detail_：6,148 / 3,074 / 922） |
| 物件數（每個 LOD） | 1（本體 1 + 無） |
| 材質數 | 1（`M_YP07_03_PotFloweringHerb`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | `YP07_03_Collision`：一個盒子 0.27 × 0.27 × 0.19 m（只在 FBX 和 .blend 裡，不顯示） |
| 檔案 | `art/exports/yard-props-c/YP07_03_v001.fbx`（LOD0–2）、`art/exports/yard-props-c/YP07_03_v001.glb`（LOD0）、`art/source/yard-props-c/YP07_03_v001.blend` |

### YP08 牆上掛串（竹篩、辣椒、玉米、蒜）（WallHangings，v001）

掛在牆上：牆面是模型背後兩塊背板所在的平面；原點和本包其他東西一樣在腳印中心、最低的垂下物底下（擺的時候要抬到牆上的高度）。兩個木托架（背板、托臂、斜撐，釘子是 Detail_Nails）架著一根竹竿，竹竿和托臂綁住，竿上四個木鉤。竹篩：淺的編織篩（編織紋在貼圖和法線圖上），竹片箍綁了十二處（Detail_Lashings），背面交叉的竹片，從篩邊兩點用繩吊著。辣椒串（Chillies）：58 根乾辣椒，每根是彎曲變細的管，綁在一條繩上；蒜辮（Garlic）：15 顆蒜頭，各帶一撮乾根，編成一條；玉米串（Maize）：五根玉米，尖朝下，玉米皮往上翻、繞四圈綁住後散開。托架的風化和頂上的青苔、辣椒深淺不一、竹篩的灰白畫在貼圖上。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/YP08/`，選用 cand-4（92） |
| 尺寸（寬 × 深 × 高） | 1.6 × 0.377 × 0.798 m（上限 1.75 × 0.5 × 1.2 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 19,084 / 9,541 / 2,859（不含 Detail_：16,788 / 8,393 / 2,517） |
| 物件數（每個 LOD） | 3（本體 1 + Detail_Lashings, Detail_Nails） |
| 材質數 | 1（`M_YP08_WallHangings`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 模型裡沒有 |
| 檔案 | `art/exports/yard-props-c/YP08_v001.fbx`（LOD0–2）、`art/exports/yard-props-c/YP08_v001.glb`（LOD0）、`art/source/yard-props-c/YP08_v001.blend` |

### YP09_01 木箱（敞口）（CrateOpen，v001）

四根角柱凸出箱頂；每面三排木板夾在角柱之間，寬窄不一、板間有縫；四片底板；正面最上面一片缺了一角，最下面一片順紋裂開。兩端各一條麻繩提把，穿過去在內側打結；角柱上的釘子是 Detail_Nails。每片板的裂紋、曬灰的地方、釘子下的鏽水痕、箱腳的潮濕、泥和青苔畫在貼圖上。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/YP09/`，選用 cand-4（92） |
| 尺寸（寬 × 深 × 高） | 0.676 × 0.41 × 0.346 m（上限 0.72 × 0.45 × 0.4 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 4,560 / 2,280 / 682（不含 Detail_：4,032 / 2,016 / 604） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_Nails） |
| 材質數 | 1（`M_YP09_01_CrateOpen`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | `YP09_01_Collision`：一個盒子 0.6 × 0.4 × 0.34 m（只在 FBX 和 .blend 裡，不顯示） |
| 檔案 | `art/exports/yard-props-c/YP09_01_v001.fbx`（LOD0–2）、`art/exports/yard-props-c/YP09_01_v001.glb`（LOD0）、`art/source/yard-props-c/YP09_01_v001.blend` |

### YP09_02 帶蓋米箱（RiceChest，v001）

後高前低的米箱：四根角柱、柱間的木板，兩端的頂板照斜度切；正面中間一片順紋裂開。箱蓋是五片前後走向的木板、底下兩根橫木，前面伸出來；後面兩片帶插銷的鐵鉸鏈，前面一個木舌和木塊當扣；蓋子是關著的（和箱子是同一個網格）。一片板用小木板釘補；釘子是 Detail_Nails。板的裂紋、蓋上的節疤、曬灰、釘子下的鏽、箱腳的潮濕和青苔、蓋上的青苔、常掀蓋那裡磨亮的淺色畫在貼圖上。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/YP09/`，選用 cand-4（92） |
| 尺寸（寬 × 深 × 高） | 0.621 × 0.521 × 0.55 m（上限 0.68 × 0.56 × 0.6 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 3,456 / 1,728 / 516（不含 Detail_：2,620 / 1,310 / 392） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_Nails） |
| 材質數 | 1（`M_YP09_02_RiceChest`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | `YP09_02_Collision`：一個盒子 0.62 × 0.5 × 0.54 m（只在 FBX 和 .blend 裡，不顯示） |
| 檔案 | `art/exports/yard-props-c/YP09_02_v001.fbx`（LOD0–2）、`art/exports/yard-props-c/YP09_02_v001.glb`（LOD0）、`art/source/yard-props-c/YP09_02_v001.blend` |

### YP10 獨輪車（車斗裡兩個麻袋）（Wheelbarrow，v001）

實心木板輪：三片木板拼成，外圈鐵箍，兩面各一圈鐵環、各十二顆鉚釘，每面兩根釘住的橫木，車出來的輪轂套在輪軸上、兩根轅外側插銷。兩根轅從輪軸往後斜上到把手（削細、削圓、纏繩）；車斗是一片片木板：四片底板、兩側和兩端各兩片板，往上外張，每側兩根釘住的橫木。兩隻外撇的腳，各一根斜撐到轅、兩腳之間一根橫木，用繩綁住；車子靠輪子和兩隻腳站著。兩個裝滿的麻袋，袋口繞兩圈繩紮住、袋口的布摺出來往外張；每個袋子上一塊縫上的補丁畫在貼圖上，縫線的凹凸在法線圖裡。鉚釘和釘頭是 Detail_Rivets；裂紋、輪子三片板的兩道接縫、鏽、下半部的泥畫在貼圖上。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/YP10/`，選用 cand-4（92） |
| 尺寸（寬 × 深 × 高） | 1.774 × 0.628 × 0.941 m（上限 1.85 × 0.8 × 1.0 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 7,064 / 3,532 / 1,058（不含 Detail_：6,096 / 3,048 / 914） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_Rivets） |
| 材質數 | 1（`M_YP10_Wheelbarrow`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | `YP10_Collision`：一個盒子 1.3 × 0.62 × 0.62 m（只在 FBX 和 .blend 裡，不顯示） |
| 檔案 | `art/exports/yard-props-c/YP10_v001.fbx`（LOD0–2）、`art/exports/yard-props-c/YP10_v001.glb`（LOD0）、`art/source/yard-props-c/YP10_v001.blend` |

### YP11 扁擔和兩個水桶（CarryingPoleBuckets，v001）

放下來的樣子，不是挑著：兩個水桶放在地上，扁擔橫架在兩個桶口、夾在兩耳之間（三視圖畫的是挑起來）。每個桶：十二片桶板（頂端不齊、有缺角），兩道帶鉚釘的鐵箍（Detail_Rivets），兩片鑽孔的耳板，桶裡有水；提繩從耳板接到綁在扁擔端的木鉤，鬆鬆垂著。桶板的裂紋和桶口裂縫、生鏽的鐵箍、扁擔的裂紋和中間磨亮、桶腳的潮濕和青苔畫在貼圖上。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/YP11/`，選用 cand-3（90） |
| 尺寸（寬 × 深 × 高） | 1.692 × 0.397 × 0.389 m（上限 1.8 × 0.5 × 0.6 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 9,332 / 4,666 / 1,398（不含 Detail_：8,628 / 4,314 / 1,294） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_Rivets） |
| 材質數 | 1（`M_YP11_CarryingPoleBuckets`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 模型裡沒有 |
| 檔案 | `art/exports/yard-props-c/YP11_v001.fbx`（LOD0–2）、`art/exports/yard-props-c/YP11_v001.glb`（LOD0）、`art/source/yard-props-c/YP11_v001.blend` |

### YP12 大水缸（陶缸、木蓋、木瓢）（WaterVat，v001）

一個拉坯的厚缸壁，捲邊的缸口（缸內也有做），略不圓；肩上兩道凸起的繩紋；缸口三處缺口；水面在缸口下 8 cm。木蓋是三片照圓切的木板、上面兩根釘住的橫木（前面那片缺了一角），蓋住缸口一半多一點；木瓢是半個葫蘆，用三圈繩綁一根木柄。缸壁左前方一道裂縫，用三個鐵扒釘扣住（Detail_Staples），木蓋的釘子是 Detail_Nails。釉面停在一條不齊的線、線上有往上伸的釉舌，釉面剝落的角形缺塊、裂縫和滲水痕、兩道拉坯線、缸口下的白色水垢流痕、缸內的水垢線、缸腳的青苔和泥、木蓋的裂紋和節疤畫在貼圖上。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/YP12/`，選用 cand-3（92） |
| 尺寸（寬 × 深 × 高） | 0.788 × 0.786 × 0.908 m（上限 0.85 × 0.85 × 0.98 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 4,928 / 2,464 / 734（不含 Detail_：4,664 / 2,332 / 698） |
| 物件數（每個 LOD） | 3（本體 1 + Detail_Nails, Detail_Staples） |
| 材質數 | 1（`M_YP12_WaterVat`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | `YP12_Collision`：一個盒子 0.78 × 0.78 × 0.86 m（只在 FBX 和 .blend 裡，不顯示） |
| 檔案 | `art/exports/yard-props-c/YP12_v001.fbx`（LOD0–2）、`art/exports/yard-props-c/YP12_v001.glb`（LOD0）、`art/source/yard-props-c/YP12_v001.blend` |

### YP13_01 溪邊水草（CreekGrass，v001）

一叢約 1 m 高的溪邊長草：72 片有中摺的長葉，中間直立、外圈彎下垂；每片葉子都是單獨的一片，沒有葉片卡。五根高出葉子的細穗，每根頂上一串下垂的圓錐花序（16 條小枝、32 粒）；基部七片貼地的枯葉。外圈葉梢和葉尖發黃、基部褐色的枯鞘、褐色斑點畫在貼圖上。Detail_Base（一薄片濕土和五顆小石）在標準畫質關掉；葉片從地面下 1 cm 開始，可以壓進不平的地面。沒有碰撞。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/YP13/`，選用 cand-3（91，水草） |
| 尺寸（寬 × 深 × 高） | 1.223 × 1.228 × 1.188 m（上限 1.5 × 1.5 × 1.35 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 8,270 / 4,133 / 1,239（不含 Detail_：7,380 / 3,689 / 1,107） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_Base） |
| 材質數 | 1（`M_YP13_01_CreekGrass`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 模型裡沒有 |
| 檔案 | `art/exports/yard-props-c/YP13_01_v001.fbx`（LOD0–2）、`art/exports/yard-props-c/YP13_01_v001.glb`（LOD0）、`art/source/yard-props-c/YP13_01_v001.blend` |

### YP13_02 溪邊小白花（CreekFlowers，v001）

約 0.35 m 高的矮叢：16 片寬的基生葉，20 根細莖、莖上對生有鋸齒的葉（200 片），每根莖頂分成三枝：44 朵五瓣小花（多數白色，幾朵淡紫）和 16 個花苞。每片葉子和花瓣都是單獨的一片，沒有葉片卡；花心是一個小小的黃色圓頂。Detail_Base（一薄片濕土和四顆小石）在標準畫質關掉；莖從地面下開始，可以壓進不平的地面。沒有碰撞。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/YP13/`，選用 cand-4（91，小花） |
| 尺寸（寬 × 深 × 高） | 0.627 × 0.704 × 0.399 m（上限 0.9 × 0.9 × 0.6 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 10,930 / 5,464 / 1,638（不含 Detail_：10,120 / 5,060 / 1,518） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_Base） |
| 材質數 | 1（`M_YP13_02_CreekFlowers`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 模型裡沒有 |
| 檔案 | `art/exports/yard-props-c/YP13_02_v001.fbx`（LOD0–2）、`art/exports/yard-props-c/YP13_02_v001.glb`（LOD0）、`art/source/yard-props-c/YP13_02_v001.blend` |

## 驗證

- QA（`tools/art/qa_lod0_basic.py` 嚴格與寬鬆、`tools/art/qa_contact_glb.py`）：23 個模型嚴格、寬鬆都是 0 項；接觸檢查最大 2.5 mm（YP13_02 的莖，從地面下開始），其餘在 2.3 mm 以內（YP08、YP13_01 2.3 mm，YP01_04 1.9 mm，YP06_01、YP12 1.7 mm，YP11 1.6 mm，其他 1 mm 以內）。結果在 `art/previews/yard-props-c/qa/`。
- Unity 6000.3.28f1 獨立匯入：`art/previews/yard-props-c/unity/report.txt`（23 個模型 331 項全過）。檢查內容：匯入尺寸和 model_info 差 2 cm 內、在工作包上限內、底部在地面、每個 LOD 的三角面和物件數、一個材質、貼圖 1024、`minTier = standard`、Detail_ 關掉後本體還在、model_info 有碰撞的 14 件各有一個碰撞盒而其餘沒有、薄葉片和布的九件材質是雙面。
- 每件的審圖在 `art/previews/yard-props-c/<ID>/`：灰模（`clay/`）、四個方向加 1.75 m 人形尺、近看、線框、LOD0／LOD1／LOD2（不含 Detail_）。`<ID>-sheet.jpg` 把選用的三視圖和這些排在同一張。
- 同光同角度並排（含 1.75 m 人形尺，灰模和成品各一張）：`art/previews/yard-props-c/compare/`。YP01 對 C 的菜畦 VG01；YP02 對 C 的晾衣竿 VG03 和蓑衣架 LV08；YP10、YP11 對 C 的兩輪板車 VG05 和扁擔籮筐 VG06；YP03、YP04、YP12 對 C 的長石槽 VG08 和醃菜甕 LV05；YP05、YP09 對 LV05；YP06、YP07、YP08 對 C 的稻草蛋籃 LV12；YP13 對 C 的蕨 BM09_02 和 LV05；`YP-all` 是 23 個模型加 LV05。
- 院子擺設（工作包「全包檢查」）：`compare/YP-yard-eye-cam.png`（眼高 1.0 m，從東南邊看院子，對著 A1 V6）、`YP-yard-top-cam.png`（俯視配置）、`YP-yard-vs-V6.jpg`（和 V6 並排）。背景是 B 的民居 VL04_DiligentFamilyHouse，它自己的晾衣架等小物（Detail_Small）藏起來。Unity 裡同樣的擺設（沒有房子）：`unity/YP-yard-eye.png`。

## 實際工時

台灣時間，照檔案和提交時間：

| 時段 | 做的事 |
|---|---|
| 11-16 19:45–20:25 | 讀工作包和 A1 設定圖，13 種的三視圖（56 張） |
| 11-16 20:25–11-17 04:55 | YP03、YP04、YP05、YP09、YP11、YP12 v001 |
| 11-17 04:55–06:45 | 上面六件的細節（法線圖凹凸、缺角和裂開、補板） |
| 11-17 06:45–10:10 | YP06、YP07、YP08 |
| 11-17 10:10–14:35 | YP10、YP02 |
| 11-17 14:35–16:25 | YP01、YP13 |
| 11-17 20:30–11-18 02:40 | 收尾：審圖、並排、院子擺設、Unity 檢查、README |

合計約 26 小時 45 分（工作包估 A 批 52 小時，加全包檢查的一部分）。11-17 16:25–20:30 等審查意見、沒有工作，不算在內；其餘時段包含等三視圖生成和渲染的時間，沒有扣掉。

## 已知問題與未驗

- 正式場景擺放、手機上的效果都未驗。
- YP01：作物排自帶培土，放上空壟時兩層土疊在一起（作物排的土較高較寬，蓋住空壟）；白菜、豆葉是單面的薄葉片（Unity 用雙面材質）。只有三種作物。
- YP02：碰撞盒只有左邊竹竿；布衫是衣身和兩袖三片搭在繩上，不是一件縫好的衣服，從背面看得出來；扣子、補丁、條紋是畫的。
- YP04：三視圖上的石頭補片和鐵扒釘沒有做。
- YP06：草蓆和竹匾的編織紋是貼圖，不是一條條做出來的。
- YP08：原點在最低垂物底下，擺的時候要抬到牆上的高度；它寬 1.6 m，VL04 正面門和窗之間的牆只有約 0.5 m，院子擺設圖裡掛在窗旁，有一點蓋到窗框。
- YP09_02：米箱蓋子和箱子是同一個網格，不能打開。
- YP10：輪子不能轉（和車架是同一個網格）。
- YP11：做成放下的樣子（三視圖畫的是挑起來）。
- YP13：是給溪邊（V5）的，院子擺設圖裡只放在院子邊上，沒有另外對著 V5 拍。
- 院子擺設圖：地面是平的單色，沒有 V6 的石板地、石牆和竹籬；VL04 門廊上的兩個大甕是房子本身的，不是這一批。
- 重跑院子擺設和並排前，要先 `git lfs pull` B 的 VL04_DiligentFamilyHouse GLB 和並排用到的舊道具。
