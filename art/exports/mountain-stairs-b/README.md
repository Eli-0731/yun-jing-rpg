# 承天｜2026-11-07 工作包第二部分：SG01–04 山城大石階＋30 m 之字形組裝

| 項目 | 內容 |
|---|---|
| 誰做的 | B（joshsu54） |
| 工作包 | docs/execution/2026-11-07/B-104h-tea-wheel-and-mountain-way.md（第二部分 SG01–04；檔案在 `feature/qingxi-creek-chapter` 分支） |
| ID | SG01 山城大石階直段、SG02 轉折平台、SG03 石欄杆套件（直段／斜段／轉角柱／端柱）、SG04 半途歇腳石亭；30 m 之字形組裝 |
| 分支／PR | art/b-1107-sg-mountain-stairs ／ 未開（#79 已合併；同時只開一張待審 PR，SG 排第一張） |
| 版本 | 全部 v001（首次交付，沒有舊版） |
| 狀態 | Exported ／ Imported（Unity 編輯器批次檢查）／ Visually Verified；In-game Verified：未驗 |
| 素材來源 | 原創（Blender 程序化建模）；三視圖參考由 Codex image_gen 生成，只當外形參考，尺寸照世界常數。組裝用到的 SectGate（Dondon 既有，未修改）與 G01 石燈（qingxi-day12-c 既有）只是擺放 |

SG01 樣品經 z1nnz 回覆「可以」後，照同樣做法做了 SG02–04 與組裝。
**沒有改主場景、沒有改區塊 JSON、沒有宣稱已正式落位。** 組裝只是 Blender 裡的樣品場景，加上一份 `stair-assembly.json`。新東西只做在 Unity 用的模型裡，沒有新增網頁版（PWA）頁面。SectGate 只放在原點，沒有改它。

## 進度

| ID | 名稱 | Exported | Imported（Unity 編輯器） | Visually Verified | In-game Verified |
|---|---|---|---|---|---|
| SG01_StraightRun | 山城大石階直段 | 是 | 是 | 是 | 否 |
| SG02_Landing | 轉折平台 | 是 | 是 | 是 | 否 |
| SG03_RailStraight | 石欄杆直段 | 是 | 是 | 是 | 否 |
| SG03_RailSloped | 石欄杆斜段（配 SG01） | 是 | 是 | 是 | 否 |
| SG03_PostCorner | 欄杆轉角／中間柱 | 是 | 是 | 是 | 否 |
| SG03_PostEnd | 欄杆端柱（雲頭） | 是 | 是 | 是 | 否 |
| SG04_RestShelter | 半途歇腳石亭 | 是 | 是 | 是 | 否 |
| 30 m 之字形組裝（接 SectGate） | — | 是（`stair-assembly.json`） | 部分（Unity 只測了 SG01＋SG02＋兩支 SG03 斜段的組合） | 是（Blender 六張） | 否 |

**未驗**：
- 手機效能：沒有量測，不寫 FPS。
- 真人用鍵鼠走樓梯。
- 放在正式地形上的落位。
- 在 Unity 裡沿整條 30 m 連續行走。

Unity 的走路測試是在編輯器裡用 CharacterController.Move 推一個 1.75 m 膠囊，不是進遊戲跑。

## 全批數量（物件、材質、貼圖）

每件每級 LOD 都是 2 個物件（Main＋Detail_Small）、1 個材質、1 張 atlas；另有 1 個碰撞物件，不渲染。

| ID | 尺寸（m） | LOD0／LOD1／LOD2 三角面 | 碰撞三角面 | 貼圖（px） | 接口 |
|---|---|---|---|---|---|
| SG01_StraightRun | 3.0 × 3.216 × 2.06 | 30,832／15,414／4,622 | 192 | 2048 | 8 |
| SG02_Landing | 4.0 × 4.0 × 0.755 | 22,452／11,225／3,367 | 24 | 2048 | 13 |
| SG03_RailStraight | 1.61 × 0.248 × 0.901 | 3,182／1,591／475 | 12 | 1024 | 2 |
| SG03_RailSloped | 0.262 × 3.06 × 2.333 | 7,230／3,613／1,083 | 60 | 2048 | 3 |
| SG03_PostCorner | 0.255 × 0.257 × 1.202 | 1,012／505／150 | 12 | 1024 | 5 |
| SG03_PostEnd | 0.261 × 0.26 × 1.363 | 3,200／1,600／478 | 12 | 1024 | 5 |
| SG04_RestShelter | 4.0 × 2.975 × 3.961 | 49,064／24,531／7,358 | 84 | 2048 | 3 |

