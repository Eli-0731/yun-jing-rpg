# 線索、結果與回報的接線邊界

Eli-0731／Codex。這是獨立本機 fixture 契約，不是正式 API。

輸入：`{observationIds: string[], outcomeId: string|null}`。三種已知 observationIds 為 `cracked_sluice`、`silt_buildup`、`nursery_tracks`；未知線索略過並去重。B 尚未固定 outcomeId 命名，本包暫以 `clear_silt`、`restore_channel`、`protect_nursery` 作本機對照別名，之後由核心組依真正結果收據改映射，不直接 import A/B 未合併分支。未知結果、型別錯誤和資料缺漏不會推定為完成。

| 收到的範例 | 水情／畫面 | 不推定的事情 |
|---|---|---|
| 無線索且 outcomeId=null | 缺水、接近空桶，仍可任選三種回報 | 不能說已找到破槽或淤積 |
| 有已知線索且 outcomeId=null | 缺水、施工中／待協調，敘述只依已見線索 | 不能說導水已完成 |
| clear_silt | 部分水量，村田部分回潤，旗面仍為施工色 | 不等同完整修復 |
| restore_channel | 翻板背面、較高桶內水面、綠色成果旗面、濕度變深 | 不產生正式共同世界結果 |
| protect_nursery | 保留支流，村田仍部分水量 | 不等同村田完全供水；育幼區是動物育幼區 |
| 其他 outcomeId | 明示「尚無可確認的工程結果」，保守乾燥樣片 | 不把 constructor／__proto__ 等當有效映射 |

本地決定使用 `tell_shortage`、`inspect_crack`、`protect_nursery`；與上游結果分開保存。選擇、重複點選、改選、取消均不能改 `input`。重新載入另一份上游範例會清除該次本地決定，避免舊決定混入另一情境；重載頁面則還原同一份有效本機資料。沒有每日清單、固定順序或全線索門檻。

匯出的 `qingxi-water-report-c/v1` 固定 `mode=local-demo` 和 `requiresServerValidation=true`，僅含線索 ID、上游 outcomeId 及單一回報意圖，不含庫存、物品數量、貢獻、排行或獎勵。若未來轉成正式公共工程回報，核心組須驗證玩家／工程身分、區域距離、實際上游收據、當前狀態，以及 requestId 與 payload 綁定；在同一服務端交易保存／回傳唯一收據。不能接受前端自報工程完成或發獎。正式取消亦需服務端判定是否仍可逆，本機取消不代表撤回已提交的共同世界結果。

模型接線：C02 `StatusPivot` 可繞本機 X 軸旋轉 π；C03 兩個 `WaterSurface` 的 `Filled` 形態鍵可在 0–1 切換；C06 原始施工版與 `C06-complete.glb` 為同一件的材質變體。三種場景 PNG 是上述母稿狀態的實際渲染。此 PWA 使用圖片與物件標示互動，沒有即時載入 GLB 或 Unity 世界，也沒有正式場景碰撞。
