"""Golden-light presentation renders of tea-terraces-b (render only: the exported models are imported, never changed).

  blender --background --factory-startup --python art/source/tea-terraces-b/beauty_views.py -- --assets [ID ...]   one hero per asset
  blender --background --factory-startup --python art/source/tea-terraces-b/beauty_views.py -- --diorama          the three-row diorama

--assets writes art/previews/tea-terraces-b/<ID>/<ID>_golden.png (all assets when no ID is given).
--diorama stacks three rows of different wall height on a plinth: TE01_StraightB_H12 (rise 1.2), TE01_StraightA (rise 1.0, with a TE03_Stair up into it)
and TE01_StraightB_H08 (rise 0.8), each row 4 m deeper; TE02 hedge (Hedge / HedgeShort / HedgeEnd) on every ridge, TE03_Path on the lower two rows, TE03_Stepping on the top row.
Writes art/previews/tea-terraces-b/diorama/*.png and blend/diorama_v001.blend. The plinth is presentation only.
"""
import bpy, sys, json, math, random
from pathlib import Path
from mathutils import Vector, Matrix
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import golden
from te_terrace import field_profile
from te_hedge_layout import runs as hedge_runs, hedge_run
from showcase_tea_terraces_b import import_lod0, version
ART = HERE.parents[1]
KIT = 'tea-terraces-b'
PREV = ART / 'previews' / KIT
ALL = ['TE01_StraightA', 'TE01_StraightB', 'TE01_InnerBend', 'TE01_OuterBend', 'TE01_End', 'TE01_Broken', 'TE01_GentleOuter', 'TE01_GentleInner',
       'TE01_StraightB_H08', 'TE01_StraightB_H12', 'TE01_End_H08', 'TE01_End_H12', 'TE02_Round', 'TE02_Wide', 'TE02_Tall', 'TE03_Stair', 'TE03_Path', 'TE03_Stepping',
       'TE02_Hedge', 'TE02_HedgeShort', 'TE02_HedgeEnd']


def info(aid):
    return json.loads((ART / 'exports' / KIT / aid / 'model_info.json').read_text(encoding='utf-8'))


def place(src, coll, aid, pos, yaw_deg=0., mirror=False):
    M = Matrix.Translation(pos) @ Matrix.Rotation(math.radians(yaw_deg), 4, 'Z') @ Matrix.Diagonal((-1. if mirror else 1., 1., 1., 1.))
    for o in src[aid]:
        d = o.copy(); d.matrix_world = M @ o.matrix_world; coll.objects.link(d)


def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def hero(aid):
    scene = fresh(); src = import_lod0({aid})
    coll = bpy.data.collections.new('Hero'); scene.collection.children.link(coll); place(src, coll, aid, (0, 0, 0))
    i = info(aid); lo, hi = Vector(i['bounds_min_m']), Vector(i['bounds_max_m']); c = (lo + hi) / 2; size = (hi - lo).length
    golden.ground_plane(scene, z=-.002, size=400, col=(.12, .1, .07))
    golden.setup(scene, sun_azimuth_deg=-45, sun_elev_deg=18, fog=0., samples=72, res=(1600, 1000))
    small = aid.startswith(('TE02', 'TE03'))
    dist = max(size * (1.15 if small else .95), 2.4)
    eye = c + Vector((-.62, -.95, .55 if small else .62)).normalized() * dist
    out = PREV / aid / f'{aid}_golden.png'; out.parent.mkdir(parents=True, exist_ok=True)
    golden.shot(scene, out, tuple(eye), tuple(c + Vector((0, 0, -.05 * size))), lens=40 if small else 35)


