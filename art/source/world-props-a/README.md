# 承天 · 11/03 A 包：把世界補起來（Johnnnny0823）

工作包：`docs/execution/2026-11-03/A-40h-combat-and-world.md` 的模型一節（在分支 `feature/qingxi-creek-chapter`）。戰鬥手感是另一個 PR；這個 PR 只有模型，沒有改主場景、QingxiHud、服務端或別人的資料夾。

## 交付一覽

尺寸是寬 × 深 × 高（m），三角面是 LOD0 / LOD1 / LOD2（同一檔案）。完整數字（每組貼圖尺寸、碰撞形狀、樞紐點、可走高度）在 [`art/exports/world-props-a/model_info.json`](../../exports/world-props-a/model_info.json)。

| 編號 | 東西 | 尺寸上限 | 實際尺寸 | 三角面 | minTier | 細節子物件 |
|---|---|---|---|---|---|---|
| SC04 | 獵人工具棚 | 3.6 × 3 × 2.8 | 3.546 × 2.931 × 2.713 | 2,646,969 / 1,323,482 / 397,045 | `standard` | `Detail_Axe`, `Detail_Chips`, `Detail_Hang` |
| SC01 | 倒下的土地公小廟 | 1.6 × 1.4 × 1.8 | 1.576 × 1.333 × 1.397 | 193,914 / 96,953 / 29,078 | `standard` | `Detail_Ferns`, `Detail_Incense`, `Detail_Offerings`, `Detail_Tiles` |
| SC02 | 熄掉的獵人營地 | 3 × 3 × 1.2 | 2.332 × 2.176 × 1.182 | 71,100 / 35,547 / 10,663 | `standard` | `Detail_Grass`, `Detail_Leaves`, `Detail_Snare` |
| SC03 | 倒塌的歇腳亭 | 4 × 4 × 3.2 | 3.597 × 3.847 × 3.152 | 675,265 / 337,630 / 101,290 | `standard` | `Detail_Grass`, `Detail_Nest`, `Detail_Tiles`, `Detail_Vine` |
| RK05 | 載貨板車（兩輪各自可轉） | 3.2 × 1.6 × 1.4 | 2.481 × 1.576 × 1.374 | 585,190 / 292,593 / 87,775 | `standard` | `Detail_Cloth`, `Detail_Rope` |
| RK06 | 土地祠（`Glow` 油燈） | 2.4 × 2 × 2.8 | 2.336 × 1.827 × 2.609 | 713,835 / 356,915 / 107,070 | `standard` | `Detail_Grass`, `Detail_Incense`, `Detail_Offerings` |
| RK01A | 路牌 A（兩塊空白指向板） | 1.2 × 0.4 × 2.6 | 1.089 × 0.302 × 2.561 | 81,820 / 40,907 / 12,271 | `standard` | `Detail_Stones`, `Detail_Vine` |
| RK01B | 路牌 B（一塊長指向板） | 1.2 × 0.4 × 2.6 | 0.904 × 0.312 × 2.446 | 55,509 / 27,754 / 8,323 | `standard` | `Detail_Stones`, `Detail_Vine` |
| RK09 | 觀景石凳 | 2 × 0.8 × 0.6 | 1.97 × 0.743 × 0.559 | 135,008 / 67,504 / 20,250 | `standard` | `Detail_Grass`, `Detail_Pebbles` |
| RK10A | 草垛 A（整齊） | 2.4 × 2.4 × 2.2 | 2.252 × 2.166 × 2.167 | 1,976,866 / 988,432 / 296,526 | `standard` | `Detail_Straw` |
| RK10B | 草垛 B（蓬亂） | 2.4 × 2.4 × 2.2 | 2.174 × 2.364 × 1.866 | 1,185,793 / 592,894 / 177,864 | `high` | `Detail_Straw` |
| RK12A | 路緣碎石 A | 2 × 2 × 0.3 | 1.97 × 0.422 × 0.195 | 29,249 / 14,622 / 4,387 | `high` | `Detail_Grass` |
| RK12B | 路緣碎石 B | 2 × 2 × 0.3 | 1.636 × 0.425 × 0.214 | 20,700 / 10,349 / 3,104 | `high` | `Detail_Grass` |
| RK12C | 路緣碎石 C | 2 × 2 × 0.3 | 1.97 × 0.435 × 0.202 | 17,970 / 8,985 / 2,695 | `high` | `Detail_Grass` |
| RK12D | 路緣碎石 D | 2 × 2 × 0.3 | 1.268 × 0.378 × 0.226 | 17,586 / 8,792 / 2,636 | `high` | `Detail_Grass` |
| WM08A | 踏石 A | 1 × 1 × 0.4 | 0.985 × 0.784 × 0.284 | 19,599 / 9,797 / 2,938 | `standard` | `Detail_Pebbles` |
| WM08B | 踏石 B | 1 × 1 × 0.4 | 0.985 × 0.725 × 0.264 | 19,368 / 9,682 / 2,904 | `standard` | `Detail_Pebbles` |
| WM08C | 踏石 C | 1 × 1 × 0.4 | 0.985 × 0.911 × 0.285 | 19,774 / 9,886 / 2,964 | `standard` | `Detail_Pebbles` |
| WM10A | 溪石 小 | 0.5 × 0.5 × 0.5 | 0.468 × 0.38 × 0.286 | 19,403 / 9,700 / 2,909 | `standard` | — |
| WM10B | 溪石 中 | 1.2 × 1.2 × 0.8 | 1.182 × 0.91 × 0.528 | 20,597 / 10,298 / 3,088 | `standard` | `Detail_Gravel` |
| WM10C | 溪石 大 | 3 × 3 × 1.4 | 2.955 × 2.19 × 1.294 | 111,285 / 55,641 / 16,692 | `standard` | `Detail_Ferns`, `Detail_Gravel` |
| WM10D | 溪石 長 | 3 × 1.2 × 0.8 | 2.772 × 1.182 × 0.416 | 118,356 / 59,177 / 17,751 | `standard` | `Detail_Ferns`, `Detail_Gravel` |
| TY03A | 淨水蓮 1 浮葉 | 0.8 × 0.8 × 0.7 | 0.471 × 0.546 × 0.162 | 20,956 / 10,477 / 3,143 | `standard` | — |
| TY03B | 淨水蓮 2 立葉 | 0.8 × 0.8 × 0.7 | 0.474 × 0.299 × 0.37 | 13,889 / 6,944 / 2,082 | `standard` | `Detail_Leaf` |
| TY03C | 淨水蓮 3 花苞 | 0.8 × 0.8 × 0.7 | 0.615 × 0.503 × 0.569 | 17,581 / 8,789 / 2,635 | `standard` | `Detail_Leaf` |
| TY03D | 淨水蓮 4 開花（`Glow` 花心） | 0.8 × 0.8 × 0.7 | 0.615 × 0.521 × 0.63 | 18,032 / 9,014 / 2,703 | `standard` | `Detail_Leaf` |
| TY05A | 練功地面 A | 地面件 | 2 × 2 × 0.015 | 32,768 / 8,192 / 800 | `standard` | — |
| TY05B | 練功地面 B | 地面件 | 2 × 2 × 0.015 | 32,768 / 8,192 / 800 | `standard` | — |
| TY06 | 練功器材（石鎖＋石擔，兩件） | 1.4 × 0.8 × 0.6 | 1.379 × 0.649 × 0.389 | 31,686 / 15,840 / 4,751 | `standard` | `Detail_Grass` |
| TY10A | 碎石小徑 直段 A | 地面件 | 1 × 2 × 0.015 | 16,384 / 4,096 / 400 | `standard` | — |
| TY10B | 碎石小徑 直段 B | 地面件 | 1 × 2 × 0.015 | 16,384 / 4,096 / 400 | `standard` | — |
| TY10C | 碎石小徑 收尾 | 地面件 | 1 × 1 × 0.015 | 8,192 / 2,048 / 200 | `standard` | — |

