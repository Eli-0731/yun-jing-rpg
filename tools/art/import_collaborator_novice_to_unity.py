"""Convert four reviewed collaborator GLBs to Unity FBX without editing meshes.

Run from the repository root with Blender 5.2:
  blender -b -P tools/art/import_collaborator_novice_to_unity.py
The original GLBs and author records remain in art/exports.
"""

import json
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "apps/game/Assets/YunJing/Models/CollaboratorNoviceV1"
MODELS = {
    "village-board": ("Eli-0731", "art/exports/qingxi-village-signs-v1/Q01.glb"),
    "training-shelter": ("Johnnnny0823", "art/exports/qingxi-training-yard-v1/training-shelter.glb"),
    "return-table": ("Eli-0731", "art/exports/qingxi-return-c/C02.glb"),
    "alchemy-furnace": ("joshsu54", "art/exports/qingxi-alchemy-b/B01_BronzeFurnace/v001/B01_BronzeFurnace_cold.glb"),
}


def mesh_stats():
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    return len(meshes), sum(len(o.data.polygons) for o in meshes)


def convert(name, author, relative):
    source = ROOT / relative
    if source.read_bytes()[:4] != b"glTF":
        raise RuntimeError(f"Missing full Git LFS source: {source}")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    imported = mesh_stats()
    if imported[0] == 0:
        raise RuntimeError(f"No mesh in {source}")
    target = DEST / f"{name}.fbx"
    bpy.ops.export_scene.fbx(
        filepath=str(target), use_selection=False, object_types={"MESH", "EMPTY"},
        axis_forward="-Z", axis_up="Y", apply_scale_options="FBX_SCALE_ALL",
        bake_space_transform=True, use_mesh_modifiers=True, mesh_smooth_type="FACE",
        add_leaf_bones=False, bake_anim=False, path_mode="COPY", embed_textures=True,
    )
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(target))
    returned = mesh_stats()
    if imported != returned or target.stat().st_size < 1000:
        raise RuntimeError(f"Roundtrip mismatch for {name}: {imported} -> {returned}")
    return {"name": name, "originalAuthor": author, "source": relative,
            "fbx": str(target.relative_to(ROOT)).replace("\\", "/"),
            "meshes": imported[0], "polygons": imported[1], "bytes": target.stat().st_size,
            "roundtrip": True}


DEST.mkdir(parents=True, exist_ok=True)
result = [convert(name, author, relative) for name, (author, relative) in MODELS.items()]
(DEST / "conversion-report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print("QINGXI_COLLABORATOR_FBX_OK", json.dumps(result, ensure_ascii=False))
