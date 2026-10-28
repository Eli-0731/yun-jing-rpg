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
| `A01_end_source` | `A01_end_source_01` | 收尾件：下游 2.4 m 接口，往上游抬升進亂石堆與小泉潭，背面封閉 |
| `A02_side_crack` | `A02_side_crack_01` | 石槽側面裂口與細流，正面看得到 |
| `A02_end_break` | `A02_end_break_01` | 最後一塊斜裂，末端一截與端柱外傾，水從缺口落下 |
| `A03` | `A03_FormationBase` | 傾斜半埋的圓形陣基，青綠銅環缺一段，散落銅片 |
| `A04` | `A04_SiltBar`、`A04_SiltBar_cleared` | 夾斷枝的泥沙矮壩與後方積水；下方小圖為清理後狀態 |
| `A05` | `A05_WitheredSedge_01` | 下垂的枯黃莎草叢，龜裂乾泥，與綠蘆葦不同 |
| `A06` | `A06_MarkerStone` | 0.35 m 濕線、0.85 m 舊水位乾苔圈 |
| `A04_silt_side` | `A04_SiltSide_02` | 沿一側河岸伸出的低矮沙嘴，細流被擠到對岸 |
| `A04_silt_jam` | `A04_SiltJam_03` | 以橫倒腐木為骨架的雜物壩，木下滲出兩道細流，上游積潭 |
| `A05_tall_sparse` | `A05_WitheredSedge_02` | 1 m 高、稀疏、折葉下垂，兩根乾穗 |
| `A05_low_mat` | `A05_WitheredSedge_03` | 0.3 m 高、順舊水流倒伏蓋在石上的草墊 |
| `A07` | `A07_NurseryTracks` | 三種大小的四趾爪印走向水邊，飲水處踩亂；只供觀察 |
| `A08_steps_line` | `A08_steps_line_01` | 六塊平頂踏石成一列 |
| `A08_slabs_stagger` | `A08_slabs_stagger_01` | 四塊大石板之字交錯 |
| `A08_gravel_bar` | `A08_gravel_bar_01` | 自然卵石灘＋三塊大圓石＋低處急流 |
| `A09` | `A09_WaterGauge` | 刻度清楚的木樁水位尺，0.85 m 綁繩是舊水位，現在只到 0.3 m |
| `A10` | `A10_FallenBamboo` | 倒竹斜成屏障，一端留 1.2 m 缺口可穿過 |
| `A11` | `A11_PavilionRuin` | 石台殘基、台階、斷柱、倒梁、石凳、碎瓦 |
| `A12` | `A12_ResonanceStone` | 微弱青光分岔紋路的河石，腳下扁石圈與淺水 |
