# ASSET_MANIFEST｜29 件環境收邊模組（v01 成品）

由 `05_Scripts/write_final_reports.py` 依實際檔案與檢查結果產生。尺寸為匯出網格的實測範圍（含細節；草片可能略超出外側自由邊，但不會越過入口／出口接頭面）。三角面為實測值。設計階段的舊版清單保存在 `history/`。

| 共通 | 內容 |
| --- | --- |
| 單位／座標 | 公尺；Z 向上；+X＝行進方向；+Y＝行進方向左側；地面 Z = 0 |
| 檔案 | `01_Blender/road_edge_modules_v01.blend`、`riverbank_modules_v01.blend`、`bridgehead_modules_v01.blend`（每件一個 Collection）；每件一個 FBX 在 `02_Exports/<RoadEdge/Riverbank/Bridgehead>/` |
| 物件 | `<ID>`（根空物件，含接頭資訊自訂屬性）、`_Terrain_LOD0/1/2`、`_DET_Stones_LOD0`、`_DET_Grass_LOD0`、`_Rocks_LOD0/1`、`_Masonry_LOD0/1/2`（C05）、`_COL` |
| 材質 | 地表 `M_TerrainBlend`（頂點色 Mask 混合）；石 `M_Rock`／`M_Moss`；草片 `M_GrassCard`；貼圖在 `03_Textures/` |

## A 類｜道路不規則收邊（11 件）

| 編號 | 模組 ID | 名稱 | 外形 X×Y (m) | Z 範圍 (m) | LOD0／LOD1／LOD2／COL 三角面 | 預算 | 入口 | 出口 | FBX |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A01 | `SM_RoadEdge_Straight_L_A` | 直線左路緣 | 4.00 × 0.94 | -0.06～0.34 | 406／96／24／24 | 300–2000（在預算內） | ROAD_EDGE_L (0.000, 0.000, 0.000) +0.0° | ROAD_EDGE_L (4.000, 0.000, 0.000) +0.0° | `02_Exports/RoadEdge/SM_RoadEdge_Straight_L_A.fbx`（83 KB） |
| A02 | `SM_RoadEdge_Straight_R_A` | 直線右路緣 | 4.00 × 0.91 | -0.05～0.38 | 406／96／24／24 | 300–2000（在預算內） | ROAD_EDGE_R (0.000, 0.000, 0.000) +0.0° | ROAD_EDGE_R (4.000, 0.000, 0.000) +0.0° | `02_Exports/RoadEdge/SM_RoadEdge_Straight_R_A.fbx`（83 KB） |
| A03 | `SM_RoadEdge_Curve_L_A` | 左彎 15° | 4.54 × 5.07 | -0.09～0.39 | 1,256／384／96／96 | 300–2000（在預算內） | ROAD_3M (0.000, 0.000, 0.000) +0.0° | ROAD_3M (3.954, 0.521, 0.000) +15.0° | `02_Exports/RoadEdge/SM_RoadEdge_Curve_L_A.fbx`（154 KB） |
| A04 | `SM_RoadEdge_Curve_R_A` | 右彎 15° | 4.54 × 5.02 | -0.07～0.47 | 1,256／384／96／96 | 300–2000（在預算內） | ROAD_3M (0.000, 0.000, 0.000) +0.0° | ROAD_3M (3.954, -0.521, 0.000) -15.0° | `02_Exports/RoadEdge/SM_RoadEdge_Curve_R_A.fbx`（154 KB） |
| A05 | `SM_RoadEdge_WideCurve_L_A` | 左彎 30° | 4.94 × 5.37 | -0.05～0.40 | 1,256／384／96／96 | 300–2000（在預算內） | ROAD_3M (0.000, 0.000, 0.000) +0.0° | ROAD_3M (3.820, 1.023, 0.000) +30.0° | `02_Exports/RoadEdge/SM_RoadEdge_WideCurve_L_A.fbx`（154 KB） |
| A06 | `SM_RoadEdge_WideCurve_R_A` | 右彎 30° | 4.94 × 5.31 | -0.09～0.42 | 1,256／384／96／96 | 300–2000（在預算內） | ROAD_3M (0.000, 0.000, 0.000) +0.0° | ROAD_3M (3.820, -1.023, 0.000) -30.0° | `02_Exports/RoadEdge/SM_RoadEdge_WideCurve_R_A.fbx`（153 KB） |
| A07 | `SM_RoadEdge_Slope_A` | 小坡銜接 | 4.00 × 4.93 | -0.01～0.58 | 1,256／384／96／96 | 300–2000（在預算內） | ROAD_3M (0.000, 0.000, 0.000) +0.0° | ROAD_3M (4.000, 0.000, 0.200) +0.0° | `02_Exports/RoadEdge/SM_RoadEdge_Slope_A.fbx`（151 KB） |
| A08 | `SM_RoadEdge_GrassTransition_A` | 泥路轉草地 | 4.00 × 4.74 | -0.07～0.42 | 1,320／384／96／96 | 300–2000（在預算內） | ROAD_3M (0.000, 0.000, 0.000) +0.0° | ROAD_3M / GRASS_PATH (4.000, 0.000, 0.000) +0.0° | `02_Exports/RoadEdge/SM_RoadEdge_GrassTransition_A.fbx`（158 KB） |
| A09 | `SM_RoadEdge_StoneTransition_A` | 泥路轉碎石 | 4.00 × 4.77 | -0.06～0.43 | 1,736／384／96／96 | 300–2000（在預算內） | ROAD_3M (0.000, 0.000, 0.000) +0.0° | ROAD_3M / GRAVEL_PATH (4.000, 0.000, 0.000) +0.0° | `02_Exports/RoadEdge/SM_RoadEdge_StoneTransition_A.fbx`（189 KB） |
| A10 | `SM_RoadEdge_End_A` | 道路終端 | 4.00 × 4.89 | -0.10～0.42 | 1,244／384／96／96 | 300–2000（在預算內） | ROAD_3M (0.000, 0.000, 0.000) +0.0° | （單側封口）  | `02_Exports/RoadEdge/SM_RoadEdge_End_A.fbx`（151 KB） |
| A11 | `SM_RoadEdge_Damaged_A` | 破損路段 | 4.00 × 4.92 | -0.09～0.40 | 1,558／384／96／96 | 300–2000（在預算內） | ROAD_3M (0.000, 0.000, 0.000) +0.0° | ROAD_3M (4.000, 0.000, 0.000) +0.0° | `02_Exports/RoadEdge/SM_RoadEdge_Damaged_A.fbx`（182 KB） |

