#!/bin/sh
# Review renders for the C day 3-4 models (Eli-0731). Run from the repo root:
#   BLENDER=<blender.exe> [D12=<path to art/exports/qingxi-day12-c>] sh art/source/qingxi-day34-c/render_reviews.sh
# D12 points at the day 1-2 lanterns G01 / TY04 (PR #60) for the three-lantern comparison; skipped when missing.
# In Git Bash also set MSYS_NO_PATHCONV=1 so the --cam / --at values reach Blender untouched.
set -e
B="${BLENDER:?set BLENDER to blender.exe}";SRC=art/source/qingxi-day34-c;RIG=$SRC/render_day34.py
E=art/exports/qingxi-day34-c;P=art/previews/qingxi-day34-c;A=art/exports/qingxi-waterhead-a
r(){ "$B" -b --factory-startup -P "$RIG" -- "$@" >/dev/null 2>&1 || echo "render failed: $*"; }
# 1. four views with the 1.75 m figure + wireframe (lantern unlit, stones cold)
for k in UP01 UP02_01 UP02_02 UP02_03 UP03 UP04 UP05_CushionNew UP05_CushionOld UP05_Table UP05_Burner UP06; do
  g=""; case $k in UP06) g="--glow 0";; esac
  r --glb $E/$k.glb --out $P/$k --tag $k --views front,side,back,threequarter --wire $g
done
# 2. states
#    UP01: blocked (default) / cleared (Debris hidden) / cleared + gate raised 1.2 m
r --glb $E/UP01.glb --out $P/UP01/states --tag UP01-blocked --views threequarter --no-ruler
r --glb $E/UP01.glb --out $P/UP01/states --tag UP01-cleared --views threequarter --no-ruler --hide Debris
r --glb $E/UP01.glb --out $P/UP01/states --tag UP01-cleared-gate-open --views threequarter --no-ruler --hide Debris --move UP01_Gate:0,0,1.2
r --glb $E/UP01.glb --out $P/UP01/states --tag UP01-sluice-closeup --views "" --no-ruler --cam=1.6,-3.4,1.5,0,.5,1.1,32
r --glb $E/UP01.glb --out $P/UP01/states --tag UP01-sluice-open-closeup --views "" --no-ruler --hide Debris --move UP01_Gate:0,0,1.2 --cam=1.6,-3.4,1.5,0,.5,1.1,32
#    UP02: _Warmth 0 / 1 under afternoon sun and at dusk (from the .blend: glTF cannot carry the state blend)
for k in UP02_01 UP02_02 UP02_03; do for L in afternoon dusk; do for w in 0 1; do
  r --glb $SRC/$k.blend --out $P/UP02/warmth --tag $k-$L-warmth$w --views threequarter --no-ruler --light $L --state warmth=$w --res 960x720
done; done; done
#    UP03 / UP04 close-ups: the carved marks; the charcoal drawing from above
r --glb $E/UP03.glb --out $P/UP03 --tag UP03-marks-closeup --views "" --no-ruler --cam=.15,-1.0,.95,0,0,.82,50
r --glb $E/UP04.glb --out $P/UP04 --tag UP04-drawing-top --views "" --no-ruler --cam=0,-.15,1.9,0,0,.3,40
#    UP06: unlit / lit, by day and at night
for L in day night; do
  r --glb $E/UP06.glb --out $P/UP06/states --tag UP06-$L-unlit --views front --glow 0 --light $L --no-ruler --res 640x960
  r --glb $E/UP06.glb --out $P/UP06/states --tag UP06-$L-lit --views front --glow 2 --light $L --no-ruler --res 640x960
done
# 3. 1.7 m eye height
r --glb $E/UP01.glb --out $P/eye --tag UP01-from-dry-bed-1p7m --views "" --cam=-2.5,-11,1.7,0,0,1.6,26 --ruler-x 2.2
r --glb $E/UP01.glb --out $P/eye --tag UP01-on-crest-1p7m --views "" --cam=-5,.2,3.9,2,.55,2.6,24 --no-ruler
r --glb $E/UP05_Table.glb,$E/UP05_Burner.glb,$E/UP05_CushionNew.glb,$E/UP05_CushionOld.glb,$E/UP05_CushionNew.glb,$E/UP05_CushionOld.glb,$E/UP05_CushionNew.glb,$E/UP05_CushionNew.glb \
  --at="0,0,0;0.035,0.06,0,0.3;-1.2,-1.4,0;-.4,-1.4,0;.4,-1.4,0;1.2,-1.4,0;-.8,-2.2,0;.8,-2.2,0" --out $P/eye --tag UP05-lesson-layout-1p7m --views "" --cam=0,1.6,1.7,0,-1.2,.2,24 --ruler-x 1.6
