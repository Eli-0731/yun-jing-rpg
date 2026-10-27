"""B01 + B02 fit check on the exported GLBs (not the source parts).

  blender -b --python-exit-code 1 --python combo.py

Seats the matching lid state (cold lid on the cold furnace, heated lid on the heating one) on the furnace socket `lid_seat`, measures triangle overlap and clearances, renders closed/heating/open
and writes art/exports/qingxi-alchemy-b/fit_B01_B02.json.
"""
import bpy, sys, json, math
from pathlib import Path
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
import qa_lib as Q

EX = Q.EXPORTS
OUT = Q.PREVIEWS / 'B01_B02_fit'


def load(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    objs = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    for o in objs:
        o.select_set(True)
    return objs


def info(aid, key):
    return json.loads((EX / aid / Q.VER / f'{key}_model_info.json').read_text(encoding='utf-8'))


def world_verts(objs):
    return [o.matrix_world @ v.co for o in objs for v in o.data.vertices]


def overlaps(a_objs, b_objs):
    n = 0
    for a in a_objs:
        ta = Q.bvh_of(a)
        for b in b_objs:
            n += len(ta.overlap(Q.bvh_of(b)))
    return n


def run(state):
    Q.reset()
    fur = load(EX / 'B01_BronzeFurnace' / Q.VER / f'B01_BronzeFurnace_{state}.glb')
    lkey = 'B02_FurnaceLid' if state == 'cold' else f'B02_FurnaceLid_{state}'   # cold lid kept the unsuffixed key
    lid = load(EX / 'B02_FurnaceLid' / Q.VER / f'{lkey}.glb')
    fi, li = info('B01_BronzeFurnace', f'B01_BronzeFurnace_{state}'), info('B02_FurnaceLid', lkey)
    seat = Vector(fi['sockets']['lid_seat']); rim = fi['rim']
    for o in lid:
        o.location = o.location + seat
    bpy.context.view_layer.update()
    fv, lv = world_verts(fur), world_verts(lid)
    under = li['sockets']['seat_underside_z'] + seat.z
    # radial clearance: lid skirt (below the flange) vs furnace inner rim wall
    skirt_r = max(math.hypot(v.x, v.y) for v in lv if v.z < under - 0.002)
    wall_r = min(math.hypot(v.x, v.y) for v in fv if seat.z - 0.01 < v.z < rim['top_z'] - 0.002 and math.hypot(v.x, v.y) < 0.26)
    # vertical clearance: flange underside vs rim top
    flange_z = min(v.z for v in lv if math.hypot(v.x, v.y) > rim['inner_r'] + 0.01)
    res = dict(state=state, lid=lkey, seat=list(seat), triangleOverlaps=overlaps(fur, lid),
               skirtRadius=round(skirt_r, 4), rimInnerRadius=round(wall_r, 4), radialClearance=round(wall_r - skirt_r, 4),
               flangeUndersideZ=round(flange_z, 4), rimTopZ=rim['top_z'], verticalClearance=round(flange_z - rim['top_z'], 4))
    res['pass'] = res['triangleOverlaps'] == 0 and res['radialClearance'] > 0 and res['verticalClearance'] >= 0
    Q.gpu(bpy.context.scene, 64); Q.studio('stylized')
    Q.camera_fit(fur + lid, 30, 16, margin=1.12); Q.render(OUT / f'closed_{state}.png', 1024, 96)
    Q.camera_fit(fur + lid, 90, 2, lens=120, margin=0.42, target=(0.2, 0, rim['top_z'])); Q.render(OUT / f'seam_{state}.png', 1024, 96)
    if state == 'cold':
        for o in lid:   # open: lid set down on the floor to the furnace's right, leaning slightly
            o.location = Vector((0.78, -0.05, 0.0)); o.rotation_euler = (0, math.radians(-4), math.radians(25))
        Q.camera_fit(fur + lid, 24, 18, margin=1.3, target=(0.36, 0.0, 0.40)); Q.render(OUT / 'open_cold.png', 1024, 96)
    return res


report = [run('cold'), run('heating')]
(EX / 'fit_B01_B02.json').write_text(json.dumps(report, indent=1), encoding='utf-8')
for r in report:
    print('FIT', json.dumps(r))
