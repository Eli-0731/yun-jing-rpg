"""VL measured checks: read off the exported LOD0 and the collision mesh by rays, compared with StarterHouse v004's own numbers."""
import bpy, math
import numpy as np
from mathutils import Vector
from ti_core import S
from vl_roof import roof_z, DEPTH, N_COURSE

STARTER = {'size_m': (9.0478, 8.1891, 5.6129), 'wall_outer_m': {'front': -2.61, 'rear': 2.61, 'left': -3.61, 'right': 3.61}, 'floor_m': .54,
           'steps_m': (.18, .36, .54)}


def _bvh(objs):
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get(); trees = [BVHTree.FromObject(o, dg) for o in objs]
    def cast(p, d):
        best = None
        for t in trees:
            hit = t.ray_cast(Vector(p), Vector(d).normalized())
            if hit[0] is not None and (best is None or hit[3] < best[1]): best = (hit[0], hit[3])
        return best
    return cast


def texel_density(objs, size):
    """px per metre of every face after packing (sqrt of UV area x size^2 / surface area); the visible faces are those with uvw >= 0.99."""
    vis, hid = [], []
    for o in objs:
        me = o.data; uvl = me.uv_layers.active
        w = np.ones(len(me.polygons), np.float32)
        if 'uvw' in me.attributes: me.attributes['uvw'].data.foreach_get('value', w)
        for p in me.polygons:
            if p.area < 1e-5: continue
            q = [uvl.data[li].uv for li in p.loop_indices]
            a = 0.
            for i in range(1, len(q) - 1): a += abs((q[i] - q[0]).cross(q[i + 1] - q[0])) * .5
            d = math.sqrt(a * size * size / p.area)
            (vis if w[p.index] >= .99 else hid).append((d, p.area))
    def stats(L):
        if not L: return None
        L.sort(); tot = sum(a for _, a in L); acc = 0.; out = {}
        for d, a in L:
            acc += a
            for k, f in (('p10', .1), ('median', .5), ('p90', .9)):
                if k not in out and acc >= f * tot: out[k] = round(d, 1)
        out['area_m2'] = round(tot, 1); return out
    return {'visible': stats(vis), 'inside_or_covered': stats(hid), 'atlas_px': size, 'style_spec_target': '256 px/m for buildings'}


