# 青溪協作者模型接入｜2026-10-28

本輪把協作者交付從「已合併儲存庫」推進到**入口片區可見**。原始 GLB、三視圖和 Blender 母檔仍在原目錄，這裡只轉檔、排放與接線；模型原作者沒有改記為核心組。

| 地點 | 原作者 | 瀏覽器橫向入口片區 | Unity 較大青溪鎮 |
|---|---|---|---|
| 村口告示與三處線索 | Eli-0731 | Q01–Q04 實際 GLB | Q01 轉 FBX 擺在城鎮出生點附近 |
| 演武棚與練功石 | Johnnnny0823 | 兩件實際 GLB | 演武棚轉 FBX 擺在廣場支路 |
| 回村籃、桌、匣 | Eli-0731 | C01–C03 實際 GLB | C02 轉 FBX 擺在坊市入口附近 |
| 煉製爐、藥臼、藥櫃 | joshsu54 | B01／B03／B05 實際 GLB | B01 轉 FBX 擺在坊市附近 |

入口 PWA：`tools/qingxi-trial/`，從專案根目錄執行 `node tools/qingxi-trial/serve.mjs`，開啟 `http://127.0.0.1:4173/tools/qingxi-trial/`。角色從告示牌旁進入，可走到演武、溪畔、回村桌和工坊；右上方連到三個協作者獨立玩法頁。這是 **48 × 35 m 入口片區**，不是把 180 × 140 m 較大世界搬入瀏覽器。

Unity：執行 `YunJing.Editor.QingxiUnifiedWorldBuilder.Generate` 生成 `Assets/QingxiWorld/Generated/QingxiUnifiedWorld.unity`。4 件 FBX 由 `tools/art/import_collaborator_novice_to_unity.py` 從原 GLB 轉換，存於 `apps/game/Assets/YunJing/Models/CollaboratorNoviceV1/`，每件皆有往返檢查與來源登記。Unity 在城鎮出生點及坊市的既有 NavMesh 附近擺放，並按角色高度校正比例。它們目前**只有視覺擺放，無專用碰撞與正式服務端互動**；演武棚原件約 39,236 多邊形，手機 LOD 尚未處理。

已驗證：入口 PWA 實際載入 12／12 件；本機測試檢查模型檔案、GLB 標頭和擺位；Blender 4 件 FBX 往返的網格數及面數一致；Unity `6000.0.82f1` 批次生成場景成功，日誌列出 `collaborator props=4`；Windows 試玩程式也成功建置於 `artifacts/windows-unified-world/YunJingUnifiedWorld.exe`（建置產物不進 Git）。兩次 Unity 批次程序均以回傳碼 0 結束。**尚未完成**：玩家視角全路線人工走位、Unity 真機畫質及效能、12 件全部接入大世界、PWA 延伸玩法與正式角色背包互通。

下一段：以現有材質與角色尺度檢視四個 Unity 擺位，再將三個線索點接到場景觀察，把回村桌與爐接到服務端背包及煉製規則。新增碰撞前先確認不阻擋廣場到坊市的路線。
