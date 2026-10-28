# 青溪上游調查 A01–A06（第一批）：模型原始檔與建置

工作包：[`docs/execution/2026-10-29/11-A-upstream-investigation.md`](../../../docs/execution/2026-10-29/11-A-upstream-investigation.md)，共同規則：[`10-waterline-revised-brief.md`](../../../docs/execution/2026-10-29/10-waterline-revised-brief.md)；模組變體依 PR #43 的補充規則。本目錄從 main `149b865` 開始。

## 檔案

| 檔案 | 內容 |
|---|---|
| `Qingxi_Waterhead_A.blend` | 母檔：每個形體變體一組「程序分件（可編輯，隱藏）」與「烘焙遊戲網格＋LOD」Collection |
| `blend/<key>.blend` | 每個形體變體單獨的建置結果 |
| `build_waterhead.py` | 幾何、材質、烘焙、LOD、匯出、驗證、預覽 |
| `kitlib.py` | 烘焙／匯出／渲染工具，改寫自 `art/source/qingxi-alchemy-b/qa_lib.py`（joshsu54）；只改輸出路徑，並在打包前依實際面積統一 UV 島比例（大型地形塊才分得到足夠貼圖） |
| `geomlib.py` | 幾何工具，經 `art/source/qingxi-encounter-a/`（PR #39）複製自演武區 `yardlib.py`（PR #38），同作者 |
| `compose_sheets.py` | 「AI 三視圖 vs 模型正交正／側／背」對照表 |

```powershell
$B = 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
& $B -b --python-exit-code 1 --python art/source/qingxi-waterhead-a/build_waterhead.py               # 可加 key、--no-render、--quick
& $B -b --python-exit-code 1 --python art/source/qingxi-waterhead-a/build_waterhead.py -- --master
python art/source/qingxi-waterhead-a/compose_sheets.py
```

建置前會檢查 `art/references/qingxi-waterhead-a/<參考圖>_three_view.png`，沒有三視圖就拒絕建模。

## 規格與接口

- 公尺；Blender Z-up、上游 +Y；GLB Y-up、上游 −Z。
- **A01 河床接口**（所有段相同）：河道寬 2.4 m、塊寬 7 m、岸頂高於原點 1.15 m、河床中心 0.25 m、今日水面 0.30 m、舊高水位線 0.86 m。原點在下游接口的河道中心底面；放置時原點設在 y = −1.15，岸頂即與地面 0 對齊；下一段接在 `model_info.json` 的 `out_port_blender_xy_deg`。非接口的兩側邊保持不規則，但在邊緣回到岸頂高度。
- 水位史是共用規則：所有河岸、岸石、卵石、示跡石都用同一組高度畫「濕線以下深色、舊水位以下淺色乾痕、舊水位一圈深色潮線」，換段不會對不上。
- 水面是獨立、不烘焙的半透明節點（`<key>_Clear`）；草叢與枯草葉用頂點色、共用一個不烘焙材質，同樣放在 `_Clear`。其餘部分烘焙成一張圖集（BaseColor／ORM／Normal）。
- GLB 只含 LOD0、貼圖 WebP；FBX 含 LOD0–2 與 PNG。

## 模型清單

| key | 家族／變體 | 外形 m | LOD0 / LOD1 / LOD2 | 預算 | 貼圖 | GLB |
|---|---|---|---|---:|---:|---:|
| `A01_straight_01` | A01 直段 | 7.00 × 6.00 × 1.58 | 19,156 / 7,288 / 3,205 | 20k | 2048 | 2.05 MB |
| `A01_bend_left_01` | A01 左彎 25°（內岸卵石灘） | 8.07 × 7.77 × 1.70 | 19,232 / 7,325 / 3,222 | 20k | 2048 | 2.08 MB |
| `A01_bend_right_01` | A01 右彎 40°（外岸層理岩壁） | 8.36 × 8.24 × 2.05 | 20,256 / 7,837 / 3,448 | 21k¹ | 2048 | 2.24 MB |
| `A01_narrow_01` | A01 收窄（峽口約 1.2 m） | 7.00 × 6.00 × 2.00 | 19,892 / 7,655 / 3,368 | 20k | 2048 | 2.08 MB |
| `A01_end_source_01` | A01 收尾件（泉潭＋亂石堆，只有下游接口） | 7.00 × 4.42 × 1.95 | 21,758 / 8,162 / 3,591 | 22k² | 2048 | 2.19 MB |
| `A02_side_crack_01` | A02 破口 1：側面裂口 | 3.03 × 1.68 × 0.74 | 3,298 / 1,470 / 646 | 9k | 1024 | 0.36 MB |
| `A02_end_break_01` | A02 破口 2：末端斷裂外傾 | 3.72 × 1.20 × 0.74 | 3,356 / 1,500 / 660 | 9k | 1024 | 0.38 MB |
| `A03_FormationBase` | 半埋舊陣基（石＋青綠銅殘件） | 2.36 × 2.51 × 0.46 | 7,168 / 3,212 / 1,413 | 9k | 1024 | 0.68 MB |
| `A04_SiltBar` | 泥沙堆形 1（堵水狀態） | 2.47 × 2.97 × 0.70 | 4,066 / 2,001 / 880 | 9k | 1024 | 0.73 MB |
| `A04_SiltBar_cleared` | 同一處的清理後狀態 | 2.80 × 2.20 × 0.13 | 1,322 / 660 / 290 | 4k | 1024 | 0.28 MB |
| `A05_WitheredSedge_01` | 枯草叢 1 | 1.34 × 1.27 × 0.71 | 3,104 / 840 / 369³ | 3.5k | 512 | 0.32 MB |
| `A06_MarkerStone` | 濕潤青苔示跡石 | 1.63 × 1.59 × 1.17 | 6,080 / 2,920 / 1,284 | 7k | 1024 | 0.60 MB |

