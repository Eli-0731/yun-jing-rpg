# 承天｜2026-11-07 工作包第一部分：TE04 採茶竹簍／晾茶竹匾、TE05 東坡觀景亭、RI03 稻田灌溉大水車

| 項目 | 內容 |
|---|---|
| 誰做的 | B（joshsu54） |
| 工作包 | docs/execution/2026-11-07/B-104h-tea-wheel-and-mountain-way.md（第一部分；檔案在 `feature/qingxi-creek-chapter` 分支）；規格照 docs/execution/2026-11-05/B-48h-tea-and-irrigation.md 第 5、11 節 |
| ID | TE04（採茶竹簍、晾茶竹匾）、TE05（東坡觀景亭）、RI03（稻田灌溉大水車） |
| 分支／PR | art/b-1107-te04-te05-ri03-tea-wheel ／ #79 |
| 版本 | v001（首次交付，沒有舊版） |
| 狀態 | Exported ／ Imported（Unity 編輯器批次檢查）／ Visually Verified；In-game Verified：未驗 |
| 素材來源 | 原創（Blender 程序化建模）；三視圖參考由 Codex image_gen 生成，只當比例參考；同場比較用的 WM02 來自 creek-repair-b，沒有修改 |

放在 `tea-terraces-b` 同一套流程裡（同一支建模腳本、同一套材質與檢查），TE04／TE05 的槽位沿用 `A4_TeaTerraces`，RI03 用 `A6_GreatWheel`。
**沒有改主場景、沒有改區塊 JSON、沒有宣稱已正式落位。** 新東西只做在 Unity 用的模型裡，沒有新增網頁版（PWA）頁面。

> **修正輪（同日 20:17 起）**：第一版自評後四件都有低於 95 的項目，在送 PR 前直接重建 v001（v001 還沒推上遠端，所以沒有另開 v002）。下面的數字、截圖、檢查結果都是修正後重跑的；每件「自評」段落列出這輪改了什麼。

## 進度

| ID | 名稱 | Exported | Imported（Unity 編輯器） | Visually Verified | In-game Verified |
|---|---|---|---|---|---|
| TE04_Basket | 採茶竹簍 | 是 | 是（10 項 PASS） | 是 | 否 |
| TE04_Tray | 晾茶竹匾 | 是 | 是（10 項 PASS） | 是 | 否 |
| TE05_Pavilion | 東坡觀景亭 | 是 | 是（10 項 PASS） | 是 | 否 |
| RI03_GreatWheel | 稻田灌溉大水車 | 是 | 是（14 項 PASS，含轉動 3 項） | 是 | 否 |
| 40×40 m 茶田樣本 | — | JSON＋Blender 場景 | 否（沒有在 Unity 擺） | 是（Blender 算圖） | 否 |
| RI03 與 WM02 同場 | — | JSON＋Blender 場景 | 否 | 是（Blender 算圖） | 否 |

Unity 6000.0.85f1（URP）`TeaIrrigationModelCheck`：四件合計 **44 項 PASS、0 FAIL**。這是編輯器批次檢查，沒有放進主場景、沒有進遊戲跑。
**未驗**：手機效能（沒有量測，不寫 FPS）、遊戲中的互動（拿竹簍、坐亭子、水車轉動）、真人鍵鼠操作、亭子與水車在正式地形上的落位。水車只在編輯器裡轉過（檢查軸心與轉動），資產裡沒有轉動腳本。

## 共同風格三點（與既有 tea-terraces-b、harvest-market-b、creek-repair-b 一致）

1. **暖金光下的自然材色**：竹編暖金黃、杉木與亭柱暖褐、瓦青灰、石暖灰、麻繩暖褐，陰影不用純黑；和 TE01–03 的暖灰石、暖褐土同一個色溫。
2. **大色塊、細節集中在接頭**：編面、瓦面、輪圈都是大面積材色加輕微明暗差；綁繩、補編、青苔、茶葉這類細節集中在口緣、接頭和角落，拆成 `Detail_*`，低階可以整件關掉。
3. **只在該舊的地方舊**：竹簍右後一處淺凹與一塊補片、竹匾兩處補編、亭子右前角一片補過的新瓦與脊上青苔、水車石墩下半部的濕色與青苔；其他地方保持有人在用的樣子。

