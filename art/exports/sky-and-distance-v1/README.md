| 項目 | 內容 |
|---|---|
| 誰做的 | z1nnz |
| 工作包 | `docs/execution/2026-11-08/codex-v4-score-and-next.md`，A1 |
| ID | MO01、SK 弧面骨架 |
| 分支／PR | `art/codex-1108-moon-and-skyline-arc` ／ PR 待核心組建立 |
| 版本 | MO01 細彎缺月最終候選、SK 弧面骨架 v001 |
| 狀態 | MO01：Exported、Imported（Blender 回匯）、Visually Verified；SK：Exported、Imported（Blender 回匯）、灰模 Visually Verified；兩件 In-game Verified 均未驗 |
| 素材來源 | 自製素材；從本儲存庫 `feature/codex-v3-d1-sky` 工作樹的已評收版本轉交，未使用外來模型 |

## 交付範圍

- `MO01/`：1 m 方形雙三角面月亮載體，白天、夜晚與光暈三張 2048² RGBA 圖；另有灰度剪影、FBX、GLB、Blender 回匯及貼圖檢查紀錄。細彎朝左、開口朝右。模型 4 頂點、2 三角面、1 材質。月亮在遊戲裡固定位置與晝夜切換由 D 部分實作，本件不含執行邏輯。
- `SK/`：半徑 800 m、高 240 m、90° 的向內彎曲遠景貼圖載體；128 三角面、1 材質、1 UV、QA errors 0，FBX／GLB 回匯尺寸偏差小於 1 mm。此件只有骨架；SK01–06 遠景圖片尚未定稿，暫不可當成完成的天空美術。
- 可編輯母檔位於 `art/source/sky-and-distance-v1/`；選定參考圖在 `art/references/sky-and-distance-v1/`；實際看過的預覽在 `art/previews/sky-and-distance-v1/`。

## 已知限制

- MO01 的夜間山谷預覽是合成檢視，不能視為 Unity 場景已導入；小尺寸預覽另見 `MO01_night_64px.png`。
- SK 弧面尚無任何已通過的最終遠景貼圖。它只支援後續 SK01–06 製作。
- 本次只複製評分已收的最終版本；前期未通過的候選、`rejected-notch-v1/` 和 SK01 失敗的抽圖未納入。