- **A01 直線左路緣**：4 m 左側收邊帶（+Y），路面 3 m 由測試路芯或其他道路模組提供；泥土與草地自然過渡。　入口可接：A01 TEST_RoadCore_3m ROAD_3M 模組的 +Y 收邊帶；出口可接：A01 TEST_RoadCore_3m ROAD_3M 模組的 +Y 收邊帶
- **A02 直線右路緣**：4 m 右側收邊帶（-Y），與 A01 配對。　入口可接：A02 TEST_RoadCore_3m ROAD_3M 模組的 -Y 收邊帶；出口可接：A02 TEST_RoadCore_3m ROAD_3M 模組的 -Y 收邊帶
- **A03 左彎 15°**：整段 3 m 路面＋兩側收邊，中心線弧長 4 m、左轉 15°，出口位姿依圓弧計算。　入口可接：A03 A04 A05 A06 A07 A11 A01+A02+TEST_RoadCore_3m；出口可接：A03 A04 A05 A06 A07 A08 A09 A10 A11 C01 A01+A02+TEST_RoadCore_3m
- **A04 右彎 15°**：右轉 15°，直接生成（非鏡射），法線與 UV 正確。　入口可接：A03 A04 A05 A06 A07 A11 A01+A02+TEST_RoadCore_3m；出口可接：A03 A04 A05 A06 A07 A08 A09 A10 A11 C01 A01+A02+TEST_RoadCore_3m
- **A05 左彎 30°**：左轉 30°，路面與收邊沿同一圓弧，不扭曲。　入口可接：A03 A04 A05 A06 A07 A11 A01+A02+TEST_RoadCore_3m；出口可接：A03 A04 A05 A06 A07 A08 A09 A10 A11 C01 A01+A02+TEST_RoadCore_3m
- **A06 右彎 30°**：右轉 30°。　入口可接：A03 A04 A05 A06 A07 A11 A01+A02+TEST_RoadCore_3m；出口可接：A03 A04 A05 A06 A07 A08 A09 A10 A11 C01 A01+A02+TEST_RoadCore_3m
- **A07 小坡銜接**：4 m 上坡，出口比入口高 0.20 m；smoothstep 坡形，兩端坡度為 0，最大坡度 7.5%。　入口可接：A03 A04 A05 A06 A07 A11 A01+A02+TEST_RoadCore_3m；出口可接：A03 A04 A05 A06 A07 A08 A09 A10 A11 C01 A01+A02+TEST_RoadCore_3m
- **A08 泥路轉草地**：泥土路面沿行進方向漸變為草地小徑；貼圖遮罩混合＋稀疏可關閉草片。　入口可接：A03 A04 A05 A06 A07 A11 A01+A02+TEST_RoadCore_3m；出口可接：（幾何相容所有 ROAD_3M 入口；材質為草地小徑狀態，本套件尚無同狀態路段）
- **A09 泥路轉碎石**：泥土路面漸變為細碎石路，少量碎石細節；不形成石牆。　入口可接：A03 A04 A05 A06 A07 A11 A01+A02+TEST_RoadCore_3m；出口可接：（幾何相容所有 ROAD_3M 入口；材質為碎石路狀態，本套件尚無同狀態路段）
- **A10 道路終端**：道路自然收尾（半圓收口），只有入口接頭。　入口可接：A03 A04 A05 A06 A07 A11 A01+A02+TEST_RoadCore_3m；出口可接：—
- **A11 破損路段**：內側坑洞、缺角與裂紋，入口出口仍為標準斷面。　入口可接：A03 A04 A05 A06 A07 A11 A01+A02+TEST_RoadCore_3m；出口可接：A03 A04 A05 A06 A07 A08 A09 A10 A11 C01 A01+A02+TEST_RoadCore_3m

