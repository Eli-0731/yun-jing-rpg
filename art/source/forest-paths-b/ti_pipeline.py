"""Normalise -> join per group -> UV atlas -> bake -> LOD1/LOD2 -> baked materials -> FBX -> renders."""
from mathutils.bvhtree import BVHTree
import bpy, bmesh, math, json, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
from ti_core import S, write_grain_attributes
from ti_mats import MAT_INFO, set_emission

VIEWS = [('01_front', (0, -1, 0)), ('02_right', (1, 0, 0)), ('03_rear', (0, 1, 0)), ('04_left', (-1, 0, 0)),
         ('05_front_right', (1, -1, .45)), ('06_rear_right', (1, 1, .45)), ('07_rear_left', (-1, 1, .45)),
         ('08_front_left', (-1, -1, .45)), ('09_top', (0, 0, 1)), ('10_high_front', (0, -1, 1))]
EXPOSURE = -1.3   # same light rig as SectFacilities05, exposure lowered so material detail is not clipped
LOD_RULES = {0: (99, 1.0), 1: (2, .45), 2: (1, .2)}     # (drop parts with detail >= n, decimate ratio)

def eval_bounds(objs):
    dg = bpy.context.evaluated_depsgraph_get(); pts = []
    for o in objs:
        e = o.evaluated_get(dg)
        if o.type != 'MESH': continue
        me = e.to_mesh(); mw = o.matrix_world
        pts += [mw @ v.co for v in me.vertices]; e.to_mesh_clear()
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    return lo, hi

def normalise():
    """Move parts and sockets so the model sits on its bottom-centre origin."""
    bpy.context.view_layer.update()
    lo, hi = eval_bounds(S['parts'])
    shift = Matrix.Translation(-Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z)))
    for o in S['parts'] + list(S['sockets'].values()) + list(S['cut'].objects):
        if o.parent is None: o.matrix_world = shift @ o.matrix_world
    bpy.context.view_layer.update()
    write_grain_attributes()

def join_groups():
    """Evaluate every part (modifiers applied) and join per export group, at identity transform."""
    scene = bpy.context.scene
    S['lodcol'] = bpy.data.collections.new('02_Export_LODs'); scene.collection.children.link(S['lodcol'])
    dg = bpy.context.evaluated_depsgraph_get()
    groups = {}
    for o in S['parts']:
        if o.type != 'MESH': continue
        groups.setdefault(o['group'], []).append(o)
    out = {}
    for gname, parts in groups.items():
        temps = []
        for o in parts:
            e = o.evaluated_get(dg)
            me = bpy.data.meshes.new_from_object(e, preserve_all_data_layers=True, depsgraph=dg)
            if not me.uv_layers: me.uv_layers.new(name='UVMap')
            while len(me.uv_layers) > 1: me.uv_layers.remove(me.uv_layers[-1])
            me.uv_layers[0].name = 'UVMap'
            at = me.attributes.new('part_detail', 'INT', 'FACE'); at.data.foreach_set('value', [int(o['detail'])] * len(me.polygons))
            if 'uvw' not in me.attributes:      # village-houses-b: texel weight per face (hidden faces get less of the atlas)
                w = me.attributes.new('uvw', 'FLOAT', 'FACE'); w.data.foreach_set('value', [float(o.get('uvw', 1.))] * len(me.polygons))
            t = bpy.data.objects.new(o.name + '_eval', me); S['lodcol'].objects.link(t); t.matrix_world = o.matrix_world.copy()
            temps.append(t)
        bpy.ops.object.select_all(action='DESELECT')
        for t in temps: t.select_set(True)
        bpy.context.view_layer.objects.active = temps[0]
        bpy.ops.object.join()
        j = bpy.context.view_layer.objects.active
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        orient_faces(j.data)
        base = S['asset'] if gname == 'Main' else f"{S['asset']}_{gname}"
        j.name = base + '_LOD0'; j.data.name = j.name
        # merge duplicate material slots
        _dedupe_slots(j.data)
        out[gname] = j
    S['lod0'] = out
    return out

def orient_faces(me, flush=True):
    """Unity culls back faces. Drop zero-area faces (they get zero-area UVs), then each connected piece faces outward; an open piece (terrain skin, water) that lies mostly flat faces up."""
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges[:])
    dead = [f for f in bm.faces if f.calc_area() < 1e-10]
    if dead: bmesh.ops.delete(bm, geom=dead, context='FACES_ONLY')
    loose = [v for v in bm.verts if not v.link_faces]
    if loose: bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bm.faces.ensure_lookup_table(); seen = set()
    for f0 in bm.faces:
        if f0.index in seen: continue
        island, todo = [], [f0]; seen.add(f0.index)
        while todo:
            f = todo.pop(); island.append(f)
            for e in f.edges:
                for g in e.link_faces:
                    if g.index not in seen: seen.add(g.index); todo.append(g)
        bmesh.ops.recalc_face_normals(bm, faces=island)
        if any(e.is_boundary for f in island for e in f.edges):
            n = sum((f.normal * f.calc_area() for f in island), Vector())
            if n.z < 0 and abs(n.z) > .6 * n.length: bmesh.ops.reverse_faces(bm, faces=island)
        else:
            if _signed_volume(island) < 0: bmesh.ops.reverse_faces(bm, faces=island)
    bm.to_mesh(me); bm.free(); me.update()
    if flush:
        drop_twins(me); plan = {}
        for _ in range(6):
            if not separate_flush(me, plan=plan): break


