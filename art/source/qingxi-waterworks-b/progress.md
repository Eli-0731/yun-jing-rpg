# 青溪水工 B（重做 r2）— 進度紀錄

分支：`feature/qingxi-waterworks-b-r2`（舊分支 `feature/qingxi-waterworks-b` 與其工作樹保持不動）。

## 2026-10-29（十）實際按鍵操作錄影

- 播放器新增 `-qxFree <秒>` 自由錄影模式：不跑劇本，只依實際按鍵錄畫面（8 fps），每格記錄閘門、疊板、田面蓄水、鏡頭。
- `WaterDemoControls` 加 1／2／3 鏡頭切換（整條水路／F01 疊板閘／B01 取水口）；R 會把疊板升回卡滿。
- `tools/qingxi-waterworks-b/drive_demo_keys.ps1`：啟動播放器，用 Windows keybd_event 對視窗送真實按鍵。
  每個按鍵送出時都確認視窗在前景（fg=True）。
- 實跑 44 秒，352 格。播放器記錄的狀態與送出的按鍵一一對上：
  - 1 s 開閘；10 s 切疊板鏡頭，田已滿。
  - 11–15 s 按住 ↓，疊板 0.30→0.10，出水口放水。
  - 19 s 回總覽；22 s 關閘，田面退乾。
  - 30–34 s 按住 ↑，疊板升回 0.30；36 s 切取水口鏡頭。
- 影片 `art/previews/qingxi-waterworks-b/unity_player_keyboard_demo.mp4`：
  畫面上方是狀態列，按鍵提示由狀態變化推得；ffmpeg 取自 uv 暫存的 imageio-ffmpeg，未安裝到系統。

## 2026-10-29（九）水路依閘門傳遞＋F01 出水口改疊板閘

狀態：使用者指出「閘門都還沒放下來，哪來的水」。原本各段水面固定顯示，閘門擋不擋都一樣有水，這是錯的；
改為水路模擬。使用者另要求把 F01 尾端改成「木板卡滿擋水，要放水時再放下去」。尚未提交、未推送。

已完成
- `Runtime/WaterNetwork.cs`：水只從 S01 溪流進來，依 stream_test 順序逐段往下游灌。
  - 每段有灌水時間，水面由下往上浮出；上游斷水就退水。
  - 不含水面的件（S02、B06）直接把上游狀態傳下去。
- `Runtime/GateController.cs`（B05）：閘板預設在槽底（關），水停在閘門前；開閘上提 0.32 m，離底 8 cm 起放水。
- F01 出水口改疊板閘（`pieces_field.py`）：
  - 4 片橫木板，兩端鐵包角、頂板兩個提環；平時升到頂（堰頂 0.30）卡滿，田面保水、出水口不出水。
  - 轉手輪把整疊降進沉板槽（0.10–0.30 可停任一高度），水從板頂溢流出去；全降時田面退到溝底低水位。
  - 部件名稱 weir／weir_wheel、升降行程、手輪每圈 2.5 cm 不變；預設與 presets 改為 full 0.30／half 0.19／drain 0.10。
  - Blender 特寫 `F01/F01_weir_full|half|drain.png` 重拍，舊的 raised／hold 圖已刪。
- `FieldWeirController`：預設卡滿；`Holding` 判斷是否卡滿，`SetFill` 控制田面蓄水（由溝底漲到板頂）。
- `Runtime/WaterDemoControls.cs`：G 開關閘門、↑↓ 升降疊板、R 全部退乾。
  專案未啟用 IMGUI 模組，畫面上沒有按鍵說明。
- 只有一個水面的 FBX，Unity 匯入時根物件會改用檔名（`<件號>_water`），水路收集水面時一併處理。

驗證（實跑）
- `unity_demo_report.json`：
  - 疊板 full／half／drain 三個高度的位移、手輪角度、水面顯示都正確。
  - 水路五階段都通過：
    1. 關閘：B05 前有水、後面全乾。
    2. 開閘＋疊板卡滿：田滿、出水口乾。
    3. 疊板降下：出水口與 B02-V05 有水。
    4. 關閘：下游與田面退乾，閘門前保持有水。
    5. 疊板升回再開閘：田滿、出水口乾。
- Unity 正上方圖：`unity_network_closed_top.png`（水停在閘門前）、`_open_top.png`、`_release_top.png`。
- Windows 播放器實機錄影 `unity_player_network.gif`（22 秒）：
  閘門關 → 1.5 秒開閘 → 灌田 → 11 秒起降疊板放水 → 16 秒關閘退乾。每格的閘門與疊板狀態都有記錄。