## TE04_Basket 採茶竹簍（v001）

- 參考：`art/references/TE04/20261107-threeviews-v001/BASKET/candidate-01.png`；選圖理由與建模時的修正寫在 `art/references/TE04/prompt.txt`。
- 尺寸：**0.496 × 0.483 × 0.394 m**（工作包：口徑約 0.5 m、高約 0.4 m）。原點在底部中心，z = 0 在底圈下緣；正面 -Y。
- 和 harvest-market-b **MK04 背簍**不同：圓、矮、開口大；沒有立樁、木底架和背帶。
- 構造：45° 人字剖竹編（竹篾 8.5 mm，每圈整數 27 個編紋單位，沒有接縫；編塊在外形上有約 1 mm 起伏，輪廓不是光滑圓錐）、平底稍凹；口緣內外兩道竹圈各由 6 段剖竹接成，接頭在綁繩下，12 處麻繩穿壁綁；底圈 3 段、9 處綁；補片四角與四邊共 8 個十字縫；簍底 9 片、口緣 2 片、靠後壁 6 片剛採的茶葉。

### 每級 LOD 實際數字（model_info.json `budget_per_lod`）

| LOD | 三角面 | 物件數 | 不含 Detail 的物件 | 材質數 |
|---|---|---|---|---|
| LOD0 | 19,208 | 2（Main＋Detail_Small） | 1 | 1 |
| LOD1 | 9,604（50.0%） | 2 | 1 | 1 |
| LOD2 | 2,879（15.0%） | 2 | 1 | 1 |

- Main 11,964／5,982／1,793；Detail_Small 7,244／3,622／1,086。LOD0 沒有為了數字減面；LOD1、LOD2 先丟細節再 collapse 減面。
- `minTier: standard`；`detailObjects: ["TE04_Basket_Detail_Small"]`，關掉後外形不變（`TE04_Basket_LOD0_LOD1_no_detail.png`、Unity `TE04_Basket_close_no_detail.png`）。
- 碰撞：`TE04_Basket_Collision`，12 邊截錐，44 三角面。

### 貼圖（全部 1024 × 1024，同一張 atlas）

| 檔案 | 用途 |
|---|---|
| `TE04_Basket_BaseColor.png` | 顏色（sRGB） |
| `TE04_Basket_Normal.png` | 法線（OpenGL +Y） |
| `TE04_Basket_MetallicSmoothness.png` | URP Lit 用（R metallic、A smoothness） |
| `TE04_Basket_Roughness.png`、`TE04_Basket_Metallic.png` | 其他引擎／GLB 用；Unity 材質沒有引用 |

### 檢查結果

- Blender `validation.json`：12 項全部通過（尺寸、底部 z = 0、寬口收底、Detail 分件、LOD 比例、FBX 回匯尺寸誤差 0 mm（上限 2 cm）、LOD0/1/2、碰撞、GLB、十方位）。
- 網格 QA（`qa/qa_mesh.json`、`qa/qa_fbx.json`）：退化三角面 0、零面積 UV 0（1e-12～1e-9）、同向共面 0（1 mm／0.5 mm／0.1 mm）、反向封閉件 0、未烘焙黑面 0、浮空件 0；UV 重疊 0 texel。
  - 警告（接受）：FBX 雙面共面 592 對，都是葉片與補片這類薄片的正反兩面，不會閃爍。零面積 UV 到 1e-8 都是 0。
- 背面檢查（Unity 會剔除背面）：八個方向紅色（背面）最多 0.05%。
- Unity 6000.0.85f1（URP）`TeaIrrigationModelCheck`：本件 10 項 PASS、0 FAIL（匯入尺寸與邊界誤差 0.0 mm、LODGroup 三級、三角面與物件數等於 model_info、Detail_Small 每級都是獨立物件、MeshCollider、射線打得到碰撞、沒有錯誤著色器）。截圖在 `artifacts/tea-irrigation-unity/`（本機產物，不提交）。
- **未驗**：手機效能（沒有量測，不寫 FPS）、實際遊戲中拿取／擺放、真人鍵鼠操作。Unity 檢查是編輯器批次模式，不是遊戲流程。

### 交付位置