def _signed_volume(faces):
    """In doubles and about the piece's own first vertex: on a sheet this flat, single-precision world coordinates only give rounding noise."""
    o = faces[0].verts[0].co; ox, oy, oz = float(o.x), float(o.y), float(o.z); vol = 0.
    for f in faces:
        q = [(float(v.co.x) - ox, float(v.co.y) - oy, float(v.co.z) - oz) for v in f.verts]
        for k in range(1, len(q) - 1):
            (ax, ay, az), (bx, by, bz), (cx, cy, cz) = q[0], q[k], q[k + 1]
            vol += (ax * (by * cz - bz * cy) + ay * (bz * cx - bx * cz) + az * (bx * cy - by * cx)) / 6
    return vol


FLUSH_TOL, FLUSH_PUSH = .0012, .0016   # the gap must clear a 1 mm near-coplanar test

def _clip_area(A, B):
    """Area where two 2D triangles overlap."""
    def ccw(t):
        return t if (t[1][0] - t[0][0]) * (t[2][1] - t[0][1]) - (t[1][1] - t[0][1]) * (t[2][0] - t[0][0]) >= 0 else t[::-1]
    poly = [tuple(p) for p in ccw(A.tolist())]; B = ccw(B.tolist())
    for i in range(3):
        if not poly: return 0.
        p, q = B[i], B[(i + 1) % 3]; ex, ey = q[0] - p[0], q[1] - p[1]; out = []
        for j, a in enumerate(poly):
            b = poly[(j + 1) % len(poly)]
            sa = ex * (a[1] - p[1]) - ey * (a[0] - p[0]); sb = ex * (b[1] - p[1]) - ey * (b[0] - p[0])
            if sa >= 0: out.append(a)
            if sa * sb < 0:
                t = sa / (sa - sb); out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
        poly = out
    if len(poly) < 3: return 0.
    return abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))) / 2


def near_pairs(P, group, tol=FLUSH_TOL, min_area=1e-6, cell=.1):
    """Same-facing triangles of two groups (pieces, objects) within tol of one plane and overlapping by more than min_area: they z-fight. P: triangles x 3 x 3, group: one id per triangle."""
    N = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]); L = np.linalg.norm(N, axis=1); ok = L > 2e-8; N[ok] /= L[ok][:, None]
    ok &= ~((N[:, 2] < -.9) & (P[:, 0, 2] < .002))    # flat on the ground: never seen
    cells = {}
    lo = np.floor(P.min(1) / cell).astype(int); hi = np.floor(P.max(1) / cell).astype(int)
    for i in np.nonzero(ok)[0].tolist():
        for x in range(lo[i, 0], hi[i, 0] + 1):
            for y in range(lo[i, 1], hi[i, 1] + 1):
                for z in range(lo[i, 2], hi[i, 2] + 1): cells.setdefault((x, y, z), []).append(i)
    seen = set(); out = []
    for ids in cells.values():
        if len(ids) < 2: continue
        ids = np.array(ids); g = group[ids]
        ii, jj = np.nonzero(np.triu((N[ids] @ N[ids].T > .9995) & (g[:, None] != g[None, :]), 1))
        if not len(ii): continue
        A, B = ids[ii], ids[jj]
        near = (np.abs(np.einsum('ijk,ik->ij', P[B] - P[A, 0][:, None], N[A])).max(1) <= tol) & (np.abs(np.einsum('ijk,ik->ij', P[A] - P[B, 0][:, None], N[B])).max(1) <= tol)
        for a, b in zip(A[near].tolist(), B[near].tolist()):
            key = (a, b) if a < b else (b, a)
            if key in seen: continue
            seen.add(key)
            e = P[a, 1] - P[a, 0]; e = e / np.linalg.norm(e); w = np.cross(N[a], e); qa = P[a] - P[a, 0]; qb = P[b] - P[a, 0]
            if _clip_area(np.c_[qa @ e, qa @ w], np.c_[qb @ e, qb @ w]) >= min_area: out.append((a, b))
    return out, N


def _tri_arrays(bm):
    """Triangle corners, and which connected piece each triangle belongs to, of a triangulated bmesh."""
    root = list(range(len(bm.verts)))
    def find(i):
        while root[i] != i: root[i] = root[root[i]]; i = root[i]
        return i
    for e in bm.edges: root[find(e.verts[0].index)] = find(e.verts[1].index)
    bm.faces.ensure_lookup_table()
    P = np.array([[tuple(v.co) for v in f.verts] for f in bm.faces], np.float64)
    return P, np.array([find(f.verts[0].index) for f in bm.faces]), find


def drop_twins(me, most_verts=100, near=.02, sized=.012):
    """A small piece scattered twice on the same spot (a grass blade, a leaf) is a real double: keep one."""
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.verts.ensure_lookup_table()
    P, piece, find = _tri_arrays(bm)
    if not len(P): bm.free(); return 0
    verts = {}
    for v in bm.verts: verts.setdefault(find(v.index), []).append(v.index)
    co = np.array([tuple(v.co) for v in bm.verts], np.float64); dead = set()
    pairs, _ = near_pairs(P, piece)
    for a, b in {tuple(sorted((int(piece[x]), int(piece[y])))) for x, y in pairs}:
        if a in dead or b in dead or len(verts[a]) != len(verts[b]) or len(verts[a]) > most_verts: continue
        qa, qb = co[verts[a]], co[verts[b]]
        if np.abs(qa.mean(0) - qb.mean(0)).max() < near and np.abs((qa.max(0) - qa.min(0)) - (qb.max(0) - qb.min(0))).max() < sized: dead.add(b)
    bm.free()
    if dead:
        bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[bm.verts[i] for k in dead for i in verts[k]], context='VERTS')
        bm.to_mesh(me); bm.free(); me.update()
    print('FLUSH_TWINS', me.name, len(dead), flush=True)
    return len(dead)


