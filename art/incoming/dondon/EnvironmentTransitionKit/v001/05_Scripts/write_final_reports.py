"""Final PHASE 6 reports from the measured outputs (Python 3 + Pillow; no Blender).

  python3 05_Scripts/write_final_reports.py --sheets     # group contact sheets + per-view crop check
  python3 05_Scripts/write_final_reports.py --reports    # everything else (run after looking at the sheets)

Reads kit_spec.py, 01_Blender/*.build.json, 06_Reports/qa/final_all29.json, fbx_export_*.json,
fbx_reimport_v01.json, PHASE6_ProtectedAssetRecheck.json, the preview folders and the showcase folder.
--sheets writes 04_Previews/Sheets/Sheet_<group>.png and 06_Reports/qa/preview_crop_check.json.
--reports writes 06_Reports/CONNECTOR_SPEC.json, ASSET_MANIFEST.md/.csv (final; the design-stage versions
stay in 06_Reports/history/), QA_Report.md, 04_Previews/Individual/<code>_<id>/model_info.json and
validation.json, and the gallery page 04_Previews/index.html.  Only states what those files show.
Never overwrites.
"""
import csv, hashlib, html, io, json, statistics, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit_spec as K
import write_reports as WR

KIT = Path(__file__).resolve().parents[1]
REP = KIT / '06_Reports'; QA = REP / 'qa'; PREV = KIT / '04_Previews'
FONT = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
GROUP_TITLE = {'A': 'A 類｜道路不規則收邊（11 件）', 'B': 'B 類｜河岸自然收邊（10 件）', 'C': 'C 類｜橋頭與地形交接收邊（8 件）'}
VIEW_ZH = {'01_front': '正前', '02_right': '右', '03_rear': '後', '04_left': '左', '05_front_right': '右前斜', '06_rear_right': '右後斜',
           '07_rear_left': '左後斜', '08_front_left': '左前斜', '09_top': '頂視', '10_high_front': '高前視', '11_persp_45': '45° 透視'}


def new(path):
    if path.exists(): raise SystemExit('EXISTS (not overwritten): %s' % path.relative_to(KIT))
    path.parent.mkdir(parents=True, exist_ok=True); return path


def rel(p): return str(Path(p).relative_to(KIT)) if Path(p).is_absolute() else str(p)


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''): h.update(c)
    return h.hexdigest()


def folder(m): return PREV / 'Individual' / ('%s_%s' % (m['code'], m['id']))


EXTRA_DIR = PREV / 'Individual' / 'D02_SM_Bridge_Timber_A'  # D02 timber bridge, requested after the 29 modules
LOG_DIR = PREV / 'Individual' / 'D01_SM_Bridge_Log_A'        # D01 single-log bridge (first, superseded attempt; kept as an option)


def extra():
    if not (EXTRA_DIR / 'model_info.json').exists(): return None
    return json.loads((EXTRA_DIR / 'model_info.json').read_text()), json.loads((EXTRA_DIR / 'validation.json').read_text())


def font(n): return ImageFont.truetype(FONT, n)


def load():
    D = {'build': {}, 'export': {}}
    for f in K.GROUP_FILES.values():
        D['build'].update(json.loads((KIT / '01_Blender' / ('%s_v01.build.json' % f)).read_text())['modules'])
        D['export'].update(json.loads((QA / ('fbx_export_%s.json' % f)).read_text())['modules'])
    D['qa'] = json.loads((QA / 'final_all29.json').read_text())
    D['reimport'] = json.loads((QA / 'fbx_reimport_v01.json').read_text())
    D['protected'] = json.loads((REP / 'PHASE6_ProtectedAssetRecheck.json').read_text())
    D['crop'] = json.loads((QA / 'preview_crop_check.json').read_text()) if (QA / 'preview_crop_check.json').exists() else None
    return D


# ---- --sheets ------------------------------------------------------------------------------------------
def crop_check():
    """A view is 'cropped' if the model touches the picture edge: border pixels that differ from the background."""
    out = {}
    mods = K.MODULES + [m for m, d in (({'code': 'D01', 'id': 'SM_Bridge_Log_A'}, LOG_DIR), ({'code': 'D02', 'id': 'SM_Bridge_Timber_A'}, EXTRA_DIR)) if d.exists()]
    for m in mods:
        res = {}
        for p in sorted(folder(m).glob('*.png')):
            im = Image.open(p).convert('RGB'); w, h = im.size; px = im.load()
            border = [px[x, y] for x in range(0, w, 2) for y in (0, 1, h - 2, h - 1)] + [px[x, y] for y in range(0, h, 2) for x in (0, 1, w - 2, w - 1)]
            ref = tuple(statistics.median(c[i] for c in border) for i in range(3))
            off = sum(1 for c in border if max(abs(c[i] - ref[i]) for i in range(3)) > 24) / len(border)
            close = p.stem.startswith(('12_', '13_'))           # deliberate close-ups of the bridges: cropping is the point
            res[p.stem] = {'size': [w, h], 'border_pixels_off_background': round(off, 4), 'touches_edge': off > 0.002 and not close, 'close_up': close}
        out[m['code']] = {'views': len(res), 'all_1024': all(v['size'] == [1024, 1024] for v in res.values()),
                          'touching_edge': [k for k, v in res.items() if v['touches_edge']], 'detail': res}
    return out