- 貼圖：每件 5 張同尺寸 PNG：
  - `_BaseColor`（sRGB）、`_Normal`（OpenGL +Y）、`_MetallicSmoothness`（URP Lit 用）。
  - `_Roughness`、`_Metallic`：給其他引擎／GLB 用，Unity 材質沒有引用。
- LOD1／LOD2 是 LOD0 的 50%／15%；`minTier: standard`。
- Detail_Small（青苔、小草、地衣）每級都是獨立物件，關掉後外形不變。
- 交付位置（每件同 SG01 的放法）：FBX／GLB／貼圖／model_info.json／validation.json／qa 在 `art/exports/mountain-stairs-b/<ID>/`；十方位、線框、LOD 對照、Detail 關閉對照、人形尺四向在 `art/previews/mountain-stairs-b/<ID>/`；可編輯 .blend 在 `art/source/mountain-stairs-b/blend/<ID>_v001.blend`；生成腳本 `sg_landing.py`（SG02）、`sg_rail.py`（SG03）、`sg_shelter.py`（SG04），由 `build_mountain_stairs_b.py` 建模＋匯出＋驗證。
- 組裝場景用量：SG01 ×19、SG02 ×19、SG03_RailSloped ×38、SG03_RailStraight ×76、SG03_PostCorner ×57、SG03_PostEnd ×38、G01 ×19、SG04 ×1、SectGate ×1。

## SG02_Landing 轉折平台（v001）

- 參考：`art/references/SG02/` 的 candidate-01（選圖理由在 `prompt.txt`）。
- 尺寸：4 × 4 m、厚 0.4 m，走面水平在 z 0.4。原點在底部中心；正面 -Y。
- 構造：
  - 外圍：一圈 0.4 m 寬的收邊石（全高）。
  - 中間：3 × 3 塊 0.15 m 厚大石板，接縫 8 mm、填土長苔，中間十字被腳磨亮。
  - 燈座：+X +Y 角一座蓮瓣圓燈座（直徑 0.86 m、高 0.375 m、16 瓣），頂面 `Socket_Lantern` 放現成 G01 石燈。
  - 修補：-Y 面一塊收邊石用兩支鐵鋦釘補著，鋦釘嵌在鑿進石面 12 mm 的槽裡。
- 接口：
  - `Socket_Edge_S/N/E/W`：四邊中點、z 0.4、朝外；SG01 的 Socket_Top／Socket_Bottom 對上即可。
  - 8 個 `Socket_Post_*`：離外緣 0.2 m，給 SG03 的柱。
  - `Socket_Lantern`：燈座頂面中心。
- 碰撞：4 × 4 × 0.4 的盒子加燈座，24 三角面。

## SG03 石欄杆套件（v001，四件）

- 參考：`art/references/SG03/` 的 candidate-01（圓扶手、兩塊小墊塊、框邊板心、地栿）。端柱用 candidate-04 的雲頭。
- 世界常數：欄杆頂要高出走面 0.9–1.05 m。直段扶手頂 0.9 m；斜段扶手頂高出 SG01 踏步前緣線 1.02 m。
- 柱的規格：
  - 0.2 m 方柱身、0.26 m 柱座。
  - 下方 0.14 m 方榫、長 0.095 m，插進 SG01／SG02 的 0.15 m 柱孔，每邊留 5 mm。
  - 柱身四面保持平面；欄杆兩端各伸進柱面 5 mm，所以接縫是閉合的。
