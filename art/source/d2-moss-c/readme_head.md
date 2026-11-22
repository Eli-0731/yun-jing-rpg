| 項目 | 內容 |
|---|---|
| 誰做的 | C（Eli-0731） |
| 工作包 | docs/execution/2026-11-15/C-300h-D2-small-life.md，B 批；標準照 docs/execution/2026-11-15/00-300h-共同標準.md |
| ID | DP06（B 批樣品，六種：DP06_01–DP06_06；DP07–DP13 等樣品審過再做） |
| 分支／PR | art/c-1115-d2-moss-plants ／ 開 PR 後補 |
| 版本 | v002。v001 的母稿、模型及貼圖保留。 |
| 狀態 | Exported ／ Unity 6000.3.28f1 匯入結果見驗證紀錄／ Blender 並排審圖完成 ／ 正式 D2 場景驗收待驗 |
| 素材來源 | 原創；三視圖參考在 `art/references/DP06/`；貼圖全部在建模腳本裡畫，沒有外部素材 |
| 實際工時（v001） | 2026-11-19（台灣時間），約 3 小時：讀工作包、三視圖（24 張）與自評、建模腳本、灰模兩輪、上貼圖六輪、QA、審圖、Unity 檢查 |

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


**v002**
- 多瓣中丘加深瓣與瓣之間的凹谷。從連續苔面抬出小撮鈍頭幾何，減掉底層不需要的面數；修飾舊版粗塊狀的凹凸與苔尖色。早期的尖端在並排圖上呈現刺狀，已改成較低的鈍頭。
- 使用既有候選及選圖；v002 的貼圖在 `art/textures/d2-moss-c/v002/`。
