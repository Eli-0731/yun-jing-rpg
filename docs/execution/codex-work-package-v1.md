# Codex 工作包 v1（2026-10-29）

> 由 z1nnz 交辦、Claude Code 撰寫。這份是 Codex 在新手大世界 **P1（新手村完整版）**期間的**全部工作**，共 6 項，依優先順序排列。
> 每一項都有自己的工作樹或輸出資料夾，彼此不重疊，也不和 Claude Code 正在改的檔案重疊。

---

## 第一部分：先讀這些（開始任何一項之前）

### 1. 專案是什麼

- 《雲境》是手機優先的修仙 RPG：Unity 6（6000.0.82f1，URP）做用戶端，NestJS 做伺服器。
- 玩家創角後的前 10 個現實日都在「新手大世界」探索；第 10 天測出資質，再選宗門。
- 不能「付費變強」，只賣外觀。
- 美術目標：參照原神璃月（臨水聚落、石峰、雲霧、竹林、古樹），但要更好看，而且是雲境自己的風格。
- 現在可玩的場景是「青溪新手村」：
  - Windows 版和瀏覽器 PWA 版都能玩。
  - 瀏覽器版網址 `http://127.0.0.1:4190/`，由 `tools/qingxi-webgl/serve.mjs` 提供，在主場景工作樹裡。

### 2. 必讀文件（在主場景工作樹 `D:\yun-jing-rpg-workspace\yun-jing-rpg-main-scene-abc-v1`）

| 文件 | 為什麼要讀 |
|---|---|
| `docs/art/yunjing-visual-language.md` | 全專案的美術語言 |
| `docs/art/modeling-style-spec-v1.md` | **建模規格**：色票、PBR、貼圖密度、面數預算、LOD、審圖燈光、命名。草案，但你的工作**先照它做**，等於試用這份規格；做不到或不合理的地方寫進回報 |
| `docs/art/ui-ux-direction-v1.md` | 介面與操作方向（任務 C1、C3、C6 必讀） |
| `docs/execution/2026-10-29/14-grounding-spec.md` | 接地規格：原點、底部高度、接口 |
| `docs/execution/novice-world-master-plan.md` | 整體計畫，知道你的工作放在哪裡 |
| `art/incoming/dondon/StarterHouse/v004/`、`art/incoming/dondon/EnvironmentTransitionKit/v001/` | 協作者 joshsu54 的成品，你做的東西要和它們放在一起不突兀 |
| `artifacts/qingxi-novice-village/*.png` | 新手村目前的遊戲內截圖（00–15） |

### 3. 你可以用的工具

