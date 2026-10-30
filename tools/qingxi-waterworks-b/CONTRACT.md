# 古水路修復：服務端接線說明（提案）

狀態：**提案，尚未接線**。本工作包沒有修改 `services/api`、`packages/contracts`、`packages/content`、主場景或 HUD。前端示範的規則在 `src/waterworks-core.mjs`，伺服器應以同樣規則在**自己的庫存與帳本**上重算。前端示範的完工結果只存在瀏覽器記憶體，標示「本機演示 · 非正式結果」，不入正式背包，也不產生正式貢獻。

## 1. 原則

- **以伺服器結果為準。** 前端只上傳「哪個槽位放了哪一件、補石、閘門開關、處理方向、用哪批材料」，**不上傳**供水百分比、育幼區影響、結果 ID 或貢獻值。
- **沿用現有的 `POST /v1/actions`**（`services/api/src/app.ts`）與 `Game.act()` 的收據機制，不另開 API：
  - `receipts(actor_id, request_id, fingerprint, result)`：同一個 `requestId` 加同一個操作內容，回傳原收據。
  - 同一個 `requestId` 但內容不同，回 `409 IDEMPOTENCY_CONFLICT`（`game.ts` 現有行為）。
  - `ledger(actor_id, request_id, changes)`：`UNIQUE(actor_id, request_id)`，同一請求不可能寫兩筆扣料。
- **規則是決定性的。** 不使用亂數、不讀時鐘；同樣的版面、線索與淤積狀態，一定得到同樣結果。
- **不改現有帳本格式。** 本提案只新增一種 `action.kind`；材料扣除與貢獻增加都寫進現有 `ledger.changes`。

## 2. 操作：`waterworks-commit`

```jsonc
POST /v1/actions
Authorization: Bearer <access token>          // 角色由 token 決定，不在 body 內
{
  "requestId": "wwb-7f3c…-uuid",               // 每次「完工」一個；網路重試沿用同一個
  "action": {
    "kind": "waterworks-commit",
    "projectId": "qingxi-old-channel-01",       // 工程 ID（board.json 的 id）
    "role": "builder",                          // 角色在工程中的身分：builder（施工）| surveyor（調查）| support（搬料）
    "layout": {                                 // 槽位 -> 段件 ID（只送玩家放的，不送舊槽）
      "P2": "B05", "P3": "B02", "P5": "B02", "P6": "B02"
    },
    "patches": { "P4": "B07" },                  // 舊槽補石
    "gates": { "P2": true },                     // 閘門開關
    "choice": "restore_channel",                 // clear_silt | restore_channel | protect_nursery
    "materialBatch": [                           // 伺服器庫存中的材料批次（不是數量本身）
      { "stackId": "<stone stack>", "quantity": 6 },
      { "stackId": "<timber stack>", "quantity": 2 },
      { "stackId": "<bronze stack>", "quantity": 1 },
      { "stackId": "<mortar stack>", "quantity": 1 }
    ]
  }
}
```

伺服器必做的檢查與動作，依序：

1. **收據先查。** 已有 `(actor_id, requestId)` 收據：指紋相同就回原收據，不同就回 `409 IDEMPOTENCY_CONFLICT`。這一步在扣料之前，所以重送不可能重複扣料或加貢獻。
2. 確認角色在工程現場範圍內，做法比照 `merchant_proximity` 的短效接近紀錄。
3. 確認 `observationIds`：線索以伺服器上的 `player.clues` 或 A 組正式欄位為準，不採用前端傳來的值。缺線索時仍可完工，結果會列出「完工後發現」。
4. 用 `src/waterworks-core.mjs` 的同一套規則重算：
   - 接口：任何斷開接口、重疊、沒接上的段件都會回 `400 BROKEN_JOINT`，`detail` 帶槽位、接口名與修法，與前端文字相同。
   - 方向條件：條件不符回 `400 CHOICE_REQUIREMENT`，例如「修回舊渠」沒經過 P4，或「保護育幼區」離育幼區不足 80 cm。
5. 依版面算出應扣材料。`materialBatch` 不足或不屬於此角色時回 `400 NOT_ENOUGH_MATERIAL`，這一步不扣任何東西。
6. 扣料、加貢獻、更新工程狀態，寫入 `ledger`，再寫 `receipts` 並回傳。這些在同一個交易內完成。

