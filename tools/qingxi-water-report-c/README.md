# 青溪水路回聲｜C 模組化補交

作者：Eli-0731／Codex。依 main `4476c3719c7348751ce68f699e389a1111fa7a96` 的更新工作包補交。八個功能家族維持不變；重複家族現在有 **水桶 3／3、木牌 2／2、布旗裁切 2／2** 個可辨認形體，其餘五家族各一個精修版，共 12 個使用中的形體。空／半滿／滿、施工中／完成都是狀態，沒有充作新形體。

玩家可讀上游範例，在村角選三種回報、改選或取消；回報不改寫上游結果，不發放物品、貢獻或共同世界進度。15 句回應與八個規則情境在 [response-data.json](response-data.json)。沒有缺線索必須先補齊的門檻，未知結果不推定為完成。

## 開啟

在本目錄先執行 `npm ci`，再從儲存庫根目錄執行 `node tools/qingxi-water-report-c/server.mjs`。開啟 http://127.0.0.1:4321 。伺服器只綁 loopback，僅提供本包工具和自己的預覽／匯出資產。

- `index.html`：回報玩法、兩種錯落排列、12 個形體的近景、改選／取消和本機 JSON 匯入匯出。這頁用實際模型渲染圖互動，也可直接開檔。
- [walk3d.html](walk3d.html)：實際 GLB 3D 走查，需本機伺服器。1.7 m 固定眼高，WASD／方向鍵移動、Q/E 轉向、拖曳環視；有觸控按鈕。可換 A/B 排列、南／北眼高、水情、ID 標籤。三個桶使用 Empty／HalfFull／Filled 形態鍵，旗面會換成實際完成狀態 GLB。

Three.js 固定 **0.186.1**，Playwright 固定 **1.56.1**。Three.js 是第三方程式庫，保留 npm 套件的 MIT 授權，不計入原創模型。先開回報頁完成首次連線快取，再進入 3D，即可離線重開；離線快取不代表正式離線服務端。

## 形體、狀態與接口

| 家族 | 已完成的形體 | 各形體狀態 | 共用接口 |
|---|---|---|---|
| C03 | 直身 16 片高桶／帶耳八角矮桶／鼓腹、雙腳、竹提梁桶 | 各自空、半滿、滿 | GroundOrigin；Lift_L/R = (±0.16, 0, 0.30) m |
| C05 | 缺口直木牌＋方柱／錯位雙木板＋Y 分叉柱腳 | 乾、部分回潤、回潤 | GroundSocket=(0,0,0)，40 mm 方舌入土 0.12 m；PanelMount=(0,0,0.46) |
| C06 | 深 V 燕尾／不對稱斜切＋削角底緣 | 開口圈＋兩條施工線／閉口圈＋水紋完成圖樣 | 中央旗桿、0.46 m 橫梁；ClothTie 左中右=(−0.16/0/+0.16,0,0.79) |

接口座標使用 Blender X/Y/Z 公尺；GLB 為 Y-up。每個空節點名稱為 `變體ID__接口名`，避免 Blender 自動序號造成名稱碰撞；全部已回匯核對位置。旗面的兩個完成 GLB 是狀態，不新增形體計數。低桶外寬含耳座，牌高含地下方舌；尺寸以實測為準。

| ID | 形體 | 寬 × 深 × 高（m） | 三角形上限 | 材質 |
|---|---|---|---:|---:|
| C01 | 村民議事矮桌 | 1.100 × 1.097 × 0.630 | 2,020 | 6 |
| C02 | 可翻面水情告示 | 0.720 × 0.360 × 1.110 | 2,092 | 6 |
| C04 | 竹製取水扁擔 | 1.256 × 0.062 × 0.310 | 2,424 | 3 |
| C07 | 修渠手工具箱 | 0.485 × 0.280 × 0.333 | 2,420 | 4 |
| C08 | 共修紀錄石牌 | 0.600 × 0.260 × 0.920 | 1,378 | 3 |
| C03_tall_01 | 直身高桶 | 0.372 × 0.342 × 0.420 | 2,462 | 4 |
| C03_low_02 | 八角矮桶 | 0.450 × 0.440 × 0.323 | 1,630 | 5 |
| C03_bail_03 | 提梁鼓腹桶 | 0.365 × 0.365 × 0.568 | 4,082 | 5 |
| C05_notch_01 | 缺口木牌 | 0.300 × 0.140 × 0.820 | 756 | 6 |
| C05_fork_02 | 分叉柱腳木牌 | 0.360 × 0.140 × 0.740 | 784 | 6 |
| C06_fork_01 | 燕尾布旗 | 0.460 × 0.220 × 0.850 | 1,536 | 6 |
| C06_slant_02 | 斜切布旗 | 0.460 × 0.220 × 0.850 | 1,540 | 6 |

