"""2026-11-07 pack, part 2: a 30 m zigzag of SG01-SG04 climbing from Dondon's SectGate.

  blender --background --factory-startup --python art/source/mountain-stairs-b/assembly_mountain_stairs_b.py -- [--render]

Writes art/exports/mountain-stairs-b/assembly-20261108/stair-assembly.json (every piece: id, version, position, rotation) and
assembly-checks.json (treads measured along the whole climb, rail seams). With --render it also saves
blend/assembly_mountain_stairs_b_v001.blend and the previews in art/previews/mountain-stairs-b/assembly-20261108/.

Layout (Blender axes, metres; Unity = (x, z, y)): SectGate at the origin facing -Y; the climb starts 3 m behind it.
19 flights of SG01 (1.6 m each, 30.4 m in all), an SG02 landing between flights, turning 90 deg each time:
north, west, north, east, north ... Each landing is turned so its lantern corner sits between the two edges no flight uses.
SG03: a sloped run on both kerbs of every flight; on every landing the two free edges get straight bays, a corner post at the
lantern corner, line posts at the edge middles and end posts at the corners next to the flights. SG04 stands on the landing at
14.4 m against the uphill side, its open front on the landing (that edge has no rail). G01 lanterns (qingxi-day12-c) on the lantern bases.
The ground is a placeholder heightfield that hugs the pieces; it is not part of the kit. None of this is an official placement.
"""
import bpy, sys, json, math
from pathlib import Path
from mathutils import Matrix, Vector
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ART = HERE.parents[1]; KIT = 'mountain-stairs-b'; VER = 'v001'
OUT = ART / 'exports' / KIT / 'assembly-20261108'
PREV = ART / 'previews' / KIT / 'assembly-20261108'
FLIGHTS = 19
RISE_FLIGHT, RUN_FLIGHT, LAND = 1.6, 3.2, 2.0
START = Vector((0., 3.0, 0.))
SHELTER_AT = 9                     # landing (1-based) carrying SG04: its top is at 9 x 1.6 = 14.4 m
HEAD = [Vector((0, 1, 0)), Vector((-1, 0, 0)), Vector((0, 1, 0)), Vector((1, 0, 0))]


def version(kit, aid):
    f = ART / 'exports' / kit / aid / 'model_info.json'
    return json.loads(f.read_text(encoding='utf-8')).get('version', VER) if f.exists() else VER


def yaw(h): return math.atan2(-h.x, h.y)          # rotation about Z that turns the model's +Y onto h


