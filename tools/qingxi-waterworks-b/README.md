# 青溪古水路修復與導水選擇（B 組）

本機演示，結果不是正式結果。完工扣的是「本機展示材料」，不入正式背包，也不產生正式貢獻。正式接線見 [CONTRACT.md](CONTRACT.md)。

## 怎麼開

需要 Node 22 以上。網頁從 jsdelivr 載入 three.js 0.170.0。

```bash
node tools/qingxi-waterworks-b/serve.mjs
```

打開 http://127.0.0.1:8765/tools/qingxi-waterworks-b/

- 網址加 `?obs=partial` 是「只找到破槽」，加 `?obs=none` 是「沒有線索」，預設 `full`。右側面板的「線索組」也能切換。
- 規則測試：

```bash
node --test tools/qingxi-waterworks-b/tests/waterworks-core.test.mjs
```

## 玩法

玩家看到的是從 B01 取水基座往北到村田的一段舊水路：

- 白框是可放段件的槽位，入口箭頭表示水從哪邊進來。
- P1、P4 是原有的舊槽，不能拆。P1 淤了一半；P4 西牆有裂縫，可以補石。
- 右側面板列出每一段放什麼、水流到哪、哪裡斷開與修法。

步驟：

1. **放段件**：選槽位，再從面板選段件（直槽、彎槽左右、三通、閘板、放流坡）。標「✓接得上」的段件，出水口對得上下一個槽位。
2. **錯接會說明**：例如「P2 的 B04 分流三通 out_left 接口落在 (-0.5, 1.75)，最近的槽位 L1 差 25 cm；把 P2 換成 B04-V02」。斷開的接口畫面上有紅圈，水會從那裡漫出。撤回／重做隨時可用。
3. **開閘**：選到閘板按 G。閘門關著時，下游沒有水。
4. **選處理方向**：
   - 先清淤 `clear_silt`
   - 修回舊渠 `restore_channel`
   - 保護育幼區 `protect_nursery`

   方向對版面有條件；不符合時，面板會說缺什麼。
5. **完工**：彈出結果卡，內容有：
   - `outcomeId`、村田進水、育幼區影響、淤積／破槽
   - 收據：請求編號、扣料、本機貢獻
   - 三個方向的取捨表

   再按一次完工，是重送同一個請求，不會再扣料。

| 方向 | 參考擺法 | 村田今天 | 育幼區 | 花費 |
|---|---|---|---|---|
| 修回舊渠 | P2 B05 → P3 B02 → P4 舊槽＋B07 → P5／P6 B02 | 56%（清淤後 94%） | 有風險，流水距 50 cm | 石 6、木 2、銅 1、灰漿 1 |
| 保護育幼區 | P2 B03-V04 → L1 B02 → L2 B03 → L3 B02-V03 → L4 B05 → L5 B03-V02 → L6 B02 → L7 B03-V03 | 54%（清淤後 89%） | 安全，距 90 cm | 石 20、木 4、銅 1 |
| 先清淤 | P2 B04-V02 → 西 L1 B02 → L2 B02-V05 進回流溝；東 R1 B05 關閘 | 0%（淤泥排走，之後開閘接近全量） | 安全 | 石 8、木 2、銅 1 |

**村田是 F01 灌溉田地**，入水口對準最後一段的出水口。疊板預設卡滿，所以出水口不放水。田溝水位隨進水量從溝底漲向疊板頂。

**線索不足時仍可完工。** 面板會用黃色「未知風險」列出沒調查到的事，例如淤積程度、P4 有沒有裂縫、渠邊有沒有孩子走動。完工後結果卡列出「完工後發現」，真實水量也會反映在結果裡。

### 操作