- **SG03_RailStraight**：一跨，柱中心距 1.8 m，本身不帶柱。`Socket_Post_A/B` 在兩端柱中心。
- **SG03_RailSloped**：配 SG01 一整段，三根柱加兩跨斜欄。
  - 柱腳照 SG01 的柱孔位置。中柱的柱座沿坡度鋸斜，比端柱長 0.14 m。
  - 板心的框邊沿坡度剪切。
- **SG03_PostCorner**：方帽，平台轉角與邊中點共用同一個模型。
- **SG03_PostEnd**：雲頭端柱，用在接樓梯口的角。三瓣雲頭兩面每瓣各刻一圈圓渦。

## SG04_RestShelter 半途歇腳石亭（v001）

- 參考：`art/references/SG04/`（選圖理由在 `prompt.txt`）。
- 尺寸：4.0 × 2.975 × 3.961 m。
- 背面與右側就是山壁本身，不是砌牆：
  - 表面分成高窄的裂面，每面是一個傾斜平面。
  - 裂縫是約 0.1 m 寬的折線，另外加了大範圍起伏和近垂直的節理溝。
- 左前兩根石柱、雲紋額枋、單坡筒瓦屋頂；簷下淨高 ≥ 2.6 m。
- 內部：
  - 0.45 m 高的長石凳，右端斷過、用淺色石補上。
  - 左側石盆，竹筧從岩縫伸出，細水流進盆裡。
  - 地面是 0.06 m 厚的石板。
- 石凳左端離石盆 0.6 m。原本只有 0.46 m，比人形直徑 0.5 m 窄，Unity 測到人形會卡在縫裡、被抬高 0.37 m，所以把石凳整體右移 0.14 m。
- 接口：`Socket_Front`（開口邊、朝外）、`Socket_Seat`（凳面）、`Socket_Basin`（盆口）。
- 碰撞：84 三角面（地面、山壁、柱、凳、盆）。
- 背面的山壁在組裝裡貼著山坡，做得比較平。如果在空地上單獨擺放，背面看起來會是一整片平的岩板。

## 30 m 之字形組裝

- 擺放資料：`art/exports/mountain-stairs-b/assembly-20261108/stair-assembly.json`。
  - 每件有 `id`、`position_m`、`rotation_z_deg`（Blender 軸；Unity = x, z, y），另附路線點 `route_m`。
  - **這只是樣品擺法，不是遊戲場景的正式落位。**
- 走法：
  - SectGate 在原點，起點 (0, 3, 0)。
  - 19 段 SG01，每段升 1.6 m，方向照北、西、北、東輪流轉。
  - 每兩段之間一個 SG02，最上面再一個 SG02 收頭；頂面 z 30.4 m。
- 欄杆與擺件：
  - 每段 SG01 兩側各一支 SG03_RailSloped。
  - 平台上沒有接樓梯的邊放直段欄杆；轉角與邊中點放 PostCorner，靠樓梯口的角放 PostEnd。
  - 每個平台的燈座上一座 G01。
  - SG04 在第 9 個平台（14.4 m）靠山那邊，開口那邊不放欄杆。
- 石亭那個平台的燈座正好在石亭右柱前面：四個角不是靠樓梯就是靠石亭，靠石亭最不擋路，開口還剩 2.5 m。
- 量測：結果在 `assembly-checks.json`，是在擺好的網格上打射線量出來的，不是抄設計數字。
  - 階高：190 階，每階 0.1591–0.1635 m（規則 0.15–0.18 m、彼此差 ≤ 8 mm）。
  - 踏面深：152 處，0.3196–0.3206 m。
  - 淨寬：57 處，2.385–2.399 m。
  - 樓梯頂與平台的高低差：19 處，最大 3.5 mm。
  - 欄杆接縫：152 處（直段兩端對柱面），全部閉合，最大 −4.78 mm（負數＝欄杆伸進柱裡）。規則是 ≤ 2 mm；沒有對不到柱的端點。
- 渲染：`art/previews/mountain-stairs-b/assembly-20261108/`，共六張（鳥瞰、側面、山門、半途、石亭、從頂往下看）。
  - 山坡是佔位用的高度場，不是地形素材。它在每件周圍往下切，讓樓梯看起來切進山坡。
  - 三個 1.75 m 紅色人形，分別站在山門、半途、頂端。
