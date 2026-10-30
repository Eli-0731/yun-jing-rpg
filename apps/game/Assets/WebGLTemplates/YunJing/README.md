> **整合說明（Claude Code，2026-10-29）**
> - 這裡是 Codex C3（`D:\yun-jing-rpg-workspace\yun-jing-rpg-web-shell-v1`）的**快照**，已接入新手村的網頁建置：`QingxiNoviceVillageBuilder.BuildWebGL` 使用 `PROJECT:YunJing`。
> - `index.html`、`shell.js`、`shell.css`、`ServiceWorker.js` 是 Codex 的檔案。Codex 完成 C3 後，整份重新複製過來即可。
> - `TemplateData/entry.js`、`entry.css` 是 Claude Code 加的入境層：見聞卡片、撥雲、墨暈轉場（設計見 `docs/art/loading-experience-v1.md`）。重新複製時保留這兩個檔，以及 `index.html` 裡引用它們的兩行。

# 雲境 WebGL／PWA 外殼 v001

這是獨立工作樹中的網頁範本原型，尚未切入遊戲設定。`index.html` 保留 Unity 6 PWA 模板所需的 `LOADER_FILENAME`、`DATA_FILENAME`、`FRAMEWORK_FILENAME`、`CODE_FILENAME`、`WORKER_FILENAME`、`SYMBOLS_FILENAME`、`COMPANY_NAME`、`PRODUCT_NAME`、`PRODUCT_VERSION` 與 `USE_THREADS`、`USE_WASM`、`SYMBOLS_FILENAME`、`SHOW_DIAGNOSTICS` 條件，以免建置時丟失平台參數。是否被 Unity 接受仍待建置驗證。

`TemplateData/shell.css` 提供青溪初入境的玉紙墨銅配色與響應式版面；`shell.js` 管理進度、入境、橫屏、安裝提示、游標恢復和錯誤；`ServiceWorker.js` 使用網路優先、建置版本快取名稱，啟動刪除本套外殼舊快取。正式伺服器 `serve.mjs` 另有 Clear-Site-Data；本範本不送該標頭，因此不能把離線舊版回退當成等價行為。

背景源自本工作包 C1 的原創 AI 河谷概念，輸出為 960×530 WebP。它是插畫，不是遊戲中實際 3D 場景。圖示由幾何重新繪製 PNG，未複製外部標誌。

預覽：在此工作樹執行 `node tools/qingxi-webgl/shell-preview.mjs`，開啟 `http://127.0.0.1:4191/`。可加 `?error=webgl`、`?error=load`、`?error=memory`、`?slow`、`?installed`。預覽器不啟用 ServiceWorker、無 Unity 遊戲內容。

外殼目前 193,788 B，約 189.2 KiB，低於 300 KiB。最大單檔是 `riverside-v001.webp` 162,610 B。完整逐檔大小以檔案系統量測為準。尚未附字型檔，字體回退為系統字體；PNG maskable 圖示需再做安裝檢查；未在 Chrome、Edge、Safari 真機或 Unity 建置驗證。
