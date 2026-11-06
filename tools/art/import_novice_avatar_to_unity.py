"""Re-export the original Qingxi novice study mesh to the Unity walk-through.

The source was modeled after the saved AI three-view at
art/references/qingxi-novice-cultivator-v1/three-view.png. It is a playable
prototype, not the finished Heroine-01 design or a third-party model.
Run from the repository root with Blender 5.2:
  blender -b -P tools/art/import_novice_avatar_to_unity.py
"""

from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "art/exports/qingxi-entry-assets-v13/novice-cultivator-v13.glb"
REFERENCE = ROOT / "art/references/qingxi-novice-cultivator-v1/three-view.png"
TARGET = ROOT / "apps/game/Assets/QingxiWorld/Models/ArtV001/NoviceCultivatorV1.fbx"

if not REFERENCE.is_file() or SOURCE.read_bytes()[:4] != b"glTF":
    raise RuntimeError("Saved three-view or full GLB source is missing")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
before = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
if not before:
    raise RuntimeError("Novice study has no meshes")
polygons = sum(len(obj.data.polygons) for obj in before)
bpy.ops.export_scene.fbx(
    filepath=str(TARGET), use_selection=False, object_types={"MESH", "EMPTY"},
    axis_forward="-Z", axis_up="Y", apply_scale_options="FBX_SCALE_ALL",
    bake_space_transform=True, use_mesh_modifiers=True, mesh_smooth_type="FACE",
    add_leaf_bones=False, bake_anim=False, path_mode="COPY", embed_textures=True,
)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(TARGET))
after = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
if len(after) != len(before) or sum(len(obj.data.polygons) for obj in after) != polygons:
    raise RuntimeError("Novice FBX roundtrip changed mesh or polygon count")
print(f"QINGXI_NOVICE_FBX_OK meshes={len(after)} polygons={polygons} bytes={TARGET.stat().st_size}")
