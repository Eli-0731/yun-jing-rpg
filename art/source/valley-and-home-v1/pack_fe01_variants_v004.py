"""Pack FE01 corner and end as independent modular art assets."""
import bpy
import json
from pathlib import Path

root = Path(__file__).resolve().parents[3]
for kind in ('Corner', 'End'):
    slug = kind.lower()
    src = root / f'art/source/valley-and-home-v1/FE01/FE01-{slug}-qa-v003.blend'
    outblend = root / f'art/source/valley-and-home-v1/FE01/FE01-{slug}-pack-v004.blend'
    out = root / f'art/exports/valley-and-home-v1/FE01/{kind}/v004'
    out.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(src))

    def join_group(names, name):
        if not names:
            raise ValueError(f'{kind}: empty group {name}')
        bpy.ops.object.select_all(action='DESELECT')
        for item in names:
            bpy.data.objects[item].select_set(True)
        active = bpy.data.objects[names[0]]
        bpy.context.view_layer.objects.active = active
        bpy.ops.object.join()
        active.name = name
        active.data.name = name + '_Mesh'
        bpy.context.scene.cursor.location = (0, 0, 0)
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        return active

    # Keep the guard/opening silhouette in every LOD; only bindings and edge trim are optional.
    guard_prefixes = (f'Detail_FE01_{kind}_UpperRail_', f'Detail_FE01_{kind}_RailUpright_')
    main_names = sorted(o.name for o in bpy.data.objects if o.type == 'MESH' and
        (o.name.startswith('SM_FE01_') or o.name.startswith(guard_prefixes)))
    detail_names = sorted(o.name for o in bpy.data.objects if o.type == 'MESH' and
        o.name.startswith('Detail_FE01_') and not o.name.startswith(guard_prefixes))
    main = join_group(main_names, f'SM_FE01_{kind}_LOD0')
    detail = join_group(detail_names, f'Detail_FE01_{kind}_RopeBamboo_LOD0')
    objects = [main, detail]
    for lod, ratio in ((1, .90), (2, .64)):
        ob = main.copy()
        ob.data = main.data.copy()
        ob.name = f'SM_FE01_{kind}_LOD{lod}'
        bpy.context.collection.objects.link(ob)
        modifier = ob.modifiers.new(f'FE01_Decimate_LOD{lod}', 'DECIMATE')
        modifier.ratio = ratio
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        objects.append(ob)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, .38))
    collision = bpy.context.object
    collision.name = f'SM_FE01_{kind}_Collision'
    collision.dimensions = (1.58, 2.98, .14)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    collision.hide_render = True
    objects.append(collision)
    for im in bpy.data.images:
        if im.source == 'FILE' and im.has_data:
            im.pack()
    bpy.ops.wm.save_as_mainfile(filepath=str(outblend))
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = main
    bpy.ops.export_scene.fbx(filepath=str(out / f'FE01_{kind}.fbx'), use_selection=True,
        apply_unit_scale=True, mesh_smooth_type='FACE', path_mode='COPY', embed_textures=True)
    bpy.ops.export_scene.gltf(filepath=str(out / f'FE01_{kind}.glb'), export_format='GLB',
        use_selection=True, export_apply=True, export_extras=True, export_vertex_color='NONE')
    info = {ob.name: {'vertices': len(ob.data.vertices),
        'triangles': sum(len(p.vertices)-2 for p in ob.data.polygons),
        'dimensions_m': [round(x, 5) for x in ob.dimensions],
        'origin_m': [round(x, 5) for x in ob.location]}
        for ob in objects}
    info.update({'minTier': 'standard', 'detailObjects': [detail.name],
        'waterline_z_m': 0, 'deck_top_z_m': .45, 'pile_bottom_z_m': -1,
        'source': str(outblend.relative_to(root)).replace('\\', '/'),
        'status': 'export candidate; reimport and visual QA pending'})
    (out / 'model_info.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
    print('@@FE01PACK@@' + json.dumps({'kind': kind, 'triangles': {ob.name: info[ob.name]['triangles'] for ob in objects}}, ensure_ascii=False))
