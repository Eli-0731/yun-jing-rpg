"""40 x 40 m assembly sample of the tea-terraces-b kit: writes farm-assembly.json, then (optionally) renders it in Blender from the exported FBXs.

  blender --background --factory-startup --python art/source/tea-terraces-b/assembly_tea_terraces_b.py              json only
  blender --background --factory-startup --python art/source/tea-terraces-b/assembly_tea_terraces_b.py -- --render  json, assembly .blend and previews

Layout (Blender axes, metres; Unity = (x, z, y)):
  nine terrace rows climbing +Y, row k: front edge y = -18 + 4k, soil z = k + 1, piece origin z = k.
  each row: mirrored TE01_End (x -16), three straights (x -8, 0, 8), TE01_End (x 16) -> 40 m wide, connectors at x = -12, -4, 4, 12.
  a TE03_Stair up every wall (alternating sides), TE03_Path runs along the tread just behind the coping, TE02 bushes in a row behind the path.
  row 0 stands on a flat 2 m strip (y -20 .. -18) that is not part of the kit; stepping stones lead along it to the first stair.
The bends are not in this sample (a bend turns the row through 90 degrees and needs a hillside spur); they are joined to straights in the Unity check instead.
"""
import bpy, sys, json, math, random
from pathlib import Path
HERE = Path(__file__).resolve().parent
ART = HERE.parents[1]
KIT = 'tea-terraces-b'; VER = 'v001'
OUT = ART / 'exports' / KIT / 'assembly'
ROWS = 9
ROW_PIECES = [('TE01_StraightA', 'TE01_StraightB', 'TE01_StraightA'), ('TE01_StraightB', 'TE01_Broken', 'TE01_StraightA'), ('TE01_StraightA', 'TE01_StraightB', 'TE01_StraightB'),
              ('TE01_Broken', 'TE01_StraightA', 'TE01_StraightB'), ('TE01_StraightB', 'TE01_StraightA', 'TE01_StraightA'), ('TE01_StraightA', 'TE01_StraightB', 'TE01_Broken'),
              ('TE01_StraightB', 'TE01_StraightB', 'TE01_StraightA'), ('TE01_StraightA', 'TE01_Broken', 'TE01_StraightB'), ('TE01_StraightB', 'TE01_StraightA', 'TE01_StraightB')]
STAIR_X = [3.5, -6.5, 5.5, -1.5, 9.5, -9.5, 1.5, -5.5, 6.5]      # stair up into row k (row 0 has none)
DRAIN_S, BREACH = 2.9, (4.7, 7.1)
STEP_X = (-10., -2.)
PATH_D, BUSH_D = 1.15, 2.95



sys.path.insert(0, str(HERE))
from te_terrace import field_profile, RIDGE_D, RIDGE_HALF, RIDGE_H, DITCH_D, DITCH_HALF, DITCH_H   # one profile for every script


def version(aid):
    f = ART / 'exports' / KIT / aid / 'model_info.json'
    return json.loads(f.read_text(encoding='utf-8')).get('version', VER) if f.exists() else VER


def front(k): return -18. + 4 * k


def layout():
    R = random.Random(5050); P = []
    def add(aid, x, y, z, rot=0., mirror=False, row=None, note=None):
        e = {'id': aid, 'fbx': f'{aid}/{aid}_{version(aid)}.fbx', 'position_m': [round(x, 4), round(y, 4), round(z, 4)], 'rotation_z_deg': round(rot, 2), 'mirror_x': mirror}
        if row is not None: e['row'] = row
        if note: e['note'] = note
        P.append(e)
    bad = {}     # x ranges per row where a path must not lie (drain groove, breach)
    for k in range(ROWS):
        yc = front(k) + 2.
        add('TE01_End', -16., yc, k, mirror=True, row=k, note='mirrored left end (scale x -1)')
        for c, aid in zip((-8., 0., 8.), ROW_PIECES[k]):
            add(aid, c, yc, k, row=k)
            if aid == 'TE01_Broken': bad.setdefault(k, []).append((c - 4 + BREACH[0] - .3, c - 4 + BREACH[1] + .3))
            if aid == 'TE01_StraightA': bad.setdefault(k, []).append((c - 4 + DRAIN_S - .3, c - 4 + DRAIN_S + .3))
        add('TE01_End', 16., yc, k, row=k)
    for xc in STEP_X: bad.setdefault(0, []).append((xc - .5, xc + .5))     # row 0: stepping stones instead of two path lengths
    stairs = {}
    for k in range(ROWS):
        x = STAIR_X[k]; stairs[k] = x
        add('TE03_Stair', x, front(k), k, row=k, note=(f'from row {k - 1} soil up to row {k} soil' if k else 'from the front strip up to row 0 soil'))
    for k in range(ROWS):
        z = k + 1.; yp = front(k) + PATH_D
        for xc in (-10., -6., -2., 2., 6., 10.):
            if any(a < xc + 2 and xc - 2 < b for a, b in bad.get(k, [])): continue
            # the stair coming down from row k+1 lands on this tread from d = 1.6 back: the path passes in front of it
            add('TE03_Path', xc, yp, z, row=k)
        # bushes: 1.5 m apart behind the path, not where the next stair comes down or on a breach
        x = -11.25
        while x <= 11.3:
            up = stairs.get(k + 1)
            ok = (up is None or abs(x - up) > 1.3) and not any(a - .3 < x < b + .3 for a, b in bad.get(k, []) if b - a > 1.)
            if ok:
                d = BUSH_D + R.uniform(-.06, .06)
                add(R.choice(('TE02_Round', 'TE02_Round', 'TE02_Wide', 'TE02_Tall')), x, front(k) + d, z + field_profile(d), rot=R.uniform(0, 360), row=k)
            x += R.uniform(1.0, 1.1)     # crowns overlap a little: the row reads as one clipped hedge
    # row 0: two runs of stepping stones take the place of two path lengths
    for xc in STEP_X:
        add('TE03_Stepping', xc, front(0) + PATH_D, 1., row=0)
    return P