- **生圖**：你的內建 imagegen。三視圖、概念圖、參考圖都用它。
- **Blender 5.2**：`C:/Program Files/Blender Foundation/Blender 5.2/blender.exe`。建模一律用 Python 腳本，可以 `-b --factory-startup` 無頭重跑。
- **你的技能**：`C:\Users\User\.codex\skills\`。特別是：
  - `blender-asset-qa`（`scripts/qa_check.py`，`profile=game`）
  - `blender-export-pipelines`
  - `blender-pbr-materials`
  - `blender-texture-baking`
  - `blender-game-optimization`
  - `game-ui-ux`
- **Node 22**：做網頁外殼和測試。
- **Unity**：`D:\DevTools\Unity\6000.0.82f1\Editor\Unity.exe`。**除了 C3 第 6 步的建置測試，不要開 Unity**，避免和 Claude Code 搶同一份專案。

### 4. 所有任務共同的規則（違反就要重做）

1. **不要 git commit、不要 push、不要開 PR。**
   - 完成後由 Claude Code 檢查，再以 z1nnz 的名義提交。
   - 不加任何 AI 署名行（Co-Authored-By、Generated with…）。
2. **只在該任務指定的工作樹或資料夾裡寫檔案。** 不要碰別的工作樹，尤其是 `yun-jing-rpg-main-scene-abc-v1`（Claude Code 正在用）。
3. **不要改**以下東西，除非任務明確要求：
   - `apps/game/Assets/YunJing/Editor/`、`Runtime/`
   - 任何 `.unity` 場景、`ProjectSettings/`、`Packages/`
4. **不覆蓋舊檔**。新版本用新檔名，例如 `_v002`。
5. **自製模型一律先做 AI 三視圖**（正、側、背），檢視後存檔，**才開始建模**。
   - 三面互相矛盾就重新生成。
   - 看不清的部分在 README 標「推定設計」。
6. 每件模型都要：
   - 跑 QA，錯誤全部修好，警告逐條寫接受理由；
   - GLB／FBX 回匯驗證；
   - 預覽圖附 1.75 m 人形尺；
   - 寫 `model_info.json` 和誠實的 README。
7. **Unity FBX 匯出設定**：`axis_forward=-Z`、`axis_up=Y`、`apply_scale_options=FBX_SCALE_ALL`、`bake_space_transform=True`。
   - 匯出前在 Blender 確認物件旋轉為 0、縮放為 1。
   - 之前有協作者的根物件帶了 90° 旋轉和 ×100 縮放，造成場景裡的模型轉向又放大。
8. **做不到就停下來寫清楚卡在哪裡**，例如生圖額度用完、Blender 錯誤。不要用別的方法假裝完成，不要把佔位圖說成成品。
9. 生圖額度有限。**依下面的優先順序做**，額度用完時先做不需要生圖的部分，例如建模腳本、網頁程式、文件。

---

## 第二部分：任務清單（依優先順序）

| 順序 | ID | 任務 | 位置 | 需要生圖 |
|---|---|---|---|---|
| 1 | **C1** | 介面概念圖三套 | `D:\yun-jing-rpg-workspace\yun-jing-ui-concepts-v1\`（輸出資料夾，不是 git） | 多（約 13 張） |
| 2 | **C2** | 借住處室內模組 IK01–IK09 | `D:\yun-jing-rpg-workspace\yun-jing-rpg-interior-kit-v1`（分支 `feature/lodging-interior-kit-v1`） | 中（三視圖） |
| 3 | **C3** | 網頁外殼（自訂 WebGL／PWA 範本） | `D:\yun-jing-rpg-workspace\yun-jing-rpg-web-shell-v1`（分支 `feature/webgl-shell-v1`） | 少（1–2 張插畫） |
| 4 | **C4** | 遠景石峰與雲霧套件 | `D:\yun-jing-rpg-workspace\yun-jing-rpg-distant-peaks-v1`（分支 `feature/distant-peaks-kit-v1`） | 中 |
| 5 | **C5** | 丹房工作桌補 PBR 貼圖（v002） | `D:\yun-jing-rpg-workspace\yun-jing-rpg-alchemy-table-pbr-v1`（分支 `feature/alchemy-table-pbr-v1`） | 少 |
| 6 | **C6** | 圖示與介面素材定稿 | 同 C1 資料夾下的 `final/` | 多 |

**C6 要等 z1nnz 從 C1 選定一套方向才能開始。** C1 做完先停在這裡回報；z1nnz 選好前先做 C2–C5。

---

## C1｜介面概念圖三套

**完整說明**在主場景工作樹的 `docs/execution/ui-concept-codex-brief.md`，照它做。重點：

- 3 套方向：
  - A：玉、紙、墨、銅
  - B：極簡墨線
  - C：暗色絹與舊金（對照組）
- 每套 4 張：手機探索、手機戰鬥、電腦版、圖示表。另外 1 張網頁載入畫面。都是 1920×1080 PNG。
- 圖上的中文要是正確繁體。生圖若產生錯字，在 README 標出，不能假裝正確。
- 不能模仿任何現有遊戲的介面外觀（原神、鳴潮等）。
- README 要寫每套的優缺點、每張的提示詞、做不到的地方。

**做完 C1 就回報**，讓 z1nnz 先挑方向。

---

## C2｜借住處室內模組 IK01–IK09

**完整說明**在該工作樹的 `docs/execution/p1-codex-interior-kit-brief.md`，照它做。重點：

- 9 種模組：
  - 地板、牆板 1 m／2 m、窗牆、門牆、門扇、柱、樑與天花、牆角收邊
  - 1 m 格線，尺寸與面數上限都寫在說明裡
- 外觀要和 joshsu54 的 StarterHouse v004 一致，看起來像同一棟房子的內部。
- 交付：
  - 三視圖：`art/references/lodging-interior-kit-v1/`
  - 建模腳本：`tools/art/build_lodging_interior_kit_v1.py`
  - 母稿、GLB、Unity FBX，每件一份 `model_info.json`
  - 回匯報告、每件預覽
  - **一張組裝樣張**：7×5×3.2 m 房間，從門口 1.7 m 眼高往內看
- 補充（說明裡沒有的）：材質照建模規格第 3 節，要有 BaseColor／Normal／ORM 貼圖。不能只交純色。

---

## C3｜網頁外殼：自訂 WebGL／PWA 範本

### 背景

現在網頁版用 Unity 內建的 PWA 範本：白底、Unity 標誌、藍色進度條，一看就是範本。z1nnz 說「不能就是簡單草率的很 AI 的那種網頁」。這項要做一套雲境自己的範本，照介面方向文件第 7 節。

### 起點

複製 Unity 內建範本當基礎，**保留它的樣板變數和 PWA 功能**：

`D:\DevTools\Unity\6000.0.82f1\Editor\Data\PlaybackEngines\WebGLSupport\BuildTools\WebGLTemplates\PWA\`

（`index.html`、`ServiceWorker.js`、`manifest.webmanifest`、`TemplateData/`）

### 要做的檔案（都放在 `apps/game/Assets/WebGLTemplates/YunJing/`）

| 檔案 | 內容 |
|---|---|
| `index.html` | 外殼頁面：載入畫面、進度、點擊入境、錯誤畫面、橫屏提示 |
| `TemplateData/shell.css` | 所有樣式；顏色用 CSS 變數，名稱照介面方向文件 2.1 節（`--ink-900`、`--paper-100`、`--jade-500`……） |
| `TemplateData/shell.js` | 外殼邏輯（見下） |
| `TemplateData/art/` | 插畫（WebP，另附 AVIF 更好）、`favicon`、PWA 圖示 192／512 px |
| `ServiceWorker.js` | **網路優先**（先抓網路，失敗才用快取）；快取名稱要包含建置版本 `{{{ PRODUCT_VERSION }}}`，或用 Unity 的建置檔名當版本；啟動時刪除舊版本的快取 |
| `manifest.webmanifest` | 名稱「雲境」、`display: fullscreen`、`orientation: landscape`、主題色 `#1C1F1E`、背景色 `#1C1F1E` |
| `thumbnail.png` | Unity 範本選單用的縮圖 |
| `README.md` | 怎麼用、每個檔案做什麼、怎麼本機預覽、已知限制 |

