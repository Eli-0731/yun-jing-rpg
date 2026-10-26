# Heroine-01｜從概念畫到角色網格的相似度工序

**2026-10-26；角色尚未建成。** [完整三視圖](../../art/references/heroine-01/turnaround/front-left-back-v1.png)與[臉／髮／服裝近景](../../art/references/heroine-01/details/face-hair-costume-v1.png)是本作原創造型基準。[右眼局部三視圖](../../art/references/heroine-01/eye-study/right-eye-three-view-v1.png)已在建模前生成、檢視並保存。三角度圖屬 AI 推定參考，尤其側面輪廓與皮膚細節不能冒稱來自原短劇影片。

## 前一版頭部為何失敗

曾用球、管狀曲線與獨立小物拼成整頭研究件。正面與四分之三預覽跟參考圖差很多：眼眶沒有包覆眼球，鼻樑與鼻翼是貼上的橢球，嘴唇是兩條管線，瀏海像繩子，臉頰／下顎缺少自然連續的轉折。Blender 資產 QA 也報出缺 UV、重複頂點、退化面和游離裝飾。**該初稿未合併到 `main`，不可用作下一階段的基礎網格。** 問題在造型與拓樸，繼續加髮飾或渲染光效無法修好相似度。

## 查到的製作依據與適用界線

- [《原神》官方角色創作幕後](https://www.youtube.com/watch?v=PdVijhI9bK0)提供角色創作的視覺方向參考；公開片段不足以證明米哈遊的內部拓樸、材質節點或製作工時。本作只參考「輪廓、服飾分層、動作和畫面協調」的品質目標，不照搬角色資產。
- [Epic 的風格化角色製作教學](https://dev.epicgames.com/documentation/metahuman/metahuman-stylized-character-tutorial)明確區分原始造型、可用於遊戲的拓樸與貼圖、表情變形、髮型和材質；這裡借用工序，沒有改用 Unreal 或 MetaHuman。
- [Epic 的局部臉部雕塑工具](https://dev.epicgames.com/documentation/metahuman/metahuman-creator-head-sculpt-tool-in-unreal-engine)將臉部特徵分區調整。這支持我們先驗眼周小區域，但**不能**由單個眼睛自動推得整張相似的臉。
- [Blender 的重拓樸說明](https://docs.blender.org/manual/en/latest/modeling/meshes/retopology.html)與本地 `blender-retopology-uv` 技能都指出：可變形角色需要整理眼口周圍環線。自動減面只適合原型或背景，不足以替代主角的眼、嘴與肩部手工拓樸。
- [Blender 官方 Human Base Meshes](https://developer.blender.org/docs/release_notes/3.6/asset_bundles/) 提供具四邊形、UV 與面部環線的通用起點；本機已從[官方檔案目錄](https://download.blender.org/demo/asset-bundles/human-base-meshes/)取得 v1.4.1，SHA-256 為 `811f43accbb31a88266d932f8f5563b2d13586fca0ba2693aad1f5fe582b3515`，只存於忽略的 `output/` 研究區。它是 **CC0 起始網格，不是 Heroine-01**；前一個球體拼接眼周試模仍不像概念畫，所以不合併。下一次要在此網格的現有眼瞼環線上局部雕塑並重拍比較，而非直接使用原始臉型。
- [Epic 的髮片與髮絲製作案例](https://dev.epicgames.com/documentation/ar-ar/unreal-engine/digital-humans?application_version=4.27)及[行動裝置 LOD 說明](https://dev.epicgames.com/documentation/pt-br/metahuman/platform-support-and-lod-specifications-for-metahumans?application_version=5.0-5.5)顯示近景與手機髮型需要不同表示方式。等臉與大髮型通過後，先用髮束定輪廓，再為手機試驗髮片／LOD；不能用現在的圓管髮當完成品。
- [Adobe 的高低模烘焙流程](https://experienceleague.adobe.com/en/docs/substance-3d/bakers/home)解釋高模細節如何轉成遊戲貼圖；材質細節應在造型相似、低模 UV 穩定後再投入。

上述工序是根據公開官方文件制定的**本專案做法**，並非宣稱知道《原神》或《崩壞：星穹鐵道》的內部製作配方。

## 改成局部關卡，每一關先並排看圖

| 關卡 | 只處理這一區 | 通過條件；未過不可往下加細節 |
|---|---|---|
| 0 參考 | 固定同一人物正面、側面、四分之三；標出眼角、虹膜、眼瞼最高點、眉峰與眉尾 | 各角度身份一致；記錄 AI 推定或矛盾處，不能依一張圖猜整頭深度 |
| 1 右眼 10 cm 小區 | 眼球、上／下眼瞼、內外眼角、眉骨與少量面頰，**不做完整頭與頭髮** | 灰模正面與 45° 並排；眼瞼貼合球面，眼角不懸空，輪廓與參考圖可對應；必須可編輯、無退化面 |
| 2 雙眼＋鼻梁 | 複製並微調另一眼，連接額、鼻梁與鼻翼 | 五官間距與深度從正／側／45° 都成立，沒有貼球感 |
| 3 嘴與下顎 | 嘴唇、口角、鼻唇區、下顎 | 嘴與皮膚連成形體，非兩條曲線；對照臉部近景的人物辨識度 |
| 4 大髮型與飾品 | 顱頂、半盤髮、兩束胸前長髮、銀葉青花 | 先定主輪廓，再分髮束與手機髮片；飾品有接點和遊戲鏡頭辨識度 |
| 5 全身服裝 | 交領、白藍疊衣、長袖和腰封 | 正側背一致，袖口、裙襬可變形；與頭比例相符 |
| 6 遊戲化 | 手工重拓樸、UV、貼圖烘焙、骨架、表情、LOD | QA 通過、回匯尺寸一致、極端動作不穿模；手機幀時與畫面另實測 |

每關只交**該區的 `.blend`、正／側／45° 灰模圖、參考並排圖和 QA 結果**。參考圖的眼睛比前一版更圓潤、內眼角更低、上瞼覆蓋虹膜更深；眉不是單條均勻粗線。這些是優先修正的形狀關係，不是先加睫毛根數或皮膚毛孔。不得把 AI 圖當材質貼在平面上宣稱 3D 模型完成。

## 驗收原則

角色相似度優先於交件速度。正面接近但 45° 一看就變人、遊戲鏡頭看不到辨識點、沒有 UV／可用拓樸，任何一項都不能叫「女主角建好了」。PWA 可做圖片與局部模型審看；Unity Hub 登入、Editor 授權、Unity 編譯和手機畫面各是不同驗證，須分開紀錄。
