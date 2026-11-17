#!/bin/sh
# One review sheet per model (from the repo root, after render_reviews.sh): the picked three-view beside the grey model, the
# textured model with the 1.75 m figure, a close-up, wireframe and LOD0 / LOD1 / LOD2 with Detail_* off →
# art/previews/yard-props-c/<ID>/<ID>-sheet.jpg (the LOD row doubles as the quality-tier check).
#   sh art/source/yard-props-c/make_sheets.sh [ID ...]
P=art/previews/yard-props-c;S=art/source/yard-props-c
pick(){ case $1 in
  YP01_*) echo YP01/YP01-cand-4;; YP02) echo YP02/YP02-cand-4;; YP03) echo YP03/YP03-cand-4;; YP04) echo YP04/YP04-cand-3;;
  YP05_*) echo YP05/YP05-cand-4;; YP06_*) echo YP06/YP06-cand-4;; YP07_*) echo YP07/YP07-cand-4;; YP08) echo YP08/YP08-cand-4;;
  YP09_*) echo YP09/YP09-cand-4;; YP10) echo YP10/YP10-cand-4;; YP11) echo YP11/YP11-cand-3;; YP12) echo YP12/YP12-cand-3;;
  YP13_01) echo YP13/YP13A-cand-3;; YP13_02) echo YP13/YP13B-cand-4;; esac; }
IDS="${*:-YP01_01 YP01_02 YP01_03 YP01_04 YP02 YP03 YP04 YP05_01 YP05_02 YP06_01 YP06_02 YP06_03 YP07_01 YP07_02 YP07_03 YP08 YP09_01 YP09_02 YP10 YP11 YP12 YP13_01 YP13_02}"
for id in $IDS; do
  D=$P/$id
  python $S/compose_sheet.py $D/$id-sheet.jpg "$id 審圖（三視圖 $(basename $(pick $id))、灰模、成品、近看、線框、LOD0–2 不含 Detail_）" 4 \
    "art/references/$(pick $id).png=三視圖（選用）" "$D/clay/$id-clay-threequarter.png=灰模" "$D/clay/$id-clay-close-threequarter.png=灰模近看" "$D/$id-threequarter.png=成品＋1.75 m 人形尺" \
    "$D/$id-front.png=正面" "$D/$id-side.png=側面" "$D/$id-close-threequarter.png=近看" "$D/$id-wire.png=線框" \
    "$D/$id-LOD0-nodetail-threequarter.png=LOD0" "$D/$id-LOD1-nodetail-threequarter.png=LOD1" "$D/$id-LOD2-nodetail-threequarter.png=LOD2" "$D/$id-back.png=背面"
done