### 功能要求

1. **載入畫面**：
   - 遠山雲霧的分層插畫，用 imagegen 生成後切成 2–3 層，或用 CSS 漸層加 1 張插畫。
   - 雲層用純 CSS 動畫緩慢飄動，Unity 還沒開始載入就要會動。
   - 中央「雲境」標題：可用 Noto Serif TC（`apps/game/Assets/YunJing/Resources/Fonts/` 裡有）。
     - 網頁要**子集化**，只放用到的字，例如 `pyftsubset`；檔案越小越好。
     - 或者把標題做成 SVG／圖片。
2. **進度**：
   - 一條墨線由左往右畫出（SVG `stroke-dashoffset`）。
   - 下方寫「凝氣中… 43%」，並顯示已下載與總 MB 數。
   - 用 `createUnityInstance` 的進度回呼。
3. **點擊入境**：
   - 載入完成後，墨線收成一個玉色圓點，顯示「點擊入境」。
   - 點擊時：
     - 要求全螢幕（手機和桌面都試，失敗就忽略）；
     - 桌面版要求游標鎖定；
     - 淡出外殼，露出遊戲畫面。
   - 桌面版遊戲中按 Esc 解除游標後，畫面中央顯示「點擊畫面繼續」，點了再鎖定。
4. **橫屏提示**：手機直拿時，全畫面顯示紙捲風格的「請橫置手機」。不要用系統預設文字樣式。
5. **加入主畫面**：
   - Android 和桌面 Chrome：攔截 `beforeinstallprompt`，在載入完成後顯示一個小的「加入主畫面」按鈕。
   - iOS Safari：顯示「分享 → 加入主畫面」的文字說明。
   - 兩者都可以關掉，關掉後記住（`localStorage`，用 try/catch 包住）。
