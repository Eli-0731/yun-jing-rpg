"""TX04 three-view prompts (承天 B district Taixuan branch academy). Object sentences from the 11/05 package section 11 (via
prompts.json), plus what the MC01 rounds on PR #80 taught: a Chinese Song-dynasty wording, one scope sentence per item so a
sheet shows only that module, the core team's Japanese/European negatives, and per-item negatives. Layout and style52 unchanged.

    python tools/mountain-city-a/make_prompts_tx04.py          -> tools/mountain-city-a/prompts_tx04.json
    python tools/mountain-city-a/gen_threeviews.py --prompts prompts_tx04.json TX04-GATE TX04-WALL-ST
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
base = json.loads((HERE / 'prompts.json').read_text(encoding='utf-8'))
NEG_REVIEW = ('Japanese architecture, machiya, noren, shoji, chochin round paper lantern, toro stone lantern, torii, '
              'Tudor half-timbering, European timber framing, diagonal X bracing')
STYLE_FIX = ('a Chinese Song-dynasty style mountain academy', 'a solemn academy')
SCOPE = {
    'TX04-GATE': (' Show only this one gatehouse module: a single-bay gate building with its roof, its pair of doors and its stone '
                  'base, the plaque board left completely blank; no flanking courtyard walls beyond its own 6 m width, no courtyard, '
                  'no buildings behind, no lettering or emblems anywhere.',
                  'flanking walls, courtyard buildings, lettering, emblem, guardian statues, stone lions, banners with text'),
    'TX04-WALL-ST': (' Show only this one straight 4 m wall segment: both ends cut square to join the next segment, the tiled coping '
                     'running the full length; no gate, no corner, no buildings or trees behind it.',
                     'gate, doorway, corner, buildings behind, trees, lettering, decorative tiles with patterns of text'),
}
items = {}
for k, (scope, neg) in SCOPE.items():
    o = base['items'][k]['object'].replace(STYLE_FIX[1], STYLE_FIX[0], 1)
    items[k] = {'object': o + scope, 'layout': base['items'][k]['layout'], 'negative_extra': NEG_REVIEW + ', ' + neg}
out = {k: base[k] for k in ('style52', 'negative53', 'layout_single', 'layout_building')}
out['items'] = items
(HERE / 'prompts_tx04.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
print(len(items), 'items -> prompts_tx04.json')
