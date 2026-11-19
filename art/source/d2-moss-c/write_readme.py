"""Writes art/exports/d2-moss-c/README.md from model_info.json (labeling-v1 §5 header, then per-item numbers), after
art/source/undergrowth-c/write_readme.py.   python art/source/d2-moss-c/write_readme.py   (from the repo root)"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'art/exports/d2-moss-c'
info=json.loads((E/'model_info.json').read_text(encoding='utf-8'))
DESC={
 'DP06_01':('苔團・小圓墊','A cand-3（90）',
  '一團低圓的苔墊（約 0.25 × 0.25 m、高約 0.10 m），表面一團團小苔球，邊緣散出細苔鬚。放地上、根旁、石頭腳下。'),
 'DP06_02':('苔團・多瓣中丘','B cand-1（91）',
  '三、四個大小不同的圓瓣併成一丘（約 0.42 × 0.41 m、高約 0.18 m），瓣間有凹縫。像 V6 石邊那團。'),
 'DP06_03':('苔團・大片低鋪','C cand-3（90）',
  '一大片低平的苔（約 0.80 × 0.65 m、只高約 0.12 m），有幾處緩丘，外形不規則帶瓣。鋪在林床、根和根之間。'),
 'DP06_04':('苔團・沿根腳長條','D cand-1（91）',
  '一串緩丘排成微彎的長條（約 0.60 × 0.22 m），兩端收尖，貼著任一段根的根腳放。根不在模型裡（根是 Josh 的 DR 系列）。'),
 'DP06_05':('苔團・石頂苔帽','E cand-1（91）',
  '一頂圓的苔帽（約 0.47 × 0.40 m、高約 0.17 m），邊緣往下垂，底下是空的，整合時扣在任一顆石頭頂上（像 V3、V6 石頭頂的苔）。z = 0 是下垂邊緣的最低處，沒有土裙。'),
 'DP06_06':('苔團・碎散小叢','F cand-4（90）',
  '一叢大的加六叢小的，各自分開，散在約 0.49 × 0.38 m 內。每叢都有自己的土裙。'),
}
rows=[]
for k in sorted(info):
    d=info[k];l=d['lods'];name,ref,desc=DESC[k]
    tex=', '.join(sorted({f'{w}×{h}' for w,h in l['LOD0']['textures_px'].values()}))
    rows.append(f"### {k} {name}（{d['name']}，{d['version']}）\n\n{desc}\n\n"
      f"| 項目 | 數字 |\n|---|---|\n| 三視圖 | `art/references/DP06/`，選用 {ref} |\n"
      f"| 尺寸（寬 × 深 × 高） | {d['dimensions_xyz_m'][0]} × {d['dimensions_xyz_m'][1]} × {d['dimensions_xyz_m'][2]} m（高度含地下的土裙） |\n"
      f"| 三角面 LOD0 / LOD1 / LOD2 | {l['LOD0']['triangles']:,} / {l['LOD1']['triangles']:,} / {l['LOD2']['triangles']:,}（工作包每件 LOD0 ≤ 4,000） |\n"
      f"| 物件數（每個 LOD） | {l['LOD0']['objects']} |\n"
      f"| 材質數 | 1（`{d['material']}`，雙面） |\n| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，{tex} |\n"
      f"| minTier | {d['minTier']} |\n| 碰撞 | 沒有（人可以走過去） |\n"
      f"| 檔案 | `{d['files']['fbx']}`（LOD0–2）、`{d['files']['glb']}`（LOD0）、`{d['files']['blend']}` |\n")
head=(ROOT/'art/source/d2-moss-c/readme_head.md').read_text(encoding='utf-8')
tail=(ROOT/'art/source/d2-moss-c/readme_tail.md').read_text(encoding='utf-8')
(E/'README.md').write_text(head+'\n'.join(rows)+tail,encoding='utf-8');print('README written',len(rows),'items')
