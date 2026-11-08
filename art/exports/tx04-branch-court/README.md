| 項目 | 內容 |
|---|---|
| 誰做的 | A（Johnnnny0823） |
| 工作包 | docs/execution/2026-11-05/A-48h-mountain-city-architecture.md（TX04；併入 docs/execution/2026-11-08/A-80h-mountain-city.md 第一部分） |
| ID | TX04 樣品：TX04-GATE 院門、TX04-WALL-ST 直牆（其餘 6 件等樣品過審再做） |
| 分支／PR | art/a-1105-tx04-branch-court ／ PR 待開 |
| 版本 | v001 |
| 狀態 | Exported；Imported／Visually Verified／In-game Verified：未驗（只有 Blender 預覽與 FBX 回匯檢查） |
| 素材來源 | 原創。建模腳本 `art/source/tx04-branch-court/build_tx04.py`，沿用 MC01（PR #80 已合併）的建模函式與共用貼圖；三視圖用 Codex CLI 生成，存 `art/references/TX04-*/` |

# TX04 太玄分院模組：樣品批

依 11/07 規則「一批很多件，先做一件樣品」：TX04 共 8 件（院門、直／角／門邊牆、正堂、廂房、院鋪地、石階）。先交**院門 GATE**和**一段直牆 WALL-ST**，請確認尺度、朱漆換色和空插槽的做法，過了再做其餘 6 件和分院組裝。

## 和 MC01 共用的部分

- **貼圖**：共用 MC01 的 2048 × 2048 Trim Sheet（`art/textures/mountain-street-houses-a/`）和 `M_MountainStreet_Trim`，分院和山城街屋可以合批。
- **語言**：沿用 #80 第三輪定下的中式山城語言：深色木、花崗白、黛瓦、銅件；不用短簾、圓紙燈、方格窗和斜撐。

## 換裝接口（D3 §5）

| 接口 | 做法 |
|---|---|
| `_Accent`（道統色） | 朱漆的部件合成 `TX04_<ID>_Accent` 物件，用 `M_TX04_Accent` 材質。<br>材質的底色是一個顏色參數（太玄預設 `#8E2F25`），乘在 Trim Sheet 的灰泥條上，所以換色後雨痕和磨損還在。<br>Unity 裡改 `M_TX04_Accent` 的 `_BaseColor` 就能換成其他道統色。 |
| 朱漆比例 | 每件的朱漆面積寫在 `model_info.json` 的 `accent.surfaceShare`，建模腳本會擋下超過 10 % 的件。<br>院門 2.1 %（只有門扇），直牆 5.4 %（只有端柱）。 |
| `Socket_Plaque` | 院門匾面中央的空物件，Z 軸朝前（−Y），放 TX01 的匾；匾框是空白的。 |
| `Socket_Emblem` | 院門正脊中央上方的空物件，留給之後的道統徽記。 |

照規格沒有做徽記和任何文字。

## 各件數字

| ID | 尺寸 W×D×H（m） | LOD0 / LOD1 / LOD2 三角面 | 物件數 | 材質數 | 朱漆 | 碰撞 |
|---|---|---|---|---|---|---|
| TX04-GATE 院門 | 5.98 × 2.99 × 5.713 | 72,140 / 34,304 / 10,290 | 2（主體、`_Accent`） | 2 | 2.1 % | 5 個盒（台基、石階、兩側牆體、屋頂） |
| TX04-WALL-ST 直牆 | 4.0 × 0.68 × 2.477 | 15,216 / 7,068 / 2,120 | 2（主體、`_Accent`） | 2 | 5.4 % | 1 個盒 |

- **原點**：底面中心、z＝0；Blender −Y 是正面。
- **院門**：
  - 6 × 3 m 的格位裡放了台基、三級前石階和屋頂，出簷也收在範圍內。
  - 門洞淨寬 1.24 m、淨高 2.86 m。
- **直牆**：
  - 4 m 一段，兩端切平，可以接下一段。
  - 朱漆柱只在 −X 端，連續拼牆時每 4 m 一根，最後一段由轉角或門邊牆收尾。
- **LOD 與格式**：LOD0 不為數字減面；LOD1 ≤ 50 %、LOD2 ≤ 15 %。只交 FBX，內含 LOD0/1/2、`_Collision` 和兩個插槽空物件。
- **效能**：不寫 FPS；手機未實測。

## 做法

- **院門**（三視圖 option4）：
  - 結構：花崗石台基（邊石＋鋪石）、三級石階和兩側垂帶石、8 根深色杉木柱立在蓮瓣鼓墩上。
  - 牆面：兩側開間是石牆裙加白灰牆；中間門框平面有門框柱、中樑和兩側白牆。
  - 門：朱漆雙扇門，每扇 25 顆銅門釘，加鋪首和門環。
  - 簷下：前後額枋、平板枋、墊栱板，各 5 組一斗三升。
  - 屋頂：歇山頂，用 MC01 RF01 的做法改寫成可指定長寬的函式。之後的正堂（14 × 10 m）和廂房（8 × 5 m）會沿用。
- **直牆**（三視圖 option2）：兩層錯縫花崗石牆腳、白灰牆、朱漆端柱和石柱座、兩面木額枋帶小斗、雙坡筒瓦壓頂（瓦當、正脊）。

## 驗收紀錄

- **Blender 資產 QA**（blender-asset-qa `qa_check`，game profile，每個 LOD0 物件單獨掃，z-fighting／懸空都有跑）：結果存 `art/source/tx04-branch-court/qa_sample.json`。
  - 兩件主體和 `_Accent` 沒有 z-fighting、沒有翻面或破面。
  - 院門主體單獨掃會報 40 個「懸空」：都是門釘、鋪首、門環，它們釘在朱漆門扇上，而門扇屬於 `_Accent` 物件。兩個物件合在一起再掃，懸空＝0。
- **FBX 回匯**：尺寸與建模時相同（誤差 0）。
- **Unity**：尚未匯入（未驗），全套做完再跑。

## 選圖

各件的「選用：」和理由在 `art/references/TX04-*/prompt.txt`。提示詞用 `tools/mountain-city-a/make_prompts_tx04.py` 產生：

- 工作包第 11 節的物件句；
- 「只畫這一件」的範圍句；
- 核心組在 #80 給的不要日式、歐式負面詞。

## 怎麼重跑

```
python tools/mountain-city-a/make_prompts_tx04.py
python tools/mountain-city-a/gen_threeviews.py --prompts prompts_tx04.json TX04-GATE TX04-WALL-ST
blender -b --factory-startup -P art/source/tx04-branch-court/build_tx04.py -- GATE WALL_ST
blender -b --factory-startup -P art/source/tx04-branch-court/qa_tx04.py -- <out.json> GATE WALL_ST
blender -b --factory-startup -P art/source/tx04-branch-court/render_tx04.py -- --out art/previews/tx04-branch-court [--clay|--wire|--nodetail|--lod 1] GATE WALL_ST
blender -b --factory-startup -P art/source/tx04-branch-court/assemble_tx04.py -- [--clay]
python art/source/tx04-branch-court/sheets_tx04.py GATE WALL_ST
```

## 預覽

`art/previews/tx04-branch-court/`：

- 每件：四視圖（含 1.75 m 人形尺）、灰模、線框、LOD0／LOD1；
- 參考圖對模型；
- 院門加兩側各兩段直牆的組裝：材質與灰模同角度、正面、1.7 m 人眼。

## 工時

約 2 小時（11/09，含讀包、三視圖生成與選圖、屋頂函式、建模、QA 修正），由 Claude Code 執行。
