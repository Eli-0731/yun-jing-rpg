# LF01–LF03 小生命

## LF01 遠處飛鳥

依已保存的 AI 三視圖，改成 2 三角面的雙面透明卡；`LF01_Spread.png` 與 `LF01_Folded.png` 有明確分層飛羽、淺腹和叉尾。`LF01_spread.glb`、`LF01_folded.glb` 為兩個姿態，場景端需切換影格；GLB 內沒有拍翅動畫。`LF01_animation-preview.png` 為放大對照，`LF01_game-size-60m.png` 為 1920 × 1080、水平視角 55° 下 60 m 距離的 15 像素卡片合成預覽。

## LF02 蝴蝶

改為 2 三角面的雙面透明卡；象牙白與低飽和赭黃兩種翅紋均畫出細翅脈、邊紋與眼斑。`LF02_ivory.glb`、`LF02_ochre.glb` 各附獨立貼圖。`LF02_animation-preview.png` 為兩色放大對照，`LF02_game-size-3m.png` 為 1920 × 1080、水平視角 55° 下 3 m 距離的 74 像素卡片合成預覽。建議只在高畫質層啟用。

## LF03 螢火

`LF03_Glow.png` 是 256 × 256 透明暖黃光點；`LF03_night-preview.png` 顯示夜色中的尺寸變化。`particle_params.json` 給出溪邊及 D5 蕈谷夜晚用的粒子建議，數量與透明疊加開銷須由 Unity 實測調整。建議高畫質層使用，白天停用。

兩種小卡都先檢視並保留 AI 三視圖，貼圖使用內建 imagegen 生成後裁切成 1024 × 1024 RGBA。Blender 母檔、灰模、GLB 變體與 `model_info.json` 位於各自目錄。距離預覽是依攝影機幾何計算像素尺寸的圖像合成，並非 Unity 實機畫面。Unity 影格切換、雙面透明、排序及手機效能尚未驗證。LF03 的貼圖與參數維持原版。
