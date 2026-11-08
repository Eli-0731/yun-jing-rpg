"""tea-terraces-b v001 (work pack B-48h, first batch): TE01 terrace kit, TE02 tea bushes, TE03 stair / path / stepping stones.

Run one asset per process:
  blender --background --factory-startup --python art/source/tea-terraces-b/build_tea_terraces_b.py -- TE01_StraightA
  ... -- TE01_StraightA --preview <dir>     procedural look only, no bake or export
An asset whose validation.json exists is skipped unless --force is given.

ti_core / ti_mats / mk_mats / cr_mats / cr_parts / ti_pipeline are copied unchanged from art/source/creek-repair-b (PR #73 head).
Unlike that kit, the terrace pieces keep their designed origin (footprint centre on the 1 m grid, z = 0 at the lower terrace's soil)
instead of being re-centred on their bounding box, so a stone that bulges a few millimetres never moves a connector off the grid.
Writes:
  art/source/tea-terraces-b/blend/<ID>_v001.blend
  art/exports/tea-terraces-b/<ID>/<ID>_v001.fbx, Textures/, model_info.json, validation.json
  art/previews/tea-terraces-b/<ID>/turnaround/ (ten views + views.json), hero, LOD sheets
"""
import bpy, bmesh, sys, json, math, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np
from mathutils import Vector, Matrix
import ti_core, ti_mats, ti_pipeline as pl
import te_terrace as TT
import te_tea as TB
import te_paths as TP
import te_props as TPR
import te_tray as TTR
import te_pavilion as TPV
import te_wheel as TWH
from ti_core import S

KIT = 'tea-terraces-b'
ART = HERE.parents[1]
VER = 'v001'
LOD_TARGET = {1: .50, 2: .15}
LOD_DROPS = {1: (2, 99), 2: (1, 2, 99)}

TE01_NOTE = ('接口：兩端剖面相同（前緣 y 為足跡前緣、土面 z = 1.0、深 4 m），落在 1 m 格線；上一排放在 +4 m（直段為 +Y）、+1.0 m 高。'
             '牆面在足跡前緣後 7 cm，向後傾 12 cm／m；前緣土唇在 z = 0 接下一排的土面。')

ASSETS = {
    'TE01_StraightA': dict(zh='梯田直段 A（不規則野石、排水缺口）', kind='terrace', build=TT.te01_straight_a, limit=(8., 4., 1.6), ref='TE01/STRAIGHT-A', tex=2048,
        note=TE01_NOTE + ' 排水：壓頂石在 s = 2.9 m 留一道溢水口，下方一條濕石帶，牆腳是有過梁的排水口和吐水石。'),
    'TE01_StraightB': dict(zh='梯田直段 B（錯縫長石、修補角）', kind='terrace', build=TT.te01_straight_b, limit=(8., 4., 1.6), ref='TE01/STRAIGHT-B', tex=2048,
        note=TE01_NOTE + ' 右端 1.75 m 是後來重砌的：較小、較新、還沒長苔的石頭，接縫呈階梯。'),
    'TE01_InnerBend': dict(zh='梯田內彎（山凹）', kind='terrace', build=TT.te01_inner, limit=(8., 8., 1.6), ref='TE01/INNER-BEND', tex=2048,
        note=TE01_NOTE + ' 90° 內彎：牆面半徑 4 m、土面外緣半徑 8 m。左端與直段相同（朝 -Y），右端轉為朝 -X。足跡 8 × 8 m。'),
    'TE01_OuterBend': dict(zh='梯田外彎（山嘴）', kind='terrace', build=TT.te01_outer, limit=(8., 8., 1.6), ref='TE01/OUTER-BEND', tex=2048,
        note=TE01_NOTE + ' 90° 外彎：牆面半徑 8 m、土面內緣半徑 4 m。左端與直段相同（朝 -Y），右端轉為朝 +X。足跡 8 × 8 m。'),
    'TE01_End': dict(zh='梯田收尾', kind='terrace', build=TT.te01_end, limit=(8., 4., 1.6), ref='TE01/END', tex=2048,
        note=TE01_NOTE + ' 只有左端是接口；牆與土面從 s = 1.2 m 起順坡降到右端的地面（坡度約 9°，可走）。左側收尾用 X 鏡像（Unity scale.x = -1）。'),
    'TE01_Broken': dict(zh='梯田斷口', kind='terrace', build=TT.te01_broken, limit=(8., 4., 1.6), ref='TE01/BROKEN', tex=2048,
        note=TE01_NOTE + ' s = 4.7–7.1 m 牆頂塌落最多 0.5 m，土岸下陷後用木樁和編條擋住，掉下的石頭堆在土面上等著砌回；整段土面仍可走。'),
}

# v002 (2026-11-06): every TE01 tread gets the planting ridge under the bush line and the runoff ditch at the back (te_terrace.field_profile).
# The v001 exports and previews of the six original pieces are moved into <ID>/v001/; their .blend stays as <ID>_v001.blend.
V002_NOTE = (' v002：踏面加茶壟（d = 2.95 m 中心、底寬 1.2 m、平頂寬約 0.54 m、高 0.18 m，壟頂土色偏乾淺並有落葉，茶樹種在壟上）和牆根排水溝（d = 3.74 m、寬 0.4 m、深 0.12 m，溝底土色偏濕深），'
             '剖面只隨深度 d 變化，所有件的接口仍是同一個剖面。')
for _aid in ('TE01_StraightA', 'TE01_StraightB', 'TE01_InnerBend', 'TE01_OuterBend', 'TE01_End', 'TE01_Broken'):
    ASSETS[_aid]['ver'] = 'v002'; ASSETS[_aid]['note'] += V002_NOTE
GENTLE_NOTE = ('30° 緩彎（不在原工作包規格內，為了讓梯田能沿等高線彎曲而追加，待負責人確認）：沿牆 8 m、牆面半徑 15.28 m。'
               '左端接口與直段左端完全相同（x = -4、前緣 y = -2）；右端接口轉了 30°，不在 1 m 格線上，下一件依 Socket_Right 的位置與朝向擺放。')
ASSETS['TE01_GentleOuter'] = dict(zh='梯田緩外彎 30°（山嘴）', kind='terrace', build=TT.te01_gentle_outer, limit=(8., 8., 1.6), box=((-4.0, -2.0, 0.), (3.7, 3.6, 1.6)), ref='TE01/OUTER-BEND', tex=2048, ver='v001',
    note=TE01_NOTE + V002_NOTE + ' ' + GENTLE_NOTE + ' 向左（上坡側）轉。')
ASSETS['TE01_GentleInner'] = dict(zh='梯田緩內彎 30°（山凹）', kind='terrace', build=TT.te01_gentle_inner, limit=(8., 8., 1.6), box=((-4.0, -4.1, 0.), (5.7, 2.05, 1.6)), ref='TE01/INNER-BEND', tex=2048, ver='v001',
    note=TE01_NOTE + V002_NOTE + ' ' + GENTLE_NOTE + ' 向右（下坡側）轉。')
HEIGHT_NOTE = '牆高變化版（不在原工作包規格內，為了配合不均勻的坡度而追加，待負責人確認）：牆高 {h} m，上一排放在 +{h} m 高；同一排須全部使用同高度的件，本版只有直段 B 與收尾。'
for _base in ('TE01_StraightB', 'TE01_End'):
    for _h, _tag in ((.8, 'H08'), (1.2, 'H12')):
        _c = dict(ASSETS[_base]); _c.update(zh=_c['zh'] + f'（牆高 {_h} m）', rise=_h, ver='v001', limit=(8., 4., _h + .6),
                  note=_c['note'].replace('土面 z = 1.0', f'土面 z = {_h}').replace('+1.0 m 高', f'+{_h} m 高') + ' ' + HEIGHT_NOTE.format(h=_h))
        ASSETS[f'{_base}_{_tag}'] = _c

TE02_NOTE = ('修剪成形的茶樹：頂面是平的採摘面（一芽二葉的嫩梢），肩部圓、下緣收進，露出木質主幹。寬 1.2 m。'
             '葉片用透明裁切的葉片卡（TE02_LeafCards，四格共用貼圖），樹幹、根部土堆和小石烘焙到本件圖集。'
             '頂點色 Wind：R 風擺權重（根 0 → 外葉 1）、G 每張卡的相位、B 高度 0–1。')
