# 青溪上游調查（10/29 工作包 A，第一批）

斷流事件的第一段：玩家從下游入口沿溪往上游走，靠近觀察跡象，判斷水為什麼變少。這是調查，不是打怪；不發靈石、貢獻或材料。

```powershell
cd tools/qingxi-waterhead-a
npm ci
npm test          # 規則測試
npm start         # http://127.0.0.1:4182 （只綁 loopback）
```

## 操作

| 動作 | 鍵盤滑鼠 | 觸控（橫向） |
|---|---|---|
| 移動 | WASD／方向鍵 | 左下搖桿 |
| 轉視角 | 拖曳畫面 | 拖曳畫面 |
| 觀察 | E 或點擊 | 「觀察」 |
| 回下游入口 | R | 「回入口」 |

站著不動時替身面向鏡頭方向；靠近跡象並看著它，畫面中央的圈填滿後按觀察，才記入線索簿。路過不算、重複觀察不會多記，線索可以任意順序取得，也可以略過。

## 第一批內容

- 河段由 A01 五種形體串成約 29.5 m，接口數據取自 `art/exports/qingxi-waterhead-a/A01_*_model_info.json`，同一形體不相鄰：
  - 走法 A（預設）：直段 → 左彎 → 收窄 → 右彎 → 源頭收尾件
  - 走法 B（`?route=b`）：直段 → 右彎 → 收窄 → 左彎 → 源頭收尾件
  線索依模組種類擺放，兩種走法都能完成同一條調查。
- **破槽 `cracked_sluice`**：右岸兩段古石槽（A02 兩種破口），看任一處都算同一條線索。
- **泥沙 `silt_buildup`**：左彎河道中的 A04 泥沙矮壩，從岸上就能看。
- 環境提示：A06 示跡石（兩道水位線），只回應文字，不算答案。
- 任兩條線索 →「可回去討論導水方案」，並顯示交接 JSON；三條為完整判斷（育幼足跡第二批開放）。
- 回入口（R）保留線索簿；「重新調查」清空。走不上去的陡坡（右彎外側岩壁）與石槽、陣基、峽口大岩會擋住，河段外不能走。

## 交接給 B／C

`observations.example.json` 是本機 fixture，格式同 `Investigation.toJSON()`：

```json
{ "schema": "qingxi-waterhead-a/observations@1", "observationIds": ["cracked_sluice", "silt_buildup"], "order": ["cracked_sluice", "silt_buildup"], "verdict": "discuss" }
```

`observationIds` 依固定順序（`cracked_sluice`、`silt_buildup`、`nursery_tracks`）列出看過的跡象；`order` 是實際發現順序；`verdict` 為 `null`／`discuss`／`full`。資料狀態在 `investigation.mjs`（不含渲染），畫面在 `app.mjs`。

## 檔案

| 檔案 | 內容 |
|---|---|
| `investigation.mjs` | 規則：線索簿、觀察距離與視角、停留時間、去重、回入口、區域事件、交接 JSON |
| `investigation.test.mjs` | 任意順序、重複不重記、要走近並看著、可略過、提示不算答案、牆與可走範圍、育幼區只警告、交接格式 |
| `app.mjs` | three.js 0.170 場景、河段組裝、第三人稱鏡頭與碰撞、觸控 |
| `capture.mjs` | 真 Chromium 以真按鍵走完一輪並截圖，含兩種走法俯視圖、眼高圖、手機橫向（需另裝 `playwright-core`） |
| `server.mjs` | 本機靜態伺服器，白名單只開放本包 GLB 與林地遭遇的兩件背景（倒木、樹樁） |

背景的倒木與樹樁唯讀沿用 `art/exports/qingxi-encounter-a/`（PR #39，同作者），倒木只用來遮住下游端的斷面，不算本包新模型。樹與草卡是展示用背景，不是交付素材。

審查用畫面：`__wh.setPlan(true)` 切成標模組 ID 的正交俯視圖，`__wh.eye(true)` 切成 1.7 m 眼高視角（替身隱藏）；`capture.mjs` 會輸出兩種走法的俯視圖與三張眼高圖。

## 尚未完成（第二批）

- A07–A12（育幼足跡泥面、淺灘、水位尺、倒伏竹、觀測亭殘基、共鳴石）與育幼線索、非戰鬥警戒、清理泥沙前後的水面變化。
- A04 另兩種堆形、A05 另兩種高矮、A08 三種踏面；碎石／濕痕散布小件；下游端轉接件；標變體 ID 的接縫／碰撞圖。
- 短錄影；Unity 匯入、實機手機效能與觸控手感都還沒驗證。
