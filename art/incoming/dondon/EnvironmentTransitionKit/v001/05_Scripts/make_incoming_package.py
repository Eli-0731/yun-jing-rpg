"""Copy this kit into the yun-jing-rpg hand-off folder layout (Python 3 + Pillow; no Blender).

  python3 Environment_Transition_Kit/05_Scripts/make_incoming_package.py \
      --dest /path/to/yun-jing-rpg/art/incoming/dondon/EnvironmentTransitionKit/v001 [--full-previews]

The receiving repository's rule (docs/素材交接清單-dondon.md) allows keeping the original structure when moving
files would break relative paths: every .blend links its textures as //../03_Textures/..., so the kit keeps its
folder layout inside v001/.  Copied: 00_References, 01_Blender, 02_Exports, 03_Textures, 04_Previews, 05_Scripts,
06_Reports and README.md.  Not copied: _work/ (local scratch) and __pycache__.  By default the per-module previews
in 04_Previews/Individual are written at 512 px (as the receiving repo's other hand-offs do) to keep Git LFS small;
--full-previews copies the 1024 px originals.  CSV files written with CRLF are stored with LF line endings (the receiving
repository normalises text files), and SOURCE.json says so.  Writes SOURCE.json (source repo, commit, SHA-256 of every source
file and whether the copy is byte-identical), package-level model_info.json and validation.json (gathered from
the per-module records and 06_Reports/qa, no new measurements) and README.md (hand-off notes).  Run check_incoming.py with Blender
afterwards to write handoff_check.json.  Refuses to write into an existing folder.
"""
import hashlib, json, shutil, subprocess, sys
from pathlib import Path
from PIL import Image

KIT = Path(__file__).resolve().parents[1]
PARTS = ['00_References', '01_Blender', '02_Exports', '03_Textures', '04_Previews', '05_Scripts', '06_Reports', 'README.md']


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''): h.update(c)
    return h.hexdigest()


def git(*a):
    try: return subprocess.run(['git', '-C', str(KIT), *a], capture_output=True, text=True, check=True).stdout.strip()
    except Exception: return None


def main():
    a = sys.argv[1:]
    if '--dest' not in a: raise SystemExit(__doc__)
    dest = Path(a[a.index('--dest') + 1]).resolve(); full = '--full-previews' in a
    if dest.exists(): raise SystemExit('EXISTS (not overwritten): %s' % dest)
    for p in KIT.rglob('*'):                                   # LFS pointers instead of real files would make a broken hand-off
        if p.is_file() and p.suffix in ('.blend', '.fbx', '.png') and p.stat().st_size < 200 and p.read_bytes().startswith(b'version https://git-lfs'):
            raise SystemExit('Git LFS file not downloaded (run git lfs pull in the source repo): %s' % p.relative_to(KIT))
    files = []
    for part in PARTS:
        src = KIT / part
        for p in ([src] if src.is_file() else sorted(src.rglob('*'))):
            if not p.is_file() or '__pycache__' in p.parts: continue
            rel = p.relative_to(KIT); out = dest / rel; out.parent.mkdir(parents=True, exist_ok=True)
            small = (not full) and rel.parts[:2] == ('04_Previews', 'Individual') and p.suffix == '.png'
            crlf = p.suffix == '.csv' and b'\r\n' in p.read_bytes()     # receiving repo has * text=auto: store LF so hashes stay valid
            if small:
                im = Image.open(p); im.thumbnail((512, 512), Image.LANCZOS); im.save(out, optimize=True)
            elif crlf:
                out.write_bytes(p.read_bytes().replace(b'\r\n', b'\n'))
            else:
                shutil.copy2(p, out)
            files.append({'path': str(rel), 'bytes': p.stat().st_size, 'sha256': sha(p),
                          'copy': 'resized to 512 px' if small else 'CRLF line endings changed to LF' if crlf else
                                  ('identical' if sha(out) == sha(p) else 'DIFFERENT')})
    bad = [f['path'] for f in files if f['copy'] == 'DIFFERENT']
    if bad: raise SystemExit('copy mismatch: %s' % bad[:5])
    source = {'source_repository': 'https://github.com/joshsu54/dondon', 'source_branch': git('rev-parse', '--abbrev-ref', 'HEAD'),
              'source_commit': git('rev-parse', 'HEAD'), 'source_folder': 'Environment_Transition_Kit/',
              'previews': 'full 1024 px' if full else 'per-module previews resized to 512 px; originals stay in the source repository',
              'files': len(files), 'identical_copies': sum(1 for f in files if f['copy'] == 'identical'), 'file_list': files}
    (dest / 'SOURCE.json').write_text(json.dumps(source, ensure_ascii=False, indent=2))
    write_summaries(dest)
    (dest / 'README.md').rename(dest / 'README_kit.md')
    (dest / 'README.md').write_text(readme(source), encoding='utf-8')
    total = sum(p.stat().st_size for p in dest.rglob('*') if p.is_file())
    print('PACKAGED %d files, %.1f MB -> %s' % (len(files), total / 1e6, dest))
    print('Next: blender -b --python-exit-code 1 --python %s/05_Scripts/check_incoming.py -- --pkg %s' % (dest, dest))


