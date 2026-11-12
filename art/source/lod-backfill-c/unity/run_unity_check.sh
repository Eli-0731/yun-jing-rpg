#!/bin/sh
# Unity check of C's old-set LOD backfill (#34 Q01–Q04, #35 C01–C08) without changing apps/game: copies LodCVerify.cs into the project for one
# batch run, then removes it, the temporary model copies and the URP settings the run switches on.
#   UNITY=<Unity.exe 6000.3.28f1> sh art/source/lod-backfill-c/unity/run_unity_check.sh   (from the repo root)
# Results: art/previews/lod-backfill-c/unity/report.txt and renders; log in artifacts/unity-lodc.log.
set -e
U="${UNITY:?set UNITY to Unity.exe (6000.3.28f1, the version main uses since #92)}";HERE=art/source/lod-backfill-c/unity
ED=apps/game/Assets/YunJing/Editor;M=apps/game/Assets/YunJing/Models/LodBackfillC
cleanup(){
  rm -f "$ED/LodCVerify.cs" "$ED/LodCVerify.cs.meta"; rm -rf "$M" "$M.meta"
  git checkout -- apps/game/Assets/WebGLTemplates.meta apps/game/ProjectSettings/GraphicsSettings.asset apps/game/ProjectSettings/QualitySettings.asset apps/game/ProjectSettings/ShaderGraphSettings.asset 2>/dev/null || true
}
trap cleanup EXIT
cp "$HERE/LodCVerify.cs" "$ED/"
mkdir -p artifacts
"$U" -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.LodCVerify.Run -logFile artifacts/unity-lodc.log || true
grep -E "LODC_VERIFY|error CS" artifacts/unity-lodc.log || echo "no verify line, see artifacts/unity-lodc.log"