- 可編輯檔：`art/source/mountain-stairs-b/blend/assembly_mountain_stairs_b_v001.blend`；腳本 `assembly_mountain_stairs_b.py`。

## 檢查結果（SG02–04）

- Blender `validation.json`：全部通過。檢查項目：
  - SG02：走面水平（每點取 3 cm 內 5 條射線中最高的一條，代表腳掌跨過接縫）、四邊外緣齊平、13 個接口。
  - SG03：
    - 扶手頂高度。
    - 欄杆端伸進柱面。
    - 斜段柱腳對準 SG01 柱孔（讀 SG01 的 model_info 比對）。
    - 扶手高出踏步前緣 0.9–1.05 m。
    - 榫頭放得進柱孔。
  - SG04：簷下淨高 ≥ 2.6 m、額枋下淨高 ≥ 2.3 m、凳面 0.45 ± 0.015 m、地面 0.06 ± 0.006 m、可用深度、接口。
  - 每件都有：LOD 比例、FBX 回匯尺寸誤差 0 mm、FBX 含 LOD0/1/2＋碰撞＋接口、GLB、十方位。
- 網格 QA（各件的 `qa/` 資料夾）：
  - 全部為 0 的項目：退化三角面、同向共面（1 mm、0.5 mm、0.1 mm）、反向封閉件、未烘焙黑面、浮空件。
  - 警告（接受）：
    - 雙面共面：SG02 66 對、SG04 605 對。都是相鄰石塊在接縫裡背對背的兩面，看不到。
    - 零面積 UV（只在 1e-8 這一級）：SG02 1 個、SG04 20 個，其餘件 0。
    - UV 重疊：
      - SG02：1 對、6 texel。
      - PostEnd：2 對、5 texel。
      - SG04：23 對、113 texel。
      - RailSloped：12 對、265 texel（2048² 的 0.006%）。來源是斜板心的凹框沿坡剪切後留下的細三角片，和旁邊同一塊石面重疊，烘出來是同一片石頭的顏色。已改成凸包打包（663 → 265 texel），剩下的沒有再處理。
- 背面檢查：八個方向的紅色（背面）比例最多 0.19%（SG02）。

## Unity

Unity 6000.0.85f1（URP）`MountainStairsModelCheck`：**89 項 PASS、0 FAIL**（7 件加一組組合）。

- 每件都檢查：
  - 匯入尺寸與邊界誤差 0.0 mm。
  - LODGroup 三級；三角面數與物件數等於 model_info；Detail_Small 每級獨立。
  - MeshCollider；沒有錯誤著色器；接口位置誤差 0.0 mm。
- 走路（1.75 m CharacterController，半徑 0.25 m、跨步 0.3 m）：
  - SG01：三條線都走上頂階。
  - SG02：兩個方向橫越接縫，腳高一直是 0.42 m。
  - SG03 直段：推向欄杆的人停在欄杆前。
  - SG04：x 0.4 這條線走進去，停在石凳前；x −0.6 這條線從石盆和石凳中間走到山壁腳。兩條線腳高都一直在地面 0.08 m。
- 組合（SG01＋SG02＋兩支 SG03 斜段）：
  - SG02 的 Socket_Edge_S 對 SG01 的 Socket_Top，誤差 0.0 mm。
  - 六根柱對六個柱孔，誤差 0.0 mm。
  - 人從 SG01 走上 SG02。
  - 在樓梯上往側邊推，人留在側欄與欄杆內。
- 截圖在 `artifacts/mountain-stairs-unity/`（本機產物，不提交）。
- 跑完 Unity 後，已還原 85f1 改到的 ProjectSettings、Packages、DefaultPrefabObjects、WebGLTemplates.meta，沒有提交。

## 與既有件一致的三點

