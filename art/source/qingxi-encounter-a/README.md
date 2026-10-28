# 青溪林地遭遇 A01–A12：模型原始檔與建置

工作包：[`docs/execution/2026-10-29/01-A-forest-encounter.md`](../../../docs/execution/2026-10-29/01-A-forest-encounter.md)。本目錄從 main `ebe57d4` 開始，不依賴尚未合併的 PR #38（演武區重做）；`geomlib.py` 與 `kitlib.py` 是從那裡複製來的同作者工具，所以兩個 PR 可以獨立合併。

## 檔案

| 檔案 | 內容 |
|---|---|
| `Qingxi_Encounter_A.blend` | 母檔：每件有「程序分件（可編輯，隱藏）」與「烘焙遊戲網格＋LOD」兩個 Collection |
| `blend/<ID>_<Name>_v1.blend` | 每件單獨的建置結果 |
| `build_encounter.py` | 幾何、材質、烘焙、LOD、匯出、驗證、預覽 |
| `geomlib.py` | 幾何工具（車削、掃掠管、擠出、方料），複製自演武區 `yardlib.py` |
| `kitlib.py` | 烘焙／匯出／渲染工具，改寫自 `art/source/qingxi-alchemy-b/qa_lib.py`（joshsu54＋Claude Code），只改輸出路徑 |
| `layout_scene.py` | 依展示頁同一組座標擺出場景，渲染總覽、平面、眼高、地形接縫 |
| `compose_sheets.py` | 「AI 三視圖 vs 模型正交正／側／背」對照表 |
| `encode_video.py` | 用 Blender 內建 FFmpeg 把實玩 WebM 轉成 H.264 MP4 |

```powershell
$B = 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
& $B -b --python-exit-code 1 --python art/source/qingxi-encounter-a/build_encounter.py            # 可加 ID、--no-render、--quick
& $B -b --python-exit-code 1 --python art/source/qingxi-encounter-a/build_encounter.py -- --master
& $B -b art/source/qingxi-encounter-a/Qingxi_Encounter_A.blend --python-exit-code 1 --python art/source/qingxi-encounter-a/layout_scene.py
python art/source/qingxi-encounter-a/compose_sheets.py
```

建置前會檢查 `art/references/qingxi-encounter-a/<ID>_three_view.png` 是否存在，沒有三視圖就拒絕建模。

## 規格

- 公尺；Blender Z-up、正面 −Y；GLB Y-up、正面 +Z；原點在底面中心。
- **地形塊（A01、A02）**：平邊的頂面高度（基準面）在原點上方 0.6 m；放進場景時把原點放在 −0.6，平邊就會和地面 0 對齊。四邊在邊緣 0.5 m 內沒有起伏，相鄰地塊可直接拼接（見 `art/previews/qingxi-encounter-a/layout/tile_seams.png`）。A01 低邊 0.6 m、高邊 1.2 m；A02 碗底比基準面低約 0.5 m，正面（−Y）有寬緩坡出口，兔洞在背面內坡、局部座標 (0, 1.75)。
- 低於地面的部分（樹根、根盤）一律壓回地面，視覺上是「入土」，不會穿出地面下。
- 每件一個烘焙材質（BaseColor／ORM／Normal）；地形 A02 用 2048，其餘 1024。草葉與蕨葉是實體細三角面（不用透明貼片），材質雙面。
- GLB 只含 LOD0、貼圖 WebP；FBX 含 LOD0–2 與 PNG。碰撞建議寫在各件 `art/exports/qingxi-encounter-a/<key>_model_info.json`。

- **A07** 兔徑泥印地塊：厚 0.15 m，放置時原點設在 −0.15；爪印是 `textures/P_PawPrints.png` 遮罩，烘成較深、較亮的濕泥凹痕。
- **A09** 避雨龕即展示頁的安全點，地坪中心為安全點；**A10** 平台 1.8 m，可站立；**A12** 有 `A12_VineDummy`（完整）與 `A12_VineDummy_worn`（破損外皮）兩個 GLB，原點相同，可直接替換。
- 面數上限：A08 竹柵 10k（細竹管與繩綁多）、A09 避雨龕 24k（乾砌石塊與瓦）、A12 9k，其餘依各件 `model_info.json`。

作者：Johnnnny0823（委託、方向）；Claude Code（Claude Opus 5.5）程序建模、烘焙、驗證。沒有使用第三方模型。
