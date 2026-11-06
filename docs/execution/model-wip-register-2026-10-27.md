# 未完成模型接續登記｜2026-10-27

這份表保留已做的原稿與下一關，不把概念圖、預覽或交接模型誤稱為遊戲精模。製作新模型仍遵守先生成、檢視、保存 AI 三視圖的順序。修改協作者或授權模型時保留原作者與來源。

| 內容 | 現有檔案／位置 | 完成到哪裡 | 下一關 |
|---|---|---|---|
| 原創女主角 Heroine-01 | `art/references/heroine-01/`；獨立分支 `feature/heroine-original-face-v2` 的 `art/source/heroine-01-face-module-v2.blend`、`art/source/heroine-01-right-eye-v3.blend` | 全身、臉髮衣飾及眼部三視圖已保存；臉部與眼睛有局部 Blender 試模，已在獨立分支保存，但與指定長相仍有明顯差距，未匯入 Unity | 在原工作樹保留母檔，先修眼瞼與眼角，再對正面／側面／45°；通過相似度、幾何與來源檢查後才合併可用角色部件。不要拿試模替換目前場景的玩家替身 |
| 村口站位角色、牌樓、採藥竹籃 | `art/source/qingxi-entry-assets-v13.blend`、`art/exports/qingxi-entry-assets-v13/`；原創三視圖見 `art/references/qingxi-entry-v13.md` | 可審圖原型，仍有結構與近景品質警告；站位角色不是 Heroine-01 成品 | 牌樓與竹籃先進場景檢查比例、碰撞和材質；站位角色只作尺度參考 |
| 聽風台 | `art/source/qingxi-listening-terrace-v1.blend`、`apps/game/Assets/YunJing/Models/QingxiListeningTerraceV1/` | 原創母檔、FBX、預覽與局部幾何 QA；已放入統一 Unity 場景、主要石構件具碰撞 | 實際走上台階，檢查石材、竹椅、遮擋與手機 LOD |
| 彎曲道路與橋邊小物 | `art/source/qingxi-road-props-v12.blend`、`art/exports/qingxi-road-props-v12/` | 三視圖先於模型；12 m S 路、木欄、晾架、路標原稿與 GLB 已保存 | 逐段放進入口步行線，修道路邊界、草石密度、材質與碰撞 |
| 河岸、植被、古樹與水 | `docs/qingxi-world-v8.md`、`docs/qingxi-world-v11.md` 及對應 `art/source/` | Blender 樣片、樹伴原樹移植與流動水預覽；遊戲中的水和樹葉仍未達參考畫面 | 在同一遊戲鏡頭下逐件調材質、根部入土、岸線轉接與 LOD；Unity 水流及手機效能另測 |
| 協作者環境轉接模組 | `art/incoming/dondon/EnvironmentTransitionKit/v001/`；joshsu54 的 PR #29 | 31 件已進儲存庫，保留原作者；尚未整批放進標準 Unity 場景 | 先挑主路所需道路邊、河岸、橋頭件，逐件量比例與碰撞；不直接整包鋪滿世界 |
| 較大城鎮與狩獵區 | `apps/game/Assets/QingxiWorld/` 及 `art/incoming/dondon/TownLayout/v004/` | 151 筆配置加狩獵灰盒已在統一試玩場景；TownLayout v004 仍是獨立高面數原件 | 沿入口至坊市選用代表建物，分區減面、材質、LOD、路線與玩法接入 |

本輪優先順序：先走通統一場景的入口路線，再接第一處靈草／練氣互動；Heroine-01 同步做**眼部單區相似度**，通過前不擴成整個頭、衣服或骨架。協作者交件按 `docs/work-ownership.md` 和 `docs/asset-integration-register.md` 接入，不覆寫核心組的母檔。
