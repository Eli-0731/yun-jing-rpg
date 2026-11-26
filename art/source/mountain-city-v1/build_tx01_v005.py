"""TX01 v005：沿用 John MC01 共用 Trim Sheet 與石塊建模函式重做材質、底座。"""
import bpy
import bmesh
import json
import math
import sys
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'art/source/mountain-street-houses-a'))
import build_mc01 as mc

SRC = ROOT / 'art/source/mountain-city-v1/TX01'
OUT = ROOT / 'art/exports/mountain-city-v1/TX01/v005'
PRE = ROOT / 'art/previews/mountain-city-v1/TX01/v005'
OUT.mkdir(parents=True, exist_ok=True)
PRE.mkdir(parents=True, exist_ok=True)


def tris(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def strip_for(obj):
    name = obj.name.lower()
    material = (obj.data.materials[0].name if obj.data.materials else '').lower()
    if 'roof' in name or 'eave' in name or 'tiles' in material:
        return 'tile_moss' if 'lip' in name and '00' in name else 'tile'
    if 'stone' in name or 'step' in name or 'pale_stone' in material:
        return 'granite_moss' if 'base' in name else 'granite_top'
    if 'copper' in name or 'brass' in material or 'pin' in name:
        return 'bronze'
    if 'backpanel' in name or 'slot_' in name or 'smoke' in material:
        return 'oldwood'
    if 'plaque' in name or 'board' in name or 'panel' in name:
        return 'plank'
    if 'fruit' in name:
        return 'paper'
    if 'inkstone' in name:
        return 'dark'
    return 'beam'


def copy_and_trim(obj):
    new = obj.copy()
    new.data = obj.data.copy()
    bpy.context.scene.collection.objects.link(new)
    new.parent = None
    new.matrix_world = obj.matrix_world.copy()
    new.hide_set(False)
    new.hide_render = False
    new.name = 'Rework_' + obj.name
    strip = strip_for(obj)
    mc.reuv(new, strip)
    bm = bmesh.new()
    bm.from_mesh(new.data)
    bmesh.ops.dissolve_degenerate(bm, edges=list(bm.edges), dist=.0001)
    if bm.faces and bm.calc_volume(signed=True) < -.000001:
        bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
    bm.to_mesh(new.data)
    bm.free()
    new.data.materials.clear()
    new.data.materials.append(mc.MAT[0])
    new['mc01_trim_strip'] = strip
    return new


def join(objects, name):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.hide_set(False)
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    out = bpy.context.object
    out.name = name
    out.data.name = name + '_Mesh'
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    return out


def simplify(obj, name, ratio):
    out = obj.copy()
    out.data = obj.data.copy()
    bpy.context.scene.collection.objects.link(out)
    out.name = name
    bpy.context.view_layer.objects.active = out
    modifier = out.modifiers.new('LOD', 'DECIMATE')
    modifier.ratio = ratio
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    out.hide_render = True
    return out


def collider(name, center, size):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.hide_render = True
    return obj


def save_gray(objects, label):
    gray = bpy.data.materials.new('M_TX01_Gray')
    gray.diffuse_color = (.55, .55, .55, 1)
    saved = [(obj, [mat for mat in obj.data.materials]) for obj in objects]
    for obj, _ in saved:
        obj.data.materials.clear()
        obj.data.materials.append(gray)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / f'TX01_{label}_v005_gray.blend'))
    for obj, mats in saved:
        obj.data.materials.clear()
        for mat in mats:
            obj.data.materials.append(mat)


def export(label, objects):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.hide_set(False)
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.fbx(filepath=str(OUT / f'TX01_{label}.fbx'), use_selection=True,
                             apply_unit_scale=True, bake_space_transform=False, path_mode='AUTO')
    bpy.ops.export_scene.gltf(filepath=str(OUT / f'TX01_{label}.glb'), export_format='GLB', use_selection=True)


