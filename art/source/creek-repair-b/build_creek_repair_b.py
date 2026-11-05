"""creek-repair-b v001 (work pack B-56h, section models): CR05 work shelter + tea, CR09 household gates, CR12 ranking board.

Run one asset per process:
  blender --background --factory-startup --python art/source/creek-repair-b/build_creek_repair_b.py -- CR09_A_RopeGate
  ... -- CR09_A_RopeGate --preview <dir>     quick procedural look, no bake or export
An asset whose validation.json exists is skipped unless --force is given.

ti_core / ti_mats / mk_mats are copied unchanged from art/source/harvest-market-b; ti_pipeline started from there and now also cleans faces and UVs. LOD1/LOD2 land on about
50% / 15% of LOD0. Each export group is its own object with its own pivot; one baked atlas per asset.
Writes:
  art/source/creek-repair-b/blend/<ID>_v001.blend
  art/exports/creek-repair-b/<ID>/<ID>_v001.fbx, Textures/, model_info.json, validation.json
  art/previews/creek-repair-b/<ID>/turnaround/ (ten views + views.json), hero, LOD sheet, state renders
"""
import bpy, bmesh, sys, json, math, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np
from mathutils import Vector, Matrix
import ti_core, ti_mats, ti_pipeline as pl
import cr09_gate as G9, cr05_shelter as G5, cr12_board as G12, cr_site as GS, cr_wm as GW, cr_town as GT
from ti_core import S

KIT = 'creek-repair-b'
ART = HERE.parents[1]
VER = 'v001'
LOD_TARGET = {1: .50, 2: .15}
LOD_DROPS = {1: (2, 3, 99), 2: (1, 2, 3, 99)}

SLIPS = {f'Slip_{i:02d}': 'centre' for i in range(1, 13)}
WATER_STATE = '水面是獨立模型 <ID>_water_v001.fbx，不在渠身 FBX 裡：原點與渠身相同，放同一位置；UV u 0–1 橫跨、v 沿水流每公尺 +1，材質用流動 shader，沒有烘貼圖'
WATER_LODS = ((6, 32), (4, 24), (2, 14))     # across, along: 384 / 192 / 56 triangles


