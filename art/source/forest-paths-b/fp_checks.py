"""FP measured checks: read off the exported LOD meshes, the collision mesh and the baked atlas, not taken from the design numbers."""
import bpy, math
import numpy as np
from mathutils import Vector, Matrix
from ti_core import S
import fp_parts as PP


def _bvh(objs):
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get(); trees = [BVHTree.FromObject(o, dg) for o in objs]
    def cast(p, d):
        best = None
        for t in trees:
            hit = t.ray_cast(Vector(p), Vector(d).normalized())
            if hit[0] is not None and (best is None or hit[3] < best[1]): best = (hit[0], hit[3], hit[1])
        return best
    def down(x, y, z0=20.):
        h = cast((x, y, z0), (0, 0, -1)); return h[0].z if h else None
    return down, cast


def _ends(o, L):
    """{round(t, 3): (world point, top-surface corner normal or None)} of the vertices on the two end rows (s = 0 and s = L)."""
    me = o.data; pth = me.attributes['pth'].data; mw = o.matrix_world
    nrm = {}
    for p in me.polygons:
        if p.normal.z < .3: continue
        for li in p.loop_indices: nrm[me.loops[li].vertex_index] = Vector(me.corner_normals[li].vector)
    W, E = {}, {}
    for v in me.vertices:
        s, t, h = pth[v.index].vector
        if s < -1e-4 or s > L + 1e-4: continue                         # a tall end's grid (FP03 / FP05 top)
        key = (round(t, 3), True) if h > 0 else (math.copysign(9., t), False)   # a wedge's bottom corners: one key per side
        if s < 1e-4: W[key] = (mw @ v.co, nrm.get(v.index))
        elif s > L - 1e-4: E[key] = (mw @ v.co, nrm.get(v.index))
    return W, E


def _sample(img_px, size, uv):
    """Bilinear sample at uv (texel centres at (i + 0.5) / size)."""
    fx, fy = uv[0] * size - .5, uv[1] * size - .5; x0, y0 = int(math.floor(fx)), int(math.floor(fy)); ax, ay = fx - x0, fy - y0
    c = lambda x, y: img_px[min(size - 1, max(0, y)), min(size - 1, max(0, x)), :3]
    return (c(x0, y0) * (1 - ax) * (1 - ay) + c(x0 + 1, y0) * ax * (1 - ay) + c(x0, y0 + 1) * (1 - ax) * ay + c(x0 + 1, y0 + 1) * ax * ay)


