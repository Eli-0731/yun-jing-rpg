# FA01 遠景瀑布卡

選定參考：`art/references/sky-and-distance-v1/FA01/three-view.png`。正面為細長白色水線，側面與頂面是薄卡。此件用於 B1 山壁遠處，基底置入霧層，避免近景瀑布的亮度。

- `FA01.png`：1024 × 1024 RGBA 水紋。上下首尾像素相同，可沿 V 方向重複；`FA01-source.png` 為保留的來源。`build_waterfall_card.py` 可重建貼圖與預覽。
- `FA01_gray.blend`：先建的 4 × 40 公尺二三角面灰模。`FA01.blend`、`FA01.fbx`、`FA01.glb`：貼圖卡片成品。`build_fa01_card.py` 可重建模型。
- `model_info.json`：面數、材質、解析度、原點與 UV 動畫建議。材質需 Alpha Blend、雙面顯示；V 負向每秒 0.12 UV、Repeat。實際流速須在場景中微調。
- `FA01_sky-preview.png`：與 SK01 天空合成；`FA01_four-panel-check.png`：四片排圖檢查卡片透明邊；`FA01_flow-loop-check.png`：四段縱向接圖檢查。四片圖是檢查用，正式場景僅放一張卡。
- Blender 已輸出成品；Unity 6000.3.28f1 匯入、實機透明排序及 UV 捲動尚未驗證。
