"""Rebuild LOD1/LOD2 of finished world props from their saved .blend (Johnnnny0823, PR #68 review 11/07), without re-baking.
LOD0 is untouched. LOD1 is what phones see up close (quality-tiers-v1 section 4.1), so each item gets a LOD1 budget instead of a flat
50 %: the whole item at most LOD1_BUDGET triangles (and never more than 50 %), LOD2 at most LOD2_BUDGET (never more than 15 %).
The budget is shared out by water-filling on sqrt(group triangles): every group gets lambda*sqrt(n) but never more than its 50 % /
15 %, and what the small groups cannot use goes to the big ones. A flat ratio crushed small parts (SC04 ridge lashings at 3.8 %
collapsed into spikes); this keeps ropes, axes and lamps near 50 % and takes the cut from the straw and shakes.
Exports FBX only (all LODs + collision); the GLB copy was dropped in the same review. FBX carries no tangents: Unity computes
MikkTSpace tangents on import (ModelImporter default), which matches the baked normal maps and makes the file smaller.
blender -b --factory-startup -P relod_world_a.py -- SC04 RK10A ...
"""
import bpy, sys, json, math
from pathlib import Path
HERE = Path(__file__).resolve().parent
OUT = HERE.parent.parent / 'exports' / 'world-props-a'
LOD1_BUDGET, LOD2_BUDGET = 100_000, 25_000


def tri(o): return sum(len(p.vertices) - 2 for p in o.data.polygons)


def export_fbx(pid, objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=str(OUT / f'{pid}.fbx'), use_selection=True, object_types={'MESH', 'EMPTY'}, global_scale=1.0,
                             apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', bake_space_transform=True, axis_forward='-Z',
                             axis_up='Y', use_mesh_modifiers=True, mesh_smooth_type='FACE', use_tspace=False, add_leaf_bones=False,
                             bake_anim=False, path_mode='RELATIVE', embed_textures=False)


def share(n, budget, cap):
    """Water-filling: each group lambda*sqrt(n), capped at cap*n; lambda chosen so the sum meets the budget (or all are capped)."""
    if sum(cap * v for v in n.values()) <= budget: return {k: cap * v for k, v in n.items()}
    lo, hi = 0.0, max(math.sqrt(v) * cap for v in n.values()) + 1
    for _ in range(60):
        lam = (lo + hi) / 2
        if sum(min(cap * v, lam * math.sqrt(v)) for v in n.values()) > budget: hi = lam
        else: lo = lam
    return {k: min(cap * v, lo * math.sqrt(v)) for k, v in n.items()}


def relod(pid):
    bpy.ops.wm.open_mainfile(filepath=str(HERE / f'{pid}.blend'))
    sc = bpy.context.scene
    root = bpy.data.objects[f'{pid}_GroundOrigin']
    lod0 = sorted((o for o in root.children if o.type == 'MESH' and o.name.endswith('_LOD0')), key=lambda o: o.name)
    for o in [o for o in root.children if o.type == 'MESH' and (o.name.endswith('_LOD1') or o.name.endswith('_LOD2'))]:
        me = o.data; bpy.data.objects.remove(o); bpy.data.meshes.remove(me)
    n0 = {o.name: tri(o) for o in lod0}; total = sum(n0.values())
    alloc = {1: share(n0, LOD1_BUDGET, .5), 2: share(n0, LOD2_BUDGET, .15)}
    r1 = sum(alloc[1].values()) / total; r2 = sum(alloc[2].values()) / total
    levels = {0: lod0, 1: [], 2: []}
    for o in lod0:
        for L in (1, 2):
            want = alloc[L][o.name]
            d = o.copy(); d.data = o.data.copy(); sc.collection.objects.link(d)
            d.name = d.data.name = o.name[:-1] + str(L)
            d.parent = root; d.matrix_parent_inverse = o.matrix_parent_inverse.copy(); d.hide_render = True
            m = d.modifiers.new('d', 'DECIMATE'); m.ratio = min(1.0, want / n0[o.name]); m.use_collapse_triangulate = True
            bpy.ops.object.select_all(action='DESELECT'); d.select_set(True); bpy.context.view_layer.objects.active = d
            bpy.ops.object.modifier_apply(modifier='d')
            levels[L].append(d)
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE / f'{pid}.blend'), compress=True)
    col = bpy.data.objects.get(f'{pid}_Collision')
    extra = [o for o in sc.objects if o.name.endswith('LightSocket')]
    if 'glow_level' in root: root['glow_level'] = 4 if pid == 'TY04' else 1; bpy.context.view_layer.update()
    export_fbx(pid, [root] + lod0 + levels[1] + levels[2] + ([col] if col else []) + extra)
    groups = {}
    for o in lod0:
        g = o.name[:-5]; g = g[len(pid) + 1:] if g.startswith(pid + '_') else g
        groups[g] = [tri(o)] + [tri(next(d for d in levels[L] if d.name == o.name[:-1] + str(L))) for L in (1, 2)]
    tt = [sum(v[i] for v in groups.values()) for i in range(3)]
    print('RELOD', pid, tt, round(r1, 4), round(r2, 4), flush=True)
    return pid, groups, tt


ids = sys.argv[sys.argv.index('--') + 1:]
res = [relod(i) for i in ids]
mf = OUT / 'model_info.json'; info = json.loads(mf.read_text(encoding='utf-8'))
for pid, groups, tt in res:
    for g, t in groups.items():
        if g in info[pid]['groups']: info[pid]['groups'][g]['triangles'] = t
    info[pid]['triangles_total'] = tt
    info[pid]['lod_budget'] = {'LOD1_max': LOD1_BUDGET, 'LOD2_max': LOD2_BUDGET, 'note': 'quality-tiers-v1 4.1: LOD1 is the phone close-up; LOD0 untouched'}
mf.write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding='utf-8')
print('RELOD_DONE')