def diorama():
    scene = fresh()
    ids = {'TE01_StraightB_H12', 'TE01_StraightA', 'TE01_StraightB_H08', 'TE02_Hedge', 'TE02_HedgeShort', 'TE02_HedgeEnd', 'TE03_Stair', 'TE03_Path', 'TE03_Stepping'}
    src = import_lod0(ids)
    coll = bpy.data.collections.new('Diorama'); scene.collection.children.link(coll)
    rows = [('TE01_StraightB_H12', 1.2), ('TE01_StraightA', 1.0), ('TE01_StraightB_H08', .8)]
    z = 0.; R = random.Random(77); layout = []
    def add(aid, pos, yaw=0.):
        place(src, coll, aid, pos, yaw); layout.append({'id': aid, 'fbx': f'{aid}/{aid}_{version(aid)}.fbx', 'position_m': [round(v, 4) for v in pos], 'rotation_z_deg': round(yaw, 2)})
    stair_x = 1.6
    for k, (aid, rise) in enumerate(rows):
        y0 = 4. * k; add(aid, (0., y0, z)); soil = z + rise; front = y0 - 2.
        if k == 1: add('TE03_Stair', (stair_x, front, z))
        if k < 2:
            for lx in (-2., 2.):
                if aid == 'TE01_StraightA' and lx < 0: continue   # StraightA's drain groove crosses the left half
                add('TE03_Path', (lx, front + 1.15, soil))
        else:
            add('TE03_Stepping', (-.5, front + 1.15, soil))
        # TE02 hedge along the ridge (the row 1 stair lands on row 0, so row 0's hedge breaks around it); the cut-away ends get a HedgeEnd
        samples = [(t * .1 - 4., front + 2.95, not (k == 0 and abs(t * .1 - 4 - stair_x) < 1.4)) for t in range(81)]
        for run in hedge_runs(samples):
            for hid, hx, hy, hyaw in hedge_run(run)[0]: add(hid, (hx, hy, soil + field_profile(2.95)), hyaw)
        z = soil
    # earth fill under the upper rows (on a hillside the slope is there; in a cut-away it has to be added): x -4..4, from the plinth up to the row's base
    me_ = bpy.data.materials.new('Diorama_Earth'); me_.use_nodes = True; be = me_.node_tree.nodes['Principled BSDF']
    be.inputs['Base Color'].default_value = (.075, .05, .03, 1); be.inputs['Roughness'].default_value = .95
    zb = 0.
    for k, (aid, rise) in enumerate(rows):
        if k > 0:
            bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 4. * k, zb / 2)); fill = bpy.context.object; fill.name = f'Presentation_EarthFill_row{k}'
            fill.scale = (8., 4., zb); fill.data.materials.append(me_)
        zb += rise
    # plinth: dark lacquered wood under the front strip and the cut sides
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 3.5, -.21)); pl = bpy.context.object; pl.name = 'Presentation_Plinth'; pl.scale = (8.7, 13.7, .42)
    bv = pl.modifiers.new('Bevel', 'BEVEL'); bv.width = .04; bv.segments = 3
    m = bpy.data.materials.new('Plinth'); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = (.045, .028, .018, 1); b.inputs['Roughness'].default_value = .35
    pl.data.materials.append(m)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -2.65, .03)); st = bpy.context.object; st.name = 'Presentation_FrontStrip'; st.scale = (8., 1.3, .06)
    ms = bpy.data.materials.new('FrontStrip'); ms.use_nodes = True; bs = ms.node_tree.nodes['Principled BSDF']; bs.inputs['Base Color'].default_value = (.13, .1, .065, 1); bs.inputs['Roughness'].default_value = .95
    st.data.materials.append(ms)
    golden.ground_plane(scene, z=-.42, size=400, col=(.16, .15, .14))
    golden.setup(scene, sun_azimuth_deg=-40, sun_elev_deg=20, fog=0., samples=128, res=(1920, 1200))
    out = PREV / 'diorama'; out.mkdir(parents=True, exist_ok=True)
    (ART / 'exports' / KIT / 'diorama').mkdir(parents=True, exist_ok=True)
    (ART / 'exports' / KIT / 'diorama' / 'diorama-layout.json').write_text(json.dumps({'name': 'tea-terraces-b diorama (presentation only)', 'units': 'meters',
        'rows': [{'id': a, 'rise_m': r} for a, r in rows], 'note': 'three wall heights stacked; the plinth and the front strip are presentation only', 'pieces': layout}, ensure_ascii=False, indent=1), encoding='utf-8')
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE / 'blend' / 'diorama_v001.blend'))
    golden.shot(scene, out / 'diorama_three_quarter.png', (-10.5, -11.5, 8.2), (0, 3.2, 1.4), lens=40)
    golden.shot(scene, out / 'diorama_front_low.png', (2.5, -12.5, 1.6), (0, 3.5, 1.7), lens=42)
    golden.shot(scene, out / 'diorama_side_section.png', (13.5, 1.0, 3.2), (0, 3.5, 1.5), lens=42)
    golden.shot(scene, out / 'diorama_top_three_quarter.png', (8.5, -7.5, 13.0), (0, 4.0, 1.5), lens=38)
    print('DIORAMA_DONE', out, flush=True)


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if '--diorama' in argv: diorama()
    if '--assets' in argv:
        ids = [a for a in argv[argv.index('--assets') + 1:] if not a.startswith('--')] or ALL
        for aid in ids: hero(aid)
