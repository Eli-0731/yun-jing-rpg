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