| 項目 | 位置 |
|---|---|
| 可編輯 .blend | `art/source/tea-terraces-b/blend/TE04_Basket_v001.blend` |
| 生成腳本 | `art/source/tea-terraces-b/te_props.py`（竹簍）、`build_tea_terraces_b.py`（建模＋匯出＋驗證）、`ruler_views.py --four`（四向比例尺）、`pair_sheets.py`（灰模／材質並排） |
| FBX／GLB／貼圖 | `art/exports/tea-terraces-b/TE04_Basket/TE04_Basket_v001.fbx`、`.glb`、`Textures/` |
| model_info.json／validation.json／qa | 同資料夾 |
| 十方位、線框、LOD 對照、Detail 關閉對照 | `art/previews/tea-terraces-b/TE04_Basket/` |
| 1.75 m 人形四向（正、側、背、3/4），灰模與材質同光同角度 | `ruler_0{1..4}_*_{grey,material}.png`、並排 `compare_0{1..4}_*_grey_material.png` |
| Unity 檢查 | `apps/game/Assets/YunJing/Editor/TeaIrrigationModelCheck.cs` |

### 自評

六項（各 100 分）：外形與輪廓 95、拓撲與結構 96、材質與光影 95、風格一致 96、動畫互動 95、效能匯出 97。加權（25／20／20／15／10／10）95.6。
第一版：棋盤格編紋 → 人字斜編；編紋接縫；竹圈像塑膠 → 分段剖竹帶竹節；綁繩鬆散 → 緊纏；編紋太規整 → 每條竹篾明暗差＋手編輕微歪斜；外形太完美 → 右後淺凹；QA 的共面／退化面／浮空茶葉全部清零。
修正輪：編紋太粗（一圈 18 格）→ 27 格、竹篾 12.5 → 8.5 mm；輪廓是光滑圓錐 → 編塊約 1 mm 起伏；Unity 無後製時竹編偏金黃 → 竹編、竹圈降飽和；茶葉中脈加一道摺。
還沒做的：沒有提把或背帶（工作包沒要求）；動畫互動只有碰撞，沒有拿取插座。

## TE04_Tray 晾茶竹匾（v001）

- 參考：`art/references/TE04/20261107-threeviews-v001/TRAY/candidate-04.png`（平面比例）＋`candidate-04-r1.png`（扁平立面）；選圖理由與修正寫在 `art/references/TE04/prompt.txt`。
- 尺寸：**1.215 × 0.755 × 0.12 m**（工作包：寬約 1.2 m、高約 0.12 m）。原點在底部中心，z = 0；正面 -Y。長寬比 1.62，是圓角長方形，不是圓篩。
- 構造：底與壁是同一張人字剖竹編（一體成形，不是底板加圍邊）；口緣內外各一道舊杉木條，在 12 處深色藤綁處對接（每處纏 5 圈）；兩處補編（底面右後 6×6 編條、正面牆中線偏左 4×4，編條兩端參差）；底面鋪 240 片乾枯捲曲的茶葉（3 種橄欖／黃褐色，每片 0.5 mm 厚的封閉薄殼，中心間距 ≥ 2 cm，貼在編面上）。
- 葉、補編、綁繩在 `Detail_Small`；關掉後竹匾外形不變。

| LOD | 三角面 | 物件數 | 不含 Detail 的物件 | 材質數 |
|---|---|---|---|---|
| LOD0 | 39,776 | 2（Main＋Detail_Small） | 1 | 1 |
| LOD1 | 19,888（50.0%） | 2 | 1 | 1 |
| LOD2 | 5,966（15.0%） | 2 | 1 | 1 |

- Main 12,576／6,288／1,886；Detail_Small 27,200／13,600／4,080（多半是茶葉：薄殼每片約 68 三角面）。關掉 Detail 時 LOD0 是 12,576。`minTier: standard`。
- 貼圖：BaseColor、Normal（OpenGL +Y）、MetallicSmoothness、Roughness、Metallic，**全部 1024 × 1024**，同一張 atlas。
- Blender `validation.json` 12／12 通過（含尺寸、底部 z = 0、圓角長方形、Detail 分件、LOD 比例、FBX 回匯誤差 0 mm）。
- 網格 QA：退化面 0、同向共面 0、反向封閉件 0、黑面 0、浮空件 0、UV 重疊 0 texel；零面積 UV 1e-9 以下 0，最寬鬆的 1e-8 有 1 個；背面（Unity 會剔除）八方向最多 0.11%（修正前 6.41%）。警告（接受）：FBX 雙面共面 4,612 對，是 0.5 mm 葉片薄殼的上下兩面，不會閃爍。

