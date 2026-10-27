# PHASE 0｜工具與檔案保護檢查（2026-10-26）

**受保護資產：未修改；本次新建專案路徑：`/home/user/dondon/Environment_Transition_Kit/`**

## 工具狀態

| 工具 | 狀態 | 能做 | 不能做 |
| --- | --- | --- | --- |
| Blender | 5.2.3 LTS，Linux，命令列背景模式（`blender -b`）；每次腳本都是新開、未載入任何檔案的獨立程序 | 建模、UV、材質、烘焙、渲染、FBX 匯出／回匯、幾何檢查 | 無法操作使用者電腦上已開啟的 Blender |
| Blender MCP | 本雲端工作階段**未連線** | — | 不能讀取或控制使用者本機的 Blender 場景 |
| 圖像生成 | 本工作階段**沒有**可用的生圖工具 | 以 Blender 渲染＋Python（Pillow）產生可驗算的工程圖與模組總表 | 不能產生 AI 概念圖；改附英文提示詞 `00_References/IMAGE_PROMPTS.md` |
| Python 3.13＋Pillow | 可用 | 報表、標註排版、CSV／JSON | — |

## 隔離確認

- 背景 Blender 啟動時 `bpy.data.filepath = ''`，場景只有預設的 Camera／Cube／Light，沒有開啟任何既有 `.blend`。所有建模腳本啟動時都會再次斷言 `bpy.data.filepath == ''`，不呼叫 `read_factory_settings`，改為新建場景並移除預設物件。
- 新資料夾在建立前不存在；實際路徑經 `realpath` 解析與預定路徑相同，路徑上沒有符號連結。
- 所有輸出都寫在 `Environment_Transition_Kit/` 之內；腳本在每次存檔或匯出前都會檢查目標路徑在本資料夾內。

## 受保護資產掃描（只比對檔名／資料夾名，不開檔）

搜尋 `/home`、`/root`、`/tmp`、`/opt`、`/mnt`、`/srv`，關鍵字：樹伴、古樹、山兔、主世界，以及 mainworld、overworld、tree_companion、ancient_tree、rabbit 等英文寫法。

- 結果：**本環境中找不到**樹伴古樹、山兔或主世界的任何檔案或資料夾。唯一命中是 `pyright` 型別檔 `rabbitmq.pyi`（訊息佇列套件，誤判，與本專案無關）。
- 專案內共有 220 個既有 `.blend`；本次一個都不開啟、不連結、不 Append。
- 掃描結果與雜湊記錄在 `PHASE0_Safety.json`；交付前以同一腳本 `--final` 做唯讀比對（`PHASE6_ProtectedAssetRecheck.json`）。

## 範圍

本次只做不規則道路收邊、河岸收邊、橋頭收邊 29 件獨立模組，不重建小鎮、不做橋樑本體、不改舊世界或任何動植物模型。測試用道路芯、佔位橋面、示意水面只放在 `COL_TEST_Only`，不匯出為正式資產。