## 製作順序

1. **AI 三視圖**：每件用工作包提示詞原文，加風格指南 5.2 固定風格段與 5.3 固定負面提示，獨立生成至少 4 張，保存在 `art/references/<ID>/`。
   - 選用哪一張寫在各自的 `prompt.txt` 第一行「選用：」。工具：Codex CLI 內建圖像生成（`tools/world-props-a/gen_threeviews.py`），沒有回報 seed。
   - `build_world_a.py` 建模前會檢查 `prompt.txt` 已寫明選用，沒選就停。
2. **建模**：`art/source/world-props-a/build_world_a.py`（擺放件）與 `build_ground_a.py`（TY05、TY10 地面件），從 C 包的 `qingxi-day12-c` 流程改寫。
3. **烘焙**：每個材質組各自用 Cycles 烘 Albedo、AO、粗糙度、法線，再加手繪感處理，輸出 `Albedo`、`Normal`、`MaskURP`、`ORM`。
4. **審圖**：`review_world_a.sh` 匯入**匯出的檔案**（不是工作場景）渲染四視圖＋1.75 m 人形、線框，以及同角度 LOD0 | LOD1 並排且關掉 `Detail_*`（畫質分級第四節）。圖在 `art/previews/world-props-a/<ID>/`。
5. **Unity 檢查**：`QingxiWorldPropsAVerify` 匯入 FBX 與貼圖，建 URP 材質、LODGroup、碰撞，對照 `model_info.json` 檢查尺寸、上限、LOD 面數、minTier、`Detail_*`、碰撞、車輪樞紐、`Glow`，並渲染 1.7 m 視高的排列圖到 `art/previews/world-props-a/unity/`。

