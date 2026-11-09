"""FP kit 40 m sample: the exported pieces chained socket to socket (each piece's Socket_Path_W on the previous piece's
Socket_Path_E, turned 180 deg), LOD0 with the baked materials, plus 1.75 m stand-in figures; a walk check along three lines on the
chained collision meshes. Reads each piece's saved .blend; writes previews and one report, changes no model file.

blender --background --factory-startup --python art/source/forest-paths-b/assemble_40m.py -- <repo>/art
Writes art/previews/forest-paths-b/FP_Assembly_40m/*.png and art/exports/forest-paths-b/FP_Assembly_40m/assembly_walk.json
"""
import bpy, bmesh, json, math, sys
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

ART = Path(sys.argv[sys.argv.index('--') + 1:][0])
KIT = 'forest-paths-b'
# flat pieces first, the climb last, so nothing stands in the air without the terrain under it
SEQ = ['FP01_PathStraight', 'FP02_PathCurve30_L', 'FP04_PathRootCrossing', 'FP02_PathCurve60_R', 'FP01_PathStraight',
       'FP02_PathCurve30_R', 'FP03_PathSlope', 'FP05_PathLogSteps']
OUT = ART / 'previews' / KIT / 'FP_Assembly_40m'; REP = ART / 'exports' / KIT / 'FP_Assembly_40m'
OUT.mkdir(parents=True, exist_ok=True); REP.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

loaded = {}


def load(aid):
    """Append the piece's root, LOD0 meshes, collision and sockets; point its images at the exported textures."""
    path = ART / 'source' / KIT / 'blend' / f'{aid}_v001.blend'
    want = [aid, f'{aid}_LOD0', f'{aid}_Ground_LOD0', f'{aid}_Detail_Small_LOD0', f'{aid}_Collision', 'Socket_Path_W', 'Socket_Path_E']
    imgs_before = set(bpy.data.images)
    with bpy.data.libraries.load(str(path)) as (src, dst):
        dst.objects = [n for n in src.objects if n in want]
    objs = {}
    for o in dst.objects:
        if o is None: continue
        scene.collection.objects.link(o); base = o.name
        for n in want:
            if base == n or base.startswith(n + '.'): objs[n] = o
    for img in set(bpy.data.images) - imgs_before:
        if img.source == 'FILE' and img.filepath:
            p = ART / 'exports' / KIT / aid / 'Textures' / Path(bpy.path.abspath(img.filepath)).name
            if p.exists(): img.filepath = str(p); img.reload()
    bpy.context.view_layer.update()
    return objs


def instance(aid):
    if aid not in loaded:
        loaded[aid] = load(aid); return loaded[aid]
    src = loaded[aid]; root = src[aid].copy(); scene.collection.objects.link(root); out = {aid: root}
    for n, o in src.items():
        if n == aid: continue
        c = o.copy(); scene.collection.objects.link(c); c.parent = root; c.matrix_parent_inverse = o.matrix_parent_inverse.copy(); out[n] = c
    return out


pieces = []; A = Matrix.Identity(4)
for k, aid in enumerate(SEQ):
    objs = instance(aid); root = objs[aid]
    root.matrix_world = Matrix.Identity(4); bpy.context.view_layer.update()
    sw, se = objs['Socket_Path_W'].matrix_world.copy(), objs['Socket_Path_E'].matrix_world.copy()
    if k: A = pieces[-1]['A'] @ pieces[-1]['se'] @ Matrix.Rotation(math.pi, 4, 'Z') @ sw.inverted()
    root.matrix_world = A
    pieces.append(dict(aid=aid, objs=objs, A=A.copy(), sw=sw, se=se))
bpy.context.view_layer.update()
report_col_tris = {}
for p in pieces:
    p['col'] = p['objs'][f"{p['aid']}_Collision"]; p['col'].hide_render = True
    report_col_tris[p['aid']] = sum(len(f.vertices) - 2 for f in p['col'].data.polygons)
    for n in ('Socket_Path_W', 'Socket_Path_E'): p['objs'][n].hide_render = True


