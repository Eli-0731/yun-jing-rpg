"""tea-terraces-b showcase: eight terrace rows following the contour of a hillside, in the project's morning light.

This is a presentation layout, not an official placement and not the verification sample (that is assembly_tea_terraces_b.py).
Every row is the same chain, so the rows stack by a plain translation of (0, +4, +1) and never open a gap:
  [mirrored End] [straights...] [GentleOuter +30 deg] [StraightB on the 30 deg run] [GentleInner -30 deg] [straights...] [End]
The left and right ends are staggered row by row; two rows carry a breach; one stair per row on a 0 deg straight;
TE03 paths on the straights (d = 1.15 m); TE02 hedge (TE02_Hedge / HedgeShort / HedgeEnd, an addition pending owner confirmation) along the planting ridge (d = 2.95 m), bends included,
broken off at each stair, breach and End slope.

  blender --background --factory-startup --python art/source/tea-terraces-b/showcase_tea_terraces_b.py              json only
  blender --background --factory-startup --python art/source/tea-terraces-b/showcase_tea_terraces_b.py -- --render  json + golden-light renders
Writes art/exports/tea-terraces-b/showcase/showcase-layout.json and art/previews/tea-terraces-b/showcase/*.png.
"""
import bpy, sys, json, math, random
from pathlib import Path
from mathutils import Vector, Matrix
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ART = HERE.parents[1]
KIT = 'tea-terraces-b'
OUT = ART / 'exports' / KIT / 'showcase'
PREV = ART / 'previews' / KIT / 'showcase'

R_G = 8.0 / (math.pi / 6)
DEPTH = 4.0
PATH_D, BUSH_D = 1.15, 2.95
ROWS = 8
N_LEFT = [1, 2, 1, 2, 2, 1, 2, 1]
N_RIGHT = [2, 1, 2, 2, 1, 2, 1, 1]
BROKEN = {2: ('right', 0), 5: ('left', 0)}          # row: which straight run, which piece in it
STAIR = {1: ('left', 0, 1.5), 2: ('right', 0, -1.5), 3: ('left', 0, -2.5), 4: ('right', 0, 2.5), 5: ('right', 0, 1.5), 6: ('right', 0, -2.0), 7: ('left', 0, 2.0)}



sys.path.insert(0, str(HERE))
from te_hedge_layout import runs as hedge_runs, hedge_run
from te_terrace import field_profile, RIDGE_D, RIDGE_HALF, RIDGE_H, DITCH_D, DITCH_HALF, DITCH_H   # one profile for every script


def version(aid):
    return json.loads((ART / 'exports' / KIT / aid / 'model_info.json').read_text(encoding='utf-8')).get('version', 'v001')


def rot(v, yaw):
    c, s = math.cos(yaw), math.sin(yaw); return (c * v[0] - s * v[1], s * v[0] + c * v[1])


# local (s, d) -> (x, y) of each kind, origin as exported (a straight's centre; bends enter like a straight's left end)
def local(kind, s, d):
    if kind == 'outer':
        a = -math.pi / 2 + s / R_G; r = R_G - d; return (-4. + r * math.cos(a), -2. + R_G + r * math.sin(a))
    if kind == 'inner':
        a = math.pi / 2 - s / R_G; r = R_G + d; return (-4. + r * math.cos(a), -2. - R_G + r * math.sin(a))
    return (s - 4., -2. + d)


KIND = {'TE01_GentleOuter': 'outer', 'TE01_GentleInner': 'inner'}
TURN = {'outer': math.radians(30), 'inner': -math.radians(30)}


def row_chain(k):
    """Piece list of one row, origin row 0 coordinates (row k is the same chain at (0, 4k, k))."""
    R = random.Random(900 + k)
    left = [R.choice(('TE01_StraightA', 'TE01_StraightB')) for _ in range(N_LEFT[k])]
    right = [R.choice(('TE01_StraightA', 'TE01_StraightB')) for _ in range(N_RIGHT[k])]
    if k in BROKEN:
        side, i = BROKEN[k]; (left if side == 'left' else right)[i] = 'TE01_Broken'
    out = []
    # the bend group sits at a fixed place in every row, so the rows stack
    origin, yaw = (0., 0.), 0.
    def put(aid, origin, yaw, run=None, idx=None):
        out.append({'id': aid, 'origin': origin, 'yaw': yaw, 'run': run, 'idx': idx})
    # leftwards from the outer bend: straights, then a mirrored End
    for i, aid in enumerate(left):
        put(aid, (-8. * (i + 1), 0.), 0., 'left', i)
    put('TE01_End', (-8. * (len(left) + 1), 0.), 0., 'left_end')
    # the bend group
    put('TE01_GentleOuter', origin, yaw, 'bend')
    def next_origin(kind, origin, yaw):
        ex = local(kind, 8., 0.); wx = rot(ex, yaw); corner = (origin[0] + wx[0], origin[1] + wx[1])
        yaw2 = yaw + TURN.get(kind, 0.); o = rot((4., 2.), yaw2)
        return (corner[0] + o[0], corner[1] + o[1]), yaw2
    o2, y2 = next_origin('outer', origin, yaw)
    put('TE01_StraightB', o2, y2, 'turned')
    o3, y3 = next_origin('straight', o2, y2)
    put('TE01_GentleInner', o3, y3, 'bend')
    o4, y4 = next_origin('inner', o3, y3)
    for i, aid in enumerate(right):
        put(aid, o4, y4, 'right', i); o4, y4 = next_origin('straight', o4, y4)
    put('TE01_End', o4, y4, 'right_end')
    return out