- 效能（同機器，水路全開、疊板降下，12 個水面）：開 0.834 ms／關 0.695 ms。
  第一次量測只量到 4 個水面（WaterNetwork.Start 比灌滿晚執行），已修正後重量。
- QA：27 件，unity_import 全 PASS；F01 15,476 三角面，tri_budget WARNING。

仍待處理
- 疊板閘沒有逐片抽換（整疊一起升降）。
- 水路只支援單線路線（不分岔）；route_b／route_c 的分水還沒接。

## 2026-10-29（八）水面折射／泡沫／深度淡出、F01 堰板連動、實機錄影與效能

狀態：把上一節「仍待處理」逐項做完並驗證。尚未提交、未推送。

已完成
- `Qingxi/WaterFlow` 加上：
  - GrabPass 折射：依漣漪法線偏移取樣後方畫面；偏到水面前方物體上時退回不偏移。
  - 深度淡出：用 `_CameraDepthTexture` 算水厚，淺處透明度降到 35%。
  - 岸邊泡沫：水厚 `_FoamDist`（6 cm）內加一圈隨流動的白色泡沫（石頭、槽壁、岸線周圍）。
  - 新元件 `Runtime/WaterDepthCamera.cs`：確保攝影機輸出深度貼圖。
- 新元件 `Runtime/FieldWeirController.cs`（掛在 F01）：
  - 堰頂 0.10–0.30 m，堰板上移 crest − 0.28；手輪每圈 2.5 cm、繞自身垂直軸轉。
  - 田面水高度＝堰頂；堰頂 < 0.125 m 改顯示溝底低水位。規則與 model_info.states 相同。
- 新編輯器腳本 `Editor/WaterworksDemo.cs`：
  - 依 `routes.json` 的 stream_test 矩陣擺出 9 件。Blender→Unity 用 P·M·P，再乘上 FBX 根物件的匯入姿態
    （S01、S02、F01 的根物件帶 x 軸旋轉，直接覆蓋會讓整件立起來，已修正）。
  - 場景存成 `Scenes/StreamDemo.unity`，可輸出 Windows 播放器。
- `AttachWater` 同樣改為扣掉本體匯入姿態後再掛水面。

驗證（實跑）
- 堰板連動四個狀態（raised 0.30／hold 0.28／half 0.19／drain 0.10）：
  - 堰板位移與田面水位移都等於 crest − 0.28（誤差 < 0.1 mm）。
  - 手輪角度與預期相差 < 0.05°；顯示切換正確。
  - 結果 `unity_demo_report.json`（weir_tests_ok = true）；特寫 `unity_weir_<狀態>.png`。
- Unity 正上方正交圖 `unity_demo_top.png` 與 Blender `routes/stream_test_top.png` 配置一致。
- Windows 播放器實機（1280×720、D3D11、RTX 5060、Ryzen 7 7700）。結果 `unity_player_report.json`：
  - 錄影：水面以實際 `_Time` 流動，沒有推進時間位移。
    溪流 36 格、取水口 36 格（12 fps、3 秒），堰板 64 格（8 fps、8 秒）。
    堰板段堰頂 0.28→0.30→0.10→0.28，每格的堰頂都有記錄。合成 `unity_player_stream.gif`、`_intake.gif`、`_weir.gif`。
  - 效能：總覽鏡頭各 8 秒。水面開平均 0.833 ms（P95 2.86 ms），全關 0.698 ms（P95 2.62 ms）；
    12 個水面渲染器約多 0.14 ms。這是單一桌機的數字，不代表低階或行動裝置。

視覺檢查（實際開圖）
- `unity_demo_stream.png`（看得到河床、石頭周圍泡沫）、`unity_demo_top.png`、堰板四狀態拼圖、
  播放器取水口首格都開圖看過。

仍待處理
- 行動平台、低階 GPU 未測；GrabPass 在 URP 不可用（目前是 Built-in 管線）。
- 堰板沒有接玩家輸入（目前只有 API `SetCrest` 和 Inspector 拉桿）。

## 2026-10-29（七）S02 河床與河岸＋Unity 流動半透明水面

