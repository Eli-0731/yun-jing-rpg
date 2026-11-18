#!/bin/sh
# Review images and QA for C's D2 mushrooms DP01–DP05 (from the repo root). Blender 4.5.3: BL=<blender.exe>.
#   sh art/source/d2-mushrooms-c/render_reviews.sh DP01_01 [DP01_02 ...]      (no id: all)
# The render rig and QA are shared with creekside-life-c (render_wl.py there). For each id: grey model (front, side,
# three-quarter), four views with the 1.75 m figure, a close-up, wireframe, LOD0 / LOD1 / LOD2 with Detail_* off,
# strict and loose QA, contact table, and the D2 look-match shots (render_d2match.py) for the side-by-side with the setting views.
BL="${BL:?set BL to blender.exe}";S=art/source/d2-mushrooms-c;R=art/source/creekside-life-c;P=art/previews/d2-mushrooms-c;E=art/exports/d2-mushrooms-c;Q=$P/qa
m(){ cygpath -m "$1" 2>/dev/null || echo "$1"; }
r(){ MSYS_NO_PATHCONV=1 "$BL" -b --factory-startup -P "$(m $R/render_wl.py)" -- "$@" 2>&1 | grep -E "Error|Traceback"; true; }
ALL="DP01_01 DP01_02 DP01_03 DP01_04"
IDS="${*:-$ALL}";mkdir -p $Q
for id in $IDS; do
  [ -f $E/${id}_v001.glb ] || continue
  D=$P/$id;G=$(m $E/${id}_v001.glb);F=$(m $E/${id}_v001.fbx)
  r --glb "$(m $D/clay/$id-clay.glb)" --out "$(m $D/clay)" --tag $id-clay --views front,side,threequarter --clay --samples 32
  r --glb "$(m $D/clay/$id-clay.glb)" --out "$(m $D/clay)" --tag $id-clay-close --views threequarter --clay --no-ruler --samples 32
  r --glb "$G" --out "$(m $D)" --tag $id --samples 64
  r --glb "$G" --out "$(m $D)" --tag $id-close --views threequarter --no-ruler --samples 96 --res 1600x1200
  r --glb "$G" --out "$(m $D)" --tag $id --views "" --wire --no-ruler --samples 16
  for L in 0 1 2; do r --glb "$F" --out "$(m $D)" --tag $id-LOD$L-nodetail --views threequarter --lod $L --hide Detail_ --no-ruler --samples 48; done
  for o in "" "--loose"; do MSYS_NO_PATHCONV=1 "$BL" -b --factory-startup -P "$(m tools/art/qa_lod0_basic.py)" -- $o "$(m $Q/$id-qa${o:+-loose}.json)" "$G" >/dev/null 2>&1; done
  MSYS_NO_PATHCONV=1 "$BL" -b --factory-startup -P "$(m tools/art/qa_contact_glb.py)" -- "$(m $Q/$id-contact.json)" "$G" >/dev/null 2>&1
  MSYS_NO_PATHCONV=1 "$BL" -b --factory-startup -P "$(m $S/render_d2match.py)" -- --glb "$G" --out "$(m $D/d2)" --tag $id --small 1 --fig 0 2>&1 | grep -E "Error|Traceback"
  echo "done $id"
done
