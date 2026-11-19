| 項目 | 內容 |
|---|---|
| 誰做的 | C（Eli-0731） |
| 工作包 | docs/execution/2026-11-15/C-300h-D2-small-life.md，B 批；標準照 docs/execution/2026-11-15/00-300h-共同標準.md |
| ID | DP06（B 批樣品，六種：DP06_01–DP06_06；DP07–DP13 等樣品審過再做） |
| 分支／PR | art/c-1115-d2-moss-plants ／ 開 PR 後補 |
| 版本 | v001（檔名帶 `_v001`；之後改版另存 v002，不覆寫） |
| 狀態 | Exported ／ Imported（Unity 6000.3.28f1 獨立匯入檢查）／ Visually Verified（Blender 與 Unity 審圖、和 D2 設定圖並排）／ In-game Verified：未驗（沒放進正式場景） |
| 素材來源 | 原創；三視圖參考在 `art/references/DP06/`；貼圖全部在建模腳本裡畫，沒有外部素材 |
| 實際工時 | 2026-11-19（台灣時間），約 3 小時：讀工作包、三視圖（24 張）與自評、建模腳本、灰模兩輪、上貼圖六輪、QA、審圖、Unity 檢查 |

# D2 古樹神木的苔與小植物（d2-moss-c）

11/15 的 300 小時包 B 批：D2 古樹神木地上的苔與小植物（設定圖 V2、V3、V5、V6）。DP06 苔團先交樣品，審過再做 DP07 苔被片、DP08 小蕨、DP09 林下地被、DP10 垂藤、DP11 莎草、DP12 枯小灌叢、DP13 地衣片。靜態擺設；擺進世界由核心組做，這裡不改主場景、不改區塊 JSON。

**共同做法**
- 先生成三視圖（每種 4 張）、自評選一張（分數和取捨在 `art/references/DP06/prompt.txt`），再做灰模（`art/previews/d2-moss-c/<ID>/clay/`），最後上貼圖。
- 苔團是真的幾何：不規則帶瓣的外形（邊緣有細的鋸齒）、幾個大瓣、上面許多小苔球凸起；頂面用平均分布的點做 Delaunay 三角化，沒有中心放射的扇形面。一撮撮的苔尖畫在貼圖和法線上。沒有用卡片。
- 原點：底部中心，z = 0 在地面；苔的邊緣正好落在 z = 0，底下一圈土裙往地下 1.5 cm（DP06_06 的小叢 1 cm）（共同標準第四節），擺在不平的地上不會浮空。DP06_05 石頂苔帽例外：z = 0 是下垂邊緣的最低處，底下是空的，扣在石頭上。Blender −Y 是正面（FBX／Unity 是 −Z）。
- 一件一個材質、一套 1024 貼圖（Albedo／Normal／ORM／MaskURP），雙面。沒有 `Detail_*`。`minTier` 都是 `standard`。
- LOD：LOD1 約 50%、LOD2 約 15%（共同標準第四節）。
- 顏色照 D2：暗橄欖綠，朝天的苔尖帶一點暗黃綠，苔撮之間是暗縫；不是亮綠。三視圖本身比 D2 亮、偏黃，顏色不照三視圖。
- 建模流程和 `art/source/d2-mushrooms-c/build_dp.py`（DP01）相同（來源貼圖 → 一張 UV 圖集 → Cycles 烘焙），因為那個套件還沒進 main，所以把流程複製成 `build_moss.py`，工具（`creekside-life-c/wl_kit.py`）用 main 上的。亂數種子固定，重建結果一樣。
- 重建：`blender -b --factory-startup -P art/source/d2-moss-c/build_moss.py -- DP06_01 [DP06_02 ...] [--clay]`；審圖、QA、D2 對圖用的渲染：`BL=<blender> sh art/source/d2-moss-c/render_reviews.sh`；審圖總表和 D2 並排圖：`D2=<放 D2 V1–V6.png 的資料夾> sh art/source/d2-moss-c/make_sheets.sh`；Unity：`UNITY=<Unity.exe 6000.3.28f1> sh art/source/d2-moss-c/unity/run_unity_check.sh`。

### DP06_01 苔團・小圓墊（MossCushionSmall，v001）

