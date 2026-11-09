"""UV overlap on a saved asset .blend, reads only: rasterises LOD0 UV pieces onto the atlas and counts texels claimed by more than one piece.
blender --background <asset>.blend --python qa_uv_overlap.py"""
import bpy, bmesh
import numpy as np

SIZE = 2048


def pieces(bm, uv):
    seen = set(); out = []
    for f0 in bm.faces:
        if f0.index in seen: continue
        comp, todo = [], [f0]; seen.add(f0.index)
        while todo:
            f = todo.pop(); comp.append(f)
            for l in f.loops:
                r = l.link_loop_radial_next
                if r == l or r.face.index in seen: continue
                if (l[uv].uv - r.link_loop_next[uv].uv).length < 1e-6 and (l.link_loop_next[uv].uv - r[uv].uv).length < 1e-6:
                    seen.add(r.face.index); todo.append(r.face)
        out.append(comp)
    return out


def main():
    owner = np.full((SIZE, SIZE), -1, np.int32); clash = np.zeros((SIZE, SIZE), bool); pid = 0; names = []
    pairs = {}
    for o in bpy.data.objects:
        if o.type != 'MESH' or not o.name.endswith('_LOD0') or o.name.lower().endswith('_water_lod0') or o.name.endswith('_Leaves_LOD0'): continue   # the water strip tiles its own texture; FR03 vine cards share atlas cells on purpose
        bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.triangulate(bm, faces=bm.faces[:]); uv = bm.loops.layers.uv.active
        if not uv: bm.free(); continue
        for comp in pieces(bm, uv):
            for f in comp:
                t = np.array([l[uv].uv[:] for l in f.loops]) * SIZE - .5
                lo = np.maximum(np.ceil(t.min(0)).astype(int), 0); hi = np.minimum(np.floor(t.max(0)).astype(int), SIZE - 1)
                if (hi < lo).any(): continue
                ys, xs = np.mgrid[lo[1]:hi[1] + 1, lo[0]:hi[0] + 1]
                a, b, c = t
                def side(p, q): return (q[0] - p[0]) * (ys - p[1]) - (q[1] - p[1]) * (xs - p[0])
                s = np.stack((side(a, b), side(b, c), side(c, a)))
                m = (s >= 0).all(0) | (s <= 0).all(0)
                if not m.any(): continue
                yy, xx = ys[m], xs[m]; cur = owner[yy, xx]
                hit = (cur >= 0) & (cur != pid); clash[yy[hit], xx[hit]] = True
                for q in np.unique(cur[hit]): pairs[(int(q), pid)] = pairs.get((int(q), pid), 0) + int((cur[hit] == q).sum())
                owner[yy, xx] = pid
            pid += 1
        bm.free()
    print('QAUVOVERLAP', bpy.path.basename(bpy.data.filepath), 'pieces', pid, 'used_texels', int((owner >= 0).sum()), 'clash_texels', int(clash.sum()), 'clash_pairs', len(pairs), 'largest', sorted(pairs.values())[-5:])


main()