def layout():
    pieces = []; route = []
    def add(aid, pos, rot, kit=KIT, note=None, **kw):
        e = {'id': aid, 'kit': kit, 'version': version(kit, aid) if kit != 'incoming/dondon' else 'v001', 'position_m': [round(v, 4) for v in pos],
             'rotation_z_deg': round(math.degrees(rot) % 360, 3)}
        if note: e['note'] = note
        e.update(kw); pieces.append(e); return e
    add('SectGate', (0., 0., 0.), 0., kit='incoming/dondon', note='existing Dondon gate (art/incoming/dondon/SectGate/v001), not modified')
    p = START.copy(); route.append([0., -4., 0.]); route.append(list(p))
    landings = []
    for k in range(FLIGHTS):
        h = HEAD[k % 4]; r = yaw(h)
        add('SG01_StraightRun', p + h * (RUN_FLIGHT / 2), r, flight=k + 1, note=f'flight {k + 1}: bottom z {p.z:.1f} m')
        R3 = Matrix.Rotation(r, 3, 'Z')
        for s in (-1, 1):
            add('SG03_RailSloped', p + h * (RUN_FLIGHT / 2) + R3 @ Vector((s * 1.34, 0, 0)), r, flight=k + 1)
        top = p + h * RUN_FLIGHT + Vector((0, 0, RISE_FLIGHT))
        route.append(list(top))
        if k == FLIGHTS - 1:
            break
        h2 = HEAD[(k + 1) % 4]; c = top + h * LAND
        d = h - h2                                           # lantern corner direction (between the two free edges)
        rl = math.atan2(d.y, d.x) - math.atan2(1, 1)
        L = add('SG02_Landing', c - Vector((0, 0, .4)), rl, landing=k + 1)
        landings.append((k + 1, c, h, h2, rl))
        route.append(list(c)); p = c + h2 * LAND
    # top: a last landing so the climb ends on a level platform
    c = top + h * LAND
    d = h + Vector((h.y, -h.x, 0)); rl = math.atan2(d.y, d.x) - math.atan2(1, 1)
    add('SG02_Landing', c - Vector((0, 0, .4)), rl, landing=FLIGHTS, note='top landing (end of the sample)')
    route.append(list(c))
    landings.append((FLIGHTS, c, h, None, rl))
    # rails on the landings' free edges
    for n, c, h, h2, rl in landings:
        Rz = Matrix.Rotation(rl, 3, 'Z')
        free = [h] + ([-h2] if h2 is not None else [Vector((h.y, -h.x, 0)), Vector((-h.y, h.x, 0))])
        if n == SHELTER_AT: free = [e for e in free if (e - h).length > .1]        # the shelter's open front faces this edge
        for e in free:
            side = Vector((-e.y, e.x, 0))
            for t in (-.9, .9):
                add('SG03_RailStraight', c + e * 1.8 + side * t, math.atan2(side.y, side.x), landing=n,
                    note='straight bay along the landing edge')
            for t in (-1.8, 0., 1.8):
                q = c + e * 1.8 + side * t
                corner = abs(t) > 1
                other = (q - c - e * 1.8).normalized() if corner else None
                if corner and any((other - f).length < .1 for f in free):
                    kind = 'SG03_PostCorner'                       # between two railed edges
                elif corner: kind = 'SG03_PostEnd'
                else: kind = 'SG03_PostCorner'                     # line post (same model)
                add(kind, q, 0., landing=n)
        if True:
            add('G01', c + Rz @ Vector((1.32, 1.32, 0)) + Vector((0, 0, -.02 + .375)), rl, kit='qingxi-day12-c', landing=n, note='existing C lantern on the lotus base')
    # SG04 against the uphill side of landing SHELTER_AT
    n, c, h, h2, rl = landings[SHELTER_AT - 1]
    add('SG04_RestShelter', c + h * (LAND + 1.5), yaw(h), landing=n, note='open front on the landing edge (no rail there)')
    # drop duplicate posts (two edges share a corner)
    seen, out = set(), []
    for e in pieces:
        key = (e['id'], tuple(round(v, 2) for v in e['position_m'])) if e['id'].startswith('SG03_Post') else None
        if key and key in seen: continue
        if key: seen.add(key)
        out.append(e)
    return out, route


def write():
    pieces, route = layout()
    OUT.mkdir(parents=True, exist_ok=True)
    counts = {}
    for e in pieces: counts[e['id']] = counts.get(e['id'], 0) + 1
    doc = {'what': '2026-11-07 pack part 2: 30 m zigzag stair sample (SG01-SG04) from SectGate', 'units': 'metres, Blender axes (Unity = x, z, y)',
           'placement': 'position = model origin, rotation about +Z; not an official placement in the game scene',
           'top_z_m': round(FLIGHTS * RISE_FLIGHT, 2), 'counts': counts, 'route_m': [[round(v, 3) for v in q] for q in route], 'pieces': pieces}
    (OUT / 'stair-assembly.json').write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding='utf-8')
    print('ASSEMBLY_JSON', counts, flush=True)
    return doc


def fbx(e):
    if e['kit'] == 'incoming/dondon': return ART / 'incoming' / 'dondon' / e['id'] / 'v001' / f"{e['id']}_v001.fbx"
    if e['kit'] == 'qingxi-day12-c': return ART / 'exports' / 'qingxi-day12-c' / f"{e['id']}.fbx"
    return ART / 'exports' / e['kit'] / e['id'] / f"{e['id']}_{e['version']}.fbx"


