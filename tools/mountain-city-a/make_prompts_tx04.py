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
    'TX04-WALL-CO': (' Show only this one L-shaped corner wall: two 4 m arms meeting at ninety degrees around a dark cedar corner post on a '
                     'stone base, cut-stone footing and lime plaster on both arms, the tiled coping turning the corner continuously; both arm '
                     'ends cut square to join the next segment; posts are dark timber, not red; no gate, no buildings or trees behind.',
                     'gate, doorway, buildings behind, trees, red columns, lettering, decorative tiles with patterns of text'),
    'TX04-WALL-DO': (' Show only this one 4 m wall segment that ends at a doorway: one end finished with a fitted dark cedar jamb post on a '
                     'stone base and a short return of the coping, the other end cut square to join the next segment; the opening itself, '
                     'any door leaf and any gate roof are not part of it; posts are dark timber, not red.',
                     'door leaves, full gatehouse, archway, roof over the door, buildings behind, trees, red columns, lettering'),
    'TX04-HALL': (' Show only this one main hall: a single-storey hall on a raised granite platform with front steps, a front verandah '
                  'of dark cedar columns on stone bases, timber doors and windows with vertical slats (no square grids), plastered end '
                  'walls, a blank framed entrance board, bracket sets under deep eaves and a hip-and-gable roof; columns are dark timber, '
                  'red lacquer only on the central door leaves; no courtyard walls, no side buildings, no lettering anywhere.',
                  'side wings, courtyard walls, lettering, couplets, stone lions, banners, multi-storey pagoda, red columns, square grid windows'),
    'TX04-SIDE': (' Show only this one side wing: a single-storey building on a low stone base, dark cedar posts and beams, lime '
                  'plastered walls over a stone dado, narrow windows with vertical slats (no square grids), one plain door, a simple '
                  'tiled roof with modest eaves; posts are dark timber, not red; no main hall, no courtyard walls, no lettering.',
                  'main hall, courtyard walls, square grid windows, shoji, red columns, lettering, banners'),
    'TX04-PAVE': (' Show only this one flat 4 m by 4 m courtyard paving bay: fitted pale granite slabs laid in staggered courses inside '
                  'a narrow border of long kerb stones, edges worn and slightly uneven, a little moss and grass in a few joints; nothing '
                  'standing on it.',
                  'buildings, walls, stairs, trees, people, lettering, mosaic patterns, circular patterns, tiles with text'),
    'TX04-STEPS': (' Show only this one standalone stone stair: 4 m wide and 2 m deep, five shallow worn granite treads between two '
                   'sloping cheek stones, no handrail, nothing built on top or behind it.',
                   'buildings, gate, walls, handrails, balustrade, lettering, statues'),
}
items = {}
for k, (scope, neg) in SCOPE.items():
    o = base['items'][k]['object'].replace(STYLE_FIX[1], STYLE_FIX[0], 1)
    items[k] = {'object': o + scope, 'layout': base['items'][k]['layout'], 'negative_extra': NEG_REVIEW + ', ' + neg}
out = {k: base[k] for k in ('style52', 'negative53', 'layout_single', 'layout_building')}
out['items'] = items
(HERE / 'prompts_tx04.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
print(len(items), 'items -> prompts_tx04.json')
