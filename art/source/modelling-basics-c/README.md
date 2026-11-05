# 承天 · 基礎建模練習（C 包，Eli-0731）

工作包：[2026-11-03 / C-28h-modelling-basics.md](../../../docs/execution/2026-11-03/C-28h-modelling-basics.md)（在分支 `feature/qingxi-creek-chapter`，2f8a150）。只做模型，不排玩法，不做人物。照工作包「做完第 1 件（木箱）就先開一張 PR」，這一版只有 BM01。

| 編號 | 東西 | 工作包尺寸 | 實際尺寸（寬×深×高 m，箱體） | 三角面 LOD0 / 1 / 2（含 Detail_） | 箱體三角面（不含 Detail_） | `minTier` |
|---|---|---|---|---|---|---|
| BM01_01 | 舊木箱・小，背面換過一塊板 | 0.5 m 寬 | 0.50 × 0.34 × 0.29 | 10,754 / 5,376 / 1,610 | 9,038 / 4,518 / 1,354 | `standard` |
| BM01_02 | 舊木箱・中，綁麻繩 | 0.8 m 寬 | 0.80 × 0.48 × 0.39 | 30,694 / 15,346 / 4,599 | 10,104 / 5,052 / 1,514 | `standard` |
| BM01_03 | 舊木箱・大，正面換過一塊板 | 1.1 m 寬 | 1.10 × 0.58 × 0.53 | 13,656 / 6,828 / 2,044 | 11,332 / 5,666 / 1,698 | `standard` |

完整數字（每組材質的貼圖尺寸、三角面、碰撞、`detailObjects`）在 [`art/exports/modelling-basics-c/model_info.json`](../../exports/modelling-basics-c/model_info.json)。含腳邊小草和麻繩的外框會比箱體大一點（例如 BM01_02 是 0.84 × 0.55 × 0.40），碰撞只包箱體。

## 第二輪：照 #67 審查改回風格指南手繪段（2026-11-05）

z1nnz 審查：木色偏亮、板條太規整，和既有暗褐老木器（C07 工具箱）不連貫；要回到風格指南 5.2 固定段和 5.3 負面提示，保留尺寸與結構，先調板條明暗和寬度節奏，再做局部磨損和色塊，不要整箱加噪點；灰模與材質都和 C07 同燈同尺度並排；BM01_02 回匯 QA 7 項要逐項說明；不要用減面代替風格修正。

- **參考**：用 5.2＋5.3 原文（一字不改，`art/references/BM01/v2/prompt-5.2-5.3.txt`）請 Codex（GPT-6-Astra）生成 8 張三視圖，評選紀錄在 `v2/notes.md`。最好的 `BM01-v2-cand-2.png` 只有 81 分（木色仍偏亮），所以**顏色以 C07 為準**，v2 參考只取手繪的畫法：板邊的柔和高光、灰洗色塊、腳邊苔。結構仍照第一輪選的 `BM01-cand-4.png`。
- **板條節奏**：每個箱子的板寬照「一寬、一窄、其餘居中」排（1.35 / 0.72 / 1.0 / 1.15 倍），不再是 0.9–1.1 的平均寬；三種木料（中、深、曬灰）依比例分配，相鄰兩塊很少同色。
- **木頭貼圖**（`board()` 重寫）：大面柔和色塊，加少量細長的深色筆觸和淺色筆觸、少數裂紋和鏡片形的深色裂口（像 C07 的畫法）。顏色裡不再有細纖維條紋，纖維只留在法線貼圖。第一輪的「條紋」其實是雜訊沿板長只有一格，整塊板一條條通到底，這次改掉。
- **局部色塊和磨損**（`crate_paint`）：腳邊一圈不均勻的濕暗色、往上竄的深色髒痕（C07 底部那種）；側面幾塊大的深色斑和曬灰斑；頂面曬灰；板邊一律帶柔和的手繪亮邊，蓋緣、角條頂端和箱角再磨亮一些。苔只留腳邊一點（C07 沒有苔）。
- **邊角更圓**：板倒角 4 → 6.5 mm、角條 5 → 8 mm，接近 C07 的圓鈍邊。
- **實測**（Albedo，暗部 5％／平均／亮部 5％）：大箱 `#221812` / `#4d3927` / `#886746`，C07 v002 平均 `#4c3724`；中箱平均 `#55402c`、小箱 `#513d2a`。第一輪大箱平均 `#5a4b39`（偏灰）、算圖看起來偏橙亮。
- **並排**（`art/previews/modelling-basics-c/BM01/compare/`）：三箱和 C07 v001、v002 同燈同尺度，材質 `BM01-vs-C07-*.png` 和灰模 `BM01-vs-C07-clay-*.png`（同一種灰、拿掉所有貼圖），再加一張大箱和 C07 v002 的近拍 `BM01_03-vs-C07v002-close-cam.png`。