1. 石色：沿用 SG01 的青灰花崗岩組（`sg_parts.palette()`），平台、欄杆、石亭石柱放在一起色調一致；青苔與小草只長在背光面和接縫。
2. 接口：照 SG01 的做法。柱孔 0.15 m、深 0.1 m；SG02 邊接口的高度等於 SG01 頂階；SG03 的榫頭直接插進 SG01／SG02 的孔，不用另外對位。
3. 管線：與 SG01 相同。一個材質一張 atlas、Detail_Small 分開、LOD 50%／15%、碰撞用簡化稜柱，另有十方位圖與人形尺四向灰模／材質對照。

## 自評（SG02–04）

六項各 100 分，加權比例 25／20／20／15／10／10：

| ID | 外形 | 拓撲 | 材質 | 風格 | 動畫互動 | 效能匯出 | 加權 |
|---|---|---|---|---|---|---|---|
| SG02_Landing | 95 | 96 | 95 | 95 | 96 | 95 | 95.3 |
| SG03（四件） | 95 | 96 | 95 | 96 | 96 | 96 | 95.6 |
| SG04_RestShelter | 95 | 95 | 95 | 95 | 96 | 95 | 95.1 |

修正過的地方：
- 斜段欄杆的板心被布林運算切壞。原因：剪切做在平面夾緊之前，夾緊又把形狀拉平。改法：先夾緊再剪切，凹框改用十字形切刀。
- SG02 走面兩次判定不平。原因：收邊石的缺角，以及射線打進 3 mm 接縫。改法：收邊石不做缺角，檢查改成取 5 條射線中最高的一條。
- SG02 的鋦釘和外緣青苔凸出 4 m 範圍，被尺寸限制壓平在石面上，造成 1 mm 內同向共面 24 對。改法：鋦釘嵌進石面的槽，外緣不長青苔。
- 組裝的欄杆接縫最大 3.24 mm。原因：柱身的鑿面讓接欄杆的那面凹進 4–10 mm。改法：柱身四面保持平面（柱座、柱帽仍保留鑿面），現在接縫全部閉合。
- SG04 的山壁改過三版：疊方塊會漏光 → 太光滑 → Voronoi 裂面。裂面在網格上又出現鋸齒狀的「像素階梯」，最後改成柔性選面，讓裂縫成為約 0.1 m 寬的折線，並加上大範圍起伏和節理溝；右側前緣改成不規則的斷口。
- SG04 石凳與石盆之間 0.46 m 的縫會卡人 → 石凳右移，縫寬改成 0.6 m。
- SG04 從 7.5 萬面降到約 4.9 萬面（LOD0）：改了簷口做法、調整瓦列數。
- 組裝的佔位山坡原本蓋住低處的樓梯與石亭，而且沒有鋪到頂端 → 改成在每件周圍往下切，範圍延伸到 y 90 m。

還沒做的：
- LOD0 面數偏高：SG04 約 4.9 萬面、SG01 約 3.1 萬面。30 m 組裝一次看得到很多段時要靠 LOD1／LOD2，手機上未驗。
- SG04 背面不在組裝裡單獨擺放時，是一整片平的岩板。
- 組裝只在 Blender 裡量過；Unity 沒有擺出整條 30 m 讓人形連續走。

## SG01_StraightRun 山城大石階直段（v001）

- 參考：`art/references/SG01/20261108-threeviews-v001/STRAIGHT-RUN/candidate-03.png`；選圖理由與建模時改的地方寫在 `art/references/SG01/prompt.txt`。
- 尺寸：**3.0 × 3.216 × 2.06 m**（工作包：約 3 × 6 × 3 m、10 階）。原點在底部中心（地面 z = 0）；正面 -Y，往 +Y 爬升。
- 和工作包不同的地方：工作包寫「10 階、升 3 m」等於每階 0.30 m，超出世界常數（`docs/art/modeling-style-spec-v1.md` 第 4 節：高 0.15–0.18、深 0.28–0.32 m）。保留 10 階，改成每階高 0.16 m、深 0.32 m，一段升 1.6 m、水平 3.2 m、坡度 26.6°；30 m 之字形要靠多段串接。
- 構造：
  - 踏步：每階三塊錯縫整石，接縫避開 x = 0 與 ±0.95 m 三條走線；踏面中間被腳磨得比較平順（顏色較勻、稍微光滑）；第 6 階右側一塊較新、較淺的補石。
  - 側欄：兩側各 0.28 m，淨寬 2.4 m。青灰花崗岩整砌，底層一道凸出 2 cm 的勒腳；斜段的牆石是整塊石頭頂面沿坡度鋸平，沒有拉扯頂點。
  - 壓頂：每側兩塊順坡壓頂石（厚 0.2 m），兩端各一塊平頂端柱座石。
  - 柱孔：每側 3 個 0.15 m 方孔，孔底平、深 0.1 m，水平間距 1.4 m。兩端柱孔在平頂上（頂面高出踏步前緣線 0.4 m）；中段柱孔開在斜壓頂上（高出 0.26 m），所以 **SG03 斜段的中柱柱腳要切斜、比端柱長 0.14 m**。
  - 青苔、小草只長在右側（背光側）的牆縫、踏面內角和壓頂接縫。
