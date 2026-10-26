# Qingxi Mountain Rabbit v003

協作者 A 的山兔資產候選版，對應 [Issue #8](https://github.com/z1nnz/yun-jing-rpg/issues/8) 與 `docs/execution/2026-10-26/02-collaborator-a-rabbit.md`。沿用 Dondon v002 外觀，不重新設計兔子輪廓。`art/incoming/dondon/` 原件未修改。

## 來源與作者

- 原外觀模型：`joshsu54/dondon2.0` 的 `QMountainRabbit/v002`，原作者／建模流程見[來源 README](../../incoming/dondon/QMountainRabbit/v002/README.md)。來源 `.blend` SHA-256 記於 `validation.json`。
- 本次骨架、五段動畫、LOD、碰撞參考、貼圖、匯出與檢查腳本：Codex agent 依專案協作者指示製作。未將原外觀歸為本次作者創作。
- 來源儲存庫未提供授權檔。正式使用條件需由 `joshsu54` 與 `z1nnz` 確認。

## 交付

| 類別 | 檔案／內容 |
| --- | --- |
| Blender 母稿 | `QingxiMountainRabbit_v003.blend`；`rabbit_model.py` 可由 v002 重建 |
| 主交換檔 | `../../exports/qingxi-mountain-rabbit-v003/QingxiMountainRabbit_v003.fbx`、`.glb` |
| 獨立動畫 FBX | `Rabbit_Idle/Hop/Flee/Hit/Death.fbx`；主 FBX 與 GLB 也含五段動畫 |
| LOD FBX | `QingxiMountainRabbit_v003_LOD1.fbx`、`LOD2.fbx` |
| 貼圖 | `textures/T_Rabbit_BaseColor.png`、`T_Rabbit_Roughness.png`、`T_Rabbit_Normal.png` |
| 數值與回匯證據 | `model_info.json`、`validation.json`、交換檔目錄中的 `validation.json` |
| 預覽 | [正面](../../previews/qingxi-mountain-rabbit-v003/front.png)、[側面](../../previews/qingxi-mountain-rabbit-v003/side.png)、[背面](../../previews/qingxi-mountain-rabbit-v003/rear.png)、[45 度](../../previews/qingxi-mountain-rabbit-v003/three_quarter.png)、[站立](../../previews/qingxi-mountain-rabbit-v003/idle.png)、[深蹲](../../previews/qingxi-mountain-rabbit-v003/crouch.png)、[起跳](../../previews/qingxi-mountain-rabbit-v003/jump_start.png)、[空中](../../previews/qingxi-mountain-rabbit-v003/jump_air.png)、[落地](../../previews/qingxi-mountain-rabbit-v003/jump_land.png)、[逃跑](../../previews/qingxi-mountain-rabbit-v003/flee.png)、[受擊](../../previews/qingxi-mountain-rabbit-v003/hit.png)、[死亡](../../previews/qingxi-mountain-rabbit-v003/death.png) |

## 規格

- 單位公尺；正面 -Y；Z 向上；原點在地面中心。原稿外框 0.470 × 0.689 × 0.758 m。
- 17 根骨（Root、Pelvis、Spine、Chest、Neck、Head、Tail、左右耳及前後腿）；Generic 四足骨架。所有頂點有權重，每點不超過四個影響骨；一個材質槽。
- LOD0 22,192、LOD1 10,842、LOD2 4,418 三角面。LOD0／1／2 各為一個可蒙皮網格。來源的 19 個外觀物件複製、降面並合併；來源物件藏於母稿的唯讀參照 Collection。
- 24 fps：Idle 48 幀循環、Hop 24 幀循環、Flee 16 幀循環、Hit 8 幀不循環、Death 24 幀不循環。循環首尾姿勢一致，水平根骨位移為零；跳躍含局部視覺抬升，Unity 應關閉 Apply Root Motion，由單一移動系統控制世界位移。
- 碰撞參考：身體膠囊高約 0.62 m、半徑 0.22 m；頭球半徑約 0.15 m。參考代理不匯出，核心組以 Unity primitive collider 重建。

## 已驗證

Blender 5.2.2 LTS 重新開啟 `.blend`；五段 Action 存在；FBX 主檔、兩個 LOD FBX、五個獨立動作 FBX 及 GLB 在空白場景回匯。LOD 三角面、材質槽、骨數、貼圖、權重與每幀最低點檢查見 `validation.json`。FBX／GLB 主檔回匯尺寸與來源外框差值小於 1 mm。另有[四視角線框檢視](../../previews/qingxi-mountain-rabbit-v003/qa_wire.png)；LOD0/1/2 的 `blender-asset-qa` 遊戲設定檢查通過，唯一警告是色帶 UV 約 100% 重疊，屬本次單色圖集的刻意用法。獨立動作 FBX 回匯名稱會成為 `RIG_QingxiRabbit|Scene`，應依檔名指定 Unity clip；主 FBX 與 GLB 保有五段原名稱。

## 接入及限制

- **尚未做 Unity 6000.0.82f1 匯入、Generic Avatar／Animator Controller、URP 貼圖掛接、遊戲碰撞、跳躍物理、真人操作與手機效能測試。** Blender/FBX/GLB 驗證不等於 Unity 可玩。
- v002 原外觀由 19 個相交的封閉網格島組成。本次各 LOD 雖合併為一個網格，但沒有把表面重拓樸成連續兔子皮膚；大幅度蹲跳、轉向及近鏡頭關節變形仍需核心組目視驗收。Rig 無 IK 控制器，也未製作 Run/Turn 等延伸動畫。
- UV 是單色材質的共用色帶，允許重疊；不適合直接烘焙細節 AO／法線。Normal 是平面佔位貼圖，Roughness 是常數貼圖，未聲稱已完成細緻毛流或手機優化。
- 此包不含 AI 新三視圖，因為沿用 v002 外觀而沒有改頭身、耳朵、腿型或配件。若要外觀重製，先依專案規則製作並保存三視圖。

## 重建與驗證

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' -b --factory-startup --python-exit-code 1 --python art/source/qingxi-mountain-rabbit-v003/rabbit_model.py
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' -b --python-exit-code 1 --python art/source/qingxi-mountain-rabbit-v003/export_rabbit.py
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' -b --python-exit-code 1 --python art/source/qingxi-mountain-rabbit-v003/render_previews.py
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' -b --python-exit-code 1 --python art/source/qingxi-mountain-rabbit-v003/validate_rabbit.py
```
