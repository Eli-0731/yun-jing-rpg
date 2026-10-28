# 青溪新手村 v1｜A／B／C 協作者成果接入

更新：2026-10-29。z1nnz 決定方向：先不把協作者作品塞進大世界（地形起伏、樹與既有建物會擋住模型、難以驗收），改做一個**平坦的小型新手村**，讓舊 10/29 工作包（`docs/execution/2026-10-29/01`–`03`）的完整作品能被看清楚、走得到、玩得到。整合由 z1nnz 指導、Claude Code 實作；模型與玩法的原作者如下表，未改動任何原件。

| 欄位 | 內容 |
|---|---|
| 玩家目標 | 在一個小村子裡走一圈，體驗林地山兔遭遇、進丹房、回村分揀三段協作者玩法 |
| 輸入 | A：PR #39 林地 A01–A12、山兔 v003、`tools/qingxi-encounter-a/`；B：PR #40 `AlchemyRoom` 與丹房角 B01–B12；C：回村 C01–C08、告示牌 Q01–Q04、`tools/qingxi-return-c/`；Unity `6000.0.82f1` |
| 輸出 | 新場景 `QingxiNoviceVillage.unity` 與生成器、A／C 規則的 C# 移植、丹房往返、HUD 面板、建置版 smoke、7 張審圖 |
| 邊界 | 不改大世界 `QingxiUnifiedWorldBuilder.cs`、協作者母稿與模型、`AlchemyRoom` 內的煉製與 API；不寫正式背包或靈石 |
| 完成條件 | 固定 Editor 生成與 Windows 建置成功、規則對照通過、建置版 smoke 走完三段；真人與手機試玩列為未驗 |

**玩家過程：** 從南邊村口進來，廣場告示牌指向三個方向。往北走進林地，山兔會警戒、預備再衝刺；玩家閃避或格擋後找空檔攻擊，失手可按 R 回安全點重來。往西進丹房煉製，結束後回到門口。回到廣場分揀桌，把帶回的樣本分成保存、留待煉製或交委託；選錯可以取消最近一次。

**本次沒有自行製作新模型**，所以不適用「先做 AI 三視圖」的要求。所有可見模型都來自協作者的已交付成果，或是標 `Placeholder` 的灰盒。C／Q 的 GLB 只做格式轉換（FBX＋外置貼圖），網格沒有改動。

## 村子配置

| 方位 | 內容 | 原作者 |
|---|---|---|
| 南 | 村口（出生點） | 核心組灰盒 |
| 中央 | 小廣場、告示牌 Q01、回村分揀角 C01–C08 | Eli-0731／Codex |
| 西 | 溪畔丹房角 B01–B12，門口按 F 進入 B 的 `AlchemyRoom` 場景 | joshsu54 |
| 東 | 演武區：演武棚、氣擊樁、身法樁、刻紋石、兵器架、旗幟 | Johnnnny0823 |
| 北 | 林地山兔遭遇 A01–A12，避雨龕面向村子 | Johnnnny0823 |
| 四周 | 線索牌 Q02–Q04、外圍松竹（CollaboratorWorldV1） | Eli-0731／既有交接素材 |

地面、道路、廣場、三株靈草與丹房工作桌是**灰盒佔位**，物件名稱都標 `Placeholder`。

![村口](../../art/previews/qingxi-novice-village-v1/01-gate-view.png)

其他審圖：[俯視](../../art/previews/qingxi-novice-village-v1/00-overview.png)、[分揀角](../../art/previews/qingxi-novice-village-v1/02-plaza-return-C.png)、[丹房角](../../art/previews/qingxi-novice-village-v1/03-alchemy-B.png)、[演武區](../../art/previews/qingxi-novice-village-v1/04-training-yard.png)、[林地](../../art/previews/qingxi-novice-village-v1/05-forest-A.png)、[林地近景](../../art/previews/qingxi-novice-village-v1/06-forest-A-close.png)。

## 可以玩什麼

- **A 林地遭遇**：`tools/qingxi-encounter-a/encounter.mjs` 移植為 `QingxiForestEncounterRules.cs`。山兔有警戒、預備、衝刺、硬直、撤退，HUD 顯示狀態與倒數。操作：J／左鍵攻擊、Q 試招、按住 K／右鍵格擋、C 閃避、R 回安全點、在觀察台梯子旁按 F 上下。藤靶累計 8 點換破損外皮。山兔使用 v003 模型與動畫。
- **B 丹房**：走到丹房角門口按 F，載入 joshsu54 原本的 `AlchemyRoom` 場景（服務端權威，需先啟動本機 API `tools/start-local.ps1`）。左上角按鈕或 Backspace 回到村裡的丹房門口；採到的本機靈草與分揀結果會帶回來。
- **C 回村分揀**：分揀桌按 F 打開面板，三份樣本可自由選「保存／留待煉製／交委託（展示）」，可取消最近一次。規則移植自 `tools/qingxi-return-c/state.js`。
- 既有本機採草、線索觀察與演武區練氣也可在村內使用。旅途手札（M）可傳送到三區。

