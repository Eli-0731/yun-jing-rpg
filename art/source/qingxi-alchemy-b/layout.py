"""Workshop layout from the exported GLBs: player-view panorama, approach view and a top-down layout sketch.

  blender -b --python-exit-code 1 --python layout.py

Writes art/previews/qingxi-alchemy-b/layout/*.png, art/source/qingxi-alchemy-b/blend/QA_Workshop_Layout_v001.blend
and tools/qingxi-alchemy-b/data/layout.json (station positions + approach points shared with the demo).
The shed, bench, floor, scale figure and flue elbow are layout placeholders (grey/flat), not deliverable assets.
"""
import bpy, sys, json, math
from pathlib import Path
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
import qa_lib as Q

EX, OUT = Q.EXPORTS, Q.PREVIEWS / 'layout'
DEMO = Q.REPO / 'tools/qingxi-alchemy-b/data/layout.json'

# id, file key, position (x, y, z), yaw degrees (0 = front faces -Y, toward the entrance), station / role
PLACE = [
    ('B01', 'B01_BronzeFurnace/v001/B01_BronzeFurnace_heating', (0.0, 0.60, 0.0), 0, 'refine'),
    ('B02', 'B02_FurnaceLid/v001/B02_FurnaceLid', None, 0, 'refine'),
    ('B12', 'B12_WorkshopChimney/v001/B12_WorkshopChimney', (-1.15, 0.935, 0.0), 0, 'exhaust'),
    ('B07', 'B07_WoodenFuelBox/v001/B07_WoodenFuelBox', (-0.78, -0.05, 0.0), 0, 'fuel'),
    ('B06', 'B06_CeramicWaterJar/v001/B06_CeramicWaterJar', (-1.55, -0.55, 0.0), 20, 'water'),
    ('B09', 'B09_ClothFilterFrame/v001/B09_ClothFilterFrame', (0.66, 1.22, 0.0), 0, 'filter'),
    ('B05', 'B05_HerbDrawerCabinet/v001/B05_HerbDrawerCabinet', (1.50, 1.24, 0.0), 0, 'identify'),
    ('B11', 'B11_BambooRecipeStand/v001/B11_BambooRecipeStand', (1.50, 1.22, 0.88), 0, 'recipe'),
    ('B04', 'B04_BambooSortingTrays/v001/B04_BambooSortingTrays', (2.05, -0.25, 0.0), -90, 'sort'),
    ('B03', 'B03_StoneMortar/v001/B03_StoneMortar', (0.62, -0.46, 0.42), 0, 'process'),
    ('B10', 'B10_WaxSealedBottle/v001/B10_WaxSealedBottle_filled', (1.02, -0.42, 0.42), 0, 'collect'),
    ('B10', 'B10_WaxSealedBottle/v001/B10_WaxSealedBottle_filled', (1.10, -0.50, 0.42), 20, 'collect'),
    ('B10', 'B10_WaxSealedBottle/v001/B10_WaxSealedBottle_empty', (0.93, -0.53, 0.42), -15, 'collect'),
    ('B08', 'B08_VentilatedDryingBasket/v001/B08_VentilatedDryingBasket', (1.45, -0.46, 0.42), 0, 'dry'),
]
# B05 and B11 share a footprint (the stand sits on the cabinet): split their approach points left/right
APPROACH_SHIFT = {'identify': (0.30, 0.0), 'recipe': (-0.35, 0.0), 'exhaust': (-0.18, 0.0)}
STATION_LABEL = {'refine': '煉製', 'exhaust': '排煙', 'fuel': '添柴', 'water': '取水', 'filter': '濾渣', 'identify': '辨材',
                 'recipe': '配方', 'sort': '分料', 'process': '研磨', 'collect': '領取成品', 'dry': '晾藥'}