### 自評

六項：外形與輪廓 95、拓撲與結構 95、材質與光影 95、風格一致 96、動畫互動 95、效能匯出 95。加權 95.2。
第一版：亮綠紙片般的茶葉 → 乾枯捲曲葉三色；像貼紙的補片 → 真的補編；口緣太細 → 加寬杉木條；灰色綁繩 → 深色藤；尺寸超出 → 縮小外框；壁上補編的同向共面 16 對 → 0。
修正輪：單面葉翹起處露出黑色背面 → 0.5 mm 封閉薄殼（背面 6.41% → 0.11%）；葉色在 Unity 像綠色碎紙 → 橄欖、黃褐；藤綁每圈 6 點看起來像釘子 → 每處 5 圈、每圈 14 點；杉木口緣在 Unity 偏粉紅 → 舊杉木灰褐；編紋格太粗 → 縮小；補編加密後牆上那片相鄰篾片重疊（同向共面 23 對）→ 牆上改 4×4、篾寬按間距縮，回到 0。
還沒做的：茶葉薄殼讓 Detail_Small 變重（27,200）；低階關掉 Detail 就只剩 12,576。

## TE05_Pavilion 東坡觀景亭（v001）

- 參考：`art/references/TE05/20261107-threeviews-v001/PAVILION/candidate-04.png`；修正寫在 `art/references/TE05/prompt.txt`。
- 尺寸：**4.895 × 4.948 × 4.983 m**（上限 5 × 5 × 5 m）。原點在台基底面中心，z = 0；正面 -Y（踏步）。
- 和 creek-repair-b **WM09 竹亭**不同：方形四柱、木構瓦頂、架在石台基上；WM09 是圓形竹構草頂。
- 構造：0.5 m 石台基（兩層毛石面、頂鋪石板）、正面三級踏步；四根圓柱立在鼓形柱礎上，上下兩道額枋間有短柱、曲線雀替，柱頭上方墊木加十字交叉栱臂與小斗；四角攢尖青綠筒板瓦（每壟、每三層瓦各有自己的燒成深淺），翼角起翹，脊上青苔，右前角一片補過的新瓦；背側與右側 L 形坐凳＋欄杆，左側後半木板牆（內外各兩道橫帶）、前半矮欄杆，左前柱旁水缸（缸蓋、竹勺）。
- 可通行：亭內地面 = 台基頂（0.484–0.504 m）；踏步每級 0.121–0.129 m（≤ 0.2 m）；亭內淨高 5 個測點最小 2.12 m（正面柱間），其他 ≥ 3.5 m；正面柱間淨寬 2.53 m。
- 碰撞：方塊組合（台基、踏步、四柱、坐凳、板牆、欄杆、水缸；屋頂碰不到所以不做）。插座：`Socket_Seat_Back`、`Socket_Seat_Right`、`Socket_Jar`。

| LOD | 三角面 | 物件數 | 不含 Detail 的物件 | 材質數 |
|---|---|---|---|---|
| LOD0 | 75,544 | 2（Main＋Detail_Small） | 1 | 1 |
| LOD1 | 37,771（50.0%） | 2 | 1 | 1 |
| LOD2 | 11,330（15.0%） | 2 | 1 | 1 |

- Main 60,324／30,161／9,048；Detail_Small 15,220／7,610／2,282。`minTier: low`（地標，低階也要顯示）。
- 貼圖：BaseColor、Normal、MetallicSmoothness、Roughness、Metallic，**全部 2048 × 2048**。
- Blender `validation.json` 14／14 通過（含 5 m 以內、地面在台基頂、踏步高、淨高、正面開口、LOD 比例、FBX 回匯）。
- 網格 QA：退化面 0、同向共面 0、反向封閉件 0、黑面 0、浮空件 0（FBX 回匯後 491 塊）、UV 重疊 0 texel；零面積 UV 1e-9 以下 0，最寬鬆的 1e-8 有 9 個（Detail_Small 的青苔尖）。背面最多 3.77%（八方向之一）。警告（接受）：雙面共面 496 對（瓦片、青苔薄片正反面）。

### 自評