所有結果都是**本機演練**，不寫入正式背包、靈石、掉落或委託；正式結算仍走各自 CONTRACT／handoff 文件描述的服務端流程。

## 四種狀態

| 內容 | 已進 Git | 在場景可見 | 玩家能互動 | 服務端保存 |
|---|---|---|---|---|
| A 林地 A01–A12、山兔 v003、演武區 | 協作者原檔已在 main；本分支只加擺位資料，模型由生成器複製到 gitignore 目錄 | 是 | 是（遭遇、梯子、藤靶） | 否，僅本機演練 |
| B 丹房角 B01–B12、`AlchemyRoom` | 原檔已在 main | 是 | 進出場景可以；煉製本身需本機 API | 煉製由 B 的服務端判定；本次未實跑一爐 |
| C 回村 C01–C08、Q01–Q04 | 是（本分支新增轉出的 FBX 與貼圖，LFS） | 是 | 是（分揀與取消） | 否，僅本機演練 |
| 地面、道路、三株靈草、工作桌 | 是（生成器內的灰盒） | 是 | 靈草可採 | 否 |
| Windows 建置版 | 否（`artifacts/` 不進 Git） | — | — | — |

## 建置與驗證

```powershell
node tools/qingxi-main-scene/build-data.mjs          # 由 A 原版規則錄製對照劇本並輸出擺位資料
blender -b --factory-startup --python-exit-code 1 -P tools/art/import_qingxi_return_c_to_unity.py   # C／Q 的 GLB 轉 FBX
./tools/unity.ps1 -Target NoviceVillageWindows       # 生成新手村、連接丹房並建置 Windows 版
artifacts/windows-novice-village/YunJingNoviceVillage.exe -batchmode -nographics --abc-smoke
```

本次實測（Unity `6000.0.82f1`）：

- A 規則對照：C# 移植版重播 JS 原版錄下的三組輸入，事件逐項一致（13／19／37 個事件）。
- C 分揀規則測試通過；32 件 A／B 模型匯入高度與 `model_info` 相符；C／Q 共 12 件 GLB→FBX 回匯網格數與尺寸一致。
- Windows 建置成功；建置版 `--abc-smoke` 14 項全部通過：分揀桌開啟並保留選擇、靠近兔洞觸發警戒與預備、回安全點、上下觀察台、採草、進出丹房並回到門口、本機計數與分揀結果保留。
- `npm test` 64／64、`tools/qingxi-encounter-a` 測試 18／18。
- 有圖形裝置的 Editor 審圖已逐張檢視（`QingxiCollaboratorZonesCapture.CaptureVillage`）。

## 尚未完成

- 未做真人鍵鼠完整試玩、手機觸控與效能；`--abc-smoke` 是程式腳本，不等於手感驗收。
- 丹房內煉製需要本機 API，smoke 只驗證場景載入與往返，沒有跑完一爐。
- 新手村使用 URP（與丹房同一管線）；大世界 `QingxiUnifiedWorld` 本次**未改動**，仍待日後整合。
- 地面、道路、靈草、工作桌為灰盒；A 的地形磚 LOD、碰撞仍沿用模型網格，未做專用碰撞。
- 遭遇規則只在客戶端演練；正式命中與掉落仍需區域程序依 `tools/qingxi-encounter-a/CONTRACT.md` 重播驗證。
- **沒有觸控操作。** 村內角色用 `QingxiFirstPerson`，只讀鍵鼠；遭遇的攻擊、試招、格擋、閃避和 F 互動也沒有螢幕按鈕。要做橫向觸控，需要給村內加一層虛擬搖桿和動作鈕。
- PWA 入口（`tools/qingxi-trial/`）沒有加入新手村；目前只有 Unity 版。

## 依賴、衝突與回退

- 本分支建在含 PR #46 的 main 上，只新增新手村檔案。既有檔案只小幅改了 `QingxiHud.cs`（改為 partial 並加面板）、`QingxiLocalForaging.cs`（加站點掛鉤）、`tools/unity.ps1`（新增兩個 target）、`.gitignore`（兩個複製模型目錄），並在 `docs/status.md`、`docs/work-ownership.md` 加註；大世界沒有改動。按手冊，`status`／`work-ownership` 原應在 PR 合併後才由核心組更新，開 PR 前可以考慮把這兩處拿掉。
- 回退：直接 revert 這個提交即可。被複製進 gitignore 的模型資料夾可以直接刪除，生成器下次會重新複製。
- 新的斷流工作包（`10`–`13`）交付後，同一個生成器可以在村內加北邊上游、水工場和村民回應三個位置。這次沒有做，要等三人的 PR 合併後再接。
