"""Independent Blender FBX/GLB reimport and source-dimension comparison."""
import bpy
import json
import sys
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[3]
version=sys.argv[sys.argv.index("--")+1] if "--" in sys.argv else "v010"
SOURCE=ROOT/"art/source/valley-and-home-v1/RI01"/f"RI01-paddy-pack-{version}.blend"
EXPORT=ROOT/"art/exports/valley-and-home-v1/RI01"/version
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))

def bounds(obj):
    vertices=[obj.matrix_world@Vector(corner) for corner in obj.bound_box]
    low=[min(v[i] for v in vertices) for i in range(3)]
    high=[max(v[i] for v in vertices) for i in range(3)]
    return [high[i]-low[i] for i in range(3)]

def triangles(obj):
    return sum(len(p.vertices)-2 for p in obj.data.polygons)

source={o.name:{"dimensions":bounds(o),"triangles":triangles(o)}
        for o in bpy.data.objects if o.type=="MESH" and
        (o.name.startswith("SM_RI01_") or o.name.startswith("Detail_RI01_"))}
results={}
for asset in ("RI01_Paddy","RI01_Bund_Straight","RI01_Bund_Corner","RI01_Bund_T"):
    for ext in ("fbx","glb"):
        path=EXPORT/(asset+"."+ext)
        bpy.ops.wm.read_factory_settings(use_empty=True)
        if ext=="fbx":
            bpy.ops.import_scene.fbx(filepath=str(path))
        else:
            bpy.ops.import_scene.gltf(filepath=str(path))
        found={o.name:o for o in bpy.data.objects if o.type=="MESH"}
        missing=[name for name in source if name.startswith("SM_RI01_Paddy_") or
                 name.startswith("SM_RI01_State_") or name.startswith("Detail_RI01_")]
        if asset!="RI01_Paddy":
            kind=asset.split("_")[-1]
            missing=[name for name in source if name.startswith("SM_RI01_Bund_"+kind+"_")]
        entries={}
        for name in missing:
            obj=found.get(name)
            if obj is None: continue
            dims=bounds(obj)
            want=source[name]
            entries[name]={"triangles":triangles(obj),
                           "triangle_match":triangles(obj)==want["triangles"],
                           "dimensions_m":dims,
                           "dimension_error_m":max(abs(a-b) for a,b in zip(dims,want["dimensions"]))}
        results[asset+"."+ext]={"file_bytes":path.stat().st_size,
            "expected_meshes":len(missing),"imported_meshes":len(entries),
            "missing":sorted(set(missing)-set(entries)),
            "max_dimension_error_m":max((x["dimension_error_m"] for x in entries.values()),default=None),
            "triangle_mismatch":[k for k,v in entries.items() if not v["triangle_match"]],
            "meshes":entries}
    
report={"source":str(SOURCE),"results":results,
        "pass":all(x["file_bytes"]>0 and x["imported_meshes"]==x["expected_meshes"] and
                   not x["triangle_mismatch"] and x["max_dimension_error_m"] is not None and
                   x["max_dimension_error_m"]<=0.02 for x in results.values())}
(EXPORT/"reimport_validation.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
print("@@RI01REIMPORT@@"+json.dumps({"pass":report["pass"],"assets":{
    k:{p:v for p,v in r.items() if p!="meshes"} for k,r in results.items()}},ensure_ascii=False))
