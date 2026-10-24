# 協助者 B：青溪狩獵區灰盒執行單

日期：2026-10-26  
工時：6 小時  
對應 Issue：[青溪狩獵區灰盒與導航 #9](https://github.com/z1nnz/yun-jing-rpg/issues/9)

## 任務目標

做出一個可驗證移動、追蹤、山兔逃跑路徑和回村出售節奏的獨立灰盒。這不是最後大世界，也不是美術場景；優先確保玩家走得通、看得懂環境線索、山兔有地方逃、手機鏡頭不被牆與樹卡住。

不要修改正式 Qingxi.unity、戰鬥程式、API、山兔模型或協助者 A 的檔案。

## 連結既有內容

先閱讀：

- [目前狀態](../../status.md)
- [世界與山兔來源清單](../../素材交接清單-dondon.md)
- [青溪內容](../../../packages/content/qingxi.json)
- [現有場景產生器](../../../apps/game/Assets/YunJing/Editor/ProjectBuilder.cs)

可使用下列既有交接素材作視覺或比例參考：

- art/incoming/dondon/CommonPine/v001/
- art/incoming/dondon/BambooClump/v001/
- art/incoming/dondon/LayeredCliff/v001/
- art/incoming/dondon/MossBoulderSet/v001/
- art/incoming/dondon/MountainStonePath/v001/
- art/incoming/dondon/MountainStreamBend/v001/
- art/incoming/dondon/NoticeBoard/v002/
- art/incoming/dondon/MaterialShop/v001/

這些素材尚未全部在 Unity 驗收。匯入失敗時先用基本幾何體，不要花時間修模型，也不要宣稱它們已能正式使用。

## 場景結構

新增獨立產生器：

    apps/game/Assets/YunJing/Editor/QingxiHuntGrayboxBuilder.cs

由它產生：

    apps/game/Assets/YunJing/Generated/QingxiHuntGraybox.unity

Generated 場景視為可重建產物；所有關鍵尺寸、出生點與標記在 Builder 或版本化設定中有來源。不要手動改二進位場景後只交一個無法重現的 Unity 檔。

## 地圖尺寸與分區

灰盒總占地約 220 × 160 m，採彎曲路徑遮擋遠景，不要求一次看見整張圖。

| 區域 | 目標尺寸 | 用途 |
|---|---:|---|
| 聚落出口 | 30 × 24 m | 玩家出生、材料商販、回程結算 |
| 過渡山道 | 長約 60 m、寬 5–10 m | 教玩家看腳印和草叢動靜 |
| 採藥林 | 50 × 40 m | 青靈草、遮蔽物、非戰鬥選擇 |
| 山兔草坡 | 80 × 60 m | 3 個兔群活動區、追逐與失手 |
| 溪流淺灘 | 40 × 30 m | 岸石、淺水、替代回程 |
| 回村捷徑 | 長約 70 m | 狩獵後減少重走時間 |

## 必放標記

使用空物件或清楚的 Gizmo 命名：

- PlayerSpawn_01、PlayerSpawn_02
- Merchant_Material
- TrailClue_01 至 TrailClue_06
- RabbitSpawn_A01/A02、B01/B02、C01/C02
- RabbitFlee_A01 至 A03、B01 至 B03、C01 至 C03
- HerbNode_01 至 HerbNode_06
- SafeReturn_01
- AreaBoundary_Hunt
- NavBlocker_* 與 CameraBlocker_*

每個兔群至少有三個互相可達的逃跑點，逃跑路徑不能穿過陡壁、深水或碰撞體。出生點彼此相隔至少 8 m，避免兔群疊在一起。

## 玩家節奏

1. 聚落出口能看見山道，但不能直接看見所有兔子。
2. 第一個線索在 20–30 秒步行內出現。
3. 第一隻兔子在未奔跑探索時約 60–90 秒可發現。
4. 玩家追丟兔子後能由腳印、草動或地形重新判斷方向。
5. 採藥林提供不戰鬥的收益，玩家不會因為沒狩獵就毫無進展。
6. 首次完成狩獵後，回村捷徑將返程控制在 60 秒左右。
7. 地圖不使用倒數計時催促，也不以任務箭頭鎖住唯一走法。

## 導航、碰撞與鏡頭

- 地面坡度以第三人稱角色可穩定通行為準；主要路線避免超過 35°。
- 高於約 0.4 m 的落差要有坡道、階梯或清楚阻擋。
- 溪流可走區深度保持淺，深水先以阻擋體封閉。
- 山兔可用獨立較小 Agent 半徑；逃跑點必須落在可導航區域。
- 樹、岩石與建築使用簡化 Collider，不用高面數 MeshCollider。
- 狹路寬度至少 2.5 m，保留 4 人經過的空間。
- 測試相機距離 3.5–6 m；所有轉角確認沒有長時間遮住角色。
- 提供 Scene 視圖鳥瞰截圖和六個主要路段的遊玩視角截圖。

## 六小時安排

| 時段 | 工作 | 交付 |
|---|---|---|
| 0:00–0:35 | 畫平面配置、鎖定尺寸與命名 | layout.png／座標表 |
| 0:35–2:15 | 建立可重建 Builder 與六個分區 | 灰盒場景 |
| 2:15–3:05 | 放出生、線索、採集、逃跑與商販標記 | 完整標記表 |
| 3:05–4:05 | 導航、碰撞、坡度與邊界 | 可走通的主要／替代路線 |
| 4:05–4:50 | 相機、視線與回程節奏 | 截圖及問題紀錄 |
| 4:50–5:30 | 2 人與山兔占位物路線演練 | 路徑測試紀錄 |
| 5:30–6:00 | README、提交、PR | 重建方式與限制 |

## 沒有 Unity 授權時

仍然交付：

- layout.png。
- 所有標記的座標 JSON。
- Builder 原始碼草稿。
- 尺寸、坡度、視線和預期路線說明。
- 明確寫「未經 Unity 編譯、NavMesh 未實測」。

不要提交偽造截圖，也不要把單純寫出 C# 當作場景可以運行。

## Git 工作方式

1. 從最新 main 建立 feature/qingxi-hunt-graybox。
2. 只修改自己的 Builder、灰盒說明和必要的測試資料。
3. PR 連結 Issue #9，列出重建步驟、Unity 版本及實際完成的驗證。
4. 不修改 ProjectBuilder.cs 的正式 Qingxi 產生流程；核心組整合時再決定合併方式。

## 完成定義

- 六個分區、全部標記、主路和替代回程存在。
- 兩名玩家出生不重疊，主要路線不會卡死。
- 三組山兔各有合法活動與逃跑點。
- 場景可由 Builder 重建，沒有只存在於某台電腦的手動狀態。
- 有鳥瞰、路段截圖與測試紀錄；Unity 未驗證時清楚揭露。