### 回匯 QA（`art/previews/modelling-basics-c/BM01/qa-lod0.json`）

核心組的 QA 模組不在我這台電腦上，用 `tools/art/qa_lod0_basic.py`（第 3、4 天包同一支）對匯出的 GLB 跑：零面積 UV、共面重疊三角、浮空碎件、缺 UV、未套用縮放。舊版（cff26fa）BM01_02 有 5 類問題，對應審查的 7 項：

| 問題（cff26fa） | 原因 | 修法 |
|---|---|---|
| 麻繩零面積 UV 109 面 | 繩股兩端的端蓋故意把 UV 折到端圈上，面積是 0 | 端蓋改用 smart project 自己的小島 |
| 箱體零面積 UV 8 面 | 倒角留下不到 1 mm 的碎三角 | 合併時收掉 0.8 mm 以下、面積小於 0.4 mm² 的碎邊 |
| 麻繩共面 6 對（繩結） | 繩結兩圈的繩股疊在同一平面 | 分開的零件有三角疊在同一平面時，小的那個沿法線推出 1 mm（`separate_coplanar`） |
| 箱體共面 44 對 | 角條內面和板面、蓋板底面和側板頂面剛好貼在同一平面 | 角條嵌進板裡 3 mm、蓋板往下 1.5 mm（大於板面 1.8 mm 的起伏），外框尺寸不變 |
| 釘頭 × 箱體共面 2 對 | 釘頭底面剛好落在板面 | 釘頭埋進板面 1–2 mm |

**修正後**：BM01_01、BM01_02 0 項；BM01_03 剩 1 對，是左側一塊板在板縫裡朝下的底面（同一個零件自己的摺面，z = 8 cm），被上面那塊板擋住，看不到。修正前後同位置近拍在 `art/previews/modelling-basics-c/BM01/qa-evidence/qa-evidence-sheet.jpg`（左舊右新，最後一張是 BM01_03 剩下那一項）。

**QA 工具更新後（2026-11-06，#69）**：`qa_lod0_basic.py` 改成「同一位置的頂點算相連」，因為 glTF 會在 UV 接縫把頂點拆開。用新版重跑，BM01_03 那一對變成 0 項：那兩個三角其實相鄰、共用一個角，只是被 UV 接縫拆成兩組頂點，舊版才把它們當成兩個零件來比。模型沒有改，那個摺面還在原處，被上面的板擋住。`qa-lod0.json` 已是新版的結果。

三角面少了約 3–7％（例如中箱 31,650 → 30,694），全部來自收掉的碎三角和端蓋，不是為了風格減面；板、角條、蓋子、麻繩、釘頭的數量和分段都沒變。

## 製作順序

