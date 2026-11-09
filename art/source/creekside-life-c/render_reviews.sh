#!/bin/sh
# Review images and QA for C's creekside props WL01–WL05 (from the repo root). Blender 4.5.3: BL=<blender.exe>.
#   sh art/source/creekside-life-c/render_reviews.sh WL01 [WL02 ...]      (no id: all five)
# For each id: grey model (front, side, three-quarter), four views with the 1.75 m figure, a close-up, wireframe,
# LOD0 / LOD1 with Detail_* off, strict and loose QA, contact table; then the style comparisons and one sheet per id.
BL="${BL:?set BL to blender.exe}";S=art/source/creekside-life-c;P=art/previews/creekside-life-c;E=art/exports/creekside-life-c;Q=$P/qa
m(){ cygpath -m "$1" 2>/dev/null || echo "$1"; }
r(){ MSYS_NO_PATHCONV=1 "$BL" -b --factory-startup -P "$(m $S/render_wl.py)" -- "$@" 2>&1 | grep -E "Error|Traceback"; true; }
IDS="${*:-WL01 WL02 WL03 WL04 WL05 FI01 FI02 FI03 FI04 FI05}";mkdir -p $Q $P/compare
for id in $IDS; do
  D=$P/$id;G=$(m $E/${id}_v001.glb);F=$(m $E/${id}_v001.fbx)
  r --glb "$(m $D/clay/$id-clay.glb)" --out "$(m $D/clay)" --tag $id-clay --views front,side,threequarter --clay --samples 32
  r --glb "$(m $D/clay/$id-clay.glb)" --out "$(m $D/clay)" --tag $id-clay-close --views threequarter --clay --no-ruler --samples 32
  r --glb "$G" --out "$(m $D)" --tag $id --samples 64
  r --glb "$G" --out "$(m $D)" --tag $id-close --views threequarter --no-ruler --samples 96 --res 1600x1200
  r --glb "$G" --out "$(m $D)" --tag $id --views "" --wire --no-ruler --samples 16
  for L in 0 1; do r --glb "$F" --out "$(m $D)" --tag $id-LOD$L-nodetail --views threequarter --lod $L --hide Detail_ --no-ruler --samples 48; done
  for o in "" "--loose"; do MSYS_NO_PATHCONV=1 "$BL" -b --factory-startup -P "$(m tools/art/qa_lod0_basic.py)" -- $o "$(m $Q/$id-qa${o:+-loose}.json)" "$G" >/dev/null 2>&1; done
  MSYS_NO_PATHCONV=1 "$BL" -b --factory-startup -P "$(m tools/art/qa_contact_glb.py)" -- "$(m $Q/$id-contact.json)" "$G" >/dev/null 2>&1
done
# style comparisons (work pack §7): same light and angle, grey and textured, with the 1.75 m figure
cmp(){ tag=$1;glbs=$2;at=$3; for c in "" "--clay"; do r --glb "$glbs" --at="$at" --out "$(m $P/compare)" --tag "$tag${c:+-clay}" --views threequarter,front $c --samples 64; done; }
case " $IDS " in *" WL"*)
cmp WL01-WL02-vs-oldwood "$(m $E/WL01_v001.glb),$(m $E/WL02_v001.glb),$(m art/exports/modelling-basics-c/BM01_01.glb),$(m art/exports/qingxi-world-ruins-b/R03_FirewoodNeat/R03_FirewoodNeat_v001.glb)" "0,0,0;0,-.45,0;.75,0,0;-1.25,.1,0"
cmp WL03-WL04-vs-cloth "$(m $E/WL03_v001.glb),$(m $E/WL04_v001.glb),$(m art/exports/qingxi-day34-c/UP05_CushionOld.glb),$(m art/exports/territory-interior-b/TI06_WovenMat/TI06_WovenMat_v002.fbx)" "0,0,0;.75,0,0;-.75,0,0;0,.9,0"
cmp WL05-vs-stone "$(m $E/WL05_v001.glb),$(m art/exports/modelling-basics-c/BM05_03.glb),$(m art/exports/modelling-basics-c/BM06_01.glb)" "0,0,0;.6,0,0;-.85,0,0"
cmp WL-set "$(m $E/WL01_v001.glb),$(m $E/WL02_v001.glb),$(m $E/WL03_v001.glb),$(m $E/WL04_v001.glb),$(m $E/WL05_v001.glb)" "-.45,.15,0;.05,-.32,20;.5,.3,-10;.55,-.3,5;-.45,-.38,-15"
;; esac
case " $IDS " in *" FI"*)
cmp FI-vs-waterworks "$(m $E/FI01_v001.glb),$(m $E/FI03_v001.glb),$(m $E/FI04_v001.glb),$(m art/exports/qingxi-waterworks-b/B08/B08.glb),$(m art/exports/qingxi-waterworks-b/B09/B09.glb)" "-1.1,.75,0;-.6,.05,0;.75,-.1,0;1.55,-.75,0;.15,-.75,0"
cmp FI02-FI05-vs-float "$(m $E/FI02_v001.glb),$(m $E/FI05_v001.glb),$(m art/exports/qingxi-waterworks-b/B09/B09.glb)" "0,0,0;.55,0,0;1.1,0,0"
cmp FI04-vs-basket "$(m $E/FI04_v001.glb),$(m art/exports/harvest-market-b/MK04_BackBasket/MK04_BackBasket_v001.fbx)" "0,0,0;1.0,0,0"
cmp FI-set "$(m $E/FI01_v001.glb),$(m $E/FI02_v001.glb),$(m $E/FI03_v001.glb),$(m $E/FI04_v001.glb),$(m $E/FI05_v001.glb)" "-1.1,.75,0;-.3,-.6,15;-.45,.12,8;.95,-.35,-20;.35,-.75,-5"
;; esac
