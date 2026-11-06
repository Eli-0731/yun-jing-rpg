# 丹房工作桌 v1（QX_AlchemyWorkTable_v001）

z1nnz 指導、Claude Code 製作（核心組），2026-10-29。用來取代新手村丹房角的灰盒桌。尺寸沿用 joshsu54 灰盒：2.0 × 0.72 m，桌面高 0.78 m，B03 研缽、B08 晾藥籃、B10 藥瓶、B11 食譜架都放在這個高度。

| 項目 | 內容 |
|---|---|
| 參考 | `art/references/qingxi-alchemy-table-v1/`（AI 三視圖，先於建模；目前只存了縮圖） |
| 母稿 | `art/source/qingxi-alchemy-table-v1/qingxi-alchemy-table-v1.blend`，由 `tools/art/build_qingxi_alchemy_table_v1.py` 重建 |
| 匯出 | `QX_AlchemyWorkTable_v001.glb`；Unity：`apps/game/Assets/YunJing/Models/AlchemyTableV1/QX_AlchemyWorkTable_v001.fbx`（含 LOD0／LOD1） |
| 尺寸 | 2.01 × 0.73 × 0.785 m（銅包角凸出 5 mm）；原點在底部中心，ground_z = 0 |
| 面數 | LOD0 1,320 三角面，LOD1 660 |
| 材質 | 3 個純色材質：舊榆木、竹、氧化銅；沒有貼圖 |
| 碰撞 | 建議一個盒子 2.0 × 0.72 × 0.78 m（場景生成器已加） |
| QA | 母稿 0 錯誤、1 警告（18 個 n-gon，竹條端面，平面硬面可接受）。GLB／FBX 回匯尺寸與面數一致、0 錯誤；GLB 的重複頂點警告來自 glTF 依平面著色拆點，可接受。報告：`source-qa-report.json`、`roundtrip-report.json` |
| 預覽 | `art/previews/qingxi-alchemy-table-v1/`（正、側、背、3/4 視角附 1.75 m 人形尺）；新手村 `03-alchemy-B.png` |

## 推定設計與未完成

- 三視圖只拿得到 200 px 縮圖，榫卯和銅包角的細節依提示詞製作，列為推定設計；原圖在 z1nnz 的 Canva 素材庫（`MAHZU4Vva18`）。
- 還沒有木紋、刀痕貼圖，近看會偏乾淨。
- 沒有在手機上量測。
