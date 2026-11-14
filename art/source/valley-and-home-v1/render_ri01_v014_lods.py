"""Render exported RI01 GLB LOD0 and LOD1, both with Detail turned off."""
import bpy
import sys
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[3]
version=sys.argv[sys.argv.index("--")+1] if "--" in sys.argv else "v010"
SOURCE=ROOT/"art/exports/valley-and-home-v1/RI01"/version/"RI01_Paddy.glb"
PREVIEW=ROOT/"art/previews/valley-and-home-v1/RI01"/version
PREVIEW.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
for lod,shift in ((0,-6.25),(1,6.25)):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.import_scene.gltf(filepath=str(SOURCE))
    imported=[o for o in bpy.context.selected_objects if o.type=="MESH"]
    assert len(imported)==14
    for obj in imported:
        obj.location.x+=shift
        canonical=obj.name.split(".")[0]
        show=((canonical.startswith("SM_RI01_Paddy_Base_LOD") or
              canonical.startswith("SM_RI01_State_Flooded_LOD")) and
              canonical.endswith(f"LOD{lod}"))
        obj.hide_render=not show

world=bpy.data.worlds.new("RI01 LOD Comparison World")
bpy.context.scene.world=world
world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Color"].default_value=(0.73,0.76,0.79,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value=0.72
sun_data=bpy.data.lights.new("Shared Area","AREA")
sun=bpy.data.objects.new("Shared Area",sun_data)
bpy.context.collection.objects.link(sun)
sun.location=(-6,-11,15)
sun_data.energy=4500
sun_data.size=10

# Nonhuman 1.75 m measuring sticks, outside each field footprint.
ruler=bpy.data.materials.new("Ruler Neutral")
ruler.diffuse_color=(0.19,0.18,0.16,1)
ruler.use_nodes=True
ruler.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=ruler.diffuse_color
for x in (-11.8,0.7):
    bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=0.025,depth=1.75,location=(x,-4,0.875))
    bpy.context.object.name="HeightRuler_1p75m"
    bpy.context.object.data.materials.append(ruler)

cam_data=bpy.data.cameras.new("Shared Camera")
cam=bpy.data.objects.new("Shared Camera",cam_data)
bpy.context.collection.objects.link(cam)
cam.location=(2,-18,14)
cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat("-Z","Y").to_euler()
cam_data.type="ORTHO"
cam_data.ortho_scale=29
scene=bpy.context.scene
scene.camera=cam
scene.render.engine="BLENDER_EEVEE"
scene.render.resolution_x=1800
scene.render.resolution_y=1000
scene.render.resolution_percentage=100
scene.view_settings.view_transform="AgX"
gray=bpy.data.materials.new("Comparison Gray")
gray.use_nodes=True
gray.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(0.62,0.62,0.62,1)
scene.view_layers[0].material_override=gray
scene.render.filepath=str(PREVIEW/"RI01_LOD0_LOD1_detail_off_gray.png")
bpy.ops.render.render(write_still=True)
scene.view_layers[0].material_override=None
scene.render.filepath=str(PREVIEW/"RI01_LOD0_LOD1_detail_off_material.png")
bpy.ops.render.render(write_still=True)
