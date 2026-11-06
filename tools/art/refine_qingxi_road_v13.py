"""Refine the existing v12 Qingxi road against its saved AI three-view.

Run from the repository root with Blender 5.2 in background on the v12 blend.
This makes a separate v13 source and export; it never overwrites v12.
"""
import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
reference = ROOT / "art/references/qingxi-winding-road-v1/three-view.png"
if not reference.is_file():
    raise FileNotFoundError("Saved AI three-view required before road refinement: " + str(reference))
road = bpy.data.collections["ASSET_QingxiWindingRoad_v2"]
road.name = "ASSET_QingxiWindingRoad_v3"

stone_texture = ROOT / "art/textures/qingxi-riverbank-v2/stone-albedo.png"
if not stone_texture.is_file():
    raise FileNotFoundError("Existing riverbank stone texture is missing: " + str(stone_texture))
stone_image = bpy.data.images.load(str(stone_texture), check_existing=True)
stone_image.pack()
for suffix in ("Stone", "StoneDark", "StoneWarm"):
    material = bpy.data.materials["M_QX12_" + suffix]
    bsdf = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    tex = material.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = stone_image
    material.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])


def curve(y):
    # Zero at both modular ends, so another 12 m module can join cleanly.
    t = (y + 6.0) / 12.0
    return 0.58 * math.sin(math.pi * t) * math.sin(2 * math.pi * t)


for obj in road.objects:
    if obj.type != "MESH":
        continue
    ys = [v.co.y for v in obj.data.vertices]
    if max(ys) - min(ys) > 6:
        # Tread, meadow and batched foliage store their footprint in mesh data.
        for v in obj.data.vertices:
            v.co.x += curve(obj.location.y + v.co.y)
        obj.data.update()
    else:
        obj.location.x += curve(obj.location.y)

# Reuse the already modeled stones and leaf mounds. More irregular clusters
# improve the edge without introducing unreferenced new object designs.
rng = random.Random(20261028)
stones = [o for o in road.objects if o.name.startswith("SM_QX12_ShoreStone_")]
mounds = [o for o in road.objects if o.name.startswith("SM_QX12_LowLeafMound_")]
for i in range(20):
    original = stones[i % len(stones)]
    obj = original.copy()
    obj.data = original.data.copy()
    road.objects.link(obj)
    obj.name = f"SM_QX13_VergePebble_{i:02}"
    y = -5.55 + i * 0.55 + rng.uniform(-0.12, 0.12)
    x = (1 if i % 2 else -1) * rng.uniform(1.48, 2.75) + curve(y)
    obj.location = (x, y, original.location.z)
    obj.scale = tuple(s * rng.uniform(0.35, 0.55) for s in original.scale)
    obj.rotation_euler.z = rng.uniform(-math.pi, math.pi)
for i in range(12):
    original = mounds[i % len(mounds)]
    obj = original.copy()
    obj.data = original.data.copy()
    road.objects.link(obj)
    obj.name = f"SM_QX13_VergeLeaf_{i:02}"
    y = -5.2 + i * 0.9 + rng.uniform(-0.18, 0.18)
    obj.location = ((1 if i % 2 else -1) * rng.uniform(1.55, 3.0) + curve(y), y, original.location.z)
    obj.rotation_euler.z = rng.uniform(-math.pi, math.pi)
    obj.scale = tuple(s * rng.uniform(0.62, 0.92) for s in original.scale)

for obj in road.objects:
    if not obj.name.startswith("SM_QX13_Verge"):
        continue
    x, y = obj.location.x - curve(obj.location.y), obj.location.y
    ground = .05 + .045 * (1 - math.cos(math.pi * y / 6)) + .018 * math.sin(1.8 * x) * math.sin(math.pi * y / 6)
    local_min_z = min(v.co.z * obj.scale.z for v in obj.data.vertices)
    obj.location.z = ground - local_min_z - .012
    obj.data.transform(Matrix.Diagonal((obj.scale.x, obj.scale.y, obj.scale.z, 1)))
    obj.scale = (1, 1, 1)

source = ROOT / "art/source/qingxi-road-props-v13.blend"
export = ROOT / "art/exports/qingxi-road-props-v13/qingxi-road-v13.glb"
preview = ROOT / "art/previews/qingxi-road-props-v13"
export.parent.mkdir(parents=True, exist_ok=True)
preview.mkdir(parents=True, exist_ok=True)

bpy.ops.object.select_all(action="DESELECT")
meshes = [o for o in road.objects if o.type == "MESH"]
for obj in meshes:
    obj.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.export_scene.gltf(filepath=str(export), export_format="GLB", use_selection=True, export_apply=True)

for collection in bpy.data.collections:
    if collection != road:
        for obj in collection.objects:
            if obj.type == "MESH":
                obj.hide_render = True
camera = bpy.context.scene.camera
camera.location = (10, -13, 10)
camera.rotation_euler = (Vector((0, 0, .1)) - camera.location).to_track_quat("-Z", "Y").to_euler()
camera.data.type = "ORTHO"
camera.data.ortho_scale = 14
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1400
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.filepath = str(preview / "road-oblique.png")
bpy.ops.render.render(write_still=True)
camera.location = (0, 0, 18)
camera.rotation_euler = (Vector((0, 0, 0)) - camera.location).to_track_quat("-Z", "Y").to_euler()
camera.data.ortho_scale = 18
scene.render.filepath = str(preview / "road-top.png")
bpy.ops.render.render(write_still=True)

for collection in bpy.data.collections:
    for obj in collection.objects:
        obj.hide_render = False
bpy.ops.wm.save_as_mainfile(filepath=str(source))
report = {
    "reference": str(reference.relative_to(ROOT)),
    "source": str(source.relative_to(ROOT)),
    "export": str(export.relative_to(ROOT)),
    "objects": len(meshes),
    "triangles": sum(len(face.vertices) - 2 for obj in meshes for face in obj.data.polygons),
    "added_reused_pebbles": 20,
    "added_reused_leaf_mounds": 12,
    "curve_offset_max_m": 0.58,
}
(export.parent / "build-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print("@@QINGXI_ROAD_V13@@" + json.dumps(report, ensure_ascii=False))