一團低圓的苔墊（約 0.25 × 0.25 m、高約 0.10 m），表面一團團小苔球，邊緣散出細苔鬚。放地上、根旁、石頭腳下。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP06/`，選用 A cand-3（90） |
| 尺寸（寬 × 深 × 高） | 0.248 × 0.247 × 0.102 m（高度含地下的土裙） |
| 三角面 LOD0 / LOD1 / LOD2 | 2,590 / 1,295 / 388（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP06_01_MossCushionSmall`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP06_01_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP06_01_v001.glb`（LOD0）、`art/source/d2-moss-c/DP06_01_v001.blend` |

### DP06_02 苔團・多瓣中丘（MossMoundLobed，v001）

三、四個大小不同的圓瓣併成一丘（約 0.42 × 0.41 m、高約 0.18 m），瓣間有凹縫。像 V6 石邊那團。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP06/`，選用 B cand-1（91） |
| 尺寸（寬 × 深 × 高） | 0.423 × 0.41 × 0.178 m（高度含地下的土裙） |
| 三角面 LOD0 / LOD1 / LOD2 | 3,200 / 1,599 / 479（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP06_02_MossMoundLobed`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP06_02_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP06_02_v001.glb`（LOD0）、`art/source/d2-moss-c/DP06_02_v001.blend` |

### DP06_03 苔團・大片低鋪（MossPatchSpreading，v001）

一大片低平的苔（約 0.80 × 0.65 m、只高約 0.12 m），有幾處緩丘，外形不規則帶瓣。鋪在林床、根和根之間。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP06/`，選用 C cand-3（90） |
| 尺寸（寬 × 深 × 高） | 0.805 × 0.652 × 0.118 m（高度含地下的土裙） |
| 三角面 LOD0 / LOD1 / LOD2 | 3,862 / 1,931 / 578（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP06_03_MossPatchSpreading`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP06_03_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP06_03_v001.glb`（LOD0）、`art/source/d2-moss-c/DP06_03_v001.blend` |

### DP06_04 苔團・沿根腳長條（MossRootFootStrip，v001）

一串緩丘排成微彎的長條（約 0.60 × 0.22 m），兩端收尖，貼著任一段根的根腳放。根不在模型裡（根是 Josh 的 DR 系列）。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP06/`，選用 D cand-1（91） |
| 尺寸（寬 × 深 × 高） | 0.602 × 0.215 × 0.146 m（高度含地下的土裙） |
| 三角面 LOD0 / LOD1 / LOD2 | 3,008 / 1,503 / 450（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP06_04_MossRootFootStrip`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP06_04_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP06_04_v001.glb`（LOD0）、`art/source/d2-moss-c/DP06_04_v001.blend` |

### DP06_05 苔團・石頂苔帽（MossBoulderCap，v001）

一頂圓的苔帽（約 0.47 × 0.40 m、高約 0.17 m），邊緣往下垂，底下是空的，整合時扣在任一顆石頭頂上（像 V3、V6 石頭頂的苔）。z = 0 是下垂邊緣的最低處，沒有土裙。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP06/`，選用 E cand-1（91） |
| 尺寸（寬 × 深 × 高） | 0.473 × 0.403 × 0.166 m（高度含地下的土裙） |
| 三角面 LOD0 / LOD1 / LOD2 | 3,856 / 1,928 / 578（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP06_05_MossBoulderCap`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP06_05_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP06_05_v001.glb`（LOD0）、`art/source/d2-moss-c/DP06_05_v001.blend` |

### DP06_06 苔團・碎散小叢（MossTuftsScattered，v001）

一叢大的加六叢小的，各自分開，散在約 0.49 × 0.38 m 內。每叢都有自己的土裙。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/DP06/`，選用 F cand-4（90） |
| 尺寸（寬 × 深 × 高） | 0.486 × 0.384 × 0.101 m（高度含地下的土裙） |
| 三角面 LOD0 / LOD1 / LOD2 | 3,840 / 1,919 / 575（工作包每件 LOD0 ≤ 4,000） |
| 物件數（每個 LOD） | 1 |
| 材質數 | 1（`M_DP06_06_MossTuftsScattered`，雙面） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | standard |
| 碰撞 | 沒有（人可以走過去） |
| 檔案 | `art/exports/d2-moss-c/DP06_06_v001.fbx`（LOD0–2）、`art/exports/d2-moss-c/DP06_06_v001.glb`（LOD0）、`art/source/d2-moss-c/DP06_06_v001.blend` |

