# ASSET_MANIFEST｜29 件環境收邊模組

依 `05_Scripts/kit_spec.py` 產生的設計階段清單。尺寸為地表網格範圍（細節前，模組座標）；三角面數為 LOD0 地表格點估算，細節物件另計。「可相接」列出接頭類型與路面狀態都相同的模組代碼。目前狀態：**設計三視圖完成，尚未建模**。

## A. 道路不規則收邊（11）

| 編號 | 模組 ID | 名稱 | 外形 X×Y (m) | Z 範圍 (m) | 入口 | 出口 | 入口可接 | 出口可接 | LOD0 地表三角面 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A01 | `SM_RoadEdge_Straight_L_A` | 直線左路緣 | 4.00 × 0.75 | 0.00～0.04 | ROAD_EDGE_L (0.000, 0.000, 0.000) +0.0° | ROAD_EDGE_L (4.000, 0.000, 0.000) +0.0° | A01 TEST_RoadCore_3m ROAD_3M 模組的 +Y 收邊帶 | A01 TEST_RoadCore_3m ROAD_3M 模組的 +Y 收邊帶 | 192 |
| A02 | `SM_RoadEdge_Straight_R_A` | 直線右路緣 | 4.00 × 0.75 | 0.00～0.04 | ROAD_EDGE_R (0.000, 0.000, 0.000) +0.0° | ROAD_EDGE_R (4.000, 0.000, 0.000) +0.0° | A02 TEST_RoadCore_3m ROAD_3M 模組的 -Y 收邊帶 | A02 TEST_RoadCore_3m ROAD_3M 模組的 -Y 收邊帶 | 192 |
| A03 | `SM_RoadEdge_Curve_L_A` | 左彎 15° | 4.54 × 4.94 | 0.00～0.04 | ROAD_3M (0.000, 0.000, 0.000) +0.0° | ROAD_3M (3.954, 0.521, 0.000) +15.0° | A03 A04 A05 A06 A07 A11 A01+A02+TEST_RoadCore_3m | A03 A04 A05 A06 A07 A08 A09 A10 A11 C01 A01+A02+TEST_RoadCore_3m | 768 |
| A04 | `SM_RoadEdge_Curve_R_A` | 右彎 15° | 4.54 × 4.94 | 0.00～0.04 | ROAD_3M (0.000, 0.000, 0.000) +0.0° | ROAD_3M (3.954, -0.521, 0.000) -15.0° | A03 A04 A05 A06 A07 A11 A01+A02+TEST_RoadCore_3m | A03 A04 A05 A06 A07 A08 A09 A10 A11 C01 A01+A02+TEST_RoadCore_3m | 768 |
| A05 | `SM_RoadEdge_WideCurve_L_A` | 左彎 30° | 4.94 × 5.22 | 0.00～0.04 | ROAD_3M (0.000, 0.000, 0.000) +0.0° | ROAD_3M (3.820, 1.023, 0.000) +30.0° | A03 A04 A05 A06 A07 A11 A01+A02+TEST_RoadCore_3m | A03 A04 A05 A06 A07 A08 A09 A10 A11 C01 A01+A02+TEST_RoadCore_3m | 768 |
| A06 | `SM_RoadEdge_WideCurve_R_A` | 右彎 30° | 4.94 × 5.22 | 0.00～0.04 | ROAD_3M (0.000, 0.000, 0.000) +0.0° | ROAD_3M (3.820, -1.023, 0.000) -30.0° | A03 A04 A05 A06 A07 A11 A01+A02+TEST_RoadCore_3m | A03 A04 A05 A06 A07 A08 A09 A10 A11 C01 A01+A02+TEST_RoadCore_3m | 768 |
| A07 | `SM_RoadEdge_Slope_A` | 小坡銜接 | 4.00 × 4.50 | 0.00～0.24 | ROAD_3M (0.000, 0.000, 0.000) +0.0° | ROAD_3M (4.000, 0.000, 0.200) +0.0° | A03 A04 A05 A06 A07 A11 A01+A02+TEST_RoadCore_3m | A03 A04 A05 A06 A07 A08 A09 A10 A11 C01 A01+A02+TEST_RoadCore_3m | 768 |
| A08 | `SM_RoadEdge_GrassTransition_A` | 泥路轉草地 | 4.00 × 4.50 | 0.00～0.04 | ROAD_3M (0.000, 0.000, 0.000) +0.0° | ROAD_3M / GRASS_PATH (4.000, 0.000, 0.000) +0.0° | A03 A04 A05 A06 A07 A11 A01+A02+TEST_RoadCore_3m | （幾何相容所有 ROAD_3M 入口；材質為草地小徑狀態，本套件尚無同狀態路段） | 768 |
| A09 | `SM_RoadEdge_StoneTransition_A` | 泥路轉碎石 | 4.00 × 4.50 | 0.00～0.04 | ROAD_3M (0.000, 0.000, 0.000) +0.0° | ROAD_3M / GRAVEL_PATH (4.000, 0.000, 0.000) +0.0° | A03 A04 A05 A06 A07 A11 A01+A02+TEST_RoadCore_3m | （幾何相容所有 ROAD_3M 入口；材質為碎石路狀態，本套件尚無同狀態路段） | 768 |
| A10 | `SM_RoadEdge_End_A` | 道路終端 | 4.00 × 4.50 | 0.00～0.04 | ROAD_3M (0.000, 0.000, 0.000) +0.0° | （單側封口）  | A03 A04 A05 A06 A07 A11 A01+A02+TEST_RoadCore_3m | — | 768 |
| A11 | `SM_RoadEdge_Damaged_A` | 破損路段 | 4.00 × 4.50 | -0.04～0.04 | ROAD_3M (0.000, 0.000, 0.000) +0.0° | ROAD_3M (4.000, 0.000, 0.000) +0.0° | A03 A04 A05 A06 A07 A11 A01+A02+TEST_RoadCore_3m | A03 A04 A05 A06 A07 A08 A09 A10 A11 C01 A01+A02+TEST_RoadCore_3m | 768 |

