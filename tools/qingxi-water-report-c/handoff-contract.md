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

模型接線：C02 `StatusPivot` 可繞本機 X 軸旋轉 π。新版 C03 三個獨立形體的 `WaterSurface_C03…` 各有 Empty 基底與 `HalfFull`、`Filled` 兩鍵：空時兩鍵為 0，半滿只開 HalfFull，滿時只開 Filled。不要同時疊加兩鍵。C05 的 SoilMoisturePatch 只示範收到的村田狀態；C06 兩種裁切各有施工／完成 GLB，完成版改用閉口圈與水紋，不只是改色。共用接口見 README，各空節點採 `變體ID__接口名`。

`index.html` 以實際模型渲染圖呈現 A/B 兩個排列，換排列不改回報決定或上游結果。`walk3d.html` 則真的載入組裝 GLB、允許 1.7 m 眼高移動與觸控；水情選擇只是本機檢視，不回寫正式工程。碰撞為保守整件包圍盒與 0.16 m 玩家半徑，沒有 Unity 主場景或精細逐面碰撞。固定 Three.js 0.186.1；3D 頁需 npm ci 與本機伺服器，不能用 file:// 取代模型載入驗收。
