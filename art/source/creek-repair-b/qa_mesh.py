"""Mesh QA on a saved asset .blend, reads only: zero-area UV and degenerate triangles, coplanar overlapping triangles (same-facing pairs z-fight; opposite-facing pairs are the two sides of a thin sheet), closed pieces with inverted normals.
blender --background <asset>.blend --python qa_mesh.py [-- out.json]"""
import bpy, bmesh, collections, json, math, sys
from mathutils import Vector

EPS_AREA, EPS_UV = 1e-10, 1e-12


def _tri2(f, u, v):
    return [(p.co.dot(u), p.co.dot(v)) for p in f.verts]


def _overlap(A, B):
    """Separating axis on two triangles in the same plane; touching edges do not count."""
    for P, Q in ((A, B), (B, A)):
        for i in range(3):
            ex, ey = P[(i + 1) % 3][0] - P[i][0], P[(i + 1) % 3][1] - P[i][1]; L = math.hypot(ex, ey)
            if L < 1e-9: return False
            nx, ny = -ey / L, ex / L
            a = [x * nx + y * ny for x, y in P]; b = [x * nx + y * ny for x, y in Q]
            if max(a) <= min(b) + 1e-5 or max(b) <= min(a) + 1e-5: return False
    return True


def coplanar(bm, tol=.0005):
    planes = collections.defaultdict(list)
    for f in bm.faces:
        if f.calc_area() < 1e-8: continue
        n = f.normal; s = 1 if (n.x, n.y, n.z) > (0, 0, 0) else -1; c = n * s
        planes[(round(c.x, 2), round(c.y, 2), round(c.z, 2))].append((c.dot(f.verts[0].co), s, f))
    same = opp = 0; spots = collections.Counter()
    for key, fs in planes.items():
        if len(fs) < 2: continue
        fs.sort(key=lambda q: q[0]); n = Vector(key).normalized(); u = n.orthogonal().normalized(); v = n.cross(u)
        tris = [_tri2(q[2], u, v) for q in fs]
        for i in range(len(fs)):
            j = i + 1
            while j < len(fs) and fs[j][0] - fs[i][0] <= tol:
                if fs[i][2].normal.dot(fs[j][2].normal) ** 2 > .9995 and _overlap(tris[i], tris[j]):
                    if fs[i][1] == fs[j][1]:
                        same += 1; c = fs[i][2].calc_center_median(); spots[(round(c.x, 2), round(c.y, 2), round(c.z, 2))] += 1
                    else: opp += 1
                j += 1
    return same, opp, spots.most_common(6)


def islands(bm):
    seen = set(); inverted = closed = opened = 0; spots = []
    for f0 in bm.faces:
        if f0.index in seen: continue
        isl, todo = [], [f0]; seen.add(f0.index)
        while todo:
            f = todo.pop(); isl.append(f)
            for e in f.edges:
                for g in e.link_faces:
                    if g.index not in seen: seen.add(g.index); todo.append(g)
        if any(len(e.link_faces) != 2 for f in isl for e in f.edges): opened += 1; continue
        closed += 1; vol = 0.; o = isl[0].verts[0].co; ox, oy, oz = float(o.x), float(o.y), float(o.z)    # doubles about the piece: single precision is only noise on a flat sheet
        for f in isl:
            (ax, ay, az), (bx, by, bz), (cx, cy, cz) = [(float(p.co.x) - ox, float(p.co.y) - oy, float(p.co.z) - oz) for p in f.verts[:3]]
            vol += (ax * (by * cz - bz * cy) + ay * (bz * cx - bx * cz) + az * (bx * cy - by * cx)) / 6
        if vol < -1e-12:
            inverted += 1; c = isl[0].calc_center_median(); spots.append((round(c.x, 2), round(c.y, 2), round(c.z, 2)))
    return closed, opened, inverted, spots[:6]


def main():
    report = {}
    for o in sorted((o for o in bpy.data.objects if o.type == 'MESH' and '_LOD' in o.name), key=lambda o: o.name):
        bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.faces.ensure_lookup_table(); bm.normal_update()
        uv = bm.loops.layers.uv.active; deg = zero = 0; spots = collections.Counter()
        for f in bm.faces:
            d = f.calc_area() < EPS_AREA; z = False
            if uv:
                a, b, c = [l[uv].uv for l in f.loops]; z = abs((b - a).cross(c - a)) * .5 < EPS_UV
            deg += d; zero += z
            if d or z:
                q = f.calc_center_median(); spots[(round(q.x, 2), round(q.y, 2), round(q.z, 2))] += 1
        same, opp, csp = coplanar(bm) if o.name.endswith('_LOD0') else (0, 0, [])
        closed, opened, inv, isp = islands(bm)
        report[o.name] = dict(tris=len(bm.faces), degenerate=deg, zero_uv=zero, coplanar_same_facing=same, coplanar_two_sides=opp, closed_pieces=closed, open_pieces=opened, inverted_closed=inv, zero_at=spots.most_common(4), same_at=csp, inverted_at=isp)
        bm.free()
    for k, r in report.items():
        if r['degenerate'] or r['zero_uv'] or r['coplanar_same_facing'] or r['inverted_closed']:
            print('QA', k, {a: r[a] for a in ('tris', 'degenerate', 'zero_uv', 'coplanar_same_facing', 'coplanar_two_sides', 'inverted_closed')}, 'zero', r['zero_at'][:2], 'same', r['same_at'][:3], 'inv', r['inverted_at'][:3])
    t = {a: sum(r[a] for r in report.values()) for a in ('tris', 'degenerate', 'zero_uv', 'coplanar_same_facing', 'coplanar_two_sides', 'inverted_closed')}
    print('QATOTAL', bpy.path.basename(bpy.data.filepath), t)
    if '--' in sys.argv:
        args = sys.argv[sys.argv.index('--') + 1:]
        if args: json.dump(report, open(args[0], 'w', encoding='utf8'), indent=1)


main()
