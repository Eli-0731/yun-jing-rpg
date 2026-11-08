"""Build prompts.json for package A (MC01/TX04/MC02/SF) from the package docs.

Object sentences come from the 11/05 package section 11 (the text before ' Layout:') and the 11/08 package SF list.
Building modules use the building Layout block from the 11/07 B package appendix, because the 11/05 package
section 5 asks for a 3/4 view on buildings; small props keep the single-object Layout block. 5.2 and 5.3 are unchanged.

    python tools/mountain-city-a/make_prompts.py <A48.md> <A80.md> <B104.md>
"""
import json, re, sys
from pathlib import Path

a48, a80, b104 = (Path(p).read_text(encoding='utf-8') for p in sys.argv[1:4])
blocks = re.findall(r'```text\n(.*?)\n```', b104, re.S)
layout_single, layout_building, style52, negative53 = blocks[0], blocks[1], blocks[2], blocks[3]
assert layout_single.startswith('Layout: front view') and layout_building.startswith('Layout: one three-quarter')
assert style52.startswith('Art direction') and negative53.startswith('photorealistic')

items = {}
for m in re.finditer(r'### (\S+)\n\nPositive prompt:\n\n```text\n(.*?)\n```', a48, re.S):
    items[m.group(1)] = m.group(2).split(' Layout:')[0].strip()
for m in re.finditer(r'\*\*(SF0\d)\*\*\n```text\n(.*?)\n```', a80, re.S):
    items[m.group(1)] = m.group(2).strip()

SMALL = re.compile(r'^(MC01-DT|SF0)')
out = {'style52': style52, 'negative53': negative53, 'layout_single': layout_single,
       'layout_building': layout_building, 'items': {}}
for k, v in items.items():
    out['items'][k] = {'object': v, 'layout': 'single' if SMALL.match(k) else 'building'}
dst = Path(__file__).resolve().parent / 'prompts.json'
dst.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
print(len(items), 'items ->', dst)
