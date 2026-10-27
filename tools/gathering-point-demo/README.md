# 青溪採集路段：橫向示範

獨立網頁示範（Three.js 0.170.0，從 jsDelivr 載入，需要網路）。模型讀取 `art/exports/qingxi-gathering-visual-kit-v1/<Asset>/v001/<key>.glb`；缺件時以紅色線框代替，並在畫面上列出缺少的檔案。

## 啟動

在版本庫根目錄執行：

```bash
uv run --no-project python tools/gathering-point-demo/serve.py --port 8765
```

然後開啟 `http://127.0.0.1:8765/tools/gathering-point-demo/`。

- 加上 `--capture art/references/qingxi-gathering-visual-kit-v1/walkthrough_v001`，就能讓 `qxDemo.capture(name)` 存下走查截圖。
- 伺服器只綁定 127.0.0.1，不提供 `/gather`。

## 操作

| 按鍵 | 作用 |
|---|---|
| A／D 或 ←／→ | 沿溪路行走（沒有跳躍鍵） |
| W／S | 在臨水岔口選路：W 走踏板，S 涉水踩石。不選不能往前；涉水那條會被擋下並說明原因 |
| E | 第一次觀察（顯示特徵、可採部位、採後變化），第二次採集（1.2 秒，移動就中斷） |
| C | 切換近景 |

## 數量來源

- 網址沒有 `?server=` 時，畫面頂端標示「本機演示」。背包每一筆都註明「本機演示，非正式數量」。
- 有 `?server=http://…` 時，對 `POST {server}/gather` 送出 `{"node": "...", "asset": "..."}`，數量只取伺服器回應。
  - 成功回應：`{ok: true, item, qty, respawn_seconds?, reason?}`。
  - 尚未再生：回應 `{ok: false, reason, respawn_seconds?}`，畫面直接顯示 `reason`。
  - 伺服器沒有回應時，不算採集，現場也不變。

## 路段配置（1 單位 = 1 m）

| x（m） | 內容 |
|---|---|
| 0 | 採藥山門（安全點、起點） |
| 12 | 青溪蘭 |
| 24 | 赤露參 |
| 36.5–39.9 | 臨水岔口 |
| 40.0–44.39 | 支流渠：6 個踏板模組 |
| 51 | 嵌地玉脈石 |

- 主路寬 1.6 m。
- 踏板模組按 model_info 的板面寬（0.732 m）首尾相接，板面連續無縫。
- 板面在渠底上方 0.62 m，比岸面高 0.17 m，以 0.3 m 緩升上下，不需要跳。

## 尚未接入

- 正式伺服器、存檔、背包系統。
  - `?server=` 的 `POST {server}/gather` 是本示範自訂的格式，不是 `services/api` 現有的 `gather` 動作（節點 `quarry`／`seed-bank`／`herb-bank`，冷卻 15 秒）。接入時改成呼叫既有動作，數量仍只取服務端回應。
- 玩家角色：目前用簡單形體代替，人物製作已停。
- 碰撞體與導航網格：示範只用一維路線與岔口規則。
- 音效、粒子、Unity 場景。沒有 Unity 真機證據，不能稱為可玩版本或已達目標畫質。
