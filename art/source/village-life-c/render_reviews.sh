#!/bin/sh
# Review images and QA for C's village props LV01–LV06 (from the repo root). Blender 4.5.3: BL=<blender.exe>.
#   sh art/source/village-life-c/render_reviews.sh LV01 [LV02 ...]      (no id: all six)
# The render rig and QA are shared with creekside-life-c (render_wl.py there).
# For each id: grey model (front, side, three-quarter), four views with the 1.75 m figure, a close-up, wireframe,
# LOD0 / LOD1 with Detail_* off, strict and loose QA, contact table; then the style comparisons and one sheet per id.
BL="${BL:?set BL to blender.exe}";S=art/source/village-life-c;R=art/source/creekside-life-c;P=art/previews/village-life-c;E=art/exports/village-life-c;Q=$P/qa
m(){ cygpath -m "$1" 2>/dev/null || echo "$1"; }
r(){ MSYS_NO_PATHCONV=1 "$BL" -b --factory-startup -P "$(m $R/render_wl.py)" -- "$@" 2>&1 | grep -E "Error|Traceback"; true; }
IDS="${*:-LV01 LV02 LV03 LV04 LV05 LV06}";mkdir -p $Q $P/compare
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
# style comparisons (work pack part 2 "風格": grey and textured, same light and angle as old props, with the 1.75 m figure)
cmp(){ tag=$1;glbs=$2;at=$3; for c in "" "--clay"; do r --glb "$glbs" --at="$at" --out "$(m $P/compare)" --tag "$tag${c:+-clay}" --views threequarter,front $c --samples 64; done; }
B=art/exports;H=$B/harvest-market-b
cmp LV01-LV04-vs-woven "$(m $E/LV01_v001.glb),$(m $E/LV04_v001.glb),$(m $H/MK02_HarvestSieve/MK02_HarvestSieve_v001.fbx),$(m $H/MK04_BackBasket/MK04_BackBasket_v001.fbx)" "0,0,0;.85,0,0;-.95,.05,0;1.65,.05,0"
cmp LV02-LV03-vs-wood "$(m $E/LV02_v001.glb),$(m $E/LV03_v001.glb),$(m $B/qingxi-world-ruins-b/R03_FirewoodNeat/R03_FirewoodNeat_v001.glb),$(m $B/modelling-basics-c/BM02_01.glb)" "0,-.15,0;1.05,.25,0;-1.25,.25,0;1.0,-.45,0"
cmp LV05-vs-BM03 "$(m $E/LV05_v001.glb),$(m $B/modelling-basics-c/BM03_01.glb),$(m $B/modelling-basics-c/BM03_02.glb),$(m $B/modelling-basics-c/BM03_03.glb)" "0,0,0;.8,.05,0;1.2,.05,0;-.75,.05,0"
cmp LV06-vs-wood "$(m $E/LV06_v001.glb),$(m $B/modelling-basics-c/BM02_01.glb),$(m $B/qingxi-world-ruins-b/R03_FirewoodNeat/R03_FirewoodNeat_v001.glb)" "0,0,0;.7,0,0;-1.05,0,0"
cmp LV-set "$(m $E/LV01_v001.glb),$(m $E/LV02_v001.glb),$(m $E/LV03_v001.glb),$(m $E/LV04_v001.glb),$(m $E/LV05_v001.glb),$(m $E/LV06_v001.glb)" "-1.25,.35,10;.1,.85,-6;1.45,.7,0;.75,-.35,0;-.25,-.45,8;-1.35,-.65,-12"