# 4. side by side with existing work
r --glb $E/UP01.glb,$A/A01_straight_01.glb,$A/A04_SiltBar.glb --at="0,0,0;0,-7,0;2.5,-5,0" --out $P/compare --tag UP01-vs-waterhead-A01-A04 --views threequarter
r --glb $E/UP02_01.glb,$E/UP02_02.glb,$E/UP02_03.glb,$E/UP03.glb,$E/UP04.glb,$A/A06_MarkerStone.glb,$A/A04_SiltSide_02.glb --at="-2.6,0,0;-1.7,0,0;-1.0,0,0;-.3,0,0;.9,0,0;2.8,0,0;5.2,0,0" \
  --out $P/compare --tag creek-stones-vs-waterhead-A06-A04 --views front,threequarter
r --glb art/exports/qingxi-listening-terrace-v1.fbx,$E/UP05_Table.glb,$E/UP05_Burner.glb,$E/UP05_CushionNew.glb,$E/UP05_CushionOld.glb --at="0,0,0;0,-1.2,0,.72;.035,-1.14,0,1.02;-.5,-2.1,0,.72;.5,-2.1,0,.72" \
  --out $P/compare --tag UP05-on-listening-terrace --views threequarter
if [ -n "$D12" ] && [ -f "$D12/G01.glb" ]; then
  for L in day night; do
    gl=0; [ $L = night ] && gl=2
    r --glb $E/UP06.glb,$D12/G01.glb,$D12/TY04.glb --at="-.8,0,0;.2,0,0;1.4,0,0" --out $P/compare --tag lanterns-UP06-G01-TY04-$L --views front --glow $gl --light $L
  done
