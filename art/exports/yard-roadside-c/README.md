| 項目 | 內容 |
|---|---|
| 誰做的 | C（Eli-0731） |
| 工作包 | docs/execution/2026-11-11/C-36h-yard-and-roadside-props.md |
| ID | VG01–VG08（VG04 是兩種：VG04_01、VG04_02） |
| 分支／PR | 批 A（VG01–VG04）：art/c-1111-vg-yard-props；批 B（VG05–VG08）：art/c-1111-vg-roadside-props ／ 開 PR 後補（一次一張，等前一張結案） |
| 版本 | v001（檔名帶 `_v001`；之後改版另存 v002，不覆寫） |
| 狀態 | Exported ／ Imported（Unity 6000.3.28f1 獨立匯入檢查）／ Visually Verified（Blender 與 Unity 審圖）／ In-game Verified：未驗（沒放進正式場景） |
| 素材來源 | 原創；三視圖參考在 `art/references/VG01/`–`art/references/VG08/` |

# 院子和路邊的東西 VG01–VG08

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

### VG05 兩輪手推板車（完好的空車）（Handcart，v001）

練「輪子的圓和輻條；車架的榫接」。兩根縱樑從車尾一路伸到車頭，前段削細削圓成把手；四根橫樑穿過縱樑，榫頭從外側露出來，同時托住車板。車床是六片各自寬窄、長短、厚薄不同的木板。邊欄：每側三根立柱插進縱樑，內側一片側板、上面一根橫木穿過立柱，車尾一片擋板加一根橫木，後立柱用繩綁住；車頭那端敞開。輪子：車出來的輪轂加兩道鐵箍，十二根由粗到細的輻條，六段輪輞拼成圓，外包一圈鐵箍、外側十二顆鉚釘；輪軸穿過縱樑下的兩塊軸座，輪轂外各插一根鐵銷。車頭下一根支腳加兩根斜撐，讓車床放平。完好的空車，和翻倒的破車 A2_OverturnedCart 不同。輪胎和支腳底的泥、車板的曬白、把手的磨亮畫在貼圖上。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/VG05/`，選用 cand-3（93） |
| 尺寸（寬 × 深 × 高） | 2.144 × 1.096 × 0.93 m（上限 2.2 × 1.1 × 1 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 7,740 / 3,870 / 1,160（不含 Detail_：7,740 / 3,870 / 1,160） |
| 物件數（每個 LOD） | 1（本體 1 + 無） |
| 材質數 | 1（`M_VG05_Handcart`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | `VG05_Collision`：一個盒子 1.44 × 1.1 × 0.9 m（只在 FBX 和 .blend 裡，不顯示） |
| 檔案 | `art/exports/yard-roadside-c/VG05_v001.fbx`（LOD0–2）、`art/exports/yard-roadside-c/VG05_v001.glb`（LOD0）、`art/source/yard-roadside-c/VG05_v001.blend` |

### VG06 扁擔與兩個籮筐（放下來的樣子）（CarryingPoleBaskets，v001）

練「竹編用貼圖；扁擔中間磨亮」。兩個籮筐放在地上，扁擔橫架在兩個筐口上，繩子鬆垂。竹編紋路在貼圖上，筐壁是一個有厚度的光滑碗形；建出來的有：筐口一圈竹箍和八處綁紮、每個筐底交叉的兩條竹篾（從筐底繞上筐壁到筐口）、每筐四條繩從筐口收到扁擔上、扁擔上的繩圈、兩端各一根擋繩的木栓。扁擔中間寬厚、兩端收窄微翹；中間被肩膀磨亮（較淺較光滑）和竹節畫在貼圖上。右邊的筐略小一點、轉了個方向。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/VG06/`，選用 cand-1（92） |
| 尺寸（寬 × 深 × 高） | 1.757 × 0.48 × 0.38 m（上限 1.8 × 0.5 × 0.6 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 7,992 / 3,996 / 1,198（不含 Detail_：7,992 / 3,996 / 1,198） |
| 物件數（每個 LOD） | 1（本體 1 + 無） |
| 材質數 | 1（`M_VG06_CarryingPoleBaskets`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 模型裡沒有 |
| 檔案 | `art/exports/yard-roadside-c/VG06_v001.fbx`（LOD0–2）、`art/exports/yard-roadside-c/VG06_v001.glb`（LOD0）、`art/source/yard-roadside-c/VG06_v001.blend` |

### VG07 石磨（卵石基座上的手推磨）（StoneMill，v001）

