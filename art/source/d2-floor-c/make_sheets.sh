#!/bin/sh
# One review sheet per model (from the repo root, after render_reviews.sh): the picked three-view beside the grey model, the
# textured model with the 1.75 m figure, a close-up, wireframe and LOD0 / LOD1 / LOD2 → art/previews/d2-floor-c/<ID>/<ID>-sheet.jpg;
# then the D2 side-by-side (setting-view crops above, the D2 look-match renders below) → <ID>/d2/<ID>-d2-compare.jpg.
#   D2=<folder with the D2 V1–V6.png> sh art/source/d2-floor-c/make_sheets.sh [ID ...]
P=art/previews/d2-floor-c;S=art/source/d2-floor-c
pick(){ case $1 in DP17_01) echo DP17/DP17A-cand-4;; DP17_02) echo DP17/DP17B-cand-3;; DP17_03) echo DP17/DP17C-cand-2;; DP17_04) echo DP17/DP17D-cand-1;; DP17_05) echo DP17/DP17E-cand-1;; DP17_06) echo DP17/DP17F-cand-1;; DP17_07) echo DP17/DP17G-cand-2;; DP17_08) echo DP17/DP17H-cand-1;; DP18_01) echo DP18/DP18A-cand-3;; DP18_02) echo DP18/DP18B-cand-3;; DP18_03) echo DP18/DP18C-cand-1;; DP19_01) echo DP19/DP19A-cand-2;; DP19_02) echo DP19/DP19B-cand-2;; DP19_03) echo DP19/DP19C-cand-2;; DP14_01) echo DP14/DP14A-cand-1;; DP14_02) echo DP14/DP14B-cand-2;; DP14_03) echo DP14/DP14C-cand-2;; DP14_04) echo DP14/DP14D-cand-4;; DP14_05) echo DP14/DP14E-cand-1;; DP14_06) echo DP14/DP14F-cand-2;; DP14_07) echo DP14/DP14G-cand-2;; DP14_08) echo DP14/DP14H-cand-3;; DP15_01) echo DP15/DP15A-cand-1;; DP15_02) echo DP15/DP15B-cand-3;; DP15_03) echo DP15/DP15C-cand-1;; DP15_04) echo DP15/DP15D-cand-1;; DP15_05) echo DP15/DP15E-cand-1;; DP15_06) echo DP15/DP15F-cand-1;; DP16_01) echo DP16/DP16A-cand-1;; DP16_02) echo DP16/DP16B-cand-1;; DP16_03) echo DP16/DP16C-cand-1;; DP16_04) echo DP16/DP16D-cand-1;; DP16_05) echo DP16/DP16E-cand-1;; DP16_06) echo DP16/DP16F-cand-1;; DP20_01) echo DP20/DP20A-cand-1;; DP20_02) echo DP20/DP20B-cand-7;; DP20_03) echo DP20/DP20C-cand-1;; DP20_04) echo DP20/DP20D-cand-5;; DP20_05) echo DP20/DP20E-cand-8;; DP20_06) echo DP20/DP20F-cand-1;; DP21_01) echo DP21/DP21A-cand-1;; DP21_02) echo DP21/DP21B-cand-1;; DP21_03) echo DP21/DP21C-cand-1;; DP21_04) echo DP21/DP21D-cand-1;; DP22_01) echo DP22/DP22A-cand-1;; esac; }
IDS="${*:-DP17_01 DP17_02 DP17_03 DP17_04 DP17_05 DP17_06 DP17_07 DP17_08 DP18_01 DP18_02 DP18_03 DP19_01 DP19_02 DP19_03 DP14_01 DP14_02 DP14_03 DP14_04 DP14_05 DP14_06 DP14_07 DP14_08 DP15_01 DP15_02 DP15_03 DP15_04 DP15_05 DP15_06 DP16_01 DP16_02 DP16_03 DP16_04 DP16_05 DP16_06 DP20_01 DP20_02 DP20_03 DP20_04 DP20_05 DP20_06 DP21_01 DP21_02 DP21_03 DP21_04 DP22_01}"
for id in $IDS; do
  D=$P/$id
  python art/source/creekside-life-c/compose_sheet.py $D/$id-sheet.jpg "$id 審圖（三視圖 $(basename $(pick $id))、灰模、成品、近看、線框、LOD0–2）" 4 \
    "art/references/$(pick $id).png=三視圖（選用）" "$D/clay/$id-clay-threequarter.png=灰模" "$D/clay/$id-clay-close-threequarter.png=灰模近看" "$D/$id-threequarter.png=成品＋1.75 m 人形尺" \
    "$D/$id-front.png=正面" "$D/$id-side.png=側面" "$D/$id-close-threequarter.png=近看" "$D/$id-wire.png=線框" \
    "$D/$id-LOD0-nodetail-threequarter.png=LOD0" "$D/$id-LOD1-nodetail-threequarter.png=LOD1" "$D/$id-LOD2-nodetail-threequarter.png=LOD2" "$D/$id-back.png=背面"
  [ -n "$D2" ] && python $S/compose_d2.py "$D2" "$D/d2" "$D/d2/$id-d2-compare.jpg" $id
done
