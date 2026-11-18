| 項目 | 內容 |
|---|---|
| 誰做的 | B（joshsu54） |
| 工作包 | docs/execution/2026-11-15/B-300h-D2-roots-and-wood.md（A 批），共同標準 docs/execution/2026-11-15/00-300h-共同標準.md |
| ID | DR01（樣品）。DR02–DR04 等樣品過了再做 |
| 分支／PR | art/b-1115-d2-root-arch-walls ／【B】11/15 DR01–04：D2 入口大根拱與板根牆 |
| 版本 | **v005**（目前交付）。v001–v004 整份封存在 `DR01_RootArch/v001/`–`v004/`，預覽在 `art/previews/d2-roots-b/DR01_RootArch/v001/`–`v004/`，當時的腳本在 `art/source/d2-roots-b/v001_snapshot/`–`v004_snapshot/` |
| 狀態 | Exported ／ Imported（Unity 6000.3.28f1 獨立匯入檢查 27 項通過）／ Blender 與 Unity 審圖已出 ／ In-game Verified：未驗（沒放進 D2 場景，沒有和真正的神木、地面、霧一起截圖） |
| 素材來源 | 樹皮：Poly Haven `bark_brown_02`（CC0）。植物做法沿用核心組 D2 林下範本 `art/source/core-d2-v1/ground/plants.py`（原樣複製成 `core_plants.py`），根腳心形葉的葉形照核心組 `heart_plant`。其餘原創 |
| 實際工時 | 約 25 小時（2026-11-16 晚上到 11-18，估計值；工作包預估 40 小時）。由 Claude Code 經 Blender MCP 製作，三視圖由 Codex 出圖 |

# D2 根與木頭大件（B 包）

## DR01 南入口大根拱（RootArch，v005，樣品）

**v004 改成前後雙拱**（Josh 11/17：南北兩個入口都是拱門，要換別種形式才分得出來；11/18 看過 v003 交叉尖拱和雙拱預覽後選雙拱。審圖 `DR01_RootArch_v005_review.jpg`）。
v001 是三股根絞成一個圓環；v002 加右肩一道副拱；v003 交叉尖拱（都已封存）；v004 是前後雙拱；**v005 只改兩拱之間的根**（v004 俯視像梯子、側面像橫梁、氣根像平行直條；對照圖 `DR01_RootArch_v004_vs_v005.jpg`），兩道拱本身、淨空、接口都沒動：

- 南拱（入口，原點在它正下方）是三股粗根絞成的圓拱；北拱在它北邊 6.2 m，細一點（約 0.78 倍）、往反方向絞，右腿比左腿粗。
- 兩拱之間是一段短隧道：頂上六條根從南拱騎到北拱，但每條在南北兩拱上搭的位置不同，所以俯視是斜著互相交叉，側面一頭高一頭低；拱起最高的地方不在正中間。其中兩條半路分出一條細根，斜著搭到北拱另一處。根和根之間有縫透光；兩條靠邊的越過北拱垂到地上。
- 頂上的細氣根一束兩三條、粗細長短不一，上段互絞、下段散開，往南或往北斜擺（只在路兩側，3 m 以下不進拱洞淨跨）。
- 兩側各兩條根從拱肩斜著落地，在外側交叉成 X，像撐住隧道的扶壁；中段往外彎、帶一點 S 形。
- 南拱的根只往南、往外散，北拱的只往北、往外散，不散進隧道。北拱的植物是南拱的一半。
- 從設定圖 V2 的鏡位看，南拱和 v001 一樣框住神木，拱洞裡多看得到北拱的一圈；走近或從斜角看才是隧道。

