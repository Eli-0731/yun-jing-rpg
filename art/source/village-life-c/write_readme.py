"""Writes art/exports/village-life-c/README.md from model_info.json (labeling-v1 §5 header, then per-item numbers).
python art/source/village-life-c/write_readme.py   (from the repo root)"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'art/exports/village-life-c'
info=json.loads((E/'model_info.json').read_text(encoding='utf-8'))
DESC={'LV01':('竹編雞籠（倒扣的圓頂籠）','練「半球形的竹條排列、底部收邊」。22 條經向竹條從頂上麻繩結往下放射（越往頂越窄，避免在頂上互相疊住），7 圈緯向竹條一上一下穿過；底部一圈厚收邊，八處用麻繩綁住（繩子只繞外、上、內三面，兩端塞進收邊，不從地面下穿過）；頂上麻繩結加一個兩股絞成的提環；一條較新的補條綁在斷掉的竹條上。稻草卡在底部縫裡、兩根羽毛在收邊旁（Detail_）。','cand-3（92）'),
      'LV02':('竹掃帚與木畚箕','練「細枝束成一把的輪廓、木板拼接」。cand-3 把掃帚畫成直立，但提示詞和工作包高度 0.3 m 都是平放，所以掃帚平躺在畚箕旁：64 根細枝（部分分叉，兩端收細）從綁好的芯末端散成扁扇形，三道麻繩綁住；竹柄有竹節，柄頂纏繩垂一段繩尾、中段一圈布用兩條繩交叉綁住。畚箕三片底板、兩片三角側板、後板和 ∩ 形握把（交叉麻繩綁住），底板角落釘一塊補板。','cand-3（90）'),
      'LV03':('靠牆的竹梯','練「竹節、橫檔綁繩的重複節奏」。兩根粗竹竿下寬上窄、竹節間距不一；七根橫檔每個交點都用同一種綁法（竹竿上下各纏兩圈，再兩圈斜繞在正面交叉成 X）；第四根是換新的淺色竹橫檔；橫檔中段被踩得較暗、較滑，竿腳髒、帶一點苔。工作包尺寸深 0.1 m，所以模型是直立的，靠牆的角度在擺放時整件傾斜。','cand-4（93）'),
      'LV04':('竹編吊籃（掛著晾菜乾）','練「淺籃和吊繩、裡面一點乾菜」。淺圓籃（直徑 0.46 m）是一個薄殼，竹篾的一上一下編織畫在貼圖上；籃緣一圈粗竹篾每 30° 用細篾綁住，一邊略垂；三條麻繩從籃緣打結往上收到一個繩結，再一個掛圈（總高 0.77 m）；籃裡四片乾菜葉、五根紅辣椒；籃側一塊灰布補丁。原點在籃底：單獨放是籃子著地、繩子立起，擺放時由核心組掛上。','cand-1（92）'),
      'LV05':('醃菜甕三個（大中小，有蓋、壓石）','練「和 BM03 陶罐不同：寬口、厚蓋、蓋上壓一塊石頭」。三個甕各自分開放、不焊在一起，輪廓都不同：大甕肩寬、中甕直身、小甕矮胖；都是寬口、口沿一圈未上釉的陶，蓋上厚陶蓋、壓一顆平滑的河石；大甕蓋緣缺一角。深褐釉面上從肩部往下的流痕、甕腳的濕土和苔畫在貼圖上。和 BM03 的並排在 `art/previews/village-life-c/compare/LV05-vs-BM03-*`。','cand-2（92）'),
      'LV06':('劈柴木墩與柴刀','練「年輪切面、刀砍的痕、刀插在木墩上」。木墩高 0.4 m、底部根部外撇成五瓣，淺色風化木帶直向灰紋，九片樹皮從根部往上、邊緣參差、上緣往外翹；頂面年輪切面（放射裂紋），交叉的刀痕畫在貼圖上；一把寬刃柴刀在自己的平面裡斜插進頂面（刃口後端埋 1.2 cm、前端 6 cm），木柄纏布、垂兩條布尾；腳邊三塊劈柴，木屑（Detail_）。','cand-4（93）')}
rows=[]
for k in sorted(info):
    d=info[k];l=d['lods'];name,desc,ref=DESC[k]
    tex=', '.join(sorted({f'{w}×{h}' for w,h in l['LOD0']['textures_px'].values()}))
    det=', '.join(d['detailObjects']) if d['detailObjects'] else '無'
    rows.append(f"### {k} {name}（{d['name']}，{d['version']}）\n\n{desc}\n\n"
      f"| 項目 | 數字 |\n|---|---|\n| 三視圖 | `art/references/{k}/`，選用 {ref} |\n"
      f"| 尺寸（寬 × 深 × 高） | {d['dimensions_xyz_m'][0]} × {d['dimensions_xyz_m'][1]} × {d['dimensions_xyz_m'][2]} m（上限 {' × '.join(str(x) for x in d['size_limit_xyz_m'])} m） |\n"
      f"| 三角面 LOD0 / LOD1 / LOD2 | {l['LOD0']['triangles']:,} / {l['LOD1']['triangles']:,} / {l['LOD2']['triangles']:,}（不含 Detail_：{l['LOD0']['triangles_without_detail']:,} / {l['LOD1']['triangles_without_detail']:,} / {l['LOD2']['triangles_without_detail']:,}） |\n"
      f"| 物件數（每個 LOD） | {l['LOD0']['objects']}（本體 1 + {det}） |\n"
      f"| 材質數 | 1（`{d['material']}`，本體和 Detail_ 共用） |\n| 貼圖 | Albedo、Normal、ORM、MaskURP 各一張，{tex} |\n"
      f"| minTier | {d['minTier']} |\n| 檔案 | `{d['files']['fbx']}`（LOD0–2）、`{d['files']['glb']}`（LOD0）、`{d['files']['blend']}` |\n")
head="""| 項目 | 內容 |
|---|---|
| 誰做的 | C（Eli-0731） |
| 工作包 | docs/execution/2026-11-07/C-128h-creekside-and-village-life.md 第二部分 A（LV01–LV12，這張先交 LV01–LV06） |
| ID | LV01–LV06 |
| 分支／PR | art/c-1107-lv01-06-village-life ／ 本批送審 |
| 版本 | v001（檔名帶 `_v001`；之後改版另存 v002，不覆寫） |
| 狀態 | Exported ／ Imported（Unity 6000.3.28f1 獨立匯入檢查）／ Visually Verified（Blender 與 Unity 審圖）／ In-game Verified：未驗（沒放進正式場景） |
| 素材來源 | 原創；三視圖參考在 `art/references/LV01/`–`art/references/LV06/` |

