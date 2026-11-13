"""QA on a freshly re-imported FBX, reads only. Near-coplanar triangles at several tolerances, split by object pair, same-facing or two sides of a sheet, inside one piece or between two;
zero-area UV at several thresholds; pieces with nothing else within reach.
blender --background --factory-startup --python qa_fbx.py -- <asset.fbx> [out.json]"""
import bpy, bmesh, collections, json, sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

TOLS = (.001, .0005, .0001)
UV_EPS = (1e-12, 1e-10, 1e-9, 1e-8)
MIN_OVERLAP = 1e-6   # 1 mm2: anything smaller cannot show
CELL = .1


def load(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(path))
    V, T, TO, TUV = [], [], [], []; names = []; base = 0
    for o in sorted((o for o in bpy.data.objects if o.type == 'MESH' and 'LOD1' not in o.name and 'LOD2' not in o.name and '_Collision' not in o.name), key=lambda o: o.name):
        bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world); bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.verts.ensure_lookup_table()
        uv = bm.loops.layers.uv.active; k = len(names); names.append(o.name)
        V += [tuple(v.co) for v in bm.verts]
        for f in bm.faces:
            T.append([v.index + base for v in f.verts]); TO.append(k)
            TUV.append([tuple(l[uv].uv) for l in f.loops] if uv else [(0, 0)] * 3)
        base += len(bm.verts); bm.free()
    return np.array(V, np.float64), np.array(T, np.int64), np.array(TO), np.array(TUV, np.float64), names


def pieces(n, T):
    root = np.arange(n)
    def find(i):
        while root[i] != i: root[i] = root[root[i]]; i = root[i]
        return i
    for a, b, c in T.tolist():
        ra = find(a); root[find(b)] = ra; root[find(c)] = ra
    return np.array([find(i) for i in range(n)])


def clip_area(A, B):
    """Area of triangle A clipped by triangle B, both 2D."""
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


def alternatives(a, b):
    """Stage_ groups and a lamp's _Lit twin are shown instead of one another, never together."""
    return ('Stage_' in a and 'Stage_' in b) or (a != b and a.replace('_Lit', '') == b.replace('_Lit', ''))


def near_pairs(V, T, tol):
    P = V[T]; N = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]); L = np.linalg.norm(N, axis=1); ok = L > 2e-8; N[ok] /= L[ok][:, None]
    cells = collections.defaultdict(list)
    lo = np.floor(P.min(1) / CELL).astype(int); hi = np.floor(P.max(1) / CELL).astype(int)
    for i in np.nonzero(ok)[0].tolist():
        for x in range(lo[i, 0], hi[i, 0] + 1):
            for y in range(lo[i, 1], hi[i, 1] + 1):
                for z in range(lo[i, 2], hi[i, 2] + 1): cells[(x, y, z)].append(i)
    seen = set(); out = []
    for ids in cells.values():
        if len(ids) < 2: continue
        ids = np.array(ids); D = N[ids] @ N[ids].T
        ii, jj = np.nonzero(np.triu(np.abs(D) > .9995, 1))
        for a, b in zip(ids[ii].tolist(), ids[jj].tolist()):
            key = (a, b) if a < b else (b, a)
            if key in seen: continue
            seen.add(key)
            if np.abs((P[b] - P[a, 0]) @ N[a]).max() > tol or np.abs((P[a] - P[b, 0]) @ N[b]).max() > tol: continue
            e = P[a, 1] - P[a, 0]; e = e / np.linalg.norm(e); w = np.cross(N[a], e)
            area = clip_area(np.c_[(P[a] - P[a, 0]) @ e, (P[a] - P[a, 0]) @ w], np.c_[(P[b] - P[a, 0]) @ e, (P[b] - P[a, 0]) @ w])
            if area >= MIN_OVERLAP: out.append((a, b, area, float(N[a] @ N[b])))
    return out


