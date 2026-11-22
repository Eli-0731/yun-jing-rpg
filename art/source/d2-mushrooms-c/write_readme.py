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

 'DP02_01':('白色小蕈叢・苔上八朵','A cand-3（91）',
  '八朵高低不同的細長象牙白蕈和兩顆小圓鈕，從一團苔墊長出（最高的傘頂 16 cm）。傘微凸、傘緣往下垂，像 V6 右下石邊苔上那叢。'),
 'DP02_02':('白色小蕈叢・高細三朵','B cand-1（91）',
  '中間一朵高的（約 17 cm）和兩側兩朵矮的，傘和柄帶淡水青色，照 V6 朽木旁那三朵；設定圖裡它們微微發光，模型只照顏色、不做發光。'),
 'DP02_03':('白色小蕈叢・朽木段上一群','C cand-1（91）',
  '一段半埋的碎朽木（長 0.29 m），頂上一層不規則的苔，五朵小白蕈長在頂上、一朵從斷口邊長出。朽木段往地下 1.5 cm。'),

 'DP03_01':('層狀菌・薄層架','A cand-3（91）',
  '六片薄的層架菌高低錯落，長在一片樹皮板上。同心紋是褐、黃褐、灰褐，邊緣一圈淺奶油色，底下是淺色孔面。背面是平的，貼在樹幹或倒木上。'),
 'DP03_02':('層狀菌・厚蹄形三個','B cand-3（91）',
  '三個厚的蹄形多孔菌由小到大往下疊，每個底下留一點間隙。紋帶暗褐、鏽褐，最外緣淺赭色。背面是平的樹皮板。'),
 'DP03_03':('層狀菌・靈芝三朵','C cand-3（90）',
  '三朵腎形的靈芝，短柄從一塊圓的樹樁木頭側面彎出來，傘面暗紅褐帶漆光（粗糙度比其他件低），邊緣淺赭。紅色比三視圖壓暗、壓低彩度。背面是平的。'),

 'DP04_01':('苔上的小菇・九朵','A cand-3（90）',
  '九朵 2–5 cm 的小鈴形菇和兩顆小圓鈕，長在一塊低的苔墊上（0.12 m）。傘暗黃褐、傘緣淺，柄很細。點綴用。'),
 'DP04_02':('黏菌','B cand-1（90）',
  '一片苔和幾塊濕木屑上爬著芥末黃（壓低彩度）的黏菌網，從兩個中心往外分支；中間一叢十八個細柄暗褐小球的孢子囊，旁邊幾顆奶油赭色的小團。'),
 'DP04_03':('苔枝上一排小鈴菇','C cand-2（91）',
  '一段長苔的細枯枝（長 0.17 m、半埋 5 mm），頂上一排七朵 2–4 cm 的淡色小鈴菇。'),
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
head=(ROOT/'art/source/d2-mushrooms-c/readme_head.md').read_text(encoding='utf-8')
tail=(ROOT/'art/source/d2-mushrooms-c/readme_tail.md').read_text(encoding='utf-8')
(E/'README.md').write_text(head+'\n'.join(rows)+tail,encoding='utf-8');print('README written',len(rows),'items')
