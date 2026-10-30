"""Build the Qingxi alchemy work table v1 from art/references/qingxi-alchemy-table-v1.

Replaces the graybox table in the novice village alchemy corner. Size follows joshsu54's
graybox (2.0 x 0.72 m, tabletop 0.78 m) so his tabletop props keep their heights.
Blender 5.2, metres, Z up, origin at the base centre, front = -Y.

  blender -b --factory-startup --python-exit-code 1 -P tools/art/build_qingxi_alchemy_table_v1.py
Writes the .blend, GLB, Unity FBX, model_info.json, previews and a QA report.
"""
import json
import math
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
NAME = "QX_AlchemyWorkTable_v001"
SOURCE = ROOT / "art/source/qingxi-alchemy-table-v1"
EXPORTS = ROOT / "art/exports/qingxi-alchemy-table-v1"
PREVIEWS = ROOT / "art/previews/qingxi-alchemy-table-v1"
UNITY = ROOT / "apps/game/Assets/YunJing/Models/AlchemyTableV1"
QA_SCRIPTS = Path.home() / ".claude/skills/blender-asset-qa/scripts"

LENGTH, DEPTH, TOP_Z, TOP_T = 2.0, 0.72, 0.78, 0.06
LEG, LEG_X, LEG_Y = 0.08, 0.90, 0.28


def material(name, color, roughness, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def box(name, size, centre, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=centre)
    ob = bpy.context.object
    ob.name = name
    ob.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        mod = ob.modifiers.new("Bevel", "BEVEL")
        mod.width, mod.segments, mod.limit_method = bevel, 2, "ANGLE"
        bpy.ops.object.modifier_apply(modifier=mod.name)
    ob.data.materials.append(mat)
    return ob


def slat(name, x, mat):
    # Bamboo slat across the depth; its ends sit in the long stretchers.
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.018, depth=2 * LEG_Y + 0.02,
                                        location=(x, 0, 0.17 + 0.012), rotation=(math.pi / 2, 0, 0))
    ob = bpy.context.object
    ob.name = name
    bpy.ops.object.transform_apply(rotation=True)
    ob.data.materials.append(mat)
    return ob


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "METRIC"
    wood = material("M_QX_AgedElm", (0.33, 0.20, 0.11), 0.82)
    bamboo = material("M_QX_Bamboo", (0.55, 0.46, 0.26), 0.7)
    bronze = material("M_QX_OxidisedBronze", (0.24, 0.34, 0.28), 0.5, 0.6)

    parts = [box("Top", (LENGTH, DEPTH, TOP_T), (0, 0, TOP_Z - TOP_T / 2), wood, bevel=0.012)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            # Legs run 2 cm into the top so no faces sit back to back.
            parts.append(box(f"Leg_{sx}_{sy}", (LEG, LEG, TOP_Z - TOP_T + 0.02),
                             (sx * LEG_X, sy * LEG_Y, (TOP_Z - TOP_T + 0.02) / 2), wood, bevel=0.006))
            # Bronze corner caps stand 5 mm proud of the top's faces (no z-fighting).
            parts.append(box(f"Cap_{sx}_{sy}", (0.075, 0.075, 0.072),
                             (sx * (LENGTH / 2 - 0.0325), sy * (DEPTH / 2 - 0.0325), TOP_Z - 0.031), bronze, bevel=0.004))
    for sy in (-1, 1):
        parts.append(box(f"Apron_{sy}", (2 * LEG_X, 0.03, 0.065), (0, sy * 0.30, 0.6925), wood))
        parts.append(box(f"Stretcher_{sy}", (2 * LEG_X, 0.04, 0.04), (0, sy * LEG_Y, 0.15), wood))
    for sx in (-1, 1):
        parts.append(box(f"EndApron_{sx}", (0.03, 2 * LEG_Y, 0.065), (sx * 0.905, 0, 0.6925), wood))
        parts.append(box(f"EndStretcher_{sx}", (0.04, 2 * LEG_Y, 0.04), (sx * LEG_X, 0, 0.15), wood))
    for i in range(9):
        parts.append(slat(f"Slat_{i}", -0.8 + i * 0.2, bamboo))

    bpy.ops.object.select_all(action="DESELECT")
    for ob in parts:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    lod0 = bpy.context.object
    lod0.name = lod0.data.name = NAME + "_LOD0"
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.shade_flat()

    lod1 = lod0.copy()
    lod1.data = lod0.data.copy()
    lod1.name = lod1.data.name = NAME + "_LOD1"
    bpy.context.collection.objects.link(lod1)
    dec = lod1.modifiers.new("Decimate", "DECIMATE")
    dec.ratio = 0.5
    bpy.context.view_layer.objects.active = lod1
    bpy.ops.object.modifier_apply(modifier=dec.name)

    root = bpy.data.objects.new(NAME, None)
    bpy.context.collection.objects.link(root)
    for ob in (lod0, lod1):
        ob.parent = root
    return root, lod0, lod1


def tris(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def qa(objects):
    sys.path.insert(0, str(QA_SCRIPTS))
    import qa_check
    return qa_check.run(objects=objects, profile="game", tol=0.004)


def previews(lod0):
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.light = "STUDIO"
    scene.render.resolution_x, scene.render.resolution_y = 1280, 720
    # 1.75 m scale figure, only in the preview file.
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=1.75, location=(1.6, 0.3, 0.875))
    figure = bpy.context.object
    figure.name = "ScaleFigure_1p75m"
    cam_data = bpy.data.cameras.new("PreviewCam")
    cam = bpy.data.objects.new("PreviewCam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    target = (0, 0, 0.45)
    shots = {"front": (0, -4.2, 0.6), "side": (4.2, 0, 0.6), "back": (0, 4.2, 0.6), "three-quarter": (-2.9, -3.1, 1.9)}
    for name, location in shots.items():
        cam.location = location
        direction = [t - l for t, l in zip(target, location)]
        cam.rotation_euler = (math.atan2(math.hypot(direction[0], direction[1]), -direction[2]), 0,
                              math.atan2(direction[1], direction[0]) - math.pi / 2)
        figure.hide_render = name != "three-quarter"
        scene.render.filepath = str(PREVIEWS / f"{NAME}_{name}.png")
        bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(figure)
    bpy.data.objects.remove(cam)


def export(root, lod0, lod1):
    for folder in (SOURCE, EXPORTS, UNITY):
        folder.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE / "qingxi-alchemy-table-v1.blend"))
    bpy.ops.object.select_all(action="DESELECT")
    for ob in (root, lod0):
        ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(EXPORTS / f"{NAME}.glb"), use_selection=True, export_format="GLB")
    for ob in (root, lod0, lod1):
        ob.select_set(True)
    bpy.ops.export_scene.fbx(
        filepath=str(UNITY / f"{NAME}.fbx"), use_selection=True, object_types={"MESH", "EMPTY"},
        axis_forward="-Z", axis_up="Y", apply_scale_options="FBX_SCALE_ALL",
        bake_space_transform=True, use_mesh_modifiers=True, mesh_smooth_type="FACE",
        add_leaf_bones=False, bake_anim=False, path_mode="RELATIVE", embed_textures=False)


