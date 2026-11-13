# Codex v6 執行報告

## A 部分｜主視覺（2026-11-12）

- 分支：`art/core-1112-codex-keyart-distance`
- 範圍：A1 的 KA11、KA12、KA13；A2 的 KA05、KA06、KA08、KA09、KA10。
- 實際總工時：約 0.35 小時（從讀取規格、候選審圖、整理檔案到提交；未含既有 v4 圖的原製作時間）。
- 製圖方式：KA11–KA13 使用內建 imagegen 各產生四張候選；KA05、KA06、KA08–KA10 沿用 v4 選定圖。KA06、KA10 以內建 imagegen 依原圖作降飽和色彩編修，原圖保留；構圖經目視核對。

| ID | 自評／10 | 預覽路徑 | 實際工時 | 沒做到或仍待驗證 |
|---|---:|---|---:|---|
| KA11 | 8.2 | `art/references/keyart/KA11/chosen.png` | 約 0.10 小時 | 90 m 神木與巨根的真實場景尺度、LOD、地形接縫尚未在 Unity 核對。 |
| KA12 | 8.4 | `art/references/keyart/KA12/chosen.png` | 約 0.07 小時 | 古碑和缺月記號尚無正式模型；祠台及東側舊路須由場景驗證。 |
| KA13 | 8.1 | `art/references/keyart/KA13/chosen.png` | 約 0.08 小時 | 首段石階與山門的實際距離、霧中可見性尚未在 Unity 核對。 |
| KA05 | 7.8 | `art/references/keyart/KA05/chosen.png` | 約 0.02 小時 | FE01–03 尚待從美術分支合併；舊候選原檔未在來源分支提供。 |
| KA06 | 7.7 | `art/references/keyart/KA06/chosen.png` | 約 0.03 小時 | RI01、RI02 尚待合併；水槽連接未建；舊候選原檔未提供。 |
| KA08 | 7.6 | `art/references/keyart/KA08/chosen.png` | 約 0.02 小時 | 山門與 SG 階梯尚待場景校準；舊候選原檔未提供。 |
| KA09 | 7.5 | `art/references/keyart/KA09/chosen.png` | 約 0.02 小時 | ST 街道小件與索橋仍待協作者，懸挑支撐須實景核對；舊候選原檔未提供。 |
| KA10 | 7.3 | `art/references/keyart/KA10/chosen.png` | 約 0.01 小時 | 正式同心石台等故事定稿；舊候選原檔未提供。 |

- 色彩處理：以 HSV 飽和度均值檢查定稿：KA06 由 108.8／255 降至 70.4／255；KA10 由 53.6／255 降至 31.6／255。兩張原圖均存於各自的 `candidate-original.png`；此為 imagegen 編修結果，非固定倍率的逐像素轉換。
- 編號差異：舊 KA08 圖像實為 B1 山門石階、舊 KA09 圖像實為 B2 山城街，與世界施工圖的部分 `shots.ka` 對應不同；區塊圖依圖像內容放置。KA11–KA13 依本輪執行文件指定的 D2、D4、D6 製作。
- 概念圖的鏡位與 55° 水平視角是生成約束，未經遊戲攝影機實測；不得當作實景驗收截圖。

## B 部分｜天空與遠景（2026-11-12）

- 分支：`art/core-1112-codex-keyart-distance`
- 範圍：SK01–SK06、CL01–CL03、MC-S、FA01；實際總工時約 1.5 小時，包含生成、貼圖處理、目視檢查、簡單卡片建模及提交。各項時間為估計值。
- 四片弧面骨架沿用既有 `SM_Skyline_Arc`；本輪沒有在 Unity 6000.3.28f1 匯入或實景測試。

| ID | 自評／10 | 預覽路徑 | 實際工時 | 沒做到或仍待驗證 |
|---|---:|---|---:|---|
| SK01–SK03 | 7.8 | `art/exports/sky-and-distance-v1/SK/SK03_sky-preview.png` | 約 0.45 小時 | 三層與弧面實際 UV 方位、材質霧色及遊戲攝影機尺度未驗。每張另有四片接縫圖。 |
| CL01–CL03 | 7.5 | `art/exports/sky-and-distance-v1/CL/CL01_sky-preview.png` | 約 0.20 小時 | 透明排序、雲層深度與場景光照未驗。每張另有四片接縫圖。 |
| SK04–SK06 | 7.7 | `art/exports/sky-and-distance-v1/SK/SK06_sky-preview.png` | 約 0.30 小時 | 東北高山與山城同場的 UV 方位及透視尺寸未驗。每張另有四片接縫圖。 |
| MC-S | 7.6 | `art/exports/sky-and-distance-v1/MC/MC-S_sky-preview.png` | 約 0.25 小時 | A4 觀景亭的實際可見度、遠景卡遮擋與燈點亮度未驗。另有四片弧面擺位圖。 |
| FA01 | 7.4 | `art/exports/sky-and-distance-v1/FA/FA01_sky-preview.png` | 約 0.30 小時 | Unity 的 Alpha Blend、雙面顯示、透明排序及 V 向流速未驗。另有四片與縱向接圖；灰模、FBX、GLB 已輸出。 |