def path_checks(aid, check, cfg):
    RL = S['relief']; F = RL.F; L = F.L
    sw, se = S['sockets']['Socket_Path_W'].matrix_world, S['sockets']['Socket_Path_E'].matrix_world
    M = se @ Matrix.Rotation(math.pi, 4, 'Z') @ sw.inverted()          # the next piece: its W joint on this one's E joint, facing on
    # 1. the end section at every LOD: west row = east row, and a chained copy meets this piece with no gap
    ends = {}
    for lv in (0, 1, 2):
        g = S['lods'][lv]['Ground']; W, E = _ends(g, L)
        common = sorted(k for k in set(W) & set(E) if k[1])               # the top surface (the bottom of a wedge is not a joint)
        dz = max(abs((W[k][0].z - F.ground(0.)) - (E[k][0].z - F.ground(L))) for k in common)
        gap = max(((M @ W[k][0]) - E[k][0]).length for k in common)
        nd = max(((M.to_3x3() @ W[k][1]) - E[k][1]).length for k in common if W[k][1] is not None and E[k][1] is not None)
        ends[f'LOD{lv}'] = {'end_vertices': [len(W), len(E)], 'matched': len(common), 'max_dz_mm': round(dz * 1000, 3),
                            'chained_gap_mm': round(gap * 1000, 3), 'normal_difference': round(nd, 5),
                            '_W': {k: tuple(round(c, 5) for c in W[k][0]) for k in common}}
    ok = all(v['end_vertices'][0] == v['end_vertices'][1] and v['matched'] == v['end_vertices'][0] - 2 and v['chained_gap_mm'] <= 2.
             and v['normal_difference'] < .01 for v in ends.values())
    # every LOD has the same end vertices: LOD0 next to LOD2 also closes
    cross = max((Vector(ends['LOD0']['_W'][k]) - Vector(ends[f'LOD{lv}']['_W'][k])).length for lv in (1, 2) for k in ends[f'LOD{lv}']['_W'])
    for v in ends.values(): v.pop('_W')
    check('end_sections_join_every_lod', ok and cross <= .002, {'per_lod': ends, 'lod0_vs_lod1_lod2_end_vertices_max_mm': round(cross * 1000, 3),
          'need': 'end rows identical, chained copy gap <= 2 mm, same corner normals'})
    # 2. the section on the joint is the kit section (so FP01 meets FP02-FP05)
    W, _ = _ends(S['lods'][0]['Ground'], L)
    dev = max(abs(W[k][0].z - F.ground(0.) - PP.section(k[0])) for k in W if k[1])
    check('joint_is_kit_section', dev <= .001, {'max_deviation_mm': round(dev * 1000, 3), 'section_heights_m': {str(t): round(PP.section(t), 4) for t in (0., .2, .4, .5, .62, .7, .8)}})
    # 3. colour across the joint: the baked colour at the west end row against the east end row
    g = S['lods'][0]['Ground']; me = g.data; im = None
    for nd in me.materials[0].node_tree.nodes:
        if nd.type == 'TEX_IMAGE' and 'BaseColor' in nd.image.name: im = nd.image
    size = im.size[0]; px = np.array(im.pixels[:], np.float32).reshape(size, size, 4)
    uvl = me.uv_layers.active.data; pth = me.attributes['pth'].data; cw, ce = {}, {}
    ni = S['slab']['ni']; mids = [L * round(ni * f) / ni for f in (.25, .75)]      # control: two rows inside the piece
    cm = {m: ({}, {}) for m in mids}
    for p in me.polygons:
        if p.normal.z < .3: continue
        uc = sum((Vector(uvl[li].uv) for li in p.loop_indices), Vector((0, 0))) / p.loop_total
        sc = sum(pth[me.loops[li].vertex_index].vector[0] for li in p.loop_indices) / p.loop_total
        for li in p.loop_indices:                              # 0.7 texel in from the corner (about 2 mm): the colour drawn against
            s, t, h = pth[me.loops[li].vertex_index].vector    # the joint, clear of the island's padded border
            u0 = Vector(uvl[li].uv); q = u0 + (uc - u0).normalized() * (.7 / size)
            if s < 1e-4: cw.setdefault(round(t, 3), []).append(_sample(px, size, q))
            elif s > L - 1e-4: ce.setdefault(round(t, 3), []).append(_sample(px, size, q))
            for m in mids:
                if abs(s - m) < 1e-4 and h > 0: cm[m][0 if sc < m else 1].setdefault(round(t, 3), []).append(_sample(px, size, q))
    def windows(P, Q):
        keys = sorted(set(P) & set(Q))
        A = np.array([np.mean(P[k], 0) for k in keys]); B = np.array([np.mean(Q[k], 0) for k in keys])
        return keys, A, B, [float(np.abs(A[i:i + 5].mean(0) - B[i:i + 5].mean(0)).max()) for i in range(len(keys) - 4)]
    keys, A, B, win = windows(cw, ce)
    ctrl = max(max(windows(*cm[m])[3]) for m in mids)
    diff = np.abs(A - B).max(1)
    line = float(np.abs(A.mean(0) - B.mean(0)).max())
    check('joint_colour_matches', line <= .006 and max(win) <= .015,
          {'whole_joint_line_difference': round(line, 4), 'worst_16cm_window_difference': round(max(win), 4),
           'same_measure_on_two_rows_inside_the_piece': round(ctrl, 4),
           'need': 'line <= 0.006, every 16 cm window <= 0.015 (linear); the inside-row figure is for reference only',
           'single_corner_difference': {'mean': round(float(diff.mean()), 4), 'max': round(float(diff.max()), 4), 'at_across_m': keys[int(np.argmax(diff))]},
           'mean_value_at_joint': round(float(A.mean()), 4), 'corners': len(keys),
           'note': 'bilinear, 0.7 texel (about 1.4 mm) in from each end-row corner; single corners differ by the 1-3 mm soil grit between the two '
                   'sample points (2.8 mm apart across the joint), which the joint renders (joint_*.png) do not show. The control takes the '
                   'same samples either side of the grid rows at 1/4 and 3/4 of the length, where there is no joint: that is how much the '
                   'soil grain alone changes over the same 2.8 mm'})
    # 4. walking: the collision surface under the tread, and how far the visible surface stands off it
    col = S['collision_obj']; cdown, _ = _bvh([col]); vdown, vcast = _bvh([o for g, o in S['lods'][0].items() if not g.startswith('Detail_')])
    slope_max, step_max = cfg.get('slope_max', 6.), cfg.get('step_max', .03); skip = cfg.get('vis_skip') or (lambda s_, t_: False)
    steep = math.tan(math.radians(40))
    worst_slope, worst_step, cross, rise, lines = 0., 0., 0., 0., {}
    grid = []
    for t in (-.3, -.15, 0., .15, .3):
        ss = np.arange(.0125, L - .01, .025); z = []
        for s in ss:
            q = F.p(s, t, 0); z.append(cdown(q.x, q.y))
        grid.append(z)
        run = 0.; steps = []
        for a, b in zip(z, z[1:]):                               # a run of rises steeper than 40 deg is one step
            if (b - a) / .025 > steep or (a - b) / .025 > steep: run += b - a
            else:
                if abs(run) > 1e-4: steps.append(abs(run))
                run = 0.
        if abs(run) > 1e-4: steps.append(abs(run))
        for i in range(0, len(z) - 8):                           # slope over 0.2 m windows that hold no step
            seg = z[i:i + 9]
            if any(abs(b - a) / .025 > steep for a, b in zip(seg, seg[1:])): continue
            worst_slope = max(worst_slope, math.degrees(math.atan2(abs(seg[-1] - seg[0]), .2)))
        worst_step = max([worst_step] + steps); lines[str(t)] = {'steps_m': [round(v, 3) for v in steps]}
        rise = max(rise, z[-1] - z[0])
    ts = (-.3, -.15, 0., .15, .3); ss = np.arange(.0125, L - .01, .025)
    for (ta, ra), (tb, rb) in zip(zip(ts, grid), zip(ts[1:], grid[1:])):   # across the tread, 0.15 m apart, away from steps and the root
        for s, a, b in zip(ss, ra, rb):
            if abs(b - a) < .1 and not skip(s, ta) and not skip(s, tb): cross = max(cross, math.degrees(math.atan2(abs(b - a), abs(PP.widen(tb) - PP.widen(ta)))))
    check('tread_walkable', worst_slope <= slope_max and worst_step <= step_max and cross <= 8. and min(min(r) for r in grid) > 0,
          {'slope_max_deg': round(worst_slope, 2), 'need_slope_deg': slope_max, 'largest_step_m': round(worst_step, 3), 'need_step_m': step_max,
           'cross_slope_max_deg': round(cross, 2), 'rise_m': round(rise, 3), 'walk_lines': lines,
           'how': 'rays down onto the collision mesh along t = -0.3 / -0.15 / 0 / 0.15 / 0.3 every 2.5 cm; a run of rises steeper than 40 deg '
                  'counts as one step (its height); slope is over 0.2 m windows without a step'})
    off, vsteps, skipped = [], [], 0
    for t in (-.25, 0., .25):                                  # walk lines on what shows: roots are the only steps
        prev = None
        for s in np.arange(.03, L - .02, .025):
            q = F.p(s, t, 0); hv = vcast((q.x, q.y, 20.), (0, 0, -1))
            z = None
            if hv is not None:
                z = hv[0].z
                hc = cdown(q.x, q.y)
                if hc is not None:
                    if skip(s, t): skipped += 1
                    else: off.append(z - hc)
            if prev is not None and z is not None and not skip(s, t): vsteps.append(abs(z - prev))
            prev = z
    check('visible_surface_near_collision', max(off) <= .06 and min(off) >= -.025,
          {'visible_above_collision_m': [round(min(off), 4), round(max(off), 4)], 'largest_step_on_walk_lines_m': round(max(vsteps), 4),
           'samples_skipped_at_steps_or_root': skipped,
           'note': 'walk lines t = -0.25 / 0 / 0.25 every 2.5 cm on LOD0 (soil, roots, stones, logs; leaves, moss and ferns are Detail_Small and do not hold a foot); '
                   'feet sink at most 2.5 cm, stand at most 6 cm over the collision; the round face of a step log or the big root (within 0.2 / 0.32 m) is skipped'})
    check('sockets_present', {'Socket_Path_W', 'Socket_Path_E'} <= set(S['sockets']), sorted(S['sockets']))
    return {'length_m': L, 'width_m': round(2 * PP.widen(PP.HW), 3), 'section': 'fp_parts.section: tread 1.16 m wide at 0.055-0.06 m, bank crests 0.12 m at 0.82 m out, edge 0.012 m at 1.0 m',
            'joint': 'next piece: its Socket_Path_W on this Socket_Path_E, rotated 180 deg about Z',
            'end_section_vertices': ends['LOD0']['matched'], 'walk': 'from Socket_Path_W (s = 0) to Socket_Path_E (s = L)',
            'socket_heights_m': [round(F.ground(0.), 4), round(F.ground(L), 4)], 'sockets': sorted(S['sockets'])}
