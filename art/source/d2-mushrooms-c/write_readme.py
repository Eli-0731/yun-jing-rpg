"""Writes art/exports/d2-mushrooms-c/README.md from model_info.json (labeling-v1 §5 header, then per-item numbers), after
art/source/undergrowth-c/write_readme.py.   python art/source/d2-mushrooms-c/write_readme.py   (from the repo root)"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'art/exports/d2-mushrooms-c'
info=json.loads((E/'model_info.json').read_text(encoding='utf-8'))
DESC={
 'DP01_01':('褐色蕈叢・細長五朵','A cand-1（91）',
  '五朵高低不同的細長褐蕈從一團苔墊長出，往外分開（最高的傘頂 17 cm、傘寬 9 cm，最小的傘寬 4 cm）。像 V4、V5 根邊那種細長柄的褐蕈。'),
 'DP01_02':('褐色蕈叢・粗壯三朵','B cand-1（91）',
  '一朵大的成熟褐蕈（傘寬 11 cm、柄粗 2.5 cm、高 12 cm）和兩朵小的（傘寬 6 cm、4 cm）。像 V6 坑邊那叢。'),
 'DP01_03':('褐色蕈叢・沿根腳一列','C cand-1（90）',
  '十朵排成一條微彎的線（長 0.5 m），兩端是小圓鈕，往中間越來越大、傘張開。擺在任一段根的根腳，像 V2 根腳那排。根不在模型裡（根是 Josh 的 DR 系列），模型只有沿根腳的一條窄苔帶。'),
 'DP01_04':('褐色蕈叢・簇生一叢','D cand-1（91）',
  '十二朵從同一個基部長出，柄往外彎，有半開的幼菇和張開的傘，長在一塊半埋的朽木片上，木片頂上一小片苔。從十幾朵減成十二朵是為了 LOD0 ≤ 4,000 面。'),
}
rows=[]
for k in sorted(info):
    d=info[k];l=d['lods'];name,ref,desc=DESC[k]
    tex=', '.join(sorted({f'{w}×{h}' for w,h in l['LOD0']['textures_px'].values()}))
    rows.append(f"### {k} {name}（{d['name']}，{d['version']}）\n\n{desc}\n\n"
      f"| 項目 | 數字 |\n|---|---|\n| 三視圖 | `art/references/DP01/`，選用 {ref} |\n"
      f"| 尺寸（寬 × 深 × 高） | {d['dimensions_xyz_m'][0]} × {d['dimensions_xyz_m'][1]} × {d['dimensions_xyz_m'][2]} m（高度含地下的苔墊） |\n"
      f"| 三角面 LOD0 / LOD1 / LOD2 | {l['LOD0']['triangles']:,} / {l['LOD1']['triangles']:,} / {l['LOD2']['triangles']:,}（工作包每件 LOD0 ≤ 4,000） |\n"
      f"| 物件數（每個 LOD） | {l['LOD0']['objects']} |\n"
      f"| 材質數 | 1（`{d['material']}`，雙面） |\n| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，{tex} |\n"
      f"| minTier | {d['minTier']} |\n| 碰撞 | 沒有（人可以走過去） |\n"
      f"| 檔案 | `{d['files']['fbx']}`（LOD0–2）、`{d['files']['glb']}`（LOD0）、`{d['files']['blend']}` |\n")
head=(ROOT/'art/source/d2-mushrooms-c/readme_head.md').read_text(encoding='utf-8')
tail=(ROOT/'art/source/d2-mushrooms-c/readme_tail.md').read_text(encoding='utf-8')
(E/'README.md').write_text(head+'\n'.join(rows)+tail,encoding='utf-8');print('README written',len(rows),'items')
