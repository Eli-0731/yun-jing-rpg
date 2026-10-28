# 青溪回村整理 C

Eli-0731／Codex 實作；工作包規劃 z1nnz／Codex。基於 main `0f1e023434c4d080d7394d5ed34dd9a0015d9d08`，指定分支 `feature/qingxi-village-return-v1`。兩批交付：第一批 commit `fa37250`（四件道具＋兩個去向），第二批補齊八件、三個去向及驗證。

前一輪四件村口道具與三線索展示已先補交 [PR #34](https://github.com/z1nnz/yun-jing-rpg/pull/34)，commit `256299e`。本包不依賴該 PR，不複製其模型、不計入八件新物件。切換到該分支可看前一輪；兩個分支均從 main 獨立開始。本次前置補交實際經過約 40 分鐘，含環境、生成重試及上傳等待，不將預估 14 小時當作實作時數。upstream 對 Eli-0731 推送回覆 403，因此依協作規則使用 Eli-0731 自己的 fork 提 PR。

## 啟動與操作

直接開 [index.html](index.html) 可操作。PWA／離線快取需 localhost 或 HTTPS：

```powershell
node tools/qingxi-return-c/server.mjs
# http://127.0.0.1:4319
cd tools/qingxi-return-c
npm ci
npm test
npm run test:browser
```

瀏覽器測試使用 Playwright 1.56.1 及本機 Chrome，可用 `CHROME_PATH` 指定。選擇樣本後，以按鈕或場景標示選「保存／留待煉製／交委託（展示）」。Tab／Enter、滑鼠及橫向觸控均可使用。三個選項完全自由，可只整理一份或全部放同一處；重複點擊同一選項不加數量。取消按鈕只回復最近一次實際改動，再按無效；手札依每份樣本顯示來源與目前去向，過程紀錄保留最近 30 筆。場景可開闔手札、看八件近景及切換傍晚樣片；手機右欄和道具縮圖列可獨立捲動。

所有數字只表示三份固定本機展示樣本，專用 key `qingxi-return-c-v1`。沒有寫入正式背包、靈石、宗門貢獻或委託完成紀錄。可匯出 `qingxi-return-local-intents.json`，只有需服務端驗證的意圖與 UI 狀態，不含物品數量／獎勵。[正式接線草案與 UI 狀態表](handoff-contract.md)明示所有權、距離、requestId、並行、重啟與正式取消的邊界。localStorage 不保證跨分頁決策不互相覆寫，不能當正式資產存檔。

## 素材、參考與尺寸

八件各自以**內建 imagegen** 生成前／側／背及額外頂視參考，檢視並保存後才執行對應批次 Blender 建模。參考圖在 [art/references/qingxi-return-c](../../art/references/qingxi-return-c/)，完整提示詞與檢視限制在 [review.json](../../art/references/qingxi-return-c/review.json)。C03／C05 的 AI 側面比例不精確，已按指定尺寸校正；C06 為直腳簡化樣稿。所有幾何、材質紋理及程式由 Eli-0731／Codex 本輪原創，未使用第三方模型或其他組資產。圖片為實際 Blender 渲染。

| ID | 道具 | 寬 × 深 × 高（m，實測含附件） | 三角面 |
|---|---|---|---:|
| C01 | 回村背籠 | 0.481 × 0.392 × 0.600 | 1956 |
| C02 | 低木分揀桌 | 1.150 × 0.635 × 0.660 | 1512 |
| C03 | 收納竹匣 | 0.481 × 0.325 × 0.281 | 2400 |
| C04 | 藥草布包 | 0.351 × 0.296 × 0.162 | 712 |
| C05 | 委託封條盒 | 0.400 × 0.293 × 0.254 | 816 |
| C06 | 木製座凳 | 0.800 × 0.335 × 0.450 | 972 |
| C07 | 簡易油紙燈 | 0.280 × 0.280 × 0.587 | 1044 |
| C08 | 手札皮扣與木托 | 0.382 × 0.290 × 0.101 | 1188 |

母稿 [Qingxi_Return_C_batch2.blend](../../art/source/qingxi-return-c/Qingxi_Return_C_batch2.blend)保留八個獨立 Collection 與 3×4 m 審閱組裝。第一批母稿亦保留供版本比對。八個獨立 GLB 與實測／QA／回匯報告在 [art/exports/qingxi-return-c](../../art/exports/qingxi-return-c/)。Blender Z-up、前方 −Y；GLB Y-up、前方 +Z；GLB 已在組裝位移之前匯出，原點為各自地面中心座標系。C03/C04 在桌上，C08 在凳上，擺位資料見 `batch2-manifest.json`。

重建（Blender 4.5.3 LTS）：

```powershell
blender -b --python-exit-code 1 --python art/source/qingxi-return-c/build.py -- --batch 2
python art/source/qingxi-return-c/dimension_plan.py
```

[八件角落實際渲染](previews/return-corner.png)、[傍晚](previews/return-corner-dusk.png)、[帶數字的平面尺寸圖](previews/dimensions.svg)、[1.7 m 尺度參照](previews/scale-3x4m.png)及 C01–C08 逐件近景均在 `previews/`。木／竹／麻布紋理為原創 128×128 程序圖片，打包於母稿與 GLB；油紙燈為不透明暖色發光材質，不使用透明紙片。

## 驗證與限制

根目錄 `npm test` **55/55 通過**；本目錄狀態測試 **6/6 通過**。八件幾何檢查（UV、退化面、有限座標）與乾淨 Blender 場景 GLB 回匯尺寸比較通過，詳見 `batch2-manifest.json`。此檢查不代表完整量產拓樸或碰撞驗收。

[瀏覽器檢查報告](previews/browser-report.json)：本機 Chrome 的鍵盤、滑鼠、844×390 橫向觸控模擬、重載、取消、三去向、手札、離線、意圖匯出、無 localStorage 時的退回行為均通過，無頁面錯誤或資產 404。[桌面](previews/desktop-1280x720.png)、[橫向觸控模擬](previews/mobile-844x390.png)、[實際操作短片](previews/walkthrough.webm)（9.2 秒、1280×720）一併交付；短片涵蓋選樣本、改一次主意、取消與手札。錄影可設 `RECORD_VIDEO=1` 執行瀏覽器測試，需官方 Playwright FFmpeg 1011；安裝和快取放在忽略的工具目錄。

尚未完成：維護者或未參與製作的人之入口驗收、低 LOD、專用碰撞、細緻手繪／烘焙材質、手札 3D 開闔動畫、Unity／主場景接線、實體手機或多人效能。現為獨立可操作本機展示和簡化原創美術樣稿；單件共 10600 三角面，UV 可載入但未作專用光照展開。碰撞建議主體盒／背籠膠囊，繩紙不碰撞；LOD 規劃為 8m 後降低繩帶細節、小件20m剔除，尚非實測值。沒有修改角色、主 HUD、登入或正式 API。

此 checkout 以略過舊 LFS 素材下載的方式建立，全庫 `git lfs fsck` 會回報未下載的舊物件，不能宣稱全庫完整性已通過。本包新增 LFS 檔案另以工作檔、index 指標與本機 LFS 物件的 SHA-256 比對。上游 PR 的 GitHub Actions 首次 fork 執行需維護者核准，未代替維護者操作或合併。