def render(label, main, detail):
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            obj.hide_render = obj not in ([main] + ([detail] if detail else []))
    world = bpy.data.worlds.new('ReviewWorld')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (.58, .62, .66, 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = .8
    bpy.context.scene.world = world
    bpy.ops.object.light_add(type='AREA', location=(0, -5, 9))
    bpy.context.object.data.energy = 1100
    bpy.context.object.data.shape = 'DISK'
    bpy.context.object.data.size = 7
    pts = [obj.matrix_world @ Vector(c) for obj in ([main] + ([detail] if detail else [])) for c in obj.bound_box]
    low = Vector(min(p[i] for p in pts) for i in range(3))
    high = Vector(max(p[i] for p in pts) for i in range(3))
    mid = (low + high) / 2
    radius = (high - low).length / 2
    bpy.ops.object.camera_add(location=mid + Vector((radius * 1.25, -radius * 1.75, radius * 1.1)))
    camera = bpy.context.object
    camera.rotation_euler = (mid - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = radius * 2.6
    bpy.context.scene.camera = camera
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = str(PRE / f'TX01_{label}_threequarter.png')
    bpy.ops.render.render(write_still=True)


def build(label, filename):
    bpy.ops.wm.open_mainfile(filepath=str(SRC / filename))
    mc.parts.clear()
    mc.MAT.clear()
    mc.load_trim()
    originals = [obj for obj in bpy.data.objects if obj.type == 'MESH']
    core = [obj for obj in originals if (obj.name.startswith('SM_') or obj.name.startswith('Slot_'))
            and obj.name != 'SM_TX01_FrontStep']
    detail = [obj for obj in originals if obj.name.startswith('Detail_')]
    for obj in originals:
        obj.hide_render = True
        obj.hide_set(True)
    core_copies = [copy_and_trim(obj) for obj in core]
    detail_copies = [copy_and_trim(obj) for obj in detail]
    if label == 'Board':
        # MC01 石基：兩層錯縫花崗石，厚度 0.64 m，底層保留潮濕與苔色。
        for row, z in enumerate((.16, .48)):
            for index in range(8):
                x = -3.40 + index * .96 + (.12 if row else 0)
                if x > 3.36:
                    x = 3.36
                block = mc.box(f'TX01_StoneCourse_{row}_{index}', (.94, 1.85, .32),
                               (x, 0, z), 'granite_moss' if row == 0 else 'granite',
                               'TX01_Base', bev=.018, cuts=2)
                mc.chisel(block, .018, 9, 1100 + row * 20 + index)
                core_copies.append(block)
        # 舊 0.32 m 薄石台不再併入主網格；台階與供桌仍沿用原有幾何。
        for obj in list(core_copies):
            if obj.name.endswith('SM_TX01_StoneBase'):
                core_copies.remove(obj)
                bpy.data.objects.remove(obj, do_unlink=True)
    main = join(core_copies, f'SM_TX01_{label}_LOD0')
    extra = join(detail_copies, f'Detail_TX01_{label}_LOD0') if detail_copies else None
    lod1 = simplify(main, f'SM_TX01_{label}_LOD1', .72)
    lod2 = simplify(main, f'SM_TX01_{label}_LOD2', .35)
    outputs = [main] + ([extra] if extra else []) + [lod1, lod2]
    if label == 'Board':
        outputs += [collider('UCX_TX01_Board_Base', (0, 0, .32), (7.8, 1.95, .64)),
                    collider('UCX_TX01_Board_LeftPost', (-3.42, 0, 2.6), (.36, .40, 5.2)),
                    collider('UCX_TX01_Board_RightPost', (3.42, 0, 2.6), (.36, .40, 5.2)),
                    collider('UCX_TX01_Board_Panel', (0, .12, 3.15), (6.35, .24, 3.14))]
    else:
        outputs.append(collider('UCX_TX01_Plaque', (0, 0, 0), (2.4, .15, .8)))
    save_gray(outputs, label)
    for obj in outputs:
        obj.hide_render = obj != main
    if extra:
        extra.hide_render = False
    bpy.ops.wm.save_as_mainfile(filepath=str(SRC / f'TX01-{label.lower()}-pack-v005.blend'))
    export(label, outputs)
    render(label, main, extra)
    return {obj.name: tris(obj) for obj in outputs}


info = {'Board': build('Board', 'TX01-ascension-board-material-v004.blend'),
        'Plaque': build('Plaque', 'TX-Plaque-material-v004.blend')}
(OUT / 'model_info.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
print('DONE', info, flush=True)
