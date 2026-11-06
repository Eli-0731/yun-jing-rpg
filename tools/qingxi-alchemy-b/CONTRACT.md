# 煉製小工坊：正式伺服器契約（提案）

狀態：**提案，尚未接線**。本 PR 沒有修改 `services/api`、`packages/contracts`、`packages/content`，也沒有修改主場景。下面列出需要核心組實作或決定的事項。前端示範的規則在 `src/alchemy-core.mjs`，伺服器端應以同樣規則在**自己的庫存**上重算。

## 1. 原則

- **一律以伺服器結果為準。** 前端只上傳「選了哪些材料批次、怎麼處理、什麼火候、怎麼收取」，**不上傳**藥效、穩定度、成品數量，也不上傳「我做了幾瓶」。
- **沿用現有的 `POST /v1/actions`**（`services/api/src/app.ts`）以及 `Game.act()` 的收據機制：
  - `receipts(actor_id, request_id, fingerprint, result)`
  - `ledger(actor_id, request_id, changes)`
  - 同一個 `requestId` 加上同一個操作內容，回傳原收據。
  - 同一個 `requestId` 但內容不同，回 `409 IDEMPOTENCY_CONFLICT`。
- **規則是決定性的。** 同樣的庫存批次、配方和選擇，一定得到同樣結果。不使用亂數，所以失敗原因可以解釋、可以重現。
- **不設固定的在線等待**，也不設會放大永久強度的倒數。玩家的操作步驟本身就是過程。現有 `world.json` 的 `body-bath` 是 `seconds: 60`，要不要改成 0，或改成只是演出時間，由核心組決定（見第 6 節）。

## 2. 操作一：`alchemy-brew`（辨材後配伍、處理、控火、收取，一次送出）

```jsonc
POST /v1/actions
Authorization: Bearer <access token>          // 角色由 token 決定，不在 body 內
{
  "requestId": "6f1c…-uuid",                   // 每爐一個；網路重試時沿用同一個
  "action": {
    "kind": "alchemy-brew",
    "recipe": "body-bath",                     // 或研究變體 "body-bath:breath"
    "picks":   { "main": "<stackId>", "aux": "<stackId>" },   // 伺服器庫存中的材料批次
    "process": { "main": "slice", "aux": "soak" },            // slice | grind | soak
    "fire": "medium",                                          // gentle | medium | strong
    "collect": "filter",                                       // filter | direct
    "station": "qingxi-alchemy-b"                              // 工坊位置，供距離檢查
  }
}
```

伺服器必做的檢查與動作：

1. 檢查角色是否在工坊互動範圍內。比照 `merchant_proximity`，使用短效的工坊接近紀錄。
2. 確認 `picks` 屬於這個角色，數量足夠，且材料已辨識（見第 4 節）。
3. 依配方槽位檢查屬性與藥性。不符時回 `400 WRONG_MATERIAL`，並在 `detail` 中具體指出哪個槽位放錯、錯在哪裡；這時不扣材料。
4. 用伺服器上的批次純度與穩定度，以及 `process`／`fire`／`collect`，重算藥效與穩定度。
5. 扣除材料，寫入 `ledger`。
6. 成功時產生一筆 `CraftJob`（可直接領取）；研究變體失敗時，依失敗階段退回部分材料。
7. 寫入 `receipts` 並回傳。

回應沿用 `Snapshot`，另外附上本爐結果：

```jsonc
{
  "…Snapshot": "…",
  "brew": {
    "brewId": "<jobId>",
    "recipe": "body-bath:breath",
    "success": false,
    "stage": "fire",                          // process | fire | collect
    "reason": "武火讓赤露參漿汁焦化，…",
    "consumed": [{ "stackId": "…", "item": "chilu-berry", "quantity": 3 }],
    "returned": [{ "item": "chilu-berry", "quantity": 1 }, { "item": "yumai-crystal", "quantity": 1 }],
    "potency": 61,
    "stability": 47
  }
}
```

## 3. 操作二：`claim-craft`（沿用現有）

- `{ "kind": "claim-craft", "job": "<brewId>" }`
- 每次按「領取」都產生新的 `requestId`。網路重試則沿用原本的 `requestId`。
- 已領過的 job 回 `409 ALREADY_CLAIMED`，與現有實作相同，庫存不會增加。
- 前端示範的 `claimLocal()` 也是同樣行為（單元測試第 11 項）。

## 4. 辨材

- **建議：** 辨材在本地完成，只是 UI 揭示。材料的屬性與藥性是固定設計值，不影響經濟。
- 若核心組要把「已辨識」當成進度，則加一個 `identify-material` 操作。這個操作寫入 `player.milestones`，例如 `identified:chilu-berry`，並使用同一套收據機制。

## 5. 綁定規則

- 成品的 `bound` 等於所有扣除批次的 `bound` 取 OR。這與 `spend()` 回傳 `bound`、`craft` 的寫法一致。
- 退回的材料保留原批次的 `bound`。
- 綁定成品不可交易，沿用現有規則。

## 6. 等核心組決定或接線的項目

| # | 項目 | 目前狀態 |
|---|---|---|
| 1 | PR #31 材料的伺服器 item id | 轉接層 `serverItem`：青溪蘭花莖 暫定 `qingling-herb`；赤露參漿果、玉脈晶為 `null`（未指派） |
| 2 | `body-bath` 材料 | 伺服器現為 `qingling-herb ×3`；本示範為「木溫主藥 ×1 ＋ 火溫輔藥 ×2」，需要擇一 |
| 3 | 研究變體 `body-bath:breath`（調息清露） | 伺服器沒有這個配方，成品 `breath-dew` 也沒有 item 定義 |
| 4 | `recipe.seconds` | 現為 60 秒固定等待；本示範沒有等待 |
| 5 | 材料批次的純度與穩定度 | `Stack` 現在只有 `potency`；需要新增欄位，或由 `potency` 推導 |
| 6 | 工坊接近檢查 | 需要新增工坊接近紀錄，比照 `merchant_proximity` |
| 7 | Unity 場景接線 | 本 PR 只交模型、佈局參考（`data/layout.json`）與示範，沒有修改主場景 |

## 7. 失敗與退回規則（研究變體）

| 階段 | 觸發條件 | 退回 |
|---|---|---|
| process | 玉脈晶被選了切段（切不動） | 該槽位全數退回，其他槽位各損 1 |
| process | 玉脈晶沒研成粉 | 主藥 1、佐藥 1 |
| fire | 武火 | 主藥 1；佐藥 1（從濾布殘渣回收晶粉） |
| collect | 穩定度低於 55 | 主藥 1 |

已知配方材料正確時必定成功。各種選擇只會改變藥效與穩定度：

- 品級依穩定度判定：75 以上為上品，60 以上為中品，其餘為下品。
- 單元測試第 5 項逐一驗證了 54 種選擇組合。