- **A01 直線左路緣**：4 m 左側收邊帶（+Y），路面 3 m 由測試路芯或其他道路模組提供；泥土與草地自然過渡。　內部接縫：CoreSeam→TEST_RoadCore_3m (or the surface of another road module)
- **A02 直線右路緣**：4 m 右側收邊帶（-Y），與 A01 配對。　內部接縫：CoreSeam→TEST_RoadCore_3m (or the surface of another road module)
- **A03 左彎 15°**：整段 3 m 路面＋兩側收邊，中心線弧長 4 m、左轉 15°，出口位姿依圓弧計算。
- **A04 右彎 15°**：右轉 15°，直接生成（非鏡射），法線與 UV 正確。
- **A05 左彎 30°**：左轉 30°，路面與收邊沿同一圓弧，不扭曲。
- **A06 右彎 30°**：右轉 30°。
- **A07 小坡銜接**：4 m 上坡，出口比入口高 0.20 m；smoothstep 坡形，兩端坡度為 0，最大坡度 7.5%。
- **A08 泥路轉草地**：泥土路面沿行進方向漸變為草地小徑；貼圖遮罩混合＋稀疏可關閉草片。
- **A09 泥路轉碎石**：泥土路面漸變為細碎石路，少量碎石細節；不形成石牆。
- **A10 道路終端**：道路自然收尾（半圓收口），只有入口接頭。
- **A11 破損路段**：內側坑洞、缺角與裂紋，入口出口仍為標準斷面。

## B. 河岸自然收邊（10）