6. **錯誤畫面**：載入失敗或瀏覽器不支援 WebGL2 時，用同樣風格寫中文說明和建議（換瀏覽器、重新整理）。英文錯誤細節收在「技術細節」摺疊區裡。
7. **不能有 Unity 標誌**，也不能有範本預設的頁尾。
8. **效能**：
   - 外殼本身（HTML＋CSS＋JS＋插畫＋字型）**合計 ≤ 300 KB**；
   - 不依賴任何外部 CDN，所有檔案放本機。
9. **安全區**：用 `env(safe-area-inset-*)`，瀏海手機不能被切到。
10. **減少動態**：使用者設定 `prefers-reduced-motion` 時，關掉雲層飄動。

### 預覽與測試

- 做一個不需要 Unity 的預覽：`tools/qingxi-webgl/shell-preview.mjs`。
  - 用 Node 起一個本機伺服器。
  - 把範本的樣板變數換成假值。
  - 模擬 0→100% 的進度（約 8 秒），然後顯示「點擊入境」。
  - 網址加 `?error` 時顯示錯誤畫面。
- 用瀏覽器截圖（1920×1080、手機橫向 844×390、手機直向 390×844），放在 `artifacts/web-shell-v1/`。
- **建置測試**（這項唯一可以開 Unity 的地方，而且只在你自己的工作樹裡）：
  - 用 `-batchmode -quit -executeMethod`，自己寫一個暫時的 Editor 腳本設定 `PlayerSettings.WebGL.template = "PROJECT:YunJing"`，再建置一個空場景的 WebGL。
  - 確認範本能被 Unity 接受、頁面能載入。
  - **測完刪除那個暫時腳本**，並在 README 寫結果。
  - 如果 Unity 開不起來或建置太久（超過 30 分鐘），就跳過，寫清楚沒測。

### 不要做的

- 不要改 `QingxiNoviceVillageBuilder.cs`。把建置設定改成用這個範本，由 Claude Code 合併時處理。
- 不要改 `tools/qingxi-webgl/serve.mjs`。它負責清除舊快取，Claude Code 會配合你的 ServiceWorker 調整。

---

## C4｜遠景石峰與雲霧套件

### 背景

新手村現在往外看是平滑的綠色山丘和灰色天空，沒有璃月那種「層層石峰、雲霧」的感覺。這項做遠景用的低面數石峰與雲霧片，放在村子 80–400 m 外，作為背景。

### 參考

- 主場景工作樹 `docs/art/world-four-directions-and-quality-bar.md`，以及它提到的五張世界方向圖。
- 協作者的 `LayeredCliff_v001`（`apps/game/Assets/YunJing/Models/CollaboratorWorldV1/`）：材質和岩層方向要和它相容。

### 要交的模組

| ID | 名稱 | 尺寸（約） | LOD0 上限 | 說明 |
|---|---|---|---|---|
| DP01 | 高石峰 A | 底 30 m、高 90 m | 3,000 | 喀斯特式直立石峰，頂部有少量樹叢剪影；岩層橫紋明顯 |
| DP02 | 高石峰 B | 底 25 m、高 70 m | 3,000 | 和 A 輪廓明顯不同，例如歪頂、裂成兩股 |
| DP03 | 石峰群 | 底 60 m、高 50 m | 5,000 | 3–5 根矮峰連在一起，用在中景 |
| DP04 | 遠山稜線 | 寬 200 m、高 60 m | 2,500 | 一片連綿的山脊剪影，背面不需要細節 |
| DP05 | 峰頂松 | 高 8 m | 1,200 | 長在石峰頂或崖邊的歪松，遠看是剪影；可以是交叉面片加貼圖 |
| DP06 | 雲霧片（3 種） | 寬 40／80／120 m | 每片 ≤ 50 | 半透明雲帶，貼圖要有柔邊；Unity 裡用 Alpha 混合、不寫深度 |

