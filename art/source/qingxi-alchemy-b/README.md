# B｜溪畔採集後的煉製小工坊（feature/qingxi-alchemy-workshop-v1）

作者：joshsu54（AI 三視圖、方向）＋ Claude Opus 5.5（Claude Code：程序化建模、烘焙、驗證、示範）。

本 PR 只新增檔案，沒有修改：

- 正式 API（`services/api`）
- 契約（`packages/contracts`）
- 內容資料（`packages/content`）
- Unity 主場景

## 1. 交付內容

| 項目 | 位置 | 數量 |
|---|---|---|
| AI 三視圖＋審閱紀錄 | `art/references/qingxi-alchemy-b/`（`manifest.json` 記錄每件的已知構造與推定部分） | 12 張 |
| 程序化原始碼 | `art/source/qingxi-alchemy-b/*.py` | — |
| 原始 .blend | `art/source/qingxi-alchemy-b/blend/<key>_v001.blend` | 程序化分件（隱藏）＋烘焙後的遊戲網格＋LOD |
| 佈局場景 | `art/source/qingxi-alchemy-b/blend/QA_Workshop_Layout_v001.blend` | — |
| GLB | `art/exports/qingxi-alchemy-b/<ID>_<Name>/v001/<key>.glb` | 14 個（12 件；B01、B10 各兩種狀態）；LOD0，內嵌貼圖 |
| FBX | 同上，`<key>.fbx` | LOD0–2，`_LODn` 命名，供 Unity LOD Group |
| 貼圖 | 同上，`textures/` | BaseColor、ORM（R=AO、G=粗糙、B=金屬）、Normal（OpenGL）；B01 加熱狀態另有 Emissive |
| 每件資料 | 同上，`<key>_model_info.json`、`validation.json` | 尺寸、三角面、碰撞建議、socket、狀態、檢查結果、檔案 sha256 |
| 渲染 | `art/previews/qingxi-alchemy-b/<ID>/<state>/` | 每個狀態：10 方位中性光、2 張特寫（正面／側面）、線框、4 張風格光、材質表 |
| 爐蓋配合 | `art/previews/qingxi-alchemy-b/B01_B02_fit/`、`art/exports/qingxi-alchemy-b/fit_B01_B02.json` | 關閉（冷／加熱）、開蓋、接縫特寫 |
| 工坊佈局 | `art/previews/qingxi-alchemy-b/layout/` | 玩家視角全景、走到丹爐前的視角、俯視佈局草圖 |
| 玩法示範 | `tools/qingxi-alchemy-b/` | 辨材→配伍→煉製→領成品；`CONTRACT.md`；單元測試 |
| 示範錄影 | `art/previews/qingxi-alchemy-b/demo/walkthrough_player_view.mp4` | 1 支，玩家視角，H.264 1280×720 12 fps，185 秒 |

12 件：

- B01 青銅小丹爐（冷／加熱）
- B02 可拆爐蓋
- B03 石藥杵臼
- B04 二層竹分料盤
- B05 三層草藥抽屜櫃（3 個抽屜可分開）
- B06 裝水陶甕（蓋可分開）
- B07 木燃料箱
- B08 透氣晾藥筐
- B09 濾渣布架
- B10 封蠟藥瓶（裝滿／空瓶，軟木塞可分開）
- B11 配方竹簡座
- B12 排煙矮煙囪

尺寸、三角面與上限見 `ART_DIRECTION.md`。

沒有重做 PR #31 的素材（草藥、礦石、蘆葦、木板）。示範只透過 `tools/qingxi-alchemy-b/src/materials-adapter.mjs` 讀取 PR #31 的三種採集產物（commit e6202d7，`tools/gathering-point-demo/main.js`）。PR #31 併入 main（0f1e023）時只收素材，採集示範與其 NODES 不在 main；e6202d7 在 main 的歷史中，所以 adapter 仍鎖定這個 commit。正式接線時改讀伺服器背包，只需替換 adapter。

## 2. 指令

```bash
# 建模＋烘焙＋匯出＋渲染（Blender 5.2，GPU 可用 OptiX/CUDA）
blender -b --python-exit-code 1 --python art/source/qingxi-alchemy-b/build.py -- B01 B02     # 不加 ID = 全部
blender -b --python-exit-code 1 --python art/source/qingxi-alchemy-b/build.py -- B07 --no-render
blender -b --python-exit-code 1 --python art/source/qingxi-alchemy-b/combo.py                # B01+B02 配合檢查
blender -b --python-exit-code 1 --python art/source/qingxi-alchemy-b/layout.py               # 佈局、全景、layout.json
uv run --no-project --with pillow python art/source/qingxi-alchemy-b/sheets.py               # 材質表
uv run --no-project --with pillow python art/source/qingxi-alchemy-b/layout_sketch.py        # 俯視草圖標註

# 示範
node tools/qingxi-alchemy-b/serve.mjs            # http://127.0.0.1:8765/tools/qingxi-alchemy-b/
node --test tools/qingxi-alchemy-b/tests/*.test.mjs
# 錄影：開 ...?walk 自動走一輪（影格寫到系統暫存），再
blender -b --python-exit-code 1 --python art/source/qingxi-alchemy-b/encode_walkthrough.py -- <影格資料夾> 12
```