| 編號 | 模組 ID | 名稱 | 外形 X×Y (m) | Z 範圍 (m) | 入口 | 出口 | 入口可接 | 出口可接 | LOD0 地表三角面 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B01 | `SM_Riverbank_Straight_A` | 河岸直段 A | 4.00 × 3.00 | -1.00～0.00 | BANK_0_TO_MINUS_0P8 (0.000, 0.000, 0.000) +0.0° | BANK_0_TO_MINUS_0P8 (4.000, 0.000, 0.000) +0.0° | B01 B02 B03 B04 B05 B06 B07 B08 B09 C02 | B01 B02 B03 B04 B05 B06 B07 B08 B09 B10 C02 | 768 |
| B02 | `SM_Riverbank_Straight_B` | 河岸直段 B | 4.00 × 3.00 | -1.00～0.00 | BANK_0_TO_MINUS_0P8 (0.000, 0.000, 0.000) +0.0° | BANK_0_TO_MINUS_0P8 (4.000, 0.000, 0.000) +0.0° | B01 B02 B03 B04 B05 B06 B07 B08 B09 C02 | B01 B02 B03 B04 B05 B06 B07 B08 B09 B10 C02 | 768 |
| B03 | `SM_Riverbank_InnerCorner_A` | 河岸內凹轉角 | 3.55 × 3.55 | -1.00～0.00 | BANK_0_TO_MINUS_0P8 (0.000, 0.000, 0.000) +0.0° | BANK_0_TO_MINUS_0P8 (2.546, -2.546, 0.000) -90.0° | B01 B02 B03 B04 B05 B06 B07 B08 B09 C02 | B01 B02 B03 B04 B05 B06 B07 B08 B09 B10 C02 | 768 |
| B04 | `SM_Riverbank_OuterCorner_A` | 河岸外凸轉角 | 4.55 × 4.55 | -1.00～0.00 | BANK_0_TO_MINUS_0P8 (0.000, 0.000, 0.000) +0.0° | BANK_0_TO_MINUS_0P8 (2.546, 2.546, 0.000) +90.0° | B01 B02 B03 B04 B05 B06 B07 B08 B09 C02 | B01 B02 B03 B04 B05 B06 B07 B08 B09 B10 C02 | 768 |
| B05 | `SM_Riverbank_Slope_A` | 緩坡入水 | 4.00 × 3.00 | -1.00～0.00 | BANK_0_TO_MINUS_0P8 (0.000, 0.000, 0.000) +0.0° | BANK_0_TO_MINUS_0P8 (4.000, 0.000, 0.000) +0.0° | B01 B02 B03 B04 B05 B06 B07 B08 B09 C02 | B01 B02 B03 B04 B05 B06 B07 B08 B09 B10 C02 | 768 |
| B06 | `SM_Riverbank_Steep_A` | 陡岸露岩 | 4.00 × 3.00 | -1.00～0.00 | BANK_0_TO_MINUS_0P8 (0.000, 0.000, 0.000) +0.0° | BANK_0_TO_MINUS_0P8 (4.000, 0.000, 0.000) +0.0° | B01 B02 B03 B04 B05 B06 B07 B08 B09 C02 | B01 B02 B03 B04 B05 B06 B07 B08 B09 B10 C02 | 768 |
| B07 | `SM_Riverbank_RockReinforced_A` | 砌石護岸 | 4.00 × 3.00 | -1.00～0.00 | BANK_0_TO_MINUS_0P8 (0.000, 0.000, 0.000) +0.0° | BANK_0_TO_MINUS_0P8 (4.000, 0.000, 0.000) +0.0° | B01 B02 B03 B04 B05 B06 B07 B08 B09 C02 | B01 B02 B03 B04 B05 B06 B07 B08 B09 B10 C02 | 768 |
| B08 | `SM_Riverbank_GrassHeavy_A` | 草根濕岸 | 4.00 × 3.00 | -1.00～0.00 | BANK_0_TO_MINUS_0P8 (0.000, 0.000, 0.000) +0.0° | BANK_0_TO_MINUS_0P8 (4.000, 0.000, 0.000) +0.0° | B01 B02 B03 B04 B05 B06 B07 B08 B09 C02 | B01 B02 B03 B04 B05 B06 B07 B08 B09 B10 C02 | 768 |
| B09 | `SM_Riverbank_Eroded_A` | 沖刷崩岸 | 4.00 × 3.00 | -1.00～0.00 | BANK_0_TO_MINUS_0P8 (0.000, 0.000, 0.000) +0.0° | BANK_0_TO_MINUS_0P8 (4.000, 0.000, 0.000) +0.0° | B01 B02 B03 B04 B05 B06 B07 B08 B09 C02 | B01 B02 B03 B04 B05 B06 B07 B08 B09 B10 C02 | 768 |
| B10 | `SM_Riverbank_End_A` | 河岸終端 | 4.00 × 3.00 | -1.00～0.00 | BANK_0_TO_MINUS_0P8 (0.000, 0.000, 0.000) +0.0° | （單側封口）  | B01 B02 B03 B04 B05 B06 B07 B08 B09 C02 | — | 768 |

