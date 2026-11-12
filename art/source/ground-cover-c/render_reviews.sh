#!/bin/sh
# Review images and QA for C's ground stones and mushrooms GC01–GC08 (from the repo root). Blender 4.5.3: BL=<blender.exe>.
#   sh art/source/ground-cover-c/render_reviews.sh GC01 [GC02 ...]      (no id: all six)
# The render rig and QA are shared with creekside-life-c (render_wl.py there).
# For each id: grey model (front, side, three-quarter), four views with the 1.75 m figure, a close-up, wireframe,
# LOD0 / LOD1 with Detail_* off, strict and loose QA, contact table; then the style comparisons and one sheet per id.
BL="${BL:?set BL to blender.exe}";S=art/source/ground-cover-c;R=art/source/creekside-life-c;P=art/previews/ground-cover-c;E=art/exports/ground-cover-c;Q=$P/qa
m(){ cygpath -m "$1" 2>/dev/null || echo "$1"; }
r(){ MSYS_NO_PATHCONV=1 "$BL" -b --factory-startup -P "$(m $R/render_wl.py)" -- "$@" 2>&1 | grep -E "Error|Traceback"; true; }
IDS="${*:-GC01 GC02 GC03 GC04 GC05 GC06 GC07 GC08}";mkdir -p $Q $P/compare
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
# style comparisons (work pack part 2 "風格" / "驗收": grey and textured, same light and angle as old props, with the 1.75 m figure; shapes must differ)
cmp(){ tag=$1;glbs=$2;at=$3; for c in "" "--clay"; do r --glb "$glbs" --at="$at" --out "$(m $P/compare)" --tag "$tag${c:+-clay}" --views threequarter,front $c --samples 64; done; }
B=art/exports
cmp GC01-GC03-vs-rocks "$(m $E/GC01_v001.glb),$(m $E/GC02_v001.glb),$(m $E/GC03_v001.glb),$(m $B/qingxi-encounter-a/A04_MossBoulderCover.glb),$(m $B/qingxi-encounter-a/A05_LayeredRockCover.glb)" "0,.9,0;0,.35,0;0,-.35,0;-2.9,0,0;3.0,0,0"
cmp GC04-GC05-vs-forest "$(m $E/GC04_v001.glb),$(m $E/GC05_v001.glb),$(m $B/modelling-basics-c/BM09_02.glb),$(m $B/modelling-basics-c/BM10_02.glb)" "-.3,0,0;.3,0,0;-.95,0,0;1.1,0,0"
cmp GC06-vs-CR03 "$(m $E/GC06_v001.glb),$(m $B/creek-repair-b/CR03_StonePile/CR03_StonePile_v001.fbx)" "-.8,0,0;.9,0,0"
cmp GC-set "$(m $E/GC01_v001.glb),$(m $E/GC02_v001.glb),$(m $E/GC03_v001.glb),$(m $E/GC04_v001.glb),$(m $E/GC05_v001.glb),$(m $E/GC06_v001.glb)" "-.3,1.1,0;-.3,.6,0;-.3,.05,0;1.15,-.75,0;.45,-.8,10;-1.15,-1.15,0"
cmp GC07-GC08-vs-forest "$(m $E/GC07_v001.glb),$(m $E/GC08_v001.glb),$(m $E/GC05_v001.glb),$(m $B/modelling-basics-c/BM10_02.glb)" "0,.25,0;0,-.55,0;-.95,-.55,0;.95,-.55,0"
