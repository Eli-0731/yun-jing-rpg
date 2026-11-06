# 青溪公共演武區：六件三視圖

六張 AI 正／側／頂參考圖於 2026-10-27 由 Codex 以 OpenAI image_gen 生成並保存（提示詞 `prompts.json`，SHA-256 `image-manifest.json`），之後才開始建模。使用者當時因手機看不到審圖頁，指示「先做吧，我還是看不了，大不了到時候刪掉重做」；這是製作授權，不是逐件目視核准。

## 2026-10-28 重做

PR #32 的 Codex 模型被使用者退回。重做前，Claude Code 再次逐張檢視這六張圖（沒有重新生成，圖檔與雜湊不變），並以它們為準重建模型。每件的「三視圖 vs 模型正交圖」對照在 `../../previews/qingxi-training-yard-v1/<asset>/ref-vs-model.png`。

| 檔名 | 本次建模依據與取捨 |
| --- | --- |
| `training-shelter-three-view.png` | 依圖改回石台基＋前方兩級台階（Codex 版改成緩坡）；曲面屋頂、四角翹起、筒瓦與瓦當、正脊捲尾、懸山博風板與懸魚、四柱鼓形柱礎、額枋與由額、雀替、斗拱、前柱玉結垂飾。圖上沒有字，匾額只用抽象劍環紋。高度約 4.3 m（含脊飾），比圖註 3.8 m 高，為了讓梁下淨高約 2.1 m。 |
| `qi-striking-post-three-view.png` | 八角木樁、三段螺旋麻繩圈與側夾板、正面玉紋圓盤、下方三顆釘、四塊石座與木楔。 |
| `agility-post-three-view.png` | 圓樁、皮革頂墊與黑繩、左右兩臂向前斜伸（左臂紅布纏）、前下方一支腿樁、十字腳座與木楔。三支臂是獨立節點，供格擋動畫使用。 |
| `weapon-rack-three-view.png` | 空架：雙立柱、上下兩根六槽橫梁、穿釘、鐵箍與鉚釘、斜面腳座。依圖不放武器。 |
| `engraved-training-stone-three-view.png` | 約 1.8 × 1.5 × 0.28 m 不規則石板，含缺角；三道同心環、四瓣花與四個菱形刻紋，礦物青填色。 |
| `training-banner-three-view.png` | 石座、鐵套與四片支撐、木桿、象牙色頂珠、橫桿與繩綁、吊環、0.70 × 1.40 m 青綠旗面與赭邊、同心圓紋、破損旗尾、兩側垂穗。 |

作者：三視圖提示與生成 Codex（Johnnnny0823 委託）；2026-10-28 檢視與建模 Claude Code（Claude Opus 5.5）。沒有使用第三方模型。

本組只改 `art/references|source|exports|previews/qingxi-training-yard-v1/` 與 `tools/training-yard-demo/`；核心入口、聽風台、其他協作者資產、API 與 Unity 均未修改。
