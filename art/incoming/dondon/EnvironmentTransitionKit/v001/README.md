# 環境收邊模組包（EnvironmentTransitionKit v001）

來源：[joshsu54/dondon](https://github.com/joshsu54/dondon) 分支 `claude/environment-transition-kit`、提交 `45ba236` 的 `Environment_Transition_Kit/`；
310 個檔案與來源 SHA-256 相同，清單見 `SOURCE.json`。單件預覽縮為 512 px（原 1024 px 留在來源儲存庫）。

因為每個 `.blend` 以相對路徑 `//../03_Textures/` 引用貼圖，本包**保留來源的資料夾結構**（素材交接清單允許此做法）。原套件說明在 `README_kit.md`。

## 內容

| 編號 | 內容 | 可編輯原檔 | 引擎交換檔 |
| --- | --- | --- | --- |
| A01–A11 | 不規則道路收邊 11 件 | `01_Blender/road_edge_modules_v01.blend`（每件一個 Collection） | `02_Exports/RoadEdge/*.fbx` |
| B01–B10 | 河岸收邊 10 件 | `01_Blender/riverbank_modules_v01.blend` | `02_Exports/Riverbank/*.fbx` |
| C01–C08 | 橋頭收邊 8 件 | `01_Blender/bridgehead_modules_v01.blend` | `02_Exports/Bridgehead/*.fbx` |
| D02 | 木造梁橋（10 m 跨、木排架橋墩、欄杆） | `01_Blender/timber_bridge_v01.blend` | `02_Exports/Bridge/SM_Bridge_Timber_A.fbx` |
| D01 | 獨木橋（可選件） | `01_Blender/log_bridge_v01.blend` | `02_Exports/Bridge/SM_Bridge_Log_A.fbx` |
| — | 測試輔助（1 m 方塊、路芯、佔位橋面） | 在各 `.blend` 的 `COL_TEST_Only` | `02_Exports/_TestHelpers/*.fbx` |

根目錄 `model_info.json` 是 31 件的總表（尺寸、各 LOD 三角面、材質、檔案位置、UV／LOD／碰撞／動畫狀態），`validation.json` 彙整來源端實際跑過的檢查結果。
每件的 `model_info.json`、`validation.json`、`views.json` 與預覽在 `04_Previews/Individual/<編號>_<ID>/`。
總表 `04_Previews/Sheets/`、拼裝展示 `04_Previews/Showcase/`、檢查報告 `06_Reports/QA_Report.md`、引擎匯入說明 `06_Reports/README_Integration.md`。

## 規格

- 公尺、Z 向上；模組行進方向 +X、+Y 為左側（預覽的 01_front 由 -Y 看）。FBX：Forward -Z、Up Y、FBX All、Apply Transform、頂點色 Linear。
- Pivot：A、B 在入口接頭中心；C01–C05、C07、C08 共用橋頭座標系；橋在入口端橋面中心（放進橋頭座標系平移 (2, 0, +0.15)）。
- 每件有 LOD0／LOD1／LOD2 與 `_COL` 碰撞代理；UV 已整理（2 m 一個 UV 單位），地表貼圖為 1024² 可平鋪 PBR，`M_TerrainBlend` 用頂點色 Mask 混合（引擎內需依 README_Integration 重建）。
- 三角面與尺寸：`06_Reports/ASSET_MANIFEST.md`；接頭規格：`06_Reports/CONNECTOR_SPEC.json`。

## 驗證

- 來源端：接頭／串接／配對誤差 ≤ 0.0005 mm、細節不越界、29 件 FBX 在 Blender 回匯一致、木橋擱置與標高檢查，見 `06_Reports/qa/` 與 `QA_Report.md`。
- 本次交接：`handoff_check.json`（在接收端路徑重開每個 `.blend`、確認貼圖都找得到、FBX 回匯）。
- **未做：** Unity 匯入、URP 材質、手機效能、引擎內碰撞與行走。Blender 能開、FBX 能回匯，不代表 Unity 已驗收。

## 設計參考（請注意）

`00_References/ThreeViews/` 與 REF_A–E 是**建模前**由腳本依規格數值繪製的工程三視圖，**不是 AI 生成的三視圖**（製作當時的環境沒有生圖工具）；REF_F 與 `04_Previews/` 都是建模後的渲染。若要符合本儲存庫「先 AI 三視圖再建模」的規定，需要補 AI 三視圖或由使用者確認例外。

## 製作工具

`05_Scripts/`：全部生成、貼圖烘焙、檢查、匯出、出圖腳本（`build_all.sh` 依序執行；需 Blender 5.2 背景模式與 Python 3＋Pillow）。腳本依套件資料夾結構讀寫，可在本資料夾內直接重建。

## 來源與授權

- 作者：joshsu54 的 dondon 專案，由 AI 程式助理以 Blender Python 程序化建模與烘焙貼圖；沒有使用外部模型、貼圖或素材庫。
- 授權：來源儲存庫沒有授權檔；轉入《雲境》的使用條件需由 joshsu54 與 z1nnz 確認。
