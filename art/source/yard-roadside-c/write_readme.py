"""Writes art/exports/yard-roadside-c/README.md from model_info.json (labeling-v1 §5 header, then per-item numbers).
python art/source/yard-roadside-c/write_readme.py   (from the repo root)"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'art/exports/yard-roadside-c'
info=json.loads((E/'model_info.json').read_text(encoding='utf-8'))
DESC={'VG01':('菜畦一組（三條土壟：青菜、蘿蔔、蔥）','練「重複排列但每棵略不同；土壟的起伏」。三條壟是同一塊土：壟頂圓、壟間是踩實的淺溝，四周參差地斜到地面，輪廓是圓角、邊緣略有進出，不做圍欄和石牆。每種菜是一個做法（葉數、大小、仰角、朝向是參數），沿壟排成兩行、每棵的參數各自隨機，不是一棵棵手擺：青菜 12 棵（一圈寬葉加淺色菜梗）、蘿蔔 12 棵（露出土面的白肩加羽狀裂葉）、蔥 18 叢（直立的細管葉，少數葉尖折下）。溝和邊緣的土較乾較淺、壟頂較濕較深，畫在貼圖上。','cand-3（92）'),
      'VG02':('瓜架（竹架上爬著葫蘆藤，吊三顆葫蘆）','練「細竹竿的綁接；藤和葉用帶透明貼圖的面片」。四根立柱插在地上，頂上兩根長樑、兩根橫樑、五根細椽、三根細竹條，每根柱一根斜撐、兩端各兩根橫檔；竹竿都有凸起的竹節，每個交叉點用繩在兩條對角線上各繞一圈（沒有釘子）。藤是實體的細管，沿兩根柱盤上去、在頂上蜿蜒；三顆葫蘆（大、中、小）是實體，各用一段藤柄吊在椽下。葉（三種）和四朵黃花是面片，畫在圖集頂端 22% 的一條裡，alpha clip。柱腳的潮濕和青苔在貼圖上。','cand-4（93）'),
      'VG03':('晾衣竿（兩根叉竿、一根橫竿、晾著兩件布衣）','練「布掛著往下垂的形狀」。兩根略彎的原木柱插在地上，頂端分成兩叉，竹竿架在叉口、用繩綁住。上衣是衣身和兩隻袖子各一片搭在竿上（袖子穿在竿上張開的樣子），褲子是兩條褲管對折搭在竿上、前面垂下。布有 4.5 mm 厚，垂下的直褶越往下襬越深、下襬有起伏、兩側略低，都做在形狀上；布壓在竹竿頂上。下襬的毛邊和線頭是 alpha clip 面片（圖集頂端 10%）。領條、兩塊補丁和下襬的髒污畫在貼圖上。','cand-4（93）'),
      'VG04_01':('草垛（圓頂、完整）','練「大塊的軟輪廓；邊緣要毛，不要像一顆光滑的饅頭」。略歪的圓頂：一個實心的芯外面披六層稻草，每層略歪、高低不齊，下緣的參差做在形狀上，上緣塞進上一層底下；每層下緣掛一圈散開的草絲（alpha clip 面片，圖集頂端 12%）。頂上一頂小草帽綁在中心木桿上，木桿露出一截。下層較灰較濕、頂部較亮，畫在貼圖上。伸出來的零星草稈是 Detail_。','cand-3（91）'),
      'VG04_02':('草垛（一側被抽掉一角）','和 VG04_01 同樣的做法，另一個亂數；一側下半（高 1.2 m 以下、約 90° 寬）被抽走，凹口往裡收，露出五捆橫放的草把（每捆中間一道草繩），凹口前的地上一小堆散草和幾根草稈。四張三視圖都把「抽掉一角」畫成綁起來的門簾，這裡照工作包的文字做成凹口。','cand-3（91）'),
      'VG05':('兩輪手推板車（完好的空車）','練「輪子的圓和輻條；車架的榫接」。兩根縱樑從車尾一路伸到車頭，前段削細削圓成把手；四根橫樑穿過縱樑，榫頭從外側露出來，同時托住車板。車床是六片各自寬窄、長短、厚薄不同的木板。邊欄：每側三根立柱插進縱樑，內側一片側板、上面一根橫木穿過立柱，車尾一片擋板加一根橫木，後立柱用繩綁住；車頭那端敞開。輪子：車出來的輪轂加兩道鐵箍，十二根由粗到細的輻條，六段輪輞拼成圓，外包一圈鐵箍、外側十二顆鉚釘；輪軸穿過縱樑下的兩塊軸座，輪轂外各插一根鐵銷。車頭下一根支腳加兩根斜撐，讓車床放平。完好的空車，和翻倒的破車 A2_OverturnedCart 不同。輪胎和支腳底的泥、車板的曬白、把手的磨亮畫在貼圖上。','cand-3（93）'),
      'VG06':('扁擔與兩個籮筐（放下來的樣子）','練「竹編用貼圖；扁擔中間磨亮」。兩個籮筐放在地上，扁擔橫架在兩個筐口上，繩子鬆垂。竹編紋路在貼圖上，筐壁是一個有厚度的光滑碗形；建出來的有：筐口一圈竹箍和八處綁紮、每個筐底交叉的兩條竹篾（從筐底繞上筐壁到筐口）、每筐四條繩從筐口收到扁擔上、扁擔上的繩圈、兩端各一根擋繩的木栓。扁擔中間寬厚、兩端收窄微翹；中間被肩膀磨亮（較淺較光滑）和竹節畫在貼圖上。右邊的筐略小一點、轉了個方向。','cand-1（92）'),
      'VG07':('石磨（卵石基座上的手推磨）','練「兩個圓柱疊放；石頭表面的鑿痕；出料的槽口」。下磨盤固定在接料盤中間，上磨盤疊在上面：頂面中心一個進料孔，側面上三分之二有一道道鑿出來的直槽（做在形狀上）；側面的鑿點和頂面放射狀的磨紋畫在貼圖上。接料盤是一塊圓石，一圈環形的槽、外緣一圈矮壁，正面的壁上開了缺口接出料槽口——一條帶溝的石舌往外往下伸，下面立一塊石板撐著。上磨盤側面嵌一塊木座，推柄穿過木座，用繩綁住。基座是十三塊卵石圍著一個芯堆成兩圈，腳邊幾顆小石頭。槽裡殘留的粉、槽口下的濕痕、基座的青苔和泥畫在貼圖上。','cand-4（93）'),
      'VG08':('餵牲口的長石槽','練「挖空的厚度；內側的水漬和青苔」。整塊石頭挖空：槽壁厚 6–9 cm、各處不一樣（手鑿的），內側往下收窄到平的槽底；槽口的缺角做在形狀上，其中一個角缺得比較大。下面墊兩塊扁石。內側的舊水線（水線下深色帶綠、水線上有流痕）、槽底的淤泥、外側下半和槽口的青苔、淺色地衣、鏽色流痕都畫在貼圖上。照工作包只做石頭，沒有鐵件。','cand-3（93）')}
rows=[]
for k in sorted(info):
    d=info[k];l=d['lods'];name,desc,ref=DESC[k];rid=k.split('_')[0]
    tex=', '.join(sorted({f'{w}×{h}' for w,h in l['LOD0']['textures_px'].values()}))
    det=', '.join(d['detailObjects']) if d['detailObjects'] else '無'
    col=d['collision'];colt=(f"`{col['mesh']}`：一個盒子 {' × '.join(str(x) for x in col['primitives'][0]['size_xyz_m'])} m（只在 FBX 和 .blend 裡，不顯示）" if isinstance(col,dict) else '模型裡沒有')
    rows.append(f"### {k} {name}（{d['name']}，{d['version']}）\n\n{desc}\n\n"
      f"| 項目 | 數字 |\n|---|---|\n| 三視圖 | `art/references/{rid}/`，選用 {ref} |\n"
      f"| 尺寸（寬 × 深 × 高） | {d['dimensions_xyz_m'][0]} × {d['dimensions_xyz_m'][1]} × {d['dimensions_xyz_m'][2]} m（上限 {' × '.join(str(x) for x in d['size_limit_xyz_m'])} m） |\n"
      f"| 三角面 LOD0 / LOD1 / LOD2 | {l['LOD0']['triangles']:,} / {l['LOD1']['triangles']:,} / {l['LOD2']['triangles']:,}（不含 Detail_：{l['LOD0']['triangles_without_detail']:,} / {l['LOD1']['triangles_without_detail']:,} / {l['LOD2']['triangles_without_detail']:,}） |\n"
      f"| 物件數（每個 LOD） | {l['LOD0']['objects']}（本體 1 + {det}） |\n"
      f"| 材質數 | 1（`{d['material']}`，全部共用） |\n| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，{tex} |\n"
      f"| minTier | {d['minTier']} |\n| 碰撞 | {colt} |\n"
      f"| 檔案 | `{d['files']['fbx']}`（LOD0–2）、`{d['files']['glb']}`（LOD0）、`{d['files']['blend']}` |\n")
ids=sorted(info);rng=f"{ids[0].split('_')[0]}–{ids[-1].split('_')[0]}"
head=f"""| 項目 | 內容 |
|---|---|
| 誰做的 | C（Eli-0731） |
| 工作包 | docs/execution/2026-11-11/C-36h-yard-and-roadside-props.md |
| ID | {rng}（VG04 是兩種：VG04_01、VG04_02） |
| 分支／PR | 批 A（VG01–VG04）：art/c-1111-vg-yard-props；批 B（VG05–VG08）：art/c-1111-vg-roadside-props ／ 開 PR 後補（一次一張，等前一張結案） |
| 版本 | v001（檔名帶 `_v001`；之後改版另存 v002，不覆寫） |
| 狀態 | Exported ／ Imported（Unity 6000.3.28f1 獨立匯入檢查）／ Visually Verified（Blender 與 Unity 審圖）／ In-game Verified：未驗（沒放進正式場景） |
| 素材來源 | 原創；三視圖參考在 `art/references/VG01/`–`art/references/VG08/` |