### 做法要求

- 先用 imagegen 做：
  - 整組遠景的**概念圖** 1 張：從新手村廣場往西北看，近景是村子，遠景是石峰與雲霧；
  - DP01–DP05 的三視圖。
  - 存到 `art/references/distant-peaks-kit-v1/`。
- Blender 腳本：`tools/art/build_distant_peaks_kit_v1.py`。
  - 石峰可以用置換、雕刻或幾何節點做出岩層，最後**一定要減面到預算內**。
  - 細節靠法線貼圖和 AO。
- 貼圖：
  - 遠景物件用 256 px/m 太浪費；石峰整件 1 張 1024 貼圖即可。
  - 色調照建模規格的灰青石色票，**往遠處偏藍、降低對比**（空氣透視），但不要直接烘成霧色。霧由 Unity 後處理加。
- LOD：
  - 石峰要有 LOD1（50%）。
  - 不需要 LOD2：會另外用 impostor 或直接被霧蓋住。
- 原點：底部中心，`ground_z = 0`。石峰底部要往下延伸 5 m，埋進地形，避免露出懸空的邊。
- 碰撞：**不需要**。遠景走不到，在 `model_info.json` 寫 `"collision": "none"`。
- 預覽：
  - 每件 3/4 視角；
  - 一張**組合樣張**：在 Blender 裡用這些模組排出概念圖的構圖。相機放在原點 1.7 m 高、往西北看，加世界霧（Volume Scatter 或 Mist pass），和概念圖並排比較。
- 交付路徑：
  - `art/source/distant-peaks-kit-v1/distant-peaks-kit-v1.blend`
  - `art/exports/distant-peaks-kit-v1/DPxx_*.glb`、`*_model_info.json`、`roundtrip-report.json`、`README.md`
  - `apps/game/Assets/YunJing/Models/DistantPeaksKitV1/DPxx_*.fbx`
  - `art/previews/distant-peaks-kit-v1/`
- 在 README 建議擺放：哪幾件放在哪個方向、多遠、多大。Claude Code 會照著放進場景。

---

## C5｜丹房工作桌補 PBR 貼圖（v002）

### 背景

核心組（z1nnz 指導、Claude Code 製作）的丹房工作桌 v1 只有 3 個純色材質，近看像塑膠。依建模規格第 3 節要補成 PBR 貼圖組。這是建模規格「現有不一致」表裡的一項，也是規格的第一個試做案例。

### 現況（在你的工作樹裡）

- 腳本：`tools/art/build_qingxi_alchemy_table_v1.py`（v1，**不要改**）
- 母稿：`art/source/qingxi-alchemy-table-v1/qingxi-alchemy-table-v1.blend`
- 匯出：`art/exports/qingxi-alchemy-table-v1/`（README、`model_info.json`、QA 報告）
- Unity：`apps/game/Assets/YunJing/Models/AlchemyTableV1/QX_AlchemyWorkTable_v001.fbx`
- 預覽：`art/previews/qingxi-alchemy-table-v1/`
- 尺寸 2.01 × 0.73 × 0.785 m，LOD0 1,320 三角面；材質 `M_QX_AgedElm`、`M_QX_OxidisedBronze`、`M_QX_Bamboo`。

### 要做的

1. 新腳本 `tools/art/build_qingxi_alchemy_table_v2.py`。
   - 從 v1 腳本複製，**形體不變**（尺寸、原點、接口都一樣，場景裡的道具才不用移）。
   - 唯一可改的形體：在不超過 2,000 三角面的前提下，給邊緣加倒角，讓高光沿邊出現。
