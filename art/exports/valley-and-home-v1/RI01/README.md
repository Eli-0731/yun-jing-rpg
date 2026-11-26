| 項目 | 內容 |
|---|---|
| 誰做的 | z1nnz |
| 工作包 | `docs/execution/2026-11-08/codex-v4-score-and-next.md`，A3 |
| ID | RI01 水田與直／角／T 田埂 |
| 分支／PR | `art/codex-1108-rice-and-ferry` ／ PR 待核心組建立 |
| 版本 | v014 修正版；v001–v013 多次幾何及 QA 修正留在來源工作樹，本分支只交 v014 |
| 狀態 | Exported、Blender 回匯 Imported、部分 Visually Verified；In-game Verified 未驗 |
| 素材來源 | 自製；沿用 `feature/codex-v3-d2-valley` 的原創三視圖與材質母檔，修正 v013 |

## 本次修正

原 v013 三種田面在 LOD0 各有兩條 z-fighting 訊息：一條是田基內兩塊石面，另一條是西側田基與狀態面側邊。從來源母檔重包時，將其中一塊連通石島沿田埂移 0.35 m，三種狀態面上抬 5 mm，並把其西側邊界往田內收 15 mm。沒有改變三個狀態、三種田埂的 LOD 數量或田地 10 × 6 m 規格。

`v014/qa_summary.json` 的 **18 種狀態／LOD／田埂組合全部 pass，errors 0**；FBX 與 GLB 回匯 `v014/reimport_validation.json` 為 pass，四組匯出均無缺網格與三角數不符，最大尺寸誤差遠低於 2 cm。逐件 QA 仍有疊 UV、重複頂點與接觸面警告，需在未來重烘焙貼圖時留意。

已打開查看 `art/previews/valley-and-home-v1/RI01/v014/RI01_LOD0_LOD1_detail_off_material.png`：濕田輪廓與田埂可辨，但回匯預覽的田埂呈白色，材質表現尚不合格；Dry、Grown 並未逐張人工視覺確認。這一批作為**技術 QA 通過的候選**交付，不宣稱美術最終驗收或 Unity 可玩。`art/source/valley-and-home-v1/package_ri01_v014.py` 可重建來源與匯出；`qa_ri01_pack_v014.py` 可重跑檢查。