- **B01 河岸直段 A**：4 m 土坡河岸，岸上 0 m、示意水位 -0.8 m、水下坡腳 -1.0 m；稀疏植被。
- **B02 河岸直段 B**：與 B01 同接頭，多風化小石、苔蘚與不同侵蝕紋。
- **B03 河岸內凹轉角**：陸地內凹（水灣）90° 轉角：沿岸線行進時向水側右轉，岸線弧長 4 m。
- **B04 河岸外凸轉角**：陸地外凸（岬角）90° 轉角：向陸側左轉，岸線弧長 4 m。
- **B05 緩坡入水**：中段改為寬緩入水坡道（約 19°），兩端回到標準斷面；水面只在測試場景顯示。
- **B06 陡岸露岩**：中段為陡土岸與面向水側的露岩。
- **B07 砌石護岸**：岸坡上排列護岸石塊，石塊不越過兩端接頭面。
- **B08 草根濕岸**：草量多、岸頂有草皮懸邊；草片為可關閉子物件。
- **B09 沖刷崩岸**：坡面三道沖刷細溝與坡腳崩土，端面高程不變。
- **B10 河岸終端**：岸高差在 4 m 內平順消失到地面，只有入口接頭。

## C. 橋頭與地形交接收邊（8）

| 編號 | 模組 ID | 名稱 | 外形 X×Y (m) | Z 範圍 (m) | 入口 | 出口 | 入口可接 | 出口可接 | LOD0 地表三角面 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C01 | `SM_Bridgehead_RoadTransition_A` | 道路轉橋面 | 2.00 × 4.50 | 0.00～0.19 | ROAD_3M (0.000, 0.000, 0.000) +0.0° | BRIDGE_3M (2.000, 0.000, 0.150) +0.0° | A03 A04 A05 A06 A07 A11 A01+A02+TEST_RoadCore_3m | C06 TEST_BridgeDeck_3m 正式橋梁（橋面 +0.15、寬 3 m） | 384 |
| C02 | `SM_Bridgehead_BankTransition_A` | 橋頭兩側岸坡 | 3.00 × 8.00 | -1.00～0.15 | BANK_0_TO_MINUS_0P8 (3.000, -4.000, 0.000) +90.0° | BANK_0_TO_MINUS_0P8 (3.000, 4.000, 0.000) +90.0° | B01 B02 B03 B04 B05 B06 B07 B08 B09 C02 | B01 B02 B03 B04 B05 B06 B07 B08 B09 B10 C02 | 1344 |
| C03 | `SM_Bridgehead_SideTrim_L_A` | 橋頭左側收口 | 2.00 × 0.75 | 0.00～0.15 | GROUND_EDGE (0.000, 2.625, 0.000) +0.0° | BRIDGEHEAD_FIELD (2.000, 2.625, 0.000) +0.0° | — | C07 C08 | 96 |
| C04 | `SM_Bridgehead_SideTrim_R_A` | 橋頭右側收口 | 2.00 × 0.75 | 0.00～0.15 | GROUND_EDGE (0.000, -2.625, 0.000) +0.0° | BRIDGEHEAD_FIELD (2.000, -2.625, 0.000) +0.0° | — | C07 C08 | 96 |
| C05 | `SM_Bridgehead_Base_A` | 橋頭石基 | 1.25 × 3.00 | -0.55～-0.05 | BRIDGE_SEAT (2.000, 0.000, -0.050) +0.0° | BRIDGEHEAD_FIELD (3.250, 0.000, -0.192) +0.0° | — | C07 C08 | 600–1400（砌石） |
| C06 | `SM_Bridgehead_SlopeFix_A` | 接地短坡 | 1.50 × 3.00 | 0.00～0.15 | BRIDGE_3M (0.000, 0.000, 0.150) +0.0° | GROUND_3M (1.500, 0.000, 0.000) +0.0° | C01 TEST_BridgeDeck_3m 正式橋梁（橋面 +0.15、寬 3 m） | — | 288 |
| C07 | `SM_Bridgehead_CornerCap_A` | 橋頭角隅封邊 | 1.25 × 4.50 | -0.19～0.19 | BRIDGEHEAD_FIELD (2.000, 1.875, 0.000) +0.0° | BRIDGEHEAD_FIELD (3.250, 1.875, 0.000) +0.0° | C03 C04 C05 C07 | C07 C08 | 240 |
| C08 | `SM_Bridgehead_WaterEdge_A` | 橋頭近水沖刷帶 | 1.75 × 4.50 | -1.05～-0.12 | BRIDGEHEAD_FIELD (3.250, 0.000, -0.192) +0.0° | RIVERBED_EDGE (5.000, 0.000, -1.000) +0.0° | C03 C04 C05 C07 | — | 1008 |

