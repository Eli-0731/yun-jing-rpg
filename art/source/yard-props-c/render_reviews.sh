#!/bin/sh
# Review images and QA for C's yard props YP01–YP13 (from the repo root). Blender 4.5.3: BL=<blender.exe>.
#   sh art/source/yard-props-c/render_reviews.sh YP10 [YP02 ...]      (no id: all 23 models)
#   CMP=1 sh art/source/yard-props-c/render_reviews.sh -               (only the comparisons with older props)
# The render rig and QA are shared with creekside-life-c (render_wl.py there), as in yard-roadside-c.
# For each id: grey model (front, side, three-quarter), four views with the 1.75 m figure, a close-up, wireframe,
# LOD0 / LOD1 / LOD2 with Detail_* off, strict and loose QA, contact table.
BL="${BL:?set BL to blender.exe}";S=art/source/yard-props-c;R=art/source/creekside-life-c;P=art/previews/yard-props-c;E=art/exports/yard-props-c;Q=$P/qa
m(){ cygpath -m "$1" 2>/dev/null || echo "$1"; }
r(){ MSYS_NO_PATHCONV=1 "$BL" -b --factory-startup -P "$(m $R/render_wl.py)" -- "$@" 2>&1 | grep -E "Error|Traceback"; true; }
ALL="YP01_01 YP01_02 YP01_03 YP01_04 YP02 YP03 YP04 YP05_01 YP05_02 YP06_01 YP06_02 YP06_03 YP07_01 YP07_02 YP07_03 YP08 YP09_01 YP09_02 YP10 YP11 YP12 YP13_01 YP13_02"
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
[ -n "$CMP" ] || exit 0
# comparisons (work pack §2 "和同類並排"): same light and angle as older props, with the 1.75 m figure; grey and textured.
# Clay comparisons use the textured GLBs with --clay (one flat grey).
cmp(){ tag=$1;glbs=$2;at=$3; for c in "" "--clay"; do r --glb "$glbs" --at="$at" --out "$(m $P/compare)" --tag "$tag${c:+-clay}" --views threequarter,front $c --samples 64; done; echo "cmp $tag"; }
B=art/exports;V=$B/village-life-c;Y=$B/yard-roadside-c
g(){ for i in "$@"; do printf '%s,' "$(m $E/${i}_v001.glb)"; done; }
BED="$(g YP01_01 YP01_02 YP01_03 YP01_04)"
cmp YP01-vs-VG01 "$BED$(m $Y/VG01_v001.glb),$(m $V/LV05_v001.glb)" "0,0,0;-.62,0,0;0,0,0;.62,0,0;2.7,.3,0;-1.7,-1.2,0"
cmp YP02-vs-VG03 "$(g YP02)$(m $Y/VG03_v001.glb),$(m $V/LV08_v001.glb)" "-1.5,0,0;1.6,.4,0;3.7,0,0"
cmp YP10-YP11-vs-VG05-VG06 "$(g YP10 YP11)$(m $Y/VG05_v001.glb),$(m $Y/VG06_v001.glb)" "-1.3,-.6,0;-1.2,.9,0;1.6,-.5,0;1.6,1.2,0"
cmp YP03-YP04-YP12-vs-VG08 "$(g YP03 YP04 YP12)$(m $Y/VG08_v001.glb),$(m $V/LV05_v001.glb)" "-1.4,0,0;-.4,0,0;.9,0,0;2.6,.2,0;-2.4,.1,0"
cmp YP05-YP09 "$(g YP05_01 YP05_02 YP09_01 YP09_02)$(m $V/LV05_v001.glb)" "-.9,-.4,0;-.9,.6,0;.8,-.3,0;.9,.7,0;2.0,0,0"
cmp YP06-YP07-YP08 "$(g YP06_01 YP06_02 YP06_03 YP07_01 YP07_02 YP07_03 YP08)$(m $V/LV12_v001.glb)" "-1.7,-.3,0;-1.8,.9,0;-.2,.9,0;.5,-.6,0;1.0,-.6,0;1.5,-.6,0;1.3,.9,0;2.3,-.5,0"
cmp YP13-vs-ground "$(g YP13_01 YP13_02)$(m $B/modelling-basics-c/BM09_02.glb),$(m $V/LV05_v001.glb)" "-.7,0,0;.5,-.2,0;1.6,.3,0;-1.9,.2,0"
cmp YP-all "$BED$(g YP02 YP03 YP04 YP05_01 YP05_02 YP06_01 YP06_02 YP06_03 YP07_01 YP07_02 YP07_03 YP08 YP09_01 YP09_02 YP10 YP11 YP12 YP13_01 YP13_02)$(m $V/LV05_v001.glb)" \
 "-4.6,1.2,0;-5.22,1.2,0;-4.6,1.2,0;-3.98,1.2,0;-1.0,2.6,0;-2.2,-1.6,0;-1.3,-1.6,0;.4,-1.9,0;.4,-1.2,0;1.9,1.6,0;1.9,2.6,0;3.3,2.6,0;1.6,-1.5,0;2.0,-1.5,0;2.4,-1.5,0;1.0,3.3,0;3.3,-1.5,0;4.3,-1.4,0;-.4,.4,0;3.9,.6,0;5.3,.4,0;5.3,-1.0,0;6.2,-.9,0;-3.0,-1.9,0"