ASSETS = {
    'CR05_WorkShelter': dict(zh='工地涼棚和茶水', slot='修水路工地', tex=2048, palette=G5.palette, build=G5.cr05, ref='CR05',
        limit=(4., 3., 2.8), pivots={'Bench': 'bottom', 'Crate': 'bottom', 'TeaBucket': 'bottom', 'Ladle': 'bottom', 'Bowl_01': 'bottom', 'Bowl_02': 'bottom', 'Bowl_03': 'bottom', 'Bowl_04': 'bottom'},
        keep_pivot=('Canopy',), uv_weight={'Canopy': .45, 'Bench': 1.4, 'Crate': 2.2, 'TeaBucket': 3., 'Ladle': 5., 'Bowl_01': 7., 'Bowl_02': 7., 'Bowl_03': 7., 'Bowl_04': 7.},
        states=['茶水桶、水瓢、碗、木箱、長凳各自獨立，可移動；Canopy 原點與整件相同'],
        note='四根竹柱、一片補過的帆布頂（_Canopy）、一張長凳（_Bench）、茶水桶（_TeaBucket）、水瓢（_Ladle）、四個碗（_Bowl_01..04）、木箱（_Crate）都是獨立物件；_Collision 只有四根柱子，長凳和茶水不擋人。'),
    'CR09_A_RopeGate': dict(zh='每戶分水小閘（繩子綁）', slot='每戶田口 flowRoute kind=gate', tex=2048, palette=lambda: G9.palette('A'), build=G9.cr09_a, ref='CR09',
        limit=(.8, .5, .9), pivots={'Gate': 'bottom'}, states=['Gate 關：局部 Z +0', 'Gate 開：局部 Z +0.3 m（Socket_GateOpen）'],
        note='閘板 _Gate 是獨立物件，沿 Z 往上 0.3 m；關閉時總高 0.6 m，全開時 0.9 m（都在 0.9 m 內），全開時閘板下緣仍有 0.12 m 留在槽內。這戶用繩子綁：粗石、彎樹枝把手、舊繩加新繩、裂板用繩纏補。'),
    'CR09_B_TenonGate': dict(zh='每戶分水小閘（木榫）', slot='每戶田口 flowRoute kind=gate', tex=2048, palette=lambda: G9.palette('B'), build=G9.cr09_b, ref='CR09',
        limit=(.8, .5, .9), pivots={'Gate': 'bottom'}, states=['Gate 關：局部 Z +0', 'Gate 開：局部 Z +0.3 m（Socket_GateOpen）'],
        note='閘板 _Gate 是獨立物件，沿 Z 往上 0.3 m；關閉時總高 0.6 m，全開時 0.9 m（都在 0.9 m 內）。這戶用木榫：修整過的方石加蓋石、方把手貫穿榫加楔、橫檔用木釘，比 A 整齊。'),
    'CR12_RankingBoard': dict(zh='榜單告示欄', slot='山城（格位由核心組放置）', tex=2048, palette=G12.palette, build=G12.cr12, ref='CR12',
        limit=(3., .6, 2.8), pivots={**SLIPS, 'TeaCup': 'bottom'}, uv_weight={**{k: 3. for k in SLIPS}, 'TeaCup': 14.},
        states=['Slip_01..12 各自獨立，原點在紙面中心、紙面朝 -Y，字由 UI 疊上'],
        note='12 張空白榜單紙條（_Slip_01..12）各自獨立、紙面無字；_Slip_01 是榜首，最舊、最大、邊角最捲。爛茶杯 _TeaCup 獨立，放在磨亮的欄杆上。_Collision 為立柱和欄杆。'),
    'CR03_StonePile': dict(zh='石料堆（少中多）', slot='修水路工地', tex=2048, palette=GS.stone_palette, build=GS.cr03_stone, limit=(2., 1.5, 1.), keep_pivot=GS.STAGES,
        states=['Stage_Low / Stage_Mid / Stage_High 三個獨立物件，原點相同，一次顯示一個'], note='三個階段各自完整；_Collision 以最多階段為準。'),
    'CR03_TimberRack': dict(zh='木料架（少中多）', slot='修水路工地', tex=2048, palette=GS.timber_palette, build=GS.cr03_timber, limit=(2.5, 1., 1.2), keep_pivot=GS.STAGES,
        states=['架子是 Main，Stage_Low / Stage_Mid / Stage_High 是架上的料，一次顯示一個'], note='架子常駐；三個階段只換料。'),
    'CR03_MudHeap': dict(zh='泥堆（少中多）', slot='修水路工地', tex=2048, palette=GS.mud_palette, build=GS.cr03_mud, limit=(2., 2., .8), keep_pivot=GS.STAGES,
        states=['Stage_Low / Stage_Mid / Stage_High 三個獨立物件，原點相同，一次顯示一個'], note='_Collision 是最多階段中央的低矮方塊（1.36 m 見方、高 0.46 m），周圍的泥不擋人；少階段時方塊比泥高。'),
    'CR04_Tools': dict(zh='工具組', slot='修水路工地', tex=2048, palette=GS.tools_palette, build=GS.cr04, no_collision='手持工具，不擋人', limit=(3., 1.45, .55), pivots={k: 'bottom' for k in ('Spade', 'Basket', 'Tamper', 'MortarBucket', 'Trowel')},
        states=['鏟、畚箕、木夯、灰桶、抹刀各自獨立，各有 Socket_Hand_<名稱>'], note='五件各自獨立，並排只為了展示；每件都有握持點。'),
    'CR06_Straight': dict(zh='土堤木樁渠（直段）', slot='clear_silt', tex=2048, palette=GS.channel_palette, build=GS.cr06_straight, limit=(1., 2., .5), pivots={},
        states=[WATER_STATE], note='接口與 B02 相同：淨寬 0.40、槽底 z 0.10；Socket_PortIn / Out 標明兩端。'),
    'CR06_Short': dict(zh='土堤木樁渠（0.5 m 短段）', slot='clear_silt', tex=2048, palette=GS.channel_palette, build=GS.cr06_short, limit=(1.1, .6, .5), pivots={},
        states=[WATER_STATE], note='工作單外加的：兩段彎之間差半公尺，用來把土溝從 R1 接到田的進水口。接口與直段相同。'),
    'CR06_Bend': dict(zh='土堤木樁渠（彎段）', slot='clear_silt', tex=2048, palette=GS.channel_palette, build=GS.cr06_bend, limit=(2., 2., .5), pivots={},
        states=[WATER_STATE], note='半徑 1.25 m 的四分之一圓，弧長約 2 m；接口與 B03 相同。'),
    'CR08_Straight': dict(zh='竹木渡槽（直段）', slot='protect_nursery', tex=2048, palette=GS.flume_palette, build=GS.cr08_straight, limit=(.7, 2., .5), pivots={},
        states=[WATER_STATE], note='接口與 B02 相同；架在 CR08_Trestle_* 上。'),
    'CR08_Bend': dict(zh='竹木渡槽（彎段）', slot='protect_nursery', tex=2048, palette=GS.flume_palette, build=GS.cr08_bend, limit=(2., 2., .5), pivots={},
        states=[WATER_STATE], note='半徑 1.25 m；接口與 B03 相同。'),
    'CR08_Trestle_080': dict(zh='渡槽支架 0.8 m', slot='protect_nursery', tex=1024, palette=GS.trestle_palette, build=GS.cr08_t080, limit=(1.3, .6, .8), states=['Socket_TroughSeat 為槽底座面'], note='A 字架，頂面高 0.8 m。'),
    'CR08_Trestle_150': dict(zh='渡槽支架 1.5 m', slot='protect_nursery', tex=1024, palette=GS.trestle_palette, build=GS.cr08_t150, limit=(1.6, .6, 1.5), states=['Socket_TroughSeat 為槽底座面'], note='A 字架，頂面高 1.5 m。'),
    'CR08_Trestle_250': dict(zh='渡槽支架 2.5 m', slot='protect_nursery', tex=1024, palette=GS.trestle_palette, build=GS.cr08_t250, limit=(2.1, .6, 2.5), states=['Socket_TroughSeat 為槽底座面'], note='A 字架，頂面高 2.5 m。'),
    'CR15_DitchCross': dict(zh='土渠十字口', slot='配水渠', tex=2048, palette=GS.channel_palette, build=GS.cr15_cross, limit=(1.6, 1.6, .5), pivots={},
        states=[WATER_STATE], note='工作單外加的：主水路從南進，分西、東、北三路到各田閘門。四個接口都與 CR06 相同。'),
    'CR14_WeedClump': dict(zh='泥上的水草叢', slot='水草泥堆', tex=1024, palette=GS.weed_palette, build=GS.cr14_weed, limit=(.5, .5, .25), no_collision='軟草，不擋人', states=['一叢一個物件，遊戲依水草剩餘量一叢叢收掉'],
        note='工作單外加的：取代原本用線條畫的水草。草葉一律倒向 +Y，也就是要拉的方向；根部是一團泥苔。'),
    'CR07_Celebration': dict(zh='溪邊慶祝擺設', slot='修好後的慶祝', tex=2048, minTier='high', palette=GT.cele_palette, build=GT.cr07, limit=(6.6, 2.2, 2.8), pivots={'Table': 'bottom', 'FruitBasket': 'bottom', **{f'Jar_{i}': 'bottom' for i in range(1, 3)}, **{f'Lantern_{i:02d}': 'centre' for i in range(1, 10)}, **{f'Lantern_{i:02d}_Lit': 'centre' for i in range(1, 10)}},
        states=['Lantern_01..09 紙燈，夜裡顯示同名 _Lit（發光殼）'], note='3 m 拼湊長桌、三腳竹竿撐 6 m 紙燈串 9 盞（第 3 盞有補丁）、兩個酒罈、果籃。minTier: high。'),
    'CR10_CharmStall': dict(zh='符紙飾品攤', slot='A4_山城街', tex=2048, palette=GT.charm_palette, build=GT.cr10, limit=(3.5, 2., 2.8), pivots={**{f'CharmString_{i:02d}': f'Socket_Charm_{i:02d}' for i in range(1, 25)}, 'Banner': 'bottom'},
        states=['CharmString_01..24 原點在各串頂端，可在風中晃'], note='小瓦頂推車；符紙只有抽象硃砂圈紋，無字；車頂歪布幡無圖案。短腳墊磚。'),
    'CR11_NoodleStall': dict(zh='麵攤', slot='A4_山城街', tex=2048, palette=GT.noodle_palette, build=GT.cr11, limit=(4.5, 3.5, 2.8), pivots={'Bowl_Full': 'bottom', 'Bowl_Empty': 'bottom', 'Bench_Front': 'bottom', 'Bench_Back': 'bottom', 'Sign': 'bottom'},
        states=['Bowl_Full / Bowl_Empty 麵碗獨立，同一個位置一次顯示一個', 'Socket_Steam 在大鍋上方，蒸氣由遊戲放'], note='單坡披棚：補丁帆布、板牆竹編；磚灶大鍋、案板、碗架、方桌、兩條長凳（一條墊腳）；招牌布無字。'),
    'WM01_MillHouse': dict(zh='水磨坊', slot='A3_MillHouse', tex=2048, palette=GW.mill_palette, build=GW.wm01, limit=(8., 6., 6.), states=['門扇開著，從門看得到屋內磨盤；Socket_WheelAxle 是水車軸的入口（東側）'], note='石基、木構、青灰瓦；不做室內場景，只有磨盤和暗色內襯。麻袋 Detail_Sacks 可關。'),
    'WM02_WaterWheel': dict(zh='水車', slot='A3_WaterWheel', tex=2048, palette=GW.wheel_palette, build=GW.wm02, limit=(1.2, 5., 5.), axle_origin=True, states=['原點在轉軸中心，繞本地 X 軸（Unity 同為 X）旋轉'], note='輪徑 4.6 m、16 片輪葉（一片新換，下方幾片帶藻）；軸為 64 邊正圓。'),
    'WM04_Millstones': dict(zh='舊磨盤和麻袋', slot='A3_Millstones', tex=2048, palette=GW.mills_palette, build=GW.wm04, limit=(2., 1.5, 1.), states=['靜物'], note='兩片磨盤互靠、三袋麻袋和一支木勺。'),
    'WM05_WashSteps': dict(zh='洗衣石階', slot='A3_WashSteps', tex=2048, palette=GW.steps_palette, build=GW.wm05, limit=(6., 3., 1.2), states=['最下一階單獨用較光滑的材質'], note='四階朝 -Y 入水；最下一階磨得最亮；洗衣石、綁籃木樁。'),
    'WM07_StoneBridge': dict(zh='單拱石橋', slot='A3_StoneBridge', tex=2048, palette=GW.bridge_palette, build=GW.wm07, limit=(4., 12., 4.), states=['碰撞：橋面斜面可走，兩側有欄杆牆'], note='單拱跨距 6 m、橋面寬 2.4 m、坡度約 13.8 度；Socket_RoadEnd_* 為兩端路面。'),
    'WM09_BambooPavilion': dict(zh='六角竹亭', slot='A3_BambooPavilion', tex=2048, palette=GW.pav_palette, build=GW.wm09, limit=(3.5, 3.5, 4.), states=['靜物'], note='六角、竹柱、茅草頂、中間石桌四石凳；一面開口。'),
}