六項：外形與輪廓 96、拓撲與結構 95、材質與光影 95、風格一致 96、動畫互動 96、效能匯出 95。加權 95.5。
第一版：淨高測點放錯地方；雀替多一個重複點造成退化面 → 改成四邊形帶，尖端那一格去掉重複角點（之前 Blender／FBX／Unity 三邊三角面數各差 16，現在一致）；踏步背面共面 → 錯開；簷口瓦當 UV 重疊 1,618 texel → 0；翼角超出 5 m → 縮短；後側額枋、欄杆、檁條被翻轉 180°（`between` 沿 -X 時的旋轉問題）→ 統一方向；坐凳板、欄杆柱、台基石板、墊木浮空 56 塊 → 0。
修正輪：斗栱只有方墊木 → 加十字交叉栱臂與臂端小斗（相交的臂錯開 12 mm，避免共面）；瓦色偏灰藍、整片同色 → 依 SectCore 青綠瓦調暗偏綠，每壟、每三層各自深淺；柱、梁、木板顏色在 Unity 偏紅 → 降飽和、加一點灰；板牆一整片平板 → 內外各加兩道橫帶。
還沒做的：瓦當、滴水沒有紋樣；坐凳沒做坐下動作，只有插座。

## RI03_GreatWheel 稻田灌溉大水車（v001）

- 參考：`art/references/RI03/20261107-threeviews-v001/GREAT-WHEEL/candidate-04.png`；修正寫在 `art/references/RI03/prompt.txt`。
- 尺寸：**2.133 × 10.428 × 8.997 m**（輪徑 9 m，量到竹筒最外緣；組件寬約 2.1 m）。**原點在轉軸中心**；河岸地面在原點下 4.0 m（`ground_z_m: -4.0`、`Socket_Ground`），輪底沒入水道 0.5 m。正面 -Y 看到輪緣。
- 和 creek-repair-b **WM02 磨坊水車**不同：直徑約兩倍（9 m 比 4.6 m）、不用鐵件、用 32 根竹筒把水提上來，不帶動磨坊。
- **三件分開**（可單獨轉動）：
  - `Wheel`（會轉）：轉軸、軸頭、輪轂，每側 16 根輻條、雙外圈加半徑 2 m 內圈（每圈由 24／24／12 段接成），32 片輪葉，32 根竹筒。繞 Blender X（Unity 也是 X）轉，軸心在原點。
  - `Seat`（不動）：兩座收分毛石墩、基石、木軸承座。
  - `Trough`（不動）：-X 側的集水槽、往 +Y 的導水槽與四柱槽架。
  - `Detail_Wheel`：跟著輪子轉的綁繩（輻條與輪圈交接、竹筒綁繩），要掛在 Wheel 底下一起轉。`Detail_Small`：靜止的綁繩、青苔、槽裡的水。
- 怎麼運作：竹筒綁在 -X 輪圈外側、向外傾 9.5°–12°（每根略不同，不超過 12°），在水道裡裝水，轉過頂端時把水倒進旁邊的集水槽，再沿 1.5 cm/m 的坡流向田（`Socket_Trough_Out`）。圖上槽在輪子正上方，竹筒轉上去會撞到，所以改在旁邊。
- **轉一整圈不碰任何靜止件**：validation 把輪子表面點依（x、到轉軸的半徑）分格掃一圈，再查石墩、槽、槽架有沒有落在同一格（格寬 2 cm）；結果 0 點。軸在軸承裡本來就要貼著，所以那一段排除。
- 碰撞：24 邊鼓形包住輪子，加上石墩、槽、四根槽柱的方塊（188 三角面）。插座：`Socket_Axle`、`Socket_Ground`、`Socket_Trough_Out`。

| LOD | 三角面 | 物件數 | 不含 Detail 的物件 | 材質數 |
|---|---|---|---|---|
| LOD0 | 77,820 | 5（Wheel、Seat、Trough、Detail_Wheel、Detail_Small） | 3 | 1 |
| LOD1 | 38,910（50.0%） | 5 | 3 | 1 |
| LOD2 | 13,498（17.3%） | 5 | 3 | 1 |

