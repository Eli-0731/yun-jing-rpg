#!/bin/sh
# The whole of batch C set out along a stretch of road (work pack §1 "全包檢查": C 批擺在一段路邊一張). From the repo root:
#   BL=<blender.exe> sh art/source/wayside-c/render_road.sh [eevee]
# Road: two of B's straight path pieces FP01_PathStraight (6 × 2 m each, needs `git lfs pull` of its GLB) along X; A2 has no setting view,
# so the camera stands on the road at eye height 1.6 m looking along it.
# Writes art/previews/wayside-c/compare/WS-road-{eye,top}-cam.png.
BL="${BL:?set BL to blender.exe}";E=art/exports/wayside-c;P=art/previews/wayside-c/compare;EN="${1:-cycles}"
m(){ cygpath -m "$1" 2>/dev/null || echo "$1"; }
H=art/exports/forest-paths-b/FP01_PathStraight/FP01_PathStraight_v001.glb
# id  x  y  yaw  [z]
LAY="FP01 -3.0 0 0
FP01 3.0 0 0
WS03 -3.0 -1.75 20
WS04_01 -1.5 1.40 0
WS04_02 -1.05 1.62 30
WS01_01 -2.2 1.45 0
WS01_02 0.6 -1.45 0
WS02_01 2.4 1.85 0
WS02_02 -0.5 -1.35 0
WS05_01 3.9 -2.25 10
WS05_02 5.2 -1.55 80
WS06 1.0 1.55 5"
G="";A=""
while read id x y yaw z; do
  if [ "$id" = FP01 ]; then f=$H; else f=$E/${id}_v001.glb; fi
  G="$G$(m $f),";A="$A$x,$y,$yaw,${z:-0};"
done <<EOF
$LAY
EOF
G=${G%,};A=${A%;};mkdir -p $P
EV="";[ "$EN" = eevee ] && EV="--engine eevee"
for c in "-6.4,0.4,1.6,1.4,0.0,0.35,30:eye" "0.5,-0.01,22,0.5,0,0,30:top"; do
  MSYS_NO_PATHCONV=1 "$BL" -b --factory-startup -P "$(m art/source/creekside-life-c/render_wl.py)" -- --glb "$G" --at="$A" --out "$(m $P)" \
    --tag WS-road-${c##*:} --views "" --no-ruler --samples 96 --res 1536x1024 --ground .46,.41,.34 $EV --cam="${c%:*}" 2>&1 | grep -E "Error|Traceback|RIG_DONE"
done