def write_summaries(dest):
    """Package-level model_info.json / validation.json, gathered from the per-module records (no new measurements)."""
    load = lambda p: json.loads(p.read_text())
    ind = dest / '04_Previews' / 'Individual'; assets, checks = [], []
    for d in sorted(ind.iterdir()):
        if not (d / 'model_info.json').exists(): continue
        m, v = load(d / 'model_info.json'), load(d / 'validation.json'); t = m['triangles']
        lod = {k: sum(n for o, n in t.items() if o.endswith(k)) for k in ('LOD0', 'LOD1', 'LOD2', 'COL')} if 'LOD0' not in t else \
              {k: t[k] for k in ('LOD0', 'LOD1', 'LOD2', 'COL')}
        assets.append({'code': m['code'], 'id': m['id'], 'name_zh': m['name_zh'], 'group': m['group'],
                       'size_m': [round(b - a, 4) for a, b in zip(m['bounds_min_m'], m['bounds_max_m'])], 'triangles': lod,
                       'materials': m['materials'], 'blend': m['files']['blend'], 'fbx': m['files']['fbx'], 'previews': str(d.relative_to(dest))})
        checks.append({'code': m['code'], 'id': m['id'], 'overall_pass': v['overall_pass'], 'record': str((d / 'validation.json').relative_to(dest))})
    qa = dest / '06_Reports' / 'qa'; final, reimp, crop = load(qa / 'final_all29.json'), load(qa / 'fbx_reimport_v01.json'), load(qa / 'preview_crop_check.json')
    prot = load(dest / '06_Reports' / 'PHASE6_ProtectedAssetRecheck.json')
    (dest / 'model_info.json').write_text(json.dumps({
        'package': 'EnvironmentTransitionKit', 'version': 'v001', 'source_version': 'v01', 'assets': len(assets),
        'units': 'metre (1 unit = 1 m)', 'up': '+Z in Blender; FBX written Forward -Z, Up Y, Apply Transform',
        'forward': '+X = travel direction, +Y = left side; preview 01_front looks from -Y',
        'pivot': 'A/B: entry connector; C01-C05, C07, C08: shared bridgehead frame; bridges: entry-end deck centre',
        'status': {'uv': 'done (world-scale, 2 m per UV unit; textures tile)', 'lod': 'LOD0/LOD1/LOD2 per asset',
                   'collision': '_COL proxy mesh per asset (not tested in an engine)', 'rig_animation': 'none (static props)',
                   'materials': 'Blender node materials + baked 1024 px PBR textures; engine materials must be rebuilt (06_Reports/README_Integration.md)'},
        'items': assets}, ensure_ascii=False, indent=2))
    (dest / 'validation.json').write_text(json.dumps({
        'package': 'EnvironmentTransitionKit', 'version': 'v001', 'measured_in': 'source repository with Blender %s' % final['blender'],
        'connectors_chains_pairs': {'pass': final['pass'], 'tolerance_m': final['tolerance_m'], 'chains': len(final['chains']), 'pairs': len(final['pairs']),
                                    'record': '06_Reports/qa/final_all29.json'},
        'fbx_blender_reimport': {'pass': reimp['pass'], 'modules': len(reimp['modules']), 'scope': reimp['scope'], 'record': '06_Reports/qa/fbx_reimport_v01.json'},
        'preview_crop_check': {'all_1024': all(r['all_1024'] for r in crop['modules'].values()),
                               'touching_edge': {k: r['touching_edge'] for k, r in crop['modules'].items() if r['touching_edge']},
                               'record': '06_Reports/qa/preview_crop_check.json'},
        'protected_assets_unchanged': prot['unchanged'], 'per_asset': checks,
        'hand_off_check': 'handoff_check.json (written by check_incoming.py at the receiving location)',
        'not_done': ['Unity import', 'URP materials', 'mobile performance', 'in-engine collision and walking', 'AI three-views before modelling (see README)']},
        ensure_ascii=False, indent=2))


