# C7｜青溪村格位道具：村口石燈、水井、井與洗衣石、茶棚

> 先讀 `00-operating-rules.md`，再讀主場景工作樹的 `docs/execution/novice-world-block-plan.md`（**第 2 節比例標準、第 4 節格位表、第 5 節格位合約**必讀）。
> 這是第一批照「格位」接單的模型：位置、朝向、尺寸上限都已經定好，你只要在格位裡做出好看的東西。

## 1. 一句話任務

為青溪村核心（A1 區塊）做 4 種道具，填進 5 個已規劃的格位。做完後，遊戲裡原本的半透明標示盒就會換成你的模型。

## 2. 為什麼要做

- z1nnz 要求「先規劃位置和大小，再做模型，做完就能理所當然地放進遊戲」。A1 的格位表已經完成，其中 5 個格位指定給 Codex。
- 這些是村子的生活感來源：
  - 進村第一眼看到的石燈；
  - 廣場和民居中庭的井；
  - 商舖區可以歇腳、聽傳聞的茶棚。

## 3. 位置

| 項目 | 路徑 |
|---|---|
| 工作樹 | 新建：`D:\yun-jing-rpg-workspace\yun-jing-rpg-village-props-c7`。從 `feature/qingxi-main-scene-abc-v1` 開分支 `feature/village-slot-props-c7`。你可以自己用 `git worktree add` 建立，**這是唯一允許的 git 指令**，不 commit |
| 三視圖 | `art/references/village-slot-props-c7/` |
| 腳本 | `tools/art/build_village_slot_props_c7.py` |
| 母檔 | `art/source/village-slot-props-c7/village-slot-props-c7.blend` |
| 匯出 | `art/exports/village-slot-props-c7/`；Unity：`apps/game/Assets/YunJing/Models/VillageSlotPropsC7/` |
| 預覽 | `art/previews/village-slot-props-c7/` |
| 狀態 | `art/exports/village-slot-props-c7/PRODUCTION_STATUS.md` |

## 4. 格位與規格（尺寸是上限，寬 × 深 × 高，m；正面＝Unity +Z＝Blender −Y）

| 格位 | 模型 ID | 名稱 | 尺寸上限 | LOD0 上限 | 設計重點 |
|---|---|---|---|---|---|
| `Gate_Lantern_L`、`Gate_Lantern_R` | VP01 | 村口石燈（同一模型用兩次） | 0.6 × 0.6 × 2.2 | 1,500 | 灰青石座、方形燈室有木格紙窗、頂上小石帽翹角。燈室的紙用獨立材質，之後在 Unity 發光。石座有苔痕。左右兩盞要看起來成對 |
| `Plaza_Well` | VP02 | 廣場水井 | 1.8 × 1.8 × 2.4 | 3,000 | 圓形石井欄（高 0.7 m）、木架與小瓦頂、轆轤和繩、木桶。廣場是村子門面，比中庭的井更整齊 |
| `Homes_Well` | VP03 | 井與洗衣石 | 2.0 × 2.0 × 2.4 | 3,500 | 較舊、方形石井欄、無頂；旁邊一塊洗衣石板和一個木盆。生活感比 VP02 強 |
| `Shops_Teahouse` | VP04 | 茶棚 | 3.6 × 3.0 × 3.0 | 6,000 | 四根竹木柱撐起茅草或竹瓦頂、一張矮桌兩條長凳、爐子與茶壺、掛一面寫「茶」字的布幌（字用貼圖）。正面朝 +Z（朝北） |

- 全部屬於 **A 青溪河谷**（建模規格第 11.2 節）：暖舊木、灰青石、竹。
- 材質整套共用 3 個：`M_VP_Wood`、`M_VP_Stone`、`M_VP_Bamboo`；加 1 個紙或布材質 `M_VP_Paper`。每個都要有 BaseColor／Normal／ORM。
- 原點：底部中心，底部高度 0。
- 碰撞：
  - 石燈、井用一個盒子或圓柱；
  - 茶棚只擋柱子和桌子，人要走得進去。
  - 寫進 `model_info.json`。
- LOD：LOD0／LOD1（50%）。

## 5. 製作階段（照 00 規範第 5、6 節）

1. **Stage 0 分析**：
   - 看新手村截圖 `artifacts/qingxi-novice-village/17-gate-square.png`、`02-plaza-return-C.png`、`19-smithy-shops.png`，了解周圍是什麼；
   - 看 joshsu54 的 StarterHouse、Blacksmith 外觀，配色要相容。
2. **Stage 1 三視圖**：每件一張正、側、背。
3. **Stage 2 灰模**：
   - 照尺寸上限做；
   - 在 Blender 放一個 1.75 m 人形尺和格位的線框盒（照第 4 節尺寸），截圖證明沒有超出。
4. **Stage 3–6**：精修、UV、材質、LOD、匯出、回匯。
5. 每件的預覽：
   - 中性光；
   - 遊戲光（晨光）；
   - **人眼高度 1.7 m、距離 4 m 的視角**（玩家實際看到的樣子）。

## 6. 交付後（Claude Code 會做，你不用做）

- 把 `novice-village.json` 裡這 5 個格位的 `model` 填上你的 FBX 路徑、`status` 改成 `ready`；
- 重新生成新手村，生成記錄的 `QINGXI_FOOTPRINT` 會檢查你的模型有沒有超出格位。

## 7. 驗收標準

| 項目 | 標準 |
|---|---|
| 尺寸 | 每件都在格位尺寸內（超過即退回） |
| 風格 | 和 StarterHouse、Blacksmith 並排不突兀；色彩落在色票 ±10% |
| 生活感 | VP03 看得出有人在用（濕痕、木盆、洗衣石的磨痕）；VP04 看得出是歇腳的地方 |
| 預算 | 每件在面數上限內；4 個材質 |
| 技術 | QA 0 errors；回匯尺寸差 ≤ 1 mm；正面朝 +Z |

## 8. 不要做

- 不要改 `novice-village.json` 或任何 Unity 場景／生成器。
- 不要做格位表裡沒有的東西。想加東西，寫進 README 的「建議」。