| 動作 | 鍵盤 | 滑鼠 | 觸控（橫向） |
|---|---|---|---|
| 選槽位 | 方向鍵、Tab | 點槽位 | 點槽位 |
| 放段件／補石 | 1–9、0、- | 點面板按鈕 | 點面板按鈕 |
| 拆掉 | Del／Backspace | 右鍵點槽位、面板「拆掉」 | 面板「拆掉」 |
| 開關閘 | G | 面板按鈕 | 面板按鈕 |
| 撤回／重做 | Ctrl+Z／Ctrl+Y（Ctrl+Shift+Z） | 面板按鈕 | 面板按鈕 |
| 處理方向 | Q 清淤、W 修舊渠、E 護育幼 | 面板按鈕 | 面板按鈕 |
| 完工 | Enter | 面板按鈕 | 面板按鈕 |
| 視角 | — | 拖曳旋轉、滾輪縮放、右鍵拖曳平移 | 單指旋轉、雙指縮放平移 |

面板按鈕至少 36 px 高（812×375 橫向實測）。寬度 1000 px 以下或高度 520 px 以下時，側欄縮成 300 px。

## 檔案

| 路徑 | 內容 |
|---|---|
| `src/waterworks-core.mjs` | 規則：槽位擺放、接口與重疊判定、水流與分流、閘門、方向條件、`outcomeId`、撤回／重做、可重送的本機完工。不碰 DOM，不用亂數或時鐘 |
| `tests/waterworks-core.test.mjs` | 17 項規則測試，涵蓋三條方案、錯接訊息、閘門、撤回重做、重送不重複扣料、缺線索 |
| `main.js` | three.js 畫面與輸入，只讀 `evaluate()`／`preview()` |
| `walkthrough.js` | `?walk` 錄影腳本：點按鈕、送按鍵、投影槽位位置，逐格送到 `serve.mjs` |
| `data/board.json` | 工程 `qingxi-old-channel-01`：槽位、村田進水口、育幼區／回流溝範圍、隱藏事實、段件與材料庫存、參考擺法 |
| `data/catalog.json` | 由 `scripts/build-catalog.mjs` 從 `art/exports/qingxi-waterworks-b/*/model_info.json` 產生：接口、0.25 m 佔格、作者、狀態、GLB 路徑 |
| `data/fixture-observations.json` | 本機 fixture，模擬 A 組的 `observationIds`：`cracked_sluice`、`silt_buildup`、`nursery_tracks` |
| `CONTRACT.md` | 服務端接線說明（提案）：工程 ID、角色與貢獻、材料批次、唯一 requestId、結果收據、重送規則 |
| `unity/`、`drive_demo_keys.ps1` | 先前的 Unity 溪流取水試做（水面著色器、F01 疊板、閘門水網），與網頁示範分開 |

### 接口規格（B02–B05 共用）

- 外寬 60 cm、淨寬 40 cm、總高 40 cm、槽底厚 10 cm，運作水面 z = 28 cm。
- 拼接格 25 cm；接口中心在槽底中線。`in` 接口在段件原點、朝 −Y，水流往 +Y。
- 各段長度：
  - 直槽 B02 長 100 cm；短接頭 B02-V04 長 50 cm；放流坡 B02-V05 長 80 cm（出口為 `discharge`）。
- 彎槽出口：

  | 件號 | 方向 | 出口位置 (x, y) |
  |---|---|---|
  | B03 | 右 | (75, 75) cm |
  | B03-V02 | 右 | (100, 100) cm |
  | B03-V03 | 左 | (−50, 50) cm |
  | B03-V04 | 左 | (−75, 75) cm |

- 三通出口：B04 在 (±50, 75) cm，B04-V02 在 (±75, 75) cm。
- B05 閘板：長 100 cm；開閘時閘板上升 32 cm。B06 閘輪掛在 B05 的 `SOCKET_wheel_mount`，位置 (39.2, 50, 90) cm。

接口與佔格都直接取自 `model_info.json`，網頁用同一份資料擺放 GLB。規則判定「接得上」時，要求接口位置在 1 cm 內，而且方向相反。

## 玩家鏡頭圖與錄影（`art/previews/qingxi-waterworks-b/demo/`）

畫面上每段都標「槽位·變體 ID」，例如 `P2·B03-V04`、`P4·B02-V02舊`。

