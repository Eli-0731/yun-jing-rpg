| 項目 | 內容 |
|---|---|
| 誰做的 | A（Johnnnny0823） |
| 工作包 | docs/execution/2026-11-08/A-80h-mountain-city.md（第二部分：山城街道小件） |
| ID | ST01–ST06 |
| 分支／PR | art/a-1108-st-street-furniture ／ #100 |
| 版本 | v001 |
| 狀態 | Exported；Imported：見「驗收紀錄」的 Unity 6000.3.28f1 檢查；Visually Verified：預覽圖；In-game Verified：未驗 |
| 素材來源 | 原創。建模腳本 `art/source/mountain-street-a/build_st.py`，沿用 MC01（#80）的建模函式與共用貼圖；三視圖用 Codex CLI 生成，存 `art/references/ST01`–`ST06/` |

# ST01–ST06 山城街道小件

讓 MC01 拼出來的街有人在生活、做生意：燈柱、跨街燈籠、排水石槽、石長椅、店門布幌、臨崖欄杆，另附一段 20 m 街道樣張。全部空白不寫字。

![20 m 街道樣張](../../previews/mountain-street-a/assembly/st_street_overview.png)

## 各件做法（括號是選用的三視圖）

- **ST01 山城石燈柱**（option 2）：
  - 方形花崗石柱，四面都有框邊，框裡是一串五朵雲紋浮雕；燈台下有雲紋托座。
  - 燈台上是四根石柱圍成的小燈亭，開口有木格框，裡面一個紙燈箱（`Glow`，就是燈芯的光）。
  - 小石瓦頂有瓦壟和翹角，頂上寶珠。燈亭楣石用較暗的石材，代表燻黑。
  - 底座兩層，缺一角、有苔。
  - 和 MC01 DT01（銅柱、六角銅燈）、青溪 G01 村口石燈都不同：方石柱、雲紋、規整。
- **ST02 跨街燈籠串**（option 2）：
  - 一條麻繩掛五盞油紙燈籠，紅、米白交替；第 3、5 盞褪色，每盞頂下一圈燻黑。
  - 燈籠有深色木頂蓋和底座、紅絲流蘇；繩上兩處紅絲纏繩。
  - 兩端是 S 形鐵勾：上面的開口勾掛屋簷下的環或釘，下面的鐵環穿繩。
  - 繩垂約跨度的 3 %。
  - **長度**：
    - 規格的 8 m 之外，另交 6 m（四盞）和 4 m（三盞）兩種，給比較窄的街。
    - 其他長度用 `build_st.py -- --span <公尺>` 重建，盞數和間距會跟著調整。
    - 沒有用 Unity 直接拉長：拉長會把燈籠一起壓扁。
- **ST03 排水石槽**（option 3）：
  - 照選圖做成放在街面上、高 0.3 m 的石槽：底板加兩側壓頂石。
  - 石塊長短不一，臨街那側的槽沿磨得比較圓。
  - 槽底一層較暗的濕石面，接縫和牆腳有小草；直段有一個鐵鋦釘。
  - **三件**：
    - `ST03_S` 4 m 直段；
    - `ST03_C` 0.5 m 轉角（從 −X 進、往 +Y 出）；
    - `ST03_D` 4 m 跌水段。
  - **跌水段**：
    - 照 MC01 SB04 石階：11 階、每階降 0.182 m、踏面 0.364 m，總共降 2.0 m。
    - 每階出口有一片出水石舌，下面是錯縫砌的石牆。
    - 上端接上層街的直段，下端落到下層街的直段。
- **ST04 山城石長椅**（option 4）：
  - 一整塊厚石板，略出挑，放在兩個石墩上；石墩有小基座和切角框邊。
  - 坐面用另一張小貼圖上比較亮、比較光滑的花崗石，在兩個常坐的位置磨出淺凹。
  - 前緣缺一角，腳邊有苔。
  - 比 RK09 觀景石凳正式。
- **ST05 空白布幌 ×3**（option 2）：
  - 藍（`ST05_A`）、赭（`ST05_B`）、灰（`ST05_C`）各一。
  - 短木桿兩端圓頭，三角繩圈掛起。
  - 粗棉布有直向的柔和皺褶，上段曬褪色，每面兩塊補丁。
  - 下擺一排 17 條打結的流蘇。
  - **完全空白**，沒有字、沒有圖案。
  - 和 MC01 DT02（燕尾小旗掛在橫臂上）不同：這是掛在店門柱前的長條布。
- **ST06 臨崖欄杆**（option 1）：
  - 可拼的三件：
    - `ST06_S` 2 m 欄杆片（柱中心到柱中心，不含柱）；
    - `ST06_C` 轉角／中間柱；
    - `ST06_E` 端柱（蓮苞頂，外側一塊小抱鼓形石撐）。
  - 欄杆片是深色杉木：寬的上橫木（手摸得比較亮）、下橫木離地 0.1 m 排水、九根直欄。
  - 上橫木一端綁麻繩，接頭有深色鐵 L 件和釘頭。
  - 石柱柱腳較暗、有苔。