# 青溪村裡生活小物 LV01–LV06

工作包第二部分 A 的前六件：讓 A1 青溪村各戶門口、院子、牆邊有一點生活的東西。靜態擺設，沒有玩法、碰撞或動畫；擺進世界由核心組做。

**共同做法**
- 先生成三視圖（每件 4 張）、自評選一張（分數和取捨在各自的 `prompt.txt`），再做灰模（`art/previews/village-life-c/<ID>/clay/`），最後上貼圖。一件只專心練工作包寫的那一兩個技巧。
- 原點在腳印中心、底部 z = 0，Blender −Y 是正面（FBX／Unity 是 −Z）。不附地面底板。
- 一件一個材質、一套 1024 貼圖；可有可無的小東西放 `Detail_*` 子物件（標準畫質關掉），本體的環境遮蔽烘焙時不含 Detail_。
- LOD1 約 50%、LOD2 約 15%，LOD0 不減面。`minTier` 都是 `high`（畫質分級第 4 節：增加豐富度的擺設，不擋路、不參與玩法），所以沒有碰撞。
- 建模流程和 creekside-life-c（WL、FI）相同，共用那裡的工具（`wl_kit.py`、零件函式、審圖相機 `render_wl.py`），這裡只放 LV 自己的物件和建模腳本。
- 重建：`blender -b --factory-startup -P art/source/village-life-c/build_lv.py -- LV01 [--clay]`；審圖與 QA：`BL=<blender> sh art/source/village-life-c/render_reviews.sh`；Unity：`UNITY=<Unity.exe 6000.3.28f1> sh art/source/village-life-c/unity/run_unity_check.sh`。

"""
tail="""
## 驗證

- QA（`tools/art/qa_lod0_basic.py` 嚴格與寬鬆、`tools/art/qa_contact_glb.py`）：六件嚴格、寬鬆都是 0 項，結果在 `art/previews/village-life-c/qa/`。
- FBX 原始資料與回匯覆核：`blender -b --factory-startup --python-exit-code 1 -P art/source/village-life-c/verify_delivery.py`。檢查每個 LOD 的原始面數、物件／材質數、貼圖解析度、UV、回匯尺寸與底部原點；記錄在 `art/previews/village-life-c/qa/fbx-roundtrip.json`。
- Unity 6000.3.28f1 既有獨立匯入報告：`art/previews/village-life-c/unity/report.txt`，84 項 PASS。本輪核對模型及報告一致，沒有重跑 Unity Editor；模型與 FBX 沒有修改。
- 同光同角度並排（含 1.75 m 人形尺，灰模和成品各一張）：`art/previews/village-life-c/compare/`。LV01／LV04 對 B 的竹篩 MK02、背簍 MK04；LV02／LV03 對 B 的柴堆 R03、C 的木樁 BM02_01；LV05 對 C 的陶罐 BM03_01–03；LV06 對 BM02_01、R03；`LV-set` 是六件放在一起。

**和既有模型的三個共同點**
1. 材料一看就認得、帶使用痕跡：竹篾、竹竿、麻繩、舊木和陶都用 creekside-life-c 同一套來源貼圖，和 MK02、MK04 的竹編，BM02、R03 的木頭同一種畫法。
2. 同一組底色：舊木在暖褐、竹在麥稈黃到灰綠、陶是深褐釉加素陶、石在暖灰；大塊柔和的深淺，只有少量筆觸。
3. 磨損有位置：接地的一側較暗、帶土和苔（雞籠收邊、竹梯腳、甕腳、木墩根部），常摸、常踩的地方較亮或較暗、較滑（掃帚握處、橫檔中段）。

## 已知問題與未驗

- 正式場景擺放、手機上的效果都未驗。
- Blender 4.5.3 回匯 FBX 後，LV01／LV02／LV03／LV04／LV06 的部分 LOD1／LOD2 面數較原始檔少；逐項差異列在 `qa/fbx-roundtrip.json`。`model_info.json` 的面數與 FBX 原始資料、既有 Unity 匯入報告一致，沒有以 Blender 回匯數字覆寫它們。
- LV02：三視圖四張都把掃帚畫成直立，照提示詞和工作包高度改成平躺；綁好的那段芯看起來偏像一截光滑木頭。
- LV03：工作包尺寸深 0.1 m，模型是直立的；靠牆的角度要在擺放時整件傾斜。
- LV04：原點在籃底，單獨擺放是籃子著地、繩子立起；要掛起來時以頂上的繩圈為掛點。
- LV05：口沿未上釉的那圈大多被厚蓋擋住，近看才看得到。
"""
(E/'README.md').write_text(head+'\n'.join(rows)+tail,encoding='utf-8');print('README written',len(rows),'items')
