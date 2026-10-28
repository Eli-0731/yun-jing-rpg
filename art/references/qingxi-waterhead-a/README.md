# 青溪上游調查：AI 正／側／背三視圖

依工作包與共同模組規則，每個**新形體**（含同一家族的形體變體）先以 AI 生成正、側、背三視圖，檢視輪廓與比例並保存，才開始 Blender 建模。

- 生成：2026-10-28，經本機 Codex CLI（`codex exec`）呼叫 OpenAI 圖像生成；共用提示在 `generate_three_view.sh`，各件主體描述在 `prompts.json`。
- 檢視：建模前逐張檢視；檔案大小、SHA-256 與檢視紀錄在 `image-manifest.json`（`python make_manifest.py` 重算）。
- 建置腳本 `art/source/qingxi-waterhead-a/build_waterhead.py` 找不到對應三視圖就拒絕建模。
- 委託：Johnnnny0823。

| 參考圖 | 對應模型 | 檢視重點 |
|---|---|---|
| `A01_straight` | `A01_straight_01` | 7 m 寬、6 m 長，河道 2.4 m、深 0.9 m；細流、兩側卵石濕泥、岸上舊水位淺帶；兩端剖面相同 |
| `A01_bend_left` | `A01_bend_left_01` | 左彎約 25°，內岸卵石灘、外岸斜倒大石 |
| `A01_bend_right` | `A01_bend_right_01` | 右彎約 40°，外岸層理岩壁＋樹根、內岸沙洲；圖中兩端的整齊石柱收邊不採用 |
| `A01_narrow` | `A01_narrow_01` | 兩塊大岩夾成約 1.2 m 小峽；圖中水偏深，建模保持低水位 |
| `A02_side_crack` | `A02_side_crack_01` | 石槽側面裂口與細流，正面看得到 |
| `A02_end_break` | `A02_end_break_01` | 最後一塊斜裂，末端一截與端柱外傾，水從缺口落下 |
| `A03` | `A03_FormationBase` | 傾斜半埋的圓形陣基，青綠銅環缺一段，散落銅片 |
| `A04` | `A04_SiltBar`、`A04_SiltBar_cleared` | 夾斷枝的泥沙矮壩與後方積水；下方小圖為清理後狀態 |
| `A05` | `A05_WitheredSedge_01` | 下垂的枯黃莎草叢，龜裂乾泥，與綠蘆葦不同 |
| `A06` | `A06_MarkerStone` | 0.35 m 濕線、0.85 m 舊水位乾苔圈 |
