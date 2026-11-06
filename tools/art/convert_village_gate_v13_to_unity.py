"""Village gate v13 (core group) GLB -> one Unity FBX for the gate-square slot.

The GLB has 319 objects; they are joined into one mesh (materials kept as slots) so the gate costs a few
draw calls instead of hundreds. Origin goes to the base centre at height 0 (grounding spec), the model's
front stays -Y in Blender (= +Z in Unity). Writes the FBX, a model_info.json and a QA report.

blender -b --factory-startup --python tools/art/convert_village_gate_v13_to_unity.py
"""
import json
import os
import sys

import bpy
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "art", "exports", "qingxi-entry-assets-v13", "village-gate-v13.glb")
OUT_DIR = os.path.join(ROOT, "apps", "game", "Assets", "YunJing", "Models", "QingxiEntryV13")
FBX = os.path.join(OUT_DIR, "QX_VillageGate_v13.fbx")
INFO = os.path.join(ROOT, "art", "exports", "qingxi-entry-assets-v13", "village-gate-v13_unity_model_info.json")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
if not meshes:
    sys.exit("no meshes in " + SRC)

# Bake parent transforms, then join everything into one object.
for o in bpy.context.scene.objects:
    o.select_set(False)
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.join()
gate = bpy.context.view_layer.objects.active
gate.name = "SM_QX_VillageGate_v13"
for o in list(bpy.context.scene.objects):
    if o != gate:
        bpy.data.objects.remove(o, do_unlink=True)

# Origin at the base centre, base at z = 0.
corners = [gate.matrix_world @ Vector(c) for c in gate.bound_box]
lo = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
hi = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
base = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
gate.data.transform(__import__("mathutils").Matrix.Translation(-base))
gate.location = (0, 0, 0)
dims = [round(hi.x - lo.x, 3), round(hi.y - lo.y, 3), round(hi.z - lo.z, 3)]

sys.path.insert(0, r"C:\Users\User\.claude\skills\blender-asset-qa\scripts")
try:
    import qa_check
    qa = qa_check.run([gate.name], "game", 0.001)
except Exception as e:  # QA is a report, not a gate for the conversion itself
    qa = {"error": str(e)}

os.makedirs(OUT_DIR, exist_ok=True)
bpy.ops.object.select_all(action="DESELECT")
gate.select_set(True)
bpy.ops.export_scene.fbx(filepath=FBX, use_selection=True, axis_forward="-Z", axis_up="Y",
                         apply_scale_options="FBX_SCALE_ALL", bake_space_transform=True,
                         mesh_smooth_type="FACE", add_leaf_bones=False)
tris = sum(len(p.vertices) - 2 for p in gate.data.polygons)
info = {
    "id": "QX_VillageGate", "version": "v13", "author": "核心組", "source": os.path.relpath(SRC, ROOT),
    "unity_fbx": os.path.relpath(FBX, ROOT), "units": "metre", "origin": "base centre", "ground_z": 0,
    "front": "-Y (Blender) / +Z (Unity)", "dimensions_m": dims, "triangles": tris,
    "materials": [m.name for m in gate.data.materials if m], "objects_in_source": len(meshes),
    "collision": {"type": "boxes", "note": "the two pillars only; the opening stays walkable"},
    "qa": qa,
}
with open(INFO, "w", encoding="utf-8") as f:
    json.dump(info, f, ensure_ascii=False, indent=2, default=str)
print("VILLAGE_GATE_V13", json.dumps({k: info[k] for k in ("dimensions_m", "triangles", "materials", "objects_in_source")}, ensure_ascii=False))
