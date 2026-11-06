"""F01_Field LOD0 beside LOD1, the sheet the work pack asks for, and its measured size in model_info.json.

F01_Field is cut from F01 by cut_field_gap.py rather than built by the kit, so the kit's own sheet never ran on it.
The model files are not touched.

blender --background --factory-startup --python art/source/creek-repair-b/field_lod_compare.py -- <repo>/art
"""
import bpy, json, math, sys
from pathlib import Path
from mathutils import Vector

ART = Path(sys.argv[sys.argv.index('--') + 1])
sys.path.insert(0, str(Path(__file__).parent))
import field_look
ID = 'F01_Field'
OUT = ART / 'previews' / 'creek-repair-b' / ID / f'{ID}_LOD_comparison.png'
scene = bpy.context.scene
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
bpy.ops.import_scene.fbx(filepath=str(ART / 'exports' / 'creek-repair-b' / ID / f'{ID}.fbx'))   # the saved blend holds LOD0 only; the export holds all three
field_look.apply(ART)
for o in scene.objects:                         # the LODs hang off LOD0 in the file; freed so that each side moves alone
    world = o.matrix_world.copy(); o.parent = None; o.matrix_world = world
meshes = [o for o in scene.objects if o.type == 'MESH']
lod = {'_LOD0': [o for o in meshes if 'LOD' not in o.name], '_LOD1': [o for o in meshes if 'LOD1' in o.name]}
assert lod['_LOD0'] and lod['_LOD1'], [o.name for o in meshes]
for o in scene.objects: o.hide_render = not any(o in v for v in lod.values())


def bounds(objs):
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in objs:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c); lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    return lo, hi


lo, hi = bounds(lod['_LOD0']); size = hi - lo; gap = size.x * 1.08
for o in lod['_LOD0']: o.location.x -= gap / 2
for o in lod['_LOD1']: o.location.x += gap / 2
bpy.context.view_layer.update()


def tris(objs):
    return sum(len(p.vertices) - 2 for o in objs for p in o.data.polygons)


ink = bpy.data.materials.new('Ink'); ink.use_nodes = True; ink.node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value = (1, 1, 1, 1); ink.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 1
for key, x in (('_LOD0', -gap / 2), ('_LOD1', gap / 2)):
    t = bpy.data.curves.new(key, 'FONT'); t.body = f"{key[1:]}  {tris(lod[key]):,} tris"; t.size = .32; t.align_x = 'CENTER'; t.materials.append(ink)
    o = bpy.data.objects.new(key + '_label', t); scene.collection.objects.link(o); o.location = (x, lo.y - .5, 0); o.rotation_euler = (math.radians(45), 0, 0)

sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); scene.collection.objects.link(sun); sun.data.energy = 3.2
sun.rotation_euler = (math.radians(52), 0, math.radians(38))
w = bpy.data.worlds.new('Grey'); w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (.42, .43, .44, 1); scene.world = w
cam_d = bpy.data.cameras.new('Cam'); cam_d.type = 'ORTHO'; cam_d.ortho_scale = (size.x + gap) * 1.08
cam = bpy.data.objects.new('Cam', cam_d); scene.collection.objects.link(cam); scene.camera = cam
centre = (lo + hi) / 2; d = Vector((0, -1, 1.05)).normalized()
cam.location = Vector((0, centre.y, centre.z)) + d * (size.length + 4)
cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
scene.render.engine = 'BLENDER_EEVEE'; scene.render.resolution_x, scene.render.resolution_y = 1600, 900
scene.view_settings.view_transform = 'Standard'; scene.render.filepath = str(OUT)
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.render.render(write_still=True)

info_path = ART / 'exports' / 'creek-repair-b' / ID / 'model_info.json'
info = json.loads(info_path.read_text(encoding='utf-8'))
info['dimensions_m'] = [round(v, 4) for v in size]
info_path.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
print('FIELD_LOD saved', OUT, info['dimensions_m'], {k: [o.name for o in v] for k, v in lod.items()})