- 接口（空物件）：`Socket_Bottom`（第一階前緣地面，z 0）、`Socket_Top`（頂端 y +1.6、z 1.6，接 SG02 平台頂面）、`Socket_Post_L0..2`／`R0..2`（柱孔底中心上方的頂面高度）。

#### 每級 LOD 實際數字（model_info.json `budget_per_lod`）

| LOD | 三角面 | 物件數 | 不含 Detail 的物件 | 材質數 |
|---|---|---|---|---|
| LOD0 | 30,832 | 2（Main＋Detail_Small） | 1 | 1 |
| LOD1 | 15,414（50.0%） | 2 | 1 | 1 |
| LOD2 | 4,622（15.0%） | 2 | 1 | 1 |

- Main 27,878／13,938／4,180；Detail_Small（青苔、小草）2,954／1,476／442。
- `minTier: standard`；`detailObjects: ["SG01_StraightRun_Detail_Small"]`，關掉後外形不變（`SG01_StraightRun_LOD0_LOD1_no_detail.png`、Unity `SG01_StraightRun_close_no_detail.png`）。
- 碰撞：`SG01_StraightRun_Collision`，10 階＋兩側欄的稜柱，192 三角面。

#### 貼圖（全部 2048 × 2048，同一張 atlas）

| 檔案 | 用途 |
|---|---|
| `SG01_StraightRun_BaseColor.png` | 顏色（sRGB） |
| `SG01_StraightRun_Normal.png` | 法線（OpenGL +Y） |
| `SG01_StraightRun_MetallicSmoothness.png` | URP Lit 用（R metallic、A smoothness） |
| `SG01_StraightRun_Roughness.png`、`SG01_StraightRun_Metallic.png` | 其他引擎／GLB 用；Unity 材質沒有引用 |

#### 檢查結果

- Blender `validation.json`：15 項全部通過。都是對匯出的 LOD0 打射線量出來的，不是抄設計數字：
  - 10 階等高：三條走線各 10 階，每階高 0.1589–0.1616 m。
  - 踏面等深：0.3195–0.3206 m。
  - 淨寬：2.385–2.407 m。
  - 頂階與平台齊平：1.5997–1.6 m。
  - 斜壓頂上方沒有任何東西凸出：每側 3 條線、每 2 cm 一點，0 點超出。
  - 其他：8 個接口都在、LOD 比例 50%／15%、FBX 回匯尺寸誤差 0 mm、FBX 含 LOD0/1/2、碰撞、接口、GLB、十方位。
- 網格 QA（`qa/qa_mesh.json`、`qa/qa_fbx.json`）：
  - 全部為 0：退化三角面、零面積 UV（1e-12～1e-8）、同向共面（1 mm、0.5 mm、0.1 mm）、反向封閉件、未烘焙黑面、浮空件。
  - 警告（接受）：
    - FBX 雙面共面 75 對，都是相鄰石塊在 2 mm 接縫裡背對背的兩面，看不到、不會閃爍。
    - UV 重疊 5 對、共 6 texel（每對 1–2 texel）。
