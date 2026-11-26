| 項目 | 內容 |
|---|---|
| 誰做的 | z1nnz |
| 工作包 | `docs/execution/2026-11-08/codex-v4-score-and-next.md`，A2 |
| ID | FE03 渡口小棚 |
| 分支／PR | `art/codex-1108-rice-and-ferry` ／ PR 待核心組建立 |
| 版本 | v007；早期灰模及材質版本留在來源工作樹 |
| 狀態 | Exported、Blender 回匯 Imported、Visually Verified；In-game Verified 未驗 |
| 素材來源 | 自製；從 `feature/codex-v3-d2-valley` 的評分已收版本轉交 |

約 2.91 × 2.35 × 2.59 m 的渡口小棚與獨立繫船柱。主棚 LOD0 6,024 三角面，可關閉細節 376 面；附 LOD1/2、碰撞、FBX、GLB 與 QA 記錄。貼圖位於 `art/textures/valley-and-home-v1/FE03/v005/`。已實際查看 `art/previews/valley-and-home-v1/FE03/v007/FE03_shed_threequarter.png`，青灰瓦、木構和繫船柱可辨，棚體仍偏方正，故作評分 72 的候選。Unity 中與棧橋、船的同場比例和碰撞未驗。

## v008（11/13 重做）

在原有棚體及繫船柱旁補上舊貨箱、箱板、懸掛舊布、斜靠船槳等渡口生活痕跡。新增部分沿用 Josh 的 `cr_parts.py`、`vl_mats.py`，貼圖依 Eli 的烘焙清單輸出 BaseColor、Normal、ORM、AO、ObjectNormal、Pointiness、Position 等。`v008/` 提供 FBX、GLB、灰模、貼圖與 QA 紀錄；來源是 `art/source/valley-and-home-v1/FE03/fe03-rework-pack-v008.blend`，預覽是 `art/previews/valley-and-home-v1/FE03/v008/FE03_threequarter.png`。

檢查：FBX 9,412 三角面，同向重疊面 0、零面積 UV 0；Blender 新增幾何 UV 衝突 0，背面八視角最高紅色占比 0.01%。原有棚體與繫船柱仍有雙面薄片及共用貼圖的重疊 UV。已目視確認新道具的位置與可辨識度，Unity 中與棧橋、船的同場比例和碰撞未驗。
