#!/bin/sh
# Unity check of C's yard props (YP01–YP13) without changing apps/game: copies YardYPVerify.cs into the project for one
# batch run, then removes it, the temporary model copies and the URP settings the run switches on.
#   UNITY=<Unity.exe 6000.3.28f1> sh art/source/yard-props-c/unity/run_unity_check.sh   (from the repo root)
# Results: art/previews/yard-props-c/unity/report.txt and renders; log in artifacts/unity-yard-props.log.
set -e
U="${UNITY:?set UNITY to Unity.exe (6000.3.28f1, the version main uses since #92)}";HERE=art/source/yard-props-c/unity
ED=apps/game/Assets/YunJing/Editor;M=apps/game/Assets/YunJing/Models/YardPropsC
cleanup(){
  rm -f "$ED/YardYPVerify.cs" "$ED/YardYPVerify.cs.meta"; rm -rf "$M" "$M.meta"
  git checkout -- apps/game/Assets/WebGLTemplates.meta apps/game/ProjectSettings/GraphicsSettings.asset apps/game/ProjectSettings/QualitySettings.asset apps/game/ProjectSettings/ShaderGraphSettings.asset 2>/dev/null || true
}
trap cleanup EXIT
cp "$HERE/YardYPVerify.cs" "$ED/"
mkdir -p artifacts
"$U" -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.YardYPVerify.Run -logFile artifacts/unity-yard-props.log || true
grep -E "YP_VERIFY|error CS" artifacts/unity-yard-props.log || echo "no verify line, see artifacts/unity-yard-props.log"
