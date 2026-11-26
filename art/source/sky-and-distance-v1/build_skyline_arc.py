"""Build and verify the reusable 90-degree skyline carrier. Blender 5.2.2.

Run: blender -b --factory-startup --python build_skyline_arc.py
The object origin is world centre, not its geometric centroid. At zero rotation
the centre of the card faces +Y toward a viewer at the world origin.
"""
import bpy
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = "sky-and-distance-v1"
SOURCE = ROOT / "art/source" / BASE / "SK"
EXPORT = ROOT / "art/exports" / BASE / "SK"
PREVIEW = ROOT / "art/previews" / BASE / "SK"
for folder in (SOURCE, EXPORT, PREVIEW):
    folder.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
radius = 800.0
height = 240.0
segments = 64
vertices = []
uv = []
for i in range(segments + 1):
    t = -math.pi / 4 + (math.pi / 2) * i / segments
    x, y = radius * math.sin(t), -radius * math.cos(t)
    vertices.extend(((x, y, 0.0), (x, y, height)))
    uv.extend(((i / segments, 0.0), (i / segments, 1.0)))
faces = [(2*i, 2*i+1, 2*i+3, 2*i+2) for i in range(segments)]
mesh = bpy.data.meshes.new("SM_Skyline_Arc_mesh")
mesh.from_pydata(vertices, [], faces)
mesh.update(calc_edges=True)
obj = bpy.data.objects.new("SM_Skyline_Arc", mesh)
bpy.context.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
uv_layer = mesh.uv_layers.new(name="UVMap")
for polygon in mesh.polygons:
    i = polygon.index
    for li in polygon.loop_indices:
        vi = mesh.loops[li].vertex_index
        uv_layer.data[li].uv = uv[vi]

mat = bpy.data.materials.new("Skyline_Carrier_Neutral")
mat.diffuse_color = (0.52, 0.62, 0.68, 1.0)
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = mat.diffuse_color
bsdf.inputs["Roughness"].default_value = 1.0
mesh.materials.append(mat)

assert len(vertices) == 130 and len(faces) == 64
assert obj.location.length == 0
assert all(abs(math.hypot(v[0], v[1])-radius) < 1e-5 for v in vertices)
assert min(v[2] for v in vertices) == 0 and max(v[2] for v in vertices) == height
assert all(p.normal.y > 0 for p in mesh.polygons), "Normals must face the origin"
assert len(uv_layer.data) == 256

# Simple calibrated gray-model preview. The painted skyline is reviewed separately.
world = bpy.data.worlds.new("Neutral World")
bpy.context.scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.72, 0.76, 0.79, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
sun_data = bpy.data.lights.new("Neutral Area", "AREA")
sun = bpy.data.objects.new("Neutral Area", sun_data)
bpy.context.collection.objects.link(sun)
sun.location = (-450, 150, 650)
sun_data.energy = 300000
sun_data.shape = "DISK"
sun_data.size = 900

camera_data = bpy.data.cameras.new("Arc Gray Camera")
camera = bpy.data.objects.new("Arc Gray Camera", camera_data)
bpy.context.collection.objects.link(camera)
camera.location = (0, 0, 340)
from mathutils import Vector
camera.rotation_euler = (Vector((0, -730, 115))-camera.location).to_track_quat("-Z", "Y").to_euler()
camera_data.type = "ORTHO"
camera_data.ortho_scale = 1320
bpy.context.scene.camera = camera
bpy.context.scene.render.engine = "BLENDER_EEVEE"
bpy.context.scene.render.resolution_x = 1600
bpy.context.scene.render.resolution_y = 650
bpy.context.scene.render.resolution_percentage = 100
bpy.context.scene.render.filepath = str(PREVIEW / "SM_Skyline_Arc_gray.png")
bpy.context.scene.view_settings.view_transform = "AgX"
bpy.ops.render.render(write_still=True)

# Source and exports include only the carrier, not preview camera/lights.
for other in list(bpy.data.objects):
    if other != obj:
        bpy.data.objects.remove(other, do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE / "SM_Skyline_Arc.blend"))
bpy.ops.export_scene.fbx(filepath=str(EXPORT / "SM_Skyline_Arc.fbx"),
                         use_selection=True, apply_unit_scale=True, use_mesh_modifiers=True,
                         bake_space_transform=False, add_leaf_bones=False, path_mode="AUTO")
bpy.ops.export_scene.gltf(filepath=str(EXPORT / "SM_Skyline_Arc.glb"),
                          export_format="GLB", use_selection=True)

def check_import(kind, path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if kind == "fbx":
        bpy.ops.import_scene.fbx(filepath=str(path))
    else:
        bpy.ops.import_scene.gltf(filepath=str(path))
    objects = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    assert len(objects) == 1, (kind, len(objects))
    imported = objects[0]
    positions = [imported.matrix_world @ v.co for v in imported.data.vertices]
    radii = [math.hypot(v.x, v.y) for v in positions]
    zs = [v.z for v in positions]
    result = {
        "meshes": len(objects),
        "vertices": len(imported.data.vertices),
        "triangles": sum(len(p.vertices)-2 for p in imported.data.polygons),
        "radius_error_max_m": max(abs(r-radius) for r in radii),
        "bottom_error_m": abs(min(zs)),
        "height_error_m": abs(max(zs)-height),
        "object_origin_error_m": imported.matrix_world.translation.length,
        "uv_layers": len(imported.data.uv_layers),
    }
    assert result["radius_error_max_m"] <= 0.02
    assert result["bottom_error_m"] <= 0.02
    assert result["height_error_m"] <= 0.02
    assert result["object_origin_error_m"] <= 0.02
    return result

report = {
    "asset": "SM_Skyline_Arc",
    "origin": "world centre",
    "radius_m": radius,
    "height_m": height,
    "arc_degrees": 90,
    "arc_length_m": radius*math.pi/2,
    "segments": segments,
    "source_vertices": 130,
    "source_quads": 64,
    "source_triangles": 128,
    "qa_errors": 0,
    "qa_warnings": 0,
    "fbx": check_import("fbx", EXPORT / "SM_Skyline_Arc.fbx"),
    "glb": check_import("glb", EXPORT / "SM_Skyline_Arc.glb"),
}
(EXPORT / "SM_Skyline_Arc_import_report.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(report, ensure_ascii=False))
