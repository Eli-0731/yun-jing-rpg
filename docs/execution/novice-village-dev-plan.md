# 青溪新手村｜開發計畫

> 這份是新手大世界 **P0／P1（A 青溪河谷的新手村）** 的細項。整個新手大世界（五區、八大主題、P0–P6 時程）見 [新手大世界整體開發計畫](novice-world-master-plan.md)。

2026-10-29，z1nnz 指定目標，Claude Code 整理。目標來自 z1nnz 的指示：

- 新手村要能在**瀏覽器上玩**，做成 PWA；
- 整體感覺往**原神璃月**靠，依五張世界方向圖逐區擴展；
- 房屋可以**進門**，室內是獨立空間；
- 道路要像方向圖那樣；
- 古樹用 elder-tree-esg 的成樹；
- 女主角由 z1nnz 在外部生成，再到 Blender 拼接。

方向與理由見 [璃月方向計畫](liyue-direction-plan.md)。每個計畫完成時，都要同時更新 Windows 版和 **WebGL／PWA 版**，並跑 smoke。

## 計畫 1：瀏覽器可玩的新手村（進行中）

| 項目 | 完成條件 |
|---|---|
| 1.1 手機觸控 | 左下虛擬搖桿、右半邊拖曳轉視角、跳／跑、F 互動與 E 次要鍵；沒有鍵盤的手機瀏覽器也能走完一圈 |
| 1.2 借住處進門 | 門口按 F → 推門、畫面淡出 → 獨立室內場景（床、箱子、蒲團）→ 淡入；從室內門口回到借住處門前 |
| 1.3 WebGL＋PWA | Unity WebGL 建置，用 PWA 範本（manifest、service worker、可安裝）；有本機靜態伺服器可開 |
| 1.4 瀏覽器驗證 | 在瀏覽器網址加 `?abc-smoke` 就跑同一套 smoke，結果印在 console；Windows 建置版 smoke 也要維持全過 |

已知限制：丹房的煉製要連本機 API。瀏覽器版可以進出丹房，但煉製本身要另外處理跨網域問題。

### 計畫 1 目前結果（2026-10-29）

- **1.1 觸控**：`QingxiTouchControls`。手機自動顯示；用滑鼠測試時，網址加 `?touch` 或按 T 也能打開。在林地裡會多出攻擊、試招、格擋、閃避、回安全點。走路元件和林地遭遇都改成沒有鍵盤也能運作。**尚未在實體手機上試過。**
- **1.2 進門**：`QingxiLodgingInteriorBuilder` 產生 `QingxiLodgingInterior` 場景。放了 joshsu54 的床、儲物箱和蒲團；在蒲團上可以練 Johnny 的引氣呼吸。門用 `QingxiSceneFade` 轉場：往門前推進並淡出 → 載入 → 淡入。**房間外殼是灰盒**（`Placeholder_*`），室內牆面、樑柱的模型要先做 AI 三視圖再建模。
- **1.3 WebGL＋PWA**：`./tools/unity.ps1 -Target NoviceVillageWebGL`，輸出到 `artifacts/webgl-novice-village/`，總計 88 MB（場景與模型 76 MB）；用 Unity 的 PWA 範本，附 manifest 和 service worker。本機伺服器：`node tools/qingxi-webgl/serve.mjs`，網址 `http://127.0.0.1:4190/`。
- **1.4 驗證**：Windows 建置版 smoke 31／31；**瀏覽器（WebGL 2.0）跑 `?abc-smoke` 也是 31／31**。
- **順手修到的重大錯誤**：專案沒有啟用 Unity 內建的 Terrain Physics 模組，建置版裡**地形沒有碰撞，玩家會穿過地面一直掉**。已在 `Packages/manifest.json` 加入 `com.unity.modules.terrainphysics`，smoke 也加了「地形碰撞撐得住」的檢查。以前的 smoke 沒抓到，是因為批次模式沒有鍵盤時，走路元件不會執行。
- **第二個重大錯誤（z1nnz 在瀏覽器試玩時發現）**：專案設定 `activeInputHandler: 0`（只開舊版輸入），但所有程式都用新版 Input System，所以 **Windows 版和瀏覽器版的鍵盤、滑鼠都沒有作用**。現在由新手村生成器設為 1。smoke 加了「按住 W 一秒，角色真的會走」的檢查，實測走了 4.1 m。
- **中文字型**：打包 Google 的 Noto Sans TC（介面）與 Noto Serif TC（標題、地名），授權為 SIL OFL 1.1，授權檔放在 `Resources/Fonts/`。uGUI 和 IMGUI 都改用這兩套字型；瀏覽器版也會把 joshsu54 丹房介面的系統字型換掉，因為瀏覽器裡沒有正黑體。
- **還沒解決**：
  - 88 MB 對手機偏大，之後要做貼圖壓縮和場景資料瘦身。
  - URP 有兩個除錯用 shader 在 WebGL 上不支援，畫面目前看不出影響。

## 計畫 2：溪與道路

- 地形資料加入溪流中心線：沿溪挖渠、做水面，並加一處小瀑布。
- 河岸與路緣用 joshsu54 的 EnvironmentTransitionKit 模組；臨水段做石砌護岸，對照河岸三視圖。
- 路面改成泥土加碎石兩層；路緣自動散布石塊與草叢。
- 完成條件：從村口看得到溪、橋、護岸；接地驗收失敗 0；在瀏覽器版能走過溪上的橋。

## 計畫 3：第一張「璃月明信片」

- URP 後處理：高度霧、色調、Bloom；遠景石峰與雲海；竹林與花田散布。
- 古樹地標：先做 LOD 和葉片合批，再放進村子中心。
- 完成條件：村口眼高截圖和方向圖 A 擺在一起比較；手機瀏覽器維持可接受的幀數（實測數字寫進文件）。

## 計畫 4：第一個服務端循環

- 採草：靠近 → F → API 結算 → 背包 → 重新登入後仍在（進度表第 3 步）。
- 坊市出售和山兔掉落接上服務端（進度表第 4 步）。

## 計畫 5：女主角與更多室內

- 依 [女主角拼接說明](heroine-blender-assembly-brief.md) 把外部生成的女主角拼好，接成可操作角色。
- 丹房和更多房屋做室內；之後依五張方向圖逐區擴展。

## 不在近期範圍

整個大世界、多人連線、宗門。這些要等以上各區通過效能與玩法驗收後再做。
