# SK01–SK03｜河谷遠山三層

本輪選用貼圖：

| ID | 圖檔 | 天空預覽 | 四片接縫 | 首尾接縫 |
|---|---|---|---|---|
| SK01 近山 | `SK01_ai-mountains.png` | `SK01_ai-preview-on-sky.png` | `SK01_ai-four-panel-seams.png` | `SK01_ai-wrap-seam.png` |
| SK02 中山 | `SK02_ai-mountains.png` | `SK02_ai-preview-on-sky.png` | `SK02_ai-four-panel-seams.png` | `SK02_ai-wrap-seam.png` |
| SK03 遠山 | `SK03_ai-mountains.png` | `SK03_ai-preview-on-sky.png` | `SK03_ai-four-panel-seams.png` | `SK03_ai-wrap-seam.png` |

- 規格：每張 4096 × 1024、RGB 不透明；按 1024 像素切成四片，依序用於四個 90° 弧面。
- 色彩：上緣融入灰藍天空；山腳落入霧色 `#A9B8C4`。近層有岩面與樹線，中層輪廓較柔，遠層只保留淡化山形。
- 接縫：四片圖的紅線是檢查標記，不進正式貼圖。首尾像素差 0；首尾與中央拼接處以霧帶過渡，需在實際天空與視角下再看。
- 來源：六張原創 AI 山景在 `art/source/sky-and-distance-v1/SK01-source-a.png` 至 `SK03-source-b.png`。可重現的整理檔為同處 `stitch_sk01_03.py`；使用 Python、Pillow、NumPy。
- 驗證：已檢查尺寸、RGB、首尾像素與天空／四片／首尾預覽；未在 Unity 6000.3.28f1 套材質、編譯或遊戲內檢查。
- 另有先前進行中的同 ID 試作檔；此文件明確指定上述 `ai-mountains` 三張為本輪選用版本，避免整合時混用。
