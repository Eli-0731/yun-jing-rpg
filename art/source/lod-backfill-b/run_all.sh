#!/bin/bash
# 補 LOD 全批：每件跑 lod_backfill.py（匯出）＋ lod_compare.py（前後對照圖），可重跑。
# 用法：bash art/source/lod-backfill-b/run_all.sh [ID ...]      （不給 ID 就跑 jobs.json 全部）
cd "$(dirname "$0")/../../.." || exit 1
B="${BLENDER:-/c/Program Files/Blender Foundation/Blender 5.2/blender.exe}"
T=art/source/lod-backfill-b; OUT=art/exports/lod-backfill-b; PV=art/previews/lod-backfill-b
IDS="$*"
[ -z "$IDS" ] && IDS=$(python -c "import json;print(' '.join(json.load(open('$T/jobs.json',encoding='utf-8'))))" 2>/dev/null || "/c/Users/joshs/.local/bin/uv.exe" run --offline --no-project python -I -c "import json;print(' '.join(json.load(open('$T/jobs.json',encoding='utf-8'))))")
for A in $IDS; do
  "$B" --background --factory-startup --python $T/lod_backfill.py -- $T/jobs.json $A "$PWD/$OUT" 2>&1 | grep -E "LODINFO|Error|Traceback" | head -5
  "$B" --background "$OUT/$A/${A}_LOD_v001.blend" --python $T/lod_compare.py -- $A "$PWD/$PV/$A" material 2>&1 | grep -E "PANEL|Error" | head -6
done