狀態：依使用者提供的河床與河岸三視圖（`art/references/qingxi-waterworks-b/S02_riverbed_banks_three_view_v001.jpg`）建 S02；
參考圖為 S 形，為配合 S01 demo 直段改做直段（同原點、同變換疊放）。另依使用者要求寫 Unity 水面著色器。尚未提交、未推送。

已完成
- `pieces_stream.py` S02：沿 S01 剖面掃出河床（砂礫貼圖 `ww_riverbed`，底 z = −0.30）與左右河岸（土層＋岸頂草色），
  右岸在 B01 掛點留 0.78 m 半寬缺口；水邊卵石 90 顆、大石 7 顆、岸頂草叢。9,056 三角面，5.60 × 12.10 × 0.79 m。
- `routes.py` stream_test：改放 S02，移除先前的純色佔位河床；5 個接縫縫隙 0、重疊 0；取水口在水內 0.10 m、水深 0.18 m。
- 水面另出 `<件號>_water.fbx`（14 件，與本體同原點）。田面積水改用材質 `ww_water_still`（石槽／溝的流動水仍是 `ww_water`）。
- Unity 新著色器 `Qingxi/WaterFlow`（`Shaders/WaterFlow.shader`）：
  - 水色貼圖與漣漪法線各取兩層，沿 UV 流向用不同速度往下游捲動（第一層 0.30／第二層 0.17 UV/s，
    第二層縮放 1.73 倍、側向偏 0.12），兩層混合避免整張平移感。
  - 半透明：alpha:premul、ZWrite Off、Transparent 佇列；頂點色越深的地方越不透明。
  - 三個材質共用：`ww_stream`（溪流，透明度 0.72）、`ww_water`（石槽／田溝，0.42）、`ww_water_still`（田面，慢速斜向）。
  - 全域 `_QxWaterTimeOffset` 只給批次截圖逐格推進時間；執行時保持 0。
- 批次檢查實跑：27 件匯入 PASS、材質全部對應；14 件水面掛為子物件、材質皆為 Qingxi/WaterFlow。
  逐格截圖（每格 1/8 秒）水面像素在 1 秒內平均變化 6.7（溪流）／5.3（石槽），確認有在動；
  合成 `unity_water_flow_stream.gif`、`unity_water_flow_chain.gif`、靜態 `unity_water_stream.png`。
- QA：27 件；tri_budget F01 WARNING；uv_unwrap 全部 WARNING；collision_mesh 全部 NOT_TESTED；其餘 PASS／NOT_APPLICABLE。

視覺檢查（實際開圖）
- S02 eye170、hero、`S02_compare.png`、`routes/stream_test_sheet.png`、Unity 溪流特寫與石槽特寫影格開圖看過。

仍待處理
- 流動截圖由批次推進時間合成，不是 Play 模式錄影；未測行動平台效能。水面沒有折射、岸邊泡沫、深度淡出。
- F01 堰板升降與水位連動目前只在資料（model_info states），Unity 沒有腳本。S 形河段未做（依指示）。

## 2026-10-29（六）S01 溪流（demo 直段）＋溪流取水測試

狀態：依使用者提供的溪流三視圖（`art/references/qingxi-waterworks-b/S01_stream_three_view_v001.jpg`）建 S01；
使用者指示 demo 不必照 S 形，中線改為直段。尚未提交、未推送。

已完成
- `pieces_stream.py`：S01 是水面本身（封閉薄透鏡體），全長 12.03 m、寬約 1.8 m、中央厚 6 cm、岸線收為 0；
  岸線細碎波浪、表面大波 ±1 cm＋漣漪 ±0.5 cm。原點在上游端中線、z = 0 為平均水面、水流 +Y。
- 新貼圖 `ww_stream`／`ww_stream_n`（青綠水色、ridged 雜訊光紋、沿流向拉長的白色水花）；
  UV 由件自訂（U 橫越、V 沿流向 0.6／m，捲動 V 即流動）；頂點色中央深、岸邊淺。
  kit_lib 新增 `uv_fn`、`shade_fn` 兩個件自訂掛鉤；build.py 支援 S 開頭件號並把 meta 的 `extra` 寫進 model_info。
- `SOCKET_kit_B01`：右岸中點，B01 原點放這裡（含旋轉），入水口伸入水面 10 cm，基座地面 = 水面 − 0.28 m。
  routes.py 的 on_socket 改為套用掛點旋轉（既有掛點旋轉皆為 0，不影響舊路線）。