- **C01 道路轉橋面**：道路 0 m 以 2 m smoothstep 緩坡升到測試橋面 +0.15 m，最大坡度 11%，無台階。　內部接縫：SideSeam_L→SM_Bridgehead_SideTrim_L_A SideSeam_R→SM_Bridgehead_SideTrim_R_A CornerSeam→SM_Bridgehead_CornerCap_A
- **C02 橋頭兩側岸坡**：橋頭兩側陸地到河岸土坡的過渡（左右兩片），外端接 B 類標準河岸斷面。　內部接縫：TrimSeam_L→SM_Bridgehead_SideTrim_L_A InnerSeam_L→SM_Bridgehead_CornerCap_A / SM_Bridgehead_WaterEdge_A TrimSeam_R→SM_Bridgehead_SideTrim_R_A InnerSeam_R→SM_Bridgehead_CornerCap_A / SM_Bridgehead_WaterEdge_A
- **C03 橋頭左側收口**：左側（+Y）泥土草坡與散石，貼著 C01 外緣由坡道高度降回地面，避開通行區。　內部接縫：RoadSeam→SM_Bridgehead_RoadTransition_A
- **C04 橋頭右側收口**：右側（-Y）對應收口，與 C03 成對。　內部接縫：RoadSeam→SM_Bridgehead_RoadTransition_A
- **C05 橋頭石基**：橋頭下方簡潔石基（頂面 -0.05 m 承托 0.20 m 厚的測試橋面），不含橋梁主跨。
- **C06 接地短坡**：1.5 m 短坡，把 +0.15 m 橋面高度平順降到地面 0 m；可單獨用於簡易橋端或高差修飾。
- **C07 橋頭角隅封邊**：石基兩側角隅的地形與封邊石，消除土坡與石基之間的三角縫（左右兩片）。　內部接縫：BankSeam_L→SM_Bridgehead_BankTransition_A BankSeam_R→SM_Bridgehead_BankTransition_A
- **C08 橋頭近水沖刷帶**：石基前方到河床的濕泥碎石沖刷帶，河側邊緣與 B 類坡腳同為 -1.0 m。　內部接縫：BankSeam_L→SM_Bridgehead_BankTransition_A BankSeam_R→SM_Bridgehead_BankTransition_A

## 測試物件（不屬於 29 件、不匯出）

- `TEST_RoadCore_3m`：4 m × 3 m 平面路芯，Z = 0，用來測試 A01＋A02。
- `TEST_BridgeDeck_3m`：寬 3 m、頂 +0.15 m、厚 0.20 m 的佔位橋面，放在 `COL_TEST_Only`。
- `TEST_Water_-0.8`：示意水面 Z = -0.80 m，只在測試場景。
- `TEST_ScaleCube_1m`：1 m 尺度方塊。
