"""Collision for the re-textured Dondon buildings (RS02, RS03): their sources have none.

Every part a 1.75 m walker can reach (lowest point under 2.2 m; not roof tile, not Detail_Small) gets one box fitted to it: the smaller
by volume of its axis-aligned box and its box along its principal axes, so a post, a plank or a diagonal brace keeps its own lean.
A dimension thinner than 2 cm is opened to 2 cm about its middle (window paper, a blade). Parts named in `skip` get none: those inside
another part's box (forge bricks around the mortar core, embers in the fire bed), loose goods on a shelf, a water surface in a tub.
Returns (vertices, faces, boxes) for build_village_houses_b.make_collision, which joins them into <ID>_Collision (MeshCollider, convex off)."""
import numpy as np

QUADS = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]


def part_box(co, thin=.02):
    """8 corners (world) of the tighter of the axis-aligned and the principal-axes box of the points `co` (n x 3)."""
    c = co - co.mean(0)
    _, vec = np.linalg.eigh(c.T @ c)
    best = None
    for R in (np.eye(3), vec.T):                       # rows are the box axes
        p = co @ R.T; lo, hi = p.min(0), p.max(0)
        mid = (lo + hi) / 2; half = np.maximum((hi - lo) / 2, thin / 2)
        vol = float(np.prod(2 * half))
        if best is None or vol < best[0] - 1e-9: best = (vol, R, mid, half)
    _, R, mid, half = best
    corners = [mid + half * np.array([sx, sy, sz]) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    return [tuple(float(x) for x in (k @ R)) for k in corners]


def boxes(parts, skip=(), zmax=2.2, min_size=.03):
    V, F, n, names = [], [], 0, {}
    for q in parts:
        if q.type != 'MESH' or q.get('group') in ('Tile', 'Detail_Small'): continue
        if any(q.name.startswith(s) for s in skip): continue
        mw = q.matrix_world
        co = np.array([tuple(mw @ v.co) for v in q.data.vertices], np.float64)
        if len(co) < 3 or co[:, 2].min() > zmax or (co.max(0) - co.min(0)).max() < min_size: continue
        base = len(V); V += part_box(co); F += [tuple(base + i for i in f) for f in QUADS]; n += 1
        k = q.name.split('.')[0].split('_Part')[0]; names[k] = names.get(k, 0) + 1
    return V, F, n, names