練「兩個圓柱疊放；石頭表面的鑿痕；出料的槽口」。下磨盤固定在接料盤中間，上磨盤疊在上面：頂面中心一個進料孔，側面上三分之二有一道道鑿出來的直槽（做在形狀上）；側面的鑿點和頂面放射狀的磨紋畫在貼圖上。接料盤是一塊圓石，一圈環形的槽、外緣一圈矮壁，正面的壁上開了缺口接出料槽口——一條帶溝的石舌往外往下伸，下面立一塊石板撐著。上磨盤側面嵌一塊木座，推柄穿過木座，用繩綁住。基座是十三塊卵石圍著一個芯堆成兩圈，腳邊幾顆小石頭。槽裡殘留的粉、槽口下的濕痕、基座的青苔和泥畫在貼圖上。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/VG07/`，選用 cand-4（93） |
| 尺寸（寬 × 深 × 高） | 0.983 × 0.975 × 0.846 m（上限 1 × 1 × 0.9 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 5,586 / 2,792 / 836（不含 Detail_：5,586 / 2,792 / 836） |
| 物件數（每個 LOD） | 1（本體 1 + 無） |
| 材質數 | 1（`M_VG07_StoneMill`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | `VG07_Collision`：一個盒子 0.86 × 0.86 × 0.8 m（只在 FBX 和 .blend 裡，不顯示） |
| 檔案 | `art/exports/yard-roadside-c/VG07_v001.fbx`（LOD0–2）、`art/exports/yard-roadside-c/VG07_v001.glb`（LOD0）、`art/source/yard-roadside-c/VG07_v001.blend` |

### VG08 餵牲口的長石槽（StoneTrough，v001）

練「挖空的厚度；內側的水漬和青苔」。整塊石頭挖空：槽壁厚 6–9 cm、各處不一樣（手鑿的），內側往下收窄到平的槽底；槽口的缺角做在形狀上，其中一個角缺得比較大。下面墊兩塊扁石。內側的舊水線（水線下深色帶綠、水線上有流痕）、槽底的淤泥、外側下半和槽口的青苔、淺色地衣、鏽色流痕都畫在貼圖上。照工作包只做石頭，沒有鐵件。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/VG08/`，選用 cand-3（93） |
| 尺寸（寬 × 深 × 高） | 1.511 × 0.469 × 0.414 m（上限 1.6 × 0.5 × 0.45 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 2,032 / 1,016 / 304（不含 Detail_：2,032 / 1,016 / 304） |
| 物件數（每個 LOD） | 1（本體 1 + 無） |
| 材質數 | 1（`M_VG08_StoneTrough`，全部共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | `VG08_Collision`：一個盒子 1.48 × 0.43 × 0.4 m（只在 FBX 和 .blend 裡，不顯示） |
| 檔案 | `art/exports/yard-roadside-c/VG08_v001.fbx`（LOD0–2）、`art/exports/yard-roadside-c/VG08_v001.glb`（LOD0）、`art/source/yard-roadside-c/VG08_v001.blend` |

## 驗證

- QA（`tools/art/qa_lod0_basic.py` 嚴格與寬鬆、`tools/art/qa_contact_glb.py`）：九個模型（VG01、VG02、VG03、VG04_01、VG04_02、VG05–VG08）嚴格、寬鬆都是 0 項；接觸檢查本體都在 1 mm 內（VG06 0.9 mm、VG07 0.2 mm，其餘 0 mm），結果在 `art/previews/yard-roadside-c/qa/`。
- Unity 6000.3.28f1 獨立匯入：`art/previews/yard-roadside-c/unity/report.txt`（九個模型 137 項全過）。檢查內容：匯入尺寸和 model_info 差 2 cm 內、在工作包上限內、底部在地面、每個 LOD 的三角面和物件數、一個材質、貼圖 1024、`minTier = standard`、Detail_ 關掉後本體還在、VG01、VG05、VG07、VG08 各有一個碰撞盒而其餘沒有、alpha clip 的三件 Albedo 有 alpha 且 Mip Maps Preserve Coverage 打開。
- 每件的審圖在 `art/previews/yard-roadside-c/<ID>/`：灰模（`clay/`）、四個方向加 1.75 m 人形尺、近看、線框、LOD0／LOD1／LOD2（不含 Detail_）。
- 同光同角度並排（含 1.75 m 人形尺，灰模和成品各一張）：`art/previews/yard-roadside-c/compare/`。VG01 對 C 的蕨 BM09_02、落葉貼片 BM10_02 和醃菜甕 LV05；VG02、VG03 對 C 的竹梯 LV03 和蓑衣架 LV08；VG04 對 B 的柴堆 R03 和 C 的稻草蛋籃 LV12；VG05 對 B 的翻倒板車 A2_OverturnedCart 和 LV05；VG06 對 C 的雞罩 LV01、蛋籃 LV12、吊籃 LV04；VG07、VG08 對 B 的枯井 D3_DryWell 和 LV05。`VG-setA`、`VG-setB` 是兩批各自放在一起加 LV05，`VG-all` 是全包九個模型加 LV05。Unity 裡的並排是 `unity/VG-set-*.png`。

## 已知問題與未驗

- 正式場景擺放、手機上的效果都未驗。
- VG01：菜葉是單面的薄片（材質雙面）；菜的種類只有三種做法，近看同一種的葉形相同、只有大小和角度不同。
- VG02：葉片是 2 × 2 格的面片，LOD2 減面後葉子變少；葫蘆的顏色是還在長的淺綠，不是曬乾的褐色。
- VG03：上衣是三片布搭在竿上拼成的（衣身、兩袖），不是一件縫好的衣服，從背面看得出來；領條和補丁是畫的。
- VG04：草披的稻草紋路是貼圖，草絲只有下緣那一圈是面片；VG04_02 的凹口照工作包文字做，和三視圖畫的門簾不同。VG04_02 有幾根地上的散草（Detail_）離地 2.7 mm。
- 灰模圖上 alpha clip 的面片是沒裁的方片（裁切在貼圖的 alpha）。
- VG05：車板、邊欄的木紋和鐵箍的鏽是貼圖；輪子不能轉（和車架是同一個網格）；鉚釘只在輪子外側。碰撞盒只蓋車床和輪子，不含把手。
- VG06：竹編是貼圖，筐壁是光滑的碗形，近看筐口看得出壁是一整片；繩子是鬆垂擺好的固定形狀。接觸檢查最大 0.9 mm。
- VG07：基座卵石面數低（每顆 320 個三角面），近看輪廓有稜角；上磨盤不能轉；頂面的磨紋和側面的鑿點是畫的，只有側面的直槽做在形狀上。
- VG08：LOD0 只有 2,032 個三角面，槽壁的起伏比較圓滑，手鑿的粗糙感主要靠貼圖；水線只畫在內側。
- 並排用的 B 的 A2_OverturnedCart、D3_DryWell、R03_FirewoodNeat 的 GLB 在 LFS 裡，重跑並排前要先 `git lfs pull` 這三個檔。
