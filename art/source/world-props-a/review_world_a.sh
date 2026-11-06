#!/bin/sh
# Review renders for the 11/03 package A world models. Run from the repo root:
#   BLENDER=<blender.exe> sh art/source/world-props-a/review_world_a.sh RK09 [WM08A ...]
# Per item: four views with the 1.75 m figure, wireframe, and LOD0 | LOD1 side by side with Detail_* off (quality-tiers-v1 §4).
set -e
B="${BLENDER:?set BLENDER to blender.exe}";RIG=art/source/world-props-a/render_world_a.py
E=art/exports/world-props-a;P=art/previews/world-props-a
for k in "$@"; do
  "$B" -b --factory-startup -P "$RIG" -- --glb $E/$k.fbx --out $P/$k --tag $k --views front,side,back,threequarter --wire >/dev/null 2>&1 || echo "render failed: $k"
  for L in 0 1; do
    "$B" -b --factory-startup -P "$RIG" -- --glb $E/$k.fbx --out $P/$k --tag $k-LOD$L-nodetail --views threequarter --lod $L --no-detail --no-ruler --res 960x720 >/dev/null 2>&1 || echo "lod render failed: $k $L"
  done
  python - "$P/$k" "$k" <<'PY'
import sys
from PIL import Image
d,k=sys.argv[1],sys.argv[2]
a=Image.open(f'{d}/{k}-LOD0-nodetail-threequarter.png');b=Image.open(f'{d}/{k}-LOD1-nodetail-threequarter.png')
s=Image.new('RGB',(a.width+b.width,a.height));s.paste(a,(0,0));s.paste(b,(a.width,0));s.save(f'{d}/{k}-LOD0-vs-LOD1.png')
PY
done