## 驗證

- QA（`tools/art/qa_lod0_basic.py` 嚴格與寬鬆、`tools/art/qa_contact_glb.py`）：六種都是嚴格 0、寬鬆 0；接觸 0 mm（DP06_06 每叢都有自己的土裙，沒有浮空的小叢）。結果在 `art/previews/d2-moss-c/qa/`。
- Unity 6000.3.28f1 獨立匯入：`art/previews/d2-moss-c/unity/report.txt`（96 項全過）：尺寸和 model_info 差 2 cm 內、在工作包尺寸內、土裙往地下 1.5 cm（DP06_05 苔帽的下垂邊緣在原點平面上）、LOD0 ≤ 4,000 且 LOD1 50%／LOD2 15%、一個材質、1024 貼圖、雙面、沒有碰撞。截圖在同一個資料夾。
- 每件的審圖在 `art/previews/d2-moss-c/<ID>/`：灰模（`clay/`）、四個方向加 1.75 m 人形尺、近看、線框、LOD0／LOD1／LOD2，`<ID>-sheet.jpg` 把選用的三視圖和這些排在同一張。
- **和 D2 設定圖對圖**（共同標準第四節）：`<ID>/d2/<ID>-d2-compare.jpg`，上排是 V6 石邊苔團、V6 近景苔團、V3 石上的苔，下排是成品在 D2 的光下（陰天、薄霧、濕褐土）的兩個鏡位，渲染腳本 `render_d2match.py`。

## 視覺檢查紀錄（DP06）

灰模兩輪、上貼圖六輪，每輪看同樣的角度，先修最嚴重的：
1. 灰模第一輪：01、05 側面幾乎垂直像鼓 → 改成圓頂、底邊外擴；小苔球疊加成尖刺 → 取最高值不相加；02 的大瓣看不出來 → 加大瓣、降低瓣間的底。
2. 灰模第二輪：02 的瓣變成尖峰 → 瓣改成圓頂、半徑加大。
3. 上貼圖第一輪（和 D2 並排）：太暗太褐，像土堆 → 調成橄欖綠；表面一片平滑斑紋 → 苔撮做成一團團、團間是暗縫；邊緣苔鬚是深褐尖刺 → 改苔色、加多、變短。
4. 第二、三輪：黃綠跟著低頻雜訊走成大塊迷彩 → 只依朝天的面上色、保留貼圖的苔撮紋；苔鬚還是像一圈刺，而且貼在苔面上造成共面 → 拿掉苔鬚，改成外形邊緣的細鋸齒。
5. 第四、五輪：陡坡上的頂視 UV 拉成直條紋 → 陡坡改用繞著苔團的投影；頂上出現從中心放射的皺褶（極座標網格在中心擠成扇形） → 頂面改成平均分布的點做 Delaunay 三角化。
6. 第六輪（和 D2 並排）：整體比 D2 暗一截 → 苔的顏色和苔尖的黃綠調亮。

**自評：和 D2 設定圖並排約 60% 像，還沒到 85–90%。** 顏色（橄欖綠帶黃綠苔尖）、圓墊和多瓣的形狀、貼地不浮空對得上；差的是：
- D2 的苔是一根根細絲立起來的苔撮，輪廓毛茸茸的；成品的苔撮只在貼圖和法線上，近看是一粒粒的斑點，輪廓偏圓滑。要更像需要真的細絲幾何或透明卡片，但工作包要求不用卡片，面數也有 4,000 的上限，這一點要審查時決定。
- 單件放在空地上看比較「乾淨」，設定圖裡的苔是長在石頭、根和落葉中間的。
- 三視圖本身比 D2 亮、偏黃；顏色照 D2，所以成品和三視圖的顏色不同。

## 已知問題與未驗

- 工作包寫「擺幾處 48」，這裡只交六種模型，擺放由核心組做。
- DP06_04 沒有根本體，擺的時候貼著任一段根的根腳放；DP06_05 要扣在一顆石頭上，石頭頂的弧度和苔帽底不一定完全貼合。
- 正式場景擺放、手機上的效果都未驗；不寫幀率。