- `routes.py` 新增 `stream_test`：S01（水面 z = 0.28）→ B01 取水 → B02 → B05（＋B06）→ B02 → F01 → B02-V05；
  5 個石槽接縫實測縫隙 0、重疊 0；取水檢查：入水口在水面內 0.10 m、取水深度 0.18 m（`routes.json` 的 intake_check）。
  河床與河岸是 routes.py 產生的測試佔位（純色），不是交付模型。
- Unity：新增 `ww_stream` 材質（Qingxi/StandardVC 為不透明著色器，水面在 Unity 不透明）；檢查場景把 S 開頭件抬到地面上，
  避免與地面平面穿插。26 件匯入 PASS。
- QA：S01 幾何、匯出、預覽、unity_import PASS；water_hidden_in_previews 標 NOT_APPLICABLE（本件就是水）；ports_on_grid NOT_APPLICABLE。

視覺檢查（實際開圖）
- S01 hero、1.70 m 視角、`routes/stream_test_sheet.png`、Unity 總覽截圖開圖看過。

仍待處理
- S 形版本未做（依指示）；Unity 透明水面著色器、流動捲動腳本未做；正式河床／河岸模型未做。

## 2026-10-29（五）F01 出水口升降堰板、兩塊田串接

狀態：使用者指出參考圖出水口全開會一直漏水，F01 改為可升降的溢流堰；尚未提交、未推送。

已完成
- 出水石槽口底板在堰板處留 4 cm 沉板槽，槽下埋地石匣到 z = -0.17（全降時堰板沉入、板頂齊溝底）。
- 堰板部件 `weir`（板高 22 cm、青銅箍、螺桿）沿兩側木導槽升降；牆頂木橫梁中央是青銅螺母座，手輪部件 `weir_wheel`。
  堰頂 0.10–0.30 m 連續可調（預設 0.28＝保水水位）；`weir` 沿 Z 平移 crest_z − 0.28，手輪每圈 2.5 cm（推定）。
- 水面：`field`（z 依堰頂移動）、`field_low`（堰頂低於 0.125 時改顯示）、`inlet`、`outlet`；state 規則寫在 model_info.json。
- `render_detail.py`：出水口特寫四張（堰頂 0.30／0.28／0.19／0.10），只移動堰板，水面隱藏。
- `field_test` 改為兩塊田串接：上游田溢流 → B02 → 下游田 → B02-V05，7 個接縫實測縫隙 0、重疊 0。
- Unity 25 件匯入 PASS；F01 LOD0 15,272 tris（tri_budget WARNING，推定上限 12,000）。

視覺檢查（實際開圖）
- 四張堰板特寫、`F01_compare.png`、`routes/field_test_sheet.png` 開圖看過。

仍待處理
- 升降與水位連動只寫成資料規則，Unity 端尚未做互動腳本；螺桿全降時頂端藏在螺母座下（外觀可接受，未做伸縮）。

## 2026-10-29（四）F01 灌溉田地＋石槽拼接測試

狀態：依使用者提供的「灌溉田地｜三視圖」（存為 `art/references/qingxi-waterworks-b/F01_irrigated_field_three_view_v001.png`）
建出 F01，並接進石槽路線測試；尚未提交、未推送。溪水模型尚未提供。

已完成
- `pieces_field.py`：F01 灌溉田地，外框 6 × 4 m、田埂頂 0.40 m、5 條田畦（頂 0.34 m）、6 道畦間水溝、上緣分水溝、下緣集水溝。
  - 出入口是標準 U 形石槽口（外寬 60、淨寬 40、高 40、底板 10 cm），入口在原點、出水口在 (0, 4)，可直接接 B 系列。
  - 田畦為一整張高度場（邊緣餘弦加密、圓肩、平面圓角），田埂沿外框以斜接截面掃出、兩半夾住石槽口。
  - 畦溝兩端放低矮深色護石；田埂外坡腳與頂面有碎石、四角與外坡有草叢（新材質 `ww_grass`）。
  - 新貼圖 `ww_field_soil`／`ww_field_soil_n`（暖褐田土＋碎礫點）；田土加濕線頂點色（`wet_line`，只對 F01 生效）。
  - 水面獨立：入口、田內、出口三片（`F01_water.glb`），預覽不顯示。每條田畦有 `SOCKET_bed_1…5`。