回應沿用 `Snapshot`，另附本次工程收據：

```jsonc
{
  "…Snapshot": "…",
  "waterworks": {
    "projectId": "qingxi-old-channel-01",
    "requestId": "wwb-7f3c…",
    "outcomeId": "wwb.restore_channel.direct",
    "villageSupply": 56,                        // 村田今天進水 %
    "nursery": "risk",                          // risk | safe | dry
    "silt": "slowing",                          // slowing | cleared | remaining
    "crack": "patched",                         // patched | leaking | bypassed
    "discovered": [],                           // 缺線索時完工後才發現的事
    "consumed": [{ "stackId": "…", "item": "stone", "quantity": 6 }, "…"],
    "contribution": 10,
    "replayed": false
  }
}
```

## 3. 結果 ID（`outcomeId`）

| outcomeId | 方向 | 版面條件 | 結果 |
|---|---|---|---|
| `wwb.clear_silt.diverted` | 先清淤 | 三通一側接放流坡進回流溝，另一側接關著的閘板；村田沒有流水 | 今天村田 0%；淤積清除，之後開閘接近全量 |
| `wwb.restore_channel.direct` | 修回舊渠 | 水經過舊槽 P4 到村田，路上有閘板 | 村田進水多、花費少；流水離育幼區 50 cm，有風險 |
| `wwb.protect_nursery.bypass` | 保護育幼區 | 流水離育幼區 ≥ 80 cm 到村田，路上有閘板 | 育幼區安全；多四個彎、石料約三倍，進水略少 |

C 組（`tools/qingxi-water-report-c/`）可以只讀 `outcomeId` 來切換告示。

## 4. 重送與並行

| 情境 | 伺服器行為 | 前端示範對應 |
|---|---|---|
| 網路逾時後重送同一個 `requestId` | 回原收據，`replayed: true`；不扣料、不加貢獻 | `complete()` 回傳 `replayed: true`；測試第 13 項 |
| 同一 `requestId`、改了版面或方向 | `409 IDEMPOTENCY_CONFLICT`；帳本不變 | 測試第 13 項 |
| 玩家連按「完工」 | 前端在版面不變時沿用同一個 `requestId`（`requestIdFor()`），等同重送 | 錄影 20–25 秒 |
| 完工後改版面再完工 | 新的 `requestId`，算新的一次施工，再扣一次材料 | 測試第 14 項 |
| 兩個請求並行 | 依 `players.version` 的樂觀鎖，後到的重試；收據表主鍵保證只成立一筆 | 不適用（單機） |
| 撤回（Ctrl+Z） | 只改前端版面，不送請求；已完工的帳本不回滾 | 測試第 15 項 |

## 5. 與現有 `contribute`／`claim-project` 的關係

- 現有 `contribute` 是「扣石料、加 `player.contribution`、推進 `world.channel`」，工程 ID 為 `world.json` 的 `qingxi-channel`。本工程可以兩種方式接：
  1. 新增 `waterworks-commit`（建議）。帳本 `changes` 寫材料扣除與 `contribution`，`world` 另存 `waterworks[projectId] = { outcomeId, siltCleared }`。
  2. 在 `contribute` 後面掛處理方向。不建議，因為 `contribute` 的數量由前端給。
- `claim-project` 的領取條件（`contribution > 0`）不需要修改。本工程完工會加貢獻，所以也能領。

## 6. 等核心組決定或接線的項目

| # | 項目 | 目前狀態 |
|---|---|---|
| 1 | 材料 item id | 示範用 `stone`、`timber`、`bronze`、`mortar`；伺服器目前只有 `stone`（`spend(player,'stone',…)`），其他三種需要指派 |
| 2 | 貢獻換算 | 示範為「扣除材料總數」，例如直通路線 +10；正式數值由核心組決定 |
| 3 | 角色欄位 `role` | 示範只有 builder；surveyor 是否以 A 組的調查計入，待定 |
| 4 | 線索來源 | 示範讀 `data/fixture-observations.json`；正式版改讀 A 組寫入的 `player.clues` 或專屬欄位 |
| 5 | 工程狀態 | 淤積是否清除（`siltCleared`）要存在 `world`，所有玩家共用 |
| 6 | Unity 場景接線 | 本工作包只交模型、Unity 試做專案與網頁示範，沒有修改主場景 |
