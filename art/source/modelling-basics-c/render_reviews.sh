#!/bin/sh
# Review renders for C's modelling-basics models (Eli-0731). Run from the repo root:
#   BLENDER=<blender.exe> sh art/source/modelling-basics-c/render_reviews.sh [BM01 BM02 ... CLAY]
# In Git Bash also set MSYS_NO_PATHCONV=1 so the --cam / --at values reach Blender untouched.
# Work pack §1.8: four views with a 1.75 m figure, one side-by-side with the named earlier work;
# quality tiers §4: the same angle with LOD0 and LOD1, Detail_* switched off.
set -e
B="${BLENDER:?set BLENDER to blender.exe}";SRC=art/source/modelling-basics-c;RIG=$SRC/render_basics.py
E=art/exports/modelling-basics-c;P=art/previews/modelling-basics-c;WR=art/exports/qingxi-water-report-c
r(){ "$B" -b --factory-startup -P "$RIG" -- "$@" >/dev/null 2>&1 || echo "render failed: $*"; }
ITEMS="${*:-BM01}"
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
  # 3. side by side with C07 (the repair toolbox from the water-report pack, v001 and v002), same light, same scale, as the work pack
  #    and the #67 review ask: textured and clay (one grey, no maps), plus a close look at the wood next to C07 v002
  C7="$WR/C07.glb,$WR/v002/C07_v002.glb";AT="-1.5,0,0;-.7,0,0;.45,0,0;1.45,0,0;1.95,0,0"
  r --glb $E/BM01_01.glb,$E/BM01_02.glb,$E/BM01_03.glb,$C7 --at="$AT" --out $P/BM01/compare --tag BM01-vs-C07 --views front,threequarter
  r --glb $E/BM01_01.glb,$E/BM01_02.glb,$E/BM01_03.glb,$C7 --at="$AT" --out $P/BM01/compare --tag BM01-vs-C07-clay --views front,threequarter --clay
  r --glb $E/BM01_03.glb,$WR/v002/C07_v002.glb --at="-.35,0,0;.6,0,0" --out $P/BM01/compare --tag BM01_03-vs-C07v002-close --views "" --no-ruler --cam=-.5,-1.9,1.05,.1,0,.2,36 --res 1600x1000
  # 4. quality tiers: LOD0 vs LOD1 from the same angle, Detail_* off (the FBX carries every LOD)
  for k in BM01_01 BM01_02 BM01_03; do for L in 0 1; do
    r --glb $E/$k.fbx --lod $L --hide Detail_ --out $P/BM01/lod --tag $k-LOD$L-nodetail --views threequarter --no-ruler --res 960x720
  done; done
  python "$SRC/compose_lod.py" $P/BM01/lod BM01_01 BM01_02 BM01_03
;; esac
case " $ITEMS " in *" BM02 "*)
  for k in BM02_01 BM02_02; do r --glb $E/$k.glb --out $P/BM02/$k --tag $k --views front,side,back,threequarter --wire; done
  for v in front side back; do r --glb $E/BM02_01.glb,$E/BM02_02.glb --at="-.3,0,0;.3,0,0" --out $P/BM02/set --tag BM02-set --views $v --light afternoon; done
  r --glb $E/BM02_02.glb --out $P/BM02/closeup --tag BM02_02-head-groove --views "" --no-ruler --light afternoon --cam=.2,-.75,1.25,0,0,.95,50 --res 1200x900
  r --glb $E/BM02_01.glb,$E/BM02_02.glb --at="-.25,.1,20;.3,-.1,-15" --out $P/BM02/closeup --tag BM02-roadside --views "" --no-ruler --light afternoon --cam=.9,-2.0,1.2,0,0,.45,35 --res 1400x1000
  # side by side with C05 (the moisture sign board from the water-report pack), as the work pack asks
  r --glb $E/BM02_01.glb,$E/BM02_02.glb,$WR/C05.glb --at="-.5,0,0;0,0,0;.7,0,0" --out $P/BM02/compare --tag BM02-vs-C05 --views front,threequarter
  for k in BM02_01 BM02_02; do for L in 0 1; do
    r --glb $E/$k.fbx --lod $L --hide Detail_ --out $P/BM02/lod --tag $k-LOD$L-nodetail --views threequarter --no-ruler --res 960x720
  done; done
  python "$SRC/compose_lod.py" $P/BM02/lod BM02_01 BM02_02
