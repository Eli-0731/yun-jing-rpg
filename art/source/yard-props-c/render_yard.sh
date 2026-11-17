#!/bin/sh
# The whole of batch A set out as one yard, against A1 setting view V6 (work pack §1 "全包檢查"). From the repo root:
#   BL=<blender.exe> sh art/source/yard-props-c/render_yard.sh [eevee]
# Backdrop: B's lived-in house VL04_DiligentFamilyHouse (needs `git lfs pull` of its GLB), turned so its front faces +X, its own small props (Detail_Small: drying rack, jars) hidden;
# the yard is x > 0 in front of its porch. Camera at eye height 1.0 m from the lane to the south-east, as in V6.
# Writes art/previews/yard-props-c/compare/YP-yard-{eye,top}-cam.png and YP-yard-vs-V6.jpg (beside the setting view).
BL="${BL:?set BL to blender.exe}";E=art/exports/yard-props-c;P=art/previews/yard-props-c/compare;EN="${1:-cycles}"
m(){ cygpath -m "$1" 2>/dev/null || echo "$1"; }
H=art/exports/village-houses-b/VL04_DiligentFamilyHouse/VL04_DiligentFamilyHouse_v001.glb
# id  x  y  yaw  [z]
LAY="VL04 -3.9 0 90
YP01_01 4.0 1.6 0
YP01_02 3.38 1.6 0
YP01_03 4.0 1.6 0
YP01_04 4.62 1.6 0
YP02 3.6 4.3 0
YP03 0.55 -2.2 0
YP04 1.25 -2.6 30
YP05_01 0.65 2.2 90
YP05_02 1.4 1.3 10
YP06_01 2.2 -1.2 5
YP06_02 2.5 -3.9 75
YP06_03 2.3 0.3 10
YP07_01 0.40 3.3 0
YP07_02 0.45 3.75 20
YP07_03 0.85 3.55 -30
YP08 -1.10 -3.55 90 1.3
YP09_01 1.6 -3.7 -10
YP09_02 0.6 -3.4 90
YP10 5.3 -0.7 110
YP11 3.3 -2.6 15
YP12 0.75 4.6 0
YP13_01 2.2 5.0 0
YP13_02 3.5 -4.0 40"
G="";A=""
while read id x y yaw z; do
  if [ "$id" = VL04 ]; then f=$H; else f=$E/${id}_v001.glb; fi
  G="$G$(m $f),";A="$A$x,$y,$yaw,${z:-0};"
done <<EOF
$LAY
EOF
G=${G%,};A=${A%;};mkdir -p $P
EV="";[ "$EN" = eevee ] && EV="--engine eevee"
for c in "4.8,-6.0,1.0,1.1,0.4,0.95,18:eye" "2.0,-0.01,24,2.0,0,0,28:top"; do
  MSYS_NO_PATHCONV=1 "$BL" -b --factory-startup -P "$(m art/source/creekside-life-c/render_wl.py)" -- --glb "$G" --at="$A" --out "$(m $P)" \
    --tag YP-yard-${c##*:} --views "" --no-ruler --hide VL04_DiligentFamilyHouse_Detail --samples 96 --res 1536x1024 --ground .46,.41,.34 $EV --cam "${c%:*}" 2>&1 | grep -E "Error|Traceback|RIG_DONE"
done
