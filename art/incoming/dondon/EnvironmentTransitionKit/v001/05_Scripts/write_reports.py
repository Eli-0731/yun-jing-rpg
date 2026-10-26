"""Write 06_Reports/ASSET_MANIFEST.md and ASSET_MANIFEST.csv from kit_spec.py (pure Python 3).

Design-stage manifest: expected sizes and connectors come from the spec; measured values (triangles,
FBX paths, QA results) are added by the later modelling/QA scripts.  Refuses to overwrite.
Usage: python3 write_reports.py --manifest
"""
import csv, io, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit_spec as K

KIT = Path(__file__).resolve().parents[1]
REPORTS = KIT / '06_Reports'


def bounds(mod):
    xs, ys, zs = [], [], []
    if mod['kind'] == 'c_base':
        return (K.RAMP_L, K.BASE_FACE_X, -K.DECK_HALF, K.DECK_HALF, -0.55, K.DECK_BOTTOM)
    parts = [K.Surface(mod, i) for i in range(len(mod['parts']))] if mod['kind'] == 'c_grid' else [K.Surface(mod)]
    for sf in parts:
        for u in sf.us:
            for v in sf.vs:
                x, y = sf.xy(u, v); xs.append(x); ys.append(y); zs.append(sf.z(u, v))
    return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))


def tris(mod):
    if mod['kind'] == 'c_base': return None
    parts = [K.Surface(mod, i) for i in range(len(mod['parts']))] if mod['kind'] == 'c_grid' else [K.Surface(mod)]
    return sum((len(p.us) - 1) * (len(p.vs) - 1) * 2 for p in parts)


def compatible(mod, con):
    """Modules whose opposite connector has the same type (and surface variant)."""
    t = con['type']; var = con.get('surface_variant'); out = []
    if con['role'] == 'exit' and var:
        return ['（幾何相容所有 ROAD_3M 入口；材質為%s狀態，本套件尚無同狀態路段）' % ('草地小徑' if var == 'GRASS_PATH' else '碎石路')]
    want = 'exit' if con['role'] == 'entry' else 'entry'
    for m in K.MODULES:
        for c in K.connectors(m):
            if c['role'] == want and c['type'] == t and c['name'] in ('EntryConnector', 'ExitConnector'):
                if con['role'] == 'entry' and c.get('surface_variant') not in (None, var):
                    continue
                if con['role'] == 'exit' and var and m['kind'] != 'road_end':
                    continue
                out.append(m['code'])
    extra = {'BRIDGE_3M': ['TEST_BridgeDeck_3m', '正式橋梁（橋面 +0.15、寬 3 m）'],
             'ROAD_EDGE_L': ['TEST_RoadCore_3m', 'ROAD_3M 模組的 +Y 收邊帶'], 'ROAD_EDGE_R': ['TEST_RoadCore_3m', 'ROAD_3M 模組的 -Y 收邊帶']}.get(t, [])
    if t == 'ROAD_3M' and not var:
        extra = ['A01+A02+TEST_RoadCore_3m'] + extra
    return sorted(set(out)) + extra


