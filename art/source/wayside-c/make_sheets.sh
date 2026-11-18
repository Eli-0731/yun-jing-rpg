#!/bin/sh
# One review sheet per model (from the repo root, after render_reviews.sh): the picked three-view beside the grey model, the
# textured model with the 1.75 m figure, a close-up, wireframe and LOD0 / LOD1 / LOD2 with Detail_* off →
# art/previews/wayside-c/<ID>/<ID>-sheet.jpg (the LOD row doubles as the quality-tier check).
#   sh art/source/wayside-c/make_sheets.sh [ID ...]
P=art/previews/wayside-c;S=art/source/wayside-c
pick(){ case $1 in
  WS01_01) echo WS01/WS01A-cand-1;; WS01_02) echo WS01/WS01B-cand-3;; WS02_01) echo WS02/WS02A-cand-4;; WS02_02) echo WS02/WS02B-cand-1;;
  WS03) echo WS03/WS03-cand-2;; WS04_*) echo WS04/WS04-cand-4;; WS05_*) echo WS05/WS05-cand-1;; WS06) echo WS06/WS06-cand-4;; esac; }
IDS="${*:-WS01_01 WS01_02 WS02_01 WS02_02 WS03 WS04_01 WS04_02 WS05_01 WS05_02 WS06}"
for id in $IDS; do
  D=$P/$id
  python art/source/yard-props-c/compose_sheet.py $D/$id-sheet.jpg "$id 審圖（三視圖 $(basename $(pick $id))、灰模、成品、近看、線框、LOD0–2 不含 Detail_）" 4 \
    "art/references/$(pick $id).png=三視圖（選用）" "$D/clay/$id-clay-threequarter.png=灰模" "$D/clay/$id-clay-close-threequarter.png=灰模近看" "$D/$id-threequarter.png=成品＋1.75 m 人形尺" \
    "$D/$id-front.png=正面" "$D/$id-side.png=側面" "$D/$id-close-threequarter.png=近看" "$D/$id-wire.png=線框" \
    "$D/$id-LOD0-nodetail-threequarter.png=LOD0" "$D/$id-LOD1-nodetail-threequarter.png=LOD1" "$D/$id-LOD2-nodetail-threequarter.png=LOD2" "$D/$id-back.png=背面"
done