def ground(pieces):
    """Placeholder hill: at every grid point the highest of (piece base - 0.75 x distance outside its footprint), never below 0, then cut
    down to (piece base + 1.5 x distance beyond 0.3 m outside its footprint) for every piece, so a flight two turns higher up cannot bury
    a lower one: the climb reads as a terraced cut in the slope. Placeholder only, not a terrain asset."""
    foot = {'SG01_StraightRun': (1.5, 1.6), 'SG02_Landing': (2., 2.), 'SG04_RestShelter': (2., 1.5)}
    boxes = []
    for e in pieces:
        if e['id'] not in foot: continue
        hx, hy = foot[e['id']]; a = math.radians(e['rotation_z_deg']); P = Vector(e['position_m'])
        boxes.append((P, a, hx, hy, P.z))
    def h(x, y):
        best, cap = 0., 1e9
        for P, a, hx, hy, z in boxes:
            dx, dy = x - P.x, y - P.y; lx = dx * math.cos(a) + dy * math.sin(a); ly = -dx * math.sin(a) + dy * math.cos(a)
            d = math.hypot(max(0., abs(lx) - hx), max(0., abs(ly) - hy))
            best = max(best, z - .02 - .75 * d); cap = min(cap, z - .02 + 1.5 * max(0., d - .3))
        return max(0., min(best, cap))
    xs = [-16 + .25 * i for i in range(113)]; ys = [-8 + .25 * j for j in range(393)]   # to y 90: past the top landing (y 74)
    verts = [(x, y, h(x, y)) for y in ys for x in xs]; nx = len(xs)
    faces = [(j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i) for j in range(len(ys) - 1) for i in range(nx - 1)]
    me = bpy.data.meshes.new('Placeholder_Hill'); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new('Placeholder_Hill', me)
    m = bpy.data.materials.new('Placeholder_Hill'); m.use_nodes = True
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.16, .15, .09, 1); m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .95
    me.materials.append(m)
    for f in me.polygons: f.use_smooth = True
    return o


def build_scene(doc):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    lib = bpy.data.collections.new('Library'); scene.collection.children.link(lib); lib.hide_render = True; lib.hide_viewport = True
    src = {}
    for e in doc['pieces']:
        if e['id'] in src: continue
        before = set(bpy.data.objects)
        bpy.ops.import_scene.fbx(filepath=str(fbx(e)))
        new = [o for o in bpy.data.objects if o not in before]
        keep = [o for o in new if o.type == 'MESH' and not o.name.split('.')[0].endswith(('_LOD1', '_LOD2')) and 'Collision' not in o.name]
        for o in new:
            for c in list(o.users_collection): c.objects.unlink(o)
        for o in keep:
            mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw; lib.objects.link(o)
        src[e['id']] = keep
    placed = bpy.data.collections.new('Assembly'); scene.collection.children.link(placed)
    inst = []
    for e in doc['pieces']:
        M = Matrix.Translation(e['position_m']) @ Matrix.Rotation(math.radians(e['rotation_z_deg']), 4, 'Z')
        objs = []
        for o in src[e['id']]:
            d = o.copy(); d.matrix_world = M @ o.matrix_world; placed.objects.link(d); objs.append(d)
        inst.append((e, objs))
    hill = ground(doc['pieces']); placed.objects.link(hill)
    bpy.context.view_layer.update()
    return scene, placed, inst, hill