def load(path, loc, yaw):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    new = [o for o in bpy.data.objects if o not in before]
    roots = [o for o in new if o.parent is None or o.parent not in new]
    for o in roots:
        o.location = Vector(loc) + o.location; o.rotation_euler.z += math.radians(yaw)
    return [o for o in new if o.type == 'MESH']


def flat(name, rgb, rough=0.85):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Roughness'].default_value = rough; return m


def placeholders(fi):
    Q.ACTIVE['coll'] = Q.coll('20_Layout_Placeholders')
    stone, wood, roof, fig = flat('PH_Floor', (0.30, 0.29, 0.26)), flat('PH_Wood', (0.16, 0.11, 0.07)), flat('PH_Roof', (0.12, 0.20, 0.18)), flat('PH_Figure', (0.26, 0.28, 0.30), 0.6)
    P = [Q.box('PH_Floor', (4.6, 3.6, 0.06), (0.30, 0.30, -0.03), stone, bevel=0)]
    for x in (-1.95, 2.55):
        for y in (-1.45, 1.75):
            P.append(Q.box(f'PH_Post{x}{y}', (0.14, 0.14, 2.7), (x, y, 1.35), wood, bevel=0.01))
    P.append(Q.box('PH_BackWall', (4.5, 0.06, 1.25), (0.30, 1.75, 0.625), wood, bevel=0))
    rf = Q.box('PH_Roof', (5.0, 3.9, 0.06), (0.30, 0.15, 2.82), roof, bevel=0); rf.rotation_euler = (math.radians(-9), 0, 0); rf.visible_shadow = False; P.append(rf)  # open-sided shed: roof casts no studio shadow
    P.append(Q.box('PH_BenchTop', (1.30, 0.50, 0.05), (1.02, -0.46, 0.395), wood, bevel=0.006))
    for x in (0.45, 1.59):
        P.append(Q.box(f'PH_BenchLeg{x}', (0.08, 0.42, 0.37), (x, -0.46, 0.185), wood, bevel=0.006))
    # 1.70 m scale figure (capsule body + head), standing at the entrance looking in
    P.append(Q.cyl('PH_Figure_Body', 0.17, 1.30, (-0.20, -1.60, 0.70), fig, segs=24, bevel=0.15, bseg=4))
    P.append(Q.lathe('PH_Figure_Head', [(0, -0.115), (0.08, -0.095), (0.11, -0.03), (0.11, 0.03), (0.08, 0.095), (0, 0.115)], fig, segs=24))
    P[-1].location = (-0.20, -1.60, 1.585)
    # flue elbow: B01 flue outlet -> B12 inlet (+X face); layout only, the core team replaces it with a scene pipe
    soot = flat('PH_Flue', (0.05, 0.045, 0.04), 0.55)
    a = Vector(fi['B01']['sockets']['flue_outlet']) + Vector((0, 0.60, 0)); b = Vector(fi['B12']['sockets']['flue_inlet']) + Vector((-1.15, 0.935, 0))
    pts = [a - Vector((0, 0, 0.02)), Vector((a.x, a.y, b.z - 0.10)), Vector((a.x - 0.10, a.y, b.z)), Vector((b.x + 0.02, b.y, b.z))]
    P.append(Q.tube('PH_FlueElbow', pts, 0.050, soot, segs=16, res=10))
    return P, (a, b)