## B 類｜河岸自然收邊（10 件）

| 編號 | 模組 ID | 名稱 | 外形 X×Y (m) | Z 範圍 (m) | LOD0／LOD1／LOD2／COL 三角面 | 預算 | 入口 | 出口 | FBX |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B01 | `SM_Riverbank_Straight_A` | 河岸直段 A | 4.00 × 3.09 | -1.00～0.43 | 1,100／384／96／96 | 300–2000（在預算內） | BANK_0_TO_MINUS_0P8 (0.000, 0.000, 0.000) +0.0° | BANK_0_TO_MINUS_0P8 (4.000, 0.000, 0.000) +0.0° | `02_Exports/Riverbank/SM_Riverbank_Straight_A.fbx`（140 KB） |
| B02 | `SM_Riverbank_Straight_B` | 河岸直段 B | 4.00 × 3.16 | -1.00～0.42 | 1,440／384／96／96 | 300–2000（在預算內） | BANK_0_TO_MINUS_0P8 (0.000, 0.000, 0.000) +0.0° | BANK_0_TO_MINUS_0P8 (4.000, 0.000, 0.000) +0.0° | `02_Exports/Riverbank/SM_Riverbank_Straight_B.fbx`（167 KB） |
| B03 | `SM_Riverbank_InnerCorner_A` | 河岸內凹轉角 | 3.65 × 3.55 | -1.00～0.34 | 1,100／384／96／96 | 300–2000（在預算內） | BANK_0_TO_MINUS_0P8 (0.000, 0.000, 0.000) +0.0° | BANK_0_TO_MINUS_0P8 (2.546, -2.546, 0.000) -90.0° | `02_Exports/Riverbank/SM_Riverbank_InnerCorner_A.fbx`（145 KB） |
| B04 | `SM_Riverbank_OuterCorner_A` | 河岸外凸轉角 | 4.55 × 4.55 | -1.00～0.40 | 1,100／384／96／96 | 300–2000（在預算內） | BANK_0_TO_MINUS_0P8 (0.000, 0.000, 0.000) +0.0° | BANK_0_TO_MINUS_0P8 (2.546, 2.546, 0.000) +90.0° | `02_Exports/Riverbank/SM_Riverbank_OuterCorner_A.fbx`（143 KB） |
| B05 | `SM_Riverbank_Slope_A` | 緩坡入水 | 4.00 × 3.08 | -1.00～0.38 | 1,420／544／96／96 | 300–2000（在預算內） | BANK_0_TO_MINUS_0P8 (0.000, 0.000, 0.000) +0.0° | BANK_0_TO_MINUS_0P8 (4.000, 0.000, 0.000) +0.0° | `02_Exports/Riverbank/SM_Riverbank_Slope_A.fbx`（184 KB） |
| B06 | `SM_Riverbank_Steep_A` | 陡岸露岩 | 4.00 × 3.07 | -1.25～0.38 | 1,964／816／96／96 | 300–2000（在預算內） | BANK_0_TO_MINUS_0P8 (0.000, 0.000, 0.000) +0.0° | BANK_0_TO_MINUS_0P8 (4.000, 0.000, 0.000) +0.0° | `02_Exports/Riverbank/SM_Riverbank_Steep_A.fbx`（243 KB） |
| B07 | `SM_Riverbank_RockReinforced_A` | 砌石護岸 | 4.00 × 3.09 | -1.00～0.43 | 3,440／1584／96／96 | 800–4000（在預算內） | BANK_0_TO_MINUS_0P8 (0.000, 0.000, 0.000) +0.0° | BANK_0_TO_MINUS_0P8 (4.000, 0.000, 0.000) +0.0° | `02_Exports/Riverbank/SM_Riverbank_RockReinforced_A.fbx`（476 KB） |
| B08 | `SM_Riverbank_GrassHeavy_A` | 草根濕岸 | 4.00 × 3.23 | -1.00～0.51 | 1,460／384／96／96 | 300–2000（在預算內） | BANK_0_TO_MINUS_0P8 (0.000, 0.000, 0.000) +0.0° | BANK_0_TO_MINUS_0P8 (4.000, 0.000, 0.000) +0.0° | `02_Exports/Riverbank/SM_Riverbank_GrassHeavy_A.fbx`（166 KB） |
| B09 | `SM_Riverbank_Eroded_A` | 沖刷崩岸 | 4.00 × 3.06 | -1.00～0.34 | 1,250／384／96／96 | 300–2000（在預算內） | BANK_0_TO_MINUS_0P8 (0.000, 0.000, 0.000) +0.0° | BANK_0_TO_MINUS_0P8 (4.000, 0.000, 0.000) +0.0° | `02_Exports/Riverbank/SM_Riverbank_Eroded_A.fbx`（152 KB） |
| B10 | `SM_Riverbank_End_A` | 河岸終端 | 4.00 × 3.04 | -1.00～0.36 | 908／384／96／96 | 300–2000（在預算內） | BANK_0_TO_MINUS_0P8 (0.000, 0.000, 0.000) +0.0° | （單側封口）  | `02_Exports/Riverbank/SM_Riverbank_End_A.fbx`（125 KB） |