HEDGE_JOINTS = []   # joints between two open hedge ends: x, y, z (ridge top), yaw, row


def layout():
    P = []; Rb = random.Random(4242); HEDGE_JOINTS.clear()
    def add(aid, x, y, z, yaw_deg=0., mirror=False, row=None, note=None):
        e = {'id': aid, 'fbx': f'{aid}/{aid}_{version(aid)}.fbx', 'position_m': [round(x, 4), round(y, 4), round(z, 4)], 'rotation_z_deg': round(yaw_deg, 3), 'mirror_x': mirror}
        if row is not None: e['row'] = row
        if note: e['note'] = note
        P.append(e)
    chains = {k: row_chain(k) for k in range(ROWS)}
    for k in range(ROWS):
        dy, z = 4. * k, float(k)
        stair_xy = []
        if k + 1 in STAIR:
            side, i, xs = STAIR[k + 1]
            pc = [c for c in chains[k + 1] if c['run'] == side and c['idx'] == i][0]
            stair_xy.append(rot((xs, 0.), pc['yaw'])[0] + pc['origin'][0])
        ridge = {}
        for c in chains[k]:
            aid, (ox, oy), yaw = c['id'], c['origin'], c['yaw']
            if c['run'] == 'left_end':
                # mirrored End: its connector is on its local +X side, so the origin sits 8 m left of the next piece
                add(aid, ox, oy + dy, z, 0., True, k, 'mirrored left end (scale x -1)')
            else:
                add(aid, ox, oy + dy, z, math.degrees(yaw), False, k)
            kind = KIND.get(aid, 'straight'); mirror = c['run'] == 'left_end'
            # paths on 0-degree straights: two 4 m pieces, skipping the drain groove of StraightA and the breach of Broken
            if kind == 'straight' and aid in ('TE01_StraightA', 'TE01_StraightB', 'TE01_Broken') and abs(yaw) < 1e-6:
                for lx in (-2., 2.):
                    if aid == 'TE01_StraightA' and lx < 0: continue
                    if aid == 'TE01_Broken' and lx > 0: continue
                    add('TE03_Path', ox + lx, oy + dy - 2. + PATH_D, z + 1., 0., False, k)
            # ridge samples for the hedge (laid per row below, once the whole chain is known)
            for s in [t * .1 for t in range(81)]:
                ok = True
                if aid == 'TE01_Broken' and 4.3 < s < 7.5: ok = False
                if aid == 'TE01_End' and s > 5.4: ok = False
                lx, ly = local(kind, s, BUSH_D)
                if mirror: lx = -lx
                wx, wy = rot((lx, ly), yaw); x, y = ox + wx, oy + wy
                if any(abs(x - sx) < 1.4 for sx in stair_xy) and abs(yaw) < 1e-6: ok = False
                ridge.setdefault(id(c), []).append((x, y + dy, ok))
        # TE02 hedge along the planting ridge, left to right: [left End] [left straights, right to left] [bend group, right run, right End]
        ch = chains[k]
        order = [c for c in ch if c['run'] == 'left_end'] + [c for c in ch if c['run'] == 'left'][::-1] + [c for c in ch if c['run'] not in ('left', 'left_end')]
        samples = []
        for c in order:
            pts = ridge[id(c)]
            if c['run'] == 'left_end': pts = pts[::-1]
            samples += pts if not samples else pts[1:]
        zr = z + 1. + field_profile(BUSH_D)
        for run in hedge_runs(samples):
            pl_, jt = hedge_run(run)
            for hid, hx, hy, hyaw in pl_: add(hid, hx, hy, zr, hyaw, False, k)
            HEDGE_JOINTS.extend([round(jx, 4), round(jy, 4), round(zr, 4), round(jyaw, 3), k] for jx, jy, jyaw in jt)
        if k in STAIR:
            side, i, xs = STAIR[k]
            pc = [c for c in chains[k] if c['run'] == side and c['idx'] == i][0]
            add('TE03_Stair', pc['origin'][0] + xs, pc['origin'][1] + dy - 2., z, 0., False, k, f'from row {k - 1} soil up to row {k} soil')
    return P


