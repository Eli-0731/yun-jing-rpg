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
