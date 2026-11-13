| 項目 | 內容 |
|---|---|
| 誰做的 | z1nnz |
| 工作包 | `docs/execution/2026-11-08/codex-v4-score-and-next.md`，A2 |
| ID | FE02 擺渡船 |
| 分支／PR | `art/codex-1108-rice-and-ferry` ／ PR 待核心組建立 |
| 版本 | v007；早期 v001–v006 因船長、法線與船身外觀修正留在來源工作樹 |
| 狀態 | Exported、Blender 回匯 Imported、Visually Verified；In-game Verified 未驗 |
| 素材來源 | 自製；從 `feature/codex-v3-d2-valley` 的評分已收版本轉交 |

6 m 船身、棚篷、撐篙和可關閉的修補細節。`v007/` 含 FBX、GLB、各 LOD QA 與回匯數據；貼圖在 `art/textures/valley-and-home-v1/FE02/v002/`。已打開檢查 `art/previews/valley-and-home-v1/FE02/v007/FE02_ferry_threequarter_game_light.png`：可辨識為有棚渡船，但船身線條偏硬，舊船彎曲與補丁仍不足，因此是評分 68 的候選。沒有 Unity 水面、浮力和遊玩驗證。

## v008（11/13 重做）

依 11/12 核心組審查補上彎曲船舷、船首尾翹度、外側修補木片、竹編弧篷、橫向篷骨及舊布補片。新增部分沿用 Josh 的 `cr_parts.py`、`vl_mats.py`，貼圖依 Eli 的烘焙清單輸出 BaseColor、Normal、ORM、AO、ObjectNormal、Pointiness、Position 等。`v008/` 提供 FBX、GLB、灰模、貼圖與 QA 紀錄；來源是 `art/source/valley-and-home-v1/FE02/fe02-rework-pack-v008.blend`，預覽是 `art/previews/valley-and-home-v1/FE02/v008/FE02_threequarter.png`。

檢查：FBX 19,576 三角面，同向重疊面 0、零面積 UV 0；Blender 新增幾何 UV 衝突 0，背面八視角最高紅色占比 0。舊船殼保留 2 處極小同向重疊面及雙面薄片，舊共用貼圖有重疊 UV；新增材質圖集沒有重疊。已目視確認整船形狀與篷架，Unity 水面、浮力及遊玩狀態未驗。
