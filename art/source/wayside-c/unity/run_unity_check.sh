#!/bin/sh
# Unity check of C's wayside props (WS01–WS06) without changing apps/game: copies WaysideWSVerify.cs into the project for one
# batch run, then removes it, the temporary model copies and the URP settings the run switches on.
#   UNITY=<Unity.exe 6000.3.28f1> sh art/source/wayside-c/unity/run_unity_check.sh   (from the repo root)
# Results: art/previews/wayside-c/unity/report.txt and renders; log in artifacts/unity-wayside.log.
set -e
U="${UNITY:?set UNITY to Unity.exe (6000.3.28f1, the version main uses since #92)}";HERE=art/source/wayside-c/unity
ED=apps/game/Assets/YunJing/Editor;M=apps/game/Assets/YunJing/Models/WaysideC
cleanup(){
  rm -f "$ED/WaysideWSVerify.cs" "$ED/WaysideWSVerify.cs.meta"; rm -rf "$M" "$M.meta"
  git checkout -- apps/game/Assets/WebGLTemplates.meta apps/game/ProjectSettings/GraphicsSettings.asset apps/game/ProjectSettings/QualitySettings.asset apps/game/ProjectSettings/ShaderGraphSettings.asset 2>/dev/null || true
}
trap cleanup EXIT
cp "$HERE/WaysideWSVerify.cs" "$ED/"
mkdir -p artifacts
"$U" -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.WaysideWSVerify.Run -logFile artifacts/unity-wayside.log || true
grep -E "WS_VERIFY|error CS" artifacts/unity-wayside.log || echo "no verify line, see artifacts/unity-wayside.log"
