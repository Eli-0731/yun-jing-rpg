# README_Integration｜匯入 Unity／Unreal 的注意事項

本套件只在 Blender 5.2.3 內製作與驗證，FBX 也只做過 Blender 回匯檢查（見 `QA_Report.md`）。下列做法是匯入引擎時的建議與已知限制，**尚未在 Unity／Unreal 實測**。

## 1. 檔案與命名

| 位置 | 內容 |
| --- | --- |
| `02_Exports/RoadEdge/`、`Riverbank/`、`Bridgehead/` | 每件一個 FBX，檔名就是模組 ID，例如 `SM_RoadEdge_Curve_L_A.fbx` |
| `02_Exports/_TestHelpers/` | `TEST_ScaleCube_1m`、`TEST_RoadCore_3m`、`TEST_BridgeDeck_3m`：只用來在引擎內核對尺度與拼接，**不是正式資產** |
| `03_Textures/` | 共用貼圖（1024×1024，可無縫平鋪，1 張＝2 m × 2 m） |
| `06_Reports/CONNECTOR_SPEC.json` | 每件的接頭位置、方向、類型、可接對象與實測誤差 |

FBX 內的物件：

| 物件 | 用途 |
| --- | --- |
| `<ID>` | 根空物件＝Pivot。自訂屬性 `kit_connectors`（JSON）記錄接頭；FBX 以 user properties 帶出 |
| `<ID>_Terrain_LOD0/1/2` | 地表。LOD1 約為 LOD0 的 50%，LOD2 約 12–25% |
| `<ID>_DET_Stones_LOD0`、`_DET_Grass_LOD0` | 可關閉的細節（小石、草片）。只有 LOD0，手機可整組隱藏 |
| `<ID>_Rocks_LOD0/1` | 較大的石塊；LOD1 為減面 50% |
| `<ID>_SodLip_LOD0`、`_DET_Cracks_LOD0` | B08 草皮唇邊、A11 裂紋貼片 |
| `SM_Bridgehead_Base_A_Masonry_LOD0/1/2` | C05 石基（倒角切石／方石／單一方塊） |
| `<ID>_COL` | 碰撞代理（LOD2 地表或簡化方塊）。只包通行面與主要地形，不含小石頭 |

## 2. 尺度、軸向、Pivot

- 建模單位公尺；Blender 內 Z 向上，模組行進方向 +X，+Y 為行進方向左側。
- FBX 設定（`05_Scripts/export_fbx.py`）：Forward -Z、Up Y、Apply Scalings「FBX All」、Apply Transform（bake space transform）、平滑群組 Face、切線空間、頂點色 Linear、自訂屬性。這是 Blender→Unity 常用的組合，目的是匯入後縮放 1、沒有 -90° 的修正旋轉。
- **Unity**：Model 匯入設定建議 Scale Factor 1、Convert Units 開、Import Normals「Import」、Vertex Colors 保留、Generate Colliders 關（改用 `_COL`）。名稱結尾 `_LOD0/_LOD1/_LOD2` 會讓 Unity 自動建立 LOD Group。
- **Unreal**：Import Uniform Scale 1、Convert Scene 開、Normal Import Method「Import Normals」、Vertex Color Import「Replace」。LOD 需在 Static Mesh Editor 依名稱手動指定；`_COL` 可改名為 `UCX_<網格名>` 讓 Unreal 自動當成碰撞，或在編輯器內設定為簡單碰撞。
- 第一次匯入請先放 `TEST_ScaleCube_1m.fbx` 核對：它應該剛好 1 m。
- Pivot：A、B 類在入口接頭中心 (0, 0, 0)；C 類（C06 除外）共用同一個橋頭座標系，C01–C05、C07、C08 用同一個變換擺放就會組成完整橋頭；C06 的 Pivot 在高側邊緣下方地面。

## 3. 怎麼拼接

- 接頭定義在 `CONNECTOR_SPEC.json`：`location_m` 是模組座標中的接頭中心，`heading_deg` 是穿過接頭的行進方向（從 +X 逆時針）。
- 把 B 接在 A 後面：`T_B = T_A × 平移(A 出口位置) × 繞 Z 旋轉(A 出口方向)`。每件的入口就是自己的原點、方向 0°。
- 道路完整斷面 `ROAD_3M` 左右對稱；河岸 `BANK_0_TO_MINUS_0P8` 陸地永遠在行進方向左側。
- A08（草地小徑）、A09（碎石路）的出口幾何仍是 `ROAD_3M`，但材質是另一種路面狀態，接一般泥路時會有材質換線。
- 引擎內建議用 `kit_connectors` 屬性做吸附（snap）。若手動擺放，Grid snap 1 m、旋轉 snap 15° 可以對上所有直段與彎段的出口。

## 4. 材質重建（重要）

Blender 的節點材質**不會**自動變成引擎材質。貼圖都已烘好，引擎內需重建：