def house_checks(aid, check, cfg):
    cond = cfg['cond']
    objs = list(S['lods'][0].values()); cast = _bvh(objs)
    body = _bvh([o for g, o in S['lods'][0].items() if not g.startswith('Detail_')])     # the house without leaves and grass lying on it
    col = _bvh([S['collision_obj']]) if S.get('collision_obj') else None
    # wall outline: horizontal rays at 1.0 m onto the plaster of each wall, on a pier (no window, no board)
    probes = {'front': ((-1.25, -12, 1.0), (0, 1, 0), 1), 'rear': ((-1.25, 12, 1.0), (0, -1, 0), 1), 'left': ((-12, -1.25, 1.0), (1, 0, 0), 0),
              'right': ((12, -2.3, 1.6), (-1, 0, 0), 0)}
    got = {}
    for k, (p, d, ax) in probes.items():
        h = cast(p, d); got[k] = round(h[0][ax], 4) if h else None
    ok = all(v is not None and abs(v - STARTER['wall_outer_m'][k]) < .02 for k, v in got.items())
    check('wall_outline_as_starterhouse', ok, {'measured_outer_faces_m': got, 'starterhouse_m': STARTER['wall_outer_m'],
          'walls_m': [round(got['right'] - got['left'] - .22, 3) if None not in got.values() else None, round(got['rear'] - got['front'] - .22, 3) if None not in got.values() else None]})
    # plinth, porch and steps
    z = lambda x, y, z0=9.: (body((x, y, z0), (0, 0, -1)) or [Vector((0, 0, -1))])[0].z
    steps = [round(z(0., -4.55 + i * .34, 2.), 3) for i in range(3)]      # from 2 m: the eave is over the top step and the porch
    porch = round(z(-.6, -3.1, 2.), 3)
    check('porch_and_steps_as_starterhouse', all(abs(a - b) < .012 for a, b in zip(steps, STARTER['steps_m'])) and abs(porch - .54) < .012,
          {'step_tops_m': steps, 'porch_floor_m': porch, 'starterhouse_m': {'steps': STARTER['steps_m'], 'porch': .54}, 'rise_m': .18})
    # eave height over the porch, ridge
    h = cast((-.5, -3.9, 1.), (0, 0, 1)); eave = round(h[0].z, 3) if h else None
    ridge = round(z(-.5, 0.), 3)
    check('eave_underside_at_least_2_6m', eave is not None and eave >= 2.6, {'front_eave_underside_m': eave, 'above_porch_m': round(eave - .54, 3) if eave else None,
          'world_constant_m': 2.6})
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        e = o.evaluated_get(dg); m = e.to_mesh()
        co = np.zeros(len(m.vertices) * 3, np.float32); m.vertices.foreach_get('co', co); co = co.reshape(-1, 3); e.to_mesh_clear()
        lo = Vector(np.minimum(lo, co.min(0))); hi = Vector(np.maximum(hi, co.max(0)))
    dims = [round(v, 3) for v in hi - lo]
    check('outline_size_as_starterhouse', all(abs(a - b) <= .35 for a, b in zip(dims, STARTER['size_m'])),
          {'dims_m': dims, 'starterhouse_dims_m': STARTER['size_m'], 'ridge_top_m': ridge, 'tolerance_m': .35,
           'note': 'same walls, plinth, porch and roof curve; the tile courses and ridge are rebuilt, so the overall box differs by a few centimetres'})
    # collision: closed on all four sides at 1.2 m, porch floor walkable
    if col:
        cg = {}
        for k, (p, d, ax) in probes.items():
            hh = col((p[0], p[1] if k != 'right' else .5, 1.2), d); cg[k] = round(hh[0][ax], 3) if hh else None
        top = col((-.6, -3.1, 5.), (0, 0, -1))
        check('collision_closed_all_round', all(v is not None and abs(v - STARTER['wall_outer_m'][k]) < .03 for k, v in cg.items()) and top and abs(top[0].z - .54) < .01,
              {'collision_wall_faces_m': cg, 'porch_floor_m': round(top[0].z, 3) if top else None})
    out = {'eave_underside_m': eave, 'ridge_m': ridge}
    if cond == 'abandoned':
        hd = cast((0., -12, 1.8), (0, 1, 0)); hw = cast((-2.35, -12, 2.0), (0, 1, 0))
        check('door_and_windows_boarded', hd and hd[0].y < -2.81 and hw and hw[0].y < -2.75,
              {'first_hit_door_y': round(hd[0].y, 3) if hd else None, 'first_hit_window_y': round(hw[0].y, 3) if hw else None, 'door_ring_front_y': -2.80})
        rows = []
        for s, xc, kc, hw_, hk in S['holes']:
            t = 1 - (kc + .5) / N_COURSE; y = s * t * DEPTH[s]; zt = roof_z(xc, t)
            hit = cast((xc, y, 9.), (0, 0, -1)); nb = cast((xc + hw_ + .5, y, 9.), (0, 0, -1))
            rows.append({'slope': s, 'x': xc, 'course': kc, 'tile_level_m': round(zt, 3), 'first_hit_in_hole_m': round(hit[0].z, 3) if hit else None,
                         'first_hit_beside_m': round(nb[0].z, 3) if nb else None})
        check('tiles_missing_in_three_patches', all(r['first_hit_in_hole_m'] is not None and r['first_hit_in_hole_m'] < r['tile_level_m'] - .03 and
                                                   r['first_hit_beside_m'] is not None and r['first_hit_beside_m'] > r['tile_level_m'] - .03 for r in rows), rows)
    if cond == 'collapsed':
        hit = cast((12., .3, 1.6), (-1, 0, 0))
        ch = col((12., .3, 1.6), (-1, 0, 0)) if col else None
        check('room_open_where_the_wall_fell', hit and hit[0].x < 3.0, {'ray_from_+x_at_y0.3_z1.6_first_hit_x': round(hit[0].x, 3) if hit else None})
        check('collision_closes_the_gap', ch and abs(ch[0].x - 3.61) < .03, {'collision_hit_x': round(ch[0].x, 3) if ch else None, 'wall_line_x': 3.61})
        sky = cast((2.5, 2.2, 9.), (0, 0, -1))
        check('roof_open_over_the_collapse', sky and sky[0].z < 4.0, {'first_hit_down_at_x2.5_y2.2': round(sky[0].z, 3) if sky else None, 'roof_there_was_m': round(roof_z(2.5, 2.2 / 3.45), 3)})
        out['tree_leaves'] = S.get('tree_leaves')
    return out