def write():
    P = layout(); OUT.mkdir(parents=True, exist_ok=True)
    counts = {}
    for e in P: counts[e['id']] = counts.get(e['id'], 0) + 1
    doc = {'name': 'tea-terraces-b 40 x 40 m assembly sample', 'version': VER, 'units': 'meters',
           'axes': 'Blender: x right, y back (+Y uphill), z up. Unity with bakeAxisConversion: (x, z, y); rotation_z_deg becomes a rotation about Unity -Y; mirror_x is scale x = -1',
           'extent_m': {'x': [-20, 20], 'y': [-20, 18], 'z': [0, ROWS + 1]}, 'ground_note': 'y -20 .. -18 at z 0 is a flat strip that is not part of the kit (placeholder plane)',
           'rows': ROWS, 'row_rule': 'row k: front edge y = -18 + 4k, piece origin z = k, soil z = k + 1', 'connectors_x': [-12, -4, 4, 12],
           'counts': counts, 'not_included': 'TE01_InnerBend / TE01_OuterBend (joined to straights in the Unity check); no official placement in the game scene', 'pieces': P}
    path = OUT / 'farm-assembly.json'; path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding='utf-8')
    print('ASSEMBLY_JSON', path, len(P), counts, flush=True)
    return doc


def render(doc):
    """Import each FBX once (LOD0 only, collision hidden), link-duplicate it per placement, and render an aerial and two walker's-eye views."""
    sys.path.insert(0, str(HERE)); import ti_pipeline as pl
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    lib = bpy.data.collections.new('Library'); scene.collection.children.link(lib); lib.hide_render = True; lib.hide_viewport = True
    src = {}
    for aid in sorted({e['id'] for e in doc['pieces']}):
        before = set(bpy.data.objects)
        bpy.ops.import_scene.fbx(filepath=str(ART / 'exports' / KIT / aid / f'{aid}_{version(aid)}.fbx'))
        new = [o for o in bpy.data.objects if o not in before]
        keep = [o for o in new if o.type == 'MESH' and o.name.split('.')[0].endswith('_LOD0')]
        for o in new:
            for c in list(o.users_collection): c.objects.unlink(o)
        for o in keep:
            mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw; lib.objects.link(o)
        src[aid] = keep
    placed = bpy.data.collections.new('Assembly'); scene.collection.children.link(placed)
    from mathutils import Matrix
    for e in doc['pieces']:
        M = Matrix.Translation(e['position_m']) @ Matrix.Rotation(math.radians(e['rotation_z_deg']), 4, 'Z') @ Matrix.Diagonal((-1. if e['mirror_x'] else 1., 1., 1., 1.))
        for o in src[e['id']]:
            d = o.copy(); d.matrix_world = M @ o.matrix_world; placed.objects.link(d)
    # flat strip in front and a ground sheet under everything, not part of the kit
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -19.0, 0)); g = bpy.context.object; g.scale = (44, 2.0, 1); g.name = 'Placeholder_Strip'
    m = bpy.data.materials.new('Placeholder_Ground'); m.use_nodes = True; m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.12, .09, .055, 1); g.data.materials.append(m)
    for c in list(g.users_collection): c.objects.unlink(g)
    placed.objects.link(g)
    objs = list(placed.objects)
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE / 'blend' / f'assembly_{VER}.blend'))
    prev = ART / 'previews' / KIT / 'assembly'; prev.mkdir(parents=True, exist_ok=True)
    pl.persp_shot(objs, prev / 'assembly_aerial.png', direction=(.55, -1., .9), samples=48, lens=35)
    pl.persp_shot(objs, prev / 'assembly_side.png', direction=(1., -.35, .35), samples=48, lens=40)
    # walker's eye: 1.6 m up on row 2's path, looking along the row and up the slope
    cam = scene.camera
    for name, eye, tgt in (('assembly_walk_row2', (-11.5, front(2) + PATH_D, 3 + 1.6), (6., front(2) + 2.6, 2.9)),
                           ('assembly_walk_stairs', (3.0, front(1) + 1.0, 2 + 1.6), (-2., front(4) + 1., 4.6))):
        from mathutils import Vector
        cam.data.lens = 28; cam.location = eye; cam.rotation_euler = (Vector(tgt) - Vector(eye)).to_track_quat('-Z', 'Y').to_euler()
        scene.cycles.samples = 64; scene.render.filepath = str(prev / f'{name}.png'); bpy.ops.render.render(write_still=True)
    print('ASSEMBLY_RENDERED', prev, flush=True)


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    doc = write()
    if '--render' in argv: render(doc)