for _aid, _zh, _h, _extra in (('TE02_Round', '茶樹（圓頂）', .9, '圓頂，最常用。'), ('TE02_Wide', '茶樹（寬扁）', .8, '較矮較扁，偏向一側，放在梯田外緣或坡上。'),
                              ('TE02_Tall', '茶樹（高瘦）', 1.1, '久未重剪，較高，枝幹較多外露。')):
    ASSETS[_aid] = dict(zh=_zh, kind='bush', palette=TB.palette, build=(lambda P, a=_aid: TB.tea_bush(P, dict(TB.TE02[a]))), limit=(1.2, 1.2, _h), ref='TE02/' + _aid.split('_')[1].upper(), tex=1024,
                        note=TE02_NOTE + _extra, origin='root centre on the ground, z = 0 at the soil', minTier='standard', clamp_max=.04)
# TE02 v002 (2026-11-06): denser foliage. The leaf atlas cells carry more, smaller leaves with almost no skipped ones
# (new atlas in TE02_Shared/v002/Textures; the v001 atlas in TE02_Shared/Textures is left as it was), and the crown has ~40% more cards
# set closer together over a fuller inner layer, so the gaps between leaves close up. Size, origin, collision and placement are unchanged.
TE02_V002_NOTE = ' v002：葉片更密集（每格貼圖的葉子更多更小、幾乎不留空位；樹冠葉片卡多約 40%、間距縮小、內層加厚），尺寸與擺放不變。'
# TE02 v003 (2026-11-06): lusher. The crown skirt comes down to 12-20 cm above the ground so the foliage hides most of the stems,
# ~35% more and slightly larger cards set closer, a lumpier outline. Same atlas as v002; size, origin, collision and placement unchanged.
TE02_V003_NOTE = ' v003：更茂密——樹冠下緣降到離地 12–20 cm，主幹大多被葉子蓋住；葉片卡再多約 35%、稍大、間距更小；輪廓更蓬鬆。尺寸與擺放不變（v002 的「露出主幹」描述已不適用）。'
for _aid in ('TE02_Round', 'TE02_Wide', 'TE02_Tall'):
    ASSETS[_aid]['ver'] = 'v003'; ASSETS[_aid]['note'] += TE02_V002_NOTE + TE02_V003_NOTE
# TE02 v004 (2026-11-06): leaf atlas v003 (TE02_Shared/v003/Textures) without the yellowed leaves; the crowns are rebuilt unchanged.
TE02_V004_NOTE = ' v004：葉片貼圖改用 TE02_Shared/v003，拿掉整片偏黃的老葉（重複數百張卡後在樹冠上變成滿佈的淺黃點）；形狀與 v003 相同。'
for _aid in ('TE02_Round', 'TE02_Wide', 'TE02_Tall'):
    ASSETS[_aid]['ver'] = 'v004'; ASSETS[_aid]['note'] += TE02_V004_NOTE
# TE02_Hedge family (2026-11-06, addition outside the work pack, pending owner confirmation): a continuous clipped hedge along the planting ridge.
HEDGE_NOTE = ('連續修剪的茶籬（追加件，待負責人確認）：同一批茶樹密植後剪成一整條，截面與單株茶樹相同（平的採摘面、圓肩、下緣離地約 12 cm）。'
              '深 1.1 m、高 0.85 m；葉片卡與單株共用 TE02_LeafCards 貼圖。開口端是平切面，最後 0.35 m 內輪廓起伏淡出成標準截面，'
              '任兩個開口端接在一起不會有落差；沿 X 軸串接，放在梯田茶壟（d = 2.95 m）上。頂點色 Wind 同單株茶樹。')
for _aid, _zh, _lim, _extra in (('TE02_Hedge', '茶籬（2 m 段）', (2.0, 1.1, .85), '長 2 m，兩端開口，直段與緩彎用。'),
                                ('TE02_HedgeShort', '茶籬（1 m 段）', (1.0, 1.1, .85), '長 1 m，兩端開口，補長度與 90° 轉角用。'),
                                ('TE02_HedgeEnd', '茶籬（收頭）', (1.0, 1.1, .85), '長 1 m，-X 端開口接茶籬，+X 端收成半個圓頂；左側收頭旋轉 180° 使用。')):
    ASSETS[_aid] = dict(zh=_zh, kind='hedge', palette=TB.palette, build=(lambda P, a=_aid: TB.tea_hedge(P, dict(TB.HEDGE[a]))), limit=_lim, ref='TE02/HEDGE (addition)', tex=1024,
                        note=HEDGE_NOTE + _extra, origin='row centre line on the ground, z = 0 at the soil; open ends at x = +-L/2', minTier='standard', clamp_max=.04, ver='v001',
                        box=((-_lim[0] / 2 - .15, -_lim[1] / 2 - .002, 0.), (_lim[0] / 2 + .15, _lim[1] / 2 + .002, _lim[2] + .002)))   # leaf cards overhang an open end by up to 0.15 m

TE03_NOTE = '1.2 m 寬，與 TE01 共用石材、土、草和苔的材質。'
ASSETS['TE03_Stair'] = dict(zh='梯田石階', kind='te03', palette=TP.palette, build=TP.te03_stair, limit=(1.2, 2.6, 1.05), box=((-.66, -2.47, 0.), (.66, .2, 1.05)), ref='TE03/STAIR', tex=2048, clamp_max=.05,
    origin='centre of the stair back edge on the TE01 footprint front line (y = 0), z = 0 at the lower tread',
    note=TE03_NOTE + ' 六級，每級高 1/6 m、踏面深 0.40 m，從下一排土面 z = 0 上到本排土面 z = 1.0。靠在任何 TE01 直段前緣：原點對準直段足跡前緣線，往 -Y 伸出 2.4 m 落在下一排踏面上。兩側是錯縫亂石，踏面為長條石板。')
ASSETS['TE03_Path'] = dict(zh='梯田土路', kind='te03', palette=TP.palette, build=TP.te03_path, limit=(4., 1.2, .4), ref='TE03/PATH', tex=2048, clamp_max=.12,
    origin='path centre, z = 0 at the tread soil', note=TE03_NOTE + ' 長 4 m（兩段接滿一個 8 m 直段），踩實的土路中間微凹，兩側半埋的邊石與草；兩端截面相同，可沿 1 m 格線串接。放在 TE01 踏面上，路面高出土面 1–3 cm。')
ASSETS['TE03_Stepping'] = dict(zh='梯田踏石', kind='te03', palette=TP.palette, build=TP.te03_stepping, limit=(2., 1.2, .4), ref='TE03/STEPPING', tex=2048, clamp_max=.09,
    origin='run centre, z = 0 at the tread soil', note=TE03_NOTE + ' 長 2 m，四塊平石半埋在土裡，步距約 0.6 m，石面高出土面 4.5–7 cm；周圍有翻動過的土圈、草和苔。')

# 2026-11-07 work pack part 1 (TE04, TE05, RI03): new pieces start at v001.
ASSETS['TE04_Basket'] = dict(zh='採茶竹簍', kind='prop', palette=TPR.palette, build=TPR.te04_basket, limit=(.52, .52, .42), ref='TE04/BASKET', tex=1024, ver='v001',
    minTier='standard', clamp_max=.02, origin='bottom centre, z = 0 under the foot hoop',
    note='低矮寬口的採茶簍（三視圖 TE04/BASKET candidate-01）：口徑約 0.5 m、高約 0.4 m，人字紋剖竹編、口緣內外兩道竹圈用麻繩穿壁綁 12 處、底圈綁 9 處；'
         '正面左側一塊較新較灰的補片，四角與四邊十字縫；簍內與口緣有幾片剛採的茶葉。和 harvest-market-b MK04 背簍不同：圓、矮、開口大、沒有立樁、木底架和背帶。'
         '綁繩、縫線、茶葉匯出為 Detail_Small，關掉不影響外形。')

ASSETS['TE04_Tray'] = dict(zh='晾茶竹匾', kind='prop', palette=TTR.palette, build=TTR.te04_tray, limit=(1.23, .77, .13), ref='TE04/TRAY', tex=1024, ver='v001',
    minTier='standard', clamp_max=.02, origin='bottom centre, z = 0 under the woven floor',
    note='淺長圓角竹匾（三視圖 TE04/TRAY candidate-04 外形、04-r1 立面）：1.2 × 0.75 × 0.12 m，一張平編剖竹席把邊緣彎起成矮牆，口緣內外兩條舊杉木條夾住，'
         '深色藤條綁 12 處（長邊各 3、短邊各 1、四角各 1），杉木條在每處綁點對接。地板靠右後角、正面左側牆各一塊較新較灰的補片，十字縫。'
         '左側約三分之二鋪一層正在萎凋的茶葉。和圓竹篩（harvest-market-b MK02）不同：長圓角、扁、木口緣。綁繩、縫線、茶葉匯出為 Detail_Small。')

