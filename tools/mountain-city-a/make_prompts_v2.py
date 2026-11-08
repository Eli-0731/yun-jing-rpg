"""Second-round three-view prompts for MC01 (core-team review on PR #80, 2026-11-08): the object sentences given in the review
replace the old ones for SF01-03, HM01-03, DT01 and DT03; style52 and the layouts stay as in prompts.json.

- Every item adds the review's negative list (Japanese / European look) after the existing 5.3 negatives.
- From the Codex prompt review (PR80-prompt-review-for-Claude.md), where it does not conflict with the core team's text:
  one scope sentence per module family so the sheet shows only that layer, and per-family negatives.
- Variants keep their original differences (SF02 side lattice, SF03 corner; HM window counts).

    python tools/mountain-city-a/make_prompts_v2.py      -> tools/mountain-city-a/prompts_v2.json
    python tools/mountain-city-a/gen_threeviews.py --prompts prompts_v2.json --sub v2 MC01-SF01 ...
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
base = json.loads((HERE / 'prompts.json').read_text(encoding='utf-8'))
NEG_REVIEW = ('Japanese architecture, machiya, noren, shoji, chochin round paper lantern, toro stone lantern, torii, '
              'Tudor half-timbering, European timber framing, diagonal X bracing')

SF = ('Three-view orthographic turnaround sheet of an open timber shopfront bay in a Chinese Song-dynasty style mountain town, '
      'about 4 m wide, 4 m deep and 3 m tall, with a three-metre open front veranda, one single unbroken short blank dark indigo '
      'cloth valance under the front beam, one tall blank swallow-tailed cloth shop banner hanging from a timber arm beside the post, '
      'small hexagonal dark bronze-frame lanterns with blank paper panels hanging from the beam ends, made of aged dark-brown cedar, '
      'warm-grey granite and dark bronze joints, showing hand-worn edges, rain streaks and repaired timber joints, no writing.')
SF_VAR = {
    'MC01-SF01': '',
    'MC01-SF02': ' Both sides of the veranda have timber lattice screens above solid lower panels; the front stays open.',
    'MC01-SF03': ' It is a corner bay: the front and the right side are both open shopfront faces meeting at one shared corner post.',
}
SF_SCOPE = (' The open veranda stays inside the 4 m footprint and the rear 1 m is a dark closed room with a doorway. Show this one '
            'ground-floor module only, ending at its top beam frame: no roof, no upper storey, no stone foundation block, no shelves '
            'or merchandise.')
HM = ('Three-view orthographic turnaround sheet of a plaster-walled upper home bay in a Chinese Song-dynasty style mountain town, '
      'about 4 m wide, 4 m deep and 3 m tall, with an exposed chuandou timber frame of straight vertical posts and horizontal tie beams '
      'dividing the lime plaster into calm rectangular panels, no diagonal members, narrow recessed windows with straight vertical '
      'wooden bars backed by blank paper, made of aged dark-brown cedar, lime plaster and dark bronze joints, showing soft rain streaks '
      'and a few subtle plaster repairs along the posts, no writing.')
HM_VAR = {
    'MC01-HM01': ' Two narrow windows on the front face.',
    'MC01-HM02': ' One narrow recessed window on the front face.',
    'MC01-HM03': ' It is a corner bay with one narrow window on the front face and one on the right face.',
}
HM_SCOPE = (' Show this one upper storey only, with level bottom and top beam frames: no roof, no eaves, no lower storey, '
            'no projecting brackets or balcony.')
DT = {
    'MC01-DT01': ('Three-view orthographic turnaround sheet of a Chinese mountain town street lantern, about 0.6 m wide and 2.5 m tall, '
                  'with a stepped warm-grey granite pedestal, a slim dark bronze post, a hexagonal dark bronze frame with thin vertical '
                  'bars around blank warm paper panels, and a small bronze cap with gently upturned corners, verdigris in the joints, '
                  'hand-worn edges, no writing, no wooden lattice.'),
    'MC01-DT03': ('Three-view orthographic turnaround sheet of a small Chinese hanging lantern, about 0.4 m wide and 0.7 m tall, with a '
                  'hexagonal dark bronze frame, thin vertical bars around blank warm paper panels, a small bronze cap with gently '
                  'upturned corners, a hanging ring and a short dark cord tassel, verdigris in the joints, no writing, no wooden lattice.'),
}
NEG_FAMILY = {'SF': 'roof, roof tiles, upper storey, foundation block, furnished interior, merchandise, shelving, round white paper lanterns, split curtain panels',
              'HM': 'roof, roof tiles, eaves, lower storey, foundation block, balcony, projecting brackets, square grid windows',
              'DT': 'wooden lantern frame, wooden lattice, stone toro lantern'}

items = {}
for k, v in SF_VAR.items(): items[k] = {'object': SF + v + SF_SCOPE, 'layout': base['items'][k]['layout'], 'family': 'SF'}
for k, v in HM_VAR.items(): items[k] = {'object': HM + v + HM_SCOPE, 'layout': base['items'][k]['layout'], 'family': 'HM'}
for k, v in DT.items(): items[k] = {'object': v, 'layout': base['items'][k]['layout'], 'family': 'DT'}
out = {k: base[k] for k in ('style52', 'layout_single', 'layout_building')}
out['negative53'] = base['negative53']
out['items'] = {k: {**v, 'negative_extra': NEG_REVIEW + ', ' + NEG_FAMILY[v['family']]} for k, v in items.items()}
(HERE / 'prompts_v2.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
print(len(items), 'items -> prompts_v2.json')
