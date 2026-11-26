"""QA exported RI01 GLBs by mutually exclusive state and LOD combinations."""
import bpy
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
version=sys.argv[sys.argv.index("--")+1] if "--" in sys.argv else "v014"
EXPORT=ROOT/"art/exports/valley-and-home-v1/RI01"/version
sys.path.insert(0,r"C:\Users\User\.agents\skills\blender-asset-qa\scripts")
import qa_check
summary={}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(EXPORT/"RI01_Paddy.glb"))
for lod in range(3):
    for state in ("Dry","Flooded","Grown"):
        names=[f"SM_RI01_Paddy_Base_LOD{lod}",f"SM_RI01_State_{state}_LOD{lod}"]
        if lod==0:names.append("Detail_RI01_Bund_EdgeGrass_LOD0")
        result=qa_check.run(objects=names,profile="game")
        key=f"Paddy_{state}_LOD{lod}"
        (EXPORT/f"qa_{key}.json").write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
        summary[key]={"pass":result["pass"],"errors":result["errors"],
                      "warning_count":len(result["warnings"])}
for kind in ("Straight","Corner","T"):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(EXPORT/f"RI01_Bund_{kind}.glb"))
    for lod in range(3):
        key=f"Bund_{kind}_LOD{lod}"
        result=qa_check.run(objects=[f"SM_RI01_Bund_{kind}_LOD{lod}"],profile="game")
        (EXPORT/f"qa_{key}.json").write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
        summary[key]={"pass":result["pass"],"errors":result["errors"],
                      "warning_count":len(result["warnings"])}
(EXPORT/"qa_summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding="utf-8")
print("@@RI01FINALQA@@"+json.dumps({k:{"pass":v["pass"],"errors":len(v["errors"]),
                                    "warnings":v["warning_count"],"first_error":v["errors"][:1]}
                               for k,v in summary.items()},ensure_ascii=False))