def walkthrough_route():
    """First-person route for the Unity walkthrough: row 2's path line from its left end to the stair into row 3, up the stair,
    then row 3's path line (d = 1.15 m) to the right through the outer bend, the 30 degree run and the inner bend, to the right end.
    Waypoints in Blender metres; z is the soil height the walker should stand on."""
    chain3 = row_chain(3)
    side, i, xs = STAIR[3]
    pc = [c for c in chain3 if c['run'] == side and c['idx'] == i][0]
    sx = pc['origin'][0] + xs
    pts = [[-16.5, 8. - 2. + PATH_D, 3.], [sx, 8. - 2. + PATH_D, 3.], [sx, 12. - 2. + PATH_D, 4.]]
    order = sorted([c for c in chain3 if c['run'] == 'left'], key=lambda c: c['origin'][0]) + [c for c in chain3 if c['run'] in ('bend', 'turned', 'right')]
    for c in order:
        kind = KIND.get(c['id'], 'straight')
        for s in [x * .5 for x in range(17)]:
            lx, ly = local(kind, s, PATH_D); wx, wy = rot((lx, ly), c['yaw']); x, y = c['origin'][0] + wx, c['origin'][1] + wy + 12.
            if c['run'] == 'left' and x < sx + .5: continue
            if math.hypot(x - pts[-1][0], y - pts[-1][1]) > .25: pts.append([round(x, 4), round(y, 4), 4.])
    end = [c for c in chain3 if c['run'] == 'right_end'][0]
    for s in (1., 2., 3.):
        wx, wy = rot((s - 4., -2. + PATH_D), end['yaw']); pts.append([round(end['origin'][0] + wx, 4), round(end['origin'][1] + wy + 12., 4), 4.])
    return pts


def front_line():
    """Row 0's front edge (x, y) left to right, every 0.5 m: the placeholder hill follows it, so it stays under the rows after they turn uphill."""
    ch = row_chain(0)
    order = sorted([c for c in ch if c['run'] in ('left', 'left_end')], key=lambda c: c['origin'][0]) + [c for c in ch if c['run'] in ('bend', 'turned', 'right', 'right_end')]
    pts = []
    for c in order:
        kind = KIND.get(c['id'], 'straight')
        for k in range(17):
            lx, ly = local(kind, k * .5, 0.); wx, wy = rot((lx, ly), c['yaw']); q = (round(c['origin'][0] + wx, 4), round(c['origin'][1] + wy, 4))
            if not pts or q[0] > pts[-1][0] + 1e-3: pts.append(q)
    return pts


def hill_z(x, y, line):
    """Placeholder hillside: 1 m up per 4 m back from the row-0 front line, 0.3 m under the row-0 wall base at the front."""
    if x <= line[0][0]: yf = line[0][1]
    elif x >= line[-1][0]: yf = line[-1][1]
    else:
        i = next(i for i in range(1, len(line)) if line[i][0] >= x); (xa, ya), (xb, yb) = line[i - 1], line[i]
        yf = ya + (yb - ya) * (x - xa) / (xb - xa)
    return (y - yf - 2.) / 4. - .3


def write():
    P = layout(); OUT.mkdir(parents=True, exist_ok=True)
    counts = {}
    for e in P: counts[e['id']] = counts.get(e['id'], 0) + 1
    doc = {'name': 'tea-terraces-b contour showcase (presentation only, not an official placement)', 'units': 'meters', 'rows': ROWS,
           'axes': 'Blender: x right, y uphill, z up. Unity with bakeAxisConversion: (x, z, y); rotation_z_deg becomes a rotation about Unity -Y; mirror_x is scale x = -1',
           'row_rule': 'every row is the same chain translated by (0, 4k, k); where a row turns 30 degrees the upper wall foot overlaps the lower tread by up to 0.54 m (no gap)',
           'hill_note': 'placeholder hillside, not part of the kit: z = (y - y_front(x) - 2) / 4 - 0.3, with y_front(x) interpolated along hill_front_line_flat_xy (row 0 front edge)',
           'hill_front_line_flat_xy': [v for q in front_line() for v in q],
           'counts': counts, 'walkthrough_route_flat_m': [v for p in walkthrough_route() for v in p], 'walkthrough_note': 'x, y, soil z triples (Blender metres) for the Unity first-person walkthrough', 'hedge_joints_flat': [v for j in HEDGE_JOINTS for v in j], 'hedge_joints_note': 'x, y, ridge-top z, yaw (deg, hedge +X), row for every joint between two open hedge ends', 'pieces': P}
    path = OUT / 'showcase-layout.json'; path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding='utf-8')
    print('SHOWCASE_JSON', path, len(P), counts, flush=True)
    return doc


