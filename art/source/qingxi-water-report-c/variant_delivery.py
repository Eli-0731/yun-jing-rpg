"""Measured ID diagrams and final package documentation; no outside assets."""
import base64,html,json,struct,itertools
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'art/exports/qingxi-water-report-c';PRE=ROOT/'art/previews/qingxi-water-report-c';TOOL=ROOT/'tools/qingxi-water-report-c'
p=OUT/'variants/manifest.json';r=json.loads(p.read_text(encoding='utf-8'))
for a in r['variants']:a['collision']='prototype scene uses conservative whole-prop XZ AABBs; water and icons have no independent collider; not Unity collision'
p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
base=json.loads((OUT/'batch2-manifest.json').read_text(encoding='utf-8'))
names={'C01':'村民議事矮桌','C02':'可翻面水情告示','C04':'竹製取水扁擔','C07':'修渠手工具箱','C08':'共修紀錄石牌','C03_tall_01':'直身高桶','C03_low_02':'八角矮桶','C03_bail_03':'提梁鼓腹桶','C05_notch_01':'缺口木牌','C05_fork_02':'分叉柱腳木牌','C06_fork_01':'燕尾布旗','C06_slant_02':'斜切布旗'}
issues=[]
for key,layout in r['layouts'].items():
    rows=layout['instances']
    for a,b in itertools.combinations(rows,2):
        if {a['id'],b['id']}=={'C01','C07'}:continue
        overlap=[min(x[1],y[1])-max(x[0],y[0]) for x,y in zip(a['bounds_xyz'],b['bounds_xyz'])]
        if all(x>.001 for x in overlap):issues.append([key,a['id'],b['id'],overlap])
    encoded=base64.b64encode((PRE/f'variants/plan-{key}.png').read_bytes()).decode()
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1300" height="1140" viewBox="0 0 1300 1140"><rect width="1300" height="1140" fill="#eeecdf"/><g font-family="Microsoft JhengHei,sans-serif" fill="#29483e">',f'<text x="40" y="39" font-size="25">青溪議水村角 · 排列 {key.upper()} · 實際模型俯視組裝圖</text><text x="40" y="68" font-size="14">3 × 5 m / 1.75 m 角色 / 全部物件 ID / Eli-0731 · Codex</text>',f'<image x="40" y="90" width="700" height="980" href="data:image/png;base64,{encoded}"/>']
    svg.append('<rect x="481" y="142.5" width="171.5" height="875" fill="#a3c6a5" fill-opacity=".17" stroke="#416a48" stroke-dasharray="8 5"/><text x="490" y="1002" font-size="12">預留 0.98 m 通道</text>')
    for i,a in enumerate(rows):
        id=a['id'];x,y,z=a['position'];offset=-.40 if id=='C01' else .1 if id=='C07' else 0
        sx=390+x*175;sy=580-(y+offset)*175
        w=82 if len(id)>3 else 32
        svg.append(f'<rect x="{sx-w/2:.1f}" y="{sy-9:.1f}" width="{w}" height="18" rx="3" fill="#f6f1de" stroke="#5c7051"/><text x="{sx:.1f}" y="{sy+3:.1f}" text-anchor="middle" font-size="10">{id}</text>')
        ty=118+i*70;bb=a['bounds_xyz'];dims=[v[1]-v[0] for v in bb]
        svg.append(f'<text x="780" y="{ty}" font-size="17">{id} · {html.escape(names[id])}</text><text x="780" y="{ty+24}" font-size="13">配置位置 {x:.2f}, {y:.2f}, {z:.2f} m</text>')
    svg.append('<text x="40" y="1100" font-size="14">+Y 在上；前方 −Y。C07 位於 C01 桌面；C05 尖端入土 0.12 m。</text><text x="780" y="1010" font-size="13">圖中虛線為通道，與物件保持分離。</text><text x="780" y="1035" font-size="13">主路在樣片之外；不代表 Unity 碰撞驗收。</text></g></svg>')
    (PRE/f'variants/assembly-id-plan-{key}.svg').write_text(''.join(svg),encoding='utf-8')