def loose(V, T, root, reach=.005):
    """Pieces with no other piece within reach; the ground-level ones stand on the terrain."""
    comp = root[T[:, 0]]; bvh = BVHTree.FromPolygons([tuple(v) for v in V.tolist()], T.tolist(), all_triangles=True)
    verts = collections.defaultdict(list)
    for i, r in enumerate(root.tolist()): verts[r].append(i)
    zmin = V[:, 2].min(); out = []
    for r, ids in verts.items():
        q = V[ids]
        if q[:, 2].min() < zmin + .02: continue
        step = max(1, len(ids) // 300); touch = False
        for co in q[::step].tolist():
            if any(comp[h[2]] != r for h in bvh.find_nearest_range(co, reach)): touch = True; break
        if not touch: out.append((r, dict(verts=len(ids), centre=[round(float(x), 3) for x in q.mean(0)], size=[round(float(x), 3) for x in q.max(0) - q.min(0)])))
    # contact is two-way: a plank resting on a leg has no vertex over the leg, but the leg's top vertices lie on the plank.
    # So a piece also counts as touched when another piece's vertex lies within reach of it.
    if out:
        flagged = {r for r, _ in out}; touched = set()
        for r, ids in verts.items():
            step = max(1, len(ids) // 300)
            for co in V[ids][::step].tolist():
                for h in bvh.find_nearest_range(co, reach):
                    o = int(comp[h[2]])
                    if o != r and o in flagged: touched.add(o)
        out = [(r, d) for r, d in out if r not in touched]
    # contact by penetration: a spoke end or a paddle passing through a rim segment has no vertex near the rim's surface,
    # but its vertices lie inside the rim's closed volume (or the rim's inside it). Inside = the nearest face's normal points away.
    if out:
        lo_b = {r: V[ids].min(0) - reach for r, ids in verts.items()}; hi_b = {r: V[ids].max(0) + reach for r, ids in verts.items()}
        cache = {}
        def piece_bvh(r):
            if r not in cache:
                tri = T[comp == r]; cache[r] = BVHTree.FromPolygons([tuple(v) for v in V.tolist()], tri.tolist(), all_triangles=True)
            return cache[r]
        closed_c = {}
        def closed(r):          # only a closed piece has an inside; a leaf sheet or a strip does not
            if r not in closed_c:
                tri = T[comp == r]; e = np.sort(np.concatenate([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]]), 1)
                _, n = np.unique(e, axis=0, return_counts=True); closed_c[r] = bool((n == 2).all())
            return closed_c[r]
        def inside(r, co):
            if not closed(r): return False
            loc, nrm, _, _ = piece_bvh(r).find_nearest(co)
            return loc is not None and (Vector(co) - loc).dot(nrm) < 0
        keep = []
        for r, d in out:
            lo, hi = lo_b[r], hi_b[r]; hit = False
            for o, ids in verts.items():
                if o == r or (hi_b[o] < lo).any() or (lo_b[o] > hi).any(): continue
                for a_, b_, pts in ((r, o, V[verts[o]]), (o, r, V[verts[r]])):     # o's vertices inside r, then r's inside o
                    m = ((pts >= lo_b[a_]) & (pts <= hi_b[a_])).all(1); pts = pts[m]
                    for co in pts[::max(1, len(pts) // 200)].tolist():
                        if inside(a_, co): hit = True; break
                    if hit: break
                if hit: break
            if not hit: keep.append((r, d))
        out = keep
    return sorted([d for _, d in out], key=lambda d: -d['verts']), len(verts)


def main():
    args = sys.argv[sys.argv.index('--') + 1:]; fbx = Path(args[0]).resolve()
    V, T, TO, TUV, names = load(fbx); root = pieces(len(V), T); comp = root[T[:, 0]]; short = [n.split('_LOD0')[0].split('_', 2)[-1] for n in names]
    r = dict(asset=fbx.stem, tris=len(T), objects=names, near_coplanar={}, zero_uv={}, zero_uv_by_object={})
    a = TUV[:, 1] - TUV[:, 0]; b = TUV[:, 2] - TUV[:, 0]; ua = np.abs(a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]) / 2
    for e in UV_EPS:
        r['zero_uv'][str(e)] = int((ua < e).sum())
        r['zero_uv_by_object'][str(e)] = {names[k]: int(((ua < e) & (TO == k)).sum()) for k in range(len(names)) if ((ua < e) & (TO == k)).any()}
    under = collections.Counter()
    for tol in TOLS:
        ps = near_pairs(V, T, tol); states = sum(alternatives(names[TO[p[0]]], names[TO[p[1]]]) for p in ps); ps = [p for p in ps if not alternatives(names[TO[p[0]]], names[TO[p[1]]])]; t = collections.Counter(); ar = collections.Counter(); spots = collections.Counter()
        for x, y, area, d in ps:
            pair = '/'.join(sorted({short[TO[x]], short[TO[y]]}))
            kind = ('same' if d > 0 else 'two_sides') + ('_inside' if comp[x] == comp[y] else '_between')
            q = V[T[x]]; up = np.cross(q[1] - q[0], q[2] - q[0])
            if d > 0 and q[:, 2].max() < .025 and up[2] < -.9 * np.linalg.norm(up): under[tol] += 1   # both faces look straight down onto the ground: never seen
            t[(pair, kind)] += 1; ar[(pair, kind)] += area
            if d > 0: spots[tuple(round(float(q), 2) for q in V[T[x]].mean(0))] += 1
        r['near_coplanar'][f'{tol * 1000:g}mm'] = dict(
            state_alternatives=int(states), same_underside_on_ground=under[tol], same_between=sum(1 for p in ps if p[3] > 0 and comp[p[0]] != comp[p[1]]), same_inside=sum(1 for p in ps if p[3] > 0 and comp[p[0]] == comp[p[1]]), same=sum(1 for p in ps if p[3] > 0), two_sides=sum(1 for p in ps if p[3] <= 0),
            groups={f'{k[0]}|{k[1]}': dict(pairs=n, overlap_cm2=round(ar[k] * 1e4, 2)) for k, n in t.most_common()}, same_at=[list(k) + [n] for k, n in spots.most_common(12)])
    fl, count = loose(V, T, root); r['pieces'] = count; r['loose_over_5mm'] = len(fl); r['loose_list'] = fl[:30]
    m = r['near_coplanar']
    print('QAFBX', fbx.stem, 'tris', len(T), 'pieces', count, 'same@1mm', m['1mm']['same'], 'under', m['1mm']['same_underside_on_ground'], 'between', m['1mm']['same_between'], 'inside', m['1mm']['same_inside'], 'states', m['1mm']['state_alternatives'], 'same@.5', m['0.5mm']['same'], 'same@.1', m['0.1mm']['same'], 'two_sides@1mm', m['1mm']['two_sides'], 'zero_uv', r['zero_uv'], 'loose', len(fl))
    for k, v in list(m['1mm']['groups'].items())[:10]: print('  ', k, v)
    for x in fl[:6]: print('   loose', x)
    if len(args) > 1: json.dump(r, open(args[1], 'w', encoding='utf8'), indent=1, ensure_ascii=False)


if __name__ == "__main__":      # importable: build scripts reuse near_pairs()
    main()