def world_bvh(objs):
    V, F = [], []
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        e = o.evaluated_get(dg); me = e.to_mesh(); mw = o.matrix_world; b = len(V)
        V += [mw @ v.co for v in me.vertices]; F += [[b + i for i in p.vertices] for p in me.polygons]; e.to_mesh_clear()
    return BVHTree.FromPolygons(V, F)


col_t = world_bvh([p['col'] for p in pieces])
vis_t = world_bvh([o for p in pieces for n, o in p['objs'].items() if o.type == 'MESH' and n.endswith('_LOD0') and 'Detail' not in n])


RETRIED = []


def down(t, x, y):
    """Height under (x, y). A ray exactly on a triangle edge can slip through: a miss is cast again 0.3 mm to each side and
    counted (RETRIED), so a real hole still reports None."""
    h = t.ray_cast(Vector((x, y, 50.)), Vector((0, 0, -1)))
    if h[0] is not None: return h[0].z
    for dx, dy in ((.0003, 0), (-.0003, 0), (0, .0003), (0, -.0003)):
        h = t.ray_cast(Vector((x + dx, y + dy, 50.)), Vector((0, 0, -1)))
        if h[0] is not None: RETRIED.append((round(x, 3), round(y, 3))); return h[0].z
    return None


def centre_line(p, t0):
    """The piece's walk line at across t0, from its Ground_LOD0 grid ('pth' = along, across, height), in world space."""
    g = p['objs'][f"{p['aid']}_Ground_LOD0"]; me = g.data; pth = me.attributes['pth'].data; mw = g.matrix_world
    L = max(pth[v.index].vector[0] for v in me.vertices if pth[v.index].vector[2] > 0)
    pts = sorted((pth[v.index].vector[0], mw @ v.co) for v in me.vertices
                 if abs(pth[v.index].vector[1] - t0) < 1e-3 and pth[v.index].vector[2] > 0 and -1e-4 <= pth[v.index].vector[0] <= L + 1e-4)
    return [q for _, q in pts]


report = {'sequence': SEQ, 'lines': {}, 'joints': [], 'collision_triangles': report_col_tris}
steep = math.tan(math.radians(40))
for t0 in (-.24, 0., .24):
    poly = []; owner = []
    for k, p in enumerate(pieces):
        cl = centre_line(p, t0)
        if poly and (cl[0] - poly[-1]).length < .01: cl = cl[1:]
        poly += cl; owner += [k] * len(cl)
    samples = []; dist = 0.
    for a, b, k in zip(poly, poly[1:], owner[1:]):
        seg = Vector((b.x - a.x, b.y - a.y, 0)); n = max(1, int(seg.length / .025))
        for i in range(n):
            q = a + (b - a) * (i / n)
            samples.append((dist + seg.length * i / n, k, down(col_t, q.x, q.y), down(vis_t, q.x, q.y), q.copy()))
        dist += seg.length
    zc = [s[2] for s in samples]; missing = sum(1 for z in zc if z is None)
    steps, run, worst_slope = [], 0., 0.
    for (d0, k0, a, _, _), (d1, k1, b, _, _) in zip(samples, samples[1:]):
        if a is None or b is None: continue
        if abs(b - a) / max(d1 - d0, 1e-4) > steep: run += b - a
        else:
            if abs(run) > 1e-4: steps.append((round(abs(run), 3), SEQ[k0]))
            run = 0.
    for i in range(len(samples) - 8):
        seg = samples[i:i + 9]
        if any(s[2] is None for s in seg): continue
        if any(abs(b[2] - a[2]) / max(b[0] - a[0], 1e-4) > steep for a, b in zip(seg, seg[1:])): continue
        worst_slope = max(worst_slope, math.degrees(math.atan2(abs(seg[-1][2] - seg[0][2]), seg[-1][0] - seg[0][0])))
    off = [s[3] - s[2] for s in samples if s[2] is not None and s[3] is not None]
    over = {}
    for s_ in samples:
        if s_[2] is not None and s_[3] is not None and s_[3] - s_[2] > .06: over[SEQ[s_[1]]] = over.get(SEQ[s_[1]], 0) + 1
    low = {}                                    # lowest visible-minus-collision per piece (visible below the collider)
    for s_ in samples:
        if s_[2] is not None and s_[3] is not None:
            low[SEQ[s_[1]]] = round(min(low.get(SEQ[s_[1]], 9.), s_[3] - s_[2]), 3)
    miss_at = [[SEQ[s_[1]], round(s_[0], 3), [round(c, 3) for c in s_[4]]] for s_ in samples if s_[2] is None]
    report['lines'][str(t0)] = {'length_m': round(dist, 2), 'samples': len(samples), 'rays_missing_collision': missing,
                                'rise_m': round(zc[-1] - zc[0], 3), 'largest_step_m': max([s[0] for s in steps] or [0.]),
                                'steps': steps, 'slope_max_deg': round(worst_slope, 2),
                                'visible_minus_collision_m': [round(min(off), 3), round(max(off), 3)],
                                'samples_visible_over_6cm': sum(1 for v in off if v > .06), 'visible_over_6cm_by_piece': over,
                                'lowest_visible_minus_collision_by_piece': low,
                                'rays_missing_at': miss_at}
