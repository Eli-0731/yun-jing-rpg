"""Writes art/exports/undergrowth-c/README.md from model_info.json (labeling-v1 §5 header, then per-item numbers and the guide's
checklist), after art/source/yard-props-c/write_readme.py.   python art/source/undergrowth-c/write_readme.py   (from the repo root)"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'art/exports/undergrowth-c'
info=json.loads((E/'model_info.json').read_text(encoding='utf-8'))
DESC={
 'SH01':('林下灌木（闊葉）',
  '七根細幹從一點分開（幹腳站在 14 cm 的一圈上），每根往外彎的角度不同：正面是一把扇子，側面比較窄，整叢往右後方微斜。'
  '幹往地下延伸 0.18 m，可以放在不平的地上。每根幹三到六根次枝，繞著幹交錯長出（不鏡像），每根次枝三到六根細枝：幹、次枝、細枝三級粗細分明（幹腳約 1.2–1.6 cm、次枝約一半、細枝約 2.4 mm）。'
  '葉子是五頂點的立體葉（四點輪廓加抬高的中脈），一片片沿細枝和次枝的外段繞枝螺旋互生（137.5°），葉柄接在枝上，葉面朝上朝外，每個枝頂一片嫩葉；彼此很近又幾乎平行的兩片，其中一片繞中脈轉開，不會疊成一片。'
  '沒有葉片卡、葉團圖集，也不是在球裡撒葉。幹的下段光裸，有一根次枝斷掉只剩一截。'
  '葉色依高度和內外連續混色（上外亮暖、下內深冷，下層幾片偏黃），同時寫在 Albedo 和頂點色（A 是樹冠遮蔽）；第二組 UV「Wind」u 是風的權重（幹腳 0、葉 1）、v 是相位。'
  '幹腳的青苔和泥、較高處的淺色地衣畫在貼圖上；地上 34 片落葉是 Detail_Litter。沒有碰撞（人可以穿過去）。',
  'cand-2（92）')}
rows=[]
for k in sorted(info):
    d=info[k];l=d['lods'];name,desc,ref=DESC[k];rid=k.split('_')[0]
    tex=', '.join(sorted({f'{w}×{h}' for w,h in l['LOD0']['textures_px'].values()}))
    det=', '.join(d['detailObjects']) if d['detailObjects'] else '無'
    rows.append(f"### {k} {name}（{d['name']}，{d['version']}）\n\n{desc}\n\n"
      f"| 項目 | 數字 |\n|---|---|\n| 三視圖 | `art/references/{rid}/`，選用 {ref} |\n"
      f"| 尺寸（寬 × 深 × 高） | {d['dimensions_xyz_m'][0]} × {d['dimensions_xyz_m'][1]} × {d['dimensions_xyz_m'][2]} m，高度含地下 0.18 m（地上約 {d['dimensions_xyz_m'][2]-.17:.2f} m） |\n"
      f"| 三角面 LOD0 / LOD1 / LOD2 | {l['LOD0']['triangles']:,} / {l['LOD1']['triangles']:,} / {l['LOD2']['triangles']:,}（不含 Detail_：{l['LOD0']['triangles_without_detail']:,} / {l['LOD1']['triangles_without_detail']:,} / {l['LOD2']['triangles_without_detail']:,}） |\n"
      f"| LOD 做法 | LOD1：葉子留四分之一、每片放大 1.6 倍，木頭減到 15%；LOD2：葉子留十二分之一、放大 2.5 倍，木頭 6%（不是整體減面，葉子不會變成破片） |\n"
      f"| 物件數（每個 LOD） | {l['LOD0']['objects']}（本體 1 + {det}） |\n"
      f"| 材質數 | 1（`{d['material']}`，全部共用，雙面） |\n| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，{tex} |\n"
      f"| 頂點資料 | COLOR_0（葉色，A 遮蔽）、UV2 `Wind`（風的權重、相位），每個 LOD 都有 |\n"
      f"| minTier | {d['minTier']} |\n| 碰撞 | 模型裡沒有 |\n| 亂數種子 | 枝幹 `UG_SEED` 8101、葉子 `UG_LSEED` 8159（固定，重建一樣） |\n"
      f"| 檔案 | `{d['files']['fbx']}`（LOD0–2）、`{d['files']['glb']}`（LOD0）、`{d['files']['blend']}` |\n")
head="""| 項目 | 內容 |
|---|---|
| 誰做的 | C（Eli-0731） |
| 工作包 | docs/execution/2026-11-14/C-120h-yards-undergrowth-and-wayside.md，B 批；做法照 docs/execution/2026-11-14/樹木重做-v2-分工.md 和 tree-method/天空島世界樹建模歷程與精修方法.md |
| ID | SH01（樣品；B 批其餘 SH02、SP01、UG01–UG06 等樣品審過再做） |
| 分支／PR | art/c-1114-sh-ug-undergrowth ／ 開 PR 後補 |
| 版本 | v001（檔名帶 `_v001`；之後改版另存 v002，不覆寫） |
| 狀態 | Exported ／ Imported（Unity 6000.3.28f1 獨立匯入檢查）／ Visually Verified（Blender 與 Unity 審圖）／ In-game Verified：未驗（沒放進正式場景） |
| 素材來源 | 原創；三視圖參考在 `art/references/SH01/` |
| 實際工時 | 2026-11-18 02:45–04:00（台灣時間），約 1 小時 15 分：讀指南、三視圖、建模腳本（植物用的 LOD、頂點色、風權重）、建模、QA、審圖、Unity 檢查 |

