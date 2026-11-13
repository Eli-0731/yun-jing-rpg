| ID | 名稱 | 狀態 | 負責人 | 版本 | 主要輸出 |
|---|---|---|---|---|---|
| C2 | 借住處後門與室內對位 | 交付候選，待 Unity 場景驗收 | z1nnz + Codex | 外屋 v005、室內 v030 | `StarterHouse_reardoor_v005.fbx`、`lodging-room-reardoor-v030.fbx` |

## 變動

- 在 Dondon 的 `StarterHouse v004` **副本**上把後牆正中窗改成 1.2 × 2.2 m 後門，保留外屋其餘結構。後門葉沿用該屋前門的格窗、木板和門環造型，縮放至後門尺寸。原檔沒有被覆寫。
- 以本組舊版室內模組 v029 為基礎，將北牆中央兩塊實心牆換為 3 m 門牆：中間 1.2 m 開口、兩側留牆體；門葉沿用同套前門。室內地板標高是相對 0 m，外屋地板標高為世界 0.54 m，場景整合時需以這個位移對齊。
- 將協作者 B 的 TI01–TI08d 共 11 件既有室內資產放入房間作首輪配置。擺放座標在 `tools/art/build_c2_interior_reardoor_v030.py`，家具原始模型仍由原分支提供，沒有改造或覆蓋。

## 可檢視成果與限制

可編輯母檔與既有室內 v028 基底副本在 `art/source/c2-home-interior-v1/`；外屋 GLB 與兩件 FBX 在本資料夾；AI 室內三視圖在 `art/references/lodging-interior-kit-v1/`。預覽：`art/previews/c2-home-interior-v1/rear-door-v005.png`、`interior-reardoor-v030.png`、`interior-furniture-top-v030.png`。三張均已實際檢視，後門與室內門洞可見；室內家具配置是第一輪，部分物件仍需依實際玩法與走道再調整。

`verify_c2_reardoor.py`：兩件母檔結構通過；兩個 FBX 回匯通過（外屋 506 meshes／108616 三角面；室內含家具 349 meshes／247978 三角面）。室內整包 GLB 生成後達 325 MB，未作最終交付；Unity 應用 FBX 與個別資產，不應用整包房間作手機端最終網格。Unity 編譯、碰撞、開門、睡眠與手機效能尚未驗證。後門外的台基及地面落差須在 Unity 場景補可走階或坡道。

來源歸屬：StarterHouse v004 由 Dondon 製作；TI01–TI08d 由協作者 B 製作。此交付是 z1nnz 與 Codex 的外屋後門改版、室內門洞與配置工作；原作者歸屬保留。

## 2026-11-13 審查重做：外屋 v006、室內 v031

依 11/12 審查，以 Josh 的 VL 材料函式重做外屋的舊灰牆、舊木、石基、黛瓦及窗紙；室內殼體以 TI 的舊木、石、窗紙材質函式配合 VL 的室內舊灰牆，保留協作者 B 的 TI01–TI08d 家具材質與配置。函式副本位於 `art/source/c2-home-interior-v1/shared/`，重建腳本為 `rework_c2_v006.py`。10 張 512 像素 BaseColor 貼圖由上述函式取樣輸出，位於 `v006/Textures/`；新增貼圖已打包於來源 `.blend`，室內 FBX 另引用本資料夾的貼圖檔。幾何未重建。

外屋來源：`art/source/c2-home-interior-v1/StarterHouse_reardoor_v006.blend`；輸出：`v006/StarterHouse_reardoor_v006.fbx`、`.glb`。室內來源：`art/source/c2-home-interior-v1/lodging-room-reardoor-v031.blend`；輸出：`v006/lodging-room-reardoor-v031.fbx`。預覽：`art/previews/c2-home-interior-v1/v006/rear-door-v006.png`、`front-v006.png`、`interior-reardoor-v031.png`。

`verify_c2_v006.py` 核對外屋與室內的後門門檻、兩側門框座標及尺寸，均與 v005／v030 完全一致。外屋 FBX 回匯 506 網格／108,616 三角面；室內 FBX 回匯 551 網格／253,802 三角面；外屋 GLB 亦可回匯。室內整屋仍只供配置檢視，正式手機端場景應採個別 TI 資產。Unity 中材質亮度、後門開關、碰撞、台基地面落差和手機效能未驗。

## 2026-11-13 v7 A1 修正：外屋 v007、室內 v032

屋瓦 BaseColor 改為黛灰色，平均 RGB 約 `#3A4048`，保留原瓦面明暗細節。室內灰牆改為大面積舊灰，只在牆腳與背陰角落保留少量剝落露磚。牆面改用已存在的 `C2_v006` 世界投影 UV 作渲染 UV，並把垂直比例調整至 3.5 m，避免牆頂重複取到牆腳磚區。其餘幾何、家具、後門位置與尺寸不變。

可編輯母檔在 `art/source/c2-home-interior-v1/`：`StarterHouse_reardoor_v007.blend`、`lodging-room-reardoor-v032.blend`；重建與驗證腳本同資料夾的 `rework_c2_v007_textures.py`、`rework_c2_v007.py`、`verify_c2_v007.py`。FBX、外屋 GLB 與完整貼圖在 `v007/`；預覽在 `art/previews/c2-home-interior-v1/v007/`。已核對母檔網格數、面數、尺寸及後門定位與前版相同，並檢視兩張新預覽；Unity 匯入與實景亮度仍待場景驗收。
