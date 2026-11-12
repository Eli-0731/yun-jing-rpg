"""MC02 three-view prompts (承天 B district rope bridges). Object sentences from the 11/05 package section 11 (via prompts.json);
the package's own bridge layout (three-quarter with the cliff gap + front, side and top views) instead of the building layout;
plus what PR #80 / #90 taught: a Chinese Song-dynasty wording, a scope sentence so a sheet shows only the bridge, and the core
team's Japanese / European negatives. Style 5.2 and negatives 5.3 unchanged.

    python tools/mountain-city-a/make_prompts_mc02.py          -> tools/mountain-city-a/prompts_mc02.json
    python tools/mountain-city-a/gen_threeviews.py --prompts prompts_mc02.json MC02-24M MC02-12M
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
base = json.loads((HERE / 'prompts.json').read_text(encoding='utf-8'))
NEG_REVIEW = ('Japanese architecture, torii, shimenawa rope, chochin round paper lantern, toro stone lantern, '
              'European castle, medieval European drawbridge, Inca grass bridge, modern steel cable, steel wire rope, '
              'red-lacquered railings, Tudor half-timbering, diagonal X bracing')
LAYOUT_BRIDGE = ('Layout: one three-quarter view with the cliff gap, plus front, side and top orthographic views of the structure alone '
                 'on a plain light warm-grey background, same scale (package A 11/05 section 11 bridge layout).')
SCOPE = (' Show only this one bridge as a single game module: a granite bridgehead with two short stone posts at each end where the '
         'chains are anchored, two dark iron hand chains on each side hanging in a gentle catenary, short iron hangers down to two '
         'deck chains, a continuous deck of weathered cedar planks lashed with hemp (a few loose or missing decorative planks only '
         'at the outer edges, never in the walking path), the two ends at exactly the same height; Chinese Song-dynasty mountain '
         'city style; no buildings, no towers, no gates, no people, no lettering, no flags.')
items = {}
for k in ('MC02-24M', 'MC02-12M'):
    items[k] = {'object': base['items'][k]['object'] + SCOPE, 'layout': 'bridge',
                'negative_extra': NEG_REVIEW + ', buildings, towers, gatehouse, people, banners, lettering, water, river'}
out = {k: base[k] for k in ('style52', 'negative53', 'layout_single', 'layout_building')}
out['layout_bridge'] = LAYOUT_BRIDGE
out['items'] = items
(HERE / 'prompts_mc02.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
print(len(items), 'items -> prompts_mc02.json')