- 影像檢查：SK01–SK06 長條皆為 4096 × 1024 RGB，左右及上下霧色邊界已檢；CL01–CL03 為 2048 × 512 RGBA 且左右像素一致；FA01 水紋上下像素一致。這些為檔案接縫檢查，不能代替弧面或卡片的實機驗收。
- FA01 GLB 回匯：`FA01_LOD0` 為 2 個三角面、1 個材質、尺寸 4 × 40 公尺。三視圖、灰模、`model_info.json` 與重建腳本均附在資產旁。

## C 部分｜中景地形與小件（2026-11-13）

- 分支：`art/core-1112-codex-keyart-distance`。依第 7 節順序完成 MM01–02、MM03–06、GR01／GR04、VP04、TX02、LF01–03、全包檢查；各項完成後皆分別提交並推送。
- 實際工作時間約 1.1 小時（依 02:25 至 03:25 左右的作業及提交時間估算；各項時間為近似值，含生成、建模、目視檢查、測試與提交）。
- 自製模型均先生成、檢視並保存各自 AI 三視圖。MM01／MM02 第一個未提交的圓柱輪廓已捨棄；本輪改用高度場，整組並排檢查後又加寬峰體、重輸出並重新 QA。

| ID | 自評／10 | 預覽路徑 | 實際工時 | 沒做到或仍待驗證 |
|---|---:|---|---:|---|
| MM01–MM02 | 6.6 | `art/exports/midground-v1/MM01/MM01_preview.png` | 約 0.17 小時 | 高度場峰體較寬，但岩面仍較單調，與三視圖的岩台、樹木差距明顯；Unity 霧與地形埋入未驗。各 12,464 三角面，低於 15,000。 |
| MM03–MM06 | 7.0 | `art/exports/midground-v1/MM03/MM03_preview.png` | 約 0.15 小時 | 四件為 2 三角面的 RGBA 遠景卡；透明排序、雙面材質和 MM05 連片接縫尚待 Unity 驗證。 |
| GR01／GR04 | 7.2 | `art/exports/ground-textures-v1/GR01/GR01_2x2-preview.png` | 約 0.08 小時 | 2048 Albedo／Normal／MaskURP 已輸出，各通道邊緣像素接縫為零；法線由來源亮度推算，地形中的 4 m 重複感與 URP 匯入未驗。 |
| VP04 | 7.0 | `art/exports/village-props-v1/VP04/VP04_preview.png` | 約 0.23 小時 | Git 可見歷史與工作樹中未找到 v009 幾何，故從三視圖重建；獨立瓦材質已製作。近看細節與 Unity 匯入仍待審。3,752 三角面，Blender QA 0 錯誤。 |
| TX02 | 7.2 | `art/exports/mountain-city-v1/TX02/TX02_preview.png` | 約 0.18 小時 | 鐘及撞木各有可旋轉樞軸，鐘面空白；4,772 三角面、Blender QA 0 錯誤。未取得可檢視的 TE05 預覽，無法宣稱完成並排視覺比較；Unity 匯入與動畫未驗。 |
| LF01–LF03 | 6.8 | `art/exports/life-v1/LF02/LF02_animation-preview.png` | 約 0.13 小時 | 飛鳥三色、蝴蝶兩色與雙翅動畫的 GLB 通道已檢查；LF03 透明光點與夜晚粒子參數已交付。飛鳥仍偏簡化，群體擺位及 Unity 動畫／粒子效能未驗。 |
| 全包檢查 | 6.7 | `art/exports/midground-v1/C-pack-review/C-midground-with-SK03.png` | 約 0.16 小時 | SK03、兩件石峰網格渲染與 MM03 樹丘卡已同畫面並排；石峰較暗且畫法與樹丘有落差，場景光照、霧與遮擋須再審。此圖是美術合成，非 Unity 實景。 |

- MM01／MM02 Blender 5.2.2 遊戲資產 QA 再驗均為 0 錯誤；UV 有意共用平鋪貼圖，底面 -1 m 預計埋入地形。MM03–MM06、VP04、TX02 的 QA 與輸出細節記於各資產 README／`model_info.json`。
- C 各項提交：`5b222762`、`27d4bbd6`、`5d97ceef`、`bf7f158d`、`551af947`、`48fe3eb4`、`1efce2f2`。D 部分尚未開始；依第 8 節另回原分支處理。

