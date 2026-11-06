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
case " $ITEMS " in *" BM09 "*)
  # built by build_bm09_bm10.py; four views + wireframe, LOD0 vs LOD1 without Detail_*, side by side with qingxi-fern-flower-v2
  for k in BM09_01 BM09_02; do
    r --glb $E/$k.glb --out $P/BM09 --tag $k-scale --views front,side,back,threequarter --wire
    for L in 0 1; do r --glb $E/$k.fbx --lod $L --hide Detail_ --out $P/BM09 --tag $k-lod$L-nodetail --views threequarter --no-ruler; done
    r --glb $E/$k.glb,art/exports/qingxi-detail-props-v2/qingxi-fern-flower-v2.glb --at="-.8,0,0;.7,0,0" --out $P/BM09/compare --tag $k-vs-qingxi --views threequarter --no-ruler
  done
;; esac
case " $ITEMS " in *" BM10 "*)
  # ground patches: a close look at each, then the #69 edge check -- the three patches on a light and on a dark ground, near
  # and from 40 m, in EEVEE (Cycles does not mipmap, so it cannot show how the alpha edge reads far away), with a 6x crop
  for k in BM10_01 BM10_02 BM10_03; do r --glb $E/$k.glb --out $P/BM10 --tag $k-close --views "" --no-ruler --at="0,0,0,0.005" --cam=0,-.35,1.5,0,0,0,55 --light neutral --res 1200x900; done
  G="$E/BM10_01.glb,$E/BM10_02.glb,$E/BM10_03.glb";EC=$P/BM10/edge-check
  for gr in "light:.62,.57,.48" "dark:.10,.085,.07"; do n=${gr%%:*};c=${gr#*:}
    r --glb $G --at="-1.3,0,0;0,0,0;1.3,0,0" --ground $c --light afternoon --no-ruler --views "" --engine eevee --out $EC --tag patches-$n-40m-eevee --cam=0,-34.6,20,0,0,0,50 --res 1920x1080
    r --glb $G --at="-1.3,0,0;0,0,0;1.3,0,0" --ground $c --light afternoon --no-ruler --views "" --engine eevee --out $EC --tag patches-$n-near-eevee --cam=0,-2.6,1.9,0,0,0,32 --res 1600x900
  done
  python -c "
from PIL import Image
for n in ('light','dark'):
    im=Image.open('$EC/patches-'+n+'-40m-eevee-cam.png').convert('RGB');w,h=im.size
    im.crop((w//2-110,h//2-30,w//2+110,h//2+30)).resize((1320,360),Image.NEAREST).save('$EC/patches-'+n+'-40m-eevee-crop6x.png')"
;; esac
case " $ITEMS " in *" CONTACT "*)
  # #69: how each kind of loose piece rests on its support (art/previews/modelling-basics-c/qa/qa-contact.json, gap along the
  # best chain of touching pieces down to z=0); red dots at the pieces with the largest gap of that kind
  K=$P/qa-evidence/contact;c(){ r --glb $E/$1.glb --out $K --tag $2 --views "" --no-ruler --light afternoon --res 1200x900 --cam=$3 ${4:+--mark=$4}; }
  c BM06_02 BM06_02-staples ".66,.36,.5,.34,.17,.39,50"
  c BM06_03 BM06_03-shrub-leaves ".6,-.65,.9,.199,-.153,.634,45" ".199,-.153,.634,.004;.032,.284,.689,.004"
  c BM06_04 BM06_04-grass-in-soil ".45,-.75,.8,0,0,.42,40"
  c BM07_01 BM07_01-needles-on-base ".55,-.75,.6,.2,-.2,.3,40"
  c BM08_01 BM08_01-litter ".95,-.95,.5,.3,-.3,0,40"
  c BM08_02 BM08_02-berry-stalks "-.17,-.62,.5,-.26,-.36,.44,60"
  c BM08_02 BM08_02-inner-leaf-card ".45,-.75,.8,.004,-.134,.56,50" ".004,-.134,.56,.005"
  c BM09_02 BM09_02-crozier-centre ".3,-.4,.3,0,0,.08,45"
  python "$SRC/compose_sheet.py" $P/qa-evidence/contact-sheet.jpg "#69 散件接觸（qa-contact.json）" 4     $K/BM06_02-staples-cam.png="BM06_02 鐵扣：嵌進缸壁 3 mm" $K/BM06_03-shrub-leaves-cam.png="BM06_03 花台灌木葉：最遠 4.9 mm"     $K/BM06_04-grass-in-soil-cam.png="BM06_04 花台草：根部插進土 4 mm" $K/BM07_01-needles-on-base-cam.png="BM07 松針、落葉：躺在座台上，最遠 0.9 mm"     $K/BM08_01-litter-cam.png="BM08_01 落葉：平躺地面，最遠 1.2 mm" $K/BM08_02-berry-stalks-cam.png="BM08_02 紅果：果柄連到枝端，最遠 0.2 mm"     $K/BM08_02-inner-leaf-card-cam.png="BM08_02 唯一 >1 cm 的葉片（12.6 mm，樹冠內）" $K/BM09_02-crozier-centre-cam.png="BM09_02 羽片接在葉軸上：最遠 0.6 mm"
;; esac
case " $ITEMS " in *" V1 "*)
  # #69 follow-up: the second BM09 / BM10 (build_bm09.py, build_bm10.py) next to the first one, same light and camera, textured
  # and grey. V1 points at the first version's GLBs, e.g.
  #   for k in BM09_01 BM09_02 BM10_01 BM10_02 BM10_03; do git show 4684a3fd:art/exports/modelling-basics-c/$k.glb | git lfs smudge > $V1/$k.glb; done
  if [ -n "$V1" ] && [ -f "$V1/BM09_01.glb" ]; then
    C=$P/compare-v1
    for k in BM09_01 BM09_02; do
      if [ $k = BM09_01 ]; then g="-1.0,0,0;1.0,0,0";cam="0,-4.4,1.5,0,0,.38,40"; else g="-.42,0,0;.42,0,0";cam="0,-1.75,.6,0,0,.14,40"; fi
      r --glb $V1/$k.glb,$E/$k.glb --at="$g" --out $C --tag $k-v1-vs-v2 --views "" --no-ruler --light afternoon --cam=$cam --res 1600x900
      r --glb $V1/$k.glb,$E/$k.glb --at="$g" --out $C --tag $k-v1-vs-v2-clay --views "" --no-ruler --clay --light neutral --cam=$cam --res 1600x900
    done
    for k in BM10_01 BM10_02 BM10_03; do
      r --glb $V1/$k.glb,$E/$k.glb --at="-.6,0,0,0.005;.6,0,0,0.005" --out $C --tag $k-v1-vs-v2 --views "" --no-ruler --light neutral --cam=0,-1.2,2.2,0,0,0,40 --res 1600x900
    done
    python "$SRC/compose_sheet.py" $C/BM09-BM10-v1-vs-v2.jpg "BM09／BM10 第一版（左）和第二版（右），同燈同角度" 2       $C/BM09_01-v1-vs-v2-cam.png="BM09_01 大型野蕨 材質" $C/BM09_01-v1-vs-v2-clay-cam.png="BM09_01 灰模"       $C/BM09_02-v1-vs-v2-cam.png="BM09_02 矮捲蕨 材質" $C/BM09_02-v1-vs-v2-clay-cam.png="BM09_02 灰模"       $C/BM10_01-v1-vs-v2-cam.png="BM10_01 苔蘚" $C/BM10_02-v1-vs-v2-cam.png="BM10_02 紅楓落葉" $C/BM10_03-v1-vs-v2-cam.png="BM10_03 銀杏黃葉"
  else echo "V1: set V1 to a folder with the first version's GLBs"; fi
;; esac
case " $ITEMS " in *" CLAY "*)
  # grey model for every exported item (work pack §1.3): one flat grey, no textures, so only the silhouette and the forms are judged
  for f in $E/BM*.glb; do k=$(basename "$f" .glb); r --glb "$f" --clay --light neutral --out $P/${k%_*}/clay --tag $k-clay --views front,side,threequarter --res 960x720; done
  python "$SRC/compose_clay.py" $P
;; esac
echo REVIEWS_DONE
