# C3｜網頁外殼：雲境自訂 WebGL／PWA 範本

> 先讀 `00-operating-rules.md`。介面方向文件 `docs/art/ui-ux-direction-v1.md` 的第 2 節（色票、字體）、第 7 節（網頁外殼）、第 11 節（決定）必讀。
> 這項是**網頁程式＋插畫**，不是建模。00 規範第 5 節的建模階段不適用；第 6 節的視覺檢查循環**照樣要做**，改成看瀏覽器截圖。

## 1. 一句話任務

把 Unity 內建的 PWA 網頁範本換成雲境自己的外殼，包括載入畫面、進度、點擊入境、橫屏提示、加入主畫面、錯誤畫面。打開網頁的第一秒就要讓人覺得「這是一個精緻的修仙遊戲」。

## 2. 為什麼要做

- 網頁版是雲境的主要平台（手機瀏覽器加入主畫面就是 App）。玩家看到的第一個畫面就是載入頁。
- 現在是 Unity 範本：白底、Unity 標誌、藍色進度條。z1nnz 明確不要「簡單草率、很 AI 的網頁」。
- 遊戲約 100 MB，手機 4G 要載一陣子。這段時間是**留住玩家**的關鍵：要有好看、會動、說清楚進度的畫面。
- 已知的使用者痛點：
  1. 舊版本快取讓玩家玩到舊版（伺服器端已處理，見第 6 節）；
  2. 電腦版不知道要先點畫面才能用滑鼠；
  3. 手機直拿時畫面很小。

## 3. 位置

| 項目 | 路徑 |
|---|---|
| 工作樹 | `D:\yun-jing-rpg-workspace\yun-jing-rpg-web-shell-v1`（分支 `feature/webgl-shell-v1`） |
| 範本 | `apps/game/Assets/WebGLTemplates/YunJing/` |
| 預覽工具 | `tools/qingxi-webgl/shell-preview.mjs` |
| 截圖 | `artifacts/web-shell-v1/` |
| 插畫原稿 | `art/references/web-shell-v1/`（生圖原圖、提示詞） |
| 狀態 | `apps/game/Assets/WebGLTemplates/YunJing/PRODUCTION_STATUS.md` |

## 4. 起點：Unity 內建範本

複製這個資料夾當起點：
`D:\DevTools\Unity\6000.0.82f1\Editor\Data\PlaybackEngines\WebGLSupport\BuildTools\WebGLTemplates\PWA\`

**必須保留的樣板變數**（Unity 建置時會替換，少一個就會壞）：

| 檔案 | 變數 |
|---|---|
| `index.html` | `{{{ LOADER_FILENAME }}}`、`{{{ DATA_FILENAME }}}`、`{{{ FRAMEWORK_FILENAME }}}`、`{{{ CODE_FILENAME }}}`、`{{{ WORKER_FILENAME }}}`、`{{{ SYMBOLS_FILENAME }}}`、`{{{ JSON.stringify(COMPANY_NAME) }}}`、`{{{ JSON.stringify(PRODUCT_NAME) }}}`、`{{{ JSON.stringify(PRODUCT_VERSION) }}}`、`{{{ PRODUCT_NAME }}}` |
| `index.html` 的條件區塊 | `#if USE_THREADS`、`#if USE_WASM`、`#if SYMBOLS_FILENAME`、`#if SHOW_DIAGNOSTICS` 和對應的 `#endif` |
| `ServiceWorker.js` | 上面的各個 `*_FILENAME`，以及快取名稱的 `{{{JSON.stringify(COMPANY_NAME + "-" + PRODUCT_NAME + "-" + PRODUCT_VERSION )}}}` |
| `manifest.webmanifest` | 可以改成固定值（見第 5.8 節） |

`{{{ WIDTH }}}`、`{{{ HEIGHT }}}`、`{{{ BACKGROUND_FILENAME }}}` 可以不用（外殼是全螢幕）。

## 5. 功能規格

### 5.1 畫面結構

```
<body>
  #yj-shell（外殼，蓋在最上層）
     ├─ .yj-sky        天空漸層（純 CSS）
     ├─ .yj-mountains  2–3 層遠山插畫（WebP），視差微動
     ├─ .yj-clouds     2 層雲（CSS 動畫，左右緩慢漂移，30–60 秒一循環）
     ├─ .yj-title      「雲境」標題（SVG 或子集化字型）＋小字「青溪新手村」
     ├─ .yj-progress   墨線進度＋文字
     ├─ .yj-enter      「點擊入境」（載入完成才出現）
     ├─ .yj-install    加入主畫面提示（可關閉）
     └─ .yj-error      錯誤畫面（預設隱藏）
  #yj-rotate（直拿手機時的全畫面提示）
  #yj-resume（電腦版游標解除時的「點擊畫面繼續」）
  <canvas id="unity-canvas">（全螢幕）
</body>
```

