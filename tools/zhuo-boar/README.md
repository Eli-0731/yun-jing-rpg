# 第 3 天・濁化山豬

依工作包 `docs/execution/2026-11-02/01-A-day3-zhuo-boar.md`（在分支 `feature/qingxi-creek-chapter`）。

牠不是怪物，是生病的動物：不殺、不掉落，玩家被撞也不會倒。

## 流程

```text
idle → alert → telegraph（刨地，轉向，地上有線）→ charge（直線，不轉彎）
  撞到樹或石頭 → daze → 暈眩中在 2 m 內按住 1.5 秒＝驅濁 1 次
  沒撞到 → brake → 回到 alert
  暈完、撞到場地邊界，或預告結束時前方跑不到 3 m → reposition：小跑到衝得開、最好到玩家之間沒有障礙的位置，再預告一次
  所以站在同一棵樹後面只有效一次，玩家要跟著走位才能再引牠撞樹
  驅濁 2 次 → cleansed（站 2 秒，跑回山裡）→ 發出 zhuoBoar.cleansed
  被撞 3 次 → escaped → 發出 zhuoBoar.escaped → 30 秒後在原處再遇
```

## 操作

| 動作 | 鍵盤滑鼠 | 觸控 |
|---|---|---|
| 移動、看 | WASD、滑鼠 | 左手搖桿、右半邊拖曳 |
| 閃避 | Shift 或空白鍵，加方向 | 右下「閃」，方向用搖桿 |
| 驅濁 | 按住 F | 按住「驅」（暈眩且 2 m 內才出現，外圈填滿） |

沒有給方向時，閃避會往衝撞線外側閃；沒有線時往後退。

## 工作包沒寫、我補的數值

都在 `packages/content/zhuo-boar-encounter-v1.json` 的 `tuning`，以及最上層的 `cleanseRadiusM`、`staminaFloor`、`chargeLineWidthM`、`dazeShakeSeconds`（這四個是工作包文字裡的數字）。要改請告訴我或直接改 JSON，再跑 `parity.mjs`。

| 欄位 | 值 | 為什麼 |
|---|---|---|
| `alertSeconds` | 0.8 | 警戒的長度，工作包只寫了有這一段 |
| `dodgeCooldownSeconds` | 0.7 | 不然無敵時間可以連按接起來 |
| `boarLengthM`／`boarWidthM` | 1.5／0.9 | 工作包的膠囊體 |
| `playerRadiusM` | 0.15 | 加上豬寬一半剛好是衝撞線的 1.2 m：站在線外就不會被撞 |
| `cleansedStandSeconds` | 2 | `Cleanse` 動畫長度 |
| `fleeSpeedMps`／`fleeSeconds` | 6／3.5 | 跑回林子，之後隱藏 |
| `minChargeRunM` | 3 | 前方跑不到這個距離就先換位，不貼著牆或樹硬撞 |
| `repositionDistanceM`／`repositionSpeedMps` | 5.5／4.5 | 換位走多遠、多快（比衝撞慢，看得出是在繞路，也給玩家時間重新走位） |
| `repositionTurnDegPerSecond`／`repositionMaxSeconds` | 300／3.5 | 轉身速度；最久走多久，避免被卡住 |

## 檔案

| 檔案 | 用途 |
|---|---|
| `packages/content/zhuo-boar-encounter-v1.json` | 規則資料與介面文字 |
| `tools/zhuo-boar/zhuo-boar-rules.mjs` | 規則程式（純邏輯，不碰 Unity、不碰網路） |
| `tools/zhuo-boar/zhuo-boar-rules.test.mjs` | 單元測試；`tests/zhuo-boar-rules.test.ts` 讓它跟著 `npm test` 跑 |
| `tools/zhuo-boar/parity.mjs` | 把資料複製給 Unity，並錄下跑法給 C# 對照 |
| `tools/zhuo-boar/encode_video.py` | 把截下來的畫面編成 MP4 |
| `apps/game/Assets/YunJing/Runtime/QingxiZhuoBoarRules.cs` | 規則的 C# 版 |
| `apps/game/Assets/YunJing/Runtime/QingxiZhuoBoarEncounter.cs` | 遭遇元件：模型、動畫、輸入、HUD、測試掛鉤 |
| `apps/game/Assets/YunJing/Runtime/QingxiZhuoBoarFx.cs` | 衝撞線、霧氣、松針、鏡頭震、占位音效 |
| `apps/game/Assets/YunJing/Runtime/BoarObstacle.cs` | 障礙物標記；小松撞到會歪 8°、開 `_Scar`、掉松針 |
| `apps/game/Assets/YunJing/Shaders/QingxiZhuoBoar.shader` | `_Zhuo`、`_Scar` 的材質 |
| `apps/game/Assets/YunJing/Editor/QingxiZhuoBoarBuilder.cs` | 測試場景與 Windows 版 |
| `apps/game/Assets/YunJing/Editor/QingxiZhuoBoarSmoke.cs` | 在 Unity 裡重播 `parity.mjs` 的跑法，要和 JS 一致 |

