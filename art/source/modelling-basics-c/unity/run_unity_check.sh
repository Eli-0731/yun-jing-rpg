#!/bin/sh
# Unity check of C's modelling-basics models without changing apps/game: copies QingxiBasicsVerify.cs into the project for one
# batch run, then removes it, the temporary model copies and the URP settings the run switches on.
#   UNITY=<Unity.exe 6000.0.82f1> sh art/source/modelling-basics-c/unity/run_unity_check.sh   (from the repo root)
# Results: art/previews/modelling-basics-c/unity/report.txt and renders; log in artifacts/unity-basics.log.
set -e
U="${UNITY:?set UNITY to Unity.exe (6000.0.82f1)}";HERE=art/source/modelling-basics-c/unity
ED=apps/game/Assets/YunJing/Editor;M=apps/game/Assets/YunJing/Models/BasicsC
cleanup(){
  rm -f "$ED/QingxiBasicsVerify.cs" "$ED/QingxiBasicsVerify.cs.meta"; rm -rf "$M" "$M.meta"
  git checkout -- apps/game/ProjectSettings/GraphicsSettings.asset apps/game/ProjectSettings/QualitySettings.asset 2>/dev/null || true
}
trap cleanup EXIT
cp "$HERE/QingxiBasicsVerify.cs" "$ED/"
mkdir -p artifacts
"$U" -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.QingxiBasicsVerify.Run -logFile artifacts/unity-basics.log || true
grep -E "BASICS_VERIFY|error CS" artifacts/unity-basics.log || echo "no verify line, see artifacts/unity-basics.log"