- build.py 支援 F 開頭件號；母稿排列依寬度留間距。
- `routes.py` 新增 `field_test`：B01 → B02 → B05（＋B06）→ B02 → F01 → B02 → B02-V05，6 個接縫實測縫隙 0 mm、重疊 0 mm。
- Unity：新增 `ww_field_soil`（專屬法線圖）、`ww_grass` 材質；法線圖改為「有 `<貼圖>_n.png` 就用，否則用石材法線」；
  大件排在網格右側。25 件匯入全部 PASS（三角面一致、材質全部對應）。
- QA：F01 幾何、匯出、預覽、port_overreach、unity_import 皆 PASS；tri_budget WARNING（12,600 > 推定上限 12,000，
  田地面積 24 m²，預算需依場景實測再定）。

視覺檢查（實際開圖）
- `F01_compare.png`、hero、1.70 m 視角、`routes/field_test_sheet.png`、Unity 總覽截圖都開圖看過。

與參考圖的差異（推定設計）
- 俯視寬長比約 1.5，但側視圖畫得比正視長，互相矛盾，以俯視為準定 6 × 4 m。
- 參考圖的分水溝、集水溝比例較窄、田埂較細；為了讓 40 cm 石槽口與溝底同寬，溝寬取 40 cm。
- 參考圖的水流箭頭只以溝的配置表現，水面為靜水、沒有流動動畫。
- 頂部草葉最高到 0.54 m、外框有碎石外凸約 7 mm（x 6.007 m）。

仍待處理
- 等使用者提供溪水模型測試。
- UV 盒狀投影、碰撞體、LODGroup 同其他件。

## 2026-10-29（三）第二批 11 件、三條路線組合

狀態：第二批完成，24 件全部通過 Blender QA 與 Unity 6000.0.85f1 匯入；尚未提交、未推送。

已完成
- 新增 `pieces_b2.py`（11 件，依 Codex 乾燥三視圖建模）：
  - B04-V02 圓缽分流三通：缽半徑 0.30 m、外壁鼓腹弧石，兩出口 (±0.75, 0.75)。
  - B07／B07-V02／B07-V03：修補石鞍、轉角 L 形修補鍵、階梯底板修補塞（陶土墊片、青銅扒釘、木楔）。
  - B08 河床清淤篩、B09 流速指示浮標（含繫繩與木樁）、B10／B10-V02／B10-V03 三種支架、B11 兩輪手推車（含貨物）、B12 完工紀錄碑座（三根路線插銷為獨立子物件）。
- 新材質：`ww_seal`（陶土墊片）、`ww_cloth`（紅旗）、`ww_rope`、`ww_iron`（鏟）。墊片原名 `ww_clay`，
  但 render.py 的 clay 視圖也用這個材質名稱，會被蓋成灰色，因此改名。木紋貼圖整體提亮（第一批同步受影響）。
- 埋地件（B09 木樁、B10 系列柱腳）以 `preview_ground` 指定預覽地面高度，不再看起來懸空。
- 接縫：彎槽外緣在接口差 3–4 mm，`snap_to_ports` 加「推齊」步驟（左牆／右牆／底板分區，只推實體、不推水面、
  不超過接口平面），B03-V02、B03-V04 已推齊。
- FBX 匯出前先在 Blender 三角化：B04-V02 的凹多邊形由 Unity 三角化時少 33 面，改後三角面一致。
- `routes.py`：依接口自動拼接三條路線與支架展示，逐接縫量測左牆／右牆／底板：
  - A 直通村田（restore_channel）、B 繞過育幼區（protect_nursery）、C 先清淤再暫時導流（clear_silt）、supports 展示。
  - 全部接縫實測縫隙 0 mm、重疊 0 mm（`routes.json`）。石塊圓角形成的約 2 cm V 形石縫是刻意設計，不算縫隙。
- `sheets.py`：`batch1_hero_sheet.png`、`batch2_hero_sheet.png`、`routes/<路線>_sheet.png`（件號標籤）。
- Unity：24 件 FBX 全部重新匯入，材質全部對應，三角面一致；總覽截圖改成依包圍盒置中排列。
- QA：幾何、匯出、預覽、port_overreach、unity_import 24/24 PASS；ports_on_grid 13 PASS／11 NOT_APPLICABLE；
  uv_unwrap 24 WARNING；collision_mesh 24 NOT_TESTED。

視覺檢查（實際開圖）
- 第二批 11 件的 `_compare.png`、`batch2_hero_sheet.png`、四張路線總覽、Unity 總覽截圖都開圖看過。

