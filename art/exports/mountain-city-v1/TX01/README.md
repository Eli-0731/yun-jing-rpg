| ID | 名稱 | 狀態 | 負責人 | 版本 | 輸出 |
|---|---|---|---|---|---|
| TX01 | 飛升榜與空白匾額 | 交付候選，待 Unity 場景驗收 | z1nnz + Codex | v004 | `v004/TX01_Board.*`、`v004/TX01_Plaque.*` |

以 v004 材質稿完成 LOD、簡化碰撞、FBX/GLB 輸出及 Blender 回匯。榜面和匾額維持空白，沒有文字。榜主體 LOD0/1/2 為 4580/3296/1602 三角面，另有 LOD0 裝飾 4452 面；匾額 LOD0/1/2 為 44/30/14 面，另有裝飾 176 面。兩者均有 `UCX_TX01_*` 碰撞網格。

來源：`art/source/mountain-city-v1/TX01/TX01-ascension-board-material-v004.blend`、`TX-Plaque-material-v004.blend`；已另存 `*-pack-v004.blend`。參考圖在 `art/references/mountain-city-v1/TX01/`，貼圖在 `art/textures/mountain-city-v1/TX01/v004/`。正面預覽在 `art/previews/mountain-city-v1/TX01/`，本次重新輸出的三分之四視角在 `final-v004/`。

驗證：`verify_tx01_v004.py` 對兩件 FBX 與 GLB 回匯，共四次通過；LOD 網格及碰撞網格存在，三角面數符合輸出。已實際檢視榜與匾額三分之四視角。舊來源 Blender 儲存時仍報原工作樹貼圖路徑錯誤，打包腳本會重連到本分支貼圖；匯出可回匯，Unity 內材質與碰撞仍未驗收。不得將此記成 Unity 可運行。

本輪只完成 v004 的輸出包；沒有提交失敗的中間版。後續需要在山城場景確認朝向、落地與互動距離。

## v005（2026-11-13 審查重做）

依 11/12 審查調整飛升榜與空白匾額。屋瓦改用 John MC01 共用 2048 Trim Sheet 的黛瓦條帶，木構改用舊木及木梁條帶；石基改以 John `build_mc01.py` 的石塊函式組成兩層錯縫石塊，厚度由 0.32 m 增至 0.64 m，低層有潮濕苔色並經鑿面處理。榜面 40 格及匾額均保留空白。John 的原建模函式及四張共用貼圖存於 `art/source/mountain-street-houses-a/`、`art/textures/mountain-street-houses-a/`；本件重建腳本為 `art/source/mountain-city-v1/build_tx01_v005.py`。

交付位於 `v005/`：榜與匾的灰模、FBX、GLB、LOD0–2、碰撞網格及 `model_info.json`；來源檔為 `art/source/mountain-city-v1/TX01/*-pack-v005.blend`。預覽位於 `art/previews/mountain-city-v1/TX01/v005/`。Blender 回匯四次通過；榜 LOD0／1／2 為 11,052／7,956／3,868 三角面，匾為 44／30／14 三角面。v005 的退化面、零面積 UV、反向封閉面均為 0。榜主網格仍有 493 組同向共面（v004 原版為 507 組），主要在原有榜格與結構的貼合處；匾額銅邊仍有 20 組共面。共用 Trim Sheet 的 UV 重用屬設計用途。Unity 山城場景的材質、碰撞、可讀距離尚未驗證。
