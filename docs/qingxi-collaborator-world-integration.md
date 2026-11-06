# 青溪協作者模型接入｜2026-10-28

本輪把協作者交付從「已進儲存庫」推進到**入口片區可見**。原始 GLB、三視圖和 Blender 母檔仍在原目錄，這裡只轉檔、排放與接線；模型原作者沒有改記為核心組。PR #38 與 #39 的內容目前已整合到本草稿分支；#39 是協作者明示的第一批，後續 A07–A12 仍待交付。

| 地點 | 原作者 | 瀏覽器橫向入口片區 | Unity 較大青溪鎮 |
|---|---|---|---|
| 村口告示與三處線索 | Eli-0731 | Q01–Q04 實際 GLB | Q01 轉 FBX 擺在城鎮出生點附近 |
| 演武棚與練功石 | Johnnnny0823 | 兩件實際 GLB | 演武棚轉 FBX 擺在廣場支路 |
| 回村籃、桌、匣 | Eli-0731 | C01–C03 實際 GLB | C02 轉 FBX 擺在坊市入口附近 |
| 煉製爐、藥臼、藥櫃 | joshsu54 | B01／B03／B05 實際 GLB | B01 轉 FBX 擺在坊市附近 |
| 演武區新版器具 | Johnnnny0823 | 氣勁木樁、身法木樁、旗與兵器架 GLB；演武地標開啟獨立調息／格擋玩法 | 四件 FBX 擺在城鎮出生點的演武支路 |
| 山兔林地第一批 | Johnnnny0823 | A01–A06 地形與障礙 GLB；林地地標開啟閃避／格擋／破綻玩法 | 倒木、苔石、立岩及樹根四件 FBX 擺在狩獵路線附近 |

入口 PWA：先在 `tools/qingxi-trial/`、`tools/training-yard-demo/`、`tools/qingxi-encounter-a/` 各執行一次 `npm ci`，再從專案根目錄執行 `node tools/qingxi-trial/serve.mjs`，開啟 `http://127.0.0.1:4173/tools/qingxi-trial/`。角色從告示牌旁進入，可走到演武、溪畔、回村桌、工坊和山兔林地；在地標附近按互動會於場景中開啟協作者的本機玩法，返回後仍在原地。這是 **48 × 35 m 入口片區**，不是把 180 × 140 m 較大世界搬入瀏覽器。各獨立玩法尚未共用正式背包或完成跨頁進度同步。

Unity：執行 `YunJing.Editor.QingxiUnifiedWorldBuilder.Generate` 生成 `Assets/QingxiWorld/Generated/QingxiUnifiedWorld.unity`。最初四件 FBX 由 `tools/art/import_collaborator_novice_to_unity.py` 從原 GLB 轉換；其餘八件直接複製協作者交付的 FBX，存於 `apps/game/Assets/YunJing/Models/CollaboratorNoviceV1/`，各保留原始作者。Unity 在城鎮出生點、坊市和狩獵區的既有 NavMesh 附近擺放，按角色高度校正比例。它們目前**只有視覺擺放，無專用碰撞與正式服務端互動**；演武棚原件約 39,236 多邊形，手機 LOD 尚未處理。

已驗證：入口 PWA 實際載入 22／22 件；本機測試檢查模型檔案、GLB 標頭和擺位；演武規則 11 項及山兔遭遇規則 15 項測試通過；Chromium 橫向試走可從主場景打開演武玩法，山兔頁載入無頁面錯誤。Unity `6000.0.82f1` 批次生成場景成功，日誌列出 `collaborator props=12`，更新後 Windows 試玩程式也成功建置於 `artifacts/windows-unified-world/YunJingUnifiedWorld.exe`（建置產物不進 Git）。**尚未完成**：玩家視角全路線人工走位、Unity 真機畫質及效能、正式場景碰撞、PWA 延伸玩法與正式角色背包互通。

下一段：用實際 Unity 相機走過新演武與狩獵擺位，修正比例、地面接縫與遮擋；再讓練功、林地與回村玩法共用同一角色狀態。新增碰撞前先確認不阻擋廣場到坊市及狩獵區的路線。
