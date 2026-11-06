"""Close-ups of the spots listed as same-facing coplanar pairs (same rule as qa_mesh.py), and whether each pair is inside one piece or between two. Reads only; writes PNGs.
blender --background --factory-startup <asset>.blend --python qa_closeup.py -- <out dir> [how many]"""
import bpy, bmesh, collections, math, sys
from pathlib import Path
from mathutils import Vector


def _overlap(A, B):
    for P, Q in ((A, B), (B, A)):
        for i in range(3):
            ex, ey = P[(i + 1) % 3][0] - P[i][0], P[(i + 1) % 3][1] - P[i][1]; L = math.hypot(ex, ey)
            if L < 1e-9: return False
            nx, ny = -ey / L, ex / L
            a = [x * nx + y * ny for x, y in P]; b = [x * nx + y * ny for x, y in Q]
            if max(a) <= min(b) + 1e-5 or max(b) <= min(a) + 1e-5: return False
    return True


def same_facing(bm, tol=.0005):
    planes = collections.defaultdict(list)
    for f in bm.faces:
        if f.calc_area() < 1e-8: continue
        n = f.normal; s = 1 if (n.x, n.y, n.z) > (0, 0, 0) else -1; c = n * s
        planes[(round(c.x, 2), round(c.y, 2), round(c.z, 2))].append((c.dot(f.verts[0].co), s, f))
    out = []
    for key, fs in planes.items():
        if len(fs) < 2: continue
        fs.sort(key=lambda q: q[0]); n = Vector(key).normalized(); u = n.orthogonal().normalized(); v = n.cross(u)
        tris = [[(p.co.dot(u), p.co.dot(v)) for p in q[2].verts] for q in fs]
        for i in range(len(fs)):
            j = i + 1
            while j < len(fs) and fs[j][0] - fs[i][0] <= tol:
                if fs[i][1] == fs[j][1] and fs[i][2].normal.dot(fs[j][2].normal) ** 2 > .9995 and _overlap(tris[i], tris[j]): out.append((fs[i][2], fs[j][2]))
                j += 1
    return out


def main():
    args = sys.argv[sys.argv.index('--') + 1:]; out = Path(args[0]).resolve(); out.mkdir(parents=True, exist_ok=True); top = int(args[1]) if len(args) > 1 else 3
    spots = []
    for o in [o for o in bpy.data.objects if o.type == 'MESH' and o.name.endswith('_LOD0')]:
        bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table(); bm.normal_update()
        root = list(range(len(bm.verts)))
        def find(i):
            while root[i] != i: root[i] = root[root[i]]; i = root[i]
            return i
        for e in bm.edges: root[find(e.verts[0].index)] = find(e.verts[1].index)
        ps = same_facing(bm); inside = sum(find(f.verts[0].index) == find(g.verts[0].index) for f, g in ps)
        if ps: print('QAPAIRS', o.name, 'pairs', len(ps), 'inside_one_piece', inside, 'between_pieces', len(ps) - inside, 'overlap_area_cm2_at_most', round(sum(min(f.calc_area(), g.calc_area()) for f, g in ps) * 1e4, 3))
        cells = collections.defaultdict(lambda: [0, None, None])
        for f, g in ps:
            c = f.calc_center_median(); k = (round(c.x, 1), round(c.y, 1), round(c.z, 1)); cells[k][0] += 1; cells[k][1] = o.matrix_world @ c; cells[k][2] = (o.matrix_world.to_3x3() @ f.normal).normalized()
        spots += [(n, o.name, p, d) for n, p, d in cells.values()]
        bm.free()
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 32; sc.cycles.use_denoising = True; sc.render.resolution_x = sc.render.resolution_y = 640
    sc.render.film_transparent = False
    for o in bpy.data.objects:
        if o.type == 'MESH' and not o.name.endswith('_LOD0'): o.hide_render = True
    w = bpy.data.worlds.new('Sky'); w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (.6, .62, .65, 1); sc.world = w
    cam = bpy.data.objects.new('QACam', bpy.data.cameras.new('QACam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 50; cam.data.clip_start = .005
    lamp = bpy.data.objects.new('QASun', bpy.data.lights.new('QASun', 'SUN')); sc.collection.objects.link(lamp); lamp.data.energy = 3; lamp.rotation_euler = (.9, 0, -.5)
    for i, (n, name, p, d) in enumerate(sorted(spots, key=lambda s: -s[0])[:top]):
        v = (d + Vector((.15, -.2, .25))).normalized(); cam.location = p + v * .28; cam.rotation_euler = (-v).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = str(out / f'qa_closeup_{i + 1}.png'); bpy.ops.render.render(write_still=True)
        print('QASPOT', i + 1, name, 'pairs', n, [round(x, 3) for x in p], flush=True)


main()
