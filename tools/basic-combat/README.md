# 基礎戰鬥手感（新手空手）

依工作包 `docs/execution/2026-11-03/A-40h-combat-and-world.md` 第 1 節（在分支 `feature/qingxi-creek-chapter`）。之後所有戰鬥共用這一套；這一包只做新手空手，不分道統、不做法寶、不做教學。

## 動作

```text
idle → 普攻（前搖 → 判定 → 收招）→ idle
        收招中、過了 chainFrom 再按一下，才接下一段：palm1 → palm2 → palm3（第三段帶小擊退）
        前搖、判定中按的不算，也不會存起來；收招結束才按，從 palm1 重來
idle → 蓄力（按住）→ 放開 → 重擊（前搖 → 判定 → 收招）
        按不到 0.35 秒就放開＝取消，不進冷卻；按滿 1.2 秒自動放出；放出時開始冷卻 4 秒
        傷害 22→40、擊退 1.6→3.4 m，依蓄力比例
idle／收招／蓄力 → 閃避 2.5 m，從開始起無敵 0.35 秒；前搖和判定中不能閃
```

- **同一擊只中一次**：每次出手各自記錄已打中的目標；範圍內的每個目標各中一次。
- **轉向**：不做硬鎖定；出手當下轉向 4 m 內最近的目標，沒有目標時轉向搖桿方向。
- **事件**：每次命中發出 `combat.hit { targetId, attackId, damage }`（C# 是 `QingxiBasicCombat.Hit`）。結算由核心組接，這裡不扣血、不掉落。

數值全部在 `packages/content/basic-combat-v1.json`。改完跑 `node tools/basic-combat/parity.mjs`，它會把 JSON 複製到 Unity 的 `Resources/BasicCombat/`，並重錄 C# 比對用的紀錄。

## 操作

| 動作 | 鍵盤滑鼠 | 觸控 |
|---|---|---|
| 移動、看 | WASD、滑鼠 | 左手搖桿、右半邊拖曳（原本的） |
| 普攻 | J 或滑鼠左鍵（滑鼠鎖定時） | 右下「攻」 |
| 蓄力重擊 | 按住 Q 或滑鼠右鍵 | 按住「招」 |
| 閃避 | C 或左 Ctrl，加方向 | 「閃」，方向用搖桿 |

三個觸控鈕在 720 高的 GUI 空間是 112／92／92，另外保證在任何螢幕上至少 88 × 88 實體像素。只有掛了 `basicCombat` 的場景會出現，其他場景的按鈕不變。按鍵沿用林地遭遇（J／Q／C），玩家不用重學。

## 檔案

| 位置 | 內容 |
|---|---|
| `packages/content/basic-combat-v1.json` | 數值 |
| `tools/basic-combat/basic-combat-rules.mjs` | 純規則（固定步長 1/120 秒） |
| `tools/basic-combat/basic-combat-rules.test.mjs`、`tests/basic-combat.test.ts` | 單元測試，`npm test` 會跑 |
| `tools/basic-combat/parity.mjs` | 錄 4 組腳本給 C# 比對 |
| `apps/game/Assets/YunJing/Runtime/BasicCombat/QingxiBasicCombatRules.cs` | C# 版規則 |
| `.../BasicCombat/ICombatTarget.cs` | 目標介面 `ICombatTarget` 和登記表 `CombatTargets` |
| `.../BasicCombat/QingxiBasicCombat.cs` | 玩家身上的元件：輸入、規則、回饋、占位動作 |
| `.../BasicCombat/QingxiCombatTestTarget.cs` | 只給測試場景用的目標（會回擊的藤靶、山兔、山豬） |
| `.../BasicCombat/QingxiBasicCombatDemo.cs` | 錄影用的自動示範 |
| `apps/game/Assets/YunJing/Editor/QingxiBasicCombatBuilder.cs`、`QingxiBasicCombatSmoke.cs` | 產生測試場景、建 Windows 版；C# 和 JS 比對 |
| `apps/game/Assets/YunJing/Runtime/QingxiTouchControls.cs` | 只加一個 `basicCombat` 欄位和攻／招／閃三顆鈕 |

