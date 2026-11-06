"""Re-import the alchemy table GLB and FBX into empty scenes and compare with model_info.json."""
import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
NAME = "QX_AlchemyWorkTable_v001"
info = json.loads((ROOT / f"art/exports/qingxi-alchemy-table-v1/{NAME}_model_info.json").read_text(encoding="utf-8"))
sys.path.insert(0, str(Path.home() / ".claude/skills/blender-asset-qa/scripts"))
import qa_check


def measure(importer, path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    importer(filepath=str(path))
    meshes = [o for o in bpy.data.objects if o.type == "MESH" and not o.name.endswith("_LOD1")]
    pts = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
    size = [round(max(p[i] for p in pts) - min(p[i] for p in pts), 3) for i in range(3)]
    tris = sum(len(p.vertices) - 2 for o in meshes for p in o.data.polygons)
    report = qa_check.run(objects=[o.name for o in meshes], profile="game", tol=0.004)
    return {"size_xyz": size, "ground_z": round(min(p.z for p in pts), 4), "triangles": tris,
            "materials": sorted({m.name for o in meshes for m in o.data.materials if m}),
            "qa_errors": len(report["errors"]), "qa_warnings": report["warnings"][:5]}


result = {
    "expected": {"size_xyz": info["dimensions_m"], "triangles": info["triangles"]},
    "glb": measure(bpy.ops.import_scene.gltf, ROOT / f"art/exports/qingxi-alchemy-table-v1/{NAME}.glb"),
    "fbx": measure(bpy.ops.import_scene.fbx, ROOT / f"apps/game/Assets/YunJing/Models/AlchemyTableV1/{NAME}.fbx"),
}
ok = all(abs(a - b) < 0.01 for a, b in zip(result["glb"]["size_xyz"], info["dimensions_m"])) \
    and all(abs(a - b) < 0.01 for a, b in zip(result["fbx"]["size_xyz"], info["dimensions_m"])) \
    and result["glb"]["qa_errors"] == 0 and result["fbx"]["qa_errors"] == 0
result["pass"] = ok
(ROOT / "art/exports/qingxi-alchemy-table-v1/roundtrip-report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print("@@ROUNDTRIP@@" + json.dumps(result, ensure_ascii=False))
if not ok:
    raise SystemExit("round trip mismatch")
