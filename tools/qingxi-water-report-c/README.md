# 青溪水路回聲｜C 兩批交付

玩家帶回水路線索與工程結果，在 3×5 m 議水村角選擇「先告知缺水」「請工匠看破槽」「先保護育幼區」，可重選或取消。水情翻板、水桶、施工旗與濕度牌依上游範例顯示乾燥、部分恢復或恢復；玩家回報不會自行改寫工程結果，也不發放物品、貢獻或獎勵。

分支 `feature/qingxi-water-report-c`，基準 main `149b8657518c31819ce130441ec34de98f514c92`。第一批 包含 C01–C04 與最小展示；第二批補齊 C05–C08、變體、八件配置、橫向觸控、尺寸與錄影。此包只改自己的五個資產／工具目錄。

作者：Eli-0731／Codex。回應文案與八個規則情境保存在 [response-data.json](response-data.json)。

## 開啟與互動

在儲存庫根目錄執行 `node tools/qingxi-water-report-c/server.mjs`，開啟 `http://127.0.0.1:4321`。伺服器只綁 loopback，僅提供本包工具及其預覽／匯出資產。也可直接開本目錄 `index.html`；Service Worker 離線快取需 localhost 或 HTTPS，首次載入後可離線重開。

先切換上游範例，再選回報。可點告示、水桶、旗面、濕度牌、石牌及桌邊標示查看回饋，也可開八件近景。此 PWA 使用實際模型渲染圖搭配可點標示，沒有即時 GLB 視窗。JSON 匯入錯誤保持原狀，匯出僅含本地意圖；重複同選項不新增紀錄。儲存空間不可用時仍可在當次頁面操作。

輸入為 `{observationIds, outcomeId}`。已知線索 `cracked_sluice`、`silt_buildup`、`nursery_tracks`；B 的 outcomeId 尚未定稿，本包 `clear_silt`、`restore_channel`、`protect_nursery` 只是 fixture 別名。未知結果不推定為完成，沒線索仍可回報。未直接依賴 A/B 未合併分支，詳見 [接線契約](handoff-contract.md)。

## 八件原創模型

先以內建 imagegen 生成每件正／側／背參考，保存並目視檢查，再用 Blender 4.5.3 LTS 建模。三視圖與完整提示詞／參考限制在 [參考目錄](../../art/references/qingxi-water-report-c/) 的 `review.json`。C04 成功參考使用 C03 水桶建立家用取水情境；C04 GLB 只有扁擔及其附件，水桶不重複計件。沒有採用第三方網格。

尺寸為實際本機包圍盒，單位 m，依 Blender X 寬、Y 深、Z 高；GLB 為 Y-up。角色尺度 1.75 m。

| ID | 模型 | 寬 × 深 × 高 | 三角形 | 材質 |
|---|---|---|---:|---:|
| C01 | 圓形議事矮桌 | 1.100 × 1.097 × 0.630 | 2,020 | 6 |
| C02 | 可翻面水情告示 | 0.720 × 0.360 × 1.110 | 2,092 | 6 |
| C03 | 雙水桶組 | 0.673 × 0.319 × 0.558 | 3,172 | 5 |
| C04 | 竹製取水扁擔 | 1.256 × 0.062 × 0.310 | 2,424 | 3 |
| C05 | 田邊濕度木牌 | 0.280 × 0.090 × 0.770 | 824 | 4 |
| C06 | 水渠施工布旗 | 0.460 × 0.220 × 0.850 | 1,256 | 5 |
| C07 | 修渠手工具箱 | 0.485 × 0.280 × 0.333 | 2,420 | 4 |
| C08 | 共修紀錄石牌 | 0.600 × 0.260 × 0.920 | 1,378 | 3 |

總計 15,586 三角形。C05 高度含地下尖端 0.12 m，地上約 0.65 m。C02 保留 `StatusPivot` 可繞 X 轉 π；C03 兩片水面保留 `Filled` 形態鍵；C06 額外 `C06-complete.glb` 為同一件的完成材質變體，8 件共 9 個 GLB。原創 128×128 材質圖已封裝。沒有用舊分揀桌、背籠或手札換名計件。

母稿 [WaterReportC_batch2.blend](../../art/source/qingxi-water-report-c/WaterReportC_batch2.blend)，第一批母稿另存。重建：`blender -b --python-exit-code 1 --python art/source/qingxi-water-report-c/build.py -- --batch 2`。模型用公尺、Blender Z-up 正面 −Y，在排列前按本機原點個別匯出。

## 檢查與證據

在本目錄 `npm ci` 後，執行 `npm test` 及 `npm run test:browser`。Playwright 固定 1.56.1，使用本機 Chrome，可設 `CHROME_PATH`。`RECORD_VIDEO=1` 可重新錄影。模型重建會執行幾何、UV、尺寸與 GLB 回匯檢查。

- 狀態測試 **14/14**：含八個規則情境、18 組情境／選項、改選取消保留上游、未知 ID、壞資料與文案資料一致性。
- 根目錄 API `npm test` **64/64**。
- Chrome 驗收 **17 項通過**：鍵盤、重複點選、保存重載、三種水情、未知結果、物件回饋、近景、匯入匯出、離線、儲存失效、直接開檔、伺服器路徑範圍；沒有非 GET 頁面請求或頁面錯誤。
- 模型八件回匯通過，C02 轉軸、C03 兩個形態鍵及 C06 材質變體保留。兩片水面刻意為開放表面，其餘結構無非預期邊界。詳細數據在 [batch2-manifest.json](../../art/exports/qingxi-water-report-c/batch2-manifest.json)。

[預覽目錄](../../art/previews/qingxi-water-report-c/) 包含八件近景、乾燥／部分恢復／恢復配置、1.7 m 眼高、3×5 m 平面、`dimensions.svg` 尺寸圖、1280×720 桌面與 844×390 觸控模擬截圖、`browser-report.json`、約 8.92 秒 1280×720 `walkthrough.webm`。模型在配置中保留 X=0.52–1.50 m 的通道；主路在配置範圍外，沒有改動正式主場景。

## 未完成與整合限制

這些是簡化模型原型，尚未製作低 LOD、專用碰撞體或動畫。PWA 為本機圖片互動展示，沒有正式服務端、多人、主 HUD 或 Unity 整合；Unity 未編譯。844×390 是 Chrome 觸控模擬，沒有實體手機效能與正式場景路徑實測，也沒有獨立真人驗收。正式發獎、工程收據、共同世界與取消可逆性須由核心組服務端驗證。