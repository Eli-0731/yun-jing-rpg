# 2026-10-27 演武區交付驗證

驗證基準：`feature/qingxi-training-yard-v1` 最初建於 main `b2a57673751057ff6c31538d72a73898c350e7d6`，提交前已同步至 main `8a78796954e99eb7c3116e219fc2cd40bf634413`。作者／Git 提交身分為 Johnnnny0823 `<johnsnow94823@gmail.com>`；Codex 執行建模、網頁展示與檢查。六件 AI 三視圖保存於 `art/references/qingxi-training-yard-v1/`，使用者授權先建模，但手機端仍待目視審閱。這是自製資產候選版，不宣稱已達《鳴潮》正式美術審核品質。

## Blender 與匯出

- 使用 Blender 5.2.2，`build_yard.py` 在獨立背景程序建立六 Collection、可編輯母檔和 Base Color／Roughness／Normal 圖。
- `review_yard.py` 對六 Collection 跑 `blender-asset-qa` 的 game profile：六件 `pass=true`，沒有錯誤。詳細輸出見 `qa-report.json`。共享平鋪 UV 和圓柱端蓋 n-gon 有警告，未做逐件光照烘焙。
- `export_yard.py` 套用修改器，逐件匯出一個 GLB，再清空場景逐件匯回；六件均有網格、UV、材質、尺寸與匯出三角面數一致。詳細資料見 `../../exports/qingxi-training-yard-v1/asset-manifest.json`。
- 匯出三角面數：演武棚 39,236；氣勁木樁 14,156；身法木樁 6,492；兵器架 4,032；刻紋練功石 3,532；練功旗 9,012。合計 76,460。遊戲版每件一個合併網格；母檔保留可編輯分件。
- 演武棚入口坡道寬 3.40 m、台基高 0.12 m；無中央柱。碰撞建議在 `../../exports/qingxi-training-yard-v1/collision-proxies.json`，Unity Collider 尚未建立。

## 本機展示

- `npm test --prefix tools/training-yard-demo`：7/7 通過。
- 真實 Chromium：1280×720 和 844×390 視窗中六 GLB 皆載入；1.7 m 眼高由村口走進石坡，靠近木樁出現互動。
- 實際瀏覽器完成凡骨武技六次格擋，顯示 `節奏 6/6 · 成功 6 次`；凡骨引氣按鈕禁用。切換有靈根後完成三輪吸／吐，顯示 `節奏 6/6 · 成功 6 次`；兩種結束狀態均可重試。
- 本機展示不發 API 請求、不存持久狀態、不製造修為。刷新後重新開始。這些是桌面瀏覽器模擬的橫向視窗和指標操作，不是實體手機觸控或 FPS 驗證。

## 預覽

- `eye-height-1.7m.png`、`yard-overview.png`：Blender 實際模型渲染。
- `gameplay-desktop-1280x720.png`、`gameplay-landscape-844x390.png`：實際瀏覽器遊戲視窗。
- `gameplay-qi-breathing.png`、`gameplay-qi-complete.png`、`gameplay-martial-landscape.png`：實際操作 UI。另有六件近景 `*-detail.png`。

## 尚未接入或驗證

- Unity 6000.0.82f1 編譯、Generic/Prefab/URP 材質與碰撞設定；核心入口場景和村口路線的正式接線。
- 服務端 `POST /actions` 的 `practice-basic` 認證、requestId、冷卻、獎勵帳本；此 demo 節奏結果不得直接兌換修為。
- 實機觸控、手機 GPU／FPS／記憶體；正式美術主管針對《鳴潮》品質的逐件審核、材質風格及優化。
