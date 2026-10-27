# 青溪場景與協作者素材接入表

更新：2026-10-28。這裡把「收到模型」「放入某個 Unity 場景」「出現在目前試玩版」「完成玩法」分開。詳細產品順序見[開發進度表](development-roadmap.md)。來源欄是原作者；z1nnz／Codex 對採用、接線和整合負責，不把協作者建模記成核心組原創。

| 素材／工作 | 原作者及位置 | 進儲存庫 | 進 Unity | 進目前入口試玩 | 遊戲互動 |
|---|---|---|---|---|---|
| TownLayout v004，48×54 m 街區原件 | joshsu54／Dondon，`art/incoming/dondon/TownLayout/v004/` | 是 | 整包未直接用在小入口 | 否 | 否；整包高面數，待拆件、LOD、碰撞 |
| 較大青溪鎮，151 筆配置 | joshsu54 交接模型＋核心組場景配置，`apps/game/Assets/QingxiWorld/` | 是 | 是，**獨立**城鎮＋狩獵區生成器 | 否，目前試玩呼叫另一生成器 | 舊獨立場景有本機走路與兔子替身；正式採獵／背包未接 |
| StarterHouse v004、StoneArchBridge、MountainStreamBend、MountainStonePath／Stairs、CliffBoardwalk、QCaveEntrance、SectGate、LayeredCliff、CommonPine、BambooClump、MossBoulderSet | joshsu54／Dondon 原件；選入 `apps/game/Assets/YunJing/Models/CollaboratorWorldV1/` | 是 | 是，`YunJing.Editor.QingxiWorldBuilder` 已逐件排放 | 是，視野與距離依角色位置 | 基本場景模型；不是可開門、交易或採集的成品 |
| 原創聽風台與入口支路 | z1nnz 指導／Codex 製作，PR #27 | 在草稿 PR | 是，小入口 | 是 | 石構件有碰撞；未完整人工走位驗收 |
| 道路／河岸／橋頭 31 件 EnvironmentTransitionKit | joshsu54，`art/incoming/dondon/EnvironmentTransitionKit/v001/`，PR #29 | **已合入 main** | 尚未整批匯入可玩場景 | 否 | 否；下一步按路段挑選、設材質和碰撞 |
| 山兔 v003 骨架、動畫、LOD | Johnny0823／Codex，PR #21 | 是 | 模型交接；目前入口未接戰鬥 | 否 | 服務端掉落規則另有原型，兩者尚未接通 |
| 演武棚等六件公共演武區模型 | Johnnnny0823／Codex，PR #32 | **已合入 main** | 尚未接主場景 | 否；另有獨立 PWA 展示 | 正式修行與獎勵未接 |
| 溪畔採集六件模型、九種狀態 | joshsu54／Claude Code，PR #31 的素材部分 | **已合入 main，暫存待修訂**；建模前缺 AI 三視圖，依 z1nnz 本輪指示先收入 | 否；高面數、LOD／碰撞待補 | 否；獨立展示未合併 | 否；正式採集 API 未接 |
| 告示與小事件 | C 的工作包 | 截至本次稽核未見遠端交付 PR | 否 | 否 | 否；工作單不算完成素材 |

**目前的大城鎮為何看不見：** `QingxiWorld.Editor.QingxiWorldBuilder` 在 `apps/game/Assets/QingxiWorld/` 建較大的小鎮和狩獵區；PR #27 的本機試玩則用 `YunJing.Editor.QingxiWalkthroughBuilder`，底層採 `apps/game/Assets/YunJing/Editor/QingxiWorldBuilder.cs` 的小入口。這兩份生成的 Unity 場景各自獨立，尚未在現行固定 Unity 版本和畫面設定下接成同一張可玩地圖。

**每件交付的接入流程：** 協作者交原件與來源 → PR 檢查並合併 → 匯入標準場景和設定比例／材質／LOD／碰撞 → 放進玩家行走路線 → 如有玩法才連服務端、背包、保存並測重送。只有走到相應步驟，表格才能向右更新。

z1nnz 已說明提供的外來模型取得原作者授權，可在《雲境》改造。改造版仍記原作者、來源與修改者；公開交付時保留可查的授權範圍紀錄。自製新模型沿用先生成、檢視並保存 AI 三視圖的順序。
