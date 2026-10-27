"""PHASE 0 safety check for the Environment Transition Kit (read-only except creating the new kit folder).

- Scans for protected assets (樹伴古樹 / 山兔 / 主世界) by file and folder NAME only; never opens .blend files.
- Records size, mtime and SHA-256 of any match (read-only) so the final check can compare.
- Picks the first unused folder Environment_Transition_Kit[_vNN] under the project root, resolving symlinks.
- Writes 06_Reports/PHASE0_Safety.json and .md inside the new kit folder only.
Usage: python3 phase0_safety_check.py <project_root> [--final <kit_dir>]
"""
import hashlib, json, os, sys, time
from pathlib import Path

PATTERNS = ['樹伴', '古樹', '山兔', '主世界', 'mainworld', 'main_world', 'overworld', 'treecompanion', 'tree_companion',
            'ancienttree', 'ancient_tree', 'mountainrabbit', 'mountain_rabbit', 'rabbit', 'hare_']
SEARCH_ROOTS = ['/home', '/root', '/tmp', '/opt', '/mnt', '/srv', '/workspace']
SKIP = {'/proc', '/sys', '/dev', '/opt/blender', '/root/.cache', '/root/.npm'}

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''): h.update(chunk)
    return h.hexdigest()

def scan():
    hits = []
    for base in SEARCH_ROOTS:
        if not os.path.isdir(base): continue
        for dp, dns, fns in os.walk(base, followlinks=False):
            if any(dp == s or dp.startswith(s + '/') for s in SKIP) or '/.git/' in dp + '/' and dp.endswith('objects'):
                dns[:] = []; continue
            dns[:] = [d for d in dns if d not in ('.git', 'node_modules', '__pycache__')]
            for name in dns + fns:
                low = name.lower()
                if any(p in low for p in PATTERNS):
                    full = os.path.join(dp, name); rec = {'path': full, 'is_dir': os.path.isdir(full), 'is_symlink': os.path.islink(full)}
                    if os.path.isfile(full) and not os.path.islink(full):
                        st = os.stat(full); rec.update(size=st.st_size, mtime=st.st_mtime, sha256=sha(full))
                    hits.append(rec)
    return hits

def main():
    root = Path(sys.argv[1]).resolve()
    if '--final' in sys.argv:
        kit = Path(sys.argv[sys.argv.index('--final') + 1]).resolve()
        before = json.loads((kit / '06_Reports/PHASE0_Safety.json').read_text())
        now = scan(); old = {h['path']: h for h in before['protected_matches']}; new = {h['path']: h for h in now}
        changed = [p for p in old if p not in new or old[p].get('sha256') != new[p].get('sha256') or old[p].get('mtime') != new[p].get('mtime')]
        added = [p for p in new if p not in old]
        out = {'checked_at': time.strftime('%Y-%m-%d %H:%M:%S'), 'protected_matches_before': len(old), 'protected_matches_now': len(new),
               'changed_or_missing': changed, 'new_matches': added, 'unchanged': not changed and not added}
        (kit / '06_Reports/PHASE6_ProtectedAssetRecheck.json').write_text(json.dumps(out, ensure_ascii=False, indent=2))
        print(json.dumps(out, ensure_ascii=False, indent=2)); return
    hits = scan()
    n = 1; kit = root / 'Environment_Transition_Kit'
    while kit.exists() or kit.is_symlink():
        n += 1; kit = root / f'Environment_Transition_Kit_v{n:02d}'
    real_root = root.resolve(); assert str(kit.resolve().parent) == str(real_root), 'kit parent resolves elsewhere'
    for h in hits:
        rp = os.path.realpath(h['path'])
        assert not (rp == str(kit) or rp.startswith(str(kit) + '/')), ('protected path inside kit', rp)
    symlinks_in_root = [str(p) for p in [root] + list(root.parents) if p.is_symlink()]
    kit.mkdir()
    for sub in ['00_References', '01_Blender', '02_Exports/RoadEdge', '02_Exports/Riverbank', '02_Exports/Bridgehead', '03_Textures',
                '04_Previews/Individual', '04_Previews/AssemblyTests', '05_Scripts', '06_Reports']:
        (kit / sub).mkdir(parents=True)
    rep = {'checked_at': time.strftime('%Y-%m-%d %H:%M:%S'), 'project_root': str(root), 'kit_dir': str(kit), 'kit_realpath': str(kit.resolve()),
           'symlinks_on_kit_path': symlinks_in_root, 'search_roots': SEARCH_ROOTS, 'name_patterns': PATTERNS,
           'protected_matches': hits, 'protected_matches_found': len(hits),
           'blend_files_in_project': sum(1 for _ in root.rglob('*.blend')),
           'policy': 'Protected assets are never opened, linked, appended or written. Matching is by name only; hashing is read-only.'}
    (kit / '06_Reports/PHASE0_Safety.json').write_text(json.dumps(rep, ensure_ascii=False, indent=2))
    print(json.dumps({k: v for k, v in rep.items() if k != 'protected_matches'}, ensure_ascii=False, indent=2))
    for h in hits: print('MATCH', h['path'])

if __name__ == '__main__':
    main()
