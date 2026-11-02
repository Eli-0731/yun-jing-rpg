#!/bin/sh
# Review renders for C's modelling-basics models (Eli-0731). Run from the repo root:
#   BLENDER=<blender.exe> sh art/source/modelling-basics-c/render_reviews.sh [BM01]
# In Git Bash also set MSYS_NO_PATHCONV=1 so the --cam / --at values reach Blender untouched.
# Work pack §1.8: four views with a 1.75 m figure, one side-by-side with the named earlier work;
# quality tiers §4: the same angle with LOD0 and LOD1, Detail_* switched off.
set -e
B="${BLENDER:?set BLENDER to blender.exe}";SRC=art/source/modelling-basics-c;RIG=$SRC/render_basics.py
E=art/exports/modelling-basics-c;P=art/previews/modelling-basics-c;WR=art/exports/qingxi-water-report-c
r(){ "$B" -b --factory-startup -P "$RIG" -- "$@" >/dev/null 2>&1 || echo "render failed: $*"; }
ITEMS="${1:-BM01}"
case " $ITEMS " in *" BM01 "*)
  # 1. four views + wireframe, each crate
  for k in BM01_01 BM01_02 BM01_03; do r --glb $E/$k.glb --out $P/BM01/$k --tag $k --views front,side,back,threequarter --wire; done
  # 2. the set as in the reference sheet (front, side, back), and a close look in the afternoon light
  for v in front side back threequarter; do
    r --glb $E/BM01_01.glb,$E/BM01_02.glb,$E/BM01_03.glb --at="-1.35,0,0;-.55,0,0;.55,0,0" --out $P/BM01/set --tag BM01-set --views $v --light afternoon
  done
  r --glb $E/BM01_01.glb,$E/BM01_02.glb,$E/BM01_03.glb --at="-1.0,.25,12;-.15,-.45,-8;.75,.35,4" --out $P/BM01/closeup --tag BM01-street-group --views "" --no-ruler --light afternoon --cam=.6,-2.4,1.25,0,0,.25,38 --res 1600x1000
  r --glb $E/BM01_02.glb --out $P/BM01/closeup --tag BM01_02-rope-knot --views "" --no-ruler --light afternoon --cam=.45,-.9,.5,.18,-.2,.24,50 --res 1200x900
  r --glb $E/BM01_03.glb --out $P/BM01/closeup --tag BM01_03-renewed-board --views "" --no-ruler --light afternoon --cam=-.35,-1.25,.55,0,-.3,.28,45 --res 1400x900
  # 3. side by side with C07 (the repair toolbox from the water-report pack), as the work pack asks
  r --glb $E/BM01_01.glb,$E/BM01_02.glb,$E/BM01_03.glb,$WR/C07.glb --at="-1.5,0,0;-.7,0,0;.45,0,0;1.6,0,0" --out $P/BM01/compare --tag BM01-vs-C07 --views front,threequarter
  # 4. quality tiers: LOD0 vs LOD1 from the same angle, Detail_* off (the FBX carries every LOD)
  for k in BM01_01 BM01_02 BM01_03; do for L in 0 1; do
    r --glb $E/$k.fbx --lod $L --hide Detail_ --out $P/BM01/lod --tag $k-LOD$L-nodetail --views threequarter --no-ruler --res 960x720
  done; done
  python "$SRC/compose_lod.py" $P/BM01/lod BM01_01 BM01_02 BM01_03
;; esac
echo REVIEWS_DONE