def route_details():
    """Pack rule: small attachments of the main body export as their own Detail_Small object. Named pieces keep theirs."""
    for o in S['parts']:
        if o.get('group') == 'Main' and (int(o.get('detail', 0)) >= 1 or o.name.split('.')[0] in ('Moss', 'Foot_Moss')):
            o['group'] = 'Detail_Small'


LOD0_TRIM = {'WM09_BambooPavilion': .62, 'WM01_MillHouse': .68, 'CR05_WorkShelter': .68, 'CR11_NoodleStall': .65, 'WM05_WashSteps': .75, 'WM02_WaterWheel': .82, 'CR10_CharmStall': .7, 'CR12_RankingBoard': .52, 'CR08_Straight': .65, 'CR08_Bend': .65, 'CR03_TimberRack': .68, 'WM07_StoneBridge': .75}


def make_lods():
    """LOD1/LOD2 per export group: drop small parts while enough triangles remain, then collapse to the target."""
    tris = lambda me: sum(len(p.vertices) - 2 for p in me.polygons)
    if S.get('lod0_ratio'):   # the densest pieces carry triangles the eye never sees: collapse only groups big enough to spare them; compared side by side in _qa/lod0_cut_*
        for gname, src in S['lod0'].items():
            if tris(src.data) < 6000: continue
            bpy.ops.object.select_all(action='DESELECT'); src.select_set(True); bpy.context.view_layer.objects.active = src
            m = src.modifiers.new('LOD0_trim', 'DECIMATE'); m.use_collapse_triangulate = True; m.ratio = S['lod0_ratio']
            bpy.ops.object.modifier_apply(modifier=m.name)
            pl.orient_faces(src.data, flush=False); pl.spread_zero_uv([src])
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
                for _ in range(6):
                    dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); tm_ = e.to_mesh(); n = tris(tm_); e.to_mesh_clear()
                    if abs(n - want) <= max(2, want * .01): break
                    m.ratio = min(1., m.ratio * want / max(n, 1))
                bpy.ops.object.modifier_apply(modifier=m.name)
                pl.orient_faces(o.data, flush=False); pl.spread_zero_uv([o])   # the collapse can leave slivers and turn a thin piece inside out
            try: bpy.ops.mesh.customdata_custom_splitnormals_clear()
            except Exception: pass
            bpy.ops.object.shade_smooth_by_angle(angle=math.radians(38))
            lods[lv][gname] = o
            report.setdefault(gname, {'LOD0': n0})[f'LOD{lv}'] = tris(o.data)
    S['lods'] = lods
    return report