for k in range(1, len(pieces)):                # collision height either side of each joint, on the centre line
    J = (pieces[k]['A'] @ pieces[k]['sw']).translation
    fwd = ((pieces[k]['A'] @ pieces[k]['sw']).to_3x3() @ Vector((0, -1, 0))).normalized()   # into piece k
    za, zb = down(col_t, *(J - fwd * .02).xy), down(col_t, *(J + fwd * .02).xy)
    prevE = (pieces[k - 1]['A'] @ pieces[k - 1]['se']).translation
    report['joints'].append({'between': [SEQ[k - 1], SEQ[k]], 'socket_gap_mm': round((J - prevE).length * 1000, 3),
                             'collision_step_mm': round(abs(zb - za) * 1000, 2) if za is not None and zb is not None else None})

# ------------------------------------------------------------------ renders
def mat(name, rgb, rough=.8):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Roughness'].default_value = rough; return m


grey = mat('Figure', (.55, .55, .56), .7)


def figure(x, y, z, face):
    bm = bmesh.new()
    def cone(r1, r2, z0, z1, dx=0.):
        bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=r1, radius2=r2, depth=z1 - z0, matrix=Matrix.Translation((dx, 0, (z0 + z1) / 2)))
    for s in (-1, 1): cone(.075, .065, 0, .86, s * .095); cone(.05, .042, .8, 1.42, s * .25)
    cone(.19, .17, .82, 1.46); cone(.05, .05, 1.44, 1.53)
    bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=.11, matrix=Matrix.Translation((0, 0, 1.64)))
    me = bpy.data.meshes.new('Figure'); bm.to_mesh(me); bm.free(); me.materials.append(grey)
    o = bpy.data.objects.new('Figure_1.75m', me); scene.collection.objects.link(o)
    o.matrix_world = Matrix.Translation((x, y, z)) @ Matrix.Rotation(face, 4, 'Z'); return o


def on_path(k, frac, t=0.):
    """A point on piece k's centre line at frac of its length, standing on the collision; and the heading there."""
    cl = centre_line(pieces[k], 0.); i = min(len(cl) - 2, int(frac * (len(cl) - 1)))
    d = (cl[i + 1] - cl[i]); side = Vector((-d.y, d.x, 0)).normalized()     # t across, to the left of the walking direction
    q = cl[i] + side * t; z = down(col_t, q.x, q.y)
    return Vector((q.x, q.y, z)), math.atan2(d.y, d.x)


figs = []
FIGS = ((0, .5, .4), (2, .78, -.4), (3, .55, .4), (6, .6, -.4), (7, .55, .4))     # on the tread edges, clear of the eye-level views
for k, frac, t in FIGS:
    q, hd = on_path(k, frac, t); figs.append(figure(q.x, q.y, q.z, hd - math.pi / 2))
report['figures'] = [[SEQ[k], frac, t] for k, frac, t in FIGS]