;; esac
case " $ITEMS " in *" BM03 "*)
  for k in BM03_01 BM03_02 BM03_03; do r --glb $E/$k.glb --out $P/BM03/$k --tag $k --views front,side,back,threequarter --wire; done
  for v in front side back threequarter; do r --glb $E/BM03_01.glb,$E/BM03_02.glb,$E/BM03_03.glb --at="-.75,0,0;-.2,0,0;.45,0,0" --out $P/BM03/set --tag BM03-set --views $v --light afternoon; done
  r --glb $E/BM03_03.glb --out $P/BM03/closeup --tag BM03_03-rim-glaze --views "" --no-ruler --light afternoon --cam=.35,-.95,1.15,0,0,.6,45 --res 1200x900
  r --glb $E/BM03_01.glb,$E/BM03_02.glb,$E/BM03_03.glb --at="-.45,.15,30;-.05,-.25,-20;.4,.1,10" --out $P/BM03/closeup --tag BM03-street-group --views "" --no-ruler --light afternoon --cam=.7,-2.3,1.1,0,0,.35,38 --res 1400x1000
  # side by side with C03 (the water bucket from the water-report pack), as the work pack asks
  r --glb $E/BM03_01.glb,$E/BM03_02.glb,$E/BM03_03.glb,$WR/C03.glb --at="-1.1,0,0;-.55,0,0;.1,0,0;.9,0,0" --out $P/BM03/compare --tag BM03-vs-C03 --views front,threequarter
  for k in BM03_01 BM03_02 BM03_03; do for L in 0 1; do
    r --glb $E/$k.fbx --lod $L --hide Detail_ --out $P/BM03/lod --tag $k-LOD$L-nodetail --views threequarter --no-ruler --res 960x720
  done; done
  python "$SRC/compose_lod.py" $P/BM03/lod BM03_01 BM03_02 BM03_03
;; esac
case " $ITEMS " in *" BM04 "*)
  for k in BM04_01 BM04_02 BM04_03 BM04_04; do r --glb $E/$k.glb --out $P/BM04/$k --tag $k --views front,side,back,threequarter --wire; done
  for v in front side back threequarter; do r --glb $E/BM04_01.glb,$E/BM04_02.glb,$E/BM04_03.glb,$E/BM04_04.glb --at="-.9,0,0;.55,-.1,0;1.55,.05,0;2.25,-.1,0" --out $P/BM04/set --tag BM04-set --views $v --light afternoon; done
  # a top view, as the work pack's prompt asks for front, side and top
  r --glb $E/BM04_01.glb,$E/BM04_02.glb,$E/BM04_03.glb,$E/BM04_04.glb --at="-.9,0,0;.55,-.1,0;1.55,.05,0;2.25,-.1,0" --out $P/BM04/set --tag BM04-set-top --views "" --no-ruler --light afternoon --cam=.6,-.01,5.2,.6,0,0,40 --res 1400x900
  r --glb $E/BM04_01.glb,$E/BM04_02.glb,$E/BM04_03.glb,$E/BM04_04.glb --at="-.7,.3,25;.6,-.35,-40;1.45,.35,70;.25,-1.0,10" --out $P/BM04/closeup --tag BM04-path-edge --views "" --no-ruler --light afternoon --cam=1.8,-3.2,1.6,.3,0,.3,38 --res 1400x1000
  r --glb $E/BM04_01.glb --out $P/BM04/closeup --tag BM04_01-lichen-cracks --views "" --no-ruler --light afternoon --cam=.4,-1.4,1.1,0,0,.5,45 --res 1200x900
  # side by side with qingxi-moss-boulder-v2, as the work pack asks: they must read as different stones
  r --glb $E/BM04_01.glb,$E/BM04_02.glb,art/exports/qingxi-detail-props-v2/qingxi-moss-boulder-v2.glb --at="-1.1,0,0;.6,0,0;2.1,0,0" --out $P/BM04/compare --tag BM04-vs-moss-boulder --views front,threequarter
  for k in BM04_01 BM04_02 BM04_03 BM04_04; do for L in 0 1; do
    r --glb $E/$k.fbx --lod $L --hide Detail_ --out $P/BM04/lod --tag $k-LOD$L-nodetail --views threequarter --no-ruler --res 960x720
  done; done
  python "$SRC/compose_lod.py" $P/BM04/lod BM04_01 BM04_02 BM04_03 BM04_04
