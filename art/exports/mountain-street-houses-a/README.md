| 項目 | 內容 |
|---|---|
| 誰做的 | A（Johnnnny0823） |
| 工作包 | docs/execution/2026-11-05/A-48h-mountain-city-architecture.md（併入 docs/execution/2026-11-08/A-80h-mountain-city.md 第一部分） |
| ID | MC01 樣品：MC01-SB01、MC01-SF01、MC01-RF01（其餘 19 件等樣品過審再做） |
| 分支／PR | art/a-1105-mc01-street-houses ／ PR 待開 |
| 版本 | v001 |
| 狀態 | Exported；Imported／Visually Verified／In-game Verified：未驗（只有 Blender 預覽與 FBX 回匯檢查） |
| 素材來源 | 原創。建模腳本 `art/source/mountain-street-houses-a/build_mc01.py`；手繪貼圖源改自本人 11/03 世界模型的 `build_world_a.py`；三視圖用 Codex CLI 生成，存 `art/references/MC01-*/` |

# MC01 山城街屋模組：樣品批

依 11/07 新規則「一批很多件，先做一件樣品」：MC01 共 22 種輪廓，先交一間店的三層——**石基 SB01＋店面 SF01＋歇山屋頂 RF01**——確認尺度、材質與手法，過了再做其餘 19 件、三棟組裝和 `b-street-assembly.json`。

## 共用材質（D3 §4：共用同一組 2048 材質才能合批）

全部模組只用兩個材質：`M_MountainStreet_Trim`（所有不發光的面）和 `M_MountainStreet_Glow`（燈籠紙）。兩者共用同一組 2048 × 2048 Trim Sheet：

| 貼圖 | 解析度 | 用途 |
|---|---|---|
| `T_MountainStreet_Albedo.png` | 2048 × 2048 | 顏色（sRGB） |
| `T_MountainStreet_Normal.png` | 2048 × 2048 | 法線（OpenGL，Y+） |
| `T_MountainStreet_MetallicSmoothness.png` | 2048 × 2048 | R＝金屬度，A＝光滑度（URP Lit） |
| `T_MountainStreet_Emission.png` | 2048 × 2048 | 只有燈紙那一條亮，其餘黑 |

Trim Sheet 由下往上 13 條，每公尺 256 px：花崗石、帶苔花崗石、踏面花崗石、杉木板、樑木、灰朽木、灰泥、黛瓦、帶苔瓦、銅、靛藍布、燈紙、暗室。每個零件依自己的方向投到對應那一條（木紋順著構件長邊），條帶沿 U 平鋪，V 不出界。色值依 D3 第 0 節：花崗石 #C9C6BD 系、黛瓦 #3A4048 系、深色木、銅件；沒有用朱漆（街屋不是宗門建築）。

## 各件數字

| ID | 尺寸 W×D×H（m） | LOD0 / LOD1 / LOD2 三角面 | 物件數（每個 LOD） | 材質數 | minTier | 碰撞 |
|---|---|---|---|---|---|---|
| MC01-SB01 石基直段 | 3.998 × 3.999 × 2.0 | 47,772 / 23,886 / 7,164 | 1 | 1 | low | 1 個盒（頂面 2.0 m 可走） |
| MC01-SF01 開敞店面 | 3.998 × 3.998 × 3.0 | 23,740 / 8,698 / 2,654 | 4（主體、`Detail_Cloth`、`Detail_Lanterns`、`Glow`） | 2 | low | 12 個盒（柱、三面牆、門洞兩側與門頭；前廊淨空可走） |
| MC01-RF01 歇山屋頂 | 5.54 × 5.51 × 1.82 | 80,552 / 40,276 / 12,082 | 1 | 1 | low | 1 個盒 |

