| 項目 | 內容 |
|---|---|
| 誰做的 | C（Eli-0731） |
| 工作包 | docs/execution/2026-11-07/C-128h-creekside-and-village-life.md 第二部分 A（LV01–LV12）與 D（十二件並排） |
| ID | LV01–LV12（本批新增 LV07–LV12） |
| 分支／PR | LV01–LV06：[#116](https://github.com/z1nnz/chengtian/pull/116)；LV07–LV12：art/c-1110-lv07-12-village-life ／ [本批 PR](https://github.com/z1nnz/chengtian/pulls?q=is%3Apr%20author%3AEli-0731%20head%3Aart%2Fc-1110-lv07-12-village-life) |
| 版本 | v001（檔名帶 `_v001`；之後改版另存 v002，不覆寫） |
| 狀態 | Exported ／ Imported（Unity 6000.3.28f1 獨立匯入檢查）／ Visually Verified（Blender 與 Unity 審圖）／ In-game Verified：未驗（沒放進正式場景） |
| 素材來源 | 原創；三視圖參考在 `art/references/LV01/`–`art/references/LV12/` |

# 青溪村裡生活小物 LV01–LV12

LV01–LV06 已由 #116 合併；本批新增 LV07–LV12，並完成十二件並排。工作包第二部分 A 的十二件：讓 A1 青溪村各戶門口、院子、牆邊有一點生活的東西。靜態擺設，沒有玩法、碰撞或動畫；擺進世界由核心組做。

**共同做法**
- 先生成三視圖（每件 4 張）、自評選一張（分數和取捨在各自的 `prompt.txt`），再做灰模（`art/previews/village-life-c/<ID>/clay/`），最後上貼圖。一件只專心練工作包寫的那一兩個技巧。
- 原點在腳印中心、底部 z = 0，Blender −Y 是正面（FBX／Unity 是 −Z）。不附地面底板。
- 一件一個材質、一套 1024 貼圖；可有可無的小東西放 `Detail_*` 子物件（標準畫質關掉），本體的環境遮蔽烘焙時不含 Detail_。
- LOD1 約 50%、LOD2 約 15%，LOD0 不減面；LV09 的 LOD1 為 60%，保留籠條輪廓，LOD2 改用 alpha clip。`minTier` 都是 `high`（畫質分級第 4 節：增加豐富度的擺設，不擋路、不參與玩法），所以沒有碰撞。
- 建模流程和 creekside-life-c（WL、FI）相同，共用那裡的工具（`wl_kit.py`、零件函式、審圖相機 `render_wl.py`），這裡只放 LV 自己的物件和建模腳本。
- 重建：`blender -b --factory-startup -P art/source/village-life-c/build_lv.py -- LV01 [--clay]`；審圖與 QA：`BL=<blender> sh art/source/village-life-c/render_reviews.sh`；Unity：`UNITY=<Unity.exe 6000.3.28f1> sh art/source/village-life-c/unity/run_unity_check.sh`。

### LV01 竹編雞籠（倒扣的圓頂籠）（ChickenCoop，v001）

練「半球形的竹條排列、底部收邊」。22 條經向竹條從頂上麻繩結往下放射（越往頂越窄，避免在頂上互相疊住），7 圈緯向竹條一上一下穿過；底部一圈厚收邊，八處用麻繩綁住（繩子只繞外、上、內三面，兩端塞進收邊，不從地面下穿過）；頂上麻繩結加一個兩股絞成的提環；一條較新的補條綁在斷掉的竹條上。稻草卡在底部縫裡、兩根羽毛在收邊旁（Detail_）。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/LV01/`，選用 cand-3（92） |
| 尺寸（寬 × 深 × 高） | 0.8 × 0.798 × 0.575 m（上限 0.8 × 0.8 × 0.6 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 18,268 / 9,134 / 2,738（不含 Detail_：17,928 / 8,964 / 2,688） |
| 物件數（每個 LOD） | 3（本體 1 + Detail_Feathers, Detail_Straw） |
| 材質數 | 1（`M_LV01_ChickenCoop`，本體和 Detail_ 共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | high |
| 檔案 | `art/exports/village-life-c/LV01_v001.fbx`（LOD0–2）、`art/exports/village-life-c/LV01_v001.glb`（LOD0）、`art/source/village-life-c/LV01_v001.blend` |

### LV02 竹掃帚與木畚箕（BroomDustpan，v001）

練「細枝束成一把的輪廓、木板拼接」。cand-3 把掃帚畫成直立，但提示詞和工作包高度 0.3 m 都是平放，所以掃帚平躺在畚箕旁：64 根細枝（部分分叉，兩端收細）從綁好的芯末端散成扁扇形，三道麻繩綁住；竹柄有竹節，柄頂纏繩垂一段繩尾、中段一圈布用兩條繩交叉綁住。畚箕三片底板、兩片三角側板、後板和 ∩ 形握把（交叉麻繩綁住），底板角落釘一塊補板。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/LV02/`，選用 cand-3（90） |
| 尺寸（寬 × 深 × 高） | 1.32 × 0.386 × 0.234 m（上限 1.4 × 0.4 × 0.3 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 7,984 / 3,992 / 1,196（不含 Detail_：7,876 / 3,938 / 1,180） |
| 物件數（每個 LOD） | 3（本體 1 + Detail_Nails, Detail_Tail） |
| 材質數 | 1（`M_LV02_BroomDustpan`，本體和 Detail_ 共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | high |
| 檔案 | `art/exports/village-life-c/LV02_v001.fbx`（LOD0–2）、`art/exports/village-life-c/LV02_v001.glb`（LOD0）、`art/source/village-life-c/LV02_v001.blend` |

### LV03 靠牆的竹梯（BambooLadder，v001）

練「竹節、橫檔綁繩的重複節奏」。兩根粗竹竿下寬上窄、竹節間距不一；七根橫檔每個交點都用同一種綁法（竹竿上下各纏兩圈，再兩圈斜繞在正面交叉成 X）；第四根是換新的淺色竹橫檔；橫檔中段被踩得較暗、較滑，竿腳髒、帶一點苔。工作包尺寸深 0.1 m，所以模型是直立的，靠牆的角度在擺放時整件傾斜。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/LV03/`，選用 cand-4（93） |
| 尺寸（寬 × 深 × 高） | 0.495 × 0.081 × 2.381 m（上限 0.5 × 0.1 × 2.4 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 11,788 / 5,894 / 1,768（不含 Detail_：11,788 / 5,894 / 1,768） |
| 物件數（每個 LOD） | 1（本體 1 + 無） |
| 材質數 | 1（`M_LV03_BambooLadder`，本體和 Detail_ 共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | high |
| 檔案 | `art/exports/village-life-c/LV03_v001.fbx`（LOD0–2）、`art/exports/village-life-c/LV03_v001.glb`（LOD0）、`art/source/village-life-c/LV03_v001.blend` |

### LV04 竹編吊籃（掛著晾菜乾）（HangingBasket，v001）

練「淺籃和吊繩、裡面一點乾菜」。淺圓籃（直徑 0.46 m）是一個薄殼，竹篾的一上一下編織畫在貼圖上；籃緣一圈粗竹篾每 30° 用細篾綁住，一邊略垂；三條麻繩從籃緣打結往上收到一個繩結，再一個掛圈（總高 0.77 m）；籃裡四片乾菜葉、五根紅辣椒；籃側一塊灰布補丁。原點在籃底：單獨放是籃子著地、繩子立起，擺放時由核心組掛上。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/LV04/`，選用 cand-1（92） |
| 尺寸（寬 × 深 × 高） | 0.476 × 0.48 × 0.765 m（上限 0.5 × 0.5 × 0.8 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 5,306 / 2,652 / 794（不含 Detail_：5,110 / 2,554 / 766） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_Frays） |
| 材質數 | 1（`M_LV04_HangingBasket`，本體和 Detail_ 共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | high |
| 檔案 | `art/exports/village-life-c/LV04_v001.fbx`（LOD0–2）、`art/exports/village-life-c/LV04_v001.glb`（LOD0）、`art/source/village-life-c/LV04_v001.blend` |

### LV05 醃菜甕三個（大中小，有蓋、壓石）（PickleJars，v001）

練「和 BM03 陶罐不同：寬口、厚蓋、蓋上壓一塊石頭」。三個甕各自分開放、不焊在一起，輪廓都不同：大甕肩寬、中甕直身、小甕矮胖；都是寬口、口沿一圈未上釉的陶，蓋上厚陶蓋、壓一顆平滑的河石；大甕蓋緣缺一角。深褐釉面上從肩部往下的流痕、甕腳的濕土和苔畫在貼圖上。和 BM03 的並排在 `art/previews/village-life-c/compare/LV05-vs-BM03-*`。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/LV05/`，選用 cand-2（92） |
| 尺寸（寬 × 深 × 高） | 0.847 × 0.443 × 0.54 m（上限 0.9 × 0.5 × 0.6 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 3,990 / 1,994 / 598（不含 Detail_：3,990 / 1,994 / 598） |
| 物件數（每個 LOD） | 1（本體 1 + 無） |
| 材質數 | 1（`M_LV05_PickleJars`，本體和 Detail_ 共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | high |
| 檔案 | `art/exports/village-life-c/LV05_v001.fbx`（LOD0–2）、`art/exports/village-life-c/LV05_v001.glb`（LOD0）、`art/source/village-life-c/LV05_v001.blend` |

### LV06 劈柴木墩與柴刀（ChoppingBlock，v001）

練「年輪切面、刀砍的痕、刀插在木墩上」。木墩高 0.4 m、底部根部外撇成五瓣，淺色風化木帶直向灰紋，九片樹皮從根部往上、邊緣參差、上緣往外翹；頂面年輪切面（放射裂紋），交叉的刀痕畫在貼圖上；一把寬刃柴刀在自己的平面裡斜插進頂面（刃口後端埋 1.2 cm、前端 6 cm），木柄纏布、垂兩條布尾；腳邊三塊劈柴，木屑（Detail_）。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/LV06/`，選用 cand-4（93） |
| 尺寸（寬 × 深 × 高） | 0.479 × 0.544 × 0.514 m（上限 0.6 × 0.6 × 0.6 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 3,552 / 1,776 / 534（不含 Detail_：3,392 / 1,696 / 508） |
| 物件數（每個 LOD） | 3（本體 1 + Detail_Chips, Detail_ClothEnds） |
| 材質數 | 1（`M_LV06_ChoppingBlock`，本體和 Detail_ 共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | high |
| 檔案 | `art/exports/village-life-c/LV06_v001.fbx`（LOD0–2）、`art/exports/village-life-c/LV06_v001.glb`（LOD0）、`art/source/village-life-c/LV06_v001.blend` |

### LV07 葫蘆水瓢與木掛勾（GourdLadle，v001）

練「葫蘆對半剖的曲面、勾子」。瓢是一個梨形葫蘆沿長向剖開的一半：4 mm 厚的殼，剖口朝前，內面較深褐、較滑；瓢柄是葫蘆頸，頂端穿一個孔。四塊直板拼成的舊木板（板縫、兩顆鐵釘、上緣參差），一根短木樁斜插往上；麻繩圈穿過瓢柄的孔、打結後掛在木樁上（繩尾 Detail_）；瓢緣一道裂縫用三針細繩縫住（Detail_）。木樁下的水漬、木板上緣的苔畫在貼圖上。掛牆的東西：瓢底是 z = 0，木板背面平的、貼牆，擺放時整件移到牆上。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/LV07/`，選用 cand-1（93） |
| 尺寸（寬 × 深 × 高） | 0.301 × 0.154 × 0.499 m（上限 0.4 × 0.2 × 0.5 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 9,186 / 4,592 / 1,374（不含 Detail_：9,076 / 4,538 / 1,360） |
| 物件數（每個 LOD） | 3（本體 1 + Detail_Stitches, Detail_Tail） |
| 材質數 | 1（`M_LV07_GourdLadle`，本體和 Detail_ 共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | high |
| 檔案 | `art/exports/village-life-c/LV07_v001.fbx`（LOD0–2）、`art/exports/village-life-c/LV07_v001.glb`（LOD0）、`art/source/village-life-c/LV07_v001.blend` |

### LV08 斗笠與蓑衣掛在木架上（RainHatCapeRack，v001）

練「斗笠的圓錐、蓑衣的一層層草片」。斗笠是有厚度的淺圓錐殼，戴在方立柱頂上（柱角剛好頂住斗笠內面），竹篾編紋在貼圖上，緣口一圈參差的破篾（Detail_），頂上一個竹鈕；蓑衣五層草片，每層的上緣藏在上一層下面、下半往外張，越往下越寬，下緣剪成參差的草尾，前面開口看得到立柱；第一層的上緣收攏在柱上，用麻繩綁住，喉口一個蝴蝶結、兩條繩垂下帶穗；兩塊布補丁畫在貼圖上。木架：兩條橫腳、一根橫樑、柱腳兩塊楔木、柱下段纏三圈麻繩，兩根短木樁（右邊那根常用，較淺較滑）。工作包深度上限 0.4 m，斗笠只能做 0.38 m 寬（三視圖約 0.6 m）。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/LV08/`，選用 cand-2（93） |
| 尺寸（寬 × 深 × 高） | 0.711 × 0.391 × 1.6 m（上限 0.8 × 0.4 × 1.6 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 18,084 / 9,042 / 2,712（不含 Detail_：17,440 / 8,720 / 2,616） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_Fringe） |
| 材質數 | 1（`M_LV08_RainHatCapeRack`，本體和 Detail_ 共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | high |
| 檔案 | `art/exports/village-life-c/LV08_v001.fbx`（LOD0–2）、`art/exports/village-life-c/LV08_v001.glb`（LOD0）、`art/source/village-life-c/LV08_v001.blend` |

### LV09 竹鳥籠掛在短竿上（空籠）（BirdcagePole，v001）

練「圓柱細竹條、頂部提環」。籠身 36 根細竹條平均排一圈，上段彎進圓頂收到頂上的深色木鈕，三道橫箍（最下一道在門口斷開）；深色木底圈和籠底板；正面一扇小門（框和三根竹條）用細繩鉸著、往外開。「提環」：木鈕上一個鐵眼，竹環穿過鐵眼，竹環再掛在橫竿下的麻繩圈裡，三者真的互扣，彼此靠著（0.3 mm）。竹竿立在粗石塊裡，頂上一根橫竿、一根斜撐，都用麻繩綁；竿中段纏一塊舊布（垂下的布尾 Detail_）。空籠，沒有鳥。LOD2 改用一個 18 邊的圓柱加圓頂、竹條畫在貼圖上（alpha clip）：細竹條減面後會碎。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/LV09/`，選用 cand-4（93） |
| 尺寸（寬 × 深 × 高） | 0.387 × 0.298 × 1.172 m（上限 0.4 × 0.4 × 1.2 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 11,492 / 6,892 / 1,576（不含 Detail_：11,448 / 6,870 / 1,570） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_Cloth） |
| 材質數 | 1（`M_LV09_BirdcagePole`，本體和 Detail_ 共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | high |
| 檔案 | `art/exports/village-life-c/LV09_v001.fbx`（LOD0–2）、`art/exports/village-life-c/LV09_v001.glb`（LOD0）、`art/source/village-life-c/LV09_v001.blend` |

### LV10 草鞋與木屐各一雙（StrawSandalsClogs，v001）

練「小物件的比例、編織紋用貼圖表現」。照真實尺寸：草鞋長 0.24 m，木屐長 0.225 m、兩個齒高 3.4 cm。草鞋是一片平的鞋底加一圈粗草辮邊，鞋底的人字編紋、腳跟和前掌壓扁變深、草辮邊的斜紋都畫在貼圖上，不逐根建；木屐是一塊淺色舊木板、底下兩個齒，齒和板底沾泥、板面的腳印畫在貼圖上。四隻鞋都用同一種深藍布帶：兩條從腳趾的結拉到兩側，一根柱插進鞋底；結上散開的線頭是 Detail_。每隻鞋各自分開，兩雙稍微歪著放。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/LV10/`，選用 cand-1（92） |
| 尺寸（寬 × 深 × 高） | 0.382 × 0.255 × 0.089 m（上限 0.4 × 0.3 × 0.1 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 6,336 / 3,168 / 948（不含 Detail_：6,112 / 3,056 / 916） |
| 物件數（每個 LOD） | 2（本體 1 + Detail_Frays） |
| 材質數 | 1（`M_LV10_StrawSandalsClogs`，本體和 Detail_ 共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | high |
| 檔案 | `art/exports/village-life-c/LV10_v001.fbx`（LOD0–2）、`art/exports/village-life-c/LV10_v001.glb`（LOD0）、`art/source/village-life-c/LV10_v001.blend` |

### LV11 磨刀石座（長條石放在木凳上）（WhetstoneBench，v001）

練「石頭中間磨凹的形狀、木凳榫接」。磨刀石長 0.58 m，頂面沿長向磨成一道平滑的凹（中間深 4.6 cm，兩端高；橫向也略呈 U 形），兩側和端面是粗糙的斷面；凹面較亮、較滑。木凳：厚凳面，四隻腳的榫頭穿出凳面、比凳面高 3.5 mm 看得到方形端面；前後兩條牙板、兩側下橫檔都穿過凳腳。左端一個陶碗盛水，石頭下的濕痕畫在貼圖上；前牙板掛一塊布，後牙板上釘一塊斜補板。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/LV11/`，選用 cand-1（93） |
| 尺寸（寬 × 深 × 高） | 0.782 × 0.262 × 0.457 m（上限 0.8 × 0.3 × 0.5 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 9,006 / 4,502 / 1,350（不含 Detail_：9,006 / 4,502 / 1,350） |
| 物件數（每個 LOD） | 1（本體 1 + 無） |
| 材質數 | 1（`M_LV11_WhetstoneBench`，本體和 Detail_ 共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | high |
| 檔案 | `art/exports/village-life-c/LV11_v001.fbx`（LOD0–2）、`art/exports/village-life-c/LV11_v001.glb`（LOD0）、`art/source/village-life-c/LV11_v001.blend` |

### LV12 稻草蛋籃（籃裡墊稻草和幾顆蛋）（StrawEggBasket，v001）

練「籃的編織、稻草的亂、蛋的乾淨圓形」。小圓籃（直徑 0.31 m）是有厚度的殼，竹篾一上一下的編紋在貼圖上，粗籃緣和底圈都是整圈閉合的管；右前一側往內壓凹、那裡的籃緣稍低。籃裡一層稻草墊，64 根草尾從裡面翹出、跨過籃緣往外垂，少數直立彎下，26 根散草躺在草墊上。六顆奶白色的蛋（5.4–6.0 cm）都是平滑的蛋形、一頭稍尖，躺在草墊上，彼此不碰。籃側（背面）一塊布補丁畫在貼圖上。

| 項目 | 數字 |
|---|---|
| 三視圖 | `art/references/LV12/`，選用 cand-4（93） |
| 尺寸（寬 × 深 × 高） | 0.334 × 0.328 × 0.221 m（上限 0.35 × 0.35 × 0.25 m） |
| 三角面 LOD0 / LOD1 / LOD2 | 10,748 / 5,374 / 1,612（不含 Detail_：10,748 / 5,374 / 1,612） |
| 物件數（每個 LOD） | 1（本體 1 + 無） |
| 材質數 | 1（`M_LV12_StrawEggBasket`，本體和 Detail_ 共用） |
| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，1024×1024 |
| minTier | high |
| 檔案 | `art/exports/village-life-c/LV12_v001.fbx`（LOD0–2）、`art/exports/village-life-c/LV12_v001.glb`（LOD0）、`art/source/village-life-c/LV12_v001.blend` |

## 驗證

- QA（`tools/art/qa_lod0_basic.py` 嚴格與寬鬆、`tools/art/qa_contact_glb.py`）：十二件嚴格、寬鬆都是 0 項，結果在 `art/previews/village-life-c/qa/`。
- FBX 原始資料與回匯覆核：`blender -b --factory-startup --python-exit-code 1 -P art/source/village-life-c/verify_delivery.py`。檢查每個 LOD 的原始面數、物件／材質數、貼圖解析度、UV、回匯尺寸與底部原點；記錄在 `art/previews/village-life-c/qa/fbx-roundtrip.json`。
- Unity 6000.3.28f1 既有獨立匯入報告：`art/previews/village-life-c/unity/report.txt`，169 項 PASS（LV01–LV12）。本輪核對模型及報告一致，沒有重跑 Unity Editor；模型與 FBX 沒有修改。
- 同光同角度並排（含 1.75 m 人形尺，灰模和成品各一張）：`art/previews/village-life-c/compare/`。LV01／LV04 對 B 的竹篩 MK02、背簍 MK04；LV02／LV03 對 B 的柴堆 R03、C 的木樁 BM02_01；LV05 對 C 的陶罐 BM03_01–03；LV06 對 BM02_01、R03；`LV-set` 是 LV01–LV06 放在一起。LV07／LV11 對 BM02_01、R03；LV08／LV09 對 C 的晾藥架 TY08（工作包「不做已有的」：形狀要分得開）；LV10／LV12 對 MK02、MK04 和 LV04；`LV-set2` 是 LV07–LV12 放在一起。工作包第二部分 D 的十二件並排（兩排、配 1.75 m 人形）在 Unity 審圖 `art/previews/village-life-c/unity/LV-all-*.png`。

**和既有模型的三個共同點**
1. 材料一看就認得、帶使用痕跡：竹篾、竹竿、麻繩、舊木和陶都用 creekside-life-c 同一套來源貼圖，和 MK02、MK04 的竹編，BM02、R03 的木頭同一種畫法。
2. 同一組底色：舊木在暖褐、竹在麥稈黃到灰綠、陶是深褐釉加素陶、石在暖灰、草在金黃到灰綠；大塊柔和的深淺，只有少量筆觸。
3. 磨損有位置：接地的一側較暗、帶土和苔（雞籠收邊、竹梯腳、甕腳、木墩根部、木架和凳腳、石座），常摸、常踩的地方較亮或較暗、較滑（掃帚握處、橫檔中段）。

## 已知問題與未驗

- 正式場景擺放、手機上的效果都未驗。
- Blender 4.5.3 回匯 FBX 後，部分物件的 LOD1／LOD2 面數較原始檔少；逐項差異列在 `qa/fbx-roundtrip.json`。`model_info.json` 的面數與 FBX 原始資料、既有 Unity 匯入報告一致，沒有以 Blender 回匯數字覆寫它們。
- LV02：三視圖四張都把掃帚畫成直立，照提示詞和工作包高度改成平躺；綁好的那段芯看起來偏像一截光滑木頭。
- LV03：工作包尺寸深 0.1 m，模型是直立的；靠牆的角度要在擺放時整件傾斜。
- LV04：原點在籃底，單獨擺放是籃子著地、繩子立起；要掛起來時以頂上的繩圈為掛點。
- LV05：口沿未上釉的那圈大多被厚蓋擋住，近看才看得到。
- LV07：掛牆用，單獨放在地上是瓢底著地、木板懸空；擺放時以木板背面貼牆。水漬畫得淡，遠看不明顯。
- LV08：深度上限 0.4 m，斗笠只有 0.38 m 寬，比三視圖小；蓑衣的草絲紋在貼圖上，近看才分得出一根根。
- LV09：竹環、鐵眼和麻繩圈互扣，彼此間有 0.3 mm 的縫；LOD2 的竹條是貼圖（alpha clip），近看是平的，小門在 LOD2 也一起拿掉。
- LV10：鞋底編紋、草辮邊的斜紋都是貼圖，側面近看草辮是一條平滑的管。
- LV12：草墊頂面是一個淺碟，平滑，草的亂主要靠翹出的草尾；布補丁在背面。