def separate_flush(me, push=FLUSH_PUSH, plan=None):
    """Where two pieces share a face plane, swell the smaller piece a hair so it sits proud; never below the ground. Returns how many pairs it found."""
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.verts.ensure_lookup_table(); bm.normal_update()
    P, piece, find = _tri_arrays(bm)
    if not len(P): bm.free(); return 0
    area = {}
    for f in bm.faces:
        k = find(f.verts[0].index); area[k] = area.get(k, 0.) + f.calc_area()
    lo = [min(v.co[k] for v in bm.verts) for k in range(3)]; hi = [max(v.co[k] for v in bm.verts) for k in range(3)]
    span = {}
    for v in bm.verts:
        k = find(v.index); s = span.setdefault(k, [list(v.co), list(v.co)])
        for i in range(3): s[0][i] = min(s[0][i], v.co[i]); s[1][i] = max(s[1][i], v.co[i])
    def thin(k): return min(b - a for a, b in zip(*span[k])) < 4 * push    # swelling would turn it inside out
    pairs, _ = near_pairs(P, piece); grow = set(); shift = {}; active = {}; plan = {} if plan is None else plan
    for x, y in pairs:
        a, b = int(piece[x]), int(piece[y])
        k, face = (a, bm.faces[x]) if area[a] < area[b] else (b, bm.faces[y])
        n = face.normal
        ways = plan.setdefault(k, [])   # keep going the way it went, per contact: switching back and forth never clears it
        way = next((w for w in ways if w is not None and abs(w.normalized().dot(n)) > .9), None)
        if way is None:
            if any(not lo[i] - 1e-6 <= v.co[i] + n[i] * push <= hi[i] + 1e-6 for v in face.verts for i in range(3)): way = -n * push * (1 + k % 3)    # on the mesh's outer bound: sink it, sizes and ports stay exact
            elif thin(k): way = n * push * (1 + k % 3)    # a row of equal pieces must not move as one; swelling would turn it inside out: slide it clear
            else: ways.append(None); grow.add(k); continue
            ways.append(way)
        active.setdefault(k, {})[id(way)] = way
    for k, used in active.items():
        if k not in grow: shift[k] = sum(used.values(), Vector())
    moved = {}
    if grow or shift:
        for v in bm.verts:
            k = find(v.index)
            if k not in shift and k not in grow: continue
            q = v.co + shift[k] if k in shift else v.co + v.normal * push
            moved[v.index] = tuple(min(max(q[i], lo[i]), hi[i]) for i in range(3))
    bm.free()
    for i, q in moved.items(): me.vertices[i].co = q
    me.update()
    return len(grow) + len(shift)


def _alternatives(a, b):
    """Stage_ groups and a lamp's _Lit twin are shown instead of one another, never together."""
    return ('Stage_' in a and 'Stage_' in b) or a.replace('_Lit', '') == b.replace('_Lit', '')


