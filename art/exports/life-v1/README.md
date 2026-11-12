# LF01–LF03 小生命

## LF01 遠處飛鳥

以已保存的 AI 三視圖為比例參考製作一隻輕量飛鳥；身體、叉尾及兩片翅膀分開。左右翅以各自樞軸在 24 fps 的第 1–25 格循環拍動。`LF01_slate.glb`、`LF01_warm.glb`、`LF01_pale.glb` 是三種羽色。場景端可用同一隻模型錯開時間、大小與位置組成遠方鳥群；不提供地面動作。`LF01_animation-preview.png` 為四格預覽。

## LF02 蝴蝶

兩片翅膀各有自己的樞軸和拍翅動畫；`LF02_ivory.glb` 與 `LF02_yellow.glb` 為白、黃兩色，建議只在高畫質層啟用。四格預覽在 `LF02_animation-preview.png`。遠距剪影優先，尚未加翅脈細節；近看效果需要場景審查。

## LF03 螢火

`LF03_Glow.png` 是 256 × 256 透明暖黃光點；`LF03_night-preview.png` 顯示夜色中的尺寸變化。`particle_params.json` 給出溪邊及 D5 蕈谷夜晚用的粒子建議，數量與透明疊加開銷須由 Unity 實測調整。建議高畫質層使用，白天停用。

兩個模型的 Blender 來源檔、GLB 變體與 `model_info.json` 位於各自目錄。已用 Blender 5.2.2 輸出；Unity 動畫、雙面材質和實機效能尚未驗證。
