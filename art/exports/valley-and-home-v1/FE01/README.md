| 項目 | 內容 |
|---|---|
| 誰做的 | z1nnz |
| 工作包 | `docs/execution/2026-11-08/codex-v4-score-and-next.md`，A2 |
| ID | FE01 木棧橋：Straight、Corner、End |
| 分支／PR | `art/codex-1108-rice-and-ferry` ／ PR 待核心組建立 |
| 版本 | Straight v006，Corner v004，End v004；早期灰模與修正版本留於來源工作樹 |
| 狀態 | 三件均 Exported、Blender 回匯 Imported、Visually Verified；In-game Verified 未驗 |
| 素材來源 | 自製；從 `feature/codex-v3-d2-valley` 的評分已收版本轉交 |

每件有 LOD0/1/2 和獨立碰撞網格。主網格 LOD0 三角面：直段 716、轉角 1,112、盡頭 1,040；可關閉的繩／竹細節另為 1,352、1,424、2,028 面。三件各有 FBX、GLB、QA、回匯資料；`Straight/v006/model_info.json` 在製作時曾記「Corner、End 未完」，本次交件以另外兩件的 v004 匯出和組合預覽為準。

紋理使用 `art/textures/valley-and-home-v1/FE01/v004/` 六張 BaseColor 與 `v003/` 的共用 Normal、ORM。變體並排預覽 `art/previews/valley-and-home-v1/FE01/variants-v004/FE01_export_straight_corner_end_A11_materials.png` 已打開檢查。木材與橋樁仍偏乾淨、偏直，缺生活磨耗；此為評分 70 的可收候選。QA 零 errors，但回匯有疊 UV、接觸面及樁底低於地面警告；樁底是設計的入水深度。Unity 中的接縫、碰撞與走路手感未驗。
