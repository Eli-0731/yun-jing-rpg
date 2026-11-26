#!/bin/sh
# Unity check of B's D2 fallen logs and stumps (DR06 …) without changing apps/game: copies D2LogsVerify.cs into the project for one batch
# run, then removes it, the temporary model copies and the URP settings the run switches on.
#   UNITY=<Unity.exe 6000.3.28f1> sh art/source/d2-logs-b/unity/run_unity_check.sh   (from the repo root)
# Results: art/previews/d2-logs-b/<asset>/unity/report.txt and renders; log in artifacts/unity-d2-logs.log.
set -e
U="${UNITY:?set UNITY to Unity.exe (6000.3.28f1)}";HERE=art/source/d2-logs-b/unity
ED=apps/game/Assets/YunJing/Editor;M=apps/game/Assets/YunJing/Models/D2LogsB;R=apps/game/Assets/D2LogsBRawCheck
cleanup(){
  rm -f "$ED/D2LogsVerify.cs" "$ED/D2LogsVerify.cs.meta"; rm -rf "$M" "$M.meta" "$R" "$R.meta"
  git checkout -- apps/game/Assets/WebGLTemplates.meta apps/game/ProjectSettings apps/game/Packages 2>/dev/null || true
}
trap cleanup EXIT
cp "$HERE/D2LogsVerify.cs" "$ED/"
mkdir -p artifacts
"$U" -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.D2LogsVerify.Run -logFile artifacts/unity-d2-logs.log || true
grep -E "DR_VERIFY|error CS" artifacts/unity-d2-logs.log || echo "no verify line, see artifacts/unity-d2-logs.log"