def set_pivots(cfg):
    """Give each export group its own origin (bottom centre, paper centre or a socket). Mesh data moves, world stays."""
    piv = cfg.get('pivots', {})
    for gname, o in S['lod0'].items():
        want = piv.get(gname)
        if gname == 'Main' or gname in cfg.get('keep_pivot', ()) or not want: continue
        lo, hi = pl.eval_bounds([o])
        if want == 'bottom': p = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
        elif want == 'centre': p = (lo + hi) / 2
        else: p = S['sockets'][want].matrix_world.translation.copy()
        o.data.transform(Matrix.Translation(-p)); o.location = p
    bpy.context.view_layer.update()


def make_collision(aid, shift):
    """Boxes (and rotated hulls if ever needed) as one mesh named <ID>_Collision; hidden renderer, MeshCollider in Unity."""
    boxes = S.get('collision') or []
    extra = S.get('collision_mesh')
    if not boxes and not extra: return None
    verts, faces = [], []
    if extra:
        verts += [tuple(Vector(v) + shift) for v in extra[0]]; faces += list(extra[1])
    for lo, hi in boxes:
        k = len(verts); lo = Vector(lo) + shift; hi = Vector(hi) + shift
        verts += [(x, y, z) for z in (lo.z, hi.z) for y in (lo.y, hi.y) for x in (lo.x, hi.x)]
        faces += [(k, k + 2, k + 3, k + 1), (k + 4, k + 5, k + 7, k + 6), (k, k + 1, k + 5, k + 4), (k + 2, k + 6, k + 7, k + 3), (k, k + 4, k + 6, k + 2), (k + 1, k + 3, k + 7, k + 5)]
    me = bpy.data.meshes.new(aid + '_Collision'); me.from_pydata(verts, [], faces); me.update()
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
                             add_leaf_bones=False, bake_anim=False, path_mode='STRIP', embed_textures=False)
    for o in extra: o.hide_render = True


def export_water(aid, shift, fit, path):
    """The water of a channel piece as its own FBX: same origin as the body, no baked texture, flow UVs.
    v is whole metres per piece, so the shader's one-metre repeat joins pieces without a seam."""
    cross = S.get('water_cross')
    if cross:
        return export_cross_water(aid, cross, shift, fit, path)
    trace = S['water_path']
    length = sum((trace((k + 1) / 200)[0] - trace(k / 200)[0]).length for k in range(200))
    run_m = max(1, round(length))
    mat = bpy.data.materials.new('Water_Surface'); mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']; bsdf.inputs['Base Color'].default_value = (.04, .27, .27, 1); bsdf.inputs['Roughness'].default_value = .12; bsdf.inputs['Alpha'].default_value = .85
    root = bpy.data.objects.new(aid + '_water', None); S['lodcol'].objects.link(root)
    objs = {}
    for lv, (nu, nv) in enumerate(WATER_LODS):
        verts, faces, uvs = [], [], []
        for j in range(nv + 1):
            p, n = trace(j / nv)
            for i in range(nu + 1):
                q = p + n * ((i / nu - .5) * 2 * GS.CLEAR) + Vector((0, 0, GS.WATER)) + shift
                verts.append((q.x * fit[0], q.y * fit[1], q.z * fit[2])); uvs.append((i / nu, j / nv * run_m))
        for j in range(nv):
            for i in range(nu):
                a = j * (nu + 1) + i
                faces.append((a, a + 1, a + nu + 2, a + nu + 1))
        me = bpy.data.meshes.new(f'{aid}_water_LOD{lv}'); me.from_pydata(verts, [], faces); me.update()
        layer = me.uv_layers.new(name='UVMap')
        for loop in me.loops: layer.data[loop.index].uv = uvs[loop.vertex_index]
        me.materials.append(mat)
        for poly in me.polygons: poly.use_smooth = True
        o = bpy.data.objects.new(me.name, me); S['lodcol'].objects.link(o); o.parent = root; objs[lv] = o
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT')
    root.select_set(True)
    for o in objs.values(): o.select_set(True)
    bpy.context.view_layer.objects.active = root
    bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True, object_types={'MESH', 'EMPTY'},
                             apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', bake_space_transform=True,
                             axis_forward='-Z', axis_up='Y', mesh_smooth_type='FACE', use_mesh_modifiers=True,
                             add_leaf_bones=False, bake_anim=False, path_mode='STRIP', embed_textures=False)
    # kept in the .blend beside the body, moving with it
    for o in objs.values(): o.parent = S['root']
    bpy.data.objects.remove(root, do_unlink=True)
    bpy.context.view_layer.update()
    return objs, length, run_m


