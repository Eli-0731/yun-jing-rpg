"""Export each editable collection as one game mesh, then import all six GLBs back.

Run in a separate Blender background process after build_yard.py and review_yard.py.
The source .blend is never modified by this script.
"""
import bpy
import json
from pathlib import Path
from mathutils import Vector

root = Path(__file__).resolve().parent
project = root.parents[2]
out = project / 'art/exports/qingxi-training-yard-v1'
names = ['training-shelter', 'qi-striking-post', 'agility-post', 'weapon-rack', 'engraved-training-stone', 'training-banner']
bpy.ops.wm.open_mainfile(filepath=str(root / 'Qingxi_Training_Yard_v1.blend'))
manifest = json.loads((out / 'asset-manifest.json').read_text(encoding='utf8'))

for name in names:
    source = list(bpy.data.collections[name].objects)
    copies = []
    for original in source:
        duplicate = original.copy()
        duplicate.data = original.data.copy()
        bpy.context.scene.collection.objects.link(duplicate)
        bpy.ops.object.select_all(action='DESELECT')
        duplicate.select_set(True)
        bpy.context.view_layer.objects.active = duplicate
        for modifier in list(duplicate.modifiers):
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        copies.append(duplicate)
    bpy.ops.object.select_all(action='DESELECT')
    for duplicate in copies:
        duplicate.select_set(True)
    bpy.context.view_layer.objects.active = copies[0]
    bpy.ops.object.join()
    combined = copies[0]
    combined.name = name
    combined['asset_id'] = name
    combined['author'] = 'Johnnnny0823 / Codex'
    combined['source'] = 'Original procedural geometry based on saved AI three-view'
    glb = out / f'{name}.glb'
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format='GLB', use_selection=True,
                              export_apply=True, export_yup=True, export_image_format='AUTO')
    manifest[name]['export_meshes'] = 1
    manifest[name]['export_triangles'] = sum(len(face.vertices) - 2 for face in combined.data.polygons)
    manifest[name]['export_materials'] = sorted({slot.material.name for slot in combined.material_slots if slot.material})
    manifest[name]['glb_bytes'] = glb.stat().st_size
    bpy.data.objects.remove(combined, do_unlink=True)

# A fresh empty scene verifies glTF import rather than reusing source objects.
bpy.ops.wm.read_factory_settings(use_empty=True)
for name in names:
    existing = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(out / f'{name}.glb'))
    imported = [ob for ob in bpy.data.objects if ob not in existing and ob.type == 'MESH']
    assert imported, f'No mesh imported: {name}'
    triangles = sum(sum(len(face.vertices) - 2 for face in ob.data.polygons) for ob in imported)
    assert triangles == manifest[name]['export_triangles'], (name, triangles, manifest[name]['export_triangles'])
    assert all(ob.data.uv_layers for ob in imported), f'Missing UV: {name}'
    assert all(ob.data.materials for ob in imported), f'Missing material: {name}'
    points = [ob.matrix_world @ Vector(corner) for ob in imported for corner in ob.bound_box]
    size = [max(point[axis] for point in points) - min(point[axis] for point in points) for axis in range(3)]
    assert all(.05 < value < 10 for value in size), f'Unexpected size: {name}: {size}'
    manifest[name]['roundtrip'] = {'meshes': len(imported), 'triangles': triangles,
                                   'uv': True, 'materials': True, 'glb_axis_dimensions_m': size}
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    print('ROUNDTRIP_OK', name, triangles, size, flush=True)
(out / 'asset-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf8')
