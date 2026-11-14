# 天際線弧面與河谷遠山

本包沿用 `SM_Skyline_Arc`：一片 90° 弧面，半徑 800 m、高 240 m；旋轉至 0°、90°、180°、270° 組成整圈。模型來自 `art/codex-1108-moon-and-skyline-arc` 的已驗骨架。每片弧面使用對應的四分之一貼圖，或在支援的材質中取完整長條的 UV 四分之一區間。

| ID | 用途 | 完整長條 | 四片貼圖 | 天空預覽 | 接縫檢查 |
|---|---|---|---|---|---|
| SK01 | 河谷近層：樹線、岩面 | `SK01.png` | `SK01_q0.png` 至 `SK01_q3.png` | `SK01_sky-preview.png` | `SK01_seam-check.png` |
| SK02 | 河谷中層：稍淡的樹丘與山脊 | `SK02.png` | `SK02_q0.png` 至 `SK02_q3.png` | `SK02_sky-preview.png` | `SK02_seam-check.png` |
| SK03 | 河谷遠層：只留淡藍灰山形 | `SK03.png` | `SK03_q0.png` 至 `SK03_q3.png` | `SK03_sky-preview.png` | `SK03_seam-check.png` |
| SK04 | 東北近層：高陡花崗岩與疏松 | `SK04.png` | `SK04_q0.png` 至 `SK04_q3.png` | `SK04_sky-preview.png` | `SK04_seam-check.png` |
| SK05 | 東北中層：薄雲穿過峰肩 | `SK05.png` | `SK05_q0.png` 至 `SK05_q3.png` | `SK05_sky-preview.png` | `SK05_seam-check.png` |
| SK06 | 東北遠層：更高的峰越過雲海 | `SK06.png` | `SK06_q0.png` 至 `SK06_q3.png` | `SK06_sky-preview.png` | `SK06_seam-check.png` |

- 六張均為 4096 × 1024、RGB 不透明圖；上緣漸入天空色，下緣融入 `#A9B8C4` 霧色。左右首尾像素相同；四象限依 `q0 → q1 → q2 → q3` 依序繞一圈。
- `*_seam-check.png` 上半為四象限平接，下半依次放大 90°、180°、270° 與 360° 閉合點。細紅線只在檢查圖，正式貼圖沒有標記。
- `*_sky-preview.png` 是貼入中性天空的合成預覽，不是 Unity 實景截圖；實際視距、弧面重疊與霧參數仍須在 Unity 6000.3.28f1 中調整。
- 原始山景段與重建腳本位於 `art/source/sky-and-distance-v1/`；兩段各保留 256 像素重疊並於 180°、360° 處柔和混合。影像來源為內建 imagegen 生成的原創山景；腳本只處理尺寸、霧邊、接縫及四象限切片。

- SK04–SK06 的岩面比河谷遠山更高、更陡；SK06 使用無雪的灰石峰與雲海。SK05 右半來源段調低紫色飽和度，保留藍紫陰影但不形成亮紫色塊。