def settle_loose(touch=.002, rest=FLUSH_PUSH, reach=.065, rounds=5):
    """A part modelled a few millimetres off what holds it (a bowl above the shelf, a ladle head off its handle, a leaf above the floor) moves until it is held.
    Parts that touch one another move as one; a group on the ground, the largest group and a moving gate stay where they are."""
    P = []
    for gname, o in S['lod0'].items():
        bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table(); seen = set()
        for v0 in bm.verts:
            if v0.index in seen: continue
            comp, todo = [], [v0]; seen.add(v0.index)
            while todo:
                v = todo.pop(); comp.append(v.index)
                for e in v.link_edges:
                    w = e.other_vert(v)
                    if w.index not in seen: seen.add(w.index); todo.append(w)
            at = {i: n for n, i in enumerate(comp)}; faces = {f.index: [at[v.index] for v in f.verts] for i in comp for f in bm.verts[i].link_faces}
            co = np.array([tuple(bm.verts[i].co) for i in comp], np.float64)
            if faces: P.append(dict(group=gname, ids=np.array(comp), co=co, faces=list(faces.values()), still='Gate' in gname))
        bm.free()
    if len(P) < 2: return 0
    def tree(p): p['tree'] = BVHTree.FromPolygons([tuple(q) for q in p['co']], p['faces'])
    for p in P: tree(p)
    def sample(p, n=200): return [Vector(q) for q in p['co'][::max(1, len(p['co']) // n)]]
    ground = min(p['co'][:, 2].min() for p in P); moved = 0; big = max(range(len(P)), key=lambda i: len(P[i]['co']))
    def apart(a, b): return a['group'] != b['group'] and _alternatives(a['group'], b['group'])
    for _ in range(rounds):
        lo = np.array([p['co'].min(0) for p in P]); hi = np.array([p['co'].max(0) for p in P]); root = list(range(len(P)))
        def find(i):
            while root[i] != i: root[i] = root[root[i]]; i = root[i]
            return i
        for i in range(len(P)):
            for j in np.nonzero(((lo[i] - touch <= hi) & (hi[i] + touch >= lo)).all(1))[0].tolist():
                if j <= i or find(i) == find(j) or apart(P[i], P[j]): continue
                if P[i]['tree'].overlap(P[j]['tree']) or any(P[j]['tree'].find_nearest(q, touch)[0] is not None for q in sample(P[i])) or any(P[i]['tree'].find_nearest(q, touch)[0] is not None for q in sample(P[j])): root[find(i)] = find(j)
        groups = {}
        for i in range(len(P)): groups.setdefault(find(i), []).append(i)
        free = [g for g in groups.values() if big not in g and not any(P[i]['still'] or lo[i, 2] - ground <= touch for i in g)]
        if not free: break
        for g in sorted(free, key=lambda g: min(P[i]['co'][:, 2].min() for i in g)):
            inside = set(g); best = min(P[i]['co'][:, 2].min() for i in g) - ground; way = Vector((0, 0, -1)); drop = best
            box_lo = np.min([P[i]['co'].min(0) for i in g], 0); box_hi = np.max([P[i]['co'].max(0) for i in g], 0)
            near = [j for j in range(len(P)) if j not in inside and not any(apart(P[i], P[j]) for i in g)]
            for j in near:
                a, b = P[j]['co'].min(0), P[j]['co'].max(0)
                if (box_lo - best > b).any() or (box_hi + best < a).any(): continue
                for i in g:
                    for q in sample(P[i]):
                        c, _n, _f, d = P[j]['tree'].find_nearest(q, best)
                        if c is not None and d < best: best, way = d, (c - q).normalized()
            for j in near:
                if (box_lo[:2] > P[j]['co'].max(0)[:2]).any() or (box_hi[:2] < P[j]['co'].min(0)[:2]).any(): continue
                for i in g:
                    for q in sample(P[i], 80):
                        h = P[j]['tree'].ray_cast(q, Vector((0, 0, -1)), drop)
                        if h[0] is not None and h[3] < drop: drop = h[3]
            if drop <= reach and drop <= best * 2 + .005: best, way = drop, Vector((0, 0, -1))
            if best > reach:
                print('SETTLE_SKIP', [P[i]['group'] for i in g][:2], round(best, 3), [round(float(x), 3) for x in box_lo], flush=True); continue
            step = np.array(tuple(way)) * (best - rest)
            for i in g: P[i]['co'] = P[i]['co'] + step; tree(P[i])
            moved += len(g)
    for gname, o in S['lod0'].items():
        for p in P:
            if p['group'] != gname: continue
            for i, q in zip(p['ids'].tolist(), p['co'].tolist()): o.data.vertices[i].co = q
        o.data.update()
    print('SETTLE_MOVED', moved, 'of', len(P), flush=True)
    return moved


def separate_objects(push=FLUSH_PUSH, rounds=4):
    """The same between export groups: a detail object seated flush on the body. The smaller group's piece slides off along its face."""
    objs = list(S['lod0'].items())
    for _ in range(rounds):
        moved = 0
        for ai, (an, ao) in enumerate(objs):
            for bn, bo in objs[ai + 1:]:
                if _alternatives(an, bn): continue
                big, small = (ao, bo) if len(ao.data.polygons) >= len(bo.data.polygons) else (bo, ao)
                bma = bmesh.new(); bma.from_mesh(big.data); bmesh.ops.triangulate(bma, faces=bma.faces[:]); bma.faces.ensure_lookup_table()
                bmb = bmesh.new(); bmb.from_mesh(small.data); bmesh.ops.triangulate(bmb, faces=bmb.faces[:]); bmb.faces.ensure_lookup_table(); bmb.verts.ensure_lookup_table(); bmb.normal_update()
                Pa = np.array([[tuple(v.co) for v in f.verts] for f in bma.faces], np.float64); Pb, piece, find = _tri_arrays(bmb)
                bma.free()
                if not (len(Pa) and len(Pb)) or (Pa.min((0, 1)) - .002 > Pb.max((0, 1))).any() or (Pb.min((0, 1)) - .002 > Pa.max((0, 1))).any(): bmb.free(); continue
                pairs, N = near_pairs(np.r_[Pa, Pb], np.r_[np.zeros(len(Pa), int), np.ones(len(Pb), int)])
                shift = {}
                for x, y in pairs:
                    t = max(x, y) - len(Pa); k = int(piece[t]); shift[k] = Vector(N[t + len(Pa)]) * push * (1 + k % 3)
                bmb.free()
                if not shift: continue
                moved += len(shift)
                bmb = bmesh.new(); bmb.from_mesh(small.data); bmb.verts.ensure_lookup_table()
                root = list(range(len(bmb.verts)))
                def find2(i):
                    while root[i] != i: root[i] = root[root[i]]; i = root[i]
                    return i
                for e in bmb.edges: root[find2(e.verts[0].index)] = find2(e.verts[1].index)
                for v in bmb.verts:
                    k = find2(v.index)
                    if k in shift: small.data.vertices[v.index].co = v.co + shift[k]
                bmb.free(); small.data.update()
        print('FLUSH_OBJECTS', S['asset'], moved, flush=True)
        if not moved: break


def _dedupe_slots(me):
    mats = list(me.materials); uniq = []
    for m in mats:
        if m not in uniq: uniq.append(m)
    remap = [uniq.index(m) for m in mats]
    idx = np.zeros(len(me.polygons), dtype=np.int32); me.polygons.foreach_get('material_index', idx)
    idx = np.array([remap[i] if i < len(remap) else 0 for i in idx], dtype=np.int32)
    me.materials.clear()
    for m in uniq: me.materials.append(m)
    me.polygons.foreach_set('material_index', idx); me.update()

def _uv_islands(bm, uvl, skip):
    """Faces joined by edges whose two sides share their UVs; faces in skip stay out."""
    seen = set(); out = []
    for f0 in bm.faces:
        if f0.index in seen or f0.material_index in skip: continue
        comp, todo = [], [f0]; seen.add(f0.index)
        while todo:
            f = todo.pop(); comp.append(f)
            for l in f.loops:
                r = l.link_loop_radial_next
                if r == l or r.face.index in seen or r.face.material_index in skip: continue
                if (l[uvl].uv - r.link_loop_next[uvl].uv).length < 1e-6 and (l.link_loop_next[uvl].uv - r[uvl].uv).length < 1e-6:
                    seen.add(r.face.index); todo.append(r.face)
        out.append(comp)
    return out

def grow_small_islands(objs, size, own_of, min_px):
    """A piece narrower than a texel can miss every texel centre and bake to nothing, which reads black: open it to min_px along both of its axes."""
    grown = 0; tiny = 1e-7
    for o in objs:
        bm = bmesh.new(); bm.from_mesh(o.data); uvl = bm.loops.layers.uv.active
        for comp in _uv_islands(bm, uvl, own_of[o.name]):
            loops = [l for f in comp for l in f.loops]
            q = np.array([l[uvl].uv[:] for l in loops], dtype=np.float64)
            c = (q.min(0) + q.max(0)) / 2; d = q - c
            _, axes = np.linalg.eigh(d.T @ d)
            p = d @ axes; span = p.max(0) - p.min(0); want = min_px / size
            if span.min() >= want: continue
            grown += 1
            for k in range(2):
                if span[k] >= want: continue
                if span[k] > tiny: p[:, k] *= want / span[k]
                else:   # collinear in this axis: nothing to scale, so spread by the other axis
                    other = p[:, 1 - k]; rng = other.max() - other.min()
                    p[:, k] = (np.sin((other - other.min()) / max(rng, tiny) * math.pi) - .5) * want
            q = c + p @ axes.T
            for l, v in zip(loops, q): l[uvl].uv = (float(v[0]), float(v[1]))
        bm.to_mesh(o.data); bm.free(); o.data.update()
    return grown

def scale_islands_by_uvw(objs):
    """village-houses-b: each UV island scaled about its centre by sqrt(mean face 'uvw'), so its texel area follows the weight
    (inside faces of a closed house, the tops of the boards under the tiles)."""
    for o in objs:
        me = o.data
        if 'uvw' not in me.attributes: continue
        w = np.zeros(len(me.polygons), np.float32); me.attributes['uvw'].data.foreach_get('value', w)
        if np.allclose(w, 1.): continue
        bm = bmesh.new(); bm.from_mesh(me); uvl = bm.loops.layers.uv.active
        own = {i for i, m in enumerate(me.materials) if (MAT_INFO.get(m.name) or MAT_INFO.get(m.name.rsplit('.', 1)[0]) or {}).get('own_uv', False)}
        for comp in _uv_islands(bm, uvl, own):
            f = float(np.mean([w[fc.index] for fc in comp]))
            if abs(f - 1.) < 1e-3: continue
            loops = [l for fc in comp for l in fc.loops]
            q = np.array([l[uvl].uv[:] for l in loops]); c = q.mean(0); q = c + (q - c) * math.sqrt(max(f, 1e-3))
            for l, v in zip(loops, q): l[uvl].uv = (float(v[0]), float(v[1]))
        bm.to_mesh(me); bm.free(); me.update()


def uv_atlas(weights=None, size=2048, min_px=3., pad_px=2.5, shape='CONCAVE', objs=None):
    """weights: {group: factor} texel-density weight per export group (e.g. a basket's fill shares the atlas with the body).
    min_px: narrowest a piece may end up in texels. pad_px: gap between pieces in texels.
    shape: pack_islands shape_method; CONVEX packs by convex hull instead of nesting pieces into each other's notches. On the SG03
    sloped rail (sheared panel recess) it took the overlap from 663 to 265 texels; the rest are recess slivers that stay joined to the
    face beside them."""
    objs = objs or list(S['lod0'].values())
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    keep = {}
    for o in objs:
        me = o.data
        own = [(MAT_INFO.get(m.name) or MAT_INFO.get(m.name.rsplit('.', 1)[0]) or {}).get('own_uv', False) for m in me.materials]
        for p in me.polygons: p.select = not own[p.material_index]
        # own-UV faces (painting, journal page) keep their authored UVs: pack/average can still move them
        uvl = me.uv_layers.active
        keep[o.name] = {li: uvl.data[li].uv.copy() for p in me.polygons if own[p.material_index] for li in p.loop_indices}
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(58), island_margin=.0, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.average_islands_scale()
    bpy.ops.object.mode_set(mode='OBJECT'); scale_islands_by_uvw(objs); bpy.ops.object.mode_set(mode='EDIT')
    if weights:
        bpy.ops.object.mode_set(mode='OBJECT')
        for gname, o in S['lod0'].items():
            f = weights.get(gname)
            if not f: continue
            uvl = o.data.uv_layers.active; uv = np.zeros(len(uvl.data) * 2, dtype=np.float32)
            uvl.data.foreach_get('uv', uv); uvl.data.foreach_set('uv', uv * math.sqrt(f))   # area scales with f
        bpy.ops.object.mode_set(mode='EDIT')
    pack = lambda: bpy.ops.uv.pack_islands(rotate=True, margin_method='FRACTION', margin=pad_px / size, shape_method=shape)
    pack()
    own_of = {o.name: {i for i, m in enumerate(o.data.materials) if (MAT_INFO.get(m.name) or MAT_INFO.get(m.name.rsplit('.', 1)[0]) or {}).get('own_uv', False)} for o in objs}
    for _ in range(3):   # growing them changes what the next pack can fit, so measure again
        bpy.ops.object.mode_set(mode='OBJECT')
        n = grow_small_islands(objs, size, own_of, min_px)
        bpy.ops.object.mode_set(mode='EDIT')
        print('UV_GROW', S['asset'], n, flush=True)
        if not n: break
        pack()
    bpy.ops.object.mode_set(mode='OBJECT')
    for o in objs:
        uvl = o.data.uv_layers.active
        for li, uv in keep[o.name].items(): uvl.data[li].uv = uv

def _img(name, size, color=True, alpha=False):
    im = bpy.data.images.new(name, size, size, alpha=alpha, float_buffer=not color)
    im.colorspace_settings.name = 'sRGB' if color else 'Non-Color'
    return im

def spread_zero_uv(objs=None, eps=1e-8):
    """A sliver can pack to no area in the atlas: open it to a patch under one texel of the same spot."""
    n = 0
    for o in (S['lod0'].values() if objs is None else objs):
        bm = bmesh.new(); bm.from_mesh(o.data); uvl = bm.loops.layers.uv.active
        for f in bm.faces:
            q = [l[uvl].uv.copy() for l in f.loops]
            if min(abs((q[i] - q[0]).cross(q[i + 1] - q[0])) * .5 for i in range(1, len(q) - 1)) < eps:
                n += 1
                for i, l in enumerate(f.loops):
                    a = i / len(q) * math.tau; l[uvl].uv = q[i] + Vector((math.cos(a), math.sin(a))) * .0003
        bm.to_mesh(o.data); bm.free(); o.data.update()
    return n


def fill_gaps(work, name, size, color, blank, reach=24):
    """Blender bakes object by object and each object's margin paints over what the others baked, so bake with none (alpha marks written texels) and spread the colours into the gaps afterwards."""
    px = np.empty(size * size * 4, np.float32); work.pixels.foreach_get(px); px = px.reshape(size, size, 4)
    have = px[..., 3] > .5; rgb = px[..., :3].copy(); baked = float(have.mean())
    mean = rgb[have].mean(0) if have.any() else np.array(blank, np.float32)
    for _ in range(reach):
        n = have.astype(np.float32); val = rgb * n[..., None]
        tot = sum(np.roll(val, sh, ax) for sh, ax in ((1, 0), (-1, 0), (1, 1), (-1, 1)))
        cnt = sum(np.roll(n, sh, ax) for sh, ax in ((1, 0), (-1, 0), (1, 1), (-1, 1)))
        new = ~have & (cnt > 0)
        if not new.any(): break
        rgb[new] = tot[new] / cnt[new][:, None]; have |= new
    rgb[~have] = mean
    out = np.ones((size, size, 4), np.float32); out[..., :3] = rgb
    im = _img(name, size, color); im.pixels.foreach_set(out.ravel())
    bpy.data.images.remove(work)
    print('BAKE_COVER', name, round(baked, 3), flush=True)
    return im

def bake(tex_dir, size, objs=None, prefix=None):
    """Bake colour/roughness/metal/emission through an Emission shader, then a tangent normal map.
    village-houses-b: objs / prefix bake one atlas of several (prefix names the files)."""
    scene = bpy.context.scene; scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'
    scene.render.bake.margin = 0; scene.render.bake.use_clear = False
    objs = objs or list(S['lod0'].values())
    mats = {m for o in objs for m in o.data.materials if not MAT_INFO[m.name]['own_uv']}
    own = {m for o in objs for m in o.data.materials if MAT_INFO[m.name]['own_uv']}
    a = prefix or S['asset']; imgs = {}
    passes = [('BaseColor', 'OUT_COLOR', True, 16), ('Roughness', 'OUT_ROUGH', False, 4),
              ('Metallic', 'OUT_METAL', False, 4), ('Emission', 'OUT_EMIT', True, 4)]
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    dummy = _img('Bake_Dummy', 16)
    for label, node_name, color, samples in passes + [('Normal', None, False, 4)]:
        img = _img(f'{a}_{label}_work', size, color, True); img.pixels.foreach_set(np.zeros(size * size * 4, np.float32))
        scene.cycles.samples = samples
        for m in mats | own:
            nt = m.node_tree; tn = nt.nodes.new('ShaderNodeTexImage'); tn.name = 'BAKE_TARGET'
            tn.image = img if m in mats else dummy
            nt.nodes.active = tn
            if node_name:
                em = nt.nodes.new('ShaderNodeEmission'); em.name = 'BAKE_EMIT'; em.inputs['Strength'].default_value = 1
                src = nt.nodes[node_name].outputs[0]
                if src.type == 'VALUE':
                    cmb = nt.nodes.new('ShaderNodeCombineColor'); cmb.name = 'BAKE_CMB'
                    for i in range(3): nt.links.new(src, cmb.inputs[i])
                    src = cmb.outputs[0]
                nt.links.new(src, em.inputs['Color']); nt.links.new(em.outputs[0], nt.nodes['OUTPUT'].inputs['Surface'])
        if node_name: bpy.ops.object.bake(type='EMIT')
        else: bpy.ops.object.bake(type='NORMAL', normal_space='TANGENT')
        for m in mats | own:
            nt = m.node_tree
            for nm in ('BAKE_TARGET', 'BAKE_EMIT', 'BAKE_CMB'):
                if nm in nt.nodes: nt.nodes.remove(nt.nodes[nm])
            bs = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'][0]
            nt.links.new(bs.outputs[0], nt.nodes['OUTPUT'].inputs['Surface'])
        imgs[label] = fill_gaps(img, f'{a}_{label}', size, color, (.5, .5, 1.) if label == 'Normal' else (0., 0., 0.))
        print('BAKED', a, label, flush=True)
    tex_dir.mkdir(parents=True, exist_ok=True)
    files = {}
    for label in ('BaseColor', 'Normal', 'Roughness', 'Metallic', 'Emission'):
        im = imgs[label]; im.filepath_raw = str(tex_dir / f'{a}_{label}.png'); im.file_format = 'PNG'
        im.save(); files[label] = im.filepath_raw
    # Unity URP packed map: R metallic, A smoothness
    px = lambda im: np.array(im.pixels[:], dtype=np.float32).reshape(size, size, 4)
    met = px(imgs['Metallic'])[..., 0]; rough = px(imgs['Roughness'])[..., 0]
    ms = np.zeros((size, size, 4), np.float32); ms[..., 0] = met; ms[..., 1] = met; ms[..., 2] = met; ms[..., 3] = 1 - rough
    msi = _img(f'{a}_MetallicSmoothness', size, False, True); msi.pixels.foreach_set(ms.ravel())
    msi.filepath_raw = str(tex_dir / f'{a}_MetallicSmoothness.png'); msi.file_format = 'PNG'; msi.save()
    files['MetallicSmoothness'] = msi.filepath_raw
    emit_used = float(px(imgs['Emission'])[..., :3].max()) > .01
    if not emit_used:
        Path(files['Emission']).unlink(); del files['Emission']
    S['tex'] = {k: Path(v) for k, v in files.items()}
    S.setdefault('tex_sets', {})[a] = S['tex']
    return S['tex']

def make_lods():
    lods = {0: dict(S['lod0'])}
    for lv in (1, 2):
        lods[lv] = {}
        drop, ratio = LOD_RULES[lv]
        for gname, src in S['lod0'].items():
            o = src.copy(); o.data = src.data.copy(); S['lodcol'].objects.link(o)
            o.name = src.name.replace('_LOD0', f'_LOD{lv}'); o.data.name = o.name
            bm = bmesh.new(); bm.from_mesh(o.data)
            lay = bm.faces.layers.int.get('part_detail')
            kill = [f for f in bm.faces if f[lay] >= drop]
            bmesh.ops.delete(bm, geom=kill, context='FACES')
            bm.to_mesh(o.data); bm.free()
            if len(o.data.polygons) == 0:
                bpy.data.objects.remove(o); continue
            m = o.modifiers.new('LOD_decimate', 'DECIMATE'); m.ratio = ratio; m.use_collapse_triangulate = True
            bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
            bpy.ops.object.modifier_apply(modifier=m.name)
            orient_faces(o.data, flush=False)   # the collapse can leave slivers and turn a thin piece inside out
            with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o], selected_editable_objects=[o]):
                try: bpy.ops.mesh.customdata_custom_splitnormals_clear()
                except Exception: pass
                bpy.ops.object.shade_smooth_by_angle(angle=math.radians(38))
            lods[lv][gname] = o
    S['lods'] = lods
    return lods

def export_materials():
    """Swap procedural materials on the LOD meshes for baked texture materials (what ships)."""
    a = S['asset']; tex = S['tex']
    def load(p, color):
        im = bpy.data.images.load(str(p), check_existing=True); im.colorspace_settings.name = 'sRGB' if color else 'Non-Color'; return im
    base = load(tex['BaseColor'], True); nrm = load(tex['Normal'], False); rgh = load(tex['Roughness'], False)
    met = load(tex['Metallic'], False); emi = load(tex['Emission'], True) if 'Emission' in tex else None
    cache = {}
    def baked(slot, emissive):
        key = slot
        if key in cache: return cache[key]
        m = bpy.data.materials.new(f'M_{a}_{slot}'); m.use_nodes = True; nt = m.node_tree
        bs = nt.nodes['Principled BSDF']
        def t(im, sock, nonc=False):
            n = nt.nodes.new('ShaderNodeTexImage'); n.image = im; nt.links.new(n.outputs['Color'], sock); return n
        t(base, bs.inputs['Base Color']); t(rgh, bs.inputs['Roughness']); t(met, bs.inputs['Metallic'])
        nm = nt.nodes.new('ShaderNodeNormalMap'); t(nrm, nm.inputs['Color']); nt.links.new(nm.outputs[0], bs.inputs['Normal'])
        bs.inputs['Specular IOR Level'].default_value = .35
        if emissive and emi is not None:
            t(emi, bs.inputs['Emission Color'])
            v = nt.nodes.new('ShaderNodeValue'); v.name = 'EMIT_STRENGTH'; v.outputs[0].default_value = 0
            nt.links.new(v.outputs[0], bs.inputs['Emission Strength'])
        m['unity'] = {'shader': 'Universal Render Pipeline/Lit', 'emissive_slot': bool(emissive)}
        cache[key] = m; return m
    for lv, groups in S['lods'].items():
        for o in groups.values():
            me = o.data; newmats = []
            for m in me.materials:
                info = MAT_INFO.get(m.name) or dict(m['_ti_info'])
                if info['own_uv']:
                    newmats.append(m)            # keeps its own image texture; renamed once, shared by all LODs
                    if not m.name.startswith('M_'):
                        m['_ti_info'] = info; m.name = f"M_{a}_{info['slot']}"
                else:
                    newmats.append(baked(info['slot'], info['slot'] != 'Main'))
            idx = np.zeros(len(me.polygons), dtype=np.int32); me.polygons.foreach_get('material_index', idx)
            me.materials.clear()                 # clear() resets polygon material indices
            for m in newmats: me.materials.append(m)
            me.polygons.foreach_set('material_index', idx); me.update()
            _dedupe_slots(me)
    return cache

def tri_count(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)

def export_fbx(path):
    a = S['asset']
    root = bpy.data.objects.new(a, None); S['lodcol'].objects.link(root); S['root'] = root
    for groups in S['lods'].values():
        for o in groups.values(): o.parent = root
    for e in S['sockets'].values():
        mw = e.matrix_world.copy()
        for c in list(e.users_collection): c.objects.unlink(e)
        S['lodcol'].objects.link(e); e.parent = root; e.matrix_world = mw
    bpy.ops.object.select_all(action='DESELECT')
    root.select_set(True)
    for groups in S['lods'].values():
        for o in groups.values(): o.select_set(True)
    for e in S['sockets'].values(): e.select_set(True)
    bpy.context.view_layer.objects.active = root
    bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True, object_types={'MESH', 'EMPTY'},
                             apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', bake_space_transform=True,
                             axis_forward='-Z', axis_up='Y', mesh_smooth_type='FACE', use_mesh_modifiers=True,
                             add_leaf_bones=False, bake_anim=False, path_mode='STRIP', embed_textures=False)