def main():
    if '--manifest' not in sys.argv:
        print(__doc__); return
    md_path = REPORTS / 'ASSET_MANIFEST.md'; csv_path = REPORTS / 'ASSET_MANIFEST.csv'
    for p in (md_path, csv_path):
        if p.exists(): raise SystemExit('EXISTS (not overwritten): %s' % p)
    rows = []
    for m in K.MODULES:
        b = bounds(m); cons = K.connectors(m)
        ent = next((c for c in cons if c['name'] == 'EntryConnector'), None); ex = next((c for c in cons if c['name'] == 'ExitConnector'), None)
        def tf(c): return '' if not c else '(%.3f, %.3f, %.3f) %+.1f°' % (*c['location'], c['heading_deg'])
        rows.append(dict(
            code=m['code'], id=m['id'], group=m['group'], name_zh=m['name_zh'], purpose=m['purpose'],
            size_x_m='%.2f' % (b[1] - b[0]), size_y_m='%.2f' % (b[3] - b[2]), z_min_m='%.2f' % b[4], z_max_m='%.2f' % b[5],
            pivot='bridgehead frame origin (C01 road entry)' if m['group'] == 'C' and m['kind'] != 'c06' else 'entry connector (0,0,0)' if m['kind'] != 'c06' else 'ground below high edge (0,0,0)',
            entry_type=ent['type'] if ent else '', entry_transform=tf(ent),
            exit_type=(ex['type'] + (' / ' + ex['surface_variant'] if ex and ex.get('surface_variant') else '')) if ex else '（單側封口）',
            exit_transform=tf(ex),
            entry_compatible=' '.join(compatible(m, ent)) if ent else '', exit_compatible=' '.join(compatible(m, ex)) if ex else '',
            seams=' '.join('%s→%s' % (c['name'], c.get('partner', '')) for c in cons if c['role'] == 'seam'),
            lod0_terrain_tris_est=tris(m) or '600–1400（砌石）', tri_budget='%d–%d' % K.tri_budget(m),
            fbx='02_Exports/%s/%s.fbx' % (K.GROUP_EXPORT_DIR[m['group']], m['id']),
            three_view='00_References/ThreeViews/%s_%s_3view.png' % (m['code'], m['id']),
            status='設計三視圖完成；尚未建模'))
    buf = io.StringIO(); w = csv.DictWriter(buf, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    csv_path.write_text('﻿' + buf.getvalue(), encoding='utf-8')
    L = ['# ASSET_MANIFEST｜29 件環境收邊模組', '',
         '依 `05_Scripts/kit_spec.py` 產生的設計階段清單。尺寸為地表網格範圍（細節前，模組座標）；三角面數為 LOD0 地表格點估算，細節物件另計。'
         '「可相接」列出接頭類型與路面狀態都相同的模組代碼。目前狀態：**設計三視圖完成，尚未建模**。', '']
    for g, title in (('A', 'A. 道路不規則收邊（11）'), ('B', 'B. 河岸自然收邊（10）'), ('C', 'C. 橋頭與地形交接收邊（8）')):
        L += ['## ' + title, '', '| 編號 | 模組 ID | 名稱 | 外形 X×Y (m) | Z 範圍 (m) | 入口 | 出口 | 入口可接 | 出口可接 | LOD0 地表三角面 |', '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
        for r in rows:
            if r['group'] != g: continue
            L.append('| %s | `%s` | %s | %s × %s | %s～%s | %s %s | %s %s | %s | %s | %s |' % (
                r['code'], r['id'], r['name_zh'], r['size_x_m'], r['size_y_m'], r['z_min_m'], r['z_max_m'], r['entry_type'], r['entry_transform'],
                r['exit_type'], r['exit_transform'], r['entry_compatible'] or '—', r['exit_compatible'] or '—', r['lod0_terrain_tris_est']))
        L += ['']
        for r in rows:
            if r['group'] != g: continue
            L.append('- **%s %s**：%s%s' % (r['code'], r['name_zh'], r['purpose'], ('　內部接縫：' + r['seams']) if r['seams'] else ''))
        L += ['']
    L += ['## 測試物件（不屬於 29 件、不匯出）', '',
          '- `TEST_RoadCore_3m`：4 m × 3 m 平面路芯，Z = 0，用來測試 A01＋A02。',
          '- `TEST_BridgeDeck_3m`：寬 3 m、頂 +0.15 m、厚 0.20 m 的佔位橋面，放在 `COL_TEST_Only`。',
          '- `TEST_Water_-0.8`：示意水面 Z = -0.80 m，只在測試場景。',
          '- `TEST_ScaleCube_1m`：1 m 尺度方塊。', '']
    md_path.write_text('\n'.join(L), encoding='utf-8')
    print('WROTE', md_path, csv_path)


if __name__ == '__main__':
    main()