### C 部分補正（2026-11-13）

檢查第 7 節交付項目時發現 MM03–MM06 的初版對應漏了遠山脊。已於 `83c1de57` 校正為 MM03 樹丘、MM04 斷崖牆、MM05 梯田遠坡、MM06 遠山脊。MM04、MM05 使用原先已審的三視圖重新編號並重建；MM06 新選三視圖、製作 2048 × 1024 RGBA 輪廓卡，預覽為 `art/exports/midground-v1/MM06/MM06_preview.png`。三件皆為 2 個三角面，已重新輸出灰模、FBX、GLB 與 `model_info.json`。這項補正約 0.25 小時；自評 MM06 為 7.3／10。Unity 透明排序與場景距離仍未驗證。前述 C 表格的 MM05 接縫風險現應讀為 MM04 斷崖牆的連片接縫。

## D 部分｜舊件重做進度（2026-11-13）

- FE01：已於原分支 `art/codex-1108-rice-and-ferry` 提交並推送 `cbb8a43e`。Straight、Corner、End 的 v008 木棧橋改用 Josh 零件與材料函式，烘焙 Eli 的輔助圖；三段 Blender 網格的同向共面、退化面、零 UV 均為 0，FBX 1 mm 同向近共面為 0。比較預覽：`art/previews/valley-and-home-v1/FE01/v008/FE01_vs_FR04.png`（在原分支）。自評 7.5／10，實際工時約 0.6 小時；Unity 匯入、行走碰撞和水邊接縫未驗。
- FE02／FE03：已於同一原分支提交並推送 `164f1f41`。FE02 v008 補彎曲船舷、船首尾翹度、修補木片、竹編弧篷與舊布；FE03 v008 補貨箱、掛布、船槳等生活痕跡。新增部分使用 Josh 零件與材料函式及 Eli 烘焙清單。FBX 同向重疊面、零面積 UV 均為 0；新增圖集沒有 UV 衝突。舊船殼仍有 2 處極小同向重疊及雙面薄片，原有共用貼圖 UV 互疊。預覽：`art/previews/valley-and-home-v1/FE02/v008/FE02_threequarter.png`、`art/previews/valley-and-home-v1/FE03/v008/FE03_threequarter.png`（皆在原分支）。自評 FE02 7.3／10、FE03 7.2／10，實際工時合計約 0.8 小時；Unity 水面、浮力、同場比例與碰撞未驗。
- TX01：已於原分支 `art/codex-1108-tx01-ascension-board` 提交並推送 `f865cec9`。v005 榜與匾沿用 John MC01 共用 2048 Trim Sheet 及建模函式，屋瓦改黛瓦，木構改舊木，石台改兩層錯縫鑿面石塊，厚度由 0.32 m 增至 0.64 m；榜格與匾面空白。FBX、GLB 四次回匯均通過，網格退化面、零 UV、反向封閉面為 0。原有榜格與結構貼合仍有 493 組同向共面（v004 為 507 組），匾額銅邊有 20 組，須在 Unity 判斷是否可見閃面。預覽：`art/previews/mountain-city-v1/TX01/v005/TX01_Board_threequarter.png`、`TX01_Plaque_threequarter.png`（在原分支）。自評 7.4／10，實際工時約 0.6 小時；Unity 材質、碰撞與可讀距離未驗。
- C2：已於原分支 `art/codex-1108-c2-home-interior` 提交並推送 `8889472c`。外屋 v006 用 Josh VL 材料函式取樣重配舊灰牆、舊木、黛瓦、石基及窗紙；室內 v031 用 TI 舊木、石、紙材質與 VL 室內灰牆，保留 TI01–TI08d 家具原有材質。外屋與室內後門的門檻及兩側門框座標、尺寸均與 v005／v030 相同。外屋 FBX 回匯 506 網格／108,616 三角面，室內 FBX 回匯 551 網格／253,802 三角面，外屋 GLB 回匯通過。預覽：`art/previews/c2-home-interior-v1/v006/rear-door-v006.png`、`front-v006.png`、`interior-reardoor-v031.png`（在原分支）。自評 7.2／10，實際工時約 0.7 小時；Unity 中後門開關、碰撞、材質亮度、台基地面落差和手機效能未驗。室內整屋 FBX 僅作配置檢視，正式場景須採個別 TI 資產。
- D 部分四件均依 FE01 → FE02／FE03 → TX01 → C2 順序完成並推回各原分支。本報告只記錄已完成且已推送的工作；PR 審查及 Unity 實景驗收仍待核心組。
