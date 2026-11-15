#!/bin/sh
# Unity check of C's yard and roadside props (VG01–VG08) without changing apps/game: copies YardVGVerify.cs into the project for one
# batch run, then removes it, the temporary model copies and the URP settings the run switches on.
#   UNITY=<Unity.exe 6000.3.28f1> sh art/source/yard-roadside-c/unity/run_unity_check.sh   (from the repo root)
# Results: art/previews/yard-roadside-c/unity/report.txt and renders; log in artifacts/unity-yard.log.
set -e
U="${UNITY:?set UNITY to Unity.exe (6000.3.28f1, the version main uses since #92)}";HERE=art/source/yard-roadside-c/unity
ED=apps/game/Assets/YunJing/Editor;M=apps/game/Assets/YunJing/Models/YardC
cleanup(){
  rm -f "$ED/YardVGVerify.cs" "$ED/YardVGVerify.cs.meta"; rm -rf "$M" "$M.meta"
  git checkout -- apps/game/Assets/WebGLTemplates.meta apps/game/ProjectSettings/GraphicsSettings.asset apps/game/ProjectSettings/QualitySettings.asset apps/game/ProjectSettings/ShaderGraphSettings.asset 2>/dev/null || true
}
trap cleanup EXIT
cp "$HERE/YardVGVerify.cs" "$ED/"
mkdir -p artifacts
"$U" -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.YardVGVerify.Run -logFile artifacts/unity-yard.log || true
grep -E "VG_VERIFY|error CS" artifacts/unity-yard.log || echo "no verify line, see artifacts/unity-yard.log"
