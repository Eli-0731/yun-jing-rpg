#!/bin/sh
# Unity check of C's creekside props (WL01–WL05, FI01–FI05) without changing apps/game: copies CreeksideWLVerify.cs into the project for one
# batch run, then removes it, the temporary model copies and the URP settings the run switches on.
#   UNITY=<Unity.exe 6000.3.28f1> sh art/source/creekside-life-c/unity/run_unity_check.sh   (from the repo root)
# Results: art/previews/creekside-life-c/unity/report.txt and renders; log in artifacts/unity-creekside.log.
set -e
U="${UNITY:?set UNITY to Unity.exe (6000.3.28f1, the version main uses since #92)}";HERE=art/source/creekside-life-c/unity
ED=apps/game/Assets/YunJing/Editor;M=apps/game/Assets/YunJing/Models/CreeksideC
cleanup(){
  rm -f "$ED/CreeksideWLVerify.cs" "$ED/CreeksideWLVerify.cs.meta"; rm -rf "$M" "$M.meta"
  git checkout -- apps/game/Assets/WebGLTemplates.meta apps/game/ProjectSettings/GraphicsSettings.asset apps/game/ProjectSettings/QualitySettings.asset apps/game/ProjectSettings/ShaderGraphSettings.asset 2>/dev/null || true
}
trap cleanup EXIT
cp "$HERE/CreeksideWLVerify.cs" "$ED/"
mkdir -p artifacts
"$U" -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.CreeksideWLVerify.Run -logFile artifacts/unity-creekside.log || true
grep -E "WL_VERIFY|error CS" artifacts/unity-creekside.log || echo "no verify line, see artifacts/unity-creekside.log"