def export_cross_water(aid, reach, shift, fit, path):
    """The crossing's water: five flat patches, one for the middle and one per arm, with v running away from the middle along each arm."""
    c = GS.CLEAR
    mat = bpy.data.materials.new('Water_Surface'); mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']; bsdf.inputs['Base Color'].default_value = (.04, .27, .27, 1); bsdf.inputs['Roughness'].default_value = .12; bsdf.inputs['Alpha'].default_value = .85
    root = bpy.data.objects.new(aid + '_water', None); S['lodcol'].objects.link(root); objs = {}
    arms = (((-c, -reach), (c, -c), False, 1), ((-c, -c), (c, c), False, 1), ((-c, c), (c, reach), False, 1), ((c, -c), (reach, c), True, 1), ((-reach, -c), (-c, c), True, -1))
    for lv, cells in enumerate((6, 3, 1)):
        verts, faces, uvs = [], [], []
        for (x0, y0), (x1, y1), sideways, sign in arms:
            first = len(verts)
            for j in range(cells + 1):
                for i in range(cells + 1):
                    x, y = x0 + (x1 - x0) * i / cells, y0 + (y1 - y0) * j / cells; q = Vector((x, y, GS.WATER)) + shift
                    verts.append((q.x * fit[0], q.y * fit[1], q.z * fit[2]))
                    uvs.append(((y + c) / (2 * c), x * sign) if sideways else ((x + c) / (2 * c), y))
            for j in range(cells):
                for i in range(cells):
                    a = first + j * (cells + 1) + i
                    faces.append((a, a + 1, a + cells + 2, a + cells + 1))
        me = bpy.data.meshes.new(f'{aid}_water_LOD{lv}'); me.from_pydata(verts, [], faces); me.update()
        layer = me.uv_layers.new(name='UVMap')
        for loop in me.loops: layer.data[loop.index].uv = uvs[loop.vertex_index]
        me.materials.append(mat)
        for poly in me.polygons: poly.use_smooth = True
        o = bpy.data.objects.new(me.name, me); S['lodcol'].objects.link(o); o.parent = root; objs[lv] = o
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT')
    root.select_set(True)
    for o in objs.values(): o.select_set(True)
    bpy.context.view_layer.objects.active = root
    bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True, object_types={'MESH', 'EMPTY'},
                             apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', bake_space_transform=True,
                             axis_forward='-Z', axis_up='Y', mesh_smooth_type='FACE', use_mesh_modifiers=True,
                             add_leaf_bones=False, bake_anim=False, path_mode='STRIP', embed_textures=False)
    for o in objs.values(): o.parent = S['root']
    bpy.data.objects.remove(root, do_unlink=True)
    bpy.context.view_layer.update()
    return objs, 1., 1


