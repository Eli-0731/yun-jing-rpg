# 青溪公共演武區 v1：模型原始檔與建置（2026-10-28 重做）

PR #32 合併的 Codex 版被使用者退回（「跟屎一樣」），本次依同一組 AI 三視圖重做六件模型，品質對齊 main 上 B 組煉製工坊（同一套烘焙／LOD／匯出規格）。

## 檔案

| 檔案 | 內容 |
|---|---|
| `Qingxi_Training_Yard_v1.blend` | 母檔：六件各有「程序分件（可編輯，隱藏）」與「烘焙後遊戲網格＋LOD」兩個 Collection；`YardPreview` 場景依 `placement.json` 擺好整區。 |
| `blend/<asset>_v1.blend` | 每件的單獨建置結果（母檔由這六個檔組合）。 |
| `build_yard.py` | 幾何、材質、烘焙、LOD、匯出、驗證、單件預覽。 |
| `yardlib.py` | 本組幾何工具（車削、掃掠管、螺旋繩圈、擠出輪廓、方料）。 |
| `kitlib.py` | 烘焙／匯出／渲染工具，改寫自 `art/source/qingxi-alchemy-b/qa_lib.py`（joshsu54＋Claude Code，main `ebe57d4`），只改輸出路徑；原檔未動。 |
| `review_yard.py` | 用母檔 `YardPreview` 渲染整區與 1.7 m 眼高畫面。 |
| `compose_sheets.py` | 「AI 三視圖 vs 模型正交圖」對照表（需 Pillow）。 |
| `placement.json` | 示範擺位（Blender 座標），展示頁使用同一組數字。 |
| `textures/P_*.png` | 自製圖樣（旗面、匾額、刻紋、玉紋），經部件座標取樣後烘進圖集。 |

## 指令（Blender 5.2.2，背景執行，勿在已開啟的場景內跑）

```powershell
$B = 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
& $B -b --python-exit-code 1 --python art/source/qingxi-training-yard-v1/build_yard.py            # 六件；可加資產 id、--no-render、--quick
& $B -b --python-exit-code 1 --python art/source/qingxi-training-yard-v1/build_yard.py -- --master
& $B -b art/source/qingxi-training-yard-v1/Qingxi_Training_Yard_v1.blend --python-exit-code 1 --python art/source/qingxi-training-yard-v1/review_yard.py
python art/source/qingxi-training-yard-v1/compose_sheets.py
```

## 規格

- 公尺；Blender Z-up、正面 −Y；GLB Y-up、正面 +Z。原點在底面中心。
- 輪廓件用真幾何（曲面屋頂與翹角、筒瓦、瓦當、斗拱、雀替、懸魚、柱礎、螺旋繩圈、皮革護墊、槽口、鉚釘）；木紋、裂紋、苔痕、瓦縫、刻紋與舊化烘進貼圖。
- 每件一個烘焙材質：`textures/T_<asset>_BaseColor／ORM（R=AO G=粗糙 B=金屬）／Normal（OpenGL）`。演武棚 2048，其餘 1024。
- GLB 只含 LOD0，貼圖轉 WebP（給 PWA；`EXT_texture_webp`）；FBX 含 LOD0–2（`_LOD1`、`_LOD2`）並引用 PNG，給 Unity LOD Group。
- 可動節點：身法木樁 `arm_left／arm_right／arm_low`（樞紐在樁軸）、氣勁木樁 `jade_disc`、`rope_band_1..3`、練功旗 `banner_cloth`（樞紐在橫桿）。樞紐座標寫在各件 `model_info.json`。
- 演武棚步道：前階 3.4 m，柱間淨寬約 4.8 m，梁下淨高約 2.1 m；地坪高 0.30 m，兩級 0.10 m 台階。

尺寸、三角面、碰撞建議與回匯結果見 `art/exports/qingxi-training-yard-v1/<asset>_model_info.json`，總結見 `art/previews/qingxi-training-yard-v1/VALIDATION.md`。

作者：Johnnnny0823（委託、方向）；Claude Code（Claude Opus 5.5）程序建模、烘焙、驗證。三視圖來源見 `../../references/qingxi-training-yard-v1/README.md`。沒有使用第三方模型。