fi
# 7. close-ups at the distance the round-two references were judged at (afternoon light, no ruler)
C=$P/closeup
r --glb $E/UP01.glb --out $C --tag UP01-new-sluice --views "" --no-ruler --light afternoon --cam=-1.6,-3.6,2.6,0,-.2,2.3,35 --res 1400x1000
r --glb $E/UP01.glb --out $C --tag UP01-new-face --views "" --no-ruler --light afternoon --cam=-6,-9,3.2,0,0,1.4,30 --res 1600x900
r --glb $E/UP02_01.glb --out $C --tag UP02_01-new --views "" --no-ruler --light afternoon --cam=1.3,-1.6,1.0,0,0,0.2,45 --res 1200x800
r --glb $E/UP03.glb --out $C --tag UP03-new --views "" --no-ruler --light afternoon --cam=-.9,-1.6,1.1,0,0,.7,40 --res 900x1200
r --glb $E/UP04.glb --out $C --tag UP04-new --views "" --no-ruler --light afternoon --cam=1.2,-1.5,1.2,0,0,.1,40 --res 1300x900
r --glb $E/UP05_Table.glb,$E/UP05_Burner.glb,$E/UP05_CushionNew.glb,$E/UP05_CushionOld.glb --at="0,0,0;0.035,0.06,0,0.3;-0.25,-0.55,0;0.4,-0.55,0" --out $C --tag UP05-new --views "" --no-ruler --light afternoon --cam=.9,-1.7,.85,0.05,-.2,.12,40 --res 1400x900
r --glb $E/UP06.glb --out $C --tag UP06-new --views "" --no-ruler --light afternoon --glow 0 --cam=.45,-.55,.75,.1,0,.63,50 --res 900x900
# 9. wireframe close-ups of the QA items left after round three (qa-lod0.json), same cameras as qa-evidence/
W=$P/qa-evidence/wire
r --glb $E/UP01.glb --out $W --tag UP01-drumpost-plate-wire --views "" --no-ruler --wire --wire-mm .5 --cam=1.25,.2,3.5,.73,.56,3.37,50
r --glb $E/UP01.glb --out $W --tag UP01-face-4.33-wire --views "" --no-ruler --wire --wire-mm .8 --cam=4.6,-1.6,2.3,4.33,-.62,2.0,45 --mark="4.331,-.669,2.007,.012;4.02,-.613,2.007,.012"
r --glb $E/UP01.glb --out $W --tag UP01-face-6.17-wire --views "" --no-ruler --wire --wire-mm .8 --cam=6.9,-3.0,2.1,6.16,-1.36,1.46,40 --mark="6.155,-1.203,1.596,.015;6.174,-1.519,1.33,.015"
r --glb $E/UP01.glb --out $W --tag UP01-weed-strands-wire --views "" --no-ruler --wire --wire-mm .4 --cam=.55,-1.25,1.05,.32,-.48,.9,45 --mark=".324,-.509,.95,.006;.344,-.55,.847,.006;.343,-.561,.827,.006"
r --glb $E/UP02_02.glb --out $W --tag UP02_02-blade-on-stone-wire --views "" --no-ruler --wire --wire-mm .25 --cam=.45,-.55,.22,.166,-.14,.045,50 --mark=".166,-.14,.045,.003"
r --glb $E/UP03.glb --out $W --tag UP03-notch-wire --views "" --no-ruler --wire --wire-mm .3 --cam=-.05,-.65,.95,-.027,-.161,.882,50 --mark="-.027,-.161,.882,.004"
# 10. how each kind of loose piece rests on its support (qa-contact.json), UP01 close-ups on one sheet
K=$P/qa-evidence/contact
r --glb $E/UP01.glb --out $K --tag debris-jam --views "" --no-ruler --light afternoon --cam=.9,-2.4,1.5,0,-.6,1.0,35 --res 1200x900
r --glb $E/UP01.glb --out $K --tag joint-tufts --views "" --no-ruler --light afternoon --cam=-3.0,-2.2,.7,-3.32,-1.0,.39,45 --res 1200x900
r --glb $E/UP01.glb --out $K --tag ivy-on-face --views "" --no-ruler --light afternoon --cam=-4.9,-2.6,1.4,-5.3,-1.3,1.0,40 --res 1200x900
r --glb $E/UP01.glb --out $K --tag crest-tufts --views "" --no-ruler --light afternoon --cam=-1.6,-.9,2.9,-2.18,.42,2.21,40 --res 1200x900
r --glb $E/UP01.glb --out $K --tag foot-tufts-ferns --views "" --no-ruler --light afternoon --cam=2.6,-2.4,.6,2.97,-1.18,.05,45 --res 1200x900
r --glb $E/UP01.glb --out $K --tag fern-on-face --views "" --no-ruler --light afternoon --cam=1.6,-2.2,1.8,2.08,-.75,1.47,45 --res 1200x900
"${PYTHON:-python}" $SRC/compose_sheet.py $P/qa-evidence/contact-sheet.jpg "UP01 散件接觸（第三輪 settle 後）" 3   $K/debris-jam-cam.png="枯枝、細枝、水草：卡在原木和閘框上" $K/joint-tufts-cam.png="石縫草：根部嵌進石縫" $K/ivy-on-face-cam.png="常春藤：葉貼藤、藤貼壩面"   $K/crest-tufts-cam.png="壩頂草：根部在壩頂石上" $K/foot-tufts-ferns-cam.png="牆腳草叢與蕨：落在地面和碎石上" $K/fern-on-face-cam.png="壩面蕨：葉軸根部嵌進石縫"
# 8. round three vs round two as reviewed in #64 (d8411eaa), same light and camera, material and grey model.
#    OLD points at the round-two GLBs, e.g. for k in UP01 ...; do git show d8411eaa:art/exports/qingxi-day34-c/$k.glb | git lfs smudge > $OLD/$k.glb; done
#    The single renders go to RAW (not committed); compose_old_new.py puts each model's four on one sheet.
if [ -n "$OLD" ] && [ -f "$OLD/UP01.glb" ]; then
  RAW="${RAW:-${TMPDIR:-/tmp}/day34-old-new}"
  for k in UP01 UP02_01 UP02_02 UP02_03 UP03 UP04 UP05_CushionNew UP05_CushionOld UP05_Table UP05_Burner UP06; do
    g=""; case $k in UP06) g="--glow 0";; esac
    for v in old new; do
      f=$E/$k.glb; [ $v = old ] && f=$OLD/$k.glb
      r --glb $f --out $RAW --tag $k-$v-mat --views threequarter --no-ruler $g
      r --glb $f --out $RAW --tag $k-$v-clay --views threequarter --no-ruler --clay $g
    done
  done
  "${PYTHON:-python}" $SRC/compose_old_new.py "$RAW" $P/old-vs-new
fi
echo REVIEWS_DONE
