"""Reopen and audit rabbit source and exchange files in Blender 5.2."""
import hashlib
import json
import struct
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'art/source/qingxi-mountain-rabbit-v003'
EXPORT = ROOT / 'art/exports/qingxi-mountain-rabbit-v003'
SOURCE = ROOT / 'art/incoming/dondon/QMountainRabbit/v002/QMountainRabbit_v002.blend'
BLEND = BASE / 'QingxiMountainRabbit_v003.blend'
SOURCE_INFO = json.loads((SOURCE.parent / 'model_info.json').read_text(encoding='utf8'))
NAMES = ['Rabbit_Idle', 'Rabbit_Hop', 'Rabbit_Flee', 'Rabbit_Hit', 'Rabbit_Death']
errors = []
report = {'validator': 'Blender 5.2.2 + Python', 'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest()}

def check(condition, message):
    if not condition:
        errors.append(message)

def bounds(objects):
    pts = [ob.matrix_world @ Vector(c) for ob in objects for c in ob.bound_box]
    return [[min(p[i] for p in pts), max(p[i] for p in pts)] for i in range(3)]

bpy.ops.wm.open_mainfile(filepath=str(BLEND))
arm = bpy.data.objects['RIG_QingxiRabbit']
lods = [bpy.data.objects[f'SK_QingxiRabbit_LOD{i}'] for i in range(3)]
report['blend'] = {'armature_bones': len(arm.data.bones), 'bone_names': [b.name for b in arm.data.bones], 'lods': [], 'actions': {}}
check(len(arm.data.bones) >= 17, 'too few rig bones')
for i, ob in enumerate(lods):
    triangles = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    count_unweighted = sum(1 for v in ob.data.vertices if not v.groups)
    over_four = sum(1 for v in ob.data.vertices if len(v.groups) > 4)
    deviations = 0
    for v in ob.data.vertices:
        weight_sum = sum(g.weight for g in v.groups)
        if abs(weight_sum - 1) > 0.001:
            deviations += 1
    record = {'mesh': ob.name, 'triangles': triangles, 'vertices': len(ob.data.vertices), 'material_slots': len(ob.data.materials), 'unweighted_vertices': count_unweighted, 'over_four_influences': over_four, 'unnormalized_vertices': deviations, 'bounds_m': bounds([ob])}
    report['blend']['lods'].append(record)
    check(count_unweighted == 0 and over_four == 0 and deviations == 0, f'LOD{i} skin weights invalid')
    check(len(ob.data.materials) <= 3, f'LOD{i} too many material slots')
for i, limit in enumerate(((0, 22500), (10000, 12000), (3500, 5000))):
    t = report['blend']['lods'][i]['triangles']
    check(limit[0] <= t <= limit[1], f'LOD{i} triangle count {t} outside target')
for name in NAMES:
    action = bpy.data.actions.get(name)
    check(action is not None, f'missing action {name}')
    if action:
        report['blend']['actions'][name] = {'frames': int(action.get('frames', 0)), 'loop': bool(action.get('loop', False)), 'frame_range': list(action.frame_range)}
for name, frames, loop in (('Rabbit_Idle',48,True),('Rabbit_Hop',24,True),('Rabbit_Flee',16,True),('Rabbit_Hit',8,False),('Rabbit_Death',24,False)):
    item = report['blend']['actions'].get(name, {})
    check(item.get('frames') == frames and item.get('loop') == loop, f'incorrect clip metadata {name}')
report['pose_qa'] = {}
mesh = lods[0]
for name in NAMES:
    action = bpy.data.actions[name]
    arm.animation_data.action = action
    end = int(action['frames'])
    samples = range(1, end + 1)
    frames = []
    for frame in samples:
        bpy.context.scene.frame_set(frame)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        evaluated = mesh.evaluated_get(depsgraph)
        temp = evaluated.to_mesh()
        zs = [(evaluated.matrix_world @ v.co).z for v in temp.vertices]
        low_index = zs.index(min(zs))
        low_groups = [mesh.vertex_groups[g.group].name for g in mesh.data.vertices[low_index].groups]
        frames.append({'frame': frame, 'min_z_m': round(min(zs), 5), 'max_z_m': round(max(zs), 5), 'root_local_y_m': round(arm.pose.bones['Root'].location.y, 5), 'low_vertex_groups': low_groups})
        evaluated.to_mesh_clear()
    report['pose_qa'][name] = frames
    check(min(item['min_z_m'] for item in frames) >= -0.005, f'ground penetration above 5 mm in {name}')
arm.animation_data.action = bpy.data.actions['Rabbit_Idle']
bpy.context.scene.frame_set(1)
report['textures'] = {p.name: p.stat().st_size for p in (BASE/'textures').glob('*.png')}
check(len(report['textures']) == 3, 'missing PBR texture maps')

# glTF 2.0 JSON chunk is independently inspected before Blender import.
glb = EXPORT / 'QingxiMountainRabbit_v003.glb'
blob = glb.read_bytes()
check(blob[:4] == b'glTF', 'invalid GLB header')
length, chunk_type = struct.unpack_from('<II', blob, 12)
gltf = json.loads(blob[20:20+length])
report['glb_json'] = {'meshes': len(gltf.get('meshes', [])), 'skins': len(gltf.get('skins', [])), 'animations': [a.get('name') for a in gltf.get('animations', [])], 'materials': len(gltf.get('materials', []))}
check(set(report['glb_json']['animations']) == set(NAMES), 'GLB clip names missing')
check(report['glb_json']['skins'] == 1, 'GLB skin missing')
check(report['glb_json']['meshes'] == 1, 'GLB mesh count unexpected')

report['roundtrip'] = {}
for path in [EXPORT/'QingxiMountainRabbit_v003.fbx', EXPORT/'QingxiMountainRabbit_v003_LOD1.fbx', EXPORT/'QingxiMountainRabbit_v003_LOD2.fbx', glb] + [EXPORT/(name+'.fbx') for name in NAMES]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if path.suffix == '.fbx':
        bpy.ops.import_scene.fbx(filepath=str(path), use_anim=True)
    else:
        bpy.ops.import_scene.gltf(filepath=str(path))
    meshes = [ob for ob in bpy.context.scene.objects if ob.type == 'MESH' and ob.name.startswith('SK_QingxiRabbit')]
    armatures = [ob for ob in bpy.context.scene.objects if ob.type == 'ARMATURE']
    tris = sum(sum(len(p.vertices)-2 for p in ob.data.polygons) for ob in meshes)
    record = {'mesh_names': [ob.name for ob in meshes], 'mesh_count': len(meshes), 'armature_count': len(armatures), 'triangles': tris, 'bounds_m': bounds(meshes) if meshes else None, 'action_names': [a.name for a in bpy.data.actions], 'action_ranges': {a.name: list(a.frame_range) for a in bpy.data.actions}}
    report['roundtrip'][path.name] = record
    check(len(meshes) == 1 and len(armatures) == 1, f'bad roundtrip objects {path.name}')
    if path.name.endswith('_LOD1.fbx'):
        check(tris == report['blend']['lods'][1]['triangles'], 'LOD1 triangle mismatch')
    elif path.name.endswith('_LOD2.fbx'):
        check(tris == report['blend']['lods'][2]['triangles'], 'LOD2 triangle mismatch')
    else:
        check(tris == report['blend']['lods'][0]['triangles'], f'master triangle mismatch {path.name}')
    if path == glb or path.name == 'QingxiMountainRabbit_v003.fbx':
        actual_dimensions = [axis[1] - axis[0] for axis in record['bounds_m']]
        check(all(abs(a - b) < .001 for a, b in zip(actual_dimensions, SOURCE_INFO['dimensions_m'])), f'roundtrip dimension differs by 1 mm or more: {path.name}')
    if path == glb:
        check(set(record['action_names']) >= set(NAMES), 'GLB imported action names missing')
    if path.stem in NAMES:
        check(len(record['action_names']) == 1, f'clip FBX action count mismatch {path.name}')
        check(abs(max(record['action_ranges'].values())[1] - report['blend']['actions'][path.stem]['frames']) <= 1, f'clip FBX frame range mismatch {path.name}')

report['errors'] = errors
report['pass'] = len(errors) == 0
(BASE/'validation.json').write_text(json.dumps(report, indent=2), encoding='utf8')
(EXPORT/'validation.json').write_text(json.dumps({'source_validation': '../../source/qingxi-mountain-rabbit-v003/validation.json', 'roundtrip': report['roundtrip'], 'glb_json': report['glb_json'], 'pass': report['pass'], 'errors': errors}, indent=2), encoding='utf8')
print('RABBIT_VALIDATE', json.dumps({'pass': report['pass'], 'errors': errors, 'roundtrip': report['roundtrip']}))
if errors:
    raise RuntimeError('; '.join(errors))
