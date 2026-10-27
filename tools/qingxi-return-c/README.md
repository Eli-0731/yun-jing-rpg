# 青溪回村整理 C

Eli-0731／Codex 實作；工作包規劃 z1nnz／Codex。基於 main `0f1e023434c4d080d7394d5ed34dd9a0015d9d08`，指定分支 `feature/qingxi-village-return-v1`。

前一輪四件村口道具與三線索展示已先補交 [PR #34](https://github.com/z1nnz/yun-jing-rpg/pull/34)，commit `256299e`。本包不依賴該 PR，不複製其模型、不計入八件新物件。本輪先補交前置工作，實際補交投入約 40 分鐘（含環境準備、圖像工具重試、建模、測試與上傳等待），非文件估計的 14 小時工時認列。

第一批：C01 回村背籠、C02 分揀桌、C03 收納竹匣、C04 藥草布包，逐件 AI 參考已先保存並檢視，位置 `art/references/qingxi-return-c/`，完整提示詞與比例限制見 `review.json`。母稿與重建程式在 `art/source/qingxi-return-c/`，GLB 與回匯報告在 `art/exports/qingxi-return-c/`，實際渲染在本目錄 `previews/`。沒有第三方模型；嵌入材質紋理由本輪程式原創。

直接開 `index.html` 可整理樣本；啟用 PWA／離線快取請 `node tools/qingxi-return-c/server.mjs`，開啟 `http://127.0.0.1:4319`。在本目錄 `npm ci` 後可執行 `npm test` 與 `npm run test:browser`；後者用 Playwright 1.56.1 與本機 Chrome，可設 `CHROME_PATH`。

第一批可點選三份樣本，查看來源與用途，選保存／留待煉製，手札記錄去向，單步取消、重載保留。每份固定一份，同時只有一個去向；重複點擊不增量。鍵盤 Tab／Enter、滑鼠與橫向觸控可使用。所有樣本與紀錄只在本機 key `qingxi-return-c-v1`，未寫正式背包、靈石、宗門貢獻或委託。匯出的 JSON 只表達需服務端驗證的意圖，不含可自報入帳的數量或獎勵。

第二批待交：C05–C08 與其前置三視圖、委託展示去向、完整八件 3×4 m 尺度圖、橫向操作驗證及短錄影。模型為簡化原型；現有 QA 檢查 UV、退化面、有限座標及乾淨 GLB 回匯尺寸，不等於完整量產拓樸或引擎驗收。專用碰撞、低 LOD、Unity、實體手機與主場景接入尚未驗證。
