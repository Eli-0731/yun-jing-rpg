"""Writes art/exports/d2-floor-c/README.md from model_info.json (labeling-v1 §5 header, then per-item numbers), after
art/source/undergrowth-c/write_readme.py.   python art/source/d2-floor-c/write_readme.py   (from the repo root)"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'art/exports/d2-floor-c'
info=json.loads((E/'model_info.json').read_text(encoding='utf-8'))
DESC={
 'DP17_01':('小石・圓小石', 'A cand-4（90）', '一顆 6 cm 的圓小石，半埋。'),
 'DP17_02':('小石・角石一小群', 'B cand-3（90）', '五顆 3–11 cm 的角石，中間一顆高而尖，半埋。'),
 'DP17_03':('小石・扁平石', 'C cand-2（90）', '一顆 15 cm 的扁石，頂上一塊薄苔。'),
 'DP17_04':('小石・圓苔石', 'D cand-1（90）', '一顆 19 cm 的圓石，頂上和一側有苔。'),
 'DP17_05':('小石・楔形角石', 'E cand-1（90）', '一顆 25 cm 高、往上收尖的角石，有裂面。'),
 'DP17_06':('小石・兩顆一對', 'F cand-1（90）', '一大一小兩顆石頭靠在一起，縫裡長苔。'),
 'DP17_07':('小石・苔帽圓石', 'G cand-2（90）', '一顆 30 cm 的圓石，頂上一塊苔帽。'),
 'DP17_08':('小石・大石', 'H cand-1（90）', '一顆 39 cm 的大石，一面平，頂上有苔。'),
 'DP18_01':('松果與落果・松果', 'A cand-3（90）', '三顆 6–9 cm 張開的松果躺在地上，鱗片一片片做出來。'),
 'DP18_02':('松果與落果・堅果', 'B cand-3（90）', '八顆小堅果和帶殼斗的種子，兩片乾葉。'),
 'DP18_03':('松果與落果・野果', 'C cand-1（90）', '五顆 2–3 cm 的暗紅褐野果，一顆裂開露出淺色果肉，兩片乾葉。'),
 'DP19_01':('落葉堆・小', 'A cand-2（90）', '0.39 m 的一小堆落葉，一百二十片葉子一片片疊起來。'),
 'DP19_02':('落葉堆・中', 'B cand-2（90）', '0.6 m 的落葉堆，上層乾紅褐、黃褐，下層暗濕褐。'),
 'DP19_03':('落葉堆・長條', 'C cand-2（90）', '0.9 m 長、沿邊緣堆起的一長條落葉。'),
}
rows=[]
for k in sorted(info):
    d=info[k];l=d['lods'];name,ref,desc=DESC[k]
    tex=', '.join(sorted({f'{w}×{h}' for w,h in l['LOD0']['textures_px'].values()}))
    rows.append(f"### {k} {name}（{d['name']}，{d['version']}）\n\n{desc}\n\n"
      f"| 項目 | 數字 |\n|---|---|\n| 三視圖 | `art/references/{k[:4]}/`，選用 {ref} |\n"
      f"| 尺寸（寬 × 深 × 高） | {d['dimensions_xyz_m'][0]} × {d['dimensions_xyz_m'][1]} × {d['dimensions_xyz_m'][2]} m（{'深是從貼樹的背面往前伸出的距離' if k.startswith('DP03') else '高度含地下的苔墊'}） |\n"
      f"| 三角面 LOD0 / LOD1 / LOD2 | {l['LOD0']['triangles']:,} / {l['LOD1']['triangles']:,} / {l['LOD2']['triangles']:,}（工作包每件 LOD0 ≤ 4,000） |\n"
      f"| 物件數（每個 LOD） | {l['LOD0']['objects']} |\n"
      f"| 材質數 | 1（`{d['material']}`，雙面） |\n| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，{tex} |\n"
      f"| minTier | {d['minTier']} |\n| 碰撞 | 沒有（人可以走過去） |\n"
      f"| 檔案 | `{d['files']['fbx']}`（LOD0–2）、`{d['files']['glb']}`（LOD0）、`{d['files']['blend']}` |\n")
head=(ROOT/'art/source/d2-floor-c/readme_head.md').read_text(encoding='utf-8')
tail=(ROOT/'art/source/d2-floor-c/readme_tail.md').read_text(encoding='utf-8')
(E/'README.md').write_text(head+'\n'.join(rows)+tail,encoding='utf-8');print('README written',len(rows),'items')
