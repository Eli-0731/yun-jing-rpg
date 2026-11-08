"""Generate AI three-view sheets for package A (11/05 + 11/08) with Codex CLI's built-in image generation.

Prompt = object sentence + Layout block (building or single, see make_prompts.py) + 5.2; 5.3 goes after "Avoid:"
because the tool has no negative field. Four images per item; all are kept in art/references/<ID>/ with prompt.txt.
Adapted from tools/world-props-a/gen_threeviews.py (11/03 package A).

    python tools/mountain-city-a/gen_threeviews.py MC01-SB01 MC01-SF01 ...
"""
import json, shutil, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
GEN = Path.home() / '.codex' / 'generated_images'
data = json.loads((HERE / 'prompts.json').read_text(encoding='utf-8'))
only = sys.argv[1:]

for item, body in data['items'].items():
    if only and item not in only:
        continue
    out = REPO / 'art' / 'references' / item
    if out.exists() and len(list(out.glob('*_option*.png'))) >= 4:
        print(item, 'already has images, skipped', flush=True)
        continue
    out.mkdir(parents=True, exist_ok=True)
    layout = data['layout_' + body['layout']]
    prompt = f"{body['object']} {layout} {data['style52']} Avoid: {data['negative53']}"
    aspect = 'landscape 3:2 (at least 1536 px wide)'
    (out / 'prompt.txt').write_text(
        f"Tool: Codex CLI image generation (no negative-prompt field, so 5.3 is appended after 'Avoid:').\n"
        f"Aspect: {aspect}\nLayout block: {body['layout']}"
        + (" (11/07 B package building Layout; 11/05 package section 5 asks for a 3/4 view on buildings)" if body['layout'] == 'building' else '')
        + f"\n\n{prompt}\n", encoding='utf-8')
    task = (f"Use your image generation tool to create FOUR separate images (four independent variations of the same brief, "
            f"{aspect} each). Use exactly this brief for every image, do not add or remove anything:\n\n{prompt}\n\n"
            f"Do not write any files yourself. When done, list the paths of the four generated images.")
    before = {p.name for p in GEN.iterdir()} if GEN.exists() else set()
    t0 = time.time()
    r = subprocess.run(['codex', 'exec', '--skip-git-repo-check', '-s', 'read-only', '-'], input=task, text=True,
                       capture_output=True, encoding='utf-8', errors='replace', shell=True)
    new = [p for p in GEN.iterdir() if p.name not in before] if GEN.exists() else []
    pngs = sorted((png for d in new for png in d.glob('*.png')), key=lambda p: p.stat().st_mtime)
    for i, png in enumerate(pngs, 1):
        shutil.copy2(png, out / f'{item}_option{i}.png')
    print(item, 'images', len(pngs), f'{time.time() - t0:.0f}s', 'exit', r.returncode, flush=True)
    if not pngs:
        (out / 'codex_log.txt').write_text(r.stdout[-4000:] + '\n' + r.stderr[-4000:], encoding='utf-8')
