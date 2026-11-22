#!/bin/sh
# Unity check of C's D2 floor smalls (DP01 …) without changing apps/game: copies D2FloorVerify.cs into the project for one
# batch run, then removes it, the temporary model copies and the URP settings the run switches on.
#   UNITY=<Unity.exe 6000.3.28f1> sh art/source/d2-floor-c/unity/run_unity_check.sh   (from the repo root)
# Results: art/previews/d2-floor-c/unity/report.txt and renders; log in artifacts/unity-d2-floor.log.
set -e
U="${UNITY:?set UNITY to Unity.exe (6000.3.28f1, the version main uses since #92)}";HERE=art/source/d2-floor-c/unity
ED=apps/game/Assets/YunJing/Editor;M=apps/game/Assets/YunJing/Models/D2FloorC
cleanup(){
  rm -f "$ED/D2FloorVerify.cs" "$ED/D2FloorVerify.cs.meta"; rm -rf "$M" "$M.meta"
  git checkout -- apps/game/Assets/WebGLTemplates.meta apps/game/ProjectSettings/GraphicsSettings.asset apps/game/ProjectSettings/QualitySettings.asset apps/game/ProjectSettings/ShaderGraphSettings.asset 2>/dev/null || true
}
trap cleanup EXIT
cp "$HERE/D2FloorVerify.cs" "$ED/"
mkdir -p artifacts
"$U" -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.D2FloorVerify.Run -logFile artifacts/unity-d2-floor.log || true
grep -E "DP_VERIFY|error CS" artifacts/unity-d2-floor.log || echo "no verify line, see artifacts/unity-d2-floor.log"
