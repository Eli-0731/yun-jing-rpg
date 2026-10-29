# D3 上游溪谷｜區塊規劃 v1

> 2026-10-30，Claude Code。
> 資料：`tools/qingxi-terrain/blocks/D3.json`；地圖：`docs/execution/maps/d3-block-plan.png`；配置測試：`tools/qingxi-terrain/novice-village.test.mjs`。
> 用途：放 Johnnnny0823 的上游調查（PR #45）。這裡是斷流第一章的現場。

## 地形與動線

- **位置**：cell [-1, 1]，世界座標 x −150 到 −50、z 50 到 150。在青溪村的西北方。
- **溪流**：
  - 從東南角往西北上溯，寬 2.6 m（對齊 #45 改好後的河段）；
  - 水位很低，表現斷流；
  - 高度從 3 m 升到約 15 m。
- **步道**：沿西南岸，寬 2 m；南緣的 `d3-south` 之後接 A3。
- **育幼區**：在東北岸，要經過溪中的淺灘（A08，`creek.crossing`）才到得了。

## 平台與格位

| 平台 | 高度 | 格位 | 放什麼（#45 的件） |
|---|---:|---|---|
| `d3-gauge` | 3.5 m | `D3_WaterGauge`、`D3_MarkerStone` | A09 水位尺、A06 示跡石 |
| `d3-sluice` | 5 m | `D3_CrackedSluice`、`D3_FormationBase` | A02 破石槽、A03 舊陣基 |
| `d3-nursery`（東北岸） | 6 m | `D3_NurseryTracks`、`D3_FallenBamboo` | A07 足跡泥面、A10 倒竹 |
| `d3-ruin` | 8 m | `D3_PavilionRuin` | A11 觀測亭殘基 |
| `d3-source` | 11 m | `D3_ResonanceStone`、`D3_DamRemains` | A12 水脈共鳴石；斷流石壩的岸上壩頭（核心組，待規劃） |

## 沿溪的河段（`creekKit`）

| 溪上位置（從東南端算起） | 用哪些件 |
|---|---|
| 0–30 m | A01 直段、左彎 |
| 30–55 m | A01 收窄、A04 泥沙（清淤前後兩種狀態） |
| 58–66 m | A08 淺灘（過溪點） |
| 66–105 m | A01 右彎、直段；沿岸散 A05 枯草 |
| 105–125 m | A01 收窄、源頭收尾 |

## 還沒做的

- **D1 的西南角**：A1 的溪從 (−30, 50) 出村，D3 的溪從 (−50, 54) 開始，中間會經過 D1。D1 建立時要把這段接起來。
- **Unity 場景**：要等 #45 合併、模型就位後，才把 D3 加進區塊串流（`QingxiBlockBuilder`）。
- **斷流石壩的主體**：橫在溪上，屬於地標，由核心組另外規劃。