| 項目 | 數字 |
|---|---|
| 參考圖 | `art/references/DR01/v001/`（Codex 依設定圖 V2、V1、V4 出的正側背、頂視與斜角、細節圖；取捨寫在 `prompt.txt`） |
| 尺寸（寬 × 深 × 高） | 38.02 × 33.59 × 9.35 m（含鑽進土裡 0.87 m；最高的頂根比 v004 高約 0.3 m）；y 從 −14.1 到 19.5 |
| 拱洞淨高 | 南拱到北拱整段（y −1.5 到 7.5）：中央 5.79 m；路中央左右各 2 m 內最低 5.26 m（工作包 5 m） |
| 拱洞淨跨 | 整段隧道，地面到 3 m 高之間最窄 9.00 m（工作包 8 m） |
| 兩腳的根往外散 | 西 13.9 m、東 14.4 m，從最近的拱腳量（工作包 12–15 m） |
| 路 | 2.2 m 寬的路沿南北穿過（y −16 到 22 檢查），路面上方 2.2 m 內沒有東西擋；Unity 裡 1.75 m 的膠囊沿路中央和兩側邊緣都走得過 |
| 三角面 LOD0 / LOD1 / LOD2 | 114,333 / 58,392 / 17,779（51% / 16%）；不含 Detail_：78,565 / 40,508 / 12,414。兩道拱，比 v001（93,382）多約兩成；低模取樣已從 0.28 m／28 邊放寬到 0.34 m／24 邊 |
| 物件數（每個 LOD） | 2（本體 1 ＋ `Detail_DR01_Plants`） |
| 材質數 | 5：本體四個材質槽 `M_DR01_RootArch_A`–`D`（四組貼圖），`Detail_DR01_Plants` 用 `M_DR01_RootArch_Leaf`（A 組貼圖，雙面） |
| 貼圖 | 四組（A–D），每組 Albedo、Normal、ORM、MaskURP 各一張，2048×2048，共 16 張；共用細節 `Shared/D2Bark_Detail_Normal.png`、`Shared/D2Bark_Detail_Albedo.png` 各 1024×1024 |
| 紋素密度 | 交付檔約 71 px/m；照專案匯入規則（最大 1024）約 36 px/m。共用樹皮細節沿 UV0 重複 11.22 次 |
| 碰撞 | `DR01_RootArch_Collision`，8,436 面，只含半徑 0.32 m 以上（人跨不過去）的根（MeshCollider，不顯示）；碰撞殼整段隧道淨高最低 5.28 m、淨跨最窄 9.00 m；Unity 裡南拱頂下 / 北拱頂下淨高見 `unity/report.txt` |
| 接口 | `Socket_Path_S` (0, −3.5)／`Socket_Path_N` (0, 9.7)（隧道南北兩端），`Socket_Wall_W`／`Socket_Wall_E`（左右接 DR02 根牆，離原點 15 m） |
| minTier | standard（地標、會擋路） |
| 原點 | 南拱拱洞正下方地面（設定圖 V2 對的是這道拱），北拱在 +6.2 m；z = 0 是地面；Blender −Y 是南面（FBX／Unity 是 −Z） |
| 檔案 | `DR01_RootArch/DR01_RootArch_v005.fbx`（LOD0–2、碰撞、接口）、`.glb`（LOD0）、`Textures/`、`model_info.json`、`validation.json`；原始檔 `art/source/d2-roots-b/blend/`（`_high_` 是高模，另一個是高模＋遊戲模型） |

**做法**

- 對圖用設定圖 V2 的鏡頭：水平鏡頭（相機 (0.5, −15, 1.7) 看 (0, 0, 1.7)，22 mm）。兩道拱的參數在 `build_dr01.py` 的 `ARCHES`，`set_arch(i)` 切換；隧道的根在 `roof()`。連接根不能直線內插（第一版像梯子、像放射狀的梁），也不能每條都從南拱同一個位置走到北拱同一個位置（v004 俯視像梯子）；要斜著交叉、高低不一、半路分叉。
- 高模：每條根是一條路徑掃出來的管，沿路徑有扭轉的粗稜，板根的上緣收窄成稜；再用 `bark_brown_02` 的 Displacement 把樹皮板和裂溝推成幾何。苔是在幾何上鼓起來的苔墊；地衣是世界座標的雜訊斑，凸起處較濃。
- 低模用同一份路徑、較粗的取樣，不帶掃描凹凸；被別的根完全包住、看不到的面刪掉（約一萬五千面），LOD 是每條根各自降段數再刪看不到的面，不用減面器。把高模的顏色、粗糙度、法線、環境遮蔽烘到圖集。
- 顏色對齊核心組神木 GT01 v003：交付 Albedo 的樹皮平均約 (60, 54, 45)、苔約 (47, 50, 31)（GT01：樹皮 (53, 50, 42)、苔 (50, 55, 32)）。苔在引擎裡亮面容易偏螢光，所以比 GT01 略暗略灰。
- **樹皮分四組貼圖。** 這件寬 38 m，專案匯入規則（`QingxiImportBudget`）把模型貼圖壓到最大 1024、crunch 壓縮；只用一張圖集時遊戲裡只有約 22 px/m，15 m 外根是平滑的。拆成四組後照專案規則匯入約 45 px/m，樹皮紋看得到（見 `DR01_RootArch_unity_import_compare.jpg`）。整條根分到同一組，四組比例相同。
- 烘焙是「互不相鄰的根分一組，每組只對自己的高模」，避免射線打到隔壁的根。
- 所有 UV 島同比例、同方向，共用的樹皮細節貼圖可以直接用 URP Lit 的 Detail Map 沿 UV0 重複。Albedo 的 alpha 是細節遮罩（苔上只留 35%，葉子不疊）。UV1 是每 2.6 m 重複的樹皮 UV。
- `Detail_DR01_Plants`：一片片立體葉，不用葉片卡；葉柄是同一個網格裡的細長條，關掉 Detail_ 時不會留下浮在空中的葉子。葉子用 A 組圖集最下面一條，另一個材質，引擎裡開雙面（Render Face: Both）。