def readme(src):
    return f'''# 環境收邊模組包（EnvironmentTransitionKit v001）

來源：[joshsu54/dondon](https://github.com/joshsu54/dondon) 分支 `{src['source_branch']}`、提交 `{(src['source_commit'] or '')[:7]}` 的 `Environment_Transition_Kit/`；
{src['identical_copies']} 個檔案與來源 SHA-256 相同，清單見 `SOURCE.json`。{'' if 'full' in src['previews'] else '單件預覽縮為 512 px（原 1024 px 留在來源儲存庫）。'}

因為每個 `.blend` 以相對路徑 `//../03_Textures/` 引用貼圖，本包**保留來源的資料夾結構**（素材交接清單允許此做法）。原套件說明在 `README_kit.md`。

## 內容

| 編號 | 內容 | 可編輯原檔 | 引擎交換檔 |
| --- | --- | --- | --- |
| A01–A11 | 不規則道路收邊 11 件 | `01_Blender/road_edge_modules_v01.blend`（每件一個 Collection） | `02_Exports/RoadEdge/*.fbx` |
| B01–B10 | 河岸收邊 10 件 | `01_Blender/riverbank_modules_v01.blend` | `02_Exports/Riverbank/*.fbx` |
| C01–C08 | 橋頭收邊 8 件 | `01_Blender/bridgehead_modules_v01.blend` | `02_Exports/Bridgehead/*.fbx` |
| D02 | 木造梁橋（10 m 跨、木排架橋墩、欄杆） | `01_Blender/timber_bridge_v01.blend` | `02_Exports/Bridge/SM_Bridge_Timber_A.fbx` |
| D01 | 獨木橋（可選件） | `01_Blender/log_bridge_v01.blend` | `02_Exports/Bridge/SM_Bridge_Log_A.fbx` |
| — | 測試輔助（1 m 方塊、路芯、佔位橋面） | 在各 `.blend` 的 `COL_TEST_Only` | `02_Exports/_TestHelpers/*.fbx` |

根目錄 `model_info.json` 是 31 件的總表（尺寸、各 LOD 三角面、材質、檔案位置、UV／LOD／碰撞／動畫狀態），`validation.json` 彙整來源端實際跑過的檢查結果。
每件的 `model_info.json`、`validation.json`、`views.json` 與預覽在 `04_Previews/Individual/<編號>_<ID>/`。
總表 `04_Previews/Sheets/`、拼裝展示 `04_Previews/Showcase/`、檢查報告 `06_Reports/QA_Report.md`、引擎匯入說明 `06_Reports/README_Integration.md`。

## 規格

- 公尺、Z 向上；模組行進方向 +X、+Y 為左側（預覽的 01_front 由 -Y 看）。FBX：Forward -Z、Up Y、FBX All、Apply Transform、頂點色 Linear。
- Pivot：A、B 在入口接頭中心；C01–C05、C07、C08 共用橋頭座標系；橋在入口端橋面中心（放進橋頭座標系平移 (2, 0, +0.15)）。
- 每件有 LOD0／LOD1／LOD2 與 `_COL` 碰撞代理；UV 已整理（2 m 一個 UV 單位），地表貼圖為 1024² 可平鋪 PBR，`M_TerrainBlend` 用頂點色 Mask 混合（引擎內需依 README_Integration 重建）。
- 三角面與尺寸：`06_Reports/ASSET_MANIFEST.md`；接頭規格：`06_Reports/CONNECTOR_SPEC.json`。

## 驗證

- 來源端：接頭／串接／配對誤差 ≤ 0.0005 mm、細節不越界、29 件 FBX 在 Blender 回匯一致、木橋擱置與標高檢查，見 `06_Reports/qa/` 與 `QA_Report.md`。
- 本次交接：`handoff_check.json`（在接收端路徑重開每個 `.blend`、確認貼圖都找得到、FBX 回匯）。
- **未做：** Unity 匯入、URP 材質、手機效能、引擎內碰撞與行走。Blender 能開、FBX 能回匯，不代表 Unity 已驗收。

## 設計參考（請注意）

`00_References/ThreeViews/` 與 REF_A–E 是**建模前**由腳本依規格數值繪製的工程三視圖，**不是 AI 生成的三視圖**（製作當時的環境沒有生圖工具）；REF_F 與 `04_Previews/` 都是建模後的渲染。若要符合本儲存庫「先 AI 三視圖再建模」的規定，需要補 AI 三視圖或由使用者確認例外。

## 製作工具

`05_Scripts/`：全部生成、貼圖烘焙、檢查、匯出、出圖腳本（`build_all.sh` 依序執行；需 Blender 5.2 背景模式與 Python 3＋Pillow）。腳本依套件資料夾結構讀寫，可在本資料夾內直接重建。

## 來源與授權

- 作者：joshsu54 的 dondon 專案，由 AI 程式助理以 Blender Python 程序化建模與烘焙貼圖；沒有使用外部模型、貼圖或素材庫。
- 授權：來源儲存庫沒有授權檔；轉入《雲境》的使用條件需由 joshsu54 與 z1nnz 確認。
'''


if __name__ == '__main__':
    main()