## 原點與接法

| 件 | 原點 | 接法 |
|---|---|---|
| ST01、ST04、ST06_C／_E | 底面中心，z＝0，−Y 為正面 | 直接放在街面；ST04 的坐面朝 −Y，高 0.48 m |
| ST02 | 兩個鐵勾頂端連線的中點（z＝0） | `Socket_HookA`／`Socket_HookB` 就是勾頂，掛在屋簷下同高的兩點，燈串往下垂約 0.8–1.0 m。20 m 樣張掛在 RF02 前簷下（簷下約 +0.25 m） |
| ST03 | 底面中心，z＝0，槽沿 0.3 m | +Y 邊（y＝+0.25）貼 MC01 石基正面；直段兩端 x＝±2，可接成一排 |
| ST05 | 流蘇最下端，z＝0 | `Socket_Hang` 在繩圈上，掛在店門柱的釘上；樣張掛在店面地板上 2.6 m |
| ST06_S | 欄杆片中心，柱中心在 x＝±1 | 每端立一根 ST06_C 或 ST06_E；適合 MC01 CP01 懸挑平台邊或臨崖街邊 |

- MC01 沒有屋簷插槽（`Socket_*`），所以 ST02 自帶兩個勾頂插槽，掛點寫在樣張的 `st-street-assembly.json`。
- 碰撞：
  - 燈籠串、布幌是掛件，沒有碰撞。
  - 石槽的碰撞是底板加兩側牆，槽底可以走進去。
  - 跌水段每一階一組碰撞。
  - 欄杆片的碰撞高 1.1 m，擋得住人。

## 數字

| ID | 尺寸 W×D×H（m） | 規格上限 | LOD0 / LOD1 / LOD2 三角面 | 物件 | 材質 | 貼圖 | 碰撞 |
|---|---|---|---|---|---|---|---|
| ST01 山城石燈柱 | 0.598 × 0.597 × 2.4 | 0.6 × 0.6 × 2.4 | 14,330 / 6,626 / 2,004 | 3 | 2 | trim 2048 | 3 boxes |
| ST02 燈籠串 8 m | 7.993 × 0.34 × 0.973 | 8.0 × 0.4 × 1.2 | 6,980 / 3,368 / 1,010 | 2 | 2 | ST 1024 | 無（掛件） |
| ST02-6M 燈籠串 6 m | 5.993 × 0.34 × 0.89 | 同上 | 5,964 / 2,836 / 850 | 2 | 2 | ST 1024 | 無（掛件） |
| ST02-4M 燈籠串 4 m | 3.993 × 0.34 × 0.835 | 同上 | 4,948 / 2,308 / 692 | 2 | 2 | ST 1024 | 無（掛件） |
| ST03-S 石槽直段 | 3.999 × 0.5 × 0.3 | 4.0 × 0.5 × 0.3 | 2,678 / 1,185 / 356 | 2 | 2 | trim 2048 + ST 1024 | 3 boxes |
| ST03-C 石槽轉角 | 0.498 × 0.498 × 0.297 | 同上 | 398 / 174 / 60 | 2 | 1 | trim 2048 | 4 boxes |
| ST03-D 石槽跌水段 | 3.999 × 0.5 × 2.297 | 4.0 × 0.5 ×（跟石階降 2.0 m） | 8,762 / 3,975 / 1,192 | 2 | 1 | trim 2048 | 33 boxes |
| ST04 石長椅 | 1.798 × 0.479 × 0.479 | 1.8 × 0.5 × 0.5 | 8,285 / 3,938 / 1,188 | 2 | 2 | trim 2048 + ST 1024 | 3 boxes |
| ST05-A／B／C 布幌 | 0.59 × 0.07 × 1.76–1.77 | 0.6 × 0.1 × 1.8 | 3,152 / 1,576 / 472 | 1 | 2 | trim 2048 + ST 1024 | 無（掛件） |
| ST06-S 欄杆片 | 1.854 × 0.193 × 0.931（柱距 2.0） | 2.0 × 0.2 × 1.1 | 3,748 / 1,874 / 562 | 1 | 2 | trim 2048 + ST 1024 | 1 box |
| ST06-C 轉角／中間柱 | 0.198 × 0.198 × 1.095 | 同上 | 362 / 162 / 56 | 2 | 1 | trim 2048 | 1 box |
| ST06-E 端柱 | 0.473 × 0.198 × 1.1 | 同上 | 683 / 313 / 101 | 2 | 1 | trim 2048 | 2 boxes |

- **超過規格的一處**：跌水段高 2.3 m，因為要跟 SB04 石階一起降 2.0 m。槽的斷面仍是 0.5 × 0.3 m。
- **物件**：主體一個；`Glow`（燈紙）和 `Detail_Moss`（苔、草，可整組關掉）各自獨立。
- **材質**：
  - `M_MountainStreet_Trim`／`M_MountainStreet_Glow`：MC01 共用的 2048 Trim Sheet，在 `art/textures/mountain-street-houses-a`。石、木、銅鐵、ST01 燈紙都用它，可以和街屋合批。
  - `M_StreetFurniture`／`M_StreetFurniture_Glow`：這包新做的一張 1024 小貼圖 `art/textures/mountain-street-a/T_StreetFurniture_*.png`，256 px/m。用在 Trim Sheet 沒有的顏色：三色布、紅與米白燈紙、磨亮的坐面石、鐵件、麻繩、紅絲。
  - 每件最多 2 個材質。
