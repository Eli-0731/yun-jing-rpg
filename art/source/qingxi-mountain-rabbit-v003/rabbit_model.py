"""Derive the Qingxi rabbit from the read-only Dondon v002 Blender source.

Run from the repository root:
  blender -b --factory-startup --python-exit-code 1 -P art/source/qingxi-mountain-rabbit-v003/rabbit_model.py

The source silhouette is retained. This is an animation/asset pass, not a new sculpt.
"""
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "art/incoming/dondon/QMountainRabbit/v002/QMountainRabbit_v002.blend"
BASE = ROOT / "art/source/qingxi-mountain-rabbit-v003"
EXPORT = ROOT / "art/exports/qingxi-mountain-rabbit-v003"
PREVIEW = ROOT / "art/previews/qingxi-mountain-rabbit-v003"
for folder in (BASE, EXPORT, PREVIEW):
    folder.mkdir(parents=True, exist_ok=True)

# Background build loads a source copy; no changes are written to the incoming file.
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1
scene.render.fps = 24

source_objects = [ob for ob in scene.objects if ob.type == "MESH"]
assert len(source_objects) == 19
original_bounds = [list(ob.matrix_world @ Vector(corner)) for ob in source_objects for corner in ob.bound_box]
original_min = [min(p[i] for p in original_bounds) for i in range(3)]
original_max = [max(p[i] for p in original_bounds) for i in range(3)]

source_collection = bpy.data.collections.new("Dondon_v002_Reference_ReadOnly")
scene.collection.children.link(source_collection)
for ob in list(scene.objects):
    for collection in list(ob.users_collection):
        collection.objects.unlink(ob)
    source_collection.objects.link(ob)
source_collection.hide_render = True
source_collection.hide_viewport = True

asset = bpy.data.collections.new("Rabbit_SemiRealistic_v01")
scene.collection.children.link(asset)
lod_collections = {}
for level in range(3):
    child = bpy.data.collections.new(f"LOD{level}")
    asset.children.link(child)
    lod_collections[level] = child
rig_collection = bpy.data.collections.new("Rig")
asset.children.link(rig_collection)
proxy_collection = bpy.data.collections.new("Collision_Proxy_NotExported")
asset.children.link(proxy_collection)

coat_colors = {
    "furLight": (0.61, 0.63, 0.59, 1),
    "fur": (0.50, 0.52, 0.50, 1),
    "white": (0.81, 0.81, 0.77, 1),
    "pink": (0.72, 0.43, 0.47, 1),
    "black": (0.075, 0.052, 0.04, 1),
}

# A single image-backed material exports to GLB and gives Unity a simple URP map.
names = list(coat_colors)
textures = BASE / "textures"
textures.mkdir(exist_ok=True)
def save_texture(name, color_at):
    image = bpy.data.images.new(name, width=256, height=256, alpha=True)
    pixels = []
    for y in range(256):
        color = color_at(y)
        pixels.extend(color * 256)
    image.pixels.foreach_set(pixels)
    image.filepath_raw = str(textures / name)
    image.file_format = "PNG"
    image.save()
    return image