| 檔案 | 內容 |
|---|---|
| `player_01_route_a_direct.jpg` | A 直通村田全景（B05、B02、B02-V02 舊槽、B07） |
| `player_02_route_a_patch_closeup.jpg` | P3 B02 接 P4 舊槽，西牆 B07 補石近看 |
| `player_03_route_b_bypass.jpg` | B 繞過育幼區全景（B03-V04、B03、B02-V03、B05、B03-V02、B03-V03） |
| `player_04_route_b_bends_closeup.jpg` | P2 B03-V04 左彎、L1 B02、L2 B03 右彎近看 |
| `player_05_route_b_field_inlet_closeup.jpg` | L5 B03-V02、L6 B02、L7 B03-V03 接 F01 入水口近看 |
| `player_06_route_c_desilt.jpg` | C 先清淤：B04-V02 分流、B02-V05 放流進回流溝、R1 B05 關閘 |
| `player_07_route_c_tee_closeup.jpg` | B04-V02 圓缽三通兩側接口近看 |
| `player_08_wrong_tee.jpg` | 錯接：P2 放窄三通 B04，兩個出口各差 25 cm，水漫出 |
| `player_09_start.jpg` | 起始狀態 |
| `walkthrough_player_view.mp4` | 62 秒操作錄影，五段如下 |
| `walkthrough_no_clues.mp4` | 沒有線索的情況：未知風險提示，完工後才揭露 |

`walkthrough_player_view.mp4` 的五段：

1. 錯接三通，撤回。
2. 直通路線，途中修正一個錯彎。
3. 選「保護育幼區」被拒；改選「修回舊渠」完工，再按一次完工只回原收據。
4. 繞行路線完工。
5. 先清淤；清淤後再走直通路線，進水升到 94%。

錄影與鏡頭圖用 `?walk`、`?walk=none&obs=none`、`?walk=shots` 產生。程式固定時間步進，畫面逐格合成側欄，再由 `scripts/encode_walkthrough.py` 編成 MP4。

## 既有灌溉模型：只作背景

| 既有素材 | 用途 |
|---|---|
| `art/exports/irrigation-v2/water-channel.glb`（含 LOD1） | 只作背景；不算本包段件，網頁示範沒有載入 |
| `art/exports/irrigation-v2/cistern.glb`（含 LOD1） | 只作背景；不算本包段件，網頁示範沒有載入 |
| `art/exports/irrigation-v2/spirit-bed.glb`（含 LOD1） | 只作背景，屬私人靈田床，與 B01 公共工程基座不同；網頁示範沒有載入 |

本包的 B02–B05 是另行建模的段件，沒有複製 `irrigation-v2/water-channel` 充數。

## 12 件新件：作者與狀態

作者全部是 **蘇奕安 Josh（joshsu54@gmail.com），Claude Code 協作建模**。三視圖在 `art/references/qingxi-waterworks-b/`，匯出在 `art/exports/qingxi-waterworks-b/<ID>/`。

| ID | 物件 | 變體 | 狀態 | 網頁示範中的用途 |
|---|---|---|---|---|
| B01 | 舊水路方形基座 | — | 建模完成（程序化母稿），待人工精修審核 | 水源，固定 |
| B02 | 完整短直槽 | B02-V02、B02-V03、B02-V04、B02-V05 | 同上 | 可放；V02、V03 也當舊槽 P4、P1 |
| B03 | 直角彎槽（右） | B03-V02、B03-V03、B03-V04 | 同上 | 可放（左右彎） |
| B04 | 分流三通 | B04-V02 | 同上 | 可放；窄口 B04 用來示範錯接 |
| B05 | 木製手動閘板 | — | 同上 | 可放，開／關兩態 |
| B06 | 青銅水位閘輪 | — | 同上 | 自動掛在每座 B05 上，開關閘時轉動 |
| B07 | 修補石鞍 | B07-V02、B07-V03 | 同上 | P4 補石；只有 B07 合槽壁裂口 |
| B08 | 河床清淤篩 | — | 同上 | 未在網頁擺放；清淤以「先清淤」方向表達 |
| B09 | 流速指示浮標 | — | 同上 | 網頁用簡化浮子沿流水移動表示流速，未載入 B09 模型 |
| B10 | 石槽支架（排架） | B10-V02、B10-V03 | 同上 | 未在網頁擺放（本關卡段件都在地面） |
| B11 | 兩輪手推車 | — | 同上 | 擺在起點旁，當材料車 |
| B12 | 完工紀錄碑座 | — | 同上 | 擺在村田旁；完成某方向後，該方向的木栓出現 |

