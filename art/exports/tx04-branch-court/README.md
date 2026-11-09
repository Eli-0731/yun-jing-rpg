| 項目 | 內容 |
|---|---|
| 誰做的 | A（Johnnnny0823） |
| 工作包 | docs/execution/2026-11-05/A-48h-mountain-city-architecture.md（TX04；併入 docs/execution/2026-11-08/A-80h-mountain-city.md 第一部分） |
| ID | TX04-GATE、WALL-ST、WALL-CO、WALL-DO、HALL、SIDE、PAVE、STEPS（全套 8 件）＋分院組裝 |
| 分支／PR | art/a-1105-tx04-branch-court ／ z1nnz/chengtian#90 |
| 版本 | v003（全套；#90 第一、二輪審查修改都在內） |
| 狀態 | Exported、Imported（Unity 6000.0.82f1 匯入檢查，見「驗收紀錄」）；In-game Verified：未驗 |
| 素材來源 | 原創。建模腳本 `art/source/tx04-branch-court/build_tx04.py`，沿用 MC01（PR #80 已合併）的建模函式與共用貼圖；白灰牆貼圖由 `gen_wall_tex.py` 程序生成；三視圖用 Codex CLI 生成，存 `art/references/TX04-*/` |

# TX04 太玄分院模組

8 件模組都在 4 m 格上，可以拼出一座分院：院門、直牆、角牆、門邊牆、正堂、廂房、院鋪地、石階。組裝範例在 `tx04-academy-assembly.json`（Blender 座標），Blender 和 Unity 都照這份擺。

## 審查修改紀錄

**第一輪（v002，樣品）**：尺度、朱漆換色、插槽位置都過了。

- **朱漆柱不一致**：直牆端柱改成深色杉木。朱漆只放在門扇、匾框和額枋下緣一條細邊。
- **白灰牆像木板**：新增 TX04 專用白灰牆貼圖 `T_TX04_Wall_*`，1024 px 對應 4 × 4 m（256 px/m）。
  - 貼圖內容：三種尺度的不規則斑駁、補灰、剝落點，以及長短、粗細、傾斜各不相同的雨痕。
  - 牆頂對齊貼圖頂端。
  - 底色取共用灰泥條的平均色。MC01 的 Trim Sheet 沒有改。
- **門扇底部亮線**：門扇下緣伸進門檻、上緣伸進門頭各 5 mm。

**第二輪（v003，隨全套一起改）**：

- **門邊亮線**：院門、正堂的朱漆門扇後面加了深色背板（`*_doorback`），門扇兩側和中縫看進去都是深色。廂房的木門和所有直櫺窗後面也有背板。
- **屋頂太毛**：所有瓦件（瓦面、筒瓦、瓦當、脊）改用 `M_TX04_Roof` 材質，貼圖和共用 Trim Sheet 相同，只是法線強度 0.5。瓦面細雜紋減半，一壟一壟的大形靠模型，不受影響。
- **翹角像管子**：歇山頂四角的戧脊改細，半徑從 8.5 cm 收成 7 → 4 cm 漸細，貼回屋面（離瓦面 6.5 → 4.5 cm）；端頭上翹從 8 cm 降到 3.5 cm。

## 和 MC01 共用的部分

- **貼圖**：共用 MC01 的 2048 × 2048 Trim Sheet（`art/textures/mountain-street-houses-a/`），分院和山城街屋可以合批。
- **語言**：沿用 #80 第三輪定下的中式山城語言：深色木、花崗白、黛瓦、銅件；不用短簾、圓紙燈、方格窗和斜撐。

## 材質（全套共 4 個，Unity 設定照 `model_info.json` 的 `materialNotes`）

| 材質 | 貼圖 | 用在 |
|---|---|---|
| `M_MountainStreet_Trim` | MC01 共用 Trim Sheet | 石、木、銅等大部分部件 |
| `M_TX04_Roof` | 同上，法線強度 0.5（Unity `_BumpScale` 0.5） | 所有瓦件 |
| `M_TX04_Wall` | `T_TX04_Wall_Albedo` / `_Normal`（1024²） | 白灰牆、廂房山牆 |
| `M_TX04_Accent` | Trim Albedo × 道統色（Unity `_BaseColor`），Trim Normal | 朱漆部件 |

## 換裝接口（D3 §5）

| 接口 | 做法 |
|---|---|
| `_Accent`（道統色） | 朱漆部件合成 `TX04_<ID>_Accent` 物件，用 `M_TX04_Accent`。<br>材質底色是一個顏色參數（太玄預設 `#8E2F25`），乘在 Trim Sheet 灰泥條上，換色後雨痕和磨損還在。<br>Unity 改 `M_TX04_Accent` 的 `_BaseColor` 就換成其他道統色（Unity 檢查裡實際換過一次並出圖）。 |
| 朱漆比例 | 寫在 `model_info.json` 的 `accent.surfaceShare`，建模腳本會擋下超過 10 % 的件。<br>院門 2.9 %、正堂 0.8 %，其餘 6 件 0 %。 |
| `Socket_Plaque` | 院門、正堂匾面中央的空物件，Z 軸朝前（−Y），放 TX01 的匾；匾框是空白的。 |
| `Socket_Emblem` | 院門、正堂正脊中央上方的空物件，留給道統徽記。 |

