# 青溪水工 B — 資產規格（asset_spec）

作者：蘇奕安 Josh（joshsu54@gmail.com），Claude Code 協作建模。
參考：`art/references/qingxi-waterworks-b/` 的乾燥三視圖（DRY v002／v003），只用無水版本。

## 共用標準（B01–B05、B04-V02 拼接件）

| 項目 | 數值 |
|---|---|
| 單位 | 1 Blender 單位 = 1 m；FBX 以公尺匯出並套用單位縮放 |
| 座標 | Blender +Z 向上；glTF +Y 向上；入口接口在原點，水流朝 +Y |
| 外寬／淨寬 | 60 cm／40 cm（牆厚 10 cm） |
| 總高／底板 | 40 cm／10 cm |
| 水面基準 | z = 0.28 m（水面為獨立 `<件號>_water.glb`，預覽一律不顯示） |
| 拼接格 | 互拼的 in／out 接口中心與方向落在 25 cm 格、方向只取 ±X／±Y |
| 接口面 | 接口截面平整、不抖動、不長苔，兩件相接無縫無重疊 |
| 掛點 | `SOCKET_<名稱>` 空物件（如 B05 `SOCKET_wheel_mount` 對準 B06） |
| 活動件 | 子物件：B05 `gate`（closed／open +0.32 m）、B06 `wheel`（繞 X 軸） |

## 造型與材質

- 砌石（v002，2026-10-30 依核心組審查改回切石）：每塊石頭是獨立封閉網格，牆依層錯縫切成 20–40 cm 的石塊。
  倒角約為最小邊的 12%（0.8–1.3 cm、2 段），面保持平整；相鄰石塊的倒角形成 V 形石縫。倒角區只加 ±2.5 mm 起伏。
  物件套用加權法線（Weighted Normal，隨 FBX／GLB 輸出），平面受光平整、倒角圓滑。
  （r2 首版是 22%／2.6 cm／3 段，牆面圓鼓像軟墊。）
- 凹縫明暗：依頂點法線偏離原始平面的角度壓暗頂點色（最多 55%），存在 `Col` 頂點色，glTF 匯入引擎後同樣生效。
- 貼圖（程序生成、固定亂數種子，可重現）：`ww_stone`（1024²，一張 = 1 m × 1 m：10–40 cm 的大斑與水漬、
  點鑿麻點、斜向鑿痕、細砂粒；不再用 3 cm 的卵面小格）、`ww_stone_moss`、`ww_stone_n` 法線、`ww_wood`、`ww_bronze`、`ww_soil`。
  石材 UV 為盒狀投影 1 次／m，每塊石頭取固定亂數位移，相鄰石塊不重複同一片紋理；其他材質 2.4 次／m。
- 青銅（v002）：暗褐氧化銅底、少量綠鏽；鉚釘改成圓頭（Ø2.4–2.8 cm，一半埋進銅片）。
- PBR：石 roughness 0.84；木 0.80；青銅 metallic 0.9／roughness 0.30；土 0.95；墊片純色。
- 青苔：長在凹縫、低處與朝上面，接口附近收斂；部分低位石塊換成 `ww_stone_moss`。
- 崩缺：只在真轉角（≥3 條硬邊）切 1.2–2.2 cm 斜面，避開接口 3 cm 與底面；切面略提亮。
- 接口貼齊：`build.py` 的 `snap_to_ports` 把接口平面外 2 cm 內的頂點（含水面）壓回平面，QA 的 port_overreach 檢查 ≤ 1 mm；
  再把接口截面分左牆／右牆／底板三區，差 0.3–8 mm 未到平面的區域，把 5 cm 內的實體頂點推齊到平面（不推水面）。
- 第二批非拼接件（B07–B12）：原點在底面中心、正面 -Y。B10 系列地面在 z = 0，`SOCKET_trough` 為 1 m 槽入口原點的位置。
- 材質另有 `ww_seal`（陶土墊片，避開 render.py clay 視圖的 `ww_clay` 名稱）、`ww_cloth`、`ww_rope`、`ww_iron`（metallic 0.7／roughness 0.55）。
- 埋地件以 `preview_ground` 指定預覽地面高度（寫入物件屬性 `preview_ground_z`）。
- FBX 匯出前加暫時的 Triangulate 修改器（BEAUTY），確保 Unity 三角面與 Blender 一致。