```powershell
node --test tools/zhuo-boar/zhuo-boar-rules.test.mjs   # 規則測試
node tools/zhuo-boar/parity.mjs                        # 改了 JSON 或規則後重跑
```

測試場景不進版控（`Generated` 資料夾），用 Editor 選單 `Yun Jing/Generate day 3 boar test scene` 或 `QingxiZhuoBoarBuilder.Generate` 產生。

## 給核心組接的地方

- **開始**：元件掛在 `D3_BoarEncounter`，胖子演完呼叫 `BeginFromScript()`。`startOnNotice` 只給測試場景用。可以直接用 `QingxiZhuoBoarBuilder.PlaceEncounter`。
- **事件**：`QingxiZhuoBoarEncounter.Cleansed(durationSeconds, hitsTaken)`、`Escaped(hitsTaken)`，對應 `zhuoBoar.cleansed`、`zhuoBoar.escaped`。這裡不呼叫伺服器、不發任何東西。
- **體力**：元件只算這場被撞扣多少（`StaminaLost(lost, left)`，最低留 1），起始值是 `staminaStart`。接正式體力時，把起始值傳進來、在事件裡扣。
- **障礙物**：有 `BoarObstacle` 的碰撞體都算，`D3_BoarTree_01..03` 沒掛也會自動補上。
- **範圍**：`useBounds` 讓牠衝到邊界時煞車而不是衝出場；D3 沒有圍牆時要設好，或用地形自己擋。
- **模型**：`boarModel`、`clips` 留空時是 1.5 × 0.9 m 的膠囊體。

## 驗證

- 規則測試全過，並跟著 `npm test` 跑。
- `QingxiZhuoBoarSmoke`：C# 和 JS 重播 4 種跑法，事件、位置、結果一致。
- Windows 版跑過順利清掉、被撞 3 次跑掉並回來兩條路線。

**錄影**：`video/boar_clean_scripted.mp4`、`video/boar_hits_scripted.mp4`，1280×720，開著手機按鈕。

這兩段是**腳本自動操作**（`--boar-auto-clean`、`--boar-auto-hits`），不是人玩的。按鍵走的是獨立的虛擬鍵盤，手機按鈕沒有被手指按過。重錄：

```powershell
YunJingZhuoBoar.exe -screen-fullscreen 0 -screen-width 1280 -screen-height 720 --boar-auto-clean --boar-capture --touch --quality-high
```

## 手感問題（看錄影想到的，還要人玩過才算數）

1. **第一次遇到看不清方向**：預告只有 1.2 秒，鏡頭又在玩家背後，山豬在畫面深處時，衝撞線是斜的，很難判斷該往哪邊閃。
2. **換位時的節奏**：牠每次暈完和撞牆後都會小跑換位，這段玩家只能走位，要人玩過才知道會不會太閒。
3. **鏡頭會被樹擋**：玩家躲在樹後面引牠撞樹時，鏡頭常被樹冠擋住，正好看不到牠。
4. **暈眩時間偏緊**：2.5 秒裡要按滿 1.5 秒，只剩 1 秒可以跑過去；如果閃得比較遠就來不及，要多撞一次。
5. **閃避沒有角色動作**：只有位移，看起來像瞬間滑開；要等角色動畫。
6. **Shift 同時是疾跑**：戰鬥中按 Shift 想跑會變成閃避，剛好有冷卻，連按手感不好。

## 還沒做到

- **人實際玩過的錄影**（電腦與手機）：要人來玩。手機版也還沒有在真機上跑過。
- 胖子演出、同屆五人、對白、伺服器結算（工作包寫明由核心組做）。
- 音效是占位的；閃避沒有專屬動作。