**審圖**（`art/previews/d2-roots-b/DR01_RootArch/`）

- `DR01_RootArch_vs_concept_V2.jpg`：設定圖 V2、遊戲模型同鏡位（加陪襯）、Unity 單件，三張並排。中間那張的神木、蕨、石頭、路和霧是陪襯（`art/source/d2-roots-b/preview_context.py`），只為了看拱洞有沒有框住神木，不是交付物件。沒有陪襯的同鏡位圖是 `DR01_RootArch_LOD0_V2cam.png`。
- `DR01_RootArch_unity_import_compare.jpg`：Unity 裡照專案匯入規則和交付原檔的差別（近看樹皮）。
- `DR01_RootArch_LOD0_vs_LOD1_nodetail.jpg`：LOD0、LOD1（關掉 Detail_*）、LOD2 同角度。
- `turnaround/`：十個方位各一張（1024×1024）和 `views.json`；`DR01_RootArch_turnaround_sheet.jpg` 是總覽。
- `unity/`：Unity 檢查報告 `report.txt` 和截圖（`*-rawimport.png` 是不套專案匯入規則的對照）。Unity 審圖的光和遊戲世界一樣（`QingxiWorldBuilder.Lighting()`：太陽 1.25、角度 (50, −35, 0)、三色環境光），另加淡霧。

**已知問題（還沒到驗收線）**

1. **和設定圖 V2 同鏡位比，自評約 83%**：南拱是設定圖的圓環，拱洞裡多看得到北拱一圈；設定圖沒畫後面的隧道。其餘差距：設定圖的樹皮更灰、地衣更多，根身上的蕨和葉叢更密；森林、地面、石板路和真正的神木不屬於這件。和北入口的差別主要在走近、斜角和隧道裡才看得出來，從正南第一眼仍是圓拱。
2. **整體自評約 89 分（v004 約 86），沒到 95。** v005 修掉了俯視的梯子、側面的橫梁和平行直條的氣根。還差的：遊戲模型裡兩側交叉成 X 的斜根從正東看仍像兩根略彎的木頭；氣根細，遠看幾乎看不到；面數比 v001 多約兩成、碰撞殼 8,436 面；紋素密度降到約 71 px/m（進遊戲約 36 px/m），15 m 外樹皮紋比 v003 淡。
3. **沒有放進 D2 場景。** 「從南邊看框住神木」只用替身看過；神木的實際位置、大小、場景的光和霧都還沒對過。
4. 樹皮近看（2 m 內）有一兩處烘焙島接縫看得出顏色差；LOD2 有一兩條地面細根被壓扁，遠景才用。
5. Unity 裡照專案匯入規則，苔在 2 m 內近看有 crunch 壓縮的方塊感。
6. 五個材質（本體四組貼圖＋葉子）。這是為了在 1024 上限下保住樹皮；如果核心組讓 D2 大件用 2048，可以併回兩組。沒有量過幀率。
7. 沒有混 `jolcham_oak_bark_01`（工作包寫「可以」）。
8. 核心組 11/16–11/17 也做了 DR01（v1–v3）、DR02 A/B/C、DR06、DR07 和 V2 入口構圖（分支 `art/core-1114-d2-altar-terrace`，只有高模預覽）。和這件重疊，誰的版本進場景要由組裡決定。

**重建**

在開著的 Blender 5.2 裡（Blender MCP 或文字編輯器）：

```python
exec(open('art/source/d2-roots-b/game_dr01.py', encoding='utf-8').read()); run_all()      # 高模 → 低模 → 烘焙（約 20 分鐘）→ LOD、碰撞 → FBX／GLB
exec(open('art/source/d2-roots-b/report_dr01.py', encoding='utf-8').read()); report()     # 量尺寸、FBX 回匯、十視圖、審圖、model_info／validation
```

只改了貼圖後處理（苔、地衣的顏色）時：`finish_textures()`，約 30 秒，不用重烘。

先跑 `report()` 再跑 Unity 檢查（Unity 檢查拿 `model_info.json` 比對）。掃描貼圖不進版本庫：從 Poly Haven 下載 `bark_brown_02` 2k（diff、nor_gl、rough、ao、disp），放到環境變數 `DR_TEX` 指的資料夾。Unity：`UNITY=<Unity.exe> sh art/source/d2-roots-b/unity/run_unity_check.sh`（約 3 分鐘，跑完會自己清掉暫存檔和 Unity 自動改的設定）。