1. **AI 三視圖**（`art/references/BM01/`，照工作包第 1 節的路徑）：
   - 工作包 BM01 的提示詞原文，一字未改。
   - **風格改成半寫實（使用者 2026-11-02 指定）**：第一批照風格指南 5.2 手繪固定段生成，使用者看過說「這風格不太對吧 我們要比較寫實風格」，選了「半寫實」。第二批把 5.2 換成半寫實段、5.3 換成對應的負面提示（拿掉 photorealistic 等，改避開卡通、描邊、平塗）。兩段原文都在 `prompt.txt`。
   - **第二輪改回指南手繪段**（#67 審查）：`v2/` 是 5.2＋5.3 原文生成的 8 張，見上面「第二輪」。
   - Gemini 4 Argon（網頁版）半寫實 4 張、Codex CLI GPT-6-Astra（推理 xhigh）4 張，用同一段提示詞；使用者並排看過後選 Codex。手繪版 3 張也留著。
   - 選用 `BM01-cand-4.png`（三行三列：小／中／大 × 正面／側面／背面），細節對照 `BM01-cand-2.png`。沒選的原因寫在 `prompt.txt`。工具都沒有回報 seed。
2. **建模**：`build_basics.py`。建模前會檢查 `prompt.txt` 已寫明選用哪一張，沒選就停。
3. **審圖**：`render_reviews.sh` 匯入**匯出的 GLB／FBX**，固定燈光渲染。
4. **Unity 驗證**：`unity/run_unity_check.sh`（見下方）。

## BM01 怎麼做的

照 C4 拆成真的木箱結構，不是一個方塊貼木紋：

- **板**：前後兩面的橫板跨整個寬度，左右兩面的板夾在中間；每塊板各自一個物件，板和板之間留 4.5 mm 的縫，每塊有一點彎曲和傾斜；板寬有寬有窄（見第二輪）。小箱每面 3 排，中、大箱 4 排。
- **角條**：四面各兩根直角條，比板面凸出 1.3–1.9 cm（另有 3 mm 嵌進板裡），頂端比蓋子高 6 mm；每排板對應一顆釘。
- **蓋子**：3–4 塊橫向木板，兩端各一顆釘；底下有一塊看不到的底板，箱子從下面看是封起來的。
- **換過的板**：大箱正面第 2 排（由上往下）、小箱背面中間那排。中間一段是較淡、較灰的新板，兩端是同一塊舊板留下的短頭，各兩顆釘。
- **麻繩（中箱）**：一圈橫繩繞過角條，一條縱繩從正面翻過蓋子到背面，在正面交叉處打結，垂下一個繩圈和一段散開的繩頭。三股絞繩，每股是一條管子。
- **木頭貼圖**：三種舊木料（中、深、曬灰）依節奏分配給每塊板，相鄰的板顏色不同；手繪式的大色塊和少量筆觸，顏色對齊 C07（見第二輪）。
- **磨損和髒污**：板邊柔和亮邊，蓋緣、角條頂端和箱角局部磨亮；腳邊不均勻的濕暗色和往上竄的髒痕，一點苔；中、大箱背面各有節孔，蓋子下方有不規則的雨水髒痕。
- **不刻字、不寫字、不寫數字。**

### 對照風格指南（[art-style-guide-v1](../../../docs/execution/art-style-guide-v1.md)）

第一輪提示詞的風格段依使用者決定改成半寫實；第二輪照 #67 審查回到 5.2＋5.3，顏色對齊 C07。其他照指南的數據核對：

| 指南 | 要求 | BM01 |
|---|---|---|
| 第三節色票・木構 | `#6a4630` → `#a87a50`，舊木頭，帶灰 | 大箱箱體貼圖（第二輪）：暗部 `#221812`（板縫和陰影）、平均 `#4d3927`、亮部 `#886746`；C07 v002 平均 `#4c3724`。平均比色票暗一階，是照審查要和既有暗褐老木器一致 |
| 第三節色票・草地 | `#3e6a2a` → `#6fa443` → `#b8d468` | 腳邊苔從 `#3e6a2a` 起，小草葉片照同一段色票 |
| 第三節 | 不用純黑、純白 | 最暗的板縫、節孔約 `#0d0906` 以上，新板最亮約 `#bdb09a` |
| 第四節・磨損 | 邊角磨亮、縫裡有苔和土、木頭有裂紋 | 邊角磨淡、板縫積灰、腳邊土色和一叢叢的苔、順著板長的裂紋和節疤 |
| 第四節・暗部偏冷、亮部偏暖 | | 遮蔽處混一點藍紫，頂面加一點暖色 |
| 第四節・尺寸 | 真實尺寸 | 0.50 / 0.80 / 1.10 m 寬，和 1.75 m 人形尺、C07 工具箱並排 |
| 第六節 | 在遊戲裡截圖，跟方向圖放在一起比 | `art/previews/modelling-basics-c/unity/BM01-vs-direction-A.png`：Unity 截圖和方向圖 A（暖陽河谷）並排 |