### 5.2 載入畫面（打開網頁的那一刻）

- **0.1 秒內就要顯示**天空與山。插畫用最小的 WebP 先上，可用 `<link rel="preload">`。
- 雲層用純 CSS 動畫（`transform: translateX`），**不等 Unity**，一打開就會動。
- 「雲境」標題：
  - 用霞鶩文楷 TC（LXGW WenKai TC，SIL OFL 1.1，可從其 GitHub 下載），**子集化**到只剩用到的字，例如 `pyftsubset`，存成 WOFF2；
  - 或把標題做成 SVG 路徑。兩種擇一，總大小 ≤ 30 KB。
  - Noto Sans TC 在主場景工作樹 `apps/game/Assets/YunJing/Resources/Fonts/`，內文也要子集化。
  - 字型授權檔（OFL.txt）一起放進 `TemplateData/fonts/`。
- 色彩：天空從 `#EEF2F2`（月白）漸到 `#9FB8B8`；山從近到遠 `#46524F` → `#7C8784` → `#B8C4C2`；文字 `#1C1F1E`。

### 5.3 進度

- 一條水平墨線，寬約畫面 40%，用 SVG `stroke-dashoffset` 從左畫到右。線頭要有毛筆的粗細變化（用 SVG 路徑模擬，不是死板的直線）。
- 下方文字：`凝氣中… 43%`，第二行小字 `61.2 / 98.4 MB`。
  - MB 數用 `createUnityInstance` 的進度回呼乘以資料檔大小；
  - 抓不到大小就只顯示百分比。
- 進度文字分階段：
  - 0–90% 是「凝氣中…」；
  - 90–99% 是「築基中…」（Unity 解壓、初始化）；
  - 100% 是「入境」。
- **不准有 Unity 標誌**。不准有範本預設的頁尾、全螢幕按鈕、標題列。

### 5.4 點擊入境

- 載入完成後，墨線收縮成一個玉色圓點（`#5FA89A`，帶 `#7FE0D4` 光暈），下方出現「點擊入境」。圓點緩慢呼吸（1.8 秒循環）。
- 點擊（或觸控、按任意鍵）時：
  1. 要求全螢幕：`document.documentElement.requestFullscreen()`，失敗就忽略；
  2. 手機鎖橫向：`screen.orientation.lock('landscape')`，失敗就忽略；
  3. 電腦（非觸控）要求游標鎖定：對 canvas 呼叫 `requestPointerLock()`；
  4. 外殼用 0.6 秒的墨暈淡出（圓形遮罩從圓點往外擴散），露出遊戲。
- 這個點擊同時讓瀏覽器允許播放聲音。

### 5.5 電腦版：游標解除後

- 遊戲中按 Esc 會解除游標鎖定。監聽 `pointerlockchange`：解除時畫面中央淡入半透明的「點擊畫面繼續」（小玉點＋字）。
- 點了就重新鎖定並隱藏提示。
- 遊戲自己打開選單時不應該跳出這個提示。預留 JS 函式 `window.yjShell.setMenuOpen(bool)`，給 Unity 之後呼叫；選單開著時不顯示提示。

### 5.6 橫屏提示

- 觸控裝置且直向（`orientation: portrait` 媒體查詢）時，全畫面顯示：
  - 宣紙底色 `#F2ECDF`；
  - 中間一張紙捲插畫（SVG 或小 WebP）和一支手機轉 90° 的動畫圖示；
  - 文字「請橫置手機，入境更佳」。
- 轉成橫向就自動消失。

### 5.7 加入主畫面

- Android、桌面 Chrome：
  - 攔截 `beforeinstallprompt`，**載入完成後**在右上角顯示小按鍵「加入主畫面」（玉色小按鍵＋文字）；
  - 按了呼叫 `prompt()`。
- iOS Safari（沒有 `beforeinstallprompt`）：顯示一行說明「點分享 → 加入主畫面，即可全螢幕遊玩」，附分享圖示。
- 兩種都有「×」可關閉；關閉後記住：`localStorage`，**讀寫都包 try/catch**，私密瀏覽也不能壞。
- 已經是安裝後開啟（`display-mode: fullscreen` 或 `standalone`）時不顯示。

