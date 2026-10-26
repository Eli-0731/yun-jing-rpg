# 2026-10-26 分支與 PR 整合檢查

檢查基準：`main` 的 `faf2094`。已列出當時所有遠端分支，對每個分支自分叉點以來修改的檔案逐一比對與 `main` 的 blob；「同檔」表示位元內容相同，不代表原 PR 已正式合併。此次沒有以覆寫新版主線的方式強制合併舊分支。

| 分支／PR | 自分叉點的變更檔 | 與 main 同檔 | 尚有差異 | 結論 |
|---|---:|---:|---:|---|
| `feature/qingxi-hunt-graybox`／[#13](https://github.com/z1nnz/yun-jing-rpg/pull/13) | 162 | 162 | 0 | 已經由 #17 帶入；留言後關閉重複 PR。 |
| `feature/qingxi-hunt-graybox-johnny`／[#14](https://github.com/z1nnz/yun-jing-rpg/pull/14) | 10 | 5 | 5 | 保持草稿；舊 Builder 會覆蓋目前較完整配置，manifest 亦有差異。已留言修正要求。 |
| `chore/unity-6000.0.85f1`／[#15](https://github.com/z1nnz/yun-jing-rpg/pull/15) | 51 | 45 | 6 | 保持開啟；Unity／FishNet 固定版本與現行主線不同，工具腳本也會移除 WorldPreview。已留言要求基於新版主線重整。 |
| `assets/joshsu54-qingxi-town-concept`／[#16](https://github.com/z1nnz/yun-jing-rpg/pull/16) | 29 | 29 | 0 | 已經由 #17 帶入；留言後關閉重複 PR。 |
| `assets/dondon-import` | 0 | 0 | 0 | 原工作已在主線。 |
| `chore/collaboration-workflow` | 4 | 2 | 2 | 其餘是過時的 README／CONTRIBUTING 內容，不回退主線文件。 |
| `feature/qingxi-rabbit-hunt` | 0 | 0 | 0 | 原工作已在主線。 |
| `feature/qingxi-reuse-world-v2` | 139 | 137 | 2 | 只剩 `.gitignore` 與進度文件的舊版本差異；保留主線。 |
| `feature/qingxi-world-foundation-v1` | 28 | 25 | 3 | Builder、忽略規則、進度文件已有後續版本；不覆寫。 |
| `integration/20261026` | 528 | 528 | 0 | 已經由 #17 帶入。 |
| `very-string-donon` | 0 | 0 | 0 | 素材交接已在主線。 |
| `very-strong` | 342 | 334 | 8 | 主要是舊版 Unity 設定、工具與狀態文件；第一人稱程式與現行主線不同，不整批覆寫。 |
| `docs/daily-14h-20261026` | 1 | 1 | 0 | 已經由 #18 帶入。 |

PR #13–#16 的當時 `API and persistence` 工作流程均回報成功；這些檢查不等於目前主線的 Unity 編譯、FishNet 雙端連線或手機效能通過。#14 為草稿且尚有整合衝突；#15 的剩餘差異需在最新版 `main` 上重新驗證。下一次每日檢查須先重新抓取分支和 PR，再判斷是否有新提交，不沿用本表當作新變更的測試結果。

## 同日續查：道路與小物件 v12 整合前

再次 `git fetch origin --prune` 後，`main` 為 `f977ab7`，遠端仍只有開啟的 [#14](https://github.com/z1nnz/yun-jing-rpg/pull/14)（`e05672c`，草稿）與 [#15](https://github.com/z1nnz/yun-jing-rpg/pull/15)（`fe71619`）。兩支 head 與前次審查相同，沒有協作者的新提交可供這輪合併。#14 舊版青溪 Builder、#15 的 Unity／FishNet 固定版本仍與主線衝突；修正要求已留在各 PR，保持開啟等待作者更新。本輪核心組新增的道路與小物件位於自己的新檔案與新分支，未覆寫三位協作者的交付路徑。

## 同日村口 v13 續查

`main` 為 `5d249bc` 時再次查 `origin` 遠端分支：#14 `e05672c`、#15 `fe71619` 頭提交未變，沒有新上傳的 A／B／C 交付分支。兩個待審 PR 的舊衝突仍待各作者依先前留言重整，故本輪沒有代他們覆寫或強制合併。核心組的 v13 全部在 `feature/qingxi-entry-style-v13` 新路徑：角色、牌樓、竹籃、審圖組裝及文件，未改協作者現有 Builder、Unity 版本、`tools/world-preview/` 或山兔原稿。待 v13 相關 QA／瀏覽器連結及主線 CI 檢查完成後，只合併核心組自己的 PR；作者歸屬依 [工作登記](../work-ownership.md)保留。

### 新到 PR #21 已驗收合併

續查發現 Johnnnny0823 上傳 `feature/qingxi-rabbit-v003`（`440e3c7`）。37 個檔案均在獨立山兔目錄，`merge-tree` 與主線無衝突。核心組在 `D:/yun-jing-rpg-rabbit-review` 重跑 `validate_rabbit.py`：五段動畫、120 幀地面／權重、九個 FBX／GLB 回匯通過；目視跳躍圖，API 與 LFS CI 均成功。已在 PR 留驗證留言，由 z1nnz 帳號以 merge commit 合併，主線合併 SHA `842e6d6785650d3cf7989ce16ebe5fc4ffcb80ba`，保留原提交作者。這是素材候選版整合，不代表 Unity 或遊戲內戰鬥已驗收。#14／#15 的舊版本衝突仍未改變。