- **B01 河岸直段 A**：4 m 土坡河岸，岸上 0 m、示意水位 -0.8 m、水下坡腳 -1.0 m；稀疏植被。　入口可接：B01 B02 B03 B04 B05 B06 B07 B08 B09 C02；出口可接：B01 B02 B03 B04 B05 B06 B07 B08 B09 B10 C02
- **B02 河岸直段 B**：與 B01 同接頭，多風化小石、苔蘚與不同侵蝕紋。　入口可接：B01 B02 B03 B04 B05 B06 B07 B08 B09 C02；出口可接：B01 B02 B03 B04 B05 B06 B07 B08 B09 B10 C02
- **B03 河岸內凹轉角**：陸地內凹（水灣）90° 轉角：沿岸線行進時向水側右轉，岸線弧長 4 m。　入口可接：B01 B02 B03 B04 B05 B06 B07 B08 B09 C02；出口可接：B01 B02 B03 B04 B05 B06 B07 B08 B09 B10 C02
- **B04 河岸外凸轉角**：陸地外凸（岬角）90° 轉角：向陸側左轉，岸線弧長 4 m。　入口可接：B01 B02 B03 B04 B05 B06 B07 B08 B09 C02；出口可接：B01 B02 B03 B04 B05 B06 B07 B08 B09 B10 C02
- **B05 緩坡入水**：中段改為寬緩入水坡道（約 19°），兩端回到標準斷面；水面只在測試場景顯示。　入口可接：B01 B02 B03 B04 B05 B06 B07 B08 B09 C02；出口可接：B01 B02 B03 B04 B05 B06 B07 B08 B09 B10 C02
- **B06 陡岸露岩**：中段為陡土岸與面向水側的露岩。　入口可接：B01 B02 B03 B04 B05 B06 B07 B08 B09 C02；出口可接：B01 B02 B03 B04 B05 B06 B07 B08 B09 B10 C02
- **B07 砌石護岸**：岸坡上排列護岸石塊，石塊不越過兩端接頭面。　入口可接：B01 B02 B03 B04 B05 B06 B07 B08 B09 C02；出口可接：B01 B02 B03 B04 B05 B06 B07 B08 B09 B10 C02
- **B08 草根濕岸**：草量多、岸頂有草皮懸邊；草片為可關閉子物件。　入口可接：B01 B02 B03 B04 B05 B06 B07 B08 B09 C02；出口可接：B01 B02 B03 B04 B05 B06 B07 B08 B09 B10 C02
- **B09 沖刷崩岸**：坡面三道沖刷細溝與坡腳崩土，端面高程不變。　入口可接：B01 B02 B03 B04 B05 B06 B07 B08 B09 C02；出口可接：B01 B02 B03 B04 B05 B06 B07 B08 B09 B10 C02
- **B10 河岸終端**：岸高差在 4 m 內平順消失到地面，只有入口接頭。　入口可接：B01 B02 B03 B04 B05 B06 B07 B08 B09 C02；出口可接：—