def measure(inst):
    """Along the whole climb: every tread on the centre line of every flight measured by ray (rise, tread depth), each flight's
    clear width, each flight-landing joint; rail seams (bay end against post shaft) from the placed meshes."""
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    walk = [o for e, objs in inst if e['id'] in ('SG01_StraightRun', 'SG02_Landing') for o in objs if '_Detail_' not in o.name]
    trees = [BVHTree.FromPolygons([o.matrix_world @ v.co for v in o.data.vertices], [tuple(f.vertices) for f in o.data.polygons]) for o in walk]   # world space
    def cast(p, d):
        best = None
        for t in trees:
            hit = t.ray_cast(Vector(p), Vector(d))
            if hit[0] is not None and (best is None or hit[3] < best[3]): best = hit
        return best
    rises, depths, widths, joints, flights = [], [], [], [], []
    for e, objs in inst:
        if e['id'] != 'SG01_StraightRun': continue
        P = Vector(e['position_m']); a = math.radians(e['rotation_z_deg']); R3 = Matrix.Rotation(a, 3, 'Z')
        h = R3 @ Vector((0, 1, 0)); side = R3 @ Vector((1, 0, 0)); base = P - h * 1.6
        zs = []
        for k in range(11):          # k = 0: the ground / landing in front of the first riser; 1..10 the treads
            q = base + h * ((k - .5) * .32) if k else base - h * .3
            hit = cast(q + Vector((0, 0, 3.)), (0, 0, -1)); zs.append(hit[0].z if hit else (base.z if k == 0 else None))   # the first flight starts on open ground
        rs = [round(b - a_, 4) for a_, b in zip(zs, zs[1:])] if all(z is not None for z in zs) else None
        if rs: rises += rs
        # tread depths: horizontal rays along h just under each tread top find the next riser
        ys = []
        for k in range(1, 10):
            o = base - h * .5; o = Vector((o.x, o.y, P.z + k * .16 - .07))
            hit = cast(o, h); ys.append((hit[0] - base).dot(h) if hit else None)
        if all(v is not None for v in ys): depths += [round(b - a_, 4) for a_, b in zip(ys, ys[1:])]
        for k in (2, 6, 9):
            o = base + h * ((k - .5) * .32); o = Vector((o.x, o.y, P.z + k * .16 + .2))
            l = cast(o, -side); r = cast(o, side)
            if l and r: widths.append(round((r[0] - l[0]).length, 4))
        top = cast(base + h * 3.1 + Vector((0, 0, 3.)), (0, 0, -1)); land = cast(base + h * 3.4 + Vector((0, 0, 3.)), (0, 0, -1))
        if top and land: joints.append(round(land[0].z - top[0].z, 4))
        flights.append({'flight': e.get('flight'), 'bottom_z_m': round(base.z, 3), 'rises_m': rs})
    # rail seams: each straight bay against the shaft of the posts at its ends, measured on the placed meshes
    def extent(o, axis, zlo, zhi, M_inv):
        me = o.data; vals = []
        for v in me.vertices:
            w = M_inv @ (o.matrix_world @ v.co)
            if zlo <= w.z <= zhi: vals.append(w[axis])
        return (min(vals), max(vals)) if vals else None
    posts = [(Vector(e['position_m']), objs) for e, objs in inst if e['id'].startswith('SG03_Post')]
    seams = []
    for e, objs in inst:
        if e['id'] != 'SG03_RailStraight': continue
        P = Vector(e['position_m']); a = math.radians(e['rotation_z_deg']); M = Matrix.Translation(P) @ Matrix.Rotation(a, 4, 'Z'); Mi = M.inverted()
        main = [o for o in objs if '_Detail_' not in o.name][0]
        bx = extent(main, 0, .3, .85, Mi)          # local to the bay: z above its walking surface
        for end in (-1, 1):
            q = M @ Vector((end * .9, 0, 0)); post = min(posts, key=lambda t: (t[0].xy - q.xy).length)
            if (post[0].xy - q.xy).length > .01: seams.append({'bay': e['position_m'], 'end': end, 'post': None}); continue
            pm = [o for o in post[1] if '_Detail_' not in o.name][0]
            px = extent(pm, 0, .3, .85, Mi)
            gap = (px[0] - bx[1]) if end > 0 else (bx[0] - px[1])
            seams.append({'bay_m': [round(v, 2) for v in e['position_m']], 'end': end, 'gap_mm': round(gap * 1000, 2)})
    gaps = [s['gap_mm'] for s in seams if 'gap_mm' in s]
    res = {
        'rises': {'count': len(rises), 'min_m': min(rises), 'max_m': max(rises), 'rule': 'rise 0.15-0.18 m, all equal within 8 mm'},
        'tread_depths': {'count': len(depths), 'min_m': min(depths), 'max_m': max(depths), 'rule': 'tread 0.28-0.32 m'},
        'clear_widths': {'count': len(widths), 'min_m': min(widths), 'max_m': max(widths)},
        'flight_top_to_landing_step_m': {'count': len(joints), 'max_abs_m': max(abs(j) for j in joints)},
        'rail_seams': {'count': len(gaps), 'max_gap_mm': max(gaps), 'unmatched_ends': sum(1 for s in seams if 'gap_mm' not in s),
                       'note': 'gap = post shaft face minus bay end along the bay; negative = the bay runs into the post (closed)'},
        'flights': flights}
    res['pass'] = {'rises_equal_in_range': .15 <= res['rises']['min_m'] and res['rises']['max_m'] <= .18 and res['rises']['max_m'] - res['rises']['min_m'] <= .008,
                   'treads_equal_in_range': .28 <= res['tread_depths']['min_m'] and res['tread_depths']['max_m'] <= .325 and res['tread_depths']['max_m'] - res['tread_depths']['min_m'] <= .01,
                   'widths_equal': res['clear_widths']['max_m'] - res['clear_widths']['min_m'] <= .03,
                   'landings_flush': res['flight_top_to_landing_step_m']['max_abs_m'] <= .006,
                   'rail_seams_at_most_2mm': res['rail_seams']['max_gap_mm'] <= 2. and res['rail_seams']['unmatched_ends'] == 0}
    (OUT / 'assembly-checks.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
    print('ASSEMBLY_CHECKS', res['pass'], res['rises']['min_m'], res['rises']['max_m'], res['tread_depths'], res['clear_widths'], res['rail_seams']['max_gap_mm'], flush=True)
    return res


def figure(name, feet, face=0.):
    """A plain 1.75 m stand-in (body, head) like the ruler sheets."""
    import bmesh
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=.17, radius2=.2, depth=1.42, matrix=Matrix.Translation((0, 0, .71)))
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=.11, matrix=Matrix.Translation((0, 0, 1.64)))
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); o.matrix_world = Matrix.Translation(feet) @ Matrix.Rotation(face, 4, 'Z')
    m = bpy.data.materials.get('Figure') or bpy.data.materials.new('Figure'); m.use_nodes = True
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.75, .2, .12, 1); me.materials.append(m)
    return o


