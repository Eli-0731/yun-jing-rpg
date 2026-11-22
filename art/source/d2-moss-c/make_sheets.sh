#!/bin/sh
# One review sheet per model (from the repo root, after render_reviews.sh): the picked three-view beside the grey model, the
# textured model with the 1.75 m figure, a close-up, wireframe and LOD0 / LOD1 / LOD2 → art/previews/d2-moss-c/<ID>/<ID>-sheet.jpg;
# then the D2 side-by-side (setting-view crops above, the D2 look-match renders below) → <ID>/d2/<ID>-d2-compare.jpg.
#   D2=<folder with the D2 V1–V6.png> sh art/source/d2-moss-c/make_sheets.sh [ID ...]
P=art/previews/d2-moss-c;S=art/source/d2-moss-c
pick(){ case $1 in DP06_01) echo DP06/DP06A-cand-3;; DP06_02) echo DP06/DP06B-cand-1;; DP06_03) echo DP06/DP06C-cand-3;; DP06_04) echo DP06/DP06D-cand-1;; DP06_05) echo DP06/DP06E-cand-1;; DP06_06) echo DP06/DP06F-cand-4;; DP07_01) echo DP07/DP07A-cand-1;; DP07_02) echo DP07/DP07B-cand-1;; DP07_03) echo DP07/DP07C-cand-1;; DP07_04) echo DP07/DP07D-cand-2;; DP07_05) echo DP07/DP07E-cand-1;; DP07_06) echo DP07/DP07F-cand-2;; DP13_01) echo DP13/DP13A-cand-1;; DP13_02) echo DP13/DP13B-cand-3;; DP13_03) echo DP13/DP13C-cand-2;; DP13_04) echo DP13/DP13D-cand-1;; DP08_01) echo DP08/DP08A-cand-3;; DP08_02) echo DP08/DP08B-cand-1;; DP08_03) echo DP08/DP08C-cand-1;; DP09_01) echo DP09/DP09A-cand-1;; DP09_02) echo DP09/DP09B-cand-1;; DP09_03) echo DP09/DP09C-cand-1;; DP09_04) echo DP09/DP09D-cand-2;; DP11_01) echo DP11/DP11A-cand-1;; DP11_02) echo DP11/DP11B-cand-1;; DP11_03) echo DP11/DP11C-cand-2;; DP10_01) echo DP10/DP10A-cand-1;; DP10_02) echo DP10/DP10B-cand-1;; DP10_03) echo DP10/DP10C-cand-1;; DP10_04) echo DP10/DP10D-cand-1;; DP12_01) echo DP12/DP12A-cand-1;; DP12_02) echo DP12/DP12B-cand-1;; DP12_03) echo DP12/DP12C-cand-1;; esac; }
IDS="${*:-DP06_01 DP06_02 DP06_03 DP06_04 DP06_05 DP06_06 DP07_01 DP07_02 DP07_03 DP07_04 DP07_05 DP07_06 DP13_01 DP13_02 DP13_03 DP13_04 DP08_01 DP08_02 DP08_03 DP09_01 DP09_02 DP09_03 DP09_04 DP11_01 DP11_02 DP11_03 DP10_01 DP10_02 DP10_03 DP10_04 DP12_01 DP12_02 DP12_03}"
for id in $IDS; do
  D=$P/$id
  python art/source/creekside-life-c/compose_sheet.py $D/$id-sheet.jpg "$id 審圖（三視圖 $(basename $(pick $id))、灰模、成品、近看、線框、LOD0–2）" 4 \
    "art/references/$(pick $id).png=三視圖（選用）" "$D/clay/$id-clay-threequarter.png=灰模" "$D/clay/$id-clay-close-threequarter.png=灰模近看" "$D/$id-threequarter.png=成品＋1.75 m 人形尺" \
    "$D/$id-front.png=正面" "$D/$id-side.png=側面" "$D/$id-close-threequarter.png=近看" "$D/$id-wire.png=線框" \
    "$D/$id-LOD0-nodetail-threequarter.png=LOD0" "$D/$id-LOD1-nodetail-threequarter.png=LOD1" "$D/$id-LOD2-nodetail-threequarter.png=LOD2" "$D/$id-back.png=背面"
  [ -n "$D2" ] && python $S/compose_d2.py "$D2" "$D/d2" "$D/d2/$id-d2-compare.jpg" $id
done