def main():
    root, lod0, lod1 = build()
    report = qa([lod0.name])
    dims = [round(v, 4) for v in lod0.dimensions]
    ground = round(min((lod0.matrix_world @ v.co).z for v in lod0.data.vertices), 4)
    info = {
        "id": "QX_AlchemyWorkTable", "version": "v001", "author": "z1nnz (core group, built by Claude Code)",
        "reference": "art/references/qingxi-alchemy-table-v1/",
        "units": "metre", "origin": "base centre", "forward": "-Y (Blender) / +Z (glTF)",
        "dimensions_m": dims, "ground_z": ground, "tabletop_height_m": TOP_Z,
        "triangles": tris(lod0), "lod_triangles": [tris(lod0), tris(lod1)],
        "materials": [m.name for m in lod0.data.materials],
        "collision": {"type": "box", "size": [LENGTH, DEPTH, TOP_Z], "center": [0, 0, TOP_Z / 2],
                      "note": "one box is enough; the lower shelf is not walkable"},
        "sockets": {"tabletop": [0, 0, TOP_Z]},
        "qa": {"pass": report["pass"], "errors": len(report["errors"]), "warnings": len(report["warnings"])},
    }
    previews(lod0)
    export(root, lod0, lod1)
    (EXPORTS / f"{NAME}_model_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXPORTS / "source-qa-report.json").write_text(json.dumps(
        {"errors": report["errors"][:30], "warnings": report["warnings"][:30]}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("@@TABLE@@" + json.dumps(info, ensure_ascii=False))
    print("@@TABLE_QA@@" + json.dumps({"errors": report["errors"][:12], "warnings": report["warnings"][:12]}, ensure_ascii=False))


main()
