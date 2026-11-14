| 項目 | 內容 |
|---|---|
| 誰做的 | z1nnz |
| 工作包 | `docs/execution/2026-11-08/codex-v4-score-and-next.md`，A2 |
| ID | RI02 稻株三階段 |
| 分支／PR | `art/codex-1108-rice-and-ferry` ／ PR 待核心組建立 |
| 版本 | v006；早期灰模、材質與 v005 在來源工作樹保留，這裡只交 v006 |
| 狀態 | Exported、Blender 回匯 Imported、Visually Verified；In-game Verified 未驗 |
| 素材來源 | 自製；從 `feature/codex-v3-d2-valley` 的評分已收版本轉交 |

幼苗、青稻、金稻各有 LOD0/1/2，全部打包在 `v006/RI02_Rice.fbx` 與 `.glb`。三階段 LOD0 分別為 483、1,117、1,545 三角面；貼圖 11 張，來源在 `art/textures/valley-and-home-v1/RI02/v003/`。母檔在 `art/source/valley-and-home-v1/RI02/RI02-rice-pack-v006.blend`。三視圖取評選的 candidate 02。

QA JSON 均記錄 `pass: true`、errors 0；回匯尺寸差異在數微米量級。QA 仍提示大量 UV 疊用、重複頂點和部分隱藏背靠面，這些不能直接解讀為烘焙材質可靠；原版 `model_info.json` 的 WindWeight 預期與回匯紀錄中的空頂點色欄位也需在 Unity 導入時核對。視覺預覽已打開檢查金稻遊戲光圖；葉和穗能辨識，細節仍偏風格化。
