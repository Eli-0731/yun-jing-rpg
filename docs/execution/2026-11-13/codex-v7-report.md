# Codex v7 執行報告

## A 部分｜未過項目重做（2026-11-13）

依 A1 → A2 → A3 順序完成；每項完成後分別提交並推送。工時為本次實際操作的近似值。

| ID | 分支／提交 | 自評／10 | 預覽 | 實際工時 | 未做到或待驗證 |
|---|---|---:|---|---:|---|
| A1 C2 借住處 | `art/codex-1108-c2-home-interior`／`4f50c583` | 7.6 | `art/previews/c2-home-interior-v1/v007/front-v007.png`、`interior-reardoor-v032.png` | 約 0.25 小時 | Unity 場景材質亮度、後門互動與碰撞未驗。 |
| A2 MM01／MM02 石峰 | `art/core-1112-codex-keyart-distance`／`234fa6fa` | 8.0 | `art/exports/midground-v1/MM01/MM01_preview.png`、`MM02/MM02_preview.png`、`C-pack-review/C-midground-with-SK03.png` | 約 0.20 小時 | 2048 貼圖由 imagegen 的 1254 原圖放大，沒有新增原生細節；Unity 中景尺寸、霧腳、雙面透明排序未驗。 |
| A3 LF01／LF02 小生命 | `art/core-1112-codex-keyart-distance`／`0d774c79` | 7.8 | `art/exports/life-v1/LF01/LF01_game-size-60m.png`、`LF02/LF02_game-size-3m.png` | 約 0.20 小時 | 新版 GLB 為獨立姿態／色彩卡，鳥的兩格需由場景端切換，沒有內建拍翅動畫；Unity 透明排序與手機效能未驗。LF03 保留原版。 |

A1 外屋瓦色貼圖平均 RGB 約 `#3A4048`；室內上半牆露磚像素比例為 0，牆腳約 10.3%。外屋和室內的母檔網格、三角面及後門定位均與前版一致，兩件 FBX 和外屋 GLB 回匯通過。A2 各 12 三角面、2048 × 2048 RGBA，Blender 5.2.2 遊戲資產 QA 皆 0 錯誤，FBX 與 GLB 回匯皆為 12 三角面；舊網格交付與其專用建模腳本已移除。A3 四個 2 三角面卡片的 GLB 均為雙面透明，Blender QA 0 錯誤；距離預覽以 1920 × 1080、水平視角 55° 計算，鳥 60 m 約 15 像素，蝶 3 m 約 74 像素。這些預覽均是美術合成，並非 Unity 實景截圖。

下一項為 B 部分 CO02；B 尚未開始。