¹ 外側岩壁是一片片層理岩板。² 亂石堆 12 塊大石。³ 枯草葉在 `_Clear` 節點，目前沒有 LOD（列入第二批）。

所有 GLB 在全新場景回匯，三角面數與包圍盒一致；零面積面與游離頂點皆為 0。非流形邊來自刻意的開放邊（地形塊沒有底面、單面草葉以雙面材質渲染）。碰撞建議寫在各件 `art/exports/qingxi-waterhead-a/<key>_model_info.json`。

## 每件預覽

`art/previews/qingxi-waterhead-a/<key>/`：`three_quarter`、`close_front`、`close_side`、`back`、`scale_1p7m`（1.7 m 角色尺度）、`wireframe`、正交 `ortho_front/side/back/top`，以及 `ref-vs-model.png`（三視圖 vs 模型）。組裝場景、俯視模組圖與 1.7 m 眼高圖在 `art/previews/qingxi-waterhead-a/demo/`。

## 建模報告（依《雲境》AI 3D 建模總指令 v1.0）

- **模型名稱**：青溪上游調查 A01（五種河床形體）、A02（兩種破口）、A03、A04（堆形 1＋清理後狀態）、A05（枯草 1）、A06。
- **實際工作目錄**：`art/source|exports|previews|references/qingxi-waterhead-a/`、`tools/qingxi-waterhead-a/`。
- **Blender 版本**：5.2.2 LTS，背景模式執行 Python。
- **使用技術**：程序化網格（曲率河道座標的高度場、超橢球岩石＋劈裂面、車削、掃掠管、布林破口）、程序材質烘焙（AO 驅動的邊緣與凹陷風化、共用水位色帶）、Decimate LOD、glTF／FBX 匯出與回匯驗證。草叢用頂點色低面數草束、共用材質，不做透明貼片也不逐葉建高面數模型。
- **完成的功能**：A01 五種形體共用接口，可延伸、轉彎、收窄、收尾；A04 堵水／清理後兩種狀態，原點相同可直接替換；兩條可觀察線索與一個環境提示接入本機展示。
- **材質及貼圖**：每件一張烘焙圖集（BaseColor×AO、ORM、Normal，A01 為 2048、其餘 1024／512），水面與草葉為不烘焙材質。
- **動畫與骨架**：不適用（靜態環境件）。
- **遊戲引擎整合**：只交付 GLB／FBX 與接口說明；未在 Unity 匯入驗證。
- **品質檢查結果**：見上表與預覽；自評如下。

| 項目（權重） | 自評 | 依據 |
|---|---:|---|
| 形體比例與輪廓（25%） | 3.5／5 | 變體在輪廓、彎向、岩石分布上看得出差別，尺寸符合三視圖；A04 比參考圖光滑，河岸岩石密度仍低於參考圖 |
| 幾何拓樸與結構（20%） | 3.5／5 | 原點、接口、地面接觸正確，無游離頂點與零面積面；地形網格是均勻格點，未依曲率最佳化 |
| 材質與光影（20%） | 3.0／5 | 水位史色帶在各件一致可讀；但棚拍偏白，A01 每公尺約 250 px，近看偏糊 |
| 美術風格一致性（15%） | 3.5／5 | 暖灰石、舊木、低飽和青水、乾草色系與 PR #39 林地包一致；尚未在主場景光線下並排比較 |
| 動畫或互動完整度（10%） | 4.0／5 | 兩條線索、任意順序、去重、提示、回入口、兩種走法都可操作並有測試 |
| 遊戲效能與匯出（10%） | 3.5／5 | 全部在面數預算內，GLB／FBX／LOD 齊全且回匯一致；未在手機實測 |
| **加權** | **約 69／100** | 尚未達到工作包「近看沒有破面、遠看有辨識度」的最終水準，列為下一批持續修正 |

## 尚未完成

- 第二批：A07–A12；A04 另兩種堆形、A05 另兩種高矮疏密、A08 三種踏面；碎石、濕痕等可散布小件。
- 下游端的轉接件（目前由林地包的倒木遮住斷面，等核心組接入村內寬河）。
- A05 葉片 LOD；河床近看貼圖密度（考慮 detail 貼圖或分塊烘焙）。
- Unity 匯入、遊戲內光線、實機手機效能都還沒驗證。

作者：Johnnnny0823。沒有使用第三方模型。
