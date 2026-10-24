# 青溪山兔採獵整合契約

這是 D1 已實作的服務端結算契約，以及 D2 接入 Unity 區域程序的工作界線。山兔 AI、命中判定、模型動畫、場景與手機操作尚未完成。

## 區域程序送交死亡事件

區域程序先驗證玩家身分、位置、攻擊冷卻、命中、山兔生命及參與名單。每次山兔出生時產生新的 `spawnId`；死亡時產生一次 `deathId`。伺服器以內部憑證呼叫：

```http
POST /v1/internal/hunt/death
X-Service-Key: <區域程序的內部憑證>
Content-Type: application/json

{
  "deathId": "UUID",
  "roomId": "qingxi",
  "spawnId": "UUID",
  "enemyId": "qingxi-mountain-rabbit",
  "occurredAt": 1800000000000,
  "participants": ["玩家 UUID"]
}
```

`occurredAt` 使用服務端毫秒時間。新事件最多延遲 120 秒，最多四名不重複的參與者。成功回應每人的 `items`；相同事件重送回原收據；相同 `spawnId` 換新死亡識別會被拒絕。掉落由 API 按 `packages/content/hunting.json` 計算，不能由客戶端或區域程序填寫掉落數量。

區域程序若在送交時逾時，必須以原 `deathId` 和原內容重試。不能新建死亡識別來「再領一次」。事件送出之前，伺服器要保存出生與死亡識別；這項區域程序持久化尚待 D2 實作。

## 商販距離與出售

區域程序確認玩家站在青溪材料商販互動半徑內，呼叫：

```http
POST /v1/internal/merchant/proximity
X-Service-Key: <區域程序的內部憑證>
Content-Type: application/json

{
  "playerId": "玩家 UUID",
  "roomId": "qingxi",
  "merchantId": "material-merchant"
}
```

授權有效 30 秒。玩家端再用原有 `/v1/actions` 和自己的登入憑證提交：

```json
{
  "requestId": "本次出售 UUID",
  "action": { "kind": "sell-hunt", "item": "rabbit-meat", "quantity": 1 }
}
```

同一 `requestId` 重送回原快照。只可出售未綁定的山兔肉與山兔皮；售價由服務端內容資料決定。Unity 客戶端只有 `GameAction.item` 契約欄位，商販互動 UI 及位置核驗仍需在 D2 接線，不能把目前原型稱為可玩的狩獵流程。

## 安全與故障邊界

- 內部憑證只放在專用伺服器環境變數，不序列化進 Unity 客戶端或 Prefab。
- 客戶端不能呼叫內部結算端點；HTTP 測試驗證無憑證時回 403。
- API 能防止相同 `deathId`、相同出生、重送、並行與 API 重啟造成重複獎勵。
- API 尚不能獨自證明命中、距離與參與真實性；這些必須由 D2 的專用區域程序判斷。
- 目前只有本機 PGlite 自動測試，尚無外部 PostgreSQL 並行壓力測試。
- `merchant_proximity` 只記錄短效授權；區域程序必須每次互動前重新核對角色位置。

## 驗收命令

```powershell
npm run typecheck
npm test
npm audit --omit=dev --audit-level=high
```

本輪自動測試共 53 項通過，其中 8 項是新狩獵測試。Unity 編譯、雙端互動、實機效能與美術驗證不在此結論內。
