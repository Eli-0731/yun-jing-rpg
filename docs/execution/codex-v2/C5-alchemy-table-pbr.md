# C5｜丹房工作桌 v002：形體精修＋PBR 貼圖

> 先讀 `00-operating-rules.md`。這是**建模規格的第一個完整試做案例**：從一件已存在、品質不夠的模型，走完規格的全部流程，證明規格可行，並找出規格不合理的地方。

## 1. 一句話任務

把新手村丹房的工作桌從「純色方塊拼成的桌子」升級成**近看也經得起檢查**的成品：精修形體、補上 PBR 貼圖。尺寸與接口不能變。

## 2. 為什麼要做

- 這張桌子是協作者 B（煉丹玩法）的核心家具。研缽、晾藥籃、藥瓶、食譜架都放在桌面上，玩家煉丹時鏡頭就對著它。
- 目前 v001 的問題（看 `art/previews/qingxi-alchemy-table-v1/QX_AlchemyWorkTable_v001_three-quarter.png`）：
  1. 3 個純色材質，沒有木紋，像塑膠；
  2. 全部是直角方塊，沒有倒角，邊緣沒有高光；
  3. 桌面是一塊平板，沒有厚度層次、沒有使用痕跡；
  4. 銅包角只是小方塊，不像真的包角；
  5. 竹條是光滑圓柱，沒有竹節。
- 它是核心組（z1nnz 指導）自己的模型，建模規格的「現有不一致」表裡列了它，所以拿它當第一個試做。

## 3. 位置

| 項目 | 路徑 |
|---|---|
| 工作樹 | `D:\yun-jing-rpg-workspace\yun-jing-rpg-alchemy-table-pbr-v1`（分支 `feature/alchemy-table-pbr-v1`，從 PR #49 分支開出） |
| v1 腳本（**只讀，不要改**） | `tools/art/build_qingxi_alchemy_table_v1.py`、`tools/art/verify_qingxi_alchemy_table_v1.py` |
| v1 檔案（**只讀**） | `art/source/qingxi-alchemy-table-v1/`、`art/exports/qingxi-alchemy-table-v1/`、`art/previews/qingxi-alchemy-table-v1/`、`apps/game/Assets/YunJing/Models/AlchemyTableV1/` |
| v2 參考 | `art/references/qingxi-alchemy-table-v2/` |
| v2 腳本 | `tools/art/build_qingxi_alchemy_table_v2.py`（可另寫 `verify_qingxi_alchemy_table_v2.py`） |
| v2 母檔 | `art/source/qingxi-alchemy-table-v2/qingxi-alchemy-table-v2.blend` |
| v2 匯出 | `art/exports/qingxi-alchemy-table-v2/` |
| v2 Unity | `apps/game/Assets/YunJing/Models/AlchemyTableV2/QX_AlchemyWorkTable_v002.fbx`；貼圖在 `AlchemyTableV2/Textures/` |
| v2 預覽 | `art/previews/qingxi-alchemy-table-v2/` |
| 狀態 | `art/exports/qingxi-alchemy-table-v2/PRODUCTION_STATUS.md` |

## 4. 不能變的東西（場景裡其他道具靠它們定位）

| 項目 | 值 |
|---|---|
| 外框尺寸 | 2.0 × 0.72 m（含包角最大 2.01 × 0.73） |
| 桌面高度 | **0.78 m**（接口 `tabletop: [0, 0, 0.78]`） |
| 原點 | 底部中心，`ground_z = 0` |
| 正面方向 | 和 v1 相同（Blender −Y） |
| 碰撞 | 一個盒子 2.0 × 0.72 × 0.78 m，中心 (0, 0, 0.39) |
| 物件命名 | `SM_QX_AlchemyWorkTable_LOD0`、`_LOD1` |

## 5. 可以改、應該改的東西

| 部位 | v001 | v002 要做到 |
|---|---|---|
| 桌面 | 一塊平板 | 厚 45–55 mm 的厚實榆木板，由 3 塊寬板拼成，拼縫看得到；四邊上緣倒圓角（半徑 6–8 mm），四邊略凸出桌腳 30–40 mm |
| 桌腳 | 方柱 | 方柱倒角 8 mm，下段微收（底部比頂部窄 8–10%），腳底有 15 mm 的磨損圓角 |
| 牙板（桌面下的橫板） | 直板 | 前後牙板下緣做一道簡單的弧形或如意線條，只用大形，不雕花 |
| 下層 | 光滑圓柱竹條 | 竹條有竹節（每 0.3–0.4 m 一節，節處略凸），兩端插入橫木 |
| 銅包角 | 小方塊 | 真正包住桌角的 L 形銅片，厚 2–3 mm，用 2–3 顆圓頭銅釘固定；邊緣磨亮 |
| 使用痕跡 | 無 | 見第 6 節 |

**面數**：LOD0 ≤ **3,000** 三角面（v001 是 1,320），LOD1 ≤ 1,500。
增加的面數要用在**輪廓與高光**（倒角、竹節、包角），不要用在看不見的地方。

## 6. 材質與貼圖

貼圖密度：近景道具 512 px/m → 桌面 2 m 長約 1024 px。**全部共用一組 1024 貼圖**（或木竹一組、銅一組，共兩組）。

| 材料 | 色票 | 粗糙度 | 金屬度 | 細節 |
|---|---|---|---|---|
| 舊榆木 | `#5A3A22`、`#7A5234`、暗部 `#3B2617` | 0.65–0.85；桌面中間磨亮處 0.5–0.6 | 0 | 木紋沿桌面長邊；拼板的色差（每塊略不同）；刀痕、藥漬、一兩個燒焦圈 |
| 竹 | `#A8915E`、節處 `#7A6A3E` | 0.6–0.75 | 0 | 縱向細紋、竹節 |
| 氧化銅 | `#3E5C52`、`#6B8F7E`；磨亮處 `#A8874E` | 0.35–0.55 | 0.6–0.8 | 凹處銅綠，凸邊磨出底下的黃銅色 |

