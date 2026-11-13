#!/bin/sh
# Unity check of C's village props (LV01–LV06) without changing apps/game: copies VillageLVVerify.cs into the project for one
# batch run, then removes it, the temporary model copies and the URP settings the run switches on.
#   UNITY=<Unity.exe 6000.3.28f1> sh art/source/village-life-c/unity/run_unity_check.sh   (from the repo root)
# Results: art/previews/village-life-c/unity/report.txt and renders; log in artifacts/unity-village.log.
set -e
U="${UNITY:?set UNITY to Unity.exe (6000.3.28f1, the version main uses since #92)}";HERE=art/source/village-life-c/unity
ED=apps/game/Assets/YunJing/Editor;M=apps/game/Assets/YunJing/Models/VillageC
cleanup(){
  rm -f "$ED/VillageLVVerify.cs" "$ED/VillageLVVerify.cs.meta"; rm -rf "$M" "$M.meta"
  git checkout -- apps/game/Assets/WebGLTemplates.meta apps/game/ProjectSettings/GraphicsSettings.asset apps/game/ProjectSettings/QualitySettings.asset apps/game/ProjectSettings/ShaderGraphSettings.asset 2>/dev/null || true
}
trap cleanup EXIT
cp "$HERE/VillageLVVerify.cs" "$ED/"
mkdir -p artifacts
"$U" -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.VillageLVVerify.Run -logFile artifacts/unity-village.log || true
grep -E "LV_VERIFY|error CS" artifacts/unity-village.log || echo "no verify line, see artifacts/unity-village.log"