### 5.8 PWA 設定

- `manifest.webmanifest`：
  - `name`：「雲境」；`short_name`：「雲境」；
  - `display: fullscreen`；`orientation: landscape`；
  - `theme_color` 與 `background_color`：`#1C1F1E`；
  - `start_url: "./"`。
- 圖示：192、512 px PNG 各一，`purpose: "any maskable"`。
  - 圖案：玉色圓形中一朵雲紋，四周留 maskable 安全區（中間 80%）。
  - 用 imagegen 做草稿，最後**用 SVG 重繪**再轉 PNG，確保邊緣乾淨。
- `ServiceWorker.js`（**重要，見第 6 節**）。

### 5.9 錯誤畫面

| 情況 | 偵測 | 顯示（中文） |
|---|---|---|
| 不支援 WebGL2 | 建 canvas 試 `getContext('webgl2')` | 「此瀏覽器無法開啟雲境。請改用最新版 Chrome、Edge 或 Safari。」 |
| 載入失敗 | `createUnityInstance` 的 catch | 「入境失敗，可能是網路中斷。」＋「重新整理」按鍵 |
| 記憶體不足 | 錯誤訊息含 `memory`、`Out of memory` | 「裝置記憶體不足。請關閉其他分頁後重新整理。」 |

- 樣式和載入畫面一致：宣紙卡片、墨字、朱砂小印。
- 原始英文錯誤收在「技術細節」摺疊區裡（`<details>`），方便回報問題。

### 5.10 其他要求

- **效能**：外殼本身（HTML＋CSS＋JS＋插畫＋字型＋圖示）合計 **≤ 300 KB**。
  - 插畫用 WebP；有餘力就加 AVIF，用 `<picture>` 讓瀏覽器自己選。
- 不依賴任何外部 CDN 或字型服務，全部放本機。
- 安全區：用 `env(safe-area-inset-*)`，瀏海手機不能被切到。
- `prefers-reduced-motion: reduce` 時：雲停止漂移、墨暈改成淡入淡出。
- 縮放：`<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, user-scalable=no">`。
- 鍵盤：可以用 Tab 移到按鍵、Enter 觸發，按鍵要有清楚的焦點樣式。
- 程式碼：一個 `shell.js`、一個 `shell.css`，不用框架；註解寫清楚每段做什麼。

## 6. ServiceWorker 和快取（重要）

- 背景：之前用快取優先、名稱固定的 ServiceWorker，玩家一直玩到舊版本，連「清除網站資料」都找不到。
- 現在主場景工作樹的本機伺服器 `tools/qingxi-webgl/serve.mjs` 會：
  - 在建置變更時送 `Clear-Site-Data`；
  - 並**自己產生一份 ServiceWorker**：網路優先、以建置版本命名、啟動時刪除舊快取。
  - 可以讀它（只讀）當參考。
- 你的 `ServiceWorker.js` 要做到**一樣的行為**，這樣部署到正式網站（沒有 serve.mjs）時也不會卡舊版：
  1. **網路優先**：先抓網路；成功就更新快取；失敗才用快取（離線時還能開）。
  2. 快取名稱包含建置版本。用 Unity 替換後的檔名組合（`LOADER_FILENAME` 等），或 `PRODUCT_VERSION`，確保每次建置都不同。
  3. `activate` 時刪除所有名稱不同的舊快取，並 `clients.claim()`。
  4. `install` 時 `skipWaiting()`。
- 在 README 寫清楚：哪裡和 serve.mjs 一樣、哪裡不同。

## 7. 預覽工具與測試

### 7.1 `tools/qingxi-webgl/shell-preview.mjs`（不需要 Unity）

- `node tools/qingxi-webgl/shell-preview.mjs` 在 `127.0.0.1:4191` 起一個伺服器。
- 讀範本的 `index.html`，把樣板變數換成假值，`#if` 區塊照預設處理。
- 用一個假的 `createUnityInstance`：約 8 秒內把進度從 0 推到 100%，然後完成。
- 網址參數：
  - `?error=webgl`、`?error=load`、`?error=memory`：顯示三種錯誤；
  - `?slow`：進度變成 30 秒；
  - `?installed`：模擬已安裝。

### 7.2 截圖（`artifacts/web-shell-v1/`）

用任何可用的無頭瀏覽器（Playwright、Puppeteer、Edge `--headless --screenshot`），截以下畫面：