另有 F01 灌溉田地（村田）、S01 溪流、S02 河床，是場景用件，不在 12 件之內。

## Unity 實機版（`unity/`，2026-10-29 實測）

同一套玩法也做成 Unity 6000.0.85f1（Built-in）場景 `Assets/QingxiWaterworksB/Scenes/WaterworksPuzzle.unity`，在 Windows 播放器實際操作過。

- **規則**：`Runtime/WaterworksRules.cs` 是 `src/waterworks-core.mjs` 的 C# 版。`scripts/export-scenarios.mjs` 把 JS 的 18 個情境結果寫成 `data/scenarios.json`，`Editor/WaterworksRulesParity.Run` 在 Unity 裡照同樣步驟重跑並逐項比對：水流、指標、接口問題與修法文字、方向條件、花費、請求編號、完工與重送。結果 18/18 情境、809 項一致，見 `reports/unity_rules_parity.json`。改規則時兩邊要一起改，再重跑兩支腳本。
- **場景**：`Editor/WaterworksPuzzleBuild.Build` 產生場景，加 `-qxBuild <exe>` 會輸出播放器。模型用專案內 FBX＋水面。B05 帶 B06 閘輪；F01 疊板卡滿，田面水位隨進水上升。右側用 IMGUI 面板（manifest 加了內建模組 `com.unity.modules.imgui`）。
- **操作**：與網頁版相同的鍵位，另加 C 切換選取槽位的特寫。滑鼠可以點槽位、右鍵拆、拖曳轉視角、滾輪縮放、點面板按鈕。觸控支援點選、單指拖曳、雙指縮放。
- **實測錄影**：`art/previews/qingxi-waterworks-b/demo/unity_playtest_keyboard_mouse_touch.mp4`，3 分 48 秒，1280×720、10 fps，由播放器自己擷取畫面。`unity/drive_puzzle.ps1` 送出作業系統層級的真實按鍵、滑鼠點擊／拖曳／滾輪與 Windows 觸控注入，點擊位置讀播放器輸出的 `ui_map.json`。紀錄在 `reports/unity_playtest/`：`driver.log` 是送出的每個動作，`events.jsonl` 是播放器收到並執行的每個動作，`frames.jsonl` 是每格狀態，`run_summary.json` 是總結。
  - 錯接：B03 接成死路、三通兩側沒接、P3 彎槽出口對不上、P4 補石形狀不對。每種都顯示斷開的接口與修法，修正後問題消失。
  - 修回舊渠 56%，重送回傳同一張收據，材料不再扣。保護育幼區時直通被拒（50 cm），改走西側繞道 54%。先清淤時回流溝 98%、村田 0%。清淤後重排直通 94%。
  - 右鍵拆 P5 後水從 P4 漫出，撤回、重做都有效。換成沒有線索時，預覽標示（預估）94%，完工實際 37%，並列出三條「完工後發現」。
  - 觸控：注入的點選選中了 L3，單指拖曳轉了視角（`touchTaps 1`、`touchDrags 1`）。這是 Windows 觸控注入，不是實體觸控螢幕或手機；雙指縮放沒有測。
  - 錄影期間每格平均 8.4 ms（RTX 5060，含每 0.1 秒存一張 JPG）。
- 錄完後只把「⚠」改成「！」（原字型沒有這個字），重新編譯通過，沒有重錄。

## 已知限制

- 只在桌機 Chrome 系瀏覽器檢查過：1280×720、800×600，以及模擬的 812×375 橫向（版面不橫捲、側欄 300 px）。觸控只依 pointer 事件實作，沒有在實體手機上測過。
- 水流是規則層的流量比例，不是流體模擬。田溝水位依進水比例升降，不隨時間累積。
- 疊板在網頁裡固定卡滿；升降疊板的操作在 Unity 試做專案（`unity/`）。
- 模型碰撞、UV 展開仍是待辦，見 `art/source/qingxi-waterworks-b/qa_report.json`。