def fbx_roundtrip(path):
    """Re-import the FBX into an empty scene and report object names and LOD0 dimensions."""
    before = set(bpy.data.objects)
    tmp = bpy.data.collections.new('99_FBX_Check'); bpy.context.scene.collection.children.link(tmp)
    lc = bpy.context.view_layer.layer_collection.children[tmp.name]; bpy.context.view_layer.active_layer_collection = lc
    bpy.ops.import_scene.fbx(filepath=str(path))
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH' and o.name.split('.')[0].endswith('_LOD0')]
    bpy.context.view_layer.update()
    lo, hi = eval_bounds(meshes)
    rep = {'objects': sorted(o.name for o in new), 'lod0_dimensions_m': [round(v, 4) for v in hi - lo],
           'sockets': {o.name: [round(v, 4) for v in o.matrix_world.translation] for o in new if o.name.lower().startswith('socket_')}}
    for o in new: bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.collections.remove(tmp)
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    return rep

# ---------------------------------------------------------------- studio renders
def studio(extent_objs, samples=48):
    scene = bpy.context.scene
    st = bpy.data.collections.get('90_Studio_Not_Exported')
    if st is None:
        st = bpy.data.collections.new('90_Studio_Not_Exported'); scene.collection.children.link(st)
    for o in list(st.objects): bpy.data.objects.remove(o, do_unlink=True)
    lo, hi = eval_bounds(extent_objs); centre = (lo + hi) / 2; ext = hi - lo
    cam = bpy.data.objects.new('Reference_Camera', bpy.data.cameras.new('Reference_Camera')); st.objects.link(cam)
    scene.camera = cam; cam.data.type = 'ORTHO'; cam.data.clip_start = .01; cam.data.clip_end = 100
    cam.data.ortho_scale = max(ext.length * 1.08, .3)
    ls = max(max(ext) * .65, .25)
    for name, d, p in [('Key', (-.8, -1.1, 1.5), 1100), ('Fill', (1.2, -.4, .9), 650), ('Rim', (.2, 1.1, 1.3), 950)]:
        L = bpy.data.lights.new(name, 'AREA'); L.energy = p * ls * ls / 7; L.shape = 'DISK'; L.size = ls
        o = bpy.data.objects.new(name, L); st.objects.link(o); o.location = centre + Vector(d) * ls
        o.rotation_euler = (centre - o.location).to_track_quat('-Z', 'Y').to_euler()
    scene.world = bpy.data.worlds.get('Neutral_Studio') or bpy.data.worlds.new('Neutral_Studio'); scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes['Background']; bg.inputs[0].default_value = (.19, .21, .22, 1); bg.inputs[1].default_value = .65
    scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = samples; scene.cycles.use_denoising = True
    scene.render.resolution_x = scene.render.resolution_y = 1024; scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'; scene.view_settings.view_transform = 'AgX'
    scene.view_settings.exposure = EXPOSURE
    scene.render.film_transparent = False
    return cam, centre, ext

