#!/bin/sh
# Unity check of C's ground stones and mushrooms (GC01–GC06) without changing apps/game: copies GroundGCVerify.cs into the project for one
# batch run, then removes it, the temporary model copies and the URP settings the run switches on.
#   UNITY=<Unity.exe 6000.3.28f1> sh art/source/ground-cover-c/unity/run_unity_check.sh   (from the repo root)
# Results: art/previews/ground-cover-c/unity/report.txt and renders; log in artifacts/unity-ground.log.
set -e
U="${UNITY:?set UNITY to Unity.exe (6000.3.28f1, the version main uses since #92)}";HERE=art/source/ground-cover-c/unity
ED=apps/game/Assets/YunJing/Editor;M=apps/game/Assets/YunJing/Models/GroundC
cleanup(){
  rm -f "$ED/GroundGCVerify.cs" "$ED/GroundGCVerify.cs.meta"; rm -rf "$M" "$M.meta"
  git checkout -- apps/game/Assets/WebGLTemplates.meta apps/game/ProjectSettings/GraphicsSettings.asset apps/game/ProjectSettings/QualitySettings.asset apps/game/ProjectSettings/ShaderGraphSettings.asset 2>/dev/null || true
}
trap cleanup EXIT
cp "$HERE/GroundGCVerify.cs" "$ED/"
mkdir -p artifacts
"$U" -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.GroundGCVerify.Run -logFile artifacts/unity-ground.log || true
grep -E "GC_VERIFY|error CS" artifacts/unity-ground.log || echo "no verify line, see artifacts/unity-ground.log"
