#!/bin/sh
# Review images and QA for C's wayside props WS01–WS06 (from the repo root). Blender 4.5.3: BL=<blender.exe>.
#   sh art/source/wayside-c/render_reviews.sh YP10 [YP02 ...]      (no id: all 10 models)
#   CMP=1 sh art/source/wayside-c/render_reviews.sh -               (only the comparisons with older props)
# The render rig and QA are shared with creekside-life-c (render_wl.py there), as in yard-roadside-c.
# For each id: grey model (front, side, three-quarter), four views with the 1.75 m figure, a close-up, wireframe,
# LOD0 / LOD1 / LOD2 with Detail_* off, strict and loose QA, contact table.
BL="${BL:?set BL to blender.exe}";S=art/source/wayside-c;R=art/source/creekside-life-c;P=art/previews/wayside-c;E=art/exports/wayside-c;Q=$P/qa
m(){ cygpath -m "$1" 2>/dev/null || echo "$1"; }
r(){ MSYS_NO_PATHCONV=1 "$BL" -b --factory-startup -P "$(m $R/render_wl.py)" -- "$@" 2>&1 | grep -E "Error|Traceback"; true; }
ALL="WS01_01 WS01_02 WS02_01 WS02_02 WS03 WS04_01 WS04_02 WS05_01 WS05_02 WS06"
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
Y=$B/yard-roadside-c;YP=$B/yard-props-c;G=$B/ground-cover-c
cmp WS01-WS02-vs-YP13 "$(g WS01_01 WS01_02 WS02_01 WS02_02)$(m $YP/YP13_01_v001.glb),$(m $YP/YP13_02_v001.glb)" "-1.6,.1,0;-.8,-.2,0;.4,.4,0;1.6,-.1,0;2.9,.3,0;-2.6,.0,0"
cmp WS03-WS04-vs-GC06 "$(g WS03 WS04_01 WS04_02)$(m $G/GC06_v001.glb),$(m $V/LV05_v001.glb)" "-.9,.1,0;.5,-.3,0;1.0,.2,0;2.4,.2,0;-2.4,.0,0"
cmp WS05-vs-VG04 "$(g WS05_01 WS05_02)$(m $Y/VG04_01_v001.glb),$(m $V/LV05_v001.glb)" "-1.6,0,0;.2,-.3,0;2.4,.3,0;-.6,-1.3,0"
cmp WS06-vs-YP11 "$(g WS06)$(m $YP/YP11_v001.glb),$(m $V/LV05_v001.glb)" "0,0,0;0,1.0,0;-1.2,-.6,0"
cmp WS-all "$(g WS01_01 WS01_02 WS02_01 WS02_02 WS03 WS04_01 WS04_02 WS05_01 WS05_02 WS06)$(m $V/LV05_v001.glb)"  "-3.2,1.2,0;-2.4,1.2,0;-1.2,1.3,0;.0,1.2,0;1.4,1.2,0;2.6,1.2,0;3.2,1.2,0;-2.4,-1.0,0;-.4,-1.0,0;1.6,-1.0,0;3.2,-1.0,0"
