#!/bin/sh
# Unity check of C's D2 mushrooms (DP01 …) without changing apps/game: copies D2MushroomVerify.cs into the project for one
# batch run, then removes it, the temporary model copies and the URP settings the run switches on.
#   UNITY=<Unity.exe 6000.3.28f1> sh art/source/d2-mushrooms-c/unity/run_unity_check.sh   (from the repo root)
# Results: art/previews/d2-mushrooms-c/unity/report.txt and renders; log in artifacts/unity-d2-mushrooms.log.
set -e
U="${UNITY:?set UNITY to Unity.exe (6000.3.28f1, the version main uses since #92)}";HERE=art/source/d2-mushrooms-c/unity
ED=apps/game/Assets/YunJing/Editor;M=apps/game/Assets/YunJing/Models/D2MushroomsC
cleanup(){
  rm -f "$ED/D2MushroomVerify.cs" "$ED/D2MushroomVerify.cs.meta"; rm -rf "$M" "$M.meta"
  git checkout -- apps/game/Assets/WebGLTemplates.meta apps/game/ProjectSettings/GraphicsSettings.asset apps/game/ProjectSettings/QualitySettings.asset apps/game/ProjectSettings/ShaderGraphSettings.asset 2>/dev/null || true
}
trap cleanup EXIT
cp "$HERE/D2MushroomVerify.cs" "$ED/"
mkdir -p artifacts
"$U" -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.D2MushroomVerify.Run -logFile artifacts/unity-d2-mushrooms.log || true
grep -E "DP_VERIFY|error CS" artifacts/unity-d2-mushrooms.log || echo "no verify line, see artifacts/unity-d2-mushrooms.log"