## 3. 檢查結果

狀態用詞：

- **Exported**：已匯出
- **Imported**：已重新匯入
- **Visually Verified**：已看過渲染
- **In-game Verified**：已在遊戲內驗證

| 檢查 | 結果 |
|---|---|
| GLB 在 Blender 重新匯入 | 14／14：三角面數一致，包圍盒誤差 < 2 mm（`validation.json`） → **Imported（Blender）** |
| 原點在底面中心、1 單位 = 1 m、正面 −Y | 14／14（`originAtBase`） |
| LOD0 在修正後的上限內 | 14／14 |
| GLB 材質 alphaMode | 由 `validation.json` 的 `glbAlphaModes`／`alphaModeOk` 直接讀 GLB 檢查：B08 為 MASK（cutoff 0.5），其餘烘焙材質為 OPAQUE；B10 玻璃另為 BLEND（刻意） |
| 網格健康 | 沒有鬆散頂點或零面積面。開放邊只出現在刻意不封口的薄件：繩、布、玻璃單層殼、管口 |
| 爐蓋與丹爐 | 三角面重疊 0；徑向間隙 8 mm；垂直間隙 1 mm |
| 視覺審閱 | 每件至少兩輪快速渲染（正、斜、背、特寫）並修正，最後看過完整渲染 → **Visually Verified（Blender Cycles）** |
| 示範單元測試 | `node --test`：13／13 通過 |
| 示範錄影（腳本驅動，固定 12 fps 時間步，不是手動操作） | 185 秒，一支：第 1 輪已知配方（先故意選錯→具體回饋），約 96 秒收取成功、約 115 秒第一次領取，再按兩次顯示「已領過，結果不增加」；第 2 輪研究變體用武火，約 179 秒顯示失敗原因並退回赤露參漿果 ×1、玉脈晶 ×1 → 已知配方遠低於 5 分鐘 |
| `npm test`（既有測試） | 55／55 通過（本 PR 沒有修改受測程式） |
| Unity 匯入、遊戲內光照、手機效能、LOD 切換距離 | **尚未驗證**（本機沒有對這批素材開 Unity） |

## 4. 等核心組接線的項目

1. Unity：把 FBX 放進場景，設定 LOD Group 的切換比例。碰撞依 `model_info.json` 的建議（Box／Cylinder）建立。B05 抽屜、B06 蓋、B10 軟木塞是分開的節點。
2. 煙道：B01 `flue_outlet` 到 B12 `flue_inlet` 之間的彎管只是佈局佔位，需要場景管件。棚架、長凳和比例人也都是佔位。
3. 伺服器：依 `tools/qingxi-alchemy-b/CONTRACT.md` 第 6 節決定以下事項：
   - item id 對應
   - `body-bath` 的材料
   - 研究變體的配方
   - `recipe.seconds`
   - 批次純度欄位
   - 工坊接近檢查
4. B01 冷／加熱兩種狀態是兩個 GLB；加熱時爐口的 Emissive 需要搭配場景點光源（示範中用 PointLight 閃動）。
5. B10 玻璃是 alpha blend，在 URP 要設為 Transparent；B08 編織孔是 alpha clip，要設為 Alpha Clipping。

## 5. 狀態紀錄

| 件 | 參考圖審閱 | 程序化模型 | 烘焙＋LOD | Exported | Imported（Blender） | Visually Verified（Cycles） | In-game Verified |
|---|---|---|---|---|---|---|---|
| B01–B12（14 個狀態） | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — 未驗證 |

過程中修過、值得核心組知道的問題：

- **AO 烘焙偏黑**：第一輪烘焙時，隱藏的程序化分件仍會遮住遊戲網格，AO 大片發黑。現在烘焙時隱藏其他網格，AO 距離依物件尺寸設定（0.03–0.35 m），並重調石、竹、青瓷、竹簡顏色。
- **B08 alphaMode**：第一版 GLB 寫成 BLEND（引擎會當半透明排序）。現在匯出材質的 alpha 先經 Math「Round」，GLB 寫成 MASK，validation 直接讀 GLB 檢查。
- **B01 原點**：底座石墊有幾 mm 低於 0，`game_mesh` 現在會把 z < 0 的頂點夾到 0（先確認誤差 < 1 cm）。

已知限制：

- 刻意不封口的薄件（繩、布、單層玻璃、管口）仍有開放邊。
- 棚架、長凳、彎管、比例人是佈局佔位，不屬於交付素材。
- 全景圖中比例人擋到燃料箱的一部分。