**使用痕跡**（讓這張桌子「有故事」）：
1. 桌面中間到前緣是工作區，顏色淺、粗糙度低（常摸常擦）；
2. 右前方是搗藥區，有一圈深色藥漬和細碎刀痕；
3. 左後角有一個淡淡的燒焦圈（放過熱的丹爐蓋）；
4. 桌腳下緣顏色深（地面濕氣）；
5. 下層竹條中間顏色淺（常放東西）。

## 7. 製作階段

### Stage 0｜分析
- 打開 v1 的 `.blend` 和腳本，列出每個零件的尺寸與位置。
- 依 v1 預覽寫出最嚴重的 5 個問題（第 2 節已列，要用你自己的眼睛確認並排序）。

### Stage 1｜參考（imagegen）
- **材質參考板** 1 張：舊榆木桌面（有刀痕、藥漬、燒焦）、竹條（有竹節）、銅包角與銅釘的近照風格，旁邊放色票。
- **設計三視圖** 1 張：v002 桌子的正、側、背，標出第 5 節的改動。
- **關卡**：三視圖尺寸比例和第 4 節一致；材質參考的顏色落在第 6 節色票附近。

### Stage 2｜Blockout（在 v1 基礎上）
- 從 v1 腳本複製出 v2 腳本，先改大形：桌面厚度與凸出、桌腳收分、牙板弧線。
- 渲染正、側、背、3/4，**和 v1 同角度並排**。
- **關卡**：外框與桌面高度不變（誤差 ≤ 2 mm）；剪影比 v1 更有「家具」感。

### Stage 3｜精修
- 倒角、竹節、銅包角、銅釘、拼板縫。
- **關卡**：3/4 視角高光沿邊出現；≤ 3,000 三角面。

### Stage 4｜UV
- 重新展開，桌面木紋方向沿長邊，拼板各自一個島（才能有色差）。
- 密度 512 px/m，島間距 ≥ 8 px。
- 棋盤格渲染檢查有沒有拉伸。

### Stage 5｜材質與貼圖
- 用程序化材質做出第 6 節的效果，**烘焙**成 BaseColor／Normal（OpenGL）／ORM（技能 `blender-texture-baking`）。
- 匯出後，母檔改成用貼圖的材質。確認烘焙後的樣子和程序化版本一致。
- 預覽：
  - 中性光（規格第 8 節）：正、側、背、3/4；
  - 遊戲風格光：丹房室內，桌面上方一盞暖燈，窗光從左邊進來；
  - **0.5 m 桌面特寫**（看刀痕、藥漬、木紋）；
  - **2 m 全身**（看整體會不會太髒太花）；
  - 線框圖。

### Stage 6｜LOD、匯出、回匯
- LOD1 約 50%：減竹節、減銅釘、倒角段數降低。
- 匯出 FBX、GLB（貼圖內嵌）、Unity 貼圖 PNG。
- 回匯檢查：尺寸、面數、材質、貼圖引用。
- **Unity URP 注意**：
  - URP Lit 的金屬度和平滑度放在 Metallic 貼圖的 R 和 A 通道（A 是 smoothness = 1 − roughness），AO 是另一張圖，和 ORM 打包方式不同；
  - **你不用做轉換**。在 README 寫清楚 ORM 的通道內容，Claude Code 整合時會轉成 URP 的格式；
  - 有餘力可以多輸出一張 `T_QX_AlchemyTable_MetallicSmoothness.png`（R=金屬度、A=1−粗糙度），省下轉換步驟。

## 8. 交付清單

- [ ] 參考：材質參考板、設計三視圖、README
- [ ] v2 腳本（無頭重跑，重建出同樣成品）
- [ ] v2 母檔
- [ ] `QX_AlchemyWorkTable_v002.glb`、`.fbx`
- [ ] 貼圖：`T_QX_AlchemyTable_BaseColor.png`、`_Normal.png`、`_ORM.png`（另可加 `_MetallicSmoothness.png`）
- [ ] `QX_AlchemyWorkTable_v002_model_info.json`（接口、碰撞和 v1 相同）
- [ ] `source-qa-report.json`、`roundtrip-report.json`
- [ ] 預覽：第 7 節 Stage 5 列的全部，加上 **v001 和 v002 同角度並排**
- [ ] `README.md`：和 v001 差在哪、哪些是幾何哪些是貼圖、規格試用心得
- [ ] `PRODUCTION_STATUS.md`

## 9. 驗收標準

| 項目 | 標準 |
|---|---|
| 相容 | 外框、桌面高度、原點、接口、碰撞和 v1 完全一致 |
| 品質 | v001 和 v002 並排時，v002 明顯更像「用了很多年的真家具」；0.5 m 特寫有木紋、刀痕、藥漬，2 m 看起來不髒不花 |
| 預算 | LOD0 ≤ 3,000、LOD1 ≤ 1,500；貼圖 ≤ 1024 |
| 色彩 | 落在第 6 節色票 ±10% |
| 技術 | QA 0 errors；回匯尺寸差 ≤ 1 mm；貼圖引用正確 |
| 規格試用 | README 列出建模規格裡做起來不順或不合理的地方（至少寫「沒有」或具體條目） |

## 10. 不要做

- 不要改或刪任何 v001 檔案。
- 不要動桌上的道具（研缽、藥瓶等是協作者 B 的）。
- 不要改 Unity 場景；換成 v002 由 Claude Code 做。