沒改主場景、`QingxiFirstPerson`、`QingxiHud`、伺服器，也沒改山兔和山豬遭遇的規則。

## 回饋

命中停頓（`Time.timeScale` 0.05，輕擊 0.05～0.08 秒、重擊 0.11 秒）；鏡頭輕震；目標閃白並晃動，動物照擊退距離滑開；命中點噴出碎屑；占位音效（程式產生的悶擊和揮空聲）。被藤靶打中時畫面泛紅，閃過時畫面泛藍並跳出「閃過」。

動作用試模角色現有的零件做占位：上臂、袖子、手三個零件一起繞肩關節往前推掌，第三段和重擊用雙手，蓄力時雙臂後收，身體同時微微前傾。

## 測試場景

```sh
node tools/basic-combat/parity.mjs
Unity -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.QingxiBasicCombatBuilder.Generate
Unity -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.QingxiBasicCombatBuilder.BuildWindows
```

產生和建置要分兩次執行，因為產生時會把專案切到 Input System，同一次建置會遇到 "script class layout is incompatible"。

場景 `Assets/YunJing/Generated/QingxiBasicCombatTest.unity`：
- 新手玩家；
- 我的 A12 藤靶，每 3.2 秒預備 0.55 秒後回掃一次，2.4 m 內被掃到算中；重擊可以打斷它；
- 山兔 v003、濁化山豬 BR01，各自播自己的 idle 和受擊動畫。

三個目標都不會死，血條歸零就重來，只用來測手感。

## 驗證

- `npm test`：96 項全過，其中 9 項是這一包：連擊時間窗、收招結束後重來、蓄力取消不進冷卻、半蓄力和滿蓄力的傷害與擊退、冷卻、閃避無敵剛好 0.35 秒和距離 2.5 m、閃避只能取消收招和蓄力、同一擊不重複命中、4 m 內轉向、忽略已倒下的目標。
- Unity：`QINGXI_BASIC_COMBAT_PARITY_OK runs=4 events=59`，C# 和 JS 的事件、位置、朝向、冷卻完全一致。Windows 版建置 `Succeeded errors=0`。
- 自動示範（`BasicCombatTest.exe -basicCombatDemo -capture <資料夾>`）：命中 12 次（藤靶 9、山兔 2、山豬 1），藤靶回擊 5 次中閃過 1 次，執行過程沒有例外。紀錄裡每一下都是 `combat.hit { targetId, attackId, damage }`。影片：`video/basic_combat_scripted.mp4`（**腳本自動操作，不是真人**）。

## 還沒做

- **真人錄影**：電腦和手機實際玩過的影片要由 Johnnnny0823 自己錄，錄好放進 `video/`。
- 動作都是占位，要等正式角色和動畫。

## 手感問題（實際跑過看到的）

1. **鏡頭擋住目標**：第一人稱控制器的第三人稱鏡頭在玩家正後方、高度跟頭差不多。目標在正前方時，整個人會擋住出拳和命中點；錄影時我另外架了斜側方鏡頭才看得清楚。建議戰鬥中把鏡頭稍微往肩後偏，或拉高一點。
2. **蓄力取消沒有提示**：按「招」不到 0.35 秒就放開會無聲取消，看起來像按了沒反應。建議加一個短暫的收氣音效或圖示。
3. **閃避比較寬鬆**：無敵 0.35 秒比閃避位移的 0.30 秒還長，閃完落地那一下也是無敵的。現在藤靶回擊很好閃；之後如果怪的攻擊變快，可能要縮短。另外林地遭遇用的是 2.6 m、無敵 0.26 秒，和這包寫的 2.5 m、0.35 秒不同，兩套之後要統一。
4. **打擊感偏輕**：目標只有閃白和晃動，沒有受擊硬直動畫，山豬被打中還在播 idle。輕擊的命中停頓 0.05 秒幾乎感覺不到，第三段 0.08 秒才有手感。
5. **手機按住蓄力**：按住「招」時如果手指滑出按鈕，蓄力會中斷；也要確認會不會和右半邊拖曳鏡頭搶手指。這要用真機試。