# 院子和路邊的東西 {rng}

11/11 的 36 小時包：青溪村院子裡和路邊比較大件的東西，遠遠就看得到。靜態擺設，沒有玩法或動畫；擺進世界由核心組做，這裡不改主場景、不改區塊 JSON。

**共同做法**
- 先生成三視圖（每件 4 張）、自評選一張（分數和取捨在各自的 `prompt.txt`），再做灰模（`art/previews/yard-roadside-c/<ID>/clay/`），最後上貼圖。
- 原點在腳印中心、底部 z = 0，Blender −Y 是正面（FBX／Unity 是 −Z）。不附地面底板。
- 一件一個材質、一套 1024 貼圖；可有可無的小東西放 `Detail_*`（標準畫質關掉）。`minTier` 都是 `standard`（工作包第 3.5 點）。
- LOD1 約 50%、LOD2 約 15%，LOD0 不減面。
- **alpha clip（VG02 藤葉和花、VG03 下襬毛邊、VG04 草邊）**：面片的圖畫在圖集頂端的一條裡（Albedo 的 alpha），材質用 alpha clip 0.5、雙面；Unity 匯入 Albedo 時打開「Mip Maps Preserve Coverage」（檢查腳本有設並有檢查）。灰模圖上這些面片是沒裁的方片。
- **碰撞**：工作包要簡單碰撞的（VG01、VG05、VG07、VG08）在 FBX 裡附一個盒子 `<ID>_Collision`（不顯示）；其餘模型裡沒有碰撞。
- 建模流程和 village-life-c、creekside-life-c 相同，共用那裡的工具和來源貼圖；這裡放 VG 自己的物件（`vg_items.py`）和建模腳本（`build_vg.py`）。
- 重建：`blender -b --factory-startup -P art/source/yard-roadside-c/build_vg.py -- VG01 [--clay]`；審圖與 QA：`BL=<blender> sh art/source/yard-roadside-c/render_reviews.sh`；Unity：`UNITY=<Unity.exe 6000.3.28f1> sh art/source/yard-roadside-c/unity/run_unity_check.sh`。

"""
tail=(ROOT/'art/source/yard-roadside-c/readme_tail.md').read_text(encoding='utf-8')
(E/'README.md').write_text(head+'\n'.join(rows)+tail,encoding='utf-8');print('README written',len(rows),'items')
