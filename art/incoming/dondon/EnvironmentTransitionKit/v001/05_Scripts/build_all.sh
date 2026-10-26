#!/bin/bash
# Full v01 pipeline, in order.  Every step refuses to overwrite, so move old outputs away first.
#   BLENDER=/path/to/blender 05_Scripts/build_all.sh [--skip-textures] [--skip-models]
# Textures -> 3 kit .blend files -> connector QA with assembly renders -> FBX export + re-import check ->
# D01/D02 bridges -> 11 previews per module -> showcase + labels -> material sheet (REF_F) -> group sheets + crop check ->
# protected-asset recheck -> final reports.
set -euo pipefail
B=${BLENDER:-blender}
KIT="$(cd "$(dirname "$0")/.." && pwd)"; S="$KIT/05_Scripts"; cd "$KIT"
run() { "$B" -b --python-exit-code 1 --python "$S/$1" -- "${@:2}"; }
FILES=(road_edge_modules riverbank_modules bridgehead_modules)
if [[ " $* " != *" --skip-textures "* ]]; then
  run bake_textures.py; python3 "$S/make_card_texture.py"
fi
if [[ " $* " != *" --skip-models "* ]]; then
  declare -A GF=([A]=road_edge_modules [B]=riverbank_modules [C]=bridgehead_modules)
  for g in A B C; do run generate_modules.py --stage final --group $g --out 01_Blender/${GF[$g]}_v01.blend; done
fi
ALL=01_Blender/road_edge_modules_v01.blend,01_Blender/riverbank_modules_v01.blend,01_Blender/bridgehead_modules_v01.blend
run validate_connectors.py --files "$ALL" --name final_all29 --render
run export_fbx.py --file 01_Blender/road_edge_modules_v01.blend --helpers
run export_fbx.py --file 01_Blender/riverbank_modules_v01.blend
run export_fbx.py --file 01_Blender/bridgehead_modules_v01.blend --helpers
run export_fbx.py --verify --name fbx_reimport_v01
run generate_log_bridge.py          # D01 (optional single-log bridge)
run generate_timber_bridge.py       # D02 timber bridge used by the showcase
for f in "${FILES[@]}"; do run render_previews.py --file 01_Blender/${f}_v01.blend --out 04_Previews/Individual --samples 32 --ortho-samples 12; done
run render_showcase.py --name showcase_v01 --samples 64
python3 "$S/annotate_showcase.py" --name showcase_v01
run render_material_sheet.py; python3 "$S/make_ref_f.py"
python3 "$S/write_final_reports.py" --sheets
python3 "$S/phase0_safety_check.py" "$(dirname "$KIT")" --final "$KIT"
echo "Look at 04_Previews/Sheets and the showcase, then: python3 $S/write_final_reports.py --reports"