- 分件 LOD0／1／2：Wheel 40,360／20,180／6,054；Detail_Wheel 26,112／13,056／5,746；Seat 3,852／1,926／576；Detail_Small 3,848／1,924／576；Trough 3,648／1,824／546。
- `minTier: low`（地標）；`detailObjects: ["RI03_GreatWheel_Detail_Small", "RI03_GreatWheel_Detail_Wheel"]`。
- 貼圖：BaseColor、Normal、MetallicSmoothness、Roughness、Metallic，**全部 2048 × 2048**。
- Blender `validation.json` 14／14 通過（含輪徑 9 m、寬約 2 m、最低點 -4.5 m、軸心在原點、三件分開、轉一圈不碰、LOD 比例、FBX 回匯誤差 0 mm）。
- 網格 QA：退化面 0、同向共面 0、反向封閉件 0、黑面 0、浮空件 0（FBX 回匯後 632 塊）、零面積 UV 0（到 1e-8 都是 0）、UV 重疊 0 texel；背面最多 0.01%。警告（接受）：Blender 檔雙面共面 49 對，FBX 0 對。
- Unity 轉動檢查（修正輪新增）：Wheel 與 Detail_Wheel 六個物件的軸心都在轉軸上（誤差 0.0 mm），繞 X 轉 0–90°（每 15°）外框中心不偏移；0°／15°／30° 三張側視截圖看得到輻條轉過去（45°、90° 剛好是輻條間距 22.5° 的整數倍，看起來會像沒轉，所以不用）。

### 自評

六項：外形與輪廓 96、拓撲與結構 95、材質與光影 95、風格一致 95、動畫互動 96、效能匯出 95。加權 95.4。
第一版：竹筒浮空且偏到輪葉旁 → 置中綁在輪葉端；輪圈太細 → 加粗；水色太青 → 加深；寬度超出 → 縮基石與槽；竹筒轉到頂撞到集水槽、輪圈擦過基石 → 竹筒移到輪圈外側、槽與槽架後退、基石內縮（掃掠檢查 855 點 → 0）；石墩每層之間 1.2 cm 縫讓石塊浮空 → 互相壓 3 mm；輪圈各段間 1.6 cm 縫讓沒有輻條穿過的段浮空 → 段與段對接；槽上橫木懸空 → 壓進槽壁 5 mm。
修正輪：槽架對 9 m 輪子太細 → 柱、橫梁 18 × 18 cm、斜撐 13 cm；柱頭沒有接合 → 沒有槽壓著的兩根柱頭做榫頭加木楔；32 根竹筒一模一樣 → 長度、傾角各略不同（傾角一度超過 12° 時筒口掃到側槽，掃掠檢查抓到後改成只往內收）；木色在 Unity 偏紅 → 降飽和；輪圈綁繩 4 圈只用 24 點、每圈 6 點看起來是多角形 → 3 圈、每圈 8 點；Unity 檢查加轉動 3 項。
還沒做的：沒有竹筒倒水的水花；資產裡沒有轉動腳本（軸心已對好，掛一個繞 X 的旋轉就能轉）。

## 40 × 40 m 茶田樣本（TE04／TE05 擺進茶田）

- 腳本：`art/source/tea-terraces-b/assembly_tea_irrigation.py`（`-- --render` 會存場景並算圖）。輸出 `art/exports/tea-terraces-b/assembly-20261107/farm-assembly.json`（235 件），舊的 `assembly/farm-assembly.json` 沒有動。
- 擺法：沿用舊樣本的第 0–7 排梯田（同樣的段、階梯、步道、茶叢），第 8 排換成坡頂一塊平的觀景台（y 14–20、z 8，與第 7 排土面同高；觀景台地面是佔位平面，不是套件）。
  - TE05 在 (5, 17.3, 8)，踏步朝 -Y 往下看茶田。
  - TE04 竹匾 3 個晾在觀景台上；TE04 竹簍 4 個：觀景台 1 個、第 1／3／5 排步道上坡側各 1 個。竹匾和竹簍的 z 都是往下打射線貼到地面或步道（中心加四角取最高點）。
- 算圖：`art/previews/tea-terraces-b/assembly-20261107/field_aerial.png`、`field_lookout_from_row7.png`、`field_trays_and_pavilion.png`、`field_from_pavilion.png`、`field_basket_on_path.png`。
- 可編輯場景：`art/source/tea-terraces-b/blend/assembly_tea_irrigation_v001.blend`。
- 看到的問題（沒有改）：`field_basket_on_path.png` 左上，第 3 排兩段梯田相接處的溝底有一道縫露出背景；這是沿用舊樣本的段落擺法，不是 TE04／TE05 造成的，留給梯田套件另外處理。

