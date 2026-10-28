# 青溪水路回聲｜C 第一批

作者：Eli-0731／Codex。

本批包含 C01 圓形議事矮桌、C02 可翻面水情告示、C03 雙水桶、C04 取水扁擔，以及獨立村角回報展示。八件 AI 三視圖已先保存並檢視，參考與提示詞在 art/references/qingxi-water-report-c/。

從儲存庫根目錄執行 `node tools/qingxi-water-report-c/server.mjs`，開啟 http://127.0.0.1:4321，或直接開本目錄 index.html。選本機上游範例後，可回報、改選與取消；不會發放正式物品或貢獻，也不會改動共同世界。上游 outcomeId 暫用 fixture，未知結果不推定為完成。

在本目錄執行 npm ci、npm test、npm run test:browser；Playwright 固定 1.56.1。模型母稿由 Blender 4.5.3 LTS 製作，使用公尺，GLB 為 Y-up。模型回匯記錄在 batch1-manifest.json，近景、3×5 m 配置及眼高圖位於本包預覽目錄。

第二批補齊 C05–C08、完整尺寸、旗面變體及錄影。這是簡化模型與本機圖片互動原型，沒有低 LOD、專用碰撞或 Unity 整合；Unity 未編譯，未做實體手機或多人測試。
