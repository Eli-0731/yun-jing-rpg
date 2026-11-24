#!/bin/sh
# One review sheet per model (from the repo root, after render_reviews.sh): the picked three-view beside the grey model, the
# textured model with the 1.75 m figure, a close-up, wireframe and LOD0 / LOD1 / LOD2 with Detail_* off →
# art/previews/undergrowth-c/<ID>/<ID>-sheet.jpg (the LOD row doubles as the quality-tier check).
#   sh art/source/undergrowth-c/make_sheets.sh [ID ...]
P=art/previews/undergrowth-c;S=art/source/undergrowth-c
pick(){ case $1 in SH01) echo SH01/SH01-cand-2;; SH02) echo SH02/SH02-cand-2;; SP01) echo SP01/SP01-cand-3;; UG01) echo UG01/UG01-cand-1;; UG02) echo UG02/UG02-cand-1;; UG03) echo UG03/UG03-cand-2;; UG04) echo UG04/UG04-cand-1;; UG05*) echo UG05/UG05-cand-3;; UG06*) echo UG06/UG06-cand-5;; esac; }
IDS="${*:-SH01}"
for id in $IDS; do
  D=$P/$id
  python art/source/yard-props-c/compose_sheet.py $D/$id-sheet.jpg "$id 審圖（三視圖 $(basename $(pick $id))、灰模、成品、近看、線框、LOD0–2 不含 Detail_）" 4 \
    "art/references/$(pick $id).png=三視圖（選用）" "$D/clay/$id-clay-threequarter.png=灰模" "$D/clay/$id-clay-close-threequarter.png=灰模近看" "$D/$id-threequarter.png=成品＋1.75 m 人形尺" \
    "$D/$id-front.png=正面" "$D/$id-side.png=側面" "$D/$id-close-threequarter.png=近看" "$D/$id-wire.png=線框" \
    "$D/$id-LOD0-nodetail-threequarter.png=LOD0" "$D/$id-LOD1-nodetail-threequarter.png=LOD1" "$D/$id-LOD2-nodetail-threequarter.png=LOD2" "$D/$id-back.png=背面"
done