照規格沒有做徽記和任何文字。

## 各件數字

| ID | 尺寸 W×D×H（m） | LOD0 / LOD1 / LOD2 三角面 | 物件 | 材質 | 朱漆 | 碰撞 | 最低檔 |
|---|---|---|---|---|---|---|---|
| TX04-GATE 院門 | 5.916 × 2.946 × 5.713 | 72,368 / 33,566 / 10,068 | 2 | 4 | 2.9 % | 5 盒 | low |
| TX04-WALL-ST 直牆 | 4.0 × 0.694 × 2.478 | 15,244 / 7,622 / 2,286 | 1 | 3 | 0 | 1 盒 | low |
| TX04-WALL-CO 角牆 | 2.368 × 2.367 × 2.477 | 15,684 / 7,842 / 2,352 | 1 | 3 | 0 | 2 盒 | low |
| TX04-WALL-DO 門邊牆 | 4.0 × 0.694 × 2.498 | 15,328 / 7,664 / 2,298 | 1 | 3 | 0 | 1 盒 | low |
| TX04-HALL 正堂 | 13.976 × 8.928 × 7.944 | 185,640 / 88,758 / 23,912 | 2 | 4 | 0.8 % | 4 盒 | mid |
| TX04-SIDE 廂房 | 7.936 × 4.968 × 4.938 | 82,744 / 41,372 / 12,410 | 1 | 3 | 0 | 4 盒 | low |
| TX04-PAVE 院鋪地 | 3.99 × 3.99 × 0.129 | 4,056 / 2,028 / 608 | 1 | 1 | 0 | 1 盒 | low |
| TX04-STEPS 石階 | 4.0 × 2.0 × 0.794 | 1,392 / 696 / 208 | 1 | 1 | 0 | 5 盒（每級一盒） | low |

- **原點與格式**：底面中心、z＝0；Blender −Y 是正面。LOD1 ≤ 50 %、LOD2 ≤ 15 %（上限 100k / 25k）。只交 FBX，內含 LOD0/1/2 和 `_Collision`；院門和正堂另含兩個插槽空物件。
- **正堂面數**：LOD0 18.6 萬面，大部分是 14 m 寬歇山頂的筒瓦，已經用較粗的瓦面網格（`res=2`）。
  - 最低檔標 mid，手機請從 LOD1 起跳。
  - LOD1 8.9 萬、LOD2 2.4 萬，都在上限內。
- **效能**：不寫 FPS；手機未實測。

## 各件做法與拼法

- **院門**（三視圖 option4）：
  - 結構：花崗台基、三級石階、8 根深色杉木柱立在蓮瓣鼓墩上。
  - 門：朱漆雙扇門，每扇 25 顆門釘，有鋪首、門環和深色背板。
  - 簷下與屋頂：前後各 5 組一斗三升、空白匾、歇山頂。
- **直牆 WALL-ST**（option2）：4 m 一段，兩端切平。深色木端柱只在 −X 端，連續拼牆時每 4 m 一根。
- **角牆 WALL-CO**（option2）：
  - 位置：兩道牆的中心線走在格子的中線上。A 臂從格子 −X 邊到中心，B 臂從中心到 +Y 邊，外角在 (+X, −Y)。
  - 轉角：一根 0.48 m 見方的深色木角柱；壓頂在外角斜接，並有一條斜脊。
  - 端頭：A 臂遠端自帶端柱（和直牆一樣）；B 臂端頭切平，由下一段直牆的 −X 端柱收。
  - 其他三個角：旋轉 90° 的倍數。
- **門邊牆 WALL-DO**（option2）：
  - −X 端：端柱同直牆。
  - +X 端：一根較粗的門邊柱，坐在高石座上，高出壓頂，有木蓋板和小雙坡瓦帽。
  - 門洞：門洞和門扇不屬於這一件；另一側放一段轉 180° 的 WALL-DO，就成一個門洞。
- **正堂 HALL**（option3）：
  - 結構：7 開間單層、0.75 m 花崗台基、5 級前石階，前廊一排深色柱。
  - 門面：中間開間是朱漆雙扇門（有門釘、門環、背板）；其餘 6 開間是直櫺門窗（深色框、木裙板、直櫺、背板）。
  - 牆面：兩山和後牆是石牆裙加白灰牆。
  - 簷下：每根柱和每個開間中間都有斗栱；前額枋下緣有朱漆細邊；匾框是朱漆，匾面空白。
  - 屋頂：歇山頂，深出簷。
