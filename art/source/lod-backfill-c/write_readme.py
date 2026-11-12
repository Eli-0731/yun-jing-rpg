"""Writes art/exports/lod-backfill-c/README.md from model_info.json (from the repo root):
python art/source/lod-backfill-c/write_readme.py"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'art/exports/lod-backfill-c'
info=json.loads((E/'model_info.json').read_text(encoding='utf-8'))
NM={'Q01':'有頂告示板','Q02':'刻痕立板','Q03':'竹竿掛牌','Q04':'開格告示架','C01':'背籠','C02':'分揀桌','C03':'竹編箱','C04':'布包','C05':'木箱','C06':'座凳','C07':'油紙燈','C08':'木托盤與冊子'}   # short labels read off the models (the old manifests carry ids only)
rows=[]
for k in ['Q01','Q02','Q03','Q04','C01','C02','C03','C04','C05','C06','C07','C08']:
    d=info[k];l=d['lods'];t=[l[f'LOD{i}']['triangles'] for i in range(3)];dm=d['source_dimensions_xyz_m']
    tex=sorted({f'{w}×{h}' for w,h in l['LOD0']['textures_px'].values()})
    rows.append(f"| {k} | {NM[k]} | {dm[0]:.2f} × {dm[1]:.2f} × {dm[2]:.2f} | {t[0]:,}／{t[1]:,}／{t[2]:,} | {100*t[1]/t[0]:.0f}%／{100*t[2]/t[0]:.0f}% | {l['LOD0']['objects']}／{l['LOD1']['objects']}／{l['LOD2']['objects']} | {d['detail_parts']} | {l['LOD0']['materials']} | {', '.join(tex) or '無'} | {'是' if d['lod0_equals_source'] else '否'} |")
head="""| 項目 | 內容 |
|---|---|
| 誰做的 | C（Eli-0731） |
| 工作包 | docs/execution/2026-11-07/C-128h-creekside-and-village-life.md 第二部分 C（自己的舊件補 LOD） |
| ID | #34 `qingxi-village-signs-v1` Q01–Q04、#35 `qingxi-return-c` C01–C08（#60 `qingxi-day12-c` 原本就有 LOD，見下面） |
| 分支／PR | art/c-1112-gc01-06-ground-cover ／ 開 PR 後補（和 GC01–GC06 同一張，一次一張，等前一張結案） |
| 版本 | 全部 v001（新資料夾 `lod-backfill-c/`；來源檔一個都沒改，原本的 GLB 也還在原處） |
| 狀態 | Exported ／ Imported（Unity 6000.3.28f1 獨立匯入檢查）／ Visually Verified（前後對照圖）；In-game Verified：未驗 |
| 素材來源 | 改自 C 自己的舊件，只加 LOD：#34 與 #35 的 GLB。LOD0 就是原本的幾何，沒有重做 |

# C 舊件補 LOD1／LOD2

**LOD0 不動**：每件的 LOD0 和原本 GLB 的三角面數一模一樣（`model_info.json` 的 `lod0_equals_source`），只把零件合成一個物件。做法和 B 的 `art/exports/lod-backfill-b` 相同，每件輸出：

- `<ID>/<ID>_LOD_v001.fbx`：`<ID>_LOD0／LOD1／LOD2`（本體）和 `<ID>_Detail_Small_LOD0／1／2`（釘子、繩結、掛勾這類小零件，低畫質可以整個關掉；沒有小零件的件就沒有這個物件）。
- `<ID>/<ID>_LOD_v001.glb`：同樣的 LOD，和原件一樣的格式；`<ID>/Textures/`：原件的貼圖，照材質改成不重複的檔名（原本嵌在 GLB 裡沒有名字，直接嵌進 FBX 時會互相蓋掉：C04 的綠布一度變成麻繩色）。
- `<ID>/<ID>_LOD_v001.blend`。

**做法**：逐零件減面。先把 GLB 在 UV 接縫處分開的頂點焊起來（UV 仍然留在每個角上），用 15° 設硬邊，再溶掉平面上多餘的線、往 LOD1 50%／LOD2 30% 減。每一次減面都檢查：多出破洞邊、或任一方向縮小超過 2% 就退回，改用較溫和的比例（LOD1 試 50%、75%；LOD2 試 30%、40%、50%、75%），都不行就那個零件保持原樣。24 面以下的零件不減。LOD2 另外拿掉比整件對角線 5% 還短的零件。

**代價（照實寫）**：這兩組本來就是低面數（376–4,248 面），竹條、布包、薄板一減就破，所以 LOD2 只降到原本的 34%–65%，達不到工作包的 15%；C08 的 LOD2 和 LOD1 一樣。LOD1、LOD2 用硬邊重算法線，木箱頂面這類大平面的明暗和 LOD0 略有不同（見對照圖）。

| ID | 東西 | 尺寸（m） | LOD0／LOD1／LOD2 三角面 | LOD1／LOD2 比例 | 物件數 LOD0／1／2 | 小零件 | 材質 | 貼圖（px） | LOD0 = 原件 |
|---|---|---|---|---|---|---|---|---|---|
"""
tail="""
## #60 `qingxi-day12-c`（茶亭、村口石燈、守燈、晾藥架、雜物組）

這組在 #60 交件時就已經有 LOD：`art/exports/qingxi-day12-c/<ID>.fbx` 裡每組各有 `_LOD0`、`_LOD1`（約 50%）、`_LOD2`（約 15%），三角面寫在 `art/exports/qingxi-day12-c/model_info.json`（例如 G01 石燈 16,378／8,188／2,456）。這次沒有改動，也沒有重做。

## 驗證

- 前後對照（同光同角度）：`art/previews/lod-backfill-c/Q-lod-before-after.jpg`、`C-lod-before-after.jpg`（原本 → LOD1 → LOD2），線框 `Q-lod-wire.jpg`、`C-lod-wire.jpg`（LOD0、LOD2），單張在 `art/previews/lod-backfill-c/<ID>/`。
- Unity 6000.3.28f1 獨立匯入：`art/previews/lod-backfill-c/unity/report.txt`（每件一個 3 級 LODGroup、LOD0 面數等於原件、各級面數和 model_info 一致、每級材質相同、尺寸和原件差 2 cm 內），`<ID>-lod012.png` 是 LOD0／1／2 並排。
- 重建：`blender -b --factory-startup -P art/source/lod-backfill-c/build_lod_c.py -- <原件.glb> ...`；對照圖：`BL=<blender> sh art/source/lod-backfill-c/render_lod.sh` 後 `python art/source/lod-backfill-c/compose_lod_sheets.py`；Unity：`UNITY=<Unity.exe 6000.3.28f1> sh art/source/lod-backfill-c/unity/run_unity_check.sh`。

## 未驗

- 正式場景裡的切換距離、手機上的效果都未驗。
- 遊戲現在用的仍是原本的 GLB；要改用這裡的 FBX 由核心組決定。
"""
(E/'README.md').write_text(head+'\n'.join(rows)+'\n'+tail,encoding='utf-8');print('README written',len(rows))