| 檔名 | 尺寸 | 狀態 |
|---|---|---|
| `desktop-0-first-frame.png` | 1920×1080 | 打開後 0.2 秒 |
| `desktop-1-loading.png` | 1920×1080 | 進度約 43% |
| `desktop-2-enter.png` | 1920×1080 | 點擊入境 |
| `desktop-3-resume.png` | 1920×1080 | 點擊畫面繼續 |
| `mobile-landscape-loading.png` | 844×390 | 進度約 43% |
| `mobile-landscape-install.png` | 844×390 | 加入主畫面提示 |
| `mobile-portrait-rotate.png` | 390×844 | 橫屏提示 |
| `error-webgl.png`、`error-load.png`、`error-memory.png` | 1280×720 | 三種錯誤 |

沒有可用的無頭瀏覽器時，寫明原因，並改用說明文字描述每個畫面。這種情況下 Gate 只能寫 UNVERIFIED。

### 7.3 視覺檢查

每張截圖都跑 00 規範第 6 節的 Visual Review。特別檢查：
- 第一幀有沒有白屏；
- 844×390 的手機橫向畫面字有沒有太小（最小 12 px）；
- 進度文字會不會跳動，數字要用等寬。

### 7.4 Unity 建置測試（這是全部任務中**唯一可以開 Unity** 的地方）

- 只在**你的工作樹**裡做。主場景工作樹 Claude Code 正在用，不准碰。
- 建立暫時的 Editor 腳本 `apps/game/Assets/_CodexTmp/Editor/ShellBuildTest.cs`：
  - 設 `PlayerSettings.WebGL.template = "PROJECT:YunJing"`；
  - 建一個只有攝影機的空場景；
  - 建置 WebGL 到 `<工作樹>/_codex_tmp/webgl-shell-test/`。
- 指令：

```
"D:\DevTools\Unity\6000.0.82f1\Editor\Unity.exe" -batchmode -quit -projectPath apps/game -buildTarget WebGL -executeMethod ShellBuildTest.Build -logFile _codex_tmp/unity-shell-test.log
```

- 用任何靜態伺服器打開建置結果，確認外殼和 Unity 都能載入。截一張 `artifacts/web-shell-v1/unity-build-loaded.png`。
- **測完刪除** `apps/game/Assets/_CodexTmp/`（含 `.meta`）。`ProjectSettings/` 若被 Unity 改到，**還原成原本內容**（`git diff` 確認沒有變更）。
- 第一次切換到 WebGL 平台會重新匯入資源，可能要 20–40 分鐘。超過 60 分鐘就停止，寫明沒有測。

## 8. 交付清單

- [ ] `apps/game/Assets/WebGLTemplates/YunJing/`：
  - `index.html`、`ServiceWorker.js`、`manifest.webmanifest`、`thumbnail.png`；
  - `TemplateData/shell.css`、`shell.js`、`art/`、`fonts/`（含 OFL.txt）、`icons/`；
  - `README.md`、`PRODUCTION_STATUS.md`。
- [ ] `tools/qingxi-webgl/shell-preview.mjs`
- [ ] `artifacts/web-shell-v1/` 的截圖
- [ ] `art/references/web-shell-v1/`：插畫原圖與提示詞
- [ ] README 包含：
  - 每個檔案的用途；
  - 樣板變數清單與保留理由；
  - 總大小明細（每個檔案 KB）；
  - ServiceWorker 行為；
  - 已測與未測的瀏覽器；
  - 已知限制。

## 9. 驗收標準

| 項目 | 標準 |
|---|---|
| 第一印象 | 第一幀就有山與雲，不是白屏；看不到任何 Unity 標誌或範本元素 |
| 大小 | 外殼合計 ≤ 300 KB（README 有明細） |
| 功能 | 第 5 節每一項都能在預覽工具裡看到 |
| 快取 | ServiceWorker 是網路優先、名稱含版本、會刪舊快取 |
| 相容 | Unity 建置測試通過，或寫明沒測的原因 |
| 手機 | 844×390 截圖中所有字 ≥ 12 px、按鍵 ≥ 44 px |
| 風格 | 和 C1 的 `shell/loading.png` 概念圖同一個方向 |

## 10. 不要做

- 不要改 `apps/game/Assets/YunJing/Editor/QingxiNoviceVillageBuilder.cs`（切換到新範本由 Claude Code 做）。
- 不要改 `tools/qingxi-webgl/serve.mjs`（只讀參考）。
- 不要引入 npm 套件到專案，除非只在 `tools/` 下當開發工具，並寫進 README。
