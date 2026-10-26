# 青溪聽風台 v1：原創場景模組

製作歸屬：z1nnz 與其 Codex 協作。本模組由本組製作，其他協作者如需修改請從這份來源檔接續，避免重複建模。

## 來源與界線

- 製作前先產生並檢視 `art/references/qingxi-listening-terrace-v1/three-view.png` 三視圖。
- 本模型由 `tools/art/build_qingxi_listening_terrace_v1.py` 在空白 Blender 場景建立。未匯入使用者下載的角色、鞦韆或 Boss 場景檔案，也未使用其網格或貼圖。
- 下載的第三方檔案只留在使用者本機作為觀察資料，不進本儲存庫。

## 本輪完成

- 約 8.5 × 6 公尺的橢圓石台、四階入口、分段弧形石拱與懸掛竹椅。
- 改用暖色砂岩、象牙色石材、青綠銅件及藍色野花。增加石縫、弧形刻線、平台邊緣石塊、座板支撐與拱頂吊點。
- 來源：`art/source/qingxi-listening-terrace-v1.blend`。
- 可交換網格：`art/exports/qingxi-listening-terrace-v1.glb`。
- 四角度靜態預覽：`art/previews/qingxi-listening-terrace-v1/`。

## 驗證與後續

- Blender 5.2.2 背景建置與 GLB 匯出成功。
- `blender-asset-qa` 對平台、石拱、竹椅及吊繩代表物件檢查通過，沒有錯誤。保留的警告是平台重疊內面、繩與吊點的接縫內面，以及平台底部為了嵌入地形而位於 z=-0.25 米。
- 已檢視透視、正面及三視圖。這一版是可編修的場景模組，仍需雕刻石材邊緣、製作正式貼圖、完成烘焙與 Unity 實機驗證，尚未達到最初 AI 概念圖的細節水準。
- Blender 的程序石材紋理尚未烘焙到 GLB 貼圖；GLB 主要提供幾何與基本材質，Unity 中的視覺效果需要獨立檢查。