2. 先用 imagegen 生一張**材質參考板**，存到 `art/references/qingxi-alchemy-table-v2/`：
   - 舊榆木桌面（刀痕、藥漬、燒焦點）、竹條、氧化銅包角的近照風格；
   - 對照建模規格的色票。
3. 重新展 UV。貼圖密度照規格：近景道具 512 px/m，所以桌面約 1024×1024。
4. 用程序化材質加烘焙（`blender-texture-baking`）做出 BaseColor、Normal（OpenGL）、ORM：
   - 木紋方向沿桌面長邊；
   - 桌面中間比邊緣磨得更亮更平滑（使用痕跡）；
   - 搗藥處有深色藥漬；銅包角邊緣磨亮、凹處有銅綠。
   - 粗糙度照規格：舊木 0.65–0.85、銅 0.35–0.55，金屬度 0.6–0.8。
5. 材質數維持 ≤ 2 張貼圖組（木竹共用一組、銅一組，或全部一組）。
6. 匯出新版本（不覆蓋 v001）：
   - `art/exports/qingxi-alchemy-table-v2/QX_AlchemyWorkTable_v002.glb`（貼圖內嵌）
   - `apps/game/Assets/YunJing/Models/AlchemyTableV2/QX_AlchemyWorkTable_v002.fbx`
   - 貼圖：`apps/game/Assets/YunJing/Models/AlchemyTableV2/Textures/T_QX_AlchemyTable_{BaseColor,Normal,ORM}.png`
   - `model_info.json`、`source-qa-report.json`、`roundtrip-report.json`、`README.md`
7. 預覽：
   - 照建模規格第 8 節的統一審圖設定：Poly Haven `kloofendal_48d_partly_cloudy_puresky`、AgX、正側背、3/4 視角，附 1.75 m 人形尺；
   - 外加一張和 v001 的並排比較；
   - 一張 0.5 m 距離的桌面特寫。
8. README 要誠實寫：
   - 和 v001 差在哪裡；
   - 哪些細節是貼圖、哪些是幾何；
   - 照規格做時哪裡不順，例如 Unity URP 的 ORM 通道需要換成 Mask Map，這個轉換由 Claude Code 處理，你只要寫出來。

---

## C6｜圖示與介面素材定稿（等 z1nnz 選定 C1 方向後才開始）

z1nnz 選定方向後，Claude Code 會在本檔案底下補上選定的方向和修改意見。屆時要做：

1. **14 個圖示的 SVG 原稿**，照介面方向文件第 6 節：
   - 64×64 畫布、內容區 52×52、線寬 3.5 px、毛筆收鋒；
   - 兩種狀態（一般、啟用）、三種尺寸手修（32、48、96）。
   - 生圖結果只當參考，**SVG 要是向量重繪**，不能把點陣圖包在 SVG 裡。
2. **九宮格素材**：
   - 玉按鈕（一般、按下、停用、冷卻遮罩）、紙面板、任務條、印章、搖桿底盤與把手；
   - PNG，2x 解析度，附九宮格邊界數值（`slice.json`）。
3. **一張完整定稿畫面**：用上面的素材組回去，和 C1 選定的概念圖並排比較。
4. 檢查並寫進 README：
   - 每個圖示在 32 px、灰階、色弱模擬下的截圖；
   - 圖示排在一起的線寬一致性。

---

## 第三部分：回報格式

每做完一項，在**該任務的 README** 寫好，並回報給使用者（z1nnz）。內容如下：

```
【Cx 完成／部分完成／卡住】
1. 產生的檔案（路徑清單）
2. 數字：每件三角面數、貼圖尺寸、檔案大小（C3 寫外殼總 KB）
3. QA 結果：錯誤 0？警告與接受理由
4. 三視圖／概念圖：存在哪裡、哪些是推定設計
5. 建模規格試用心得：哪條做不到或不合理
6. 還沒做、沒驗證的事
7. 生圖用了幾張、額度是否還有
```

全部 6 項的總進度也請列一張表：`ID｜狀態｜下一步`。

做完任何一項都可以先回報，不用等全部完成。Claude Code 會逐項檢查、整合進新手村，再以 z1nnz 名義提交 PR。
