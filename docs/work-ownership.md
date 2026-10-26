# 青溪工作與來源登記

更新：2026-10-26。此表用來避免重做；「z1nnz／Codex 協作」表示由 z1nnz 指導、Codex 在其專案中製作或整合，不把協作者原創誤記為 z1nnz 獨作。

| 內容 | 原始製作／來源 | 本輪整合與狀態 | 下一位可做的事 |
|---|---|---|---|
| 樹伴成樹 | z1nnz 的 `elder-tree-esg`，母稿保存在 [原檔副本](../art/source/elder-world-tree-garden-original.blend) | z1nnz 原作／Codex 移植：v11 將完整原樹 96 個物件、16 組葉冠放入青溪，保留原方向與樹形，取消 v10 補葉；[實際畫面](../art/previews/qingxi-world-v11/original-tree-in-world.png) | 葉色與樹伴 Unity 渲染仍未完全一致；需做材質、LOD、碰撞及引擎驗證，不要重新生成或複製葉冠。 |
| 青溪河岸與流動水樣片 | z1nnz／Codex 協作；既有 v8 | Blender 動畫及畫面已保存，水位／泡沫為樣片 | 實際遊戲水材質、遮擋和手機效能。 |
| 12 m 不規則土路近景 v12 | z1nnz 指導／Codex 實作；沿用既有道路三視圖及河岸貼圖 | [Blender 原稿與 GLB](qingxi-road-props-v12.md)、斜視與俯視圖、QA 0 錯誤；道路仍偏程式化 | 協作者 B 獨立完成可互換三段道路與橋頭河岸銜接，勿覆寫此原稿。 |
| 橋邊木欄、採藥晾架、苔石路標 | z1nnz 指導／Codex 實作；[新增 AI 三視圖](../art/references/qingxi-road-props-v12.md)先於模型保存 | 三件可獨立擺放的 Blender／GLB 初版；QA 0 錯誤 | 精修材質、烘焙、LOD 與擺位；不要重做同名初版。 |
| 河岸蘆葦、蕨草花叢、苔石、木路燈 v2 | z1nnz／Codex 協作；先有 [AI 三視圖](../art/references/qingxi-detail-props-v2/three-view.png) | 有獨立 Blender 原稿、GLB 和近景預覽；質感仍是初版 | 精修紋理、近景細節及 LOD；不要做重名初版。 |
| 客舍及鎮區模型 | z1nnz／Codex 的客舍 v1；joshsu54／Dondon 的模型依來源分別登記 | 已放入青溪組裝及協作者鎮區分支，兩者不能互稱原創 | 選用時保留來源，修改不要覆寫交接原件。 |
| 青溪鎮與採獵區 Unity 場景 | joshsu54 分支 `very-strong`、Johnny 分支 `feature/qingxi-hunt-graybox-johnny` | 已在整合分支合併，保留兩個獨立 builder；Unity 整合版尚未編譯 | 待可用 Editor 再驗證，避免同時改同一生成場景。 |
| 山兔掉落與售出 API | z1nnz／Codex 協作 | 服務端原型及冪等測試完成 | 協作者 A 做模型／動畫；區域程序仍需實際命中、距離及死亡事件接線。 |
| 青溪視覺檢視 PWA | z1nnz／Codex 協作 | 圖片和現有玩法測試頁可在瀏覽器查看；不等於 3D 客戶端 | 協作者 C 做獨立行走鏡頭樣片，不改登入 API。 |

## 青溪村口 v13 新增工作

| 內容 | 原始製作／來源 | 實際狀態 | 專責後續 |
|---|---|---|---|
| 原創初始角色 AI 三視圖與低面數雛形 | z1nnz 指導／Codex 製作；本次仙俠短劇影像僅作風格參考 | [三視圖](../art/references/qingxi-novice-cultivator-v1/three-view.png)先於[模型](../art/previews/qingxi-entry-assets-v13/novice-front.png)保存；無骨架／動畫／操作；含曲線網格 QA 0 錯誤，造型仍為低精度原型 | A 在自己分支重做形變模型與兩段動畫，保留來源，不覆寫 v13 雛形 |
| 村口牌樓、採藥竹籃、碎石花草散佈 | z1nnz 指導／Codex 製作；各新模型先有 AI 三視圖 | 獨立 Blender／GLB 與預覽；QA 0 錯誤但仍有警告，不能稱為量產資產 | B 另做道路岸線模組；核心組處理剩餘 UV／隱藏面等警告 |
| 12 m 青溪村口組裝 | z1nnz 指導／Codex 組裝，沿用樹伴原樹及既有客舍／道路 | [審圖](../tools/entry-review-v13/index.html)；靜態 Blender 預覽，未達完整區域或可玩狀態 | C 做獨立 PWA 試走；核心組保留主組裝母稿 |

最新 [三位協作者各 14 小時任務](execution/2026-10-26/08-entry-v13-three-collaborators-14h.md)優先；[07 舊工作包](execution/2026-10-26/07-daily-14h-work-package.md)保留歷史，山兔五段動畫與 LOD 已由 PR #21 合併，不重派。核心組保留樹伴成樹、主場景整合、服務端資產帳本與驗收。新交付先看此表與遠端分支，再開始製作。

山兔 v003 來源與作者：原外觀 Dondon v002；Johnnnny0823／其 Codex 完成骨架、動畫、LOD；z1nnz／Codex 只負責重跑驗證及合併。保留原提交 `440e3c7`，合併為 `842e6d6`。
