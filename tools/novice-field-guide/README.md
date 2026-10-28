# 青溪村內告示與三段小探索

作者：Eli-0731／Codex 實作；工作包規劃：z1nnz／Codex。基於 main `0f1e023434c4d080d7394d5ed34dd9a0015d9d08`，分支 `feature/qingxi-novice-field-guide-v1`。這是 10/29 郵件要求先補交的 10/27 工作，不計入 10/29 的八件新模型。

直接開 `index.html` 可使用互動；安裝與離線快取需 localhost 或 HTTPS：

```powershell
cd tools/novice-field-guide
node server.mjs
# 瀏覽 http://127.0.0.1:4317
npm ci
npm test
npm run test:browser
```

執行瀏覽器測試使用 Playwright 1.56.1 與本機 Chrome；可用 `CHROME_PATH` 指定瀏覽器。測試不需要額外下載 Chromium。Chrome 的手機視窗為觸控模擬，不代表真機效能。

方向鍵／WASD 移動，E 與附近木牌互動；滑鼠、Tab／Enter 和觸控可直接選地標。三事件任意順序、可重讀改選，返回告示查看紀錄。手札顯示三個可選方向，找到全部線索後加一段青溪文字。資料只寫本瀏覽器專用 key `qingxi-c-field-guide-v1`，無登入、正式背包、資產或獎勵 API。

四件新道具先用內建 imagegen 逐件生成，檢視後存於 `art/references/qingxi-village-signs-v1/Q01–Q04-three-view.png`，提示詞和視角限制見 `review.json`；之後才建立 Blender 4.5.3 母稿。幾何、材質、程式均由 Eli-0731／Codex 原創，未挪用其他組模型或第三方資產。木紋為自製 128×128 程序紋理，已打包並嵌入 GLB。圖片是原稿實際渲染，並非 AI 完成圖。

| ID | 道具 | 寬 × 深 × 高（m） | 三角面 |
|---|---|---|---:|
| Q01 | 村口告示 | 1.250 × 0.553 × 1.765 | 4248 |
| Q02 | 劍痕木牌 | 0.480 × 0.363 × 0.829 | 376 |
| Q03 | 採藥標記 | 0.247 × 0.217 × 1.050 | 1136 |
| Q04 | 客舍留言板 | 0.850 × 0.420 × 1.241 | 3488 |

母稿 `art/source/qingxi-village-signs-v1/Qingxi_Village_Signs_v1.blend`，四個獨立 Collection；每件 GLB、面數、尺寸和回匯結果在 `art/exports/qingxi-village-signs-v1/`。Blender Z-up，正面 -Y；GLB Y-up、正面 +Z；原點使用資產共同地面中心座標系，幾何已落地。重建命令：`blender -b --python-exit-code 1 --python art/source/qingxi-village-signs-v1/build.py`。腳本檢查已保存的前置參考，檢查 UV、退化面、非有限座標，輸出後在乾淨場景回匯比較尺寸。結構接點的隱藏內面尚未逐一刪除；此 QA 不包含完整碰撞或拓樸量產驗收。

建議碰撞：主體簡化盒或膠囊，繩索、紙片不碰撞；單層原型 LOD，建議整合時 25 m 剔除，低 LOD 尚未交付。沒有修改 Unity、角色、主 HUD、API 或核心場景。未做 Unity 匯入、實機手機、多人大世界或完整美術精修。

本輪驗證：狀態單元測試 3 項；桌面 1280×720 與 844×390 橫向觸控模擬、三事件、重訪、重載、手札、鍵盤與離線重載流程通過，詳見 `previews/browser-report.json`。根目錄 `npm test` 在沙箱外 55/55 通過；沙箱內曾出現 PGlite abort 與 localhost EACCES，不改產品程式繞過限制。四件 GLB 回匯及幾何檢查通過；`previews/` 附近景、總覽及桌面／手機畫面。