## 地形件（F01 灌溉田地）

- 件號 F 開頭，定義在 `pieces_field.py`；接口與石槽套件相同（入口在原點、水流 +Y、出口落在 25 cm 格）。
- F01：外框 6 × 4 m、田埂頂 0.40、溝底 0.10（= 石槽底板）、田畦頂 0.34、水面 0.28；材質 `ww_field_soil`、`ww_stone`、
  `ww_stone_moss`、`ww_grass`。`SOCKET_bed_1…5` 在各田畦頂中心。
- 出水口疊板閘：4 片橫木板（部件 `weir`）平時升到頂卡滿（crest 0.30，不出水），放水時降下；沿 Z 平移 crest_z − 0.28（crest 0.10–0.30），手輪 `weir_wheel` 每圈 2.5 cm；
  水面 `field` 的 z 設為 crest_z，低於 0.125 改顯示 `field_low`；`inlet`、`outlet` 常駐。埋地石匣最低 z = -0.17。
- 特寫：`blender -b <母稿> --python art/source/qingxi-waterworks-b/render_detail.py -- --out <絕對路徑>`

## 地形件（S01 溪流，demo 直段）

- 水面本身即模型（材質 `ww_stream`），原點上游端中線、z = 0 為平均水面、水流 +Y；長 12.03 m、寬約 1.8 m、厚 0–6 cm。
- UV：U 橫越、V 沿流向（0.6／m）。`SOCKET_kit_B01` 為 B01 原點位置（含 Z 旋轉、z = −0.28）。剖面資料在 model_info 的 `extra.profile`。

## 地形件（S02 河床與河岸，demo 直段）

- 與 S01 同原點、同變換疊放（參考圖為 S 形，依 demo 需求改直段）。河床底 z = −0.30，岸頂約 +0.49（相對水面）。
- 材質 `ww_riverbed`（砂礫）、`ww_field_soil`（河岸，色調略灰）、`ww_stone`、`ww_grass`；右岸 B01 缺口半寬 0.78 m。

## 水面（Unity）

- 石槽、田溝、田面水面輸出 `<件號>_water.fbx`，放在 Unity `Models/Water/`，掛成本體子物件（局部原點 0）。
- 著色器 `Qingxi/WaterFlow`：兩層水色＋漣漪法線沿 `_FlowDir` 以 `_Speed1`／`_Speed2` 捲動、半透明（premul）。
  UV 慣例：帶狀水面 U 橫跨 0–1、V＝沿流距離 m（往下游增加）；S01 V＝m × 0.6；田面積水 UV＝平面 m。
- 同一支著色器另含 GrabPass 折射、深度淡出（淺處較透明）、岸邊泡沫；攝影機需開深度貼圖（`WaterDepthCamera`）。
  只適用 Built-in 管線。
- F01 疊板閘：`FieldWeirController.SetCrest(z)`（0.10–0.30，預設 0.30 卡滿）同時移動疊板、轉手輪、調整田面水位，並切換低水位顯示。
- B05 閘門：`GateController.open`（預設關＝閘板在槽底）。
- 水路：`WaterNetwork` 依路線順序傳遞水；關閘時下游乾，疊板卡滿時 F01 出水口不出水。
- Demo 按鍵：G 開關閘門、↑↓ 升降疊板、R 全部退乾。
- Demo：`Unity.exe -batchmode -projectPath tools/qingxi-waterworks-b/unity -executeMethod WaterworksDemo.Run -quit [-qxBuild <exe>]`；
  播放器加 `-qxOut <資料夾>` 會量效能、錄影格並寫 `demo_report.json` 後自動結束。

## LOD 與預算

