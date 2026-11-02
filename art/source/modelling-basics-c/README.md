# 承天 · 基礎建模練習（C 包，Eli-0731）

工作包：[2026-11-03 / C-28h-modelling-basics.md](../../../docs/execution/2026-11-03/C-28h-modelling-basics.md)（在分支 `feature/qingxi-creek-chapter`，2f8a150）。只做模型，不排玩法，不做人物。照工作包「做完第 1 件（木箱）就先開一張 PR」，這一版只有 BM01。

| 編號 | 東西 | 工作包尺寸 | 實際尺寸（寬×深×高 m，箱體） | 三角面 LOD0 / 1 / 2（含 Detail_） | 箱體三角面（不含 Detail_） | `minTier` |
|---|---|---|---|---|---|---|
| BM01_01 | 舊木箱・小，背面換過一塊板 | 0.5 m 寬 | 0.50 × 0.34 × 0.29 | 11,612 / 5,806 / 1,738 | 9,852 / 4,926 / 1,476 | `standard` |
| BM01_02 | 舊木箱・中，綁麻繩 | 0.8 m 寬 | 0.80 × 0.48 × 0.39 | 31,650 / 15,824 / 4,745 | 11,148 / 5,574 / 1,672 | `standard` |
| BM01_03 | 舊木箱・大，正面換過一塊板 | 1.1 m 寬 | 1.10 × 0.58 × 0.53 | 14,116 / 7,058 / 2,116 | 11,748 / 5,874 / 1,762 | `standard` |

完整數字（每組材質的貼圖尺寸、三角面、碰撞、`detailObjects`）在 [`art/exports/modelling-basics-c/model_info.json`](../../exports/modelling-basics-c/model_info.json)。含腳邊小草和麻繩的外框會比箱體大一點（例如 BM01_02 是 0.84 × 0.55 × 0.40），碰撞只包箱體。

## 製作順序

1. **AI 三視圖**（`art/references/BM01/`，照工作包第 1 節的路徑）：
   - 工作包 BM01 的提示詞原文，一字未改。
   - **風格改成半寫實（使用者 2026-11-02 指定）**：第一批照風格指南 5.2 手繪固定段生成，使用者看過說「這風格不太對吧 我們要比較寫實風格」，選了「半寫實」。第二批把 5.2 換成半寫實段、5.3 換成對應的負面提示（拿掉 photorealistic 等，改避開卡通、描邊、平塗）。兩段原文都在 `prompt.txt`。
   - Gemini 4 Argon（網頁版）半寫實 4 張、Codex CLI GPT-6-Astra（推理 xhigh）4 張，用同一段提示詞；使用者並排看過後選 Codex。手繪版 3 張也留著。
   - 選用 `BM01-cand-4.png`（三行三列：小／中／大 × 正面／側面／背面），細節對照 `BM01-cand-2.png`。沒選的原因寫在 `prompt.txt`。工具都沒有回報 seed。
2. **建模**：`build_basics.py`。建模前會檢查 `prompt.txt` 已寫明選用哪一張，沒選就停。
3. **審圖**：`render_reviews.sh` 匯入**匯出的 GLB／FBX**，固定燈光渲染。
4. **Unity 驗證**：`unity/run_unity_check.sh`（見下方）。

## BM01 怎麼做的

照 C4 拆成真的木箱結構，不是一個方塊貼木紋：

- **板**：前後兩面的橫板跨整個寬度，左右兩面的板夾在中間；每塊板各自一個物件，板和板之間留 4.5 mm 的縫，每塊有一點彎曲和傾斜。小箱每面 3 排，中、大箱 4 排。
- **角條**：四面各兩根直角條，比板面凸出 1.6–2.2 cm，頂端比蓋子高 6 mm；每排板對應一顆釘。
- **蓋子**：3–4 塊橫向木板，兩端各一顆釘；底下有一塊看不到的底板，箱子從下面看是封起來的。
- **換過的板**：大箱正面第 2 排（由上往下）、小箱背面中間那排。中間一段是較淡、較灰的新板，兩端是同一塊舊板留下的短頭，各兩顆釘。
- **麻繩（中箱）**：一圈橫繩繞過角條，一條縱繩從正面翻過蓋子到背面，在正面交叉處打結，垂下一個繩圈和一段散開的繩頭。三股絞繩，每股是一條管子。
- **木頭貼圖**：三種舊木料（一般、較深、較灰白）每塊板隨機分配，所以相鄰的板顏色不同，顏色在風格指南的木構色票內（見下節）。木紋是不等距的深色紋線加細纖維、順著板長的裂紋和節疤，曬白的灰色斑塊；起伏主要來自纖維和裂紋，避免看起來像瓦楞板。
- **磨損和髒污**：邊角磨淡、板縫積灰；腳邊一圈土色，苔從縫和角落一叢一叢往上長；中、大箱背面各有節孔，蓋子下方有淡淡的雨水髒痕。
- **不刻字、不寫字、不寫數字。**

### 對照風格指南（[art-style-guide-v1](../../../docs/execution/art-style-guide-v1.md)）

提示詞的風格段依使用者決定改成半寫實，其他照指南的數據核對：

| 指南 | 要求 | BM01 |
|---|---|---|
| 第三節色票・木構 | `#6a4630` → `#a87a50`，舊木頭，帶灰 | 大箱箱體貼圖：暗部 `#362c24`（板縫和陰影）、平均 `#5a4b39`、亮部 `#8e7157`；三種木料都有曬灰的斑塊。第一版平均只有 `#41392a`，太暗太灰，已調整 |
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
| `art/previews/modelling-basics-c/BM01/` | 四視圖加 1.75 m 人形尺、線框、三個一組、近拍、和 C07 工具箱並排、LOD0／LOD1 並排 |
| `art/previews/modelling-basics-c/unity/` | Unity 匯入檢查結果 `report.txt` 和截圖 |

原點：箱底中心，底部 z = 0；Blender 的 -Y 是正面（FBX／Unity 的 -Z）。沒有地面底板。

## 重建

```bash
B=<blender 4.5.3>; MSYS_NO_PATHCONV=1 "$B" -b --factory-startup -P art/source/modelling-basics-c/build_basics.py -- BM01_01 BM01_02 BM01_03
BLENDER="$B" MSYS_NO_PATHCONV=1 sh art/source/modelling-basics-c/render_reviews.sh BM01
UNITY=<Unity 6000.0.82f1> sh art/source/modelling-basics-c/unity/run_unity_check.sh
```

Unity 驗證不改 `apps/game`：跑的時候把 `QingxiBasicsVerify.cs` 和模型暫時複製進去，跑完刪掉，並還原它切換的 URP 設定。