;; esac
case " $ITEMS " in *" BM05 "*)
  for k in BM05_01 BM05_02 BM05_03; do r --glb $E/$k.glb --out $P/BM05/$k --tag $k --views front,side,back,threequarter --wire; done
  # the set as in the reference sheet: drum stool, table, square stool
  for v in front side back threequarter; do r --glb $E/BM05_02.glb,$E/BM05_01.glb,$E/BM05_03.glb --at="-.8,0,0;0,0,0;.8,0,0" --out $P/BM05/set --tag BM05-set --views $v --light afternoon; done
  r --glb $E/BM05_01.glb,$E/BM05_02.glb,$E/BM05_03.glb,$E/BM05_02.glb --at="0,0,0;-.72,-.25,15;.65,-.4,-20;.2,.75,40" --out $P/BM05/closeup --tag BM05-resting-spot --views "" --no-ruler --light afternoon --cam=1.4,-2.4,1.5,0,0,.4,38 --res 1400x1000
  r --glb $E/BM05_01.glb --out $P/BM05/closeup --tag BM05_01-top-chip --views "" --no-ruler --light afternoon --cam=.5,-1.1,1.25,.1,-.2,.65,45 --res 1200x900
  for k in BM05_01 BM05_02 BM05_03; do for L in 0 1; do
    r --glb $E/$k.fbx --lod $L --hide Detail_ --out $P/BM05/lod --tag $k-LOD$L-nodetail --views threequarter --no-ruler --res 960x720
  done; done
  python "$SRC/compose_lod.py" $P/BM05/lod BM05_01 BM05_02 BM05_03
;; esac
case " $ITEMS " in *" BM06 "*)
  for k in BM06_01 BM06_02 BM06_03 BM06_04; do r --glb $E/$k.glb --out $P/BM06/$k --tag $k --views front,side,back,threequarter --wire; done
  for v in front side back threequarter; do r --glb $E/BM06_01.glb,$E/BM06_02.glb,$E/BM06_03.glb,$E/BM06_04.glb --at="-1.9,0,0;-.95,0,0;.25,0,0;1.6,0,0" --out $P/BM06/set --tag BM06-set --views $v --light afternoon; done
  r --glb $E/BM06_01.glb --out $P/BM06/closeup --tag BM06_01-cloud-relief --views "" --no-ruler --light afternoon --cam=.35,-1.05,.55,0,-.3,.26,50 --res 1200x900
  r --glb $E/BM06_03.glb --out $P/BM06/closeup --tag BM06_03-planter-relief --views "" --no-ruler --light afternoon --cam=.6,-1.6,.9,0,-.3,.3,45 --res 1200x900
  # side by side with BM05, as the work pack asks
  r --glb $E/BM06_01.glb,$E/BM06_03.glb,$E/BM05_01.glb,$E/BM05_02.glb --at="-1.5,0,0;-.2,0,0;1.3,0,0;2.2,0,0" --out $P/BM06/compare --tag BM06-vs-BM05 --views front,threequarter
  for k in BM06_01 BM06_02 BM06_03 BM06_04; do for L in 0 1; do
    r --glb $E/$k.fbx --lod $L --hide Detail_ --out $P/BM06/lod --tag $k-LOD$L-nodetail --views threequarter --no-ruler --res 960x720
  done; done
  python "$SRC/compose_lod.py" $P/BM06/lod BM06_01 BM06_02 BM06_03 BM06_04