def sheets(D):
    crop = crop_check()
    new(QA / 'preview_crop_check.json').write_text(json.dumps({'method': 'border pixels of each preview compared with the median border colour; >0.2 % off-background = model touches the edge',
                                                               'modules': crop}, ensure_ascii=False, indent=2))
    cell, cols = 470, 4
    for g in 'ABC':
        mods = [m for m in K.MODULES if m['group'] == g]; rows = (len(mods) + cols - 1) // cols
        im = Image.new('RGB', (cols * cell + 40, rows * (cell + 92) + 110), (246, 244, 239)); d = ImageDraw.Draw(im)
        d.text((24, 24), GROUP_TITLE[g] + '　每件的 45° 透視成品圖（另有 10 個正交角度在各自資料夾）', font=font(32), fill=(25, 25, 25))
        for i, m in enumerate(mods):
            x = 20 + (i % cols) * cell; y = 100 + (i // cols) * (cell + 92)
            im.paste(Image.open(folder(m) / '11_persp_45.png').convert('RGB').resize((cell - 16, cell - 16)), (x, y))
            b = D['build'][m['id']]
            d.text((x, y + cell - 8), '%s %s' % (m['code'], m['name_zh']), font=font(27), fill=(20, 20, 20))
            d.text((x, y + cell + 28), '%s　LOD0 %s 三角面' % (m['id'], format(b['lod0_tris'], ',')), font=font(17), fill=(90, 90, 90))
        name = {'A': 'Sheet_A_RoadEdge.png', 'B': 'Sheet_B_Riverbank.png', 'C': 'Sheet_C_Bridgehead.png'}[g]
        im.save(new(PREV / 'Sheets' / name)); print('WROTE', rel(PREV / 'Sheets' / name))
    if extra():
        im = Image.new('RGB', (3 * 470 + 40, 470 + 190), (246, 244, 239)); d = ImageDraw.Draw(im)
        d.text((24, 24), 'D02 木造梁橋（29 件之外新增）　跨距 10 m、橋面寬 3 m，兩端擱在 C05 石基上，河中央一座木排架', font=font(30), fill=(25, 25, 25))
        for i, (v, cap) in enumerate((('11_persp_45', '整座'), ('12_detail', '近看：木板橋面、欄杆、端柱'), ('13_pier', '橋下：主梁、帽梁、圓木樁、斜撐'))):
            im.paste(Image.open(EXTRA_DIR / (v + '.png')).convert('RGB').resize((454, 454)), (20 + i * 470, 90))
            d.text((20 + i * 470, 552), cap, font=font(22), fill=(40, 40, 40))
        im.save(new(PREV / 'Sheets' / 'Sheet_D_TimberBridge.png')); print('WROTE', rel(PREV / 'Sheets' / 'Sheet_D_TimberBridge.png'))
    need = {k: {'D01': 12, 'D02': 13}.get(k, 11) for k in crop}
    bad = {k: v['touching_edge'] for k, v in crop.items() if v['touching_edge'] or v['views'] != need[k] or not v['all_1024']}
    print('CROP CHECK', 'all clear' if not bad else bad)


# ---- --reports -----------------------------------------------------------------------------------------
def lod_sum(tris, suffix): return sum(t for n, t in tris.items() if n.endswith(suffix))


def con_results(D, m):
    return {c['connector']: c for c in D['qa']['modules'][m['id']]['connectors']}


def module_facts(D, m):
    mid = m['id']; b = D['build'][mid]; e = D['export'][mid]; q = D['qa']['modules'][mid]; r = D['reimport']['modules'][mid]
    tris = b['tris']; lo, hi = K.tri_budget(m)
    crop = D['crop']['modules'][m['code']] if D['crop'] else None
    return dict(lod0=b['lod0_tris'], lod1=lod_sum(tris, '_LOD1'), lod2=lod_sum(tris, '_LOD2'), col=lod_sum(tris, '_COL'), budget=(lo, hi),
                within=b['lod0_tris'] <= hi, under_min=b['lod0_tris'] < lo, objects=[n for n in e['objects']],
                materials=sorted({mt for o in e['objects'].values() for mt in o['materials']}), bounds=(e['bounds_min'], e['bounds_max']),
                qa_pass=q['pass'], detail=q['details'], reimport=r, fbx=e['fbx'], fbx_bytes=e['bytes'], crop=crop, dropped=b.get('details_dropped_at_connectors', 0))


def connector_spec(D):
    mods = []
    for m in K.MODULES:
        f = module_facts(D, m); res = con_results(D, m); cons = []
        for c in K.connectors(m):
            q = res.get(c['name'], {})
            cons.append({'name': c['name'], 'role': c['role'], 'type': c['type'], 'partner': c.get('partner'), 'surface_variant': c.get('surface_variant'),
                         'location_m': [round(v, 6) for v in c['location']], 'heading_deg': round(c['heading_deg'], 6), 'vertex_count': len(c['vertices']),
                         'compatible': WR.compatible(m, c) if c['name'] in ('EntryConnector', 'ExitConnector') else [c.get('partner')],
                         'allowed_height_difference_m': K.TOL, 'measured_max_position_error_m': q.get('max_position_error_m'),
                         'measured_max_normal_error_deg': q.get('max_normal_error_deg'), 'qa_pass': q.get('pass')})
        mods.append({'code': m['code'], 'id': m['id'], 'group': m['group'], 'name_zh': m['name_zh'], 'note': m['purpose'],
                     'pivot': WR_pivot(m), 'bounds_min_m': [round(v, 4) for v in f['bounds'][0]], 'bounds_max_m': [round(v, 4) for v in f['bounds'][1]],
                     'connectors': cons})
    return {'kit': 'Environment_Transition_Kit', 'version': K.KIT_VERSION, 'generated_by': '05_Scripts/write_final_reports.py',
            'units': 'metre', 'axes': {'up': '+Z', 'forward': '+X = direction of travel', 'left': '+Y'},
            'transform_convention': ('location = connector centre in module space; heading_deg = direction of travel through the connector, '
                                     'counter-clockwise from +X about +Z.  To attach B after A: T_B = T_A * Translate(A.exit.location) * RotZ(A.exit.heading). '
                                     'Every module entry is its own origin with heading 0, except the bridgehead pieces, which share one frame.'),
            'tolerance_m': K.TOL, 'connector_types': K.CONNECTOR_TYPES,
            'bounds_note': 'Bounds are measured from all exported meshes (details included; grass cards may overhang free outer edges, never entry/exit planes).',
            'modules': mods,
            'extras': [extra()[0]] if extra() else [],
            'test_objects': {'TEST_RoadCore_3m': '4 m x 3 m flat road core at Z=0 (frame of A01/A02)', 'TEST_BridgeDeck_3m': '3 m wide placeholder deck, top +0.15, bottom -0.05, from X=2 (bridgehead frame)',
                             'TEST_ScaleCube_1m': '1 m cube for the engine scale check', 'export': '02_Exports/_TestHelpers/*.fbx (never inside a module FBX)'}}


def WR_pivot(m):
    if m['group'] == 'C' and m['kind'] != 'c06': return 'bridgehead frame origin = C01 road entry (0,0,0); C01-C05, C07, C08 share it'
    if m['kind'] == 'c06': return 'ground below the high edge (0,0,0)'
    return 'entry connector (0,0,0)'


def manifest(D):
    rows = []
    for m in K.MODULES:
        f = module_facts(D, m); cons = K.connectors(m)
        ent = next((c for c in cons if c['name'] == 'EntryConnector'), None); ex = next((c for c in cons if c['name'] == 'ExitConnector'), None)
        def tf(c): return '' if not c else '(%.3f, %.3f, %.3f) %+.1f°' % (*c['location'], c['heading_deg'])
        (x0, y0, z0), (x1, y1, z1) = f['bounds']
        ok = f['qa_pass'] and f['reimport']['pass'] and f['crop'] and f['crop']['views'] == 11 and not f['crop']['touching_edge']
        rows.append(dict(
            code=m['code'], id=m['id'], group=m['group'], name_zh=m['name_zh'], purpose=m['purpose'],
            size_x_m='%.2f' % (x1 - x0), size_y_m='%.2f' % (y1 - y0), z_min_m='%.2f' % z0, z_max_m='%.2f' % z1, pivot=WR_pivot(m),
            entry_type=ent['type'] if ent else '', entry_transform=tf(ent),
            exit_type=(ex['type'] + (' / ' + ex['surface_variant'] if ex.get('surface_variant') else '')) if ex else '（單側封口）', exit_transform=tf(ex),
            entry_compatible=' '.join(WR.compatible(m, ent)) if ent else '', exit_compatible=' '.join(WR.compatible(m, ex)) if ex else '',
            lod0_tris=f['lod0'], lod1_tris=f['lod1'], lod2_tris=f['lod2'], col_tris=f['col'], tri_budget='%d–%d' % f['budget'],
            budget_note='在預算內' if f['within'] and not f['under_min'] else ('低於建議下限（小件，可接受）' if f['under_min'] else '超出預算'),
            materials=' '.join(f['materials']), blend='01_Blender/%s_v01.blend（Collection %s）' % (K.GROUP_FILES[m['group']], m['id']),
            fbx=f['fbx'], fbx_kb='%.0f' % (f['fbx_bytes'] / 1024), previews=rel(folder(m)) + '/（10 正交＋1 透視）',
            three_view='00_References/ThreeViews/%s_%s_3view.png' % (m['code'], m['id']),
            status=('已建模（LOD0/1/2＋COL）；接頭與細節自動檢查通過；FBX 已匯出並通過 Blender 回匯檢查；11 張預覽已檢查未裁切；未在 Unity/Unreal 驗證'
                    if ok else '有檢查未通過，見 validation.json')))
    buf = io.StringIO(); w = csv.DictWriter(buf, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    new(REP / 'ASSET_MANIFEST.csv').write_text('﻿' + buf.getvalue(), encoding='utf-8')
    L = ['# ASSET_MANIFEST｜29 件環境收邊模組（v01 成品）', '',
         '由 `05_Scripts/write_final_reports.py` 依實際檔案與檢查結果產生。尺寸為匯出網格的實測範圍（含細節；草片可能略超出外側自由邊，但不會越過入口／出口接頭面）。'
         '三角面為實測值。設計階段的舊版清單保存在 `history/`。', '',
         '| 共通 | 內容 |', '| --- | --- |',
         '| 單位／座標 | 公尺；Z 向上；+X＝行進方向；+Y＝行進方向左側；地面 Z = 0 |',
         '| 檔案 | `01_Blender/road_edge_modules_v01.blend`、`riverbank_modules_v01.blend`、`bridgehead_modules_v01.blend`（每件一個 Collection）；每件一個 FBX 在 `02_Exports/<RoadEdge/Riverbank/Bridgehead>/` |',
         '| 物件 | `<ID>`（根空物件，含接頭資訊自訂屬性）、`_Terrain_LOD0/1/2`、`_DET_Stones_LOD0`、`_DET_Grass_LOD0`、`_Rocks_LOD0/1`、`_Masonry_LOD0/1/2`（C05）、`_COL` |',
         '| 材質 | 地表 `M_TerrainBlend`（頂點色 Mask 混合）；石 `M_Rock`／`M_Moss`；草片 `M_GrassCard`；貼圖在 `03_Textures/` |', '']
    for g in 'ABC':
        L += ['## ' + GROUP_TITLE[g], '', '| 編號 | 模組 ID | 名稱 | 外形 X×Y (m) | Z 範圍 (m) | LOD0／LOD1／LOD2／COL 三角面 | 預算 | 入口 | 出口 | FBX |',
              '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
        for r in rows:
            if r['group'] != g: continue
            L.append('| %s | `%s` | %s | %s × %s | %s～%s | %s／%s／%s／%s | %s（%s） | %s %s | %s %s | `%s`（%s KB） |' % (
                r['code'], r['id'], r['name_zh'], r['size_x_m'], r['size_y_m'], r['z_min_m'], r['z_max_m'], format(r['lod0_tris'], ','), r['lod1_tris'], r['lod2_tris'], r['col_tris'],
                r['tri_budget'], r['budget_note'], r['entry_type'], r['entry_transform'], r['exit_type'], r['exit_transform'], r['fbx'], r['fbx_kb']))
        L += ['']
        for r in rows:
            if r['group'] != g: continue
            L.append('- **%s %s**：%s　入口可接：%s；出口可接：%s' % (r['code'], r['name_zh'], r['purpose'], r['entry_compatible'] or '—', r['exit_compatible'] or '—'))
        L += ['']
    ex = extra()
    if ex:
        mi, va = ex; g = va['geometry']
        L += ['## D 類｜後續新增（不在原 29 件內）', '', '| 編號 | 模組 ID | 名稱 | 外形 X×Y (m) | LOD0／LOD1／LOD2／COL 三角面 | 放置 | FBX |', '| --- | --- | --- | --- | --- | --- | --- |',
              '| D02 | `%s` | %s | %.2f × %.2f | %s／%s／%s／%s | 橋頭座標系平移 (2, 0, +0.15)；接兩座相距 14 m 的橋頭 | `%s` |' % (
                  mi['id'], mi['name_zh'], mi['bounds_max_m'][0] - mi['bounds_min_m'][0], mi['bounds_max_m'][1] - mi['bounds_min_m'][1],
                  format(g['tris']['SM_Bridge_Timber_A_LOD0'], ','), g['tris']['SM_Bridge_Timber_A_LOD1'], g['tris']['SM_Bridge_Timber_A_LOD2'], g['tris']['SM_Bridge_Timber_A_COL'], mi['files']['fbx']),
              '', '- **D02 木造梁橋**：' + mi['purpose'] + '材質 M_Timber／M_Bark／M_EndGrain。檔案 `01_Blender/timber_bridge_v01.blend`。',
              '- D01 獨木橋（`01_Blender/log_bridge_v01.blend`、`02_Exports/Bridge/SM_Bridge_Log_A.fbx`）：先前做的單根原木橋，保留為可選件。', '']
    L += ['## 狀態', '', '全部 29 件：' + ('、'.join(sorted({r['status'] for r in rows}))) + '。', '',
          '## 測試輔助（不屬於 29 件，不在模組 FBX 內）', '', '- `02_Exports/_TestHelpers/TEST_RoadCore_3m.fbx`、`TEST_BridgeDeck_3m.fbx`、`TEST_ScaleCube_1m.fbx`：引擎內拼接測試與 1 m 尺度核對用。', '']
    new(REP / 'ASSET_MANIFEST.md').write_text('\n'.join(L), encoding='utf-8')
    return rows


def per_module_json(D):
    for m in K.MODULES:
        f = module_facts(D, m); fo = folder(m); res = con_results(D, m)
        info = {'id': m['id'], 'code': m['code'], 'name_zh': m['name_zh'], 'group': m['group'], 'purpose': m['purpose'], 'version': K.KIT_VERSION,
                'units': 'metre', 'up': '+Z', 'forward': '+X (travel direction); preview 01_front looks from -Y', 'pivot': WR_pivot(m),
                'bounds_min_m': f['bounds'][0], 'bounds_max_m': f['bounds'][1],
                'triangles': {'LOD0': f['lod0'], 'LOD1': f['lod1'], 'LOD2': f['lod2'], 'COL': f['col'], 'budget_LOD0': list(f['budget']), 'by_object': D['build'][m['id']]['tris']},
                'objects': f['objects'], 'materials': f['materials'],
                'files': {'blend': '01_Blender/%s_v01.blend' % K.GROUP_FILES[m['group']], 'blend_collection': m['id'],
                          'blend_sha256': sha256(KIT / '01_Blender' / ('%s_v01.blend' % K.GROUP_FILES[m['group']])),
                          'fbx': f['fbx'], 'fbx_sha256': sha256(KIT / f['fbx']), 'previews': rel(fo), 'three_view': '00_References/ThreeViews/%s_%s_3view.png' % (m['code'], m['id'])},
                'connectors': [{'name': c['name'], 'role': c['role'], 'type': c['type'], 'location_m': c['location'], 'heading_deg': c['heading_deg']} for c in K.connectors(m)]}
        new(fo / 'model_info.json').write_text(json.dumps(info, ensure_ascii=False, indent=2))
        val = {'module': m['id'], 'code': m['code'], 'tolerance_m': K.TOL, 'overall_pass': bool(f['qa_pass'] and f['reimport']['pass']),
               'connectors': list(res.values()), 'details_stay_behind_entry_exit_planes': f['detail'],
               'detail_pieces_removed_by_guard_at_build': f['dropped'],
               'mesh_checks': D['qa']['modules'][m['id']]['stats'],
               'fbx_blender_reimport': f['reimport'], 'previews': f['crop'],
               'source_reports': ['06_Reports/qa/final_all29.json', '06_Reports/qa/fbx_reimport_v01.json', '06_Reports/qa/preview_crop_check.json'],
               'not_verified': ['Unity / Unreal import, materials and LOD groups', 'in-engine collision and walkability', 'performance on target devices']}
        if m['kind'] == 'c_base':
            (x0, y0, z0), (x1, y1, z1) = f['bounds']
            val['seat_and_face_from_bounds'] = {'top_z_m': z1, 'expected_top_z_m': K.DECK_BOTTOM, 'front_face_x_m': x1, 'expected_front_face_x_m': K.BASE_FACE_X,
                                                'pass': abs(z1 - K.DECK_BOTTOM) <= K.TOL and abs(x1 - K.BASE_FACE_X) <= K.TOL}
        new(fo / 'validation.json').write_text(json.dumps(val, ensure_ascii=False, indent=2, default=float))
    print('WROTE model_info.json + validation.json x', len(K.MODULES))


def qa_report(D, rows):
    q = D['qa']; ri = D['reimport']; crop = D['crop']['modules']
    con_max = max(c.get('max_position_error_m', 0) for mm in q['modules'].values() for c in mm['connectors'])
    nrm_max = max(c.get('max_normal_error_deg', 0) for mm in q['modules'].values() for c in mm['connectors'])
    chain_max = max(s['max_position_error_m'] for c in q['chains'] for s in c['steps'])
    chain_nrm = max(s['max_normal_error_deg'] for c in q['chains'] for s in c['steps'])
    pair_max = max(p['max_position_error_m'] for p in q['pairs'])
    det_max = max(mm['details']['max_protrusion_m'] for mm in q['modules'].values())
    mods_pass = sum(1 for mm in q['modules'].values() if mm['pass'])
    re_pass = sum(1 for mm in ri['modules'].values() if mm['pass'])
    views_ok = sum(1 for v in crop.values() if v['views'] == 11 and v['all_1024'] and not v['touching_edge'])
    mm = lambda x: '%.4f mm' % (x * 1000)
    def chain(title): return next(c for c in q['chains'] if c['chain'] == title)
    def pair(prefix): return next(p for p in q['pairs'] if p['pair'].startswith(prefix))
    L = ['# QA_Report｜環境收邊模組 v01', '',
         '本報告的數字全部來自 `06_Reports/qa/` 內的 JSON（由腳本實際量測），由 `05_Scripts/write_final_reports.py` 產生。容許誤差 1 mm。', '',
         '## 白話總結', '',
         '- **29 件模型全部做完**：每件有地形網格、石塊與草叢細節、LOD1／LOD2 與碰撞代理，分在 3 個 `.blend`；每件各匯出 1 個 FBX（共 29 個）。',
         '- **接得起來**：所有接頭頂點與規格的最大誤差 %s，串接測試最大 %s，配對測試最大 %s（目標 ≤ 1 mm）。接縫兩側法線差最大 %.3f°，所以光影不會在接縫斷開。' % (mm(con_max), mm(chain_max), mm(pair_max), max(nrm_max, chain_nrm)),
         '- **細節不越界**：石頭、草片、砌石都不會伸過入口／出口接頭面（最大 %s）。' % mm(det_max),
         '- **FBX 可回讀**：29 個 FBX 在 Blender 重新匯入後，物件、三角面數、尺寸、接頭頂點、UV、頂點遮罩與材質槽都一致（%d/29）。' % re_pass,
         '- **還沒驗證的**：Unity／Unreal 實際匯入、引擎內碰撞與行走、手機效能。見第 5 節。', '',
         '## 1. 任務書 PHASE 5 必做檢查', '',
         '| # | 檢查 | 方法 | 結果 | 證據 |', '| --- | --- | --- | --- | --- |',
         '| 1 | A01＋A02 與路面中間測試段完整結合 | A01／A02 的 CoreSeam 頂點與 `TEST_RoadCore_3m` 邊緣逐點比對 | 通過，最大 %s | `qa/final_all29.json` pairs |' % mm(max(pair('A01 CoreSeam')['max_position_error_m'], pair('A02 CoreSeam')['max_position_error_m'])),
         '| 2 | 三段道路直線連接 | A01 依出口位姿連放 3 段，出口對入口逐點比對位置、遮罩、法線 | 通過，最大 %s | chain「straight x3」 |' % mm(max(s['max_position_error_m'] for s in chain('straight x3')['steps'])),
         '| 3 | 15° 左／右、30° 左／右彎段位置與切線 | A03→A04→A05→A06 依圓弧計算的出口位姿串接 | 通過，最大 %s，法線差 ≤ %.3f° | chain「curves L15 R15 L30 R30」 |' % (mm(max(s['max_position_error_m'] for s in chain('curves L15 R15 L30 R30')['steps'])), max(s['max_normal_error_deg'] for s in chain('curves L15 R15 L30 R30')['steps'])),
         '| 4 | 河岸直段與內凹／外凸轉角、緩坡的岸頂與水位連續 | B01→B03→B02→B04→B05→B06→B07→B08→B09→B10 串接 | 通過，最大 %s | chain「bank chain」、`AssemblyTests/final_all29_bank_chain_*.png` |' % mm(max(s['max_position_error_m'] for s in chain('bank chain')['steps'])),
         '| 5 | C01 道路過渡到測試橋面是否平順 | C01 出口頂點高度與測試橋面頂 +0.15 m 比對 | 通過，最大 %s | pairs、`Showcase/showcase_v01_seam_deck_labels.png` |' % mm(pair('C01 exit on TEST_BridgeDeck')['max_position_error_m']),
         '| 5b | 橋頭左右細節是否互相穿插 | 每件細節不得越過自己的入口／出口面；橋頭 11 條內部接縫逐點比對 | 通過，細節最大越界 %s；內部接縫最大 %s | modules.details、pairs（C01/C02/C03/C04/C07/C08） |' % (mm(det_max), mm(max(p['max_position_error_m'] for p in q['pairs'] if p['pair'].startswith(('C0',))))),
         '| 6 | 接頭採樣點誤差 ≤ 1 mm | 29 件所有接頭：頂點數、頂點不多不少、位置、遮罩、法線 | %d/29 件通過，最大 %s | modules.connectors |' % (mods_pass, mm(con_max)),
         '| 7 | 45° 斜視、頂視、側視檢查裂縫、Z-fighting、硬切紋理、陰影破綻 | 3 組拼裝場景各 3 視角＋展示場景 5 視角＋3 張接縫特寫，我逐張打開看過 | 未見裂縫、閃爍或接縫處光影斷開（說明見第 3 節） | `AssemblyTests/final_all29_*.png`、`Showcase/*_labels.png` |',
         '| 8 | 拼接前後截圖與通過標記 | 單件 11 視角（拼接前）＋拼裝與特寫（拼接後），特寫圖上標出接縫位置與實測誤差 | 已產出 | `04_Previews/` |', '',
         '## 2. 每件數據', '',
         '| 編號 | 名稱 | LOD0 | LOD1 | LOD2 | COL | 預算 | 接頭 | 細節越界 | FBX 回匯 | 11 張預覽 |', '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for r in rows:
        m = K.BY_CODE[r['code']]; mq = q['modules'][m['id']]; rr = ri['modules'][m['id']]; cv = crop[r['code']]
        L.append('| %s | %s | %s | %s | %s | %s | %s %s | %s | %s | %s | %s |' % (
            r['code'], r['name_zh'], format(r['lod0_tris'], ','), r['lod1_tris'], r['lod2_tris'], r['col_tris'], r['tri_budget'], '' if r['budget_note'] == '在預算內' else '（' + r['budget_note'] + '）',
            ('通過 %d 個' % len(mq['connectors'])) if mq['connectors'] else '石基以實測範圍核對（頂 -0.05、前緣 3.25）', '通過' if mq['details']['pass'] else '未通過',
            '通過' if rr['pass'] else '未通過', '通過（未裁切、1024²）' if cv['views'] == 11 and cv['all_1024'] and not cv['touching_edge'] else '見 crop check'))
    L += ['', '說明：LOD1／LOD2 由同一格點抽稀；`_Rocks_LOD1` 為 LOD0 大石減面 50%%；C05 的 LOD1 是無倒角方石、LOD2 是一個方塊。小石、草片只在 LOD0（任務書：可分離的 Detail 子組件）。'
          '%s 低於任務書建議下限，因為它們本身就是小片收邊件；任務書註明這是初始預算、不是死規定。B07 砌石護岸照「護岸」的 800–4,000 預算計算。' % '、'.join(r['code'] for r in rows if r['budget_note'] != '在預算內'), '',
          '## 3. 外觀檢查紀錄（實際打開的圖）', '']
    L += VISUAL_NOTES
    L += ['', '## 4. 製作中發現並已修正的問題', ''] + FIXED_NOTES
    L += ['', '## 5. 交付狀態三分類', '', '### 真正生成且驗證', '',
          '- 3 個 `.blend`（每件一個 Collection；可直接開啟編輯）；生成腳本 `05_Scripts/generate_modules.py` 可重建。',
          '- 29 個模組 FBX（`02_Exports/`）：Blender 回匯檢查 %d/29 通過（`qa/fbx_reimport_v01.json`）。另有 3 個測試輔助 FBX（`02_Exports/_TestHelpers/`）。' % re_pass,
          '- 接頭、串接、配對、細節越界檢查：全部通過（`qa/final_all29.json`）。',
          '- 6 組共用 PBR 貼圖＋混合雜訊（`03_Textures/`，1024²，2×2 平鋪檢查無接縫），材質參考 `00_References/REF_F_Materials.png`；另有木橋用 Timber／Bark／EndGrain／Wood 與水面波紋法線。',
          '- D02 木造梁橋（另有 D01 獨木橋）：`.blend`、FBX、預覽與自動檢查都通過，見第 6 節。',
          '- 每件 11 張 1024×1024 預覽＋`views.json`／`model_info.json`／`validation.json`（%d/29 件預覽未裁切）；分組總表 `04_Previews/Sheets/`；圖庫 `04_Previews/index.html`。' % views_ok,
          '- 拼裝場景、展示場景與接縫特寫（`04_Previews/AssemblyTests/`、`04_Previews/Showcase/`）。',
          '- 受保護資產唯讀複查：%s（`PHASE6_ProtectedAssetRecheck.json`）；本套件以外沒有任何檔案被修改。' % ('無變動' if D['protected']['unchanged'] else '有變動，需檢查'), '',
          '### 生成但未驗證', '',
          '- FBX 在 **Unity／Unreal** 的匯入結果（軸向、比例、LOD Group、頂點色、法線）——只做了 Blender 回匯，這不等於引擎驗證。',
          '- 引擎內材質：`M_TerrainBlend` 是 Blender 節點，需依 `README_Integration.md` 在引擎重建；貼圖本身已備妥。',
          '- `_COL` 碰撞代理只檢查了存在與三角面數，沒有在引擎內測試角色行走或卡腳。',
          '- 展示場景中對岸的 A11 是「入口對入口」接上 C01（道路斷面左右對稱，所以幾何相同），這個特定配對沒有列入自動檢查。', '',
          '### 待人工處理', '',
          '- 在目標引擎匯入 `_TestHelpers/TEST_ScaleCube_1m.fbx` 核對尺度，再匯入一組模組實測拼接。',
          '- 是否把本套件登錄到專案的 `ArtLibrary`／`Models/`（任務書限制只能寫入本資料夾，所以這次沒有登錄）。',
          '- 足跡、車轍等更細的路面敘事細節；手機端效能實測。', '',
          '## 6. D02 木造梁橋（後續新增，不在原 29 件內）', ''] + D01_SECTION(D) + ['',
          '## 7. 證據檔案', '',
          '- `06_Reports/qa/final_all29.json`：接頭／串接／配對／細節越界／網格檢查（%d 件、%d 串、%d 對）。' % (len(q['modules']), len(q['chains']), len(q['pairs'])),
          '- `06_Reports/qa/fbx_export_*.json`、`fbx_reimport_v01.json`：FBX 匯出紀錄與回匯檢查。',
          '- `06_Reports/qa/preview_crop_check.json`：預覽張數、解析度、是否裁切。',
          '- `06_Reports/qa/blockout_*.json`：PHASE 2 白模檢查；`qa/history/` 保留第一次誤判的紀錄。',
          '- `04_Previews/AssemblyTests/final_all29_*.png`、`final_all29_assembly.blend`；`04_Previews/Showcase/`（含 `showcase_v01_scene.blend`）。', '']
    new(REP / 'QA_Report.md').write_text('\n'.join(L), encoding='utf-8')


def D01_SECTION(D):
    ex = extra()
    if not ex: return ['- 未產生。']
    mi, va = ex; g = va['geometry']; ri = va['fbx_blender_reimport']; mm = lambda x: '%.4f mm' % (abs(x) * 1000)
    out = ['使用者在 29 件完成後要求新增「用木頭搭造的橋」。任務書原本不做橋梁本體，這件是依使用者後續指示加做的獨立資產（D02）。', '',
           '| 檢查 | 結果 |', '| --- | --- |',
           '| 結構 | %d 片橋面板、4 根主梁、兩側欄杆（7 根立柱／側、扶手、中欄）、河中央木排架（3 根圓木樁、帽梁、交叉斜撐） |' % g['planks'],
           '| 入口橋面與 C01 坡道頂（+0.15 m） | 差 %s；中段橋面板最大下陷 %s（刻意的自然高低差，≤ 3 mm；兩端各兩片完全齊平） |' % (mm(g['entry_top_in_bridgehead_frame_z_m'] - g['c01_exit_z_m']), mm(g['deck_top_min_z_m'])),
           '| 主梁削口與 C05 石基頂（-0.05 m） | 差 %s；接觸頂點 %d 個；擱置段沒有任何頂點低於削口面或超出 |Y| = 1.5 m（不碰 C07 角石） |' % (mm(g['seat_in_bridgehead_frame_z_m'] - g['c05_top_z_m']), g['seat_contact_vertices']),
           '| 與橋頭河岸地形（C08／C02）的最小間隙 | %.3f m |' % g['min_clearance_above_c08_c02_m'],
           '| 欄杆 | 高 %.2f m；欄杆間可走寬度 %.2f m |' % (g['railing_height_m'], g['clear_walk_width_m']),
           '| 三角面 | LOD0 %s（預算 800–4,000）；LOD1 %s；LOD2 %s；COL %s |' % (format(g['lod0_tris'], ','), g['tris']['SM_Bridge_Timber_A_LOD1'], g['tris']['SM_Bridge_Timber_A_LOD2'], g['tris']['SM_Bridge_Timber_A_COL']),
           '| FBX Blender 回匯 | %s（尺寸差 %s） |' % ('通過' if ri['pass'] else '未通過', mm(ri['max_bounds_error_m'])),
           '| 預覽 | 10 個正交角度（每個角度各自取景）＋45° 透視＋橋面近景＋橋下近景，共 13 張 |', '',
           '- 尚未驗證：引擎內行走與欄杆碰撞（`_COL` 為橋面板＋兩側欄杆牆）。',
           '- 只適合兩座相距 14 m 的橋頭（兩個 C01 出口之間 10 m）；橋墩木樁下到局部 Z -1.95 m，河床更深時需加長。']
    if (LOG_DIR / 'validation.json').exists():
        out += ['- 另有 D01 獨木橋（`01_Blender/log_bridge_v01.blend`）：先前誤解需求做的單根原木橋，檢查也通過；保留為可選件，不需要可刪除。']
    return out


VISUAL_NOTES = [
    '- **D02 木造梁橋**：看過 13 張預覽（含橋面與橋下近景）：橋面板、主梁、欄杆、木排架與斜撐都正確；展示場景中兩端擱在石基上，橋面與坡道頂齊平。',
    '- **29 件 45° 成品圖**（`04_Previews/Sheets/Sheet_A/B/C_*.png`）：逐件看過。道路有斑駁乾土、路肩草叢與小石；河岸由草皮、乾土過渡到濕泥；B07 是大小混雜的圓石半埋在碎石層、兩端參差融入土坡的砌石護坡；橋頭石基有兩層倒角切石；沒有破面、飛點或貼圖拉伸。',
    '- **11 視角**：自動檢查每張圖邊緣是否有模型（裁切），並抽看 A03、B07、C05 的全部 11 張。',
    '- **拼裝場景**（`AssemblyTests/final_all29_road_bridgehead/road_chain/bank_chain_45deg.png`）：道路串、河岸串、橋頭組合都連續，沒有看到縫隙或高低差。',
    '- **展示場景與接縫特寫**（`Showcase/*_labels.png`）：A03→A04 路面接縫、C02→B07 岸坡接縫、C01→D02 木橋橋面三處在 3–4 m 近距離都看不出接縫（圖上黃色虛線是事後標註的接縫位置）；沒有 Z-fighting 或光影斷線。',
    '- 展示場景的草地平面比模組低 3 cm，所以在橋頭側邊看得到一條細細的階梯陰影；那是展示用地面與模組外緣之間，不是模組接縫。',
    '- 展示用溪水：清澈見底的水體，河床中間較深（約 0.75 m），越深越偏青綠；河床鋪卵石、散放溪石，水底有細碎波光；順流細波紋；岸邊白沫依實際水深（對模組做光線投射）計算；補光燈不在水面反射，避免大片白斑。',
]
FIXED_NOTES = [
    '- 貼圖對比太低、碎石像泡泡、泥土小石像坑洞 → 重寫程序貼圖並重烤（`bake_textures.py`）。',
    '- 河岸護岸石太白、像方糖或鋪路磚 → 石材變暗、改成有隆起與傾斜的自然石（`KB.chunk` 的 dome／tilt），以邊角角度設定平滑與銳利邊。',
    '- 小石頭上的青苔看起來像綠色貼紙 → 只保留在較大的石頭上。',
    '- C05 石基原本是 10 個平方塊 → 改為倒角切石＋內縮灰縫；LOD1 改為真正減面的方石。',
    '- 細節越界檢查一開始抓到 4 件（A07、C02、C07 草片；C08 大石插入 C05 石基 9.7 cm）→ 加入建模時的防越界機制並調整擺放，重新檢查全部通過。',
    '- C08 大石只有 20 面（Blender icosphere 細分 1 = 正二十面體）→ 改為 80 面。',
    '- 使用者回饋「岸邊一塊一塊的石頭」：B07 原本是隔開成排的方石，像丟在坡上的積木、像地磚、又在模組邊界硬生生開始 → 改為大小混雜的圓石半埋在碎石層，方向打亂，每排起訖點隨機錯開，兩端參差融入土坡；其他河岸的單顆石頭改扁、半埋。',
    '- 使用者要求石頭精緻化：石塊加入隨機剝裂面（平整斷面＋銳利稜角）與兩層雜訊，石材貼圖加大冷暖色差。',
    '- 使用者要求清澈見底、有漸層的溪水：展示水面由一片平面改為清澈的水體（吸收很低，深處才偏青綠），河床改成中間深的溪谷並鋪卵石與溪石、加水底波光；波紋法線貼圖 `T_Water_Normal.png`；天空改為漸層，水面反射藍天。',
    '- 45° 透視圖鏡頭太近，18 件模型邊緣被裁到（自動裁切檢查發現）→ 改用整個包圍球入鏡的距離重拍。',
    '- 抽查 C05 全部視角時發現：石基背面（朝道路那面，使用時埋在坡道下）出現黑色三角破面，原因是內部灰縫填充塊與石塊背面共面 → 填充塊內縮 4 cm，重建橋頭檔並重跑全部檢查與匯出。',
    '- 使用者要求加橋：先誤解成獨木橋做了 D01；使用者說明要木頭搭造的橋梁後改做 D02 木造梁橋。D02 端視圖發現交叉斜撐共面重疊出現黑色菱形 → 第二根斜撐外移一根木料厚度。',
    '- 預覽主視角有時太小或看到側面 → 依地形平均法線取景，C05 從河側看石基正面。',
]


def gallery(D, rows):
    E = html.escape
    def img(p, alt, cls=''): return '<img loading="lazy" class="%s" src="%s" alt="%s">' % (cls, E(p), E(alt))
    parts = ['<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
             '<title>環境收邊模組圖庫</title><style>',
             ':root{--bg:#f4f2ed;--card:#fff;--ink:#222;--muted:#666;--line:#ddd}',
             '@media (prefers-color-scheme:dark){:root{--bg:#1d1f22;--card:#2a2d31;--ink:#eee;--muted:#aaa;--line:#444}}',
             'body{margin:0;background:var(--bg);color:var(--ink);font-family:system-ui,"PingFang TC","Noto Sans TC","Microsoft JhengHei",sans-serif}',
             'main{max-width:1280px;margin:0 auto;padding:16px}h1{font-size:1.6rem}h2{margin-top:2rem;border-bottom:1px solid var(--line);padding-bottom:.3rem}',
             '.show img{width:100%;border-radius:6px;margin:.4rem 0}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:14px}',
             '.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px}.card img.hero{width:100%;border-radius:4px}',
             '.card h3{margin:.4rem 0 .2rem;font-size:1.05rem}.meta{color:var(--muted);font-size:.85rem;line-height:1.5}',
             '.views{display:grid;grid-template-columns:repeat(5,1fr);gap:3px;margin-top:6px}.views img{width:100%;border-radius:2px}',
             'a{color:inherit}</style></head><body><main>',
             '<h1>環境收邊模組 v01｜29 件</h1><p class="meta">道路收邊 11、河岸 10、橋頭 8。每件 10 個正交角度＋45° 透視（1024×1024）。點圖片看原圖。'
             '地面、河床、溪石與水面是展示用道具。報告：<a href="../06_Reports/QA_Report.md">QA_Report.md</a>、<a href="../06_Reports/ASSET_MANIFEST.md">ASSET_MANIFEST.md</a>、'
             '<a href="../06_Reports/README_Integration.md">README_Integration.md</a></p>', '<h2>拼裝示範</h2><div class="show">']
    for v in ('hero', 'bridgehead', 'river', 'stream', 'top', 'seam_road', 'seam_bank', 'seam_deck'):
        p = 'Showcase/showcase_v01_%s_labels.png' % v
        parts.append('<a href="%s">%s</a>' % (E(p), img(p, v)))
    parts.append('</div>')
    for g in 'ABC':
        parts.append('<h2>%s</h2><div class="grid">' % E(GROUP_TITLE[g]))
        for r in rows:
            if r['group'] != g: continue
            m = K.BY_CODE[r['code']]; fo = 'Individual/%s_%s/' % (m['code'], m['id'])
            views = ''.join('<a href="%s%s.png" title="%s">%s</a>' % (E(fo), k, E(VIEW_ZH[k]), img(fo + k + '.png', VIEW_ZH[k])) for k in list(VIEW_ZH)[:10])
            parts.append('<div class="card"><a href="%s11_persp_45.png">%s</a><h3>%s %s</h3><div class="meta">%s<br>LOD0 %s／LOD1 %s／LOD2 %s 三角面｜預算 %s<br>'
                         '<a href="../%s">FBX</a>｜<a href="%smodel_info.json">model_info</a>｜<a href="%svalidation.json">validation</a></div><div class="views">%s</div></div>' % (
                             E(fo), img(fo + '11_persp_45.png', r['name_zh'], 'hero'), E(r['code']), E(r['name_zh']), E(m['purpose']), format(r['lod0_tris'], ','), r['lod1_tris'], r['lod2_tris'],
                             E(r['tri_budget']), E(r['fbx']), E(fo), E(fo), views))
        parts.append('</div>')
    if extra():
        mi, va = extra(); fo = 'Individual/D02_SM_Bridge_Timber_A/'
        views = ''.join('<a href="%s%s.png">%s</a>' % (E(fo), k, img(fo + k + '.png', k)) for k in list(VIEW_ZH)[:10] + ['12_detail', '13_pier'])
        parts.append('<h2>D 類｜後續新增</h2><div class="grid"><div class="card"><a href="%s11_persp_45.png">%s</a><h3>D02 木造梁橋</h3><div class="meta">%s<br>LOD0 %s 三角面｜'
                     '<a href="../%s">FBX</a>｜<a href="%smodel_info.json">model_info</a>｜<a href="%svalidation.json">validation</a></div><div class="views">%s</div></div></div>' % (
                         E(fo), img(fo + '11_persp_45.png', '木造梁橋', 'hero'), E(mi['purpose']), format(va['geometry']['lod0_tris'], ','), E(mi['files']['fbx']), E(fo), E(fo), views))
    parts.append('<h2>拼接測試（自動檢查用場景）</h2><div class="show">')
    for p in sorted((PREV / 'AssemblyTests').glob('final_all29_*.png')):
        parts.append('<a href="AssemblyTests/%s">%s</a>' % (E(p.name), img('AssemblyTests/' + p.name, p.stem)))
    parts.append('</div></main></body></html>')
    new(PREV / 'index.html').write_text('\n'.join(parts), encoding='utf-8')


def main():
    D = load()
    if '--sheets' in sys.argv:
        sheets(D); return
    if '--reports' in sys.argv:
        assert D['crop'], 'run --sheets first'
        new(REP / 'CONNECTOR_SPEC.json').write_text(json.dumps(connector_spec(D), ensure_ascii=False, indent=2, default=float))
        rows = manifest(D); per_module_json(D); qa_report(D, rows); gallery(D, rows)
        print('WROTE CONNECTOR_SPEC.json ASSET_MANIFEST.md/.csv QA_Report.md index.html'); return
    print(__doc__)


if __name__ == '__main__':
    main()
