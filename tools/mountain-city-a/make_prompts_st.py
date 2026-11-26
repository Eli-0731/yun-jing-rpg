"""ST01-ST06 three-view prompts (11/08 package A part 2, mountain-city street furniture). Object sentences from the 11/08
package (via prompts.json) + single-object Layout + 5.2; negatives 5.3 plus what PR #80 / #90 / #98 taught: a Chinese
Song-dynasty wording, a scope sentence so a sheet shows only the one module, and the core team's Japanese / European negatives.

    python tools/mountain-city-a/make_prompts_st.py          -> tools/mountain-city-a/prompts_st.json
    python tools/mountain-city-a/gen_threeviews.py --prompts prompts_st.json ST01 ST02 ST03 ST04 ST05 ST06
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
base = json.loads((HERE / 'prompts.json').read_text(encoding='utf-8'))
NEG_REVIEW = ('Japanese style, toro stone lantern, ishidoro, torii, shimenawa rope, noren curtain, kanji or any lettering, '
              'European gothic, Victorian street furniture, cast-iron park bench, modern concrete, plastic, gold ornament')
SCOPE = {
    'ST01': ' Chinese Song-dynasty mountain city style, a square shaft (not round), a small hip-roofed stone lamp house with '
            'open window panels on four sides, shown alone; no wall, no street, no people, no writing.',
    'ST02': ' Chinese Song-dynasty style oval lanterns of oiled paper with dark wooden top and bottom caps and short red '
            'tassels, evenly spaced on one rope, shown as a single module with the hooks at both ends; no buildings, '
            'no poles, no people, no writing or symbols on the lanterns.',
    'ST03': ' Chinese Song-dynasty mountain city style, show the three modules side by side as separate pieces on the same '
            'ground line; no street, no buildings, no water spouts, no people.',
    'ST04': ' Chinese Song-dynasty mountain city style, one bench only, plain rectangular slab with a softened front edge, '
            'two blocky supports with a simple recessed panel; no backrest, no armrests, no people.',
    'ST05': ' Chinese Song-dynasty shop banners, the three banners side by side at the same scale, each hanging from its own '
            'short horizontal rod with a cord loop; completely blank cloth, no characters, no symbols, no patterns, no people.',
    'ST06': ' Chinese Song-dynasty mountain city style, show the three modules side by side as separate pieces on the same '
            'ground line; plain horizontal rails with simple square balusters, no platform, no cliff, no people.',
}
NEG_EXTRA = {'ST02': ', Japanese chochin with black lettering, round white festival lantern with kamon crest, electric bulbs',
             'ST05': ', noren split curtain, flags with emblems, any writing'}
items = {}
for k in SCOPE:
    items[k] = {'object': base['items'][k]['object'] + SCOPE[k], 'layout': 'single',
                'negative_extra': NEG_REVIEW + NEG_EXTRA.get(k, '')}
out = {k: base[k] for k in ('style52', 'negative53', 'layout_single', 'layout_building')}
out['items'] = items
(HERE / 'prompts_st.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
print(len(items), 'items -> prompts_st.json')