def show_only(objs):
    keep = set(objs)
    for o in bpy.context.scene.objects:
        if o.type == 'MESH': o.hide_render = o not in keep

def ten_views(objs, out_dir, source_rel):
    from bpy_extras.object_utils import world_to_camera_view
    scene = bpy.context.scene; show_only(objs)
    cam, centre, ext = studio(objs)
    out_dir.mkdir(parents=True, exist_ok=True); records = []
    for name, d in VIEWS:
        cam.location = centre + Vector(d).normalized() * cam.data.ortho_scale * 2.3
        cam.rotation_euler = (centre - cam.location).to_track_quat('-Z', 'Y').to_euler(); bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        proj = [world_to_camera_view(scene, cam, o.matrix_world @ Vector(p)) for o in objs for p in o.evaluated_get(dg).bound_box]
        ok = all(.005 < p.x < .995 and .005 < p.y < .995 and p.z > 0 for p in proj)
        assert ok, (S['asset'], name, 'cropped')
        scene.render.filepath = str(out_dir / f'{name}.png'); bpy.ops.render.render(write_still=True)
        records.append({'file': f'{name}.png', 'direction': list(d), 'camera_location': [round(v, 4) for v in cam.location],
                        'projection': 'orthographic', 'framing_checked': True})
        print('VIEW_COMPLETE', S['asset'], name, flush=True)
    (out_dir / 'views.json').write_text(json.dumps({'asset': S['asset'], 'source': source_rel, 'same_geometry': True,
                                                     'render_of': 'exported LOD0 with baked textures', 'views': records}, indent=2))
    return records

def persp_shot(objs, path, direction=(1, -1.25, .55), samples=64, lens=55, margin=1.12):
    scene = bpy.context.scene; show_only(objs)
    cam, centre, ext = studio(objs, samples)
    cam.data.type = 'PERSP'; cam.data.lens = lens
    dist = ext.length * margin / (2 * math.tan(cam.data.angle / 2))
    cam.location = centre + Vector(direction).normalized() * dist
    cam.rotation_euler = (centre - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(path); bpy.ops.render.render(write_still=True)

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()
