"""Same-light lineups for the 11/05 review (Johnnnny0823): each family of world props side by side, rendered once as a neutral
grey model (--clay: form only) and once with its baked materials, under the same style-guide day light and camera, pasted
grey | material into one sheet per family. Imports the exported FBX files, so this is what the engine receives.
python lineup_world_a.py <blender.exe> [family ...]   (run from the repo root; writes art/previews/world-props-a/lineup/)
"""
import json, subprocess, sys, os
from PIL import Image
B = sys.argv[1]; E = 'art/exports/world-props-a'; OUT = 'art/previews/world-props-a/lineup'; os.makedirs(OUT, exist_ok=True)
RIG = 'art/source/world-props-a/render_world_a.py'
info = json.load(open(f'{E}/model_info.json', encoding='utf-8'))
FAMILIES = {
    'rocks-RK12': ['RK12A', 'RK12B', 'RK12C', 'RK12D'],
    'banks-WM08': ['WM08A', 'WM08B', 'WM08C'],
    'banks-WM10': ['WM10A', 'WM10B', 'WM10C', 'WM10D'],
    'lotus-TY03': ['TY03A', 'TY03B', 'TY03C', 'TY03D'],
    'posts-RK01': ['RK01A', 'RK01B'],
    'stacks-RK10': ['RK10A', 'RK10B'],
    'shrines-SC01-RK06': ['SC01', 'RK06'],
    'camp-SC02-RK09-TY06': ['SC02', 'RK09', 'TY06'],
    'buildings-SC03-SC04-RK05': ['SC03', 'SC04', 'RK05'],
}
for fam, ids in FAMILIES.items():
    if sys.argv[2:] and fam not in sys.argv[2:]: continue
    ids = [i for i in ids if i in info]
    x = 0.0; ats = []
    for i in ids:   # left to right with a 0.4 m gap, each centred on its own footprint
        w = info[i]['dimensions_xyz_m'][0]; ats.append(f'{x + w / 2:.3f},0,0'); x += w + .4
    shift = x / 2 - .2; ats = [f'{float(a.split(",")[0]) - shift:.3f},0,0' for a in ats]
    files = ','.join(f'{E}/{i}.fbx' for i in ids)
    shots = []
    for mode in ('clay', 'mat'):
        tag = f'{fam}-{mode}'
        cmd = [B, '-b', '--factory-startup', '-P', RIG, '--', '--glb', files, '--at=' + ';'.join(ats), '--out', OUT, '--tag', tag,
               '--views', 'threequarter', '--light', 'day', '--res', '1280x720', '--samples', '48'] + (['--clay'] if mode == 'clay' else [])
        r = subprocess.run(cmd, capture_output=True, text=True)
        if 'RIG_DONE' not in r.stdout: print('FAILED', tag, r.stdout[-800:], r.stderr[-800:]); continue
        shots.append(f'{OUT}/{tag}-threequarter.png')
    if len(shots) == 2:
        a, b = Image.open(shots[0]), Image.open(shots[1]); s = Image.new('RGB', (a.width + b.width, a.height))
        s.paste(a, (0, 0)); s.paste(b, (a.width, 0)); s.save(f'{OUT}/{fam}-grey-vs-material.png'); print('LINEUP', fam, ids)
