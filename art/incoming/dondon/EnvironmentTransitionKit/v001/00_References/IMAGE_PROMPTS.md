# 參考圖生圖提示詞

本工作階段**沒有**可用的圖像生成工具，所以 `00_References/` 中的 REF 圖是由 Blender 實際渲染模組，再用 Pillow 標註尺寸與接頭；數字以 `05_Scripts/kit_spec.py` 為準。以下提示詞供日後用生圖工具產生概念圖。依任務書規定，生成的概念圖**只作視覺參考，不可當作施工尺寸**。

共同限制：原創半寫實東方仙俠村落／林地；只畫模組，不畫人物、兔子、古樹、完整村莊或正式橋樑；淺灰或白色乾淨背景；各模組分開排列。

## 主提示詞（繁體中文，任務書 4.2）

請為一款原創半寫實 3D 東方仙俠村落遊戲，設計「可重複拼接的獨立環境收邊模組庫」。內容限定：不規則自然泥土道路邊、河岸土石草坡、木橋或石橋橋頭與地面交接的收邊模組；不要做整個村莊、不要正式橋樑本體、不要人物、不要兔子、不要古樹。各模組獨立隔開排列，淺灰或白色乾淨背景，專業遊戲美術建模參考板，半寫實但乾淨且自然，泥土、岩塊、草、青苔、溼土的材質細節恰當。每件提供 45 度斜視圖、正確正投影頂視圖、標準化接縫、接頭方向箭頭、ID、尺寸（公尺）與材質說明。道路寬 3m，直線段長 4m，左右各 0.75m 道路收邊；河岸上端高程 0m、下端設計水位 -0.8m；橋面測試高程 +0.15m。所有模組自然的破損、泥土侵蝕、石塊細節只能發生在拼接段內側，連接邊必須能無縫對接。風格統一、輪廓清楚、適合 Blender 遊戲建模。

## REF_A_Road_Edge_Sheet

Game environment modelling reference sheet, semi-realistic original Eastern xianxia village style. Eleven separate modular dirt-road edge pieces laid out in a numbered grid (A01-A11) on a clean light grey background, each shown as a 45-degree three-quarter view with a small orthographic top view beside it. A01 left road verge strip 4 m long, 0.75 m wide; A02 matching right strip; A03/A04 15-degree left and right road curves; A05/A06 30-degree curves; A07 gentle 4 m slope rising 0.2 m; A08 dirt road fading into a grass path; A09 dirt road fading into fine gravel; A10 rounded natural road end; A11 damaged road with potholes and chipped edges kept inside the piece. Road surface 3 m wide, compacted warm grey-brown earth, fine gravel, grass roots and a little moss at the verge, subtle trampled marks. Straight clean connection edges with direction arrows at entry and exit. No characters, no animals, no trees, no buildings, no bridge. Clean, natural, not cartoonish, not noisy photogrammetry.

## REF_B_Riverbank_Sheet

Game environment modelling reference sheet, semi-realistic Eastern xianxia riverside. Ten separate modular riverbank pieces in a numbered grid (B01-B10) on a clean light grey background, 45-degree view plus top view each. Each piece is 4 m long; land side flat at 0 m on the left, earth slope down to a test water line at -0.8 m on the right, labelled "LAND" and "WATER". B01 plain earth bank with sparse grass; B02 same with weathered small stones and moss; B03 inner (concave land, bay) 90-degree corner; B04 outer (convex headland) 90-degree corner; B05 wide gentle slope into the water; B06 steep earth bank with exposed rock facing the water; B07 bank reinforced with natural laid stones; B08 wet bank with heavy grass and an overhanging turf lip; B09 eroded bank with small gullies and slumped soil; B10 bank end where the height difference fades into flat ground. Warm grey-brown soil, dark wet soil near the water line, cool grey rock, moss green grass. Only a simple flat test water plane. No people, rabbits, trees or full river scene.

## REF_C_Bridgehead_Sheet

Game environment modelling reference sheet for bridgehead edge pieces, semi-realistic Eastern xianxia village. Eight separate modules in a numbered grid (C01-C08) on a clean light grey background, 45-degree view plus top view each, with a plain grey placeholder deck block marked "TEST DECK +0.15 m" — do not draw a finished bridge. C01 2 m dirt road ramp rising smoothly from 0 to +0.15 m; C02 land and earth bank transition on both sides of the bridgehead; C03 left side trim of earth, grass and scattered stones; C04 matching right side trim; C05 simple low stone foundation under the deck end; C06 short 1.5 m ramp from +0.15 m down to the ground; C07 small corner caps of earth and edging stones closing the gap between soil and stone base; C08 wet mud and gravel scour band in front of the stone base reaching the river toe. Mark road, deck and bank interfaces with arrows. No complete bridge, no people, no animals, no trees.

## REF_D_Orthographic_Construction

Orthographic construction drawing for game modules, white background, technical line drawing with light shading. Representative modules A01 road verge strip, A03 15-degree road curve, B01 straight riverbank and C01 bridgehead road ramp, each shown as true orthographic top, front and side views with dimension lines in metres: road width 3.00 m, verge band 0.75 m, segment length 4.00 m, curve arc length 4.00 m, bank top 0.00 m, water level -0.80 m, toe -1.00 m, ramp length 2.00 m, deck height +0.15 m. No perspective distortion, consistent line weights, labels in English.

## REF_E_Connector_Engineering

Engineering diagram of modular connectors for a game environment kit. Cross-section profiles: ROAD_3M section (3.00 m surface plus 0.75 m verge bands with a 4 cm hump), BANK section (land 1.00 m, bank line, smooth slope through water level -0.80 m to toe -1.00 m), BRIDGE ramp profile (0 to +0.15 m over 2.00 m). Top views: straight segment entry (0,0,0) exit (4,0,0); 15-degree and 30-degree curves with computed exit positions and rotated exit arrows; 90-degree bank corners; bridgehead plan with zones C01-C08 and the test deck. Assembly arrows between modules, coordinate axes +X forward, +Y left, Z up. Clean vector style, white background, thin black lines, cyan connectors.

## REF_F_Materials

Material reference board with six square PBR material swatches and spheres: dry soil (warm grey-brown), wet mud (dark brown, glossy patches), rock (cool grey with cracks), moss (green cushions), grass (moss green with dry blades), trampled path with fine gravel. Under each swatch note "Base Color / Normal / Roughness" and the colour palette chips. Neutral studio lighting, clean light grey background, semi-realistic hand-tuned look, not cartoon, not noisy scan.