- 背面檢查（Unity 會剔除背面）：八個方向紅色（背面）最多 0.05%。
- Unity 6000.0.85f1（URP）`MountainStairsModelCheck`：SG01 的 14 項 PASS（全批結果見上方「Unity」）。
  - 匯入尺寸與邊界誤差 0.0 mm；LODGroup 三級；三角面與物件數等於 model_info；Detail_Small 每級都是獨立物件。
  - MeshCollider，射線打得到碰撞；沒有錯誤著色器；8 個接口位置誤差 0.0 mm。
  - 1.75 m CharacterController（半徑 0.25、跨步 0.3 m）在 x = −0.85／0／0.85 三條線都從地面走上頂階（終點 y 1.62 m）。
  - 截圖在 `artifacts/mountain-stairs-unity/`（本機產物，不提交）。
- 跑完 Unity 後已還原 85f1 改到的 ProjectSettings、Packages、DefaultPrefabObjects，沒有提交。
- **未驗**：手機效能（沒有量測，不寫 FPS）、真人操作、正式地形。

#### 交付位置

| 項目 | 位置 |
|---|---|
| 可編輯 .blend | `art/source/mountain-stairs-b/blend/SG01_StraightRun_v001.blend` |
| 生成腳本 | `art/source/mountain-stairs-b/sg_parts.py`（石階）、`build_mountain_stairs_b.py`（建模＋匯出＋驗證）、`ruler_views.py --four`、`pair_sheets.py`；共用的 `ti_*`、`cr_*`、`mk_mats.py`、`qa_*.py`、`backface_check.py` 從 tea-terraces-b 複製（`cr_mats.py` 的 stone() 多了踏面磨亮參數） |
| FBX／GLB／貼圖 | `art/exports/mountain-stairs-b/SG01_StraightRun/SG01_StraightRun_v001.fbx`、`.glb`、`Textures/` |
| model_info.json／validation.json／qa | 同資料夾 |
| 十方位、線框、LOD 對照、Detail 關閉對照 | `art/previews/mountain-stairs-b/SG01_StraightRun/` |
| 1.75 m 人形四向（正、側、背、3/4），灰模與材質同光同角度 | `ruler_0{1..4}_*_{grey,material}.png`、並排 `compare_0{1..4}_*_grey_material.png` |
| Unity 檢查 | `apps/game/Assets/YunJing/Editor/MountainStairsModelCheck.cs` |

#### 自評

六項（各 100 分）：外形與輪廓 95、拓撲與結構 96、材質與光影 95、風格一致 95、動畫互動 96、效能匯出 95。加權（25／20／20／15／10／10）95.3。

修正過的地方：
- 第一版側牆的斜頂是把方石頂點硬壓成斜的，出現翻面與細縫 → 改成整塊石頭沿坡度鋸頂。
- 踏面有 ±2 cm 的高低差（頂面也做了鑿面） → 頂面改平，現在每階差 3 mm 以內。
- 中段柱座原本是一塊平石擱在斜壓頂上，看起來像箱子 → 拿掉，柱孔直接開在斜壓頂。
- 斜壓頂兩側各有兩塊牆石的平頂凸出壓頂 → 只要有一部分高過坡線就鋸頂，並加了「斜壓頂上方沒有凸出」的檢查。
- 端柱座下有 4–5 cm 的薄片石 → 最上一層吃掉剩餘高度。
- 牆面青苔浮在鑿面前 → 每團都先打射線貼到實際石面。
- 踏面在成品圖裡偏白 → 降低磨亮層的亮度與光滑度，改成暖灰。

還沒做的：
- 踏步前緣的缺角只有少數幾處。
- LOD0 三萬面偏多：之字形一次看得到很多段時要靠 LOD1／LOD2，手機上未驗。

## 工時

- SG01：約 1.1 小時，2026-11-08 02:26–03:31（台灣時間，照對話紀錄的時間），含 SG01–04 三視圖生成與選圖、建模、修正和 Unity 檢查。
- SG02–04＋組裝：約 1.9 小時，2026-11-08 10:30–12:25（台灣時間，照對話紀錄的時間），含建模、三輪修正（接縫、石亭卡人、山壁鋸齒、平台鋦釘）、組裝量測與渲染、Unity 檢查。
