# 青溪公共演武區：六件三視圖

六件物件的 AI 正／側／頂參考圖已先生成、檢視、保存，才開始 Blender 建模。手機無法開啟本機審圖頁；使用者於 2026-10-27 指示「先做吧，我還是看不了，大不了到時候刪掉重做」。這是製作授權，並非逐件造型的目視核准。原圖可從 PR 的 `art/references/qingxi-training-yard-v1/` 在手機直接查看。圖片具概念圖性質，側／頂視的局部透視或尺寸矛盾，以統一模型規格修正。

工作包來源：`z1nnz/yun-jing-rpg` 的 `7225d37`，`docs/execution/2026-10-27/01-novice-entry-parallel-work-42h.md`，A 組。本分支 `feature/qingxi-training-yard-v1` 從取得時最新的 main `b2a57673751057ff6c31538d72a73898c350e7d6` 建立。工作包文件當時尚未在該 main 中，因此沒有擅自合併其他組的變更。

| 檔名 | 正式建模規格與檢視修正 |
| --- | --- |
| `training-shelter-three-view.png` | 四柱、木樑與青瓦；低台基 0.12 m，前入口石坡淨寬 3.4 m、棚內無中央柱。圖中台階改為平緩坡。 |
| `qi-striking-post-three-view.png` | 高 1.65 m，八角舊木、三段麻繩墊、正面渦紋與節奏點。原提示四點、生成圖三點；模型依實際圖採三點。 |
| `agility-post-three-view.png` | 高 1.65 m，兩支格擋臂、一支低腿桿、紅布節奏提示及交叉穩固腳座。 |
| `weapon-rack-three-view.png` | 空木架，雙立柱、雙五槽橫梁與加寬腳座，不附武器。前兩次圖片生成被工具拒絕；第三次空架方案成功後才建模。 |
| `engraved-training-stone-three-view.png` | 約 1.8 × 1.5 × 0.28 m；天然石板、淺刻同心環與礦物色填紋。 |
| `training-banner-three-view.png` | 2.65 m 旗桿、0.70 × 1.40 m 青綠布旗、赭色印紋與邊、實體吊環和石座。 |

圖片由 OpenAI image_gen 生成，提示詞保存在 `prompts.json`，SHA-256 在 `image-manifest.json`。建模程式是原創程序幾何與自製 PBR 貼圖，未下載或轉用第三方模型。委託與造型方向來自 Johnnnny0823；Codex 執行圖像提示、建模與資產驗證。

本組只新增 `art/references/qingxi-training-yard-v1/`、`art/source/qingxi-training-yard-v1/`、`art/exports/qingxi-training-yard-v1/`、`art/previews/qingxi-training-yard-v1/`。核心入口、聽風台、其他協作者資產與 API 均交核心組接入。

本輪只交建模資產，不含練功玩法或 API 接線；Unity 編譯及手機效能也尚未驗證。
