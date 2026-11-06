"""Cross-sub-mesh contact check for exported world props (Johnnnny0823, 11/05 review round).
A per-sub-mesh qa_check (qa_submesh.py) reports a loose piece as floating whenever it rests on a *different* sub-mesh (a tile on
the Stone mesh, an axe in the chopping block): it only sees its own object. This walks every connected island of every LOD0
object and classifies it, using the same 2 mm contact tolerance as the game profile:
  grounded   lowest point within 2 mm of z 0 (loose ground dressing: grass blades, pebbles, chips)
  contact    some vertex within 2 mm of another island (same or another sub-mesh), or its triangles cut through one (a leaf
             pinned into a post, incense pushed into the ash)
  enclosed   wholly inside another closed part without touching it (a glow core inside a lantern): reported, not an error
  hover      neither: a real float, listed with its centre and lowest point
blender -b --factory-startup -P qa_contact.py -- <out.json> <ID> [<ID> ...]
"""
import bpy, sys, os, json, time
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'exports', 'world-props-a')
TOL = .002
a = sys.argv[sys.argv.index('--') + 1:]; out = a[0]; ids = a[1:]
res = json.load(open(out, encoding='utf-8')) if os.path.exists(out) else {}


def islands(me):
    n = len(me.vertices); e = np.empty(len(me.edges) * 2, int); me.edges.foreach_get('vertices', e); e = e.reshape(-1, 2)
    par = np.arange(n)
    def find(i):
        r = i
        while par[r] != r: r = par[r]
        while par[i] != r: par[i], i = r, par[i]
        return r
    for x, y in e:
        rx, ry = find(x), find(y)
        if rx != ry: par[rx] = ry
    return np.array([find(i) for i in range(n)])


for k in ids:
    t0 = time.time()
    if os.environ.get('WA_GEOM'):   # geometry-only build of build_world_a.py (no bake/export): its joined LOD0 groups
        bpy.ops.wm.open_mainfile(filepath=os.path.join(os.environ['WA_GEOM'], k + '_geom.blend'))
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=os.path.join(R, k + '.fbx'))
    for o in bpy.data.objects: o.select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    obs = sorted((o for o in bpy.data.objects if o.type == 'MESH' and o.name.endswith('_LOD0')), key=lambda o: o.name)
    dg = bpy.context.evaluated_depsgraph_get()
    data = {}
    for o in obs:
        me = o.data; n = len(me.vertices); co = np.empty(n * 3); me.vertices.foreach_get('co', co); co = co.reshape(n, 3)
        il = islands(me); pv = np.empty(len(me.polygons), int); me.polygons.foreach_get('loop_start', pv)
        lv = np.empty(len(me.loops), int); me.loops.foreach_get('vertex_index', lv)
        tris = np.empty(len(me.polygons), int); me.polygons.foreach_get('loop_total', tris)
        polys = [lv[s_:s_ + t_].tolist() for s_, t_ in zip(pv, tris)]
        data[o.name] = dict(co=co, il=il, fil=il[lv[pv]], polys=polys, bvh=BVHTree.FromObject(o, dg))
    rows = {}
    for o in obs:
        d = data[o.name]; co, il = d['co'], d['il']; cnt = {'grounded': 0, 'contact': 0, 'enclosed': 0, 'hover': []}
        uniq = np.unique(il)
        for r in uniq:
            vi = np.nonzero(il == r)[0]; pts = co[vi]
            if len(uniq) == 1 and len(obs) == 1: cnt['contact'] += 1; continue
            if pts[:, 2].min() <= TOL: cnt['grounded'] += 1; continue
            hit = False
            # other sub-meshes first (one nearest query per vertex, early exit), then other islands of the same sub-mesh
            for on, od in data.items():
                if on == o.name: continue
                for p in pts:
                    if od['bvh'].find_nearest(Vector(p), TOL)[0] is not None: hit = True; break
                if hit: break
            if not hit and len(uniq) > 1:
                for p in pts:
                    if any(d['fil'][h[2]] != r for h in d['bvh'].find_nearest_range(Vector(p), TOL)): hit = True; break
            if not hit:   # cutting through another part counts as contact
                fi = np.nonzero(d['fil'] == r)[0]; ib = BVHTree.FromPolygons([Vector(c) for c in co], [d['polys'][i] for i in fi])
                for on, od in data.items():
                    pr = ib.overlap(od['bvh'])
                    if on != o.name and pr: hit = True; break
                    if on == o.name and any(d['fil'][j] != r for _, j in pr): hit = True; break
            if not hit:   # inside a closed part: a ray up and a ray down both leave through back faces of the same other part
                p = Vector(pts[0]); inside = False
                for on, od in data.items():
                    hu = od['bvh'].ray_cast(p + Vector((0, 0, 1e-4)), Vector((0, 0, 1))); hd = od['bvh'].ray_cast(p - Vector((0, 0, 1e-4)), Vector((0, 0, -1)))
                    if hu[0] is not None and hd[0] is not None and hu[1].z > 0 and hd[1].z < 0 and (on != o.name or (d['fil'][hu[2]] != r and d['fil'][hd[2]] != r)):
                        inside = True; break
                if inside: cnt['enclosed'] += 1; continue
            if hit: cnt['contact'] += 1
            else:   # how far off is it: nearest other geometry (any sub-mesh, other islands of its own), searched up to 10 cm
                gap = 1.0
                for on, od in data.items():
                    for p in pts[::max(1, len(pts) // 400)]:
                        if on != o.name:
                            h = od['bvh'].find_nearest(Vector(p), .1)
                            if h[0] is not None: gap = min(gap, h[3])
                        else:
                            for h in od['bvh'].find_nearest_range(Vector(p), min(gap, .1)):
                                if d['fil'][h[2]] != r: gap = min(gap, h[3])
                cnt['hover'].append({'centre': [round(x, 3) for x in pts.mean(0)], 'min_z': round(float(pts[:, 2].min()), 4), 'verts': len(vi),
                                     'gap': round(gap, 4)})
        cnt['islands'] = len(uniq); rows[o.name] = cnt
        print('CONTACT', k, o.name, len(uniq), cnt['grounded'], cnt['contact'], cnt['enclosed'], len(cnt['hover']), flush=True)
    res[k] = rows; print('ITEM', k, round(time.time() - t0, 1), flush=True)
    json.dump(res, open(out, 'w', encoding='utf-8'), indent=1)
print('CONTACT_DONE')