| 材質槽 | 貼圖 | 用在 |
| --- | --- | --- |
| `M_DrySoil`、`M_WetSoil`、`M_Grass`、`M_Moss`、`M_Rock`、`M_PathGravel` | `T_<名稱>_BaseColor.png`（sRGB）、`_Roughness.png`（線性，R 通道）、`_Normal.png`（線性，OpenGL／Y+ 切線空間） | 石塊、砌石、草皮唇邊、裂紋 |
| `M_TerrainBlend` | 以上六組＋`T_BlendNoise.png` | 所有 `_Terrain_LOD*` |
| `M_GrassCard` | `T_GrassCard_BaseColor.png`（RGBA，Alpha 裁切） | `_DET_Grass_LOD0`，雙面、Alpha Clip 0.5 |

- Unreal 使用 DirectX 法線（Y−），匯入法線貼圖時勾選 Flip Green Channel。Unity 使用 OpenGL（Y+），直接使用。
- UV：1 個 UV 單位＝2 m。A、B 類 U 沿行進方向，出口 U 為整數，所以相鄰模組貼圖連續。

`M_TerrainBlend` 的混合方式（頂點色 `Mask` 為線性資料）：

```
color = DrySoil
for layer, channel in [(PathGravel, B), (WetSoil, R), (Grass, G), (Moss, A)]:
    n = dot(BlendNoise(uv + offset_layer).rgb, weights_layer)
    f = smoothstep(lo, hi, Mask[channel] + amp * n)
    color = lerp(color, layer, f)          # roughness、normal 同樣 lerp
```

| 層 | offset（UV） | weights (R, G, B) | amp | lo | hi |
| --- | --- | --- | --- | --- | --- |
| PathGravel | (0.37, 0.61) | (0.5, 0.0, 0.5) | 0.70 | 0.78 | 0.92 |
| WetSoil | (0.74, 1.22) | (0.4, 0.6, 0.0) | 0.55 | 0.55 | 0.97 |
| Grass | (1.11, 1.83) | (0.5, 0.2, 0.3) | 0.70 | 0.78 | 0.92 |
| Moss | (1.48, 2.44) | (0.6, 0.0, 0.4) | 0.70 | 0.80 | 0.95 |

數值來源：`05_Scripts/kit_blender.py` 的 `BLEND`、`terrain_material()`。

## 5. 碰撞與通行

- 用 `_COL`，不要用 LOD0 或細節物件產生碰撞。河岸不需要每顆石頭的碰撞。
- 路面寬 3 m、C01 緩坡 2 m 升 0.15 m（約 7.5%），C06 1.5 m 降 0.15 m。這些都在 CharacterMovement 預設可走坡度內，但**尚未在引擎內實測**。
- 測試水位 -0.80 m；水面不在模組內，請在引擎內另放水體。可用 `03_Textures/T_Water_Normal.png`（可平鋪的順流波紋法線，V 方向沿水流，1 張＝2 m）做水面法線；展示場景的做法見 `05_Scripts/render_showcase.py` 的 `water_material()`：折射水面＋很低的體積吸收（清澈見底，深處偏青綠）＋水深小於約 3.5 cm 處的白沫；河床卵石與水底波光見 `riverbed_material()`。引擎內可用深度淡化（depth fade）做同樣的近岸透明、深處上色。

## 6. 效能

- LOD0 三角面每件實測值見 `ASSET_MANIFEST.md`（道路約 400–1,750、河岸約 900–3,700、橋頭約 350–1,650）。
- 大量重複時共用同一組材質，開 GPU Instancing（Unity）或使用 Instanced Static Mesh／HISM（Unreal）。
- 手機：可隱藏 `_DET_*` 子物件；LOD2 已不含細節。

## 7. 木橋（D02，後續新增）

- `02_Exports/Bridge/SM_Bridge_Timber_A.fbx`：Pivot 在入口端橋面頂中心；放進橋頭座標系時平移 (2, 0, +0.15)，跨到對岸轉 180° 的橋頭（兩橋頭座標原點相距 14 m）。
- 物件：`_LOD0`（橋面板、主梁、欄杆、木排架）、`_LOD1`（整片橋面＋兩根主梁＋簡化欄杆與橋墩）、`_LOD2`（方塊組）、`_COL`（橋面＋兩側欄杆牆，防止角色掉落）。
- 材質：`M_Timber`（`T_Timber_*`）、`M_Bark`（`T_Bark_*`，圓木樁）、`M_EndGrain`（`T_EndGrain_*`，鋸斷面；這組貼圖以 UV 中心為年輪中心，不可平鋪）。
- 另有 D01 獨木橋 `SM_Bridge_Log_A.fbx`，放置方式相同，行走面寬 0.33–0.39 m。

## 8. 不在本套件內

- 永久水面、主世界場景／Prefab／Level 的修改。本套件只交付獨立模組。