- LOD0 完整幾何；LOD1 = 50%、LOD2 = 15%（Decimate collapse），與 LOD0 放在同一個 GLB／FBX。
  LOD0 保留原名（閘板、疊板等程式以名稱查找），簡化網格命名 `<物件>_LOD1`／`_LOD2`，掛在對應的 LOD0 部件底下（會動的部件 LOD 一起動）。
  Unity 由 `WaterworksModelPostprocessor` 在根物件建 LODGroup（門檻 0.30／0.10／0.012 螢幕高度，待手機實測調整）；
  因為 LOD0 沒有 `_LOD0` 尾碼，Unity 不會自動建 LODGroup，接進主專案時要帶這支後處理或自行建。
  LOD0／1／2 並排預覽：`<件號>_lods.png`（`render_lods.py` 讀匯出的 GLB 產生）。各件數字見 `qa_report.md`。
- 單件 LOD0 預算暫定 12,000 三角面（推定值，待 Unity 場景實測調整）。

## 交付檔

- 母稿：`art/source/qingxi-waterworks-b/qingxi-waterworks-b.blend`（貼圖打包），由 `build.py` 重建。
- 匯出：`art/exports/qingxi-waterworks-b/<件號>/`：`.glb`、`_water.glb`、`.fbx`、`_water.fbx`、`model_info.json`（LOD 在主檔內）。
- 預覽：`art/previews/qingxi-waterworks-b/<件號>/`：四向正交、前後 3/4（中性光）、clay、線框、hero（風格光）、
  1.70 m 視角（含 1.75 m 比例人台）、`_compare.png`（三視圖對照表）。

## Unity（6000.0.85f1）

- 專案：`tools/qingxi-waterworks-b/unity`（Built-in、Linear）。模型複製到 `Assets/QingxiWaterworksB/Models`，貼圖在 `Textures`。
- FBX 只帶法線貼圖路徑；`WaterworksImportCheck.Run` 依 FBX 材質名稱（ww_stone…）對應到 `Materials/` 共用材質，
  著色器 `Qingxi/StandardVC` 乘上頂點色（Col）。`WaterworksModelPostprocessor` 匯入時去掉 Blender 的 `.001` 尾碼。
- 座標：Blender (x, y, z) → Unity (x, z, y)，流向 Unity +Z，入口在模型原點。擺放矩陣用 P·M·P，再乘上 FBX 根物件的匯入姿態（有些件的根物件帶 x 軸旋轉）。
- 批次指令：`Unity.exe -batchmode -projectPath tools/qingxi-waterworks-b/unity -executeMethod WaterworksImportCheck.Run -quit`，
  輸出 `art/source/qingxi-waterworks-b/unity_import_report.json`、截圖與 `unity_water_frames/` 流動影格。模型更新後要重新複製 FBX 再跑。

## 重建指令（repo 根目錄）

```
blender -b --python art/source/qingxi-waterworks-b/build.py -- [件號 ...]
blender -b art/source/qingxi-waterworks-b/qingxi-waterworks-b.blend --python art/source/qingxi-waterworks-b/render.py -- --out <絕對路徑>
uv run --no-project --with pillow python art/source/qingxi-waterworks-b/compose.py <件號> <預覽根目錄>
python art/source/qingxi-waterworks-b/qa_report.py
blender -b art/source/qingxi-waterworks-b/qingxi-waterworks-b.blend --python art/source/qingxi-waterworks-b/routes.py
uv run --no-project --with pillow python art/source/qingxi-waterworks-b/sheets.py
```

`render.py` 的 `--out` 請給絕對路徑：相對路徑會被 Blender 以 .blend 所在資料夾解析。

## 已知限制

- UV 為盒狀投影，未做不重疊展開，不能烘焙 AO／法線。
- 碰撞體、導航尚未做（QA 標 NOT_TESTED）；Unity 只驗證了匯入、材質與渲染。GLB 未在 Unity 測試。
- B04 外寬 100 cm（參考 120 cm），為對齊拼接格的推定設計；B05 柱寬 15 cm 依比例推定；B03 轉彎半徑 0.75 m。
- B04-V02 外寬 150 cm（參考約 140 cm）以對齊拼接格；B10-V02 柱子移到槽寬外側。