## RI03 與 WM02 同場比較

- 同一條沿 Y 的水道（寬 1.43 m，水面 z -0.15），河岸 z 0：RI03 軸心 z 4.0（輪底 -0.50），WM02（creek-repair-b）軸心 z 2.0（輪底 -0.30），兩輪相距 9 m，中間站 1.75 m 人形。
- 輪徑比 1.96（8.997 m ／ 4.602 m）。數字在 `art/exports/tea-terraces-b/assembly-20261107/wheel-compare.json`。
- 算圖：`wheels_side_by_side.png`、`wheels_three_quarter.png`（同資料夾）。只供比較，不是遊戲落位。

## 這次改到的共用工具

- `qa_fbx.py`：浮空件的判斷加上「穿入」：一件的頂點落在另一件封閉體積裡也算接觸（例如輻條端插進輪圈、輪葉穿過輪圈）。只對封閉的件算，薄片不算。原本的 5 mm 雙向接觸判斷不變。
- `build_tea_terraces_b.py`：加上 TE04_Tray、TE05_Pavilion、RI03_GreatWheel 三件的設定與專屬檢查（竹匾比例、亭子淨高／踏步／開口、水車輪徑／軸心／分件／轉動掃掠）；`base_z` 讓 RI03 的最低點檢查用 -4.5 m；model_info 多 `ground_z_m` 與 `parts`。
- `mk_mats.py`：竹編材質 `weave()` 多兩個參數 `wobble`（編紋格線輕微歪斜）與 `strip_var`（每條竹篾明暗差）；預設值與原本相同，舊素材不受影響。
- `ruler_views.py`：有 `ground_z_m` 的件把河岸放在 z 0 再擺人形。
- `TeaIrrigationModelCheck.cs`：有 `ground_z_m` 的件（RI03）往上抬 4 m，讓河岸落在地板上；RI03 多三項轉動檢查與 0／15／30° 截圖。
- `cr_mats.py`：瓦材質 `tile()` 多 `tone` 參數（每塊瓦一個 0–1 屬性，決定偏深或偏淡）；不給就跟原本一樣，只有 TE05 用到。

## 交付位置（每件同一套）

| 項目 | 位置 |
|---|---|
| 可編輯 .blend | `art/source/tea-terraces-b/blend/<ID>_v001.blend` |
| 生成腳本 | `te_props.py`（竹簍）、`te_tray.py`（竹匾）、`te_pavilion.py`（亭）、`te_wheel.py`（水車）；`build_tea_terraces_b.py -- <ID> --force` 建模＋匯出＋驗證 |
| FBX／GLB／貼圖 | `art/exports/tea-terraces-b/<ID>/<ID>_v001.fbx`、`.glb`、`Textures/` |
| model_info.json／validation.json／qa | 同資料夾 |
| 十方位、線框、LOD 對照、LOD0/1 關 Detail 對照、hero | `art/previews/tea-terraces-b/<ID>/` |
| 1.75 m 人形四向（正、側、背、3/4），灰模與材質同光同角度 | `ruler_0{1..4}_*_{grey,material}.png`、並排 `compare_0{1..4}_*_grey_material.png` |
| Unity 檢查 | `apps/game/Assets/YunJing/Editor/TeaIrrigationModelCheck.cs`；截圖在 `artifacts/tea-irrigation-unity/`（本機產物，不提交） |

## 實際工時

照對話紀錄的時間戳算（2026-11-07）：
- 11:27–12:05 約 0.6 小時：讀工作包、請 Codex 生成並檢視三視圖、選圖。
- 13:24–14:19 約 0.9 小時：TE04 竹簍樣品。
- 18:57–20:20 約 1.4 小時：竹匾、觀景亭、大水車、兩個同場樣本、Unity 檢查、README。
- 20:17–22:05 約 1.8 小時：修正輪（四件依自評重建、重跑 QA／Unity／同場算圖、更新 README）。
- 合計約 4.7 小時；12:05–13:24、14:19–18:57 是等使用者回覆，沒有算進去。工作包估的 24 小時是上限，不是實際用量。

