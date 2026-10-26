"""Original Qingxi Listening-Wind Terrace from its saved AI three-view.

No geometry, textures or Blender data from the downloaded reference archives is used.
"""

import math
import pathlib
import random

import bpy
from mathutils import Vector

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE = ROOT / "art/source/qingxi-listening-terrace-v1.blend"
EXPORT = ROOT / "art/exports/qingxi-listening-terrace-v1.glb"
PREVIEW = ROOT / "art/previews/qingxi-listening-terrace-v1"
for path in (SOURCE.parent, EXPORT.parent, PREVIEW):
    path.mkdir(parents=True, exist_ok=True)

# A fresh background Blender process is required by the build command.
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1
asset = bpy.data.collections.new("ASSET_QingxiListeningTerrace")
scene.collection.children.link(asset)
presentation = bpy.data.collections.new("PREVIEW_Only")
scene.collection.children.link(presentation)


def material(name, color, roughness=.8, metallic=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    node = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    node.inputs["Base Color"].default_value = (*color, 1)
    node.inputs["Roughness"].default_value = roughness
    node.inputs["Metallic"].default_value = metallic
    return m


stone = material("M_WarmGreyLimestone", (.47, .52, .50))
stone_light = material("M_PaleIvoryStone", (.72, .74, .68))
stone_dark = material("M_WeatheredStoneJoint", (.31, .32, .28))
stone_accent = material("M_WeatheredLimestone", (.59, .62, .57))
bronze = material("M_MutedPatinatedBronze", (.19, .31, .28), .43, .7)
bamboo = material("M_GoldenBamboo", (.64, .39, .14), .58)
rope = material("M_WovenHemp", (.40, .26, .12), .85)
moss = material("M_DeepMoss", (.08, .24, .13))
grass = material("M_SpringGrass", (.18, .42, .16))
flower = material("M_AzureFlower", (.08, .34, .74), .65)


def stone_grain(mat, dark, light, scale):
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    coords = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 4
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = .23
    ramp.color_ramp.elements[0].color = (*dark, 1)
    ramp.color_ramp.elements[1].position = .78
    ramp.color_ramp.elements[1].color = (*light, 1)
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = .14
    bump.inputs["Distance"].default_value = .025
    links.new(coords.outputs["Generated"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])


stone_grain(stone, (.32, .37, .35), (.63, .66, .59), 9)
stone_grain(stone_light, (.57, .61, .57), (.86, .85, .76), 11)
stone_grain(stone_accent, (.45, .48, .43), (.72, .73, .63), 12)


def mesh_object(name, verts, faces, mat, collection=asset):
    data = bpy.data.meshes.new(name + "_Mesh")
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    data.materials.append(mat)
    # Separate UV islands per face so future texture bakes do not overlap.
    uv = data.uv_layers.new(name="UV0")
    grid = math.ceil(math.sqrt(len(data.polygons)))
    for face_index, polygon in enumerate(data.polygons):
        tile_x, tile_y = face_index % grid, face_index // grid
        count = len(polygon.loop_indices)
        coords = ([(.08, .08), (.92, .08), (.92, .92), (.08, .92)] if count == 4 else
                  [(0.5 + .42 * math.cos(2 * math.pi * j / count),
                    0.5 + .42 * math.sin(2 * math.pi * j / count)) for j in range(count)])
        for loop_index, (u, v) in zip(polygon.loop_indices, coords):
            uv.data[loop_index].uv = ((tile_x + u) / grid, (tile_y + v) / grid)
    return obj


def box(name, center, size, mat):
    x, y, z = center
    sx, sy, sz = (v / 2 for v in size)
    verts = [(x + dx * sx, y + dy * sy, z + dz * sz)
             for dz in (-1, 1) for dy in (-1, 1) for dx in (-1, 1)]
    faces = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4),
             (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
    return mesh_object(name, verts, faces, mat)


def ellipse_dais(name, rx, ry, bottom, top, mat, steps=64):
    verts = [(0, 0, top)]
    for z in (top, bottom):
        verts.extend((rx * math.cos(2 * math.pi * i / steps),
                      ry * math.sin(2 * math.pi * i / steps), z) for i in range(steps))
    verts.append((0, 0, bottom))
    faces = []
    for i in range(steps):
        j = (i + 1) % steps
        faces += [(0, 1 + i, 1 + j), (1 + i, 1 + steps + i, 1 + steps + j, 1 + j),
                  (1 + 2 * steps, 1 + steps + j, 1 + steps + i)]
    return mesh_object(name, verts, faces, mat)


def tube(name, points, radius, mat, sides=8):
    verts = []
    for i, point in enumerate(points):
        p = Vector(point)
        tangent = Vector(points[min(i + 1, len(points) - 1)]) - Vector(points[max(i - 1, 0)])
        tangent.normalize()
        side = tangent.cross(Vector((0, 0, 1)))
        if side.length < .001:
            side = Vector((1, 0, 0))
        side.normalize()
        up = tangent.cross(side).normalized()
        for j in range(sides):
            angle = 2 * math.pi * j / sides
            verts.append(tuple(p + radius * (side * math.cos(angle) + up * math.sin(angle))))
    bottom_center = len(verts)
    verts.append(tuple(points[0]))
    top_center = len(verts)
    verts.append(tuple(points[-1]))
    faces = [(bottom_center, (j + 1) % sides, j) for j in range(sides)]
    for i in range(len(points) - 1):
        for j in range(sides):
            k = (j + 1) % sides
            faces.append((i * sides + j, i * sides + k, (i + 1) * sides + k, (i + 1) * sides + j))
    faces.extend((top_center, (len(points) - 1) * sides + j,
                  (len(points) - 1) * sides + (j + 1) % sides) for j in range(sides))
    return mesh_object(name, verts, faces, mat)


def bezier(t):
    p = (Vector((2.7, .82)), Vector((3.35, 3.55)), Vector((.3, 4.85)), Vector((-2.25, 3.83)))
    u = 1 - t
    return p[0] * u ** 3 + p[1] * 3 * u * u * t + p[2] * 3 * u * t * t + p[3] * t ** 3


def arch_block(name, start, end):
    a = bezier(start)
    b = bezier(end)
    tangent = (b - a).normalized()
    n = Vector((-tangent.y, tangent.x))
    thick = .38 - .12 * ((start + end) / 2)
    points = [a + n * thick / 2, b + n * thick / 2,
              b - n * thick / 2, a - n * thick / 2]
    verts = [(p.x, y, p.y) for y in (.35, 1.0) for p in points]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    obj = mesh_object(name, verts, faces, stone_light if int(name[-2:]) % 4 else stone_accent)
    bevel = obj.modifiers.new("SoftMasonryEdges", "BEVEL")
    bevel.width = .025
    bevel.segments = 2
    bevel.affect = "EDGES"
    return obj


# Primary terrace: stone, with a stepped edge rather than the reference's wood deck.
ellipse_dais("SM_TerraceFoundation", 4.25, 3.0, -.25, .58, stone)
ellipse_dais("SM_TerracePaving", 4.02, 2.78, .58, .72, stone_light)
for ring, radius in enumerate((1.60, 2.38, 3.30)):
    segments = 24 + ring * 12
    for i in range(segments):
        a = 2 * math.pi * i / segments
        b = 2 * math.pi * (i + .95) / segments
        tube(f"SM_PavingRing_{ring}_{i:02d}",
             [(radius * math.cos(a), radius * .69 * math.sin(a), .728),
              (radius * math.cos(b), radius * .69 * math.sin(b), .728)],
             .013, stone_dark, 5)
for i in range(18):
    angle = 2 * math.pi * i / 18
    tube(f"SM_RadialStoneJoint_{i:02d}",
         [(1.64 * math.cos(angle), 1.13 * math.sin(angle), .728),
          (2.38 * math.cos(angle), 1.64 * math.sin(angle), .728)],
         .010, stone_dark, 5)
for row in range(4):
    box(f"SM_EntryStep_{row + 1}", (0, -3.0 - row * .43, .58 - row * .145),
        (3.7 + row * .26, .48, .24), stone_light)
for index, theta in enumerate((.12, .29, .46, .63, .8, 2.18, 2.38, 2.58, 2.78, 2.98)):
    x, y = 4.00 * math.cos(theta), 2.72 * math.sin(theta)
    box(f"SM_LowParapet_{index:02d}", (x, y, .88), (.45, .30, .26), stone_accent if index % 3 == 0 else stone)
    box(f"SM_ParapetCap_{index:02d}", (x, y, 1.035), (.53, .38, .055), stone_light)

# Separate arch masonry segments and two inset bronze contour lines.
for i in range(20):
    arch_block(f"SM_MoonArchStone_{i:02d}", (i + .005) / 20, (i + .995) / 20)
for front_y, suffix in ((.325, "Front"), (1.025, "Back")):
    pts = []
    for i in range(45):
        t = .015 + i / 44 * .97
        p = bezier(t)
        pts.append((p.x, front_y, p.y))
    tube(f"SM_BronzeArchContour_{suffix}", pts, .015, bronze, 8)
box("SM_ArchFoot", (2.7, .675, .75), (.95, 1.05, .40), stone_dark)

# Curved bench, with two independent suspension lines and a bamboo slat family.
for i in range(13):
    x = -1.15 + i * (2.3 / 12)
    sag = .09 * (1 - (x / 1.16) ** 2)
    box(f"SM_BambooSeatSlat_{i:02d}", (x, .65, 1.46 - sag), (.12, .55, .08), bamboo)
for side_y, label in ((.42, "Front"), (.88, "Back")):
    tube(f"SM_BambooSeatSupport_{label}",
         [(-1.18 + i * .118, side_y,
           1.385 - .09 * (1 - ((-1.18 + i * .118) / 1.18) ** 2))
          for i in range(21)], .035, bronze, 8)
for side in (-1, 1):
    x = side * 1.15
    tube(f"SM_SeatRope_{'L' if side < 0 else 'R'}",
         [(x, .65, 1.48), (x + side * .03, .65, 2.3), (x + side * .01, .65, 3.65)],
         .018, rope, 10)
    tube(f"SM_SeatRim_{'L' if side < 0 else 'R'}",
         [(x, .29, 1.50), (x, 1.01, 1.50)], .055, bronze, 12)
    t = min((i / 1000 for i in range(1001)), key=lambda candidate: abs(bezier(candidate).x - x))
    p = bezier(t)
    tube(f"SM_UpperHook_{'L' if side < 0 else 'R'}",
         [(x, .65, 3.65), (p.x, .65, p.y)], .055, bronze, 12)

# A low-relief circle distinguishes the site when seen from an exploration camera.
for i in range(64):
    a, b = 2 * math.pi * i / 64, 2 * math.pi * (i + .82) / 64
    r = 1.15
    tube(f"SM_InlayArc_{i:02d}",
         [(r * math.cos(a), r * math.sin(a) - .38, .733),
          (r * math.cos(b), r * math.sin(b) - .38, .733)],
         .012, bronze, 6)

# Detachable edge dressing: bounded clumps for later LOD/culling.
rng = random.Random(617)
for index in range(26):
    angle = 2 * math.pi * index / 26 + rng.uniform(-.11, .11)
    x = 4.10 * math.cos(angle)
    y = 2.85 * math.sin(angle)
    for blade in range(4):
        ox, oy = rng.uniform(-.08, .08), rng.uniform(-.08, .08)
        height = rng.uniform(.13, .30)
        verts = [(x + ox - .025, y + oy, .73), (x + ox + .025, y + oy, .73),
                 (x + ox + rng.uniform(-.09, .09), y + oy + rng.uniform(-.06, .06), .73 + height)]
        mesh_object(f"SM_EdgeGrass_{index:02d}_{blade}", verts, [(0, 1, 2)], grass)
    if index % 3 == 0:
        stem = [(x, y, .74), (x, y, .94)]
        tube(f"SM_FlowerStem_{index:02d}", stem, .012, moss, 6)
        for petal in range(5):
            t = 2 * math.pi * petal / 5
            px, py = x + .035 * math.cos(t), y + .035 * math.sin(t)
            box(f"SM_BluePetal_{index:02d}_{petal}", (px, py, .94), (.045, .045, .017), flower)

# Loose stones and clustered wildflowers soften the cut edge without changing
# the walkable terrace; these are separate pieces for future Unity LODs.
for index in range(32):
    angle = 2 * math.pi * (index + rng.uniform(-.2, .2)) / 32
    x, y = 4.18 * math.cos(angle), 2.99 * math.sin(angle)
    radius = rng.uniform(.10, .27)
    verts = [(x + radius * math.cos(2 * math.pi * j / 7),
              y + radius * .65 * math.sin(2 * math.pi * j / 7),
              rng.uniform(-.14, .04)) for j in range(7)]
    verts.append((x, y, .20 + radius * .8))
    faces = [(j, (j + 1) % 7, 7) for j in range(7)]
    mesh_object(f"SM_EdgeStone_{index:02d}", verts, faces,
                stone if index % 3 else stone_dark)
for index in range(14):
    angle = 2 * math.pi * (index + .25) / 14
    x, y = 3.80 * math.cos(angle), 2.65 * math.sin(angle)
    for petal in range(5):
        theta = 2 * math.pi * petal / 5
        box(f"SM_FlowerCluster_{index:02d}_{petal}",
            (x + .06 * math.cos(theta), y + .06 * math.sin(theta), .87),
            (.055, .028, .016), flower)

# Presentation lights and cameras are excluded from the exported asset.
world = bpy.data.worlds.new("QingxiSky")
scene.world = world
world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs["Color"].default_value = (.63, .69, .69, 1)
bg.inputs["Strength"].default_value = 1.0
sun_data = bpy.data.lights.new("EveningSun", "SUN")
sun = bpy.data.objects.new("EveningSun", sun_data)
presentation.objects.link(sun)
sun_data.energy = 2.6
sun.rotation_euler = (math.radians(30), math.radians(-18), math.radians(-24))
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1500
scene.render.resolution_y = 950
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "Standard"
camera_data = bpy.data.cameras.new("ReviewCamera")
camera = bpy.data.objects.new("ReviewCamera", camera_data)
presentation.objects.link(camera)
scene.camera = camera
camera_data.type = "ORTHO"

for name, pos, target, scale in (
    ("perspective", (9, -12, 8), (0, .4, 1.35), 11.5),
    ("front", (0, -15, 3), (0, .25, 2), 10.0),
    ("right", (13, 0, 3), (0, .25, 2), 10.0),
    ("top", (0, 0, 15), (0, 0, 0), 10.5),
):
    camera.location = pos
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.ortho_scale = scale
    scene.render.filepath = str(PREVIEW / (name + ".png"))
    bpy.ops.render.render(write_still=True)

scene.render.filepath = "//"
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE))
for ob in bpy.context.selected_objects:
    ob.select_set(False)
for ob in asset.objects:
    ob.select_set(True)
bpy.context.view_layer.objects.active = next(iter(asset.objects))
bpy.ops.export_scene.gltf(filepath=str(EXPORT), export_format="GLB", use_selection=True)
print("TERRACE_BUILT", len(asset.objects), "parts", SOURCE, EXPORT)
