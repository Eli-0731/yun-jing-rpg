#!/bin/sh
# Review images and QA for C's undergrowth plants SH01–SH02, SP01, UG01–UG06 (from the repo root). Blender 4.5.3: BL=<blender.exe>.
#   sh art/source/undergrowth-c/render_reviews.sh YP10 [YP02 ...]      (no id: all)
#   CMP=1 sh art/source/undergrowth-c/render_reviews.sh -               (only the comparisons with older props)
# The render rig and QA are shared with creekside-life-c (render_wl.py there), as in yard-roadside-c.
# For each id: grey model (front, side, three-quarter), four views with the 1.75 m figure, a close-up, wireframe,
# LOD0 / LOD1 / LOD2 with Detail_* off, strict and loose QA, contact table.
BL="${BL:?set BL to blender.exe}";S=art/source/undergrowth-c;R=art/source/creekside-life-c;P=art/previews/undergrowth-c;E=art/exports/undergrowth-c;Q=$P/qa
m(){ cygpath -m "$1" 2>/dev/null || echo "$1"; }
r(){ MSYS_NO_PATHCONV=1 "$BL" -b --factory-startup -P "$(m $R/render_wl.py)" -- "$@" 2>&1 | grep -E "Error|Traceback"; true; }
ALL="SH01 SH02 SP01 UG01 UG02 UG03 UG04 UG05_01 UG05_02 UG05_03 UG06_01 UG06_02 UG06_03 UG06_04"
IDS="${*:-$ALL}";[ "$IDS" = "-" ] && IDS="";mkdir -p $Q $P/compare
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
  echo "done $id"
done
# comparisons and the plant shots of 樹木重做-v2-分工.md §3 (silhouettes, under the crown, 20 m / 60 m, front and 35° each side)
for id in $IDS; do
  [ -f $E/${id}_v001.glb ] && MSYS_NO_PATHCONV=1 "$BL" -b --factory-startup -P "$(m $S/render_plant.py)" -- --glb "$(m $E/${id}_v001.glb)" --out "$(m $P/$id/plant)" --tag $id 2>&1 | grep -E "Error|Traceback|PLANT_DONE"
done
[ -n "$CMP" ] || exit 0