scene.render.engine = 'CYCLES'; scene.cycles.samples = 64; scene.cycles.use_denoising = True
scene.view_settings.view_transform = 'AgX'
world = bpy.data.worlds.new('w'); scene.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.32, .34, .38, 1); world.node_tree.nodes['Background'].inputs[1].default_value = 1.3
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); scene.collection.objects.link(sun)
sun.data.energy = 4.; sun.rotation_euler = (math.radians(48), 0, math.radians(30))
floor_me = bpy.data.meshes.new('Floor'); bmf = bmesh.new(); bmesh.ops.create_grid(bmf, x_segments=1, y_segments=1, size=80); bmf.to_mesh(floor_me); bmf.free()
floor_me.materials.append(mat('Floor', (.16, .16, .17), .95)); floor = bpy.data.objects.new('Floor', floor_me); scene.collection.objects.link(floor)
floor.location.z = -.002
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); scene.collection.objects.link(cam); scene.camera = cam
pts = [o.matrix_world @ Vector(c) for p in pieces for o in p['objs'].values() if o.type == 'MESH' for c in o.bound_box]
lo = Vector([min(v[i] for v in pts) for i in range(3)]); hi = Vector([max(v[i] for v in pts) for i in range(3)]); mid = (lo + hi) / 2
floor.location.x, floor.location.y = mid.x, mid.y
# a piece that starts above the floor (after the climb) stands on a plain grey block: a stand-in for the terrain, not a kit piece
plinth = mat('Terrain_Standin', (.24, .24, .25), .95)
for p in pieces:
    zA = p['A'].translation.z
    if zA < .01: continue
    g = p['objs'][f"{p['aid']}_Ground_LOD0"]; bb = [Vector(c) for c in g.bound_box]
    x0, x1 = min(v.x for v in bb), max(v.x for v in bb); y0, y1 = min(v.y for v in bb), max(v.y for v in bb)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1., matrix=Matrix.Translation(((x0 + x1) / 2, (y0 + y1) / 2, -zA / 2 - .001)) @
                          Matrix.Diagonal(Vector((x1 - x0, y1 - y0, zA - .002, 1))))
    me = bpy.data.meshes.new('Terrain_Standin'); bm.to_mesh(me); bm.free(); me.materials.append(plinth)
    o = bpy.data.objects.new('Terrain_Standin', me); scene.collection.objects.link(o); o.matrix_world = g.matrix_world.copy()
report['terrain_standin'] = 'a plain grey block under every piece that starts above z = 0 (after FP03): stands in for the terrain in the renders only'


def shot(name, eye, target, lens=35, res=(1800, 1100), ortho=None):
    scene.render.resolution_x, scene.render.resolution_y = res
    cam.data.type = 'ORTHO' if ortho else 'PERSP'
    if ortho: cam.data.ortho_scale = ortho
    cam.data.lens = lens; cam.data.clip_end = 400; cam.location = Vector(eye)
    cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(OUT / f'{name}.png'); bpy.ops.render.render(write_still=True); print('ASSEMBLY_VIEW', name, flush=True)


ext = max(hi.x - lo.x, hi.y - lo.y)
shot('overview_three_quarter', mid + Vector((.45, -.75, .6)).normalized() * 120, mid, res=(1800, 1300), ortho=ext * 1.02)
shot('overview_top', mid + Vector((0, 0, 60)), mid, ortho=ext * 1.08, res=(1800, 1800))
for name, k, frac, back, up in (('eye_root_crossing', 2, .2, 3.2, 1.6), ('eye_curve60', 3, .15, 3., 1.6), ('eye_slope_and_steps', 6, .05, 3.5, 1.6)):
    q, hd = on_path(k, frac); d = Vector((math.cos(hd), math.sin(hd), 0))
    shot(name, q - d * back + Vector((0, 0, up)) + Vector((-d.y, d.x, 0)) * .25, q + d * 3.5 + Vector((0, 0, .4)), lens=30)
report['rays_hit_after_0_3mm_shift'] = RETRIED; report['length_m'] = report['lines']['0.0']['length_m']; report['rise_m'] = report['lines']['0.0']['rise_m']
report['note'] = ('walk lines at across -0.24 / 0 / 0.24 m, every 2.5 cm, rays down onto the chained collision meshes (LOD0 visible surface '
                  'without Detail_Small for the visible check); a run of rises steeper than 40 deg is one step; slope over 0.2 m windows without a step')
(REP / 'assembly_walk.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print('ASSEMBLY_DONE', report['length_m'], report['rise_m'], [(t, v['largest_step_m'], v['slope_max_deg'], v['rays_missing_collision']) for t, v in report['lines'].items()], flush=True)