- 原點：底面中心、z＝0；Blender −Y 是街面（前）。4 m 格線，石基、店面外框落在 ±2.0 m 內，接縫 ≤ 2 mm。
- 屋頂 RF 的範圍是 4 m 格子加四周 0.77 m 出簷，所以比 4 m 大；疊在店面／住家層頂（z＝3.0）上。
- `Detail_*` 可整個關掉（布簾、燈籠骨架、銅蓋）；`Glow` 是獨立的發光網格（燈紙）。
- LOD0 不為數字減面；LOD1 ≤ 50 %、LOD2 ≤ 15 %，預算依各組三角面的平方根分配。
- 只交 FBX（`MC01_*.fbx` 內含 LOD0/1/2 與 `_Collision`），不帶切線，Unity 匯入時以 MikkTSpace 計算。
- 不寫 FPS；手機未實測。

## 驗收紀錄

- Blender 資產 QA（blender-asset-qa `qa_check`，game profile，每個 LOD0 物件單獨掃、max_tris 拉到物件本身，z-fighting／懸空掃描都有跑）：三件主體 **errors＝0**，結果存 `art/source/mountain-street-houses-a/qa_sample.json`。
  - 唯一一筆是 `Glow_LOD0` 單獨掃時「懸空」：它是燈籠紙獨立網格，本來就不和自己相連；和 `Detail_Lanterns` 合在一起再掃一次 errors＝0（燈紙接在上下銅蓋上）。
  - 警告：UV 重疊（Trim Sheet 本來就讓很多零件共用同一條，不烘焙）、相接零件的背對背面（只多花面數，不會閃）。
- FBX 回匯尺寸與建模時相同（誤差 0）。
- Unity 尚未匯入（未驗）。

## 選圖與和參考圖的差異

見各件 `art/references/MC01-*/prompt.txt` 的「選用：」。重點：

- **SB01**：四張參考都在石基上緣加了小瓦簷和木角柱，但石基上面要疊店面／住家層，會重複，所以拿掉，角部改整塊角石，上下層咬合（隔層交替）。勒腳和 4 m 格線齊平，上層退 3.5 cm；鑿面只往內凹，不超出格線。
- **SF01**：照 option3 的正面全開、石礎＋銅箍圓柱、雀替、空白布簾、兩盞紙燈；D3 規定不做室內，所以店內貨架拿掉，後方改暗室與門洞，門上加橫披窗格。
- **RF01**：照 option1 的歇山：山花（封山竪板＋懸魚）、正脊兩端卷草收頭、戧脊翹角；筒瓦一條一條建模，每片瓦一個起伏，簷口有瓦當。

## 想請審查確認的地方

1. **前廊 3 m 的解讀**：原包寫 4 × 4 × 3 m、「前廊 3 m 出挑」。我照尺寸上限解讀為「4 × 4 m 格子內前 3 m 開敞、後 1 m 暗室」；若要的是另外再往街上挑出 3 m 的雨棚，請告訴我，其餘店面會照改。
2. **石基 2 m 高**：照原包第 3 節與 D3 第 4 節做 4 × 4 × 2 m。單棟看會覺得高，是給陡坡墊高／擋土用；需要的話可以多做一個 1 m 的矮石基變體。
3. **SF01 面數**：主體 19.6k，比石基、屋頂少，是因為主要是方木與板；若希望更密（例如板面起伏、更多斗栱），請說。

## 怎麼重跑

```
blender -b --factory-startup -P art/source/mountain-street-houses-a/build_mc01.py -- trim SB01 SF01 RF01
blender -b --factory-startup -P art/source/mountain-street-houses-a/qa_mc01.py -- <out.json> SB01 SF01 RF01
blender -b --factory-startup -P art/source/mountain-street-houses-a/render_mc01.py -- --out art/previews/mountain-street-houses-a SB01 SF01 RF01
```

`trim` 會重畫 Trim Sheet；不加 `trim` 時模組直接讀已存的貼圖。三視圖用 `tools/mountain-city-a/gen_threeviews.py`（提示詞由 `make_prompts.py` 從工作包取出）。

## 預覽

`art/previews/mountain-street-houses-a/`：每件四視圖（含 1.75 m 人形尺）、灰模、線框、關 `Detail_*` 的 LOD0／LOD1；三件疊成一間店的組裝（材質與灰模同角度）；參考圖與模型並排。

## 工時

約 1.5 小時（11/08 12:45–14:10，含讀包、三視圖生成與選圖、Trim Sheet 管線、建模、QA 修正），由 Claude Code 執行。