ASSETS['TE05_Pavilion'] = dict(zh='東坡觀景亭', kind='pavilion', palette=TPV.palette, build=TPV.te05_pavilion, limit=(5., 5., 5.), ref='TE05/PAVILION', tex=2048, ver='v001',
    minTier='low', clamp_max=.03, origin='bottom centre, z = 0 under the stone plinth; steps on the front (-Y)',
    note='方形四柱觀景亭（三視圖 TE05/PAVILION candidate-04）：5 × 5 × 5 m。暖灰石台基高 0.5 m（亂石兩層＋鋪石），正面三級石階（每級 0.125 m）；'
         '四根圓柱立在石鼓柱礎上，四面各一道大額枋、一道小額枋、三支短柱與兩支雀替；平板枋、斗、圓檐檩承托屋頂，四根角梁在戧脊下。'
         '攢尖青灰瓦頂，筒瓦十層，四角起翹、戧脊尾端上捲，戧脊有青苔；右前角一片較新的補瓦。後方與右側 L 形長凳加欄杆，左側後半是一塊空白木板，前半是矮欄杆；'
         '左前柱旁一口加蓋陶水缸和竹舀。中央可走，柱間淨寬約 2.5 m、小額枋下淨高約 2.1 m。和 creek-repair-b WM09（圓形竹亭、茅草頂、圓石台）不同。')

ASSETS['RI03_GreatWheel'] = dict(zh='稻田灌溉大水車', kind='wheel', palette=TWH.palette, build=TWH.ri03_great_wheel, limit=(2.2, 10.6, 9.1), tex=2048, ver='v001',
    box=((-1.07, -5.12, -4.52), (1.07, 5.42, 4.52)), base_z=-4.5, ground_z=-4.0, ref='RI03/GREAT-WHEEL', slot='A6_GreatWheel',
    minTier='low', clamp_max=.03, origin='axle centre (the wheel pivot); the banks / footings are at z = -4.0, the wheel dips 0.5 m below them into its channel',
    note='稻田灌溉大水車（三視圖 RI03/GREAT-WHEEL candidate-04）：直徑 9.0 m、總寬 2.1 m（含軸頭與石座）。分三件：Wheel（軸、輪轂、兩側各 16 輻、雙層外輪框、中圈、'
         '32 片槳板、32 支竹筒，繞軸轉，樞軸在原點）、Seat（兩座收分亂石墩加木軸承座與基石）、Trough（輪側高處木槽、集水頭、四柱框架）；'
         '轉動用的繩綁另成 Detail_Wheel，靜態的繩綁、青苔、槽中水成 Detail_Small。竹筒綁在 -X 側輪框外、向外傾 9.5°–12°（每根略不同）、筒口朝前，過頂後把水倒進輪側的集水頭；'
         '三視圖把木槽畫在輪子正上方，那個位置會被竹筒打到，所以改在輪側。和 creek-repair-b WM02（4.6 m 磨坊下擊輪、鐵件）不同：兩倍大、無鐵件、用竹筒提水。')


def route_details():
    """Grass, ferns, moss, pebbles and chink stones export as their own Detail_Small object (quality-tiers-v1 section 4)."""
    for o in S['parts']:
        if o.get('group') == 'Main' and int(o.get('detail', 0)) >= 1:
            o['group'] = 'Detail_Small'


def part_twins(me):
    bm = bmesh.new(); bm.from_mesh(me); seen, twins = set(), []
    for f in bm.faces:
        k = frozenset(v.index for v in f.verts)
        (twins.append(f) if k in seen else seen.add(k))
    if twins: bmesh.ops.split(bm, geom=twins)
    bm.to_mesh(me); bm.free(); me.update()
    return len(twins)


def make_lods():
    """LOD1/LOD2 per export group: drop small parts while enough triangles remain, then collapse to the target."""
    tris = lambda me: sum(len(p.vertices) - 2 for p in me.polygons)
    for src in S['lod0'].values():
        bm = bmesh.new(); bm.from_mesh(src.data); big = [f for f in bm.faces if len(f.verts) > 4]
        if big: bmesh.ops.triangulate(bm, faces=big, quad_method='BEAUTY', ngon_method='BEAUTY')
        bm.to_mesh(src.data); bm.free(); S.setdefault('ngons_split', {})[src.name] = len(big)
        S.setdefault('twins_parted', {})[src.name] = part_twins(src.data)
    lods = {0: dict(S['lod0'])}; report = {}
    for lv in (1, 2):
        lods[lv] = {}
        for gname, src in S['lod0'].items():
            n0 = tris(src.data); want = n0 * LOD_TARGET[lv]
            for drop in LOD_DROPS[lv]:
                me = src.data.copy(); bm = bmesh.new(); bm.from_mesh(me)
                lay = bm.faces.layers.int.get('part_detail')
                if lay is not None and drop < 99:
                    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[lay] >= drop], context='FACES')
                bm.to_mesh(me); bm.free()
                if tris(me) >= want * .98 or drop == 99: break
                bpy.data.meshes.remove(me)
            o = src.copy(); o.data = me; S['lodcol'].objects.link(o)
            o.name = src.name.replace('_LOD0', f'_LOD{lv}'); me.name = o.name
            r = min(1., want / max(tris(me), 1))
            bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
            if r < .999:
                m = o.modifiers.new('LOD_decimate', 'DECIMATE'); m.use_collapse_triangulate = True; m.ratio = r
                if S.get('keep_border'):
                    m.use_symmetry = False
                for _ in range(6):
                    dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); tm_ = e.to_mesh(); n = tris(tm_); e.to_mesh_clear()
                    if abs(n - want) <= max(2, want * .01): break
                    m.ratio = min(1., m.ratio * want / max(n, 1))
                bpy.ops.object.modifier_apply(modifier=m.name)
                pl.orient_faces(o.data, flush=False); pl.spread_zero_uv([o])
                S.setdefault('twins_parted', {})[o.name] = part_twins(o.data)
            try: bpy.ops.mesh.customdata_custom_splitnormals_clear()
            except Exception: pass
            bpy.ops.object.shade_smooth_by_angle(angle=math.radians(38))
            lods[lv][gname] = o
            report.setdefault(gname, {'LOD0': n0})[f'LOD{lv}'] = tris(o.data)
    S['lods'] = lods
    return report


