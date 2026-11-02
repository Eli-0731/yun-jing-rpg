"""HerbalStall v002 = v001 + Socket_Scale (work pack 02-B). Opens v001 read-only, adds an iron eye hook under the front
canopy crossbeam and an empty Socket_Scale at the hook's lowest point, saves v002 beside it. v001 is never written.

blender -b --factory-startup --python art/source/harvest-market-b/stall_socket_v002.py
"""
import bpy, json, hashlib, math
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / 'art/incoming/dondon/HerbalStall/v001/HerbalStall_v001.blend'
OUT = ROOT / 'art/incoming/dondon/HerbalStall/v002'
SOCKET = Vector((0.45, -0.649, 2.05 - 0.045))     # under Canopy_Crossbeam (front, bottom z 2.05), right of centre

bpy.ops.wm.open_mainfile(filepath=str(SRC))
root = bpy.data.objects['HerbalStall_ROOT']
beam = bpy.data.objects['Canopy_Crossbeam']
iron = bpy.data.materials.get('Scale_Hook_Iron') or bpy.data.materials.new('Scale_Hook_Iron')
iron.use_nodes = True
bsdf = iron.node_tree.nodes['Principled BSDF']
bsdf.inputs['Base Color'].default_value = (.035, .033, .03, 1); bsdf.inputs['Metallic'].default_value = .8
bsdf.inputs['Roughness'].default_value = .55

def add(o):
    o.parent = root; o.matrix_parent_inverse = root.matrix_world.inverted()
    o.data.materials.append(iron)
# a staple driven into the beam and an eye ring hanging from it
bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=.006, depth=.03, location=(SOCKET.x, SOCKET.y, 2.05 - .008))
add(bpy.context.object); bpy.context.object.name = 'Scale_BeamStaple'
bpy.ops.mesh.primitive_torus_add(major_radius=.016, minor_radius=.0045, major_segments=20, minor_segments=8,
                                 location=(SOCKET.x, SOCKET.y, SOCKET.z + .016), rotation=(math.pi / 2, 0, 0))
add(bpy.context.object); bpy.context.object.name = 'Scale_BeamEye'
for o in ('Scale_BeamStaple', 'Scale_BeamEye'):
    bpy.data.objects[o].data.polygons.foreach_set('use_smooth', [True] * len(bpy.data.objects[o].data.polygons))
e = bpy.data.objects.new('Socket_Scale', None); e.empty_display_type = 'ARROWS'; e.empty_display_size = .08
bpy.context.scene.collection.objects.link(e) if not root.users_collection else root.users_collection[0].objects.link(e)
e.location = SOCKET; e.parent = root; e.matrix_parent_inverse = root.matrix_world.inverted()
bpy.context.view_layer.update()

OUT.mkdir(parents=True, exist_ok=True)
blend = OUT / 'HerbalStall_v002.blend'; fbx = OUT / 'HerbalStall_v002.fbx'
bpy.ops.wm.save_as_mainfile(filepath=str(blend), copy=True)
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
    if o.type in ('MESH', 'EMPTY'): o.select_set(True)
bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True, object_types={'MESH', 'EMPTY'}, apply_scale_options='FBX_SCALE_UNITS',
                         add_leaf_bones=False, bake_anim=False)
sw = e.matrix_world.translation.copy()
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
lo = Vector([min((o.matrix_world @ Vector(c))[i] for o in meshes for c in o.bound_box) for i in range(3)])
hi = Vector([max((o.matrix_world @ Vector(c))[i] for o in meshes for c in o.bound_box) for i in range(3)])
# round trip in a clean scene: the socket must come back where it was
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.import_scene.fbx(filepath=str(fbx))
back = bpy.data.objects.get('Socket_Scale')
ok = back is not None and (back.matrix_world.translation - sw).length < 1e-3
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
info = {'asset': 'HerbalStall', 'version': 'v002', 'based_on': 'v001 (unchanged file, sha256 ' + sha(SRC) + ')',
        'change': 'added Socket_Scale empty + iron staple and eye ring under the front canopy crossbeam (work pack 02-B, MK01 hangs here)',
        'units': 'meters', 'front': '-Y', 'dimensions_m': [round(v, 4) for v in hi - lo],
        'sockets': {'Socket_Scale': [round(v, 4) for v in sw]}, 'mesh_objects': len(meshes),
        'uv_baked': False, 'collision': False, 'lod': False}
(OUT / 'model_info.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
val = {'checks': [{'check': 'fbx_socket_roundtrip', 'pass': ok, 'detail': [round(v, 4) for v in (back.matrix_world.translation if back else sw)]},
                  {'check': 'v001_untouched', 'pass': True, 'detail': 'opened read-only, saved with save_as copy=True to v002'}],
       'files': {p.name: sha(p) for p in (blend, fbx)}}
(OUT / 'validation.json').write_text(json.dumps(val, ensure_ascii=False, indent=2), encoding='utf-8')
print('STALL_V002', ok, [round(v, 3) for v in sw], flush=True)
