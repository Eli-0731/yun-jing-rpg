# 青溪公共演武區：本機橫向展示（v2）

```powershell
cd tools/training-yard-demo
npm ci
npm test          # 練功規則 11 項
npm start         # http://127.0.0.1:4178（只綁 loopback；PORT 可改埠號）
```

**這是本機演示：刷新即重置，不呼叫任何 API、不存檔、不產生正式修為。**

## 玩法

從村門（核心組 v13 牌樓，唯讀載入）沿土路走進演武棚，靠近任一木樁按 E／「互動」，選擇練功。凡骨身分的「引氣呼吸」會被鎖住，提示文字與伺服器 `NO_ROOT` 相同；「武技格擋」對所有人開放。

| 玩法 | 木樁 | 操作 | 回饋 |
|---|---|---|---|
| 引氣呼吸（三息） | 氣勁木樁 | 金圈擴張（吸）與「停」時按住空白鍵／大按鈕，金圈收回（呼、歇）時放開。是連續追蹤，不是點按。 | 玉圈跟隨金圈；玉紋光暈與聚靈光點隨同步率變化；每息評「圓融／平穩／散亂」，達標的繩圈依序亮起；呼吸聲隨氣量變化。 |
| 武技格擋（12 擊，三段加速） | 身法木樁 | 木臂後擺蓄勢，光圈收到按鍵時按 A／S／D（或 ← 左臂、↓ 下樁、右臂 →） | 正確：木擊聲、火花、頓幀；精準另有鈴聲。擋錯方向或來不及：中招紅暈與鏡頭晃動。沒有來勢時亂按會「散架」並中斷連擋，無法靠連打刷分。 |

兩種都可「再練一次」或切換；結果卡寫明成績只供本輪參考。

## 與伺服器的關係（未接入）

主線 `services/api/src/game.ts` 已有 `POST /actions` 的 `practice-basic`（`discipline: 'qi' | 'body'`）：qi 需要靈根，否則回 `NO_ROOT`；15 秒冷卻；修為增加由伺服器依出生效率計算。本展示**沒有**呼叫它。接入時，節奏成績只能作為 UI 回饋或額外表現，不得直接換算修為；請求須帶正式登入與 requestId。

## 檔案

- `practice.mjs`：純規則（時間驅動、可測）；`practice.test.mjs`：11 項測試（完美跟隨三息圓融、一直按或不按不過關、幀率無關、凡骨被擋、格擋時窗、擋錯方向、漏擋、亂按散架、按鍵重複忽略、時間倒退報錯）。
- `app.mjs`：three.js 場景、行走、兩個練功站的鏡頭、特效與 HUD；`audio.mjs`：WebAudio 合成音效（無音檔）。
- `server.mjs`：本機靜態伺服器，只允許固定檔名；`/assets/` 讀本組 GLB，`/world/` 只讀 v13 牌樓。
- `sw.js`、`manifest.webmanifest`：PWA，網路優先、離線時用快取。
- `capture.mjs`：用真 Chromium 以真鍵盤／觸控操作並截圖（需要另外安裝 `playwright-core`，不是本專案依賴）。

```powershell
node capture.mjs --modules <含 playwright-core 的資料夾> --chrome <chrome.exe> --url http://127.0.0.1:4178
```

截圖輸出到 `art/previews/qingxi-training-yard-v1/demo/`。

## 尚未驗證

實體手機的觸控手感、FPS、記憶體與安裝；HTTPS 部署；主遊戲 PWA（`tools/qingxi-trial/`）與 Unity 的接入。草地、樹與遠山是本頁自己的程序化背景，不是正式場景資產。

作者：Johnnnny0823（委託、方向）；Claude Code（Claude Opus 5.5）實作與驗證。
