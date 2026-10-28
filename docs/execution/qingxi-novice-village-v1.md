# 青溪新手村 v1｜A／B／C 協作者成果接入

更新：2026-10-28。z1nnz 決定方向：先不把協作者作品塞進大世界（地形起伏、樹與既有建物會擋住模型、難以驗收），改做一個**平坦的小型新手村**，讓 10/29 工作包的完整作品能被看清楚、走得到、玩得到。整合由 z1nnz 指導、Claude Code 實作；模型與玩法的原作者如下表，未改動任何原件。

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