## C 類｜橋頭與地形交接收邊（8 件）

| 編號 | 模組 ID | 名稱 | 外形 X×Y (m) | Z 範圍 (m) | LOD0／LOD1／LOD2／COL 三角面 | 預算 | 入口 | 出口 | FBX |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C01 | `SM_Bridgehead_RoadTransition_A` | 道路轉橋面 | 2.00 × 4.63 | -0.01～0.43 | 524／192／48／48 | 800–4000（低於建議下限（小件，可接受）） | ROAD_3M (0.000, 0.000, 0.000) +0.0° | BRIDGE_3M (2.000, 0.000, 0.150) +0.0° | `02_Exports/Bridgehead/SM_Bridgehead_RoadTransition_A.fbx`（94 KB） |
| C02 | `SM_Bridgehead_BankTransition_A` | 橋頭兩側岸坡 | 3.04 × 8.00 | -1.00～0.45 | 1,652／672／168／168 | 800–4000（在預算內） | BANK_0_TO_MINUS_0P8 (3.000, -4.000, 0.000) +90.0° | BANK_0_TO_MINUS_0P8 (3.000, 4.000, 0.000) +90.0° | `02_Exports/Bridgehead/SM_Bridgehead_BankTransition_A.fbx`（188 KB） |
| C03 | `SM_Bridgehead_SideTrim_L_A` | 橋頭左側收口 | 2.00 × 1.18 | -0.05～0.43 | 376／48／12／12 | 800–4000（低於建議下限（小件，可接受）） | GROUND_EDGE (0.000, 2.625, 0.000) +0.0° | BRIDGEHEAD_FIELD (2.000, 2.625, 0.000) +0.0° | `02_Exports/Bridgehead/SM_Bridgehead_SideTrim_L_A.fbx`（80 KB） |
| C04 | `SM_Bridgehead_SideTrim_R_A` | 橋頭右側收口 | 2.00 × 1.09 | -0.05～0.45 | 376／48／12／12 | 800–4000（低於建議下限（小件，可接受）） | GROUND_EDGE (0.000, -2.625, 0.000) +0.0° | BRIDGEHEAD_FIELD (2.000, -2.625, 0.000) +0.0° | `02_Exports/Bridgehead/SM_Bridgehead_SideTrim_R_A.fbx`（80 KB） |
| C05 | `SM_Bridgehead_Base_A` | 橋頭石基 | 1.25 × 3.00 | -0.55～-0.05 | 452／120／12／12 | 800–4000（低於建議下限（小件，可接受）） | BRIDGE_SEAT (2.000, 0.000, -0.050) +0.0° | BRIDGEHEAD_FIELD (3.250, 0.000, -0.192) +0.0° | `02_Exports/Bridgehead/SM_Bridgehead_Base_A.fbx`（69 KB） |
| C06 | `SM_Bridgehead_SlopeFix_A` | 接地短坡 | 1.50 × 3.00 | 0.00～0.15 | 348／144／36／36 | 800–4000（低於建議下限（小件，可接受）） | BRIDGE_3M (0.000, 0.000, 0.150) +0.0° | GROUND_3M (1.500, 0.000, 0.000) +0.0° | `02_Exports/Bridgehead/SM_Bridgehead_SlopeFix_A.fbx`（73 KB） |
| C07 | `SM_Bridgehead_CornerCap_A` | 橋頭角隅封邊 | 1.25 × 4.71 | -0.55～0.40 | 796／384／36／36 | 800–4000（低於建議下限（小件，可接受）） | BRIDGEHEAD_FIELD (2.000, 1.875, 0.000) +0.0° | BRIDGEHEAD_FIELD (3.250, 1.875, 0.000) +0.0° | `02_Exports/Bridgehead/SM_Bridgehead_CornerCap_A.fbx`（145 KB） |
| C08 | `SM_Bridgehead_WaterEdge_A` | 橋頭近水沖刷帶 | 1.75 × 4.50 | -1.07～-0.12 | 1,648／624／144／144 | 800–4000（在預算內） | BRIDGEHEAD_FIELD (3.250, 0.000, -0.192) +0.0° | RIVERBED_EDGE (5.000, 0.000, -1.000) +0.0° | `02_Exports/Bridgehead/SM_Bridgehead_WaterEdge_A.fbx`（200 KB） |

