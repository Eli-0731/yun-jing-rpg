#!/bin/sh
# One review sheet per model (from the repo root, after render_reviews.sh): the picked three-view beside the grey model, the
# textured model with the 1.75 m figure, a close-up, wireframe and LOD0 / LOD1 / LOD2 → art/previews/d2-mushrooms-c/<ID>/<ID>-sheet.jpg;
# then the D2 side-by-side (setting-view crops above, the D2 look-match renders below) → <ID>/d2/<ID>-d2-compare.jpg.
#   D2=<folder with the D2 V1–V6.png> sh art/source/d2-mushrooms-c/make_sheets.sh [ID ...]
P=art/previews/d2-mushrooms-c;S=art/source/d2-mushrooms-c
pick(){ case $1 in DP01_01) echo DP01/DP01A-cand-1;; DP01_02) echo DP01/DP01B-cand-1;; DP01_03) echo DP01/DP01C-cand-1;; DP01_04) echo DP01/DP01D-cand-1;; DP02_01) echo DP02/DP02A-cand-3;; DP02_02) echo DP02/DP02B-cand-1;; DP02_03) echo DP02/DP02C-cand-1;; esac; }
IDS="${*:-DP01_01 DP01_02 DP01_03 DP01_04 DP02_01 DP02_02 DP02_03}"
for id in $IDS; do
  D=$P/$id
  python art/source/creekside-life-c/compose_sheet.py $D/$id-sheet.jpg "$id 審圖（三視圖 $(basename $(pick $id))、灰模、成品、近看、線框、LOD0–2）" 4 \
    "art/references/$(pick $id).png=三視圖（選用）" "$D/clay/$id-clay-threequarter.png=灰模" "$D/clay/$id-clay-close-threequarter.png=灰模近看" "$D/$id-threequarter.png=成品＋1.75 m 人形尺" \
    "$D/$id-front.png=正面" "$D/$id-side.png=側面" "$D/$id-close-threequarter.png=近看" "$D/$id-wire.png=線框" \
    "$D/$id-LOD0-nodetail-threequarter.png=LOD0" "$D/$id-LOD1-nodetail-threequarter.png=LOD1" "$D/$id-LOD2-nodetail-threequarter.png=LOD2" "$D/$id-back.png=背面"
  [ -n "$D2" ] && python $S/compose_d2.py "$D2" "$D/d2" "$D/d2/$id-d2-compare.jpg" $id
done