base_map = save_texture("T_Rabbit_BaseColor.png", lambda y: coat_colors[names[min(4, y // 51)]])
save_texture("T_Rabbit_Roughness.png", lambda y: (.8, .8, .8, 1))
save_texture("T_Rabbit_Normal.png", lambda y: (.5, .5, 1, 1))

material = bpy.data.materials.new("M_QingxiRabbit_Atlas")
material.use_nodes = True
nodes = material.node_tree.nodes
bsdf = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
image_node = nodes.new("ShaderNodeTexImage")
image_node.image = base_map
material.node_tree.links.new(image_node.outputs["Color"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.8
bsdf.inputs["Metallic"].default_value = 0

arm_data = bpy.data.armatures.new("Rabbit_GameSkeleton")
arm = bpy.data.objects.new("RIG_QingxiRabbit", arm_data)
rig_collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
arm.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")

def bone(name, head, tail, parent=None, deform=True):
    b = arm_data.edit_bones.new(name)
    b.head, b.tail = head, tail
    if parent:
        b.parent = arm_data.edit_bones[parent]
    b.use_deform = deform
    return b

bone("Root", (0, 0, 0), (0, 0, .09), deform=False)
bone("Pelvis", (0, .12, .17), (0, .05, .23), "Root")
bone("Spine", (0, .05, .23), (0, -.10, .25), "Pelvis")
bone("Chest", (0, -.10, .25), (0, -.17, .29), "Spine")
bone("Neck", (0, -.17, .29), (0, -.22, .35), "Chest")
bone("Head", (0, -.22, .35), (0, -.28, .40), "Neck")
bone("Tail", (0, .22, .20), (0, .31, .20), "Pelvis")
for side, x in (("L", -.1), ("R", .1)):
    bone("Ear_" + side, (x*.75, -.15, .45), (x*.75, -.15, .69), "Head")
    bone("FrontUpper_" + side, (x*.8, -.16, .21), (x*.8, -.17, .10), "Chest")
    bone("FrontPaw_" + side, (x*.8, -.17, .10), (x*.8, -.18, .04), "FrontUpper_" + side)
    bone("HindUpper_" + side, (x*1.3, .11, .21), (x*1.3, .08, .11), "Pelvis")
    bone("HindPaw_" + side, (x*1.3, .08, .11), (x*1.3, -.02, .04), "HindUpper_" + side)
bpy.ops.object.mode_set(mode="OBJECT")
arm.select_set(False)

def owner(name):
    if "ear" in name:
        return "Ear_L" if "_-1" in name else "Ear_R"
    if "front_paw" in name:
        return "FrontPaw_L" if "_-1" in name else "FrontPaw_R"
    if "back_paw" in name:
        return "HindPaw_L" if "_-1" in name else "HindPaw_R"
    if "haunch" in name:
        return "HindUpper_L" if "_-1" in name else "HindUpper_R"
    if "tail" in name:
        return "Tail"
    if any(word in name for word in ("head", "eye", "glint", "muzzle", "nose")):
        return "Head"
    return "Spine"

lods = {}
for level in range(3):
    copies = []
    for original in source_objects:
        ob = original.copy()
        ob.data = original.data.copy()
        lod_collections[level].objects.link(ob)
        ob.name = f"{original.name}_LOD{level}"
        ob.parent = None
        ob.matrix_world = original.matrix_world.copy()
        # v002 uses spheres with transforms. Bake those transforms so skinning/export has unit scale.
        ob.data.transform(ob.matrix_world)
        ob.matrix_world.identity()
        ob.data.materials.clear()
        ob.data.materials.append(material)
        old_mat = original.data.materials[0].name if original.data.materials else "furLight"
        band = names.index(old_mat)
        uv = ob.data.uv_layers.get("UVMap") or ob.data.uv_layers.new(name="UVMap")
        for item in uv.data:
            item.uv = ((item.uv.x % 1) * .98 + .01, (band + .1 + (item.uv.y % 1) * .8) / 5)
        primary = owner(original.name)
        group = ob.vertex_groups.new(name=primary)
        group.add(list(range(len(ob.data.vertices))), 1, "REPLACE")
        if original.name == "Rabbit_body":
            chest = ob.vertex_groups.new(name="Chest")
            pelvis = ob.vertex_groups.new(name="Pelvis")
            for vertex in ob.data.vertices:
                y = vertex.co.y
                if y < -.09:
                    amount = min(.75, (-.09-y)/.18)
                    group.add([vertex.index], 1-amount, "REPLACE")
                    chest.add([vertex.index], amount, "REPLACE")
                elif y > .08:
                    amount = min(.75, (y-.08)/.17)
                    group.add([vertex.index], 1-amount, "REPLACE")
                    pelvis.add([vertex.index], amount, "REPLACE")
        elif original.name == "Rabbit_head":
            neck = ob.vertex_groups.new(name="Neck")
            for vertex in ob.data.vertices:
                amount = min(.6, max(0, (vertex.co.y+.17)/.15))
                if amount:
                    group.add([vertex.index], 1-amount, "REPLACE")
                    neck.add([vertex.index], amount, "REPLACE")
        elif "haunch" in original.name:
            pelvis = ob.vertex_groups.new(name="Pelvis")
            for vertex in ob.data.vertices:
                amount = min(.6, max(0, (vertex.co.z-.16)/.15))
                if amount:
                    group.add([vertex.index], 1-amount, "REPLACE")
                    pelvis.add([vertex.index], amount, "REPLACE")
        if level:
            mod = ob.modifiers.new(f"LOD{level}_Decimate", "DECIMATE")
            mod.ratio = 0.49 if level == 1 else 0.20
            bpy.context.view_layer.objects.active = ob
            ob.select_set(True)
            bpy.ops.object.modifier_apply(modifier=mod.name)
            ob.select_set(False)
        deform = ob.modifiers.new("Skin", "ARMATURE")
        deform.object = arm
        deform.use_deform_preserve_volume = True
        copies.append(ob)
    # Join each LOD into one skinned mesh. UV atlas and vertex groups survive join.
    bpy.ops.object.select_all(action="DESELECT")
    for ob in copies:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = copies[0]
    bpy.ops.object.join()
    merged = copies[0]
    merged.name = f"SK_QingxiRabbit_LOD{level}"
    merged.data.name = merged.name
    merged["lod"] = level
    merged["source"] = "Dondon QMountainRabbit v002; source geometry only"
    merged.hide_render = level != 0
    merged.hide_viewport = level != 0
    lods[level] = merged

# Reference-only physics proxies: Unity should create capsule/sphere colliders,
# never a MeshCollider from the skinned surface.
def proxy(name, location, scale):
    mesh = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, mesh)
    proxy_collection.objects.link(ob)
    from mathutils import Vector as V
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1)
    bm.to_mesh(mesh)
    bm.free()
    ob.location = location
    ob.scale = scale
    ob.hide_render = True
    ob.hide_viewport = True
    return ob
proxy("COL_Body_Capsule_Reference", (0, 0, .31), (.22, .22, .31))
proxy("COL_Head_Sphere_Reference", (0, -.22, .39), (.15, .15, .15))

scene.frame_start = 1
scene.frame_end = 48
arm.animation_data_create()
pose_bones = arm.pose.bones
for pose_bone in pose_bones:
    pose_bone.rotation_mode = "QUATERNION"

clips = {
    "Rabbit_Idle": (48, True),
    "Rabbit_Hop": (24, True),
    "Rabbit_Flee": (16, True),
    "Rabbit_Hit": (8, False),
    "Rabbit_Death": (24, False),
}

def set_pose(angles, height=0):
    for pb in pose_bones:
        pb.rotation_quaternion.identity()
        if pb.name in angles:
            pb.rotation_quaternion = __import__("mathutils").Euler(angles[pb.name], "XYZ").to_quaternion()
    pose_bones["Root"].location = (0, height, 0)

def key(frame, angles, height=0):
    scene.frame_set(frame)
    set_pose(angles, height)
    for pb in pose_bones:
        pb.keyframe_insert(data_path="rotation_quaternion", frame=frame, group=pb.name)
    pose_bones["Root"].keyframe_insert(data_path="location", frame=frame, group="Root")

def all_sides(front=0, hind=0, ear=0):
    pose = {}
    for suffix in ("L", "R"):
        pose["FrontUpper_" + suffix] = (front, 0, 0)
        pose["HindUpper_" + suffix] = (hind, 0, 0)
        pose["Ear_" + suffix] = (ear, 0, 0)
    return pose

for name, (end, loop) in clips.items():
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    arm.animation_data.action = action
    if name == "Rabbit_Idle":
        key(1, all_sides(ear=-.02))
        key(24, {**all_sides(ear=.09), "Spine": (.025, 0, 0), "Head": (.035, 0, 0)}, .012)
        key(end, all_sides(ear=-.02))
    elif name in ("Rabbit_Hop", "Rabbit_Flee"):
        key(1, all_sides(front=.28, hind=-.4))
        key(round(end*.25), all_sides(front=-.40, hind=.34, ear=-.12), .15 if name == "Rabbit_Hop" else .13)
        key(round(end*.55), all_sides(front=.35, hind=.42, ear=.12), .19 if name == "Rabbit_Hop" else .15)
        key(round(end*.78), all_sides(front=-.25, hind=-.18), .025)
        key(end, all_sides(front=.28, hind=-.4))
    elif name == "Rabbit_Hit":
        key(1, all_sides())
        key(4, {**all_sides(front=.3, hind=-.12, ear=.2), "Spine": (-.20, 0, 0), "Head": (-.25, 0, 0)}, 0)
        key(end, all_sides())
    else:
        key(1, all_sides())
        key(8, {**all_sides(front=.7, hind=-.3), "Spine": (.35, 0, .25), "Head": (.18, 0, 0)}, .06)
        key(16, {**all_sides(front=1.2, hind=-.65, ear=.38), "Spine": (.7, 0, .75), "Head": (.35, 0, 0)}, .02)
        key(end, {**all_sides(front=1.2, hind=-.65, ear=.38), "Spine": (.7, 0, .75), "Head": (.35, 0, 0)}, .02)
    action["loop"] = loop
    action["root_motion"] = "in_place"
    action["frames"] = end
    # NLA keeps each clip available to both FBX and glTF exporters.
    track = arm.animation_data.nla_tracks.new()
    track.name = name
    strip = track.strips.new(name, 1, action)
    strip.mute = True
    track.mute = True

arm.animation_data.action = bpy.data.actions["Rabbit_Idle"]
scene.frame_set(1)
for level, ob in lods.items():
    ob.hide_viewport = level != 0
    ob.hide_render = level != 0

output_blend = BASE / "QingxiMountainRabbit_v003.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(output_blend))
print("RABBIT_BUILD_PASS", output_blend)
