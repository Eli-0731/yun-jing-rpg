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

## v008 重做（2026-11-13）

依核心組審查重建 Straight、Corner、End 三段，接口維持橋面頂部 0.45 m、樁底 -1 m。使用 Josh `cr_parts.py` 的鑿木板、圓木和綁繩函式，木板有寬窄、翹曲、缺角、細裂與鐵釘；下緣與樁腳加入濕黑、苔色及局部樹皮材質。使用 `cr_mats.py`、`vl_mats.py`、`ti_pipeline.py` 與 Eli 烘焙清單產生 BaseColor、Normal、AO、Roughness、ObjectNormal、Pointiness、Position、ORM、MaskURP。LOD 依零件細節等級拆分。

- 成品：`Straight/v008/`、`Corner/v008/`、`End/v008/`；每段有灰模、FBX、GLB、三層 LOD、碰撞代理、紋理及 `model_info.json`。
- 預覽：`art/previews/valley-and-home-v1/FE01/v008/FE01_Straight_threequarter.png` 等三段。`FE01_vs_FR04.png` 左為本件直段，右為 Josh FR04 獨木橋的材質參照；兩圖光照與構圖不同，僅比木質老化和細節密度。
- QA：三段 `qa_mesh.py` 的退化面、零面積 UV、同向共面、反面封閉件、黑面皆為 0；`qa_uv_overlap.py` 的圖集重疊像素為 0；`qa_fbx.py` 在 1 mm 的同向近共面及零 UV 為 0；八角度背面檢查最大紅面比例為 0。FBX 的獨立零件警告主要是刻意分開的木板、鐵釘與裂縫片。
- 實際工時：約 0.6 小時（含重建、三段烘焙、QA 與審圖）。尚未在 Unity 6000.3.28f1 匯入、以 1.75 m 膠囊走過或核對三段在水邊的接縫。