每件建好後我都先出預覽和參考圖比對，差太多就改程式重建；這輪重建過的問題記在下方「自查」。

## 檔案

| 位置 | 內容 |
|---|---|
| `art/source/world-props-a/<ID>.blend` | 可編輯母檔：烘焙後的 LOD、`_Collision`、原始零件集合 |
| `art/exports/world-props-a/<ID>.fbx` | 引擎用：所有 LOD、`_Collision`；−Z 前、Y 上、1 單位 = 1 m |
| `art/exports/world-props-a/<ID>.glb` | LOD0，貼圖內嵌 |
| `art/textures/world-props-a/` | 擺放件 `<ID>_<組>_*.png`，地面件 `T_<ID>_*.png` |
| `art/previews/world-props-a/` | 審圖渲染與 Unity 檢查圖 |
| `tools/world-props-a/` | 三視圖生成與對照表 |

## 共同規格

- **原點與接地**：原點在腳印中心，底部 z = 0，前方是 Blender −Y，不附地面底板。
- **LOD**：同一檔案每組各有 `_LOD0`、`_LOD1`（約 50%）、`_LOD2`（約 15%），一個 LOD 由該件所有組的同級網格組成。
- **細節**：可拿掉也不影響看懂的東西（小石、落葉、掛物、繩、草）是 `Detail_*` 子物件，列在 `detailObjects`。
- **碰撞**：會擋人的件有 `<ID>_Collision`，由盒和圓柱組成，原始形狀在 `model_info.json`。地面件（TY05、TY10）沒有碰撞。
- **特殊件**：
  - RK05 兩個車輪各自是獨立網格，原點在輪軸上，可以各自旋轉。
  - RK06 油燈火焰和 TY03D 花心是獨立的 `Glow` 網格，發光強度 0 時也正常好看。
  - RK01 指向板是空白的，地名在遊戲裡疊字。
  - WM08 頂面接近平的，可以踩；SC03 台基可走，只有立柱和瓦堆擋人。
  - RK10B、RK12A–D 是 `minTier: high`。

## 自查

- **面數超出手機預算（已和使用者確認維持現狀）**：使用者要求面數盡量高、以美感為先。結果 SC04 的 LOD1 約 132 萬面、RK10A 約 99 萬面，單件就超過畫質分級「標準檔整個畫面 30 萬面」的上限；匯出檔合計約 2.2 GB（SC04.fbx 約 345 MB）。手機要不要另外降面、LOD 距離怎麼設，交給核心組決定。
- **這輪重建修掉的問題**：
  - 地衣斑點原本是三角函數相乘，會排成整齊圓點，改成 3D 值雜訊。
  - 梳齒狀草殼被自動 UV 拆成幾千個島，貼圖幾乎全黑；改成保留連續 UV、用外框排版。
  - 小於 1024 的細節貼圖被島間距吃掉而發黑，改成最低 1024。
  - 踏石側邊的苔墊看起來像凸出的黑石頭，拿掉；水線變暗不再套到小卵石上。
  - 路牌朝左的指向板做成燕尾凹口，修正成箭頭。
  - 土地祠的椽頭穿出屋面，改成收在屋簷下。
- **Unity 檢查**：Unity 6000.0.82f1 跑 `QingxiWorldPropsAVerify`，416 項全部通過（`art/previews/world-props-a/unity/report.txt`）。
  - 檢查過程修掉三個問題：RK06、SC03、RK05 的碰撞超出模型；RK05 的尺寸紀錄沒有算進車輪位置。
- **尺寸**：自動縮放只用來吸收雜訊和草叢造成的微小超出。SC04、RK05、RK01 原本被縮到 0.62–0.80 倍（工具棚簷口比人還矮、板車像玩具），已改設計，現在都在 0.96 倍以上。
- **沒有實測的**：手機與網頁的實際幀數、記憶體。

## 重建

```bash
blender -b --factory-startup -P art/source/world-props-a/build_world_a.py -- SC04
BLENDER=<blender.exe> sh art/source/world-props-a/review_world_a.sh SC04
blender -b --factory-startup -P art/source/world-props-a/build_ground_a.py -- TY05A TY05B TY10A TY10B TY10C
```

大件（SC04、RK10、RK06）各要 40–60 分鐘，大部分時間在烘焙。