def import_lod0(ids):
    lib = bpy.data.collections.new('Library'); bpy.context.scene.collection.children.link(lib); lib.hide_render = True; lib.hide_viewport = True
    src = {}
    for aid in sorted(ids):
        before = set(bpy.data.objects)
        bpy.ops.import_scene.fbx(filepath=str(ART / 'exports' / KIT / aid / f'{aid}_{version(aid)}.fbx'))
        new = [o for o in bpy.data.objects if o not in before]
        keep = [o for o in new if o.type == 'MESH' and o.name.split('.')[0].endswith('_LOD0')]
        for o in new:
            for c in list(o.users_collection): c.objects.unlink(o)
        for o in keep:
            mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw; lib.objects.link(o)
        src[aid] = keep
    return src


def hill(scene, x0, x1, y0, y1):
    """Placeholder hillside following the row-0 front line (hill_z), grass-brown, with a soft noise mix."""
    import bmesh
    me = bpy.data.meshes.new('Hill'); bm = bmesh.new(); line = front_line()
    nx, ny = 200, 120
    def v(i, j):
        x, y = x0 + (x1 - x0) * i / nx, y0 + (y1 - y0) * j / ny; return bm.verts.new((x, y, min(hill_z(x, y, line), 12.)))   # levels off 3 m above the top row
    vs = [[v(i, j) for i in range(nx + 1)] for j in range(ny + 1)]
    for j in range(ny):
        for i in range(nx): bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new('Placeholder_Hill', me); scene.collection.objects.link(o)
    m = bpy.data.materials.new('Placeholder_Hill'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = .35; n.inputs['Detail'].default_value = 6
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].color = (.07, .085, .03, 1); r.color_ramp.elements[1].color = (.15, .13, .06, 1)
    r.color_ramp.elements[0].position = .4; r.color_ramp.elements[1].position = .62
    nt.links.new(n.outputs['Fac'], r.inputs[0]); nt.links.new(r.outputs[0], b.inputs['Base Color']); b.inputs['Roughness'].default_value = .95
    o.data.materials.append(m)
    return o


def render(doc):
    import golden
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    src = import_lod0({e['id'] for e in doc['pieces']})
    placed = bpy.data.collections.new('Showcase'); scene.collection.children.link(placed)
    xs, ys = [], []
    for e in doc['pieces']:
        M = Matrix.Translation(e['position_m']) @ Matrix.Rotation(math.radians(e['rotation_z_deg']), 4, 'Z') @ Matrix.Diagonal((-1. if e['mirror_x'] else 1., 1., 1., 1.))
        xs.append(e['position_m'][0]); ys.append(e['position_m'][1])
        for o in src[e['id']]:
            d = o.copy(); d.matrix_world = M @ o.matrix_world; placed.objects.link(d)
    hill(scene, min(xs) - 160, max(xs) + 160, -120, max(ys) + 260)
    golden.distant_hills(scene, centre=((min(xs) + max(xs)) / 2, max(ys), 0), radius=230, count=9, height=(45, 90))
    golden.setup(scene, sun_azimuth_deg=-50, sun_elev_deg=16, fog=.0012, strength=1.25, sky=.5, samples=128, fog_centre=((min(xs) + max(xs)) / 2, max(ys) / 2, 0.), fog_size=(600., 600., 110.))   # the box dims the sun too: ~180 m of 0.0018 = x0.72, hence strength 1.25
    blend = HERE / 'blend' / 'showcase_v001.blend'; bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    PREV.mkdir(parents=True, exist_ok=True)
    cx = (min(xs) + max(xs)) / 2
    golden.shot(scene, PREV / 'showcase_aerial.png', (cx - 30, -48, 34), (cx + 4, 12, 4), lens=32)
    golden.shot(scene, PREV / 'showcase_from_below.png', (cx + 18, -24, 2.2), (cx - 2, 14, 6), lens=28)
    # eye level on row 2's path, left straight, looking along the row into the bend
    golden.shot(scene, PREV / 'showcase_walk_row2.png', (-14., 8. - 2. + PATH_D, 3. + 1.6), (6., 8. + 2.6, 3.2), lens=24)
    golden.shot(scene, PREV / 'showcase_bend_close.png', (6., 4. * 3 - 6., 4.6), (4., 4. * 3 + 2.5, 4.), lens=28)
    print('SHOWCASE_RENDERED', PREV, flush=True)


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    doc = write()
    if '--render' in argv: render(doc)