- **C01 道路轉橋面**：道路 0 m 以 2 m smoothstep 緩坡升到測試橋面 +0.15 m，最大坡度 11%，無台階。　入口可接：A03 A04 A05 A06 A07 A11 A01+A02+TEST_RoadCore_3m；出口可接：C06 TEST_BridgeDeck_3m 正式橋梁（橋面 +0.15、寬 3 m）
- **C02 橋頭兩側岸坡**：橋頭兩側陸地到河岸土坡的過渡（左右兩片），外端接 B 類標準河岸斷面。　入口可接：B01 B02 B03 B04 B05 B06 B07 B08 B09 C02；出口可接：B01 B02 B03 B04 B05 B06 B07 B08 B09 B10 C02
- **C03 橋頭左側收口**：左側（+Y）泥土草坡與散石，貼著 C01 外緣由坡道高度降回地面，避開通行區。　入口可接：—；出口可接：C07 C08
- **C04 橋頭右側收口**：右側（-Y）對應收口，與 C03 成對。　入口可接：—；出口可接：C07 C08
- **C05 橋頭石基**：橋頭下方簡潔石基（頂面 -0.05 m 承托 0.20 m 厚的測試橋面），不含橋梁主跨。　入口可接：—；出口可接：C07 C08
- **C06 接地短坡**：1.5 m 短坡，把 +0.15 m 橋面高度平順降到地面 0 m；可單獨用於簡易橋端或高差修飾。　入口可接：C01 TEST_BridgeDeck_3m 正式橋梁（橋面 +0.15、寬 3 m）；出口可接：—
- **C07 橋頭角隅封邊**：石基兩側角隅的地形與封邊石，消除土坡與石基之間的三角縫（左右兩片）。　入口可接：C03 C04 C05 C07；出口可接：C07 C08
- **C08 橋頭近水沖刷帶**：石基前方到河床的濕泥碎石沖刷帶，河側邊緣與 B 類坡腳同為 -1.0 m。　入口可接：C03 C04 C05 C07；出口可接：—

## D 類｜後續新增（不在原 29 件內）

| 編號 | 模組 ID | 名稱 | 外形 X×Y (m) | LOD0／LOD1／LOD2／COL 三角面 | 放置 | FBX |
| --- | --- | --- | --- | --- | --- | --- |
| D02 | `SM_Bridge_Timber_A` | 木造梁橋 | 10.00 × 3.20 | 1,112／248／48／36 | 橋頭座標系平移 (2, 0, +0.15)；接兩座相距 14 m 的橋頭 | `02_Exports/Bridge/SM_Bridge_Timber_A.fbx` |

- **D02 木造梁橋**：木造梁橋：3 m 寬木板橋面、4 根主梁、兩側木欄杆、河中央一座木排架（3 根圓木樁＋帽梁＋交叉斜撐）；跨距 10 m，橋面與 C01 坡道頂齊平，主梁兩端削口擱在兩岸 C05 石基上。材質 M_Timber／M_Bark／M_EndGrain。檔案 `01_Blender/timber_bridge_v01.blend`。
- D01 獨木橋（`01_Blender/log_bridge_v01.blend`、`02_Exports/Bridge/SM_Bridge_Log_A.fbx`）：先前做的單根原木橋，保留為可選件。

## 狀態

全部 29 件：已建模（LOD0/1/2＋COL）；接頭與細節自動檢查通過；FBX 已匯出並通過 Blender 回匯檢查；11 張預覽已檢查未裁切；未在 Unity/Unreal 驗證。

## 測試輔助（不屬於 29 件，不在模組 FBX 內）

- `02_Exports/_TestHelpers/TEST_RoadCore_3m.fbx`、`TEST_BridgeDeck_3m.fbx`、`TEST_ScaleCube_1m.fbx`：引擎內拼接測試與 1 m 尺度核對用。