;; esac
case " $ITEMS " in *" BM07 "*)
  r --glb $E/BM07_01.glb --out $P/BM07/BM07_01 --tag BM07_01 --views front,side,back,threequarter --wire
  r --glb $E/BM07_01.glb --out $P/BM07/closeup --tag BM07_01-chiselled-strip --views "" --no-ruler --light afternoon --cam=.75,-1.3,1.6,.15,-.2,1.2,45 --res 1200x900
  r --glb $E/BM07_01.glb --out $P/BM07/closeup --tag BM07_01-base-litter --views "" --no-ruler --light afternoon --cam=.7,-1.0,.9,0,-.15,.3,45 --res 1200x900
  # side by side with BM04, as the work pack asks
  r --glb $E/BM07_01.glb,$E/BM04_01.glb,$E/BM04_03.glb --at="0,0,0;1.6,0,0;-1.1,0,0" --out $P/BM07/compare --tag BM07-vs-BM04 --views front,threequarter
  for L in 0 1; do r --glb $E/BM07_01.fbx --lod $L --hide Detail_ --out $P/BM07/lod --tag BM07_01-LOD$L-nodetail --views threequarter --no-ruler --res 960x720; done
  python "$SRC/compose_lod.py" $P/BM07/lod BM07_01
;; esac
case " $ITEMS " in *" BM08 "*)
  # built by build_bm08.py (alpha-cut leaf cards); four views + wireframe each shrub, the pair, close looks at the leaf cards
  for k in BM08_01 BM08_02; do r --glb $E/$k.glb --out $P/BM08/$k --tag $k --views front,side,back,threequarter --wire; done
  for v in front threequarter; do r --glb $E/BM08_01.glb,$E/BM08_02.glb --at="-.85,0,0;.75,0,0" --out $P/BM08/set --tag BM08-set --views $v --light afternoon; done
  r --glb $E/BM08_01.glb --out $P/BM08/closeup --tag BM08_01-willow-leaves --views "" --no-ruler --light afternoon --cam=1.1,-1.3,1.3,.15,-.2,.85,45 --res 1200x900
  r --glb $E/BM08_02.glb --out $P/BM08/closeup --tag BM08_02-berries --views "" --no-ruler --light afternoon --cam=1.0,-1.2,1.1,.1,-.15,.6,45 --res 1200x900
  # side by side with WildShrub (dondon's library shrub), as the work pack asks: they must read as different
  r --glb $E/BM08_01.glb,$E/BM08_02.glb,art/incoming/dondon/WildShrub/v001/WildShrub_v001.fbx --at="-1.6,0,0;0,0,0;1.5,0,0" --out $P/BM08/compare --tag BM08-vs-WildShrub --views front,threequarter
  for k in BM08_01 BM08_02; do for L in 0 1; do
    r --glb $E/$k.fbx --lod $L --hide Detail_ --out $P/BM08/lod --tag $k-LOD$L-nodetail --views threequarter --no-ruler --res 960x720
  done; done
  python "$SRC/compose_lod.py" $P/BM08/lod BM08_01 BM08_02
;; esac
case " $ITEMS " in *" CLAY "*)
  # grey model for every exported item (work pack §1.3): one flat grey, no textures, so only the silhouette and the forms are judged
  for f in $E/BM*.glb; do k=$(basename "$f" .glb); r --glb "$f" --clay --light neutral --out $P/${k%_*}/clay --tag $k-clay --views front,side,threequarter --res 960x720; done
  python "$SRC/compose_clay.py" $P
;; esac
echo REVIEWS_DONE