assert not issues,issues
stateChecks=[]
for id in ['C06_fork_01','C06_slant_02']:
    for suffix in ['', '-complete']:
        b=(OUT/f'variants/{id}{suffix}.glb').read_bytes();n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);nodeNames=[x.get('name','') for x in g['nodes']]
        if suffix:assert any(x.startswith('CompleteClosedCircle') for x in nodeNames) and not any(x.startswith('WorkOpenCircle') for x in nodeNames)
        else:assert any(x.startswith('WorkOpenCircle') for x in nodeNames) and not any(x.startswith('CompleteClosedCircle') for x in nodeNames)
        stateChecks.append(id+suffix)
(PRE/'variants/assembly-check.json').write_text(json.dumps({'pass':True,'layouts':['a','b'],'overlappingInstanceAABBs':issues,'allowedOverlap':'C07 rests on C01','stateGLBsChecked':stateChecks,'note':'Conservative instance bounds; not exact mesh collision, Unity or physical-device acceptance.'},indent=2)+'\n',encoding='utf-8')

active=[a for a in base['assets'] if a['id'] in ['C01','C02','C04','C07','C08']]+r['variants']
rows='\n'.join(f"| {a['id']} | {names[a['id']]} | "+' × '.join(f'{v:.3f}' for v in a['dimensions_xyz'])+f" | {a['triangles']:,} | {a['materials']} |" for a in active)
total=sum(a['triangles'] for a in active)
text=f'''# 青溪水路回聲｜C 模組化補交

作者：Eli-0731／Codex。依 main `4476c3719c7348751ce68f699e389a1111fa7a96` 的更新工作包補交。八個功能家族維持不變；重複家族現在有 **水桶 3／3、木牌 2／2、布旗裁切 2／2** 個可辨認形體，其餘五家族各一個精修版，共 12 個使用中的形體。空／半滿／滿、施工中／完成都是狀態，沒有充作新形體。

玩家可讀上游範例，在村角選三種回報、改選或取消；回報不改寫上游結果，不發放物品、貢獻或共同世界進度。15 句回應與八個規則情境在 [response-data.json](response-data.json)。沒有缺線索必須先補齊的門檻，未知結果不推定為完成。

## 開啟

在本目錄先執行 `npm ci`，再從儲存庫根目錄執行 `node tools/qingxi-water-report-c/server.mjs`。開啟 http://127.0.0.1:4321 。伺服器只綁 loopback，僅提供本包工具和自己的預覽／匯出資產。

- `index.html`：回報玩法、兩種錯落排列、12 個形體的近景、改選／取消和本機 JSON 匯入匯出。這頁用實際模型渲染圖互動，也可直接開檔。
- [walk3d.html](walk3d.html)：實際 GLB 3D 走查，需本機伺服器。1.7 m 固定眼高，WASD／方向鍵移動、Q/E 轉向、拖曳環視；有觸控按鈕。可換 A/B 排列、南／北眼高、水情、ID 標籤。三個桶使用 Empty／HalfFull／Filled 形態鍵，旗面會換成實際完成狀態 GLB。

Three.js 固定 **0.186.1**，Playwright 固定 **1.56.1**。Three.js 是第三方程式庫，保留 npm 套件的 MIT 授權，不計入原創模型。先開回報頁完成首次連線快取，再進入 3D，即可離線重開；離線快取不代表正式離線服務端。

## 形體、狀態與接口

| 家族 | 已完成的形體 | 各形體狀態 | 共用接口 |
|---|---|---|---|
| C03 | 直身 16 片高桶／帶耳八角矮桶／鼓腹、雙腳、竹提梁桶 | 各自空、半滿、滿 | GroundOrigin；Lift_L/R = (±0.16, 0, 0.30) m |
| C05 | 缺口直木牌＋方柱／錯位雙木板＋Y 分叉柱腳 | 乾、部分回潤、回潤 | GroundSocket=(0,0,0)，40 mm 方舌入土 0.12 m；PanelMount=(0,0,0.46) |
| C06 | 深 V 燕尾／不對稱斜切＋削角底緣 | 開口圈＋兩條施工線／閉口圈＋水紋完成圖樣 | 中央旗桿、0.46 m 橫梁；ClothTie 左中右=(−0.16/0/+0.16,0,0.79) |

接口座標使用 Blender X/Y/Z 公尺；GLB 為 Y-up。每個空節點名稱為 `變體ID__接口名`，避免 Blender 自動序號造成名稱碰撞；全部已回匯核對位置。旗面的兩個完成 GLB 是狀態，不新增形體計數。低桶外寬含耳座，牌高含地下方舌；尺寸以實測為準。

| ID | 形體 | 寬 × 深 × 高（m） | 三角形上限 | 材質 |
|---|---|---|---:|---:|
{rows}

合計三角形上限 **{total:,}**，含旗面兩種圖樣的母稿節點；單一狀態只顯示一套圖樣。三個桶各有兩個形態鍵。沒有用旋轉、縮放、鏡射、改色或舊分揀桌冒充新形體。

## 參考、母稿與組裝

七個新形體皆先生成、保存並目視檢查正／側／背三視圖，再寫網格。參考在 [variants](../../art/references/qingxi-water-report-c/variants/)，完整提示詞與推定細節在 [variant-review.json](../../art/references/qingxi-water-report-c/variant-review.json)：包含 AI 尺寸箭頭、側邊旗桿與吊點不一致時的處理。生成工具為內建 imagegen，全部網格與 128×128 材質圖由本包製作。

新版母稿 [WaterReportC_variants.blend](../../art/source/qingxi-water-report-c/WaterReportC_variants.blend)，七個變體各自 Collection；五件單一精修家族沿用本包第二批母稿。重建：`blender -b --python-exit-code 1 --python art/source/qingxi-water-report-c/build_variants.py`，再 `python art/source/qingxi-water-report-c/variant_delivery.py`。Blender 固定 4.5.3 LTS。

獨立 GLB 在 [variants](../../art/exports/qingxi-water-report-c/variants/)；七個形體、兩個旗面完成狀態、A/B 兩個實際組裝 GLB，另沿用 C01/C02/C04/C07/C08。原第一／二批母稿及舊 C03/C05/C06 留作階段記錄，不列入新版最低變體數。

兩個 3×5 m 排列都將同族物件錯開位置，保留 X=0.52–1.50 m 的通道。每組都有實際俯視與南／北兩張 1.7 m 眼高圖：

- [排列 A 標 ID 俯視組裝圖](../../art/previews/qingxi-water-report-c/variants/assembly-id-plan-a.svg)／[南側](../../art/previews/qingxi-water-report-c/variants/eye-a-south-1p7m.png)／[北側](../../art/previews/qingxi-water-report-c/variants/eye-a-north-1p7m.png)。
- [排列 B 標 ID 俯視組裝圖](../../art/previews/qingxi-water-report-c/variants/assembly-id-plan-b.svg)／[南側](../../art/previews/qingxi-water-report-c/variants/eye-b-south-1p7m.png)／[北側](../../art/previews/qingxi-water-report-c/variants/eye-b-north-1p7m.png)。

主路在樣片之外。物件實例 AABB 沒有非預期相交；C07 放在 C01 桌面是刻意配置，木牌舌端刻意入土。走查採保守的整件水平包圍盒與 0.16 m 玩家半徑，不是逐三角形或 Unity 碰撞；不可據此宣稱主場景碰撞已完成。

## 驗證與未完成項

`npm test`：14 項狀態規則。`npm run test:browser`：原回報、鍵盤、改選取消、重複點選、壞 JSON、保存失效、離線與 844×390 觸控模擬，再檢查 A/B 換排列不改本機決定。`npm run test:walk3d`：兩組各載入 12 物件、三桶形態鍵、南北眼高、兩條通道行走、石牌擋路、ID 標示、實際模擬觸控長按與離線 3D 重載。測試用本機 Chrome，可設 CHROME_PATH；錄影元件用 Playwright 對應版本。

模型檢查包含閉合結構、UV、零面積面、回匯尺寸、所有接口位置、兩個水面形態鍵與旗面狀態圖樣。水面為刻意開放表面。報告：[manifest.json](../../art/exports/qingxi-water-report-c/variants/manifest.json)、[組裝／狀態檢查](../../art/previews/qingxi-water-report-c/variants/assembly-check.json)、[3D 實測](../../art/previews/qingxi-water-report-c/variants/walk3d-report.json)。截圖與 `walkthrough-3d.webm` 在同一預覽目錄。

**工作包要求的形體變體已全數補齊，沒有以狀態抵件數。** 未完成：低 LOD、引擎專用碰撞、Unity 整合／編譯、實體手機效能、獨立真人全程驗收、正式跨場景收據及多人。B outcomeId 仍以本機別名展示，不依賴未合併分支；正式資產由核心組服務端驗證。
'''
(TOOL/'README.md').write_text(text,encoding='utf-8')
print('WATER_REPORT_VARIANT_DELIVERY_PASS',len(active),total)