### 畫質分級（[quality-tiers-v1](../../../docs/standards/quality-tiers-v1.md) 第四節）

- `minTier` 都是 `standard`：木箱會擋路，每個人都要看得到。
- 可以拿掉也看得懂的小東西拆成子物件：`<編號>_Detail_Nails_LOD<n>`（釘頭）、`<編號>_Detail_Rope_LOD<n>`（麻繩，只有中箱）、`<編號>_Detail_Grass_LOD<n>`（腳邊小草）。`model_info.json` 的 `detailObjects` 列組名，`detailMeshes` 列完整物件名。標準檔只要關掉名字含 `_Detail_` 的網格。
- LOD0 不減；LOD1 約 50%、LOD2 約 15%，同一個 FBX。審圖有一張 LOD0 和 LOD1 同角度、關掉 Detail_ 的並排（`art/previews/modelling-basics-c/BM01/lod/lod0-vs-lod1-nodetail.png`）。
- 貼圖：箱體 2048（小箱 1024）、麻繩 1024、釘頭 256–512、小草 256，都在 2048 以內。

## 交件內容

| 路徑 | 內容 |
|---|---|
| `art/exports/modelling-basics-c/<編號>.fbx` | LOD0／1／2、`<編號>_Collision`、根節點 `<編號>_GroundOrigin`，給 Unity |
| `art/exports/modelling-basics-c/<編號>.glb` | LOD0（含 Detail_），給網頁預覽 |
| `art/exports/modelling-basics-c/model_info.json` | 尺寸、三角面、貼圖、碰撞、`minTier`、`detailObjects` |
| `art/textures/modelling-basics-c/<編號>_<組>_*.png` | Albedo／Normal／MaskURP（R 金屬、G AO、A 光滑度）／ORM（glTF） |
| `art/source/modelling-basics-c/<編號>.blend` | 工作檔（原始零件收在 `<編號>_SourceParts`） |
| `art/previews/modelling-basics-c/BM01/` | 四視圖加 1.75 m 人形尺、線框、三個一組、近拍、和 C07 工具箱（v001、v002）同燈同尺度並排（材質和灰模）、LOD0／LOD1 並排、`qa-lod0.json` 和 `qa-evidence/` 近拍 |
| `art/previews/modelling-basics-c/unity/` | Unity 匯入檢查結果 `report.txt` 和截圖 |

原點：箱底中心，底部 z = 0；Blender 的 -Y 是正面（FBX／Unity 的 -Z）。沒有地面底板。

## 重建

```bash
B=<blender 4.5.3>; MSYS_NO_PATHCONV=1 "$B" -b --factory-startup -P art/source/modelling-basics-c/build_basics.py -- BM01_01 BM01_02 BM01_03
BLENDER="$B" MSYS_NO_PATHCONV=1 sh art/source/modelling-basics-c/render_reviews.sh BM01
UNITY=<Unity 6000.0.82f1> sh art/source/modelling-basics-c/unity/run_unity_check.sh
MSYS_NO_PATHCONV=1 "$B" -b --factory-startup -P tools/art/qa_lod0_basic.py -- art/previews/modelling-basics-c/BM01/qa-lod0.json art/exports/modelling-basics-c/BM01_0{1,2,3}.glb
```

Unity 驗證不改 `apps/game`：跑的時候把 `QingxiBasicsVerify.cs` 和模型暫時複製進去，跑完刪掉，並還原它切換的 URP 設定。