def leaf_lods(src, tex_dir):
    """Leaf cards are not decimated: each LOD keeps the cards whose lod_mask bit is set (fewer, larger cards further away); the core mass is in all three."""
    import shutil
    tex_dir.mkdir(parents=True, exist_ok=True)
    for f in TB.LEAF_DIR.glob('TE02_LeafCards_*.png'): shutil.copy2(f, tex_dir / f.name)
    rep = {}; orig = src.data
    for lv in (0, 1, 2):
        me = orig.copy(); bm = bmesh.new(); bm.from_mesh(me); lay = bm.faces.layers.int.get('lod_mask')
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if not (f[lay] >> lv) & 1], context='FACES')
        bm.to_mesh(me); bm.free()
        co = np.zeros(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
        if lv == 0: box0 = (co.min(0), co.max(0))
        else:   # fewer, larger cards reach further: scale this LOD about the root into the LOD0 leaf box
            k = np.ones(3, np.float32)
            for ax in range(3):
                if co[:, ax].max() > box0[1][ax]: k[ax] = min(k[ax], box0[1][ax] / co[:, ax].max())
                if ax < 2 and co[:, ax].min() < box0[0][ax]: k[ax] = min(k[ax], box0[0][ax] / co[:, ax].min())
            co *= k; me.vertices.foreach_set('co', co.ravel()); me.update(); rep[f'LOD{lv}_fit_scale'] = [round(float(v), 3) for v in k]
        o = src.copy() if lv else src; o.data = me
        if lv: S['lodcol'].objects.link(o)
        o.name = f"{S['asset']}_Leaves_LOD{lv}"; me.name = o.name
        S['lods'][lv]['Leaves'] = o
        rep[f'LOD{lv}'] = sum(len(p.vertices) - 2 for p in me.polygons)
    S['lod0']['Leaves'] = S['lods'][0]['Leaves']
    return rep


def apply_leaf_normals():
    """Point every card vertex's normal out of the crown (attribute leaf_n) so the bush shades as one soft mass instead of a heap of flat cards."""
    for lv in (0, 1, 2):
        me = S['lods'][lv]['Leaves'].data
        n = np.zeros(len(me.vertices) * 3, np.float32); me.attributes['leaf_n'].data.foreach_get('vector', n)
        for p in me.polygons: p.use_smooth = True
        me.normals_split_custom_set_from_vertices([tuple(v) for v in n.reshape(-1, 3)])
        me.attributes.remove(me.attributes['leaf_n'])
        if 'lod_mask' in me.attributes: me.attributes.remove(me.attributes['lod_mask'])


def clamp_to_limit(cfg):
    """Separating flush faces pushes a piece out by a millimetre or two; pull every vertex back inside the footprint and above z = 0."""
    lo_b, hi_b = cfg.get('box') or ((-cfg['limit'][0] / 2, -cfg['limit'][1] / 2, 0.), (cfg['limit'][0] / 2, cfg['limit'][1] / 2, 99.)); moved = 0
    objs = [o for g in S['lods'].values() for o in g.values()] + ([S['collision_obj']] if S.get('collision_obj') else [])
    for o in objs:
        me = o.data; co = np.zeros(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
        w = co + np.array(o.location, np.float32)
        c = w.copy(); c[:, 0] = np.clip(c[:, 0], lo_b[0], hi_b[0]); c[:, 1] = np.clip(c[:, 1], lo_b[1], hi_b[1]); c[:, 2] = np.maximum(c[:, 2], lo_b[2])
        moved = max(moved, float(np.abs(c - w).max()))
        me.vertices.foreach_set('co', (c - np.array(o.location, np.float32)).ravel()); me.update()
    S['clamped_m'] = round(moved, 5)
    assert moved < cfg.get('clamp_max', .02), ('clamp moved a vertex too far', moved)   # TE03: buried stone bottoms are flattened onto z = 0


def make_collision(aid):
    extra = S.get('collision_mesh')
    if not extra: return None
    me = bpy.data.meshes.new(aid + '_Collision'); me.from_pydata(extra[0], [], extra[1]); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(aid + '_Collision', me); S['lodcol'].objects.link(o); o.hide_render = True
    S['collision_obj'] = o
    return o


def export_fbx(path):
    a = S['asset']
    root = bpy.data.objects.new(a, None); S['lodcol'].objects.link(root); S['root'] = root
    for groups in S['lods'].values():
        for o in groups.values(): o.parent = root
    extra = [S['collision_obj']] if S.get('collision_obj') else []
    for o in extra: o.parent = root
    for e in S['sockets'].values():
        mw = e.matrix_world.copy()
        for c in list(e.users_collection): c.objects.unlink(e)
        S['lodcol'].objects.link(e); e.parent = root; e.matrix_world = mw
    bpy.ops.object.select_all(action='DESELECT')
    root.select_set(True)
    for groups in S['lods'].values():
        for o in groups.values(): o.select_set(True)
    for o in extra: o.hide_render = False; o.select_set(True)
    for e in S['sockets'].values(): e.select_set(True)
    bpy.context.view_layer.objects.active = root
    bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True, object_types={'MESH', 'EMPTY'},
                             apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', bake_space_transform=True,
                             axis_forward='-Z', axis_up='Y', mesh_smooth_type='FACE', use_mesh_modifiers=True,
                             add_leaf_bones=False, bake_anim=False, path_mode='STRIP', embed_textures=False, colors_type='LINEAR')
    for o in extra: o.hide_render = True


def export_glb(path):
    """Same LOD0..2 and collision as the FBX, for web previews; textures packed."""
    bpy.ops.object.select_all(action='DESELECT')
    S['root'].select_set(True)
    for o in S['root'].children_recursive: o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True, export_yup=True, export_apply=True, export_image_format='JPEG', export_jpeg_quality=88)


def build(aid):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene; scene.unit_settings.system = 'METRIC'; scene.unit_settings.scale_length = 1
    bpy.context.preferences.filepaths.save_version = 0
    ti_mats.MAT_INFO.clear(); ti_core.reset_state(aid)
    cfg = ASSETS[aid]; TT.RISE = cfg.get('rise', 1.0)
    P = TT.palette() if cfg['kind'] == 'terrace' else cfg['palette'](); cfg['build'](P)
    bpy.context.view_layer.update()
    return cfg


