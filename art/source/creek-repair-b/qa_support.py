"""Is each separate piece of a delivered FBX actually held by something? Reads only.
For every connected piece: the gap to the nearest other piece (or the ground) and how far it could drop straight down.
blender --background --python qa_support.py -- <asset.fbx> [out.json]"""
import bpy, bmesh, json, sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

TOUCH = .002   # 2 mm: closer than this reads as resting on or fixed to it, at any distance the game shows


def load(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(path))
    out = []
    for o in sorted((o for o in bpy.data.objects if o.type == 'MESH' and 'LOD1' not in o.name and 'LOD2' not in o.name and '_Collision' not in o.name and not o.name.lower().endswith('_water_lod0')), key=lambda o: o.name):
        bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world); bm.verts.ensure_lookup_table(); seen = set()
        for v0 in bm.verts:
            if v0.index in seen: continue
            comp, todo = [], [v0]; seen.add(v0.index)
            while todo:
                v = todo.pop(); comp.append(v)
                for e in v.link_edges:
                    w = e.other_vert(v)
                    if w.index not in seen: seen.add(w.index); todo.append(w)
            ids = {v.index for v in comp}; index = {v.index: i for i, v in enumerate(comp)}
            faces = [[index[v.index] for v in f.verts] for f in {f for v in comp for f in v.link_faces} if all(v.index in ids for v in f.verts)]
            if faces: out.append((o.name, [v.co.copy() for v in comp], faces))
        bm.free()
    return out


def main():
    args = sys.argv[sys.argv.index('--') + 1:]; path = Path(args[0]); P = load(path)
    trees = [BVHTree.FromPolygons(q, f) for _, q, f in P]
    los = [Vector(tuple(min(v[k] for v in q) for k in range(3))) for _, q, f in P]; his = [Vector(tuple(max(v[k] for v in q) for k in range(3))) for _, q, f in P]
    held = []; rows = []
    for i, (name, q, f) in enumerate(P):
        best = los[i].z   # the ground
        who = 'ground'
        for j, t in enumerate(trees):
            if j == i or any(los[i][k] > his[j][k] + best or his[i][k] < los[j][k] - best for k in range(3)): continue
            if t.overlap(trees[i]): best, who = 0., P[j][0]; break
            for v in q[::max(1, len(q) // 80)]:
                n = t.find_nearest(v, best)
                if n[0] is not None and n[3] < best: best, who = n[3], P[j][0]
        drop = los[i].z
        for j, t in enumerate(trees):
            if j == i: continue
            for v in q[::max(1, len(q) // 40)]:
                h = t.ray_cast(v, Vector((0, 0, -1)), drop)
                if h[0] is not None and h[3] < drop: drop = h[3]
        if best > TOUCH:
            lo, hi = los[i], his[i]
            rows.append(dict(object=name.split('_LOD0')[0], verts=len(q), centre=[round(v, 3) for v in (lo + hi) / 2], size=[round(v, 3) for v in hi - lo], gap_mm=round(best * 1000, 1), nearest=who.split('_LOD0')[0], drop_mm=round(drop * 1000, 1)))
    rows.sort(key=lambda r: -r['gap_mm'])
    print('QASUPPORT', path.stem, 'pieces', len(P), 'over_2mm', len(rows), 'over_5mm', sum(r['gap_mm'] > 5 for r in rows), 'over_20mm', sum(r['gap_mm'] > 20 for r in rows))
    for r in rows[:14]: print('  ', r)
    if len(args) > 1: json.dump(dict(asset=path.stem, pieces=len(P), touch_m=TOUCH, unsupported=rows), open(args[1], 'w', encoding='utf8'), indent=1)


main()