- **廂房 SIDE**（option1）：
  - 結構：4 開間單層、0.45 m 台基，門前 3 級石階；石牆裙加白灰牆。
  - 門窗：3 扇直櫺窗、1 扇素木雙扇門（不上朱漆）。
  - 屋頂：簡單斗栱，兩坡懸山頂，山牆是白灰三角牆。
- **院鋪地 PAVE**（option3）：4 × 4 m，裡面是錯縫長石板，頂面高低差在 ±3 mm 內。邊石只在 −X、−Y 兩邊，所以一格一格拼起來時，每條格線只有一條邊石。
- **石階 STEPS**（option2）：
  - 尺寸：4 m 寬、2 m 深、5 級，從地面升到 0.75 m（和正堂台基同高）。
  - 兩側：整塊斜放的花崗垂帶石，端頭有石墩；不上朱漆、不放瓦。
  - 用途：院子分台地時用，平地的組裝範例沒有用到。

## 分院組裝（`tx04-academy-assembly.json`）

圍牆中心線在 x＝±8、y＝±10（16 × 20 m）：

- 前牆中間是院門，兩側各一段直牆；
- 四角各一個角牆（轉 0 / −90 / 90 / 180°）；
- 兩側各 4 段直牆；
- 後牆中間是兩段門邊牆夾出的 4 m 後門；
- 正堂在後半；兩側廂房面向院子；中間鋪 6 格院鋪地。

## 驗收紀錄

- **Blender 資產 QA**（blender-asset-qa `qa_check`，game profile，每個 LOD0 物件單獨掃，z-fighting／懸空都有跑）：結果存 `art/source/tx04-branch-court/qa_all.json`。
  - 8 件都沒有 z-fighting、翻面或破面。
  - 院門、正堂主體單獨掃時，會把門釘、鋪首、門環報成「懸空」，因為它們釘在屬於 `_Accent` 物件的朱漆門扇上。主體和 `_Accent` 合在一起再掃，懸空＝0。
- **FBX 回匯**：8 件尺寸都和建模時相同（誤差 0）。
- **Unity 6000.0.82f1 匯入檢查**（`apps/game/Assets/YunJing/Editor/Tx04BranchCourtVerify.cs`）：報告和截圖在 `art/previews/tx04-branch-court/unity/`，結果見 `unity/report.txt`。
  - 每件都檢查：尺寸、底面在地上、LOD 三角面、物件數；材質槽全部對到 4 個共用材質、朱漆物件、插槽位置；LODGroup、碰撞。
  - 換色測試：實際把 `M_TX04_Accent` 換成藍色出一張圖，確認只有朱漆部件變色。
  - 整座分院：照 `tx04-academy-assembly.json` 擺出來並截圖。
  - 貼圖照專案的 QingxiImportBudget 在 Unity 裡縮成 1024，這條規則沒有改。

## 選圖

各件的「選用：」和理由在 `art/references/TX04-*/prompt.txt`。提示詞用 `tools/mountain-city-a/make_prompts_tx04.py` 產生：

- 工作包第 11 節的物件句；
- 「只畫這一件」的範圍句；
- 核心組在 #80 給的不要日式、歐式負面詞；
- 第一輪審查後加的「柱子是深色木、不是紅色」。

## 怎麼重跑

```
python art/source/tx04-branch-court/gen_wall_tex.py
python tools/mountain-city-a/make_prompts_tx04.py
python tools/mountain-city-a/gen_threeviews.py --prompts prompts_tx04.json <ID ...>
blender -b --factory-startup -P art/source/tx04-branch-court/build_tx04.py -- GATE WALL_ST WALL_CO WALL_DO HALL SIDE PAVE STEPS
blender -b --factory-startup -P art/source/tx04-branch-court/qa_tx04.py -- <絕對路徑 out.json> <ID ...>
blender -b --factory-startup -P art/source/tx04-branch-court/render_tx04.py -- --out <repo 絕對路徑>/art/previews/tx04-branch-court [--clay|--wire|--nodetail|--lod 1] <ID ...>
blender -b --factory-startup -P art/source/tx04-branch-court/assemble_tx04.py -- [--academy] [--clay]
python art/source/tx04-branch-court/sheets_tx04.py <ID ...>
Unity -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.Tx04BranchCourtVerify.Run -logFile <log>
```

## 預覽

`art/previews/tx04-branch-court/`：

- 每件：四視圖（含 1.75 m 人形尺）、灰模、線框、LOD0／LOD1、參考圖對模型；
- `TX04_academy_*`：整座分院（材質與灰模同角度、正面、院內 1.7 m 人眼），`TX04_academy_sheet_a/b.jpg` 是對照表；
- `TX04_sample_*`：第一輪的樣品組裝（院門＋直牆）；
- `unity/`：Unity 匯入截圖與報告。

## 工時

- 樣品：約 2 小時（11/09）；
- 第一輪修改：約 1 小時；
- 其餘 6 件、第二輪修改、分院組裝和 Unity 檢查：約 5 小時（11/09）。

全部由 Claude Code 執行。