合計三角形上限 **23,124**，含旗面兩種圖樣的母稿節點；單一狀態只顯示一套圖樣。三個桶各有兩個形態鍵。沒有用旋轉、縮放、鏡射、改色或舊分揀桌冒充新形體。

## 參考、母稿與組裝

七個新形體皆先生成、保存並目視檢查正／側／背三視圖，再寫網格。參考在 [variants](../../art/references/qingxi-water-report-c/variants/)，完整提示詞與推定細節在 [variant-review.json](../../art/references/qingxi-water-report-c/variant-review.json)：包含 AI 尺寸箭頭、側邊旗桿與吊點不一致時的處理。生成工具為內建 imagegen，全部網格與 128×128 材質圖由本包製作。

新版母稿 [WaterReportC_variants.blend](../../art/source/qingxi-water-report-c/WaterReportC_variants.blend)，七個變體各自 Collection；五件單一精修家族沿用本包第二批母稿。重建：`blender -b --python-exit-code 1 --python art/source/qingxi-water-report-c/build_variants.py`，再 `python art/source/qingxi-water-report-c/variant_delivery.py`。Blender 固定 4.5.3 LTS。

獨立 GLB 在 [variants](../../art/exports/qingxi-water-report-c/variants/)；七個形體、兩個旗面完成狀態、A/B 兩個實際組裝 GLB，另沿用 C01/C02/C04/C07/C08。原第一／二批母稿及舊 C03/C05/C06 留作階段記錄，不列入新版最低變體數。

兩個 3×5 m 排列都將同族物件錯開位置，保留 X=0.52–1.50 m 的通道。每組都有實際俯視與南／北兩張 1.7 m 眼高圖：

- [排列 A 標 ID 俯視組裝圖](../../art/previews/qingxi-water-report-c/variants/assembly-id-plan-a.svg)／[南側](../../art/previews/qingxi-water-report-c/variants/eye-a-south-1p7m.png)／[北側](../../art/previews/qingxi-water-report-c/variants/eye-a-north-1p7m.png)。
- [排列 B 標 ID 俯視組裝圖](../../art/previews/qingxi-water-report-c/variants/assembly-id-plan-b.svg)／[南側](../../art/previews/qingxi-water-report-c/variants/eye-b-south-1p7m.png)／[北側](../../art/previews/qingxi-water-report-c/variants/eye-b-north-1p7m.png)。

主路在樣片之外。物件實例 AABB 沒有非預期相交；C07 放在 C01 桌面是刻意配置，木牌舌端刻意入土。走查採保守的整件水平包圍盒與 0.16 m 玩家半徑，不是逐三角形或 Unity 碰撞；不可據此宣稱主場景碰撞已完成。

## 驗證與未完成項

`npm test`：14 項狀態規則。`npm run test:browser`：原回報、鍵盤、改選取消、重複點選、壞 JSON、保存失效、離線與 844×390 觸控模擬，再檢查 A/B 換排列不改本機決定。`npm run test:walk3d`：兩組各載入 12 物件、三桶形態鍵、南北眼高、兩條通道行走、石牌擋路、ID 標示、實際模擬觸控長按與離線 3D 重載。測試用本機 Chrome，可設 CHROME_PATH；錄影元件用 Playwright 對應版本。

模型檢查包含閉合結構、UV、零面積面、回匯尺寸、所有接口位置、兩個水面形態鍵與旗面狀態圖樣。水面為刻意開放表面。報告：[manifest.json](../../art/exports/qingxi-water-report-c/variants/manifest.json)、[組裝／狀態檢查](../../art/previews/qingxi-water-report-c/variants/assembly-check.json)、[3D 實測](../../art/previews/qingxi-water-report-c/variants/walk3d-report.json)。截圖與 `walkthrough-3d.webm` 在同一預覽目錄。

**工作包要求的形體變體已全數補齊，沒有以狀態抵件數。** 未完成：低 LOD、引擎專用碰撞、Unity 整合／編譯、實體手機效能、獨立真人全程驗收、正式跨場景收據及多人。B outcomeId 仍以本機別名展示，不依賴未合併分支；正式資產由核心組服務端驗證。