- **LOD**：LOD0 是完整建模；LOD1 ≤ 50 %，LOD2 ≤ 15 %。
- **minTier**：全部 low。
- **交付格式**：只交 FBX，內含 LOD0/1/2、`_Collision`、插槽 empty。不帶切線，Unity 匯入時用 MikkTSpace 算。
- **效能**：不寫 FPS；手機未實測。

## 20 m 街道樣張（`st-street-assembly.json`）

- 街長 x＝−10 … +10，寬 5 m。北側是 MC01 店屋，南側臨崖。
- **北側店屋**：
  - 四間店屋：SB05＋SF01／SF02，兩間有 HM 住家層；屋頂都是 RF02。
  - 東端是 SB04 石階，上到 2 m 平台上的一間 SB01＋SF03＋RF03。
- **北側小件**：
  - 店前一排 ST03 石槽；石階旁是跌水段，落到街面接一個轉角。
  - 三間店的門柱各掛一條布幌。
  - 兩間二樓店的前簷之間掛一串 8 m 燈籠。
- **南側**：
  - 臨崖一整排 ST06：兩端端柱、中間 9 根柱、10 片欄杆。
  - 兩根 ST01 燈柱、兩張 ST04 長椅（背對懸崖、面向街）。
- 五個 1.75 m 人形尺。
- **檔案**：
  - 零件寫 `id`、`pos`、`rotZ`。
  - 換到 Unity 的軸向和 MC01 `b-street-assembly.json` 相同。Unity 檢查用 ST06_E 量出軸向，再照這份檔案擺一次。

![街上 1.7 m 人眼](../../previews/mountain-street-a/assembly/st_street_eye_1p7m.png)

## 驗收紀錄

- **Blender 資產 QA**（blender-asset-qa `qa_check`，game profile，LOD0 逐物件掃，z-fighting／懸空都有跑）：
  - 14 件主體 errors＝0。
  - 燈紙＋主體、苔＋主體合併檢查，懸空＝0。
  - 結果存 `art/source/mountain-street-a/qa_all.json`。
  - 苔單獨掃描會報「懸空」，因為每叢苔本來就是分開的小片，要和主體合併看。
- **FBX 回匯**：14 件尺寸和建模時相同（誤差 0）。
- **Unity 6000.3.28f1**（`apps/game/Assets/YunJing/Editor/StreetFurnitureVerify.cs`）：結果見 `art/previews/mountain-street-a/unity/report.txt`。
- **修過的問題**：
  - 疊起來的石塊只有面貼面，鑿面雜訊把上面那塊往下壓，留出縫而被判懸空；改成都互相重疊 6–8 mm。
  - 雲紋浮雕和雲尾背面同一平面。
  - 框邊、木格四根條的端面和側面重疊閃爍。
  - 鐵勾的環和勾同一平面。
  - 欄杆鐵件兩片同高。
  - 布幌厚度邊的 UV 是零面積。
  - 石槽的苔、草長出尺寸上限。

## 怎麼重跑

```
python tools/mountain-city-a/make_prompts_st.py
python tools/mountain-city-a/gen_threeviews.py --prompts prompts_st.json ST01 ST02 ST03 ST04 ST05 ST06
blender -b --factory-startup -P art/source/mountain-street-a/build_st.py -- all
blender -b --factory-startup -P art/source/mountain-street-a/qa_st.py -- <絕對路徑 out.json> ST01 ST02 ...
blender -b --factory-startup -P art/source/mountain-street-a/render_st.py -- --out <repo 絕對路徑>/art/previews/mountain-street-a [--clay|--wire|--lod 1] ST01 ST02 ...
blender -b --factory-startup -P art/source/mountain-street-a/assemble_st.py -- [--clay]
python art/source/mountain-street-a/sheets_st.py ST01 ST02 ...
Unity -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.StreetFurnitureVerify.Run -logFile <log>
```

## 預覽

`art/previews/mountain-street-a/`：

- **每件**：
  - 3/4、側、正、俯視（含 1.75 m 人形尺；掛件掛在 2.6 m）；
  - 灰模、線框、LOD1；
  - `*_ref_vs_model.jpg`：參考圖對模型；
  - `*_LOD0_vs_LOD1.jpg`。
- `assembly/`：20 m 樣張，有材質和灰模兩版，五個角度：
  - 鳥瞰；
  - 1.7 m 人眼；
  - 臨崖側；
  - 石階跌水；
  - 店面布幌與燈籠。
- `unity/`：Unity 截圖與報告。

## 工時

約 3 小時（11/11，含讀包、三視圖生成與選圖、建模、QA 修正、樣張、Unity 檢查），由 Claude Code 執行。