def preview(aid, out_dir, samples=20):
    cfg = build(aid)
    ti_core.write_grain_attributes()
    S['cut'].hide_render = True
    lo, hi = pl.eval_bounds(S['parts']); print('PREVIEW_BOUNDS', aid, [round(v, 3) for v in lo], [round(v, 3) for v in hi], flush=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    tris = 0; dg = bpy.context.evaluated_depsgraph_get()
    for o in S['parts']:
        e = o.evaluated_get(dg); m = e.to_mesh(); tris += sum(len(p.vertices) - 2 for p in m.polygons); e.to_mesh_clear()
    print('PREVIEW_TRIS', aid, tris, len(S['parts']), flush=True)
    views = (('front', (0, -1, .12)), ('three_quarter', (1, -1.3, .55)), ('side', (1, 0, .15)), ('top', (.05, -.25, 1)), ('close', None))
    for name, d in views:
        if d is None:
            close_shot(S['parts'], out_dir / f'{aid}_close.png', samples=samples)
            continue
        pl.persp_shot(S['parts'], out_dir / f'{aid}_{name}.png', direction=d, samples=samples, lens=50)
    bpy.ops.wm.save_as_mainfile(filepath=str(out_dir / f'{aid}_preview.blend'))


def archive_previous(aid, ver):
    """Before a piece's first build of version ver, move the previous version's exports and previews into <ID>/<prev>/ so nothing is overwritten.
    Folders of older versions (v001/, v002/ ...) stay where they are."""
    import shutil, re
    prev = f'v{int(ver[1:]) - 1:03d}'
    exp = ART / 'exports' / KIT / aid
    if not (exp / f'{aid}_{prev}.fbx').exists(): return
    for root in (exp, ART / 'previews' / KIT / aid):
        if not root.exists(): continue
        items = [q for q in root.iterdir() if not re.fullmatch(r'v\d{3}', q.name)]
        (root / prev).mkdir(exist_ok=True)
        for q in items: shutil.move(str(q), str(root / prev / q.name))
        print('ARCHIVED_' + prev.upper(), root, len(items), flush=True)


def run(aid, force=False):
    global VER
    cfg = ASSETS[aid]; VER = cfg.get('ver', 'v001')
    exp = ART / 'exports' / KIT / aid; prev = ART / 'previews' / KIT / aid; blend = ART / 'source' / KIT / 'blend'
    if VER != 'v001': archive_previous(aid, VER)
    if (exp / 'validation.json').exists() and not force:
        print('ALREADY_COMPLETE', aid, flush=True); return
    t0 = time.time()
    build(aid)
    ti_core.write_grain_attributes(); route_details()
    pl.join_groups()
    leaves = S['lod0'].pop('Leaves', None)
    pl.uv_atlas(cfg.get('uv_weight'), cfg['tex']); pl.spread_zero_uv()
    pl.bake(exp / 'Textures', cfg['tex'])
    lod_report = make_lods()
    if leaves is not None: lod_report['Leaves'] = leaf_lods(leaves, exp / 'Textures')
    pl.export_materials()
    if leaves is not None: apply_leaf_normals()
    make_collision(aid); clamp_to_limit(cfg)
    S['col'].hide_render = True; S['col'].hide_viewport = True
    lod0 = list(S['lods'][0].values())
    lo, hi = pl.eval_bounds(lod0); dims = hi - lo
    checks = []
    def check(name, ok, detail): checks.append({'check': name, 'pass': bool(ok), 'detail': detail})
    if cfg['kind'] in ('bush', 'hedge'): lim = cfg['limit']; cfg = dict(cfg, limit=(lim[0] + .002, lim[1] + .002, lim[2] + .002))
    pieces = {}
    for gname, o in S['lods'][0].items():
        a, b = pl.eval_bounds([o]); pieces[gname] = {'dims_m': [round(v, 4) for v in b - a], 'min': [round(v, 4) for v in a], 'max': [round(v, 4) for v in b]}
    lim = cfg['limit']
    if cfg.get('box'):
        (bx0, by0, _), (bx1, by1, bz1) = cfg['box']
        check('footprint_within_limit', lo.x >= bx0 - 1e-3 and hi.x <= bx1 + 1e-3 and lo.y >= by0 - 1e-3 and hi.y <= by1 + 1e-3 and hi.z <= bz1 + 1e-3,
              {'min': [round(v, 4) for v in lo], 'max': [round(v, 4) for v in hi], 'box_m': cfg['box']})
    else: check('footprint_within_limit', lo.x >= -lim[0] / 2 - 1e-3 and hi.x <= lim[0] / 2 + 1e-3 and lo.y >= -lim[1] / 2 - 1e-3 and hi.y <= lim[1] / 2 + 1e-3 and dims.z <= lim[2] + 1e-3,
          {'min': [round(v, 4) for v in lo], 'max': [round(v, 4) for v in hi], 'limit_m': lim, 'note': 'footprint centred on the origin; height includes grass on the tread'})
    bz = cfg.get('base_z', 0.)   # RI03: origin at the axle, the lowest point is the bottom of the wheel
    check('base_at_z0' if not bz else 'lowest_point_at_design_z', abs(lo.z - bz) < (1e-3 if not bz else .01), {'min_z': round(lo.z, 5), 'design_min_z': bz, 'largest_clamp_m': S.get('clamped_m')})
    spec = spec_checks(aid, check)
    tot = {k: sum(g[k] for g in lod_report.values()) for k in ('LOD0', 'LOD1', 'LOD2')}  # (fit-scale keys are ignored)
    r1, r2 = tot['LOD1'] / tot['LOD0'], tot['LOD2'] / tot['LOD0']
    check('lod_ratios_50_15', .45 <= r1 <= .55 and .12 <= r2 <= .18, {'triangles': tot, 'LOD1': round(r1, 3), 'LOD2': round(r2, 3), 'per_group': lod_report})
    exp.mkdir(parents=True, exist_ok=True)
    fbx = exp / f'{aid}_{VER}.fbx'
    export_fbx(fbx)
    rt = pl.fbx_roundtrip(fbx)
    check('fbx_reimport_dimensions', all(abs(a - b) < .02 for a, b in zip(rt['lod0_dimensions_m'], dims)),
          {'fbx_lod0_dims_m': rt['lod0_dimensions_m'], 'blend_dims_m': [round(v, 4) for v in dims], 'tolerance_m': .02, 'max_error_m': round(max(abs(a - b) for a, b in zip(rt['lod0_dimensions_m'], dims)), 5)})
    names = rt['objects']
    check('fbx_has_lod0_1_2', all(any(n.split('.')[0].endswith(f'_LOD{lv}') for n in names) for lv in (0, 1, 2)), names)
    check('fbx_sockets', sorted(k.split('.')[0] for k in rt['sockets']) == sorted(S['sockets']), rt['sockets'])
    check('fbx_collision', cfg.get('no_collision') or (aid + '_Collision') in [n.split('.')[0] for n in names], cfg.get('no_collision') or 'collision mesh present')
    glb = exp / f'{aid}_{VER}.glb'; export_glb(glb)
    check('glb_written', glb.exists() and glb.stat().st_size > 1000, {'bytes': glb.stat().st_size})
    pl.ten_views(lod0, prev / 'turnaround', f'art/source/{KIT}/blend/{aid}_{VER}.blend')
    check('ten_views_rendered', len(list((prev / 'turnaround').glob('*.png'))) == 10, 'orthographic, framing asserted per view')
    shots = []
    for lv in (0, 1, 2):
        p = prev / f'_lod{lv}.png'; pl.persp_shot(list(S['lods'][lv].values()), p, samples=32); shots.append(p)
    _strip(shots, prev / f'{aid}_LOD_comparison.png'); [p.unlink() for p in shots]
    shots = []
    for lv in (0, 1):
        p = prev / f'_nd{lv}.png'; pl.persp_shot([o for g, o in S['lods'][lv].items() if not g.startswith('Detail_')], p, samples=48); shots.append(p)
    _strip(shots, prev / f'{aid}_LOD0_LOD1_no_detail.png'); [p.unlink() for p in shots]
    pl.persp_shot(lod0, prev / f'{aid}_hero.png', samples=96)
    wire(lod0, prev / f'{aid}_wireframe.png')
    for o in lod0: o.hide_render = False
    blend.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend / f'{aid}_{VER}.blend'))
    mats = sorted({m.name for g in S['lods'].values() for o in g.values() for m in o.data.materials})
    def png_px(p):   # width x height from the PNG header (IHDR)
        b = p.read_bytes()[16:24]; return [int.from_bytes(b[:4], 'big'), int.from_bytes(b[4:], 'big')]
    budget = {f'LOD{lv}': {'triangles': tot[f'LOD{lv}'], 'objects': len(S['lods'][lv]),
                           'objects_without_detail': len([g for g in S['lods'][lv] if not g.startswith('Detail_')]),
                           'materials': len({m.name for o in S['lods'][lv].values() for m in o.data.materials})} for lv in (0, 1, 2)}
    tex_px = {p.name: png_px(p) for p in sorted((exp / 'Textures').glob('*.png'))}
    info = {
        'asset': aid, 'version': VER, 'minTier': cfg.get('minTier', 'standard'), 'detailObjects': sorted(f'{aid}_{g}' for g in S['lods'][0] if g.startswith('Detail_')),
        'name_zh': cfg['zh'], 'slot': cfg.get('slot', 'A4_TeaTerraces'), 'note': cfg['note'],
        'budget_per_lod': budget, 'texture_resolution_px': tex_px,
        'units': 'meters', 'front': '-Y (Blender)', 'up': '+Z (Blender); FBX exported Y-up, -Z forward, transforms baked',
        'origin': cfg.get('origin', 'footprint centre on the 1 m grid, z = 0 at the lower terrace soil'), 'dimensions_m': [round(v, 4) for v in dims], 'bounds_min_m': [round(v, 4) for v in lo], 'bounds_max_m': [round(v, 4) for v in hi],
        'size_limit_m': cfg['limit'], 'pieces': pieces,
        'lods': lod_report, 'lod_totals': tot, 'lod_rule': 'LOD1 about 50%, LOD2 about 15% of LOD0 (detail parts dropped first, then collapse decimate)',
        'materials': mats, 'textures': sorted(p.name for p in (exp / 'Textures').glob('*.png')), 'texture_size_px': cfg['tex'],
        'unity': {'pipeline': 'URP Lit', 'axes': 'imported with bakeAxisConversion: Unity local = (Blender x, z, y); the model front faces Unity -Z', 'BaseColor': f'{aid}_BaseColor.png', 'Normal': f'{aid}_Normal.png (OpenGL +Y)',
                  'MetallicSmoothness': f'{aid}_MetallicSmoothness.png (R metallic, A smoothness)', 'lod_group': 'objects end in _LOD0/_LOD1/_LOD2 under one root',
                  'collision': f'{aid}_Collision: MeshCollider (convex off), renderer hidden'},
        'collision': bool(S.get('collision_obj')),
        **({'ground_z_m': cfg['ground_z']} if 'ground_z' in cfg else {}),
        **({'parts': S['part_notes']} if S.get('part_notes') else {}),
        'sockets_blender_xyz': {k: [round(v, 4) for v in e.matrix_world.translation] for k, e in S['sockets'].items()},
        'sockets_fbx_reimport_xyz': rt['sockets'], 'fbx_objects': rt['objects'], 'glb': glb.name,
        'interface': spec,
        'modeling_method': f'procedural mesh construction (art/source/{KIT}/); procedural shaders (cr_mats.py) baked to one {cfg["tex"]} atlas',
        'reference': f"art/references/{cfg['ref'].split('/')[0]}/ (AI three-view {cfg['ref']}; proportions from the work pack's written sizes, not measured from the image)",
        'unity_import_verified': 'see artifacts/tea-terraces-unity/unity-verify-report.txt',
    }
    (exp / 'model_info.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
    val = {'asset': aid, 'checks': checks, 'all_pass': all(c['pass'] for c in checks), 'seconds': round(time.time() - t0),
           'not_checked': ['in-engine lighting and walking (see the Unity report)', 'mobile frame rate (not measured)']}
    (exp / 'validation.json').write_text(json.dumps(val, ensure_ascii=False, indent=2), encoding='utf-8')
    print('ASSET_COMPLETE', aid, 'all_pass=', val['all_pass'], [c['check'] for c in checks if not c['pass']], round(time.time() - t0), 's', flush=True)


def spec_checks(aid, check):
    out = {}
    if ASSETS[aid]['kind'] == 'bush': return bush_checks(aid, check)
    if ASSETS[aid]['kind'] == 'hedge': return hedge_checks(aid, check)
    if ASSETS[aid]['kind'] == 'te03': return te03_checks(aid, check)
    if ASSETS[aid]['kind'] == 'prop': return prop_checks(aid, check)
    if ASSETS[aid]['kind'] == 'pavilion': return pavilion_checks(aid, check)
    if ASSETS[aid]['kind'] == 'wheel': return wheel_checks(aid, check)
    if ASSETS[aid]['kind'] != 'terrace': return out
    T = S['terrace']; M = S['map']; L = T.L
    lod0 = S['lods'][0]['Main']
    # the connector cross-sections: soil top at both ends sampled from the exported LOD0 by ray, compared with the shared profile
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get(); bvh = BVHTree.FromObject(lod0, dg)
    def ray_z(x, y):
        hit = bvh.ray_cast(Vector((x, y, 5.)), Vector((0, 0, -1)))
        return None if hit[0] is None else hit[0].z
    ends = [0., L] if T.kind != 'end' else [0.]
    worst = 0.; samples = {}
    for s in ends:
        inset = .01 if s == 0 else -.01
        row = []
        for d in [.8 + k * .3 for k in range(11)]:
            x, y = M(s + inset, d); z = ray_z(x, y)
            err = abs((z if z is not None else -9) - (TT.RISE + TT.field_profile(d))); worst = max(worst, err); row.append(round(z if z is not None else -9, 4))
        samples[f's={round(s, 3)}'] = row
    check('connector_soil_at_rise_within_2mm', worst <= .002, {'max_error_m': round(worst, 5), 'samples_z': samples, 'note': 'any two pieces meet on the same heights, so a joint opens no step over 2 mm'})
    # connector planes on the 1 m grid
    corners = {f's={round(s, 3)}': [[round(v, 4) for v in M(s, d)] for d in (0., TT.DEPTH)] for s in ends}
    gentle = T.kind.startswith('gentle')
    grid_pts = [corners['s=0.0']] if gentle else list(corners.values())
    on_grid = all(abs(v - round(v)) < 1e-6 for pts in grid_pts for p in pts for v in p)
    check('connectors_on_1m_grid', on_grid, dict(corners, note='gentle bends: only the entry connector is on the grid; the exit is turned by 30 degrees') if gentle else corners)
    lo, hi = pl.eval_bounds(list(S['lods'][0].values()))
    if gentle:
        (x0, y0), (x1, y1) = M(L, 0.), M(L, TT.DEPTH)
        turn = math.degrees(math.atan2(y1 - y0, x1 - x0)) - 90
        check('exit_connector_turned_30deg', abs(abs(turn) - 30) < .01 and abs(math.hypot(x1 - x0, y1 - y0) - TT.DEPTH) < 1e-4,
              {'exit_front_xy': [round(x0, 4), round(y0, 4)], 'exit_back_xy': [round(x1, 4), round(y1, 4)], 'turn_deg': round(turn, 3)})
        check('nothing_past_connector_planes', lo.x >= -4 - 1e-3, {'min_x': round(lo.x, 4), 'note': 'entry plane x = -4; the exit side is checked by the footprint box'})
    else:
        check('nothing_past_connector_planes', lo.x >= -4 - 1e-3 and (hi.x <= 4 + 1e-3), {'min_x': round(lo.x, 4), 'max_x': round(hi.x, 4)})
    front_ok = True
    if T.kind in ('straight', 'end', 'broken'):
        front_ok = lo.y >= -2 - 1e-3
    check('front_lip_meets_lower_tread_at_z0', front_ok, 'the toe lip starts on the footprint front edge at z = 0')
    out = {'rise_m': TT.RISE, 'depth_m': TT.DEPTH, 'wall_face_inset_m': TT.FACE0, 'batter_per_m': TT.BATTER, 'connector_corners_xy': corners,
           'field_profile': {'ridge_centre_d': TT.RIDGE_D, 'ridge_half_width': TT.RIDGE_HALF, 'ridge_height': TT.RIDGE_H, 'ditch_centre_d': TT.DITCH_D, 'ditch_half_width': TT.DITCH_HALF, 'ditch_depth': TT.DITCH_H},
           'stack_next_row': {'straight': f'(0, +4, +{TT.RISE})', 'inner': 'row above follows the outer radius 8: use straight pieces and another bend', 'outer': 'row above sits on the inner radius 4',
                              'gentle': 'translate the whole row by (0, +4, +rise): in the turned part the upper wall foot overlaps the lower tread by up to 0.54 m, never a gap'}[
                              T.kind if T.kind in ('inner', 'outer') else 'gentle' if T.kind.startswith('gentle') else 'straight']}
    if gentle:
        (x0, y0), (x1, y1) = M(L, 0.), M(L, TT.DEPTH); ang = math.atan2(y1 - y0, x1 - x0) - math.pi / 2
        out['exit_connector'] = {'front_corner_xy': [round(x0, 4), round(y0, 4)], 'heading_deg': round(math.degrees(ang), 3),
                                 'next_straight_origin_xy': [round(x0 + 4 * math.cos(ang) + 2 * math.cos(ang + math.pi / 2), 4), round(y0 + 4 * math.sin(ang) + 2 * math.sin(ang + math.pi / 2), 4)]}
    return out


def te03_checks(aid, check):
    from mathutils.bvhtree import BVHTree
    t = S['te03']; dg = bpy.context.evaluated_depsgraph_get()
    main = S['lods'][0]['Main']; bvh = BVHTree.FromObject(main, dg)
    def ray_z(x, y):
        hit = bvh.ray_cast(Vector((x, y, 5.)), Vector((0, 0, -1)))
        return None if hit[0] is None else round(hit[0].z, 4)
    if t['kind'] == 'stair':
        # each tread sampled on a 7 x 3 grid; a ray that drops into the rounded joint between two slabs is a joint, not the tread, so the tread height is the median
        xs = [-.45 + .15 * k for k in range(7)]; tops, med = [], []
        for i in range(TP.N_STEP):
            zs = sorted(z for f in (.3, .5, .7) for x in xs for z in [ray_z(x, TP.step_front(i) + TP.GOING * f)] if z is not None)
            tops.append([zs[0], zs[len(zs) // 2], zs[-1]]); med.append(zs[len(zs) // 2])
        want = [(i + 1) * TP.RISE_STEP for i in range(TP.N_STEP)]
        err = max(abs(m - w) for m, w in zip(med, want))
        check('step_tops_at_one_sixth_m_within_2cm', err <= .02, {'tread_z_min_median_max': tops, 'design_z': [round(w, 4) for w in want], 'max_error_of_median_m': round(err, 4),
              'note': 'min is a ray into a slab joint or onto a worn edge; the walking check is in Unity'})
        rises = [round(b - a, 4) for a, b in zip([0.] + med, med)]
        check('every_riser_under_0_2m', all(r <= .2 for r in rises), {'rises_m': rises, 'unity_step_offset_m': .3})
        check('top_tread_meets_upper_soil_z1', abs(med[-1] - 1.) <= .02, {'top_tread_z': med[-1]})
        return {'risers': TP.N_STEP, 'rise_m': round(TP.RISE_STEP, 4), 'going_m': TP.GOING, 'run_m': -TP.Y0, 'width_m': TP.W, 'back_edge_y_m': round(t['back'], 3)}
    L = TP.L_PATH if t['kind'] == 'path' else TP.L_STEP
    if t['kind'] == 'path':
        ys = [-.45 + .1 * k for k in range(10)]
        a = [ray_z(-L / 2 + .005, y) for y in ys]; b = [ray_z(L / 2 - .005, y) for y in ys]
        err = max(abs((p or 0) - (q or 0)) for p, q in zip(a, b))
        check('path_ends_share_one_cross_section_2mm', err <= .002, {'left_z': a, 'right_z': b, 'max_diff_m': round(err, 5)})
        mid = [ray_z(x, 0.) for x in (-1.5, -.5, .5, 1.5)]
        check('path_surface_1_to_3cm_above_soil', all(z is not None and 0. <= z <= .04 for z in mid), {'centre_line_z': mid})
        return {'length_m': L, 'width_m': TP.W}
    tops = [ray_z(x, y) for x, y, l, w, tp in TP.STONES]
    check('stepping_tops_4_to_8cm', all(z is not None and .035 <= z <= .085 for z in tops), {'stone_top_z': tops})
    xs = [s_[0] for s_ in TP.STONES]; stride = [round(b - a, 3) for a, b in zip(xs, xs[1:])]
    check('stride_0_4_to_0_7m', all(.4 <= d <= .7 for d in stride), {'stride_m': stride})
    return {'length_m': L, 'width_m': TP.W, 'stones': len(TP.STONES)}


def prop_checks(aid, check):
    """TE04: overall size against the work pack, the shape that tells it from neighbouring kits, and the detail object really optional."""
    p = S['prop']; lods = S['lods']
    lo, hi = pl.eval_bounds([lods[0]['Main']])
    w, d, h = hi.x - lo.x, hi.y - lo.y, hi.z - lo.z
    det = lods[0].get('Detail_Small')
    if p['kind'] == 'tray':
        check('tray_1_2m_long_0_12m_tall', 1.17 <= w <= 1.22 and .68 <= d <= .76 and .105 <= h <= .13, {'main_dims_m': [round(w, 4), round(d, 4), round(h, 4)], 'design': '1.2 x 0.74 x 0.12 m'})
        check('rounded_rectangle_not_round', w / d > 1.45, {'length_to_depth': round(w / d, 3), 'note': 'a round sieve would be 1.0'})
        dlo, dhi = pl.eval_bounds([det]) if det else (lo, hi)
        check('detail_small_is_separate', det is not None and dhi.z <= hi.z + .012, {'detail_object': det.name if det else None, 'detail_top_z_m': round(dhi.z, 4),
              'note': 'bindings, stitches and leaves; turning it off leaves the woven mat and both cedar strips'})
        return {'rim_top_z_m': round(p['rim_top'], 4), 'floor_top_z_m': round(p['floor_z'], 4), 'half_length_m': round(p['half_len'], 4), 'half_depth_m': round(p['half_depth'], 4)}
    check('basket_0_5m_wide_0_4m_tall', .47 <= w <= .52 and .44 <= d <= .52 and .38 <= h <= .42, {'main_dims_m': [round(w, 4), round(d, 4), round(h, 4)], 'design': '0.5 x 0.5 x 0.4 m'})
    check('wide_mouth_tapered', p['rim_outer_r'] > p['foot_r'] * 1.15, {'rim_outer_r': round(p['rim_outer_r'], 4), 'foot_r': round(p['foot_r'], 4)})
    check('detail_small_is_separate', det is not None and lo.z <= 1e-3, {'detail_object': det.name if det else None, 'note': 'lashings, stitches and leaves; turning it off leaves the woven body, rim and foot hoops'})
    return {'rim_top_z_m': round(p['rim_top'], 4), 'rim_outer_radius_m': round(p['rim_outer_r'], 4), 'foot_radius_m': round(p['foot_r'], 4)}


def pavilion_checks(aid, check):
    """TE05: the 5 m cube, a walkable plinth and steps, head room between the posts, the roof clear of the bench."""
    p = S['prop']; lod0 = list(S['lods'][0].values())
    lo, hi = pl.eval_bounds(lod0)
    check('within_5x5x5', hi.x - lo.x <= 5.001 and hi.y - lo.y <= 5.001 and hi.z <= 5.001, {'dims_m': [round(v, 4) for v in hi - lo], 'top_z_m': round(hi.z, 4)})
    dg = bpy.context.evaluated_depsgraph_get()
    def ray_z(x, y, z0=10.):
        best = None
        for o in lod0:
            e = o.evaluated_get(dg); mi = o.matrix_world.inverted()
            ok, loc, *_ = e.ray_cast(mi @ Vector((x, y, z0)), mi.to_3x3() @ Vector((0, 0, -1)))
            if ok:
                z = (o.matrix_world @ loc).z
                best = z if best is None else max(best, z)
        return best
    def ray_up(x, y, z0):
        best = None
        for o in lod0:
            e = o.evaluated_get(dg); mi = o.matrix_world.inverted()
            ok, loc, *_ = e.ray_cast(mi @ Vector((x, y, z0)), mi.to_3x3() @ Vector((0, 0, 1)))
            if ok:
                z = (o.matrix_world @ loc).z
                best = z if best is None else min(best, z)
        return best
    floor = [ray_z(x, y, Z) for x, y, Z in ((0, 0, 1.5), (.5, -.6, 1.5), (-.6, .3, 1.5), (0, -1.2, 1.5))]
    check('floor_at_plinth_top', all(f is not None and abs(f - p['plinth_top']) < .03 for f in floor), {'floor_hits_z_m': [round(f, 4) if f is not None else None for f in floor], 'plinth_top_m': p['plinth_top']})
    steps = [ray_z(0., y, 1.) for y in (-2.38, -2.12, -1.88, -1.6)]
    rises = [round(b - a, 4) for a, b in zip([0.] + steps[:-1], steps)] if all(s is not None for s in steps) else None
    check('steps_rise_under_0_2m', rises is not None and max(rises) <= .2, {'tread_z_m': [round(s, 4) if s is not None else None for s in steps], 'rises_m': rises})
    heads = [ray_up(x, y, p['plinth_top'] + .05) for x, y in ((0, -.6), (0, -1.4), (.6, .5), (-.7, -.5), (-.6, .7))]
    head = [round(h - p['plinth_top'], 3) if h is not None else None for h in heads]
    check('head_room_2_1m', all(h is not None and h >= 2.1 for h in head), {'clear_above_floor_m': head, 'note': 'front of centre, the front opening between the posts, and three points of the walkable floor (the apex post hangs over the very centre)'})
    check('front_opening_2_4m', p['opening'] >= 2.4, {'opening_m': round(p['opening'], 3)})
    return {'plinth_top_z_m': p['plinth_top'], 'step_rise_m': p['step_rise'], 'step_tread_m': p['step_tread'], 'post_centres_m': [p['post_half'], p['post_half']],
            'finial_top_z_m': round(p['finial_top'], 4), 'clear_under_low_beam_z_m': round(p['clear_z'], 4), 'sockets': sorted(S['sockets'])}


def surface_points(objs, step=.02):
    """Points spread over the triangles of objs (world space), about one per step x step; numpy N x 3."""
    out = []
    for o in objs:
        me = o.data; me.calc_loop_triangles(); n = len(me.loop_triangles)
        if not n: continue
        co = np.zeros(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
        tri = np.zeros(n * 3, np.int32); me.loop_triangles.foreach_get('vertices', tri); tri = tri.reshape(-1, 3)
        M = np.array(o.matrix_world, np.float32); co = co @ M[:3, :3].T + M[:3, 3]
        A, B, C = co[tri[:, 0]], co[tri[:, 1]], co[tri[:, 2]]
        area = np.linalg.norm(np.cross(B - A, C - A), axis=1) / 2
        k = np.clip((area / (step * step)).astype(int) + 1, 1, 400)
        idx = np.repeat(np.arange(n), k); r1 = np.sqrt(np.random.default_rng(1).random(len(idx))); r2 = np.random.default_rng(2).random(len(idx))
        out.append(A[idx] * (1 - r1)[:, None] + B[idx] * (r1 * (1 - r2))[:, None] + C[idx] * (r1 * r2)[:, None])
        out.append(co)
    return np.concatenate(out) if out else np.zeros((0, 3))


def wheel_checks(aid, check):
    """RI03: 9 m across, about 2 m wide, the turning part pivots on the origin, and as it turns it never meets the seats or the trough."""
    lods = S['lods']; g = lods[0]
    lo, hi = pl.eval_bounds([g['Wheel']])
    dia = max(hi.y - lo.y, hi.z - lo.z)
    check('wheel_9m_diameter', 8.9 <= dia <= 9.05, {'wheel_dims_m': [round(v, 4) for v in hi - lo], 'design_m': 9.0})
    alo, ahi = pl.eval_bounds(list(g.values()))
    check('assembly_about_2m_wide', 1.9 <= ahi.x - alo.x <= 2.2, {'width_x_m': round(ahi.x - alo.x, 4), 'note': 'axle ends and stone seats; the trough frame stands on the -X side within the same width'})
    c = (lo + hi) / 2
    check('wheel_pivot_at_origin', abs(c.y) < .03 and abs(c.z) < .03, {'wheel_bbox_centre_m': [round(v, 4) for v in c]})
    parts = sorted(g)
    check('separate_parts', all(k in g for k in ('Wheel', 'Seat', 'Trough', 'Detail_Wheel')) and all(k in lods[lv] for lv in (1, 2) for k in ('Wheel', 'Seat', 'Trough')),
          {'groups_LOD0': parts, 'note': 'Wheel and Detail_Wheel turn; Seat, Trough and Detail_Small stand'})
    # swept clearance: the wheel turned through a full revolution occupies, at each x, a set of radii; nothing static may sit there
    W = surface_points([g['Wheel'], g['Detail_Wheel']]); Sx = surface_points([g[k] for k in g if k in ('Seat', 'Trough', 'Detail_Small')])
    cell = .02; occ = set()
    for x, r in zip(np.floor(W[:, 0] / cell).astype(int), np.floor(np.hypot(W[:, 1], W[:, 2]) / cell).astype(int)):
        occ.add((x, r))
    hits = []
    for p_, x, r in zip(Sx, np.floor(Sx[:, 0] / cell).astype(int), np.floor(np.hypot(Sx[:, 1], Sx[:, 2]) / cell).astype(int)):
        if (x, r) in occ:
            hits.append([round(float(v), 3) for v in p_])
    # the axle turns inside its bearing caps, which is meant to touch: ignore static points within 0.25 m of the axle line at the pillars
    hits = [h for h in hits if not (abs(h[0]) > .55 and math.hypot(h[1], h[2]) < .25)]
    check('wheel_turns_clear_of_static_parts', not hits, {'static_points_inside_swept_wheel': len(hits), 'first': hits[:6], 'cell_m': cell,
          'note': 'surface samples of the turning wheel binned by (x, radius about the axle); the axle in its bearings is excluded'})
    p = S['sockets'].get('Socket_Trough_Out')
    return {'diameter_m': round(dia, 4), 'ground_z_m': S['prop']['ground'], 'axle': 'Blender X through the origin', 'trough_outlet_xyz_m': [round(v, 3) for v in p.matrix_world.translation] if p else None,
            'sockets': sorted(S['sockets'])}


def bush_checks(aid, check):
    cfg = S['bush']; lods = S['lods']
    lo, hi = pl.eval_bounds(list(lods[0].values()))
    w = max(hi.x - lo.x, hi.y - lo.y)
    check('width_1_2m', abs(w - 1.2) <= .01, {'plan_width_m': round(w, 4), 'x_m': round(hi.x - lo.x, 4), 'y_m': round(hi.y - lo.y, 4)})
    check('height_0_8_to_1_1m', .8 - 1e-3 <= hi.z <= 1.1 + 1e-3 and abs(hi.z - cfg['H']) <= .01, {'top_m': round(hi.z, 4), 'design_m': cfg['H']})
    wind = {}
    for lv, g in lods.items():
        for gname, o in g.items():
            me = o.data; ca = me.color_attributes.get('Wind')
            if ca is None: wind[o.name] = None; continue
            c = np.zeros(len(ca.data) * 4, np.float32); ca.data.foreach_get('color', c); c = c.reshape(-1, 4)
            wind[o.name] = [round(float(c[:, 0].min()), 3), round(float(c[:, 0].max()), 3)]
    ok = all(v is not None for v in wind.values())
    lw = wind.get(f'{aid}_LOD0'); leaf = wind.get(f'{aid}_Leaves_LOD0')
    check('wind_vertex_colour_on_every_mesh', ok and lw[0] <= .02 and leaf[1] >= .95, {'R_min_max': wind, 'note': 'R 0 at the root to 1 on the outer leaves; G phase; B height'})
    lm = lods[0]['Leaves'].data.materials[0]
    check('leaf_cards_alpha_clip_two_sided', not lm.use_backface_culling, {'material': lm.name, 'alpha': 'BaseColor alpha, clip 0.5'})
    me = lods[0]['Leaves'].data; uv = np.zeros(len(me.loops) * 2, np.float32); me.uv_layers[0].data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
    shoots = int(((uv[:, 0] > .5) & (uv[:, 1] > .5)).sum() // 9)
    check('plucking_table_shoot_cards_present', shoots >= 20, {'cards_using_shoot_cell_approx': shoots})
    st = lods[0].get('Main')
    check('woody_stems_present', st is not None and len(st.data.polygons) > 500, {'main_faces': len(st.data.polygons) if st else 0})
    return {'design': {k: cfg[k] for k in ('H', 'W', 'z_under', 'shoulder', 'stems', 'seed')}, 'fit_scale_xy_z': S.get('fit_scale'), 'collision': 'octagonal prism r 0.42 m, 0.75 H tall'}



def hedge_checks(aid, check):
    cfg = S['hedge']; lods = S['lods']
    lo, hi = pl.eval_bounds(list(lods[0].values()))
    mm = lods[0]['Main'].data; cm_ = np.zeros(len(mm.vertices) * 3, np.float32); mm.vertices.foreach_get('co', cm_); cm_ = cm_.reshape(-1, 3)
    soil_x = [round(float(cm_[:, 0].min()), 4), round(float(cm_[:, 0].max()), 4)]
    ok_x = abs(soil_x[0] + cfg['L'] / 2) <= .002 and (abs(soil_x[1] - cfg['L'] / 2) <= .002 if cfg['ends'][1] else soil_x[1] < cfg['L'] / 2)
    check('length_depth_height', ok_x and abs(hi.y - lo.y - cfg['D']) <= .01 and abs(hi.z - cfg['H']) <= .01 and lo.x >= -cfg['L'] / 2 - .15 and hi.x <= cfg['L'] / 2 + .15,
          {'joint_pitch_m': cfg['L'], 'soil_and_stems_x_m': soil_x, 'overall_x_m': [round(lo.x, 4), round(hi.x, 4)], 'y_m': round(hi.y - lo.y, 4), 'top_m': round(hi.z, 4),
           'note': 'open ends: the soil strip and core end on x = +-L/2 (the joint), leaf cards overhang it by up to 0.15 m and interleave with the neighbour'})
    # open ends: leaves must reach the cut on both faces and the core tube must end on the cut, so a neighbour carries straight on
    me = lods[0]['Leaves'].data; co = np.zeros(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    ends = {}
    for sgn, is_open in ((-1, cfg['ends'][0]), (1, cfg['ends'][1])):
        if not is_open: continue
        cut = sgn * cfg['L'] / 2; near = co[np.abs(co[:, 0] - cut) < .06]   # leaf cards crossing the joint plane
        ends['+X' if sgn > 0 else '-X'] = {'leaf_verts_within_6cm': int(len(near)), 'reach_m': round(float(np.abs(co[:, 0]).max()), 4),
                                         'y_span_m': [round(float(near[:, 1].min()), 3), round(float(near[:, 1].max()), 3)] if len(near) else None,
                                         'z_span_m': [round(float(near[:, 2].min()), 3), round(float(near[:, 2].max()), 3)] if len(near) else None}
    ok = all(e['leaf_verts_within_6cm'] >= 150 and e['y_span_m'] and e['y_span_m'][0] < -.4 and e['y_span_m'][1] > .4 and e['z_span_m'][0] < .25 and e['z_span_m'][1] > cfg['H'] - .1 for e in ends.values())
    check('open_ends_leaves_reach_the_cut', ok, ends)
    wind = {}
    for lv, g in lods.items():
        for gname, o in g.items():
            ca = o.data.color_attributes.get('Wind')
            if ca is None: wind[o.name] = None; continue
            c = np.zeros(len(ca.data) * 4, np.float32); ca.data.foreach_get('color', c); c = c.reshape(-1, 4)
            wind[o.name] = [round(float(c[:, 0].min()), 3), round(float(c[:, 0].max()), 3)]
    lw = wind.get(f'{aid}_LOD0'); leaf = wind.get(f'{aid}_Leaves_LOD0')
    check('wind_vertex_colour_on_every_mesh', all(v is not None for v in wind.values()) and lw[0] <= .02 and leaf[1] >= .95, {'R_min_max': wind})
    lm = lods[0]['Leaves'].data.materials[0]
    check('leaf_cards_alpha_clip_two_sided', not lm.use_backface_culling, {'material': lm.name})
    uv = np.zeros(len(me.loops) * 2, np.float32); me.uv_layers[0].data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
    shoots = int(((uv[:, 0] > .5) & (uv[:, 1] > .5)).sum() // 9)
    check('plucking_table_shoot_cards_present', shoots >= 20 * cfg['L'], {'cards_using_shoot_cell_approx': shoots})
    return {'design': {k: cfg[k] for k in ('L', 'D', 'H', 'z_under', 'shoulder', 'seed', 'ends', 'plants')}, 'fit_scale_xyz': S.get('fit_scale'),
            'collision': 'prism 0.76 m deep, 0.75 H tall; full length at an open end, rounded at a closed end'}

def close_shot(objs, path, samples=32, target=None, eye=None, lens=40):
    """A person's-eye close-up of the wall: 1.6 m eye height, 2.4 m in front of it."""
    scene = bpy.context.scene; pl.show_only(objs)
    cam, centre, ext = pl.studio(objs, samples)
    cam.data.type = 'PERSP'; cam.data.lens = lens
    target = Vector(target or (centre.x - ext.x * .12, centre.y - ext.y * .45, .55)); eye = Vector(eye or (target.x + 1.3, target.y - 2.4, 1.6))
    cam.location = eye; cam.rotation_euler = (target - eye).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(path); bpy.ops.render.render(write_still=True)


def wire(objs, path):
    """Wireframe over the baked colour, same 3/4 angle as the hero."""
    for o in objs:
        m = o.modifiers.new('QA_Wire', 'WIREFRAME'); m.thickness = .004; m.use_replace = False; m.material_offset = 99
    pl.persp_shot(objs, path, samples=24)
    for o in objs: o.modifiers.remove(o.modifiers['QA_Wire'])


def _strip(paths, out):
    ims = [bpy.data.images.load(str(p)) for p in paths]
    w, h = ims[0].size
    arr = np.concatenate([np.array(i.pixels[:], np.float32).reshape(h, w, 4) for i in ims], axis=1)
    im = bpy.data.images.new(out.stem, w * len(ims), h, alpha=True); im.pixels.foreach_set(arr.ravel())
    im.filepath_raw = str(out); im.file_format = 'PNG'; im.save()


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    force = '--force' in argv; ids = [a for a in argv if a in ASSETS] or list(ASSETS)
    if '--preview' in argv:
        out = Path(argv[argv.index('--preview') + 1])
        for aid in ids: preview(aid, out)
    else:
        for aid in ids: run(aid, force)