def render(doc, scene, placed, inst):
    import ti_pipeline as pl
    PREV.mkdir(parents=True, exist_ok=True)
    route = [Vector(q) for q in doc['route_m']]
    for i, q in enumerate((route[1], route[len(route) // 2], route[-1])):
        placed.objects.link(figure(f'Figure_{i}', q))
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE / 'blend' / f'assembly_mountain_stairs_b_{VER}.blend'))
    objs = [o for o in placed.objects if o.name != 'Placeholder_Hill']       # frame the climb, not the whole placeholder slope
    hill = [o for o in placed.objects if o.name == 'Placeholder_Hill']; only = pl.show_only
    pl.show_only = lambda keep: only(list(keep) + hill)                      # still drawn, just not used for the framing
    pl.persp_shot(objs, PREV / 'assembly_aerial.png', direction=(1., -.8, .75), samples=48, lens=35)
    pl.persp_shot(objs, PREV / 'assembly_side.png', direction=(1., 0., .18), samples=48, lens=35)
    cam = scene.camera; cam.data.type = 'PERSP'
    shots = [('assembly_gate', route[0] + Vector((2.5, -6., 1.6)), route[2] + Vector((0, 0, 1.))),
             ('assembly_walk_mid', route[len(route) // 2 - 2] + Vector((0, 0, 1.6)), route[len(route) // 2] + Vector((0, 0, 1.2))),
             ('assembly_shelter', None, None),
             ('assembly_top_down_the_climb', route[-1] + Vector((0, 0, 1.6)) + (route[-1] - route[-2]).normalized() * 1.5, route[-6])]
    sh = [e for e, _ in inst if e['id'] == 'SG04_RestShelter'][0]
    sp = Vector(sh['position_m']); a = math.radians(sh['rotation_z_deg']); fwd = Matrix.Rotation(a, 3, 'Z') @ Vector((0, -1, 0))
    shots[2] = ('assembly_shelter', sp + fwd * 6.5 + Matrix.Rotation(a, 3, 'Z') @ Vector((2.2, 0, 0)) + Vector((0, 0, 1.7)), sp + Vector((0, 0, 1.5)))
    for name, eye, tgt in shots:
        cam.data.lens = 26; cam.location = eye; cam.rotation_euler = (Vector(tgt) - Vector(eye)).to_track_quat('-Z', 'Y').to_euler()
        scene.cycles.samples = 64; scene.render.filepath = str(PREV / f'{name}.png'); bpy.ops.render.render(write_still=True)
    print('ASSEMBLY_RENDERED', PREV, flush=True)


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    doc = write()
    scene, placed, inst, hill = build_scene(doc)
    measure(inst)
    if '--render' in argv:
        render(doc, scene, placed, inst)
