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
 'DP07_01':('苔被片・石頂苔帽', 'A cand-1（90）', '一層薄苔像帽子蓋在圓石頂（宿主半徑約 0.55 m），2–4 cm 厚，有低墊，邊緣細鬚往下垂。'),
 'DP07_02':('苔被片・平石苔片', 'B cand-1（90）', '平石面上一片 1–3 cm 的薄苔，幾個低墊、破邊。'),
 'DP07_03':('苔被片・根頂苔條', 'C cand-1（90）', '沿著根頂（半徑約 0.12 m）的一條 1 m 長苔，往兩側垂一點。'),
 'DP07_04':('苔被片・石側垂苔', 'D cand-2（91）', '貼在石頭直面上的一片薄苔，下緣是長短不一的苔舌往下垂。'),
 'DP07_05':('苔被片・小苔斑', 'E cand-1（90）', '微彎石面上的一小片不規則薄苔。'),
 'DP07_06':('苔被片・包角苔', 'F cand-2（91）', '從方石頂面包過邊角往正面垂的一片薄苔。'),
 'DP08_01':('小蕨・鐵線蕨型', 'A cand-3（90）', '十條細黑柄往外拱，分出側柄，每根側柄一扇小圓扇形小葉。'),
 'DP08_02':('小蕨・細裂蕨', 'B cand-1（91）', '六片往外拱的葉，左右錯開的齒緣羽片，中間一個捲曲的幼葉。'),
 'DP08_03':('小蕨・梯子蕨', 'C cand-1（90）', '十片直立窄葉成瓶狀一叢，兩排短圓小葉像梯子。'),
 'DP09_01':('林下地被・酢漿草', 'A cand-1（90）', '二十八根細紅褐柄，每根三片微摺的心形小葉，成一團低矮的葉堆。'),
 'DP09_02':('林下地被・幼苗', 'B cand-1（91）', '五株紅褐細莖的幼苗，兩到四片橢圓葉。'),
 'DP09_03':('林下地被・圓葉', 'C cand-1（90）', '一片匍匐的銅錢形圓葉，貼地。'),
 'DP09_04':('林下地被・混合', 'D cand-2（90）', '心形葉、兩株小蕨和幾片圓葉混在一起的低矮地被。'),
 'DP10_01':('垂藤・單條', 'A cand-1（90）', '一條 0.6 m 細藤，成對的橢圓小葉，幾條捲鬚。'),
 'DP10_02':('垂藤・兩條', 'B cand-1（91）', '兩條約 1.5 m 的細藤，心形和橢圓小葉。'),
 'DP10_03':('垂藤・長藤', 'C cand-1（90）', '一條 3 m 長藤，下端在地上捲一圈。'),
 'DP10_04':('垂藤・藤簾', 'D cand-1（91）', '一條沿邊緣橫走的藤垂下五條 0.65–1.2 m 細藤。'),
 'DP11_01':('莎草・小叢', 'A cand-1（90）', '八十片窄長深綠葉往外拱，幾片葉尖枯黃。'),
 'DP11_02':('莎草・大叢', 'B cand-1（90）', '九十二片長葉像噴泉往外垂到地，基部有枯葉。'),
 'DP11_03':('莎草・穗', 'C cand-2（91）', '直立細葉叢，五根細莖頂著褐色小穗。'),
 'DP12_01':('枯小灌叢・小', 'A cand-1（90）', '約 0.3 m 的細乾枝叢，掛幾片捲曲枯葉。'),
 'DP12_02':('枯小灌叢・中', 'B cand-1（91）', '約 0.5 m 的細乾枝叢、斷枝頭、十來片紅褐枯葉。'),
 'DP12_03':('枯小灌叢・大', 'C cand-1（90）', '約 0.7 m 的乾枝叢，微微往一邊斜，幾簇枯葉。'),
 'DP13_01':('地衣片・殼狀', 'A cand-1（90）', '一片 0.25 m 的灰綠殼狀地衣，2–4 mm 厚，貼在石面上。'),
 'DP13_02':('地衣片・葉狀', 'B cand-3（90）', '五朵灰綠葉狀地衣，瓣邊微捲。'),
 'DP13_03':('地衣片・杯狀', 'C cand-2（91）', '淺鼠尾草綠鱗片墊上長著二十幾個 1–2 cm 的小喇叭杯。'),
 'DP13_04':('地衣片・樹皮地衣條', 'D cand-1（90）', '沿樹幹（半徑約 0.3 m）往上的一條地衣，殼狀帶小葉瓣。'),
}
rows=[]
for k in sorted(info):
    d=info[k];l=d['lods'];name,ref,desc=DESC[k]
    tex=', '.join(sorted({f'{w}×{h}' for w,h in l['LOD0']['textures_px'].values()}))
    rows.append(f"### {k} {name}（{d['name']}，{d['version']}）\n\n{desc}\n\n"
      f"| 項目 | 數字 |\n|---|---|\n| 三視圖 | `art/references/{k[:4]}/`，選用 {ref} |\n"
      f"| 尺寸（寬 × 深 × 高） | {d['dimensions_xyz_m'][0]} × {d['dimensions_xyz_m'][1]} × {d['dimensions_xyz_m'][2]} m（{'抬高到最低點在 z = 0；宿主貼合點見 model_info' if k[:4] in ('DP07','DP10','DP13') else '高度含地下的土裙'}） |\n"
      f"| 三角面 LOD0 / LOD1 / LOD2 | {l['LOD0']['triangles']:,} / {l['LOD1']['triangles']:,} / {l['LOD2']['triangles']:,}（工作包每件 LOD0 ≤ 4,000） |\n"
      f"| 物件數（每個 LOD） | {l['LOD0']['objects']} |\n"
      f"| 材質數 | 1（`{d['material']}`，雙面） |\n| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，{tex} |\n"
      f"| minTier | {d['minTier']} |\n| 碰撞 | 沒有（人可以走過去） |\n"
      f"| 檔案 | `{d['files']['fbx']}`（LOD0–2）、`{d['files']['glb']}`（LOD0）、`{d['files']['blend']}` |\n")
head=(ROOT/'art/source/d2-moss-c/readme_head.md').read_text(encoding='utf-8')
tail=(ROOT/'art/source/d2-moss-c/readme_tail.md').read_text(encoding='utf-8')
(E/'README.md').write_text(head+'\n'.join(rows)+tail,encoding='utf-8');print('README written',len(rows),'items')