# 林下植物（undergrowth-c）

11/14 的 120 小時包 B 批：D2 林下（設定圖 V2、V3、V6），也用在 D1、A1 院子。照《樹木重做 v2》的分工，SH01 先交一個樣品，等審查意見再做其他的。靜態擺設；擺進世界由核心組做，這裡不改主場景、不改區塊 JSON。

**共同做法**
- 先生成三視圖（每件 4 張）、自評選一張（分數和取捨在 `prompt.txt`），再做灰模（`art/previews/undergrowth-c/<ID>/clay/`），最後上貼圖。
- 照指南的順序：先定三面剪影和幹，再分次枝、細枝（三級粗細），最後才排葉子；葉子是五頂點的立體葉，一片片沿枝排，不用葉片卡、不用葉團圖集、不在球裡撒葉，不鏡像。
- 原點在幹基中心的地面（z = 0），Blender −Y 是正面（FBX／Unity 是 −Z）；幹往地下延伸 0.18 m。
- 一件一個材質、一套 1024 貼圖（Albedo／Normal／ORM／MaskURP），雙面；葉色同時在 Albedo 和頂點色。可有可無的小東西放 `Detail_*`（標準畫質關掉）。`minTier` 都是 `standard`。
- **面數**：工作包寫「件小，面數各 ≤ 4,000」，《樹木重做 v2》寫灌木 LOD0 ≤ 30,000、LOD1 ≤ 7,500、LOD2 ≤ 2,000。這裡取品質優先：LOD0 一片片的葉子約 16,600 面，LOD1 ≤ 4,000（符合工作包），LOD2 ≤ 2,000。如果 LOD0 也要 ≤ 4,000，請在審查時說，會改成更少更大的葉子。
- 建模流程和 yard-props-c、yard-roadside-c 相同（共用工具和來源貼圖），`build_ug.py` 只多三件事：原點留在幹基、葉子減量的 LOD、頂點色和風權重。
- 重建：`blender -b --factory-startup -P art/source/undergrowth-c/build_ug.py -- SH01 [--clay]`；審圖、QA 和植物出圖（剪影、樹冠下、20 m／60 m、正面和左右 35°）：`BL=<blender> sh art/source/undergrowth-c/render_reviews.sh`；Unity：`UNITY=<Unity.exe 6000.3.28f1> sh art/source/undergrowth-c/unity/run_unity_check.sh`。

"""
tail=(ROOT/'art/source/undergrowth-c/readme_tail.md').read_text(encoding='utf-8')
(E/'README.md').write_text(head+'\n'.join(rows)+tail,encoding='utf-8');print('README written',len(rows),'items')
