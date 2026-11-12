#!/bin/sh
# Before/after images for C's old-set LOD backfill (from the repo root). Blender 4.5.3: BL=<blender.exe>.
#   BL=<blender> sh art/source/lod-backfill-c/render_lod.sh
# For each item: the source GLB as delivered (before: LOD0 only), LOD1 and LOD2 from the new FBX, wireframes of LOD0 and
# LOD2, same camera and light; then one sheet per set. QA (strict, loose) on each LOD of the new FBX via a GLB re-export.
BL="${BL:?set BL to blender.exe}";R=art/source/creekside-life-c;P=art/previews/lod-backfill-c;E=art/exports/lod-backfill-c
m(){ cygpath -m "$1" 2>/dev/null || echo "$1"; }
r(){ MSYS_NO_PATHCONV=1 "$BL" -b --factory-startup -P "$(m $R/render_wl.py)" -- "$@" 2>&1 | grep -E "Error|Traceback"; true; }
for src in art/exports/qingxi-village-signs-v1/Q01.glb art/exports/qingxi-village-signs-v1/Q02.glb art/exports/qingxi-village-signs-v1/Q03.glb art/exports/qingxi-village-signs-v1/Q04.glb \
           art/exports/qingxi-return-c/C01.glb art/exports/qingxi-return-c/C02.glb art/exports/qingxi-return-c/C03.glb art/exports/qingxi-return-c/C04.glb \
           art/exports/qingxi-return-c/C05.glb art/exports/qingxi-return-c/C06.glb art/exports/qingxi-return-c/C07.glb art/exports/qingxi-return-c/C08.glb; do
  id=$(basename $src .glb);D=$P/$id;F=$E/$id/${id}_LOD_v001.fbx;mkdir -p $D
  r --glb "$(m $src)" --out "$(m $D)" --tag $id-before --views threequarter --no-ruler --samples 48
  for L in 1 2; do r --glb "$(m $F)" --out "$(m $D)" --tag $id-LOD$L --views threequarter --lod $L --no-ruler --samples 48; done
  for L in 0 2; do r --glb "$(m $F)" --out "$(m $D)" --tag $id-LOD$L --views "" --wire --lod $L --no-ruler --samples 16; done
done
