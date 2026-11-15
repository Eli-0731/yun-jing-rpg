#!/bin/sh
# Review images and QA for C's yard and roadside props VG01–VG08 (from the repo root). Blender 4.5.3: BL=<blender.exe>.
#   sh art/source/yard-roadside-c/render_reviews.sh VG01 [VG02 ...]      (no id: all; the comparisons run for the ids given)
# The render rig and QA are shared with creekside-life-c (render_wl.py there).
# For each id: grey model (front, side, three-quarter), four views with the 1.75 m figure, a close-up, wireframe,
# LOD0 / LOD1 / LOD2 with Detail_* off, strict and loose QA, contact table; then the comparisons with older props.
# Grey models show the alpha-clip cards (VG02 leaves, VG03 hems, VG04 fringes) as plain quads: the cut-out is in the texture.
BL="${BL:?set BL to blender.exe}";S=art/source/yard-roadside-c;R=art/source/creekside-life-c;P=art/previews/yard-roadside-c;E=art/exports/yard-roadside-c;Q=$P/qa
m(){ cygpath -m "$1" 2>/dev/null || echo "$1"; }
r(){ MSYS_NO_PATHCONV=1 "$BL" -b --factory-startup -P "$(m $R/render_wl.py)" -- "$@" 2>&1 | grep -E "Error|Traceback"; true; }
IDS="${*:-VG01 VG02 VG03 VG04_01 VG04_02 VG05 VG06 VG07 VG08}";mkdir -p $Q $P/compare
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
done
# comparisons (work pack §2 "全包檢查" and §3.3: same light and angle as an older prop, with the 1.75 m figure; grey and textured)
cmp(){ tag=$1;glbs=$2;at=$3; for c in "" "--clay"; do r --glb "$glbs" --at="$at" --out "$(m $P/compare)" --tag "$tag${c:+-clay}" --views threequarter,front $c --samples 64; done; }
B=art/exports;V=$B/village-life-c
has(){ case " $IDS " in *" $1 "*) return 0;; esac; return 1; }
if has VG01; then
cmp VG01-vs-ground "$(m $E/VG01_v001.glb),$(m $B/modelling-basics-c/BM09_02.glb),$(m $B/modelling-basics-c/BM10_02.glb),$(m $V/LV05_v001.glb)" "0,0,0;2.1,.2,0;-2.3,.2,0;2.0,-.7,0"
cmp VG02-VG03-vs-bamboo "$(m $E/VG02_v001.glb),$(m $E/VG03_v001.glb),$(m $V/LV03_v001.glb),$(m $V/LV08_v001.glb)" "-1.5,.6,0;1.5,-.5,0;3.1,.5,0;-3.1,.3,0"
cmp VG04-vs-straw "$(m $E/VG04_01_v001.glb),$(m $E/VG04_02_v001.glb),$(m $B/qingxi-world-ruins-b/R03_FirewoodNeat/R03_FirewoodNeat_v001.glb),$(m $V/LV12_v001.glb)" "-1.35,0,0;1.35,0,0;3.0,0,0;-2.9,0,0"
cmp VG-setA "$(m $E/VG01_v001.glb),$(m $E/VG02_v001.glb),$(m $E/VG03_v001.glb),$(m $E/VG04_01_v001.glb),$(m $E/VG04_02_v001.glb),$(m $V/LV05_v001.glb)" "0,-2.3,0;-2.6,.9,0;.6,1.6,0;3.1,.4,0;5.6,.4,0;2.3,-2.3,0"
fi
if has VG05; then
W=$B/qingxi-world-ruins-b
cmp VG05-vs-cart "$(m $E/VG05_v001.glb),$(m $W/A2_OverturnedCart/A2_OverturnedCart_v001.glb),$(m $V/LV05_v001.glb)" "-.6,0,0;2.4,.2,0;1.0,-1.1,0"
cmp VG06-vs-baskets "$(m $E/VG06_v001.glb),$(m $V/LV01_v001.glb),$(m $V/LV12_v001.glb),$(m $V/LV04_v001.glb)" "0,0,0;1.6,.1,0;-1.3,.1,0;.0,-.8,0"
cmp VG07-VG08-vs-stone "$(m $E/VG07_v001.glb),$(m $E/VG08_v001.glb),$(m $W/D3_DryWell/D3_DryWell_v001.glb),$(m $V/LV05_v001.glb)" "-1.0,.3,0;.6,-.5,0;1.6,.9,0;-.4,-.9,0"
cmp VG-setB "$(m $E/VG05_v001.glb),$(m $E/VG06_v001.glb),$(m $E/VG07_v001.glb),$(m $E/VG08_v001.glb),$(m $V/LV05_v001.glb)" "-.9,1.0,0;-1.2,-1.0,0;1.9,.9,0;1.3,-1.0,0;2.6,-.9,0"
# the whole pack side by side (work pack §2 "全包檢查"), with one older prop (LV05)
cmp VG-all "$(m $E/VG01_v001.glb),$(m $E/VG02_v001.glb),$(m $E/VG03_v001.glb),$(m $E/VG04_01_v001.glb),$(m $E/VG04_02_v001.glb),$(m $E/VG05_v001.glb),$(m $E/VG06_v001.glb),$(m $E/VG07_v001.glb),$(m $E/VG08_v001.glb),$(m $V/LV05_v001.glb)" "-4.2,-1.6,0;-4.4,1.6,0;-1.5,1.9,0;1.6,1.7,0;4.3,1.7,0;-.8,-1.6,0;1.9,-2.0,0;3.6,-1.5,0;5.2,-1.9,0;-2.6,-2.6,0"
fi