def run(aid, force=False):
    cfg = ASSETS[aid]
    exp = ART / 'exports' / KIT / aid; prev = ART / 'previews' / KIT / aid; blend = ART / 'source' / KIT / 'blend'
    if (exp / 'validation.json').exists() and not force:
        print('ALREADY_COMPLETE', aid, flush=True); return
    t0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene; scene.unit_settings.system = 'METRIC'; scene.unit_settings.scale_length = 1
    bpy.context.preferences.filepaths.save_version = 0
    ti_mats.MAT_INFO.clear(); ti_core.reset_state(aid)
    P = cfg['palette'](); cfg['build'](P)
    bpy.context.view_layer.update()
    lo0, hi0 = pl.eval_bounds(S['parts']); shift = -Vector(((lo0.x + hi0.x) / 2, (lo0.y + hi0.y) / 2, lo0.z))
    pl.normalise(); route_details()
    pl.join_groups(); pl.settle_loose(); pl.separate_objects(); set_pivots(cfg); pl.uv_atlas(cfg.get('uv_weight'), cfg['tex']); pl.spread_zero_uv()
    pl.bake(exp / 'Textures', cfg['tex'])
    S['lod0_ratio'] = LOD0_TRIM.get(aid); lod_report = make_lods(); pl.export_materials()
    make_collision(aid, shift)
    S['col'].hide_render = True; S['col'].hide_viewport = True
    lod0 = list(S['lods'][0].values())
    lo, hi = pl.eval_bounds(lod0); dims = hi - lo
    if cfg.get('axle_origin'):
        # the wheel turns about its origin: move the meshes, the collision and the sockets down to the axle
        drop = Matrix.Translation((0, 0, -(lo.z + hi.z) / 2))
        for groups in S['lods'].values():
            for o in groups.values(): o.data.transform(drop)
        if S.get('collision_obj'): S['collision_obj'].data.transform(drop)
        bpy.context.view_layer.update()
        lo, hi = pl.eval_bounds(lod0); dims = hi - lo
    elif 1e-5 < abs(lo.z) < .005 or max(abs(lo.x + hi.x), abs(lo.y + hi.y)) / 2 > 5e-4:
        # settling a part or pulling flush pieces apart can move the outermost one by a few millimetres: the asset still stands centred on z = 0
        drop = Matrix.Translation((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))
        for groups in S['lods'].values():
            for o in groups.values(): o.data.transform(drop)
        if S.get('collision_obj'): S['collision_obj'].data.transform(drop)
        bpy.context.view_layer.update()
        lo, hi = pl.eval_bounds(lod0); dims = hi - lo
    # a stray stake tip or tile lip can pass the limit by a few centimetres: squeeze that axis, never more than 3.5 %
    fit = [min(1., l / d) if d > 0 else 1. for d, l in zip(dims, cfg['limit'])]
    fit_applied = [round(v, 4) for v in fit]
    if min(fit) < 1:
        assert min(fit) >= .965, f'{aid} is over its limit by more than a trim: {dims} {cfg["limit"]}'
        m = Matrix.Diagonal((*fit, 1.))
        targets = {k: m @ e.matrix_world.translation for k, e in S['sockets'].items()}
        for groups in S['lods'].values():
            for o in groups.values():
                o.data.transform(m); o.location = m @ o.location
        if S.get('collision_obj'): S['collision_obj'].data.transform(m)
        bpy.context.view_layer.update()
        for k, e in S['sockets'].items():
            mw = e.matrix_world.copy(); mw.translation = targets[k]; e.matrix_world = mw
        bpy.context.view_layer.update()
        lo, hi = pl.eval_bounds(lod0); dims = hi - lo
    checks = []
    def check(name, ok, detail): checks.append({'check': name, 'pass': bool(ok), 'detail': detail})
    check('axis_fit_scale', min(fit) >= .965, fit_applied)
    pieces = {}
    for gname, o in S['lods'][0].items():
        a, b = pl.eval_bounds([o]); pieces[gname] = {'dims_m': [round(v, 4) for v in b - a], 'pivot': [round(v, 4) for v in o.location],
                                                      'min_z_local': round(a.z - o.location.z, 4)}
    check('origin_bottom_centre' if not cfg.get('axle_origin') else 'origin_at_axle_centre', (abs(lo.z) < 1e-4 if not cfg.get('axle_origin') else abs(lo.z + hi.z) < 2e-3) and abs((lo.x + hi.x) / 2) < 1e-3 and abs((lo.y + hi.y) / 2) < 1e-3,
          {'min': [round(v, 4) for v in lo], 'max': [round(v, 4) for v in hi]})
    check('within_size_limit', all(d <= l + 1e-4 for d, l in zip(dims, cfg['limit'])), {'dims_m': [round(v, 4) for v in dims], 'limit_m': cfg['limit']})
    spec_checks(aid, check, pieces, dims, shift)
    tot = {k: sum(g[k] for g in lod_report.values()) for k in ('LOD0', 'LOD1', 'LOD2')}
    r1, r2 = tot['LOD1'] / tot['LOD0'], tot['LOD2'] / tot['LOD0']
    check('lod_ratios_50_15', .45 <= r1 <= .55 and .12 <= r2 <= .18, {'triangles': tot, 'LOD1': round(r1, 3), 'LOD2': round(r2, 3), 'per_group': lod_report})
    exp.mkdir(parents=True, exist_ok=True)
    fbx = exp / f'{aid}_{VER}.fbx'
    export_fbx(fbx)
    rt = pl.fbx_roundtrip(fbx)
    check('fbx_reimport_dimensions', all(abs(a - b) < 2e-3 for a, b in zip(rt['lod0_dimensions_m'], dims)),
          {'fbx_lod0_dims_m': rt['lod0_dimensions_m'], 'blend_dims_m': [round(v, 4) for v in dims]})
    names = rt['objects']
    check('fbx_has_lod0_1_2', all(any(n.split('.')[0].endswith(f'_LOD{lv}') for n in names) for lv in (0, 1, 2)), names)
    check('fbx_sockets', sorted(k.split('.')[0] for k in rt['sockets']) == sorted(S['sockets']), rt['sockets'])
    check('fbx_collision', cfg.get('no_collision') or (aid + '_Collision') in [n.split('.')[0] for n in names], cfg.get('no_collision') or 'collision mesh present')
    water = None
    if S.get('water_path') or S.get('water_cross'):
        water_fbx = exp / f'{aid}_water_{VER}.fbx'
        wobjs, wlen, wrun = export_water(aid, shift, fit, water_fbx)
        wrt = pl.fbx_roundtrip(water_fbx); wlo, whi = pl.eval_bounds([wobjs[0]])
        wtris = {f'LOD{lv}': sum(len(q.vertices) - 2 for q in o.data.polygons) for lv, o in wobjs.items()}
        check('water_is_its_own_fbx', water_fbx.exists() and not any('water' in n.lower() for n in names), {'water_file': water_fbx.name, 'body_objects_with_water': [n for n in names if 'water' in n.lower()]})
        check('water_fbx_reimport_dimensions', all(abs(a - b) < 2e-3 for a, b in zip(wrt['lod0_dimensions_m'], whi - wlo)), {'fbx': wrt['lod0_dimensions_m'], 'blend': [round(v, 4) for v in whi - wlo]})
        check('water_flow_uv_whole_metres', abs(wrun - max(wlen, 1)) < .1, {'path_length_m': round(wlen, 3), 'uv_v_length': wrun, 'note': 'a piece under 1 m still runs v 0..1, so the pattern joins its neighbours'})
        water = {'file': water_fbx.name, 'objects': sorted(o.name for o in wobjs.values()), 'triangles': wtris, 'origin': 'same as the body FBX', 'dimensions_m': [round(v, 4) for v in whi - wlo],
                 'uv': 'u 0..1 across the channel, v in metres downstream, whole metres per piece', 'path_length_m': round(wlen, 3), 'textures': 'none',
                 'unity_shader': 'YunJing/CreekFlowWater (apps/game/Assets/YunJing/Runtime/CreekRepair/CreekFlowWater.shader): moves on _Time, no script needed'}
    pl.ten_views(lod0, prev / 'turnaround', f'art/source/{KIT}/blend/{aid}_{VER}.blend')
    check('ten_views_rendered', len(list((prev / 'turnaround').glob('*.png'))) == 10, 'orthographic, framing asserted per view')
    shots = []
    for lv in (0, 1, 2):
        p = prev / f'_lod{lv}.png'; pl.persp_shot(list(S['lods'][lv].values()), p, samples=32); shots.append(p)
    _strip(shots, prev / f'{aid}_LOD_comparison.png'); [p.unlink() for p in shots]
    # quality-tiers-v1 section 4: same angle, LOD0 beside LOD1, Detail_* off
    shots = []
    for lv in (0, 1):
        p = prev / f'_nd{lv}.png'; pl.persp_shot([o for g, o in S['lods'][lv].items() if not g.startswith('Detail_')], p, samples=48); shots.append(p)
    _strip(shots, prev / f'{aid}_LOD0_LOD1_no_detail.png'); [p.unlink() for p in shots]
    pl.persp_shot(lod0, prev / f'{aid}_hero.png', samples=96)
    states = state_renders(aid, prev, lod0)
    if water:
        pl.persp_shot(lod0 + [wobjs[0]], prev / f'{aid}_with_water.png', samples=64)
        pl.persp_shot([wobjs[0]], prev / f'{aid}_water_only.png', samples=32)
        for o in wobjs.values(): o.hide_render = False
    for o in lod0: o.hide_render = False
    blend.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend / f'{aid}_{VER}.blend'))
    mats = sorted({m.name for g in S['lods'].values() for o in g.values() for m in o.data.materials})
    info = {
        'asset': aid, 'version': VER, 'minTier': cfg.get('minTier', 'standard'), 'detailObjects': sorted(f'{aid}_{g}' for g in S['lods'][0] if g.startswith('Detail_')), 'name_zh': cfg['zh'], 'slot': cfg['slot'], 'note': cfg['note'],
        'units': 'meters', 'front': '-Y (Blender)', 'up': '+Z (Blender); FBX exported Y-up, -Z forward, transforms baked',
        'origin': 'axle centre' if cfg.get('axle_origin') else 'bottom centre', 'dimensions_m': [round(v, 4) for v in dims], 'size_limit_m': cfg['limit'], 'pieces': pieces,
        'lods': lod_report, 'lod_totals': tot, 'lod_rule': 'LOD1 about 50%, LOD2 about 15% of LOD0 (small parts dropped first, then collapse decimate)',
        'materials': mats, 'textures': sorted(p.name for p in (exp / 'Textures').glob('*.png')), 'texture_size_px': cfg['tex'],
        'unity': {'pipeline': 'URP Lit', 'axes': 'imported with bakeAxisConversion: Unity local = (Blender x, z, y); the model front faces Unity -Z (seen in the captures)', 'BaseColor': f'{aid}_BaseColor.png', 'Normal': f'{aid}_Normal.png (OpenGL +Y)',
                  'MetallicSmoothness': f'{aid}_MetallicSmoothness.png (R metallic, A smoothness)',
                  'lod_group': 'objects end in _LOD0/_LOD1/_LOD2 under one root, so Unity builds a LODGroup on import',
                  'collision': f'{aid}_Collision: add a MeshCollider (convex off); hide its renderer'},
        'collision': bool(S.get('collision_obj')), 'collision_shapes': [[list(a), list(b)] for a, b in S.get('collision', [])],
        'sockets_blender_xyz': {k: [round(v, 4) for v in e.matrix_world.translation] for k, e in S['sockets'].items()},
        'sockets_fbx_reimport_xyz': rt['sockets'], 'states': cfg['states'], 'state_renders': states, 'fbx_objects': rt['objects'],
        'modeling_method': f'procedural mesh construction (art/source/{KIT}/); procedural shaders (cr_mats.py) baked to a UV atlas',
        'reference': f"art/references/{aid.split('_')[0]}/selected.png (AI three-view; proportions taken from the work pack's written sizes, not measured from the image)",
        'unity_import_verified': 'imported by Editor/CreekRepairModelCheck under Unity 6000.0.85f1 (the project pins 82f1); results in artifacts/creek-repair-unity/unity-verify-report.txt, not in this file',
    }
    if water: info['water'] = water
    if aid.startswith('CR09'):
        info['channel_interface'] = {'clear_width_m': .4, 'floor_top_z_m': .1, 'wall_top_z_m': .4, 'outer_width_at_port_m': .6, 'port_y_m': [-.25, .25], 'flow_axis': 'Y',
                                     'water_opening_when_open_m': .3, 'note': 'same numbers as B02/B03; fit against CR06 and CR08 is not tested because they are not built yet'}
    (exp / 'model_info.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
    val = {'asset': aid, 'checks': checks, 'all_pass': all(c['pass'] for c in checks), 'seconds': round(time.time() - t0),
           'not_checked': ['in-engine lighting (see the Unity report)']}
    (exp / 'validation.json').write_text(json.dumps(val, ensure_ascii=False, indent=2), encoding='utf-8')
    print('ASSET_COMPLETE', aid, 'all_pass=', val['all_pass'], [c['check'] for c in checks if not c['pass']], round(time.time() - t0), 's', flush=True)


def spec_checks(aid, check, pieces, dims, shift):
    if aid.startswith('CR09'):
        g = S['lods'][0]['Gate']; a, b = pl.eval_bounds([g])
        check('gate_is_separate_object', 'Gate' in pieces, list(pieces))
        check('open_top_within_0.9', b.z + .3 <= .9, {'closed_top_m': round(b.z, 4), 'open_top_m': round(b.z + .3, 4)})
        check('gate_keeps_groove_engagement', a.z + .3 < G9.TOP - .1, {'open_bottom_m': round(a.z + .3, 4), 'groove_top_m': G9.TOP})
        check('port_sockets_at_floor_0.1', all(abs(S['sockets'][k].matrix_world.translation.z - .1) < 1e-3 for k in ('Socket_PortFront', 'Socket_PortBack')),
              {k: [round(v, 4) for v in S['sockets'][k].matrix_world.translation] for k in ('Socket_PortFront', 'Socket_PortBack')})
    if aid == 'WM07_StoneBridge':
        slopes = [abs(GW.deck_z(y + .1) - GW.deck_z(y)) / .1 for y in [-6 + k * .1 for k in range(119)]]
        check('deck_slope_within_15_deg', max(slopes) <= math.tan(math.radians(15)), {'max_degrees': round(math.degrees(math.atan(max(slopes))), 2)})
    if aid == 'WM02_WaterWheel':
        check('wheel_diameter_4.6', abs(dims[1] - 4.6) < .02 and abs(dims[2] - 4.6) < .02, {'dims_m': [round(v, 3) for v in dims]})
    if aid == 'CR05_WorkShelter':
        need = {'Canopy', 'Bench', 'Crate', 'TeaBucket', 'Ladle', 'Bowl_01', 'Bowl_02', 'Bowl_03', 'Bowl_04'}
        check('independent_objects', need <= set(pieces), sorted(pieces))
        check('canopy_clears_1.75_m_head', pieces['Canopy']['min_z_local'] >= 1.75, {'canopy_min_z_m': pieces['Canopy']['min_z_local']})
    if aid == 'CR12_RankingBoard':
        need = {f'Slip_{i:02d}' for i in range(1, 13)}
        check('twelve_slips_separate', need <= set(pieces), sorted(pieces))
        check('tea_cup_separate', 'TeaCup' in pieces, list(pieces))
        check('slip_01_is_largest', all(pieces['Slip_01']['dims_m'][0] > pieces[k]['dims_m'][0] for k in need - {'Slip_01'}), {k: pieces[k]['dims_m'] for k in sorted(need)})


def state_renders(aid, prev, lod0):
    states = {}
    if aid.startswith('CR09'):
        g = S['lods'][0]['Gate']; z = g.location.z
        g.location.z = z + .3
        pl.persp_shot(lod0, prev / 'state_gate_open.png', direction=(.7, -1, .35), samples=64); states['gate_open'] = 'state_gate_open.png'
        g.location.z = z
    if aid == 'CR12_RankingBoard':
        keep = [o for n, o in S['lods'][0].items() if not n.startswith('Slip_')]
        pl.persp_shot(keep, prev / 'state_no_slips.png', direction=(.2, -1, .25), samples=48); states['no_slips'] = 'state_no_slips.png'
    return states


def _strip(paths, out):
    ims = [bpy.data.images.load(str(p)) for p in paths]
    w, h = ims[0].size
    arr = np.concatenate([np.array(i.pixels[:], np.float32).reshape(h, w, 4) for i in ims], axis=1)
    im = bpy.data.images.new(out.stem, w * len(ims), h, alpha=True); im.pixels.foreach_set(arr.ravel())
    im.filepath_raw = str(out); im.file_format = 'PNG'; im.save()


def preview(aid, out_dir, samples=24, res=900):
    """Quick look before the bake: procedural materials, five perspective views."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ti_mats.MAT_INFO.clear(); ti_core.reset_state(aid)
    cfg = ASSETS[aid]; P = cfg['palette'](); cfg['build'](P); pl.normalise()
    S['cut'].hide_render = True
    lo, hi = pl.eval_bounds(S['parts']); print('PREVIEW_DIMS', aid, [round(v, 3) for v in hi - lo], flush=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    tris = 0
    dg = bpy.context.evaluated_depsgraph_get()
    for o in S['parts']:
        e = o.evaluated_get(dg); m = e.to_mesh(); tris += sum(len(p.vertices) - 2 for p in m.polygons); e.to_mesh_clear()
    print('PREVIEW_TRIS', tris, flush=True)
    for name, d in (('front', (0, -1, .1)), ('side', (1, 0, .1)), ('back', (0, 1, .1)), ('three_quarter', (-1, -1.2, .5)), ('top', (.05, -.2, 1))):
        pl.persp_shot(S['parts'], out_dir / f'{aid}_{name}.png', direction=d, samples=samples, lens=70)


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    force = '--force' in argv; ids = [a for a in argv if a in ASSETS] or list(ASSETS)
    if '--preview' in argv:
        out = Path(argv[argv.index('--preview') + 1])
        for aid in ids: preview(aid, out)
    else:
        for aid in ids: run(aid, force)
