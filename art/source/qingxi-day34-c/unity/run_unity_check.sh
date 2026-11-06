#!/bin/sh
# Unity check of the C day 3-4 models without changing apps/game: copies QingxiDay34Verify.cs into the project for one
# batch run, then removes it, the temporary model copies and the URP settings the run switches on.
#   UNITY=<Unity.exe 6000.0.82f1> sh art/source/qingxi-day34-c/unity/run_unity_check.sh   (from the repo root)
# Results: art/previews/qingxi-day34-c/unity/report.txt and renders; log in artifacts/unity-day34.log.
set -e
U="${UNITY:?set UNITY to Unity.exe (6000.0.82f1)}";HERE=art/source/qingxi-day34-c/unity
ED=apps/game/Assets/YunJing/Editor;M=apps/game/Assets/YunJing/Models/Day34C
cleanup(){
  rm -f "$ED/QingxiDay34Verify.cs" "$ED/QingxiDay34Verify.cs.meta"; rm -rf "$M" "$M.meta"
  git checkout -- apps/game/ProjectSettings/GraphicsSettings.asset apps/game/ProjectSettings/QualitySettings.asset 2>/dev/null || true
}
trap cleanup EXIT
cp "$HERE/QingxiDay34Verify.cs" "$ED/"
mkdir -p artifacts
"$U" -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.QingxiDay34Verify.Run -logFile artifacts/unity-day34.log || true
grep -E "DAY34_VERIFY|error CS" artifacts/unity-day34.log || echo "no verify line, see artifacts/unity-day34.log"