與參考圖的差異（推定設計）
- B04-V02 外寬 150 cm（參考約 140 cm），為讓出口落在 25 cm 格。
- B10-V02 柱子移到槽寬外側，避免穿過石槽。
- 第二批三視圖把長邊畫在「正視」，對照表上對應我們的右視。

仍待處理
- 路線總覽圖 C 的少數標籤互相壓到（B02-V04 被 B02＋B09 蓋住一部分），不影響模型。
- UV 只有盒狀投影；碰撞體未做；Unity 未設 LODGroup；GLB 未在 Unity 測。
- 等使用者提供的農田、溪水模型來測試拼接與擺放。
- Unity 玩法原型、規則測試、伺服器對接文件、錄影。

## 2026-10-29（二）石材細節、逐件對照、Unity 匯入

狀態：第一批 13 件完成第二輪精修並通過 Unity 6000.0.85f1 匯入檢查；尚未提交、未推送。

已完成
- 石材：轉角崩缺（真轉角才切、避開接口）、手鑿邊起伏、凹縫壓暗頂點色、凹縫生苔、整體調暖；
  青銅 (158,110,64)／metallic 0.65／roughness 0.32，木色偏灰。
- 13 件逐張與三視圖並排檢查後修正：
  - B01：加底座線腳、轉角與開口端加高蓋石、轉角水平青銅箍。
  - B02：端柱外凸 1.5 cm、木樁加綁帶（舊紀錄的「端柱齊平」已修）。
  - B02-V02：三層砌、頂層崩塌楔形過渡、中層外凹、+X 牆裂縫加青銅扒釘。
  - B02-V03：基腳往內退 3 cm，接口端不再露出埋地截面（舊紀錄問題已修）。
  - B02-V04、B02-V05：重排；B02-V05 柱箍縮到 0.19 m，不再超出接口面。
  - B03：重做為 R 0.75、方形外牆＋圓角內角、四片底板。
  - B03-V03：對角扶壁肋。
  - B04：重做，低矮分水尖貼後牆。
  - B05：柱改 15 cm、柱座加大，閘板青銅減為邊條＋角片。
- build.py：`snap_to_ports` 把接口平面外 2 cm 內的頂點壓回平面；新增 `port_overreach` 檢查（in／out ≤ 1 mm）。
- Unity：新增 `tools/qingxi-waterworks-b/unity`（6000.0.85f1、Built-in、Linear）。`WaterworksImportCheck.Run` 會依名稱建立共用材質，
  著色器 `Qingxi/StandardVC` 把頂點色乘回凹縫明暗；FBX 重新對應材質、匯入時去掉 `.001` 尾碼。批次模式實跑結果：
  - 13 件三角面與 Blender 完全一致，尺寸以 1 m 為單位，流向為 Unity +Z。
  - 材質全部對應成功，頂點色都在，SOCKET 名稱乾淨。
  - 直線拼接 B02→B02-V02→B05→B02-V04→B02 首尾相接。
  - 截圖：`art/previews/qingxi-waterworks-b/unity_import_all.png`、`unity_import_chain.png`。
- QA（`qa_report.md`）：
  - 幾何、匯出、預覽、port_overreach、unity_import：13/13 PASS。
  - ports_on_grid：12 PASS，B06 為 NOT_APPLICABLE。
  - uv_unwrap：WARNING。
  - collision_mesh：NOT_TESTED。

視覺檢查（實際開圖）
- 13 件全部和 `_compare.png` 三視圖對照過；總覽 `batch1_hero_sheet.png`、Unity 兩張截圖都開圖看過。

仍待處理
- FBX 本身只帶法線貼圖路徑（Blender 節點的底色＋頂點色混合無法寫進 FBX），Unity 端靠名稱對應材質解決；GLB 未在 Unity 測（需 glTFast）。
- UV 只有盒狀投影；碰撞體未做；LOD 未在 Unity 設 LODGroup。
- 第二批：B07–B12、B04-V02、B07×3、B10×3、三條路線組合。
- Unity 玩法原型、規則測試、伺服器對接文件、錄影。

## 2026-10-29（一）第一批外觀重工

- 依三視圖逐件修正 B02-V03、B02-V05、B04、B01、B03-V03；石材改成獨立石塊大圓角＋鎚鑿卵面貼圖。
- 修正 `_cove` 退化面；新增 `qa_report.py`、`asset_spec.md`、本檔。
