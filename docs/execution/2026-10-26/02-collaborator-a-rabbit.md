# 協助者 A：山兔生產資產執行單

日期：2026-10-26  
工時：6 小時  
對應 Issue：[山兔骨架、動畫與 Unity 匯出 #8](https://github.com/z1nnz/yun-jing-rpg/issues/8)

## 任務目標

把既有的靜態山兔外觀原型整理成可供狩獵玩法使用的生物資產。不要重新設計玩法、API、掉落或場景；這一輪只負責骨架、動畫、碰撞／LOD 資料、匯出及交接證據。

## 必須使用的來源

- [QMountainRabbit_v002.blend](../../../art/incoming/dondon/QMountainRabbit/v002/QMountainRabbit_v002.blend)
- [QMountainRabbit_v002.fbx](../../../art/incoming/dondon/QMountainRabbit/v002/QMountainRabbit_v002.fbx)
- [model_info.json](../../../art/incoming/dondon/QMountainRabbit/v002/model_info.json)
- [現有預覽](../../../art/incoming/dondon/QMountainRabbit/v002/previews/QMountainRabbit_v002_render_512.png)
- [驗證限制](../../../art/incoming/dondon/QMountainRabbit/v002/README.md)

現況是 0.47 × 0.689 × 0.758 m、19 個網格、22,192 三角面、5 個材質，沒有骨架、動畫、專用碰撞與 LOD。來源資料夾 art/incoming/dondon/ 是交接原件，不得覆寫。

## 三視圖規則

這次是在既有模型上做綁骨、動畫、LOD 與碰撞，沒有改變外觀，所以可直接開始。若要改頭身、耳朵、腿型、輪廓或新增配件，先停止幾何修改，通知核心組生成並保存新的 AI 三視圖；三視圖放入 art/references/qingxi-mountain-rabbit-v003/ 並經檢視後才能繼續。

## 輸出位置

不要動來源檔。新增：

    art/source/qingxi-mountain-rabbit-v003/
      QingxiMountainRabbit_v003.blend
      README.md
      model_info.json
      validation.json
      previews/front.png
      previews/side.png
      previews/rear.png
      previews/idle.png
      previews/run.png
      previews/death.png

    art/exports/qingxi-mountain-rabbit-v003/
      QingxiMountainRabbit_v003.fbx
      QingxiMountainRabbit_v003.glb
      validation.json

Unity 匯入檔由核心組整合前放至：

    apps/game/Assets/YunJing/Models/QingxiMountainRabbitV003/

## 骨架規格

- 一個根骨控制整體，原點保持在地面中心，Z 向上。
- 至少包含骨盆、脊椎、頸、頭、左右耳、前腿與後腿；腿部使用一致命名。
- 左右權重對稱，耳朵可有輕微次級動作；不能讓腹部或腳掌明顯拉裂。
- 循環動作全部做成原地動畫，實際位移由遊戲伺服器與角色控制器決定。
- 套用縮放後再匯出；場景單位使用公尺。
- Clip 名稱：Rabbit_Idle、Rabbit_Hop、Rabbit_Flee、Rabbit_Hit、Rabbit_Death。

## 五組必要動畫

專案目前以 24 fps 製作這一批動畫：

| Clip | 建議長度 | 循環 | 必須看得出的行為 |
|---|---:|---|---|
| Rabbit_Idle | 48 幀 | 是 | 呼吸、耳朵觀察、重心穩定 |
| Rabbit_Hop | 24 幀 | 是 | 低速小跳，落地腳掌不滑動 |
| Rabbit_Flee | 16 幀 | 是 | 快速逃跑，後腿有推進力 |
| Rabbit_Hit | 8 幀 | 否 | 短促受擊，不轉成死亡 |
| Rabbit_Death | 24 幀 | 否 | 清楚倒地，最後姿勢保持 |

可另做 Rabbit_Alert，但五個必要 Clip 未完成前不要增加範圍。動畫事件與音效事件由核心組在 Unity 設定；FBX 不寫發獎邏輯。

## LOD、材質與碰撞

- LOD0：保留輪廓，不超過 22,500 三角面。
- LOD1：10,000–12,000 三角面，臉與耳朵仍可辨識。
- LOD2：3,500–5,000 三角面，遠距離保留主要輪廓。
- 材質槽目標 2 個、最高 3 個；無法合併時在 README 說明。
- 保留可重做的 Blender 修改器，不為降面破壞母稿。
- 建立簡化碰撞參考：身體膠囊約高 0.62 m、半徑 0.22 m，另提供頭部球體建議。
- 不使用可見模型的 19 個網格直接作 MeshCollider。

## 六小時安排

| 時段 | 工作 | 交付 |
|---|---|---|
| 0:00–0:30 | 複製母稿、檢查比例、命名與變形風險 | 新母稿與檢查紀錄 |
| 0:30–1:30 | 建骨架、控制器、權重 | 可擺姿勢的完整 rig |
| 1:30–3:20 | 五組必要動畫 | Actions／NLA clip |
| 3:20–4:20 | LOD1、LOD2、材質整理 | 三層網格與材質表 |
| 4:20–5:05 | FBX、GLB 匯出與回匯 | 交換檔及回匯資料 |
| 5:05–5:35 | 預覽、數值與穿模檢查 | PNG 與 validation.json |
| 5:35–6:00 | README、提交、PR | 可重現的交接說明 |

## 驗證方式

1. 重新開啟 .blend，五個 Action 仍存在且播放正常。
2. 逐一播放循环，確認腳掌沒有持續滑動、耳朵和腿不翻面。
3. FBX 回匯到空白 Blender 場景，尺寸與原稿誤差小於 1 mm。
4. 每個 clip 起訖幀正確，死亡不勾選循環。
5. LOD 數量、材質槽、三角面、骨數寫入 model_info.json。
6. 預覽包含正、側、後和三個關鍵動作。
7. 若能開 Unity，檢查 Avatar、clip、材質、比例與動畫；若授權仍無效，只能寫「Blender/FBX 已驗證，Unity 未驗證」。

## Git 工作方式

1. 從最新 main 建立 assets/rabbit-rig-v003。
2. 大型二進位檔確認由 Git LFS 追蹤後再加入。
3. PR 連結 Issue #8，列出三角面、材質、骨數、clip 與驗證工具版本。
4. 不修改 services/、packages/content/、主場景或來源交接資料夾。

## 完成定義

- 生產版 .blend、FBX、GLB、五組動畫、LOD0/1/2、碰撞建議、預覽與驗證紀錄齊全。
- 原始 v002 完全未改動。
- 模型比例和原點符合規格，循環動畫無明顯破面與滑步。
- 清楚區分 Blender 已驗證與 Unity 是否真的完成匯入。
