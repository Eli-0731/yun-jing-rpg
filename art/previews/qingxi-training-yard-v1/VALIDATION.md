# 2026-10-28 演武區重做：驗證紀錄

分支 `feature/qingxi-training-yard-v2`，從 main `ebe57d4` 建立。PR #32（Codex 版）已合併但被使用者退回，本次在同一組目錄重做。作者：Johnnnny0823（委託、方向）；Claude Code（Claude Opus 5.5）建模、烘焙、展示、驗證。

## 模型（Blender 5.2.2 實跑）

| 物件 | 外形 寬×深×高 m | LOD0 / LOD1 / LOD2 三角面 | 上限 | 圖集 | GLB（WebP） | 回匯 | 可動節點 |
|---|---|---|---|---|---|---|---|
| 演武棚 `training-shelter` | 7.12 × 6.04 × 4.33 | 61,278 / 30,638 / 13,481 | 65,000 | 2048 | 3.43 MB | ✓ | — |
| 氣勁木樁 `qi-striking-post` | 0.78 × 0.79 × 1.65 | 9,744 / 4,872 / 2,143 | 10,500 | 1024 | 0.76 MB | ✓ | rope_band_1, rope_band_2, rope_band_3, jade_disc |
| 身法木樁 `agility-post` | 1.21 × 1.10 × 1.67 | 3,676 / 1,837 / 808 | 6,000 | 1024 | 0.42 MB | ✓ | arm_left, arm_right, arm_low |
| 兵器架 `weapon-rack` | 1.90 × 0.65 × 1.65 | 2,688 / 1,344 / 591 | 5,000 | 1024 | 0.35 MB | ✓ | — |
| 刻紋練功石 `engraved-training-stone` | 2.08 × 1.67 × 0.28 | 3,072 / 1,536 / 674 | 4,000 | 1024 | 0.23 MB | ✓ | — |
| 練功旗 `training-banner` | 0.84 × 0.55 × 2.66 | 5,996 / 2,997 / 1,319 | 8,000 | 1024 | 0.64 MB | ✓ | banner_cloth |

LOD0 合計 86,454 三角面。演武棚超出原估 60k，是因為兩坡共 56 列筒瓦、瓦當、斗拱與四組雀替都是輪廓件；它是村口遠看得到的地標，LOD1 約 30k。上限改為 65k。

- 每件單一烘焙材質（BaseColor、ORM、Normal），陰影縫、邊緣磨損、苔痕、瓦縫與刻紋都跟著真實幾何烘焙。
- GLB 回匯：三角面數與包圍盒在全新場景重新匯入後一致（上表「回匯」欄）。零面積面 0、游離頂點 0。
- `nonManifoldEdges` 不為 0：來自封口與側面分開的頂點（保留硬邊），以及屋瓦、旗面等單面薄片。這些物件不做 3D 列印也不做布林，遊戲使用沒有影響。
- 圖集內 UV 由 Smart UV 自動打包；不適合拿來再烘光照貼圖（需要時另開 UV2）。
- 先前用同一批模型跑過 `blender-asset-qa` game profile（重做中期的分件版本），修正了封口 UV、極點零長邊、未套用縮放、重疊面與懸浮件後六件 0 錯誤；最終版改用烘焙管線內建的回匯與網格健康檢查。

## 預覽

- 眼高 1.7 m（Cycles）：`eye-height-village-approach.png`、`eye-height-steps.png`、`eye-height-under-shelter.png`、`eye-height-stone-and-banner.png`；整區 `yard-overview.png`。
- 每件 `<asset>/`：中性光五方位、兩張特寫、線框、風格光、正交三視與 `ref-vs-model.png`（AI 三視圖 vs 模型）。
- 操作畫面：`demo/` 14 張，由 `tools/training-yard-demo/capture.mjs` 在真 Chromium 以真按鍵／觸控操作截出（1280×720 與 844×390 觸控模式）。

## 展示頁

- `npm test`：11/11 通過。
- 真 Chromium 實跑：有靈根三息全「圓融」→「三息調和」；凡骨的引氣被鎖、顯示伺服器 `NO_ROOT` 原文、武技可練；格擋 12 擊中故意漏 1 擊，結果 11/12；console 與 page error 為 0。
- 手機橫向是瀏覽器觸控模擬，不是實機。

## 尚未接入／未驗證

- 主遊戲 PWA `tools/qingxi-trial/` 與 v14 入口組裝（核心組負責擺入）；本頁只唯讀載入 v13 牌樓作背景。
- 伺服器 `practice-basic`（qi／body）沒有接；節奏成績不換算修為。
- Unity 匯入、LOD 切換距離、碰撞（各件 `model_info.json` 只有建議）。
- 實體手機的 FPS、記憶體、觸控手感、安裝；HTTPS 部署。
- 正式美術審核（以《鳴潮》品質為目標，但未經美術主管逐件驗收）。
