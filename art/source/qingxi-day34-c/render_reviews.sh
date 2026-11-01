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
echo REVIEWS_DONE