def main():
    Q.reset()
    fi = {}
    for aid, key, *_ in PLACE:
        mi = EX / f'{key}_model_info.json'
        fi.setdefault(aid, json.loads(mi.read_text(encoding='utf-8')))
    Q.ACTIVE['coll'] = Q.coll('10_Kit_GLB')
    objs, stations, instances = [], [], []
    seat = Vector(fi['B01']['sockets']['lid_seat'])
    for aid, key, loc, yaw, role in PLACE:
        if loc is None:
            loc = tuple(Vector(PLACE[0][2]) + seat)
        objs += load(EX / f'{key}.glb', loc, yaw)
        instances.append(dict(id=aid, glb=f'{key}.glb', role=role, position=[round(c, 4) for c in loc], yawDeg=yaw))
        if role not in [s['role'] for s in stations]:
            fwd = Vector((math.sin(math.radians(yaw)), -math.cos(math.radians(yaw)), 0))
            ap = Vector(loc) + fwd * 0.75 + Vector((*APPROACH_SHIFT.get(role, (0, 0)), 0)); ap.z = 0
            stations.append(dict(id=aid, role=role, label=STATION_LABEL[role], position=[round(c, 3) for c in loc], yawDeg=yaw,
                                 approach=[round(ap.x, 3), round(ap.y, 3), 0.0], interactRadius=0.9))
    ph, flue = placeholders(fi)
    bpy.context.view_layer.update()
    s = Q.gpu(bpy.context.scene, 96) or bpy.context.scene
    Q.studio('stylized', ground=True); bpy.data.objects['QA_Ground'].location.z = -0.08
    cam = bpy.data.objects.new('QA_Cam', bpy.data.cameras.new('QA_Cam')); s.collection.objects.link(cam); s.camera = cam
    cam.data.sensor_width = 36; cam.data.clip_start = 0.02

    def shoot(name, loc, look, lens, rx, ry, samples=128):
        cam.location = loc; cam.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = lens
        s.render.resolution_x, s.render.resolution_y = rx, ry; s.cycles.samples = samples
        s.render.filepath = str(OUT / f'{name}.png'); OUT.mkdir(parents=True, exist_ok=True); bpy.ops.render.render(write_still=True)

    # third-person player view: camera behind and above the 1.70 m figure, everything operable in frame
    shoot('player_view_panorama', (0.75, -4.6, 2.75), (0.35, 0.30, 0.45), 20, 2048, 1024)
    # approach view: standing at the furnace approach point, eye height 1.58 m
    shoot('approach_furnace', (0.35, -0.55, 1.58), (0.0, 0.62, 0.55), 24, 1600, 1000)
    # top-down layout sketch (orthographic); labels are drawn later by layout_sketch.py
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 5.4
    for o in [o for o in ph if o.name.startswith('PH_Roof')]:
        o.hide_render = True
    shoot('layout_top_raw', (0.30, 0.20, 8.0), (0.30, 0.2001, 0.0), 50, 1600, 1600, 64)
    blend = Q.HERE / 'blend' / 'QA_Workshop_Layout_v001.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), compress=True, relative_remap=True)
    data = dict(note='Layout reference for the Batch-2 demo; positions in metres, Blender axes (x right, y into the workshop, z up). '
                     'Unity axis mapping depends on the FBX import settings (exported with forward -Z, up Y): verify on import. Placeholders (shed, bench, flue elbow, figure) are not deliverables.',
                topOrtho=dict(center=[0.30, 0.20], scale=5.4, px=1600), entrance=[-0.20, -1.60, 0.0], figureHeight=1.70,
                flueElbow=dict(start=[round(c, 3) for c in flue[0]], end=[round(c, 3) for c in flue[1]]), stations=stations, instances=instances)
    DEMO.parent.mkdir(parents=True, exist_ok=True); DEMO.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding='utf-8')
    # reach check: approach points stay on the floor and keep 0.45 m from every other station's base
    bad = [st['role'] for st in stations if not (-2.0 < st['approach'][0] < 2.6 and -1.5 < st['approach'][1] < 2.1)
           or any(o is not st and o['position'][2] == 0 and math.dist(st['approach'][:2], o['position'][:2]) < 0.45 for o in stations)
           or any(o is not st and math.dist(st['approach'][:2], o['approach'][:2]) < 0.30 for o in stations)]
    data['reachCheck'] = dict(blocked=bad, pass_=not bad)
    DEMO.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding='utf-8')
    print('LAYOUT', len(objs), 'kit meshes', len(stations), 'stations', 'blocked', bad)


main()
